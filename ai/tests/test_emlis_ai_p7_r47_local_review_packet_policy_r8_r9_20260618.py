# -*- coding: utf-8 -*-
"""P7-R47 R8/R9 disposal-retention and P5 human Blind QA packet policy freeze."""

from __future__ import annotations

import json

import pytest

from emlis_ai_p7_r46_p5_p6_human_readfeel_handoff_material import (
    P5_HUMAN_BLIND_QA_FAMILIES,
    P5_HUMAN_BLIND_QA_RATING_AXES,
    P5_HUMAN_BLIND_QA_TARGETS,
)
from emlis_ai_p7_r47_local_review_packet_policy import (
    P7_R47_BODY_FREE_DISPOSAL_RECEIPT_FORBIDDEN_FIELD_REFS,
    P7_R47_BODY_FREE_DISPOSAL_RECEIPT_REQUIRED_FIELD_REFS,
    P7_R47_BODY_FREE_DISPOSAL_RECEIPT_SCHEMA_VERSION,
    P7_R47_BODY_FULL_PACKET_DELETE_TRIGGER_REFS,
    P7_R47_BODY_FULL_PACKET_RETENTION_HOURS,
    P7_R47_DISPOSAL_CLEANUP_RETENTION_POLICY_SCHEMA_VERSION,
    P7_R47_DISPOSAL_STATUSES,
    P7_R47_P5_FIRST_FORMAL_MINIMUMS,
    P7_R47_P5_HISTORY_SURFACE_MAX_RECORDS,
    P7_R47_P5_HISTORY_SURFACE_MIN_EVIDENCE_RECORDS,
    P7_R47_P5_HUMAN_BLIND_QA_PACKET_POLICY_SCHEMA_VERSION,
    P7_R47_P5_REVIEWER_FACING_ALLOWED_FIELD_REFS,
    P7_R47_P5_REVIEWER_FACING_FORBIDDEN_FIELD_REFS,
    P7_R47_PACKET_KINDS,
    P7_R47_R8_R9_DISPOSAL_P5_POLICY_SCHEMA_VERSION,
    P7_R47_R8_R9_IMPLEMENTED_STEPS,
    P7_R47_R8_R9_NEXT_REQUIRED_STEP_REF,
    P7_R47_R8_R9_NOT_YET_IMPLEMENTED_STEPS,
    P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS,
    assert_p7_r47_body_free_disposal_receipt_payload_contract,
    assert_p7_r47_body_free_disposal_receipt_schema_contract,
    assert_p7_r47_disposal_cleanup_retention_policy_contract,
    assert_p7_r47_p5_human_blind_qa_packet_policy_contract,
    assert_p7_r47_r8_r9_disposal_p5_policy_freeze_contract,
    build_p7_r47_body_free_disposal_receipt_schema,
    build_p7_r47_disposal_cleanup_retention_policy,
    build_p7_r47_p5_human_blind_qa_packet_policy,
    build_p7_r47_r8_r9_disposal_p5_policy_freeze,
)

SECRET_INPUT = "R47 R8/R9 raw input must never enter body-free materials"
SECRET_SURFACE = "R47 R8/R9 Emlis visible surface must remain local-only"
SECRET_NOTE = "R47 R8/R9 reviewer note must remain local-only"
SECRET_PATH = "/tmp/cocolon_emlis_r47_local_review_root/body_full_packets.local_only"


