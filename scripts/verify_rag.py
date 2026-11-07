"""
Phase 2 verification — confirm policy_documents are queryable via SQLAlchemy.

Runs a pgvector similarity search using a sample query and prints the top results.

Usage:
    cd /path/to/meridian-hr-agent
    python scripts/verify_rag.py
"""

import asyncio
import os
import sys

# Loads backend/.env and puts backend/ on the path. Must precede app.* imports.
# No branch override: this operates on the main database by design.
import _bootstrap  # noqa: F401

from openai import OpenAI
from sqlalchemy import func, select, text

from app.db.session import async_session
from app.db.tables import PolicyDocument

EMBEDDING_MODEL = "text-embedding-3-small"
TOP_K = 3
TEST_QUERIES = [
    "When does health insurance coverage start for new employees?",
    "How much PTO do I get in my first year?",
    "Can I work from home?",
]

async def run_all(queries: list[tuple[str, list[float]]]) -> None:
    async with async_session() as session:
        count_result = await session.execute(select(func.count()).select_from(PolicyDocument))
        total = count_result.scalar()
        print(f"Total chunks in DB: {total}\n")

        for query, embedding in queries:
            # Mirrors the query shape in skills/retrieve_policy.py exactly —
            # ordering on the raw <=> operator so this measures what production
            # does, index and all.
            raw = text(
                "SELECT title, category, 1 - (embedding <=> CAST(:vec AS vector)) AS similarity "
                "FROM policy_documents "
                "WHERE embedding IS NOT NULL "
                "ORDER BY embedding <=> CAST(:vec AS vector) "
                "LIMIT :top_k"
            )
            results = await session.execute(
                raw, {"vec": str(embedding), "top_k": TOP_K}
            )
            rows = results.all()

            print(f'Query: "{query}"')
            print(f"Top {TOP_K} results:")
            for i, row in enumerate(rows, 1):
                print(f"  {i}. [{row.category}] {row.title}  (similarity: {row.similarity:.4f})")
            print()

def main() -> None:
    openai_key = os.environ.get("OPENAI_API_KEY")
    if not openai_key:
        print("ERROR: OPENAI_API_KEY not set")
        sys.exit(1)

    client = OpenAI(api_key=openai_key)

    print("Verifying RAG pipeline — embedding queries and running similarity search...\n")
    print("=" * 60 + "\n")

    queries = []
    for query in TEST_QUERIES:
        response = client.embeddings.create(model=EMBEDDING_MODEL, input=query)
        queries.append((query, response.data[0].embedding))

    asyncio.run(run_all(queries))

    print("=" * 60)
    print("Verification complete. Results with similarity > 0.5 confirm the pipeline is working.")

if __name__ == "__main__":
    main()
