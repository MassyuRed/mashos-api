"""Final authoring, admission and public read of grounded primary structures."""
import asyncio
import hashlib
import json
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

import analysis_cumulative_service as service
import analysis_semantic_map as maps
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from test_analysis_cumulative import OWNER
from test_analysis_node_local_native_profile import accepts
from test_analysis_node_local_v4_phases import response
from test_analysis_occurrence_v11_display import map_stages
from test_analysis_occurrence_v17_record_owners import packet
from test_analysis_v13_separate_record_titles import wire

FIRST = '会議では、自分で選んだ仕事なので私から引き受けた。'
SECOND = '家では手伝うと決められてしまい、自分で決めたかったので断った。'


def scenario(*notes, self_report=False, version=True):
    old, plan, bodies = map_stages(*notes)
    snapshot = json.loads(old.source_snapshot_json)
    if self_report:
        snapshot['members'][0]['original'].update(emotions=['自己理解'])
    p = maps.prepare_semantic_map(OWNER, snapshot, prompt_version=core.SEMANTIC_MAP_OCCURRENCE_V24_PROFILE, primary_structures=version)
    for node in bodies['nodes'].values():
        node['units']['u1'].update(unknowns=[], source_mode='PERSON_JUDGMENT')
    return p, plan, bodies


def reading(scope='across_records', anchors=('n1.u1.e1', 'n2.u1.e1')):
    return dict(anchors=list(anchors), scope=scope, heading='自分で選ぶ余地',
                reading='手を貸すかを決める場面では、ご自身で引き受けるかどうかを選べることを大切にしています。')


def v2_reading():
    return dict(anchors=['n1.u1.e1', 'n2.u1.e1'], scope='across_records',
                criterion='手を貸すかを考えるとき、ご自身で引き受けるかどうかを決められることを大切にしています。',
                case_reading='会議では自分から手を挙げ、家では断った二つの選択に、決める余地があったかどうかが表れています。',
                heading='自分で選ぶ余地')


def v3_reading():
    return dict(anchors=['n1.u1.e1', 'n2.u1.e1'], scope='across_records', decision_factor='選べる余地',
                criterion='引き受けるとき、ご自身で選べる余地があることを大切にしています。',
                case_reading='会議では自分で選んだ仕事を引き受け、家では先に手伝うと決まっていて断ったことに、選べる余地の違いが表れています。',
                heading='引き受ける前のひと言')


def observed_v2_repeated_conclusion():
    # The complete, authored axis from the second fictional RELATIONS run.
    return dict(anchors=['n1.u1.e1', 'n2.u1.e1'], scope='across_records',
                criterion='自分で選んだ仕事か、手伝うと決められてしまったか。',
                case_reading='会議では自分で選んだ仕事は引き受けたが、家では手伝うと決められてしまい、自分で決めたかったので断った。',
                heading='自分で選んだ仕事か、手伝うと決められてしまったか。')


def v3_renamed_previous_response():
    previous = observed_v2_repeated_conclusion()
    return dict(anchors=previous['anchors'], scope=previous['scope'], decision_factor='自分で選んだ',
                criterion=previous['criterion'], case_reading=previous['case_reading'], heading='自分の返事')


@pytest.mark.parametrize('version, authored, publish', [
    ('karen.v1', reading, True), ('karen.v2', v2_reading, True), ('karen.v2', observed_v2_repeated_conclusion, False),
    ('karen.v3', v3_reading, True), ('karen.v3', v3_renamed_previous_response, False),
])
def test_final_native_receipt_and_saved_graph_show_conditional_conclusion_and_hide_private_anchors(version, authored, publish, monkeypatch):
    p, plan, bodies = scenario(FIRST, SECOND, version=version)
    axis = authored()
    description = axis.get('reading') or axis['criterion'] + axis['case_reading']
    nodes = core._semantic_v4_join(plan, bodies)
    notes = [FIRST, SECOND]
    plan_wire = packet(p, [[[(i, note)]] for i, note in enumerate(notes, 1)])
    material = json.loads(p.material_json)
    from analysis_plan_source_choices import WholeMapTitle
    scope = WholeMapTitle(material, nodes).neutral
    rel = dict(schema_version=core._semantic_v4_schema('RELATIONS'), nodes_sha256=core.semantic_map_hash(nodes),
               qualification_review={}, edges=[], overview=dict(node_refs=['n1', 'n2'], title_proposal='', title=scope),
               primary_structures=[axis])
    receipts = []
    for phase, value in zip(core.SEMANTIC_MAP_NODE_LOCAL_V4_PHASES,
                            (plan_wire, wire(p, plan, bodies), rel), strict=True):
        messages = core.semantic_node_local_v4_messages(p, phase, plan=plan if phase != 'PLAN' else None,
                                                       nodes=bodies if phase == 'RELATIONS' else None)
        if phase == 'RELATIONS':
            assert json.loads(messages[1]['content'])['primary_structure_reading'] == version
            assert accepts(value, messages)
        raw = json.dumps(value, ensure_ascii=False, separators=(',', ':'))
        receipts.append(dict(phase=phase, messages_sha256=core.semantic_map_hash(messages), raw=raw,
                             raw_sha256=hashlib.sha256(raw.encode()).hexdigest(), finish_reason='stop', completion_tokens=100))
    received = dict(schema_version=core.semantic_node_local_v4_artifact_schema(p), phases=receipts)
    artifact, coverage = maps.build_semantic_map(p, response(p, received))
    graph = artifact.safe_projection(authenticated_owner_scope=OWNER)
    text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text']
    assert coverage['mapped_count'] == 2
    expected = [dict(scope='across_records', title=axis['heading'], description=description, node_refs=['n1', 'n2'])]
    if version == 'karen.v3':
        expected[0]['criterion'] = axis['criterion']
    assert graph['overview']['primary_structures'] == (expected if publish else [])
    if version == 'karen.v3' and publish:
        free, free_text = service.map_projection_for_plan(graph, 'free')
        plus, plus_text = service.map_projection_for_plan(graph, 'plus')
        assert [n['node_ref'] for n in free['nodes']] == ['n1', 'n2']
        assert free['edges'][0]['label'] == plus['edges'][0]['label']
        assert '私から引き受けた' in free['edges'][0]['label'] and '断った' in free['edges'][0]['label']
        assert axis['case_reading'] not in free_text
        assert axis['case_reading'] in plus_text
    assert (description in text) == publish
    assert 'n1.u1.e1' not in json.dumps(graph)
    assert 'decision_factor' not in json.dumps(graph)
    private = artifact.private_evidence()['graph']['meaning_review']['node_local_plan']['phase_artifact']
    assert private['phases'][-1]['raw'] == receipts[-1]['raw']
    row = dict(id=str(UUID(artifact.artifact_id[9:])), content_text=text, source_profile='cumulative.v1',
               report_mode='standard', content_json=dict(report_mode='standard', watashiMap=graph, map_context=coverage))
    stored = dict(items=[row], subscription_tier='free', matched=True, history_limit=2)
    monkeypatch.setattr(service, '_rpc', AsyncMock(return_value=json.loads(json.dumps(stored))))
    refetched, = asyncio.run(service.read_maps(OWNER, report_id=row['id']))['items']
    assert refetched == row
    payload = dict(meta=refetched['content_json']['watashiMap'], item=refetched, content_text=refetched['content_text'])
    assert service.map_response_for_renderer(payload, 'semantic.v2')['meta'] == graph
    old = service.map_response_for_renderer(payload, 'semantic.v1')
    assert 'primary_structures' not in old['meta']['overview']
    assert 'primary_structures' not in old['item']['content_json']['watashiMap']['overview']
    assert 'primary_structures' in graph['overview']


