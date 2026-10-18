"""Negative revisions preserve real SQL state across saved reads and retry."""
import asyncio
from unittest.mock import patch
import pytest
import emlis_ai_grounded_human_reception as reception
from test_cmee_emlis_negative_revision_surface import ROWS, RECEPTION
from test_cmee_emlis_loneliness_delivery import export_dto, reopen
from test_cmee_emlis_relief_received_delivery import record_operation_times, record_sql_errors
from test_emlis_q3_application import qdb, qcase
from test_emlis_q2_application import run, answer

CASES = ('mixed_unknown_now_negative', 'mixed_unknown_current_negative')

def events(snapshot, kind):
    return [event for event in snapshot['events'] if event['kind'] == kind]

def persisted(snapshot):
    # SQL read's `now` is query time, not persisted thread or event content.
    return {key: value for key, value in snapshot.items() if key != 'now'}

def begin_case(qcase, qdb, case, tier):
    user, parent, service = qcase
    row = ROWS[case, 'q3']
    assert 'code' not in qdb.query('update public.emotions set memo=$2 where id=$1', [parent, row['memo']])
    assert 'code' not in qdb.query('update public.profiles set subscription_tier=$2 where id=$1', [user, tier])
    first = run(service.start(user, parent))
    assert first['state'] == 'AWAITING_ANSWER', first
    assert first['pending_question'] is not None and first['issued_count'] == 1
    assert first['question_limit'] == (3 if tier == 'premium' else 1)
    return user, parent, service, row, first

def assert_repaired(saved, first):
    assert saved['state'] == 'COMPLETED' and saved['body_state'] == 'REFINED', saved
    assert saved['answer_saved'] and saved['meaning_updated']
    assert saved['original'] == first['original']
    assert saved['pending_question'] is None and not saved['can_continue'] and not saved['can_retry']
    assert saved['issued_count'] == 1
    observation, reception_body = saved['current_observation']['text'].split('\n\nEmlisから：\n', 1)
    assert observation.startswith('見えたこと：\n')
    assert '「褒められた」のに「嬉しくなかった」という経験が書かれています。' in observation
    assert '同時に' not in observation
    assert reception_body == RECEPTION
    assert len([e for e in saved['timeline'] if e['kind'] == 'ANSWER']) == 1

@pytest.mark.parametrize('tier', ['free', 'premium'])
@pytest.mark.parametrize('case', CASES)
def test_new_negative_revision_is_saved_and_reopened_unchanged(qcase, qdb, tier, case):
    user, parent, service, row, first = begin_case(qcase, qdb, case, tier)
    saved = run(answer(service, user, first, row['answer']))
    assert_repaired(saved, first)
    stored = run(service.store.read(user, input_id=parent))
    assert len(events(stored, 'ANSWER')) == 1
    assert len(events(stored, 'MEANING_UPDATE')) == 2
    assert len(events(stored, 'QUESTION')) == 1
    reopen(user, parent, saved)
    assert run(service.get(user, parent)) == saved
    assert persisted(run(service.store.read(user, input_id=parent))) == persisted(stored)
    record_operation_times(stored, f'u354-current-{tier}-{case}')
    export_dto(f'u354-current-{tier}-{case}', saved)

@pytest.mark.parametrize('tier', ['free', 'premium'])
def test_saved_old_terminal_failure_is_not_regenerated(qcase, qdb, tier):
    user, parent, service, row, first = begin_case(qcase, qdb, 'mixed_unknown_current_negative', tier)
    assert row['artifact'] is None and row['status'] == 'UNAVAILABLE'
    # Reproduce the old reference, then remove this hook before all saved reads.
    with patch.object(reception, 'source_grounded_current_negative_relief_reference', return_value=False):
        saved = run(answer(service, user, first, row['answer']))
    assert saved['state'] == 'RESPONSE_FAILED' and saved['failure_code'] == 'body_not_validated'
    assert saved['body_state'] == 'MEANING_UPDATED_BODY_UNAVAILABLE'
    assert saved['answer_saved'] and saved['meaning_updated']
    assert saved['original'] == first['original'] and saved['current_observation'] is None
    assert not saved['can_retry'] and not saved['can_continue']
    assert [e for e in saved['timeline'] if e['kind'] == 'OBSERVATION'] == [
        dict(e, is_current=False) for e in first['timeline'] if e['kind'] == 'OBSERVATION']
    stored = run(service.store.read(user, input_id=parent))
    assert len(events(stored, 'ANSWER')) == 1 and len(events(stored, 'MEANING_UPDATE')) == 2
    reopen(user, parent, saved)
    assert run(service.get(user, parent)) == saved
    assert persisted(run(service.store.read(user, input_id=parent))) == persisted(stored)
    export_dto(f'u354-old-terminal-{tier}', saved)

@pytest.mark.parametrize('stage', ['before_meaning', 'after_meaning'])
def test_interrupted_answer_resumes_without_duplicate_or_replaced_meaning(qcase, qdb, monkeypatch, stage):
    user, parent, service, row, first = begin_case(qcase, qdb, 'mixed_unknown_current_negative', 'premium')
    initial_meanings = events(run(service.store.read(user, input_id=parent)), 'MEANING_UPDATE')
    assert len(initial_meanings) == 1
    prepare, generate = service.engine.prepare_emlis_update, service.engine.generate
    def interrupted(*args, **kwargs): raise asyncio.CancelledError()
    monkeypatch.setattr(service.engine, 'generate', interrupted)
    if stage == 'before_meaning': monkeypatch.setattr(service.engine, 'prepare_emlis_update', interrupted)
    with pytest.raises(asyncio.CancelledError): run(answer(service, user, first, row['answer']))
    pending = run(service.get(user, parent))
    assert pending['failure_code'] == 'worker_interrupted', pending
    assert pending['can_retry'] and pending['answer_saved'] and pending['original'] == first['original']
    before = run(service.store.read(user, input_id=parent))
    meanings, answers = events(before, 'MEANING_UPDATE'), events(before, 'ANSWER')
    assert len(answers) == 1 and meanings[:1] == initial_meanings
    assert len(meanings) == 1 + int(stage == 'after_meaning')
    def forbidden_prepare(*args, **kwargs): pytest.fail('Committed answer meaning must be reused')
    monkeypatch.setattr(service.engine, 'generate', generate)
    monkeypatch.setattr(service.engine, 'prepare_emlis_update', prepare if stage == 'before_meaning' else forbidden_prepare)
    saved = run(service.action(user, pending['thread_id'], action='retry_response',
        expected_revision=pending['revision'], idempotency_key=f'u354-retry-{stage}', operation_id=pending['operation_id']))
    assert_repaired(saved, first)
    assert saved['operation_id'] == pending['operation_id'] and saved['attempt_id'] != pending['attempt_id']
    after = run(service.store.read(user, input_id=parent)); current = events(after, 'MEANING_UPDATE')
    assert len(current) == 2 and current[:1] == initial_meanings
    assert events(after, 'ANSWER') == answers and len(events(after, 'QUESTION')) == 1
    if stage == 'after_meaning':
        assert current == meanings
        assert after['thread']['current_meaning_event_id'] == before['thread']['current_meaning_event_id']
    reopen(user, parent, saved)
    assert persisted(run(service.store.read(user, input_id=parent))) == persisted(after)
    record_operation_times(after, f'u354-retry-{stage}')
    export_dto(f'u354-retry-{stage}', saved)
