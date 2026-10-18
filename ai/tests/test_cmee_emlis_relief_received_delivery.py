"""The bounded received experience reaches real SQL storage and saved DTOs.

These service tests reuse the existing isolated PostgreSQL WASM fixture.  The
HTTP/Auth/native boundary is exercised separately with these exact exported DTOs.
Historical text comes from the independently captured, pre-u350 fixture.
"""
import asyncio
from contextlib import contextmanager
from datetime import datetime
import json
from pathlib import Path
from unittest.mock import patch

import pytest
from cocolon_meaning_experience_engine import emlis_question
from test_cmee_emlis_loneliness_delivery import export_dto, reopen
from test_emlis_q3_application import qdb, qcase
from test_emlis_q2_application import run, answer


BASELINE = json.loads((Path(__file__).parent /
    'fixtures/cmee_emlis_u349_relief_received_v1.json').read_text())
ROWS = {row['case']: row for row in BASELINE['cases']}
UPDATES = {row['case']: row for row in BASELINE['updates']}
PAIR = 'ほっとしたと聞いて、私も少し安心しましたが、その寂しさにも、今、耳を傾けていたいです。'
UNKNOWN = '何が不安なのか、あなたにもまだわからないのですね。'
STAGES = ('add', 'add_negative', 'add_past', 'add_past_negative',
          'revise', 'withdraw_event', 'withdraw_reaction')


@pytest.fixture(autouse=True)
def record_sql_errors(qdb, monkeypatch):
    query = qdb.query

    def observed(*args, **kwargs):
        result = query(*args, **kwargs)
        if isinstance(result, dict) and 'code' in result:
            print('DELIVERY_SQL_ERROR ' + json.dumps(result, ensure_ascii=False))
        return result

    monkeypatch.setattr(qdb, 'query', observed)


def source_row(with_unknown):
    return ROWS['base_unknown' if with_unknown else 'base']


def update_row(stage, with_unknown):
    return UPDATES[stage + ('_unknown' if with_unknown else '')]


def frozen_text(stage, with_unknown):
    row = source_row(with_unknown) if stage == 'initial' else update_row(stage, with_unknown)
    artifact = row['q3']['artifact']
    assert artifact is not None
    return f"見えたこと：\n{artifact['observation']}\n\nEmlisから：\n{artifact['reception']}"


@contextmanager
def original_u348():
    original = emlis_question._original_source_meaning_plan

    def legacy(source, **kwargs):
        kwargs['_legacy_relief_received_retention'] = True
        return original(source, **kwargs)

    # Reproduce the old source version through the actual service, then compare
    # its output against the independent fixture; do not fabricate a saved body.
    with patch.object(emlis_question, '_original_source_meaning_plan', legacy):
        yield


def set_source(qdb, user, parent, with_unknown, tier='free'):
    qdb.query('update public.emotions set memo=$2 where id=$1',
              [parent, source_row(with_unknown)['memo']])
    qdb.query('update public.profiles set subscription_tier=$2 where id=$1', [user, tier])


def events(stored, kind):
    return [event for event in stored['events'] if event['kind'] == kind]


def record_operation_times(stored, label):
    """Report actual SQL timestamps without changing the real 30-second limit."""
    for observation in events(stored, 'OBSERVATION'):
        started = next(event for event in events(stored, 'OPERATION')
                       if event['attempt_id'] == observation['attempt_id']
                       and event['payload'].get('status') == 'RUNNING')
        elapsed = (datetime.fromisoformat(observation['recorded_at'])
                   - datetime.fromisoformat(started['recorded_at'])).total_seconds()
        print(f"DELIVERY_TIMING {label} {observation['payload']['stage']} {elapsed:.3f}s")


