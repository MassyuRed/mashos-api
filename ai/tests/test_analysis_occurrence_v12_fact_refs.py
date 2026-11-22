"""Request-bound, lossless compact NODES values on the normal staged provider."""
import asyncio
import json
from copy import deepcopy

import httpx
import pytest

import analysis_model_source as source
import analysis_semantic_map as app
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from test_analysis_cumulative import OWNER
from test_analysis_node_local_native_profile import accepts
from test_analysis_occurrence_v11_display import map_stages
from test_emlis_natural_reply_probe_http import probe


def fixture():
    old, plan, body = map_stages('私は展覧会の図面を保存した。', '私は印刷した図面を机に置いた。')
    parent = app.prepare_semantic_map(OWNER, json.loads(old.source_snapshot_json),
        prompt_version=core.SEMANTIC_MAP_OCCURRENCE_V12_PROFILE)
    plan_wire = dict(schema_version=plan['schema_version'],
        source_choices_sha256=json.loads(parent.messages()[1]['content'])['source_choices_sha256'],
        nodes=deepcopy(plan['nodes']))
    table=core._semantic_plan_choices(parent,json.loads(parent.material_json))[1]
    inverse={(f,q):key for (f,key),q in table.items()}
    for node in plan_wire['nodes']:
        for unit in node['units']:
            for root in unit['evidence']:
                root['quote']=inverse[root['field'],root['quote']]
    expected = deepcopy(body)
    compact = deepcopy(body)
    compact['plan_sha256'] = core.semantic_map_hash(['analysis.node-facts.v1', 'NODES', parent.request_ref, plan])
    for (n,u,k),(ref,quote) in core._semantic_node_fact_sources(plan,json.loads(parent.material_json)).items():
        assert body['nodes'][n]['units'][u]['fact_parts'][k] == quote
        compact['nodes'][n]['units'][u]['fact_parts'][k] = ref
    return old,parent,plan,plan_wire,expected,compact


def test_normal_provider_sends_expanded_observations_to_relations_and_retains_original_wire():
    _,p,plan,plan_wire,expected,short = fixture()
    seen = []
    raw=[]
    def handler(req):
        messages=json.loads(req.content)['messages']
        material=json.loads(messages[1]['content'])
        phase=material['author_phase']
        if phase=='PLAN':
            value=plan_wire
        elif phase=='NODES':
            value=short
            assert core.admit_semantic_node_local_v4_nodes_response(p,plan,short)==expected
        else:
            joined=core._semantic_v4_join(plan,expected)
            assert material['candidate_nodes']==joined
            value=dict(schema_version=core._semantic_v4_schema(phase),nodes_sha256=core.semantic_map_hash(joined),
                qualification_review={k:dict(status='STATED') for k in material['qualification_candidates']},edges=[],
                overview=dict(node_refs=['n1'],title='記録に残した図面'))
        assert accepts(value,messages)
        seen.append(phase)
        raw.append(json.dumps(value,ensure_ascii=False,separators=(',',':')))
        return httpx.Response(200,json=dict(model=source.SEMANTIC_OCCURRENCE_V12_MODEL,
            choices=[dict(finish_reason='stop',message=dict(role='assistant',content=raw[-1]))],usage=dict(completion_tokens=100)))
    transport=source.SelfHostedSemanticAnalysisModelSource(endpoint='https://fixture.invalid/v1/chat/completions',
        model=source.SEMANTIC_OCCURRENCE_V12_MODEL,semantic_prompt_version=p.prompt_version,
        api_key='offline-fixture',transport=httpx.MockTransport(handler))
    reply=asyncio.run(transport(p))
    assert seen==['PLAN','NODES','RELATIONS']
    result,_=app.build_semantic_map(p,reply)
    saved=result.private_evidence()['graph']['meaning_review']['node_local_plan']['phase_artifact']
    assert [row['raw'] for row in saved['phases']]==raw
    assert core.assemble_semantic_node_local_v4(p,saved)['nodes'][0]['units'][0]['fact']==plan['nodes'][0]['units'][0]['evidence'][0]['quote']
    assert plan['nodes'][1]['units'][0]['evidence'][0]['quote'] in result.safe_text_projection(authenticated_owner_scope=OWNER)['text']


