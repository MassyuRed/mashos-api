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


def test_v6_adds_only_an_independent_contrast_to_unchanged_v4_material():
    snap = sample()
    v4 = service.prepare_cumulative_category_units(OWNER, snap, prompt_version='selected_material.v4')
    v6 = service.prepare_cumulative_category_units(OWNER, snap, prompt_version='selected_material.v6')
    # Frozen from the unchanged 722835f9 API before adding the new profile.
    assert admission.digest(v4.messages()) == 'fc06c5a05d4994fc4dfb3b464cf78f0e978f2ed47a538a322cd72e29ab26169e'
    assert v6.request == v4.request and v6.source_guard == v4.source_guard
    assert v6.request_ref != v4.request_ref and v6.messages()[1] == v4.messages()[1]
    assert v6.messages()[0]['content'] == v4.messages()[0]['content'] + admission._responsibility_decision_units_instruction()
    contrast = admission._responsibility_decision_units_instruction()
    raw_input, raw_output = contrast.split('例の入力:', 1)[1].split('\n例の出力:', 1)
    material = json.loads(raw_input)
    packet = json.loads(raw_output.split('\n今回の入力', 1)[0])
    assert '会場' not in contrast and '手順' not in contrast and '日程' not in contrast
    assert [len(f['units']) for f in packet['fields']] == [2, 2]
    for field, row in zip(material['fields'], packet['fields']):
        assert set(row) == {'field', 'units'}
        assert [u['node_kind'] for u in row['units']] == ['ROLE', 'ACTION_OR_NONACTION']
        for unit in row['units']:
            assert unit['quote'] in field['text'] and unit['parent_quote'] is None
            assert unit['scope_role'] is None and '私は' in unit['quote']
            assert all(q['quote'] in unit['quote'] for q in unit['qualifiers'])
    assert all(any(q['kind'] == 'NEGATION' for q in u['qualifiers']) for u in packet['fields'][1]['units'])
    example = source_snapshot(2)
    for member, field in zip(example['members'], material['fields']):
        member['original'].update(memo=field['text'], memo_action='')
    prepared = service.prepare_cumulative_category_units(OWNER, example, prompt_version='selected_material.v6')
    artifact, counts = service.build_cumulative_map(OWNER, example, model_input=call(prepared, packet))
    assert artifact and len(artifact.graph.nodes) == 4 and not artifact.graph.edges
    assert counts['source_count'] == counts['mapped_count'] == 2 and counts['unparsed_count'] == 0


@pytest.mark.parametrize('memo,category,negative,ordered', [
    ('私は会場の準備を担当しました。その後、私は手順を決めました。', '仕事', False, True),
    ('僕は連絡を担当しなかった。僕は日程を決めなかった。', '生活', True, False),
])
def test_v6_held_out_sources_already_have_complete_existing_witnesses(memo, category, negative, ordered):
    # Synthetic proposals check the existing scope before any live comparison.
    snap = source_snapshot(1)
    snap['members'][0]['original'].update(memo=memo, memo_action='', category=[category])
    prepared = service.prepare_cumulative_category_units(OWNER, snap, prompt_version='selected_material.v6')
    value = replace(prepared, response=response_for(prepared, qualifiers=True))
    frozen, _, _ = admission._admit_quoted_parent_units(value.request, value)
    expected = compiler.compile_observed_graph(frozen)
    artifact, counts = service.build_cumulative_map(OWNER, snap, model_input=value)
    assert artifact and artifact.graph == expected and len(artifact.graph.nodes) == 2
    assert counts['source_count'] == counts['processed_count'] == counts['mapped_count'] == 1
    assert counts['unparsed_count'] == 0 and len(artifact.graph.edges) == int(ordered)
    assert all(n.proposition.actor == 'SELF' and n.temporal_scope == 'past'
        and n.polarity == ('negative' if negative else 'positive')
        and n.selected_categories == (category,) for n in artifact.graph.nodes)


@pytest.mark.parametrize('source_profile,target_profile', [
    ('selected_material.v4', 'selected_material.v6'),
    ('selected_material.v6', 'selected_material.v4'),
    ('selected_material.v4', 'selected_material.v7'),
    ('selected_material.v7', 'selected_material.v4'),
    ('selected_material.v6', 'selected_material.v7'),
    ('selected_material.v7', 'selected_material.v6'),
])
@pytest.mark.parametrize('change_ref', [False, True])
def test_response_cannot_be_reassigned_across_prompt_versions(source_profile, target_profile, change_ref):
    snap = sample()
    source = service.prepare_cumulative_category_units(OWNER, snap, prompt_version=source_profile)
    target = service.prepare_cumulative_category_units(OWNER, snap, prompt_version=target_profile)
    response = response_for(source)
    if change_ref: response = replace(response, request_ref=target.request_ref)
    with pytest.raises(admission.AnalysisSemanticError):
        service.build_cumulative_map(OWNER, snap, model_input=replace(target, response=response))


