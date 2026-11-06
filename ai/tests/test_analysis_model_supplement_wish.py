"""Saved-answer wishes keep their own complete evidence and one parent occasion."""
import asyncio
import copy
from dataclasses import replace
import hashlib
import json
from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest
import analysis_cumulative_service as service
from astor_material_snapshots import AnalysisSavedSourceError
from cocolon_meaning_experience_engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.cores.analysis import intent_compiler as compiler
from cocolon_meaning_experience_engine.cores.analysis import observed_route_realizer as author
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as admission
from cocolon_meaning_experience_engine.cores.analysis.source_adapter import (
    AnalysisSourceError, freeze_analysis_sources, source_field_text)
from test_analysis_cumulative import OWNER, source_snapshot
from test_analysis_model_observed_actions import prepared
from test_analysis_model_quoted_parent_units import call
from test_analysis_saved_period import with_answer


ERRORS=(admission.AnalysisSemanticError,AnalysisSourceError,AnalysisSavedSourceError)
FORMS=[('たい','current_input','positive'),('たかった','past','positive'),
    ('たくない','current_input','negative'),('たくなかった','past','negative')]
PARENTS={'action':'私は資料を見た。','wish':'私は日記を書きたい。',
    'unknown':'まだ言葉にできません。'}


def supplement_fixture(answer='私は仕事を続けたい。', *, parent='action',
        prompt='selected_material.v10', categories=('仕事',), snapshot=None, change=None):
    snap=source_snapshot(1) if snapshot is None else copy.deepcopy(snapshot)
    if snapshot is None:
        snap['members'][0]['original'].update(memo=PARENTS.get(parent,parent),memo_action='',
            category=list(categories),emotion_details=[dict(type='平穏',strength='medium')])
        snap['members'][0]=with_answer(snap['members'][0],answer)
    p=prepared(snap,prompt)
    fields=json.loads(p.messages()[1]['content'])['fields']
    data=dict(fields=[])
    for f in fields:
        units=[]
        for q in f['text'].rstrip('。').split('。'):
            is_wish=any(x in q for x in ('たい','たかった','たくない','たくなかった'))
            qualifiers=[]
            if q.startswith(('私は','僕は')):
                qualifiers.append(dict(kind='EXPLICIT_ACTOR',quote=q[0]))
            if q.endswith(('続けたくない','続けたくなかった')):
                qualifiers.append(dict(kind='NEGATION',quote=q[q.index('続け'):]))
            units.append(dict(quote=q,node_kind='ATTENTION_OR_THOUGHT' if is_wish
                else 'ACTION_OR_NONACTION',parent_quote=None,scope_role=None,qualifiers=qualifiers))
        data['fields'].append(dict(field=f['field'],units=units))
    if change:change(data)
    return snap,p,call(p,data)


def admitted(p,value):
    frozen,fields,_=admission._admit_quoted_parent_units(p.request,value)
    answers=tuple(s for s in frozen.sources if s.envelope.source_role=='SUPPLEMENTAL_ANSWER')
    return frozen,fields,answers


def assert_source_evidence(artifact,frozen):
    for n in artifact.graph.nodes:
        for e in n.evidence_refs:
            source=next(s for s in frozen.sources if s.envelope.envelope_id==e.source_envelope_id)
            text=source_field_text(source,e.field_path)
            label=text[e.scalar_start:e.scalar_end]
            assert e.field_sha256==hashlib.sha256(text.encode()).hexdigest()
            assert e.literal_sha256==hashlib.sha256(label.encode()).hexdigest()
            assert source.envelope.raw_utf8[e.utf8_start:e.utf8_end].decode()==label
            assert source.record_ref in n.record_refs


