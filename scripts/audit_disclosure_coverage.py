from __future__ import annotations

from collections import Counter
from pathlib import Path

from src.ingestion.disclosures.registry import CompanyRegistry, SourceRegistry


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    registry = CompanyRegistry.from_seed_files(
        companies_path=ROOT / "data/seed/companies.json",
        bindings_path=ROOT / "data/seed/disclosure_source_bindings.json",
        sec_10k_targets_path=ROOT / "data/seed/sec_10k_targets.json",
        sec_20f_targets_path=ROOT / "data/seed/sec_20f_targets.json",
    )
    sources = SourceRegistry.from_json(
        ROOT / "data/seed/disclosure_sources.json"
    )

    companies = registry.enabled()
    missing: list[str] = []
    invalid_sources: list[str] = []
    provider_counts: Counter[str] = Counter()

    for company in companies:
        bindings = registry.bindings_for(company.company_id)
        if not bindings:
            missing.append(company.company_id)
            continue

        for binding in bindings:
            try:
                source = sources.get(binding.source_id)
            except KeyError:
                invalid_sources.append(
                    f"{company.company_id}:{binding.source_id}"
                )
                continue
            if not source.enabled:
                invalid_sources.append(
                    f"{company.company_id}:{binding.source_id}:disabled"
                )
                continue
            provider_counts[binding.source_id] += 1

    print("===== DISCLOSURE COVERAGE AUDIT =====")
    print(f"Baseline companies: {len(companies)}")
    print(
        "Companies with at least one source route: "
        f"{len(companies) - len(missing)}"
    )
    print(f"Companies without a source route: {len(missing)}")
    print(f"Invalid/disabled source bindings: {len(invalid_sources)}")
    print()
    print("Configured routes by provider:")
    for source_id, count in sorted(provider_counts.items()):
        print(f"  {source_id}: {count}")

    if missing:
        print()
        print("Missing company routes:")
        for company_id in missing:
            print(f"  - {company_id}")

    if invalid_sources:
        print()
        print("Invalid source bindings:")
        for value in invalid_sources:
            print(f"  - {value}")

    print("=====================================")
    if missing or invalid_sources:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
