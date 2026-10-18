"""Past SELF uncertainty keeps its object/time without a current-state claim."""
from dataclasses import replace
import json
from pathlib import Path
from unittest.mock import patch

import pytest
import emlis_ai_grounded_observation_plan as gp
import emlis_ai_grounded_human_reception as hr
import emlis_ai_grounded_sentence_surface as surface
from cocolon_meaning_experience_engine import MeaningExperienceEngine, contracts as c
from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning, build_updated_grounded_plan
from cocolon_meaning_experience_engine.emlis_thread_projection import project_thread_meaning
from test_cmee_emlis_relief_cognition import BASE, encoded, digest
from test_cmee_emlis_source_scope_regressions import request
from test_cmee_emlis_q1_thread import initial
from test_cmee_emlis_received_discourse import actual
from test_cmee_emlis_detached_observation import read_body

BASELINE = json.loads((Path(__file__).parent/'fixtures/cmee_emlis_u337_past_unknown_v1.json').read_text())
IMPROVED = {name+suffix for name in ('jibun_past','watashi_past','boku_past','self_suffix','ore','watashi_kana','boku_kana')
            for suffix in ('_single','_pair')}


def assert_record(req, row):
    p=prepare_emlis_meaning(req); plan=build_updated_grounded_plan(p)
    assert encoded(p.checkpoint)==row['checkpoint']
    assert digest(plan)==row['plan_sha']
    if 'error' in row:
        with pytest.raises(ValueError) as error: project_thread_meaning(p,plan)
        assert str(error.value)==row['error']
    else:
        assert digest(project_thread_meaning(p,plan).selected_reception)==row['selected_sha']
    out=MeaningExperienceEngine().generate(req)
    assert (encoded(out.artifact) if out.artifact else None)==row['body']
    assert (encoded(out.question) if out.question else None)==row['question']
    assert list(out.reason_codes)==row['reasons']
    return p


@pytest.mark.parametrize('row',BASELINE['cases'],ids=lambda r:r['case'])
def test_current_past_recognition_or_complete_unchanged_control(row):
    req=request(row['memo'])
    if row['case'] not in IMPROVED:
        assert_record(req,row)
        return
    p=prepare_emlis_meaning(req);plan=build_updated_grounded_plan(p)
    group=gp._source_past_self_unknown_from_resolver(plan.nuclei,plan.relations,p.thread.resolver())
    assert len(group)==(3 if row['case'].endswith('_pair') else 1)
    n=group[0];f=n.semantic_frame
    assert (n.kind,f.predicate_kind,f.actor,f.polarity,f.modality,f.time_scope)==(
        'uncertainty','uncertainty','current_user','negative','uncertain','past')
    unknown,=tuple(b for b in plan.unknown_boundaries if b.dimension=='source_explicit_epistemic_limit')
    assert unknown.affected_nucleus_ids==(n.nucleus_id,)
    assert unknown.evidence_span_ids==n.source_span_ids
    projection=project_thread_meaning(p,plan)
    disposition,=tuple(d for d in projection.premeaning.grounded_graph.owner_dispositions if d.target_unknown_ref)
    assert c.source_explicit_epistemic_unknown_object_ref(projection.premeaning,disposition)
    source=p.thread.resolver().resolve(n.source_span_ids[0]).raw_text
    out=MeaningExperienceEngine().generate(req)
    assert out.artifact and out.question is None and out.question_decision.disposition=='END'
    assert 'その時の認識として、「'+source+'」とあります。' in out.artifact.observation
    owner=gp._source_self_unknown_object_parts(source,past=True)
    a,b=owner.span('owner')
    if owner['owner']=='自分' and owner['self_suffix']:b=owner.end('self_suffix')
    recipient=source[:a]+('ご自身' if owner['owner']=='自分' else 'あなた')+source[b:]
    assert out.artifact.reception.endswith(recipient+'のですね。')
    assert '結論を急がず' not in out.artifact.reception
    if len(group)==3:
        assert out.artifact.reception.startswith('ほっとしたと聞いて、私も少し安心しましたが、その寂しさにも、今、耳を傾けていたいです。')
        assert len(projection.selected_reception.decisions)==2
    assert p.checkpoint.checkpoint_id!=row['checkpoint']['checkpoint_id']
    replay=replace(req,emlis_thread=replace(req.emlis_thread,prepared_meaning_checkpoint_ref=p.checkpoint.checkpoint_id))
    assert MeaningExperienceEngine().generate(replay).artifact==out.artifact


