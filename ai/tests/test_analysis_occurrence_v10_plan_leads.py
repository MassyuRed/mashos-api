"""A new map item leads with its own source location; context can be shared."""
import json

import pytest

from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from test_analysis_node_local_native_profile import accepts, advance, probe
from test_analysis_occurrence_v7_qualifications import MIXED, PENDING, REPORTED, prepared
from test_analysis_occurrence_v9_plan import compact, node, plan


def test_same_start_cannot_be_recycled_by_extending_its_quote_or_changing_the_other_unit():
    current = prepared(core.SEMANTIC_MAP_OCCURRENCE_V10_PROFILE)
    previous = prepared(core.SEMANTIC_MAP_OCCURRENCE_V9_PROFILE)
    first, second = json.loads(current.material_json)['fields']
    earlier = dict(quote=PENDING, field=first['field'])
    report = dict(quote=REPORTED, field=second['field'])
    extended = dict(quote=second['text'], field=second['field'])
    other = dict(quote=MIXED, field=second['field'])
    opening = node(1, [report], [earlier])
    repeated = plan(opening, node(2, [extended], [other]))
    assert core.semantic_node_local_v4_plan(previous, repeated) == repeated
    assert accepts(repeated, previous.messages())
    with pytest.raises(ValueError, match='analysis_semantic_node_lead_repeated'):
        core.semantic_node_local_v4_plan(current, repeated)
    assert not accepts(repeated, current.messages())
    for new_lead in (other, earlier):
        # Common context (report) may recur and a former supporting root can lead a later item.
        changed = plan(opening, node(2, [new_lead, report]))
        assert core.semantic_node_local_v4_plan(current, changed) == changed
        assert accepts(changed, current.messages())


def test_last_available_lead_lets_the_model_finish_without_offering_an_empty_node():
    parent = prepared(core.SEMANTIC_MAP_OCCURRENCE_V10_PROFILE)
    leaf = core.prepare_semantic_leaf(parent, (parent.frozen.members[0].saved_record_ref,))
    field, = json.loads(leaf.material_json)['fields']
    raw = compact(plan(node(1, [dict(quote=field['text'], field=field['field'])])))
    messages = leaf.messages()
    alphabet = ''.join(dict.fromkeys(raw + compact(messages) + ' '))
    state = advance(probe.semantic_json_parser(messages, alphabet), raw[:-2])
    assert ',' not in state.get_allowed_characters()
    assert advance(state, ']}').can_end()
