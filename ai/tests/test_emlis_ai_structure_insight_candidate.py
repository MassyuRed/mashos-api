from __future__ import annotations

from typing import Any

import pytest

from emlis_ai_observation_structure_material_service import build_observation_structure_material
from emlis_ai_structure_insight_candidate import (
    RELATION_DESIRE_BLOCKAGE_CONFLICT,
    RELATION_EVENT_REACTION_LINK,
    RELATION_FEAR_LOAD_PAIR,
    RELATION_LOW_INFORMATION_UNSPECIFIED_WEIGHT,
    RELATION_SELF_DENIAL_IDENTITY_SPLIT,
    STRUCTURE_INSIGHT_CANDIDATE_PHASE7_STEP,
    STRUCTURE_INSIGHT_CANDIDATE_VERSION,
    StructureInsightCandidateMetaOnlyError,
    assert_structure_insight_candidate_meta_only,
    build_structure_insight_candidate_material,
    build_structure_insight_candidate_meta,
    normalize_structure_insight_candidate_to_scorecard_fields,
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
        assert payload.get("comment_text_generated") is not True
        assert payload.get("comment_text_written_by_candidate") is not True
        assert payload.get("comment_text_written_by_scorecard") is not True
        assert payload.get("public_response_key_added") is not True
        assert payload.get("public_response_key_change") is not True
        assert payload.get("public_payload_changed") is not True
        assert payload.get("response_shape_changed") is not True
        assert payload.get("api_route_changed") is not True
        assert payload.get("db_physical_name_changed") is not True
        assert payload.get("rn_visible_contract_changed") is not True
        assert payload.get("rn_visible_title_changed") is not True
        assert payload.get("display_gate_relaxed") is not True
        assert payload.get("gate_relaxed") is not True
        assert payload.get("diagnosis_allowed") is not True
        assert payload.get("personality_claim_allowed") is not True
        assert payload.get("cause_claim_allowed") is not True
        assert payload.get("advice_allowed") is not True
        assert payload.get("period_tendency_from_single_record") is not True
        assert payload.get("product_gate_ready") is not True
        assert payload.get("public_release_applied") is not True
        for value in payload.values():
            _assert_meta_only(value)
    elif isinstance(payload, (list, tuple)):
        for item in payload:
            _assert_meta_only(item)


def _structure_input() -> dict[str, Any]:
    return {
        "id": "phase7-structure",
        "memo": "変えたいのに動けなくて疲れた。ずっとこのままなのが不安で、どうしたらいいのか考えている",
        "memo_action": "職場で新しい役割を任されて、追加の仕事を断れなかった",
        "emotion_details": [{"type": "不安", "strength": "medium"}],
        "category": ["仕事"],
    }


def test_phase7_builds_structure_insight_candidates_from_self_report_material_meta_only() -> None:
    meta = build_structure_insight_candidate_meta(_structure_input(), run_id="phase7-candidate-test")

    assert meta["version"] == STRUCTURE_INSIGHT_CANDIDATE_VERSION
    assert meta["step"] == STRUCTURE_INSIGHT_CANDIDATE_PHASE7_STEP
    assert meta["phase7_structure_insight_candidate_ready"] is True
    assert meta["structure_insight_candidate_ready"] is True
    assert meta["candidate_material_kind"] == "internal_meta_only"
    assert meta["self_report_material"]["material_slots"]["memo_present"] is True
    assert meta["self_report_material"]["material_slots"]["memo_action_present"] is True
    assert meta["self_report_material"]["material_slots"]["emotion_details_present"] is True
    assert RELATION_EVENT_REACTION_LINK in meta["relation_candidate_families"]
    assert RELATION_DESIRE_BLOCKAGE_CONFLICT in meta["relation_candidate_families"]
    assert RELATION_FEAR_LOAD_PAIR in meta["relation_candidate_families"]
    assert meta["candidate_count"] >= 3
    assert meta["initial_public_surface_connected"] is False
    assert meta["public_surface_connected"] is False
    assert meta["surface_connection_deferred_to_structure_insight_gate"] is True
    for candidate in meta["candidates"]:
        assert candidate["source_scope"] == "current_input_only"
        assert candidate["evidence"]["raw_text_included"] is False
        assert candidate["surface_permission"]["may_surface_now"] is False
        assert candidate["surface_permission"]["must_use_soft_expression"] is True
        assert "diagnosis" in candidate["forbidden_claims"]
        assert "personality_claim" in candidate["forbidden_claims"]
        assert "cause_claim_without_evidence" in candidate["forbidden_claims"]
        assert "advice" in candidate["forbidden_claims"]
    _assert_meta_only(meta)
    assert_structure_insight_candidate_meta_only(meta)


def test_phase7_low_information_keeps_unspecified_weight_only_and_does_not_overclaim() -> None:
    meta = build_structure_insight_candidate_meta(
        {
            "id": "phase7-low-info",
            "memo": "疲れた",
            "memo_action": "",
            "emotion_details": [{"type": "悲しみ", "strength": "strong"}],
            "category": ["生活"],
        }
    )

    assert meta["material_quality"] == "low_information"
    assert meta["relation_candidate_families"] == [RELATION_LOW_INFORMATION_UNSPECIFIED_WEIGHT]
    assert meta["candidate_count"] == 1
    candidate = meta["candidates"][0]
    assert candidate["relation_family"] == RELATION_LOW_INFORMATION_UNSPECIFIED_WEIGHT
    assert candidate["inference_strength"] == "soft"
    assert candidate["candidate_quality"] == "low_information_boundary"
    assert "background_deep_reading" in candidate["forbidden_claims"]
    assert candidate["surface_permission"]["may_surface_now"] is False
    assert meta["public_surface_connected"] is False
    _assert_meta_only(meta)


def test_phase7_self_denial_candidate_keeps_identity_claim_forbidden() -> None:
    meta = build_structure_insight_candidate_meta(
        {
            "id": "phase7-self-denial",
            "memo": "自分が嫌で、何もできないと思ってしまう。でもこうして言葉にしようとしている",
            "memo_action": "今日も少しだけメモを書いた",
            "emotion_details": [{"type": "自己否定", "strength": "strong"}],
            "category": ["自己理解"],
        }
    )

    assert RELATION_SELF_DENIAL_IDENTITY_SPLIT in meta["relation_candidate_families"]
    candidate = next(
        item for item in meta["candidates"] if item["relation_family"] == RELATION_SELF_DENIAL_IDENTITY_SPLIT
    )
    assert candidate["inference_strength"] == "soft"
    assert "identity_claim_as_fact" in candidate["forbidden_claims"]
    assert "self_denial_accepted_as_user_fact" in candidate["forbidden_claims"]
    assert candidate["surface_permission"]["must_not_surface_as_personality"] is True
    _assert_meta_only(meta)


def test_phase7_uses_existing_observation_structure_material_as_supporting_material_only() -> None:
    observation_material = build_observation_structure_material(current_input=_structure_input())
    meta = build_structure_insight_candidate_meta(
        _structure_input(),
        observation_structure_material=observation_material,
        run_id="phase7-observation-material-test",
    )

    assert meta["observation_structure_material_connected"] is True
    assert meta["state_answer_surface_contract_connected"] is True
    assert meta["state_answer_surface_contract_material_only"] is True
    assert "desire_stagnation" in meta["supporting_observation_relation_ids"]
    assert meta["supporting_observation_relation_count"] >= 1
    assert meta["phase7_completion_conditions"]["public_surface_not_connected_initially"] is True
    assert meta["comment_text_generated"] is False
    assert meta["public_response_key_added"] is False
    _assert_meta_only(meta)


def test_phase7_normalizes_to_scorecard_fields_without_public_or_body_leak() -> None:
    material = build_structure_insight_candidate_material(_structure_input())
    fields = normalize_structure_insight_candidate_to_scorecard_fields(material)

    assert fields["phase7_structure_insight_candidate_ready"] is True
    assert fields["structure_insight_candidate_internal_material_only"] is True
    assert fields["structure_insight_candidate_count"] >= 3
    assert RELATION_DESIRE_BLOCKAGE_CONFLICT in fields["structure_insight_candidate_relation_families"]
    assert fields["structure_insight_candidate_must_use_soft_expression"] is True
    assert fields["structure_insight_candidate_public_surface_connected"] is False
    assert fields["structure_insight_candidate_surface_connection_deferred_to_gate"] is True
    assert fields["structure_insight_candidate_raw_text_included"] is False
    assert fields["structure_insight_candidate_comment_text_body_included"] is False
    assert fields["structure_insight_candidate_response_shape_changed"] is False
    _assert_meta_only(fields)
    assert_structure_insight_candidate_meta_only(fields)


def test_phase7_meta_only_assertion_rejects_text_or_contract_mutation() -> None:
    with pytest.raises(StructureInsightCandidateMetaOnlyError):
        assert_structure_insight_candidate_meta_only({"comment_text": "出してはいけない"})
    with pytest.raises(StructureInsightCandidateMetaOnlyError):
        assert_structure_insight_candidate_meta_only({"candidate_body_included": True})
    with pytest.raises(StructureInsightCandidateMetaOnlyError):
        assert_structure_insight_candidate_meta_only({"public_response_key_added": True})
    with pytest.raises(StructureInsightCandidateMetaOnlyError):
        assert_structure_insight_candidate_meta_only({"diagnosis_allowed": True})
