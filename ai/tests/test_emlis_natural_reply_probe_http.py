"""Actual local HTTP probe protocol with a synthetic generator; no GPU."""
import importlib.util
from copy import deepcopy
import hashlib
import json
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


def _correction_context_messages():
    from cocolon_meaning_experience_engine.natural_reply import NaturalReplyInput, build_natural_reply_messages
    def correction(identity, target, explanation):
        return dict(source_role='USER_INTERPRETATION_CORRECTION', correction_id=identity,
            target_event_id='event-' + identity, target_ai_interpretation=target,
            recorded_at='2026-11-13T04:00:00+09:00', user_explanation=explanation, assessment='UNASSESSED')
    material = dict(current_input_id='current-input', current=dict(memo='本人の原文。'),
        interpretation_corrections=[correction('current-correction', '先生が姉を呼び止めた', '違います。')],
        past_user_records=[dict(input_id='past-input', original=dict(memo='昔の原文。'),
            interpretation_corrections=[correction('past-correction', '先に説明した', '後から説明しました。')])])
    request = NaturalReplyInput('same-source-prefix', json.dumps(material, ensure_ascii=False))
    return build_natural_reply_messages(request, correction_target_context=True)


@pytest.mark.parametrize('enabled', [False, True])
def test_correction_context_http_admission_is_explicit_natural_only_and_locator_bound(enabled):
    calls = []
    def generate(messages, deadline, *, profile=None):
        calls.append((deepcopy(messages), profile))
        return '合成の返事です。', 'stop'
    server = ThreadingHTTPServer(('127.0.0.1', 0), probe.make_handler(generate,
        api_key='analysis-test-key', model_name='analysis', deadline=float('inf'), max_requests=0,
        max_new_tokens=4096, request_seconds=210,
        natural_reply={'api_key':'natural-test-key', 'model_name':'natural'},
        correction_target_context=enabled))
    worker = threading.Thread(target=server.serve_forever, daemon=True); worker.start()
    candidate = _correction_context_messages()
    def packet(messages, *, model='natural', tokens=2048, **extra):
        return dict(model=model, messages=messages, max_tokens=tokens, temperature=0,
            stream=False, chat_template_kwargs={'enable_thinking':False}, **extra)
    try:
        with httpx.Client(trust_env=False, timeout=5) as client:
            url = f'http://127.0.0.1:{server.server_port}/v1/chat/completions'
            def post(body, key='natural-test-key'):
                return client.post(url, json=body, headers={'Authorization':'Bearer ' + key})
            assert post(packet(candidate), key='wrong-private-key').status_code == 401
            assert not calls
            assert post(packet(candidate)).status_code == (200 if enabled else 400)
            assert len(calls) == int(enabled)
            if enabled:
                assert calls[0] == (candidate, 'natural')
            count = len(calls)
            # Neither another profile nor a Piece request may use the new shape.
            assert post(packet(candidate, model='analysis', tokens=4096), key='analysis-test-key').status_code == 400
            assert post(packet(candidate, candidate_format=probe.PIECE_CANDIDATE_FORMAT)).status_code == 400
            for mutation in ('extra-context', 'extra-target-field', 'spoof-role', 'parent', 'event', 'path',
                             'duplicate-ref', 'dangling-ref', 'source-target', 'blank-target',
                             'extra-target', 'missing-target', 'extra-message', 'wrong-message-role', 'invalid-json'):
                messages = deepcopy(candidate)
                context = json.loads(messages[1]['content'])
                person = json.loads(messages[2]['content'])
                targets = context['ai_interpretation_targets']
                if mutation == 'extra-context': context['other_assistant_history'] = 'unsupported'
                elif mutation == 'extra-target-field': targets[0]['other'] = 'unsupported'
                elif mutation == 'spoof-role': targets[0]['source_role'] = 'USER_INTERPRETATION_CORRECTION'
                elif mutation == 'parent': targets[0]['parent_input_id'] = 'another-input'
                elif mutation == 'event': targets[0]['target_event_id'] = 'another-event'
                elif mutation == 'path': targets[0]['correction_source_path'] = 'past_user_records[0].interpretation_corrections[0]'
                elif mutation == 'duplicate-ref': targets[1]['context_ref'] = targets[0]['context_ref']
                elif mutation == 'dangling-ref': person['interpretation_corrections'][0]['target_ai_context_ref'] = 'ai_interpretation_targets[99]'
                elif mutation == 'source-target': person['interpretation_corrections'][0]['target_ai_interpretation'] = targets[0]['target_ai_interpretation']
                elif mutation == 'blank-target': targets[0]['target_ai_interpretation'] = ' '
                elif mutation == 'extra-target': targets.append(deepcopy(targets[0]))
                elif mutation == 'missing-target': targets.pop()
                messages[1]['content'] = json.dumps(context, ensure_ascii=False)
                messages[2]['content'] = json.dumps(person, ensure_ascii=False)
                if mutation == 'extra-message': messages.insert(2, dict(role='assistant', content='extra context'))
                elif mutation == 'wrong-message-role': messages[1]['role'] = 'user'
                elif mutation == 'invalid-json': messages[1]['content'] = '{'
                assert post(packet(messages)).status_code == 400, mutation
            assert len(calls) == count
            ordinary = [dict(role='system',content='synthetic'), dict(role='user',content='synthetic')]
            assert post(packet(ordinary)).status_code == 200
            assert post(packet(ordinary, model='analysis', tokens=4096), key='analysis-test-key').status_code == 200
            piece = [ordinary[0], dict(role='user', content=json.dumps(dict(core='piece', task='PIECE_MODEL_BODY',
                control=dict(field_slots={'memo_0':{}}))))]
            assert post(packet(piece, candidate_format=probe.PIECE_CANDIDATE_FORMAT)).status_code == 200
            assert calls[count:] == [(ordinary, 'natural'), (ordinary, None), (piece, 'piece')]
    finally:
        server.shutdown(); server.server_close(); worker.join(3)


