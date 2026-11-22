"""An unrelated first answer must retain the two approved relief/listening facets.

The u343 baseline was captured in its untouched commit, using actual Q1/Q3
questions. Full old checkpoints, meaning, selection (or exact failure), delivery,
and source identity remain reproducible. This does not qualify a new affect.
"""
from dataclasses import replace
from functools import lru_cache
import json
import os
from pathlib import Path
import re
from unittest.mock import patch

import pytest
import emlis_ai_grounded_sentence_surface as surface
from cocolon_meaning_experience_engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.emlis_answer_update import (
    prepare_emlis_meaning, build_updated_grounded_plan,
    _prepare_emlis_meaning_from_plan,
)
from cocolon_meaning_experience_engine.emlis_thread_source import admit_emlis_thread
from cocolon_meaning_experience_engine.emlis_question import original_meaning_plan
from cocolon_meaning_experience_engine.emlis_thread_projection import project_thread_meaning
from test_cmee_emlis_contrast_degree import encoded, digest
from test_cmee_emlis_q1_thread import initial
from test_cmee_emlis_q3_thread import begin, advance
from test_cmee_emlis_received_discourse import actual
from test_cmee_emlis_detached_observation import read_body

SOURCE_COMMIT = '3b7b590bc10e28abf4606bba198c3e0d0e704290'
BASELINE = json.loads((Path(__file__).parent / 'fixtures' /
    'cmee_emlis_u343_relief_update_v1.json').read_text())
ROWS = {row['case']: row for row in BASELINE['cases']}
IMPROVED = {
    'add_now_positive', 'add_past_positive', 'add_now_negative', 'add_past_burden',
    'self_pair', 'degree_pair', 'revise_other',
    'withdraw_other_event', 'extra_unknown',  # u346 restores the same pair duty.
}
CASES = [pytest.param(row, id=row['case']) for row in BASELINE['cases']]
PROFILES = pytest.mark.parametrize('profile', ['q1', 'q3'])


def with_checkpoint(req, checkpoint):
    return replace(req, emlis_thread=replace(req.emlis_thread,
        prepared_meaning_checkpoint_ref=checkpoint))


@lru_cache(maxsize=None)
def starting(case, profile):
    row = ROWS[case]
    return (initial if profile == 'q1' else begin)(row['memo'])


@lru_cache(maxsize=None)
def answered(case, profile):
    # advance obtains and records the actually generated canonical question.
    return advance(starting(case, profile), ROWS[case]['answer'])


def assert_source(prepared, frozen):
    assert prepared.thread.source_prefix_ref == frozen['source_prefix']
    assert encoded(prepared.thread.original.evidence_spans) == frozen['spans']


def export_current_body(row, profile, out, prepared, plan=None):
    folder = os.environ.get('CMEE_RELIEF_UPDATE_BODY_DIR')
    if not folder or profile != 'q3':
        return
    from test_cmee_emlis_relief_cognition import facets
    record = {'case': row['case'], 'memo': row['memo'], 'reply': row['answer'],
        'body': out.artifact.text if out.artifact else None, 'reasons': list(out.reason_codes),
        'status': out.status.value, 'body_state': out.body_state}
    try:
        plan = plan or build_updated_grounded_plan(prepared)
        selected = project_thread_meaning(prepared, plan).selected_reception
        record['selected_facet_count'] = len(facets(selected))
    except ValueError as exc:
        record['selected_facet_count'] = None
        record['projection_error'] = str(exc)
    Path(folder).mkdir(parents=True, exist_ok=True)
    Path(folder, row['case'] + '.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')


