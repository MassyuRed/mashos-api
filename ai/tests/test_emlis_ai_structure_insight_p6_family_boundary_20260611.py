# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

import pytest

from emlis_ai_structure_insight_p6_family_boundary import (
    DECISION_ALLOW_LIMITED_SURFACE,
    DECISION_BLOCK,
    DECISION_HOLD,
    DECISION_META_ONLY,
    P6_ALLOWED_TARGET_FAMILIES,
    P6_NO_CONNECT_FAMILIES,
    STRUCTURE_INSIGHT_P6_FAMILY_BOUNDARY_SCHEMA_VERSION,
    STRUCTURE_INSIGHT_P6_FAMILY_BOUNDARY_STEP,
    STRUCTURE_INSIGHT_P6_FAMILY_BOUNDARY_SUMMARY_SCHEMA_VERSION,
    assert_structure_insight_p6_family_boundary_contract,
    build_structure_insight_p6_family_boundary,
    dump_structure_insight_p6_family_boundary_public_summary,
)


FORBIDDEN_RAW_KEYS = {
    "raw_input",
    "rawInput",
    "raw_text",
    "rawText",
    "source_text",
    "sourceText",
    "input",
    "input_text",
    "inputText",
    "user_input",
    "userInput",
    "current_input",
    "currentInput",
    "history_context",
    "historyContext",
    "history_records",
    "historyRecords",
    "history_raw_text",
    "historyRawText",
    "memo",
    "memo_text",
    "memoText",
    "memo_action",
    "memoAction",
    "comment_text",
    "commentText",
    "comment_text_body",
    "commentTextBody",
    "candidate_body",
    "candidateBody",
    "surface_body",
    "surfaceBody",
    "surface_text",
    "surfaceText",
    "visible_text",
    "visibleText",
    "reply_text",
    "replyText",
    "display_text",
    "displayText",
    "reviewer_note",
    "reviewer_notes",
    "reviewer_free_text",
    "raw_test_output",
    "test_output",
    "command_output",
    "terminal_output",
    "stdout",
    "stderr",
    "traceback",
    "body",
    "text",
}


def _contains_forbidden_raw_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(str(key) in FORBIDDEN_RAW_KEYS or _contains_forbidden_raw_key(child) for key, child in value.items())
    if isinstance(value, list):
        return any(_contains_forbidden_raw_key(child) for child in value)
    return False


def _allowed(family: str) -> dict[str, Any]:
    return build_structure_insight_p6_family_boundary(
        family=family,
        material_quality="eligible",
        current_input_grounded=True,
        observation_status="passed",
        run_id=f"p6_family_{family}",
    )


def test_p6_2_allows_only_initial_target_families_as_limited_surface_candidates_body_free() -> None:
    for family in P6_ALLOWED_TARGET_FAMILIES:
        boundary = _allowed(family)
        summary = boundary["summary"]

        assert boundary["schema_version"] == STRUCTURE_INSIGHT_P6_FAMILY_BOUNDARY_SCHEMA_VERSION
        assert boundary["step"] == STRUCTURE_INSIGHT_P6_FAMILY_BOUNDARY_STEP
        assert summary["schema_version"] == STRUCTURE_INSIGHT_P6_FAMILY_BOUNDARY_SUMMARY_SCHEMA_VERSION
        assert boundary["family"] == family
        assert boundary["decision"] == DECISION_ALLOW_LIMITED_SURFACE
        assert summary["decision"] == DECISION_ALLOW_LIMITED_SURFACE
        assert summary["allow_limited_surface"] is True
        assert summary["limited_surface_candidate"] is True
        assert summary["allowed_target_family"] is True
        assert summary["no_connect_reason_codes"] == []
        assert summary["deep_insight_blocked"] is False
        assert summary["release_allowed"] is False
        assert summary["public_contract"]["public_response_key_added"] is False
        assert summary["body_free"]["comment_text_body_included"] is False
        assert _contains_forbidden_raw_key(boundary) is False
        assert_structure_insight_p6_family_boundary_contract(boundary)


def test_p6_2_blocks_no_connect_families_and_keeps_reason_codes_safe() -> None:
    for family in P6_NO_CONNECT_FAMILIES:
        boundary = build_structure_insight_p6_family_boundary(
            family=family,
            material_quality="eligible",
            current_input_grounded=True,
            observation_status="passed",
            run_id=f"p6_no_connect_{family}",
        )
        summary = boundary["summary"]

        assert summary["decision"] == DECISION_BLOCK
        assert summary["block"] is True
        assert summary["allow_limited_surface"] is False
        assert summary["limited_surface_candidate"] is False
        assert summary["deep_insight_blocked"] is True
        assert summary["no_connect_family"] is True
        assert f"no_connect_family:{family}" in summary["no_connect_reason_codes"]
        assert summary["no_deep_insight_for_daily"] is True
        assert summary["no_deep_insight_for_low_information"] is True
        assert summary["no_deep_insight_for_positive_only"] is True
        assert summary["no_deep_insight_for_safety_adjacent"] is True
        assert _contains_forbidden_raw_key(summary) is False


