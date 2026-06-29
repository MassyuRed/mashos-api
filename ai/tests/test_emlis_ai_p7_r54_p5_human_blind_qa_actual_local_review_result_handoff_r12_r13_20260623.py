# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import uuid
from copy import deepcopy

import pytest

import emlis_ai_p7_r54_p5_human_blind_qa_actual_local_review_result_handoff as r54


FORBIDDEN_BODY_TOKENS = (
    '"raw_input":',
    '"comment_text":',
    '"returned_emlis_surface":',
    '"current_input_review_surface":',
    '"bounded_owned_history_review_surface":',
    '"reviewer_free_text":',
    '"reviewer_notes":',
    '"question_text":',
    '"draft_question_text":',
    '"local_absolute_path":',
    '"body_content_hash":',
    '"packet_content_hash":',
    '"terminal_output": "',
    '"stdout":',
    '"stderr":',
)
FORBIDDEN_PROMOTION_TRUE_TOKENS = (
    '"release_allowed": true',
    '"p7_complete": true',
    '"p8_start_allowed": true',
    '"p6_limited_human_readfeel_start_allowed": true',
    '"question_trigger_logic_implemented": true',
    '"question_api_implemented": true',
    '"question_db_schema_implemented": true',
    '"question_rn_ui_implemented": true',
    '"question_response_key_implemented": true',
    '"api_db_rn_response_key_changed_here": true',
    '"runtime_changed_here": true',
    '"actual_human_review_run_here": true',
    '"actual_manual_review_run_here": true',
    '"body_full_packet_generated_here": true',
    '"actual_body_full_packet_generated_here": true',
    '"actual_disposal_receipt_materialized_here": true',
    '"p5_human_blind_qa_confirmed_candidate": true',
)


def _assert_body_free_no_runtime_promotion(material: dict[str, object]) -> None:
    dumped = json.dumps(material, ensure_ascii=False, sort_keys=True).lower()
    for forbidden in FORBIDDEN_BODY_TOKENS:
        assert forbidden not in dumped
    for forbidden in FORBIDDEN_PROMOTION_TRUE_TOKENS:
        assert forbidden not in dumped


def _ready_root(tmp_path) -> str:
    root = tmp_path / f"r54_external_local_review_root_{uuid.uuid4().hex}"
    root.mkdir()
    return str(root)


def _r3_ready(tmp_path) -> dict[str, object]:
    return r54.build_p7_r54_local_only_actual_review_preflight_bodyfree(
        validation_evidence_intake=r54.build_p7_r54_validation_evidence_intake_bodyfree(),
        local_review_root=_ready_root(tmp_path),
        explicit_allow_token=r54.P7_R54_EXPLICIT_LOCAL_REVIEW_ALLOW_TOKEN_REF,
        purge_plan=r54.build_p7_r54_default_local_only_purge_plan_bodyfree(),
        export_candidate_refs=("bodyfree/result_handoff.json",),
    )


def _r5_ready(tmp_path) -> dict[str, object]:
    envelope = r54.build_p7_r54_actual_review_session_envelope_bodyfree(
        local_only_actual_review_preflight=_r3_ready(tmp_path),
    )
    manifest = r54.build_p7_r54_24_case_manifest_freeze_bodyfree(actual_review_session_envelope=envelope)
    assert manifest["manifest_status"] == "READY_FOR_LOCAL_ONLY_PACKET_GENERATION_REQUEST"
    return manifest


def _r8_ready(tmp_path) -> dict[str, object]:
    manifest = _r5_ready(tmp_path)
    request = r54.build_p7_r54_local_only_body_full_packet_generation_request_bodyfree(case_manifest_freeze=manifest)
    completion_rows = [
        r54.build_p7_r54_packet_completion_scan_row_bodyfree(
            blind_case_id=row["blind_case_id"],
            packet_ref_id=row["packet_ref_id"],
            index=index,
        )
        for index, row in enumerate(request["packet_generation_request_rows"], start=1)
    ]
    scan = r54.build_p7_r54_packet_completeness_export_denylist_scan_bodyfree(
        packet_generation_request=request,
        packet_completion_rows=completion_rows,
        export_candidate_refs=("bodyfree/result_handoff.json", "bodyfree/disposal_receipt.json"),
    )
    form = r54.build_p7_r54_reviewer_instruction_rating_form_freeze_bodyfree(packet_completeness_export_denylist_scan=scan)
    assert form["instruction_form_status"] == "READY_FOR_ACTUAL_HUMAN_REVIEW_OPERATION_STATE_CAPTURE"
    return form


