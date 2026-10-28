"""Explicit named wire against independent source/prose fixtures; CPU, no SQL."""
import asyncio
import copy
from dataclasses import replace
import json

import pytest

from test_cmee_emlis_sixrow import state, fixture_packet, outcome, canonical
from test_cmee_preparation import emlis_request, original
from cocolon_meaning_experience_engine import named_reference_wire as named
from cocolon_meaning_experience_engine.preparation import prepare_emlis, receive_candidate
from cocolon_meaning_experience_engine.emlis_semantic_admission import (
    MODEL_PROFILE, SemanticInput, SemanticNotAdopted, prepare_model_snapshot,
    restore_model_snapshot,
)
from cocolon_meaning_experience_engine.model_candidate_source import (
    MODEL, REVISION, ModelCandidateSource, ModelCallLimits, ModelResponse,
    build_model_messages,
)


def named_fixture(packet):
    """Mechanical fixture writer with arbitrary names, independent of the decoder."""
    identities = {}
    def alias(value):
        if value not in identities.values():
            identities['identity'+str(len(identities))] = value
        return '@'+next(k for k,v in identities.items() if v == value)
    rows = [dict(id='proof'+str(i), s=alias(e['source_id']), f=e['field_path'], t=e['quote'])
            for i,e in enumerate(packet['evidence'])]
    def visit(value, key=None):
        if key in ('anchor_source_id', 'prior_snapshot_ref'):
            return alias(value)
        if key == 'evidence_indexes':
            return ['proof'+str(i) for i in value]
        if key == 'update_refs':
            return ['change'+str(i) for i in value]
        if isinstance(value, list):
            return [visit(x) for x in value]
        if isinstance(value, dict):
            return {named.KEYS[k]:visit(v,k) for k,v in value.items()}
        return value
    candidate = visit(packet['candidate'])
    for i,item in enumerate(candidate['updates']):
        item['$id'] = 'change'+str(i)
    return dict(v=named.SCHEMA, a=identities, q=rows, c=candidate)


def received(req, text, finish='stop', explicit=True):
    material = prepare_emlis(req)
    return receive_candidate(material,request_id=material.request_id,raw_output=text,
        finish_reason=finish,**({'candidate_format':named.SCHEMA} if explicit else {}))


def after(topic='book'):
    req,old,old_out,prior = state(topic,True)
    packet = fixture_packet(req,topic,prior)
    return req,old,old_out,prior,packet,named_fixture(packet)


@pytest.mark.parametrize('topic,count',[('book',7),('shop',8)])
def test_actual_named_raw_replay_native_meaning_body_all_updates_and_saved_resume(topic,count):
    req,old,old_out,prior,packet,wire = after(topic)
    raw = ' \n'+json.dumps(wire,ensure_ascii=False,indent=1)+'\n'
    receipt = received(req,raw)
    assert receipt.status == 'CANDIDATE_UNREVIEWED'
    assert receipt.raw_output == raw
    assert json.loads(receipt.candidate_json) == packet
    metadata = json.loads(receipt.metadata_json)
    assert metadata.pop('evidence_check') == 'LOCATION_ONLY_NOT_SEMANTIC_ADMISSION'
    material = prepare_emlis(req)
    assert receive_candidate(material,request_id=receipt.request_id,raw_output=raw,**metadata) == receipt
    prepared = prepare_model_snapshot(req,SemanticInput('FRESH_CANDIDATE',receipt,
        prior_snapshot_json=prior.semantic_snapshot,semantic_profile=MODEL_PROFILE))
    a,b = json.loads(prepared.semantic_snapshot),json.loads(old.semantic_snapshot)
    for key in ('packet','meaning_packet','native_bindings','question_control','source_bindings'):
        assert a[key] == b[key]
    assert len(a['packet']['candidate']['updates']) == count
    assert a['receipt']['raw_output'] == raw
    assert prepared.semantic_snapshot != old.semantic_snapshot
    result = outcome(req,prepared)
    assert result.artifact is not None and result.question is None
    for section in ('observation','reception','update_note'):
        assert getattr(result.artifact,section) == getattr(old_out.artifact,section)
    assert restore_model_snapshot(req,prepared.semantic_snapshot) == prepared
    resumed = replace(req,emlis_thread=replace(req.emlis_thread,
        prepared_meaning_checkpoint_ref=prepared.checkpoint.checkpoint_id))
    assert outcome(resumed,prepared) == result


