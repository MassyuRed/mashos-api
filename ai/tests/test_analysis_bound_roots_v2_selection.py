"""Selection-first ordering is a private author constraint, not meaning proof."""
from copy import deepcopy
import json

import pytest

import analysis_model_source as sources
import analysis_if_model_source as if_sources
import analysis_semantic_map as app
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from test_analysis_cumulative import OWNER
from test_analysis_node_local_native_profile import accepts
from test_emlis_natural_reply_probe_http import probe
import test_analysis_node_local_v4_phases as old
import test_analysis_node_local_bound_roots as bound
from test_analysis_event_plan_model_alias import environment

PROFILE = core.SEMANTIC_MAP_NODE_LOCAL_V4_BOUND_V2_PROFILE
ALIAS = sources.SEMANTIC_NODE_LOCAL_V4_BOUND_V2_MODEL
SCHEMA = core.SEMANTIC_MAP_NODE_LOCAL_V4_BOUND_V2_SCHEMA
original_packets = old.phase_packets
original_generated = old.generated_phase_values
original_artifact = old.artifact


def prepared():
    return app.prepare_semantic_map(OWNER,
        json.loads(old.prepared().source_snapshot_json), prompt_version=PROFILE)


def select_first(values):
    plan, nodes, relations = bound.prefixed(values)
    overview = relations['overview']
    relations['overview'] = dict(node_refs=overview['node_refs'], title=overview['title'])
    return plan, nodes, relations


def phase_packets(p):
    return select_first(original_packets(p))


def artifact(p, values=None):
    result = original_artifact(p, phase_packets(p) if values is None else values)
    result['schema_version'] = SCHEMA
    return result


def test_exact_private_alias_routes_and_if_keeps_original_adapter(monkeypatch):
    settings = environment(monkeypatch, model=ALIAS)
    source = sources.application_analysis_model_source()
    assert sources.analysis_model_prompt_version(source) == PROFILE
    assert source._settings == settings
    if_source = if_sources.application_analysis_if_model_source()
    assert if_source._settings_snapshot == settings
    assert if_source.model == sources.SEMANTIC_EVENT_PLAN_BASE_MODEL


def test_overview_selects_real_node_refs_before_free_title_only_in_v2():
    p = prepared()
    plan, nodes, relations = phase_packets(p)
    selected = core.semantic_node_local_v4_messages(p, 'RELATIONS', plan=plan, nodes=nodes)
    schema = probe.semantic_output_schema(selected)
    assert list(schema['properties']['overview']['properties']) == ['node_refs', 'title']
    assert accepts(relations, selected)
    reversed_value = deepcopy(relations)
    overview = reversed_value['overview']
    reversed_value['overview'] = dict(title=overview['title'], node_refs=overview['node_refs'])
    assert not accepts(reversed_value, selected)
    legacy = bound.prepared()
    old_plan, old_nodes, old_rel = bound.prefixed(original_packets(legacy))
    old_messages = core.semantic_node_local_v4_messages(legacy, 'RELATIONS', plan=old_plan, nodes=old_nodes)
    assert list(probe.semantic_output_schema(old_messages)['properties']['overview']['properties']) == ['title', 'node_refs']
    assert accepts(old_rel, old_messages)


def test_all_phase_materials_and_lesson_use_exact_profile_and_current_shape():
    p = prepared()
    plan, nodes, relations = phase_packets(p)
    for phase, value in zip(core.SEMANTIC_MAP_NODE_LOCAL_V4_PHASES, (plan, nodes, relations), strict=True):
        messages = core.semantic_node_local_v4_messages(p, phase, plan=plan, nodes=nodes)
        assert json.loads(messages[1]['content'])['author_profile'] == PROFILE
        assert accepts(value, messages)
    value = artifact(p)
    result, coverage = app.build_semantic_map(p, old.response(p, value))
    assert coverage['mapped_count'] == 2
    assert result.private_evidence()['graph']['meaning_review']['node_local_plan']['phase_artifact'] == value
    assert result.safe_projection(authenticated_owner_scope=OWNER)['wire_kind'] == 'watashi.map.v3'


def test_old_and_new_outer_identities_reject_rebinding_and_keep_source():
    p, v1 = prepared(), bound.prepared()
    assert p.fields == v1.fields and p.source_guard == v1.source_guard and p.frozen == v1.frozen
    assert p.request_ref != v1.request_ref
    with pytest.raises(core.AnalysisSemanticMapError, match='lineage_invalid'):
        core.assemble_semantic_node_local_v4(p, bound.artifact(v1))
    with pytest.raises(core.AnalysisSemanticMapError, match='lineage_invalid'):
        core.assemble_semantic_node_local_v4(v1, artifact(p))


