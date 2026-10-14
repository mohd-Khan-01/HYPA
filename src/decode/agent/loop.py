from pydantic_ai import Agent, DeferredToolRequests
from pydantic_ai.messages import ToolReturnPart
from pydantic_ai.run import AgentRunResult
from pydantic_ai.tools import DeferredToolResults
from pydantic_ai.usage import RunUsage, UsageLimits

from decode.agent.deps import AgentDeps
from decode.entities.events import ToolCallStarted, ToolResult


async def run_turn(
    agent: Agent[AgentDeps, str | DeferredToolRequests],
    prompt: str,
    deps: AgentDeps,
) -> AgentRunResult[str | DeferredToolRequests]:
    usage = RunUsage()
    limits = UsageLimits(
        request_limit=5,
        tool_calls_limit=6,
    )
    seen_results: set[str] = set()

    result = await agent.run(
        prompt,
        deps=deps,
        usage=usage,
        usage_limits=limits,
    )

    while True:
        # History is carried across resume legs; emit each result once.
        for message in result.all_messages():
            for part in message.parts:
                if (
                    isinstance(part, ToolReturnPart)
                    and part.tool_call_id not in seen_results
                ):
                    seen_results.add(part.tool_call_id)
                    deps.emit(
                        ToolResult(
                            tool_name=part.tool_name,
                            result=str(part.content),
                        )
                    )

        if not isinstance(result.output, DeferredToolRequests):
            return result

        pending = result.output

        if pending.calls or not pending.approvals:
            raise RuntimeError(
                "This runner handles local approval requests only."
            )

        approvals: dict[str, bool] = {}

        for call in pending.approvals:
            decision = deps.gate(call.tool_name)

            if decision == "ask":
                raise RuntimeError(
                    "Interactive approval handling comes next. "
                    "Only read-only tools should be registered."
                )

            approvals[call.tool_call_id] = decision == "allow"

            if decision == "allow":
                deps.emit(ToolCallStarted(tool_name=call.tool_name))

        result = await agent.run(
            deps=deps,
            message_history=result.all_messages(),
            deferred_tool_results=DeferredToolResults(
                approvals=approvals,
            ),
            usage=usage,
            usage_limits=limits,
        )