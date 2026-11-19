"""Both validators compare a multirecord title to the records it actually cites."""
import json

import pytest

import analysis_plan_source_choices as choices
import analysis_semantic_map as maps
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from test_analysis_cumulative import OWNER
from test_analysis_node_local_native_profile import accepts
from test_analysis_v13_separate_record_titles import combined, stages, wire


def prepare(notes, profile):
    _, current, plan, bodies = stages(*notes)
    prepared = maps.prepare_semantic_map(OWNER, json.loads(current.source_snapshot_json), prompt_version=profile)
    for node in bodies['nodes'].values():
        node['units']['u1']['unknowns'] = []
    return prepared, plan, bodies


@pytest.mark.parametrize('version,refs,title,expected', [
    (15, ['n1', 'n2'], '翌日、予約が届いた。、', True),
    (16, ['n1', 'n2'], '翌日、予約が届いた。、', False),
    (16, ['n2'], '翌日、予約が届いた。', True),
    (16, ['n2', 'n1'], '下書き、その翌日に予約を確認', True),
    (16, ['n1', 'n2'], '翌日、予約が届いた。下書きも保存済み', True),
])
def test_overview_compares_only_its_selected_records(version, refs, title, expected):
    profile = getattr(core, f'SEMANTIC_MAP_OCCURRENCE_V{version}_PROFILE')
    p, plan, bodies = prepare(('下書きを保存した。', '翌日、予約が届いた。'), profile)
    joined = core._semantic_v4_join(plan, bodies)
    rel = dict(schema_version=core._semantic_v4_schema('RELATIONS'), nodes_sha256=core.semantic_map_hash(joined),
        qualification_review={}, edges=[], overview=dict(node_refs=refs, title=title))
    assert accepts(rel, core.semantic_node_local_v4_messages(p, 'RELATIONS', plan=plan, nodes=bodies)) is expected
    if expected:
        assert core.semantic_node_local_v4_relations(p, plan, bodies, rel)['overview'] == rel['overview']
    else:
        with pytest.raises(core.AnalysisSemanticMapError, match='relations_invalid'):
            core.semantic_node_local_v4_relations(p, plan, bodies, rel)


def test_combined_node_has_same_title_rule_and_recognizes_real_joint_title():
    p, plan, bodies = prepare(('窓を開けた。', '照明を点けた。'), core.SEMANTIC_MAP_OCCURRENCE_V16_PROFILE)
    combined(plan, bodies)
    messages = core.semantic_node_local_v4_messages(p, 'NODES', plan=plan)
    for title, good in [('照明を点けた。、', False), ('窓を開け、照明を点けた', True)]:
        bodies['nodes']['n1']['title'] = title
        raw = wire(p, plan, bodies)
        assert accepts(raw, messages) is good
        if good:
            assert core.admit_semantic_node_local_v4_nodes_response(p, plan, raw) == bodies
        else:
            with pytest.raises(core.AnalysisSemanticMapError, match='nodes_invalid'):
                core.admit_semantic_node_local_v4_nodes_response(p, plan, raw)


def test_shared_grounding_is_compared_before_removing_independent_titles():
    p, plan, _ = prepare(('同じ合図を聞いた。', '同じ合図を聞いた！'), core.SEMANTIC_MAP_OCCURRENCE_V16_PROFILE)
    units = [node['units'][0] for node in plan['nodes']]
    assert choices.one_sided_source_titles(json.loads(p.material_json), units, compare_end_marks=True) == []
    assert choices.source_title_key('第1,000回の「再演？」。') == '第1,000回の「再演？」'
