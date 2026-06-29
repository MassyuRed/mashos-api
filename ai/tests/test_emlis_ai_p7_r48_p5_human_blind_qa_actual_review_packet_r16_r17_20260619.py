from __future__ import annotations

import pytest

import emlis_ai_p7_r48_p5_human_blind_qa_actual_review_packet as r48


def _r14_r15_freeze() -> dict:
    freeze = r48.build_p7_r48_r14_r15_regression_freeze()
    assert r48.assert_p7_r48_r14_r15_regression_freeze_contract(freeze) is True
    return freeze


def _r16_policy() -> dict:
    policy = r48.build_p7_r48_display_contract_rn_no_touch_confirmation(
        r14_r15_regression_freeze=_r14_r15_freeze()
    )
    assert r48.assert_p7_r48_display_contract_rn_no_touch_confirmation_contract(policy) is True
    return policy


def _r17_matrix() -> dict:
    matrix = r48.build_p7_r48_validation_command_matrix(
        display_contract_rn_no_touch_confirmation=_r16_policy()
    )
    assert r48.assert_p7_r48_validation_command_matrix_contract(matrix) is True
    return matrix


def test_r0_to_r15_existing_freeze_is_present_before_r16_r17() -> None:
    freeze = _r14_r15_freeze()

    assert freeze["next_required_step"] == "R16_display_contract_rn_no_touch_confirmation"
    assert "R14_r46_handoff_regression" in freeze["implemented_steps"]
    assert "R15_p5_core_subset_regression" in freeze["implemented_steps"]
    assert freeze["p5_human_blind_qa_confirmed"] is False
    assert freeze["p6_limited_human_readfeel_start_allowed"] is False
    assert freeze["release_allowed"] is False
    assert freeze["p7_complete"] is False
    assert freeze["p8_start_allowed"] is False
    assert freeze["hold004_close_allowed"] is False


def test_r16_fixes_display_contract_regression_and_keeps_green_unconfirmed() -> None:
    policy = _r16_policy()

    assert set(policy) == set(r48.P7_R48_DISPLAY_CONTRACT_RN_NO_TOUCH_REQUIRED_FIELD_REFS)
    assert policy["policy_section"] == "R16_display_contract_rn_no_touch_confirmation"
    assert policy["display_contract_regression_required"] is True
    assert tuple(policy["display_contract_regression_test_refs"]) == (
        r48.P7_R48_DISPLAY_CONTRACT_REGRESSION_TEST_REFS
    )
    assert policy["display_contract_regression_executed_here"] is False
    assert policy["actual_display_contract_regression_executed_here"] is False
    assert policy["display_contract_green_confirmed_here"] is False
    assert policy["display_contract_green_claim_allowed"] is False
    assert policy["next_required_step"] == "R17_validation_command_matrix"


def test_r16_keeps_rn_no_touch_and_optional_rn_contract() -> None:
    policy = _r16_policy()

    assert policy["rn_no_touch_confirmation_required"] is True
    assert policy["rn_contract_optional"] is True
    assert tuple(policy["rn_contract_test_refs"]) == r48.P7_R48_RN_CONTRACT_OPTIONAL_TEST_REFS
    assert tuple(policy["rn_contract_command_refs"]) == r48.P7_R48_RN_CONTRACT_COMMAND_REFS
    assert tuple(policy["rn_production_file_refs"]) == r48.P7_R48_RN_PRODUCTION_NO_TOUCH_FILE_REFS
    assert policy["rn_contract_executed_here"] is False
    assert policy["actual_rn_contract_executed_here"] is False
    assert policy["rn_contract_green_confirmed_here"] is False
    assert policy["rn_contract_changed_here"] is False
    assert policy["rn_production_files_touched_here"] is False
    assert policy["rn_visible_contract_changed_here"] is False
    assert policy["public_response_shape_changed_here"] is False
    assert policy["api_response_shape_changed_here"] is False
    assert policy["public_response_top_level_key_added_here"] is False
    assert policy["db_schema_changed_here"] is False


def test_r16_contract_rejects_rn_touch_claim() -> None:
    policy = _r16_policy()
    policy["rn_production_files_touched_here"] = True

    with pytest.raises(ValueError):
        r48.assert_p7_r48_display_contract_rn_no_touch_confirmation_contract(policy)


