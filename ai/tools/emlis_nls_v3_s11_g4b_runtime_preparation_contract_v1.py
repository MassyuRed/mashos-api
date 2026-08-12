#!/usr/bin/env python3
"""Immutable contract for the G4-B runtime-preparation controller family V1.

This module owns only canonicalisation, public policy constants, schemas, and
pure validation.  Importing it performs no filesystem, environment, clock,
random, process, or network operation.  The effect-owning modules deliberately
depend on this module in one direction.
"""

from __future__ import annotations

import copy
import datetime as _datetime
import hashlib
import json
import posixpath
import re
import unicodedata
from typing import Any, NoReturn


__all__ = (
    "PreparationViolation",
    "PreparationContractV1",
    "canonical_json_bytes",
    "canonical_file_bytes",
    "canonical_sha256",
    "strict_json_from_bytes",
    "validate_lock_derivation",
    "derive_requirements_bytes",
    "validate_stable_authority_approval",
    "validate_execution_request",
    "validate_path_plan",
    "validate_public_result",
    "validate_durable_publication_transition",
)


class PreparationViolation(ValueError):
    """A deterministic fail-closed contract violation."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


def _fail(code: str, detail: str) -> NoReturn:
    raise PreparationViolation(code, detail)


def _normalise(value: Any, location: str = "$", *, reject_non_nfc: bool = False) -> Any:
    if value is None or type(value) in (bool, int):
        return value
    if type(value) is float:
        _fail("JSON_NUMBER_INVALID", f"{location}: floating point is forbidden")
    if type(value) is str:
        if "\x00" in value:
            _fail("JSON_STRING_INVALID", f"{location}: NUL is forbidden")
        normal = unicodedata.normalize("NFC", value)
        if reject_non_nfc and normal != value:
            _fail("JSON_NON_NFC", location)
        return normal
    if type(value) is list or type(value) is tuple:
        return [
            _normalise(item, f"{location}[{index}]", reject_non_nfc=reject_non_nfc)
            for index, item in enumerate(value)
        ]
    if type(value) is dict:
        result: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                _fail("JSON_KEY_INVALID", f"{location}: key must be a string")
            normal_key = _normalise(
                key, f"{location}.<key>", reject_non_nfc=reject_non_nfc
            )
            if normal_key in result:
                _fail("JSON_NORMALIZED_KEY_COLLISION", f"{location}.{normal_key}")
            result[normal_key] = _normalise(
                item, f"{location}.{normal_key}", reject_non_nfc=reject_non_nfc
            )
        return result
    _fail("JSON_TYPE_INVALID", f"{location}: {type(value).__name__}")


def canonical_json_bytes(value: Any) -> bytes:
    """Return compact, sorted, NFC, UTF-8 JSON without a final LF."""

    normal = _normalise(value)
    try:
        return json.dumps(
            normal,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        _fail("CANONICAL_JSON_INVALID", type(exc).__name__)


def canonical_file_bytes(value: Any) -> bytes:
    """Return canonical JSON followed by exactly one LF."""

    return canonical_json_bytes(value) + b"\n"


def canonical_sha256(value: Any) -> str:
    """Hash bytes verbatim, or hash an object's canonical JSON representation."""

    if isinstance(value, (bytes, bytearray, memoryview)):
        payload = bytes(value)
    else:
        payload = canonical_json_bytes(value)
    return hashlib.sha256(payload).hexdigest()


def _reject_constant(_value: str) -> NoReturn:
    _fail("JSON_NUMBER_INVALID", "non-finite number token")


def _pairs_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _fail("JSON_DUPLICATE_KEY", key)
        result[key] = value
    return result


def _parse_json(payload: bytes, *, canonical: bool, final_lf: bool) -> Any:
    if not isinstance(payload, bytes):
        _fail("JSON_BYTES_REQUIRED", type(payload).__name__)
    if payload.startswith(b"\xef\xbb\xbf"):
        _fail("JSON_BOM_FORBIDDEN", "UTF-8 BOM")
    if b"\r" in payload:
        _fail("JSON_CR_FORBIDDEN", "CR byte")
    if final_lf:
        if not payload.endswith(b"\n") or payload.endswith(b"\n\n"):
            _fail("JSON_FINAL_LF_INVALID", "exactly one final LF required")
        body = payload[:-1]
        if b"\n" in body and canonical:
            _fail("JSON_CANONICALITY_INVALID", "interior LF")
    else:
        if payload.endswith(b"\n"):
            _fail("JSON_FINAL_LF_FORBIDDEN", "unexpected final LF")
        body = payload
    try:
        text = body.decode("utf-8", "strict")
    except UnicodeDecodeError:
        _fail("JSON_UTF8_INVALID", "strict UTF-8 decode failed")
    try:
        value = json.loads(
            text,
            object_pairs_hook=_pairs_without_duplicates,
            parse_constant=_reject_constant,
            parse_float=lambda _value: _fail(
                "JSON_NUMBER_INVALID", "floating point is forbidden"
            ),
        )
    except PreparationViolation:
        raise
    except (json.JSONDecodeError, UnicodeError, ValueError) as exc:
        _fail("JSON_PARSE_INVALID", type(exc).__name__)
    _normalise(value, reject_non_nfc=True)
    if canonical and canonical_json_bytes(value) != body:
        _fail("JSON_CANONICALITY_INVALID", "bytes differ from canonical serialization")
    return value


def strict_json_from_bytes(payload: bytes, *, require_final_lf: bool = False) -> Any:
    """Parse only byte-exact canonical JSON, optionally with exactly one final LF."""

    return _parse_json(payload, canonical=True, final_lf=require_final_lf)


