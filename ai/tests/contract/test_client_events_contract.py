from __future__ import annotations

from api_contract_registry import API_CONTRACT_POLICY_VERSION


def test_client_events_accepts_observability_payload_and_returns_contract_headers(client):
    response = client.post(
        "/ops/client-events",
        headers={
            "X-App-Version": "1.0.0",
            "X-App-Build": "100",
            "X-Platform": "ios",
        },
        json={
            "client_event_id": "evt-1",
            "event_name": "api_error",
            "severity": "error",
            "source": "react_native",
            "scope": "apiClient",
            "api_path": "/home/state",
            "status_code": 503,
            "error_name": "TimeoutError",
            "error_message": "Request timed out",
            "meta": {
                "method": "GET",
                "access_token": "must-not-log",
            },
        },
    )

    assert response.status_code == 200, response.text
    assert response.headers["X-Cocolon-Api-Policy-Version"] == API_CONTRACT_POLICY_VERSION
    assert response.headers["X-Cocolon-Contract-Id"] == "ops.client_events.write.v1"
    assert response.headers["X-Cocolon-Deprecated"] == "false"
    assert response.headers["X-Cocolon-Request-Id"]
    body = response.json()
    assert body["status"] == "ok"
    assert body["accepted"] is True
    assert body["event_name"] == "api_error"
    assert body["severity"] == "error"
    assert body["event_id"] == "evt-1"
    assert body["stored"] is False
    assert body["schema_version"] == "ops.client_event.v1"
    assert body["received_at"]


def test_client_events_redacts_sensitive_payload_before_logging(client, monkeypatch):
    import api_client_events as client_events_module

    captured = {}
    alerts = {}

    async def fake_optional_user_id(_authorization):
        return "11111111-2222-4333-9444-555555555555"

    def fake_log_event(_logger, event, *, level="info", **fields):
        captured.update({"event": event, "level": level, **fields})

    def fake_log_alert(_logger, alert_key, *, level="warning", message=None, event="alert", **fields):
        alerts.update({"alert_key": alert_key, "level": level, "message": message, "event": event, **fields})

    monkeypatch.setattr(client_events_module, "_optional_user_id", fake_optional_user_id)
    monkeypatch.setattr(client_events_module, "log_event", fake_log_event)
    monkeypatch.setattr(client_events_module, "log_alert", fake_log_alert)

    response = client.post(
        "/ops/client-events",
        headers={
            "Authorization": "Bearer fake-token",
            "X-App-Version": "1.0.0",
            "X-App-Build": "100",
            "X-Platform": "android",
        },
        json={
            "event_name": "api_error",
            "severity": "fatal",
            "scope": "apiClient",
            "api_path": "/account/profile/me?email=mash@example.com",
            "error_name": "NetworkError",
            "error_message": "Bearer abcdefghijklmnopqrstuvwxyz1234567890 user=mash@example.com id=11111111-2222-4333-9444-555555555555",
            "message": "refresh_token=abcdefghijklmnopqrstuvwxyz1234567890",
            "meta": {
                "Authorization": "Bearer secret-token-abcdefghijklmnopqrstuvwxyz",
                "nested": {
                    "email": "mash@example.com",
                    "user_id": "11111111-2222-4333-9444-555555555555",
                    "safe": "ok",
                },
            },
        },
    )

    assert response.status_code == 200, response.text
    assert captured["event"] == "client_event_received"
    assert captured["level"] == "error"
    assert captured["user_present"] is True
    assert captured["user_hash"]
    assert "user_id" not in captured
    assert "[redacted-email]" in captured["api_path"]
    assert "[redacted-email]" in captured["error_message"]
    assert "[redacted-token]" in captured["error_message"]
    assert "[redacted-id]" in captured["error_message"]
    assert captured["meta"]["Authorization"] == "[redacted]"
    assert captured["meta"]["nested"]["email"] == "[redacted-email]"
    assert captured["meta"]["nested"]["user_id"] == "[redacted-id]"
    assert alerts["alert_key"] == "CLIENT_EVENT_ERROR"
    assert "mash@example.com" not in str(captured)
    assert "secret-token" not in str(captured)
    assert "11111111-2222-4333-9444-555555555555" not in str(captured)
