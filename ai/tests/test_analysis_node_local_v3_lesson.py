"""Fictional instruction/source/view checks, never a model quality verdict."""
from copy import deepcopy
import json

import pytest

import analysis_semantic_map as app
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from cocolon_meaning_experience_engine.cores.analysis import intent_compiler as compiler
from test_analysis_semantic_map import OWNER, response, sample
from test_analysis_semantic_node_local_v3 import packet, prepared

PROFILE = 'semantic_map.node_local.v3'


def lesson(stage=None):
    text = core._semantic_node_local_v3_lesson_instruction(stage)
    material, output = text.split('\n例入力=', 1)[1].split('\n例出力=', 1)
    return json.loads(material), json.loads(output.split('\n例はここまで。', 1)[0])


def lesson_source(material):
    snapshot = sample()
    snapshot['members'] = snapshot['members'][:len(material['records'])]
    snapshot['period_start'] = '2026-07-01T00:00:00+00:00'
    snapshot['now'] = snapshot['period_end'] = material['analysis_as_of']
    for row, member in zip(material['records'], snapshot['members'], strict=True):
        original = member['original']
        original.update(created_at=row['recorded_at'], category=row['selected_categories'],
            emotions=row['selected_emotions'], emotion_details=row['emotion_details'])
        for name in ('memo', 'memo_action'):
            original[name] = next(field['text'] for field in material['fields']
                if field['record'] == row['record'] and field['field_path'] == name)
    return snapshot


@pytest.mark.parametrize('stage', [None, 'LEAF', 'MERGE'])
def test_complete_current_lesson_compiles_its_own_exact_source_and_native_contract(stage):
    from test_analysis_node_local_native_profile import accepts
    material, authored = lesson(stage)
    snapshot = lesson_source(material)
    before = deepcopy(snapshot)
    source = app.prepare_semantic_map(OWNER, snapshot, prompt_version=PROFILE)
    assert json.loads(source.material_json)['fields'] == material['fields']
    if stage == 'LEAF':
        source = core.prepare_semantic_leaf(source, (source.frozen.members[0].saved_record_ref,))
    result = response(source, authored)
    if stage == 'LEAF':
        graph = core.build_semantic_stage(source, result)
        assert type(graph) is compiler.AnalysisSemanticMapGraph
        graph_nodes = json.loads(graph.nodes_json)
        assert json.loads(graph.coverage_json)['mapped_count'] == 1
    else:
        artifact, coverage = app.build_semantic_map(source, result)
        graph_nodes = artifact.private_evidence()['graph']['nodes']
        assert coverage['mapped_count'] == 2 and coverage['unparsed_count'] == 0
        assert artifact.safe_projection(authenticated_owner_scope=OWNER)['wire_kind'] == 'watashi.map.v3'
    assert accepts(authored, source.messages())
    fields = {field['field']: field for field in material['fields']}
    for node in authored['nodes']:
        for unit in node['units']:
            # The complete example demonstrates one episode per unit, rather
            # than a verb distributed over unrelated dates or source records.
            assert len({fields[root['field']]['record'] for root in unit['evidence']}) == 1
            for root in unit['evidence']:
                assert fields[root['field']]['text'].count(root['quote']) == 1
    assert snapshot == before and len(graph_nodes) == len(authored['nodes'])


def test_lesson_distinguishes_confirmation_remaining_unknown_wish_plan_and_judgment():
    material, authored = lesson()
    artifact, _ = app.build_semantic_map(
        source := app.prepare_semantic_map(OWNER, lesson_source(material), prompt_version=PROFILE),
        response(source, authored))
    nodes = artifact.safe_projection(authenticated_owner_scope=OWNER)['nodes']
    assert nodes[1]['unknowns'] == []
    assert '確かめる状態へ' in nodes[1]['summary']
    assert nodes[3]['unknowns'] == ['奏が実際に弓を張り替えたかは聞いていない。']
    assert '弾くつもりのない' in nodes[2]['title']
    assert '弾くつもりはありません' in nodes[2]['explanation']
    assert authored['nodes'][2]['units'][0]['source_mode'] == 'PERSON_WISH'
    assert authored['nodes'][4]['units'][0]['source_mode'] == 'DECIDED_PLAN'
    assert 'その練習はまだ' in nodes[4]['explanation']
    assert authored['nodes'][5]['units'][0]['source_mode'] == 'PERSON_JUDGMENT'
    assert '身につけたとは判断していません' in nodes[5]['explanation']
    for node in authored['nodes'][:2]:
        assert node['meaning']
        assert node['meaning'] not in {unit['fact'] for unit in node['units']}
        assert node['meaning'] != ''.join(unit['fact'] for unit in node['units'])
    private = artifact.private_evidence()['graph']['meaning_review']
    assert private['node_local_plan']['plan'] == authored
    assert private['node_local_plan']['meaning_status'] == 'UNASSESSED'
    assert private['node_local_plan']['full_source_semantic_coverage'] is False