@pytest.mark.parametrize('fault',['wrong_slot','original_on_fixed_slot','plan_digest','missing_key','another_stage'])
def test_strict_source_receipt_and_compatibility(fault):
    old,p,plan,_,expected,short=fixture()
    msgs=core.semantic_node_local_v4_messages(p,'NODES',plan=plan)
    assert core.semantic_node_local_v4_nodes(old,plan,expected)==expected
    wire=deepcopy(short);parts=wire['nodes']['n1']['units']['u1']['fact_parts'];key=next(iter(parts))
    if fault=='wrong_slot':parts[key]=2
    elif fault=='original_on_fixed_slot':parts[key]=expected['nodes']['n1']['units']['u1']['fact_parts'][key]
    elif fault=='plan_digest':wire['plan_sha256']=core.semantic_map_hash(plan)
    elif fault=='missing_key':del parts[key]
    else:
        leaf=core.prepare_semantic_leaf(p,tuple(m.saved_record_ref for m in p.frozen.members))
        wire['plan_sha256']=core.semantic_map_hash(['analysis.node-facts.v1','NODES',leaf.request_ref,plan])
    assert not accepts(wire,msgs)
    with pytest.raises(core.AnalysisSemanticMapError):
        core.admit_semantic_node_local_v4_nodes_response(p,plan,wire)


def test_duplicate_comparison_decodes_using_each_full_original():
    _,p,plan,_,expected,short=fixture()
    msg=core.semantic_node_local_v4_messages(p,'NODES',plan=plan)
    lookup=probe._semantic_wire_fact_sources(msg)
    for n in plan['nodes']:
        nid=n['node_id']; canonical=expected['nodes'][nid]; wire=short['nodes'][nid]
        signature=lambda body,refs: probe._occurrence_visible_signature(body['units'],body['title'],body['meaning'],refs)
        assert signature(wire,lookup)==signature(canonical,None)
        assert signature(wire,None)!=signature(canonical,None)


def test_same_sentence_in_two_records_gets_independent_slot_identity():
    old,plan,body=map_stages('同じ説明を読んだ。','同じ説明を読んだ。')
    p=app.prepare_semantic_map(OWNER,json.loads(old.source_snapshot_json),
        prompt_version=core.SEMANTIC_MAP_OCCURRENCE_V12_PROFILE)
    slots=core._semantic_node_fact_sources(plan,json.loads(p.material_json))
    assert [value for value in slots.values()]==[(1,'同じ説明を読んだ。'),(2,'同じ説明を読んだ。')]
    assert core.semantic_node_local_v4_nodes(p,plan,body)==body


def test_free_prose_includes_source_like_markers_without_substitution():
    old,plan,body=map_stages('資料を保存した。','資料を保存したかどうか')
    p=app.prepare_semantic_map(OWNER,json.loads(old.source_snapshot_json),
        prompt_version=core.SEMANTIC_MAP_OCCURRENCE_V12_PROFILE)
    # The unfinished second original has no literal display enum. Its authored
    # value may legitimately contain an ID that is a reference in another slot.
    canonical=deepcopy(body)
    second=canonical['nodes']['n2']['units']['u1']['fact_parts']
    second[next(iter(second))]='版の表記は@1です。'
    wire=deepcopy(canonical)
    wire['plan_sha256']=core.semantic_map_hash(['analysis.node-facts.v1','NODES',p.request_ref,plan])
    refs=core._semantic_node_fact_sources(plan,json.loads(p.material_json))
    assert len(refs)==1
    for (n,u,k),(ref,_) in refs.items():
        wire['nodes'][n]['units'][u]['fact_parts'][k]=ref
    assert accepts(wire,core.semantic_node_local_v4_messages(p,'NODES',plan=plan))
    assert core.admit_semantic_node_local_v4_nodes_response(p,plan,wire)==canonical


@pytest.mark.parametrize(('source_text','prose','allowed'),[
    ('送り先は未定','@999',False),
    ('送り先は@999のアカウント','@999',True),
    ('送り先は@9999のアカウント','@999',False),
    ('連絡先はhana@999.example','@999',False),
    ('連絡先はhana@999.example','hana@999.example',True),
    ('送り先は@summer_15','@summer_15',True),
    ('アットマークを書いた','@',True),
    ('送り先は未定',999,False),
])
def test_free_slot_numeric_handle_requires_its_exact_original(source_text,prose,allowed):
    old,plan,body=map_stages(source_text)
    p=app.prepare_semantic_map(OWNER,json.loads(old.source_snapshot_json),
        prompt_version=core.SEMANTIC_MAP_OCCURRENCE_V12_PROFILE)
    assert not core._semantic_node_fact_sources(plan,json.loads(p.material_json))
    wire=deepcopy(body)
    wire['plan_sha256']=core.semantic_map_hash(['analysis.node-facts.v1','NODES',p.request_ref,plan])
    part=wire['nodes']['n1']['units']['u1']['fact_parts']
    part[next(iter(part))]=prose
    msg=core.semantic_node_local_v4_messages(p,'NODES',plan=plan)
    assert accepts(wire,msg)==allowed
    if allowed:
        expanded=core.admit_semantic_node_local_v4_nodes_response(p,plan,wire)
        assert expanded['nodes']['n1']['units']['u1']['fact_parts']==part
    else:
        with pytest.raises(core.AnalysisSemanticMapError):
            core.admit_semantic_node_local_v4_nodes_response(p,plan,wire)


