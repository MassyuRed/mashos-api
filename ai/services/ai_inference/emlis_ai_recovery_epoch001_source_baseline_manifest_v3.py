# -*- coding: utf-8 -*-
from __future__ import annotations

"""Body-free candidate source closure for Recovery Epoch 001.

This owner freezes the implementation candidate only.  It does not issue a
Step 0-10 completion receipt, lock the canonical source baseline, authorize a
fresh batch, or accept Cycle 001.
"""

import ast
from copy import deepcopy
import hashlib
from pathlib import Path
import re
from typing import Any, Mapping

from emlis_ai_nls_v3_artifact_contract import artifact_sha256


RECOVERY_EPOCH001_CANDIDATE_VERSION_ID = "nls_v3_rc_0032"
RECOVERY_EPOCH001_SCOPE = "RECOVERY_EPOCH001_PREREQUISITE_ONLY"
RECOVERY_EPOCH001_SOURCE_PREDECESSOR_CANDIDATE_VERSION_ID = "nls_v3_rc_0027"
RECOVERY_EPOCH001_SOURCE_PREDECESSOR_DISPOSITION = (
    "SOURCE_PREDECESSOR_ONLY_NOT_CYCLE_ACCEPTANCE"
)
RECOVERY_EPOCH001_SOURCE_BASELINE_MANIFEST_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch001_source_baseline_manifest.v1"
)

FROZEN_RECOVERY_EPOCH001_MANIFEST_SOURCE_NORMALIZED_SHA256 = "2821918c9fea1cdb40fc508eda3ca07b73759d9abcfa09a57dd4c40da4119ca8"
FROZEN_RECOVERY_EPOCH001_SOURCE_CLOSURE_SHA256 = "07ffb9ee2015df1cf057a50b69dbbb62e4ebf7b06c3bb9a045db350f1a69bf22"

RECOVERY_EPOCH001_SOURCE_BASELINE_NEGATIVE_CODES = frozenset(
    {
        "RECOVERY_SOURCE_BASELINE_ENTRY_INVALID",
        "RECOVERY_SOURCE_BASELINE_REQUIRED_PATH_MISSING",
        "RECOVERY_SOURCE_BASELINE_EXTRA_PATH",
        "RECOVERY_SOURCE_BASELINE_SOURCE_HASH_DRIFT",
        "RECOVERY_SOURCE_BASELINE_UNLISTED_IMPORTER",
        "RECOVERY_SOURCE_BASELINE_UNBOUND_LOCAL_IMPORT",
        "RECOVERY_SOURCE_BASELINE_OWNER_ROLE_MISMATCH",
        "RECOVERY_SOURCE_BASELINE_IMPORT_EDGE_FORBIDDEN",
        "RECOVERY_SOURCE_BASELINE_PUBLIC_DIRECT_IMPORT_FORBIDDEN",
        "RECOVERY_SOURCE_BASELINE_EVALUATION_CUE_INGRESS",
        "RECOVERY_SOURCE_BASELINE_RAW_BODY_INGRESS",
        "RECOVERY_SOURCE_BASELINE_DEFAULT_OWNER_OR_DORMANT_STATE_DRIFT",
        "RECOVERY_SOURCE_BASELINE_CANDIDATE_IDENTITY_INVALID",
        "RECOVERY_SOURCE_BASELINE_PREDECESSOR_BINDING_INVALID",
        "RECOVERY_SOURCE_BASELINE_HISTORICAL_STEP10_BINDING_INVALID",
    }
)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_MANIFEST_PATH = (
    "ai/services/ai_inference/"
    "emlis_ai_recovery_epoch001_source_baseline_manifest_v3.py"
)
_SHA_RE = re.compile(r"^[0-9a-f]{64}$")
_ALLOWED_ROLES = frozenset(
    {"semantic_core", "offline_runtime", "evidence", "test", "tool", "contract"}
)
_NORMALIZED_ASSIGNMENTS = frozenset(
    {
        "FROZEN_RECOVERY_EPOCH001_MANIFEST_SOURCE_NORMALIZED_SHA256",
        "FROZEN_RECOVERY_EPOCH001_SOURCE_CLOSURE_SHA256",
    }
)
_GUARDED_MODULES = frozenset(
    {
        "emlis_ai_refined_source_partition_v3",
        "emlis_ai_semantic_obligation_inventory_v3",
        "emlis_ai_content_selection_v3",
        "emlis_ai_recovery_epoch001_source_baseline_manifest_v3",
    }
)
_DESIGNATED_GENERATION_OWNER = (
    "ai/services/ai_inference/emlis_ai_content_selection_v3.py"
)
_PUBLIC_REPLY_OWNER = "ai/services/ai_inference/emlis_ai_reply_service.py"

