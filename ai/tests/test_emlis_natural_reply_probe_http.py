"""Actual local HTTP probe protocol with a synthetic generator; no GPU."""
import importlib.util
import hashlib
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time
from http.server import ThreadingHTTPServer

import httpx
import pytest

spec = importlib.util.spec_from_file_location("natural_probe", Path(__file__).parents[1] / "tools/serve_emlis_natural_reply.py")
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


def test_selected_saved_candidate_requires_matching_pair_and_detects_later_change(tmp_path):
    weights, config = b'synthetic saved weights', b'{"synthetic":"config"}'
    (tmp_path/'adapter_model.safetensors').write_bytes(weights)
    (tmp_path/'adapter_config.json').write_bytes(config)
    identity = hashlib.sha256(weights).hexdigest(), hashlib.sha256(config).hexdigest()
    assert probe.adapter_identity(tmp_path, *identity) == identity
    with pytest.raises(ValueError, match='configuration_invalid'):
        probe.adapter_identity(tmp_path, identity[0], None)
    with pytest.raises(ValueError, match='configuration_invalid'):
        probe.adapter_identity(None, *identity)
    with pytest.raises(ValueError, match='identity_changed'):
        probe.adapter_identity(tmp_path, '0'*64, identity[1])
    (tmp_path/'adapter_config.json').write_bytes(b'changed after load')
    with pytest.raises(ValueError, match='identity_changed'):
        probe.adapter_identity(tmp_path, *identity)


def test_default_adapter_still_requires_fit38_identity(tmp_path, monkeypatch):
    (tmp_path/'adapter_model.safetensors').write_bytes(b'weights')
    (tmp_path/'adapter_config.json').write_bytes(b'config')
    monkeypatch.setattr(probe,'FIT38_WEIGHTS',hashlib.sha256(b'weights').hexdigest())
    monkeypatch.setattr(probe,'FIT38_CONFIG',hashlib.sha256(b'config').hexdigest())
    assert probe.adapter_identity(tmp_path) == (probe.FIT38_WEIGHTS,probe.FIT38_CONFIG)


def test_authenticated_probe_enforces_request_limit_without_repeating_generator():
    calls = []

    def generate(messages, deadline):
        calls.append(messages)
        assert time.monotonic() < deadline
        return "合成の返事です。", "stop"
    server = ThreadingHTTPServer(("127.0.0.1", 0), probe.make_handler(generate,
        api_key="synthetic-private-key", model_name="chosen-4b", deadline=time.monotonic() + 10, max_requests=1))
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    payload = {"model": "chosen-4b", "messages": [{"role": "system", "content": "合成の指示"},
        {"role": "user", "content": "合成の入力"}], "temperature": 0, "max_tokens": 2048,
        "stream": False, "chat_template_kwargs": {"enable_thinking": False}}
    try:
        url = f"http://127.0.0.1:{server.server_port}/v1/chat/completions"
        with httpx.Client(trust_env=False) as client:
            assert client.post(url, json=payload).status_code == 401
            headers = {"Authorization": "Bearer synthetic-private-key"}
            assert client.post(url, headers=headers, json={**payload, "model": "other"}).status_code == 400
            first = client.post(url, headers=headers, json=payload)
            assert first.status_code == 200
            assert first.json()["choices"][0]["message"]["content"] == "合成の返事です。"
            assert first.json()["model"] == "chosen-4b"
            assert client.post(url, headers=headers, json=payload).status_code == 429
        assert len(calls) == 1
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)


def test_probe_hard_deadline_also_stops_blocked_model_loading():
    script = Path(__file__).parents[1] / "tools/serve_emlis_natural_reply.py"
    code = """import importlib.util, sys, time
spec=importlib.util.spec_from_file_location('probe',sys.argv[1])
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
module.load_generator=lambda *_:time.sleep(30)
sys.argv=['probe','--model-name','synthetic','--max-requests','1','--seconds','1']
module.main()
"""
    started = time.monotonic()
    result = subprocess.run([sys.executable, "-c", code, str(script)],
        env={**os.environ, "EMLIS_NATURAL_REPLY_API_KEY": "synthetic-key-never-used-on-network"},
        capture_output=True, timeout=4)
    assert result.returncode == -signal.SIGALRM
    assert time.monotonic() - started < 4
