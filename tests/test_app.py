"""Static web shell + /api/v1 stubs (M5 scaffold). Live wiring waits on the contract."""

from fastapi.testclient import TestClient

from worksim.app import app

client = TestClient(app)


def test_index_is_split_pane_shell():
    r = client.get("/")
    assert r.status_code == 200
    body = r.text
    assert "WorkSim" in body
    assert "const api=(p,o)=>fetch('/api/v1'+p,o)" in body
    assert 'aria-label="Chat"' in body
    assert 'data-tab="money"' in body
    assert "EventSource" not in body  # polling, not SSE


def test_health_is_live():
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json() == {"ok": True, "service": "worksim"}


def test_run_lifecycle_routes_are_stubs():
    stubs = [
        ("GET", "/api/v1/scenarios"),
        ("GET", "/api/v1/jobs"),
        ("GET", "/api/v1/employees"),
        ("GET", "/api/v1/runs"),
        ("POST", "/api/v1/runs"),
        ("GET", "/api/v1/runs/run-x"),
        ("POST", "/api/v1/runs/run-x/start"),
        ("POST", "/api/v1/runs/run-x/stop"),
        ("GET", "/api/v1/runs/run-x/messages?since=0"),
        ("POST", "/api/v1/runs/run-x/messages"),
        ("GET", "/api/v1/runs/run-x/deliverables"),
        ("GET", "/api/v1/runs/run-x/money"),
    ]
    for method, path in stubs:
        r = client.request(method, path)
        assert r.status_code == 501, path
        body = r.json()
        assert body.get("ok") is False
        assert body.get("todo")
