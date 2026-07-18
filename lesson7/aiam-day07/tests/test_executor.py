from sandbox.executor import SandboxExecutor


def test_safe_arithmetic():
    r = SandboxExecutor().run("print(sum(range(1, 11)))")
    assert r.ok
    assert "55" in r.output
    assert not r.timeout
    assert not r.blocked


def test_allowed_math_import():
    r = SandboxExecutor().run("import math\nprint(int(math.pi))")
    assert r.ok
    assert "3" in r.output


def test_allowed_collections_import():
    r = SandboxExecutor().run(
        "from collections import Counter\nprint(Counter('hello').most_common(1))"
    )
    assert r.ok
    assert "l" in r.output


def test_allowed_json_import():
    r = SandboxExecutor().run("import json\nprint(json.dumps({'a': 1}))")
    assert r.ok
    assert "a" in r.output


def test_blocked_os_import():
    r = SandboxExecutor().run("import os\nprint(os.getcwd())")
    assert not r.ok
    assert r.blocked
    assert "Blocked" in r.output or "ImportError" in r.output


def test_timeout_enforced():
    r = SandboxExecutor().run("while True: pass", timeout=0.3)
    assert not r.ok
    assert r.timeout
    assert r.output == "TIMED OUT"


def test_syntax_error():
    r = SandboxExecutor().run("def broken(")
    assert not r.ok
    assert r.error
    assert not r.timeout
    assert not r.blocked
