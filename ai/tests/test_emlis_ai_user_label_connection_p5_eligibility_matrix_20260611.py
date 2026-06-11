# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

import pytest

from emlis_ai_user_label_connection_p5_eligibility_matrix import (
    DECISION_BLOCKED,
    DECISION_CONNECTABLE,
    DECISION_META_ONLY,
    DECISION_REVIEW_REQUIRED,
    USER_LABEL_CONNECTION_P5_ELIGIBILITY_MATRIX_SCHEMA_VERSION,
    USER_LABEL_CONNECTION_P5_ELIGIBILITY_MATRIX_STEP,
    assert_user_label_connection_p5_eligibility_matrix_contract,
    build_user_label_connection_p5_eligibility_matrix,
    user_label_connection_p5_eligibility_matrix_public_summary,
)
from emlis_ai_user_label_connection_p5_readiness import build_user_label_connection_p5_readiness
from emlis_ai_user_label_connection_p5_visibility_boundary import build_user_label_connection_p5_visibility_boundary
from fixtures.emlis_ai_product_readfeel_p4_regression_handoff_20260610 import (
    SCENARIO_GREEN_REGRESSION_P5_HOLD,
    SCENARIO_GREEN_REGRESSION_P5_READY,
    build_product_readfeel_p4_regression_handoff_summary_from_ratings_review_20260610,
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
    "reply_text",
    "replyText",
    "surface_text",
    "surfaceText",
    "display_text",
    "displayText",
    "visible_text",
    "visibleText",
    "body",
    "text",
}


def _contains_forbidden_raw_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(str(key) in FORBIDDEN_RAW_KEYS or _contains_forbidden_raw_key(child) for key, child in value.items())
    if isinstance(value, list):
        return any(_contains_forbidden_raw_key(child) for child in value)
    return False


def _readiness_ready() -> dict[str, Any]:
    handoff = build_product_readfeel_p4_regression_handoff_summary_from_ratings_review_20260610(
        scenario=SCENARIO_GREEN_REGRESSION_P5_READY,
        run_id="p5_2_ready_handoff",
    )
    return build_user_label_connection_p5_readiness(handoff, run_id="p5_2_ready")


def _readiness_hold() -> dict[str, Any]:
    handoff = build_product_readfeel_p4_regression_handoff_summary_from_ratings_review_20260610(
        scenario=SCENARIO_GREEN_REGRESSION_P5_HOLD,
        run_id="p5_2_hold_handoff",
    )
    return build_user_label_connection_p5_readiness(handoff, run_id="p5_2_hold")


def _material_meta(**overrides: Any) -> dict[str, Any]:
    material = {
        "capability_tier": "plus",
        "source_scope": "current_input_with_owned_history",
        "record_scope": "current_input_with_owned_history",
        "history_read_allowed": True,
        "current_point_present": True,
        "current_input_included": True,
        "user_fact_grounding_boundary_passed": True,
        "material_quality": "history_connection_candidate",
        "connection_edges": [
            {
                "edge_family": "category_state_recurrence",
                "evidence_record_count": 2,
                "current_record_included": True,
                "evidence_point_ids": ["current:present", "history:owned:001"],
            }
        ],
        "max_edge_evidence_record_count": 2,
    }
    material.update(overrides)
    return material


def _gate_meta(**overrides: Any) -> dict[str, Any]:
    gate = {
        "passed": True,
        "blocked": False,
        "source_scope": "current_input_with_owned_history",
        "evidence_contract": {
            "evidence_record_count": 2,
            "current_record_included": True,
            "history_record_count": 1,
        },
        "scope_marker_required": True,
        "soft_marker_required": True,
    }
    gate.update(overrides)
    return gate


def _surface_plan_meta(**overrides: Any) -> dict[str, Any]:
    surface = {
        "surface_plan_kind": "limited_history_line_observation",
        "connectable_family": "structure_question",
        "source_scope": "current_input_with_owned_history",
        "evidence_contract": {
            "evidence_record_count": 2,
            "current_record_included": True,
            "history_record_count": 1,
        },
        "scope_marker_required": True,
        "soft_marker_required": True,
    }
    surface.update(overrides)
    return surface


def _existing_gate_reports() -> dict[str, Any]:
    return {
        "display_gate": {"passed": True},
        "grounding_gate": {"passed": True},
        "visible_surface_acceptance_gate": {"passed": True},
        "runtime_surface_pre_return_gate": {"passed": True},
        "template_gate": {"passed": True},
    }