class PreparationContractV1:
    """Frozen public constants and schema keysets for functional exact7."""

    METHOD_ID = "G4B_RUNTIME_PREPARATION_CONTROLLER_FAMILY_V1"
    CANDIDATE_ID = (
        "NLS_V3_STEP11_CYCLE001_G4_GATE_B_RUNTIME_PREPARATION_CONTROLLER_"
        "FAMILY_V1_FUNCTIONAL_EXACT7_JOINT_IMPLEMENTATION_CANDIDATE_"
        "CORRECTED_DRAFT_V3"
    )
    APPROVED_CANDIDATE_BODY_SHA256 = (
        "3eae1025095726a29ec01d37ab4e5056270d115722a746d95ab7744e1aa03bf2"
    )

    FORMAL_LOCK_RAW_SHA256 = (
        "9bb2875541a6d959c1dca47cb5b96de5b0041ccf5288e849c469c15a8b310787"
    )
    DERIVED_LOCK_LOGICAL_SHA256 = (
        "1e5b243a9d610f9d4d469a6b3424a88ea8022557c8fffe79d676326840f1004d"
    )
    DERIVED_LOCK_BODY_SHA256 = (
        "0292b3d74ffc307105d8fa63f78e5e1cee3664882350aec226f796d251084dab"
    )
    DERIVED_LOCK_RAW_SHA256 = (
        "8c0e3482089e6420f624e93ba974897e01ee777740e8b7af133e1a6c293767c8"
    )
    DERIVED_LOCK_GIT_BLOB = "259e8f2c96e87b2f1fa66349c880cc57ac0fc7e4"
    DERIVED_LOCK_LOGICAL_BYTES = 5057
    DERIVED_LOCK_BODY_BYTES = 5138
    DERIVED_LOCK_RAW_BYTES = 5139
    PROJECTION_SHA256 = (
        "f501025c1dccef68c47c0a3e52f3ef74d01233f371b16f2b1a0bdfb21089e57e"
    )
    REQUIREMENTS_SHA256 = (
        "4f7218509a20e42850afe75597f2abfdf447035001847621d4637faa246065f1"
    )
    REQUIREMENTS_BYTES = 473
    ACCEPTED_WHEEL_MANIFEST_SHA256 = (
        "00d2df98c8cda7f1473794892bafe7ccd18cc816c79ccb346f3e21ff629b136d"
    )
    WHEEL_RECORD_MANIFEST_SHA256 = (
        "61006261c4aebbb68d941153cdb5be4feb753f1bd638a500dc389b6f4e506fae"
    )
    DISTRIBUTION_CLOSURE_SHA256 = (
        "4d3d6afdac2b9a606d4797ff5fbe65010faddf0de9788202798ddb8d95e6556c"
    )
    ENVIRONMENT_POLICY_SHA256 = (
        "24944cb1b02cae519768de1b32748809a0de690c517e81e0f756a4f5c3be46d0"
    )

    ACQUISITION_POLICY_ID = (
        "EXPLICIT_OFFICIAL_PUBLIC_PYPI_EXACT2_HOST_HASH_LOCKED_ONE_SHOT_"
        "ACQUISITION_POLICY_V1"
    )
    AUTHORITY_POLICY_ID = (
        "G4B_RUNTIME_PREPARATION_CONTROLLER_FAMILY_V1_ONE_SHOT_LIVE_"
        "AUTHORITY_POLICY"
    )
    EGRESS_ISSUER_CLASS = "WORK_PLATFORM_CONTROL_PLANE_ATTESTATION_V1"
    EGRESS_ISSUER_POLICY_ID = "WORK_PLATFORM_EXACT2_HOST_EGRESS_ENFORCEMENT_V1"
    PRIMARY_INDEX_URL = "https://pypi.org/simple/"
    ALLOWED_SCHEME = "https"
    ALLOWED_HOSTS = ("files.pythonhosted.org", "pypi.org")
    ACQUISITION_PROCESS_COUNT = 1
    ATTESTATION_ISSUE_PHASE = (
        "AFTER_MASH_AUTHORITY_APPROVAL_BEFORE_P1_REQUEST_FINALIZATION"
    )
    ATTESTATION_MAX_LIFETIME_SECONDS = 900
    MINIMUM_REMAINING_LIFETIME_AT_P3_SECONDS = 330
    RESULT_UNKNOWN_POLICY = "FRESH_TARGET_READ_NO_BLIND_REWRITE_NO_TECHNICAL_RERUN"

    EXPECTED_INTERPRETER_SHA256 = (
        "9ed008e5a8685235361f0c53771b520ab082dd99a877ad2fd796a93fa4c0b488"
    )
    EXPECTED_IMPLEMENTATION = "CPython"
    EXPECTED_PYTHON_VERSION = "3.12.13"
    EXPECTED_PLATFORM_TAG = "linux-x86_64"
    EXPECTED_PIP_VERSION = "26.0.1"
    PIP_MAIN_PARSER_SHA256 = (
        "623cc9023a9fefc01136c2e59c94fd97a7cd6e9c833c903e6ab3885d8b0ae489"
    )
    PIP_BUILD_ENV_SHA256 = (
        "5e980e2254d02e0cf73ef0d3da7ee3d8dcd7feb54564b0881bbb7b6f675d85c3"
    )
    PIP_RUNNER_SHA256 = (
        "24ea04653c2bb6fee345a5c1920490280134e323727c59861f1aa91e2187bcbd"
    )
    P5_STATIC_PROOF_STATE = (
        "CURRENT_WORK_READ_ONLY_STATIC_SOURCE_BRANCH_PROVEN__LIVE_OS_EDGE_UNOBSERVED"
    )
    PROCEDURE_IDS = (
        "COCOLON_RULE13_RUNTIME_CONTINUITY_V20260811",
        "COCOLON_RULE16_ONE_SHOT_PRELAUNCH_V20260811",
    )
    SITE_PACKAGES_RELATIVE = "lib/python3.12/site-packages"

    EXECUTION_REQUEST_SCHEMA = "emlis.nls_v3.s11.g4b.runtime_preparation.request.v1"
    STABLE_AUTHORITY_APPROVAL_SCHEMA = (
        "emlis.nls_v3.s11.g4b.runtime_preparation.stable_authority_approval.v1"
    )
    PRIVATE_TRANSPORT_SCHEMA = (
        "emlis.nls_v3.s11.g4b.runtime_preparation.private_transport.v1"
    )
    EGRESS_ATTESTATION_SOURCE_SCHEMA = (
        "emlis.nls_v3.s11.g4b.runtime_preparation.egress_attestation_source.v1"
    )
    EGRESS_ATTESTATION_SCHEMA = (
        "emlis.nls_v3.s11.g4b.runtime_preparation.egress_attestation.v1"
    )
    PUBLICATION_CONTRACT_SCHEMA = (
        "emlis.nls_v3.s11.g4b.runtime_preparation.publication_contract.v1"
    )
    TRANSPORT_BINDING_SCHEMA = (
        "emlis.nls_v3.s11.g4b.runtime_preparation.transport_binding.v1"
    )
    ACQUISITION_OBSERVATION_SCHEMA = (
        "emlis.nls_v3.s11.g4b.runtime_preparation.acquisition_observation.v1"
    )
    MATERIALIZATION_ATTESTATION_SCHEMA = (
        "emlis.nls_v3.s11.g4b.runtime_preparation.materialization_attestation.v1"
    )
    MATERIALIZATION_EVENT_SCHEMA = (
        "emlis.nls_v3.s11.g4b.runtime_materialization.external_attestation.v1"
    )
    COMPOSITE_BINDING_SCHEMA = (
        "emlis.nls_v3.s11.g4b.runtime_preparation.composite_binding.v1"
    )
    PRIVATE_HANDOFF_SCHEMA = (
        "emlis.nls_v3.s11.g4b.runtime_preparation.private_handoff.v1"
    )
    PUBLIC_RESULT_SCHEMA = (
        "emlis.nls_v3.s11.g4b.runtime_preparation.public_result.v1"
    )
    DURABLE_TRANSITION_SCHEMA = (
        "emlis.nls_v3.s11.g4b.runtime_preparation.durable_transition.v1"
    )
    TERMINAL_EVIDENCE_SCHEMA = (
        "emlis.nls_v3.s11.g4b.runtime_preparation.terminal_evidence.v1"
    )

    DERIVED_TOP_KEYS = frozenset(
        {
            "schema_version", "identity_class", "target", "root_imports",
            "root_requirements", "module_distribution_map", "distribution_count",
            "distributions", "pip_require_hashes_lines", "resolution", "lock_sha256",
        }
    )
    DERIVED_TARGET_KEYS = frozenset(
        {
            "abi_flags", "byte_order", "implementation", "machine", "platform",
            "python_cache_tag", "python_version", "wheel_only",
        }
    )
    DERIVED_ROW_KEYS = frozenset(
        {
            "normalized_distribution_name", "distribution_version", "wheel_filename",
            "wheel_sha256", "wheel_record_sha256", "installed_record_closure_sha256",
            "requires_dist", "selected_dependency_names", "top_level_imports",
        }
    )
    DERIVED_RESOLUTION_KEYS = frozenset(
        {
            "activated_extras", "allow_sdist", "hashes_required",
            "index_access_during_install", "installation_mode",
            "installed_record_closure_rule", "marker_environment",
            "namespace_module_distribution_map", "only_binary", "pip_version",
            "reachable_distribution_count", "resolver", "root_requirement_count",
            "unresolved_dependency_count",
        }
    )
    EXACT5_NAMES = ("iniconfig", "packaging", "pluggy", "pygments", "pytest")
    MODULE_DISTRIBUTION_MAP = (
        ("_pytest", "pytest"), ("iniconfig", "iniconfig"),
        ("packaging", "packaging"), ("pluggy", "pluggy"),
        ("py", "pytest"), ("pygments", "pygments"), ("pytest", "pytest"),
    )

    EXECUTION_REQUEST_KEYS = frozenset(
        {
            "schema_version", "candidate_id", "approved_candidate_body_sha256",
            "stable_authority_approval_binding_sha256", "authority_id",
            "observation_session_id", "receiver_session_id", "receiver_nonce",
            "expected_git", "control_runtime", "path_plan", "private_transport",
            "egress_attestation_source", "egress_attestation",
            "egress_attestation_sha256", "publication_contract",
        }
    )
    STABLE_AUTHORITY_APPROVAL_KEYS = frozenset(
        {
            "schema_version", "candidate_id", "approved_candidate_body_sha256",
            "authority_id", "authority_policy_id", "acquisition_policy_id",
            "egress_issuer_class", "egress_issuer_policy_id", "allowed_scheme",
            "allowed_hosts", "acquisition_process_count", "attestation_issue_phase",
            "attestation_max_lifetime_seconds",
            "minimum_remaining_lifetime_at_p3_seconds", "same_authority_reissue_allowed",
        }
    )
    EXPECTED_GIT_KEYS = frozenset(
        {"cocolon_commit", "cocolon_tree", "mashos_api_commit", "mashos_api_tree"}
    )
    CONTROL_RUNTIME_KEYS = frozenset(
        {
            "executable", "implementation", "python_version", "platform_tag",
            "resolved_interpreter_sha256", "pip_version",
            "pip_installed_source_manifest_sha256", "pip_main_parser_sha256",
            "pip_build_env_sha256", "pip_runner_sha256",
            "p5_static_launch_edge_proof_state",
        }
    )
    PRIVATE_TRANSPORT_KEYS = frozenset(
        {
            "schema_version", "https_proxy", "custom_ca_locator",
            "expected_proxy_class", "expected_ca_raw_sha256",
            "expected_stable_projection_sha256",
        }
    )
    EGRESS_ATTESTATION_SOURCE_KEYS = frozenset(
        {
            "schema_version", "private_locator", "expected_owner_class",
            "expected_mode", "expected_regular_file", "expected_nlink",
            "expected_raw_sha256", "expected_expiry",
        }
    )
    EGRESS_ATTESTATION_KEYS = frozenset(
        {
            "schema_version", "source_class", "issuer_policy_id",
            "platform_control_state_instance_id", "issuer_provenance_binding_sha256",
            "stable_authority_approval_binding_sha256", "approved_candidate_body_sha256",
            "policy_id", "allowed_scheme", "allowed_hosts", "enforcement_scope",
            "authority_id", "observation_session_id", "acquisition_process_count",
            "active", "issued_at", "expires_at",
        }
    )
    ISSUER_PROVENANCE_KEYS = (
        "schema_version", "source_class", "issuer_policy_id",
        "platform_control_state_instance_id", "stable_authority_approval_binding_sha256",
        "approved_candidate_body_sha256", "authority_id", "observation_session_id",
    )
    PUBLICATION_CONTRACT_KEYS = frozenset(
        {
            "schema_version", "cocolon_pre_head", "receipt_path", "current_state_path",
            "conditional_closure_route_path", "conditional_milestone_path",
            "approved_public_path_set_sha256", "result_unknown_policy",
        }
    )

    PATH_ROLE_NAMES = (
        "authority_root", "controller_test_cwd", "controller_test_temp_root",
        "requirements_file_outside_runtime", "wheel_root", "process_temp_root",
        "runtime_root", "checker_test_cwd", "checker_test_pytest_ini",
        "checker_test_basetemp", "checker_probe_cwd",
        "private_transport_binding_observation", "acquisition_observation",
        "materialization_attestation", "checker_request", "checker_result",
        "private_handoff", "terminal_evidence", "cleanup_ledger", "publication_staging",
    )
    PATH_ROLE_LEAVES = (
        ("controller_test_temp_root", "controller-test-tmp"),
        ("requirements_file_outside_runtime", "exact5-requirements.txt"),
        ("wheel_root", "wheelhouse"),
        ("process_temp_root", "process-tmp"),
        ("runtime_root", "runtime"),
        ("checker_test_pytest_ini", "checker-test.ini"),
        ("checker_test_basetemp", "checker-test-basetemp"),
        ("checker_probe_cwd", "checker-probe-cwd"),
        ("private_transport_binding_observation", "private-transport-binding.jsonl"),
        ("acquisition_observation", "acquisition-observation.json"),
        ("materialization_attestation", "materialization-attestation.json"),
        ("checker_request", "checker-request.json"),
        ("checker_result", "checker-result.json"),
        ("private_handoff", "private-handoff.json"),
        ("terminal_evidence", "terminal-evidence.json"),
        ("cleanup_ledger", "cleanup-ledger.jsonl"),
        ("publication_staging", "publication-staging.json"),
    )

    ACQUISITION_OBSERVATION_KEYS = frozenset(
        {
            "schema_version", "authority_id", "observation_session_id", "consumed",
            "process_launch_count", "argv_sha256", "environment_sha256",
            "egress_attestation_sha256", "egress_attestation_source_observation_sha256",
            "transport_b0_sha256", "transport_b1_sha256", "transport_b2_sha256",
            "returncode", "stdout_sha256", "stderr_sha256", "requirements_sha256",
            "accepted_wheel_rows", "accepted_wheel_manifest_sha256",
        }
    )
    # The frozen 674-byte manifest (00d2...) uses the formal-lock field names.
    # Short aliases such as ``filename``/``raw_sha256`` serialize to a different
    # body and therefore are not V1-compatible.
    ACCEPTED_WHEEL_ROW_KEYS = frozenset({"wheel_filename", "wheel_sha256"})
    MATERIALIZATION_ATTESTATION_KEYS = frozenset(
        {
            "schema_version", "authority_id", "observation_session_id", "event_id",
            "procedure_ids", "fresh_root_nonexistent_before", "prior_artifact_reuse_count",
            "runtime_root_locator_sha256", "site_packages_relative",
            "derived_lock_raw_sha256", "derived_lock_logical_sha256",
            "accepted_wheel_manifest_sha256", "wheel_record_rows",
            "wheel_record_manifest_sha256", "distribution_closure_sha256",
            "runtime_executable_locator_sha256", "resolved_interpreter_sha256",
            "installed_file_manifest_sha256", "full_runtime_root_manifest_sha256",
            "materialization_process_ledger_sha256", "environment_policy_sha256", "status",
        }
    )
    WHEEL_RECORD_ROW_KEYS = frozenset(
        {"wheel_filename", "wheel_sha256", "wheel_record_sha256"}
    )
    COMPOSITE_BINDING_KEYS = frozenset(
        {
            "schema_version", "authority_id", "observation_session_id",
            "formal_lock_raw_sha256", "formal_lock_logical_sha256",
            "derived_lock_git_blob", "derived_lock_raw_sha256",
            "derived_lock_logical_sha256", "preparation_contract_raw_sha256",
            "stable_authority_approval_binding_sha256", "execution_request_sha256",
            "projection_sha256", "requirements_sha256", "accepted_wheel_manifest_sha256",
            "wheel_record_manifest_sha256", "distribution_closure_sha256",
            "issuer_provenance_binding_sha256", "egress_attestation_source_observation_sha256",
            "egress_attestation_sha256", "transport_binding_observation_sha256",
            "acquisition_observation_sha256", "materialization_attestation_sha256",
            "checker_request_sha256", "checker_result_sha256", "handoff_binding_sha256",
        }
    )
    PRIVATE_HANDOFF_KEYS = frozenset(
        {
            "schema_version", "authority_id", "observation_session_id",
            "receiver_session_id", "receiver_nonce", "materialization_event_id",
            "runtime_root_locator_sha256", "runtime_executable_locator_sha256",
            "expected_full_root_manifest_sha256", "runtime_readiness_observation_id",
            "handoff_binding_sha256", "consumed",
        }
    )
    HANDOFF_BINDING_KEYS = frozenset(
        {
            "schema_version", "handoff_claim", "private_locator_holder",
            "consumer_observed", "observation_session_id", "receiver_session_id",
            "receiver_nonce", "mashos_api_commit", "mashos_api_tree",
            "freshness_evidence_class", "freshness_claim_limit",
            "materialization_event_id", "runtime_root_locator_sha256",
            "runtime_executable_locator_sha256",
            "expected_full_root_manifest_sha256", "runtime_instance_observation_id",
            "runtime_readiness_observation_id", "entrypoint_control_identity_sha256",
        }
    )
    TERMINAL_EVIDENCE_KEYS = frozenset(
        {
            "schema_version", "candidate_id", "authority_id", "observation_session_id",
            "activated", "consumed", "primary_terminal", "nested_checker_terminal",
            "checker_component_status", "cleanup_state", "retention_state",
            "publication_state", "process_ledger_sha256", "path_ledger_sha256",
            "composite_binding_sha256", "public_result_sha256", "cleanup_ledger_sha256",
            "created_at", "automatic_progression",
        }
    )
    PUBLIC_RESULT_KEYS = frozenset(
        {
            "schema_version", "method_id", "candidate_id",
            "authority_context_binding_sha256", "session_context_binding_sha256", "status",
            "primary_terminal", "nested_checker_terminal", "technical_primary_outcome",
            "activated", "consumed", "checker_execution_attempt_count",
            "checker_component_status", "composite_technical_result",
            "current_session_runtime_readiness", "gate_b_technical_condition",
            "handoff_state", "gate_c_authorized", "cleanup_state", "retention_state",
            "technical_chain_complete", "publication_state", "durable_work_complete",
            "durable_current_owner_state", "durable_current_owner_runtime_ready",
            "durable_current_owner_gate_b_closed", "durable_current_owner_readiness_credit",
            "durable_current_owner_technical_credit", "durable_current_owner_product_credit",
            "durable_current_owner_primary_outcome", "automatic_progression",
        }
    )
    DURABLE_TRANSITION_KEYS = frozenset(
        {
            "schema_version", "candidate_id", "authority_context_binding_sha256",
            "session_context_binding_sha256", "controller_public_result_sha256",
            "terminal_evidence_envelope_sha256", "publication_state",
            "remote_postverify_state", "durable_work_complete",
            "current_owner_runtime_ready", "current_owner_gate_b_closed",
            "current_owner_readiness_credit", "current_owner_technical_credit",
            "current_owner_product_credit", "current_owner_primary_outcome",
            "publication_staging_cleanup_state", "automatic_progression",
        }
    )

    PRIMARY_SUCCESS_TERMINAL = "HANDOFF_BOUND_CURRENT_SESSION"
    PRIMARY_STOP_TERMINALS = (
        "CONTROLLER_LAUNCH_REJECTED", "BASE_OR_PREIMAGE_DRIFT",
        "PATH_BUDGET_OR_SCOPE_EXCEEDED", "CONTROLLER_FOCUSED_TEST_INVALID",
        "PRIVATE_TRANSPORT_BINDING_INVALID", "HOST_EXCEPTION_NOT_ENFORCED",
        "ACQUISITION_PROCESS_INVALID", "ACQUISITION_ROUTE_INVALID",
        "ACQUIRED_WHEEL_SET_INVALID", "PRIVATE_TRANSPORT_DRIFT",
        "MATERIALIZATION_PROCESS_INVALID", "MATERIALIZATION_IDENTITY_INVALID",
        "CHECKER_DEDICATED_TEST_INVALID", "ADMISSION_BRIDGE_INVALID",
        "CHECKER_PROCESS_INVALID", "CHECKER_RETURNED_TYPED_STOP",
        "HANDOFF_BINDING_INVALID", "PRIVACY_VIOLATION", "INTERNAL_FAIL_CLOSED",
    )
    CONDITIONAL_LAUNCH_EDGE_TOPOLOGY = (
        "P1_CONTROLLER", "P2_FOCUSED_UNITTEST", "P3_PIP_DOWNLOAD",
        "P4_CONTROL_PIP_OFFLINE_INSTALL", "P5_TARGET_INTERPRETER_PIP_REEXEC",
        "P6_CHECKER_DEDICATED_TEST", "P7_CHECKER", "P8_OWNER",
        "P9_PYTEST_VERSION_PROBE", "P10_REQUIRED_ROLE_SMOKE", "P11_INDEPENDENT",
    )
    CLEANUP_LEDGER_KEYS = frozenset(
        {"sequence", "phase", "role", "action", "pre_state", "result", "post_state", "evidence_sha256"}
    )
    CLEANUP_PHASES = (
        "CONTROLLER_TEST", "ACQUISITION", "MATERIALIZATION", "CHECKER_TEST",
        "ADMISSION", "TERMINAL_CLEANUP", "TERMINAL_SEAL",
    )
    CLEANUP_ACTIONS = (
        "CREATE", "WRITE", "SEAL", "DELETE", "VERIFY_ABSENT", "RETAIN", "NOT_CREATED"
    )

    CONTROLLER_TOTAL_WALL_SECONDS = 3600
    FOCUSED_TEST_WALL_SECONDS = 300
    ACQUISITION_WALL_SECONDS = 300
    OFFLINE_INSTALL_WALL_SECONDS = 300
    IN_PROCESS_MATERIALIZATION_WALL_SECONDS = 300
    CHECKER_TEST_WALL_SECONDS = 600
    CHECKER_WALL_SECONDS = 900
    CLEANUP_RESERVE_SECONDS = 300
    CHILD_STREAM_BYTES = 1_048_576
    PUBLIC_STDOUT_BYTES = 65_536
    WHEEL_RAW_BYTES = 16_777_216
    WHEEL_AGGREGATE_BYTES = 33_554_432
    ZIP_MEMBERS_PER_WHEEL = 4096
    ZIP_UNCOMPRESSED_PER_WHEEL = 134_217_728
    RUNTIME_REGULAR_FILES = 4096
    RUNTIME_DIRECTORIES = 1024
    RUNTIME_AGGREGATE_BYTES = 536_870_912
    PATH_UTF8_BYTES = 4095
    PATH_COMPONENT_UTF8_BYTES = 255


