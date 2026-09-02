from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.ingestion.sec.parser import (
    FilingMetadata,
    SEC10KParser,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Parse a downloaded SEC 10-K filing."
    )

    parser.add_argument(
        "--input",
        required=True,
        type=Path,
    )

    parser.add_argument(
        "--output",
        required=True,
        type=Path,
    )

    parser.add_argument(
        "--cik",
        required=True,
    )

    parser.add_argument(
        "--accession",
        required=True,
    )

    parser.add_argument(
        "--company",
        required=True,
    )

    parser.add_argument(
        "--filing-date",
        required=True,
    )

    parser.add_argument(
        "--source-url",
        required=True,
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    html = args.input.read_text(
        encoding="utf-8",
        errors="replace",
    )

    metadata = FilingMetadata(
        cik=args.cik,
        accession_number=args.accession,
        company_name=args.company,
        filing_date=args.filing_date,
        form="10-K",
        source_url=args.source_url,
    )

    parser = SEC10KParser()

    result = parser.parse(
        html=html,
        metadata=metadata,
    )

    args.output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    args.output.write_text(
        json.dumps(
            result.to_dict(),
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    total_paragraphs = sum(
        len(section.paragraphs)
        for section in result.sections
    )

    relevant_paragraphs = sum(
        paragraph.relevant
        for section in result.sections
        for paragraph in section.paragraphs
    )

    print(
        f"Saved: {args.output}"
    )

    print(
        f"Sections: {len(result.sections)}"
    )

    print(
        f"Paragraphs: {total_paragraphs}"
    )

    print(
        f"Relevant paragraphs: {relevant_paragraphs}"
    )


if __name__ == "__main__":
    main()