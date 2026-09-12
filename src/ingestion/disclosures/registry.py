from __future__ import annotations

import json
from pathlib import Path

from .models import Company, CompanyIdentifier, CompanySourceBinding, DisclosureSource


class CompanyRegistry:
    def __init__(
        self,
        companies: list[Company],
        bindings: list[CompanySourceBinding] | None = None,
    ) -> None:
        self._companies = {company.company_id: company for company in companies}
        self._bindings = list(bindings or [])

    @classmethod
    def from_seed_files(
        cls,
        *,
        companies_path: Path,
        bindings_path: Path | None = None,
        sec_10k_targets_path: Path | None = None,
        sec_20f_targets_path: Path | None = None,
    ) -> "CompanyRegistry":
        raw_companies = json.loads(companies_path.read_text(encoding="utf-8"))
        identifier_map: dict[str, list[CompanyIdentifier]] = {}
        bindings: list[CompanySourceBinding] = []

        def load_sec_targets(path: Path | None, family: str) -> None:
            if path is None or not path.exists():
                return
            for row in json.loads(path.read_text(encoding="utf-8")):
                company_id = row["company_id"]
                cik = str(row["cik"]).zfill(10)
                identifier_map.setdefault(company_id, []).append(
                    CompanyIdentifier(namespace="SEC_CIK", value=cik)
                )
                bindings.append(
                    CompanySourceBinding(
                        company_id=company_id,
                        source_id="sec_edgar",
                        external_company_id=cik,
                        metadata={"document_family": family},
                    )
                )

        load_sec_targets(sec_10k_targets_path, "10-k")
        load_sec_targets(sec_20f_targets_path, "20-f")

        companies = [
            Company(
                company_id=row["company_id"],
                name=row.get("name"),
                legal_name=row.get("legal_name") or row["name"],
                aliases=[value for value in [row.get("name"), row.get("legal_name")] if value],
                industry_id=row.get("industry_id"),
                country_of_incorporation=row.get("country_of_incorporation"),
                headquarters_country=row.get("headquarters_country"),
                identifiers=identifier_map.get(row["company_id"], []),
                preferred_languages=row.get("preferred_languages", ["en"]),
                enabled=row.get("enabled", True),
            )
            for row in raw_companies
        ]

        if bindings_path is not None and bindings_path.exists():
            raw_bindings = json.loads(bindings_path.read_text(encoding="utf-8"))
            bindings.extend(CompanySourceBinding.model_validate(row) for row in raw_bindings)

        return cls(companies, bindings)

    def get(self, company_id: str) -> Company:
        try:
            return self._companies[company_id]
        except KeyError as exc:
            raise KeyError(f"Unknown company_id: {company_id}") from exc

    def enabled(self) -> list[Company]:
        return [company for company in self._companies.values() if company.enabled]

    def bindings_for(self, company_id: str) -> list[CompanySourceBinding]:
        return [
            binding
            for binding in self._bindings
            if binding.company_id == company_id and binding.enabled
        ]

    def all_bindings(self) -> list[CompanySourceBinding]:
        return list(self._bindings)


class SourceRegistry:
    def __init__(self, sources: list[DisclosureSource]) -> None:
        self._sources = {source.source_id: source for source in sources}

    @classmethod
    def from_json(cls, path: Path) -> "SourceRegistry":
        rows = json.loads(path.read_text(encoding="utf-8"))
        return cls([DisclosureSource.model_validate(row) for row in rows])

    def get(self, source_id: str) -> DisclosureSource:
        try:
            return self._sources[source_id]
        except KeyError as exc:
            raise KeyError(f"Unknown source_id: {source_id}") from exc

    def enabled(self) -> list[DisclosureSource]:
        return [source for source in self._sources.values() if source.enabled]
