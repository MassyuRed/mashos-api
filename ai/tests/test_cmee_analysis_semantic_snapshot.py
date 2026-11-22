"""Approved P5: bounded meaning, sole realizer and private replay; no live I/O."""
from contextlib import ExitStack
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.preparation import prepare_analysis, receive_candidate
from cocolon_meaning_experience_engine.cores.analysis.source_adapter import (
    AnalysisObservedMapRequest, AnalysisSavedRecord, AnalysisSupplement,
    canonical_bytes, commitment,
)
from cocolon_meaning_experience_engine.cores.analysis import intent_compiler as compiler
from cocolon_meaning_experience_engine.cores.analysis import observed_route_realizer as realizer
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as sem


FIXTURE = json.loads((Path(__file__).parent / 'fixtures/cmee_analysis_semantic_snapshot_v1.json').read_text())


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def context(*, packet=None, originals=None, tier='plus', owner=None):
    rows = deepcopy(FIXTURE['originals'] if originals is None else originals)
    owner = FIXTURE['owner_scope'] if owner is None else owner
    request = AnalysisObservedMapRequest(
        FIXTURE['operation_request_id'], owner, FIXTURE['period']['start'],
        FIXTURE['period']['end_exclusive'], tuple(
            AnalysisSavedRecord(owner, raw['id'], commitment(raw), canonical_bytes(raw).decode())
            for raw in rows))
    prepared = prepare_analysis(request, tier=tier)
    receipt = receive_candidate(prepared, request_id=prepared.request_id,
        raw_output=canonical(FIXTURE['packet'] if packet is None else packet),
        finish_reason='stop', provider='HAND_AUTHORED_P5_SYNTHETIC')
    return request, sem.AnalysisSemanticInputV1(prepared, receipt, tier=tier)


def status(result):
    return getattr(result.status, 'value', result.status)


def generated(**kwargs):
    request, semantic_input = context(**kwargs)
    result = MeaningExperienceEngine().generate(request, semantic_input=semantic_input)
    assert result.decision == 'ADOPTED_PROVISIONAL', result.reason_codes
    assert status(result) == 'GENERATED', result.reason_codes
    assert result.snapshot is not None and result.graph is not None and result.artifact is not None
    return request, semantic_input, result


def unit(candidate, ref):
    return next(x for x in candidate['units'] if x['unit_ref'] == ref)


def test_hand_authored_fixture_retains_original_p1_identity():
    request, semantic_input = context()
    assert semantic_input.prepared.request_id == FIXTURE['source_p1_request_ref']
    assert semantic_input.prepared.payload()['control']['source_set_ref'] == FIXTURE['source_set_ref']
    assert semantic_input.receipt.status == 'CANDIDATE_UNREVIEWED'
    assert semantic_input.receipt.adoption_state == 'NOT_ADOPTED'
    assert json.loads(semantic_input.receipt.candidate_json) == FIXTURE['packet']
    result = sem.admit_analysis_semantics(request, semantic_input)
    assert result.decision == 'ADOPTED_PROVISIONAL'
    assert status(result) == 'MEANING_READY'
    assert result.snapshot is not None and result.graph is None and result.artifact is None


