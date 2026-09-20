"""Current-path checks for responsibilities hidden by retained old assertions.

Inputs come from the existing public tests. Old expected text is not replaced;
each mutation here must change the actual body before rejection is credited.
"""
from dataclasses import replace
from functools import lru_cache
from types import SimpleNamespace
import pytest
from cocolon_meaning_experience_engine import MeaningExperienceEngine
from test_cmee_emlis_q1_thread import answered
from test_cmee_emlis_q3_thread import begin, advance
from test_cmee_emlis_received_discourse import actual, inverse
from test_cmee_emlis_adjacent_action_context import SOURCES, ACTIONS


@lru_cache(maxsize=None)
def independent_context(memo, action):
    return actual(request=begin(memo, action))


@pytest.mark.parametrize("memo", SOURCES)
@pytest.mark.parametrize("action", ACTIONS)
def test_original_contextual_inputs_keep_two_independent_sources(memo, action):
    context = independent_context(memo, action)
    result, plan, _, _, selected = context
    follow = result.artifact.reception
    assert memo.rstrip("。") in follow and action.rstrip("。") in follow
    assert "ことを背景に、" not in follow
    moves = plan.response_plan.human_reception_plan.moves
    assert len(moves) == 2 and all(m.required for m in moves)
    assert not any(m.support_nucleus_ids for m in moves)
    refs = [ref for d in selected.decisions for ref in d.selected_contribution_refs]
    assert refs and len(refs) == len(set(refs))
    assert inverse(context, follow, without_author=True).passed


@pytest.mark.parametrize("memo", SOURCES)
@pytest.mark.parametrize("action", ACTIONS)
@pytest.mark.parametrize("axis", ["drop_memo", "drop_action", "actor", "time", "quote", "background"])
def test_current_independent_sources_reject_real_mutations(memo, action, axis):
    context = independent_context(memo, action)
    follow = context[0].artifact.reception
    anchor = action.rstrip("。")
    if axis == "drop_memo":
        changed = follow.split("。", 1)[1]
    elif axis == "drop_action":
        changed = follow.split("。", 1)[0] + "。"
    elif axis == "actor":
        changed = follow.replace(anchor, "友人が" + anchor)
    elif axis == "time":
        changed = follow.replace(anchor, "来月は" + anchor)
    elif axis == "quote":
        changed = follow.replace(memo.rstrip("。"), "「" + memo.rstrip("。") + "」")
    else:
        changed = anchor + "ことを背景に、" + follow
    assert changed != follow
    assert not inverse(context, changed, without_author=True).passed


@lru_cache(maxsize=None)
def recovered_context(name):
    base = "誘われたのに、悲しかった。頼まれたのに、寂しかった。準備を忘れた自分が情けない。"
    if name == "initial":
        request = begin("褒められたけど、嬉しくなかった。誘われたのに、悲しかった。")
    elif name == "past_positive":
        request = advance(advance(begin(), "その時は重かった。"), "その時は嬉しかった。")
    elif name == "withdraw_event":
        request = advance(advance(begin(), "今は嬉しい。"), '「褒められた」は誤りです。')
    elif name == "feeling_reason":
        request = begin("私は少し怖い。その理由はまだよく分からない。", "お茶を飲んだ。")
    else:
        request = begin(base, "机を拭いた。")
        correction = ('「準備を忘れた自分が情けない」は誤りです。' if name == "withdraw_appraisal"
                      else '「準備を忘れた自分が情けない」ではなく「' +
                      ("不安です" if name == "replace_present" else "不安でした") + '」。')
        request = advance(request, correction)
    original = request.current_input_bundle
    result = actual(request=request)
    assert request.current_input_bundle == original
    assert inverse(result, result[0].artifact.reception, without_author=True).passed
    return result


@pytest.mark.parametrize("name,old,new", [
    ("feeling_reason", "あなたは少し怖くて", "「あなたは少し怖くて」"),
    ("initial", "嬉しさにはつながらず、誘われたのに、悲しさを感じた", "悲しさにはつながらず、誘われたのに、嬉しさを感じた"),
    ("initial", "誘われたのに、悲しさを感じた", "褒められたのに、嬉しさを感じなかった"),
    ("initial", "褒められたことは、嬉しさにはつながらず", "「褒められたことは、嬉しさにはつながらず」"),
    ("past_positive", "その時は嬉しかった", "回答した時点では嬉しかった"),
    ("past_positive", "その時は嬉しかった", "嬉しかった"),
    ("past_positive", "その時は嬉しかった", "その時は嬉しくなかった"),
    ("past_positive", "その時は嬉しかった", "「その時は嬉しかった」"),
    ("withdraw_event", "誘われたのに、悲しさを感じ、", ""),
    ("withdraw_event", "悲しさを感じ", "嬉しさを感じ"),
])
def test_previous_noop_mutations_now_change_the_actual_clause(name, old, new):
    context = recovered_context(name)
    follow = context[0].artifact.reception
    assert old in follow
    changed = follow.replace(old, new)
    assert changed != follow
    assert not inverse(context, changed, without_author=True).passed


@pytest.mark.parametrize("name", ["withdraw_appraisal", "replace_present", "replace_past"])
@pytest.mark.parametrize("old,new", [
    ("誘われたのに、悲しさを感じ、", ""),
    ("頼まれたのに、寂しさを感じた", "寂しさを感じた"),
    ("誘われたのに", "友人が誘われたのに"),
    ("悲しさを感じ、", "今は悲しさを感じ、"),
    ("寂しさを感じた", "寂しさを感じなかった"),
])
def test_surviving_pairs_are_checked_after_withdrawal_or_replacement(name, old, new):
    context = recovered_context(name)
    follow = context[0].artifact.reception
    assert old in follow
    changed = follow.replace(old, new)
    assert changed != follow
    assert not inverse(context, changed, without_author=True).passed


@pytest.mark.parametrize("duplicate", [False, True])
def test_extra_sensation_is_actually_inserted_before_semantic_check(duplicate):
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning, build_updated_grounded_plan
    from cocolon_meaning_experience_engine.emlis_thread_surface import realize_emlis_thread_body
    from emlis_ai_grounded_observation_gate import _semantic_subcheck_reasons
    import emlis_ai_grounded_sentence_surface as surface
    prepared = prepare_emlis_meaning(answered("その時は重かった。"))
    plan = build_updated_grounded_plan(prepared)
    original = realize_emlis_thread_body(prepared).artifact.text
    changed = original.replace("重かった", "重かった重さ")
    assert changed != original
    reception = plan.response_plan.human_reception_plan
    altered = replace(plan, response_plan=replace(plan.response_plan, human_reception_plan=
        replace(reception, moves=reception.moves * 2) if duplicate else None))
    reasons, _, _ = _semantic_subcheck_reasons(plan=altered,
        sentence_plan=surface.build_grounded_sentence_plan(plan, prepared.thread.resolver(), recovery_stage="full"),
        surface_result=SimpleNamespace(text=changed, lines=()), resolver=prepared.thread.resolver())
    assert "ungrounded_sensation_family_added" in reasons
