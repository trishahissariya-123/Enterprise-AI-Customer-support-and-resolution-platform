from backend.app.models.customer import Customer
from backend.app.models.recharge import Recharge
from backend.app.repositories.recharge_repository import RechargeRepository


class RechargeService:
    def __init__(self, recharge_repository: RechargeRepository):
        self.recharge_repository = recharge_repository

    async def get_recharge(
        self,
        recharge_id: str,
    ) -> Recharge | None:
        return await self.recharge_repository.get_by_recharge_id(
            recharge_id
        )

    async def get_customer_recharges(
        self,
        customer: Customer,
        limit: int = 20,
    ) -> list[Recharge]:
        return await self.recharge_repository.get_customer_recharges(
            customer.id,
            limit,
        )