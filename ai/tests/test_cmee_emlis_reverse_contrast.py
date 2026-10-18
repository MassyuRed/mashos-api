"""Reverse proximity is not an asserted block; old meanings remain restorable."""
import asyncio
from dataclasses import replace
import json
import os
from pathlib import Path
from unittest.mock import patch
import pytest
import emlis_ai_grounded_observation_plan as gp
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

BASELINE = json.loads((Path(__file__).parent / 'fixtures' /
    'cmee_emlis_u341_reverse_contrast_v1.json').read_text())
IMPROVED = {'reverse', 'hiragana', 'degree_both', 'degree_past',
    'also', 'punctuation', 'negative'}


def with_checkpoint(req, checkpoint):
    return replace(req, emlis_thread=replace(req.emlis_thread, prepared_meaning_checkpoint_ref=checkpoint))


@pytest.mark.parametrize('row', BASELINE['cases'], ids=lambda r: r['case'])
def test_current_repair_changes_only_the_proved_reverse_edge(row):
    assert BASELINE['source_commit'] == 'd663ce22836fd32604788605001d71e8561f7ba2'
    req = request(row['memo']); prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    assert digest(plan.nuclei) == row['nuclei_sha']
    out = MeaningExperienceEngine().generate(req)
    if row['case'] not in IMPROVED:
        assert digest(prepared.checkpoint) == row['checkpoint_sha']
        assert digest(plan) == row['plan_sha']
        assert digest(out.artifact) == row['artifact_sha']
        assert encoded(out.question) == row['question']
        assert encoded(out.question_decision) == row['question_decision']
        assert list(out.reason_codes) == row['reasons']
        if 'projection_error' in row:
            with pytest.raises(ValueError, match=row['projection_error']): project_thread_meaning(prepared, plan)
        else: assert digest(project_thread_meaning(prepared, plan).selected_reception) == row['selected_sha']
        return
    assert prepared.checkpoint.checkpoint_id != row['checkpoint_id']
    before = row['relations']; after = encoded(plan.relations)
    assert len(before) == len(after)
    for old, new in zip(before, after, strict=True):
        if old['type'] == 'attempt_and_block':
            expected = dict(old, type='uncertain_connection', grounding_kind='bounded_structural_inference', retention='should')
            assert new == expected
        else: assert new == old
    edge, = (r for r in plan.relations if r.retention == 'required')
    assert edge.type == 'contrast'
    index = {n.nucleus_id: n for n in plan.nuclei}; resolver = prepared.thread.resolver()
    left, right = (resolver.resolve(index[nid].source_span_ids[0]).raw_text
        for nid in (edge.from_nucleus_id, edge.to_nucleus_id))
    assert out.artifact.observation == f'「{left}」の一方で「{right}」とあります。'
    assert out.artifact.reception == f'{left}ことと{right}ことの両方を、その違いも含めて小さくせずに受け止めています。'
    assert out.question is None and out.question_decision.disposition == 'END'
    assert not out.automatic_progression
    assert MeaningExperienceEngine().generate(with_checkpoint(req, prepared.checkpoint.checkpoint_id)).artifact == out.artifact
    assert MeaningExperienceEngine().generate(initial(row['memo'])).artifact.text == out.artifact.text


@pytest.mark.parametrize('q1', [False, True], ids=['q3', 'q1'])
@pytest.mark.parametrize('row', BASELINE['cases'], ids=lambda r: r['case'])
def test_u341_checkpoint_restores_whole_meaning_and_delivery(row, q1):
    old = row['q1'] if q1 else row
    req = with_checkpoint((initial if q1 else request)(row['memo']), old['checkpoint_id'])
    prepared = prepare_emlis_meaning(req); plan = build_updated_grounded_plan(prepared)
    assert prepared.legacy_reverse_time_contrast == (row['case'] in IMPROVED)
    assert digest(prepared.checkpoint) == old['checkpoint_sha']
    assert digest(plan) == row['plan_sha']
    if 'projection_error' in row:
        with pytest.raises(ValueError, match=row['projection_error']): project_thread_meaning(prepared, plan)
    elif not q1:
        # The frozen selected container belongs to Q3; Q1 has its own source
        # references. Its full checkpoint and public delivery are frozen below.
        assert digest(project_thread_meaning(prepared, plan).selected_reception) == row['selected_sha']
    out = MeaningExperienceEngine().generate(req)
    assert digest(out.artifact) == old['artifact_sha']
    assert encoded(out.question) == old['question']
    assert encoded(out.question_decision) == old['question_decision']
    assert list(out.reason_codes) == old['reasons']