def test_all_meaning_groups_scopes_annotations_unknown_and_selections_reach_both_projections():
    request, _, result = generated()
    graph = result.graph.payload(); artifact = result.artifact.payload()
    assert len(graph['nodes']) == 16
    assert len(graph['dependent_scopes']) == 1
    assert len(graph['annotations']) == 1
    assert len(graph['groups']) == 11
    assert len(graph['scope_relations']) == 8
    assert graph['route_edges'] == []
    assert len(graph['unknowns']) == 1 and len(graph['source_selections']) == 4
    assert {x['unit_ref'] for x in graph['nodes']} == {
        x['unit_ref'] for x in FIXTURE['packet']['candidate']['units'] if x['carrier'] == 'GRAPH_NODE'}
    assert all(x['node_kind'] != 'SCENE' for x in graph['nodes'])
    assert all(x['projection_role'] == 'SOURCE_SCOPE_NOT_ROUTE_EDGE' for x in graph['scope_relations'])
    assert graph['unknowns'][0]['origin'] == 'NOT_OBSERVED_IN_MATERIAL'
    assert graph['unknowns'][0]['resolution_state'] == 'NO_USABILITY_ANSWER_IN_MATERIAL'
    assert len(graph['unknowns'][0]['checked_text_fields']) == 6
    assert graph['annotations'][0]['target_unit_refs'] == ['a.make_memo']
    assert artifact['snapshot_ref'] == graph['snapshot_ref'] == result.snapshot.snapshot_ref
    assert artifact['graph_ref'] == graph['graph_ref']
    assert artifact['schema_version'] == 'cocolon.cmee.analysis_semantic_artifact.v1'
    assert artifact['meaning_contract_version'] == 'cocolon.cmee.analysis_candidate_meaning.v1'
    assert not hasattr(result.artifact, 'content_payload')
    visual = artifact['visual_projection_json']
    assert visual['schema_version'] == 'cocolon.cmee.analysis_semantic_visual.v1'
    assert visual['graph_ref'] == graph['graph_ref']
    assert len(visual['nodes']) == 16 and len(visual['groups']) == 11
    assert len(visual['scope_relations']) == 8 and visual['route_edges'] == []
    assert len(visual['dependent_scopes']) == 1 and len(visual['annotations']) == 1
    assert len(visual['unknowns']) == 1 and len(visual['source_selections']) == 4
    sections = artifact['text_sections']
    for raw in FIXTURE['originals']:
        sections_for_record = [x for x in sections if x['source_id'] == raw['id'] and x['section_kind'] != 'MATERIAL_UNKNOWN']
        assert len(sections_for_record) == 1
        assert sections_for_record[0]['text'] == raw['memo'] + '\n' + raw['memo_action']
    text = '\n'.join(x['text'] for x in sections)
    assert '今回の材料には、使いやすさについての回答が記されていない。' in text
    assert '少し面倒だった' in text and '買う物は買えたけど' in text
    assert '前より待つ時間は短かった' in text and '残したかった' in text
    assert 'ほっとした' in text and '聞いていない' in text
    assert '不安' not in text and '平穏' not in text and 'weak' not in text
    selection_traces = [x for x in artifact['realizations'] if x['trace_kind'] == 'RETAINED_SOURCE_SELECTION']
    assert len(selection_traces) == 4
    assert all(all(x[k] is None for k in ('group_ref', 'text_section_index', 'visible_scalar_start', 'visible_scalar_end')) for x in selection_traces)
    assert len(artifact['retained_selection_refs']) == 4
    expected = {(x['source_id'], x['label'], x['strength']) for x in FIXTURE['packet']['candidate']['source_selections']}
    assert {(x['source_id'], x['label'], x['strength']) for x in graph['source_selections']} == expected


