from __future__ import annotations

import json
import sqlite3
from hashlib import sha256
from pathlib import Path

from .models import (
    DisclosureDocument,
    DocumentRepresentation,
    IngestionStatus,
    NormalizedDisclosure,
    RawArtifact,
)


class RawArtifactStore:
    def __init__(self, root: Path) -> None:
        self.root = root

    @staticmethod
    def content_hash(content: bytes) -> str:
        return sha256(content).hexdigest()

    @staticmethod
    def extension_for_mime(mime_type: str) -> str:
        mime = mime_type.lower()
        if "pdf" in mime:
            return ".pdf"
        if "xml" in mime:
            return ".xml"
        if "json" in mime:
            return ".json"
        if "html" in mime:
            return ".html"
        return ".bin"

    def save(self, artifact: RawArtifact) -> tuple[str, Path]:
        digest = self.content_hash(artifact.content)
        extension = self.extension_for_mime(artifact.mime_type)
        path = self.root / digest[:2] / f"{digest}{extension}"
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_bytes(artifact.content)
        return digest, path


class DocumentRegistry:
    """SQLite metadata/state registry for disclosure acquisition.

    Physical artifacts are content-addressed once, while representations record
    every provider/source occurrence. This lets identical bytes discovered from
    two authoritative sources share storage without losing either provenance.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    document_id TEXT PRIMARY KEY,
                    company_id TEXT NOT NULL,
                    document_family TEXT NOT NULL,
                    native_document_type TEXT,
                    reporting_period_end TEXT,
                    reporting_year INTEGER,
                    publication_date TEXT,
                    filing_date TEXT,
                    language TEXT,
                    logical_document_key TEXT NOT NULL UNIQUE,
                    current_representation_id TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS artifacts (
                    content_sha256 TEXT PRIMARY KEY,
                    mime_type TEXT NOT NULL,
                    byte_size INTEGER NOT NULL,
                    storage_uri TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS representations (
                    representation_id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    provider_document_id TEXT,
                    source_url TEXT NOT NULL,
                    retrieved_at TEXT NOT NULL,
                    mime_type TEXT NOT NULL,
                    content_sha256 TEXT NOT NULL,
                    byte_size INTEGER NOT NULL,
                    storage_uri TEXT NOT NULL,
                    version_number INTEGER NOT NULL,
                    amendment INTEGER NOT NULL DEFAULT 0,
                    supersedes_representation_id TEXT,
                    is_canonical_representation INTEGER NOT NULL DEFAULT 0,
                    UNIQUE(source_id, provider_document_id),
                    FOREIGN KEY(document_id) REFERENCES documents(document_id),
                    FOREIGN KEY(content_sha256) REFERENCES artifacts(content_sha256)
                );

                CREATE INDEX IF NOT EXISTS idx_representation_hash
                ON representations(content_sha256);

                CREATE TABLE IF NOT EXISTS ingestion_state (
                    company_id TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    provider_document_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    error_type TEXT,
                    error_message TEXT,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY(company_id, source_id, provider_document_id)
                );

                CREATE TABLE IF NOT EXISTS normalized_documents (
                    representation_id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    FOREIGN KEY(document_id) REFERENCES documents(document_id)
                );
                """
            )

    def artifact_exists(self, content_sha256: str) -> bool:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT 1 FROM artifacts WHERE content_sha256 = ?",
                (content_sha256,),
            ).fetchone()
            return row is not None

    def representation_by_occurrence(
        self,
        *,
        source_id: str,
        provider_document_id: str | None,
        source_url: str,
    ) -> sqlite3.Row | None:
        with self._connect() as connection:
            if provider_document_id:
                return connection.execute(
                    """
                    SELECT * FROM representations
                    WHERE source_id = ? AND provider_document_id = ?
                    """,
                    (source_id, provider_document_id),
                ).fetchone()
            return connection.execute(
                """
                SELECT * FROM representations
                WHERE source_id = ? AND source_url = ?
                """,
                (source_id, source_url),
            ).fetchone()

    def save_artifact(
        self,
        *,
        content_sha256: str,
        mime_type: str,
        byte_size: int,
        storage_uri: str,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO artifacts (
                    content_sha256, mime_type, byte_size, storage_uri
                ) VALUES (?, ?, ?, ?)
                """,
                (content_sha256, mime_type, byte_size, storage_uri),
            )

    def upsert_document(self, document: DisclosureDocument) -> None:
        payload = document.model_dump(mode="json")
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO documents (
                    document_id, company_id, document_family,
                    native_document_type, reporting_period_end, reporting_year,
                    publication_date, filing_date, language,
                    logical_document_key, current_representation_id,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(document_id) DO UPDATE SET
                    current_representation_id = excluded.current_representation_id,
                    updated_at = excluded.updated_at
                """,
                (
                    payload["document_id"],
                    payload["company_id"],
                    payload["document_family"],
                    payload["native_document_type"],
                    payload["reporting_period_end"],
                    payload["reporting_year"],
                    payload["publication_date"],
                    payload["filing_date"],
                    payload["language"],
                    payload["logical_document_key"],
                    payload["current_representation_id"],
                    payload["created_at"],
                    payload["updated_at"],
                ),
            )

    def insert_representation(self, representation: DocumentRepresentation) -> None:
        payload = representation.model_dump(mode="json")
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO representations (
                    representation_id, document_id, source_id,
                    provider_document_id, source_url, retrieved_at, mime_type,
                    content_sha256, byte_size, storage_uri, version_number,
                    amendment, supersedes_representation_id,
                    is_canonical_representation
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["representation_id"],
                    payload["document_id"],
                    payload["source_id"],
                    payload["provider_document_id"],
                    payload["source_url"],
                    payload["retrieved_at"],
                    payload["mime_type"],
                    payload["content_sha256"],
                    payload["byte_size"],
                    payload["storage_uri"],
                    payload["version_number"],
                    int(payload["amendment"]),
                    payload["supersedes_representation_id"],
                    int(payload["is_canonical_representation"]),
                ),
            )

    def save_normalized(self, normalized: NormalizedDisclosure) -> None:
        payload = normalized.model_dump(mode="json")
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO normalized_documents (
                    representation_id, document_id, payload_json
                ) VALUES (?, ?, ?)
                """,
                (
                    normalized.source_representation_id,
                    normalized.document_id,
                    json.dumps(payload, ensure_ascii=False),
                ),
            )

    def load_normalized(self, representation_id: str) -> NormalizedDisclosure | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT payload_json FROM normalized_documents
                WHERE representation_id = ?
                """,
                (representation_id,),
            ).fetchone()
        if row is None:
            return None
        return NormalizedDisclosure.model_validate_json(row["payload_json"])

    def set_status(
        self,
        *,
        company_id: str,
        source_id: str,
        provider_document_id: str,
        status: IngestionStatus,
        error: Exception | None = None,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO ingestion_state (
                    company_id, source_id, provider_document_id,
                    status, error_type, error_message, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(company_id, source_id, provider_document_id)
                DO UPDATE SET
                    status = excluded.status,
                    error_type = excluded.error_type,
                    error_message = excluded.error_message,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    company_id,
                    source_id,
                    provider_document_id,
                    status.value,
                    type(error).__name__ if error else None,
                    str(error) if error else None,
                ),
            )
