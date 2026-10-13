from pathlib import Path
from pydantic_ai import ApprovalRequired, ModelRetry, RunContext
from decode.agent.deps import AgentDeps
import logging
from decode.config.settings import settings
from decode.tools.truncate import truncate
logger=logging.getLogger(__name__)
from decode.tools.approval import needs_approval

def _resolve_in_cwd(cwd: Path, path: str) -> Path:
    base = cwd.resolve()
    target = (base / path).resolve()

    try:
        target.relative_to(base)
    except ValueError as error:
        raise ModelRetry(
            f"Path {path!r} escapes the working directory."
        ) from error

    return target
def _number_lines(
    content: str,
    *,
    start: int,
    limit: int | None,
) -> str | None:
    lines = content.splitlines()

    if not lines and start == 1:
        return ""

    if start > len(lines):
        return None

    window = (
        lines[start - 1:]
        if limit is None
        else lines[start - 1:start - 1 + limit]
    )

    return "\n".join(
        f"{start + index}\t{line}"
        for index, line in enumerate(window)
    )
    
def _cap_output(content: str) -> str:
    result = truncate(
        content,
        max_lines=settings.max_output_lines,
        max_bytes=settings.max_output_bytes,
    )

    text = result.text.rstrip("\n")

    if result.truncated:
        text += (
            f"\n\n[Output truncated; "
            f"full content at {result.full_path}]"
        )

    return text
def _render_numbered(
    content: str,
    path: str,
    *,
    offset: int | None,
    limit: int | None,
) -> str:
    start = 1 if offset is None else max(offset, 1)
    line_limit = None if limit is None else max(limit, 0)

    numbered = _number_lines(
        content,
        start=start,
        limit=line_limit,
    )

    if numbered is None:
        raise ModelRetry(
            f"{path!r} has no line {start}: "
            "offset is past the end of the file."
        )

    return _cap_output(numbered)

def _reject_escaping_pattern(pattern: str) -> None:
    parsed = Path(pattern)

    if parsed.anchor or ".." in parsed.parts:
        raise ModelRetry(
            f"Glob pattern {pattern!r} must stay "
            "relative to the working directory."
        )
def _contain(base: Path, matches: list[Path]) -> list[Path]:
    return sorted(
        m for m in matches
        if m.is_file() and m.resolve().is_relative_to(base)
    )
def glob(ctx: RunContext[AgentDeps], pattern: str) -> str:
    if needs_approval(ctx):
        logger.debug("glob requires approval (pattern=%r)", pattern)
        raise ApprovalRequired

    _reject_escaping_pattern(pattern)

    base = ctx.deps.cwd.resolve()
    matches = _contain(base, list(base.glob(pattern)))

    if not matches:
        raise ModelRetry(
            f"No files match {pattern!r} under the working directory."
        )

    output = "\n".join(
    str(path.relative_to(base))
    for path in matches)
    return _cap_output(output)
def read(ctx:RunContext[AgentDeps],path:str,offset:int|None=None,limit:int|None=None)->str:
    if needs_approval(ctx):
        logger.debug("read require approval(path=%r)",path)
        raise ApprovalRequired
    target=_resolve_in_cwd(ctx.deps.cwd,path)
    if not target.exists():
        raise ModelRetry(f"file not found {path!r}")
    if target.is_dir():
        raise ModelRetry(f"the path is a directory not a file:{path!r} use global to list its content")
    try:
        content=target.read_text(
            encoding="utf8"
        )
    except(OSError,UnicodeDecodeError) as e:
        raise ModelRetry(f"not able to read {path!r}:{e}")from e
    return _render_numbered(
    content,
    path,
    offset=offset,
    limit=limit,
)

       
def _find_normalized_match(
    content: str,
    old_string: str,
) -> tuple[int, int]:
    normalized_content, positions = _normalized_with_positions(content)
    normalized_old, _ = _normalized_with_positions(old_string)

    if not normalized_old:
        raise ValueError("old_string cannot be empty")

    first = normalized_content.find(normalized_old)

    if first == -1:
        raise ValueError("old_string not found")

    second = normalized_content.find(
        normalized_old,
        first + 1,
    )

    if second != -1:
        raise ValueError(
            "old_string is ambiguous: multiple matches found"
        )

    start = positions[first]
    end = positions[first + len(normalized_old) - 1] + 1

    return start, end