def _visibility_boundary(*, readiness: dict[str, Any] | None = None, **overrides: Any) -> dict[str, Any]:
    args = {
        "p5_readiness": readiness or _readiness_ready(),
        "material_meta": _material_meta(),
        "gate_meta": _gate_meta(),
        "surface_plan_meta": _surface_plan_meta(),
        "observation_reply_meta": {"family": "structure_question", "low_information": False},
        "existing_comment_text_present": True,
        "existing_gate_reports": _existing_gate_reports(),
        "subscription_tier": "plus",
        "run_id": "p5_2_visibility_boundary",
    }
    args.update(overrides)
    return build_user_label_connection_p5_visibility_boundary(**args)


def _matrix(**overrides: Any) -> dict[str, Any]:
    args = {
        "p5_visibility_boundary": _visibility_boundary(),
        "material_meta": _material_meta(),
        "gate_meta": _gate_meta(),
        "surface_plan_meta": _surface_plan_meta(),
        "observation_reply_meta": {"family": "structure_question", "low_information": False},
        "edge_meta": {
            "edge_family": "category_state_recurrence",
            "evidence_record_count": 2,
            "current_record_included": True,
            "evidence_point_ids": ["current:present", "history:owned:001"],
        },
        "run_id": "p5_2_matrix",
    }
    args.update(overrides)
    return build_user_label_connection_p5_eligibility_matrix(**args)


def test_p5_2_connects_only_limited_family_and_allow_edge_after_p5_1_boundary() -> None:
    matrix = _matrix(run_id="p5_2_connectable_test")

    assert matrix["schema_version"] == USER_LABEL_CONNECTION_P5_ELIGIBILITY_MATRIX_SCHEMA_VERSION
    assert matrix["step"] == USER_LABEL_CONNECTION_P5_ELIGIBILITY_MATRIX_STEP
    assert matrix["decision"] == DECISION_CONNECTABLE
    assert matrix["connectable"] is True
    assert matrix["meta_only"] is False
    assert matrix["review_required"] is False
    assert matrix["blocked"] is False
    assert matrix["rejection_reasons"] == []
    assert matrix["connectable_family"] == "structure_question"
    assert matrix["family_decision"] == DECISION_CONNECTABLE
    assert matrix["edge_family"] == "category_state_recurrence"
    assert matrix["edge_decision"] == DECISION_CONNECTABLE
    assert matrix["eligibility"]["p5_visibility_boundary_allowed"] is True
    assert matrix["eligibility"]["owned_history_only"] is True
    assert matrix["eligibility"]["current_record_included"] is True
    assert matrix["eligibility"]["evidence_record_count"] == 2
    assert matrix["eligibility"]["history_record_count"] == 1
    assert matrix["matrix_contract"]["limited_connectable_families"] == [
        "long_meaning_arc",
        "self_understanding_follow",
        "structure_question",
    ]
    assert matrix["matrix_contract"]["allow_edge_families"] == [
        "category_state_recurrence",
        "label_route_current_alignment",
    ]
    assert matrix["visible_surface_connected"] is False
    assert matrix["comment_text_generated_by_this_layer"] is False
    assert matrix["public_contract"]["response_shape_changed"] is False
    assert matrix["public_contract"]["public_response_key_added"] is False
    assert matrix["body_free"]["raw_text_included"] is False
    assert matrix["body_free"]["history_raw_text_included"] is False
    assert _contains_forbidden_raw_key(matrix) is False
    assert_user_label_connection_p5_eligibility_matrix_contract(matrix)


def test_p5_2_allows_label_route_current_alignment_as_the_second_initial_edge() -> None:
    matrix = _matrix(
        connectable_family="self_understanding_follow",
        edge_meta={
            "edge_family": "label_route_current_alignment",
            "evidence_record_count": 2,
            "current_record_included": True,
            "evidence_point_ids": ["current:present", "history:owned:001"],
        },
        run_id="p5_2_label_route_allow_edge_test",
    )

    assert matrix["decision"] == DECISION_CONNECTABLE
    assert matrix["connectable_family"] == "self_understanding_follow"
    assert matrix["edge_family"] == "label_route_current_alignment"
    assert matrix["edge_decision"] == DECISION_CONNECTABLE
    assert_user_label_connection_p5_eligibility_matrix_contract(matrix)