def assert_whole_snapshot(req, frozen, *, export_row=None, profile=None):
    prepared = prepare_emlis_meaning(req)
    assert encoded(prepared.checkpoint) == frozen['checkpoint']
    assert digest(prepared.checkpoint) == frozen['checkpoint_sha']
    assert_source(prepared, frozen)
    plan = None
    if 'plan_error' in frozen:
        with pytest.raises(ValueError, match='^' + re.escape(frozen['plan_error']) + '$'):
            build_updated_grounded_plan(prepared)
    else:
        plan = build_updated_grounded_plan(prepared)
        assert digest(plan) == frozen['plan_sha']
        assert encoded(plan.nuclei) == frozen['nuclei']
        assert encoded(plan.relations) == frozen['relations']
        if 'projection_error' in frozen:
            with pytest.raises(ValueError, match='^' + re.escape(frozen['projection_error']) + '$'):
                project_thread_meaning(prepared, plan)
        else:
            assert digest(project_thread_meaning(prepared, plan).selected_reception) == frozen['selected_sha']
    out = MeaningExperienceEngine().generate(req)
    if export_row is not None:
        export_current_body(export_row, profile, out, prepared, plan)
    assert encoded(out.artifact) == frozen['artifact']
    assert digest(out.artifact) == frozen['artifact_sha']
    assert encoded(out.question) == frozen['question']
    assert encoded(out.question_decision) == frozen['question_decision']
    assert list(out.reason_codes) == frozen['reasons']
    assert out.status.value == frozen['status']
    assert out.body_state == frozen['body_state']
    return prepared


@PROFILES
@pytest.mark.parametrize('row', CASES)
def test_initial_whole_meaning_question_and_body_are_unchanged(row, profile):
    assert BASELINE['source_commit'] == SOURCE_COMMIT
    assert_whole_snapshot(starting(row['case'], profile), row[profile]['initial'])


