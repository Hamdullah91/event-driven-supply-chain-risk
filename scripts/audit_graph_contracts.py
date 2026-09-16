from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.graph.audit import GraphContractAudit
from src.graph.connection import Neo4jConnection


def main() -> None:
    connection = Neo4jConnection()
    try:
        audit = GraphContractAudit(connection)
        report = {
            "canonical_ids": audit.canonical_id_completeness(),
            "geographic_coordinates": audit.geographic_coordinate_completeness(),
        }
        print(json.dumps(report, indent=2))
    finally:
        connection.close()


if __name__ == "__main__":
    main()
