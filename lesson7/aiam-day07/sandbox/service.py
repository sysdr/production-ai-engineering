"""Coordinates sandboxed executions and dashboard metrics."""
from __future__ import annotations

from typing import Any

from sandbox.executor import SandboxExecutor
from sandbox.metrics import METRICS

# Demo cases intentionally cover OK / allowed / blocked / timeout / syntax error.
DEMO_CASES: list[tuple[str, str, float, bool, bool]] = [
    # (label, code, timeout, allowed_hit, blocked_hit)
    ("Safe arithmetic", "print(sum(range(1, 101)))", 2.0, False, False),
    ("Math import OK", "import math\nprint(round(math.pi, 4))", 2.0, True, False),
    (
        "Collections OK",
        "from collections import Counter\nprint(Counter('hello').most_common(2))",
        2.0,
        True,
        False,
    ),
    ("JSON import OK", "import json\nprint(json.dumps({'ok': True}))", 2.0, True, False),
    ("OS blocked", "import os\nprint(os.listdir('/'))", 2.0, False, True),
    (
        "Subprocess blocked",
        "import subprocess\nsubprocess.run(['id'])",
        2.0,
        False,
        True,
    ),
    ("Socket blocked", "import socket\nsocket.gethostname()", 2.0, False, True),
    ("Infinite loop", "while True: pass", 0.4, False, False),
    ("Syntax error", "def broken(", 2.0, False, False),
]


class SandboxService:
    """Run sandbox cases and record outcomes for the dashboard."""

    def __init__(self, executor: SandboxExecutor | None = None) -> None:
        self.executor = executor or SandboxExecutor(default_timeout=2.0)

    def execute(
        self,
        code: str,
        *,
        timeout: float | None = None,
        label: str = "adhoc",
        allowed_hit: bool = False,
        blocked_hit: bool = False,
    ) -> dict[str, Any]:
        result = self.executor.run(code, timeout=timeout, label=label)
        # Infer import hits when not provided by the caller.
        if not allowed_hit and result.ok and "import " in code:
            allowed_hit = True
        if not blocked_hit and result.blocked:
            blocked_hit = True

        METRICS.record(
            label=label or result.label or "adhoc",
            ok=result.ok,
            timeout=result.timeout,
            blocked=result.blocked,
            error=result.error,
            duration_ms=result.duration_ms,
            output=result.output,
            allowed_hit=allowed_hit,
            blocked_hit=blocked_hit,
        )
        return {
            "label": label or result.label,
            "ok": result.ok,
            "timeout": result.timeout,
            "blocked": result.blocked,
            "error": result.error,
            "duration_ms": result.duration_ms,
            "output": result.output,
        }

    def run_demo(self) -> dict[str, Any]:
        """Execute every demo case so all dashboard metrics become non-zero."""
        results: list[dict[str, Any]] = []
        for label, code, timeout, allowed_hit, blocked_hit in DEMO_CASES:
            results.append(
                self.execute(
                    code,
                    timeout=timeout,
                    label=label,
                    allowed_hit=allowed_hit,
                    blocked_hit=blocked_hit,
                )
            )
        METRICS.mark_demo()
        return {"results": results, "metrics": METRICS.snapshot()}
