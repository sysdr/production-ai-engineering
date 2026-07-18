"""Subprocess-isolated code runner with import allowlist and timeouts."""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import textwrap
import time
from dataclasses import dataclass
from typing import Final

# Documented safe modules for demos / operators (stdlib may pull helpers).
ALLOWED_MODULES: Final[frozenset[str]] = frozenset(
    {"math", "json", "re", "collections", "itertools", "datetime"}
)

# Dangerous roots blocked at import time (deny-list keeps allowlisted demos working
# when CPython pulls transitive stdlib helpers such as keyword/operator).
BLOCKED_MODULES: Final[frozenset[str]] = frozenset(
    {
        "os",
        "posix",
        "nt",
        "subprocess",
        "socket",
        "ssl",
        "select",
        "shutil",
        "pathlib",
        "ctypes",
        "multiprocessing",
        "threading",
        "pickle",
        "marshal",
        "importlib",
        "pty",
        "fcntl",
        "resource",
        "signal",
        "code",
        "codeop",
        "http",
        "urllib",
        "asyncio",
        "concurrent",
        "webbrowser",
        "cgi",
        "ftplib",
        "smtplib",
        "mmap",
        "sysconfig",
        "platform",
    }
)

# Injected before user code: deny dangerous modules, allow safe computation libs.
_WRAPPER_HEAD = textwrap.dedent(
    """\
    import builtins
    _blocked = {
        'os', 'posix', 'nt', 'subprocess', 'socket', 'ssl', 'select', 'shutil',
        'pathlib', 'ctypes', 'multiprocessing', 'threading', 'pickle', 'marshal',
        'importlib', 'pty', 'fcntl', 'resource', 'signal', 'code', 'codeop',
        'http', 'urllib', 'asyncio', 'concurrent', 'webbrowser', 'cgi', 'ftplib',
        'smtplib', 'mmap', 'sysconfig', 'platform',
    }
    _real = builtins.__import__
    def _safe(name, globals=None, locals=None, fromlist=(), level=0):
        if level > 0:
            return _real(name, globals, locals, fromlist, level)
        root = name.split('.')[0] if name else ''
        if root in _blocked:
            raise ImportError('Blocked: ' + name)
        return _real(name, globals, locals, fromlist, level)
    builtins.__import__ = _safe
    """
)


@dataclass(frozen=True, slots=True)
class SandboxResult:
    """Outcome of one sandboxed execution."""

    ok: bool
    output: str
    timeout: bool
    blocked: bool
    error: bool
    duration_ms: float
    label: str = ""


class SandboxExecutor:
    """Run untrusted Python in a child process with isolation guards."""

    def __init__(self, default_timeout: float = 2.0) -> None:
        self.default_timeout = default_timeout

    def run(
        self,
        code: str,
        *,
        timeout: float | None = None,
        label: str = "",
    ) -> SandboxResult:
        limit = self.default_timeout if timeout is None else timeout
        src = _WRAPPER_HEAD + textwrap.dedent(code)
        fname: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".py",
                delete=False,
                encoding="utf-8",
            ) as handle:
                handle.write(src)
                fname = handle.name

            started = time.monotonic()
            try:
                completed = subprocess.run(
                    [sys.executable, fname],
                    capture_output=True,
                    text=True,
                    timeout=limit,
                    env={
                        "PATH": os.environ.get("PATH", ""),
                        "PYTHONPATH": "",
                        "PYTHONDONTWRITEBYTECODE": "1",
                    },
                )
            except subprocess.TimeoutExpired:
                elapsed = (time.monotonic() - started) * 1000.0
                return SandboxResult(
                    ok=False,
                    output="TIMED OUT",
                    timeout=True,
                    blocked=False,
                    error=False,
                    duration_ms=round(elapsed, 2),
                    label=label,
                )

            elapsed = (time.monotonic() - started) * 1000.0
            combined = ((completed.stdout or "") + (completed.stderr or "")).strip()
            blocked = "Blocked:" in combined or "ImportError" in combined
            errored = completed.returncode != 0 and not blocked
            ok = completed.returncode == 0
            out = combined[:200] if combined else ("OK" if ok else "FAILED")
            return SandboxResult(
                ok=ok,
                output=out,
                timeout=False,
                blocked=blocked,
                error=errored,
                duration_ms=round(elapsed, 2),
                label=label,
            )
        finally:
            if fname is not None:
                try:
                    os.unlink(fname)
                except OSError:
                    pass
