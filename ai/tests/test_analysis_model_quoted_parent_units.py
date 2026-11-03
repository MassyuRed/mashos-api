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


def role_sample(text='私の役割は連絡係だった。'):
    snap = sample()
    snap['members'] = snap['members'][:1]
    snap['members'][0]['original'].update(memo=text, memo_action='')
    return snap


def role_call(snap, *, quote=None, kind='ROLE', prompt='baseline.v1'):
    p = (service.prepare_cumulative_quoted_parent_units(OWNER, snap, prompt_version=prompt)
        if prompt in {'baseline.v1', 'semantic_boundaries.v2', 'semantic_boundaries.v3'} else
        service.prepare_cumulative_category_units(OWNER, snap, prompt_version=prompt))
    text = snap['members'][0]['original']['memo']
    data = {'fields': [{'field': 1, 'units': [dict(node_kind=kind,
        quote=text.rstrip('。．.') if quote is None else quote,
        parent_quote=None, scope_role=None, qualifiers=[])]}]}
    return call(p, data)


@pytest.mark.parametrize('text,role,polarity', [
    ('私の役割は連絡係だった。', '連絡係', 'positive'),
    ('わたしの役割は会場の受付でした。', '会場の受付', 'positive'),
    ('僕の役割は道具係ではなかった。', '道具係', 'negative'),
    ('私の役割は記録係ではありませんでした。', '記録係', 'negative'),
])
def test_written_role_model_vertical_adds_typed_meaning_to_the_existing_map(text, role, polarity):
    snap = role_sample(text); value = role_call(snap)
    before, before_counts = service.build_cumulative_map(OWNER, snap)
    assert before is None and before_counts['unparsed_count'] == 1
    candidate, candidate_counts = service.build_cumulative_quoted_parent_candidates(
        OWNER, snap, model_input=value)
    artifact, coverage = service.build_cumulative_written_role_map(OWNER, snap, model_input=value)
    assert type(artifact.graph) is compiler.ObservedGraph
    node, = artifact.graph.nodes
    assert (node.node_kind, node.proposition.actor, node.proposition.arguments,
        node.polarity, node.modality, node.temporal_scope, node.proposition.role_state) == (
            'ROLE', 'SELF', (('は', role),), polarity, 'fact', 'past', 'WRITTEN_PAST_ROLE')
    assert node.quoted_field is None and not artifact.graph.edges
    assert {g.missing_scope for g in artifact.graph.unknown_gaps} == set(compiler.NODE_KINDS) - {'ROLE'}
    assert coverage['mapped_count'] == 1 and coverage['unparsed_count'] == 0
    visual = artifact.safe_projection(authenticated_owner_scope=OWNER)
    body = artifact.safe_text_projection(authenticated_owner_scope=OWNER)
    assert visual['nodes'][0]['visible_label'] == text.rstrip('。．.') + '（記録された役割）'
    assert visual['nodes'][0]['visible_label'] in canonical(body)
    # Original candidates never become globally validated or rewritten.
    assert candidate_counts['mapped_count'] == 0 and candidate_counts['unparsed_count'] == 1
    assert candidate.graph.fields[0].units[0].actor == 'UNRESOLVED_NOT_OWNER_DERIVED'
    assert candidate.graph.fields[0].units[0].polarity == 'AS_WRITTEN_UNRESOLVED'


def test_written_role_uses_complete_source_witness_instead_of_an_actor_qualifier():
    snap = role_sample('私の役割は荷物の受付ではなかった。')
    value = role_call(snap, quote='荷物の受付ではなかった')
    artifact, _ = service.build_cumulative_written_role_map(OWNER, snap, model_input=value)
    node = artifact.graph.nodes[0]
    assert (node.proposition.actor, node.polarity) == ('SELF', 'negative')
    assert node.evidence_refs[0].scalar_start == 0
    assert node.evidence_refs[0].scalar_end == len(snap['members'][0]['original']['memo'])
    assert [role for role, _, _ in node.proposition.source_parts] == [
        'SELF_POSSESSIVE', 'EXPLICIT_ROLE_TOPIC', 'ROLE_NOMINAL', 'FINITE_ROLE_COPULA']


