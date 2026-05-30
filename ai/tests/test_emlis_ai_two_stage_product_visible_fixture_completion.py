# -*- coding: utf-8 -*-
from __future__ import annotations

import pytest

from helpers.emlis_ai_two_stage_product_visible_fixture_assertions import (
    PHASE17_PRODUCT_VISIBLE_CLASSIFICATIONS,
    PHASE17_PRODUCT_VISIBLE_FIXTURE_EVALUATION_SCHEMA_VERSION,
    PHASE17_PRODUCT_VISIBLE_FIXTURE_SOURCE_PHASE,
    PHASE17_PRODUCT_VISIBLE_REQUIRED_CASE_IDS,
    assert_phase17_product_visible_fixture_passed,
    assert_phase17_visible_gate_blocks_forbidden_surface,
    evaluate_phase17_two_stage_product_visible_candidate,
    generate_phase17_two_stage_product_visible_candidate,
)


@pytest.mark.parametrize("case_id", PHASE17_PRODUCT_VISIBLE_REQUIRED_CASE_IDS)
def test_phase17_0_complete_composer_five_fixtures_reach_product_visible_two_stage_comment_text(case_id: str) -> None:
    candidate = generate_phase17_two_stage_product_visible_candidate(case_id)
    evaluation = evaluate_phase17_two_stage_product_visible_candidate(case_id=case_id, candidate=candidate)

    assert_phase17_product_visible_fixture_passed(evaluation)


@pytest.mark.parametrize(
    ("surface", "expected_reason_any"),
    (
        (
            "見えたこと：\nachievement が見えます。\n\nEmlisから：\n気持ちが動いた変化が残っています。",
            ("two_stage_internal_role_label_leak", "two_stage_complete_surface_internal_label_leak"),
        ),
        (
            "見えたこと：\n自分の状態が positive state として見えます。\n\nEmlisから：\n少し整えようとする動きが残っています。",
            ("two_stage_internal_role_label_leak", "two_stage_complete_surface_internal_label_leak"),
        ),
        (
            "見えたこと：\nperfection fear が前に出ています。\n\nEmlisから：\n自分の気持ちを見ようとしています。",
            ("two_stage_internal_role_label_leak", "two_stage_complete_surface_internal_label_leak"),
        ),
        (
            "見えたこと：\n同じ流れが同じ場所に残っています。\n\nEmlisから：\n片方だけに寄らずにあります。",
            ("two_stage_relation_skeleton_leak", "two_stage_relation_skeleton_leak_surface"),
        ),
    ),
)
def test_phase17_0_visible_gate_blocks_internal_role_and_relation_skeleton_leaks(
    surface: str,
    expected_reason_any: tuple[str, ...],
) -> None:
    assert_phase17_visible_gate_blocks_forbidden_surface(
        surface=surface,
        expected_reason_any=expected_reason_any,
    )


@pytest.mark.parametrize("case_id", PHASE17_PRODUCT_VISIBLE_REQUIRED_CASE_IDS)
def test_phase17_0_section_budget_matches_product_visible_fixture_expectations(case_id: str) -> None:
    candidate = generate_phase17_two_stage_product_visible_candidate(case_id)
    evaluation = evaluate_phase17_two_stage_product_visible_candidate(case_id=case_id, candidate=candidate)

    assert evaluation["comment_text_shape"]["labels_present"] is True, evaluation
    assert evaluation["comment_text_shape"]["label_order_valid"] is True, evaluation
    assert evaluation["surface_quality"]["section_budget_valid"] is True, evaluation


@pytest.mark.parametrize("case_id", PHASE17_PRODUCT_VISIBLE_REQUIRED_CASE_IDS)
def test_phase17_1_product_visible_fixture_evaluation_helper_is_meta_only(case_id: str) -> None:
    candidate = generate_phase17_two_stage_product_visible_candidate(case_id)
    evaluation = evaluate_phase17_two_stage_product_visible_candidate(case_id=case_id, candidate=candidate)

    assert evaluation["schema_version"] == PHASE17_PRODUCT_VISIBLE_FIXTURE_EVALUATION_SCHEMA_VERSION
    assert evaluation["source_phase"] == PHASE17_PRODUCT_VISIBLE_FIXTURE_SOURCE_PHASE
    assert evaluation["classification"] in PHASE17_PRODUCT_VISIBLE_CLASSIFICATIONS
    assert "comment_text" not in evaluation
    assert "observation_text" not in evaluation
    assert "reception_text" not in evaluation
    assert evaluation["public_contract"]["public_response_key_added"] is False
    assert evaluation["public_contract"]["rn_visible_contract_changed"] is False
    assert evaluation["public_contract"]["raw_input_included"] is False
    assert evaluation["public_contract"]["comment_text_body_included"] is False
    assert evaluation["public_contract"]["display_gate_relaxed"] is False
    assert evaluation["public_contract"]["grounding_gate_relaxed"] is False
    assert evaluation["implementation_contract"]["external_ai_used"] is False
    assert evaluation["implementation_contract"]["local_llm_used"] is False


