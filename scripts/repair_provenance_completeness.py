from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.graph.connection import Neo4jConnection
from src.graph.repository import GraphRepository


def backfill_event_provenance(connection: Neo4jConnection) -> int:
    query = """
    MATCH (event:Event)
    WHERE event.payload IS NOT NULL
    RETURN event.event_id AS event_id, event.payload AS payload
    """
    updated = 0
    with connection.driver.session() as session:
        rows = list(session.run(query))
        for row in rows:
            try:
                payload = json.loads(row["payload"]) if isinstance(row["payload"], str) else dict(row["payload"])
            except (TypeError, ValueError, json.JSONDecodeError):
                continue
            description = payload.get("description") or payload.get("title")
            confidence = payload.get("confidence")
            source_url = payload.get("source_url")
            if description is None and confidence is None and source_url is None:
                continue
            session.run(
                """
                MATCH (event:Event {event_id: $event_id})
                SET event.description = coalesce(event.description, $description),
                    event.confidence = coalesce(event.confidence, $confidence),
                    event.source_url = coalesce(event.source_url, $source_url)
                """,
                event_id=row["event_id"],
                description=description,
                confidence=confidence,
                source_url=source_url,
            ).consume()
            updated += 1
    return updated


def main() -> None:
    facilities = json.loads((ROOT / "data/seed/facilities.json").read_text(encoding="utf-8"))
    locations = json.loads((ROOT / "data/seed/locations.json").read_text(encoding="utf-8"))
    companies = json.loads((ROOT / "data/seed/companies.json").read_text(encoding="utf-8"))
    connection = Neo4jConnection()
    try:
        repository = GraphRepository(connection)
        repository.seed_companies(companies)
        repository.seed_locations(locations)
        repository.seed_facilities(facilities)
        event_count = backfill_event_provenance(connection)
        print(f"Provenance repair completed; event nodes updated: {event_count}")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
