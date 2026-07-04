# -*- coding: utf-8 -*-
"""R54-AHR Post-ALR12 explicit local-only review start/retry ELR-OP16/OP17 tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_20260703 as elr
import emlis_ai_p7_r54_ahr_post_dmh18_downstream_manual_decision_triage_20260703 as dmd
from test_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op06_op07_20260703 import (
    _op02_accepted,
    _op03_ready,
    _op04_ready,
    _op05_accepted,
    _op06_passed,
)
from test_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op08_op09_20260703 import (
    _op07_ready,
    _op08_completed,
)
from test_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op10_op11_20260703 import (
    _op09_accepted,
    _op10_accepted,
)
from test_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op12_op13_20260703 import (
    _op11_normalized,
    _op12_normalized,
)
from test_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op14_op15_20260703 import (
    _op13_passed,
    _op14_accepted,
    _op15_passed,
)

_OP16_COMPLETE_CACHE: dict[str, object] | None = None
_OP17_READY_CACHE: dict[str, object] | None = None


def _complete_evidence_materials() -> list[dict[str, object]]:
    return [
        _op02_accepted(),
        _op03_ready(),
        _op04_ready(),
        _op05_accepted(),
        _op06_passed(),
        _op07_ready(),
        _op08_completed(),
        _op09_accepted(),
        _op10_accepted(),
        _op11_normalized(),
        _op12_normalized(),
        _op13_passed(),
        _op14_accepted(),
    ]


def _op16_complete() -> dict[str, object]:
    global _OP16_COMPLETE_CACHE
    if _OP16_COMPLETE_CACHE is None:
        material = elr.build_p7_r54_ahr_post_alr12_elr_op16_actual_review_evidence_complete_predicate(
            op15_final_no_leak_no_touch_validation=_op15_passed(),
            complete_evidence_materials_optional=_complete_evidence_materials(),
        )
        assert material["actual_review_evidence_complete_predicate_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP16_STATUS_COMPLETE_CANDIDATE_BODYFREE_REF
        assert elr.assert_p7_r54_ahr_post_alr12_elr_op16_actual_review_evidence_complete_predicate_contract(material) is True
        _OP16_COMPLETE_CACHE = material
    return deepcopy(_OP16_COMPLETE_CACHE)


def _op17_ready() -> dict[str, object]:
    global _OP17_READY_CACHE
    if _OP17_READY_CACHE is None:
        material = elr.build_p7_r54_ahr_post_alr12_elr_op17_dmd_compatible_actual_operation_evidence_receipt_adapter_handoff_candidate(
            op16_actual_review_evidence_complete_predicate=_op16_complete(),
        )
        assert material["dmd_compatible_receipt_adapter_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP17_STATUS_READY_BODYFREE_REF
        assert elr.assert_p7_r54_ahr_post_alr12_elr_op17_dmd_compatible_actual_operation_evidence_receipt_adapter_handoff_candidate_contract(material) is True
        _OP17_READY_CACHE = material
    return deepcopy(_OP17_READY_CACHE)


def _assert_common_bodyfree_no_touch(material: dict[str, object], *, allow_actual_complete: bool = False) -> None:
    assert material["body_free"] is True
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    for field in elr.P7_R54_AHR_POST_ALR12_ELR_REQUIRED_FALSE_FLAG_REFS:
        if allow_actual_complete and field == "actual_review_evidence_complete":
            assert material[field] is True
        else:
            assert material[field] is False, field
    for marker_map_key in ("public_contract", "post_alr12_no_touch_contract", "body_free_markers"):
        assert material[marker_map_key]
        assert all(value is False for value in material[marker_map_key].values()), marker_map_key
    assert all(value is False for value in material["not_claimed_boundary"].values())


def test_elr_op16_waits_when_final_validation_passed_but_complete_chain_is_not_supplied() -> None:
    material = elr.build_p7_r54_ahr_post_alr12_elr_op16_actual_review_evidence_complete_predicate(
        op15_final_no_leak_no_touch_validation=_op15_passed(),
    )

    assert set(material) == set(elr.P7_R54_AHR_POST_ALR12_ELR_OP16_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP16_SCHEMA_VERSION
    assert material["actual_review_evidence_complete_predicate_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP16_STATUS_WAITING_FOR_EVIDENCE_REF
    assert material["actual_review_evidence_complete"] is False
    assert material["actual_review_evidence_complete_candidate"] is False
    assert material["ready_for_dmd_compatible_receipt_adapter"] is False
    assert material["complete_condition_missing_or_false_ref_count"] > 0
    assert "explicit_local_only_allow_receipt_accepted" in material["complete_condition_missing_or_false_refs"]
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_NEXT_STEP_WAIT_FOR_COMPLETE_PREDICATE_EVIDENCE_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op16_actual_review_evidence_complete_predicate_contract(material) is True
    _assert_common_bodyfree_no_touch(material)


def test_elr_op16_marks_complete_candidate_only_when_all_external_bodyfree_evidence_conditions_pass() -> None:
    material = _op16_complete()

    assert set(material) == set(elr.P7_R54_AHR_POST_ALR12_ELR_OP16_REQUIRED_FIELD_REFS)
    assert material["actual_review_evidence_complete_predicate_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP16_STATUS_COMPLETE_CANDIDATE_BODYFREE_REF
    assert material["actual_review_evidence_complete"] is True
    assert material["actual_review_evidence_complete_candidate"] is True
    assert material["actual_review_evidence_complete_from_real_operation_claimed_here"] is False
    assert material["source_kind_is_actual_local_only_human_review_by_person"] is True
    assert material["complete_condition_pass_count"] == len(elr.P7_R54_AHR_POST_ALR12_ELR_OP16_COMPLETE_CONDITION_REFS)
    assert material["complete_condition_missing_or_false_refs"] == []
    for count_key in elr.P7_R54_AHR_POST_ALR12_ELR_OP17_DMD_RECEIPT_COUNT_FIELD_REFS:
        assert material[count_key] == 24
    assert material["ready_for_dmd_compatible_receipt_adapter"] is True
    assert material["helper_green_promoted_to_actual_review_complete"] is False
    assert material["target_green_promoted_to_actual_review_complete"] is False
    assert material["result_memo_green_promoted_to_actual_review_complete"] is False
    assert material["manual_decision_auto_executes_downstream"] is False
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP17_STEP_REF
    assert material["elr_op16_blocker_refs"] == []
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op16_actual_review_evidence_complete_predicate_contract(material) is True
    _assert_common_bodyfree_no_touch(material, allow_actual_complete=True)


@pytest.mark.parametrize("condition_ref", elr.P7_R54_AHR_POST_ALR12_ELR_OP16_COMPLETE_CONDITION_REFS)
def test_elr_op16_waits_when_any_complete_condition_ref_is_false(condition_ref: str) -> None:
    condition_map = {ref: True for ref in elr.P7_R54_AHR_POST_ALR12_ELR_OP16_COMPLETE_CONDITION_REFS}
    condition_map[condition_ref] = False
    refs = {
        "operation_receipt_ref": _op09_accepted()["operation_receipt_ref"],
        "packet_request_ref": _op04_ready()["packet_request_ref"],
        "disposal_purge_receipt_ref": _op14_accepted()["disposal_purge_receipt_ref"],
        "source_kind_ref": elr.P7_R54_AHR_POST_ALR12_ELR_ACTUAL_REVIEW_SOURCE_KIND_REF,
    }
    material = elr.build_p7_r54_ahr_post_alr12_elr_op16_actual_review_evidence_complete_predicate(
        op15_final_no_leak_no_touch_validation=_op15_passed(),
        complete_condition_pass_map_optional=condition_map,
        evidence_ref_summary_optional=refs,
    )

    assert material["actual_review_evidence_complete_predicate_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP16_STATUS_WAITING_FOR_EVIDENCE_REF
    assert condition_ref in material["complete_condition_missing_or_false_refs"]
    assert material["actual_review_evidence_complete_candidate"] is False
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op16_actual_review_evidence_complete_predicate_contract(material) is True


def test_elr_op16_repairs_forbidden_body_material_without_leaking_body_value() -> None:
    materials = _complete_evidence_materials()
    bad_material = dict(materials[0])
    bad_material["question_text"] = "this body text must never leak"
    materials[0] = bad_material

    material = elr.build_p7_r54_ahr_post_alr12_elr_op16_actual_review_evidence_complete_predicate(
        op15_final_no_leak_no_touch_validation=_op15_passed(),
        complete_evidence_materials_optional=materials,
    )

    assert material["actual_review_evidence_complete_predicate_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP16_STATUS_REPAIR_REQUIRED_REF
    assert "elr_op16_evidence_ref_summary_forbidden_payload_key_detected" in material["elr_op16_blocker_refs"]
    assert material["evidence_ref_summary_forbidden_payload_key_path_count"] > 0
    assert "this body text must never leak" not in repr(material)
    assert material["actual_review_evidence_complete"] is False
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op16_actual_review_evidence_complete_predicate_contract(material) is True


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("actual_review_evidence_complete", False),
        ("actual_review_evidence_complete_candidate", False),
        ("ready_for_dmd_compatible_receipt_adapter", False),
        ("complete_condition_pass_count", 12),
        ("operation_receipt_ref", "/tmp/unsafe/bodyfull.json"),
        ("helper_green_promoted_to_actual_review_complete", True),
        ("actual_review_evidence_complete_from_real_operation_claimed_here", True),
        ("manual_decision_auto_executes_downstream", True),
        ("release_allowed", True),
        ("next_required_step", "P8_START"),
    ],
)
def test_elr_op16_contract_rejects_complete_candidate_mutations(field: str, bad_value: object) -> None:
    material = _op16_complete()
    material[field] = bad_value

    with pytest.raises(ValueError):
        elr.assert_p7_r54_ahr_post_alr12_elr_op16_actual_review_evidence_complete_predicate_contract(material)


def test_elr_op17_waits_when_op16_complete_predicate_is_not_ready() -> None:
    op16_waiting = elr.build_p7_r54_ahr_post_alr12_elr_op16_actual_review_evidence_complete_predicate(
        op15_final_no_leak_no_touch_validation=_op15_passed(),
    )
    material = elr.build_p7_r54_ahr_post_alr12_elr_op17_dmd_compatible_actual_operation_evidence_receipt_adapter_handoff_candidate(
        op16_actual_review_evidence_complete_predicate=op16_waiting,
    )

    assert set(material) == set(elr.P7_R54_AHR_POST_ALR12_ELR_OP17_REQUIRED_FIELD_REFS)
    assert material["dmd_compatible_receipt_adapter_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP17_STATUS_WAITING_FOR_COMPLETE_EVIDENCE_REF
    assert material["dmd_compatible_receipt_waiting_for_complete_evidence"] is True
    assert material["dmd_compatible_receipt_adapter_ready"] is False
    assert material["dmd_compatible_actual_operation_evidence_receipt_bodyfree"] == {}
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_NEXT_STEP_WAIT_FOR_COMPLETE_PREDICATE_EVIDENCE_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op17_dmd_compatible_actual_operation_evidence_receipt_adapter_handoff_candidate_contract(material) is True
    _assert_common_bodyfree_no_touch(material)


def test_elr_op17_builds_dmd_compatible_receipt_handoff_candidate_without_running_dmd_or_r52() -> None:
    material = _op17_ready()
    receipt = material["dmd_compatible_actual_operation_evidence_receipt_bodyfree"]

    assert set(material) == set(elr.P7_R54_AHR_POST_ALR12_ELR_OP17_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP17_SCHEMA_VERSION
    assert material["dmd_compatible_receipt_adapter_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP17_STATUS_READY_BODYFREE_REF
    assert material["dmd_compatible_receipt_adapter_ready"] is True
    assert material["dmd_compatible_receipt_handoff_candidate_ready"] is True
    assert receipt["schema_version"] == dmd.P7_R54_AHR_POST_DMH18_DMD_ACTUAL_OPERATION_EVIDENCE_RECEIPT_SCHEMA_VERSION
    assert receipt["source_kind_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_ACTUAL_OPERATION_SOURCE_KIND_REF
    assert dmd._receipt_core_real_operation_claim_supported(receipt) is True
    for field in elr.P7_R54_AHR_POST_ALR12_ELR_OP17_DMD_RECEIPT_COUNT_FIELD_REFS:
        assert receipt[field] == 24
    for field in elr.P7_R54_AHR_POST_ALR12_ELR_OP17_DMD_RECEIPT_REQUIRED_TRUE_FIELD_REFS:
        assert receipt[field] is True
    assert material["dmd_compatible_receipt_forbidden_payload_key_paths"] == []
    assert material["dmd_compatible_receipt_created_here"] is False
    assert material["dmd_compatible_receipt_created_here_by_helper"] is False
    assert material["dmd_compatible_receipt_adapter_created_bodyfree_candidate_only"] is True
    assert material["elr_op17_does_not_execute_dmd_or_r52"] is True
    assert material["r52_actual_execution_started_here"] is False
    assert material["r52_actual_execution_started_here_by_adapter"] is False
    assert material["manual_decision_auto_executes_downstream"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP18_STEP_REF
    assert material["elr_op17_blocker_refs"] == []
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op17_dmd_compatible_actual_operation_evidence_receipt_adapter_handoff_candidate_contract(material) is True
    _assert_common_bodyfree_no_touch(material)


def test_elr_op17_repairs_when_op16_complete_material_fails_contract() -> None:
    op16 = _op16_complete()
    op16["actual_review_evidence_complete"] = False
    material = elr.build_p7_r54_ahr_post_alr12_elr_op17_dmd_compatible_actual_operation_evidence_receipt_adapter_handoff_candidate(
        op16_actual_review_evidence_complete_predicate=op16,
    )

    assert material["dmd_compatible_receipt_adapter_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP17_STATUS_REPAIR_REQUIRED_REF
    assert "elr_op17_op16_complete_predicate_contract_invalid" in material["elr_op17_blocker_refs"]
    assert material["dmd_compatible_receipt_adapter_ready"] is False
    assert material["dmd_compatible_actual_operation_evidence_receipt_bodyfree"] == {}
    assert material["next_required_step"] == elr.P7_R54_AHR_POST_ALR12_ELR_NEXT_STEP_REPAIR_DMD_COMPATIBLE_RECEIPT_ADAPTER_REF
    assert elr.assert_p7_r54_ahr_post_alr12_elr_op17_dmd_compatible_actual_operation_evidence_receipt_adapter_handoff_candidate_contract(material) is True


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("dmd_compatible_receipt_adapter_ready", False),
        ("dmd_compatible_receipt_handoff_candidate_ready", False),
        ("dmd_compatible_receipt_counts_are_24", False),
        ("dmd_compatible_receipt_required_true_fields_passed", False),
        ("dmd_compatible_receipt_created_here", True),
        ("dmd_compatible_receipt_created_here_by_helper", True),
        ("r52_actual_execution_started_here_by_adapter", True),
        ("manual_decision_auto_executes_downstream", True),
        ("release_allowed", True),
        ("next_required_step", "R52_ACTUAL_EXECUTION"),
    ],
)
def test_elr_op17_contract_rejects_ready_mutations(field: str, bad_value: object) -> None:
    material = _op17_ready()
    material[field] = bad_value

    with pytest.raises(ValueError):
        elr.assert_p7_r54_ahr_post_alr12_elr_op17_dmd_compatible_actual_operation_evidence_receipt_adapter_handoff_candidate_contract(material)


@pytest.mark.parametrize(
    ("receipt_field", "bad_value"),
    [
        ("rating_row_count", 23),
        ("reviewed_case_count", 23),
        ("source_kind_ref", "synthetic_fixture"),
        ("actual_human_review_executed_by_person", False),
        ("question_text", "forbidden body text"),
    ],
)
def test_elr_op17_contract_rejects_mutated_dmd_receipt_counts_source_guards_or_body_keys(
    receipt_field: str, bad_value: object
) -> None:
    material = _op17_ready()
    receipt = dict(material["dmd_compatible_actual_operation_evidence_receipt_bodyfree"])
    receipt[receipt_field] = bad_value
    material["dmd_compatible_actual_operation_evidence_receipt_bodyfree"] = receipt

    with pytest.raises(ValueError):
        elr.assert_p7_r54_ahr_post_alr12_elr_op17_dmd_compatible_actual_operation_evidence_receipt_adapter_handoff_candidate_contract(material)


def test_elr_op16_op17_full_operation_aliases_match_canonical_functions() -> None:
    op16 = elr.build_p7_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op16_actual_review_evidence_complete_predicate(
        op15_final_no_leak_no_touch_validation=_op15_passed(),
        complete_evidence_materials_optional=_complete_evidence_materials(),
    )
    assert elr.assert_p7_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op16_actual_review_evidence_complete_predicate_contract(op16) is True
    op17 = elr.build_p7_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op17_dmd_compatible_actual_operation_evidence_receipt_adapter_handoff_candidate(
        op16_actual_review_evidence_complete_predicate=op16,
    )
    assert elr.assert_p7_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op17_dmd_compatible_actual_operation_evidence_receipt_adapter_handoff_candidate_contract(op17) is True
    assert op17["dmd_compatible_receipt_adapter_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP17_STATUS_READY_BODYFREE_REF


def test_elr_op16_op17_result_memo_is_bodyfree_and_current_scope_only() -> None:
    memo_path = TEST_DIR / "R54_AHR_PostALR12_ExplicitLocalOnlyReviewStartRetryOperation_ELR_OP00_OP17_Result_20260704.md"
    text = memo_path.read_text(encoding="utf-8")

    assert "ELR-OP16" in text
    assert "ELR-OP17" in text
    assert "actual_review_evidence_complete predicate: implemented" in text
    assert "DMD-compatible actual_operation_evidence_receipt adapter: implemented" in text
    assert "DMD re-execution: not performed" in text
    assert "R52 actual execution: not started" in text
    assert "release_allowed: false" in text
    assert "ELR-OP18: downstream non-promotion manual decision hold" in text
    assert "raw_input:" not in text
    assert "comment_text:" not in text
    assert "question_text:" not in text
    assert "local_path:" not in text
    assert "body_hash:" not in text
    assert "terminal_output:" not in text
