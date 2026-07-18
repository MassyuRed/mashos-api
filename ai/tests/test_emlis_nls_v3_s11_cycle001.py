# -*- coding: utf-8 -*-
from __future__ import annotations

"""Cycle 001 acceptance and append-only evidence recomputation tests."""

import ast
from copy import deepcopy
import inspect
import json
from pathlib import Path
import sys
from typing import Any


_HERE = Path(__file__).resolve().parent
_AI_ROOT = _HERE.parent
_TOOLS = _AI_ROOT / "tools"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

from emlis_ai_step10_evidence_v3 import (  # noqa: E402
    assert_body_free,
    validate_historical_batch_run_summary,
)
from emlis_ai_step11_cycle_evidence_v3 import (  # noqa: E402
    _CHANGE_NEGATIVE_TEST_IDS,
    _CASE_IDS,
    _STEP11_REVIEW_FAILURE_CODES,
    _surface_distribution_assessment,
    _valid_change_negative_test_ids,
    CUMULATIVE100_RECEIPT_SCHEMA,
    CYCLE_ACCEPTANCE_SCHEMA,
    FROZEN_KNOWN28_EXPECTED_APPLICABILITY_SHA256,
    FROZEN_KNOWN28_GENERIC_PROJECTION_POLICY_SHA256,
    KNOWN28_EXPECTED_APPLICABILITY,
    KNOWN28_EXPECTED_APPLICABILITY_SHA256,
    KNOWN28_GENERIC_PROJECTION_POLICY,
    KNOWN28_GENERIC_PROJECTION_POLICY_SHA256,
    KNOWN28_RECEIPT_SCHEMA,
    STEP11_CURRENT_CANDIDATE_VERSION_ID,
    STEP11_HISTORICAL_RC0021_CANDIDATE_VERSION_ID,
    STEP11_RC0023_SURFACE_DISTRIBUTION_ASSESSMENT_SCHEMA,
    STEP11_BATCH_RUN_SCHEMA,
    STEP11_RUNTIME_ADAPTER_VERSION,
    STEP11_SUCCESSOR_CANDIDATE_VERSION_ID,
    build_known28_receipt,
    validate_known28_applicability_contract,
    validate_known28_receipt,
    validate_step11_batch_run_summary,
    validate_step11_private_verification_receipt,
)
from emlis_ai_step11_natural_surface_v3 import (  # noqa: E402
    STEP11_CANDIDATE_VERSION_ID,
)
from emlis_ai_step11_runtime_adapter_v3 import (  # noqa: E402
    STEP11_RUNTIME_ADAPTER_VERSION as RUNTIME_ADAPTER_VERSION,
    STEP11_RUNTIME_SUMMARY_SCHEMA,
)
from emlis_nls_v3_s2_sample_registry import (  # noqa: E402
    load_canonical_json,
)
import emlis_nls_v3_step11_batch_run as batch_run_module  # noqa: E402
from emlis_nls_v3_step11_batch_run import (  # noqa: E402
    _surface_distribution_fields,
)
from emlis_nls_v3_step11_cycle_finalize import (  # noqa: E402
    _LEDGER_NEGATIVE_TEST_IDS,
    _common_cause_codes,
    _correction_owner_paths,
    _correction_strategy_codes,
    _change_rows,
    _failure_layer,
    _regression_risk_codes,
)
from emlis_nls_v3_step11_regression import (  # noqa: E402
    STEP11_DEVELOPMENT42_RECEIPT_SCHEMA,
    validate_development42_receipt,
)


_FIXTURE_ROOT = _HERE / "fixtures" / "emlis_nls_v3"
_GENERATED = _FIXTURE_ROOT / "generated"
_CYCLE = _FIXTURE_ROOT / "cycle_001"


def _json(name: str) -> dict[str, Any]:
    return load_canonical_json(_CYCLE / name)


def _synthetic_surface_profile(variant: int) -> dict[str, Any]:
    variant_id = f"thought_notice_{variant}"
    return {
        "opening_family": variant_id,
        "opening_semantic_family": "thought_notice",
        "opening_variant_id": variant_id,
        "ending_family": "reception_anaphoric",
        "predicate_families": ["thought_notice"],
        "reception_act_families": ["hold_in_attention"],
        "reception_content_kind": "anaphoric",
        "observation_literal_count": 1,
        "unique_literal_owner_count": 1,
        "literal_replay_count": 0,
        "reception_literal_count": 0,
        "near_duplicate_skeleton_commitment": "a" * 64,
    }


