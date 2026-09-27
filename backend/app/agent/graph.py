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


def route_after_triage(state: AgentState):
    intent = state.get("intent")

    if intent == Intent.KNOWLEDGE.value:
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


    return graph.compile(checkpointer=checkpointer)