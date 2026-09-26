from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.tools import tool

from backend.app.agent.context import get_current_customer_id
from backend.app.repositories.customer_repository import CustomerRepository
from backend.app.repositories.recharge_repository import RechargeRepository
from backend.app.services.customer_service import CustomerService
from backend.app.services.recharge_service import RechargeService


def create_recharge_tools(db: AsyncSession):

    recharge_repository = RechargeRepository(db)
    recharge_service = RechargeService(recharge_repository)
    customer_repository = CustomerRepository(db)
    customer_service = CustomerService(customer_repository)

    @tool
    async def get_recharge(recharge_id: str) -> dict:
        """
        Retrieve details of a specific customer recharge.

        Use this tool when a customer asks about a particular
        recharge, such as its status, amount, payment method,
        failure reason, or provider reference.
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

        recharge = await recharge_service.get_recharge(
            recharge_id
        )

        if recharge is None:
            return {
                "found": False,
                "recharge_id": recharge_id,
                "message": "Recharge not found",
            }
        if (
                recharge.customer_id != customer.id
        ):
            return {
                "found": False,
                "transaction_id": recharge_id,
                "message": (
                    "Recharge id does not belong to "
                    "the authenticated customer"
                ),
            }

        return {
            "found": True,
            "recharge_id": recharge.recharge_id,
            "amount": str(recharge.amount),
            "currency": recharge.currency,
            "status": recharge.status,
            "payment_method": recharge.payment_method,
            "provider_reference": recharge.provider_reference,
            "failure_reason": recharge.failure_reason,
            "created_at": (
                recharge.created_at.isoformat()
                if recharge.created_at
                else None
            ),
        }

    return [get_recharge]