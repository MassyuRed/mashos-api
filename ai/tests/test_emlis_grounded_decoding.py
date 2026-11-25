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
from test_emlis_natural_question_application import ONE, natural_questions
from test_emlis_natural_reply_probe_http import probe
from test_emlis_q2_application import answer, run
from test_emlis_q3_application import past_record, qdb
from test_piece_model_server_constraints import messages as piece_messages, synthetic_generator


QWEN = probe.QWEN_9B_NATURAL_ALIAS
FORMAT = grounded.CONSTRAINED_CANDIDATE_FORMAT
MEMO = '紙の見本帳にあった細い青い縞が好きでした。'
FOLLOW = '青い縞に目を留めたお話を分けてくださって、Emlisは嬉しいです。'


def _messages(*, multi=False, context_version=None):
    passages = [{'id': 'P1', 'text': MEMO, 'field': 'memo', 'source_role': 'ORIGINAL_INPUT'}]
    if multi:
        passages.append({'id': 'P2', 'text': '受付で見本帳を返しました。', 'field': 'memo_action',
                         'source_role': 'ORIGINAL_INPUT'})
    return grounded.messages({'records': [{'scope': 'CURRENT_INPUT'}], 'grounded_passages': passages,
                              'user_frame_feedback': [], 'source_context_version': context_version})


def _accepts(messages, text):
    parser = probe.emlis_grounded_json_parser(messages, ''.join(dict.fromkeys(text)))
    for char in text:
        if char not in parser.get_allowed_characters():
            return False
        parser = parser.add_character(char)
    return parser.can_end()


def _answer_focus_messages():
    selected = _messages()
    material = json.loads(selected[1]['content'])
    material.update(stage='REFINED', ai_question_context='褒められた時は、どう感じましたか。')
    material['current'].update(
        follow_profile=probe.EMLIS_ANSWER_FOLLOW_PROFILE,
        original_evidence=['教室で褒められました。'],
    )
    material['quote'].update(field='answer', source_role='SUPPLEMENTAL_ANSWER', text='その時は怖かった。')
    selected[1]['content'] = json.dumps(material, ensure_ascii=False)
    return selected


def test_answer_focus_keeps_the_legacy_json_envelope():
    focused = _answer_focus_messages()
    legacy = _messages()
    assert probe.emlis_grounded_output_schema(focused) == probe.emlis_grounded_output_schema(legacy)
    assert probe._emlis_grounded_model_messages(legacy) is legacy


@pytest.mark.parametrize('disallowed', ['stage', 'role', 'history', 'evidence', 'marker'])
def test_answer_focus_rejects_other_stages_and_source_shapes(disallowed):
    focused = _answer_focus_messages()
    material = json.loads(focused[1]['content'])
    if disallowed == 'stage':
        material['stage'] = 'FINAL'
        del material['ai_question_context']
    if disallowed == 'role':
        material['quote'].update(field='memo', source_role='ORIGINAL_INPUT')
    if disallowed == 'history':
        material['history'] = ['昔の記録。']
    if disallowed == 'evidence':
        material['current']['original_evidence'] = '資料。'
    if disallowed == 'marker':
        material['current']['follow_profile'] = 'unknown'
    focused[1]['content'] = json.dumps(material, ensure_ascii=False)
    with pytest.raises(ValueError, match='emlis_grounded_answer_focus_invalid'):
        probe.emlis_grounded_output_schema(focused)


def test_answer_focus_tokenizes_one_answer_with_the_pinned_decoding_mask(monkeypatch):
    focused = _answer_focus_messages()
    snapshot = deepcopy(focused)
    raw = json.dumps({'follow': FOLLOW}, ensure_ascii=False)
    generator, capture, _, _ = synthetic_generator(monkeypatch, constrained=True, raw_output=raw, qwen_9b=True)
    assert generator(focused, time.monotonic() + 23, profile='emlis_grounded') == (raw, 'stop')
    chat, _ = capture['tokenize'][0]
    assert chat[0] == focused[0]
    assert json.loads(chat[1]['content']) == {
        'latest_answer': 'その時は怖かった。',
        'issued_question': '褒められた時は、どう感じましたか。',
        'original_evidence': ['教室で褒められました。'],
    }
    assert focused == snapshot


