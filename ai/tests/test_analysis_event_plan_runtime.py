"""Loopback/fake-adapter runtime boundaries, with no model or hosted service."""
from copy import deepcopy
import json
from http.server import ThreadingHTTPServer
import sys
import threading
import time

import httpx
import pytest

from test_emlis_natural_reply_probe_http import probe
from test_piece_model_server_constraints import adapter_loader_fixture

ALIAS = 'cocolon-qwen3.5-4b-analysis-event-plan-v1'


def messages(material=None):
    return [dict(role='system', content='synthetic runtime instruction'),
        dict(role='user', content='plain legacy input' if material is None else json.dumps(material))]


def packet(model, selected, tokens=4096):
    return dict(model=model, messages=selected, max_tokens=tokens, temperature=0,
        stream=False, chat_template_kwargs={'enable_thinking': False})


def server_for(generate, *, enabled=True, maximum=0):
    server = ThreadingHTTPServer(('127.0.0.1', 0), probe.make_handler(generate,
        api_key='analysis-test-key', model_name='analysis', deadline=float('inf'),
        max_requests=maximum, max_new_tokens=4096, request_seconds=210,
        natural_reply=dict(api_key='natural-test-key', model_name='natural'),
        event_plan_model=ALIAS if enabled else None))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def close(server, thread):
    server.shutdown()
    server.server_close()
    thread.join(3)


def test_explicit_alias_schema_and_analysis_key_route_once_after_invalid_requests():
    calls = []
    def generate(selected, end, *, profile=None):
        calls.append((deepcopy(selected), profile))
        assert 205 < end - time.monotonic() <= 210
        return 'synthetic-plan-raw', 'stop'
    server, thread = server_for(generate, maximum=1)
    try:
        url = f'http://127.0.0.1:{server.server_port}/v1/chat/completions'
        selected = messages(dict(model_schema=probe.EVENT_PLAN_SCHEMA))
        with httpx.Client(trust_env=False) as client:
            def post(value, key='analysis-test-key'):
                return client.post(url, headers={'Authorization':'Bearer ' + key}, json=value)
            invalid = [packet('analysis', selected), packet(ALIAS, messages()),
                packet(ALIAS, messages(dict(model_schema='cocolon.analysis.semantic_map.model.v2'))),
                packet(ALIAS, messages(dict(model_schema=probe.IF_CANDIDATE_SCHEMA)))]
            for value in invalid:
                assert post(value).status_code == 400
            assert post(packet(ALIAS, selected, 2048), key='natural-test-key').status_code == 400
            assert post(packet(ALIAS, selected), key='wrong-key').status_code == 401
            assert calls == []
            result = post(packet(ALIAS, selected))
            assert result.status_code == 200 and result.json()['model'] == ALIAS
            assert result.json()['choices'][0]['message']['content'] == 'synthetic-plan-raw'
            assert calls == [(selected, 'event_plan')]
            assert post(packet(ALIAS, selected)).status_code == 429
    finally:
        close(server, thread)


def test_optional_alias_absent_rejects_new_contract_and_preserves_plain_legacy_and_if_route():
    calls = []
    def generate(selected, end, *, profile=None):
        calls.append((deepcopy(selected), profile))
        return 'legacy-synthetic-raw', 'stop'
    server, thread = server_for(generate, enabled=False)
    try:
        url = f'http://127.0.0.1:{server.server_port}/v1/chat/completions'
        with httpx.Client(trust_env=False, headers={'Authorization':'Bearer analysis-test-key'}) as client:
            marked = messages(dict(model_schema=probe.EVENT_PLAN_SCHEMA))
            assert client.post(url, json=packet(ALIAS, marked)).status_code == 400
            assert client.post(url, json=packet('analysis', marked)).status_code == 400
            for selected in (messages(), messages(dict(model_schema=probe.IF_CANDIDATE_SCHEMA))):
                result = client.post(url, json=packet('analysis', selected))
                assert result.status_code == 200 and result.json()['model'] == 'analysis'
            assert calls == [(messages(), None), (messages(dict(model_schema=probe.IF_CANDIDATE_SCHEMA)), None)]
    finally:
        close(server, thread)


@pytest.mark.parametrize('alias', ['analysis', 'natural', '', ' ', 1, True])
def test_alias_collisions_and_invalid_configuration_are_rejected(alias):
    with pytest.raises(ValueError, match='event_plan_model_configuration_invalid'):
        probe.make_handler(lambda *_: pytest.fail('no generation'), api_key='analysis-test-key',
            model_name='analysis', deadline=float('inf'), max_requests=0,
            natural_reply=dict(api_key='natural-test-key', model_name='natural'), event_plan_model=alias)


class FakeModel:
    def __init__(self, failure=None):
        self.active_adapter = 'default'
        self.training, self.grads = True, True
        self.calls = []
        self.failure = failure
    def set_adapter(self, name, *, inference_mode):
        self.calls.append((name, inference_mode))
        if self.failure == name:
            raise RuntimeError('synthetic adapter selection failure')
        self.active_adapter = name
        self.grads = not inference_mode
    def eval(self):
        self.training = False
    def requires_grad_(self, value):
        self.grads = value


