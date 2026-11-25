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
from test_emlis_natural_reply_application import _active_application_owner, _piece_adapter, natural_case
from test_emlis_natural_reply_probe_http import probe
from test_emlis_q2_application import answer, run
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


@pytest.mark.parametrize('version', [grounded.CONTEXT_VERSION, grounded.CONSTRAINED_CONTEXT_VERSION,
                                     grounded.SEMANTIC_CONTEXT_VERSION, grounded.LISTENER_CONTEXT_VERSION])
def test_grounded_receipts_keep_their_exact_messages_when_flag_changes(
        natural_case, qdb, monkeypatch, version):
    user, parent, _, _ = natural_case
    qdb.query("update public.emotions set memo=$2,memo_action='' where id=$1", [parent, MEMO])
    calls = []
    failed = False
    constrained = version in grounded.CONSTRAINED_CONTEXT_VERSIONS

    def infer(request):
        payload = json.loads(request.content)
        calls.append(payload)
        assert payload["messages"] == _messages_for_same_current_record(payload, version)
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
    monkeypatch.setenv("COCOLON_EMLIS_GROUNDED_SEMANTICS",
                       "true" if version in grounded.SEMANTIC_CONTEXT_VERSIONS else "")
    monkeypatch.setenv("COCOLON_EMLIS_GROUNDED_LISTENER", "true" if version == grounded.LISTENER_CONTEXT_VERSION else "")
    source = SelfHostedNaturalReplySource(endpoint='https://model.invalid/v1/chat/completions',
        model=QWEN, api_key='synthetic-only', transport=httpx.MockTransport(infer))
    service = _active_application_owner(monkeypatch, source, None)
    failed_reply = run(service.start(user, parent))
    assert failed_reply["can_retry"] and failed_reply["current_observation"] is None
    before = run(service.store.read(user, input_id=parent))
    receipt = next(event['payload'] for event in before['events']
                   if event['payload'].get('stage') == 'NATURAL_REPLY_RECEIVED')
    assert receipt['writer_context_version'] == version

    monkeypatch.setenv("COCOLON_EMLIS_GROUNDED_DECODING", "" if constrained else "true")
    monkeypatch.setenv("COCOLON_EMLIS_GROUNDED_SEMANTICS", "" if version in grounded.SEMANTIC_CONTEXT_VERSIONS else "true")
    monkeypatch.setenv("COCOLON_EMLIS_GROUNDED_LISTENER", "")
    restarted = _active_application_owner(monkeypatch, source, None)
    saved = run(restarted.action(user, failed_reply['thread_id'], action='retry_response',
        expected_revision=failed_reply['revision'], idempotency_key='restore-received-reply',
        operation_id=failed_reply['operation_id']))
    assert saved['current_observation']['text'] == f'「{MEMO}」\n\n{FOLLOW}'
    reread = run(restarted.get(user, parent))
    assert reread['current_observation'] == saved['current_observation']
    assert reread['revision'] == saved['revision'] and len(calls) == 1


def _messages_for_same_current_record(payload, version):
    material = json.loads(payload["messages"][1]["content"])
    writer = {'records': [material['current']], 'user_frame_feedback': [],
              'grounded_passages': [{'id': 'P1', 'text': MEMO, 'field': 'memo',
                                    'source_role': 'ORIGINAL_INPUT'}],
              'source_context_version': version}
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


@pytest.mark.parametrize(('source', 'follow', 'reason'), [
    ('誘われたのに、嬉しくなかった。', 'その気持ちを大切に抱き続けてください。', 'directive'),
    ('その時は怖かった。', 'その怖さが今も強く残っているのですね。', 'unwritten_continuity'),
    ('その時は怖かった。', 'その怖さを誰にも言わずにいたのですね。', 'unwritten_disclosure'),
    ('怖さは今も残っています。', 'その怖さが今も残っているのですね。', None),
    ('その時は怖かった。', 'その時のことを聞かせてくださって、ありがとうございます。', None),
])
def test_opt_in_semantic_reader_checks_only_supported_claims_without_changing_older_receipts(
        source, follow, reason):
    writer = {'source_context_version': grounded.SEMANTIC_CONTEXT_VERSION,
              'records': [{'active_fields': [{'text': source}]}],
              'grounded_passages': [{'id': 'P1', 'text': source, 'field': 'memo',
                                    'source_role': 'ORIGINAL_INPUT'}]}
    composed = grounded.compose(json.dumps({'follow': follow}, ensure_ascii=False), writer)
    if reason:
        with pytest.raises(ValueError, match='grounded_observation_' + reason):
            grounded.read_reply(composed, writer)
    else:
        assert grounded.read_reply(composed, writer) == follow
    v7_writer = {**writer, 'source_context_version': grounded.ANSWER_FOCUS_CONTEXT_VERSION}
    if reason:
        with pytest.raises(ValueError, match='grounded_observation_' + reason):
            grounded.read_reply(composed, v7_writer)
    else:
        assert grounded.read_reply(composed, v7_writer) == follow
    for version in (grounded.CONTEXT_VERSION, grounded.CONSTRAINED_CONTEXT_VERSION):
        assert grounded.read_reply(composed, {**writer, 'source_context_version': version}) == follow


