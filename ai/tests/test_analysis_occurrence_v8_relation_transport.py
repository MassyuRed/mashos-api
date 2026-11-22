"""Bind the v8 relation decoder to the original PLAN while preserving v7 wires."""
import json

import pytest

import analysis_if_model_source as if_sources
import analysis_model_source as sources
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from test_analysis_event_plan_model_alias import environment
from test_analysis_node_local_native_profile import accepts
from test_analysis_occurrence_v7_qualifications import packets, prepared
from test_emlis_natural_reply_probe_http import probe


def relation_messages(p, plan, nodes):
    return core.semantic_node_local_v4_messages(p, 'RELATIONS', plan=plan, nodes=nodes)


def test_v8_keeps_the_authored_registry_and_native_decoder_of_v7(monkeypatch):
    environment(monkeypatch, model=sources.SEMANTIC_OCCURRENCE_V8_MODEL)
    source = sources.application_analysis_model_source()
    profile = sources.analysis_model_prompt_version(source)
    assert profile == core.SEMANTIC_MAP_OCCURRENCE_V8_PROFILE
    assert if_sources.application_analysis_if_model_source().model == sources.SEMANTIC_EVENT_PLAN_BASE_MODEL
    v8 = prepared(profile)
    v7 = prepared(core.SEMANTIC_MAP_OCCURRENCE_V7_PROFILE)
    plan, nodes, response = packets(v7)
    old = relation_messages(v7, plan, nodes)
    new = relation_messages(v8, plan, nodes)
    original, compact = [json.loads(messages[1]['content']) for messages in (old, new)]
    assert compact.pop('plan_sha256') == core.semantic_map_hash(plan)
    assert compact.keys() == original.keys() - {'plan', 'relation_units'}
    for key in compact.keys() - {'author_profile'}:
        assert compact[key] == original[key]
    assert core.semantic_node_local_v4_artifact_schema(v8) != core.semantic_node_local_v4_artifact_schema(v7)
    assert probe.semantic_output_schema(old) == probe.semantic_output_schema(new)
    assert accepts(response, new)


@pytest.mark.parametrize('change', ['digest', 'missing', 'order', 'extra_plan', 'extra_facts'])
def test_v8_refuses_stale_plan_digest_or_ambiguous_registry(change):
    v7 = prepared(core.SEMANTIC_MAP_OCCURRENCE_V7_PROFILE)
    v8 = prepared(core.SEMANTIC_MAP_OCCURRENCE_V8_PROFILE)
    plan, nodes, _ = packets(v7)
    messages = relation_messages(v8, plan, nodes)
    material = json.loads(messages[1]['content'])
    if change == 'digest':
        material['plan_sha256'] = '0' * 64
    elif change == 'missing':
        del material['plan_sha256']
    elif change == 'order':
        material['candidate_nodes'].reverse()
    elif change == 'extra_plan':
        material['plan'] = plan
    else:
        material['relation_units'] = {}
    messages[1]['content'] = json.dumps(material, ensure_ascii=False)
    with pytest.raises(ValueError, match='semantic_v8_compact_'):
        probe.semantic_output_schema(messages)