@pytest.mark.parametrize('row',BASELINE['cases'],ids=lambda r:r['case'])
def test_u337_checkpoint_restores_every_old_meaning_and_output_field(row):
    assert BASELINE['source_commit']=='c26ece428f59a01cf8928ab19bd5416b879c7d31'
    req=request(row['memo']);req=replace(req,emlis_thread=replace(req.emlis_thread,
        prepared_meaning_checkpoint_ref=row['checkpoint']['checkpoint_id']))
    p=assert_record(req,row)
    assert p.legacy_past_self_unknown==(row['case'] in IMPROVED)


@pytest.fixture(scope='module',params=['jibun_past_single','jibun_past_pair','self_suffix_pair'])
def context(request):
    row=next(r for r in BASELINE['cases'] if r['case']==request.param)
    # The public Q1 entry must select the same prepared meaning as Q3.
    req=initial(row['memo']);value=actual(request=req)
    assert MeaningExperienceEngine().generate(req).artifact.text==value[0].artifact.text
    return value


@pytest.mark.parametrize('mutation',['outer_time','inner_time','current_still','known','owner','degree','missing','cause','quote','observation_time'])
def test_independent_reader_rejects_changes_to_time_object_owner_and_duty(context,mutation):
    body=context[0].artifact.text
    if mutation=='outer_time': changed=body.replace('わからなかったのですね','わからないのですね').replace('分からなかったのですね','分からないのですね')
    elif mutation=='inner_time': changed=body.replace('何が嫌なのか、ご自身','何が嫌だったのか、ご自身')
    elif mutation=='current_still': changed=body.replace('ご自身でも','ご自身でも今も')
    elif mutation=='known': changed=body.replace('わからなかったのですね','わかったのですね').replace('分からなかったのですね','分かったのですね')
    elif mutation=='owner': changed=body.replace('ご自身','友達')
    elif mutation=='degree': changed=body.replace('でもよくわからなかったのですね','でもわからなかったのですね').replace('でもまだはっきり分からなかったのですね','でも分からなかったのですね')
    elif mutation=='missing':
        reception=context[0].artifact.reception
        changed=body.replace(reception,reception[:reception.rfind('。',0,len(reception)-1)+1] or '今ここに置かれた言葉を受け止めています。')
    elif mutation=='cause': changed=body.replace('何が嫌なのか、ご自身','だから、何が嫌なのか、ご自身')
    elif mutation=='quote': changed=body.replace('何が嫌なのか、ご自身','「何が嫌なのか、ご自身').replace('のですね。','」と聞きました。')
    else: changed=body.replace('その時の認識として、','今の認識として、')
    assert changed!=body
    with patch.object(hr,'_unknown_object_recipient',side_effect=AssertionError('no author')):
        with patch.object(surface,'_realize_line',side_effect=AssertionError('no observation author')):
            assert read_body(context,body).passed
            assert not read_body(context,changed).passed


def test_failed_dedicated_past_reader_cannot_fall_back_to_generic(context):
    import emlis_ai_grounded_observation_gate as gate
    with patch.object(gate,'_read_unknown_object_discourse',return_value=None):
        assert not read_body(context,context[0].artifact.text).passed


