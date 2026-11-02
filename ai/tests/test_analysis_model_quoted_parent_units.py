"""New private wire binds quoted parents; these are structural synthetic cases."""
import copy
from dataclasses import replace
import hashlib
import json
from unittest.mock import patch

import pytest
import analysis_cumulative_service as service
from cocolon_meaning_experience_engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.cores.analysis import intent_compiler as compiler
from cocolon_meaning_experience_engine.cores.analysis import observed_route_realizer as author
from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import (
    AnalysisModelQuotedParentUnitsResponse, AnalysisSemanticError, canonical,
    serialize_analysis_model_quoted_parent_units, serialize_analysis_model_units)
from test_analysis_model_fields import sample
from test_analysis_model_units import packet, build as old_build, synthetic_call as old_call
from test_analysis_cumulative import OWNER


def quoted_packet():
    # Derive only this synthetic test fixture, never a saved model raw.
    data = packet()
    for field in data['fields']:
        old = field['units']
        field['units'] = [dict(quote=u['quote'], node_kind=u['node_kind'],
            parent_quote=None if u['parent'] is None else old[u['parent']-1]['quote'],
            scope_role=u['scope_role'], qualifiers=u['qualifiers']) for u in old]
    return data


def prepared(snap=None):
    return service.prepare_cumulative_quoted_parent_units(OWNER, sample() if snap is None else snap)


def call(p, data=None, *, raw=None, finish='stop'):
    sent = hashlib.sha256(canonical(p.messages()).encode()).hexdigest()
    raw = canonical(quoted_packet() if data is None else data) if raw is None else raw
    return replace(p, response=AnalysisModelQuotedParentUnitsResponse(p.request_ref, sent,
        hashlib.sha256(raw.encode()).hexdigest(), finish, raw))


def build(data=None, snap=None):
    snap = sample() if snap is None else snap
    value = call(prepared(snap), data)
    artifact, counts = service.build_cumulative_quoted_parent_candidates(OWNER, snap, model_input=value)
    return value, artifact, counts


def test_new_wire_binds_same_source_fields_and_preserves_actual_raw():
    value, artifact, coverage = build()
    _, old, old_counts = old_build()
    assert artifact.graph.fields == old.graph.fields
    assert json.loads(artifact.diagram_json)['fields'] == json.loads(old.diagram_json)['fields']
    assert coverage == old_counts and coverage['unparsed_count'] == 2 and coverage['mapped_count'] == 0
    assert artifact.graph.route_edges == () and not hasattr(artifact, 'safe_projection')
    assert not isinstance(artifact.graph, compiler.ObservedGraph)
    saved = json.loads(serialize_analysis_model_quoted_parent_units(value, artifact))
    assert saved['response']['raw'] == value.response.raw
    assert 'parent_quote' in saved['response']['raw']
    assert '"parent":' not in saved['response']['raw']
    for field in artifact.graph.fields:
        assert field.complete_source_text in artifact.text
        for u in field.units:
            assert field.complete_source_text[u.evidence.scalar_start:u.evidence.scalar_end] == u.quote
            assert u.actor == 'UNRESOLVED_NOT_OWNER_DERIVED'
            assert u.polarity == u.modality == u.temporal_scope == 'AS_WRITTEN_UNRESOLVED'


def test_parent_quotes_survive_unit_reordering_without_rewriting_references():
    data = quoted_packet(); units = data['fields'][0]['units']
    data['fields'][0]['units'] = [units[3], units[2], units[0], units[1]]
    _, artifact, _ = build(data)
    units = artifact.graph.fields[0].units
    assert units[1].parent == 1 and units[2].parent == 4
    # Forward parent plus the existing two-level attribute/context tree.
    assert artifact.graph.fields[2].units[0].parent == 2
    assert artifact.graph.fields[2].units[1].parent == 3


def test_all_prompt_demonstrations_use_only_the_new_wire():
    instruction = prepared().messages()[0]['content']
    examples = [json.loads(line[len('例の出力:'):]) for line in instruction.split('\n')
                if line.startswith('例の出力:')]
    assert len(examples) == 3
    for example in examples:
        for field in example['fields']:
            for u in field['units']:
                assert set(u) == {'quote','node_kind','parent_quote','scope_role','qualifiers'}
                if u['parent_quote'] is not None:
                    assert sum(p['quote'] == u['parent_quote'] for p in field['units']) == 1


