from pydantic import BaseModel, Field
from typing import Any
from enum import Enum
import uuid


class AgentRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class SecurityContext(BaseModel):
    """Attached to every request that enters the agent."""
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    session_id: str
    permissions: list[str] = Field(default_factory=list)
    rate_limit_tier: str = "standard"


class AgentRequest(BaseModel):
    raw_input: str
    security_ctx: SecurityContext
    max_tokens: int = 512
    temperature: float = 0.1
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentResponse(BaseModel):
    request_id: str
    content: str
    tool_calls: list[dict] = Field(default_factory=list)
    tokens_used: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0
    layer_timings: dict[str, int] = Field(default_factory=dict)
    status: str = "ok"  # ok | blocked | rejected
