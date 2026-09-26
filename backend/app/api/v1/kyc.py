from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.dependencies import get_db
from backend.app.repositories.customer_repository import CustomerRepository
from backend.app.repositories.kyc_repository import KYCRepository
from backend.app.services.customer_service import CustomerService
from backend.app.services.kyc_service import KYCService


router = APIRouter(
    prefix="/customers",
    tags=["KYC"],
)


@router.get("/{customer_id}/kyc")
async def get_customer_kyc(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
):
    customer_repository = CustomerRepository(db)
    customer_service = CustomerService(customer_repository)

    customer = await customer_service.get_customer_by_id(
        customer_id
    )

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    kyc_repository = KYCRepository(db)
    kyc_service = KYCService(kyc_repository)

    kyc = await kyc_service.get_kyc_status(customer)

    if kyc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="KYC record not found",
        )

    return {
        "customer_id": customer.customer_id,
        "kyc_status": kyc.status,
        "verification_type": kyc.verification_type,
        "rejection_reason": kyc.rejection_reason,
        "verified_at": kyc.verified_at,
    }