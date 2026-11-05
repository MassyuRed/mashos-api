"""Model units keep the existing source-proved responsibility/decision graph."""
import asyncio
from contextlib import ExitStack
from dataclasses import replace
import json
from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest
import analysis_cumulative_service as service
from cocolon_meaning_experience_engine.cores.analysis import intent_compiler as compiler
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as admission
from test_analysis_cumulative import source_snapshot, OWNER
from test_analysis_model_quoted_parent_units import call


def sample(role_negative=False, decision_negative=False, marker='その後、', prepared=False):
    snap=source_snapshot(1)
    role='私は会合の進行を担当'+('しなかった' if role_negative else 'した')
    ending=('決めておかなかった' if decision_negative else '決めておいた') if prepared else ('決めなかった' if decision_negative else '決めた')
    snap['members'][0]['original']['memo']=role+'。'+marker+'私は分担を'+ending+'。'
    return snap


def response_for(prepared, *, style='whole', qualifiers=False, reorder=False, change=None):
    material=json.loads(prepared.messages()[1]['content'])['fields']
    packet=dict(fields=[])
    for f in material:
        units=[]
        for label in f['text'].rstrip('。.').split('。'):
            p=compiler._proposition(label)
            role='担当' in label
            subject=next(((a,b) for k,a,b in p.source_parts if k=='SELF_TOPIC'),None) if p else None
            finite=next(((a,b) for k,a,b in p.source_parts if k==('FINITE_RESPONSIBILITY' if role else 'FINITE_PREDICATE')),None) if p else None
            quote=label
            if style=='without_marker' and subject:quote=label[subject[0]:]
            if style=='without_subject' and subject:quote=label[subject[1]:]
            if style=='predicate' and finite:quote=label[finite[0]:finite[1]]
            unit=dict(quote=quote,node_kind='ROLE' if role else 'ACTION_OR_NONACTION',parent_quote=None,scope_role=None,qualifiers=[])
            if qualifiers and subject and label[subject[0]:subject[1]] in quote:
                unit['qualifiers'].append(dict(kind='EXPLICIT_ACTOR',quote=label[subject[0]:subject[1]].rstrip('は')))
            if qualifiers and p and p.polarity=='negative':
                unit['qualifiers'].append(dict(kind='NEGATION',quote='しなかった' if role else 'なかった'))
            units.append(unit)
            if p and style=='predicate':
                units.append(dict(quote=p.arguments[0][1],node_kind=None,parent_quote=quote,scope_role='CONTENT_TARGET',qualifiers=[]))
        if reorder:units.reverse()
        packet['fields'].append(dict(field=f['field'],units=units))
    if change:change(packet)
    return call(prepared,packet).response


def proposal(snap,**kw):
    p=service.prepare_cumulative_category_units(OWNER,snap,prompt_version='selected_material.v4')
    return replace(p,response=response_for(p,**kw))


@pytest.mark.parametrize('role_negative',[False,True])
@pytest.mark.parametrize('decision_negative',[False,True])
@pytest.mark.parametrize('marker',['','その後、','それから、'])
@pytest.mark.parametrize('prepared',[False,True])
def test_existing_full_source_graph_is_preserved_exactly(role_negative,decision_negative,marker,prepared):
    snap=sample(role_negative,decision_negative,marker,prepared);value=proposal(snap,qualifiers=True)
    frozen,_,_=admission._admit_quoted_parent_units(value.request,value)
    expected=compiler.compile_observed_graph(frozen)
    a,c=service.build_cumulative_map(OWNER,snap,model_input=value)
    assert a and a.graph==expected
    role,decision=a.graph.nodes
    assert role.proposition.role_state=='PAST_RESPONSIBILITY'
    assert role.polarity==('negative' if role_negative else 'positive')
    assert decision.polarity==('negative' if decision_negative else 'positive')
    assert decision.proposition.predicate_lemma==('決めておく' if prepared else '決める')
    assert c['source_count']==c['processed_count']==c['mapped_count']==1 and c['unparsed_count']==0
    assert len(a.graph.edges)==int(bool(marker))
    if marker:assert a.graph.edges[0].edge_kind=='OBSERVED_ORDER'
    else:assert any(g.missing_scope=='ROUTE_CONNECTION' for g in a.graph.unknown_gaps)
    body=a.safe_text_projection(authenticated_owner_scope=OWNER)['text']
    assert '記録された担当' in body and '分担' in body
    assert ('原因を示す線ではありません' in body)==bool(marker)
    finite,_=service.build_cumulative_map(OWNER,snap)
    assert finite.safe_text_projection(authenticated_owner_scope=OWNER)['text']==body


