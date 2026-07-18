#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""Recompute and write the body-free rc0027 Cycle 001 evidence graph."""

import argparse
import ast
import hashlib
from pathlib import Path
import re
import sys
from typing import Any, Mapping, Sequence


AI_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = AI_ROOT.parent
SERVICES = AI_ROOT / "services" / "ai_inference"
TESTS = AI_ROOT / "tests"
HELPERS = AI_ROOT / "tests" / "helpers"
TOOLS = AI_ROOT / "tools"
for entry in (SERVICES, TESTS, HELPERS, TOOLS):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

from emlis_ai_nls_v3_artifact_contract import (  # noqa: E402
    artifact_sha256,
    canonical_json_bytes,
)
from emlis_ai_step11_cycle_evidence_v3 import (  # noqa: E402
    build_case_specific_workaround_scan_receipt,
    build_cumulative100_receipt,
    build_cycle001_acceptance,
    build_cycle001_corpus_validation,
    build_cycle_change_ledger,
    build_initial_run_lock,
    build_local_review_set,
    build_output_change_review,
    build_output_diff,
    build_rc0010_rc0020_correction_rerun_lineage,
    build_rc0010_rc0021_correction_rerun_lineage,
    build_rc0010_rc0022_correction_rerun_lineage,
    build_rc0010_rc0023_correction_rerun_lineage,
    build_rc0010_rc0024_correction_rerun_lineage,
    build_rc0010_rc0025_correction_rerun_lineage,
    build_rc0010_rc0026_correction_rerun_lineage,
    build_rc0010_rc0027_correction_rerun_lineage,
    FROZEN_RC0020_PREFLIGHT_BATCH_SUMMARY_SHA256,
    FROZEN_RC0020_PREFLIGHT_MANIFEST_ARTIFACT_SHA256,
    FROZEN_RC0020_PREFLIGHT_SOURCE_CLOSURE_SHA256,
    FROZEN_RC0021_PREFLIGHT_BATCH_SUMMARY_SHA256,
    FROZEN_RC0021_PREFLIGHT_MANIFEST_ARTIFACT_SHA256,
    FROZEN_RC0021_PREFLIGHT_PRIVATE_VERIFICATION_SHA256,
    FROZEN_RC0021_PREFLIGHT_SOURCE_CLOSURE_SHA256,
    FROZEN_RC0022_FORMAL_BATCH_SUMMARY_SHA256,
    FROZEN_RC0022_FORMAL_MANIFEST_ARTIFACT_SHA256,
    FROZEN_RC0022_FORMAL_PRIVATE_VERIFICATION_SHA256,
    FROZEN_RC0022_FORMAL_SOURCE_CLOSURE_SHA256,
    FROZEN_RC0023_FORMAL_BATCH_SUMMARY_SHA256,
    FROZEN_RC0023_FORMAL_MANIFEST_ARTIFACT_SHA256,
    FROZEN_RC0023_FORMAL_PRIVATE_VERIFICATION_SHA256,
    FROZEN_RC0023_FORMAL_SOURCE_CLOSURE_SHA256,
    FROZEN_RC0024_FORMAL_BATCH_SUMMARY_SHA256,
    FROZEN_RC0024_FORMAL_MANIFEST_ARTIFACT_SHA256,
    FROZEN_RC0024_FORMAL_PRIVATE_VERIFICATION_SHA256,
    FROZEN_RC0024_FORMAL_SOURCE_CLOSURE_SHA256,
    FROZEN_RC0025_FORMAL_BATCH_SUMMARY_SHA256,
    FROZEN_RC0025_FORMAL_MANIFEST_ARTIFACT_SHA256,
    FROZEN_RC0025_FORMAL_PRIVATE_VERIFICATION_SHA256,
    FROZEN_RC0025_FORMAL_SOURCE_CLOSURE_SHA256,
    FROZEN_RC0025_DEVELOPMENT42_RECEIPT_SHA256,
    FROZEN_RC0025_INVALID16_RECEIPT_SHA256,
    FROZEN_RC0025_KNOWN28_RECEIPT_SHA256,
    FROZEN_RC0025_PRODUCT_READ_FAILURE_AXES,
    FROZEN_RC0025_PRODUCT_READ_FAILURE_REASONS,
    FROZEN_RC0025_PRODUCT_READ_FAILURE_SHA256,
    FROZEN_RC0026_FORMAL_BATCH_SUMMARY_SHA256,
    FROZEN_RC0026_FORMAL_MANIFEST_ARTIFACT_SHA256,
    FROZEN_RC0026_FORMAL_PRIVATE_VERIFICATION_SHA256,
    FROZEN_RC0026_FORMAL_SOURCE_CLOSURE_SHA256,
    FROZEN_RC0026_DEVELOPMENT42_RECEIPT_SHA256,
    FROZEN_RC0026_INVALID16_RECEIPT_SHA256,
    FROZEN_RC0026_KNOWN28_RECEIPT_SHA256,
    FROZEN_RC0026_PRODUCT_READ_FAILURE_AXES,
    FROZEN_RC0026_PRODUCT_READ_FAILURE_REASONS,
    FROZEN_RC0026_PRODUCT_READ_FAILURE_SHA256,
    STEP11_CURRENT_CANDIDATE_VERSION_ID,
    validate_cycle001_acceptance,
    validate_invalid16_receipt,
    validate_known28_receipt,
    WORKAROUND_NEGATIVE_POLICY_SHA256,
)
from emlis_nls_v3_batch_run import _write_json  # noqa: E402
from emlis_nls_v3_s0_s1_baseline import (  # noqa: E402
    load_baseline_cases,
    load_json as load_step1_json,
    validate_input_contract,
    validate_step1,
)
from emlis_nls_v3_s2_sample_registry import (  # noqa: E402
    LEGACY_FIXTURE_PATH,
    REGISTRY_PATH,
    STEP1_INPUT_CONTRACT_PATH,
    STEP1_INPUT_CONTRACT_SHA256,
    STEP1_RECEIPT_PATH,
    STEP1_RECEIPT_SHA256,
    load_canonical_json,
    load_canonical_jsonl,
    validate_app_reachable_input,
    validate_corpus_registry,
)
from emlis_nls_v3_step11_regression import (  # noqa: E402
    FROZEN_DEVELOPMENT42_LOADER_SHA256,
    FROZEN_DEVELOPMENT42_SOURCE_FILE_SHA256,
    FROZEN_KNOWN28_SOURCE_FILE_SHA256,
    _load_frozen_development42_cases,
    _verify_known28_source_files,
    validate_development42_receipt,
)
from emlis_nls_v3_step11_dependency_manifest import (  # noqa: E402
    validate_current_step11_dependency_manifest,
)


_GENERATION_OWNER_NAMES = frozenset(
    {
        "emlis_ai_step11_surface_catalog_v3.py",
        "emlis_ai_step11_planning_frontier_v3.py",
        "emlis_ai_step11_semantic_overlay_v3.py",
        "emlis_ai_step11_natural_surface_v3.py",
        "emlis_ai_step11_natural_surface_matcher_v3.py",
        "emlis_ai_step11_hard_gate_v3.py",
        "emlis_ai_step11_runtime_adapter_v3.py",
    }
)
_DIMENSIONS = (
    "case_id_branch",
    "coverage_family_branch",
    "expected_output_literal",
    "fixed_sentence_literal",
    "input_specific_literal",
)
_SHA_RE = re.compile(r"^[0-9a-f]{64}$")
_FROZEN_BATCH001_CORPUS_SHA256 = (
    "013dd2ad1c1f446f843f400b3eb16231e8f32649e30114e70039b4cb709e8414"
)
AVAILABLE_INPUT_SCOPE_RECEIPT_SCHEMA = (
    "cocolon.emlis.nls_v3.available_input_scope_receipt.step11.rc0027.v1"
)
HISTORICAL_RC0026_AVAILABLE_INPUT_SCOPE_RECEIPT_SCHEMA = (
    "cocolon.emlis.nls_v3.available_input_scope_receipt.step11.rc0026.v1"
)
HISTORICAL_RC0025_AVAILABLE_INPUT_SCOPE_RECEIPT_SCHEMA = (
    "cocolon.emlis.nls_v3.available_input_scope_receipt.step11.rc0025.v1"
)
HISTORICAL_RC0024_AVAILABLE_INPUT_SCOPE_RECEIPT_SCHEMA = (
    "cocolon.emlis.nls_v3.available_input_scope_receipt.step11.rc0024.v1"
)
HISTORICAL_RC0023_AVAILABLE_INPUT_SCOPE_RECEIPT_SCHEMA = (
    "cocolon.emlis.nls_v3.available_input_scope_receipt.step11.rc0023.v1"
)
HISTORICAL_RC0022_AVAILABLE_INPUT_SCOPE_RECEIPT_SCHEMA = (
    "cocolon.emlis.nls_v3.available_input_scope_receipt.step11.rc0022.v1"
)
HISTORICAL_RC0021_AVAILABLE_INPUT_SCOPE_RECEIPT_SCHEMA = (
    "cocolon.emlis.nls_v3.available_input_scope_receipt.step11.rc0021.v1"
)
HISTORICAL_RC0020_AVAILABLE_INPUT_SCOPE_RECEIPT_SCHEMA = (
    "cocolon.emlis.nls_v3.available_input_scope_receipt.step11.rc0020.v1"
)
_FROZEN_STEP2_REGISTRY_SHA256 = (
    "7746ec94267fae0b89adbf8b5a676e469386fd3376275bc5197e39742941eb3d"
)
_FROZEN_LEGACY_FIXTURE_SHA256 = (
    "e61614561986f92ead55aa830e4c4a0e32932dfbc1fe4d02b7ba4cb9aa7b1db6"
)
_STEP11_SCOPE_CANDIDATE_VERSION_ID = STEP11_CURRENT_CANDIDATE_VERSION_ID
_WORKAROUND_SCAN_INPUT_SCOPE_SCHEMA = (
    "cocolon.emlis.nls_v3.workaround_scan_input_scope.step11.rc0027.v1"
)
_RC_CORRECTION_SUPPORT_SCHEMA = (
    "cocolon.emlis.nls_v3.rc_correction_support.step11.rc0027.v1"
)
_RC0026_CORRECTION_SUPPORT_SCHEMA = (
    "cocolon.emlis.nls_v3.rc_correction_support.step11.rc0026.v1"
)
_RC0025_CORRECTION_SUPPORT_SCHEMA = (
    "cocolon.emlis.nls_v3.rc_correction_support.step11.rc0025.v1"
)
_RC0024_CORRECTION_SUPPORT_SCHEMA = (
    "cocolon.emlis.nls_v3.rc_correction_support.step11.rc0024.v1"
)
_RC0023_CORRECTION_SUPPORT_SCHEMA = (
    "cocolon.emlis.nls_v3.rc_correction_support.step11.rc0023.v1"
)
_RC0022_CORRECTION_SUPPORT_SCHEMA = (
    "cocolon.emlis.nls_v3.rc_correction_support.step11.rc0022.v1"
)
_RC0021_CORRECTION_SUPPORT_SCHEMA = (
    "cocolon.emlis.nls_v3.rc_correction_support.step11.rc0021.v1"
)
_RC0020_PRODUCT_READ_FAILURE_SCHEMA = (
    "cocolon.emlis.nls_v3.product_read_failure.step11.rc0020.v1"
)
_RC0021_PRODUCT_READ_FAILURE_SCHEMA = (
    "cocolon.emlis.nls_v3.product_read_failure.step11.rc0021.v1"
)
_RC0025_PRODUCT_READ_FAILURE_SCHEMA = (
    "cocolon.emlis.nls_v3.product_read_failure.step11.rc0025.v1"
)
_RC0026_PRODUCT_READ_FAILURE_SCHEMA = (
    "cocolon.emlis.nls_v3.product_read_failure.step11.rc0026.v1"
)
_HISTORICAL_LINEAGE_MANIFEST_CANDIDATES = frozenset(
    {
        "nls_v3_rc_0011",
        "nls_v3_rc_0014",
        "nls_v3_rc_0015",
        "nls_v3_rc_0016",
        "nls_v3_rc_0018",
        "nls_v3_rc_0019",
        "nls_v3_rc_0020",
        "nls_v3_rc_0021",
        "nls_v3_rc_0022",
        "nls_v3_rc_0023",
        "nls_v3_rc_0024",
        "nls_v3_rc_0025",
        "nls_v3_rc_0026",
    }
)
_HISTORICAL_LINEAGE_SUMMARY_CANDIDATES = frozenset(
    {
        "nls_v3_rc_0014",
        "nls_v3_rc_0015",
        "nls_v3_rc_0016",
        "nls_v3_rc_0018",
        "nls_v3_rc_0019",
        "nls_v3_rc_0020",
        "nls_v3_rc_0021",
        "nls_v3_rc_0022",
        "nls_v3_rc_0023",
        "nls_v3_rc_0024",
        "nls_v3_rc_0025",
        "nls_v3_rc_0026",
    }
)
_RC_CORRECTION_SCOPE_CODES = {
    "nls_v3_rc_0011": ("initial_cycle_common_structure",),
    "nls_v3_rc_0012": (
        "unknown_classification",
        "self_denial_anchor_binding",
    ),
    "nls_v3_rc_0013": ("legacy_input_projection",),
    "nls_v3_rc_0014": (
        "known_applicability_contract",
        "negative_failure_code_contract",
    ),
    "nls_v3_rc_0015": (
        "legacy_projection_binding",
        "anchor_binding",
    ),
    "nls_v3_rc_0016": (
        "unknown_obligation_binding",
        "matcher_common_structure",
    ),
    "nls_v3_rc_0017": (
        "literal_replay_budget",
        "semantic_coverage",
        "causal_promotion_prevention",
    ),
    "nls_v3_rc_0018": (
        "relation_endpoint_contract",
        "unknown_lifecycle",
        "reception_source_ownership",
        "surface_distribution",
    ),
    "nls_v3_rc_0019": (
        "selected_frontier",
        "obligation_first_planning",
        "typed_clause_grammar",
        "independent_depth_recomputation",
        "two_phase_semantic_binding",
        "semantic_owner_key",
        "literal_replay_budget",
    ),
    "nls_v3_rc_0020": (
        "connective_prefixed_nucleus_source_range_binding",
        "cycle_evidence_append_only_boundary",
        "duplicate_unknown_ownership_distinction",
        "independent_matcher_hard_gate_recomputation",
        "required_explicit_choice_unknown_classification",
        "typed_unknown_target_antecedent_binding",
    ),
    "nls_v3_rc_0021": (
        "compound_surface_balance",
        "natural_non_repetitive_product_read_repair",
        "product_read_acceptance_boundary",
    ),
    "nls_v3_rc_0022": (
        "action_lifecycle_negation_scope",
        "reception_exact_source_ownership",
        "reception_visible_typed_antecedent",
        "independent_reception_owner_recomputation",
        "ordered_product_read_failure_lineage",
    ),
    "nls_v3_rc_0023": (
        "typed_reception_evidence_profile",
        "batch_evidence_reference_resolution",
        "independent_action_lifecycle_source_modality",
        "failed_machine_run_append_only_lineage",
    ),
    "nls_v3_rc_0024": (
        "reception_action_lifecycle_source_slot_ownership",
        "independent_reception_source_slot_recomputation",
    ),
    "nls_v3_rc_0025": (
        "source_local_independent_event_grouping",
        "neutral_coexisting_event_surface_role",
        "development42_v1_body_diagnostic_binding",
    ),
    "nls_v3_rc_0026": (
        "primary_meaning_retention",
        "relation_direction_and_cause_promotion_prevention",
        "unknown_boundary_preservation",
        "natural_surface_distribution_repair",
    ),
    "nls_v3_rc_0027": (
        "fused_semantic_surface_composition",
        "immediate_observation_product_read_repair",
        "append_only_regression_receipt_lineage",
    ),
}
_LEGACY_DISPOSITIONS = frozenset(
    {
        "app_reachable_to_execute",
        "expected_non_applicable",
        "contract_negative_expected_rejection",
    }
)
_SECURITY_TEST_PATH = "ai/tests/test_emlis_nls_v3_s11_hard_gate_security.py"
_LEDGER_NEGATIVE_TEST_IDS = (
    "case_id_override_lookup",
    "forged_candidate_without_ast",
    "noncanonical_body_mutation",
    "relation_scoped_unknown_rejects_partial_antecedent",
    "removing_exact_action_denial_fails_closed",
    "surplus_semantic_atom",
    "typed_unknown_generic_substitution",
    "unbound_denial_injection_is_surplus",
)


