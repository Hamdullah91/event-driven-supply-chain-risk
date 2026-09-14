from __future__ import annotations

import asyncio
from collections.abc import Mapping
from typing import Any

import pytest

from src.agent.controller import AgentController
from src.agent.cypher_generator import CypherGenerator
from src.agent.cypher_validator import CypherValidator, UnsafeCypherError
from src.agent.planner import AgentPlanner


class FakeStructuredLLM:
    def __init__(self, responses: list[Mapping[str, Any]]) -> None:
        self.responses = list(responses)

    async def complete_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> Mapping[str, Any]:
        return self.responses.pop(0)


@pytest.fixture
def validator() -> CypherValidator:
    return CypherValidator()


def test_allows_parameterized_company_lookup(validator: CypherValidator) -> None:
    result = validator.validate(
        "MATCH (c:Company {company_id: $company_id}) RETURN c LIMIT 10"
    )
    assert result.valid
    assert result.errors == ()


def test_allows_three_hop_dependency_traversal(validator: CypherValidator) -> None:
    result = validator.validate(
        "MATCH p=(c:Company)-[:DEPENDS_ON*1..3]->(s:Company) "
        "RETURN p LIMIT 50"
    )
    assert result.valid


def test_allows_three_hop_supply_traversal(validator: CypherValidator) -> None:
    result = validator.validate(
        "MATCH p=(s:Company)-[:SUPPLIES*1..3]->(c:Company) "
        "RETURN p LIMIT 50"
    )
    assert result.valid


@pytest.mark.parametrize(
    ("query", "message"),
    [
        ("CREATE (:Company {name: 'Fake'}) RETURN 1 LIMIT 1", "CREATE"),
        ("MERGE (c:Company {name: 'Fake'}) RETURN c LIMIT 1", "MERGE"),
        ("MATCH (c:Company) DELETE c RETURN c LIMIT 1", "DELETE"),
        ("MATCH (c:Company) DETACH DELETE c RETURN c LIMIT 1", "DETACH"),
        ("MATCH (c:Company) SET c.name = 'x' RETURN c LIMIT 1", "SET"),
        ("LOAD CSV FROM 'https://example.test/x.csv' AS row RETURN row LIMIT 1", "LOAD"),
        ("CALL db.labels() YIELD label RETURN label LIMIT 10", "Procedure calls"),
    ],
)
def test_rejects_write_admin_and_procedure_operations(
    validator: CypherValidator,
    query: str,
    message: str,
) -> None:
    result = validator.validate(query)
    assert not result.valid
    assert any(message in error for error in result.errors)


def test_rejects_unknown_node_label(validator: CypherValidator) -> None:
    result = validator.validate("MATCH (x:SecretNode) RETURN x LIMIT 10")
    assert not result.valid
    assert "Node label is not allowed: SecretNode." in result.errors


def test_rejects_unknown_relationship_type(validator: CypherValidator) -> None:
    result = validator.validate(
        "MATCH (a:Company)-[:PURCHASES_FROM]->(b:Company) RETURN a, b LIMIT 10"
    )
    assert not result.valid
    assert "Relationship type is not allowed: PURCHASES_FROM." in result.errors


def test_rejects_more_than_three_hops(validator: CypherValidator) -> None:
    result = validator.validate(
        "MATCH p=(a:Company)-[:DEPENDS_ON*1..4]->(b:Company) RETURN p LIMIT 20"
    )
    assert not result.valid
    assert any("maximum 3 hops" in error for error in result.errors)


def test_rejects_unbounded_traversal(validator: CypherValidator) -> None:
    result = validator.validate(
        "MATCH p=(a:Company)-[:DEPENDS_ON*]->(b:Company) RETURN p LIMIT 20"
    )
    assert not result.valid
    assert "Unbounded variable-length traversal is forbidden." in result.errors


def test_rejects_variable_length_on_non_supply_chain_relationship(
    validator: CypherValidator,
) -> None:
    result = validator.validate(
        "MATCH p=(e:Event)-[:AFFECTS*1..3]->(c:Company) RETURN p LIMIT 20"
    )
    assert not result.valid
    assert any("Variable-length traversal is only allowed" in error for error in result.errors)


def test_rejects_missing_limit(validator: CypherValidator) -> None:
    result = validator.validate("MATCH (c:Company) RETURN c")
    assert not result.valid
    assert "LLM-generated Cypher must contain a numeric LIMIT." in result.errors


def test_rejects_excessive_limit(validator: CypherValidator) -> None:
    result = validator.validate("MATCH (c:Company) RETURN c LIMIT 1000")
    assert not result.valid
    assert "LIMIT 1000 exceeds maximum allowed 100." in result.errors


def test_rejects_multiple_statements(validator: CypherValidator) -> None:
    result = validator.validate(
        "MATCH (c:Company) RETURN c LIMIT 1; MATCH (e:Event) RETURN e LIMIT 1"
    )
    assert not result.valid
    assert "Only one Cypher statement is allowed." in result.errors


def test_keywords_inside_string_literals_do_not_trigger_write_block(
    validator: CypherValidator,
) -> None:
    result = validator.validate(
        "MATCH (c:Company) WHERE c.name = 'CREATE DELETE SET' RETURN c LIMIT 10"
    )
    assert result.valid


def test_blocked_words_in_comments_do_not_trigger_false_positive(
    validator: CypherValidator,
) -> None:
    result = validator.validate(
        "// DELETE everything\nMATCH (c:Company) RETURN c LIMIT 10"
    )
    assert result.valid


def test_controller_rejects_unsafe_generated_cypher() -> None:
    llm = FakeStructuredLLM(
        [
            {
                "intent": "GRAPH_LOOKUP",
                "tool": "GRAPH_QUERY",
                "objective": "Find a company",
                "entities": [{"name": "NVIDIA", "entity_type": "Company"}],
                "requires_generated_cypher": True,
                "max_hops": 3,
            },
            {
                "cypher": "MATCH (c:Company) DELETE c RETURN c LIMIT 10",
                "parameters": {},
                "expected_fields": ["c"],
            },
        ]
    )
    controller = AgentController(
        planner=AgentPlanner(llm),
        cypher_generator=CypherGenerator(llm),
    )

    with pytest.raises(UnsafeCypherError, match="DELETE"):
        asyncio.run(controller.prepare("Find NVIDIA"))