def test_phase17_6_log3_grounding_relation_binding_reaches_product_visible_without_relaxing_gate() -> None:
    """Lock the real log3 fixture at the Phase17-6 grounding boundary.

    Phase17-6 is not a synthetic grounding-only case.  The real
    independence/life/health/money/pace fixture must carry the S3 reception
    line through declared evidence / phrase / relation binding, with the
    natural relation markers surfaced in the generated line and without
    relaxing Grounding.
    """

    case_id = "independence_life_health_money_pace"
    candidate = generate_phase17_two_stage_product_visible_candidate(case_id)
    evaluation = evaluate_phase17_two_stage_product_visible_candidate(case_id=case_id, candidate=candidate)

    assert_phase17_product_visible_fixture_passed(evaluation)

    composer_meta = candidate.get("composer_meta") or {}
    grounding_input = composer_meta.get("grounding_input") or {}
    phase17_6_binding = grounding_input.get("phase17_6_grounding_relation_binding") or {}
    surface_rows = list(grounding_input.get("surface_lines") or grounding_input.get("bindings") or ())
    final_grounding = composer_meta.get("final_grounding_report") or {}
    initial_grounding = composer_meta.get("initial_grounding_report") or {}
    comment_text = str(candidate.get("comment_text") or "")

    target_row = next(
        (
            row
            for row in surface_rows
            if str(row.get("sentence_id") or "").endswith("_s3")
            or "effort_pace_reception_not_overeffort_received" in set(row.get("role_phrase_keys") or ())
        ),
        None,
    )

    assert target_row is not None, surface_rows
    assert phase17_6_binding["schema_version"] == "cocolon.emlis_two_stage.grounding_binding_patch.v1"
    assert phase17_6_binding["source_phase"] == "Phase17_6_grounding_relation_binding"
    assert phase17_6_binding["applied"] is True
    assert phase17_6_binding["case_family"] == "effort_pace_context"
    assert "standard_state_answer" in phase17_6_binding["target_modes"]
    assert "effort_support" in phase17_6_binding["target_modes"]
    assert "context_mi_nagara" in phase17_6_binding["allowed_relation_marker_codes"]
    assert "sustainable_pace_shape" in phase17_6_binding["allowed_relation_marker_codes"]
    assert "future_guarantee_jiritsu_dekimasu" in phase17_6_binding["forbidden_relation_marker_codes"]
    assert str(target_row.get("sentence_id") or "") in phase17_6_binding["relation_expression_required_sentence_ids"]
    assert phase17_6_binding["unsupported_sentence_allowed"] is False
    assert phase17_6_binding["relation_not_expressed_allowed"] is False
    assert phase17_6_binding["grounding_gate_relaxed"] is False
    assert phase17_6_binding["comment_text_body_included"] is False

    assert target_row.get("relation_type") == "coexistence"
    assert target_row.get("used_evidence_span_ids"), target_row
    assert target_row.get("used_phrase_unit_ids"), target_row
    assert target_row.get("phase17_6_grounding_relation_binding_applied") is True
    assert target_row.get("relation_expression_required") is True
    assert target_row.get("unsupported_sentence_allowed") is False
    assert target_row.get("relation_not_expressed_allowed") is False
    assert "effort_pace_reception_not_overeffort_received" in set(target_row.get("role_phrase_keys") or ())
    assert any(marker in str(target_row.get("surface_text") or "") for marker in ("並んで", "見ながら", "続けられる形")), target_row

    assert initial_grounding.get("passed") is True, initial_grounding
    assert final_grounding.get("passed") is True, final_grounding
    assert final_grounding.get("unsupported_sentence_ids") == []
    assert final_grounding.get("relation_not_expressed_sentence_ids") == []
    assert final_grounding.get("grounding_gate_relaxed") is False
    assert grounding_input.get("grounding_gate_relaxed") is False
    assert grounding_input.get("display_gate_relaxed") is False
    assert composer_meta.get("grounding_gate_relaxed") is False
    assert composer_meta.get("display_gate_relaxed") is False

    for forbidden in ("自立できます", "お金が原因", "もっと頑張りましょう"):
        assert forbidden not in comment_text
