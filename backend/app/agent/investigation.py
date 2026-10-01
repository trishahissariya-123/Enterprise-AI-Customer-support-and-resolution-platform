from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.agent.context import get_current_customer_id
from backend.app.repositories.customer_repository import CustomerRepository
from backend.app.repositories.transaction_repository import TransactionRepository
from backend.app.repositories.wallet_repository import WalletRepository
from backend.app.services.customer_service import CustomerService
from backend.app.services.transaction_service import TransactionService
from backend.app.repositories.recharge_repository import RechargeRepository
from backend.app.services.recharge_service import RechargeService
from backend.app.services.wallet_service import WalletService


def create_transaction_investigation_node(db: AsyncSession):

    customer_repository = CustomerRepository(db)
    customer_service = CustomerService(customer_repository)

    transaction_repository = TransactionRepository(db)
    transaction_service = TransactionService(transaction_repository)

    async def transaction_investigation_node(state):

        customer_id = get_current_customer_id()

        if customer_id is None:
            return {
                "transaction_result": {
                    "found": False,
                    "message": "Authenticated customer context is missing",
                }
            }

        customer = await customer_service.get_customer_by_id(customer_id)

        if customer is None:
            return {
                "transaction_result": {
                    "found": False,
                    "message": "Authenticated customer not found",
                }
            }

        messages = state["messages"]

        latest_user_message = None

        for message in reversed(messages):
            if getattr(message, "type", None) == "human":
                latest_user_message = message.content
                break

        if not latest_user_message:
            return {
                "transaction_result": {
                    "found": False,
                    "message": "Customer request could not be identified",
                }
            }

        transaction_id = None

        # Look for a transaction ID in the customer's request.
        words = latest_user_message.split()

        for word in words:
            cleaned = word.strip(".,!?():;")

            if cleaned.upper().startswith("TXN-"):
                transaction_id = cleaned.upper()
                break

        # ---------------------------------------------------------
        # Case 1: Transaction ID was provided
        # ---------------------------------------------------------
        if transaction_id is not None:

            transaction = await transaction_service.get_transaction(
                transaction_id
            )

            if transaction is None:
                return {
                    "transaction_result": {
                        "found": False,
                        "transaction_id": transaction_id,
                        "message": "Transaction not found",
                    }
                }

            # Authorization check.
            if (
                transaction.sender_customer_id != customer.id
                and transaction.receiver_customer_id != customer.id
            ):
                return {
                    "transaction_result": {
                        "found": False,
                        "transaction_id": transaction_id,
                        "message": (
                            "Transaction does not belong to "
                            "the authenticated customer"
                        ),
                    }
                }

        # ---------------------------------------------------------
        # Case 2: Transaction ID was not provided
        # Use recent transactions belonging to authenticated customer
        # ---------------------------------------------------------
        else:

            transactions = await transaction_service.get_customer_transactions(
                customer,
                limit=5,
            )

            if not transactions:
                return {
                    "transaction_result": {
                        "found": False,
                        "message": "No recent customer transactions were found",
                    }
                }

            # Use the most recent transaction as the candidate.
            transaction = transactions[0]

        return {
            "transaction_result": {
                "found": True,
                "transaction_id": transaction.transaction_id,
                "transaction_type": transaction.transaction_type,
                "status": transaction.status,
                "amount": str(transaction.amount),
                "currency": transaction.currency,
                "failure_reason": transaction.failure_reason,
                "provider_reference": transaction.provider_reference,
                "created_at": (
                    transaction.created_at.isoformat()
                    if transaction.created_at
                    else None
                ),
            }
        }

    return transaction_investigation_node

def create_recharge_investigation_node(db: AsyncSession):

    customer_repository = CustomerRepository(db)
    customer_service = CustomerService(customer_repository)

    recharge_repository = RechargeRepository(db)
    recharge_service = RechargeService(recharge_repository)

    async def recharge_investigation_node(state):

        customer_id = get_current_customer_id()

        if customer_id is None:
            return {
                "recharge_result": {
                    "found": False,
                    "message": "Authenticated customer context is missing",
                }
            }

        customer = await customer_service.get_customer_by_id(customer_id)

        if customer is None:
            return {
                "recharge_result": {
                    "found": False,
                    "message": "Authenticated customer not found",
                }
            }

        messages = state["messages"]

        latest_user_message = None

        for message in reversed(messages):
            if getattr(message, "type", None) == "human":
                latest_user_message = message.content
                break

        if not latest_user_message:
            return {
                "recharge_result": {
                    "found": False,
                    "message": "Customer request could not be identified",
                }
            }

        recharge_id = None

        # Look for a recharge ID in the customer's request.
        words = latest_user_message.split()

        for word in words:
            cleaned = word.strip(".,!?():;")

            if cleaned.upper().startswith("RECH-"):
                recharge_id = cleaned.upper()
                break

        if recharge_id is not None:

            # Explicit recharge ID provided by customer.
            recharge = await recharge_service.get_recharge(
                recharge_id
            )

            if recharge is None:
                return {
                    "recharge_result": {
                        "found": False,
                        "recharge_id": recharge_id,
                        "message": "Recharge not found",
                    }
                }

            # Authorization check.
            if recharge.customer_id != customer.id:
                return {
                    "recharge_result": {
                        "found": False,
                        "recharge_id": recharge_id,
                        "message": (
                            "Recharge does not belong to "
                            "the authenticated customer"
                        ),
                    }
                }

        else:

            # No recharge ID provided.
            # Retrieve recent recharges for the authenticated customer.
            recharges = await recharge_service.get_customer_recharges(
                customer,
                limit=5,
            )

            if not recharges:
                return {
                    "recharge_result": {
                        "found": False,
                        "message": "No recent customer recharges were found",
                    }
                }

            # Use the most recent recharge as the candidate.
            recharge = recharges[0]
        return {
            "recharge_result": {
                "found": True,
                "recharge_id": recharge.recharge_id,
                "amount": str(recharge.amount),
                "currency": recharge.currency,
                "status": recharge.status,
                "payment_method": recharge.payment_method,
                "provider_reference": recharge.provider_reference,
                "failure_reason": recharge.failure_reason,
                "created_at": (
                    recharge.created_at.isoformat()
                    if recharge.created_at
                    else None
                ),
            }
        }

    return recharge_investigation_node