def _synthetic_distribution_rows() -> list[dict[str, Any]]:
    return [
        {
            "case_id": case_id,
            "status": "selected",
            "surface_profile": _synthetic_surface_profile(index % 3),
        }
        for index, case_id in enumerate(_CASE_IDS)
    ]


def test_s11_batch_runtime_receives_only_app_reachable_projection() -> None:
    """Keep the frozen semantic_contract on the evaluation side only."""

    source = inspect.getsource(batch_run_module.run_step11_batch)
    tree = ast.parse(source)
    runtime_calls = tuple(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "execute_step11_offline_v3"
    )

    assert len(runtime_calls) == 1
    assert len(runtime_calls[0].args) == 1
    assert isinstance(runtime_calls[0].args[0], ast.Name)
    assert runtime_calls[0].args[0].id == "projected_input"


def test_s11_rc0023_schema_and_tool_version_boundary() -> None:
    assert STEP11_CANDIDATE_VERSION_ID == (
        STEP11_CURRENT_CANDIDATE_VERSION_ID
    )
    assert STEP11_CURRENT_CANDIDATE_VERSION_ID == "nls_v3_rc_0023"
    assert STEP11_HISTORICAL_RC0021_CANDIDATE_VERSION_ID == (
        "nls_v3_rc_0021"
    )
    assert STEP11_SUCCESSOR_CANDIDATE_VERSION_ID == "nls_v3_rc_0020"
    assert CYCLE_ACCEPTANCE_SCHEMA == (
        "cocolon.emlis.nls_v3.cycle_acceptance.v6"
    )
    assert STEP11_BATCH_RUN_SCHEMA == (
        "cocolon.emlis.nls_v3.batch_run_receipt.step11.v2"
    )
    assert STEP11_RUNTIME_SUMMARY_SCHEMA == (
        "cocolon.emlis.nls_v3.step11_runtime_execution_summary.v2"
    )
    assert STEP11_RC0023_SURFACE_DISTRIBUTION_ASSESSMENT_SCHEMA == (
        "cocolon.emlis.nls_v3."
        "surface_distribution_assessment.step11.rc0023.v1"
    )
    assert STEP11_RUNTIME_ADAPTER_VERSION == RUNTIME_ADAPTER_VERSION
    assert STEP11_RUNTIME_ADAPTER_VERSION.endswith(".rc0023.v1")


def test_s11_surface_distribution_rejects_opening_concentration() -> None:
    rows = _synthetic_distribution_rows()
    for index, row in enumerate(rows):
        variant = 0 if index < 60 else 1 if index < 80 else 2
        row["surface_profile"] = _synthetic_surface_profile(variant)

    assessment = _surface_distribution_assessment(
        rows,
        candidate_version_id=STEP11_CANDIDATE_VERSION_ID,
    )

    family = assessment["family_rows"][0]
    assert family["case_count"] == 100
    assert family["distinct_variant_count"] == 3
    assert family["dominant_variant_count"] == 60
    assert family["policy_passed"] is False
    assert assessment["failed_family_count"] == 1
    assert assessment["acceptance_passed"] is False


def test_s11_surface_distribution_rejects_literal_replay() -> None:
    fields = _surface_distribution_fields(
        [
            {
                "section_role": "observation",
                "form_id": "thought_notice:0",
                "source_fragments": ["同じ根拠"],
            },
            {
                "section_role": "observation",
                "form_id": "thought_notice:1",
                "source_fragments": ["同じ根拠"],
            },
            {
                "section_role": "reception",
                "form_id": "reception:anaphoric:hold_in_attention:thought:0",
                "source_fragments": [],
            },
        ]
    )
    assert fields["literal_replay_count"] == 1
    assert fields["reception_content_kind"] == "anaphoric"

    rows = _synthetic_distribution_rows()
    profile = {**rows[0]["surface_profile"], **fields}
    profile["opening_family"] = profile["opening_variant_id"]
    rows[0]["surface_profile"] = profile
    assessment = _surface_distribution_assessment(
        rows,
        candidate_version_id=STEP11_CANDIDATE_VERSION_ID,
    )

    assert assessment["failed_family_count"] == 0
    assert assessment["literal_replay_case_count"] == 1
    assert assessment["acceptance_passed"] is False


