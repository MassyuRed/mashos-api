"""Approved u332 source-bound relief/listening, updates and u331 compatibility."""
from dataclasses import asdict, fields, replace
import hashlib
import json
from pathlib import Path

import pytest
from cocolon_meaning_experience_engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine import contracts
from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning, build_updated_grounded_plan
from cocolon_meaning_experience_engine.emlis_thread_projection import project_thread_meaning
from cocolon_meaning_experience_engine.emlis_stage1_composition import _contract_manifest
from emlis_ai_grounded_observation_plan import source_owned_relief_cognition_from_resolver, source_relief_cognition_replacement
from test_cmee_emlis_source_scope_regressions import request
from test_cmee_emlis_q1_thread import initial
from test_cmee_emlis_q3_thread import begin, advance
from test_cmee_emlis_received_discourse import actual, inverse

BASELINE = json.loads((Path(__file__).parent / 'fixtures' / 'cmee_emlis_u331_relief_cognition_v1.json').read_text())
BASE = BASELINE['cases'][0]['memo']
LEFT, RIGHT = BASE.split('。でも、')
RIGHT = RIGHT.rstrip('。')
IMPROVED = {'base', 'relief_degree', 'relief_anxiety', 'lonely_slight', 'lonely_very',
            'lonely_continuing', 'past_possible', 'future_topic', 'other_experience', 'with_question'}


def encoded(value):
    return json.loads(json.dumps(asdict(value), ensure_ascii=False))


def digest(value):
    return hashlib.sha256(json.dumps(asdict(value), ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':')).encode()).hexdigest()


def facets(selected):
    from emlis_ai_grounded_human_reception import SelectedRetainedReliefCognitionDecisionV1
    return tuple(content for d in selected.decisions
                 if type(content := (d.retained_relief_cognition.proposition.appraisal_content
                     if type(d) is SelectedRetainedReliefCognitionDecisionV1
                     else d.subjective_proposition.appraisal_content)) is contracts.EmlisReliefCognitionAppraisalContent)


@pytest.mark.parametrize('row', BASELINE['cases'], ids=lambda row: row['case'])
def test_new_selection_requires_the_two_source_roles_and_preserves_controls(row):
    req = request(row['memo'])
    p = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(p)
    if 'error' in row:
        with pytest.raises(ValueError) as error:
            project_thread_meaning(p, plan)
        assert type(error.value).__name__ + ':' + str(error.value) == row['error']
        return
    selected = project_thread_meaning(p, plan).selected_reception
    out = MeaningExperienceEngine().generate(req)
    assert out.artifact
    if row['case'] in IMPROVED:
        content, = facets(selected)
        assert content.reaction == 'BOUNDED_RELIEF_AT_REPORTED_RELIEF'
        assert content.response == 'LISTEN_TO_PRESENT_LONELINESS_UNDER_UNCERTAINTY'
        assert set(content.relief_binding_refs).isdisjoint(content.loneliness_binding_refs)
        assert set(content.relief_binding_refs + content.loneliness_binding_refs) == set(content.appraised_bindings)
        assert p.checkpoint.checkpoint_id != row['checkpoint']['checkpoint_id']
        assert out.artifact.observation == row['body']['observation']
        assert 'と聞いて、私も少し' in out.artifact.reception
        assert '今、耳を傾けていたいです' in out.artifact.reception
        assert 'かもしれない' in out.artifact.observation
        assert 'とても寂しさ' not in out.artifact.reception
        if row['case'] == 'past_possible':
            assert '友達を傷つけたかもしれない' in out.artifact.observation
            assert 'これから' not in out.artifact.reception
        assert inverse(actual(request=req), out.artifact.reception, without_author=True).passed
    else:
        assert not facets(selected)
        assert encoded(p.checkpoint) == row['checkpoint']
        assert digest(plan) == row['plan_sha']
        assert digest(selected) == row['selected_sha']
        assert encoded(out.artifact) == row['body']