# The path set is literal.  Discovery may reject a new importer but may never
# enlarge this candidate closure.
_FILE_CONTRACTS: dict[str, tuple[str, bool]] = {
    "ai/services/ai_inference/emlis_ai_bounded_recovery_v3.py": (
        "semantic_core",
        False,
    ),
    "ai/services/ai_inference/emlis_ai_canonical_renderer_v3.py": (
        "semantic_core",
        False,
    ),
    "ai/services/ai_inference/emlis_ai_content_selection_v3.py": (
        "semantic_core",
        False,
    ),
    "ai/services/ai_inference/emlis_ai_discourse_graph_planner_v3.py": (
        "semantic_core",
        False,
    ),
    "ai/services/ai_inference/emlis_ai_dormant_runtime_adapter_v3.py": (
        "offline_runtime",
        False,
    ),
    "ai/services/ai_inference/emlis_ai_evidence_ledger_service.py": (
        "semantic_core",
        False,
    ),
    "ai/services/ai_inference/emlis_ai_grounded_lexical_role_experiment_snapshot_successor_v3.py": (
        "evidence",
        False,
    ),
    "ai/services/ai_inference/emlis_ai_grounded_lexical_role_experiment_snapshot_v3.py": (
        "evidence",
        False,
    ),
    "ai/services/ai_inference/emlis_ai_grounded_observation_plan.py": (
        "semantic_core",
        False,
    ),
    "ai/services/ai_inference/emlis_ai_independent_semantic_matcher_v3.py": (
        "semantic_core",
        False,
    ),
    "ai/services/ai_inference/emlis_ai_lexicographic_selector_v3.py": (
        "semantic_core",
        False,
    ),
    _MANIFEST_PATH: ("contract", False),
    "ai/services/ai_inference/emlis_ai_nls_v3_artifact_contract.py": (
        "contract",
        False,
    ),
    "ai/services/ai_inference/emlis_ai_observation_stage_context_v3.py": (
        "semantic_core",
        False,
    ),
    "ai/services/ai_inference/emlis_ai_rc0028_experiment_dependency_manifest_v3.py": (
        "contract",
        False,
    ),
    "ai/services/ai_inference/emlis_ai_refined_source_partition_v3.py": (
        "semantic_core",
        False,
    ),
    _PUBLIC_REPLY_OWNER: ("contract", True),
    "ai/services/ai_inference/emlis_ai_semantic_hard_gate_v3.py": (
        "semantic_core",
        False,
    ),
    "ai/services/ai_inference/emlis_ai_semantic_obligation_inventory_v3.py": (
        "semantic_core",
        False,
    ),
    "ai/services/ai_inference/emlis_ai_step10_dependency_manifest_v3.py": (
        "contract",
        False,
    ),
    "ai/services/ai_inference/emlis_ai_step10_evidence_v3.py": (
        "evidence",
        False,
    ),
    "ai/services/ai_inference/emlis_ai_step11_hard_gate_v3.py": (
        "semantic_core",
        False,
    ),
    "ai/services/ai_inference/emlis_ai_step11_natural_surface_matcher_v3.py": (
        "semantic_core",
        False,
    ),
    "ai/services/ai_inference/emlis_ai_step11_natural_surface_v3.py": (
        "semantic_core",
        False,
    ),
    "ai/services/ai_inference/emlis_ai_step11_planning_frontier_v3.py": (
        "semantic_core",
        False,
    ),
    "ai/services/ai_inference/emlis_ai_step11_rc0031_reception_focus_authority_v3.py": (
        "evidence",
        False,
    ),
    "ai/services/ai_inference/emlis_ai_step11_runtime_adapter_v3.py": (
        "offline_runtime",
        False,
    ),
    "ai/services/ai_inference/emlis_ai_step11_semantic_overlay_v3.py": (
        "semantic_core",
        False,
    ),
    "ai/services/ai_inference/emlis_ai_typed_surface_ast_v3.py": (
        "semantic_core",
        False,
    ),
    "ai/tests/test_emlis_nls_v3_recovery_epoch001_prerequisite_red.py": (
        "test",
        False,
    ),
    "ai/tests/test_emlis_nls_v3_s10_dormant_runtime_batch_evidence.py": (
        "test",
        False,
    ),
    "ai/tests/test_emlis_nls_v3_s11_rc0028_lexical_role_snapshot_red.py": (
        "test",
        False,
    ),
    "ai/tests/test_emlis_nls_v3_s11_rc0028_successor_snapshot.py": (
        "test",
        False,
    ),
    "ai/tests/test_emlis_nls_v3_s4_semantic_obligation_inventory.py": (
        "test",
        False,
    ),
    "ai/tests/test_emlis_nls_v3_s5_content_selection_stage_context.py": (
        "test",
        False,
    ),
    "ai/tests/test_emlis_nls_v3_s6_discourse_graph_planner.py": (
        "test",
        False,
    ),
    "ai/tests/test_emlis_nls_v3_s7_typed_ast_canonical_renderer.py": (
        "test",
        False,
    ),
    "ai/tests/test_emlis_nls_v3_s8_body_parser_independent_matcher.py": (
        "test",
        False,
    ),
    "ai/tests/test_emlis_nls_v3_s9_hard_gate_selector_recovery.py": (
        "test",
        False,
    ),
    "ai/tools/emlis_nls_v3_batch_run.py": ("tool", False),
}

