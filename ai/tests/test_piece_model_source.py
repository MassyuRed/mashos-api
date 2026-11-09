"""Shared 4B transport with synthetic HTTP, without GPU or external requests."""
import asyncio
from copy import deepcopy
from dataclasses import replace
import hashlib
import json

import httpx
import pytest

import piece_model_source as sources
from cocolon_meaning_experience_engine.preparation import PreparedRequest

ENDPOINT = 'https://synthetic-shared.invalid/private/v1/chat/completions'
MODEL = 'synthetic-shared-base-4b'
KEY = 'synthetic-existing-private-key-32'
run = asyncio.run


def prepared(*, refined=False):
    from cocolon_meaning_experience_engine.piece_semantic_admission import prepare_piece_model_request
    from cocolon_meaning_experience_engine.piece_v1c import PieceGenerationRequest
    from test_cmee_piece_refined_sources import source, request
    selected = source()
    value = request(selected) if refined else PieceGenerationRequest('transport-original',
        selected.original, selected.original.owner_id, selected.original.saved_input_id,
        selected.original.source_version)
    return prepare_piece_model_request(value)


def raw_for(value):
    count = len(value.payload()['control']['block_partition'])
    return json.dumps({'field_blocks': dict(zip(('memo_0', 'answer_text_private_1')[:count],
        ['私は、陶芸を選びたい。', '私は、考える時間を大切にしたい。'][:count], strict=True))}, ensure_ascii=False)


def packet(raw, *, finish='stop', **changes):
    value = {'model': MODEL, 'choices': [{'finish_reason': finish,
        'message': {'role': 'assistant', 'content': raw}}]}
    value.update(changes)
    return value


def source(handler):
    return sources.Shared4BPieceModelSource(endpoint=ENDPOINT, model=MODEL,
        api_key=KEY, transport=httpx.MockTransport(handler))


def environment(monkeypatch):
    values = {'PIECE_MODEL_SOURCE': sources.SELECTOR,
        'EMLIS_NATURAL_REPLY_ENDPOINT': ENDPOINT,
        'EMLIS_NATURAL_REPLY_MODEL': MODEL, 'EMLIS_NATURAL_REPLY_API_KEY': KEY}
    for name, value in values.items():
        monkeypatch.setenv(name, value)
    return values


@pytest.mark.parametrize('refined', [False, True], ids=['original', 'separate-answer'])
def test_one_shared_base_request_keeps_complete_material_and_unadopted_raw(refined):
    value = prepared(refined=refined)
    original = deepcopy(value.payload())
    raw = raw_for(value)
    calls = []

    def handler(request):
        calls.append(request)
        body = json.loads(request.content)
        assert request.method == 'POST' and str(request.url) == ENDPOINT
        assert request.headers['authorization'] == 'Bearer ' + KEY
        assert request.headers['content-type'] == 'application/json'
        assert request.headers['accept-encoding'] == 'identity'
        assert len(request.content) <= 65536
        assert set(body) == {'model', 'messages', 'temperature', 'max_tokens', 'stream',
                             'chat_template_kwargs'}
        assert {key: body[key] for key in ('model', 'temperature', 'max_tokens', 'stream',
            'chat_template_kwargs')} == dict(model=MODEL, temperature=0, max_tokens=2048,
                stream=False, chat_template_kwargs={'enable_thinking': False})
        assert [message['role'] for message in body['messages']] == ['system', 'user']
        material = json.loads(body['messages'][1]['content'])
        slots = material['control'].pop('field_slots')
        assert set(slots) == ({'memo_0', 'answer_text_private_1'} if refined else {'memo_0'})
        assert slots['memo_0']['literal'] == '私が選びたいのは、陶芸です。'
        if refined:
            assert slots['answer_text_private_1']['source_role'] == 'SUPPLEMENTAL_ANSWER'
            assert slots['answer_text_private_1']['literal'] == '私は考える時間を大切にしたい。'
        assert material == original
        assert set(material['sources'][0]['original']) == {'id', 'created_at', 'memo',
            'memo_action', 'category', 'emotions', 'emotion_details'}
        assert [item['role'] for item in material['sources']] == (
            ['ORIGINAL_INPUT', 'SUPPLEMENTAL_ANSWER'] if refined else ['ORIGINAL_INPUT'])
        assert '私は、陶芸を選びたい。' not in str(body['messages'])
        if refined:
            assert material['sources'][1]['text_fields']['answer_text_private'] == '私は考える時間を大切にしたい。'
            assert material['sources'][0]['original']['memo'] == '私が選びたいのは、陶芸です。'
        return httpx.Response(200, json=packet(raw))

    receipt = run(source(handler)(value))
    assert len(calls) == 1
    assert receipt.request_id == value.request_id
    assert receipt.raw_output == raw
    assert receipt.status == 'CANDIDATE_UNREVIEWED'
    assert json.loads(receipt.candidate_json) == {'body_blocks':
        ['私は、陶芸を選びたい。', '私は、考える時間を大切にしたい。'][:len(original['control']['block_partition'])]}
    assert receipt.adoption_state == 'NOT_ADOPTED'
    metadata = json.loads(receipt.metadata_json)
    assert metadata['model'] == MODEL and metadata['provider'] == sources.PROVIDER
    assert metadata['revision'] is None and metadata['usage'] is None
    assert metadata['evidence_check'] == 'BODY_UNREVIEWED_NOT_SEMANTIC_ADMISSION'
    assert metadata['candidate_format'] == 'piece.field_slots.v1'
    assert value.payload() == original


