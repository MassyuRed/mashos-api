"""MERGE tuple output preserves the existing native source and visible-text constraints."""
import json
from copy import deepcopy
from types import SimpleNamespace

import pytest

import analysis_merge_wire as wire
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from test_analysis_merge_action_sources import NONACTION, OPENING, OUTCOME, UNCONFIRMED, WISH, stage_with_action
from test_analysis_node_local_native_profile import advance, probe
from test_analysis_occurrence_v17_record_owners import packet


def planned():
    stage = stage_with_action()
    fields = {f['field_path']: f['field'] for f in json.loads(stage.material_json)['fields']}
    memo, action = fields['memo'], fields['memo_action']
    parts = [[[(memo, OPENING), (action, OUTCOME + NONACTION)], [(action, UNCONFIRMED + WISH)]]]
    return stage, packet(stage, parts)


def exchange(phase):
    stage, authored = planned()
    admitted = core.admit_semantic_node_local_v4_plan_response(stage, authored, merge_anchors=True, merge_action_sources=True)
    opts = {'plan': admitted} if phase == 'NODES' else {}
    msgs = core.semantic_node_local_v4_wire_messages(stage, phase, **opts)
    codec = wire.response_codec(msgs, choice_module=probe._semantic_choice_module(), fact_key=probe._semantic_fact_part_key)
    if phase == 'NODES':
        node = probe.semantic_output_schema(msgs)['properties']['nodes']['properties']['n1']['properties']
        units = {}
        for uid, schema in node['units']['properties'].items():
            props = schema['properties']
            facts = {key: value['enum'][0] for key, value in props['fact_parts']['properties'].items()}
            units[uid] = dict(evidence_ref='n1.' + uid, source_mode='RECORDED', fact_parts=facts, unknowns=[])
        meaning = node['meaning'].get('enum', [''])[0]
        authored = dict(schema_version=core._semantic_v4_schema('NODES'), plan_sha256=codec.binding,
                        nodes={'n1': dict(units=units, node_kind='STATE_CONTEXT', perspective='SELF',
                                          title=node['title'].get('enum', ['改修の問い合わせと保留'])[0], meaning=meaning)})
    physical = codec.encode(authored)
    alphabet = ''.join(dict.fromkeys(wire.compact_json(msgs) + wire.compact_json(physical) + wire.compact_json(authored)))
    return msgs, authored, physical, alphabet


@pytest.mark.parametrize('phase', ['PLAN', 'NODES'])
def test_private_tuple_projects_to_original_native_prefix_and_exact_response(phase):
    msgs, authored, physical, alphabet = exchange(phase)
    root = probe.semantic_json_parser(msgs, alphabet)
    complete = advance(root, wire.compact_json(physical))
    assert complete.can_end() and json.loads(complete.projected_prefix()) == authored
    assert not root.can_end()
    with pytest.raises(ValueError):
        advance(root, wire.compact_json(authored))
    old = wire.prepare_messages(wire.legacy_messages(msgs), version=wire.RECORD_VERSION)
    assert advance(probe.semantic_json_parser(old, alphabet), wire.compact_json(authored)).can_end()


@pytest.mark.parametrize('change', ['binding', 'field', 'unknown_code', 'repeat', 'incomplete_action'])
def test_failed_plan_branch_cannot_alter_source_ownership_or_accept_incomplete_action(change):
    msgs, _, physical, alphabet = exchange('PLAN')
    other = deepcopy(physical)
    roots = other['n'][0][0]
    if change == 'binding':
        other['h'] = '0' * 64
    elif change == 'field':
        roots[0][1] = 20
    elif change == 'unknown_code':
        roots[0][0] = '~未登録'
    elif change == 'repeat':
        roots.insert(1, roots[0])
    else:
        other['n'][0].pop()
    parser = probe.semantic_json_parser(msgs, alphabet)
    with pytest.raises(ValueError):
        advance(parser, wire.compact_json(other))
    assert advance(parser, wire.compact_json(physical)).can_end()


def test_invalid_native_qualification_and_visible_residue_remain_unavailable():
    msgs, _, physical, alphabet = exchange('NODES')
    parser = probe.semantic_json_parser(msgs, alphabet + '}')
    for mutate in ('invalid_fact', 'out_of_scope_unknown', 'title_closer'):
        other = deepcopy(physical)
        entry = other['n'][0][0][0]
        if mutate == 'invalid_fact':
            entry[1][0] = 999999
        elif mutate == 'out_of_scope_unknown':
            entry[2].append(['~無関係', 9])
        else:
            other['n'][0][3] = '無関係}}'
        with pytest.raises(ValueError):
            advance(parser, wire.compact_json(other))
    assert advance(parser, wire.compact_json(physical)).can_end()