def _repo_ref(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError("step11_scope_source_outside_repo") from exc


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _assert_frozen_scope_parent(
    value: Mapping[str, Any],
    *,
    path: Path,
    expected_sha256: str,
    validator: Any,
    role: str,
) -> None:
    if type(value) is not dict:
        raise ValueError(f"step11_scope_{role}_mapping_required")
    if _sha256_file(path) != expected_sha256:
        raise ValueError(f"step11_scope_{role}_source_drift")
    live = load_step1_json(path)
    if dict(value) != live:
        raise ValueError(f"step11_scope_{role}_parent_mismatch")
    issues = tuple(validator(value))
    if issues:
        raise ValueError(f"step11_scope_{role}_invalid:{issues[0]}")


def _known_regression_scope_row(row: Mapping[str, Any]) -> dict[str, Any]:
    regression_id = row.get("regression_id")
    classification = row.get("classification")
    if type(regression_id) is not str or type(classification) is not str:
        raise ValueError("step11_scope_known_inventory_row_invalid")
    case_count = row.get("case_count")
    status = row.get("status")
    if case_count is not None and (
        type(case_count) is not int or case_count <= 0
    ):
        raise ValueError("step11_scope_known_case_count_invalid")
    if status is not None and type(status) is not str:
        raise ValueError("step11_scope_known_status_invalid")

    if classification == "executable_known_regression":
        if case_count is None:
            raise ValueError("step11_scope_known_executable_count_missing")
        disposition = "execute_all_with_legacy_applicability_contract"
        required_receipt_role = "known_regression_execution_receipt"
        machine_execution_required = True
    elif classification == "known_regression_not_novel_evidence":
        if case_count is None:
            raise ValueError("step11_scope_development_count_missing")
        disposition = "execute_all_with_legacy_applicability_contract"
        required_receipt_role = "development_regression_execution_receipt"
        machine_execution_required = True
    elif classification == "body_free_historical_failure":
        disposition = "negative_lineage_only_no_recoverable_input_cohort"
        required_receipt_role = None
        machine_execution_required = False
    elif classification in {
        "sealed_historical_only_do_not_reopen",
        "sealed_historical_only_do_not_open",
    }:
        disposition = "sealed_historical_excluded"
        required_receipt_role = None
        machine_execution_required = False
    elif classification == (
        "known_legacy_ui_unreachable_device_product_failure"
    ):
        if row.get("app_reachable_under_current_contract") is not False:
            raise ValueError("step11_scope_device_legacy_reachability_invalid")
        disposition = "historical_device_baseline_not_local_machine_regression"
        required_receipt_role = None
        machine_execution_required = False
    elif classification == "actual_device_operator_required_later":
        if (
            status != "not_run"
            or row.get("progression_authority") != "none"
            or row.get("valid_for_progression") is not False
        ):
            raise ValueError("step11_scope_actual_device_boundary_invalid")
        disposition = "deferred_actual_device_not_local_machine_regression"
        required_receipt_role = None
        machine_execution_required = False
    else:
        raise ValueError(
            f"step11_scope_unknown_known_classification:{classification}"
        )
    return {
        "regression_id": regression_id,
        "classification": classification,
        "registered_case_count": case_count,
        "source_status": status,
        "execution_disposition": disposition,
        "machine_execution_required": machine_execution_required,
        "required_receipt_role": required_receipt_role,
        "counts_toward_karen_minimum": False,
    }


def _legacy_disposition_rows(
    registry: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], Mapping[str, Any]]:
    collections = registry.get("collections")
    if type(collections) is not list:
        raise ValueError("step11_scope_registry_collections_invalid")
    legacy_collections = [
        row
        for row in collections
        if type(row) is dict and row.get("classification") == "legacy_input"
    ]
    if len(legacy_collections) != 1:
        raise ValueError("step11_scope_exact_one_legacy_collection_required")
    collection = legacy_collections[0]
    if (
        collection.get("status") != "available_contract_fixture"
        or collection.get("storage") != "repo_safe_synthetic_fixture"
        or collection.get("corpus_ref") != _repo_ref(LEGACY_FIXTURE_PATH)
        or collection.get("corpus_sha256") != _FROZEN_LEGACY_FIXTURE_SHA256
        or collection.get("raw_body_in_registry") is not False
        or collection.get("counts_toward_karen_minimum") is not False
        or _sha256_file(LEGACY_FIXTURE_PATH)
        != _FROZEN_LEGACY_FIXTURE_SHA256
    ):
        raise ValueError("step11_scope_legacy_collection_boundary_invalid")
    fixtures = load_canonical_jsonl(LEGACY_FIXTURE_PATH, validator=None)
    if (
        type(collection.get("case_count")) is not int
        or collection["case_count"] != len(fixtures)
        or collection.get("app_reachable_valid_count") != 0
    ):
        raise ValueError("step11_scope_legacy_collection_count_mismatch")

    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for fixture in fixtures:
        if type(fixture) is not dict:
            raise ValueError("step11_scope_legacy_fixture_mapping_required")
        fixture_id = fixture.get("fixture_id")
        classification = fixture.get("classification")
        provenance = fixture.get("provenance_subtype")
        if (
            type(fixture_id) is not str
            or not fixture_id
            or fixture_id in seen
            or classification not in {"legacy_input", "invalid_contract"}
            or type(provenance) is not str
        ):
            raise ValueError("step11_scope_legacy_fixture_identity_invalid")
        seen.add(fixture_id)
        payload = fixture.get("legacy_payload")
        validator_issues = tuple(validate_app_reachable_input(payload))
        if classification == "invalid_contract":
            if not validator_issues:
                raise ValueError("step11_scope_contract_negative_not_rejected")
            disposition = "contract_negative_expected_rejection"
        elif validator_issues:
            disposition = "expected_non_applicable"
        else:
            disposition = "app_reachable_to_execute"
        if disposition not in _LEGACY_DISPOSITIONS:
            raise ValueError("step11_scope_legacy_disposition_invalid")
        result.append(
            {
                "fixture_id": fixture_id,
                "classification": classification,
                "provenance_subtype": provenance,
                "execution_disposition": disposition,
                "exact_validator_issue_codes": list(validator_issues),
                "disposition_contract_passed": True,
                "counts_toward_karen_minimum": False,
            }
        )
    if len(result) != collection["case_count"]:
        raise ValueError("step11_scope_legacy_disposition_incomplete")
    return sorted(result, key=lambda row: row["fixture_id"]), collection


def build_historical_rc0020_available_input_scope_receipt(
    *,
    step1_baseline_receipt: Mapping[str, Any],
    step1_input_contract: Mapping[str, Any],
    step2_corpus_registry: Mapping[str, Any],
) -> dict[str, Any]:
    """Freeze every currently available Step 11 auxiliary input scope.

    The receipt never carries an input body.  It recomputes legacy fixture
    disposition with the frozen App-Reachable validator and refuses to infer
    real-user availability from anything other than the mutually consistent
    Step 1 and Step 2 registries.
    """

    _assert_frozen_scope_parent(
        step1_baseline_receipt,
        path=STEP1_RECEIPT_PATH,
        expected_sha256=STEP1_RECEIPT_SHA256,
        validator=validate_step1,
        role="step1_baseline",
    )
    _assert_frozen_scope_parent(
        step1_input_contract,
        path=STEP1_INPUT_CONTRACT_PATH,
        expected_sha256=STEP1_INPUT_CONTRACT_SHA256,
        validator=validate_input_contract,
        role="step1_input_contract",
    )
    _assert_frozen_scope_parent(
        step2_corpus_registry,
        path=REGISTRY_PATH,
        expected_sha256=_FROZEN_STEP2_REGISTRY_SHA256,
        validator=validate_corpus_registry,
        role="step2_registry",
    )
    if (
        step2_corpus_registry.get("parent_step1_sha256")
        != STEP1_RECEIPT_SHA256
    ):
        raise ValueError("step11_scope_step2_parent_step1_mismatch")

    known_source = step1_baseline_receipt.get("known_regression_inventory")
    if type(known_source) is not list or not known_source:
        raise ValueError("step11_scope_known_inventory_missing")
    known_rows = sorted(
        (_known_regression_scope_row(row) for row in known_source),
        key=lambda row: row["regression_id"],
    )
    if len({row["regression_id"] for row in known_rows}) != len(known_rows):
        raise ValueError("step11_scope_known_inventory_duplicate")
    executable_known = [
        row for row in known_rows if row["machine_execution_required"]
    ]
    if not executable_known:
        raise ValueError("step11_scope_known_executable_inventory_empty")
    known_case_count = sum(
        int(row["registered_case_count"] or 0) for row in executable_known
    )

    legacy_rows, legacy_collection = _legacy_disposition_rows(
        step2_corpus_registry
    )
    collections = step2_corpus_registry["collections"]
    real_user_rows = [
        row
        for row in collections
        if type(row) is dict
        and row.get("classification") == "real_user_current_valid"
    ]
    if len(real_user_rows) != 1:
        raise ValueError("step11_scope_exact_one_real_user_collection_required")
    real_user = real_user_rows[0]
    intake = step1_input_contract.get("supabase_future_intake")
    if type(intake) is not dict:
        raise ValueError("step11_scope_real_user_intake_contract_missing")
    if (
        step1_baseline_receipt.get("supabase_corpus_status")
        != "not_received_not_blocking"
        or intake.get("current_status") != "not_received_not_blocking"
        or intake.get("raw_corpus_repo_allowed") is not False
        or intake.get("raw_corpus_public_receipt_allowed") is not False
        or intake.get("private_local_workspace_required") is not True
        or intake.get("current_valid_and_legacy_separated") is not True
        or real_user.get("status") != "not_received"
        or real_user.get("provenance_subtype") != "supabase_not_received"
        or real_user.get("storage") != "private_local_only"
        or real_user.get("case_count") != 0
        or real_user.get("app_reachable_valid_count") != 0
        or real_user.get("corpus_ref") is not None
        or real_user.get("corpus_sha256") is not None
        or real_user.get("raw_body_in_registry") is not False
    ):
        raise ValueError("step11_scope_real_user_zero_not_received_invalid")
    if (
        step2_corpus_registry.get("aggregate_counts", {}).get(
            "real_user_current_valid"
        )
        != 0
    ):
        raise ValueError("step11_scope_real_user_aggregate_not_zero")

    legacy_counts = {
        disposition: sum(
            row["execution_disposition"] == disposition for row in legacy_rows
        )
        for disposition in sorted(_LEGACY_DISPOSITIONS)
    }
    source_bindings = [
        {
            "role": "step1_baseline_receipt",
            "ref": _repo_ref(STEP1_RECEIPT_PATH),
            "sha256": STEP1_RECEIPT_SHA256,
        },
        {
            "role": "step1_input_contract",
            "ref": _repo_ref(STEP1_INPUT_CONTRACT_PATH),
            "sha256": STEP1_INPUT_CONTRACT_SHA256,
        },
        {
            "role": "step2_corpus_registry",
            "ref": _repo_ref(REGISTRY_PATH),
            "sha256": _FROZEN_STEP2_REGISTRY_SHA256,
        },
        {
            "role": "step2_legacy_fixture",
            "ref": _repo_ref(LEGACY_FIXTURE_PATH),
            "sha256": _FROZEN_LEGACY_FIXTURE_SHA256,
        },
    ]
    return {
        "schema_version": (
            HISTORICAL_RC0020_AVAILABLE_INPUT_SCOPE_RECEIPT_SCHEMA
        ),
        "candidate_version_id": "nls_v3_rc_0020",
        "body_free": True,
        "source_registry_bindings": source_bindings,
        "known_regression_inventory": known_rows,
        "legacy_compatibility_inventory": legacy_rows,
        "available_real_user_attestation": {
            "collection_id": real_user["collection_id"],
            "classification": "real_user_current_valid",
            "registry_status": "not_received",
            "step1_intake_status": "not_received_not_blocking",
            "available_case_count": 0,
            "app_reachable_valid_count": 0,
            "execution_disposition": "zero_available_no_execution_fabricated",
            "storage": "private_local_only",
            "raw_body_included": False,
            "attestation_status": "frozen_zero_not_received",
        },
        "scope_aggregate": {
            "known_inventory_entry_count": len(known_rows),
            "known_machine_execution_cohort_count": len(executable_known),
            "known_machine_execution_case_count": known_case_count,
            "legacy_registered_case_count": len(legacy_rows),
            "legacy_app_reachable_to_execute_count": legacy_counts[
                "app_reachable_to_execute"
            ],
            "legacy_expected_non_applicable_count": legacy_counts[
                "expected_non_applicable"
            ],
            "legacy_contract_negative_expected_rejection_count": (
                legacy_counts["contract_negative_expected_rejection"]
            ),
            "available_real_user_current_valid_count": 0,
            "registered_auxiliary_case_count": (
                known_case_count + len(legacy_rows)
            ),
        },
        "legacy_collection_binding": {
            "collection_id": legacy_collection["collection_id"],
            "case_count": legacy_collection["case_count"],
            "corpus_sha256": legacy_collection["corpus_sha256"],
            "all_registered_cases_have_explicit_disposition": True,
        },
        "completion_contract": {
            "known_regression_all_registered": True,
            "legacy_all_registered_dispositioned": True,
            "available_real_user_all_registered": True,
            "real_user_absence_not_treated_as_passed_execution": True,
            "case_specific_generation_branch_allowed": False,
            "raw_input_included": False,
        },
        "formal_status": "scope_frozen",
    }


def build_historical_rc0021_available_input_scope_receipt(
    *,
    step1_baseline_receipt: Mapping[str, Any],
    step1_input_contract: Mapping[str, Any],
    step2_corpus_registry: Mapping[str, Any],
) -> dict[str, Any]:
    """Historical rc0021 alias over the immutable rc0020 computation."""

    historical = build_historical_rc0020_available_input_scope_receipt(
        step1_baseline_receipt=step1_baseline_receipt,
        step1_input_contract=step1_input_contract,
        step2_corpus_registry=step2_corpus_registry,
    )
    return {
        **historical,
        "schema_version": (
            HISTORICAL_RC0021_AVAILABLE_INPUT_SCOPE_RECEIPT_SCHEMA
        ),
        "candidate_version_id": "nls_v3_rc_0021",
    }


def build_available_input_scope_receipt(
    *,
    step1_baseline_receipt: Mapping[str, Any],
    step1_input_contract: Mapping[str, Any],
    step2_corpus_registry: Mapping[str, Any],
) -> dict[str, Any]:
    """Current rc0027 scope alias over the immutable rc0026 alias."""

    historical = build_historical_rc0026_available_input_scope_receipt(
        step1_baseline_receipt=step1_baseline_receipt,
        step1_input_contract=step1_input_contract,
        step2_corpus_registry=step2_corpus_registry,
    )
    return {
        **historical,
        "schema_version": AVAILABLE_INPUT_SCOPE_RECEIPT_SCHEMA,
        "candidate_version_id": _STEP11_SCOPE_CANDIDATE_VERSION_ID,
    }


def build_historical_rc0026_available_input_scope_receipt(
    *,
    step1_baseline_receipt: Mapping[str, Any],
    step1_input_contract: Mapping[str, Any],
    step2_corpus_registry: Mapping[str, Any],
) -> dict[str, Any]:
    """Historical rc0026 alias over the immutable rc0025 computation."""

    historical = build_historical_rc0025_available_input_scope_receipt(
        step1_baseline_receipt=step1_baseline_receipt,
        step1_input_contract=step1_input_contract,
        step2_corpus_registry=step2_corpus_registry,
    )
    return {
        **historical,
        "schema_version": (
            HISTORICAL_RC0026_AVAILABLE_INPUT_SCOPE_RECEIPT_SCHEMA
        ),
        "candidate_version_id": "nls_v3_rc_0026",
    }


def build_historical_rc0025_available_input_scope_receipt(
    *,
    step1_baseline_receipt: Mapping[str, Any],
    step1_input_contract: Mapping[str, Any],
    step2_corpus_registry: Mapping[str, Any],
) -> dict[str, Any]:
    """Historical rc0025 alias over the immutable rc0024 computation."""

    historical = build_historical_rc0024_available_input_scope_receipt(
        step1_baseline_receipt=step1_baseline_receipt,
        step1_input_contract=step1_input_contract,
        step2_corpus_registry=step2_corpus_registry,
    )
    return {
        **historical,
        "schema_version": (
            HISTORICAL_RC0025_AVAILABLE_INPUT_SCOPE_RECEIPT_SCHEMA
        ),
        "candidate_version_id": "nls_v3_rc_0025",
    }


def build_historical_rc0024_available_input_scope_receipt(
    *,
    step1_baseline_receipt: Mapping[str, Any],
    step1_input_contract: Mapping[str, Any],
    step2_corpus_registry: Mapping[str, Any],
) -> dict[str, Any]:
    """Historical rc0024 alias over the immutable rc0023 computation."""

    historical = build_historical_rc0023_available_input_scope_receipt(
        step1_baseline_receipt=step1_baseline_receipt,
        step1_input_contract=step1_input_contract,
        step2_corpus_registry=step2_corpus_registry,
    )
    return {
        **historical,
        "schema_version": (
            HISTORICAL_RC0024_AVAILABLE_INPUT_SCOPE_RECEIPT_SCHEMA
        ),
        "candidate_version_id": "nls_v3_rc_0024",
    }


def build_historical_rc0023_available_input_scope_receipt(
    *,
    step1_baseline_receipt: Mapping[str, Any],
    step1_input_contract: Mapping[str, Any],
    step2_corpus_registry: Mapping[str, Any],
) -> dict[str, Any]:
    """Historical rc0023 alias over the immutable rc0022 computation."""

    historical = build_historical_rc0022_available_input_scope_receipt(
        step1_baseline_receipt=step1_baseline_receipt,
        step1_input_contract=step1_input_contract,
        step2_corpus_registry=step2_corpus_registry,
    )
    return {
        **historical,
        "schema_version": (
            HISTORICAL_RC0023_AVAILABLE_INPUT_SCOPE_RECEIPT_SCHEMA
        ),
        "candidate_version_id": "nls_v3_rc_0023",
    }


def build_historical_rc0022_available_input_scope_receipt(
    *,
    step1_baseline_receipt: Mapping[str, Any],
    step1_input_contract: Mapping[str, Any],
    step2_corpus_registry: Mapping[str, Any],
) -> dict[str, Any]:
    """Historical rc0022 alias over the immutable rc0021 computation."""

    historical = build_historical_rc0021_available_input_scope_receipt(
        step1_baseline_receipt=step1_baseline_receipt,
        step1_input_contract=step1_input_contract,
        step2_corpus_registry=step2_corpus_registry,
    )
    return {
        **historical,
        "schema_version": (
            HISTORICAL_RC0022_AVAILABLE_INPUT_SCOPE_RECEIPT_SCHEMA
        ),
        "candidate_version_id": "nls_v3_rc_0022",
    }


def validate_available_input_scope_receipt(
    value: Any,
    *,
    step1_baseline_receipt: Mapping[str, Any],
    step1_input_contract: Mapping[str, Any],
    step2_corpus_registry: Mapping[str, Any],
) -> tuple[str, ...]:
    if type(value) is not dict:
        return ("step11_available_input_scope_mapping_required",)
    try:
        expected = build_available_input_scope_receipt(
            step1_baseline_receipt=step1_baseline_receipt,
            step1_input_contract=step1_input_contract,
            step2_corpus_registry=step2_corpus_registry,
        )
    except (KeyError, OSError, TypeError, UnicodeError, ValueError) as exc:
        return (f"step11_available_input_scope_parent_invalid:{exc}",)
    return () if canonical_json_bytes(value) == canonical_json_bytes(expected) else (
        "step11_available_input_scope_recomputed_value_mismatch",
    )


def _build_rc0021_available_input_scope_receipt(
    *,
    step1_baseline_receipt: Mapping[str, Any],
    step1_input_contract: Mapping[str, Any],
    step2_corpus_registry: Mapping[str, Any],
) -> dict[str, Any]:
    """Compatibility name for the frozen rc0021 append-only scope alias."""

    return build_historical_rc0021_available_input_scope_receipt(
        step1_baseline_receipt=step1_baseline_receipt,
        step1_input_contract=step1_input_contract,
        step2_corpus_registry=step2_corpus_registry,
    )


def _build_rc0022_available_input_scope_receipt(
    *,
    step1_baseline_receipt: Mapping[str, Any],
    step1_input_contract: Mapping[str, Any],
    step2_corpus_registry: Mapping[str, Any],
) -> dict[str, Any]:
    """Compatibility name for the frozen rc0022 append-only scope alias."""

    return build_historical_rc0022_available_input_scope_receipt(
        step1_baseline_receipt=step1_baseline_receipt,
        step1_input_contract=step1_input_contract,
        step2_corpus_registry=step2_corpus_registry,
    )


def _build_rc0023_available_input_scope_receipt(
    *,
    step1_baseline_receipt: Mapping[str, Any],
    step1_input_contract: Mapping[str, Any],
    step2_corpus_registry: Mapping[str, Any],
) -> dict[str, Any]:
    """Compatibility name for the frozen rc0023 append-only scope alias."""

    return build_historical_rc0023_available_input_scope_receipt(
        step1_baseline_receipt=step1_baseline_receipt,
        step1_input_contract=step1_input_contract,
        step2_corpus_registry=step2_corpus_registry,
    )


def _build_rc0024_available_input_scope_receipt(
    *,
    step1_baseline_receipt: Mapping[str, Any],
    step1_input_contract: Mapping[str, Any],
    step2_corpus_registry: Mapping[str, Any],
) -> dict[str, Any]:
    """Compatibility name for the frozen rc0024 append-only scope alias."""

    return build_historical_rc0024_available_input_scope_receipt(
        step1_baseline_receipt=step1_baseline_receipt,
        step1_input_contract=step1_input_contract,
        step2_corpus_registry=step2_corpus_registry,
    )


