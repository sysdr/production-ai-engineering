from collections import defaultdict

# Approximate costs per 1M tokens (gpt-4o-mini)
COST_PER_1M = {"input": 0.15, "output": 0.60}


class CostTracker:
    """Tracks per-user token consumption and spend with budget alerting."""

    def __init__(self, budget_usd: float = 10.0) -> None:
        self.budget_usd = budget_usd
        self._spend: dict[str, float] = defaultdict(float)
        self._tokens: dict[str, dict[str, int]] = defaultdict(
            lambda: {"input": 0, "output": 0}
        )

    def record(self, user_id: str, input_tokens: int, output_tokens: int) -> float:
        cost = (
            input_tokens / 1_000_000 * COST_PER_1M["input"]
            + output_tokens / 1_000_000 * COST_PER_1M["output"]
        )
        self._spend[user_id] += cost
        self._tokens[user_id]["input"] += input_tokens
        self._tokens[user_id]["output"] += output_tokens
        return round(cost, 8)

    def total_spend(self) -> float:
        return round(sum(self._spend.values()), 6)

    def user_spend(self, user_id: str) -> float:
        return round(self._spend.get(user_id, 0.0), 6)

    def budget_remaining(self) -> float:
        return round(self.budget_usd - self.total_spend(), 6)

    def is_over_budget(self) -> bool:
        return self.total_spend() >= self.budget_usd

    def user_count(self) -> int:
        return len(self._spend)

    def total_input_tokens(self) -> int:
        return sum(v["input"] for v in self._tokens.values())

    def total_output_tokens(self) -> int:
        return sum(v["output"] for v in self._tokens.values())

    def report(self) -> list[dict]:
        return sorted(
            [
                {
                    "user": u,
                    "spend_usd": round(v, 6),
                    "input_tokens": self._tokens[u]["input"],
                    "output_tokens": self._tokens[u]["output"],
                }
                for u, v in self._spend.items()
            ],
            key=lambda x: -x["spend_usd"],
        )
