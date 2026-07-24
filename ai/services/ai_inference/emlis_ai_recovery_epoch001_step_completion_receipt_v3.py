# -*- coding: utf-8 -*-
from __future__ import annotations

"""Fail-closed owner for future Recovery Epoch 001 step receipts.

The contract binds every Detailed Design section 22.1 element to current
repository bytes.  This module defines and validates candidates only; it does
not instantiate, persist, or accept a successful Step 0--10 receipt.
"""

import ast
from pathlib import Path
import re
import subprocess
from typing import Any, Mapping, Sequence

from emlis_ai_nls_v3_artifact_contract import artifact_sha256
from emlis_ai_recovery_epoch001_canonical_current_closure_v3 import (
    RECOVERY_EPOCH001_CANDIDATE_VERSION_ID,
    fresh_recovery_epoch001_canonical_current_closure,
)


RECOVERY_EPOCH001_CURRENT_STEP_COMPLETION_RECEIPT_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch001."
    "current_step_completion_receipt.v1"
)
RECOVERY_EPOCH001_PROVED_ISSUANCE_AUTHORIZED = False
RECOVERY_EPOCH001_NEXT_AUTHORITY_BY_STEP = {
    0: (
        "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_"
        "P1_STEP1_CURRENT_COMPLETION_PROOF_ONLY"
    ),
    1: (
        "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_"
        "P1_STEP2_CURRENT_COMPLETION_PROOF_ONLY"
    ),
    2: (
        "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_"
        "P1_STEP3_CURRENT_COMPLETION_PROOF_ONLY"
    ),
    3: (
        "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_"
        "P1_STEP4_SEMANTIC_INVENTORY_COMPLETION_VERIFICATION_ONLY"
    ),
    4: (
        "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_"
        "P1_STEP5_REFINED_CONTENT_SELECTION_COMPLETION_VERIFICATION_ONLY"
    ),
    5: (
        "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_"
        "P1_STEP6_DISCOURSE_GRAPH_COMPLETION_VERIFICATION_ONLY"
    ),
    6: (
        "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_"
        "P1_STEP7_TYPED_AST_RENDERER_COMPLETION_VERIFICATION_ONLY"
    ),
    7: (
        "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_"
        "P1_STEP8_BODY_ONLY_PARSER_MATCHER_COMPLETION_VERIFICATION_ONLY"
    ),
    8: (
        "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_"
        "P1_STEP9_STANDALONE_SUCCESSOR_COMPLETION_VERIFICATION_ONLY"
    ),
    9: (
        "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_"
        "P1_STEP10_SINGLE_GRAPH_DORMANT_INTEGRATION_COMPLETION_VERIFICATION_ONLY"
    ),
    10: (
        "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH001_"
        "P1_EXIT_TO_P2_SEPARATE_APPROVAL_ONLY"
    ),
}
RECOVERY_EPOCH001_CURRENT_STEP_COMPLETION_RECEIPT_NEGATIVE_CODES = frozenset(
    {
        "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_ENTRY_INVALID",
        "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_STEP_INVALID",
        "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_LINEAGE_INVALID",
        "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_HISTORICAL_REWRITE_FORBIDDEN",
        "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_HISTORICAL_AS_CURRENT_FORBIDDEN",
        "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_CURRENT_BINDING_INVALID",
        "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_ACTUAL_OWNER_BINDING_INVALID",
        "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_STRICT_CONTRACT_BINDING_INVALID",
        "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_POSITIVE_PROOF_INVALID",
        (
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_"
            "INDEPENDENT_NEGATIVE_PROOF_INVALID"
        ),
        "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_ARTIFACT_BINDING_INVALID",
        "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_PARENT_CHAIN_INVALID",
        (
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_"
            "SOURCE_OR_VIEW_ROOT_MISMATCH"
        ),
        "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_STOP_NOT_FALSE",
        "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_NEXT_AUTHORITY_INVALID",
        "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_VERDICT_INVALID",
        "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_BODY_FREE_REQUIRED",
        "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_HASH_MISMATCH",
    }
)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SHA_RE = re.compile(r"^[0-9a-f]{64}$")
_BLOB_RE = re.compile(r"^[0-9a-f]{40}$")
_MACHINE_RE = re.compile(r"^[A-Z][A-Z0-9_]{2,127}$")
_BODY_FREE_TOKEN_RE = re.compile(r"^[A-Za-z0-9_./:-]{1,512}$")
_VERDICTS = frozenset({"PROVED", "NOT_PROVED", "FAILED", "CONFLICT"})
_TOP_KEYS = frozenset(
    {
        "schema_version",
        "candidate_version_id",
        "step_number",
        "lineage",
        "current_binding",
        "actual_owners",
        "strict_contracts",
        "positive_proof",
        "independent_negative_proof",
        "artifact_receipt",
        "parent_binding",
        "completion_condition",
        "stop_conditions",
        "next_authority",
        "verdict",
        "body_free",
        "receipt_sha256",
    }
)
_LINEAGE_KEYS = frozenset(
    {
        "kind",
        "historical_disposition",
        "historical_rewrite",
        "historical_as_current",
        "backfill",
    }
)
_CURRENT_KEYS = frozenset(
    {
        "source_commit",
        "canonical_current_closure_sha256",
        "source_dependency_closure_sha256",
        "step_view_key",
        "step_view_sha256",
    }
)
_OWNER_KEYS = frozenset(
    {"path", "git_blob_sha1", "sha256", "symbol", "role"}
)
_CONTRACT_KEYS = frozenset(
    {
        "contract_id",
        "schema_version",
        "validator_path",
        "validator_blob_sha1",
        "validator_symbol",
        "invariant_ids",
    }
)
_PROOF_KEYS = frozenset(
    {
        "test_node_id",
        "result",
        "source_path",
        "source_blob_sha1",
        "source_sha256",
        "evidence_sha256",
    }
)
_ARTIFACT_KEYS = frozenset(
    {"path", "git_blob_sha1", "sha256", "schema_version", "body_free"}
)
_COMPLETION_KEYS = frozenset(
    {"condition_id", "required", "satisfied", "evidence_sha256"}
)
_STOP_KEYS = frozenset(
    {"condition_id", "triggered", "evidence_sha256"}
)


