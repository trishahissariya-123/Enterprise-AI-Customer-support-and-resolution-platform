from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.tools import tool

from backend.app.agent.context import get_current_customer_id
from backend.app.repositories.customer_repository import CustomerRepository
from backend.app.repositories.transaction_repository import TransactionRepository
from backend.app.services.customer_service import CustomerService
from backend.app.services.transaction_service import TransactionService


def create_transaction_history_tools(db: AsyncSession):

    customer_repository = CustomerRepository(db)
    customer_service = CustomerService(customer_repository)

    transaction_repository = TransactionRepository(db)
    transaction_service = TransactionService(transaction_repository)

    @tool
    async def get_customer_transactions(
        limit: int = 10,
    ) -> dict:
        """
        Retrieve recent transactions for a customer.

        Use this tool when a customer asks about their recent
        transaction history.

        Keep the number of transactions small. Do not request
        an unnecessarily large history.
        """
        authenticated_customer_id = get_current_customer_id()

        if authenticated_customer_id is None:
            return {
                "found": False,
                "message": "Authenticated customer context is missing",
            }

        customer_id = authenticated_customer_id

        customer = await customer_service.get_customer_by_id(
            customer_id
        )

        if customer is None:
            return {
                "found": False,
                "customer_id": customer_id,
                "message": "Customer not found",
            }

        # Defensive limit for the tool layer.
        limit = min(max(limit, 1), 20)

        transactions = await transaction_service.get_customer_transactions(
            customer,
            limit,
        )

        return {
            "found": True,
            "customer_id": customer.customer_id,
            "count": len(transactions),
            "transactions": [
                {
                    "transaction_id": transaction.transaction_id,
                    "transaction_type": transaction.transaction_type,
                    "status": transaction.status,
                    "amount": str(transaction.amount),
                    "currency": transaction.currency,
                    "failure_reason": transaction.failure_reason,
                    "created_at": (
                        transaction.created_at.isoformat()
                        if transaction.created_at
                        else None
                    ),
                }
                for transaction in transactions
            ],
        }

    return [get_customer_transactions]