def test_selected_refs_and_order_do_not_certify_unwritten_free_title():
    p = prepared()
    values = list(phase_packets(p))
    values[2]['overview'] = dict(node_refs=['n2'], title='本人は島へ旅行したい')
    selected = core.semantic_node_local_v4_messages(p, 'RELATIONS', plan=values[0], nodes=values[1])
    assert accepts(values[2], selected)
    value = artifact(p, values)
    result, _ = app.build_semantic_map(p, old.response(p, value))
    review = result.private_evidence()['graph']['meaning_review']['node_local_plan']
    assert review['meaning_status'] == 'UNASSESSED'
    assert review['full_source_semantic_coverage'] is False
    assert review['phase_artifact'] == value


def test_transport_and_existing_shared_deadline_guards_keep_v2_lineage(monkeypatch):
    monkeypatch.setattr(old, 'PROFILE', PROFILE)
    monkeypatch.setattr(old, 'ALIAS', ALIAS)
    monkeypatch.setattr(old, 'phase_packets', phase_packets)
    old.test_real_three_transport_requests_keep_original_raw_and_freeze_actual_registry()
    old.test_absolute_deadline_cancels_slow_continuous_stream(monkeypatch)
    old.test_cancellation_propagates_without_next_phase_or_retry()
    old.test_exhausted_total_token_budget_never_starts_second_generation()


def test_cohort_and_leaf_merge_source_views_keep_selection_order(monkeypatch):
    monkeypatch.setattr(old, 'PROFILE', PROFILE)
    monkeypatch.setattr(old, 'generated_phase_values', lambda p: select_first(original_generated(p)))
    monkeypatch.setattr(old, 'artifact', artifact)
    old.test_correction_cohort_full_explanation_and_leaf_merge_lineage_are_preserved(monkeypatch)


@pytest.mark.parametrize('alias,marker,status', [
    (ALIAS, PROFILE, 200),
    (ALIAS, core.SEMANTIC_MAP_NODE_LOCAL_V4_BOUND_PROFILE, 400),
    (sources.SEMANTIC_NODE_LOCAL_V4_BOUND_MODEL, PROFILE, 400),
    (sources.SEMANTIC_NODE_LOCAL_V4_MODEL, PROFILE, 400),
])
def test_native_alias_profile_pair_is_exact_in_v2(alias, marker, status, monkeypatch):
    monkeypatch.setattr(bound, 'PROFILE', PROFILE)
    bound.test_native_exact_alias_marker_pair_and_actual_phase_usage(alias, marker, status)


def occurrence_prepared():
    return app.prepare_semantic_map(OWNER, json.loads(old.prepared().source_snapshot_json),
        prompt_version=core.SEMANTIC_MAP_OCCURRENCE_PROFILE)


def test_occurrence_private_alias_selects_three_phase_transport_and_keeps_if(monkeypatch):
    alias = sources.SEMANTIC_OCCURRENCE_MODEL
    profile = core.SEMANTIC_MAP_OCCURRENCE_PROFILE
    environment(monkeypatch, model=alias)
    configured = sources.application_analysis_model_source()
    assert sources.analysis_model_prompt_version(configured) == profile
    assert if_sources.application_analysis_if_model_source().model == sources.SEMANTIC_EVENT_PLAN_BASE_MODEL
    monkeypatch.setattr(old, 'PROFILE', profile)
    monkeypatch.setattr(old, 'ALIAS', alias)
    monkeypatch.setattr(old, 'phase_packets', phase_packets)
    old.test_real_three_transport_requests_keep_original_raw_and_freeze_actual_registry()


@pytest.mark.parametrize('alias, marker, status', [
    (sources.SEMANTIC_OCCURRENCE_MODEL, core.SEMANTIC_MAP_OCCURRENCE_PROFILE, 200),
    (sources.SEMANTIC_OCCURRENCE_MODEL, PROFILE, 400),
    (ALIAS, core.SEMANTIC_MAP_OCCURRENCE_PROFILE, 400),
])
def test_native_occurrence_alias_requires_exact_marker(alias, marker, status):
    bound.test_native_exact_alias_marker_pair_and_actual_phase_usage(alias, marker, status)


def test_occurrence_filters_repeated_unknown_before_generation_legacy_retains_wire():
    current, legacy = occurrence_prepared(), prepared()
    plan, nodes, _ = phase_packets(current)
    messages = [core.semantic_node_local_v4_messages(source, 'NODES', plan=plan)
        for source in (current, legacy)]
    assert current.fields == legacy.fields and current.source_guard == legacy.source_guard
    assert current.request_ref != legacy.request_ref
    assert all(accepts(nodes, material) for material in messages)
    duplicated = deepcopy(nodes)
    unknowns = duplicated['nodes']['n2']['units']['u1']['unknowns']
    assert len(unknowns) == 1
    unknowns.append(deepcopy(unknowns[0]))
    assert not accepts(duplicated, messages[0])
    assert accepts(duplicated, messages[1])
    with pytest.raises(core.AnalysisSemanticMapError, match='lineage_invalid'):
        core.assemble_semantic_node_local_v4(current, artifact(legacy))


