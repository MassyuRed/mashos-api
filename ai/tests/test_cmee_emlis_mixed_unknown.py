"""Approved mixed-source unknown retention, full u347 compatibility and inverse proof."""
from dataclasses import replace
from functools import lru_cache
import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest
import emlis_ai_grounded_sentence_surface as surface
import emlis_ai_grounded_observation_plan as gp
import emlis_ai_grounded_human_reception as hr
from cocolon_meaning_experience_engine import MeaningExperienceEngine, contracts as c
from cocolon_meaning_experience_engine import emlis_answer_update as update
from cocolon_meaning_experience_engine.emlis_thread_projection import project_thread_meaning, validate_retained_relief_cognition_source
from cocolon_meaning_experience_engine.emlis_thread_contracts import EmlisClarificationV1,EmlisQuestionDecisionV1,SupplementalAnswerSource
from test_cmee_emlis_contrast_degree import encoded,digest
from test_cmee_emlis_q1_thread import initial
from test_cmee_emlis_q3_thread import begin,advance
from test_cmee_emlis_received_discourse import actual
from test_cmee_emlis_detached_observation import read_body

BASELINE=json.loads((Path(__file__).parent/'fixtures/cmee_emlis_u347_mixed_unknown_v1.json').read_text())
ROWS={row['case']:row for row in BASELINE['cases']}
UPDATES={row['case']:row for row in BASELINE['updates']}
QUALIFIED={'mixed','self','degree','kana','boku','wh_degree','received_kana','received_connective','self_unknown'}
UPDATED={'add','add_negative','add_past','revise','withdraw','degree_add'}


def checkpoint(req,ref):
    return replace(req,emlis_thread=replace(req.emlis_thread,prepared_meaning_checkpoint_ref=ref))


def decode_question(value):
    q=dict(value);d=dict(q.pop('decision'))
    for key in ('supporting_evidence_refs','affected_meaning_refs','affected_reception_refs','asked_target_refs'):
        d[key]=tuple(d[key])
    return EmlisClarificationV1(decision=EmlisQuestionDecisionV1(**d),**q)


@lru_cache(None)
def request(case,profile='q3',answered=False,historical=False):
    row=UPDATES[case] if answered else ROWS[case]
    req=(initial if profile=='q1' else begin)(row['memo'])
    if not answered:return checkpoint(req,row[profile]['checkpoint_id']) if historical else req
    if not historical:return advance(req,row['answer'])
    q=decode_question(ROWS[row['original_case']][profile]['question']);t=req.emlis_thread
    answer=SupplementalAnswerSource('answer-1',t.thread_id,q.question_id,1,t.original_source_ref,row['answer'],'2026-09-11T01:00:00Z')
    control=replace(t.question_control_context,pending_question=q,asked_target_refs=(q.decision.target_ref,),issued_count=1,issued_questions=(q,))
    return replace(req,emlis_thread=replace(t,answers=(answer,),current_round=1,
        prepared_meaning_checkpoint_ref=row[profile]['checkpoint_id'],question_control_context=control))


def full_snapshot(req,old):
    prepared=update.prepare_emlis_meaning(req)
    assert digest(prepared.checkpoint)==old['checkpoint_sha']
    assert digest(prepared.original_plan)==old['original_plan_sha']
    if 'plan_error' in old:
        with pytest.raises(ValueError) as exc:update.build_updated_grounded_plan(prepared)
        assert str(exc.value)==old['plan_error']
    else:
        plan=update.build_updated_grounded_plan(prepared);assert digest(plan)==old['plan_sha']
        if 'projection_error' in old:
            with pytest.raises(ValueError) as exc:project_thread_meaning(prepared,plan)
            assert str(exc.value)==old['projection_error']
        else:assert digest(project_thread_meaning(prepared,plan).selected_reception)==old['selected_sha']
    out=MeaningExperienceEngine().generate(req)
    for key in ('artifact','question','question_decision'):assert encoded(getattr(out,key))==old[key]
    assert list(out.reason_codes)==old['reasons']
    assert out.status.value==old['status'] and out.body_state==old['body_state']
    return prepared,out


