"""Preserve a person's reported response and the writer's own interpretation at MERGE."""
import json

import pytest

import analysis_plan_source_choices as choices
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from test_analysis_merge_action_sources import MEMO, stage_with_action
from test_analysis_occurrence_v17_record_owners import packet


ACTION = '自分の解釈を説明した。'
SELF = '私は、途切れた旋律は呼びかけに聞こえると説明した。'
WORDS = '講師は、切れ目を聴く人によって拍の取り方が変わると述べた。'
RECEPTION = '私はその説明を聞いて考え直したが、講師が私だけに向けたのかは分からない。'


def rules(stage, new):
    material = json.loads(stage.material_json)
    return choices.merge_action_sources(material, choices.record_plan_owners(material, merge_anchors=True),
        context_sources=True, distinct_context_sources=True, speaker_context_sources=True,
        attributed_context_sources=new)[1]


def test_preserves_both_named_accounts_and_the_uncertain_scope_in_source_order():
    pair = WORDS + RECEPTION
    stage = stage_with_action(MEMO + SELF + '\n\n' + pair, ACTION, (SELF, pair))
    assert rules(stage, False).context_groups == ((SELF,),)
    assert rules(stage, True).context_groups == ((SELF,), (pair,))
    flags = dict(merge_anchors=True, merge_action_sources=True, context_sources=True,
                 distinct_context_sources=True, speaker_context_sources=True)
    for incomplete in (WORDS, RECEPTION, SELF):
        units = [[(2, ACTION), (1, SELF)]]
        if incomplete != SELF:
            units.append([(1, incomplete)])
        raw = packet(stage, [units])
        assert core.admit_semantic_node_local_v4_plan_response(stage, raw, **flags)
        with pytest.raises(core.AnalysisSemanticMapError, match='action_source_missing'):
            core.admit_semantic_node_local_v4_plan_response(stage, raw, **flags, attributed_context_sources=True)
    raw = packet(stage, [[[(2, ACTION), (1, SELF)], [(1, pair)]]])
    plan = core.admit_semantic_node_local_v4_plan_response(stage, raw, **flags, attributed_context_sources=True)
    units = [dict(unit, source_mode='RECORDED') for unit in plan['nodes'][0]['units']]
    assert choices.ordered_record_sections(json.loads(stage.material_json)['fields'], units) == [
        ('memo', [SELF, WORDS, RECEPTION]), ('memo_action', [ACTION])]


@pytest.mark.parametrize('words,reply,join', [
    (WORDS, RECEPTION.replace('講師が', '友人が'), ''),
    (WORDS, RECEPTION.replace('私は', '通訳は'), ''),
    (WORDS, RECEPTION.replace('私はその説明を聞いて', '私は予定表を見て'), ''),
    (WORDS, RECEPTION.replace('分からない。', '確かめた。'), ''),
    (WORDS, RECEPTION, '\n\n'),
    (WORDS, RECEPTION, '作曲家は別の合図も欲しいと答えた。'),
    (WORDS.replace('切れ目を', 'もし切れ目を'), RECEPTION, ''),
    ('講師は、録音係が明日聴くと言ったと話した。', RECEPTION, ''),
])
def test_another_actor_unbound_reply_or_hypothetical_is_not_forced(words, reply, join):
    quote = words + join + reply
    stage = stage_with_action(MEMO + SELF + quote, ACTION, (SELF, quote))
    assert rules(stage, True).context_groups == ((SELF,),)


def test_requires_both_leaf_witnesses_and_a_unique_exchange():
    pair = WORDS + RECEPTION
    for leaves in ((SELF,), (SELF, WORDS, RECEPTION), (pair,)):
        stage = stage_with_action(MEMO + SELF + pair, ACTION, leaves)
        assert (pair,) not in rules(stage, True).context_groups
    second = pair.replace('講師', '奏者')
    stage = stage_with_action(MEMO + SELF + pair + second, ACTION, (SELF, pair, second))
    assert rules(stage, True).context_groups == ((SELF,),)


def test_another_participants_wish_cannot_replace_the_writers_own_words():
    from test_analysis_merge_speaker_context import WISH
    action = '監督と希望を話し、自分の解釈を説明した。'
    pair = WORDS + RECEPTION
    stage = stage_with_action(MEMO + WISH + '\n\n' + SELF + '\n\n' + pair, action, (SELF, pair))
    old, new = rules(stage, False), rules(stage, True)
    assert old.context_groups == ((WISH, SELF),)
    assert new.context_groups == ((WISH, SELF), (SELF,), (pair,))
    roots = [(2, action), (1, WISH), (1, pair)]
    assert not old.missing(roots)
    assert new.missing(roots)
    assert not new.missing([*roots,(1, SELF)])


def test_eight_slots_preserve_prior_narrator_reply_and_its_explicit_referent():
    from test_analysis_merge_speaker_context import WISH, REPLY, LIMIT, STANCE, REFERENCE
    before = '途中で、係員が小さな合図を返したことが話題になった。'
    corrected = '私はそこを見落としていたので、返事がなかったという説明を直した。'
    hold = 'ただ、その合図がどんな意図で送られたのかはまだ分からない。'
    contact = '準備を終えてから車掌へ短い報告を送り、駅名を確認できるか尋ねた。'
    received = '昼過ぎに駅名が届き、候補の表を作り直した。'
    memo = '\n\n'.join((WISH+REPLY+LIMIT, STANCE+REFERENCE, SELF, WORDS+RECEPTION,
                        before+corrected+hold, contact, received))
    action = '監督と希望を話し、自分の解釈を説明した。駅名について車掌へ報告した。返答後に表を書き直した。途中で事実の説明を修正した。'
    stage = stage_with_action(memo, action, (SELF, WORDS+RECEPTION, received))
    old, new = rules(stage, False), rules(stage, True)
    assert old.minimum_roots[old.required] == 8
    assert old.context_groups[-2:] == ((REPLY+LIMIT,), (STANCE+REFERENCE,))
    assert new.context_groups == old.context_groups
    assert new.minimum_roots[new.required] == 8
