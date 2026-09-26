from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.kyc import KYCRecord


class KYCRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_customer_id(
        self,
        customer_id: int,
    ) -> KYCRecord | None:

        result = await self.db.execute(
            select(KYCRecord).where(
                KYCRecord.customer_id == customer_id
            )
        )

        return result.scalar_one_or_none()