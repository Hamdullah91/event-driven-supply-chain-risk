from __future__ import annotations

from typing import Any

from src.graph.company_repository import CompanyGraphRepository


class CompanyGraphService:
    """Application service for read-only company graph operations."""

    def __init__(self, repository: CompanyGraphRepository) -> None:
        self.repository = repository

    def list_companies(self, *, limit: int, offset: int) -> dict[str, Any]:
        return {
            "companies": self.repository.list_companies(limit=limit, offset=offset),
            "count": self.repository.count_companies(),
            "limit": limit,
            "offset": offset,
        }

    def get_company(self, company_id: str) -> dict[str, Any] | None:
        return self.repository.get_company(company_id)

    def get_company_network(self, company_id: str, *, depth: int) -> dict[str, Any] | None:
        network = self.repository.get_company_network(company_id, depth=depth)
        if network is None:
            return None

        for relationship in network["relationships"]:
            relationship["relationship_type"] = relationship.pop("type")
        return network
