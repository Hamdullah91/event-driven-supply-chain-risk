from __future__ import annotations

import sqlite3
from pathlib import Path

from src.ingestion.news.models import NewsArticle


class NewsRepository:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)

        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._initialize_database()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.database_path,
            timeout=30,
        )

        connection.row_factory = sqlite3.Row

        return connection

    def _initialize_database(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS news_articles (
                    article_id TEXT PRIMARY KEY,

                    title TEXT NOT NULL,
                    description TEXT,
                    content TEXT,

                    url TEXT NOT NULL,
                    source TEXT NOT NULL,

                    published_at TEXT NOT NULL,
                    ingested_at TEXT NOT NULL,

                    nlp_processed INTEGER NOT NULL DEFAULT 0,
                    classification_processed INTEGER NOT NULL DEFAULT 0,
                    graph_injected INTEGER NOT NULL DEFAULT 0
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_news_published_at
                ON news_articles(published_at)
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_news_nlp_processed
                ON news_articles(nlp_processed)
                """
            )

            connection.commit()

    def exists(self, article_id: str) -> bool:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT 1
                FROM news_articles
                WHERE article_id = ?
                LIMIT 1
                """,
                (article_id,),
            ).fetchone()

        return row is not None

    def save(self, article: NewsArticle) -> bool:
        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO news_articles (
                        article_id,
                        title,
                        description,
                        content,
                        url,
                        source,
                        published_at,
                        ingested_at,
                        nlp_processed,
                        classification_processed,
                        graph_injected
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 0)
                    """,
                    (
                        article.article_id,
                        article.title,
                        article.description,
                        article.content,
                        article.url,
                        article.source,
                        article.published_at.isoformat(),
                        article.ingested_at.isoformat(),
                    ),
                )

                connection.commit()

            return True

        except sqlite3.IntegrityError:
            # article_id already exists = duplicate
            return False

    def count(self) -> int:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS total
                FROM news_articles
                """
            ).fetchone()

        return int(row["total"])