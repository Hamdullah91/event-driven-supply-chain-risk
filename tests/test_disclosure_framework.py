from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from src.ingestion.disclosures.models import (
    Company,
    CompanySourceBinding,
    DisclosureSource,
    DocumentFamily,
    RawArtifact,
    RemoteDocument,
    SourceAuthority,
)
from src.ingestion.disclosures.normalizers import HTMLNormalizer, NormalizerRegistry
from src.ingestion.disclosures.providers.base import DisclosureProvider
from src.ingestion.disclosures.providers.ir import InvestorRelationsDisclosureProvider
from src.ingestion.disclosures.registry import CompanyRegistry, SourceRegistry
from src.ingestion.disclosures.router import SourceRouter
from src.ingestion.disclosures.service import DisclosureIngestionService
from src.ingestion.disclosures.storage import DocumentRegistry, RawArtifactStore


ROOT = Path(__file__).resolve().parents[1]


def production_registry() -> CompanyRegistry:
    return CompanyRegistry.from_seed_files(
        companies_path=ROOT / "data/seed/companies.json",
        bindings_path=ROOT / "data/seed/disclosure_source_bindings.json",
        sec_10k_targets_path=ROOT / "data/seed/sec_10k_targets.json",
        sec_20f_targets_path=ROOT / "data/seed/sec_20f_targets.json",
    )


def test_all_50_baseline_companies_have_disclosure_routes() -> None:
    registry = production_registry()
    companies = registry.enabled()

    assert len(companies) == 50
    missing = [
        company.company_id
        for company in companies
        if not registry.bindings_for(company.company_id)
    ]
    assert missing == []


def test_every_company_binding_references_registered_source() -> None:
    registry = production_registry()
    sources = SourceRegistry.from_json(ROOT / "data/seed/disclosure_sources.json")

    for binding in registry.all_bindings():
        assert sources.get(binding.source_id).enabled


def test_nxp_is_now_configured_as_sec_10k() -> None:
    registry = production_registry()
    nxp = registry.get("nxp")

    assert nxp.identifier("SEC_CIK") == "0001413447"
    bindings = registry.bindings_for("nxp")
    assert any(
        binding.source_id == "sec_edgar"
        and binding.metadata.get("document_family") == "10-k"
        for binding in bindings
    )


def test_korean_baseline_companies_have_opendart_bindings() -> None:
    registry = production_registry()
    expected = {
        "samsung_electronics",
        "sk_hynix",
        "lg_energy_solution",
        "samsung_sdi",
        "sk_on",
    }
    configured = {
        company_id
        for company_id in expected
        if any(
            binding.source_id == "opendart"
            for binding in registry.bindings_for(company_id)
        )
    }
    assert configured == expected


def test_html_normalizer_preserves_provenance_and_semantic_sections() -> None:
    document = RemoteDocument(
        source_id="test_provider",
        provider_document_id="doc-1",
        company_id="example",
        document_family=DocumentFamily.ANNUAL_REPORT,
        title="Example Annual Report",
        source_url="https://example.com/report.html",
        reporting_year=2025,
        language="en",
    )
    artifact = RawArtifact(
        metadata=document,
        content=(
            b"<html><body><h2>Supply Chain</h2>"
            b"<p>We depend on a small number of suppliers.</p>"
            b"<h2>Manufacturing</h2><p>We operate three plants.</p>"
            b"</body></html>"
        ),
        mime_type="text/html",
    )

    normalized = HTMLNormalizer().normalize(artifact)

    assert normalized.company_id == "example"
    assert normalized.provider_document_id == "doc-1"
    assert normalized.source_url == "https://example.com/report.html"
    assert normalized.document_family == DocumentFamily.ANNUAL_REPORT
    assert "suppliers" in normalized.full_text
    assert [section.semantic_role for section in normalized.sections] == [
        "SUPPLY_CHAIN",
        "MANUFACTURING",
    ]


def test_ir_provider_rejects_cross_domain_links_and_scores_reports() -> None:
    assert InvestorRelationsDisclosureProvider._same_domain(
        "https://company.example/investors",
        "https://company.example/reports/report.pdf",
    )
    assert not InvestorRelationsDisclosureProvider._same_domain(
        "https://company.example/investors",
        "https://untrusted.example/report.pdf",
    )
    assert InvestorRelationsDisclosureProvider._score_candidate(
        "Annual Report 2025",
        "/investors/annual-report-2025.pdf",
        {2025},
    ) >= 35
    assert InvestorRelationsDisclosureProvider._score_candidate(
        "Quarterly presentation",
        "/q3-presentation.pdf",
        {2025},
    ) < 35