def test_correction_context_cli_requires_shared_profile_and_forwards_explicit_option(monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['serve','--model-name','analysis','--analysis-service',
        '--natural-reply-correction-target-context'])
    with pytest.raises(SystemExit) as error:
        probe.main()
    assert error.value.code == 2
    captured = {}
    def load(adapter, stop, **kwargs):
        captured['stop'] = stop
        return lambda *_args, **_kwargs: None
    def handler(generator, **kwargs):
        captured.update(kwargs)
        return object()
    class Server:
        def __init__(self, address, handler): pass
        def handle_request(self): captured['stop'].set()
        def server_close(self): captured['closed'] = True
    monkeypatch.setattr(probe, 'load_generator', load)
    monkeypatch.setattr(probe, 'make_handler', handler)
    monkeypatch.setattr(probe, 'ThreadingHTTPServer', Server)
    monkeypatch.setattr(probe.signal, 'signal', lambda *_args: None)
    monkeypatch.setenv('COCOLON_ANALYSIS_MODEL_API_KEY', 'synthetic-analysis-private-key')
    monkeypatch.setenv('EMLIS_NATURAL_REPLY_API_KEY', 'synthetic-natural-private-key')
    monkeypatch.setattr(sys, 'argv', ['serve','--model-name','analysis','--analysis-service',
        '--natural-reply-model','natural','--natural-reply-correction-target-context'])
    probe.main()
    assert captured['correction_target_context'] is True
    assert captured['natural_reply'] == dict(api_key='synthetic-natural-private-key',model_name='natural')
    assert captured['closed'] and captured['max_new_tokens'] == 4096 and captured['request_seconds'] == 210


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


@pytest.mark.parametrize('configured,expected_profile', [
    (probe.EVENT_PLAN_V2_MODEL, 'event_plan'), (probe.EVENT_PLAN_V2_BASE_MODEL, 'event_plan_base')])
