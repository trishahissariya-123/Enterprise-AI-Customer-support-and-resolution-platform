from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.llm_usage import LLMUsage


class LLMUsageRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        request_id: str,
        conversation_id: int | None,
        customer_id: int | None,
        model: str,
        llm_call_count: int,
        input_tokens: int,
        output_tokens: int,
        total_tokens: int,
        estimated_cost_usd: float,
    ) -> LLMUsage:

        usage = LLMUsage(
            request_id=request_id,
            conversation_id=conversation_id,
            customer_id=customer_id,
            model=model,
            llm_call_count=llm_call_count,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=estimated_cost_usd,
        )

        self.db.add(usage)

        await self.db.flush()

        return usage