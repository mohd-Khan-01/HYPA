from pathlib import Path

from pydantic_ai.models.test import TestModel
from pydantic_ai.usage import UsageLimits

from decode.agent.deps import AgentDeps
from decode.agent.factory import build_agent
from decode.permission.gate import PermissionGate


async def unavailable(question: str):
    raise RuntimeError(
        "This smoke check should not request human input."
    )


deps = AgentDeps(
    cwd=Path.cwd(),
    emit=lambda event: None,
    gate=PermissionGate(),
    resolve_permission=unavailable,
    resolve_user_question=unavailable,
)

model = TestModel(
    call_tools=[],
    custom_output_text="HYPA wiring works.",
)

agent = build_agent(model)

result = agent.run_sync(
    "Check the agent wiring.",
    deps=deps,
    usage_limits=UsageLimits(
        request_limit=3,
        tool_calls_limit=3,
    ),
)

assert result.output == "HYPA wiring works."
print(result.output)
print("Factory smoke check passed.")