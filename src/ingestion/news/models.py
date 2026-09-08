from __future__ import annotations

from datetime import datetime
from hashlib import sha256
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator


TRACKING_PARAMETERS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "fbclid",
    "gclid",
}


class NewsArticle(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    article_id: str = Field(min_length=64, max_length=64)

    title: str
    description: str | None = None
    content: str | None = None

    url: str
    source: str

    published_at: datetime
    ingested_at: datetime

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        if not value:
            raise ValueError("Article title cannot be empty")
        return value


def normalize_url(url: str) -> str:
    parts = urlsplit(url.strip())

    filtered_query = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if key.lower() not in TRACKING_PARAMETERS
    ]

    return urlunsplit(
        (
            parts.scheme.lower(),
            parts.netloc.lower(),
            parts.path.rstrip("/"),
            urlencode(filtered_query),
            "",
        )
    )


def build_article_id(
    *,
    title: str,
    url: str | None,
    source: str,
    published_at: datetime,
) -> str:
    if url:
        identity = normalize_url(url)
    else:
        normalized_title = " ".join(
            title.lower().split()
        )

        identity = "|".join(
            (
                source.strip().lower(),
                normalized_title,
                published_at.isoformat(),
            )
        )

    return sha256(
        identity.encode("utf-8")
    ).hexdigest()