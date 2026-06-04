from __future__ import annotations

from typing import Any

import pytest

from emlis_ai_input_material_bundle import MATERIAL_QUALITY_SAFETY_TRIAGE_REQUIRED
from emlis_ai_structure_insight_candidate import (
    RELATION_DESIRE_BLOCKAGE_CONFLICT,
    RELATION_SELF_DENIAL_IDENTITY_SPLIT,
    RELATION_VALUE_LINE_CROSSED,
    build_structure_insight_candidate_meta,
)
from emlis_ai_structure_insight_gate import (
    GATE_ACTION_ALLOW_INTERNAL_SURFACE_CANDIDATE,
    GATE_ACTION_BLOCK_SURFACE_CANDIDATE,
    STRUCTURE_INSIGHT_GATE_PHASE9_STEP,
    STRUCTURE_INSIGHT_GATE_VERSION,
    assert_structure_insight_gate_meta_only,
    build_structure_insight_gate_report,
    normalize_structure_insight_gate_to_scorecard_fields,
    structure_insight_gate_public_summary,
)


def _assert_meta_only(payload: Any) -> None:
    if isinstance(payload, dict):
        for forbidden in (
            "raw_input",
            "raw_text",
            "input_text",
            "user_input",
            "current_input",
            "memo",
            "memo_action",
            "emotion_details",
            "comment_text",
            "commentText",
            "reply_text",
            "surface_text",
            "display_text",
            "visible_text",
            "candidate_body",
            "surface_body",
            "body",
            "text",
        ):
            assert forbidden not in payload
        assert payload.get("raw_input_included") is not True
        assert payload.get("raw_text_included") is not True
        assert payload.get("input_text_included") is not True
        assert payload.get("comment_text_included") is not True
        assert payload.get("comment_text_body_included") is not True
        assert payload.get("candidate_body_included") is not True
        assert payload.get("candidate_surface_generated") is not True
        assert payload.get("candidate_body_generated") is not True
        assert payload.get("comment_text_generated") is not True
        assert payload.get("comment_text_key_written") is not True
        assert payload.get("comment_text_written_by_gate") is not True
        assert payload.get("public_response_key_added") is not True
        assert payload.get("public_response_key_change") is not True
        assert payload.get("public_payload_changed") is not True
        assert payload.get("response_shape_changed") is not True
        assert payload.get("api_route_changed") is not True
        assert payload.get("db_physical_name_changed") is not True
        assert payload.get("rn_visible_contract_changed") is not True
        assert payload.get("rn_visible_title_changed") is not True
        assert payload.get("display_gate_relaxed") is not True
        assert payload.get("grounding_gate_relaxed") is not True
        assert payload.get("reader_gate_relaxed") is not True
        assert payload.get("template_gate_relaxed") is not True
        assert payload.get("gate_relaxed") is not True
        assert payload.get("diagnosis_allowed") is not True
        assert payload.get("personality_claim_allowed") is not True
        assert payload.get("cause_claim_allowed") is not True
        assert payload.get("advice_allowed") is not True
        assert payload.get("target_judgement_agreement_allowed") is not True
        assert payload.get("period_tendency_from_single_record_allowed") is not True
        assert payload.get("user_dictionary_fact_claim_allowed") is not True
        assert payload.get("product_gate_ready") is not True
        assert payload.get("public_release_applied") is not True
        for value in payload.values():
            _assert_meta_only(value)
    elif isinstance(payload, (list, tuple)):
        for item in payload:
            _assert_meta_only(item)


def _structure_input() -> dict[str, Any]:
    return {
        "id": "phase9-structure",
        "memo": "変えたいのに動けなくて疲れた。ずっとこのままなのが不安で、どうしたらいいのか考えている",
        "memo_action": "職場で新しい役割を任されて、追加の仕事を断れなかった",
        "emotion_details": [{"type": "不安", "strength": "medium"}],
        "category": ["仕事"],
    }


