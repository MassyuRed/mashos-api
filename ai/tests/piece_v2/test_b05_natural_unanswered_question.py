"""An unanswered natural question remains an original-only Piece source."""
import copy
from uuid import uuid4

import httpx
import pytest

import emlis_thread_store

from piece_v2_contract import PieceContractError
from piece_v2_source_adapter import PieceSavedSourceAdapter
from test_cmee_piece_request_saved_pipeline import _bind_saved_request_io
from test_emlis_natural_question_application import natural_questions
from test_emlis_q2_application import run
from test_emlis_q3_application import qdb


@pytest.mark.parametrize('ending', ['open', 'skip', 'stop'])
def test_current_unanswered_original_has_both_current_observation_and_question_control(
        qdb, natural_questions, monkeypatch, ending):
    user, parent, emlis, calls = natural_questions(memo='誘われたのに、悲しかった。')
    _bind_saved_request_io(qdb, monkeypatch, user, 'fictional-piece-owner')
    initial = run(emlis.start(user, parent))
    if ending == 'open':
        current = initial
    else:
        current = run(emlis.action(user, initial['thread_id'], action=ending,
            expected_revision=initial['revision'], idempotency_key='q-'+ending,
            question_id=initial['pending_question']['question_id']))
    args = ('Bearer fictional-piece-owner', parent)
    adapter = PieceSavedSourceAdapter()
    ref = run(adapter.resolve_original_source_ref(*args))
    saved = run(emlis.store.read(user, input_id=parent))
    question, = [e for e in saved['events'] if e['kind'] == 'QUESTION']
    assert ref['emlis_observation_stage'] == 'pre_question_observation'
    assert ref['emlis_observation_result_identity'] == current['current_observation']['event_id']
    assert ref['question_need_decision_identity'] == question['id']
    assert ref['supplemental_answer_identity'] is None
    assert run(adapter.resolve_original_source_ref(*args)) == ref
    result = run(adapter.generate_original_candidate_from_saved_state(*args))
    assert result['source_lineage']['semantic_source_roles'] == ['original_input']
    assert result['candidate']['piece_text'] == '誘われたのに、悲しかった。'
    assert len(calls) == (1 if ending == 'open' else 2)
    if ending != 'skip':
        return

    original_read = adapter._store.read
    mutations = {
        'wrong_current_body': lambda s,e,op: s['thread'].update(last_observation_event_id=e('OBSERVATION')[0]['id']),
        'missing_final_request': lambda s,e,op: s['events'].remove(op('NATURAL_FINAL_REQUESTED')[0]),
        'swapped_question': lambda s,e,op: e('QUESTION')[0].update(attempt_id=e('OBSERVATION')[-1]['attempt_id']),
        'extra_answer': lambda s,e,op: e('QUESTION')[0].update(kind='ANSWER'),
        'different_source': lambda s,e,op: op('NATURAL_REPLY_RECEIVED')[-1]['payload'].update(source_prefix_ref='other'),
        'different_reply': lambda s,e,op: op('NATURAL_REPLY_RECEIVED')[-1]['payload']['reply'].update(text='別の返事。'),
        'reused_receipt': lambda s,e,op: op('NATURAL_REPLY_RECEIVED')[-1].update(attempt_id=e('OBSERVATION')[0]['attempt_id']),
        'changed_ending': lambda s,e,op: op('NATURAL_FINAL_REQUESTED')[0]['payload'].update(question_ending='stop'),
        'changed_stage': lambda s,e,op: op('NATURAL_REPLY_CALL_STARTED')[-1]['payload'].update(response_stage='PRE_QUESTION'),
    }
    for mutation in mutations.values():
        async def read_changed(*a, **kw):
            s = copy.deepcopy(await original_read(*a, **kw))
            events = lambda kind: [r for r in s['events'] if r['kind']==kind]
            operations = lambda stage: [r for r in events('OPERATION') if r['payload'].get('stage')==stage]
            mutation(s, events, operations)
            return s
        monkeypatch.setattr(adapter._store, 'read', read_changed)
        with pytest.raises(PieceContractError, match='PIECE_SOURCE_NOT_ELIGIBLE'):
            run(adapter.resolve_original_source_ref(*args))

