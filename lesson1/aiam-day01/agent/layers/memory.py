import logging

log = logging.getLogger("memory")


class InMemoryStore:
    """Layer 2 — short-term in-process session memory."""

    def __init__(self, max_turns: int = 10):
        self._store: dict[str, list[dict]] = {}
        self.max_turns = max_turns

    def get_context(self, session_id: str) -> list[dict]:
        history = self._store.get(session_id, [])
        log.info(f"[L2] Memory.get — session={session_id} turns={len(history)}")
        return history

    def store(self, session_id: str, user_msg: str, assistant_msg: str):
        turns = self._store.setdefault(session_id, [])
        turns.append({"role": "user", "content": user_msg})
        turns.append({"role": "assistant", "content": assistant_msg})
        if len(turns) > self.max_turns * 2:
            turns[:] = turns[-(self.max_turns * 2) :]
        log.info(f"[L2] Memory.store — session={session_id} total_turns={len(turns)//2}")