def _r9_capture_ready(tmp_path) -> dict[str, object]:
    state = r54.build_p7_r54_actual_human_review_operation_state_capture_bodyfree(
        reviewer_instruction_rating_form_freeze=_r8_ready(tmp_path),
        review_operation_state_ref="review_completed_pending_sanitized_capture",
        reviewer_selection_count=24,
        reviewer_selection_source_ref="external_local_only_review_form_selection_count_only",
    )
    assert state["operation_state_capture_status"] == "READY_FOR_SANITIZED_ACTUAL_REVIEW_RESULT_CAPTURE"
    return state


def _subscription_boundary(row: dict[str, object]) -> str:
    return "free_history_not_allowed" if row["subscription_tier_ref"] == "free" else "plus_or_premium_history_allowed"


def _review_rows_from_manifest(manifest: dict[str, object]) -> list[dict[str, object]]:
    return [
        r54.build_p7_r54_sanitized_review_result_row_bodyfree(
            blind_case_id=row["blind_case_id"],
            case_ref_id=row["case_ref_id"],
            packet_ref_id=row["packet_ref_id"],
            case_family_ref=row["family"],
            case_role_ref=row["case_role"],
            subscription_boundary_ref=_subscription_boundary(row),
        )
        for row in manifest["controller_manifest_rows"]
    ]


def _r10_ready(tmp_path, rows: list[dict[str, object]] | None = None) -> dict[str, object]:
    manifest = _r5_ready(tmp_path)
    capture = r54.build_p7_r54_sanitized_actual_review_result_capture_bodyfree(
        actual_human_review_operation_state_capture=_r9_capture_ready(tmp_path),
        case_manifest_freeze=manifest,
        sanitized_review_result_rows=rows if rows is not None else _review_rows_from_manifest(manifest),
    )
    assert capture["capture_status"] == "READY_FOR_RATING_ROW_NORMALIZATION"
    return capture


def _r11_ready(tmp_path, capture: dict[str, object] | None = None) -> dict[str, object]:
    normalization = r54.build_p7_r54_rating_row_normalization_bodyfree(
        sanitized_actual_review_result_capture=capture or _r10_ready(tmp_path),
    )
    assert normalization["rating_row_normalizer_status"] == "READY_FOR_READFEEL_BLOCKER_EXECUTION_BLOCKER_INGESTION"
    return normalization


def _r12_ready(tmp_path, r11: dict[str, object] | None = None) -> dict[str, object]:
    ingestion = r54.build_p7_r54_readfeel_blocker_execution_blocker_ingestion_bodyfree(
        rating_row_normalization=r11 or _r11_ready(tmp_path),
    )
    assert ingestion["blocker_ingestion_status"] == "READY_FOR_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION"
    return ingestion


