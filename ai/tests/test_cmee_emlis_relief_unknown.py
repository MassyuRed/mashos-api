"""Approved initial relief/loneliness plus independent SELF unknown retention."""
from dataclasses import replace
import json
from pathlib import Path
import pytest
from cocolon_meaning_experience_engine import MeaningExperienceEngine, contracts as c
from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning, build_updated_grounded_plan
from cocolon_meaning_experience_engine.emlis_thread_projection import project_thread_meaning
import emlis_ai_grounded_human_reception as hr
import emlis_ai_grounded_observation_plan as gp
from test_cmee_emlis_relief_cognition import BASE, encoded, digest
from test_cmee_emlis_source_scope_regressions import request
from test_cmee_emlis_q1_thread import initial
from test_cmee_emlis_received_discourse import actual, inverse

BASELINE = json.loads((Path(__file__).parent/'fixtures/cmee_emlis_u333_relief_unknown_v1.json').read_text())
UNKNOWN = '何が不安なのか、私にもまだわからない。'
IMPROVED = {'base', 'self', 'boku', 'slight', 'past_possible'}


@pytest.mark.parametrize('row', BASELINE['cases'], ids=lambda row: row['case'])
def test_u334_original_meaning_and_controls_survive_while_independent_unknown_is_received(row):
    req = request(row['memo'])
    if row['case'] not in IMPROVED:
        # Preserve historical controls explicitly; current source/short-form
        # outcomes are checked against u335 in relief_anaphora.
        req = replace(req, emlis_thread=replace(req.emlis_thread,
            prepared_meaning_checkpoint_ref=row['checkpoint']['checkpoint_id']))
    p = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(p); out = MeaningExperienceEngine().generate(req)
    if row['case'] in IMPROVED:
        assert p.checkpoint.checkpoint_id != row['checkpoint']['checkpoint_id']
        projection = project_thread_meaning(p, plan)
        assert projection.meaning_plan.projection_branch == 'LIMITED'
        claim, = projection.meaning_plan.subjective_claim_rows
        aggregate = claim.asserted_subjective_proposition
        assert len(aggregate.response_object_refs) == 3
        assert (aggregate.appraisal_content.dimension, aggregate.appraisal_content.operation) == ('MATERIAL_WEIGHT','RECEIVE_AS_MATERIAL')
        pair, unknown = projection.selected_reception.decisions
        assert type(pair) is hr.SelectedRetainedReliefCognitionDecisionV1
        assert type(unknown) is hr.SelectedSubjectiveReceptionDecisionV1
        assert pair.subjective_proposition == unknown.subjective_proposition == aggregate
        local = pair.retained_relief_cognition
        assert local.eligibility.checkpoint_ref == p.checkpoint.checkpoint_id
        assert type(local.proposition.appraisal_content) is c.EmlisReliefCognitionAppraisalContent
        assert len(local.basis_rows) == len(local.qualifier_rows) == 2
        assert set(pair.selected_contribution_refs).isdisjoint(unknown.selected_contribution_refs)
        assert set(pair.selected_contribution_refs + unknown.selected_contribution_refs) == set(aggregate.target_contribution_refs)
        assert out.artifact and out.question is None
        assert out.artifact.observation == row['body']['observation']
        assert '私も少し安心しましたが' in out.artifact.reception
        assert '今、耳を傾けていたいです。何が不安なのか、あなたにもまだわからないのですね。' in out.artifact.reception
        # A new checkpoint may complete with the same fully grounded body.
        resumed = MeaningExperienceEngine().generate(replace(req, emlis_thread=replace(req.emlis_thread,
            prepared_meaning_checkpoint_ref=p.checkpoint.checkpoint_id)))
        assert resumed.artifact == out.artifact
    else:
        assert encoded(p.checkpoint) == row['checkpoint']
        assert digest(plan) == row['plan_sha']
        assert (encoded(out.artifact) if out.artifact else None) == row['body']
        assert list(out.reason_codes) == row['reasons']
        assert (encoded(out.question) if out.question else None) == row['question']
        if 'error' in row:
            with pytest.raises(ValueError) as error: project_thread_meaning(p,plan)
            assert type(error.value).__name__+':'+str(error.value) == row['error']
        else: assert digest(project_thread_meaning(p,plan).selected_reception) == row['selected_sha']


