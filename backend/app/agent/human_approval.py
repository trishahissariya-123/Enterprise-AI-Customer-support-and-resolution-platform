from langgraph.types import interrupt


async def human_approval_node(state):
    ticket_reason = state.get(
        "ticket_reason",
        "The issue requires human support.",
    )

    decision = interrupt(
        {
            "type": "ticket_approval",
            "message": "Human approval is required before creating a support ticket.",
            "reason": ticket_reason,
        }
    )

    if decision == "approve":
        return {
            "allow_write_tools": True,
            "ticket_action": "CREATE_TICKET",
        }

    return {
        "allow_write_tools": False,
        "ticket_action": "ASK_CUSTOMER",
    }