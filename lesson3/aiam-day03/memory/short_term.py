"""Sliding-window session memory with token-budget awareness."""
from __future__ import annotations

import time
from collections import deque

from pydantic import BaseModel, Field


class Turn(BaseModel):
    role: str
    content: str
    timestamp: float = Field(default=0.0)


class ShortTermMemory:
    """Sliding-window session memory with token-budget awareness."""

    def __init__(self, max_turns: int = 10, max_tokens: int = 4096) -> None:
        self._sessions: dict[str, deque[Turn]] = {}
        self.max_turns = max_turns
        self.max_tokens = max_tokens

    def _token_estimate(self, turns: list[Turn]) -> int:
        return sum(len(t.content.split()) * 4 // 3 for t in turns)

    def get(self, session_id: str) -> list[dict[str, str]]:
        turns = list(self._sessions.get(session_id, []))
        while turns and self._token_estimate(turns) > self.max_tokens:
            turns = turns[2:]  # drop oldest pair
        return [{"role": t.role, "content": t.content} for t in turns]

    def store(self, session_id: str, user: str, assistant: str) -> None:
        q = self._sessions.setdefault(
            session_id, deque(maxlen=self.max_turns * 2)
        )
        now = time.time()
        q.append(Turn(role="user", content=user, timestamp=now))
        q.append(Turn(role="assistant", content=assistant, timestamp=now))

    def flush(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    def session_count(self) -> int:
        return len(self._sessions)

    def stats(self, session_id: str) -> dict[str, int]:
        turns = list(self._sessions.get(session_id, []))
        return {"turns": len(turns) // 2, "est_tokens": self._token_estimate(turns)}
