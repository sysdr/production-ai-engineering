"""Secrets/PII output scanning and HMAC payload signing."""
from __future__ import annotations

import hashlib
import hmac
import re
from typing import Any


SECRET_PATTERNS: list[tuple[str, str]] = [
    (r"sk-[A-Za-z0-9]{32,}", "openai_key"),
    (r"ghp_[A-Za-z0-9]{36}", "github_pat"),
    (r"AKIA[0-9A-Z]{16}", "aws_access_key"),
    (r"password\s*=\s*\S+", "password_literal"),
    (r"Bearer\s+[A-Za-z0-9\-._~+/]+=*", "bearer_token"),
]

PII_PATTERNS: list[tuple[str, str]] = [
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "email"),
    (r"\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b", "phone_us"),
    (r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b", "credit_card"),
]


class OutputGuard:
    """Scan model/output text for secrets and PII; redact matches."""

    def __init__(self) -> None:
        self._secrets = [(re.compile(p, re.IGNORECASE), t) for p, t in SECRET_PATTERNS]
        self._pii = [(re.compile(p, re.IGNORECASE), t) for p, t in PII_PATTERNS]

    def scan(self, text: str) -> dict[str, Any]:
        findings: list[str] = []
        for pat, label in self._secrets + self._pii:
            if pat.search(text):
                findings.append(label)

        redacted = text
        for pat, _ in self._secrets + self._pii:
            redacted = pat.sub("[REDACTED]", redacted)

        secret_hits = [f for f in findings if f in {t for _, t in SECRET_PATTERNS}]
        pii_hits = [f for f in findings if f in {t for _, t in PII_PATTERNS}]

        return {
            "clean": len(findings) == 0,
            "findings": findings,
            "secret_count": len(secret_hits),
            "pii_count": len(pii_hits),
            "redacted": redacted,
            "redaction_count": max(0, len(findings)),
        }


class SignatureVerifier:
    """HMAC-SHA256 sign/verify for request integrity."""

    def __init__(self, secret: str) -> None:
        self._secret = secret.encode("utf-8")

    def sign(self, payload: str) -> str:
        return hmac.new(self._secret, payload.encode("utf-8"), hashlib.sha256).hexdigest()

    def verify(self, payload: str, signature: str) -> bool:
        expected = self.sign(payload)
        return hmac.compare_digest(expected, signature)