@pytest.mark.parametrize('fault', ['one_record', 'copied_note', 'unknown_anchor', 'same_anchor', 'only_other_person',
                                   'four_claims', 'duplicated_axis', 'wish_only', 'claim_as_source'])
def test_reject_unbound_repeated_or_overgeneralised_readings(fault):
    p, plan, bodies = scenario(FIRST, FIRST if fault == 'copied_note' else SECOND)
    nodes = core._semantic_v4_join(plan, bodies)
    axes = [reading()]
    if fault == 'one_record':
        axes = [reading(anchors=['n1.u1.e1'])]
    if fault == 'unknown_anchor':
        axes = [reading(anchors=['n1.u99.e1'])]
    if fault == 'same_anchor':
        axes = [reading(anchors=['n1.u1.e1'] * 2)]
    if fault == 'only_other_person':
        for node in nodes:
            node['perspective'] = 'OBSERVED_INTERACTION'
    if fault in ('four_claims', 'duplicated_axis'):
        axes *= 4 if fault == 'four_claims' else 2
    if fault == 'wish_only':
        for node in nodes:
            node['units'][0]['source_mode'] = 'PERSON_WISH'
    if fault == 'claim_as_source':
        axes[0]['reading'] = FIRST
    with pytest.raises(core.AnalysisSemanticMapError):
        core._read_primary_structures(p, json.loads(p.material_json), nodes, axes)


def test_single_self_interpretation_and_one_off_event_have_different_scope():
    p, plan, bodies = scenario('人と過ごした後は一人で本を読む時間も大切だと思った。', self_report=True)
    material = json.loads(p.material_json)
    nodes = core._semantic_v4_join(plan, bodies)
    axes = [reading('self_report', ['n1.u1.e1'])]
    assert core._read_primary_structures(p, material, nodes, axes)[0]['scope'] == 'self_report'
    material['records'][0]['selected_emotions'] = ['喜び']
    with pytest.raises(core.AnalysisSemanticMapError):
        core._read_primary_structures(p, material, nodes, axes)
    assert core._read_primary_structures(p, material, nodes, [reading('in_this_record', ['n1.u1.e1'])])
    assert core._read_primary_structures(p, material, nodes, []) == []
    material['fields'][0]['field_path'] = 'memo_action'
    with pytest.raises(core.AnalysisSemanticMapError):
        core._read_primary_structures(p, material, nodes, [reading('in_this_record', ['n1.u1.e1'])])


def test_v3_single_choice_requires_the_anchored_reason_and_same_recorded_choice():
    prepared, plan, bodies = scenario(FIRST, version='karen.v3')
    material = json.loads(prepared.material_json)
    nodes = core._semantic_v4_join(plan, bodies)
    axis = dict(scope='in_this_record', anchors=['n1.u1.e1'], heading='会議で仕事を引き受けた場面',
                decision_factor='自分で選んだ仕事',
                criterion='自分で選んだ仕事だったことが、この場面で引き受けた理由です。',
                case_reading='会議では、自分で選んだ仕事だったため、引き受けました。')
    assert core._read_primary_structures(prepared, material, nodes, [axis])[0]['scope'] == 'in_this_record'
    for unsupported in (
        dict(axis, decision_factor='昇進', criterion='昇進を大切にしています。',
             case_reading='会議では昇進を考えて引き受けました。'),
        dict(axis, case_reading=axis['case_reading'].replace('引き受けました', '断りました')),
        dict(axis, criterion='自分で選んだ仕事を引き受けた後、別の仕事は断ったと書いています。'),
    ):
        assert core._read_primary_structures(prepared, material, nodes, [unsupported]) == []


def test_v3_self_report_requires_the_anchored_statement_and_the_self_insight_selection():
    statement = '人と過ごした後は一人で本を読む時間も大切だ'
    prepared, plan, bodies = scenario(statement + 'と思った。', self_report=True, version='karen.v3')
    material = json.loads(prepared.material_json)
    nodes = core._semantic_v4_join(plan, bodies)
    axis = dict(scope='self_report', anchors=['n1.u1.e1'], heading='本を読む時間についての気づき',
                decision_factor='一人で本を読む時間', criterion='「' + statement + '」との気づきです。',
                case_reading='「' + statement + '」と振り返っています。')
    assert core._read_primary_structures(prepared, material, nodes, [axis])[0]['scope'] == 'self_report'
    invented = dict(axis, decision_factor='昇進', criterion='昇進を大切にしています。',
                    case_reading='会議では昇進を考えて引き受けました。')
    assert core._read_primary_structures(prepared, material, nodes, [invented]) == []
    material['records'][0]['selected_emotions'] = ['喜び']
    assert core._read_primary_structures(prepared, material, nodes, [axis]) == []


@pytest.mark.parametrize('version', ['karen.v1', 'karen.v2', 'karen.v3'])
def test_history_merge_native_parser_preserves_structure_and_leaf_never_authors_one(version):
    from dataclasses import replace

    import analysis_merge_wire as merge
    from test_analysis_merge_transport import source_merge
    from test_analysis_node_local_native_profile import advance
    from test_emlis_natural_reply_probe_http import probe
    from analysis_plan_source_choices import WholeMapTitle

    p, plan, bodies = scenario(FIRST, SECOND, version=version)
    stage = source_merge([FIRST, SECOND])
    material = json.loads(stage.material_json)
    material['primary_structure_reading'] = version
    stage = replace(stage, parent=p, material_json=core.semantic_map_canonical(material))
    messages = core.semantic_node_local_v4_wire_messages(stage, 'RELATIONS', plan=plan, nodes=bodies)
    codec = merge.response_codec(messages)
    overview = dict(node_refs=['n1', 'n2'], title_proposal='', title=WholeMapTitle(
        material, core._semantic_v4_join(plan, bodies)).neutral)
    authored = {'karen.v1': reading, 'karen.v2': v2_reading, 'karen.v3': v3_reading}
    rel = dict(schema_version=core._semantic_v4_schema('RELATIONS'), nodes_sha256=codec.binding,
               qualification_review={}, edges=[], overview=overview, primary_structures=[authored[version]()])
    physical = codec.encode(rel)
    raw = merge.compact_json(physical)
    alphabet = ''.join(dict.fromkeys(merge.compact_json(messages) + raw))
    completed = advance(probe.semantic_json_parser(messages, alphabet), raw)
    assert completed.can_end() and json.loads(completed.projected_prefix()) == rel
    joined = core.semantic_node_local_v4_relations(stage, plan, bodies, codec.decode(physical))
    assert joined['overview']['primary_structures'][0]['node_refs'] == ['n1', 'n2']
    refs = tuple(m.saved_record_ref for m in p.frozen.members)
    leaf = core.prepare_semantic_leaf(p, refs)
    leaf_messages = core.semantic_node_local_v4_messages(leaf, 'RELATIONS', plan=plan, nodes=bodies)
    assert 'primary_structures' not in probe.semantic_output_schema(leaf_messages)['properties']