@pytest.mark.parametrize('change',['native','raw','format','missing_format'])
def test_forged_receipt_is_rejected(change):
    req,_,_,prior,_,wire=after()
    receipt=received(req,canonical(wire))
    if change=='native': receipt=replace(receipt,candidate_json=receipt.candidate_json.replace('本','字',1))
    if change=='raw': receipt=replace(receipt,raw_output=receipt.raw_output.replace('本','字',1))
    if change in ('format','missing_format'):
        metadata=json.loads(receipt.metadata_json)
        if change=='format': metadata['candidate_format']='other'
        else: metadata.pop('candidate_format')
        receipt=replace(receipt,metadata_json=canonical(metadata))
    with pytest.raises(SemanticNotAdopted):
        prepare_model_snapshot(req,SemanticInput('FRESH_CANDIDATE',receipt,
            prior_snapshot_json=prior.semantic_snapshot,semantic_profile=MODEL_PROFILE))


@pytest.mark.parametrize('change',[
    'undefined_quote','duplicate_quote','numeric_quote','boolean_quote','missing_quote_field',
    'undefined_update','duplicate_update','missing_update','unknown_key','undefined_identity',
    'unused_identity','duplicate_identity_value','duplicate_json','truncated_json','nonfinite',
    'other_profile','other_core','empty_quotes','empty_quote',
])
def test_malformed_named_wire_closes_without_semantic_repair(change):
    req,_,_,_,_,wire=after()
    ev=wire['c']['claims'][0]['ev']
    if change=='undefined_quote': ev[0]='absent'
    if change=='duplicate_quote': wire['q'][1]['id']=wire['q'][0]['id']
    if change=='numeric_quote': ev[0]=0
    if change=='boolean_quote': ev[0]=True
    if change=='missing_quote_field': wire['q'][0].pop('f')
    if change=='undefined_update': wire['c']['prose']['binds'][-1]['ur']=['absent']
    if change=='duplicate_update': wire['c']['updates'][1]['$id']=wire['c']['updates'][0]['$id']
    if change=='missing_update': wire['c']['updates'][0].pop('$id')
    if change=='unknown_key': wire['c']['future']=True
    if change=='undefined_identity': wire['q'][0]['s']='@absent'
    if change=='unused_identity': wire['a']['unused']='other'
    if change=='duplicate_identity_value':
        wire['a']['dup']=next(iter(wire['a'].values()));wire['q'][0]['s']='@dup'
    if change=='other_profile': wire['c']['schema']='cocolon.cmee.semantic_mapping_proposal.v1'
    if change=='other_core': wire['c']['core']='piece'
    if change=='empty_quotes': wire['q']=[]
    if change=='empty_quote': wire['q'][0]['t']=''
    raw=canonical(wire)
    if change=='duplicate_json': raw=raw[:-1]+',"v":"'+named.SCHEMA+'"}'
    if change=='truncated_json': raw=raw[:-1]
    if change=='nonfinite': raw=raw.replace('"conflicts":[]','"conflicts":[NaN]')
    receipt=received(req,raw)
    assert receipt.raw_output == raw
    assert receipt.status == 'INVALID_FORMAT'
    assert receipt.candidate_json is None


@pytest.mark.parametrize('finish,status',[('timeout','TIMEOUT'),('length','TOKEN_LIMIT'),
    ('error','PROVIDER_ERROR'),('future','UNKNOWN_FINISH')])
def test_finish_status_dominates_valid_named_json(finish,status):
    req,_,_,_,_,wire=after()
    assert received(req,canonical(wire),finish).status == status


def test_missing_gap_is_not_supplied_by_decoder_or_reader():
    req,_,_,prior,_,wire=after()
    removed=wire['c']['updates'].pop()['$id']
    for binding in wire['c']['prose']['binds']:
        if 'ur' in binding: binding['ur']=[x for x in binding['ur'] if x != removed]
    receipt=received(req,canonical(wire))
    assert receipt.status=='CANDIDATE_UNREVIEWED'
    assert len(json.loads(receipt.candidate_json)['candidate']['updates'])==6
    with pytest.raises(SemanticNotAdopted,match='updates_not_bound'):
        prepare_model_snapshot(req,SemanticInput('FRESH_CANDIDATE',receipt,
            prior_snapshot_json=prior.semantic_snapshot,semantic_profile=MODEL_PROFILE))


@pytest.mark.parametrize('topic,after_answer',[('book',False),('shop',False),('repot',False),('knit',False)])
def test_new_format_cannot_select_initial_or_foreign_source_family(topic,after_answer):
    req,_,_,prior=state(topic,after_answer)
    with pytest.raises(ValueError,match='explanation_required'):
        build_model_messages(req,candidate_format=named.SCHEMA)
    raw=canonical(named_fixture(fixture_packet(req,topic,prior)))
    assert received(req,raw).status=='INVALID_FORMAT'


