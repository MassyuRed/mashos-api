# -*- coding: utf-8 -*-
from __future__ import annotations

"""Retrospective, non-mutating audit for Natural Language Surface v2 Steps 0-13.

The audit intentionally preserves the one-shot Holdout A lineage.  It records
and reproduces defects without changing the frozen v2 implementation, Holdout
fixtures, evaluation receipts, runtime owner, or public contract.
"""

import ast
from collections import Counter
from dataclasses import replace
import json
from pathlib import Path

from helpers.emlis_nls_v2_s2_development import (
    load_development_cases,
    sha256_file,
)
from helpers.emlis_nls_v2_s6_s7_development import (
    load_development_selection_rows,
)
from emlis_ai_grounded_observation_plan import build_grounded_observation_plan
from emlis_ai_grounded_reception_candidate_plan_v2 import (
    build_reception_candidate_plans_v2,
)
from emlis_ai_grounded_reception_candidate_selector_v2 import (
    HARD_GATE_CODES,
    _evaluate_hard_gate,
    evaluate_and_select_reception_candidate_v2,
)
from emlis_ai_grounded_reception_content_plan_v2 import (
    build_reception_content_plan_v2,
    validate_reception_content_plan_v2,
)


_TEST_ROOT = Path(__file__).resolve().parent
_AI_ROOT = _TEST_ROOT.parent
_REPO_ROOT = _AI_ROOT.parent
_FIXTURE_ROOT = _TEST_ROOT / "fixtures"
_AUDIT_PATH = _FIXTURE_ROOT / "emlis_nls_v2_all_steps_audit_20260713.json"
_S7_FREEZE_PATH = _FIXTURE_ROOT / "emlis_nls_v2_s7_freeze_20260713.json"
_PROTOCOL_PATH = _FIXTURE_ROOT / "emlis_nls_v2_s8_s9_protocol_freeze_20260713.json"
_A_RECEIPT_PATH = _FIXTURE_ROOT / "emlis_nls_v2_s8_holdout_a_receipt_20260713.json"
_B_RECEIPT_PATH = _FIXTURE_ROOT / "emlis_nls_v2_s9_holdout_b_receipt_20260713.json"
_S10_S11_PATH = _FIXTURE_ROOT / "emlis_nls_v2_s10_s11_runtime_blocked_20260713.json"
_S12_S13_PATH = _FIXTURE_ROOT / "emlis_nls_v2_s12_s13_device_blocked_20260713.json"
_FROZEN_HOLDOUT_TEST_PATH = (
    _TEST_ROOT / "test_emlis_nls_v2_s8_s9_holdout_evaluation.py"
)
_FORBIDDEN_HOLDOUT_RUNNER_CALLS = frozenset(
    {
        "evaluate_holdout_once",
        "load_holdout_cases_for_one_shot",
        "prepare_blind_review_once",
    }
)
_FORBIDDEN_AUDIT_BODY_KEYS = frozenset(
    {
        "current_input",
        "memo",
        "memo_action",
        "text",
        "v1_text",
        "v2_text",
        "surface_text",
        "candidate_text",
        "selected_text",
        "raw_input",
        "raw_text",
        "source_text",
        "comment_text",
        "expected_text",
    }
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _called_function_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def _assert_audit_body_free(value) -> None:
    if isinstance(value, dict):
        assert not (_FORBIDDEN_AUDIT_BODY_KEYS & set(value))
        for child in value.values():
            _assert_audit_body_free(child)
    elif isinstance(value, list):
        for child in value:
            _assert_audit_body_free(child)


def test_all_steps_audit_fixes_the_completion_boundary_without_rewriting_history() -> None:
    audit = _load(_AUDIT_PATH)
    assert audit["schema_version"] == "cocolon.emlis.nls_v2.all_steps_audit.v1"
    assert audit["audit_boundary"] == {
        "last_fully_verified_step": 2,
        "first_confirmed_underimplementation_step": 3,
        "first_surface_quality_defect_step": 5,
        "first_formal_nonpass_step": 8,
        "first_wholly_unperformed_step": 9,
        "current_runtime_owner": "grounded_sentence_surface_canonical_v1",
        "current_v2_state": "offline_only_stopped",
        "in_place_v2_repair_allowed_after_holdout_a_stop": False,
        "new_design_and_fresh_holdouts_required": True,
    }
    assert [row["step"] for row in audit["steps"]] == list(range(14))
    assert audit["steps"][3]["audit_status"] == (
        "underimplemented_contract_invalid"
    )
    assert audit["steps"][8]["audit_status"] == "executed_stop"
    assert audit["steps"][9]["audit_status"] == (
        "not_executed_correctly_blocked"
    )
    scope = audit["correction_scope"]
    assert scope["production_files_modified"] == []
    assert scope["runtime_files_modified"] == []
    assert scope["holdout_files_modified"] == []
    assert scope["historical_freeze_files_modified"] == []
    assert audit["body_policy"] == {
        "body_free_metadata": True,
        "raw_input_included": False,
        "raw_text_included": False,
        "source_text_included": False,
        "candidate_bodies_included": False,
        "selected_bodies_included": False,
        "expected_text_included": False,
        "holdout_b_body_parsed": False,
    }
    _assert_audit_body_free(audit)

    manifest = audit["correction_file_manifest"]
    assert manifest["changed_or_new_file_count"] == 8
    assert manifest["hash_bound_file_count"] == 7
    assert manifest["self_referential_file_count"] == 1
    assert manifest["receipt_self"] == {
        "path": "ai/tests/fixtures/emlis_nls_v2_all_steps_audit_20260713.json",
        "change_type": "new",
        "sha256_omitted_reason": "self_referential_receipt",
    }
    expected_paths = {
        "ai/docs/Cocolon_EmlisAI_NLSv2_AllSteps_Audit_Correction_20260713.md",
        "ai/docs/Cocolon_EmlisAI_NLSv2_S2_S3_Result_20260713.md",
        "ai/docs/Cocolon_EmlisAI_NLSv2_S4_S5_Result_20260713.md",
        "ai/docs/Cocolon_EmlisAI_NLSv2_S6_S7_Result_20260713.md",
        "ai/docs/Cocolon_EmlisAI_NLSv2_S10_S11_Blocked_Result_20260713.md",
        "ai/docs/Cocolon_EmlisAI_NLSv2_S12_S13_DeviceCheck_Blocked_Result_20260713.md",
        "ai/tests/test_emlis_nls_v2_all_steps_audit.py",
    }
    assert {row["path"] for row in manifest["hash_bound_files"]} == expected_paths
    assert [
        {
            "path": row["path"],
            "change_type": row["change_type"],
            "sha256": sha256_file(_REPO_ROOT / row["path"]),
        }
        for row in manifest["hash_bound_files"]
    ] == manifest["hash_bound_files"]


def test_all_frozen_receipts_and_stopped_v2_sources_remain_byte_exact() -> None:
    audit = _load(_AUDIT_PATH)
    for section in (
        "frozen_artifact_hashes",
        "v2_source_snapshot",
        "runtime_source_snapshot",
    ):
        live = [
            {
                "path": row["path"],
                "sha256": sha256_file(_REPO_ROOT / row["path"]),
            }
            for row in audit[section]
        ]
        assert live == audit[section]

    assert audit["v2_source_snapshot"] == _load(_S7_FREEZE_PATH)[
        "source_snapshot"
    ]
    assert audit["runtime_source_snapshot"] == _load(_S10_S11_PATH)[
        "runtime_boundary"
    ]["runtime_source_files"]

    reply_source = (
        _AI_ROOT / "services" / "ai_inference" / "emlis_ai_reply_service.py"
    ).read_text(encoding="utf-8")
    assert "emlis_ai_grounded_reception_candidate_selector_v2" not in reply_source
    sentence_source = (
        _AI_ROOT
        / "services"
        / "ai_inference"
        / "emlis_ai_grounded_sentence_surface.py"
    ).read_text(encoding="utf-8")
    assert (
        'GROUND_SURFACE_GENERATION_PATH: Final = "grounded_sentence_surface_canonical_v1"'
        in sentence_source
    )


def test_audit_reproduces_step3_validator_acceptance_defect() -> None:
    case = load_development_cases()[0]
    observation_plan = build_grounded_observation_plan(case.current_input)
    content_plan = build_reception_content_plan_v2(observation_plan)
    first = content_plan.content_units[0]

    invalid_plans = (
        replace(
            content_plan,
            content_units=(replace(first, role="not_a_content_role"),)
            + content_plan.content_units[1:],
        ),
        replace(
            content_plan,
            content_units=(replace(first, required="yes"),)
            + content_plan.content_units[1:],
        ),
        replace(content_plan, safety_policy_ref="wrong_policy:invented"),
        replace(
            content_plan,
            quote_policy=replace(content_plan.quote_policy, max_anchor_count=99),
        ),
        replace(
            content_plan,
            discourse_constraints=replace(
                content_plan.discourse_constraints,
                allowed_strategy_codes=("not_a_discourse_strategy",),
            ),
        ),
    )
    assert all(
        validate_reception_content_plan_v2(plan, observation_plan) == ()
        for plan in invalid_plans
    )


def test_audit_reproduces_step3_felt_role_gap_and_step4_grouping_gap() -> None:
    role_counts: Counter[str] = Counter()
    attention_signature_counts: Counter[str] = Counter()
    attention_then_felt_allowed = 0
    candidate_total = 0
    merged_group_case_count = 0
    sentence_count_variation_case_count = 0

    for case in load_development_cases():
        observation_plan = build_grounded_observation_plan(case.current_input)
        content_plan = build_reception_content_plan_v2(observation_plan)
        role_counts.update(unit.role for unit in content_plan.content_units)
        attention_signature_counts.update(
            unit.semantic_signature
            for unit in content_plan.content_units
            if unit.role == "attention"
        )
        attention_then_felt_allowed += (
            "attention_then_felt"
            in content_plan.discourse_constraints.allowed_strategy_codes
        )
        candidate_set = build_reception_candidate_plans_v2(content_plan)
        candidate_total += len(candidate_set.candidates)
        merged_group_case_count += any(
            len(group) > 1
            for candidate in candidate_set.candidates
            for group in candidate.sentence_groups
        )
        sentence_count_variation_case_count += len(
            {len(candidate.sentence_groups) for candidate in candidate_set.candidates}
        ) > 1

    assert role_counts == {
        "attention": 42,
        "connection": 30,
        "significance": 7,
        "bounded_counterposition": 3,
    }
    assert role_counts["felt_response"] == 0
    assert attention_signature_counts == {
        "concrete_action_recorded": 24,
        "expression_or_label_present": 8,
        "current_burden_present": 5,
        "help_seeking_preserved": 2,
        "intention_retained": 2,
        "lived_change_observed": 1,
    }
    assert attention_then_felt_allowed == 42
    assert candidate_total == 213
    assert merged_group_case_count == 0
    assert sentence_count_variation_case_count == 0


def test_audit_reproduces_step6_metadata_circularity_with_generic_body() -> None:
    rows = load_development_selection_rows()
    assert sum(row.selected_surface.source_anchor_count > 0 for row in rows) == 32
    assert sum(
        row.selection.selected_candidate_id is not None
        and row.selection.selected_candidate_id.endswith("_02")
        for row in rows
    ) == 30
    anchor_available_count = 0
    anchor_selected_over_non_anchor_count = 0
    for selection_row in rows:
        surface_by_id = {
            surface.candidate_id: surface
            for surface in selection_row.surface_candidate_set.candidates
        }
        evaluation_by_id = {
            evaluation.candidate_id: evaluation
            for evaluation in selection_row.selection.evaluations
        }
        anchor_surfaces = tuple(
            surface
            for surface in selection_row.surface_candidate_set.candidates
            if surface.source_anchor_count > 0
        )
        non_anchor_surfaces = tuple(
            surface
            for surface in selection_row.surface_candidate_set.candidates
            if surface.source_anchor_count == 0
        )
        if not anchor_surfaces:
            continue
        anchor_available_count += 1
        selected_id = selection_row.selection.selected_candidate_id
        assert selected_id is not None
        selected_surface = surface_by_id[selected_id]
        selected_score = evaluation_by_id[selected_id].total_score
        assert selected_score is not None
        non_anchor_scores = tuple(
            evaluation_by_id[surface.candidate_id].total_score
            for surface in non_anchor_surfaces
            if evaluation_by_id[surface.candidate_id].total_score is not None
        )
        assert non_anchor_scores
        if (
            selected_surface.source_anchor_count > 0
            and selected_score > max(non_anchor_scores)
        ):
            anchor_selected_over_non_anchor_count += 1
    assert anchor_available_count == 32
    assert anchor_selected_over_non_anchor_count == 32
    row = next(
        item
        for item in rows
        if item.case.case_id == "NLS2-F10-D01"
    )
    candidate_plan = next(
        item
        for item in row.candidate_plan_set.candidates
        if item.candidate_id == row.selection.selected_candidate_id
    )
    generic_text = (
        "Emlisには、ここに言葉を置いたことが特に印象に残っています。"
        "今そこにあることを、まだ決めつけずにいます。"
        "また、ここに言葉を置いたことを、そのまま静かに受け取っています。"
    )
    mutated_surface = replace(
        row.selected_surface,
        text=generic_text,
        sentence_count=3,
        source_anchor_count=0,
        source_anchor_max_visible_chars=0,
    )
    hard_gate, coverage = _evaluate_hard_gate(
        row.observation_plan,
        row.content_plan,
        candidate_plan,
        mutated_surface,
        row.resolver,
    )

    assert row.case.semantic_obligation_codes == (
        "preserve_initial_failure_evaluation",
        "preserve_repeated_pattern",
        "preserve_unknown_cause",
        "preserve_single_variable_intention",
        "preserve_recording_action",
    )
    assert hard_gate.status == "passed"
    assert hard_gate.failed_codes == ()
    assert len(hard_gate.checks) == len(HARD_GATE_CODES) == 14
    assert all(check.status == "passed" for check in hard_gate.checks)
    assert coverage.missing_unit_ids == ()
    assert coverage.covered_unit_ids == ("cu_01", "cu_02", "cu_03")

    observed_negative_codes = {
        code
        for selection_row in rows
        for evaluation in selection_row.selection.evaluations
        for code in evaluation.hard_gate.failed_codes
    }
    negative_row = rows[0]
    invalid_surfaces = tuple(
        replace(
            surface,
            text=surface.text + "必ず成功しました。",
            sentence_count=surface.sentence_count + 1,
        )
        for surface in negative_row.surface_candidate_set.candidates
    )
    invalid_selection = evaluate_and_select_reception_candidate_v2(
        negative_row.observation_plan,
        negative_row.content_plan,
        negative_row.candidate_plan_set,
        replace(
            negative_row.surface_candidate_set,
            candidates=invalid_surfaces,
        ),
        negative_row.resolver,
    )
    observed_negative_codes.update(
        code
        for evaluation in invalid_selection.evaluations
        for code in evaluation.hard_gate.failed_codes
    )
    assert set(HARD_GATE_CODES) - observed_negative_codes == {
        "body_free_meta",
        "depth_proportionality",
        "evidence_resolution",
        "observation_replay",
        "reference_scope",
        "relation_direction",
        "required_content_coverage",
        "section_role_distinctness",
        "self_denial_boundary",
    }


def test_audit_reads_holdout_receipts_without_rerunning_or_masking_the_stop() -> None:
    audit = _load(_AUDIT_PATH)
    protocol = _load(_PROTOCOL_PATH)
    holdout_a = _load(_A_RECEIPT_PATH)
    holdout_b = _load(_B_RECEIPT_PATH)
    facts = audit["holdout_a_facts"]

    assert holdout_a["evaluation_run_count"] == facts["evaluation_run_count"] == 1
    assert holdout_a["overall_status"] == facts["overall_status"] == "stop"
    assert holdout_a["automatic_gate"]["machine_failure_case_count"] == 1
    assert holdout_a["automatic_gate"]["distribution_pass"] is False
    product = holdout_a["human_review"]["product_metrics"]
    assert product["naturalness_pass_count"] == facts["naturalness_pass_count"] == 5
    assert product["non_template_pass_count"] == facts["non_template_pass_count"] == 1
    paired = holdout_a["human_review"]["paired_comparison"]
    assert paired["v2_clearly_better_count"] == 5
    assert paired["same_count"] == 3
    assert paired["v1_clearly_better_count"] == 6
    assert holdout_a["human_review"]["reviewer"][
        "independent_external_reviewer"
    ] is False
    assert holdout_b["evaluation_run_count"] == 0
    assert holdout_b["overall_status"] == "not_evaluated"

    tree = ast.parse(_FROZEN_HOLDOUT_TEST_PATH.read_text(encoding="utf-8"))
    actual_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and _called_function_name(node) in _FORBIDDEN_HOLDOUT_RUNNER_CALLS
    ]
    assert actual_calls == []
    assert sha256_file(_FROZEN_HOLDOUT_TEST_PATH) == protocol[
        "evaluation_protocol"
    ]["receipt_test_sha256"]
    assert audit["known_frozen_test_state"] == {
        "acceptance_red_count": 2,
        "self_matching_string_assertion_red_count": 1,
        "actual_forbidden_holdout_runner_call_count_by_ast": 0,
        "frozen_test_modified": False,
        "classified_failures": [
            {
                "test_id": "test_emlis_nls_v2_s8_s9_holdout_evaluation.py::test_step8_holdout_a_one_shot_body_free_receipt_passes",
                "classification": "expected_red_holdout_a_stop",
            },
            {
                "test_id": "test_emlis_nls_v2_s8_s9_holdout_evaluation.py::test_step8_step9_do_not_reexecute_holdouts_from_tests_or_persist_review_bodies",
                "classification": "frozen_test_self_matching_string_assertion",
            },
            {
                "test_id": "test_emlis_nls_v2_s8_s9_holdout_evaluation.py::test_step9_holdout_b_one_shot_body_free_receipt_passes_without_a_to_b_change",
                "classification": "expected_red_holdout_b_not_evaluated",
            },
        ],
    }
    assert audit["verification"] == {
        "new_audit_test_pass_count": 7,
        "new_audit_test_fail_count": 0,
        "all_nls_v2_zero_argument_test_pass_count": 62,
        "all_nls_v2_zero_argument_test_fail_count": 3,
        "classified_failure_count": 3,
        "unclassified_failure_count": 0,
        "compileall": "pass",
        "json_validation": "pass",
    }