@pytest.mark.parametrize('mutation', [
    'owner_as_actor', 'wish_as_completed', 'nonask_affirmed', 'past_as_present',
    'comparison_as_improvement', 'additive_dropped', 'wish_content_dropped',
    'wrong_argument', 'degree_dropped', 'rareru_as_independent_action',
    'nagara_as_cause', 'relation_endpoint', 'relation_marker', 'route_order',
    'unknown_as_person_unknown', 'unknown_target', 'unknown_resolution',
    'unknown_missing_checked_field', 'unknown_checked_field_digest',
    'burden_buy_target', 'burden_current_time', 'burden_degree',
    'selection_missing', 'selection_strength', 'selection_textualized',
    'selection_alias', 'group_scope_truncated', 'missing_unit', 'renamed_duplicate_unit',
    'missing_relation', 'extra_conflict', 'extra_update', 'extra_field',
    'unused_evidence', 'bool_evidence_index', 'wrong_quote',
])
def test_located_quotes_do_not_admit_changed_or_incomplete_meaning(mutation):
    packet = deepcopy(FIXTURE['packet']); candidate = packet['candidate']
    if mutation == 'owner_as_actor': unit(candidate, 'a.role')['actor_binding'] = 'SELF'
    if mutation == 'wish_as_completed': unit(candidate, 'a.intention')['modality'] = 'ASSERTED_AS_WRITTEN'
    if mutation == 'nonask_affirmed': unit(candidate, 'a.non_action')['polarity'] = 'AFFIRMED'
    if mutation == 'past_as_present': unit(candidate, 'a.relief')['temporal_scope'] = 'WRITTEN_CURRENT'
    if mutation == 'comparison_as_improvement': unit(candidate, 'a.relative_wait')['temporal_scope'] = 'PREVIOUS_PERIOD_IMPROVEMENT'
    if mutation == 'additive_dropped': unit(candidate, 'a.role')['qualifiers'].pop()
    if mutation == 'wish_content_dropped': unit(candidate, 'a.intention')['arguments'] = []
    if mutation == 'wrong_argument': unit(candidate, 'a.compare_count')['arguments'][0]['text'] = '返事の数'
    if mutation == 'degree_dropped': unit(candidate, 'a.burden')['qualifiers'].pop()
    if mutation == 'rareru_as_independent_action': unit(candidate, 'a.match_scope')['carrier'] = 'GRAPH_NODE'
    if mutation == 'nagara_as_cause': candidate['scope_relations'][-1]['kind'] = 'CAUSE'
    if mutation == 'relation_endpoint': candidate['scope_relations'][0]['endpoint_unit_refs'][1] = 'a.wait'
    if mutation == 'relation_marker': candidate['scope_relations'][0]['marker_evidence_indexes'] = [0]
    if mutation == 'route_order': candidate['route_edges'] = [{'from': 'a.make_memo', 'to': 'a.buy', 'kind': 'OBSERVED_ORDER'}]
    if mutation == 'unknown_as_person_unknown': candidate['unknowns'][0]['origin'] = 'PERSON_STATED_UNKNOWN'
    if mutation == 'unknown_target': candidate['unknowns'][0]['target_unit_refs'] = ['a.wait']
    if mutation == 'unknown_resolution': candidate['unknowns'][0]['resolution_state'] = 'AWAITING_REPLY'
    if mutation == 'unknown_missing_checked_field': candidate['unknowns'][0]['checked_text_fields'].pop()
    if mutation == 'unknown_checked_field_digest': candidate['unknowns'][0]['checked_text_fields'][0]['field_sha256'] = '0' * 64
    if mutation == 'burden_buy_target': candidate['annotations'][0]['target_unit_refs'] = ['a.buy']
    if mutation == 'burden_current_time': candidate['annotations'][0]['temporal_scope'] = 'CURRENT_SELF_WISH'
    if mutation == 'burden_degree': candidate['annotations'][0]['degree_evidence_indexes'] = []
    if mutation == 'selection_missing': candidate['source_selections'].pop()
    if mutation == 'selection_strength': candidate['source_selections'][0]['strength'] = 'strong'
    if mutation == 'selection_textualized': candidate['source_selections'][-1]['coverage_state'] = 'TEXTUALIZED'
    if mutation == 'selection_alias': candidate['source_selections'][0]['alias_refs'].pop()
    if mutation == 'group_scope_truncated': candidate['sentence_groups'][0]['evidence_indexes'] = [11]
    if mutation == 'missing_unit': candidate['units'].pop()
    if mutation == 'renamed_duplicate_unit':
        duplicate = deepcopy(candidate['units'][0]); duplicate['unit_ref'] = 'a.renamed_duplicate'
        candidate['units'].append(duplicate)
    if mutation == 'missing_relation': candidate['scope_relations'].pop()
    if mutation == 'extra_conflict': candidate['conflicts'] = [{'reason': 'roles_differ'}]
    if mutation == 'extra_update': candidate['updates'] = [{'operation': 'WITHDRAW'}]
    if mutation == 'extra_field': candidate['units'][0]['confidence'] = 1
    if mutation == 'unused_evidence': packet['evidence'].append(deepcopy(packet['evidence'][0]))
    if mutation == 'bool_evidence_index': candidate['units'][0]['evidence_indexes'] = [False]
    if mutation == 'wrong_quote': packet['evidence'][0]['quote'] = '連絡係ではなかった。'
    request, semantic_input = context(packet=packet)
    if mutation != 'wrong_quote':
        assert semantic_input.receipt.status == 'CANDIDATE_UNREVIEWED'
    result = MeaningExperienceEngine().generate(request, semantic_input=semantic_input)
    assert result.decision in ('REJECTED', 'UNSUPPORTED', 'HOLD')
    assert result.snapshot is None and result.graph is None and result.artifact is None


