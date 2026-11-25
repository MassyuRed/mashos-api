"""Normal paid replies with the existing history owner and isolated SQL."""

from dataclasses import replace
import hashlib
import json
import re
from types import SimpleNamespace

import httpx
import pytest

import emlis_thread_store
from cocolon_meaning_experience_engine import grounded_observation_reply as grounded
from cocolon_meaning_experience_engine.natural_reply import (
    NaturalReply, NaturalReplyError, NaturalReplyInput, SelfHostedNaturalReplySource,
    _grounded_answer_original_evidence, validate_reply,
)
from test_emlis_natural_frames_application import REVISION, _case, _past
from test_emlis_natural_question_application import THREE, natural_questions
from test_emlis_natural_reply_application import _active_application_owner, _piece_adapter, natural_case
from test_emlis_natural_reply_probe_http import probe
from test_emlis_q2_application import answer, run
from test_emlis_q3_application import qdb


ANSWER = 'その時は怖かった。'
FOLLOW = 'そのときの怖さも聞かせてくださって、Emlisは大事に受け取ります。'
ACTION = '会議で発表した。'
QWEN = probe.QWEN_9B_NATURAL_ALIAS
FORMAT = grounded.CONSTRAINED_CANDIDATE_FORMAT


@pytest.mark.parametrize(('tier', 'related'), [('plus', True), ('premium', True), ('plus', False)])
def test_paid_answer_keeps_history_out_of_writer_and_replays_the_verified_suffix(
        natural_case, qdb, monkeypatch, tier, related):
    user, parent, _, _, past, _ = _case(natural_case, qdb, tier=tier, history=related)
    qdb.query('update public.emotions set memo_action=$2 where id=$1', [parent, ACTION])
    if not related:
        # A repeated event from the other field is outside this question's scope.
        past, _, _ = _past(qdb, user, memo='誘われたのに、悲しかった。', memo_action=ACTION)
    calls = []

    def infer(request):
        wire = json.loads(request.content)
        material = json.loads(wire['messages'][1]['content'])
        assert probe.emlis_grounded_output_schema(wire['messages'])
        assert wire['candidate_format'] == FORMAT
        calls.append(material)
        if material['stage'] == 'PRE_QUESTION':
            result = {'passages': ['P1'], 'follow': 'そのときの気持ちに、Emlisは耳を傾けています。'}
        else:
            assert material['stage'] == 'REFINED'
            assert material['history'] == material['confirmed_frame_feedback'] == []
            assert set(material['current']) == {'scope', 'original_evidence'}
            assert material['current']['scope'] == 'CURRENT_INPUT'
            assert material['quote']['text'] == ANSWER
            assert material['ai_question_context'] == first['pending_question']['text']
            content = wire['messages'][1]['content']
            assert content.count(ANSWER) == content.count(first['pending_question']['text']) == 1
            assert ACTION not in content and '重かった' not in content and REVISION not in content
            result = {'follow': FOLLOW}
        return httpx.Response(200, json={'model': QWEN, 'candidate_format': FORMAT, 'choices': [
            {'finish_reason': 'stop', 'message': {'role': 'assistant',
                'content': json.dumps(result, ensure_ascii=False)}}]})

    monkeypatch.setenv('COCOLON_EMLIS_GROUNDED_OBSERVATION', 'true')
    monkeypatch.setenv('COCOLON_EMLIS_GROUNDED_DECODING', 'true')
    source = SelfHostedNaturalReplySource(endpoint='https://model.invalid/v1/chat/completions',
        model=QWEN, api_key='synthetic-only', transport=httpx.MockTransport(infer))
    service = _active_application_owner(monkeypatch, source, 'paid')
    first = run(service.start(user, parent))
    assert first['state'] == 'AWAITING_ANSWER'
    if tier == 'premium':
        frame, = first['interpretive_frames']
        first = run(service.frame_feedback(user, first['thread_id'], frame_ref=frame['frame_ref'],
            status='REVISED', correction_text=REVISION, expected_revision=first['revision'],
            idempotency_key='revise-past-frame'))
    failed = False

    async def rpc(name, payload, **kwargs):
        nonlocal failed
        if not failed and any(event['kind'] == 'OBSERVATION' for event in payload.get('p_events', [])):
            failed = True
            return httpx.Response(503, json={'code': '57P03'})
        return await qdb.rpc(name, payload, **kwargs)

    monkeypatch.setattr(emlis_thread_store, 'sb_post_rpc', rpc)
    interruption = run(answer(service, user, first, ANSWER))
    assert interruption['can_retry'] and len(calls) == 2
    snapshot = run(service.store.read(user, input_id=parent))
    receipt, = [event['payload'] for event in snapshot['events']
                if event['payload'].get('stage') == 'NATURAL_REPLY_RECEIVED'
                and event['operation_id'] == interruption['operation_id']]
    assert receipt['writer_context_version'] == grounded.ANSWER_EVIDENCE_CONTEXT_VERSION
    assert ('writer_history_sha256' in receipt) is related
    current = f'「{ANSWER}」\n\n{FOLLOW}'
    if related:
        assert receipt['provider_reply_text'] == current
        stored_current, history = receipt['reply']['text'].rsplit('\n\n', 1)
        assert stored_current == current
        assert re.search(r'\d{4}-\d{2}-\d{2}の記録', history)
        assert '記録の「褒められた」' in history and '重かった' not in history and REVISION not in history
        assert receipt['writer_history_sha256'] == hashlib.sha256(history.encode('utf-8')).hexdigest()
    else:
        assert 'provider_reply_text' not in receipt
        assert receipt['reply']['text'] == current

    monkeypatch.delenv('COCOLON_EMLIS_GROUNDED_DECODING')
    monkeypatch.delenv('COCOLON_EMLIS_GROUNDED_OBSERVATION')
    reopened = _active_application_owner(monkeypatch, source, 'paid')
    saved = run(reopened.action(user, interruption['thread_id'], action='retry_response',
        expected_revision=interruption['revision'], idempotency_key='save-received-reply',
        operation_id=interruption['operation_id']))
    assert saved['body_state'] == 'REFINED'
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
        supplemental_answer_identity=snapshot['thread']['latest_answer_event_id'], opted_in=True))
    assert ref['emlis_observation_result_identity'] == saved['current_observation']['event_id']
    qdb.query('update public.emotions set memo=$2 where id=$1', [past, '別の記録です。'])
    assert run(reopened.get(user, parent))['current_observation'] is None
    assert len(calls) == 2


