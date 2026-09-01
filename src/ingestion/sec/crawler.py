from __future__ import annotations

from typing import Any

from .models import CompanyTarget, DownloadResult, FilingMetadata

from .client import SECClient

import os
import tempfile
from pathlib import Path
import json
import logging
import asyncio

logger = logging.getLogger(__name__)

class FilingNotFoundError(RuntimeError):
    pass

def find_10k_in_filing_data(
    filing_data: dict[str, Any],
) -> dict[str, Any] | None:
    forms = filing_data.get("form", [])

    if not isinstance(forms, list):
        return None

    for index, form in enumerate(forms):
        if form != "10-K":
            continue

        return {
            "accession_number": filing_data["accessionNumber"][index],
            "filing_date": filing_data["filingDate"][index],
            "report_date": filing_data["reportDate"][index],
            "primary_document": filing_data["primaryDocument"][index],
        }

    return None
def find_latest_10k(
    submissions: dict[str, Any],
) -> dict[str, Any]:
    recent = submissions.get(
        "filings",
        {},
    ).get("recent")

    if not isinstance(recent, dict):
        raise FilingNotFoundError(
            "SEC submissions response does not contain recent filings"
        )

    filing = find_10k_in_filing_data(recent)

    if filing is not None:
        return filing

    raise FilingNotFoundError(
        "No 10-K filing found in recent SEC submissions"
    )
def build_archive_url(
    *,
    company: CompanyTarget,
    accession_number: str,
    primary_document: str,
) -> str:
    accession_without_dashes = accession_number.replace("-", "")

    return (
        "https://www.sec.gov/Archives/edgar/data/"
        f"{company.numeric_cik}/"
        f"{accession_without_dashes}/"
        f"{primary_document}"
    )

async def find_latest_10k_with_history(
    *,
    client: SECClient,
    submissions: dict[str, Any],
) -> dict[str, Any]:
    try:
        return find_latest_10k(submissions)

    except FilingNotFoundError:
        logger.info(
            "No 10-K found in recent filings; checking historical submissions"
        )

    historical_files = (
        submissions.get("filings", {}).get("files", [])
    )

    if not isinstance(historical_files, list):
        raise FilingNotFoundError(
            "SEC historical filing list is invalid"
        )

    for historical_file in historical_files:
        if not isinstance(historical_file, dict):
            continue

        filename = historical_file.get("name")

        if not filename:
            continue

        logger.info(
            "Checking historical SEC submissions file=%s",
            filename,
        )

        filing_data = await client.get_submission_file(
            filename
        )

        filing = find_10k_in_filing_data(
            filing_data
        )

        if filing is not None:
            logger.info(
                "Found 10-K in historical submissions accession=%s",
                filing["accession_number"],
            )
            return filing

    raise FilingNotFoundError(
        "No 10-K filing found in SEC submissions history"
    )

def save_raw_filing(
    *,
    output_dir: Path,
    company: CompanyTarget,
    accession_number: str,
    primary_document: str,
    document: bytes,
) -> Path:
    company_dir = (
        output_dir
        / company.numeric_cik
        / accession_number
    )

    company_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    extension = Path(primary_document).suffix or ".htm"

    output_path = company_dir / f"10-k{extension}"

    fd, temp_path = tempfile.mkstemp(
        dir=company_dir,
        prefix=".10-k-",
        suffix=".tmp",
    )

    try:
        with os.fdopen(fd, "wb") as file:
            file.write(document)
            file.flush()
            os.fsync(file.fileno())

        os.replace(temp_path, output_path)

    except Exception:
        try:
            os.unlink(temp_path)
        except FileNotFoundError:
            pass

        raise

    return output_path

def save_metadata(
    *,
    output_dir: Path,
    company: CompanyTarget,
    filing: dict[str, Any],
    source_url: str,
) -> tuple[FilingMetadata, Path]:
    company_dir = (
        output_dir
        / company.numeric_cik
        / filing["accession_number"]
    )

    company_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    metadata = FilingMetadata.create(
        company_name=company.name,
        cik=company.normalized_cik,
        form="10-K",
        accession_number=filing["accession_number"],
        filing_date=filing["filing_date"],
        report_date=filing["report_date"],
        primary_document=filing["primary_document"],
        source_url=source_url,
    )

    metadata_path = company_dir / "metadata.json"

    metadata_json = json.dumps(
        metadata.to_dict(),
        indent=2,
        ensure_ascii=False,
    )

    fd, temp_path = tempfile.mkstemp(
        dir=company_dir,
        prefix=".metadata-",
        suffix=".tmp",
    )

    try:
        with os.fdopen(
            fd,
            "w",
            encoding="utf-8",
        ) as file:
            file.write(metadata_json)
            file.flush()
            os.fsync(file.fileno())

        os.replace(
            temp_path,
            metadata_path,
        )

    except Exception:
        try:
            os.unlink(temp_path)
        except FileNotFoundError:
            pass

        raise

    return metadata, metadata_path

async def crawl_latest_10k(
    *,
    client: SECClient,
    company: CompanyTarget,
    output_dir: Path,
) -> DownloadResult:
    logger.info(
        "Starting SEC 10-K crawl company=%s cik=%s",
        company.name,
        company.normalized_cik,
    )

    submissions = await client.get_company_submissions(
        company.normalized_cik
    )

    filing = await find_latest_10k_with_history(
        client=client,
        submissions=submissions,
    )
    logger.info(
        "Found 10-K company=%s accession=%s filing_date=%s",
        company.name,
        filing["accession_number"],
        filing["filing_date"],
    )

    source_url = build_archive_url(
        company=company,
        accession_number=filing["accession_number"],
        primary_document=filing["primary_document"],
    )

    document = await client.get_bytes(source_url)

    document_path = save_raw_filing(
        output_dir=output_dir,
        company=company,
        accession_number=filing["accession_number"],
        primary_document=filing["primary_document"],
        document=document,
    )

    metadata, metadata_path = save_metadata(
        output_dir=output_dir,
        company=company,
        filing=filing,
        source_url=source_url,
    )

    logger.info(
        "Completed SEC 10-K crawl company=%s document=%s metadata=%s",
        company.name,
        document_path,
        metadata_path,
    )

    return DownloadResult(
        metadata=metadata,
        document_path=document_path,
        metadata_path=metadata_path,
    )


async def crawl_many(
    *,
    client: SECClient,
    companies: list[CompanyTarget],
    output_dir: Path,
    max_concurrency: int = 3,
) -> list[
    tuple[CompanyTarget, DownloadResult | Exception]
]:
    if max_concurrency <= 0:
        raise ValueError(
            "max_concurrency must be greater than zero"
        )
    semaphore = asyncio.Semaphore(max_concurrency)

    async def crawl_one(
        company: CompanyTarget,
    ) -> tuple[
            CompanyTarget,
            DownloadResult | Exception,
        ]:
        async with semaphore:
            try:
                result = await crawl_latest_10k(
                    client=client,
                    company=company,
                    output_dir=output_dir,
                )

                return company, result

            except Exception as exc:
                logger.exception(
                    "SEC crawl failed company=%s cik=%s",
                    company.name,
                    company.normalized_cik,
                )

                return company, exc

    return await asyncio.gather(
        *(crawl_one(company) for company in companies)
    )