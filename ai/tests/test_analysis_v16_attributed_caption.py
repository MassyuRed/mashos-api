"""Dates in derived captions stay attached to their individual source facts."""
from dataclasses import replace

import pytest

from cocolon_meaning_experience_engine.cores.analysis import intent_compiler, semantic_admission as core
from test_analysis_v13_separate_record_titles import stages
from test_analysis_v14_mixed_record_dates import fact


@pytest.mark.parametrize('quote_length,overview_uses_title,node_uses_title', [
    (9, False, False),
    (21, True, False),
    (40, True, True),
])
def test_attributed_captions_preserve_fact_ownership_at_both_public_text_limits(
        quote_length, overview_uses_title, node_uses_title):
    quotes = tuple(('記録' + str(i)).ljust(quote_length-1, 'あ') + '。' for i in range(4))
    _, prepared, plan, _ = stages(*quotes)
    root = [n['units'][0]['evidence'][0] for n in plan['nodes']]
    groups = [root, root[::-1]]
    title = quotes[1]
    node = dict(units=[fact(part) for part in groups], node_kind='STATE_CONTEXT',
                perspective='SELF', title=title, meaning='')
    packet = dict(schema_version=core.SEMANTIC_MAP_NODE_LOCAL_V3_SCHEMA, nodes=[node], edges=[],
                  overview=dict(node_refs=['n1'], title='記録の変化'))
    fixed = {f'n1.u{i}': tuple(r['quote'] for r in part) for i, part in enumerate(groups,1)}
    old = replace(prepared, prompt_version=core.SEMANTIC_MAP_NODE_LOCAL_V3_PROFILE)
    render = intent_compiler._expand_analysis_semantic_node_local_v3
    result = render(old, packet, mark_record_ownership=True, fixed_record_units=fixed,
                    use_attributed_captions=True)
    legacy = render(old, packet, mark_record_ownership=True, fixed_record_units=fixed)
    assert '・' in legacy['overview']['summary']
    overview, body = result['overview']['summary'], result['nodes'][0]
    assert (overview == title) == overview_uses_title
    assert (body['summary'] == title) == node_uses_title
    assert len(overview) <= 249 and len(body['summary']) <= 400
    assert '・' not in overview and '・' not in body['summary']
    assert all('：' + quote in body['explanation'] for quote in quotes)
    if not overview_uses_title:
        assert overview == body['summary']
        assert all('：' + quote in overview for quote in quotes)