def test_event_plan_v2_alias_keeps_authentication_profiles_and_shared_nine_call_limit(configured, expected_profile):
    calls = []
    def generate(messages, deadline, *, profile=None):
        calls.append((deepcopy(messages), profile))
        return 'unchanged synthetic raw', 'stop'
    server = ThreadingHTTPServer(('127.0.0.1', 0), probe.make_handler(generate,
        api_key='analysis-test-key', model_name='analysis', deadline=float('inf'), max_requests=9,
        max_new_tokens=4096, request_seconds=210,
        natural_reply={'api_key':'natural-test-key', 'model_name':'natural'},
        event_plan_model=configured))
    worker = threading.Thread(target=server.serve_forever, daemon=True); worker.start()
    def messages(material):
        return [dict(role='system', content='same synthetic instruction'),
            dict(role='user', content=json.dumps(material))]
    selected = messages(dict(model_schema=probe.EVENT_PLAN_V2_SCHEMA))
    ordinary = messages(dict(model_schema=probe.IF_CANDIDATE_SCHEMA))
    piece = messages(dict(core='piece', task='PIECE_MODEL_BODY', control=dict(field_slots={'memo_0':{}})))
    def packet(model, source=selected, *, tokens=4096, **extra):
        return dict(model=model, messages=source, max_tokens=tokens, temperature=0, stream=False,
            chat_template_kwargs={'enable_thinking':False}, **extra)
    try:
        with httpx.Client(trust_env=False, timeout=5) as client:
            url = f'http://127.0.0.1:{server.server_port}/v1/chat/completions'
            def post(payload, key='analysis-test-key'):
                return client.post(url, json=payload, headers={'Authorization':'Bearer ' + key})
            base = packet(configured)
            assert post(base, key='wrong-key').status_code == 401
            assert post(base, key='natural-test-key').status_code == 400
            for marker in (probe.EVENT_PLAN_SCHEMA, probe.IF_CANDIDATE_SCHEMA, None):
                assert post(packet(configured,
                    messages(dict(model_schema=marker)))).status_code == 400
            other_alias = (probe.EVENT_PLAN_V2_MODEL if configured == probe.EVENT_PLAN_V2_BASE_MODEL
                else probe.EVENT_PLAN_V2_BASE_MODEL)
            assert post(packet(other_alias)).status_code == 400
            assert post(packet('analysis')).status_code == 400
            assert post({**base, 'max_tokens':2048}).status_code == 400
            assert not calls
            routes = [
                (packet('analysis', ordinary), 'analysis-test-key', ordinary, None),
                (packet('natural', ordinary, tokens=2048), 'natural-test-key', ordinary, 'natural'),
                (packet('natural', piece, tokens=2048, candidate_format=probe.PIECE_CANDIDATE_FORMAT),
                    'natural-test-key', piece, 'piece'),
                (base, 'analysis-test-key', selected, expected_profile),
            ]
            routes += [(base, 'analysis-test-key', selected, expected_profile)] * 5
            for payload, key, source, profile in routes:
                result = post(payload, key)
                assert result.status_code == 200 and result.json()['model'] == payload['model']
                assert result.json()['choices'][0]['message']['content'] == 'unchanged synthetic raw'
            assert calls == [(source, profile) for _, _, source, profile in routes]
            for payload in (base, packet('analysis', ordinary)):
                assert post(payload).status_code == 429
            assert len(calls) == 9
    finally:
        server.shutdown(); server.server_close(); worker.join(3)


@pytest.mark.parametrize('configured', [None, 'cocolon-qwen3.5-4b-analysis-event-plan-v1', probe.EVENT_PLAN_V2_MODEL])
def test_event_plan_base_alias_requires_its_explicit_configuration(configured):
    server = ThreadingHTTPServer(('127.0.0.1', 0), probe.make_handler(
        lambda *_args, **_kwargs: pytest.fail('unconfigured base profile must not generate'),
        api_key='analysis-test-key', model_name='analysis', deadline=float('inf'), max_requests=9,
        max_new_tokens=4096, event_plan_model=configured))
    worker = threading.Thread(target=server.serve_forever, daemon=True); worker.start()
    try:
        result = httpx.post(f'http://127.0.0.1:{server.server_port}/v1/chat/completions', trust_env=False,
            headers={'Authorization':'Bearer analysis-test-key'}, json=dict(model=probe.EVENT_PLAN_V2_BASE_MODEL,
                messages=[dict(role='system', content='same instruction'), dict(role='user',
                    content=json.dumps(dict(model_schema=probe.EVENT_PLAN_V2_SCHEMA)))],
                max_tokens=4096, temperature=0, stream=False, chat_template_kwargs={'enable_thinking':False}))
        assert result.status_code == 400
    finally:
        server.shutdown(); server.server_close(); worker.join(3)


