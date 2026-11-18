"""Opt-in MAP unit references keep the same plan ownership and IF route."""
from copy import deepcopy
import json

import pytest

import analysis_if_model_source as if_sources
import analysis_model_source as sources
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from test_analysis_event_plan_model_alias import environment
from test_analysis_node_local_native_profile import accepts
from test_emlis_natural_reply_probe_http import probe
import test_analysis_node_local_bound_roots as bound
import test_analysis_bound_roots_v2_selection as selection


def sample():
    source = selection.prepared()
    plan, nodes, _ = selection.phase_packets(source)
    plan['nodes'][0]['units'].append(dict(evidence=[dict(quote='まだ送っていない。', field=1)]))
    nodes['plan_sha256'] = core.semantic_map_hash(plan)
    first_node = nodes['nodes']['n1']
    first_node['units']['u2'] = dict(
        assigned_evidence=core._semantic_v4_assigned_evidence(plan['nodes'][0]['units'][1]),
        source_mode='RECORDED', fact='本人はまだ送っていません。', unknowns=[])
    # Feed the actual native private contract, with no model or renderer mock.
    selected = core.semantic_node_local_v4_messages(source, 'NODES', plan=plan)
    material = json.loads(selected[1]['content'])
    variants = {}
    for version in (probe.OCCURRENCE_V4_PROFILE, probe.OCCURRENCE_V5_PROFILE):
        material['author_profile'] = version
        variants[version] = [selected[0], dict(role='user', content=json.dumps(material, ensure_ascii=False))]
    compact = deepcopy(nodes)
    for node_id, node in compact['nodes'].items():
        for unit_id, unit in node['units'].items():
            unit.pop('assigned_evidence')
            node['units'][unit_id] = dict(evidence_ref=f'{node_id}.{unit_id}', **unit)
    return nodes, compact, variants


def test_compact_native_requires_its_current_node_unit_and_plan_digest():
    original, compact, messages = sample()
    selected = messages[probe.OCCURRENCE_V5_PROFILE]
    legacy = messages[probe.OCCURRENCE_V4_PROFILE]
    assert accepts(compact, selected) and accepts(original, legacy)
    assert not accepts(compact, legacy) and not accepts(original, selected)
    for wrong in ('n2.u1', 'n1.u2', 'u1', '', 'n1.u1.extra'):
        bad = deepcopy(compact)
        bad['nodes']['n1']['units']['u1']['evidence_ref'] = wrong
        assert not accepts(bad, selected)
    compact['plan_sha256'] = '0' * 64
    assert not accepts(compact, selected)


def test_compact_native_preserves_visible_duplicate_guard():
    _, compact, _ = sample()
    compact['nodes']['n2'] = deepcopy(compact['nodes']['n1'])
    for unit_id, unit in compact['nodes']['n2']['units'].items():
        unit['evidence_ref'] = f'n2.{unit_id}'
    assert probe._occurrence_duplicate_prefix(json.dumps(compact, ensure_ascii=False))


@pytest.mark.parametrize('alias, profile, status', [
    (probe.OCCURRENCE_V5_MODEL, probe.OCCURRENCE_V5_PROFILE, 200),
    (probe.OCCURRENCE_V5_MODEL, probe.OCCURRENCE_V4_PROFILE, 400),
    (probe.OCCURRENCE_V4_MODEL, probe.OCCURRENCE_V5_PROFILE, 400),
])
def test_compact_native_checks_request_profile(alias, profile, status):
    bound.test_native_exact_alias_marker_pair_and_actual_phase_usage(alias, profile, status)


def test_compact_map_alias_preserves_analysis_if(monkeypatch):
    environment(monkeypatch, model=sources.SEMANTIC_OCCURRENCE_V5_MODEL)
    assert sources.application_analysis_model_source().prompt_version == probe.OCCURRENCE_V5_PROFILE
    assert if_sources.application_analysis_if_model_source().model == sources.SEMANTIC_EVENT_PLAN_BASE_MODEL


def test_same_plan_ref_binds_exact_source_at_both_admission_and_relation_readback():
    import analysis_semantic_map as app
    original, compact, messages = sample()
    material = json.loads(messages[probe.OCCURRENCE_V5_PROFILE][1]['content'])
    plan = material['plan']
    p = app.prepare_semantic_map(selection.OWNER,
        json.loads(selection.prepared().source_snapshot_json), prompt_version=core.SEMANTIC_MAP_OCCURRENCE_V5_PROFILE)
    assert core.semantic_node_local_v4_nodes(p, plan, compact) is compact
    expected = core._semantic_v4_join(plan, original)
    rel_material = json.loads(core.semantic_node_local_v4_messages(p, 'RELATIONS', plan=plan, nodes=compact)[1]['content'])
    assert rel_material['candidate_nodes'] == expected
    for wrong in ('n1.u2', 'n2.u1', 'n1.u1.extra'):
        damaged = deepcopy(compact)
        damaged['nodes']['n1']['units']['u1']['evidence_ref'] = wrong
        with pytest.raises(core.AnalysisSemanticMapError):
            core.semantic_node_local_v4_nodes(p, plan, damaged)
    changed = deepcopy(plan)
    changed['nodes'][0]['units'].reverse()
    with pytest.raises(core.AnalysisSemanticMapError):
        core.semantic_node_local_v4_nodes(p, changed, compact)
    with pytest.raises(core.AnalysisSemanticMapError):
        core.semantic_node_local_v4_nodes(p, plan, original)