def test_s11_surface_distribution_rejects_owner_available_direct_reception(
) -> None:
    fields = _surface_distribution_fields(
        [
            {
                "section_role": "observation",
                "form_id": "thought_notice:0",
                "source_fragments": ["一意の根拠"],
            },
            {
                "section_role": "reception",
                "form_id": "reception:direct:hold_in_attention:thought:0",
                "source_fragments": ["一意の根拠"],
            },
        ]
    )
    assert fields["literal_replay_count"] == 0
    assert fields["reception_content_kind"] == "direct_owned_antecedent"

    rows = _synthetic_distribution_rows()
    profile = {**rows[0]["surface_profile"], **fields}
    profile["opening_family"] = profile["opening_variant_id"]
    rows[0]["surface_profile"] = profile
    assessment = _surface_distribution_assessment(
        rows,
        candidate_version_id=STEP11_CANDIDATE_VERSION_ID,
    )

    assert assessment["failed_family_count"] == 0
    assert assessment["owned_antecedent_direct_reception_count"] == 1
    assert assessment["acceptance_passed"] is False


def test_s11_change_ledger_contract_covers_every_review_failure() -> None:
    assert set(_LEDGER_NEGATIVE_TEST_IDS) == _CHANGE_NEGATIVE_TEST_IDS
    expected = {
        "DEPTH_MISMATCH": (
            "discourse",
            "discourse_depth_selection_mismatch",
            "select_proportional_discourse_depth",
        ),
        "EMLIS_RECEPTION_UNBOUND": (
            "content",
            "reception_not_bound_to_observation",
            "bind_reception_to_source_nucleus",
        ),
        "EXECUTION_EXCEPTION": (
            "runtime",
            "runtime_execution_failed",
            "stabilize_runtime_execution",
        ),
        "FALSE_UNDERSTANDING_COMPLETION": (
            "matcher",
            "false_understanding_completion_not_prevented",
            "prevent_false_understanding_completion",
        ),
        "IMMEDIATE_OBSERVATION_NOT_READ": (
            "content",
            "source_nucleus_not_surface_bound",
            "retain_source_nucleus_observation",
        ),
        "NO_RESPONSE": (
            "runtime",
            "runtime_response_missing",
            "restore_runtime_response_delivery",
        ),
        "NO_VALID_CANDIDATE": (
            "selector",
            "selector_no_valid_candidate",
            "restore_candidate_selection_path",
        ),
        "RELATION_DIRECTION_REVERSED": (
            "discourse",
            "relation_endpoint_direction_mismatch",
            "preserve_relation_endpoints_direction",
        ),
        "REQUIRED_MEANING_MISSING": (
            "content",
            "required_obligation_not_realised",
            "realise_required_obligations",
        ),
        "SECTIONS_SEMANTICALLY_DUPLICATED": (
            "renderer",
            "section_semantic_distinctness_lost",
            "separate_section_semantic_contributions",
        ),
        "SELF_DENIAL_ADOPTED_OR_AMPLIFIED": (
            "matcher",
            "self_denial_boundary_not_preserved",
            "preserve_self_denial_source_scope",
        ),
        "SURFACE_DISTRIBUTION_OVERCONCENTRATED": (
            "renderer",
            "surface_family_selection_collapse",
            "rebalance_surface_family_selection",
        ),
        "SURFACE_UNNATURAL_OR_REPETITIVE": (
            "renderer",
            "internal_surface_abstraction_leak",
            "render_exact_source_nuclei_naturally",
        ),
        "UNKNOWN_BOUNDARY_FILLED": (
            "matcher",
            "unknown_boundary_not_preserved",
            "preserve_unknown_boundary_scope",
        ),
        "UNSUPPORTED_CAUSE_OR_PERSONALITY_OR_DIAGNOSIS": (
            "matcher",
            "unsupported_inference_not_filtered",
            "reject_unsupported_semantic_atom",
        ),
    }
    assert set(expected) == _STEP11_REVIEW_FAILURE_CODES
    for failure_code, (layer, cause, strategy) in expected.items():
        codes = [failure_code]
        assert _failure_layer(codes) == layer
        assert _common_cause_codes(codes) == [cause]
        assert _correction_strategy_codes(codes) == [strategy]
        assert _correction_owner_paths(layer)
        assert _regression_risk_codes(codes)


