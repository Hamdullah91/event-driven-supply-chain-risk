from __future__ import annotations

import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

from scripts.crawl_sec import configure_logging, load_companies
from src.ingestion.sec.client import SECClient
from src.ingestion.sec.crawler import crawl_many


OUTPUT_DIR = Path("data/raw/sec")
TARGETS_PATH = Path("data/seed/sec_20f_targets.json")
DEFAULT_MAX_CONCURRENCY = 3


async def main() -> None:
    load_dotenv(dotenv_path=".env")
    configure_logging()

    companies = load_companies(TARGETS_PATH)

    async with SECClient(
        user_agent=os.environ["SEC_USER_AGENT"],
        requests_per_second=float(
            os.getenv("SEC_REQUESTS_PER_SECOND", "8")
        ),
        max_retries=int(os.getenv("SEC_MAX_RETRIES", "5")),
        timeout_seconds=float(os.getenv("SEC_TIMEOUT_SECONDS", "30")),
    ) as client:
        results = await crawl_many(
            client=client,
            companies=companies,
            output_dir=OUTPUT_DIR,
            max_concurrency=DEFAULT_MAX_CONCURRENCY,
            form="20-F",
        )

    success_count = 0
    failure_count = 0

    for company, result in results:
        if isinstance(result, Exception):
            failure_count += 1
            print(f"FAILED: {company.name} -> {result}")
            continue

        success_count += 1
        print(f"SUCCESS: {company.name}")
        print(f"  Form: {result.metadata.form}")
        print(f"  Document: {result.document_path}")
        print(f"  Metadata: {result.metadata_path}")
        print(f"  Filing date: {result.metadata.filing_date}")

    print()
    print("SEC 20-F crawl summary")
    print(f"  Successful: {success_count}")
    print(f"  Failed: {failure_count}")
    print(f"  Total: {len(results)}")

    if failure_count:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
