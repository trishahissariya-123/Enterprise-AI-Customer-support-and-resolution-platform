from backend.app.models.customer import Customer
from backend.app.models.merchant_payment import MerchantPayment
from backend.app.repositories.merchant_payment_repository import (
    MerchantPaymentRepository,
)


class MerchantPaymentService:
    def __init__(
        self,
        merchant_payment_repository: MerchantPaymentRepository,
    ):
        self.merchant_payment_repository = merchant_payment_repository

    async def get_payment(
        self,
        payment_id: str,
    ) -> MerchantPayment | None:
        return await self.merchant_payment_repository.get_by_payment_id(
            payment_id
        )

    async def get_customer_payments(
        self,
        customer: Customer,
        limit: int = 20,
    ) -> list[MerchantPayment]:
        return await self.merchant_payment_repository.get_customer_payments(
            customer.id,
            limit,
        )