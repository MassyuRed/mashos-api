"""An admitted OPEN is dated by its own original source, without deciding the event."""
from copy import deepcopy
from dataclasses import replace
import json

import analysis_plan_source_choices as choices
import analysis_cumulative_service as service
from cocolon_meaning_experience_engine.cores.analysis import intent_compiler, semantic_admission as core
from cocolon_meaning_experience_engine.cores.analysis.observed_route_realizer import (
    analysis_semantic_projection_text as render, analysis_semantic_projection_text_legacy as legacy)
from test_analysis_occurrence_v11_display import map_stages
from test_analysis_semantic_text_views import view


def test_earlier_fields_use_absolute_stamps_and_existing_distinct_jst_labels():
    material = dict(records=[
        dict(record=3, recorded_at='2026-11-07T15:00:00Z'),
        dict(record=2, recorded_at='2025-11-07T15:00:30'),
        dict(record=4, recorded_at='2026-11-08T00:00:00+09:00'),
        dict(record=1, recorded_at='2025-11-08T00:00:00+09:00')],
        fields=[dict(field=n, record=n, source_role='ORIGINAL_INPUT') for n in range(1, 5)])
    material['fields'] += [dict(field=5, record=1, source_role='SUPPLEMENTAL_ANSWER'),
                          dict(field=6, record=1, source_role='USER_ANALYSIS_MAP_CORRECTION')]
    assert choices.earlier_unknown_fields(material) == {
        1:'記録1（2025年11月8日 00:00）', 2:'記録2（2025年11月8日 00:00）'}
    for row in material['records']:
        row['recorded_at'] = '2026-11-08T00:00:00Z'
    assert choices.earlier_unknown_fields(material) == {}


def test_each_retained_open_keeps_its_field_even_when_two_records_share_the_quote():
    quote = 'どの色を希望するかは聞いていない。'
    p, plan, nodes = map_stages(quote, quote)
    material = json.loads(p.material_json)
    for row, date in zip(material['records'], ('2026-11-08', '2026-11-12'), strict=True):
        row['recorded_at'] = date + 'T00:00:00Z'
    p = replace(p, material_json=json.dumps(material, ensure_ascii=False), prompt_version=core.SEMANTIC_MAP_NODE_LOCAL_V3_PROFILE)
    joined = core._semantic_v4_join(plan, nodes)
    for node in joined:
        del node['node_id']
    joined[0]['units'].extend(joined.pop()['units'])
    packet = dict(schema_version=core.SEMANTIC_MAP_NODE_LOCAL_V3_SCHEMA, nodes=joined,
        edges=[], overview=dict(title='希望の聞き取り', node_refs=['n1']))
    original = deepcopy(packet)
    expand = intent_compiler._expand_analysis_semantic_node_local_v3
    assert expand(p, packet)['nodes'][0]['unknowns'] == [quote]
    dated = expand(p, packet, scope_earlier_unknowns=True)
    assert dated['nodes'][0]['unknowns'] == ['当時の未確認（11月8日の記録）：' + quote, quote]
    assert packet == original
    # Status review removes its STATED/EARLIER candidates upstream; rendering
    # cannot restore a qualification absent from the admitted local unit.
    joined[0]['units'][0]['unknowns'] = []
    assert expand(p, packet, scope_earlier_unknowns=True)['nodes'][0]['unknowns'] == [quote]


def test_immutable_saved_text_and_linear_view_show_the_historical_label_once():
    graph = view()
    early = '当時の未確認（11月8日の記録）：担当者が確認したかは知らない。'
    current = '本人の考えは聞いていない。'
    graph['nodes'][0]['unknowns'] = [early, current]
    previous = render(graph, record_scoped_unknowns=False)
    scoped = render(graph, record_scoped_unknowns=True)
    assert scoped.splitlines().count(early) == 1
    assert 'まだ記録にないこと：' + early not in scoped and 'まだ記録にないこと：' + current in scoped
    assert 'まだ記録にないこと：' + early in previous
    for exact in (legacy(graph), previous, scoped):
        assert service._saved_projection_text_matches(graph, exact)
        assert not service._saved_projection_text_matches(graph, exact + '。')