@pytest.mark.parametrize('ending,time,polarity',FORMS)
@pytest.mark.parametrize('parent',['action','wish','unknown'])
@pytest.mark.parametrize('prompt',['selected_material.v4','selected_material.v10'])
def test_ordinary_answer_plain_wish_is_separate_from_parent_meaning(ending,time,polarity,parent,prompt):
    text='私は仕事を続け'+ending+'。'
    snap,p,value=supplement_fixture(text,parent=parent,prompt=prompt)
    before=copy.deepcopy(snap);raw=value.response.raw
    frozen,fields,(answer,)=admitted(p,value)
    a,c=service.build_cumulative_map(OWNER,snap,model_input=value)
    assert a is not None and c['mapped_count']==c['source_count']==c['processed_count']==1
    assert c['unparsed_count']==int(parent=='unknown')
    assert len(a.graph.nodes)==(1 if parent=='unknown' else 2) and not a.graph.edges
    wish,=tuple(n for n in a.graph.nodes if any(
        e.source_envelope_id==answer.envelope.envelope_id for e in n.evidence_refs))
    assert (wish.node_kind,wish.proposition.actor,wish.modality,wish.temporal_scope,wish.polarity)==(
        'ATTENTION_OR_THOUGHT','SELF','wish',time,polarity)
    assert wish.proposition.predicate_lemma=='続ける' and wish.visible_label==text.rstrip('。')
    assert len(wish.evidence_refs)==1 and wish.evidence_refs[0].field_path=='memo'
    assert wish.record_refs==(snap['members'][0]['original']['id'],)
    assert wish.selected_categories==('仕事',) and not wish.update_refs
    assert a.source_members==frozen.members and a.source_set_ref==frozen.source_set_ref
    assert len(a.source_members[0].child_source_envelope_refs)==2
    assert any(g.missing_scope=='SOURCE_SCOPE' for g in a.graph.unknown_gaps)==(parent=='unknown')
    assert all(n['evidence_badge_count']==1 for n in a.safe_projection(authenticated_owner_scope=OWNER)['nodes'])
    assert_source_evidence(a,frozen)
    assert snap==before and value.response.raw==raw


@pytest.mark.parametrize('object_and_stem,lemma',[
    ('記録を書き','書く'),('資料を調べ','調べる'),('方法を試し','試す'),
    ('資料を見','見る'),('模型を作り','作る'),('記録を残し','残す'),
    ('費用を記録し','記録する'),('予定をメモし','メモする'),('仕事を続け','続ける')])
def test_answer_wish_uses_only_the_existing_plain_wish_lexemes(object_and_stem,lemma):
    snap,p,value=supplement_fixture('私は'+object_and_stem+'たい。')
    a,c=service.build_cumulative_map(OWNER,snap,model_input=value)
    wish,=tuple(n for n in a.graph.nodes if n.modality=='wish')
    assert wish.proposition.predicate_lemma==lemma and c['unparsed_count']==0


@pytest.mark.parametrize('ending,time,polarity',FORMS)
def test_canonical_duplicate_rederives_each_answer_proposition_and_counts_one_record(ending,time,polarity):
    text='僕は仕事を続け'+ending+'。'
    snap,p,value=supplement_fixture(text,parent='私は仕事を続け'+ending+'。')
    frozen,fields,(answer,)=admitted(p,value)
    full=compiler.compile_observed_graph(frozen)
    assert len(full.nodes)==1 and len(full.nodes[0].evidence_refs)==2
    assert full.nodes[0].visible_label.startswith('私は')
    own=compiler.compile_model_supplement_plain_wish(frozen,fields,answer)
    assert own is not None and len(own.nodes)==1 and not own.edges
    node,=own.nodes
    assert node.visible_label==text.rstrip('。')
    assert node.proposition==compiler._proposition(text.rstrip('。'))
    assert len(node.evidence_refs)==1 and node.evidence_refs[0].source_envelope_id==answer.envelope.envelope_id
    a,c=service.build_cumulative_map(OWNER,snap,model_input=value)
    assert len(a.graph.nodes)==1 and len(a.graph.nodes[0].evidence_refs)==2
    assert len(a.graph.nodes[0].record_refs)==1 and not a.graph.edges
    assert c['mapped_count']==1 and c['unparsed_count']==0
    assert a.safe_projection(authenticated_owner_scope=OWNER)['nodes'][0]['evidence_badge_count']==1
    assert_source_evidence(a,frozen)


@pytest.mark.parametrize('categories,nodes,records',[
    (('仕事',),2,2),(('生活',),4,1),(('生活','仕事'),4,1)])
