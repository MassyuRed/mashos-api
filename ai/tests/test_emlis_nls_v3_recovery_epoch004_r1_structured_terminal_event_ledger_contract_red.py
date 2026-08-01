from __future__ import annotations

"""Contract-only RED for the R1 structured terminal-event owner.

This single test freezes a synthetic, body-free semantic-ledger/final-capture
pair and the complete negative matrix.  It neither imports nor executes D1,
generates a challenge, starts a subprocess, reads a remote, nor writes an
artifact.  The deterministic RED is emitted from the test call phase while
the separately-authorized production owner remains absent.
"""

import copy
import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
import sys
import tempfile
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest


_RED_SIGNATURE = "R1_STRUCTURED_TERMINAL_EVENT_OWNER_IMPLEMENTATION_ABSENT_RED"
_OWNER_PATH = (
    "ai/tools/"
    "emlis_nls_v3_recovery_epoch004_r1_structured_terminal_event_ledger.py"
)
_OWNER_MODULE_NAME = (
    "emlis_nls_v3_recovery_epoch004_r1_structured_terminal_event_ledger"
)
_D1_PATH = (
    "ai/tests/"
    "test_emlis_nls_v3_recovery_epoch004_operational_admission_v2_"
    "event1_connection_actual_git_identity_parent_phase3_red.py"
)
_D1_BLOB_SHA1 = "c0eb936690a3423ac4615a9aabb37c40cc257324"
_D1_RAW_SHA256 = (
    "3536b8a838ffe2ccbe29db69e9c5400c719de8e63ddf83da9ea0f83b94f17d14"
)

_LEDGER_SCHEMA = (
    "cocolon.emlis.nls_v3.step11.cycle001.recovery_epoch004."
    "d1_v5.r1_structured_pytest_semantic_ledger.v1"
)
_ENVELOPE_SCHEMA = (
    "cocolon.emlis.nls_v3.step11.cycle001.recovery_epoch004."
    "d1_v5.r1_outer_terminal_capture_envelope.v1"
)
_PROJECTION_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch004."
    "actual_git_observation_body_free_projection.v1"
)
_LEDGER_STATE = (
    "STRUCTURED_PYTEST_SEMANTIC_LEDGER_COMPLETE_PENDING_"
    "OUTER_TERMINAL_ENVELOPE"
)
_ENVELOPE_STATE = "POSTPROCESS_FINAL_CAPTURE_ENVELOPE_COMPLETE"
_LEDGER_HASH_RULE = (
    "SHA256_OF_UTF8_COMPACT_SORTED_KEY_JSON_AFTER_DELETING_"
    "LEDGER_SHA256_WITH_NO_TRAILING_LF"
)
_ENVELOPE_HASH_RULE = (
    "SHA256_OF_UTF8_COMPACT_SORTED_KEY_JSON_AFTER_DELETING_"
    "TERMINAL_ENVELOPE_SHA256_WITH_NO_TRAILING_LF"
)
_EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()

_TEST_PATH = _D1_PATH
_NODE_NAMES = (
    "test_o01_event1_v2_owner_schema_dispatch_public_signature_and_"
    "invalid_envelope",
    "test_o02_event1_v2_independent_schema_dispatch_reexecutes_"
    "without_owner_trust",
    "test_o03_source_subject_owner_independent_same_actual_git_root_"
    "head_tree_module_blob_raw",
    "test_o04_unknown_mixed_and_v2_to_v1_fallback_rejected_fail_closed",
    "test_o05_event1_exact23_nests_distinct_candidate_and_consumes_"
    "oa_v2_exactly_once",
    "test_o06_parent_phase3_reconstructs_actual_postfetch_and_calls_"
    "independent_once",
    "test_o07_missing_mixed_stale_identity_evidence_fail_closed_with_"
    "zero_effects",
    "test_o08_v1_exact16_exact8_and_predecessor_oracles_remain_immutable",
)
_ORDERED_NODE_IDS = tuple(f"{_TEST_PATH}::{name}" for name in _NODE_NAMES)
_ORDERED_NODE_LIST_SHA256 = (
    "e2661d946c060efc44ce7da06f8c55f51d10dfad2af4f5f0526bd38109c340bc"
)
_RAW_PROJECTION_VECTOR_SHA256 = (
    "3e3dd315bc0fee6769845344c3eab8684bb9d95a4a5801069d9c57b161e894a3"
)
_NORMALIZED_EXPECTED_VECTOR_SHA256 = (
    "da9d266a254a12a655d4dd9388ccd3e866a57455ff98254e119571f8b824055b"
)

_SIGNATURES = (
    "O01_OWNER_ADDITIONAL_LIVE_REMOTE_QUERY",
    "O02_INDEPENDENT_ADDITIONAL_LIVE_REMOTE_QUERY",
    "O03_SOURCE_AND_ROLES_NOT_ONE_OBSERVATION_CUT",
    "O04_VALID_DISPATCH_ADDITIONAL_LIVE_REMOTE_QUERY",
    "O05_EXACT23_CANDIDATE_OA_PATHS_REACQUIRE",
    "O06_PARENT_POSTFETCH_AND_INDEPENDENT_REACQUIRE",
    "O07_HARNESS_POSITIVE_PATH_EXCEEDS_EXACT1",
    None,
)
_VIOLATIONS = (
    "LIVE_REMOTE_REQUERY_OUTSIDE_ACQUIRER",
    "LIVE_REMOTE_REQUERY_OUTSIDE_ACQUIRER",
    "OBSERVATION_MISSING_OR_MIXED",
    "LIVE_REMOTE_REQUERY_OUTSIDE_ACQUIRER",
    "LIVE_REMOTE_REQUERY_OUTSIDE_ACQUIRER",
    "LIVE_REMOTE_REQUERY_OUTSIDE_ACQUIRER",
    "ACQUISITION_CARDINALITY_INVALID",
    None,
)
_GLOBAL_VIOLATIONS = (
    "ACQUISITION_CARDINALITY_INVALID",
    "OBSERVATION_MISSING_OR_MIXED",
    "LIVE_REMOTE_REQUERY_OUTSIDE_ACQUIRER",
)
_EQUALITY_KEYS = (
    "repository_identity_consistent",
    "source_cut_consistent",
    "owner_executor_consistent",
    "independent_executor_consistent",
    "parent_phase3_source_consistent",
    "live_remote_match",
    "closure_consistent",
    "body_free",
)

_LEDGER_KEYS = frozenset(
    {
        "admission_sha256",
        "authority_token_sha256",
        "body_free",
        "collection",
        "consumption_sha256",
        "d1_projection",
        "fixed_source_identity_sha256",
        "ledger_sha256",
        "ledger_sha256_preimage_rule",
        "launcher_contract_sha256",
        "pytest_reports",
        "run_challenge_id",
        "runtime_identity_sha256",
        "schema_version",
        "session",
        "single_use_key_sha256",
        "state",
    }
)
_COLLECTION_KEYS = frozenset(
    {
        "collected_count",
        "ordered_node_ids",
        "ordered_node_list_sha256",
        "source_d1_blob_sha1",
    }
)
_PROJECTION_KEYS = frozenset(
    {
        "schema_version",
        "source_preflight_sha256",
        "source_observation_sha256",
        "source_closure_sha256",
        "run_challenge_id",
        "run_scope",
        "repository_full_name",
        "remote_ref",
        "acquisition_profile_id",
        "preflight_class",
        "acquisition_class",
        "run_terminal_class",
        "violation_classes",
        "oracle_outcomes",
        "equality_verdicts",
        "projection_sha256",
    }
)
_REPORT_KEYS = frozenset(
    {
        "causal_signature_id",
        "node_id",
        "outcome",
        "phase",
        "report_index",
        "violation_class",
    }
)
_SESSION_KEYS = frozenset(
    {
        "collected_count",
        "error_count",
        "executed_count",
        "exit_code",
        "failed_count",
        "passed_count",
        "report_count",
        "session_finish_count",
    }
)
_ENVELOPE_KEYS = frozenset(
    {
        "admission_sha256",
        "authority_token_sha256",
        "body_free",
        "completed",
        "consumption_sha256",
        "exit_code",
        "fixed_source_identity_sha256",
        "launcher_contract_sha256",
        "postrun_identity_all_equal",
        "postrun_identity_sha256",
        "postrun_source_clean",
        "process_group_reaped",
        "run_challenge_id",
        "runtime_identity_sha256",
        "schema_version",
        "semantic_ledger_byte_count",
        "semantic_ledger_logical_sha256",
        "semantic_ledger_persistence_validated",
        "semantic_ledger_raw_sha256",
        "single_use_key_sha256",
        "started",
        "state",
        "stderr_byte_count",
        "stderr_sha256",
        "stderr_state",
        "stdout_byte_count",
        "stdout_sha256",
        "stdout_state",
        "terminal_envelope_sha256",
        "terminal_envelope_sha256_preimage_rule",
        "timed_out",
    }
)
_EXPECTED_BINDING_KEYS = frozenset(
    {
        "admission_sha256",
        "authority_token_sha256",
        "consumption_sha256",
        "fixed_source_identity_sha256",
        "launcher_contract_sha256",
        "postrun_identity_sha256",
        "runtime_identity_sha256",
        "single_use_key_sha256",
        "source_d1_blob_sha1",
    }
)
_LIVE_EVIDENCE_KEYS = frozenset(
    {
        "challenge_generated_after_process_start",
        "challenge_generation_contract",
        "challenge_generation_count",
        "challenge_prebound_in_admission_or_consumption",
        "challenge_second_hash_applied",
        "closure",
        "fixture_active_after_teardown",
        "module_fixture_teardown_report",
        "observation",
        "postprojection_credit_gate",
        "preflight",
        "pytest_exit_code",
        "pytest_session_finish_count",
        "secrets_monkeypatch_or_injection_used",
        "terminalization_count",
    }
)
_SEMANTIC_WRITE_KEYS = frozenset(
    {
        "complete_write_count",
        "exclusive_create",
        "file_mode",
        "fsync_before_process_exit",
        "parent_mode",
        "parent_precreated",
        "partial_write_count",
        "path_outside_cocolon",
        "path_outside_empty_cwd",
        "path_outside_mashos_api",
        "path_outside_retained_runtime",
        "private_ephemeral_path_prebound",
        "symlink",
    }
)
_PROCESS_EVIDENCE_KEYS = frozenset(
    {
        "completed",
        "exit_code",
        "postrun_identity_all_equal",
        "postrun_identity_sha256",
        "postrun_source_clean",
        "process_group_reaped",
        "semantic_ledger_persistence_validated",
        "started",
        "timed_out",
    }
)
_OUTER_WRITE_KEYS = frozenset(
    {
        "capture_after_final_communicate",
        "capture_after_postrun_identity",
        "capture_after_process_group_reap",
        "complete_write_count",
        "envelope_attests_own_persistence",
        "exclusive_create",
        "file_mode",
        "fsync_before_receipt_consumption",
        "launcher_mutated_semantic_ledger",
        "parent_mode",
        "parent_precreated",
        "partial_write_count",
        "path_outside_cocolon",
        "path_outside_empty_cwd",
        "path_outside_mashos_api",
        "path_outside_retained_runtime",
        "private_ephemeral_path_prebound",
        "semantic_ledger_validated_before_creation",
        "symlink",
    }
)