def _expect_keys(value: Any, keys: frozenset[str], location: str) -> dict[str, Any]:
    if type(value) is not dict:
        _fail("SCHEMA_TYPE_INVALID", f"{location}: object required")
    actual = set(value)
    if actual != keys:
        missing = sorted(keys - actual)
        unknown = sorted(actual - keys)
        _fail("SCHEMA_KEYS_INVALID", f"{location}: missing={missing}, unknown={unknown}")
    return value


def _expect_string(value: Any, location: str, *, nonempty: bool = True) -> str:
    if type(value) is not str or (nonempty and not value):
        _fail("SCHEMA_STRING_INVALID", location)
    if unicodedata.normalize("NFC", value) != value or "\x00" in value:
        _fail("SCHEMA_STRING_INVALID", location)
    return value


def _expect_bool(value: Any, location: str) -> bool:
    if type(value) is not bool:
        _fail("SCHEMA_BOOLEAN_INVALID", location)
    return value


def _expect_int(value: Any, location: str, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        _fail("SCHEMA_INTEGER_INVALID", location)
    return value


def _expect_sha256(value: Any, location: str) -> str:
    value = _expect_string(value, location)
    if re.fullmatch(r"[0-9a-f]{64}", value) is None:
        _fail("SCHEMA_SHA256_INVALID", location)
    return value


def _expect_sha1(value: Any, location: str) -> str:
    value = _expect_string(value, location)
    if re.fullmatch(r"[0-9a-f]{40}", value) is None:
        _fail("SCHEMA_GIT_SHA_INVALID", location)
    return value


def _expect_fixed(value: Any, expected: Any, location: str) -> None:
    if value != expected or type(value) is not type(expected):
        _fail("FIXED_VALUE_MISMATCH", location)


def _derive_lock(formal: dict[str, Any]) -> dict[str, Any]:
    names = PreparationContractV1.EXACT5_NAMES
    rows = [
        copy.deepcopy(row)
        for row in formal.get("distributions", [])
        if type(row) is dict and row.get("normalized_distribution_name") in names
    ]
    rows.sort(key=lambda row: row["normalized_distribution_name"])
    if tuple(row.get("normalized_distribution_name") for row in rows) != names:
        _fail("LOCK_DERIVATION_INVALID", "formal exact5 row selection")
    candidate: dict[str, Any] = {
        "schema_version": formal["schema_version"],
        "identity_class": formal["identity_class"],
        "target": copy.deepcopy(formal["target"]),
        "root_imports": ["pytest"],
        "root_requirements": ["pytest==8.4.1"],
        "module_distribution_map": dict(PreparationContractV1.MODULE_DISTRIBUTION_MAP),
        "distribution_count": 5,
        "distributions": rows,
        "pip_require_hashes_lines": [
            f'{row["normalized_distribution_name"]}=={row["distribution_version"]} '
            f'--hash=sha256:{row["wheel_sha256"]}'
            for row in rows
        ],
        "resolution": {
            "activated_extras": {},
            "allow_sdist": False,
            "hashes_required": True,
            "index_access_during_install": False,
            "installation_mode": "no_index_no_compile_target",
            "installed_record_closure_rule": formal["resolution"][
                "installed_record_closure_rule"
            ],
            "marker_environment": copy.deepcopy(formal["resolution"]["marker_environment"]),
            "namespace_module_distribution_map": {},
            "only_binary": ":all:",
            "pip_version": "26.0.1",
            "reachable_distribution_count": 5,
            "resolver": "pip",
            "root_requirement_count": 1,
            "unresolved_dependency_count": 0,
        },
    }
    logical = canonical_json_bytes(candidate)
    candidate["lock_sha256"] = canonical_sha256(logical)
    return candidate


def _validate_derived_keysets(lock: dict[str, Any]) -> None:
    contract = PreparationContractV1
    _expect_keys(lock, contract.DERIVED_TOP_KEYS, "derived_lock")
    _expect_keys(lock["target"], contract.DERIVED_TARGET_KEYS, "derived_lock.target")
    _expect_keys(lock["resolution"], contract.DERIVED_RESOLUTION_KEYS, "derived_lock.resolution")
    if type(lock["distributions"]) is not list or len(lock["distributions"]) != 5:
        _fail("LOCK_SCHEMA_INVALID", "distribution exact5")
    for index, row in enumerate(lock["distributions"]):
        _expect_keys(row, contract.DERIVED_ROW_KEYS, f"derived_lock.distributions[{index}]")


def validate_lock_derivation(formal_lock_bytes: bytes, derived_lock_bytes: bytes) -> dict[str, Any]:
    """Validate formal-full46 to canonical-derived-exact5 byte-for-byte."""

    contract = PreparationContractV1
    if canonical_sha256(formal_lock_bytes) != contract.FORMAL_LOCK_RAW_SHA256:
        _fail("FORMAL_LOCK_RAW_IDENTITY_MISMATCH", "formal full46 raw SHA-256")
    formal = _parse_json(formal_lock_bytes, canonical=False, final_lf=True)
    derived = strict_json_from_bytes(derived_lock_bytes, require_final_lf=True)
    if len(derived_lock_bytes) != contract.DERIVED_LOCK_RAW_BYTES:
        _fail("DERIVED_LOCK_RAW_IDENTITY_MISMATCH", "raw byte count")
    if canonical_sha256(derived_lock_bytes) != contract.DERIVED_LOCK_RAW_SHA256:
        _fail("DERIVED_LOCK_RAW_IDENTITY_MISMATCH", "raw SHA-256")
    if canonical_sha256(derived_lock_bytes[:-1]) != contract.DERIVED_LOCK_BODY_SHA256:
        _fail("DERIVED_LOCK_RAW_IDENTITY_MISMATCH", "body SHA-256")
    _validate_derived_keysets(derived)
    expected = _derive_lock(formal)
    if derived != expected:
        _fail("LOCK_DERIVATION_INVALID", "derived semantic body mismatch")
    logical = copy.deepcopy(derived)
    logical.pop("lock_sha256")
    logical_bytes = canonical_json_bytes(logical)
    if len(logical_bytes) != contract.DERIVED_LOCK_LOGICAL_BYTES:
        _fail("LOCK_DERIVATION_INVALID", "logical byte count")
    if canonical_sha256(logical_bytes) != contract.DERIVED_LOCK_LOGICAL_SHA256:
        _fail("LOCK_DERIVATION_INVALID", "logical SHA-256")
    _expect_fixed(derived["lock_sha256"], contract.DERIVED_LOCK_LOGICAL_SHA256, "lock_sha256")
    return copy.deepcopy(derived)


def derive_requirements_bytes(validated_lock: dict[str, Any]) -> bytes:
    """Derive the exact private pip --require-hashes requirements bytes."""

    _validate_derived_keysets(validated_lock)
    lines = validated_lock["pip_require_hashes_lines"]
    if type(lines) is not list or len(lines) != 5 or any(type(line) is not str for line in lines):
        _fail("REQUIREMENTS_DERIVATION_INVALID", "line exact5")
    payload = ("\n".join(lines) + "\n").encode("utf-8")
    if len(payload) != PreparationContractV1.REQUIREMENTS_BYTES:
        _fail("REQUIREMENTS_DERIVATION_INVALID", "byte count")
    if canonical_sha256(payload) != PreparationContractV1.REQUIREMENTS_SHA256:
        _fail("REQUIREMENTS_DERIVATION_INVALID", "SHA-256")
    return payload


def validate_stable_authority_approval(record: dict[str, Any]) -> dict[str, Any]:
    """Validate the stable, human-approved exact15 authority record."""

    c = PreparationContractV1
    record = _expect_keys(record, c.STABLE_AUTHORITY_APPROVAL_KEYS, "stable_approval")
    fixed = {
        "schema_version": c.STABLE_AUTHORITY_APPROVAL_SCHEMA,
        "candidate_id": c.CANDIDATE_ID,
        "approved_candidate_body_sha256": c.APPROVED_CANDIDATE_BODY_SHA256,
        "authority_policy_id": c.AUTHORITY_POLICY_ID,
        "acquisition_policy_id": c.ACQUISITION_POLICY_ID,
        "egress_issuer_class": c.EGRESS_ISSUER_CLASS,
        "egress_issuer_policy_id": c.EGRESS_ISSUER_POLICY_ID,
        "allowed_scheme": c.ALLOWED_SCHEME,
        "allowed_hosts": list(c.ALLOWED_HOSTS),
        "acquisition_process_count": 1,
        "attestation_issue_phase": c.ATTESTATION_ISSUE_PHASE,
        "attestation_max_lifetime_seconds": 900,
        "minimum_remaining_lifetime_at_p3_seconds": 330,
        "same_authority_reissue_allowed": False,
    }
    for key, expected in fixed.items():
        _expect_fixed(record[key], expected, f"stable_approval.{key}")
    _expect_string(record["authority_id"], "stable_approval.authority_id")
    canonical_json_bytes(record)
    return copy.deepcopy(record)


def _validate_rfc3339(value: Any, location: str) -> _datetime.datetime:
    value = _expect_string(value, location)
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value) is None:
        _fail("TIME_FORMAT_INVALID", location)
    try:
        return _datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=_datetime.timezone.utc
        )
    except ValueError:
        _fail("TIME_FORMAT_INVALID", location)


