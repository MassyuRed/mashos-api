"""Source-qualified author compilation/decoding, not actual model quality."""
from copy import deepcopy
from http.server import ThreadingHTTPServer
import json
import threading

import httpx
import pytest

import analysis_model_source as sources
import analysis_if_model_source as if_sources
import analysis_semantic_map as application
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from cocolon_meaning_experience_engine.cores.analysis import intent_compiler as compiler
from test_analysis_semantic_map import OWNER, sample, response
from test_analysis_event_plan_model_alias import environment
from test_emlis_natural_reply_probe_http import probe

PROFILE = 'semantic_map.event_plan.v2'
SCHEMA = 'cocolon.analysis.semantic_map.event_plan.model.v2'
ALIAS = 'cocolon-qwen3.5-4b-analysis-event-plan-v2'
SENT = '同僚は工房へ図面を送ると言っていたが、実際に送信したか私は聞いていない。'
JUDGED = '担当者の説明を性能の保証としては扱わなかった。'
ACHIEVED = '申込みを終え、選んだ理由を説明できたことに満足した。'
PLANNED = '明日窓口へ行くと決めた。'


def material(profile=PROFILE, first=SENT):
    snapshot = sample()
    snapshot['members'][0]['original'].update(memo=first, memo_action='')
    snapshot['members'][1]['original'].update(memo=JUDGED + ACHIEVED, memo_action=PLANNED)
    return application.prepare_semantic_map(OWNER, snapshot, prompt_version=profile)


def plan():
    def event(i, field, quote, mode, fact, unknowns=None):
        return dict(evidence=[dict(quote=quote,field=field)], event_id='e'+str(i),
            source_mode=mode, fact=fact, unknowns=unknowns or [])
    return dict(schema_version=SCHEMA, events=[
        event(1,1,SENT,'RECORDED','同僚から工房へ図面を送るという話を聞いた。',
            [dict(source_quote=SENT,source_field=1)]),
        event(2,2,JUDGED,'PERSON_JUDGMENT',JUDGED),
        event(3,2,ACHIEVED,'RECORDED',ACHIEVED),
        event(4,3,PLANNED,'DECIDED_PLAN','明日窓口へ行く予定を決めた。')],
        readings=[dict(reading_id='r1',event_refs=['e2','e3'],
            meaning='説明を保証とは区別し、選んだ理由を説明できる形で申込みを終えている。')],
        nodes=[dict(node_id='n1',node_kind='STATE_CONTEXT',perspective='OBSERVED_INTERACTION',
            title='同僚が話した送信と、未確認の実行',unit_refs=['e1']),
            dict(node_id='n2',node_kind='CHOICE_OUTPUT',perspective='SELF',
            title='説明の扱いと、申込みを終えた満足',unit_refs=['r1','e4'])],
        edges=[dict(**{'from':'n1','to':'n2'},relation_kind='CONTEXT_CONTRAST',
            label='聞いた話と、本人が確かめ終えた範囲',unit_refs=['e1','r1'])],
        overview=dict(title='話の確認範囲と、自分の選択',unit_refs=['r1','e1','e4']))


def compile_plan(packet=None, prepared=None):
    return compiler.compile_analysis_semantic_map(material() if prepared is None else prepared,
        plan() if packet is None else packet,response_sha256='a'*64)


def authored_lesson():
    """Exercise the actual author's example through the existing source path."""
    instruction = core._SEMANTIC_MAP_EVENT_PLAN_V2_INSTRUCTION
    decoder = json.JSONDecoder()
    inputs, _ = decoder.raw_decode(instruction.split('例入力=', 1)[1])
    packet, _ = decoder.raw_decode(instruction.split('例出力=', 1)[1])
    snapshot = sample()
    for member, field in zip(snapshot['members'], inputs['fields'], strict=True):
        member['original'].update(memo=field['text'], memo_action='')
    prepared = application.prepare_semantic_map(OWNER, snapshot, prompt_version=PROFILE)
    assert [f['text'] for f in json.loads(prepared.material_json)['fields']] == [
        f['text'] for f in inputs['fields']]
    return prepared, packet