def test_r17_validation_command_matrix_lists_required_and_optional_commands_without_green_claims() -> None:
    matrix = _r17_matrix()

    assert set(matrix) == set(r48.P7_R48_VALIDATION_COMMAND_MATRIX_REQUIRED_FIELD_REFS)
    assert matrix["policy_section"] == "R17_validation_command_matrix"
    assert matrix["validation_command_matrix_required"] is True
    assert tuple(matrix["validation_command_refs"]) == r48.P7_R48_VALIDATION_COMMAND_REFS
    assert len(matrix["validation_command_rows"]) == len(r48.P7_R48_VALIDATION_COMMAND_REFS)

    rows = {row["validation_ref"]: row for row in matrix["validation_command_rows"]}
    assert rows["rn_contract_optional"]["required"] is False
    assert rows["rn_contract_optional"]["optional"] is True
    assert rows["rn_contract_optional"]["working_dir_ref"] == "Cocolon"
    assert rows["backend_collect_only"]["full_backend_suite_green_confirmation"] is False

    for row in matrix["validation_command_rows"]:
        assert set(row) == set(r48.P7_R48_VALIDATION_COMMAND_ROW_FIELD_REFS)
        assert row["executed_here"] is False
        assert row["green_confirmed_here"] is False
        assert row["green_claim_allowed_here"] is False
        assert row["full_backend_suite_green_confirmation"] is False
        assert row["body_free"] is True


def test_r17_keeps_collect_only_separate_from_full_backend_suite_green() -> None:
    matrix = _r17_matrix()

    assert matrix["backend_collect_only_executed_here"] is False
    assert matrix["backend_collect_only_green_confirmed_here"] is False
    assert matrix["backend_collect_only_claimed_as_full_suite_green"] is False
    assert matrix["collect_only_is_full_backend_suite_green"] is False
    assert matrix["full_backend_suite_executed_here"] is False
    assert matrix["full_backend_suite_green_confirmed_here"] is False
    assert matrix["green_unconfirmed_must_not_be_reported_as_green"] is True
    assert matrix["rn_contract_optional"] is True
    assert matrix["next_required_step"] == "R18_touch_candidate_no_touch_boundary_freeze"


def test_r17_contract_rejects_collect_only_as_full_suite_green() -> None:
    matrix = _r17_matrix()
    matrix["collect_only_is_full_backend_suite_green"] = True

    with pytest.raises(ValueError):
        r48.assert_p7_r48_validation_command_matrix_contract(matrix)


def test_r16_r17_combined_freeze_keeps_runtime_rn_release_closed_and_points_to_r18() -> None:
    freeze = r48.build_p7_r48_r16_r17_validation_no_touch_freeze(
        r14_r15_regression_freeze=_r14_r15_freeze()
    )

    assert r48.assert_p7_r48_r16_r17_validation_no_touch_freeze_contract(freeze) is True
    assert freeze["freeze_kind"] == "r16_r17_validation_no_touch_freeze"
    assert freeze["display_contract_regression_required"] is True
    assert freeze["rn_no_touch_confirmation_required"] is True
    assert freeze["validation_command_matrix_required"] is True
    assert freeze["display_contract_regression_executed_here"] is False
    assert freeze["validation_commands_executed_here"] is False
    assert freeze["rn_contract_executed_here"] is False
    assert freeze["rn_production_files_touched_here"] is False
    assert freeze["p5_runtime_changed_here"] is False
    assert freeze["p5_gate_relaxed_here"] is False
    assert freeze["api_response_shape_changed_here"] is False
    assert freeze["db_schema_changed_here"] is False
    assert freeze["emlis_reply_runtime_changed_here"] is False
    assert freeze["p5_human_blind_qa_confirmed"] is False
    assert freeze["p6_limited_human_readfeel_start_allowed"] is False
    assert freeze["release_allowed"] is False
    assert freeze["p7_complete"] is False
    assert freeze["p8_start_allowed"] is False
    assert freeze["hold004_close_allowed"] is False
    assert tuple(freeze["implemented_steps"]) == r48.P7_R48_R16_R17_IMPLEMENTED_STEPS
    assert tuple(freeze["not_yet_implemented_steps"]) == r48.P7_R48_R16_R17_NOT_YET_IMPLEMENTED_STEPS
    assert freeze["next_required_step"] == "R18_touch_candidate_no_touch_boundary_freeze"