def test_p5_2_review_required_edges_do_not_become_connectable_visible_candidates() -> None:
    for edge_family in [
        "state_output_attachment",
        "action_state_bridge",
        "unresolved_weight_reappearance",
        "value_line_reappearance",
        "category_output_route",
    ]:
        matrix = _matrix(
            edge_meta={
                "edge_family": edge_family,
                "evidence_record_count": 2,
                "current_record_included": True,
                "evidence_point_ids": ["current:present", "history:owned:001"],
            },
            run_id=f"p5_2_review_edge_{edge_family}",
        )

        assert matrix["decision"] == DECISION_REVIEW_REQUIRED
        assert matrix["connectable"] is False
        assert matrix["review_required"] is True
        assert f"edge_family_review_required:{edge_family}" in matrix["rejection_reasons"]
        assert_user_label_connection_p5_eligibility_matrix_contract(matrix)


def test_p5_2_meta_only_families_and_edges_stay_invisible_without_hard_blocking() -> None:
    daily = _matrix(
        connectable_family="daily_unpleasant",
        run_id="p5_2_daily_unpleasant_meta_only_test",
    )
    assert daily["decision"] == DECISION_META_ONLY
    assert daily["meta_only"] is True
    assert "family_suppressed_meta_only:daily_unpleasant" in daily["rejection_reasons"]

    contrast = _matrix(
        edge_meta={
            "edge_family": "contrast_line_shift",
            "evidence_record_count": 2,
            "current_record_included": True,
            "evidence_point_ids": ["current:present", "history:owned:001"],
        },
        run_id="p5_2_contrast_edge_meta_only_test",
    )
    assert contrast["decision"] == DECISION_META_ONLY
    assert contrast["edge_decision"] == DECISION_META_ONLY
    assert "edge_family_meta_only:contrast_line_shift" in contrast["rejection_reasons"]


def test_p5_2_blocks_initial_visible_for_low_information_safety_self_denial_and_target_judgement() -> None:
    for family, reason in [
        ("low_information_short", "family_blocked_initial_p5:low_information_short"),
        ("limited_grounding", "family_blocked_initial_p5:limited_grounding"),
        ("self_denial", "family_blocked_initial_p5:self_denial"),
        ("anger_or_boundary", "family_blocked_initial_p5:anger_or_boundary"),
        ("safety_adjacent", "family_blocked_initial_p5:safety_adjacent"),
    ]:
        matrix = _matrix(connectable_family=family, run_id=f"p5_2_blocked_family_{family}")

        assert matrix["decision"] == DECISION_BLOCKED
        assert matrix["blocked"] is True
        assert reason in matrix["rejection_reasons"]
        assert_user_label_connection_p5_eligibility_matrix_contract(matrix)


def test_p5_2_blocks_when_p5_1_visibility_boundary_is_not_allowed() -> None:
    hold_boundary = _visibility_boundary(readiness=_readiness_hold(), run_id="p5_2_p5_1_hold_boundary")
    matrix = _matrix(
        p5_visibility_boundary=hold_boundary,
        run_id="p5_2_p5_1_not_allowed_block_test",
    )

    assert hold_boundary["allow_limited_visible"] is False
    assert matrix["decision"] == DECISION_BLOCKED
    assert "p5_visibility_boundary_not_allowed" in matrix["rejection_reasons"]
    assert "p5_visibility:p5_entry_not_allowed" in matrix["rejection_reasons"]
    assert_user_label_connection_p5_eligibility_matrix_contract(matrix)


