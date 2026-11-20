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
    monkeypatch.setattr(core, 'admit_semantic_node_local_v4_nodes_response', lambda _, plan, value, **kwargs: value)
    monkeypatch.setattr(core, 'semantic_node_local_v4_relations', lambda _, plan, nodes, value, **kwargs: (plan, nodes, value))
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


def recurring_sources():
    notes = ['録音機の電源を点検した。', '録音機の電源を交換した。', '植木鉢に水を注いだ。']
    fields = [dict(field=i, field_path='memo_action', record=i, source_role='ORIGINAL_INPUT',
                   text=text, fragment_is_complete_field=True) for i, text in enumerate(notes, 1)]
    nodes = [dict(node_id=f'n{i}', units=[dict(evidence=[dict(field=i, quote=text)])])
             for i, text in enumerate(notes, 1)]
    return dict(author_phase='RELATIONS', fields=fields, candidate_nodes=nodes, qualification_candidates={})


def test_recurring_sources_require_two_records_and_unambiguous_selected_cues():
    sources = recurring_sources()
    first, second, _ = sources['fields']
    pair, = wire.comparison_candidates(sources)
    assert pair['wording'] == ['録音機', '電源']
    assert [pair[side]['record'] for side in ['left', 'right']] == [1, 2]
    for key, value in [('source_role', 'SUPPLEMENT'), ('fragment_is_complete_field', False),
                       ('field_path', 'other'), ('record', first['record']), ('supplement', 3)]:
        changed = deepcopy(sources)
        changed['fields'][1][key] = value
        assert not wire.comparison_candidates(changed)
    mixed = deepcopy(sources)
    mixed['candidate_nodes'][1]['units'][0]['evidence'].append(dict(field=3, quote=sources['fields'][2]['text']))
    assert not wire.comparison_candidates(mixed)
    duplicated = deepcopy(sources)
    duplicated['candidate_nodes'][1]['units'][0]['evidence'].append(dict(field=2, quote=second['text']))
    assert not wire.comparison_candidates(duplicated)
    assert not wire.comparison_candidates({**sources, 'map_corrections': ['訂正']})
    assert not wire.comparison_candidates({**sources, 'author_phase': 'NODES'})


def test_comparison_choices_keep_model_prose_and_each_original_skip_reason():
    sources = recurring_sources()
    pairs = wire.comparison_candidates(sources)
    codec = wire.ResponseCodec(sources, None, None, comparisons=pairs)
    logical = dict(schema_version=wire.MODEL_SCHEMA+'.relations', nodes_sha256=codec.binding,
                   qualification_review={}, edges=[], overview={})
    empty = codec.encode(logical)
    for skip in ('INSUFFICIENT_EVIDENCE', 'DIFFERENT_SUBJECT'):
        raw = dict(empty, comparisons=[skip])
        assert codec.decode(raw) == logical
        assert codec.encode(logical, comparison_decisions=raw['comparisons']) == raw
    accepted = dict(empty, comparisons=[['COMPARE', '電源の点検から交換へ進んだ。', 'CONTEXT_CONTRAST']])
    compared = codec.decode(accepted)
    assert compared['edges'] == [dict(wire.comparison_endpoints(pairs[0]), label='電源の点検から交換へ進んだ。',
                                     relation_kind='CONTEXT_CONTRAST')]
    assert codec.encode(compared, comparison_decisions=accepted['comparisons']) == accepted
    extra = dict(compared['edges'][0], to='n3', to_unit='n3.u1', to_source='植木鉢')
    assert codec.decode(dict(accepted, edges=[extra]))['edges'] == [*compared['edges'], extra]
    for decisions in ([], ['MAYBE'], ['DIFFERENT_SUBJECT'] * 2, [['COMPARE', '説明']]):
        with pytest.raises(ValueError):
            codec.decode(dict(empty, comparisons=decisions))
    with pytest.raises(ValueError):
        codec.encode(compared, comparison_decisions=empty['comparisons'])
    with pytest.raises(ValueError):
        codec.decode(dict(empty, edges=compared['edges']))
    reversed_edge = dict(compared['edges'][0])
    for suffix in ('', '_unit', '_source'):
        left, right = 'from' + suffix, 'to' + suffix
        reversed_edge[left], reversed_edge[right] = reversed_edge[right], reversed_edge[left]
    with pytest.raises(ValueError):
        codec.decode(dict(empty, edges=[reversed_edge]))