def export(name,req,out):
    folder=os.environ.get('CMEE_MIXED_UNKNOWN_BODY_DIR')
    if folder:
        Path(folder).mkdir(parents=True,exist_ok=True)
        Path(folder,name+'.json').write_text(json.dumps(dict(case=name,memo=update.prepare_emlis_meaning(req).thread.original.normalized_current_input['memo'],
            body=out.artifact.text if out.artifact else None,question=encoded(out.question),reasons=list(out.reason_codes)),ensure_ascii=False,indent=2)+'\n')


@pytest.mark.parametrize('profile',['q1','q3'])
@pytest.mark.parametrize('kind,case',[*[(False,k) for k in ROWS],*[(True,k) for k in UPDATES]])
def test_full_u347_checkpoint_reproduces_meaning_selection_body_and_stop(kind,case,profile):
    assert BASELINE['source_commit']=='e53e8af8513bd567e1df9bca1b09dad4977e230c'
    row=(UPDATES if kind else ROWS)[case]
    full_snapshot(request(case,profile,kind,True),row[profile])


@pytest.mark.parametrize('profile',['q1','q3'])
@pytest.mark.parametrize('case',ROWS)
def test_initial_receives_only_the_qualified_current_unknown(case,profile):
    req=request(case,profile);old=ROWS[case][profile]
    if case not in QUALIFIED:
        full_snapshot(req,old);return
    p=update.prepare_emlis_meaning(req);plan=update.build_updated_grounded_plan(p)
    group=gp._source_mixed_relief_unknown_group(plan.nuclei,plan.relations,p.thread.original.evidence_spans,p.thread.original.normalized_current_input)
    assert group and len(group)==7
    unknown,left,right,event,reaction,*_=group
    assert p.checkpoint.checkpoint_id!=old['checkpoint_id']
    assert len([n for n in plan.nuclei if n.retention=='required' and set(n.source_fields)&gp._TEXT_SOURCE_FIELDS])==5
    moves=plan.response_plan.human_reception_plan.moves
    assert len(moves)==2 and moves[1].target_nucleus_ids==(unknown.nucleus_id,)
    assert not {event.nucleus_id,reaction.nucleus_id}&{x for m in moves for x in (*m.target_nucleus_ids,*m.support_nucleus_ids)}
    selected=project_thread_meaning(p,plan).selected_reception
    pair,other=selected.decisions
    assert type(pair.retained_relief_cognition) is c.RetainedReliefCognitionContentV1
    assert len(pair.subjective_proposition.response_object_refs)==3
    assert pair.subjective_proposition==other.subjective_proposition
    assert set(pair.selected_contribution_refs).isdisjoint(other.selected_contribution_refs)
    out=MeaningExperienceEngine().generate(req);assert out.artifact,out.reason_codes
    assert ('よくわからないのですね。' if case == 'self_unknown' else 'まだわからないのですね。') in out.artifact.reception
    assert '私も少し安心しましたが' in out.artifact.reception
    assert 'かもしれない' not in out.artifact.reception
    if old['artifact']:
        assert out.artifact.observation==old['artifact']['observation']
        assert encoded(out.question)==old['question'] and encoded(out.question_decision)==old['question_decision']
    again=checkpoint(req,p.checkpoint.checkpoint_id)
    assert MeaningExperienceEngine().generate(again).artifact==out.artifact
    if profile=='q3':export('initial-'+case,req,out)