def test_r54_r12_default_is_blocked_without_r11_rating_rows() -> None:
    ingestion = r54.build_p7_r54_readfeel_blocker_execution_blocker_ingestion_bodyfree()

    assert set(ingestion) == set(r54.P7_R54_READFEEL_EXECUTION_BLOCKER_INGESTION_REQUIRED_FIELD_REFS)
    assert ingestion["schema_version"] == r54.P7_R54_READFEEL_EXECUTION_BLOCKER_INGESTION_SCHEMA_VERSION
    assert ingestion["policy_section"] == r54.P7_R54_R12_STEP_REF
    assert ingestion["blocker_ingestion_status"] == "BLOCKED_BY_R54_11_RATING_ROW_NORMALIZATION"
    assert ingestion["r11_rating_rows_ready_for_blocker_ingestion"] is False
    assert ingestion["rating_row_count"] == 0
    assert ingestion["readfeel_blocker_rows"] == []
    assert ingestion["execution_blocker_rows"] == []
    assert ingestion["actual_blocker_rows_materialized_here"] is False
    assert ingestion["actual_execution_blocker_rows_materialized_here"] is False
    assert ingestion["actual_question_need_observation_rows_materialized_here"] is False
    assert "r54_rating_row_normalization_not_ready_for_blocker_ingestion" in ingestion["execution_blocker_ids"]
    assert ingestion["next_required_step"] == r54.P7_R54_R12_BLOCKED_NEXT_REQUIRED_STEP_REF

    assert r54.assert_p7_r54_readfeel_blocker_execution_blocker_ingestion_bodyfree_contract(ingestion) is True
    _assert_body_free_no_runtime_promotion(ingestion)


def test_r54_r12_ready_separates_readfeel_and_execution_blockers_without_p5_promotion(tmp_path) -> None:
    manifest = _r5_ready(tmp_path)
    rows = _review_rows_from_manifest(manifest)
    first = manifest["controller_manifest_rows"][0]
    second = manifest["controller_manifest_rows"][1]
    rows[0] = r54.build_p7_r54_sanitized_review_result_row_bodyfree(
        blind_case_id=first["blind_case_id"],
        case_ref_id=first["case_ref_id"],
        packet_ref_id=first["packet_ref_id"],
        case_family_ref=first["family"],
        case_role_ref=first["case_role"],
        subscription_boundary_ref=_subscription_boundary(first),
        verdict="REPAIR_REQUIRED",
        readfeel_blocker_ids=("p5_history_connection_too_generic",),
    )
    rows[1] = r54.build_p7_r54_sanitized_review_result_row_bodyfree(
        blind_case_id=second["blind_case_id"],
        case_ref_id=second["case_ref_id"],
        packet_ref_id=second["packet_ref_id"],
        case_family_ref=second["family"],
        case_role_ref=second["case_role"],
        subscription_boundary_ref=_subscription_boundary(second),
        verdict="REPAIR_REQUIRED",
        execution_blocker_ids=("r54_sanitized_review_result_row_body_leak_detected",),
    )
    capture = _r10_ready(tmp_path, rows=rows)
    r11 = _r11_ready(tmp_path, capture=capture)
    ingestion = r54.build_p7_r54_readfeel_blocker_execution_blocker_ingestion_bodyfree(rating_row_normalization=r11)

    assert ingestion["blocker_ingestion_status"] == "READY_FOR_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION"
    assert ingestion["readfeel_blocker_row_count"] == 1
    assert ingestion["execution_blocker_row_count"] == 1
    assert ingestion["open_readfeel_blocker_count"] == 1
    assert ingestion["open_execution_blocker_count"] == 1
    assert ingestion["readfeel_and_execution_blockers_separated"] is True
    assert ingestion["execution_blockers_do_not_assign_readfeel_verdict"] is True
    assert ingestion["execution_blocker_open_blocks_p5_confirmed_candidate"] is True
    assert ingestion["p5_confirmed_candidate_blocked_by_open_execution_blockers"] is True
    assert ingestion["actual_rating_rows_materialized_here"] is True
    assert ingestion["actual_blocker_rows_materialized_here"] is True
    assert ingestion["actual_execution_blocker_rows_materialized_here"] is True
    assert ingestion["actual_human_review_run_here"] is False
    assert ingestion["p5_human_blind_qa_confirmed_candidate"] is False
    assert ingestion["p8_start_allowed"] is False
    assert ingestion["execution_blocker_ids"] == []
    assert ingestion["next_required_step"] == r54.P7_R54_R12_NEXT_REQUIRED_STEP_REF

    assert r54.assert_p7_r54_readfeel_blocker_execution_blocker_ingestion_bodyfree_contract(ingestion) is True
    _assert_body_free_no_runtime_promotion(ingestion)