def test_p6_2_blocks_low_information_limited_grounding_safety_and_ungrounded_material_even_in_target_family() -> None:
    for material_quality in ("low_information", "limited_grounding", "safety_triage_required"):
        boundary = build_structure_insight_p6_family_boundary(
            family="structure_question",
            material_quality=material_quality,
            current_input_grounded=True,
            observation_status="passed",
        )
        assert boundary["summary"]["decision"] == DECISION_BLOCK
        assert f"material_quality_not_connectable:{material_quality}" in boundary["summary"]["no_connect_reason_codes"]

    ungrounded = build_structure_insight_p6_family_boundary(
        family="structure_question",
        material_quality="eligible",
        current_input_grounded=False,
        observation_status="passed",
    )
    assert ungrounded["summary"]["decision"] == DECISION_BLOCK
    assert "current_input_evidence_insufficient" in ungrounded["summary"]["no_connect_reason_codes"]


def test_p6_2_keeps_allowed_family_meta_only_when_observation_status_is_not_connectable() -> None:
    boundary = build_structure_insight_p6_family_boundary(
        family="long_meaning_arc",
        material_quality="eligible",
        current_input_grounded=True,
        observation_status="hold",
        run_id="p6_family_meta_only_observation_hold",
    )
    summary = boundary["summary"]

    assert summary["decision"] == DECISION_META_ONLY
    assert summary["meta_only"] is True
    assert summary["allow_limited_surface"] is False
    assert summary["limited_surface_candidate"] is False
    assert summary["deep_insight_blocked"] is True
    assert "observation_status_not_connectable" in summary["no_connect_reason_codes"]


def test_p6_2_holds_when_family_or_material_or_grounding_is_not_confirmed_without_guessing() -> None:
    missing_family = build_structure_insight_p6_family_boundary(
        material_quality="eligible",
        current_input_grounded=True,
        observation_status="passed",
    )
    assert missing_family["summary"]["decision"] == DECISION_HOLD
    assert "family_missing" in missing_family["summary"]["no_connect_reason_codes"]

    unknown_family = build_structure_insight_p6_family_boundary(
        family="relationship_future_prediction",
        material_quality="eligible",
        current_input_grounded=True,
        observation_status="passed",
    )
    assert unknown_family["summary"]["decision"] == DECISION_HOLD
    assert "family_not_in_initial_p6_scope" in unknown_family["summary"]["no_connect_reason_codes"]

    missing_material = build_structure_insight_p6_family_boundary(
        family="self_understanding_follow",
        current_input_grounded=True,
        observation_status="passed",
    )
    assert missing_material["summary"]["decision"] == DECISION_HOLD
    assert "material_quality_not_confirmed" in missing_material["summary"]["no_connect_reason_codes"]


def test_p6_2_blocks_pre_gate_body_generation_user_dictionary_fact_target_judgement_and_safety_adjacent() -> None:
    boundary = build_structure_insight_p6_family_boundary(
        family="structure_question",
        material_quality="eligible",
        current_input_grounded=True,
        observation_status="passed",
        pre_gate_body_generated=True,
        user_dictionary_fact_assertion_required=True,
        target_judgement_required=True,
        safety_adjacent=True,
        emergency_safety=True,
        source_unavailable=True,
    )
    reasons = boundary["summary"]["no_connect_reason_codes"]

    assert boundary["summary"]["decision"] == DECISION_BLOCK
    assert "body_generated_before_gate" in reasons
    assert "user_dictionary_fact_assertion_required" in reasons
    assert "target_judgement_required" in reasons
    assert "safety_adjacent_family" in reasons
    assert "emergency_safety_family" in reasons
    assert "source_unavailable_family" in reasons


def test_p6_2_public_summary_is_body_free_and_does_not_expose_source_packets_or_release() -> None:
    dumped = dump_structure_insight_p6_family_boundary_public_summary(_allowed("structure_question"))
    parsed = json.loads(dumped)

    assert parsed["schema_version"] == STRUCTURE_INSIGHT_P6_FAMILY_BOUNDARY_SUMMARY_SCHEMA_VERSION
    assert parsed["decision"] == DECISION_ALLOW_LIMITED_SURFACE
    assert parsed["public_response_key_added"] is False
    assert parsed["response_shape_changed"] is False
    assert parsed["raw_text_included"] is False
    assert parsed["comment_text_body_included"] is False
    assert parsed["release_allowed"] is False
    assert '"family_meta"' not in dumped
    assert '"comment_text"' not in dumped
    assert '"raw_test_output"' not in dumped
    assert _contains_forbidden_raw_key(parsed) is False
    assert_structure_insight_p6_family_boundary_contract(parsed, allow_partial=True)


def test_p6_2_contract_rejects_raw_payload_keys_release_and_public_contract_mutation() -> None:
    with pytest.raises(ValueError):
        assert_structure_insight_p6_family_boundary_contract({"comment_text": "must not leak"}, allow_partial=True)
    with pytest.raises(ValueError):
        assert_structure_insight_p6_family_boundary_contract({"release_allowed": True}, allow_partial=True)

    clean = _allowed("structure_question")
    contract = dict(clean)
    contract["summary"] = {
        **clean["summary"],
        "public_contract": dict(clean["summary"]["public_contract"], response_shape_changed=True),
    }
    with pytest.raises(ValueError):
        assert_structure_insight_p6_family_boundary_contract(contract)