@pytest.mark.parametrize('memo', [BASE+UNKNOWN, '私は'+BASE+UNKNOWN, BASE+UNKNOWN.replace('私にも','僕にも')])
def test_q1_and_q3_share_complete_body_and_do_not_invent_a_question(memo):
    one=MeaningExperienceEngine().generate(initial(memo)); three=MeaningExperienceEngine().generate(request(memo))
    assert one.artifact and three.artifact and one.artifact.text == three.artifact.text
    assert 'まだわからないのですね' in one.artifact.reception
    assert one.question is None and three.question is None


@pytest.fixture(scope='module')
def context():
    return actual(request=request('私は'+BASE+UNKNOWN))


def test_current_body_is_read_independently_and_keeps_approved_synonym(context):
    body=context[0].artifact.reception
    assert inverse(context,body,without_author=True).passed
    changed=body.replace('私も少し安心しましたが','私も少しほっとしましたし')
    assert changed!=body and inverse(context,changed,without_author=True).passed


@pytest.mark.parametrize('before,after', [
 ('私も少し安心しましたが、',''), ('今、耳を傾けていたいです','違いを感じています'),
 ('何が不安なのか、あなたにもまだわからないのですね。',''),
 ('何が不安なのか','何が悲しいのか'), ('あなたにもまだわからない','友達にもまだわからない'),
 ('あなたにもまだわからない','あなたにもまだわからなかった'),
 ('まだわからない','もうわかった'), ('まだわからない','まだわからないから寂しい'),
 ('です。何が','です。だから、何が'), ('かもしれない','に違いない'),
 ('ほっとした','ほっとしなかった'), ('寂しい','怖い'),
 ('私は友達','友達は友達'), ('と聞いて、','が原因で、'),
 ('その寂しさにも','その時の寂しさにも'),
])
def test_reader_rejects_loss_swapped_owner_certainty_and_cause_without_author(context,before,after):
    from test_cmee_emlis_detached_observation import read_body
    body=context[0].artifact.text; changed=body.replace(before,after)
    assert changed!=body
    assert not read_body(context,changed).passed


@pytest.mark.parametrize('mutation', ['checkpoint','move','unknown_move','unknown_role','projection','claim',
    'grounding','relief_role','facet','basis','qualifier','foreign_source'])
def test_resealed_carrier_cannot_replace_any_source_projection_or_role(context,mutation):
    selected=context[4];decision=selected.decisions[0];local=decision.retained_relief_cognition
    if mutation in {'checkpoint','move','unknown_move','unknown_role'}:
        key={'checkpoint':'checkpoint_ref','move':'move_ref','unknown_move':'unknown_move_ref','unknown_role':'unknown_nucleus_ref'}[mutation]
        local=replace(local,eligibility=replace(local.eligibility,**{key:'foreign'}))
    elif mutation in {'projection','claim','grounding'}:
        key={'projection':'aggregate_projection_seal_ref','claim':'aggregate_claim_ref','grounding':'grounding_ref'}[mutation]
        local=replace(local,**{key:'foreign'})
    elif mutation=='relief_role':
        appraisal=local.proposition.appraisal_content
        appraisal=replace(appraisal,relief_binding_refs=appraisal.loneliness_binding_refs,loneliness_binding_refs=appraisal.relief_binding_refs)
        local=replace(local,proposition=replace(local.proposition,appraisal_content=appraisal))
    elif mutation=='facet':
        local=replace(local,proposition=replace(local.proposition,
            appraisal_content=replace(local.proposition.appraisal_content,response='INVENTED_CERTAINTY')))
    elif mutation=='basis': local=replace(local,basis_rows=local.basis_rows[::-1])
    elif mutation=='qualifier':local=replace(local,qualifier_rows=(replace(local.qualifier_rows[0],time_scope='current_input'),*local.qualifier_rows[1:]))
    else:
        other=actual(request=request('私は'+BASE.replace('寂しい','少し寂しい')+UNKNOWN))
        local=other[4].decisions[0].retained_relief_cognition
    local=replace(local,seal_ref=c.retained_relief_cognition_seal(local))
    decision=hr.identify_selected_subjective_reception_decision(replace(decision,retained_relief_cognition=local))
    forged=hr.identify_selected_subjective_reception_input(replace(selected,decisions=(decision,*selected.decisions[1:])))
    with pytest.raises(hr.GroundedHumanReceptionSurfaceError):
        hr.validate_selected_subjective_reception_input(forged,context[1].response_plan.human_reception_plan,context[1],context[3])


