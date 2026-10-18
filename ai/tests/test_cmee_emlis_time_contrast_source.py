"""Bounded source contrasts preserve full prior meanings and saved delivery."""
import asyncio
from dataclasses import replace
import json
import os
from pathlib import Path
import re
from unittest.mock import patch

import pytest
import emlis_ai_grounded_sentence_surface as surface
from cocolon_meaning_experience_engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.emlis_answer_update import (
    prepare_emlis_meaning, build_updated_grounded_plan, _prepare_emlis_meaning_from_plan)
from cocolon_meaning_experience_engine.emlis_question import original_meaning_plan
from cocolon_meaning_experience_engine.emlis_thread_source import admit_emlis_thread
from cocolon_meaning_experience_engine.emlis_thread_projection import project_thread_meaning
from test_cmee_emlis_source_scope_regressions import request
from test_cmee_emlis_q1_thread import initial
from test_cmee_emlis_received_discourse import actual
from test_cmee_emlis_detached_observation import read_body
from test_cmee_emlis_contrast_degree import encoded, digest, NoGeneration
from test_emlis_q3_application import qdb, qcase
from test_emlis_q2_application import run


SOURCE_COMMIT = 'b27f22047250fe5a508b0fb28e9ae0b49788a2c7'
FIXTURES = Path(__file__).parent / 'fixtures'
BASELINES = {
    family: json.loads((FIXTURES / filename).read_text())
    for family, filename in (
        ('past_then', 'cmee_emlis_u342_past_then_v1.json'),
        ('inline', 'cmee_emlis_u342_inline_contrast_v1.json'),
    )
}
CASES = [
    pytest.param(family, row, id=f"{family}-{row['case']}")
    for family, baseline in BASELINES.items() for row in baseline['cases']
]

# These expected clauses are independently written from the source memos. They
# must survive in both body sections with their owner, polarity and degree.
EXPECTED = {
    ('past_then', 'past_then'): ('今は疲れている', 'その時は友達と話せて嬉しかった'),
    ('past_then', 'past_then_demo'): ('今日は疲れている', 'その時は友達と話せて嬉しかった'),
    ('past_then', 'past_then_negative'): ('今は疲れている', 'その時は友達と話せて嬉しくなかった'),
    ('past_then', 'past_then_degree'): ('今はとても疲れている', 'その時は友達と話せてとても嬉しかった'),
    ('past_then', 'past_then_hiragana'): ('今は疲れている', 'その時は友達と話せてうれしかった'),
    ('past_then', 'past_then_also'): ('今日も疲れている', 'その時も友達と話せて嬉しかった'),
    ('past_then', 'past_then_punctuation'): ('今は疲れている', 'その時は友達と話せて嬉しかった'),
    ('past_then', 'past_then_forward'): ('その時は友達と話せて嬉しかった', '今は疲れている'),
    ('past_then', 'now'): ('今は疲れている', '昨日は友達と話せて嬉しかった'),
    ('inline', 'shikashi'): ('今は疲れている', '昨日は友達と話せて嬉しかった'),
    ('inline', 'shikashi_negative'): ('今日は疲れている', '昨日は友達と話せて嬉しくなかった'),
    ('inline', 'shikashi_degree'): ('今はとても疲れている', '昨日は友達と話せてとても嬉しかった'),
    ('inline', 'shikashi_hiragana'): ('今は疲れている', '昨日は友達と話せてうれしかった'),
    ('inline', 'shikashi_no_comma'): ('今は疲れている', '昨日は友達と話せて嬉しかった'),
    ('inline', 'shikashi_forward'): ('昨日は友達と話せて嬉しかった', '今は疲れている'),
    ('inline', 'shikashi_then'): ('今は疲れている', 'その時は友達と話せて嬉しかった'),
    ('inline', 'shikashi_then_forward'): ('その時は友達と話せて嬉しかった', '今は疲れている'),
}


def with_checkpoint(req, checkpoint):
    return replace(req, emlis_thread=replace(
        req.emlis_thread, prepared_meaning_checkpoint_ref=checkpoint))


