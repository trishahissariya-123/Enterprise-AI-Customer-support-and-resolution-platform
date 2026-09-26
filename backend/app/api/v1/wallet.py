from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.dependencies import get_db
from backend.app.repositories.customer_repository import CustomerRepository
from backend.app.repositories.wallet_repository import WalletRepository
from backend.app.services.customer_service import CustomerService
from backend.app.services.wallet_service import WalletService


router = APIRouter(
    prefix="/customers",
    tags=["Wallet"],
)


@router.get("/{customer_id}/wallet")
async def get_customer_wallet(
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

    wallet_repository = WalletRepository(db)
    wallet_service = WalletService(wallet_repository)

    wallet = await wallet_service.get_wallet(customer)

    if wallet is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not found",
        )

    return {
        "customer_id": customer.customer_id,
        "currency": wallet.currency,
        "balance": wallet.balance,
        "status": wallet.status,
    }