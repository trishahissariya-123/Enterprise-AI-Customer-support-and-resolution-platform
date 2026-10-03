from typing import Any

from langgraph.graph import MessagesState


class AgentState(MessagesState):
    """
    State maintained by the customer-support agent.

    MessagesState stores the conversation messages,
    including customer messages, AI responses,
    and tool results.
    """

    customer_id: str | None = None
    intent: str
    triage_reason: str | None = None
    tool_iterations: int= 0
    # Investigation state
    investigation_required: bool = False
    investigation_type: str | None = None
    investigation_route: str | None
    transaction_result: dict[str, Any] | None = None
    recharge_result: dict[str, Any] | None = None
    wallet_result: dict[str, Any] | None = None

    investigation_status: str | None = None
    investigation_reason: str | None = None
    allow_write_tools: bool = False
    ticket_action: str | None
    ticket_reason: str | None

    # LLM usage / cost tracking
    llm_input_tokens: int = 0
    llm_output_tokens: int = 0
    llm_total_tokens: int = 0
    llm_estimated_cost_usd: float = 0.0
    llm_call_count: int = 0