_SEMANTIC_CASE_IDS = (
    "OWNER_IMPLEMENTATION_ABSENT",
    "TOP_KEYSET_OR_SCHEMA",
    "HASH_OR_PREIMAGE_RULE",
    "SOURCE_RUNTIME_LAUNCHER_BINDING",
    "ADMISSION_CONSUMPTION_SINGLE_USE_BINDING",
    "CHALLENGE_OR_OBSERVATION_BINDING",
    "COLLECTION_COUNT_MISSING_DUPLICATE_REORDER_UNKNOWN",
    "REPORT_COUNT",
    "REPORT_INDEX_MISSING_DUPLICATE_OR_RANGE",
    "PHASE_ORDER",
    "SETUP_NONPASS",
    "TEARDOWN_NONPASS",
    "O01_O07_CALL_NONFAIL_SKIP_XFAIL_XPASS",
    "O08_CALL_NONPASS_SKIP_XFAIL_XPASS",
    "SIGNATURE_MISSING_WRONG_OR_CROSSNODE",
    "VIOLATION_MISSING_WRONG_OR_CROSSNODE",
    "PROJECTION_SCHEMA_KEYSET_OR_HASH",
    "PROJECTION_TERMINAL_CLASS",
    "PREFLIGHT_OR_ACQUISITION_CLASS",
    "CLOSURE_NULL_OR_INVALID",
    "GLOBAL_VIOLATION_VECTOR",
    "EQUALITY_FALSE",
    "TERMINALIZATION_OR_POSTPROJECTION_GATE",
    "SESSION_COUNTS_STATE_OR_WRITE_BOUNDARY",
)
_OUTER_CASE_IDS = (
    "ENVELOPE_TOP_SCHEMA_STATE_OR_HASH",
    "SEMANTIC_LEDGER_LOGICAL_RAW_BYTE_AND_EXIT_CROSSBIND",
    "AUTHORITY_SOURCE_RUNTIME_LAUNCHER_BINDING",
    "ADMISSION_CONSUMPTION_SINGLE_USE_CHALLENGE_BINDING",
    "PROCESS_FLAGS_EXIT_AND_REAP",
    "POSTRUN_IDENTITY_CLEAN_AND_EQUAL",
    "STREAM_STATE_COUNT_HASH_AND_BODY_ABSENCE",
    "WRITE_PERSISTENCE_ORDER_AND_PATH",
)

_HERE = Path(__file__).resolve()
_REPO_ROOT = _HERE.parents[2]


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _label_hash(label: str) -> str:
    return _sha256(label.encode("utf-8"))


def _hash_without(value: dict[str, Any], key: str) -> str:
    preimage = copy.deepcopy(value)
    del preimage[key]
    return _sha256(_canonical_bytes(preimage))


def _git_blob_sha1(raw: bytes) -> str:
    preimage = f"blob {len(raw)}\0".encode("ascii") + raw
    return hashlib.sha1(preimage).hexdigest()


def _self_hashed(value: dict[str, Any], key: str) -> dict[str, Any]:
    value[key] = ""
    value[key] = _hash_without(value, key)
    return value


def _projection_rows() -> list[dict[str, Any]]:
    return [
        {
            "node_id": node_id,
            "outcome": "CAUSAL_RED" if index < 7 else "GREEN",
            "causal_signature_id": _SIGNATURES[index],
            "violation_class": _VIOLATIONS[index],
        }
        for index, node_id in enumerate(_ORDERED_NODE_IDS)
    ]


def _normalized_expected_rows() -> list[dict[str, Any]]:
    return [
        {
            "node_id": f"O{index + 1:02d}",
            "outcome": (
                "CAUSAL_RED" if index < 7 else "GREEN_V1_INVARIANCE"
            ),
            "causal_signature_id": _SIGNATURES[index],
            "violation_class": _VIOLATIONS[index],
        }
        for index in range(8)
    ]


def _pytest_reports() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, node_id in enumerate(_ORDERED_NODE_IDS):
        rows.extend(
            (
                {
                    "causal_signature_id": None,
                    "node_id": node_id,
                    "outcome": "passed",
                    "phase": "setup",
                    "report_index": 3 * index,
                    "violation_class": None,
                },
                {
                    "causal_signature_id": _SIGNATURES[index],
                    "node_id": node_id,
                    "outcome": "failed" if index < 7 else "passed",
                    "phase": "call",
                    "report_index": 3 * index + 1,
                    "violation_class": _VIOLATIONS[index],
                },
                {
                    "causal_signature_id": None,
                    "node_id": node_id,
                    "outcome": "passed",
                    "phase": "teardown",
                    "report_index": 3 * index + 2,
                    "violation_class": None,
                },
            )
        )
    return rows


def _valid_pair() -> dict[str, Any]:
    challenge = _label_hash("synthetic-child-generated-challenge")
    preflight = _self_hashed(
        {
            "preflight_class": "PREFLIGHT_ELIGIBLE",
            "run_challenge_id": challenge,
        },
        "preflight_sha256",
    )
    observation = _self_hashed(
        {
            "acquisition_class": "AVAILABLE_MATCH",
            "body_free": True,
            "run_challenge_id": challenge,
        },
        "observation_sha256",
    )
    closure = _self_hashed(
        {
            "observation_sha256": observation["observation_sha256"],
            "postrun_matches_acquisition": True,
            "run_challenge_id": challenge,
            "run_state": "CLOSED",
        },
        "closure_sha256",
    )
    projection = _self_hashed(
        {
            "schema_version": _PROJECTION_SCHEMA,
            "source_preflight_sha256": preflight["preflight_sha256"],
            "source_observation_sha256": observation["observation_sha256"],
            "source_closure_sha256": closure["closure_sha256"],
            "run_challenge_id": challenge,
            "run_scope": "D1_V5_CAUSAL_RED_REFREEZE",
            "repository_full_name": "MassyuRed/mashos-api",
            "remote_ref": "refs/heads/main",
            "acquisition_profile_id": (
                "cocolon.emlis.nls_v3.recovery_epoch004."
                "actual_git_ls_remote_main.v1"
            ),
            "preflight_class": "PREFLIGHT_ELIGIBLE",
            "acquisition_class": "AVAILABLE_MATCH",
            "run_terminal_class": "D1_CAUSAL_RED_REFREEZE_ESTABLISHED",
            "violation_classes": list(_GLOBAL_VIOLATIONS),
            "oracle_outcomes": _projection_rows(),
            "equality_verdicts": {key: True for key in _EQUALITY_KEYS},
        },
        "projection_sha256",
    )
    identities = {
        key: _label_hash(key)
        for key in (
            "admission_sha256",
            "authority_token_sha256",
            "consumption_sha256",
            "fixed_source_identity_sha256",
            "launcher_contract_sha256",
            "runtime_identity_sha256",
            "single_use_key_sha256",
        )
    }
    ledger = _self_hashed(
        {
            **identities,
            "body_free": True,
            "collection": {
                "collected_count": 8,
                "ordered_node_ids": list(_ORDERED_NODE_IDS),
                "ordered_node_list_sha256": _ORDERED_NODE_LIST_SHA256,
                "source_d1_blob_sha1": _D1_BLOB_SHA1,
            },
            "d1_projection": projection,
            "ledger_sha256_preimage_rule": _LEDGER_HASH_RULE,
            "pytest_reports": _pytest_reports(),
            "run_challenge_id": challenge,
            "schema_version": _LEDGER_SCHEMA,
            "session": {
                "collected_count": 8,
                "error_count": 0,
                "executed_count": 8,
                "exit_code": 1,
                "failed_count": 7,
                "passed_count": 1,
                "report_count": 24,
                "session_finish_count": 1,
            },
            "state": _LEDGER_STATE,
        },
        "ledger_sha256",
    )
    ledger_raw = _canonical_bytes(ledger) + b"\n"
    final_stdout = b"synthetic pytest terminal diagnostic\n"
    final_stderr = b""
    envelope = _self_hashed(
        {
            **identities,
            "body_free": True,
            "completed": True,
            "exit_code": 1,
            "postrun_identity_all_equal": True,
            "postrun_identity_sha256": _label_hash("postrun_identity_sha256"),
            "postrun_source_clean": True,
            "process_group_reaped": True,
            "run_challenge_id": challenge,
            "schema_version": _ENVELOPE_SCHEMA,
            "semantic_ledger_byte_count": len(ledger_raw),
            "semantic_ledger_logical_sha256": ledger["ledger_sha256"],
            "semantic_ledger_persistence_validated": True,
            "semantic_ledger_raw_sha256": _sha256(ledger_raw),
            "started": True,
            "state": _ENVELOPE_STATE,
            "stderr_byte_count": len(final_stderr),
            "stderr_sha256": _sha256(final_stderr),
            "stderr_state": "CAPTURED",
            "stdout_byte_count": len(final_stdout),
            "stdout_sha256": _sha256(final_stdout),
            "stdout_state": "CAPTURED",
            "terminal_envelope_sha256_preimage_rule": _ENVELOPE_HASH_RULE,
            "timed_out": False,
        },
        "terminal_envelope_sha256",
    )
    envelope_raw = _canonical_bytes(envelope) + b"\n"
    return {
        "semantic_ledger": ledger,
        "semantic_ledger_raw": ledger_raw,
        "terminal_envelope": envelope,
        "terminal_envelope_raw": envelope_raw,
        "final_stdout": final_stdout,
        "final_stderr": final_stderr,
        "expected_bindings": {
            **identities,
            "postrun_identity_sha256": envelope["postrun_identity_sha256"],
            "source_d1_blob_sha1": _D1_BLOB_SHA1,
        },
        "live_evidence": {
            "preflight": preflight,
            "observation": observation,
            "closure": closure,
            "challenge_generation_contract": (
                "SHA256_OF_SECRETS_TOKEN_BYTES_32"
            ),
            "challenge_generation_count": 1,
            "challenge_generated_after_process_start": True,
            "challenge_prebound_in_admission_or_consumption": False,
            "challenge_second_hash_applied": False,
            "secrets_monkeypatch_or_injection_used": False,
            "terminalization_count": 1,
            "postprojection_credit_gate": True,
            "fixture_active_after_teardown": False,
            "module_fixture_teardown_report": "passed",
            "pytest_exit_code": 1,
            "pytest_session_finish_count": 1,
        },
        "semantic_write": {
            "complete_write_count": 1,
            "exclusive_create": True,
            "file_mode": "0600",
            "fsync_before_process_exit": True,
            "parent_mode": "0700",
            "parent_precreated": True,
            "partial_write_count": 0,
            "path_outside_cocolon": True,
            "path_outside_empty_cwd": True,
            "path_outside_mashos_api": True,
            "path_outside_retained_runtime": True,
            "private_ephemeral_path_prebound": True,
            "symlink": False,
        },
        "process_evidence": {
            "completed": True,
            "exit_code": 1,
            "postrun_identity_all_equal": True,
            "postrun_identity_sha256": envelope["postrun_identity_sha256"],
            "postrun_source_clean": True,
            "process_group_reaped": True,
            "semantic_ledger_persistence_validated": True,
            "started": True,
            "timed_out": False,
        },
        "outer_write": {
            "capture_after_final_communicate": True,
            "capture_after_postrun_identity": True,
            "capture_after_process_group_reap": True,
            "complete_write_count": 1,
            "envelope_attests_own_persistence": False,
            "exclusive_create": True,
            "file_mode": "0600",
            "fsync_before_receipt_consumption": True,
            "launcher_mutated_semantic_ledger": False,
            "parent_mode": "0700",
            "parent_precreated": True,
            "partial_write_count": 0,
            "path_outside_cocolon": True,
            "path_outside_empty_cwd": True,
            "path_outside_mashos_api": True,
            "path_outside_retained_runtime": True,
            "private_ephemeral_path_prebound": True,
            "semantic_ledger_validated_before_creation": True,
            "symlink": False,
        },
    }