@pytest.mark.parametrize('row', [r for r in BASELINE['cases'] if 'checkpoint' in r], ids=lambda row: row['case'])
def test_saved_u331_checkpoint_rederives_complete_old_meaning_and_body(row):
    assert BASELINE['source_commit'] == '661fbe951edee16be93e9a94d5aac50ba10deb57'
    req = request(row['memo'])
    req = replace(req, emlis_thread=replace(req.emlis_thread,
        prepared_meaning_checkpoint_ref=row['checkpoint']['checkpoint_id']))
    p = prepare_emlis_meaning(req)
    assert p.legacy_relief_cognition_reception == (row['case'] in IMPROVED)
    assert encoded(p.checkpoint) == row['checkpoint']
    plan = build_updated_grounded_plan(p)
    assert digest(plan) == row['plan_sha']
    selected = project_thread_meaning(p, plan).selected_reception
    assert digest(selected) == row['selected_sha']
    assert not facets(selected)
    out = MeaningExperienceEngine().generate(req)
    assert encoded(out.artifact) == row['body']
    assert list(out.reason_codes) == row['reasons']
    assert (encoded(out.question) if out.question else None) == row['question']


@pytest.mark.parametrize('ending', ['友人の話です。', '全部友人の話です。', 'これは友人の感想です。'])
def test_after_attribution_cannot_license_emlis_personal_reaction(ending):
    p = prepare_emlis_meaning(request(BASE + ending))
    plan = build_updated_grounded_plan(p)
    assert not source_owned_relief_cognition_from_resolver(plan.nuclei, plan.relations, p.thread.resolver())
    assert not any(c.startswith('source_relief_cognition_slot:') for n in plan.nuclei for c in n.semantic_frame.attribute_codes)


@pytest.mark.parametrize('memo', [BASE, BASE.replace('寂しい', 'ずっと寂しい'), BASE.replace('もう誘ってもらえなくなる', '友達を傷つけた')])
def test_original_q1_and_q3_share_the_new_reception(memo):
    one = MeaningExperienceEngine().generate(initial(memo))
    three = MeaningExperienceEngine().generate(request(memo))
    assert one.artifact and three.artifact and one.artifact.text == three.artifact.text
    assert one.question is None and three.question is None


@pytest.fixture(scope='module')
def context():
    return actual(request=request(BASE))


@pytest.mark.parametrize('before,after', [
    ('私も少し安心しましたが、', ''),
    ('耳を傾けていたいです', '違いを感じています'),
    ('と聞いて、', 'が原因で、'),
    ('安心しましたが', '安心しませんでしたが'),
    ('かもしれない', ''),
    ('かもしれない', 'に違いない'),
    ('ほっとした', 'ほっとしなかった'),
    ('寂しい', '怖い'),
    ('友達からの誘い', '上司からの誘い'),
    ('私も少し安心しました', '友達も少し安心しました'),
    ('私も少し安心しました', 'それで正しかったと思います'),
    ('今、耳を傾けていたいです', 'きっとまた誘ってもらえます'),
    ('今、耳を傾けていたいです', 'これからもずっとそばにいます'),
])
def test_reader_rejects_missing_facets_source_changes_and_unselected_claims_without_author(context, before, after):
    from test_cmee_emlis_detached_observation import read_body
    body = context[0].artifact.text
    changed = body.replace(before, after)
    assert changed != body
    assert not read_body(context, changed).passed


def test_reader_accepts_bounded_synonyms_but_not_old_generic_content(context):
    follow = context[0].artifact.reception
    assert inverse(context, follow.replace('安心しましたが', 'ほっとしましたし').replace('傾けていたい', '傾けたい'), without_author=True).passed
    old = BASELINE['cases'][0]['body']['reception']
    assert not inverse(context, old, without_author=True).passed