def test_r54_r13_default_is_blocked_without_r12_and_r10() -> None:
    normalization = r54.build_p7_r54_question_need_observation_row_normalization_bodyfree()

    assert set(normalization) == set(r54.P7_R54_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION_REQUIRED_FIELD_REFS)
    assert normalization["schema_version"] == r54.P7_R54_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION_SCHEMA_VERSION
    assert normalization["policy_section"] == r54.P7_R54_R13_STEP_REF
    assert normalization["question_observation_normalizer_status"] == "BLOCKED_BY_R54_12_OR_R54_10_PRECHECK"
    assert normalization["r12_ready_for_question_need_observation_row_normalization"] is False
    assert normalization["r10_capture_ready_for_question_observation"] is False
    assert normalization["question_observation_row_count"] == 0
    assert normalization["question_need_observation_rows"] == []
    assert normalization["actual_question_need_observation_rows_materialized_here"] is False
    assert normalization["question_text_or_draft_text_saved_here"] is False
    assert normalization["execution_blocker_ids"]
    assert normalization["next_required_step"] == r54.P7_R54_R13_BLOCKED_NEXT_REQUIRED_STEP_REF

    assert r54.assert_p7_r54_question_need_observation_row_normalization_bodyfree_contract(normalization) is True
    _assert_body_free_no_runtime_promotion(normalization)


def test_r54_r13_ready_normalizes_24_bodyfree_question_observation_rows_without_question_text(tmp_path) -> None:
    capture = _r10_ready(tmp_path)
    r11 = _r11_ready(tmp_path, capture=capture)
    ingestion = _r12_ready(tmp_path, r11=r11)
    normalization = r54.build_p7_r54_question_need_observation_row_normalization_bodyfree(
        readfeel_blocker_execution_blocker_ingestion=ingestion,
        sanitized_actual_review_result_capture=capture,
    )

    assert normalization["question_observation_normalizer_status"] == "READY_FOR_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD"
    assert normalization["review_session_status"] == "R54_QUESTION_NEED_OBSERVATION_ROWS_NORMALIZED_BODYFREE"
    assert normalization["r12_ready_for_question_need_observation_row_normalization"] is True
    assert normalization["r10_capture_ready_for_question_observation"] is True
    assert normalization["question_observation_row_count"] == 24
    assert normalization["row_case_ref_sets_match_review_capture"] is True
    assert normalization["row_case_ref_sets_match_rating_rows"] is True
    assert normalization["all_required_question_need_observation_rows_present"] is True
    assert normalization["primary_class_ambiguity_one_question_fit_are_canonical_refs"] is True
    assert normalization["question_text_absent_for_all_rows"] is True
    assert normalization["draft_question_text_absent_for_all_rows"] is True
    assert normalization["reviewer_free_text_absent_for_all_rows"] is True
    assert normalization["raw_input_absent_for_all_rows"] is True
    assert normalization["returned_surface_absent_for_all_rows"] is True
    assert normalization["local_path_absent_for_all_rows"] is True
    assert normalization["body_hash_absent_for_all_rows"] is True
    assert normalization["question_api_implemented"] is False
    assert normalization["question_db_schema_implemented"] is False
    assert normalization["question_rn_ui_implemented"] is False
    assert normalization["question_response_key_implemented"] is False
    assert normalization["question_trigger_logic_implemented"] is False
    assert normalization["actual_human_review_run_here"] is False
    assert normalization["actual_manual_review_run_here"] is False
    assert normalization["actual_rating_rows_materialized_here"] is True
    assert normalization["actual_blocker_rows_materialized_here"] is True
    assert normalization["actual_execution_blocker_rows_materialized_here"] is True
    assert normalization["actual_question_need_observation_rows_materialized_here"] is True
    assert normalization["actual_question_need_observation_summary_materialized_here"] is False
    assert normalization["p5_actual_review_still_not_run_by_helper"] is True
    assert normalization["execution_blocker_ids"] == []
    assert normalization["r54_13_question_need_observation_row_normalization_built"] is True
    assert tuple(normalization["implemented_steps"]) == r54.P7_R54_R13_IMPLEMENTED_STEPS
    assert tuple(normalization["not_yet_implemented_steps"]) == r54.P7_R54_R13_NOT_YET_IMPLEMENTED_STEPS
    assert normalization["next_required_step"] == r54.P7_R54_R13_NEXT_REQUIRED_STEP_REF

    first = normalization["question_need_observation_rows"][0]
    assert set(first) == set(r54.P7_R54_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_REQUIRED_FIELD_REFS)
    assert first["body_free"] is True
    assert first["question_text_included"] is False
    assert first["draft_question_text_included"] is False
    assert first["reviewer_free_text_included"] is False

    assert r54.assert_p7_r54_question_need_observation_row_normalization_bodyfree_contract(normalization) is True
    _assert_body_free_no_runtime_promotion(normalization)