def test_leaf_lesson_keeps_only_its_earlier_state_and_cannot_borrow_later_confirmation():
    material, authored = lesson('LEAF')
    assert len(material['records']) == 1 and authored['edges'] == []
    assert authored['nodes'][1]['units'][0]['unknowns'] == [
        dict(source_field=2, source_quote='講師からの返答はまだ来ていない。')]
    assert '翌週' not in core.semantic_map_canonical(material)
    # The lesson must not teach the author to import a later record's person,
    # objects, results, or confirmation into an earlier single-record leaf.
    leaf = core.semantic_map_canonical(dict(input=material, output=authored))
    assert all(later not in leaf for later in (
        '奏', '張り替え', '低い弦の指', '八回', '三回', '次の火曜', '確かめた'))
    source = app.prepare_semantic_map(OWNER, lesson_source(material), prompt_version=PROFILE)
    source = core.prepare_semantic_leaf(source, (source.frozen.members[0].saved_record_ref,))
    value = deepcopy(authored)
    value['nodes'][1]['units'].append(lesson()[1]['nodes'][1]['units'][1])
    with pytest.raises(core.AnalysisSemanticMapError):
        core.build_semantic_stage(source, response(source, value))


def test_worked_example_is_instruction_only_and_cannot_be_cited_as_the_person_source():
    source = prepared()
    original_fields = source.fields
    material, authored = lesson()
    assert 'チェロ' in source.messages()[0]['content']
    assert 'チェロ' not in source.material_json
    with pytest.raises(core.AnalysisSemanticMapError):
        app.build_semantic_map(source, response(source, authored))
    assert source.fields == original_fields
    for old_profile in ('semantic_map.v1', 'semantic_map.event_plan.v1', 'semantic_map.event_plan.v2'):
        assert 'チェロ' not in prepared(old_profile).messages()[0]['content']


@pytest.mark.parametrize('copy_kind', ['first-fact', 'joined-facts', 'concatenated-facts'])
def test_derived_body_omits_only_exact_fact_copy_meaning_and_keeps_authored_plan(copy_kind):
    source, value = prepared(), packet()
    facts = [unit['fact'] for unit in value['nodes'][0]['units']]
    value['nodes'][0]['meaning'] = {
        'first-fact': facts[0], 'joined-facts': '\n'.join(facts),
        'concatenated-facts': ''.join(facts)}[copy_kind]
    original = deepcopy(value)
    artifact, _ = app.build_semantic_map(source, response(source, value))
    node = artifact.safe_projection(authenticated_owner_scope=OWNER)['nodes'][0]
    assert node['summary'] == value['nodes'][0]['meaning']
    assert node['explanation'].split('\n')[:2] == facts
    assert all(node['explanation'].count(fact) == 1 for fact in facts)
    assert artifact.private_evidence()['graph']['meaning_review']['node_local_plan']['plan'] == original
    assert value == original


@pytest.mark.parametrize('meaning', [
    '下書きの時点では未送信で、確認後には案内を直して送信しています。',
    'まだ送っていないという当時の状態は、後日の送信済みと区別します。',
    '同じ説明に見えても、当時はまだ送っていませんでした。',
])
def test_distinct_time_and_negation_qualifications_are_never_deleted_as_repetition(meaning):
    value = packet()
    value['nodes'][0]['meaning'] = meaning
    graph = compiler.compile_analysis_semantic_map(prepared(), value, response_sha256='a' * 64)
    node = json.loads(graph.nodes_json)[0]
    assert meaning in node['explanation'] and node['summary'] == meaning
    assert graph.meaning_review_json


def test_exact_paragraph_identity_does_not_normalize_punctuation_or_whitespace():
    value = packet()
    first = value['nodes'][0]['units'][0]['fact']
    value['nodes'][0]['meaning'] = first.replace('。', ' 。')
    graph = compiler.compile_analysis_semantic_map(prepared(), value, response_sha256='a' * 64)
    node = json.loads(graph.nodes_json)[0]
    assert first in node['explanation']
    assert value['nodes'][0]['meaning'] in node['explanation']
