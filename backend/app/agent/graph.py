from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode
from langchain_core.messages import ToolMessage
from backend.app.agent.nodes import (
    create_agent_node,
    triage_node,
    create_knowledge_node, agent_limit_handler,
)
from backend.app.agent.state import AgentState
from backend.app.tools.registry import create_all_tools
from backend.app.agent.intent import Intent
from backend.app.agent.policy import DEFAULT_AGENT_POLICY
from backend.app.agent.investigation import (
    create_transaction_investigation_node,
    create_recharge_investigation_node,
    investigation_decision_node,
    create_wallet_investigation_node,
)
from backend.app.agent.investigation_supervisor import (
    investigation_supervisor,
)
from backend.app.agent.ticket_decision import (
    ticket_decision_node,
)
from backend.app.agent.human_approval import (
    human_approval_node,
)

def route_after_triage(state: AgentState):
    intent=state.get("intent")
    investigation_required = state.get(
        "investigation_required",
        False,
    )
    if intent=="SUPPORT_TICKET":
        return "human_approval"

    if investigation_required:
        return "investigation_supervisor"


    if state.get("intent") == "KNOWLEDGE":
        return "knowledge"

    return "agent"


def route_after_agent(state: AgentState):

    last_message = state["messages"][-1]

    if not getattr(last_message, "tool_calls", None):
        return END

    current_iterations = state.get("tool_iterations", 0)

    if current_iterations >= DEFAULT_AGENT_POLICY.max_tool_iterations:
        return "limit_reached"

    return "tool_guard"
def route_after_ticket_decision(
    state: AgentState,
):
    action = state.get(
        "ticket_action",
        "ASK_CUSTOMER",
    )

    if action == "CREATE_TICKET":
        return "human_approval"

    return "agent"

def route_after_investigation_supervisor(
    state: AgentState,
):
    route = state.get(
        "investigation_route",
        "none",
    )

    if route == "transaction_recharge":
        return "transaction_recharge"

    if route == "wallet_transaction":
        return "wallet_transaction"

    if route == "merchant_payment":
        return "merchant_payment"

    return "agent"

def increment_tool_iteration(state: AgentState):

    current = state.get("tool_iterations", 0)

    return {
        "tool_iterations": current + 1
    }


def create_agent_graph(db, checkpointer=None):

    tools = create_all_tools(db)

    agent_node = create_agent_node(db)
    tool_node = ToolNode(tools)
    knowledge_workflow = create_knowledge_node(db)
    transaction_investigation = create_transaction_investigation_node(db)
    recharge_investigation = create_recharge_investigation_node(db)
    wallet_investigation = create_wallet_investigation_node(db)
    async def safe_tool_node(state: AgentState):
        try:
            result = await tool_node.ainvoke(state)
            return result

        except Exception as exc:
            return {
                "messages": [
                    ToolMessage(
                        content=(
                            "The requested tool could not be executed. "
                            "The system encountered a temporary internal error."
                        ),
                        tool_call_id=(
                            state["messages"][-1].tool_calls[0]["id"]
                            if getattr(state["messages"][-1], "tool_calls", None)
                            else "unknown"
                        ),
                    )
                ]
            }

    graph = StateGraph(AgentState)

    # Nodes
    graph.add_node("triage", triage_node)
    graph.add_node("agent", agent_node)
    graph.add_node("tool_guard", increment_tool_iteration)
    graph.add_node("tools", safe_tool_node)
    graph.add_node("knowledge", knowledge_workflow)
    graph.add_node("limit_handler", agent_limit_handler)
    graph.add_node(
        "transaction_investigation",
        transaction_investigation,
    )
    graph.add_node(
        "wallet_investigation",
        wallet_investigation,
    )

    graph.add_node(
        "recharge_investigation",
        recharge_investigation,
    )

    graph.add_node(
        "investigation_decision",
        investigation_decision_node,
    )
    graph.add_node(
        "investigation_supervisor",
        investigation_supervisor,
    )
    graph.add_node(
        "ticket_decision",
        ticket_decision_node,
    )
    graph.add_node(
        "human_approval",
        human_approval_node,
    )
    # START → TRIAGE
    graph.add_edge(
        START,
        "triage",
    )

    # TRIAGE → KNOWLEDGE / AGENT
    graph.add_conditional_edges(
        "triage",
        route_after_triage,
        {
            "knowledge": "knowledge",
            "investigation_supervisor": "investigation_supervisor",
            "human_approval": "human_approval",
            "agent": "agent",
        },
    )
    graph.add_conditional_edges(
        "investigation_supervisor",
        route_after_investigation_supervisor,
        {
            "transaction_recharge": "transaction_investigation",
            "wallet_transaction": "transaction_investigation",
            "merchant_payment": "agent",
            "agent": "agent",
        },
    )

    # AGENT → TOOL GUARD / END
    graph.add_conditional_edges(
        "agent",
        route_after_agent,
        {
            "tool_guard": "tool_guard",
            "limit_reached": "limit_handler",
            END: END,
        },
    )

    # TOOL GUARD → TOOLS
    graph.add_edge(
        "tool_guard",
        "tools",
    )

    # TOOLS → AGENT
    graph.add_edge(
        "tools",
        "agent",
    )

    # KNOWLEDGE → END
    graph.add_edge(
        "knowledge",
        END,
    )
    graph.add_edge(
        "limit_handler",
        END,
    )
    graph.add_edge(
        "transaction_investigation",
        "recharge_investigation",
    )

    graph.add_edge(
        "recharge_investigation",
        "wallet_investigation",
    )
    graph.add_edge(
        "wallet_investigation",
        "investigation_decision",
    )
    graph.add_edge(
        "investigation_decision",
        "ticket_decision",
    )
    graph.add_conditional_edges(
        "ticket_decision",
        route_after_ticket_decision,{
            "human_approval": "human_approval",
            "agent":"agent",
        },
    )
    graph.add_edge(
        "human_approval",
        "agent",
    )


    return graph.compile(checkpointer=checkpointer)