import time
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
from backend.app.core.logging import get_logger
from backend.app.core.request_context import get_request_id

logger = get_logger(__name__)

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


def create_agent_graph(db, checkpointer=None,   kafka_producer=None,):

    tools = create_all_tools(db, kafka_producer,)

    agent_node = create_agent_node(db, kafka_producer,)
    tool_node = ToolNode(tools)
    knowledge_workflow = create_knowledge_node(db)
    transaction_investigation = create_transaction_investigation_node(db)
    recharge_investigation = create_recharge_investigation_node(db)
    wallet_investigation = create_wallet_investigation_node(db)

    async def safe_tool_node(state: AgentState):
        request_id = get_request_id()

        last_message = state["messages"][-1]
        tool_calls = getattr(last_message, "tool_calls", []) or []

        if not tool_calls:
            return {
                "messages": []
            }

        tool_messages = []

        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            tool = next(
                (
                    current_tool
                    for current_tool in tools
                    if current_tool.name == tool_name
                ),
                None,
            )

            if tool is None:
                logger.warning(
                    "Tool not found | request_id=%s | tool=%s",
                    request_id,
                    tool_name,
                )

                tool_messages.append(
                    ToolMessage(
                        content="Requested tool is unavailable.",
                        tool_call_id=tool_call["id"],
                    )
                )
                continue

            start_time = time.perf_counter()

            logger.info(
                "Tool started | request_id=%s | tool=%s",
                request_id,
                tool_name,
            )

            try:
                result = await tool.ainvoke(
                    tool_call["args"]
                )

                duration_ms = (
                                      time.perf_counter() - start_time
                              ) * 1000

                logger.info(
                    "Tool completed | request_id=%s | tool=%s | duration_ms=%.2f",
                    request_id,
                    tool_name,
                    duration_ms,
                )

                tool_messages.append(
                    ToolMessage(
                        content=str(result),
                        tool_call_id=tool_call["id"],
                    )
                )

            except Exception:
                duration_ms = (
                                      time.perf_counter() - start_time
                              ) * 1000

                logger.exception(
                    "Tool failed | request_id=%s | tool=%s | duration_ms=%.2f",
                    request_id,
                    tool_name,
                    duration_ms,
                )

                tool_messages.append(
                    ToolMessage(
                        content="The requested operation could not be completed.",
                        tool_call_id=tool_call["id"],
                    )
                )

        return {
            "messages": tool_messages,
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