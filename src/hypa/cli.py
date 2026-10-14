from decode.entities.events import AssistantTextDelta,Event,ToolCallStarted,ToolResult
import os

from pydantic_ai.models.groq import GroqModel, GroqModelSettings

from decode.agent.factory import build_agent
from decode.agent.loop import run_turn
from decode.config.settings import settings

from pathlib import Path

from decode.agent.deps import AgentDeps
from decode.permission.gate import PermissionGate
from decode.permission.types import PermissionMode
import asyncio




async def refuse_permission(description: str) -> bool:
    return False

async def ask_permission(description: str) -> bool:
    answer = input(description + "[y/N] ").strip().lower()
    return answer == "y"
async def question_unavailable(question: str) -> str:
    raise RuntimeError("Question handling is not connected yet.")
def render_event(event:Event)->None:
    if isinstance(event,AssistantTextDelta):
        print(event.text,end='',flush=True)
    elif isinstance(event,ToolCallStarted):
        print(f"\n using tool call name {event.tool_name}")
    elif isinstance(event,ToolResult):
        print(f"{event.tool_name}:{event.result}")

async def _run_cli() -> None:
    if not os.getenv("GROQ_API_KEY"):
        raise SystemExit("Set GROQ_API_KEY before starting HYPA.")

    model = GroqModel(
        settings.groq_model,
        settings=GroqModelSettings(
            max_tokens=1024,
            timeout=30,
            groq_reasoning_effort="low",
        ),
    )
    agent = build_agent(model)

    deps = AgentDeps(
        cwd=Path.cwd(),
        emit=render_event,
        gate=PermissionGate(PermissionMode.DEFAULT),
        resolve_permission=ask_permission,
        resolve_user_question=question_unavailable,
    )

    while True:
        task = input("\nWhat should HYPA do? ").strip()

        if not task:
            continue

        if task.lower() == "exit":
            print("Goodbye!")
            break

        print("Thinking...", flush=True)

        try:
            result = await run_turn(agent, task, deps)
        except Exception as error:
            print(f"\nTurn failed: {error}")
            continue

        print(f"\nHYPA: {result.output}")
        print(f"Model requests: {result.usage.requests}")


def run_cli() -> None:
    asyncio.run(_run_cli())