@pytest.fixture(scope='module', params=['degree_both', 'negative'])
def context(request):
    row = next(r for r in BASELINE['cases'] if r['case'] == request.param)
    return actual(request=initial(row['memo']))


@pytest.mark.parametrize('mutation', ['observation_time', 'reception_time', 'degree_or_polarity',
    'owner', 'blocked_attempt', 'cause', 'simultaneous', 'missing_operand', 'reverse_times', 'extra_claim'])
def test_independent_body_reader_keeps_the_original_relation_and_endpoints(context, mutation):
    artifact = context[0].artifact; observation, reception = artifact.observation, artifact.reception
    if mutation == 'observation_time': observation = observation.replace('昨日', '今日')
    elif mutation == 'reception_time': reception = reception.replace('今日は', '')
    elif mutation == 'degree_or_polarity':
        reception = reception.replace('とても', '', 1) if 'とても' in reception else reception.replace('嬉しくなかった', '嬉しかった')
    elif mutation == 'owner': reception = reception.replace('友達と', '友達が')
    elif mutation == 'blocked_attempt': observation = observation.replace('の一方で', 'が妨げたため')
    elif mutation == 'cause': observation = observation.replace('の一方で', 'が原因で')
    elif mutation == 'simultaneous': observation = '同時に、' + observation
    elif mutation == 'missing_operand': reception = reception.split('ことと', 1)[1]
    elif mutation == 'reverse_times': observation = observation.replace('今日', 'TEMP').replace('昨日', '今日').replace('TEMP', '昨日')
    else: reception += 'だから疲れは必ずなくなります。'
    changed = artifact.text.replace(artifact.observation, observation).replace(artifact.reception, reception)
    assert changed != artifact.text
    with patch.object(surface, '_realize_line', side_effect=AssertionError('no surface oracle')):
        assert read_body(context, artifact.text).passed
        assert not read_body(context, changed).passed


@pytest.mark.parametrize('mutation', ['cause', 'result', 'foreign_provenance', 'multiple_provenance',
    'foreign_arc', 'missing_span', 'foreign_endpoint', 'inferred_grounding', 'optional_retention',
    'foreign_marker', 'no_marker', 'extra_required', 'forged_time', 'other_owner',
    'marker_not_contrast', 'marker_not_source'])
def test_source_repair_cannot_downgrade_asserted_or_foreign_relations(mutation):
    row = BASELINE['cases'][0]
    prepared = prepare_emlis_meaning(with_checkpoint(request(row['memo']), row['checkpoint_id']))
    plan = build_updated_grounded_plan(prepared); resolver = prepared.thread.resolver()
    reverse = next(r for r in plan.relations if r.type == 'attempt_and_block')
    contrast = next(r for r in plan.relations if r.type == 'contrast')
    nuclei, relations = plan.nuclei, plan.relations
    if mutation in {'cause', 'result'}: changed = replace(reverse, type='user_stated_' + mutation)
    elif mutation == 'foreign_provenance': changed = replace(reverse, source_relation_ids=('foreign',))
    elif mutation == 'multiple_provenance': changed = replace(reverse, source_relation_ids=('conflict.e2', 'conflict.e3'))
    elif mutation == 'foreign_arc': changed = replace(reverse, source_meaning_arc_keys=('foreign',))
    elif mutation == 'missing_span': changed = replace(reverse, source_span_ids=reverse.source_span_ids[:1])
    elif mutation == 'foreign_endpoint': changed = replace(reverse, from_nucleus_id='foreign')
    elif mutation == 'inferred_grounding': changed = replace(reverse, grounding_kind='bounded_structural_inference')
    elif mutation == 'optional_retention': changed = replace(reverse, retention='should')
    else: changed = reverse
    relations = tuple(changed if r == reverse else r for r in relations)
    if mutation in {'foreign_marker', 'no_marker'}:
        refs = ('evidence_relation_marker:foreign',) if mutation == 'foreign_marker' else ()
        relations = tuple(replace(r, source_relation_ids=refs) if r == contrast else r for r in relations)
    elif mutation == 'extra_required': relations = (*relations, replace(reverse, relation_id='foreign:required'))
    elif mutation in {'forged_time', 'other_owner'}:
        kwargs = {'time_scope': 'present'} if mutation == 'forged_time' else {'actor': 'other'}
        nuclei = tuple(replace(n, semantic_frame=replace(n.semantic_frame, **kwargs)) if n.nucleus_id == reverse.from_nucleus_id else n for n in nuclei)
    spans = resolver.resolve_many(resolver.span_ids)
    if mutation in {'marker_not_contrast', 'marker_not_source'}:
        text = '同時に' if mutation == 'marker_not_contrast' else 'ただ'
        spans = tuple(replace(s, raw_text=text) if s.span_id == 's2' else s for s in spans)
    assert gp._final_source_reverse_time_contrast_relations(nuclei, relations,
        spans, prepared.thread.original.normalized_current_input) == relations


