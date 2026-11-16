"""Synthetic node-local author compilation; these are not model quality ratings."""
from copy import deepcopy
import json

import pytest

import analysis_semantic_map as application
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from cocolon_meaning_experience_engine.cores.analysis import intent_compiler as compiler
from test_analysis_semantic_map import OWNER, sample, response

PROFILE = 'semantic_map.node_local.v3'
SCHEMA = 'cocolon.analysis.semantic_map.node_local.model.v3'
DRAFT = '案内の下書きを保存した。ほかの人には送っていない。'
EARLY = '共同担当者は箱の寸法を測ると話したが、測ったかはまだ聞いていない。'
JUDGMENT = '私は完成した案内だとは考えていない。'
LATER = '翌日、共同担当者から箱の幅を測ったと連絡が来た。私はその寸法を読んで案内を直した。'
WISH = '共同担当者は別の箱も測りたいと言っているが、その作業が済んだかは確認していない。'
UNREAD = '全員が案内を読んだかは分からない。'
SENT = '確認した幅を案内に反映して仲間へ送信し、一人から了解の返信を受け取った。'


def prepared(profile=PROFILE):
    snapshot = sample()
    snapshot['members'][0]['original'].update(
        memo='作業場で使う飾りの案内を作った。' + EARLY + JUDGMENT, memo_action=DRAFT)
    snapshot['members'][1]['original'].update(memo=LATER + WISH + UNREAD, memo_action=SENT)
    return application.prepare_semantic_map(OWNER, snapshot, prompt_version=profile)


def unit(field, quote, fact=None, mode='RECORDED', unknown=None):
    default_fact = {
        DRAFT: '案内の下書きを保存した段階では、ほかの人へまだ送っていなかった。',
        LATER: '翌日、共同担当者から測定済みの連絡を受け、本人が寸法を読んで案内を直した。',
    }.get(quote, quote)
    return dict(evidence=[dict(quote=quote, field=field)], source_mode=mode,
        fact=default_fact if fact is None else fact,
        unknowns=[] if unknown is None else [dict(source_quote=unknown, source_field=field)])


def node(title, units, meaning='', *, kind='STATE_CONTEXT', perspective='SELF'):
    return dict(units=units, node_kind=kind, perspective=perspective, title=title, meaning=meaning)


def packet():
    return dict(schema_version=SCHEMA, nodes=[
        node('下書きから、寸法を反映した送信へ', [
            unit(2, DRAFT), unit(4, SENT)],
            '下書きの段階では未送信だったが、翌日の寸法確認後には案内を直して送信し、一人の了解を得ている。',
            kind='CHOICE_OUTPUT'),
        node('共同担当者の測定について確認できたこと', [
            unit(1, EARLY, unknown='測ったかはまだ聞いていない'),
            unit(3, LATER)],
            '当初は測定したか未確認だったが、翌日には共同担当者から測ったとの連絡を受け、自分で寸法を読んで修正した。',
            perspective='OBSERVED_INTERACTION'),
        node('別の箱の測定は、希望と未確認の範囲', [
            unit(3, WISH, unknown='その作業が済んだかは確認していない')],
            perspective='OBSERVED_INTERACTION'),
        node('全員の既読は未確認', [unit(3, UNREAD, unknown=UNREAD)]),
        node('下書き当時の完成についての判断', [unit(1, JUDGMENT, mode='PERSON_JUDGMENT')],
            '最初の記録では、本人は案内を完成したものとは扱っていない。', kind='SELF_POSITION')],
        edges=[dict(**{'from': 'n1', 'to': 'n2'}, relation_kind='SHARED_MEANING',
            label='測定の確認と案内の修正・送信')],
        overview=dict(title='確認が進んだことと、残る未確認', node_refs=['n1', 'n2', 'n3', 'n4', 'n5']))


def compile_packet(value=None, source=None):
    return compiler.compile_analysis_semantic_map(prepared() if source is None else source,
        packet() if value is None else value, response_sha256='a' * 64)