def test_authored_lesson_realizes_later_confirmation_and_separate_remaining_unknown():
    prepared, packet = authored_lesson()
    before = deepcopy(packet)
    artifact, counts = application.build_semantic_map(prepared, response(prepared, packet))
    projection = artifact.safe_projection(authenticated_owner_scope=OWNER)
    text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text']
    assert counts['mapped_count'] == 2 and counts['unparsed_count'] == 0
    assert projection['wire_kind'] == 'watashi.map.v3'
    confirmed, separate = projection['nodes']
    reading = packet['readings'][0]['meaning']
    assert confirmed['summary'] == confirmed['explanation'] == reading
    assert confirmed['unknowns'] == []
    assert separate['unknowns'] == [packet['events'][2]['unknowns'][0]['source_quote']]
    assert separate['explanation'] == packet['events'][2]['fact']
    assert reading in text and separate['explanation'] in text
    graph = compile_plan(packet, prepared)
    roots = json.loads(graph.nodes_json)
    assert len(roots[0]['evidence_refs']) == 2 and len(roots[1]['evidence_refs']) == 1
    assert accepts(packet, prepared)
    assert packet == before


def test_authored_lesson_rejects_unused_reading_even_when_all_events_are_reachable():
    prepared, packet = authored_lesson()
    packet['nodes'][0]['unit_refs'] = ['e1', 'e2']
    packet['overview']['unit_refs'] = ['e1', 'e2', 'e3']
    before = deepcopy(packet)
    with pytest.raises(core.AnalysisSemanticMapError, match='event_plan_orphan'):
        compile_plan(packet, prepared)
    assert packet == before


def test_reading_dependencies_are_derived_once_but_not_added_as_visible_prose():
    p=plan();before=deepcopy(p);graph=compile_plan(p)
    nodes=json.loads(graph.nodes_json);edges=json.loads(graph.edges_json)
    assert nodes[0]['unknowns']==[SENT]
    assert nodes[1]['summary']==p['readings'][0]['meaning']
    assert nodes[1]['explanation']=='\n'.join([p['readings'][0]['meaning'],p['events'][3]['fact']])
    assert JUDGED not in nodes[1]['explanation'] and ACHIEVED not in nodes[1]['explanation']
    assert {r['field_path'] for r in nodes[1]['evidence_refs']}=={'memo','memo_action'}
    assert len(nodes[1]['evidence_refs'])==3
    assert edges[0]['explanation']=='\n'.join([p['events'][0]['fact'],p['readings'][0]['meaning']])
    assert json.loads(graph.overview_json)['summary']=='\n'.join([
        p['readings'][0]['meaning'],p['events'][0]['fact'],p['events'][3]['fact']])
    private=json.loads(graph.meaning_review_json)['event_plan']
    assert private['profile']==PROFILE and private['plan']==before
    assert private['meaning_status']=='UNASSESSED' and p==before


@pytest.mark.parametrize('mutate',[
    lambda p:p['nodes'][0].update(unit_refs=['r9']),
    lambda p:p['nodes'][0].update(unit_refs=['e1','e1']),
    lambda p:p['events'][0].update(unknowns=['同僚へ届いたか']),
    lambda p:p['events'][0].update(unknowns=[dict(source_quote=JUDGED,source_field=2)]),
    lambda p:p['events'][0].update(unknowns=[dict(source_quote=SENT.replace('同僚は','同僚へ'),source_field=1)]),
    lambda p:p['events'][0].update(source_mode='ACCEPTED_TRUE'),
    lambda p:p['events'][0].update(source_mode=True),
    lambda p:p['events'][0].update(unknowns=[dict(source_quote=SENT,source_field=True)]),
    lambda p:p['events'][0].update(unknowns=[dict(source_quote=SENT,source_field=1)]*2),
])
def test_invalid_qualification_or_selection_is_rejected_without_raw_repair(mutate):
    p=plan();mutate(p);original=deepcopy(p)
    with pytest.raises(core.AnalysisSemanticMapError):compile_plan(p)
    assert p==original


def test_unknown_must_be_in_its_event_root_even_if_present_elsewhere_in_same_field():
    p=plan();p['events'][1]['unknowns']=[dict(source_quote=ACHIEVED,source_field=2)]
    with pytest.raises(core.AnalysisSemanticMapError,match='unknown_unbound'):compile_plan(p)


def test_source_mode_and_verbatim_quote_are_not_a_semantic_acceptance_certificate():
    p=plan();p['events'][1]['unknowns']=[dict(source_quote=JUDGED,source_field=2)]
    graph=compile_plan(p)
    assert JUDGED in json.loads(graph.nodes_json)[1]['unknowns']
    assert json.loads(graph.meaning_review_json)['event_plan']['meaning_status']=='UNASSESSED'


def test_edge_cannot_select_a_unit_outside_both_endpoint_closures():
    p=plan();p['nodes'][1]['unit_refs']=['r1']
    p['nodes'].append(dict(node_id='n3',node_kind='CHOICE_OUTPUT',perspective='SELF',
        title='明日の予定',unit_refs=['e4']))
    p['edges'][0]['unit_refs']=['e4']
    with pytest.raises(core.AnalysisSemanticMapError,match='event_plan_invalid'):compile_plan(p)


