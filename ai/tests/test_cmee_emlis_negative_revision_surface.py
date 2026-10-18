"""A revised current negative feeling keeps all selected sources in the body.

u353 is captured by an independent unchanged process. Its saved semantics stay
identical; only the four unfinished current-negative surfaces are repaired.
"""
from dataclasses import replace
import json
from pathlib import Path
import pytest
from cocolon_meaning_experience_engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine import emlis_answer_update as update
from cocolon_meaning_experience_engine.emlis_thread_projection import project_thread_meaning
from cocolon_meaning_experience_engine.contracts import EmlisAppraisalContent
import emlis_ai_grounded_observation_gate as gate
import emlis_ai_grounded_human_reception as reception
from test_cmee_emlis_unknown_revision_time import request, checkpoint, first
from test_cmee_emlis_contrast_degree import encoded, digest
from test_cmee_emlis_received_discourse import actual
from test_cmee_emlis_detached_observation import read_body

BASELINE = json.loads((Path(__file__).parent / 'fixtures' /
    'cmee_emlis_u353_negative_revision_v1.json').read_text())
ROWS = {(r['case'], r['profile']): r for r in BASELINE['cases']}
CHANGED = {'mixed_unknown_current_negative', 'mixed_unknown_now_negative'}
PAIR = ('友達からの誘いを断って、一人で休めたことにほっとした',
        'もう誘ってもらえなくなるかもしれないと思うと寂しい')
RECEPTION = ('回答した時点で嬉しくないことを小さくせずに受け止めています。'
             + PAIR[0] + 'という気持ちと' + PAIR[1] + 'こととの違いを受け止めています。')

@pytest.mark.parametrize('case,profile', ROWS)
def test_u353_whole_meaning_identity_and_bounded_surface_change(case, profile):
    row = ROWS[case, profile]
    assert BASELINE['source_commit'] == 'ace2b4aaed8224f364b4f89c2df44362a5713a37'
    req = request(case, profile)
    assert encoded(first(case, profile)[1].artifact) == row['initial_artifact']
    assert encoded(first(case, profile)[1].question) == row['initial_question']
    p = update.prepare_emlis_meaning(req)
    assert encoded(p.checkpoint) == row['checkpoint']
    assert digest(p.checkpoint) == row['checkpoint_sha']
    assert digest(p.original_plan) == row['original_plan_sha']
    assert digest(p.accepted_nuclei) == row['accepted_sha']
    if 'plan_error' in row:
        with pytest.raises(ValueError, match=row['plan_error']): update.build_updated_grounded_plan(p)
    else:
        plan = update.build_updated_grounded_plan(p)
        assert digest(plan) == row['plan_sha']
        assert digest(plan.nuclei) == row['nuclei_sha']
        assert digest(plan.relations) == row['relations_sha']
        assert [m.reference_mode for m in plan.response_plan.human_reception_plan.moves] == row['references']
        if 'projection_error' in row:
            with pytest.raises(ValueError, match=row['projection_error']): project_thread_meaning(p, plan)
        else:
            selected = project_thread_meaning(p, plan).selected_reception
            assert digest(selected) == row['selected_sha']
            assert digest(selected.decisions) == row['decisions_sha']
    out = MeaningExperienceEngine().generate(checkpoint(req, p.checkpoint.checkpoint_id))
    assert encoded(out.question) == row['question']
    decision = encoded(out.question_decision)
    if case in CHANGED and profile == 'q3':
        # Successful body uses normal END instead of the unavailable fallback.
        assert decision == dict(row['question_decision'], decision_reason='no_bound_personal_meaning_target')
    else:
        assert decision == row['question_decision']
    if case in CHANGED:
        assert row['status'] == 'UNAVAILABLE' and row['artifact'] is None
        assert out.status.value == 'GENERATED' and out.body_state == 'REFINED'
        assert out.artifact.reception == RECEPTION
        assert not out.automatic_progression
        # The dedicated content expires; retain all three generic appraisal objects.
        for decision in selected.decisions:
            prop = decision.subjective_proposition
            assert type(prop.appraisal_content) is EmlisAppraisalContent
            assert prop.appraisal_content.dimension == 'MATERIAL_WEIGHT'
            assert len(prop.response_object_refs) == 3
    else:
        assert digest(out.artifact) == row['artifact_sha']
        assert out.status.value == row['status'] and out.body_state == row['body_state']
        assert list(out.reason_codes) == row['reasons']

@pytest.fixture(scope='module')
def context():
    return actual(request=request('mixed_unknown_current_negative', 'q3'))