@pytest.mark.parametrize('text', [
    '連絡係だった。', '姉の役割は連絡係だった。', '私は無関係だった。',
    '私の役割は連絡係だったかもしれない。', '私の役割は連絡係だったか分からない。',
    '私の役割は連絡係だったと言われた。', '「私の役割は連絡係だった」と姉が言った。',
    'もし私の役割は連絡係だったなら困った。', '私の役割は連絡係だった。これは姉の話だ。',
    '私の役割は連絡係だ。', '私の役割は連絡係ではなかったわけではない。',
    '私の役割は誰の連絡係だった。', '私の役割は来週の連絡係だった。',
])
def test_written_role_does_not_promote_a_source_with_unresolved_actor_scope_or_time(text):
    from cocolon_meaning_experience_engine.cores.analysis.source_adapter import AnalysisSourceError
    snap = role_sample(text)
    with pytest.raises((AnalysisSemanticError, AnalysisSourceError)):
        service.build_cumulative_written_role_map(OWNER, snap, model_input=role_call(snap))


@pytest.mark.parametrize('change', ['other_field', 'two_records', 'wrong_kind', 'small_quote', 'false_qualifier'])
def test_written_role_does_not_drop_another_field_or_accept_a_conflicting_candidate(change):
    from cocolon_meaning_experience_engine.cores.analysis.source_adapter import AnalysisSourceError
    snap = role_sample(); value = role_call(snap)
    if change == 'other_field':
        snap['members'][0]['original']['memo_action'] = '姉の話を聞いた。'
        p = prepared(snap)
        data = json.loads(value.response.raw)
        data['fields'].append(dict(field=2, units=[]))
        value = call(p, data)
    if change == 'two_records':
        extra = copy.deepcopy(snap['members'][0]); extra['original']['id'] = '00000000-0000-0000-0000-000000000067'
        snap['members'].append(extra)
        data = json.loads(value.response.raw); data['fields'].append(dict(field=2, units=[]))
        value = call(prepared(snap), data)
    if change == 'wrong_kind': value = role_call(snap, kind='SCENE')
    if change == 'small_quote': value = role_call(snap, quote='連絡係')
    if change == 'false_qualifier':
        data = json.loads(value.response.raw)
        data['fields'][0]['units'][0]['qualifiers'] = [dict(kind='NEGATION', quote='だった')]
        value = call(prepared(snap), data)
    with pytest.raises((AnalysisSemanticError, AnalysisSourceError)):
        service.build_cumulative_written_role_map(OWNER, snap, model_input=value)


@pytest.mark.parametrize('prompt', ['baseline.v1', 'selected_categories.v1', 'selected_material.v2',
    'semantic_boundaries.v2', 'semantic_boundaries.v3'])
def test_written_role_saved_meaning_and_body_replay_without_engine_or_model_calls(prompt):
    snap = role_sample(); value = role_call(snap, prompt=prompt)
    artifact, coverage = service.build_cumulative_written_role_map(OWNER, snap, model_input=value)
    raw = service.serialize_cumulative_written_role_map(OWNER, snap,
        model_input=value, artifact=artifact, coverage=coverage)
    with patch.object(MeaningExperienceEngine, 'generate', side_effect=AssertionError('no generation')), \
         patch.object(compiler, 'compile_model_written_role_graph', side_effect=AssertionError('no compile')), \
         patch.object(author, 'realize_model_written_role_graph', side_effect=AssertionError('no author')):
        assert service.reload_cumulative_written_role_map(OWNER, snap, raw) == (artifact, coverage)
    assert json.loads(raw)['state']['response']['raw'] == value.response.raw