@pytest.mark.parametrize('mutation', [
    'owner', 'period_start', 'period_end', 'member_version',
    'member_owner', 'record_state', 'missing_member', 'source_text', 'source_selection',
    'comparison', 'mode', 'tier', 'profile', 'receipt_request', 'receipt_candidate',
])
def test_request_receipt_and_full_sources_are_rebound(mutation):
    request, semantic_input = context()
    if mutation == 'owner': request = replace(request, authenticated_owner_scope='other-owner')
    if mutation == 'period_start': request = replace(request, period_start='2026-10-08T15:00:00+00:00')
    if mutation == 'period_end': request = replace(request, period_end='2026-10-15T15:00:00+00:00')
    if mutation in ('member_version', 'member_owner', 'record_state'):
        fields = {'member_version': {'saved_record_version': 'sha256:' + '0' * 64},
                  'member_owner': {'owner_scope': 'other-owner'},
                  'record_state': {'record_state': 'DELETED'}}[mutation]
        request = replace(request, members=(replace(request.members[0], **fields),) + request.members[1:])
    if mutation == 'missing_member': request = replace(request, members=request.members[:-1])
    if mutation in ('source_text', 'source_selection'):
        original = json.loads(request.members[0].original_json)
        if mutation == 'source_text': original['memo'] += '回答は使いやすかったということだった。'
        else: original['emotion_details'][0]['strength'] = 'strong'
        first = replace(request.members[0], original_json=canonical(original), saved_record_version=commitment(original))
        request = replace(request, members=(first,) + request.members[1:])
    if mutation == 'comparison': request = replace(request, comparison_previous_request=request)
    if mutation == 'mode': request = replace(request, execution_mode='ANALYSIS_APPLICATION')
    if mutation == 'tier': semantic_input = replace(semantic_input, tier='premium')
    if mutation == 'profile': semantic_input = replace(semantic_input, semantic_profile='piece_candidate_snapshot.v1')
    if mutation == 'receipt_request': semantic_input = replace(semantic_input, receipt=replace(semantic_input.receipt, request_id='other'))
    if mutation == 'receipt_candidate': semantic_input = replace(semantic_input, receipt=replace(semantic_input.receipt, candidate_json='{}'))
    result = MeaningExperienceEngine().generate(request, semantic_input=semantic_input)
    assert result.decision in ('REJECTED', 'UNSUPPORTED', 'HOLD')
    assert result.snapshot is None and result.graph is None and result.artifact is None


def test_unreviewed_answer_cannot_be_silently_dropped_from_new_profile():
    request, semantic_input = context()
    first = request.members[0]
    supplement = AnalysisSupplement('saved-answer', first.owner_scope, first.saved_record_ref,
        first.saved_record_version, '使いやすかったと聞いた。', commitment('使いやすかったと聞いた。'))
    request = replace(request, members=(replace(first, supplements=(supplement,)),) + request.members[1:])
    prepared = prepare_analysis(request, tier='plus')
    receipt = receive_candidate(prepared, request_id=prepared.request_id,
        raw_output=semantic_input.receipt.raw_output, finish_reason='stop')
    result = sem.generate_analysis_semantic(request, sem.AnalysisSemanticInputV1(prepared, receipt, tier='plus'))
    assert result.decision in ('UNSUPPORTED', 'HOLD') and result.snapshot is None


@pytest.mark.parametrize('finish', ['timeout', 'length', 'error', 'unexpected'])
def test_provider_failure_cannot_become_adoption(finish):
    request, semantic_input = context()
    receipt = receive_candidate(semantic_input.prepared, request_id=semantic_input.prepared.request_id,
        raw_output=semantic_input.receipt.raw_output, finish_reason=finish)
    result = sem.generate_analysis_semantic(request, replace(semantic_input, receipt=receipt))
    assert result.decision == 'HOLD' and result.snapshot is None and result.artifact is None