def test_p5_2_blocks_missing_current_input_insufficient_evidence_and_non_owned_scope() -> None:
    matrix = _matrix(
        material_meta=_material_meta(
            source_scope="current_input_with_owned_history_and_cross_core",
            record_scope="current_input_with_owned_history_and_cross_core",
            current_point_present=False,
            current_input_included=False,
            max_edge_evidence_record_count=1,
            connection_edges=[
                {
                    "edge_family": "category_state_recurrence",
                    "evidence_record_count": 1,
                    "current_record_included": False,
                    "evidence_point_ids": ["history:owned:001"],
                }
            ],
        ),
        gate_meta=_gate_meta(
            source_scope="current_input_with_owned_history_and_cross_core",
            evidence_contract={"evidence_record_count": 1, "current_record_included": False, "history_record_count": 1},
        ),
        surface_plan_meta=_surface_plan_meta(
            source_scope="current_input_with_owned_history_and_cross_core",
            evidence_contract={"evidence_record_count": 1, "current_record_included": False, "history_record_count": 1},
        ),
        edge_meta={
            "edge_family": "category_state_recurrence",
            "evidence_record_count": 1,
            "current_record_included": False,
            "evidence_point_ids": ["history:owned:001"],
        },
        run_id="p5_2_evidence_scope_block_test",
    )

    assert matrix["decision"] == DECISION_BLOCKED
    assert "source_scope_not_owned_history" in matrix["rejection_reasons"]
    assert "current_input_missing" in matrix["rejection_reasons"]
    assert "evidence_record_count_insufficient" in matrix["rejection_reasons"]
    assert_user_label_connection_p5_eligibility_matrix_contract(matrix)


def test_p5_2_unsupported_or_missing_edge_family_is_blocked() -> None:
    unsupported = _matrix(
        edge_meta={
            "edge_family": "unsupported_edge_family",
            "evidence_record_count": 2,
            "current_record_included": True,
            "evidence_point_ids": ["current:present", "history:owned:001"],
        },
        run_id="p5_2_unsupported_edge_block_test",
    )
    assert unsupported["decision"] == DECISION_BLOCKED
    assert "edge_family_unsupported_blocked:unsupported_edge_family" in unsupported["rejection_reasons"]

    missing = _matrix(
        material_meta=_material_meta(connection_edges=[]),
        edge_meta=None,
        run_id="p5_2_missing_edge_block_test",
    )
    assert missing["decision"] == DECISION_BLOCKED
    assert "edge_family_missing" in missing["rejection_reasons"]


def test_p5_2_detects_raw_payload_and_contract_mutation_without_leaking_bodies() -> None:
    raw_payload = _matrix(
        material_meta=_material_meta(memo="raw memo must not be retained"),
        run_id="p5_2_raw_payload_block_test",
    )
    assert raw_payload["decision"] == DECISION_BLOCKED
    assert "raw_text_payload_detected" in raw_payload["rejection_reasons"]
    assert _contains_forbidden_raw_key(raw_payload) is False
    assert_user_label_connection_p5_eligibility_matrix_contract(raw_payload)

    mutation = _matrix(
        surface_plan_meta=_surface_plan_meta(public_response_key_added=True),
        run_id="p5_2_contract_mutation_block_test",
    )
    assert mutation["decision"] == DECISION_BLOCKED
    assert "contract_mutation_detected" in mutation["rejection_reasons"]
    assert_user_label_connection_p5_eligibility_matrix_contract(mutation)


def test_p5_2_public_summary_is_body_free_and_contract_stable() -> None:
    matrix = _matrix(run_id="p5_2_public_summary_source")
    public_summary = user_label_connection_p5_eligibility_matrix_public_summary(matrix)
    dumped = json.dumps(public_summary, ensure_ascii=False, sort_keys=True)

    assert public_summary["decision"] == DECISION_CONNECTABLE
    assert public_summary["connectable"] is True
    assert public_summary["public_response_key_added"] is False
    assert public_summary["response_shape_changed"] is False
    assert public_summary["raw_text_included"] is False
    assert public_summary["comment_text_body_included"] is False
    assert public_summary["history_raw_text_included"] is False
    assert '"comment_text"' not in dumped
    assert '"current_input"' not in dumped
    assert '"history_records"' not in dumped
    assert_user_label_connection_p5_eligibility_matrix_contract(public_summary, allow_partial=True)


def test_p5_2_contract_guard_rejects_body_keys_and_forbidden_true_flags() -> None:
    with pytest.raises(ValueError):
        assert_user_label_connection_p5_eligibility_matrix_contract(
            {"schema_version": USER_LABEL_CONNECTION_P5_ELIGIBILITY_MATRIX_SCHEMA_VERSION, "text": "body"}
        )

    with pytest.raises(ValueError):
        assert_user_label_connection_p5_eligibility_matrix_contract(
            {
                "schema_version": USER_LABEL_CONNECTION_P5_ELIGIBILITY_MATRIX_SCHEMA_VERSION,
                "step": USER_LABEL_CONNECTION_P5_ELIGIBILITY_MATRIX_STEP,
                "public_response_key_added": True,
            },
            allow_partial=True,
        )