def assert_current_body(dto, stage, with_unknown):
    assert dto['current_observation'] is not None, dto
    body = dto['current_observation']['text']
    observation, reception = body.split('Emlisから：', 1)
    assert reception.count(PAIR) == 1
    assert 'かもしれない' in observation and 'かもしれない' not in reception
    assert reception.count(UNKNOWN) == int(with_unknown)
    assert ('何が不安なのか、私にもまだわからない' in observation) == with_unknown
    assert len([part for part in reception.split('。') if part.strip()]) <= (3 if with_unknown else 2)

    if stage == 'withdraw_event':
        assert '褒められた' not in body
        assert '嬉しくなかった' in reception
        return
    assert '褒められた' in reception
    if stage == 'withdraw_reaction':
        assert '嬉しくなかった' not in body
        assert '嬉し' not in reception and '悲し' not in reception
        return
    if stage == 'revise':
        assert '嬉しくなかった' not in body
        assert '悲し' in reception
        assert 'その時' in reception or '褒められた時' in reception
        return

    assert '嬉しくなかった' in observation
    assert any(value in reception for value in
               ('嬉しくなかった', '嬉しさを伴わない', '嬉しさにはつながらなかった'))
    if stage in ('add', 'add_negative'):
        assert '回答した時点' in reception
        assert ('嬉しい' if stage == 'add' else '嬉しくない') in reception
    elif stage in ('add_past', 'add_past_negative'):
        assert 'その時' in reception
        assert ('嬉しかった' if stage == 'add_past' else '悲しくなかった') in reception


def assert_history(dto, stage, with_unknown, first=None):
    assert dto['original']['memo'] == source_row(with_unknown)['memo']
    observations = [event for event in dto['timeline'] if event['kind'] == 'OBSERVATION']
    questions = [event for event in dto['timeline'] if event['kind'] == 'QUESTION']
    answers = [event for event in dto['timeline'] if event['kind'] == 'ANSWER']
    assert len(questions) == dto['issued_count'] == 1
    assert questions[0]['text'] == source_row(with_unknown)['q3']['question']['prompt_private']
    assert observations[-1]['text'] == dto['current_observation']['text']
    if stage == 'initial':
        assert dto['state'] == 'AWAITING_ANSWER' and dto['body_state'] == 'PRE_QUESTION'
        assert dto['pending_question'] == questions[0]
        assert len(observations) == 1 and answers == []
    else:
        assert dto['state'] == 'COMPLETED' and dto['body_state'] == 'REFINED', dto
        assert dto['pending_question'] is None and not dto['can_continue']
        assert dto['answer_saved'] and dto['meaning_updated']
        assert len(observations) == 2 and len(answers) == 1
        assert answers[0]['text'] == update_row(stage, with_unknown)['answer']
        assert answers[0]['question_id'] == questions[0]['question_id']
        assert first is not None and dto['original'] == first['original']
        assert observations[0]['text'] == first['current_observation']['text']


@pytest.mark.parametrize('with_unknown', [False, True], ids=['plain', 'unknown'])
@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
def test_initial_received_is_saved_with_the_existing_question(qcase, qdb, with_unknown, tier):
    user, parent, service = qcase
    set_source(qdb, user, parent, with_unknown, tier)
    saved = run(service.start(user, parent))
    assert_current_body(saved, 'initial', with_unknown)
    assert_history(saved, 'initial', with_unknown)
    assert saved['question_limit'] == (3 if tier == 'premium' else 1)
    record_operation_times(run(service.store.read(user, input_id=parent)),
                           f'initial-{with_unknown}-{tier}')
    reopen(user, parent, saved)
    export_dto(f'relief-received-initial-{with_unknown}-{tier}', saved)


@pytest.mark.parametrize('with_unknown', [False, True], ids=['plain', 'unknown'])
@pytest.mark.parametrize('stage', STAGES)
def test_one_actual_answer_retains_only_the_valid_experience(qcase, qdb, with_unknown, stage):
    user, parent, service = qcase
    set_source(qdb, user, parent, with_unknown)
    first = run(service.start(user, parent))
    assert_current_body(first, 'initial', with_unknown)
    text, key = update_row(stage, with_unknown)['answer'], f'u350-{stage}-{with_unknown}'
    saved = run(answer(service, user, first, text, key))
    assert_current_body(saved, stage, with_unknown)
    assert_history(saved, stage, with_unknown, first)
    before = run(service.store.read(user, input_id=parent))
    record_operation_times(before, f'{stage}-{with_unknown}')
    assert len(events(before, 'MEANING_UPDATE')) == len(events(before, 'OBSERVATION')) == 2
    assert len(events(before, 'ANSWER')) == 1
    assert events(before, 'OBSERVATION')[-1]['payload']['meaning_checkpoint_ref'] == events(before, 'MEANING_UPDATE')[-1]['payload']['checkpoint_id']
    with patch.object(service.engine, 'generate', side_effect=AssertionError('idempotent replay must not regenerate')):
        replay = run(answer(service, user, first, text, key))
    assert replay['current_observation'] == saved['current_observation']
    assert replay['timeline'] == saved['timeline']
    assert run(service.store.read(user, input_id=parent))['events'] == before['events']
    reopen(user, parent, saved)
    export_dto(f'relief-received-current-{stage}-{with_unknown}', saved)


