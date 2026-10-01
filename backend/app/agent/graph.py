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

def route_after_triage(state: AgentState):
    intent = state.get("intent")

    messages = state.get("messages", [])

    latest_message = ""
    for message in reversed(messages):
        if getattr(message, "type", None) == "human":
            latest_message = message.content.lower()
            break

    # Complex recharge/transaction issue requiring
    # transaction + recharge correlation.
    investigation_keywords = [
        "wallet was debited",
        "wallet debited",
        "money was deducted",
        "money deducted",
        "amount deducted",
        "recharge didn't happen",
        "recharge did not happen",
        "recharge failed",
        "recharge pending",
        "charged but",
        "debited but",
    ]

    requires_investigation = any(
        keyword in latest_message
        for keyword in investigation_keywords
    )

    if requires_investigation and intent in {
        "RECHARGE",
        "TRANSACTION",
    }:
        return "investigation"

    if intent == "KNOWLEDGE":
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
            "investigation": "transaction_investigation",
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
        "agent",
    )


    return graph.compile(checkpointer=checkpointer)