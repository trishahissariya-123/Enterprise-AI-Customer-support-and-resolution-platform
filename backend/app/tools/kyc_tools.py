from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.tools import tool

from backend.app.repositories.customer_repository import CustomerRepository
from backend.app.repositories.kyc_repository import KYCRepository
from backend.app.services.customer_service import CustomerService
from backend.app.services.kyc_service import KYCService
from backend.app.agent.context import get_current_customer_id

def create_kyc_tools(db: AsyncSession):

    customer_repository = CustomerRepository(db)
    customer_service = CustomerService(customer_repository)

    kyc_repository = KYCRepository(db)
    kyc_service = KYCService(kyc_repository)

    @tool
    async def get_kyc_status() -> dict:
        """
        Retrieve the KYC verification status for a customer.

        Use this tool when a customer asks about their KYC status,
        verification type, rejection reason, or verification date.
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

        kyc = await kyc_service.get_kyc_status(customer)

        if kyc is None:
            return {
                "found": False,
                "customer_id": customer_id,
                "message": "KYC record not found",
            }

        return {
            "found": True,
            "customer_id": customer.customer_id,
            "kyc_status": kyc.status,
            "verification_type": kyc.verification_type,
            "rejection_reason": kyc.rejection_reason,
            "verified_at": (
                kyc.verified_at.isoformat()
                if kyc.verified_at
                else None
            ),
        }

    return [get_kyc_status]