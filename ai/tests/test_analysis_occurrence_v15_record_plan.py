"""Normal MAP reads each record before grouping. History keeps its own directions."""
import json

from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from test_analysis_node_local_native_profile import accepts
from test_analysis_occurrence_v13_plan_choices import view
from test_analysis_occurrence_v14_visible_closers import stages

PROFILES = (core.SEMANTIC_MAP_OCCURRENCE_V14_PROFILE, core.SEMANTIC_MAP_OCCURRENCE_V15_PROFILE)


def test_distinct_trials_and_later_corroboration_remain_bound_to_the_same_record_fields():
    notes = ('私は外で八分測った。', '私は屋内で三分測った。', '外で八分測ったときの写真が後で届いた。')
    rows = []
    for profile in PROFILES:
        prepared, _, _ = stages(*notes, profile=profile)
        material, _, table, _ = view(prepared)
        addresses = {quote: (field, cue) for (field, cue), quote in table.items()}
        def evidence(quote):
            field, cue = addresses[quote]
            return dict(quote=cue, field=field)
        raw = dict(schema_version=core._semantic_v4_schema('PLAN'),
                   source_choices_sha256=material['source_choices_sha256'],
                   nodes=[dict(node_id='n1', units=[dict(evidence=[evidence(notes[0]), evidence(notes[2])]),
                                                     dict(evidence=[evidence(notes[1])])])])
        assert accepts(raw, prepared.messages())
        admitted = core.admit_semantic_node_local_v4_plan_response(prepared, raw)
        rows.append((material, table, admitted, prepared.messages()[0]['content']))
    old, new = rows
    assert old[0]['fields'] == new[0]['fields'] and old[0]['records'] == new[0]['records']
    assert old[1:3] == new[1:3]
    assert core._SEMANTIC_RECORD_FIRST_PLAN not in old[3]
    assert new[3].count(core._SEMANTIC_RECORD_FIRST_PLAN) == 1
    assert '全記録を読み、1〜12項目のnode_id・unitsを選びます。' not in new[3]


def test_leaf_body_and_relations_keep_the_original_directions():
    systems = []
    for profile in PROFILES:
        parent, plan, bodies = stages('温度計を戸外に置いた。', '翌日、計器はまだ取り込んでいない。', profile=profile)
        leaf = core.prepare_semantic_leaf(parent, (parent.frozen.members[0].saved_record_ref,))
        leaf_system = leaf.messages()[0]['content']
        assert '今はLEAFです。' in leaf_system and core._SEMANTIC_RECORD_FIRST_PLAN not in leaf_system
        nodes = core.semantic_node_local_v4_messages(parent, 'NODES', plan=plan)
        relations = core.semantic_node_local_v4_messages(parent, 'RELATIONS', plan=plan, nodes=bodies)
        assert json.loads(nodes[1]['content'])['author_profile'] == profile
        systems.append([leaf_system.split('例入力=')[0], nodes[0]['content'], relations[0]['content']])
    assert systems[0] == systems[1]