class FakeProvider(DisclosureProvider):
    def __init__(
        self,
        provider_id: str = "fake",
        provider_document_id: str = "fake-2025",
        source_url: str = "https://example.com/report.html",
    ) -> None:
        self.provider_id = provider_id
        self.provider_document_id = provider_document_id
        self.source_url = source_url

    def supports(self, company, binding) -> bool:
        return bool(binding and binding.source_id == self.provider_id)

    async def discover_documents(
        self,
        company,
        binding,
        *,
        year_from=None,
        year_to=None,
    ):
        return [
            RemoteDocument(
                source_id=self.provider_id,
                provider_document_id=self.provider_document_id,
                company_id=company.company_id,
                document_family=DocumentFamily.ANNUAL_REPORT,
                source_url=self.source_url,
                filing_date=date(2026, 3, 1),
                reporting_year=2025,
                language="en",
            )
        ]

    async def fetch_document(self, document):
        return RawArtifact(
            metadata=document,
            content=b"<h1>Business</h1><p>Example manufactures components.</p>",
            mime_type="text/html",
        )


def build_fake_service(
    tmp_path: Path,
    *,
    providers: list[FakeProvider],
    bindings: list[CompanySourceBinding],
) -> tuple[DisclosureIngestionService, DocumentRegistry]:
    company = Company(company_id="example", legal_name="Example Corp")
    company_registry = CompanyRegistry([company], bindings)
    source_registry = SourceRegistry(
        [
            DisclosureSource(
                source_id=provider.provider_id,
                display_name=provider.provider_id,
                provider_type="fake",
                authority=SourceAuthority.ISSUER,
                default_priority=index + 1,
            )
            for index, provider in enumerate(providers)
        ]
    )
    router = SourceRouter(
        company_registry=company_registry,
        source_registry=source_registry,
        providers=providers,
    )
    registry = DocumentRegistry(tmp_path / "registry.db")
    return (
        DisclosureIngestionService(
            company_registry=company_registry,
            router=router,
            artifact_store=RawArtifactStore(tmp_path / "raw"),
            document_registry=registry,
            normalizers=NormalizerRegistry(),
        ),
        registry,
    )


@pytest.mark.asyncio
async def test_ingestion_service_deduplicates_same_source_occurrence(
    tmp_path: Path,
) -> None:
    provider = FakeProvider()
    service, _ = build_fake_service(
        tmp_path,
        providers=[provider],
        bindings=[CompanySourceBinding(company_id="example", source_id="fake")],
    )

    first = await service.ingest_company("example")
    second = await service.ingest_company("example")

    assert first[0].normalized is not None
    assert first[0].duplicate is False
    assert second[0].duplicate is True
    assert second[0].normalized is not None


@pytest.mark.asyncio
async def test_identical_bytes_from_two_sources_keep_two_representations(
    tmp_path: Path,
) -> None:
    first_provider = FakeProvider(
        provider_id="regulator",
        provider_document_id="reg-2025",
        source_url="https://regulator.example/report",
    )
    second_provider = FakeProvider(
        provider_id="issuer",
        provider_document_id="issuer-2025",
        source_url="https://issuer.example/report",
    )
    service, registry = build_fake_service(
        tmp_path,
        providers=[first_provider, second_provider],
        bindings=[
            CompanySourceBinding(company_id="example", source_id="regulator"),
            CompanySourceBinding(company_id="example", source_id="issuer"),
        ],
    )

    results = await service.ingest_company("example")

    assert len(results) == 2
    assert all(result.normalized is not None for result in results)
    first_row = registry.representation_by_occurrence(
        source_id="regulator",
        provider_document_id="reg-2025",
        source_url="https://regulator.example/report",
    )
    second_row = registry.representation_by_occurrence(
        source_id="issuer",
        provider_document_id="issuer-2025",
        source_url="https://issuer.example/report",
    )
    assert first_row is not None
    assert second_row is not None
    assert first_row["content_sha256"] == second_row["content_sha256"]
    assert first_row["representation_id"] != second_row["representation_id"]