def relation_views():
    old,plan,body=map_stages('私は備品を数えた。','倉庫の前に置かれた棚')
    p=app.prepare_semantic_map(OWNER,json.loads(old.source_snapshot_json),
        prompt_version=core.SEMANTIC_MAP_OCCURRENCE_V12_PROFILE)
    unit=body['nodes']['n2']['units']['u1']
    key=next(iter(unit['fact_parts']))
    unit['fact_parts'][key]='記載された場所は倉庫の前です。'
    full=core.semantic_node_local_v4_messages(p,'RELATIONS',plan=plan,nodes=body)
    original=json.loads(full[1]['content'])
    reduced=core._semantic_compact_relation_message(original,full,1)
    return full,original,reduced,json.loads(reduced[1]['content'])


def test_large_relation_view_preserves_every_source_and_fact_and_fits_small_views_verbatim():
    full,original,reduced,packed=relation_views()
    size=len(core.semantic_map_canonical(full).encode())
    assert core._semantic_compact_relation_message(original,full,size) is full
    assert 'evidence_parts_by_unit' not in packed
    assert packed['fact_part_overrides']=={'n2.u1.e1':'記載された場所は倉庫の前です。'}
    assert probe._semantic_relation_fact_parts(packed)==original['evidence_parts_by_unit']
    for key in original.keys()-{'evidence_parts_by_unit'}:
        assert packed[key]==original[key]
    assert probe.semantic_output_schema(full)==probe.semantic_output_schema(reduced)


@pytest.mark.parametrize('fault',['unbound_key','missing_override','redundant_override','forged_body','missing_hash','missing_both','wrong_digest','two_tables'])
def test_relation_transport_rejects_damaged_or_forged_fact_parts(fault):
    _,original,messages,m=relation_views()
    values=m['fact_part_overrides']
    if fault=='unbound_key': values['n3.u1.e1']='別の根拠'
    elif fault=='missing_override': values.clear()
    elif fault=='redundant_override': values['n1.u1.e1']=original['candidate_nodes'][0]['units'][0]['fact']
    elif fault=='forged_body': values['n2.u1.e1']='別のところにあります。'
    elif fault=='missing_hash': del m['evidence_parts_sha256']
    elif fault=='missing_both': del m['fact_part_overrides'],m['evidence_parts_sha256']
    elif fault=='wrong_digest': m['evidence_parts_sha256']='0'*64
    else: m['evidence_parts_by_unit']=original['evidence_parts_by_unit']
    messages[1]['content']=json.dumps(m,ensure_ascii=False)
    with pytest.raises(ValueError,match='semantic_relation_fact_parts_unbound'):
        probe.semantic_output_schema(messages)


def test_relation_checks_evidence_part_boundaries_even_when_the_joined_fact_is_identical():
    _,_,_,m=relation_views()
    unit=m['candidate_nodes'][0]['units'][0]
    unit['evidence']=[dict(field=1,quote='根拠甲。'),dict(field=1,quote='根拠乙。')]
    unit['fact']='一二三四'
    m['fact_part_overrides'].update({'n1.u1.e1':'一二','n1.u1.e2':'三四'})
    # Bind the actual two authored parts. The digest also covers every other
    # unit's field, quote and complete original fact text.
    covered={}
    for node in m['candidate_nodes']:
        for i,u in enumerate(node['units'],1):
            uid=f"{node['node_id']}.u{i}"
            covered[uid]={f'e{j}':dict(field=r['field'],quote=r['quote'],
                fact_part=m['fact_part_overrides'].get(f'{uid}.e{j}',r['quote']))
                for j,r in enumerate(u['evidence'],1)}
    m['evidence_parts_sha256']=core.semantic_map_hash(covered)
    assert probe._semantic_relation_fact_parts(m)==covered
    m['fact_part_overrides'].update({'n1.u1.e1':'一','n1.u1.e2':'二三四'})
    with pytest.raises(ValueError,match='semantic_relation_fact_parts_unbound'):
        probe._semantic_relation_fact_parts(m)
