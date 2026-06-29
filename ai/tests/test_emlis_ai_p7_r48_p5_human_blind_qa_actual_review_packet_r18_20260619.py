from __future__ import annotations

import pytest
from copy import deepcopy
from functools import lru_cache

import emlis_ai_p7_r48_p5_human_blind_qa_actual_review_packet as r48


@lru_cache(maxsize=1)
def _cached_r16_r17_freeze() -> tuple:
    freeze = r48.build_p7_r48_r16_r17_validation_no_touch_freeze()
    assert r48.assert_p7_r48_r16_r17_validation_no_touch_freeze_contract(freeze) is True
    return (freeze,)


def _r16_r17_freeze() -> dict:
    return deepcopy(_cached_r16_r17_freeze()[0])


@lru_cache(maxsize=1)
def _cached_r18_freeze() -> tuple:
    freeze = r48.build_p7_r48_touch_candidate_no_touch_boundary_freeze(
        r16_r17_validation_no_touch_freeze=_r16_r17_freeze()
    )
    assert r48.assert_p7_r48_touch_candidate_no_touch_boundary_freeze_contract(freeze) is True
    return (freeze,)


def _r18_freeze() -> dict:
    return deepcopy(_cached_r18_freeze()[0])


def test_r0_to_r17_existing_freeze_is_present_before_r18() -> None:
    freeze = _r16_r17_freeze()

    assert freeze["next_required_step"] == "R18_touch_candidate_no_touch_boundary_freeze"
    assert "R16_display_contract_rn_no_touch_confirmation" in freeze["implemented_steps"]
    assert "R17_validation_command_matrix" in freeze["implemented_steps"]
    assert "R18_touch_candidate_no_touch_boundary_freeze" in freeze["not_yet_implemented_steps"]
    assert freeze["p5_human_blind_qa_confirmed"] is False
    assert freeze["p6_limited_human_readfeel_start_allowed"] is False
    assert freeze["release_allowed"] is False
    assert freeze["p7_complete"] is False
    assert freeze["p8_start_allowed"] is False
    assert freeze["hold004_close_allowed"] is False


def test_r18_freezes_allowed_production_test_and_no_touch_refs() -> None:
    freeze = _r18_freeze()

    assert set(freeze) == set(r48.P7_R48_TOUCH_CANDIDATE_NO_TOUCH_BOUNDARY_REQUIRED_FIELD_REFS)
    assert freeze["policy_section"] == "R18_touch_candidate_no_touch_boundary_freeze"
    assert freeze["touch_boundary_freeze_required"] is True
    assert tuple(freeze["production_touch_candidate_file_refs"]) == r48.P7_R48_PRODUCTION_TOUCH_CANDIDATE_FILE_REFS
    assert tuple(freeze["optional_touch_candidate_file_refs"]) == r48.P7_R48_OPTIONAL_TOUCH_CANDIDATE_FILE_REFS
    assert tuple(freeze["test_touch_candidate_file_refs"]) == r48.P7_R48_R48_TARGET_TEST_REFS
    assert tuple(freeze["allowed_production_file_refs"]) == r48.P7_R48_ALLOWED_PRODUCTION_TOUCH_FILE_REFS
    assert tuple(freeze["allowed_test_file_refs"]) == r48.P7_R48_ALLOWED_TEST_TOUCH_FILE_REFS
    assert tuple(freeze["allowed_actual_touched_file_refs"]) == r48.P7_R48_ALLOWED_ACTUAL_TOUCHED_FILE_REFS
    assert tuple(freeze["explicit_no_touch_file_refs"]) == r48.P7_R48_EXPLICIT_NO_TOUCH_FILE_REFS
    assert tuple(freeze["explicit_no_touch_area_refs"]) == r48.P7_R48_EXPLICIT_NO_TOUCH_AREA_REFS

    assert set(freeze["allowed_actual_touched_file_refs"]).isdisjoint(freeze["explicit_no_touch_file_refs"])
    assert freeze["allowed_refs_do_not_include_no_touch_refs"] is True
    assert freeze["no_touch_refs_must_remain_untouched"] is True
    assert freeze["forbidden_actual_touched_refs_rejected"] is True


def test_r18_r48_target_refs_include_the_r18_boundary_test_without_claiming_execution() -> None:
    freeze = _r18_freeze()
    matrix = r48.build_p7_r48_validation_command_matrix()
    rows = {row["validation_ref"]: row for row in matrix["validation_command_rows"]}

    assert "tests/test_emlis_ai_p7_r48_p5_human_blind_qa_actual_review_packet_r18_20260619.py" in freeze[
        "allowed_test_file_refs"
    ]
    assert "tests/test_emlis_ai_p7_r48_p5_human_blind_qa_actual_review_packet_r18_20260619.py" in rows[
        "r48_target_tests"
    ]["target_refs"]
    assert rows["r48_target_tests"]["executed_here"] is False
    assert rows["r48_target_tests"]["green_confirmed_here"] is False
    assert rows["r48_target_tests"]["green_claim_allowed_here"] is False


