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


@pytest.mark.parametrize('profile, hashes, prior_hashes', [
    (core.SEMANTIC_MAP_PROFILE, (
        'a3ed60a1869b60e91a1b5973446bdeda7536f2990351fbd762a475201ff9806a',
        '726cd3db5aae8e4375a0d05edaafbd6332e68a6b56e294d84e00d631a3c254c6'), (
        ('f612e6a95d1a146a4a61c188386a5e036724c7eae8e2e0b967ec86e0bff8f64e',
         '6bdd333c1b4a8e1991603d59e04b87c12c755154c63a69535f52de9cc25f9085',
         '0ed9e6c3dcb9b436f13c4418575dc9237762d1e4edd4f18426b217a975c49b99'),
        ('3d2faafa7936346b4c0e3fc5a06f9fdb2e2287dbfe9e857a51e6c582024b559a',
         '2254c261ae000d00f5b064af444b8527f89aa89ec0483381501ae4c0b3f75ea3',
         'f574cab50cfc085e3978b9eef12b626541309d6ef1b913edaf06c55532241798'))),
    (core.SEMANTIC_MAP_SOURCE_DUTIES_PROFILE, (
        'ad20df27112a84554f06cb13c1cbcf4e639aa6becccb4c6dbc4d4b9dffa6cc3e',
        '328cb478a0527ce8a866d95cea5a014d341f0f36d60eaeb838be6f43358f45c7'), (
        ('ad66ec1a1b9d80a5c1ea029012891ae6f623725f0e635afdbd58fcf6afcd26db',
         '903cbcb7cfc3aa86aec4ec7ed476bd96ae7217b3294f88ad4843e1144a323aaa',
         '8d11d9426788eaccaea3c70fe68c55483d7f1aaac8eb339d1f4abee880108087'),
        ('d9f3b5c2bb9836654ac8095d7934e524ec4a5f3fcad8b81b583501a3620656d9',
         '896d8d4651740bab5b5e16f787e7280c6a46415109d9225f5b7fbf4c916cf4f4',
         '2068408ed06947b40a94eb169901101a0afe7cc1a4550403ff679c99c8e0ab9a'))),
])
def test_history_receipts_bind_current_reading_prompt_and_reject_prior_prompt(profile, hashes, prior_hashes):
    prepared = parent(profile=profile)
    leaves = standard_leaves(prepared)
    assert tuple(core.semantic_map_hash(stage.messages()) for stage, _ in leaves) == hashes
    for (stage, receipt), stale_hashes in zip(leaves, prior_hashes):
        for prior_hash in stale_hashes:
            with pytest.raises(core.AnalysisSemanticMapError, match='analysis_semantic_response_unbound'):
                core.build_semantic_stage(stage, replace(receipt, messages_sha256=prior_hash))
        assert json.loads(stage.material_json)['history_stage']['profile'] == 'semantic_map.history_synthesis.v1'
        core.build_semantic_stage(stage, receipt)
    merge = core.prepare_semantic_merge(prepared, leaves)
    assert json.loads(merge.material_json)['history_stage']['profile'] == 'semantic_map.history_synthesis.v2'


def test_merge_sources_only_keep_exact_leaf_raw_and_unassessed_unknowns_private():
    prepared = parent()
    leaves = []
    for index, (stage, receipt) in enumerate(standard_leaves(prepared)):
        leaf_packet = json.loads(receipt.raw)
        leaf_packet['overview'] = dict(title='葉だけの見出し' + str(index), summary='葉だけの概要' + str(index))
        for node in leaf_packet['nodes']:
            node.update(title='葉だけの項目' + str(index), summary='葉だけの要約' + str(index),
                explanation='葉だけの説明' + str(index), unknowns=['葉だけの未検証事項' + str(index)])
        if index == 0:
            # Repeated use of one literal in two AI nodes yields one flat
            # source-index entry, without carrying that node grouping forward.
            duplicate = deepcopy(leaf_packet['nodes'][0])
            duplicate.update(node_id='n2', title='葉だけの別項目', summary='葉だけの別要約',
                explanation='葉だけの別説明')
            leaf_packet['nodes'].append(duplicate)
        leaves.append((stage, response(stage, leaf_packet)))
    leaves = tuple(leaves)
    merge = core.prepare_semantic_merge(prepared, leaves)
    material = json.loads(merge.material_json)
    assert 'leaf_interpretations' not in material and 'scoped_unknowns' not in material
    assert len(material['leaf_receipts']) == 2 and len(material['leaf_source_index']) == 3
    assert all(set(receipt) == {'leaf_request_ref', 'messages_sha256', 'response_sha256'}
        for receipt in material['leaf_receipts'])
    originals = {field[0]: field[1] for field in prepared.fields}
    for entry in material['leaf_source_index']:
        assert set(entry) == {'field', 'quote', 'scalar_range'}
        start, end = entry['scalar_range']
        assert originals[entry['field']][start:end] == entry['quote']
    assert '葉だけの' not in core.semantic_map_canonical(merge.messages())
    packet = candidate()
    paraphrase = 'その場で黙っていた理由はまだ分からない'
    packet['nodes'][1]['unknowns'] = [paraphrase]
    original = deepcopy(packet)
    receipt = response(merge, packet)
    raw = receipt.raw
    result = core.build_semantic_stage(merge, receipt)
    assert packet == original and receipt.raw == raw
    projection = result.artifact.safe_projection(authenticated_owner_scope=OWNER)
    assert projection['nodes'][1]['unknowns'] == [paraphrase]
    visible = result.artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text']
    assert paraphrase in visible and '葉だけの' not in visible
    private = result.artifact.private_evidence()
    assert private['response_sha256'] == receipt.raw_sha256
    assert private['messages_sha256'] == receipt.messages_sha256
    retained = result.artifact.private_evidence()['graph']['meaning_review']['history_synthesis']
    assert retained['profile'] == 'semantic_map.history_synthesis.v2'
    assert retained['unknown_handling'] == 'PRIVATE_ONLY_UNASSESSED'
    assert retained['scoped_unknowns'][0]['unknowns'] == ['葉だけの未検証事項0']
    assert retained['full_source_semantic_coverage'] is False
    assert retained['inherited_unknowns'] == []
    assert retained['leaf_source_index'] == material['leaf_source_index']
    for entry, (stage, leaf_receipt) in zip(retained['leaf_candidates'], leaves):
        assert entry['leaf_request_ref'] == stage.request_ref
        assert entry['raw'] == leaf_receipt.raw and entry['packet'] == json.loads(leaf_receipt.raw)
        assert entry['messages_sha256'] == leaf_receipt.messages_sha256
        assert entry['response_sha256'] == leaf_receipt.raw_sha256