@pytest.mark.parametrize('raw', ('{"follow":"「引用」"}', '{"follow":"『引用』"}',
                                r'{"follow":"\u300c引用\u300d"}', r'{"follow":"一行\n二行"}',
                                r'{"follow":"\"引用\""}'))
def test_answer_focus_blocks_quotes_and_escapes_only_in_the_focused_decoder(monkeypatch, raw):
    generator, _, _, _ = synthetic_generator(monkeypatch, constrained=True, raw_output=raw, qwen_9b=True)
    assert generator(_messages(), time.monotonic() + 23, profile='emlis_grounded') == (raw, 'stop')
    with pytest.raises(AssertionError):
        # The synthetic forward verifies every scripted token against the live
        # prefix function, including the one it cannot emit for a focused reply.
        generator(_answer_focus_messages(), time.monotonic() + 23, profile='emlis_grounded')


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
def test_reception_prompt_keeps_v4_source_material_and_decoder_schema(multi):
    legacy = _messages(multi=multi, context_version=grounded.CONSTRAINED_CONTEXT_VERSION)
    candidate = _messages(multi=multi, context_version=grounded.RECEPTION_CONTEXT_VERSION)
    assert legacy == _messages(multi=multi, context_version=grounded.CONTEXT_VERSION)
    assert candidate[0] != legacy[0]
    assert candidate[1:] == legacy[1:]
    assert probe.emlis_grounded_output_schema(candidate) == probe.emlis_grounded_output_schema(legacy)


@pytest.mark.parametrize(('emotion', 'action_text', 'expected'), [
    ('自己理解', '', grounded.RECEPTION_CONTEXT_VERSION),
    ('平穏', '', grounded.CONSTRAINED_CONTEXT_VERSION),
    ('自己理解', '会議のメモを読みました。', grounded.CONSTRAINED_CONTEXT_VERSION),
    ('自己理解', '明日は何を準備する？', grounded.CONSTRAINED_CONTEXT_VERSION),
])
def test_initial_self_insight_reception_keeps_a_single_authored_memo_scope(
        natural_case, qdb, monkeypatch, emotion, action_text, expected):
    user, parent, _, _ = natural_case
    memo = '誰かにゆっくり説明すると考えを整理しやすいと気づきました。'
    assert 'code' not in qdb.query(
        "update public.emotions set memo=$2,memo_action=$3,emotions=$4,emotion_details=$5 where id=$1",
        [parent, memo, action_text, [emotion], json.dumps([dict(type=emotion, strength='medium')])])
    requests = []

    def infer(request):
        wire = json.loads(request.content)
        assert wire['candidate_format'] == FORMAT
        material = json.loads(wire['messages'][1]['content'])
        requests.append(material)
        reply = {'follow': '説明しながら考えが整うという気づきを、Emlisは喜んで受け取りました。'}
        if 'passages' in material:
            reply['passages'] = ['P1']
        return httpx.Response(200, json={'model': QWEN, 'candidate_format': FORMAT, 'choices': [{
            'finish_reason': 'stop', 'message': {'role': 'assistant',
                'content': json.dumps(reply, ensure_ascii=False)},
        }]})

    monkeypatch.setenv('COCOLON_EMLIS_GROUNDED_OBSERVATION', 'true')
    monkeypatch.setenv('COCOLON_EMLIS_GROUNDED_DECODING', 'true')
    source = SelfHostedNaturalReplySource(endpoint='https://model.invalid/v1/chat/completions',
        model=QWEN, api_key='synthetic-only', transport=httpx.MockTransport(infer))
    owner = _active_application_owner(monkeypatch, source, 'paid')
    dto = run(owner.start(user, parent))
    assert dto['state'] == 'COMPLETED' and dto['pending_question'] is None
    assert dto['body_state'] == 'FINAL' and dto['current_observation']['text'].startswith(f'「{memo}」')
    assert len(requests) == 1 and requests[0]['stage'] == 'FINAL' and not requests[0]['history']
    saved = run(owner.store.read(user, input_id=parent))
    received, = [row['payload'] for row in saved['events']
                 if row['payload'].get('stage') == 'NATURAL_REPLY_RECEIVED']
    assert received['writer_context_version'] == expected
    assert run(owner.get(user, parent))['current_observation'] == dto['current_observation']
    assert len(requests) == 1


