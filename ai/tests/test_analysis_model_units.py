"""Private unit proposals preserve full context; structural tests, not teachers."""
import copy
from dataclasses import asdict, replace
import hashlib
import json
from unittest.mock import patch

import pytest
import analysis_cumulative_service as service
from cocolon_meaning_experience_engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.cores.analysis import intent_compiler as compiler
from cocolon_meaning_experience_engine.cores.analysis import observed_route_realizer as author
from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import (
    AnalysisModelUnitsResponse, AnalysisSemanticError, AnalysisSemanticUnsupported,
    canonical, serialize_analysis_model_units, reload_analysis_model_units)
from test_analysis_model_fields import sample
from test_analysis_cumulative import OWNER


def unit(quote, kind=None, parent=None, role=None, qualifiers=()):
    return dict(quote=quote, node_kind=kind, parent=parent, scope_role=role,
        qualifiers=[dict(kind=k, quote=q) for k,q in qualifiers])


def packet():
    return dict(fields=[dict(field=1, units=[
        unit('断ったこと', parent=2, role='CONTENT_TARGET'),
        unit('後悔してはいない', 'ATTENTION_OR_THOUGHT', qualifiers=[('NEGATION','はいない')]),
        unit('相手がどう思ったか', parent=4, role='UNKNOWN_CONTENT'),
        unit('分からない', role='WRITTEN_UNKNOWN', qualifiers=[('EPISTEMIC_EXPRESSION','分からない')])]),
        dict(field=2, units=[
        unit('疲れていたので', parent=2, role='WRITTEN_REASON', qualifiers=[('REASON_MARKER','ので')]),
        unit('今日の集まりへの誘いは断った', 'ACTION_OR_NONACTION', qualifiers=[('WRITTEN_MODIFIER','今日の集まり')])]),
        dict(field=3, units=[
        unit('昨日は分からなかった問題', parent=2, role='ATTRIBUTIVE_CONTENT',
            qualifiers=[('RELATIVE_TIME','昨日'),('EPISTEMIC_EXPRESSION','分からなかった')]),
        unit('今日は解けて', parent=3, role='TE_CONTEXT', qualifiers=[('RELATIVE_TIME','今日')]),
        unit('うれしい', 'IMMEDIATE_RESULT_OR_AFTERMATH')])])


def prepared(snap=None):
    return service.prepare_cumulative_model_units(OWNER, sample() if snap is None else snap)


def synthetic_call(p, data=None, *, raw=None, finish='stop'):
    # Capture these before obtaining a synthetic response, like the GPU caller.
    ref, sent_hash = p.request_ref, hashlib.sha256(canonical(p.messages()).encode()).hexdigest()
    raw = canonical(packet() if data is None else data) if raw is None else raw
    return replace(p, response=AnalysisModelUnitsResponse(ref, sent_hash,
        hashlib.sha256(raw.encode()).hexdigest(), finish, raw))


def build(data=None, snap=None):
    snap = sample() if snap is None else snap
    value = synthetic_call(prepared(snap), data)
    artifact, coverage = service.build_cumulative_unit_candidates(OWNER, snap, model_input=value)
    return value, artifact, coverage


def test_complete_context_units_and_dependent_scope_are_retained():
    value, artifact, coverage = build()
    assert coverage['source_count'] == coverage['unparsed_count'] == 2
    assert coverage['mapped_count'] == 0 and artifact.graph.route_edges == ()
    assert not isinstance(artifact.graph, compiler.ObservedGraph)
    assert not hasattr(artifact, 'safe_projection')
    assert sum(len(f.units) for f in artifact.graph.fields) == 9
    assert sum(len(u.qualifiers) for f in artifact.graph.fields for u in f.units) == 7
    diagram = json.loads(artifact.diagram_json)
    for field, visible in zip(artifact.graph.fields, diagram['fields']):
        assert field.complete_source_text in artifact.text
        assert visible['complete_source_text'] == field.complete_source_text
        assert visible['requires_complete_field_context']
        for u in field.units:
            assert field.complete_source_text[u.evidence.scalar_start:u.evidence.scalar_end] == u.quote
            assert u.actor == 'UNRESOLVED_NOT_OWNER_DERIVED'
            assert u.polarity == u.modality == u.temporal_scope == 'AS_WRITTEN_UNRESOLVED'
    a,b,c = artifact.graph.fields
    assert a.units[3].scope_role == 'WRITTEN_UNKNOWN' and a.units[3].node_kind is None
    assert a.units[0].qualifiers == ()  # Negation does not propagate to declined action.
    assert c.units[0].qualifiers[0].quote == '昨日'
    assert c.units[1].qualifiers[0].quote == '今日'
    assert c.units[2].qualifiers == ()  # No inferred date or cause for joy.
    assert any(c.complete_source_text[x:y] == '。🙂' for x,y in c.residual_ranges)


