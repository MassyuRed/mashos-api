# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from copy import deepcopy

import pytest

import emlis_ai_p7_r54_p5_human_blind_qa_actual_local_review_result_handoff as r54


FORBIDDEN_DUMP_TOKENS = (
    '"raw_input":',
    '"raw_answer":',
    '"comment_text":',
    '"comment_text_body":',
    '"returned_emlis_surface":',
    '"current_input_review_surface":',
    '"bounded_owned_history_review_surface":',
    '"reviewer_free_text":',
    '"reviewer_note":',
    '"reviewer_notes":',
    '"question_text":',
    '"draft_question_text":',
    '"question_body":',
    '"local_absolute_path":',
    '"body_content_hash":',
    '"packet_content_hash":',
    '"terminal_output": "',
    '"stdout":',
    '"stderr":',
    '"traceback":',
)
FORBIDDEN_TRUE_TOKENS = (
    '"release_allowed": true',
    '"p7_complete": true',
    '"p8_start_allowed": true',
    '"hold004_close_allowed": true',
    '"p6_limited_human_readfeel_start_allowed": true',
    '"question_trigger_logic_implemented": true',
    '"p8_question_implementation_spec_finalized_here": true',
    '"api_db_rn_response_key_changed_here": true',
    '"runtime_changed_here": true',
    '"actual_human_review_run_here": true',
    '"actual_manual_review_run_here": true',
    '"body_full_packet_generated_here": true',
    '"body_full_packets_created_local_only": true',
    '"actual_rating_rows_materialized_here": true',
    '"actual_question_need_observation_rows_materialized_here": true',
    '"actual_disposal_receipt_materialized_here": true',
    '"p5_human_blind_qa_confirmed_candidate": true',
)


def _assert_body_free_no_promotion(material: dict[str, object]) -> None:
    dumped = json.dumps(material, ensure_ascii=False, sort_keys=True).lower()
    for forbidden in FORBIDDEN_DUMP_TOKENS:
        assert forbidden not in dumped
    for forbidden in FORBIDDEN_TRUE_TOKENS:
        assert forbidden not in dumped


def _ready_root(tmp_path) -> str:
    root = tmp_path / "r54_external_local_review_root"
    root.mkdir()
    return str(root)


def _ready_purge_plan() -> dict[str, object]:
    return r54.build_p7_r54_default_local_only_purge_plan_bodyfree()


def _r3_ready(tmp_path) -> dict[str, object]:
    preflight = r54.build_p7_r54_local_only_actual_review_preflight_bodyfree(
        validation_evidence_intake=r54.build_p7_r54_validation_evidence_intake_bodyfree(),
        local_review_root=_ready_root(tmp_path),
        explicit_allow_token=r54.P7_R54_EXPLICIT_LOCAL_REVIEW_ALLOW_TOKEN_REF,
        purge_plan=_ready_purge_plan(),
        export_candidate_refs=("bodyfree/result_handoff.json",),
    )
    assert preflight["preflight_status"] == "R54_LOCAL_REVIEW_PREFLIGHT_READY"
    assert r54.assert_p7_r54_local_only_actual_review_preflight_bodyfree_contract(preflight) is True
    return preflight


def _r4_ready(tmp_path) -> dict[str, object]:
    envelope = r54.build_p7_r54_actual_review_session_envelope_bodyfree(
        local_only_actual_review_preflight=_r3_ready(tmp_path),
    )
    assert envelope["envelope_status"] == "READY_FOR_24_CASE_MANIFEST_FREEZE"
    assert r54.assert_p7_r54_actual_review_session_envelope_bodyfree_contract(envelope) is True
    return envelope


def _r5_ready(tmp_path) -> dict[str, object]:
    manifest = r54.build_p7_r54_24_case_manifest_freeze_bodyfree(
        actual_review_session_envelope=_r4_ready(tmp_path),
    )
    assert manifest["manifest_status"] == "READY_FOR_LOCAL_ONLY_PACKET_GENERATION_REQUEST"
    assert r54.assert_p7_r54_24_case_manifest_freeze_bodyfree_contract(manifest) is True
    return manifest


