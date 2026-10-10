from pathlib import Path
from pydantic_ai import RunContext,ModelRetry
from decode.agent.deps import AgentDeps
import logging
from decode.config.settings import settings
from decode.tools.truncate import truncate
logger=logging.getLogger(__name__)
from decode.tools.approval import needs_approval

def _resolve_in_cwd(cwd:Path,path:str)->Path:
    target=(cwd/path).resolve()
    try:
        target.relative_to(cwd.resolve())
    except ValueError:
        raise ValueError(f"Path escapes working directory:{path!r}")
    return target
def _number_lines(
    content: str,
    *,
    start: int,
    limit: int | None,
) -> str | None:
    lines = content.splitlines()

    if start > len(lines):
        return None

    window = (
        lines[start - 1:]
        if limit is None
        else lines[start - 1:start - 1 + limit]
    )

    return "\n".join(
        f"{start + i}\t{line}"
        for i, line in enumerate(window)
    )
def _render_numbered(content:str,path:str,*,offset:int|None,limit:int|None)->str:
    start=1 if offset is None else max(offset,1)
    line_limit={
        None
        if limit is None
        else max(limit,0)
    }
    numbered=_number_lines(content,start,line_limit)
    if numbered is None:
        raise ModelRetry(
            f"{path!r} has no line {start}: "
            "offset is past the end of the file."
        )
    result=truncate(
        numbered,
        max_lines=settings.max_output_lines,
        max_bytes=settings.max_output_bytes
    )
    text = result.text.rstrip("\n")

    if result.truncated:
        text += (
            f"\n\n[output truncated to "
            f"{settings.max_output_lines} lines / "
            f"{settings.max_output_bytes} bytes; "
            f"full content at {result.full_path}]"
        )
    return numbered

def _reject_escaping_pattern(pattern: str) -> None:
    """stopping model from accessing other dir aside from the main project
    glob("../*.py")       # ❌
    glob("../../*.py")    # ❌
    glob("/home/user/*")  # ❌"""
    if pattern.startswith("/") or ".." in Path(pattern).parts:
        raise ModelRetry(
            f"Glob pattern {pattern!r} points outside the working directory."
        )
def _contain(base: Path, matches: list[Path]) -> list[Path]:
    return sorted(
        m for m in matches
        if m.is_file() and m.resolve().is_relative_to(base)
    )
def glob(ctx: RunContext[AgentDeps], pattern: str) -> str:
    if needs_approval(ctx):
        logger.debug("glob requires approval (pattern=%r)", pattern)
        raise needs_approval

    _reject_escaping_pattern(pattern)

    base = ctx.deps.cwd.resolve()
    matches = _contain(base, list(base.glob(pattern)))

    if not matches:
        raise ModelRetry(
            f"No files match {pattern!r} under the working directory."
        )

    return "\n".join(
        str(p.relative_to(base))
        for p in matches
    )
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
def edit(ctx:RunContext[AgentDeps],path:str,old_string:str,new_string:str)->str:
    decision = ctx.deps.gate("edit")

    if decision == "deny":
        raise PermissionError(
            "Edit operation denied"
        )

    if decision == "ask":
        approved =await ctx.deps.resolve_permission(f"Allow agent to edit {path!r}?" )

        if not approved:
            raise ModelRetry(
                "User denied the edit."
                )
    
    target=_resolve_in_cwd(ctx.deps.cwd,path)
    if not target.exists():
        raise FileNotFoundError(f"File not found: {path!r}")
    if not target.is_file():
        raise ValueError(f"Not a file: {path!r}")
    content=target.read_text(encoding="utf-8")
    if not old_string:
        raise ValueError(
            "old string cannot be empty"
        )
    count=content.count(old_string)
#finding exact match first
    if count == 1:
        updated = content.replace(
            old_string,
            new_string,
            1,)
    elif count > 1:
        raise ModelRetry(
            f"old_string is ambiguous: "
            f"found {count} matches"
        )
    else:
        # --------------------------------------------
        # 2. Exact match failed.
        # Try normalized whitespace matching.
        # ---------------------------------------------
        start, end = _find_normalized_match(
            content,
            old_string,
        )

        updated = (
            content[:start]
            + new_string
            + content[end:]
        )

    target.write_text(
        updated,
        encoding="utf-8",
    )

    return (
        f"Edited {path!r} "
        f"(replaced 1 occurrence)."
    )
        
    