@pytest.mark.parametrize('change', [dict(reaction='UNBOUNDED_RELIEF'), dict(response='PREDICT_REINVITATION'),
    dict(schema_version='v0'), dict(relief_binding_refs=()), dict(loneliness_binding_refs=())])
def test_new_content_is_closed_and_nonempty(context, change):
    proposition = context[4].decisions[0].subjective_proposition
    with pytest.raises(contracts.CMEEStage1ContractError):
        contracts._stage1_subjective_v2_content_bindings(replace(proposition,
            appraisal_content=replace(proposition.appraisal_content, **change)))


UPDATES = [
    ('relief_negative', LEFT, LEFT.replace('ほっとした', 'ほっとしなかった'), 'past'),
    ('factual_present', RIGHT, 'もう誘ってもらえなくなったので寂しい', 'current_input'),
    ('factual_past', RIGHT, 'もう誘ってもらえなくなったので寂しかった', 'past'),
    ('relief_withdraw', LEFT, None, None),
    ('lonely_withdraw', RIGHT, None, None),
]


@pytest.mark.parametrize('name,old,new,time', UPDATES, ids=[r[0] for r in UPDATES])
def test_actual_question_correction_or_withdrawal_expires_joint_facets_and_keeps_live_duties(name, old, new, time):
    req = begin(BASE + '褒められたのに、嬉しくなかった。')
    first = MeaningExperienceEngine().generate(req)
    assert first.artifact and first.question
    reply = f'「{old}」ではなく「{new}」です。' if new else f'「{old}」は誤りです。'
    req = advance(req, reply)
    p = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(p)
    update, = p.checkpoint.answer_update.updates
    assert update.operation == ('REVISE' if new else 'WITHDRAW')
    assert not p.checkpoint.unresolved_parts
    assert not facets(project_thread_meaning(p, plan).selected_reception)
    out = MeaningExperienceEngine().generate(req)
    assert out.artifact and '私も少し安心しました' not in out.artifact.text
    assert '耳を傾けていたい' not in out.artifact.text
    assert old not in out.artifact.text
    assert (RIGHT if old == LEFT else LEFT) in out.artifact.text
    assert '褒められた' in out.artifact.text and '嬉しくなかった' in out.artifact.text
    if new:
        assert new in out.artifact.reception
        assert any(n.semantic_frame.time_scope == time and n.source_fields == ('answer_text_private',)
                   for n in plan.nuclei)
    assert inverse(actual(request=req), out.artifact.reception, without_author=True).passed


@pytest.mark.parametrize('slot,text', [
    ('relief', 'ほっとしなかった'), ('relief', '私の部屋で休めたことにほっとしなかった'),
    ('relief', '一人で休めたことにほっとしなかったかもしれない'),
    ('loneliness', '誘ってもらえなくなった'), ('loneliness', '友達が誘ってもらえなくなったので寂しい'),
    ('loneliness', 'もう誘ってもらえなくなるかもしれないので寂しい'),
    ('loneliness', '誘われたので友人は寂しい'), ('loneliness', '誘われたので寂しいと聞いた'),
])
def test_correction_cannot_import_a_person_or_unstated_feeling(slot, text):
    assert source_relief_cognition_replacement(text, slot) is None


def test_forged_or_source_changed_checkpoint_cannot_gain_legacy_compatibility():
    req = request(BASE)
    for reference in ('foreign', BASELINE['cases'][0]['checkpoint']['checkpoint_id']):
        changed = request(BASE.replace('ほっとした', '嬉しかった')) if reference != 'foreign' else req
        with pytest.raises(ValueError, match='emlis_checkpoint_source_prefix_mismatch'):
            prepare_emlis_meaning(replace(changed, emlis_thread=replace(changed.emlis_thread,
                prepared_meaning_checkpoint_ref=reference)))


