"""
services/search.py — Serper.dev search client with 24h DB cache.

Serper wraps Google Search. Free tier: 2,500 queries/month (~400 full analyses).

Flow per query:
  1. Hash query → check search_cache table.
  2. Cache hit (< 24h)  → return cached results.
  3. Cache miss         → call Serper API → store in cache → return.
  4. Apply freshness filter (discard results > 24 months old unless academic/regulatory).
"""
import hashlib
from datetime import datetime, timedelta, timezone

import httpx
import structlog
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from config import get_settings
from models.database import SearchCache
from models.schemas import SearchSnippet

log = structlog.get_logger(__name__)
settings = get_settings()

SERPER_URL = "https://google.serper.dev/search"

_EVERGREEN_SIGNALS = (
    "arxiv", "ncbi", "gov", "regulation", "legislation",
    "ieee", "springer", "sciencedirect", "statista",
)


def _is_fresh(published_date: str | None) -> bool:
    """Return True if result falls within the freshness window."""
    if not published_date:
        return True
    try:
        pub = datetime.fromisoformat(published_date.replace("Z", "+00:00"))
        cutoff = datetime.now(timezone.utc) - timedelta(days=settings.result_freshness_months * 30)
        return pub >= cutoff
    except ValueError:
        return True


def _is_evergreen_source(url: str) -> bool:
    """Academic, regulatory, and government sources ignore age filter."""
    return any(sig in url.lower() for sig in _EVERGREEN_SIGNALS)


def _hash_query(query: str) -> str:
    return hashlib.sha256(query.strip().lower().encode()).hexdigest()


async def _fetch_from_serper(query: str) -> list[dict]:
    """Call Serper.dev and return normalised result list."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            SERPER_URL,
            json={"q": query, "num": settings.search_results_per_query, "gl": "us", "hl": "en"},
            headers={"X-API-KEY": settings.serper_api_key, "Content-Type": "application/json"},
            timeout=15.0,
        )
        resp.raise_for_status()
        data = resp.json()

    return [
        {
            "title":       r.get("title", ""),
            "url":         r.get("link", ""),
            "description": r.get("snippet", ""),
            "published":   r.get("date"),
        }
        for r in data.get("organic", [])
    ]


async def search_with_cache(query: str, db: AsyncSession) -> list[SearchSnippet]:
    """Return fresh SearchSnippets — DB cache first, Serper API on miss."""
    query_hash = _hash_query(query)
    cache_cutoff = datetime.utcnow() - timedelta(hours=settings.search_cache_ttl_hours)

    stmt = select(SearchCache).where(
        SearchCache.query_hash == query_hash,
        SearchCache.created_at >= cache_cutoff,
    )
    cached = (await db.execute(stmt)).scalar_one_or_none()

    if cached:
        log.info("search.cache_hit", query=query[:60])
        raw_results = cached.results_json
    else:
        log.info("search.api_call", query=query[:60])
        raw_results = await _fetch_from_serper(query)
        await db.execute(delete(SearchCache).where(SearchCache.query_hash == query_hash))
        db.add(SearchCache(query_hash=query_hash, query_text=query, results_json=raw_results))
        await db.commit()

    snippets: list[SearchSnippet] = []
    for r in raw_results:
        url = r.get("url", "")
        pub_date = r.get("published") or None
        fresh = _is_fresh(pub_date) or _is_evergreen_source(url)
        snippets.append(SearchSnippet(
            title=r.get("title", ""),
            url=url,
            snippet=r.get("description", ""),
            published_date=pub_date,
            is_fresh=fresh,
        ))

    fresh_snippets = [s for s in snippets if s.is_fresh]
    log.info("search.results", total=len(snippets), fresh=len(fresh_snippets), query=query[:60])
    return fresh_snippets


async def multi_search(queries: list[str], db: AsyncSession) -> list[SearchSnippet]:
    """Run all queries sequentially (rate-limit safe) and deduplicate by URL."""
    seen_urls: set[str] = set()
    all_snippets: list[SearchSnippet] = []

    for query in queries:
        for snippet in await search_with_cache(query, db):
            if snippet.url not in seen_urls:
                seen_urls.add(snippet.url)
                all_snippets.append(snippet)

    return all_snippets