@pytest.mark.parametrize('change', ['owner', 'guard', 'source', 'role', 'polarity', 'text', 'diagram', 'coverage', 'bool'])
def test_written_role_saved_meaning_cannot_be_tampered_or_moved_to_a_fresh_source(change):
    snap = role_sample(); value = role_call(snap)
    artifact, coverage = service.build_cumulative_written_role_map(OWNER, snap, model_input=value)
    data = json.loads(service.serialize_cumulative_written_role_map(OWNER, snap,
        model_input=value, artifact=artifact, coverage=coverage))
    owner = OWNER; a = data['state']['artifact']
    if change == 'owner': owner = '00000000-0000-0000-0000-000000000002'
    if change == 'guard': snap['guard'] = 'analysis-db-cumulative-v1:' + 'f'*64
    if change == 'source': snap['members'][0]['original']['memo'] = '私の役割は道具係だった。'
    if change == 'role': a['graph']['nodes'][0]['proposition']['arguments'][0][1] = '道具係'
    if change == 'polarity': a['graph']['nodes'][0]['polarity'] = 'negative'
    if change == 'text': a['text'] = {'text': '連絡係という性格です。'}
    if change == 'diagram': a['diagram']['nodes'][0]['visible_label'] = '連絡係ではなかった'
    if change == 'coverage': data['coverage']['unparsed_count'] = 1
    if change == 'bool': data['coverage']['mapped_count'] = True
    with pytest.raises((AnalysisSemanticError, ValueError)):
        service.reload_cumulative_written_role_map(owner, snap, canonical(data))


@pytest.mark.parametrize('kind,quote', [('NEGATION', 'た'), ('EXPLICIT_ACTOR', '役割は')])
def test_written_role_qualifier_requires_the_actual_operator_or_holder(kind, quote):
    from cocolon_meaning_experience_engine.cores.analysis.source_adapter import AnalysisSourceError
    snap = role_sample('私の役割は連絡係ではなかった。')
    data = json.loads(role_call(snap).response.raw)
    data['fields'][0]['units'][0]['qualifiers'] = [dict(kind=kind, quote=quote)]
    with pytest.raises(AnalysisSourceError, match='analysis_written_role_qualifier_mismatch'):
        service.build_cumulative_written_role_map(OWNER, snap,
            model_input=call(prepared(snap), data))


def test_semantic_boundaries_are_an_explicit_instruction_only_variant():
    snap = sample(); old = prepared(snap)
    new = service.prepare_cumulative_quoted_parent_units(OWNER, snap, prompt_version='semantic_boundaries.v2')
    assert prepared(snap) == old and old.prompt_version == 'baseline.v1'
    assert new.request == old.request and new.source_guard == old.source_guard
    assert new.request_ref != old.request_ref
    assert new.messages()[1] == old.messages()[1]
    assert new.messages()[0]['content'].startswith(old.messages()[0]['content'] + '\n')
    assert json.loads(new.messages()[1]['content']) == json.loads(old.messages()[1]['content'])
    for p, foreign in [(new, call(old)), (old, call(new))]:
        with pytest.raises(AnalysisSemanticError):
            service.build_cumulative_quoted_parent_candidates(OWNER, snap,
                model_input=replace(p, response=foreign.response))


