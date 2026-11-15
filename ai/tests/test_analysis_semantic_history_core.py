"""Bounded history synthesis tests use synthetic outputs, not quality ratings."""
from copy import deepcopy
from dataclasses import replace
import json

import pytest

import analysis_semantic_map as application
from cocolon_meaning_experience_engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from test_analysis_cumulative import OWNER, source_snapshot
from test_analysis_semantic_map import sample, candidate, response


def parent(snapshot=None, profile=core.SEMANTIC_MAP_PROFILE):
    return application.prepare_semantic_map(OWNER, sample() if snapshot is None else snapshot,
        prompt_version=profile)


def packet_for(fields, *, unknowns=()):
    return dict(schema_version=core.SEMANTIC_MAP_MODEL_SCHEMA,
        overview=dict(title='それぞれの記録', summary='記録に書かれた内容を分けて読みます。'),
        nodes=[dict(node_id='n1', node_kind='STATE_CONTEXT', title='記録に書かれた場面',
            summary='この記録の記述を参照しています。', explanation='記載された範囲からの仮の読みです。',
            perspective='SELF', unknowns=list(unknowns), evidence=fields)], edges=[])


def standard_leaves(prepared):
    result = []
    for index, member in enumerate(prepared.frozen.members):
        stage = core.prepare_semantic_leaf(prepared, (member.saved_record_ref,))
        packet = candidate()
        packet['nodes'] = [packet['nodes'][index]]
        packet['nodes'][0]['node_id'] = 'n1'
        packet['edges'] = []
        result.append((stage, response(stage, packet)))
    return tuple(result)


@pytest.mark.parametrize('profile', [core.SEMANTIC_MAP_PROFILE, core.SEMANTIC_MAP_SOURCE_DUTIES_PROFILE])
def test_global_fields_complete_record_leaf_and_final_parent_map_share_one_realizer(profile, monkeypatch):
    from cocolon_meaning_experience_engine.cores.analysis import observed_route_realizer
    prepared = parent(profile=profile)
    original = deepcopy(prepared)
    leaves = standard_leaves(prepared)
    calls = []
    realizer = observed_route_realizer.realize_analysis_semantic_map
    monkeypatch.setattr(observed_route_realizer, 'realize_analysis_semantic_map',
        lambda graph: (calls.append(graph), realizer(graph))[1])
    for stage, receipt in leaves:
        assert stage.parent == prepared and stage.source_guard == prepared.source_guard
        material = json.loads(stage.material_json)
        assert [f['field'] for f in material['fields']] == ([1] if stage == leaves[0][0] else [2, 3])
        graph = core.build_semantic_stage(stage, receipt)
        assert json.loads(graph.coverage_json)['processed_count'] == 1
        assert json.loads(graph.coverage_json)['mapped_count'] == 1
        assert not calls
    merge = core.prepare_semantic_merge(prepared, leaves)
    result = MeaningExperienceEngine().generate(prepared.request,
        semantic_input=replace(merge, response=response(merge)))
    assert len(calls) == 1
    assert result.coverage['processed_count'] == result.coverage['mapped_count'] == 2
    assert result.coverage['unparsed_count'] == 0
    projection = result.artifact.safe_projection(authenticated_owner_scope=OWNER)
    assert projection['wire_kind'] == 'watashi.map.v3' and len(projection['edges']) == 1
    private = result.artifact.private_evidence()
    assert private['source_guard'] == prepared.source_guard
    assert private['request_ref'] == merge.request_ref
    assert private['messages_sha256'] == core.semantic_map_hash(merge.messages())
    assert private['response_sha256'] == response(merge).raw_sha256
    assert len(private['graph']['meaning_review']['history_synthesis']['leaf_receipts']) == 2
    assert prepared == original


@pytest.mark.parametrize('refs', [(), [], ('unknown',), (True,), ('same', 'same')])
def test_invalid_leaf_partition_never_becomes_material(refs):
    with pytest.raises(core.AnalysisSemanticMapError, match='partition_invalid'):
        core.prepare_semantic_leaf(parent(), refs)


