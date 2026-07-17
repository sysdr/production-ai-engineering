"""In-process metrics store for the Day 5 dashboard (single-worker uvicorn)."""
from __future__ import annotations

import threading
from copy import deepcopy
from datetime import UTC, datetime
from typing import Any


class MetricsStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._event_sequence = 0
        self._data: dict[str, Any] = {
            "scans_total": 0,
            "scans_clean": 0,
            "scans_blocked": 0,
            "block_rate": 0.0,
            "secrets_detected": 0,
            "pii_detected": 0,
            "redactions_total": 0,
            "hmac_signs": 0,
            "hmac_verifications_ok": 0,
            "hmac_verifications_fail": 0,
            "latency_ms_avg": 0.0,
            "latency_ms_total": 0,
            "demo_runs": 0,
            "last_status": "idle",
            "last_label": "",
            "last_detail": "",
            "recent_events": [],
        }

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return deepcopy(self._data)

    def record_scan(
        self,
        *,
        label: str,
        clean: bool,
        secret_count: int,
        pii_count: int,
        redaction_count: int,
        latency_ms: int,
        detail: str = "",
        findings: list[str] | None = None,
    ) -> None:
        with self._lock:
            self._data["scans_total"] += 1
            if clean:
                self._data["scans_clean"] += 1
                status = "clean"
            else:
                self._data["scans_blocked"] += 1
                status = "blocked"

            total = self._data["scans_total"]
            blocked = self._data["scans_blocked"]
            self._data["block_rate"] = round(blocked / total, 4) if total else 0.0
            self._data["secrets_detected"] += max(0, secret_count)
            self._data["pii_detected"] += max(0, pii_count)
            self._data["redactions_total"] += max(0, redaction_count)
            self._data["latency_ms_total"] += max(0, latency_ms)
            self._data["latency_ms_avg"] = round(
                self._data["latency_ms_total"] / total, 2
            )
            self._data["last_status"] = status
            self._data["last_label"] = label
            self._data["last_detail"] = detail[:200]

            self._event_sequence += 1
            events = self._data["recent_events"]
            events.insert(
                0,
                {
                    "id": self._event_sequence,
                    "timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
                    "label": label,
                    "status": status,
                    "latency_ms": latency_ms,
                    "detail": detail[:120],
                    "findings": findings or [],
                },
            )
            self._data["recent_events"] = events[:10]

    def record_hmac(
        self,
        *,
        label: str,
        signed: bool = False,
        verified_ok: bool | None = None,
        expect_reject: bool = False,
        latency_ms: int = 0,
        detail: str = "",
    ) -> None:
        with self._lock:
            if signed:
                self._data["hmac_signs"] += 1
            if verified_ok is True:
                self._data["hmac_verifications_ok"] += 1
                # Unexpected accept when we expected rejection is a real failure
                status = "hmac_fail" if expect_reject else "hmac_ok"
            elif verified_ok is False:
                self._data["hmac_verifications_fail"] += 1
                # Intentional tamper probe: rejection is the correct outcome
                status = "tamper_caught" if expect_reject else "hmac_fail"
            else:
                status = "hmac_sign"

            if latency_ms:
                # attribute latency without inflating scan averages disproportionately
                self._data["latency_ms_total"] += max(0, latency_ms)
                denom = max(1, self._data["scans_total"] + self._data["hmac_signs"])
                self._data["latency_ms_avg"] = round(
                    self._data["latency_ms_total"] / denom, 2
                )

            self._data["last_status"] = status
            self._data["last_label"] = label
            self._data["last_detail"] = detail[:200]

            self._event_sequence += 1
            events = self._data["recent_events"]
            events.insert(
                0,
                {
                    "id": self._event_sequence,
                    "timestamp": datetime.now(UTC).isoformat(timespec="seconds"),
                    "label": label,
                    "status": status,
                    "latency_ms": latency_ms,
                    "detail": detail[:120],
                    "findings": [],
                },
            )
            self._data["recent_events"] = events[:10]

    def bump_demo(self) -> None:
        with self._lock:
            self._data["demo_runs"] += 1


METRICS = MetricsStore()
