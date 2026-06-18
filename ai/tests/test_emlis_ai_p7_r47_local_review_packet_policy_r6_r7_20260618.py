# -*- coding: utf-8 -*-
"""P7-R47 R6/R7 body-free rating/blocker rows and local-only notes policy."""

from __future__ import annotations

import json

import pytest

from emlis_ai_p7_r47_local_review_packet_policy import (
    P7_R47_BLOCKER_KINDS,
    P7_R47_BLOCKER_STATUSES,
    P7_R47_BODY_FREE_BLOCKER_ROW_REQUIRED_FIELD_REFS,
    P7_R47_BODY_FREE_BLOCKER_ROW_SCHEMA_VERSION,
    P7_R47_BODY_FREE_RATING_BLOCKER_FORBIDDEN_FIELD_REFS,
    P7_R47_BODY_FREE_RATING_ROW_REQUIRED_FIELD_REFS,
    P7_R47_BODY_FREE_RATING_ROW_SCHEMA_VERSION,
    P7_R47_EXECUTION_BLOCKER_ID_REFS,
    P7_R47_PACKET_KINDS,
    P7_R47_R6_R7_IMPLEMENTED_STEPS,
    P7_R47_R6_R7_NEXT_REQUIRED_STEP_REF,
    P7_R47_R6_R7_NOT_YET_IMPLEMENTED_STEPS,
    P7_R47_R6_R7_RATING_BLOCKER_NOTES_POLICY_SCHEMA_VERSION,
    P7_R47_REVIEW_VERDICTS,
    P7_R47_REVIEWER_NOTES_LOCAL_ONLY_POLICY_SCHEMA_VERSION,
    P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS,
    P7_R47_SANITIZED_REASON_ID_REFS,
    assert_p7_r47_body_free_blocker_row_payload_contract,
    assert_p7_r47_body_free_blocker_row_schema_contract,
    assert_p7_r47_body_free_rating_row_payload_contract,
    assert_p7_r47_body_free_rating_row_schema_contract,
    assert_p7_r47_r6_r7_rating_blocker_notes_policy_freeze_contract,
    assert_p7_r47_reviewer_notes_local_only_policy_contract,
    build_p7_r47_body_free_blocker_row_schema,
    build_p7_r47_body_free_rating_row_schema,
    build_p7_r47_r6_r7_rating_blocker_notes_policy_freeze,
    build_p7_r47_reviewer_notes_local_only_policy,
)

SECRET_INPUT = "R47 R6/R7 raw input must not enter body-free rows"
SECRET_SURFACE = "R47 R6/R7 Emlis surface must not enter body-free rows"
SECRET_REVIEWER = "R47 R6/R7 reviewer free text must remain local-only"
SECRET_ROOT = "/tmp/cocolon_emlis_r47_local_review_root"


