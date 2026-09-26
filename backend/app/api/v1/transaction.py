from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.dependencies import get_db
from backend.app.repositories.customer_repository import CustomerRepository
from backend.app.repositories.transaction_repository import TransactionRepository
from backend.app.services.customer_service import CustomerService
from backend.app.services.transaction_service import TransactionService


router = APIRouter(
    prefix="/customers",
    tags=["Transactions"],
)


@router.get("/{customer_id}/transactions")
async def get_customer_transactions(
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

    transaction_repository = TransactionRepository(db)
    transaction_service = TransactionService(transaction_repository)

    transactions = await transaction_service.get_customer_transactions(
        customer,
        limit,
    )

    return {
        "customer_id": customer.customer_id,
        "count": len(transactions),
        "transactions": [
            {
                "transaction_id": transaction.transaction_id,
                "transaction_type": transaction.transaction_type,
                "status": transaction.status,
                "amount": transaction.amount,
                "currency": transaction.currency,
                "sender_customer_id": transaction.sender_customer_id,
                "receiver_customer_id": transaction.receiver_customer_id,
                "failure_reason": transaction.failure_reason,
                "created_at": transaction.created_at,
            }
            for transaction in transactions
        ],
    }
@router.get("/transactions/{transaction_id}")
async def get_transaction(
    transaction_id: str,
    db: AsyncSession = Depends(get_db),
):
    transaction_repository = TransactionRepository(db)
    transaction_service = TransactionService(transaction_repository)

    transaction = await transaction_service.get_transaction(
        transaction_id
    )

    if transaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )

    return {
        "transaction_id": transaction.transaction_id,
        "transaction_type": transaction.transaction_type,
        "status": transaction.status,
        "amount": transaction.amount,
        "currency": transaction.currency,
        "sender_customer_id": transaction.sender_customer_id,
        "receiver_customer_id": transaction.receiver_customer_id,
        "provider_reference": transaction.provider_reference,
        "failure_reason": transaction.failure_reason,
        "created_at": transaction.created_at,
    }