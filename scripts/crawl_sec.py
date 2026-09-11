from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

from src.ingestion.sec.client import SECClient
from src.ingestion.sec.crawler import crawl_many
from src.ingestion.sec.models import CompanyTarget


OUTPUT_DIR = Path("data/raw/sec")
LOG_DIR = Path("data/logs")
TARGETS_PATH = Path("data/seed/sec_10k_targets.json")

DEFAULT_MAX_CONCURRENCY = 3


def configure_logging() -> None:
    LOG_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    log_file = LOG_DIR / "sec_crawler.log"

    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s | %(levelname)s | "
            "%(name)s | %(message)s"
        ),
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(
                log_file,
                encoding="utf-8",
            ),
        ],
    )

    logging.getLogger("httpx").setLevel(
        logging.WARNING
    )


def load_companies(
    path: Path = TARGETS_PATH,
) -> list[CompanyTarget]:
    """
    Load SEC 10-K crawl targets from a data file.

    The registry intentionally contains only core companies that
    are expected to file Form 10-K with the SEC. Foreign/private
    companies remain in the baseline KG but are not forced through
    the 10-K crawler.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"SEC target registry not found: {path}"
        )

    raw_targets = json.loads(
        path.read_text(encoding="utf-8")
    )

    if not isinstance(raw_targets, list):
        raise ValueError(
            "SEC target registry must contain a JSON list."
        )

    companies: list[CompanyTarget] = []
    seen_ciks: set[str] = set()

    for item in raw_targets:
        if not isinstance(item, dict):
            raise ValueError(
                "Each SEC target must be a JSON object."
            )

        name = str(item.get("name", "")).strip()
        cik = str(item.get("cik", "")).strip()

        if not name or not cik:
            raise ValueError(
                f"SEC target requires name and cik: {item!r}"
            )

        company = CompanyTarget(
            name=name,
            cik=cik,
        )

        normalized_cik = company.normalized_cik

        if normalized_cik in seen_ciks:
            raise ValueError(
                f"Duplicate SEC CIK in target registry: {cik}"
            )

        seen_ciks.add(normalized_cik)
        companies.append(company)

    if not companies:
        raise ValueError(
            "SEC target registry cannot be empty."
        )

    return companies


async def main() -> None:
    load_dotenv(
        dotenv_path=".env"
    )

    configure_logging()

    companies = load_companies()

    async with SECClient(
        user_agent=os.environ[
            "SEC_USER_AGENT"
        ],
        requests_per_second=float(
            os.getenv(
                "SEC_REQUESTS_PER_SECOND",
                "8",
            )
        ),
        max_retries=int(
            os.getenv(
                "SEC_MAX_RETRIES",
                "5",
            )
        ),
        timeout_seconds=float(
            os.getenv(
                "SEC_TIMEOUT_SECONDS",
                "30",
            )
        ),
    ) as client:
        results = await crawl_many(
            client=client,
            companies=companies,
            output_dir=OUTPUT_DIR,
            max_concurrency=(
                DEFAULT_MAX_CONCURRENCY
            ),
        )

    success_count = 0
    failure_count = 0

    for company, result in results:
        if isinstance(
            result,
            Exception,
        ):
            failure_count += 1

            print(
                f"FAILED: "
                f"{company.name} "
                f"-> {result}"
            )

            continue

        success_count += 1

        print(
            f"SUCCESS: "
            f"{company.name}"
        )
        print(
            f"  Document: "
            f"{result.document_path}"
        )
        print(
            f"  Metadata: "
            f"{result.metadata_path}"
        )
        print(
            f"  Filing date: "
            f"{result.metadata.filing_date}"
        )

    print()
    print(
        "SEC crawl summary"
    )
    print(
        f"  Successful: "
        f"{success_count}"
    )
    print(
        f"  Failed: "
        f"{failure_count}"
    )
    print(
        f"  Total: "
        f"{len(results)}"
    )


if __name__ == "__main__":
    asyncio.run(main())