def assert_source_unchanged(prepared, frozen):
    assert prepared.thread.source_prefix_ref == frozen['source_prefix']
    assert encoded(prepared.thread.original.evidence_spans) == frozen['spans']


def assert_projection_matches(prepared, plan, frozen):
    if 'projection_error' in frozen:
        with pytest.raises(ValueError, match='^' + re.escape(frozen['projection_error']) + '$'):
            project_thread_meaning(prepared, plan)
    else:
        selected = project_thread_meaning(prepared, plan).selected_reception
        assert digest(selected) == frozen['selected_sha']


def assert_whole_meaning_matches(prepared, plan, frozen):
    assert digest(prepared.checkpoint) == frozen['checkpoint_sha']
    assert prepared.checkpoint.checkpoint_id == frozen['checkpoint_id']
    assert digest(plan) == frozen['plan_sha']
    assert encoded(plan.nuclei) == frozen['nuclei']
    assert encoded(plan.relations) == frozen['relations']
    assert_source_unchanged(prepared, frozen)
    assert_projection_matches(prepared, plan, frozen)


def assert_delivery_matches(out, frozen):
    assert digest(out.artifact) == frozen['artifact_sha']
    assert (out.artifact.text if out.artifact else None) == frozen['body']
    assert encoded(out.question) == frozen['question']
    assert encoded(out.question_decision) == frozen['question_decision']
    assert list(out.reason_codes) == frozen['reasons']


@pytest.mark.parametrize('q1', [False, True], ids=['q3', 'q1'])
@pytest.mark.parametrize('family,row', CASES)
def test_current_source_repair_is_bounded_and_new_checkpoint_roundtrips(family, row, q1):
    assert BASELINES[family]['source_commit'] == SOURCE_COMMIT
    frozen = row['q1' if q1 else 'q3']
    req = (initial if q1 else request)(row['memo'])
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    assert_source_unchanged(prepared, frozen)
    out = MeaningExperienceEngine().generate(req)
    if (family, row['case']) not in EXPECTED:
        assert_whole_meaning_matches(prepared, plan, frozen)
        assert_delivery_matches(out, frozen)
        return

    assert prepared.checkpoint.checkpoint_id != frozen['checkpoint_id']
    assert not prepared.legacy_time_contrast_source
    left, right = EXPECTED[family, row['case']]
    assert out.artifact is not None
    assert out.artifact.observation == f'「{left}」の一方で「{right}」とあります。'
    assert out.artifact.reception == (
        f'{left}ことと{right}ことの両方を、その違いも含めて小さくせずに受け止めています。')
    assert out.question is None and out.question_decision.disposition == 'END'
    assert not out.automatic_progression
    restored_req = with_checkpoint(req, prepared.checkpoint.checkpoint_id)
    restored = prepare_emlis_meaning(restored_req)
    restored_plan = build_updated_grounded_plan(restored)
    assert digest(restored.checkpoint) == digest(prepared.checkpoint)
    assert digest(restored_plan) == digest(plan)
    assert_source_unchanged(restored, frozen)
    assert digest(project_thread_meaning(restored, restored_plan).selected_reception) == digest(
        project_thread_meaning(prepared, plan).selected_reception)
    restored_out = MeaningExperienceEngine().generate(restored_req)
    assert restored_out.artifact == out.artifact
    assert restored_out.question == out.question
    assert restored_out.question_decision == out.question_decision
    assert restored_out.reason_codes == out.reason_codes


@pytest.mark.parametrize('q1', [False, True], ids=['q3', 'q1'])
@pytest.mark.parametrize('family,row', CASES)
def test_u342_checkpoint_restores_whole_meaning_and_delivery(family, row, q1):
    assert BASELINES[family]['source_commit'] == SOURCE_COMMIT
    frozen = row['q1' if q1 else 'q3']
    fresh_req = (initial if q1 else request)(row['memo'])
    assert digest(old_prepare(fresh_req)) == frozen['checkpoint_sha']
    req = with_checkpoint(fresh_req, frozen['checkpoint_id'])
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    assert prepared.legacy_time_contrast_source == ((family, row['case']) in EXPECTED)
    assert_whole_meaning_matches(prepared, plan, frozen)
    assert_delivery_matches(MeaningExperienceEngine().generate(req), frozen)


