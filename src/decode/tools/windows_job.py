"""Windows process grouping; this is cleanup, not a sandbox."""
import ctypes
import os
from ctypes import wintypes

if os.name != "nt":
    raise RuntimeError("This HYPA execution backend requires Windows.")

_kernel = ctypes.WinDLL("kernel32", use_last_error=True)
_kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
_kernel.CreateJobObjectW.restype = wintypes.HANDLE
_kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
_kernel.OpenProcess.restype = wintypes.HANDLE
_kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
_kernel.AssignProcessToJobObject.restype = wintypes.BOOL
_kernel.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
_kernel.TerminateJobObject.restype = wintypes.BOOL
_kernel.CloseHandle.argtypes = [wintypes.HANDLE]
_kernel.CloseHandle.restype = wintypes.BOOL


class WindowsJob:
    def __init__(self) -> None:
        self._handle = _kernel.CreateJobObjectW(None, None)
        if not self._handle:
            raise ctypes.WinError(ctypes.get_last_error())

    def assign(self, pid: int) -> None:
        # AssignProcessToJobObject requires SET_QUOTA and TERMINATE rights.
        process = _kernel.OpenProcess(0x0100 | 0x0001, False, pid)
        if not process:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            if not _kernel.AssignProcessToJobObject(self._handle, process):
                raise ctypes.WinError(ctypes.get_last_error())
        finally:
            _kernel.CloseHandle(process)

    def terminate(self) -> None:
        if self._handle and not _kernel.TerminateJobObject(self._handle, 1):
            raise ctypes.WinError(ctypes.get_last_error())

    def close(self) -> None:
        if self._handle:
            if not _kernel.CloseHandle(self._handle):
                raise ctypes.WinError(ctypes.get_last_error())
            self._handle = None