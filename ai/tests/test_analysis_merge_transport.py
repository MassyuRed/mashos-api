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


def packets(monkeypatch, version=wire.RECORD_VERSION):
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


@pytest.mark.parametrize('version', [wire.LEGACY_VERSION, wire.RECORD_VERSION])
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
    for version in wire.VERSIONS:
        messages = core.semantic_node_local_v4_wire_messages(merge, wire_version=version)
        strict = version != wire.LEGACY_VERSION
        codec = wire.response_codec(messages)
        assert accepts(codec.encode(compared) if codec else compared, messages)
        assert core.admit_semantic_node_local_v4_plan_response(merge, compared, merge_anchors=strict)
        for raw in (mixed, mixed_unit):
            assert accepts(codec.encode(raw) if codec else raw, messages) is not strict
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
    messages = core.semantic_node_local_v4_wire_messages(merge)
    assert accepts(wire.response_codec(messages).encode(raw), messages)
    assert core.admit_semantic_node_local_v4_plan_response(merge, raw, merge_anchors=True)


def test_v3_response_binding_and_original_text_collisions():
    quotes = ['~同じ語', '~同…語', '朝の計画で道具を運ばなかった。',
              '朝の計画でメモを運ばなかった。', '朝の別件で道具を運ばなかった。']
    codes = wire._quote_codes(quotes)
    assert len(set(codes.values())) == len(quotes)
    assert codes['~同…語'] == '~~同…語'
    assert codes == wire._quote_codes(reversed(quotes))
    assert any('…' in code for quote, code in codes.items() if len(quote) > 8)

    from test_analysis_occurrence_v17_record_owners import packet
    quote = '隣の畑で照明を点検した。'
    stage = source_merge([quote])
    messages = core.semantic_node_local_v4_wire_messages(stage)
    codec = wire.response_codec(messages)
    original = packet(stage, [[[(1, quote)]]])
    raw = codec.encode(original)
    assert codec.decode(raw) == original
    assert list(raw) == ['h', 'n']
    for bad in ({'h': '0' * 64, 'n': raw['n']}, {**raw, 'extra': True},
                {**raw, 'n': [[[[codec.quote_code(quote), True]]]]},
                {**raw, 'n': [[[['~does-not-exist', 1]]]]}):
        with pytest.raises(ValueError):
            codec.decode(bad)
    for version in (wire.LEGACY_VERSION, wire.RECORD_VERSION):
        assert wire.response_codec(core.semantic_node_local_v4_wire_messages(stage, wire_version=version)) is None


def test_v3_nodes_reconstructs_only_the_roots_bound_to_its_request():
    from test_analysis_occurrence_v17_record_owners import packet
    quote, other = '隣の畑で照明を点検した。', '同じ日に別の店で机を選んだ。'
    stage = source_merge([quote, other])
    plan = core.admit_semantic_node_local_v4_plan_response(stage, packet(stage, [[[(1, quote)]], [[(2, other)]]]),
                                                            merge_anchors=True)
    original = core.semantic_node_local_v4_messages(stage, 'NODES', plan=plan)
    wire_nodes = core.semantic_node_local_v4_wire_messages(stage, 'NODES', plan=plan)
    codec = wire.response_codec(wire_nodes)
    display = json.loads(wire_nodes[1]['content'])
    assert display['plan']['nodes'][0]['units'][0]['evidence'] == 1
    assert display['evidence_parts_by_unit']['n1.u1']['e1']['quote'] == quote
    assert wire.legacy_messages(wire_nodes) == original
    raw = dict(h=codec.binding, n=[[[['RECORDED', [i], []]], 'STATE_CONTEXT', 'SELF', q, '']
                                   for i, q in enumerate((quote, other), 1)])
    logical = codec.decode(raw)
    assert codec.encode(logical) == raw
    for n, q in enumerate((quote, other), 1):
        unit = logical['nodes'][f'n{n}']['units']['u1']
        assert unit['evidence_ref'] == f'n{n}.u1'
        assert list(unit['fact_parts'].values()) == [n]
        assert list(unit['fact_parts'])[0].startswith('e1/')
    swapped = deepcopy(logical)
    swapped['nodes']['n1']['units']['u1']['evidence_ref'] = 'n2.u1'
    with pytest.raises(ValueError):
        codec.encode(swapped)
    missing = deepcopy(raw)
    missing['n'][0][0][0][1].clear()
    with pytest.raises(ValueError):
        codec.decode(missing)
    display['plan']['nodes'][0]['units'][0]['evidence'] = 2
    with pytest.raises(ValueError):
        wire.legacy_messages([wire_nodes[0], dict(wire_nodes[1], content=wire.compact_json(display))])