def test_leaf_cannot_graft_an_unshown_parent_field():
    prepared = parent()
    stage = standard_leaves(prepared)[0][0]
    packet = packet_for([dict(field=3, quote='私は意見を言わなかった')])
    with pytest.raises(core.AnalysisSemanticMapError, match='evidence_not_shown'):
        core.build_semantic_stage(stage, response(stage, packet))


@pytest.mark.parametrize('mutation', [
    lambda s: replace(s, material_json=s.material_json.replace('価値観', '架空場面')),
    lambda s: replace(s, request_ref='analysis-semantic-stage:' + '0' * 64),
    lambda s: replace(s, record_refs=tuple(reversed(s.parent.frozen.members))),
    lambda s: replace(s, parent=replace(s.parent, source_count=999)),
])
def test_leaf_rederives_parent_and_stage_before_admitting_external_raw(mutation):
    stage = mutation(standard_leaves(parent())[0][0])
    with pytest.raises((core.AnalysisSemanticMapError, TypeError)):
        core.build_semantic_stage(stage, response(stage, packet_for([dict(field=1, quote='自分が納得して選びたい')])))


@pytest.mark.parametrize('selection', [lambda l: l[:1], lambda l: l[::-1], lambda l: (l[0], l[0]),
    lambda l: l + l, lambda l: [*l]])
def test_merge_requires_all_parent_records_once_and_bounded_order(selection):
    prepared = parent()
    with pytest.raises(core.AnalysisSemanticMapError, match='partition_invalid'):
        core.prepare_semantic_merge(prepared, selection(standard_leaves(prepared)))


def test_merge_inherits_scoped_unknowns_without_rewriting_a_correct_paraphrase_or_raw():
    prepared = parent()
    merge = core.prepare_semantic_merge(prepared, standard_leaves(prepared))
    packet = candidate()
    paraphrase = 'その場で黙っていた理由はまだ分からない'
    packet['nodes'][1]['unknowns'] = [paraphrase]
    original = deepcopy(packet)
    receipt = response(merge, packet)
    raw = receipt.raw
    result = core.build_semantic_stage(merge, receipt)
    assert packet == original and receipt.raw == raw
    projection = result.artifact.safe_projection(authenticated_owner_scope=OWNER)
    old_unknown = 'その場で意見を伝えなかった理由'
    assert projection['nodes'][1]['unknowns'] == [paraphrase, old_unknown]
    visible = result.artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text']
    assert paraphrase in visible and old_unknown in visible
    private = result.artifact.private_evidence()
    assert private['response_sha256'] == receipt.raw_sha256
    assert private['messages_sha256'] == receipt.messages_sha256
    retained = result.artifact.private_evidence()['graph']['meaning_review']['history_synthesis']
    assert retained['scoped_unknowns'][0]['unknowns'] == [old_unknown]
    assert retained['full_source_semantic_coverage'] is False
    inherited, = retained['inherited_unknowns']
    assert inherited['text'] == old_unknown and inherited['added_to_final']
    assert inherited['node_ref'] == 'n2' and inherited['status'] == 'INHERITED_AI_UNASSESSED'
    node = private['graph']['nodes'][1]
    assert set(inherited['matched_final_evidence_ids']) <= {r['evidence_id'] for r in node['evidence_refs']}
    assert inherited['source_evidence_refs'] == [core._semantic_map_evidence(prepared, e)[1]
        for e in retained['scoped_unknowns'][0]['evidence']]
    assert 'INHERITED_AI_UNASSESSED' not in core.semantic_map_canonical(projection)
    # An exact existing unknown is retained once; no synonym guess or cutoff.
    exact = core.build_semantic_stage(merge, response(merge))
    assert exact.artifact.safe_projection(authenticated_owner_scope=OWNER)['nodes'][1]['unknowns'] == [old_unknown]
    assert not exact.artifact.private_evidence()['graph']['meaning_review']['history_synthesis']['inherited_unknowns'][0]['added_to_final']


