"""Layer 3 — schema-validated tool registry with permission-gated dispatch."""
from __future__ import annotations

import logging
import time
from typing import Any

from pydantic import BaseModel, Field

from tools.metrics import METRICS

log = logging.getLogger("tools")


class ToolSchema(BaseModel):
    name: str
    description: str
    required_permission: str
    parameters: dict[str, str] = Field(default_factory=dict)


class ToolResult(BaseModel):
    tool: str
    success: bool
    output: Any = None
    error: str | None = None
    latency_ms: int = 0


TOOL_REGISTRY: dict[str, ToolSchema] = {
    "calculate": ToolSchema(
        name="calculate",
        description="Safe arithmetic evaluator",
        required_permission="read",
        parameters={"expression": "str"},
    ),
    "echo": ToolSchema(
        name="echo",
        description="Echo input as-is",
        required_permission="read",
        parameters={"message": "str"},
    ),
    "write_log": ToolSchema(
        name="write_log",
        description="Append a message to audit log",
        required_permission="write",
        parameters={"message": "str", "level": "str"},
    ),
}

# Restricted eval namespace — no builtins that enable code execution / I/O
SAFE_BUILTINS: dict[str, Any] = {
    "__builtins__": {},
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sum": sum,
    "len": len,
    "pow": pow,
}


class ToolOrchestrator:
    """Permission-gated, schema-validated tool dispatcher with metrics."""

    def available(self, permissions: list[str]) -> list[str]:
        return [
            name
            for name, schema in TOOL_REGISTRY.items()
            if schema.required_permission in permissions
        ]

    def call(
        self,
        tool_name: str,
        params: dict[str, Any],
        permissions: list[str],
        *,
        label: str = "",
        record_metrics: bool = True,
    ) -> ToolResult:
        t0 = time.monotonic()
        if tool_name not in TOOL_REGISTRY:
            ms = max(1, int((time.monotonic() - t0) * 1000))
            result = ToolResult(
                tool=tool_name, success=False, error="Unknown tool", latency_ms=ms
            )
            if record_metrics:
                METRICS.record(
                    tool=tool_name,
                    success=False,
                    error=result.error,
                    latency_ms=ms,
                    label=label or "unknown",
                )
            return result

        schema = TOOL_REGISTRY[tool_name]
        if schema.required_permission not in permissions:
            log.warning(
                "[L3] Permission denied: %s requires %s",
                tool_name,
                schema.required_permission,
            )
            ms = max(1, int((time.monotonic() - t0) * 1000))
            result = ToolResult(
                tool=tool_name,
                success=False,
                error="Permission denied",
                latency_ms=ms,
            )
            if record_metrics:
                METRICS.record(
                    tool=tool_name,
                    success=False,
                    error=result.error,
                    latency_ms=ms,
                    label=label or tool_name,
                )
            return result

        missing = [k for k in schema.parameters if k not in params]
        if missing:
            ms = max(1, int((time.monotonic() - t0) * 1000))
            result = ToolResult(
                tool=tool_name,
                success=False,
                error=f"Missing params: {missing}",
                latency_ms=ms,
            )
            if record_metrics:
                METRICS.record(
                    tool=tool_name,
                    success=False,
                    error=result.error,
                    latency_ms=ms,
                    label=label or tool_name,
                )
            return result

        try:
            output = self._dispatch(tool_name, params)
            ms = max(1, int((time.monotonic() - t0) * 1000))
            log.info("[L3] Tool OK: %s %sms", tool_name, ms)
            result = ToolResult(
                tool=tool_name, success=True, output=output, latency_ms=ms
            )
            if record_metrics:
                METRICS.record(
                    tool=tool_name,
                    success=True,
                    latency_ms=ms,
                    output=output,
                    label=label or tool_name,
                )
            return result
        except Exception as exc:  # noqa: BLE001 — surface tool errors cleanly
            ms = max(1, int((time.monotonic() - t0) * 1000))
            result = ToolResult(
                tool=tool_name, success=False, error=str(exc), latency_ms=ms
            )
            if record_metrics:
                METRICS.record(
                    tool=tool_name,
                    success=False,
                    error=result.error,
                    latency_ms=ms,
                    label=label or tool_name,
                )
            return result

    def _dispatch(self, name: str, params: dict[str, Any]) -> Any:
        if name == "calculate":
            expr = str(params["expression"])
            banned = ('"', "'", "import", "exec", "eval", "open", "__", "os.", "sys.")
            if any(token in expr for token in banned):
                raise ValueError("Unsafe expression rejected")
            # Sandboxed arithmetic only — empty builtins + allowlisted helpers
            return eval(expr, SAFE_BUILTINS, {})  # noqa: S307
        if name == "echo":
            return params["message"]
        if name == "write_log":
            entry = {
                "level": params.get("level", "INFO"),
                "msg": params["message"],
            }
            log.info("[AUDITLOG] %s", entry)
            return "logged"
        raise ValueError(f"No handler for {name}")
