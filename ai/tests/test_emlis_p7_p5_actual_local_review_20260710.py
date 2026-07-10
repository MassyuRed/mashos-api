# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import shutil
import stat
import sys
from datetime import timedelta
from pathlib import Path
from typing import Any

import pytest


TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import emlis_p7_p5_actual_local_review as review  # noqa: E402


PASS_A_REVIEWER = "human-pass-a-reviewer-01"
PASS_B_REVIEWER = "human-pass-b-reviewer-01"
PASS_C_RESOLVER = "human-pass-c-resolver-01"
SNAPSHOT_REF = "current-snapshot-20260710"
RUNTIME_REF = "current-runtime-20260710"
SOURCE_MATERIAL_REF = "current-source-material-20260710"
EXECUTION_INSTRUCTION_REF = "mash-explicit-p5-actual-local-review-20260710"
PASS_A_TIME = "2026-07-10T10:00:00+09:00"
PASS_B_TIME = "2026-07-10T11:00:00+09:00"
PASS_C_TIME = "2026-07-10T12:00:00+09:00"


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    assert isinstance(value, dict)
    return value


def _write_json(path: Path, value: dict[str, Any]) -> None:
    os.chmod(path, 0o600)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    os.chmod(path, 0o600)


def _materialize_actual_manifest(layout: review.SessionLayout) -> list[str]:
    manifest = _read_json(layout.source_manifest_file)
    manifest.update(
        {
            "manifest_status_ref": review.SOURCE_MANIFEST_READY_STATUS,
            "snapshot_ref": SNAPSHOT_REF,
            "runtime_revision_ref": RUNTIME_REF,
            "source_material_ref": SOURCE_MATERIAL_REF,
            "supplied_user_execution_instruction_ref": EXECUTION_INSTRUCTION_REF,
            "currentness_status_ref": review.CURRENTNESS_READY_STATUS,
        }
    )
    secret_tokens: list[str] = []
    for row in manifest["case_rows"]:
        ordinal = int(row["ordinal"])
        input_secret = f"P5_ACTUAL_TEST_INPUT_SECRET_{ordinal:03d}"
        emlis_secret = f"P5_ACTUAL_TEST_EMLIS_SECRET_{ordinal:03d}"
        history_secret_1 = f"P5_ACTUAL_TEST_HISTORY_SECRET_{ordinal:03d}_A"
        history_secret_2 = f"P5_ACTUAL_TEST_HISTORY_SECRET_{ordinal:03d}_B"
        secret_tokens.extend(
            [input_secret, emlis_secret, history_secret_1, history_secret_2]
        )
        row.update(
            {
                "case_ref_id": f"current-case-{ordinal:03d}",
                "source_case_ref": f"current-source-case-{ordinal:03d}",
                "subscription_tier_ref": (
                    "free"
                    if row["family"] == "free_tier_history_present_not_allowed"
                    else "plus"
                ),
                "source_snapshot_ref": SNAPSHOT_REF,
                "source_runtime_ref": RUNTIME_REF,
                "currentness_status_ref": review.CURRENTNESS_READY_STATUS,
                "body_source_kind_ref": "CURRENT_RUNTIME_CAPTURE",
                "current_input_review_surface": input_secret,
                "returned_emlis_surface": emlis_secret,
                "bounded_owned_history_review_surface": [
                    {
                        "relative_time_ref": "relative-1",
                        "review_surface": history_secret_1,
                    },
                    {
                        "relative_time_ref": "relative-2",
                        "review_surface": history_secret_2,
                    },
                ],
            }
        )
    _write_json(layout.source_manifest_file, manifest)
    return secret_tokens


def _set_exact_allows(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        review.P7_R50_EXPLICIT_BODY_FULL_ALLOW_ENV_VAR,
        review.P7_R50_EXPLICIT_BODY_FULL_ALLOW_TOKEN_REF,
    )
    monkeypatch.setenv(
        review.P7_R51_EXPLICIT_ACTUAL_LOCAL_MANUAL_RUN_ALLOW_ENV_VAR,
        review.P7_R51_EXPLICIT_ACTUAL_LOCAL_MANUAL_RUN_ALLOW_TOKEN_REF,
    )