def _validate_relative_public_path(value: Any, location: str, *, may_be_empty: bool) -> None:
    value = _expect_string(value, location, nonempty=not may_be_empty)
    if not value and may_be_empty:
        return
    if value.startswith("/") or "\\" in value or value != posixpath.normpath(value):
        _fail("PUBLICATION_PATH_INVALID", location)
    if value == ".." or value.startswith("../"):
        _fail("PUBLICATION_PATH_INVALID", location)


def validate_path_plan(path_plan: dict[str, Any]) -> dict[str, Any]:
    """Validate PATH_ROLE_EXACT20, distinct19, and fixed locator topology."""

    c = PreparationContractV1
    expected_keys = frozenset(c.PATH_ROLE_NAMES)
    path_plan = _expect_keys(path_plan, expected_keys, "path_plan")
    for role in c.PATH_ROLE_NAMES:
        locator = _expect_string(path_plan[role], f"path_plan.{role}")
        if not locator.startswith("/") or "\\" in locator or "//" in locator:
            _fail("PATH_LOCATOR_INVALID", role)
        if locator == "/" or locator.endswith("/") or posixpath.normpath(locator) != locator:
            _fail("PATH_LOCATOR_INVALID", role)
        encoded = locator.encode("utf-8")
        if len(encoded) > c.PATH_UTF8_BYTES:
            _fail("PATH_BUDGET_OR_SCOPE_EXCEEDED", role)
        for component in locator.split("/")[1:]:
            if len(component.encode("utf-8")) > c.PATH_COMPONENT_UTF8_BYTES:
                _fail("PATH_BUDGET_OR_SCOPE_EXCEEDED", role)
    if path_plan["controller_test_cwd"] != path_plan["checker_test_cwd"]:
        _fail("PATH_ALIAS_INVALID", "controller_test_cwd != checker_test_cwd")
    if len(set(path_plan.values())) != 19:
        _fail("PATH_CARDINALITY_INVALID", "distinct locator exact19")
    authority_root = path_plan["authority_root"]
    repository_root = path_plan["controller_test_cwd"]
    if repository_root == authority_root or repository_root.startswith(authority_root + "/"):
        _fail("PATH_SCOPE_INVALID", "repository root below authority root")
    if authority_root.startswith(repository_root + "/"):
        _fail("PATH_SCOPE_INVALID", "authority root below repository root")
    for role, leaf in c.PATH_ROLE_LEAVES:
        expected = authority_root + "/" + leaf
        if path_plan[role] != expected:
            _fail("PATH_ROLE_LOCATOR_MISMATCH", role)
    return copy.deepcopy(path_plan)