def test_r54_r4_blocks_by_default_before_r3_preflight_ready() -> None:
    envelope = r54.build_p7_r54_actual_review_session_envelope_bodyfree()

    assert envelope["schema_version"] == r54.P7_R54_ACTUAL_REVIEW_SESSION_ENVELOPE_SCHEMA_VERSION
    assert set(envelope) == set(r54.P7_R54_ACTUAL_REVIEW_SESSION_ENVELOPE_REQUIRED_FIELD_REFS)
    assert envelope["policy_section"] == "R54-4_actual_review_session_envelope"
    assert envelope["review_session_status"] == "R54_PRECHECK_BLOCKED"
    assert envelope["envelope_status"] == "BLOCKED_BY_R54_3_PREFLIGHT"
    assert envelope["r3_preflight_ready_for_envelope"] is False
    assert "r54_actual_review_session_preflight_not_ready" in envelope["execution_blocker_ids"]
    assert envelope["body_full_generation_allowed"] is False
    assert envelope["local_only_body_full_generation_allowed"] is False
    assert envelope["actual_review_session_envelope_created_here"] is True
    assert envelope["r54_4_actual_review_session_envelope_built"] is False
    assert tuple(envelope["implemented_steps"]) == r54.P7_R54_R3_IMPLEMENTED_STEPS
    assert tuple(envelope["not_yet_implemented_steps"]) == r54.P7_R54_R3_NOT_YET_IMPLEMENTED_STEPS
    assert envelope["next_required_step"] == r54.P7_R54_R4_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert envelope["actual_human_review_run_here"] is False
    assert envelope["body_full_packet_generated_here"] is False

    assert r54.assert_p7_r54_actual_review_session_envelope_bodyfree_contract(envelope) is True
    _assert_body_free_no_promotion(envelope)


def test_r54_r4_ready_freezes_body_free_session_envelope_after_preflight(tmp_path) -> None:
    envelope = _r4_ready(tmp_path)

    assert envelope["review_session_status"] == "R54_ACTUAL_REVIEW_SESSION_ENVELOPE_READY"
    assert envelope["envelope_status"] == "READY_FOR_24_CASE_MANIFEST_FREEZE"
    assert envelope["r3_preflight_ready_for_envelope"] is True
    assert envelope["required_case_count"] == 24
    assert envelope["reviewer_ref"] == r54.P7_R54_DEFAULT_REVIEWER_REF
    assert envelope["reviewer_ref_pseudonymous"] is True
    assert envelope["actual_reviewer_name_included"] is False
    assert envelope["reviewer_notes_included"] is False
    assert envelope["reviewer_notes_materialized_here"] is False
    assert envelope["reviewer_free_text_materialized_here"] is False
    assert envelope["reviewer_blind_policy"]["reviewer_receives_blind_case_id"] is True
    assert envelope["reviewer_blind_policy"]["reviewer_receives_case_ref_id"] is False
    assert envelope["reviewer_blind_policy"]["reviewer_receives_exact_family_label"] is False
    assert tuple(envelope["reviewer_visible_field_refs"]) == r54.P7_R50_REVIEWER_VISIBLE_FIELD_REFS
    assert tuple(envelope["reviewer_hidden_field_refs"]) == r54.P7_R50_REVIEWER_HIDDEN_FIELD_REFS
    assert tuple(envelope["rating_axis_refs"]) == r54.P5_HUMAN_BLIND_QA_RATING_AXES
    assert envelope["local_root_ref"] == "external_local_review_root"
    assert envelope["root_path_exposed"] is False
    assert envelope["local_absolute_path_included"] is False
    assert envelope["body_full_generation_allowed"] is True
    assert envelope["local_only_body_full_generation_allowed"] is True
    assert envelope["disposal_plan_ready"] is True
    assert envelope["execution_blocker_ids"] == []
    assert envelope["open_execution_blocker_ids"] == []
    assert envelope["actual_human_review_run_here"] is False
    assert envelope["body_full_packet_generated_here"] is False
    assert envelope["actual_rating_rows_materialized_here"] is False
    assert envelope["actual_question_need_observation_rows_materialized_here"] is False
    assert envelope["actual_disposal_receipt_materialized_here"] is False
    assert envelope["p5_actual_review_still_not_run"] is True
    assert envelope["r54_4_actual_review_session_envelope_built"] is True
    assert tuple(envelope["implemented_steps"]) == r54.P7_R54_R4_IMPLEMENTED_STEPS
    assert tuple(envelope["not_yet_implemented_steps"]) == r54.P7_R54_R4_NOT_YET_IMPLEMENTED_STEPS
    assert envelope["next_required_step"] == r54.P7_R54_R4_NEXT_REQUIRED_STEP_REF

    _assert_body_free_no_promotion(envelope)


def test_r54_r4_sanitizes_actual_looking_reviewer_ref_to_pseudonymous_ref(tmp_path) -> None:
    envelope = r54.build_p7_r54_actual_review_session_envelope_bodyfree(
        local_only_actual_review_preflight=_r3_ready(tmp_path),
        reviewer_ref="Mash Taro",
    )
    assert envelope["reviewer_ref"] == r54.P7_R54_DEFAULT_REVIEWER_REF
    assert r54.assert_p7_r54_actual_review_session_envelope_bodyfree_contract(envelope) is True
    _assert_body_free_no_promotion(envelope)