def test_history_merge_keeps_24_record_bindings_and_draws_the_admitted_choice_pair():
    import analysis_merge_wire as merge
    from analysis_plan_source_choices import WholeMapTitle, source_node_titles
    from test_analysis_cumulative import source_snapshot
    from test_analysis_v24_direct_capacity_recovery import bind_reply

    notes = [f'{n}番の見本を確認した。' for n in range(1, 25)]
    # The two choices live in different leaves and are both u2, not the
    # leading source in their respective nodes.
    notes[1], notes[13] = FIRST, SECOND
    snapshot = source_snapshot(24, tier='premium')
    for member, note in zip(snapshot['members'], notes, strict=True):
        member['original'].update(memo=note, memo_action='')
    parent = maps.prepare_semantic_map(OWNER, snapshot,
        prompt_version=core.SEMANTIC_MAP_OCCURRENCE_V24_PROFILE, primary_structures='karen.v3')
    refs = tuple(member.saved_record_ref for member in parent.frozen.members)

    def receipt(phase, messages, authored):
        raw = merge.compact_json(authored)
        return dict(phase=phase, messages_sha256=core.semantic_map_hash(messages), raw=raw,
                    raw_sha256=hashlib.sha256(raw.encode()).hexdigest(), finish_reason='stop', completion_tokens=100)

    leaves = []
    for index in (0, 12):
        leaf = core.prepare_semantic_leaf(parent, refs[index:index + 12])
        plan = nodes = None
        receipts = []
        for phase in core.SEMANTIC_MAP_NODE_LOCAL_V4_PHASES:
            messages = core.semantic_node_local_v4_wire_messages(leaf, phase, plan=plan, nodes=nodes)
            _, _, authored = bind_reply(messages)
            receipts.append(receipt(phase, messages, authored))
            if phase == 'PLAN':
                plan = core.admit_semantic_node_local_v4_plan_response(leaf, authored)
            if phase == 'NODES':
                nodes = core.admit_semantic_node_local_v4_nodes_response(leaf, plan, authored)
        leaves.append((leaf, response(leaf, dict(schema_version=core.semantic_node_local_v4_artifact_schema(leaf),
                                                  phases=receipts))))

    stage = core.prepare_semantic_merge(parent, tuple(leaves))
    material = json.loads(stage.material_json)
    assert [field['text'] for field in material['fields']] == notes
    assert all(field['fragment_is_complete_field'] for field in material['fields']) and not material['omitted_ranges']
    units = [[[(i, notes[i - 1])]] for i in range(1, 25)]
    raw_plan = packet(stage, [units[i] + units[i + 1] for i in range(0, len(units), 2)])
    plan = core.admit_semantic_node_local_v4_plan_response(stage, raw_plan, merge_anchors=True,
        merge_action_sources=True, context_sources=True, distinct_context_sources=True,
        speaker_context_sources=True, attributed_context_sources=True)
    fact_slots = core._semantic_node_fact_sources(plan, material, stage.prompt_version)
    raw_nodes = dict(schema_version=core._semantic_v4_schema('NODES'), plan_sha256=core.semantic_map_hash(
        ['analysis.node-facts.v1', 'NODES', stage.request_ref, plan]), nodes={})
    for node in plan['nodes']:
        ref = node['node_id']
        title = source_node_titles(material, node['units'], ())[0]
        raw_nodes['nodes'][ref] = dict(node_kind='CHOICE_OUTPUT', perspective='SELF', title=title, meaning='', units={
            unit: dict(evidence_ref=f'{ref}.{unit}', source_mode='RECORDED', fact_parts={key: ordinal}, unknowns=[])
            for (node_id, unit, key), (ordinal, _) in fact_slots.items() if node_id == ref})
    nodes = core.admit_semantic_node_local_v4_nodes_response(stage, plan, raw_nodes, bound_titles=True, ordered_titles=True)
    joined = core._semantic_v4_join(plan, nodes)
    axis = dict(v3_reading(), anchors=['n1.u2.e1', 'n7.u2.e1'])
    invalid = dict(axis, scope='self_report', anchors=['n1.u2.e1'])
    rel = dict(schema_version=core._semantic_v4_schema('RELATIONS'), nodes_sha256=core.semantic_map_hash(joined),
               qualification_review={}, edges=[], primary_structures=[invalid, axis],
               overview=dict(node_refs=list(nodes['nodes']), title_proposal='', title=WholeMapTitle(material, joined).neutral))

    def receipts_for(*, source_reading, primary_structures=None):
        receipts = []
        relations = rel if primary_structures is None else dict(rel, primary_structures=primary_structures)
        for phase, logical in zip(core.SEMANTIC_MAP_NODE_LOCAL_V4_PHASES, (raw_plan, raw_nodes, relations), strict=True):
            args = dict(plan=plan if phase != 'PLAN' else None, nodes=nodes if phase == 'RELATIONS' else None)
            messages = core.semantic_node_local_v4_wire_messages(stage, phase, **args, merge_source_reading=source_reading)
            restored = merge.legacy_messages(messages)
            if source_reading:
                old = core.semantic_node_local_v4_wire_messages(stage, phase, **args, merge_source_reading=False)
                assert restored[1] == merge.legacy_messages(old)[1]
                assert len(core.semantic_map_canonical(messages).encode()) <= len(core.semantic_map_canonical(old).encode())
            if phase == 'PLAN' and source_reading:
                assert '一文を丸ごと引用' in messages[0]['content']
            if phase == 'RELATIONS' and source_reading:
                assert 'self_reportは使いません。' in messages[0]['content']
                assert 'n1.u2.e1 (record 2), n7.u2.e1 (record 14)' in messages[0]['content']
            assert len(core.semantic_map_canonical(messages).encode()) < core.SEMANTIC_HISTORY_MERGE_MAX_PROMPT_BYTES
            physical = merge.response_codec(messages).encode(logical)
            receipts.append(dict(receipt(phase, messages, physical), logical_messages_sha256=core.semantic_map_hash(restored)))
        return dict(schema_version=core.semantic_node_local_v4_artifact_schema(stage),
                    merge_wire_version=merge.JUDGMENT_VERSION, phases=receipts)

    previous, current = receipts_for(source_reading=False), receipts_for(source_reading=True)
    assert core.assemble_semantic_node_local_v4(stage, previous)['edges'] == []
    unsupported = core.assemble_semantic_node_local_v4(stage, receipts_for(source_reading=True, primary_structures=[invalid]))
    assert unsupported['overview']['primary_structures'] == unsupported['edges'] == []
    result = core.build_semantic_stage(stage, response(stage, current))
    assert result.coverage['mapped_count'] == 24
    private = result.artifact.private_evidence()
    assert {ref for node in private['graph']['nodes'] for ref in node['record_refs']} == set(refs)
    public = result.artifact.safe_projection(authenticated_owner_scope=OWNER)
    assert len(public['overview']['primary_structures']) == 1
    assert public['overview']['primary_structures'][0]['criterion'] == axis['criterion']
    edge, = public['edges']
    assert ('n1', 'n7') == (edge['from_ref'], edge['to_ref'])
    assert '私から引き受けた' in edge['label'] and '断った' in edge['label']
    for tier in ('free', 'plus', 'premium'):
        graph, description = service.map_projection_for_plan(public, tier)
        expected = dict(edge, explanation=edge['label']) if tier == 'free' else edge
        assert graph['edges'] == [expected]
        assert axis['criterion'] in description
        assert (axis['case_reading'] in description) == (tier != 'free')