def test_answer_wishes_merge_only_matching_category_sets_and_preserve_record_counts(categories,nodes,records):
    snap,_,_=supplement_fixture()
    second=copy.deepcopy(snap['members'][0])
    second['original'].update(id=str(UUID(int=102)),category=list(categories))
    second=with_answer(second,'私は仕事を続けたい。')
    second['thread']['id']=str(UUID(int=401))
    for index,event in enumerate(second['events'],402):
        event.update(id=str(UUID(int=index)),thread_id=second['thread']['id'])
        if event['kind']=='QUESTION':event['payload']['thread_id']=second['thread']['id']
        if event['kind']=='ANSWER':event['payload']['source'].update(
            answer_id=event['id'],thread_id=second['thread']['id'])
    snap['members'].append(second)
    snap,p,value=supplement_fixture(snapshot=snap)
    a,c=service.build_cumulative_map(OWNER,snap,model_input=value)
    assert a is not None and len(a.graph.nodes)==nodes and not a.graph.edges
    assert c['source_count']==c['processed_count']==c['mapped_count']==2 and c['unparsed_count']==0
    work_wish,=tuple(n for n in a.graph.nodes if n.modality=='wish' and n.selected_categories==('仕事',))
    assert len(work_wish.record_refs)==len(work_wish.evidence_refs)==records
    assert a.source_members==freeze_analysis_sources(p.request).members
    assert [n['evidence_badge_count'] for n in a.safe_projection(authenticated_owner_scope=OWNER)['nodes']]==[
        len(n.record_refs) for n in a.graph.nodes]


def with_second_answer(member,text):
    member=copy.deepcopy(member)
    question=copy.deepcopy(next(e for e in member['events'] if e['kind']=='QUESTION'))
    answer=copy.deepcopy(next(e for e in member['events'] if e['kind']=='ANSWER'))
    qid='synthetic-second-question'
    question.update(id=str(UUID(int=302)),question_id=qid,round_index=2)
    question['payload'].update(question_id=qid,parent_request_id='synthetic-second-request')
    question['payload']['decision']['target_ref']='synthetic-second-target'
    answer.update(id=str(UUID(int=303)),question_id=qid,round_index=2)
    answer['payload']['source'].update(answer_id=answer['id'],question_id=qid,round_index=2,answer_text_private=text)
    member['events'].extend([question,answer])
    member['thread'].update(issued_count=2,revision=5,started_question_limit=3)
    member['thread']['data']['runtime_profile']='q3.plan.sequential.v1'
    return member


@pytest.mark.parametrize('second,expected_nodes,wish_evidence',[
    ('私は仕事を続けたい。',2,[2]),('私は計画を続けたかった。',3,[1,1])])
def test_multiple_saved_answers_remain_one_occasion_without_answer_order_edges(second,expected_nodes,wish_evidence):
    snap,_,_=supplement_fixture()
    snap['members'][0]=with_second_answer(snap['members'][0],second)
    snap['tier']='premium'
    snap,p,value=supplement_fixture(snapshot=snap)
    a,c=service.build_cumulative_map(OWNER,snap,model_input=value)
    assert a is not None and len(a.graph.nodes)==expected_nodes and not a.graph.edges
    assert c['mapped_count']==c['processed_count']==c['source_count']==1 and c['unparsed_count']==0
    assert sorted(len(n.evidence_refs) for n in a.graph.nodes if n.modality=='wish')==wish_evidence
    assert all(len(n.record_refs)==1 for n in a.graph.nodes)
    assert len(a.source_members[0].child_source_envelope_refs)==3
    assert_source_evidence(a,freeze_analysis_sources(p.request))


@pytest.mark.parametrize('mutation',['kind','short_negative','false_actor','false_negative','time_modifier',
    'partial_predicate','extra_root','extra_child','missing','borrowed_field'])
def test_answer_wish_model_packet_cannot_erase_or_borrow_source_proof(mutation):
    def change(data):
        answer=data['fields'][-1];unit=answer['units'][0]
        if mutation=='kind':unit['node_kind']='ACTION_OR_NONACTION'
        if mutation=='short_negative':unit['qualifiers'][-1]['quote']='たくなかった'
        if mutation=='false_actor':unit['qualifiers'][0]['quote']='仕事'
        if mutation=='false_negative':unit['qualifiers'][-1]['quote']='仕事'
        if mutation=='time_modifier':unit['qualifiers'].append(dict(kind='WRITTEN_MODIFIER',quote='たくなかった'))
        if mutation=='partial_predicate':unit['quote']='私は仕事を続け'
        if mutation=='extra_root':answer['units'].append(dict(unit,quote='仕事',node_kind='ROLE',qualifiers=[]))
        if mutation=='extra_child':answer['units'].append(dict(quote='私は',node_kind=None,
            parent_quote=unit['quote'],scope_role='CONTENT_TARGET',qualifiers=[]))
        if mutation=='missing':answer['units']=[]
        if mutation=='borrowed_field':unit['quote']='私は資料を見た'
    try:
        snap,p,value=supplement_fixture('私は仕事を続けたくなかった。',change=change)
        a,c=service.build_cumulative_map(OWNER,snap,model_input=value)
    except ERRORS:
        return
    assert a is None and c['mapped_count']==0 and c['unparsed_count']==1


