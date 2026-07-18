"""CLI demo for AIAM Day 07 — Sandboxed Code Execution."""
from __future__ import annotations

from sandbox.service import SandboxService


def main() -> None:
    svc = SandboxService()
    print("")
    print("=" * 55)
    print("  AIAM Day 7 — Sandboxed Code Execution")
    print("=" * 55)
    demo = svc.run_demo()
    for item in demo["results"]:
        if item["timeout"]:
            tag = "TIMEOUT"
        elif item["blocked"]:
            tag = "BLOCKED"
        elif item["ok"]:
            tag = "OK      "
        else:
            tag = "ERROR  "
        print(f"  [{tag}] {item['label']:<28} -> {item['output'][:50]}")
    m = demo["metrics"]
    print("")
    print(
        f"  totals: ok={m['executions_ok']} blocked={m['executions_blocked']} "
        f"timeout={m['executions_timeout']} error={m['executions_error']}"
    )
    print("  Day 7 Complete — Next: Day 8 — Multi-Agent Orchestration")


if __name__ == "__main__":
    main()
