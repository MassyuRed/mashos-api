#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""Run Cycle 001 rc0023 Known28, Development42 and invalid regressions."""

import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any, Mapping, Sequence


AI_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = AI_ROOT.parent
SERVICES = AI_ROOT / "services" / "ai_inference"
HELPERS = AI_ROOT / "tests" / "helpers"
TESTS = AI_ROOT / "tests"
TOOLS = AI_ROOT / "tools"
for entry in (SERVICES, TESTS, HELPERS, TOOLS):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

from emlis_ai_reply_service import render_emlis_ai_reply  # noqa: E402
from emlis_ai_nls_v3_artifact_contract import artifact_sha256  # noqa: E402
from emlis_ai_step10_app_reachable_contract_v3 import (  # noqa: E402
    project_app_reachable_input,
    validate_app_reachable_input,
)
from emlis_ai_step10_evidence_v3 import (  # noqa: E402
    assert_body_free,
    commitment_key_id,
    hmac_commit_bytes,
)
from emlis_ai_step11_cycle_evidence_v3 import (  # noqa: E402
    FROZEN_KNOWN28_EXPECTED_APPLICABILITY_SHA256,
    INVALID16_EXPECTED_INVENTORY,
    KNOWN28_EXPECTED_APPLICABILITY,
    KNOWN28_GENERIC_PROJECTION_POLICY,
    KNOWN28_GENERIC_PROJECTION_POLICY_SHA256,
    build_invalid16_receipt,
    build_known28_receipt,
    validate_step11_batch_run_summary,
    validate_step11_dependency_manifest,
    validate_invalid16_inventory_contract,
    validate_known28_applicability_contract,
)
from emlis_ai_step11_natural_surface_v3 import (  # noqa: E402
    STEP11_CANDIDATE_VERSION_ID,
)
from emlis_ai_step11_runtime_adapter_v3 import (  # noqa: E402
    execute_step11_offline_v3,
    validate_step11_runtime_execution,
)
from emlis_nls_v3_batch_run import (  # noqa: E402
    _read_key,
    _secure_unlink,
    _write_json,
)
from emlis_nls_v3_step11_dependency_manifest import (  # noqa: E402
    assert_current_step11_dependency_manifest,
)
from emlis_nls_v3_step11_batch_run import _commit_json  # noqa: E402
from emlis_nls_v3_s0_s1_baseline import load_baseline_cases  # noqa: E402
from emlis_nls_v2_s2_development import (  # noqa: E402
    DEVELOPMENT_FIXTURE_PATH,
    load_development_cases,
)
from emlis_nls_v3_s2_sample_registry import (  # noqa: E402
    load_canonical_json,
    load_canonical_jsonl,
)


STEP11_KNOWN28_PRIVATE_SCHEMA = (
    "cocolon.emlis.nls_v3.known28_private_packet.step11.v2"
)
STEP11_DEVELOPMENT42_PRIVATE_SCHEMA = (
    "cocolon.emlis.nls_v3.development42_private_packet.step11.v1"
)
STEP11_DEVELOPMENT42_RECEIPT_SCHEMA = (
    "cocolon.emlis.nls_v3.development42_receipt.step11.v1"
)
_LEGACY_INPUT_KEYS = frozenset(
    {"memo", "memo_action", "emotions", "category"}
)
_PRIVATE_CASE_KEYS = frozenset(
    {
        "case_ref",
        "cohort",
        "family",
        "legacy_current_input",
        "projected_current_input",
        "applicability_status",
        "applicability_issue_codes",
        "v1_body",
        "v3_body",
    }
)
_APPLICABILITY_STATUSES = frozenset(
    {"app_reachable", "expected_non_applicable"}
)
_LEGACY_COMMITMENT_DOMAIN = "step11_known28_legacy_input"
_PROJECTED_COMMITMENT_DOMAIN = "step11_known28_projected_input"
_APPLICABILITY_BINDING_DOMAIN = "step11_known28_applicability_binding"
_STEP1_INPUT_CONTRACT_RELATIVE_PATH = (
    "ai/tests/fixtures/emlis_nls_v3_s1_input_contract_20260714.json"
)
_STEP1_INPUT_CONTRACT_SHA256 = (
    "d577ac80457e25389c0bac351139b2c80a9a506f225023fb7928a1b9068d53c6"
)
FROZEN_DEVELOPMENT42_SOURCE_FILE_SHA256 = (
    "9e8e81b553b8f3d5d51e66c434350ebbc2fa134a813250dbb5bc5de251e6aa36"
)
FROZEN_DEVELOPMENT42_LOADER_SHA256 = (
    "cf29cbebceea3c4489adc00bb7744aa0c29b43a1376cd9d5ce2809aa0f58f140"
)
FROZEN_DEVELOPMENT42_EXPECTED_APPLICABILITY_SHA256 = (
    "080972e62ff982014e8b4198294d3d5e713fe1621cb3619e2f9f22e70276d407"
)
FROZEN_INVALID16_FILE_SHA256 = (
    "d7cbc344701635d53da21ebb2814a9c8d814cf1c403392b506ece6c00e6e5b77"
)
_INVALID16_FIXTURE_WRAPPER_KEYS = frozenset(
    {"expected_issue", "fixture_id", "input"}
)
FROZEN_KNOWN28_SOURCE_FILE_SHA256 = {
    _STEP1_INPUT_CONTRACT_RELATIVE_PATH: _STEP1_INPUT_CONTRACT_SHA256,
    "ai/tests/fixtures/grounded_human_reception_exact8_v2_20260712.json": (
        "cb601019dc2c7e4e46281133d3965addf04adf4f6af8defaf715f91f522e3efb"
    ),
    "ai/tests/local_only/grounded_human_reception_rr8_unseen12_20260713.json": (
        "d53740015a091898d776caec56d11517ff7d4aaf44c5a48172cde54ef3cb132d"
    ),
    "ai/tests/helpers/emlis_ai_grounded_observation_i6_cases.py": (
        "6d36cb6fc2de9bbbb0120747332e771fd7be39dcc86966e447f2ebea4cde2966"
    ),
}

_DEVELOPMENT42_LOADER_RELATIVE_PATH = (
    "ai/tests/helpers/emlis_nls_v2_s2_development.py"
)
_DEVELOPMENT42_SOURCE_RELATIVE_PATH = (
    "ai/tests/local_only/emlis_nls_v2_s2_development42_20260713.json"
)
_DEVELOPMENT42_CASE_RE = re.compile(r"^NLS2-F(0[1-9]|1[0-4])-D0[1-3]$")
_RUN_ID_RE = re.compile(r"^nls3run_[0-9a-f]{16,64}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_DEVELOPMENT42_PRIVATE_CASE_KEYS = frozenset(
    {
        "case_ref",
        "cohort",
        "family",
        "legacy_current_input",
        "projected_current_input",
        "applicability_status",
        "applicability_issue_codes",
        "v1_body",
        "v3_body",
    }
)
_DEVELOPMENT42_PUBLIC_ROW_KEYS = frozenset(
    {
        "case_ref",
        "family",
        "legacy_input_commitment",
        "projected_input_commitment",
        "applicability_binding_commitment",
        "applicability_status",
        "applicability_issue_codes",
        "v1_baseline_body_commitment",
        "selected_candidate_body_commitment",
        "status",
        "hard_gate_status",
        "failure_codes",
        "exception",
        "v1_fallback_used",
    }
)
_DEVELOPMENT42_LEGACY_COMMITMENT_DOMAIN = (
    "step11_development42_legacy_input"
)
_DEVELOPMENT42_PROJECTED_COMMITMENT_DOMAIN = (
    "step11_development42_projected_input"
)
_DEVELOPMENT42_APPLICABILITY_BINDING_DOMAIN = (
    "step11_development42_applicability_binding"
)


def _verify_known28_source_files() -> None:
    repo = AI_ROOT.parent
    for relative_path, expected in FROZEN_KNOWN28_SOURCE_FILE_SHA256.items():
        actual = hashlib.sha256((repo / relative_path).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f"step11_known28_source_drift:{relative_path}")


