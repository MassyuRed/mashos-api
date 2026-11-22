"""Keep qualified, first-person thoughts intact when interpreting a paired action."""
from copy import deepcopy

import pytest

from analysis_plan_source_choices import paired_node_meanings
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from test_analysis_node_local_native_profile import accepts
from test_analysis_occurrence_v11_display import map_stages
from test_analysis_occurrence_v17_record_owners import packet, verify
from test_analysis_occurrence_v18_compact_originals import prepared
from test_analysis_v13_separate_record_titles import wire


THOUGHT = 'どちらの経路を使うかは保留し、地図だけ手元に残した。'
ACTION = '二つの経路を記録した。'
MISREADING = '二つの経路を区別しなかった。'


@pytest.mark.parametrize('profile', [core.SEMANTIC_MAP_OCCURRENCE_V19_PROFILE,
                                     core.SEMANTIC_MAP_OCCURRENCE_V20_PROFILE])
def test_interpretation_matches_qualified_thought_in_decoder_and_admission(profile):
    p = prepared([(ACTION, THOUGHT)], profile)
    # The displayed text is bound to the complete selected source sentence.
    plan = verify(p, packet(p, [[[(2, ACTION), (1, THOUGHT)]]]), True)
    _, _, response = map_stages(ACTION)
    node = response['nodes']['n1']
    node['title'] = ACTION
    roots = plan['nodes'][0]['units'][0]['evidence']
    node['units']['u1']['fact_parts'] = {
        core._semantic_fact_part_key(roots, i): root['quote'] for i, root in enumerate(roots)}
    node['units']['u1']['unknowns'] = []
    messages = core.semantic_node_local_v4_messages(p, 'NODES', plan=plan)
    for meaning in (MISREADING, THOUGHT):
        node['meaning'] = meaning
        raw = wire(p, plan, response)
        allowed = profile == core.SEMANTIC_MAP_OCCURRENCE_V19_PROFILE or meaning == THOUGHT
        assert accepts(raw, messages) is allowed
        if allowed:
            assert core.admit_semantic_node_local_v4_nodes_response(p, plan, raw)['nodes']['n1']['meaning'] == meaning
        else:
            with pytest.raises(core.AnalysisSemanticMapError, match='meaning_not_in_source'):
                core.admit_semantic_node_local_v4_nodes_response(p, plan, raw)


def test_meanings_stay_with_the_selected_record_sentence_and_original_fields():
    later = '先の道を選び、出発した。'
    fields = [dict(field=1, field_path='memo', source_role='ORIGINAL_INPUT', record=1, text=THOUGHT+later),
              dict(field=2, field_path='memo_action', source_role='ORIGINAL_INPUT', record=1, text=ACTION)]
    units = [dict(evidence=[dict(field=1, quote=THOUGHT), dict(field=2, quote=ACTION)])]
    sentences = {1: {later, THOUGHT}, 2: {ACTION}}
    assert paired_node_meanings(fields, units, sentences) == [THOUGHT]
    assert paired_node_meanings(fields, units, {}) == []
    for updated in (dict(record=2), dict(source_role='SUPPLEMENTAL_ANSWER')):
        other = deepcopy(fields)
        other[1].update(updated)
        assert paired_node_meanings(other, units, sentences) == []
    correction = dict(field=3, record=None, source_role='USER_ANALYSIS_MAP_CORRECTION')
    assert paired_node_meanings([*fields, correction], units, sentences) == []