@pytest.mark.parametrize('with_unknown', [False, True], ids=['plain', 'unknown'])
@pytest.mark.parametrize('stage', ['initial', 'add'])
def test_completed_u348_body_is_never_regenerated(qcase, qdb, with_unknown, stage):
    user, parent, service = qcase
    set_source(qdb, user, parent, with_unknown)
    with original_u348():
        first = run(service.start(user, parent))
        assert first['current_observation']['text'] == frozen_text('initial', with_unknown)
        saved = (first if stage == 'initial' else run(answer(service, user, first,
            update_row(stage, with_unknown)['answer'], 'u350-old-completed')))
    assert saved['current_observation']['text'] == frozen_text(stage, with_unknown)
    assert_history(saved, stage, with_unknown, first)
    reopen(user, parent, saved)
    export_dto(f'relief-received-old-completed-{stage}-{with_unknown}', saved)


def interrupted(*_):
    raise asyncio.CancelledError()


def forbid_reprepare(*_):
    pytest.fail('saved meaning must be reused')


def retry(service, user, pending, key):
    return run(service.action(user, pending['thread_id'], action='retry_response',
        expected_revision=pending['revision'], idempotency_key=key,
        operation_id=pending['operation_id']))


@pytest.mark.parametrize('with_unknown', [False, True], ids=['plain', 'unknown'])
@pytest.mark.parametrize('stage', ['initial', 'withdraw_reaction'])
def test_saved_u348_checkpoint_resumes_exact_old_selection(qcase, qdb, monkeypatch, with_unknown, stage):
    user, parent, service = qcase
    set_source(qdb, user, parent, with_unknown)
    first, generate = None, service.engine.generate
    with original_u348():
        if stage != 'initial':
            first = run(service.start(user, parent))
            assert first['current_observation']['text'] == frozen_text('initial', with_unknown)
        monkeypatch.setattr(service.engine, 'generate', interrupted)
        with pytest.raises(asyncio.CancelledError):
            if stage == 'initial':
                run(service.start(user, parent))
            else:
                run(answer(service, user, first, update_row(stage, with_unknown)['answer'], 'u350-old-pending'))
    pending = run(service.get(user, parent))
    assert pending['failure_code'] == 'worker_interrupted' and pending['can_retry']
    before = run(service.store.read(user, input_id=parent))
    meanings = events(before, 'MEANING_UPDATE')
    assert len(meanings) == (1 if stage == 'initial' else 2)
    monkeypatch.setattr(service.engine, 'generate', generate)
    monkeypatch.setattr(service.engine, 'prepare_emlis_update', forbid_reprepare)
    saved = retry(service, user, pending, 'u350-old-retry')
    after = run(service.store.read(user, input_id=parent))
    assert events(after, 'MEANING_UPDATE') == meanings
    assert saved['operation_id'] == pending['operation_id']
    assert saved['current_observation']['text'] == frozen_text(stage, with_unknown)
    assert_history(saved, stage, with_unknown, first)
    reopen(user, parent, saved)
    export_dto(f'relief-received-old-checkpoint-{stage}-{with_unknown}', saved)


