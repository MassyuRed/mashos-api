"""The PLAN may share sources between distinct allocations and finish without filling every node."""
import json

import pytest

from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from test_analysis_node_local_native_profile import accepts, advance, probe
from test_analysis_occurrence_v7_qualifications import prepared


def node(index, *units):
    return dict(node_id=f'n{index}', units=[dict(evidence=list(roots)) for roots in units])


def plan(*nodes):
    return dict(schema_version=core._semantic_v4_schema('PLAN'), nodes=list(nodes))


def compact(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'))


def test_full_allocation_is_unique_but_shared_roots_and_split_units_stay_valid():
    current = prepared(core.SEMANTIC_MAP_OCCURRENCE_V9_PROFILE)
    previous = prepared(core.SEMANTIC_MAP_OCCURRENCE_V8_PROFILE)
    fields = json.loads(current.material_json)['fields']
    a, b = (dict(quote=f['text'].split('。', 1)[0] + '。', field=f['field']) for f in fields)
    first = node(1, [a], [b])
    repeat = plan(first, node(2, [a], [b]))
    with pytest.raises(ValueError, match='analysis_semantic_node_allocation_repeated'):
        core.semantic_node_local_v4_plan(current, repeat)
    assert not accepts(repeat, current.messages())
    assert core.semantic_node_local_v4_plan(previous, repeat) == repeat
    assert accepts(repeat, previous.messages())
    for different in [node(2, [a, b]), node(2, [b], [a]), node(2, [a], [b, a])]:
        changed = plan(first, different)
        assert core.semantic_node_local_v4_plan(current, changed) == changed
        assert accepts(changed, current.messages())


@pytest.mark.parametrize('two_units_first', [False, True])
def test_smallest_leaf_can_take_either_distinct_node_and_end_when_options_exhausted(two_units_first):
    parent = prepared(core.SEMANTIC_MAP_OCCURRENCE_V9_PROFILE)
    leaf = core.prepare_semantic_leaf(parent, (parent.frozen.members[0].saved_record_ref,))
    field, = json.loads(leaf.material_json)['fields']
    evidence = [dict(quote=field['text'], field=field['field'])]
    allocations = [[evidence, evidence], [evidence]]
    if not two_units_first:
        allocations.reverse()
    complete = plan(node(1, *allocations[0]), node(2, *allocations[1]))
    messages = leaf.messages()
    raw = compact(complete)
    alphabet = ''.join(dict.fromkeys(raw + compact(messages) + ' '))
    state = advance(probe.semantic_json_parser(messages, alphabet), raw[:-2])
    assert ']' in state.get_allowed_characters() and ',' not in state.get_allowed_characters()
    assert advance(state, ']}').can_end()
    assert core.semantic_node_local_v4_plan(leaf, complete) == complete


def test_saturated_last_unit_offers_a_distinct_final_root_before_it_is_too_late():
    current = prepared(core.SEMANTIC_MAP_OCCURRENCE_V9_PROFILE)
    messages = current.messages()
    material = json.loads(messages[1]['content'])
    quotes = ['窓を開けた。', '鍵を置いた。', '棚を閉めた。', '机を動かした。', '椅子を戻した。']
    material['fields'] = [dict(field=1, record=1, text=''.join(quotes))]
    messages[1]['content'] = compact(material)
    a, b, c, d, e = [dict(quote=q, field=1) for q in quotes]
    first = node(1, [a], [a, b, c, d])
    repeat = plan(first, node(2, [a], [a, b, c, d]))
    changed = plan(first, node(2, [a], [a, b, c, e]))
    raw = compact(repeat)
    prefix = raw[:raw.rindex(compact(d))]
    alphabet = ''.join(dict.fromkeys(compact(messages) + raw + ' '))
    start = probe.semantic_json_parser(messages, alphabet)
    with pytest.raises(ValueError, match='native_character_rejected'):
        advance(advance(start, prefix), compact(d))
    assert advance(advance(start, prefix), compact(changed)[len(prefix):]).can_end()