@pytest.mark.parametrize(('tier', 'history', 'action', 'memo', 'expected'), [
    ('free', False, 'answer', ONE, grounded.RECEPTION_CONTEXT_VERSION),
    ('plus', False, 'answer', ONE, grounded.RECEPTION_CONTEXT_VERSION),
    ('premium', True, 'answer', ONE, grounded.CONSTRAINED_CONTEXT_VERSION),
    ('premium', True, 'skip', ONE, grounded.RECEPTION_CONTEXT_VERSION),
    ('premium', False, 'answer', ONE + '誘われたのに、悲しかった。', grounded.RECEPTION_CONTEXT_VERSION),
])
def test_reception_selection_uses_admitted_material_and_persists_the_writer(
        natural_questions, qdb, monkeypatch, tier, history, action, memo, expected):
    user, parent, _, _ = natural_questions(tier=tier, memo=memo)
    if history:
        past_record(qdb, user, monkeypatch)
    requests = []

    def infer(request):
        wire = json.loads(request.content)
        assert wire['candidate_format'] == FORMAT
        requests.append(wire['messages'])
        material = json.loads(wire['messages'][1]['content'])
        follow = ('その時の怖さを伝えてくださったことを、Emlisは受け止めました。'
                  if material['stage'] == 'REFINED' else '率直なお気持ちをEmlisは受け止めました。')
        return httpx.Response(200, json={'model': QWEN, 'candidate_format': FORMAT, 'choices': [{
            'finish_reason': 'stop', 'message': {'role': 'assistant',
                'content': json.dumps({'follow': follow}, ensure_ascii=False)},
        }]})

    monkeypatch.setenv('COCOLON_EMLIS_GROUNDED_OBSERVATION', 'true')
    monkeypatch.setenv('COCOLON_EMLIS_GROUNDED_DECODING', 'true')
    source = SelfHostedNaturalReplySource(endpoint='https://model.invalid/v1/chat/completions',
        model=QWEN, api_key='synthetic-only', transport=httpx.MockTransport(infer))
    owner = _active_application_owner(monkeypatch, source, 'paid')
    started = run(owner.start(user, parent))
    question = started['pending_question']
    assert question is not None and started['current_observation'] is not None
    if action == 'answer':
        closed = run(answer(owner, user, started, 'その時は怖かった。'))
    else:
        closed = run(owner.action(user, started['thread_id'], action='skip',
            question_id=question['question_id'], expected_revision=started['revision'],
            idempotency_key='skip-first-question'))

    assert closed['current_observation'] is not None
    assert len(requests) == 2
    sent = json.loads(requests[1][1]['content'])
    assert bool(sent['history']) == (history and action == 'answer')
    assert sent['quote']['source_role'] == ('SUPPLEMENTAL_ANSWER' if action == 'answer' else 'ORIGINAL_INPUT')
    if action == 'answer':
        assert sent['ai_question_context'] == question['text']
    stored = run(owner.store.read(user, input_id=parent))
    versions = [row['payload']['writer_context_version'] for row in stored['events']
                if row['payload'].get('stage') == 'NATURAL_REPLY_RECEIVED']
    initial = (grounded.QUESTION_PREFACE_CONTEXT_VERSION if memo == ONE
               else grounded.CONSTRAINED_CONTEXT_VERSION)
    assert versions == [initial, expected]

    monkeypatch.delenv('COCOLON_EMLIS_GROUNDED_DECODING')
    restarted = _active_application_owner(monkeypatch, source, 'paid')
    reread = run(restarted.get(user, parent))
    assert reread['current_observation'] == closed['current_observation']
    assert reread['revision'] == closed['revision'] and len(requests) == 2