def test_current_manifest_records_complete_new_type_and_keeps_base_unchanged():
    manifest = dict(_contract_manifest())
    assert manifest['logical_contract_count'] == 79
    row, = (dict(row) for row in manifest['logical_contract_descriptors']
            if dict(row)['type_name'] == 'EmlisReliefCognitionAppraisalContent')
    assert row['logical_version'] == 'relief-cognition-appraisal-v1'
    assert len(row['fields']) == len(fields(contracts.EmlisReliefCognitionAppraisalContent)) == 11
    assert tuple(dict(f)['field_name'] for f in row['fields']) == tuple(
        f.name for f in fields(contracts.EmlisReliefCognitionAppraisalContent))
    assert tuple(f.name for f in fields(contracts.EmlisAppraisalContent)) == (
        'dimension', 'operation', 'appraised_bindings', 'focal_relation_ref', 'protected_bindings', 'basis_contribution_refs')


@pytest.mark.parametrize('alter', ['swap_roles', 'overlap_roles', 'foreign_relation'])
def test_reidentified_content_must_match_live_source_roles(context, alter):
    import emlis_ai_grounded_human_reception as hr
    from emlis_ai_grounded_observation_gate import _relief_cognition_selected_reception
    selected = context[4]
    decision, = selected.decisions
    content = decision.subjective_proposition.appraisal_content
    if alter == 'swap_roles':
        content = replace(content, relief_binding_refs=content.loneliness_binding_refs,
                          loneliness_binding_refs=content.relief_binding_refs)
    elif alter == 'overlap_roles':
        content = replace(content, relief_binding_refs=content.appraised_bindings)
    else:
        content = replace(content, focal_relation_ref='foreign-relation')
    decision = hr.identify_selected_subjective_reception_decision(replace(decision, decision_ref='',
        subjective_proposition=replace(decision.subjective_proposition, appraisal_content=content)))
    selected = hr.identify_selected_subjective_reception_input(replace(selected, input_ref='', decisions=(decision,)))
    move, = context[1].response_plan.human_reception_plan.moves
    assert _relief_cognition_selected_reception(move, context[1], context[3], selected) is None
    changed = (*context[:4], selected)
    assert not inverse(changed, context[0].artifact.reception, without_author=True).passed


@pytest.mark.parametrize('action,qualified', [('これは友人の話です。', False), ('全部友人の感想です。', False), ('植木に水をやった。', True)])
def test_other_original_field_attribution_is_in_the_same_source_proof(action, qualified):
    p = prepare_emlis_meaning(begin(BASE, action))
    plan = build_updated_grounded_plan(p)
    assert bool(source_owned_relief_cognition_from_resolver(plan.nuclei, plan.relations, p.thread.resolver())) == qualified


def test_old_original03_u319_checkpoint_replays_without_current_identity_assumption():
    old = json.loads((Path(__file__).parent / 'fixtures' / 'cmee_emlis_u319_temporal_topic_checkpoint_v1.json').read_text())
    row, = (r for r in old['cases'] if r['case_id'] == 'original03')
    req = request(row['memo'])
    req = replace(req, emlis_thread=replace(req.emlis_thread, prepared_meaning_checkpoint_ref=row['checkpoint']['checkpoint_id']))
    restored = prepare_emlis_meaning(req)
    assert restored.legacy_relief_cognition_reception
    assert encoded(restored.checkpoint) == row['checkpoint']
    for name in ('nuclei', 'relations'):
        data = json.dumps([asdict(n) for n in getattr(restored.original_plan, name)], ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
        assert hashlib.sha256(data).hexdigest() == row['original_' + name + '_sha256']
    out = MeaningExperienceEngine().generate(req)
    public = row['public_result']
    assert out.status.value == public['status']
    assert out.artifact and out.artifact.text == public['body']
    assert encoded(out.meaning_checkpoint) == row['checkpoint']
    assert list(out.reason_codes) == public['reason_codes']
    assert encoded(out.question_decision) == public['question_decision']
