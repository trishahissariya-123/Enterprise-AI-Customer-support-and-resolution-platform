from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.dependencies import get_db
from backend.app.repositories.customer_repository import CustomerRepository
from backend.app.repositories.merchant_payment_repository import (
    MerchantPaymentRepository,
)
from backend.app.services.customer_service import CustomerService
from backend.app.services.merchant_payment_service import (
    MerchantPaymentService,
)


router = APIRouter(
    prefix="/customers",
    tags=["Merchant Payments"],
)


@router.get("/{customer_id}/merchant-payments")
async def get_customer_payments(
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

    payment_repository = MerchantPaymentRepository(db)
    payment_service = MerchantPaymentService(payment_repository)

    payments = await payment_service.get_customer_payments(
        customer,
        limit,
    )

    return {
        "customer_id": customer.customer_id,
        "count": len(payments),
        "payments": [
            {
                "payment_id": payment.payment_id,
                "merchant_id": payment.merchant_id,
                "amount": payment.amount,
                "currency": payment.currency,
                "status": payment.status,
                "provider_reference": payment.provider_reference,
                "failure_reason": payment.failure_reason,
                "created_at": payment.created_at,
            }
            for payment in payments
        ],
    }


@router.get("/merchant-payments/{payment_id}")
async def get_payment(
    payment_id: str,
    db: AsyncSession = Depends(get_db),
):
    payment_repository = MerchantPaymentRepository(db)
    payment_service = MerchantPaymentService(payment_repository)

    payment = await payment_service.get_payment(payment_id)

    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Merchant payment not found",
        )

    return {
        "payment_id": payment.payment_id,
        "merchant_id": payment.merchant_id,
        "amount": payment.amount,
        "currency": payment.currency,
        "status": payment.status,
        "provider_reference": payment.provider_reference,
        "failure_reason": payment.failure_reason,
        "created_at": payment.created_at,
    }