def _verify_known28_projection_contract() -> dict[str, dict[str, Any]]:
    """Validate the frozen generic policy and expected applicability ledger."""

    if (
        validate_known28_applicability_contract()
        or artifact_sha256(KNOWN28_GENERIC_PROJECTION_POLICY)
        != KNOWN28_GENERIC_PROJECTION_POLICY_SHA256
        or artifact_sha256(KNOWN28_EXPECTED_APPLICABILITY)
        != FROZEN_KNOWN28_EXPECTED_APPLICABILITY_SHA256
    ):
        raise ValueError("step11_known28_projection_contract_hash_drift")
    step1 = json.loads(
        (REPO_ROOT / _STEP1_INPUT_CONTRACT_RELATIVE_PATH).read_text(
            encoding="utf-8"
        )
    )
    backend = step1.get("backend_compatibility_boundary")
    fixture_boundary = step1.get("baseline_fixture_boundary")
    if (
        type(backend) is not dict
        or backend.get("legacy_string_emotion_accepted") is not True
        or backend.get("unknown_strength_coerced_to_medium") is not True
        or backend.get("backend_permissiveness_is_app_valid_authority")
        is not False
        or type(fixture_boundary) is not dict
        or fixture_boundary.get(
            "known_fixture_string_emotions_are_legacy_comparison_inputs"
        )
        is not True
        or fixture_boundary.get(
            "known_fixture_strength_omission_is_not_app_contract_authority"
        )
        is not True
    ):
        raise ValueError("step11_known28_step1_compatibility_basis_invalid")
    inventory = KNOWN28_EXPECTED_APPLICABILITY
    if (
        type(inventory) is not dict
        or inventory.get("projection_policy_sha256")
        != KNOWN28_GENERIC_PROJECTION_POLICY_SHA256
        or inventory.get("classification_source")
        != "frozen_regression_input_contract_only"
        or inventory.get("body_free") is not True
        or inventory.get("counts")
        != {"app_reachable": 19, "expected_non_applicable": 9}
        or type(inventory.get("cases")) is not list
        or len(inventory["cases"]) != 28
    ):
        raise ValueError("step11_known28_expected_applicability_invalid")
    by_ref: dict[str, dict[str, Any]] = {}
    for row in inventory["cases"]:
        if (
            type(row) is not dict
            or set(row)
            != {
                "case_ref",
                "applicability_status",
                "expected_issue_codes",
            }
            or type(row.get("case_ref")) is not str
            or row.get("applicability_status") not in _APPLICABILITY_STATUSES
            or type(row.get("expected_issue_codes")) is not list
            or any(type(code) is not str or not code for code in row["expected_issue_codes"])
            or row["case_ref"] in by_ref
            or (
                row["applicability_status"] == "app_reachable"
                and row["expected_issue_codes"]
            )
            or (
                row["applicability_status"] == "expected_non_applicable"
                and not row["expected_issue_codes"]
            )
        ):
            raise ValueError("step11_known28_expected_applicability_row_invalid")
        by_ref[row["case_ref"]] = dict(row)
    return by_ref


def _copy_legacy_current_input(value: Mapping[str, Any]) -> dict[str, Any]:
    """Copy a structurally valid legacy input without normalising any value."""

    if type(value) is not dict or set(value) != _LEGACY_INPUT_KEYS:
        raise ValueError("step11_known28_legacy_input_shape_invalid")
    emotions = value.get("emotions")
    categories = value.get("category")
    if type(emotions) is not list or type(categories) is not list:
        raise ValueError("step11_known28_legacy_input_shape_invalid")
    return {
        "memo": value.get("memo"),
        "memo_action": value.get("memo_action"),
        "emotions": list(emotions),
        "category": list(categories),
    }


def project_legacy_regression_input(
    value: Any,
) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    """Mechanically project a legacy regression input, then apply App rules.

    This adapter has no case, family, or source-text input.  It never trims,
    deduplicates, replaces values, or supplies text.  The sole compatibility
    default is the Step 1 backend's historical strength omission value,
    ``medium``; the projected value is then judged by the existing frozen
    App-Reachable validator.
    """

    if type(value) is not dict:
        return None, ("legacy_input:mapping_required",)
    if set(value) != _LEGACY_INPUT_KEYS:
        return None, ("legacy_input:keyset_mismatch",)
    if type(value.get("memo")) is not str:
        return None, ("legacy_input.memo:string_required",)
    if type(value.get("memo_action")) is not str:
        return None, ("legacy_input.memo_action:string_required",)
    emotions = value.get("emotions")
    if type(emotions) is not list:
        return None, ("legacy_input.emotions:array_required",)
    if any(type(item) is not str for item in emotions):
        return None, ("legacy_input.emotions:string_items_required",)
    categories = value.get("category")
    if type(categories) is not list:
        return None, ("legacy_input.category:array_required",)
    if any(type(item) is not str for item in categories):
        return None, ("legacy_input.category:string_items_required",)
    projected = {
        "thought_text": value["memo"],
        "action_text": value["memo_action"],
        "emotions": [
            {"type": item, "strength": "medium"} for item in emotions
        ],
        "categories": list(categories),
    }
    issues = validate_app_reachable_input(projected)
    if issues:
        return projected, issues
    # Reuse the frozen projector as a second, exact defensive copy only after
    # the independent validator has accepted the mechanical projection.
    return project_app_reachable_input(projected), ()


def project_known28_legacy_input(
    value: Any,
) -> tuple[dict[str, Any] | None, tuple[str, ...]]:
    """Backward-compatible name for the cohort-independent legacy adapter."""

    return project_legacy_regression_input(value)


def _known28_input_commitments(
    *,
    commitment_key: bytes,
    case_ref: str,
    legacy_current_input: Mapping[str, Any],
    projected_current_input: Mapping[str, Any] | None,
    applicability_status: str,
    applicability_issue_codes: Sequence[str],
) -> tuple[str, str | None, str]:
    legacy_commitment = _commit_json(
        commitment_key,
        _LEGACY_COMMITMENT_DOMAIN,
        legacy_current_input,
    )
    projected_commitment = (
        _commit_json(
            commitment_key,
            _PROJECTED_COMMITMENT_DOMAIN,
            projected_current_input,
        )
        if projected_current_input is not None
        else None
    )
    binding_commitment = _commit_json(
        commitment_key,
        _APPLICABILITY_BINDING_DOMAIN,
        {
            "case_ref": case_ref,
            "legacy_input_commitment": legacy_commitment,
            "projected_input_commitment": projected_commitment,
            "projection_policy_sha256": (
                KNOWN28_GENERIC_PROJECTION_POLICY_SHA256
            ),
            "applicability_status": applicability_status,
            "applicability_issue_codes": list(applicability_issue_codes),
        },
    )
    return legacy_commitment, projected_commitment, binding_commitment


async def _v1_body(current_input: Mapping[str, Any], case_ref: str) -> str:
    reply = await render_emlis_ai_reply(
        user_id=f"nls-v3-step11-known-{case_ref}",
        subscription_tier="free",
        current_input=dict(current_input),
    )
    if type(reply.comment_text) is not str or not reply.comment_text:
        raise ValueError("step11_known28_v1_body_invalid")
    return reply.comment_text