def test_old_literal_date_like_text_and_malformed_prefix_keep_their_own_wording():
    graph = view()
    graph.update(projection_of='artifact:example@1', period_label='これまでの記録', accessibility_linear_order=['n1', 'n2'])
    for node in graph['nodes']:
        node['evidence_badge_count'] = 1
    literal = '当時の未確認（11月8日の記録）：以前の文章を引用した。'
    malformed = '当時の未確認（担当者）：状態は不明。'
    graph['nodes'][0]['unknowns'] = [literal, malformed]
    for mode in (False, True):
        full = render(graph, record_scoped_unknowns=mode)
        old_client = service._legacy_semantic_projection(graph, full)['nodes'][0]['visible_label']
        if mode:
            assert literal in full.splitlines() and literal in old_client.splitlines()
        else:
            assert 'まだ記録にないこと：' + literal in full.splitlines()
            assert 'この記録では決められないこと：' + literal in old_client.splitlines()
        assert 'まだ記録にないこと：' + malformed in full.splitlines()


def test_v18_three_phase_entry_preserves_review_decisions_in_both_views():
    import hashlib
    import analysis_semantic_map as maps
    from test_analysis_cumulative import OWNER
    from test_analysis_node_local_v4_phases import response
    from test_analysis_occurrence_v17_record_owners import packet
    from test_analysis_v13_separate_record_titles import wire

    notes = ('担当者が返事をしたかは聞いていない。', '本人の希望はまだ分からない。')
    old, plan, bodies = map_stages(*notes)
    p = maps.prepare_semantic_map(OWNER, json.loads(old.source_snapshot_json), prompt_version=core.SEMANTIC_MAP_OCCURRENCE_V18_PROFILE)
    allocations = [[[(r['field'], r['quote']) for r in unit['evidence']] for unit in node['units']] for node in plan['nodes']]
    source = packet(p, allocations)
    joined = core._semantic_v4_join(plan, bodies)
    keys = core._semantic_qualification_candidates(joined, predicate_cues=True)
    for status in ('OPEN', 'EARLIER', 'STATED'):
        review = {key:(dict(status='OPEN', source_quote=q) if i or status == 'OPEN' else dict(status=status))
                  for i, (key, q) in enumerate(zip(keys, notes, strict=True))}
        relations = dict(schema_version=core._semantic_v4_schema('RELATIONS'), nodes_sha256=core.semantic_map_hash(joined),
            edges=[], overview=dict(node_refs=['n1', 'n2'], title='各記録に残った問い'), qualification_review=review)
        rows = []
        for phase, value in zip(core.SEMANTIC_MAP_NODE_LOCAL_V4_PHASES, (source, wire(p,plan,bodies), relations), strict=True):
            messages = core.semantic_node_local_v4_messages(p, phase, plan=plan if phase != 'PLAN' else None,
                nodes=bodies if phase == 'RELATIONS' else None)
            raw = core.semantic_map_canonical(value)
            rows.append(dict(phase=phase, messages_sha256=core.semantic_map_hash(messages), raw=raw,
                raw_sha256=hashlib.sha256(raw.encode()).hexdigest(), finish_reason='stop', completion_tokens=100))
        artifact, _ = maps.build_semantic_map(p, response(p, dict(schema_version=core.semantic_node_local_v4_artifact_schema(p),
            phases=rows)))
        graph = artifact.safe_projection(authenticated_owner_scope=OWNER)
        full = artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text']
        first = '当時の未確認（2025年1月1日の記録）：' + notes[0]
        assert graph['nodes'][0]['unknowns'] == ([first] if status == 'OPEN' else [])
        assert (first in full.splitlines()) is (status == 'OPEN')
        assert graph['nodes'][1]['unknowns'] == [notes[1]]
        assert 'まだ記録にないこと：' + notes[1] in full.splitlines()
        assert full == render(graph) and service._saved_projection_text_matches(graph, full)