@pytest.mark.parametrize('model_generation, configured, enabled', [
    ('4B', None, False), ('4B', 'karen.v3', False), ('4B', 'free_plus.v1', False),
    ('9B', None, False), ('9B', 'karen.v3', 'karen.v3'), ('9B', 'free_plus.v1', 'karen.v3'),
])
def test_direct_transport_primary_structure_mode_requires_the_pinned_9b_alias(monkeypatch, model_generation, configured, enabled):
    import analysis_model_source as sources

    monkeypatch.delenv('COCOLON_ANALYSIS_PRIMARY_STRUCTURE_READING', raising=False)
    monkeypatch.delenv('COCOLON_ANALYSIS_PLAN_READ_ROLLOUT', raising=False)
    if configured == 'free_plus.v1':
        monkeypatch.setenv('COCOLON_ANALYSIS_PLAN_READ_ROLLOUT', configured)
    elif configured:
        monkeypatch.setenv('COCOLON_ANALYSIS_PRIMARY_STRUCTURE_READING', configured)
    model = sources.SEMANTIC_OCCURRENCE_V24_MODEL if model_generation == '4B' else sources.SEMANTIC_OCCURRENCE_V24_9B_MODEL
    source = sources.SelfHostedSemanticAnalysisModelSource(endpoint='https://synthetic.invalid/v1/chat/completions',
        model=model, api_key='synthetic', semantic_prompt_version=core.SEMANTIC_MAP_OCCURRENCE_V24_PROFILE)
    assert sources.analysis_model_primary_structure_reading(source) == enabled


@pytest.mark.parametrize('fault', ['one_wish', 'one_record', 'duplicate_quote', 'unrelated_cases',
                                   'repeat_heading', 'raw_reference', 'raw_node_identifier',
                                   'raw_unit_identifier', 'question', 'copied_source',
                                   'multiple_record_self_report', 'multiple_record_single_scope', 'invented_force'])
def test_v3_keeps_the_graph_when_optional_structure_lacks_a_complete_reading(fault):
    p, plan, bodies = scenario(FIRST, FIRST if fault == 'duplicate_quote' else SECOND, version='karen.v3')
    nodes = core._semantic_v4_join(plan, bodies)
    material = json.loads(p.material_json)
    axis = v3_reading()
    if fault == 'one_wish':
        nodes[1]['units'][0]['source_mode'] = 'PERSON_WISH'
    elif fault == 'one_record':
        axis['anchors'].pop()
    elif fault == 'unrelated_cases':
        axis['case_reading'] = '会議では自分から手を挙げ、家では断ったという記録です。'
    elif fault == 'repeat_heading':
        axis['heading'] = axis['criterion'].rstrip('。')
    elif fault == 'raw_reference':
        axis['case_reading'] = 'n1.u1.e1とn2.u1.e1に選べる余地が書かれています。'
    elif fault == 'raw_node_identifier':
        axis['case_reading'] += '会議（n1）での選択です。'
    elif fault == 'raw_unit_identifier':
        axis['heading'] += '（ｎ２．ｕ１）'
    elif fault == 'question':
        axis = v3_renamed_previous_response()
    elif fault == 'copied_source':
        copied = '選べる余地が大切です。'
        axis['criterion'] = copied
        nodes[0]['units'][0]['evidence'][0]['quote'] = copied
    elif fault == 'multiple_record_self_report':
        axis['scope'] = 'self_report'
    elif fault == 'multiple_record_single_scope':
        axis['scope'] = 'in_this_record'
    elif fault == 'invented_force':
        axis['case_reading'] = '家では強制されて選べる余地がなかったので断りました。'
    assert core._read_primary_structures(p, material, nodes, [axis]) == []


def test_archived_real_list_only_response_is_readable_only_on_its_original_contract():
    # Verbatim model-authored axis from the one-shot fictional 4B RELATIONS run.
    old_axis = dict(anchors=['n1.u1.e1', 'n2.u1.e1'], scope='across_records', heading='選択の基準',
                    reading='会議では自分で選んだ仕事は引き受けたが、家では手伝うと決められて断った。')
    for version in ('karen.v1', 'karen.v2'):
        p, plan, bodies = scenario(FIRST, SECOND, version=version)
        material = json.loads(p.material_json)
        nodes = core._semantic_v4_join(plan, bodies)
        if version == 'karen.v1':
            assert core._read_primary_structures(p, material, nodes, [old_axis])[0]['description'] == old_axis['reading']
            continue
        with pytest.raises(core.AnalysisSemanticMapError):
            core._read_primary_structures(p, material, nodes, [old_axis])
        for incomplete in (dict(v2_reading(), criterion=''), dict(v2_reading(), criterion=FIRST),
                           dict(v2_reading(), criterion=v2_reading()['case_reading'])):
            with pytest.raises(core.AnalysisSemanticMapError):
                core._read_primary_structures(p, material, nodes, [incomplete])


def test_worker_selects_new_grammar_only_for_explicitly_enabled_9b_map(monkeypatch):
    import analysis_model_source as sources
    import analysis_if_model_source as if_sources
    from test_emlis_natural_reply_probe_http import probe

    for model, setting, enabled, if_alias in [
        (sources.SEMANTIC_OCCURRENCE_V24_MODEL, 'karen.v3', False, sources.SEMANTIC_EVENT_PLAN_BASE_MODEL),
        (sources.SEMANTIC_OCCURRENCE_V24_MODEL, 'free_plus.v1', False, sources.SEMANTIC_EVENT_PLAN_BASE_MODEL),
        (sources.SEMANTIC_OCCURRENCE_V24_9B_MODEL, None, False, sources.SEMANTIC_ANALYSIS_9B_MODEL),
        (sources.SEMANTIC_OCCURRENCE_V24_9B_MODEL, 'karen.v2', False, sources.SEMANTIC_ANALYSIS_9B_MODEL),
        (sources.SEMANTIC_OCCURRENCE_V24_9B_MODEL, 'karen.v3', 'karen.v3', sources.SEMANTIC_ANALYSIS_9B_MODEL),
        (sources.SEMANTIC_OCCURRENCE_V24_9B_MODEL, 'free_plus.v1', 'karen.v3', sources.SEMANTIC_ANALYSIS_9B_MODEL),
    ]:
        monkeypatch.setenv('COCOLON_ANALYSIS_MODEL_SOURCE', sources.SEMANTIC_SELECTOR)
        monkeypatch.setenv('COCOLON_ANALYSIS_MODEL', model)
        monkeypatch.setenv('COCOLON_ANALYSIS_MODEL_ENDPOINT', 'https://synthetic.invalid/v1/chat/completions')
        monkeypatch.setenv('COCOLON_ANALYSIS_MODEL_API_KEY', 'synthetic')
        monkeypatch.delenv('COCOLON_ANALYSIS_PRIMARY_STRUCTURE_READING', raising=False)
        monkeypatch.delenv('COCOLON_ANALYSIS_PLAN_READ_ROLLOUT', raising=False)
        if setting == 'free_plus.v1':
            monkeypatch.setenv('COCOLON_ANALYSIS_PLAN_READ_ROLLOUT', setting)
        elif setting:
            monkeypatch.setenv('COCOLON_ANALYSIS_PRIMARY_STRUCTURE_READING', setting)
        assert if_sources.application_analysis_if_model_source().model == if_alias
        source = sources.application_analysis_model_source()
        assert source.prompt_version == core.SEMANTIC_MAP_OCCURRENCE_V24_PROFILE
        assert sources.analysis_model_primary_structure_reading(source) == enabled
        p, plan, bodies = scenario(FIRST, SECOND, version=enabled)
        messages = core.semantic_node_local_v4_messages(p, 'RELATIONS', plan=plan, nodes=bodies)
        props = probe.semantic_output_schema(messages)['properties']
        assert ('primary_structures' in props) == bool(enabled)
        assert json.loads(messages[1]['content']).get('primary_structure_reading', False) == enabled

