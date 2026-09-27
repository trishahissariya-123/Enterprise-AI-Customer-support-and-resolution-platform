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
