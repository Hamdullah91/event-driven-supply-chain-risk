from datetime import datetime, timezone
from unittest.mock import MagicMock

from src.events.builder import build_news_event
from src.graph.repository import GraphRepository


def test_save_event_promotes_news_provenance_from_payload():
    connection = MagicMock()
    session = connection.driver.session.return_value.__enter__.return_value
    event = build_news_event(
        article_id="c4-article",
        classifier_label="FACILITY_OUTAGE",
        source="news_api",
        timestamp=datetime.now(timezone.utc),
        confidence=0.93,
        title="TSMC Fab 18 outage",
        source_url="https://example.com/c4-article",
    )

    GraphRepository(connection).save_event(event)

    _, kwargs = session.run.call_args
    assert kwargs["description"] == "TSMC Fab 18 outage"
    assert kwargs["confidence"] == 0.93
    assert kwargs["source_url"] == "https://example.com/c4-article"
    query = session.run.call_args.args[0]
    assert "event.description = $description" in query
    assert "event.confidence = $confidence" in query
    assert "event.source_url = $source_url" in query


def test_seed_facilities_propagates_supported_provenance_to_relationships():
    connection = MagicMock()
    session = connection.driver.session.return_value.__enter__.return_value
    GraphRepository(connection).seed_facilities([
        {
            "facility_id": "tsmc_fab_18",
            "name": "TSMC Fab 18",
            "company_id": "tsmc",
            "location_id": "tainan_tw",
            "facility_type": "semiconductor_fab",
            "city": "Tainan",
            "region": "Tainan",
            "country": "Taiwan",
            "source_type": "official_company_source",
            "verification_status": "verified",
        }
    ])
    query = session.run.call_args.args[0]
    assert "operates.source_type = facility.source_type" in query
    assert "located.source_type = facility.source_type" in query
    assert "operates.verification_status = facility.verification_status" in query
    assert "located.verification_status = facility.verification_status" in query


def test_seed_locations_records_coordinate_source_on_country_link():
    connection = MagicMock()
    session = connection.driver.session.return_value.__enter__.return_value
    GraphRepository(connection).seed_locations([
        {
            "location_id": "tainan_tw",
            "city": "Tainan",
            "region": "Tainan",
            "country_id": "taiwan",
            "latitude": 22.99,
            "longitude": 120.21,
            "coordinate_source": "GeoNames",
        }
    ])
    query = session.run.call_args.args[0]
    assert "r.source = location.coordinate_source" in query
    assert "r.source_type = 'coordinate_dataset'" in query