def _leaf(
    case_id: str,
    leaf_id: str,
    operation: str,
    path: tuple[Any, ...],
    value: Any = None,
    repairs: tuple[str, ...] = (),
) -> dict[str, Any]:
    return {
        "case_id": case_id,
        "leaf_id": leaf_id,
        "operation": operation,
        "path": path,
        "value": value,
        "repairs": repairs,
    }


_SEMANTIC_LEAVES = (
    _leaf(
        "TOP_KEYSET_OR_SCHEMA",
        "S02_TOP_KEY_MISSING",
        "delete",
        ("semantic_ledger", "body_free"),
        repairs=("ledger_bind",),
    ),
    _leaf(
        "TOP_KEYSET_OR_SCHEMA",
        "S02_TOP_KEY_UNKNOWN",
        "add",
        ("semantic_ledger", "unknown"),
        True,
        ("ledger_bind",),
    ),
    _leaf(
        "TOP_KEYSET_OR_SCHEMA",
        "S02_SCHEMA_WRONG",
        "set",
        ("semantic_ledger", "schema_version"),
        "wrong.schema",
        ("ledger_bind",),
    ),
    _leaf(
        "TOP_KEYSET_OR_SCHEMA",
        "S02_BODY_FREE_FALSE",
        "set",
        ("semantic_ledger", "body_free"),
        False,
        ("ledger_bind",),
    ),
    _leaf(
        "HASH_OR_PREIMAGE_RULE",
        "S03_LEDGER_SELF_HASH_WRONG",
        "set",
        ("semantic_ledger", "ledger_sha256"),
        "0" * 64,
    ),
    _leaf(
        "HASH_OR_PREIMAGE_RULE",
        "S03_LEDGER_RULE_WRONG",
        "set",
        ("semantic_ledger", "ledger_sha256_preimage_rule"),
        "WRONG_RULE",
        ("ledger_bind",),
    ),
    _leaf(
        "SOURCE_RUNTIME_LAUNCHER_BINDING",
        "S04_SOURCE_IDENTITY_WRONG",
        "set",
        ("semantic_ledger", "fixed_source_identity_sha256"),
        "0" * 64,
        ("ledger_bind",),
    ),
    _leaf(
        "SOURCE_RUNTIME_LAUNCHER_BINDING",
        "S04_RUNTIME_IDENTITY_WRONG",
        "set",
        ("semantic_ledger", "runtime_identity_sha256"),
        "0" * 64,
        ("ledger_bind",),
    ),
    _leaf(
        "SOURCE_RUNTIME_LAUNCHER_BINDING",
        "S04_LAUNCHER_IDENTITY_WRONG",
        "set",
        ("semantic_ledger", "launcher_contract_sha256"),
        "0" * 64,
        ("ledger_bind",),
    ),
    _leaf(
        "SOURCE_RUNTIME_LAUNCHER_BINDING",
        "S04_AUTHORITY_IDENTITY_WRONG",
        "set",
        ("semantic_ledger", "authority_token_sha256"),
        "0" * 64,
        ("ledger_bind",),
    ),
    _leaf(
        "SOURCE_RUNTIME_LAUNCHER_BINDING",
        "S04_EXPECTED_BINDING_KEY_MISSING",
        "delete",
        ("expected_bindings", "fixed_source_identity_sha256"),
    ),
    _leaf(
        "SOURCE_RUNTIME_LAUNCHER_BINDING",
        "S04_EXPECTED_BINDING_KEY_UNKNOWN",
        "add",
        ("expected_bindings", "unknown"),
        "0" * 64,
    ),
    _leaf(
        "ADMISSION_CONSUMPTION_SINGLE_USE_BINDING",
        "S05_ADMISSION_WRONG",
        "set",
        ("semantic_ledger", "admission_sha256"),
        "0" * 64,
        ("ledger_bind",),
    ),
    _leaf(
        "ADMISSION_CONSUMPTION_SINGLE_USE_BINDING",
        "S05_CONSUMPTION_WRONG",
        "set",
        ("semantic_ledger", "consumption_sha256"),
        "0" * 64,
        ("ledger_bind",),
    ),
    _leaf(
        "ADMISSION_CONSUMPTION_SINGLE_USE_BINDING",
        "S05_SINGLE_USE_WRONG",
        "set",
        ("semantic_ledger", "single_use_key_sha256"),
        "0" * 64,
        ("ledger_bind",),
    ),
    _leaf(
        "CHALLENGE_OR_OBSERVATION_BINDING",
        "S06_LEDGER_PROJECTION_CHALLENGE_MISMATCH",
        "set",
        ("semantic_ledger", "run_challenge_id"),
        "1" * 64,
        ("ledger_bind",),
    ),
    _leaf(
        "CHALLENGE_OR_OBSERVATION_BINDING",
        "S06_CHALLENGE_NOT_LOWER64HEX",
        "set",
        ("semantic_ledger", "run_challenge_id"),
        "G" * 64,
        ("ledger_bind",),
    ),
    _leaf(
        "CHALLENGE_OR_OBSERVATION_BINDING",
        "S06_PREFLIGHT_CHALLENGE_MISMATCH",
        "set",
        ("live_evidence", "preflight", "run_challenge_id"),
        "1" * 64,
        ("live_preflight", "projection", "ledger_bind"),
    ),
    _leaf(
        "CHALLENGE_OR_OBSERVATION_BINDING",
        "S06_OBSERVATION_CHALLENGE_MISMATCH",
        "set",
        ("live_evidence", "observation", "run_challenge_id"),
        "1" * 64,
        ("live_observation", "projection", "ledger_bind"),
    ),
    _leaf(
        "CHALLENGE_OR_OBSERVATION_BINDING",
        "S06_PREFLIGHT_SELF_HASH_WRONG",
        "set",
        ("live_evidence", "preflight", "preflight_sha256"),
        "0" * 64,
    ),
    _leaf(
        "CHALLENGE_OR_OBSERVATION_BINDING",
        "S06_OBSERVATION_SELF_HASH_WRONG",
        "set",
        ("live_evidence", "observation", "observation_sha256"),
        "0" * 64,
    ),
    *(
        _leaf(
            "CHALLENGE_OR_OBSERVATION_BINDING",
            leaf_id,
            "set",
            ("live_evidence", key),
            value,
        )
        for leaf_id, key, value in (
            (
                "S06_GENERATION_CONTRACT_WRONG",
                "challenge_generation_contract",
                "WRONG_CONTRACT",
            ),
            ("S06_GENERATION_COUNT_ZERO", "challenge_generation_count", 0),
            (
                "S06_GENERATED_BEFORE_PROCESS_START",
                "challenge_generated_after_process_start",
                False,
            ),
            (
                "S06_CHALLENGE_PREBOUND",
                "challenge_prebound_in_admission_or_consumption",
                True,
            ),
            (
                "S06_SECOND_HASH_APPLIED",
                "challenge_second_hash_applied",
                True,
            ),
            (
                "S06_SECRETS_INJECTION_USED",
                "secrets_monkeypatch_or_injection_used",
                True,
            ),
        )
    ),
    _leaf(
        "COLLECTION_COUNT_MISSING_DUPLICATE_REORDER_UNKNOWN",
        "S07_COLLECTION_COUNT_WRONG",
        "set",
        ("semantic_ledger", "collection", "collected_count"),
        7,
        ("ledger_bind",),
    ),
    _leaf(
        "COLLECTION_COUNT_MISSING_DUPLICATE_REORDER_UNKNOWN",
        "S07_NODE_MISSING",
        "pop",
        ("semantic_ledger", "collection", "ordered_node_ids"),
        -1,
        ("ledger_bind",),
    ),
    _leaf(
        "COLLECTION_COUNT_MISSING_DUPLICATE_REORDER_UNKNOWN",
        "S07_NODE_DUPLICATE",
        "copy_from",
        ("semantic_ledger", "collection", "ordered_node_ids", 1),
        ("semantic_ledger", "collection", "ordered_node_ids", 0),
        ("ledger_bind",),
    ),
    _leaf(
        "COLLECTION_COUNT_MISSING_DUPLICATE_REORDER_UNKNOWN",
        "S07_NODE_REORDER",
        "swap",
        ("semantic_ledger", "collection", "ordered_node_ids"),
        (0, 1),
        ("ledger_bind",),
    ),
    _leaf(
        "COLLECTION_COUNT_MISSING_DUPLICATE_REORDER_UNKNOWN",
        "S07_NODE_UNKNOWN",
        "set",
        ("semantic_ledger", "collection", "ordered_node_ids", 0),
        "ai/tests/unknown.py::test_unknown",
        ("ledger_bind",),
    ),
    _leaf(
        "COLLECTION_COUNT_MISSING_DUPLICATE_REORDER_UNKNOWN",
        "S07_NODE_LIST_HASH_WRONG",
        "set",
        ("semantic_ledger", "collection", "ordered_node_list_sha256"),
        "0" * 64,
        ("ledger_bind",),
    ),
    _leaf(
        "COLLECTION_COUNT_MISSING_DUPLICATE_REORDER_UNKNOWN",
        "S07_SOURCE_D1_BLOB_WRONG",
        "set",
        ("semantic_ledger", "collection", "source_d1_blob_sha1"),
        "0" * 40,
        ("ledger_bind",),
    ),
    _leaf(
        "COLLECTION_COUNT_MISSING_DUPLICATE_REORDER_UNKNOWN",
        "S07_COLLECTION_KEY_MISSING",
        "delete",
        ("semantic_ledger", "collection", "source_d1_blob_sha1"),
        repairs=("ledger_bind",),
    ),
    _leaf(
        "COLLECTION_COUNT_MISSING_DUPLICATE_REORDER_UNKNOWN",
        "S07_COLLECTION_KEY_UNKNOWN",
        "add",
        ("semantic_ledger", "collection", "unknown"),
        True,
        ("ledger_bind",),
    ),
    _leaf(
        "REPORT_COUNT",
        "S08_REPORT_EXACT23",
        "pop",
        ("semantic_ledger", "pytest_reports"),
        -1,
        ("ledger_bind",),
    ),
    _leaf(
        "REPORT_COUNT",
        "S08_REPORT_EXACT25",
        "append_copy",
        ("semantic_ledger", "pytest_reports"),
        -1,
        ("ledger_bind",),
    ),
    _leaf(
        "REPORT_COUNT",
        "S08_REPORT_KEY_UNKNOWN",
        "add",
        ("semantic_ledger", "pytest_reports", 0, "unknown"),
        True,
        ("ledger_bind",),
    ),
    _leaf(
        "REPORT_INDEX_MISSING_DUPLICATE_OR_RANGE",
        "S09_INDEX_KEY_MISSING",
        "delete",
        ("semantic_ledger", "pytest_reports", 0, "report_index"),
        repairs=("ledger_bind",),
    ),
    _leaf(
        "REPORT_INDEX_MISSING_DUPLICATE_OR_RANGE",
        "S09_INDEX_DUPLICATE",
        "set",
        ("semantic_ledger", "pytest_reports", 1, "report_index"),
        0,
        ("ledger_bind",),
    ),
    _leaf(
        "REPORT_INDEX_MISSING_DUPLICATE_OR_RANGE",
        "S09_INDEX_OUT_OF_RANGE",
        "set",
        ("semantic_ledger", "pytest_reports", 23, "report_index"),
        24,
        ("ledger_bind",),
    ),
    _leaf(
        "REPORT_INDEX_MISSING_DUPLICATE_OR_RANGE",
        "S09_INDEX_FORMULA_WRONG",
        "swap",
        ("semantic_ledger", "pytest_reports"),
        (1, 4),
        ("ledger_bind",),
    ),
    _leaf(
        "REPORT_INDEX_MISSING_DUPLICATE_OR_RANGE",
        "S09_REPORT_NODE_ID_WRONG",
        "set",
        ("semantic_ledger", "pytest_reports", 0, "node_id"),
        "ai/tests/unknown.py::test_unknown",
        ("ledger_bind",),
    ),
    _leaf(
        "PHASE_ORDER",
        "S10_PHASE_REORDER",
        "swap",
        ("semantic_ledger", "pytest_reports"),
        (0, 1),
        ("ledger_bind",),
    ),
    _leaf(
        "PHASE_ORDER",
        "S10_PHASE_UNKNOWN",
        "set",
        ("semantic_ledger", "pytest_reports", 0, "phase"),
        "unknown",
        ("ledger_bind",),
    ),
    _leaf(
        "SETUP_NONPASS",
        "S11_SETUP_FAILED",
        "set",
        ("semantic_ledger", "pytest_reports", 0, "outcome"),
        "failed",
        ("ledger_bind",),
    ),
    _leaf(
        "SETUP_NONPASS",
        "S11_SETUP_SKIPPED",
        "set",
        ("semantic_ledger", "pytest_reports", 0, "outcome"),
        "skipped",
        ("ledger_bind",),
    ),
    _leaf(
        "SETUP_NONPASS",
        "S11_SETUP_SIGNATURE_NON_NULL",
        "set",
        ("semantic_ledger", "pytest_reports", 0, "causal_signature_id"),
        "FORBIDDEN_SETUP_SIGNATURE",
        ("ledger_bind",),
    ),
    _leaf(
        "SETUP_NONPASS",
        "S11_SETUP_VIOLATION_NON_NULL",
        "set",
        ("semantic_ledger", "pytest_reports", 0, "violation_class"),
        "FORBIDDEN_SETUP_VIOLATION",
        ("ledger_bind",),
    ),
    _leaf(
        "TEARDOWN_NONPASS",
        "S12_TEARDOWN_FAILED",
        "set",
        ("semantic_ledger", "pytest_reports", 2, "outcome"),
        "failed",
        ("ledger_bind",),
    ),
    _leaf(
        "TEARDOWN_NONPASS",
        "S12_TEARDOWN_SKIPPED",
        "set",
        ("semantic_ledger", "pytest_reports", 2, "outcome"),
        "skipped",
        ("ledger_bind",),
    ),
    _leaf(
        "TEARDOWN_NONPASS",
        "S12_TEARDOWN_SIGNATURE_NON_NULL",
        "set",
        ("semantic_ledger", "pytest_reports", 2, "causal_signature_id"),
        "FORBIDDEN_TEARDOWN_SIGNATURE",
        ("ledger_bind",),
    ),
    _leaf(
        "TEARDOWN_NONPASS",
        "S12_TEARDOWN_VIOLATION_NON_NULL",
        "set",
        ("semantic_ledger", "pytest_reports", 2, "violation_class"),
        "FORBIDDEN_TEARDOWN_VIOLATION",
        ("ledger_bind",),
    ),
    *(
        _leaf(
            "O01_O07_CALL_NONFAIL_SKIP_XFAIL_XPASS",
            f"S13_O01_CALL_{outcome.upper()}",
            "set",
            ("semantic_ledger", "pytest_reports", 1, "outcome"),
            outcome,
            ("ledger_bind",),
        )
        for outcome in ("passed", "skipped", "xfailed", "xpassed")
    ),
    *(
        _leaf(
            "O08_CALL_NONPASS_SKIP_XFAIL_XPASS",
            f"S14_O08_CALL_{outcome.upper()}",
            "set",
            ("semantic_ledger", "pytest_reports", 22, "outcome"),
            outcome,
            ("ledger_bind",),
        )
        for outcome in ("failed", "skipped", "xfailed", "xpassed")
    ),
    _leaf(
        "O08_CALL_NONPASS_SKIP_XFAIL_XPASS",
        "S14_O08_SIGNATURE_NON_NULL",
        "set",
        ("semantic_ledger", "pytest_reports", 22, "causal_signature_id"),
        "FORBIDDEN_O08_SIGNATURE",
        ("ledger_bind",),
    ),
    _leaf(
        "O08_CALL_NONPASS_SKIP_XFAIL_XPASS",
        "S14_O08_VIOLATION_NON_NULL",
        "set",
        ("semantic_ledger", "pytest_reports", 22, "violation_class"),
        "FORBIDDEN_O08_VIOLATION",
        ("ledger_bind",),
    ),
    _leaf(
        "SIGNATURE_MISSING_WRONG_OR_CROSSNODE",
        "S15_SIGNATURE_MISSING",
        "set",
        ("semantic_ledger", "pytest_reports", 1, "causal_signature_id"),
        None,
        ("ledger_bind",),
    ),
    _leaf(
        "SIGNATURE_MISSING_WRONG_OR_CROSSNODE",
        "S15_SIGNATURE_WRONG",
        "set",
        ("semantic_ledger", "pytest_reports", 1, "causal_signature_id"),
        "WRONG_SIGNATURE",
        ("ledger_bind",),
    ),
    _leaf(
        "SIGNATURE_MISSING_WRONG_OR_CROSSNODE",
        "S15_SIGNATURE_CROSSNODE",
        "copy_from",
        ("semantic_ledger", "pytest_reports", 1, "causal_signature_id"),
        ("semantic_ledger", "pytest_reports", 4, "causal_signature_id"),
        ("ledger_bind",),
    ),
    _leaf(
        "VIOLATION_MISSING_WRONG_OR_CROSSNODE",
        "S16_VIOLATION_MISSING",
        "set",
        ("semantic_ledger", "pytest_reports", 1, "violation_class"),
        None,
        ("ledger_bind",),
    ),
    _leaf(
        "VIOLATION_MISSING_WRONG_OR_CROSSNODE",
        "S16_VIOLATION_WRONG",
        "set",
        ("semantic_ledger", "pytest_reports", 1, "violation_class"),
        "WRONG_VIOLATION",
        ("ledger_bind",),
    ),
    _leaf(
        "VIOLATION_MISSING_WRONG_OR_CROSSNODE",
        "S16_VIOLATION_CROSSNODE",
        "copy_from",
        ("semantic_ledger", "pytest_reports", 7, "violation_class"),
        ("semantic_ledger", "pytest_reports", 10, "violation_class"),
        ("ledger_bind",),
    ),
    _leaf(
        "PROJECTION_SCHEMA_KEYSET_OR_HASH",
        "S17_PROJECTION_KEY_MISSING",
        "delete",
        ("semantic_ledger", "d1_projection", "remote_ref"),
        repairs=("projection", "ledger_bind"),
    ),
    _leaf(
        "PROJECTION_SCHEMA_KEYSET_OR_HASH",
        "S17_PROJECTION_KEY_UNKNOWN",
        "add",
        ("semantic_ledger", "d1_projection", "unknown"),
        True,
        ("projection", "ledger_bind"),
    ),
    _leaf(
        "PROJECTION_SCHEMA_KEYSET_OR_HASH",
        "S17_PROJECTION_SCHEMA_WRONG",
        "set",
        ("semantic_ledger", "d1_projection", "schema_version"),
        "wrong.schema",
        ("projection", "ledger_bind"),
    ),
    _leaf(
        "PROJECTION_SCHEMA_KEYSET_OR_HASH",
        "S17_PROJECTION_SELF_HASH_WRONG",
        "set",
        ("semantic_ledger", "d1_projection", "projection_sha256"),
        "0" * 64,
        ("ledger_bind",),
    ),
    _leaf(
        "PROJECTION_SCHEMA_KEYSET_OR_HASH",
        "S17_ORACLE_ROW_KEY_MISSING",
        "delete",
        (
            "semantic_ledger",
            "d1_projection",
            "oracle_outcomes",
            0,
            "outcome",
        ),
        repairs=("projection", "ledger_bind"),
    ),
    _leaf(
        "PROJECTION_SCHEMA_KEYSET_OR_HASH",
        "S17_ORACLE_NODE_WRONG",
        "set",
        (
            "semantic_ledger",
            "d1_projection",
            "oracle_outcomes",
            0,
            "node_id",
        ),
        "O01",
        ("projection", "ledger_bind"),
    ),
    _leaf(
        "PROJECTION_SCHEMA_KEYSET_OR_HASH",
        "S17_ORACLE_OUTCOME_WRONG",
        "set",
        (
            "semantic_ledger",
            "d1_projection",
            "oracle_outcomes",
            0,
            "outcome",
        ),
        "GREEN",
        ("projection", "ledger_bind"),
    ),
    _leaf(
        "PROJECTION_SCHEMA_KEYSET_OR_HASH",
        "S17_ORACLE_ROWS_REORDERED",
        "swap",
        ("semantic_ledger", "d1_projection", "oracle_outcomes"),
        (0, 1),
        ("projection", "ledger_bind"),
    ),
    *(
        _leaf(
            "PROJECTION_SCHEMA_KEYSET_OR_HASH",
            leaf_id,
            "set",
            ("semantic_ledger", "d1_projection", key),
            value,
            ("projection", "ledger_bind"),
        )
        for leaf_id, key, value in (
            (
                "S17_SOURCE_PREFLIGHT_CROSSBIND",
                "source_preflight_sha256",
                "0" * 64,
            ),
            (
                "S17_SOURCE_OBSERVATION_CROSSBIND",
                "source_observation_sha256",
                "0" * 64,
            ),
            (
                "S17_SOURCE_CLOSURE_CROSSBIND",
                "source_closure_sha256",
                "0" * 64,
            ),
            ("S17_RUN_SCOPE_WRONG", "run_scope", "WRONG_SCOPE"),
            (
                "S17_REPOSITORY_WRONG",
                "repository_full_name",
                "Wrong/repository",
            ),
            ("S17_REMOTE_REF_WRONG", "remote_ref", "refs/heads/wrong"),
            (
                "S17_ACQUISITION_PROFILE_WRONG",
                "acquisition_profile_id",
                "wrong.profile",
            ),
        )
    ),
    _leaf(
        "PROJECTION_TERMINAL_CLASS",
        "S18_TERMINAL_CLASS_WRONG",
        "set",
        ("semantic_ledger", "d1_projection", "run_terminal_class"),
        "RUN_EVALUATED_GREEN",
        ("projection", "ledger_bind"),
    ),
    _leaf(
        "PREFLIGHT_OR_ACQUISITION_CLASS",
        "S19_PREFLIGHT_CLASS_WRONG",
        "set",
        ("semantic_ledger", "d1_projection", "preflight_class"),
        "PREFLIGHT_REJECTED",
        ("projection", "ledger_bind"),
    ),
    _leaf(
        "PREFLIGHT_OR_ACQUISITION_CLASS",
        "S19_ACQUISITION_CLASS_WRONG",
        "set",
        ("semantic_ledger", "d1_projection", "acquisition_class"),
        "UNAVAILABLE",
        ("projection", "ledger_bind"),
    ),
    _leaf(
        "CLOSURE_NULL_OR_INVALID",
        "S20_CLOSURE_NULL",
        "set",
        ("live_evidence", "closure"),
        None,
    ),
    _leaf(
        "CLOSURE_NULL_OR_INVALID",
        "S20_CLOSURE_STATE_INVALID",
        "set",
        ("live_evidence", "closure", "run_state"),
        "OPEN",
        ("live_closure", "projection", "ledger_bind"),
    ),
    _leaf(
        "CLOSURE_NULL_OR_INVALID",
        "S20_CLOSURE_SELF_HASH_WRONG",
        "set",
        ("live_evidence", "closure", "closure_sha256"),
        "0" * 64,
    ),
    _leaf(
        "CLOSURE_NULL_OR_INVALID",
        "S20_CLOSURE_OBSERVATION_CROSSBIND",
        "set",
        ("live_evidence", "closure", "observation_sha256"),
        "0" * 64,
        ("live_closure", "projection", "ledger_bind"),
    ),
    *(
        _leaf(
            "GLOBAL_VIOLATION_VECTOR",
            leaf_id,
            operation,
            ("semantic_ledger", "d1_projection", "violation_classes"),
            value,
            ("projection", "ledger_bind"),
        )
        for leaf_id, operation, value in (
            ("S21_VIOLATION_MISSING", "pop", -1),
            (
                "S21_VIOLATION_EXTRA",
                "append",
                "UNAPPROVED_VIOLATION",
            ),
            ("S21_VIOLATION_REORDER", "swap", (0, 1)),
            (
                "S21_VIOLATION_UNKNOWN",
                "set_index",
                (0, "UNKNOWN_VIOLATION"),
            ),
        )
    ),
    _leaf(
        "EQUALITY_FALSE",
        "S22_EQUALITY_FALSE",
        "set",
        (
            "semantic_ledger",
            "d1_projection",
            "equality_verdicts",
            "source_cut_consistent",
        ),
        False,
        ("projection", "ledger_bind"),
    ),
    _leaf(
        "EQUALITY_FALSE",
        "S22_EQUALITY_KEY_MISSING",
        "delete",
        (
            "semantic_ledger",
            "d1_projection",
            "equality_verdicts",
            "body_free",
        ),
        repairs=("projection", "ledger_bind"),
    ),
    _leaf(
        "EQUALITY_FALSE",
        "S22_EQUALITY_KEY_UNKNOWN",
        "add",
        (
            "semantic_ledger",
            "d1_projection",
            "equality_verdicts",
            "unknown",
        ),
        True,
        ("projection", "ledger_bind"),
    ),
    _leaf(
        "TERMINALIZATION_OR_POSTPROJECTION_GATE",
        "S23_TERMINALIZATION_ZERO",
        "set",
        ("live_evidence", "terminalization_count"),
        0,
    ),
    _leaf(
        "TERMINALIZATION_OR_POSTPROJECTION_GATE",
        "S23_TERMINALIZATION_TWO",
        "set",
        ("live_evidence", "terminalization_count"),
        2,
    ),
    _leaf(
        "TERMINALIZATION_OR_POSTPROJECTION_GATE",
        "S23_POSTPROJECTION_GATE_FALSE",
        "set",
        ("live_evidence", "postprojection_credit_gate"),
        False,
    ),
    _leaf(
        "TERMINALIZATION_OR_POSTPROJECTION_GATE",
        "S23_FIXTURE_STILL_ACTIVE",
        "set",
        ("live_evidence", "fixture_active_after_teardown"),
        True,
    ),
    _leaf(
        "TERMINALIZATION_OR_POSTPROJECTION_GATE",
        "S23_FIXTURE_TEARDOWN_NONPASS",
        "set",
        ("live_evidence", "module_fixture_teardown_report"),
        "failed",
    ),
    _leaf(
        "TERMINALIZATION_OR_POSTPROJECTION_GATE",
        "S23_LIVE_EVIDENCE_KEY_MISSING",
        "delete",
        ("live_evidence", "postprojection_credit_gate"),
    ),
    _leaf(
        "TERMINALIZATION_OR_POSTPROJECTION_GATE",
        "S23_LIVE_EVIDENCE_KEY_UNKNOWN",
        "add",
        ("live_evidence", "unknown"),
        True,
    ),
    *(
        _leaf(
            "SESSION_COUNTS_STATE_OR_WRITE_BOUNDARY",
            f"S24_SESSION_{key.upper()}",
            "set",
            ("semantic_ledger", "session", key),
            value,
            ("ledger_bind",),
        )
        for key, value in (
            ("collected_count", 7),
            ("error_count", 1),
            ("executed_count", 7),
            ("exit_code", 0),
            ("failed_count", 6),
            ("passed_count", 2),
            ("report_count", 23),
            ("session_finish_count", 0),
        )
    ),
    _leaf(
        "SESSION_COUNTS_STATE_OR_WRITE_BOUNDARY",
        "S24_SESSION_KEY_MISSING",
        "delete",
        ("semantic_ledger", "session", "error_count"),
        repairs=("ledger_bind",),
    ),
    _leaf(
        "SESSION_COUNTS_STATE_OR_WRITE_BOUNDARY",
        "S24_SESSION_KEY_UNKNOWN",
        "add",
        ("semantic_ledger", "session", "unknown"),
        0,
        ("ledger_bind",),
    ),
    _leaf(
        "SESSION_COUNTS_STATE_OR_WRITE_BOUNDARY",
        "S24_LEDGER_STATE_WRONG",
        "set",
        ("semantic_ledger", "state"),
        "WRONG_STATE",
        ("ledger_bind",),
    ),
    _leaf(
        "SESSION_COUNTS_STATE_OR_WRITE_BOUNDARY",
        "S24_LIVE_EXIT_CODE_WRONG",
        "set",
        ("live_evidence", "pytest_exit_code"),
        0,
    ),
    _leaf(
        "SESSION_COUNTS_STATE_OR_WRITE_BOUNDARY",
        "S24_LIVE_SESSION_FINISH_ZERO",
        "set",
        ("live_evidence", "pytest_session_finish_count"),
        0,
    ),
    _leaf(
        "SESSION_COUNTS_STATE_OR_WRITE_BOUNDARY",
        "S24_ARTIFACT_MISSING_LF",
        "strip_final_lf",
        ("semantic_ledger_raw",),
    ),
    _leaf(
        "SESSION_COUNTS_STATE_OR_WRITE_BOUNDARY",
        "S24_ARTIFACT_EXTRA_LF",
        "append_final_lf",
        ("semantic_ledger_raw",),
    ),
    _leaf(
        "SESSION_COUNTS_STATE_OR_WRITE_BOUNDARY",
        "S24_ARTIFACT_NONCANONICAL_JSON",
        "noncanonical_json",
        ("semantic_ledger_raw",),
        ("semantic_ledger",),
    ),
    *(
        _leaf(
            "SESSION_COUNTS_STATE_OR_WRITE_BOUNDARY",
            leaf_id,
            "set",
            ("semantic_write", key),
            value,
        )
        for leaf_id, key, value in (
            ("S24_WRITE_PARTIAL", "partial_write_count", 1),
            ("S24_WRITE_DUPLICATE", "complete_write_count", 2),
            ("S24_FILE_MODE", "file_mode", "0644"),
            ("S24_PARENT_MODE", "parent_mode", "0755"),
            ("S24_PARENT_NOT_PRECREATED", "parent_precreated", False),
            ("S24_SYMLINK", "symlink", True),
            ("S24_NO_FSYNC", "fsync_before_process_exit", False),
            ("S24_NOT_EXCLUSIVE", "exclusive_create", False),
            (
                "S24_PATH_NOT_PREBOUND",
                "private_ephemeral_path_prebound",
                False,
            ),
            (
                "S24_PATH_INSIDE_EMPTY_CWD",
                "path_outside_empty_cwd",
                False,
            ),
            (
                "S24_PATH_INSIDE_MASHOS",
                "path_outside_mashos_api",
                False,
            ),
            ("S24_PATH_INSIDE_COCOLON", "path_outside_cocolon", False),
            (
                "S24_PATH_INSIDE_RUNTIME",
                "path_outside_retained_runtime",
                False,
            ),
        )
    ),
    _leaf(
        "SESSION_COUNTS_STATE_OR_WRITE_BOUNDARY",
        "S24_SEMANTIC_WRITE_KEY_MISSING",
        "delete",
        ("semantic_write", "exclusive_create"),
    ),
    _leaf(
        "SESSION_COUNTS_STATE_OR_WRITE_BOUNDARY",
        "S24_SEMANTIC_WRITE_KEY_UNKNOWN",
        "add",
        ("semantic_write", "unknown"),
        True,
    ),
)