def test_native_9b_server_accepts_ordinary_and_v3_v24_with_one_pinned_identity():
    from http.server import ThreadingHTTPServer
    from threading import Thread
    import httpx
    from test_emlis_natural_reply_probe_http import probe

    old_model, new_model = probe.OCCURRENCE_V24_MODEL, probe.OCCURRENCE_V24_9B_MODEL

    def generate(messages, end, *, profile, output_tokens):
        return 'fictional transport result', 'stop', {'completion_tokens': 2}

    with ThreadingHTTPServer(('127.0.0.1', 0), probe.make_handler(generate,
            api_key='synthetic', model_name=probe.QWEN_9B_ANALYSIS_ALIAS, event_plan_model=new_model,
            max_new_tokens=4096, request_seconds=210, max_requests=0, deadline=float('inf'))) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            url = f'http://127.0.0.1:{server.server_port}/v1/chat/completions'
            with httpx.Client(trust_env=False) as client:
                for model, reading_version, accepted in [
                    (old_model, False, False), (old_model, 'karen.v3', False),
                    (new_model, False, True), (new_model, 'karen.v3', True),
                    (new_model, 'karen.v1', False), (new_model, 'karen.v2', False),
                ]:
                    p, plan, bodies = scenario(FIRST, SECOND, version=reading_version)
                    messages = core.semantic_node_local_v4_messages(p, 'RELATIONS', plan=plan, nodes=bodies)
                    reply = client.post(url, headers={'Authorization': 'Bearer synthetic'},
                        json=dict(model=model, messages=messages, max_tokens=2048, generation_seconds=30,
                                  stream=False, temperature=0, chat_template_kwargs={'enable_thinking': False}))
                    assert reply.status_code == (200 if accepted else 400)
                    if accepted:
                        assert reply.json()['model'] == model
        finally:
            server.shutdown()
            thread.join()

def test_omission_preserves_neighbors_and_checks_every_origin_before_publication():
    p, plan, bodies = scenario(FIRST, SECOND, version='karen.v2')
    nodes = core._semantic_v4_join(plan, bodies)
    material = json.loads(p.material_json)
    first = v2_reading()
    omitted = observed_v2_repeated_conclusion()
    last = dict(anchors=['n2.u1.e1'], scope='in_this_record',
                criterion='家での手伝いについては、ご自身にも決める余地があることを重んじています。',
                case_reading='手伝うと先に決まっていたことが、断るという選択につながっています。',
                heading='頼まれたときの返事')
    public = core._read_primary_structures(p, material, nodes, [first, omitted, last])
    assert [(axis['title'], axis['node_refs']) for axis in public] == [
        (first['heading'], ['n1', 'n2']), (last['heading'], ['n2'])]
    for bad in (dict(omitted, anchors=['n9.u1.e1']), dict(omitted, scope='across_records', anchors=['n1.u1.e1'])):
        with pytest.raises(core.AnalysisSemanticMapError):
            core._read_primary_structures(p, material, nodes, [first, bad, last])


