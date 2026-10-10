from pathlib import Path
from decode.tools.truncate import truncate
from decode.config.settings import settings
from decode.agent.deps import EventSink,AgentDeps
from decode.entities.events import (
    AssistantTextDelta,
    ToolCallStarted,
    ToolResult,
)

async def demo_turn(task: str, deps: AgentDeps) -> None:
    decision = deps.gate("read")

    if decision == "deny":
        deps.emit(AssistantTextDelta(text="Read denied.\n"))
        return

    if decision == "ask":
        approved = await deps.resolve_permission(
            f"Allow reading {task!r}? "
        )

        if not approved:
            deps.emit(AssistantTextDelta(text="Read declined.\n"))
            return

    # Resolve and read the file.
    base = deps.cwd.resolve()
    target = (base / task).resolve()

    try:
        target.relative_to(base)
    except ValueError:
        deps.emit(
            AssistantTextDelta(
                text="Path is outside the working directory.\n"
            )
        )
        return

    if not target.is_file():
        deps.emit(AssistantTextDelta(text=f"Not a file: {task}\n"))
        return

    deps.emit(ToolCallStarted(tool_name="read"))

    try:
        content = target.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        deps.emit(
            AssistantTextDelta(text=f"Could not read file: {error}\n")
        )
        return

    # Limit the output after reading succeeds.
    result = truncate(
        content,
        max_lines=settings.max_output_lines,
        max_bytes=settings.max_output_bytes,
    )

    text = result.text

    if result.truncated:
        text += (
            f"\n[Output truncated. "
            f"Full contents saved at: {result.full_path}]\n"
        )

    deps.emit(ToolResult(tool_name="read", result=text))