@pytest.mark.parametrize(('answers', 'repeated'), [
    (('その時は重かった。',), '褒められた'),
    (('その時は重かった。', 'その時は怖かった。'), '誘われた'),
])
def test_paid_final_binds_the_answered_question_when_a_later_question_is_skipped(
        natural_questions, qdb, monkeypatch, answers, repeated):
    user, parent, _, _ = natural_questions(tier='premium', memo=THREE)
    _past(qdb, user, memo=THREE)
    stages = []

    def infer(request):
        wire = json.loads(request.content)
        material = json.loads(wire['messages'][1]['content'])
        assert probe.emlis_grounded_output_schema(wire['messages'])
        stages.append(material)
        content = {'follow': 'そのときの気持ちに、Emlisは耳を傾けています。'}
        if 'passages' in material:
            content['passages'] = ['P1']
        return httpx.Response(200, json={'model': QWEN, 'candidate_format': FORMAT, 'choices': [
            {'finish_reason': 'stop', 'message': {'role': 'assistant',
                'content': json.dumps(content, ensure_ascii=False)}}]})

    monkeypatch.setenv('COCOLON_EMLIS_GROUNDED_OBSERVATION', 'true')
    monkeypatch.setenv('COCOLON_EMLIS_GROUNDED_DECODING', 'true')
    source = SelfHostedNaturalReplySource(endpoint='https://model.invalid/v1/chat/completions',
        model=QWEN, api_key='synthetic-only', transport=httpx.MockTransport(infer))
    service = _active_application_owner(monkeypatch, source, 'paid')
    dto = run(service.start(user, parent))
    for index, text in enumerate(answers, start=1):
        answered = dto['pending_question']
        dto = run(answer(service, user, dto, text, f'answer-{index}'))
        assert dto['state'] == 'AWAITING_CONTINUE'
        dto = run(service.action(user, dto['thread_id'], action='continue',
            expected_revision=dto['revision'], idempotency_key=f'continue-{index}'))

    skipped = dto['pending_question']
    done = run(service.action(user, dto['thread_id'], action='skip', question_id=skipped['question_id'],
        expected_revision=dto['revision'], idempotency_key='skip-later-paid'))
    assert done['state'] == 'COMPLETED' and done['body_state'] == 'REFINED'
    assert len(stages) == len(answers) + 2
    received = stages[-1]
    assert received['stage'] == 'FINAL' and received['quote']['text'] == answers[-1]
    assert received['current']['ai_question_context'] == answered['text']
    assert skipped['text'] not in json.dumps(received, ensure_ascii=False)
    assert received['history'] == received['confirmed_frame_feedback'] == []
    assert f'記録の「{repeated}」' in done['current_observation']['text']
    assert run(service.get(user, parent))['current_observation'] == done['current_observation']


