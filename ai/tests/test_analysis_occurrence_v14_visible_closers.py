"""Check source-bound visible strings through ordinary NODES and RELATIONS."""
import json

import pytest

import analysis_semantic_map as maps
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from test_analysis_cumulative import OWNER
from test_analysis_node_local_native_profile import accepts, advance
from test_analysis_occurrence_v11_display import map_stages
from test_analysis_v13_separate_record_titles import wire
from test_emlis_natural_reply_probe_http import probe


def stages(*notes, profile=core.SEMANTIC_MAP_OCCURRENCE_V14_PROFILE):
    old, plan, bodies = map_stages(*notes)
    prepared = maps.prepare_semantic_map(OWNER, json.loads(old.source_snapshot_json), prompt_version=profile)
    for node in bodies['nodes'].values():
        node['units']['u1']['unknowns'] = []
    return prepared, plan, bodies


@pytest.mark.parametrize('field', ['title', 'meaning', 'fact_parts'])
@pytest.mark.parametrize('value,allowed', [
    ('記録を観察。}}', True),
    ('}},', True),
    ('長さは[1, 2]で、辞書は{"末尾":"}"}です', True),
    ('根拠にある }} の表記', True),
    ('根拠を超えた }}} の表記', False),
    ('別の記録にある ] の表記', False),
])
def test_each_authored_node_field_preserves_balanced_code_and_its_own_source(field, value, allowed):
    prepared, plan, bodies = stages('原文の記号は }} の続き', '別件の記号は ] の続き')
    node = bodies['nodes']['n1']
    if field == 'fact_parts':
        parts = node['units']['u1'][field]
        parts[next(iter(parts))] = value
    else:
        node[field] = value
    raw = wire(prepared, plan, bodies)
    messages = core.semantic_node_local_v4_messages(prepared, 'NODES', plan=plan)
    # Each original licenses its own orphan run, including if it occurs at the
    # start or at the end of the authored string. Ordinary punctuation is free.
    assert accepts(raw, messages) == allowed
    if allowed:
        assert core.admit_semantic_node_local_v4_nodes_response(prepared, plan, raw) == bodies
    else:
        with pytest.raises(core.AnalysisSemanticMapError, match='serialization_residue'):
            core.admit_semantic_node_local_v4_nodes_response(prepared, plan, raw)


@pytest.mark.parametrize('value', ['}},', '記録。' + '}' * 50, '残りは ]'])
def test_unwitnessed_free_fact_never_becomes_a_number_or_an_auto_repair(value):
    prepared, plan, bodies = stages('部材の到着について連絡を待つ')
    parts = bodies['nodes']['n1']['units']['u1']['fact_parts']
    parts[next(iter(parts))] = value
    raw = wire(prepared, plan, bodies)
    assert not accepts(raw, core.semantic_node_local_v4_messages(prepared, 'NODES', plan=plan))
    with pytest.raises(core.AnalysisSemanticMapError, match='serialization_residue'):
        core.admit_semantic_node_local_v4_nodes_response(prepared, plan, raw)
    assert list(parts.values()) == [value]


def relation(prepared, plan, bodies, label=None):
    items = []
    if label:
        edge = {'from': 'n1', 'to': 'n2', 'from_unit': 'n1.u1', 'to_unit': 'n2.u1'}
        first, second = [n['units'][0]['evidence'][0]['quote'] for n in plan['nodes'][:2]]
        edge.update(from_source=core._semantic_source_cues(first)[0], to_source=core._semantic_source_cues(second)[0],
                    label=label, relation_kind='CONTEXT_CONTRAST')
        items.append(edge)
    return dict(schema_version=core._semantic_v4_schema('RELATIONS'),
        nodes_sha256=core.semantic_map_hash(core._semantic_v4_join(plan, bodies)),
        qualification_review={}, edges=items, overview=dict(node_refs=['n1'], title='前日の記録'))


