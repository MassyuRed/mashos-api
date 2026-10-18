"""Initial independent experiences support the already approved pair reference.

Meaning selection and question decisions stay identical to untouched u346.
Unknown Reception is not introduced by an Observation layout repair.
"""
from dataclasses import replace
from functools import lru_cache
import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest
import emlis_ai_grounded_sentence_surface as surface
from cocolon_meaning_experience_engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning, build_updated_grounded_plan
from cocolon_meaning_experience_engine.emlis_thread_projection import project_thread_meaning
from test_cmee_emlis_contrast_degree import encoded, digest
from test_cmee_emlis_q1_thread import initial
from test_cmee_emlis_q3_thread import begin, advance
from test_cmee_emlis_received_discourse import actual
from test_cmee_emlis_detached_observation import read_body

BASELINE=json.loads((Path(__file__).parent/'fixtures/cmee_emlis_u346_initial_layout_v1.json').read_text())
ROWS={r['case']:r for r in BASELINE['cases']}
SHORTENED={'mixed','unknown','self','degree','kana','past_unknown','cause_unknown'}


@lru_cache(None)
def request(case,profile):
    return (initial if profile=='q1' else begin)(ROWS[case]['memo'])


def same_meaning_and_decision(req,old):
    p=prepare_emlis_meaning(req)
    assert digest(p.checkpoint)==old['checkpoint_sha']
    assert digest(p.original_plan)==old['original_plan_sha']
    if 'plan_error' in old:
        with pytest.raises(ValueError) as exc: build_updated_grounded_plan(p)
        assert str(exc.value)==old['plan_error']
    else:
        plan=build_updated_grounded_plan(p)
        assert digest(plan)==old['plan_sha']
        if 'projection_error' in old:
            with pytest.raises(ValueError) as exc: project_thread_meaning(p,plan)
            assert str(exc.value)==old['projection_error']
        else:
            assert digest(project_thread_meaning(p,plan).selected_reception)==old['selected_sha']
    out=MeaningExperienceEngine().generate(req)
    assert encoded(out.question)==old['question']
    assert encoded(out.question_decision)==old['question_decision']
    assert list(out.reason_codes)==old['reasons']
    assert out.status.value==old['status'] and out.body_state==old['body_state']
    return out


@pytest.mark.parametrize('case',ROWS)
@pytest.mark.parametrize('profile',['q1','q3'])
def test_initial_meaning_question_and_complete_source_are_preserved(case,profile):
    assert BASELINE['source_commit']=='b2e1306cf2a742aeb063e6245cbd81a7c0bf2260'
    old=ROWS[case][profile];req=request(case,profile)
    out=same_meaning_and_decision(req,old)
    if profile=='q3' and (folder:=os.environ.get('CMEE_INITIAL_LAYOUT_BODY_DIR')):
        Path(folder).mkdir(parents=True,exist_ok=True)
        Path(folder,case+'.json').write_text(json.dumps(dict(case=case,memo=ROWS[case]['memo'],
            body=out.artifact.text if out.artifact else None,reason_codes=list(out.reason_codes)),ensure_ascii=False,indent=2)+'\n')
    if case in SHORTENED:
        assert out.artifact
        obs,follow=out.artifact.observation,out.artifact.reception
        assert len(obs.splitlines())>len(old['artifact']['observation'].splitlines())
        # Only a separator changes in Observation: no word, order or relation does.
        assert obs.replace('\n',' ')==old['artifact']['observation'].replace('\n',' ')
        assert 'かもしれない' in obs and 'かもしれない' not in follow
        assert 'ほっとしたと聞いて、私も少し安心しましたが、その' in follow
        assert '今、耳を傾けていたいです。' in follow
        assert len(follow)<len(old['artifact']['reception'])
        assert encoded(replace(out.artifact,artifact_id=old['artifact']['artifact_id'],
            observation=old['artifact']['observation'],reception=old['artifact']['reception']))==old['artifact']
    elif case=='ambiguous':
        assert out.artifact.reception==old['artifact']['reception']
        assert out.artifact.observation.replace('\n',' ')==old['artifact']['observation'].replace('\n',' ')
    else:
        assert encoded(out.artifact)==old['artifact']
    saved=replace(req,emlis_thread=replace(req.emlis_thread,prepared_meaning_checkpoint_ref=old['checkpoint_id']))
    assert MeaningExperienceEngine().generate(saved).artifact==out.artifact


