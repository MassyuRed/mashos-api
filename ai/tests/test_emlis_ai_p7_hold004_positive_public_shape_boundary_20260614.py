# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

import pytest

from emlis_ai_input_material_bundle import (
    MATERIAL_QUALITY_ELIGIBLE,
    MATERIAL_QUALITY_SAFETY_TRIAGE_REQUIRED,
    VISIBLE_MATERIAL_SLOT_ACTION,
    VISIBLE_MATERIAL_SLOT_CHANGE,
    VISIBLE_MATERIAL_SLOT_EMOTION_DIRECTION,
    VISIBLE_MATERIAL_SLOT_EVENT,
    VISIBLE_MATERIAL_SLOT_RELATIONSHIP,
    VISIBLE_MATERIAL_SLOT_TARGET,
    VISIBLE_MATERIAL_SLOT_TIME,
    assert_emlis_input_material_bundle_meta_contract,
    build_emlis_input_material_bundle,
)
from emlis_ai_p7_hold004_positive_public_shape_boundary import (
    P7_HOLD004_POSITIVE_PUBLIC_SHAPE_BOUNDARY_ID,
    P7_HOLD004_POSITIVE_PUBLIC_SHAPE_CLASSIFICATION,
    P7_HOLD004_POSITIVE_PUBLIC_SHAPE_REPAIRED_STATUS,
    P7_HOLD004_POSITIVE_PUBLIC_SHAPE_SCHEMA_VERSION,
    assert_p7_hold004_positive_public_shape_boundary_contract,
    build_p7_hold004_positive_public_shape_boundary_classification,
    build_p7_hold004_positive_public_shape_boundary_repaired_material,
)
from emlis_ai_p7_hold_matrix import (
    assert_p7_backend_suite_split_matrix_contract,
    assert_p7_r10_hold_matrix_contract,
    build_p7_backend_suite_split_matrix,
    build_p7_r10_hold_matrix,
)
from emlis_ai_p7_release_handoff import (
    P7_HOLD004_POSITIVE_PUBLIC_SHAPE_IMPLEMENTATION_RESULT_DOC_PATH,
    P7_HOLD004_POSITIVE_PUBLIC_SHAPE_IMPLEMENTATION_RESULT_DOC_REF,
    assert_p7_release_decision_handoff_contract,
    build_p7_release_decision_handoff,
)
from emlis_ai_p7_validation_matrix import (
    assert_p7_validation_regression_matrix_contract,
    build_p7_validation_regression_matrix,
)
from emlis_ai_safety_triage import (
    TRIAGE_SAFE_OBSERVATION,
    TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER,
    TRIAGE_SAFETY_BLOCKED_EMERGENCY,
    TRIAGE_SAFETY_SUPPORT_REQUIRED,
    assert_emlis_safety_triage_meta,
    build_emlis_safety_triage_decision,
    classify_emlis_safety_triage_text,
)
from fixtures.emlis_ai_two_stage_reception_cases import two_stage_reception_case_by_id


def _assert_body_free_safety_meta(meta: dict) -> None:
    assert meta["raw_user_text_included"] is False
    assert meta["comment_text_generated"] is False
    assert "comment_text" not in meta
    assert "candidate_body" not in meta
    assert "raw_input" not in meta
    assert_emlis_safety_triage_meta(meta)


