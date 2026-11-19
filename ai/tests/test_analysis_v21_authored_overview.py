"""A model can propose a complete heading, then select its exact text or the neutral title."""
from copy import deepcopy

import pytest

from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from test_analysis_node_local_native_profile import accepts
from test_analysis_v16_source_title_endings import prepare
from test_analysis_v18_overview_source_coverage import relation


PROFILE = core.SEMANTIC_MAP_OCCURRENCE_V21_PROFILE
NOTES = ('資料を照合して測量図を保管した。', '担当者から橋梁工事の再開を聞いた。')
NEUTRAL = '2件の記録を振り返って'


@pytest.mark.parametrize('proposal,eligible', [
    ('測量図の保管と担当者から聞いた橋梁工事の再開', True),
    ('担当者から聞いた橋梁工事の再開、その前に保管した測量図', True),
    ('資料を照合して測量図を保管した。担当者から橋梁工事の再開を聞いた。', True),
    ('測量図の保管を振り返った。橋梁工事については、担当者から再開を聞いている。', True),
    ('「測量図を保管した。どうする？」と橋梁工事について振り返る', True),
    ('"測量図を保管した。どうする？"と橋梁工事について振り返る', True),
    ('測量図を保管した。橋梁工事の再開を聞いた。', False),
    ('資料を照合して測量図を保管した。再・橋梁', False),
    ('あ' * 80, False),
    ('', False),
])
def test_private_draft_and_literal_publication(proposal, eligible):
    p, plan, nodes = prepare(NOTES, PROFILE)
    value, messages = relation(p, plan, nodes, ['n2', 'n1'], proposal)
    value['overview'] = dict(node_refs=['n2', 'n1'], title_proposal=proposal, title=NEUTRAL)
    assert accepts(value, messages)
    receipt = deepcopy(value)
    expected = dict(node_refs=['n2', 'n1'], title=NEUTRAL)
    assert core.semantic_node_local_v4_relations(p, plan, nodes, value)['overview'] == expected
    assert receipt == value
    value['overview']['title'] = proposal
    assert accepts(value, messages) is eligible
    if eligible:
        assert core.semantic_node_local_v4_relations(p, plan, nodes, value)['overview']['title'] == proposal
    else:
        with pytest.raises(core.AnalysisSemanticMapError):
            core.semantic_node_local_v4_relations(p, plan, nodes, value)


def test_another_supported_title_cannot_replace_the_proposal():
    p, plan, nodes = prepare(NOTES, PROFILE)
    v, msg = relation(p, plan, nodes, ['n1', 'n2'], '')
    v['overview'] = dict(node_refs=['n1', 'n2'], title_proposal='測量図の保管から橋梁工事の再開まで',
        title='橋梁工事と保管した測量図')
    assert not accepts(v, msg)
    with pytest.raises(core.AnalysisSemanticMapError):
        core.semantic_node_local_v4_relations(p, plan, nodes, v)


def test_single_record_still_uses_its_direct_title():
    p, plan, nodes = prepare((NOTES[0],), PROFILE)
    v, msg = relation(p, plan, nodes, ['n1'], '照合して保管した測量図')
    assert accepts(v, msg)
    assert core.semantic_node_local_v4_relations(p, plan, nodes, v)['overview'] == v['overview']
    v['overview'] = dict(node_refs=['n1'], title_proposal='測量図', title='測量図')
    assert not accepts(v, msg)
    with pytest.raises(core.AnalysisSemanticMapError):
        core.semantic_node_local_v4_relations(p, plan, nodes, v)
