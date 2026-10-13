from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from pydantic_ai import ApprovalRequired, ModelRetry

from decode.permission.gate import PermissionGate
from decode.permission.types import PermissionMode
from decode.tools.files import edit, read, write


def expect_unchanged(label, exception_type, operation, target):
    before = target.read_bytes() if target.exists() else None

    try:
        operation()
    except exception_type:
        pass
    else:
        raise AssertionError(f"{label}: expected rejection")

    after = target.read_bytes() if target.exists() else None
    assert after == before, f"{label}: file changed unexpectedly"
    print(f"{label}: PASS")


with TemporaryDirectory(
    dir=Path.cwd(),
    prefix="hypa-tools-check-",
) as directory:
    root = Path(directory)
    workspace = root / "workspace"
    workspace.mkdir()

    # Outside the tool workspace, but still inside our temporary fixture.
    outside = root / "outside.txt"
    outside.write_text("protected", encoding="utf-8")

    ctx = SimpleNamespace(
        deps=SimpleNamespace(
            cwd=workspace,
            gate=PermissionGate(PermissionMode.EDIT),
        ),
        tool_call_approved=True,
    )

    target = workspace / "example.py"

    # Create, overwrite, and edit.
    write(ctx, "example.py", "placeholder\n")
    assert target.read_text(encoding="utf-8") == "placeholder\n"

    write(ctx, "example.py", "answer = 41\n")
    assert target.read_text(encoding="utf-8") == "answer = 41\n"

    edit(ctx, "example.py", "41", "42")
    assert target.read_text(encoding="utf-8") == "answer = 42\n"
    assert read(ctx, "example.py") == "1\tanswer = 42"
    print("Create, overwrite, exact edit, and read-back: PASS")

    expect_unchanged(
        "Empty old_string",
        ModelRetry,
        lambda: edit(ctx, "example.py", "", "replacement"),
        target,
    )

    expect_unchanged(
        "Absent old_string",
        ModelRetry,
        lambda: edit(ctx, "example.py", "missing", "replacement"),
        target,
    )

    repeated = workspace / "repeated.txt"
    write(ctx, "repeated.txt", "same same")
    expect_unchanged(
        "Ambiguous match",
        ModelRetry,
        lambda: edit(ctx, "repeated.txt", "same", "changed"),
        repeated,
    )

    write(ctx, "repeated.txt", "aaa")
    expect_unchanged(
        "Overlapping matches",
        ModelRetry,
        lambda: edit(ctx, "repeated.txt", "aa", "changed"),
        repeated,
    )

    expect_unchanged(
        "Outside write",
        ModelRetry,
        lambda: write(ctx, "../outside.txt", "changed"),
        outside,
    )

    expect_unchanged(
        "Outside edit",
        ModelRetry,
        lambda: edit(ctx, "../outside.txt", "protected", "changed"),
        outside,
    )

    # Plan mode denies mutation even with an approved context.
    ctx.deps.gate.mode = PermissionMode.PLAN

    expect_unchanged(
        "Plan-mode write",
        ModelRetry,
        lambda: write(ctx, "example.py", "changed"),
        target,
    )

    expect_unchanged(
        "Plan-mode edit",
        ModelRetry,
        lambda: edit(ctx, "example.py", "42", "99"),
        target,
    )

    # Default mode pauses an unapproved mutation.
    ctx.deps.gate.mode = PermissionMode.DEFAULT
    ctx.tool_call_approved = False

    expect_unchanged(
        "Unapproved write",
        ApprovalRequired,
        lambda: write(ctx, "example.py", "changed"),
        target,
    )

    expect_unchanged(
        "Unapproved edit",
        ApprovalRequired,
        lambda: edit(ctx, "example.py", "42", "99"),
        target,
    )

    new_target = workspace / "never-created.txt"
    expect_unchanged(
        "Unapproved creation",
        ApprovalRequired,
        lambda: write(ctx, "never-created.txt", "changed"),
        new_target,
    )

print("All mutation checks passed; temporary fixtures removed.")