def test_r54_r13_plus_question_candidate_is_material_only_and_does_not_start_p8(tmp_path) -> None:
    manifest = _r5_ready(tmp_path)
    rows = _review_rows_from_manifest(manifest)
    first = manifest["controller_manifest_rows"][0]
    rows[0] = r54.build_p7_r54_sanitized_review_result_row_bodyfree(
        blind_case_id=first["blind_case_id"],
        case_ref_id=first["case_ref_id"],
        packet_ref_id=first["packet_ref_id"],
        case_family_ref=first["family"],
        case_role_ref=first["case_role"],
        subscription_boundary_ref=_subscription_boundary(first),
        question_need_primary_class="plus_single_question_candidate_later",
        ambiguity_kind_refs=("missing_target",),
        one_question_fit_ref="fits_one_question",
        repair_required_refs=("no_repair_required",),
    )
    capture = _r10_ready(tmp_path, rows=rows)
    ingestion = _r12_ready(tmp_path, r11=_r11_ready(tmp_path, capture=capture))
    normalization = r54.build_p7_r54_question_need_observation_row_normalization_bodyfree(
        readfeel_blocker_execution_blocker_ingestion=ingestion,
        sanitized_actual_review_result_capture=capture,
    )

    assert normalization["question_need_primary_class_counts"]["plus_single_question_candidate_later"] == 1
    assert normalization["ambiguity_kind_counts"]["missing_target"] == 1
    assert normalization["one_question_fit_counts"]["fits_one_question"] == 1
    assert normalization["plan_candidate_flag_counts"]["plus_single_question_candidate_later"] == 1
    assert normalization["plan_candidate_flag_counts"]["p8_design_material_candidate"] >= 1
    assert normalization["p8_material_candidate_row_count"] == 1
    assert normalization["p8_start_allowed"] is False
    assert normalization["question_api_implemented"] is False
    assert normalization["question_text_or_draft_text_saved_here"] is False
    assert normalization["p5_weakness_not_hidden_by_question_candidates_here"] is True

    assert r54.assert_p7_r54_question_need_observation_row_normalization_bodyfree_contract(normalization) is True
    _assert_body_free_no_runtime_promotion(normalization)