def test_relation_fact_keeps_the_exact_selected_parts_and_qualifications():
    messages = fixture('RELATIONS')
    material = json.loads(messages[1]['content'])
    roots = [dict(field=3, quote='返事が来るか未確認だった。'), dict(field=4, quote='翌日返事が届いた。')]
    unit = dict(evidence=roots, fact='来るか未確認だった。翌日返事が届いた。', source_mode='RECORDED',
                unknowns=[dict(source_quote='返事が来るか未確認だった。', source_field=3)])
    material.update(fact_part_overrides={'n1.u1.e1': '来るか未確認だった。'},
                    candidate_nodes=[dict(node_id='n1', units=[unit])])
    messages[1]['content'] = wire.compact_json(material)
    physical = wire.prepare_messages(messages)
    view = json.loads(physical[1]['content'])
    assert view['candidate_nodes'][0]['units'][0] == {**unit, 'fact': 0}
    assert wire.legacy_messages(physical) == messages
    view['fact_part_overrides']['n1.u1.e1'] = '返事が来た。'
    with pytest.raises(ValueError):
        wire.legacy_messages([physical[0], dict(physical[1], content=wire.compact_json(view))])
    unit['fact'] = '作者による別の本文'
    messages[1]['content'] = wire.compact_json(material)
    physical = wire.prepare_messages(messages)
    assert json.loads(physical[1]['content'])['candidate_nodes'][0]['units'][0] == unit
    assert wire.legacy_messages(physical) == messages


def test_source_ranges_qualifications_and_unread_spans_round_trip_without_changing_owners():
    quote = '市役所に確認を依頼したが、返事が戻ったかはまだ分からない。'
    start = 19
    text = '本人のメモ。' + quote + '同じ日に別の話をした。'
    fields = {i: dict(text=text, fragment_scalar_range=[start, start + len(text)]) for i in (3, 7)}
    first = dict(source_field=3, source_quote=quote)
    second = dict(source_field=7, source_quote=quote)
    unit = dict(evidence=[dict(field=3, quote=quote)], unknowns=[first, second])
    material = dict(author_phase='RELATIONS', candidate_nodes=[dict(node_id='n1', units=[unit])],
                    qualification_candidates={'first': dict(first), 'second': dict(second)})
    original = deepcopy(material)
    wire._visible_sources(material, fields)
    ref = unit['evidence'][0]['quote']
    assert ref[:2] == [start + text.index(quote), start + text.index(quote) + len(quote)]
    assert material['qualification_candidates'] == {'first': [1, 1, 1], 'second': [1, 1, 2]}
    corrupt = deepcopy(material)
    corrupt['candidate_nodes'][0]['units'][0]['unknowns'][0]['source_quote'][2] = 'changed'
    with pytest.raises(ValueError):
        wire._visible_sources(corrupt, fields, unpack=True)
    wire._visible_sources(material, fields, unpack=True)
    assert material == original

    ranges = [[i*6, i*6+5] for i in range(30)] + [[181, 185], [185, 187]]
    duties = dict(source_duties=dict(unassessed_source_ranges=[dict(field=7, ranges=ranges)]))
    original = deepcopy(duties)
    wire._range_lengths(duties)
    assert duties['source_duties']['unassessed_source_ranges'][0]['ranges']['gaps'] == [[30, 2], [31, 0]]
    wire._range_lengths(duties, unpack=True)
    assert duties == original


def test_relation_review_references_bind_each_open_quote_and_closed_decision():
    import analysis_plan_source_choices as choices
    a = '返答がないので実施日を知らない。予定変更の理由も不明だった。'
    b = '二番目の資料を受け取ったかはその時点で分からなかった。'
    registry = [{'node_id': 'n1'}, {'node_id': 'n2'}]
    material = dict(author_phase='RELATIONS', candidate_nodes=registry, qualification_candidates={
        'q1/時点': {'source_quote': a}, 'q2/受取': {'source_quote': b}, 'q3/保留': {'source_quote': a},
        'q4/既往': {'source_quote': b}, 'q5/重複': {'source_quote': b}})
    codec = wire.ResponseCodec(material, choices, None)
    later = '予定変更の理由も不明だった。'
    logical = dict(schema_version=wire.MODEL_SCHEMA+'.relations', nodes_sha256=codec.binding,
        qualification_review={'q1/時点': dict(status='OPEN', source_quote=later),
            'q2/受取': dict(status='OPEN', source_quote=b), 'q3/保留': dict(status='STATED'),
            'q4/既往': dict(status='EARLIER'), 'q5/重複': dict(status='DUPLICATE')},
        edges=[], overview=dict(node_refs=['n1', 'n2'], title='検証'))
    compact = codec.encode(logical)
    assert compact['qualification_review'] == [[codec.quote_code(later)], [0], 'STATED', 'EARLIER', 'DUPLICATE']
    assert codec.decode(compact) == logical
    for bad in ([True], [1], [codec.quote_code(b)], [], 'OPEN', 'UNKNOWN'):
        changed = deepcopy(compact)
        changed['qualification_review'][1] = bad
        with pytest.raises(ValueError):
            codec.decode(changed)
    broken = {**compact, 'qualification_review': compact['qualification_review'][:-1]}
    with pytest.raises(ValueError):
        codec.decode(broken)


def test_qualification_ordinals_survive_sorted_request_keys():
    import analysis_plan_source_choices as choices
    items = {f'q{i}/留保': dict(source_quote=f'{i}番の留保。') for i in range(1, 13)}
    material = dict(author_phase='RELATIONS', candidate_nodes=[], qualification_candidates=dict(sorted(items.items())))
    codec = wire.ResponseCodec(material, choices, None)
    assert list(dict(codec.qualification_items)) == list(items)