@pytest.fixture(scope='module', params=[
    ('past_then', 'past_then_degree'), ('inline', 'shikashi_negative')],
    ids=['then_degree', 'inline_negative'])
def context(request):
    family, name = request.param
    row = next(r for r in BASELINES[family]['cases'] if r['case'] == name)
    return actual(request=initial(row['memo']))


@pytest.mark.parametrize('mutation', [
    'observation_time', 'reception_time', 'degree_or_polarity', 'owner',
    'blocked_attempt', 'cause', 'simultaneous', 'missing_operand',
    'reverse_times', 'extra_claim'])
def test_independent_body_reader_preserves_source_contrast_without_author(context, mutation):
    artifact = context[0].artifact
    observation, reception = artifact.observation, artifact.reception
    past = 'その時' if 'その時' in observation else '昨日'
    present = '今日' if '今日' in observation else '今'
    if mutation == 'observation_time':
        observation = observation.replace(past, '明日')
    elif mutation == 'reception_time':
        reception = reception.replace(present, '明日')
    elif mutation == 'degree_or_polarity':
        reception = (reception.replace('とても', '', 1) if 'とても' in reception
            else reception.replace('嬉しくなかった', '嬉しかった'))
    elif mutation == 'owner':
        reception = reception.replace('友達と', '友達が')
    elif mutation == 'blocked_attempt':
        observation = observation.replace('の一方で', 'が妨げたため')
    elif mutation == 'cause':
        observation = observation.replace('の一方で', 'が原因で')
    elif mutation == 'simultaneous':
        observation = '同時に、' + observation
    elif mutation == 'missing_operand':
        reception = reception.split('ことと', 1)[1]
    elif mutation == 'reverse_times':
        observation = observation.replace(present, 'TIME_SWAP').replace(
            past, present).replace('TIME_SWAP', past)
    else:
        reception += 'だから疲れは必ずなくなります。'
    changed = artifact.text.replace(artifact.observation, observation).replace(
        artifact.reception, reception)
    assert changed != artifact.text
    with patch.object(surface, '_realize_line', side_effect=AssertionError('no surface oracle')):
        assert read_body(context, artifact.text).passed
        assert not read_body(context, changed).passed


def old_prepare(req):
    thread = admit_emlis_thread(req)
    return _prepare_emlis_meaning_from_plan(req, thread,
        original_meaning_plan(thread, _legacy_time_contrast_source=True)).checkpoint


def test_saved_old_completed_time_wording_is_never_regenerated(qcase, qdb, monkeypatch):
    from emlis_thread_service import EmlisThreadService, Q3_PROFILE
    user, parent, service = qcase
    row = next(r for r in BASELINES['past_then']['cases'] if r['case'] == 'past_then_forward')
    qdb.query('update public.emotions set memo=$2 where id=$1', [parent, row['memo']])
    monkeypatch.setattr(service.engine, 'prepare_emlis_update', old_prepare)
    saved = run(service.start(user, parent))
    assert saved['state'] == 'COMPLETED' and saved['body_state'] == 'FINAL'
    assert saved['current_observation']['text'] == row['q3']['body']
    assert '同時' in saved['current_observation']['text']
    assert saved['pending_question'] is None and not saved['can_continue']
    reader = EmlisThreadService(runtime_profile=Q3_PROFILE, engine=NoGeneration())
    assert run(reader.get(user, parent)) == saved and run(reader.start(user, parent)) == saved
    export_dto('old-complete-past_then_forward', saved)


def export_dto(name, dto):
    if folder := os.environ.get('CMEE_TIME_CONTRAST_DTO_DIR'):
        Path(folder).mkdir(parents=True, exist_ok=True)
        Path(folder, name + '.json').write_text(json.dumps(dto, ensure_ascii=False))