def _valid_sha(value: Any) -> bool:
    return type(value) is str and _SHA_RE.fullmatch(value) is not None


def _valid_blob(value: Any) -> bool:
    return type(value) is str and _BLOB_RE.fullmatch(value) is not None


def _valid_machine(value: Any) -> bool:
    return type(value) is str and _MACHINE_RE.fullmatch(value) is not None


def _file_rows(closure: Mapping[str, Any]) -> dict[str, dict[str, str]]:
    rows = closure.get("files")
    if type(rows) is not list:
        return {}
    return {
        row["path"]: row
        for row in rows
        if type(row) is dict
        and type(row.get("path")) is str
        and set(row) == {"path", "role", "sha256", "git_blob_sha1"}
    }


def _top_level_symbols(path: Path) -> set[str]:
    if path.suffix != ".py":
        return set()
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    symbols: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            symbols.add(node.name)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = (
                node.targets if isinstance(node, ast.Assign) else [node.target]
            )
            for target in targets:
                if isinstance(target, ast.Name):
                    symbols.add(target.id)
    return symbols


def _body_free(value: Any, active: set[int] | None = None) -> bool:
    if value is None or type(value) in (bool, int):
        return True
    if type(value) is str:
        return _BODY_FREE_TOKEN_RE.fullmatch(value) is not None
    if type(value) not in (list, dict):
        return False
    seen = set() if active is None else active
    identity = id(value)
    if identity in seen:
        return False
    seen.add(identity)
    try:
        if type(value) is list:
            return all(_body_free(item, seen) for item in value)
        for key, item in value.items():
            if type(key) is not str:
                return False
            if any(
                token in key.lower()
                for token in (
                    "raw_body",
                    "candidate_body",
                    "prompt_text",
                    "response_text",
                    "user_text",
                )
            ):
                return False
            if not _body_free(item, seen):
                return False
        return True
    finally:
        seen.remove(identity)