@pytest.mark.parametrize('stage', [None, 'MERGE'])
def test_example_separates_incidents_and_keeps_later_recollection_of_the_same_one(stage):
    material, packet = core._semantic_occurrence_lesson_material(stage)
    fields = {field['field']: field for field in material['fields']}
    earlier, later = packet['nodes'][0]['units']
    early_roots = earlier['evidence']
    late_roots = later['evidence']
    assert [fields[e['field']]['record'] for e in early_roots] == [1, 1, 2]
    assert '先週、隣室の試験中' in early_roots[-1]['quote']
    assert [fields[e['field']]['record'] for e in late_roots] == [2, 2]
    assert '翌週、隣室の試験が終わった日' in late_roots[0]['quote']
    assert all(fields[e['field']]['text'].count(e['quote']) == 1 for e in early_roots + late_roots)
    # Both incidents are written in the same later field. The completed example separates them.
    material_check = packet['nodes'][6]['units'][1]['evidence'][0]
    clip_replacement = packet['nodes'][7]['units'][1]['evidence'][0]
    assert material_check['field'] == clip_replacement['field'] == 3
    assert '材質表示を読み' in material_check['quote']
    assert '留め具へ交換' in clip_replacement['quote']


def test_leaf_example_uses_only_the_earlier_sources():
    material, packet = core._semantic_occurrence_lesson_material('LEAF')
    assert [row['record'] for row in material['records']] == [1]
    fields = {field['field']: field for field in material['fields']}
    for node in packet['nodes']:
        for unit in node['units']:
            for root in unit['evidence']:
                assert fields[root['field']]['text'].count(root['quote']) == 1
    assert '先週、隣室' not in json.dumps(packet, ensure_ascii=False)
    assert packet['edges'] == []


def test_original_dates_do_not_replace_correction_clock_or_cohort():
    from test_analysis_semantic_history_core import correction_snapshot
    prepared = app.prepare_semantic_map(OWNER, correction_snapshot(), prompt_version=core.SEMANTIC_MAP_OCCURRENCE_PROFILE)
    original = json.loads(prepared.material_json)
    wire = json.loads(prepared.messages()[1]['content'])
    dates = {row['record']: row['recorded_at'] for row in original['records']}
    cohort = next(f for f in original['fields'] if f['record'] is None)
    assert len(cohort['record_refs']) == 2 and cohort['source_recorded_at']
    for source, written in zip(original['fields'], wire['fields'], strict=True):
        expected = dict(source)
        if source['source_role'] == 'ORIGINAL_INPUT':
            expected['original_recorded_at'] = dates[source['record']]
        assert written == expected
    assert wire['map_corrections'] == original['map_corrections']


def test_non_original_fields_keep_their_own_source_context():
    material, _ = core._semantic_occurrence_lesson_material(None)
    update = dict(material['fields'][0], field=5, source_role='USER_INTERPRETATION_CORRECTION',
                  source_recorded_at='2026-07-11T12:00:00', text='私が話したのは前の練習のことです。')
    supplement = dict(material['fields'][1], field=6, source_role='SUPPLEMENTAL_ANSWER',
                      supplement=1, text='その日の試験は午前中でした。')
    material['fields'].extend((update, supplement))
    wire = json.loads(core._semantic_occurrence_message(material))
    assert wire['fields'][-2:] == [update, supplement]
    assert 'original_recorded_at' not in material['fields'][0]


def test_nodes_author_distinguishes_speech_action_and_knowledge_from_own_wish():
    snapshot = json.loads(old.prepared().source_snapshot_json)
    new = app.prepare_semantic_map(OWNER, snapshot, prompt_version=core.SEMANTIC_MAP_OCCURRENCE_PROFILE)
    previous = app.prepare_semantic_map(OWNER, snapshot, prompt_version=core.SEMANTIC_MAP_NODE_LOCAL_V4_BOUND_V2_PROFILE)
    plan, nodes, _ = phase_packets(new)
    for phase in core.SEMANTIC_MAP_NODE_LOCAL_V4_PHASES:
        authored = core.semantic_node_local_v4_messages(new, phase, plan=plan, nodes=nodes)
        controls = core.semantic_node_local_v4_messages(previous, phase, plan=plan, nodes=nodes)
        cues = ['未確認なのは奏が弓を張り替えたか', '望んだ行動を実施したことへ変えません']
        for cue in cues:
            assert (cue in authored[0]['content']) is (phase == 'NODES')
            assert cue not in authored[1]['content']
            assert cue not in controls[0]['content']




