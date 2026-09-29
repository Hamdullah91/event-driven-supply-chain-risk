from __future__ import annotations

from typing import Any

from src.graph.company_repository import CompanyGraphRepository


class FakeResult:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows

    def __iter__(self):
        return iter([FakeRecord(row) for row in self.rows])

    def single(self) -> dict[str, Any] | None:
        return self.rows[0] if self.rows else None


class FakeRecord(dict[str, Any]):
    def data(self) -> dict[str, Any]:
        return dict(self)


class FakeSession:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def __enter__(self) -> "FakeSession":
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def run(self, query: str, **params: Any) -> FakeResult:
        self.calls.append((query, params))
        if "RETURN count(DISTINCT c) AS count" in query:
            return FakeResult([{"count": 0}])
        return FakeResult([])


class FakeDriver:
    def __init__(self, session: FakeSession) -> None:
        self._session = session

    def session(self) -> FakeSession:
        return self._session


class FakeConnection:
    def __init__(self, session: FakeSession) -> None:
        self.driver = FakeDriver(session)


def compact(query: str) -> str:
    return " ".join(query.split())


def assert_company_filter_precedes_optional_industry(query: str) -> None:
    normalized = compact(query)
    assert normalized.index("WHERE ($search IS NULL") < normalized.index(
        "OPTIONAL MATCH (c)-[:OPERATES_IN]->(i:Industry)"
    )
    assert "AND ($entity_type IS NULL OR c.entity_type = $entity_type)" in normalized
    assert "WITH c, i WHERE ($industry_id IS NULL OR i.industry_id = $industry_id)" in normalized


def test_list_companies_filters_company_before_optional_industry_match() -> None:
    session = FakeSession()
    repository = CompanyGraphRepository(FakeConnection(session))  # type: ignore[arg-type]

    result = repository.list_companies(
        limit=25,
        offset=0,
        search=" no-such-company-xyz ",
        industry_id=" semiconductors ",
        entity_type=" core ",
    )

    assert result == []
    query, params = session.calls[0]
    assert_company_filter_precedes_optional_industry(query)
    assert params["search"] == "no-such-company-xyz"
    assert params["industry_id"] == "semiconductors"
    assert params["entity_type"] == "core"


def test_count_companies_uses_the_same_filter_order() -> None:
    session = FakeSession()
    repository = CompanyGraphRepository(FakeConnection(session))  # type: ignore[arg-type]

    count = repository.count_companies(search="missing")

    assert count == 0
    query, params = session.calls[0]
    assert_company_filter_precedes_optional_industry(query)
    assert params["search"] == "missing"
