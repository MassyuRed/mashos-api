"""Exact opt-in application alias routing; no hosted model or runtime activation."""
import asyncio
import json
from unittest.mock import AsyncMock

import httpx
import pytest

import analysis_model_source as sources
import analysis_semantic_map as application
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from test_analysis_semantic_map import OWNER, sample


ALIAS = 'cocolon-qwen3.5-4b-analysis-event-plan-v1'
ENDPOINT = 'https://synthetic-analysis.invalid/v1/chat/completions'
KEY = 'synthetic-local-test-key'


def environment(monkeypatch, model=ALIAS, selector=sources.SEMANTIC_SELECTOR):
    values = dict(COCOLON_ANALYSIS_MODEL_SOURCE=selector,
        COCOLON_ANALYSIS_MODEL_ENDPOINT=ENDPOINT, COCOLON_ANALYSIS_MODEL=model,
        COCOLON_ANALYSIS_MODEL_API_KEY=KEY)
    for name, value in values.items():
        monkeypatch.setenv(name, value)
    sources._configured_source.cache_clear()
    return tuple(values.values())


def test_exact_alias_selects_new_profile_with_existing_four_setting_identity(monkeypatch):
    settings = environment(monkeypatch)
    source = sources.application_analysis_model_source()
    assert sources._settings() == settings and len(settings) == 4
    assert type(source) is sources._ApplicationSemanticAnalysisSource
    assert sources.is_semantic_analysis_model_source(source)
    assert sources.analysis_model_prompt_version(source) == core.SEMANTIC_MAP_EVENT_PLAN_PROFILE
    assert source is sources.application_analysis_model_source()
    assert source._settings == settings


@pytest.mark.parametrize('model, profile, artifact_schema', [
    (sources.SEMANTIC_OCCURRENCE_V13_MODEL, core.SEMANTIC_MAP_OCCURRENCE_V13_PROFILE,
     core.SEMANTIC_MAP_OCCURRENCE_V13_SCHEMA),
    (sources.SEMANTIC_OCCURRENCE_V14_MODEL, core.SEMANTIC_MAP_OCCURRENCE_V14_PROFILE,
     core.SEMANTIC_MAP_OCCURRENCE_V14_SCHEMA),
    (sources.SEMANTIC_OCCURRENCE_V15_MODEL, core.SEMANTIC_MAP_OCCURRENCE_V15_PROFILE,
     core.SEMANTIC_MAP_OCCURRENCE_V15_SCHEMA),
    (sources.SEMANTIC_OCCURRENCE_V16_MODEL, core.SEMANTIC_MAP_OCCURRENCE_V16_PROFILE,
     core.SEMANTIC_MAP_OCCURRENCE_V16_SCHEMA),
    (sources.SEMANTIC_OCCURRENCE_V17_MODEL, core.SEMANTIC_MAP_OCCURRENCE_V17_PROFILE,
     core.SEMANTIC_MAP_OCCURRENCE_V17_SCHEMA),
    (sources.SEMANTIC_OCCURRENCE_V18_MODEL, core.SEMANTIC_MAP_OCCURRENCE_V18_PROFILE,
     core.SEMANTIC_MAP_OCCURRENCE_V18_SCHEMA),
])
def test_content_plan_alias_binds_version_for_generation_and_replay(monkeypatch, model, profile, artifact_schema):
    environment(monkeypatch, model)
    source = sources.application_analysis_model_source()
    assert sources.analysis_model_prompt_version(source) == profile
    prepared = application.prepare_semantic_map(OWNER, sample(), prompt_version=profile)
    assert core.semantic_node_local_v4_artifact_schema(prepared) == artifact_schema
    material = json.loads(prepared.messages()[1]['content'])
    assert material['author_profile'] == profile
    assert material['source_choices_sha256']


@pytest.mark.parametrize('alias', ['', 'synthetic-analysis-4b',
    'cocolon-qwen3.5-4b-analysis-semantic-120u', ALIAS.upper(), ALIAS + '-unknown', ' ' + ALIAS])
def test_old_default_unknown_and_near_matching_aliases_stay_legacy(alias, monkeypatch):
    environment(monkeypatch, model=alias)
    source = sources.application_analysis_model_source()
    assert sources.analysis_model_prompt_version(source) == core.SEMANTIC_MAP_PROFILE


@pytest.mark.parametrize('selector', ['', 'off'])
def test_alias_does_not_activate_disabled_application(selector, monkeypatch):
    settings = environment(monkeypatch, selector=selector)
    assert sources.application_analysis_model_source() is None
    assert sources._settings() == settings


def test_quotation_only_selector_keeps_its_existing_default_even_with_new_alias(monkeypatch):
    environment(monkeypatch, selector=sources.SELECTOR)
    source = sources.application_analysis_model_source()
    assert type(source) is sources._ApplicationAnalysisSource
    assert sources.analysis_model_prompt_version(source) == sources.DEFAULT_PROMPT_VERSION
    assert sources.analysis_model_prompt_version(AsyncMock()) == sources.DEFAULT_PROMPT_VERSION