def _build_rc0025_available_input_scope_receipt(
    *,
    step1_baseline_receipt: Mapping[str, Any],
    step1_input_contract: Mapping[str, Any],
    step2_corpus_registry: Mapping[str, Any],
) -> dict[str, Any]:
    """Compatibility name for the frozen rc0025 append-only scope alias."""

    return build_historical_rc0025_available_input_scope_receipt(
        step1_baseline_receipt=step1_baseline_receipt,
        step1_input_contract=step1_input_contract,
        step2_corpus_registry=step2_corpus_registry,
    )


def _build_rc0026_available_input_scope_receipt(
    *,
    step1_baseline_receipt: Mapping[str, Any],
    step1_input_contract: Mapping[str, Any],
    step2_corpus_registry: Mapping[str, Any],
) -> dict[str, Any]:
    """Compatibility name for the frozen rc0026 append-only scope alias."""

    return build_historical_rc0026_available_input_scope_receipt(
        step1_baseline_receipt=step1_baseline_receipt,
        step1_input_contract=step1_input_contract,
        step2_corpus_registry=step2_corpus_registry,
    )


def _build_rc0027_available_input_scope_receipt(
    *,
    step1_baseline_receipt: Mapping[str, Any],
    step1_input_contract: Mapping[str, Any],
    step2_corpus_registry: Mapping[str, Any],
) -> dict[str, Any]:
    """Compatibility name for the current rc0027 append-only scope alias."""

    return build_available_input_scope_receipt(
        step1_baseline_receipt=step1_baseline_receipt,
        step1_input_contract=step1_input_contract,
        step2_corpus_registry=step2_corpus_registry,
    )


def _normalise(value: str) -> str:
    return " ".join(value.replace("\r\n", "\n").replace("\r", "\n").split())


def _input_string_leaves(value: Any) -> list[str]:
    """Return only literal values carried by an input payload."""

    if type(value) is str:
        return [value] if _normalise(value) else []
    if type(value) is dict:
        return [
            text
            for key in sorted(value)
            for text in _input_string_leaves(value[key])
        ]
    if type(value) in {list, tuple}:
        return [text for item in value for text in _input_string_leaves(item)]
    return []


def _workaround_scan_input_material(
    samples: Sequence[Mapping[str, Any]],
) -> tuple[list[str], dict[str, Any]]:
    """Load every available input cohort without emitting a raw body.

    Raw literals live only for the duration of the scanner call.  The public
    scope binds their frozen source hashes and exact scan counts, never their
    values.
    """

    corpus_bytes = b"".join(
        canonical_json_bytes(dict(row)) + b"\n" for row in samples
    )
    if (
        type(samples) not in {list, tuple}
        or len(samples) != 100
        or hashlib.sha256(corpus_bytes).hexdigest()
        != _FROZEN_BATCH001_CORPUS_SHA256
    ):
        raise ValueError("step11_workaround_karen100_source_invalid")
    karen_inputs = [row.get("input") for row in samples]
    if any(type(value) is not dict for value in karen_inputs):
        raise ValueError("step11_workaround_karen100_input_invalid")

    _verify_known28_source_files()
    known_cases = tuple(load_baseline_cases())
    if len(known_cases) != 28 or len({row.case_id for row in known_cases}) != 28:
        raise ValueError("step11_workaround_known28_source_invalid")
    known_inputs = [dict(row.current_input) for row in known_cases]

    development_cases = _load_frozen_development42_cases()
    development_inputs = [dict(row.current_input) for row in development_cases]

    if _sha256_file(LEGACY_FIXTURE_PATH) != _FROZEN_LEGACY_FIXTURE_SHA256:
        raise ValueError("step11_workaround_legacy_source_drift")
    legacy_rows = load_canonical_jsonl(LEGACY_FIXTURE_PATH, validator=None)
    if len(legacy_rows) != 3 or any(type(row) is not dict for row in legacy_rows):
        raise ValueError("step11_workaround_legacy_source_invalid")
    legacy_inputs = [row.get("legacy_payload") for row in legacy_rows]
    if any(type(value) is not dict for value in legacy_inputs):
        raise ValueError("step11_workaround_legacy_payload_invalid")

    cohort_values = (
        (
            "karen_batch001",
            karen_inputs,
            [
                {
                    "path": (
                        "ai/tests/fixtures/emlis_nls_v3/generated/"
                        "batch_001.jsonl"
                    ),
                    "sha256": _FROZEN_BATCH001_CORPUS_SHA256,
                }
            ],
        ),
        (
            "known28",
            known_inputs,
            [
                {"path": path, "sha256": sha256}
                for path, sha256 in sorted(
                    FROZEN_KNOWN28_SOURCE_FILE_SHA256.items()
                )
            ],
        ),
        (
            "development42",
            development_inputs,
            [
                {
                    "path": (
                        "ai/tests/local_only/"
                        "emlis_nls_v2_s2_development42_20260713.json"
                    ),
                    "sha256": FROZEN_DEVELOPMENT42_SOURCE_FILE_SHA256,
                },
                {
                    "path": "ai/tests/helpers/emlis_nls_v2_s2_development.py",
                    "sha256": FROZEN_DEVELOPMENT42_LOADER_SHA256,
                },
            ],
        ),
        (
            "legacy3",
            legacy_inputs,
            [
                {
                    "path": _repo_ref(LEGACY_FIXTURE_PATH),
                    "sha256": _FROZEN_LEGACY_FIXTURE_SHA256,
                }
            ],
        ),
    )
    all_literals: list[str] = []
    cohort_rows: list[dict[str, Any]] = []
    for cohort, inputs, source_files in cohort_values:
        literals = [
            text for value in inputs for text in _input_string_leaves(value)
        ]
        normalized = [_normalise(text) for text in literals]
        scanned = [text for text in normalized if len(text) >= 12]
        if not scanned:
            raise ValueError(f"step11_workaround_{cohort}_literal_scope_empty")
        all_literals.extend(literals)
        cohort_rows.append(
            {
                "cohort": cohort,
                "case_count": len(inputs),
                "input_literal_count": len(literals),
                "scanned_literal_count": len(scanned),
                "unique_scanned_literal_count": len(set(scanned)),
                "source_file_hashes": source_files,
            }
        )
    normalized_all = [_normalise(text) for text in all_literals]
    scanned_all = [text for text in normalized_all if len(text) >= 12]
    scope = {
        "schema_version": _WORKAROUND_SCAN_INPUT_SCOPE_SCHEMA,
        "candidate_version_id": _STEP11_SCOPE_CANDIDATE_VERSION_ID,
        "scan_policy_sha256": WORKAROUND_NEGATIVE_POLICY_SHA256,
        "cohorts": cohort_rows,
        "aggregate": {
            "cohort_count": len(cohort_rows),
            "case_count": sum(row["case_count"] for row in cohort_rows),
            "input_literal_count": len(all_literals),
            "scanned_literal_count": len(scanned_all),
            "unique_scanned_literal_count": len(set(scanned_all)),
        },
        "raw_input_included": False,
        "body_free": True,
    }
    return all_literals, scope


def _string_expression(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and type(node.value) is str:
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _string_expression(node.left)
        right = _string_expression(node.right)
        return left + right if left is not None and right is not None else None
    if isinstance(node, ast.JoinedStr):
        parts: list[str] = []
        for value in node.values:
            if not isinstance(value, ast.Constant) or type(value.value) is not str:
                return None
            parts.append(value.value)
        return "".join(parts)
    return None


def _source_literals(tree: ast.AST) -> list[str]:
    direct = [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and type(node.value) is str
    ]
    combined = [
        value
        for node in ast.walk(tree)
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.NamedExpr))
        for value in [_string_expression(node.value)]
        if value is not None
    ]
    return direct + combined


def _control_nodes(tree: ast.AST) -> list[ast.AST]:
    nodes: list[ast.AST] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.IfExp, ast.While, ast.Assert)):
            nodes.append(node.test)
        elif isinstance(node, ast.Match):
            nodes.append(node.subject)
            nodes.extend(case.pattern for case in node.cases)
    return nodes


def _control_identifiers(nodes: Sequence[ast.AST]) -> set[str]:
    identifiers: set[str] = set()
    for root in nodes:
        for node in ast.walk(root):
            if isinstance(node, ast.Name):
                identifiers.add(node.id)
            elif isinstance(node, ast.Attribute):
                identifiers.add(node.attr)
            elif isinstance(node, ast.Constant) and type(node.value) is str:
                identifiers.add(node.value)
    return identifiers


def _scan_one_source(
    source: str,
    *,
    input_texts: Sequence[str],
) -> dict[str, int]:
    try:
        tree = ast.parse(source)
    except (SyntaxError, UnicodeError) as exc:
        raise ValueError("step11_workaround_scanner_source_invalid") from exc
    literals = _source_literals(tree)
    control_nodes = _control_nodes(tree)
    control_identifiers = _control_identifiers(control_nodes)
    control_strings = {
        value
        for root in control_nodes
        for node in ast.walk(root)
        for value in (_string_expression(node),)
        if value is not None
    }
    control_dump = "\n".join(
        ast.dump(node, include_attributes=False) for node in control_nodes
    )
    normalized_inputs = tuple(
        text for text in (_normalise(value) for value in input_texts) if len(text) >= 12
    )
    counts = {dimension: 0 for dimension in _DIMENSIONS}
    all_identifiers = {
        value
        for node in ast.walk(tree)
        for value in (
            (node.id,) if isinstance(node, ast.Name) else
            (node.attr,) if isinstance(node, ast.Attribute) else ()
        )
    }
    if (
        "case_id" in all_identifiers
        or "nls3s_b001_" in control_dump
        or any("nls3s_b001_" in value for value in control_strings)
        or any("nls3s_b001_" in value for value in literals)
        or (
            any("nls3s_" in value for value in literals)
            and any("b001_" in value for value in literals)
        )
    ):
        counts["case_id_branch"] += 1
    coverage_tokens = {
        "coverage",
        "coverage_family",
        "semantic_contract",
    }
    if (
        control_identifiers & coverage_tokens
        or any(value.lower() in coverage_tokens for value in literals)
        or "family" in control_strings
    ):
        counts["coverage_family_branch"] += 1
    counts["expected_output_literal"] += sum(
        bool(
            re.search(
                r"expected_(?:final|output|response|text)|completed_sentence|gold_answer",
                value,
                flags=re.IGNORECASE,
            )
        )
        for value in literals
    )
    counts["expected_output_literal"] += sum(
        bool(
            re.fullmatch(
                r"(?i)(?:expected_(?:output|response|final_text)|gold_answer|completed_sentence)",
                identifier,
            )
        )
        for identifier in all_identifiers
    )
    counts["fixed_sentence_literal"] += sum(
        "見えたこと：" in value and "Emlisから：" in value for value in literals
    )
    for value in literals:
        normalized = _normalise(value)
        if len(normalized) < 12:
            continue
        if any(
            normalized == source_text or normalized in source_text
            for source_text in normalized_inputs
        ):
            counts["input_specific_literal"] += 1
    for node in ast.walk(tree):
        lookup_or_branch = isinstance(node, ast.Subscript) or (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in {"get", "setdefault", "__getitem__"}
        )
        material = ast.dump(node, include_attributes=False).lower()
        input_hash_compare = isinstance(node, ast.Compare) and (
            any(
                isinstance(child, ast.Constant)
                and type(child.value) is str
                and _SHA_RE.fullmatch(child.value) is not None
                for child in ast.walk(node)
            )
            or any(
                isinstance(child, ast.Name)
                and any(
                    token in child.id.lower()
                    for token in ("override", "special_case", "allowlist")
                )
                for child in ast.walk(node)
            )
            or any(
                isinstance(child, (ast.Dict, ast.List, ast.Set, ast.Tuple))
                for child in ast.walk(node)
            )
        )
        if not lookup_or_branch and not input_hash_compare:
            continue
        if "case_id" in material:
            counts["case_id_branch"] += 1
        if "input" in material and any(
            token in material for token in ("sha", "hash", "digest")
        ):
            counts["input_specific_literal"] += 1
    return counts