def test_phase9_allows_safe_candidate_only_as_internal_next_phase_material() -> None:
    material = build_structure_insight_candidate_meta(_structure_input())
    report = build_structure_insight_gate_report(
        material,
        proposed_surface="変えたい気持ちと動けない状態が重なっているように見えます。",
        run_id="phase9-safe",
    )

    assert report["version"] == STRUCTURE_INSIGHT_GATE_VERSION
    assert report["step"] == STRUCTURE_INSIGHT_GATE_PHASE9_STEP
    assert report["phase9_structure_insight_gate_ready"] is True
    assert report["structure_insight_gate_ready"] is True
    assert report["structure_insight_candidate_connected"] is True
    assert report["passed"] is True
    assert report["blocked"] is False
    assert report["action"] == GATE_ACTION_ALLOW_INTERNAL_SURFACE_CANDIDATE
    assert report["allowed_candidate_count"] >= 1
    assert report["blocked_candidate_count"] == 0
    assert report["soft_expression_required_enforced"] is True
    assert report["soft_expression_marker_detected"] is True
    assert report["public_surface_connected"] is False
    assert report["surface_connection_deferred_to_phase10"] is True
    assert report["comment_text_generated"] is False
    assert report["public_response_key_added"] is False
    assert report["gate_relaxed"] is False
    _assert_meta_only(report)
    assert_structure_insight_gate_meta_only(report)


def test_phase9_blocks_surface_without_soft_expression_even_when_candidate_is_valid() -> None:
    material = build_structure_insight_candidate_meta(_structure_input())
    report = build_structure_insight_gate_report(
        material,
        proposed_surface="変えたい気持ちと動けない状態がぶつかっています。",
    )

    assert report["passed"] is False
    assert report["blocked"] is True
    assert report["action"] == GATE_ACTION_BLOCK_SURFACE_CANDIDATE
    assert report["soft_expression_missing_blocked"] is True
    assert "soft_expression_missing" in report["rejection_reasons"]
    assert report["public_surface_connected"] is False
    _assert_meta_only(report)


def test_phase9_blocks_diagnosis_personality_cause_advice_and_period_tendency() -> None:
    material = build_structure_insight_candidate_meta(_structure_input())
    report = build_structure_insight_gate_report(
        material,
        proposed_surface=(
            "原因は仕事です。あなたはいつも抱え込みやすい人です。"
            "これは心理学的な症状かもしれません。相談しましょう。"
        ),
    )

    assert report["passed"] is False
    assert report["unsafe_insight_surface_blocked"] is True
    assert report["single_record_period_tendency_blocked"] is True
    for reason in (
        "diagnosis_surface",
        "personality_claim_surface",
        "cause_claim_without_evidence_surface",
        "advice_surface",
        "period_tendency_from_single_record_surface",
    ):
        assert reason in report["rejection_reasons"]
    _assert_meta_only(report)


def test_phase9_blocks_user_dictionary_fact_assertion_even_when_surface_is_soft() -> None:
    material = build_structure_insight_candidate_meta(_structure_input())
    report = build_structure_insight_gate_report(
        material,
        proposed_surface="変えたい気持ちと動けない状態が重なっているように見えます。",
        user_dictionary_meta={"user_dictionary_used_as_fact": True},
    )

    assert report["passed"] is False
    assert report["user_dictionary_fact_claim_blocked"] is True
    assert "user_dictionary_fact_claim_blocked" in report["rejection_reasons"]
    assert report["public_surface_connected"] is False
    _assert_meta_only(report)


def test_phase9_applies_strict_gate_to_anger_boundary_and_target_judgement() -> None:
    material = build_structure_insight_candidate_meta(
        {
            "id": "phase9-anger",
            "memo": "相手に軽く扱われた気がして怒りが残っている。大事な線を踏まれた感じがある",
            "memo_action": "職場で上司に約束を急に変えられた",
            "emotion_details": [{"type": "怒り", "strength": "strong"}],
            "category": ["人間関係"],
        }
    )
    assert RELATION_VALUE_LINE_CROSSED in material["relation_candidate_families"]

    report = build_structure_insight_gate_report(
        material,
        proposed_surface="相手が悪いので、怒りは当然かもしれません。",
    )

    assert report["passed"] is False
    assert report["anger_or_boundary_strict_gate_active"] is True
    assert "target_judgement_agreement_surface" in report["rejection_reasons"]
    assert "anger_or_boundary_strict_gate_blocked" in report["rejection_reasons"]
    _assert_meta_only(report)