@pytest.mark.parametrize('mode', ['karen.v3', 'free_plus.v1'])
def test_viewer_plan_projects_one_saved_version_without_leaking_paid_graph_or_text(monkeypatch, mode):
    from copy import deepcopy
    from datetime import datetime, timedelta, timezone
    from fastapi import HTTPException
    from report_artifact_read_service import get_detail

    rid = str(UUID(int=840))
    node_refs = ['n1', 'n2', 'n3', 'n4', 'n5', 'n6']
    nodes = [dict(node_ref=ref, node_kind='CHOICE_OUTPUT', perspective='SELF', title=f'{ref}の選択',
                  summary=f'{ref}の有料要約', explanation=f'{ref}の有料詳細', context=[f'{ref}の有料条件'],
                  unknowns=[f'{ref}の有料未確認'], evidence_badge_count=1) for ref in node_refs]
    edges = [dict(edge_ref=f'e{i}', from_ref=left, to_ref=right, relation_kind='CONTEXT_CONTRAST',
                  label=f'{i}の違い', explanation=f'{i}の有料関係')
             for i, (left, right) in enumerate((('n2', 'n3'), ('n3', 'n5'), ('n1', 'n4'), ('n1', 'n5')), 1)]
    axes = [dict(scope='across_records', title=title, description=criterion + '有料の比較説明です。',
                 criterion=criterion, node_refs=refs)
            for title, criterion, refs in [('優先', '時間を優先します。', ['n2', 'n3', 'n5']),
                                           ('確認', '確認を先にします。', ['n1', 'n4']),
                                           ('納得', '納得して進めます。', ['n6'])]]
    graph = dict(schema_version='cocolon.analysis.semantic_map.v1', wire_kind='watashi.map.v3',
                 projection_of=f'artifact:{UUID(rid).hex}@1', artifact_version=1, period_label='すべての記録',
                 overview=dict(title='本人の選び方', summary='有料の全体要約', primary_structures=axes),
                 nodes=nodes, edges=edges, accessibility_linear_order=node_refs)
    coverage = dict(profile='cumulative.v1', source_count=6, processed_count=6, mapped_count=6,
                    unparsed_count=0, excluded_count=0, exclusion_reasons={}, stale_supplement_count=0)
    row = dict(id=rid, report_type='latest', report_mode='standard', source_profile='cumulative.v1',
               title='わたしマップ', period_start='2026-01-01', period_end='2026-11-01', generated_at='2026-11-02',
               snapshot_month=None, captured_at=None, content_text=service._projection_text(graph),
               content_json=dict(watashiMap=graph, report_mode='standard', map_context=coverage))
    source = deepcopy(row)
    month = datetime.now(timezone(timedelta(hours=9))).date().replace(day=1).isoformat()
    tier = 'free'
    calls = []

    async def rpc(name, payload):
        calls.append(name)
        if name == 'analysis_cumulative_evidence':
            return {'tier': tier, 'items': []}
        assert name == 'analysis_cumulative_read'
        item = deepcopy(source)
        if payload['p_month'] or payload['p_history']:
            item.update(report_type='monthly', snapshot_month=month, captured_at='2026-11-02')
        return dict(items=[item], matched=True, subscription_tier=tier,
                    history_limit={'free': 2, 'plus': 12, 'premium': None}[tier])

    monkeypatch.setattr(service, '_rpc', rpc)
    monkeypatch.setattr('analysis_observed_service.observed_enabled', lambda: True)
    monkeypatch.setattr(service, '_project_evidence', lambda _owner, raw: raw['items'])
    switch = ('COCOLON_ANALYSIS_PLAN_READ_ROLLOUT' if mode == 'free_plus.v1' else
              'COCOLON_ANALYSIS_PRIMARY_STRUCTURE_READING')
    monkeypatch.setenv(switch, mode)

    def current(renderer='semantic.v3'):
        result = asyncio.run(service.ensure_map(OWNER, ensure=False))
        return service.map_response_for_renderer(result, renderer)

    def monthly(renderer='semantic.v3'):
        result = asyncio.run(service.ensure_map(OWNER, monthly=True, ensure=False))
        return service.map_response_for_renderer(result, renderer)

    def detail(renderer='semantic.v3'):
        result = asyncio.run(get_detail(user_id=OWNER, family='self_structure', report_id=rid, month=month))
        return service.map_response_for_renderer(result, renderer)

    free = current()
    assert free['map_plan_scoped'] and free['map_subscription_tier'] == 'free'
    assert free['report_id'] == rid == detail()['item']['id']
    assert all(axis['criterion'] in free['content_text'] for axis in axes)
    assert free['meta']['overview']['summary'] == free['content_text']
    assert '有料' not in json.dumps(free, ensure_ascii=False)
    assert [axis['node_refs'] for axis in free['meta']['overview']['primary_structures']] == [['n2', 'n3', 'n5'], [], []]
    assert [edge['edge_ref'] for edge in free['meta']['edges']] == ['e1', 'e2']
    assert detail()['item']['content_text'] == free['content_text']
    assert detail()['item']['content_json']['watashiMap'] == free['meta']
    assert monthly()['snapshot_month'] == month
    assert monthly()['meta'] == free['meta']
    assert monthly()['report_id'] == rid
    for renderer in ('semantic.v2', 'semantic.v1', None):
        latest = current(renderer)
        assert latest['content_text'] == free['content_text']
        if mode == 'karen.v3':
            assert latest['meta'] is None
            assert 'watashiMap' not in detail(renderer)['item']['content_json']
        else:
            projected = latest['meta']
            assert projected == monthly(renderer)['meta'] == detail(renderer)['item']['content_json']['watashiMap']
            assert projected['projection_of'] == graph['projection_of']
            assert projected['accessibility_linear_order'] == ['n2', 'n3', 'n5']
            if renderer:
                assert projected['overview'] == dict(title=graph['overview']['title'], summary=free['content_text'])
                assert [edge['edge_ref'] for edge in projected['edges']] == ['e1', 'e2']
            else:
                assert projected['wire_kind'] == 'watashi.map.v2' and projected['edges'] == []
            assert '有料' not in json.dumps(latest, ensure_ascii=False)
    with pytest.raises(HTTPException) as unauthorized:
        asyncio.run(service.map_evidence(OWNER, rid, 'n2', month=month))
    assert unauthorized.value.status_code == 404
    assert 'analysis_cumulative_evidence' not in calls

    tier = 'plus'
    plus = current()
    assert plus['map_subscription_tier'] == 'plus'
    assert plus['report_id'] == rid and plus['meta']['projection_of'] == free['meta']['projection_of']
    assert [axis['description'] for axis in plus['meta']['overview']['primary_structures']] == [axis['description'] for axis in axes]
    assert plus['meta']['overview']['summary'] == plus['content_text']
    assert [edge['edge_ref'] for edge in plus['meta']['edges']] == ['e1', 'e2', 'e3']
    assert asyncio.run(service.map_evidence(OWNER, rid, 'n1', month=month)) == {'items': []}
    assert detail()['item']['content_json']['watashiMap'] == plus['meta']
    assert monthly()['meta'] == plus['meta']
    if mode == 'free_plus.v1':
        assert current('semantic.v1')['meta']['overview']['summary'] == plus['content_text']
        assert '有料の比較説明' in current('semantic.v1')['meta']['overview']['summary']

    tier = 'premium'
    assert current()['meta'] == plus['meta']
    assert detail()['map_subscription_tier'] == 'premium'
    tier = 'free'
    assert current() == free
    assert row == source
    assert all(call.startswith('analysis_cumulative_') for call in calls)

    # With no independently supported relationship, the same verified conclusion
    # remains readable. A saved result with no accepted conclusion reveals no details.
    unsupported = deepcopy(graph)
    unsupported['edges'] = []
    figureless, text = service.map_projection_for_plan(unsupported, 'free')
    assert figureless['nodes'] == [] and figureless['edges'] == []
    assert text == free['content_text']
    unsupported['overview']['primary_structures'] = []
    figureless, text = service.map_projection_for_plan(unsupported, 'premium')
    assert figureless['nodes'] == [] and figureless['overview']['primary_structures'] == []
    assert '有料' not in text

    monkeypatch.delenv(switch)
    archived = current('semantic.v1')
    assert archived['map_plan_scoped']
    assert archived['meta']['overview']['summary'] == archived['content_text'] == free['content_text']
    assert archived['meta']['nodes'] == free['meta']['nodes']
    assert archived['meta']['edges'] == free['meta']['edges']
    assert '有料' not in json.dumps(archived, ensure_ascii=False)

    source['content_json']['watashiMap'] = unsupported
    source['content_text'] = service._projection_text(unsupported)
    historical = current('semantic.v1')
    assert historical['map_plan_scoped'] and historical['meta'] is None
    assert '有料' not in json.dumps(historical, ensure_ascii=False)


def test_v3_rejects_unwritten_priority_and_does_not_repeat_the_same_roots():
    prepared, plan, bodies = scenario(FIRST, SECOND, version='karen.v3')
    nodes = core._semantic_v4_join(plan, bodies)
    material = json.loads(prepared.material_json)
    grounded = v3_reading()
    overstated = dict(grounded, heading='最も重要な基準')
    repeated = dict(grounded, heading='引き受ける前の判断', decision_factor='余地',
                    criterion='引き受けるかどうかを自分で判断できる余地を大切にしています。',
                    case_reading='会議では余地があるため引き受け、家では先に決められていて断っています。',
                    anchors=list(reversed(grounded['anchors'])))
    admitted = core._read_primary_structures(prepared, material, nodes, [overstated, grounded, repeated])
    assert [axis['title'] for axis in admitted] == [grounded['heading']]


@pytest.mark.parametrize('shape', ['supported', 'recorded', 'reversed', 'thin', 'thin_recorded', 'planned'])
def test_v3_only_keeps_independent_decisions_supported_by_original_conditions(shape):
    from analysis_plan_source_choices import WholeMapTitle

    notes = ['通路に置ける幅だったので、私は小さい棚を買った。',
             '通路をふさぐ幅だと確かめたので、私は大きい棚を買わなかった。']
    axis = dict(v3_reading(), decision_factor='通路', heading='棚を選んだときの条件',
                criterion='この二つの場面では、通路をふさがずに置ける幅かどうかで棚を選んでいます。',
                case_reading='通路に置ける幅だったので、小さい棚を買いました。'
                             '通路をふさぐ幅だったので、大きい棚は買いませんでした。')
    label = '置ける幅で小さい棚を買ったが、通路をふさぐ幅で大きい棚を買わなかった。'
    if shape == 'reversed':
        axis.update(case_reading='通路に置ける幅だったので小さい棚を買いました。'
                                 '通路をふさぐ幅でしたが通路への影響は問題ないと確かめ、大きい棚は買いませんでした。')
        label = '置ける幅で小さい棚を買ったが、通路をふさぐ幅でも問題ないため大きい棚を買わなかった。'
    elif shape in ('thin', 'thin_recorded'):
        notes = ['川を見た。', '紅茶を飲んだ。']
        axis.update(decision_factor='対象物', criterion='この二つの場面では、対象物で行為を選んでいます。',
                    case_reading='川という対象物は見ました。紅茶という対象物は飲みました。')
        label = '川という対象では見ましたが、紅茶という対象では飲みました。'
    elif shape == 'planned':
        notes[1] = '通路をふさぐ幅だと確かめたので、私は大きい棚を買わないつもりだった。'
    prepared, plan, bodies = scenario(*notes, version='karen.v3')
    if shape in ('recorded', 'thin_recorded'):
        for node in bodies['nodes'].values():
            node['units']['u1']['source_mode'] = 'RECORDED'
    material = json.loads(prepared.material_json)
    nodes = core._semantic_v4_join(plan, bodies)
    edge = {'from': 'n1', 'to': 'n2', 'from_unit': 'n1.u1', 'to_unit': 'n2.u1',
            'from_source': notes[0][:16], 'to_source': notes[1][:16],
            'label': label, 'relation_kind': 'CONTEXT_CONTRAST'}
    packet = dict(schema_version=core._semantic_v4_schema('RELATIONS'), nodes_sha256=core.semantic_map_hash(nodes),
                  qualification_review={}, edges=[edge], primary_structures=[axis],
                  overview=dict(node_refs=['n1', 'n2'], title_proposal='', title=WholeMapTitle(material, nodes).neutral))
    joined = core.semantic_node_local_v4_relations(prepared, plan, bodies, packet)
    assert [node['node_id'] for node in joined['nodes']] == ['n1', 'n2']
    assert bool(joined['edges']) == (shape in ('supported', 'recorded'))
    assert bool(joined['overview']['primary_structures']) == (shape in ('supported', 'recorded'))
    assert packet['edges'] == [edge]
    assert packet['primary_structures'] == [axis]