def test_listener_omits_only_displayed_source_rows_from_the_ordinary_record():
    other = {'field_path': 'memo_action', 'source_role': 'ORIGINAL_INPUT', 'text': '今日窓口へ行きました。'}
    current = {'scope': 'CURRENT_INPUT', 'metadata': {'emotions': ['喜び']}, 'active_state': 'RESOLVED',
               'meaning_state': 'NOT_GENERATED',
               'active_fields': [{**other, 'field_path': 'memo', 'text': MEMO}, other]}
    writer = {'records': [current], 'user_frame_feedback': [], 'source_context_version': grounded.LISTENER_CONTEXT_VERSION,
              'grounded_passages': [{'id': 'P1', 'field': 'memo', 'text': MEMO, 'source_role': 'ORIGINAL_INPUT'}]}
    messages = grounded.messages(writer)
    material = json.loads(messages[-1]['content'])
    assert probe.emlis_grounded_output_schema(messages)
    assert material['current']['active_fields'] == [other]
    assert messages[-1]['content'].count(MEMO) == 1
    current['active_state'] = 'PENDING'
    assert json.loads(grounded.messages(writer)[-1]['content'])['current'] == current


def test_answer_focus_requires_the_exact_active_original_evidence_range():
    from types import SimpleNamespace
    from cocolon_meaning_experience_engine.natural_reply import _grounded_answer_original_evidence

    def evidence(evidence_id, start, end):
        ref = SimpleNamespace(evidence_id=evidence_id, source_envelope_id='original', field_path='memo',
                              scalar_start=start, scalar_end=end)
        return SimpleNamespace(evidence=ref, thread_span_id=evidence_id)

    selected = evidence('selected', 3, 6)
    same_words = evidence('same_words', 7, 10)
    resolver = SimpleNamespace(qualified_refs=[selected, same_words],
                               resolve=lambda _: SimpleNamespace(raw_text='返事済'))
    question = SimpleNamespace(question_id='question',
        decision=SimpleNamespace(supporting_evidence_refs=['selected']))
    admitted = SimpleNamespace(
        control=SimpleNamespace(question_control_context=SimpleNamespace(issued_questions=[question])),
        original=SimpleNamespace(envelope=SimpleNamespace(envelope_id='original')),
        resolver=lambda: resolver)
    answer = {'question_id': 'question', 'text': 'その時は重く感じました。',
              'ai_question_context': 'どのように受け取りましたか。'}
    current = {'source_role': 'ORIGINAL_INPUT', 'source_envelope_id': 'original',
               'field_path': 'memo', 'scalar_start': 7, 'scalar_end': 10, 'text': '返事済'}
    active = {'coverage': {'active_state': 'RESOLVED'}, 'active_fields': [current]}
    assert _grounded_answer_original_evidence(admitted, active, answer) == []
    active['active_fields'] = [{**current, 'scalar_start': 2, 'scalar_end': 7, 'text': '前返事済後'}]
    assert _grounded_answer_original_evidence(admitted, active, answer) == ['返事済']
    active['coverage']['active_state'] = 'PENDING'
    assert _grounded_answer_original_evidence(admitted, active, answer) == []


@pytest.mark.parametrize(('tier', 'related', 'action'), [
    ('plus', True, '会議で発表した。'), ('premium', True, '会議で発表した。'),
    ('plus', False, '会議で発表した。'), ('plus', True, ''),
])
@pytest.mark.parametrize('version', [grounded.SEMANTIC_CONTEXT_VERSION, grounded.ANSWER_FOCUS_CONTEXT_VERSION,
                                     grounded.LISTENER_CONTEXT_VERSION])
