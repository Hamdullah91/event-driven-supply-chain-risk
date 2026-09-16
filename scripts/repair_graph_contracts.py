from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.graph.connection import Neo4jConnection
from src.graph.repository import GraphRepository


def stable_id(name: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")
    if not value:
        raise ValueError("Cannot repair an unnamed node")
    return value


def repair_missing_domain_ids(connection: Neo4jConnection) -> None:
    with connection.driver.session() as session:
        for label, identity_property in (("Product", "product_id"), ("Material", "material_id")):
            rows = session.run(
                f"MATCH (n:{label}) WHERE n.{identity_property} IS NULL OR trim(toString(n.{identity_property})) = '' RETURN elementId(n) AS element_id, n.name AS name"
            )
            for row in rows:
                name = row["name"]
                if not name:
                    raise ValueError(f"Cannot repair {label} node {row['element_id']} without a name")
                session.run(
                    f"MATCH (n:{label}) WHERE elementId(n) = $element_id SET n.{identity_property} = $identity",
                    element_id=row["element_id"],
                    identity=stable_id(name),
                ).consume()


def main() -> None:
    locations = json.loads((ROOT / "data/seed/locations.json").read_text(encoding="utf-8"))
    connection = Neo4jConnection()
    try:
        GraphRepository(connection).seed_locations(locations)
        repair_missing_domain_ids(connection)
        print("Graph contract repair completed.")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