def _dumped(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _assert_no_body_or_release_promotion(value: object) -> None:
    dumped = _dumped(value)
    assert SECRET_INPUT not in dumped
    assert SECRET_SURFACE not in dumped
    assert SECRET_NOTE not in dumped
    assert SECRET_PATH not in dumped
    assert '"raw_input":' not in dumped
    assert '"comment_text":' not in dumped
    assert '"candidate_body":' not in dumped
    assert '"surface_body":' not in dumped
    assert '"reviewer_free_text":' not in dumped
    assert '"reviewer_notes":' not in dumped
    assert '"terminal_output":' not in dumped
    assert '"stdout":' not in dumped
    assert '"stderr":' not in dumped
    assert '"traceback":' not in dumped
    assert '"release_allowed": true' not in dumped.lower()
    assert '"p7_complete": true' not in dumped.lower()
    assert '"p8_start_allowed": true' not in dumped.lower()
    assert '"hold004_close_allowed": true' not in dumped.lower()


def _receipt() -> dict[str, object]:
    return {
        "schema_version": P7_R47_BODY_FREE_DISPOSAL_RECEIPT_SCHEMA_VERSION,
        "review_session_id": "review-session-001",
        "packet_kind": P7_R47_PACKET_KINDS[0],
        "case_count": 24,
        "deleted_file_count": 24,
        "disposal_status": "DISPOSAL_VERIFIED",
        "body_removed": True,
        "reviewer_notes_removed": True,
        "local_packet_exported": False,
        "content_hash_of_body_stored": False,
        "body_free": True,
        "release_allowed": False,
        "p7_complete": False,
        "p8_start_allowed": False,
        "hold004_close_allowed": False,
    }


def test_r47_r8_body_free_disposal_receipt_schema_is_shape_only() -> None:
    schema = build_p7_r47_body_free_disposal_receipt_schema()
    assert_p7_r47_body_free_disposal_receipt_schema_contract(schema)

    assert schema["schema_version"] == P7_R47_BODY_FREE_DISPOSAL_RECEIPT_SCHEMA_VERSION
    assert schema["policy_section"] == "R8_body_free_disposal_receipt_schema"
    assert tuple(schema["receipt_required_field_refs"]) == P7_R47_BODY_FREE_DISPOSAL_RECEIPT_REQUIRED_FIELD_REFS
    assert tuple(schema["receipt_forbidden_field_refs"]) == P7_R47_BODY_FREE_DISPOSAL_RECEIPT_FORBIDDEN_FIELD_REFS
    assert tuple(schema["disposal_status_enum"]) == P7_R47_DISPOSAL_STATUSES
    assert schema["content_hash_of_body_allowed"] is False
    assert schema["body_full_packet_export_allowed"] is False
    assert schema["release_allowed"] is False

    json_schema = schema["receipt_json_schema"]
    assert json_schema["$id"] == P7_R47_BODY_FREE_DISPOSAL_RECEIPT_SCHEMA_VERSION
    assert tuple(json_schema["required"]) == P7_R47_BODY_FREE_DISPOSAL_RECEIPT_REQUIRED_FIELD_REFS
    assert set(json_schema["properties"]) == set(P7_R47_BODY_FREE_DISPOSAL_RECEIPT_REQUIRED_FIELD_REFS)
    assert tuple(json_schema["properties"]["packet_kind"]["enum"]) == P7_R47_PACKET_KINDS
    assert tuple(json_schema["properties"]["disposal_status"]["enum"]) == P7_R47_DISPOSAL_STATUSES
    for forbidden in P7_R47_BODY_FREE_DISPOSAL_RECEIPT_FORBIDDEN_FIELD_REFS:
        assert forbidden not in json_schema["properties"]

    _assert_no_body_or_release_promotion(schema)


def test_r47_r8_disposal_cleanup_retention_policy_fixes_retention_and_no_hash() -> None:
    policy = build_p7_r47_disposal_cleanup_retention_policy()
    assert_p7_r47_disposal_cleanup_retention_policy_contract(policy)

    assert policy["schema_version"] == P7_R47_DISPOSAL_CLEANUP_RETENTION_POLICY_SCHEMA_VERSION
    assert policy["body_full_packet_retention_max_hours"] == P7_R47_BODY_FULL_PACKET_RETENTION_HOURS == 72
    assert policy["reviewer_notes_retention_after_rating_finalized_max_hours"] == P7_R47_REVIEWER_NOTES_RETENTION_AFTER_RATING_HOURS == 24
    assert tuple(policy["body_full_packet_delete_trigger_refs"]) == P7_R47_BODY_FULL_PACKET_DELETE_TRIGGER_REFS
    assert policy["rating_finalized_requires_purge_required"] is True
    assert policy["body_removed_required_before_p5_p6_review_confirmed"] is True
    assert policy["disposal_receipt_body_free"] is True
    assert policy["content_hash_of_body_allowed"] is False
    assert policy["content_hash_of_body_stored"] is False
    assert policy["actual_cleanup_run_here"] is False
    assert policy["actual_disposal_receipt_materialized_here"] is False
    assert policy["p5_human_blind_qa_confirmed"] is False
    assert policy["release_allowed"] is False

    _assert_no_body_or_release_promotion(policy)


def test_r47_r8_disposal_receipt_payload_accepts_only_body_free_receipt_fields() -> None:
    receipt = _receipt()
    assert_p7_r47_body_free_disposal_receipt_payload_contract(receipt)
    _assert_no_body_or_release_promotion(receipt)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("raw_input", SECRET_INPUT),
        ("comment_text", SECRET_SURFACE),
        ("reviewer_free_text", SECRET_NOTE),
        ("reviewer_notes", SECRET_NOTE),
        ("terminal_output", "terminal output must not enter receipt"),
        ("local_absolute_path", SECRET_PATH),
        ("body_full_file_content_hash", "hash must not be retained"),
    ],
)
def test_r47_r8_disposal_receipt_payload_rejects_body_note_path_or_hash_keys(key: str, value: str) -> None:
    receipt = _receipt()
    receipt[key] = value
    with pytest.raises(ValueError):
        assert_p7_r47_body_free_disposal_receipt_payload_contract(receipt)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("local_packet_exported", True),
        ("content_hash_of_body_stored", True),
        ("body_free", False),
        ("release_allowed", True),
        ("p7_complete", True),
        ("p8_start_allowed", True),
        ("hold004_close_allowed", True),
        ("disposal_status", "PRODUCT_PASS"),
        ("packet_kind", "unknown_packet_kind"),
        ("case_count", -1),
        ("deleted_file_count", -1),
    ],
)
def test_r47_r8_disposal_receipt_payload_rejects_boundary_or_enum_drift(key: str, value: object) -> None:
    receipt = _receipt()
    receipt[key] = value
    with pytest.raises(ValueError):
        assert_p7_r47_body_free_disposal_receipt_payload_contract(receipt)