@pytest.mark.parametrize('prompt', ['semantic_boundaries.v2', 'semantic_boundaries.v3'])
def test_semantic_boundaries_saved_unit_file_replays_without_an_engine_compiler_or_author(prompt):
    snap = sample()
    p = service.prepare_cumulative_quoted_parent_units(OWNER, snap, prompt_version=prompt)
    value = call(p)
    artifact, counts = service.build_cumulative_quoted_parent_candidates(OWNER, snap, model_input=value)
    raw = service.serialize_cumulative_quoted_parent_candidates(OWNER, snap,
        model_input=value, artifact=artifact, coverage=counts)
    state = json.loads(raw)['state']
    assert state['schema_version'] == 'cocolon.cmee.analysis_model_units_quoted_parents_state.' + prompt
    assert state['prompt_version'] == prompt
    assert state['response']['raw'] == value.response.raw
    with patch.object(MeaningExperienceEngine, 'generate', side_effect=AssertionError('generate')), \
         patch.object(compiler, 'compile_analysis_unit_candidates', side_effect=AssertionError('compile')), \
         patch.object(compiler, 'compile_model_written_role_graph', side_effect=AssertionError('role compile')), \
         patch.object(author, 'realize_analysis_unit_candidates', side_effect=AssertionError('author')), \
         patch.object(author, 'realize_model_written_role_graph', side_effect=AssertionError('role author')):
        assert service.reload_cumulative_quoted_parent_candidates(OWNER, snap, raw) == (artifact, counts)
    assert counts['mapped_count'] == 0 and counts['unparsed_count'] == 2


@pytest.mark.parametrize('prompt', ['semantic_boundaries.v2', 'semantic_boundaries.v3'])
@pytest.mark.parametrize('change', ['version','schema','messages','request','qualifier'])
def test_semantic_boundaries_do_not_relabel_saved_calls_or_relax_source_binding(change, prompt):
    snap = sample()
    p = service.prepare_cumulative_quoted_parent_units(OWNER, snap, prompt_version=prompt)
    value = call(p)
    if change == 'qualifier':
        data = quoted_packet(); data['fields'][0]['units'][0]['qualifiers'] = [dict(kind='EXPLICIT_ACTOR', quote='原文外')]
        with pytest.raises(AnalysisSemanticError):
            service.build_cumulative_quoted_parent_candidates(OWNER, snap, model_input=call(p, data))
        return
    artifact, counts = service.build_cumulative_quoted_parent_candidates(OWNER, snap, model_input=value)
    data = json.loads(service.serialize_cumulative_quoted_parent_candidates(OWNER, snap,
        model_input=value, artifact=artifact, coverage=counts))
    state = data['state']
    if change == 'version': state['prompt_version'] = 'baseline.v1'
    if change == 'schema': state['schema_version'] = 'cocolon.cmee.analysis_model_units_quoted_parents_state.v1'
    if change == 'messages': state['response']['messages_sha256'] = call(prepared(snap)).response.messages_sha256
    if change == 'request': state['request_ref'] = prepared(snap).request_ref
    with pytest.raises(AnalysisSemanticError):
        service.reload_cumulative_quoted_parent_candidates(OWNER, snap, canonical(data))


@pytest.mark.parametrize('prompt', ['semantic_boundaries.v2', 'semantic_boundaries.v3'])
def test_semantic_boundaries_preserve_written_role_rejection_of_an_unwanted_copula_modifier(prompt):
    from cocolon_meaning_experience_engine.cores.analysis.source_adapter import AnalysisSourceError
    snap = role_sample()
    value = role_call(snap, prompt=prompt)
    data = json.loads(value.response.raw)
    data['fields'][0]['units'][0]['qualifiers'] = [dict(kind='WRITTEN_MODIFIER', quote='だった')]
    with pytest.raises((AnalysisSemanticError, AnalysisSourceError), match='analysis_written_role_qualifier_mismatch'):
        service.build_cumulative_written_role_map(OWNER, snap,
            model_input=call(service.prepare_cumulative_quoted_parent_units(OWNER, snap,
                prompt_version=prompt), data))


