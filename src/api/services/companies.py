from __future__ import annotations

from typing import Any

from src.graph.company_repository import CompanyGraphRepository
from src.provenance import relationship_evidence_availability


class CompanyGraphService:
    """Application service for read-only company graph operations."""

    def __init__(self, repository: CompanyGraphRepository) -> None:
        self.repository = repository

    def list_companies(
        self,
        *,
        limit: int,
        offset: int,
        search: str | None = None,
        industry_id: str | None = None,
        entity_type: str | None = None,
    ) -> dict[str, Any]:
        filters = {
            "search": search,
            "industry_id": industry_id,
            "entity_type": entity_type,
        }
        return {
            "companies": self.repository.list_companies(
                limit=limit,
                offset=offset,
                **filters,
            ),
            "count": self.repository.count_companies(**filters),
            "limit": limit,
            "offset": offset,
        }

    def search_entities(self, query: str, *, limit: int) -> dict[str, Any]:
        results = self.repository.search_entities(query, limit=limit)
        return {
            "query": query,
            "results": results,
            "count": len(results),
        }

    def get_company(self, company_id: str) -> dict[str, Any] | None:
        return self.repository.get_company(company_id)

    def get_company_network(
        self,
        company_id: str,
        *,
        depth: int,
    ) -> dict[str, Any] | None:
        network = self.repository.get_company_network(company_id, depth=depth)
        if network is None:
            return None

        for relationship in network.get("relationships", []):
            properties = relationship.get("properties") or {}
            relationship["evidence_status"] = relationship_evidence_availability(
                properties
            )
        return network