def test_r0_current_positive_public_red_is_classified_body_free_and_release_closed() -> None:
    material = build_p7_hold004_positive_public_shape_boundary_classification()

    assert material["schema_version"] == P7_HOLD004_POSITIVE_PUBLIC_SHAPE_SCHEMA_VERSION
    assert material["boundary_id"] == P7_HOLD004_POSITIVE_PUBLIC_SHAPE_BOUNDARY_ID
    assert material["hold_id"] == "P7-HOLD-004"
    assert material["status"] == "CLASSIFIED_UNRESOLVED"
    assert material["classification"] == P7_HOLD004_POSITIVE_PUBLIC_SHAPE_CLASSIFICATION
    assert material["target_path_id"] == "emotion_submit_public_product_visible_fixture_suite"
    assert material["target_fixture_family"] == "positive_change_after_work_streaming"
    assert material["observed_before_repair"] == {
        "public_reached": True,
        "labelled_two_stage_reached": False,
        "safety_triage_kind": "self_denial_safe_state_answer",
        "response_kind": "self_denial_safe_state_answer",
        "candidate_source_kind": "self_denial_safe_state_answer",
        "surface_requirement_family": "safety_blocked",
        "two_stage_required": False,
    }
    assert material["expected_after_repair"] == {
        "public_reached": True,
        "labelled_two_stage_reached": True,
        "safety_triage_kind": "safe_observation",
        "response_kind": "normal_observation",
        "self_denial_safe_state_answer_candidate_used": False,
    }
    assert material["runtime_repair_applied"] is False
    assert material["target_green_confirmed"] is False
    assert material["full_backend_suite_green_confirmed"] is False
    assert material["hold004_close_allowed"] is False
    assert material["p7_complete_claim_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert material["body_free"] is True
    assert material["body_free_markers"]["raw_input_included"] is False
    assert material["body_free_markers"]["comment_text_body_included"] is False
    assert material["body_free_markers"]["candidate_body_included"] is False
    assert material["body_free_markers"]["surface_body_included"] is False
    assert material["body_free_markers"]["reviewer_free_text_included"] is False
    assert material["body_free_markers"]["terminal_output_included"] is False
    assert_p7_hold004_positive_public_shape_boundary_contract(material)


def test_r0_positive_public_shape_boundary_contract_rejects_body_payload_and_closure_claim() -> None:
    material = build_p7_hold004_positive_public_shape_boundary_classification()

    closure = dict(material)
    closure["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_positive_public_shape_boundary_contract(closure)

    payload = dict(material)
    payload["comment_text"] = "forbidden public body"
    with pytest.raises(ValueError):
        assert_p7_hold004_positive_public_shape_boundary_contract(payload)


# R1 target tests were added before the R2 runtime repair.  After R2 they must
# stay green without case-specific routing, fixed commentText, or public key changes.


def test_r1_positive_change_expression_difficulty_fixture_should_be_safe_observation_body_free() -> None:
    case = two_stage_reception_case_by_id("positive_change_after_work_streaming")
    decision = build_emlis_safety_triage_decision(current_input=case["current_input"])
    meta = decision.as_meta()

    assert meta["safety_triage_kind"] == TRIAGE_SAFE_OBSERVATION
    assert meta["response_kind"] == "normal_observation"
    assert meta["normal_observation_allowed"] is True
    assert meta["safe_state_answer_allowed"] is False
    assert meta["public_input_feedback_allowed"] is True
    assert meta["public_emlis_observation_allowed"] is True
    _assert_body_free_safety_meta(meta)


def test_r1_expression_difficulty_without_identity_denial_should_not_open_self_denial_candidate() -> None:
    probes = (
        "自分の気持ちをうまく表現できない。",
        "自分の中の変化をまだ整理できない。",
        "私はまだ上手く言葉にできない。",
    )

    for text in probes:
        decision = classify_emlis_safety_triage_text(text)
        meta = decision.as_meta()
        assert meta["safety_triage_kind"] == TRIAGE_SAFE_OBSERVATION
        assert meta["response_kind"] == "normal_observation"
        assert meta["safe_state_answer_allowed"] is False
        _assert_body_free_safety_meta(meta)


def test_r2_inability_without_identity_denial_should_remain_safe_observation() -> None:
    probes = (
        "疲れ切って何もできないくらい消耗している。",
        "今日は悲しみが強くて、何もできない。",
    )

    for text in probes:
        decision = classify_emlis_safety_triage_text(text)
        meta = decision.as_meta()
        assert meta["safety_triage_kind"] == TRIAGE_SAFE_OBSERVATION
        assert meta["response_kind"] == "normal_observation"
        assert meta["safe_state_answer_allowed"] is False
        _assert_body_free_safety_meta(meta)


@pytest.mark.parametrize(
    "text",
    (
        "自分には何もできないし、価値がないと思ってしまう。",
        "私はできない人間だと思う。",
        "私は私が嫌いで、全部自分が悪いと思ってしまう。",
    ),
)
def test_r1_true_self_denial_identity_inability_stays_safe_state_answer(text: str) -> None:
    decision = classify_emlis_safety_triage_text(text)
    meta = decision.as_meta()

    assert meta["safety_triage_kind"] == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER
    assert meta["response_kind"] == "self_denial_safe_state_answer"
    assert meta["must_not_accept_identity_claim_as_fact"] is True
    assert meta["safe_state_answer_allowed"] is True
    assert meta["public_input_feedback_allowed"] is True
    assert meta["requires_separate_safety_surface"] is False
    _assert_body_free_safety_meta(meta)


def test_r1_emergency_and_support_required_boundaries_stay_closed() -> None:
    emergency = classify_emlis_safety_triage_text("もう消えたい。今日で終わりにしたい。")
    emergency_meta = emergency.as_meta()
    assert emergency_meta["safety_triage_kind"] == TRIAGE_SAFETY_BLOCKED_EMERGENCY
    assert emergency_meta["response_kind"] == "safety_blocked_emergency"
    assert emergency_meta["public_input_feedback_allowed"] is False
    assert emergency_meta["public_emlis_observation_allowed"] is False
    assert emergency_meta["requires_separate_safety_surface"] is True
    _assert_body_free_safety_meta(emergency_meta)

    support = classify_emlis_safety_triage_text("安全が保てない。助けが必要。")
    support_meta = support.as_meta()
    assert support_meta["safety_triage_kind"] == TRIAGE_SAFETY_SUPPORT_REQUIRED
    assert support_meta["response_kind"] == "safety_support_required"
    assert support_meta["public_input_feedback_allowed"] is False
    assert support_meta["public_emlis_observation_allowed"] is False
    assert support_meta["requires_separate_safety_surface"] is True
    _assert_body_free_safety_meta(support_meta)


def test_r3_positive_expression_difficulty_material_route_stays_eligible_body_free() -> None:
    case = two_stage_reception_case_by_id("positive_change_after_work_streaming")
    decision = build_emlis_safety_triage_decision(current_input=case["current_input"])
    triage_meta = decision.as_meta()

    assert triage_meta["safety_triage_kind"] == TRIAGE_SAFE_OBSERVATION
    _assert_body_free_safety_meta(triage_meta)

    bundle = build_emlis_input_material_bundle(
        case["current_input"],
        safety_triage_decision=decision,
    )
    meta = bundle.as_meta()
    visible_slots = set(meta["visible_material_slots"])

    assert meta["safety_triage_kind"] == TRIAGE_SAFE_OBSERVATION
    assert meta["material_quality"] == MATERIAL_QUALITY_ELIGIBLE
    assert meta["material_quality"] != MATERIAL_QUALITY_SAFETY_TRIAGE_REQUIRED
    assert {
        VISIBLE_MATERIAL_SLOT_EVENT,
        VISIBLE_MATERIAL_SLOT_EMOTION_DIRECTION,
        VISIBLE_MATERIAL_SLOT_RELATIONSHIP,
        VISIBLE_MATERIAL_SLOT_TARGET,
        VISIBLE_MATERIAL_SLOT_ACTION,
        VISIBLE_MATERIAL_SLOT_CHANGE,
        VISIBLE_MATERIAL_SLOT_TIME,
    }.issubset(visible_slots)
    assert meta["raw_input_included"] is False
    assert meta["raw_text_included"] is False
    assert meta["comment_text_body_included"] is False
    assert meta["comment_text_generated"] is False
    assert meta["case_specific_route_used"] is False
    assert meta["case_id_runtime_condition_used"] is False
    assert meta["public_response_key_added"] is False
    assert meta["rn_visible_contract_changed"] is False
    assert_emlis_input_material_bundle_meta_contract(meta)



def test_r4_emotion_submit_positive_change_public_path_returns_labelled_two_stage_not_self_denial(
    monkeypatch,
) -> None:
    """R4: positive public E2E returns labelled two-stage through /emotion/submit.

    The case id is used only by the test fixture. Runtime still flows through
    /emotion/submit -> reply_service -> Complete Composer; no case-specific
    branch, fixed commentText, public response key, API route, RN, or DB change
    is added.
    """

    import asyncio

    import emotion_submit_service as submit_service
    from test_emotion_submit_two_stage_reception_e2e import (  # local public E2E helpers
        _assert_public_two_stage_input_feedback_contract,
        _patch_reply_rendering,
        _patch_submit_persistence,
    )

    case_id = "positive_change_after_work_streaming"
    case = two_stage_reception_case_by_id(case_id)
    current_input = dict(case["current_input"])
    _patch_submit_persistence(monkeypatch, current_input)
    _patch_reply_rendering(monkeypatch)

    async def _submit() -> dict:
        return await submit_service.persist_emotion_submission(
            user_id=f"p7-hold004-r4-user-{case_id}",
            emotions=current_input["emotions"],
            memo=current_input["memo"],
            memo_action=current_input["memo_action"],
            category=current_input["category"],
            created_at=current_input["created_at"],
            is_secret=bool(current_input.get("is_secret")),
        )

    result = asyncio.run(_submit())
    _assert_public_two_stage_input_feedback_contract(
        result=result,
        case_id=case_id,
        current_input=current_input,
    )

    comment_text = result["input_feedback_comment"]
    meta = result["input_feedback_meta"]
    lineage = meta["public_surface_lineage"]
    recomposition = meta["labelled_two_stage_surface_recomposition_summary"]

    assert comment_text.startswith("見えたこと：\n")
    assert "\n\nEmlisから：\n" in comment_text
    assert lineage["candidate_source_kind"] == "labelled_two_stage_surface_recomposition_candidate"
    assert lineage["candidate_source_kind"] != "self_denial_safe_state_answer"
    assert lineage["labelled_two_stage_surface_recomposition_used"] is True
    assert lineage["surface_requirement_family"] == "labelled_two_stage"
    assert lineage["two_stage_required"] is True
    assert lineage["safety_gate_relaxed"] is False
    assert lineage["raw_input_included"] is False
    assert lineage["comment_text_body_included"] is False
    assert lineage["candidate_body_included"] is False
    assert recomposition["labelled_two_stage_surface_recomposition_used"] is True
    assert recomposition["two_stage_required"] is True
    assert recomposition["plain_surface_allowed"] is False
    assert recomposition["display_gate_relaxed"] is False
    assert recomposition["raw_input_included"] is False
    assert recomposition["comment_text_body_included"] is False
    assert meta["public_feedback_meta_boundary"]["raw_input_included"] is False
    assert meta["public_feedback_meta_boundary"]["comment_text_body_included"] is False
    assert meta["public_feedback_meta_boundary"]["candidate_body_included"] is False
    assert meta["submit_speed_regression"].get("reply_timeout") is False
    assert meta["submit_speed_regression"].get("public_feedback_included") is True


@pytest.mark.parametrize(
    "text",
    (
        "自分の気持ちをうまく表現できないし、私は価値がないと思ってしまう。",
        "まだ言葉にできないけれど、私はできない人間だと思ってしまう。",
        "自分の中の変化を整理できないまま、全部自分が悪いと思ってしまう。",
        "自分は価値がないし、何をしても駄目だと思ってしまう。",
        "私はできない人間で、そんな自分が嫌いだ。",
        "全部自分のせいで、私が悪いと思ってしまう。",
    ),
)
def test_r5_true_self_denial_stays_safe_state_answer_even_near_expression_difficulty(text: str) -> None:
    decision = classify_emlis_safety_triage_text(text)
    meta = decision.as_meta()

    assert meta["safety_triage_kind"] == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER
    assert meta["response_kind"] == "self_denial_safe_state_answer"
    assert meta["must_not_accept_identity_claim_as_fact"] is True
    assert meta["safe_state_answer_allowed"] is True
    assert meta["public_input_feedback_allowed"] is True
    assert meta["public_emlis_observation_allowed"] is True
    assert meta["requires_separate_safety_surface"] is False
    _assert_body_free_safety_meta(meta)


def test_r5_expression_difficulty_boundary_does_not_soften_emergency_or_support_required() -> None:
    emergency = classify_emlis_safety_triage_text("うまく表現できないけれど、もう消えたい。今日で終わりにしたい。")
    emergency_meta = emergency.as_meta()
    assert emergency_meta["safety_triage_kind"] == TRIAGE_SAFETY_BLOCKED_EMERGENCY
    assert emergency_meta["response_kind"] == "safety_blocked_emergency"
    assert emergency_meta["public_input_feedback_allowed"] is False
    assert emergency_meta["public_emlis_observation_allowed"] is False
    assert emergency_meta["requires_separate_safety_surface"] is True
    _assert_body_free_safety_meta(emergency_meta)

    support = classify_emlis_safety_triage_text("まだ言葉にできないけれど、安全が保てない。助けが必要。")
    support_meta = support.as_meta()
    assert support_meta["safety_triage_kind"] == TRIAGE_SAFETY_SUPPORT_REQUIRED
    assert support_meta["response_kind"] == "safety_support_required"
    assert support_meta["public_input_feedback_allowed"] is False
    assert support_meta["public_emlis_observation_allowed"] is False
    assert support_meta["requires_separate_safety_surface"] is True
    _assert_body_free_safety_meta(support_meta)


def test_r5_expression_difficulty_near_self_reference_stays_normal_observation() -> None:
    probes = (
        "自分の変化が大きすぎて、まだ言葉にできない。",
        "私は嬉しいのと驚きが混ざって、うまく言えない。",
        "自分の中で起きたことを、まだ整理できない。",
    )

    for text in probes:
        decision = classify_emlis_safety_triage_text(text)
        meta = decision.as_meta()
        assert meta["safety_triage_kind"] == TRIAGE_SAFE_OBSERVATION
        assert meta["response_kind"] == "normal_observation"
        assert meta["safe_state_answer_allowed"] is False
        assert meta["normal_observation_allowed"] is True
        _assert_body_free_safety_meta(meta)


def test_r6_positive_boundary_repaired_material_is_body_free_target_green_but_hold_open() -> None:
    material = build_p7_hold004_positive_public_shape_boundary_repaired_material()

    assert material["schema_version"] == P7_HOLD004_POSITIVE_PUBLIC_SHAPE_SCHEMA_VERSION
    assert material["status"] == P7_HOLD004_POSITIVE_PUBLIC_SHAPE_REPAIRED_STATUS
    assert material["hold_id"] == "P7-HOLD-004"
    assert material["runtime_repair_applied"] is True
    assert material["r2_runtime_repair_applied"] is True
    assert material["r3_input_material_bundle_not_safety_triage_required"] is True
    assert material["r4_public_e2e_labelled_two_stage_confirmed"] is True
    assert material["r5_safety_regression_preserved"] is True
    assert material["target_green_confirmed"] is True
    assert material["true_self_denial_regression_preserved"] is True
    assert material["emergency_safety_regression_preserved"] is True
    assert material["support_required_regression_preserved"] is True
    assert material["full_backend_suite_green_confirmed"] is False
    assert material["full_backend_suite_green_claim_allowed"] is False
    assert material["hold004_close_allowed"] is False
    assert material["p7_complete_claim_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert material["body_free"] is True
    assert material["public_contract"]["public_response_key_added"] is False
    assert material["public_contract"]["rn_visible_contract_changed"] is False
    assert material["body_free_markers"]["raw_input_included"] is False
    assert material["body_free_markers"]["comment_text_body_included"] is False
    assert material["body_free_markers"]["candidate_body_included"] is False
    assert material["body_free_markers"]["surface_body_included"] is False
    assert material["body_free_markers"]["reviewer_free_text_included"] is False
    assert material["body_free_markers"]["terminal_output_included"] is False
    assert "P7-HOLD-004" in material["unresolved_hold_refs"]
    assert_p7_hold004_positive_public_shape_boundary_contract(material)


def test_r6_positive_boundary_matrix_handoff_validation_carry_target_green_without_closing_hold004() -> None:
    material = build_p7_hold004_positive_public_shape_boundary_repaired_material()
    backend_split = build_p7_backend_suite_split_matrix(
        hold004_positive_public_shape_boundary=material,
    )
    r10_matrix = build_p7_r10_hold_matrix(
        backend_suite_split_matrix=backend_split,
        hold004_positive_public_shape_boundary=material,
    )
    handoff = build_p7_release_decision_handoff(
        backend_suite_split_matrix=backend_split,
        r10_hold_matrix=r10_matrix,
        hold004_positive_public_shape_boundary=material,
    )
    validation = build_p7_validation_regression_matrix(
        backend_suite_split_matrix=backend_split,
        r10_hold_matrix=r10_matrix,
        release_handoff=handoff,
        hold004_positive_public_shape_boundary=material,
    )

    assert backend_split["hold004_positive_public_shape_boundary_status"] == P7_HOLD004_POSITIVE_PUBLIC_SHAPE_REPAIRED_STATUS
    assert backend_split["hold004_positive_public_shape_target_green_confirmed"] is True
    assert backend_split["hold004_positive_public_shape_repaired_target_green_pending_full_suite"] is True
    assert backend_split["hold004_positive_public_shape_full_backend_suite_green_confirmed"] is False
    assert backend_split["hold004_positive_public_shape_release_allowed"] is False
    assert backend_split["full_backend_suite_green_confirmed"] is False
    assert backend_split["release_allowed"] is False
    assert "P7-HOLD-004" in backend_split["unresolved_hold_refs"]
    assert "positive_public_shape_target_green_pending_full_suite" in backend_split["required_followup_fixes"]

    assert r10_matrix["hold004_positive_public_shape_target_green_confirmed"] is True
    assert r10_matrix["hold004_positive_public_shape_full_backend_suite_green_confirmed"] is False
    assert r10_matrix["hold004_positive_public_shape_release_allowed"] is False
    assert r10_matrix["full_backend_suite_green_confirmed"] is False
    assert r10_matrix["release_allowed"] is False
    assert "P7-HOLD-004" in r10_matrix["unresolved_hold_refs"]

    manual = handoff["manual_hold_status"]
    assert handoff["hold004_positive_public_shape_target_green_confirmed"] is True
    assert handoff["hold004_positive_public_shape_full_backend_suite_green_confirmed"] is False
    assert handoff["hold004_positive_public_shape_release_allowed"] is False
    assert manual["hold004_positive_public_shape_target_green_confirmed"] is True
    assert manual["hold004_positive_public_shape_full_backend_suite_green_confirmed"] is False
    assert manual["hold004_positive_public_shape_release_allowed"] is False
    assert handoff["release_allowed"] is False
    assert "P7-HOLD-004" in handoff["unresolved_hold_refs"]
    assert "positive_public_shape_target_green_pending_full_suite" in handoff["required_followup_fixes"]

    assert validation["hold004_positive_public_shape_boundary_status"] == P7_HOLD004_POSITIVE_PUBLIC_SHAPE_REPAIRED_STATUS
    assert validation["summary"]["hold004_positive_public_shape_target_green_confirmed"] is True
    assert validation["summary"]["hold004_positive_public_shape_full_backend_suite_green_confirmed"] is False
    assert validation["summary"]["hold004_positive_public_shape_release_allowed"] is False
    assert validation["row_statuses"]["P7-VAL-019"] == "PASS"
    assert validation["release_allowed"] is False
    assert "P7-HOLD-004" in validation["unresolved_hold_refs"]

    assert_p7_backend_suite_split_matrix_contract(backend_split)
    assert_p7_r10_hold_matrix_contract(r10_matrix)
    assert_p7_release_decision_handoff_contract(handoff)
    assert_p7_validation_regression_matrix_contract(validation)


def test_r8_positive_boundary_implementation_result_doc_exists_and_keeps_non_release_boundary() -> None:
    doc_path = Path(__file__).resolve().parents[1] / P7_HOLD004_POSITIVE_PUBLIC_SHAPE_IMPLEMENTATION_RESULT_DOC_PATH
    text = doc_path.read_text(encoding="utf-8")

    assert doc_path.exists()
    assert "R8 実装結果doc / release handoff参照更新" in text
    assert "P7-HOLD-004" in text
    assert "GitHub接続確認: Mash様指定により未実施" in text
    assert "DB変更: なし" in text
    assert "RN変更: なし" in text
    assert "API route / request key / public response top-level key変更: なし" in text
    assert "Gate緩和: なし" in text
    assert "fixed commentText追加: なし" in text
    assert "case専用branch追加: なし" in text
    assert "true self-denial regression確認結果" in text
    assert "emergency / support required regression確認結果" in text
    assert "positive public E2E確認結果" in text
    assert "P7-HOLD-004全体: 未解消" in text
    assert "full_backend_suite_green_confirmed: false" in text
    assert "p7_complete: false" in text
    assert "p8_start_allowed: false" in text
    assert "release_allowed: false" in text


def test_r8_positive_boundary_implementation_result_doc_is_handoff_reference_only() -> None:
    material = build_p7_hold004_positive_public_shape_boundary_repaired_material()
    backend_split = build_p7_backend_suite_split_matrix(
        hold004_positive_public_shape_boundary=material,
    )
    r10_matrix = build_p7_r10_hold_matrix(
        backend_suite_split_matrix=backend_split,
        hold004_positive_public_shape_boundary=material,
    )
    handoff = build_p7_release_decision_handoff(
        backend_suite_split_matrix=backend_split,
        r10_hold_matrix=r10_matrix,
        hold004_positive_public_shape_boundary=material,
    )

    assert handoff["hold004_positive_public_shape_implementation_result_doc_path"] == (
        P7_HOLD004_POSITIVE_PUBLIC_SHAPE_IMPLEMENTATION_RESULT_DOC_PATH
    )
    assert handoff["hold004_positive_public_shape_implementation_result_doc_ref"] == (
        P7_HOLD004_POSITIVE_PUBLIC_SHAPE_IMPLEMENTATION_RESULT_DOC_REF
    )
    assert P7_HOLD004_POSITIVE_PUBLIC_SHAPE_IMPLEMENTATION_RESULT_DOC_PATH in handoff[
        "implementation_result_doc_refs"
    ]
    assert handoff["source_material_status"]["hold004_positive_public_shape_implementation_result_documented"] is True
    assert handoff["source_material_status"]["hold004_positive_public_shape_implementation_result_doc_ref"] == (
        P7_HOLD004_POSITIVE_PUBLIC_SHAPE_IMPLEMENTATION_RESULT_DOC_REF
    )
    assert handoff["manual_hold_status"]["hold004_positive_public_shape_implementation_result_documented"] is True
    assert handoff["manual_hold_status"]["hold004_positive_public_shape_implementation_result_doc_ref"] == (
        P7_HOLD004_POSITIVE_PUBLIC_SHAPE_IMPLEMENTATION_RESULT_DOC_REF
    )
    assert handoff["release_allowed"] is False
    assert handoff["manual_hold_status"]["p7_complete_claim_allowed"] is False
    assert handoff["manual_hold_status"]["p8_start_allowed"] is False
    assert handoff["manual_hold_status"]["release_allowed"] is False
    assert handoff["hold004_positive_public_shape_full_backend_suite_green_confirmed"] is False

    missing_doc_ref = dict(handoff)
    missing_doc_ref["implementation_result_doc_refs"] = [
        ref
        for ref in handoff["implementation_result_doc_refs"]
        if ref != P7_HOLD004_POSITIVE_PUBLIC_SHAPE_IMPLEMENTATION_RESULT_DOC_PATH
    ]
    with pytest.raises(ValueError):
        assert_p7_release_decision_handoff_contract(missing_doc_ref)

    wrong_manual_ref = dict(handoff)
    wrong_manual_ref["manual_hold_status"] = dict(handoff["manual_hold_status"])
    wrong_manual_ref["manual_hold_status"]["hold004_positive_public_shape_implementation_result_doc_ref"] = "wrong_ref"
    with pytest.raises(ValueError):
        assert_p7_release_decision_handoff_contract(wrong_manual_ref)

    assert_p7_release_decision_handoff_contract(handoff)


def test_r6_contracts_reject_positive_boundary_release_or_full_suite_promotion() -> None:
    material = build_p7_hold004_positive_public_shape_boundary_repaired_material()

    promoted_material = dict(material)
    promoted_material["full_backend_suite_green_confirmed"] = True
    with pytest.raises(ValueError):
        assert_p7_hold004_positive_public_shape_boundary_contract(promoted_material)

    backend_split = build_p7_backend_suite_split_matrix(
        hold004_positive_public_shape_boundary=material,
    )
    promoted_backend = dict(backend_split)
    promoted_backend["hold004_positive_public_shape_full_backend_suite_green_confirmed"] = True
    with pytest.raises(ValueError):
        assert_p7_backend_suite_split_matrix_contract(promoted_backend)

    r10_matrix = build_p7_r10_hold_matrix(
        backend_suite_split_matrix=backend_split,
        hold004_positive_public_shape_boundary=material,
    )
    promoted_r10 = dict(r10_matrix)
    promoted_r10["hold004_positive_public_shape_release_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_r10_hold_matrix_contract(promoted_r10)

    handoff = build_p7_release_decision_handoff(
        backend_suite_split_matrix=backend_split,
        r10_hold_matrix=r10_matrix,
        hold004_positive_public_shape_boundary=material,
    )
    promoted_handoff = dict(handoff)
    promoted_handoff["hold004_positive_public_shape_release_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_release_decision_handoff_contract(promoted_handoff)

    validation = build_p7_validation_regression_matrix(
        backend_suite_split_matrix=backend_split,
        r10_hold_matrix=r10_matrix,
        release_handoff=handoff,
        hold004_positive_public_shape_boundary=material,
    )
    promoted_validation = dict(validation)
    promoted_validation["summary"] = dict(validation["summary"])
    promoted_validation["summary"]["hold004_positive_public_shape_release_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_validation_regression_matrix_contract(promoted_validation)