def test_file_replay_forbids_generation_compilation_and_author(tmp_path):
    value, artifact, coverage = build()
    path = tmp_path/'private-candidate.json'
    path.write_text(service.serialize_cumulative_unit_candidates(OWNER, sample(),
        model_input=value, artifact=artifact, coverage=coverage), encoding='utf-8')
    with patch.object(MeaningExperienceEngine, 'generate', side_effect=AssertionError('generate forbidden')), \
         patch.object(compiler, 'compile_analysis_unit_candidates', side_effect=AssertionError('compiler forbidden')), \
         patch.object(author, 'realize_analysis_unit_candidates', side_effect=AssertionError('author forbidden')):
        restored, counts = service.reload_cumulative_unit_candidates(OWNER, sample(), path.read_text(encoding='utf-8'))
    assert restored == artifact
    assert json.loads(path.read_text())['state']['graph']['fields'][2]['residual_ranges'][-1] == [24,26]
    assert counts == coverage and coverage['unparsed_count'] == 2


def test_stale_supplement_count_is_kept_in_the_same_saved_file():
    snap=sample(); old=copy.deepcopy(snap['members'][0]['original']); old['memo']='古い入力。'
    snap['members'][0].update(thread=dict(user_id=OWNER,original_emotion_id=old['id'],source_snapshot=old),
        events=[dict(kind='ANSWER')])
    value,artifact,coverage=build(snap=snap)
    assert coverage['stale_supplement_count'] == 1
    raw=service.serialize_cumulative_unit_candidates(OWNER,snap,
        model_input=value,artifact=artifact,coverage=coverage)
    restored,counts=service.reload_cumulative_unit_candidates(OWNER,snap,raw)
    assert restored == artifact and counts == coverage
    changed=json.loads(raw); changed['coverage']['stale_supplement_count']=0
    with pytest.raises(AnalysisSemanticError,match='coverage_invalid'):
        service.reload_cumulative_unit_candidates(OWNER,snap,canonical(changed))


def test_insufficient_partial_proposal_cannot_hide_the_negative_full_context():
    data = dict(fields=[dict(field=1,units=[unit('後悔','ATTENTION_OR_THOUGHT')]),
        dict(field=2,units=[]),dict(field=3,units=[])])
    _, artifact, coverage = build(data)
    assert '後悔してはいない' in artifact.text
    assert json.loads(artifact.diagram_json)['fields'][0]['complete_source_text'] == sample()['members'][0]['original']['memo']
    assert artifact.graph.semantic_status == 'UNVALIDATED_MODEL_CANDIDATE'
    assert coverage['mapped_count'] == 0 and coverage['unparsed_count'] == 2


@pytest.mark.parametrize('change', ['cycle','self','bool','float','out_of_field','depth',
    'unknown_parent','orphan','qualifier_outside','missing_quote','extra','bad_kind','unit_limit','qualifier_limit'])
def test_invalid_units_fail_closed(change):
    data=packet(); units=data['fields'][0]['units']
    if change=='cycle': units[1].update(node_kind=None,parent=1,scope_role='CONTENT_TARGET')
    if change=='self': units[0]['parent']=1
    if change=='bool': units[0]['parent']=True
    if change=='float': units[0]['parent']=2.0
    if change=='out_of_field': units[0]['parent']=6
    if change=='depth':
        units[0]['parent']=2; units[1].update(node_kind=None,parent=3,scope_role='CONTENT_TARGET'); units[2]['parent']=4
    if change=='unknown_parent': units[2]['parent']=2
    if change=='orphan': units[0]['parent']=None
    if change=='qualifier_outside': units[1]['qualifiers'][0]['quote']='断った'
    if change=='missing_quote': units[1]['quote']='後悔している'
    if change=='extra': units[1]['cause']='invented'
    if change=='bad_kind': units[1]['node_kind']='PERSONALITY'
    if change=='unit_limit': units.extend([copy.deepcopy(units[0])]*5)
    if change=='qualifier_limit': units[1]['qualifiers']*=7
    with pytest.raises(AnalysisSemanticError): build(data)