def test_unknowns_do_not_cross_unrelated_source_scopes_and_above_four_is_rejected():
    prepared = parent()
    merge = core.prepare_semantic_merge(prepared, standard_leaves(prepared))
    packet = candidate()
    packet['nodes'] = packet['nodes'][:1]
    packet['edges'] = []
    result = core.build_semantic_stage(merge, response(merge, packet))
    assert result.artifact.safe_projection(authenticated_owner_scope=OWNER)['nodes'][0]['unknowns'] == []
    assert result.artifact.private_evidence()['graph']['meaning_review']['history_synthesis']['inherited_unknowns'] == []
    packet = candidate()
    packet['nodes'][1]['unknowns'] = ['追加の未確認' + str(i) for i in range(4)]
    original = deepcopy(packet)
    receipt = response(merge, packet)
    with pytest.raises(core.AnalysisSemanticMapError, match='unknown_capacity_exceeded'):
        core.build_semantic_stage(merge, receipt)
    assert packet == original and json.loads(receipt.raw) == original


def test_complete_merge_fields_use_the_exact_message_budget_and_preserve_unquoted_source(monkeypatch):
    import analysis_model_source as sources
    assert core.SEMANTIC_HISTORY_MERGE_MAX_PROMPT_BYTES == sources.SEMANTIC_MERGE_MAX_PROMPT_BYTES == 98304
    snapshot = source_snapshot(2)
    snapshot['members'][0]['original'].update(memo='私は返事を待った。', memo_action='返事の前に資料を見た。')
    snapshot['members'][1]['original'].update(memo='私は話した。', memo_action='')
    prepared = parent(snapshot)
    original = deepcopy(prepared)
    leaves = []
    for member in prepared.frozen.members:
        leaf = core.prepare_semantic_leaf(prepared, (member.saved_record_ref,))
        field = json.loads(leaf.material_json)['fields'][0]
        leaves.append((leaf, response(leaf, packet_for([dict(field=field['field'], quote=field['text'])]))))
    leaves = tuple(leaves)
    merge = core.prepare_semantic_merge(prepared, leaves)
    material = json.loads(merge.material_json)
    originals = json.loads(prepared.material_json)['fields']
    assert [{k: v for k, v in field.items() if k not in {
        'fragment_scalar_range', 'fragment_is_complete_field', 'semantic_coverage'}}
        for field in material['fields']] == originals
    assert all(field['fragment_scalar_range'] == [0, len(field['text'])]
        and field['fragment_is_complete_field'] and field['semantic_coverage'] == 'UNASSESSED'
        for field in material['fields'])
    assert material['omitted_ranges'] == []
    assert material['history_coverage']['full_source_semantic_coverage'] is False
    # The complete source includes a field that no leaf selected as evidence.
    packet = packet_for([dict(field=2, quote='返事の前に資料を見た。')])
    result = core.build_semantic_stage(merge, response(merge, packet))
    assert result.coverage['mapped_count'] == 1 and result.coverage['unparsed_count'] == 1
    assert result.artifact.private_evidence()['graph']['meaning_review']['history_synthesis'][
        'full_source_semantic_coverage'] is False
    byte_count = sources._semantic_message_bytes(merge)
    assert byte_count == len(core.semantic_map_canonical(merge.messages()).encode('utf-8'))
    # Pad only the system control text. Person source stays short and intact;
    # receipts are rebound after each instruction change, before consumption.
    instruction = core._SEMANTIC_MAP_INSTRUCTION
    padded = instruction + 'x' * (sources.SEMANTIC_MERGE_MAX_PROMPT_BYTES - byte_count)
    monkeypatch.setattr(core, '_SEMANTIC_MAP_INSTRUCTION', padded)
    boundary_leaves = tuple((leaf, response(leaf, json.loads(receipt.raw))) for leaf, receipt in leaves)
    boundary = core.prepare_semantic_merge(prepared, boundary_leaves)
    assert sources._semantic_message_bytes(boundary) == sources.SEMANTIC_MERGE_MAX_PROMPT_BYTES
    assert json.loads(boundary.material_json)['omitted_ranges'] == []
    core.build_semantic_stage(boundary, response(boundary, packet))
    monkeypatch.setattr(core, '_SEMANTIC_MAP_INSTRUCTION', padded + 'x')
    fallback_leaves = tuple((leaf, response(leaf, json.loads(receipt.raw))) for leaf, receipt in leaves)
    fallback = core.prepare_semantic_merge(prepared, fallback_leaves)
    assert sources._semantic_message_bytes(fallback) <= sources.SEMANTIC_MERGE_MAX_PROMPT_BYTES
    fallback_material = json.loads(fallback.material_json)
    assert [field['field'] for field in fallback_material['fields']] == [1, 3]
    assert fallback_material['omitted_ranges'] == [dict(field=2,
        ranges=[[0, len(originals[1]['text'])]], reason='NO_LEAF_EVIDENCE')]
    assert fallback_material['history_coverage'] == material['history_coverage']
    with pytest.raises(core.AnalysisSemanticMapError, match='evidence_not_shown'):
        core.build_semantic_stage(fallback, response(fallback, packet))
    forged = replace(fallback, material_json=boundary.material_json)
    with pytest.raises(core.AnalysisSemanticMapError, match='stage_unbound'):
        core.build_semantic_stage(forged, response(forged, packet))
    assert prepared == original


