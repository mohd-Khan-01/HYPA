from pydant_ai import Agent
from decode.agent.deps import AgentDeps
from decode.tools.files import read

def build_agent()->Agent[AgentDeps,str]:
    agent = Agent(
        "openai:gpt-5.6",
        deps_type=AgentDeps,
    )
    agent.tool(read)
    return agent