_OUTER_LEAVES = (
    _leaf(
        "ENVELOPE_TOP_SCHEMA_STATE_OR_HASH",
        "O01_TOP_KEY_MISSING",
        "delete",
        ("terminal_envelope", "body_free"),
        repairs=("envelope",),
    ),
    _leaf(
        "ENVELOPE_TOP_SCHEMA_STATE_OR_HASH",
        "O01_TOP_KEY_UNKNOWN",
        "add",
        ("terminal_envelope", "unknown"),
        True,
        ("envelope",),
    ),
    _leaf(
        "ENVELOPE_TOP_SCHEMA_STATE_OR_HASH",
        "O01_SCHEMA_WRONG",
        "set",
        ("terminal_envelope", "schema_version"),
        "wrong.schema",
        ("envelope",),
    ),
    _leaf(
        "ENVELOPE_TOP_SCHEMA_STATE_OR_HASH",
        "O01_STATE_WRONG",
        "set",
        ("terminal_envelope", "state"),
        "WRONG_STATE",
        ("envelope",),
    ),
    _leaf(
        "ENVELOPE_TOP_SCHEMA_STATE_OR_HASH",
        "O01_SELF_HASH_WRONG",
        "set",
        ("terminal_envelope", "terminal_envelope_sha256"),
        "0" * 64,
    ),
    _leaf(
        "ENVELOPE_TOP_SCHEMA_STATE_OR_HASH",
        "O01_PREIMAGE_RULE_WRONG",
        "set",
        (
            "terminal_envelope",
            "terminal_envelope_sha256_preimage_rule",
        ),
        "WRONG_RULE",
        ("envelope",),
    ),
    _leaf(
        "ENVELOPE_TOP_SCHEMA_STATE_OR_HASH",
        "O01_BODY_FREE_FALSE",
        "set",
        ("terminal_envelope", "body_free"),
        False,
        ("envelope",),
    ),
    *(
        _leaf(
            "SEMANTIC_LEDGER_LOGICAL_RAW_BYTE_AND_EXIT_CROSSBIND",
            leaf_id,
            "set",
            ("terminal_envelope", key),
            value,
            ("envelope",),
        )
        for leaf_id, key, value in (
            (
                "O02_LEDGER_LOGICAL_HASH_WRONG",
                "semantic_ledger_logical_sha256",
                "0" * 64,
            ),
            (
                "O02_LEDGER_RAW_HASH_WRONG",
                "semantic_ledger_raw_sha256",
                "0" * 64,
            ),
            ("O02_LEDGER_BYTE_COUNT_WRONG", "semantic_ledger_byte_count", 0),
            ("O02_EXIT_CROSSBIND_WRONG", "exit_code", 0),
        )
    ),
    *(
        _leaf(
            "AUTHORITY_SOURCE_RUNTIME_LAUNCHER_BINDING",
            f"O03_{key.upper()}_MISMATCH",
            "set",
            ("terminal_envelope", key),
            "0" * 64,
            ("envelope",),
        )
        for key in (
            "authority_token_sha256",
            "fixed_source_identity_sha256",
            "runtime_identity_sha256",
            "launcher_contract_sha256",
        )
    ),
    *(
        _leaf(
            "ADMISSION_CONSUMPTION_SINGLE_USE_CHALLENGE_BINDING",
            f"O04_{key.upper()}_MISMATCH",
            "set",
            ("terminal_envelope", key),
            "0" * 64,
            ("envelope",),
        )
        for key in (
            "admission_sha256",
            "consumption_sha256",
            "single_use_key_sha256",
            "run_challenge_id",
        )
    ),
    *(
        _leaf(
            "PROCESS_FLAGS_EXIT_AND_REAP",
            leaf_id,
            "set",
            ("terminal_envelope", key),
            value,
            ("envelope",),
        )
        for leaf_id, key, value in (
            ("O05_NOT_STARTED", "started", False),
            ("O05_NOT_COMPLETED", "completed", False),
            ("O05_TIMED_OUT", "timed_out", True),
            ("O05_EXIT_NOT_ONE", "exit_code", 0),
            ("O05_GROUP_NOT_REAPED", "process_group_reaped", False),
        )
    ),
    _leaf(
        "PROCESS_FLAGS_EXIT_AND_REAP",
        "O05_PROCESS_EVIDENCE_KEY_MISSING",
        "delete",
        ("process_evidence", "started"),
    ),
    _leaf(
        "PROCESS_FLAGS_EXIT_AND_REAP",
        "O05_PROCESS_EVIDENCE_KEY_UNKNOWN",
        "add",
        ("process_evidence", "unknown"),
        True,
    ),
    *(
        _leaf(
            "POSTRUN_IDENTITY_CLEAN_AND_EQUAL",
            leaf_id,
            "set",
            ("terminal_envelope", key),
            value,
            ("envelope",),
        )
        for leaf_id, key, value in (
            ("O06_SOURCE_DIRTY", "postrun_source_clean", False),
            (
                "O06_IDENTITIES_NOT_EQUAL",
                "postrun_identity_all_equal",
                False,
            ),
            (
                "O06_POSTRUN_IDENTITY_INVALID",
                "postrun_identity_sha256",
                "not-a-sha256",
            ),
        )
    ),
    *(
        _leaf(
            "STREAM_STATE_COUNT_HASH_AND_BODY_ABSENCE",
            leaf_id,
            "set",
            path,
            value,
            repairs,
        )
        for leaf_id, path, value, repairs in (
            (
                "O07_STDERR_STATE_WRONG",
                ("terminal_envelope", "stderr_state"),
                "PARTIAL",
                ("envelope",),
            ),
            (
                "O07_STDOUT_STATE_WRONG",
                ("terminal_envelope", "stdout_state"),
                "PARTIAL",
                ("envelope",),
            ),
            (
                "O07_STDERR_COUNT_WRONG",
                ("terminal_envelope", "stderr_byte_count"),
                1,
                ("envelope",),
            ),
            (
                "O07_STDERR_HASH_WRONG",
                ("terminal_envelope", "stderr_sha256"),
                "0" * 64,
                ("envelope",),
            ),
            (
                "O07_STDOUT_COUNT_WRONG",
                ("terminal_envelope", "stdout_byte_count"),
                0,
                ("envelope",),
            ),
            (
                "O07_STDOUT_HASH_WRONG",
                ("terminal_envelope", "stdout_sha256"),
                "0" * 64,
                ("envelope",),
            ),
            (
                "O07_STDOUT_FINAL_BYTES_EMPTY",
                ("final_stdout",),
                b"",
                (),
            ),
            (
                "O07_STDERR_FINAL_BYTES_NONEMPTY",
                ("final_stderr",),
                b"unexpected",
                (),
            ),
        )
    ),
    _leaf(
        "STREAM_STATE_COUNT_HASH_AND_BODY_ABSENCE",
        "O07_STDOUT_BODY_EMBEDDED",
        "add",
        ("terminal_envelope", "stdout_body"),
        "forbidden",
        ("envelope",),
    ),
    _leaf(
        "STREAM_STATE_COUNT_HASH_AND_BODY_ABSENCE",
        "O07_STDERR_BODY_EMBEDDED",
        "add",
        ("terminal_envelope", "stderr_body"),
        "forbidden",
        ("envelope",),
    ),
    _leaf(
        "WRITE_PERSISTENCE_ORDER_AND_PATH",
        "O08_LEDGER_PERSISTENCE_FALSE",
        "set",
        (
            "terminal_envelope",
            "semantic_ledger_persistence_validated",
        ),
        False,
        ("envelope",),
    ),
    *(
        _leaf(
            "WRITE_PERSISTENCE_ORDER_AND_PATH",
            leaf_id,
            "set",
            ("outer_write", key),
            value,
        )
        for leaf_id, key, value in (
            (
                "O08_BEFORE_FINAL_COMMUNICATE",
                "capture_after_final_communicate",
                False,
            ),
            (
                "O08_BEFORE_GROUP_REAP",
                "capture_after_process_group_reap",
                False,
            ),
            (
                "O08_BEFORE_POSTRUN_IDENTITY",
                "capture_after_postrun_identity",
                False,
            ),
            (
                "O08_BEFORE_LEDGER_VALIDATION",
                "semantic_ledger_validated_before_creation",
                False,
            ),
            (
                "O08_LAUNCHER_MUTATED_LEDGER",
                "launcher_mutated_semantic_ledger",
                True,
            ),
            (
                "O08_ENVELOPE_SELF_PERSISTENCE_CLAIM",
                "envelope_attests_own_persistence",
                True,
            ),
            ("O08_WRITE_PARTIAL", "partial_write_count", 1),
            ("O08_WRITE_DUPLICATE", "complete_write_count", 2),
            ("O08_FILE_MODE", "file_mode", "0644"),
            ("O08_PARENT_MODE", "parent_mode", "0755"),
            ("O08_PARENT_NOT_PRECREATED", "parent_precreated", False),
            ("O08_SYMLINK", "symlink", True),
            ("O08_NOT_EXCLUSIVE", "exclusive_create", False),
            ("O08_NO_FSYNC", "fsync_before_receipt_consumption", False),
            (
                "O08_PATH_NOT_PREBOUND",
                "private_ephemeral_path_prebound",
                False,
            ),
            (
                "O08_PATH_INSIDE_EMPTY_CWD",
                "path_outside_empty_cwd",
                False,
            ),
            (
                "O08_PATH_INSIDE_MASHOS",
                "path_outside_mashos_api",
                False,
            ),
            ("O08_PATH_INSIDE_COCOLON", "path_outside_cocolon", False),
            (
                "O08_PATH_INSIDE_RUNTIME",
                "path_outside_retained_runtime",
                False,
            ),
        )
    ),
    _leaf(
        "WRITE_PERSISTENCE_ORDER_AND_PATH",
        "O08_ENVELOPE_ARTIFACT_EXTRA_LF",
        "append_final_lf",
        ("terminal_envelope_raw",),
    ),
    _leaf(
        "WRITE_PERSISTENCE_ORDER_AND_PATH",
        "O08_ENVELOPE_ARTIFACT_NONCANONICAL_JSON",
        "noncanonical_json",
        ("terminal_envelope_raw",),
        ("terminal_envelope",),
    ),
    _leaf(
        "WRITE_PERSISTENCE_ORDER_AND_PATH",
        "O08_OUTER_WRITE_KEY_MISSING",
        "delete",
        ("outer_write", "exclusive_create"),
    ),
    _leaf(
        "WRITE_PERSISTENCE_ORDER_AND_PATH",
        "O08_OUTER_WRITE_KEY_UNKNOWN",
        "add",
        ("outer_write", "unknown"),
        True,
    ),
)


