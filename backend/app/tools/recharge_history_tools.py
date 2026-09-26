from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.tools import tool

from backend.app.repositories.customer_repository import CustomerRepository
from backend.app.repositories.recharge_repository import RechargeRepository
from backend.app.services.customer_service import CustomerService
from backend.app.services.recharge_service import RechargeService
from backend.app.agent.context import get_current_customer_id

def create_recharge_history_tools(db: AsyncSession):

    customer_repository = CustomerRepository(db)
    customer_service = CustomerService(customer_repository)

    recharge_repository = RechargeRepository(db)
    recharge_service = RechargeService(recharge_repository)

    @tool
    async def get_customer_recharges(
        limit: int = 10,
    ) -> dict:
        """
        Retrieve recent recharge history for a customer.

        Use this tool when a customer asks about recent recharges,
        recharge history, amounts, statuses, or payment methods.
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

        # Defensive limit.
        limit = min(max(limit, 1), 20)

        recharges = await recharge_service.get_customer_recharges(
            customer,
            limit,
        )

        return {
            "found": True,
            "customer_id": customer.customer_id,
            "count": len(recharges),
            "recharges": [
                {
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
                for recharge in recharges
            ],
        }

    return [get_customer_recharges]