def test_complete_or_excerpt_merge_preserves_actual_shown_source_and_rejects_tampering(monkeypatch):
    snapshot = source_snapshot(2)
    hidden = '未提示の前提を確認したとは扱わない。'
    quote = 'この場面で私は返事を待った。'
    context = 'その日の資料を読み、内容をノートへ書き留めた。' * 35
    snapshot['members'][0]['original'].update(memo=hidden + context + quote + context, memo_action='')
    snapshot['members'][1]['original'].update(memo='別の場面で私は話した。', memo_action='')
    prepared = parent(snapshot)
    leaves = []
    for index, member in enumerate(prepared.frozen.members):
        stage = core.prepare_semantic_leaf(prepared, (member.saved_record_ref,))
        packet = packet_for([dict(field=index + 1, quote=quote if index == 0 else '私は話した')])
        leaves.append((stage, response(stage, packet)))
    merge = core.prepare_semantic_merge(prepared, tuple(leaves))
    material = json.loads(merge.material_json)
    fragment = material['fields'][0]
    assert quote in fragment['text'] and hidden in fragment['text']
    assert fragment['fragment_is_complete_field'] is True
    assert material['omitted_ranges'] == []
    assert material['history_coverage']['full_source_semantic_coverage'] is False
    packet = packet_for([dict(field=1, quote=hidden)])
    assert core.build_semantic_stage(merge, response(merge, packet)).coverage['mapped_count'] == 1
    material['fields'][0]['text'] = hidden
    forged = replace(merge, material_json=core.semantic_map_canonical(material))
    with pytest.raises(core.AnalysisSemanticMapError, match='stage_unbound'):
        core.build_semantic_stage(forged, response(forged, packet))
    good = core.build_semantic_stage(merge, response(merge, packet_for([dict(field=1, quote=quote)])))
    assert good.coverage['source_count'] == 2 and good.coverage['mapped_count'] == 1
    assert good.coverage['unparsed_count'] == 1
    full_bytes = len(core.semantic_map_canonical(merge.messages()).encode('utf-8'))
    monkeypatch.setattr(core, '_SEMANTIC_MAP_INSTRUCTION', core._SEMANTIC_MAP_INSTRUCTION
        + 'x' * (core.SEMANTIC_HISTORY_MERGE_MAX_PROMPT_BYTES - full_bytes + 1))
    rebound = tuple((leaf, response(leaf, json.loads(receipt.raw))) for leaf, receipt in leaves)
    excerpt = core.prepare_semantic_merge(prepared, rebound)
    material = json.loads(excerpt.material_json)
    shown = material['fields'][0]
    text = prepared.fields[0][1]
    start = text.index(quote)
    assert shown['fragment_scalar_range'] == [start - 160, start + len(quote) + 160]
    assert shown['text'] == text[start - 160:start + len(quote) + 160]
    assert shown['fragment_is_complete_field'] is False and hidden not in shown['text']
    assert material['omitted_ranges'] and material['history_coverage']['full_source_semantic_coverage'] is False
    assert len(core.semantic_map_canonical(excerpt.messages()).encode('utf-8')) <= core.SEMANTIC_HISTORY_MERGE_MAX_PROMPT_BYTES
    with pytest.raises(core.AnalysisSemanticMapError, match='evidence_not_shown'):
        core.build_semantic_stage(excerpt, response(excerpt, packet_for([dict(field=1, quote=hidden)])))
    core.build_semantic_stage(excerpt, response(excerpt, packet_for([dict(field=1, quote=quote)])))


