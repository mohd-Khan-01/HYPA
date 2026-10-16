import subprocess
import sys
from pathlib import Path

from decode.tools.commands import run_command


cwd = Path.cwd()

result = run_command(
    [sys.executable, "-B", "-c", "print('runner works')"],
    cwd=cwd,
)
assert result.returncode == 0
assert result.stdout.strip() == "runner works"
assert result.stderr == ""
print("Successful command: PASS")

result = run_command(
    [
        sys.executable,
        "-B",
        "-c",
        "import sys; print('check failed', file=sys.stderr); sys.exit(3)",
    ],
    cwd=cwd,
)
assert result.returncode == 3
assert result.stderr.strip() == "check failed"
print("Nonzero exit and stderr: PASS")

result = run_command(
    [sys.executable, "-B", "-c", "import time; time.sleep(2)"],
    cwd=cwd,
    timeout=0.2,
)
assert result.timed_out
assert result.returncode is None
print("Timeout: PASS")


from types import SimpleNamespace
from unittest.mock import patch

from pydantic_ai import ApprovalRequired, ModelRetry

from decode.permission.gate import PermissionGate
from decode.permission.types import PermissionMode
from decode.tools.commands import execute


cases = [
    (PermissionMode.DEFAULT, False, ApprovalRequired),
    (PermissionMode.EDIT, False, ApprovalRequired),
    (PermissionMode.PLAN, False, ModelRetry),
    (PermissionMode.PLAN, True, ModelRetry),
]

for mode, approved, expected_error in cases:
    ctx = SimpleNamespace(
        deps=SimpleNamespace(gate=PermissionGate(mode)),
        tool_call_approved=approved,
    )

    with patch("decode.tools.commands.run_command") as launch:
        try:
            execute(ctx, [sys.executable, "--version"])
        except expected_error:
            pass
        else:
            raise AssertionError(f"{mode}: expected {expected_error.__name__}")

        launch.assert_not_called()

    print(f"{mode.value}, approved={approved}: blocked before launch")
    
approved_ctx = SimpleNamespace(
    deps=SimpleNamespace(
        gate=PermissionGate(),
        cwd=Path.cwd(),
    ),
    tool_call_approved=True,
)

output = execute(
    approved_ctx,
    [
        sys.executable,
        "-B",
        "-c",
        "import sys; print('intentional failure', file=sys.stderr); sys.exit(3)",
    ],
)

assert "Status: completed" in output
assert "Exit code: 3" in output
assert "intentional failure" in output
print("Approved execution preserves failure evidence: PASS")