@pytest.mark.parametrize('memo,action', [
 (BASE+UNKNOWN.replace('私にも','友達にも'),''), (BASE+UNKNOWN.replace('わからない','わからなかった'),''),
 (BASE+'「'+UNKNOWN+'」',''), (BASE+UNKNOWN+'メモを書いた。',''), (BASE+UNKNOWN,'机を片付けた。'),
 (BASE+'だから、'+UNKNOWN,''), (BASE.replace('でも、','')+UNKNOWN,''),
 (BASE+UNKNOWN+'これは友人の話でした。',''), (BASE+UNKNOWN,'これは友人の話でした。'),
 (UNKNOWN+BASE,''), (BASE+'今はまだわからない。',''), (BASE+'何が不安なのか、私にももうわかった。',''),
])
def test_whole_source_proof_rejects_other_material_attribution_time_and_causality(memo,action):
    p=prepare_emlis_meaning(initial(memo,memo_action=action));plan=build_updated_grounded_plan(p)
    assert not gp._source_relief_cognition_unknown_from_resolver(plan.nuclei,plan.relations,p.thread.resolver())


@pytest.mark.parametrize('field,value', [('retention','required'),('type','user_stated_cause'),('grounding_kind','user_stated_relation')])
def test_inferred_unknown_connection_cannot_be_promoted_to_required_or_cause(context,field,value):
    plan=context[1];group=gp._source_relief_cognition_unknown_from_resolver(plan.nuclei,plan.relations,context[3])
    unknown=group[0].nucleus_id
    incident=tuple(r for r in plan.relations if unknown in (r.from_nucleus_id,r.to_nucleus_id))
    assert len(incident)==1
    edges=tuple(replace(r,**{field:value}) if r==incident[0] else r for r in plan.relations)
    assert not gp._source_relief_cognition_unknown_from_resolver(plan.nuclei,edges,context[3])


@pytest.mark.parametrize('row', BASELINE['cases'], ids=lambda row: row['case'])
def test_saved_u333_checkpoint_restores_full_old_plan_selection_body_and_question(row):
    assert BASELINE['source_commit'] == '92cc0832998e488ac352b6c9504beaacb9be79cd'
    req=request(row['memo'])
    req=replace(req,emlis_thread=replace(req.emlis_thread,prepared_meaning_checkpoint_ref=row['checkpoint']['checkpoint_id']))
    p=prepare_emlis_meaning(req);plan=build_updated_grounded_plan(p)
    assert p.legacy_relief_unknown_retention == (row['case'] in IMPROVED)
    assert encoded(p.checkpoint)==row['checkpoint'] and digest(plan)==row['plan_sha']
    if 'error' in row:
        with pytest.raises(ValueError) as error:project_thread_meaning(p,plan)
        assert type(error.value).__name__+':'+str(error.value)==row['error']
    else:assert digest(project_thread_meaning(p,plan).selected_reception)==row['selected_sha']
    out=MeaningExperienceEngine().generate(req)
    assert (encoded(out.artifact) if out.artifact else None)==row['body']
    assert list(out.reason_codes)==row['reasons']
    assert (encoded(out.question) if out.question else None)==row['question']


def test_current_manifest_registers_the_two_new_private_contracts():
    from dataclasses import fields
    from cocolon_meaning_experience_engine.emlis_stage1_composition import _contract_manifest
    manifest=dict(_contract_manifest())
    descriptors={dict(row)['type_name']:dict(row) for row in manifest['logical_contract_descriptors']}
    assert manifest['logical_contract_count']==79
    for cls in (c.RetainedReliefCognitionEligibilityV1,c.RetainedReliefCognitionContentV1):
        descriptor=descriptors[cls.__name__]
        assert descriptor['serialization_boundary']=='REQUEST_LOCAL_PRIVATE_CANONICAL_VIEW'
        assert tuple(dict(row)['field_name'] for row in descriptor['fields'])==tuple(f.name for f in fields(cls))


from test_emlis_q3_application import qdb, qcase
from test_emlis_q2_application import run


@pytest.mark.parametrize('tier', ['free','plus','premium'])
def test_saved_three_target_body_reopens_without_generation(qcase,qdb,monkeypatch,tier):
    user,parent,service=qcase
    qdb.query('update public.profiles set subscription_tier=$2 where id=$1',[user,tier])
    qdb.query('update public.emotions set memo=$2 where id=$1',[parent,'私は'+BASE+UNKNOWN])
    dto=run(service.start(user,parent))
    assert dto['body_state']=='FINAL' and dto['pending_question'] is None
    body=dto['current_observation']['text']
    assert '私も少し安心しましたが' in body and '今、耳を傾けていたいです。何が不安なのか、あなたにもまだわからないのですね。' in body
    monkeypatch.setattr(service.engine,'generate',lambda *_:pytest.fail('saved body regenerated'))
    assert run(service.get(user,parent))==dto and run(service.start(user,parent))==dto