@pytest.mark.parametrize('change',['field_bool','field_missing','field_duplicate','field_reverse',
    'duplicate_key','nonfinite','wrapper','length','response_hash','messages','request','no_response'])
def test_packet_and_trusted_call_correspondence(change):
    p=prepared(); data=packet(); value=None
    if change=='field_bool': data['fields'][0]['field']=True
    if change=='field_missing': data['fields'].pop()
    if change=='field_duplicate': data['fields'][1]=copy.deepcopy(data['fields'][0])
    if change=='field_reverse': data['fields'].reverse()
    if change=='duplicate_key': value=synthetic_call(p,raw=canonical(data).replace('"field":1','"field":1,"field":1'))
    if change=='nonfinite': value=synthetic_call(p,raw='{"fields":NaN}')
    if change=='wrapper': value=synthetic_call(p,raw='```json\n{}\n```')
    if change=='length': value=synthetic_call(p,finish='length')
    value = value or synthetic_call(p,data)
    if change=='response_hash': value=replace(value,response=replace(value.response,raw=value.response.raw+' '))
    if change=='messages': value=replace(value,response=replace(value.response,messages_sha256='0'*64))
    if change=='request': value=replace(value,response=replace(value.response,request_ref='other'))
    if change=='no_response': value=p
    with pytest.raises(AnalysisSemanticError):
        service.build_cumulative_unit_candidates(OWNER,sample(),model_input=value)


@pytest.mark.parametrize('change',['owner','guard','version'])
def test_fresh_sources_reject_old_response(change):
    snap=sample(); value=synthetic_call(prepared(snap)); owner=OWNER
    if change=='owner': owner='00000000-0000-0000-0000-000000000002'
    if change=='guard': snap['guard']='analysis-db-cumulative-v1:'+'c'*64
    if change=='version': snap['members'][0]['original']['memo']+='変更。'
    with pytest.raises(AnalysisSemanticError):
        service.build_cumulative_unit_candidates(owner,snap,model_input=value)


@pytest.mark.parametrize('change',['text','diagram','graph','id','raw'])
def test_saved_candidate_tampering_is_rejected(change):
    value,artifact,_=build(); data=json.loads(serialize_analysis_model_units(value,artifact))
    if change=='text': data['text']=data['text'].replace('はいない','はいる')
    if change=='diagram': data['diagram']['fields'][0]['complete_source_text']='後悔'
    if change=='graph': data['graph']['fields'][0]['units'][0]['parent']=None
    if change=='id': data['candidate_id']='forged'
    if change=='raw': data['response']['raw']+=' '
    with pytest.raises(AnalysisSemanticError): reload_analysis_model_units(prepared(),canonical(data))


def test_overlapping_occurrences_are_ambiguous_but_unicode_remains_exact():
    snap=sample(); snap['members'][0]['original']['memo']='aaa🙂'
    data=packet(); data['fields'][0]['units']=[unit('aa','ATTENTION_OR_THOUGHT')]
    with pytest.raises(AnalysisSemanticError,match='ambiguous'): build(data,snap)
    data['fields'][0]['units']=[unit('aaa🙂','ATTENTION_OR_THOUGHT')]
    _,artifact,_=build(data,snap)
    u=artifact.graph.fields[0].units[0]
    assert u.evidence.scalar_end == 4 and u.evidence.utf8_end-u.evidence.utf8_start == 7


def test_explicit_actor_is_still_a_candidate_not_owner_derived():
    data=packet(); data['fields'][0]['units'][2]['qualifiers']=[dict(kind='EXPLICIT_ACTOR',quote='相手が')]
    _,artifact,_=build(data)
    assert artifact.graph.fields[0].units[2].actor == 'UNRESOLVED_NOT_OWNER_DERIVED'


