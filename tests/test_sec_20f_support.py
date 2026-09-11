from src.ingestion.sec.crawler import find_form_in_filing_data
from src.ingestion.sec.parser.filing_parser_20f import SEC20FParser
from src.ingestion.sec.parser.models import FilingMetadata


def test_find_form_in_filing_data_supports_20f():
    filing_data = {
        "form": ["6-K", "20-F"],
        "accessionNumber": ["0001", "0002"],
        "filingDate": ["2026-01-01", "2026-02-01"],
        "reportDate": ["2025-09-30", "2025-12-31"],
        "primaryDocument": ["sixk.htm", "annual.htm"],
    }

    filing = find_form_in_filing_data(filing_data, form="20-F")

    assert filing is not None
    assert filing["accession_number"] == "0002"
    assert filing["primary_document"] == "annual.htm"


def test_20f_parser_extracts_relevant_items():
    repeated = " supplier manufacturing supply chain dependency " * 80
    html = f"""
    <html><body>
    <p>ITEM 3. Key Information</p>
    <p>{repeated}</p>
    <p>ITEM 4. Information on the Company</p>
    <p>{repeated}</p>
    <p>ITEM 5. Operating and Financial Review and Prospects</p>
    <p>{repeated}</p>
    <p>ITEM 6. Directors and Senior Management</p>
    </body></html>
    """
    metadata = FilingMetadata(
        cik="0001046179",
        accession_number="000-test",
        company_name="TSMC",
        filing_date="2026-04-16",
        form="20-F",
        source_url="https://example.test/20f",
    )

    parsed = SEC20FParser().parse(html=html, metadata=metadata)

    assert [section.item for section in parsed.sections] == ["3", "4", "5"]
    assert all(section.paragraphs for section in parsed.sections)
    assert any(
        paragraph.relevant
        for section in parsed.sections
        for paragraph in section.paragraphs
    )


def test_20f_parser_rejects_wrong_form():
    metadata = FilingMetadata(
        cik="0001046179",
        accession_number="000-test",
        company_name="TSMC",
        filing_date="2026-04-16",
        form="10-K",
        source_url="https://example.test/10k",
    )

    try:
        SEC20FParser().parse(
            html="<html><body>ITEM 3. x</body></html>",
            metadata=metadata,
        )
    except ValueError as exc:
        assert "requires form 20-F" in str(exc)
    else:
        raise AssertionError("Expected SEC20FParser to reject non-20-F metadata")
