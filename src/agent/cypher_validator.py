from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

from src.agent.models import CypherProposal
from src.agent.schema import allowed_labels, allowed_relationship_types


logger = logging.getLogger(__name__)

MAX_HOPS = 3
MAX_LIMIT = 100
VARIABLE_LENGTH_RELATIONSHIPS = frozenset({"DEPENDS_ON", "SUPPLIES"})

BLOCKED_KEYWORDS = frozenset(
    {
        "ALTER",
        "CREATE",
        "DELETE",
        "DENY",
        "DETACH",
        "DROP",
        "FOREACH",
        "GRANT",
        "LOAD",
        "MERGE",
        "REMOVE",
        "RENAME",
        "REVOKE",
        "SET",
        "START",
        "STOP",
        "TERMINATE",
        "USE",
    }
)


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    errors: tuple[str, ...] = field(default_factory=tuple)


class UnsafeCypherError(ValueError):
    """Raised when an LLM-generated Cypher proposal violates the safety policy."""

    def __init__(self, errors: tuple[str, ...]) -> None:
        self.errors = errors
        super().__init__("Unsafe Cypher proposal: " + "; ".join(errors))


class CypherValidator:
    """Validate LLM-generated Cypher before any Neo4j execution boundary."""

    def __init__(self, *, max_hops: int = MAX_HOPS, max_limit: int = MAX_LIMIT) -> None:
        if max_hops < 1 or max_hops > MAX_HOPS:
            raise ValueError(f"max_hops must be between 1 and {MAX_HOPS}")
        if max_limit < 1:
            raise ValueError("max_limit must be positive")
        self.max_hops = max_hops
        self.max_limit = max_limit
        self._allowed_labels = frozenset(allowed_labels())
        self._allowed_relationships = frozenset(allowed_relationship_types())

    def validate(self, proposal: CypherProposal | str) -> ValidationResult:
        query = proposal.cypher if isinstance(proposal, CypherProposal) else proposal
        errors: list[str] = []

        if not query or not query.strip():
            return ValidationResult(valid=False, errors=("Cypher query is empty.",))

        without_comments = self._strip_comments(query)
        masked = self._mask_string_literals(without_comments)

        self._validate_single_statement(masked, errors)
        self._validate_read_only(masked, errors)
        self._validate_labels(masked, errors)
        self._validate_relationships(masked, errors)
        self._validate_hops(masked, errors)
        self._validate_limit(masked, errors)

        result = ValidationResult(valid=not errors, errors=tuple(errors))
        logger.info(
            "agent_cypher_validation valid=%s error_count=%s",
            result.valid,
            len(result.errors),
        )
        return result

    def ensure_safe(self, proposal: CypherProposal | str) -> ValidationResult:
        result = self.validate(proposal)
        if not result.valid:
            raise UnsafeCypherError(result.errors)
        return result

    @staticmethod
    def _strip_comments(query: str) -> str:
        query = re.sub(r"/\*.*?\*/", " ", query, flags=re.DOTALL)
        return re.sub(r"//.*?$", " ", query, flags=re.MULTILINE).strip()

    @staticmethod
    def _mask_string_literals(query: str) -> str:
        # Preserve query structure while preventing keywords/semicolons inside
        # parameter-like string values from being treated as Cypher syntax.
        query = re.sub(r"'(?:\\.|''|[^'])*'", "''", query)
        return re.sub(r'"(?:\\.|""|[^"])*"', '""', query)

    @staticmethod
    def _validate_single_statement(query: str, errors: list[str]) -> None:
        statements = [part.strip() for part in query.split(";") if part.strip()]
        if len(statements) > 1:
            errors.append("Only one Cypher statement is allowed.")

    @staticmethod
    def _validate_read_only(query: str, errors: list[str]) -> None:
        upper_query = query.upper()
        for keyword in sorted(BLOCKED_KEYWORDS):
            if re.search(rf"\b{re.escape(keyword)}\b", upper_query):
                errors.append(f"Forbidden Cypher operation detected: {keyword}.")

        if re.search(r"\bCALL\b", upper_query):
            errors.append("Procedure calls are not allowed in LLM-generated Cypher.")

        if not re.search(r"\bRETURN\b", upper_query):
            errors.append("LLM-generated Cypher must contain RETURN.")

    def _validate_labels(self, query: str, errors: list[str]) -> None:
        labels = re.findall(
            r"\(\s*(?:`[^`]+`|[A-Za-z_][A-Za-z0-9_]*)?\s*:\s*`?([A-Za-z_][A-Za-z0-9_]*)`?",
            query,
        )
        for label in labels:
            if label not in self._allowed_labels:
                errors.append(f"Node label is not allowed: {label}.")

    def _validate_relationships(self, query: str, errors: list[str]) -> None:
        for block in re.findall(r"\[([^\]]*)\]", query, flags=re.DOTALL):
            relationship_types = re.findall(
                r"(?:^|[:|])\s*`?([A-Za-z_][A-Za-z0-9_]*)`?",
                block,
            )
            # A named relationship variable is not a relationship type; only
            # colon/pipe-prefixed values count. Re-parse conservatively.
            relationship_types = re.findall(
                r"[:|]\s*`?([A-Za-z_][A-Za-z0-9_]*)`?",
                block,
            )
            if not relationship_types:
                errors.append("Relationship patterns must declare an allowed relationship type.")
                continue
            for relationship in relationship_types:
                if relationship not in self._allowed_relationships:
                    errors.append(f"Relationship type is not allowed: {relationship}.")

    def _validate_hops(self, query: str, errors: list[str]) -> None:
        for block in re.findall(r"\[([^\]]*)\]", query, flags=re.DOTALL):
            if "*" not in block:
                continue

            relationship_types = re.findall(
                r"[:|]\s*`?([A-Za-z_][A-Za-z0-9_]*)`?",
                block,
            )
            for relationship in relationship_types:
                if relationship not in VARIABLE_LENGTH_RELATIONSHIPS:
                    errors.append(
                        "Variable-length traversal is only allowed for DEPENDS_ON or SUPPLIES; "
                        f"found {relationship}."
                    )

            hop_match = re.search(r"\*\s*(\d+)?\s*(?:\.\.\s*(\d+)?)?", block)
            if hop_match is None:
                errors.append("Unable to validate variable-length traversal.")
                continue

            raw = hop_match.group(0).replace(" ", "")
            start_text, end_text = hop_match.groups()

            if raw == "*" or raw.endswith(".."):
                errors.append("Unbounded variable-length traversal is forbidden.")
                continue

            if ".." in raw:
                if start_text is None or end_text is None:
                    errors.append("Variable-length traversal must have explicit lower and upper bounds.")
                    continue
                start = int(start_text)
                end = int(end_text)
                if start < 1 or end < start:
                    errors.append("Variable-length traversal bounds are invalid.")
                    continue
                if end > self.max_hops:
                    errors.append(
                        f"Traversal exceeds maximum {self.max_hops} hops: {start}..{end}."
                    )
            else:
                hops = int(start_text or 0)
                if hops < 1 or hops > self.max_hops:
                    errors.append(
                        f"Traversal must be between 1 and {self.max_hops} hops; found {hops}."
                    )

    def _validate_limit(self, query: str, errors: list[str]) -> None:
        matches = re.findall(r"\bLIMIT\s+(\d+)\b", query, flags=re.IGNORECASE)
        if not matches:
            errors.append("LLM-generated Cypher must contain a numeric LIMIT.")
            return

        limit = int(matches[-1])
        if limit < 1:
            errors.append("LIMIT must be positive.")
        elif limit > self.max_limit:
            errors.append(
                f"LIMIT {limit} exceeds maximum allowed {self.max_limit}."
            )
