from __future__ import annotations

import argparse
import asyncio
import logging
import os
from pathlib import Path

import spacy
from dotenv import load_dotenv

from src.graph.connection import Neo4jConnection
from src.graph.ingestion.pipeline import GraphIngestionPipeline
from src.graph.ingestion.repository import GraphIngestionRepository
from src.graph.ingestion.service import DisclosureGraphIngestionService
from src.ingestion.disclosures.graph_bridge import NormalizedDisclosureGraphBridge
from src.ingestion.disclosures.normalizers import NormalizerRegistry
from src.ingestion.disclosures.providers import (
    InvestorRelationsDisclosureProvider,
    OpenDARTDisclosureProvider,
    SECDisclosureProvider,
)
from src.ingestion.disclosures.registry import CompanyRegistry, SourceRegistry
from src.ingestion.disclosures.router import SourceRouter
from src.ingestion.disclosures.service import DisclosureIngestionService
from src.ingestion.disclosures.storage import DocumentRegistry, RawArtifactStore
from src.ingestion.sec.client import SECClient
from src.nlp.relation_extraction import RelationExtractor


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

COMPANIES_PATH = Path("data/seed/companies.json")
SOURCES_PATH = Path("data/seed/disclosure_sources.json")
BINDINGS_PATH = Path("data/seed/disclosure_source_bindings.json")
SEC_10K_PATH = Path("data/seed/sec_10k_targets.json")
SEC_20F_PATH = Path("data/seed/sec_20f_targets.json")
RAW_ROOT = Path("data/raw/disclosures")
REGISTRY_DB = Path("data/disclosures/disclosure_registry.db")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ingest annual corporate disclosures from configured providers."
    )
    parser.add_argument(
        "--company",
        action="append",
        dest="companies",
        help="company_id to ingest (repeatable). Defaults to all enabled companies.",
    )
    parser.add_argument("--year-from", type=int)
    parser.add_argument("--year-to", type=int)
    parser.add_argument(
        "--graph",
        action="store_true",
        help="Run normalized English disclosures through the existing NLP/Neo4j pipeline.",
    )
    return parser.parse_args()


def build_company_registry() -> CompanyRegistry:
    return CompanyRegistry.from_seed_files(
        companies_path=COMPANIES_PATH,
        bindings_path=BINDINGS_PATH,
        sec_10k_targets_path=SEC_10K_PATH,
        sec_20f_targets_path=SEC_20F_PATH,
    )


async def async_main(args: argparse.Namespace) -> int:
    load_dotenv()
    company_registry = build_company_registry()
    source_registry = SourceRegistry.from_json(SOURCES_PATH)

    sec_user_agent = os.getenv("SEC_USER_AGENT", "").strip()
    if not sec_user_agent:
        raise RuntimeError(
            "SEC_USER_AGENT is required for the unified disclosure runner. "
            "Set it in .env before running ingestion."
        )

    sec_client = SECClient(user_agent=sec_user_agent)
    dart_provider = OpenDARTDisclosureProvider()
    ir_provider = InvestorRelationsDisclosureProvider()
    providers = [
        SECDisclosureProvider(sec_client),
        dart_provider,
        ir_provider,
    ]

    router = SourceRouter(
        company_registry=company_registry,
        source_registry=source_registry,
        providers=providers,
    )
    ingestion_service = DisclosureIngestionService(
        company_registry=company_registry,
        router=router,
        artifact_store=RawArtifactStore(RAW_ROOT),
        document_registry=DocumentRegistry(REGISTRY_DB),
        normalizers=NormalizerRegistry(),
        supported_languages={"en"},
    )

    graph_connection: Neo4jConnection | None = None
    graph_bridge: NormalizedDisclosureGraphBridge | None = None
    if args.graph:
        nlp = spacy.load("en_core_web_sm")
        relation_extractor = RelationExtractor(nlp)
        graph_connection = Neo4jConnection()
        graph_connection.verify_connection()
        repository = GraphIngestionRepository(graph_connection)
        graph_pipeline = GraphIngestionPipeline(repository)
        graph_service = DisclosureGraphIngestionService(
            relation_extractor=relation_extractor,
            graph_pipeline=graph_pipeline,
        )
        graph_bridge = NormalizedDisclosureGraphBridge(
            company_registry=company_registry,
            graph_service=graph_service,
        )

    try:
        if args.companies:
            all_results = []
            for company_id in args.companies:
                all_results.extend(
                    await ingestion_service.ingest_company(
                        company_id,
                        year_from=args.year_from,
                        year_to=args.year_to,
                    )
                )
        else:
            all_results = await ingestion_service.ingest_enabled_companies(
                year_from=args.year_from,
                year_to=args.year_to,
                max_concurrency=int(
                    os.getenv("DISCLOSURE_MAX_CONCURRENCY", "8")
                ),
            )

        graph_totals = {"attempted": 0, "inserted": 0, "rejected": 0}
        if graph_bridge is not None:
            for result in all_results:
                if result.normalized is None:
                    continue
                counts = graph_bridge.ingest(result.normalized)
                for key in graph_totals:
                    graph_totals[key] += counts[key]

        succeeded = sum(
            result.status.value.startswith("normalized")
            or result.duplicate
            for result in all_results
        )
        failed = sum(result.error is not None for result in all_results)
        unsupported = sum(
            result.status.value == "normalized_unsupported_language"
            for result in all_results
        )

        print()
        print("===== CORPORATE DISCLOSURE INGESTION =====")
        print(f"Results: {len(all_results)}")
        print(f"Successful/duplicate: {succeeded}")
        print(f"Unsupported-language normalized: {unsupported}")
        print(f"Failed: {failed}")
        if args.graph:
            print(f"Graph attempted: {graph_totals['attempted']}")
            print(f"Graph inserted: {graph_totals['inserted']}")
            print(f"Graph rejected: {graph_totals['rejected']}")
        print(f"Registry DB: {REGISTRY_DB}")
        print("==========================================")
        return 1 if failed else 0
    finally:
        await sec_client.close()
        await dart_provider.close()
        await ir_provider.close()
        if graph_connection is not None:
            graph_connection.close()


def main() -> None:
    args = parse_args()
    raise SystemExit(asyncio.run(async_main(args)))


if __name__ == "__main__":
    main()