def test_answer_uses_current_sources_and_replays_verified_paid_history(
        natural_case, qdb, monkeypatch, tier, related, action, version):
    from test_emlis_natural_frames_application import REVISION, _case, _past

    user, parent, _, _, past, _ = _case(natural_case, qdb, tier=tier, history=related)
    qdb.query('update public.emotions set memo_action=$2 where id=$1', [parent, action])
    if not related:
        past, _, _ = _past(qdb, user, memo='誘われたのに、悲しかった。', memo_action=action)
    calls = []
    follow = 'そのときの怖さも聞かせてくださって、Emlisは大事に受け取ります。'

    def infer(request):
        payload = json.loads(request.content)
        current = json.loads(payload['messages'][1]['content'])
        assert probe.emlis_grounded_output_schema(payload['messages'])
        calls.append(current)
        if current['stage'] == 'PRE_QUESTION':
            assert payload.get('candidate_format') == (FORMAT if tier == 'premium' else None)
            result = {'follow': 'そのときの気持ちに、Emlisは耳を傾けています。'}
            if action:
                result['passages'] = ['P1']
        else:
            assert current['stage'] == 'REFINED'
            assert payload['candidate_format'] == FORMAT
            assert current['history'] == current['confirmed_frame_feedback'] == []
            assert current['quote']['text'] == 'その時は怖かった。'
            assert current['ai_question_context'] == initial['pending_question']['text']
            if version != grounded.SEMANTIC_CONTEXT_VERSION:
                assert set(current['current']) == {'scope', 'original_evidence'}
                content = payload['messages'][1]['content']
                assert content.count('その時は怖かった。') == 1
                assert content.count(initial['pending_question']['text']) == 1
            if action:
                assert action not in payload['messages'][1]['content']
            result = {'follow': follow}
        return httpx.Response(200, json={'model': QWEN,
            **({'candidate_format': FORMAT} if payload.get('candidate_format') else {}), 'choices': [
            {'finish_reason': 'stop', 'message': {'role': 'assistant',
             'content': json.dumps(result, ensure_ascii=False)}}]})

    monkeypatch.setenv('COCOLON_EMLIS_GROUNDED_OBSERVATION', 'true')
    monkeypatch.setenv('COCOLON_EMLIS_GROUNDED_DECODING', 'true' if tier == 'premium' else '')
    monkeypatch.delenv('COCOLON_EMLIS_GROUNDED_SEMANTICS', raising=False)
    source = SelfHostedNaturalReplySource(endpoint='https://model.invalid/v1/chat/completions',
        model=QWEN, api_key='synthetic-only', transport=httpx.MockTransport(infer))
    service = _active_application_owner(monkeypatch, source, 'paid')
    initial = run(service.start(user, parent))
    assert initial['state'] == 'AWAITING_ANSWER'
    if tier == 'premium':
        frame, = initial['interpretive_frames']
        initial = run(service.frame_feedback(user, initial['thread_id'], frame_ref=frame['frame_ref'],
            status='REVISED', correction_text=REVISION, expected_revision=initial['revision'],
            idempotency_key='revise-past-frame'))
    monkeypatch.setenv('COCOLON_EMLIS_GROUNDED_DECODING', 'true')
    monkeypatch.setenv('COCOLON_EMLIS_GROUNDED_SEMANTICS', 'true')
    monkeypatch.setenv('COCOLON_EMLIS_GROUNDED_ANSWER_FOCUS',
                       'true' if version == grounded.ANSWER_FOCUS_CONTEXT_VERSION else '')
    monkeypatch.setenv('COCOLON_EMLIS_GROUNDED_LISTENER', 'true' if version == grounded.LISTENER_CONTEXT_VERSION else '')
    service = _active_application_owner(monkeypatch, source, 'paid')
    failed = False

    async def rpc(name, payload, **kwargs):
        nonlocal failed
        if not failed and any(event['kind'] == 'OBSERVATION' for event in payload.get('p_events', [])):
            failed = True
            return httpx.Response(503, json={'code': '57P03'})
        return await qdb.rpc(name, payload, **kwargs)

    monkeypatch.setattr(emlis_thread_store, 'sb_post_rpc', rpc)
    interruption = run(answer(service, user, initial, 'その時は怖かった。'))
    assert interruption['can_retry'] and len(calls) == 2
    before = run(service.store.read(user, input_id=parent))
    receipt, = [e['payload'] for e in before['events']
                if e['payload'].get('stage') == 'NATURAL_REPLY_RECEIVED'
                and e['operation_id'] == interruption['operation_id']]
    assert receipt['writer_context_version'] == version
    assert ('writer_history_sha256' in receipt) is related
    current = f'「その時は怖かった。」\n\n{follow}'
    if related:
        assert receipt['provider_reply_text'] == current
        assert '記録の「褒められた」' in receipt['reply']['text']
    else:
        assert receipt['reply']['text'] == current

    monkeypatch.delenv('COCOLON_EMLIS_GROUNDED_SEMANTICS')
    reopened = _active_application_owner(monkeypatch, source, 'paid')
    saved = run(reopened.action(user, interruption['thread_id'], action='retry_response',
        expected_revision=interruption['revision'], idempotency_key='save-received-reply',
        operation_id=interruption['operation_id']))
    assert saved['current_observation']['text'] == receipt['reply']['text']
    if tier == 'premium':
        frame, = saved['interpretive_frames']
        assert frame['input_id'] == past and frame['status'] == 'REVISED'
        assert frame['received_meaning'] == REVISION
    else:
        assert saved['interpretive_frames'] == []
    reread = run(reopened.get(user, parent))
    assert reread['current_observation'] == saved['current_observation']
    assert reread['interpretive_frames'] == saved['interpretive_frames']
    adapter = _piece_adapter(user, reopened, monkeypatch)
    ref = run(adapter.resolve_refined_source_ref('Bearer synthetic', parent,
        supplemental_answer_identity=before['thread']['latest_answer_event_id'], opted_in=True))
    assert ref['emlis_observation_result_identity'] == saved['current_observation']['event_id']
    assert len(calls) == 2
    qdb.query('update public.emotions set memo=$2 where id=$1', [past, '別の記録です。'])
    assert run(reopened.get(user, parent))['current_observation'] is None
