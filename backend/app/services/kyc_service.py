from backend.app.models.customer import Customer
from backend.app.models.kyc import KYCRecord
from backend.app.repositories.kyc_repository import KYCRepository


class KYCService:

    def __init__(
        self,
        kyc_repository: KYCRepository,
    ):
        self.kyc_repository = kyc_repository

    async def get_kyc_status(
        self,
        customer: Customer,
    ) -> KYCRecord | None:

        return await self.kyc_repository.get_by_customer_id(
            customer.id
        )