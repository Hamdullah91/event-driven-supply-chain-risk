from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import spacy

from src.graph.ingestion.resolution import resolve_graph_candidates
from src.nlp.triplet_extractor import TripletExtractor


PROCESSED_SEC_ROOT = Path("data/processed/sec")


def main() -> None:
    processed_files = sorted(
        PROCESSED_SEC_ROOT.rglob("processed.json")
    )

    if not processed_files:
        raise FileNotFoundError(
            f"No processed SEC filings found under {PROCESSED_SEC_ROOT}"
        )

    nlp = spacy.load("en_core_web_sm")
    extractor = TripletExtractor(nlp)

    global_type_counts: Counter[tuple[str, str, str]] = Counter()
    total_raw = 0
    total_resolved = 0

    for processed_file in processed_files:
        filing = json.loads(
            processed_file.read_text(encoding="utf-8")
        )

        raw_candidates = []

        for section in filing.get("sections", []):
            for chunk in section.get("chunks", []):
                text = chunk.get("text", "").strip()
                if text:
                    raw_candidates.extend(
                        extractor.extract(text)
                    )

        resolved_candidates = resolve_graph_candidates(
            raw_candidates,
            filing_company=filing["company_name"],
        )

        type_counts = Counter(
            (
                candidate.relationship,
                candidate.subject_type,
                candidate.object_type,
            )
            for candidate in resolved_candidates
        )

        global_type_counts.update(type_counts)
        total_raw += len(raw_candidates)
        total_resolved += len(resolved_candidates)

        print()
        print("=" * 80)
        print(f"Company: {filing['company_name']}")
        print(f"Accession: {filing['accession_number']}")
        print(f"Raw triplets: {len(raw_candidates)}")
        print(f"Resolved graph candidates: {len(resolved_candidates)}")

        print("Resolved candidate type counts:")
        if type_counts:
            for (
                relationship,
                subject_type,
                object_type,
            ), count in sorted(type_counts.items()):
                print(
                    f"  {relationship} | "
                    f"{subject_type} -> {object_type}: {count}"
                )
        else:
            print("  none")

        print(
            "AUDIT_SUMMARY | "
            f"company={filing['company_name']} | "
            f"raw={len(raw_candidates)} | "
            f"resolved={len(resolved_candidates)}"
        )
        for (
            relationship,
            subject_type,
            object_type,
        ), count in sorted(type_counts.items()):
            print(
                "AUDIT_SUMMARY_TYPE | "
                f"company={filing['company_name']} | "
                f"relationship={relationship} | "
                f"types={subject_type}->{object_type} | "
                f"count={count}"
            )

        print("Raw predicate counts:")
        for predicate, count in sorted(
            Counter(c.predicate for c in raw_candidates).items()
        ):
            print(f"  {predicate}: {count}")

        print()
        print("RAW TRIPLETS")
        for index, candidate in enumerate(raw_candidates, start=1):
            print(
                f"[{index}] "
                f"{candidate.subject} -[{candidate.predicate}]-> {candidate.object}"
            )
            print(
                f"    types: {candidate.subject_type or 'unknown'} "
                f"-> {candidate.object_type or 'unknown'}"
            )
            print(f"    sentence: {candidate.source_sentence}")

        print()
        print("RESOLVED CANDIDATES")
        for index, candidate in enumerate(
            resolved_candidates,
            start=1,
        ):
            print(
                f"[{index}] "
                f"({candidate.subject_type}) {candidate.subject} "
                f"-[{candidate.relationship}]-> "
                f"({candidate.object_type}) {candidate.object}"
            )

    print()
    print("=" * 80)
    print("GLOBAL AUDIT SUMMARY")
    print(f"Filings: {len(processed_files)}")
    print(f"Raw triplets: {total_raw}")
    print(f"Resolved graph candidates: {total_resolved}")
    for (
        relationship,
        subject_type,
        object_type,
    ), count in sorted(global_type_counts.items()):
        print(
            "AUDIT_GLOBAL_TYPE | "
            f"relationship={relationship} | "
            f"types={subject_type}->{object_type} | "
            f"count={count}"
        )


if __name__ == "__main__":
    main()