@pytest.mark.parametrize('style',['whole','without_marker','without_subject','predicate'])
@pytest.mark.parametrize('negative',[False,True])
def test_unchanged_model_units_can_quote_the_finite_host_or_a_bound_predicate_and_object(style,negative):
    snap=sample(negative,negative);value=proposal(snap,style=style,qualifiers=True,reorder=True)
    a,c=service.build_cumulative_map(OWNER,snap,model_input=value)
    assert a and len(a.graph.nodes)==2 and len(a.graph.edges)==1 and c['unparsed_count']==0


@pytest.mark.parametrize('defect',['role_kind','decision_kind','missing_role','missing_decision',
    'false_actor','false_negation','modifier','extra_root','cross_parent','predicate_without_object'])
def test_incorrect_model_reading_is_not_replaced_with_the_finite_graph(defect):
    snap=sample()
    def edit(packet):
        units=packet['fields'][0]['units']
        if defect=='role_kind':units[0]['node_kind']='ACTION_OR_NONACTION'
        if defect=='decision_kind':units[1]['node_kind']='ATTENTION_OR_THOUGHT'
        if defect=='missing_role':units.pop(0)
        if defect=='missing_decision':units.pop()
        if defect=='false_actor':units[1]['qualifiers']=[dict(kind='EXPLICIT_ACTOR',quote='分担')]
        if defect=='false_negation':units[1]['qualifiers']=[dict(kind='NEGATION',quote='決めた')]
        if defect=='modifier':units[1]['qualifiers']=[dict(kind='WRITTEN_MODIFIER',quote='分担')]
        if defect=='extra_root':units.append(dict(quote='分担',node_kind='SCENE',parent_quote=None,scope_role=None,qualifiers=[]))
        if defect=='cross_parent':units[1].update(node_kind=None,parent_quote=units[0]['quote'],scope_role='CONTENT_TARGET')
        if defect=='predicate_without_object':units[1]['quote']='決めた'
    a,c=service.build_cumulative_map(OWNER,snap,model_input=proposal(snap,change=edit))
    assert a is None and c['mapped_count']==0 and c['unparsed_count']==1


@pytest.mark.parametrize('memo',[
    '姉は会合の進行を担当した。その後、私は分担を決めた。',
    '私は会合の進行を担当した。その後、姉は分担を決めた。',
    '会合の進行を担当した。その後、分担を決めた。',
    '私は会合の進行を担当した。その後、私は分担を決めたい。',
    '私は会合の進行を担当した。その後、私は分担を決めたかもしれない。',
    '私は会合の進行を担当した。その後、私は分担を決めたという話だった。',
    '私は会合の進行を担当した。まだ言えない。その後、私は分担を決めた。',
    'まだ言えない。私は会合の進行を担当した。その後、私は分担を決めた。',
    '私は会合の進行を担当した。その後、私は分担を決めた。まだ言えない。',
    '友人は「私は会合の進行を担当した。その後、私は分担を決めた」と言った。',
])
def test_unproved_actor_report_and_unread_text_never_get_a_complete_role_decision_map(memo):
    snap=sample();snap['members'][0]['original']['memo']=memo
    a,c=service.build_cumulative_map(OWNER,snap,model_input=proposal(snap))
    assert a is None and c['unparsed_count']==1


def test_an_order_marker_in_another_field_cannot_supply_a_same_field_route():
    snap=sample();text=snap['members'][0]['original']['memo'];left,right=text.rstrip('。').split('。')
    snap['members'][0]['original'].update(memo=left+'。',memo_action=right+'。')
    a,c=service.build_cumulative_map(OWNER,snap,model_input=proposal(snap))
    assert a is None and c['unparsed_count']==1


def test_normal_saved_wire_read_does_not_rebuild_the_graph_or_derive_a_model_reply():
    snap=sample();a,c=service.build_cumulative_map(OWNER,snap,model_input=proposal(snap))
    row=dict(id=str(UUID(a.artifact_id[9:])),source_profile='cumulative.v1',report_mode='standard',
        content_text=a.safe_text_projection(authenticated_owner_scope=OWNER)['text'],
        content_json=dict(report_mode='standard',watashiMap=a.safe_projection(authenticated_owner_scope=OWNER),map_context=c))
    expected=dict(items=[row],subscription_tier='free',matched=True,history_limit=2)
    with ExitStack() as stack:
        for obj,name in [(compiler,'compile_observed_graph'),(compiler,'compile_model_observed_role_decision'),
            (admission,'generate_analysis_model_observed_actions'),(service,'build_cumulative_map')]:
            stack.enter_context(patch.object(obj,name,side_effect=AssertionError('saved generation')))
        stack.enter_context(patch.object(service,'_rpc',AsyncMock(return_value=expected)))
        assert asyncio.run(service.read_maps(OWNER,report_id=row['id']))==expected
