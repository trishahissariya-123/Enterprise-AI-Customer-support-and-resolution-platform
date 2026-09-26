from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.knowledge_document import KnowledgeDocument


class KnowledgeDocumentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_documents(
        self,
        documents: list[KnowledgeDocument],
    ) -> None:
        self.db.add_all(documents)
        await self.db.commit()