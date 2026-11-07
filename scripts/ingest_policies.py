"""
Policy ingestion script.

Reads all markdown docs from backend/app/rag/documents/, chunks them,
embeds each chunk via the OpenAI embeddings API (text-embedding-3-small, 1536d),
and inserts into the policy_documents table.

Re-runnable: clears existing chunks before inserting, so the table always
reflects the current contents of the documents directory.

Usage:
    cd /path/to/meridian-hr-agent
    python scripts/ingest_policies.py
"""

import asyncio
import os
import re
import sys
from pathlib import Path


# Loads backend/.env and puts backend/ on the path. Must precede app.* imports.
# No branch override: this operates on the main database by design.
import _bootstrap  # noqa: F401

from openai import OpenAI
from sqlalchemy import delete

from app.db.session import async_session
from app.db.tables import PolicyDocument

# ── Config ────────────────────────────────────────────────────────────────────

DOCS_DIR = Path(__file__).parent.parent / "backend" / "app" / "rag" / "documents"
EMBEDDING_MODEL = "text-embedding-3-small"  # 1536d — matches policy_documents vector(1536)
CHUNK_TARGET_TOKENS = 750
MIN_CHUNK_TOKENS = 20


# ── Chunking ──────────────────────────────────────────────────────────────────

def estimate_tokens(text: str) -> int:
    # Rough approximation: 1 token ≈ 0.75 words
    return max(1, len(text.split()) * 4 // 3)


def chunk_document(text: str) -> list[str]:
    """
    Split a markdown document into chunks of ~CHUNK_TARGET_TOKENS.
    Strategy: split on H2/H3 headers first, then merge small sections
    and split large ones by paragraph.
    """
    sections = re.split(r"\n(?=#{1,3} )", text)
    chunks: list[str] = []
    buffer = ""

    for section in sections:
        section = section.strip()
        if not section:
            continue

        if estimate_tokens(section) > CHUNK_TARGET_TOKENS * 1.5:
            # Large section — flush buffer, then split by paragraph
            if buffer.strip():
                chunks.append(buffer.strip())
                buffer = ""
            para_buffer = ""
            for para in section.split("\n\n"):
                para = para.strip()
                if not para:
                    continue
                combined = f"{para_buffer}\n\n{para}" if para_buffer else para
                if estimate_tokens(combined) > CHUNK_TARGET_TOKENS:
                    if para_buffer.strip():
                        chunks.append(para_buffer.strip())
                    para_buffer = para
                else:
                    para_buffer = combined
            if para_buffer.strip():
                chunks.append(para_buffer.strip())
        else:
            combined = f"{buffer}\n\n{section}" if buffer else section
            if estimate_tokens(combined) > CHUNK_TARGET_TOKENS:
                if buffer.strip():
                    chunks.append(buffer.strip())
                buffer = section
            else:
                buffer = combined

    if buffer.strip():
        chunks.append(buffer.strip())

    return [c for c in chunks if estimate_tokens(c) >= MIN_CHUNK_TOKENS]


# ── Main ──────────────────────────────────────────────────────────────────────

async def ingest() -> None:
    openai_key = os.environ.get("OPENAI_API_KEY")
    database_url = os.environ.get("DATABASE_URL")

    if not all([openai_key, database_url]):
        print("ERROR: Missing required env vars (OPENAI_API_KEY, DATABASE_URL)")
        sys.exit(1)

    openai_client = OpenAI(api_key=openai_key)

    doc_files = sorted(DOCS_DIR.glob("*.md"))
    if not doc_files:
        print(f"No markdown files found in {DOCS_DIR}")
        sys.exit(1)

    total_chunks = 0

    async with async_session() as session:
        # Clear existing chunks so re-runs are idempotent
        await session.execute(delete(PolicyDocument))
        print("Cleared existing policy_documents rows.\n")

        for doc_path in doc_files:
            text = doc_path.read_text(encoding="utf-8")
            category = doc_path.stem
            source_file = doc_path.name
            title = category.replace("_", " ").title()

            chunks = chunk_document(text)
            print(f"{source_file}  →  {len(chunks)} chunks")

            for i, chunk_text in enumerate(chunks, start=1):
                response = openai_client.embeddings.create(
                    model=EMBEDDING_MODEL,
                    input=chunk_text,
                )
                embedding: list[float] = response.data[0].embedding

                # The pgvector SQLAlchemy type adapts a plain list[float], so
                # no string-and-cast dance is needed on the write path.
                session.add(
                    PolicyDocument(
                        title=f"{title} — chunk {i}",
                        content=chunk_text,
                        category=category,
                        source_file=source_file,
                        embedding=embedding,
                        version="1.0",
                    )
                )

                total_chunks += 1
                print(f"  [{i}/{len(chunks)}] ~{estimate_tokens(chunk_text)} tokens, {len(embedding)}d embedding")

            print()

        # One commit for the whole run — the delete and every insert land
        # together, so a mid-run failure leaves the old chunks in place.
        await session.commit()

    print(f"Done. {total_chunks} chunks ingested from {len(doc_files)} documents.")


if __name__ == "__main__":
    asyncio.run(ingest())