@pytest.mark.parametrize(('follow', 'accepted'), [
    ('あなたは資料を書かなかったのですね。', True),
    ('あなたは資料を書いたのですね。', False),
])
def test_grounded_reply_checks_current_answer_polarity_before_saving(
        natural_questions, monkeypatch, follow, accepted):
    user, parent, _, _ = natural_questions()
    authored = '私は資料を書かなかった。'
    requests = []

    def infer(request):
        wire = json.loads(request.content)
        material = json.loads(wire['messages'][-1]['content'])
        requests.append(material)
        text = follow if material['stage'] == 'REFINED' else 'お気持ちをEmlisは受け止めました。'
        return httpx.Response(200, json={'model': QWEN, 'candidate_format': FORMAT, 'choices': [{
            'finish_reason': 'stop', 'message': {'role': 'assistant',
                'content': json.dumps({'follow': text}, ensure_ascii=False)},
        }]})

    monkeypatch.setenv('COCOLON_EMLIS_GROUNDED_OBSERVATION', 'true')
    monkeypatch.setenv('COCOLON_EMLIS_GROUNDED_DECODING', 'true')
    source = SelfHostedNaturalReplySource(endpoint='https://model.invalid/v1/chat/completions',
        model=QWEN, api_key='synthetic-only', transport=httpx.MockTransport(infer))
    owner = _active_application_owner(monkeypatch, source, None)
    started = run(owner.start(user, parent))
    result = run(answer(owner, user, started, authored))
    assert requests[1]['quote']['text'] == authored
    assert result['answer_saved']
    assert result['state'] == ('COMPLETED' if accepted else 'RESPONSE_FAILED')
    assert (result['current_observation'] is not None) == accepted

    snapshot = run(owner.store.read(user, input_id=parent))
    answer_event, = [event for event in snapshot['events'] if event['kind'] == 'ANSWER']
    assert answer_event['payload']['source']['answer_text_private'] == authored
    assert answer_event['question_id'] == started['pending_question']['question_id']
    reread = run(owner.get(user, parent))
    assert reread['current_observation'] == result['current_observation']
    assert reread['revision'] == result['revision'] and len(requests) == 2


@pytest.mark.parametrize(('follow', 'reason'), [
    ('その時の気持ちを大切にしてください。', 'grounded_observation_directive'),
    ('今もその気持ちが残っているのですね。', 'grounded_observation_unwritten_continuity'),
    ('そのことを誰にも言わずにいたのですね。', 'grounded_observation_unwritten_disclosure'),
])
def test_question_preface_admission_uses_v5_checks_without_changing_older_versions(follow, reason):
    passage = {'id': 'P1', 'text': ONE, 'field': 'memo', 'source_role': 'ORIGINAL_INPUT'}
    writer = {'records': [{'active_fields': [passage]}], 'grounded_passages': [passage],
              'source_context_version': grounded.QUESTION_PREFACE_CONTEXT_VERSION}
    reply = grounded.compose(json.dumps({'follow': follow}, ensure_ascii=False), writer)
    with pytest.raises(ValueError, match=reason):
        grounded.read_reply(reply, writer)
    for version in (grounded.CONSTRAINED_CONTEXT_VERSION, grounded.RECEPTION_CONTEXT_VERSION):
        assert grounded.read_reply(reply, {**writer, 'source_context_version': version}) == follow


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


