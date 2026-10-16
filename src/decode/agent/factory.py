from pydantic_ai import Agent, DeferredToolRequests
from pydantic_ai.models import Model

from decode.agent.deps import AgentDeps
from decode.tools.registry import register_tools


def build_agent(
    model: Model,
) -> Agent[AgentDeps, str | DeferredToolRequests]:
    agent: Agent[AgentDeps, str | DeferredToolRequests] = Agent(
        model,
        deps_type=AgentDeps,
        output_type=[str, DeferredToolRequests],
        instructions=(
            "You are HYPA, a coding assistant. "
            "Use tools to inspect files before making claims "
            "about their contents. "
            "Never invent tool results. "
            "Respect tool refusals and policy denials. "
            "Do not retry a refused change through another tool. "
            "For execute, pass argv as a list and use python -B "
            "for Python checks. "
            "Only report a check passed after observing its "
            "successful exit code and relevant output. "
            "Command output may be truncated; say so when "
            "that limits your conclusions."
        ),
    )

    register_tools(agent)
    return agent