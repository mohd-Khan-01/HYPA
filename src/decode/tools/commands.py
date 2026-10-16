import json
import os
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from queue import SimpleQueue
from typing import BinaryIO

from pydantic_ai import ApprovalRequired, ModelRetry, RunContext

from decode.agent.deps import AgentDeps
from decode.config.settings import settings
from decode.permission.types import PermissionOutcome
from decode.tools.approval import needs_approval
from decode.tools.process_output import OutputCapture
from decode.tools.windows_job import WindowsJob


# The launcher cannot start the requested command until our parent releases it.
# Its stdout/stderr are inherited by the requested command.
_STARTER = """
import json
import subprocess
import sys

if sys.stdin.buffer.readline() != b"start\\n":
    sys.exit(126)

try:
    code = subprocess.call(
        json.loads(sys.argv[1]),
        stdin=subprocess.DEVNULL,
        shell=False,
    )
except OSError as error:
    print(f"Could not launch requested executable: {error}", file=sys.stderr)
    sys.exit(127)

sys.exit(code)
"""


@dataclass(frozen=True, slots=True)
class CommandResult:
    returncode: int | None
    stdout: str
    stderr: str
    timed_out: bool
    stdout_truncated: bool
    stderr_truncated: bool


def _drain(
    stream: BinaryIO,
    capture: OutputCapture,
    errors: SimpleQueue,
) -> None:
    try:
        while chunk := stream.read(4096):
            capture.append(chunk)
    except Exception as error:
        errors.put(error)
    finally:
        stream.close()


def _cleanup(
    job: WindowsJob,
    process: subprocess.Popen | None,
    readers: list[threading.Thread],
) -> None:
    try:
        # Also removes background descendants after a normal command exit.
        job.terminate()
    finally:
        try:
            if process is not None:
                if process.poll() is None:
                    process.kill()
                process.wait(timeout=5)
                if process.stdin is not None and not process.stdin.closed:
                    process.stdin.close()

            deadline = time.monotonic() + 5
            for reader in readers:
                reader.join(timeout=max(0.0, deadline - time.monotonic()))

            if any(reader.is_alive() for reader in readers):
                raise RuntimeError("Output-reader cleanup did not finish.")
        finally:
            job.close()


def run_command(
    argv: list[str],
    *,
    cwd: Path,
    timeout: float = 10.0,
) -> CommandResult:
    if (
        not isinstance(argv, list)
        or not argv
        or not all(isinstance(arg, str) for arg in argv)
        or not argv[0]
    ):
        raise ValueError("argv must be a non-empty list of string arguments.")

    if not 0 < timeout <= 30:
        raise ValueError("timeout must be greater than 0 and at most 30.")

    per_stream = max(1, settings.max_output_bytes // 2)
    stdout = OutputCapture(per_stream)
    stderr = OutputCapture(per_stream)
    errors = SimpleQueue()
    readers: list[threading.Thread] = []
    process = None
    timed_out = False
    returncode = None

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    job = WindowsJob()
    deadline = time.monotonic() + timeout

    try:
        process = subprocess.Popen(
            [sys.executable, "-B", "-u", "-c", _STARTER, json.dumps(argv)],
            cwd=cwd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
            shell=False,
            env=env,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

        # The launcher is waiting for input, so it cannot spawn the target yet.
        job.assign(process.pid)

        assert process.stdout is not None
        assert process.stderr is not None
        for stream, capture in (
            (process.stdout, stdout),
            (process.stderr, stderr),
        ):
            reader = threading.Thread(
                target=_drain,
                args=(stream, capture, errors),
                daemon=True,
            )
            reader.start()
            readers.append(reader)

        assert process.stdin is not None
        process.stdin.write(b"start\n")
        process.stdin.close()

        try:
            returncode = process.wait(
                timeout=max(0.001, deadline - time.monotonic())
            )
        except subprocess.TimeoutExpired:
            timed_out = True
    finally:
        _cleanup(job, process, readers)

    if not errors.empty():
        raise RuntimeError(f"Output capture failed: {errors.get()}")

    return CommandResult(
        returncode=returncode,
        stdout=stdout.text(),
        stderr=stderr.text(),
        timed_out=timed_out,
        stdout_truncated=stdout.truncated,
        stderr_truncated=stderr.truncated,
    )


def _display_stream(text: str, truncated: bool) -> tuple[str, bool]:
    # Limit lines first, then UTF-8 bytes. There is no oversized-line exception.
    line_limit = max(1, settings.max_output_lines // 2)
    lines = text.splitlines(keepends=True)
    if len(lines) > line_limit:
        truncated = True
    text = "".join(lines[:line_limit])

    encoded = text.encode("utf-8")
    byte_limit = max(1, settings.max_output_bytes // 2)
    if len(encoded) > byte_limit:
        truncated = True
    text = encoded[:byte_limit].decode("utf-8", errors="ignore")
    return text, truncated


def execute(
    ctx: RunContext[AgentDeps],
    argv: list[str],
    timeout: float = 10.0,
) -> str:
    """Run a program using an argv list, without a shell.

    Runs locally in the project directory, without filesystem isolation.
    Use python -B for Python checks. Background descendants are terminated
    when this call ends. Inspect exit code and output before claiming success.
    """
    if ctx.deps.gate("execute") == PermissionOutcome.DENY:
        raise ModelRetry("Command execution denied by the permission policy.")

    if needs_approval(ctx):
        raise ApprovalRequired

    try:
        result = run_command(argv, cwd=ctx.deps.cwd, timeout=timeout)
    except (OSError, ValueError, RuntimeError) as error:
        raise ModelRetry(
            "Command execution/capture could not finish reliably. "
            f"The command may already have run: {error}"
        ) from error

    stdout, out_cut = _display_stream(
        result.stdout, result.stdout_truncated
    )
    stderr, err_cut = _display_stream(
        result.stderr, result.stderr_truncated
    )
    status = "timed_out" if result.timed_out else "completed"
    code = "unavailable" if result.returncode is None else str(result.returncode)
    timeout_note = f"Timeout: {timeout} seconds\n" if result.timed_out else ""

    return (
        f"Status: {status}\n"
        f"Exit code: {code}\n"
        f"{timeout_note}"
        f"STDOUT truncated: {out_cut}\n"
        f"STDERR truncated: {err_cut}\n\n"
        f"STDOUT:\n{stdout}\n\n"
        f"STDERR:\n{stderr}"
    )