@pytest.mark.parametrize('profile',['q1','q3'])
@pytest.mark.parametrize('case',UPDATES)
def test_one_existing_answer_keeps_unknown_or_expires_the_new_duty(case,profile):
    req=request(case,profile,True);old=UPDATES[case][profile]
    if case=='without_unknown_add':full_snapshot(req,old);return
    p=update.prepare_emlis_meaning(req)
    if 'plan_error' in old and case not in UPDATED:
        with pytest.raises(ValueError) as exc:update.build_updated_grounded_plan(p)
        assert str(exc.value)==old['plan_error']
        out=MeaningExperienceEngine().generate(req);assert encoded(out.artifact)==old['artifact']
        return
    plan=update.build_updated_grounded_plan(p)
    duties=update._retained_unchanged_relief_cognition_duties(p,plan.nuclei,plan.relations)
    out=MeaningExperienceEngine().generate(req)
    if case in UPDATED:
        assert len(duties)==3
        selected=project_thread_meaning(p,plan).selected_reception
        assert len(selected.decisions)==3
        pair=selected.decisions[0];content=pair.retained_relief_cognition
        assert type(content) is c.RetainedUpdatedReliefCognitionContentV2 and content.schema_version=='2.0'
        assert len(pair.subjective_proposition.response_object_refs)==4
        assert len(content.basis_rows)==len(content.qualifier_rows)==2
        refs=[set(d.selected_contribution_refs) for d in selected.decisions]
        assert all(refs[i].isdisjoint(refs[j]) for i in range(3) for j in range(i+1,3))
        assert set.union(*refs)==set(pair.subjective_proposition.target_contribution_refs)
        unknown_id=content.eligibility.unknown_nucleus_ref
        assert next(n for n in plan.nuclei if n.nucleus_id==unknown_id)==next(n for n in p.original_plan.nuclei if n.nucleus_id==unknown_id)
        assert out.artifact,out.reason_codes
        assert out.artifact.reception.count('何が不安なのか、あなたにもまだわからないのですね。')==1
        assert '今、耳を傾けていたいです。' in out.artifact.reception
        assert 'かもしれない' not in out.artifact.reception
        assert out.artifact.observation==old['artifact']['observation']
        if case=='withdraw':assert '褒められた' not in out.artifact.text
        elif case=='revise':assert '嬉しくなかった' not in out.artifact.text and '悲しかった' in out.artifact.observation
        assert encoded(out.question)==old['question'] and encoded(out.question_decision)==old['question_decision']
        assert MeaningExperienceEngine().generate(checkpoint(req,p.checkpoint.checkpoint_id)).artifact==out.artifact
    elif p.checkpoint.answer_update.disposition == 'NO_MATERIAL_UPDATE':
        assert not duties and plan == p.original_plan
        assert len(plan.response_plan.human_reception_plan.moves) == 2
        assert out.artifact is None and out.body_state == 'UNCHANGED'
        assert out.reason_codes == ('reuse_saved_observation_required',)
    else:
        assert len(duties)!=3
        assert (out.artifact.text if out.artifact else None)==(None if old['artifact'] is None else '見えたこと：\n'+old['artifact']['observation']+'\n\nEmlisから：\n'+old['artifact']['reception'])
    if profile=='q3':export('update-'+case,req,out)


@pytest.fixture(scope='module',params=['initial','add','revise','withdraw'])
def context(request):
    case=request.param
    req=globals()['request']('mixed') if case=='initial' else globals()['request'](case,'q3',True)
    return actual(request=req)


@pytest.mark.parametrize('mutation',['unknown','object','owner','past','resolved','cause','pair','answer','certainty'])
def test_body_inverse_rejects_loss_without_using_the_author(context,mutation):
    out,*_=context;body=out.artifact.text;follow=out.artifact.reception
    sentence='何が不安なのか、あなたにもまだわからないのですね。'
    if mutation=='unknown':changed=body.replace(sentence,'')
    elif mutation=='object':changed=body.replace(sentence,sentence.replace('不安','喜び'))
    elif mutation=='owner':changed=body.replace(sentence,sentence.replace('あなた','友人'))
    elif mutation=='past':changed=body.replace(sentence,sentence.replace('わからない','わからなかった'))
    elif mutation=='resolved':changed=body.replace(sentence,sentence.replace('まだわからない','もうわかった'))
    elif mutation=='cause':changed=body.replace(sentence,'だから、'+sentence)
    elif mutation=='pair':changed=body.replace('私も少し安心しましたが、','')
    elif mutation=='answer':changed=body.replace(out.artifact.observation.splitlines()[1],'')
    else:changed=body.replace('かもしれない','に違いない')
    assert changed!=body
    with patch.object(surface,'_realize_line',side_effect=AssertionError('no author oracle')):
        assert read_body(context,body).passed
        assert not read_body(context,changed).passed


