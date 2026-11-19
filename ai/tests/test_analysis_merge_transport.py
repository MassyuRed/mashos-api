"""Require the stored v24 history MERGE receipt to match the exact phase transport."""
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from types import SimpleNamespace

import pytest

import analysis_merge_wire as wire
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from test_analysis_merge_wire import fixture


def packets(monkeypatch, version=wire.VERSION):
    stage = SimpleNamespace(kind='MERGE', prompt_version=core.SEMANTIC_MAP_OCCURRENCE_V24_PROFILE)
    monkeypatch.setattr(core, 'semantic_node_local_v4_messages', lambda _, phase='PLAN', **kwargs: fixture(phase))
    monkeypatch.setattr(core, 'admit_semantic_node_local_v4_plan_response', lambda _, value, **kwargs: value)
    monkeypatch.setattr(core, 'admit_semantic_node_local_v4_nodes_response', lambda _, plan, value: value)
    monkeypatch.setattr(core, 'semantic_node_local_v4_relations', lambda _, plan, nodes, value: (plan, nodes, value))
    compact = dict(merge_wire_version=version, schema_version=core.semantic_node_local_v4_artifact_schema(stage), phases=[])
    historical = dict(schema_version=compact['schema_version'], phases=[])
    for phase in core.SEMANTIC_MAP_NODE_LOCAL_V4_PHASES:
        raw = core.semantic_map_canonical({'phase': phase})
        logical = core.semantic_node_local_v4_messages(stage, phase)
        actual = core.semantic_node_local_v4_wire_messages(stage, phase, wire_version=version)
        assert actual != logical and wire.legacy_messages(actual) == logical
        old = dict(phase=phase, raw=raw, raw_sha256=hashlib.sha256(raw.encode()).hexdigest(), finish_reason='stop',
                   completion_tokens=8, messages_sha256=core.semantic_map_hash(logical))
        historical['phases'].append(old)
        compact['phases'].append(dict(old, messages_sha256=core.semantic_map_hash(actual), logical_messages_sha256=old['messages_sha256']))
    return stage, historical, compact


@pytest.mark.parametrize('version', wire.VERSIONS)
def test_v24_merge_reads_original_and_compact_phase_artifacts(monkeypatch, version):
    stage, historical, compact = packets(monkeypatch, version)
    assert core.assemble_semantic_node_local_v4(stage, historical) == core.assemble_semantic_node_local_v4(stage, compact)
    lost_marker = deepcopy(compact)
    del lost_marker['merge_wire_version']
    with pytest.raises(ValueError):
        core.assemble_semantic_node_local_v4(stage, lost_marker)
    other_version = wire.LEGACY_VERSION if version == wire.VERSION else wire.VERSION
    with pytest.raises(ValueError):
        core.assemble_semantic_node_local_v4(stage, {**compact, 'merge_wire_version': other_version})
    for kind in ('WHOLE', 'LEAF'):
        old_path = SimpleNamespace(kind=kind, prompt_version=stage.prompt_version)
        assert core.semantic_node_local_v4_wire_messages(old_path) == core.semantic_node_local_v4_messages(old_path)
        with pytest.raises(ValueError):
            core.assemble_semantic_node_local_v4(old_path, compact)


@pytest.mark.parametrize('index', [0, 1, 2])
@pytest.mark.parametrize('key', ['raw', 'raw_sha256', 'messages_sha256', 'logical_messages_sha256'])
def test_saved_merge_rejects_changed_raw_or_message_binding(monkeypatch, index, key):
    stage, _, compact = packets(monkeypatch)
    compact['phases'][index][key] += 'x'
    with pytest.raises(ValueError):
        core.assemble_semantic_node_local_v4(stage, compact)


def test_compiler_parent_view_reconstructs_the_merge_transport(monkeypatch):
    from test_analysis_occurrence_v17_record_owners import prepared
    parent = prepared(['朝、庭で土を見た。', '夕方、鉢に水を足した。'], core.SEMANTIC_MAP_OCCURRENCE_V24_PROFILE)
    leaf = core.prepare_semantic_leaf(parent, (parent.frozen.members[0].saved_record_ref,))
    material = json.loads(leaf.material_json)
    material['history_stage']['kind'] = 'MERGE'
    stage = replace(leaf, kind='MERGE', material_json=core.semantic_map_canonical(material))
    compiler_view = core._semantic_v4_view(stage)
    assert not hasattr(compiler_view, 'kind') and compiler_view.request_ref == stage.request_ref
    _, old, compact = packets(monkeypatch)
    assert core.assemble_semantic_node_local_v4(compiler_view, old) == core.assemble_semantic_node_local_v4(compiler_view, compact)
    assert not core.semantic_node_local_v4_uses_compact_merge(parent)
    assert not core.semantic_node_local_v4_uses_compact_merge(replace(parent, material_json=stage.material_json))
    assert not core.semantic_node_local_v4_uses_compact_merge(core._semantic_v4_view(leaf))