@pytest.mark.parametrize('profile',[core.SEMANTIC_MAP_PROFILE,core.SEMANTIC_MAP_EVENT_PLAN_PROFILE])
def test_v2_is_not_cross_admitted_into_a_prior_profile(profile):
    with pytest.raises(core.AnalysisSemanticMapError,match='profile_unbound'):
        compile_plan(prepared=material(profile))


def test_v1_raw_and_its_strict_reference_validation_remain_unchanged():
    from test_analysis_semantic_event_plan_compiler import plan as v1_plan,prepared as v1_prepared
    value=v1_plan();value['nodes'][0]['reading_refs']=['r1']
    with pytest.raises(core.AnalysisSemanticMapError,match='event_plan_invalid'):
        compiler.compile_analysis_semantic_map(v1_prepared(),value,response_sha256='a'*64)
    with pytest.raises(core.AnalysisSemanticMapError,match='profile_unbound'):compile_plan(v1_plan())


def accepts(packet,prepared=None):
    pytest.importorskip('lmformatenforcer')
    raw=json.dumps(packet,ensure_ascii=False,separators=(',',':'))
    alphabet=''.join(dict.fromkeys(raw+json.dumps(plan(),ensure_ascii=False)+'P '))
    parser=probe.semantic_json_parser((prepared or material()).messages(),alphabet)
    try:
        for char in raw:
            if char not in parser.get_allowed_characters():return False
            parser=parser.add_character(char)
        return parser.can_end()
    except ValueError:return False


def test_native_decoder_tracks_v2_nodes_edges_and_source_qualifications():
    assert accepts(plan())


def test_context_qualified_unknown_can_keep_its_prior_sentence_in_one_root():
    original='知人は受付へ質問する予定だと話した。その問い合わせを送ったか私は聞いていない。'
    prepared=material(first=original);p=plan()
    p['events'][0]['evidence']=[dict(quote=original,field=1)]
    p['events'][0]['fact']='知人が受付へ質問するという予定を話した。'
    p['events'][0]['unknowns']=[dict(source_quote=original,source_field=1)]
    assert accepts(p,prepared)
    assert json.loads(compile_plan(p,prepared).nodes_json)[0]['unknowns']==[original]


@pytest.mark.parametrize('mutate',[
    lambda p:p['nodes'][0].update(unit_refs=['r2']),
    lambda p:p['events'][0].update(unknowns=[dict(source_quote=JUDGED,source_field=2)]),
    lambda p:p['events'][1].update(unknowns=[dict(source_quote=ACHIEVED,source_field=2)]),
    lambda p:p['events'][0].update(unknowns=[dict(source_quote=SENT.replace('同僚は','同僚へ'),source_field=1)]),
    lambda p:p['edges'][0].update(to='n1'),
])
def test_native_decoder_rejects_missing_units_and_unbound_unknowns(mutate):
    p=plan();mutate(p);assert not accepts(p)


def test_new_profile_keeps_source_material_and_metadata_unchanged():
    p=material();old=material(core.SEMANTIC_MAP_PROFILE)
    assert p.frozen==old.frozen and p.fields==old.fields and p.source_guard==old.source_guard
    a=json.loads(p.material_json);b=json.loads(old.material_json)
    assert a.pop('model_schema')==SCHEMA and a==b
    assert p.request_ref!=old.request_ref and p.messages()!=old.messages()
    assert probe.semantic_output_schema(p.messages())['properties']['schema_version']['enum']==[SCHEMA]


@pytest.mark.parametrize('alias', [ALIAS, sources.SEMANTIC_EVENT_PLAN_V2_BASE_MODEL])
def test_exact_v2_alias_selects_new_profile_but_if_retains_original_identity(monkeypatch, alias):
    settings=environment(monkeypatch,model=alias)
    source=sources.application_analysis_model_source()
    assert sources.analysis_model_prompt_version(source)==PROFILE
    assert source._settings==settings
    if_source=if_sources.application_analysis_if_model_source()
    assert if_source.model==sources.SEMANTIC_EVENT_PLAN_BASE_MODEL
    assert if_source._settings_snapshot==settings
    assert sources._configured_semantic_prompt_version(alias+'-unknown')==core.SEMANTIC_MAP_PROFILE


