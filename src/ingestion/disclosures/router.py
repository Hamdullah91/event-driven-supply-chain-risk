from __future__ import annotations

from .models import Company, CompanySourceBinding
from .providers.base import DisclosureProvider
from .registry import CompanyRegistry, SourceRegistry


class SourceRouter:
    def __init__(
        self,
        *,
        company_registry: CompanyRegistry,
        source_registry: SourceRegistry,
        providers: list[DisclosureProvider],
    ) -> None:
        self.company_registry = company_registry
        self.source_registry = source_registry
        self.providers = {provider.provider_id: provider for provider in providers}

    def routes_for(
        self,
        company: Company,
    ) -> list[tuple[DisclosureProvider, CompanySourceBinding | None]]:
        bindings = self.company_registry.bindings_for(company.company_id)
        routes: list[tuple[int, DisclosureProvider, CompanySourceBinding | None]] = []

        for binding in bindings:
            provider = self.providers.get(binding.source_id)
            if provider is None:
                continue
            source = self.source_registry.get(binding.source_id)
            if not source.enabled or not provider.supports(company, binding):
                continue
            priority = (
                binding.priority_override
                if binding.priority_override is not None
                else source.default_priority
            )
            routes.append((priority, provider, binding))

        # Providers may also support a company directly from generic identifiers
        # even when an explicit binding has not yet been authored.
        bound_provider_ids = {binding.source_id for binding in bindings}
        for provider in self.providers.values():
            if provider.provider_id in bound_provider_ids:
                continue
            source = self.source_registry.get(provider.provider_id)
            if source.enabled and provider.supports(company, None):
                routes.append((source.default_priority, provider, None))

        routes.sort(key=lambda item: item[0])
        return [(provider, binding) for _, provider, binding in routes]