def source_merge(notes):
    from test_analysis_occurrence_v17_record_owners import prepared

    parent = prepared(notes, wire.PROFILE)
    refs = tuple(member.saved_record_ref for member in parent.frozen.members)
    stage = core.prepare_semantic_leaf(parent, refs)
    material = json.loads(stage.material_json)
    material['history_stage']['kind'] = 'MERGE'
    material.update(leaf_source_index=[], field_manifest=[], omitted_ranges=[], leaf_receipts=[])
    for field in material['fields']:
        field['fragment_scalar_range'] = [0, len(field['text'])]
        field['fragment_is_complete_field'] = True
    return replace(stage, kind='MERGE', material_json=core.semantic_map_canonical(material))


def test_merge_wire_record_anchors_preserve_comparisons_and_old_receipts():
    from test_analysis_node_local_native_profile import accepts
    from test_analysis_occurrence_v17_record_owners import packet

    first, detail = '午前に庭で土を測った。', '雨の後で土は湿っていた。'
    later, condition = '翌朝、別の畑で土を測った。', '日なたの土は乾いていた。'
    merge = source_merge([first + detail, later + condition])
    anchors = [[[(1, first)]], [[(2, later)]]]
    compared = packet(merge, anchors + [[[(1, detail)], [(2, condition)]]])
    mixed = packet(merge, [[[(1, first), (2, condition)]], [[(2, later)]]])
    mixed_unit = packet(merge, anchors + [[[(1, detail), (2, condition)]]])
    for version in (wire.LEGACY_VERSION, wire.VERSION):
        messages = core.semantic_node_local_v4_wire_messages(merge, wire_version=version)
        strict = version == wire.VERSION
        assert accepts(compared, messages)
        assert core.admit_semantic_node_local_v4_plan_response(merge, compared, merge_anchors=strict)
        for raw in (mixed, mixed_unit):
            assert accepts(raw, messages) is not strict
            if strict:
                with pytest.raises(core.AnalysisSemanticMapError, match='record_owner_invalid'):
                    core.admit_semantic_node_local_v4_plan_response(merge, raw, merge_anchors=True)
            else:
                assert core.admit_semantic_node_local_v4_plan_response(merge, raw)


@pytest.mark.parametrize('count,missing,correction', [(13, False, False), (3, True, False), (12, False, True)])
def test_merge_keeps_flexible_allocation_when_source_anchors_do_not_fit(count, missing, correction):
    from analysis_plan_source_choices import record_plan_owners

    rows = [{'record': i} for i in range(1, count + 1)]
    fields = [dict(field=i, record=i, source_role='ORIGINAL_INPUT') for i in range(1, count + 1)]
    if missing:
        fields[-1]['source_role'] = 'SUPPLEMENTAL_ANSWER'
    if correction:
        fields.append(dict(field=count + 1, record=None, source_role='USER_ANALYSIS_MAP_CORRECTION'))
    material = dict(author_profile=wire.PROFILE, history_stage={'kind': 'MERGE'}, records=rows, fields=fields)
    assert record_plan_owners(material, {f['field'] for f in fields}, merge_anchors=True) == ()


def test_larger_merge_can_group_original_evidence_beyond_node_capacity():
    from test_analysis_node_local_native_profile import accepts
    from test_analysis_occurrence_v17_record_owners import packet

    notes = [f'{i}番の棚の温度を記録した。' for i in range(1, 14)]
    merge = source_merge(notes)
    groups = [[[(1, notes[0]), (2, notes[1])]]] + [[[(i, notes[i - 1])]] for i in range(3, 14)]
    raw = packet(merge, groups)
    assert accepts(raw, core.semantic_node_local_v4_wire_messages(merge))
    assert core.admit_semantic_node_local_v4_plan_response(merge, raw, merge_anchors=True)
