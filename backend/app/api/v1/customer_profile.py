from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.dependencies import get_db
from backend.app.repositories.customer_profile_repository import (
    CustomerProfileRepository,
)
from backend.app.repositories.customer_repository import CustomerRepository
from backend.app.services.customer_profile_service import (
    CustomerProfileService,
)
from backend.app.services.customer_service import CustomerService


router = APIRouter(
    prefix="/customers",
    tags=["Customer Profile"],
)


@router.get("/{customer_id}/profile")
async def get_customer_profile(
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

    profile_repository = CustomerProfileRepository(db)
    profile_service = CustomerProfileService(
        profile_repository
    )

    profile = await profile_service.get_profile(customer)

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer profile not found",
        )

    return {
        "customer_id": customer.customer_id,
        "first_name": profile.first_name,
        "last_name": profile.last_name,
        "country": profile.country,
        "language": profile.language,
    }