@pytest.mark.parametrize('profile,state', [
    ('selected_material.v4', admission.QUOTED_PARENT_MATERIAL_V4_STATE),
    ('selected_material.v6', admission.QUOTED_PARENT_MATERIAL_V6_STATE),
    ('selected_material.v7', admission.QUOTED_PARENT_MATERIAL_V7_STATE),
])
def test_versioned_candidate_state_keeps_exact_schema_and_non_generating_roundtrip(profile, state):
    snap = sample()
    prepared = service.prepare_cumulative_category_units(OWNER, snap, prompt_version=profile)
    value = replace(prepared, response=response_for(prepared, qualifiers=True))
    artifact, counts = service.build_cumulative_quoted_parent_candidates(OWNER, snap, model_input=value)
    raw = service.serialize_cumulative_quoted_parent_candidates(OWNER, snap,
        model_input=value, artifact=artifact, coverage=counts)
    saved = json.loads(raw)
    assert saved['state']['schema_version'] == state and saved['state']['prompt_version'] == profile
    assert saved['state']['response']['messages_sha256'] == admission.digest(prepared.messages())
    with patch.object(service, 'build_cumulative_quoted_parent_candidates', side_effect=AssertionError('saved build')), \
         patch.object(compiler, 'compile_observed_graph', side_effect=AssertionError('saved finite graph')), \
         patch.object(compiler, 'compile_analysis_unit_candidates', side_effect=AssertionError('saved candidate')):
        assert service.reload_cumulative_quoted_parent_candidates(OWNER, snap, raw) == (artifact, counts)
    changed = json.loads(raw)
    changed['state']['prompt_version'] = 'selected_material.v6' if profile.endswith('v4') else 'selected_material.v4'
    with pytest.raises(admission.AnalysisSemanticError):
        service.reload_cumulative_quoted_parent_candidates(OWNER, snap, admission.canonical(changed))


@pytest.mark.parametrize('defect', ['field_omitted', 'metadata', 'foreign_quote', 'role_kind'])
def test_v6_keeps_strict_fields_source_binding_and_model_kind_adoption(defect):
    snap = sample()
    prepared = service.prepare_cumulative_category_units(OWNER, snap, prompt_version='selected_material.v6')
    response = response_for(prepared)
    packet = json.loads(response.raw)
    if defect == 'field_omitted': packet['fields'].clear()
    if defect == 'metadata': packet['fields'][0]['record'] = 1
    if defect == 'foreign_quote': packet['fields'][0]['units'][0]['quote'] = '私は道具の管理を担当した'
    if defect == 'role_kind': packet['fields'][0]['units'][0]['node_kind'] = 'ACTION_OR_NONACTION'
    value = call(prepared, packet)
    if defect == 'role_kind':
        artifact, counts = service.build_cumulative_map(OWNER, snap, model_input=value)
        assert artifact is None and counts['mapped_count'] == 0 and counts['unparsed_count'] == 1
    else:
        with pytest.raises(admission.AnalysisSemanticError):
            service.build_cumulative_map(OWNER, snap, model_input=value)


def test_v6_preserves_supplement_context_and_rejects_cross_envelope_quotes():
    from test_analysis_saved_period import with_answer
    snap = sample()
    snap['members'][0]['original']['emotion_details'] = [dict(type='平穏', strength='medium')]
    snap['members'][0] = with_answer(snap['members'][0], '私は資料を見た。')
    v4 = service.prepare_cumulative_category_units(OWNER, snap, prompt_version='selected_material.v4')
    v6 = service.prepare_cumulative_category_units(OWNER, snap, prompt_version='selected_material.v6')
    assert v4.messages()[1] == v6.messages()[1]
    fields = json.loads(v6.messages()[1]['content'])['fields']
    assert [f['source_role'] for f in fields] == ['ORIGINAL_INPUT', 'SUPPLEMENTAL_ANSWER']
    assert [f['record'] for f in fields] == [1, 1]
    assert all(f['selected_categories'] == ['仕事'] for f in fields)
    response = response_for(v6)
    artifact, counts = service.build_cumulative_map(OWNER, snap, model_input=replace(v6, response=response))
    assert artifact and len(artifact.graph.nodes) == 3 and len(artifact.graph.edges) == 1
    assert counts['source_count'] == counts['mapped_count'] == 1 and counts['unparsed_count'] == 0
    assert len({e.source_envelope_id for n in artifact.graph.nodes for e in n.evidence_refs}) == 2
    packet = json.loads(response.raw)
    packet['fields'][0]['units'][0]['quote'] = packet['fields'][1]['units'][0]['quote']
    with pytest.raises(admission.AnalysisSemanticError):
        service.build_cumulative_map(OWNER, snap, model_input=call(v6, packet))