def _rel_example(stage, profile):
    text = core._semantic_v4_lesson(stage, 'RELATIONS', bound=True, author_profile=profile)
    user, answer = text.split('\n例入力=', 1)[1].split('\n例出力=', 1)
    nodes = json.loads(user)['candidate_nodes']
    roots = {node['node_id']: {root['quote'] for unit in node['units'] for root in unit['evidence']}
             for node in nodes}
    return roots, json.loads(answer.split('\n例はここまで。', 1)[0]), text


def test_occurrence_rel_reading_direction_keeps_judgement_and_trial_at_selected_ends():
    snapshot = json.loads(old.prepared().source_snapshot_json)
    occurrence = app.prepare_semantic_map(OWNER, snapshot, prompt_version=core.SEMANTIC_MAP_OCCURRENCE_PROFILE)
    previous = prepared()
    plan, nodes, _ = phase_packets(occurrence)
    cue = '矢印は関係を読む向きです。'
    for phase in core.SEMANTIC_MAP_NODE_LOCAL_V4_PHASES:
        inputs = core.semantic_node_local_v4_messages(occurrence, phase, plan=plan, nodes=nodes)
        assert (cue in inputs[0]['content']) == (phase == 'RELATIONS')
        assert cue not in core.semantic_node_local_v4_messages(previous, phase, plan=plan, nodes=nodes)[0]['content']
    for stage in (None, 'MERGE'):
        roots, answer, _ = _rel_example(stage, occurrence.prompt_version)
        edge = answer['edges'][0]
        judgement = '私は八回の結果だけで、重音を身につけたとは判断していない。'
        trial = '二本の弦が同時に鳴ったのは三回だった。'
        assert (edge['from'], edge['to']) == ('n6', 'n1')
        assert judgement in roots[edge['from']] and trial in roots[edge['to']]
        assert judgement not in roots[edge['to']] and trial not in roots[edge['from']]
        assert edge['label'] == '八回で習得したとは決めておらず、その試行で二本の弦が同時に鳴ったのは三回'


def test_occurrence_rel_overview_uses_supporting_refs_and_preserves_frozen_v2_lesson():
    import hashlib

    old_hashes = {None: '3cedc809bd9d81f6976215426c98bf257658e80ceb2beb21188614cbf6e94d1f',
                  'MERGE': 'e0bddcb503d1f69fbf09120977fa75bf19d41295bdbe5e571e07a695533c89c6'}
    expected = {'n1': '翌週、隣室の試験が終わった日に、私は重音を八回試した。',
                'n2': '翌週、私は講師の返答を読み、低い弦の指を先に置く手順だと確かめた。',
                'n7': '翌週、私は材質表示を読み、同じ支柱が樹脂製だと確かめた。',
                'n8': '私は赤い留め具を外し、青い留め具へ交換した。'}
    for stage, old_hash in old_hashes.items():
        roots, answer, _ = _rel_example(stage, core.SEMANTIC_MAP_OCCURRENCE_PROFILE)
        overview = answer['overview']
        assert overview['node_refs'] == list(expected)
        assert overview['title'] == '重音の練習と講師の返答、譜面台で確かめた材質と交換した留め具'
        assert all(quote in roots[ref] for ref, quote in expected.items())
        # Substituting an existing ID still loses the source of the fastener change.
        foil_refs = ['n1', 'n2', 'n7', 'n4']
        assert expected['n8'] not in set().union(*(roots[ref] for ref in foil_refs))
        _, _, frozen = _rel_example(stage, PROFILE)
        assert hashlib.sha256(frozen.encode()).hexdigest() == old_hash


@pytest.mark.parametrize('alias, profile, schema', [
    (sources.SEMANTIC_OCCURRENCE_V2_MODEL, core.SEMANTIC_MAP_OCCURRENCE_V2_PROFILE, core.SEMANTIC_MAP_OCCURRENCE_V2_SCHEMA),
    (sources.SEMANTIC_OCCURRENCE_V3_MODEL, core.SEMANTIC_MAP_OCCURRENCE_V3_PROFILE, core.SEMANTIC_MAP_OCCURRENCE_V3_SCHEMA),
    (sources.SEMANTIC_OCCURRENCE_V4_MODEL, core.SEMANTIC_MAP_OCCURRENCE_V4_PROFILE, core.SEMANTIC_MAP_OCCURRENCE_V4_SCHEMA),
])
def test_occurrence_alias_preserves_existing_if_and_user_projection(monkeypatch, alias, profile, schema):
    environment(monkeypatch, model=alias)
    assert sources.application_analysis_model_source().prompt_version == profile
    assert if_sources.application_analysis_if_model_source().model == sources.SEMANTIC_EVENT_PLAN_BASE_MODEL
    prior = occurrence_prepared()
    current = app.prepare_semantic_map(OWNER, json.loads(prior.source_snapshot_json), prompt_version=profile)
    assert current.frozen == prior.frozen and current.request_ref != prior.request_ref
    for prepared_map, expected_schema in (
            (prior, core.SEMANTIC_MAP_OCCURRENCE_SCHEMA),
            (current, schema)):
        packet = old.artifact(prepared_map, phase_packets(prepared_map))
        packet['schema_version'] = expected_schema
        artifact, coverage = app.build_semantic_map(prepared_map, old.response(prepared_map, packet))
        assert artifact.safe_projection(authenticated_owner_scope=OWNER)['wire_kind'] == 'watashi.map.v3'
        assert coverage['mapped_count'] == len(prepared_map.frozen.members)
        opposite = current if prepared_map is prior else prior
        with pytest.raises(core.AnalysisSemanticMapError, match='lineage_invalid'):
            core.assemble_semantic_node_local_v4(opposite, packet)
    monkeypatch.setattr(old, 'PROFILE', profile)
    monkeypatch.setattr(old, 'ALIAS', alias)
    monkeypatch.setattr(old, 'phase_packets', phase_packets)
    old.test_real_three_transport_requests_keep_original_raw_and_freeze_actual_registry()