def test_r47_r9_p5_packet_policy_matches_r46_handoff_families_axes_and_thresholds() -> None:
    policy = build_p7_r47_p5_human_blind_qa_packet_policy()
    assert_p7_r47_p5_human_blind_qa_packet_policy_contract(policy)

    assert policy["schema_version"] == P7_R47_P5_HUMAN_BLIND_QA_PACKET_POLICY_SCHEMA_VERSION
    assert policy["packet_kind"] == "p5_human_blind_qa_local_review_packet"
    assert tuple(policy["review_family_refs"]) == P5_HUMAN_BLIND_QA_FAMILIES
    assert tuple(policy["rating_axis_refs"]) == P5_HUMAN_BLIND_QA_RATING_AXES
    assert policy["rating_axis_target_thresholds"] == P5_HUMAN_BLIND_QA_TARGETS

    minimums = policy["first_formal_review_minimums"]
    assert minimums == P7_R47_P5_FIRST_FORMAL_MINIMUMS
    assert minimums["minimum_total_cases"] == 24
    assert minimums["minimum_per_family"] == 2
    assert minimums["minimum_history_line_eligible_input"] == 4
    assert minimums["minimum_owned_history_positive_cases"] == 12
    assert minimums["minimum_block_boundary_cases"]["low_information_history_not_eligible"] == 2
    assert minimums["minimum_block_boundary_cases"]["free_tier_history_present_not_allowed"] == 2

    assert policy["reviewer_facing_identifier_policy"] == "blind_case_id_only"
    assert tuple(policy["reviewer_facing_allowed_field_refs"]) == P7_R47_P5_REVIEWER_FACING_ALLOWED_FIELD_REFS
    assert tuple(policy["reviewer_facing_forbidden_field_refs"]) == P7_R47_P5_REVIEWER_FACING_FORBIDDEN_FIELD_REFS
    assert not (set(policy["reviewer_facing_allowed_field_refs"]) & set(policy["reviewer_facing_forbidden_field_refs"]))
    assert policy["free_tier_boundary_family_ref"] == "free_tier_history_present_not_allowed"
    assert policy["low_information_boundary_family_ref"] == "low_information_history_not_eligible"

    history_policy = policy["bounded_owned_history_review_surface_policy"]
    assert history_policy["max_history_record_surfaces"] == P7_R47_P5_HISTORY_SURFACE_MAX_RECORDS == 3
    assert history_policy["min_evidence_record_count_when_history_line_expected"] == P7_R47_P5_HISTORY_SURFACE_MIN_EVIDENCE_RECORDS == 2
    assert history_policy["history_record_identifier_policy"] == "no_db_id_no_user_id"
    assert history_policy["created_at_policy"] == "bucketed_or_relative_only"
    assert history_policy["raw_memo_full_dump_allowed"] is False
    assert history_policy["history_summary_style"] == "bounded_review_surface_local_only"

    assert policy["p5_human_blind_qa_packet_generation_allowed_here"] is False
    assert policy["actual_body_full_packet_generated_here"] is False
    assert policy["actual_human_review_run_here"] is False
    assert policy["p5_human_blind_qa_confirmed"] is False
    assert policy["p6_limited_human_readfeel_start_allowed"] is False
    assert policy["release_allowed"] is False
    _assert_no_body_or_release_promotion(policy)