def test_same_file_replay_never_generates_compiles_or_authors():
    value, artifact, counts = build()
    raw = service.serialize_cumulative_quoted_parent_candidates(OWNER, sample(),
        model_input=value, artifact=artifact, coverage=counts)
    with patch.object(MeaningExperienceEngine, 'generate', side_effect=AssertionError('generate')), \
         patch.object(compiler, 'compile_analysis_unit_candidates', side_effect=AssertionError('compile')), \
         patch.object(author, 'realize_analysis_unit_candidates', side_effect=AssertionError('author')):
        assert service.reload_cumulative_quoted_parent_candidates(OWNER, sample(), raw) == (artifact, counts)


@pytest.mark.parametrize('change', ['missing','foreign','ambiguous','self','cycle','depth','unknown_root',
    'int','bool','list','blank','changed_copy','old_key','mixed_keys','qualifier_outside','bad_quote','too_many'])
def test_invalid_parent_links_and_source_units_fail_closed(change):
    data = quoted_packet(); units = data['fields'][0]['units']
    if change == 'missing': units[0]['parent_quote'] = 'でも'  # In source, not a returned unit.
    if change == 'foreign': units[0]['parent_quote'] = data['fields'][1]['units'][1]['quote']
    if change == 'ambiguous':
        duplicate = copy.deepcopy(units[1]); duplicate['node_kind'] = 'SCENE'; units.append(duplicate)
    if change == 'self': units[0]['parent_quote'] = units[0]['quote']
    if change == 'cycle': units[1].update(node_kind=None, parent_quote=units[0]['quote'], scope_role='CONTENT_TARGET')
    if change == 'depth':
        units[1].update(node_kind=None, parent_quote=units[2]['quote'], scope_role='CONTENT_TARGET')
        units[2]['scope_role'] = 'CONTENT_TARGET'
    if change == 'unknown_root': units[2]['parent_quote'] = units[1]['quote']
    if change == 'int': units[0]['parent_quote'] = 2
    if change == 'bool': units[0]['parent_quote'] = True
    if change == 'list': units[0]['parent_quote'] = [units[1]['quote']]
    if change == 'blank': units[0]['parent_quote'] = ''
    if change == 'changed_copy': units[0]['parent_quote'] += ' '
    if change == 'old_key': units[0]['parent'] = units[0].pop('parent_quote')
    if change == 'mixed_keys': units[0]['parent'] = 2
    if change == 'qualifier_outside': units[1]['qualifiers'][0]['quote'] = units[0]['quote']
    if change == 'bad_quote': units[1]['quote'] = '後悔している'
    if change == 'too_many': units.extend(copy.deepcopy(units[0]) for _ in range(5))
    with pytest.raises(AnalysisSemanticError): build(data)


@pytest.mark.parametrize('change', ['request','messages','raw','length','no_response','old_response',
    'duplicate_key','nonfinite','field_order','field_bool','field_missing','unit_key'])
def test_trusted_call_and_strict_packet_binding(change):
    p = prepared(); data = quoted_packet(); value = None
    if change == 'duplicate_key': value = call(p, raw=canonical(data).replace('"field":1','"field":1,"field":1'))
    if change == 'nonfinite': value = call(p, raw='{"fields":NaN}')
    if change == 'field_order': data['fields'].reverse()
    if change == 'field_bool': data['fields'][0]['field'] = True
    if change == 'field_missing': data['fields'].pop()
    if change == 'unit_key': data['fields'][0]['units'][0]['cause'] = 'invented'
    value = value or call(p, data)
    if change == 'request': value = replace(value, response=replace(value.response, request_ref='other'))
    if change == 'messages': value = replace(value, response=replace(value.response, messages_sha256='0'*64))
    if change == 'raw': value = replace(value, response=replace(value.response, raw=value.response.raw+' '))
    if change == 'length': value = replace(value, response=replace(value.response, finish_reason='length'))
    if change == 'no_response': value = p
    if change == 'old_response':
        old = service.prepare_cumulative_model_units(OWNER, sample())
        value = replace(value, response=old_call(old).response)
    with pytest.raises(AnalysisSemanticError):
        service.build_cumulative_quoted_parent_candidates(OWNER, sample(), model_input=value)


