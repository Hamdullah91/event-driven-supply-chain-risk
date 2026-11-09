from __future__ import annotations

import asyncio

from src.api.services.risk_stream import RiskStreamService


def company(company_id: str, hop_distance: int) -> dict:
    return {
        "company_id": company_id,
        "company_name": company_id.upper(),
        "hop_distance": hop_distance,
    }


class FakeRiskService:
    def __init__(self, companies: list[dict]) -> None:
        self.companies = companies
        self.impact_calls: list[tuple[str, int]] = []

    def get_event_blast_radius(self, event_id: str, *, max_hops: int = 3) -> dict:
        self.impact_calls.append((event_id, max_hops))
        return {
            "event_id": event_id,
            "max_hops": max_hops,
            "companies": list(self.companies),
        }

    def get_company_risk(self, company_id: str, *, max_hops: int = 3) -> dict:
        return {
            "company_id": company_id,
            "risk_score": 0.61,
            "risk_level": "HIGH",
            "contributing_event_count": 1,
            "max_hops": max_hops,
        }


class CapturingManager:
    def __init__(self) -> None:
        self.messages: list[dict] = []

    async def broadcast(self, message: dict) -> None:
        self.messages.append(message)


def ids_for(companies: list[dict], *, max_hops: int = 3) -> list[str]:
    service = RiskStreamService(FakeRiskService(companies), manager=CapturingManager())
    return service.impacted_company_ids_for_event(
        event_id="evt-propagation",
        max_hops=max_hops,
    )


def test_a1_direct_affected_company_is_in_realtime_scope() -> None:
    assert ids_for([company("tsmc", 0)]) == ["tsmc"]


def test_a2_hop_one_downstream_company_is_in_realtime_scope() -> None:
    assert ids_for([company("tsmc", 0), company("nvidia", 1)]) == ["nvidia", "tsmc"]


def test_a3_hop_two_downstream_company_is_in_realtime_scope() -> None:
    assert "amd" in ids_for([company("tsmc", 0), company("amd", 2)])


def test_a4_hop_three_downstream_company_is_in_realtime_scope() -> None:
    assert "dell" in ids_for([company("tsmc", 0), company("dell", 3)])


def test_a5_company_beyond_max_hops_is_not_published() -> None:
    manager = CapturingManager()
    service = RiskStreamService(
        FakeRiskService([company("tsmc", 0), company("too-far", 4)]),
        manager=manager,
    )

    messages = asyncio.run(
        service.publish_event_risk(
            event_id="evt-propagation",
            event_type="FACILITY_OUTAGE",
            max_hops=3,
        )
    )

    assert [message["company_id"] for message in messages] == ["tsmc"]
    assert [message["company_id"] for message in manager.messages] == ["tsmc"]


def test_a6_duplicate_paths_do_not_duplicate_company_publication() -> None:
    manager = CapturingManager()
    service = RiskStreamService(
        FakeRiskService(
            [
                company("tsmc", 0),
                company("nvidia", 1),
                company("nvidia", 2),
                company("nvidia", 3),
            ]
        ),
        manager=manager,
    )

    asyncio.run(
        service.publish_event_risk(
            event_id="evt-propagation",
            event_type="FACILITY_OUTAGE",
        )
    )

    assert [message["company_id"] for message in manager.messages].count("nvidia") == 1


def test_a7_unrelated_company_is_not_published() -> None:
    manager = CapturingManager()
    service = RiskStreamService(
        FakeRiskService([company("tsmc", 0), company("nvidia", 1)]),
        manager=manager,
    )

    asyncio.run(
        service.publish_event_risk(
            event_id="evt-propagation",
            event_type="FACILITY_OUTAGE",
        )
    )

    published = {message["company_id"] for message in manager.messages}
    assert published == {"tsmc", "nvidia"}
    assert "unrelated-company" not in published


def test_a8_published_messages_use_canonical_company_ids() -> None:
    manager = CapturingManager()
    service = RiskStreamService(
        FakeRiskService([company("tsmc", 0), company("nvidia", 1)]),
        manager=manager,
    )

    asyncio.run(
        service.publish_event_risk(
            event_id="evt-canonical",
            event_type="FACILITY_OUTAGE",
        )
    )

    assert {message["company_id"] for message in manager.messages} == {"tsmc", "nvidia"}


def test_a9_published_messages_preserve_canonical_event_id() -> None:
    manager = CapturingManager()
    service = RiskStreamService(
        FakeRiskService([company("tsmc", 0), company("nvidia", 1)]),
        manager=manager,
    )

    asyncio.run(
        service.publish_event_risk(
            event_id="event-123-canonical",
            event_type="FACILITY_OUTAGE",
        )
    )

    assert manager.messages
    assert all(message["event_id"] == "event-123-canonical" for message in manager.messages)


def test_a10_existing_direct_company_publication_remains_functional() -> None:
    manager = CapturingManager()
    risk_service = FakeRiskService([company("tsmc", 0)])
    service = RiskStreamService(risk_service, manager=manager)

    messages = asyncio.run(
        service.publish_event_risk(
            event_id="evt-direct",
            event_type="SUPPLY_DISRUPTION",
        )
    )

    assert risk_service.impact_calls == [("evt-direct", 3)]
    assert len(messages) == 1
    assert messages[0]["company_id"] == "tsmc"
    assert messages[0]["event_id"] == "evt-direct"
    assert messages[0]["trigger_event_type"] == "SUPPLY_DISRUPTION"
