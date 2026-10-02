from pydantic import BaseModel, Field
from typing import Literal
from backend.app.agent.intent import Intent


class TriageResult(BaseModel):
    intent: Intent = Field(
        description="The single most relevant capability required to answer the customer's request."
    )
    investigation_required: bool = Field(
        description=(
            "Whether the request requires deterministic investigation "
            "of customer-specific financial state before responding."
        )
    )
    reason: str = Field(
        description="Short explanation for why this intent was selected."
    )
    investigation_type: str | None = Field(
        default=None,
        description=(
            "The investigation workflow required for the request. "
            "Examples: transaction_recharge, merchant_payment, "
            "wallet_transaction, or None."
        ),
    )

class TicketDecision(BaseModel):
    action: Literal[
        "RESOLVED",
        "ASK_CUSTOMER",
        "CREATE_TICKET",
    ] = Field(
        description=(
            "Determines what should happen after investigation."
        )
    )

    reason: str = Field(
        description=(
            "Short explanation for the selected action."
        )
    )