def test_phase9_applies_strict_gate_to_self_denial_identity_claims() -> None:
    material = build_structure_insight_candidate_meta(
        {
            "id": "phase9-self-denial",
            "memo": "自分が嫌で、何もできないと思ってしまう。でもこうして言葉にしようとしている",
            "memo_action": "今日も少しだけメモを書いた",
            "emotion_details": [{"type": "自己否定", "strength": "strong"}],
            "category": ["自己理解"],
        }
    )
    assert RELATION_SELF_DENIAL_IDENTITY_SPLIT in material["relation_candidate_families"]

    report = build_structure_insight_gate_report(
        material,
        proposed_surface="あなたは何もできない状態です、ということかもしれません。",
    )

    assert report["passed"] is False
    assert report["self_denial_strict_gate_active"] is True
    assert "self_denial_identity_claim_as_fact_surface" in report["rejection_reasons"]
    assert "self_denial_strict_gate_blocked" in report["rejection_reasons"]
    _assert_meta_only(report)


def test_phase9_blocks_safety_adjacent_candidate_even_without_public_surface_connection() -> None:
    safety_material = {
        "version": "cocolon.emlis.structure_insight_candidate.v1",
        "structure_insight_candidate_ready": True,
        "material_quality": MATERIAL_QUALITY_SAFETY_TRIAGE_REQUIRED,
        "candidates": [
            {
                "candidate_id": "safety_adjacent_001",
                "relation_family": RELATION_DESIRE_BLOCKAGE_CONFLICT,
                "source_scope": "current_input_only",
                "candidate_quality": "relation_candidate_ready_for_gate",
                "evidence": {
                    "source_field_ids": ["memo", "memo_action", "emotion_details"],
                    "evidence_slot_count": 3,
                    "requires_external_knowledge": False,
                    "requires_user_history": False,
                    "raw_text_included": False,
                    "comment_text_body_included": False,
                },
                "surface_permission": {
                    "must_use_soft_expression": True,
                    "must_not_surface_as_fact": True,
                },
                "forbidden_claims": [
                    "diagnosis",
                    "personality_claim",
                    "cause_claim_without_evidence",
                    "advice",
                ],
            }
        ],
        "raw_text_included": False,
        "comment_text_body_included": False,
        "public_response_key_added": False,
        "response_shape_changed": False,
    }

    report = build_structure_insight_gate_report(
        safety_material,
        proposed_surface="願いと動けなさが重なっているように見えます。",
    )

    assert report["passed"] is False
    assert report["safety_adjacent_strict_gate_active"] is True
    assert "safety_adjacent_insight_surface_blocked" in report["rejection_reasons"]
    assert report["public_surface_connected"] is False
    _assert_meta_only(report)


def test_phase9_normalizes_to_scorecard_fields_and_public_summary_without_body_leak() -> None:
    material = build_structure_insight_candidate_meta(_structure_input())
    report = build_structure_insight_gate_report(
        material,
        proposed_surface="変えたい気持ちと動けない状態が重なっているように見えます。",
    )
    fields = normalize_structure_insight_gate_to_scorecard_fields(report)
    summary = structure_insight_gate_public_summary(report)

    assert fields["phase9_structure_insight_gate_ready"] is True
    assert fields["structure_insight_gate_passed"] is True
    assert fields["structure_insight_gate_public_surface_connected"] is False
    assert fields["structure_insight_gate_gate_relaxed"] is False
    assert fields["structure_insight_gate_public_response_key_added"] is False
    assert summary["passed"] is True
    assert summary["public_surface_connected"] is False
    assert summary["public_meta_summary_only"] is True
    _assert_meta_only(fields)
    _assert_meta_only(summary)
    assert_structure_insight_gate_meta_only(fields)
    assert_structure_insight_gate_meta_only(summary)


def test_phase9_meta_only_assertion_rejects_text_or_contract_mutation() -> None:
    with pytest.raises(ValueError):
        assert_structure_insight_gate_meta_only({"comment_text": "出してはいけない"})
    with pytest.raises(ValueError):
        assert_structure_insight_gate_meta_only({"surface_text": "出してはいけない"})
    with pytest.raises(ValueError):
        assert_structure_insight_gate_meta_only({"candidate_body_included": True})
    with pytest.raises(ValueError):
        assert_structure_insight_gate_meta_only({"public_response_key_added": True})
    with pytest.raises(ValueError):
        assert_structure_insight_gate_meta_only({"gate_relaxed": True})
    with pytest.raises(ValueError):
        assert_structure_insight_gate_meta_only({"diagnosis_allowed": True})