def _validate_egress_attestation(attestation: dict[str, Any]) -> None:
    c = PreparationContractV1
    _expect_keys(attestation, c.EGRESS_ATTESTATION_KEYS, "egress_attestation")
    fixed = {
        "schema_version": c.EGRESS_ATTESTATION_SCHEMA,
        "source_class": c.EGRESS_ISSUER_CLASS,
        "issuer_policy_id": c.EGRESS_ISSUER_POLICY_ID,
        "approved_candidate_body_sha256": c.APPROVED_CANDIDATE_BODY_SHA256,
        "policy_id": c.ACQUISITION_POLICY_ID,
        "allowed_scheme": c.ALLOWED_SCHEME,
        "allowed_hosts": list(c.ALLOWED_HOSTS),
        "enforcement_scope": "CURRENT_G4B_ONE_SHOT_ACQUISITION_EXACT1",
        "acquisition_process_count": 1,
        "active": True,
    }
    for key, expected in fixed.items():
        _expect_fixed(attestation[key], expected, f"egress_attestation.{key}")
    for key in (
        "platform_control_state_instance_id", "authority_id", "observation_session_id"
    ):
        _expect_string(attestation[key], f"egress_attestation.{key}")
    for key in (
        "issuer_provenance_binding_sha256", "stable_authority_approval_binding_sha256"
    ):
        _expect_sha256(attestation[key], f"egress_attestation.{key}")
    provenance = {key: attestation[key] for key in c.ISSUER_PROVENANCE_KEYS}
    if canonical_sha256(provenance) != attestation["issuer_provenance_binding_sha256"]:
        _fail("ISSUER_PROVENANCE_BINDING_INVALID", "canonical exact8")
    issued = _validate_rfc3339(attestation["issued_at"], "egress_attestation.issued_at")
    expires = _validate_rfc3339(attestation["expires_at"], "egress_attestation.expires_at")
    lifetime = int((expires - issued).total_seconds())
    if not 1 <= lifetime <= c.ATTESTATION_MAX_LIFETIME_SECONDS:
        _fail("ATTESTATION_LIFETIME_INVALID", str(lifetime))