def _initialized_session(
    tmp_path: Path,
    *,
    session_id: str = "p5-actual-review-test",
) -> tuple[Path, review.SessionLayout, list[str]]:
    local_root = tmp_path / "external-local-review-root"
    result = review.initialize_session(local_root=local_root, session_id=session_id)
    assert result["state_ref"] == review.STATE_INITIALIZED
    layout = review._layout(local_root, session_id)  # noqa: SLF001 - operation contract test.
    secrets = _materialize_actual_manifest(layout)
    return local_root, layout, secrets


def _prepared_session(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    session_id: str = "p5-actual-review-test",
) -> tuple[Path, review.SessionLayout, list[str]]:
    local_root, layout, secrets = _initialized_session(
        tmp_path,
        session_id=session_id,
    )
    _set_exact_allows(monkeypatch)
    result = review.prepare_session(
        local_root=local_root,
        session_id=session_id,
        reviewer_ref=PASS_A_REVIEWER,
        human_reviewer_attested=True,
    )
    assert result["state_ref"] == review.STATE_PASS_A_OPEN
    return local_root, layout, secrets


def _record_all_pass_a(local_root: Path, session_id: str) -> dict[str, Any]:
    status: dict[str, Any] = {}
    for ordinal in range(1, review.EXPECTED_CASE_COUNT + 1):
        status = review.record_pass_a_selection(
            local_root=local_root,
            session_id=session_id,
            ordinal=ordinal,
            reviewer_ref=PASS_A_REVIEWER,
            axis_scores={axis: 1.0 for axis in review.P5_HUMAN_BLIND_QA_RATING_AXES},
            verdict="PASS",
            sanitized_reason_ids=[],
            blocker_ids=[],
            human_entry_attested=True,
            reviewed_at=PASS_A_TIME,
        )
    assert status["state_ref"] == review.STATE_PASS_A_FROZEN
    return status


def _record_all_pass_b(local_root: Path, session_id: str) -> dict[str, Any]:
    status: dict[str, Any] = {}
    for ordinal in range(1, review.EXPECTED_CASE_COUNT + 1):
        status = review.record_pass_b_selection(
            local_root=local_root,
            session_id=session_id,
            ordinal=ordinal,
            reviewer_ref=PASS_B_REVIEWER,
            question_need_primary_class="no_question_needed_emlis_can_observe",
            ambiguity_kind_refs=["no_material_ambiguity"],
            sanitized_reason_ids=["no_question_needed_emlis_can_observe"],
            preliminary_observation_possible_ref="AVAILABLE",
            question_kind_candidate_ref="NONE",
            answer_affordance_candidate_refs=["NOT_APPLICABLE"],
            interrogation_risk_ref="ABSENT",
            self_blame_amplification_risk_ref="ABSENT",
            immediate_observation_delay_risk_ref="ABSENT",
            refined_observation_eligibility_ref="NOT_ELIGIBLE",
            human_entry_attested=True,
            reviewed_at=PASS_B_TIME,
        )
    assert status["state_ref"] == review.STATE_PASS_B_FROZEN
    return status


def _record_all_pass_c(local_root: Path, session_id: str) -> dict[str, Any]:
    status: dict[str, Any] = {}
    for ordinal in range(1, review.EXPECTED_CASE_COUNT + 1):
        status = review.record_pass_c_selection(
            local_root=local_root,
            session_id=session_id,
            ordinal=ordinal,
            resolver_ref=PASS_C_RESOLVER,
            plan_candidate_ref="NONE",
            human_resolver_attested=True,
            resolved_at=PASS_C_TIME,
        )
    assert status["state_ref"] == review.STATE_PURGE_REQUIRED
    return status


def _all_file_text(root: Path) -> str:
    chunks: list[str] = []
    for path in root.rglob("*"):
        if path.is_file():
            chunks.append(path.read_text(encoding="utf-8"))
    return "\n".join(chunks)


