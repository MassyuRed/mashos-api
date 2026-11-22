"""Mixed-source unknown reception survives actual SQL storage and versioned retry."""
import asyncio
from contextlib import contextmanager
import json
from pathlib import Path
from unittest.mock import patch

import pytest
from cocolon_meaning_experience_engine import emlis_question
from test_cmee_emlis_loneliness_delivery import export_dto, reopen
from test_emlis_q3_application import qdb, qcase
from test_emlis_q2_application import run, answer


BASELINE = json.loads((Path(__file__).parent /
    'fixtures/cmee_emlis_u347_mixed_unknown_v1.json').read_text())
ROWS = {row['case']: row for row in BASELINE['cases']}
UPDATES = {row['case']: row for row in BASELINE['updates']}
MEMO = ROWS['mixed']['memo']
UNKNOWN = '何が不安なのか、あなたにもまだわからないのですね。'
STAGES = ('initial', 'add', 'revise', 'withdraw')


def frozen_text(stage):
    artifact = (ROWS['mixed'] if stage == 'initial' else UPDATES[stage])['q3']['artifact']
    assert artifact is not None
    return f"見えたこと：\n{artifact['observation']}\n\nEmlisから：\n{artifact['reception']}"


@contextmanager
def original_u347():
    original = emlis_question._original_source_meaning_plan

    def legacy(source, **kwargs):
        kwargs['_legacy_mixed_relief_unknown'] = True
        return original(source, **kwargs)

    # Reproduce the source version, not a fabricated persisted body. Every
    # completed result below must match the independent frozen u347 text.
    with patch.object(emlis_question, '_original_source_meaning_plan', legacy):
        yield


def set_memo(qdb, parent):
    qdb.query('update public.emotions set memo=$2 where id=$1', [parent, MEMO])


def assert_current_body(dto, stage):
    body = dto['current_observation']['text']
    observation, reception = body.split('Emlisから：', 1)
    assert '何が不安なのか、私にもまだわからない' in observation
    assert reception.count(UNKNOWN) == 1
    assert 'かもしれない' in observation and 'かもしれない' not in reception
    assert 'ほっとしたと聞いて、私も少し安心しましたが、その寂しさにも、今、耳を傾けていたいです。' in reception
    if stage == 'initial':
        assert '褒められた' in observation and '嬉しくなかった' in observation
        assert '褒められた' not in reception
    elif stage == 'add':
        assert '褒められたことについて、回答した時点では嬉しいのですね。' in reception
    elif stage == 'revise':
        assert '褒められたことについて、その時の悲しさに目が留まり、それを小さくせずに受け止めています。' in reception
        assert '嬉しくなかった' not in body
    else:
        assert 'その時は嬉しくなかったのですね。' in reception
        assert '褒められた' not in body


def assert_history(dto, stage, first=None):
    assert dto['original']['memo'] == MEMO
    observations = [event for event in dto['timeline'] if event['kind'] == 'OBSERVATION']
    questions = [event for event in dto['timeline'] if event['kind'] == 'QUESTION']
    answers = [event for event in dto['timeline'] if event['kind'] == 'ANSWER']
    assert len(questions) == dto['issued_count'] == 1
    assert questions[0]['text'] == ROWS['mixed']['q3']['question']['prompt_private']
    assert observations[-1]['text'] == dto['current_observation']['text']
    if stage == 'initial':
        assert dto['state'] == 'AWAITING_ANSWER' and dto['body_state'] == 'PRE_QUESTION'
        assert dto['pending_question'] == questions[0]
        assert len(observations) == 1 and answers == []
    else:
        assert dto['state'] == 'COMPLETED' and dto['body_state'] == 'REFINED'
        assert dto['pending_question'] is None and not dto['can_continue']
        assert dto['answer_saved'] and dto['meaning_updated']
        assert len(observations) == 2 and len(answers) == 1
        assert answers[0]['text'] == UPDATES[stage]['answer']
        assert answers[0]['question_id'] == questions[0]['question_id']
        assert first is not None and dto['original'] == first['original']
        assert observations[0]['text'] == first['current_observation']['text']


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
def test_current_initial_unknown_and_existing_question_are_saved(qcase, qdb, tier):
    user, parent, service = qcase
    set_memo(qdb, parent)
    qdb.query('update public.profiles set subscription_tier=$2 where id=$1', [user, tier])
    saved = run(service.start(user, parent))
    assert_current_body(saved, 'initial')
    assert_history(saved, 'initial')
    reopen(user, parent, saved)
    export_dto('mixed-unknown-initial-' + tier, saved)


