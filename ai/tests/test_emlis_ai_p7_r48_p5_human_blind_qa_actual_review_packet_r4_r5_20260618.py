# -*- coding: utf-8 -*-
"""R48 R4/R5 contract tests for P5 Human Blind QA actual review packet work."""

from __future__ import annotations

import json

import pytest

from emlis_ai_p7_r46_p5_p6_human_readfeel_handoff_material import P5_HUMAN_BLIND_QA_RATING_AXES
from emlis_ai_p7_r47_local_review_packet_policy import (
    P7_R47_P5_REVIEWER_FACING_ALLOWED_FIELD_REFS,
    P7_R47_P5_REVIEWER_FACING_FORBIDDEN_FIELD_REFS,
)
from emlis_ai_p7_r48_p5_human_blind_qa_actual_review_packet import (
    P7_R48_BLIND_CASE_ID_CASE_REF_SEPARATION_SCHEMA_VERSION,
    P7_R48_CONTROLLER_MANIFEST_ROW_FIELD_REFS,
    P7_R48_P5_REVIEWER_PACKET_BODY_FIELD_REFS,
    P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_FORBIDDEN_FIELD_REFS,
    P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_REQUIRED_FIELD_REFS,
    P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_SCHEMA_VERSION,
    P7_R48_P5_REVIEWER_PACKET_REVIEWER_VISIBLE_FIELD_REFS,
    P7_R48_R4_NEXT_REQUIRED_STEP_REF,
    P7_R48_R4_R5_IMPLEMENTED_STEPS,
    P7_R48_R4_R5_NEXT_REQUIRED_STEP_REF,
    P7_R48_R4_R5_NOT_YET_IMPLEMENTED_STEPS,
    P7_R48_R4_R5_REVIEWER_PACKET_SCHEMA_FREEZE_SCHEMA_VERSION,
    P7_R48_REVIEWER_FACING_CASE_INDEX_ROW_FIELD_REFS,
    P7_R48_REVIEWER_FACING_LOCAL_PACKET_SCHEMA_FREEZE_SCHEMA_VERSION,
    P7_R48_REVIEW_KIND,
    P7_R48_REVIEW_PROMPT_VERSION,
    P7_R48_PACKET_KIND,
    assert_p7_r48_blind_case_id_case_ref_separation_contract,
    assert_p7_r48_p5_reviewer_facing_local_packet_schema_freeze_contract,
    assert_p7_r48_p5_reviewer_packet_local_only_payload_contract,
    assert_p7_r48_r4_r5_reviewer_packet_schema_freeze_contract,
    build_p7_r48_blind_case_id_case_ref_separation,
    build_p7_r48_p5_reviewer_facing_local_packet_schema_freeze,
    build_p7_r48_r2_r3_local_storage_case_matrix_freeze,
    build_p7_r48_r4_r5_reviewer_packet_schema_freeze,
)

LOCAL_ONLY_CURRENT_SURFACE = "local-only current surface fixture"
LOCAL_ONLY_RETURNED_SURFACE = "local-only returned Emlis surface fixture"
LOCAL_ONLY_HISTORY_SURFACE = "local-only bounded owned history surface fixture"


def _dumped(payload: object) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def _assert_release_closed(payload: dict) -> None:
    for key in (
        "release_allowed",
        "p7_complete",
        "p8_start_allowed",
        "hold004_close_allowed",
        "full_backend_suite_green_confirmed",
    ):
        assert payload[key] is False


def _minimal_local_only_packet(blind_case_id: str = "p7r48-p5-bqa-s000-001") -> dict:
    return {
        "schema_version": P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_SCHEMA_VERSION,
        "local_only": True,
        "must_not_export": True,
        "disposal_required": True,
        "packet_kind": P7_R48_PACKET_KIND,
        "review_kind": P7_R48_REVIEW_KIND,
        "review_session_id": "p7_r48_p5_first_formal_review_session",
        "packet_ref_id": "p7r48-p5-packet-s000-001",
        "blind_case_id": blind_case_id,
        "review_prompt_version": P7_R48_REVIEW_PROMPT_VERSION,
        "current_input_review_surface": LOCAL_ONLY_CURRENT_SURFACE,
        "returned_emlis_surface": LOCAL_ONLY_RETURNED_SURFACE,
        "bounded_owned_history_review_surface": LOCAL_ONLY_HISTORY_SURFACE,
        "review_questions": [
            "q1",
            "q2",
            "q3",
            "q4",
            "q5",
            "q6",
            "q7",
            "q8",
        ],
        "axis_rating_form": {
            "score_min": 0.0,
            "score_max": 1.0,
            "required_axes": list(P5_HUMAN_BLIND_QA_RATING_AXES),
            "free_text_allowed_local_only": True,
        },
    }