@pytest.mark.parametrize('mutation',['record','record_version','field_path','text','envelope',
    'field_hash','scalar_start','scalar_end','utf8_start','utf8_end','literal_hash'])
def test_answer_helper_does_not_accept_a_reassigned_or_partial_bound_field(mutation):
    snap,p,value=supplement_fixture()
    frozen,fields,(answer,)=admitted(p,value)
    own=next(f for f in fields if f.evidence.source_envelope_id==answer.envelope.envelope_id)
    changed=own
    if mutation=='record':changed=replace(own,record_ref=str(UUID(int=999)))
    if mutation=='record_version':changed=replace(own,record_version='wrong')
    if mutation=='field_path':changed=replace(own,field_path='memo_action')
    if mutation=='text':changed=replace(own,complete_source_text=own.complete_source_text+'まだ分からない。')
    if mutation=='envelope':changed=replace(own,evidence=replace(own.evidence,source_envelope_id=fields[0].evidence.source_envelope_id))
    if mutation=='field_hash':changed=replace(own,evidence=replace(own.evidence,field_sha256='0'*64))
    if mutation=='scalar_start':changed=replace(own,evidence=replace(own.evidence,scalar_start=1))
    if mutation=='scalar_end':changed=replace(own,evidence=replace(own.evidence,scalar_end=own.evidence.scalar_end-1))
    if mutation=='utf8_start':changed=replace(own,evidence=replace(own.evidence,utf8_start=own.evidence.utf8_start+1))
    if mutation=='utf8_end':changed=replace(own,evidence=replace(own.evidence,utf8_end=own.evidence.utf8_end-1))
    if mutation=='literal_hash':changed=replace(own,evidence=replace(own.evidence,literal_sha256='0'*64))
    altered=tuple(changed if f is own else f for f in fields)
    assert compiler.compile_model_supplement_plain_wish(frozen,altered,answer) is None


@pytest.mark.parametrize('text',[
    '姉は仕事を続けたい。','仕事を続けたい。','私は仕事を続けたいと思っている。',
    '私は仕事を続けたくないと思った。','私は仕事を続けたいかもしれない。',
    'その後、私は仕事を続けたい。','昨日、私は仕事を続けたかった。',
    '私は資料を見た。私は仕事を続けたい。','私は仕事を続けたい。私は記録を残したい。',
    '私は仕事を続けたい。まだ分からない。','私は旅行に行きたい。',
    '「私は資料を見た」ではなく「私は資料を見なかった」です。私は仕事を続けたい。'])
def test_other_unread_embedded_ordered_or_multiclause_answers_stay_bounded(text):
    try:
        snap,p,value=supplement_fixture(text)
        a,c=service.build_cumulative_map(OWNER,snap,model_input=value)
    except ERRORS:
        return
    assert a is None and c['mapped_count']==0 and c['unparsed_count']==1


@pytest.mark.parametrize('defect',['owner','parent','round','parent_version','answer_version','raw','messages'])
def test_saved_answer_wish_cannot_be_reassigned_after_binding(defect):
    snap,p,value=supplement_fixture()
    member=snap['members'][0]
    answer=next(e for e in member['events'] if e['kind']=='ANSWER')
    if defect=='owner':member['thread']['user_id']=str(UUID(int=2))
    if defect=='parent':answer['payload']['source']['original_source_ref']='foreign'
    if defect=='round':answer['payload']['source']['round_index']=2
    if defect=='parent_version':member['original']['memo']='私は資料を調べた。'
    if defect=='answer_version':answer['payload']['source']['source_version']='wrong'
    if defect=='raw':value=replace(value,response=replace(value.response,raw=value.response.raw+' '))
    if defect=='messages':value=replace(value,response=replace(value.response,messages_sha256='0'*64))
    with pytest.raises(ERRORS):
        service.build_cumulative_map(OWNER,snap,model_input=value)


