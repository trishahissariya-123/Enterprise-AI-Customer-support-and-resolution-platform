from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.tools import tool

from backend.app.repositories.customer_repository import CustomerRepository
from backend.app.repositories.wallet_repository import WalletRepository
from backend.app.services.customer_service import CustomerService
from backend.app.services.wallet_service import WalletService
from backend.app.agent.context import get_current_customer_id

def create_wallet_tools(db: AsyncSession):

    customer_repository = CustomerRepository(db)
    customer_service = CustomerService(customer_repository)

    wallet_repository = WalletRepository(db)
    wallet_service = WalletService(wallet_repository)

    @tool
    async def get_wallet_balance() -> dict:
        """
          Retrieve the current wallet balance and wallet status
    for the authenticated customer.

    The customer identity comes from the authenticated
    request context and must not be supplied by the LLM.
        """
        authenticated_customer_id = get_current_customer_id()
        if authenticated_customer_id is None:
            return {
                "found": False,
                "message": "Authenticated customer context is missing",
            }
        customer_id = authenticated_customer_id
        customer = await customer_service.get_customer_by_id(customer_id
        )

        if customer is None:
            return {
                "found": False,
                "customer_id": customer_id,
                "message": "Customer not found",
            }

        wallet = await wallet_service.get_wallet(customer)

        if wallet is None:
            return {
                "found": False,
                "customer_id": customer_id,
                "message": "Wallet not found",
            }

        return {
            "found": True,
            "customer_id": customer.customer_id,
            "balance": str(wallet.balance),
            "currency": wallet.currency,
            "status": wallet.status,
        }

    return [get_wallet_balance]