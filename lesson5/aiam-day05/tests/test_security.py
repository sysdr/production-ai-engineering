from security.hardening import OutputGuard, SignatureVerifier


def test_clean():
    g = OutputGuard()
    assert g.scan("Paris is the capital of France.")["clean"]


def test_secret():
    g = OutputGuard()
    r = g.scan("key sk-abc123abc123abc123abc123abc123ab")
    assert not r["clean"]
    assert "openai_key" in r["findings"]
    assert r["secret_count"] >= 1
    assert "[REDACTED]" in r["redacted"]


def test_email_pii():
    g = OutputGuard()
    r = g.scan("alice@example.com")
    assert not r["clean"]
    assert "email" in r["findings"]
    assert r["pii_count"] >= 1


def test_aws_key():
    g = OutputGuard()
    r = g.scan("AKIAIOSFODNN7EXAMPLE")
    assert not r["clean"]
    assert "aws_access_key" in r["findings"]


def test_hmac_valid():
    sv = SignatureVerifier("s3cr3t")
    sig = sv.sign("payload")
    assert sv.verify("payload", sig)


def test_hmac_tampered():
    sv = SignatureVerifier("s3cr3t")
    sig = sv.sign("payload")
    assert not sv.verify("tampered", sig)