def _dumped(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _assert_no_body_or_release_promotion(value: object) -> None:
    dumped = _dumped(value)
    assert SECRET_INPUT not in dumped
    assert SECRET_SURFACE not in dumped
    assert SECRET_REVIEWER not in dumped
    assert SECRET_ROOT not in dumped
    assert '"raw_input":' not in dumped
    assert '"comment_text":' not in dumped
    assert '"candidate_body":' not in dumped
    assert '"surface_body":' not in dumped
    assert '"reviewer_free_text":' not in dumped
    assert '"terminal_output":' not in dumped
    assert '"stdout":' not in dumped
    assert '"stderr":' not in dumped
    assert '"release_allowed": true' not in dumped.lower()
    assert '"p7_complete": true' not in dumped.lower()
    assert '"p8_start_allowed": true' not in dumped.lower()
    assert '"hold004_close_allowed": true' not in dumped.lower()


def _rating_row() -> dict[str, object]:
    return {
        "schema_version": P7_R47_BODY_FREE_RATING_ROW_SCHEMA_VERSION,
        "review_session_id": "review-session-001",
        "packet_ref_id": "packet-ref-001",
        "blind_case_id": "blind-case-001",
        "case_ref_id": "case-ref-001",
        "packet_kind": P7_R47_PACKET_KINDS[0],
        "family": "history_line_eligible_input",
        "subscription_tier": "plus",
        "reviewer_ref": "reviewer-001",
        "reviewed_at": "2026-06-18T00:00:00+09:00",
        "axis_scores": {
            "history_connection_naturalness": 0.92,
            "creepy_absence": 0.98,
        },
        "verdict": "YELLOW",
        "sanitized_reason_ids": ["p5_history_connection_too_generic"],
        "blocker_ids": [],
        "reviewer_free_text_included": False,
        "body_removed": False,
        "body_free": True,
    }


def _blocker_row() -> dict[str, object]:
    return {
        "schema_version": P7_R47_BODY_FREE_BLOCKER_ROW_SCHEMA_VERSION,
        "review_session_id": "review-session-001",
        "packet_ref_id": "packet-ref-001",
        "blind_case_id": "blind-case-001",
        "case_ref_id": "case-ref-001",
        "packet_kind": P7_R47_PACKET_KINDS[1],
        "family": "structure_question",
        "subscription_tier": "plus",
        "blocker_id": "review_timeout_unclassified",
        "blocker_kind": "EXECUTION_BLOCKER",
        "blocker_status": "OPEN",
        "sanitized_reason_ids": ["p6_review_execution_blocked"],
        "reviewer_free_text_included": False,
        "body_removed": False,
        "body_free": True,
    }


def test_r47_r6_body_free_rating_row_schema_is_shape_only_and_not_review_result() -> None:
    schema = build_p7_r47_body_free_rating_row_schema()
    assert_p7_r47_body_free_rating_row_schema_contract(schema)

    assert schema["schema_version"] == P7_R47_BODY_FREE_RATING_ROW_SCHEMA_VERSION
    assert schema["policy_section"] == "R6_body_free_rating_row_schema"
    assert schema["schema_definition_only"] is True
    assert schema["json_schema_file_created_here"] is False
    assert tuple(schema["required_field_refs"]) == P7_R47_BODY_FREE_RATING_ROW_REQUIRED_FIELD_REFS
    assert tuple(schema["packet_kind_enum"]) == P7_R47_PACKET_KINDS
    assert tuple(schema["verdict_enum"]) == P7_R47_REVIEW_VERDICTS
    assert schema["axis_scores_machine_auto_fill_allowed"] is False
    assert schema["read_feeling_auto_estimation_allowed"] is False
    assert schema["sanitized_reason_ids_only"] is True
    assert schema["blocker_ids_only"] is True
    assert schema["reviewer_free_text_included"] is False
    assert schema["reviewer_free_text_material_allowed"] is False
    assert schema["body_removed_status_required"] is True
    assert schema["actual_rating_rows_materialized_here"] is False
    assert schema["actual_human_review_run_here"] is False
    assert schema["rating_row_schema_created_here"] is True
    assert schema["blocker_row_schema_created_here"] is False
    assert schema["release_allowed"] is False

    json_schema = schema["json_schema"]
    assert json_schema["$id"] == P7_R47_BODY_FREE_RATING_ROW_SCHEMA_VERSION
    assert tuple(json_schema["required"]) == P7_R47_BODY_FREE_RATING_ROW_REQUIRED_FIELD_REFS
    assert tuple(json_schema["properties"].keys()) == P7_R47_BODY_FREE_RATING_ROW_REQUIRED_FIELD_REFS
    for forbidden in P7_R47_BODY_FREE_RATING_BLOCKER_FORBIDDEN_FIELD_REFS:
        assert forbidden not in json_schema["properties"]

    _assert_no_body_or_release_promotion(schema)


def test_r47_r6_body_free_rating_row_payload_contract_accepts_only_ids_scores_and_status() -> None:
    row = _rating_row()
    assert_p7_r47_body_free_rating_row_payload_contract(row)
    _assert_no_body_or_release_promotion(row)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("comment_text", SECRET_SURFACE),
        ("raw_input", SECRET_INPUT),
        ("reviewer_free_text", SECRET_REVIEWER),
        ("terminal_output", "terminal output must not enter rating rows"),
    ],
)
def test_r47_r6_rating_row_payload_rejects_body_or_notes_keys(key: str, value: str) -> None:
    row = _rating_row()
    row[key] = value
    with pytest.raises(ValueError):
        assert_p7_r47_body_free_rating_row_payload_contract(row)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("reviewer_free_text_included", True),
        ("verdict", "PRODUCT_PASS"),
        ("packet_kind", "unknown_packet_kind"),
        ("subscription_tier", "enterprise"),
        ("body_free", False),
    ],
)
def test_r47_r6_rating_row_payload_rejects_false_boundary_or_enum_drift(key: str, value: object) -> None:
    row = _rating_row()
    row[key] = value
    with pytest.raises(ValueError):
        assert_p7_r47_body_free_rating_row_payload_contract(row)


def test_r47_r6_rating_row_payload_rejects_invalid_axis_score_and_non_identifier_lists() -> None:
    row = _rating_row()
    row["axis_scores"]["creepy_absence"] = 1.1
    with pytest.raises(ValueError):
        assert_p7_r47_body_free_rating_row_payload_contract(row)

    row = _rating_row()
    row["sanitized_reason_ids"] = [""]
    with pytest.raises(ValueError):
        assert_p7_r47_body_free_rating_row_payload_contract(row)


