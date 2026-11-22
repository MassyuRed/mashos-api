"""Public synthetic cases for already-selected future-action references."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import emlis_ai_grounded_human_reception as reception
from emlis_ai_grounded_observation_gate import evaluate_grounded_surface_body_inverse
from emlis_ai_grounded_observation_plan import source_proven_future_action_status
from test_emlis_cmee_body_inverse_protected import _final_stage1_artifacts


PLANNED_ACTIONS = (
    "明日は棚を拭く。",
    "来週は会場を見に行く。",
)


def artifacts(memo, action):
    plan, sentence, surface, resolver, selected = _final_stage1_artifacts(
        memo, memo_action=action,
    )
    hr = plan.response_plan.human_reception_plan
    targets = {n.nucleus_id: n for n in plan.nuclei}
    move = next(m for m in hr.moves if m.reception_act == "honor_concrete_effort")
    target = targets[move.target_nucleus_ids[0]]
    body = surface.text.split("Emlisから：", 1)[1].strip()
    return plan, sentence, surface, resolver, selected, hr, move, target, body


@pytest.mark.parametrize("memo", ["少し不安だ。", "まだよく分からない。少し不安だ。"])
@pytest.mark.parametrize("action", PLANNED_ACTIONS)
def test_selected_future_action_keeps_complete_content_and_future_status(memo, action):
    plan, sentence, surface, resolver, selected, hr, move, target, body = artifacts(memo, action)
    assert surface.recovery_stage == "full"
    assert source_proven_future_action_status(target)
    assert target.semantic_frame.modality == "intention"
    assert "operator:performed_action" not in target.semantic_frame.attribute_codes
    assert move.required and move.reference_mode == "short_anchor_if_ambiguous"
    assert move.target_nucleus_ids == (target.nucleus_id,) and not move.support_nucleus_ids
    assert target.source_fields == ("memo_action",)
    assert action.rstrip("。") in body
    assert "実際の行動" not in body and "その手間" not in body
    if move.move_role == "attention":
        assert "これからの行動に目が留まり、それを" not in body
        assert action.rstrip("。") + "こと" in body
    if memo:
        assert "不安" in body
    result = evaluate_grounded_surface_body_inverse(
        body=surface.text.encode(), plan=plan, sentence_plan=sentence,
        resolver=resolver, selected_subjective_input=selected,
    )
    assert result.passed, result.failure_codes


@pytest.mark.parametrize("action", [
    "明日は参加することにした。",
    "明日は結論を決めず、条件を見てから連絡することにした。",
])
def test_independent_attention_keeps_decision_content_without_promoting_execution(action):
    data = artifacts("少し不安だ。", action)
    plan, sentence, surface, resolver, selected, hr, move, target, body = data
    assert surface.recovery_stage == "full"
    assert source_proven_future_action_status(target)
    assert move.required and move.reference_mode == "short_anchor_if_ambiguous"
    assert action.rstrip("。") in body
    assert "不安" in body and "これからの行動" in body
    assert "実際の行動" not in body


@pytest.mark.parametrize("mutation", ["erase", "completed", "negation", "owner", "time"])
def test_inverse_rejects_lost_content_future_status_or_negation_without_reauthoring(mutation):
    action = "明日は結論を決めず、条件を見てから連絡することにした。"
    plan, sentence, surface, resolver, selected, hr, move, target, body = artifacts("少し不安だ。", action)
    if mutation == "erase":
        changed = body.replace(action.rstrip("。") + "というこれからの行動", "これからの行動")
    elif mutation == "completed":
        changed = body.replace("これからの行動", "実際の行動")
    elif mutation == "negation":
        changed = body.replace("決めず", "決めて")
    elif mutation == "owner":
        changed = body.replace("明日は", "別の人が明日は")
    else:
        changed = body.replace("明日は", "昨日は")
    assert changed != body
    tampered = surface.text.replace(body, changed, 1)
    with patch.object(reception, "realize_source_grounded_human_reception", side_effect=AssertionError("No reauthor")):
        result = evaluate_grounded_surface_body_inverse(
            body=tampered.encode(), plan=plan, sentence_plan=sentence,
            resolver=resolver, selected_subjective_input=selected,
        )
    assert not result.passed


@pytest.mark.parametrize("modality", ["uncertain", "wish", "fact"])
def test_concrete_intention_nominal_does_not_promote_other_modalities(modality):
    plan, sentence, surface, resolver, selected, hr, move, target, body = artifacts("少し不安だ。", PLANNED_ACTIONS[0])
    move = replace(move, move_role="felt_response")
    assert reception.source_grounded_future_action_nominal(move, {target.nucleus_id: target}, resolver)
    changed = replace(target, semantic_frame=replace(target.semantic_frame, modality=modality))
    assert reception.source_grounded_future_action_nominal(move, {changed.nucleus_id: changed}, resolver) == ""


@pytest.mark.parametrize("changes", [
    dict(actor="other_person"), dict(time_scope="past"),
    dict(attribute_codes=("operator:performed_action", "semantic_role:next_intention")),
])
def test_future_nominal_requires_original_owner_time_and_unperformed_status(changes):
    plan, sentence, surface, resolver, selected, hr, move, target, body = artifacts("少し不安だ。", PLANNED_ACTIONS[0])
    move = replace(move, move_role="felt_response")
    assert reception.source_grounded_future_action_nominal(move, {target.nucleus_id: target}, resolver)
    changed = replace(target, semantic_frame=replace(target.semantic_frame, **changes))
    assert reception.source_grounded_future_action_nominal(move, {changed.nucleus_id: changed}, resolver) == ""


@pytest.mark.parametrize("action", PLANNED_ACTIONS)
def test_single_future_reference_policy_is_not_promoted(action):
    plan, sentence, surface, resolver, selected, hr, move, target, body = artifacts("", action)
    assert hr.reference_mode == "anaphoric_first"
    assert move.reference_mode == "anaphoric_first"
    assert source_proven_future_action_status(target)
    assert "これからの行動" in body and "実際の行動" not in body