def test_v3_keeps_a_written_choice_when_its_optional_meaning_adds_an_action():
    first = '通路に置ける幅だったので、私は小さい棚を買った。'
    second = '通路をふさぐ幅だと確かめたので、私は大きい棚を買わなかった。'
    prepared, plan, bodies = scenario(first, second, version='karen.v3')
    material = json.loads(prepared.material_json)
    for node in bodies['nodes'].values():
        node.update(node_kind='CHOICE_OUTPUT', perspective='SELF')
        node['units']['u1']['source_mode'] = 'RECORDED'
    invented = '通路の寸法を確認し、小さい棚を選びました。'
    grounded = '通路をふさぐ幅だと確認し、大きい棚を買いませんでした。'
    bodies['nodes']['n1']['meaning'] = invented
    bodies['nodes']['n2']['meaning'] = grounded
    nodes = core._semantic_v4_join(plan, bodies)
    packet = dict(schema_version=core._semantic_v4_schema('RELATIONS'), nodes_sha256=core.semantic_map_hash(nodes),
                  qualification_review={}, edges=[], primary_structures=[],
                  overview=dict(node_refs=['n1', 'n2'], title_proposal='', title='2件の記録を振り返って'))
    joined = core.semantic_node_local_v4_relations(prepared, plan, bodies, packet)
    assert [node['meaning'] for node in joined['nodes']] == ['', grounded]
    assert [node['units'][0]['evidence'][0]['quote'] for node in joined['nodes']] == [first, second]
    assert bodies['nodes']['n1']['meaning'] == invented
    assert packet['nodes_sha256'] == core.semantic_map_hash(nodes)

    sentences = core._semantic_display_sentences(material)
    fields = material['fields']
    left = core._bound_choice(fields[0], first, sentences)
    right = core._bound_choice(fields[1], second, sentences)
    assert core._choice_comparison_covers('通路に置ける幅で小さい棚を買いました。' + grounded, left, right)
    assert not core._choice_comparison_covers('通路に置ける幅だと確かめて小さい棚を買いました。' + grounded, left, right)
    assert not core._choice_comparison_covers('通路に置ける幅なので店員に話して買いました。' + grounded, left, right)
    assert core._choice_added_action('妨げになる可能性を排除した。', second)
    assert core._choice_added_action('通路をふさぐ幅か確認しなかった。', second)


def test_v3_across_records_allows_short_quotes_but_rejects_combined_full_sources():
    first = '通路に置ける幅だったので、私は小さい棚を買いました。'
    second = '通路をふさぐ幅だったので、私は大きい棚を買いませんでした。'
    prepared, plan, bodies = scenario(first, second, version='karen.v3')
    material = json.loads(prepared.material_json)
    nodes = core._semantic_v4_join(plan, bodies)
    axis = dict(v3_reading(), decision_factor='通路', heading='棚を選んだときの条件',
                criterion='この二つの場面では、通路をふさがずに置ける幅かどうかで棚を選んでいます。',
                case_reading='「通路に置ける幅」のときは小さい棚を買いました。'
                             '「通路をふさぐ幅」では大きい棚を買いませんでした。')
    admitted = core._read_primary_structures(prepared, material, nodes, [axis])
    assert admitted[0]['description'] == axis['criterion'] + axis['case_reading']

    for combined in (first + second, second + first):
        assert core._read_primary_structures(prepared, material, nodes, [dict(axis, case_reading=combined)]) == []


@pytest.mark.parametrize('raw_kind', ['absent', 'contradictory_edge', 'valid_edge', 'contradictory_axis'])
def test_v3_diagram_uses_exact_choices_after_independent_axis_admission(raw_kind):
    notes = ('机で見返せるので、私は作業手順をノートに書いた。',
             '作業場所で見返せないので、私は作業手順をノートに書かなかった。')
    prepared, plan, bodies = scenario(*notes, version='karen.v3')
    material = json.loads(prepared.material_json)
    nodes = core._semantic_v4_join(plan, bodies)
    axis = dict(v3_reading(), decision_factor='見返せるか', heading='作業手順を残す条件',
                criterion='作業手順をノートに書くかは、その場で見返せるかどうかで選んでいます。',
                case_reading='見返せるかが違い、机で見返せるときはノートに書きました。'
                             '作業場所で見返せないときは書きませんでした。')
    raw_label = '机で見返せるときは書きました。一方、作業場所で見返せないときも書きました。'
    if raw_kind == 'valid_edge':
        raw_label = '机で見返せるときは書きました。一方、作業場所で見返せないときは書きませんでした。'
    elif raw_kind == 'contradictory_axis':
        axis['case_reading'] = axis['case_reading'].replace('書きませんでした', '書きました')
    edge = {'from': 'n1', 'to': 'n2', 'from_unit': 'n1.u1', 'to_unit': 'n2.u1',
            'from_source': notes[0][:16], 'to_source': notes[1][:16],
            'label': raw_label, 'relation_kind': 'CONTEXT_CONTRAST'}
    raw_edges = [] if raw_kind == 'absent' else [edge]
    packet = dict(schema_version=core._semantic_v4_schema('RELATIONS'), nodes_sha256=core.semantic_map_hash(nodes),
                  qualification_review={}, edges=raw_edges, primary_structures=[axis],
                  overview=dict(node_refs=['n1', 'n2'], title_proposal='', title='2件の記録を振り返って'))
    joined = core.semantic_node_local_v4_relations(prepared, plan, bodies, packet)
    assert packet['edges'] == raw_edges == ([] if raw_kind == 'absent' else [edge])
    if raw_kind == 'contradictory_axis':
        assert not joined['edges'] and not joined['overview']['primary_structures']
        return
    assert joined['overview']['primary_structures'][0]['description'].endswith(axis['case_reading'])
    admitted, = joined['edges']
    assert (admitted['from_unit'], admitted['to_unit']) == ('n1.u1', 'n2.u1')
    expected = ('机で見返せる → 私は作業手順をノートに書いた／'
                '作業場所で見返せない → 私は作業手順をノートに書かなかった')
    assert admitted['label'] == (raw_label if raw_kind == 'valid_edge' else expected)


