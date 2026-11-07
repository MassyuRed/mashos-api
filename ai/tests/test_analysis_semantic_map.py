"""Synthetic model responses test binding/visibility, not model reading quality."""
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
from uuid import UUID

import pytest

import analysis_semantic_map as semantic
from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import AnalysisModelQuotedParentUnitsResponse
from test_analysis_cumulative import OWNER, source_snapshot


def sample():
    snapshot = source_snapshot(2)
    snapshot['members'][0]['original'].update(memo='周りと同じ進み方より、自分が納得して選びたい。',
        memo_action='', category=['価値観', '人生'], emotions=['自己理解'],
        emotion_details=[{'type': '自己理解', 'strength': 'medium'}])
    snapshot['members'][1]['original'].update(memo='意見を聞かれず決まったことに腹が立った。自分で選びたい。',
        memo_action='別の人が方針を決めた。私は意見を言わなかった。', category=['価値観'], emotions=['怒り'],
        emotion_details=[{'type': '怒り', 'strength': 'strong'}])
    return snapshot


def candidate():
    return {'schema_version': semantic.MODEL_SCHEMA,
        'overview': {'title': '自分の選択と、その場の決定',
            'summary': '納得して選びたいという基準と、意見が決定に入っていない場面との距離が見えます。'},
        'nodes': [
            {'node_id': 'n1', 'node_kind': 'SELF_POSITION', 'title': '納得して選ぶ自分',
             'summary': '自分の納得を選ぶ基準に置きたいと述べています。',
             'explanation': '本人の記述には「自分が納得して選びたい」があります。周りと同じ進み方だけを基準にせず、選ぶ本人としての位置を大切にしたいという読みです。',
             'perspective': 'SELF', 'unknowns': [],
             'evidence': [{'field': 1, 'quote': '自分が納得して選びたい'}]},
            {'node_id': 'n2', 'node_kind': 'CHOICE_OUTPUT', 'title': '意見が決定に入らなかった場面',
             'summary': '希望と、その場で外へ出した内容の間に距離があります。',
             'explanation': '意見を聞かれず決まったことへの怒りと、自分で選びたいという希望が記されています。一方、その場では意見を言っていません。相手が本人をどう見ていたか、発言しなかった理由は記されていません。',
             'perspective': 'OBSERVED_INTERACTION', 'unknowns': ['その場で意見を伝えなかった理由'],
             'evidence': [{'field': 2, 'quote': '意見を聞かれず決まったことに腹が立った'},
                          {'field': 3, 'quote': '私は意見を言わなかった'}]}],
        'edges': [{'from': 'n1', 'to': 'n2', 'relation_kind': 'SELF_OUTSIDE_GAP',
                   'label': '希望と実際の位置の距離',
                   'explanation': '自分が納得して選ぶという基準を、実際の決定にどこまで入れられたかという関係として見比べられます。'}]}


def response(prepared, packet=None, *, raw=None):
    raw = semantic._canonical(candidate() if packet is None else packet) if raw is None else raw
    return AnalysisModelQuotedParentUnitsResponse(prepared.request_ref, semantic._hash(prepared.messages()),
        hashlib.sha256(raw.encode('utf-8')).hexdigest(), 'stop', raw)


def build(packet=None):
    prepared = semantic.prepare_semantic_map(OWNER, sample())
    artifact, coverage = semantic.build_semantic_map(prepared, response(prepared, packet))
    return prepared, artifact, coverage