@PROFILES
@pytest.mark.parametrize('row', CASES)
def test_first_answer_keeps_pair_and_exact_other_experience_or_remains_a_control(row, profile):
    req = answered(row['case'], profile)
    frozen = row[profile]['updated']
    if row['case'] not in IMPROVED:
        assert_whole_snapshot(req, frozen, export_row=row, profile=profile)
        return
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    assert_source(prepared, frozen)
    # All original source spans and the two approved source-owned roles survive.
    assert digest(prepared.original_plan) == row[profile]['initial']['plan_sha']
    if 'plan_error' not in frozen:
        assert encoded(plan.nuclei) == frozen['nuclei']
        assert encoded(plan.relations) == frozen['relations']
    else:
        # u343 could not construct this active plan at all. Derive its complete
        # surviving source from the frozen initial plan and accepted withdrawal.
        # The existing withdrawal witness plus this scoped retention witness are
        # the only additions; neither changes the source, time, or predicate.
        assert row['case'] == 'withdraw_other_event'
        assert frozen['plan_error'] == 'human_reception_withdrawal_capability_gap'
        initial_plan = row[profile]['initial']
        update, = frozen['checkpoint']['answer_update']['updates']
        event_id, = update['target_meaning_refs']
        received_edge, = (edge for edge in initial_plan['relations']
                          if edge['from_nucleus_id'] == event_id)
        inactive = set(frozen['checkpoint']['inactive_claim_refs'])
        assert inactive == {event_id, received_edge['relation_id']}
        expected = encoded([n for n in initial_plan['nuclei']
                            if n['nucleus_id'] not in inactive])
        survivor, = (n for n in expected
                     if n['nucleus_id'] == received_edge['to_nucleus_id'])
        survivor['semantic_frame']['attribute_codes'] += [
            'thread_subject:withdrawn_source_event',
            'thread_subject:unchanged_relief_pair_withdrawal:v1',
        ]
        assert encoded(plan.nuclei) == expected
        assert encoded(plan.relations) == [edge for edge in initial_plan['relations']
                                          if edge['relation_id'] not in inactive]
    assert prepared.checkpoint.checkpoint_id != frozen['checkpoint_id']
    assert not prepared.legacy_relief_cognition_update_retention
    assert prepared.checkpoint.assessment_status == 'RESOLVED'
    assert not prepared.checkpoint.unresolved_parts
    assert prepared.checkpoint.answer_update.disposition == 'MATERIAL_UPDATE'
    assert len(prepared.checkpoint.answer_update.updates) == 1
    out = MeaningExperienceEngine().generate(req)
    export_current_body(row, profile, out, prepared, plan)
    assert out.artifact, out.reason_codes
    text, follow = out.artifact.text, out.artifact.reception
    assert 'と聞いて、私も少し安心しましたが' in follow
    assert '今、耳を傾けていたいです' in follow
    assert 'かもしれないと思うと' in out.artifact.observation
    assert '一人で休めたことに' in out.artifact.observation
    assert '必ず' not in text and 'だから' not in follow
    assert not out.automatic_progression
    if row['case'] == 'withdraw_other_event':
        assert '褒められた' not in text
        assert '嬉しくなかった' in follow
    else:
        assert '褒められた' in follow
        if row['case'] == 'withdraw_other_feeling':
            assert '嬉しくなかった' not in text
        elif row['case'] == 'revise_other':
            assert '嬉しくなかった' not in text
            assert '悲しかった' in text
        else:
            assert '嬉しくなかった' in text
            expected = {
                'add_now_positive': ('回答した時点', '嬉しい'),
                'add_past_positive': ('その時', '嬉しかった'),
                'add_now_negative': ('回答した時点', '悲し'),
                'add_past_burden': ('その時', '重'),
                'self_pair': ('回答した時点', '嬉しい'),
                'degree_pair': ('回答した時点', '少し悲し'),
                'extra_unknown': ('回答した時点', '嬉しい'),
            }[row['case']]
            assert all(part in follow for part in expected)
    if row['case'] == 'degree_pair':
        assert '少しほっとした' in out.artifact.observation
        assert 'とても寂しい' in out.artifact.observation
    # A newly saved checkpoint rederives the same entire meaning and delivery.
    restored = prepare_emlis_meaning(with_checkpoint(req, prepared.checkpoint.checkpoint_id))
    restored_plan = build_updated_grounded_plan(restored)
    assert encoded(restored.checkpoint) == encoded(prepared.checkpoint)
    assert digest(restored_plan) == digest(plan)
    assert digest(project_thread_meaning(restored, restored_plan).selected_reception) == digest(
        project_thread_meaning(prepared, plan).selected_reception)
    resumed = MeaningExperienceEngine().generate(with_checkpoint(req, prepared.checkpoint.checkpoint_id))
    assert resumed.artifact == out.artifact
    assert resumed.question == out.question
    assert resumed.question_decision == out.question_decision
    assert resumed.reason_codes == out.reason_codes


@PROFILES
@pytest.mark.parametrize('row', CASES)
def test_u343_answer_checkpoint_restores_entire_old_meaning_and_delivery(row, profile):
    assert BASELINE['source_commit'] == SOURCE_COMMIT
    frozen = row[profile]['updated']
    req = with_checkpoint(answered(row['case'], profile), frozen['checkpoint_id'])
    prepared = assert_whole_snapshot(req, frozen)
    assert prepared.legacy_relief_cognition_update_retention == (row['case'] in IMPROVED)


def old_prepare(req):
    req = with_checkpoint(req, None)
    thread = admit_emlis_thread(req)
    return _prepare_emlis_meaning_from_plan(req, thread, original_meaning_plan(thread),
        legacy_relief_cognition_update_retention=True).checkpoint


@PROFILES
@pytest.mark.parametrize('case', sorted(IMPROVED))
def test_explicit_old_derivation_matches_independently_frozen_u343(case, profile):
    assert encoded(old_prepare(answered(case, profile))) == ROWS[case][profile]['updated']['checkpoint']


@pytest.fixture(scope='module', params=[
    'add_now_positive', 'add_past_positive', 'add_now_negative', 'revise_other',
    'withdraw_other_event', 'degree_pair',
])
def complete(request):
    return request.param, actual(request=answered(request.param, 'q3'))