def _proof_valid(
    value: Any,
    *,
    files: Mapping[str, Mapping[str, str]],
    repo_root: Path,
    allowed_paths: frozenset[str],
    accepted_test_results: Mapping[str, Any] | None,
) -> bool:
    if type(value) is not dict or set(value) != _PROOF_KEYS:
        return False
    path = value.get("source_path")
    row = files.get(path) if type(path) is str else None
    node_id = value.get("test_node_id")
    if (
        row is None
        or path not in allowed_paths
        or row.get("role") == "immutable_historical_evidence"
        or value.get("result") != "PASSED"
        or value.get("source_blob_sha1") != row.get("git_blob_sha1")
        or value.get("source_sha256") != row.get("sha256")
        or not _valid_sha(value.get("evidence_sha256"))
        or type(node_id) is not str
        or not node_id.startswith(f"{path}::test_")
        or node_id.rpartition("::")[2] not in _top_level_symbols(
            repo_root / path
        )
        or type(accepted_test_results) is not dict
    ):
        return False
    accepted = accepted_test_results.get(node_id)
    return (
        type(accepted) is dict
        and accepted.get("result") == "PASSED"
        and accepted.get("evidence_sha256")
        == value.get("evidence_sha256")
    )


def _receipt_material(value: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value[key]
        for key in sorted(_TOP_KEYS - {"receipt_sha256"})
    }