@pytest.mark.parametrize('change', ['owner','guard','version'])
def test_fresh_sources_do_not_accept_an_old_call(change):
    snap = sample(); value = call(prepared(snap)); owner = OWNER
    if change == 'owner': owner = '00000000-0000-0000-0000-000000000002'
    if change == 'guard': snap['guard'] = 'analysis-db-cumulative-v1:'+'c'*64
    if change == 'version': snap['members'][0]['original']['memo'] += '変更。'
    with pytest.raises(AnalysisSemanticError):
        service.build_cumulative_quoted_parent_candidates(owner, snap, model_input=value)


@pytest.mark.parametrize('change', ['schema','text','diagram','graph','id','raw','coverage'])
def test_saved_payload_tampering_is_rejected(change):
    value, artifact, counts = build()
    data = json.loads(service.serialize_cumulative_quoted_parent_candidates(OWNER, sample(),
        model_input=value, artifact=artifact, coverage=counts))
    state = data['state']
    if change == 'schema': state['schema_version'] = 'cocolon.cmee.analysis_model_units_state.v2'
    if change == 'text': state['text'] += 'invented'
    if change == 'diagram': state['diagram']['fields'][0]['complete_source_text'] = 'changed'
    if change == 'graph': state['graph']['fields'][0]['units'][0]['parent'] = None
    if change == 'id': state['candidate_id'] = 'forged'
    if change == 'raw': state['response']['raw'] += ' '
    if change == 'coverage': data['coverage']['unparsed_count'] = 0
    with pytest.raises(AnalysisSemanticError):
        service.reload_cumulative_quoted_parent_candidates(OWNER, sample(), canonical(data))


def test_old_new_requests_raw_and_saved_files_cannot_be_interchanged():
    new, artifact, counts = build(); old, old_artifact, old_counts = old_build()
    assert new.request_ref != old.request_ref and new.messages() != old.messages()
    assert json.loads(new.messages()[1]['content'])['schema_version'].endswith('quoted_parents.v1')
    for make in [lambda: serialize_analysis_model_units(new, artifact),
                 lambda: serialize_analysis_model_quoted_parent_units(old, old_artifact),
                 lambda: service.build_cumulative_unit_candidates(OWNER, sample(), model_input=new),
                 lambda: service.build_cumulative_quoted_parent_candidates(OWNER, sample(), model_input=old),
                 lambda: service.build_cumulative_quoted_parent_candidates(OWNER, sample(), model_input=call(prepared(), packet()))]:
        with pytest.raises(AnalysisSemanticError): make()
    old_raw = service.serialize_cumulative_unit_candidates(OWNER, sample(), model_input=old,
        artifact=old_artifact, coverage=old_counts)
    new_raw = service.serialize_cumulative_quoted_parent_candidates(OWNER, sample(), model_input=new,
        artifact=artifact, coverage=counts)
    with pytest.raises(AnalysisSemanticError): service.reload_cumulative_unit_candidates(OWNER, sample(), new_raw)
    with pytest.raises(AnalysisSemanticError): service.reload_cumulative_quoted_parent_candidates(OWNER, sample(), old_raw)
    assert service.reload_cumulative_unit_candidates(OWNER, sample(), old_raw) == (old_artifact, old_counts)


def test_ambiguous_source_quotes_remain_rejected_and_unicode_ranges_exact():
    snap = sample(); snap['members'][0]['original']['memo'] = 'aaa🙂'
    data = quoted_packet(); data['fields'][0]['units'] = [dict(quote='aa', node_kind='ATTENTION_OR_THOUGHT',
        parent_quote=None, scope_role=None, qualifiers=[])]
    with pytest.raises(AnalysisSemanticError, match='ambiguous'): build(data, snap)
    data['fields'][0]['units'][0]['quote'] = 'aaa🙂'
    _, artifact, _ = build(data, snap)
    u = artifact.graph.fields[0].units[0]
    assert u.evidence.scalar_end == 4 and u.evidence.utf8_end-u.evidence.utf8_start == 7


def test_normal_map_never_selects_new_profile():
    with patch.object(service, 'prepare_cumulative_quoted_parent_units', side_effect=AssertionError('not default')):
        assert service.build_cumulative_map(OWNER, sample())[0] is None



