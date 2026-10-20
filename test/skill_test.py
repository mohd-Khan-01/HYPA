from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from pydantic_ai import ApprovalRequired, ModelRetry

from decode.permission.gate import PermissionGate
from decode.permission.types import PermissionMode, PermissionOutcome
from decode.tools.skills import MAX_SKILL_BYTES, load_skill, skill_catalog


with TemporaryDirectory() as directory:
    root = Path(directory)
    path = root / ".hypa" / "skills" / "review" / "SKILL.md"
    path.parent.mkdir(parents=True)
    body = "Inspect inputs and report evidence."
    path.write_text(body, encoding="utf-8")

    gate = PermissionGate(PermissionMode.PLAN)
    ctx = SimpleNamespace(
        deps=SimpleNamespace(cwd=root, gate=gate),
        tool_call_approved=True,
    )

    assert "review:" in skill_catalog()
    assert body not in skill_catalog()
    assert body in load_skill(ctx, "review")
    print("Metadata separate from loaded body: PASS")

    assert gate("edit") == PermissionOutcome.DENY
    print("Loading preserves plan-mode restrictions: PASS")

    unapproved = SimpleNamespace(
        deps=SimpleNamespace(gate=gate),
        tool_call_approved=False,
    )
    try:
        load_skill(unapproved, "review")
    except ApprovalRequired:
        print("Defers before filesystem access: PASS")
    else:
        raise AssertionError("Expected approval deferral.")

    for name in ("unknown", "../outside"):
        try:
            load_skill(ctx, name)
        except ModelRetry:
            pass
        else:
            raise AssertionError(f"Unexpected skill accepted: {name}")

    print("Unknown and traversal names rejected: PASS")

    for payload in (
        b"",
        b"\xff",
        b"x" * (MAX_SKILL_BYTES + 1),
    ):
        path.write_bytes(payload)
        try:
            load_skill(ctx, "review")
        except ModelRetry:
            pass
        else:
            raise AssertionError("Invalid skill body accepted.")

    print("Empty, invalid UTF-8, and oversized bodies rejected: PASS")

print("Skill checks passed.")