@pytest.mark.parametrize('old,new', [
    ('回答した時点で嬉しくない', 'その時に嬉しくなかった'),
    ('回答した時点で嬉しくない', '嬉しくない'),
    ('回答した時点で嬉しくない', '回答した時点で嬉しい'),
    (PAIR[0], 'ほっとした'),
    (PAIR[0], '一人で休めたことにほっとした'),
    (PAIR[0], '友人が一人で休めたことにほっとした'),
    (PAIR[0], PAIR[0].replace('ほっとした', 'ほっとしなかった')),
    (PAIR[0], PAIR[0].replace('ほっとした', 'ほっとする')),
    (PAIR[1], '寂しい'),
    (PAIR[1], PAIR[1].replace('かもしれない', '')),
    (PAIR[1], PAIR[1].replace('寂しい', '寂しかった')),
    (PAIR[1], PAIR[1].replace('と思うと', 'から')),
    ('という気持ちと', 'という気持ちだから'),
    ('との違いを受け止めています。', 'との因果関係を受け止めています。'),
    ('との違いを受け止めています。', 'との違いをどちらの側も残したまま、感じています。'),
    (PAIR[0] + 'という気持ちと' + PAIR[1] + 'こと', 'その安堵と寂しさ'),
])
def test_independent_reader_rejects_source_scope_polarity_time_and_relation_loss(context, old, new):
    body = context[0].artifact.text
    assert read_body(context, body).passed
    # Change Reception only; Observation retaining the source cannot cover it.
    prefix, reception_body = body.split('\n\nEmlisから：\n')
    changed = prefix + '\n\nEmlisから：\n' + reception_body.replace(old, new)
    assert changed != body
    assert not read_body(context, changed).passed

@pytest.mark.parametrize('mutation', ['drop_answer', 'drop_pair', 'contribution', 'qualifier',
                                      'source_role', 'binding', 'duplicate', 'focal_relation'])
def test_pair_reader_requires_whole_selected_aggregate(context, mutation):
    _, plan, _, resolver, selected = context
    move = plan.response_plan.human_reception_plan.moves[1]
    d = selected.decisions[1]; p = d.subjective_proposition
    rows, qualifiers = d.basis_rows, d.qualifier_rows
    if mutation == 'drop_answer': p = replace(p, response_object_refs=p.response_object_refs[:2])
    elif mutation == 'drop_pair': p = replace(p, primary_target_refs=p.primary_target_refs[1:])
    elif mutation == 'contribution': rows = (replace(rows[0], contribution_ref=rows[2].contribution_ref), *rows[1:])
    elif mutation == 'qualifier': qualifiers = (replace(qualifiers[0], polarity='negative'), *qualifiers[1:])
    elif mutation == 'source_role': qualifiers = (replace(qualifiers[0], source_argument_role='RIGHT'), *qualifiers[1:])
    elif mutation == 'binding': rows = (*rows[:2], replace(rows[2], semantic_ref=rows[0].semantic_ref))
    elif mutation == 'duplicate': rows = (*rows, rows[0])
    elif mutation == 'focal_relation': p = replace(p, focal_relation_ref=selected.relation_pairs[0][0])
    # Keep both decisions mutually equal where applicable; no one-sided mismatch shortcut.
    altered = replace(selected, decisions=tuple(replace(row, subjective_proposition=p,
        basis_rows=rows, qualifier_rows=qualifiers) for row in selected.decisions))
    assert gate._body_inverse_past_cognitive_feeling_contrast_forms(move, plan, resolver, selected)
    assert gate._body_inverse_past_cognitive_feeling_contrast_forms(move, plan, resolver, altered) is None

@pytest.mark.parametrize('field,value', [('time_scope', 'past'), ('polarity', 'positive'),
    ('actor', 'other_person'), ('modality', 'uncertain')])
def test_reference_override_cannot_expand_to_other_answer_semantics(context, field, value):
    _, plan, _, resolver, _ = context
    rp = plan.response_plan.human_reception_plan; move = rp.moves[1]
    nid = rp.moves[0].target_nucleus_ids[0]
    answer = next(n for n in plan.nuclei if n.nucleus_id == nid)
    forged = replace(answer, semantic_frame=replace(answer.semantic_frame, **{field:value}))
    altered = replace(plan, nuclei=tuple(forged if n.nucleus_id==nid else n for n in plan.nuclei))
    assert reception.source_grounded_current_negative_relief_reference(rp, move, plan, resolver)
    assert not reception.source_grounded_current_negative_relief_reference(rp, move, altered, resolver)


@pytest.mark.parametrize('field', ['meaning_outcome_ref', 'reception_binding_ref',
                                  'projected_claim_ref', 'selected_opportunity_ref'])
def test_independent_reader_rejects_split_aggregate_identity(context, field):
    _, plan, _, resolver, selected = context
    move = plan.response_plan.human_reception_plan.moves[1]
    first, second = selected.decisions
    altered = replace(selected, decisions=(replace(first, **{field: 'other-aggregate'}), second))
    assert gate._body_inverse_past_cognitive_feeling_contrast_forms(move, plan, resolver, altered) is None
