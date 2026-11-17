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