@pytest.mark.parametrize('mutation',['owner','time','kind','marker_missing','marker_version','marker_duplicate','span','optional','source_fields'])
def test_past_source_qualification_is_not_a_label(context,mutation):
    _,plan,_,resolver,_=context
    group=gp._source_past_self_unknown_from_resolver(plan.nuclei,plan.relations,resolver);n=group[0]
    f=n.semantic_frame;changed=n;relations=plan.relations
    if mutation=='owner':changed=replace(n,semantic_frame=replace(f,actor='other'))
    elif mutation=='time':changed=replace(n,semantic_frame=replace(f,time_scope='current_input'))
    elif mutation=='kind':changed=replace(n,kind='self_evaluation')
    elif mutation=='marker_missing':changed=replace(n,semantic_frame=replace(f,attribute_codes=tuple(v for v in f.attribute_codes if not v.startswith('source_past_self_unknown:'))))
    elif mutation=='marker_version':changed=replace(n,semantic_frame=replace(f,attribute_codes=tuple(v.replace('source_past_self_unknown:v1','source_past_self_unknown:v2') for v in f.attribute_codes)))
    elif mutation=='marker_duplicate':changed=replace(n,semantic_frame=replace(f,attribute_codes=(*f.attribute_codes,'source_past_self_unknown:v1')))
    elif mutation=='span':changed=replace(n,source_span_ids=('foreign-span',))
    elif mutation=='optional':changed=replace(n,retention='optional')
    elif mutation=='source_fields':changed=replace(n,source_fields=('answer_text_private',))
    assert not gp._source_past_self_unknown_from_resolver(tuple(changed if v==n else v for v in plan.nuclei),relations,resolver)


@pytest.mark.parametrize('mutation',['foreign_binding','foreign_contribution','response','primary','duplicate_decision','missing_selection'])
def test_independent_reader_requires_complete_selected_meaning(context,mutation):
    selected=context[4]
    group=gp._source_past_self_unknown_from_resolver(context[1].nuclei,context[1].relations,context[3])
    decision,=tuple(d for d in selected.decisions if d.target_nucleus_ids==(group[0].nucleus_id,))
    proposition=decision.subjective_proposition;appraisal=proposition.appraisal_content
    if mutation=='foreign_binding':
        proposition=replace(proposition,appraisal_content=replace(appraisal,appraised_bindings=(*appraisal.appraised_bindings,'foreign-binding')))
    elif mutation=='foreign_contribution':
        proposition=replace(proposition,appraisal_content=replace(appraisal,basis_contribution_refs=(*appraisal.basis_contribution_refs,'foreign-contribution')))
    elif mutation=='response':proposition=replace(proposition,response_object_refs=())
    elif mutation=='primary':proposition=replace(proposition,primary_target_refs=())
    changed=hr.identify_selected_subjective_reception_decision(replace(decision,decision_ref='',subjective_proposition=proposition))
    decisions=tuple(changed if d==decision else d for d in selected.decisions)
    if mutation=='duplicate_decision':decisions=(*decisions,changed)
    changed=hr.identify_selected_subjective_reception_input(replace(selected,input_ref='',decisions=decisions))
    if mutation=='missing_selection':changed=None
    assert not read_body((*context[:4],changed),context[0].artifact.text).passed


@pytest.mark.parametrize('mutation',['no_witness','time','owner','modality','polarity','duplicate_time','foreign_source'])
def test_unknown_binding_requires_the_complete_past_axes_and_source(mutation):
    p=prepare_emlis_meaning(request('何が嫌なのか、自分でもよくわからなかった。'))
    pre=project_thread_meaning(p,build_updated_grounded_plan(p)).premeaning
    d,=tuple(d for d in pre.grounded_graph.owner_dispositions if d.target_unknown_ref)
    ref=c.source_explicit_epistemic_unknown_object_ref(pre,d);assert ref
    q,=tuple(q for q in pre.source_qualifier_rows if q.node_ref==ref)
    codes=q.qualifier_refs
    if mutation=='no_witness':codes=tuple(v for v in codes if not v.startswith('qualifier:source_past_self_unknown:'))
    elif mutation=='duplicate_time':codes=(*codes,'time_scope:current_input')
    elif mutation=='foreign_source':
        graph=replace(pre.grounded_graph,nodes=tuple(replace(n,value='何が嫌なのか、友達でもわからなかった') if n.node_kind=='uncertainty' else n for n in pre.grounded_graph.nodes))
        pre=replace(pre,grounded_graph=graph)
    else:
        axis,value={'time':('time_scope','current_input'),'owner':('actor','other'),'modality':('modality','fact'),'polarity':('polarity','positive')}[mutation]
        codes=tuple(axis+':'+value if v.startswith(axis+':') else v for v in codes)
    changed=replace(q,qualifier_refs=codes)
    pre=replace(pre,source_qualifier_rows=tuple(changed if v==q else v for v in pre.source_qualifier_rows))
    assert c.source_explicit_epistemic_unknown_object_ref(pre,d) is None