def test_named_raw_never_auto_detected_and_quote_default_receipt_unchanged():
    req,_,_,_,packet,wire=after()
    assert received(req,canonical(wire),explicit=False).status=='INVALID_FORMAT'
    from test_cmee_emlis_sixrow import wire as quoted
    raw=canonical(quoted(packet))
    a=received(req,raw,explicit=False)
    assert a.status=='CANDIDATE_UNREVIEWED'
    assert 'candidate_format' not in json.loads(a.metadata_json)
    assert received(req,raw).status=='INVALID_FORMAT'


@pytest.mark.parametrize('returned,finish,expected',[('named','stop','CANDIDATE_UNREVIEWED'),
    ('old','stop','PROVIDER_ERROR'),('old','length','TOKEN_LIMIT'),('old','timeout','TIMEOUT')])
def test_model_source_explicit_format_no_fallback_and_terminal_priority(returned,finish,expected):
    req,_,_,prior,packet,wire=after()
    from test_cmee_emlis_sixrow import wire as quoted
    raw=canonical(wire if returned=='named' else quoted(packet))
    calls=[]
    async def generate(messages,limits):
        calls.append(messages)
        return ModelResponse(raw,finish,'synthetic',MODEL,REVISION)
    source=ModelCandidateSource(generate,lambda _:100,limits=ModelCallLimits(5000,3584,1),candidate_format=named.SCHEMA)
    receipt=asyncio.run(source(req,prior.semantic_snapshot))
    assert len(calls)==1 and receipt.raw_output==raw and receipt.status==expected
    body=json.loads(calls[0][1]['content'])
    assert body['model_output_format']==named.SCHEMA
    assert body['output_spec']['shape']['c']['schema']=='cocolon.cmee.semantic_and_surface_proposal.v1'
    assert all('field_unicode_spans' not in s for s in body['material']['sources'])


def test_prepared_material_does_not_allow_foreign_family_even_with_valid_named_answer():
    # Location receipt cannot grant a family. The independent native owner still
    # checks source meanings and actual pending/prior lineage before adoption.
    # Initial named material fails before it can acquire a family label.
    req=emlis_request(original(memo='これは初回です。'))
    _,_,_,_,_,wire=after()
    assert received(req,canonical(wire)).status=='INVALID_FORMAT'


def test_valid_chair_answer_cannot_opt_itself_into_named_v3_family():
    from test_cmee_emlis_model_meaning import initial_model_request, model_packet, model_semantic, model_answer
    first=initial_model_request()
    prior=prepare_model_snapshot(first,model_semantic(first))
    req=model_answer(first,prior)
    packet=model_packet(req,prior)
    receipt=received(req,canonical(named_fixture(packet)))
    assert receipt.status=='CANDIDATE_UNREVIEWED'
    with pytest.raises(SemanticNotAdopted,match='named_reference_explanation_required'):
        prepare_model_snapshot(req,SemanticInput('FRESH_CANDIDATE',receipt,
            prior_snapshot_json=prior.semantic_snapshot,semantic_profile=MODEL_PROFILE))
    with pytest.raises(ValueError,match='explanation_required'):
        build_model_messages(req,prior.semantic_snapshot,candidate_format=named.SCHEMA)


@pytest.mark.parametrize('topic', ['book', 'shop'])
def test_named_prompt_prior_roundtrip_keeps_all_meanings_quotes_and_saved_bytes(topic):
    req, _, _, prior, _, _ = after(topic)
    saved = prior.semantic_snapshot
    quote_messages = build_model_messages(req, saved, candidate_format=named.QUOTE)
    quoted = json.loads(quote_messages[1]['content'])
    messages = build_model_messages(req, saved, candidate_format=named.SCHEMA)
    body = json.loads(messages[1]['content'])
    before = quoted['prior_adopted_interpretation']
    projected = body['prior_adopted_interpretation']
    decoded = named.decode(projected['meaning_packet'])
    assert decoded['candidate'] == before['meaning_packet']['candidate']
    assert decoded['evidence_quotes'] == before['meaning_packet']['evidence']
    assert projected['snapshot_ref'] == before['snapshot_ref']
    assert projected['semantic_profile'] == before['semantic_profile']
    assert body['material'] == quoted['material']
    assert prior.semantic_snapshot == saved
    assert build_model_messages(req, saved, candidate_format=named.QUOTE) == quote_messages
    for role in body['output_spec']['clause_roles'].values():
        assert not {'about_time', 'modality', 'time_expression'} & role.keys()
        assert {'time', 'mode', 'expr'} <= role.keys()
    # Calling the projection repeatedly never mutates the adopted snapshot.
    assert build_model_messages(req, saved, candidate_format=named.SCHEMA) == messages