def test_paired_comparison_binds_the_subject_and_both_complete_source_sentences():
    sources = recurring_sources()
    pairs = wire.paired_comparison_candidates(sources, None)
    pair, = pairs
    assert pair['subject'] == '録音機の電源'
    assert (pair['left']['record'], pair['right']['record']) == (1, 2)
    codec = wire.ResponseCodec(sources, None, None, comparisons=pairs, paired=True)
    logical = dict(schema_version=wire.MODEL_SCHEMA + '.relations', nodes_sha256=codec.binding,
                   qualification_review={}, edges=[], overview={})
    skipped = codec.encode(logical)
    assert codec.decode(skipped) == logical
    for action, label in wire.paired_decisions(pair):
        selected = {**skipped, 'comparisons': [action]}
        value = codec.decode(selected)
        assert value['edges'][0]['label'] == label
        assert label == sources['fields'][0]['text'] + action[3] + sources['fields'][1]['text']
        assert codec.encode(value, comparison_decisions=[action]) == selected
    for invalid in (['COMPARE', '電源', 1, '一方、', 1], ['COMPARE', pair['subject'], True, '一方、', 1],
                    ['COMPARE', pair['subject'], 1, 'その結果、', 1],
                    ['COMPARE', sources['fields'][0]['text'], 'CONTEXT_CONTRAST']):
        with pytest.raises(ValueError):
            codec.decode({**skipped, 'comparisons': [invalid]})
    for role in ('SUPPLEMENT', 'CORRECTION'):
        sources['fields'][1]['source_role'] = role
        assert not wire.paired_comparison_candidates(sources, None)


def test_two_different_objects_and_a_within_day_time_phrase_are_not_a_recurring_subject():
    sources = recurring_sources()
    for index, note in enumerate(('夕食前に封筒の寸法を測った。', '出発前に脚立の寸法を測った。')):
        sources['fields'][index]['text'] = note
        sources['candidate_nodes'][index]['units'][0]['evidence'][0]['quote'] = note
    assert not wire.paired_comparison_candidates(sources, None)
    codec = wire.ResponseCodec(sources, None, None, paired=True)
    logical = dict(schema_version=wire.MODEL_SCHEMA + '.relations', nodes_sha256=codec.binding,
                   qualification_review={}, edges=[], overview={})
    accepted = codec.encode(logical)
    first, second = [r['text'] for r in sources['fields'][:2]]
    edge = dict(from_unit='n1.u1', to_unit='n2.u1', from_source=first[:16], to_source=second[:16],
                label=first+'一方、'+second, relation_kind='CONTEXT_CONTRAST')
    edge.update({'from':'n1','to':'n2'})
    with pytest.raises(ValueError):
        codec.decode({**accepted, 'edges': [edge]})

    for label,accepted_label in [(first + 'と考えた。',False), (first + '脚立。',False),
            ('封筒と脚立を調べた。',False), ('封筒の寸法を測ったことと、脚立の寸法を測ったことを読み分けた。',True)]:
        candidate = dict(edge,relation_kind='SHARED_MEANING',label=label)
        if accepted_label:
            assert codec.decode({**accepted, 'edges':[candidate]})['edges']==[candidate]
        else:
            with pytest.raises(ValueError):
                codec.decode({**accepted, 'edges':[candidate]})


