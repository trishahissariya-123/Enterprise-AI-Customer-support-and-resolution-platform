from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.knowledge_document import KnowledgeDocument


class KnowledgeRetrievalRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def similarity_search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> list[KnowledgeDocument]:

        distance = KnowledgeDocument.embedding.cosine_distance(
            query_embedding
        )

        result = await self.db.execute(
            select(KnowledgeDocument)
            .order_by(distance)
            .limit(top_k)
        )

        return list(result.scalars().all())