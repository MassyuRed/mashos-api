"""Offline private input composition; every response below is synthetic."""
import copy
from dataclasses import asdict, replace
import json
from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest

import analysis_cumulative_service as service
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as semantic
from cocolon_meaning_experience_engine.cores.analysis import observed_route_realizer as author
from cocolon_meaning_experience_engine.cores.analysis.source_adapter import AnalysisSupplement, commitment
from test_analysis_cumulative import OWNER, source_snapshot
from test_analysis_model_quoted_parent_units import call


PROFILES = ('selected_material.v4', 'selected_material.v7')


def snapshot(count):
    snap = source_snapshot(count)
    for member in snap['members']:
        member['original'].update(memo='私は本を見た。', memo_action='')
    return snap


def packet(prepared):
    """Author this fixture for its own fields; never transform stored raw."""
    return dict(fields=[dict(field=f['field'], units=[dict(quote=f['text'].rstrip('。'),
        node_kind='ROLE' if 'の役割は' in f['text'] else 'ACTION_OR_NONACTION',
        parent_quote=None, scope_role=None, qualifiers=[] if 'なかった' not in f['text'] else
            [dict(kind='NEGATION', quote='なかった')])])
        for f in json.loads(prepared.messages()[1]['content'])['fields']])


def measure(prepared):
    body = json.loads(prepared.messages()[1]['content'])
    # Count complete nonempty occasions, leaving fieldless metadata with its
    # neighbouring record. This is a test counter, not tokenizer evidence.
    occasions = sum(bool(r['fields']) for r in body['records'])
    return service.AnalysisModelInputBudget(3000+2000*occasions, 1000)


def inputs(snap, profile='selected_material.v4'):
    plan = service.prepare_cumulative_model_batches(OWNER, snap,
        prompt_version=profile, measure_budget=measure)
    return semantic.AnalysisModelObservedBatchInput(plan.parent,
        tuple(call(child, packet(child)) for child in plan.batches))


def compare_maps(left, right):
    if left is None or right is None:
        assert left is right
        return
    assert left.graph == right.graph
    assert left.source_set_ref == right.source_set_ref
    assert left.source_members == right.source_members and left.category_records == right.category_records
    assert left.period == right.period and left.owner_scope == right.owner_scope
    a = left.safe_text_projection(authenticated_owner_scope=OWNER)
    b = right.safe_text_projection(authenticated_owner_scope=OWNER)
    a.pop('projection_of'); b.pop('projection_of')
    assert a == b
    a = left.safe_projection(authenticated_owner_scope=OWNER)
    b = right.safe_projection(authenticated_owner_scope=OWNER)
    a.pop('projection_of'); b.pop('projection_of')
    assert a == b


@pytest.mark.parametrize('profile', PROFILES)
def test_201_independent_inputs_match_one_complete_synthetic_response_exactly(profile):
    snap = snapshot(201)
    original = copy.deepcopy(snap)
    value = inputs(snap, profile)
    assert len(value.batches) == 201
    raw = tuple(c.response.raw for c in value.batches)
    # The large single packet is only a logical CPU oracle. It does not claim
    # that a real 2048-token response or one 60-second acquisition could fit it.
    single = call(value.parent, packet(value.parent))
    expected, expected_counts = service.build_cumulative_map(OWNER, snap, model_input=single)
    with patch.object(service, '_rpc', AsyncMock(side_effect=AssertionError('offline RPC'))):
        actual, counts = service.build_cumulative_model_batch_map(OWNER, snap, model_input=value)
        service._rpc.assert_not_called()
    compare_maps(expected, actual)
    assert counts == expected_counts
    assert counts['source_count'] == counts['processed_count'] == counts['mapped_count'] == 201
    assert counts['unparsed_count'] == 0 and len(actual.graph.nodes[0].record_refs) == 201
    assert tuple(c.response.raw for c in value.batches) == raw and snap == original
    _, child_fields, _ = semantic._admit_quoted_parent_units(value.batches[-1].request, value.batches[-1])
    _, whole_fields, _ = semantic._admit_quoted_parent_units(single.request, single)
    assert child_fields[0].field == 1 and whole_fields[-1].field == 201
    assert child_fields[0].field_ref == whole_fields[-1].field_ref
    assert child_fields[0].evidence == whole_fields[-1].evidence


