import logging
from agent.core.types import AgentResponse

log = logging.getLogger("tools")

TOOL_REGISTRY = {
    "echo": {"permissions": ["read"], "description": "Echo back the input"},
    "calculate": {"permissions": ["read"], "description": "Basic arithmetic"},
    "write_db": {"permissions": ["write"], "description": "Write to a database"},
}


class ToolOrchestrator:
    """Layer 3 — controls tool access, validates schemas, filters output."""

    def get_available_tools(self, permissions: list[str]) -> list[str]:
        available = [
            name
            for name, meta in TOOL_REGISTRY.items()
            if any(p in permissions for p in meta["permissions"])
        ]
        log.info(f"[L3] Available tools for {permissions}: {available}")
        return available

    def filter_output(self, response: AgentResponse) -> AgentResponse:
        filtered = response.content
        for pattern in ["sk-", "Bearer ", "password=", "secret="]:
            if pattern in filtered:
                filtered = "[REDACTED]"
                log.warning("[L3] Output filter — potential secret redacted")
                break
        return response.model_copy(update={"content": filtered})
