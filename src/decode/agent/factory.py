from pydantic_ai import Agent, DeferredToolRequests,RunContext
from pydantic_ai.models import Model
from decode.tools.skills import skill_catalog
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

    @agent.instructions
    def project_conventions(ctx: RunContext[AgentDeps]) -> str | None:
        if not ctx.deps.project_instructions:
            return None

        return (
            "Project conventions from .hypa/project.md:\n"
            f"{ctx.deps.project_instructions}\n\n"
            "The current user task may override these conventions, "
            "but core agent rules and tool permission policy still apply."
        )
    @agent.instructions
    def available_skills() -> str:
        return (
            "Available workflow skills:\n"
            f"{skill_catalog()}\n\n"
            "When a task calls for a skill, load it with load_skill "
            "before following its workflow. Skill instructions do not "
            "override the current task or tool permissions."
        )
    register_tools(agent)
    return agent