@pytest.mark.parametrize('source_variant', ['exact', 'different_object', 'different_reason', 'not_performed', 'different_actor'])
def test_v3_reads_the_confirmed_contrast_when_model_scope_is_too_wide(source_variant):
    first = '机で見返せるので、私は作業手順をノートに書いた。'
    second = '作業場所で見返せないので、私は作業手順をノートに書かなかった。'
    case_reading = '机で見返せるので、私は作業手順をノートに書きました。' + second
    if source_variant != 'exact':
        changes = {
            'different_object': ('作業手順を', '進捗を'),
            'different_reason': ('見返せない', '思い出せない'),
            'not_performed': ('書かなかった', '書かないつもりだった'),
            'different_actor': ('私は', '同僚は'),
        }
        before, after = changes[source_variant]
        case_reading = case_reading.removesuffix(second) + second.replace(before, after)
        second = second.replace(before, after)
    prepared, plan, bodies = scenario(first, second, version='karen.v3')
    nodes = core._semantic_v4_join(plan, bodies)
    axis = dict(v3_reading(), decision_factor='見返せるか', heading='見返せるか',
                criterion='作業手順をノートに書くかどうかは、その場で見返せるかどうかを基準に決めます。',
                case_reading=case_reading)
    packet = dict(schema_version=core._semantic_v4_schema('RELATIONS'), nodes_sha256=core.semantic_map_hash(nodes),
                  qualification_review={}, edges=[], primary_structures=[axis],
                  overview=dict(node_refs=['n1', 'n2'], title_proposal='', title='2件の記録を振り返って'))
    assert core._read_primary_structures(prepared, json.loads(prepared.material_json), nodes, [axis]) == []
    admitted = core.semantic_node_local_v4_relations(prepared, plan, bodies, packet)
    assert packet['primary_structures'] == [axis] and not packet['edges']
    if source_variant != 'exact':
        assert not admitted['overview']['primary_structures'] and not admitted['edges']
        return

    comparison, = admitted['overview']['primary_structures']
    assert comparison['criterion'] == 'この二つの記録では、見返せることが作業手順をノートに書く条件でした。'
    assert comparison['description'] == comparison['criterion'] + (
        '机で見返せるため、作業手順をノートに書きました。作業場所で見返せないため、書きませんでした。')
    assert comparison['node_refs'] == ['n1', 'n2']
    assert '書かなかった' in admitted['edges'][0]['label']


@pytest.mark.parametrize('fault', [None, 'wrong_anchor', 'wrong_factor', 'reversed_choice', 'both_outcomes'])
def test_v3_reads_original_choices_when_model_splits_the_cases(fault):
    first = '机で見返せるので、私は作業手順をノートに書いた。'
    second = '作業場所で見返せないので、私は作業手順をノートに書かなかった。'
    prepared, plan, bodies = scenario(first, second, version='karen.v3')
    nodes = core._semantic_v4_join(plan, bodies)
    comparison = dict(v3_reading(), decision_factor='作業場所の視認性（見返せるか見返せないか）',
                      criterion='確認できる環境がある場合、それを理由にノートに記録する。',
                      case_reading='机という場所で見返せる条件があったため、本人は手順をノートに書いた。')
    peer = dict(scope='in_this_record', anchors=['n2.u1.e1'], decision_factor='作業場所の視認性（見返せない）',
                criterion='確認できない環境ではノートに記録しない。',
                case_reading='作業場所で見返せない条件だったため、本人は手順をノートに書かなかった。',
                heading='ノートに書かない場面')
    if fault == 'wrong_anchor':
        peer['anchors'] = ['n1.u1.e1']
    elif fault == 'wrong_factor':
        peer['decision_factor'] = '作業場所の広さ'
    elif fault == 'reversed_choice':
        peer['case_reading'] = peer['case_reading'].replace('書かなかった', '書いた')
    elif fault == 'both_outcomes':
        peer['case_reading'] += comparison['case_reading']
    packet = dict(schema_version=core._semantic_v4_schema('RELATIONS'), nodes_sha256=core.semantic_map_hash(nodes),
                  qualification_review={}, edges=[], primary_structures=[comparison, peer],
                  overview=dict(node_refs=['n1', 'n2'], title_proposal='', title='2件の記録を振り返って'))

    admitted = core.semantic_node_local_v4_relations(prepared, plan, bodies, packet)
    axes = admitted['overview']['primary_structures']
    if fault:
        assert axes == [] and admitted['edges'] == []
    else:
        assert len(axes) == len(admitted['edges']) == 1
        assert axes[0]['criterion'] == 'この二つの記録では、見返せることが作業手順をノートに書く条件でした。'
        assert axes[0]['description'].endswith('作業場所で見返せないため、書きませんでした。')


@pytest.mark.parametrize('fault', [None, 'different_condition', 'different_source_actor', 'different_model_actor',
                                   'different_model_object', 'reversed_model_choice', 'unrelated_factor'])
def test_v3_keeps_explicit_ability_and_two_actual_choices_when_model_paraphrases(fault):
    first = '机で照合できるので、私は鍵の番号を手帳に書いた。'
    second = '廊下で照合できないので、私は鍵の番号を手帳に書かなかった。'
    case = ('机という環境では照合が可能だったため、鍵の番号を手帳に書いたが、'
            '廊下では照合ができなかったため、同じ鍵の番号も手帳に書かなかった。')
    factor = '場所の制約（照合可否）'
    if fault == 'different_condition':
        second = second.replace('照合できない', '確認できない')
    elif fault == 'different_source_actor':
        second = second.replace('私は', '同僚は')
    elif fault == 'different_model_actor':
        case = case.replace('ため、鍵', 'ため、同僚が鍵')
    elif fault == 'different_model_object':
        case = case.replace('同じ鍵の番号', '切符の番号')
    elif fault == 'reversed_model_choice':
        case = case.replace('書かなかった', '書いた')
    elif fault == 'unrelated_factor':
        factor = '手帳の大きさ'

    prepared, plan, bodies = scenario(first, second, version='karen.v3')
    nodes = core._semantic_v4_join(plan, bodies)
    axis = dict(v3_reading(), heading='場所による行動の分岐', decision_factor=factor, case_reading=case,
                criterion='照合が可能な環境であれば記録し、不可能であれば記録しない')
    packet = dict(schema_version=core._semantic_v4_schema('RELATIONS'), nodes_sha256=core.semantic_map_hash(nodes),
                  qualification_review={}, edges=[], primary_structures=[axis],
                  overview=dict(node_refs=['n1', 'n2'], title_proposal='', title='2件の記録を振り返って'))
    admitted = core.semantic_node_local_v4_relations(prepared, plan, bodies, packet)
    axes = admitted['overview']['primary_structures']
    if fault:
        assert axes == [] and admitted['edges'] == []
    else:
        comparison, = axes
        assert comparison['criterion'] == 'この二つの記録では、照合できることが鍵の番号を手帳に書く条件でした。'
        assert comparison['description'].endswith('机で照合できるため、鍵の番号を手帳に書きました。廊下で照合できないため、書きませんでした。')
        assert comparison['node_refs'] == ['n1', 'n2']
        assert admitted['edges'][0]['label'] == (
            '机で照合できる → 私は鍵の番号を手帳に書いた／廊下で照合できない → 私は鍵の番号を手帳に書かなかった')