@pytest.mark.parametrize(
    "key,value",
    [
        ("git_connection_required", True),
        ("git_checked", True),
        ("actual_reviewer_name_included", True),
        ("reviewer_notes_included", True),
        ("reviewer_notes_materialized_here", True),
        ("reviewer_free_text_materialized_here", True),
        ("reviewer_ref_pseudonymous", False),
        ("root_path_exposed", True),
        ("local_absolute_path_included", True),
        ("actual_human_review_run_here", True),
        ("body_full_packet_generated_here", True),
        ("actual_rating_rows_materialized_here", True),
        ("actual_question_need_observation_rows_materialized_here", True),
        ("p5_human_blind_qa_confirmed_candidate", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
    ],
)
def test_r54_r4_rejects_reviewer_identity_notes_review_packet_or_promotion_mutation(tmp_path, key: str, value: object) -> None:
    material = _r4_ready(tmp_path)
    material[key] = value
    with pytest.raises(ValueError):
        r54.assert_p7_r54_actual_review_session_envelope_bodyfree_contract(material)


def test_r54_r5_blocks_when_r4_envelope_is_blocked() -> None:
    manifest = r54.build_p7_r54_24_case_manifest_freeze_bodyfree()

    assert manifest["schema_version"] == r54.P7_R54_24_CASE_MANIFEST_FREEZE_SCHEMA_VERSION
    assert set(manifest) == set(r54.P7_R54_24_CASE_MANIFEST_FREEZE_REQUIRED_FIELD_REFS)
    assert manifest["policy_section"] == "R54-5_24_case_manifest_freeze"
    assert manifest["review_session_status"] == "R54_PRECHECK_BLOCKED"
    assert manifest["manifest_status"] == "BLOCKED_BY_R54_4_ENVELOPE"
    assert manifest["r4_envelope_ready_for_manifest_freeze"] is False
    assert manifest["case_count"] == 0
    assert manifest["case_rows"] == []
    assert manifest["controller_manifest_rows"] == []
    assert manifest["reviewer_facing_case_index_rows"] == []
    assert manifest["r54_5_24_case_manifest_freeze_built"] is False
    assert manifest["body_full_packet_generated_here"] is False
    assert manifest["actual_human_review_run_here"] is False
    assert manifest["next_required_step"] == r54.P7_R54_R5_BLOCKED_NEXT_REQUIRED_STEP_REF

    assert r54.assert_p7_r54_24_case_manifest_freeze_bodyfree_contract(manifest) is True
    _assert_body_free_no_promotion(manifest)


def test_r54_r5_ready_freezes_24_case_manifest_with_reviewer_facing_hidden_metadata(tmp_path) -> None:
    manifest = _r5_ready(tmp_path)

    assert manifest["review_session_status"] == "R54_24_CASE_MANIFEST_READY"
    assert manifest["manifest_status"] == "READY_FOR_LOCAL_ONLY_PACKET_GENERATION_REQUEST"
    assert manifest["r4_envelope_ready_for_manifest_freeze"] is True
    assert manifest["matrix_kind"] == "p5_24_case_first_formal_review_matrix"
    assert manifest["required_case_count"] == 24
    assert manifest["case_count"] == 24
    assert len(manifest["case_rows"]) == 24
    assert len(manifest["controller_manifest_rows"]) == 24
    assert len(manifest["reviewer_facing_case_index_rows"]) == 24
    assert manifest["family_case_counts"] == {
        "history_line_eligible_input": 4,
        "standard_state_answer_owned_history": 4,
        "self_understanding_owned_history": 3,
        "uncertainty_support_owned_history": 3,
        "change_future_intention_owned_history": 3,
        "relationship_gratitude_recovery_owned_history": 3,
        "low_information_history_not_eligible": 2,
        "free_tier_history_present_not_allowed": 2,
    }
    assert manifest["owned_history_positive_case_count"] == 20
    assert manifest["boundary_case_count"] == 4
    assert manifest["low_information_boundary_case_count"] == 2
    assert manifest["free_tier_boundary_case_count"] == 2
    assert manifest["minimums_satisfied"] is True
    assert manifest["blind_case_ids_unique"] is True
    assert manifest["case_ref_ids_unique"] is True
    assert manifest["packet_ref_ids_unique"] is True
    assert manifest["blind_case_id_case_ref_separated"] is True
    assert manifest["blind_case_id_packet_ref_separated"] is True
    assert manifest["case_ref_id_packet_ref_separated"] is True
    assert manifest["reviewer_facing_identifier_policy"] == "blind_case_id_only"
    assert manifest["reviewer_facing_family_exposed"] is False
    assert manifest["reviewer_facing_tier_exposed"] is False
    assert manifest["reviewer_facing_case_ref_exposed"] is False
    assert manifest["reviewer_facing_packet_ref_exposed"] is False
    assert manifest["reviewer_facing_expected_result_exposed"] is False
    assert manifest["reviewer_facing_hidden_metadata_exposed"] is False
    assert manifest["controller_keeps_family_tier_expected_refs"] is True
    assert manifest["reviewer_receives_blind_case_id_only"] is True

    reviewer_row = manifest["reviewer_facing_case_index_rows"][0]
    assert set(reviewer_row) == set(r54.P7_R54_REVIEWER_FACING_CASE_INDEX_ROW_FIELD_REFS)
    assert reviewer_row["case_ref_hidden"] is True
    assert reviewer_row["packet_ref_hidden"] is True
    assert reviewer_row["family_hidden"] is True
    assert reviewer_row["tier_hidden"] is True
    assert reviewer_row["expected_result_hidden"] is True
    assert reviewer_row["gate_result_hidden"] is True
    assert reviewer_row["derived_from_body_or_record_hash"] is False

    controller_row = manifest["controller_manifest_rows"][0]
    assert controller_row["reviewer_receives_blind_case_id"] is True
    assert controller_row["reviewer_receives_case_ref_id"] is False
    assert controller_row["reviewer_receives_family"] is False
    assert controller_row["reviewer_receives_subscription_tier"] is False
    assert controller_row["reviewer_receives_expected_result"] is False
    assert controller_row["reviewer_receives_gate_result"] is False

    assert manifest["body_full_packet_materialized_here"] is False
    assert manifest["local_reviewer_payload_materialized_here"] is False
    assert manifest["body_full_packet_generated_here"] is False
    assert manifest["body_full_packets_created_local_only"] is False
    assert manifest["actual_human_review_run_here"] is False
    assert manifest["actual_manual_review_run_here"] is False
    assert manifest["actual_rating_rows_materialized_here"] is False
    assert manifest["actual_question_need_observation_rows_materialized_here"] is False
    assert manifest["actual_disposal_receipt_materialized_here"] is False
    assert manifest["p5_actual_review_still_not_run"] is True
    assert manifest["execution_blocker_ids"] == []
    assert tuple(manifest["implemented_steps"]) == r54.P7_R54_R5_IMPLEMENTED_STEPS
    assert tuple(manifest["not_yet_implemented_steps"]) == r54.P7_R54_R5_NOT_YET_IMPLEMENTED_STEPS
    assert manifest["next_required_step"] == r54.P7_R54_R5_NEXT_REQUIRED_STEP_REF

    _assert_body_free_no_promotion(manifest)


@pytest.mark.parametrize(
    "key,value",
    [
        ("reviewer_facing_family_exposed", True),
        ("reviewer_facing_case_ref_exposed", True),
        ("reviewer_facing_packet_ref_exposed", True),
        ("reviewer_facing_expected_result_exposed", True),
        ("reviewer_facing_hidden_metadata_exposed", True),
        ("body_full_packet_materialized_here", True),
        ("local_reviewer_payload_materialized_here", True),
        ("body_full_packet_generated_here", True),
        ("body_full_packets_created_local_only", True),
        ("actual_human_review_run_here", True),
        ("actual_rating_rows_materialized_here", True),
        ("actual_question_need_observation_rows_materialized_here", True),
        ("p5_human_blind_qa_confirmed_candidate", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
    ],
)
def test_r54_r5_rejects_hidden_metadata_packet_review_or_promotion_mutation(tmp_path, key: str, value: object) -> None:
    material = _r5_ready(tmp_path)
    material[key] = value
    with pytest.raises(ValueError):
        r54.assert_p7_r54_24_case_manifest_freeze_bodyfree_contract(material)


def test_r54_r5_rejects_reviewer_row_exposing_hidden_metadata(tmp_path) -> None:
    material = _r5_ready(tmp_path)
    material["reviewer_facing_case_index_rows"][0] = deepcopy(material["reviewer_facing_case_index_rows"][0])
    material["reviewer_facing_case_index_rows"][0]["family_hidden"] = False
    with pytest.raises(ValueError):
        r54.assert_p7_r54_24_case_manifest_freeze_bodyfree_contract(material)


def test_r54_r5_rejects_blind_case_id_case_ref_collision(tmp_path) -> None:
    material = _r5_ready(tmp_path)
    material["case_rows"][0] = deepcopy(material["case_rows"][0])
    material["case_rows"][0]["blind_case_id"] = material["case_rows"][0]["case_ref_id"]
    with pytest.raises(ValueError):
        r54.assert_p7_r54_24_case_manifest_freeze_bodyfree_contract(material)