def test_greedy_filter_compares_completed_public_nodes_through_the_compact_prefix(monkeypatch):
    np = pytest.importorskip('numpy')
    msgs, _, physical, alphabet = exchange('NODES')
    parser = probe.semantic_json_parser(msgs, alphabet)
    raw = wire.compact_json(physical)
    state = advance(parser, raw[:-1])
    enforcer = SimpleNamespace(prefix_states={(): SimpleNamespace(parser=state)},
                               tokenizer_tree=SimpleNamespace(new_word_tokens={0, 1}, tokens_to_strs={0: '}', 1: ']'}))
    inspected = []
    def duplicate(expanded, sources):
        inspected.append(json.loads(expanded))
        return True
    monkeypatch.setattr(probe, '_occurrence_duplicate_prefix', duplicate)
    filter_choice = probe._occurrence_greedy_node_filter(None, 1, compact_prefix=SimpleNamespace(token_enforcer=enforcer))
    with pytest.raises(ValueError, match='no_distinct_node_continuation'):
        filter_choice(np.array([[9]]), np.array([[2.0, 1.0]]))
    assert len(inspected) == 1 and inspected[0]['nodes']['n1']['units']['u1']['evidence_ref'] == 'n1.u1'


def test_normal_compiler_keeps_raw_receipts_and_projects_each_supported_wire_version():
    from hashlib import sha256
    from dataclasses import replace
    from cocolon_meaning_experience_engine.cores.analysis import intent_compiler as compiler

    stage, plan_packet = planned()
    material = json.loads(stage.material_json)
    material['history_stage']['profile'] = core.SEMANTIC_HISTORY_MERGE_PROFILE
    stage = replace(stage, material_json=core.semantic_map_canonical(material))
    plan_packet['source_choices_sha256'] = json.loads(stage.messages()[1]['content'])['source_choices_sha256']
    plan = core.admit_semantic_node_local_v4_plan_response(stage, plan_packet, merge_anchors=True, merge_action_sources=True)
    _, node_packet, _, _ = exchange('NODES')
    node_packet['plan_sha256'] = core.semantic_map_hash(['analysis.node-facts.v1','NODES',stage.request_ref,plan])
    admitted = core.admit_semantic_node_local_v4_nodes_response(stage, plan, node_packet)
    rel_messages = core.semantic_node_local_v4_messages(stage, 'RELATIONS', plan=plan, nodes=admitted)
    registry = json.loads(rel_messages[1]['content'])['candidate_nodes']
    rel = dict(schema_version=core._semantic_v4_schema('RELATIONS'),nodes_sha256=core.semantic_map_hash(registry),
               qualification_review={},edges=[],overview=dict(node_refs=['n1'],title='図面の問い合わせ'))
    projections = []
    compiled_nodes = []
    for version in wire.VERSIONS:
        receipt = dict(schema_version=core.semantic_node_local_v4_artifact_schema(stage),merge_wire_version=version,phases=[])
        for phase, value, opts in [('PLAN',plan_packet,{}),('NODES',node_packet,dict(plan=plan)),
                                   ('RELATIONS',rel,dict(plan=plan,nodes=admitted))]:
            msgs = core.semantic_node_local_v4_wire_messages(stage,phase,wire_version=version,**opts)
            codec = wire.response_codec(msgs)
            raw = wire.compact_json(codec.encode(value) if codec else value)
            receipt['phases'].append(dict(phase=phase,raw=raw,raw_sha256=sha256(raw.encode()).hexdigest(),
                messages_sha256=core.semantic_map_hash(msgs),logical_messages_sha256=core.semantic_map_hash(wire.legacy_messages(msgs)),
                finish_reason='stop',completion_tokens=80))
        view = core._semantic_v4_view(stage)
        projections.append(compiler.expand_analysis_semantic_event_plan(view,receipt))
        graph = compiler.compile_analysis_semantic_stage(stage,receipt,response_sha256=core.semantic_map_hash(receipt))
        private=json.loads(graph.meaning_review_json)['node_local_plan']
        assert private['phase_artifact'] == receipt
        compiled_nodes.append(graph.nodes_json)
        joined, choices = core.assemble_semantic_node_local_v4_with_node_choices(view,receipt)
        assert choices == node_packet and joined['nodes'][0]['units'][0]['evidence'] == plan['nodes'][0]['units'][0]['evidence']
        assert all(sha256(row['raw'].encode()).hexdigest()==row['raw_sha256'] for row in receipt['phases'])
        assert ('h' in json.loads(receipt['phases'][1]['raw'])) == (version in wire.OUTPUT_VERSIONS)
    assert all(view == projections[0] for view in projections)
    assert all(nodes == compiled_nodes[0] for nodes in compiled_nodes)
    assert OUTCOME in projections[0]['nodes'][0]['explanation'] and NONACTION in projections[0]['nodes'][0]['explanation']