@pytest.mark.parametrize('mutation', [
    lambda p: p.update(model='other-model'),
    lambda p: p.update(choices=[]),
    lambda p: p['choices'].append(deepcopy(p['choices'][0])),
    lambda p: p['choices'][0]['message'].update(role='user'),
    lambda p: p['choices'][0]['message'].update(tool_calls=[{'id': 'tool'}]),
    lambda p: p['choices'][0]['message'].update(function_call={'name': 'tool'}),
    lambda p: p['choices'][0]['message'].update(reasoning_content='hidden reasoning'),
    lambda p: p['choices'][0]['message'].update(content=None),
    lambda p: p['choices'][0].update(finish_reason='tool_calls'),
    lambda p: p.update(usage={'total_tokens': -1}),
    lambda p: p.update(usage={'total_tokens': True}),
    lambda p: p.update(revision={}),
], ids=['model', 'empty', 'multiple', 'role', 'tools', 'function', 'reasoning', 'content',
        'finish', 'negative-usage', 'boolean-usage', 'revision'])
def test_provider_contract_failure_is_one_unadopted_error(mutation):
    value = prepared()
    response = packet(raw_for(value))
    mutation(response)
    calls = []

    def handler(request):
        calls.append(request)
        return httpx.Response(200, json=response)

    receipt = run(source(handler)(value))
    assert len(calls) == 1
    assert receipt.status == 'PROVIDER_ERROR' and receipt.candidate_json is None
    assert receipt.adoption_state == 'NOT_ADOPTED'


@pytest.mark.parametrize('raw', ['not JSON', '{"body_blocks":["ok"],"format_type":"quote"}',
    '{"body_blocks":["first"],"body_blocks":["second"]}'])
def test_invalid_candidate_is_retained_without_repair_or_fallback(raw):
    receipt = run(source(lambda request: httpx.Response(200, json=packet(raw)))(prepared()))
    assert receipt.raw_output == raw
    assert receipt.status == 'INVALID_FORMAT' and receipt.candidate_json is None


def test_length_finish_dominates_even_complete_candidate_json():
    value = prepared()
    raw = raw_for(value)
    receipt = run(source(lambda request: httpx.Response(200,
        json=packet(raw, finish='length')))(value))
    assert receipt.raw_output == raw and receipt.status == 'TOKEN_LIMIT'
    assert receipt.adoption_state == 'NOT_ADOPTED'