_FROZEN_FILE_SHA256: dict[str, str] = {
    "ai/services/ai_inference/emlis_ai_bounded_recovery_v3.py": "e1e62049fc521658597124832d700a4842aca995ffd9ae38f8db583b7ba4f13f",
    "ai/services/ai_inference/emlis_ai_canonical_renderer_v3.py": "7f85e7dc8c5e2009409adf5a6700cfc12a4c1e7b2ffa522c96f7319fcbfa5507",
    "ai/services/ai_inference/emlis_ai_content_selection_v3.py": "ec2ccfc92c5566e8ec780e67db54b4a4c620a9334f2ab2cac91a314550f43f0d",
    "ai/services/ai_inference/emlis_ai_discourse_graph_planner_v3.py": "b53fc447707f1fe77440aaf0f59ccb815557064ecfeb9c6b484db0733e4917bf",
    "ai/services/ai_inference/emlis_ai_dormant_runtime_adapter_v3.py": "e277b0a34d5926f9ad3af100b3cf0d8dd92e2c3f773c18b5d6ae9fe1b633d6c2",
    "ai/services/ai_inference/emlis_ai_evidence_ledger_service.py": "17e51d7ff39535d60f81ad17582f36ab252301502a3a3328e703d116cea7f9e2",
    "ai/services/ai_inference/emlis_ai_grounded_lexical_role_experiment_snapshot_successor_v3.py": "c20b3b476a13639d0571d90ad04bc59c67124df01017287878aa2c646679e518",
    "ai/services/ai_inference/emlis_ai_grounded_lexical_role_experiment_snapshot_v3.py": "4671aa22c4e432f907780f0becf900fead57044c53ea3bbc1bf501eb5abc1a27",
    "ai/services/ai_inference/emlis_ai_grounded_observation_plan.py": "b422093f907f3a825ec30f687f2f8b1d2688bf89950d9bc7436bfe0b5a67d177",
    "ai/services/ai_inference/emlis_ai_independent_semantic_matcher_v3.py": "12f040407adc299b2695ee58b93619157690cfb745072b4e72f529ee5dd2ed9e",
    "ai/services/ai_inference/emlis_ai_lexicographic_selector_v3.py": "4fa8770d82273b328e0a968b1315ec68f6c57cdf4aec576dbc36434f5453833d",
    _MANIFEST_PATH: FROZEN_RECOVERY_EPOCH001_MANIFEST_SOURCE_NORMALIZED_SHA256,
    "ai/services/ai_inference/emlis_ai_nls_v3_artifact_contract.py": "c20b262495276c9b549b257380e1a7c28069c316a7aca4b6e00a49de03d1512b",
    "ai/services/ai_inference/emlis_ai_observation_stage_context_v3.py": "c112508fa530d23c15f6771debaaaa63c972855bdae8e007530179c5cef8f935",
    "ai/services/ai_inference/emlis_ai_rc0028_experiment_dependency_manifest_v3.py": "284dcf838851fc8a9596a2e8e86702e97f901f9c2c2872d218334db987b1e093",
    "ai/services/ai_inference/emlis_ai_refined_source_partition_v3.py": "02d943e3cb6f3e1a60bae38242900af0f929de9bf0b5300c3f9d4be10a44389a",
    _PUBLIC_REPLY_OWNER: "162b94eb185c519e50dceee62e591cc8ab02204312761874eb2fbb636ffbe50a",
    "ai/services/ai_inference/emlis_ai_semantic_hard_gate_v3.py": "ce2a9818b46196fa5966a2e13394cc1b51089aab664e6660e86c4526f9050c51",
    "ai/services/ai_inference/emlis_ai_semantic_obligation_inventory_v3.py": "0a66adbf3163cf3aad1d4454a8a26aa6292284911b4bd5ba1825e0780e3aa2bc",
    "ai/services/ai_inference/emlis_ai_step10_dependency_manifest_v3.py": "3bc1311c264cbbae71e69c643d055575e9b80c58b71d321ff28e744ad0ee090c",
    "ai/services/ai_inference/emlis_ai_step10_evidence_v3.py": "ac4ed5cf28cf538e481964077dc3a9c57e77eb55dab61423953aadb7279f01ac",
    "ai/services/ai_inference/emlis_ai_step11_hard_gate_v3.py": "88514bb2a179e8d726f36e1666d2618330d95979107403ededc93aa35655943b",
    "ai/services/ai_inference/emlis_ai_step11_natural_surface_matcher_v3.py": "648a3a6690f8df860053c811a5416fcfc9983524e5ff880a0e6921a122a52e30",
    "ai/services/ai_inference/emlis_ai_step11_natural_surface_v3.py": "22295885af5c25d1738988a06846b3c70ab86f8d1ee88a6e6db7767e8774cd39",
    "ai/services/ai_inference/emlis_ai_step11_planning_frontier_v3.py": "0dbdef20024bbb668c446f4510fcdeff85bf913124c325c6374434708e2e89c6",
    "ai/services/ai_inference/emlis_ai_step11_rc0031_reception_focus_authority_v3.py": "af141bc43728f915e19f675f261c18d5381f7da80b3fb1145257965fd3917753",
    "ai/services/ai_inference/emlis_ai_step11_runtime_adapter_v3.py": "012d09ab82ff526a9d854c845a7930eb8836e1dbd41c67428644c2c3a02bfbc7",
    "ai/services/ai_inference/emlis_ai_step11_semantic_overlay_v3.py": "9bde482db60183078692c2b9a38311f30185c93180ddfca85cc282c60f088e42",
    "ai/services/ai_inference/emlis_ai_typed_surface_ast_v3.py": "2c35115761245534c3c811251e451b8bb163b6e664454a21f275acf0dc76046b",
    "ai/tests/test_emlis_nls_v3_recovery_epoch001_prerequisite_red.py": "fffda42687a77f5f2c1f83d39c96cbf4eb7099438b8c0f7179dacdf5b02ceb14",
    "ai/tests/test_emlis_nls_v3_s10_dormant_runtime_batch_evidence.py": "524912e7961feedde0b73d69315e3a2343ac8fc096b53c1c0d957b00a260ff06",
    "ai/tests/test_emlis_nls_v3_s11_rc0028_lexical_role_snapshot_red.py": "4d71b27ad4755d7412a847b328cb9475190af843c66f7c6979be81610b4f2b23",
    "ai/tests/test_emlis_nls_v3_s11_rc0028_successor_snapshot.py": "b2a18ca43a638b5c973d9b0adc579868e617e84aeea1ab6180879f559f518d4d",
    "ai/tests/test_emlis_nls_v3_s4_semantic_obligation_inventory.py": "5a874d7298a5d6d2c7d08439b44af02ed08a3520d5191d6cf3fc3c9672614314",
    "ai/tests/test_emlis_nls_v3_s5_content_selection_stage_context.py": "79039dd364e21d1e78e2b83e0cb5e13404fe703f22d310143445d3bbd01347cb",
    "ai/tests/test_emlis_nls_v3_s6_discourse_graph_planner.py": "fff89be79c546a505246ea5ce5e065516b4d26d98405916b16aaceb24008080d",
    "ai/tests/test_emlis_nls_v3_s7_typed_ast_canonical_renderer.py": "952f64e87f06588b101b18206669a311093ae9007f97d955a1093391010508a4",
    "ai/tests/test_emlis_nls_v3_s8_body_parser_independent_matcher.py": "b6eb04935e8c6ab082565551cec48b379f6aafa58b22cfdc40184c977f547d16",
    "ai/tests/test_emlis_nls_v3_s9_hard_gate_selector_recovery.py": "3e30a9ee2190054e2a7585d3df7068566cde1f1b6b8134d5ab9db6e652f52ed6",
    "ai/tools/emlis_nls_v3_batch_run.py": "3349199e386088d493f568345debc3e9bfa657aaec8d5024d3514e40979f28f3",
}

_SOURCE_PREDECESSOR = {
    "candidate_version_id": RECOVERY_EPOCH001_SOURCE_PREDECESSOR_CANDIDATE_VERSION_ID,
    "disposition": RECOVERY_EPOCH001_SOURCE_PREDECESSOR_DISPOSITION,
}
_HISTORICAL_STEP10 = {
    "candidate_version_id": "nls_v3_rc_0010",
    "manifest_source_sha256": "3bc1311c264cbbae71e69c643d055575e9b80c58b71d321ff28e744ad0ee090c",
    "manifest_artifact_sha256": "83af18e635b16a7ca5680940f7362e9b844961bf2ac23101ba65a1b44fcc1af2",
    "dependency_closure_sha256": "2b4cd6cb5ea0f0d69ae7de31930dd6833ba21fce8eb7262f579cad514f14a8e9",
    "disposition": "HISTORICAL_IMMUTABLE_NOT_CURRENT_AUTHORITY",
}
_STEP10_RUNTIME_BOUNDARY = {
    "default_public_routing_state": "disabled",
    "production_owner": "grounded_sentence_surface_canonical_v1",
    "v3_general_account_visible": False,
    "owner_activation_permitted": False,
    "reply_service_public_export": ["render_emlis_ai_reply"],
}
_AUTHORITY_BOUNDARY = {
    "source_baseline_state": "UNLOCKED_PENDING_RECEIPT_GENERATION_AND_VERIFICATION",
    "successful_step0_10_completion_receipt_count": 0,
    "fresh_batch_state": "RESERVED_NOT_CREATED",
    "cycle001_state": "NOT_ACCEPTED",
}


def build_recovery_epoch001_source_baseline_manifest() -> dict[str, Any]:
    """Build the candidate closure without granting completion authority."""

    return {
        "schema_version": RECOVERY_EPOCH001_SOURCE_BASELINE_MANIFEST_SCHEMA,
        "candidate_version_id": RECOVERY_EPOCH001_CANDIDATE_VERSION_ID,
        "scope": RECOVERY_EPOCH001_SCOPE,
        "source_predecessor": deepcopy(_SOURCE_PREDECESSOR),
        "historical_step10": deepcopy(_HISTORICAL_STEP10),
        "manifest_source_normalized_sha256": (
            FROZEN_RECOVERY_EPOCH001_MANIFEST_SOURCE_NORMALIZED_SHA256
        ),
        "files": {
            path: {
                "sha256": _FROZEN_FILE_SHA256[path],
                "role": role,
                "runtime_connected": runtime_connected,
                "body_free": True,
            }
            for path, (role, runtime_connected) in sorted(_FILE_CONTRACTS.items())
        },
        "step10_runtime_boundary": deepcopy(_STEP10_RUNTIME_BOUNDARY),
        "authority_boundary": deepcopy(_AUTHORITY_BOUNDARY),
        "source_closure_sha256": (
            FROZEN_RECOVERY_EPOCH001_SOURCE_CLOSURE_SHA256
        ),
        "body_free": True,
    }


RECOVERY_EPOCH001_SOURCE_BASELINE_MANIFEST = (
    build_recovery_epoch001_source_baseline_manifest()
)


def _normalized_manifest_source_bytes(raw: bytes) -> bytes | None:
    try:
        source = raw.decode("utf-8", errors="strict")
        tree = ast.parse(source)
    except (SyntaxError, UnicodeError):
        return None
    lines = raw.splitlines(keepends=True)
    starts: list[int] = []
    offset = 0
    for line in lines:
        starts.append(offset)
        offset += len(line)
    replacements: dict[str, tuple[int, int]] = {}
    for node in tree.body:
        if (
            not isinstance(node, ast.Assign)
            or len(node.targets) != 1
            or not isinstance(node.targets[0], ast.Name)
            or node.targets[0].id not in _NORMALIZED_ASSIGNMENTS
            or not hasattr(node.value, "end_lineno")
            or not hasattr(node.value, "end_col_offset")
        ):
            continue
        name = node.targets[0].id
        if name in replacements:
            return None
        replacements[name] = (
            starts[node.value.lineno - 1] + node.value.col_offset,
            starts[node.value.end_lineno - 1] + node.value.end_col_offset,
        )
    if set(replacements) != _NORMALIZED_ASSIGNMENTS:
        return None
    normalized = raw
    zero = b'"' + (b"0" * 64) + b'"'
    for start, end in sorted(replacements.values(), reverse=True):
        normalized = normalized[:start] + zero + normalized[end:]
    return normalized


def normalized_recovery_epoch001_manifest_source_sha256() -> str | None:
    try:
        raw = (_REPO_ROOT / _MANIFEST_PATH).read_bytes()
    except OSError:
        return None
    normalized = _normalized_manifest_source_bytes(raw)
    return hashlib.sha256(normalized).hexdigest() if normalized is not None else None


def _safe_relative_path(value: Any) -> str | None:
    if type(value) is not str or not value or "\\" in value:
        return None
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or path.as_posix() != value:
        return None
    return value


def _imports_from_tree(tree: ast.AST) -> frozenset[str]:
    result: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            result.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            result.add(node.module)
    return frozenset(result)


def _repository_local_modules() -> frozenset[str]:
    result: set[str] = set()
    for root in (
        _REPO_ROOT / "ai" / "services" / "ai_inference",
        _REPO_ROOT / "ai" / "tests",
        _REPO_ROOT / "ai" / "tests" / "helpers",
        _REPO_ROOT / "ai" / "tools",
    ):
        try:
            paths = root.glob("*.py")
        except OSError:
            continue
        result.update(path.stem for path in paths)
    return frozenset(result)


def _generation_ingress_issues(tree: ast.AST) -> set[str]:
    issues: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            lowered = node.id.lower()
            if "expected_answer" in lowered or "expected_surface" in lowered:
                issues.add("RECOVERY_SOURCE_BASELINE_EVALUATION_CUE_INGRESS")
            if lowered in {"raw_input", "raw_body", "request_body"}:
                issues.add("RECOVERY_SOURCE_BASELINE_RAW_BODY_INGRESS")
        elif isinstance(node, ast.Attribute):
            if (
                node.attr == "body"
                and isinstance(node.value, ast.Name)
                and node.value.id == "request"
            ):
                issues.add("RECOVERY_SOURCE_BASELINE_RAW_BODY_INGRESS")
    return issues


def validate_recovery_epoch001_source_guard(
    relative_path: str,
    source_bytes: bytes,
    manifest: Mapping[str, Any],
) -> tuple[str, ...]:
    """Validate one body-free closure edge from caller-supplied bytes."""

    issues: set[str] = set()
    path = _safe_relative_path(relative_path)
    if path is None or type(source_bytes) is not bytes or not isinstance(manifest, Mapping):
        return ("RECOVERY_SOURCE_BASELINE_ENTRY_INVALID",)
    try:
        source = source_bytes.decode("utf-8", errors="strict")
        tree = ast.parse(source, filename=path)
    except (SyntaxError, UnicodeError):
        return ("RECOVERY_SOURCE_BASELINE_ENTRY_INVALID",)
    imports = _imports_from_tree(tree)
    files = manifest.get("files")
    row = files.get(path) if isinstance(files, Mapping) else None
    if not isinstance(row, Mapping):
        if imports & _GUARDED_MODULES:
            issues.add("RECOVERY_SOURCE_BASELINE_UNLISTED_IMPORTER")
        return tuple(sorted(issues))

    normalized = (
        _normalized_manifest_source_bytes(source_bytes)
        if path == _MANIFEST_PATH
        else source_bytes
    )
    actual = hashlib.sha256(normalized).hexdigest() if normalized is not None else None
    if actual != row.get("sha256"):
        issues.add("RECOVERY_SOURCE_BASELINE_SOURCE_HASH_DRIFT")

    local_modules = _repository_local_modules()
    if any(
        (name.startswith("emlis_ai_") or name.startswith("test_emlis_"))
        and name.split(".", 1)[0] not in local_modules
        for name in imports
    ):
        issues.add("RECOVERY_SOURCE_BASELINE_UNBOUND_LOCAL_IMPORT")
    if row.get("role") != "test" and any(
        name.split(".", 1)[0].startswith("test_emlis_") for name in imports
    ):
        issues.add("RECOVERY_SOURCE_BASELINE_IMPORT_EDGE_FORBIDDEN")
    if path == _PUBLIC_REPLY_OWNER and imports & (
        _GUARDED_MODULES - {"emlis_ai_recovery_epoch001_source_baseline_manifest_v3"}
    ):
        issues.add("RECOVERY_SOURCE_BASELINE_PUBLIC_DIRECT_IMPORT_FORBIDDEN")
    if path == _DESIGNATED_GENERATION_OWNER:
        issues.update(_generation_ingress_issues(tree))
    return tuple(sorted(issues))


def validate_recovery_epoch001_source_baseline_manifest_shape(
    value: Any,
) -> tuple[str, ...]:
    issues: set[str] = set()
    if type(value) is not dict:
        return ("RECOVERY_SOURCE_BASELINE_ENTRY_INVALID",)
    expected_keys = {
        "schema_version",
        "candidate_version_id",
        "scope",
        "source_predecessor",
        "historical_step10",
        "manifest_source_normalized_sha256",
        "files",
        "step10_runtime_boundary",
        "authority_boundary",
        "source_closure_sha256",
        "body_free",
    }
    if set(value) != expected_keys:
        issues.add("RECOVERY_SOURCE_BASELINE_ENTRY_INVALID")
    if (
        value.get("schema_version")
        != RECOVERY_EPOCH001_SOURCE_BASELINE_MANIFEST_SCHEMA
        or value.get("scope") != RECOVERY_EPOCH001_SCOPE
        or value.get("body_free") is not True
    ):
        issues.add("RECOVERY_SOURCE_BASELINE_ENTRY_INVALID")
    if value.get("candidate_version_id") != RECOVERY_EPOCH001_CANDIDATE_VERSION_ID:
        issues.add("RECOVERY_SOURCE_BASELINE_CANDIDATE_IDENTITY_INVALID")
    if value.get("source_predecessor") != _SOURCE_PREDECESSOR:
        issues.add("RECOVERY_SOURCE_BASELINE_PREDECESSOR_BINDING_INVALID")
    if value.get("historical_step10") != _HISTORICAL_STEP10:
        issues.add("RECOVERY_SOURCE_BASELINE_HISTORICAL_STEP10_BINDING_INVALID")
    if value.get("step10_runtime_boundary") != _STEP10_RUNTIME_BOUNDARY:
        issues.add("RECOVERY_SOURCE_BASELINE_DEFAULT_OWNER_OR_DORMANT_STATE_DRIFT")
    if value.get("authority_boundary") != _AUTHORITY_BOUNDARY:
        issues.add("RECOVERY_SOURCE_BASELINE_ENTRY_INVALID")
    if (
        value.get("manifest_source_normalized_sha256")
        != FROZEN_RECOVERY_EPOCH001_MANIFEST_SOURCE_NORMALIZED_SHA256
        or value.get("source_closure_sha256")
        != FROZEN_RECOVERY_EPOCH001_SOURCE_CLOSURE_SHA256
    ):
        issues.add("RECOVERY_SOURCE_BASELINE_ENTRY_INVALID")

    files = value.get("files")
    if type(files) is not dict:
        return tuple(sorted(issues | {"RECOVERY_SOURCE_BASELINE_ENTRY_INVALID"}))
    expected_paths = set(_FILE_CONTRACTS)
    actual_paths = set(files)
    if expected_paths - actual_paths:
        issues.add("RECOVERY_SOURCE_BASELINE_REQUIRED_PATH_MISSING")
    if actual_paths - expected_paths:
        issues.add("RECOVERY_SOURCE_BASELINE_EXTRA_PATH")
    for path in expected_paths & actual_paths:
        row = files[path]
        expected_role, expected_runtime = _FILE_CONTRACTS[path]
        if (
            type(row) is not dict
            or set(row) != {"sha256", "role", "runtime_connected", "body_free"}
            or type(row.get("sha256")) is not str
            or _SHA_RE.fullmatch(row["sha256"]) is None
            or row["sha256"] == "0" * 64
            or row.get("body_free") is not True
        ):
            issues.add("RECOVERY_SOURCE_BASELINE_ENTRY_INVALID")
            continue
        if (
            row.get("role") not in _ALLOWED_ROLES
            or row.get("role") != expected_role
            or row.get("runtime_connected") is not expected_runtime
        ):
            issues.add("RECOVERY_SOURCE_BASELINE_OWNER_ROLE_MISMATCH")
    return tuple(sorted(issues))


def _fresh_file_rows() -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for path, (role, runtime_connected) in sorted(_FILE_CONTRACTS.items()):
        raw = (_REPO_ROOT / path).read_bytes()
        normalized = (
            _normalized_manifest_source_bytes(raw) if path == _MANIFEST_PATH else raw
        )
        if normalized is None:
            raise ValueError("RECOVERY_SOURCE_BASELINE_SOURCE_UNAVAILABLE")
        rows[path] = {
            "sha256": hashlib.sha256(normalized).hexdigest(),
            "role": role,
            "runtime_connected": runtime_connected,
            "body_free": True,
        }
    return rows


def fresh_recovery_epoch001_source_closure_sha256() -> str:
    """Fresh-read the candidate closure; never use import-cached source bytes."""

    return artifact_sha256(
        {
            "schema_version": "cocolon.emlis.nls_v3.recovery_epoch001_source_closure.v1",
            "candidate_version_id": RECOVERY_EPOCH001_CANDIDATE_VERSION_ID,
            "scope": RECOVERY_EPOCH001_SCOPE,
            "source_predecessor": _SOURCE_PREDECESSOR,
            "historical_step10": _HISTORICAL_STEP10,
            "files": _fresh_file_rows(),
            "step10_runtime_boundary": _STEP10_RUNTIME_BOUNDARY,
            "authority_boundary": _AUTHORITY_BOUNDARY,
            "body_free": True,
        }
    )


def recovery_epoch001_source_file_sha256(relative_path: str) -> str | None:
    row = RECOVERY_EPOCH001_SOURCE_BASELINE_MANIFEST["files"].get(relative_path)
    if type(row) is not dict:
        return None
    value = row.get("sha256")
    return value if type(value) is str and _SHA_RE.fullmatch(value) else None


def _unexpected_importer_issues(manifest: Mapping[str, Any]) -> set[str]:
    issues: set[str] = set()
    declared = manifest.get("files")
    declared_paths = set(declared) if isinstance(declared, Mapping) else set()
    for path in (_REPO_ROOT / "ai").rglob("*.py"):
        relative = path.relative_to(_REPO_ROOT).as_posix()
        if relative in declared_paths:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=relative)
        except (OSError, SyntaxError, UnicodeError):
            continue
        if _imports_from_tree(tree) & _GUARDED_MODULES:
            issues.add("RECOVERY_SOURCE_BASELINE_UNLISTED_IMPORTER")
    return issues


def validate_recovery_epoch001_source_baseline_manifest(
    value: Any = None,
) -> tuple[str, ...]:
    manifest = (
        RECOVERY_EPOCH001_SOURCE_BASELINE_MANIFEST if value is None else value
    )
    issues = set(validate_recovery_epoch001_source_baseline_manifest_shape(manifest))
    if type(manifest) is not dict:
        return tuple(sorted(issues))
    files = manifest.get("files")
    if type(files) is dict:
        for path in sorted(set(files) & set(_FILE_CONTRACTS)):
            try:
                raw = (_REPO_ROOT / path).read_bytes()
            except OSError:
                issues.add("RECOVERY_SOURCE_BASELINE_SOURCE_HASH_DRIFT")
                continue
            issues.update(validate_recovery_epoch001_source_guard(path, raw, manifest))
        issues.update(_unexpected_importer_issues(manifest))
    if normalized_recovery_epoch001_manifest_source_sha256() != (
        FROZEN_RECOVERY_EPOCH001_MANIFEST_SOURCE_NORMALIZED_SHA256
    ):
        issues.add("RECOVERY_SOURCE_BASELINE_SOURCE_HASH_DRIFT")
    try:
        fresh = fresh_recovery_epoch001_source_closure_sha256()
    except (OSError, ValueError):
        fresh = None
    if fresh != FROZEN_RECOVERY_EPOCH001_SOURCE_CLOSURE_SHA256:
        issues.add("RECOVERY_SOURCE_BASELINE_SOURCE_HASH_DRIFT")
    return tuple(sorted(issues))


__all__ = [
    "FROZEN_RECOVERY_EPOCH001_MANIFEST_SOURCE_NORMALIZED_SHA256",
    "FROZEN_RECOVERY_EPOCH001_SOURCE_CLOSURE_SHA256",
    "RECOVERY_EPOCH001_CANDIDATE_VERSION_ID",
    "RECOVERY_EPOCH001_SCOPE",
    "RECOVERY_EPOCH001_SOURCE_BASELINE_MANIFEST",
    "RECOVERY_EPOCH001_SOURCE_BASELINE_MANIFEST_SCHEMA",
    "RECOVERY_EPOCH001_SOURCE_BASELINE_NEGATIVE_CODES",
    "RECOVERY_EPOCH001_SOURCE_PREDECESSOR_CANDIDATE_VERSION_ID",
    "RECOVERY_EPOCH001_SOURCE_PREDECESSOR_DISPOSITION",
    "build_recovery_epoch001_source_baseline_manifest",
    "fresh_recovery_epoch001_source_closure_sha256",
    "normalized_recovery_epoch001_manifest_source_sha256",
    "recovery_epoch001_source_file_sha256",
    "validate_recovery_epoch001_source_baseline_manifest",
    "validate_recovery_epoch001_source_baseline_manifest_shape",
    "validate_recovery_epoch001_source_guard",
]
