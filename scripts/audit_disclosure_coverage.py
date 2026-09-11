from __future__ import annotations

from collections import Counter
from pathlib import Path

from src.ingestion.disclosures.registry import CompanyRegistry


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    registry = CompanyRegistry.from_seed_files(
        companies_path=ROOT / "data/seed/companies.json",
        bindings_path=ROOT / "data/seed/disclosure_source_bindings.json",
        sec_10k_targets_path=ROOT / "data/seed/sec_10k_targets.json",
        sec_20f_targets_path=ROOT / "data/seed/sec_20f_targets.json",
    )

    companies = registry.enabled()
    missing: list[str] = []
    provider_counts: Counter[str] = Counter()

    for company in companies:
        bindings = registry.bindings_for(company.company_id)
        if not bindings:
            missing.append(company.company_id)
            continue
        provider_counts.update(binding.source_id for binding in bindings)

    print("===== DISCLOSURE COVERAGE AUDIT =====")
    print(f"Baseline companies: {len(companies)}")
    print(f"Companies with at least one source route: {len(companies) - len(missing)}")
    print(f"Companies without a source route: {len(missing)}")
    print()
    print("Configured routes by provider:")
    for source_id, count in sorted(provider_counts.items()):
        print(f"  {source_id}: {count}")

    if missing:
        print()
        print("Missing company routes:")
        for company_id in missing:
            print(f"  - {company_id}")
        raise SystemExit(1)

    print("=====================================")


if __name__ == "__main__":
    main()
