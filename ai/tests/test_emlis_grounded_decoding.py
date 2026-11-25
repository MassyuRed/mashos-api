"""Versioned Emlis decoder transport, independent of product text quality."""

from copy import deepcopy
from http.server import ThreadingHTTPServer
import json
import threading
import time

import httpx
import pytest

import emlis_thread_store
from cocolon_meaning_experience_engine import grounded_observation_reply as grounded
from cocolon_meaning_experience_engine.natural_reply import SelfHostedNaturalReplySource
from test_emlis_natural_reply_application import _active_application_owner, natural_case
from test_emlis_natural_reply_probe_http import probe
from test_emlis_q2_application import run
from test_emlis_q3_application import qdb
from test_piece_model_server_constraints import messages as piece_messages, synthetic_generator


QWEN = probe.QWEN_9B_NATURAL_ALIAS
FORMAT = grounded.CONSTRAINED_CANDIDATE_FORMAT
MEMO = '紙の見本帳にあった細い青い縞が好きでした。'
FOLLOW = '青い縞に目を留めたお話を分けてくださって、Emlisは嬉しいです。'


def _messages(*, multi=False):
    passages = [{'id': 'P1', 'text': MEMO, 'field': 'memo', 'source_role': 'ORIGINAL_INPUT'}]
    if multi:
        passages.append({'id': 'P2', 'text': '受付で見本帳を返しました。', 'field': 'memo_action',
                         'source_role': 'ORIGINAL_INPUT'})
    return grounded.messages({'records': [{'scope': 'CURRENT_INPUT'}], 'grounded_passages': passages,
                              'user_frame_feedback': []})


def _accepts(messages, text):
    parser = probe.emlis_grounded_json_parser(messages, ''.join(dict.fromkeys(text)))
    for char in text:
        if char not in parser.get_allowed_characters():
            return False
        parser = parser.add_character(char)
    return parser.can_end()


def test_pinned_parser_requires_the_exact_reply_envelope_and_list_limits():
    bound, multi = _messages(), _messages(multi=True)
    valid = json.dumps({'follow': FOLLOW}, ensure_ascii=False)
    assert _accepts(bound, valid)
    assert not _accepts(bound, FOLLOW)
    assert not _accepts(bound, '{"follow":""}')
    assert not _accepts(bound, json.dumps({'follow': 'あ' * 241}, ensure_ascii=False))
    assert not _accepts(bound, '{"follow":"返事","extra":"余分"}')
    for ids, accepted in [(['P1'], True), (['P2', 'P1'], True), ([], False),
                          (['P3'], False), (['P1', 'P2', 'P1'], False)]:
        output = json.dumps({'passages': ids, 'follow': FOLLOW}, ensure_ascii=False)
        assert _accepts(multi, output) == accepted
        assert not _accepts(bound, output)
    assert not _accepts(multi, valid)
    # The receiver still independently rejects embedded quotes and duplicate IDs.
    assert _accepts(bound, '{"follow":"「引用」"}')
    assert _accepts(multi, '{"passages":["P1","P1"],"follow":"返事"}')


@pytest.mark.parametrize('multi', [False, True])
def test_real_serving_mask_and_budget_with_deterministic_cpu_forward(monkeypatch, multi):
    selected = _messages(multi=multi)
    packet = {'passages': ['P2']} if multi else {}
    raw = json.dumps({**packet, 'follow': FOLLOW}, ensure_ascii=False)
    generator, capture, _, eos = synthetic_generator(monkeypatch, constrained=True, raw_output=raw, qwen_9b=True)
    assert generator(selected, time.monotonic() + 23, profile='emlis_grounded') == (raw, 'stop')
    options, = capture['generate']
    assert options['max_new_tokens'] == 2048 and options['eos_token_id'] == eos
    assert options['do_sample'] is False and options['num_beams'] == 1
    assert 'logits_processor' not in options
    assert callable(options['prefix_allowed_tokens_fn'])
    assert capture['format_prefix'].token_enforcer.root_parser.config.force_json_field_order is True


@pytest.mark.parametrize('qwen,constrained', [(True, False), (False, True)])
def test_grounded_profile_never_falls_back_to_unconstrained_generation(monkeypatch, qwen, constrained):
    generator, capture, _, _ = synthetic_generator(monkeypatch, constrained=constrained, qwen_9b=qwen)
    with pytest.raises(ValueError, match='emlis_grounded_constraint_unavailable'):
        generator(_messages(), time.monotonic() + 23, profile='emlis_grounded')
    assert capture == {'generate': [], 'tokenize': []}


