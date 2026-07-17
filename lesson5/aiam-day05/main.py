#!/usr/bin/env python3
"""AIAM Day 5 — CLI demo for security hardening."""
from security.service import SecurityService


def hr() -> None:
    print("─" * 60)


def main() -> None:
    print("\n" + "=" * 60)
    print("  AIAM Day 5 — Security Hardening Demo")
    print("=" * 60)

    svc = SecurityService()
    result = svc.run_demo()

    print("\n[1] OUTPUT GUARD")
    hr()
    for item in result["scans"]:
        status = "CLEAN  " if item["clean"] else "BLOCKED"
        findings = item["findings"] or ["ok"]
        print(f"  [{status}] {item['label']:25s} → {findings}")

    print("\n[2] HMAC SIGNING")
    hr()
    hmac_info = result["hmac"]
    print(f"  Payload:   {hmac_info['payload']}")
    print(f"  Signature: {hmac_info['signature'][:20]}...")
    print(f"  Valid?     {hmac_info['valid']}")
    print(f"  Tampered?  {hmac_info['tampered']}")

    m = result["metrics"]
    print("\n[3] METRICS SNAPSHOT")
    hr()
    for key in (
        "scans_total",
        "scans_clean",
        "scans_blocked",
        "secrets_detected",
        "pii_detected",
        "redactions_total",
        "hmac_signs",
        "hmac_verifications_ok",
        "hmac_verifications_fail",
        "demo_runs",
    ):
        print(f"  {key:28s} {m[key]}")

    print("\n" + "=" * 60)
    print("  Day 5 Complete — Security hardening shown.")
    print("  Next: Day 6 — Observability Stack")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
