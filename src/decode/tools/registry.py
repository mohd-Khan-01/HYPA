from pydantic_ai import Agent, DeferredToolRequests

from decode.agent.deps import AgentDeps
from decode.tools.files import glob, grep, read


READ_ONLY_TOOLS = (read, glob, grep)


def register_read_only_tools(
    agent: Agent[AgentDeps, str | DeferredToolRequests],
) -> None:
    for tool in READ_ONLY_TOOLS:
        agent.tool(tool)