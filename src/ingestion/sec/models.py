from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class CompanyTarget:
    name: str
    cik: str

    @property
    def normalized_cik(self) -> str:
        digits = self.cik.strip().lstrip("0")

        if not digits.isdigit():
            raise ValueError(
                f"Invalid CIK for {self.name!r}: {self.cik!r}"
            )

        return digits.zfill(10)

    @property
    def numeric_cik(self) -> str:
        return str(int(self.normalized_cik))


@dataclass(frozen=True, slots=True)
class FilingMetadata:
    company_name: str
    cik: str
    form: str
    accession_number: str
    filing_date: str
    report_date: str | None
    primary_document: str
    source_url: str
    downloaded_at: str

    @classmethod
    def create(
        cls,
        *,
        company_name: str,
        cik: str,
        form: str,
        accession_number: str,
        filing_date: str,
        report_date: str | None,
        primary_document: str,
        source_url: str,
    ) -> "FilingMetadata":
        return cls(
            company_name=company_name,
            cik=cik,
            form=form,
            accession_number=accession_number,
            filing_date=filing_date,
            report_date=report_date,
            primary_document=primary_document,
            source_url=source_url,
            downloaded_at=datetime.now(timezone.utc).isoformat(),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class DownloadResult:
    metadata: FilingMetadata
    document_path: Path
    metadata_path: Path