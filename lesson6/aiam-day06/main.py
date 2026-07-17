#!/usr/bin/env python3
"""AIAM Day 6 — CLI demo for the observability stack."""
from observability.service import ObservabilityService


def hr() -> None:
    print("-" * 60)


def main() -> None:
    print("\n" + "=" * 60)
    print("  AIAM Day 6 — Observability Stack Demo")
    print("=" * 60)

    svc = ObservabilityService()
    result = svc.run_demo()
    m = result["metrics"]

    print(f"\n[1] STRUCTURED LOGS  (emitted {result['generated']} JSON events above)")
    hr()
    print("  Each line above is a single JSON document with route, status,")
    print("  latency_ms and request_id — ready for log shipping / parsing.")

    print("\n[2] RED METRICS  (Rate / Errors / Duration)")
    hr()
    print(f"  requests_total      {m['requests_total']}")
    print(f"  requests_ok         {m['requests_ok']}")
    print(f"  requests_error      {m['requests_error']}")
    print(f"  error_rate          {m['error_rate'] * 100:.1f}%")
    print(f"  throughput_rps      {m['throughput_rps']}")

    print("\n[3] LATENCY HISTOGRAM")
    hr()
    print(f"  p50   {m['latency_p50_ms']} ms")
    print(f"  p95   {m['latency_p95_ms']} ms")
    print(f"  p99   {m['latency_p99_ms']} ms")
    print(f"  avg   {m['latency_avg_ms']} ms")
    print(f"  max   {m['latency_max_ms']} ms")

    print("\n[4] LOG LEVELS")
    hr()
    print(f"  INFO   {m['logs_info']}")
    print(f"  WARN   {m['logs_warn']}")
    print(f"  ERROR  {m['logs_error']}")

    print("\n[5] PER-ROUTE BREAKDOWN")
    hr()
    for route, stats in m["routes"].items():
        print(f"  {route:14s} count={stats['count']:<4d} errors={stats['errors']}")

    print("\n" + "=" * 60)
    print("  Day 6 Complete — Observability stack shown.")
    print("  Next: Day 7 — Sandboxed Code Execution")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
