from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.tools import tool

from backend.app.repositories.transaction_repository import TransactionRepository
from backend.app.services.customer_service import CustomerService
from backend.app.repositories.customer_repository import CustomerRepository
from backend.app.services.transaction_service import TransactionService

from backend.app.agent.context import get_current_customer_id
def create_transaction_tools(db: AsyncSession):

    transaction_repository = TransactionRepository(db)
    transaction_service = TransactionService(transaction_repository)
    customer_repository=CustomerRepository(db)
    customer_service=CustomerService(customer_repository)

    @tool
    async def get_transaction(transaction_id: str) -> dict:
        """
        Retrieve details of a specific customer transaction.

        Use this tool when a customer asks about a particular
        transaction, such as its status, amount, type, failure
        reason, or transaction date.
        """
        authenticated_customer_id = get_current_customer_id()

        if authenticated_customer_id is None:
            return {
                "found": False,
                "message": "Authenticated customer context is missing",
            }
        customer = await customer_service.get_customer_by_id(authenticated_customer_id)

        if customer is None:
            return {
                "found": False,
                "message": "Authenticated customer not found",
            }


        transaction = await transaction_service.get_transaction(
            transaction_id
        )

        if transaction is None:
            return {
                "found": False,
                "transaction_id": transaction_id,
                "message": "Transaction not found",
            }
        if (
                    transaction.sender_customer_id != customer.id
                    and transaction.receiver_customer_id != customer.id
            ):
            return {
                "found": False,
                "transaction_id": transaction_id,
                "message": (
                    "Transaction does not belong to "
                    "the authenticated customer"
                ),
            }

        return {
            "found": True,
            "transaction_id": transaction.transaction_id,
            "transaction_type": transaction.transaction_type,
            "status": transaction.status,
            "amount": str(transaction.amount),
            "currency": transaction.currency,
            "failure_reason": transaction.failure_reason,
            "provider_reference": transaction.provider_reference,
            "created_at": transaction.created_at.isoformat()
            if transaction.created_at
            else None,
        }

    return [get_transaction]