from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.customer import Customer


class CustomerRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_customer_id(
        self,
        customer_id: str,
    ) -> Customer | None:
        result = await self.db.execute(
            select(Customer).where(
                Customer.customer_id == customer_id
            )
        )

        return result.scalar_one_or_none()

    async def get_by_phone_number(
        self,
        phone_number: str,
    ) -> Customer | None:
        result = await self.db.execute(
            select(Customer).where(
                Customer.phone_number == phone_number
            )
        )

        return result.scalar_one_or_none()