def _validate_recovery_epoch001_current_step_completion_receipt_shape_impl(
    value: Any,
    *,
    repo_root: Path | None = None,
    previous_receipt: Mapping[str, Any] | None = None,
    step0_parent_authority: Mapping[str, Any] | None = None,
    accepted_test_results: Mapping[str, Any] | None = None,
) -> tuple[str, ...]:
    """Validate actual owners, tests, parent chain, STOPs, and current roots."""

    if type(value) is not dict:
        return ("RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_ENTRY_INVALID",)
    issues: set[str] = set()
    if set(value) != _TOP_KEYS:
        issues.add("RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_ENTRY_INVALID")
    root = (_REPO_ROOT if repo_root is None else Path(repo_root)).resolve()
    try:
        closure = fresh_recovery_epoch001_canonical_current_closure(
            repo_root=root
        )
    except (
        FileNotFoundError,
        KeyError,
        OSError,
        RecursionError,
        subprocess.SubprocessError,
        SyntaxError,
        UnicodeError,
        ValueError,
    ):
        closure = {}
    files = _file_rows(closure)
    step = value.get("step_number")
    valid_step = (
        type(step) is int
        and not isinstance(step, bool)
        and step in range(11)
    )
    if not valid_step:
        issues.add("RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_STEP_INVALID")
    if (
        value.get("schema_version")
        != RECOVERY_EPOCH001_CURRENT_STEP_COMPLETION_RECEIPT_SCHEMA
        or value.get("candidate_version_id")
        != RECOVERY_EPOCH001_CANDIDATE_VERSION_ID
    ):
        issues.add(
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_HISTORICAL_AS_CURRENT_FORBIDDEN"
        )
    lineage = value.get("lineage")
    if type(lineage) is not dict or set(lineage) != _LINEAGE_KEYS:
        issues.add("RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_LINEAGE_INVALID")
    else:
        if (
            lineage.get("kind") != "current"
            or lineage.get("historical_disposition")
            != "IMMUTABLE_NONCURRENT_EVIDENCE"
        ):
            issues.add(
                "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_LINEAGE_INVALID"
            )
        if (
            lineage.get("historical_rewrite") is not False
            or lineage.get("backfill") is not False
        ):
            issues.add(
                "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_HISTORICAL_REWRITE_FORBIDDEN"
            )
        if lineage.get("historical_as_current") is not False:
            issues.add(
                "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_HISTORICAL_AS_CURRENT_FORBIDDEN"
            )

    current = value.get("current_binding")
    step_key = f"step_{step}" if valid_step else None
    expected_view = (
        closure.get("step_views", {}).get(step_key)
        if type(closure.get("step_views")) is dict
        else None
    )
    expected_view_sha = (
        artifact_sha256(expected_view)
        if type(expected_view) is list
        else None
    )
    allowed_paths = frozenset(
        path for path in (expected_view or ()) if type(path) is str
    )
    if (
        type(current) is not dict
        or set(current) != _CURRENT_KEYS
        or current.get("source_commit") != closure.get("source_commit")
        or current.get("canonical_current_closure_sha256")
        != closure.get("canonical_current_closure_sha256")
        or current.get("source_dependency_closure_sha256")
        != closure.get("source_dependency_closure_sha256")
        or current.get("step_view_key") != step_key
        or current.get("step_view_sha256") != expected_view_sha
    ):
        issues.add(
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_CURRENT_BINDING_INVALID"
        )
        issues.add(
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_SOURCE_OR_VIEW_ROOT_MISMATCH"
        )

    owners = value.get("actual_owners")
    owner_paths: set[str] = set()
    if type(owners) is not list or not owners:
        issues.add(
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_ACTUAL_OWNER_BINDING_INVALID"
        )
    else:
        for owner in owners:
            path = owner.get("path") if type(owner) is dict else None
            row = files.get(path) if type(path) is str else None
            if (
                type(owner) is not dict
                or set(owner) != _OWNER_KEYS
                or row is None
                or path not in allowed_paths
                or row.get("role") == "immutable_historical_evidence"
                or path in owner_paths
                or owner.get("git_blob_sha1") != row.get("git_blob_sha1")
                or owner.get("sha256") != row.get("sha256")
                or owner.get("role") != row.get("role")
                or owner.get("symbol") not in _top_level_symbols(root / path)
            ):
                issues.add(
                    "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_ACTUAL_OWNER_BINDING_INVALID"
                )
            if type(path) is str:
                owner_paths.add(path)
        if all(type(item) is dict for item in owners) and owners != sorted(
            owners,
            key=lambda item: (
                str(item.get("path")),
                str(item.get("symbol")),
            ),
        ):
            issues.add(
                "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_ACTUAL_OWNER_BINDING_INVALID"
            )

    contracts = value.get("strict_contracts")
    contract_ids: set[str] = set()
    if type(contracts) is not list or not contracts:
        issues.add(
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_STRICT_CONTRACT_BINDING_INVALID"
        )
    else:
        for contract in contracts:
            path = (
                contract.get("validator_path")
                if type(contract) is dict
                else None
            )
            row = files.get(path) if type(path) is str else None
            contract_id = (
                contract.get("contract_id")
                if type(contract) is dict
                else None
            )
            invariants = (
                contract.get("invariant_ids")
                if type(contract) is dict
                else None
            )
            if (
                type(contract) is not dict
                or set(contract) != _CONTRACT_KEYS
                or row is None
                or path not in allowed_paths
                or row.get("role") == "immutable_historical_evidence"
                or contract.get("validator_blob_sha1")
                != row.get("git_blob_sha1")
                or contract.get("validator_symbol")
                not in _top_level_symbols(root / path)
                or type(contract_id) is not str
                or not _valid_machine(contract_id)
                or contract_id in contract_ids
                or type(contract.get("schema_version")) is not str
                or not contract.get("schema_version")
                or type(invariants) is not list
                or not invariants
                or any(not _valid_machine(item) for item in invariants)
                or invariants != sorted(invariants)
                or len(invariants) != len(set(invariants))
            ):
                issues.add(
                    "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_STRICT_CONTRACT_BINDING_INVALID"
                )
            if type(contract_id) is str:
                contract_ids.add(contract_id)
        if all(type(item) is dict for item in contracts) and contracts != sorted(
            contracts,
            key=lambda item: str(item.get("contract_id")),
        ):
            issues.add(
                "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_STRICT_CONTRACT_BINDING_INVALID"
            )

    positive = value.get("positive_proof")
    negative = value.get("independent_negative_proof")
    if not _proof_valid(
        positive,
        files=files,
        repo_root=root,
        allowed_paths=allowed_paths,
        accepted_test_results=accepted_test_results,
    ):
        issues.add(
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_POSITIVE_PROOF_INVALID"
        )
    if not _proof_valid(
        negative,
        files=files,
        repo_root=root,
        allowed_paths=allowed_paths,
        accepted_test_results=accepted_test_results,
    ) or (
        type(positive) is dict
        and type(negative) is dict
        and positive.get("source_path") == negative.get("source_path")
    ):
        issues.add(
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_"
            "INDEPENDENT_NEGATIVE_PROOF_INVALID"
        )

    artifact = value.get("artifact_receipt")
    artifact_path = (
        artifact.get("path") if type(artifact) is dict else None
    )
    artifact_row = (
        files.get(artifact_path) if type(artifact_path) is str else None
    )
    if (
        type(artifact) is not dict
        or set(artifact) != _ARTIFACT_KEYS
        or artifact_row is None
        or artifact_path not in allowed_paths
        or artifact_row.get("role") == "immutable_historical_evidence"
        or artifact.get("git_blob_sha1")
        != artifact_row.get("git_blob_sha1")
        or artifact.get("sha256") != artifact_row.get("sha256")
        or type(artifact.get("schema_version")) is not str
        or not artifact.get("schema_version")
        or artifact.get("body_free") is not True
    ):
        issues.add(
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_ARTIFACT_BINDING_INVALID"
        )

    parent = value.get("parent_binding")
    if step == 0:
        expected_parent_keys = {
            "kind",
            "detailed_design_sha256",
            "parent_receipt_path",
            "parent_receipt_git_blob_sha1",
            "parent_receipt_sha256",
            "canonical_current_closure_sha256",
        }
        parent_valid = (
            type(parent) is dict
            and set(parent) == expected_parent_keys
            and parent.get("kind") == "step0_design_parent"
            and _valid_sha(parent.get("detailed_design_sha256"))
            and _valid_blob(parent.get("parent_receipt_git_blob_sha1"))
            and _valid_sha(parent.get("parent_receipt_sha256"))
            and parent.get("canonical_current_closure_sha256")
            == closure.get("canonical_current_closure_sha256")
            and type(step0_parent_authority) is dict
            and parent == step0_parent_authority
        )
    elif valid_step:
        expected_parent_keys = {
            "kind",
            "previous_step",
            "previous_receipt_sha256",
            "source_commit",
            "canonical_current_closure_sha256",
        }
        parent_valid = (
            type(parent) is dict
            and set(parent) == expected_parent_keys
            and parent.get("kind") == "previous_current_step_receipt"
            and parent.get("previous_step") == step - 1
            and parent.get("source_commit") == closure.get("source_commit")
            and parent.get("canonical_current_closure_sha256")
            == closure.get("canonical_current_closure_sha256")
            and type(previous_receipt) is dict
            and set(previous_receipt) == _TOP_KEYS
            and previous_receipt.get("step_number") == step - 1
            and previous_receipt.get("verdict") == "PROVED"
            and type(previous_receipt.get("current_binding")) is dict
            and previous_receipt["current_binding"].get("source_commit")
            == closure.get("source_commit")
            and previous_receipt["current_binding"].get(
                "canonical_current_closure_sha256"
            )
            == closure.get("canonical_current_closure_sha256")
            and parent.get("previous_receipt_sha256")
            == previous_receipt.get("receipt_sha256")
            and _valid_sha(previous_receipt.get("receipt_sha256"))
        )
        if parent_valid:
            try:
                parent_valid = (
                    artifact_sha256(_receipt_material(previous_receipt))
                    == previous_receipt["receipt_sha256"]
                )
            except (
                KeyError,
                RecursionError,
                TypeError,
                UnicodeError,
                ValueError,
            ):
                parent_valid = False
    else:
        parent_valid = False
    if not parent_valid:
        issues.add(
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_PARENT_CHAIN_INVALID"
        )

    completion = value.get("completion_condition")
    completion_shape_invalid = (
        type(completion) is not dict
        or set(completion) != _COMPLETION_KEYS
        or not _valid_machine(completion.get("condition_id"))
        or completion.get("required") is not True
        or type(completion.get("satisfied")) is not bool
        or not _valid_sha(completion.get("evidence_sha256"))
    )
    if completion_shape_invalid:
        issues.add(
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_VERDICT_INVALID"
        )
    stops = value.get("stop_conditions")
    stop_shape_invalid = (
        type(stops) is not list
        or not stops
        or any(
            type(item) is not dict
            or set(item) != _STOP_KEYS
            or not _valid_machine(item.get("condition_id"))
            or type(item.get("triggered")) is not bool
            or not _valid_sha(item.get("evidence_sha256"))
            for item in (stops if type(stops) is list else ())
        )
    )
    if not stop_shape_invalid:
        stop_ids = [item["condition_id"] for item in stops]
        stop_shape_invalid = (
            stop_ids != sorted(stop_ids)
            or len(stop_ids) != len(set(stop_ids))
        )
    if stop_shape_invalid:
        issues.add(
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_STOP_NOT_FALSE"
        )
    verdict = value.get("verdict")
    if verdict not in _VERDICTS:
        issues.add("RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_VERDICT_INVALID")
    elif verdict == "PROVED":
        # Successful receipt issuance remains outside this authority.  A
        # later authority must add the immutable per-step requirement
        # registry and accepted-run receipt binding before this can open.
        issues.add("RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_VERDICT_INVALID")
        if (
            completion_shape_invalid
            or completion.get("satisfied") is not True
            or stop_shape_invalid
            or any(item["triggered"] is not False for item in stops)
        ):
            issues.add(
                "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_STOP_NOT_FALSE"
            )
    elif not completion_shape_invalid:
        if completion.get("satisfied") is not False:
            issues.add(
                "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_VERDICT_INVALID"
            )
        elif not stop_shape_invalid:
            triggered = [item["triggered"] for item in stops]
            if verdict == "NOT_PROVED" and any(triggered):
                issues.add(
                    "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_VERDICT_INVALID"
                )
            if verdict in {"FAILED", "CONFLICT"} and not any(triggered):
                issues.add(
                    "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_VERDICT_INVALID"
                )
    expected_next_authority = (
        RECOVERY_EPOCH001_NEXT_AUTHORITY_BY_STEP.get(step)
        if verdict == "PROVED" and valid_step
        else None
    )
    if value.get("next_authority") != expected_next_authority:
        issues.add(
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_NEXT_AUTHORITY_INVALID"
        )
    if value.get("body_free") is not True or not _body_free(value):
        issues.add(
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_BODY_FREE_REQUIRED"
        )
    try:
        expected_hash = artifact_sha256(_receipt_material(value))
    except (KeyError, RecursionError, TypeError, UnicodeError, ValueError):
        expected_hash = None
    if (
        expected_hash is None
        or value.get("receipt_sha256") != expected_hash
        or not _valid_sha(value.get("receipt_sha256"))
    ):
        issues.add("RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_HASH_MISMATCH")
    return tuple(sorted(issues))


