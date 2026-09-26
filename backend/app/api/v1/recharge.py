from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.dependencies import get_db
from backend.app.repositories.customer_repository import CustomerRepository
from backend.app.repositories.recharge_repository import RechargeRepository
from backend.app.services.customer_service import CustomerService
from backend.app.services.recharge_service import RechargeService


router = APIRouter(
    prefix="/customers",
    tags=["Recharge"],
)


@router.get("/{customer_id}/recharges")
async def get_customer_recharges(
    customer_id: str,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    customer_repository = CustomerRepository(db)
    customer_service = CustomerService(customer_repository)

    customer = await customer_service.get_customer_by_id(customer_id)

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    recharge_repository = RechargeRepository(db)
    recharge_service = RechargeService(recharge_repository)

    recharges = await recharge_service.get_customer_recharges(
        customer,
        limit,
    )

    return {
        "customer_id": customer.customer_id,
        "count": len(recharges),
        "recharges": [
            {
                "recharge_id": recharge.recharge_id,
                "amount": recharge.amount,
                "currency": recharge.currency,
                "status": recharge.status,
                "payment_method": recharge.payment_method,
                "provider_reference": recharge.provider_reference,
                "failure_reason": recharge.failure_reason,
                "created_at": recharge.created_at,
            }
            for recharge in recharges
        ],
    }


@router.get("/recharges/{recharge_id}")
async def get_recharge(
    recharge_id: str,
    db: AsyncSession = Depends(get_db),
):
    recharge_repository = RechargeRepository(db)
    recharge_service = RechargeService(recharge_repository)

    recharge = await recharge_service.get_recharge(recharge_id)

    if recharge is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recharge not found",
        )

    return {
        "recharge_id": recharge.recharge_id,
        "amount": recharge.amount,
        "currency": recharge.currency,
        "status": recharge.status,
        "payment_method": recharge.payment_method,
        "provider_reference": recharge.provider_reference,
        "failure_reason": recharge.failure_reason,
        "created_at": recharge.created_at,
    }