def test_decision_comparisons_use_the_object_of_the_action_and_allow_skipping():
    previous = '前に調べた顕微鏡についてもう一度考えた。'
    notes = ['顕微鏡の状態を調べた。条件が合わず購入せず、記録だけ残した。',
             '設置台の準備を済ませて顕微鏡を購入した。', '薬品の価格を記録した。']
    material = recurring_sources()
    for field, node, note in zip(material['fields'], material['candidate_nodes'], notes):
        field['text'] = note
        node['units'][0]['evidence'][0]['quote'] = note
    material['fields'][1]['text'] = previous + notes[1]
    candidate, = wire.paired_comparison_candidates(material, None, decision_sources=True)
    assert candidate['subject'] == '顕微鏡'
    assert candidate['left']['sentences'] == ['条件が合わず購入せず、記録だけ残した。']
    assert candidate['right']['sentences'] == [notes[1]]
    codec = wire.ResponseCodec(material, None, None, comparisons=[candidate], paired=True, decision_sources=True)
    logical = dict(schema_version=wire.MODEL_SCHEMA + '.relations', nodes_sha256=codec.binding,
                   qualification_review={}, edges=[], overview={})
    compact = codec.encode(logical)
    for skip in wire.COMPARISON_SKIPS:
        assert codec.decode(dict(compact, comparisons=[skip]))['edges'] == []
    for decision, label in wire.paired_decisions(candidate):
        sources = {}
        physical = dict(compact, comparisons=[decision])
        edge, = codec.decode(physical, comparison_sources=sources)['edges']
        assert edge['label'] == label and notes[1] in label
        left, right = sources[(edge['from_unit'], edge['to_unit'], label)]
        assert left == (1, notes[0], '条件が合わず購入せず、記録だけ残した。')
        assert right == (2, notes[1], notes[1])
        old_codec = wire.ResponseCodec(material, None, None, comparisons=[candidate], paired=True)
        prior_sources = {}
        assert old_codec.decode(physical, comparison_sources=prior_sources)['edges'] == [edge]
        assert prior_sources == {}
    # A supported pair outside the offered decisions also binds its two chosen sentences in either direction.
    free = wire.ResponseCodec(material, None, None, paired=True, decision_sources=True)
    for swapped in (False, True):
        row = dict(candidate, left=candidate['right'], right=candidate['left']) if swapped else candidate
        decision, label = wire.paired_decisions(row)[0]
        edge = dict(wire.comparison_endpoints(row), label=label, relation_kind='CONTEXT_CONTRAST')
        sources = {}
        physical = dict(free.encode(logical), edges=[edge])
        assert free.decode(physical, comparison_sources=sources)['edges'] == [edge]
        left, right = sources[(edge['from_unit'], edge['to_unit'], label)]
        assert (left, right) == tuple((row[side]['field'], row[side]['quote'], row[side]['sentences'][0])
                                      for side in ('left', 'right'))
        with pytest.raises(ValueError):
            free.decode(dict(physical, edges=[dict(edge, label='別の内容')]))
        with pytest.raises(ValueError):
            codec.decode(dict(compact, comparisons=['INSUFFICIENT_EVIDENCE'], edges=[edge]))
    other = '顕微鏡の状態を調べた。条件が合わず容器を購入せず、記録だけ残した。'
    material['fields'][0]['text'] = other
    material['candidate_nodes'][0]['units'][0]['evidence'][0]['quote'] = other
    assert not wire.paired_comparison_candidates(material, None, decision_sources=True)


def test_same_recipient_and_partial_spelling_need_the_same_requested_object_in_both_records():
    message = '受付への部品依頼を提案したが、送信したかは分からない。'
    reply = '家族から食品の依頼連絡に返事をした。'
    row = dict(subject='受付', subject_witness=dict(kind='companion', quote='家族から食品を受付へ頼んだと聞いた。'),
               left=dict(record=1, sentences=[message]), right=dict(record=2, sentences=[reply]))
    original = {1: [(1, message, message)], 2: [(3, reply, '家族から食品を受付へ頼んだと聞いた。' + reply)]}
    assert wire._decision_endpoints(row, original) is None
    row['right']['sentences'] = ['家族から交換部品の依頼連絡に返事をした。']
    original[1].append((1, '欲しいのは交換の部品だと伝えた。', '欲しいのは交換の部品だと伝えた。\n 家族はその依頼を受付へ送ると答えた。'))
    result = wire._decision_endpoints(row, original)
    assert result['object_witnesses'][0]['object'] == '交換部品'
    assert result['object_witnesses'][0]['quote'] == original[1][1][2]


def test_comparison_witness_preserves_original_inter_sentence_spacing():
    source = recurring_sources()
    first, second = '受付用の資料をそろえた。', '受付へ知らせた。'
    source['fields'][0]['text'] = first + '\n  ' + second
    import analysis_plan_source_choices as choices
    windows = wire._comparison_originals(source, choices)[1]
    assert (1, first, first + '\n  ' + second) in windows
    assert all(span in source['fields'][0]['text'] for _, _, span in windows)


