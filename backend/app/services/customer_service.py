from backend.app.models.customer import Customer
from backend.app.repositories.customer_repository import CustomerRepository


class CustomerService:

    def __init__(
        self,
        customer_repository: CustomerRepository,
    ):
        self.customer_repository = customer_repository

    async def get_customer_by_id(
        self,
        customer_id: str,
    ) -> Customer | None:
        return await self.customer_repository.get_by_customer_id(
            customer_id
        )

    async def get_customer_by_phone(
        self,
        phone_number: str,
    ) -> Customer | None:
        return await self.customer_repository.get_by_phone_number(
            phone_number
        )