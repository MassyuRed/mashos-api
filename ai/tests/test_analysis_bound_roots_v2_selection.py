"""Selection-first ordering is a private author constraint, not meaning proof."""
from copy import deepcopy
import json

import pytest

import analysis_model_source as sources
import analysis_if_model_source as if_sources
import analysis_semantic_map as app
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from test_analysis_cumulative import OWNER
from test_analysis_node_local_native_profile import accepts
from test_emlis_natural_reply_probe_http import probe
import test_analysis_node_local_v4_phases as old
import test_analysis_node_local_bound_roots as bound
from test_analysis_event_plan_model_alias import environment

PROFILE = core.SEMANTIC_MAP_NODE_LOCAL_V4_BOUND_V2_PROFILE
ALIAS = sources.SEMANTIC_NODE_LOCAL_V4_BOUND_V2_MODEL
SCHEMA = core.SEMANTIC_MAP_NODE_LOCAL_V4_BOUND_V2_SCHEMA
original_packets = old.phase_packets
original_generated = old.generated_phase_values
original_artifact = old.artifact


def prepared():
    return app.prepare_semantic_map(OWNER,
        json.loads(old.prepared().source_snapshot_json), prompt_version=PROFILE)


def select_first(values):
    plan, nodes, relations = bound.prefixed(values)
    overview = relations['overview']
    relations['overview'] = dict(node_refs=overview['node_refs'], title=overview['title'])
    return plan, nodes, relations


def phase_packets(p):
    return select_first(original_packets(p))


def artifact(p, values=None):
    result = original_artifact(p, phase_packets(p) if values is None else values)
    result['schema_version'] = SCHEMA
    return result


def test_exact_private_alias_routes_and_if_keeps_original_adapter(monkeypatch):
    settings = environment(monkeypatch, model=ALIAS)
    source = sources.application_analysis_model_source()
    assert sources.analysis_model_prompt_version(source) == PROFILE
    assert source._settings == settings
    if_source = if_sources.application_analysis_if_model_source()
    assert if_source._settings_snapshot == settings
    assert if_source.model == sources.SEMANTIC_EVENT_PLAN_BASE_MODEL


def test_overview_selects_real_node_refs_before_free_title_only_in_v2():
    p = prepared()
    plan, nodes, relations = phase_packets(p)
    selected = core.semantic_node_local_v4_messages(p, 'RELATIONS', plan=plan, nodes=nodes)
    schema = probe.semantic_output_schema(selected)
    assert list(schema['properties']['overview']['properties']) == ['node_refs', 'title']
    assert accepts(relations, selected)
    reversed_value = deepcopy(relations)
    overview = reversed_value['overview']
    reversed_value['overview'] = dict(title=overview['title'], node_refs=overview['node_refs'])
    assert not accepts(reversed_value, selected)
    legacy = bound.prepared()
    old_plan, old_nodes, old_rel = bound.prefixed(original_packets(legacy))
    old_messages = core.semantic_node_local_v4_messages(legacy, 'RELATIONS', plan=old_plan, nodes=old_nodes)
    assert list(probe.semantic_output_schema(old_messages)['properties']['overview']['properties']) == ['title', 'node_refs']
    assert accepts(old_rel, old_messages)


def test_all_phase_materials_and_lesson_use_exact_profile_and_current_shape():
    p = prepared()
    plan, nodes, relations = phase_packets(p)
    for phase, value in zip(core.SEMANTIC_MAP_NODE_LOCAL_V4_PHASES, (plan, nodes, relations), strict=True):
        messages = core.semantic_node_local_v4_messages(p, phase, plan=plan, nodes=nodes)
        assert json.loads(messages[1]['content'])['author_profile'] == PROFILE
        assert accepts(value, messages)
    value = artifact(p)
    result, coverage = app.build_semantic_map(p, old.response(p, value))
    assert coverage['mapped_count'] == 2
    assert result.private_evidence()['graph']['meaning_review']['node_local_plan']['phase_artifact'] == value
    assert result.safe_projection(authenticated_owner_scope=OWNER)['wire_kind'] == 'watashi.map.v3'


def test_old_and_new_outer_identities_reject_rebinding_and_keep_source():
    p, v1 = prepared(), bound.prepared()
    assert p.fields == v1.fields and p.source_guard == v1.source_guard and p.frozen == v1.frozen
    assert p.request_ref != v1.request_ref
    with pytest.raises(core.AnalysisSemanticMapError, match='lineage_invalid'):
        core.assemble_semantic_node_local_v4(p, bound.artifact(v1))
    with pytest.raises(core.AnalysisSemanticMapError, match='lineage_invalid'):
        core.assemble_semantic_node_local_v4(v1, artifact(p))


def test_selected_refs_and_order_do_not_certify_unwritten_free_title():
    p = prepared()
    values = list(phase_packets(p))
    values[2]['overview'] = dict(node_refs=['n2'], title='本人は島へ旅行したい')
    selected = core.semantic_node_local_v4_messages(p, 'RELATIONS', plan=values[0], nodes=values[1])
    assert accepts(values[2], selected)
    value = artifact(p, values)
    result, _ = app.build_semantic_map(p, old.response(p, value))
    review = result.private_evidence()['graph']['meaning_review']['node_local_plan']
    assert review['meaning_status'] == 'UNASSESSED'
    assert review['full_source_semantic_coverage'] is False
    assert review['phase_artifact'] == value


def test_transport_and_existing_shared_deadline_guards_keep_v2_lineage(monkeypatch):
    monkeypatch.setattr(old, 'PROFILE', PROFILE)
    monkeypatch.setattr(old, 'ALIAS', ALIAS)
    monkeypatch.setattr(old, 'phase_packets', phase_packets)
    old.test_real_three_transport_requests_keep_original_raw_and_freeze_actual_registry()
    old.test_absolute_deadline_cancels_slow_continuous_stream(monkeypatch)
    old.test_cancellation_propagates_without_next_phase_or_retry()
    old.test_exhausted_total_token_budget_never_starts_second_generation()


def test_cohort_and_leaf_merge_source_views_keep_selection_order(monkeypatch):
    monkeypatch.setattr(old, 'PROFILE', PROFILE)
    monkeypatch.setattr(old, 'generated_phase_values', lambda p: select_first(original_generated(p)))
    monkeypatch.setattr(old, 'artifact', artifact)
    old.test_correction_cohort_full_explanation_and_leaf_merge_lineage_are_preserved(monkeypatch)


@pytest.mark.parametrize('alias,marker,status', [
    (ALIAS, PROFILE, 200),
    (ALIAS, core.SEMANTIC_MAP_NODE_LOCAL_V4_BOUND_PROFILE, 400),
    (sources.SEMANTIC_NODE_LOCAL_V4_BOUND_MODEL, PROFILE, 400),
    (sources.SEMANTIC_NODE_LOCAL_V4_MODEL, PROFILE, 400),
])
def test_native_alias_profile_pair_is_exact_in_v2(alias, marker, status, monkeypatch):
    monkeypatch.setattr(bound, 'PROFILE', PROFILE)
    bound.test_native_exact_alias_marker_pair_and_actual_phase_usage(alias, marker, status)
