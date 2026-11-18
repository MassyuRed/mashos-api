"""Private source choices stay with the authored text and its edge endpoint."""

import pytest

import analysis_semantic_map as app
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from test_analysis_node_local_native_profile import accepts
from test_analysis_occurrence_v7_qualifications import MIXED, PENDING, REPORTED, packets, prepared, reply


def example(profile):
    p = prepared(profile)
    plan, nodes, relations = packets(prepared(core.SEMANTIC_MAP_OCCURRENCE_V7_PROFILE))
    # A second unit of the same node supports only the completed repair.
    plan['nodes'][1]['units'].append(dict(evidence=[dict(quote=REPORTED, field=2)]))
    nodes['plan_sha256'] = core.semantic_map_hash(plan)
    nodes['nodes']['n2']['units']['u2'] = dict(evidence_ref='n2.u2', source_mode='RECORDED',
        fact_parts=dict(e1='作業を終えたという報告を受けました。'), unknowns=[])
    edge = {'from': 'n1', 'to': 'n2', 'from_unit': 'n1.u1', 'to_unit': 'n2.u1'}
    if profile == core.SEMANTIC_MAP_OCCURRENCE_V9_PROFILE:
        for node in plan['nodes']:
            for i, unit in enumerate(node['units'], 1):
                parts = nodes['nodes'][node['node_id']]['units'][f'u{i}']['fact_parts']
                for j in range(len(unit['evidence'])):
                    key = core._semantic_fact_part_key(unit['evidence'], j)
                    parts[key] = parts.pop(f'e{j + 1}')
        edge.update(from_source=core._semantic_source_cues(PENDING)[0], to_source=core._semantic_source_cues(MIXED)[0])
    edge.update(label='初日は修理の完了を知らず、連絡を読んだ後も別件の相談については分からない', relation_kind='CONTEXT_CONTRAST')
    relations['nodes_sha256'] = core.semantic_map_hash(core._semantic_v4_join(plan, nodes))
    relations['edges'] = [edge]
    return p, plan, nodes, relations


def test_private_cues_admit_paraphrases_keep_both_receipts_and_preserve_public_content():
    old, old_plan, old_nodes, old_rel = example(core.SEMANTIC_MAP_OCCURRENCE_V8_PROFILE)
    p, plan, nodes, rel = example(core.SEMANTIC_MAP_OCCURRENCE_V9_PROFILE)
    new_artifact, _ = app.build_semantic_map(p, reply(p, (plan, nodes, rel)))
    old_artifact, _ = app.build_semantic_map(old, reply(old, (old_plan, old_nodes, old_rel)))
    from test_analysis_cumulative import OWNER
    for key in ('nodes', 'edges', 'overview'):
        assert new_artifact.safe_projection(authenticated_owner_scope=OWNER)[key] == (
            old_artifact.safe_projection(authenticated_owner_scope=OWNER)[key])
    for phase, value in [('NODES', nodes), ('RELATIONS', rel)]:
        wire = core.semantic_node_local_v4_messages(p, phase, plan=plan, nodes=nodes)
        assert accepts(value, wire)
    assert core.semantic_node_local_v4_relations(p, plan, nodes, rel) == (
        core.semantic_node_local_v4_relations(old, old_plan, old_nodes, old_rel))


def test_sibling_fact_cue_is_refused_while_authored_text_is_free():
    p, plan, nodes, _ = example(core.SEMANTIC_MAP_OCCURRENCE_V9_PROFILE)
    units = nodes['nodes']['n2']['units']
    wire = core.semantic_node_local_v4_messages(p, 'NODES', plan=plan)
    assert core._semantic_source_cues(REPORTED)[0] != core._semantic_source_cues(MIXED)[0]
    evidence = plan['nodes'][1]['units'][0]['evidence']
    parts = units['u1']['fact_parts']
    own_key = core._semantic_fact_part_key(evidence, 1)
    sibling_cue = core._semantic_fact_part_key(evidence, 0).split('/', 1)[1]
    parts['e2/' + sibling_cue] = parts.pop(own_key)
    with pytest.raises(core.AnalysisSemanticMapError):
        core.semantic_node_local_v4_nodes(p, plan, nodes)
    assert not accepts(nodes, wire)