def validate_known28_private_packet(
    private_packet: Any,
    receipt: Any,
    *,
    commitment_key: bytes,
) -> tuple[str, ...]:
    """Recompute raw identity, applicability, v1, v3 and every HMAC binding."""

    if type(private_packet) is not dict or type(receipt) is not dict:
        return ("STEP11_KNOWN28_PRIVATE_MAPPING_REQUIRED",)
    issues: set[str] = set()
    if (
        set(private_packet)
        != {
            "schema_version",
            "storage_scope",
            "body_full",
            "candidate_version_id",
            "run_id",
            "commitment_key_id",
            "projection_policy_sha256",
            "cases",
        }
        or private_packet.get("schema_version") != STEP11_KNOWN28_PRIVATE_SCHEMA
        or private_packet.get("storage_scope")
        != "private_local_only_outside_repo"
        or private_packet.get("body_full") is not True
        or private_packet.get("candidate_version_id")
        != receipt.get("candidate_version_id")
        or private_packet.get("candidate_version_id")
        != STEP11_CANDIDATE_VERSION_ID
        or private_packet.get("run_id") != receipt.get("run_id")
        or private_packet.get("commitment_key_id")
        != commitment_key_id(commitment_key)
        or private_packet.get("projection_policy_sha256")
        != KNOWN28_GENERIC_PROJECTION_POLICY_SHA256
        or receipt.get("commitment_key_id")
        != commitment_key_id(commitment_key)
        or receipt.get("generic_projection_policy_sha256")
        != KNOWN28_GENERIC_PROJECTION_POLICY_SHA256
        or receipt.get("expected_applicability_inventory_sha256")
        != FROZEN_KNOWN28_EXPECTED_APPLICABILITY_SHA256
        or receipt.get("private_packet_commitment")
        != _commit_json(
            commitment_key, "step11_known28_private_packet", private_packet
        )
    ):
        issues.add("STEP11_KNOWN28_PRIVATE_PARENT_INVALID")
    private_rows = private_packet.get("cases")
    public_rows = receipt.get("rows")
    if (
        type(private_rows) is not list
        or type(public_rows) is not list
        or len(private_rows) != 28
        or len(public_rows) != 28
    ):
        return tuple(sorted(issues | {"STEP11_KNOWN28_PRIVATE_EXACT_28_REQUIRED"}))
    private_by_ref = {
        row.get("case_ref"): row for row in private_rows if type(row) is dict
    }
    public_by_ref = {
        row.get("case_ref"): row for row in public_rows if type(row) is dict
    }
    if (
        len(private_by_ref) != 28
        or len(public_by_ref) != 28
        or set(private_by_ref) != set(public_by_ref)
    ):
        return tuple(sorted(issues | {"STEP11_KNOWN28_PRIVATE_CASE_SET_INVALID"}))
    try:
        expected_applicability = _verify_known28_projection_contract()
        baseline_cases = load_baseline_cases()
    except (KeyError, TypeError, ValueError):
        return tuple(
            sorted(
                issues
                | {"STEP11_KNOWN28_PRIVATE_PROJECTION_CONTRACT_INVALID"}
            )
        )
    baseline_by_ref = {row.case_id: row for row in baseline_cases}
    if (
        len(baseline_by_ref) != 28
        or set(baseline_by_ref) != set(private_by_ref)
        or set(expected_applicability) != set(private_by_ref)
    ):
        return tuple(
            sorted(issues | {"STEP11_KNOWN28_PRIVATE_CASE_SET_INVALID"})
        )
    for public in public_rows:
        case_ref = public.get("case_ref") if type(public) is dict else None
        private = private_by_ref.get(case_ref)
        baseline = baseline_by_ref.get(case_ref)
        try:
            if (
                type(private) is not dict
                or set(private) != _PRIVATE_CASE_KEYS
                or baseline is None
                or private.get("cohort") != baseline.cohort
                or private.get("family") != baseline.family
                or type(private.get("legacy_current_input")) is not dict
                or type(private.get("v1_body")) is not str
            ):
                raise ValueError("private row invalid")
            expected_legacy = _copy_legacy_current_input(
                dict(baseline.current_input)
            )
            legacy = private["legacy_current_input"]
            if legacy != expected_legacy:
                issues.add("STEP11_KNOWN28_PRIVATE_LEGACY_SOURCE_MISMATCH")
                continue
            projected_candidate, projection_issues = (
                project_known28_legacy_input(legacy)
            )
            measured_status = (
                "app_reachable"
                if not projection_issues
                else "expected_non_applicable"
            )
            expected_row = expected_applicability[case_ref]
            if (
                measured_status != expected_row["applicability_status"]
                or list(projection_issues)
                != expected_row["expected_issue_codes"]
                or private.get("applicability_status") != measured_status
                or private.get("applicability_issue_codes")
                != list(projection_issues)
            ):
                issues.add("STEP11_KNOWN28_PRIVATE_APPLICABILITY_MISMATCH")
                continue
            projected = (
                projected_candidate if measured_status == "app_reachable" else None
            )
            if private.get("projected_current_input") != projected:
                issues.add("STEP11_KNOWN28_PRIVATE_PROJECTION_MISMATCH")
                continue
            legacy_commitment, projected_commitment, binding_commitment = (
                _known28_input_commitments(
                    commitment_key=commitment_key,
                    case_ref=case_ref,
                    legacy_current_input=legacy,
                    projected_current_input=projected,
                    applicability_status=measured_status,
                    applicability_issue_codes=projection_issues,
                )
            )
            v1_input = _copy_legacy_current_input(legacy)
            recomputed_v1_body = asyncio.run(_v1_body(v1_input, case_ref))
            if v1_input != legacy or recomputed_v1_body != private["v1_body"]:
                issues.add("STEP11_KNOWN28_PRIVATE_V1_RECOMPUTATION_MISMATCH")
                continue
            expected_v1 = hmac_commit_bytes(
                commitment_key,
                "v1_baseline_body",
                recomputed_v1_body.encode("utf-8", errors="strict"),
            )
            expected_v3_body: str | None = None
            if measured_status == "app_reachable":
                if projected is None:
                    raise ValueError("projected input missing")
                execution = execute_step11_offline_v3(
                    projected,
                    candidate_version_id=STEP11_CANDIDATE_VERSION_ID,
                    source_dependency_closure_sha256=receipt[
                        "source_dependency_closure_sha256"
                    ],
                )
                if (
                    validate_step11_runtime_execution(execution)
                    or execution.status != "selected"
                    or type(execution.final_utf8_bytes) is not bytes
                ):
                    raise ValueError("v3 recomputation invalid")
                expected_v3_body = execution.final_utf8_bytes.decode(
                    "utf-8", errors="strict"
                )
            if private.get("v3_body") != expected_v3_body:
                issues.add("STEP11_KNOWN28_PRIVATE_V3_RECOMPUTATION_MISMATCH")
                continue
            expected_v3 = (
                hmac_commit_bytes(
                    commitment_key,
                    "selected_candidate_body",
                    expected_v3_body.encode("utf-8", errors="strict"),
                )
                if expected_v3_body is not None
                else None
            )
        except (
            AttributeError,
            KeyError,
            RuntimeError,
            TypeError,
            UnicodeError,
            ValueError,
        ):
            issues.add("STEP11_KNOWN28_PRIVATE_RECOMPUTATION_FAILED")
            continue
        if (
            public.get("legacy_input_commitment") != legacy_commitment
            or public.get("projected_input_commitment")
            != projected_commitment
            or public.get("applicability_binding_commitment")
            != binding_commitment
            or public.get("v1_baseline_body_commitment") != expected_v1
            or public.get("selected_candidate_body_commitment") != expected_v3
            or public.get("applicability_status") != measured_status
            or public.get("applicability_issue_codes")
            != list(projection_issues)
            or public.get("status")
            != (
                "selected"
                if measured_status == "app_reachable"
                else "expected_non_applicable"
            )
            or public.get("hard_gate_status")
            != (
                "passed"
                if measured_status == "app_reachable"
                else "not_applicable"
            )
            or public.get("failure_codes") != []
            or public.get("exception") is not False
            or public.get("v1_fallback_used") is not False
        ):
            issues.add("STEP11_KNOWN28_PRIVATE_HMAC_MISMATCH")
    return tuple(sorted(issues))