def test_r54_r13_not_question_repair_required_is_not_p8_material(tmp_path) -> None:
    manifest = _r5_ready(tmp_path)
    rows = _review_rows_from_manifest(manifest)
    first = manifest["controller_manifest_rows"][0]
    rows[0] = r54.build_p7_r54_sanitized_review_result_row_bodyfree(
        blind_case_id=first["blind_case_id"],
        case_ref_id=first["case_ref_id"],
        packet_ref_id=first["packet_ref_id"],
        case_family_ref=first["family"],
        case_role_ref=first["case_role"],
        subscription_boundary_ref=_subscription_boundary(first),
        verdict="REPAIR_REQUIRED",
        readfeel_blocker_ids=("p5_history_connection_too_generic",),
        question_need_primary_class="not_question_p5_surface_repair_required",
        ambiguity_kind_refs=("history_connection_basis_unclear",),
        one_question_fit_ref="repair_required_not_question",
        repair_required_refs=("p5_surface_repair_required",),
    )
    capture = _r10_ready(tmp_path, rows=rows)
    ingestion = _r12_ready(tmp_path, r11=_r11_ready(tmp_path, capture=capture))
    normalization = r54.build_p7_r54_question_need_observation_row_normalization_bodyfree(
        readfeel_blocker_execution_blocker_ingestion=ingestion,
        sanitized_actual_review_result_capture=capture,
    )

    assert normalization["question_need_primary_class_counts"]["not_question_p5_surface_repair_required"] == 1
    assert normalization["repair_required_counts"]["p5_surface_repair_required"] == 1
    assert normalization["not_question_repair_required_count"] == 1
    assert normalization["p8_material_candidate_row_count"] == 0
    assert normalization["not_question_repair_rows_misclassified_as_p8_material"] is False
    assert normalization["plan_candidate_flag_counts"]["p5_repair_return_not_p8_material"] == 1
    assert normalization["question_need_observation_rows"][0]["p8_material_candidate_allowed"] is False
    assert normalization["p8_start_allowed"] is False

    assert r54.assert_p7_r54_question_need_observation_row_normalization_bodyfree_contract(normalization) is True
    _assert_body_free_no_runtime_promotion(normalization)


@pytest.mark.parametrize(
    "key,value",
    [
        ("question_text_included_allowed", True),
        ("draft_question_text_included_allowed", True),
        ("reviewer_free_text_included_allowed", True),
        ("raw_input_allowed", True),
        ("returned_surface_allowed", True),
        ("local_path_allowed", True),
        ("body_hash_allowed", True),
        ("p8_question_implementation_spec_finalized_here", True),
        ("question_trigger_logic_implemented", True),
        ("question_trigger_logic_implemented_here", True),
        ("question_api_implemented", True),
        ("question_db_schema_implemented", True),
        ("question_rn_ui_implemented", True),
        ("question_response_key_implemented", True),
        ("question_storage_schema_implemented", True),
        ("question_text_or_draft_text_saved_here", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("api_db_rn_response_key_changed_here", True),
        ("runtime_changed_here", True),
        ("actual_human_review_run_here", True),
        ("actual_manual_review_run_here", True),
    ],
)
def test_r54_r13_rejects_question_text_question_implementation_body_leak_review_run_or_release_promotion(tmp_path, key: str, value: object) -> None:
    capture = _r10_ready(tmp_path)
    normalizer = r54.build_p7_r54_question_need_observation_row_normalization_bodyfree(
        readfeel_blocker_execution_blocker_ingestion=_r12_ready(tmp_path, r11=_r11_ready(tmp_path, capture=capture)),
        sanitized_actual_review_result_capture=capture,
    )
    normalizer[key] = value
    with pytest.raises(ValueError):
        r54.assert_p7_r54_question_need_observation_row_normalization_bodyfree_contract(normalizer)


def test_r54_r13_rejects_not_question_repair_row_misclassified_as_p8_material(tmp_path) -> None:
    manifest = _r5_ready(tmp_path)
    first = manifest["controller_manifest_rows"][0]
    row = r54.build_p7_r54_sanitized_review_result_row_bodyfree(
        blind_case_id=first["blind_case_id"],
        case_ref_id=first["case_ref_id"],
        packet_ref_id=first["packet_ref_id"],
        case_family_ref=first["family"],
        case_role_ref=first["case_role"],
        subscription_boundary_ref=_subscription_boundary(first),
        question_need_primary_class="not_question_p5_surface_repair_required",
        one_question_fit_ref="repair_required_not_question",
        repair_required_refs=("p5_surface_repair_required",),
    )
    qrow = r54.build_p7_r54_question_need_observation_row_bodyfree(sanitized_review_result_row=row)
    qrow = deepcopy(qrow)
    qrow["p8_material_candidate_allowed"] = True
    with pytest.raises(ValueError):
        r54.assert_p7_r54_question_need_observation_row_bodyfree_contract(qrow)
