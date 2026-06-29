# -*- coding: utf-8 -*-
"""R54-AHR Post-CR22 actual local review evidence completion EX02-EX03 tests."""

from __future__ import annotations

from copy import deepcopy

import pytest

import emlis_ai_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_20260629 as ex


def _assert_bodyfree_no_touch_nonpromotion(material: dict[str, object]) -> None:
    assert material["body_free"] is True
    for key in ex.P7_R54_AHR_POST_CR22_REQUIRED_FALSE_FLAG_REFS:
        assert material[key] is False, key
    for marker_map_key in ("public_contract", "postcr22_no_touch_contract", "body_free_markers"):
        assert material[marker_map_key]
        assert all(value is False for value in material[marker_map_key].values()), marker_map_key
    for forbidden_key in ex.P7_R54_AHR_POST_CR22_FORBIDDEN_PAYLOAD_KEY_REFS:
        assert forbidden_key not in material, forbidden_key


def _ready_ex02() -> dict[str, object]:
    return ex.build_p7_r54_ahr_post_cr22_ex02_review_session_envelope_actual_source_guard_freeze()


def _ready_ex03() -> dict[str, object]:
    return ex.build_p7_r54_ahr_post_cr22_ex03_local_only_preflight_explicit_allow_packet_request_boundary(
        review_session_envelope_actual_source_guard=_ready_ex02(),
        explicit_allow_ref=ex.P7_R54_AHR_POST_CR22_EX03_DEFAULT_EXPLICIT_ALLOW_REF,
    )