@pytest.mark.parametrize('alias, marker, status', [
    (sources.SEMANTIC_OCCURRENCE_V2_MODEL, core.SEMANTIC_MAP_OCCURRENCE_V2_PROFILE, 200),
    (sources.SEMANTIC_OCCURRENCE_V3_MODEL, core.SEMANTIC_MAP_OCCURRENCE_V3_PROFILE, 200),
    (sources.SEMANTIC_OCCURRENCE_V4_MODEL, core.SEMANTIC_MAP_OCCURRENCE_V4_PROFILE, 200),
    (sources.SEMANTIC_OCCURRENCE_V4_MODEL, core.SEMANTIC_MAP_OCCURRENCE_V3_PROFILE, 400),
    (sources.SEMANTIC_OCCURRENCE_V3_MODEL, core.SEMANTIC_MAP_OCCURRENCE_V4_PROFILE, 400),
    (sources.SEMANTIC_OCCURRENCE_V2_MODEL, core.SEMANTIC_MAP_OCCURRENCE_V3_PROFILE, 400),
    (sources.SEMANTIC_OCCURRENCE_V3_MODEL, core.SEMANTIC_MAP_OCCURRENCE_V2_PROFILE, 400),
    (sources.SEMANTIC_OCCURRENCE_MODEL, core.SEMANTIC_MAP_OCCURRENCE_V2_PROFILE, 400),
    (sources.SEMANTIC_OCCURRENCE_V2_MODEL, core.SEMANTIC_MAP_OCCURRENCE_PROFILE, 400),
])
def test_native_occurrence_accepts_only_its_own_profile(alias, marker, status):
    bound.test_native_exact_alias_marker_pair_and_actual_phase_usage(alias, marker, status)


@pytest.mark.parametrize('stage', [None, 'MERGE'])
def test_occurrence_v2_distinguishes_revised_belief_from_replacing_the_same_object(stage):
    material, example = core._semantic_occurrence_lesson_material(stage, same_subject=True)
    original = {field['field']: field['text'] for field in material['fields']}
    inferred, confirmed = example['nodes'][6]['units']
    before_exchange, replacement = example['nodes'][7]['units']
    assert [inferred['source_mode'], confirmed['source_mode']] == ['PERSON_JUDGMENT', 'RECORDED']
    assert confirmed == before_exchange and replacement['source_mode'] == 'RECORDED'
    assert '金属だと思った' in inferred['evidence'][0]['quote']
    assert '同じ支柱が樹脂製だと確かめた' in confirmed['evidence'][0]['quote']
    assert '樹脂製の支柱を外し、木製の支柱を取り付けた' in replacement['evidence'][0]['quote']
    assert all(original[root['field']].count(root['quote']) == 1
               for unit in (inferred, confirmed, replacement) for root in unit['evidence'])
    belief, action = example['nodes'][6:8]
    assert '見立て' in belief['title'] and '交換' not in belief['title']
    assert '樹脂製と確認した支柱を木製に取り替えた' == action['title']
    assert example['edges'][1]['label'] == '支柱が樹脂製だと確かめ、その後に木製の支柱へ交換した'
    assert example['overview']['node_refs'][-2:] == ['n7', 'n8']
    assert '樹脂製と確かめてから交換した支柱' in example['overview']['title']
    assert '金属から' not in action['title'] + example['overview']['title']


def test_occurrence_v2_leaf_cannot_borrow_the_later_actual_replacement():
    _, example = core._semantic_occurrence_lesson_material('LEAF', same_subject=True)
    inferred, uninstalled = example['nodes'][3:]
    assert inferred['units'][0]['source_mode'] == 'PERSON_JUDGMENT'
    assert uninstalled['units'][0]['evidence'][0]['quote'] == '交換用の木製の支柱は、まだ取り付けていない。'
    assert all(root['field'] <= 2 for n in example['nodes'] for unit in n['units'] for root in unit['evidence'])
    assert '樹脂製' not in json.dumps(example, ensure_ascii=False)


