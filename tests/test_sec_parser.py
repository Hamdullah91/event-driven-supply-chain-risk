from src.ingestion.sec.parser import (
    FilingMetadata,
    SEC10KParser,
)


def test_html_to_text():
    html = """
    <html>
        <body>
            <h1>ITEM 1. BUSINESS</h1>
            <p>We use external suppliers.</p>
        </body>
    </html>
    """

    text = SEC10KParser.html_to_text(html)

    assert "ITEM 1. BUSINESS" in text
    assert "We use external suppliers." in text


def test_extract_sections():
    text = """
ITEM 1. BUSINESS
We use external suppliers.

ITEM 1A. RISK FACTORS
Supplier shortages may affect production.

ITEM 2. PROPERTIES
We operate manufacturing facilities.

ITEM 3. LEGAL PROCEEDINGS
Legal information.

ITEM 7. MANAGEMENT DISCUSSION
Supply constraints affected operations.
"""

    sections = SEC10KParser.extract_sections(text)

    assert "1" in sections
    assert "1A" in sections
    assert "2" in sections
    assert "7" in sections


def test_filter_relevant_sections():
    sections = {
        "1": "Business",
        "1A": "Risk Factors",
        "2": "Properties",
        "3": "Legal Proceedings",
        "7": "Management Discussion",
    }

    filtered = SEC10KParser.filter_relevant_sections(
        sections
    )

    assert set(filtered.keys()) == {
        "1",
        "1A",
        "2",
        "7",
    }


def test_keyword_detection():
    paragraph = (
        "We depend on semiconductor suppliers "
        "for critical components."
    )

    keywords = SEC10KParser.find_supply_chain_keywords(
        paragraph
    )

    assert "supplier" in keywords
    assert "semiconductor" in keywords
    assert "component" in keywords


def test_full_parser():
    html = """
    <html>
        <body>
            ITEM 1. BUSINESS
            We use semiconductor suppliers.

            ITEM 1A. RISK FACTORS
            Supplier shortages may affect production.

            ITEM 2. PROPERTIES
            We operate manufacturing facilities.

            ITEM 3. LEGAL PROCEEDINGS
            Legal information.
        </body>
    </html>
    """

    metadata = FilingMetadata(
        cik="0000000001",
        accession_number="0000000001-26-000001",
        company_name="Example Company",
        filing_date="2026-01-01",
        form="10-K",
        source_url="https://example.com",
    )

    parser = SEC10KParser()

    result = parser.parse(
        html=html,
        metadata=metadata,
    )

    assert result.metadata.company_name == "Example Company"
    assert len(result.sections) == 3

    relevant = [
        paragraph
        for section in result.sections
        for paragraph in section.paragraphs
        if paragraph.relevant
    ]

    assert len(relevant) >= 2