def test_s11_change_ledger_requires_the_exact_negative_suite() -> None:
    exact = sorted(_CHANGE_NEGATIVE_TEST_IDS)
    assert _valid_change_negative_test_ids(exact) is True
    assert _valid_change_negative_test_ids(exact[:-1]) is False
    assert _valid_change_negative_test_ids([*exact, "unknown_attack"]) is False


def test_s11_change_ledger_splits_cross_layer_review_failures() -> None:
    rows = _change_rows(
        {
            "rows": [
                {
                    "review": {
                        "case_identity_commitment": "a" * 64,
                        "severity": "BLOCKER",
                        "reason_codes": [
                            "REQUIRED_MEANING_MISSING",
                            "UNKNOWN_BOUNDARY_FILLED",
                        ],
                    }
                }
            ]
        }
    )
    assert len(rows) == 2
    by_code = {row["failure_codes"][0]: row for row in rows}
    assert all(len(row["failure_codes"]) == 1 for row in rows)
    assert by_code["REQUIRED_MEANING_MISSING"]["failure_layer"] == "content"
    assert by_code["UNKNOWN_BOUNDARY_FILLED"]["failure_layer"] == "matcher"
    assert all(
        row["negative_test_ids"] == sorted(_CHANGE_NEGATIVE_TEST_IDS)
        for row in rows
    )


def test_s11_known28_applicability_policy_and_inventory_are_frozen() -> None:
    assert validate_known28_applicability_contract() == ()
    assert KNOWN28_GENERIC_PROJECTION_POLICY_SHA256 == (
        FROZEN_KNOWN28_GENERIC_PROJECTION_POLICY_SHA256
    )
    assert KNOWN28_EXPECTED_APPLICABILITY_SHA256 == (
        FROZEN_KNOWN28_EXPECTED_APPLICABILITY_SHA256
    )
    assert KNOWN28_GENERIC_PROJECTION_POLICY[
        "case_specific_overrides_allowed"
    ] is False
    assert KNOWN28_GENERIC_PROJECTION_POLICY[
        "candidate_generation_control_allowed"
    ] is False
    inventory = KNOWN28_EXPECTED_APPLICABILITY
    assert inventory["projection_policy_sha256"] == (
        FROZEN_KNOWN28_GENERIC_PROJECTION_POLICY_SHA256
    )
    assert inventory["counts"] == {
        "app_reachable": 19,
        "expected_non_applicable": 9,
    }
    nonapp = {
        row["case_ref"]: row["expected_issue_codes"]
        for row in inventory["cases"]
        if row["applicability_status"] == "expected_non_applicable"
    }
    assert nonapp == {
        "I6-C02": [
            "input.emotions[0].type:unknown_emotion_type",
            "input.categories[0]:unknown_category",
        ],
        "I6-C03": [
            "input.emotions[0].type:unknown_emotion_type",
            "input.categories[0]:unknown_category",
        ],
        "I6-D01": [
            "input.emotions[0].type:unknown_emotion_type",
            "input.categories[0]:unknown_category",
        ],
        "I6-D03": [
            "input.emotions[0].type:unknown_emotion_type",
            "input.categories[0]:unknown_category",
        ],
        "I6-L01": ["input.emotions[0].type:unknown_emotion_type"],
        "I6-L02": [
            "input.emotions[0].type:unknown_emotion_type",
            "input.categories[0]:unknown_category",
        ],
        "I6-S01": [
            "input.emotions[0].type:unknown_emotion_type",
            "input.categories[0]:unknown_category",
        ],
        "I6-S02": [
            "input.emotions[0].type:unknown_emotion_type",
            "input.categories[0]:unknown_category",
        ],
        "RR8-U12": ["input:thought_action_both_empty_after_js_trim"],
    }


