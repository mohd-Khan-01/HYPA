from pydantic_ai import Agent, DeferredToolRequests
from decode.tools.skills import load_skill
from decode.agent.deps import AgentDeps
from decode.tools.commands import execute
from decode.tools.files import edit, glob, grep, read, write


READ_ONLY_TOOLS = (read, glob, grep)
FILE_TOOLS = (*READ_ONLY_TOOLS, write, edit)
AGENT_TOOLS = (*FILE_TOOLS, execute, load_skill)


def register_read_only_tools(
    agent: Agent[AgentDeps, str | DeferredToolRequests],
) -> None:
    for tool in READ_ONLY_TOOLS:
        agent.tool(tool)


def register_file_tools(
    agent: Agent[AgentDeps, str | DeferredToolRequests],
) -> None:
    for tool in FILE_TOOLS:
        agent.tool(tool)


def register_tools(
    agent: Agent[AgentDeps, str | DeferredToolRequests],
) -> None:
    for tool in AGENT_TOOLS:
        agent.tool(tool)