@pytest.mark.parametrize('body_failure', [False, True])
def test_event_plan_adapter_context_restores_original_default_after_success_or_failure(body_failure):
    model, stop = FakeModel(), threading.Event()
    def run():
        with probe.piece_inference_context(model, stop, adapter_name=probe.EVENT_PLAN_ADAPTER_NAME):
            assert model.active_adapter == probe.EVENT_PLAN_ADAPTER_NAME
            assert model.training is False and model.grads is False
            if body_failure:
                raise RuntimeError('synthetic forward failure')
    if body_failure:
        with pytest.raises(RuntimeError, match='synthetic forward failure'):
            run()
    else:
        run()
    assert model.active_adapter == 'default' and model.training is False and model.grads is False
    assert model.calls == [(probe.EVENT_PLAN_ADAPTER_NAME, True), ('default', True)]
    assert not stop.is_set()


def test_event_plan_selection_failure_restores_default_and_restore_failure_stops_serving():
    stop = threading.Event()
    model = FakeModel(failure=probe.EVENT_PLAN_ADAPTER_NAME)
    with pytest.raises(RuntimeError):
        with probe.piece_inference_context(model, stop, adapter_name=probe.EVENT_PLAN_ADAPTER_NAME):
            pytest.fail('failed adapter cannot yield')
    assert model.active_adapter == 'default' and model.training is False and model.grads is False
    assert not stop.is_set()
    model = FakeModel(failure='default')
    with pytest.raises(RuntimeError):
        with probe.piece_inference_context(model, stop, adapter_name=probe.EVENT_PLAN_ADAPTER_NAME):
            assert model.active_adapter == probe.EVENT_PLAN_ADAPTER_NAME
    assert stop.is_set()


def test_default_piece_context_keeps_existing_piece_name_and_refuses_wrong_initial_adapter():
    model, stop = FakeModel(), threading.Event()
    with probe.piece_inference_context(model, stop):
        assert model.active_adapter == probe.PIECE_ADAPTER_NAME
    assert model.calls == [(probe.PIECE_ADAPTER_NAME, True), ('default', True)]
    model.active_adapter = probe.EVENT_PLAN_ADAPTER_NAME
    with pytest.raises(ValueError, match='piece_adapter_state_invalid'):
        with probe.piece_inference_context(model, stop, adapter_name=probe.EVENT_PLAN_ADAPTER_NAME):
            pytest.fail('wrong initial adapter cannot yield')


def test_named_adapter_loader_uses_event_plan_state_and_does_not_replace_default_or_piece(monkeypatch, tmp_path):
    load, model, _, states, expected = adapter_loader_fixture(monkeypatch, tmp_path)
    states[probe.EVENT_PLAN_ADAPTER_NAME] = deepcopy(expected)
    before = deepcopy(states)
    load(adapter_name=probe.EVENT_PLAN_ADAPTER_NAME)
    assert model.loaded == [(tmp_path / 'piece', dict(adapter_name=probe.EVENT_PLAN_ADAPTER_NAME,
        is_trainable=False, local_files_only=True))]
    assert states == before and model.active_adapter == 'default'


def test_named_adapter_loader_rejects_changed_event_plan_weights(monkeypatch, tmp_path):
    load, _, _, states, expected = adapter_loader_fixture(monkeypatch, tmp_path)
    states[probe.EVENT_PLAN_ADAPTER_NAME] = {}
    with pytest.raises(ValueError, match='piece_adapter_loaded_weights_changed'):
        load(adapter_name=probe.EVENT_PLAN_ADAPTER_NAME)


@pytest.mark.parametrize('missing', ['--event-plan-model', '--event-plan-adapter',
    '--event-plan-adapter-weights-sha256', '--event-plan-adapter-config-sha256', None])
def test_cli_requires_complete_event_plan_identity_before_loader_and_preserves_original_adapter(monkeypatch, missing):
    base = ['probe', '--analysis-service', '--semantic-json', '--model-name', 'analysis',
        '--adapter', 'original-120u', '--adapter-weights-sha256', 'a' * 64,
        '--adapter-config-sha256', 'b' * 64]
    options = {'--event-plan-model': ALIAS, '--event-plan-adapter':'isolated-map-candidate',
        '--event-plan-adapter-weights-sha256':'c' * 64, '--event-plan-adapter-config-sha256':'d' * 64}
    if missing:
        options.pop(missing)
    argv = base + [part for item in options.items() for part in item]
    monkeypatch.setattr(sys, 'argv', argv)
    monkeypatch.setenv('COCOLON_ANALYSIS_MODEL_API_KEY', 'synthetic-analysis-key-at-least-24-chars')
    monkeypatch.setattr(probe.signal, 'signal', lambda *_: None)
    captured = []
    def loader(adapter, stop, **kwargs):
        captured.append((adapter, kwargs))
        raise RuntimeError('stop before any actual model load')
    monkeypatch.setattr(probe, 'load_generator', loader)
    if missing:
        with pytest.raises(SystemExit) as result:
            probe.main()
        assert result.value.code == 2 and captured == []
    else:
        with pytest.raises(RuntimeError, match='stop before any actual model load'):
            probe.main()
        assert captured == [('original-120u', dict(weights_sha256='a' * 64, config_sha256='b' * 64,
            max_new_tokens=4096, context_tokens=16384, semantic_json=True,
            event_plan_adapter='isolated-map-candidate', event_plan_weights_sha256='c' * 64,
            event_plan_config_sha256='d' * 64))]
