from sqlalchemy import text

from app.db.supabase import async_session
from app.skills.base import ClaudeSkill

EMBEDDING_MODEL = "text-embedding-3-small"
TOP_K = 3
# OpenAI text-embedding-3-small produces cosine similarities in roughly the 0.27–0.65
# range for this dataset. On-topic keyword queries score ~0.38–0.65; clearly off-topic
# queries (stock options, workers comp) score ~0.27–0.31. Threshold calibrated against
# observed scores from the actual corpus — not an arbitrary 0.7.
ESCALATION_THRESHOLD = 0.38


def _confidence_label(score: float) -> str:
    if score >= 0.50:
        return "high"
    if score >= 0.38:
        return "medium"
    return "low"


class RetrievePolicySkill(ClaudeSkill):
    name = "retrieve_policy"
    description = (
        "Search the company policy handbook for answers to HR questions. "
        "Returns the most relevant policy chunks with a confidence score. "
        "If confidence is low (should_escalate: true), the result will indicate escalation "
        "is needed — do not answer the user directly in that case."
    )
    parameters = {
        "query": {
            "type": "string",
            "description": "The policy question to search for (natural language)",
        },
        "context": {
            "type": "object",
            "description": "Optional context about the employee asking (department, role, etc.)",
            "optional": True,
        },
    }

    def __init__(self, openai_client=None):
        # Accept an injected client or create one lazily — avoids import-time side effects
        self._openai = openai_client

    def _get_openai(self):
        if self._openai is None:
            from openai import AsyncOpenAI
            from app.config import get_settings
            self._openai = AsyncOpenAI(api_key=get_settings().openai_api_key)
        return self._openai

    async def execute(self, query: str, context: dict | None = None) -> dict:
        client = self._get_openai()

        response = await client.embeddings.create(model=EMBEDDING_MODEL, input=query)
        query_embedding = response.data[0].embedding

        async with async_session() as session:
            # Order by the alias — ordering on the raw <=> expression can short-circuit
            # IVFFlat indexes on small datasets (verified in Phase 2)
            sql = text(
                "SELECT title, category, content, source_file, "
                "1 - (embedding <=> CAST(:vec AS vector)) AS similarity "
                "FROM policy_documents "
                "WHERE embedding IS NOT NULL "
                "ORDER BY similarity DESC "
                f"LIMIT {TOP_K}"
            )
            result = await session.execute(sql, {"vec": str(query_embedding)})
            rows = result.all()

        if not rows:
            return {
                "documents": [],
                "confidence_score": 0.0,
                "confidence_level": "low",
                "should_escalate": True,
            }

        top_score: float = rows[0].similarity
        documents = [
            {
                "title": row.title,
                "category": row.category,
                "content": row.content,
                "source_file": row.source_file,
                "similarity": round(row.similarity, 4),
            }
            for row in rows
        ]

        return {
            "documents": documents,
            "confidence_score": round(top_score, 4),
            "confidence_level": _confidence_label(top_score),
            "should_escalate": top_score < ESCALATION_THRESHOLD,
        }
