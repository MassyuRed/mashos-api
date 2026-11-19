"""Require the stored v24 history MERGE receipt to match the exact phase transport."""
from copy import deepcopy
import hashlib
from types import SimpleNamespace

import pytest

import analysis_merge_wire as wire
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from test_analysis_merge_wire import fixture


def packets(monkeypatch):
    stage = SimpleNamespace(kind='MERGE', prompt_version=core.SEMANTIC_MAP_OCCURRENCE_V24_PROFILE)
    monkeypatch.setattr(core, 'semantic_node_local_v4_messages', lambda _, phase='PLAN', **kwargs: fixture(phase))
    monkeypatch.setattr(core, 'admit_semantic_node_local_v4_plan_response', lambda _, value: value)
    monkeypatch.setattr(core, 'admit_semantic_node_local_v4_nodes_response', lambda _, plan, value: value)
    monkeypatch.setattr(core, 'semantic_node_local_v4_relations', lambda _, plan, nodes, value: (plan, nodes, value))
    compact = dict(merge_wire_version=wire.VERSION, schema_version=core.semantic_node_local_v4_artifact_schema(stage), phases=[])
    historical = dict(schema_version=compact['schema_version'], phases=[])
    for phase in core.SEMANTIC_MAP_NODE_LOCAL_V4_PHASES:
        raw = core.semantic_map_canonical({'phase': phase})
        logical = core.semantic_node_local_v4_messages(stage, phase)
        actual = core.semantic_node_local_v4_wire_messages(stage, phase)
        assert actual != logical and wire.legacy_messages(actual) == logical
        old = dict(phase=phase, raw=raw, raw_sha256=hashlib.sha256(raw.encode()).hexdigest(), finish_reason='stop',
                   completion_tokens=8, messages_sha256=core.semantic_map_hash(logical))
        historical['phases'].append(old)
        compact['phases'].append(dict(old, messages_sha256=core.semantic_map_hash(actual), logical_messages_sha256=old['messages_sha256']))
    return stage, historical, compact


def test_v24_merge_reads_original_and_compact_phase_artifacts(monkeypatch):
    stage, historical, compact = packets(monkeypatch)
    assert core.assemble_semantic_node_local_v4(stage, historical) == core.assemble_semantic_node_local_v4(stage, compact)
    lost_marker = deepcopy(compact)
    del lost_marker['merge_wire_version']
    with pytest.raises(ValueError):
        core.assemble_semantic_node_local_v4(stage, lost_marker)
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