def validate_execution_request(request: dict[str, Any]) -> dict[str, Any]:
    """Validate the canonical private exact16 execution request without effects."""

    c = PreparationContractV1
    request = _expect_keys(request, c.EXECUTION_REQUEST_KEYS, "execution_request")
    fixed = {
        "schema_version": c.EXECUTION_REQUEST_SCHEMA,
        "candidate_id": c.CANDIDATE_ID,
        "approved_candidate_body_sha256": c.APPROVED_CANDIDATE_BODY_SHA256,
    }
    for key, expected in fixed.items():
        _expect_fixed(request[key], expected, f"execution_request.{key}")
    _expect_sha256(
        request["stable_authority_approval_binding_sha256"],
        "execution_request.stable_authority_approval_binding_sha256",
    )
    for key in ("authority_id", "observation_session_id", "receiver_session_id", "receiver_nonce"):
        _expect_string(request[key], f"execution_request.{key}")
    # The unchanged checker V1 contract binds its handoff receiver to the
    # currently observed session.  Reject a divergent value before any effect
    # instead of deferring the mismatch to the admission bridge.
    if request["receiver_session_id"] != request["observation_session_id"]:
        _fail("SESSION_BINDING_INVALID", "receiver session is not the observed session")

    expected_git = _expect_keys(request["expected_git"], c.EXPECTED_GIT_KEYS, "expected_git")
    for key, value in expected_git.items():
        _expect_sha1(value, f"expected_git.{key}")

    runtime = _expect_keys(request["control_runtime"], c.CONTROL_RUNTIME_KEYS, "control_runtime")
    runtime_fixed = {
        "implementation": c.EXPECTED_IMPLEMENTATION,
        "python_version": c.EXPECTED_PYTHON_VERSION,
        "platform_tag": c.EXPECTED_PLATFORM_TAG,
        "resolved_interpreter_sha256": c.EXPECTED_INTERPRETER_SHA256,
        "pip_version": c.EXPECTED_PIP_VERSION,
        "pip_main_parser_sha256": c.PIP_MAIN_PARSER_SHA256,
        "pip_build_env_sha256": c.PIP_BUILD_ENV_SHA256,
        "pip_runner_sha256": c.PIP_RUNNER_SHA256,
        "p5_static_launch_edge_proof_state": c.P5_STATIC_PROOF_STATE,
    }
    for key, expected in runtime_fixed.items():
        _expect_fixed(runtime[key], expected, f"control_runtime.{key}")
    _expect_string(runtime["executable"], "control_runtime.executable")
    _expect_sha256(
        runtime["pip_installed_source_manifest_sha256"],
        "control_runtime.pip_installed_source_manifest_sha256",
    )
    validate_path_plan(request["path_plan"])

    transport = _expect_keys(
        request["private_transport"], c.PRIVATE_TRANSPORT_KEYS, "private_transport"
    )
    _expect_fixed(transport["schema_version"], c.PRIVATE_TRANSPORT_SCHEMA, "private_transport.schema")
    proxy = _expect_string(transport["https_proxy"], "private_transport.https_proxy")
    if not proxy.startswith("https://") or "@" in proxy:
        _fail("PRIVATE_TRANSPORT_BINDING_INVALID", "proxy scheme or userinfo")
    _expect_string(transport["custom_ca_locator"], "private_transport.custom_ca_locator")
    _expect_string(transport["expected_proxy_class"], "private_transport.expected_proxy_class")
    _expect_sha256(transport["expected_ca_raw_sha256"], "private_transport.expected_ca_raw_sha256")
    _expect_sha256(
        transport["expected_stable_projection_sha256"],
        "private_transport.expected_stable_projection_sha256",
    )

    source = _expect_keys(
        request["egress_attestation_source"],
        c.EGRESS_ATTESTATION_SOURCE_KEYS,
        "egress_attestation_source",
    )
    _expect_fixed(
        source["schema_version"], c.EGRESS_ATTESTATION_SOURCE_SCHEMA,
        "egress_attestation_source.schema_version",
    )
    _expect_string(source["private_locator"], "egress_attestation_source.private_locator")
    if source["expected_owner_class"] not in (
        "PLATFORM_ROOT", "APPROVED_DISTINCT_NON_AUTHORITY_OWNER"
    ):
        _fail("EGRESS_ATTESTATION_SOURCE_INVALID", "owner class")
    _expect_fixed(source["expected_mode"], "0400", "egress_attestation_source.expected_mode")
    _expect_fixed(source["expected_regular_file"], True, "egress_attestation_source.regular")
    _expect_fixed(source["expected_nlink"], 1, "egress_attestation_source.nlink")
    _expect_sha256(source["expected_raw_sha256"], "egress_attestation_source.raw_sha256")
    _validate_rfc3339(source["expected_expiry"], "egress_attestation_source.expected_expiry")

    attestation = request["egress_attestation"]
    _validate_egress_attestation(attestation)
    if attestation["authority_id"] != request["authority_id"]:
        _fail("AUTHORITY_BINDING_INVALID", "egress authority")
    if attestation["observation_session_id"] != request["observation_session_id"]:
        _fail("SESSION_BINDING_INVALID", "egress observation session")
    if (
        attestation["stable_authority_approval_binding_sha256"]
        != request["stable_authority_approval_binding_sha256"]
    ):
        _fail("AUTHORITY_BINDING_INVALID", "stable approval")
    attestation_sha = canonical_sha256(attestation)
    _expect_fixed(request["egress_attestation_sha256"], attestation_sha, "egress_attestation_sha256")
    _expect_fixed(source["expected_raw_sha256"], attestation_sha, "egress source raw SHA")
    _expect_fixed(source["expected_expiry"], attestation["expires_at"], "egress source expiry")

    publication = _expect_keys(
        request["publication_contract"], c.PUBLICATION_CONTRACT_KEYS, "publication_contract"
    )
    _expect_fixed(
        publication["schema_version"], c.PUBLICATION_CONTRACT_SCHEMA,
        "publication_contract.schema_version",
    )
    _expect_sha1(publication["cocolon_pre_head"], "publication_contract.cocolon_pre_head")
    _validate_relative_public_path(publication["receipt_path"], "publication_contract.receipt_path", may_be_empty=False)
    _validate_relative_public_path(publication["current_state_path"], "publication_contract.current_state_path", may_be_empty=False)
    _validate_relative_public_path(
        publication["conditional_closure_route_path"],
        "publication_contract.conditional_closure_route_path", may_be_empty=True,
    )
    _validate_relative_public_path(
        publication["conditional_milestone_path"],
        "publication_contract.conditional_milestone_path", may_be_empty=True,
    )
    _expect_sha256(
        publication["approved_public_path_set_sha256"],
        "publication_contract.approved_public_path_set_sha256",
    )
    _expect_fixed(
        publication["result_unknown_policy"], c.RESULT_UNKNOWN_POLICY,
        "publication_contract.result_unknown_policy",
    )
    canonical_json_bytes(request)
    return copy.deepcopy(request)