def _container_at(root: Any, path: tuple[Any, ...]) -> tuple[Any, Any]:
    cursor = root
    for part in path[:-1]:
        cursor = cursor[part]
    return cursor, path[-1]


def _apply_operation(pair: dict[str, Any], leaf: dict[str, Any]) -> None:
    operation = leaf["operation"]
    path = leaf["path"]
    value = leaf["value"]
    container, key = _container_at(pair, path)
    if operation == "set":
        container[key] = copy.deepcopy(value)
    elif operation == "add":
        assert key not in container
        container[key] = copy.deepcopy(value)
    elif operation == "delete":
        del container[key]
    elif operation == "pop":
        container[key].pop(value)
    elif operation == "append":
        container[key].append(copy.deepcopy(value))
    elif operation == "append_copy":
        container[key].append(copy.deepcopy(container[key][value]))
    elif operation == "copy_from":
        source_container, source_key = _container_at(pair, value)
        container[key] = copy.deepcopy(source_container[source_key])
    elif operation == "swap":
        left, right = value
        container[key][left], container[key][right] = (
            container[key][right],
            container[key][left],
        )
    elif operation == "set_index":
        index, replacement = value
        container[key][index] = replacement
    elif operation == "strip_final_lf":
        assert container[key].endswith(b"\n")
        container[key] = container[key][:-1]
    elif operation == "append_final_lf":
        assert container[key].endswith(b"\n")
        container[key] = container[key] + b"\n"
    elif operation == "noncanonical_json":
        source_container, source_key = _container_at(pair, value)
        container[key] = (
            json.dumps(
                source_container[source_key],
                ensure_ascii=False,
                sort_keys=False,
                indent=1,
                allow_nan=False,
            ).encode("utf-8")
            + b"\n"
        )
    else:
        raise AssertionError(f"unknown frozen mutation operation: {operation}")