def run_known28(
    *,
    final_batch_summary: Mapping[str, Any],
    before_dependency_manifest: Mapping[str, Any],
    dependency_manifest: Mapping[str, Any],
    commitment_key: bytes,
    run_id: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    _verify_known28_source_files()
    expected_applicability = _verify_known28_projection_contract()
    closure = assert_current_step11_dependency_manifest(
        dependency_manifest,
        before_manifest=before_dependency_manifest,
    )
    if final_batch_summary.get("commitment_key_id") != commitment_key_id(
        commitment_key
    ):
        raise ValueError("step11_known28_commitment_key_mismatch")
    rows: list[dict[str, Any]] = []
    private_rows: list[dict[str, Any]] = []
    for case in load_baseline_cases():
        case_ref = case.case_id
        legacy_current_input = _copy_legacy_current_input(
            dict(case.current_input)
        )
        legacy_identity_before = artifact_sha256(legacy_current_input)
        v1_input = _copy_legacy_current_input(legacy_current_input)
        v1_body = asyncio.run(_v1_body(v1_input, case_ref))
        if (
            v1_input != legacy_current_input
            or artifact_sha256(legacy_current_input) != legacy_identity_before
        ):
            raise ValueError("step11_known28_v1_mutated_legacy_input")
        projected_candidate, projection_issues = project_known28_legacy_input(
            legacy_current_input
        )
        applicability_status = (
            "app_reachable"
            if not projection_issues
            else "expected_non_applicable"
        )
        expected = expected_applicability.get(case_ref)
        if (
            expected is None
            or applicability_status != expected["applicability_status"]
            or list(projection_issues) != expected["expected_issue_codes"]
        ):
            raise ValueError(
                "step11_known28_applicability_inventory_mismatch"
            )
        projected_current_input = (
            projected_candidate
            if applicability_status == "app_reachable"
            else None
        )
        legacy_commitment, projected_commitment, binding_commitment = (
            _known28_input_commitments(
                commitment_key=commitment_key,
                case_ref=case_ref,
                legacy_current_input=legacy_current_input,
                projected_current_input=projected_current_input,
                applicability_status=applicability_status,
                applicability_issue_codes=projection_issues,
            )
        )
        v3_body: str | None = None
        selected_commitment: str | None = None
        if applicability_status == "app_reachable":
            if projected_current_input is None:
                raise ValueError("step11_known28_projection_missing")
            execution = execute_step11_offline_v3(
                projected_current_input,
                candidate_version_id=STEP11_CANDIDATE_VERSION_ID,
                source_dependency_closure_sha256=closure,
            )
            execution_issues = validate_step11_runtime_execution(execution)
            selected = execution.selected_candidate
            gate = next(
                (
                    row
                    for row in execution.selection_result.gate_results
                    if selected is not None
                    and row.candidate_id == selected.candidate_id
                ),
                None,
            )
            if (
                execution_issues
                or execution.status != "selected"
                or selected is None
                or gate is None
                or gate.hard_pass is not True
                or gate.failure_codes
                or type(execution.final_utf8_bytes) is not bytes
            ):
                raise ValueError("step11_known28_applicable_v3_failed")
            v3_body = execution.final_utf8_bytes.decode(
                "utf-8", errors="strict"
            )
            selected_commitment = hmac_commit_bytes(
                commitment_key,
                "selected_candidate_body",
                execution.final_utf8_bytes,
            )
        v1_commitment = hmac_commit_bytes(
            commitment_key,
            "v1_baseline_body",
            v1_body.encode("utf-8", errors="strict"),
        )
        rows.append(
            {
                "case_ref": case_ref,
                "legacy_input_commitment": legacy_commitment,
                "projected_input_commitment": projected_commitment,
                "applicability_binding_commitment": binding_commitment,
                "applicability_status": applicability_status,
                "applicability_issue_codes": list(projection_issues),
                "v1_baseline_body_commitment": v1_commitment,
                "selected_candidate_body_commitment": selected_commitment,
                "status": (
                    "selected"
                    if applicability_status == "app_reachable"
                    else "expected_non_applicable"
                ),
                "hard_gate_status": (
                    "passed"
                    if applicability_status == "app_reachable"
                    else "not_applicable"
                ),
                "failure_codes": [],
                "exception": False,
                "v1_fallback_used": False,
            }
        )
        private_rows.append(
            {
                "case_ref": case_ref,
                "cohort": case.cohort,
                "family": case.family,
                "legacy_current_input": legacy_current_input,
                "projected_current_input": projected_current_input,
                "applicability_status": applicability_status,
                "applicability_issue_codes": list(projection_issues),
                "v1_body": v1_body,
                "v3_body": v3_body,
            }
        )
    private_packet = {
        "schema_version": STEP11_KNOWN28_PRIVATE_SCHEMA,
        "storage_scope": "private_local_only_outside_repo",
        "body_full": True,
        "candidate_version_id": STEP11_CANDIDATE_VERSION_ID,
        "run_id": run_id,
        "commitment_key_id": commitment_key_id(commitment_key),
        "projection_policy_sha256": (
            KNOWN28_GENERIC_PROJECTION_POLICY_SHA256
        ),
        "cases": private_rows,
    }
    receipt = build_known28_receipt(
        rows,
        final_batch_summary=final_batch_summary,
        final_dependency_manifest=dependency_manifest,
        run_id=run_id,
        private_packet_commitment=_commit_json(
            commitment_key, "step11_known28_private_packet", private_packet
        ),
        verifier_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        verified_case_count=len(private_rows),
    )
    private_issues = validate_known28_private_packet(
        private_packet, receipt, commitment_key=commitment_key
    )
    if private_issues:
        raise ValueError(f"step11_known28_private_invalid:{private_issues[0]}")
    if (
        assert_current_step11_dependency_manifest(
            dependency_manifest,
            before_manifest=before_dependency_manifest,
        )
        != closure
    ):
        raise ValueError("step11_known28_source_changed_during_run")
    return private_packet, receipt


def _load_frozen_development42_cases() -> tuple[Any, ...]:
    """Load the exact Development42 source through its frozen validator."""

    expected_path = REPO_ROOT / _DEVELOPMENT42_SOURCE_RELATIVE_PATH
    loader_path = REPO_ROOT / _DEVELOPMENT42_LOADER_RELATIVE_PATH
    if DEVELOPMENT_FIXTURE_PATH.resolve() != expected_path.resolve():
        raise ValueError("step11_development42_source_path_drift")
    source_before = DEVELOPMENT_FIXTURE_PATH.read_bytes()
    if (
        hashlib.sha256(source_before).hexdigest()
        != FROZEN_DEVELOPMENT42_SOURCE_FILE_SHA256
    ):
        raise ValueError("step11_development42_source_drift")
    if (
        hashlib.sha256(loader_path.read_bytes()).hexdigest()
        != FROZEN_DEVELOPMENT42_LOADER_SHA256
    ):
        raise ValueError("step11_development42_loader_drift")
    cases = tuple(load_development_cases())
    if DEVELOPMENT_FIXTURE_PATH.read_bytes() != source_before:
        raise ValueError("step11_development42_source_changed_during_load")
    expected_case_ids = tuple(
        f"NLS2-F{family:02d}-D{case:02d}"
        for family in range(1, 15)
        for case in range(1, 4)
    )
    if (
        len(cases) != 42
        or tuple(row.case_id for row in cases) != expected_case_ids
        or len({row.case_id for row in cases}) != 42
        or any(_DEVELOPMENT42_CASE_RE.fullmatch(row.case_id) is None for row in cases)
    ):
        raise ValueError("step11_development42_case_set_invalid")
    return cases


def build_development42_expected_applicability() -> dict[str, Any]:
    """Classify Development42 only by source shape and the frozen App validator.

    The resulting body-free inventory is evaluation-only.  No classification
    field is passed to candidate generation and no case/family override exists.
    """

    rows: list[dict[str, Any]] = []
    for case in _load_frozen_development42_cases():
        _, issues = project_legacy_regression_input(dict(case.current_input))
        rows.append(
            {
                "case_ref": case.case_id,
                "applicability_status": (
                    "app_reachable" if not issues else "expected_non_applicable"
                ),
                "expected_issue_codes": list(issues),
            }
        )
    value = {
        "schema_version": (
            "cocolon.emlis.nls_v3.development42_expected_applicability.v1"
        ),
        "projection_policy_sha256": KNOWN28_GENERIC_PROJECTION_POLICY_SHA256,
        "classification_source": (
            "frozen_development42_source_plus_frozen_app_reachable_validator"
        ),
        "development_fixture_file_sha256": (
            FROZEN_DEVELOPMENT42_SOURCE_FILE_SHA256
        ),
        "cases": rows,
        "counts": {
            "app_reachable": sum(
                row["applicability_status"] == "app_reachable" for row in rows
            ),
            "expected_non_applicable": sum(
                row["applicability_status"] == "expected_non_applicable"
                for row in rows
            ),
        },
        "candidate_generation_control_allowed": False,
        "body_free": True,
    }
    assert_body_free(value)
    return value


def validate_development42_applicability_contract() -> tuple[str, ...]:
    """Recompute the complete Development42 applicability classification."""

    try:
        inventory = build_development42_expected_applicability()
        rows = inventory["cases"]
        if (
            artifact_sha256(inventory)
            != FROZEN_DEVELOPMENT42_EXPECTED_APPLICABILITY_SHA256
            or inventory["projection_policy_sha256"]
            != KNOWN28_GENERIC_PROJECTION_POLICY_SHA256
            or inventory["counts"]
            != {"app_reachable": 24, "expected_non_applicable": 18}
            or inventory["candidate_generation_control_allowed"] is not False
            or len(rows) != 42
            or tuple(row["case_ref"] for row in rows)
            != tuple(
                f"NLS2-F{family:02d}-D{case:02d}"
                for family in range(1, 15)
                for case in range(1, 4)
            )
            or any(
                type(row) is not dict
                or set(row)
                != {
                    "case_ref",
                    "applicability_status",
                    "expected_issue_codes",
                }
                or row["applicability_status"] not in _APPLICABILITY_STATUSES
                or type(row["expected_issue_codes"]) is not list
                or len(row["expected_issue_codes"])
                != len(set(row["expected_issue_codes"]))
                or any(
                    type(code) is not str or not code
                    for code in row["expected_issue_codes"]
                )
                or (
                    row["applicability_status"] == "app_reachable"
                    and row["expected_issue_codes"]
                )
                or (
                    row["applicability_status"] == "expected_non_applicable"
                    and not row["expected_issue_codes"]
                )
                for row in rows
            )
        ):
            return ("STEP11_DEVELOPMENT42_APPLICABILITY_CONTRACT_INVALID",)
    except (AttributeError, KeyError, TypeError, ValueError):
        return ("STEP11_DEVELOPMENT42_APPLICABILITY_CONTRACT_INVALID",)
    return ()


def _development42_input_commitments(
    *,
    commitment_key: bytes,
    case_ref: str,
    legacy_current_input: Mapping[str, Any],
    projected_current_input: Mapping[str, Any] | None,
    applicability_status: str,
    applicability_issue_codes: Sequence[str],
) -> tuple[str, str | None, str]:
    legacy_commitment = _commit_json(
        commitment_key,
        _DEVELOPMENT42_LEGACY_COMMITMENT_DOMAIN,
        legacy_current_input,
    )
    projected_commitment = (
        _commit_json(
            commitment_key,
            _DEVELOPMENT42_PROJECTED_COMMITMENT_DOMAIN,
            projected_current_input,
        )
        if projected_current_input is not None
        else None
    )
    binding_commitment = _commit_json(
        commitment_key,
        _DEVELOPMENT42_APPLICABILITY_BINDING_DOMAIN,
        {
            "case_ref": case_ref,
            "legacy_input_commitment": legacy_commitment,
            "projected_input_commitment": projected_commitment,
            "development_fixture_file_sha256": (
                FROZEN_DEVELOPMENT42_SOURCE_FILE_SHA256
            ),
            "expected_applicability_inventory_sha256": (
                FROZEN_DEVELOPMENT42_EXPECTED_APPLICABILITY_SHA256
            ),
            "projection_policy_sha256": KNOWN28_GENERIC_PROJECTION_POLICY_SHA256,
            "applicability_status": applicability_status,
            "applicability_issue_codes": list(applicability_issue_codes),
        },
    )
    return legacy_commitment, projected_commitment, binding_commitment


def _development42_final_parent(
    final_batch_summary: Mapping[str, Any],
    dependency_manifest: Mapping[str, Any],
    *,
    before_dependency_manifest: Mapping[str, Any] | None = None,
) -> tuple[str, dict[str, str]]:
    if before_dependency_manifest is None:
        if validate_step11_dependency_manifest(dependency_manifest):
            raise ValueError("step11_development42_dependency_manifest_invalid")
        closure = dependency_manifest["source_dependency_closure_sha256"]
    else:
        closure = assert_current_step11_dependency_manifest(
            dependency_manifest,
            before_manifest=before_dependency_manifest,
        )
    if (
        validate_step11_batch_run_summary(
            final_batch_summary, dependency_manifest=dependency_manifest
        )
        or final_batch_summary.get("candidate_version_id")
        != STEP11_CANDIDATE_VERSION_ID
        or final_batch_summary.get("source_dependency_closure_sha256") != closure
        or final_batch_summary.get("source_closure_start_sha256") != closure
        or final_batch_summary.get("source_closure_end_sha256") != closure
        or final_batch_summary.get("source_closure_stable") is not True
        or final_batch_summary.get("machine_status") != "clean"
        or final_batch_summary.get("executed_case_count") != 100
        or final_batch_summary.get("all_expected_cases_executed") is not True
        or type(final_batch_summary.get("case_rows")) is not list
        or len(final_batch_summary["case_rows"]) != 100
        or any(
            row.get("status") != "selected"
            or row.get("v1_fallback_used") is not False
            for row in final_batch_summary["case_rows"]
            if type(row) is dict
        )
        or any(type(row) is not dict for row in final_batch_summary["case_rows"])
    ):
        raise ValueError("step11_development42_final_parent_invalid")
    file_rows = dependency_manifest.get("file_hashes")
    if type(file_rows) is not list:
        raise ValueError("step11_development42_dependency_file_rows_invalid")
    by_path = {
        row["path"]: row["sha256"]
        for row in file_rows
        if type(row) is dict
        and type(row.get("path")) is str
        and type(row.get("sha256")) is str
    }
    required = {
        "ai/tools/emlis_nls_v3_step11_regression.py",
        (
            "ai/services/ai_inference/"
            "emlis_ai_step10_app_reachable_contract_v3.py"
        ),
    }
    if not required.issubset(by_path):
        raise ValueError("step11_development42_dependency_owner_missing")
    return closure, by_path


def _development42_public_row(
    value: Mapping[str, Any],
    expected: Mapping[str, Any],
) -> dict[str, Any]:
    if type(value) is not dict or set(value) != _DEVELOPMENT42_PUBLIC_ROW_KEYS:
        raise ValueError("step11_development42_public_row_shape_invalid")
    row = dict(value)
    codes = row["applicability_issue_codes"]
    failure_codes = row["failure_codes"]
    status = row["applicability_status"]
    if (
        row["case_ref"] != expected["case_ref"]
        or _DEVELOPMENT42_CASE_RE.fullmatch(row["case_ref"]) is None
        or type(row["family"]) is not str
        or not row["family"]
        or status != expected["applicability_status"]
        or codes != expected["expected_issue_codes"]
        or type(codes) is not list
        or len(codes) != len(set(codes))
        or type(failure_codes) is not list
        or failure_codes
        or row["exception"] is not False
        or row["v1_fallback_used"] is not False
        or not all(
            type(row[key]) is str
            and _SHA256_RE.fullmatch(row[key]) is not None
            and row[key] != "0" * 64
            for key in (
                "legacy_input_commitment",
                "applicability_binding_commitment",
                "v1_baseline_body_commitment",
            )
        )
    ):
        raise ValueError("step11_development42_public_row_invalid")
    if status == "app_reachable":
        if (
            codes
            or row["status"] != "selected"
            or row["hard_gate_status"] != "passed"
            or any(
                type(row[key]) is not str
                or _SHA256_RE.fullmatch(row[key]) is None
                or row[key] == "0" * 64
                for key in (
                    "projected_input_commitment",
                    "selected_candidate_body_commitment",
                )
            )
        ):
            raise ValueError("step11_development42_selected_row_invalid")
    elif (
        not codes
        or row["projected_input_commitment"] is not None
        or row["selected_candidate_body_commitment"] is not None
        or row["status"] != "expected_non_applicable"
        or row["hard_gate_status"] != "not_applicable"
    ):
        raise ValueError("step11_development42_nonapp_row_invalid")
    assert_body_free(row)
    return row


def build_development42_receipt(
    rows: Sequence[Mapping[str, Any]],
    *,
    final_batch_summary: Mapping[str, Any],
    dependency_manifest: Mapping[str, Any],
    run_id: str,
    private_packet_commitment: str,
    verifier_sha256: str,
    verified_case_count: int,
) -> dict[str, Any]:
    """Build a body-free, independently recomputable Development42 receipt."""

    if validate_development42_applicability_contract():
        raise ValueError("step11_development42_applicability_contract_invalid")
    closure, by_path = _development42_final_parent(
        final_batch_summary, dependency_manifest
    )
    if (
        type(run_id) is not str
        or _RUN_ID_RE.fullmatch(run_id) is None
        or type(private_packet_commitment) is not str
        or _SHA256_RE.fullmatch(private_packet_commitment) is None
        or private_packet_commitment == "0" * 64
        or verifier_sha256
        != by_path["ai/tools/emlis_nls_v3_step11_regression.py"]
        or verified_case_count != 42
        or type(verified_case_count) is bool
        or type(rows) not in {list, tuple}
        or len(rows) != 42
    ):
        raise ValueError("step11_development42_receipt_parent_invalid")
    inventory = build_development42_expected_applicability()
    expected_by_ref = {row["case_ref"]: row for row in inventory["cases"]}
    if (
        len(expected_by_ref) != 42
        or {row.get("case_ref") for row in rows if type(row) is dict}
        != set(expected_by_ref)
    ):
        raise ValueError("step11_development42_receipt_case_set_invalid")
    normalized = [
        _development42_public_row(row, expected_by_ref[row["case_ref"]])
        for row in sorted(rows, key=lambda item: item["case_ref"])
    ]
    selected_count = sum(row["status"] == "selected" for row in normalized)
    nonapp_count = sum(
        row["status"] == "expected_non_applicable" for row in normalized
    )
    pass_count = selected_count + nonapp_count
    aggregate = {
        "case_count": 42,
        "pass_count": pass_count,
        "app_reachable_count": inventory["counts"]["app_reachable"],
        "selected_count": selected_count,
        "expected_non_applicable_count": inventory["counts"][
            "expected_non_applicable"
        ],
        "expected_non_applicable_match_count": nonapp_count,
        "hard_gate_pass_count": sum(
            row["hard_gate_status"] == "passed" for row in normalized
        ),
        "failure_count": sum(bool(row["failure_codes"]) for row in normalized),
        "exception_count": sum(row["exception"] is True for row in normalized),
        "v1_fallback_count": sum(
            row["v1_fallback_used"] is True for row in normalized
        ),
    }
    value = {
        "schema_version": STEP11_DEVELOPMENT42_RECEIPT_SCHEMA,
        "cycle_id": "cycle_001",
        "candidate_version_id": STEP11_CANDIDATE_VERSION_ID,
        "run_id": run_id,
        "source_dependency_closure_sha256": closure,
        "commitment_policy_sha256": final_batch_summary[
            "commitment_policy_sha256"
        ],
        "commitment_key_id": final_batch_summary["commitment_key_id"],
        "final_batch_summary_sha256": artifact_sha256(final_batch_summary),
        "regression_set": "V2_DEVELOPMENT_42",
        "development_fixture_file_sha256": (
            FROZEN_DEVELOPMENT42_SOURCE_FILE_SHA256
        ),
        "development_fixture_loader_sha256": FROZEN_DEVELOPMENT42_LOADER_SHA256,
        "generic_projection_policy_sha256": KNOWN28_GENERIC_PROJECTION_POLICY_SHA256,
        "expected_applicability_inventory_sha256": (
            FROZEN_DEVELOPMENT42_EXPECTED_APPLICABILITY_SHA256
        ),
        "validator_owner_sha256": by_path[
            "ai/services/ai_inference/"
            "emlis_ai_step10_app_reachable_contract_v3.py"
        ],
        "private_packet_commitment": private_packet_commitment,
        "verifier_sha256": verifier_sha256,
        "verified_case_count": verified_case_count,
        "private_packet_validation_status": "clean",
        "rows": normalized,
        "aggregate": aggregate,
        "aggregate_recomputed_from_rows": True,
        "formal_status": "clean" if pass_count == 42 else "failed",
        "counts_toward_karen_minimum": False,
        "body_free": True,
    }
    assert_body_free(value)
    return value


def validate_development42_receipt(
    value: Any,
    *,
    final_batch_summary: Mapping[str, Any],
    dependency_manifest: Mapping[str, Any],
) -> tuple[str, ...]:
    if type(value) is not dict or type(value.get("rows")) is not list:
        return ("STEP11_DEVELOPMENT42_RECEIPT_MAPPING_REQUIRED",)
    try:
        expected = build_development42_receipt(
            value["rows"],
            final_batch_summary=final_batch_summary,
            dependency_manifest=dependency_manifest,
            run_id=value.get("run_id"),
            private_packet_commitment=value.get("private_packet_commitment"),
            verifier_sha256=value.get("verifier_sha256"),
            verified_case_count=value.get("verified_case_count"),
        )
    except (AttributeError, KeyError, TypeError, ValueError):
        return ("STEP11_DEVELOPMENT42_RECEIPT_CONTRACT_INVALID",)
    return (
        ()
        if value == expected
        else ("STEP11_DEVELOPMENT42_RECEIPT_RECOMPUTATION_MISMATCH",)
    )


def validate_development42_private_packet(
    private_packet: Any,
    receipt: Any,
    *,
    commitment_key: bytes,
) -> tuple[str, ...]:
    """Recompute source identity, classification, v1, v3 and HMAC bindings."""

    if type(private_packet) is not dict or type(receipt) is not dict:
        return ("STEP11_DEVELOPMENT42_PRIVATE_MAPPING_REQUIRED",)
    issues: set[str] = set()
    private_rows = private_packet.get("cases")
    public_rows = receipt.get("rows")
    if (
        set(private_packet)
        != {
            "schema_version",
            "storage_scope",
            "body_full",
            "candidate_version_id",
            "run_id",
            "commitment_key_id",
            "development_fixture_file_sha256",
            "projection_policy_sha256",
            "expected_applicability_inventory_sha256",
            "cases",
        }
        or private_packet.get("schema_version")
        != STEP11_DEVELOPMENT42_PRIVATE_SCHEMA
        or private_packet.get("storage_scope")
        != "private_local_only_outside_repo"
        or private_packet.get("body_full") is not True
        or private_packet.get("candidate_version_id")
        != STEP11_CANDIDATE_VERSION_ID
        or private_packet.get("candidate_version_id")
        != receipt.get("candidate_version_id")
        or private_packet.get("run_id") != receipt.get("run_id")
        or private_packet.get("commitment_key_id")
        != commitment_key_id(commitment_key)
        or receipt.get("commitment_key_id")
        != commitment_key_id(commitment_key)
        or private_packet.get("development_fixture_file_sha256")
        != FROZEN_DEVELOPMENT42_SOURCE_FILE_SHA256
        or receipt.get("development_fixture_file_sha256")
        != FROZEN_DEVELOPMENT42_SOURCE_FILE_SHA256
        or private_packet.get("projection_policy_sha256")
        != KNOWN28_GENERIC_PROJECTION_POLICY_SHA256
        or receipt.get("generic_projection_policy_sha256")
        != KNOWN28_GENERIC_PROJECTION_POLICY_SHA256
        or private_packet.get("expected_applicability_inventory_sha256")
        != FROZEN_DEVELOPMENT42_EXPECTED_APPLICABILITY_SHA256
        or receipt.get("expected_applicability_inventory_sha256")
        != FROZEN_DEVELOPMENT42_EXPECTED_APPLICABILITY_SHA256
        or receipt.get("private_packet_commitment")
        != _commit_json(
            commitment_key,
            "step11_development42_private_packet",
            private_packet,
        )
    ):
        issues.add("STEP11_DEVELOPMENT42_PRIVATE_PARENT_INVALID")
    if (
        type(private_rows) is not list
        or type(public_rows) is not list
        or len(private_rows) != 42
        or len(public_rows) != 42
    ):
        return tuple(
            sorted(issues | {"STEP11_DEVELOPMENT42_PRIVATE_EXACT_42_REQUIRED"})
        )
    private_by_ref = {
        row.get("case_ref"): row for row in private_rows if type(row) is dict
    }
    public_by_ref = {
        row.get("case_ref"): row for row in public_rows if type(row) is dict
    }
    try:
        cases = _load_frozen_development42_cases()
        inventory = build_development42_expected_applicability()
    except (AttributeError, KeyError, TypeError, ValueError):
        return tuple(
            sorted(issues | {"STEP11_DEVELOPMENT42_PRIVATE_SOURCE_INVALID"})
        )
    cases_by_ref = {row.case_id: row for row in cases}
    expected_by_ref = {row["case_ref"]: row for row in inventory["cases"]}
    if (
        len(private_by_ref) != 42
        or len(public_by_ref) != 42
        or set(private_by_ref) != set(public_by_ref)
        or set(private_by_ref) != set(cases_by_ref)
        or set(private_by_ref) != set(expected_by_ref)
    ):
        return tuple(
            sorted(issues | {"STEP11_DEVELOPMENT42_PRIVATE_CASE_SET_INVALID"})
        )
    for case_ref in sorted(cases_by_ref):
        private = private_by_ref[case_ref]
        public = public_by_ref[case_ref]
        source = cases_by_ref[case_ref]
        expected = expected_by_ref[case_ref]
        try:
            if (
                set(private) != _DEVELOPMENT42_PRIVATE_CASE_KEYS
                or private.get("cohort") != "development"
                or private.get("family") != source.family
                or public.get("family") != source.family
            ):
                raise ValueError("development42 private row invalid")
            expected_legacy = _copy_legacy_current_input(
                dict(source.current_input)
            )
            legacy = private["legacy_current_input"]
            if legacy != expected_legacy:
                issues.add("STEP11_DEVELOPMENT42_PRIVATE_SOURCE_MISMATCH")
                continue
            projected_candidate, projection_issues = (
                project_legacy_regression_input(legacy)
            )
            measured_status = (
                "app_reachable"
                if not projection_issues
                else "expected_non_applicable"
            )
            if (
                measured_status != expected["applicability_status"]
                or list(projection_issues) != expected["expected_issue_codes"]
                or private["applicability_status"] != measured_status
                or private["applicability_issue_codes"]
                != list(projection_issues)
            ):
                issues.add("STEP11_DEVELOPMENT42_PRIVATE_APPLICABILITY_MISMATCH")
                continue
            projected = (
                projected_candidate if measured_status == "app_reachable" else None
            )
            if private["projected_current_input"] != projected:
                issues.add("STEP11_DEVELOPMENT42_PRIVATE_PROJECTION_MISMATCH")
                continue
            legacy_commitment, projected_commitment, binding_commitment = (
                _development42_input_commitments(
                    commitment_key=commitment_key,
                    case_ref=case_ref,
                    legacy_current_input=legacy,
                    projected_current_input=projected,
                    applicability_status=measured_status,
                    applicability_issue_codes=projection_issues,
                )
            )
            v1_input = _copy_legacy_current_input(legacy)
            recomputed_v1 = asyncio.run(_v1_body(v1_input, case_ref))
            if v1_input != legacy or private["v1_body"] != recomputed_v1:
                issues.add("STEP11_DEVELOPMENT42_PRIVATE_V1_MISMATCH")
                continue
            expected_v1 = hmac_commit_bytes(
                commitment_key,
                "v1_baseline_body",
                recomputed_v1.encode("utf-8", errors="strict"),
            )
            expected_v3_body: str | None = None
            if measured_status == "app_reachable":
                if projected is None:
                    raise ValueError("projected Development42 input missing")
                execution = execute_step11_offline_v3(
                    projected,
                    candidate_version_id=STEP11_CANDIDATE_VERSION_ID,
                    source_dependency_closure_sha256=receipt[
                        "source_dependency_closure_sha256"
                    ],
                )
                if (
                    validate_step11_runtime_execution(execution)
                    or execution.status != "selected"
                    or type(execution.final_utf8_bytes) is not bytes
                ):
                    raise ValueError("Development42 v3 recomputation invalid")
                expected_v3_body = execution.final_utf8_bytes.decode(
                    "utf-8", errors="strict"
                )
            if private["v3_body"] != expected_v3_body:
                issues.add("STEP11_DEVELOPMENT42_PRIVATE_V3_MISMATCH")
                continue
            expected_v3 = (
                hmac_commit_bytes(
                    commitment_key,
                    "selected_candidate_body",
                    expected_v3_body.encode("utf-8", errors="strict"),
                )
                if expected_v3_body is not None
                else None
            )
        except (
            AttributeError,
            KeyError,
            RuntimeError,
            TypeError,
            UnicodeError,
            ValueError,
        ):
            issues.add("STEP11_DEVELOPMENT42_PRIVATE_RECOMPUTATION_FAILED")
            continue
        if (
            public.get("legacy_input_commitment") != legacy_commitment
            or public.get("projected_input_commitment") != projected_commitment
            or public.get("applicability_binding_commitment")
            != binding_commitment
            or public.get("v1_baseline_body_commitment") != expected_v1
            or public.get("selected_candidate_body_commitment") != expected_v3
            or public.get("applicability_status") != measured_status
            or public.get("applicability_issue_codes")
            != list(projection_issues)
            or public.get("status")
            != (
                "selected"
                if measured_status == "app_reachable"
                else "expected_non_applicable"
            )
            or public.get("hard_gate_status")
            != (
                "passed"
                if measured_status == "app_reachable"
                else "not_applicable"
            )
            or public.get("failure_codes") != []
            or public.get("exception") is not False
            or public.get("v1_fallback_used") is not False
        ):
            issues.add("STEP11_DEVELOPMENT42_PRIVATE_HMAC_MISMATCH")
    return tuple(sorted(issues))


def run_development42(
    *,
    final_batch_summary: Mapping[str, Any],
    before_dependency_manifest: Mapping[str, Any],
    dependency_manifest: Mapping[str, Any],
    commitment_key: bytes,
    run_id: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Execute every current-applicable Development42 case via rc0023."""

    closure, _ = _development42_final_parent(
        final_batch_summary,
        dependency_manifest,
        before_dependency_manifest=before_dependency_manifest,
    )
    if final_batch_summary.get("commitment_key_id") != commitment_key_id(
        commitment_key
    ):
        raise ValueError("step11_development42_commitment_key_mismatch")
    contract_issues = validate_development42_applicability_contract()
    if contract_issues:
        raise ValueError(contract_issues[0])
    inventory = build_development42_expected_applicability()
    expected_by_ref = {row["case_ref"]: row for row in inventory["cases"]}
    public_rows: list[dict[str, Any]] = []
    private_rows: list[dict[str, Any]] = []
    for case in _load_frozen_development42_cases():
        case_ref = case.case_id
        legacy = _copy_legacy_current_input(dict(case.current_input))
        legacy_identity_before = artifact_sha256(legacy)
        v1_input = _copy_legacy_current_input(legacy)
        v1_body = asyncio.run(_v1_body(v1_input, case_ref))
        if v1_input != legacy or artifact_sha256(legacy) != legacy_identity_before:
            raise ValueError("step11_development42_v1_mutated_legacy_input")
        projected_candidate, projection_issues = (
            project_legacy_regression_input(legacy)
        )
        applicability_status = (
            "app_reachable" if not projection_issues else "expected_non_applicable"
        )
        expected = expected_by_ref[case_ref]
        if (
            applicability_status != expected["applicability_status"]
            or list(projection_issues) != expected["expected_issue_codes"]
        ):
            raise ValueError("step11_development42_applicability_mismatch")
        projected = (
            projected_candidate if applicability_status == "app_reachable" else None
        )
        legacy_commitment, projected_commitment, binding_commitment = (
            _development42_input_commitments(
                commitment_key=commitment_key,
                case_ref=case_ref,
                legacy_current_input=legacy,
                projected_current_input=projected,
                applicability_status=applicability_status,
                applicability_issue_codes=projection_issues,
            )
        )
        v3_body: str | None = None
        selected_commitment: str | None = None
        if applicability_status == "app_reachable":
            if projected is None:
                raise ValueError("step11_development42_projection_missing")
            execution = execute_step11_offline_v3(
                projected,
                candidate_version_id=STEP11_CANDIDATE_VERSION_ID,
                source_dependency_closure_sha256=closure,
            )
            selected = execution.selected_candidate
            gate = next(
                (
                    row
                    for row in execution.selection_result.gate_results
                    if selected is not None
                    and row.candidate_id == selected.candidate_id
                ),
                None,
            )
            if (
                validate_step11_runtime_execution(execution)
                or execution.status != "selected"
                or selected is None
                or gate is None
                or gate.hard_pass is not True
                or gate.failure_codes
                or type(execution.final_utf8_bytes) is not bytes
            ):
                raise ValueError("step11_development42_applicable_v3_failed")
            v3_body = execution.final_utf8_bytes.decode("utf-8", errors="strict")
            selected_commitment = hmac_commit_bytes(
                commitment_key,
                "selected_candidate_body",
                execution.final_utf8_bytes,
            )
        v1_commitment = hmac_commit_bytes(
            commitment_key,
            "v1_baseline_body",
            v1_body.encode("utf-8", errors="strict"),
        )
        public_rows.append(
            {
                "case_ref": case_ref,
                "family": case.family,
                "legacy_input_commitment": legacy_commitment,
                "projected_input_commitment": projected_commitment,
                "applicability_binding_commitment": binding_commitment,
                "applicability_status": applicability_status,
                "applicability_issue_codes": list(projection_issues),
                "v1_baseline_body_commitment": v1_commitment,
                "selected_candidate_body_commitment": selected_commitment,
                "status": (
                    "selected"
                    if applicability_status == "app_reachable"
                    else "expected_non_applicable"
                ),
                "hard_gate_status": (
                    "passed"
                    if applicability_status == "app_reachable"
                    else "not_applicable"
                ),
                "failure_codes": [],
                "exception": False,
                "v1_fallback_used": False,
            }
        )
        private_rows.append(
            {
                "case_ref": case_ref,
                "cohort": "development",
                "family": case.family,
                "legacy_current_input": legacy,
                "projected_current_input": projected,
                "applicability_status": applicability_status,
                "applicability_issue_codes": list(projection_issues),
                "v1_body": v1_body,
                "v3_body": v3_body,
            }
        )
    private_packet = {
        "schema_version": STEP11_DEVELOPMENT42_PRIVATE_SCHEMA,
        "storage_scope": "private_local_only_outside_repo",
        "body_full": True,
        "candidate_version_id": STEP11_CANDIDATE_VERSION_ID,
        "run_id": run_id,
        "commitment_key_id": commitment_key_id(commitment_key),
        "development_fixture_file_sha256": (
            FROZEN_DEVELOPMENT42_SOURCE_FILE_SHA256
        ),
        "projection_policy_sha256": KNOWN28_GENERIC_PROJECTION_POLICY_SHA256,
        "expected_applicability_inventory_sha256": (
            FROZEN_DEVELOPMENT42_EXPECTED_APPLICABILITY_SHA256
        ),
        "cases": private_rows,
    }
    verifier_sha256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    receipt = build_development42_receipt(
        public_rows,
        final_batch_summary=final_batch_summary,
        dependency_manifest=dependency_manifest,
        run_id=run_id,
        private_packet_commitment=_commit_json(
            commitment_key,
            "step11_development42_private_packet",
            private_packet,
        ),
        verifier_sha256=verifier_sha256,
        verified_case_count=42,
    )
    private_issues = validate_development42_private_packet(
        private_packet, receipt, commitment_key=commitment_key
    )
    if private_issues:
        raise ValueError(
            f"step11_development42_private_invalid:{private_issues[0]}"
        )
    if (
        assert_current_step11_dependency_manifest(
            dependency_manifest,
            before_manifest=before_dependency_manifest,
        )
        != closure
    ):
        raise ValueError("step11_development42_source_changed_during_run")
    return private_packet, receipt


def run_invalid16(
    invalid_fixture_path: Path,
    *,
    final_batch_summary: Mapping[str, Any],
    before_dependency_manifest: Mapping[str, Any],
    dependency_manifest: Mapping[str, Any],
    run_id: str,
) -> dict[str, Any]:
    closure = assert_current_step11_dependency_manifest(
        dependency_manifest,
        before_manifest=before_dependency_manifest,
    )
    invalid_raw = invalid_fixture_path.read_bytes()
    if hashlib.sha256(invalid_raw).hexdigest() != FROZEN_INVALID16_FILE_SHA256:
        raise ValueError("step11_invalid16_source_drift")
    invalid_fixtures = load_invalid16_fixtures(invalid_fixture_path)
    if invalid_fixture_path.read_bytes() != invalid_raw:
        raise ValueError("step11_invalid16_source_changed_during_load")
    rows = [
        {
            "fixture_id": fixture["fixture_id"],
            "actual_issue_codes": list(validate_app_reachable_input(fixture["input"])),
        }
        for fixture in invalid_fixtures
    ]
    receipt = build_invalid16_receipt(
        rows,
        final_batch_summary=final_batch_summary,
        final_dependency_manifest=dependency_manifest,
        run_id=run_id,
        verifier_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        verified_case_count=len(rows),
    )
    if (
        assert_current_step11_dependency_manifest(
            dependency_manifest,
            before_manifest=before_dependency_manifest,
        )
        != closure
    ):
        raise ValueError("step11_invalid16_source_changed_during_run")
    return receipt


def load_invalid16_fixtures(path: Path) -> list[Mapping[str, Any]]:
    """Load the frozen Step 3 negative wrapper through its actual contract.

    ``load_canonical_jsonl`` defaults to the valid sample-case validator.  The
    invalid corpus deliberately wraps an invalid app input with its fixture ID
    and expected issue, so the wrapper must first be parsed canonically without
    applying the valid-sample schema.  This adapter then reproduces the frozen
    wrapper and rejection bindings without changing the Step 0--3 owner bytes.
    """

    inventory_issues = validate_invalid16_inventory_contract()
    if inventory_issues:
        raise ValueError(
            f"step11_invalid_fixture_inventory_invalid:{inventory_issues[0]}"
        )
    raw_rows = load_canonical_jsonl(path, validator=None)
    rows: list[Mapping[str, Any]] = []
    seen_fixture_ids: set[str] = set()
    for line_number, raw in enumerate(raw_rows, start=1):
        if type(raw) is not dict or set(raw) != _INVALID16_FIXTURE_WRAPPER_KEYS:
            raise ValueError(
                f"step11_invalid_fixture_wrapper_keyset_invalid:{line_number}"
            )
        fixture_id = raw["fixture_id"]
        expected_issue = raw["expected_issue"]
        if type(fixture_id) is not str or fixture_id in seen_fixture_ids:
            raise ValueError(
                f"step11_invalid_fixture_id_invalid_or_duplicate:{line_number}"
            )
        if type(expected_issue) is not str:
            raise ValueError(
                f"step11_invalid_fixture_expected_issue_invalid:{line_number}"
            )
        seen_fixture_ids.add(fixture_id)
        actual_issues = validate_app_reachable_input(raw["input"])
        if expected_issue not in actual_issues:
            raise ValueError(
                f"step11_invalid_fixture_expected_issue_mismatch:{line_number}"
            )
        rows.append(raw)
    actual_inventory = [
        {
            "fixture_id": row["fixture_id"],
            "expected_issue": row["expected_issue"],
        }
        for row in rows
    ]
    if actual_inventory != list(INVALID16_EXPECTED_INVENTORY):
        raise ValueError("step11_invalid_fixture_inventory_mismatch")
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run Cycle 001 rc0023 regressions with the exact frozen rc0022 "
            "failed-run manifest as predecessor."
        )
    )
    parser.add_argument("--final-summary", type=Path, required=True)
    parser.add_argument("--before-dependency-manifest", type=Path, required=True)
    parser.add_argument("--dependency-manifest", type=Path, required=True)
    parser.add_argument("--invalid-fixtures", type=Path, required=True)
    parser.add_argument("--commitment-key-file", type=Path, required=True)
    parser.add_argument("--known-run-id", required=True)
    parser.add_argument("--development-run-id", required=True)
    parser.add_argument("--invalid-run-id", required=True)
    parser.add_argument("--known-private-output", type=Path, required=True)
    parser.add_argument("--known-receipt-output", type=Path, required=True)
    parser.add_argument("--development-private-output", type=Path, required=True)
    parser.add_argument("--development-receipt-output", type=Path, required=True)
    parser.add_argument("--invalid-receipt-output", type=Path, required=True)
    args = parser.parse_args(argv)
    outputs = (
        args.known_private_output,
        args.known_receipt_output,
        args.development_private_output,
        args.development_receipt_output,
        args.invalid_receipt_output,
    )
    if any(path.exists() for path in outputs):
        raise ValueError("step11_regression_output_already_exists")
    inputs = (
        args.final_summary,
        args.before_dependency_manifest,
        args.dependency_manifest,
        args.invalid_fixtures,
        args.commitment_key_file,
    )
    resolved = [path.resolve() for path in (*inputs, *outputs)]
    if len(resolved) != len(set(resolved)):
        raise ValueError("step11_regression_cli_path_collision")
    repo = REPO_ROOT.resolve()
    for label, path in (
        ("known28", args.known_private_output),
        ("development42", args.development_private_output),
    ):
        private_resolved = path.resolve()
        private_lexical = path.absolute()
        if (
            private_resolved == repo
            or repo in private_resolved.parents
            or private_lexical == repo
            or repo in private_lexical.parents
        ):
            raise ValueError(
                f"step11_{label}_private_packet_must_be_outside_repo"
            )
    final = load_canonical_json(args.final_summary)
    before_dependency = load_canonical_json(args.before_dependency_manifest)
    dependency = load_canonical_json(args.dependency_manifest)
    key = _read_key(args.commitment_key_file)
    private, known = run_known28(
        final_batch_summary=final,
        before_dependency_manifest=before_dependency,
        dependency_manifest=dependency,
        commitment_key=key,
        run_id=args.known_run_id,
    )
    development_private, development = run_development42(
        final_batch_summary=final,
        before_dependency_manifest=before_dependency,
        dependency_manifest=dependency,
        commitment_key=key,
        run_id=args.development_run_id,
    )
    invalid = run_invalid16(
        args.invalid_fixtures,
        final_batch_summary=final,
        before_dependency_manifest=before_dependency,
        dependency_manifest=dependency,
        run_id=args.invalid_run_id,
    )
    created: list[Path] = []
    try:
        _write_json(args.known_private_output, private, private=True)
        created.append(args.known_private_output)
        _write_json(args.known_receipt_output, known, private=False)
        created.append(args.known_receipt_output)
        _write_json(
            args.development_private_output,
            development_private,
            private=True,
        )
        created.append(args.development_private_output)
        _write_json(
            args.development_receipt_output,
            development,
            private=False,
        )
        created.append(args.development_receipt_output)
        _write_json(args.invalid_receipt_output, invalid, private=False)
        created.append(args.invalid_receipt_output)
    except BaseException:
        for path in reversed(created):
            try:
                _secure_unlink(path)
            except OSError:
                pass
        raise
    return (
        0
        if known["formal_status"]
        == development["formal_status"]
        == invalid["formal_status"]
        == "clean"
        else 2
    )


if __name__ == "__main__":
    raise SystemExit(main())