@pytest.mark.parametrize('profile, phase, filtered', [
    (core.SEMANTIC_MAP_OCCURRENCE_PROFILE, 'NODES', False),
    (core.SEMANTIC_MAP_OCCURRENCE_V2_PROFILE, 'PLAN', False),
    (core.SEMANTIC_MAP_OCCURRENCE_V2_PROFILE, 'NODES', True),
    (core.SEMANTIC_MAP_OCCURRENCE_V3_PROFILE, 'NODES', True),
])
def test_occurrence_filter_reaches_single_greedy_model_generate(monkeypatch, profile, phase, filtered):
    import time
    from test_piece_model_server_constraints import synthetic_generator

    prepared_map = app.prepare_semantic_map(OWNER, json.loads(old.prepared().source_snapshot_json),
        prompt_version=profile)
    plan, nodes, _ = phase_packets(prepared_map)
    messages = core.semantic_node_local_v4_messages(prepared_map, phase, plan=plan)
    raw = json.dumps(plan if phase == 'PLAN' else nodes, ensure_ascii=False, separators=(',', ':'))
    real_loader = probe.load_generator

    def load_event_fixture(adapter, stop, **options):
        # Use the CPU fixture's second synthetic LoRA for the event-plan branch.
        mock_load = probe.load_piece_adapter
        def load_adapter(model, path, *, adapter_name, **verified):
            assert adapter_name == probe.EVENT_PLAN_ADAPTER_NAME
            mock_load(model, path, **verified)
        monkeypatch.setattr(probe, 'load_piece_adapter', load_adapter)
        for key in ('adapter', 'weights_sha256', 'config_sha256'):
            options['event_plan_' + key] = options.pop('piece_' + key)
        return real_loader(adapter, stop, **options)

    monkeypatch.setattr(probe, 'load_generator', load_event_fixture)
    generator, seen, _, _ = synthetic_generator(monkeypatch, constrained=True,
        with_piece_adapter=True, raw_output=raw)
    model = seen['model']
    def select_adapter(name, *, inference_mode=False):
        assert name in {'default', probe.EVENT_PLAN_ADAPTER_NAME}
        model.active_adapter, model.grads = name, not inference_mode
    monkeypatch.setattr(model, 'set_adapter', select_adapter)
    result, finish, usage = generator(messages, time.monotonic() + 60, profile='event_plan', output_tokens=4096)
    assert result == raw and finish == 'stop' and usage['completion_tokens'] > 0
    assert len(seen['generate']) == 1
    options = seen['generate'][0]
    assert options['num_beams'] == 1 and options['do_sample'] is False
    assert ('logits_processor' in options) is filtered
    assert model.active_adapter == 'default'


def test_occurrence_public_duplicate_filter_preserves_related_but_distinct_nodes():
    p = occurrence_prepared()
    plan, bodies, _ = phase_packets(p)
    first = bodies['nodes']['n1']
    repeated = deepcopy(first)
    repeated['perspective'] = 'OBSERVED_INTERACTION'
    bodies['nodes'] = {'n1': first, 'n2': repeated}
    assert probe._occurrence_duplicate_prefix(json.dumps(bodies, ensure_ascii=False))
    repeated['title'] = '同じ記録にある別の判断'
    assert not probe._occurrence_duplicate_prefix(json.dumps(bodies, ensure_ascii=False))


def test_occurrence_duplicate_at_meaning_limit_keeps_distinct_last_character():
    p = occurrence_prepared()
    _, bodies, _ = phase_packets(p)
    first = bodies['nodes']['n1']
    first['meaning'] = '灯' * 240
    second = deepcopy(first)
    bodies['nodes'] = {'n1': first, 'n2': second}
    encoded = json.dumps(bodies, ensure_ascii=False, separators=(',', ':'))
    last = encoded.rindex('灯' * 240) + 240
    assert not probe._occurrence_duplicate_prefix(encoded[:last-1])
    assert probe._occurrence_duplicate_prefix(encoded[:last])
    assert not probe._occurrence_duplicate_prefix(encoded[:last-1] + '別')


def test_occurrence_duplicate_comparison_ignores_only_terminal_padding_and_repeat_stops():
    first = dict(u1=dict(fact='支柱の表示を確かめた。'))
    signature = probe._occurrence_visible_signature
    expected = signature(first, '支柱の確認', first['u1']['fact'])
    assert signature(first, '支柱の確認　', '支柱の表示を確かめた。。　') == expected
    assert signature(first, '支柱の確認', '支柱の表示を確かめた？') != expected
    assert signature(first, '支柱の確認', '樹脂製と確かめた。') != expected


