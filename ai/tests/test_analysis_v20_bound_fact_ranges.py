"""Every generated fact resolves against its own original, even with four dense roots."""
from copy import deepcopy
import json

import pytest

from analysis_plan_source_choices import source_fact_ranges
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from test_analysis_node_local_native_profile import accepts, probe
from test_analysis_occurrence_v14_visible_closers import stages


V20 = core.SEMANTIC_MAP_OCCURRENCE_V20_PROFILE


def request(pieces):
    prepared, plan, raw = stages(''.join(pieces), profile=V20)
    roots = [dict(field=1, quote=piece) for piece in pieces]
    plan['nodes'][0]['units'][0]['evidence'] = roots
    raw['plan_sha256'] = core.semantic_map_hash(['analysis.node-facts.v1', 'NODES', prepared.request_ref, plan])
    node = raw['nodes']['n1']
    node['title'] = '記録した行動'
    parts = {core._semantic_fact_part_key(roots, i): i + 1 for i in range(len(roots))}
    node['units']['u1']['fact_parts'] = parts
    messages = core.semantic_node_local_v4_messages(prepared, 'NODES', plan=plan)
    return prepared, plan, raw, parts, messages


def test_each_compact_source_survives_sibling_budget_and_receipt_scope():
    # The action includes both the first attempt and the later practice.
    action = '装置を点検して試運転を止めた。昼間には窓辺で一時間ほど下絵を描き、夜の作業にはまだ使っていない。'
    pieces = [action, '最初の計測では' + '端の線が暗く見え、' * 9 + '照度の違いを記録した。',
              '買い替え前の条件は' + '寸法と値段、' * 12 + '保証の範囲だった。',
              "元の記録の欄名は ,'unit': [2]、私は「@4」を消さずに残した。"]
    p, plan, raw, parts, messages = request(pieces)
    saved = deepcopy(raw)
    assert accepts(raw, messages)
    assert list(json.loads(messages[1]['content'])['evidence_parts_by_unit']['n1.u1'].values())[0]['fact_ref'] == 1
    canonical = core.admit_semantic_node_local_v4_nodes_response(p, plan, raw)
    unit = canonical['nodes']['n1']['units']['u1']
    assert list(unit['fact_parts'].values()) == pieces
    assert core._semantic_unit_fact(unit) == ''.join(pieces)
    assert core._semantic_v4_join(plan, canonical)[0]['units'][0]['fact'] == ''.join(pieces)
    rel = core.semantic_node_local_v4_messages(p, 'RELATIONS', plan=plan, nodes=canonical)
    assert probe.semantic_output_schema(rel)
    assert raw == saved
    key = next(iter(parts))
    for invalid in (2, True, '@1', pieces[1], ",'e4/別の記録': 1", '42/別文', '</part>'):
        parts[key] = invalid
        assert not accepts(raw, messages)
        with pytest.raises(core.AnalysisSemanticMapError):
            core.admit_semantic_node_local_v4_nodes_response(p, plan, raw)
    canonical['nodes']['n1']['units']['u1']['fact_parts'][key] = '無関係な表示'
    with pytest.raises(core.AnalysisSemanticMapError):
        core.semantic_node_local_v4_nodes(p, plan, canonical)


def test_long_source_ranges_dispatch_to_exact_text_and_preserve_literal_delimiters():
    long = ('箱の説明では' + '目盛りの数と材料、' * 10 + '数字は「3:2」だった。'
            + '担当者から、' + '試作と照合を行い、' * 9 + '夜の作業はいったん中断したと連絡があった。')
    p, plan, raw, parts, messages = request([long])
    key, = parts
    options = source_fact_ranges(long)
    assert options and all(0 < len(v) <= 160 for v in options.values())
    for ref, text in options.items():
        parts[key] = ref
        assert accepts(raw, messages)
        lookup = probe._semantic_wire_fact_sources(messages)
        assert lookup['n1.u1', key, ref] == text
        canon = core.admit_semantic_node_local_v4_nodes_response(p, plan, raw)
        assert canon['nodes']['n1']['units']['u1']['fact_parts'][key] == text
    assert any('中断したと連絡があった。' in text for text in options.values())
    for invalid in ('@1:160', '架空の要約', 1):
        parts[key] = invalid
        assert not accepts(raw, messages)
        with pytest.raises(core.AnalysisSemanticMapError):
            core.admit_semantic_node_local_v4_nodes_response(p, plan, raw)


def test_single_overlong_sentence_uses_visible_cut_marks_and_covers_unicode_source():
    note = '左端😀' + '紙に英字©と【右側】を記したが、' * 17 + '一度も送っていない。'
    options = source_fact_ranges(note)
    spans = [tuple(map(int, ref[1:].split(':'))) for ref in options]
    assert spans[0][0] == 0 and spans[-1][1] == len(note)
    assert [b for _, b in spans[:-1]] == [a for a, _ in spans[1:]]
    assert list(options.values())[0].endswith('…')
    assert list(options.values())[-1].startswith('…')
    for (start, end), text in zip(spans, options.values(), strict=True):
        assert len(text) <= 160 and text.strip('…') == note[start:end]