def test_foreign_checkpoint_cannot_choose_the_old_graph():
    row = BASELINE['cases'][0]
    checkpoint = row['checkpoint_id'][:-1] + ('0' if row['checkpoint_id'][-1] != '0' else '1')
    with pytest.raises(ValueError, match='emlis_checkpoint_source_prefix_mismatch'):
        prepare_emlis_meaning(with_checkpoint(request(row['memo']), checkpoint))


def old_prepare(req):
    thread = admit_emlis_thread(req)
    return _prepare_emlis_meaning_from_plan(req, thread,
        original_meaning_plan(thread, _legacy_reverse_time_contrast=True)).checkpoint


def export_dto(name, dto):
    if folder := os.environ.get('CMEE_REVERSE_CONTRAST_DTO_DIR'):
        Path(folder).mkdir(parents=True, exist_ok=True)
        Path(folder, name + '.json').write_text(json.dumps(dto, ensure_ascii=False))


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
@pytest.mark.parametrize('case', ['reverse', 'negative'])
@pytest.mark.parametrize('historical', [False, True], ids=['current', 'old_unavailable'])
def test_saved_new_body_and_old_unavailable_reopen_without_generation(qcase, qdb, monkeypatch, tier, case, historical):
    from emlis_thread_service import EmlisThreadService, Q3_PROFILE
    user, parent, service = qcase
    row = next(r for r in BASELINE['cases'] if r['case'] == case)
    qdb.query('update public.profiles set subscription_tier=$2 where id=$1', [user, tier])
    qdb.query('update public.emotions set memo=$2 where id=$1', [parent, row['memo']])
    if historical: monkeypatch.setattr(service.engine, 'prepare_emlis_update', old_prepare)
    saved = run(service.start(user, parent))
    if historical:
        assert saved['state'] == 'RESPONSE_FAILED' and saved['failure_code'] == 'body_not_validated'
        assert saved['current_observation'] is None and not saved['can_retry']
    else:
        assert saved['state'] == 'COMPLETED' and saved['body_state'] == 'FINAL'
        assert 'の一方で' in saved['current_observation']['text']
        assert '同時' not in saved['current_observation']['text']
    assert saved['pending_question'] is None and not saved['can_continue']
    reader = EmlisThreadService(runtime_profile=Q3_PROFILE, engine=NoGeneration())
    assert run(reader.get(user, parent)) == saved
    assert run(reader.start(user, parent)) == saved
    export_dto(f'{tier}-{case}-{historical}', saved)


@pytest.mark.parametrize('case', ['reverse', 'negative'])
@pytest.mark.parametrize('after_checkpoint', [False, True], ids=['before_meaning', 'after_old_meaning'])
def test_confirmed_initial_interruption_preserves_the_checkpoint_boundary(qcase, qdb, monkeypatch, case, after_checkpoint):
    from emlis_thread_service import EmlisThreadService, Q3_PROFILE
    user, parent, service = qcase
    row = next(r for r in BASELINE['cases'] if r['case'] == case)
    qdb.query('update public.emotions set memo=$2 where id=$1', [parent, row['memo']])
    original_prepare, original_generate = service.engine.prepare_emlis_update, service.engine.generate
    def interrupted(*_): raise asyncio.CancelledError()
    monkeypatch.setattr(service.engine, 'prepare_emlis_update', old_prepare if after_checkpoint else interrupted)
    monkeypatch.setattr(service.engine, 'generate', interrupted)
    with pytest.raises(asyncio.CancelledError): run(service.start(user, parent))
    pending = run(service.get(user, parent))
    assert pending['failure_code'] == 'worker_interrupted' and pending['can_retry']
    before = run(service.store.read(user, input_id=parent))
    meanings = [e for e in before['events'] if e['kind'] == 'MEANING_UPDATE']
    assert len(meanings) == int(after_checkpoint)
    monkeypatch.setattr(service.engine, 'generate', original_generate)
    monkeypatch.setattr(service.engine, 'prepare_emlis_update',
        (lambda *_: pytest.fail('saved checkpoint must be reused')) if after_checkpoint else original_prepare)
    done = run(service.action(user, pending['thread_id'], action='retry_response',
        expected_revision=pending['revision'], idempotency_key='u342-confirmed-retry', operation_id=pending['operation_id']))
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
    assert run(reader.get(user, parent)) == done and run(reader.start(user, parent)) == done
    export_dto(f'retry-{case}-{after_checkpoint}', done)
