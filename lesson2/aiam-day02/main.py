#!/usr/bin/env python3
"""AIAM Day 2 — Tool Execution & Validation CLI Demo."""
from __future__ import annotations

import logging

from tools.registry import ToolOrchestrator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)-12s] %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)


def demo(orch: ToolOrchestrator, tool: str, params: dict, perms: list[str], label: str):
    r = orch.call(tool, params, perms, label=label)
    status = "OK " if r.success else "ERR"
    detail = r.output if r.success else r.error
    print(f"[{status}] {label:40s} → {detail}")


def main() -> None:
    print("\n" + "=" * 55)
    print("  AIAM Day 2 — Tool Execution & Validation (Layer 3)")
    print("=" * 55)
    orch = ToolOrchestrator()
    print(f"\nAvailable for [read]:       {orch.available(['read'])}")
    print(f"Available for [read,write]: {orch.available(['read', 'write'])}\n")

    demo(orch, "calculate", {"expression": "3 * (7 + 2)"}, ["read"], "Safe arithmetic 3*(7+2)")
    demo(orch, "calculate", {"expression": "__import__('os')"}, ["read"], "Unsafe injection attempt")
    demo(orch, "echo", {"message": "Hello from Layer 3!"}, ["read"], "Echo tool")
    demo(
        orch,
        "write_log",
        {"message": "deploy v1.2", "level": "INFO"},
        ["read", "write"],
        "Write log (write perm)",
    )
    demo(
        orch,
        "write_log",
        {"message": "sneaky write", "level": "INFO"},
        ["read"],
        "Write log (read only — denied)",
    )
    demo(orch, "nonexistent", {}, ["read", "write"], "Unknown tool")

    print("\n" + "=" * 55)
    print("  Day 2 Complete — Tool registry demonstrated.")
    print("  Next: Day 3 — Memory Systems")
    print("=" * 55 + "\n")


if __name__ == "__main__":
    main()
