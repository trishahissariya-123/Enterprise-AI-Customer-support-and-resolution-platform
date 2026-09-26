from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.recharge import Recharge


class RechargeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_recharge_id(
        self,
        recharge_id: str,
    ) -> Recharge | None:
        result = await self.db.execute(
            select(Recharge).where(
                Recharge.recharge_id == recharge_id
            )
        )
        return result.scalar_one_or_none()

    async def get_customer_recharges(
        self,
        customer_id: int,
        limit: int = 20,
    ) -> list[Recharge]:
        result = await self.db.execute(
            select(Recharge)
            .where(Recharge.customer_id == customer_id)
            .order_by(Recharge.created_at.desc())
            .limit(limit)
        )

        return list(result.scalars().all())