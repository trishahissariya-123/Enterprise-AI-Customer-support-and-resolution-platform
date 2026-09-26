from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.transaction import Transaction


class TransactionRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_transaction_id(
        self,
        transaction_id: str,
    ) -> Transaction | None:

        result = await self.db.execute(
            select(Transaction).where(
                Transaction.transaction_id == transaction_id
            )
        )

        return result.scalar_one_or_none()

    async def get_customer_transactions(
        self,
        customer_id: int,
        limit: int = 20,
    ) -> list[Transaction]:

        result = await self.db.execute(
            select(Transaction)
            .where(
                (Transaction.sender_customer_id == customer_id)
                | (Transaction.receiver_customer_id == customer_id)
            )
            .order_by(Transaction.created_at.desc())
            .limit(limit)
        )

        return list(result.scalars().all())