@pytest.mark.parametrize(('version', 'memo'), [
    (grounded.CONTEXT_VERSION, MEMO),
    (grounded.CONSTRAINED_CONTEXT_VERSION, MEMO),
    (grounded.CONSTRAINED_CONTEXT_VERSION, ONE),
    (grounded.QUESTION_PREFACE_CONTEXT_VERSION, ONE),
])
def test_grounded_receipts_keep_their_exact_messages_when_flag_changes(
        natural_case, qdb, monkeypatch, version, memo):
    user, parent, _, _ = natural_case
    qdb.query("update public.emotions set memo=$2,memo_action='' where id=$1", [parent, memo])
    constrained = version != grounded.CONTEXT_VERSION
    legacy_question = memo == ONE and version == grounded.CONSTRAINED_CONTEXT_VERSION
    supports_question_preface = grounded.supports_question_preface
    if legacy_question:
        monkeypatch.setattr(grounded, 'supports_question_preface', lambda passage: False)
    follow = FOLLOW if memo == MEMO else '率直なお気持ちをEmlisは受け止めました。'
    calls = []
    failed = False

    def infer(request):
        payload = json.loads(request.content)
        calls.append(payload)
        assert payload["messages"] == _messages_for_same_current_record(payload, version, memo)
        assert payload.get('candidate_format') == (FORMAT if constrained else None)
        result = {'model': QWEN, 'choices': [{'finish_reason': 'stop',
            'message': {'role': 'assistant', 'content': json.dumps({'follow': follow}, ensure_ascii=False)}}]}
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
    assert receipt['writer_context_version'] == version

    monkeypatch.setattr(grounded, 'supports_question_preface', supports_question_preface)
    monkeypatch.setenv("COCOLON_EMLIS_GROUNDED_DECODING", "true" if legacy_question or not constrained else "")
    restarted = _active_application_owner(monkeypatch, source, None)
    saved = run(restarted.action(user, failed_reply['thread_id'], action='retry_response',
        expected_revision=failed_reply['revision'], idempotency_key='restore-received-reply',
        operation_id=failed_reply['operation_id']))
    assert saved['current_observation']['text'] == f'「{memo}」\n\n{follow}'
    reread = run(restarted.get(user, parent))
    assert reread['current_observation'] == saved['current_observation']
    assert reread['revision'] == saved['revision'] and len(calls) == 1


def _messages_for_same_current_record(payload, version, memo):
    material = json.loads(payload["messages"][1]["content"])
    writer = {'records': [material['current']], 'user_frame_feedback': [],
              'grounded_passages': [{'id': 'P1', 'text': memo, 'field': 'memo',
                                    'source_role': 'ORIGINAL_INPUT'}],
              'response_purpose': {'stage': 'FINAL' if memo == MEMO else 'PRE_QUESTION'},
              'source_context_version': version}
    return grounded.messages(writer)


def test_free_answer_receipt_keeps_original_writer_binding_on_retry(natural_questions, qdb, monkeypatch):
    user, parent, _, _ = natural_questions()
    authored = 'その時は怖かった。'
    follow = 'その時の怖さをEmlisは受け止めました。'
    calls = []

    def infer(request):
        payload = json.loads(request.content)
        material = json.loads(payload['messages'][1]['content'])
        calls.append(material)
        assert payload['candidate_format'] == FORMAT
        return httpx.Response(200, json={'model': QWEN, 'candidate_format': FORMAT, 'choices': [{
            'finish_reason': 'stop', 'message': {'role': 'assistant',
                'content': json.dumps({'follow': follow}, ensure_ascii=False)},
        }]})

    async def interrupt_observation(name, payload, **kwargs):
        if any(event['kind'] == 'OBSERVATION' for event in payload.get('p_events', [])):
            return httpx.Response(503, json={'code': '57P03'})
        return await qdb.rpc(name, payload, **kwargs)

    monkeypatch.setenv('COCOLON_EMLIS_GROUNDED_OBSERVATION', 'true')
    monkeypatch.setenv('COCOLON_EMLIS_GROUNDED_DECODING', 'true')
    source = SelfHostedNaturalReplySource(endpoint='https://model.invalid/v1/chat/completions',
        model=QWEN, api_key='synthetic-only', transport=httpx.MockTransport(infer))
    service = _active_application_owner(monkeypatch, source, 'paid')
    started = run(service.start(user, parent))
    with monkeypatch.context() as making_receipt:
        making_receipt.setattr(emlis_thread_store, 'sb_post_rpc', interrupt_observation)
        interrupted = run(answer(service, user, started, authored))
    assert interrupted['can_retry'] and len(calls) == 2
    state = run(service.store.read(user, input_id=parent))
    receipt, = [event['payload'] for event in state['events'] if event['operation_id'] == interrupted['operation_id']
                and event['payload'].get('stage') == 'NATURAL_REPLY_RECEIVED']
    assert receipt['writer_context_version'] == grounded.RECEPTION_CONTEXT_VERSION
    material = calls[1]
    assert material['ai_question_context'] == started['pending_question']['text']
    assert 'ai_question_context' not in json.dumps(material['current'], ensure_ascii=False)

    monkeypatch.delenv('COCOLON_EMLIS_GROUNDED_DECODING')
    restarted = _active_application_owner(monkeypatch, source, 'true')
    saved = run(restarted.action(user, interrupted['thread_id'], action='retry_response',
        expected_revision=interrupted['revision'], idempotency_key='restore-free-answer',
        operation_id=interrupted['operation_id']))
    assert saved['body_state'] == 'REFINED'
    assert saved['current_observation']['text'] == f'「{authored}」\n\n{follow}'
    assert len(calls) == 2


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


