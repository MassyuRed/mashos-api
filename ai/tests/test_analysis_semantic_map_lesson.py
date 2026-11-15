"""Authored lesson contract checks; these do not rate model meaning quality."""
from copy import deepcopy
import json

import pytest

import analysis_semantic_map as application
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from test_analysis_semantic_generation_schema import (
    allowed, assert_compact_leaf_native, probe,
)
from test_analysis_cumulative import source_snapshot
from test_analysis_semantic_history_core import packet_for, standard_leaves
from test_analysis_semantic_map import OWNER, response, sample


def lesson(text):
    source = json.loads(text.split('\n例の入力:', 1)[1].splitlines()[0])
    raw = text.split('\n例の出力:', 1)[1].splitlines()[0]
    return source, json.loads(raw), raw


@pytest.mark.parametrize('stage', [None, 'LEAF', 'MERGE'])
def test_authored_lesson_fits_native_profile_with_exact_source_quotes(stage):
    source, packet, raw = lesson(core._semantic_map_lesson_instruction(stage))
    before = deepcopy(source), deepcopy(packet)
    messages = [dict(role='system', content='authored synthetic lesson'),
        dict(role='user', content=json.dumps(source, ensure_ascii=False))]
    schema = probe.semantic_output_schema(messages)
    assert allowed(schema, packet)
    assert list(packet) == list(schema['properties'])
    assert all(list(node) == list(schema['properties']['nodes']['items']['properties'])
        for node in packet['nodes'])
    fields = {field['field']: field['text'] for field in source['fields']}
    for node in packet['nodes']:
        for root in node['evidence']:
            assert fields[root['field']].count(root['quote']) == 1
    assert_compact_leaf_native(messages, raw, True)
    assert (source, packet) == before
    if stage == 'LEAF':
        # The leaf teaches only its present record, never the later example.
        assert {field['record'] for field in source['fields']} == {1}
        assert set(fields) == {1, 2}
        assert len(packet['nodes']) == 2 and packet['edges'] == []
        assert all(node['unknowns'] == [] for node in packet['nodes'])
        assert '肥料' not in raw and '二日後' not in raw
    else:
        assert {field['record'] for field in source['fields']} == {1, 2}
        assert len(packet['nodes']) == 2 and len(packet['edges']) == 1
        assert {root['field'] for root in packet['nodes'][0]['evidence']} == {1, 2, 3, 4}
        assert packet['nodes'][0]['unknowns'] == []
        assert packet['nodes'][1]['unknowns'] == ['妹が肥料を替えたか']
        assert (packet['edges'][0]['from'], packet['edges'][0]['to']) == ('n1', 'n2')


@pytest.mark.parametrize('profile', [core.SEMANTIC_MAP_PROFILE,
    core.SEMANTIC_MAP_SOURCE_DUTIES_PROFILE])
def test_lesson_stays_in_system_and_each_stage_keeps_its_actual_sources(profile):
    prepared = application.prepare_semantic_map(OWNER, sample(), prompt_version=profile)
    original = deepcopy(prepared)
    leaves = standard_leaves(prepared)
    merge = core.prepare_semantic_merge(prepared, leaves)
    for current in (prepared, *(stage for stage, _ in leaves), merge):
        messages = current.messages()
        assert len(messages) == 2 and [m['role'] for m in messages] == ['system', 'user']
        assert messages[1]['content'] == current.material_json
        assert current.source_guard == prepared.source_guard
        assert messages[0]['content'].count('\n例の入力:') == 1
        example, _, _ = lesson(messages[0]['content'])
        expected = {1} if getattr(current, 'kind', None) == 'LEAF' else {1, 2}
        assert {field['record'] for field in example['fields']} == expected
        assert '鉢' not in messages[1]['content']
        assert messages == current.messages()
    assert prepared == original


@pytest.mark.parametrize('stage', [None, 'LEAF', 'MERGE'])
@pytest.mark.parametrize('profile', [core.SEMANTIC_MAP_PROFILE,
    core.SEMANTIC_MAP_SOURCE_DUTIES_PROFILE])
def test_literal_lesson_target_is_admitted_from_its_own_prepared_sources(stage, profile):
    source, _, raw = lesson(core._semantic_map_lesson_instruction(stage))
    snapshot = source_snapshot(len(source['records']))
    for field in source['fields']:
        snapshot['members'][field['record'] - 1]['original'][field['field_path']] = field['text']
    prepared = application.prepare_semantic_map(OWNER, snapshot, prompt_version=profile)
    if stage is None:
        artifact, _ = application.build_semantic_map(prepared, response(prepared, raw=raw))
    elif stage == 'LEAF':
        leaf = core.prepare_semantic_leaf(prepared, (prepared.frozen.members[0].saved_record_ref,))
        graph = core.build_semantic_stage(leaf, response(leaf, raw=raw))
        review = json.loads(graph.meaning_review_json)
        if profile == core.SEMANTIC_MAP_SOURCE_DUTIES_PROFILE:
            assert review['interpretation_status'] == 'UNASSESSED'
        else:
            assert 'interpretation_status' not in review
        return
    else:
        first = core.prepare_semantic_leaf(prepared, (prepared.frozen.members[0].saved_record_ref,))
        first_raw = lesson(core._semantic_map_lesson_instruction('LEAF'))[2]
        second = core.prepare_semantic_leaf(prepared, (prepared.frozen.members[1].saved_record_ref,))
        second_packet = packet_for([dict(field=3,
            quote='二日後、土が乾いていたので、私はその鉢に水を足した。')])
        merge = core.prepare_semantic_merge(prepared, ((first, response(first, raw=first_raw)),
            (second, response(second, second_packet))))
        outcome = core.build_semantic_stage(merge, response(merge, raw=raw))
        assert outcome.artifact is not None
        artifact = outcome.artifact
    review = artifact.private_evidence()['graph'].get('meaning_review', {})
    if profile == core.SEMANTIC_MAP_SOURCE_DUTIES_PROFILE:
        assert review['interpretation_status'] == 'UNASSESSED'
    else:
        assert 'interpretation_status' not in review


def test_lesson_quotes_cannot_become_evidence_for_unrelated_actual_input():
    prepared = application.prepare_semantic_map(OWNER, sample())
    _, _, raw = lesson(prepared.messages()[0]['content'])
    assert_compact_leaf_native(prepared.messages(), raw, False)
    with pytest.raises(application.SemanticMapError, match='analysis_semantic_evidence_unbound'):
        application.build_semantic_map(prepared, response(prepared, raw=raw))