def test_r48_r4_builds_body_free_blind_case_id_case_ref_separation() -> None:
    freeze = build_p7_r48_r2_r3_local_storage_case_matrix_freeze(session_short_ref="s024")
    separation = build_p7_r48_blind_case_id_case_ref_separation(r2_r3_freeze=freeze)
    assert_p7_r48_blind_case_id_case_ref_separation_contract(separation)

    assert separation["schema_version"] == P7_R48_BLIND_CASE_ID_CASE_REF_SEPARATION_SCHEMA_VERSION
    assert separation["next_required_step"] == P7_R48_R4_NEXT_REQUIRED_STEP_REF
    assert separation["packet_kind"] == P7_R48_PACKET_KIND
    assert separation["review_kind"] == P7_R48_REVIEW_KIND
    assert separation["case_count"] == 24
    assert separation["case_ref_count"] == 24
    assert separation["blind_case_id_count"] == 24
    assert separation["case_ref_to_blind_case_ref_separated"] is True
    assert separation["controller_manifest_keeps_case_ref_family_tier"] is True
    assert separation["reviewer_facing_identifier_policy"] == "blind_case_id_only"
    assert separation["reviewer_facing_uses_blind_case_id_only"] is True
    assert separation["reviewer_facing_case_ref_id_allowed"] is False
    assert separation["reviewer_facing_family_allowed"] is False
    assert separation["reviewer_facing_subscription_tier_allowed"] is False
    assert separation["blind_case_id_derived_from_body_or_record_hash"] is False
    assert separation["blind_case_id_derived_from_record_id_hash"] is False
    assert separation["body_full_packet_materialized_here"] is False
    assert separation["local_reviewer_payload_materialized_here"] is False
    assert separation["actual_body_full_packet_generated_here"] is False
    assert separation["body_full_writer_created_here"] is False
    assert separation["actual_human_review_run_here"] is False
    _assert_release_closed(separation)

    controller_rows = separation["controller_manifest_rows"]
    reviewer_rows = separation["reviewer_facing_case_index_rows"]
    assert len(controller_rows) == 24
    assert len(reviewer_rows) == 24
    assert {row["blind_case_id"] for row in controller_rows} == {row["blind_case_id"] for row in reviewer_rows}

    for row in controller_rows:
        assert set(row) == set(P7_R48_CONTROLLER_MANIFEST_ROW_FIELD_REFS)
        assert row["controller_only"] is True
        assert row["reviewer_receives_blind_case_id"] is True
        assert row["reviewer_receives_case_ref_id"] is False
        assert row["reviewer_receives_family"] is False
        assert row["reviewer_receives_subscription_tier"] is False
        assert row["reviewer_receives_expected_result"] is False
        assert row["reviewer_receives_gate_result"] is False
        assert row["blind_case_id_derived_from_body_or_record_hash"] is False
        assert row["body_free"] is True

    for row in reviewer_rows:
        assert set(row) == set(P7_R48_REVIEWER_FACING_CASE_INDEX_ROW_FIELD_REFS)
        assert set(row).isdisjoint({"case_ref_id", "family", "subscription_tier_ref", "expected_result", "gate_result"})
        assert row["reviewer_identifier_kind"] == "blind_case_id_only"
        assert row["case_ref_hidden"] is True
        assert row["family_hidden"] is True
        assert row["tier_hidden"] is True
        assert row["expected_result_hidden"] is True
        assert row["gate_result_hidden"] is True
        assert row["derived_from_body_or_record_hash"] is False
        assert row["body_free"] is True

    dumped = _dumped(separation)
    assert LOCAL_ONLY_CURRENT_SURFACE not in dumped
    assert LOCAL_ONLY_RETURNED_SURFACE not in dumped
    assert LOCAL_ONLY_HISTORY_SURFACE not in dumped


