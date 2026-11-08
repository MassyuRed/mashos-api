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


def test_explicit_analysis_service_accepts_longer_output_and_does_not_expire_after_probe_count():
    calls = []
    def generate(messages, deadline):
        calls.append(messages)
        assert 208 < deadline - time.monotonic() <= 210
        return '{"overview":"合成の分析"}', 'stop'
    server = ThreadingHTTPServer(('127.0.0.1', 0), probe.make_handler(generate,
        api_key='synthetic-analysis-key', model_name='analysis-4b', deadline=float('inf'), max_requests=0,
        max_new_tokens=4096, request_seconds=210, max_request_bytes=262144))
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    packet = dict(model='analysis-4b', messages=[dict(role='system', content='合成の定義'),
        dict(role='user', content='合成の入力')], temperature=0, max_tokens=4096, stream=False,
        chat_template_kwargs={'enable_thinking': False})
    try:
        base = f'http://127.0.0.1:{server.server_port}'
        with httpx.Client(trust_env=False) as client:
            assert client.get(base + '/healthz').json() == {'status': 'ok'}
            assert client.post(base + '/v1/chat/completions', json=packet).status_code == 401
            headers = {'Authorization': 'Bearer synthetic-analysis-key'}
            assert client.post(base + '/v1/chat/completions', headers=headers,
                               json={**packet, 'max_tokens': 2048}).status_code == 400
            assert client.post(base + '/v1/chat/completions', headers=headers,
                               json={**packet, 'max_tokens': True}).status_code == 400
            for _ in range(19):
                response = client.post(base + '/v1/chat/completions', headers=headers, json=packet)
                assert response.status_code == 200
                assert response.json()['choices'][0]['finish_reason'] == 'stop'
        assert len(calls) == 19
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)


def test_service_cli_uses_explicit_analysis_budgets_without_probe_alarm(monkeypatch):
    class Loaded(Exception):
        pass
    captured = {}
    def load(adapter, stop, **kwargs):
        captured.update(adapter=adapter, **kwargs)
        raise Loaded
    alarms = []
    monkeypatch.setattr(probe, 'load_generator', load)
    monkeypatch.setattr(probe.signal, 'signal', lambda *_: None)
    monkeypatch.setattr(probe.signal, 'setitimer', lambda *args: alarms.append(args))
    monkeypatch.setenv('COCOLON_ANALYSIS_MODEL_API_KEY', 'synthetic-analysis-private-key')
    monkeypatch.setattr(sys, 'argv', ['serve', '--model-name', 'analysis-4b', '--analysis-service'])
    with pytest.raises(Loaded):
        probe.main()
    assert captured == dict(adapter=None, max_new_tokens=4096, context_tokens=16384)
    assert alarms == []


@pytest.mark.parametrize('extra', [[], ['--seconds', '1800'], ['--max-requests', '18'],
    ['--max-new-tokens', '9000'], ['--context-tokens', '4096'], ['--request-seconds', '211'],
    ['--adapter', 'unselected-path']])
def test_service_cli_rejects_ambiguous_modes_budgets_and_unselected_adapter(extra, monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['serve', '--model-name', 'analysis-4b'] +
        ([] if not extra else ['--analysis-service'] + extra))
    monkeypatch.setattr(probe, 'load_generator', lambda *_a, **_k: pytest.fail('must reject before model load'))
    with pytest.raises(SystemExit) as exc:
        probe.main()
    assert exc.value.code == 2