@pytest.mark.parametrize('stage', STAGES[1:])
def test_current_one_update_keeps_unknown_and_its_separate_answer(qcase, qdb, stage):
    user, parent, service = qcase
    set_memo(qdb, parent)
    first = run(service.start(user, parent))
    assert_current_body(first, 'initial')
    saved = run(answer(service, user, first, UPDATES[stage]['answer'], 'u348-' + stage))
    assert_current_body(saved, stage)
    assert_history(saved, stage, first)
    reopen(user, parent, saved)
    export_dto('mixed-unknown-current-' + stage, saved)


@pytest.mark.parametrize('stage', STAGES)
def test_completed_u347_text_is_not_regenerated(qcase, qdb, stage):
    user, parent, service = qcase
    set_memo(qdb, parent)
    with original_u347():
        first = run(service.start(user, parent))
        assert first['current_observation']['text'] == frozen_text('initial')
        saved = (first if stage == 'initial' else
            run(answer(service, user, first, UPDATES[stage]['answer'], 'u348-old-' + stage)))
    assert saved['current_observation']['text'] == frozen_text(stage)
    assert_history(saved, stage, first)
    reopen(user, parent, saved)
    export_dto('mixed-unknown-old-completed-' + stage, saved)


@pytest.mark.parametrize('stage', ['initial', 'withdraw'])
def test_saved_u347_checkpoint_resumes_its_exact_old_body(qcase, qdb, monkeypatch, stage):
    user, parent, service = qcase
    set_memo(qdb, parent)
    first = None
    generate = service.engine.generate
    with original_u347():
        if stage != 'initial':
            first = run(service.start(user, parent))
            assert first['current_observation']['text'] == frozen_text('initial')
        monkeypatch.setattr(service.engine, 'generate', interrupted)
        with pytest.raises(asyncio.CancelledError):
            if stage == 'initial':
                run(service.start(user, parent))
            else:
                run(answer(service, user, first, UPDATES[stage]['answer'], 'u348-old-pending'))
    pending = run(service.get(user, parent))
    assert pending['failure_code'] == 'worker_interrupted' and pending['can_retry']
    before = run(service.store.read(user, input_id=parent))
    meanings = [event for event in before['events'] if event['kind'] == 'MEANING_UPDATE']
    assert len(meanings) == (1 if stage == 'initial' else 2)
    monkeypatch.setattr(service.engine, 'generate', generate)
    monkeypatch.setattr(service.engine, 'prepare_emlis_update', forbid_reprepare)
    saved = retry(service, user, pending, 'u348-old-retry')
    after = run(service.store.read(user, input_id=parent))
    assert [event for event in after['events'] if event['kind'] == 'MEANING_UPDATE'] == meanings
    assert saved['operation_id'] == pending['operation_id']
    assert saved['current_observation']['text'] == frozen_text(stage)
    assert_history(saved, stage, first)
    reopen(user, parent, saved)
    export_dto('mixed-unknown-old-checkpoint-' + stage, saved)


def interrupted(*_):
    raise asyncio.CancelledError()


def forbid_reprepare(*_):
    pytest.fail('saved meaning must be reused')


def retry(service, user, pending, key):
    return run(service.action(user, pending['thread_id'], action='retry_response',
        expected_revision=pending['revision'], idempotency_key=key,
        operation_id=pending['operation_id']))