def test_base_alias_keeps_identical_v2_messages_but_if_wire_still_uses_120u(monkeypatch):
    import asyncio
    from test_analysis_event_plan_model_alias import if_prepared
    from test_analysis_if_routes import packet as if_packet
    settings=environment(monkeypatch,model=sources.SEMANTIC_EVENT_PLAN_V2_BASE_MODEL)
    source=sources.application_analysis_model_source()
    prepared=material()
    packets=[]
    def receive(request):
        body=json.loads(request.content);packets.append(body)
        return httpx.Response(200,json=dict(model=body['model'],choices=[dict(
            finish_reason='stop',message=dict(role='assistant',content='synthetic transport only'))]))
    original_client=httpx.AsyncClient
    monkeypatch.setattr(sources.httpx,'AsyncClient',lambda **kwargs:
        original_client(**{**kwargs,'transport':kwargs.get('transport') or httpx.MockTransport(receive)}))
    receipt=asyncio.run(source(prepared))
    assert packets==[dict(model=sources.SEMANTIC_EVENT_PLAN_V2_BASE_MODEL,
        messages=prepared.messages(),temperature=0,max_tokens=4096,stream=False,
        chat_template_kwargs={'enable_thinking':False})]
    assert receipt.messages_sha256==core.semantic_map_hash(prepared.messages())
    assert source._settings==settings
    candidate_if=if_sources.application_analysis_if_model_source()
    bound_if=if_prepared()
    wire=[]
    def receive_if(request):
        body=json.loads(request.content);wire.append(body)
        return httpx.Response(200,json=dict(model=body['model'],choices=[dict(
            finish_reason='stop',message=dict(role='assistant',content=json.dumps(if_packet(bound_if))))]))
    candidate_if._transport=httpx.MockTransport(receive_if)
    asyncio.run(candidate_if(bound_if))
    assert wire[0]['model']==sources.SEMANTIC_EVENT_PLAN_BASE_MODEL
    assert wire[0]['max_tokens']==4096 and wire[0]['messages']==bound_if.messages()
    assert candidate_if._settings_snapshot==settings


def test_native_alias_binds_exact_v2_marker_and_keeps_legacy_control():
    calls=[]
    def generate(messages,end,*,profile=None):
        calls.append(profile);return 'synthetic-runtime-only','stop'
    server=ThreadingHTTPServer(('127.0.0.1',0),probe.make_handler(generate,api_key='synthetic-key',
        model_name='analysis',deadline=float('inf'),max_requests=2,max_new_tokens=4096,
        event_plan_model=ALIAS))
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        with httpx.Client(trust_env=False,headers={'Authorization':'Bearer synthetic-key'}) as client:
            def send(model,marker):
                messages=[dict(role='system',content='synthetic'),
                    dict(role='user',content=json.dumps(dict(model_schema=marker)))]
                return client.post(f'http://127.0.0.1:{server.server_port}/v1/chat/completions',
                    json=dict(model=model,messages=messages,temperature=0,max_tokens=4096,stream=False,
                        chat_template_kwargs={'enable_thinking':False}))
            assert send(ALIAS,probe.EVENT_PLAN_SCHEMA).status_code==400
            assert send('analysis',SCHEMA).status_code==400
            assert send(ALIAS,SCHEMA).status_code==200
            assert send('analysis',probe.IF_CANDIDATE_SCHEMA).status_code==200
            assert calls==['event_plan',None]
    finally:
        server.shutdown();server.server_close();thread.join(3)


def test_typed_response_still_uses_same_source_bound_compiler_and_sole_realizer():
    p=material();packet=plan()
    artifact,coverage=application.build_semantic_map(p,response(p,packet))
    projected=artifact.safe_projection(authenticated_owner_scope=OWNER)
    assert projected['wire_kind']=='watashi.map.v3' and coverage['mapped_count']==2
    assert projected['nodes'][0]['unknowns']==[SENT]
    assert artifact.private_evidence()['graph']['meaning_review']['event_plan']['plan']==packet


def test_two_readings_can_use_six_ground_events_within_existing_public_bounds():
    sentences=[str(i)+'件目の記録を残した。' for i in range(1,6)]
    prepared=material(first=''.join(sentences));p=plan()
    # The existing native coverage order visits both records before returning
    # to further events in the first record; no coverage rule is relaxed.
    roots=[(1,sentences[0],'RECORDED'),(2,JUDGED,'PERSON_JUDGMENT')]
    roots += [(1,sentence,'RECORDED') for sentence in sentences[1:]]
    p['events']=[dict(evidence=[dict(quote=sentence,field=field)],event_id='e'+str(i),
        source_mode=mode,fact=sentence,unknowns=[]) for i,(field,sentence,mode) in enumerate(roots,1)]
    p['readings']=[dict(reading_id='r1',event_refs=['e1','e2','e3'],meaning='記録を残し、説明を保証と区別している。'),
        dict(reading_id='r2',event_refs=['e4','e5','e6'],meaning='ほかに三つの記録を残している。')]
    p['nodes']=p['nodes'][:1];p['nodes'][0].update(unit_refs=['r1','r2']);p['edges']=[]
    p['overview']['unit_refs']=['r1','r2']
    assert accepts(p,prepared)
    graph=compile_plan(p,prepared)
    assert len(json.loads(graph.nodes_json)[0]['evidence_refs'])==6
    assert json.loads(graph.nodes_json)[0]['explanation']=='\n'.join(x['meaning'] for x in p['readings'])


