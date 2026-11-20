"""Distinct, literal source passages for both sides of a qualified reply in history MERGE."""
import json

import pytest

import analysis_plan_source_choices as choices
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from test_analysis_merge_action_sources import MEMO, stage_with_action
from test_analysis_occurrence_v17_record_owners import packet


WISH = '監督は僕に本番の先頭に立ってほしいと言った。'
REPLY = '僕は、出番を全部引き受けたいわけではないと答えた。'
LIMIT = '演奏を希望することと、公演を全部任されることは別にしたかった。'
STANCE = '一度の参加が次回も引き受けるという了承になるのは困る。'
REFERENCE = '監督がそのように解釈したかはまだ分からない。'
ACTION = '監督と演目を話し、希望と参加判断を分けたいと伝えた。'


def rule(memo, speaker=True):
    stage = stage_with_action(memo, ACTION)
    material = json.loads(stage.material_json)
    owners = choices.record_plan_owners(material, merge_anchors=True)
    result = choices.merge_action_sources(material, owners, context_sources=True,
                                         distinct_context_sources=True, speaker_context_sources=speaker)
    return stage, result[1]


def test_both_speakers_and_the_referent_are_bound_to_their_own_quotes():
    memo = WISH + REPLY + LIMIT + '\n\n' + MEMO + STANCE + REFERENCE
    stage, selected = rule(memo)
    assert selected.context_groups == ((WISH,), (REPLY + LIMIT,), (STANCE + REFERENCE,))
    flags = dict(merge_anchors=True, merge_action_sources=True, context_sources=True, distinct_context_sources=True)
    old = packet(stage, [[[(2,ACTION), (1,WISH), (1,REFERENCE)]]])
    assert core.admit_semantic_node_local_v4_plan_response(stage, old, **flags)
    with pytest.raises(core.AnalysisSemanticMapError, match='action_source_missing'):
        core.admit_semantic_node_local_v4_plan_response(stage, old, **flags, speaker_context_sources=True)
    complete = packet(stage, [[[(2,ACTION), (1,WISH)], [(1,REPLY + LIMIT),(1,STANCE + REFERENCE)]]])
    admitted = core.admit_semantic_node_local_v4_plan_response(stage, complete, **flags, speaker_context_sources=True)
    assert choices.ordered_record_sections(json.loads(stage.material_json)['fields'],
                                           [dict(u,source_mode='RECORDED') for u in admitted['nodes'][0]['units']]) == [
        ('memo',[WISH,REPLY,LIMIT,STANCE,REFERENCE]), ('memo_action',[ACTION])]
    assert rule(memo, speaker=False)[1].context_groups == ((WISH,),)


@pytest.mark.parametrize('interruption', ['\n\n','演出家は先に撮影したいと伝えた。','演出家は別の順で歌いたいと頼んだ。'])
def test_a_new_paragraph_or_another_turn_does_not_supply_the_narrators_reply(interruption):
    _, selected = rule(WISH + interruption + REPLY + LIMIT + MEMO + STANCE + REFERENCE)
    assert selected.context_groups == ((WISH,),)


@pytest.mark.parametrize('antecedent', ['助手はすべての公演に参加したいと答えた。','助手は延期を希望していた。'])
def test_someone_elses_position_remains_theirs(antecedent):
    stage, selected = rule(WISH + REPLY + LIMIT + '\n\n' + MEMO + antecedent + REFERENCE)
    assert selected.context_groups == ((WISH,), (REPLY + LIMIT,))
    assert selected.coverage(1, antecedent) == 0
    original = packet(stage, [[[(2,ACTION), (1,WISH)], [(1,REPLY + LIMIT), (1,antecedent + REFERENCE)]]])
    admitted = core.admit_semantic_node_local_v4_plan_response(
        stage, original, merge_anchors=True, merge_action_sources=True, context_sources=True,
        distinct_context_sources=True, speaker_context_sources=True)
    sections = choices.ordered_record_sections(json.loads(stage.material_json)['fields'],
                                               [dict(u,source_mode='RECORDED') for u in admitted['nodes'][0]['units']])
    assert sections == [('memo',[WISH, REPLY, LIMIT, antecedent, REFERENCE]), ('memo_action',[ACTION])]


def test_does_not_attach_an_interpretation_across_paragraphs():
    _, selected = rule(WISH + REPLY + LIMIT + '\n' + MEMO + STANCE + '\n\n' + REFERENCE)
    assert selected.context_groups == ((WISH,), (REPLY + LIMIT,))

def test_a_different_speakers_adjacent_qualification_is_not_the_narrators_reply():
    other = '助手は歌を希望することと全公演に出ることは別だと伝えた。'
    _, selected = rule(MEMO + WISH + REPLY + other)
    assert selected.context_groups == ((WISH,), (REPLY,))
