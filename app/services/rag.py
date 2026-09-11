import re

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

STOP = {
    "the",
    "a",
    "an",
    "is",
    "are",
    "to",
    "for",
    "of",
    "and",
    "in",
    "on",
    "can",
    "i",
    "you",
    "my",
}


def tokenize(value: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9]+", value.lower()) if w not in STOP}


def reciprocal_rank_fusion(
    vector_rows: list[dict], keyword_rows: list[dict], k: int = 60
) -> list[dict]:
    scores = {}
    by_id = {}
    for rows in (vector_rows, keyword_rows):
        for rank, row in enumerate(rows, 1):
            key = str(row["id"])
            by_id[key] = row
            scores[key] = scores.get(key, 0) + 1 / (k + rank)
    return [
        {**by_id[key], "rrf_score": score}
        for key, score in sorted(scores.items(), key=lambda x: x[1], reverse=True)
    ]


async def retrieve(session: AsyncSession, query: str, limit: int = 5) -> list[dict]:
    # FTS is always available. Embedding retrieval can be added by filling the embedding column.
    sql = text("""SELECT id::text,title,content,source_url,authority,
      ts_rank_cd(search_vector, websearch_to_tsquery('english', :query)) AS rank
      FROM knowledge_documents
      WHERE search_vector @@ websearch_to_tsquery('english', :query)
      ORDER BY authority DESC, rank DESC LIMIT :limit""")
    rows = [
        dict(r) for r in (await session.execute(sql, {"query": query, "limit": limit})).mappings()
    ]
    if rows:
        return rows
    # Safe fallback for short/medical terms missed by stemming.
    fallback = text("""SELECT id::text,title,content,source_url,authority,0.0 AS rank
      FROM knowledge_documents WHERE content ILIKE :pattern OR title ILIKE :pattern
      ORDER BY authority DESC LIMIT :limit""")
    return [
        dict(r)
        for r in (
            await session.execute(fallback, {"pattern": f"%{query[:80]}%", "limit": limit})
        ).mappings()
    ]