@pytest.mark.parametrize('stage', [None, 'MERGE'])
def test_occurrence_v3_models_the_object_of_a_written_correction(stage):
    material, packet = core._semantic_occurrence_lesson_material(stage, same_subject=True, written_object=True)
    practice = packet['nodes'][4]
    plan, notation = practice['units']
    source = next(row['text'] for row in material['fields'] if row['field'] == 4)
    for unit in (plan, notation):
        assert all(e['quote'] in source for e in unit['evidence'])
    assert plan['source_mode'] == 'DECIDED_PLAN' and 'まだその練習はしていない' in plan['evidence'][0]['quote']
    assert notation['source_mode'] == 'RECORDED' and '欄の曜日' in notation['evidence'][0]['quote']
    assert '移すつもりはなかった' in notation['evidence'][0]['quote']
    assert '移すつもりはなく' in notation['fact'] and '練習日を移す意図はなく' in practice['title']
    assert '移す意図はありません' in practice['meaning'] and '曜日欄の記載' in practice['meaning']
    # The material check and the later actual replacement still share one root.
    belief, replacement = packet['nodes'][6:8]
    assert belief['units'][1]['evidence'] == replacement['units'][0]['evidence']


@pytest.mark.parametrize('field', ['title', 'meaning', 'fact', 'edge', 'overview'])
def test_occurrence_v3_rejects_unquoted_serialization_in_authored_public_fields(field):
    p = app.prepare_semantic_map(OWNER,
        json.loads(old.prepared().source_snapshot_json), prompt_version=core.SEMANTIC_MAP_OCCURRENCE_V3_PROFILE)
    plan, nodes, relations = phase_packets(p)
    residue = '本人は図面を保存しました。},'
    if field in {'title','meaning','fact'}:
        target = nodes['nodes']['n1']
        if field == 'fact':
            target = target['units']['u1']
        target[field] = residue
        with pytest.raises(core.AnalysisSemanticMapError, match='authored_serialization_residue'):
            core.semantic_node_local_v4_nodes(p, plan, nodes)
    else:
        if field == 'edge':
            relations['edges'] = [{'from':'n1', 'to':'n2',
                'relation_kind': sorted(core.SEMANTIC_MAP_RELATION_KINDS)[0], 'label':residue}]
        else:
            relations['overview']['title'] = residue
        with pytest.raises(core.AnalysisSemanticMapError, match='authored_serialization_residue'):
            core.semantic_node_local_v4_relations(p, plan, nodes, relations)


def test_occurrence_v3_preserves_quoted_code_and_reports_without_rewriting():
    literal = '入力例は「完了。},」です。'
    code = '完了。},'
    for prose in (literal, code, '例の最終行\n' + code, 'コードは {"status": "ok"},'):
        assert core._semantic_occurrence_check_prose(prose, [literal]) is None
    with pytest.raises(core.AnalysisSemanticMapError, match='authored_serialization_residue'):
        core._semantic_occurrence_check_prose('私が保存しました。},\n翌朝に確かめました。', ['保存した。'])


def test_occurrence_v3_allows_shared_evidence_with_distinct_claims():
    p = app.prepare_semantic_map(OWNER,
        json.loads(old.prepared().source_snapshot_json), prompt_version=core.SEMANTIC_MAP_OCCURRENCE_V3_PROFILE)
    _, nodes, _ = phase_packets(p)
    first = nodes['nodes']['n1']
    first['meaning'] = '用意した図面は保存済みです。'
    second = deepcopy(first)
    second['meaning'] = '保存した時点では、送信は済んでいません。'
    core._semantic_occurrence_check_nodes({'n1': first, 'n2': second})
    second['meaning'] = first['meaning']
    with pytest.raises(core.AnalysisSemanticMapError, match='repeated_authored_reading'):
        core._semantic_occurrence_check_nodes({'n1': first, 'n2': second})



def test_occurrence_v3_general_nodes_instruction_keeps_example_subject_in_the_lesson():
    p = app.prepare_semantic_map(OWNER,
        json.loads(old.prepared().source_snapshot_json), prompt_version=core.SEMANTIC_MAP_OCCURRENCE_V3_PROFILE)
    plan, _, _ = phase_packets(p)
    instruction = core.semantic_node_local_v4_messages(p, 'NODES', plan=plan)[0]['content']
    lesson, general = instruction.rsplit('例はここまで。', 1)
    assert '練習帳' in lesson and '練習日' in lesson
    assert '練習帳' not in general and '練習日' not in general
    assert '記録上の表記と、その表記が指す予定・対象' in general