def sql_case(case):
    family = 'past_then' if case == 'past_then' else 'inline'
    return next(r for r in BASELINES[family]['cases'] if r['case'] == case)


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
@pytest.mark.parametrize('case', ['past_then', 'shikashi'])
@pytest.mark.parametrize('historical', [False, True], ids=['current', 'old_unavailable'])
def test_saved_new_body_and_old_unavailable_reopen_without_generation(
        qcase, qdb, monkeypatch, tier, case, historical):
    from emlis_thread_service import EmlisThreadService, Q3_PROFILE
    user, parent, service = qcase
    row = sql_case(case)
    qdb.query('update public.profiles set subscription_tier=$2 where id=$1', [user, tier])
    qdb.query('update public.emotions set memo=$2 where id=$1', [parent, row['memo']])
    if historical:
        monkeypatch.setattr(service.engine, 'prepare_emlis_update', old_prepare)
    saved = run(service.start(user, parent))
    if historical:
        assert saved['state'] == 'RESPONSE_FAILED' and saved['failure_code'] == 'body_not_validated'
        assert saved['current_observation'] is None and not saved['can_retry']
    else:
        assert saved['state'] == 'COMPLETED' and saved['body_state'] == 'FINAL'
        assert 'の一方で' in saved['current_observation']['text']
        assert '同時' not in saved['current_observation']['text']
    assert saved['pending_question'] is None and not saved['can_continue']
    assert not any(e['kind'] in {'QUESTION', 'ANSWER'} for e in saved['timeline'])
    reader = EmlisThreadService(runtime_profile=Q3_PROFILE, engine=NoGeneration())
    assert run(reader.get(user, parent)) == saved
    assert run(reader.start(user, parent)) == saved
    export_dto(f'{tier}-{case}-{historical}', saved)


@pytest.mark.parametrize('case', ['past_then', 'shikashi'])
@pytest.mark.parametrize('after_checkpoint', [False, True], ids=['before_meaning', 'after_old_meaning'])
def test_confirmed_initial_interruption_preserves_the_checkpoint_boundary(
        qcase, qdb, monkeypatch, case, after_checkpoint):
    from emlis_thread_service import EmlisThreadService, Q3_PROFILE
    user, parent, service = qcase
    row = sql_case(case)
    qdb.query('update public.emotions set memo=$2 where id=$1', [parent, row['memo']])
    original_prepare = service.engine.prepare_emlis_update
    original_generate = service.engine.generate

    def interrupted(*_):
        raise asyncio.CancelledError()

    monkeypatch.setattr(service.engine, 'prepare_emlis_update', old_prepare if after_checkpoint else interrupted)
    monkeypatch.setattr(service.engine, 'generate', interrupted)
    with pytest.raises(asyncio.CancelledError):
        run(service.start(user, parent))
    pending = run(service.get(user, parent))
    assert pending['failure_code'] == 'worker_interrupted' and pending['can_retry']
    before = run(service.store.read(user, input_id=parent))
    meanings = [e for e in before['events'] if e['kind'] == 'MEANING_UPDATE']
    assert len(meanings) == int(after_checkpoint)
    monkeypatch.setattr(service.engine, 'generate', original_generate)
    monkeypatch.setattr(service.engine, 'prepare_emlis_update',
        (lambda *_: pytest.fail('saved checkpoint must be reused')) if after_checkpoint else original_prepare)
    done = run(service.action(user, pending['thread_id'], action='retry_response',
        expected_revision=pending['revision'], idempotency_key='u343-confirmed-retry',
        operation_id=pending['operation_id']))
    after = run(service.store.read(user, input_id=parent))
    current = [e for e in after['events'] if e['kind'] == 'MEANING_UPDATE']
    assert len(current) == 1 and done['operation_id'] == pending['operation_id']
    if after_checkpoint:
        assert current == meanings
        assert done['current_observation'] is None and done['failure_code'] == 'body_not_validated'
    else:
        assert done['state'] == 'COMPLETED' and done['current_observation']
        observation, = (e for e in after['events'] if e['kind'] == 'OBSERVATION')
        assert observation['payload']['meaning_checkpoint_ref'] == current[0]['payload']['checkpoint_id']
    reader = EmlisThreadService(runtime_profile=Q3_PROFILE, engine=NoGeneration())
    assert run(reader.get(user, parent)) == done
    assert run(reader.start(user, parent)) == done
    export_dto(f'retry-{case}-{after_checkpoint}', done)
