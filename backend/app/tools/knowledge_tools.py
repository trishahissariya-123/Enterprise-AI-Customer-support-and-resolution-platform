from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.tools import tool

from backend.app.rag.retrieval import retrieve_knowledge


def create_knowledge_tools(db: AsyncSession):

    @tool
    async def search_knowledge_base(
        query: str,
        top_k: int = 3,
    ) -> dict:
        """
        Search the customer support knowledge base.

        Use this tool for policy, FAQ, troubleshooting,
        and general customer-support questions.

        Do not use this tool to retrieve customer-specific
        information such as wallet balance, transactions,
        recharge status, KYC status, or account details.
        """

        top_k = min(max(top_k, 1), 5)

        results = await retrieve_knowledge(
            db=db,
            query=query,
            top_k=top_k,
        )

        return {
            "found": bool(results),
            "count": len(results),
            "results": [
                {
                    "document": document.document_name,
                    "chunk_index": document.chunk_index,
                    "content": document.content,
                }
                for document in results
            ],
        }

    return [search_knowledge_base]