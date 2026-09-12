from __future__ import annotations

from src.graph.connection import Neo4jConnection
from src.risk.repository import RiskRepository
from src.risk.service import RiskPropagationService


EVENT_ID = "day41-three-hop-validation-event"


def main() -> None:
    connection = Neo4jConnection()
    try:
        service = RiskPropagationService(RiskRepository(connection))
        exposures = service.calculate_three_hop_exposure(EVENT_ID)

        print("\n=== DAY 41 THREE-HOP RISK ===")

        if not exposures:
            print("No three-hop downstream supply paths found.")
            return

        for exposure in exposures:
            print(f"Event: {exposure.event_id}")
            print(f"Severity: {exposure.event_severity}")
            print(
                "Path: "
                f"{exposure.source_company_name} -> "
                f"{exposure.hop_1_company_name} -> "
                f"{exposure.hop_2_company_name} -> "
                f"{exposure.hop_3_company_name}"
            )
            print(f"Hop: {exposure.hop_distance}")
            print(f"Initial risk: {exposure.initial_risk}")
            print(
                "Dependency weights: "
                f"{exposure.hop_1_weight} ({exposure.hop_1_weight_source}), "
                f"{exposure.hop_2_weight} ({exposure.hop_2_weight_source}), "
                f"{exposure.hop_3_weight} ({exposure.hop_3_weight_source})"
            )
            print(f"Path dependency: {exposure.path_dependency}")
            print(f"Distance decay: {exposure.distance_decay}")
            print(f"Propagated risk: {exposure.propagated_risk}")
            print()
    finally:
        connection.close()


if __name__ == "__main__":
    main()
