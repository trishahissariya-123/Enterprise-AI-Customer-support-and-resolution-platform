from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.dependencies import create_access_token, get_db
from backend.app.repositories.customer_repository import CustomerRepository
from backend.app.services.customer_service import CustomerService


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


class LoginRequest(BaseModel):
    customer_id: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Temporary customer login for local development.

    In production this will be replaced by OTP/password/KYC-based
    authentication.
    """

    customer_repository = CustomerRepository(db)
    customer_service = CustomerService(customer_repository)

    customer = await customer_service.get_customer_by_id(
        request.customer_id
    )

    if customer is None:
        raise HTTPException(
            status_code=401,
            detail="Customer not found",
        )

    if customer.status != "ACTIVE":
        raise HTTPException(
            status_code=403,
            detail="Customer account is not active",
        )

    access_token = create_access_token(
        customer_id=customer.customer_id
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }