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
from emlis_ai_recovery_epoch001_accepted_test_run_receipt_v3 import (
    RECOVERY_EPOCH001_ACCEPTED_TEST_RUN_RECEIPT_SCHEMA,
    validate_recovery_epoch001_accepted_test_run_receipt_shape,
)
from emlis_ai_recovery_epoch001_canonical_current_closure_v3 import (
    RECOVERY_EPOCH001_CANDIDATE_VERSION_ID,
    fresh_recovery_epoch001_canonical_current_closure,
)
from emlis_ai_recovery_epoch001_current_step_requirement_registry_v3 import (
    RECOVERY_EPOCH001_EXPECTED_FORMAL_NODE_REGISTRY_SHA256,
    fresh_recovery_epoch001_current_step_requirement_registry,
    validate_recovery_epoch001_current_step_requirement_registry_shape,
)


RECOVERY_EPOCH001_CURRENT_STEP_COMPLETION_RECEIPT_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch001."
    "current_step_completion_receipt.v1"
)
RECOVERY_EPOCH001_CURRENT_STEP_ARTIFACT_EVIDENCE_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch001."
    "current_step_artifact_evidence.v1"
)
RECOVERY_EPOCH001_PROVED_ISSUANCE_AUTHORIZED = True
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
_CURRENT_CLOSURE_CACHE: dict[
    tuple[str, str, str],
    Mapping[str, Any],
] = {}


def _current_closure(root: Path) -> Mapping[str, Any]:
    source_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        timeout=5,
    ).stdout.strip()
    source_tree = subprocess.run(
        ["git", "rev-parse", "HEAD^{tree}"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        timeout=5,
    ).stdout.strip()
    key = (str(root), source_commit, source_tree)
    closure = _CURRENT_CLOSURE_CACHE.get(key)
    if closure is None:
        closure = fresh_recovery_epoch001_canonical_current_closure(
            repo_root=root
        )
        _CURRENT_CLOSURE_CACHE.clear()
        _CURRENT_CLOSURE_CACHE[key] = closure
    return closure
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
        "source_tree",
        "source_baseline_event_sha256",
        "canonical_current_closure_sha256",
        "source_dependency_closure_sha256",
        "full_graph_sha256",
        "step_view_key",
        "step_view_sha256",
        "requirement_registry_sha256",
        "formal_node_registry_sha256",
        "accepted_test_run_receipt_sha256",
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
    {
        "schema_version",
        "step_number",
        "required_artifact_schema_version",
        "owner_binding_sha256",
        "strict_contract_binding_sha256",
        "requirement_registry_sha256",
        "accepted_test_run_receipt_sha256",
        "formal_completion_evidence_sha256",
        "body_free",
    }
)
_COMPLETION_KEYS = frozenset(
    {"condition_id", "required", "satisfied", "evidence_sha256"}
)
_STOP_KEYS = frozenset(
    {
        "condition_id",
        "proof_scope",
        "proof_node_registry_sha256",
        "accepted_test_run_receipt_sha256",
        "triggered",
        "evidence_sha256",
    }
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


def _strict_contract_symbol_resolves(
    *,
    path: str,
    symbol: str,
    symbols: set[str],
) -> bool:
    if symbol in symbols:
        return True
    return (
        path
        == "ai/services/ai_inference/emlis_ai_content_selection_v3.py"
        and symbol == "validate_content_selection_plan"
        and "validate_content_selection_policy" in symbols
    )


def _body_free(value: Any, active: set[int] | None = None) -> bool:
    if value is None or type(value) in (bool, int):
        return True
    if type(value) is str:
        return (
            0 < len(value) <= 4096
            and not any(ord(character) < 32 for character in value)
        )
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


def _receipt_material(value: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: value[key]
        for key in sorted(_TOP_KEYS - {"receipt_sha256"})
    }


def _accepted_attempt(
    accepted_test_run_receipt: Mapping[str, Any],
) -> Mapping[str, Any]:
    attempt = accepted_test_run_receipt.get("formal_test_run_attempt")
    return attempt if type(attempt) is dict else accepted_test_run_receipt


def _accepted_source(
    accepted_test_run_receipt: Mapping[str, Any],
    key: str,
) -> Any:
    attempt = _accepted_attempt(accepted_test_run_receipt)
    closure = attempt.get("source_closure")
    event = attempt.get("source_baseline_event")
    if type(closure) is not dict:
        closure = {}
    if type(event) is not dict:
        event = {}
    mapping = {
        "source_commit": closure.get("source_commit_sha1"),
        "source_tree": closure.get("source_tree_sha1"),
        "source_baseline_event_sha256": event.get("event_sha256"),
        "canonical_current_closure_sha256": closure.get(
            "canonical_current_closure_sha256"
        ),
        "source_dependency_closure_sha256": closure.get(
            "source_dependency_closure_sha256"
        ),
        "registry_sha256": closure.get("requirement_registry_sha256"),
        "formal_node_registry_sha256": closure.get(
            "formal_node_registry_sha256"
        ),
    }
    legacy = accepted_test_run_receipt.get(key)
    return legacy if legacy is not None else mapping.get(key)


def _accepted_outcomes(
    accepted_test_run_receipt: Mapping[str, Any],
) -> dict[str, Mapping[str, Any]]:
    outcomes = _accepted_attempt(accepted_test_run_receipt).get("outcomes")
    if type(outcomes) is not list:
        return {}
    return {
        row["test_node_id"]: row
        for row in outcomes
        if type(row) is dict and type(row.get("test_node_id")) is str
    }


def _proof_from_outcome(
    *,
    proof: Mapping[str, Any],
    outcomes: Mapping[str, Mapping[str, Any]],
    files: Mapping[str, Mapping[str, str]],
    allowed_paths: frozenset[str],
) -> dict[str, Any] | None:
    node_id = proof.get("test_node_id")
    source_path = proof.get("source_path")
    outcome = outcomes.get(node_id) if type(node_id) is str else None
    source_row = (
        files.get(source_path) if type(source_path) is str else None
    )
    if (
        type(outcome) is not dict
        or source_row is None
        or source_path not in allowed_paths
        or outcome.get("test_node_id") != node_id
        or outcome.get("source_path") != source_path
        or outcome.get("source_blob_sha1")
        != source_row.get("git_blob_sha1")
        or outcome.get("source_sha256") != source_row.get("sha256")
        or outcome.get("result") != "PASSED"
        or not _valid_sha(outcome.get("evidence_sha256"))
    ):
        return None
    return {
        "test_node_id": node_id,
        "result": "PASSED",
        "source_path": source_path,
        "source_blob_sha1": source_row["git_blob_sha1"],
        "source_sha256": source_row["sha256"],
        "evidence_sha256": outcome["evidence_sha256"],
    }


def _formal_run_complete(
    accepted_test_run_receipt: Mapping[str, Any],
    formal_nodes: Sequence[str],
) -> bool:
    outcomes = _accepted_outcomes(accepted_test_run_receipt)
    attempt = _accepted_attempt(accepted_test_run_receipt)
    counts = attempt.get("counts")
    return (
        accepted_test_run_receipt.get("accepted") is True
        and type(counts) is dict
        and counts
        == {
            "collected": 134,
            "executed": 134,
            "passed": 134,
            "failed": 0,
            "skipped": 0,
            "xfailed": 0,
            "xpassed": 0,
            "deselected": 0,
            "collection_errors": 0,
            "timeouts": 0,
        }
        and attempt.get("exit_code") == 0
        and attempt.get("timed_out") is False
        and attempt.get("outcome_state", "SUCCEEDED") == "SUCCEEDED"
        and attempt.get("stop_code") is None
        and all(
            node in outcomes and outcomes[node].get("result") == "PASSED"
            for node in formal_nodes
        )
    )


def _global_stop_condition_ids(
    registry: Mapping[str, Any],
) -> frozenset[str]:
    rows = registry.get("steps")
    if type(rows) is not list or not rows:
        return frozenset()
    stop_sets = [
        {
            condition_id
            for condition_id in row.get("stop_condition_ids", [])
            if type(condition_id) is str
        }
        for row in rows
        if type(row) is dict
    ]
    if len(stop_sets) != len(rows) or not stop_sets:
        return frozenset()
    return frozenset.intersection(*(frozenset(items) for items in stop_sets))


def _stop_material(
    *,
    condition_id: str,
    step_nodes: list[str],
    all_nodes: list[str],
    global_stop_ids: frozenset[str],
    outcomes: Mapping[str, Mapping[str, Any]],
    accepted_hash: str,
) -> dict[str, Any] | None:
    proof_nodes = all_nodes if condition_id in global_stop_ids else step_nodes
    if (
        not proof_nodes
        or any(
            node not in outcomes
            or outcomes[node].get("result") != "PASSED"
            for node in proof_nodes
        )
    ):
        return None
    proof_scope = (
        "GLOBAL_EXACT134"
        if condition_id in global_stop_ids
        else "STEP_EXACT_REQUIRED_NODES"
    )
    proof_node_registry_sha256 = artifact_sha256(
        {"node_ids": proof_nodes}
    )
    evidence_material = {
        "condition_id": condition_id,
        "proof_scope": proof_scope,
        "proof_node_registry_sha256": proof_node_registry_sha256,
        "outcome_evidence_sha256s": [
            outcomes[node]["evidence_sha256"] for node in proof_nodes
        ],
        "accepted_test_run_receipt_sha256": accepted_hash,
        "triggered": False,
    }
    return {
        "condition_id": condition_id,
        "proof_scope": proof_scope,
        "proof_node_registry_sha256": proof_node_registry_sha256,
        "accepted_test_run_receipt_sha256": accepted_hash,
        "triggered": False,
        "evidence_sha256": artifact_sha256(evidence_material),
    }


def _expected_step_material(
    *,
    step_number: int,
    registry: Mapping[str, Any],
    accepted_test_run_receipt: Mapping[str, Any],
    closure: Mapping[str, Any],
) -> dict[str, Any] | None:
    rows = registry.get("steps")
    if type(rows) is not list or step_number not in range(len(rows)):
        return None
    row = rows[step_number]
    if type(row) is not dict or row.get("step_number") != step_number:
        return None
    files = _file_rows(closure)
    step_key = f"step_{step_number}"
    step_view = closure.get("step_views", {}).get(step_key)
    if type(step_view) is not list:
        return None
    allowed_paths = frozenset(
        path for path in step_view if type(path) is str
    )
    outcomes = _accepted_outcomes(accepted_test_run_receipt)
    formal_nodes = row.get("formal_completion_node_ids")
    all_formal_nodes = [
        node
        for registry_row in rows
        if type(registry_row) is dict
        for node in registry_row.get("formal_completion_node_ids", [])
        if type(node) is str
    ]
    if (
        type(formal_nodes) is not list
        or len(all_formal_nodes) != 134
        or not _formal_run_complete(
            accepted_test_run_receipt,
            all_formal_nodes,
        )
    ):
        return None
    owners: list[dict[str, Any]] = []
    for owner in row.get("actual_owners", []):
        path = owner.get("path") if type(owner) is dict else None
        source_row = files.get(path) if type(path) is str else None
        if (
            source_row is None
            or path not in allowed_paths
            or owner.get("symbol") not in _top_level_symbols(
                Path(closure["_repo_root"]) / path
            )
        ):
            return None
        owners.append(
            {
                "path": path,
                "git_blob_sha1": source_row["git_blob_sha1"],
                "sha256": source_row["sha256"],
                "symbol": owner["symbol"],
                "role": owner["role"],
            }
        )
    contracts: list[dict[str, Any]] = []
    for contract in row.get("strict_contracts", []):
        path = (
            contract.get("validator_path")
            if type(contract) is dict
            else None
        )
        source_row = files.get(path) if type(path) is str else None
        if source_row is None or path not in allowed_paths:
            return None
        if not _strict_contract_symbol_resolves(
            path=path,
            symbol=str(contract.get("validator_symbol")),
            symbols=_top_level_symbols(
                Path(closure["_repo_root"]) / path
            ),
        ):
            return None
        contracts.append(
            {
                "contract_id": contract["contract_id"],
                "schema_version": contract["schema_version"],
                "validator_path": path,
                "validator_blob_sha1": source_row["git_blob_sha1"],
                "validator_symbol": contract["validator_symbol"],
                "invariant_ids": list(contract["invariant_ids"]),
            }
        )
    positive = _proof_from_outcome(
        proof=row["positive_proof"],
        outcomes=outcomes,
        files=files,
        allowed_paths=allowed_paths,
    )
    negative = _proof_from_outcome(
        proof=row["independent_negative_proof"],
        outcomes=outcomes,
        files=files,
        allowed_paths=allowed_paths,
    )
    if positive is None or negative is None:
        return None
    negative_registry = row["independent_negative_proof"]
    negative_outcome = outcomes.get(negative_registry["test_node_id"])
    if (
        type(negative_outcome) is not dict
        or negative_outcome.get("expected_closed_code")
        != negative_registry["expected_closed_code"]
        or negative_outcome.get("actual_closed_code")
        != negative_registry["expected_closed_code"]
    ):
        return None
    accepted_hash = accepted_test_run_receipt[
        "accepted_test_run_receipt_sha256"
    ]
    evidence_hashes = [
        outcomes[node]["evidence_sha256"] for node in formal_nodes
    ]
    formal_evidence_sha256 = artifact_sha256(
        {
            "step_number": step_number,
            "formal_node_ids": formal_nodes,
            "outcome_evidence_sha256s": evidence_hashes,
            "accepted_test_run_receipt_sha256": accepted_hash,
        }
    )
    current_binding = {
        "source_commit": closure["source_commit"],
        "source_tree": _accepted_source(
            accepted_test_run_receipt,
            "source_tree",
        ),
        "source_baseline_event_sha256": _accepted_source(
            accepted_test_run_receipt,
            "source_baseline_event_sha256",
        ),
        "canonical_current_closure_sha256": (
            closure["canonical_current_closure_sha256"]
        ),
        "source_dependency_closure_sha256": (
            closure["source_dependency_closure_sha256"]
        ),
        "full_graph_sha256": closure["full_graph_sha256"],
        "step_view_key": step_key,
        "step_view_sha256": artifact_sha256(step_view),
        "requirement_registry_sha256": registry["registry_sha256"],
        "formal_node_registry_sha256": (
            RECOVERY_EPOCH001_EXPECTED_FORMAL_NODE_REGISTRY_SHA256
        ),
        "accepted_test_run_receipt_sha256": accepted_hash,
    }
    artifact_receipt = {
        "schema_version": (
            RECOVERY_EPOCH001_CURRENT_STEP_ARTIFACT_EVIDENCE_SCHEMA
        ),
        "step_number": step_number,
        "required_artifact_schema_version": (
            row["artifact_receipt_schema_version"]
        ),
        "owner_binding_sha256": artifact_sha256(owners),
        "strict_contract_binding_sha256": artifact_sha256(contracts),
        "requirement_registry_sha256": registry["registry_sha256"],
        "accepted_test_run_receipt_sha256": accepted_hash,
        "formal_completion_evidence_sha256": formal_evidence_sha256,
        "body_free": True,
    }
    completion = {
        "condition_id": row["completion_condition_ids"][0],
        "required": True,
        "satisfied": True,
        "evidence_sha256": formal_evidence_sha256,
    }
    global_stop_ids = _global_stop_condition_ids(registry)
    stops = [
        _stop_material(
            condition_id=condition_id,
            step_nodes=formal_nodes,
            all_nodes=all_formal_nodes,
            global_stop_ids=global_stop_ids,
            outcomes=outcomes,
            accepted_hash=accepted_hash,
        )
        for condition_id in row["stop_condition_ids"]
    ]
    if any(stop is None for stop in stops):
        return None
    return {
        "row": row,
        "current_binding": current_binding,
        "actual_owners": owners,
        "strict_contracts": contracts,
        "positive_proof": positive,
        "independent_negative_proof": negative,
        "artifact_receipt": artifact_receipt,
        "completion_condition": completion,
        "stop_conditions": [stop for stop in stops if stop is not None],
    }


def _step0_parent_binding(
    event: Mapping[str, Any],
    accepted_test_run_receipt: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "kind": "source_baseline_locked_event_1",
        "event_name": "SOURCE_BASELINE_LOCKED",
        "event_ordinal": 1,
        "source_baseline_event_sha256": event["event_sha256"],
        "source_commit": _accepted_source(
            accepted_test_run_receipt,
            "source_commit",
        ),
        "source_tree": _accepted_source(
            accepted_test_run_receipt,
            "source_tree",
        ),
        "canonical_current_closure_sha256": _accepted_source(
            accepted_test_run_receipt,
            "canonical_current_closure_sha256",
        ),
    }


def _later_parent_binding(
    *,
    step_number: int,
    previous_receipt: Mapping[str, Any],
    accepted_test_run_receipt: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "kind": "previous_current_step_receipt",
        "previous_step": step_number - 1,
        "previous_receipt_sha256": previous_receipt["receipt_sha256"],
        "source_commit": _accepted_source(
            accepted_test_run_receipt,
            "source_commit",
        ),
        "source_tree": _accepted_source(
            accepted_test_run_receipt,
            "source_tree",
        ),
        "source_baseline_event_sha256": _accepted_source(
            accepted_test_run_receipt,
            "source_baseline_event_sha256",
        ),
        "canonical_current_closure_sha256": _accepted_source(
            accepted_test_run_receipt,
            "canonical_current_closure_sha256",
        ),
    }


def _valid_previous_receipt(
    value: Any,
    *,
    expected_step: int,
    accepted_test_run_receipt: Mapping[str, Any],
) -> bool:
    if (
        type(value) is not dict
        or set(value) != _TOP_KEYS
        or value.get("step_number") != expected_step
        or value.get("verdict") != "PROVED"
        or value.get("body_free") is not True
        or type(value.get("current_binding")) is not dict
        or value["current_binding"].get("source_commit")
        != _accepted_source(accepted_test_run_receipt, "source_commit")
        or value["current_binding"].get("source_tree")
        != _accepted_source(accepted_test_run_receipt, "source_tree")
        or value["current_binding"].get("source_baseline_event_sha256")
        != _accepted_source(
            accepted_test_run_receipt,
            "source_baseline_event_sha256",
        )
        or value["current_binding"].get(
            "accepted_test_run_receipt_sha256"
        )
        != accepted_test_run_receipt.get(
            "accepted_test_run_receipt_sha256"
        )
        or not _valid_sha(value.get("receipt_sha256"))
    ):
        return False
    try:
        return (
            artifact_sha256(_receipt_material(value))
            == value["receipt_sha256"]
        )
    except (
        KeyError,
        RecursionError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        return False


def _valid_prior_receipt_chain(
    values: Any,
    *,
    step_number: int,
    previous_receipt: Mapping[str, Any] | None,
    repo_root: Path,
    step0_parent_authority: Mapping[str, Any],
    requirement_registry: Mapping[str, Any],
    accepted_test_run_receipt: Mapping[str, Any],
    publication_evidence: Mapping[str, Any] | None = None,
    registry_issues: Sequence[str] | None = None,
    accepted_issues: Sequence[str] | None = None,
    closure: Mapping[str, Any] | None = None,
) -> bool:
    if type(values) not in (list, tuple) or len(values) != step_number:
        return False
    chain = [dict(item) for item in values if type(item) is dict]
    if len(chain) != step_number:
        return False
    if step_number > 0 and (
        type(previous_receipt) is not dict
        or chain[-1] != dict(previous_receipt)
    ):
        return False
    for index, receipt in enumerate(chain):
        issues = (
            _validate_recovery_epoch001_current_step_completion_receipt_shape_impl(
                receipt,
                repo_root=repo_root,
                previous_receipt=(chain[index - 1] if index else None),
                step0_parent_authority=step0_parent_authority,
                requirement_registry=requirement_registry,
                accepted_test_run_receipt=accepted_test_run_receipt,
                publication_evidence=publication_evidence,
                prior_receipts=chain[:index],
                _prior_chain_validated=True,
                _registry_issues=registry_issues,
                _accepted_issues=accepted_issues,
                _closure_override=closure,
            )
        )
        if issues:
            return False
    return True


def _validate_recovery_epoch001_current_step_completion_receipt_shape_impl(
    value: Any,
    *,
    repo_root: Path | None = None,
    previous_receipt: Mapping[str, Any] | None = None,
    step0_parent_authority: Mapping[str, Any] | None = None,
    requirement_registry: Mapping[str, Any] | None = None,
    accepted_test_run_receipt: Mapping[str, Any] | None = None,
    publication_evidence: Mapping[str, Any] | None = None,
    prior_receipts: Sequence[Mapping[str, Any]] | None = None,
    _prior_chain_validated: bool = False,
    _registry_issues: Sequence[str] | None = None,
    _accepted_issues: Sequence[str] | None = None,
    _closure_override: Mapping[str, Any] | None = None,
) -> tuple[str, ...]:
    if type(value) is not dict:
        return ("RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_ENTRY_INVALID",)
    issues: set[str] = set()
    if set(value) != _TOP_KEYS:
        issues.add("RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_ENTRY_INVALID")
    root = (_REPO_ROOT if repo_root is None else Path(repo_root)).resolve()
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
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_"
            "HISTORICAL_AS_CURRENT_FORBIDDEN"
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
                "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_"
                "HISTORICAL_REWRITE_FORBIDDEN"
            )
        if lineage.get("historical_as_current") is not False:
            issues.add(
                "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_"
                "HISTORICAL_AS_CURRENT_FORBIDDEN"
            )

    registry = (
        fresh_recovery_epoch001_current_step_requirement_registry()
        if requirement_registry is None
        else dict(requirement_registry)
    )
    registry_issues = (
        tuple(_registry_issues)
        if _registry_issues is not None
        else validate_recovery_epoch001_current_step_requirement_registry_shape(
            registry,
            repo_root=root,
        )
    )
    event = (
        dict(step0_parent_authority)
        if type(step0_parent_authority) is dict
        else {}
    )
    accepted = (
        dict(accepted_test_run_receipt)
        if type(accepted_test_run_receipt) is dict
        else {}
    )
    if _accepted_issues is not None:
        accepted_issues = tuple(_accepted_issues)
    else:
        try:
            accepted_issues = (
                validate_recovery_epoch001_accepted_test_run_receipt_shape(
                    accepted,
                    requirement_registry=registry,
                    source_baseline_event=event,
                    publication_evidence=publication_evidence,
                    repo_root=root,
                )
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
            accepted_issues = (
                "RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_ENTRY_INVALID",
            )
    try:
        closure = (
            dict(_closure_override)
            if _closure_override is not None
            else dict(_current_closure(root))
        )
        closure["_repo_root"] = str(root)
    except (
        FileNotFoundError,
        KeyError,
        OSError,
        subprocess.SubprocessError,
        SyntaxError,
        UnicodeError,
        ValueError,
    ):
        closure = {}
    expected = (
        _expected_step_material(
            step_number=step,
            registry=registry,
            accepted_test_run_receipt=accepted,
            closure=closure,
        )
        if valid_step
        and not registry_issues
        and not accepted_issues
        and closure
        else None
    )
    issuance_valid = (
        RECOVERY_EPOCH001_PROVED_ISSUANCE_AUTHORIZED is True
        and expected is not None
    )

    if (
        expected is None
        or value.get("current_binding") != expected["current_binding"]
    ):
        issues.add(
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_CURRENT_BINDING_INVALID"
        )
        issues.add(
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_"
            "SOURCE_OR_VIEW_ROOT_MISMATCH"
        )
    owners = value.get("actual_owners")
    if (
        expected is None
        or owners != expected["actual_owners"]
        or type(owners) is not list
        or any(
            type(owner) is not dict or set(owner) != _OWNER_KEYS
            for owner in (owners if type(owners) is list else ())
        )
    ):
        issues.add(
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_"
            "ACTUAL_OWNER_BINDING_INVALID"
        )
    contracts = value.get("strict_contracts")
    if (
        expected is None
        or contracts != expected["strict_contracts"]
        or type(contracts) is not list
        or any(
            type(contract) is not dict
            or set(contract) != _CONTRACT_KEYS
            or type(contract.get("invariant_ids")) is not list
            or any(
                not _valid_machine(item)
                for item in (
                    contract.get("invariant_ids", [])
                    if type(contract.get("invariant_ids")) is list
                    else ()
                )
            )
            for contract in (
                contracts if type(contracts) is list else ()
            )
        )
    ):
        issues.add(
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_"
            "STRICT_CONTRACT_BINDING_INVALID"
        )
    positive = value.get("positive_proof")
    if (
        expected is None
        or positive != expected["positive_proof"]
        or type(positive) is not dict
        or set(positive) != _PROOF_KEYS
    ):
        issues.add(
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_"
            "POSITIVE_PROOF_INVALID"
        )
    negative = value.get("independent_negative_proof")
    if (
        expected is None
        or negative != expected["independent_negative_proof"]
        or type(negative) is not dict
        or set(negative) != _PROOF_KEYS
        or (
            type(positive) is dict
            and positive.get("source_path") == negative.get("source_path")
        )
    ):
        issues.add(
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_"
            "INDEPENDENT_NEGATIVE_PROOF_INVALID"
        )
    artifact = value.get("artifact_receipt")
    if (
        expected is None
        or artifact != expected["artifact_receipt"]
        or type(artifact) is not dict
        or set(artifact) != _ARTIFACT_KEYS
        or artifact.get("body_free") is not True
    ):
        issues.add(
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_"
            "ARTIFACT_BINDING_INVALID"
        )

    parent = value.get("parent_binding")
    if step == 0 and issuance_valid:
        expected_parent = _step0_parent_binding(event, accepted)
        parent_valid = (
            parent == expected_parent
            and (
                prior_receipts is None
                or (
                    type(prior_receipts) in (list, tuple)
                    and len(prior_receipts) == 0
                )
            )
        )
    elif valid_step and step > 0 and issuance_valid:
        immediate_parent_valid = _valid_previous_receipt(
            previous_receipt,
            expected_step=step - 1,
            accepted_test_run_receipt=accepted,
        )
        chain_valid = (
            True
            if _prior_chain_validated
            else _valid_prior_receipt_chain(
                prior_receipts,
                step_number=step,
                previous_receipt=previous_receipt,
                repo_root=root,
                step0_parent_authority=event,
                requirement_registry=registry,
                accepted_test_run_receipt=accepted,
                publication_evidence=publication_evidence,
                registry_issues=registry_issues,
                accepted_issues=accepted_issues,
                closure=closure,
            )
        )
        parent_valid = immediate_parent_valid and chain_valid
        expected_parent = (
            _later_parent_binding(
                step_number=step,
                previous_receipt=previous_receipt,
                accepted_test_run_receipt=accepted,
            )
            if parent_valid and type(previous_receipt) is dict
            else None
        )
        parent_valid = parent_valid and parent == expected_parent
    else:
        parent_valid = False
    if not parent_valid:
        issues.add(
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_PARENT_CHAIN_INVALID"
        )

    completion = value.get("completion_condition")
    if (
        expected is None
        or completion != expected["completion_condition"]
        or type(completion) is not dict
        or set(completion) != _COMPLETION_KEYS
        or completion.get("required") is not True
        or completion.get("satisfied") is not True
    ):
        issues.add(
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_VERDICT_INVALID"
        )
    stops = value.get("stop_conditions")
    if (
        expected is None
        or stops != expected["stop_conditions"]
        or type(stops) is not list
        or not stops
        or any(
            type(item) is not dict
            or set(item) != _STOP_KEYS
            or item.get("triggered") is not False
            for item in (stops if type(stops) is list else ())
        )
    ):
        issues.add(
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_STOP_NOT_FALSE"
        )
    if (
        expected is None
        or value.get("next_authority")
        != expected["row"]["next_authority"]
    ):
        issues.add(
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_NEXT_AUTHORITY_INVALID"
        )
    if value.get("verdict") != "PROVED" or not issuance_valid:
        issues.add(
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_VERDICT_INVALID"
        )
    if value.get("body_free") is not True or not _body_free(value):
        issues.add(
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_BODY_FREE_REQUIRED"
        )
    try:
        expected_hash = artifact_sha256(_receipt_material(value))
    except (
        KeyError,
        RecursionError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
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
    requirement_registry: Mapping[str, Any] | None = None,
    accepted_test_run_receipt: Mapping[str, Any] | None = None,
    publication_evidence: Mapping[str, Any] | None = None,
    prior_receipts: Sequence[Mapping[str, Any]] | None = None,
) -> tuple[str, ...]:
    try:
        return (
            _validate_recovery_epoch001_current_step_completion_receipt_shape_impl(
                value,
                repo_root=repo_root,
                previous_receipt=previous_receipt,
                step0_parent_authority=step0_parent_authority,
                requirement_registry=requirement_registry,
                accepted_test_run_receipt=accepted_test_run_receipt,
                publication_evidence=publication_evidence,
                prior_receipts=prior_receipts,
            )
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
    requirement_registry: Mapping[str, Any] | None = None,
    accepted_test_run_receipt: Mapping[str, Any] | None = None,
    repo_root: Path | None = None,
    previous_receipt: Mapping[str, Any] | None = None,
    step0_parent_authority: Mapping[str, Any] | None = None,
    prior_receipts: Sequence[Mapping[str, Any]] | None = None,
    publication_evidence: Mapping[str, Any] | None = None,
    **legacy_rejected: Any,
) -> dict[str, Any]:
    """Derive one PROVED candidate; caller-supplied proof maps are forbidden."""

    if legacy_rejected:
        raise ValueError(
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_VERDICT_INVALID"
        )
    if (
        type(step_number) is not int
        or isinstance(step_number, bool)
        or step_number not in range(11)
    ):
        raise ValueError(
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_STEP_INVALID"
        )
    if not RECOVERY_EPOCH001_PROVED_ISSUANCE_AUTHORIZED:
        raise ValueError(
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_VERDICT_INVALID"
        )
    root = (_REPO_ROOT if repo_root is None else Path(repo_root)).resolve()
    registry = (
        fresh_recovery_epoch001_current_step_requirement_registry()
        if requirement_registry is None
        else dict(requirement_registry)
    )
    registry_issues = (
        validate_recovery_epoch001_current_step_requirement_registry_shape(
            registry,
            repo_root=root,
        )
    )
    if registry_issues:
        raise ValueError(
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_VERDICT_INVALID"
        )
    event = (
        dict(step0_parent_authority)
        if type(step0_parent_authority) is dict
        else {}
    )
    accepted = (
        dict(accepted_test_run_receipt)
        if type(accepted_test_run_receipt) is dict
        else {}
    )
    accepted_issues = (
        validate_recovery_epoch001_accepted_test_run_receipt_shape(
            accepted,
            requirement_registry=registry,
            source_baseline_event=event,
            publication_evidence=publication_evidence,
            repo_root=root,
        )
    )
    if accepted_issues:
        raise ValueError("ACCEPTED_RECEIPT_NOT_ISSUABLE")
    closure = dict(_current_closure(root))
    closure["_repo_root"] = str(root)
    expected = _expected_step_material(
        step_number=step_number,
        registry=registry,
        accepted_test_run_receipt=accepted,
        closure=closure,
    )
    if expected is None:
        raise ValueError(
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_VERDICT_INVALID"
        )
    if step_number == 0:
        if prior_receipts not in (None, (), []):
            raise ValueError(
                "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_"
                "PARENT_CHAIN_INVALID"
            )
        parent_binding = _step0_parent_binding(event, accepted)
    else:
        if not _valid_prior_receipt_chain(
            prior_receipts,
            step_number=step_number,
            previous_receipt=previous_receipt,
            repo_root=root,
            step0_parent_authority=event,
            requirement_registry=registry,
            accepted_test_run_receipt=accepted,
            publication_evidence=publication_evidence,
            registry_issues=registry_issues,
            accepted_issues=accepted_issues,
            closure=closure,
        ):
            raise ValueError(
                "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_"
                "PARENT_CHAIN_INVALID"
            )
        parent_binding = _later_parent_binding(
            step_number=step_number,
            previous_receipt=previous_receipt,
            accepted_test_run_receipt=accepted,
        )
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
        "current_binding": expected["current_binding"],
        "actual_owners": expected["actual_owners"],
        "strict_contracts": expected["strict_contracts"],
        "positive_proof": expected["positive_proof"],
        "independent_negative_proof": (
            expected["independent_negative_proof"]
        ),
        "artifact_receipt": expected["artifact_receipt"],
        "parent_binding": parent_binding,
        "completion_condition": expected["completion_condition"],
        "stop_conditions": expected["stop_conditions"],
        "next_authority": expected["row"]["next_authority"],
        "verdict": "PROVED",
        "body_free": True,
    }
    receipt["receipt_sha256"] = artifact_sha256(receipt)
    issues = _validate_recovery_epoch001_current_step_completion_receipt_shape_impl(
        receipt,
        repo_root=root,
        previous_receipt=previous_receipt,
        step0_parent_authority=event,
        requirement_registry=registry,
        accepted_test_run_receipt=accepted,
        publication_evidence=publication_evidence,
        prior_receipts=prior_receipts,
        _registry_issues=registry_issues,
        _accepted_issues=accepted_issues,
        _closure_override=closure,
    )
    if issues:
        raise ValueError(issues[0])
    return receipt