def _normalized_with_positions(
    text: str,
) -> tuple[str, list[int]]:
    normalized = []
    positions = []

    previous_was_space = False

    for index, char in enumerate(text):
        if char.isspace():
            if not previous_was_space:
                normalized.append(" ")
                positions.append(index)

            previous_was_space = True
            continue

        normalized.append(char)
        positions.append(index)
        previous_was_space = False

    return "".join(normalized).strip(), positions

def _check_mutation(
    ctx: RunContext[AgentDeps],
    tool_name: str,
) -> None:
    if ctx.deps.gate(tool_name) == "deny":
        raise ModelRetry(
            f"{tool_name} denied by the permission policy."
        )

    if needs_approval(ctx):
        raise ApprovalRequired
def write(
    ctx: RunContext[AgentDeps],
    path: str,
    content: str,
) -> str:
    """Create or replace an entire UTF-8 text file."""
    _check_mutation(ctx, "write")
    target = _resolve_in_cwd(ctx.deps.cwd, path)

    if target.exists() and not target.is_file():
        raise ModelRetry(f"{path!r} is not a file.")

    if not target.parent.is_dir():
        raise ModelRetry(
            f"Parent directory does not exist for {path!r}."
        )

    try:
        target.write_text(content, encoding="utf-8")
    except OSError as error:
        raise ModelRetry(
            f"Could not write {path!r}: {error}"
        ) from error

    return f"Wrote {path!r}."

def edit(
    ctx: RunContext[AgentDeps],
    path: str,
    old_string: str,
    new_string: str,
) -> str:
    """Replace exactly one occurrence in a UTF-8 text file."""
    _check_mutation(ctx, "edit")
    target = _resolve_in_cwd(ctx.deps.cwd, path)

    if not target.is_file():
        raise ModelRetry(
            f"Cannot edit {path!r}: file missing or not a file."
        )

    if not old_string:
        raise ModelRetry("old_string cannot be empty.")

    try:
        content = target.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise ModelRetry(
            f"Could not read {path!r}: {error}"
        ) from error

    first = content.find(old_string)

    if first == -1:
        raise ModelRetry(
            "old_string was not found. Read the file again."
        )

    second = content.find(old_string, first + 1)

    if second != -1:
        raise ModelRetry(
            "old_string has multiple matches. "
            "Provide a larger unique section."
        )

    updated = content.replace(old_string, new_string, 1)

    try:
        target.write_text(updated, encoding="utf-8")
    except OSError as error:
        raise ModelRetry(
            f"Could not save {path!r}: {error}"
        ) from error

    return f"Edited {path!r}: replaced one occurrence."
        
def grep(
    ctx: RunContext[AgentDeps],
    pattern: str,
    include: str = "**/*.py",
) -> str:
    if needs_approval(ctx):
        raise ApprovalRequired

    if not pattern or "\n" in pattern or "\r" in pattern:
        raise ModelRetry(
            "Search text must be non-empty and single-line."
        )

    _reject_escaping_pattern(include)
    base = ctx.deps.cwd.resolve()

    excluded = {".git", ".venv", "node_modules", "__pycache__"}
    candidates = [
        path
        for path in base.glob(include)
        if not excluded.intersection(path.relative_to(base).parts)
    ]

    matches: list[str] = []
    skipped = 0

    for target in _contain(base, candidates):
        try:
            content = target.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            skipped += 1
            continue

        relative = target.relative_to(base).as_posix()

        for number, line in enumerate(content.splitlines(), start=1):
            if pattern in line:
                matches.append(f"{relative}:{number}:{line}")

    if not matches:
        raise ModelRetry(
            f"No matches for {pattern!r} in readable files "
            f"matching {include!r}. Skipped {skipped} unreadable files."
        )

    if skipped:
        matches.append(f"[Skipped {skipped} unreadable files.]")

    return _cap_output("\n".join(matches))