@pytest.mark.parametrize('row',BASELINE['updates'],ids=lambda r:r['case'])
@pytest.mark.parametrize('profile',['q1','q3'])
def test_one_answer_full_result_is_unchanged(row,profile):
    req=advance((initial if profile=='q1' else begin)(row['memo']),row['answer'])
    out=same_meaning_and_decision(req,row[profile])
    assert encoded(out.artifact)==row[profile]['artifact']


@pytest.fixture(scope='module')
def context():
    from cocolon_meaning_experience_engine import emlis_thread_surface
    original=emlis_thread_surface.evaluate_grounded_observation_gate
    def capture(**kwargs):
        CAPTURED.update(kwargs)
        return original(**kwargs)
    with patch.object(emlis_thread_surface,'evaluate_grounded_observation_gate',capture):
        return actual(request=request('unknown','q3'))


CAPTURED={}


@pytest.mark.parametrize('mutation',['join','pair_loss','other_loss','unknown_loss','duplicate',
    'modality','owner','time','contrast','reaction','listening'])
def test_actual_body_reader_rejects_loss_without_using_author(context,mutation):
    out,plan,sentence,resolver,selected=context
    body=out.artifact.text;obs=out.artifact.observation
    if mutation=='join':changed=body.replace(obs,obs.replace('\n',' '))
    elif mutation=='pair_loss':changed=body.replace(obs.splitlines()[0]+'\n','')
    elif mutation=='other_loss':changed=body.replace(obs.splitlines()[1]+'\n','')
    elif mutation=='unknown_loss':changed=body.replace(obs.splitlines()[-1],'')
    elif mutation=='duplicate':changed=body.replace(obs,obs+'\n'+obs.splitlines()[0])
    elif mutation=='modality':changed=body.replace('かもしれない','に違いない')
    elif mutation=='owner':changed=body.replace('一人で休めた','友人が一人で休めた')
    elif mutation=='time':changed=body.replace('ほっとした','ほっとする',1)
    elif mutation=='contrast':changed=body.replace('の一方で','が原因で')
    elif mutation=='reaction':changed=body.replace('私も少し安心しましたが、','')
    else:changed=body.replace('今、耳を傾けていたいです','違いを感じています')
    assert body!=changed
    with patch.object(surface,'_realize_line',side_effect=AssertionError('no author oracle')):
        assert read_body(context,body).passed
        assert not read_body(context,changed).passed


@pytest.mark.parametrize('case',['mixed','unknown','degree'])
def test_old_completion_setup_matches_untouched_u346(case):
    with patch.object(surface,'_retained_relief_observation_pair',return_value=frozenset()):
        old=MeaningExperienceEngine().generate(request(case,'q3'))
    assert encoded(old.artifact)==ROWS[case]['q3']['artifact']


def test_cross_experience_relation_prevents_layout_split(context):
    _,plan,_,resolver,_=context
    pair=surface._retained_relief_observation_pair(plan,resolver)
    assert len(pair)==2
    other=next(n.nucleus_id for n in plan.nuclei if n.nucleus_id not in pair and n.kind=='event')
    relation=next(r for r in plan.relations if r.from_nucleus_id in pair)
    crossing=replace(relation,relation_id='synthetic-cross-experience',to_nucleus_id=other)
    assert not surface._retained_relief_observation_pair(replace(plan,relations=(*plan.relations,crossing)),resolver)


def test_standalone_pair_has_no_new_component_arc():
    p=prepare_emlis_meaning(request('pair_only','q3'))
    assert not surface._retained_relief_observation_pair(build_updated_grounded_plan(p),p.thread.resolver())


def test_initial_same_experience_fragmentation_is_rejected(context):
    from emlis_ai_grounded_observation_gate import _semantic_subcheck_reasons
    _,plan,sentence,resolver,_=context
    lines=[line for line in sentence.lines if line.binding.line_role!='human_follow']
    assert len(lines)==3
    owner=lines[0]
    split=surface._make_line(sentence_number=len(sentence.lines)+1,
        line_role=owner.binding.line_role,surface_function='observe_nuclei',
        nucleus_ids=owner.binding.nucleus_ids[:1],relation_ids=(),
        nucleus_index={n.nucleus_id:n for n in plan.nuclei},
        relation_index={r.relation_id:r for r in plan.relations},
        claim_scope=owner.binding.claim_scope,recovery_stage='full',plan=plan,resolver=resolver)
    reasons=_semantic_subcheck_reasons(plan=plan,sentence_plan=replace(sentence,lines=(*sentence.lines,split)),
        surface_result=CAPTURED['surface_result'],resolver=resolver)
    assert 'required_arc_fragmented_without_reason' in reasons[2]