def test_history_leaf_keeps_new_private_plan_and_rejects_unshown_root():
    prepared=material();stage=core.prepare_semantic_leaf(prepared,(prepared.frozen.members[0].saved_record_ref,))
    p=plan();p['events']=p['events'][:1];p['readings']=[];p['nodes']=p['nodes'][:1]
    p['edges']=[];p['overview']['unit_refs']=['e1']
    graph=core.build_semantic_stage(stage,response(stage,p))
    review=json.loads(graph.meaning_review_json)
    assert review['event_plan']['profile']==PROFILE and review['event_plan']['plan']==p
    assert review['history_synthesis']['kind']=='LEAF'
    hidden=deepcopy(p);hidden['events'][0]['evidence']=[dict(quote=JUDGED,field=2)]
    hidden['events'][0]['unknowns']=[]
    with pytest.raises(core.AnalysisSemanticMapError,match='analysis_semantic_history_evidence_not_shown'):
        core.build_semantic_stage(stage,response(stage,hidden))


def test_whole_person_correction_remains_root_while_unknown_is_only_its_qualification():
    from test_analysis_semantic_history_core import correction_snapshot
    snapshot=correction_snapshot()
    explanation='普段から避けているわけではありません。その時だけ返事を待ちました。返事が送られたかはまだ聞いていません。'
    snapshot['map_corrections'][0]['explanation']['text']=explanation
    parent=application.prepare_semantic_map(OWNER,snapshot,prompt_version=PROFILE)
    stage=core.prepare_semantic_leaf(parent,tuple(m.saved_record_ref for m in parent.frozen.members[:2]))
    fields=json.loads(stage.material_json)['fields']
    correction=next(f for f in fields if f['source_role']=='USER_ANALYSIS_MAP_CORRECTION')
    ordinary=[f for f in fields if f['record'] in (1,2) and f['field_path']=='memo']
    p=dict(schema_version=SCHEMA,events=[dict(evidence=[
        *[dict(quote=f['text'],field=f['field']) for f in ordinary],
        dict(quote=explanation,field=correction['field'])],event_id='e1',source_mode='PERSON_JUDGMENT',
        fact='その場で返事を待った事情を、普段の傾向とは区別して説明している。',
        unknowns=[dict(source_quote='返事が送られたかはまだ聞いていません。',source_field=correction['field'])])],
        readings=[],nodes=[dict(node_id='n1',node_kind='STATE_CONTEXT',perspective='SELF',
            title='本人が訂正した、その場の事情',unit_refs=['e1'])],edges=[],
        overview=dict(title='本人説明の範囲',unit_refs=['e1']))
    assert accepts(p,stage)
    graph=core.build_semantic_stage(stage,response(stage,p))
    assert json.loads(graph.nodes_json)[0]['unknowns']==['返事が送られたかはまだ聞いていません。']
    assert json.loads(graph.meaning_review_json)['event_plan']['plan']==p
    partial=deepcopy(p);partial['events'][0]['evidence'][-1]['quote']='その時だけ返事を待ちました。'
    with pytest.raises(core.AnalysisSemanticMapError,match='evidence_incomplete'):
        core.build_semantic_stage(stage,response(stage,partial))


def test_combined_dependency_unknowns_keep_existing_public_limit_without_truncation():
    sentences=[str(i)+'番目の状況はまだ分かりません。' for i in range(1,6)]
    original=''.join(sentences);prepared=material(first=original);p=plan()
    for index,parts in ((0,sentences[:3]),(1,sentences[3:])):
        p['events'][index]['evidence']=[dict(quote=original,field=1)]
        p['events'][index]['unknowns']=[dict(source_quote=s,source_field=1) for s in parts]
    p['nodes'][0]['unit_refs']=['e1','e2']
    before=deepcopy(p)
    with pytest.raises(core.AnalysisSemanticMapError):compile_plan(p,prepared)
    assert p==before and len(p['events'][0]['unknowns'])+len(p['events'][1]['unknowns'])==5
