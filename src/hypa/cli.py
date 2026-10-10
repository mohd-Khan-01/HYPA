from decode.entities.events import AssistantTextDelta,Event,ToolCallStarted,ToolResult
from decode.agent.demo import demo_turn

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

def run_cli() -> None:
    deps = AgentDeps(
    cwd=Path.cwd(),
    emit=render_event,
    gate=PermissionGate(mode=PermissionMode.DEFAULT),
    resolve_permission=ask_permission,
    resolve_user_question=question_unavailable,
)
    while True:
        task = input("What should HYPA do? ").strip()

        if not task:
            print("Please enter a task.")
            continue

        if task == "exit":
            print("Goodbye!")
            break
        
        asyncio.run(demo_turn(task, deps=deps))