@pytest.mark.parametrize('mutation', ['drop_pair', 'drop_other', 'no_relief',
    'no_listening', 'relief_negated', 'future_promise', 'cause', 'loneliness_certain'])
def test_independent_body_reader_rejects_lost_or_invented_meaning(complete, mutation):
    case, context = complete
    artifact = context[0].artifact
    observation, follow = artifact.observation, artifact.reception
    sentences = [part + '。' for part in follow.removesuffix('。').split('。')]
    pair = next(s for s in sentences if '耳を傾けていたいです' in s)
    others = [s for s in sentences if s != pair]
    assert others
    if mutation == 'drop_pair': changed = artifact.text.replace(pair, '')
    elif mutation == 'drop_other': changed = artifact.text.replace(''.join(others), '')
    elif mutation == 'no_relief': changed = artifact.text.replace('私も少し安心しましたが、', '')
    elif mutation == 'no_listening': changed = artifact.text.replace('今、耳を傾けていたいです', '違いを感じています')
    elif mutation == 'relief_negated': changed = artifact.text.replace('ほっとしたと聞いて', 'ほっとしなかったと聞いて')
    elif mutation == 'future_promise': changed = artifact.text + '友達は必ずまた誘ってくれます。'
    elif mutation == 'cause': changed = artifact.text.replace('の一方で', 'が原因で', 1)
    else: changed = artifact.text.replace('かもしれない', 'に違いない', 1)
    assert changed != artifact.text
    with patch.object(surface, '_realize_line', side_effect=AssertionError('no surface oracle')):
        assert read_body(context, artifact.text).passed
        assert not read_body(context, changed).passed


@pytest.mark.parametrize('case,before,after', [
    ('add_now_positive', '回答した時点', 'その時'),
    ('add_past_positive', 'その時', '回答した時点'),
    ('add_now_positive', '嬉しい', '嬉しくない'),
    ('add_now_negative', '悲し', '嬉し'),
    ('degree_pair', '少し悲し', 'とても悲し'),
    ('revise_other', '褒められた', '誘われた'),
])
def test_updated_other_experience_retains_its_own_time_polarity_degree_and_owner(case, before, after):
    context = actual(request=answered(case, 'q3'))
    artifact = context[0].artifact
    follow = artifact.reception
    changed = follow.replace(before, after)
    assert changed != follow
    assert read_body(context, artifact.text).passed
    assert not read_body(context, artifact.text.replace(follow, changed)).passed


def test_unknown_checkpoint_never_selects_the_old_update_meaning():
    req = answered('add_now_positive', 'q3')
    checkpoint = prepare_emlis_meaning(req).checkpoint.checkpoint_id
    unknown = checkpoint[:-1] + ('0' if checkpoint[-1] != '0' else '1')
    with pytest.raises(ValueError, match='emlis_checkpoint_source_prefix_mismatch'):
        prepare_emlis_meaning(with_checkpoint(req, unknown))


@pytest.fixture(scope='module')
def selected_update():
    from emlis_ai_grounded_human_reception import SelectedRetainedReliefCognitionDecisionV1
    from cocolon_meaning_experience_engine import contracts as c
    context = actual(request=answered('add_now_positive', 'q3'))
    selected = context[4]
    decision, = (d for d in selected.decisions if type(d) is SelectedRetainedReliefCognitionDecisionV1)
    local = decision.retained_relief_cognition
    assert type(local) is c.RetainedUpdatedReliefCognitionContentV1
    assert type(local.eligibility) is c.RetainedUpdatedReliefCognitionEligibilityV1
    content = local.proposition.appraisal_content
    assert type(content) is c.EmlisReliefCognitionAppraisalContent
    assert content.reaction == 'BOUNDED_RELIEF_AT_REPORTED_RELIEF'
    assert content.response == 'LISTEN_TO_PRESENT_LONELINESS_UNDER_UNCERTAINTY'
    assert len(local.basis_rows) == len(local.qualifier_rows) == 2
    assert set(content.relief_binding_refs).isdisjoint(content.loneliness_binding_refs)
    assert set(content.relief_binding_refs + content.loneliness_binding_refs) == set(content.appraised_bindings)
    return context, decision