def test_every_local_fact_is_visible_and_all_views_share_the_same_graph(monkeypatch):
    from cocolon_meaning_experience_engine.cores.analysis import observed_route_realizer
    calls = []
    realize = observed_route_realizer.realize_analysis_semantic_map
    monkeypatch.setattr(observed_route_realizer, 'realize_analysis_semantic_map',
        lambda graph: (calls.append(graph), realize(graph))[1])
    source, value = prepared(), packet()
    original = deepcopy(value)
    receipt = response(source, value)
    artifact, coverage = application.build_semantic_map(source, receipt)
    public = artifact.safe_projection(authenticated_owner_scope=OWNER)
    text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text']
    assert len(calls) == 1 and type(calls[0]) is compiler.AnalysisSemanticMapGraph
    assert public['wire_kind'] == 'watashi.map.v3'
    assert coverage['mapped_count'] == coverage['processed_count'] == 2
    assert coverage['unparsed_count'] == 0
    for authored, visible in zip(value['nodes'], public['nodes'], strict=True):
        for fact in authored['units']:
            assert fact['fact'] in visible['explanation'] and fact['fact'] in text
        assert visible['summary'] == (authored['meaning'] or authored['units'][0]['fact'])
        assert visible['unknowns'] == list(dict.fromkeys(
            unknown['source_quote'] for fact in authored['units'] for unknown in fact['unknowns']))
        assert visible['explanation'] in text
    assert artifact.private_evidence()['response_sha256'] == receipt.raw_sha256
    assert artifact.private_evidence()['messages_sha256'] == receipt.messages_sha256
    assert receipt.raw == application._canonical(original) and value == original
    assert 'evidence_refs' not in application._canonical(public)


def test_edge_and_overview_only_derive_their_selected_node_content():
    source, value = prepared(), packet()
    expanded = compiler.expand_analysis_semantic_event_plan(source, value)
    assert expanded['overview']['summary'] == '\n'.join(n['summary'] for n in expanded['nodes'])
    edge = expanded['edges'][0]
    assert value['nodes'][0]['meaning'] in edge['explanation']
    assert value['nodes'][1]['meaning'] in edge['explanation']
    assert WISH not in edge['explanation'] and UNREAD not in edge['explanation']
    assert all(unit['fact'] in expanded['nodes'][i]['explanation']
        for i, authored in enumerate(value['nodes']) for unit in authored['units'])
    assert set(value) == {'schema_version', 'nodes', 'edges', 'overview'}
    assert all('node_id' not in n and 'unit_refs' not in n for n in value['nodes'])


def test_exact_roles_dates_and_unknowns_stay_attached_to_their_private_source_ranges():
    source = prepared()
    graph = compile_packet(source=source)
    nodes = json.loads(graph.nodes_json)
    assert nodes[0]['summary'].startswith('下書きの段階では未送信だったが、翌日')
    assert '共同担当者から測ったとの連絡' in nodes[1]['summary']
    assert nodes[2]['unknowns'] == ['その作業が済んだかは確認していない']
    assert nodes[3]['unknowns'] == [UNREAD]
    assert len(nodes[0]['record_refs']) == len(nodes[1]['record_refs']) == 2
    assert len(nodes[2]['record_refs']) == 1
    for n in nodes:
        for root in n['evidence_refs']:
            field = next(f for f in source.fields
                if f[3].source_envelope_id == root['source_envelope_id']
                and f[3].field_path == root['field_path'])
            assert field[1][root['scalar_start']:root['scalar_end']]
    # Admission retains unassessed model interpretation, not a semantic pass.
    review = json.loads(graph.meaning_review_json)
    assert review['node_local_plan']['meaning_status'] == 'UNASSESSED'
    assert review['node_local_plan']['full_source_semantic_coverage'] is False
    assert review['node_local_plan']['plan'] == packet()
    assert review['node_local_plan']['assigned_unit_ids']['n1'] == ['n1.u1', 'n1.u2']


