import hashlib
import os
import re
from pathlib import Path
from typing import Any

import psycopg


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHUNK_SIZE = 800
CHUNK_OVERLAP = 120
DEFAULT_RESULTS = 5

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()


def _connect():
    if DATABASE_URL:
        return psycopg.connect(DATABASE_URL)

    return psycopg.connect(
        dbname=os.getenv("PGDATABASE", "news_research"),
        user=os.getenv("PGUSER", "rafah"),
        host=os.getenv("PGHOST", "/var/run/postgresql"),
    )


def init_rag_db() -> None:
    """Create the PostgreSQL tables required by the RAG service."""
    with _connect() as conn:
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS saved_articles (
                article_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                url TEXT NOT NULL DEFAULT '',
                source TEXT NOT NULL DEFAULT '',
                published_at TEXT NOT NULL DEFAULT '',
                created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS saved_article_chunks (
                chunk_id TEXT PRIMARY KEY,
                article_id TEXT NOT NULL
                    REFERENCES saved_articles(article_id)
                    ON DELETE CASCADE,
                chunk_index INTEGER NOT NULL,
                chunk_text TEXT NOT NULL,
                embedding vector,
                search_vector TSVECTOR GENERATED ALWAYS AS (
                    to_tsvector('english', chunk_text)
                ) STORED,
                UNIQUE(article_id, chunk_index)
            )
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_saved_article_chunks_search
            ON saved_article_chunks USING GIN(search_vector)
        """)

        conn.commit()


def _clean_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return re.sub(r"\s+", " ", value).strip()


def _split_into_chunks(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[str]:
    text = _clean_text(text)

    if not text:
        return []

    if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
        raise ValueError("Invalid chunk size or overlap.")

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = end - overlap

    return chunks


def save_article(article: dict) -> dict:
    """Store an article and its text chunks in PostgreSQL."""
    if not isinstance(article, dict):
        raise ValueError("Article must be a dictionary.")

    title = _clean_text(article.get("title")) or "Untitled article"
    url = _clean_text(article.get("url"))
    content = (
        _clean_text(article.get("article_text"))
        or _clean_text(article.get("content"))
        or _clean_text(article.get("description"))
    )

    if not content:
        raise ValueError(
            "Article has no text. Provide article_text, content, "
            "or description."
        )

    source = article.get("source", "")
    if isinstance(source, dict):
        source = source.get("name", "")
    source = _clean_text(source)
    published_at = _clean_text(article.get("publishedAt"))

    identity = url or f"{title}\n{content}"
    article_id = hashlib.sha256(
        identity.encode("utf-8")
    ).hexdigest()

    chunks = _split_into_chunks(content)
    if not chunks:
        raise ValueError("Article text could not be split into chunks.")

    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO saved_articles
                (article_id, title, url, source, published_at)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (article_id) DO UPDATE SET
                title = EXCLUDED.title,
                url = EXCLUDED.url,
                source = EXCLUDED.source,
                published_at = EXCLUDED.published_at
            """,
            (article_id, title, url, source, published_at),
        )

        # Replace previous chunks so repeated saves don't leave stale text.
        conn.execute(
            "DELETE FROM saved_article_chunks WHERE article_id = %s",
            (article_id,),
        )

        for index, chunk in enumerate(chunks):
            chunk_id = hashlib.sha256(
                f"{article_id}:{index}".encode("utf-8")
            ).hexdigest()

            conn.execute(
                """
                INSERT INTO saved_article_chunks
                    (chunk_id, article_id, chunk_index, chunk_text)
                VALUES (%s, %s, %s, %s)
                """,
                (chunk_id, article_id, index, chunk),
            )

        conn.commit()

    return {
        "status": "saved",
        "article_id": article_id,
        "title": title,
        "url": url,
        "chunks_saved": len(chunks),
    }


def save_articles(articles: list[dict]) -> dict:
    """Save multiple articles and report individual errors."""
    if not isinstance(articles, list):
        raise ValueError("Articles must be a list.")

    saved = []
    errors = []

    for index, article in enumerate(articles):
        try:
            saved.append(save_article(article))
        except Exception as exc:
            errors.append({"index": index, "error": str(exc)})

    return {
        "saved_count": len(saved),
        "error_count": len(errors),
        "saved": saved,
        "errors": errors,
    }



def search_saved_articles(
    query: str,
    n_results: int = DEFAULT_RESULTS,
) -> dict:
    """Search saved article chunks using full-text search with a substring fallback."""
    query = _clean_text(query)

    if not query:
        raise ValueError("Search query cannot be empty.")
    if len(query) > 1000:
        raise ValueError("Search query must not exceed 1000 characters.")

    n_results = max(1, min(int(n_results), 10))
    init_rag_db()

    with _connect() as conn:
        # First: use PostgreSQL full-text search.
        rows = conn.execute(
            """
            SELECT
                c.chunk_text,
                a.title,
                a.url,
                a.source,
                a.published_at,
                c.chunk_index,
                ts_rank_cd(
                    c.search_vector,
                    websearch_to_tsquery('english', %s)
                ) AS score
            FROM saved_article_chunks AS c
            JOIN saved_articles AS a
                ON a.article_id = c.article_id
            WHERE c.search_vector @@
                websearch_to_tsquery('english', %s)
            ORDER BY score DESC, a.created_at DESC
            LIMIT %s
            """,
            (query, query, n_results),
        ).fetchall()

        search_type = "postgresql_full_text"

        # Fallback: match the query directly in title, URL, or text.
        if not rows:
            pattern = f"%{query}%"
            rows = conn.execute(
                """
                SELECT
                    c.chunk_text,
                    a.title,
                    a.url,
                    a.source,
                    a.published_at,
                    c.chunk_index,
                    0.0 AS score
                FROM saved_article_chunks AS c
                JOIN saved_articles AS a
                    ON a.article_id = c.article_id
                WHERE a.title ILIKE %s
                   OR a.url ILIKE %s
                   OR c.chunk_text ILIKE %s
                ORDER BY a.created_at DESC, c.chunk_index ASC
                LIMIT %s
                """,
                (pattern, pattern, pattern, n_results),
            ).fetchall()
            search_type = "postgresql_substring_fallback"

        total = conn.execute(
            "SELECT COUNT(*) FROM saved_article_chunks"
        ).fetchone()[0]

    results = [
        {
            "text": row[0],
            "title": row[1],
            "url": row[2],
            "source": row[3],
            "publishedAt": row[4],
            "chunk_index": row[5],
            "score": float(row[6]),
        }
        for row in rows
    ]

    return {
        "query": query,
        "results": results,
        "result_count": len(results),
        "stored_chunks": total,
        "search_type": search_type,
        "message": (
            "No matching saved articles found."
            if not results
            else ""
        ),
    }


def get_saved_article_count() -> int:
    """Return the number of stored chunks."""
    init_rag_db()

    with _connect() as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM saved_article_chunks"
        ).fetchone()[0]


# Ensure the tables exist when the service is imported.
init_rag_db()