def test_ex02_freezes_review_session_envelope_and_actual_source_guard_without_promoting_rows() -> None:
    material = _ready_ex02()

    assert set(material) == set(ex.P7_R54_AHR_POST_CR22_EX02_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == (
        ex.P7_R54_AHR_POST_CR22_EX02_REVIEW_SESSION_ENVELOPE_ACTUAL_SOURCE_GUARD_FREEZE_SCHEMA_VERSION
    )
    assert material["operation_step_ref"] == ex.P7_R54_AHR_POST_CR22_EX02_STEP_REF
    assert material["review_session_envelope_ready"] is True
    assert material["review_session_state_ref"] == ex.P7_R54_AHR_POST_CR22_REVIEW_SESSION_STATE_NOT_STARTED_REF
    assert material["review_session_id"] == ex.P7_R54_AHR_POST_CR22_DEFAULT_REVIEW_SESSION_ID
    assert material["review_session_id_bodyfree_identifier"] is True
    assert material["review_session_id_has_local_path_shape"] is False
    assert material["actual_source_guard_required"] is True
    assert material["actual_source_guard_ready"] is True
    assert material["actual_source_guard_step_blocker_refs"] == []
    assert tuple(material["allowed_actual_source_refs"]) == ex.P7_R54_AHR_POST_CR22_ALLOWED_ACTUAL_SOURCE_REFS
    assert tuple(material["forbidden_actual_source_refs"]) == ex.P7_R54_AHR_POST_CR22_FORBIDDEN_ACTUAL_SOURCE_REFS
    assert material["actual_source_guard_blocks_helper_default_rows"] is True
    assert material["actual_source_guard_blocks_unit_test_rows"] is True
    assert material["actual_source_guard_blocks_synthetic_rows"] is True
    assert material["actual_source_guard_blocks_historical_rows"] is True
    assert material["actual_source_guard_requires_person_read_receipt_later"] is True
    assert material["actual_rows_source_guard_passed"] is False
    assert material["actual_rows_intaked_here"] is False
    for key in ex.P7_R54_AHR_POST_CR22_EX02_REQUIRED_SOURCE_GUARD_FALSE_FIELD_REFS:
        assert material[key] is False, key
    assert material["actual_review_basis_ref"] == "current_received_snapshot_264_85_258_171"
    assert material["local_received_zip_refs_are_actual_review_basis"] is False
    assert tuple(material["implemented_steps"]) == ex.P7_R54_AHR_POST_CR22_EX02_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ex.P7_R54_AHR_POST_CR22_EX02_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == ex.P7_R54_AHR_POST_CR22_EX03_STEP_REF
    _assert_bodyfree_no_touch_nonpromotion(material)
    assert ex.assert_p7_r54_ahr_post_cr22_ex02_review_session_envelope_actual_source_guard_freeze_contract(material) is True


def test_ex02_keeps_source_guard_lists_separated_and_bodyfree() -> None:
    material = _ready_ex02()

    assert set(material["allowed_actual_source_refs"]).isdisjoint(material["forbidden_actual_source_refs"])
    assert "actual_person_local_only_review_operation_receipt" in material["allowed_actual_source_refs"]
    assert "actual_person_selection_only_rows_local_review" in material["allowed_actual_source_refs"]
    assert "actual_local_body_full_packet_generation_receipt_bodyfree" in material["allowed_actual_source_refs"]
    assert "actual_local_disposal_receipt_bodyfree" in material["allowed_actual_source_refs"]
    assert "helper_default_fixture_rows" in material["forbidden_actual_source_refs"]
    assert "unit_test_contract_rows" in material["forbidden_actual_source_refs"]
    assert "synthetic_bodyfree_rows" in material["forbidden_actual_source_refs"]
    assert "ai_inferred_review_rows" in material["forbidden_actual_source_refs"]
    assert "rows_without_person_read_receipt" in material["forbidden_actual_source_refs"]
    assert ex.assert_p7_r54_ahr_post_cr22_ex02_review_session_envelope_actual_source_guard_freeze_contract(material) is True


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("helper_default_rows_allowed_as_actual", True),
        ("unit_test_rows_allowed_as_actual", True),
        ("synthetic_rows_allowed_as_actual", True),
        ("historical_rows_allowed_as_actual", True),
        ("ai_inferred_rows_allowed_as_actual", True),
        ("rows_without_person_read_receipt_allowed_as_actual", True),
        ("actual_source_guard_materializes_actual_rows_here", True),
        ("actual_source_guard_runs_actual_human_review_here", True),
        ("actual_rows_source_guard_passed", True),
        ("actual_rows_intaked_here", True),
        ("actual_review_evidence_complete", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("next_required_step", "mutated_next_step"),
    ),
)
def test_ex02_contract_rejects_source_guard_row_or_promotion_mutations(field: str, value: object) -> None:
    material = deepcopy(_ready_ex02())
    material[field] = value

    with pytest.raises(ValueError):
        ex.assert_p7_r54_ahr_post_cr22_ex02_review_session_envelope_actual_source_guard_freeze_contract(material)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("allowed_actual_source_refs", ["helper_default_fixture_rows"]),
        ("allowed_actual_source_ref_count", 999),
        ("forbidden_actual_source_refs", ["actual_person_selection_only_rows_local_review"]),
        ("forbidden_actual_source_ref_count", 999),
        ("review_session_state_ref", ex.P7_R54_AHR_POST_CR22_REVIEW_SESSION_STATE_PREFLIGHT_READY_REF),
        ("review_session_id_has_local_path_shape", True),
    ),
)
def test_ex02_contract_rejects_actual_source_or_session_envelope_mutations(field: str, value: object) -> None:
    material = deepcopy(_ready_ex02())
    material[field] = value

    with pytest.raises(ValueError):
        ex.assert_p7_r54_ahr_post_cr22_ex02_review_session_envelope_actual_source_guard_freeze_contract(material)