def test_same_requested_item_is_named_instead_of_the_recipient_and_witnesses_keep_both_roles():
    left = '窓口への部品依頼を提案したが、渡したかは確認していない。'
    right = '同僚の交換部品の依頼連絡に返事をした。'
    context = '壊れた器具の交換の部品も頼みたいと提案した。'
    follow = '担当者はその依頼を窓口へ送ると言った。'
    response = '同僚から交換部品を窓口へ頼んだと連絡があった。'
    candidate = dict(subject='窓口', wording=['依頼'], subject_witness=dict(kind='companion'),
                     left=dict(record=1, quote=left, sentences=[left]), right=dict(record=2, quote=right, sentences=[right]))
    originals = {1: [(1, context, context + '\n ' + follow)], 2: [(3, response, response)]}
    row = wire._decision_endpoints(candidate, originals, named_requests=True)
    assert row['subject'] == '交換部品' and row['decision_pairs'] == [[1, 1]]
    assert row['subject_witness'] == dict(kind='requested_object', recipient='窓口',
        left=dict(field=1, quote=context + '\n ' + follow), right=dict(field=3, quote=response))
    options = wire.paired_decisions(row)
    assert options and all(a[1] == '交換部品' and a[1] != '窓口' and left in label and right in label for a,label in options)
    assert wire._decision_endpoints(candidate, originals)['subject'] == '窓口'

    material = recurring_sources()
    for field, node, quote, text in zip(material['fields'][:2], material['candidate_nodes'][:2],
                (left, right), (context + '\n ' + follow + left, response + right), strict=True):
        field['text'] = text
        node['units'][0]['evidence'][0]['quote'] = quote
    captured, = wire.paired_comparison_candidates(material, None, decision_sources=True, named_requests=True)
    assert (captured['subject'], captured['subject_witness']['recipient']) == ('交換部品', '窓口')
    assert all(side['quote'] in material['fields'][side['field']-1]['text'] for side in
               (captured['subject_witness']['left'], captured['subject_witness']['right']))
    codec = wire.ResponseCodec(material, None, None, comparisons=[captured], paired=True,
                               decision_sources=True, named_requests=True)
    logical = dict(schema_version=wire.MODEL_SCHEMA + '.relations', nodes_sha256=codec.binding,
                   qualification_review={}, edges=[], overview={})
    blank = codec.encode(logical)
    for skip in wire.COMPARISON_SKIPS:
        assert codec.decode(dict(blank, comparisons=[skip]))['edges'] == []
    for action, label in wire.paired_decisions(captured):
        edge, = codec.decode(dict(blank, comparisons=[action]))['edges']
        assert edge['label'] == label
        with pytest.raises(ValueError):
            codec.decode(dict(blank, comparisons=[['COMPARE', '窓口', *action[2:]]]))

    # A mention and a separate request for another item do not establish what was requested.
    wrong = '交換の部品を調べた。'
    originals[1] = [(1, wrong, wrong + '担当者は別の申請を窓口へ送った。')]
    assert wire._decision_endpoints(candidate, originals, named_requests=True) is None
    originals[1] = [(1, context, context + '\n\n' + follow)]
    assert wire._decision_endpoints(candidate, originals, named_requests=True) is None


def test_different_documents_for_same_recipient_are_not_one_subject_even_if_another_request_mentions_both():
    first = '印刷会社への契約書依頼を提案したが、送信したかは分からない。'
    second = '同僚の請求書の依頼連絡に返事をした。'
    other = '別件の請求書を印刷会社に頼んだ。'
    next_day = '同僚から請求書を印刷会社に頼んだと聞いた。'
    row = dict(subject='印刷会社', wording=['依頼'], subject_witness=dict(kind='companion'),
               left=dict(record=1, quote=first, sentences=[first]), right=dict(record=2, quote=second, sentences=[second]))
    originals = {1:[(1, first, first), (1, other, other)], 2:[(3, next_day, next_day)]}
    assert wire._decision_endpoints(row, originals, named_requests=True) is None
