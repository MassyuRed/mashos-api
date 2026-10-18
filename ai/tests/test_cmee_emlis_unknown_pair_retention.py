"""Keep an already selected relief pair when an independent unknown coexists.

The unknown remains a source-owned Observation object. No third Reception
move is introduced, and saved u345 meanings still reproduce in full.
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
from cocolon_meaning_experience_engine import emlis_answer_update as update
from cocolon_meaning_experience_engine.emlis_thread_projection import project_thread_meaning
from test_cmee_emlis_contrast_degree import encoded, digest
from test_cmee_emlis_q1_thread import initial
from test_cmee_emlis_q3_thread import begin, advance
from test_cmee_emlis_received_discourse import actual
from test_cmee_emlis_detached_observation import read_body

BASELINE = json.loads((Path(__file__).parent/'fixtures/cmee_emlis_u345_unknown_pair_retention_v1.json').read_text())
ROWS = {r['case']:r for r in BASELINE['cases']}
# The frozen label "scalar" is the existing wh-object "どれくらい不安なのか";
# it is not a bare, objectless unknown and uses the unchanged source grammar.
IMPROVED = {'now_positive','past_positive','now_negative','revise_other','withdraw_event','degree','kana','self_other','scalar'}


def checkpoint(req, ref):
    return replace(req, emlis_thread=replace(req.emlis_thread, prepared_meaning_checkpoint_ref=ref))


@lru_cache(None)
def request(case, profile, answered=False):
    r=ROWS[case]; req=(initial if profile=='q1' else begin)(r['memo'])
    return advance(req,r['answer']) if answered else req


def snapshot(req, frozen):
    p=update.prepare_emlis_meaning(req)
    assert encoded(p.checkpoint)==frozen['checkpoint']
    assert digest(p.checkpoint)==frozen['checkpoint_sha']
    assert p.thread.source_prefix_ref==frozen['source_prefix']
    assert encoded(p.thread.original.evidence_spans)==frozen['spans']
    if 'plan_error' in frozen:
        with pytest.raises(ValueError) as exc: update.build_updated_grounded_plan(p)
        assert str(exc.value)==frozen['plan_error']
    else:
        plan=update.build_updated_grounded_plan(p)
        assert digest(plan)==frozen['plan_sha']
        assert encoded(plan.nuclei)==frozen['nuclei']
        assert encoded(plan.relations)==frozen['relations']
        if 'projection_error' in frozen:
            with pytest.raises(ValueError) as exc: project_thread_meaning(p,plan)
            assert str(exc.value)==frozen['projection_error']
        else:
            assert digest(project_thread_meaning(p,plan).selected_reception)==frozen['selected_sha']
    out=MeaningExperienceEngine().generate(req)
    for field in ('artifact','question','question_decision'):
        assert encoded(getattr(out,field))==frozen[field]
    assert list(out.reason_codes)==frozen['reasons']
    assert out.status.value==frozen['status'] and out.body_state==frozen['body_state']
    return p


@pytest.mark.parametrize('profile',['q1','q3'])
@pytest.mark.parametrize('case',ROWS)
def test_initial_and_old_saved_answer_reproduce_full_u345(case,profile):
    assert BASELINE['source_commit']=='54e2adbb35d013cded34bc65faa46286467deadd'
    row=ROWS[case][profile]
    snapshot(request(case,profile),row['initial'])
    if 'answer_error' in row:
        with pytest.raises(AssertionError) as exc: request(case,profile,True)
        assert str(exc.value).splitlines()[0]==row['answer_error']
        return
    saved=row['updated']
    snapshot(checkpoint(request(case,profile,True),saved['checkpoint_id']),saved)


def assert_current(case,profile):
    r=ROWS[case]; frozen=r[profile]['updated']; req=request(case,profile,True)
    p=update.prepare_emlis_meaning(req); plan=update.build_updated_grounded_plan(p)
    assert not p.legacy_relief_cognition_update_retention
    assert p.checkpoint.checkpoint_id!=frozen['checkpoint_id']
    assert p.thread.source_prefix_ref==frozen['source_prefix']
    assert encoded(p.thread.original.evidence_spans)==frozen['spans']
    assert digest(p.original_plan)==r[profile]['initial']['plan_sha']
    unknown,= [n for n in p.original_plan.nuclei if n.kind=='uncertainty' and n.retention=='required']
    assert next(n for n in plan.nuclei if n.nucleus_id==unknown.nucleus_id)==unknown
    assert not any(unknown.nucleus_id in (e.from_nucleus_id,e.to_nucleus_id) for e in plan.relations)
    if case!='withdraw_event':
        assert encoded(plan.nuclei)==frozen['nuclei']
        assert encoded(plan.relations)==frozen['relations']
    else:
        inactive=set(p.checkpoint.inactive_claim_refs)
        expected=[n for n in p.original_plan.nuclei if n.nucleus_id not in inactive]
        reaction=next(n for n in expected if n.source_span_ids==('s4',) and n.kind=='reaction')
        expected=[replace(n,semantic_frame=replace(n.semantic_frame,attribute_codes=(*n.semantic_frame.attribute_codes,
            'thread_subject:withdrawn_source_event','thread_subject:unchanged_relief_pair_withdrawal:v1'))) if n==reaction else n for n in expected]
        assert plan.nuclei==tuple(expected)
        assert plan.relations==tuple(e for e in p.original_plan.relations if e.relation_id not in inactive)
    moves=plan.response_plan.human_reception_plan.moves
    assert len(moves)==2 and len(p.original_plan.response_plan.human_reception_plan.moves)==1
    assert unknown.nucleus_id not in {nid for m in moves for nid in (*m.target_nucleus_ids,*m.support_nucleus_ids)}
    from test_cmee_emlis_relief_cognition import facets
    selected=project_thread_meaning(p,plan).selected_reception
    content,=facets(selected)
    assert content.reaction=='BOUNDED_RELIEF_AT_REPORTED_RELIEF'
    assert content.response=='LISTEN_TO_PRESENT_LONELINESS_UNDER_UNCERTAINTY'
    assert len(selected.decisions)==2
    out=MeaningExperienceEngine().generate(req)
    assert out.artifact, out.reason_codes
    obs,follow=out.artifact.observation,out.artifact.reception
    raw=next(s.raw_text for s in p.thread.original.evidence_spans if s.span_id==unknown.source_span_ids[0])
    assert raw in obs and raw not in follow
    assert len(obs.splitlines())==3
    assert 'かもしれない' in obs and 'かもしれない' not in follow
    assert '私も少し安心しましたが、その' in follow
    assert '今、耳を傾けていたいです。' in follow
    if case=='withdraw_event': assert '褒められた' not in out.artifact.text and '嬉しくなかった' in follow
    elif case=='revise_other':
        assert '嬉しくなかった' not in out.artifact.text
        assert '悲しかった' in obs and 'その時の悲しさ' in follow
    else:
        assert '嬉しくなかった' in obs
        assert 'その時' in follow if case=='past_positive' else '回答した時点' in follow
    assert not out.automatic_progression
    assert encoded(out.question)==frozen['question']
    decision=encoded(out.question_decision)
    if profile=='q3' and frozen['status']=='UNAVAILABLE':
        # A validated Q3 body reaches the real no-target decision. The old
        # unavailable-body fallback reported the free-profile stop reason.
        assert decision==dict(frozen['question_decision'],decision_reason='no_bound_personal_meaning_target')
    else: assert decision==frozen['question_decision']
    restored=checkpoint(req,p.checkpoint.checkpoint_id)
    again=update.prepare_emlis_meaning(restored); active=update.build_updated_grounded_plan(again)
    assert again.checkpoint==p.checkpoint and active==plan
    assert project_thread_meaning(again,active).selected_reception==selected
    assert MeaningExperienceEngine().generate(restored).artifact==out.artifact
    folder=os.environ.get('CMEE_UNKNOWN_PAIR_BODY_DIR')
    if folder and profile=='q3':
        Path(folder).mkdir(parents=True,exist_ok=True)
        Path(folder,case+'.json').write_text(json.dumps(dict(case=case,memo=r['memo'],answer=r['answer'],body=out.artifact.text),ensure_ascii=False,indent=2)+'\n')


@pytest.mark.parametrize('profile',['q1','q3'])
@pytest.mark.parametrize('case',ROWS)
def test_current_answer_retains_existing_pair_or_keeps_exact_control(case,profile):
    row=ROWS[case][profile]
    if 'answer_error' in row:
        with pytest.raises(AssertionError): request(case,profile,True)
    elif case in IMPROVED: assert_current(case,profile)
    else: snapshot(request(case,profile,True),row['updated'])


@pytest.fixture(scope='module')
def prepared():
    return update.prepare_emlis_meaning(request('now_positive','q3',True))


@pytest.mark.parametrize('mutation',['actor','past','kind','scope','anchor','required_edge','optional_edge','extra_move','no_move','target_unknown'])
def test_source_scope_cannot_be_extended_by_changed_meaning(prepared,mutation):
    source=update._unchanged_relief_cognition_update_source(prepared)
    assert source
    p=prepared; original=p.original_plan
    unknown=next(n for n in original.nuclei if n.kind=='uncertainty' and n.retention=='required')
    if mutation in {'actor','past','kind','scope','anchor'}:
        if mutation=='actor': changed=replace(unknown,semantic_frame=replace(unknown.semantic_frame,actor='other_person'))
        elif mutation=='past': changed=replace(unknown,semantic_frame=replace(unknown.semantic_frame,time_scope='past'))
        elif mutation=='kind': changed=replace(unknown,kind='reaction')
        elif mutation=='scope': changed=replace(unknown,allowed_claim_scope='explicit_supplemental_answer')
        else: changed=replace(unknown,surface_anchor_ids=('s1',))
        original=replace(original,nuclei=tuple(changed if n==unknown else n for n in original.nuclei))
    elif mutation.endswith('_edge'):
        edge=replace(original.relations[-1],relation_id='injected',to_nucleus_id=unknown.nucleus_id,
            retention='required' if mutation=='required_edge' else 'optional')
        original=replace(original,relations=(*original.relations,edge))
    elif mutation in {'extra_move','no_move'}:
        reception=original.response_plan.human_reception_plan
        move=replace(reception.moves[0],move_id='unknown_move',target_nucleus_ids=(unknown.nucleus_id,),support_nucleus_ids=())
        reception=replace(reception,moves=(*reception.moves,move) if mutation=='extra_move' else ())
        original=replace(original,response_plan=replace(original.response_plan,human_reception_plan=reception))
    else:
        item,=p.checkpoint.answer_update.updates
        p=replace(p,checkpoint=replace(p.checkpoint,answer_update=replace(p.checkpoint.answer_update,
            updates=(replace(item,target_meaning_refs=(unknown.nucleus_id,)),))))
    p=replace(p,original_plan=original)
    assert update._unchanged_relief_cognition_update_source(p) is None


@pytest.mark.parametrize('mutation',['changed_unknown','linked_unknown'])
def test_current_unknown_must_stay_exact_and_independent(prepared,mutation):
    plan=update.build_updated_grounded_plan(prepared)
    assert update._retained_unchanged_relief_cognition_duties(prepared,plan.nuclei,plan.relations)
    unknown=next(n for n in plan.nuclei if n.kind=='uncertainty' and n.retention=='required')
    nuclei,relations=plan.nuclei,plan.relations
    if mutation=='changed_unknown':
        changed=replace(unknown,semantic_frame=replace(unknown.semantic_frame,time_scope='past'))
        nuclei=tuple(changed if n==unknown else n for n in nuclei)
    else: relations=(*relations,replace(relations[-1],relation_id='injected',to_nucleus_id=unknown.nucleus_id,retention='optional'))
    assert not update._retained_unchanged_relief_cognition_duties(prepared,nuclei,relations)


@pytest.fixture(scope='module')
def context():
    return actual(request=request('degree','q3',True))


@pytest.mark.parametrize('mutation',['unknown','unknown_owner','unknown_object','pair','answer','certainty','relief_response','listening','answer_time'])
def test_independent_reader_rejects_loss_without_author_replay(context,mutation):
    out,*_=context; body=out.artifact.text; obs=out.artifact.observation
    if mutation=='unknown': changed=body.replace(obs.splitlines()[2],'')
    elif mutation=='unknown_owner': changed=body.replace('私にもまだわからない','友達にもまだわからない')
    elif mutation=='unknown_object': changed=body.replace('何が不安なのか','何が嬉しいのか')
    elif mutation=='pair': changed=body.replace(obs.splitlines()[0],'')
    elif mutation=='answer': changed=body.replace(obs.splitlines()[1],'')
    elif mutation=='certainty': changed=body.replace('かもしれない','に違いない')
    elif mutation=='relief_response': changed=body.replace('私も少し安心しましたが、','')
    elif mutation=='listening': changed=body.replace('今、耳を傾けていたいです','違いを感じています')
    else: changed=body.replace('回答した時点','その時')
    assert changed!=body
    with patch.object(surface,'_realize_line',side_effect=AssertionError('no author oracle')):
        assert read_body(context,body).passed
        assert not read_body(context,changed).passed