def _validate_acquisition_observation(
    request: dict[str, Any], observation: dict[str, Any]
) -> dict[str, Any]:
    """Strictly bind the private exact18 acquisition output to its request."""

    c = PreparationContractV1
    observation = _expect_keys(
        observation, c.ACQUISITION_OBSERVATION_KEYS, "acquisition_observation"
    )
    fixed = {
        "schema_version": c.ACQUISITION_OBSERVATION_SCHEMA,
        "authority_id": request["authority_id"],
        "observation_session_id": request["observation_session_id"],
        "consumed": True,
        "process_launch_count": 1,
        "egress_attestation_sha256": request["egress_attestation_sha256"],
        "returncode": 0,
        "requirements_sha256": c.REQUIREMENTS_SHA256,
        "accepted_wheel_manifest_sha256": c.ACCEPTED_WHEEL_MANIFEST_SHA256,
    }
    for key, expected in fixed.items():
        _expect_fixed(observation[key], expected, f"acquisition_observation.{key}")
    for key in (
        "argv_sha256", "environment_sha256",
        "egress_attestation_source_observation_sha256", "transport_b0_sha256",
        "transport_b1_sha256", "transport_b2_sha256", "stdout_sha256",
        "stderr_sha256",
    ):
        _expect_sha256(observation[key], f"acquisition_observation.{key}")
    if len(
        {
            observation["transport_b0_sha256"],
            observation["transport_b1_sha256"],
            observation["transport_b2_sha256"],
        }
    ) != 1:
        _fail("PRIVATE_TRANSPORT_DRIFT", "acquisition observation B0/B1/B2 mismatch")
    rows = observation["accepted_wheel_rows"]
    if type(rows) is not list or len(rows) != 5:
        _fail("ACQUIRED_WHEEL_SET_INVALID", "accepted wheel row exact5")
    for index, row in enumerate(rows):
        row = _expect_keys(
            row, c.ACCEPTED_WHEEL_ROW_KEYS,
            f"acquisition_observation.accepted_wheel_rows[{index}]",
        )
        _expect_string(
            row["wheel_filename"],
            f"accepted_wheel_rows[{index}].wheel_filename",
        )
        _expect_sha256(
            row["wheel_sha256"],
            f"accepted_wheel_rows[{index}].wheel_sha256",
        )
    if canonical_sha256(rows) != c.ACCEPTED_WHEEL_MANIFEST_SHA256:
        _fail("ACQUIRED_WHEEL_SET_INVALID", "accepted wheel manifest semantic mismatch")
    canonical_json_bytes(observation)
    return copy.deepcopy(observation)


def _validate_materialization_attestation(
    request: dict[str, Any], attestation: dict[str, Any]
) -> dict[str, Any]:
    """Strictly bind the private exact22 materialization output to its request."""

    c = PreparationContractV1
    attestation = _expect_keys(
        attestation, c.MATERIALIZATION_ATTESTATION_KEYS, "materialization_attestation"
    )
    paths = request["path_plan"]
    runtime_root = paths["runtime_root"]
    executable = posixpath.join(runtime_root, "bin/python")
    root_locator_sha256 = canonical_sha256(
        {
            "schema_version": "emlis.nls_v3.s11.g4b.runtime_root_locator.v1",
            "runtime_root": runtime_root,
        }
    )
    executable_locator_sha256 = canonical_sha256(
        {
            "schema_version": "emlis.nls_v3.s11.g4b.runtime_executable_locator.v1",
            "runtime_executable": executable,
        }
    )
    fixed = {
        "schema_version": c.MATERIALIZATION_ATTESTATION_SCHEMA,
        "authority_id": request["authority_id"],
        "observation_session_id": request["observation_session_id"],
        "procedure_ids": list(c.PROCEDURE_IDS),
        "fresh_root_nonexistent_before": True,
        "prior_artifact_reuse_count": 0,
        "runtime_root_locator_sha256": root_locator_sha256,
        "site_packages_relative": c.SITE_PACKAGES_RELATIVE,
        "derived_lock_raw_sha256": c.DERIVED_LOCK_RAW_SHA256,
        "derived_lock_logical_sha256": c.DERIVED_LOCK_LOGICAL_SHA256,
        "accepted_wheel_manifest_sha256": c.ACCEPTED_WHEEL_MANIFEST_SHA256,
        "wheel_record_manifest_sha256": c.WHEEL_RECORD_MANIFEST_SHA256,
        "distribution_closure_sha256": c.DISTRIBUTION_CLOSURE_SHA256,
        "runtime_executable_locator_sha256": executable_locator_sha256,
        "resolved_interpreter_sha256": c.EXPECTED_INTERPRETER_SHA256,
        "environment_policy_sha256": c.ENVIRONMENT_POLICY_SHA256,
        "status": "MATERIALIZED_VERIFIED",
    }
    for key, expected in fixed.items():
        _expect_fixed(attestation[key], expected, f"materialization_attestation.{key}")
    for key in (
        "event_id", "installed_file_manifest_sha256",
        "full_runtime_root_manifest_sha256", "materialization_process_ledger_sha256",
    ):
        _expect_sha256(attestation[key], f"materialization_attestation.{key}")
    wheel_rows = attestation["wheel_record_rows"]
    if type(wheel_rows) is not list or len(wheel_rows) != 5:
        _fail("MATERIALIZATION_IDENTITY_INVALID", "wheel RECORD row exact5")
    for index, row in enumerate(wheel_rows):
        row = _expect_keys(
            row, c.WHEEL_RECORD_ROW_KEYS,
            f"materialization_attestation.wheel_record_rows[{index}]",
        )
        _expect_string(
            row["wheel_filename"], f"wheel_record_rows[{index}].wheel_filename"
        )
        _expect_sha256(
            row["wheel_sha256"], f"wheel_record_rows[{index}].wheel_sha256"
        )
        _expect_sha256(
            row["wheel_record_sha256"],
            f"wheel_record_rows[{index}].wheel_record_sha256",
        )
    if canonical_sha256(wheel_rows) != c.WHEEL_RECORD_MANIFEST_SHA256:
        _fail("MATERIALIZATION_IDENTITY_INVALID", "wheel RECORD manifest semantic mismatch")
    event_preimage = {
        "schema_version": c.MATERIALIZATION_EVENT_SCHEMA,
        "authority_id": request["authority_id"],
        "observation_session_id": request["observation_session_id"],
        "procedure_ids": list(c.PROCEDURE_IDS),
        "fresh_root_nonexistent_before": True,
        "prior_artifact_reuse_count": 0,
        "root_locator_sha256": root_locator_sha256,
        "expected_full_root_manifest_sha256": attestation[
            "full_runtime_root_manifest_sha256"
        ],
        "site_packages_relative": c.SITE_PACKAGES_RELATIVE,
        "admitted_executable_relative_path": "bin/python",
    }
    _expect_fixed(
        attestation["event_id"], canonical_sha256(event_preimage),
        "materialization_attestation.event_id",
    )
    canonical_json_bytes(attestation)
    return copy.deepcopy(attestation)