def test_direct_constructor_default_is_legacy_and_explicit_profile_remains_supported():
    for model in (ALIAS, 'synthetic-existing-alias'):
        default = sources.SelfHostedSemanticAnalysisModelSource(endpoint=ENDPOINT, model=model, api_key=KEY)
        explicit = sources.SelfHostedSemanticAnalysisModelSource(endpoint=ENDPOINT, model=model, api_key=KEY,
            semantic_prompt_version=core.SEMANTIC_MAP_EVENT_PLAN_PROFILE)
        assert sources.analysis_model_prompt_version(default) == core.SEMANTIC_MAP_PROFILE
        assert sources.analysis_model_prompt_version(explicit) == core.SEMANTIC_MAP_EVENT_PLAN_PROFILE


def test_application_acquisition_sends_exact_alias_bound_messages_and_existing_wire_limits(monkeypatch):
    settings = environment(monkeypatch)
    source = sources.application_analysis_model_source()
    prepared = application.prepare_semantic_map(OWNER, sample(),
        prompt_version=sources.analysis_model_prompt_version(source))
    calls = []
    def receive(request):
        calls.append(request)
        return httpx.Response(200, json=dict(model=ALIAS, choices=[dict(finish_reason='stop',
            message=dict(role='assistant', content='transport-only synthetic raw'))]))
    original_client = httpx.AsyncClient
    monkeypatch.setattr(sources.httpx, 'AsyncClient', lambda **kwargs:
        original_client(**{**kwargs, 'transport': httpx.MockTransport(receive)}))
    receipt = asyncio.run(source(prepared))
    assert len(calls) == 1
    body = json.loads(calls[0].content)
    assert body == dict(model=ALIAS, messages=prepared.messages(), temperature=0,
        max_tokens=4096, stream=False, chat_template_kwargs={'enable_thinking': False})
    assert calls[0].headers['Authorization'] == 'Bearer ' + KEY
    assert receipt.raw == 'transport-only synthetic raw'
    assert receipt.request_ref == prepared.request_ref
    assert receipt.messages_sha256 == core.semantic_map_hash(prepared.messages())
    assert source._settings == sources._settings() == settings


def test_settings_change_is_rejected_before_acquisition_and_existing_identity_not_rebound(monkeypatch):
    environment(monkeypatch)
    source = sources.application_analysis_model_source()
    old_profile = sources.analysis_model_prompt_version(source)
    prepared = application.prepare_semantic_map(OWNER, sample(), prompt_version=old_profile)
    monkeypatch.setenv('COCOLON_ANALYSIS_MODEL', 'synthetic-analysis-4b')
    monkeypatch.setattr(sources.httpx, 'AsyncClient', lambda **kwargs:
        pytest.fail('changed source must not send any request'))
    with pytest.raises(RuntimeError, match='analysis_model_configuration_changed'):
        asyncio.run(source(prepared))
    assert sources.analysis_model_prompt_version(source) == old_profile
    assert sources.analysis_model_prompt_version(sources.application_analysis_model_source()) == core.SEMANTIC_MAP_PROFILE


def test_new_alias_cannot_acquire_a_legacy_prepared_request(monkeypatch):
    environment(monkeypatch)
    source = sources.application_analysis_model_source()
    prepared = application.prepare_semantic_map(OWNER, sample())
    monkeypatch.setattr(sources.httpx, 'AsyncClient', lambda **kwargs:
        pytest.fail('wrong prepared profile must not send any request'))
    with pytest.raises(ValueError, match='analysis_semantic_input_invalid'):
        asyncio.run(source(prepared))


def test_if_original_identity_matches_existing_current_4b_fixture():
    from pathlib import Path
    fixture = json.loads((Path(__file__).parent / 'fixtures/cmee_current_4b_packet_20261114.json').read_text())
    assert sources.SEMANTIC_EVENT_PLAN_BASE_MODEL == fixture['analysis_model']