@pytest.mark.parametrize('mutation', [
    'source_prefix', 'checkpoint', 'original_source', 'answer_source',
    'relief_role', 'loneliness_role', 'contrast', 'event', 'reaction', 'move',
    'missing_update', 'missing_answer', 'round', 'aggregate_projection',
    'aggregate_claim', 'grounding', 'facet', 'basis', 'qualifier_time', 'cross_request',
])
def test_resealed_retention_proof_cannot_borrow_another_source_role_or_update(selected_update, mutation):
    import emlis_ai_grounded_human_reception as hr
    from cocolon_meaning_experience_engine import contracts as c
    context, decision = selected_update
    selected = context[4]
    local = decision.retained_relief_cognition
    eligibility = local.eligibility
    eligibility_fields = {
        'source_prefix': 'source_prefix_ref', 'checkpoint': 'checkpoint_ref',
        'original_source': 'original_source_ref', 'answer_source': 'answer_source_ref',
        'relief_role': 'relief_nucleus_ref', 'loneliness_role': 'loneliness_nucleus_ref',
        'contrast': 'contrast_relation_ref', 'event': 'received_event_ref',
        'reaction': 'received_reaction_ref', 'move': 'move_ref',
    }
    if mutation in eligibility_fields:
        eligibility = replace(eligibility, **{eligibility_fields[mutation]: 'foreign'})
        local = replace(local, eligibility=eligibility)
    elif mutation == 'missing_update':
        local = replace(local, eligibility=replace(eligibility, answer_update=None))
    elif mutation == 'missing_answer':
        local = replace(local, eligibility=replace(eligibility,
            thread_control=replace(eligibility.thread_control, answers=())))
    elif mutation == 'round':
        local = replace(local, eligibility=replace(eligibility,
            thread_control=replace(eligibility.thread_control, current_round=2)))
    elif mutation in {'aggregate_projection', 'aggregate_claim', 'grounding'}:
        key = {'aggregate_projection': 'aggregate_projection_seal_ref',
               'aggregate_claim': 'aggregate_claim_ref', 'grounding': 'grounding_ref'}[mutation]
        local = replace(local, **{key: 'foreign'})
    elif mutation == 'facet':
        local = replace(local, proposition=replace(local.proposition,
            appraisal_content=replace(local.proposition.appraisal_content,
                                      response='PROMISE_FUTURE_INVITATIONS')))
    elif mutation == 'basis':
        local = replace(local, basis_rows=local.basis_rows[::-1])
    elif mutation == 'qualifier_time':
        local = replace(local, qualifier_rows=(
            replace(local.qualifier_rows[0], time_scope='current_input'),
            *local.qualifier_rows[1:]))
    else:
        different = actual(request=answered('self_pair', 'q3'))
        donor, = (d for d in different[4].decisions if type(d) is hr.SelectedRetainedReliefCognitionDecisionV1)
        local = donor.retained_relief_cognition
    local = replace(local, seal_ref=c.retained_relief_cognition_seal(local))
    changed = hr.identify_selected_subjective_reception_decision(
        replace(decision, retained_relief_cognition=local))
    forged = hr.identify_selected_subjective_reception_input(replace(selected,
        decisions=tuple(changed if d == decision else d for d in selected.decisions)))
    with pytest.raises(hr.GroundedHumanReceptionSurfaceError):
        hr.validate_selected_subjective_reception_input(forged,
            context[1].response_plan.human_reception_plan, context[1], context[3])
