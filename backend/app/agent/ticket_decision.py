from backend.app.agent.state import AgentState


async def ticket_decision_node(
    state: AgentState,
):
    investigation_status = state.get(
        "investigation_status"
    )

    investigation_reason = state.get(
        "investigation_reason"
    )

    if investigation_status == "RESOLVED":
        return {
            "ticket_action": "RESOLVED",
            "ticket_reason": investigation_reason,
        }

    if investigation_status == "INSUFFICIENT_DATA":
        return {
            "ticket_action": "ASK_CUSTOMER",
            "ticket_reason": investigation_reason,
        }

    if investigation_status == "NEEDS_SUPPORT":
        return {
            "ticket_action": "CREATE_TICKET",
            "ticket_reason": investigation_reason,
        }

    return {
        "ticket_action": "ASK_CUSTOMER",
        "ticket_reason": (
            "The issue could not be classified "
            "for automatic resolution."
        ),
    }