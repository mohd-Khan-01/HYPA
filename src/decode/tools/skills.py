from dataclasses import dataclass
from pathlib import Path

from pydantic_ai import ApprovalRequired, ModelRetry, RunContext

from decode.agent.deps import AgentDeps
from decode.permission.types import PermissionOutcome
from decode.tools.approval import needs_approval


MAX_SKILL_BYTES = 4_000


@dataclass(frozen=True, slots=True)
class SkillInfo:
    name: str
    description: str


SKILLS = (
    SkillInfo(
        name="review",
        description="Review a requested file and report concrete findings.",
    ),
)


def skill_catalog() -> str:
    return "\n".join(
        f"- {skill.name}: {skill.description}"
        for skill in SKILLS
    )


def load_skill(ctx: RunContext[AgentDeps], name: str) -> str:
    """Load a workflow's instructions by name; this does not run its steps."""
    if ctx.deps.gate("load_skill") == PermissionOutcome.DENY:
        raise ModelRetry("Skill loading denied by the permission policy.")

    if needs_approval(ctx):
        raise ApprovalRequired

    if name not in {skill.name for skill in SKILLS}:
        raise ModelRetry(
            f"Unknown skill {name!r}. Available:\n{skill_catalog()}"
        )

    base = ctx.deps.cwd.resolve()
    path = (base / ".hypa" / "skills" / name / "SKILL.md").resolve()

    if not path.is_relative_to(base):
        raise ModelRetry("Skill path escapes the working directory.")

    try:
        with path.open("rb") as stream:
            payload = stream.read(MAX_SKILL_BYTES + 1)
    except OSError as error:
        raise ModelRetry(
            f"Could not load skill {name!r}: {error}"
        ) from error

    if len(payload) > MAX_SKILL_BYTES:
        raise ModelRetry(
            f"Skill {name!r} exceeds {MAX_SKILL_BYTES} bytes."
        )

    try:
        body = payload.decode("utf-8").strip()
    except UnicodeDecodeError as error:
        raise ModelRetry(
            f"Skill {name!r} must be valid UTF-8."
        ) from error

    if not body:
        raise ModelRetry(f"Skill {name!r} is empty.")

    return (
        f"Loaded skill: {name}\n\n{body}\n\n"
        "Follow this workflow using the available tools. "
        "Normal permission checks still apply."
    )