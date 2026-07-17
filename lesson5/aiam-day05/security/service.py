"""Coordinates output scanning, HMAC signing, and metrics."""
from __future__ import annotations

import os
import time
from typing import Any

from security.hardening import OutputGuard, SignatureVerifier
from security.metrics import METRICS


class SecurityService:
    def __init__(self, hmac_secret: str | None = None) -> None:
        secret = hmac_secret or os.getenv("HMAC_SECRET", "day05-secret")
        self.guard = OutputGuard()
        self.signer = SignatureVerifier(secret)

    def scan_text(self, text: str, *, label: str = "scan") -> dict[str, Any]:
        t0 = time.monotonic()
        result = self.guard.scan(text)
        ms = max(1, int((time.monotonic() - t0) * 1000))
        findings = result["findings"]
        detail = (
            "ok"
            if result["clean"]
            else f"findings={','.join(findings)}"
        )
        METRICS.record_scan(
            label=label,
            clean=result["clean"],
            secret_count=result["secret_count"],
            pii_count=result["pii_count"],
            redaction_count=result["redaction_count"],
            latency_ms=ms,
            detail=detail,
            findings=findings,
        )
        return {**result, "label": label, "latency_ms": ms}

    def sign_payload(self, payload: str, *, label: str = "sign") -> dict[str, Any]:
        t0 = time.monotonic()
        signature = self.signer.sign(payload)
        ms = max(1, int((time.monotonic() - t0) * 1000))
        METRICS.record_hmac(
            label=label,
            signed=True,
            latency_ms=ms,
            detail=f"sig={signature[:16]}…",
        )
        return {"payload": payload, "signature": signature, "latency_ms": ms}

    def verify_payload(
        self,
        payload: str,
        signature: str,
        *,
        label: str = "verify",
        expect_reject: bool = False,
    ) -> dict[str, Any]:
        t0 = time.monotonic()
        ok = self.signer.verify(payload, signature)
        ms = max(1, int((time.monotonic() - t0) * 1000))
        if expect_reject:
            detail = (
                "tamper correctly rejected"
                if not ok
                else "unexpected accept of tampered payload"
            )
        else:
            detail = "valid" if ok else "tampered/invalid"
        METRICS.record_hmac(
            label=label,
            verified_ok=ok,
            expect_reject=expect_reject,
            latency_ms=ms,
            detail=detail,
        )
        return {"payload": payload, "valid": ok, "latency_ms": ms}

    def run_demo(self) -> dict[str, Any]:
        cases = [
            ("Normal text", "Paris is the capital of France."),
            ("OpenAI key leak", "Use key sk-testkeytestkeytestkeytestkeytestkey"),
            ("AWS key leak", "AKIAIOSFODNN7EXAMPLE in config"),
            ("Email PII", "email alice@corp.example.com for help"),
            ("Credit card PII", "Card: 4111 1111 1111 1111"),
            ("Clean text", "No secrets here at all."),
            ("Bearer token", "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.abc"),
            ("Password literal", "db password=s3cretValue99"),
        ]
        scan_results: list[dict[str, Any]] = []
        for label, text in cases:
            scan_results.append(self.scan_text(text, label=label))

        payload = '{"user":"alice","action":"deploy"}'
        signed = self.sign_payload(payload, label="HMAC_SIGN")
        # Probe tampering first (correct reject → tamper_caught), then end on valid OK
        tampered = self.verify_payload(
            payload + "x",
            signed["signature"],
            label="HMAC_TAMPER",
            expect_reject=True,
        )
        valid = self.verify_payload(payload, signed["signature"], label="HMAC_OK")

        METRICS.bump_demo()
        return {
            "scans": scan_results,
            "hmac": {
                "payload": payload,
                "signature": signed["signature"],
                "valid": valid["valid"],
                "tampered": tampered["valid"],
            },
            "metrics": METRICS.snapshot(),
        }