def test_audit_keeps_steps9_through13_in_their_actual_nonexecuted_state() -> None:
    holdout_b = _load(_B_RECEIPT_PATH)
    runtime = _load(_S10_S11_PATH)
    device = _load(_S12_S13_PATH)

    assert holdout_b["evaluation_run_count"] == 0
    assert holdout_b["opened_for_evaluation"] is False
    assert runtime["step10_runtime_preconnection_shadow"]["status"] == "not_executed"
    assert runtime["step10_runtime_preconnection_shadow"]["shadow_run_count"] == 0
    assert runtime["step11_runtime_owner_switch"]["status"] == "not_executed"
    assert runtime["step11_runtime_owner_switch"]["owner_switch_count"] == 0
    assert runtime["runtime_boundary"]["production_owner"] == "v1"
    representative = device["representative4_review"]
    assert representative["formal_v2_evaluation_status"] == "not_executed"
    assert representative["case_count"] == 4
    assert all(
        row["generation_path"] == "grounded_sentence_surface_canonical_v1"
        for row in representative["cases"]
    )
    assert representative["exact8"]["run_count"] == 0
    assert representative["holdout_derived_representatives"]["run_count"] == 0
    step13 = device["step13_two_stage_quantity_ratio_adjustment"]
    assert step13["status"] == "not_executed"
    assert step13["production_adjustment_count"] == 0