@pytest.mark.parametrize(
    ("mutator"),
    [
        lambda p: p.__setitem__("review_family_refs", list(P5_HUMAN_BLIND_QA_FAMILIES[:-1])),
        lambda p: p.__setitem__("rating_axis_refs", list(P5_HUMAN_BLIND_QA_RATING_AXES[:-1])),
        lambda p: p["first_formal_review_minimums"].__setitem__("minimum_total_cases", 23),
        lambda p: p["first_formal_review_minimums"]["minimum_block_boundary_cases"].__setitem__(
            "free_tier_history_present_not_allowed", 1
        ),
        lambda p: p["bounded_owned_history_review_surface_policy"].__setitem__("max_history_record_surfaces", 4),
        lambda p: p.__setitem__("reviewer_facing_family_visible_allowed", True),
        lambda p: p.__setitem__("p5_human_blind_qa_packet_generation_allowed_here", True),
        lambda p: p.__setitem__("p5_human_blind_qa_confirmed", True),
    ],
)
def test_r47_r9_p5_packet_policy_rejects_family_axis_minimum_or_runtime_drift(mutator) -> None:  # type: ignore[no-untyped-def]
    policy = build_p7_r47_p5_human_blind_qa_packet_policy()
    mutator(policy)
    with pytest.raises(ValueError):
        assert_p7_r47_p5_human_blind_qa_packet_policy_contract(policy)


def test_r47_r8_r9_combined_policy_freeze_keeps_next_step_at_r10_and_review_closed() -> None:
    freeze = build_p7_r47_r8_r9_disposal_p5_policy_freeze()
    assert_p7_r47_r8_r9_disposal_p5_policy_freeze_contract(freeze)

    assert freeze["schema_version"] == P7_R47_R8_R9_DISPOSAL_P5_POLICY_SCHEMA_VERSION
    assert tuple(freeze["implemented_steps"]) == P7_R47_R8_R9_IMPLEMENTED_STEPS
    assert tuple(freeze["not_yet_implemented_steps"]) == P7_R47_R8_R9_NOT_YET_IMPLEMENTED_STEPS
    assert freeze["implemented_steps"][-2:] == [
        "R8_disposal_cleanup_retention_policy",
        "R9_p5_human_blind_qa_packet_policy",
    ]
    assert freeze["not_yet_implemented_steps"][0] == "R10_p6_limited_human_readfeel_packet_policy"
    assert freeze["next_required_step"] == P7_R47_R8_R9_NEXT_REQUIRED_STEP_REF
    assert freeze["disposal_policy_fixed"] is True
    assert freeze["p5_human_blind_qa_packet_policy_fixed"] is True
    assert freeze["body_full_packet_retention_max_hours"] == 72
    assert freeze["p5_first_formal_minimum_total_cases"] == 24
    assert freeze["p5_bounded_history_max_record_surfaces"] == 3
    assert freeze["local_review_packet_policy_ready"] is False
    assert freeze["policy_ready"] is False
    assert freeze["r47_policy_ready"] is False
    assert freeze["p5_human_blind_qa_start_allowed_after_r8_r9"] is False
    assert freeze["p5_human_blind_qa_confirmed"] is False
    assert freeze["p6_limited_human_readfeel_start_allowed"] is False
    assert freeze["actual_cleanup_run_here"] is False
    assert freeze["actual_disposal_receipt_materialized_here"] is False
    assert freeze["actual_body_full_packet_generated_here"] is False
    assert freeze["actual_human_review_run_here"] is False
    assert freeze["release_allowed"] is False
    assert freeze["p7_complete"] is False
    assert freeze["p8_start_allowed"] is False
    assert freeze["hold004_close_allowed"] is False
    _assert_no_body_or_release_promotion(freeze)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("raw_input", SECRET_INPUT),
        ("comment_text", SECRET_SURFACE),
        ("reviewer_free_text", SECRET_NOTE),
        ("terminal_output", "terminal output must not enter combined freeze"),
        ("release_allowed", True),
        ("p7_complete", True),
        ("p8_start_allowed", True),
        ("hold004_close_allowed", True),
        ("p5_human_blind_qa_confirmed", True),
        ("actual_human_review_run_here", True),
    ],
)
def test_r47_r8_r9_combined_policy_rejects_body_keys_or_release_review_promotion(key: str, value: object) -> None:
    freeze = build_p7_r47_r8_r9_disposal_p5_policy_freeze()
    freeze[key] = value
    with pytest.raises(ValueError):
        assert_p7_r47_r8_r9_disposal_p5_policy_freeze_contract(freeze)