def test_r47_r6_body_free_blocker_row_schema_is_shape_only_and_body_free() -> None:
    schema = build_p7_r47_body_free_blocker_row_schema()
    assert_p7_r47_body_free_blocker_row_schema_contract(schema)

    assert schema["schema_version"] == P7_R47_BODY_FREE_BLOCKER_ROW_SCHEMA_VERSION
    assert schema["policy_section"] == "R6_body_free_blocker_row_schema"
    assert schema["schema_definition_only"] is True
    assert schema["json_schema_file_created_here"] is False
    assert tuple(schema["required_field_refs"]) == P7_R47_BODY_FREE_BLOCKER_ROW_REQUIRED_FIELD_REFS
    assert tuple(schema["packet_kind_enum"]) == P7_R47_PACKET_KINDS
    assert tuple(schema["blocker_kind_enum"]) == P7_R47_BLOCKER_KINDS
    assert tuple(schema["blocker_status_enum"]) == P7_R47_BLOCKER_STATUSES
    assert tuple(schema["execution_blocker_id_refs"]) == P7_R47_EXECUTION_BLOCKER_ID_REFS
    assert schema["sanitized_reason_ids_only"] is True
    assert schema["reviewer_free_text_included"] is False
    assert schema["body_removed_status_required"] is True
    assert schema["actual_blocker_rows_materialized_here"] is False
    assert schema["blocker_row_schema_created_here"] is True
    assert schema["rating_row_schema_created_here"] is False
    assert schema["release_allowed"] is False

    json_schema = schema["json_schema"]
    assert json_schema["$id"] == P7_R47_BODY_FREE_BLOCKER_ROW_SCHEMA_VERSION
    assert tuple(json_schema["required"]) == P7_R47_BODY_FREE_BLOCKER_ROW_REQUIRED_FIELD_REFS
    assert tuple(json_schema["properties"].keys()) == P7_R47_BODY_FREE_BLOCKER_ROW_REQUIRED_FIELD_REFS
    for forbidden in P7_R47_BODY_FREE_RATING_BLOCKER_FORBIDDEN_FIELD_REFS:
        assert forbidden not in json_schema["properties"]

    _assert_no_body_or_release_promotion(schema)


def test_r47_r6_body_free_blocker_row_payload_contract_accepts_execution_blocker_ids_only() -> None:
    row = _blocker_row()
    assert_p7_r47_body_free_blocker_row_payload_contract(row)
    _assert_no_body_or_release_promotion(row)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("comment_text", SECRET_SURFACE),
        ("reviewer_free_text", SECRET_REVIEWER),
        ("terminal_output", "terminal output must not enter blocker rows"),
    ],
)
def test_r47_r6_blocker_row_payload_rejects_body_or_notes_keys(key: str, value: str) -> None:
    row = _blocker_row()
    row[key] = value
    with pytest.raises(ValueError):
        assert_p7_r47_body_free_blocker_row_payload_contract(row)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("reviewer_free_text_included", True),
        ("blocker_kind", "READFEEL_COMMENT"),
        ("blocker_status", "DONE"),
        ("packet_kind", "unknown_packet_kind"),
        ("body_free", False),
    ],
)
def test_r47_r6_blocker_row_payload_rejects_false_boundary_or_enum_drift(key: str, value: object) -> None:
    row = _blocker_row()
    row[key] = value
    with pytest.raises(ValueError):
        assert_p7_r47_body_free_blocker_row_payload_contract(row)


def test_r47_r7_reviewer_notes_policy_is_local_only_and_reduced_to_reason_ids() -> None:
    policy = build_p7_r47_reviewer_notes_local_only_policy()
    assert_p7_r47_reviewer_notes_local_only_policy_contract(policy)

    assert policy["schema_version"] == P7_R47_REVIEWER_NOTES_LOCAL_ONLY_POLICY_SCHEMA_VERSION
    assert policy["policy_section"] == "R7_reviewer_free_text_notes_local_only_policy"
    assert policy["local_only_notes_policy_fixed"] is True
    assert policy["reviewer_free_text_policy_fixed"] is True
    assert policy["local_notes_dir_ref"] == "reviewer_notes.local_only"
    assert policy["local_notes_standard_export_allowed"] is False
    assert policy["local_notes_release_material_allowed"] is False
    assert policy["local_notes_p7_scorecard_material_allowed"] is False
    assert policy["direct_note_copy_to_p7_allowed"] is False
    assert policy["raw_quote_to_reason_id_allowed"] is False
    assert policy["sanitized_reason_id_required_for_p7_material"] is True
    assert tuple(policy["sanitized_reason_id_refs"]) == P7_R47_SANITIZED_REASON_ID_REFS
    assert tuple(policy["execution_blocker_id_refs"]) == P7_R47_EXECUTION_BLOCKER_ID_REFS
    assert policy["default_unmapped_reason_id"] == "reason_id_other_local_note_purged"
    assert policy["notes_retention_after_rating_finalized_max_hours"] == P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS
    assert policy["reviewer_free_text_included"] is False
    assert policy["actual_notes_materialized_here"] is False
    assert policy["actual_human_review_run_here"] is False
    assert policy["disposal_policy_created_here"] is False
    assert policy["release_allowed"] is False

    _assert_no_body_or_release_promotion(policy)