def test_semantic_v3_appends_one_public_reason_contrast_to_v2_only():
    snap = sample()
    v2 = service.prepare_cumulative_quoted_parent_units(OWNER, snap, prompt_version='semantic_boundaries.v2')
    v3 = service.prepare_cumulative_quoted_parent_units(OWNER, snap, prompt_version='semantic_boundaries.v3')
    assert prepared(snap).prompt_version == 'baseline.v1'
    assert v3.request == v2.request and v3.source_guard == v2.source_guard
    assert v3.request_ref != v2.request_ref and v3.messages()[1] == v2.messages()[1]
    assert v3.messages()[0]['content'].startswith(v2.messages()[0]['content'] + '\n')
    lines = v3.messages()[0]['content'].split('\n')
    inputs = [json.loads(line[len('例の入力:'):]) for line in lines if line.startswith('例の入力:')]
    outputs = [json.loads(line[len('例の出力:'):]) for line in lines if line.startswith('例の出力:')]
    assert len(inputs) == len(outputs) == 4
    old_lines = v2.messages()[0]['content'].split('\n')
    assert inputs[:3] == [json.loads(line[len('例の入力:'):]) for line in old_lines if line.startswith('例の入力:')]
    assert outputs[:3] == [json.loads(line[len('例の出力:'):]) for line in old_lines if line.startswith('例の出力:')]
    contrast = role_sample(inputs[-1]['fields'][0]['text'])
    p = service.prepare_cumulative_quoted_parent_units(OWNER, contrast, prompt_version='semantic_boundaries.v3')
    artifact, counts = service.build_cumulative_quoted_parent_candidates(OWNER, contrast,
        model_input=call(p, outputs[-1]))
    units = artifact.graph.fields[0].units
    assert [u.scope_role for u in units] == [None, 'WRITTEN_REASON', 'ATTRIBUTIVE_CONTENT']
    assert units[1].parent == 1 and units[2].parent == 2
    assert [(q.kind, q.quote) for q in units[1].qualifiers] == [('RELATIVE_TIME', '今日'), ('REASON_MARKER', 'ので')]
    assert counts['mapped_count'] == 0 and artifact.graph.route_edges == ()


@pytest.mark.parametrize('source,target', [('semantic_boundaries.v2','semantic_boundaries.v3'),
    ('semantic_boundaries.v3','semantic_boundaries.v2')])
def test_semantic_v2_v3_calls_and_saved_profiles_cannot_be_relabelled(source, target):
    from cocolon_meaning_experience_engine.cores.analysis.semantic_admission import reload_analysis_model_quoted_parent_units
    snap = sample()
    p = service.prepare_cumulative_quoted_parent_units(OWNER, snap, prompt_version=source)
    other = service.prepare_cumulative_quoted_parent_units(OWNER, snap, prompt_version=target)
    value = call(p)
    with pytest.raises(AnalysisSemanticError):
        service.build_cumulative_quoted_parent_candidates(OWNER, snap,
            model_input=replace(other, response=value.response))
    artifact, counts = service.build_cumulative_quoted_parent_candidates(OWNER, snap, model_input=value)
    saved = json.loads(service.serialize_cumulative_quoted_parent_candidates(OWNER, snap,
        model_input=value, artifact=artifact, coverage=counts))
    with pytest.raises(AnalysisSemanticError):
        reload_analysis_model_quoted_parent_units(other, canonical(saved['state']))
    saved['state']['prompt_version'] = target
    saved['state']['schema_version'] = 'cocolon.cmee.analysis_model_units_quoted_parents_state.' + target
    with pytest.raises(AnalysisSemanticError):
        service.reload_cumulative_quoted_parent_candidates(OWNER, snap, canonical(saved))


@pytest.mark.parametrize('prompt', ['semantic_boundaries.v2', 'semantic_boundaries.v3'])
def test_semantic_profiles_keep_complete_unknown_roots_without_mandatory_content_splitting(prompt):
    snap = role_sample('なぜ開催できたかは分からない。')
    p = service.prepare_cumulative_quoted_parent_units(OWNER, snap, prompt_version=prompt)
    data = dict(fields=[dict(field=1, units=[dict(quote='なぜ開催できたかは分からない',node_kind=None,
        parent_quote=None,scope_role='WRITTEN_UNKNOWN',
        qualifiers=[dict(kind='EPISTEMIC_EXPRESSION',quote='分からない')])])])
    artifact, counts = service.build_cumulative_quoted_parent_candidates(OWNER, snap, model_input=call(p, data))
    unit, = artifact.graph.fields[0].units
    assert unit.scope_role == 'WRITTEN_UNKNOWN' and unit.parent is None and unit.node_kind is None
    assert counts['mapped_count'] == 0 and counts['unparsed_count'] == 1 and artifact.graph.route_edges == ()