def test_original_role_definition_and_all_ten_sample_materials_are_model_input_not_traits():
    snapshot = source_snapshot(10)
    cases = json.loads((Path(__file__).parent / 'fixtures/cocolon-input-contract-samples-20261107.json').read_text())['cases'][:10]
    for member, case in zip(snapshot['members'], cases):
        member['original'].update({key: case[key] for key in ('memo', 'memo_action', 'category', 'emotion_details')})
        member['original']['emotions'] = [emotion['type'] for emotion in case['emotion_details']]
    prepared = semantic.prepare_semantic_map(OWNER, snapshot)
    material = json.loads(prepared.material_json)
    assert len(material['records']) == 10 and len(material['fields']) == 19
    assert 'それぞれの世界における座標' in prepared.messages()[0]['content']
    assert '自分が自分の世界／他者の世界においてどう存在しているか' in prepared.messages()[0]['content']
    assert '内部分類' in prepared.messages()[0]['content']
    for index, (record, case) in enumerate(zip(material['records'], cases), 1):
        assert record['selected_categories'] == case['category']
        assert record['emotion_details'] == case['emotion_details']
        for name in ('memo', 'memo_action'):
            matching = [field['text'] for field in material['fields'] if field['record'] == index and field['field_path'] == name]
            assert matching == ([case[name]] if case[name] else [])
    assert OWNER not in prepared.material_json


def test_same_graph_gives_rich_details_relationships_accessible_text_and_private_exact_roots():
    prepared, artifact, counts = build()
    projection = artifact.safe_projection(authenticated_owner_scope=OWNER)
    assert semantic.validate_semantic_projection(projection, str(UUID(artifact.artifact_id[9:]))) == projection
    assert projection['wire_kind'] == 'watashi.map.v3'
    assert projection['edges'][0]['relation_kind'] == 'SELF_OUTSIDE_GAP'
    assert projection['nodes'][0]['context'] == ['価値観／人生：自己理解']
    assert projection['nodes'][1]['context'] == ['価値観：怒り・強']
    assert counts['mapped_count'] == 2 and counts['unparsed_count'] == 0
    text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text']
    assert all(node['explanation'] in text for node in projection['nodes'])
    assert projection['edges'][0]['explanation'] in text
    private = artifact.private_evidence()
    assert len(private['source_members']) == 2
    assert len(private['graph']['nodes'][1]['record_refs']) == 1
    for node in private['graph']['nodes']:
        assert len(node['record_refs']) == projection['nodes'][int(node['node_ref'][1:])-1]['evidence_badge_count']
        for root in node['evidence_refs']:
            field = next(field for field in prepared.fields if field[3].source_envelope_id == root['source_envelope_id'] and field[3].field_path == root['field_path'])
            quote = field[1][root['scalar_start']:root['scalar_end']]
            assert hashlib.sha256(quote.encode('utf-8')).hexdigest() == root['literal_sha256']
            source = next(source for source in prepared.frozen.sources if source.envelope.envelope_id == root['source_envelope_id'])
            assert source.envelope.raw_utf8[root['utf8_start']:root['utf8_end']].decode() == quote
    # Quotes and identities are private roots, never public payload fields.
    assert 'evidence_refs' not in semantic._canonical(projection)
    assert 'source_envelope_id' not in semantic._canonical(projection)
    assert 'messages_sha256' not in semantic._canonical(projection)


def test_common_engine_compiles_and_realizes_one_graph_for_all_views(monkeypatch):
    from cocolon_meaning_experience_engine.cores.analysis import intent_compiler, observed_route_realizer
    calls = []
    original_engine = semantic.MeaningExperienceEngine.generate
    original_compile = intent_compiler.compile_analysis_semantic_map
    original_realize = observed_route_realizer.realize_analysis_semantic_map
    def engine(self, *args, **kwargs):
        calls.append('engine')
        return original_engine(self, *args, **kwargs)
    def compile_map(*args, **kwargs):
        calls.append('compiler')
        return original_compile(*args, **kwargs)
    def realize_map(*args, **kwargs):
        calls.append('realizer')
        return original_realize(*args, **kwargs)
    monkeypatch.setattr(semantic.MeaningExperienceEngine, 'generate', engine)
    monkeypatch.setattr(intent_compiler, 'compile_analysis_semantic_map', compile_map)
    monkeypatch.setattr(observed_route_realizer, 'realize_analysis_semantic_map', realize_map)
    _, artifact, _ = build()
    assert calls == ['engine', 'compiler', 'realizer']
    assert type(artifact.graph) is intent_compiler.AnalysisSemanticMapGraph
    projection = artifact.safe_projection(authenticated_owner_scope=OWNER)
    private = artifact.private_evidence()
    for visible, owned in zip(projection['nodes'], private['graph']['nodes']):
        assert {key: owned[key] for key in visible} == visible
        assert owned['record_refs'] and owned['evidence_refs']
    assert private['graph_commitment'] == intent_compiler.commitment(private['graph'])
    assert artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'] == semantic.semantic_projection_text(projection)


