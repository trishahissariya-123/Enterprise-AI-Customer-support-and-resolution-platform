from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.wallet import Wallet


class WalletRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_customer_id(
        self,
        customer_id: int,
    ) -> Wallet | None:

        result = await self.db.execute(
            select(Wallet).where(
                Wallet.customer_id == customer_id
            )
        )

        return result.scalar_one_or_none()