from backend.app.models.customer import Customer
from backend.app.models.transaction import Transaction
from backend.app.repositories.transaction_repository import TransactionRepository


class TransactionService:
    def __init__(self, transaction_repository: TransactionRepository):
        self.transaction_repository = transaction_repository

    async def get_transaction(
        self,
        transaction_id: str,
    ) -> Transaction | None:
        return await self.transaction_repository.get_by_transaction_id(
            transaction_id
        )

    async def get_customer_transactions(
        self,
        customer: Customer,
        limit: int = 20,
    ) -> list[Transaction]:
        return await self.transaction_repository.get_customer_transactions(
            customer.id,
            limit,
        )