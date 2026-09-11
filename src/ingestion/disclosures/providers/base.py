from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import Company, CompanySourceBinding, RawArtifact, RemoteDocument


class DisclosureProvider(ABC):
    provider_id: str

    @abstractmethod
    def supports(
        self,
        company: Company,
        binding: CompanySourceBinding | None,
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def discover_documents(
        self,
        company: Company,
        binding: CompanySourceBinding | None,
        *,
        year_from: int | None = None,
        year_to: int | None = None,
    ) -> list[RemoteDocument]:
        raise NotImplementedError

    @abstractmethod
    async def fetch_document(self, document: RemoteDocument) -> RawArtifact:
        raise NotImplementedError
