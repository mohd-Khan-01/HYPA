from decode.entities.events import AssistantTextDelta,Event,ToolCallStarted,ToolResult
import os

from pydantic_ai.models.groq import GroqModel, GroqModelSettings

from decode.agent.factory import build_agent
from decode.agent.loop import run_turn
from decode.config.settings import settings

from pathlib import Path
from pydantic_ai.messages import ModelMessage
from decode.agent.deps import AgentDeps
from decode.permission.gate import PermissionGate
from decode.permission.types import PermissionMode
import asyncio
from pydantic import ValidationError
from decode.agent.project_memory import load_project_instructions
from decode.agent.session import load_session, save_session, session_path   
from decode.agent.compaction import build_summarizer, compact_history
from pydantic_ai.messages import ModelMessagesTypeAdapter

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
    summarizer = build_summarizer(model)
    gate = PermissionGate(PermissionMode.DEFAULT)
    project_text, notice = load_project_instructions(Path.cwd())

    if notice:
        print(notice)
    elif project_text:
        print("Loaded project instructions from .hypa/project.md.")
    deps = AgentDeps(
        cwd=Path.cwd(),
        emit=render_event,
        gate=gate,
        resolve_permission=ask_permission,
        resolve_user_question=question_unavailable,
        project_instructions=project_text
    )
    history: list[ModelMessage] = []
    while True:
        task = input("\nWhat should HYPA do? ").strip()

        if not task:
            continue

        if task.lower() == "exit":
            print("Goodbye!")
            break
        parts = task.split()
        if task.lower() == "/clear":
            history = []
            print("Conversation history cleared.")
            continue
        if parts[0].lower() == "/mode":
            if len(parts) == 1:
                print(f"Current mode: {gate.mode.value}")
            elif len(parts) != 2:
                print("Usage: /mode default|plan|edit|bypass")
            else:
                try:
                    selected_mode = PermissionMode(parts[1].lower())
                except ValueError:
                    print("Unknown mode. Use default, plan, edit, or bypass.")
                else:
                    gate.mode = selected_mode
                    print(f"Permission mode: {gate.mode.value}")

            continue
        if parts[0].lower() in ("/save", "/resume"):
            command = parts[0].lower()

            if len(parts) != 2:
                print(f"Usage: {command} NAME")
                continue

            try:
                path = session_path(deps.cwd, parts[1])

                if command == "/save":
                    save_session(path, history)
                    print(f"Saved {len(history)} messages to {path}")
                else:
                    restored = load_session(path)
                    history = restored
                    print(f"Resumed {len(history)} messages from {path}")

            except ValidationError:
                print("Could not resume: the session JSON is invalid.")
            except (OSError, ValueError) as error:
                print(f"Session command failed: {error}")

            continue
        if parts[0].lower() == "/compact":
            if len(parts) != 1:
                print("Usage: /compact")
                continue

            print("Compacting older conversation...", flush=True)

            try:
                candidate = await compact_history(history, summarizer)
                before = len(ModelMessagesTypeAdapter.dump_json(history))
                after = len(ModelMessagesTypeAdapter.dump_json(candidate))
            except Exception as error:
                print(f"Compaction failed; history unchanged: {error}")
            else:
                history = candidate
                print(
                    f"Compacted serialized history: {before} -> {after} bytes."
                )

            continue
        print("Thinking...", flush=True)

        try:
            result = await run_turn(
                agent,
                task,
                deps,
                message_history=history,
            )
        except Exception as error:
            print(f"\nTurn failed: {error}")
            continue

        history = result.all_messages()

        print(f"\nHYPA: {result.output}")
        print(f"Model requests: {result.usage.requests}")


def run_cli() -> None:
    asyncio.run(_run_cli())