def test_r18_expected_current_patch_touched_refs_are_allowed() -> None:
    freeze = _r18_freeze()

    assert tuple(freeze["current_patch_expected_touched_file_refs"]) == (
        r48.P7_R48_R18_CURRENT_PATCH_EXPECTED_TOUCHED_FILE_REFS
    )
    assert r48.assert_p7_r48_touch_candidate_no_touch_actual_touched_file_refs_contract(
        freeze["current_patch_expected_touched_file_refs"], touch_boundary_freeze=freeze
    ) is True


def test_r18_rejects_rn_api_runtime_and_p5_boundary_touches() -> None:
    freeze = _r18_freeze()

    forbidden_refs = [
        "Cocolon/screens/InputScreen.js",
        "Cocolon/tests/rn-screen-contracts.test.js",
        "services/ai_inference/api_emotion_submit.py",
        "services/ai_inference/emlis_ai_reply_service.py",
        "services/ai_inference/emlis_ai_user_label_connection_gate.py",
    ]
    for ref in forbidden_refs:
        with pytest.raises(ValueError):
            r48.assert_p7_r48_touch_candidate_no_touch_actual_touched_file_refs_contract(
                [
                    "services/ai_inference/emlis_ai_p7_r48_p5_human_blind_qa_actual_review_packet.py",
                    ref,
                ],
                touch_boundary_freeze=freeze,
            )


def test_r18_rejects_unlisted_actual_touched_refs() -> None:
    freeze = _r18_freeze()

    with pytest.raises(ValueError):
        r48.assert_p7_r48_touch_candidate_no_touch_actual_touched_file_refs_contract(
            ["services/ai_inference/unplanned_r48_runtime_helper.py"],
            touch_boundary_freeze=freeze,
        )


def test_r18_keeps_runtime_rn_api_db_release_and_review_execution_closed() -> None:
    freeze = _r18_freeze()

    for key in (
        "production_runtime_spread_allowed",
        "rn_runtime_spread_allowed",
        "api_db_release_spread_allowed",
        "rn_contract_changed_here",
        "rn_production_files_touched_here",
        "rn_contract_test_files_touched_here",
        "rn_visible_contract_changed_here",
        "public_response_shape_changed_here",
        "api_response_shape_changed_here",
        "public_response_top_level_key_added_here",
        "api_route_changed_here",
        "db_schema_changed_here",
        "db_migration_changed_here",
        "emlis_reply_runtime_changed_here",
        "p5_runtime_changed_here",
        "p5_gate_relaxed_here",
        "release_material_changed_here",
        "actual_human_review_run_here",
        "actual_body_full_packet_generated_here",
        "body_full_writer_created_here",
        "local_reviewer_payload_materialized_here",
        "actual_rating_rows_materialized_here",
        "actual_blocker_rows_materialized_here",
        "actual_execution_blocker_rows_materialized_here",
        "actual_disposal_run_here",
        "actual_disposal_receipt_materialized_here",
        "p5_human_blind_qa_confirmed",
        "p6_limited_human_readfeel_start_allowed",
        "release_allowed",
        "p7_complete",
        "p8_start_allowed",
        "hold004_close_allowed",
    ):
        assert freeze[key] is False


def test_r18_contract_rejects_no_touch_overlap_and_runtime_spread() -> None:
    freeze = _r18_freeze()
    freeze["allowed_actual_touched_file_refs"] = list(freeze["allowed_actual_touched_file_refs"]) + [
        "services/ai_inference/emlis_ai_reply_service.py"
    ]

    with pytest.raises(ValueError):
        r48.assert_p7_r48_touch_candidate_no_touch_boundary_freeze_contract(freeze)

    freeze = _r18_freeze()
    freeze["production_runtime_spread_allowed"] = True

    with pytest.raises(ValueError):
        r48.assert_p7_r48_touch_candidate_no_touch_boundary_freeze_contract(freeze)


def test_r18_completes_r48_step_list_but_does_not_open_release_or_p6() -> None:
    freeze = _r18_freeze()

    assert tuple(freeze["implemented_steps"]) == r48.P7_R48_R18_IMPLEMENTED_STEPS
    assert tuple(freeze["not_yet_implemented_steps"]) == r48.P7_R48_R18_NOT_YET_IMPLEMENTED_STEPS
    assert freeze["not_yet_implemented_steps"] == []
    assert freeze["next_required_step"] == "P5_human_blind_qa_actual_review_execution_decision"
    assert freeze["post_r18_next_work_ref"] == "P5_human_blind_qa_actual_review_execution_decision"
    assert freeze["p5_human_blind_qa_confirmed"] is False
    assert freeze["p6_limited_human_readfeel_start_allowed"] is False
    assert freeze["release_allowed"] is False
    assert freeze["p7_complete"] is False
    assert freeze["p8_start_allowed"] is False
    assert freeze["hold004_close_allowed"] is False