@pytest.mark.parametrize('prompt,ref,messages_hash,saved_hash', [
    ('baseline.v1','e0707847563ac1da98e11185201736153553fd5237961295a341503544668447',
        '26cb491d51904ec4cea26b42d89485d5ea1ef54a50bedb2674b58fc269bff69d','ad571817653c5958cb9490a78e77e6bb7d6637bcab9fe3cd65c4f55aaef30be7'),
    ('selected_categories.v1','0a699af3bbd412153779a26ee281d31c885c21cfbaa89b5bb787004ebb849b99',
        'faa24b0fea10811143604c9327e5b29bd4522090abcef51b73b3eeea9dbf8ee3','71fca025b6a8f973b29c3945c88744a7d768a1fa3b46a037ec3eb03e704309f2'),
    ('selected_material.v2','0bbf80a466bb1d067a4b6d7007c9058aa46fbaa6022a112bd01ae26fa21b5f8b',
        '6ac3eef2932535feb52456bde39679a012fe9874e1b46d6d491ca4a90724b5b4','e9ad25fb11119945bafa4104615ce2974a4dd639e88e262d383f397e42f65609'),
    ('semantic_boundaries.v2','664446f5f1b9fa7b1c2478ac4026683f9341e71e3a5d8da541779d03ff99b2e5',
        '4ec4139c1a0603a1a3d542c4c301aa37055906b8eb2e8acae7d0bbc06362afd0','9c745e1059b5536a7f9e0c07b802c7ff589486f827fba4d149c1d289fe18cdb7'),
])
def test_existing_quoted_profile_messages_refs_and_saved_bytes_remain_frozen(prompt, ref, messages_hash, saved_hash):
    from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as admission
    from cocolon_meaning_experience_engine.cores.analysis.source_adapter import (
        AnalysisObservedMapRequest, AnalysisSavedRecord, commitment)
    # Byte snapshots captured on dc05 before adding v3, using only this public fixture.
    original = dict(id='00000000-0000-0000-0000-000000000101',created_at='2025-01-01T01:00:00',
        memo='私の役割は連絡係だった。',memo_action='',category=['仕事'],emotions=['平穏'],emotion_details=[])
    record = AnalysisSavedRecord(OWNER,original['id'],commitment(original),canonical(original))
    request = AnalysisObservedMapRequest('analysis-model-compat',OWNER,'2025-01-01T01:00:00+00:00',
        '2026-11-01T08:00:00+00:00',(record,),selected_category_context=prompt.startswith('selected_'))
    p = admission.prepare_analysis_model_quoted_parent_units(request,
        source_guard='analysis-db-cumulative-v1:'+'a'*64,prompt_version=prompt)
    value = call(p, dict(fields=[dict(field=1,units=[dict(quote='私の役割は連絡係だった',node_kind='ROLE',
        parent_quote=None,scope_role=None,qualifiers=[])])]))
    artifact = admission.generate_analysis_model_quoted_parent_units(request,value)
    saved = admission.serialize_analysis_model_quoted_parent_units(value,artifact)
    assert p.request_ref == 'analysis-quoted-parent-units-request:' + ref
    assert hashlib.sha256(canonical(p.messages()).encode()).hexdigest() == messages_hash
    assert hashlib.sha256(saved.encode()).hexdigest() == saved_hash
    assert admission.reload_analysis_model_quoted_parent_units(p,saved) == artifact

