import asyncio
from pathlib import Path

from pydantic_ai.exceptions import UsageLimitExceeded
from pydantic_ai.messages import ModelResponse, ToolCallPart
from pydantic_ai.models.function import FunctionModel

from decode.agent.deps import AgentDeps
from decode.agent.factory import build_agent
from decode.agent.loop import run_turn
from decode.permission.gate import PermissionGate


async def unavailable(question: str) -> bool:
    raise AssertionError("This check should not need human input.")


async def main() -> None:
    requests = 0

    async def keep_reading(messages, info) -> ModelResponse:
        nonlocal requests
        requests += 1
        print(f"Model request {requests}")

        return ModelResponse(
            parts=[
                ToolCallPart(
                    tool_name="read",
                    args={"path": "README.md", "limit": 1},
                    tool_call_id=f"read-{requests}",
                )
            ]
        )

    agent = build_agent(FunctionModel(keep_reading))
    deps = AgentDeps(
        cwd=Path.cwd(),
        emit=lambda event: None,
        gate=PermissionGate(),
        resolve_permission=unavailable,
        resolve_user_question=unavailable,
    )

    try:
        await run_turn(agent, "Keep reading README.md.", deps)
    except UsageLimitExceeded as error:
        assert requests == 5, requests
        assert "request_limit" in str(error), str(error)
        print(f"Correctly stopped: {error}")
        print("Request-limit check passed.")
    else:
        raise AssertionError("The request limit did not stop the run.")


if __name__ == "__main__":
    asyncio.run(main())