@pytest.mark.parametrize('alias', [probe.EVENT_PLAN_V2_BASE_MODEL, probe.NODE_LOCAL_V3_BASE_MODEL])
def test_event_plan_base_cli_keeps_explicit_event_adapter_and_existing_budgets(monkeypatch, alias):
    captured = {}
    def load(adapter, stop, **options):
        captured.update(adapter=adapter, stop=stop, options=options)
        return object()
    def handler(generate, **options):
        captured['handler'] = options
        return object()
    class Server:
        def __init__(self, *_args): pass
        def handle_request(self): captured['stop'].set()
        def server_close(self): pass
    monkeypatch.setattr(probe, 'load_generator', load)
    monkeypatch.setattr(probe, 'make_handler', handler)
    monkeypatch.setattr(probe, 'ThreadingHTTPServer', Server)
    monkeypatch.setattr(probe.signal, 'signal', lambda *_args: None)
    monkeypatch.setenv('COCOLON_ANALYSIS_MODEL_API_KEY', 'synthetic-analysis-private-key')
    monkeypatch.setattr(sys, 'argv', ['serve', '--analysis-service', '--semantic-json',
        '--model-name', 'analysis', '--adapter', 'original-120u',
        '--adapter-weights-sha256', 'a' * 64, '--adapter-config-sha256', 'b' * 64,
        '--context-tokens', '32768', '--event-plan-model', alias,
        '--event-plan-adapter', 'same-event-34u', '--event-plan-adapter-weights-sha256', 'c' * 64,
        '--event-plan-adapter-config-sha256', 'd' * 64])
    probe.main()
    assert captured['adapter'] == 'original-120u'
    assert captured['options'] == dict(weights_sha256='a' * 64, config_sha256='b' * 64,
        max_new_tokens=4096, context_tokens=32768, semantic_json=True,
        event_plan_adapter='same-event-34u', event_plan_weights_sha256='c' * 64,
        event_plan_config_sha256='d' * 64)
    assert captured['handler']['event_plan_model'] == alias
    assert captured['handler']['model_name'] == 'analysis'


@pytest.mark.parametrize('constrained', [False, True])
def test_event_plan_base_without_loaded_event_adapter_never_falls_back(monkeypatch, constrained):
    from test_piece_model_server_constraints import synthetic_generator
    generate, captured, _, _ = synthetic_generator(monkeypatch, constrained=constrained)
    with pytest.raises(ValueError, match='event_plan_adapter_unavailable'):
        generate([], time.monotonic() + 210, profile='event_plan_base')
    assert captured == {'generate':[], 'tokenize':[]}


def test_qwen_9b_requires_all_pinned_aliases_and_no_legacy_adapter(monkeypatch):
    command = ['serve', '--qwen-9b', '--analysis-service', '--semantic-json',
        '--model-name', probe.QWEN_9B_ANALYSIS_ALIAS, '--natural-reply-model', probe.QWEN_9B_NATURAL_ALIAS,
        '--event-plan-model', probe.OCCURRENCE_V24_9B_MODEL, '--bind', '127.0.0.1']
    captured = {}

    def load(adapter, stop, **options):
        captured.update(adapter=adapter, stop=stop, options=options)
        return object()

    class Server:
        def __init__(self, address, handler):
            captured['address'] = address

        def handle_request(self):
            captured['stop'].set()

        def server_close(self):
            pass

    monkeypatch.setattr(probe, 'load_generator', load)
    monkeypatch.setattr(probe, 'ThreadingHTTPServer', Server)
    monkeypatch.setattr(probe.signal, 'signal', lambda *_args: None)
    monkeypatch.setenv('COCOLON_ANALYSIS_MODEL_API_KEY', 'synthetic-analysis-private-key')
    monkeypatch.setenv('EMLIS_NATURAL_REPLY_API_KEY', 'synthetic-natural-private-key')

    for invalid in (command + ['--event-plan-adapter', 'legacy-adapter'],
                    [part for part in command if part != '--qwen-9b'],
                    [probe.OCCURRENCE_V24_MODEL if part == probe.OCCURRENCE_V24_9B_MODEL else part
                     for part in command]):
        monkeypatch.setattr(sys, 'argv', invalid)
        with pytest.raises(SystemExit) as error:
            probe.main()
        assert error.value.code == 2 and not captured

    monkeypatch.setattr(sys, 'argv', command)
    probe.main()
    assert captured['adapter'] is None
    assert captured['options'] == dict(qwen_9b=True, semantic_json=True,
                                      context_tokens=16384, max_new_tokens=4096)
    assert captured['address'] == ('127.0.0.1', 8000)


