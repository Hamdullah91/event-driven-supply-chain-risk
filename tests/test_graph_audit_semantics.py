from src.graph.audit import GraphContractAudit


class _Result:
    def __init__(self, rows):
        self.rows = rows

    def __iter__(self):
        return iter(self.rows)

    def single(self):
        return self.rows[0] if self.rows else None


class _Session:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def run(self, query):
        if "MATCH ()-[r]->()" in query:
            return _Result(
                [
                    {
                        "relationship_type": "SUPPLIES",
                        "total": 1,
                        "with_source": 1,
                        "with_source_url": 1,
                        "with_confidence": 1,
                        "with_verification_status": 1,
                        "with_derivation": 0,
                        "with_link_method": 0,
                        "with_linked_at": 0,
                    }
                ]
            )
        return _Result(
            [
                {
                    "total": 1,
                    "with_source": 1,
                    "with_timestamp": 1,
                    "with_confidence": 1,
                    "with_description": 0,
                }
            ]
        )


class _Driver:
    def session(self):
        return _Session()


class _Connection:
    driver = _Driver()


def test_event_core_evidence_complete_is_explicitly_distinct_from_description():
    report = GraphContractAudit(_Connection()).provenance_completeness()
    events = report["events"]

    assert events["core_evidence_fields"] == [
        "with_source",
        "with_timestamp",
        "with_confidence",
    ]
    assert events["core_evidence_complete"] is True
    assert events["description_complete"] is False
    assert "core_complete" not in events