def test_new_fresh_route_never_calls_legacy_parser_or_safe_projection():
    paths = [
        (compiler, '_proposition'), (compiler, '_parsed_proposition'),
        (compiler, 'compile_observed_graph'), (realizer, '_safe_label'),
        (realizer.ObservedSelfStructureMap, '_text_from_visual'),
    ]
    with ExitStack() as stack:
        mocks = [stack.enter_context(patch.object(module, name, side_effect=AssertionError(name))) for module, name in paths]
        generated()
        for mock in mocks: mock.assert_not_called()


def test_meaning_snapshot_is_deeply_detached_from_payload_and_prepared_views():
    request, semantic_input, result = generated()
    before = result.snapshot.payload()
    detached = result.snapshot.payload(); detached['candidate_packet'] = '{}'
    source_view = semantic_input.prepared.payload(); source_view['sources'][0]['original']['emotions'].append('喜び')
    assert result.snapshot.payload() == before
    sem.validate_analysis_snapshot(request, result.snapshot, tier='plus')


def test_reviewed_constructions_are_not_authorized_by_fixture_record_ids_or_hashes():
    renamed = {'A02-4': 'renamed-contact', 'A02-5': 'renamed-tools', 'A02-6': 'renamed-shopping'}
    rows = deepcopy(FIXTURE['originals'])
    for raw in rows: raw['id'] = renamed[raw['id']]
    request, old_input = context(originals=rows, owner='another-synthetic-owner')

    def renamed_value(value):
        if type(value) is dict: return {k: renamed_value(v) for k, v in value.items()}
        if type(value) is list: return [renamed_value(v) for v in value]
        if type(value) is str:
            for old, new in renamed.items(): value = value.replace(old, new)
        return value

    packet = renamed_value(deepcopy(FIXTURE['packet']))
    packet['candidate']['unknowns'][0]['checked_source_set_ref'] = old_input.prepared.payload()['control']['source_set_ref']
    by_id = {raw['id']: raw for raw in rows}
    for selection in packet['candidate']['source_selections']:
        selection['source_commitment'] = commitment(by_id[selection['source_id']])
    receipt = receive_candidate(old_input.prepared, request_id=old_input.prepared.request_id,
        raw_output=canonical(packet), finish_reason='stop')
    result = sem.generate_analysis_semantic(request, replace(old_input, receipt=receipt))
    assert result.decision == 'ADOPTED_PROVISIONAL' and status(result) == 'GENERATED'
    assert result.request_ref != FIXTURE['source_p1_request_ref']
    assert result.snapshot.payload()['source_set_ref'] != FIXTURE['source_set_ref']
    assert {x['source_id'] for x in result.artifact.payload()['text_sections']} == set(renamed.values())


@pytest.mark.parametrize('mutation', [
    'polarity', 'polarity_and_binding', 'unknown_origin', 'annotation_target',
    'bool_admission_version', 'bool_adapter_version', 'extra_key',
    'binding_actor', 'binding_scalar', 'binding_carrier',
])
def test_rehashed_saved_snapshot_cannot_self_certify_changed_meaning(mutation):
    request, semantic_input = context()
    meaning = sem.admit_analysis_semantics(request, semantic_input)
    state = json.loads(sem.serialize_analysis_semantic_state(request, meaning, tier='plus'))
    snapshot = state['snapshot']; candidate = snapshot['candidate_packet']['candidate']
    if mutation in ('polarity', 'polarity_and_binding'):
        unit(candidate, 'a.non_action')['polarity'] = 'AFFIRMED'
        if mutation == 'polarity_and_binding':
            next(x for x in snapshot['unit_bindings'] if x['unit_ref'] == 'a.non_action')['claim_json']['polarity'] = 'AFFIRMED'
    if mutation == 'unknown_origin': candidate['unknowns'][0]['origin'] = 'PERSON_STATED_UNKNOWN'
    if mutation == 'annotation_target': candidate['annotations'][0]['target_unit_refs'] = ['a.buy']
    if mutation == 'bool_admission_version': snapshot['admission_version'] = True
    if mutation == 'bool_adapter_version': snapshot['adapter_version'] = True
    if mutation == 'extra_key': snapshot['confidence'] = 1
    if mutation == 'binding_actor': snapshot['unit_bindings'][0]['claim_json']['actor_binding'] = 'SELF'
    if mutation == 'binding_scalar': snapshot['unit_bindings'][0]['source_binding_json']['scalar_start'] = 1
    if mutation == 'binding_carrier': snapshot['unit_bindings'][0]['carrier'] = 'DEPENDENT_SCOPE'
    material = {k: v for k, v in snapshot.items() if k != 'snapshot_ref'}
    snapshot['snapshot_ref'] = 'analysis-semantic-snapshot:' + hashlib.sha256(canonical(material).encode()).hexdigest()
    with pytest.raises(sem.AnalysisSemanticError):
        sem.reload_analysis_semantic_state(request, canonical(state), tier='plus')