def test_r48_r4_separation_contract_rejects_reviewer_leak_or_blind_id_leak() -> None:
    separation = build_p7_r48_blind_case_id_case_ref_separation()
    separation["reviewer_facing_case_index_rows"][0]["case_ref_id"] = "p7r48-p5-case-001"
    with pytest.raises(ValueError):
        assert_p7_r48_blind_case_id_case_ref_separation_contract(separation)

    separation = build_p7_r48_blind_case_id_case_ref_separation()
    separation["controller_manifest_rows"][0]["blind_case_id"] = "p7r48-p5-bqa-free-tier-001"
    with pytest.raises(ValueError):
        assert_p7_r48_blind_case_id_case_ref_separation_contract(separation)

    separation = build_p7_r48_blind_case_id_case_ref_separation()
    separation["reviewer_facing_family_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_r48_blind_case_id_case_ref_separation_contract(separation)


def test_r48_r5_fixes_reviewer_facing_local_packet_schema_without_materializing_body_payload() -> None:
    schema = build_p7_r48_p5_reviewer_facing_local_packet_schema_freeze()
    assert_p7_r48_p5_reviewer_facing_local_packet_schema_freeze_contract(schema)

    assert schema["schema_version"] == P7_R48_REVIEWER_FACING_LOCAL_PACKET_SCHEMA_FREEZE_SCHEMA_VERSION
    assert schema["packet_schema_version"] == P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_SCHEMA_VERSION
    assert schema["packet_kind"] == P7_R48_PACKET_KIND
    assert schema["review_kind"] == P7_R48_REVIEW_KIND
    assert schema["review_prompt_version"] == P7_R48_REVIEW_PROMPT_VERSION
    assert schema["reviewer_facing_identifier_policy"] == "blind_case_id_only"
    assert tuple(schema["reviewer_visible_field_refs"]) == P7_R48_P5_REVIEWER_PACKET_REVIEWER_VISIBLE_FIELD_REFS
    assert tuple(schema["reviewer_visible_field_refs"]) == P7_R47_P5_REVIEWER_FACING_ALLOWED_FIELD_REFS
    assert tuple(schema["required_field_refs"]) == P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_REQUIRED_FIELD_REFS
    assert tuple(schema["allowed_payload_field_refs"]) == P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_REQUIRED_FIELD_REFS
    assert set(P7_R47_P5_REVIEWER_FACING_FORBIDDEN_FIELD_REFS).issubset(set(schema["forbidden_payload_field_refs"]))
    assert tuple(schema["local_only_body_field_refs"]) == P7_R48_P5_REVIEWER_PACKET_BODY_FIELD_REFS
    assert schema["additional_properties_allowed"] is False
    assert schema["local_only_required"] is True
    assert schema["must_not_export_required"] is True
    assert schema["disposal_required_required"] is True
    assert schema["case_ref_visible_to_reviewer_allowed"] is False
    assert schema["family_visible_to_reviewer_allowed"] is False
    assert schema["subscription_tier_visible_to_reviewer_allowed"] is False
    assert schema["public_meta_in_reviewer_payload_allowed"] is False
    assert schema["body_free_material_can_include_local_packet_payload"] is False
    assert schema["json_schema_file_created_here"] is False
    assert schema["body_full_packet_materialized_here"] is False
    assert schema["local_reviewer_payload_materialized_here"] is False
    assert schema["actual_body_full_packet_generated_here"] is False
    assert schema["body_full_writer_created_here"] is False
    assert schema["actual_human_review_run_here"] is False
    assert schema["next_required_step"] == P7_R48_R4_R5_NEXT_REQUIRED_STEP_REF
    _assert_release_closed(schema)

    axis_contract = schema["axis_rating_form_contract"]
    assert axis_contract["score_min"] == 0.0
    assert axis_contract["score_max"] == 1.0
    assert axis_contract["required_axis_refs"] == list(P5_HUMAN_BLIND_QA_RATING_AXES)
    assert axis_contract["free_text_allowed_local_only"] is True
    assert axis_contract["free_text_bodyfree_allowed"] is False


def test_r48_r5_schema_contract_rejects_field_boundary_drift() -> None:
    schema = build_p7_r48_p5_reviewer_facing_local_packet_schema_freeze()
    schema["allowed_payload_field_refs"] = [*schema["allowed_payload_field_refs"], "family"]
    with pytest.raises(ValueError):
        assert_p7_r48_p5_reviewer_facing_local_packet_schema_freeze_contract(schema)

    schema = build_p7_r48_p5_reviewer_facing_local_packet_schema_freeze()
    schema["forbidden_payload_field_refs"] = [
        field for field in schema["forbidden_payload_field_refs"] if field != "case_ref_id"
    ]
    with pytest.raises(ValueError):
        assert_p7_r48_p5_reviewer_facing_local_packet_schema_freeze_contract(schema)

    schema = build_p7_r48_p5_reviewer_facing_local_packet_schema_freeze()
    schema["case_ref_visible_to_reviewer_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_r48_p5_reviewer_facing_local_packet_schema_freeze_contract(schema)


def test_r48_r5_local_only_payload_contract_accepts_schema_shape_and_rejects_controller_leaks() -> None:
    payload = _minimal_local_only_packet()
    assert_p7_r48_p5_reviewer_packet_local_only_payload_contract(payload)

    payload = _minimal_local_only_packet()
    payload["case_ref_id"] = "p7r48-p5-case-001"
    with pytest.raises(ValueError):
        assert_p7_r48_p5_reviewer_packet_local_only_payload_contract(payload)

    payload = _minimal_local_only_packet(blind_case_id="p7r48-p5-bqa-history-line-001")
    with pytest.raises(ValueError):
        assert_p7_r48_p5_reviewer_packet_local_only_payload_contract(payload)

    payload = _minimal_local_only_packet()
    payload["axis_rating_form"]["required_axes"] = ["changed_axis"]
    with pytest.raises(ValueError):
        assert_p7_r48_p5_reviewer_packet_local_only_payload_contract(payload)


def test_r48_r4_r5_combined_freeze_keeps_review_release_closed_and_points_to_r6() -> None:
    freeze = build_p7_r48_r4_r5_reviewer_packet_schema_freeze()
    assert_p7_r48_r4_r5_reviewer_packet_schema_freeze_contract(freeze)

    assert freeze["schema_version"] == P7_R48_R4_R5_REVIEWER_PACKET_SCHEMA_FREEZE_SCHEMA_VERSION
    assert freeze["implemented_steps"] == list(P7_R48_R4_R5_IMPLEMENTED_STEPS)
    assert freeze["not_yet_implemented_steps"] == list(P7_R48_R4_R5_NOT_YET_IMPLEMENTED_STEPS)
    assert freeze["next_required_step"] == P7_R48_R4_R5_NEXT_REQUIRED_STEP_REF
    assert freeze["packet_kind"] == P7_R48_PACKET_KIND
    assert freeze["review_kind"] == P7_R48_REVIEW_KIND
    assert freeze["case_count"] == 24
    assert freeze["minimums_satisfied"] is True
    assert freeze["r0_current_source_r47_handoff_hold_refrozen"] is True
    assert freeze["r1_scope_schema_packet_kind_fixed"] is True
    assert freeze["local_storage_root_policy_connected"] is True
    assert freeze["p5_24_case_first_formal_review_matrix_built"] is True
    assert freeze["blind_case_id_case_ref_separated"] is True
    assert freeze["reviewer_facing_local_packet_schema_fixed"] is True
    assert freeze["body_free_case_matrix_ready"] is True
    assert freeze["actual_case_matrix_materialized_here"] is True
    assert freeze["body_full_packet_materialized_here"] is False
    assert freeze["local_reviewer_payload_materialized_here"] is False
    assert freeze["actual_body_full_packet_generated_here"] is False
    assert freeze["body_full_writer_created_here"] is False
    assert freeze["actual_human_review_run_here"] is False
    assert freeze["p5_human_blind_qa_actual_review_start_allowed_after_r4_r5"] is False
    assert freeze["p5_human_blind_qa_confirmed"] is False
    assert freeze["p6_limited_human_readfeel_start_allowed"] is False
    assert freeze["real_device_modal_review_start_allowed"] is False
    _assert_release_closed(freeze)


def test_r48_r4_r5_rejects_body_payload_inputs_and_release_promotion() -> None:
    r2_r3 = build_p7_r48_r2_r3_local_storage_case_matrix_freeze()
    r2_r3["reviewer_free_text"] = "must remain local-only"
    with pytest.raises(ValueError):
        build_p7_r48_blind_case_id_case_ref_separation(r2_r3_freeze=r2_r3)

    freeze = build_p7_r48_r4_r5_reviewer_packet_schema_freeze()
    freeze["release_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_r48_r4_r5_reviewer_packet_schema_freeze_contract(freeze)

    freeze = build_p7_r48_r4_r5_reviewer_packet_schema_freeze()
    freeze["local_reviewer_payload_materialized_here"] = True
    with pytest.raises(ValueError):
        assert_p7_r48_r4_r5_reviewer_packet_schema_freeze_contract(freeze)