@pytest.mark.parametrize('related', [True, False])
def test_plus_answer_focus_saves_only_verified_history_and_reuses_the_receipt(
        natural_case, qdb, monkeypatch, related):
    from test_emlis_natural_frames_application import _case, _past

    user, parent, _, _, _, _ = _case(natural_case, qdb, tier='plus', history=related)
    independent_action = '会議で発表した。'
    qdb.query('update public.emotions set memo_action=$2 where id=$1', [parent, independent_action])
    if not related:
        _past(qdb, user, memo='誘われたのに、悲しかった。', memo_action=independent_action)
    calls = []
    authored = 'その時は怖かった。'
    follow = 'そのときの怖さまで話してくださったこと、Emlisは大事に受け止めます。'

    def infer(request):
        wire = json.loads(request.content)
        material = json.loads(wire['messages'][1]['content'])
        calls.append(material)
        if material['stage'] == 'PRE_QUESTION':
            result = {'passages': ['P1'], 'follow': 'そのときの気持ちに、Emlisは耳を傾けています。'}
        else:
            assert material['current']['follow_profile'] == 'answer_focus_v1'
            assert material['quote']['text'] == authored
            assert material['ai_question_context'] == first['pending_question']['text']
            assert material['history'] == material['confirmed_frame_feedback'] == []
            assert independent_action not in wire['messages'][1]['content']
            result = {'follow': follow}
        return httpx.Response(200, json={'model': QWEN, 'candidate_format': FORMAT, 'choices': [
            {'finish_reason': 'stop', 'message': {'role': 'assistant',
                'content': json.dumps(result, ensure_ascii=False)}}]})

    for name in ('COCOLON_EMLIS_GROUNDED_OBSERVATION', 'COCOLON_EMLIS_GROUNDED_DECODING'):
        monkeypatch.setenv(name, 'true')
    source = SelfHostedNaturalReplySource(endpoint='https://model.invalid/v1/chat/completions',
        model=QWEN, api_key='synthetic-only', transport=httpx.MockTransport(infer))
    service = _active_application_owner(monkeypatch, source, 'paid')
    first = run(service.start(user, parent))
    failed = False

    async def rpc(name, payload, **kwargs):
        nonlocal failed
        if not failed and any(event['kind'] == 'OBSERVATION' for event in payload.get('p_events', [])):
            failed = True
            return httpx.Response(503, json={'code': '57P03'})
        return await qdb.rpc(name, payload, **kwargs)

    monkeypatch.setattr(emlis_thread_store, 'sb_post_rpc', rpc)
    interrupted = run(answer(service, user, first, authored))
    assert interrupted['can_retry'] and len(calls) == 2
    for name in ('COCOLON_EMLIS_GROUNDED_OBSERVATION', 'COCOLON_EMLIS_GROUNDED_DECODING'):
        monkeypatch.delenv(name)
    reopened = _active_application_owner(monkeypatch, source, 'paid')
    saved = run(reopened.action(user, interrupted['thread_id'], action='retry_response',
        expected_revision=interrupted['revision'], idempotency_key='save-received-plus-answer',
        operation_id=interrupted['operation_id']))
    assert saved['body_state'] == 'REFINED'
    text = saved['current_observation']['text']
    expected = f'「{authored}」\n\n{follow}'
    if related:
        current, suffix = text.rsplit('\n\n', 1)
        assert current == expected and 'の記録の「褒められた」' in suffix
    else:
        assert text == expected
    reread = run(reopened.get(user, parent))
    assert reread['current_observation'] == saved['current_observation']
    assert reread['revision'] == saved['revision'] and len(calls) == 2
