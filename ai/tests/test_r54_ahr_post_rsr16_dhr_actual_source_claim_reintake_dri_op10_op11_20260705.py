# -*- coding: utf-8 -*-
"""R54-AHR Post-RSR16 DRI-OP10/OP11 branch resolver and no-touch guard tests."""

from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_20260705 as dri
from test_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op04_op05_20260705 import (
    _assert_common_bodyfree_no_touch_no_promotion,
)
from test_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op08_op09_20260705 import (
    _op08_waiting_for_op07,
    _op09_ready,
    _ready_chain,
)


_ALLOWED_CHANGED_FILE_REFS = [
    "mashos-api/ai/services/ai_inference/emlis_ai_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_20260705.py",
    "mashos-api/ai/tests/test_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op10_op11_20260705.py",
    "mashos-api/ai/tests/R54_AHR_PostRSR16_DHRActualSourceClaimReintake_DRI_OP00_OP11_Result_20260705.md",
]


def _op09_waiting_for_final_scan() -> dict[str, object]:
    chain = _ready_chain()
    op08_wait = _op08_waiting_for_op07(chain)
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op09_dhr_op04_external_actual_source_claim_adapter_candidate(
        dri_op08_final_bodyfree_no_promotion_source_kind_rescan=op08_wait,
        dri_op04_actual_operation_receipt_revalidation=chain["op04"],
        dri_op05_sanitized_rows_rating_rows_revalidation=chain["op05"],
        dri_op06_question_need_rows_bridge_only_revalidation=chain["op06"],
        dri_op07_disposal_purge_receipt_revalidation=chain["op07"],
    )
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op09_dhr_op04_external_actual_source_claim_adapter_candidate_contract(material) is True
    return material


@lru_cache(maxsize=1)
def _cached_op09_ready() -> dict[str, object]:
    return _op09_ready()


@lru_cache(maxsize=1)
def _cached_op10_ready() -> dict[str, object]:
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op10_deterministic_branch_resolver(
        dri_op09_dhr_op04_external_actual_source_claim_adapter_candidate=_cached_op09_ready(),
    )
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op10_deterministic_branch_resolver_contract(material) is True
    return material


def _op10_ready(op09: dict[str, object] | None = None) -> dict[str, object]:
    if op09 is None:
        return deepcopy(_cached_op10_ready())
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op10_deterministic_branch_resolver(
        dri_op09_dhr_op04_external_actual_source_claim_adapter_candidate=op09,
    )
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op10_deterministic_branch_resolver_contract(material) is True
    return material


@lru_cache(maxsize=1)
def _cached_op11_clear() -> dict[str, object]:
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op11_no_touch_selected_regression_guard(
        dri_op10_deterministic_branch_resolver=_cached_op10_ready(),
        changed_file_refs=_ALLOWED_CHANGED_FILE_REFS,
    )
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op11_no_touch_selected_regression_guard_contract(material) is True
    return material


def _op11_clear(op10: dict[str, object] | None = None) -> dict[str, object]:
    if op10 is None:
        return deepcopy(_cached_op11_clear())
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op11_no_touch_selected_regression_guard(
        dri_op10_deterministic_branch_resolver=op10,
        changed_file_refs=_ALLOWED_CHANGED_FILE_REFS,
    )
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op11_no_touch_selected_regression_guard_contract(material) is True
    return material