def test_material_context_binds_record_fields_and_saved_selections_without_ids():
    snap = sample()
    snap['members'][0]['original']['category'] = ['仕事']
    snap['members'][1]['original']['category'] = ['趣味']
    p = service.prepare_cumulative_category_units(OWNER, snap, prompt_version='selected_material.v2')
    material = json.loads(p.messages()[1]['content'])
    assert len(material['records']) == 2
    assert [r['fields'] for r in material['records']] == [[1, 2], [3]]
    assert [f['record'] for f in material['fields']] == [1, 1, 2]
    for context, member in zip(material['records'], snap['members']):
        raw = member['original']
        assert context['selected_categories'] == raw['category']
        assert context['selected_emotions'] == raw['emotions']
        assert context['emotion_details'] == raw['emotion_details']
        assert context['recorded_at'].startswith(raw['created_at'][:19])
        assert set(context) == {'record','recorded_at','selected_categories','selected_emotions','emotion_details','fields'}
        assert raw['id'] not in p.messages()[1]['content']
    assert material['analysis_as_of'] == p.request.period_end
    assert '記録日時で、本文の出来事日時ではありません' in p.messages()[0]['content']
    assert 'recordsの値を引用しません' in p.messages()[0]['content']


@pytest.mark.parametrize('prompt', ['baseline.v1', 'selected_categories.v1', 'selected_material.v2'])
def test_all_three_saved_message_versions_replay_without_generation(prompt):
    snap = sample()
    p = (prepared(snap) if prompt == 'baseline.v1' else
        service.prepare_cumulative_category_units(OWNER, snap, prompt_version=prompt))
    value = call(p)
    artifact, counts = service.build_cumulative_quoted_parent_candidates(OWNER, snap, model_input=value)
    saved = service.serialize_cumulative_quoted_parent_candidates(OWNER, snap,
        model_input=value, artifact=artifact, coverage=counts)
    with patch.object(MeaningExperienceEngine, 'generate', side_effect=AssertionError('generate')), \
         patch.object(compiler, 'compile_analysis_unit_candidates', side_effect=AssertionError('compile')), \
         patch.object(author, 'realize_analysis_unit_candidates', side_effect=AssertionError('author')):
        assert service.reload_cumulative_quoted_parent_candidates(OWNER, snap, saved) == (artifact, counts)
    assert counts['mapped_count'] == 0 and artifact.graph.route_edges == ()
    material = json.loads(p.messages()[1]['content'])
    if prompt != 'selected_material.v2':
        assert set(material) == {'schema_version','fields'}
        assert all('record' not in f for f in material['fields'])
    if prompt == 'baseline.v1':
        assert all(set(f) == {'field','field_path','text'} for f in material['fields'])
    elif prompt == 'selected_categories.v1':
        assert all(set(f) == {'field','field_path','text','selected_categories'} for f in material['fields'])


@pytest.mark.parametrize('change', ['created_at','emotions','category'])
def test_material_context_changes_invalidate_the_old_call(change):
    snap = sample()
    p = service.prepare_cumulative_category_units(OWNER, snap, prompt_version='selected_material.v2')
    value = call(p)
    replacement = {'created_at':'2025-01-01T01:01:00','emotions':['怒り'],'category':['趣味']}[change]
    snap['members'][0]['original'][change] = replacement
    changed = service.prepare_cumulative_category_units(OWNER, snap, prompt_version='selected_material.v2')
    assert changed.messages() != p.messages()
    with pytest.raises(AnalysisSemanticError):
        service.build_cumulative_quoted_parent_candidates(OWNER, snap, model_input=value)


def test_material_metadata_is_not_an_extra_quote_source_or_a_legacy_saved_state():
    snap = sample()
    p = service.prepare_cumulative_category_units(OWNER, snap, prompt_version='selected_material.v2')
    packet = quoted_packet()
    packet['fields'][0]['units'][0]['quote'] = '2025-01-01T01:00:00+00:00'
    with pytest.raises(AnalysisSemanticError):
        service.build_cumulative_quoted_parent_candidates(OWNER, snap, model_input=call(p, packet))
    value = call(p)
    artifact, counts = service.build_cumulative_quoted_parent_candidates(OWNER, snap, model_input=value)
    saved = json.loads(service.serialize_cumulative_quoted_parent_candidates(OWNER, snap,
        model_input=value, artifact=artifact, coverage=counts))
    saved['state']['prompt_version'] = 'selected_categories.v1'
    with pytest.raises(AnalysisSemanticError):
        service.reload_cumulative_quoted_parent_candidates(OWNER, snap, canonical(saved))