def _event_plan_comparison_generator(monkeypatch, *, input_count, node_local=False):
    """Reuse the existing CPU loader stand-in and the real serving/LMFE closure."""
    from test_piece_model_server_constraints import synthetic_generator
    if node_local:
        from test_analysis_node_local_native_profile import messages, packet as node_local_packet
        selected, packet = messages(), node_local_packet()
    else:
        from test_analysis_semantic_event_plan_v2 import authored_lesson
        prepared, packet = authored_lesson()
        selected = prepared.messages()
    raw = json.dumps(packet, ensure_ascii=False, separators=(',', ':'))
    original_loader = probe.load_generator
    event_loads = []
    def load(adapter, stop, **kwargs):
        original_adapter_loader = probe.load_piece_adapter
        def load_named(model, path, **options):
            if options.get('adapter_name') == probe.EVENT_PLAN_ADAPTER_NAME:
                event_loads.append((path, options['weights_sha256'], options['config_sha256']))
                assert path == 'event-plan-cpu'
                options.pop('adapter_name')
                # Existing fixture checks the same structural config and frozen weights.
                return original_adapter_loader(model, 'piece-cpu', **options)
            return original_adapter_loader(model, path, **options)
        monkeypatch.setattr(probe, 'load_piece_adapter', load_named)
        return original_loader(adapter, stop, **{**kwargs, 'context_tokens':32768,
            'event_plan_adapter':'event-plan-cpu', 'event_plan_weights_sha256':'c' * 64,
            'event_plan_config_sha256':'d' * 64})
    monkeypatch.setattr(probe, 'load_generator', load)
    generate, captured, _, eos = synthetic_generator(monkeypatch, constrained=True,
        input_count=input_count, with_piece_adapter=True, raw_output=raw)
    model = captured['model']
    original_select = model.set_adapter
    def select(name, *, inference_mode=False):
        if name == probe.EVENT_PLAN_ADAPTER_NAME:
            model.active_adapter, model.grads = name, not inference_mode
        else:
            original_select(name, inference_mode=inference_mode)
    monkeypatch.setattr(model, 'set_adapter', select)
    assert event_loads == [('event-plan-cpu', 'c' * 64, 'd' * 64)]
    return generate, captured, selected, raw, eos


@pytest.mark.parametrize('forward_failure', [False, True])
@pytest.mark.parametrize('node_local', [False, True])
def test_event_plan_base_real_loader_preserves_schema_budget_and_restores_all_adapters(monkeypatch, forward_failure, node_local):
    generate, captured, messages, raw, eos = _event_plan_comparison_generator(
        monkeypatch, input_count=28672, node_local=node_local)
    model = captured['model']
    if forward_failure:
        original_generate = model.generate
        def fail(**options):
            assert not model.adapter_enabled and model.active_adapter == 'default'
            assert options['max_new_tokens'] == 4096 and callable(options['prefix_allowed_tokens_fn'])
            raise RuntimeError('synthetic forward failure')
        monkeypatch.setattr(model, 'generate', fail)
        with pytest.raises(RuntimeError, match='synthetic forward failure'):
            generate(messages, time.monotonic() + 210, profile='event_plan_base')
        monkeypatch.setattr(model, 'generate', original_generate)
    else:
        assert generate(messages, time.monotonic() + 210, profile='event_plan_base') == (raw, 'stop')
        assert captured['adapter_states'] == [('default', False, False, False)]
        options = captured['generate'][0]
        assert options['max_new_tokens'] == 4096 and options['eos_token_id'] == eos
        assert options['do_sample'] is False and options['num_beams'] == 1 and options['use_cache'] is True
        assert captured['format_prefix'].token_enforcer.root_parser.config.force_json_field_order is True
        assert captured['tokenize'][0] == (messages, dict(enable_thinking=False,
            add_generation_prompt=True, tokenize=True, return_dict=True, return_tensors='pt', truncation=False))
    assert model.adapter_enabled and model.active_adapter == 'default'
    assert model.training is False and model.grads is False
    # The same closure and loaded event adapter still serve the original alias afterwards.
    assert generate(messages, time.monotonic() + 210, profile='event_plan') == (raw, 'stop')
    assert captured['adapter_states'][-1] == ('event_plan', True, False, False)
    assert model.adapter_enabled and model.active_adapter == 'default'
    assert model.training is False and model.grads is False