@pytest.mark.parametrize('change', [
    lambda p: p['nodes'][0]['units'][0]['evidence'][0].update(field=True),
    lambda p: p['nodes'][0]['units'][0]['evidence'][0].update(field=3),
    lambda p: p['nodes'][0]['units'][0]['evidence'][0].update(quote='送信したことにした。'),
    lambda p: p['nodes'][0]['units'][0].update(event_id='e1'),
    lambda p: p['nodes'][0].update(unit_refs=['e1']),
    lambda p: p['nodes'][0].update(node_id='n1'),
    lambda p: p.update(events=[]),
    lambda p: p['nodes'][0]['units'][0].update(source_mode='CERTAIN'),
    lambda p: p['edges'][0].update(to='n99'),
    lambda p: p['edges'][0].update(unit_refs=['e1']),
    lambda p: p['overview'].update(summary='別の独立した事実'),
    lambda p: p['overview'].update(node_refs=['n1', 'n1']),
    lambda p: p['nodes'][0]['units'].append(deepcopy(p['nodes'][1]['units'][0])),
])
def test_invalid_private_rebinding_and_extra_author_tables_are_rejected_without_raw_repair(change):
    value = packet()
    change(value)
    raw = deepcopy(value)
    with pytest.raises(core.AnalysisSemanticMapError):
        compile_packet(value)
    assert value == raw


@pytest.mark.parametrize('unknown', [
    dict(source_field=3, source_quote=UNREAD),
    dict(source_field=1, source_quote=JUDGMENT),
    dict(source_field=True, source_quote='測ったかはまだ聞いていない'),
])
def test_unknown_is_a_literal_inside_its_own_unit_not_elsewhere_in_the_same_record(unknown):
    value = packet()
    value['nodes'][1]['units'][0]['unknowns'] = [unknown]
    with pytest.raises(core.AnalysisSemanticMapError):
        compile_packet(value)


@pytest.mark.parametrize('old_profile', ['semantic_map.event_plan.v1', 'semantic_map.event_plan.v2'])
def test_new_private_wire_is_not_silently_reinterpreted_as_an_old_profile(old_profile):
    with pytest.raises(core.AnalysisSemanticMapError):
        compile_packet(source=prepared(old_profile))


def test_history_leaf_has_only_its_record_and_merge_reuses_exact_original_sources():
    source, value = prepared(), packet()
    leaves = []
    for index, member in enumerate(source.frozen.members):
        stage = core.prepare_semantic_leaf(source, (member.saved_record_ref,))
        local = dict(schema_version=SCHEMA, nodes=[node('この記録の確認範囲', [
            unit(2, DRAFT), unit(1, EARLY, unknown='測ったかはまだ聞いていない')])]
            if index == 0 else [node('翌日の確認と送信', [unit(3, LATER), unit(4, SENT)])],
            edges=[], overview=dict(title='この記録', node_refs=['n1']))
        receipt = response(stage, local)
        partial = core.build_semantic_stage(stage, receipt)
        assert type(partial) is compiler.AnalysisSemanticMapGraph
        assert stage.source_guard == source.source_guard
        assert json.loads(partial.coverage_json)['mapped_count'] == 1
        fields = json.loads(stage.material_json)['fields']
        assert [f['field'] for f in fields] == ([1, 2] if index == 0 else [3, 4])
        leaves.append((stage, receipt))
    merge = core.prepare_semantic_merge(source, tuple(leaves))
    material = json.loads(merge.material_json)
    assert 'leaf_interpretations' not in material
    assert 'この記録の確認範囲' not in core.semantic_map_canonical(merge.messages())
    final = core.build_semantic_stage(merge, response(merge, value))
    assert final.coverage['mapped_count'] == 2 and final.coverage['unparsed_count'] == 0
    assert final.artifact.safe_projection(authenticated_owner_scope=OWNER)['wire_kind'] == 'watashi.map.v3'
    saved = final.artifact.private_evidence()
    assert saved['source_guard'] == source.source_guard
    retained = saved['graph']['meaning_review']['history_synthesis']
    assert len(retained['leaf_receipts']) == 2
    assert [entry['raw'] for entry in retained['leaf_candidates']] == [receipt.raw for _, receipt in leaves]
    for entry in material['leaf_source_index']:
        field = next(f for f in source.fields if f[0] == entry['field'])
        assert field[1][slice(*entry['scalar_range'])] == entry['quote']


def test_leaf_cannot_cite_the_unshown_later_record():
    source = prepared()
    stage = core.prepare_semantic_leaf(source, (source.frozen.members[0].saved_record_ref,))
    local = dict(schema_version=SCHEMA, nodes=[node('隠れた翌日の内容', [unit(4, SENT)])],
        edges=[], overview=dict(title='不正な範囲', node_refs=['n1']))
    with pytest.raises(core.AnalysisSemanticMapError):
        core.build_semantic_stage(stage, response(stage, local))