def test_skip_retains_only_original_after_paid_context_is_revoked(qdb, natural_questions, monkeypatch):
    user, parent, emlis, calls = natural_questions(tier='plus')
    _bind_saved_request_io(qdb, monkeypatch, user, 'fictional-piece-owner')
    history = str(uuid4())
    qdb.query(
        "insert into public.emotions select $1,user_id,created_at-interval '1 day',"
        "'褒められた。会議の感想を考えた。',memo_action,category,emotions,emotion_details "
        "from public.emotions where id=$2", [history, parent])
    initial = run(emlis.start(user, parent))
    assert len(calls[0]['past_user_records']) == 1
    qdb.query('delete from public.emotions where id=$1', [history])
    changed = run(emlis.get(user, parent))
    done = run(emlis.action(user, initial['thread_id'], action='skip',
        expected_revision=changed['revision'], idempotency_key='skip-revoked',
        question_id=initial['pending_question']['question_id']))
    assert calls[-1]['past_user_records'] == []
    adapter = PieceSavedSourceAdapter()
    result = run(adapter.generate_original_candidate_from_saved_state('Bearer fictional-piece-owner', parent))
    lineage = result['source_lineage']
    assert lineage['observation']['emlis_observation_result_identity'] == done['current_observation']['event_id']
    assert lineage['semantic_source_roles'] == ['original_input']
    assert result['candidate']['piece_text'] == '褒められたのに、嬉しくなかった。'


@pytest.mark.parametrize('failed_call', [1, 2], ids=['pre-question', 'final'])
def test_saved_reply_survives_same_operation_explicit_retry(qdb, natural_questions, monkeypatch, failed_call):
    user, parent, emlis, calls = natural_questions()
    _bind_saved_request_io(qdb, monkeypatch, user, 'fictional-piece-owner')
    failed = False

    async def transient(name, payload, **kwargs):
        nonlocal failed
        writing_body = any(e['kind'] == 'OBSERVATION' for e in payload.get('p_events', []))
        if not failed and writing_body and len(calls) == failed_call:
            failed = True
            return httpx.Response(503, json={'code': '57P03'})
        return await qdb.rpc(name, payload, **kwargs)

    monkeypatch.setattr(emlis_thread_store, 'sb_post_rpc', transient)

    def retry(dto):
        assert dto['can_retry']
        return run(emlis.action(user, dto['thread_id'], action='retry_response',
            expected_revision=dto['revision'], idempotency_key='retry', operation_id=dto['operation_id']))

    initial = run(emlis.start(user, parent))
    if failed_call == 1:
        initial = retry(initial)
    final = run(emlis.action(user, initial['thread_id'], action='skip', question_id=initial['pending_question']['question_id'],
        expected_revision=initial['revision'], idempotency_key='skip'))
    if failed_call == 2:
        final = retry(final)
    adapter = PieceSavedSourceAdapter()
    ref = run(adapter.resolve_original_source_ref('Bearer fictional-piece-owner', parent))
    assert failed and len(calls) == 2
    assert ref['emlis_observation_result_identity'] == final['current_observation']['event_id']
    assert ref['supplemental_answer_identity'] is None

    # The old receipt alone never authorizes a different attempt's body.
    read = adapter._store.read
    async def unbound(*args, **kwargs):
        saved = copy.deepcopy(await read(*args, **kwargs))
        saved['events'] = [e for e in saved['events'] if e.get('idempotency_key') != 'retry']
        return saved
    monkeypatch.setattr(adapter._store, 'read', unbound)
    with pytest.raises(PieceContractError, match='PIECE_SOURCE_NOT_ELIGIBLE'):
        run(adapter.resolve_original_source_ref('Bearer fictional-piece-owner', parent))
