from __future__ import annotations

from datetime import date, datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class DocumentFamily(str, Enum):
    ANNUAL_REPORT = "annual_report"
    TEN_K = "10-k"
    TWENTY_F = "20-f"
    ANNUAL_SECURITIES_REPORT = "annual_securities_report"
    BUSINESS_REPORT = "business_report"
    UNIVERSAL_REGISTRATION_DOCUMENT = "universal_registration_document"
    INTEGRATED_REPORT = "integrated_report"
    OTHER_ANNUAL_DISCLOSURE = "other_annual_disclosure"


class SourceAuthority(str, Enum):
    REGULATOR = "regulator"
    EXCHANGE = "exchange"
    ISSUER = "issuer"
    OTHER_OFFICIAL = "other_official"


class IngestionStatus(str, Enum):
    DISCOVERED = "discovered"
    DOWNLOADING = "downloading"
    DOWNLOADED = "downloaded"
    NORMALIZED = "normalized"
    NLP_COMPLETE = "nlp_complete"
    GRAPH_COMPLETE = "graph_complete"
    NORMALIZED_UNSUPPORTED_LANGUAGE = "normalized_unsupported_language"
    FAILED_DISCOVERY = "failed_discovery"
    FAILED_DOWNLOAD = "failed_download"
    FAILED_NORMALIZATION = "failed_normalization"
    FAILED_NLP = "failed_nlp"
    FAILED_GRAPH = "failed_graph"


class CompanyIdentifier(BaseModel):
    namespace: str
    value: str

    @field_validator("namespace")
    @classmethod
    def normalize_namespace(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not normalized:
            raise ValueError("identifier namespace cannot be blank")
        return normalized

    @field_validator("value")
    @classmethod
    def validate_value(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("identifier value cannot be blank")
        return normalized


class Company(BaseModel):
    company_id: str
    legal_name: str
    name: str | None = None
    aliases: list[str] = Field(default_factory=list)
    industry_id: str | None = None
    country_of_incorporation: str | None = None
    headquarters_country: str | None = None
    identifiers: list[CompanyIdentifier] = Field(default_factory=list)
    preferred_languages: list[str] = Field(default_factory=lambda: ["en"])
    enabled: bool = True

    def identifier(self, namespace: str) -> str | None:
        target = namespace.strip().upper()
        for identifier in self.identifiers:
            if identifier.namespace == target:
                return identifier.value
        return None


class DisclosureSource(BaseModel):
    source_id: str
    display_name: str
    provider_type: str
    authority: SourceAuthority
    jurisdictions: list[str] = Field(default_factory=list)
    supported_document_families: list[DocumentFamily] = Field(default_factory=list)
    requires_api_key: bool = False
    supports_discovery_api: bool = False
    base_url: str | None = None
    default_priority: int = 100
    enabled: bool = True


class CompanySourceBinding(BaseModel):
    company_id: str
    source_id: str
    external_company_id: str | None = None
    discovery_url: str | None = None
    enabled: bool = True
    priority_override: int | None = None
    preferred_languages: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RemoteDocument(BaseModel):
    source_id: str
    provider_document_id: str | None = None
    company_id: str
    document_family: DocumentFamily | None = None
    native_document_type: str | None = None
    title: str | None = None
    source_url: str
    filing_date: date | None = None
    publication_date: date | None = None
    reporting_period_end: date | None = None
    reporting_year: int | None = None
    language: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RawArtifact(BaseModel):
    metadata: RemoteDocument
    content: bytes
    mime_type: str
    retrieved_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    response_headers: dict[str, str] = Field(default_factory=dict)


class NormalizedSection(BaseModel):
    native_heading: str | None = None
    semantic_role: str | None = None
    text: str
    order: int
    page_start: int | None = None
    page_end: int | None = None


class NormalizedDisclosure(BaseModel):
    document_id: str
    company_id: str
    source_id: str
    provider_document_id: str | None = None
    source_url: str
    title: str | None = None
    document_family: DocumentFamily
    native_document_type: str | None = None
    reporting_period_end: date | None = None
    reporting_year: int | None = None
    filing_date: date | None = None
    publication_date: date | None = None
    language: str = "en"
    sections: list[NormalizedSection] = Field(default_factory=list)
    full_text: str
    source_representation_id: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class DisclosureDocument(BaseModel):
    document_id: str
    company_id: str
    document_family: DocumentFamily
    native_document_type: str | None = None
    reporting_period_end: date | None = None
    reporting_year: int | None = None
    publication_date: date | None = None
    filing_date: date | None = None
    language: str | None = None
    logical_document_key: str
    current_representation_id: str | None = None
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class DocumentRepresentation(BaseModel):
    representation_id: str
    document_id: str
    source_id: str
    provider_document_id: str | None = None
    source_url: str
    retrieved_at: datetime
    mime_type: str
    content_sha256: str
    byte_size: int
    storage_uri: str
    version_number: int = 1
    amendment: bool = False
    supersedes_representation_id: str | None = None
    is_canonical_representation: bool = False
