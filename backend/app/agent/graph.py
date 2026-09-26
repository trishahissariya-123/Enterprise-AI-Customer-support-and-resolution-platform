from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from backend.app.agent.nodes import (
    create_agent_node,
    triage_node,
    create_knowledge_node,
)
from backend.app.agent.state import AgentState
from backend.app.tools.registry import create_all_tools
from backend.app.agent.intent import Intent


def route_after_triage(state: AgentState):
    intent = state.get("intent")

    if intent == Intent.KNOWLEDGE.value:
        return "knowledge"

    return "agent"


def route_after_agent(state: AgentState):

    last_message = state["messages"][-1]

    if getattr(last_message, "tool_calls", None):
        return "tools"

    return END


def create_agent_graph(db):

    tools = create_all_tools(db)

    agent_node = create_agent_node(db)
    tool_node = ToolNode(tools)
    knowledge_workflow = create_knowledge_node(db)

    graph = StateGraph(AgentState)

    # -------------------------
    # Nodes
    # -------------------------

    graph.add_node("triage", triage_node)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    graph.add_node("knowledge", knowledge_workflow)

    # -------------------------
    # START → TRIAGE
    # -------------------------

    graph.add_edge(
        START,
        "triage",
    )

    # -------------------------
    # TRIAGE → KNOWLEDGE / AGENT
    # -------------------------

    graph.add_conditional_edges(
        "triage",
        route_after_triage,
        {
            "knowledge": "knowledge",
            "agent": "agent",
        },
    )

    # -------------------------
    # AGENT → TOOLS / END
    # -------------------------

    graph.add_conditional_edges(
        "agent",
        route_after_agent,
        {
            "tools": "tools",
            END: END,
        },
    )

    # -------------------------
    # TOOLS → AGENT
    # -------------------------

    graph.add_edge(
        "tools",
        "agent",
    )

    # -------------------------
    # KNOWLEDGE → END
    # -------------------------

    graph.add_edge(
        "knowledge",
        END,
    )

    return graph.compile()