@pytest.mark.parametrize('mutation', [
    lambda prepared: replace(prepared, material_json=prepared.material_json.replace('価値観', '偽の場面')),
    lambda prepared: replace(prepared, dictionary_json='{}'),
    lambda prepared: replace(prepared, fields=prepared.fields[:-1]),
    lambda prepared: replace(prepared, source_count=999),
])
def test_cmee_rechecks_prepared_material_even_when_response_matches_modified_messages(mutation):
    prepared = mutation(semantic.prepare_semantic_map(OWNER, sample()))
    with pytest.raises(semantic.SemanticMapError, match='analysis_semantic_input_unbound'):
        semantic.build_semantic_map(prepared, response(prepared))


@pytest.mark.parametrize('change', [
    lambda packet: packet['nodes'][0]['evidence'][0].update(quote='周囲に認められたい'),
    lambda packet: packet['nodes'][0]['evidence'][0].update(field=2),
    lambda packet: packet['nodes'][0]['evidence'][0].update(field=True),
    lambda packet: packet['nodes'][0]['evidence'].append(deepcopy(packet['nodes'][0]['evidence'][0])),
    lambda packet: packet['edges'][0].update(to='n99'),
    lambda packet: packet['edges'][0].update(to=2),
    lambda packet: packet['nodes'][1].update(node_id='n1'),
    lambda packet: packet['nodes'][1].update(node_id='n3'),
    lambda packet: packet['nodes'][1].update({key: packet['nodes'][0][key]
        for key in ('title', 'summary', 'explanation')}),
    lambda packet: packet['edges'][0].update(relation_kind='CAUSES'),
    lambda packet: packet['edges'].append(deepcopy(packet['edges'][0])),
    lambda packet: packet['nodes'][0].update(hidden_diagnosis='diagnosis'),
])
def test_unbound_evidence_invented_endpoint_or_extra_model_fields_never_become_saved_map(change):
    prepared = semantic.prepare_semantic_map(OWNER, sample())
    packet = candidate()
    change(packet)
    with pytest.raises(semantic.SemanticMapError):
        semantic.build_semantic_map(prepared, response(prepared, packet))


@pytest.mark.parametrize('field,value', [('request_ref', 'other'), ('messages_sha256', '0'*64),
    ('raw_sha256', '0'*64), ('finish_reason', 'length')])
def test_another_request_modified_messages_or_incomplete_model_output_is_not_adopted(field, value):
    prepared = semantic.prepare_semantic_map(OWNER, sample())
    with pytest.raises(semantic.SemanticMapError):
        semantic.build_semantic_map(prepared, replace(response(prepared), **{field: value}))


def test_duplicate_json_keys_and_other_owner_are_rejected_without_text_fallback():
    prepared, artifact, _ = build()
    raw = semantic._canonical(candidate()).replace('"overview":', '"overview":{},"overview":', 1)
    with pytest.raises(semantic.SemanticMapError):
        semantic.build_semantic_map(prepared, response(prepared, raw=raw))
    with pytest.raises(semantic.SemanticMapError, match='analysis_owner_mismatch'):
        artifact.safe_projection(authenticated_owner_scope=str(UUID(int=2)))