def test_actual_24_human_review_happy_path_is_blind_irreversible_and_purged(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_id = "p5-actual-review-happy-path"
    local_root, layout, body_secrets = _prepared_session(
        tmp_path,
        monkeypatch,
        session_id=session_id,
    )

    controller = _read_json(layout.controller_manifest_file)
    assert controller["case_count"] == 24
    assert controller["supplied_user_execution_instruction_ref"] == EXECUTION_INSTRUCTION_REF
    assert controller["pass_a_human_reviewer_ref"] == PASS_A_REVIEWER
    assert controller["family_and_tier_hidden_in_pass_a"] is True
    assert controller["family_and_tier_hidden_in_pass_b"] is True
    assert controller["body_full_surface_visible_in_pass_c"] is False

    packet_files = sorted(layout.body_full_dir.glob("*.local_review_packet.json"))
    assert len(packet_files) == 24
    for packet_file in packet_files:
        packet = _read_json(packet_file)
        assert review.assert_p7_r48_p5_reviewer_packet_local_only_payload_contract(packet) is True
        for hidden_key in (
            "case_ref_id",
            "source_case_ref",
            "family",
            "case_role",
            "subscription_tier_ref",
            "expected_boundary_audit_ref",
            "source_snapshot_ref",
            "source_runtime_ref",
        ):
            assert hidden_key not in packet

    _record_all_pass_a(local_root, session_id)
    assert stat.S_IMODE(
        (layout.pass_a_rows_dir / review._row_filename(1)).stat().st_mode  # noqa: SLF001
    ) == 0o400
    with pytest.raises(review.ReviewOperationError):
        review.record_pass_a_selection(
            local_root=local_root,
            session_id=session_id,
            ordinal=1,
            reviewer_ref=PASS_A_REVIEWER,
            axis_scores={axis: 1.0 for axis in review.P5_HUMAN_BLIND_QA_RATING_AXES},
            verdict="PASS",
            sanitized_reason_ids=[],
            blocker_ids=[],
            human_entry_attested=True,
        )

    _record_all_pass_b(local_root, session_id)
    _record_all_pass_c(local_root, session_id)

    frozen_state = _read_json(layout.state_file)
    assert frozen_state["pass_a_human_reviewer_ref"] == PASS_A_REVIEWER
    assert frozen_state["pass_b_human_reviewer_ref"] == PASS_B_REVIEWER
    assert frozen_state["pass_c_plan_overlay_resolver_ref"] == PASS_C_RESOLVER

    final_status = review.purge_session(
        local_root=local_root,
        session_id=session_id,
    )
    assert final_status["state_ref"] == review.STATE_DISPOSAL_VERIFIED
    assert final_status["disposal_verified"] is True
    assert final_status["p5_confirmed_candidate"] is False
    assert final_status["p6_start_allowed"] is False

    assert not layout.body_full_dir.exists()
    assert not layout.reviewer_forms_dir.exists()
    assert not layout.reviewer_notes_dir.exists()

    receipt = _read_json(layout.body_free_results_dir / "disposal_receipt.bodyfree.json")
    assert review.assert_p7_r47_body_free_disposal_receipt_payload_contract(receipt) is True
    assert receipt["body_removed"] is True
    assert receipt["reviewer_notes_removed"] is True
    assert receipt["local_packet_exported"] is False
    assert receipt["content_hash_of_body_stored"] is False

    handoff = _read_json(
        layout.body_free_results_dir / "p5_actual_review_handoff.bodyfree.json"
    )
    assert handoff["actual_human_rating_row_count"] == 24
    assert handoff["actual_r49_question_observation_row_count"] == 24
    assert handoff["actual_p7_pqr_sidecar_row_count"] == 24
    assert handoff["pass_a_human_reviewer_ref"] == PASS_A_REVIEWER
    assert handoff["pass_b_human_reviewer_ref"] == PASS_B_REVIEWER
    assert handoff["pass_c_plan_overlay_resolver_ref"] == PASS_C_RESOLVER
    assert handoff["p5_decision_made_here"] is False
    assert handoff["p6_start_allowed"] is False

    retained_text = _all_file_text(layout.session_dir)
    for secret in body_secrets:
        assert secret not in retained_text
    assert str(local_root.resolve()) not in retained_text
    assert review.P7_R50_EXPLICIT_BODY_FULL_ALLOW_TOKEN_REF not in retained_text
    assert review.P7_R51_EXPLICIT_ACTUAL_LOCAL_MANUAL_RUN_ALLOW_TOKEN_REF not in retained_text


def test_prepare_requires_exact_r50_and_r51_scoped_allows(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_id = "p5-actual-review-missing-allows"
    local_root, layout, _secrets = _initialized_session(
        tmp_path,
        session_id=session_id,
    )
    monkeypatch.delenv(review.P7_R50_EXPLICIT_BODY_FULL_ALLOW_ENV_VAR, raising=False)
    monkeypatch.delenv(
        review.P7_R51_EXPLICIT_ACTUAL_LOCAL_MANUAL_RUN_ALLOW_ENV_VAR,
        raising=False,
    )

    with pytest.raises(review.ReviewOperationError, match="R50"):
        review.prepare_session(
            local_root=local_root,
            session_id=session_id,
            reviewer_ref=PASS_A_REVIEWER,
            human_reviewer_attested=True,
        )

    state = _read_json(layout.state_file)
    assert state["state_ref"] == review.STATE_INITIALIZED
    assert list(layout.body_full_dir.glob("*.local_review_packet.json")) == []

    monkeypatch.setenv(
        review.P7_R50_EXPLICIT_BODY_FULL_ALLOW_ENV_VAR,
        review.P7_R50_EXPLICIT_BODY_FULL_ALLOW_TOKEN_REF,
    )
    monkeypatch.setenv(
        review.P7_R51_EXPLICIT_ACTUAL_LOCAL_MANUAL_RUN_ALLOW_ENV_VAR,
        "wrong-token",
    )
    with pytest.raises(review.ReviewOperationError, match="R51"):
        review.prepare_session(
            local_root=local_root,
            session_id=session_id,
            reviewer_ref=PASS_A_REVIEWER,
            human_reviewer_attested=True,
        )


def test_prepare_keeps_retention_bound_to_earliest_local_body_material(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_id = "p5-actual-review-retention-bound"
    local_root, layout, _secrets = _initialized_session(
        tmp_path,
        session_id=session_id,
    )
    initialized_state = _read_json(layout.state_file)
    source_manifest = _read_json(layout.source_manifest_file)
    _set_exact_allows(monkeypatch)

    review.prepare_session(
        local_root=local_root,
        session_id=session_id,
        reviewer_ref=PASS_A_REVIEWER,
        human_reviewer_attested=True,
    )
    prepared_state = _read_json(layout.state_file)

    retention_deadline = review._parse_timestamp(  # noqa: SLF001
        prepared_state["body_full_retention_deadline"],
        field="body_full_retention_deadline",
    )
    intake_deadline = review._parse_timestamp(  # noqa: SLF001
        initialized_state["intake_retention_deadline"],
        field="intake_retention_deadline",
    )
    source_created_at = review._parse_timestamp(  # noqa: SLF001
        source_manifest["created_at"],
        field="source_manifest.created_at",
    )
    assert retention_deadline <= intake_deadline
    assert retention_deadline <= source_created_at + timedelta(
        hours=review.P7_R47_BODY_FULL_PACKET_RETENTION_HOURS
    )
    assert prepared_state["source_body_material_created_at"] == source_manifest[
        "created_at"
    ]


def test_prepare_rejects_default_unresolved_or_distribution_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_id = "p5-actual-review-manifest-reject"
    local_root, layout, _secrets = _initialized_session(
        tmp_path,
        session_id=session_id,
    )
    _set_exact_allows(monkeypatch)

    manifest = _read_json(layout.source_manifest_file)
    manifest["case_rows"][0]["case_ref_id"] = "p7r48-p5-case-001"
    _write_json(layout.source_manifest_file, manifest)
    with pytest.raises(review.ReviewOperationError, match="default / synthetic / unresolved"):
        review.prepare_session(
            local_root=local_root,
            session_id=session_id,
            reviewer_ref=PASS_A_REVIEWER,
            human_reviewer_attested=True,
        )

    manifest["case_rows"][0]["case_ref_id"] = "current-case-001"
    manifest["case_rows"][0]["family"] = "standard_state_answer_owned_history"
    _write_json(layout.source_manifest_file, manifest)
    with pytest.raises(review.ReviewOperationError, match="family / role配分"):
        review.prepare_session(
            local_root=local_root,
            session_id=session_id,
            reviewer_ref=PASS_A_REVIEWER,
            human_reviewer_attested=True,
        )


def test_prepare_rejects_terminal_control_characters_in_reviewer_surfaces(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_id = "p5-actual-review-terminal-control-reject"
    local_root, layout, _secrets = _initialized_session(
        tmp_path,
        session_id=session_id,
    )
    _set_exact_allows(monkeypatch)
    manifest = _read_json(layout.source_manifest_file)
    manifest["case_rows"][0]["current_input_review_surface"] = "visible\x1b[2Jhidden"
    _write_json(layout.source_manifest_file, manifest)

    with pytest.raises(review.ReviewOperationError, match="local review上限"):
        review.prepare_session(
            local_root=local_root,
            session_id=session_id,
            reviewer_ref=PASS_A_REVIEWER,
            human_reviewer_attested=True,
        )


def test_pass_order_and_each_human_role_are_frozen_independently(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_id = "p5-actual-review-pass-role-freeze"
    local_root, _layout, _secrets = _prepared_session(
        tmp_path,
        monkeypatch,
        session_id=session_id,
    )

    with pytest.raises(review.ReviewOperationError):
        review.record_pass_b_selection(
            local_root=local_root,
            session_id=session_id,
            ordinal=1,
            reviewer_ref=PASS_B_REVIEWER,
            question_need_primary_class="no_question_needed_emlis_can_observe",
            ambiguity_kind_refs=["no_material_ambiguity"],
            sanitized_reason_ids=[],
            preliminary_observation_possible_ref="AVAILABLE",
            question_kind_candidate_ref="NONE",
            answer_affordance_candidate_refs=["NOT_APPLICABLE"],
            interrogation_risk_ref="ABSENT",
            self_blame_amplification_risk_ref="ABSENT",
            immediate_observation_delay_risk_ref="ABSENT",
            refined_observation_eligibility_ref="NOT_ELIGIBLE",
            human_entry_attested=True,
        )

    with pytest.raises(review.ReviewOperationError, match="Pass A reviewer"):
        review.record_pass_a_selection(
            local_root=local_root,
            session_id=session_id,
            ordinal=1,
            reviewer_ref=PASS_B_REVIEWER,
            axis_scores={axis: 1.0 for axis in review.P5_HUMAN_BLIND_QA_RATING_AXES},
            verdict="PASS",
            sanitized_reason_ids=[],
            blocker_ids=[],
            human_entry_attested=True,
        )

    _record_all_pass_a(local_root, session_id)
    with pytest.raises(review.ReviewOperationError, match="human entry attestation"):
        review.record_pass_b_selection(
            local_root=local_root,
            session_id=session_id,
            ordinal=1,
            reviewer_ref=PASS_B_REVIEWER,
            question_need_primary_class="no_question_needed_emlis_can_observe",
            ambiguity_kind_refs=["no_material_ambiguity"],
            sanitized_reason_ids=[],
            preliminary_observation_possible_ref="AVAILABLE",
            question_kind_candidate_ref="NONE",
            answer_affordance_candidate_refs=["NOT_APPLICABLE"],
            interrogation_risk_ref="ABSENT",
            self_blame_amplification_risk_ref="ABSENT",
            immediate_observation_delay_risk_ref="ABSENT",
            refined_observation_eligibility_ref="NOT_ELIGIBLE",
            human_entry_attested=False,
        )
    assert review.session_status(
        local_root=local_root,
        session_id=session_id,
    )["state_ref"] == review.STATE_PASS_A_FROZEN

    review.record_pass_b_selection(
        local_root=local_root,
        session_id=session_id,
        ordinal=1,
        reviewer_ref=PASS_B_REVIEWER,
        question_need_primary_class="no_question_needed_emlis_can_observe",
        ambiguity_kind_refs=["no_material_ambiguity"],
        sanitized_reason_ids=[],
        preliminary_observation_possible_ref="AVAILABLE",
        question_kind_candidate_ref="NONE",
        answer_affordance_candidate_refs=["NOT_APPLICABLE"],
        interrogation_risk_ref="ABSENT",
        self_blame_amplification_risk_ref="ABSENT",
        immediate_observation_delay_risk_ref="ABSENT",
        refined_observation_eligibility_ref="NOT_ELIGIBLE",
        human_entry_attested=True,
        reviewed_at=PASS_B_TIME,
    )
    with pytest.raises(review.ReviewOperationError, match="freeze済み"):
        review.record_pass_b_selection(
            local_root=local_root,
            session_id=session_id,
            ordinal=2,
            reviewer_ref="human-another-pass-b-reviewer",
            question_need_primary_class="no_question_needed_emlis_can_observe",
            ambiguity_kind_refs=["no_material_ambiguity"],
            sanitized_reason_ids=[],
            preliminary_observation_possible_ref="AVAILABLE",
            question_kind_candidate_ref="NONE",
            answer_affordance_candidate_refs=["NOT_APPLICABLE"],
            interrogation_risk_ref="ABSENT",
            self_blame_amplification_risk_ref="ABSENT",
            immediate_observation_delay_risk_ref="ABSENT",
            refined_observation_eligibility_ref="NOT_ELIGIBLE",
            human_entry_attested=True,
        )


def test_question_candidate_requires_available_preobservation_specific_kind_and_absent_risks(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_id = "p5-actual-review-question-guard"
    local_root, layout, _secrets = _prepared_session(
        tmp_path,
        monkeypatch,
        session_id=session_id,
    )
    _record_all_pass_a(local_root, session_id)

    with pytest.raises(review.ReviewOperationError, match="preliminary observation AVAILABLE"):
        review.record_pass_b_selection(
            local_root=local_root,
            session_id=session_id,
            ordinal=1,
            reviewer_ref=PASS_B_REVIEWER,
            question_need_primary_class="question_may_reduce_overread_risk",
            ambiguity_kind_refs=["missing_target"],
            sanitized_reason_ids=["question_may_reduce_overread_risk"],
            preliminary_observation_possible_ref="NOT_AVAILABLE",
            question_kind_candidate_ref="EVENT_CONFIRMATION",
            answer_affordance_candidate_refs=["CHOICES"],
            interrogation_risk_ref="ABSENT",
            self_blame_amplification_risk_ref="ABSENT",
            immediate_observation_delay_risk_ref="ABSENT",
            refined_observation_eligibility_ref="ELIGIBLE",
            human_entry_attested=True,
            reviewed_at=PASS_B_TIME,
        )
    assert not (layout.pass_b_r49_rows_dir / review._row_filename(1)).exists()  # noqa: SLF001

    status = review.record_pass_b_selection(
        local_root=local_root,
        session_id=session_id,
        ordinal=1,
        reviewer_ref=PASS_B_REVIEWER,
        question_need_primary_class="question_may_reduce_overread_risk",
        ambiguity_kind_refs=["missing_target"],
        sanitized_reason_ids=["question_may_reduce_overread_risk"],
        preliminary_observation_possible_ref="AVAILABLE",
        question_kind_candidate_ref="EVENT_CONFIRMATION",
        answer_affordance_candidate_refs=["CHOICES", "DONT_KNOW"],
        interrogation_risk_ref="ABSENT",
        self_blame_amplification_risk_ref="ABSENT",
        immediate_observation_delay_risk_ref="ABSENT",
        refined_observation_eligibility_ref="ELIGIBLE",
        human_entry_attested=True,
        reviewed_at=PASS_B_TIME,
    )
    assert status["pass_b_completed_count"] == 1


def test_pass_c_reads_only_bodyfree_material(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_id = "p5-actual-review-pass-c-no-body"
    local_root, layout, _secrets = _prepared_session(
        tmp_path,
        monkeypatch,
        session_id=session_id,
    )
    _record_all_pass_a(local_root, session_id)
    _record_all_pass_b(local_root, session_id)

    with pytest.raises(review.ReviewOperationError, match="plan overlayはNONE"):
        review.record_pass_c_selection(
            local_root=local_root,
            session_id=session_id,
            ordinal=1,
            resolver_ref=PASS_C_RESOLVER,
            plan_candidate_ref="FREE_LIGHT_SINGLE_QUESTION_CANDIDATE_LATER",
            human_resolver_attested=True,
            resolved_at=PASS_C_TIME,
        )
    assert not (layout.pass_c_sidecar_rows_dir / review._row_filename(1)).exists()  # noqa: SLF001

    original_load_json = review._load_json  # noqa: SLF001

    def guarded_load_json(path: Path, *, max_bytes: int = 8_000_000) -> dict[str, Any]:
        if review._path_under(path, layout.body_full_dir):  # noqa: SLF001
            raise AssertionError("Pass C attempted to read body-full material")
        return original_load_json(path, max_bytes=max_bytes)

    monkeypatch.setattr(review, "_load_json", guarded_load_json)
    status = review.record_pass_c_selection(
        local_root=local_root,
        session_id=session_id,
        ordinal=1,
        resolver_ref=PASS_C_RESOLVER,
        plan_candidate_ref="NONE",
        human_resolver_attested=True,
        resolved_at=PASS_C_TIME,
    )
    assert status["pass_c_completed_count"] == 1


def test_interactive_entry_requires_human_attestation_before_any_prompt_or_body_display(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_id = "p5-actual-review-interactive-attestation"
    local_root, _layout, _secrets = _prepared_session(
        tmp_path,
        monkeypatch,
        session_id=session_id,
    )

    def input_must_not_run(_message: str) -> str:
        raise AssertionError("input prompt must not run before human attestation")

    with pytest.raises(review.ReviewOperationError, match="human entry attestation"):
        review.run_pass_a_interactive(
            local_root=local_root,
            session_id=session_id,
            reviewer_ref=PASS_A_REVIEWER,
            human_entry_attested=False,
            input_fn=input_must_not_run,
        )


def test_abort_physically_purges_partial_local_material_without_creating_handoff(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_id = "p5-actual-review-abort"
    local_root, layout, body_secrets = _prepared_session(
        tmp_path,
        monkeypatch,
        session_id=session_id,
    )
    review.record_pass_a_selection(
        local_root=local_root,
        session_id=session_id,
        ordinal=1,
        reviewer_ref=PASS_A_REVIEWER,
        axis_scores={axis: 1.0 for axis in review.P5_HUMAN_BLIND_QA_RATING_AXES},
        verdict="PASS",
        sanitized_reason_ids=[],
        blocker_ids=[],
        human_entry_attested=True,
        local_note="LOCAL_ONLY_NOTE_MUST_BE_PURGED",
        reviewed_at=PASS_A_TIME,
    )

    status = review.purge_session(
        local_root=local_root,
        session_id=session_id,
        abort=True,
    )
    assert status["state_ref"] == review.STATE_ABORTED_PURGED
    assert status["disposal_verified"] is False
    assert not layout.body_full_dir.exists()
    assert not layout.reviewer_forms_dir.exists()
    assert not layout.reviewer_notes_dir.exists()
    assert not (
        layout.body_free_results_dir / "p5_actual_review_handoff.bodyfree.json"
    ).exists()

    retained_text = _all_file_text(layout.session_dir)
    assert "LOCAL_ONLY_NOTE_MUST_BE_PURGED" not in retained_text
    for secret in body_secrets:
        assert secret not in retained_text


def test_purge_journal_resumes_after_partial_deletion_without_inventing_counts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_id = "p5-actual-review-purge-resume"
    local_root, layout, _secrets = _prepared_session(
        tmp_path,
        monkeypatch,
        session_id=session_id,
    )
    state = review._load_state(layout)  # noqa: SLF001
    target_paths = {
        "body_full_packets.local_only": layout.body_full_dir,
        "reviewer_forms.local_only": layout.reviewer_forms_dir,
        "reviewer_notes.local_only": layout.reviewer_notes_dir,
    }
    target_counts = {
        target_ref: review._entry_count(path)  # noqa: SLF001
        for target_ref, path in target_paths.items()
    }
    state = review._save_state(  # noqa: SLF001
        layout,
        state,
        new_state=review.STATE_PURGE_IN_PROGRESS,
        purge_mode_ref="ABORTED_REVIEW",
        purge_target_entry_counts=target_counts,
        purge_started_at="2026-07-10T13:00:00+09:00",
    )
    assert state["state_ref"] == review.STATE_PURGE_IN_PROGRESS

    review._thaw_tree(layout.body_full_dir)  # noqa: SLF001
    shutil.rmtree(layout.body_full_dir)
    status = review.purge_session(
        local_root=local_root,
        session_id=session_id,
        abort=True,
    )
    assert status["state_ref"] == review.STATE_ABORTED_PURGED
    evidence = _read_json(
        layout.audit_dir / "r51_purge_evidence_rows.bodyfree.json"
    )
    by_ref = {
        row["purge_target_ref"]: row
        for row in evidence["purge_evidence_rows"]
    }
    for target_ref, expected_count in target_counts.items():
        assert by_ref[target_ref]["removed_count"] == expected_count


def test_purge_does_not_claim_verification_when_required_target_was_missing_before_journal(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_id = "p5-actual-review-purge-missing-target"
    local_root, layout, _secrets = _prepared_session(
        tmp_path,
        monkeypatch,
        session_id=session_id,
    )
    shutil.rmtree(layout.reviewer_notes_dir)

    with pytest.raises(review.ReviewOperationError, match="required local-only target"):
        review.purge_session(
            local_root=local_root,
            session_id=session_id,
            abort=True,
        )
    assert not (
        layout.body_free_results_dir / "disposal_receipt.bodyfree.json"
    ).exists()
