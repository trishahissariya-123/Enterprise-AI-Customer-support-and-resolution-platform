from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.rag.embeddings import get_embedding_model
from backend.app.repositories.knowledge_retrieval_repository import (
    KnowledgeRetrievalRepository,
)


async def retrieve_knowledge(
    db: AsyncSession,
    query: str,
    top_k: int = 5,
):
    embedding_model = get_embedding_model()

    query_embedding = embedding_model.embed_query(query)

    repository = KnowledgeRetrievalRepository(db)

    results = await repository.similarity_search(
        query_embedding=query_embedding,
        top_k=top_k,
    )

    return results