@pytest.mark.parametrize('profile,allowed', [
    (core.SEMANTIC_MAP_OCCURRENCE_V13_PROFILE, True),
    (core.SEMANTIC_MAP_OCCURRENCE_V14_PROFILE, False),
])
def test_previous_profile_replays_limit_length_overview_with_orphan_closers(profile, allowed):
    prepared, plan, bodies = stages('電話をかけた。', '翌日、受付から返事があった。', profile=profile)
    packet = relation(prepared, plan, bodies)
    title = '翌日、受付から返事があった。'
    packet['overview'] = dict(node_refs=['n1', 'n2'], title=title.ljust(80, '}'))
    messages = core.semantic_node_local_v4_messages(prepared, 'RELATIONS', plan=plan, nodes=bodies)
    assert accepts(packet, messages) == allowed
    if allowed:
        assert core.semantic_node_local_v4_relations(prepared, plan, bodies, packet)['overview'] == packet['overview']
    else:
        with pytest.raises(core.AnalysisSemanticMapError, match='serialization_residue'):
            core.semantic_node_local_v4_relations(prepared, plan, bodies, packet)
        # A JSON escape produces exactly the same public character.
        raw = json.dumps(packet, ensure_ascii=False, separators=(',', ':')).replace(title + '}', title + r'\u007d')
        alphabet = ''.join(dict.fromkeys(raw + json.dumps(messages, ensure_ascii=False)))
        with pytest.raises(ValueError, match='native_character_rejected'):
            advance(probe.semantic_json_parser(messages, alphabet), raw)


@pytest.mark.parametrize('where,source_id,allowed', [
    ('overview', 'n1', False), ('overview', 'n3', True), ('edge', 'n1', False), ('edge', 'n3', True),
])
def test_selected_overview_nodes_and_edge_endpoints_delimit_the_allowed_sources(where, source_id, allowed):
    notes = ['缶を開ける予定。', '中身を取り出した。', '手順には }} とあった。']
    if where == 'edge' and allowed:
        notes[0], notes[2] = notes[2], notes[0]
    prepared, plan, bodies = stages(*notes)
    label = '手順にある }} の表記'
    packet = relation(prepared, plan, bodies, label if where == 'edge' else None)
    if where == 'overview':
        packet['overview'].update(node_refs=[source_id], title=label)
    messages = core.semantic_node_local_v4_messages(prepared, 'RELATIONS', plan=plan, nodes=bodies)
    assert accepts(packet, messages) == allowed
    if allowed:
        result = core.semantic_node_local_v4_relations(prepared, plan, bodies, packet)
        assert result['overview'] == packet['overview']
        if where == 'edge':
            assert result['edges'][0]['label'] == label
    else:
        with pytest.raises(core.AnalysisSemanticMapError, match='serialization_residue'):
            core.semantic_node_local_v4_relations(prepared, plan, bodies, packet)


@pytest.mark.parametrize('phase', ['NODES', 'RELATIONS'])
@pytest.mark.parametrize('prefix_offset', [0, 1])
def test_greedy_shortcut_rechecks_a_multichar_token_before_emission(phase, prefix_offset):
    from types import SimpleNamespace
    np = pytest.importorskip('numpy')
    prepared, plan, bodies = stages('結果を待つ')
    if phase == 'NODES':
        packet = wire(prepared, plan, bodies)
        packet['nodes']['n1']['meaning'] = '待つ'
        key = '"meaning":"'
    else:
        packet = relation(prepared, plan, bodies)
        key = '"title":"'
    messages = core.semantic_node_local_v4_messages(prepared, phase, plan=plan,
        nodes=bodies if phase == 'RELATIONS' else None)
    raw = json.dumps(packet, ensure_ascii=False, separators=(',', ':'))
    raw_prefix = raw[:raw.index(key) + len(key)]
    alphabet = ''.join(dict.fromkeys(raw + '続き}' + json.dumps(messages, ensure_ascii=False)))
    parser = probe.semantic_json_parser(messages, alphabet)
    tokens = {0: '続き}}', 1: '続き'}
    enforcer = SimpleNamespace(root_parser=parser, prefix_states={},
        tokenizer_tree=SimpleNamespace(new_word_tokens=tokens.keys(), tokens_to_strs=tokens))
    model_filter = probe._occurrence_greedy_relation_filter(SimpleNamespace(token_enforcer=enforcer),
                                                        prompt_tokens=prefix_offset)
    step = advance(parser, raw_prefix)
    assert step.shortcut_key()[0] == 'json_freetext'
    enforcer.prefix_states[(7, 8)[prefix_offset:]] = SimpleNamespace(parser=step)
    if phase == 'NODES':
        tokenizer = SimpleNamespace(decode=lambda ids, **kwargs: raw_prefix + tokens[ids[-1]])
        model_filter = probe._occurrence_greedy_node_filter(tokenizer, 1, visible_filter=model_filter)
    scores = model_filter(np.array([[7, 8]]), np.array([[1., .5]]))
    assert scores.tolist() == [[float('-inf'), .5]]
