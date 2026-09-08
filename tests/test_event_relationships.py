from unittest.mock import MagicMock

from src.graph.repository import GraphRepository


def build_repository_with_record(record_value):
    connection = MagicMock()

    session = connection.driver.session.return_value.__enter__.return_value
    result = session.run.return_value
    result.single.return_value = record_value

    repository = GraphRepository(connection)

    return repository, session


def test_link_event_to_company_returns_true_when_linked():
    repository, session = build_repository_with_record(
        {"linked": True}
    )

    result = repository.link_event_to_company(
        event_id="event-001",
        company_id="company-tsmc",
        confidence=0.95,
    )

    assert result is True

    session.run.assert_called_once()

    _, kwargs = session.run.call_args

    assert kwargs["event_id"] == "event-001"
    assert kwargs["company_id"] == "company-tsmc"
    assert kwargs["confidence"] == 0.95
    assert kwargs["link_method"] == "entity_resolution"


def test_link_event_to_company_returns_false_when_not_found():
    repository, _ = build_repository_with_record(
        {"linked": False}
    )

    result = repository.link_event_to_company(
        event_id="event-missing",
        company_id="company-tsmc",
        confidence=0.90,
    )

    assert result is False


def test_link_event_to_facility_returns_true_when_linked():
    repository, session = build_repository_with_record(
        {"linked": True}
    )

    result = repository.link_event_to_facility(
        event_id="event-001",
        facility_id="facility-fab18",
        confidence=0.91,
    )

    assert result is True

    session.run.assert_called_once()

    _, kwargs = session.run.call_args

    assert kwargs["event_id"] == "event-001"
    assert kwargs["facility_id"] == "facility-fab18"
    assert kwargs["confidence"] == 0.91
    assert kwargs["link_method"] == "entity_resolution"


def test_link_event_to_facility_returns_false_when_not_found():
    repository, _ = build_repository_with_record(
        {"linked": False}
    )

    result = repository.link_event_to_facility(
        event_id="event-001",
        facility_id="facility-missing",
        confidence=0.88,
    )

    assert result is False


def test_company_link_query_uses_affects_relationship():
    repository, session = build_repository_with_record(
        {"linked": True}
    )

    repository.link_event_to_company(
        event_id="event-001",
        company_id="company-tsmc",
        confidence=0.95,
    )

    query = session.run.call_args.args[0]

    assert "AFFECTS" in query
    assert "MERGE" in query
    assert "MATCH (company:Company" in query


def test_facility_link_query_uses_occurs_at_relationship():
    repository, session = build_repository_with_record(
        {"linked": True}
    )

    repository.link_event_to_facility(
        event_id="event-001",
        facility_id="facility-fab18",
        confidence=0.95,
    )

    query = session.run.call_args.args[0]

    assert "OCCURS_AT" in query
    assert "MERGE" in query
    assert "MATCH (facility:Facility" in query