def test_event_plan_base_cannot_exceed_existing_32768_context(monkeypatch):
    generate, captured, messages, _, _ = _event_plan_comparison_generator(monkeypatch, input_count=28673)
    with pytest.raises(ValueError, match='context_or_deadline_exceeded'):
        generate(messages, time.monotonic() + 210, profile='event_plan_base')
    assert captured['generate'] == [] and captured['adapter_states'] == []
    assert captured['model'].adapter_enabled and captured['model'].active_adapter == 'default'


def _compact_merge_plan_for_context_test():
    from analysis_merge_wire import compact_json, response_codec
    from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
    from test_analysis_merge_transport import source_merge
    from test_analysis_occurrence_v17_record_owners import packet

    notes = ['庭の箱を片づけた。', '集会で資料を配った。']
    stage = source_merge(notes)
    messages = core.semantic_node_local_v4_wire_messages(stage)
    codec = response_codec(messages)
    raw = compact_json(codec.encode(packet(stage, [[[(1, notes[0])]], [[(2, notes[1])]]])))
    return messages, raw


@pytest.mark.parametrize('count, expected', [(28672, 4096), (30814, 1954), (32768, None), (32769, None)])
def test_9b_compact_merge_plan_uses_only_available_context_and_reports_actual_tokens(monkeypatch, count, expected):
    from test_piece_model_server_constraints import synthetic_generator

    messages, raw = _compact_merge_plan_for_context_test()
    generate, captured, _, _ = synthetic_generator(monkeypatch, constrained=True, qwen_9b=True,
        context_tokens=32768, input_count=count, raw_output=raw)
    if expected is None:
        with pytest.raises(ValueError, match='context_or_deadline_exceeded'):
            generate(messages, time.monotonic() + 210, profile='event_plan', output_tokens=4096)
        assert captured['generate'] == []
        return
    text, finish, usage = generate(messages, time.monotonic() + 210, profile='event_plan', output_tokens=4096)
    assert (text, finish) == (raw, 'stop')
    assert captured['generate'][0]['max_new_tokens'] == expected
    assert captured['tokenize'][0][0] == messages
    assert captured['tokenize'][0][1]['truncation'] is False
    assert usage == dict(prompt_tokens=count, completion_tokens=len(raw) + 1, total_tokens=count + len(raw) + 1)


@pytest.mark.parametrize('kind, phase, compact', [
    ('LEAF', 'PLAN', False), ('WHOLE', 'PLAN', False), ('MERGE', 'PLAN', False),
    ('MERGE', 'NODES', True), ('MERGE', 'RELATIONS', True),
])
def test_9b_other_staged_routes_keep_the_full_requested_reservation(monkeypatch, kind, phase, compact):
    from analysis_merge_wire import compact_json, legacy_messages
    from test_piece_model_server_constraints import synthetic_generator

    messages, raw = _compact_merge_plan_for_context_test()
    if not compact:
        messages = legacy_messages(messages)
    user = json.loads(messages[1]['content'])
    user['history_stage']['kind'], user['author_phase'] = kind, phase
    messages[1]['content'] = compact_json(user)
    generate, captured, _, _ = synthetic_generator(monkeypatch, constrained=True, qwen_9b=True,
        context_tokens=32768, input_count=30814, raw_output=raw)
    with pytest.raises(ValueError, match='context_or_deadline_exceeded'):
        generate(messages, time.monotonic() + 210, profile='event_plan', output_tokens=4096)
    assert captured['generate'] == []