@pytest.mark.parametrize('stage,with_unknown', [('initial', False), ('add', True)])
@pytest.mark.parametrize('after_checkpoint', [False, True], ids=['before_meaning', 'after_meaning'])
def test_current_interruption_preserves_one_meaning_and_answer(qcase, qdb, monkeypatch,
                                                            stage, with_unknown, after_checkpoint):
    user, parent, service = qcase
    set_source(qdb, user, parent, with_unknown)
    first = run(service.start(user, parent)) if stage != 'initial' else None
    prepare, generate = service.engine.prepare_emlis_update, service.engine.generate
    monkeypatch.setattr(service.engine, 'generate', interrupted)
    if not after_checkpoint:
        monkeypatch.setattr(service.engine, 'prepare_emlis_update', interrupted)
    with pytest.raises(asyncio.CancelledError):
        if stage == 'initial':
            run(service.start(user, parent))
        else:
            run(answer(service, user, first, update_row(stage, with_unknown)['answer'], 'u350-current-pending'))
    pending = run(service.get(user, parent))
    assert pending['failure_code'] == 'worker_interrupted' and pending['can_retry']
    before = run(service.store.read(user, input_id=parent))
    meanings, previous = events(before, 'MEANING_UPDATE'), int(stage != 'initial')
    assert len(meanings) == previous + int(after_checkpoint)
    monkeypatch.setattr(service.engine, 'generate', generate)
    monkeypatch.setattr(service.engine, 'prepare_emlis_update', forbid_reprepare if after_checkpoint else prepare)
    saved = retry(service, user, pending, 'u350-current-retry')
    after = run(service.store.read(user, input_id=parent))
    current, observations = events(after, 'MEANING_UPDATE'), events(after, 'OBSERVATION')
    assert len(current) == len(observations) == previous + 1
    assert current == meanings if after_checkpoint else current[:previous] == meanings
    assert observations[-1]['payload']['meaning_checkpoint_ref'] == current[-1]['payload']['checkpoint_id']
    assert len(events(after, 'ANSWER')) == previous
    assert saved['operation_id'] == pending['operation_id']
    assert_current_body(saved, stage, with_unknown)
    assert_history(saved, stage, with_unknown, first)
    reopen(user, parent, saved)
    export_dto(f'relief-received-current-retry-{stage}-{with_unknown}-{after_checkpoint}', saved)


@pytest.mark.parametrize('with_unknown', [False, True], ids=['plain', 'unknown'])
@pytest.mark.parametrize('name,text', [
    ('unknown_answer', 'まだわからない。'),
    ('repeated_feeling', 'その時は嬉しくなかった。'),
])
def test_no_material_update_reuses_full_initial_body(qcase, qdb, with_unknown, name, text):
    user, parent, service = qcase
    set_source(qdb, user, parent, with_unknown)
    first = run(service.start(user, parent))
    assert_current_body(first, 'initial', with_unknown)
    before = run(service.store.read(user, input_id=parent))
    old_meanings, old_observations = events(before, 'MEANING_UPDATE'), events(before, 'OBSERVATION')
    assert len(old_meanings) == len(old_observations) == 1
    with patch.object(service.engine, 'generate', side_effect=AssertionError('unchanged body must not regenerate')) as generate:
        saved = run(answer(service, user, first, text, 'u350-no-material-' + name))
        generate.assert_not_called()
    after = run(service.store.read(user, input_id=parent))
    meanings, answers, observations = events(after, 'MEANING_UPDATE'), events(after, 'ANSWER'), events(after, 'OBSERVATION')
    assert meanings[:1] == old_meanings and len(meanings) == 2
    assert observations == old_observations
    assert len(answers) == 1 and answers[0]['payload']['source']['answer_text_private'] == text
    assert answers[0]['question_id'] == first['pending_question']['question_id']
    assessment = meanings[-1]['payload']
    assert assessment['checkpoint_id'] != old_meanings[0]['payload']['checkpoint_id']
    assert assessment['assessment_status'] == 'RESOLVED'
    assert assessment['answer_update']['disposition'] == 'NO_MATERIAL_UPDATE'
    assert assessment['answer_update']['updates'] == []
    assert assessment['accepted_update_refs'] == assessment['inactive_claim_refs'] == assessment['unresolved_parts'] == []
    assert assessment['answer_update']['new_meaning_ref'] == assessment['base_meaning_ref']
    assert assessment['base_meaning_ref'] == old_observations[0]['payload']['effective_plan_ref']
    assert after['thread']['current_meaning_event_id'] == meanings[-1]['id']
    assert after['thread']['latest_answer_event_id'] == answers[0]['id']
    assert after['thread']['last_observation_event_id'] == old_observations[0]['id']
    assert saved['state'] == 'COMPLETED' and saved['body_state'] == 'UNCHANGED'
    assert saved['answer_saved'] and not saved['meaning_updated']
    assert saved['answer_assessment'] == 'RESOLVED'
    assert saved['current_observation'] == first['current_observation']
    assert saved['original'] == first['original']
    assert saved['issued_count'] == 1 and saved['pending_question'] is None and not saved['can_continue']
    assert [event['kind'] for event in saved['timeline']] == ['OBSERVATION', 'QUESTION', 'ANSWER']
    assert_current_body(saved, 'initial', with_unknown)
    reopen(user, parent, saved)
    export_dto(f'relief-received-no-material-{name}-{with_unknown}', saved)
