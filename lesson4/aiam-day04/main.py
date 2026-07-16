#!/usr/bin/env python3
"""AIAM Day 4 — CLI demo for rate limiting and cost control."""
from ratelimit.service import RateLimitService


def hr() -> None:
    print("─" * 55)


def main() -> None:
    print("\n" + "=" * 55)
    print("  AIAM Day 4 — Rate Limiting & Cost Control Demo")
    print("=" * 55)

    svc = RateLimitService(budget_usd=1.00)

    print("\n[1] TOKEN BUCKET RATE LIMITER")
    hr()
    allowed = blocked = 0
    for _ in range(15):
        r = svc.check_request("alice", tier="standard", label="CLI_BURST")
        if r["allowed"]:
            allowed += 1
        else:
            blocked += 1
    print(f"  15 rapid requests → allowed={allowed} blocked={blocked}")
    print(f"  Bucket status: {svc.rate_limiter.status('alice')}")

    print("\n  Premium tier (50 burst):")
    premium_allowed = 0
    for _ in range(20):
        r = svc.check_request("premium_bob", tier="premium", label="CLI_PREMIUM")
        if r["allowed"]:
            premium_allowed += 1
    print(f"  20 rapid premium requests → allowed={premium_allowed}")

    print("\n[2] COST TRACKER")
    hr()
    users = [
        ("alice", 500_000, 200_000),
        ("bob", 300_000, 150_000),
        ("carol", 50_000, 25_000),
    ]
    for user, inp, out in users:
        r = svc.check_request(
            user, tier="standard", input_tokens=inp, output_tokens=out, label="CLI_COST"
        )
        print(
            f"  {user:8s}  in={inp:>8,}  out={out:>7,}  cost=${r['cost_usd']:.6f}"
        )

    ct = svc.cost_tracker
    print(f"\n  Total spend:        ${ct.total_spend()}")
    print(f"  Budget remaining:   ${ct.budget_remaining()}")
    print(f"  Over budget?        {ct.is_over_budget()}")
    print("\n  Spend report (sorted):")
    for row in ct.report():
        print(f"    {row['user']:8s}  ${row['spend_usd']:.6f}")

    print("\n[3] BUDGET ALERT DEMO")
    hr()
    budget_svc = RateLimitService(budget_usd=0.10)
    for i in range(10):
        budget_svc.check_request(
            f"user_{i}",
            tier="standard",
            input_tokens=100_000,
            output_tokens=50_000,
            label="CLI_BUDGET",
        )
    if budget_svc.cost_tracker.is_over_budget():
        print(
            f"  BUDGET EXCEEDED — spent ${budget_svc.cost_tracker.total_spend()} of $0.10 budget"
        )
    else:
        print(f"  Within budget — spent ${budget_svc.cost_tracker.total_spend()}")

    print("\n" + "=" * 55)
    print("  Day 4 Complete — Rate limiting & cost control shown.")
    print("  Next: Day 5 — Security Hardening")
    print("=" * 55 + "\n")


if __name__ == "__main__":
    main()
