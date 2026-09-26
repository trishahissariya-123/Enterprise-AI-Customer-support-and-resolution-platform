from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.merchant_payment import MerchantPayment


class MerchantPaymentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_payment_id(
        self,
        payment_id: str,
    ) -> MerchantPayment | None:
        result = await self.db.execute(
            select(MerchantPayment).where(
                MerchantPayment.payment_id == payment_id
            )
        )
        return result.scalar_one_or_none()

    async def get_customer_payments(
        self,
        customer_id: int,
        limit: int = 20,
    ) -> list[MerchantPayment]:
        result = await self.db.execute(
            select(MerchantPayment)
            .where(
                MerchantPayment.customer_id == customer_id
            )
            .order_by(MerchantPayment.created_at.desc())
            .limit(limit)
        )

        return list(result.scalars().all())