@pytest.mark.parametrize('profile', PROFILES)
def test_other_unsupported_fieldless_categories_and_one_global_unread_marker(profile):
    snap = snapshot(7)
    snap['members'][2]['original']['memo'] = '父は僕の本を見た。'
    snap['members'][3]['original']['memo'] = 'ふと気になったことを、まだ言葉にできません。'
    snap['members'][4]['original']['memo'] = ''
    snap['members'][5]['original']['memo'] = '私の本を見なかった。'
    snap['members'][6]['original']['category'] = ['家']
    value = inputs(snap, profile)
    single = call(value.parent, packet(value.parent))
    expected, expected_counts = service.build_cumulative_map(OWNER, snap, model_input=single)
    actual, counts = service.build_cumulative_model_batch_map(OWNER, snap, model_input=value)
    compare_maps(expected, actual)
    assert counts == expected_counts and counts['source_count'] == 7
    represented = {r for n in actual.graph.nodes for r in n.record_refs}
    assert all(snap['members'][i]['original']['id'] not in represented for i in (2,3,4))
    assert actual.graph.unknown_gaps[-1].missing_scope == 'SOURCE_SCOPE'
    assert actual.graph.unknown_gaps[-1].between_node_refs == (actual.graph.nodes[0].node_ref,)
    assert len(actual.source_members) == 7


@pytest.mark.parametrize('profile', PROFILES)
def test_both_fields_and_three_answers_stay_one_complete_occasion(profile, monkeypatch):
    snap = snapshot(2)
    snap['members'][0]['original']['memo_action'] = '私は費用を記録した。'
    base = service._cumulative_model_request(OWNER, snap)
    first = base.members[0]
    texts = ('僕は資料を見た。', '僕は費用を記録した。', '僕は日程を決めなかった。')
    answers = tuple(AnalysisSupplement(str(UUID(int=800+i)), OWNER, first.saved_record_ref,
        first.saved_record_version, text, commitment(text)) for i, text in enumerate(texts))
    request = replace(base, members=(replace(first, supplements=answers), base.members[1]))
    monkeypatch.setattr(service, '_cumulative_model_request', lambda *_:request)
    value = inputs(snap, profile)
    assert len(value.batches) == 2 and value.batches[0].request.members == request.members[:1]
    assert value.batches[0].request.members[0].supplements == answers
    assert len(json.loads(value.batches[0].messages()[1]['content'])['fields']) == 5
    expected, expected_counts = service.build_cumulative_map(OWNER, snap,
        model_input=call(value.parent, packet(value.parent)))
    actual, counts = service.build_cumulative_model_batch_map(OWNER, snap, model_input=value)
    compare_maps(expected, actual)
    assert counts == expected_counts and counts['source_count'] == counts['processed_count'] == 2


@pytest.mark.parametrize('profile', PROFILES)
def test_input_roundtrip_does_not_acquire_compile_author_or_read_a_saved_map(profile, monkeypatch):
    snap = snapshot(3)
    value = inputs(snap, profile)
    def forbidden(*_args, **_kwargs):
        raise AssertionError('input roundtrip must not compile or realize')
    with monkeypatch.context() as scoped:
        scoped.setattr(semantic, '_compile_model_observed_record', forbidden)
        scoped.setattr(semantic, '_realize_model_observed_records', forbidden)
        scoped.setattr(author, 'realize_observed_graph', forbidden)
        scoped.setattr(service, '_rpc', forbidden)
        scoped.setattr(service, '_model_response', forbidden)
        raw = service.serialize_cumulative_model_batch_input(OWNER, snap, model_input=value)
        restored = service.reload_cumulative_model_batch_input(OWNER, snap, raw, prompt_version=profile)
    assert restored == value
    state = json.loads(raw)
    assert set(state) == {'schema_version', 'parent', 'batches'}
    assert all(row['response'] == asdict(child.response) for row, child in zip(state['batches'], value.batches))
    expected, counts = service.build_cumulative_model_batch_map(OWNER, snap, model_input=value)
    actual, after_counts = service.build_cumulative_model_batch_map(OWNER, snap, model_input=restored)
    compare_maps(expected, actual)
    assert after_counts == counts