def test_occurrence_v4_unknown_can_keep_only_the_locally_qualified_clause():
    tail = '登録されたかはまだ分からない。'
    root = '本人は検査票を受け取ったが、' + tail
    snapshot = json.loads(old.prepared().source_snapshot_json)
    snapshot['members'][0]['original']['memo'] = root + '封筒を渡したが、到着時刻は未確認。'
    for profile, expected in ((core.SEMANTIC_MAP_OCCURRENCE_V3_PROFILE, False),
                              (core.SEMANTIC_MAP_OCCURRENCE_V4_PROFILE, True)):
        current = app.prepare_semantic_map(OWNER, snapshot, prompt_version=profile)
        plan, nodes, _ = phase_packets(current)
        first_unit = plan['nodes'][0]['units'][0]
        first_unit['evidence'][0]['quote'] = root
        nodes['plan_sha256'] = core.semantic_map_hash(plan)
        unit = nodes['nodes']['n1']['units']['u1']
        unit['assigned_evidence'] = core._semantic_v4_assigned_evidence(first_unit)
        messages = core.semantic_node_local_v4_messages(current, 'NODES', plan=plan)

        unit['unknowns'] = [dict(source_quote=root, source_field=1)]
        assert accepts(nodes, messages)
        unit['unknowns'] = [dict(source_quote=tail, source_field=1)]
        assert accepts(nodes, messages) == expected
        assert core.semantic_node_local_v4_nodes(current, plan, nodes) is nodes

        for wrong_quote, wrong_field in ((tail, 2), ('到着時刻は未確認。', 1), ('登録済み。', 1)):
            unit['unknowns'] = [dict(source_quote=wrong_quote, source_field=wrong_field)]
            assert not accepts(nodes, messages)
            with pytest.raises(core.AnalysisSemanticMapError):
                core.semantic_node_local_v4_nodes(current, plan, nodes)


@pytest.mark.parametrize('quoted', ['「まず、内側。次、最後」', '『「内、側」。次』', '“内、側。”',
                                    '（参照、未確定。）', '"内、側。"', '`内、側。`'])
def test_occurrence_v4_qualification_preserves_quoted_commas(quoted):
    text = quoted + 'と書いたが、結果はまだ届いていない。'
    assert probe._semantic_sentence_quotes(text, qualification_tails=True) == ['結果はまだ届いていない。']


def test_occurrence_v4_qualification_preserves_length_uniqueness_and_boundary_ambiguity():
    options = lambda text: probe._semantic_sentence_quotes(text, qualification_tails=True)
    valid = '未' * 239 + '。'
    assert options('前段、' + valid) == [valid]
    assert options('前段、未' + valid) == []
    assert options('前段、その後は不明。別件、その後は不明。') == []
    assert options('「前段、その後は不明。') == []
    assert options('前段、その後は不明。】') == []


@pytest.mark.parametrize('stage', [None, 'LEAF', 'MERGE'])
def test_occurrence_v4_reporting_contrast_is_phase_local_and_outside_source(stage):
    def lesson(phase, profile):
        return core._semantic_v4_lesson(stage, phase, bound=True, author_profile=profile)
    current = core.SEMANTIC_MAP_OCCURRENCE_V4_PROFILE
    previous = core.SEMANTIC_MAP_OCCURRENCE_V3_PROFILE
    for phase in ('PLAN', 'NODES', 'RELATIONS'):
        text = lesson(phase, current)
        example, full_lesson = text.split('架空完成例', 1)
        assert '藍布' not in full_lesson and '藍布' not in lesson(phase, previous)
        if phase == 'PLAN':
            assert not example.strip()
            continue
        assert '染め終えたと返事' in example and '染められると返事' in example
        assert example.count('私は伝票で枚数を確かめた') == 2
        if phase == 'NODES':
            assert '工房からの染色完了の知らせ' in example
            assert '染色が可能だという工房の返事' in example
            assert example.count('本人の枚数確認') == 2
        else:
            assert '染色完了の知らせを受け、枚数を照合' in example
            assert '染色できるという返事を受け、枚数を照合' in example
            assert ('知らせと照合が線の両端なら' in example) is (stage != 'LEAF')


def test_occurrence_v4_plan_example_keeps_occurrences_and_shared_referent_in_their_source():
    profile = core.SEMANTIC_MAP_OCCURRENCE_V4_PROFILE
    caption = '別の架空例（今回の本人事実ではない）。原文欄='
    for stage in (None, 'LEAF', 'MERGE'):
        for phase in ('PLAN', 'NODES', 'RELATIONS'):
            text = core._semantic_v4_lesson(stage, phase, bound=True, author_profile=profile)
            assert (caption in text) is (stage is None and phase == 'PLAN')

    lesson = core._semantic_v4_lesson(None, 'PLAN', bound=True, author_profile=profile)
    field_line, plan_line, _ = lesson.split(caption, 1)[1].split('\n', 2)
    fields = json.loads(field_line)
    plan = json.loads(plan_line.removeprefix('根拠選択例='))
    evidence = [node['units'][0]['evidence'] for node in plan['nodes']]
    for unit in evidence:
        for quote in unit:
            assert fields[str(quote['field'])].count(quote['quote']) == 1
    first, later, applied, recorded = evidence
    assert first[0]['field'] != later[0]['field']
    assert applied[0] == recorded[0] and applied[1] != recorded[1]