def test_r47_r6_r7_combined_freeze_advances_to_r8_without_starting_review_or_policy_ready() -> None:
    freeze = build_p7_r47_r6_r7_rating_blocker_notes_policy_freeze(
        local_review_root=SECRET_ROOT,
        export_roots=("/mnt/data",),
    )
    assert_p7_r47_r6_r7_rating_blocker_notes_policy_freeze_contract(freeze)

    assert freeze["schema_version"] == P7_R47_R6_R7_RATING_BLOCKER_NOTES_POLICY_SCHEMA_VERSION
    assert tuple(freeze["implemented_steps"]) == P7_R47_R6_R7_IMPLEMENTED_STEPS
    assert tuple(freeze["not_yet_implemented_steps"]) == P7_R47_R6_R7_NOT_YET_IMPLEMENTED_STEPS
    assert freeze["next_required_step"] == P7_R47_R6_R7_NEXT_REQUIRED_STEP_REF
    assert freeze["rating_row_schema_version"] == P7_R47_BODY_FREE_RATING_ROW_SCHEMA_VERSION
    assert freeze["blocker_row_schema_version"] == P7_R47_BODY_FREE_BLOCKER_ROW_SCHEMA_VERSION
    assert freeze["reviewer_notes_policy_schema_version"] == P7_R47_REVIEWER_NOTES_LOCAL_ONLY_POLICY_SCHEMA_VERSION
    assert freeze["rating_row_schema_fixed"] is True
    assert freeze["blocker_row_schema_fixed"] is True
    assert freeze["reviewer_notes_local_only_policy_fixed"] is True
    assert freeze["body_full_packet_schema_created_here"] is True
    assert freeze["body_free_manifest_schema_created_here"] is True
    assert freeze["rating_row_schema_created_here"] is True
    assert freeze["blocker_row_schema_created_here"] is True
    assert freeze["reviewer_notes_policy_created_here"] is True
    assert freeze["local_review_packet_policy_ready"] is False
    assert freeze["policy_ready"] is False
    assert freeze["r47_policy_ready"] is False
    assert freeze["p5_human_blind_qa_start_allowed_after_r6_r7"] is False
    assert freeze["p5_human_blind_qa_confirmed"] is False
    assert freeze["p6_limited_human_readfeel_start_allowed"] is False
    assert freeze["real_device_modal_review_start_allowed"] is False
    assert freeze["actual_rating_rows_materialized_here"] is False
    assert freeze["actual_blocker_rows_materialized_here"] is False
    assert freeze["actual_notes_materialized_here"] is False
    assert freeze["disposal_policy_created_here"] is False
    assert freeze["release_allowed"] is False
    assert freeze["p7_complete"] is False
    assert freeze["p8_start_allowed"] is False
    assert freeze["hold004_close_allowed"] is False

    _assert_no_body_or_release_promotion(freeze)


def test_r47_r6_r7_contracts_reject_schema_drift_notes_export_and_false_review_start() -> None:
    rating_schema = build_p7_r47_body_free_rating_row_schema()
    rating_schema["json_schema"]["properties"]["comment_text"] = {"type": "string"}
    with pytest.raises(ValueError):
        assert_p7_r47_body_free_rating_row_schema_contract(rating_schema)

    blocker_schema = build_p7_r47_body_free_blocker_row_schema()
    blocker_schema["json_schema"]["properties"]["reviewer_free_text"] = {"type": "string"}
    with pytest.raises(ValueError):
        assert_p7_r47_body_free_blocker_row_schema_contract(blocker_schema)

    notes_policy = build_p7_r47_reviewer_notes_local_only_policy()
    notes_policy["direct_note_copy_to_p7_allowed"] = True
    with pytest.raises(ValueError):
        assert_p7_r47_reviewer_notes_local_only_policy_contract(notes_policy)

    freeze = build_p7_r47_r6_r7_rating_blocker_notes_policy_freeze(
        local_review_root=SECRET_ROOT,
        export_roots=("/mnt/data",),
    )
    freeze["p5_human_blind_qa_start_allowed_after_r6_r7"] = True
    with pytest.raises(ValueError):
        assert_p7_r47_r6_r7_rating_blocker_notes_policy_freeze_contract(freeze)