def test_relation_reviewer_can_keep_narrow_or_close_the_same_bound_qualification():
    from test_analysis_merge_transport import source_merge

    tail = '弟が店に相談を送ったかは聞いていない。'
    original = '完了の知らせは読んだが、' + tail
    stage = source_merge([original])
    plan = core.admit_semantic_node_local_v4_plan_response(stage, packet(stage, [[[(1, original)]]]), merge_anchors=True)
    node_messages = core.semantic_node_local_v4_wire_messages(stage, 'NODES', plan=plan)
    codec = wire.response_codec(node_messages)
    node = probe.semantic_output_schema(node_messages)['properties']['nodes']['properties']['n1']['properties']
    body = dict(schema_version=core._semantic_v4_schema('NODES'), plan_sha256=codec.binding,
                nodes={'n1':dict(units={'u1':dict(evidence_ref='n1.u1',source_mode='RECORDED',
                      fact_parts={codec.plan_units[0][0][0]:1},unknowns=[dict(source_quote=original,source_field=1)])},
                      node_kind='STATE_CONTEXT',perspective='SELF',title=node['title'].get('enum',[original])[0],
                      meaning=node['meaning'].get('enum',[''])[0])})
    admitted = core.admit_semantic_node_local_v4_nodes_response(stage,plan,body)
    messages = core.semantic_node_local_v4_wire_messages(stage,'RELATIONS',plan=plan,nodes=admitted)
    codec = wire.response_codec(messages)
    (key, primary), = codec.qualification_items
    assert primary == original
    logical = dict(schema_version=core._semantic_v4_schema('RELATIONS'),nodes_sha256=codec.binding,
                   qualification_review={},edges=[],overview=dict(node_refs=['n1'],title='修理の記録'))
    alphabet = ''.join(dict.fromkeys(wire.compact_json(messages) + '修理の記録未登録0123456789～' + tail))
    native = probe.semantic_json_parser(messages,alphabet)
    for answer in (dict(status='OPEN',source_quote=original),dict(status='OPEN',source_quote=tail),
                   dict(status='STATED'),dict(status='EARLIER'),dict(status='DUPLICATE')):
        logical['qualification_review']={key:answer}
        physical=codec.encode(logical)
        complete=advance(native,wire.compact_json(physical))
        assert complete.can_end() and json.loads(complete.projected_prefix())==logical
        assert core.semantic_node_local_v4_relations(stage,plan,admitted,codec.decode(physical))
    for review in ([], [[1]], [[True]], [['~未登録']], ['OPEN'], [[0],[0]], [[codec.quote_code(original)]]):
        with pytest.raises(ValueError):
            advance(native,wire.compact_json(dict(physical,qualification_review=review)))


def test_new_merge_rejects_a_condition_or_actor_added_to_a_node_title():
    from test_analysis_merge_transport import source_merge

    first = '担当者が予定を電話で伝えた。'
    second = '設置できるかは翌週に確認する。'
    extra = '別の棚は注文済みだった。'
    stage = source_merge([first + second + extra])
    plan = core.admit_semantic_node_local_v4_plan_response(
        stage, packet(stage, [[[(1, first + second)]]]), merge_anchors=True)
    for version in wire.OUTPUT_VERSIONS:
        messages = core.semantic_node_local_v4_wire_messages(stage, 'NODES', plan=plan, wire_version=version)
        codec = wire.response_codec(messages)
        root = codec.plan_units[0][0][0]
        entry = dict(units={'u1': dict(evidence_ref='n1.u1', source_mode='RECORDED',
            fact_parts={root: 1}, unknowns=[])}, node_kind='STATE_CONTEXT', perspective='SELF',
            title=second, meaning='')
        node = dict(schema_version=core._semantic_v4_schema('NODES'), plan_sha256=codec.binding, nodes={'n1': entry})
        candidates = (second, '担当者が設置できるのは翌週だけだ。', '本人が予定を電話で伝えた。', extra)
        alphabet = ''.join(dict.fromkeys(wire.compact_json(messages) + wire.compact_json(node) + ''.join(candidates)))
        for title in candidates:
            entry['title'] = title
            raw = wire.compact_json(codec.encode(node))
            parser = probe.semantic_json_parser(messages, alphabet)
            if version in wire.TITLE_VERSIONS and title != second:
                with pytest.raises(ValueError):
                    advance(parser, raw)
                with pytest.raises(core.AnalysisSemanticMapError, match='merge_title_not_in_source'):
                    core.admit_semantic_node_local_v4_nodes_response(stage, plan, node, bound_titles=True)
            else:
                assert advance(parser, raw).can_end()
                assert core.admit_semantic_node_local_v4_nodes_response(
                    stage, plan, node, bound_titles=version in wire.TITLE_VERSIONS)['nodes']['n1']['title'] == title


def test_title_choices_preserve_quotation_scope_fragment_boundaries_and_record_owners():
    fields = [
        dict(field=1, record=1, text='「明日は休む。」と友人が言った。明日は店が開く。'),
        dict(field=2, record=2, text='前日から予定していた。'),
    ]
    material = dict(fields=fields)
    def headings(*roots):
        from analysis_plan_source_choices import source_node_titles
        return source_node_titles(material, [dict(evidence=[dict(field=f, quote=q) for f,q in roots])], ())
    assert headings((1, '明日は休む。')) == ['記録にある場面']
    assert headings((1, fields[0]['text'])) == ['「明日は休む。」と友人が言った。', '明日は店が開く。']
    assert headings((1, fields[0]['text']), (2, fields[1]['text'])) == ['記録を比べて']
    fields[1]['fragment_is_complete_field'] = False
    assert headings((2, fields[1]['text'])) == ['記録にある場面']