@pytest.mark.parametrize('selector,alias,expected,budget', [
    (sources.SEMANTIC_SELECTOR, sources.SEMANTIC_OCCURRENCE_V14_MODEL, sources.SEMANTIC_EVENT_PLAN_BASE_MODEL, 4096),
    (sources.SEMANTIC_SELECTOR, sources.SEMANTIC_OCCURRENCE_V15_MODEL, sources.SEMANTIC_EVENT_PLAN_BASE_MODEL, 4096),
    (sources.SEMANTIC_SELECTOR, sources.SEMANTIC_OCCURRENCE_V16_MODEL, sources.SEMANTIC_EVENT_PLAN_BASE_MODEL, 4096),
    (sources.SEMANTIC_SELECTOR, sources.SEMANTIC_OCCURRENCE_V17_MODEL, sources.SEMANTIC_EVENT_PLAN_BASE_MODEL, 4096),
    (sources.SEMANTIC_SELECTOR, sources.SEMANTIC_OCCURRENCE_V18_MODEL, sources.SEMANTIC_EVENT_PLAN_BASE_MODEL, 4096),
    (sources.SEMANTIC_SELECTOR, sources.SEMANTIC_NODE_LOCAL_V4_BOUND_MODEL, sources.SEMANTIC_EVENT_PLAN_BASE_MODEL, 4096),
    (sources.SEMANTIC_SELECTOR, sources.SEMANTIC_NODE_LOCAL_V4_MODEL, sources.SEMANTIC_EVENT_PLAN_BASE_MODEL, 4096),
    (sources.SEMANTIC_SELECTOR, ALIAS, 'cocolon-qwen3.5-4b-analysis-semantic-120u', 4096),
    (sources.SEMANTIC_SELECTOR, ALIAS + '-unknown', ALIAS + '-unknown', 4096),
    (sources.SEMANTIC_SELECTOR, 'existing-analysis-4b', 'existing-analysis-4b', 4096),
    (sources.SELECTOR, ALIAS, ALIAS, 2048),
])
def test_if_factory_only_remaps_exact_semantic_candidate_and_retains_original_settings(selector, alias,
        expected, budget, monkeypatch):
    import analysis_if_model_source as if_source
    settings = environment(monkeypatch, model=alias, selector=selector)
    monkeypatch.setattr(if_source.httpx, 'AsyncClient', lambda **kwargs:
        pytest.fail('factory must not acquire any response'))
    source = if_source.application_analysis_if_model_source()
    assert source.model == expected
    assert source._max_tokens == budget
    assert source._settings_snapshot == settings == sources._settings()


def if_prepared():
    from test_analysis_if_routes import request, if_route
    return if_route.prepare_if_model_request(request(count=2, legacy=True))


@pytest.mark.parametrize('map_alias', [ALIAS, sources.SEMANTIC_NODE_LOCAL_V4_MODEL,
    sources.SEMANTIC_NODE_LOCAL_V4_BOUND_MODEL, sources.SEMANTIC_OCCURRENCE_V11_MODEL])
def test_if_wire_uses_original_120u_under_map_candidate_and_native_does_not_switch_adapter(monkeypatch, map_alias):
    from io import BytesIO
    from types import SimpleNamespace
    import time
    import analysis_if_model_source as if_source
    from test_emlis_natural_reply_probe_http import probe
    from test_analysis_if_routes import packet as if_packet
    settings = environment(monkeypatch, model=map_alias)
    source = if_source.application_analysis_if_model_source()
    prepared = if_prepared()
    authored = json.dumps(if_packet(prepared), ensure_ascii=False)
    calls, native_profiles = [], []
    def generate(messages, end, *, profile=None):
        native_profiles.append(profile)
        assert messages == prepared.messages()
        return authored, 'stop'
    handler_type = probe.make_handler(generate, api_key=KEY,
        model_name=sources.SEMANTIC_EVENT_PLAN_BASE_MODEL, event_plan_model=map_alias,
        deadline=time.monotonic() + 30, max_requests=1, max_new_tokens=4096)
    def receive(request):
        body = json.loads(request.content)
        calls.append(body)
        assert body == dict(model=sources.SEMANTIC_EVENT_PLAN_BASE_MODEL,
            messages=prepared.messages(), temperature=0, max_tokens=4096,
            stream=False, chat_template_kwargs={'enable_thinking':False})
        handler = handler_type.__new__(handler_type)
        handler.path = '/v1/chat/completions'
        handler.headers = dict(request.headers)
        handler.headers['Content-Length'] = str(len(request.content))
        handler.headers['Authorization'] = request.headers['authorization']
        handler.rfile = BytesIO(request.content)
        handler.connection = SimpleNamespace(settimeout=lambda seconds: None)
        captured = []
        handler.reply = lambda status, value: captured.append((status, value))
        handler.do_POST()
        status, value = captured[0]
        return httpx.Response(status, json=value)
    source._transport = httpx.MockTransport(receive)
    receipt = asyncio.run(source(prepared))
    assert len(calls) == 1 and native_profiles == [None]
    assert receipt.raw == authored
    assert receipt.messages_sha256 == core.semantic_map_hash(prepared.messages())
    assert receipt.request_ref == prepared.request_ref
    assert source._settings_snapshot == settings == sources._settings()


def test_if_candidate_remap_still_rejects_configuration_changes_before_request(monkeypatch):
    import analysis_if_model_source as if_source
    environment(monkeypatch)
    source = if_source.application_analysis_if_model_source()
    prepared = if_prepared()
    monkeypatch.setenv('COCOLON_ANALYSIS_MODEL', 'existing-analysis-4b')
    monkeypatch.setattr(if_source.httpx, 'AsyncClient', lambda **kwargs:
        pytest.fail('changed configuration must not acquire IF response'))
    with pytest.raises(RuntimeError, match='analysis_if_model_configuration_changed'):
        asyncio.run(source(prepared))