def validate_recovery_epoch001_current_step_completion_receipt_shape(
    value: Any,
    *,
    repo_root: Path | None = None,
    previous_receipt: Mapping[str, Any] | None = None,
    step0_parent_authority: Mapping[str, Any] | None = None,
    accepted_test_results: Mapping[str, Any] | None = None,
) -> tuple[str, ...]:
    try:
        return _validate_recovery_epoch001_current_step_completion_receipt_shape_impl(
            value,
            repo_root=repo_root,
            previous_receipt=previous_receipt,
            step0_parent_authority=step0_parent_authority,
            accepted_test_results=accepted_test_results,
        )
    except (
        AttributeError,
        KeyError,
        OSError,
        RecursionError,
        subprocess.SubprocessError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        return ("RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_ENTRY_INVALID",)


def build_recovery_epoch001_current_step_completion_receipt(
    *,
    step_number: int,
    actual_owners: Sequence[Mapping[str, Any]],
    strict_contracts: Sequence[Mapping[str, Any]],
    positive_proof: Mapping[str, Any],
    independent_negative_proof: Mapping[str, Any],
    artifact_receipt: Mapping[str, Any],
    parent_binding: Mapping[str, Any],
    completion_condition: Mapping[str, Any],
    stop_conditions: Sequence[Mapping[str, Any]],
    verdict: str,
    repo_root: Path | None = None,
    previous_receipt: Mapping[str, Any] | None = None,
    step0_parent_authority: Mapping[str, Any] | None = None,
    accepted_test_results: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one candidate only after independently supplied proof authority."""

    if (
        verdict == "PROVED"
        and not RECOVERY_EPOCH001_PROVED_ISSUANCE_AUTHORIZED
    ):
        raise ValueError(
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_VERDICT_INVALID"
        )
    if (
        type(step_number) is not int
        or isinstance(step_number, bool)
        or step_number not in range(11)
        or verdict not in _VERDICTS
    ):
        raise ValueError(
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_STEP_INVALID"
        )
    if (
        any(type(item) is not dict for item in actual_owners)
        or any(type(item) is not dict for item in strict_contracts)
        or type(positive_proof) is not dict
        or type(independent_negative_proof) is not dict
        or type(artifact_receipt) is not dict
        or type(parent_binding) is not dict
        or type(completion_condition) is not dict
        or any(type(item) is not dict for item in stop_conditions)
    ):
        raise ValueError(
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_ENTRY_INVALID"
        )
    root = (_REPO_ROOT if repo_root is None else Path(repo_root)).resolve()
    closure = fresh_recovery_epoch001_canonical_current_closure(
        repo_root=root
    )
    step_key = f"step_{step_number}"
    current_binding = {
        "source_commit": closure["source_commit"],
        "canonical_current_closure_sha256": (
            closure["canonical_current_closure_sha256"]
        ),
        "source_dependency_closure_sha256": (
            closure["source_dependency_closure_sha256"]
        ),
        "step_view_key": step_key,
        "step_view_sha256": artifact_sha256(
            closure["step_views"].get(step_key)
        ),
    }
    receipt: dict[str, Any] = {
        "schema_version": (
            RECOVERY_EPOCH001_CURRENT_STEP_COMPLETION_RECEIPT_SCHEMA
        ),
        "candidate_version_id": RECOVERY_EPOCH001_CANDIDATE_VERSION_ID,
        "step_number": step_number,
        "lineage": {
            "kind": "current",
            "historical_disposition": "IMMUTABLE_NONCURRENT_EVIDENCE",
            "historical_rewrite": False,
            "historical_as_current": False,
            "backfill": False,
        },
        "current_binding": current_binding,
        "actual_owners": [dict(item) for item in actual_owners],
        "strict_contracts": [dict(item) for item in strict_contracts],
        "positive_proof": dict(positive_proof),
        "independent_negative_proof": dict(independent_negative_proof),
        "artifact_receipt": dict(artifact_receipt),
        "parent_binding": dict(parent_binding),
        "completion_condition": dict(completion_condition),
        "stop_conditions": [dict(item) for item in stop_conditions],
        "next_authority": None,
        "verdict": verdict,
        "body_free": True,
    }
    receipt["receipt_sha256"] = artifact_sha256(receipt)
    issues = validate_recovery_epoch001_current_step_completion_receipt_shape(
        receipt,
        repo_root=root,
        previous_receipt=previous_receipt,
        step0_parent_authority=step0_parent_authority,
        accepted_test_results=accepted_test_results,
    )
    if issues:
        raise ValueError(issues[0])
    return receipt