def test_leaf_unknowns_never_expand_final_unknowns_or_the_existing_four_item_limit():
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
    result = core.build_semantic_stage(merge, receipt)
    assert result.artifact.safe_projection(authenticated_owner_scope=OWNER)['nodes'][1]['unknowns'] == packet['nodes'][1]['unknowns']
    assert packet == original and json.loads(receipt.raw) == original
    packet['nodes'][1]['unknowns'].append('五つ目の未確認')
    with pytest.raises(core.AnalysisSemanticMapError, match='analysis_semantic_map_invalid'):
        core.build_semantic_stage(merge, response(merge, packet))


def test_complete_merge_fields_use_the_exact_message_budget_and_preserve_unquoted_source(monkeypatch):
    import analysis_model_source as sources
    assert core.SEMANTIC_HISTORY_MERGE_MAX_PROMPT_BYTES == sources.SEMANTIC_MERGE_MAX_PROMPT_BYTES == 131072
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


def test_compiler_added_source_context_keeps_leaf_unknown_private_without_editing_raw():
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
    assert result.artifact.safe_projection(authenticated_owner_scope=OWNER)['nodes'][0]['unknowns'] == []
    private = result.artifact.private_evidence()
    history = private['graph']['meaning_review']['history_synthesis']
    assert history['inherited_unknowns'] == []
    assert history['scoped_unknowns'][0]['unknowns'] == [unknown]
    assert history['leaf_candidates'][0]['raw'] == first_receipt.raw
    root = core._semantic_map_evidence(prepared, dict(field=1, quote='私は会議にいた'))[1]
    assert root in private['graph']['nodes'][0]['evidence_refs']
    assert private['response_sha256'] == receipt.raw_sha256


def test_later_recorded_confirmation_is_not_forced_back_into_a_leaf_unknown():
    snapshot = source_snapshot(2)
    snapshot['members'][0]['original'].update(
        memo='私は母に予定を伝えた。母から「了解しました」と返信があった。返事の理由までは分からない。',
        memo_action='')
    snapshot['members'][1]['original'].update(memo='私は資料を確認した。', memo_action='')
    prepared = parent(snapshot)
    leaves = []
    false_unknown = '母から返信があったかは分からない。'
    for index, member in enumerate(prepared.frozen.members):
        leaf = core.prepare_semantic_leaf(prepared, (member.saved_record_ref,))
        field = json.loads(leaf.material_json)['fields'][0]
        leaves.append((leaf, response(leaf, packet_for([dict(field=field['field'],
            quote='私は母に予定を伝えた。' if index == 0 else field['text'])],
            unknowns=[false_unknown] if index == 0 else []))))
    merge = core.prepare_semantic_merge(prepared, tuple(leaves))
    packet = packet_for([dict(field=1, quote='母から「了解しました」と返信があった。')],
        unknowns=['返事の理由までは分からない。'])
    packet['nodes'][0].update(summary='母から「了解しました」と返信があったと記録されています。',
        explanation='予定を伝えた後の返信が書かれています。返事の理由までは分からないと記されています。')
    baseline = application.build_semantic_map(prepared, response(prepared, packet))[0]
    result = core.build_semantic_stage(merge, response(merge, packet))
    assert result.artifact.safe_projection(authenticated_owner_scope=OWNER)['nodes'] == baseline.safe_projection(
        authenticated_owner_scope=OWNER)['nodes']
    visible = result.artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text']
    assert '了解しました' in visible and '返事の理由までは分からない。' in visible
    assert false_unknown not in visible and false_unknown not in core.semantic_map_canonical(merge.messages())
    history = result.artifact.private_evidence()['graph']['meaning_review']['history_synthesis']
    assert history['scoped_unknowns'][0]['unknowns'] == [false_unknown]
    assert history['leaf_candidates'][0]['packet']['nodes'][0]['unknowns'] == [false_unknown]