def _repair_pair(pair: dict[str, Any], repairs: tuple[str, ...]) -> None:
    ledger = pair["semantic_ledger"]
    projection = ledger["d1_projection"]
    live = pair["live_evidence"]
    if "live_preflight" in repairs:
        preflight = live["preflight"]
        preflight["preflight_sha256"] = _hash_without(
            preflight,
            "preflight_sha256",
        )
        projection["source_preflight_sha256"] = preflight["preflight_sha256"]
    if "live_observation" in repairs:
        observation = live["observation"]
        observation["observation_sha256"] = _hash_without(
            observation,
            "observation_sha256",
        )
        projection["source_observation_sha256"] = observation[
            "observation_sha256"
        ]
        closure = live["closure"]
        closure["observation_sha256"] = observation["observation_sha256"]
        closure["closure_sha256"] = _hash_without(
            closure,
            "closure_sha256",
        )
        projection["source_closure_sha256"] = closure["closure_sha256"]
    if "live_closure" in repairs:
        closure = live["closure"]
        closure["closure_sha256"] = _hash_without(
            closure,
            "closure_sha256",
        )
        projection["source_closure_sha256"] = closure["closure_sha256"]
    if "projection" in repairs:
        projection["projection_sha256"] = _hash_without(
            projection,
            "projection_sha256",
        )
    if "ledger_bind" in repairs:
        ledger["ledger_sha256"] = _hash_without(ledger, "ledger_sha256")
        pair["semantic_ledger_raw"] = _canonical_bytes(ledger) + b"\n"
        envelope = pair["terminal_envelope"]
        for field in (
            "admission_sha256",
            "authority_token_sha256",
            "consumption_sha256",
            "fixed_source_identity_sha256",
            "launcher_contract_sha256",
            "run_challenge_id",
            "runtime_identity_sha256",
            "single_use_key_sha256",
        ):
            envelope[field] = ledger[field]
        envelope["exit_code"] = ledger["session"]["exit_code"]
        envelope["semantic_ledger_logical_sha256"] = ledger["ledger_sha256"]
        envelope["semantic_ledger_raw_sha256"] = _sha256(
            pair["semantic_ledger_raw"]
        )
        envelope["semantic_ledger_byte_count"] = len(
            pair["semantic_ledger_raw"]
        )
        envelope["terminal_envelope_sha256"] = _hash_without(
            envelope,
            "terminal_envelope_sha256",
        )
        pair["terminal_envelope_raw"] = _canonical_bytes(envelope) + b"\n"
    if "envelope" in repairs:
        envelope = pair["terminal_envelope"]
        envelope["terminal_envelope_sha256"] = _hash_without(
            envelope,
            "terminal_envelope_sha256",
        )
        pair["terminal_envelope_raw"] = _canonical_bytes(envelope) + b"\n"


