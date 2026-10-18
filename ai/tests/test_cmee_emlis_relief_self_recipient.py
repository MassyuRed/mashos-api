"""A surviving source-owned feeling remains the user's in indirect speech."""
from dataclasses import replace
from pathlib import Path
import json
from unittest.mock import patch

import pytest
import emlis_ai_grounded_human_reception as hr
import emlis_ai_grounded_sentence_surface as surface
from cocolon_meaning_experience_engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning, build_updated_grounded_plan
from cocolon_meaning_experience_engine.emlis_thread_projection import project_thread_meaning
from test_cmee_emlis_relief_cognition import BASE, LEFT, RIGHT, encoded, digest
from test_cmee_emlis_q3_thread import begin, advance
from test_cmee_emlis_source_scope_regressions import request as initial_request
from test_cmee_emlis_received_discourse import actual
from test_cmee_emlis_detached_observation import read_body
from test_emlis_q3_application import qdb, qcase
from test_emlis_q2_application import run, answer

BASELINE = json.loads((Path(__file__).parent/'fixtures/cmee_emlis_u336_self_recipient_v1.json').read_text())


def updated(row, *, legacy=False):
    req=begin(row['memo'])
    if legacy:
        req=replace(req,emlis_thread=replace(req.emlis_thread,
            prepared_meaning_checkpoint_ref=row['initial_checkpoint']['checkpoint_id']))
    req=advance(req,row['reply'])
    if legacy:
        req=replace(req,emlis_thread=replace(req.emlis_thread,
            prepared_meaning_checkpoint_ref=row['checkpoint']['checkpoint_id']))
    return req


@pytest.mark.parametrize('row',BASELINE['cases'],ids=lambda r:r['case'])
def test_corrected_or_withdrawn_partner_keeps_complete_user_owned_survivor(row):
    out=MeaningExperienceEngine().generate(updated(row))
    assert out.artifact and row['body']
    assert out.artifact.observation==row['body']['observation']
    old=row['body']['reception']
    owner=row['memo'][:row['memo'].index(LEFT)]
    expected=old.replace(owner+LEFT,'あなた'+owner[-1]+LEFT,1) if owner else old
    assert out.artifact.reception==expected
    assert '私も少し安心しました' not in out.artifact.reception
    assert '耳を傾けていたい' not in out.artifact.reception
    assert encoded(out.question)==row['question'] if out.question else row['question'] is None
    assert list(out.reason_codes)==row['reasons']


@pytest.mark.parametrize('row',BASELINE['cases'],ids=lambda r:r['case'])
def test_complete_u336_update_checkpoint_keeps_every_old_field(row):
    req=updated(row,legacy=True);p=prepare_emlis_meaning(req)
    assert encoded(p.checkpoint)==row['checkpoint']
    plan=build_updated_grounded_plan(p)
    assert digest(plan)==row['plan_sha']
    assert digest(project_thread_meaning(p,plan).selected_reception)==row['selected_sha']
    out=MeaningExperienceEngine().generate(req)
    assert encoded(out.artifact)==row['body']
    assert (encoded(out.question) if out.question else None)==row['question']
    assert list(out.reason_codes)==row['reasons']


@pytest.fixture(scope='module')
def context():
    return actual(request=updated(BASELINE['cases'][0]))


@pytest.mark.parametrize('before,after',[
    ('あなたは','私は'),('あなたは','友達は'),('あなたは','あなたが'),
    ('休めたことにほっとした','休めなかったことにほっとした'),
    ('ほっとしたという気持ち','ほっとしなかったという気持ち'),
    ('ほっとしたという気持ち','ほっとするという気持ち'),
    ('ほっとしたという気持ち','少しほっとしたという気持ち'),
    ('友達からの誘い','上司からの誘い'),
    ('という気持ちを受け止めています','という気持ちが正解だと思います'),
])
def test_independent_reader_rejects_changes_to_user_experience(context,before,after):
    out=context[0]
    changed=out.artifact.reception.replace(before,after)
    assert changed!=out.artifact.reception
    with patch.object(hr,'_source_owned_relief_survivor_sentence',side_effect=AssertionError('no author')):
        with patch.object(surface,'_realize_line',side_effect=AssertionError('no observation author')):
            assert read_body(context,out.artifact.text).passed
            assert not read_body(context,out.artifact.text.replace(out.artifact.reception,changed)).passed


