from __future__ import annotations

import asyncio

import pytest

from src.ingestion.sec.crawler import (
    FilingNotFoundError,
    find_latest_10k,
    find_latest_10k_with_history,
)
from src.ingestion.sec.models import CompanyTarget



class FakeSECClient:
    async def get_submission_file(
        self,
        filename: str,
    ) -> dict:
        return {
            "form": ["8-K", "10-K"],
            "accessionNumber": [
                "0000000000-26-000001",
                "0000000000-25-000099",
            ],
            "filingDate": [
                "2026-01-15",
                "2025-03-01",
            ],
            "reportDate": [
                "2026-01-15",
                "2024-12-31",
            ],
            "primaryDocument": [
                "example-8k.htm",
                "example-10k.htm",
            ],
        }


def test_historical_10k_fallback() -> None:
    submissions = {
        "filings": {
            "recent": {
                "form": ["8-K", "10-Q"],
                "accessionNumber": [
                    "0000000000-26-000010",
                    "0000000000-26-000011",
                ],
                "filingDate": [
                    "2026-08-01",
                    "2026-07-01",
                ],
                "reportDate": [
                    "2026-08-01",
                    "2026-06-30",
                ],
                "primaryDocument": [
                    "recent-8k.htm",
                    "recent-10q.htm",
                ],
            },
            "files": [
                {
                    "name": "CIK0000000000-submissions-001.json",
                }
            ],
        }
    }

    filing = asyncio.run(
        find_latest_10k_with_history(
            client=FakeSECClient(),
            submissions=submissions,
        )
    )

    assert filing["accession_number"] == (
        "0000000000-25-000099"
    )

    assert filing["filing_date"] == "2025-03-01"

    assert filing["report_date"] == "2024-12-31"

    assert filing["primary_document"] == (
        "example-10k.htm"
    )


def test_find_latest_10k_from_recent_filings() -> None:
    submissions = {
        "filings": {
            "recent": {
                "form": ["8-K", "10-K", "10-Q"],
                "accessionNumber": [
                    "test-8k",
                    "test-10k",
                    "test-10q",
                ],
                "filingDate": [
                    "2026-08-01",
                    "2026-02-25",
                    "2026-05-01",
                ],
                "reportDate": [
                    "2026-08-01",
                    "2026-01-31",
                    "2026-04-30",
                ],
                "primaryDocument": [
                    "8k.htm",
                    "annual-report.htm",
                    "10q.htm",
                ],
            }
        }
    }

    filing = find_latest_10k(submissions)

    assert filing["accession_number"] == "test-10k"
    assert filing["filing_date"] == "2026-02-25"
    assert filing["report_date"] == "2026-01-31"
    assert filing["primary_document"] == "annual-report.htm"


def test_no_10k_raises_filing_not_found() -> None:
    submissions = {
        "filings": {
            "recent": {
                "form": ["8-K", "10-Q"],
                "accessionNumber": [
                    "test-8k",
                    "test-10q",
                ],
                "filingDate": [
                    "2026-08-01",
                    "2026-07-01",
                ],
                "reportDate": [
                    "2026-08-01",
                    "2026-06-30",
                ],
                "primaryDocument": [
                    "8k.htm",
                    "10q.htm",
                ],
            },
            "files": [],
        }
    }

    with pytest.raises(
        FilingNotFoundError,
        match="No 10-K filing found",
    ):
        asyncio.run(
            find_latest_10k_with_history(
                client=FakeSECClient(),
                submissions=submissions,
            )
        )


def test_company_target_cik_normalization() -> None:
    company = CompanyTarget(
        name="Apple Inc.",
        cik="320193",
    )

    assert company.normalized_cik == "0000320193"
    assert company.numeric_cik == "320193"


def test_invalid_cik_raises_value_error() -> None:
    company = CompanyTarget(
        name="Invalid Company",
        cik="ABC123",
    )

    with pytest.raises(
        ValueError,
        match="Invalid CIK",
    ):
        _ = company.normalized_cik