@pytest.mark.parametrize('profile', PROFILES)
def test_split_written_roles_pair_and_clause_keep_per_record_proofs(profile):
    snap = snapshot(4)
    role = '僕の役割は受付係だった。'
    snap['members'][0]['original']['memo'] = role
    snap['members'][1]['original'].update(memo=role, memo_action='僕は費用を記録した。')
    snap['members'][2]['original']['memo'] = role+'費用を記録した。'
    plan = service.prepare_cumulative_model_batches(OWNER, snap, prompt_version=profile, measure_budget=measure)
    def role_packet(prepared):
        return dict(fields=[dict(field=f['field'], units=[dict(quote=text,
            node_kind='ROLE' if 'の役割は' in text else 'ACTION_OR_NONACTION',
            parent_quote=None, scope_role=None, qualifiers=[])
            for text in f['text'].rstrip('。').split('。')])
            for f in json.loads(prepared.messages()[1]['content'])['fields']])
    value = semantic.AnalysisModelObservedBatchInput(plan.parent,
        tuple(call(child, role_packet(child)) for child in plan.batches))
    expected, counts = service.build_cumulative_map(OWNER, snap,
        model_input=call(plan.parent, role_packet(plan.parent)))
    actual, after_counts = service.build_cumulative_model_batch_map(OWNER, snap, model_input=value)
    compare_maps(expected, actual)
    assert after_counts == counts and counts['mapped_count'] == 4 and counts['unparsed_count'] == 1
    assert sum(n.node_kind == 'ROLE' for n in actual.graph.nodes) == 3


@pytest.mark.parametrize('defect', ['missing', 'duplicate', 'reordered', 'partial', 'parent_response',
    'stale_guard', 'foreign_owner', 'profile', 'child_period', 'child_member'])
def test_invalid_batch_envelopes_never_compile_or_return_a_partial_map(defect, monkeypatch):
    snap = snapshot(3)
    value = inputs(snap)
    first = value.batches[0]
    if defect == 'missing': value = replace(value, batches=value.batches[:-1])
    elif defect == 'duplicate': value = replace(value, batches=(first, first, value.batches[-1]))
    elif defect == 'reordered': value = replace(value, batches=tuple(reversed(value.batches)))
    elif defect == 'partial': value = replace(value, batches=(replace(first, response=None), *value.batches[1:]))
    elif defect == 'parent_response': value = replace(value, parent=call(value.parent, packet(value.parent)))
    elif defect == 'stale_guard': value = replace(value, parent=replace(value.parent, source_guard='analysis-db-cumulative-v1:'+'b'*64))
    elif defect == 'foreign_owner': value = replace(value, parent=replace(value.parent,
        request=replace(value.parent.request, authenticated_owner_scope=str(UUID(int=2)))))
    elif defect == 'profile': value = replace(value, batches=(replace(first, prompt_version='selected_material.v7'), *value.batches[1:]))
    elif defect == 'child_period': value = replace(value, batches=(replace(first,
        request=replace(first.request, period_end='2026-11-02T08:00:00+00:00')), *value.batches[1:]))
    elif defect == 'child_member': value = replace(value, batches=(replace(first,
        request=replace(first.request, members=(replace(first.request.members[0], original_json='{}'),))), *value.batches[1:]))
    monkeypatch.setattr(semantic, '_compile_model_observed_record',
        lambda *_:(_ for _ in ()).throw(AssertionError('invalid input reached compiler')))
    with pytest.raises(ValueError):
        service.build_cumulative_model_batch_map(OWNER, snap, model_input=value)


@pytest.mark.parametrize('defect', ['raw', 'raw_hash', 'messages_hash', 'request_ref', 'finish', 'row_request_ref',
    'missing', 'duplicate', 'reordered', 'foreign_record', 'parent_guard', 'parent_profile', 'parent_owner',
    'outer_artifact', 'outer_graph', 'outer_coverage', 'child_artifact', 'parent_extra', 'response_extra'])
def test_input_state_rejects_tampering_and_any_saved_map_claim(defect):
    snap = snapshot(3)
    value = inputs(snap)
    state = json.loads(service.serialize_cumulative_model_batch_input(OWNER, snap, model_input=value))
    response = state['batches'][0]['response']
    if defect == 'raw': response['raw'] += ' '
    elif defect == 'raw_hash': response['raw_sha256'] = '0'*64
    elif defect == 'messages_hash': response['messages_sha256'] = '0'*64
    elif defect == 'request_ref': response['request_ref'] = value.parent.request_ref
    elif defect == 'finish': response['finish_reason'] = 'length'
    elif defect == 'row_request_ref': state['batches'][0]['request_ref'] = value.parent.request_ref
    elif defect == 'missing': state['batches'].pop()
    elif defect == 'duplicate': state['batches'][1] = copy.deepcopy(state['batches'][0])
    elif defect == 'reordered': state['batches'].reverse()
    elif defect == 'foreign_record': state['batches'][0]['record_refs'] = [str(UUID(int=9999))]
    elif defect == 'parent_guard': state['parent']['source_guard'] = 'analysis-db-cumulative-v1:'+'b'*64
    elif defect == 'parent_profile': state['parent']['prompt_version'] = 'selected_material.v7'
    elif defect == 'parent_owner': state['parent']['owner_scope'] = str(UUID(int=2))
    elif defect.startswith('outer_'): state[defect[6:]] = {}
    elif defect == 'child_artifact': state['batches'][0]['artifact'] = {}
    elif defect == 'parent_extra': state['parent']['graph'] = {}
    elif defect == 'response_extra': response['artifact'] = {}
    with pytest.raises(ValueError):
        service.reload_cumulative_model_batch_input(OWNER, snap, semantic.canonical(state))