@pytest.mark.parametrize('parent,guard',[
    ('私は資料を見た。私は資料を見なかった。','conflicts'),
    ('私は仕事を続けたいけれど、私は辛い。','annotations')])
def test_answer_helper_cannot_detach_its_plain_wish_from_parent_conflicts_or_annotations(parent,guard):
    snap,p,value=supplement_fixture('私は計画を続けたい。',parent=parent,
        change=lambda data:data['fields'][0]['units'][0].update(qualifiers=[]))
    frozen,fields,(answer,)=admitted(p,value)
    full=compiler.compile_observed_graph(frozen)
    assert getattr(full,guard)
    assert compiler.compile_model_supplement_plain_wish(frozen,fields,answer) is None
    a,c=service.build_cumulative_map(OWNER,snap,model_input=value)
    assert a is None and c['mapped_count']==0 and c['unparsed_count']==1


def test_answer_helper_keeps_a_prior_answer_source_update_in_the_full_parent_check():
    snap=source_snapshot(1)
    snap['members'][0]['original'].update(memo=PARENTS['action'],memo_action='',
        emotion_details=[dict(type='平穏',strength='medium')])
    snap['members'][0]=with_answer(snap['members'][0],
        '「私は資料を見た」ではなく「私は資料を見なかった」です。')
    snap['members'][0]=with_second_answer(snap['members'][0],'私は仕事を続けたい。')
    snap['tier']='premium'
    request=replace(service._cumulative_model_request(OWNER,snap),selected_category_context=True)
    frozen=freeze_analysis_sources(request)
    answers=tuple(s for s in frozen.sources if s.envelope.source_role=='SUPPLEMENTAL_ANSWER')
    full=compiler.compile_observed_graph(frozen)
    assert len(full.source_updates)==1
    assert compiler.compile_model_supplement_plain_wish(frozen,(),answers[-1]) is None
    with pytest.raises(admission.AnalysisSemanticError):
        prepared(snap)


def test_answer_helper_rejects_original_or_role_changed_source_objects():
    snap,p,value=supplement_fixture()
    frozen,fields,(answer,)=admitted(p,value)
    original=next(s for s in frozen.sources if s.envelope.source_role=='ORIGINAL_INPUT')
    assert compiler.compile_model_supplement_plain_wish(frozen,fields,original) is None
    changed=replace(answer,envelope=replace(answer.envelope,source_role='ORIGINAL_INPUT'))
    assert compiler.compile_model_supplement_plain_wish(frozen,fields,changed) is None
    assert frozen.sources[-1].envelope.source_role=='SUPPLEMENTAL_ANSWER'


def test_rejected_answer_model_unit_does_not_fall_back_to_a_source_generated_map():
    snap,p,value=supplement_fixture(change=lambda d:d['fields'][-1]['units'][0].update(node_kind='ROLE'))
    ordinary,_=service.build_cumulative_map(OWNER,snap)
    assert ordinary is not None and any(n.modality=='wish' for n in ordinary.graph.nodes)
    a,c=service.build_cumulative_map(OWNER,snap,model_input=value)
    assert a is None and c['mapped_count']==0 and c['unparsed_count']==1


def test_saved_answer_wish_projection_is_read_without_a_generation_or_proof_call():
    snap,p,value=supplement_fixture('私は仕事を続けたくなかった。',parent='unknown')
    a,c=service.build_cumulative_map(OWNER,snap,model_input=value)
    row=dict(id=str(UUID(a.artifact_id[9:])),source_profile=service.PROFILE,report_mode='standard',
        content_text=a.safe_text_projection(authenticated_owner_scope=OWNER)['text'],
        content_json=dict(report_mode='standard',watashiMap=a.safe_projection(authenticated_owner_scope=OWNER),map_context=c))
    expected=dict(items=[row],subscription_tier='free',matched=True,history_limit=2)
    forbidden=AssertionError('saved answer wish must not regenerate')
    with patch.object(service,'_rpc',AsyncMock(return_value=json.loads(admission.canonical(expected)))),\
         patch.object(MeaningExperienceEngine,'generate',side_effect=forbidden),\
         patch.object(compiler,'compile_observed_graph',side_effect=forbidden),\
         patch.object(compiler,'compile_model_supplement_plain_wish',side_effect=forbidden),\
         patch.object(author,'realize_observed_graph',side_effect=forbidden):
        assert asyncio.run(service.read_maps(OWNER,report_id=row['id']))==expected