def correction_snapshot():
    snapshot = source_snapshot(3)
    refs = [row['original']['id'] for row in snapshot['members']]
    snapshot['map_corrections'] = [dict(schema_version='cocolon.analysis.map_correction.v1',
        correction_id='00000000-0000-4000-8000-000000000099', owner_scope=OWNER,
        recorded_at=snapshot['now'], source_state='ACTIVE',
        target_context=dict(artifact_ref='artifact:' + '1' * 32 + '@1', kind='node', ref='n1',
            field='explanation', target_text='いつも避けるという読み', field_text='いつも避けるという読み',
            source_guard=snapshot['guard'], cohort=[dict(record_ref=ref,
                source_guard='analysis-map-member-v1:' + '2' * 64) for ref in refs[:2]]),
        explanation=dict(source_role='USER_ANALYSIS_MAP_CORRECTION',
            text='いつも避けているわけではなく、その時だけ返事を待ちました。'))]
    return snapshot


def test_map_correction_cohort_is_indivisible_and_full_explanation_is_mandatory():
    prepared = parent(correction_snapshot())
    refs = tuple(m.saved_record_ref for m in prepared.frozen.members)
    with pytest.raises(core.AnalysisSemanticMapError, match='cohort_split'):
        core.prepare_semantic_leaf(prepared, refs[:1])
    first = core.prepare_semantic_leaf(prepared, refs[:2])
    field = next(f for f in json.loads(first.material_json)['fields'] if f['record'] is None)
    first_packet = packet_for([dict(field=field['field'], quote=field['text'])])
    first_response = response(first, first_packet)
    second = core.prepare_semantic_leaf(prepared, refs[2:])
    ordinary = json.loads(second.material_json)['fields'][0]
    second_response = response(second, packet_for([dict(field=ordinary['field'], quote=ordinary['text'])]))
    merge = core.prepare_semantic_merge(prepared, ((first, first_response), (second, second_response)))
    shown = next(f for f in json.loads(merge.material_json)['fields'] if f['field'] == field['field'])
    assert shown['text'] == field['text'] and shown['fragment_is_complete_field']
    assert core.build_semantic_stage(merge, response(merge, first_packet)).coverage['mapped_count'] == 2
    partial = deepcopy(first_packet); partial['nodes'][0]['evidence'][0]['quote'] = 'その時だけ返事を待ちました'
    with pytest.raises(core.AnalysisSemanticMapError, match='evidence_incomplete'):
        core.build_semantic_stage(merge, response(merge, partial))
    with pytest.raises(core.AnalysisSemanticMapError, match='correction_not_applied'):
        core.build_semantic_stage(merge, response(merge,
            packet_for([dict(field=ordinary['field'], quote=ordinary['text'])])))


def test_pure_leaf_budget_probes_do_not_requalify_the_parent(monkeypatch):
    prepared = parent()
    original = core.prepare_analysis_semantic_map
    calls = []
    monkeypatch.setattr(core, 'prepare_analysis_semantic_map', lambda *a, **kw:
        (calls.append(True), original(*a, **kw))[1])
    for member in prepared.frozen.members:
        core.prepare_semantic_leaf(prepared, (member.saved_record_ref,))
    assert not calls
    leaf, receipt = standard_leaves(prepared)[0]
    core.build_semantic_stage(leaf, receipt)
    assert len(calls) == 1


def test_three_leaves_are_complete_and_final_coverage_is_not_leaf_count_sum():
    prepared = parent(source_snapshot(3))
    leaves, evidence = [], []
    for member in prepared.frozen.members:
        leaf = core.prepare_semantic_leaf(prepared, (member.saved_record_ref,))
        field = json.loads(leaf.material_json)['fields'][0]
        root = dict(field=field['field'], quote=field['text'])
        evidence.append(root)
        leaves.append((leaf, response(leaf, packet_for([root]))))
    merge = core.prepare_semantic_merge(prepared, tuple(leaves))
    result = core.build_semantic_stage(merge, response(merge, packet_for(evidence)))
    assert result.coverage['processed_count'] == result.coverage['mapped_count'] == 3
    assert result.coverage['unparsed_count'] == 0


