from backend.app.models.customer import Customer
from backend.app.models.customer_profile import CustomerProfile
from backend.app.repositories.customer_profile_repository import (
    CustomerProfileRepository,
)


class CustomerProfileService:

    def __init__(
        self,
        customer_profile_repository: CustomerProfileRepository,
    ):
        self.customer_profile_repository = customer_profile_repository

    async def get_profile(
        self,
        customer: Customer,
    ) -> CustomerProfile | None:

        return await self.customer_profile_repository.get_by_customer_id(
            customer.id
        )