def test_forged_old_checkpoint_cannot_select_a_legacy_interpretation():
    row=BASELINE['cases'][0];req=request(row['memo'])
    req=replace(req,emlis_thread=replace(req.emlis_thread,prepared_meaning_checkpoint_ref=row['checkpoint']['checkpoint_id']+'forged'))
    with pytest.raises(ValueError,match='emlis_checkpoint_source_prefix_mismatch'):
        prepare_emlis_meaning(req)


@pytest.mark.parametrize('mutation',['missing','duplicate','target','span','policy'])
def test_adapter_reproves_past_unknown_boundary_after_plan_equality(mutation):
    import cocolon_meaning_experience_engine.emlis_answer_update as update
    from cocolon_meaning_experience_engine.emlis_thread_projection import _project_thread_meaning_aggregate
    p=prepare_emlis_meaning(request('何が嫌なのか、自分でもよくわからなかった。'))
    plan=build_updated_grounded_plan(p)
    boundary,=tuple(b for b in plan.unknown_boundaries if b.dimension=='source_explicit_epistemic_limit')
    if mutation=='missing':boundaries=()
    elif mutation=='duplicate':boundaries=(boundary,boundary)
    elif mutation=='target':boundaries=(replace(boundary,affected_nucleus_ids=('foreign',)),)
    elif mutation=='span':boundaries=(replace(boundary,evidence_span_ids=('foreign',)),)
    else:boundaries=(replace(boundary,surface_policy='omit'),)
    changed=replace(plan,unknown_boundaries=boundaries)
    with patch.object(update,'build_updated_grounded_plan',return_value=changed):
        with pytest.raises(ValueError,match='emlis_thread_past_unknown_source_unbound'):
            _project_thread_meaning_aggregate(p,changed)


def test_asserted_edge_cannot_be_removed_to_manufacture_past_pair_eligibility():
    p=prepare_emlis_meaning(request(BASE+'何が嫌なのか、自分でもよくわからなかった。'))
    plan=build_updated_grounded_plan(p);resolver=p.thread.resolver()
    group=gp._source_past_self_unknown_from_resolver(plan.nuclei,plan.relations,resolver)
    edge=next(r for r in plan.relations if group[0].nucleus_id in (r.from_nucleus_id,r.to_nucleus_id))
    changed=replace(edge,type='user_stated_cause',retention='required',grounding_kind='user_stated_relation')
    relations=tuple(changed if r==edge else r for r in plan.relations)
    assert not gp._source_past_self_unknown_from_resolver(plan.nuclei,relations,resolver)


from test_emlis_q3_application import qdb,qcase
from test_emlis_q2_application import run


@pytest.mark.parametrize('tier',['free','plus','premium'])
@pytest.mark.parametrize('prefix',['',BASE],ids=['single','pair'])
def test_service_saves_past_recognition_and_reopens_without_generation(qcase,qdb,tier,prefix):
    from emlis_thread_service import EmlisThreadService,Q3_PROFILE
    user,parent,service=qcase
    qdb.query('update public.profiles set subscription_tier=$2 where id=$1',[user,tier])
    qdb.query('update public.emotions set memo=$2 where id=$1',[parent,prefix+'何が嫌なのか、自分でもよくわからなかった。'])
    saved=run(service.start(user,parent))
    assert saved['body_state']=='FINAL' and saved['pending_question'] is None
    assert '何が嫌なのか、ご自身でもよくわからなかったのですね。' in saved['current_observation']['text']
    assert not any(e['kind'] in {'QUESTION','ANSWER'} for e in saved['timeline'])
    class NoGeneration:
        def __getattr__(self,name):raise AssertionError('saved body tried generation: '+name)
    reader=EmlisThreadService(runtime_profile=Q3_PROFILE,engine=NoGeneration())
    assert run(reader.get(user,parent))==saved
    assert run(reader.start(user,parent))==saved