@pytest.mark.parametrize('change', ['guard', 'record', 'owner', 'profile'])
def test_input_state_cannot_rebind_to_a_changed_caller_snapshot_or_profile(change):
    snap = snapshot(2)
    value = inputs(snap)
    raw = service.serialize_cumulative_model_batch_input(OWNER, snap, model_input=value)
    changed = copy.deepcopy(snap)
    owner, profile = OWNER, PROFILES[0]
    if change == 'guard': changed['guard'] = 'analysis-db-cumulative-v1:'+'b'*64
    elif change == 'record': changed['members'][0]['original']['memo'] = '私は資料を見た。'
    elif change == 'owner': owner = str(UUID(int=2))
    elif change == 'profile': profile = PROFILES[1]
    with pytest.raises(ValueError):
        service.reload_cumulative_model_batch_input(owner, changed, raw, prompt_version=profile)


@pytest.mark.parametrize('profile', ['baseline.v1', 'selected_categories.v1', 'selected_material.v2',
    'selected_material.v3', 'selected_material.v4', 'selected_material.v6', 'selected_material.v7',
    'semantic_boundaries.v2', 'semantic_boundaries.v3'])
def test_legacy_single_record_branch_keeps_exact_graph_and_original_input_bytes(profile):
    snap = snapshot(1)
    prepared = service.prepare_cumulative_category_units(OWNER, snap, prompt_version=profile)
    messages = prepared.messages()
    value = call(prepared, packet(prepared))
    frozen, fields, _ = semantic._admit_quoted_parent_units(value.request, value)
    expected = semantic._compile_model_observed_record(frozen, fields)
    actual, mapped, unread = semantic.generate_analysis_model_observed_actions(value.request, value,
        with_record_counts=True)
    assert actual.graph == expected and mapped == 1 and unread == 0
    assert prepared.messages() == messages and value.response == call(prepared, packet(prepared)).response


def test_one_unsplit_envelope_and_no_supported_record_match_existing_behavior():
    snap = snapshot(1)
    snap['members'][0]['original']['memo'] = '父は僕の本を見た。'
    value = inputs(snap)
    assert len(value.batches) == 1 and value.batches[0].request == value.parent.request
    expected, counts = service.build_cumulative_map(OWNER, snap, model_input=value.batches[0])
    actual, after_counts = service.build_cumulative_model_batch_map(OWNER, snap, model_input=value)
    assert expected is actual is None and after_counts == counts and counts['unparsed_count'] == 1


@pytest.mark.parametrize('profile', PROFILES)
def test_unsplit_unordered_parent_keeps_exact_child_input_and_canonical_partition(profile):
    snap = snapshot(2)
    snap['members'].reverse()
    plan = service.prepare_cumulative_model_batches(OWNER, snap, prompt_version=profile,
        measure_budget=lambda _:service.AnalysisModelInputBudget(3000,1000))
    assert plan.batches == (plan.parent,)
    value = semantic.AnalysisModelObservedBatchInput(plan.parent, (call(plan.parent, packet(plan.parent)),))
    raw = service.serialize_cumulative_model_batch_input(OWNER, snap, model_input=value)
    restored = service.reload_cumulative_model_batch_input(OWNER, snap, raw, prompt_version=profile)
    assert restored == value and restored.batches[0].request.members == plan.parent.request.members
    expected, counts = service.build_cumulative_map(OWNER, snap, model_input=value.batches[0])
    actual, after_counts = service.build_cumulative_model_batch_map(OWNER, snap, model_input=restored)
    compare_maps(expected, actual)
    assert after_counts == counts
    state = json.loads(raw)
    state['batches'][0]['record_refs'].reverse()
    with pytest.raises(ValueError):
        service.reload_cumulative_model_batch_input(OWNER, snap, semantic.canonical(state), prompt_version=profile)