def test_authenticated_marker_is_distinct_from_ordinary_natural_piece_and_analysis():
    calls = []

    def generate(messages, deadline, *, profile=None):
        calls.append((deepcopy(messages), profile))
        if messages[0]['content'] == 'fail only this model call':
            raise ValueError('synthetic parser failure')
        return 'unchanged synthetic raw', 'stop'

    server = ThreadingHTTPServer(('127.0.0.1', 0), probe.make_handler(
        generate, api_key='analysis-test-key', model_name=probe.QWEN_9B_ANALYSIS_ALIAS,
        deadline=float('inf'), max_requests=0, max_new_tokens=4096,
        natural_reply={'api_key': 'natural-test-key', 'model_name': QWEN}))
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    url = f'http://127.0.0.1:{server.server_port}/v1/chat/completions'
    valid = dict(model=QWEN, messages=_messages(), max_tokens=2048, temperature=0, stream=False,
                 chat_template_kwargs={'enable_thinking': False}, candidate_format=FORMAT)
    try:
        with httpx.Client(trust_env=False, timeout=5) as client:
            def post(body, key='natural-test-key'):
                return client.post(url, json=body, headers={'Authorization': 'Bearer ' + key})

            assert post(valid, key='wrong-key').status_code == 401
            assert post({**valid, 'model': probe.QWEN_9B_ANALYSIS_ALIAS, 'max_tokens': 4096},
                        key='analysis-test-key').status_code == 400
            assert post({**valid, 'model': 'old-natural'}).status_code == 400
            assert post({**valid, 'candidate_format': 'emlis.unknown'}).status_code == 400
            assert post({**valid, 'candidate_format': None}).status_code == 400
            assert post({**valid, 'candidate_format': probe.PIECE_CANDIDATE_FORMAT}).status_code == 400
            assert post({**valid, 'messages': piece_messages()}).status_code == 400
            assert post({**valid, 'max_tokens': 1024}).status_code == 400
            bad = deepcopy(valid)
            material = json.loads(bad['messages'][1]['content'])
            material['passages'] = []
            bad['messages'][1]['content'] = json.dumps(material)
            assert post(bad).status_code == 400
            assert not calls

            selected = post(valid)
            assert selected.status_code == 200 and selected.json()['candidate_format'] == FORMAT
            ordinary = {key: value for key, value in valid.items() if key != 'candidate_format'}
            assert 'candidate_format' not in post(ordinary).json()
            piece = post({**ordinary, 'messages': piece_messages(),
                          'candidate_format': probe.PIECE_CANDIDATE_FORMAT})
            assert piece.status_code == 200 and piece.json()['candidate_format'] == probe.PIECE_CANDIDATE_FORMAT
            analysis = post({**ordinary, 'model': probe.QWEN_9B_ANALYSIS_ALIAS, 'max_tokens': 4096},
                            key='analysis-test-key')
            assert analysis.status_code == 200 and 'candidate_format' not in analysis.json()
            failure = deepcopy(valid)
            failure['messages'][0]['content'] = 'fail only this model call'
            assert post(failure).status_code == 503
            assert [profile for _, profile in calls] == [
                'emlis_grounded', 'natural', 'piece', None, 'emlis_grounded']
    finally:
        server.shutdown()
        server.server_close()
        worker.join(3)