@pytest.fixture(scope='module')
def updated_context():return actual(request=request('add','q3',True))


@pytest.mark.parametrize('mutation',['checkpoint','unknown','unknown_move','unknown_contribution','erase_unknown_decision','downgrade'])
def test_resealed_v2_cannot_borrow_or_erase_the_unknown(updated_context,mutation):
    _,plan,_,resolver,selected=updated_context
    pair=selected.decisions[0];local=pair.retained_relief_cognition;eligibility=local.eligibility
    decisions=selected.decisions
    if mutation=='checkpoint':local=replace(local,eligibility=replace(eligibility,checkpoint_ref='forged'))
    elif mutation=='unknown':local=replace(local,eligibility=replace(eligibility,unknown_nucleus_ref=eligibility.relief_nucleus_ref))
    elif mutation=='unknown_move':local=replace(local,eligibility=replace(eligibility,unknown_move_ref=decisions[1].move_id))
    elif mutation=='downgrade':local=replace(local,schema_version='cocolon.cmee.retained_updated_relief_cognition_content.v1')
    elif mutation=='erase_unknown_decision':decisions=decisions[:2]
    else:decisions=(*decisions[:2],replace(decisions[2],selected_contribution_refs=decisions[1].selected_contribution_refs))
    local=replace(local,seal_ref=c.retained_relief_cognition_seal(local))
    forged=hr.identify_selected_subjective_reception_decision(replace(pair,retained_relief_cognition=local))
    altered=hr.identify_selected_subjective_reception_input(replace(selected,decisions=(forged,*decisions[1:])))
    with pytest.raises((ValueError,c.CMEEStage1ContractError)):
        validate_retained_relief_cognition_source(forged,altered,plan,resolver)


def test_current_manifest_versions_the_two_new_private_contracts():
    from dataclasses import fields
    from cocolon_meaning_experience_engine.emlis_stage1_composition import _contract_manifest
    manifest = dict(_contract_manifest())
    descriptors = {dict(row)['type_name']: dict(row) for row in manifest['logical_contract_descriptors']}
    assert manifest['logical_contract_count'] == 83
    for cls in (c.RetainedUpdatedReliefCognitionEligibilityV2, c.RetainedUpdatedReliefCognitionContentV2):
        row = descriptors[cls.__name__]
        assert row['logical_version'] == 'retained-updated-relief-cognition-v2'
        assert row['serialization_boundary'] == 'REQUEST_LOCAL_PRIVATE_CANONICAL_VIEW'
        assert tuple(dict(f)['field_name'] for f in row['fields']) == tuple(f.name for f in fields(cls))
    assert descriptors['RetainedUpdatedReliefCognitionEligibilityV1']['logical_version'] == 'retained-updated-relief-cognition-v1'
    assert descriptors['RetainedUpdatedReliefCognitionContentV1']['logical_version'] == 'retained-updated-relief-cognition-v1'


@pytest.mark.parametrize('case', ['add', 'revise', 'withdraw'])
def test_updated_reader_requires_the_separate_answer_reception(case):
    ctx = actual(request=request(case, 'q3', True))
    out, *_ = ctx
    phrases = {'add': '褒められたことについて、回答した時点では嬉しいのですね。',
               'revise': '褒められたことについて、その時の悲しさに目が留まり、それを小さくせずに受け止めています。',
               'withdraw': 'その時は嬉しくなかったのですね。'}
    assert phrases[case] in out.artifact.reception
    changed = out.artifact.text.replace(phrases[case], '')
    with patch.object(surface, '_realize_line', side_effect=AssertionError('no author oracle')):
        assert not read_body(ctx, changed).passed
