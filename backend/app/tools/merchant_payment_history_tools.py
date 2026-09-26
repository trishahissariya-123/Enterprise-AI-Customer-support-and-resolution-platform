from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.tools import tool

from backend.app.agent.context import get_current_customer_id
from backend.app.repositories.customer_repository import CustomerRepository
from backend.app.repositories.merchant_payment_repository import (
    MerchantPaymentRepository,
)
from backend.app.services.customer_service import CustomerService
from backend.app.services.merchant_payment_service import (
    MerchantPaymentService,
)


def create_merchant_payment_history_tools(db: AsyncSession):

    customer_repository = CustomerRepository(db)
    customer_service = CustomerService(customer_repository)

    payment_repository = MerchantPaymentRepository(db)
    payment_service = MerchantPaymentService(payment_repository)

    @tool
    async def get_customer_merchant_payments(
        limit: int = 10,
    ) -> dict:
        """
        Retrieve recent merchant payment history for a customer.

        Use this tool when a customer asks about recent merchant
        payments, payment amounts, statuses, or payment history.
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

        payments = await payment_service.get_customer_payments(
            customer,
            limit,
        )

        return {
            "found": True,
            "customer_id": customer.customer_id,
            "count": len(payments),
            "payments": [
                {
                    "payment_id": payment.payment_id,
                    "merchant_id": payment.merchant_id,
                    "amount": str(payment.amount),
                    "currency": payment.currency,
                    "status": payment.status,
                    "provider_reference": payment.provider_reference,
                    "failure_reason": payment.failure_reason,
                    "created_at": (
                        payment.created_at.isoformat()
                        if payment.created_at
                        else None
                    ),
                }
                for payment in payments
            ],
        }

    return [get_customer_merchant_payments]