def test_s11_cycle001_rc0023_formal_evidence_is_consistent_and_accepted() -> None:
    dependency = _json("cycle001_dependency_manifest_rc0023.json")
    initial_summary = _json("cycle001_initial_rc0010_summary.json")
    final_summary = _json("cycle001_final_rc0023_summary.json")
    private_verification = _json(
        "cycle001_final_rc0023_private_verification.json"
    )
    known28 = _json("cycle001_known28_rc0023.json")
    development42 = _json("cycle001_development42_rc0023.json")
    invalid16 = _json("cycle001_invalid16_rc0023.json")

    assert STEP11_CURRENT_CANDIDATE_VERSION_ID == "nls_v3_rc_0023"
    assert STEP11_CANDIDATE_VERSION_ID == "nls_v3_rc_0023"
    assert KNOWN28_RECEIPT_SCHEMA == "cocolon.emlis.nls_v3.known28_receipt.v3"
    assert CUMULATIVE100_RECEIPT_SCHEMA.endswith(".v4")
    assert CYCLE_ACCEPTANCE_SCHEMA.endswith(".v6")
    assert validate_known28_applicability_contract() == ()
    assert validate_historical_batch_run_summary(initial_summary) == ()
    assert validate_step11_batch_run_summary(
        final_summary,
        dependency_manifest=dependency,
    ) == ()
    assert validate_step11_private_verification_receipt(
        private_verification,
        final_batch_summary=final_summary,
        final_dependency_manifest=dependency,
    ) == ()
    assert validate_development42_receipt(
        development42,
        final_batch_summary=final_summary,
        dependency_manifest=dependency,
    ) == ()
    artifact_names = {
        "cycle001_acceptance.json",
        "cycle001_available_input_scope.json",
        "cycle001_change_ledger.json",
        "cycle001_corpus_validation.json",
        "cycle001_cumulative100.json",
        "cycle001_final_review.json",
        "cycle001_initial_review.json",
        "cycle001_initial_run_lock.json",
        "cycle001_output_change_review.json",
        "cycle001_output_diff.json",
        "cycle001_rc_correction_rerun_lineage.json",
        "cycle001_rc_correction_support.json",
        "cycle001_workaround_scan.json",
        "cycle001_workaround_scan_input_scope.json",
    }
    artifacts = {name: _json(name) for name in artifact_names}
    for name, artifact in artifacts.items():
        assert_body_free(artifact)

    acceptance = artifacts["cycle001_acceptance.json"]
    cumulative = artifacts["cycle001_cumulative100.json"]
    workaround = artifacts["cycle001_workaround_scan.json"]
    assert acceptance["state"] == "ACCEPTED"
    assert acceptance["counts_toward_karen_minimum"] == 100
    assert all(acceptance["acceptance_conditions"].values())
    assert cumulative["aggregate"]["selected_count"] == 100
    assert cumulative["aggregate"]["exception_count"] == 0
    assert cumulative["aggregate"]["no_valid_candidate_count"] == 0
    assert cumulative["aggregate"]["known28_pass_count"] == 28
    assert cumulative["aggregate"]["known28_selected_count"] == 19
    assert (
        cumulative["aggregate"][
            "known28_expected_non_applicable_match_count"
        ]
        == 9
    )
    assert development42["schema_version"] == (
        STEP11_DEVELOPMENT42_RECEIPT_SCHEMA
    )
    assert cumulative["aggregate"]["development42_pass_count"] == 42
    assert cumulative["aggregate"]["development42_selected_count"] == 24
    assert (
        cumulative["aggregate"][
            "development42_expected_non_applicable_match_count"
        ]
        == 18
    )
    assert cumulative["aggregate"]["known_regression_pass_count"] == 70
    assert cumulative["aggregate"]["legacy_registered_case_count"] == 3
    assert (
        cumulative["aggregate"]["available_real_user_current_valid_count"]
        == 0
    )
    assert known28["schema_version"] == KNOWN28_RECEIPT_SCHEMA
    assert known28["generic_projection_policy_sha256"] == (
        FROZEN_KNOWN28_GENERIC_PROJECTION_POLICY_SHA256
    )
    assert known28["expected_applicability_inventory_sha256"] == (
        FROZEN_KNOWN28_EXPECTED_APPLICABILITY_SHA256
    )
    assert known28["aggregate"] == {
        "case_count": 28,
        "app_reachable_count": 19,
        "expected_non_applicable_count": 9,
        "selected_count": 19,
        "hard_gate_pass_count": 19,
        "expected_non_applicable_match_count": 9,
        "contract_pass_count": 28,
        "exception_count": 0,
        "v1_fallback_count": 0,
        "failure_case_count": 0,
    }
    assert acceptance["acceptance_conditions"][
        "known28_app_reachable_selected_19"
    ] is True
    assert acceptance["acceptance_conditions"][
        "known28_expected_non_applicable_matched_9"
    ] is True
    assert acceptance["acceptance_conditions"][
        "development42_app_reachable_selected_24"
    ] is True
    assert acceptance["acceptance_conditions"][
        "development42_expected_non_applicable_matched_18"
    ] is True
    assert acceptance["acceptance_conditions"][
        "correction_lineage_complete_and_ready"
    ] is True
    assert acceptance["acceptance_conditions"][
        "lineage_final_rc0022_parents_exact"
    ] is True
    assert (
        cumulative["aggregate"]["invalid16_expected_rejection_match_count"]
        == 16
    )
    assert workaround["finding_count"] == 0
    assert all(workaround["negative_test_results"].values())