def test_noncontiguous_map_correction_cohort_preserves_parent_global_numbers():
    snapshot = correction_snapshot()
    snapshot['map_corrections'][0]['target_context']['cohort'][1]['record_ref'] = snapshot['members'][2]['original']['id']
    prepared = parent(snapshot)
    refs = tuple(m.saved_record_ref for m in prepared.frozen.members)
    first = core.prepare_semantic_leaf(prepared, (refs[0], refs[2]))
    correction = next(f for f in json.loads(first.material_json)['fields'] if f['record'] is None)
    first_receipt = response(first, packet_for([dict(field=correction['field'], quote=correction['text'])]))
    second = core.prepare_semantic_leaf(prepared, (refs[1],))
    field = json.loads(second.material_json)['fields'][0]
    second_receipt = response(second, packet_for([dict(field=field['field'], quote=field['text'])]))
    merge = core.prepare_semantic_merge(prepared, ((first, first_receipt), (second, second_receipt)))
    result = core.build_semantic_stage(merge, response(merge,
        packet_for([dict(field=correction['field'], quote=correction['text'])])))
    assert result.coverage['mapped_count'] == 2 and result.coverage['unparsed_count'] == 1


def test_final_compiler_added_source_context_roots_are_also_shown():
    from test_analysis_semantic_source_duties import condition_sample, condition_candidate
    prepared = parent(condition_sample(), core.SEMANTIC_MAP_SOURCE_DUTIES_PROFILE)
    leaves = []
    for index, member in enumerate(prepared.frozen.members):
        leaf = core.prepare_semantic_leaf(prepared, (member.saved_record_ref,))
        packet = condition_candidate()
        packet['nodes'] = [packet['nodes'][index]]
        packet['nodes'][0]['node_id'] = 'n1'
        packet['edges'] = []
        leaves.append((leaf, response(leaf, packet)))
    merge = core.prepare_semantic_merge(prepared, tuple(leaves))
    assert len(json.loads(merge.material_json)['fields']) == 4
    result = core.build_semantic_stage(merge, response(merge, condition_candidate()))
    nodes = result.artifact.private_evidence()['graph']['nodes']
    assert all(len(node['evidence_refs']) == 2 for node in nodes)
    assert '私は会議にいた' in result.artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text']


def test_compiler_added_context_inherits_its_leaf_unknown_without_editing_raw():
    from test_analysis_semantic_source_duties import condition_sample, condition_candidate
    prepared = parent(condition_sample(), core.SEMANTIC_MAP_SOURCE_DUTIES_PROFILE)
    first = core.prepare_semantic_leaf(prepared, (prepared.frozen.members[0].saved_record_ref,))
    unknown = 'その会議の場面が本人にとってどのような意味だったか'
    first_receipt = response(first, packet_for([dict(field=1, quote='私は会議にいた')], unknowns=[unknown]))
    second = core.prepare_semantic_leaf(prepared, (prepared.frozen.members[1].saved_record_ref,))
    second_receipt = response(second, packet_for([dict(field=4, quote='私は資料を調べた')]))
    merge = core.prepare_semantic_merge(prepared, ((first, first_receipt), (second, second_receipt)))
    packet = condition_candidate()
    original = deepcopy(packet)
    receipt = response(merge, packet)
    result = core.build_semantic_stage(merge, receipt)
    assert packet == original and json.loads(receipt.raw) == original
    assert result.artifact.safe_projection(authenticated_owner_scope=OWNER)['nodes'][0]['unknowns'] == [unknown]
    private = result.artifact.private_evidence()
    audit, = private['graph']['meaning_review']['history_synthesis']['inherited_unknowns']
    root = core._semantic_map_evidence(prepared, dict(field=1, quote='私は会議にいた'))[1]
    assert root in audit['source_evidence_refs']
    assert root['evidence_id'] in audit['matched_final_evidence_ids']
    assert private['response_sha256'] == receipt.raw_sha256
