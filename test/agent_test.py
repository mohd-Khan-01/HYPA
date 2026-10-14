import os
from pathlib import Path

from pydantic_ai import DeferredToolRequests
from pydantic_ai.messages import ToolReturnPart
from pydantic_ai.models.groq import GroqModel, GroqModelSettings
from pydantic_ai.usage import UsageLimits

from decode.agent.deps import AgentDeps
from decode.agent.factory import build_agent
from decode.config.settings import settings
from decode.permission.gate import PermissionGate
from decode.permission.types import PermissionMode


async def unavailable(question: str):
    raise RuntimeError("Human interaction is not connected here.")


def main() -> None:
    if not os.getenv("GROQ_API_KEY"):
        raise SystemExit(
            "Set GROQ_API_KEY in this terminal before running."
        )

    model = GroqModel(settings.groq_model)
    agent = build_agent(model)

    deps = AgentDeps(
        cwd=Path.cwd(),
        emit=lambda event: None,
        gate=PermissionGate(PermissionMode.BYPASS),
        resolve_permission=unavailable,
        resolve_user_question=unavailable,
    )

    result = agent.run_sync(
        "Use the read tool to inspect README.md. "
        "Then state the project name and current status "
        "in one sentence, based on the file.",
        deps=deps,
        usage_limits=UsageLimits(
            request_limit=5,
            tool_calls_limit=4,
        ),
        model_settings=GroqModelSettings(
            max_tokens=1024,
            timeout=30,
            groq_reasoning_effort="low",
        ),
    )

    if isinstance(result.output, DeferredToolRequests):
        raise RuntimeError(
            "Unexpected deferred request in this read-only runner."
        )

    reads = [
        part
        for message in result.all_messages()
        for part in message.parts
        if isinstance(part, ToolReturnPart)
        and part.tool_name == "read"
        and part.outcome == "success"
    ]

    if not reads:
        raise AssertionError(
            "No successful read-tool result was recorded."
        )

    print("\n--- Actual read-tool evidence ---")
    for part in reads:
        print(part.content)

    print("\n--- Model answer ---")
    print(result.output)
    print("\nModel requests:", result.usage.requests)


if __name__ == "__main__":
    main()