def test_empty_candidates_are_retained_and_normal_build_never_selects_them():
    data=dict(fields=[dict(field=i,units=[]) for i in (1,2,3)])
    _,artifact,coverage=build(data)
    assert len(artifact.graph.fields) == 3 and coverage['unparsed_count'] == 2
    with patch.object(service,'prepare_cumulative_model_units',side_effect=AssertionError('not default')):
        assert service.build_cumulative_map(OWNER,sample())[0] is None


def test_clarified_instruction_has_distinct_binding_and_keeps_old_replay():
    old=prepared(); new=service.prepare_cumulative_model_units(OWNER,sample(),instruction_version='clarified.v1')
    assert old.request_ref != new.request_ref and old.messages() != new.messages()
    value=synthetic_call(new)
    artifact,counts=service.build_cumulative_unit_candidates(OWNER,sample(),model_input=value)
    raw=service.serialize_cumulative_unit_candidates(OWNER,sample(),model_input=value,artifact=artifact,coverage=counts)
    assert json.loads(raw)['state']['schema_version'].endswith('.v2')
    restored,recounted=service.reload_cumulative_unit_candidates(OWNER,sample(),raw,instruction_version='clarified.v1')
    assert restored==artifact and recounted==counts
    with pytest.raises(AnalysisSemanticError): service.reload_cumulative_unit_candidates(OWNER,sample(),raw)
    old_value,old_artifact,old_counts=build()
    old_raw=service.serialize_cumulative_unit_candidates(OWNER,sample(),model_input=old_value,artifact=old_artifact,coverage=old_counts)
    assert json.loads(old_raw)['state']['schema_version'].endswith('.v1')
    assert service.reload_cumulative_unit_candidates(OWNER,sample(),old_raw)==(old_artifact,old_counts)


@pytest.mark.parametrize('version',['unknown.v1',None,True])
def test_unknown_instruction_versions_are_not_defaulted(version):
    with pytest.raises(AnalysisSemanticError,match='instruction_invalid'):
        service.prepare_cumulative_model_units(OWNER,sample(),instruction_version=version)


def test_responses_cannot_be_transferred_between_instruction_versions():
    old=synthetic_call(prepared())
    new=service.prepare_cumulative_model_units(OWNER,sample(),instruction_version='clarified.v1')
    with pytest.raises(AnalysisSemanticError,match='response_invalid'):
        service.build_cumulative_unit_candidates(OWNER,sample(),model_input=replace(new,response=old.response))


def test_quote_first_preserves_meaning_and_replay_but_rejects_other_version_binding():
    new=service.prepare_cumulative_model_units(OWNER,sample(),instruction_version='quote_first.v1')
    data=packet()
    for field in data['fields']:
        field['units']=[{key:u[key] for key in ('quote','scope_role','node_kind','parent','qualifiers')}
            for u in field['units']]
    value=synthetic_call(new,raw=json.dumps(data,ensure_ascii=False,separators=(',',':')))
    artifact,counts=service.build_cumulative_unit_candidates(OWNER,sample(),model_input=value)
    assert artifact.graph.fields[0].units[2].parent == 4
    assert artifact.graph.fields[0].units[1].qualifiers[0].quote == 'はいない'
    raw=service.serialize_cumulative_unit_candidates(OWNER,sample(),model_input=value,artifact=artifact,coverage=counts)
    with patch.object(MeaningExperienceEngine,'generate',side_effect=AssertionError('no generation')):
        assert service.reload_cumulative_unit_candidates(OWNER,sample(),raw,instruction_version='quote_first.v1') == (artifact,counts)
    for version in ('baseline.v1','clarified.v1'):
        other=service.prepare_cumulative_model_units(OWNER,sample(),instruction_version=version)
        assert other.request_ref != new.request_ref
        with pytest.raises(AnalysisSemanticError):
            service.build_cumulative_unit_candidates(OWNER,sample(),model_input=replace(other,response=value.response))
        with pytest.raises(AnalysisSemanticError):
            service.reload_cumulative_unit_candidates(OWNER,sample(),raw,instruction_version=version)
