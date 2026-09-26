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


def create_merchant_payment_tools(db: AsyncSession):

    payment_repository = MerchantPaymentRepository(db)
    payment_service = MerchantPaymentService(payment_repository)
    customer_repository = CustomerRepository(db)
    customer_service = CustomerService(customer_repository)

    @tool
    async def get_merchant_payment(payment_id: str) -> dict:
        """
        Retrieve details of a specific merchant payment.

        Use this tool when a customer asks about a merchant payment,
        such as its status, amount, merchant, failure reason,
        or provider reference.
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

        payment = await payment_service.get_payment(
            payment_id
        )

        if payment is None:
            return {
                "found": False,
                "payment_id": payment_id,
                "message": "Merchant payment not found",
            }
        if (
                payment.customer_id != customer.id

        ):
            return {
                "found": False,
                "transaction_id": payment_id,
                "message": (
                    "payment id does not belong to "
                    "the authenticated customer"
                ),
            }

        return {
            "found": True,
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

    return [get_merchant_payment]