@pytest.mark.parametrize('constrained', [False, True])
def test_v3_and_v4_receipts_keep_their_exact_messages_when_flag_changes(
        natural_case, qdb, monkeypatch, constrained):
    user, parent, _, _ = natural_case
    qdb.query("update public.emotions set memo=$2,memo_action='' where id=$1", [parent, MEMO])
    calls = []
    failed = False

    def infer(request):
        payload = json.loads(request.content)
        calls.append(payload)
        assert payload["messages"] == _messages_for_same_current_record(payload)
        assert payload.get('candidate_format') == (FORMAT if constrained else None)
        result = {'model': QWEN, 'choices': [{'finish_reason': 'stop',
            'message': {'role': 'assistant', 'content': json.dumps({'follow': FOLLOW}, ensure_ascii=False)}}]}
        if constrained:
            result['candidate_format'] = FORMAT
        return httpx.Response(200, json=result)

    async def rpc(name, payload, **kwargs):
        nonlocal failed
        if not failed and any(event["kind"] == "OBSERVATION" for event in payload.get("p_events", [])):
            failed = True
            return httpx.Response(503, json={"code": "57P03"})
        return await qdb.rpc(name, payload, **kwargs)

    monkeypatch.setattr(emlis_thread_store, "sb_post_rpc", rpc)
    monkeypatch.setenv("COCOLON_EMLIS_GROUNDED_OBSERVATION", "true")
    monkeypatch.setenv("COCOLON_EMLIS_GROUNDED_DECODING", "true" if constrained else "")
    source = SelfHostedNaturalReplySource(endpoint='https://model.invalid/v1/chat/completions',
        model=QWEN, api_key='synthetic-only', transport=httpx.MockTransport(infer))
    service = _active_application_owner(monkeypatch, source, None)
    failed_reply = run(service.start(user, parent))
    assert failed_reply["can_retry"] and failed_reply["current_observation"] is None
    before = run(service.store.read(user, input_id=parent))
    receipt = next(event['payload'] for event in before['events']
                   if event['payload'].get('stage') == 'NATURAL_REPLY_RECEIVED')
    assert receipt['writer_context_version'] == (
        grounded.CONSTRAINED_CONTEXT_VERSION if constrained else grounded.CONTEXT_VERSION)

    monkeypatch.setenv("COCOLON_EMLIS_GROUNDED_DECODING", "" if constrained else "true")
    restarted = _active_application_owner(monkeypatch, source, None)
    saved = run(restarted.action(user, failed_reply['thread_id'], action='retry_response',
        expected_revision=failed_reply['revision'], idempotency_key='restore-received-reply',
        operation_id=failed_reply['operation_id']))
    assert saved['current_observation']['text'] == f'「{MEMO}」\n\n{FOLLOW}'
    reread = run(restarted.get(user, parent))
    assert reread['current_observation'] == saved['current_observation']
    assert reread['revision'] == saved['revision'] and len(calls) == 1


def _messages_for_same_current_record(payload):
    material = json.loads(payload["messages"][1]["content"])
    writer = {'records': [material['current']], 'user_frame_feedback': [],
              'grounded_passages': [{'id': 'P1', 'text': MEMO, 'field': 'memo',
                                    'source_role': 'ORIGINAL_INPUT'}],
              'source_context_version': grounded.CONTEXT_VERSION}
    return grounded.messages(writer)


@pytest.mark.parametrize('response_marker', [None, probe.PIECE_CANDIDATE_FORMAT, 'legacy_http_400'])
def test_client_rejects_unavailable_or_unconfirmed_decoder_with_one_call(
        natural_case, qdb, monkeypatch, response_marker):
    user, parent, _, _ = natural_case
    qdb.query("update public.emotions set memo=$2,memo_action='' where id=$1", [parent, MEMO])
    calls = []

    def infer(request):
        calls.append(json.loads(request.content))
        assert calls[-1]['candidate_format'] == FORMAT
        if response_marker == 'legacy_http_400':
            return httpx.Response(400, json={'error': 'request_invalid'})
        result = {'model': QWEN, 'choices': [{'finish_reason': 'stop',
            'message': {'role': 'assistant', 'content': json.dumps({'follow': FOLLOW}, ensure_ascii=False)}}]}
        if response_marker is not None:
            result['candidate_format'] = response_marker
        return httpx.Response(200, json=result)

    monkeypatch.setenv("COCOLON_EMLIS_GROUNDED_OBSERVATION", "true")
    monkeypatch.setenv("COCOLON_EMLIS_GROUNDED_DECODING", "true")
    source = SelfHostedNaturalReplySource(endpoint='https://model.invalid/v1/chat/completions',
        model=QWEN, api_key='synthetic-only', transport=httpx.MockTransport(infer))
    service = _active_application_owner(monkeypatch, source, None)
    reply = run(service.start(user, parent))
    assert reply['state'] == 'RESPONSE_FAILED' and not reply['can_retry']
    assert reply['current_observation'] is None
    assert run(service.get(user, parent))['current_observation'] is None
    assert len(calls) == 1
