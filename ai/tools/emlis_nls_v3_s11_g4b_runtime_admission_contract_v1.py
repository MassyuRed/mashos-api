#!/usr/bin/env python3
"""Immutable V1 contract for the G4-B read-only runtime admission checker.

This module deliberately contains schemas and canonicalisation only.  It does
not walk a runtime, launch a process, materialise an environment, or write a
file.  Owner and independent implementations may share this immutable
contract, but never share their derivation code or intermediate evidence.
"""

from __future__ import annotations

import hashlib
import json
import posixpath
import re
import sys
from typing import Any, BinaryIO, NoReturn, TextIO

sys.dont_write_bytecode = True


class ContractViolation(ValueError):
    """A deterministic fail-closed contract violation."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


class ContractV1:
    METHOD_ID = "GATE_B_GITHUB_TRACKED_RUNTIME_ADMISSION_CHECKER_V1"
    OFFICIAL_ADMISSION_MODULE = (
        "ai.tools.emlis_nls_v3_s11_g4b_runtime_admission_checker_v1"
    )
    OFFICIAL_ADMISSION_ENTRYPOINT = (
        OFFICIAL_ADMISSION_MODULE + ":main"
    )
    OFFICIAL_PYTHON_FLAGS = ("-E", "-s", "-S", "-B", "-m")
    LIBRARY_INVOCATION_CREDIT = False
    REQUEST_SCHEMA = "emlis.nls_v3.s11.g4b.runtime_admission.request.v1"
    ROLE_RESULT_SCHEMA = "emlis.nls_v3.s11.g4b.runtime_admission.role_result.v1"
    PUBLIC_RESULT_SCHEMA = "emlis.nls_v3.s11.g4b.runtime_admission.public_result.v1"
    HANDOFF_SCHEMA = "emlis.nls_v3.s11.g4b.runtime_admission.handoff.v1"
    MATERIALIZATION_ATTESTATION_SCHEMA = (
        "emlis.nls_v3.s11.g4b.runtime_materialization.external_attestation.v1"
    )
    ROOT_LOCATOR_SCHEMA = "emlis.nls_v3.s11.g4b.runtime_root_locator.v1"
    EXECUTABLE_LOCATOR_SCHEMA = "emlis.nls_v3.s11.g4b.runtime_executable_locator.v1"
    FRESHNESS_EVIDENCE_CLASS = "EXTERNAL_RULE13_RULE16_ATTESTATION_ACCEPTED_V1"
    FRESHNESS_CLAIM_LIMIT = (
        "CHECKER_DOES_NOT_RECONSTRUCT_PREMATERIALIZATION_NONEXISTENCE"
    )
    HANDOFF_CLAIM = "CURRENT_SESSION_BINDING_ONLY_CONSUMER_NOT_OBSERVED_V1"

    CHECK_ORDER = (
        "INPUT_SCHEMA_AND_HEAD_BINDING",
        "FRESH_MATERIALIZATION_EVIDENCE",
        "PRE_ROOT_AND_FROZEN_IDENTITIES",
        "OWNER_DERIVATION",
        "PYTEST_VERSION_PROBE",
        "REQUIRED_ROLE_SMOKE",
        "INDEPENDENT_DERIVATION",
        "RECONCILIATION_AND_POST_ROOT",
        "SAME_INSTANCE_HANDOFF_BINDING",
    )

    EXPECTED_IMPLEMENTATION = "CPython"
    EXPECTED_PYTHON_VERSION = "3.12.13"
    EXPECTED_PLATFORM_TAG = "linux-x86_64"
    EXPECTED_DISTRIBUTIONS = (
        ("iniconfig", "2.3.0"),
        ("packaging", "26.2"),
        ("pluggy", "1.6.0"),
        ("pygments", "2.20.0"),
        ("pytest", "8.4.1"),
    )
    EXPECTED_PYTEST_VERSION = "8.4.1"
    EXPECTED_SITE_PACKAGES_RELATIVE = "lib/python3.12/site-packages"
    EXPECTED_EXECUTABLE_RELATIVE = "bin/python"
    EXPECTED_INTERPRETER_SHA256 = (
        "9ed008e5a8685235361f0c53771b520ab082dd99a877ad2fd796a93fa4c0b488"
    )
    ENVIRONMENT_POLICY_SHA256 = (
        "8a43751b49a8db1d024063608405f9b169e829f3c0be3488433b31800d44b1a4"
    )
    REQUIRED_ROLE_PATH_ORDERED_SHA256 = (
        "e01f5e587ba1884b988075eee1c162454d3a6a1d4b10febc3b7111c2b5c1b248"
    )
    EXPECTED_MANIFEST_ROW_COUNT = 482
    EXPECTED_CANONICAL_PREIMAGE_BYTES = 89_653
    EXPECTED_SITE_REGULAR_FILE_COUNT = 487
    EXPECTED_SITE_DIRECTORY_COUNT = 27
    EXPECTED_EXTERNAL_ENTRYPOINT_COUNT = 3
    EXPECTED_EXTERNAL_ENTRYPOINT_PATHSET_SHA256 = (
        "e68059e3cc382b66728dfa6fe0a2b0bad4685d105e12f037fd09649e0f4b9b61"
    )
    EXPECTED_CANONICAL_PATHSET_SHA256 = (
        "6fb972b20c2c5c776886c53c905bf08e8577fa74284d760c39065b9ba65328f2"
    )
    EXPECTED_EMPTY_MISMATCH_ROW_SHA256 = (
        "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
    )
    EXPECTED_RECORD_CLOSURES = (
        ("iniconfig", "2.3.0", "390ff70b72d7d6be5bf03dae9ff546d6a13584704d3078ce0000eded74092e05"),
        ("packaging", "26.2", "851cdb430628cce99eb887f87405c6c2bfb24e642a972cdf843267018c82c3a1"),
        ("pluggy", "1.6.0", "b072098f6cace7afdf1d4759f13b91f805836743a0af3c4f38f40343c60ee942"),
        ("pygments", "2.20.0", "ce2debc2a42c4274ea75b03e9c0f4dc5bd01c6f25e86da4fac5d76296e3b1a05"),
        ("pytest", "8.4.1", "5cefca6d1f84bef673818f562c6b63b100d32b51dc26405c5bed8cbd91b11874"),
    )
    REQUIRED_ROLE_SOURCES = (
        (
            "OWNER",
            "ai/services/ai_inference/emlis_ai_recovery_epoch002_sequence_ledger_v3.py",
            "13aa675be1356ab524a69066f861c2d27a8d8e32f0d690811b2b3308f199057d",
            "validate_recovery_epoch004_sequence_event1_contract_state_v2",
        ),
        (
            "INDEPENDENT",
            "ai/tools/emlis_nls_v3_recovery_epoch002_closure_receipt_verify.py",
            "634ddb104e0b7630c695e032bb54726912fcfc9ad4351ab0eb6da7901671fc2b",
            "verify_recovery_epoch004_sequence_event1_contract_state_v2",
        ),
        (
            "PARENT",
            "ai/tools/emlis_nls_v3_recovery_epoch002_formal_parent_orchestrator_v3.py",
            "14fedde39823d90253a6adec6fc05ccde29f05a659edbac7edc007b28eab5793",
            "validate_recovery_epoch004_parent_phase3_event1_evidence_state_v2",
        ),
    )
    REQUIRED_ROLE_BLOB_SHA1S = (
        ("OWNER", "044287009b1fd155689bded46628b8fc91b73c06"),
        ("INDEPENDENT", "0fae71a29f8fe44d31c18af42aaf53cc34beac6c"),
        ("PARENT", "fdea3dc18d81ca9ce1e3a842e802d21d0019a8c5"),
    )
    EXPECTED_PROCEDURE_IDS = (
        "COCOLON_RULE13_RUNTIME_CONTINUITY_V20260811",
        "COCOLON_RULE16_ONE_SHOT_PRELAUNCH_V20260811",
    )
    LOCK_SOURCE_RELATIVE = (
        "ai/configs/"
        "emlis_nls_v3_recovery_epoch002_formal_worker_bootstrap_lock_v1.json"
    )

    LOCK_RAW_SHA256 = "9bb2875541a6d959c1dca47cb5b96de5b0041ccf5288e849c469c15a8b310787"
    LOCK_LOGICAL_SHA256 = "801ba54efc0f6655238d14e7c153fb70b555801489aa8ba028515fc64d9c05f4"
    PROJECTION_SHA256 = "f501025c1dccef68c47c0a3e52f3ef74d01233f371b16f2b1a0bdfb21089e57e"
    REQUIREMENTS_SHA256 = "4f7218509a20e42850afe75597f2abfdf447035001847621d4637faa246065f1"
    WHEEL_MANIFEST_SHA256 = "00d2df98c8cda7f1473794892bafe7ccd18cc816c79ccb346f3e21ff629b136d"
    DISTRIBUTION_CLOSURE_SHA256 = "4d3d6afdac2b9a606d4797ff5fbe65010faddf0de9788202798ddb8d95e6556c"
    INSTALLED_MANIFEST_COMPARATOR_SHA256 = (
        "0eba095e4c173b4b69f68532fd66cf2c871ab9edef64d91754b52ed7daee15c5"
    )

    REQUEST_KEYS = frozenset(
        {
            "schema_version",
            "authority_id",
            "observation_session_id",
            "materialization",
            "runtime",
            "frozen",
            "handoff",
        }
    )
    MATERIALIZATION_KEYS = frozenset(
        {
            "event_id",
            "procedure_ids",
            "fresh_root_nonexistent_before",
            "prior_artifact_reuse_count",
            "root",
            "root_locator_sha256",
            "expected_full_root_manifest_sha256",
            "site_packages_relative",
            "probe_cwd",
        }
    )
    RUNTIME_KEYS = frozenset(
        {
            "executable",
            "implementation",
            "python_version",
            "platform_tag",
            "resolved_interpreter_sha256",
        }
    )
    FROZEN_KEYS = frozenset(
        {
            "mashos_api_commit",
            "mashos_api_tree",
            "lock_raw_sha256",
            "lock_logical_sha256",
            "projection_sha256",
            "requirements_sha256",
            "wheel_manifest_sha256",
            "distribution_closure_sha256",
            "installed_manifest_comparator_sha256",
        }
    )
    HANDOFF_KEYS = frozenset({"receiver_session_id", "receiver_nonce"})
    PUBLIC_SUCCESS_KEYS = frozenset(
        {
            "schema_version",
            "method_id",
            "status",
            "terminal",
            "checks_completed",
            "primary_outcome",
            "runtime_ready",
            "gate_b_closed",
            "runtime_readiness_observation_id",
            "runtime_instance_observation_id",
            "installed_file_manifest_sha256",
            "runtime_identity_exact19_sha256",
            "canonical_diagnostic_sha256",
            "handoff_state",
            "handoff_binding_sha256",
            "handoff_consumed",
            "gate_c_authorized",
            "target_execution_count",
            "automatic_progression",
        }
    )
    PUBLIC_STOP_KEYS = frozenset(
        {
            "schema_version",
            "method_id",
            "status",
            "terminal",
            "primary_outcome",
            "runtime_ready",
            "gate_b_closed",
            "handoff_state",
            "handoff_consumed",
            "gate_c_authorized",
            "target_execution_count",
            "automatic_progression",
        }
    )
    STOP_CODES = frozenset(
        {
            "METHOD_OVERRIDE_NOT_AUTHORIZED",
            "BASE_OR_PREIMAGE_DRIFT",
            "PATH_BUDGET_OR_SCOPE_EXCEEDED",
            "PROHIBITED_EFFECT_REQUIRED",
            "INPUT_SCHEMA_INVALID",
            "SCHEMA_OR_VERSION_INVALID",
            "FRESHNESS_UNPROVED",
            "PAST_ARTIFACT_REUSE_DETECTED",
            "PROCESS_CARDINALITY_OR_LAUNCH_INVALID",
            "OWNER_INVALID",
            "PROBE_OR_SMOKE_INVALID",
            "INDEPENDENT_INVALID",
            "DERIVATION_DIVERGENCE",
            "ROOT_DRIFT",
            "HANDOFF_INVALID",
            "PRIVACY_VIOLATION",
            "INTERNAL_FAIL_CLOSED",
            "CURRENT_AUTHORITY_STOP",
            "AUTOMATIC_PROGRESSION_FALSE",
        }
    )

    ROLE_RESULT_KEYS = frozenset(
        {
            "schema_version",
            "role",
            "status",
            "process_id",
            "strategy",
            "runtime_identity_exact19",
            "manifest_sha256",
            "manifest_rows",
            "distribution_closures",
            "canonical_diagnostic",
        }
    )
    MANIFEST_ROW_KEYS = frozenset(
        {"normalized_distribution_name", "relative_path", "byte_count", "raw_sha256"}
    )
    RECORD_ENTRY_KEYS = frozenset({"path", "sha256", "size"})
    DISTRIBUTION_CLOSURE_KEYS = frozenset(
        {
            "normalized_distribution_name",
            "distribution_version",
            "installed_record_closure_sha256",
        }
    )
    RUNTIME_IDENTITY_EXACT19_KEYS = (
        "logical_runtime_id",
        "runtime_content_identity",
        "runtime_root_identity_sha256",
        "runtime_instance_observation_id",
        "materialization_event_id",
        "formal_lock_logical_sha256",
        "runner_projection_sha256",
        "accepted_wheel_manifest_sha256",
        "distribution_closure_sha256",
        "installed_file_manifest_sha256",
        "full_runtime_root_manifest_sha256",
        "entrypoint_control_identity_sha256",
        "resolved_interpreter_executable_sha256",
        "environment_policy_sha256",
        "required_role_path_ordered_sha256",
        "admitted_executable_relative_path",
        "distribution_count",
        "record_closure_match_count",
        "unexpected_entry_count",
    )
    CANONICAL_DIAGNOSTIC_KEYS = frozenset(
        {
            "canonical_row_count",
            "canonical_preimage_bytes",
            "canonical_preimage_lf",
            "site_regular_file_count",
            "site_directory_count",
            "site_symlink_count",
            "site_other_count",
            "eligible_regular_payload_count",
            "owned_file_count",
            "unowned_file_count",
            "duplicate_relative_path_count",
            "missing_file_count",
            "extra_file_count",
            "pyc_file_count",
            "pycache_directory_count",
            "record_self_excluded_count",
            "verified_external_entrypoint_count",
            "external_entrypoint_pathset_sha256",
            "canonical_pathset_sha256",
            "mismatch_row_sha256",
            "mismatch_row_count",
            "nonzero_mismatch_family_count",
        }
    )
    READINESS_PREIMAGE_FIELDS = (
        "schema_version",
        "authority_id",
        "technical_contract_raw_sha256",
        "owner_process_body_raw_sha256",
        "independent_process_body_raw_sha256",
        "comparator_schema",
        "comparator_expected_sha256",
        "accepted_wheel_count",
        "accepted_wheel_manifest_sha256",
        "materialization_event_id",
        "logical_runtime_id",
        "runtime_content_identity",
        "runtime_root_identity_sha256",
        "runtime_instance_observation_id",
        "execution_order",
        "owner_process_count",
        "owner_result",
        "owner_output_sha256",
        "pytest_version_probe_count",
        "pytest_version",
        "pytest_version_stdout_sha256",
        "pytest_version_stderr_bytes",
        "required_role_smoke_process_count",
        "required_role_smoke_inline_program_observed_sha256",
        "required_role_smoke_program_preimage_class",
        "required_role_smoke_output_sha256",
        "required_role_direct_load_count",
        "required_role_public_api_call_count",
        "required_role_effect_count",
        "independent_process_count",
        "independent_result",
        "independent_output_sha256",
        "runtime_identity_exact19_full_match",
        "runtime_identity_exact19_sha256",
        "canonical_diagnostic_full_match",
        "canonical_diagnostic_sha256",
        "current_comparator_match",
        "installed_file_manifest_sha256",
        "full_runtime_root_manifest_sha256",
        "full_runtime_root_pre_post_match",
    )

    MAX_INPUT_BYTES = 1_048_576
    SHA256_RE = re.compile(r"\A[0-9a-f]{64}\Z")
    GIT_OID_RE = re.compile(r"\A[0-9a-f]{40}\Z")
    TOKEN_RE = re.compile(r"\A[A-Za-z0-9][A-Za-z0-9._:-]{0,255}\Z")


def _reject_constant(value: str) -> NoReturn:
    raise ContractViolation("INPUT_SCHEMA_INVALID", f"non-finite number {value!r}")


def _pairs_no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ContractViolation("INPUT_SCHEMA_INVALID", f"duplicate object key {key!r}")
        result[key] = value
    return result


def canonical_json_bytes(value: Any) -> bytes:
    """Return compact UTF-8 canonical JSON with lexical object keys and no LF."""

    try:
        rendered = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ContractViolation("SCHEMA_OR_VERSION_INVALID", str(exc)) from exc
    return rendered.encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def runtime_root_locator_sha256(root: str) -> str:
    """Bind a private canonical root locator without exposing it publicly."""

    return canonical_sha256(
        {
            "schema_version": ContractV1.ROOT_LOCATOR_SCHEMA,
            "runtime_root": root,
        }
    )


def runtime_executable_locator_sha256(executable: str) -> str:
    """Bind the private exact absolute executable locator for handoff V1."""

    return canonical_sha256(
        {
            "schema_version": ContractV1.EXECUTABLE_LOCATOR_SCHEMA,
            "runtime_executable": executable,
        }
    )


def materialization_attestation_preimage(request: dict[str, Any]) -> dict[str, Any]:
    """Return the versioned Rule13/Rule16 external-attestation preimage.

    The checker verifies the canonical identity and the current filesystem
    projection.  The historical fact that the locator did not exist before
    materialisation remains an external Rule13/Rule16 owner attestation; it is
    intentionally not reconstructed or reimplemented here.
    """

    materialization = request["materialization"]
    return {
        "schema_version": ContractV1.MATERIALIZATION_ATTESTATION_SCHEMA,
        "authority_id": request["authority_id"],
        "observation_session_id": request["observation_session_id"],
        "procedure_ids": materialization["procedure_ids"],
        "fresh_root_nonexistent_before": materialization[
            "fresh_root_nonexistent_before"
        ],
        "prior_artifact_reuse_count": materialization[
            "prior_artifact_reuse_count"
        ],
        "root_locator_sha256": materialization["root_locator_sha256"],
        "expected_full_root_manifest_sha256": materialization[
            "expected_full_root_manifest_sha256"
        ],
        "site_packages_relative": materialization["site_packages_relative"],
        "admitted_executable_relative_path": ContractV1.EXPECTED_EXECUTABLE_RELATIVE,
    }


def materialization_event_id(request: dict[str, Any]) -> str:
    return canonical_sha256(materialization_attestation_preimage(request))


def read_strict_json(stream: BinaryIO | TextIO) -> Any:
    raw = stream.read(ContractV1.MAX_INPUT_BYTES + 1)
    if isinstance(raw, str):
        try:
            payload = raw.encode("utf-8", "strict")
        except UnicodeEncodeError as exc:
            raise ContractViolation("INPUT_SCHEMA_INVALID", "input is not UTF-8") from exc
    else:
        payload = raw
    if len(payload) > ContractV1.MAX_INPUT_BYTES:
        raise ContractViolation("INPUT_SCHEMA_INVALID", "input exceeds size limit")
    if not payload:
        raise ContractViolation("INPUT_SCHEMA_INVALID", "empty input")
    try:
        text = payload.decode("utf-8", "strict")
        return json.loads(
            text,
            object_pairs_hook=_pairs_no_duplicates,
            parse_constant=_reject_constant,
        )
    except ContractViolation:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ContractViolation("INPUT_SCHEMA_INVALID", "invalid strict UTF-8 JSON") from exc


def write_strict_json(value: Any, stream: BinaryIO | TextIO) -> None:
    payload = canonical_json_bytes(value)
    try:
        stream.write(payload)  # type: ignore[arg-type]
    except TypeError:
        stream.write(payload.decode("utf-8"))  # type: ignore[arg-type]
    stream.flush()


def _require_exact_keys(value: Any, keys: frozenset[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractViolation("INPUT_SCHEMA_INVALID", f"{label} must be an object")
    actual = frozenset(value)
    if actual != keys:
        missing = sorted(keys - actual)
        unknown = sorted(actual - keys)
        raise ContractViolation(
            "INPUT_SCHEMA_INVALID", f"{label} keys mismatch; missing={missing}; unknown={unknown}"
        )
    return value


def _require_string(value: Any, label: str, *, absolute: bool = False) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise ContractViolation("INPUT_SCHEMA_INVALID", f"{label} must be a non-empty string")
    if absolute:
        if not value.startswith("/") or posixpath.normpath(value) != value or value == "/":
            raise ContractViolation(
                "INPUT_SCHEMA_INVALID", f"{label} must be a canonical absolute POSIX path"
            )
    return value


def _require_token(value: Any, label: str) -> str:
    text = _require_string(value, label)
    if ContractV1.TOKEN_RE.fullmatch(text) is None:
        raise ContractViolation("INPUT_SCHEMA_INVALID", f"{label} is not a valid token")
    return text


def _require_sha256(value: Any, label: str) -> str:
    text = _require_string(value, label)
    if ContractV1.SHA256_RE.fullmatch(text) is None:
        raise ContractViolation("INPUT_SCHEMA_INVALID", f"{label} must be lowercase SHA-256")
    return text


def validate_request(value: Any) -> dict[str, Any]:
    """Validate a strict V1 external attestation without touching the filesystem.

    ``fresh_root_nonexistent_before`` is owned by the existing Rule13/Rule16
    acquisition/materialisation procedure.  This validator binds that
    attestation to the authority, session, private locator and expected current
    full-root manifest; it does not claim to recreate historical nonexistence.
    The checker independently binds ``lock_raw_sha256`` to the tracked lock
    bytes.  The logical lock, projection, requirements and accepted-wheel
    identities remain frozen external-attestation inputs to this V1 checker.
    """

    request = _require_exact_keys(value, ContractV1.REQUEST_KEYS, "request")
    if request["schema_version"] != ContractV1.REQUEST_SCHEMA:
        raise ContractViolation("SCHEMA_OR_VERSION_INVALID", "unsupported request schema")
    _require_token(request["authority_id"], "authority_id")
    session_id = _require_token(request["observation_session_id"], "observation_session_id")

    materialization = _require_exact_keys(
        request["materialization"], ContractV1.MATERIALIZATION_KEYS, "materialization"
    )
    _require_sha256(materialization["event_id"], "materialization.event_id")
    procedure_ids = materialization["procedure_ids"]
    if not isinstance(procedure_ids, list) or len(procedure_ids) != 2:
        raise ContractViolation("FRESHNESS_UNPROVED", "procedure_ids must contain exact2 owners")
    for index, item in enumerate(procedure_ids):
        _require_token(item, f"materialization.procedure_ids[{index}]")
    if tuple(procedure_ids) != ContractV1.EXPECTED_PROCEDURE_IDS:
        raise ContractViolation("FRESHNESS_UNPROVED", "procedure_ids do not match tracked exact2")
    if materialization["fresh_root_nonexistent_before"] is not True:
        raise ContractViolation("FRESHNESS_UNPROVED", "fresh root evidence is not true")
    if type(materialization["prior_artifact_reuse_count"]) is not int or materialization[
        "prior_artifact_reuse_count"
    ] != 0:
        raise ContractViolation("PAST_ARTIFACT_REUSE_DETECTED", "reuse count must be integer zero")
    root = _require_string(materialization["root"], "materialization.root", absolute=True)
    root_locator = _require_sha256(
        materialization["root_locator_sha256"],
        "materialization.root_locator_sha256",
    )
    if root_locator != runtime_root_locator_sha256(root):
        raise ContractViolation("FRESHNESS_UNPROVED", "runtime root locator binding mismatch")
    _require_sha256(
        materialization["expected_full_root_manifest_sha256"],
        "materialization.expected_full_root_manifest_sha256",
    )
    relative = _require_string(
        materialization["site_packages_relative"], "materialization.site_packages_relative"
    )
    if (
        relative != ContractV1.EXPECTED_SITE_PACKAGES_RELATIVE
        or relative.startswith("/")
        or posixpath.normpath(relative) != relative
        or any(part in ("", ".", "..") for part in relative.split("/"))
    ):
        raise ContractViolation("INPUT_SCHEMA_INVALID", "site_packages_relative is not canonical")
    probe_cwd = _require_string(
        materialization["probe_cwd"], "materialization.probe_cwd", absolute=True
    )
    if posixpath.commonpath((root, probe_cwd)) in (root, probe_cwd):
        raise ContractViolation(
            "INPUT_SCHEMA_INVALID", "probe_cwd and runtime root must not contain each other"
        )

    runtime = _require_exact_keys(request["runtime"], ContractV1.RUNTIME_KEYS, "runtime")
    executable = _require_string(runtime["executable"], "runtime.executable", absolute=True)
    if executable != posixpath.join(root, ContractV1.EXPECTED_EXECUTABLE_RELATIVE):
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "runtime executable locator mismatch")
    if runtime["implementation"] != ContractV1.EXPECTED_IMPLEMENTATION:
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "runtime implementation mismatch")
    if runtime["python_version"] != ContractV1.EXPECTED_PYTHON_VERSION:
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "Python version mismatch")
    if runtime["platform_tag"] != ContractV1.EXPECTED_PLATFORM_TAG:
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "platform tag mismatch")
    interpreter_sha256 = _require_sha256(
        runtime["resolved_interpreter_sha256"], "runtime.resolved_interpreter_sha256"
    )
    if interpreter_sha256 != ContractV1.EXPECTED_INTERPRETER_SHA256:
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "runtime interpreter digest mismatch")

    frozen = _require_exact_keys(request["frozen"], ContractV1.FROZEN_KEYS, "frozen")
    for key in ("mashos_api_commit", "mashos_api_tree"):
        oid = _require_string(frozen[key], f"frozen.{key}")
        if ContractV1.GIT_OID_RE.fullmatch(oid) is None:
            raise ContractViolation("INPUT_SCHEMA_INVALID", f"frozen.{key} must be a Git object id")
    fixed = {
        "lock_raw_sha256": ContractV1.LOCK_RAW_SHA256,
        "lock_logical_sha256": ContractV1.LOCK_LOGICAL_SHA256,
        "projection_sha256": ContractV1.PROJECTION_SHA256,
        "requirements_sha256": ContractV1.REQUIREMENTS_SHA256,
        "wheel_manifest_sha256": ContractV1.WHEEL_MANIFEST_SHA256,
        "distribution_closure_sha256": ContractV1.DISTRIBUTION_CLOSURE_SHA256,
        "installed_manifest_comparator_sha256": ContractV1.INSTALLED_MANIFEST_COMPARATOR_SHA256,
    }
    for key, expected in fixed.items():
        actual = _require_sha256(frozen[key], f"frozen.{key}")
        if actual != expected:
            raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", f"frozen.{key} mismatch")

    handoff = _require_exact_keys(request["handoff"], ContractV1.HANDOFF_KEYS, "handoff")
    if _require_token(handoff["receiver_session_id"], "handoff.receiver_session_id") != session_id:
        raise ContractViolation("HANDOFF_INVALID", "receiver session is not the observed session")
    _require_token(handoff["receiver_nonce"], "handoff.receiver_nonce")
    if materialization["event_id"] != materialization_event_id(request):
        raise ContractViolation(
            "FRESHNESS_UNPROVED", "materialization event canonical identity mismatch"
        )
    return request


def validate_role_result(value: Any, expected_role: str) -> dict[str, Any]:
    result = _require_exact_keys(value, ContractV1.ROLE_RESULT_KEYS, f"{expected_role} result")
    if result["schema_version"] != ContractV1.ROLE_RESULT_SCHEMA:
        raise ContractViolation("SCHEMA_OR_VERSION_INVALID", "unsupported role result schema")
    if result["role"] != expected_role or result["status"] != "VALID":
        raise ContractViolation(f"{expected_role.upper()}_INVALID", "role did not return VALID")
    if type(result["process_id"]) is not int or result["process_id"] <= 0:
        raise ContractViolation("PROCESS_CARDINALITY_OR_LAUNCH_INVALID", "invalid process id")
    expected_strategy = {
        "owner": "DISTRIBUTION_FIRST_RECORD_CLAIM_CONSTRUCTION",
        "independent": "FILESYSTEM_FIRST_REVERSE_OWNERSHIP_RECONCILIATION",
    }.get(expected_role)
    if expected_strategy is None or result["strategy"] != expected_strategy:
        raise ContractViolation(f"{expected_role.upper()}_INVALID", "role strategy mismatch")
    identity = _require_exact_keys(
        result["runtime_identity_exact19"],
        frozenset(ContractV1.RUNTIME_IDENTITY_EXACT19_KEYS),
        "runtime_identity_exact19",
    )
    for key in ContractV1.RUNTIME_IDENTITY_EXACT19_KEYS[:15]:
        _require_sha256(identity[key], f"runtime_identity_exact19.{key}")
    if identity["admitted_executable_relative_path"] != ContractV1.EXPECTED_EXECUTABLE_RELATIVE:
        raise ContractViolation(f"{expected_role.upper()}_INVALID", "admitted executable mismatch")
    for key, expected in (
        ("formal_lock_logical_sha256", ContractV1.LOCK_LOGICAL_SHA256),
        ("runner_projection_sha256", ContractV1.PROJECTION_SHA256),
        ("accepted_wheel_manifest_sha256", ContractV1.WHEEL_MANIFEST_SHA256),
        ("distribution_closure_sha256", ContractV1.DISTRIBUTION_CLOSURE_SHA256),
        ("installed_file_manifest_sha256", ContractV1.INSTALLED_MANIFEST_COMPARATOR_SHA256),
        ("resolved_interpreter_executable_sha256", ContractV1.EXPECTED_INTERPRETER_SHA256),
        ("environment_policy_sha256", ContractV1.ENVIRONMENT_POLICY_SHA256),
        ("required_role_path_ordered_sha256", ContractV1.REQUIRED_ROLE_PATH_ORDERED_SHA256),
    ):
        if identity[key] != expected:
            raise ContractViolation(f"{expected_role.upper()}_INVALID", f"{key} mismatch")
    if any(
        type(identity[key]) is not int
        for key in (
            "distribution_count",
            "record_closure_match_count",
            "unexpected_entry_count",
        )
    ) or (
        identity["distribution_count"] != 5
        or identity["record_closure_match_count"] != 5
        or identity["unexpected_entry_count"] != 0
    ):
        raise ContractViolation(f"{expected_role.upper()}_INVALID", "identity count mismatch")
    _require_sha256(result["manifest_sha256"], "role.manifest_sha256")
    rows = result["manifest_rows"]
    if not isinstance(rows, list):
        raise ContractViolation(f"{expected_role.upper()}_INVALID", "manifest_rows must be a list")
    previous: tuple[int, str] | None = None
    slots = {name: index for index, (name, _version) in enumerate(ContractV1.EXPECTED_DISTRIBUTIONS)}
    for row in rows:
        item = _require_exact_keys(row, ContractV1.MANIFEST_ROW_KEYS, "manifest row")
        name = _require_string(
            item["normalized_distribution_name"],
            "manifest row normalized_distribution_name",
        )
        if name not in slots:
            raise ContractViolation(f"{expected_role.upper()}_INVALID", "unexpected distribution")
        path = _require_string(item["relative_path"], "manifest row path")
        if (
            path.startswith("/")
            or "\\" in path
            or posixpath.normpath(path) != path
            or any(part in ("", ".", "..") for part in path.split("/"))
            or any(ord(character) < 32 or ord(character) == 127 for character in path)
        ):
            raise ContractViolation(f"{expected_role.upper()}_INVALID", "non-canonical manifest path")
        if type(item["byte_count"]) is not int or item["byte_count"] < 0:
            raise ContractViolation(f"{expected_role.upper()}_INVALID", "invalid manifest byte count")
        _require_sha256(item["raw_sha256"], "manifest row raw_sha256")
        order = (slots[name], path)
        if previous is not None and order <= previous:
            raise ContractViolation(f"{expected_role.upper()}_INVALID", "manifest order/uniqueness invalid")
        previous = order
    if len(rows) != ContractV1.EXPECTED_MANIFEST_ROW_COUNT:
        raise ContractViolation(f"{expected_role.upper()}_INVALID", "manifest row count mismatch")
    if canonical_sha256(rows) != result["manifest_sha256"]:
        raise ContractViolation(f"{expected_role.upper()}_INVALID", "manifest digest mismatch")
    if result["manifest_sha256"] != ContractV1.INSTALLED_MANIFEST_COMPARATOR_SHA256:
        raise ContractViolation(f"{expected_role.upper()}_INVALID", "current comparator mismatch")
    closures = result["distribution_closures"]
    if not isinstance(closures, list) or len(closures) != len(ContractV1.EXPECTED_DISTRIBUTIONS):
        raise ContractViolation(f"{expected_role.upper()}_INVALID", "closure cardinality mismatch")
    for index, closure in enumerate(closures):
        item = _require_exact_keys(
            closure, ContractV1.DISTRIBUTION_CLOSURE_KEYS, "distribution closure"
        )
        expected_name, expected_version, expected_closure = ContractV1.EXPECTED_RECORD_CLOSURES[index]
        if (
            item["normalized_distribution_name"] != expected_name
            or item["distribution_version"] != expected_version
            or item["installed_record_closure_sha256"] != expected_closure
        ):
            raise ContractViolation(f"{expected_role.upper()}_INVALID", "closure slot mismatch")
        _require_sha256(item["installed_record_closure_sha256"], "record closure digest")
    if canonical_sha256(closures) != ContractV1.DISTRIBUTION_CLOSURE_SHA256:
        raise ContractViolation(f"{expected_role.upper()}_INVALID", "aggregate closure mismatch")
    diagnostic = _require_exact_keys(
        result["canonical_diagnostic"],
        ContractV1.CANONICAL_DIAGNOSTIC_KEYS,
        "canonical_diagnostic",
    )
    integer_fields = ContractV1.CANONICAL_DIAGNOSTIC_KEYS - {
        "external_entrypoint_pathset_sha256",
        "canonical_pathset_sha256",
        "mismatch_row_sha256",
    }
    for key in integer_fields:
        if type(diagnostic[key]) is not int or diagnostic[key] < 0:
            raise ContractViolation(f"{expected_role.upper()}_INVALID", f"diagnostic {key} invalid")
    for key in (
        "external_entrypoint_pathset_sha256",
        "canonical_pathset_sha256",
        "mismatch_row_sha256",
    ):
        _require_sha256(diagnostic[key], f"canonical_diagnostic.{key}")
    if (
        diagnostic["canonical_row_count"] != ContractV1.EXPECTED_MANIFEST_ROW_COUNT
        or diagnostic["canonical_preimage_bytes"]
        != ContractV1.EXPECTED_CANONICAL_PREIMAGE_BYTES
        or diagnostic["canonical_preimage_lf"] != 0
        or diagnostic["site_regular_file_count"]
        != ContractV1.EXPECTED_SITE_REGULAR_FILE_COUNT
        or diagnostic["site_directory_count"] != ContractV1.EXPECTED_SITE_DIRECTORY_COUNT
        or diagnostic["eligible_regular_payload_count"] != ContractV1.EXPECTED_MANIFEST_ROW_COUNT
        or diagnostic["owned_file_count"] != ContractV1.EXPECTED_MANIFEST_ROW_COUNT
        or diagnostic["record_self_excluded_count"] != 5
        or diagnostic["verified_external_entrypoint_count"]
        != ContractV1.EXPECTED_EXTERNAL_ENTRYPOINT_COUNT
        or diagnostic["external_entrypoint_pathset_sha256"]
        != ContractV1.EXPECTED_EXTERNAL_ENTRYPOINT_PATHSET_SHA256
        or diagnostic["canonical_pathset_sha256"]
        != ContractV1.EXPECTED_CANONICAL_PATHSET_SHA256
        or diagnostic["mismatch_row_sha256"]
        != ContractV1.EXPECTED_EMPTY_MISMATCH_ROW_SHA256
    ):
        raise ContractViolation(f"{expected_role.upper()}_INVALID", "diagnostic cardinality mismatch")
    for key in (
        "site_symlink_count",
        "site_other_count",
        "unowned_file_count",
        "duplicate_relative_path_count",
        "missing_file_count",
        "extra_file_count",
        "pyc_file_count",
        "pycache_directory_count",
        "mismatch_row_count",
        "nonzero_mismatch_family_count",
    ):
        if diagnostic[key] != 0:
            raise ContractViolation(f"{expected_role.upper()}_INVALID", f"diagnostic {key} nonzero")
    return result


def validate_public_result(value: Any) -> dict[str, Any]:
    """Validate a body-free success or STOP projection; reject all extensions."""

    if not isinstance(value, dict):
        raise ContractViolation("PRIVACY_VIOLATION", "public result is not an object")
    if value.get("status") == "VALID":
        if frozenset(value) != ContractV1.PUBLIC_SUCCESS_KEYS:
            raise ContractViolation("PRIVACY_VIOLATION", "public success field set invalid")
        result = value
        if (
            result["schema_version"] != ContractV1.PUBLIC_RESULT_SCHEMA
            or result["method_id"] != ContractV1.METHOD_ID
            or result["terminal"] != "RUNTIME_READY_CURRENT_SESSION_STOP"
            or result["checks_completed"] != list(ContractV1.CHECK_ORDER)
            or result["primary_outcome"] != "TECHNICAL_CREDIT"
            or result["runtime_ready"] is not True
            or result["gate_b_closed"] is not True
            or result["handoff_state"] != "HANDOFF_BOUND_CURRENT_SESSION"
            or result["handoff_consumed"] is not False
            or result["gate_c_authorized"] is not False
            or type(result["target_execution_count"]) is not int
            or result["target_execution_count"] != 0
            or result["automatic_progression"] is not False
        ):
            raise ContractViolation("PRIVACY_VIOLATION", "public success semantics invalid")
        for key in (
            "runtime_readiness_observation_id",
            "runtime_instance_observation_id",
            "installed_file_manifest_sha256",
            "runtime_identity_exact19_sha256",
            "canonical_diagnostic_sha256",
            "handoff_binding_sha256",
        ):
            _require_sha256(result[key], f"public success.{key}")
        if result["installed_file_manifest_sha256"] != ContractV1.INSTALLED_MANIFEST_COMPARATOR_SHA256:
            raise ContractViolation("PRIVACY_VIOLATION", "public comparator identity invalid")
        return result
    if value.get("status") == "STOP":
        if frozenset(value) != ContractV1.PUBLIC_STOP_KEYS:
            raise ContractViolation("PRIVACY_VIOLATION", "public STOP field set invalid")
        result = value
        if (
            result["schema_version"] != ContractV1.PUBLIC_RESULT_SCHEMA
            or result["method_id"] != ContractV1.METHOD_ID
            or result["terminal"] not in ContractV1.STOP_CODES
            or result["primary_outcome"] != "BLOCKER_NARROWED"
            or result["runtime_ready"] is not False
            or result["gate_b_closed"] is not False
            or result["handoff_state"] != "NOT_BOUND"
            or result["handoff_consumed"] is not False
            or result["gate_c_authorized"] is not False
            or type(result["target_execution_count"]) is not int
            or result["target_execution_count"] != 0
            or result["automatic_progression"] is not False
        ):
            raise ContractViolation("PRIVACY_VIOLATION", "public STOP semantics invalid")
        return result
    raise ContractViolation("PRIVACY_VIOLATION", "public result status invalid")