def test_dri_op10_ready_branch_selects_exactly_one_branch_without_downstream_execution() -> None:
    material = _op10_ready()

    assert set(material) == set(dri.P7_R54_AHR_POST_RSR16_DRI_OP10_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP10_SCHEMA_VERSION
    assert material["operation_step_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP10_STEP_REF
    assert material["dri_branch_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_BRANCH_READY_FOR_DHR_ACTUAL_SOURCE_CLAIM_REINTAKE_MATERIAL_NO_AUTO_EXECUTION_REF
    assert material["ready_for_dhr_actual_source_claim_reintake_material_no_auto_execution"] is True
    assert material["waiting_for_supplied_receipts_or_complete_candidate"] is False
    assert material["repair_required_before_dhr_reintake_material"] is False
    assert material["bodyfree_leak_or_promotion_blocked"] is False
    assert material["manual_hold_unresolved_no_promotion"] is False
    assert material["adapter_candidate_materialized"] is True
    assert material["adapter_candidate_for_manual_dhr_op04_input_only"] is True
    assert material["adapter_candidate_not_dhr_confirmed"] is True
    assert material["branch_blocker_refs"] == []
    assert material["next_required_step"] == dri.P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_PROVIDE_ADAPTER_TO_DHR_OP04_MANUALLY_REF
    assert material["downstream_auto_execution_allowed"] is False
    assert material["dhr_op04_called_by_dri_op10"] is False
    assert material["dhr_actual_source_claim_confirmed_by_dri_op10"] is False
    assert material["dhr_actual_source_claim_reintake_executed_by_dri_op10"] is False
    assert material["dmd_execution_started_by_dri_op10"] is False
    assert material["r52_actual_execution_started_by_dri_op10"] is False
    assert material["p8_question_design_started"] is False
    assert material["release_allowed"] is False
    assert material["implemented_steps"] == list(dri.P7_R54_AHR_POST_RSR16_DRI_OP10_IMPLEMENTED_STEPS)
    assert material["not_yet_implemented_steps"] == list(dri.P7_R54_AHR_POST_RSR16_DRI_OP10_NOT_YET_IMPLEMENTED_STEPS)
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dri_op10_wait_branch_when_op09_is_waiting_for_final_scan_clear() -> None:
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op10_deterministic_branch_resolver(
        dri_op09_dhr_op04_external_actual_source_claim_adapter_candidate=_op09_waiting_for_final_scan(),
    )

    assert material["dri_branch_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_BRANCH_WAITING_FOR_RSR_COMPLETE_CANDIDATE_OR_SUPPLIED_RECEIPTS_REF
    assert material["waiting_for_supplied_receipts_or_complete_candidate"] is True
    assert material["adapter_candidate_materialized"] is False
    assert "dri_op09_waiting_for_final_scan_clear_or_supplied_material" in material["branch_blocker_refs"]
    assert material["next_required_step"] == dri.P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_WAIT_FOR_RSR_OP15_COMPLETE_CANDIDATE_REF
    assert material["dhr_op04_called_by_dri_op10"] is False
    assert material["release_allowed"] is False
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op10_deterministic_branch_resolver_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dri_op10_repair_branch_when_op09_contract_is_malformed() -> None:
    op09 = deepcopy(_op09_ready())
    op09["adapter_candidate_materialized_bodyfree"] = False

    material = dri.build_p7_r54_ahr_post_rsr16_dri_op10_deterministic_branch_resolver(
        dri_op09_dhr_op04_external_actual_source_claim_adapter_candidate=op09,
    )

    assert material["op09_contract_valid"] is False
    assert material["dri_branch_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_BRANCH_REPAIR_REQUIRED_BEFORE_DHR_REINTAKE_MATERIAL_REF
    assert material["repair_required_before_dhr_reintake_material"] is True
    assert "dri_op09_contract_invalid" in material["branch_blocker_refs"]
    assert material["next_required_step"] == dri.P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_REPAIR_OP03_INVENTORY_REF
    assert material["dhr_op04_called_by_dri_op10"] is False
    assert material["release_allowed"] is False
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op10_deterministic_branch_resolver_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dri_op10_blocked_branch_for_body_or_promotion_material_before_manual_dhr_input() -> None:
    op09 = deepcopy(_op09_ready())
    op09["question_text"] = "do not leak DRI OP10 question text"
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op10_deterministic_branch_resolver(
        dri_op09_dhr_op04_external_actual_source_claim_adapter_candidate=op09,
    )

    assert material["dri_branch_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_BRANCH_BODYFREE_LEAK_OR_PROMOTION_BLOCKED_REF
    assert material["bodyfree_leak_or_promotion_blocked"] is True
    assert "dri_op09.question_text" in material["branch_blocker_refs"]
    assert material["adapter_candidate_materialized"] is False
    assert material["dhr_op04_called_by_dri_op10"] is False
    assert material["p8_question_design_started"] is False
    assert material["release_allowed"] is False
    assert "do not leak DRI OP10 question text" not in repr(material)
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op10_deterministic_branch_resolver_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dri_op11_clear_guard_accepts_only_helper_tests_result_memo_changes() -> None:
    material = _op11_clear()

    assert set(material) == set(dri.P7_R54_AHR_POST_RSR16_DRI_OP11_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP11_SCHEMA_VERSION
    assert material["operation_step_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP11_STEP_REF
    assert material["dri_op11_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP11_STATUS_NO_TOUCH_GUARD_CLEAR_REF
    assert material["dri_op11_no_touch_guard_clear"] is True
    assert material["changed_file_scope_limited_to_helper_tests_result_memo"] is True
    assert material["changed_file_refs"] == _ALLOWED_CHANGED_FILE_REFS
    assert material["disallowed_changed_file_refs"] == []
    assert material["blocked_changed_file_refs"] == []
    assert material["rn_no_touch_grep_match_refs"] == []
    assert material["selected_regression_required"] is True
    assert material["api_change_allowed_here"] is False
    assert material["db_change_allowed_here"] is False
    assert material["rn_change_allowed_here"] is False
    assert material["runtime_change_allowed_here"] is False
    assert material["response_key_change_allowed_here"] is False
    assert material["p8_question_surface_change_allowed_here"] is False
    assert material["dhr_op04_called_by_dri_op11"] is False
    assert material["dhr_actual_source_claim_reintake_executed_by_dri_op11"] is False
    assert material["p8_question_design_started"] is False
    assert material["release_allowed"] is False
    assert material["next_required_step"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP12_STEP_REF
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dri_op11_repairs_when_changed_file_refs_are_missing_without_promotion() -> None:
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op11_no_touch_selected_regression_guard(
        dri_op10_deterministic_branch_resolver=_op10_ready(),
    )

    assert material["dri_op11_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP11_STATUS_REPAIR_CHANGED_FILE_REFS_OR_OP10_REF
    assert material["dri_op11_repair_required"] is True
    assert "changed_file_refs_missing_for_no_touch_guard" in material["dri_op11_blocker_refs"]
    assert material["changed_file_scope_limited_to_helper_tests_result_memo"] is False
    assert material["dhr_op04_called_by_dri_op11"] is False
    assert material["release_allowed"] is False
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op11_no_touch_selected_regression_guard_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dri_op11_blocks_rn_or_p8_touch_before_result_memo() -> None:
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op11_no_touch_selected_regression_guard(
        dri_op10_deterministic_branch_resolver=_op10_ready(),
        changed_file_refs=_ALLOWED_CHANGED_FILE_REFS,
        rn_no_touch_grep_match_refs=["Cocolon/src/screens/P8QuestionSurface.tsx:DRI-OP11"],
        p8_question_surface_change_detected=True,
    )

    assert material["dri_op11_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP11_STATUS_BLOCKED_NO_TOUCH_OR_P8_SURFACE_CHANGE_REF
    assert material["dri_op11_blocked_no_touch_or_p8_surface_change"] is True
    assert "p8_question_surface_change_detected" in material["dri_op11_blocker_refs"]
    assert material["rn_no_touch_grep_match_refs"] == ["Cocolon/src/screens/P8QuestionSurface.tsx:DRI-OP11"]
    assert material["changed_file_scope_limited_to_helper_tests_result_memo"] is False
    assert material["dhr_op04_called_by_dri_op11"] is False
    assert material["p8_question_design_started"] is False
    assert material["release_allowed"] is False
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op11_no_touch_selected_regression_guard_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("schema_version", "wrong.schema"),
        ("dri_branch_ref", dri.P7_R54_AHR_POST_RSR16_DRI_BRANCH_WAITING_FOR_RSR_COMPLETE_CANDIDATE_OR_SUPPLIED_RECEIPTS_REF),
        ("ready_for_dhr_actual_source_claim_reintake_material_no_auto_execution", False),
        ("downstream_auto_execution_allowed", True),
        ("dhr_op04_called_by_dri_op10", True),
        ("dhr_actual_source_claim_confirmed_by_dri_op10", True),
        ("dhr_actual_source_claim_reintake_executed_by_dri_op10", True),
        ("p8_question_design_started", True),
        ("release_allowed", True),
        ("body_free", False),
    ],
)
def test_dri_op10_contract_rejects_branch_or_downstream_mutations(field: str, bad_value: object) -> None:
    material = _op10_ready()
    material[field] = bad_value

    with pytest.raises(ValueError):
        dri.assert_p7_r54_ahr_post_rsr16_dri_op10_deterministic_branch_resolver_contract(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("schema_version", "wrong.schema"),
        ("dri_op11_status_ref", dri.P7_R54_AHR_POST_RSR16_DRI_OP11_STATUS_REPAIR_CHANGED_FILE_REFS_OR_OP10_REF),
        ("dri_op11_no_touch_guard_clear", False),
        ("api_change_allowed_here", True),
        ("db_change_allowed_here", True),
        ("rn_change_allowed_here", True),
        ("runtime_change_allowed_here", True),
        ("response_key_change_allowed_here", True),
        ("p8_question_surface_change_allowed_here", True),
        ("downstream_auto_execution_allowed", True),
        ("dhr_op04_called_by_dri_op11", True),
        ("dhr_actual_source_claim_reintake_executed_by_dri_op11", True),
        ("p8_question_design_started", True),
        ("release_allowed", True),
        ("body_free", False),
    ],
)
def test_dri_op11_contract_rejects_no_touch_or_downstream_mutations(field: str, bad_value: object) -> None:
    material = _op11_clear()
    material[field] = bad_value

    with pytest.raises(ValueError):
        dri.assert_p7_r54_ahr_post_rsr16_dri_op11_no_touch_selected_regression_guard_contract(material)


def test_dri_op10_op11_full_title_aliases_match_short_builders_and_asserts() -> None:
    op09 = _op09_ready()
    op10 = dri.build_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op10_deterministic_branch_resolver(
        dri_op09_dhr_op04_external_actual_source_claim_adapter_candidate=op09,
    )
    assert op10["ready_for_dhr_actual_source_claim_reintake_material_no_auto_execution"] is True
    assert dri.assert_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op10_deterministic_branch_resolver_contract(op10) is True

    op11 = dri.build_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op11_no_touch_selected_regression_guard(
        dri_op10_deterministic_branch_resolver=op10,
        changed_file_refs=_ALLOWED_CHANGED_FILE_REFS,
    )
    assert op11["dri_op11_no_touch_guard_clear"] is True
    assert dri.assert_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op11_no_touch_selected_regression_guard_contract(op11) is True