def _mutated_pair(
    baseline: dict[str, Any],
    leaf: dict[str, Any],
) -> dict[str, Any]:
    mutated = copy.deepcopy(baseline)
    _apply_operation(mutated, leaf)
    _repair_pair(mutated, leaf["repairs"])
    return mutated


def _load_owner_or_red(owner_path: Path) -> ModuleType:
    if not owner_path.is_file():
        pytest.fail(_RED_SIGNATURE, pytrace=False)
    spec = importlib.util.spec_from_file_location(_OWNER_MODULE_NAME, owner_path)
    if spec is None or spec.loader is None:
        raise AssertionError("owner module spec or loader unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[_OWNER_MODULE_NAME] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(_OWNER_MODULE_NAME, None)
        raise
    return module


def _parameter_names(value: Any) -> tuple[str, ...]:
    return tuple(inspect.signature(value).parameters)


def _assert_owner_surface(owner: ModuleType) -> None:
    assert owner.R1_STRUCTURED_TERMINAL_EVENT_LEDGER_SCHEMA == _LEDGER_SCHEMA
    assert owner.R1_OUTER_TERMINAL_CAPTURE_ENVELOPE_SCHEMA == _ENVELOPE_SCHEMA
    assert tuple(owner.R1_STRUCTURED_TERMINAL_EVENT_SEMANTIC_CASE_IDS) == (
        _SEMANTIC_CASE_IDS
    )
    assert tuple(owner.R1_STRUCTURED_TERMINAL_EVENT_OUTER_CASE_IDS) == (
        _OUTER_CASE_IDS
    )
    assert issubclass(
        owner.R1StructuredTerminalEventContractRejected,
        Exception,
    )
    assert _parameter_names(
        owner.canonicalize_r1_structured_terminal_event_artifact
    ) == ("artifact",)
    assert _parameter_names(
        owner.build_r1_structured_pytest_semantic_ledger
    ) == (
        "collection",
        "pytest_reports",
        "d1_projection",
        "live_evidence",
        "expected_bindings",
        "semantic_write",
    )
    assert _parameter_names(
        owner.build_r1_outer_terminal_capture_envelope
    ) == (
        "semantic_ledger",
        "semantic_ledger_raw",
        "final_stdout",
        "final_stderr",
        "expected_bindings",
        "process_evidence",
        "outer_write",
    )
    assert _parameter_names(
        owner.validate_r1_structured_terminal_event_pair
    ) == ("pair",)
    assert _parameter_names(
        owner.write_r1_structured_terminal_event_artifact_exclusive
    ) == (
        "path",
        "raw",
        "file_mode",
        "parent_mode",
        "fsync_before_return",
    )
    plugin = owner.R1StructuredTerminalEventPytestPlugin
    assert _parameter_names(plugin) == (
        "expected_bindings",
        "semantic_write",
        "semantic_ledger_path",
        "live_evidence_provider",
    )
    for hook_name in (
        "pytest_collection_finish",
        "pytest_runtest_logreport",
        "pytest_sessionfinish",
        "finalize_structured_semantic_ledger",
    ):
        assert callable(getattr(plugin, hook_name))


def _assert_positive_fixture(pair: dict[str, Any]) -> None:
    ledger = pair["semantic_ledger"]
    projection = ledger["d1_projection"]
    envelope = pair["terminal_envelope"]
    assert set(pair) == {
        "semantic_ledger",
        "semantic_ledger_raw",
        "terminal_envelope",
        "terminal_envelope_raw",
        "final_stdout",
        "final_stderr",
        "expected_bindings",
        "live_evidence",
        "semantic_write",
        "process_evidence",
        "outer_write",
    }
    assert set(ledger) == _LEDGER_KEYS and len(ledger) == 17
    assert set(ledger["collection"]) == _COLLECTION_KEYS
    assert set(projection) == _PROJECTION_KEYS and len(projection) == 16
    assert len(projection["oracle_outcomes"]) == 8
    assert all(set(row) == {
        "node_id",
        "outcome",
        "causal_signature_id",
        "violation_class",
    } for row in projection["oracle_outcomes"])
    assert set(projection["equality_verdicts"]) == set(_EQUALITY_KEYS)
    assert all(projection["equality_verdicts"].values())
    assert projection["projection_sha256"] == _hash_without(
        projection,
        "projection_sha256",
    )
    assert len(ledger["pytest_reports"]) == 24
    assert all(set(row) == _REPORT_KEYS for row in ledger["pytest_reports"])
    assert set(ledger["session"]) == _SESSION_KEYS
    assert ledger["ledger_sha256"] == _hash_without(ledger, "ledger_sha256")
    assert pair["semantic_ledger_raw"] == _canonical_bytes(ledger) + b"\n"
    assert set(envelope) == _ENVELOPE_KEYS and len(envelope) == 31
    assert envelope["terminal_envelope_sha256"] == _hash_without(
        envelope,
        "terminal_envelope_sha256",
    )
    assert pair["terminal_envelope_raw"] == _canonical_bytes(envelope) + b"\n"
    assert envelope["semantic_ledger_logical_sha256"] == ledger[
        "ledger_sha256"
    ]
    assert envelope["semantic_ledger_raw_sha256"] == _sha256(
        pair["semantic_ledger_raw"]
    )
    assert envelope["semantic_ledger_byte_count"] == len(
        pair["semantic_ledger_raw"]
    )
    assert envelope["stdout_byte_count"] == len(pair["final_stdout"]) > 0
    assert envelope["stdout_sha256"] == _sha256(pair["final_stdout"])
    assert envelope["stderr_byte_count"] == len(pair["final_stderr"]) == 0
    assert envelope["stderr_sha256"] == _EMPTY_SHA256
    assert set(pair["expected_bindings"]) == _EXPECTED_BINDING_KEYS
    assert set(pair["live_evidence"]) == _LIVE_EVIDENCE_KEYS
    assert set(pair["semantic_write"]) == _SEMANTIC_WRITE_KEYS
    assert set(pair["process_evidence"]) == _PROCESS_EVIDENCE_KEYS
    assert set(pair["outer_write"]) == _OUTER_WRITE_KEYS
    preflight = pair["live_evidence"]["preflight"]
    observation = pair["live_evidence"]["observation"]
    closure = pair["live_evidence"]["closure"]
    assert preflight["preflight_sha256"] == _hash_without(
        preflight,
        "preflight_sha256",
    )
    assert observation["observation_sha256"] == _hash_without(
        observation,
        "observation_sha256",
    )
    assert closure["closure_sha256"] == _hash_without(
        closure,
        "closure_sha256",
    )
    assert projection["source_preflight_sha256"] == preflight[
        "preflight_sha256"
    ]
    assert projection["source_observation_sha256"] == observation[
        "observation_sha256"
    ]
    assert projection["source_closure_sha256"] == closure["closure_sha256"]
    assert (
        ledger["run_challenge_id"]
        == projection["run_challenge_id"]
        == preflight["run_challenge_id"]
        == observation["run_challenge_id"]
        == closure["run_challenge_id"]
        == envelope["run_challenge_id"]
    )
    for field in (
        "admission_sha256",
        "authority_token_sha256",
        "consumption_sha256",
        "fixed_source_identity_sha256",
        "launcher_contract_sha256",
        "runtime_identity_sha256",
        "single_use_key_sha256",
    ):
        assert ledger[field] == envelope[field] == pair["expected_bindings"][
            field
        ]
    assert ledger["collection"]["source_d1_blob_sha1"] == pair[
        "expected_bindings"
    ]["source_d1_blob_sha1"]
    assert envelope["postrun_identity_sha256"] == pair[
        "expected_bindings"
    ]["postrun_identity_sha256"]
    assert envelope["postrun_identity_sha256"] == pair["process_evidence"][
        "postrun_identity_sha256"
    ]
    for field in (
        "completed",
        "exit_code",
        "postrun_identity_all_equal",
        "postrun_identity_sha256",
        "postrun_source_clean",
        "process_group_reaped",
        "semantic_ledger_persistence_validated",
        "started",
        "timed_out",
    ):
        assert envelope[field] == pair["process_evidence"][field]


def _exercise_owner_plugin_and_writer(
    owner: ModuleType,
    baseline: dict[str, Any],
) -> None:
    def live_evidence_provider() -> dict[str, Any]:
        return {
            "d1_projection": copy.deepcopy(
                baseline["semantic_ledger"]["d1_projection"]
            ),
            "live_evidence": copy.deepcopy(baseline["live_evidence"]),
        }

    with tempfile.TemporaryDirectory(
        prefix="cocolon-r1-structured-terminal-"
    ) as temporary_parent_text:
        temporary_parent = Path(temporary_parent_text)
        temporary_parent.chmod(0o700)
        output_path = temporary_parent / "semantic-ledger.json"
        plugin = owner.R1StructuredTerminalEventPytestPlugin(
            expected_bindings=copy.deepcopy(baseline["expected_bindings"]),
            semantic_write=copy.deepcopy(baseline["semantic_write"]),
            semantic_ledger_path=output_path,
            live_evidence_provider=live_evidence_provider,
        )
        session = SimpleNamespace(
            items=[SimpleNamespace(nodeid=node_id) for node_id in _ORDERED_NODE_IDS],
            testscollected=8,
        )
        plugin.pytest_collection_finish(session)
        for row in baseline["semantic_ledger"]["pytest_reports"]:
            report = SimpleNamespace(
                nodeid=row["node_id"],
                when=row["phase"],
                outcome=row["outcome"],
                longrepr="FORBIDDEN_HUMAN_PRESENTATION_DIAGNOSTIC_ONLY",
                capstdout="FORBIDDEN_RAW_STDOUT_BODY",
                capstderr="FORBIDDEN_RAW_STDERR_BODY",
                wasxfail=None,
            )
            plugin.pytest_runtest_logreport(report)
        plugin.pytest_sessionfinish(session, 1)
        assert output_path.read_bytes() == baseline["semantic_ledger_raw"]
        assert output_path.stat().st_mode & 0o777 == 0o600
        assert temporary_parent.stat().st_mode & 0o777 == 0o700
        assert plugin.semantic_ledger == baseline["semantic_ledger"]
        assert plugin.semantic_ledger_raw == baseline["semantic_ledger_raw"]
        before_duplicate = output_path.read_bytes()
        with pytest.raises(FileExistsError):
            owner.write_r1_structured_terminal_event_artifact_exclusive(
                path=output_path,
                raw=baseline["semantic_ledger_raw"],
                file_mode="0600",
                parent_mode="0700",
                fsync_before_return=True,
            )
        assert output_path.read_bytes() == before_duplicate
        assert not any(
            key in plugin.semantic_ledger
            for key in ("stdout", "stderr", "stdout_body", "stderr_body")
        )


def _exercise_owner_plugin_negative_sequences(
    owner: ModuleType,
    baseline: dict[str, Any],
) -> None:
    canonical_reports = baseline["semantic_ledger"]["pytest_reports"]
    sequence_cases: tuple[
        tuple[str, str, list[str], list[dict[str, Any]]], ...
    ] = (
        (
            "PLUGIN_COLLECTION_MISSING",
            "COLLECTION_COUNT_MISSING_DUPLICATE_REORDER_UNKNOWN",
            list(_ORDERED_NODE_IDS[:-1]),
            copy.deepcopy(canonical_reports),
        ),
        (
            "PLUGIN_COLLECTION_DUPLICATE",
            "COLLECTION_COUNT_MISSING_DUPLICATE_REORDER_UNKNOWN",
            [*_ORDERED_NODE_IDS[:-1], _ORDERED_NODE_IDS[0]],
            copy.deepcopy(canonical_reports),
        ),
        (
            "PLUGIN_COLLECTION_REORDERED",
            "COLLECTION_COUNT_MISSING_DUPLICATE_REORDER_UNKNOWN",
            [
                _ORDERED_NODE_IDS[1],
                _ORDERED_NODE_IDS[0],
                *_ORDERED_NODE_IDS[2:],
            ],
            copy.deepcopy(canonical_reports),
        ),
        (
            "PLUGIN_COLLECTION_UNKNOWN",
            "COLLECTION_COUNT_MISSING_DUPLICATE_REORDER_UNKNOWN",
            ["ai/tests/unknown.py::test_unknown", *_ORDERED_NODE_IDS[1:]],
            copy.deepcopy(canonical_reports),
        ),
        (
            "PLUGIN_REPORT_MISSING",
            "REPORT_COUNT",
            list(_ORDERED_NODE_IDS),
            copy.deepcopy(canonical_reports[:-1]),
        ),
        (
            "PLUGIN_REPORT_DUPLICATE",
            "REPORT_COUNT",
            list(_ORDERED_NODE_IDS),
            [*copy.deepcopy(canonical_reports), copy.deepcopy(canonical_reports[0])],
        ),
        (
            "PLUGIN_REPORT_REORDERED",
            "REPORT_INDEX_MISSING_DUPLICATE_OR_RANGE",
            list(_ORDERED_NODE_IDS),
            [
                copy.deepcopy(canonical_reports[1]),
                copy.deepcopy(canonical_reports[0]),
                *copy.deepcopy(canonical_reports[2:]),
            ],
        ),
        (
            "PLUGIN_REPORT_UNKNOWN_NODE",
            "REPORT_INDEX_MISSING_DUPLICATE_OR_RANGE",
            list(_ORDERED_NODE_IDS),
            [
                {
                    **copy.deepcopy(canonical_reports[0]),
                    "node_id": "ai/tests/unknown.py::test_unknown",
                },
                *copy.deepcopy(canonical_reports[1:]),
            ],
        ),
        (
            "PLUGIN_REPORT_UNKNOWN_PHASE",
            "PHASE_ORDER",
            list(_ORDERED_NODE_IDS),
            [
                {
                    **copy.deepcopy(canonical_reports[0]),
                    "phase": "unknown",
                },
                *copy.deepcopy(canonical_reports[1:]),
            ],
        ),
    )
    assert len(sequence_cases) == 9
    assert len({case[0] for case in sequence_cases}) == 9

    def live_evidence_provider() -> dict[str, Any]:
        return {
            "d1_projection": copy.deepcopy(
                baseline["semantic_ledger"]["d1_projection"]
            ),
            "live_evidence": copy.deepcopy(baseline["live_evidence"]),
        }

    with tempfile.TemporaryDirectory(
        prefix="cocolon-r1-structured-terminal-negative-"
    ) as temporary_parent_text:
        temporary_parent = Path(temporary_parent_text)
        temporary_parent.chmod(0o700)
        for sequence_id, case_id, collected_nodes, reports in sequence_cases:
            output_path = temporary_parent / f"{sequence_id}.json"
            plugin = owner.R1StructuredTerminalEventPytestPlugin(
                expected_bindings=copy.deepcopy(
                    baseline["expected_bindings"]
                ),
                semantic_write=copy.deepcopy(baseline["semantic_write"]),
                semantic_ledger_path=output_path,
                live_evidence_provider=live_evidence_provider,
            )
            session = SimpleNamespace(
                items=[SimpleNamespace(nodeid=node_id) for node_id in collected_nodes],
                testscollected=len(collected_nodes),
            )
            with pytest.raises(
                owner.R1StructuredTerminalEventContractRejected
            ) as rejected:
                plugin.pytest_collection_finish(session)
                for row in reports:
                    plugin.pytest_runtest_logreport(
                        SimpleNamespace(
                            nodeid=row["node_id"],
                            when=row["phase"],
                            outcome=row["outcome"],
                            longrepr=(
                                "FORBIDDEN_HUMAN_PRESENTATION_DIAGNOSTIC_ONLY"
                            ),
                            capstdout="FORBIDDEN_RAW_STDOUT_BODY",
                            capstderr="FORBIDDEN_RAW_STDERR_BODY",
                            wasxfail=None,
                        )
                    )
                plugin.pytest_sessionfinish(session, 1)
            assert rejected.value.case_id == case_id, sequence_id
            assert not output_path.exists(), sequence_id


def test_r1_structured_terminal_event_owner_contract_or_red() -> None:
    d1_raw = (_REPO_ROOT / _D1_PATH).read_bytes()
    assert _sha256(d1_raw) == _D1_RAW_SHA256
    assert _git_blob_sha1(d1_raw) == _D1_BLOB_SHA1
    assert _sha256(_canonical_bytes(_ORDERED_NODE_IDS)) == (
        _ORDERED_NODE_LIST_SHA256
    )
    assert _sha256(_canonical_bytes(_projection_rows())) == (
        _RAW_PROJECTION_VECTOR_SHA256
    )
    assert _sha256(_canonical_bytes(_normalized_expected_rows())) == (
        _NORMALIZED_EXPECTED_VECTOR_SHA256
    )

    baseline = _valid_pair()
    _assert_positive_fixture(baseline)

    assert len(_SEMANTIC_CASE_IDS) == 24
    assert len(_OUTER_CASE_IDS) == 8
    assert len(_SEMANTIC_CASE_IDS + _OUTER_CASE_IDS) == 32
    assert len(set(_SEMANTIC_CASE_IDS)) == 24
    assert len(set(_OUTER_CASE_IDS)) == 8
    assert set(leaf["case_id"] for leaf in _SEMANTIC_LEAVES) == (
        set(_SEMANTIC_CASE_IDS) - {"OWNER_IMPLEMENTATION_ABSENT"}
    )
    assert set(leaf["case_id"] for leaf in _OUTER_LEAVES) == set(
        _OUTER_CASE_IDS
    )
    assert len(_SEMANTIC_LEAVES) >= 40
    assert len(_OUTER_LEAVES) >= 24
    assert len(_SEMANTIC_LEAVES) + len(_OUTER_LEAVES) >= 64
    assert len({leaf["leaf_id"] for leaf in _SEMANTIC_LEAVES}) == len(
        _SEMANTIC_LEAVES
    )
    assert len({leaf["leaf_id"] for leaf in _OUTER_LEAVES}) == len(
        _OUTER_LEAVES
    )

    frozen_leafs = _SEMANTIC_LEAVES + _OUTER_LEAVES
    for leaf in frozen_leafs:
        mutated = _mutated_pair(baseline, leaf)
        assert mutated != baseline, leaf["leaf_id"]
    _assert_positive_fixture(baseline)

    owner = _load_owner_or_red(_REPO_ROOT / _OWNER_PATH)
    assert not (
        _REPO_ROOT / "ai/tools/__r1_owner_intentionally_absent__.py"
    ).exists()
    _assert_owner_surface(owner)
    built_ledger, built_ledger_raw = (
        owner.build_r1_structured_pytest_semantic_ledger(
            collection=copy.deepcopy(baseline["semantic_ledger"]["collection"]),
            pytest_reports=copy.deepcopy(
                baseline["semantic_ledger"]["pytest_reports"]
            ),
            d1_projection=copy.deepcopy(
                baseline["semantic_ledger"]["d1_projection"]
            ),
            live_evidence=copy.deepcopy(baseline["live_evidence"]),
            expected_bindings=copy.deepcopy(baseline["expected_bindings"]),
            semantic_write=copy.deepcopy(baseline["semantic_write"]),
        )
    )
    assert built_ledger == baseline["semantic_ledger"]
    assert built_ledger_raw == baseline["semantic_ledger_raw"]
    built_envelope, built_envelope_raw = (
        owner.build_r1_outer_terminal_capture_envelope(
            semantic_ledger=copy.deepcopy(built_ledger),
            semantic_ledger_raw=built_ledger_raw,
            final_stdout=baseline["final_stdout"],
            final_stderr=baseline["final_stderr"],
            expected_bindings=copy.deepcopy(baseline["expected_bindings"]),
            process_evidence=copy.deepcopy(baseline["process_evidence"]),
            outer_write=copy.deepcopy(baseline["outer_write"]),
        )
    )
    assert built_envelope == baseline["terminal_envelope"]
    assert built_envelope_raw == baseline["terminal_envelope_raw"]
    assert owner.canonicalize_r1_structured_terminal_event_artifact(
        built_ledger
    ) == built_ledger_raw
    assert owner.canonicalize_r1_structured_terminal_event_artifact(
        built_envelope
    ) == built_envelope_raw
    _exercise_owner_plugin_and_writer(owner, baseline)
    _exercise_owner_plugin_negative_sequences(owner, baseline)

    validate = owner.validate_r1_structured_terminal_event_pair
    positive_input = copy.deepcopy(baseline)
    positive_before = copy.deepcopy(positive_input)
    positive_issues = validate(positive_input)
    assert type(positive_issues) is tuple
    assert positive_issues == ()
    assert positive_input == positive_before
    allowed_issues = (
        set(_SEMANTIC_CASE_IDS) | set(_OUTER_CASE_IDS)
    ) - {"OWNER_IMPLEMENTATION_ABSENT"}
    for leaf in _SEMANTIC_LEAVES:
        negative_input = _mutated_pair(baseline, leaf)
        negative_before = copy.deepcopy(negative_input)
        issues = validate(negative_input)
        assert type(issues) is tuple, leaf["leaf_id"]
        assert issues == (leaf["case_id"],), leaf["leaf_id"]
        assert set(issues) <= allowed_issues, leaf["leaf_id"]
        assert negative_input == negative_before, leaf["leaf_id"]
    for leaf in _OUTER_LEAVES:
        negative_input = _mutated_pair(baseline, leaf)
        negative_before = copy.deepcopy(negative_input)
        issues = validate(negative_input)
        assert type(issues) is tuple, leaf["leaf_id"]
        assert issues == (leaf["case_id"],), leaf["leaf_id"]
        assert set(issues) <= allowed_issues, leaf["leaf_id"]
        assert negative_input == negative_before, leaf["leaf_id"]