@pytest.mark.parametrize('stage', ['initial', 'add'])
@pytest.mark.parametrize('after_checkpoint', [False, True], ids=['before_meaning', 'after_meaning'])
def test_current_confirmed_interruption_keeps_one_meaning_and_answer(qcase, qdb, monkeypatch,
                                                                  stage, after_checkpoint):
    user, parent, service = qcase
    set_memo(qdb, parent)
    first = run(service.start(user, parent)) if stage != 'initial' else None
    prepare, generate = service.engine.prepare_emlis_update, service.engine.generate
    monkeypatch.setattr(service.engine, 'generate', interrupted)
    if not after_checkpoint:
        monkeypatch.setattr(service.engine, 'prepare_emlis_update', interrupted)
    with pytest.raises(asyncio.CancelledError):
        if stage == 'initial':
            run(service.start(user, parent))
        else:
            run(answer(service, user, first, UPDATES[stage]['answer'], 'u348-current-pending'))
    pending = run(service.get(user, parent))
    assert pending['failure_code'] == 'worker_interrupted' and pending['can_retry']
    before = run(service.store.read(user, input_id=parent))
    meanings = [event for event in before['events'] if event['kind'] == 'MEANING_UPDATE']
    previous = int(stage != 'initial')
    assert len(meanings) == previous + int(after_checkpoint)
    monkeypatch.setattr(service.engine, 'generate', generate)
    monkeypatch.setattr(service.engine, 'prepare_emlis_update', forbid_reprepare if after_checkpoint else prepare)
    saved = retry(service, user, pending, 'u348-current-retry')
    after = run(service.store.read(user, input_id=parent))
    current = [event for event in after['events'] if event['kind'] == 'MEANING_UPDATE']
    assert len(current) == previous + 1
    if after_checkpoint:
        assert current == meanings
    else:
        assert current[:previous] == meanings
    observations = [event for event in after['events'] if event['kind'] == 'OBSERVATION']
    assert len(observations) == previous + 1
    assert observations[-1]['payload']['meaning_checkpoint_ref'] == current[-1]['payload']['checkpoint_id']
    assert len([event for event in after['events'] if event['kind'] == 'ANSWER']) == previous
    assert saved['operation_id'] == pending['operation_id']
    assert_current_body(saved, stage)
    assert_history(saved, stage, first)
    reopen(user, parent, saved)
    export_dto(f'mixed-unknown-current-retry-{stage}-{after_checkpoint}', saved)


@pytest.mark.parametrize('name,text', [
    ('unknown_answer', 'まだわからない。'),
    ('repeated_feeling', 'その時は嬉しくなかった。'),
])
def test_current_free_no_material_update_reuses_initial_unknown_body(qcase, qdb, name, text):
    user, parent, service = qcase
    set_memo(qdb, parent)
    qdb.query('update public.profiles set subscription_tier=$2 where id=$1', [user, 'free'])
    first = run(service.start(user, parent))
    assert_current_body(first, 'initial')
    assert_history(first, 'initial')
    assert first['question_limit'] == 1
    before = run(service.store.read(user, input_id=parent))
    old_meanings = [event for event in before['events'] if event['kind'] == 'MEANING_UPDATE']
    old_observations = [event for event in before['events'] if event['kind'] == 'OBSERVATION']
    assert len(old_meanings) == len(old_observations) == 1

    with patch.object(service.engine, 'generate', side_effect=AssertionError('unchanged body must not regenerate')) as generate:
        saved = run(answer(service, user, first, text, 'u348-no-material-' + name))
        generate.assert_not_called()

    after = run(service.store.read(user, input_id=parent))
    meanings = [event for event in after['events'] if event['kind'] == 'MEANING_UPDATE']
    answers = [event for event in after['events'] if event['kind'] == 'ANSWER']
    observations = [event for event in after['events'] if event['kind'] == 'OBSERVATION']
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
    assert_current_body(saved, 'initial')
    reopen(user, parent, saved)
    export_dto('mixed-unknown-no-material-' + name, saved)
