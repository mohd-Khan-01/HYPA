import ctypes
import sys
import time
from ctypes import wintypes
from pathlib import Path
from types import SimpleNamespace

from decode.config.settings import settings
from decode.permission.gate import PermissionGate
from decode.tools.commands import execute, run_command

cwd = Path.cwd()
per_stream = max(1, settings.max_output_bytes // 2)

result = run_command(
    [
        sys.executable, "-B", "-c",
        "import sys; "
        "sys.stdout.buffer.write(b'x' * 100_000); "
        "sys.stderr.buffer.write(b'y' * 100_000)",
    ],
    cwd=cwd,
)
assert result.returncode == 0
assert result.stdout == "x" * per_stream
assert result.stderr == "y" * per_stream
assert result.stdout_truncated and result.stderr_truncated
print("Large stdout/stderr bounded without blocking: PASS")

ctx = SimpleNamespace(
    deps=SimpleNamespace(gate=PermissionGate(), cwd=cwd),
    tool_call_approved=True,
)
output = execute(
    ctx,
    [
        sys.executable, "-B", "-c",
        "import sys; sys.stdout.write(chr(233) * 100_000)",
    ],
)
assert "STDOUT truncated: True" in output
# The configured payload budget plus a small fixed status/header overhead.
assert len(output.encode("utf-8")) <= settings.max_output_bytes + 512
print("Long Unicode line has bounded model-visible output: PASS")

result = run_command(
    [
        sys.executable, "-B", "-c",
        "import time; print('before timeout', flush=True); time.sleep(10)",
    ],
    cwd=cwd,
    timeout=2,
)
assert result.timed_out
assert result.returncode is None
assert "before timeout" in result.stdout
print("Timeout preserves captured partial output: PASS")

result = run_command(
    ["__hypa_nonexistent_executable_9fa2__.exe"],
    cwd=cwd,
)
assert result.returncode == 127
assert "Could not launch requested executable" in result.stderr
print("Missing executable produces failure evidence: PASS")

kernel = ctypes.WinDLL("kernel32", use_last_error=True)
kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel.OpenProcess.restype = wintypes.HANDLE
kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
kernel.GetExitCodeProcess.restype = wintypes.BOOL
kernel.CloseHandle.argtypes = [wintypes.HANDLE]
kernel.CloseHandle.restype = wintypes.BOOL


def is_running(pid: int) -> bool:
    handle = kernel.OpenProcess(0x1000, False, pid)
    if not handle:
        error = ctypes.get_last_error()
        if error in (87, 1168):  # PID no longer exists.
            return False
        raise ctypes.WinError(error)
    try:
        code = wintypes.DWORD()
        if not kernel.GetExitCodeProcess(handle, ctypes.byref(code)):
            raise ctypes.WinError(ctypes.get_last_error())
        return code.value == 259  # STILL_ACTIVE
    finally:
        kernel.CloseHandle(handle)


def assert_child_stopped(output: str) -> None:
    pid_line = next(
        line for line in output.splitlines()
        if line.startswith("CHILD_PID=")
    )
    pid = int(pid_line.partition("=")[2])
    deadline = time.monotonic() + 3
    while is_running(pid) and time.monotonic() < deadline:
        time.sleep(0.02)
    assert not is_running(pid), f"Child {pid} is still running."


spawn_child = (
    "import subprocess, sys, time; "
    "child = subprocess.Popen([sys.executable, '-B', '-c', "
    "'import time; time.sleep(60)']); "
    "print('CHILD_PID=' + str(child.pid), flush=True); "
)

result = run_command(
    [sys.executable, "-B", "-c", spawn_child + "time.sleep(60)"],
    cwd=cwd,
    timeout=2,
)
assert result.timed_out
assert_child_stopped(result.stdout)
print("Timeout removes descendant process: PASS")

result = run_command(
    [sys.executable, "-B", "-c", spawn_child],
    cwd=cwd,
)
assert result.returncode == 0
assert_child_stopped(result.stdout)
print("Normal exit removes background descendant: PASS")

print("Integrated command-limit checks passed.")