@pytest.mark.parametrize('field', ['unit_bindings', 'period'])
def test_snapshot_frozen_shell_cannot_hold_mutable_lists(field):
    request, semantic_input = context()
    meaning = sem.admit_analysis_semantics(request, semantic_input)
    snapshot = replace(meaning.snapshot, **{field: list(getattr(meaning.snapshot, field))})
    with pytest.raises(sem.AnalysisSemanticError):
        sem.validate_analysis_snapshot(request, snapshot, tier='plus')


@pytest.mark.parametrize('mutation', [
    'node_polarity', 'node_kind', 'node_label', 'duplicate_node', 'missing_dependent',
    'relation_cause', 'relation_target', 'unknown_origin', 'annotation_target',
    'selection_strength', 'group_text', 'route_edge', 'bool_scalar',
])
def test_rehashed_private_graph_cannot_change_adopted_meaning(mutation):
    request, semantic_input = context()
    meaning = sem.admit_analysis_semantics(request, semantic_input)
    graph = compiler.compile_semantic_graph(meaning.snapshot)
    state = json.loads(sem.serialize_analysis_semantic_state(request, replace(meaning, graph=graph), tier='plus'))
    payload = state['graph']
    if mutation == 'node_polarity': payload['nodes'][0]['claim_json']['polarity'] = 'NEGATED'
    if mutation == 'node_kind': payload['nodes'][0]['node_kind'] = 'SCENE'
    if mutation == 'node_label': payload['nodes'][0]['visible_label'] = 'いつも連絡係を任される性格だった。'
    if mutation == 'duplicate_node':
        row = deepcopy(payload['nodes'][0]); row['node_ref'] = 'renamed-node'
        payload['nodes'].append(row)
    if mutation == 'missing_dependent': payload['dependent_scopes'] = []
    if mutation == 'relation_cause': payload['scope_relations'][0]['kind'] = 'CAUSE'
    if mutation == 'relation_target': payload['scope_relations'][0]['endpoint_unit_refs'][-1] = 'a.buy'
    if mutation == 'unknown_origin': payload['unknowns'][0]['origin'] = 'PERSON_STATED_UNKNOWN'
    if mutation == 'annotation_target': payload['annotations'][0]['target_unit_refs'] = ['a.buy']
    if mutation == 'selection_strength': payload['source_selections'][0]['strength'] = 'strong'
    if mutation == 'group_text': payload['groups'][0]['original_text'] = '今日も連絡係ではなかった。'
    if mutation == 'route_edge': payload['route_edges'] = [{'kind': 'REPEATED_COOCCURRENCE'}]
    if mutation == 'bool_scalar': payload['nodes'][0]['source_binding_json']['scalar_start'] = False
    material = {k: v for k, v in payload.items() if k != 'graph_ref'}
    payload['graph_ref'] = 'analysis-semantic-graph:' + hashlib.sha256(canonical(material).encode()).hexdigest()
    with pytest.raises(sem.AnalysisSemanticError):
        sem.reload_analysis_semantic_state(request, canonical(state), tier='plus')