def test_s11_known28_applicability_exclusion_cannot_false_green() -> None:
    dependency = _json("cycle001_dependency_manifest_rc0023.json")
    final_summary = _json("cycle001_final_rc0023_summary.json")
    known28 = _json("cycle001_known28_rc0023.json")
    assert validate_known28_receipt(
        known28,
        final_batch_summary=final_summary,
        final_dependency_manifest=dependency,
    ) == ()

    forged_rows = deepcopy(known28["rows"])
    app_row = next(
        row for row in forged_rows if row["applicability_status"] == "app_reachable"
    )
    app_row.update(
        {
            "projected_input_commitment": None,
            "applicability_status": "expected_non_applicable",
            "applicability_issue_codes": ["input:keyset_mismatch"],
            "selected_candidate_body_commitment": None,
            "status": "expected_non_applicable",
            "hard_gate_status": "not_applicable",
        }
    )
    forged = build_known28_receipt(
        forged_rows,
        final_batch_summary=final_summary,
        final_dependency_manifest=dependency,
        run_id=known28["run_id"],
        private_packet_commitment=known28["private_packet_commitment"],
        verifier_sha256=known28["verifier_sha256"],
        verified_case_count=known28["verified_case_count"],
    )
    assert forged["formal_status"] == "failed"
    assert forged["aggregate"]["contract_pass_count"] == 27
    assert forged["aggregate"]["selected_count"] == 18
    assert forged["aggregate"]["failure_case_count"] == 1

    false_green = deepcopy(known28)
    false_green["rows"] = forged_rows
    assert validate_known28_receipt(
        false_green,
        final_batch_summary=final_summary,
        final_dependency_manifest=dependency,
    ) != ()


def test_s11_known28_nonapp_issue_substitution_cannot_false_green() -> None:
    dependency = _json("cycle001_dependency_manifest_rc0023.json")
    final_summary = _json("cycle001_final_rc0023_summary.json")
    known28 = _json("cycle001_known28_rc0023.json")
    forged_rows = deepcopy(known28["rows"])
    nonapp_row = next(
        row
        for row in forged_rows
        if row["case_ref"] == "RR8-U12"
    )
    nonapp_row["applicability_issue_codes"] = ["input:keyset_mismatch"]
    forged = build_known28_receipt(
        forged_rows,
        final_batch_summary=final_summary,
        final_dependency_manifest=dependency,
        run_id=known28["run_id"],
        private_packet_commitment=known28["private_packet_commitment"],
        verifier_sha256=known28["verifier_sha256"],
        verified_case_count=known28["verified_case_count"],
    )
    assert forged["formal_status"] == "failed"
    assert forged["aggregate"]["contract_pass_count"] == 27
    assert forged["aggregate"]["expected_non_applicable_match_count"] == 8


def test_s11_cycle001_public_artifacts_contain_no_visible_bodies() -> None:
    forbidden_keys = {
        "action_text",
        "body",
        "current_input",
        "emotions",
        "final_utf8_bytes",
        "rendered_surface",
        "thought_text",
        "utf8_bytes",
        "v1_body",
        "v3_body",
    }
    for path in sorted(_CYCLE.glob("*.json")):
        value = json.loads(path.read_text(encoding="utf-8"))
        assert_body_free(value)
        stack = [value]
        while stack:
            current = stack.pop()
            if type(current) is dict:
                assert not (forbidden_keys & set(current))
                stack.extend(current.values())
            elif type(current) is list:
                stack.extend(current)