@pytest.mark.parametrize('memo',[
    BASE, '友達は'+BASE, '「私は'+BASE+'」', '私は'+BASE+'これは友人の話です。',
    '私の部屋で'+BASE, '私は'+BASE.replace('ほっとした','ほっとしなかった'),
])
def test_unqualified_sources_cannot_gain_recipient_version(memo):
    p=prepare_emlis_meaning(begin(memo));plan=build_updated_grounded_plan(p)
    assert not any('source_relief_self_recipient:v1' in n.semantic_frame.attribute_codes for n in plan.nuclei)


def test_forged_checkpoint_cannot_reuse_old_recipient_surface():
    row=BASELINE['cases'][0];req=updated(row)
    req=replace(req,emlis_thread=replace(req.emlis_thread,
        prepared_meaning_checkpoint_ref=row['checkpoint']['checkpoint_id']+'forged'))
    with pytest.raises(ValueError,match='emlis_checkpoint_source_prefix_mismatch'):
        prepare_emlis_meaning(req)


@pytest.mark.parametrize('row',BASELINE['initial_cases'],ids=lambda r:r['case'])
def test_current_initial_body_question_and_reasons_stay_unchanged(row):
    out=MeaningExperienceEngine().generate(initial_request(row['memo']))
    assert bool(out.artifact)==bool(row['body'])
    if out.artifact:
        assert out.artifact.observation==row['body']['observation']
        assert out.artifact.reception==row['body']['reception']
    assert (encoded(out.question) if out.question else None)==row['question']
    assert list(out.reason_codes)==row['reasons']


@pytest.mark.parametrize('row',BASELINE['initial_cases'],ids=lambda r:r['case'])
def test_complete_u336_initial_checkpoint_and_body_stay_unchanged(row):
    req=initial_request(row['memo'])
    req=replace(req,emlis_thread=replace(req.emlis_thread,
        prepared_meaning_checkpoint_ref=row['checkpoint']['checkpoint_id']))
    p=prepare_emlis_meaning(req)
    assert encoded(p.checkpoint)==row['checkpoint']
    plan=build_updated_grounded_plan(p)
    assert digest(plan)==row['plan_sha']
    if 'error' in row:
        with pytest.raises(ValueError) as failure:
            project_thread_meaning(p,plan)
        assert str(failure.value)==row['error']
    else:
        assert digest(project_thread_meaning(p,plan).selected_reception)==row['selected_sha']
    out=MeaningExperienceEngine().generate(req)
    assert (encoded(out.artifact) if out.artifact else None)==row['body']
    assert (encoded(out.question) if out.question else None)==row['question']
    assert list(out.reason_codes)==row['reasons']


@pytest.mark.parametrize('field,value',[
    ('appraised_bindings',('foreign-binding',)),
    ('basis_contribution_refs',('foreign-contribution',)),
])
@pytest.mark.parametrize('append',[False,True])
def test_independent_reader_rejects_reidentified_foreign_appraisal_basis(context,field,value,append):
    selected=context[4]
    decision,=tuple(d for d in selected.decisions if d.reception_act=='recognize_lived_change')
    original=decision.subjective_proposition.appraisal_content
    content=replace(original,**{field:(getattr(original,field)+value if append else value)})
    changed_decision=hr.identify_selected_subjective_reception_decision(replace(
        decision,decision_ref='',subjective_proposition=replace(
            decision.subjective_proposition,appraisal_content=content)))
    changed=hr.identify_selected_subjective_reception_input(replace(selected,input_ref='',
        decisions=tuple(changed_decision if d==decision else d for d in selected.decisions)))
    with patch.object(hr,'_source_owned_relief_survivor_sentence',side_effect=AssertionError('no author')):
        with patch.object(surface,'_realize_line',side_effect=AssertionError('no observation author')):
            assert not read_body((*context[:4],changed),context[0].artifact.text).passed


@pytest.mark.parametrize('row',BASELINE['cases'][:3],ids=lambda r:r['case'])
def test_service_saves_survivor_and_rereads_it_without_generation(qcase,qdb,row):
    from emlis_thread_service import EmlisThreadService,Q3_PROFILE
    user,parent,service=qcase
    qdb.query('update public.emotions set memo=$2 where id=$1',[parent,row['memo']])
    first=run(service.start(user,parent))
    assert first['pending_question']
    saved=run(answer(service,user,first,row['reply'],'self-recipient'))
    assert saved['body_state']=='REFINED' and saved['original']==first['original']
    assert 'あなたは'+LEFT in saved['current_observation']['text']
    class NoGeneration:
        def __getattr__(self,name):
            raise AssertionError('saved body tried generation: '+name)
    reader=EmlisThreadService(runtime_profile=Q3_PROFILE,engine=NoGeneration())
    assert run(reader.get(user,parent))==saved
    assert run(reader.start(user,parent))==saved