@pytest.mark.parametrize('mutation', [
    'text_polarity', 'text_missing_record', 'text_add_selected_feeling', 'text_unknown',
    'visual_missing_node', 'visual_scope_cause', 'visual_unknown_origin',
    'visual_annotation_target', 'trace_target', 'trace_bool_range', 'selection_visible',
    'missing_selection_trace', 'retained_selection_missing', 'extra_key',
])
def test_rehashed_completed_artifact_cannot_change_one_surface_or_coverage(mutation):
    request, _, original = generated()
    state = json.loads(sem.serialize_analysis_semantic_state(request, original, tier='plus'))
    artifact = state['artifact']; visual = artifact['visual_projection_json']
    if mutation == 'text_polarity': artifact['text_sections'][1]['text'] = artifact['text_sections'][1]['text'].replace('聞いていない', '聞いた')
    if mutation == 'text_missing_record': artifact['text_sections'].pop(0)
    if mutation == 'text_add_selected_feeling': artifact['text_sections'][2]['text'] += '不安もあった。'
    if mutation == 'text_unknown': artifact['text_sections'][-1]['text'] = '使いやすかったか、本人にもわからない。'
    if mutation == 'visual_missing_node': visual['nodes'].pop()
    if mutation == 'visual_scope_cause': visual['scope_relations'][0]['kind'] = 'CAUSE'
    if mutation == 'visual_unknown_origin': visual['unknowns'][0]['origin'] = 'PERSON_STATED_UNKNOWN'
    if mutation == 'visual_annotation_target': visual['annotations'][0]['target_unit_refs'] = ['a.buy']
    if mutation == 'trace_target': artifact['realizations'][0]['visual_ref'] = visual['nodes'][1]['node_ref']
    if mutation == 'trace_bool_range': artifact['realizations'][0]['visible_scalar_start'] = False
    if mutation == 'selection_visible':
        trace = next(x for x in artifact['realizations'] if x['trace_kind'] == 'RETAINED_SOURCE_SELECTION')
        trace.update(text_section_index=0, visible_scalar_start=0, visible_scalar_end=2)
    if mutation == 'missing_selection_trace': artifact['realizations'] = [x for x in artifact['realizations'] if x['trace_kind'] != 'RETAINED_SOURCE_SELECTION']
    if mutation == 'retained_selection_missing': artifact['retained_selection_refs'].pop()
    if mutation == 'extra_key': artifact['confidence'] = 1
    material = {k: v for k, v in artifact.items() if k not in ('artifact_ref', 'content_hash')}
    artifact['content_hash'] = 'sha256:' + hashlib.sha256(canonical(material).encode()).hexdigest()
    identity = [artifact['content_hash'], artifact['schema_version'], artifact['semantic_profile'],
                artifact['snapshot_ref'], artifact['graph_ref']]
    artifact['artifact_ref'] = 'analysis-semantic-artifact:' + hashlib.sha256(canonical(identity).encode()).hexdigest()
    with pytest.raises(sem.AnalysisSemanticError):
        sem.reload_analysis_semantic_state(request, canonical(state), tier='plus')


def test_private_meaning_graph_and_complete_roundtrips(tmp_path):
    request, semantic_input = context()
    meaning = sem.admit_analysis_semantics(request, semantic_input)
    graph = compiler.compile_semantic_graph(meaning.snapshot)
    graph_result = replace(meaning, graph=graph)
    complete = sem.generate_analysis_semantic(request, semantic_input)
    for label, original in [('meaning', meaning), ('graph', graph_result), ('complete', complete)]:
        path = tmp_path / (label + '.json')
        path.write_text(sem.serialize_analysis_semantic_state(request, original, tier='plus'))
        with patch.object(compiler, 'compile_semantic_graph', side_effect=AssertionError('compiler')) as comp, \
             patch.object(realizer, 'realize_semantic_graph', side_effect=AssertionError('author')) as author:
            restored = sem.reload_analysis_semantic_state(request, path.read_text(), tier='plus')
        comp.assert_not_called(); author.assert_not_called()
        assert restored.snapshot.payload() == original.snapshot.payload()
        assert (restored.graph.payload() if restored.graph else None) == (original.graph.payload() if original.graph else None)
        assert (restored.artifact.payload() if restored.artifact else None) == (original.artifact.payload() if original.artifact else None)