def test_only_the_exact_effective_original_range_of_the_answered_question_is_exposed():
    def evidence(evidence_id, envelope, start, end):
        ref = SimpleNamespace(evidence_id=evidence_id, source_envelope_id=envelope, field_path='memo',
                              scalar_start=start, scalar_end=end)
        return SimpleNamespace(evidence=ref, thread_span_id=evidence_id)

    resolver = SimpleNamespace(qualified_refs=[evidence('selected', 'original', 3, 6),
        evidence('same_words', 'original', 7, 10), evidence('past', 'past', 3, 6)],
        resolve=lambda _: SimpleNamespace(raw_text='返事済'))
    question = SimpleNamespace(question_id='question',
        decision=SimpleNamespace(supporting_evidence_refs=['selected', 'past']))
    admitted = SimpleNamespace(control=SimpleNamespace(question_control_context=SimpleNamespace(
        issued_questions=[question])), original=SimpleNamespace(envelope=SimpleNamespace(envelope_id='original')),
        resolver=lambda: resolver)
    latest = {'question_id': 'question', 'text': ANSWER, 'ai_question_context': 'どのように受け取りましたか。'}
    selected = {'source_role': 'ORIGINAL_INPUT', 'source_envelope_id': 'original', 'field_path': 'memo',
                'scalar_start': 2, 'scalar_end': 7, 'text': '前返事済後'}
    fields = [{'source_role': 'ORIGINAL_INPUT', 'source_envelope_id': 'original',
               'field_path': 'memo', 'scalar_start': 7, 'scalar_end': 10, 'text': '返事済'},
              {**selected, 'source_envelope_id': 'past'}]
    active = {'coverage': {'active_state': 'RESOLVED'}, 'active_fields': fields}
    assert _grounded_answer_original_evidence(admitted, active, latest) == []
    fields.append(selected)
    assert _grounded_answer_original_evidence(admitted, active, latest) == ['返事済']
    assert _grounded_answer_original_evidence(admitted, active, {**latest, 'question_id': 'other'}) == []
    active['coverage']['active_state'] = 'PENDING'
    assert _grounded_answer_original_evidence(admitted, active, latest) == []


def test_only_the_verified_suffix_is_admitted_after_the_full_follow_width():
    history = '2026年11月22日の記録の「褒められた」と、今回の「褒められた」は、本人が書いた同じ言葉です。'
    writer = {'source_context_version': grounded.ANSWER_EVIDENCE_CONTEXT_VERSION,
        'history_line': history, 'records': [{'active_fields': []}], 'grounded_passages': [
            {'id': 'P1', 'text': ANSWER, 'field': 'answer', 'source_role': 'SUPPLEMENTAL_ANSWER'}]}
    material = NaturalReplyInput('prefix', '{"current":{}}', writer_material_json=json.dumps(writer))
    body = grounded.compose(json.dumps({'follow': 'あ' * 239 + '。'}), writer)
    raw = NaturalReply(body, QWEN, material.source_prefix_ref)
    verified = replace(raw, text=f'{raw.text}\n\n{history}')
    assert validate_reply(raw, material) == raw
    assert validate_reply(verified, material, allow_verified_history=True) == verified
    with pytest.raises(NaturalReplyError) as error:
        validate_reply(verified, material)
    assert error.value.reason == 'grounded_observation_follow'
    short = replace(raw, text=f'「{ANSWER}」\n\n{FOLLOW}')
    for extra in (history.replace('22日', '21日'), history + '\n\n' + history, '過去にも同じでした。'):
        with pytest.raises(NaturalReplyError) as error:
            validate_reply(replace(short, text=f'{short.text}\n\n{extra}'), material, allow_verified_history=True)
        assert error.value.reason == 'grounded_observation_follow'
    with pytest.raises(NaturalReplyError) as error:
        validate_reply(replace(short, text=f'「{ANSWER}」\n\n今も強く残っているのですね。\n\n{history}'),
                       material, allow_verified_history=True)
    assert error.value.reason == 'grounded_observation_unwritten_continuity'