@pytest.mark.parametrize('fault', ['wrong_unit', 'foreign_endpoint', 'missing_cue'])
def test_endpoint_cue_must_match_selected_unit_before_label(fault):
    p, plan, nodes, rel = example(core.SEMANTIC_MAP_OCCURRENCE_V9_PROFILE)
    wire = core.semantic_node_local_v4_messages(p, 'RELATIONS', plan=plan, nodes=nodes)
    edge = rel['edges'][0]
    if fault == 'wrong_unit':
        edge['to_unit'] = 'n2.u2'
    elif fault == 'foreign_endpoint':
        edge['from_source'] = edge['to_source']
    else:
        del edge['to_source']
    with pytest.raises(core.AnalysisSemanticMapError):
        core.semantic_node_local_v4_relations(p, plan, nodes, rel)
    assert not accepts(rel, wire)


def test_cue_is_bounded_and_verbatim_including_literal_syntax_and_unicode():
    from test_emlis_natural_reply_probe_http import probe
    for quote in ('空', '空白 " と\\改行\n、絵文字🔍の混じる前半。続いて、長い記述の後半にも「原文」がある。'):
        cues = core._semantic_source_cues(quote)
        assert cues == probe._semantic_source_cues(quote)
        assert all(cue in quote and 1 <= len(cue) <= 16 for cue in cues)

def test_fact_key_distinguishes_sibling_quotes_with_same_prefix_and_survives_literal_punctuation():
    roots = [dict(field=1, quote='先ほどの連絡では「道具」を貸す、と聞いた。'),
             dict(field=1, quote='先ほどの連絡では「道具」は戻した、と聞いた。')]
    from test_emlis_natural_reply_probe_http import probe
    for i, sibling in ((0,1),(1,0)):
        key = core._semantic_fact_part_key(roots, i)
        assert key == probe._semantic_fact_part_key(roots, i)
        cue = key.split('/', 1)[1]
        assert cue in roots[i]['quote'] and cue not in roots[sibling]['quote']
        assert len(cue) <= 8


def test_native_decoder_accepts_literal_slash_and_unicode_inside_private_fact_key():
    from test_analysis_cumulative import OWNER, source_snapshot
    quote = '「A/B🔍」を書き写した。'
    snapshot = source_snapshot(1)
    original = '記号 "A" と区切りの\\を見た。\n' + quote
    snapshot['members'][0]['original'].update(memo=original, memo_action='')
    p = app.prepare_semantic_map(OWNER, snapshot, prompt_version=core.SEMANTIC_MAP_OCCURRENCE_V9_PROFILE)
    roots = [dict(quote=quote, field=1)]
    plan = dict(schema_version=core._semantic_v4_schema('PLAN'),
        nodes=[dict(node_id='n1', units=[dict(evidence=roots)])])
    actual = dict(evidence_ref='n1.u1', source_mode='RECORDED',
        fact_parts={core._semantic_fact_part_key(roots, 0): '記号を書きました。'}, unknowns=[])
    body = dict(schema_version=core._semantic_v4_schema('NODES'), plan_sha256=core.semantic_map_hash(plan),
        nodes={'n1': dict(units={'u1': actual}, node_kind='CHOICE_OUTPUT', perspective='SELF',
                          title='記号の書き写し', meaning='')})
    wire = core.semantic_node_local_v4_messages(p, 'NODES', plan=plan)
    import json
    assert json.loads(wire[1]['content'])['fields'][0]['text'] == original
    assert accepts(body, wire)
    assert core.semantic_node_local_v4_nodes(p, plan, body) is body


@pytest.mark.parametrize('quote', ['a"b\\c\nd🔍', '"', '\\', '\n', '📗/本'])
def test_native_character_mask_round_trips_literal_fact_key(quote):
    # Normal PLAN keeps quoted originals intact in input but offers spans
    # between escape characters. Exercise even the escaped property itself.
    import json
    lmfe = pytest.importorskip('lmformatenforcer')
    from test_analysis_node_local_native_profile import advance
    from test_emlis_natural_reply_probe_http import probe

    key = core._semantic_fact_part_key([dict(quote=quote, field=1)], 0)
    raw = json.dumps({key: '自由な本文'}, ensure_ascii=False, separators=(',', ':'))
    schema = dict(type='object', properties={key: dict(type='string', minLength=1, maxLength=20)},
                  required=[key], additionalProperties=False)
    config = lmfe.CharacterLevelParserConfig(alphabet=''.join(dict.fromkeys(raw + quote + ' ')))
    config.force_json_field_order = True
    parser = probe._semantic_unique_json_schema_parser(schema, config)
    assert advance(parser, raw).can_end()