@pytest.mark.parametrize('status', [302, 401, 429, 503])
def test_non_success_status_never_redirects_or_retries(status):
    calls = []

    def handler(request):
        calls.append(str(request.url))
        return httpx.Response(status, headers={'Location': 'https://other.invalid/v1/chat/completions'})

    receipt = run(source(handler)(prepared()))
    assert receipt.status == 'PROVIDER_ERROR' and calls == [ENDPOINT]


@pytest.mark.parametrize('extra', [0, 1], ids=['exact-cap', 'one-byte-over'])
def test_streamed_response_byte_cap(extra):
    value = prepared()
    body = json.dumps(packet(raw_for(value)), ensure_ascii=False).encode('utf-8')
    body += b' ' * (sources.MAX_RESPONSE_BYTES + extra - len(body))

    class Chunks(httpx.AsyncByteStream):
        async def __aiter__(self):
            for start in range(0, len(body), 4096):
                yield body[start:start + 4096]

    receipt = run(source(lambda request: httpx.Response(200, stream=Chunks()))(value))
    assert receipt.status == ('PROVIDER_ERROR' if extra else 'CANDIDATE_UNREVIEWED')


def test_oversized_request_is_not_sent_or_shortened(monkeypatch):
    value = prepared(refined=True)
    before = value.private_json
    calls = []
    assert sources.MAX_REQUEST_BYTES == 65536
    monkeypatch.setattr(sources, 'MAX_REQUEST_BYTES', 1)
    receipt = run(source(lambda request: calls.append(request))(value))
    assert receipt.status == 'PROVIDER_ERROR' and calls == []
    assert value.private_json == before


def test_compressed_response_is_rejected_before_read_or_decompression():
    reads = []

    class Compressed(httpx.AsyncByteStream):
        async def __aiter__(self):
            reads.append(True)
            yield b'not-read-or-decompressed'

    receipt = run(source(lambda request: httpx.Response(200,
        headers={'Content-Encoding': 'gzip'}, stream=Compressed()))(prepared()))
    assert receipt.status == 'PROVIDER_ERROR' and reads == []


@pytest.mark.parametrize('kind', ['transport', 'total'])
def test_timeout_returns_one_timeout_receipt_without_retry(monkeypatch, kind):
    calls = []
    cancelled = []

    async def handler(request):
        calls.append(request)
        if kind == 'transport':
            raise httpx.ReadTimeout('synthetic private provider exception', request=request)
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            cancelled.append(True)
            raise

    if kind == 'total':
        monkeypatch.setattr(sources, 'REQUEST_SECONDS', 0.01)
    receipt = run(source(handler)(prepared()))
    assert receipt.status == 'TIMEOUT' and len(calls) == 1
    assert receipt.raw_output is None
    assert bool(cancelled) == (kind == 'total')
    assert 'synthetic private provider exception' not in receipt.metadata_json


def test_caller_cancellation_propagates_without_retry():
    calls = []

    async def handler(request):
        calls.append(request)
        raise asyncio.CancelledError

    with pytest.raises(asyncio.CancelledError):
        run(source(handler)(prepared()))
    assert len(calls) == 1


@pytest.mark.parametrize('endpoint', [
    'http://synthetic.invalid/v1/chat/completions',
    'https://user:private@synthetic.invalid/v1/chat/completions',
    ENDPOINT + '?query=1', ENDPOINT + '#fragment', ' ' + ENDPOINT,
    'https://synthetic.invalid:99999/v1/chat/completions',
    'https://synthetic.invalid/v1/other', 'https://synthetic.invalid\n/v1/chat/completions',
])
def test_endpoint_authority_cannot_be_rewritten(endpoint):
    with pytest.raises(ValueError, match='^piece_model_configuration_invalid$'):
        sources.Shared4BPieceModelSource(endpoint=endpoint, model=MODEL, api_key=KEY)


