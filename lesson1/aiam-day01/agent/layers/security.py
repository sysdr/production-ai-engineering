import re
import html
import time
import logging
from agent.core.types import AgentRequest

log = logging.getLogger("security")

INJECTION_PATTERNS = [
    r"ignore (previous|above|prior) instructions",
    r"you are now",
    r"pretend (you are|to be)",
    r"disregard (all|your) (previous|prior)",
    r"reveal your (instructions|prompt|system)",
    r"<\|.*?\|>",
    r"\[INST\].*?\[/INST\]",
    r"DAN mode",
    r"jailbreak",
    r"bypass (safety|filter|restriction)",
]


class StubRateLimiter:
    _counts: dict = {}
    LIMITS = {"standard": 60, "premium": 300}

    def check(self, user_id: str, tier: str):
        key = f"{user_id}:{int(time.time() // 60)}"
        self._counts[key] = self._counts.get(key, 0) + 1
        if self._counts[key] > self.LIMITS.get(tier, 60):
            raise PermissionError(f"Rate limit exceeded for {user_id} ({tier})")
        log.info(
            f"[L4] Rate OK — {user_id} used {self._counts[key]}/{self.LIMITS.get(tier, 60)}"
        )


class StubRBAC:
    ROLE_PERMISSIONS = {
        "guest": ["read"],
        "user": ["read", "write"],
        "admin": ["read", "write", "delete", "config"],
    }

    def assert_request_allowed(self, ctx):
        log.info(f"[L4] RBAC OK — user={ctx.user_id} perms={ctx.permissions}")


class SecurityPerimeter:
    """Layer 4 — the outermost gate. All input processed here first."""

    MAX_INPUT_LENGTH = 8_000

    def __init__(self):
        self._compiled = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]
        self._rate_limiter = StubRateLimiter()
        self._rbac = StubRBAC()

    def process(self, request: AgentRequest) -> AgentRequest:
        ctx = request.security_ctx
        log.info(f"[L4] SecurityPerimeter.start — request_id={ctx.request_id}")

        if len(request.raw_input) > self.MAX_INPUT_LENGTH:
            raise ValueError(f"Input exceeds {self.MAX_INPUT_LENGTH} chars")

        sanitised = html.escape(request.raw_input)
        sanitised = " ".join(sanitised.split())

        for pattern in self._compiled:
            if pattern.search(sanitised):
                log.warning(
                    f"[L4] INJECTION ATTEMPT blocked — pattern={pattern.pattern[:40]!r}"
                )
                raise PermissionError("Potential prompt injection detected")

        self._rate_limiter.check(ctx.user_id, ctx.rate_limit_tier)
        self._rbac.assert_request_allowed(ctx)

        log.info(f"[L4] SecurityPerimeter.pass — request_id={ctx.request_id}")
        return request.model_copy(update={"raw_input": sanitised})