def test_ex03_blocks_without_explicit_allow_by_default_and_does_not_materialize_packet_request() -> None:
    ex02 = _ready_ex02()
    material = ex.build_p7_r54_ahr_post_cr22_ex03_local_only_preflight_explicit_allow_packet_request_boundary(
        review_session_envelope_actual_source_guard=ex02,
    )

    assert set(material) == set(ex.P7_R54_AHR_POST_CR22_EX03_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == (
        ex.P7_R54_AHR_POST_CR22_EX03_LOCAL_ONLY_PREFLIGHT_EXPLICIT_ALLOW_PACKET_REQUEST_BOUNDARY_SCHEMA_VERSION
    )
    assert material["operation_step_ref"] == ex.P7_R54_AHR_POST_CR22_EX03_STEP_REF
    assert material["local_only_preflight_ready"] is False
    assert material["body_full_packet_request_boundary_ready"] is False
    assert material["body_full_packet_request_ref"] == ""
    assert material["body_full_packet_request_ref_present"] is False
    assert material["explicit_allow_ref_present"] is False
    assert "explicit_allow_ref_missing" in material["local_only_preflight_blocker_refs"]
    assert tuple(material["implemented_steps"]) == ex.P7_R54_AHR_POST_CR22_EX02_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ex.P7_R54_AHR_POST_CR22_EX02_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == ex.P7_R54_AHR_POST_CR22_EX03_DEFAULT_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert material["body_full_packet_generation_started_here"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["actual_human_review_newly_run_here"] is False
    assert material["actual_review_evidence_complete"] is False
    _assert_bodyfree_no_touch_nonpromotion(material)
    assert ex.assert_p7_r54_ahr_post_cr22_ex03_local_only_preflight_explicit_allow_packet_request_boundary_contract(material) is True


def test_ex03_ready_with_explicit_allow_creates_only_bodyfree_packet_request_boundary() -> None:
    material = _ready_ex03()

    assert set(material) == set(ex.P7_R54_AHR_POST_CR22_EX03_REQUIRED_FIELD_REFS)
    assert material["local_only_preflight_status_ref"] == ex.P7_R54_AHR_POST_CR22_EX03_PREFLIGHT_READY_STATUS_REF
    assert material["local_only_preflight_ready"] is True
    assert material["local_only_preflight_blocker_refs"] == []
    assert material["local_only"] is True
    assert material["must_not_export"] is True
    assert material["local_review_root_ref"] == ex.P7_R54_AHR_POST_CR22_EX03_DEFAULT_LOCAL_REVIEW_ROOT_REF
    assert material["local_review_root_ref_is_bodyfree_ref"] is True
    assert material["local_review_root_ref_has_local_path_shape"] is False
    assert material["explicit_allow_ref"] == ex.P7_R54_AHR_POST_CR22_EX03_DEFAULT_EXPLICIT_ALLOW_REF
    assert material["explicit_allow_ref_present"] is True
    assert material["retention_policy_ref_present"] is True
    assert material["disposal_policy_ref_present"] is True
    assert material["export_denylist_policy_ref_present"] is True
    assert material["body_full_packet_export_allowed"] is False
    assert material["body_free_summary_export_allowed"] is True
    assert material["body_full_packet_request_boundary_ready"] is True
    assert material["body_full_packet_request_allowed_by_preflight"] is True
    assert material["body_full_packet_request_ref"] == ex.P7_R54_AHR_POST_CR22_EX03_DEFAULT_PACKET_REQUEST_REF
    assert material["body_full_packet_request_ref_present"] is True
    assert material["body_full_packet_request_materialized_bodyfree_only"] is True
    assert material["body_full_packet_generation_started_here"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["body_full_packet_content_included"] is False
    assert material["local_absolute_path_included"] is False
    assert material["body_hash_included"] is False
    assert material["terminal_output_body_included"] is False
    assert tuple(material["implemented_steps"]) == ex.P7_R54_AHR_POST_CR22_EX03_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ex.P7_R54_AHR_POST_CR22_EX03_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == ex.P7_R54_AHR_POST_CR22_EX04_STEP_REF
    _assert_bodyfree_no_touch_nonpromotion(material)
    assert ex.assert_p7_r54_ahr_post_cr22_ex03_local_only_preflight_explicit_allow_packet_request_boundary_contract(material) is True


def test_ex03_blocks_policy_export_and_local_only_mutations_without_promotion() -> None:
    material = ex.build_p7_r54_ahr_post_cr22_ex03_local_only_preflight_explicit_allow_packet_request_boundary(
        review_session_envelope_actual_source_guard=_ready_ex02(),
        local_only=False,
        must_not_export=False,
        explicit_allow_ref=ex.P7_R54_AHR_POST_CR22_EX03_DEFAULT_EXPLICIT_ALLOW_REF,
        retention_policy_ref="",
        disposal_policy_ref="",
        export_denylist_policy_ref="",
        body_full_packet_export_allowed=True,
    )

    assert material["local_only_preflight_ready"] is False
    assert "local_only_not_confirmed" in material["local_only_preflight_blocker_refs"]
    assert "must_not_export_not_confirmed" in material["local_only_preflight_blocker_refs"]
    assert "retention_policy_ref_missing" in material["local_only_preflight_blocker_refs"]
    assert "disposal_policy_ref_missing" in material["local_only_preflight_blocker_refs"]
    assert "export_denylist_policy_ref_missing" in material["local_only_preflight_blocker_refs"]
    assert "body_full_packet_export_allowed" in material["local_only_preflight_blocker_refs"]
    assert material["body_full_packet_request_ref_present"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert ex.assert_p7_r54_ahr_post_cr22_ex03_local_only_preflight_explicit_allow_packet_request_boundary_contract(material) is True


def test_ex03_rejects_path_shaped_local_review_root_without_exporting_actual_path() -> None:
    material = ex.build_p7_r54_ahr_post_cr22_ex03_local_only_preflight_explicit_allow_packet_request_boundary(
        review_session_envelope_actual_source_guard=_ready_ex02(),
        explicit_allow_ref=ex.P7_R54_AHR_POST_CR22_EX03_DEFAULT_EXPLICIT_ALLOW_REF,
        local_review_root_ref="/tmp/secret_local_review_root",
    )

    assert material["local_only_preflight_ready"] is False
    assert material["local_review_root_ref"] == ex.P7_R54_AHR_POST_CR22_EX03_REJECTED_LOCAL_REVIEW_ROOT_PATH_SHAPE_REF
    assert material["local_review_root_ref_has_local_path_shape"] is True
    assert "secret_local_review_root" not in repr(material)
    assert "local_review_root_ref_must_be_bodyfree_ref_not_path" in material["local_only_preflight_blocker_refs"]
    assert material["local_absolute_path_included"] is False
    assert material["body_full_packet_request_ref_present"] is False
    assert ex.assert_p7_r54_ahr_post_cr22_ex03_local_only_preflight_explicit_allow_packet_request_boundary_contract(material) is True


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("body_full_packet_generation_started_here", True),
        ("body_full_packet_generated_here", True),
        ("body_full_packet_content_included", True),
        ("local_absolute_path_included", True),
        ("body_hash_included", True),
        ("actual_human_review_complete", True),
        ("actual_review_evidence_complete", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("next_required_step", "mutated_next_step"),
    ),
)
def test_ex03_contract_rejects_packet_generation_review_or_promotion_mutations(field: str, value: object) -> None:
    material = deepcopy(_ready_ex03())
    material[field] = value

    with pytest.raises(ValueError):
        ex.assert_p7_r54_ahr_post_cr22_ex03_local_only_preflight_explicit_allow_packet_request_boundary_contract(material)


def test_ex02_and_ex03_alias_functions_match_primary_builders_and_contracts() -> None:
    ex02_primary = _ready_ex02()
    ex02_alias = (
        ex.build_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_review_session_envelope_actual_source_guard_freeze_bodyfree()
    )
    assert ex02_alias == ex02_primary
    assert (
        ex.assert_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_review_session_envelope_actual_source_guard_freeze_bodyfree_contract(
            ex02_alias
        )
        is True
    )

    ex03_primary = _ready_ex03()
    ex03_alias = (
        ex.build_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_local_only_preflight_explicit_allow_packet_request_boundary_bodyfree(
            review_session_envelope_actual_source_guard=ex02_primary,
            explicit_allow_ref=ex.P7_R54_AHR_POST_CR22_EX03_DEFAULT_EXPLICIT_ALLOW_REF,
        )
    )
    assert ex03_alias == ex03_primary
    assert (
        ex.assert_p7_r54_ahr_post_cr22_actual_local_review_execution_evidence_completion_local_only_preflight_explicit_allow_packet_request_boundary_bodyfree_contract(
            ex03_alias
        )
        is True
    )