def test_saved_projection_is_closed_and_detached_from_returned_copy():
    _, artifact, _ = build()
    projection = artifact.safe_projection(authenticated_owner_scope=OWNER)
    projection['nodes'][0]['title'] = 'changed after reading'
    assert artifact.safe_projection(authenticated_owner_scope=OWNER)['nodes'][0]['title'] != projection['nodes'][0]['title']
    with pytest.raises(semantic.SemanticMapError):
        semantic.validate_semantic_projection(dict(projection, raw_model_text='private'), str(UUID(artifact.artifact_id[9:])))
    with pytest.raises(semantic.SemanticMapError):
        semantic.validate_semantic_projection(projection, str(UUID(int=999)))


def test_one_old_safety_source_does_not_block_other_eligible_sources_or_reach_model():
    snapshot = sample()
    snapshot['members'][1]['original']['memo'] = '死にたい。'
    prepared = semantic.prepare_semantic_map(OWNER, snapshot)
    assert len(prepared.frozen.members) == 1
    assert '死にたい' not in prepared.material_json
    packet = candidate()
    packet['nodes'] = packet['nodes'][:1]
    packet['edges'] = []
    artifact, counts = semantic.build_semantic_map(prepared, response(prepared, packet))
    assert counts == {'profile': 'cumulative.v1', 'source_count': 2, 'processed_count': 1,
        'mapped_count': 1, 'unparsed_count': 0, 'excluded_count': 1,
        'exclusion_reasons': {'analysis_separate_safety_required': 1}, 'stale_supplement_count': 0}
    assert len(artifact.private_evidence()['source_members']) == 1


@pytest.mark.parametrize('count', [0, 1, 2])
def test_no_eligible_material_carries_counts_without_acquiring_model(count):
    snapshot = source_snapshot(count)
    for member in snapshot['members']:
        member['original']['memo'] = '死にたい。'
    with pytest.raises(semantic.SemanticMapNoMaterial) as result:
        semantic.prepare_semantic_map(OWNER, snapshot)
    assert result.value.coverage['source_count'] == count
    assert result.value.coverage['processed_count'] == 0
    assert result.value.coverage['excluded_count'] == count


def test_old_answer_after_original_edit_is_not_sent_and_exclusion_count_survives():
    snapshot = sample()
    original = snapshot['members'][0]['original']
    previous = dict(original, memo='旧版にだけある本人の文。')
    snapshot['members'][0]['thread'] = {'user_id': OWNER, 'original_emotion_id': original['id'],
                                     'source_snapshot': previous}
    snapshot['members'][0]['events'] = [{'kind': 'ANSWER'}]
    prepared = semantic.prepare_semantic_map(OWNER, snapshot)
    assert '旧版にだけある本人の文' not in prepared.material_json
    _, counts = semantic.build_semantic_map(prepared, response(prepared))
    assert counts['stale_supplement_count'] == 1


def test_empty_legacy_text_is_accounted_for_without_hiding_an_unrelated_readable_record():
    snapshot = sample()
    snapshot['members'][1]['original'].update(memo='', memo_action='')
    prepared = semantic.prepare_semantic_map(OWNER, snapshot)
    packet = candidate()
    packet['nodes'] = packet['nodes'][:1]
    packet['edges'] = []
    _, counts = semantic.build_semantic_map(prepared, response(prepared, packet))
    assert counts['source_count'] == 2 and counts['processed_count'] == 1
    assert counts['exclusion_reasons'] == {'analysis_semantic_text_empty': 1}


def test_duplicate_original_identity_is_not_counted_as_two_independent_records():
    snapshot = sample()
    snapshot['members'][1] = deepcopy(snapshot['members'][0])
    with pytest.raises(semantic.SemanticMapError, match='analysis_semantic_duplicate_record'):
        semantic.prepare_semantic_map(OWNER, snapshot)
