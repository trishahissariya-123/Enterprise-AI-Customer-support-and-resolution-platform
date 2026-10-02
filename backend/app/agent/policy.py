from dataclasses import dataclass


@dataclass(frozen=True)
class AgentExecutionPolicy:
    """
    Controls execution limits and safety boundaries
    for the customer-support agent.
    """

    max_tool_iterations: int = 5
    allow_write_tools: bool = False


DEFAULT_AGENT_POLICY = AgentExecutionPolicy()