def scan_case_specific_workarounds(
    dependency_manifest: Mapping[str, Any],
    samples: Sequence[Mapping[str, Any]],
) -> tuple[dict[str, int], str, dict[str, bool], dict[str, Any]]:
    input_texts, input_scope = _workaround_scan_input_material(samples)
    totals = {dimension: 0 for dimension in _DIMENSIONS}
    declared = {
        row["path"]: row["sha256"] for row in dependency_manifest["file_hashes"]
    }
    for relative_path, expected_sha in declared.items():
        path = REPO_ROOT / relative_path
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected_sha:
            raise ValueError("step11_workaround_scan_dependency_drift")
        if path.name not in _GENERATION_OWNER_NAMES:
            continue
        source = raw.decode("utf-8", errors="strict")
        counts = _scan_one_source(source, input_texts=input_texts)
        for dimension in _DIMENSIONS:
            totals[dimension] += counts[dimension]

    first = next(
        value for value in input_texts if len(_normalise(value)) >= 12
    )
    midpoint = max(1, len(first) // 2)
    attacks = {
        "case_id_control_branch": (
            "case_id_branch",
            "if case_id == 'nls3s_b001_0001':\n    value = 1\n",
        ),
        "case_id_override_lookup": (
            "case_id_branch",
            "value = OVERRIDES.get(case_id)\n",
        ),
        "case_id_split_control_branch": (
            "case_id_branch",
            "if cid == 'nls3s_' + 'b001_0001':\n    value = 1\n",
        ),
        "coverage_family_control_branch": (
            "coverage_family_branch",
            "if coverage['family'] == 'thought_only':\n    value = 1\n",
        ),
        "coverage_family_subscript_branch": (
            "coverage_family_branch",
            "if meta['family'] == 'thought_only':\n    value = 1\n",
        ),
        "expected_output_identifier": (
            "expected_output_literal",
            "EXPECTED_OUTPUT = '完成文'\n",
        ),
        "fixed_body_split_literal": (
            "fixed_sentence_literal",
            "VALUE = '見えたこと：\\n固定' + '\\n\\nEmlisから：\\n固定'\n",
        ),
        "input_hash_override_lookup": (
            "input_specific_literal",
            "value = OVERRIDES.get(input_sha256)\n",
        ),
        "input_literal_direct": (
            "input_specific_literal",
            f"VALUE = {first!r}\n",
        ),
        "input_literal_split_concatenation": (
            "input_specific_literal",
            f"VALUE = {first[:midpoint]!r} + {first[midpoint:]!r}\n",
        ),
    }
    attack_results: dict[str, bool] = {}
    for attack_id, (dimension, source) in attacks.items():
        result = _scan_one_source(source, input_texts=input_texts)
        attack_results[attack_id] = result[dimension] > 0
    if not all(attack_results.values()):
        raise ValueError("step11_workaround_scanner_negative_attack_missed")
    return (
        totals,
        WORKAROUND_NEGATIVE_POLICY_SHA256,
        attack_results,
        input_scope,
    )


def _failure_layer(codes: Sequence[str]) -> str:
    values = set(codes)
    if values & {"EXECUTION_EXCEPTION", "NO_RESPONSE"}:
        return "runtime"
    if "NO_VALID_CANDIDATE" in values:
        return "selector"
    if "RELATION_DIRECTION_REVERSED" in values:
        return "discourse"
    if "DEPTH_MISMATCH" in values:
        return "discourse"
    if values & {
        "FALSE_UNDERSTANDING_COMPLETION",
        "UNKNOWN_BOUNDARY_FILLED",
        "SELF_DENIAL_ADOPTED_OR_AMPLIFIED",
        "UNSUPPORTED_CAUSE_OR_PERSONALITY_OR_DIAGNOSIS",
    }:
        return "matcher"
    if values & {
        "EMLIS_RECEPTION_UNBOUND",
        "IMMEDIATE_OBSERVATION_NOT_READ",
        "REQUIRED_MEANING_MISSING",
    }:
        return "content"
    return "renderer"


def _correction_owner_paths(layer: str) -> list[str]:
    owners = {
        "content": [
            "ai/services/ai_inference/emlis_ai_step11_semantic_overlay_v3.py",
            "ai/services/ai_inference/emlis_ai_step11_natural_surface_v3.py",
        ],
        "discourse": [
            "ai/services/ai_inference/emlis_ai_step11_natural_surface_v3.py",
        ],
        "matcher": [
            "ai/services/ai_inference/emlis_ai_step11_hard_gate_v3.py",
            "ai/services/ai_inference/emlis_ai_step11_natural_surface_matcher_v3.py",
        ],
        "renderer": [
            "ai/services/ai_inference/emlis_ai_step11_natural_surface_v3.py",
            "ai/services/ai_inference/emlis_ai_step11_surface_catalog_v3.py",
        ],
        "runtime": [
            "ai/services/ai_inference/emlis_ai_step11_runtime_adapter_v3.py",
        ],
        "selector": [
            "ai/services/ai_inference/emlis_ai_step11_hard_gate_v3.py",
            "ai/services/ai_inference/emlis_ai_step11_runtime_adapter_v3.py",
        ],
    }
    return sorted(owners[layer])


def _regression_risk_codes(codes: Sequence[str]) -> list[str]:
    risks = {
        "BODY_PARSER_DIVERGENCE",
        "NATURALNESS_REGRESSION",
        "SEMANTIC_COVERAGE_REGRESSION",
    }
    values = set(codes)
    if "RELATION_DIRECTION_REVERSED" in values:
        risks.add("RELATION_DIRECTION_REGRESSION")
    if values & {
        "FALSE_UNDERSTANDING_COMPLETION",
        "UNKNOWN_BOUNDARY_FILLED",
    }:
        risks.add("UNKNOWN_BOUNDARY_REGRESSION")
    if "SELF_DENIAL_ADOPTED_OR_AMPLIFIED" in values:
        risks.add("SELF_DENIAL_SCOPE_REGRESSION")
    return sorted(risks)


def _common_cause_codes(codes: Sequence[str]) -> list[str]:
    by_failure = {
        "DEPTH_MISMATCH": "discourse_depth_selection_mismatch",
        "EMLIS_RECEPTION_UNBOUND": "reception_not_bound_to_observation",
        "EXECUTION_EXCEPTION": "runtime_execution_failed",
        "FALSE_UNDERSTANDING_COMPLETION": (
            "false_understanding_completion_not_prevented"
        ),
        "IMMEDIATE_OBSERVATION_NOT_READ": "source_nucleus_not_surface_bound",
        "NO_RESPONSE": "runtime_response_missing",
        "NO_VALID_CANDIDATE": "selector_no_valid_candidate",
        "RELATION_DIRECTION_REVERSED": "relation_endpoint_direction_mismatch",
        "REQUIRED_MEANING_MISSING": "required_obligation_not_realised",
        "SECTIONS_SEMANTICALLY_DUPLICATED": (
            "section_semantic_distinctness_lost"
        ),
        "SELF_DENIAL_ADOPTED_OR_AMPLIFIED": (
            "self_denial_boundary_not_preserved"
        ),
        "SURFACE_DISTRIBUTION_OVERCONCENTRATED": (
            "surface_family_selection_collapse"
        ),
        "SURFACE_UNNATURAL_OR_REPETITIVE": "internal_surface_abstraction_leak",
        "UNKNOWN_BOUNDARY_FILLED": "unknown_boundary_not_preserved",
        "UNSUPPORTED_CAUSE_OR_PERSONALITY_OR_DIAGNOSIS": (
            "unsupported_inference_not_filtered"
        ),
    }
    return sorted({by_failure[code] for code in codes})


def _correction_strategy_codes(codes: Sequence[str]) -> list[str]:
    by_failure = {
        "DEPTH_MISMATCH": "select_proportional_discourse_depth",
        "EMLIS_RECEPTION_UNBOUND": "bind_reception_to_source_nucleus",
        "EXECUTION_EXCEPTION": "stabilize_runtime_execution",
        "FALSE_UNDERSTANDING_COMPLETION": (
            "prevent_false_understanding_completion"
        ),
        "IMMEDIATE_OBSERVATION_NOT_READ": "retain_source_nucleus_observation",
        "NO_RESPONSE": "restore_runtime_response_delivery",
        "NO_VALID_CANDIDATE": "restore_candidate_selection_path",
        "RELATION_DIRECTION_REVERSED": "preserve_relation_endpoints_direction",
        "REQUIRED_MEANING_MISSING": "realise_required_obligations",
        "SECTIONS_SEMANTICALLY_DUPLICATED": (
            "separate_section_semantic_contributions"
        ),
        "SELF_DENIAL_ADOPTED_OR_AMPLIFIED": (
            "preserve_self_denial_source_scope"
        ),
        "SURFACE_DISTRIBUTION_OVERCONCENTRATED": (
            "rebalance_surface_family_selection"
        ),
        "SURFACE_UNNATURAL_OR_REPETITIVE": (
            "render_exact_source_nuclei_naturally"
        ),
        "UNKNOWN_BOUNDARY_FILLED": "preserve_unknown_boundary_scope",
        "UNSUPPORTED_CAUSE_OR_PERSONALITY_OR_DIAGNOSIS": (
            "reject_unsupported_semantic_atom"
        ),
    }
    return sorted({by_failure[code] for code in codes})


def _change_rows(initial_review: Mapping[str, Any]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[str]] = {}
    for row in initial_review["rows"]:
        review = row["review"]
        severity = review["severity"]
        if severity not in {"BLOCKER", "MAJOR"}:
            continue
        for failure_code in review["reason_codes"]:
            key = (severity, failure_code)
            groups.setdefault(key, []).append(
                review["case_identity_commitment"]
            )
    result = []
    for (severity, failure_code), commitments in sorted(groups.items()):
        codes = (failure_code,)
        layer = _failure_layer(codes)
        owners = _correction_owner_paths(layer)
        hypothesis = {
            "schema_version": "cocolon.emlis.nls_v3.shared_failure_hypothesis.v2",
            "owner_scope": "step11_common_structural_owner",
            "failure_layer": layer,
            "severity": severity,
            "failure_codes": list(codes),
            "common_cause_codes": _common_cause_codes(codes),
            "correction_strategy_codes": _correction_strategy_codes(codes),
            "affected_owner_paths": owners,
            "applies_to_case_count": len(commitments),
        }
        result.append(
            {
                "failure_case_commitments": sorted(commitments),
                "failure_layer": layer,
                "severity": severity,
                "failure_codes": list(codes),
                "shared_structural_hypothesis": hypothesis,
                "shared_structural_hypothesis_commitment": artifact_sha256(
                    hypothesis
                ),
                "correction_owner_paths": owners,
                "regression_risk_codes": _regression_risk_codes(codes),
                "negative_test_ids": list(_LEDGER_NEGATIVE_TEST_IDS),
            }
        )
    if not result:
        raise ValueError("step11_corrected_cycle_requires_blocking_change_rows")
    return result


def _lineage_artifacts_by_candidate(
    values: Sequence[Mapping[str, Any]],
    *,
    expected_candidates: frozenset[str],
    role: str,
) -> dict[str, dict[str, Any]]:
    if type(values) not in {list, tuple}:
        raise ValueError(f"step11_lineage_{role}_sequence_required")
    result: dict[str, dict[str, Any]] = {}
    for value in values:
        if type(value) is not dict:
            raise ValueError(f"step11_lineage_{role}_mapping_required")
        candidate = value.get("candidate_version_id")
        if type(candidate) is not str or candidate in result:
            raise ValueError(f"step11_lineage_{role}_candidate_invalid")
        result[candidate] = dict(value)
    if set(result) != expected_candidates:
        raise ValueError(
            f"step11_lineage_{role}_candidate_set_invalid:"
            f"{sorted(result)}"
        )
    return result


def _body_free_support_commitment(value: Mapping[str, Any]) -> str:
    if type(value) is not dict or value.get("body_free") is not True:
        raise ValueError("step11_lineage_support_body_free_required")
    return artifact_sha256(value)


def _validated_product_read_failure(
    value: Mapping[str, Any] | None,
    *,
    schema_version: str,
    candidate_version_id: str,
    batch_summary_sha256: str,
    failure_axis_codes: Sequence[str],
    failure_reason_codes: Sequence[str],
    failure_case_ids: Sequence[str] | None = None,
    maximum_severity: str = "MAJOR",
    exact_parent_receipt_sha256s: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    row = dict(value) if type(value) is dict else {}
    expected_keys = {
        "schema_version",
        "candidate_version_id",
        "batch_summary_sha256",
        "review_outcome",
        "maximum_severity",
        "failure_axis_codes",
        "failure_reason_codes",
        "body_free",
    }
    if failure_case_ids is not None:
        expected_keys.add("failure_case_ids")
    expected_parent_receipts = dict(exact_parent_receipt_sha256s or {})
    expected_keys.update(expected_parent_receipts)
    if (
        set(row) != expected_keys
        or row.get("schema_version") != schema_version
        or row.get("candidate_version_id") != candidate_version_id
        or row.get("batch_summary_sha256") != batch_summary_sha256
        or row.get("review_outcome") != "failed"
        or row.get("maximum_severity") != maximum_severity
        or row.get("failure_axis_codes") != list(failure_axis_codes)
        or row.get("failure_reason_codes") != list(failure_reason_codes)
        or any(
            row.get(name) != sha256
            for name, sha256 in expected_parent_receipts.items()
        )
        or (
            failure_case_ids is not None
            and row.get("failure_case_ids") != list(failure_case_ids)
        )
        or row.get("body_free") is not True
    ):
        raise ValueError(
            f"step11_lineage_{candidate_version_id[-4:]}_"
            "product_read_failure_required"
        )
    return row


def _validate_frozen_rc0021_private_verification(
    value: Mapping[str, Any],
) -> None:
    if (
        type(value) is not dict
        or artifact_sha256(value)
        != FROZEN_RC0021_PREFLIGHT_PRIVATE_VERIFICATION_SHA256
        or value.get("candidate_version_id") != "nls_v3_rc_0021"
        or value.get("source_dependency_closure_sha256")
        != FROZEN_RC0021_PREFLIGHT_SOURCE_CLOSURE_SHA256
        or value.get("final_batch_summary_sha256")
        != FROZEN_RC0021_PREFLIGHT_BATCH_SUMMARY_SHA256
        or value.get("verified_case_count") != 100
        or value.get("verified_selected_count") != 100
        or value.get("verified_no_valid_candidate_count") != 0
        or value.get("verified_exception_count") != 0
        or value.get("private_packet_validation_status") != "clean"
        or value.get("body_free") is not True
        or "hmac_key_hex" in value
        or "commitment_key" in value
    ):
        raise ValueError(
            "step11_finalize_exact_rc0021_private_verification_required"
        )


def _validate_frozen_rc0022_private_verification(
    value: Mapping[str, Any],
) -> None:
    """Require the exact body-free verification of the failed rc0022 run."""

    if (
        type(value) is not dict
        or artifact_sha256(value)
        != FROZEN_RC0022_FORMAL_PRIVATE_VERIFICATION_SHA256
        or value.get("candidate_version_id") != "nls_v3_rc_0022"
        or value.get("source_dependency_closure_sha256")
        != FROZEN_RC0022_FORMAL_SOURCE_CLOSURE_SHA256
        or value.get("final_batch_summary_sha256")
        != FROZEN_RC0022_FORMAL_BATCH_SUMMARY_SHA256
        or value.get("verified_case_count") != 100
        or value.get("verified_selected_count") != 0
        or value.get("verified_no_valid_candidate_count") != 5
        or value.get("verified_exception_count") != 95
        or value.get("private_packet_validation_status") != "clean"
        or value.get("body_free") is not True
        or "hmac_key_hex" in value
        or "commitment_key" in value
    ):
        raise ValueError(
            "step11_finalize_exact_rc0022_private_verification_required"
        )


def _validate_frozen_rc0023_private_verification(
    value: Mapping[str, Any],
) -> None:
    """Require the exact body-free verification of the clean rc0023 run."""

    if (
        type(value) is not dict
        or artifact_sha256(value)
        != FROZEN_RC0023_FORMAL_PRIVATE_VERIFICATION_SHA256
        or value.get("candidate_version_id") != "nls_v3_rc_0023"
        or value.get("dependency_manifest_sha256")
        != FROZEN_RC0023_FORMAL_MANIFEST_ARTIFACT_SHA256
        or value.get("source_dependency_closure_sha256")
        != FROZEN_RC0023_FORMAL_SOURCE_CLOSURE_SHA256
        or value.get("final_batch_summary_sha256")
        != FROZEN_RC0023_FORMAL_BATCH_SUMMARY_SHA256
        or value.get("verified_case_count") != 100
        or value.get("verified_selected_count") != 100
        or value.get("verified_no_valid_candidate_count") != 0
        or value.get("verified_exception_count") != 0
        or value.get("private_packet_validation_status") != "clean"
        or value.get("body_free") is not True
        or "hmac_key_hex" in value
        or "commitment_key" in value
    ):
        raise ValueError(
            "step11_finalize_exact_rc0023_private_verification_required"
        )


def _validate_frozen_rc0024_private_verification(
    value: Mapping[str, Any],
) -> None:
    """Require the exact body-free verification of the clean rc0024 run."""

    if (
        type(value) is not dict
        or artifact_sha256(value)
        != FROZEN_RC0024_FORMAL_PRIVATE_VERIFICATION_SHA256
        or value.get("candidate_version_id") != "nls_v3_rc_0024"
        or value.get("dependency_manifest_sha256")
        != FROZEN_RC0024_FORMAL_MANIFEST_ARTIFACT_SHA256
        or value.get("source_dependency_closure_sha256")
        != FROZEN_RC0024_FORMAL_SOURCE_CLOSURE_SHA256
        or value.get("final_batch_summary_sha256")
        != FROZEN_RC0024_FORMAL_BATCH_SUMMARY_SHA256
        or value.get("verified_case_count") != 100
        or value.get("verified_selected_count") != 100
        or value.get("verified_no_valid_candidate_count") != 0
        or value.get("verified_exception_count") != 0
        or value.get("private_packet_validation_status") != "clean"
        or value.get("body_free") is not True
        or "hmac_key_hex" in value
        or "commitment_key" in value
    ):
        raise ValueError(
            "step11_finalize_exact_rc0024_private_verification_required"
        )


def _validate_frozen_rc0025_private_verification(
    value: Mapping[str, Any],
) -> None:
    """Require the exact body-free verification of the clean rc0025 run."""

    if (
        type(value) is not dict
        or artifact_sha256(value)
        != FROZEN_RC0025_FORMAL_PRIVATE_VERIFICATION_SHA256
        or value.get("candidate_version_id") != "nls_v3_rc_0025"
        or value.get("dependency_manifest_sha256")
        != FROZEN_RC0025_FORMAL_MANIFEST_ARTIFACT_SHA256
        or value.get("source_dependency_closure_sha256")
        != FROZEN_RC0025_FORMAL_SOURCE_CLOSURE_SHA256
        or value.get("final_batch_summary_sha256")
        != FROZEN_RC0025_FORMAL_BATCH_SUMMARY_SHA256
        or value.get("verified_case_count") != 100
        or value.get("verified_selected_count") != 100
        or value.get("verified_no_valid_candidate_count") != 0
        or value.get("verified_exception_count") != 0
        or value.get("private_packet_validation_status") != "clean"
        or value.get("body_free") is not True
        or "hmac_key_hex" in value
        or "commitment_key" in value
    ):
        raise ValueError(
            "step11_finalize_exact_rc0025_private_verification_required"
        )


def _validate_frozen_rc0026_private_verification(
    value: Mapping[str, Any],
) -> None:
    """Require rc0026's exact machine-clean body-free verification."""

    if (
        type(value) is not dict
        or artifact_sha256(value)
        != FROZEN_RC0026_FORMAL_PRIVATE_VERIFICATION_SHA256
        or value.get("schema_version")
        != "cocolon.emlis.nls_v3.private_verification_receipt.step11.v1"
        or value.get("candidate_version_id") != "nls_v3_rc_0026"
        or value.get("dependency_manifest_sha256")
        != FROZEN_RC0026_FORMAL_MANIFEST_ARTIFACT_SHA256
        or value.get("source_dependency_closure_sha256")
        != FROZEN_RC0026_FORMAL_SOURCE_CLOSURE_SHA256
        or value.get("final_batch_summary_sha256")
        != FROZEN_RC0026_FORMAL_BATCH_SUMMARY_SHA256
        or value.get("verified_case_count") != 100
        or value.get("verified_selected_count") != 100
        or value.get("verified_no_valid_candidate_count") != 0
        or value.get("verified_exception_count") != 0
        or value.get("private_packet_validation_status") != "clean"
        or value.get("body_free") is not True
        or "hmac_key_hex" in value
        or "commitment_key" in value
    ):
        raise ValueError(
            "step11_finalize_exact_rc0026_private_verification_required"
        )


def _validated_frozen_rc0025_regression_bindings(
    *,
    known28_receipt: Mapping[str, Any],
    development42_receipt: Mapping[str, Any],
    invalid16_receipt: Mapping[str, Any],
    final_batch_summary: Mapping[str, Any],
    dependency_manifest: Mapping[str, Any],
) -> dict[str, str]:
    """Validate and bind the exact clean rc0025 regression receipts."""

    known_issues = validate_known28_receipt(
        known28_receipt,
        final_batch_summary=final_batch_summary,
        final_dependency_manifest=dependency_manifest,
    )
    development_issues = validate_development42_receipt(
        development42_receipt,
        final_batch_summary=final_batch_summary,
        dependency_manifest=dependency_manifest,
    )
    invalid_issues = validate_invalid16_receipt(
        invalid16_receipt,
        final_batch_summary=final_batch_summary,
        final_dependency_manifest=dependency_manifest,
    )
    bindings = {
        "known28_receipt_sha256": artifact_sha256(known28_receipt),
        "development42_receipt_sha256": artifact_sha256(
            development42_receipt
        ),
        "invalid16_receipt_sha256": artifact_sha256(invalid16_receipt),
    }
    run_ids = (
        final_batch_summary.get("run_id"),
        known28_receipt.get("run_id"),
        development42_receipt.get("run_id"),
        invalid16_receipt.get("run_id"),
    )
    if (
        known_issues
        or development_issues
        or invalid_issues
        or bindings
        != {
            "known28_receipt_sha256": (
                FROZEN_RC0025_KNOWN28_RECEIPT_SHA256
            ),
            "development42_receipt_sha256": (
                FROZEN_RC0025_DEVELOPMENT42_RECEIPT_SHA256
            ),
            "invalid16_receipt_sha256": (
                FROZEN_RC0025_INVALID16_RECEIPT_SHA256
            ),
        }
        or any(type(run_id) is not str or not run_id for run_id in run_ids)
        or len(set(run_ids)) != 4
    ):
        raise ValueError(
            "step11_finalize_exact_rc0025_regression_receipts_required"
        )
    return bindings


def _validated_frozen_rc0026_regression_bindings(
    *,
    known28_receipt: Mapping[str, Any],
    development42_receipt: Mapping[str, Any],
    invalid16_receipt: Mapping[str, Any],
    final_batch_summary: Mapping[str, Any],
    dependency_manifest: Mapping[str, Any],
) -> dict[str, str]:
    """Bind exact clean rc0026 regressions without overriding Product Read."""

    receipts = (
        known28_receipt,
        development42_receipt,
        invalid16_receipt,
    )
    expected_schemas = (
        "cocolon.emlis.nls_v3.known28_receipt.v3",
        "cocolon.emlis.nls_v3.development42_receipt.step11.v1",
        "cocolon.emlis.nls_v3.invalid16_receipt.v2",
    )
    bindings = {
        "known28_receipt_sha256": artifact_sha256(known28_receipt),
        "development42_receipt_sha256": artifact_sha256(
            development42_receipt
        ),
        "invalid16_receipt_sha256": artifact_sha256(invalid16_receipt),
    }
    run_ids = (
        final_batch_summary.get("run_id"),
        *(receipt.get("run_id") for receipt in receipts),
    )
    if (
        bindings
        != {
            "known28_receipt_sha256": (
                FROZEN_RC0026_KNOWN28_RECEIPT_SHA256
            ),
            "development42_receipt_sha256": (
                FROZEN_RC0026_DEVELOPMENT42_RECEIPT_SHA256
            ),
            "invalid16_receipt_sha256": (
                FROZEN_RC0026_INVALID16_RECEIPT_SHA256
            ),
        }
        or any(
            type(receipt) is not dict
            or receipt.get("schema_version") != expected_schema
            or receipt.get("candidate_version_id") != "nls_v3_rc_0026"
            or receipt.get("final_batch_summary_sha256")
            != FROZEN_RC0026_FORMAL_BATCH_SUMMARY_SHA256
            or receipt.get("source_dependency_closure_sha256")
            != FROZEN_RC0026_FORMAL_SOURCE_CLOSURE_SHA256
            or receipt.get("formal_status") != "clean"
            or receipt.get("body_free") is not True
            for receipt, expected_schema in zip(receipts, expected_schemas)
        )
        or any(type(run_id) is not str or not run_id for run_id in run_ids)
        or len(set(run_ids)) != 4
    ):
        raise ValueError(
            "step11_finalize_exact_rc0026_regression_receipts_required"
        )
    return bindings


def _build_rc0010_rc0021_lineage(
    *,
    initial_summary: Mapping[str, Any],
    initial_review: Mapping[str, Any],
    final_summary: Mapping[str, Any],
    dependency_manifest: Mapping[str, Any],
    historical_dependency_manifests: Sequence[Mapping[str, Any]],
    historical_batch_run_summaries: Sequence[Mapping[str, Any]],
    workaround_scan_input_scope: Mapping[str, Any],
    rc0020_product_read_failure: Mapping[str, Any] | None,
    rc0021_product_read_failure: Mapping[str, Any] | None = None,
    rc0022_private_verification_receipt: Mapping[str, Any] | None = None,
    rc0023_private_verification_receipt: Mapping[str, Any] | None = None,
    rc0024_private_verification_receipt: Mapping[str, Any] | None = None,
    rc0025_private_verification_receipt: Mapping[str, Any] | None = None,
    rc0025_product_read_failure: Mapping[str, Any] | None = None,
    rc0025_known28_receipt: Mapping[str, Any] | None = None,
    rc0025_development42_receipt: Mapping[str, Any] | None = None,
    rc0025_invalid16_receipt: Mapping[str, Any] | None = None,
    rc0026_private_verification_receipt: Mapping[str, Any] | None = None,
    rc0026_product_read_failure: Mapping[str, Any] | None = None,
    rc0026_known28_receipt: Mapping[str, Any] | None = None,
    rc0026_development42_receipt: Mapping[str, Any] | None = None,
    rc0026_invalid16_receipt: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    """Build an honest append-only history from retained receipts only."""

    rc0027_parents = (
        rc0026_private_verification_receipt,
        rc0026_product_read_failure,
        rc0026_known28_receipt,
        rc0026_development42_receipt,
        rc0026_invalid16_receipt,
    )
    rc0027_mode = all(value is not None for value in rc0027_parents)
    if any(value is not None for value in rc0027_parents) and not rc0027_mode:
        raise ValueError(
            "step11_lineage_complete_rc0026_formal_parent_set_required"
        )
    rc0026_parents = (
        rc0025_private_verification_receipt,
        rc0025_product_read_failure,
        rc0025_known28_receipt,
        rc0025_development42_receipt,
        rc0025_invalid16_receipt,
    )
    rc0026_mode = all(value is not None for value in rc0026_parents)
    if any(value is not None for value in rc0026_parents) and not rc0026_mode:
        raise ValueError(
            "step11_lineage_complete_rc0025_formal_parent_set_required"
        )
    rc0025_mode = rc0024_private_verification_receipt is not None
    rc0024_mode = rc0023_private_verification_receipt is not None
    rc0023_mode = rc0022_private_verification_receipt is not None
    rc0022_mode = rc0021_product_read_failure is not None
    rc0021_mode = rc0020_product_read_failure is not None
    if rc0027_mode and not rc0026_mode:
        raise ValueError("step11_lineage_rc0025_parent_set_required")
    if rc0026_mode and not rc0025_mode:
        raise ValueError("step11_lineage_rc0024_private_parent_required")
    if rc0025_mode and not rc0024_mode:
        raise ValueError("step11_lineage_rc0023_private_parent_required")
    if rc0024_mode and not rc0023_mode:
        raise ValueError("step11_lineage_rc0022_private_parent_required")
    if rc0023_mode and not rc0022_mode:
        raise ValueError("step11_lineage_rc0021_product_read_parent_required")
    if rc0022_mode and not rc0021_mode:
        raise ValueError("step11_lineage_rc0020_product_read_parent_required")
    current_candidate = (
        "nls_v3_rc_0027"
        if rc0027_mode
        else "nls_v3_rc_0026"
        if rc0026_mode
        else "nls_v3_rc_0025"
        if rc0025_mode
        else "nls_v3_rc_0024"
        if rc0024_mode
        else "nls_v3_rc_0023"
        if rc0023_mode
        else "nls_v3_rc_0022"
        if rc0022_mode
        else "nls_v3_rc_0021"
        if rc0021_mode
        else "nls_v3_rc_0020"
    )
    current_number = int(current_candidate.rsplit("_", 1)[1])
    historical_manifest_candidates = frozenset(
        candidate
        for candidate in _HISTORICAL_LINEAGE_MANIFEST_CANDIDATES
        if int(candidate.rsplit("_", 1)[1]) < current_number
    )
    historical_summary_candidates = frozenset(
        candidate
        for candidate in _HISTORICAL_LINEAGE_SUMMARY_CANDIDATES
        if int(candidate.rsplit("_", 1)[1]) < current_number
    )

    manifest_by_candidate = _lineage_artifacts_by_candidate(
        historical_dependency_manifests,
        expected_candidates=frozenset(historical_manifest_candidates),
        role="historical_manifest",
    )
    summary_by_candidate = _lineage_artifacts_by_candidate(
        historical_batch_run_summaries,
        expected_candidates=frozenset(historical_summary_candidates),
        role="historical_summary",
    )
    if (
        initial_summary.get("candidate_version_id") != "nls_v3_rc_0010"
        or final_summary.get("candidate_version_id") != current_candidate
        or dependency_manifest.get("candidate_version_id")
        != current_candidate
    ):
        raise ValueError("step11_lineage_fixed_endpoint_candidate_invalid")
    rc0020_manifest = manifest_by_candidate.get("nls_v3_rc_0020")
    rc0020_summary = summary_by_candidate.get("nls_v3_rc_0020")
    if rc0021_mode and (
        rc0020_manifest is None
        or artifact_sha256(rc0020_manifest)
        != FROZEN_RC0020_PREFLIGHT_MANIFEST_ARTIFACT_SHA256
        or rc0020_manifest.get("source_dependency_closure_sha256")
        != FROZEN_RC0020_PREFLIGHT_SOURCE_CLOSURE_SHA256
        or rc0020_summary is None
        or artifact_sha256(rc0020_summary)
        != FROZEN_RC0020_PREFLIGHT_BATCH_SUMMARY_SHA256
    ):
        raise ValueError("step11_lineage_exact_rc0020_preflight_required")
    rc0021_manifest = manifest_by_candidate.get("nls_v3_rc_0021")
    rc0021_summary = summary_by_candidate.get("nls_v3_rc_0021")
    if rc0022_mode and (
        rc0021_manifest is None
        or artifact_sha256(rc0021_manifest)
        != FROZEN_RC0021_PREFLIGHT_MANIFEST_ARTIFACT_SHA256
        or rc0021_manifest.get("source_dependency_closure_sha256")
        != FROZEN_RC0021_PREFLIGHT_SOURCE_CLOSURE_SHA256
        or rc0021_summary is None
        or artifact_sha256(rc0021_summary)
        != FROZEN_RC0021_PREFLIGHT_BATCH_SUMMARY_SHA256
    ):
        raise ValueError("step11_lineage_exact_rc0021_preflight_required")
    rc0022_manifest = manifest_by_candidate.get("nls_v3_rc_0022")
    rc0022_summary = summary_by_candidate.get("nls_v3_rc_0022")
    if rc0023_mode and (
        rc0022_manifest is None
        or artifact_sha256(rc0022_manifest)
        != FROZEN_RC0022_FORMAL_MANIFEST_ARTIFACT_SHA256
        or rc0022_manifest.get("source_dependency_closure_sha256")
        != FROZEN_RC0022_FORMAL_SOURCE_CLOSURE_SHA256
        or rc0022_summary is None
        or artifact_sha256(rc0022_summary)
        != FROZEN_RC0022_FORMAL_BATCH_SUMMARY_SHA256
        or rc0022_summary.get("machine_status") != "failed"
        or rc0022_summary.get("all_expected_cases_executed") is not True
        or rc0022_summary.get("executed_case_count") != 100
        or rc0022_summary.get("aggregate", {}).get("selected_count") != 0
        or rc0022_summary.get("aggregate", {}).get("exception_count") != 95
        or rc0022_summary.get("aggregate", {}).get(
            "no_valid_candidate_count"
        )
        != 5
    ):
        raise ValueError("step11_lineage_exact_rc0022_formal_failure_required")
    if rc0023_mode:
        _validate_frozen_rc0022_private_verification(
            rc0022_private_verification_receipt
        )
    rc0023_manifest = manifest_by_candidate.get("nls_v3_rc_0023")
    rc0023_summary = summary_by_candidate.get("nls_v3_rc_0023")
    if rc0024_mode and (
        rc0023_manifest is None
        or artifact_sha256(rc0023_manifest)
        != FROZEN_RC0023_FORMAL_MANIFEST_ARTIFACT_SHA256
        or rc0023_manifest.get("source_dependency_closure_sha256")
        != FROZEN_RC0023_FORMAL_SOURCE_CLOSURE_SHA256
        or rc0023_manifest.get("before_candidate_version_id")
        != "nls_v3_rc_0022"
        or rc0023_manifest.get("before_source_closure_sha256")
        != FROZEN_RC0022_FORMAL_SOURCE_CLOSURE_SHA256
        or type(rc0023_manifest.get("file_hashes")) is not list
        or len(rc0023_manifest["file_hashes"]) != 145
        or rc0023_summary is None
        or artifact_sha256(rc0023_summary)
        != FROZEN_RC0023_FORMAL_BATCH_SUMMARY_SHA256
        or rc0023_summary.get("dependency_manifest_sha256")
        != FROZEN_RC0023_FORMAL_MANIFEST_ARTIFACT_SHA256
        or rc0023_summary.get("source_dependency_closure_sha256")
        != FROZEN_RC0023_FORMAL_SOURCE_CLOSURE_SHA256
        or rc0023_summary.get("source_closure_start_sha256")
        != FROZEN_RC0023_FORMAL_SOURCE_CLOSURE_SHA256
        or rc0023_summary.get("source_closure_end_sha256")
        != FROZEN_RC0023_FORMAL_SOURCE_CLOSURE_SHA256
        or rc0023_summary.get("source_closure_stable") is not True
        or rc0023_summary.get("machine_status") != "clean"
        or rc0023_summary.get("all_expected_cases_executed") is not True
        or rc0023_summary.get("executed_case_count") != 100
        or rc0023_summary.get("aggregate", {}).get("selected_count") != 100
        or rc0023_summary.get("aggregate", {}).get(
            "no_valid_candidate_count"
        )
        != 0
        or rc0023_summary.get("aggregate", {}).get("exception_count") != 0
        or rc0023_summary.get("aggregate", {}).get("v1_fallback_count") != 0
    ):
        raise ValueError("step11_lineage_exact_rc0023_formal_clean_required")
    if rc0024_mode:
        _validate_frozen_rc0023_private_verification(
            rc0023_private_verification_receipt
        )
    rc0024_manifest = manifest_by_candidate.get("nls_v3_rc_0024")
    rc0024_summary = summary_by_candidate.get("nls_v3_rc_0024")
    if rc0025_mode and (
        rc0024_manifest is None
        or artifact_sha256(rc0024_manifest)
        != FROZEN_RC0024_FORMAL_MANIFEST_ARTIFACT_SHA256
        or rc0024_manifest.get("source_dependency_closure_sha256")
        != FROZEN_RC0024_FORMAL_SOURCE_CLOSURE_SHA256
        or rc0024_manifest.get("before_candidate_version_id")
        != "nls_v3_rc_0023"
        or rc0024_manifest.get("before_source_closure_sha256")
        != FROZEN_RC0023_FORMAL_SOURCE_CLOSURE_SHA256
        or type(rc0024_manifest.get("file_hashes")) is not list
        or len(rc0024_manifest["file_hashes"]) != 148
        or rc0024_summary is None
        or artifact_sha256(rc0024_summary)
        != FROZEN_RC0024_FORMAL_BATCH_SUMMARY_SHA256
        or rc0024_summary.get("dependency_manifest_sha256")
        != FROZEN_RC0024_FORMAL_MANIFEST_ARTIFACT_SHA256
        or rc0024_summary.get("source_dependency_closure_sha256")
        != FROZEN_RC0024_FORMAL_SOURCE_CLOSURE_SHA256
        or rc0024_summary.get("source_closure_start_sha256")
        != FROZEN_RC0024_FORMAL_SOURCE_CLOSURE_SHA256
        or rc0024_summary.get("source_closure_end_sha256")
        != FROZEN_RC0024_FORMAL_SOURCE_CLOSURE_SHA256
        or rc0024_summary.get("source_closure_stable") is not True
        or rc0024_summary.get("machine_status") != "clean"
        or rc0024_summary.get("all_expected_cases_executed") is not True
        or rc0024_summary.get("executed_case_count") != 100
        or rc0024_summary.get("aggregate", {}).get("selected_count") != 100
        or rc0024_summary.get("aggregate", {}).get(
            "no_valid_candidate_count"
        )
        != 0
        or rc0024_summary.get("aggregate", {}).get("exception_count") != 0
        or rc0024_summary.get("aggregate", {}).get("v1_fallback_count") != 0
    ):
        raise ValueError("step11_lineage_exact_rc0024_formal_clean_required")
    if rc0025_mode:
        _validate_frozen_rc0024_private_verification(
            rc0024_private_verification_receipt
        )
    rc0025_manifest = manifest_by_candidate.get("nls_v3_rc_0025")
    rc0025_summary = summary_by_candidate.get("nls_v3_rc_0025")
    if rc0026_mode and (
        rc0025_manifest is None
        or artifact_sha256(rc0025_manifest)
        != FROZEN_RC0025_FORMAL_MANIFEST_ARTIFACT_SHA256
        or rc0025_manifest.get("source_dependency_closure_sha256")
        != FROZEN_RC0025_FORMAL_SOURCE_CLOSURE_SHA256
        or rc0025_manifest.get("before_candidate_version_id")
        != "nls_v3_rc_0024"
        or rc0025_manifest.get("before_source_closure_sha256")
        != FROZEN_RC0024_FORMAL_SOURCE_CLOSURE_SHA256
        or type(rc0025_manifest.get("file_hashes")) is not list
        or len(rc0025_manifest["file_hashes"]) != 151
        or rc0025_summary is None
        or artifact_sha256(rc0025_summary)
        != FROZEN_RC0025_FORMAL_BATCH_SUMMARY_SHA256
        or rc0025_summary.get("dependency_manifest_sha256")
        != FROZEN_RC0025_FORMAL_MANIFEST_ARTIFACT_SHA256
        or rc0025_summary.get("source_dependency_closure_sha256")
        != FROZEN_RC0025_FORMAL_SOURCE_CLOSURE_SHA256
        or rc0025_summary.get("source_closure_start_sha256")
        != FROZEN_RC0025_FORMAL_SOURCE_CLOSURE_SHA256
        or rc0025_summary.get("source_closure_end_sha256")
        != FROZEN_RC0025_FORMAL_SOURCE_CLOSURE_SHA256
        or rc0025_summary.get("source_closure_stable") is not True
        or rc0025_summary.get("machine_status") != "clean"
        or rc0025_summary.get("all_expected_cases_executed") is not True
        or rc0025_summary.get("executed_case_count") != 100
        or rc0025_summary.get("aggregate", {}).get("selected_count") != 100
        or rc0025_summary.get("aggregate", {}).get(
            "no_valid_candidate_count"
        )
        != 0
        or rc0025_summary.get("aggregate", {}).get("exception_count") != 0
        or rc0025_summary.get("aggregate", {}).get("v1_fallback_count") != 0
    ):
        raise ValueError("step11_lineage_exact_rc0025_formal_clean_required")
    if rc0026_mode:
        _validate_frozen_rc0025_private_verification(
            rc0025_private_verification_receipt
        )
    product_read = (
        _validated_product_read_failure(
            rc0020_product_read_failure,
            schema_version=_RC0020_PRODUCT_READ_FAILURE_SCHEMA,
            candidate_version_id="nls_v3_rc_0020",
            batch_summary_sha256=(
                FROZEN_RC0020_PREFLIGHT_BATCH_SUMMARY_SHA256
            ),
            failure_axis_codes=("NATURAL_NON_REPETITIVE_SURFACE",),
            failure_reason_codes=("SURFACE_UNNATURAL_OR_REPETITIVE",),
        )
        if rc0021_mode
        else {}
    )
    rc0021_product_read = (
        _validated_product_read_failure(
            rc0021_product_read_failure,
            schema_version=_RC0021_PRODUCT_READ_FAILURE_SCHEMA,
            candidate_version_id="nls_v3_rc_0021",
            batch_summary_sha256=(
                FROZEN_RC0021_PREFLIGHT_BATCH_SUMMARY_SHA256
            ),
            failure_axis_codes=(
                "BOUND_EMLIS_RECEPTION",
                "IMMEDIATE_OBSERVATION_FEELS_READ",
                "NATURAL_NON_REPETITIVE_SURFACE",
            ),
            failure_reason_codes=(
                "EMLIS_RECEPTION_UNBOUND",
                "IMMEDIATE_OBSERVATION_NOT_READ",
                "SURFACE_UNNATURAL_OR_REPETITIVE",
            ),
            failure_case_ids=("nls3s_b001_0035",),
        )
        if rc0022_mode
        else {}
    )
    rc0025_product_read = (
        _validated_product_read_failure(
            rc0025_product_read_failure,
            schema_version=_RC0025_PRODUCT_READ_FAILURE_SCHEMA,
            candidate_version_id="nls_v3_rc_0025",
            batch_summary_sha256=(
                FROZEN_RC0025_FORMAL_BATCH_SUMMARY_SHA256
            ),
            failure_axis_codes=FROZEN_RC0025_PRODUCT_READ_FAILURE_AXES,
            failure_reason_codes=FROZEN_RC0025_PRODUCT_READ_FAILURE_REASONS,
            maximum_severity="BLOCKER",
            exact_parent_receipt_sha256s={
                "private_verification_receipt_sha256": (
                    FROZEN_RC0025_FORMAL_PRIVATE_VERIFICATION_SHA256
                ),
                "known28_receipt_sha256": (
                    FROZEN_RC0025_KNOWN28_RECEIPT_SHA256
                ),
                "development42_receipt_sha256": (
                    FROZEN_RC0025_DEVELOPMENT42_RECEIPT_SHA256
                ),
                "invalid16_receipt_sha256": (
                    FROZEN_RC0025_INVALID16_RECEIPT_SHA256
                ),
            },
        )
        if rc0026_mode
        else {}
    )
    if (
        rc0026_mode
        and artifact_sha256(rc0025_product_read)
        != FROZEN_RC0025_PRODUCT_READ_FAILURE_SHA256
    ):
        raise ValueError(
            "step11_lineage_exact_rc0025_product_read_failure_required"
        )
    rc0025_regression_bindings = (
        _validated_frozen_rc0025_regression_bindings(
            known28_receipt=rc0025_known28_receipt,
            development42_receipt=rc0025_development42_receipt,
            invalid16_receipt=rc0025_invalid16_receipt,
            final_batch_summary=rc0025_summary,
            dependency_manifest=rc0025_manifest,
        )
        if rc0026_mode
        else {}
    )
    rc0026_manifest = manifest_by_candidate.get("nls_v3_rc_0026")
    rc0026_summary = summary_by_candidate.get("nls_v3_rc_0026")
    if rc0027_mode and (
        rc0026_manifest is None
        or artifact_sha256(rc0026_manifest)
        != FROZEN_RC0026_FORMAL_MANIFEST_ARTIFACT_SHA256
        or rc0026_manifest.get("source_dependency_closure_sha256")
        != FROZEN_RC0026_FORMAL_SOURCE_CLOSURE_SHA256
        or rc0026_manifest.get("before_candidate_version_id")
        != "nls_v3_rc_0025"
        or rc0026_manifest.get("before_source_closure_sha256")
        != FROZEN_RC0025_FORMAL_SOURCE_CLOSURE_SHA256
        or type(rc0026_manifest.get("file_hashes")) is not list
        or len(rc0026_manifest["file_hashes"]) != 156
        or rc0026_summary is None
        or artifact_sha256(rc0026_summary)
        != FROZEN_RC0026_FORMAL_BATCH_SUMMARY_SHA256
        or rc0026_summary.get("dependency_manifest_sha256")
        != FROZEN_RC0026_FORMAL_MANIFEST_ARTIFACT_SHA256
        or rc0026_summary.get("source_dependency_closure_sha256")
        != FROZEN_RC0026_FORMAL_SOURCE_CLOSURE_SHA256
        or rc0026_summary.get("source_closure_start_sha256")
        != FROZEN_RC0026_FORMAL_SOURCE_CLOSURE_SHA256
        or rc0026_summary.get("source_closure_end_sha256")
        != FROZEN_RC0026_FORMAL_SOURCE_CLOSURE_SHA256
        or rc0026_summary.get("source_closure_stable") is not True
        or rc0026_summary.get("machine_status") != "clean"
        or rc0026_summary.get("all_expected_cases_executed") is not True
        or rc0026_summary.get("executed_case_count") != 100
        or rc0026_summary.get("aggregate", {}).get("selected_count") != 100
        or rc0026_summary.get("aggregate", {}).get(
            "no_valid_candidate_count"
        )
        != 0
        or rc0026_summary.get("aggregate", {}).get("exception_count") != 0
        or rc0026_summary.get("aggregate", {}).get("v1_fallback_count") != 0
    ):
        raise ValueError("step11_lineage_exact_rc0026_formal_clean_required")
    if rc0027_mode:
        _validate_frozen_rc0026_private_verification(
            rc0026_private_verification_receipt
        )
    rc0026_product_read = (
        _validated_product_read_failure(
            rc0026_product_read_failure,
            schema_version=_RC0026_PRODUCT_READ_FAILURE_SCHEMA,
            candidate_version_id="nls_v3_rc_0026",
            batch_summary_sha256=(
                FROZEN_RC0026_FORMAL_BATCH_SUMMARY_SHA256
            ),
            failure_axis_codes=FROZEN_RC0026_PRODUCT_READ_FAILURE_AXES,
            failure_reason_codes=FROZEN_RC0026_PRODUCT_READ_FAILURE_REASONS,
            maximum_severity="MAJOR",
            exact_parent_receipt_sha256s={
                "private_verification_receipt_sha256": (
                    FROZEN_RC0026_FORMAL_PRIVATE_VERIFICATION_SHA256
                ),
                "known28_receipt_sha256": (
                    FROZEN_RC0026_KNOWN28_RECEIPT_SHA256
                ),
                "development42_receipt_sha256": (
                    FROZEN_RC0026_DEVELOPMENT42_RECEIPT_SHA256
                ),
                "invalid16_receipt_sha256": (
                    FROZEN_RC0026_INVALID16_RECEIPT_SHA256
                ),
            },
        )
        if rc0027_mode
        else {}
    )
    if (
        rc0027_mode
        and artifact_sha256(rc0026_product_read)
        != FROZEN_RC0026_PRODUCT_READ_FAILURE_SHA256
    ):
        raise ValueError(
            "step11_lineage_exact_rc0026_product_read_failure_required"
        )
    rc0026_regression_bindings = (
        _validated_frozen_rc0026_regression_bindings(
            known28_receipt=rc0026_known28_receipt,
            development42_receipt=rc0026_development42_receipt,
            invalid16_receipt=rc0026_invalid16_receipt,
            final_batch_summary=rc0026_summary,
            dependency_manifest=rc0026_manifest,
        )
        if rc0027_mode
        else {}
    )
    manifest_by_candidate[current_candidate] = dict(dependency_manifest)
    summary_by_candidate["nls_v3_rc_0010"] = dict(initial_summary)
    summary_by_candidate[current_candidate] = dict(final_summary)
    lineage_manifests = [
        manifest_by_candidate[candidate]
        for candidate in sorted(manifest_by_candidate)
    ]
    lineage_summaries = [
        summary_by_candidate[candidate]
        for candidate in sorted(summary_by_candidate)
    ]

    initial_disposition = {
        "schema_version": (
            "cocolon.emlis.nls_v3.rc_revision_disposition_support.v1"
        ),
        "candidate_version_id": "nls_v3_rc_0010",
        "disposition": "superseded_after_observed_result",
        "initial_batch_summary_sha256": artifact_sha256(initial_summary),
        "initial_review_set_sha256": artifact_sha256(initial_review),
        "unreceipted_execution_claimed": False,
        "body_free": True,
    }
    support_rows: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = [
        {
            "event_type": "initial_run_observed",
            "candidate_version_id": "nls_v3_rc_0010",
            "batch_summary_sha256": artifact_sha256(initial_summary),
        },
        {
            "event_type": "revision_disposition",
            "candidate_version_id": "nls_v3_rc_0010",
            "disposition": "superseded_after_observed_result",
            "decision_receipt_commitment": _body_free_support_commitment(
                initial_disposition
            ),
        },
    ]
    security_sha = {
        row["path"]: row["sha256"]
        for row in dependency_manifest.get("file_hashes", [])
        if type(row) is dict
        and type(row.get("path")) is str
        and type(row.get("sha256")) is str
    }.get(_SECURITY_TEST_PATH)
    if type(security_sha) is not str or _SHA_RE.fullmatch(security_sha) is None:
        raise ValueError("step11_lineage_current_security_test_unbound")

    for number in range(11, current_number + 1):
        candidate = f"nls_v3_rc_{number:04d}"
        predecessor = f"nls_v3_rc_{number - 1:04d}"
        manifest = manifest_by_candidate.get(candidate)
        predecessor_summary = summary_by_candidate.get(predecessor)
        if manifest is not None:
            source_kind = "dependency_manifest"
            source_state = {
                "schema_version": (
                    "cocolon.emlis.nls_v3.rc_source_state_support.v1"
                ),
                "candidate_version_id": candidate,
                "source_state_kind": source_kind,
                "dependency_manifest_sha256": artifact_sha256(manifest),
                "source_dependency_closure_sha256": manifest.get(
                    "source_dependency_closure_sha256"
                ),
                "body_free": True,
            }
            source_state_artifact_sha256 = artifact_sha256(manifest)
            changed_file_set = {
                "schema_version": (
                    "cocolon.emlis.nls_v3.rc_changed_file_set_support.v1"
                ),
                "candidate_version_id": candidate,
                "evidence_status": "dependency_manifest_retained",
                "changed_file_hashes_sha256": artifact_sha256(
                    manifest.get("changed_file_hashes")
                ),
                "changed_file_count": len(manifest.get("changed_file_hashes", [])),
                "body_free": True,
            }
            changed_file_set_commitment = artifact_sha256(
                manifest.get("changed_file_hashes")
            )
        else:
            source_kind = "historical_unfrozen_no_receipt"
            source_state = {
                "schema_version": (
                    "cocolon.emlis.nls_v3.rc_source_state_support.v1"
                ),
                "candidate_version_id": candidate,
                "source_state_kind": source_kind,
                "retained_dependency_manifest": False,
                "execution_claimed": False,
                "body_free": True,
            }
            source_state_artifact_sha256 = _body_free_support_commitment(
                source_state
            )
            changed_file_set = {
                "schema_version": (
                    "cocolon.emlis.nls_v3.rc_changed_file_set_support.v1"
                ),
                "candidate_version_id": candidate,
                "evidence_status": "not_retained_as_durable_artifact",
                "changed_file_count": None,
                "execution_claimed": False,
                "body_free": True,
            }
            changed_file_set_commitment = _body_free_support_commitment(
                changed_file_set
            )

        failure_evidence = {
            "schema_version": (
                "cocolon.emlis.nls_v3.rc_failure_evidence_support.v1"
            ),
            "candidate_version_id": candidate,
            "predecessor_candidate_version_id": predecessor,
            "evidence_status": (
                "retained_batch_summary"
                if predecessor_summary is not None
                else "historical_report_without_durable_run_receipt"
            ),
            "predecessor_batch_summary_sha256": (
                artifact_sha256(predecessor_summary)
                if predecessor_summary is not None
                else None
            ),
            **(
                {
                    "predecessor_regression_receipt_sha256s": dict(
                        rc0025_regression_bindings
                    ),
                    "predecessor_product_read_failure_receipt_sha256": (
                        FROZEN_RC0025_PRODUCT_READ_FAILURE_SHA256
                    ),
                }
                if rc0026_mode and candidate == "nls_v3_rc_0026"
                else {}
            ),
            **(
                {
                    "predecessor_regression_receipt_sha256s": dict(
                        rc0026_regression_bindings
                    ),
                    "predecessor_product_read_failure_receipt_sha256": (
                        FROZEN_RC0026_PRODUCT_READ_FAILURE_SHA256
                    ),
                }
                if rc0027_mode and candidate == "nls_v3_rc_0027"
                else {}
            ),
            "unreceipted_execution_claimed": False,
            "body_free": True,
        }
        structural_hypothesis = {
            "schema_version": (
                "cocolon.emlis.nls_v3.rc_structural_hypothesis_support.v1"
            ),
            "candidate_version_id": candidate,
            "correction_scope_codes": list(
                _RC_CORRECTION_SCOPE_CODES[candidate]
            ),
            "owner_scope": "shared_structure_only",
            "case_specific_branch_allowed": False,
            "historical_run_outcome_inferred": False,
            "body_free": True,
        }
        negative_suite = {
            "schema_version": (
                "cocolon.emlis.nls_v3.rc_negative_suite_support.v1"
            ),
            "candidate_version_id": candidate,
            "evidence_status": (
                "current_frozen_suite"
                if candidate == current_candidate
                else "historical_suite_not_replayed_by_lineage_builder"
            ),
            "hard_gate_security_test_sha256": (
                security_sha if candidate == current_candidate else None
            ),
            "workaround_negative_policy_sha256": (
                WORKAROUND_NEGATIVE_POLICY_SHA256
                if candidate == current_candidate
                else None
            ),
            "workaround_scan_input_scope_sha256": (
                artifact_sha256(workaround_scan_input_scope)
                if candidate == current_candidate
                else None
            ),
            "unreceipted_execution_claimed": False,
            "body_free": True,
        }
        correction_decision = {
            "schema_version": (
                "cocolon.emlis.nls_v3.rc_correction_decision_support.v1"
            ),
            "candidate_version_id": candidate,
            "predecessor_candidate_version_id": predecessor,
            "previous_candidate_is_immutable": True,
            "new_candidate_required_for_text_affecting_change": True,
            "case_specific_branch_allowed": False,
            "execution_claimed": False,
            "body_free": True,
        }
        disposition = (
            "superseded_unexecuted"
            if candidate == "nls_v3_rc_0011"
            else "historical_unfrozen_no_receipt"
            if candidate in {
                "nls_v3_rc_0012",
                "nls_v3_rc_0013",
                "nls_v3_rc_0017",
            }
            else "cycle_final_candidate"
            if candidate == current_candidate
            else "superseded_after_observed_result"
        )
        disposition_decision = {
            "schema_version": (
                "cocolon.emlis.nls_v3.rc_revision_disposition_support.v1"
            ),
            "candidate_version_id": candidate,
            "disposition": disposition,
            "observed_batch_summary_sha256": (
                artifact_sha256(summary_by_candidate[candidate])
                if candidate in summary_by_candidate
                else None
            ),
            "unreceipted_execution_claimed": False,
            "body_free": True,
        }
        row = {
            "candidate_version_id": candidate,
            "predecessor_candidate_version_id": predecessor,
            "source_state": source_state,
            "source_state_artifact_sha256": source_state_artifact_sha256,
            "failure_evidence": failure_evidence,
            "failure_evidence_commitment": _body_free_support_commitment(
                failure_evidence
            ),
            "structural_hypothesis": structural_hypothesis,
            "structural_hypothesis_commitment": _body_free_support_commitment(
                structural_hypothesis
            ),
            "changed_file_set": changed_file_set,
            "changed_file_set_commitment": changed_file_set_commitment,
            "negative_suite": negative_suite,
            "negative_suite_commitment": _body_free_support_commitment(
                negative_suite
            ),
            "correction_decision": correction_decision,
            "correction_decision_commitment": _body_free_support_commitment(
                correction_decision
            ),
            "disposition_decision": disposition_decision,
            "disposition_decision_commitment": _body_free_support_commitment(
                disposition_decision
            ),
            "body_free": True,
        }
        support_rows.append(row)
        events.append(
            {
                "event_type": "correction_recorded",
                "candidate_version_id": candidate,
                "source_state_kind": source_kind,
                "source_state_artifact_sha256": source_state_artifact_sha256,
                "failure_evidence_commitment": row[
                    "failure_evidence_commitment"
                ],
                "structural_hypothesis_commitment": row[
                    "structural_hypothesis_commitment"
                ],
                "changed_file_set_commitment": changed_file_set_commitment,
                "negative_suite_commitment": row[
                    "negative_suite_commitment"
                ],
                "correction_decision_commitment": row[
                    "correction_decision_commitment"
                ],
            }
        )
        if candidate in summary_by_candidate:
            events.append(
                {
                    "event_type": "execution_observed",
                    "candidate_version_id": candidate,
                    "execution_scope": (
                        "preflight"
                        if candidate in {"nls_v3_rc_0018", "nls_v3_rc_0019"}
                        or (
                            rc0021_mode
                            and candidate == "nls_v3_rc_0020"
                        )
                        or (
                            rc0022_mode
                            and candidate == "nls_v3_rc_0021"
                        )
                        else "formal_cumulative_rerun"
                    ),
                    "batch_summary_sha256": artifact_sha256(
                        summary_by_candidate[candidate]
                    ),
                }
            )
        if rc0027_mode and candidate == "nls_v3_rc_0026":
            for regression_suite, receipt_commitment in (
                ("known28", FROZEN_RC0026_KNOWN28_RECEIPT_SHA256),
                (
                    "development42",
                    FROZEN_RC0026_DEVELOPMENT42_RECEIPT_SHA256,
                ),
                ("invalid16", FROZEN_RC0026_INVALID16_RECEIPT_SHA256),
            ):
                events.append(
                    {
                        "event_type": "regression_receipt_observed",
                        "candidate_version_id": candidate,
                        "batch_summary_sha256": (
                            FROZEN_RC0026_FORMAL_BATCH_SUMMARY_SHA256
                        ),
                        "regression_suite": regression_suite,
                        "receipt_commitment": receipt_commitment,
                    }
                )
        if rc0021_mode and candidate == "nls_v3_rc_0020":
            events.append(
                {
                    "event_type": "product_read_observed",
                    "candidate_version_id": candidate,
                    "batch_summary_sha256": product_read[
                        "batch_summary_sha256"
                    ],
                    "review_outcome": product_read["review_outcome"],
                    "maximum_severity": product_read["maximum_severity"],
                    "failure_axis_codes": product_read[
                        "failure_axis_codes"
                    ],
                    "failure_reason_codes": product_read[
                        "failure_reason_codes"
                    ],
                    "review_receipt_commitment": artifact_sha256(
                        product_read
                    ),
                }
            )
        if rc0022_mode and candidate == "nls_v3_rc_0021":
            events.append(
                {
                    "event_type": "product_read_observed",
                    "candidate_version_id": candidate,
                    "batch_summary_sha256": rc0021_product_read[
                        "batch_summary_sha256"
                    ],
                    "review_outcome": rc0021_product_read[
                        "review_outcome"
                    ],
                    "maximum_severity": rc0021_product_read[
                        "maximum_severity"
                    ],
                    "failure_axis_codes": rc0021_product_read[
                        "failure_axis_codes"
                    ],
                    "failure_reason_codes": rc0021_product_read[
                        "failure_reason_codes"
                    ],
                    "failure_case_ids": rc0021_product_read[
                        "failure_case_ids"
                    ],
                    "review_receipt_commitment": artifact_sha256(
                        rc0021_product_read
                    ),
                }
            )
        if rc0026_mode and candidate == "nls_v3_rc_0025":
            events.append(
                {
                    "event_type": "product_read_observed",
                    "candidate_version_id": candidate,
                    "batch_summary_sha256": rc0025_product_read[
                        "batch_summary_sha256"
                    ],
                    "review_outcome": rc0025_product_read[
                        "review_outcome"
                    ],
                    "maximum_severity": rc0025_product_read[
                        "maximum_severity"
                    ],
                    "failure_axis_codes": rc0025_product_read[
                        "failure_axis_codes"
                    ],
                    "failure_reason_codes": rc0025_product_read[
                        "failure_reason_codes"
                    ],
                    "review_receipt_commitment": artifact_sha256(
                        rc0025_product_read
                    ),
                }
            )
        if rc0027_mode and candidate == "nls_v3_rc_0026":
            events.append(
                {
                    "event_type": "product_read_observed",
                    "candidate_version_id": candidate,
                    "batch_summary_sha256": rc0026_product_read[
                        "batch_summary_sha256"
                    ],
                    "review_outcome": rc0026_product_read[
                        "review_outcome"
                    ],
                    "maximum_severity": rc0026_product_read[
                        "maximum_severity"
                    ],
                    "failure_axis_codes": rc0026_product_read[
                        "failure_axis_codes"
                    ],
                    "failure_reason_codes": rc0026_product_read[
                        "failure_reason_codes"
                    ],
                    "review_receipt_commitment": artifact_sha256(
                        rc0026_product_read
                    ),
                }
            )
        events.append(
            {
                "event_type": "revision_disposition",
                "candidate_version_id": candidate,
                "disposition": disposition,
                "decision_receipt_commitment": row[
                    "disposition_decision_commitment"
                ],
            }
        )

    correction_support = {
        "schema_version": (
            _RC_CORRECTION_SUPPORT_SCHEMA
            if rc0027_mode
            else _RC0026_CORRECTION_SUPPORT_SCHEMA
            if rc0026_mode
            else _RC0025_CORRECTION_SUPPORT_SCHEMA
            if rc0025_mode
            else _RC0024_CORRECTION_SUPPORT_SCHEMA
            if rc0024_mode
            else _RC0023_CORRECTION_SUPPORT_SCHEMA
            if rc0023_mode
            else _RC0022_CORRECTION_SUPPORT_SCHEMA
            if rc0022_mode
            else _RC0021_CORRECTION_SUPPORT_SCHEMA
            if rc0021_mode
            else "cocolon.emlis.nls_v3.rc_correction_support.step11.rc0020.v1"
        ),
        "cycle_id": "cycle_001",
        "initial_disposition": initial_disposition,
        "rows": support_rows,
        "aggregate": {
            "correction_count": len(support_rows),
            "retained_dependency_manifest_count": len(
                manifest_by_candidate
            ),
            "retained_batch_summary_count": len(summary_by_candidate),
            "historical_no_receipt_correction_count": sum(
                row["source_state"]["source_state_kind"]
                == "historical_unfrozen_no_receipt"
                for row in support_rows
            ),
            "unreceipted_execution_claim_count": 0,
        },
        "workaround_scan_input_scope_sha256": artifact_sha256(
            workaround_scan_input_scope
        ),
        **(
            {
                "rc0020_product_read_failure_receipt_sha256": (
                    artifact_sha256(product_read)
                )
            }
            if rc0021_mode
            else {}
        ),
        **(
            {
                "rc0021_product_read_failure_receipt_sha256": (
                    artifact_sha256(rc0021_product_read)
                )
            }
            if rc0022_mode
            else {}
        ),
        **(
            {
                "rc0022_private_verification_receipt_sha256": (
                    artifact_sha256(rc0022_private_verification_receipt)
                )
            }
            if rc0023_mode
            else {}
        ),
        **(
            {
                "rc0023_private_verification_receipt_sha256": (
                    artifact_sha256(rc0023_private_verification_receipt)
                )
            }
            if rc0024_mode
            else {}
        ),
        **(
            {
                "rc0024_private_verification_receipt_sha256": (
                    artifact_sha256(rc0024_private_verification_receipt)
                )
            }
            if rc0025_mode
            else {}
        ),
        **(
            {
                "rc0025_private_verification_receipt_sha256": (
                    artifact_sha256(rc0025_private_verification_receipt)
                ),
                "rc0025_product_read_failure_receipt_sha256": (
                    artifact_sha256(rc0025_product_read)
                ),
                "rc0025_regression_receipt_sha256s": dict(
                    rc0025_regression_bindings
                ),
            }
            if rc0026_mode
            else {}
        ),
        **(
            {
                "rc0026_private_verification_receipt_sha256": (
                    artifact_sha256(rc0026_private_verification_receipt)
                ),
                "rc0026_product_read_failure_receipt_sha256": (
                    artifact_sha256(rc0026_product_read)
                ),
                "rc0026_regression_receipt_sha256s": dict(
                    rc0026_regression_bindings
                ),
            }
            if rc0027_mode
            else {}
        ),
        "raw_input_included": False,
        "body_free": True,
    }
    lineage_builder = (
        build_rc0010_rc0027_correction_rerun_lineage
        if rc0027_mode
        else build_rc0010_rc0026_correction_rerun_lineage
        if rc0026_mode
        else build_rc0010_rc0025_correction_rerun_lineage
        if rc0025_mode
        else build_rc0010_rc0024_correction_rerun_lineage
        if rc0024_mode
        else build_rc0010_rc0023_correction_rerun_lineage
        if rc0023_mode
        else build_rc0010_rc0022_correction_rerun_lineage
        if rc0022_mode
        else build_rc0010_rc0021_correction_rerun_lineage
        if rc0021_mode
        else build_rc0010_rc0020_correction_rerun_lineage
    )
    lineage = lineage_builder(
        events,
        dependency_manifests=lineage_manifests,
        batch_run_summaries=lineage_summaries,
    )
    return lineage, correction_support, lineage_manifests, lineage_summaries


def _build_rc0010_rc0020_lineage(
    *,
    initial_summary: Mapping[str, Any],
    initial_review: Mapping[str, Any],
    final_summary: Mapping[str, Any],
    dependency_manifest: Mapping[str, Any],
    historical_dependency_manifests: Sequence[Mapping[str, Any]],
    historical_batch_run_summaries: Sequence[Mapping[str, Any]],
    workaround_scan_input_scope: Mapping[str, Any],
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    """Historical rc0020 finalizer lineage, retained without relabelling."""

    return _build_rc0010_rc0021_lineage(
        initial_summary=initial_summary,
        initial_review=initial_review,
        final_summary=final_summary,
        dependency_manifest=dependency_manifest,
        historical_dependency_manifests=historical_dependency_manifests,
        historical_batch_run_summaries=historical_batch_run_summaries,
        workaround_scan_input_scope=workaround_scan_input_scope,
        rc0020_product_read_failure=None,
    )


def _build_rc0010_rc0022_lineage(
    *,
    initial_summary: Mapping[str, Any],
    initial_review: Mapping[str, Any],
    final_summary: Mapping[str, Any],
    dependency_manifest: Mapping[str, Any],
    historical_dependency_manifests: Sequence[Mapping[str, Any]],
    historical_batch_run_summaries: Sequence[Mapping[str, Any]],
    workaround_scan_input_scope: Mapping[str, Any],
    rc0020_product_read_failure: Mapping[str, Any],
    rc0021_product_read_failure: Mapping[str, Any],
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    """Current rc0022 lineage over exact rc0020 and rc0021 failures."""

    return _build_rc0010_rc0021_lineage(
        initial_summary=initial_summary,
        initial_review=initial_review,
        final_summary=final_summary,
        dependency_manifest=dependency_manifest,
        historical_dependency_manifests=historical_dependency_manifests,
        historical_batch_run_summaries=historical_batch_run_summaries,
        workaround_scan_input_scope=workaround_scan_input_scope,
        rc0020_product_read_failure=rc0020_product_read_failure,
        rc0021_product_read_failure=rc0021_product_read_failure,
    )


def _build_rc0010_rc0023_lineage(
    *,
    initial_summary: Mapping[str, Any],
    initial_review: Mapping[str, Any],
    final_summary: Mapping[str, Any],
    dependency_manifest: Mapping[str, Any],
    historical_dependency_manifests: Sequence[Mapping[str, Any]],
    historical_batch_run_summaries: Sequence[Mapping[str, Any]],
    workaround_scan_input_scope: Mapping[str, Any],
    rc0020_product_read_failure: Mapping[str, Any],
    rc0021_product_read_failure: Mapping[str, Any],
    rc0022_private_verification_receipt: Mapping[str, Any],
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    """Historical rc0023 lineage over the exact failed rc0022 formal run."""

    return _build_rc0010_rc0021_lineage(
        initial_summary=initial_summary,
        initial_review=initial_review,
        final_summary=final_summary,
        dependency_manifest=dependency_manifest,
        historical_dependency_manifests=historical_dependency_manifests,
        historical_batch_run_summaries=historical_batch_run_summaries,
        workaround_scan_input_scope=workaround_scan_input_scope,
        rc0020_product_read_failure=rc0020_product_read_failure,
        rc0021_product_read_failure=rc0021_product_read_failure,
        rc0022_private_verification_receipt=(
            rc0022_private_verification_receipt
        ),
    )


def _build_rc0010_rc0024_lineage(
    *,
    initial_summary: Mapping[str, Any],
    initial_review: Mapping[str, Any],
    final_summary: Mapping[str, Any],
    dependency_manifest: Mapping[str, Any],
    historical_dependency_manifests: Sequence[Mapping[str, Any]],
    historical_batch_run_summaries: Sequence[Mapping[str, Any]],
    workaround_scan_input_scope: Mapping[str, Any],
    rc0020_product_read_failure: Mapping[str, Any],
    rc0021_product_read_failure: Mapping[str, Any],
    rc0022_private_verification_receipt: Mapping[str, Any],
    rc0023_private_verification_receipt: Mapping[str, Any],
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    """Historical rc0024 lineage over the exact clean rc0023 formal run."""

    return _build_rc0010_rc0021_lineage(
        initial_summary=initial_summary,
        initial_review=initial_review,
        final_summary=final_summary,
        dependency_manifest=dependency_manifest,
        historical_dependency_manifests=historical_dependency_manifests,
        historical_batch_run_summaries=historical_batch_run_summaries,
        workaround_scan_input_scope=workaround_scan_input_scope,
        rc0020_product_read_failure=rc0020_product_read_failure,
        rc0021_product_read_failure=rc0021_product_read_failure,
        rc0022_private_verification_receipt=(
            rc0022_private_verification_receipt
        ),
        rc0023_private_verification_receipt=(
            rc0023_private_verification_receipt
        ),
    )


def _build_rc0010_rc0025_lineage(
    *,
    initial_summary: Mapping[str, Any],
    initial_review: Mapping[str, Any],
    final_summary: Mapping[str, Any],
    dependency_manifest: Mapping[str, Any],
    historical_dependency_manifests: Sequence[Mapping[str, Any]],
    historical_batch_run_summaries: Sequence[Mapping[str, Any]],
    workaround_scan_input_scope: Mapping[str, Any],
    rc0020_product_read_failure: Mapping[str, Any],
    rc0021_product_read_failure: Mapping[str, Any],
    rc0022_private_verification_receipt: Mapping[str, Any],
    rc0023_private_verification_receipt: Mapping[str, Any],
    rc0024_private_verification_receipt: Mapping[str, Any],
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    """Historical rc0025 lineage over the exact clean rc0024 formal run."""

    return _build_rc0010_rc0021_lineage(
        initial_summary=initial_summary,
        initial_review=initial_review,
        final_summary=final_summary,
        dependency_manifest=dependency_manifest,
        historical_dependency_manifests=historical_dependency_manifests,
        historical_batch_run_summaries=historical_batch_run_summaries,
        workaround_scan_input_scope=workaround_scan_input_scope,
        rc0020_product_read_failure=rc0020_product_read_failure,
        rc0021_product_read_failure=rc0021_product_read_failure,
        rc0022_private_verification_receipt=(
            rc0022_private_verification_receipt
        ),
        rc0023_private_verification_receipt=(
            rc0023_private_verification_receipt
        ),
        rc0024_private_verification_receipt=(
            rc0024_private_verification_receipt
        ),
    )


def _build_rc0010_rc0026_lineage(
    *,
    initial_summary: Mapping[str, Any],
    initial_review: Mapping[str, Any],
    final_summary: Mapping[str, Any],
    dependency_manifest: Mapping[str, Any],
    historical_dependency_manifests: Sequence[Mapping[str, Any]],
    historical_batch_run_summaries: Sequence[Mapping[str, Any]],
    workaround_scan_input_scope: Mapping[str, Any],
    rc0020_product_read_failure: Mapping[str, Any],
    rc0021_product_read_failure: Mapping[str, Any],
    rc0022_private_verification_receipt: Mapping[str, Any],
    rc0023_private_verification_receipt: Mapping[str, Any],
    rc0024_private_verification_receipt: Mapping[str, Any],
    rc0025_private_verification_receipt: Mapping[str, Any],
    rc0025_product_read_failure: Mapping[str, Any],
    rc0025_known28_receipt: Mapping[str, Any],
    rc0025_development42_receipt: Mapping[str, Any],
    rc0025_invalid16_receipt: Mapping[str, Any],
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    """Historical rc0026 lineage over clean rc0025 and its BLOCKER review."""

    return _build_rc0010_rc0021_lineage(
        initial_summary=initial_summary,
        initial_review=initial_review,
        final_summary=final_summary,
        dependency_manifest=dependency_manifest,
        historical_dependency_manifests=historical_dependency_manifests,
        historical_batch_run_summaries=historical_batch_run_summaries,
        workaround_scan_input_scope=workaround_scan_input_scope,
        rc0020_product_read_failure=rc0020_product_read_failure,
        rc0021_product_read_failure=rc0021_product_read_failure,
        rc0022_private_verification_receipt=(
            rc0022_private_verification_receipt
        ),
        rc0023_private_verification_receipt=(
            rc0023_private_verification_receipt
        ),
        rc0024_private_verification_receipt=(
            rc0024_private_verification_receipt
        ),
        rc0025_private_verification_receipt=(
            rc0025_private_verification_receipt
        ),
        rc0025_product_read_failure=rc0025_product_read_failure,
        rc0025_known28_receipt=rc0025_known28_receipt,
        rc0025_development42_receipt=rc0025_development42_receipt,
        rc0025_invalid16_receipt=rc0025_invalid16_receipt,
    )


def _build_rc0010_rc0027_lineage(
    *,
    initial_summary: Mapping[str, Any],
    initial_review: Mapping[str, Any],
    final_summary: Mapping[str, Any],
    dependency_manifest: Mapping[str, Any],
    historical_dependency_manifests: Sequence[Mapping[str, Any]],
    historical_batch_run_summaries: Sequence[Mapping[str, Any]],
    workaround_scan_input_scope: Mapping[str, Any],
    rc0020_product_read_failure: Mapping[str, Any],
    rc0021_product_read_failure: Mapping[str, Any],
    rc0022_private_verification_receipt: Mapping[str, Any],
    rc0023_private_verification_receipt: Mapping[str, Any],
    rc0024_private_verification_receipt: Mapping[str, Any],
    rc0025_private_verification_receipt: Mapping[str, Any],
    rc0025_product_read_failure: Mapping[str, Any],
    rc0025_known28_receipt: Mapping[str, Any],
    rc0025_development42_receipt: Mapping[str, Any],
    rc0025_invalid16_receipt: Mapping[str, Any],
    rc0026_private_verification_receipt: Mapping[str, Any],
    rc0026_product_read_failure: Mapping[str, Any],
    rc0026_known28_receipt: Mapping[str, Any],
    rc0026_development42_receipt: Mapping[str, Any],
    rc0026_invalid16_receipt: Mapping[str, Any],
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    """Current rc0027 lineage over rc0026 machine-clean and Product Read failure parents."""

    return _build_rc0010_rc0021_lineage(
        initial_summary=initial_summary,
        initial_review=initial_review,
        final_summary=final_summary,
        dependency_manifest=dependency_manifest,
        historical_dependency_manifests=historical_dependency_manifests,
        historical_batch_run_summaries=historical_batch_run_summaries,
        workaround_scan_input_scope=workaround_scan_input_scope,
        rc0020_product_read_failure=rc0020_product_read_failure,
        rc0021_product_read_failure=rc0021_product_read_failure,
        rc0022_private_verification_receipt=(
            rc0022_private_verification_receipt
        ),
        rc0023_private_verification_receipt=(
            rc0023_private_verification_receipt
        ),
        rc0024_private_verification_receipt=(
            rc0024_private_verification_receipt
        ),
        rc0025_private_verification_receipt=(
            rc0025_private_verification_receipt
        ),
        rc0025_product_read_failure=rc0025_product_read_failure,
        rc0025_known28_receipt=rc0025_known28_receipt,
        rc0025_development42_receipt=rc0025_development42_receipt,
        rc0025_invalid16_receipt=rc0025_invalid16_receipt,
        rc0026_private_verification_receipt=(
            rc0026_private_verification_receipt
        ),
        rc0026_product_read_failure=rc0026_product_read_failure,
        rc0026_known28_receipt=rc0026_known28_receipt,
        rc0026_development42_receipt=rc0026_development42_receipt,
        rc0026_invalid16_receipt=rc0026_invalid16_receipt,
    )


def _validate_finalizer_regression_parents(
    *,
    final_summary: Mapping[str, Any],
    dependency_manifest: Mapping[str, Any],
    known28_receipt: Mapping[str, Any],
    development42_receipt: Mapping[str, Any],
    invalid16_receipt: Mapping[str, Any],
) -> None:
    development_issues = validate_development42_receipt(
        development42_receipt,
        final_batch_summary=final_summary,
        dependency_manifest=dependency_manifest,
    )
    if development_issues:
        raise ValueError(
            f"step11_finalize_development42_invalid:{development_issues[0]}"
        )
    run_ids = {
        "final_batch": final_summary.get("run_id"),
        "known28": known28_receipt.get("run_id"),
        "development42": development42_receipt.get("run_id"),
        "invalid16": invalid16_receipt.get("run_id"),
    }
    if (
        any(type(value) is not str or not value for value in run_ids.values())
        or len(set(run_ids.values())) != len(run_ids)
    ):
        raise ValueError(f"step11_finalize_run_ids_not_distinct:{run_ids}")


def build_cycle_artifacts(
    *,
    manifest: Mapping[str, Any],
    coverage_matrix: Mapping[str, Any],
    duplicate_report: Mapping[str, Any],
    samples: Sequence[Mapping[str, Any]],
    initial_summary: Mapping[str, Any],
    initial_decisions: Sequence[Mapping[str, Any]],
    final_summary: Mapping[str, Any],
    final_decisions: Sequence[Mapping[str, Any]],
    private_verification_receipt: Mapping[str, Any],
    dependency_manifest: Mapping[str, Any],
    known28_receipt: Mapping[str, Any],
    development42_receipt: Mapping[str, Any],
    invalid16_receipt: Mapping[str, Any],
    historical_lineage_dependency_manifests: Sequence[Mapping[str, Any]],
    historical_lineage_batch_run_summaries: Sequence[Mapping[str, Any]],
    rc0020_product_read_failure: Mapping[str, Any],
    rc0021_product_read_failure: Mapping[str, Any],
    rc0021_private_verification_receipt: Mapping[str, Any],
    rc0022_private_verification_receipt: Mapping[str, Any],
    rc0023_private_verification_receipt: Mapping[str, Any],
    rc0024_private_verification_receipt: Mapping[str, Any],
    rc0025_private_verification_receipt: Mapping[str, Any],
    rc0025_product_read_failure: Mapping[str, Any],
    rc0025_known28_receipt: Mapping[str, Any],
    rc0025_development42_receipt: Mapping[str, Any],
    rc0025_invalid16_receipt: Mapping[str, Any],
    rc0026_final_summary: Mapping[str, Any],
    rc0026_private_verification_receipt: Mapping[str, Any],
    rc0026_product_read_failure: Mapping[str, Any],
    rc0026_known28_receipt: Mapping[str, Any],
    rc0026_development42_receipt: Mapping[str, Any],
    rc0026_invalid16_receipt: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    rc0022_parents = [
        value
        for value in historical_lineage_dependency_manifests
        if type(value) is dict
        and value.get("candidate_version_id") == "nls_v3_rc_0022"
    ]
    if (
        len(rc0022_parents) != 1
        or artifact_sha256(rc0022_parents[0])
        != FROZEN_RC0022_FORMAL_MANIFEST_ARTIFACT_SHA256
        or rc0022_parents[0].get("source_dependency_closure_sha256")
        != FROZEN_RC0022_FORMAL_SOURCE_CLOSURE_SHA256
    ):
        raise ValueError(
            "step11_finalize_exact_rc0022_formal_manifest_required"
        )
    rc0023_parents = [
        value
        for value in historical_lineage_dependency_manifests
        if type(value) is dict
        and value.get("candidate_version_id") == "nls_v3_rc_0023"
    ]
    if (
        len(rc0023_parents) != 1
        or artifact_sha256(rc0023_parents[0])
        != FROZEN_RC0023_FORMAL_MANIFEST_ARTIFACT_SHA256
        or rc0023_parents[0].get("source_dependency_closure_sha256")
        != FROZEN_RC0023_FORMAL_SOURCE_CLOSURE_SHA256
        or rc0023_parents[0].get("before_candidate_version_id")
        != "nls_v3_rc_0022"
        or rc0023_parents[0].get("before_source_closure_sha256")
        != FROZEN_RC0022_FORMAL_SOURCE_CLOSURE_SHA256
        or type(rc0023_parents[0].get("file_hashes")) is not list
        or len(rc0023_parents[0]["file_hashes"]) != 145
    ):
        raise ValueError(
            "step11_finalize_exact_rc0023_formal_manifest_required"
        )
    rc0024_parents = [
        value
        for value in historical_lineage_dependency_manifests
        if type(value) is dict
        and value.get("candidate_version_id") == "nls_v3_rc_0024"
    ]
    if (
        len(rc0024_parents) != 1
        or artifact_sha256(rc0024_parents[0])
        != FROZEN_RC0024_FORMAL_MANIFEST_ARTIFACT_SHA256
        or rc0024_parents[0].get("source_dependency_closure_sha256")
        != FROZEN_RC0024_FORMAL_SOURCE_CLOSURE_SHA256
        or rc0024_parents[0].get("before_candidate_version_id")
        != "nls_v3_rc_0023"
        or rc0024_parents[0].get("before_source_closure_sha256")
        != FROZEN_RC0023_FORMAL_SOURCE_CLOSURE_SHA256
        or type(rc0024_parents[0].get("file_hashes")) is not list
        or len(rc0024_parents[0]["file_hashes"]) != 148
    ):
        raise ValueError(
            "step11_finalize_exact_rc0024_formal_manifest_required"
        )
    rc0025_parents = [
        value
        for value in historical_lineage_dependency_manifests
        if type(value) is dict
        and value.get("candidate_version_id") == "nls_v3_rc_0025"
    ]
    if (
        len(rc0025_parents) != 1
        or artifact_sha256(rc0025_parents[0])
        != FROZEN_RC0025_FORMAL_MANIFEST_ARTIFACT_SHA256
        or rc0025_parents[0].get("source_dependency_closure_sha256")
        != FROZEN_RC0025_FORMAL_SOURCE_CLOSURE_SHA256
        or rc0025_parents[0].get("before_candidate_version_id")
        != "nls_v3_rc_0024"
        or rc0025_parents[0].get("before_source_closure_sha256")
        != FROZEN_RC0024_FORMAL_SOURCE_CLOSURE_SHA256
        or type(rc0025_parents[0].get("file_hashes")) is not list
        or len(rc0025_parents[0]["file_hashes"]) != 151
    ):
        raise ValueError(
            "step11_finalize_exact_rc0025_formal_manifest_required"
        )
    rc0026_parents = [
        value
        for value in historical_lineage_dependency_manifests
        if type(value) is dict
        and value.get("candidate_version_id") == "nls_v3_rc_0026"
    ]
    rc0026_summaries = [
        value
        for value in historical_lineage_batch_run_summaries
        if type(value) is dict
        and value.get("candidate_version_id") == "nls_v3_rc_0026"
    ]
    if (
        len(rc0026_parents) != 1
        or artifact_sha256(rc0026_parents[0])
        != FROZEN_RC0026_FORMAL_MANIFEST_ARTIFACT_SHA256
        or rc0026_parents[0].get("source_dependency_closure_sha256")
        != FROZEN_RC0026_FORMAL_SOURCE_CLOSURE_SHA256
        or rc0026_parents[0].get("before_candidate_version_id")
        != "nls_v3_rc_0025"
        or rc0026_parents[0].get("before_source_closure_sha256")
        != FROZEN_RC0025_FORMAL_SOURCE_CLOSURE_SHA256
        or type(rc0026_parents[0].get("file_hashes")) is not list
        or len(rc0026_parents[0]["file_hashes"]) != 156
        or len(rc0026_summaries) != 1
        or rc0026_summaries[0] != rc0026_final_summary
        or artifact_sha256(rc0026_final_summary)
        != FROZEN_RC0026_FORMAL_BATCH_SUMMARY_SHA256
        or rc0026_final_summary.get("dependency_manifest_sha256")
        != FROZEN_RC0026_FORMAL_MANIFEST_ARTIFACT_SHA256
        or rc0026_final_summary.get("source_dependency_closure_sha256")
        != FROZEN_RC0026_FORMAL_SOURCE_CLOSURE_SHA256
        or rc0026_final_summary.get("source_closure_start_sha256")
        != FROZEN_RC0026_FORMAL_SOURCE_CLOSURE_SHA256
        or rc0026_final_summary.get("source_closure_end_sha256")
        != FROZEN_RC0026_FORMAL_SOURCE_CLOSURE_SHA256
        or rc0026_final_summary.get("source_closure_stable") is not True
        or rc0026_final_summary.get("machine_status") != "clean"
        or rc0026_final_summary.get("all_expected_cases_executed") is not True
        or rc0026_final_summary.get("executed_case_count") != 100
        or rc0026_final_summary.get("aggregate", {}).get("selected_count")
        != 100
        or rc0026_final_summary.get("aggregate", {}).get(
            "no_valid_candidate_count"
        )
        != 0
        or rc0026_final_summary.get("aggregate", {}).get("exception_count")
        != 0
        or rc0026_final_summary.get("aggregate", {}).get("v1_fallback_count")
        != 0
    ):
        raise ValueError(
            "step11_finalize_exact_rc0026_formal_public_parents_required"
        )
    _validate_frozen_rc0021_private_verification(
        rc0021_private_verification_receipt
    )
    _validate_frozen_rc0022_private_verification(
        rc0022_private_verification_receipt
    )
    _validate_frozen_rc0023_private_verification(
        rc0023_private_verification_receipt
    )
    _validate_frozen_rc0024_private_verification(
        rc0024_private_verification_receipt
    )
    _validate_frozen_rc0025_private_verification(
        rc0025_private_verification_receipt
    )
    _validate_frozen_rc0026_private_verification(
        rc0026_private_verification_receipt
    )
    current_dependency_issues = validate_current_step11_dependency_manifest(
        dependency_manifest,
        before_manifest=rc0026_parents[0],
    )
    if current_dependency_issues:
        raise ValueError(
            "step11_finalize_current_dependency_invalid:"
            + current_dependency_issues[0]
        )
    _validate_finalizer_regression_parents(
        final_summary=final_summary,
        dependency_manifest=dependency_manifest,
        known28_receipt=known28_receipt,
        development42_receipt=development42_receipt,
        invalid16_receipt=invalid16_receipt,
    )
    available_input_scope = _build_rc0027_available_input_scope_receipt(
        step1_baseline_receipt=load_step1_json(STEP1_RECEIPT_PATH),
        step1_input_contract=load_step1_json(STEP1_INPUT_CONTRACT_PATH),
        step2_corpus_registry=load_step1_json(REGISTRY_PATH),
    )
    corpus_bytes = b"".join(canonical_json_bytes(dict(row)) + b"\n" for row in samples)
    if (
        len(samples) != 100
        or hashlib.sha256(corpus_bytes).hexdigest()
        != _FROZEN_BATCH001_CORPUS_SHA256
    ):
        raise ValueError("step11_finalize_frozen_batch001_mismatch")
    declared = {
        row["path"]: row["sha256"] for row in dependency_manifest["file_hashes"]
    }
    security_test_bytes = (REPO_ROOT / _SECURITY_TEST_PATH).read_bytes()
    if hashlib.sha256(security_test_bytes).hexdigest() != declared.get(
        _SECURITY_TEST_PATH
    ):
        raise ValueError("step11_negative_test_source_drift")
    security_test_source = security_test_bytes.decode("utf-8", errors="strict")
    if any(
        re.search(rf"^def test_{re.escape(test_id)}\(", security_test_source, re.MULTILINE)
        is None
        for test_id in _LEDGER_NEGATIVE_TEST_IDS
        if test_id != "case_id_override_lookup"
    ):
        raise ValueError("step11_ledger_negative_test_missing")
    corpus = build_cycle001_corpus_validation(
        manifest, coverage_matrix, duplicate_report
    )
    lock = build_initial_run_lock(
        initial_summary,
        corpus,
        lock_id="nls3lock_0010c00100000001",
    )
    initial_review = build_local_review_set(
        lock,
        initial_summary,
        corpus,
        initial_summary,
        initial_decisions,
        review_stage="initial",
    )
    final_review = build_local_review_set(
        lock,
        initial_summary,
        corpus,
        final_summary,
        final_decisions,
        review_stage="final",
        dependency_manifest=dependency_manifest,
    )
    output_diff = build_output_diff(
        lock,
        initial_summary,
        corpus,
        final_summary,
        final_dependency_manifest=dependency_manifest,
    )
    output_review = build_output_change_review(
        lock,
        initial_summary,
        corpus,
        initial_review,
        final_summary,
        final_review,
        output_diff,
        final_dependency_manifest=dependency_manifest,
    )
    (
        scan_counts,
        negative_hash,
        negative_results,
        workaround_scan_input_scope,
    ) = scan_case_specific_workarounds(dependency_manifest, samples)
    if any(scan_counts.values()):
        raise ValueError(f"step11_case_specific_workaround_detected:{scan_counts}")
    workaround = build_case_specific_workaround_scan_receipt(
        dependency_manifest,
        scanner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        negative_test_receipt_sha256=negative_hash,
        forbidden_reference_counts=scan_counts,
        negative_test_results=negative_results,
    )
    (
        correction_rerun_lineage,
        correction_support,
        lineage_dependency_manifests,
        lineage_batch_run_summaries,
    ) = _build_rc0010_rc0027_lineage(
        initial_summary=initial_summary,
        initial_review=initial_review,
        final_summary=final_summary,
        dependency_manifest=dependency_manifest,
        historical_dependency_manifests=(
            historical_lineage_dependency_manifests
        ),
        historical_batch_run_summaries=(
            historical_lineage_batch_run_summaries
        ),
        workaround_scan_input_scope=workaround_scan_input_scope,
        rc0020_product_read_failure=rc0020_product_read_failure,
        rc0021_product_read_failure=rc0021_product_read_failure,
        rc0022_private_verification_receipt=(
            rc0022_private_verification_receipt
        ),
        rc0023_private_verification_receipt=(
            rc0023_private_verification_receipt
        ),
        rc0024_private_verification_receipt=(
            rc0024_private_verification_receipt
        ),
        rc0025_private_verification_receipt=(
            rc0025_private_verification_receipt
        ),
        rc0025_product_read_failure=rc0025_product_read_failure,
        rc0025_known28_receipt=rc0025_known28_receipt,
        rc0025_development42_receipt=rc0025_development42_receipt,
        rc0025_invalid16_receipt=rc0025_invalid16_receipt,
        rc0026_private_verification_receipt=(
            rc0026_private_verification_receipt
        ),
        rc0026_product_read_failure=rc0026_product_read_failure,
        rc0026_known28_receipt=rc0026_known28_receipt,
        rc0026_development42_receipt=rc0026_development42_receipt,
        rc0026_invalid16_receipt=rc0026_invalid16_receipt,
    )
    correction_support = {
        **correction_support,
        "rc0021_private_verification_receipt_sha256": artifact_sha256(
            rc0021_private_verification_receipt
        ),
    }
    cumulative = build_cumulative100_receipt(
        lock,
        initial_summary,
        corpus,
        initial_review,
        final_summary,
        final_review,
        private_verification_receipt,
        known28_receipt,
        invalid16_receipt,
        output_diff,
        output_review,
        development42_receipt=development42_receipt,
        available_input_scope_receipt=available_input_scope,
        correction_rerun_lineage=correction_rerun_lineage,
        lineage_dependency_manifests=lineage_dependency_manifests,
        lineage_batch_run_summaries=lineage_batch_run_summaries,
        final_dependency_manifest=dependency_manifest,
        cumulative_run_id="nls3cum_0027c00100000001",
    )
    ledger = build_cycle_change_ledger(
        lock,
        initial_summary,
        corpus,
        initial_review,
        final_summary,
        cumulative,
        _change_rows(initial_review),
        final_dependency_manifest=dependency_manifest,
        workaround_scan_receipt=workaround,
    )
    acceptance = build_cycle001_acceptance(
        lock,
        initial_summary,
        corpus,
        initial_review,
        final_summary,
        final_review,
        private_verification_receipt,
        known28_receipt,
        invalid16_receipt,
        output_diff,
        output_review,
        cumulative,
        ledger,
        manifest=manifest,
        coverage_matrix=coverage_matrix,
        duplicate_report=duplicate_report,
        development42_receipt=development42_receipt,
        available_input_scope_receipt=available_input_scope,
        correction_rerun_lineage=correction_rerun_lineage,
        lineage_dependency_manifests=lineage_dependency_manifests,
        lineage_batch_run_summaries=lineage_batch_run_summaries,
        final_dependency_manifest=dependency_manifest,
        workaround_scan_receipt=workaround,
    )
    parents = {
        "initial_lock": lock,
        "initial_batch_summary": initial_summary,
        "corpus_validation": corpus,
        "initial_review_set": initial_review,
        "final_batch_summary": final_summary,
        "final_review_set": final_review,
        "private_verification_receipt": private_verification_receipt,
        "known28_receipt": known28_receipt,
        "development42_receipt": development42_receipt,
        "available_input_scope_receipt": available_input_scope,
        "correction_rerun_lineage": correction_rerun_lineage,
        "lineage_dependency_manifests": lineage_dependency_manifests,
        "lineage_batch_run_summaries": lineage_batch_run_summaries,
        "invalid16_receipt": invalid16_receipt,
        "output_diff": output_diff,
        "output_change_review": output_review,
        "cumulative100_receipt": cumulative,
        "change_ledger": ledger,
        "manifest": manifest,
        "coverage_matrix": coverage_matrix,
        "duplicate_report": duplicate_report,
        "final_dependency_manifest": dependency_manifest,
        "workaround_scan_receipt": workaround,
    }
    if validate_cycle001_acceptance(acceptance, **parents):
        raise ValueError("step11_cycle_acceptance_recomputation_failed")
    return {
        "cycle001_available_input_scope.json": available_input_scope,
        "cycle001_corpus_validation.json": corpus,
        "cycle001_initial_run_lock.json": lock,
        "cycle001_initial_review.json": initial_review,
        "cycle001_final_review.json": final_review,
        "cycle001_output_diff.json": output_diff,
        "cycle001_output_change_review.json": output_review,
        "cycle001_workaround_scan_input_scope.json": (
            workaround_scan_input_scope
        ),
        "cycle001_workaround_scan.json": workaround,
        "cycle001_rc_correction_support.json": correction_support,
        "cycle001_rc_correction_rerun_lineage.json": (
            correction_rerun_lineage
        ),
        "cycle001_cumulative100.json": cumulative,
        "cycle001_change_ledger.json": ledger,
        "cycle001_acceptance.json": acceptance,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Finalize body-free rc0027 Cycle 001 evidence from exact "
            "machine-clean rc0026/rc0025 formal parents, three regression "
            "receipts, and ordered Product Read failures."
        )
    )
    for name in (
        "manifest",
        "coverage-matrix",
        "duplicate-report",
        "batch",
        "initial-summary",
        "initial-decisions",
        "final-summary",
        "final-decisions",
        "private-verification-receipt",
        "dependency-manifest",
        "known28-receipt",
        "development42-receipt",
        "invalid16-receipt",
        "rc0020-product-read-failure",
        "rc0021-product-read-failure",
        "rc0021-private-verification-receipt",
        "rc0022-private-verification-receipt",
        "rc0023-private-verification-receipt",
        "rc0024-private-verification-receipt",
        "rc0025-private-verification-receipt",
        "rc0025-product-read-failure",
        "rc0025-known28-receipt",
        "rc0025-development42-receipt",
        "rc0025-invalid16-receipt",
        "rc0026-final-summary",
        "rc0026-private-verification-receipt",
        "rc0026-product-read-failure",
        "rc0026-known28-receipt",
        "rc0026-development42-receipt",
        "rc0026-invalid16-receipt",
    ):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument(
        "--lineage-dependency-manifest",
        dest="lineage_dependency_manifests",
        action="append",
        type=Path,
        required=True,
        help=(
            "Repeat for retained historical manifests rc0011/14/15/16/18/19; "
            "include the exact frozen rc0020/rc0021 preflight manifests and "
            "the exact failed rc0022 plus machine-clean "
            "rc0023/rc0024/rc0025/rc0026 "
            "formal manifests; current rc0027 is appended internally."
        ),
    )
    parser.add_argument(
        "--lineage-batch-summary",
        dest="lineage_batch_summaries",
        action="append",
        type=Path,
        required=True,
        help=(
            "Repeat for retained historical summaries rc0014/15/16/18/19; "
            "include the exact frozen rc0020/rc0021 preflight summaries and "
            "the exact failed rc0022 plus machine-clean "
            "rc0023/rc0024/rc0025/rc0026 "
            "formal summaries; rc0010 and current rc0027 are appended."
        ),
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    artifacts = build_cycle_artifacts(
        manifest=load_canonical_json(args.manifest),
        coverage_matrix=load_canonical_json(args.coverage_matrix),
        duplicate_report=load_canonical_json(args.duplicate_report),
        samples=load_canonical_jsonl(args.batch),
        initial_summary=load_canonical_json(args.initial_summary),
        initial_decisions=load_canonical_json(args.initial_decisions),
        final_summary=load_canonical_json(args.final_summary),
        final_decisions=load_canonical_json(args.final_decisions),
        private_verification_receipt=load_canonical_json(
            args.private_verification_receipt
        ),
        dependency_manifest=load_canonical_json(args.dependency_manifest),
        known28_receipt=load_canonical_json(args.known28_receipt),
        development42_receipt=load_canonical_json(
            args.development42_receipt
        ),
        invalid16_receipt=load_canonical_json(args.invalid16_receipt),
        historical_lineage_dependency_manifests=[
            load_canonical_json(path)
            for path in args.lineage_dependency_manifests
        ],
        historical_lineage_batch_run_summaries=[
            load_canonical_json(path)
            for path in args.lineage_batch_summaries
        ],
        rc0020_product_read_failure=load_canonical_json(
            args.rc0020_product_read_failure
        ),
        rc0021_product_read_failure=load_canonical_json(
            args.rc0021_product_read_failure
        ),
        rc0021_private_verification_receipt=load_canonical_json(
            args.rc0021_private_verification_receipt
        ),
        rc0022_private_verification_receipt=load_canonical_json(
            args.rc0022_private_verification_receipt
        ),
        rc0023_private_verification_receipt=load_canonical_json(
            args.rc0023_private_verification_receipt
        ),
        rc0024_private_verification_receipt=load_canonical_json(
            args.rc0024_private_verification_receipt
        ),
        rc0025_private_verification_receipt=load_canonical_json(
            args.rc0025_private_verification_receipt
        ),
        rc0025_product_read_failure=load_canonical_json(
            args.rc0025_product_read_failure
        ),
        rc0025_known28_receipt=load_canonical_json(
            args.rc0025_known28_receipt
        ),
        rc0025_development42_receipt=load_canonical_json(
            args.rc0025_development42_receipt
        ),
        rc0025_invalid16_receipt=load_canonical_json(
            args.rc0025_invalid16_receipt
        ),
        rc0026_final_summary=load_canonical_json(
            args.rc0026_final_summary
        ),
        rc0026_private_verification_receipt=load_canonical_json(
            args.rc0026_private_verification_receipt
        ),
        rc0026_product_read_failure=load_canonical_json(
            args.rc0026_product_read_failure
        ),
        rc0026_known28_receipt=load_canonical_json(
            args.rc0026_known28_receipt
        ),
        rc0026_development42_receipt=load_canonical_json(
            args.rc0026_development42_receipt
        ),
        rc0026_invalid16_receipt=load_canonical_json(
            args.rc0026_invalid16_receipt
        ),
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    paths = [args.output_dir / name for name in artifacts]
    if any(path.exists() for path in paths):
        raise ValueError("step11_finalize_output_already_exists")
    for name, artifact in artifacts.items():
        _write_json(args.output_dir / name, artifact, private=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
