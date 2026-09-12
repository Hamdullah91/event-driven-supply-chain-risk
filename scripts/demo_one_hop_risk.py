from src.graph.connection import Neo4jConnection
from src.risk.repository import RiskRepository
from src.risk.service import RiskPropagationService


EVENT_ID = "7d2d4a12-c6b7-55f2-9dfa-959be9ae1968"


def main() -> None:
    connection = Neo4jConnection()

    try:
        repository = RiskRepository(connection)
        service = RiskPropagationService(repository)

        exposures = service.calculate_one_hop_exposure(EVENT_ID)

        print("\n=== DAY 39 ONE-HOP RISK ===")

        for exposure in exposures:
            print(f"Event: {exposure.event_id}")
            print(f"Severity: {exposure.event_severity}")
            print(
                f"Path: {exposure.source_company_name}"
                f" -> {exposure.target_company_name}"
            )
            print(f"Hop: {exposure.hop_distance}")
            print(f"Initial risk: {exposure.initial_risk}")
            print(
                f"Dependency weight: "
                f"{exposure.dependency_weight}"
            )
            print(f"Weight source: {exposure.weight_source}")
            print(
                f"Distance decay: "
                f"{exposure.distance_decay}"
            )
            print(
                f"Propagated risk: "
                f"{exposure.propagated_risk}"
            )
            print()

    finally:
        connection.close()


if __name__ == "__main__":
    main()