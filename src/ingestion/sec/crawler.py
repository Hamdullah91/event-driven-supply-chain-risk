from __future__ import annotations

import asyncio
import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any

from .client import SECClient
from .models import CompanyTarget, DownloadResult, FilingMetadata


logger = logging.getLogger(__name__)

SUPPORTED_ANNUAL_FORMS = {"10-K", "20-F"}


class FilingNotFoundError(RuntimeError):
    pass


def _validate_form(form: str) -> str:
    normalized = form.strip().upper()
    if normalized not in SUPPORTED_ANNUAL_FORMS:
        raise ValueError(
            f"Unsupported SEC annual filing form: {form!r}. "
            f"Supported forms: {sorted(SUPPORTED_ANNUAL_FORMS)}"
        )
    return normalized


def find_form_in_filing_data(
    filing_data: dict[str, Any],
    *,
    form: str,
) -> dict[str, Any] | None:
    form = _validate_form(form)
    forms = filing_data.get("form", [])

    if not isinstance(forms, list):
        return None

    for index, filing_form in enumerate(forms):
        if filing_form != form:
            continue

        return {
            "accession_number": filing_data["accessionNumber"][index],
            "filing_date": filing_data["filingDate"][index],
            "report_date": filing_data["reportDate"][index],
            "primary_document": filing_data["primaryDocument"][index],
        }

    return None


def find_10k_in_filing_data(
    filing_data: dict[str, Any],
) -> dict[str, Any] | None:
    """Backward-compatible 10-K helper."""
    return find_form_in_filing_data(filing_data, form="10-K")


def find_latest_form(
    submissions: dict[str, Any],
    *,
    form: str,
) -> dict[str, Any]:
    form = _validate_form(form)
    recent = submissions.get("filings", {}).get("recent")

    if not isinstance(recent, dict):
        raise FilingNotFoundError(
            "SEC submissions response does not contain recent filings"
        )

    filing = find_form_in_filing_data(recent, form=form)
    if filing is not None:
        return filing

    raise FilingNotFoundError(
        f"No {form} filing found in recent SEC submissions"
    )


def find_latest_10k(
    submissions: dict[str, Any],
) -> dict[str, Any]:
    """Backward-compatible 10-K helper."""
    return find_latest_form(submissions, form="10-K")


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


async def find_latest_form_with_history(
    *,
    client: SECClient,
    submissions: dict[str, Any],
    form: str,
) -> dict[str, Any]:
    form = _validate_form(form)

    try:
        return find_latest_form(submissions, form=form)
    except FilingNotFoundError:
        logger.info(
            "No %s found in recent filings; checking historical submissions",
            form,
        )

    historical_files = submissions.get("filings", {}).get("files", [])
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

        logger.info("Checking historical SEC submissions file=%s", filename)
        filing_data = await client.get_submission_file(filename)
        filing = find_form_in_filing_data(filing_data, form=form)

        if filing is not None:
            logger.info(
                "Found %s in historical submissions accession=%s",
                form,
                filing["accession_number"],
            )
            return filing

    raise FilingNotFoundError(
        f"No {form} filing found in SEC submissions history"
    )


async def find_latest_10k_with_history(
    *,
    client: SECClient,
    submissions: dict[str, Any],
) -> dict[str, Any]:
    """Backward-compatible 10-K helper."""
    return await find_latest_form_with_history(
        client=client,
        submissions=submissions,
        form="10-K",
    )


def save_raw_filing(
    *,
    output_dir: Path,
    company: CompanyTarget,
    accession_number: str,
    primary_document: str,
    document: bytes,
    form: str = "10-K",
) -> Path:
    form = _validate_form(form)
    company_dir = output_dir / company.numeric_cik / accession_number
    company_dir.mkdir(parents=True, exist_ok=True)

    extension = Path(primary_document).suffix or ".htm"
    filename_stem = form.lower()
    output_path = company_dir / f"{filename_stem}{extension}"

    fd, temp_path = tempfile.mkstemp(
        dir=company_dir,
        prefix=f".{filename_stem}-",
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
    form: str = "10-K",
) -> tuple[FilingMetadata, Path]:
    form = _validate_form(form)
    company_dir = (
        output_dir
        / company.numeric_cik
        / filing["accession_number"]
    )
    company_dir.mkdir(parents=True, exist_ok=True)

    metadata = FilingMetadata.create(
        company_name=company.name,
        cik=company.normalized_cik,
        form=form,
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
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            file.write(metadata_json)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temp_path, metadata_path)
    except Exception:
        try:
            os.unlink(temp_path)
        except FileNotFoundError:
            pass
        raise

    return metadata, metadata_path


async def crawl_latest_filing(
    *,
    client: SECClient,
    company: CompanyTarget,
    output_dir: Path,
    form: str,
) -> DownloadResult:
    form = _validate_form(form)
    logger.info(
        "Starting SEC %s crawl company=%s cik=%s",
        form,
        company.name,
        company.normalized_cik,
    )

    submissions = await client.get_company_submissions(company.normalized_cik)
    filing = await find_latest_form_with_history(
        client=client,
        submissions=submissions,
        form=form,
    )

    logger.info(
        "Found %s company=%s accession=%s filing_date=%s",
        form,
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
        form=form,
    )
    metadata, metadata_path = save_metadata(
        output_dir=output_dir,
        company=company,
        filing=filing,
        source_url=source_url,
        form=form,
    )

    logger.info(
        "Completed SEC %s crawl company=%s document=%s metadata=%s",
        form,
        company.name,
        document_path,
        metadata_path,
    )

    return DownloadResult(
        metadata=metadata,
        document_path=document_path,
        metadata_path=metadata_path,
    )


async def crawl_latest_10k(
    *,
    client: SECClient,
    company: CompanyTarget,
    output_dir: Path,
) -> DownloadResult:
    """Backward-compatible 10-K wrapper."""
    return await crawl_latest_filing(
        client=client,
        company=company,
        output_dir=output_dir,
        form="10-K",
    )


async def crawl_many(
    *,
    client: SECClient,
    companies: list[CompanyTarget],
    output_dir: Path,
    max_concurrency: int = 3,
    form: str = "10-K",
) -> list[tuple[CompanyTarget, DownloadResult | Exception]]:
    form = _validate_form(form)
    if max_concurrency <= 0:
        raise ValueError("max_concurrency must be greater than zero")

    semaphore = asyncio.Semaphore(max_concurrency)

    async def crawl_one(
        company: CompanyTarget,
    ) -> tuple[CompanyTarget, DownloadResult | Exception]:
        async with semaphore:
            try:
                result = await crawl_latest_filing(
                    client=client,
                    company=company,
                    output_dir=output_dir,
                    form=form,
                )
                return company, result
            except Exception as exc:
                logger.exception(
                    "SEC %s crawl failed company=%s cik=%s",
                    form,
                    company.name,
                    company.normalized_cik,
                )
                return company, exc

    return await asyncio.gather(
        *(crawl_one(company) for company in companies)
    )