def test_shared_profiles_keep_keys_budgets_and_single_gpu_lock():
    entered, release = threading.Event(), threading.Event()
    calls = []
    def generate(messages, deadline, *, profile=None):
        calls.append(profile)
        assert (20 < deadline-time.monotonic() <= 23) if profile == 'natural' else (208 < deadline-time.monotonic() <= 210)
        if messages[1]['content'] == 'hold':
            entered.set()
            assert release.wait(3)
        return '合成の返事です。' if profile else '{}', 'stop'
    server = ThreadingHTTPServer(('127.0.0.1', 0), probe.make_handler(generate,
        api_key='analysis-test-key', model_name='analysis', deadline=float('inf'), max_requests=0,
        max_new_tokens=4096, request_seconds=210, max_request_bytes=262144,
        natural_reply={'api_key':'natural-test-key','model_name':'natural'}, natural_queue_seconds=0.05))
    worker = threading.Thread(target=server.serve_forever, daemon=True); worker.start()
    def packet(model, tokens, body='synthetic'):
        return dict(model=model, max_tokens=tokens, temperature=0, stream=False,
                    chat_template_kwargs={'enable_thinking':False}, messages=[dict(role='system',content='synthetic'),dict(role='user',content=body)])
    url = f'http://127.0.0.1:{server.server_port}/v1/chat/completions'
    def post(key, payload):
        return httpx.post(url, headers={'Authorization':'Bearer '+key}, json=payload, trust_env=False)
    try:
        assert post('natural-test-key',packet('analysis',4096)).status_code == 400
        assert post('analysis-test-key',packet('natural',2048)).status_code == 400
        assert post('natural-test-key',packet('natural',4096)).status_code == 400
        assert post('natural-test-key',packet('natural',2048)).json()['model'] == 'natural'
        pending = threading.Thread(target=lambda:post('analysis-test-key',packet('analysis',4096,'hold')))
        pending.start(); assert entered.wait(3)
        assert post('natural-test-key',packet('natural',2048)).status_code == 429
        release.set(); pending.join(3)
        assert post('natural-test-key',packet('natural',2048)).status_code == 200
        assert calls == ['natural',None,'natural']
    finally:
        release.set();server.shutdown();server.server_close();worker.join(3)


@pytest.mark.parametrize('fail', [False, True])
def test_base_profile_restores_frozen_adapter_after_peft_context_exit(fail):
    from contextlib import contextmanager
    class Model:
        training = False
        grads = False
        active = True
        @contextmanager
        def disable_adapter(self):
            self.active = False
            try:
                yield
            finally:
                self.active = True
                self.grads = True  # PEFT 0.21.2 set_adapter's default on re-enable.
        def eval(self):
            self.training = False
        def requires_grad_(self, value):
            self.grads = value
    model = Model()
    try:
        with probe.base_inference_context(model):
            assert not model.active
            if fail:
                raise RuntimeError('synthetic forward failure')
    except RuntimeError:
        assert fail
    assert model.active and not model.grads and not model.training


def test_natural_waits_for_existing_analysis_without_repeating_either_generation():
    entered, release = threading.Event(), threading.Event()
    calls = []
    def generate(messages, deadline, *, profile=None):
        calls.append(profile)
        if profile is None:
            entered.set(); assert release.wait(3)
        return '合成の返事です。' if profile else '{}', 'stop'
    server = ThreadingHTTPServer(('127.0.0.1',0), probe.make_handler(generate,
        api_key='analysis',model_name='analysis',deadline=float('inf'),max_requests=0,
        max_new_tokens=4096,request_seconds=210,natural_reply={'api_key':'natural','model_name':'natural'}, natural_queue_seconds=2))
    worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
    replies=[]
    def post(model,tokens):
        replies.append(httpx.post(f'http://127.0.0.1:{server.server_port}/v1/chat/completions', trust_env=False,
            headers={'Authorization':'Bearer '+model}, json=dict(model=model,max_tokens=tokens,temperature=0,stream=False,
                chat_template_kwargs={'enable_thinking':False}, messages=[dict(role='system',content='synthetic'),dict(role='user',content='synthetic')])).status_code)
    a=threading.Thread(target=post,args=('analysis',4096));n=threading.Thread(target=post,args=('natural',2048))
    try:
        a.start();assert entered.wait(2);n.start()
        time.sleep(.1)
        assert calls==[None]
        release.set();a.join(3);n.join(3)
        assert sorted(replies)==[200,200] and calls==[None,'natural']
    finally:
        release.set();server.shutdown();server.server_close();worker.join(3)
