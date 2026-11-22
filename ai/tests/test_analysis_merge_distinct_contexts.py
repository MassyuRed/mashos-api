"""Independent source passages cannot stand in for one another in MERGE v6."""
import json

import pytest

import analysis_merge_wire as wire
import analysis_plan_source_choices as choices
from cocolon_meaning_experience_engine.cores.analysis import semantic_admission as core
from test_analysis_merge_action_sources import MEMO, stage_with_action
from test_analysis_node_local_native_profile import accepts
from test_analysis_occurrence_v17_record_owners import packet


def selected_rule(stage, distinct=True):
    material = json.loads(stage.material_json)
    owners = choices.record_plan_owners(material, merge_anchors=True)
    return choices.merge_action_sources(material, owners, context_sources=True,
                                       distinct_context_sources=distinct)[1]


def test_reported_proposal_reply_and_availability_need_separate_witnesses():
    earlier = '委員は神社へ行こうと言った。'
    check = '整備の予定があり、開くかどうかは前日に判明する。'
    reply = '委員本人に連絡した。風が強ければ近場でもよいという返事だった。'
    followup = 'その後、最初に遠出を提案した委員が、次は同じ所へ行こうと言った。'
    action = '整備予定を確認した。委員本人の希望を聞いて、近場に決めた。'
    stage = stage_with_action(earlier + MEMO + check + reply + followup, action)
    rule = selected_rule(stage)
    assert rule.context_groups == ((reply,), (earlier,), (followup,), (check,))
    assert rule.minimum_roots[rule.required] == 5  # The two-sentence reply already fills its complete span.
    for missing in rule.context_groups:
        other = [q for group in rule.context_groups if group != missing for q in group]
        assert rule.missing([(1, q) for q in other] + [(2, action)])
    assert not rule.missing([(1, group[0]) for group in rule.context_groups] + [(2, action)])
    assert not selected_rule(stage, distinct=False).missing([(1, reply), (2, action)])


def test_correction_preserves_original_fact_and_only_its_unanswered_reason():
    reading = '私は、合図の意味は決められないと話した。'
    before = '途中で、係員が小さな合図を返したことが話題になった。'
    changed = '私はそこを見落としていたので、返事がなかったという説明を直した。'
    open_reason = 'ただ、その合図がどんな意図で送られたのかはまだ分からない。'
    other = 'ただ、その連絡がどんな意図で送られたのかはまだ分からない。'
    act = '先に自分の理解を話した。途中で事実の説明を修正した。'
    stage = stage_with_action(reading + MEMO + before + changed + open_reason, act, (reading,))
    rule = selected_rule(stage)
    assert rule.context_groups == ((reading,), (before + changed,), (open_reason,))
    old = core.semantic_node_local_v4_wire_messages(stage, wire_version=wire.COMPARISON_VERSION)
    current = core.semantic_node_local_v4_wire_messages(stage)
    assert wire.legacy_messages(current) == wire.legacy_messages(old)
    flags = dict(merge_anchors=True, merge_action_sources=True, context_sources=True)
    once = packet(stage, [[[(2, act), (1, reading)]]])
    assert accepts(wire.response_codec(old).encode(once), old)
    assert not accepts(wire.response_codec(current).encode(once), current)
    assert core.admit_semantic_node_local_v4_plan_response(stage, once, **flags)
    with pytest.raises(core.AnalysisSemanticMapError, match='analysis_semantic_plan_action_source_missing'):
        core.admit_semantic_node_local_v4_plan_response(stage, once, **flags, distinct_context_sources=True)
    all_sources = packet(stage, [[[(2, act), (1, reading)], [(1, before + changed), (1, open_reason)]]])
    assert accepts(wire.response_codec(current).encode(all_sources), current)
    assert core.admit_semantic_node_local_v4_plan_response(stage, all_sources, **flags, distinct_context_sources=True)
    ends_with_correction = stage_with_action(reading + MEMO + before + changed, act, (reading,))
    assert selected_rule(ends_with_correction).context_groups == ((reading,), (before + changed,))
    unrelated = stage_with_action(reading + MEMO + before + changed + other, act, (reading,))
    assert selected_rule(unrelated).context_groups == ((reading,), (before + changed,))


def test_a_response_and_the_reason_to_keep_an_explanation_come_from_the_prior_leaf():
    contact = '準備を終えてから車掌へ短い報告を送り、駅名を確認できるか尋ねた。'
    reply = '昼過ぎに駅名が届き、候補の表を作り直した。'
    different = '正午に係名が届き、候補の表を作り直した。'
    memo = contact + MEMO + reply + different
    act = '駅名について車掌へ報告した。返答後に表を書き直した。'
    assert selected_rule(stage_with_action(memo, act, (reply, different))).context_groups == ((contact,), (reply,))
    assert selected_rule(stage_with_action(memo, act)).context_groups == ((contact,),)
    words = '省かれたのは、音をどう集めたかという記述だった。完成時には分からないから、私は残したかった。'
    act = '発表で残したい手順の記述を伝えた。'
    assert selected_rule(stage_with_action(MEMO + words, act, (words,))).context_groups == ((words,),)
    assert selected_rule(stage_with_action(MEMO + words, act)).context_groups == ((),)