def create_wallet_investigation_node(db: AsyncSession):

    customer_repository = CustomerRepository(db)
    customer_service = CustomerService(customer_repository)

    wallet_repository = WalletRepository(db)
    wallet_service = WalletService(wallet_repository)

    async def wallet_investigation_node(state):

        customer_id = get_current_customer_id()

        if customer_id is None:
            return {
                "wallet_result": {
                    "found": False,
                    "message": "Authenticated customer context is missing",
                }
            }

        customer = await customer_service.get_customer_by_id(
            customer_id
        )

        if customer is None:
            return {
                "wallet_result": {
                    "found": False,
                    "message": "Authenticated customer not found",
                }
            }

        # Retrieve wallet using the authenticated customer.
        # Do not use customer.wallet because async lazy loading
        # can cause MissingGreenlet errors.
        wallet = await wallet_service.get_wallet(customer)

        if wallet is None:
            return {
                "wallet_result": {
                    "found": False,
                    "message": "Customer wallet was not found",
                }
            }

        return {
            "wallet_result": {
                "found": True,
                "wallet_id": wallet.wallet_id,
                "balance": str(wallet.balance),
                "currency": wallet.currency,
                "status": wallet.status,
            }
        }

    return wallet_investigation_node
async def investigation_decision_node(state):


        transaction = state.get("transaction_result")
        recharge = state.get("recharge_result")
        wallet = state.get("wallet_result")
        if not wallet or not wallet.get("found"):
            return {
                "investigation_status": "INSUFFICIENT_DATA",
                "investigation_reason": (
                    "Customer wallet information could not be verified."
                ),
            }

        if not transaction or not transaction.get("found"):
            return {
                "investigation_status": "INSUFFICIENT_DATA",
                "investigation_reason": (
                    "Transaction information could not be verified."
                ),
            }

        if not recharge or not recharge.get("found"):
            return {
                "investigation_status": "INSUFFICIENT_DATA",
                "investigation_reason": (
                    "Recharge information could not be verified."
                ),
            }

        transaction_status = transaction.get("status")
        recharge_status = recharge.get("status")

        transaction_amount = transaction.get("amount")
        recharge_amount = recharge.get("amount")

        transaction_reference = transaction.get("provider_reference")
        recharge_reference = recharge.get("provider_reference")

        # ---------------------------------------------------------
        # 1. Verify amount consistency
        # ---------------------------------------------------------
        if transaction_amount != recharge_amount:
            return {
                "investigation_status": "NEEDS_SUPPORT",
                "investigation_reason": (
                    "The transaction amount and recharge amount do not match."
                ),
            }

        # ---------------------------------------------------------
        # 2. Verify provider reference when both are available
        # ---------------------------------------------------------
        if (
                transaction_reference
                and recharge_reference
                and transaction_reference != recharge_reference
        ):
            return {
                "investigation_status": "NEEDS_SUPPORT",
                "investigation_reason": (
                    "The transaction and recharge have different "
                    "provider references, so their relationship "
                    "could not be verified."
                ),
            }

        # ---------------------------------------------------------
        # 3. Successful transaction + failed/pending recharge
        # ---------------------------------------------------------
        if (
                transaction_status == "SUCCESS"
                and recharge_status in {"FAILED", "PENDING"}
        ):
            return {
                "investigation_status": "NEEDS_SUPPORT",
                "investigation_reason": (
                    "The payment transaction succeeded, but the "
                    "recharge is not in a completed state."
                ),
            }

        # ---------------------------------------------------------
        # 4. Both successful
        # ---------------------------------------------------------
        if (
                transaction_status == "SUCCESS"
                and recharge_status == "SUCCESS"
        ):
            return {
                "investigation_status": "RESOLVED",
                "investigation_reason": (
                    "The payment transaction and recharge both "
                    "completed successfully."
                ),
            }

        # ---------------------------------------------------------
        # 5. Transaction failed
        # ---------------------------------------------------------
        if transaction_status == "FAILED":
            return {
                "investigation_status": "RESOLVED",
                "investigation_reason": (
                    "The payment transaction failed, so the "
                    "recharge was not successfully funded."
                ),
            }

        # ---------------------------------------------------------
        # 6. Recharge failed
        # ---------------------------------------------------------
        if recharge_status == "FAILED":
            return {
                "investigation_status": "NEEDS_SUPPORT",
                "investigation_reason": (
                    "The recharge failed and requires further "
                    "support investigation."
                ),
            }

        # ---------------------------------------------------------
        # 7. Unknown/unhandled combination
        # ---------------------------------------------------------
        return {
            "investigation_status": "NEEDS_SUPPORT",
            "investigation_reason": (
                "The transaction and recharge states require "
                "additional support investigation."
            ),
        }