def test_transport_uses_tls_defaults_without_proxy_environment(monkeypatch):
    calls = []
    original = sources.httpx.AsyncClient

    def client(**kwargs):
        calls.append(kwargs)
        return original(**kwargs)

    monkeypatch.setattr(sources.httpx, 'AsyncClient', client)
    value = prepared()
    run(source(lambda request: httpx.Response(200, json=packet(raw_for(value))))(value))
    assert len(calls) == 1
    assert calls[0]['follow_redirects'] is False and calls[0]['trust_env'] is False
    assert 'verify' not in calls[0]  # httpx default certificate+hostname checks.
    assert calls[0]['timeout'].connect == 5.0 and calls[0]['timeout'].read == 240.0


@pytest.mark.parametrize('corruption', ['hash', 'task', 'core'])
def test_unbound_or_other_core_preparation_never_reaches_transport(corruption):
    value = prepared()
    if corruption == 'hash':
        value = replace(value, request_id='prep-wrong')
    else:
        material = value.payload()
        material[corruption] = 'emlis'
        raw = sources._json(material)
        value = PreparedRequest('prep-' + hashlib.sha256(raw.encode()).hexdigest(), raw)
    calls = []
    with pytest.raises(ValueError, match='^piece_model_prepared_invalid$'):
        run(source(lambda request: calls.append(request))(value))
    assert calls == []


def test_application_default_off_and_explicit_configuration_is_stable(monkeypatch):
    monkeypatch.delenv('PIECE_MODEL_SOURCE', raising=False)
    assert sources.application_piece_model_source() is None
    monkeypatch.setenv('PIECE_MODEL_SOURCE', 'off')
    assert sources.application_piece_model_source() is None
    environment(monkeypatch)
    first = sources.application_piece_model_source()
    assert first is sources.application_piece_model_source()
    sources.require_current_piece_model_source(first)


@pytest.mark.parametrize('when', ['before', 'after'])
@pytest.mark.parametrize('name', ['PIECE_MODEL_SOURCE', 'EMLIS_NATURAL_REPLY_ENDPOINT',
    'EMLIS_NATURAL_REPLY_MODEL', 'EMLIS_NATURAL_REPLY_API_KEY'])
def test_application_setting_change_fences_pending_source(monkeypatch, when, name):
    environment(monkeypatch)
    value = prepared()
    factory = sources.application_piece_model_source()
    calls = []

    class FakeSource:
        def __init__(self, **kwargs):
            assert kwargs == dict(endpoint=ENDPOINT, model=MODEL, api_key=KEY)

        async def __call__(self, item):
            calls.append(item)
            monkeypatch.setenv(name, 'changed-private-configuration')
            return object()

    monkeypatch.setattr(sources, 'Shared4BPieceModelSource', FakeSource)
    if when == 'before':
        monkeypatch.setenv(name, 'changed-private-configuration')
    with pytest.raises(RuntimeError, match='^piece_model_configuration_changed$'):
        run(factory(value))
    assert len(calls) == (when == 'after')


@pytest.mark.parametrize('setting', ['selector', 'missing-endpoint', 'missing-model', 'short-key'])
def test_enabled_bad_configuration_is_deferred_but_cannot_fall_back(monkeypatch, setting):
    environment(monkeypatch)
    name, value = {'selector': ('PIECE_MODEL_SOURCE', 'unknown'),
        'missing-endpoint': ('EMLIS_NATURAL_REPLY_ENDPOINT', ''),
        'missing-model': ('EMLIS_NATURAL_REPLY_MODEL', ''),
        'short-key': ('EMLIS_NATURAL_REPLY_API_KEY', 'short')}[setting]
    monkeypatch.setenv(name, value)
    factory = sources.application_piece_model_source()
    assert callable(factory)
    with pytest.raises(RuntimeError, match='^piece_model_configuration_invalid$'):
        run(factory(prepared()))
