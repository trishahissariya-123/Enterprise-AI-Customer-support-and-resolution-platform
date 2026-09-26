from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.customer_profile import CustomerProfile


class CustomerProfileRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_customer_id(
        self,
        customer_id: int,
    ) -> CustomerProfile | None:

        result = await self.db.execute(
            select(CustomerProfile).where(
                CustomerProfile.customer_id == customer_id
            )
        )

        return result.scalar_one_or_none()