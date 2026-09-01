from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

from src.ingestion.sec.client import SECClient
from src.ingestion.sec.crawler import crawl_many
from src.ingestion.sec.models import CompanyTarget


OUTPUT_DIR = Path("data/raw/sec")
LOG_DIR = Path("data/logs")

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


def load_companies() -> list[CompanyTarget]:
    return [
        CompanyTarget(
            name="Apple Inc.",
            cik="320193",
        ),
        CompanyTarget(
            name="NVIDIA Corporation",
            cik="1045810",
        ),
        CompanyTarget(
            name="Advanced Micro Devices, Inc.",
            cik="2488",
        ),
    ]


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