def test_actual_author_failure_after_meaning_save_resumes_same_file(tmp_path):
    request, semantic_input = context()
    meaning = sem.admit_analysis_semantics(request, semantic_input)
    path = tmp_path / 'meaning-before-author.json'
    path.write_text(sem.serialize_analysis_semantic_state(request, meaning, tier='plus'))

    def author_failure(*args, **kwargs):
        assert path.is_file()
        assert json.loads(path.read_text())['snapshot'] is not None
        raise RuntimeError('actual author failure after private meaning save')

    with patch.object(realizer, 'realize_semantic_graph', side_effect=author_failure) as author:
        failed = sem.resume_analysis_semantics(request, path.read_text(), tier='plus')
    author.assert_called_once()
    assert failed.decision == 'ADOPTED_PROVISIONAL' and status(failed) == 'UNAVAILABLE'
    assert failed.snapshot.payload() == meaning.snapshot.payload() and failed.artifact is None
    with patch.object(sem, 'admit_analysis_semantics', side_effect=AssertionError('re-admission')) as admission, \
         patch.object(sem, 'receive_candidate', side_effect=AssertionError('candidate alias')) as receive_alias, \
         patch('cocolon_meaning_experience_engine.preparation.receive_candidate', side_effect=AssertionError('candidate')) as receive:
        resumed = sem.resume_analysis_semantics(request, path.read_text(), tier='plus')
    admission.assert_not_called(); receive_alias.assert_not_called(); receive.assert_not_called()
    assert status(resumed) == 'GENERATED' and resumed.snapshot.payload() == meaning.snapshot.payload()
    assert path.read_text() == sem.serialize_analysis_semantic_state(request, meaning, tier='plus')


def test_completed_private_reload_does_not_fetch_adopt_compile_or_author(tmp_path):
    request, _, original = generated()
    path = tmp_path / 'complete.json'
    path.write_text(sem.serialize_analysis_semantic_state(request, original, tier='plus'))
    with ExitStack() as stack:
        targets = [(sem, 'admit_analysis_semantics'), (sem, 'receive_candidate'), (compiler, 'compile_semantic_graph'),
                   (realizer, 'realize_semantic_graph')]
        mocks = [stack.enter_context(patch.object(module, name, side_effect=AssertionError(name))) for module, name in targets]
        receive = stack.enter_context(patch('cocolon_meaning_experience_engine.preparation.receive_candidate', side_effect=AssertionError('fetch')))
        replay = sem.resume_analysis_semantics(request, path.read_text(), tier='plus')
        for mock in mocks + [receive]: mock.assert_not_called()
    assert replay.snapshot.payload() == original.snapshot.payload()
    assert replay.graph.payload() == original.graph.payload()
    assert replay.artifact.payload() == original.artifact.payload()


@pytest.mark.parametrize('mutation', ['extra_key', 'schema', 'no_snapshot', 'no_graph', 'owner', 'request', 'tier', 'period', 'member'])
def test_private_state_rejects_unknown_shape_and_foreign_binding(mutation):
    request, _, original = generated()
    state = json.loads(sem.serialize_analysis_semantic_state(request, original, tier='plus'))
    if mutation == 'extra_key': state['extra'] = True
    if mutation == 'schema': state['schema_version'] = 'watashi.map.v2'
    if mutation == 'no_snapshot': state['snapshot'] = None
    if mutation == 'no_graph': state['graph'] = None
    if mutation == 'owner': request = replace(request, authenticated_owner_scope='other-owner')
    if mutation == 'request': request = replace(request, request_id='other-operation')
    if mutation == 'period': request = replace(request, period_end='2026-10-15T15:00:00+00:00')
    if mutation == 'member': request = replace(request, members=request.members[:-1])
    with pytest.raises(sem.AnalysisSemanticError):
        sem.reload_analysis_semantic_state(request, canonical(state), tier='premium' if mutation == 'tier' else 'plus')