def validate_public_result(result: dict[str, Any]) -> dict[str, Any]:
    """Validate the immutable body-free exact31 controller result."""

    c = PreparationContractV1
    result = _expect_keys(result, c.PUBLIC_RESULT_KEYS, "public_result")
    _expect_fixed(result["schema_version"], c.PUBLIC_RESULT_SCHEMA, "public_result.schema")
    _expect_fixed(result["method_id"], c.METHOD_ID, "public_result.method_id")
    _expect_fixed(result["candidate_id"], c.CANDIDATE_ID, "public_result.candidate_id")
    _expect_sha256(result["authority_context_binding_sha256"], "authority context")
    _expect_sha256(result["session_context_binding_sha256"], "session context")
    for key in (
        "activated", "consumed", "gate_c_authorized", "technical_chain_complete",
        "durable_work_complete", "durable_current_owner_runtime_ready",
        "durable_current_owner_gate_b_closed", "automatic_progression",
    ):
        _expect_bool(result[key], f"public_result.{key}")
    for key in (
        "checker_execution_attempt_count", "durable_current_owner_readiness_credit",
        "durable_current_owner_technical_credit", "durable_current_owner_product_credit",
    ):
        _expect_int(result[key], f"public_result.{key}")
    if result["checker_execution_attempt_count"] not in (0, 1):
        _fail("PUBLIC_RESULT_INVALID", "checker attempt count")
    for key in (
        "status", "primary_terminal", "nested_checker_terminal", "technical_primary_outcome",
        "checker_component_status", "composite_technical_result",
        "current_session_runtime_readiness", "gate_b_technical_condition", "handoff_state",
        "cleanup_state", "retention_state", "publication_state",
        "durable_current_owner_state", "durable_current_owner_primary_outcome",
    ):
        _expect_string(result[key], f"public_result.{key}")
    if result["status"] not in ("VALID", "STOP"):
        _fail("PUBLIC_RESULT_INVALID", "status")
    if result["checker_component_status"] not in ("NOT_RUN", "VALID", "STOP"):
        _fail("PUBLIC_RESULT_INVALID", "checker component status")
    if result["cleanup_state"] not in ("COMPLETE", "FAILED", "UNKNOWN"):
        _fail("PUBLIC_RESULT_INVALID", "cleanup state")
    if result["retention_state"] not in (
        "NONE", "EVIDENCE_RETAINED", "CURRENT_SESSION_RETAINED",
        "PARTIAL_PRIVATE_STATE_RETAINED",
    ):
        _fail("PUBLIC_RESULT_INVALID", "retention state")
    fixed_durable = {
        "gate_c_authorized": False,
        "publication_state": "NOT_ATTEMPTED",
        "durable_work_complete": False,
        "durable_current_owner_runtime_ready": False,
        "durable_current_owner_gate_b_closed": False,
        "durable_current_owner_readiness_credit": 0,
        "durable_current_owner_technical_credit": 0,
        "durable_current_owner_product_credit": 0,
        "automatic_progression": False,
    }
    for key, expected in fixed_durable.items():
        _expect_fixed(result[key], expected, f"public_result.{key}")
    if result["status"] == "VALID":
        success = {
            "primary_terminal": c.PRIMARY_SUCCESS_TERMINAL,
            "technical_primary_outcome": "TECHNICAL_CREDIT",
            "checker_component_status": "VALID",
            "composite_technical_result": "VALID",
            "current_session_runtime_readiness": "READY_CURRENT_SESSION",
            "gate_b_technical_condition": "SATISFIED_CURRENT_SESSION",
            "handoff_state": "HANDOFF_BOUND_CURRENT_SESSION",
            "cleanup_state": "COMPLETE",
            "retention_state": "CURRENT_SESSION_RETAINED",
            "technical_chain_complete": True,
            "durable_current_owner_state": "UNCHANGED_PENDING_PUBLICATION",
            "durable_current_owner_primary_outcome": "BLOCKER_NARROWED",
        }
        for key, expected in success.items():
            _expect_fixed(result[key], expected, f"public_result.{key}")
        _expect_fixed(result["activated"], True, "public_result.activated")
        _expect_fixed(result["checker_execution_attempt_count"], 1, "checker attempt")
    else:
        if result["primary_terminal"] not in c.PRIMARY_STOP_TERMINALS:
            _fail("PUBLIC_RESULT_INVALID", "primary STOP terminal")
        if result["technical_primary_outcome"] not in (
            "NO_TECHNICAL_CREDIT", "BLOCKER_NARROWED", "STOPPED"
        ):
            _fail("PUBLIC_RESULT_INVALID", "technical primary outcome")
        if result["composite_technical_result"] not in ("STOP", "STOP_CLEANUP_INCOMPLETE"):
            _fail("PUBLIC_RESULT_INVALID", "composite STOP")
        _expect_fixed(result["current_session_runtime_readiness"], "NOT_READY", "readiness")
        _expect_fixed(result["gate_b_technical_condition"], "NOT_SATISFIED", "Gate B")
        _expect_fixed(result["technical_chain_complete"], False, "technical chain")
        _expect_fixed(result["durable_current_owner_state"], "UNCHANGED", "current owner")
        if result["durable_current_owner_primary_outcome"] not in (
            "BLOCKER_NARROWED", "NO_TECHNICAL_CREDIT", "UNCHANGED"
        ):
            _fail("PUBLIC_RESULT_INVALID", "durable primary outcome")
    canonical_json_bytes(result)
    return copy.deepcopy(result)


def validate_durable_publication_transition(evidence: dict[str, Any]) -> dict[str, Any]:
    """Validate separate, post-controller durable transition exact17 evidence."""

    c = PreparationContractV1
    evidence = _expect_keys(evidence, c.DURABLE_TRANSITION_KEYS, "durable_transition")
    _expect_fixed(evidence["schema_version"], c.DURABLE_TRANSITION_SCHEMA, "transition.schema")
    _expect_fixed(evidence["candidate_id"], c.CANDIDATE_ID, "transition.candidate_id")
    for key in (
        "authority_context_binding_sha256", "session_context_binding_sha256",
        "controller_public_result_sha256", "terminal_evidence_envelope_sha256",
    ):
        _expect_sha256(evidence[key], f"durable_transition.{key}")
    for key in (
        "durable_work_complete", "current_owner_runtime_ready",
        "current_owner_gate_b_closed", "automatic_progression",
    ):
        _expect_bool(evidence[key], f"durable_transition.{key}")
    for key in (
        "current_owner_readiness_credit", "current_owner_technical_credit",
        "current_owner_product_credit",
    ):
        _expect_int(evidence[key], f"durable_transition.{key}")
    for key in (
        "publication_state", "remote_postverify_state", "current_owner_primary_outcome",
        "publication_staging_cleanup_state",
    ):
        _expect_string(evidence[key], f"durable_transition.{key}")
    _expect_fixed(evidence["automatic_progression"], False, "transition.automatic_progression")
    if evidence["durable_work_complete"]:
        fixed = {
            "publication_state": "VERIFIED",
            "remote_postverify_state": "EXACT_MATCH",
            "current_owner_runtime_ready": True,
            "current_owner_gate_b_closed": True,
            "current_owner_readiness_credit": 1,
            "current_owner_technical_credit": 1,
            "current_owner_product_credit": 0,
            "current_owner_primary_outcome": "TECHNICAL_CREDIT",
            "publication_staging_cleanup_state": "ABSENT_VERIFIED",
        }
    else:
        fixed = {
            "current_owner_runtime_ready": False,
            "current_owner_gate_b_closed": False,
            "current_owner_readiness_credit": 0,
            "current_owner_technical_credit": 0,
            "current_owner_product_credit": 0,
        }
        if evidence["publication_state"] == "VERIFIED":
            _fail("DURABLE_TRANSITION_INVALID", "VERIFIED without durable completion")
    for key, expected in fixed.items():
        _expect_fixed(evidence[key], expected, f"durable_transition.{key}")
    canonical_json_bytes(evidence)
    return copy.deepcopy(evidence)


# Module-level immutable aliases make source-only conformance checks direct while
# leaving the approved callable public API exactly thirteen names.
ACQUISITION_POLICY_ID = PreparationContractV1.ACQUISITION_POLICY_ID
ALLOWED_HOSTS = PreparationContractV1.ALLOWED_HOSTS
PRIMARY_INDEX_URL = PreparationContractV1.PRIMARY_INDEX_URL
REQUIREMENTS_SHA256 = PreparationContractV1.REQUIREMENTS_SHA256
ACCEPTED_WHEEL_MANIFEST_SHA256 = PreparationContractV1.ACCEPTED_WHEEL_MANIFEST_SHA256
DERIVED_LOCK_RAW_SHA256 = PreparationContractV1.DERIVED_LOCK_RAW_SHA256
DERIVED_LOCK_LOGICAL_SHA256 = PreparationContractV1.DERIVED_LOCK_LOGICAL_SHA256
DERIVED_LOCK_GIT_BLOB = PreparationContractV1.DERIVED_LOCK_GIT_BLOB
DISTRIBUTION_CLOSURE_SHA256 = PreparationContractV1.DISTRIBUTION_CLOSURE_SHA256
WHEEL_RECORD_MANIFEST_SHA256 = PreparationContractV1.WHEEL_RECORD_MANIFEST_SHA256
EXPECTED_INTERPRETER_SHA256 = PreparationContractV1.EXPECTED_INTERPRETER_SHA256
PROCEDURE_IDS = PreparationContractV1.PROCEDURE_IDS
SITE_PACKAGES_RELATIVE = PreparationContractV1.SITE_PACKAGES_RELATIVE
ACQUISITION_OBSERVATION_SCHEMA = PreparationContractV1.ACQUISITION_OBSERVATION_SCHEMA
MATERIALIZATION_ATTESTATION_SCHEMA = PreparationContractV1.MATERIALIZATION_ATTESTATION_SCHEMA
TRANSPORT_BINDING_SCHEMA = PreparationContractV1.TRANSPORT_BINDING_SCHEMA
ENVIRONMENT_POLICY_SHA256 = PreparationContractV1.ENVIRONMENT_POLICY_SHA256
