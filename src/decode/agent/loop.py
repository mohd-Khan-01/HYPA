from pydantic_ai import Agent, DeferredToolRequests
from pydantic_ai.messages import ModelMessage, ToolReturnPart
from pydantic_ai.run import AgentRunResult
from pydantic_ai.tools import DeferredToolResults
from pydantic_ai.usage import RunUsage, UsageLimits

from decode.agent.deps import AgentDeps
from decode.entities.events import ToolCallStarted, ToolResult
import json

from decode.permission.types import PermissionOutcome

async def run_turn(
    agent: Agent[AgentDeps, str | DeferredToolRequests],
    prompt: str,
    deps: AgentDeps,
    message_history:list[ModelMessage] |None=None
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
        message_history=message_history
    )

    while True:
        #Display results produced by this run leg, excluding supplied history.
        for message in result.new_messages():
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

            if decision == PermissionOutcome.ASK:
                arguments = json.dumps(
                    call.args_as_dict(),
                    indent=2,
                    ensure_ascii=False,
                )
                description = (
                    f"Allow tool {call.tool_name!r} "
                    f"(call {call.tool_call_id})?\n"
                    f"Arguments:\n{arguments}\n"
                )
                approved = await deps.resolve_permission(description)
            else:
                approved = decision == PermissionOutcome.ALLOW

            approvals[call.tool_call_id] = approved

            if approved:
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