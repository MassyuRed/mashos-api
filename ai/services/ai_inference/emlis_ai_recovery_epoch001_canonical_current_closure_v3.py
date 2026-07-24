# -*- coding: utf-8 -*-
from __future__ import annotations

"""Fresh, body-free Recovery Epoch 001 canonical-current closure owner.

The historical Step 0/1 and rc0032 manifests remain immutable evidence.  This
owner derives the current reply dependency closure and the Step 0--10 proof
views from the bytes that are actually present in the repository.
"""

import ast
import hashlib
from pathlib import Path
import re
import subprocess
from typing import Any, Iterable, Mapping

from emlis_ai_nls_v3_artifact_contract import (
    artifact_sha256,
    canonical_json_bytes,
)


RECOVERY_EPOCH001_CANONICAL_CURRENT_CLOSURE_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch001."
    "canonical_current_closure.v1"
)
RECOVERY_EPOCH001_CANDIDATE_VERSION_ID = "nls_v3_rc_0034"
RECOVERY_EPOCH001_SCOPE = (
    "RECOVERY_EPOCH001_CANONICAL_CURRENT_CLOSURE_CANDIDATE_ONLY"
)
RECOVERY_EPOCH001_DISPOSITION = (
    "CURRENT_CLOSURE_CANDIDATE_NOT_BASELINE_NOT_CYCLE_ACCEPTANCE"
)
RECOVERY_EPOCH001_SOURCE_PREDECESSOR_COMMIT = (
    "bd62ef0eec2348e3b190ec2a39c3794886ccd10d"
)
RECOVERY_EPOCH001_AUTHORITY_ENTRY_COMMIT = (
    "7a771247ca26ce435d325b5eb484197b1bdec7c2"
)
RECOVERY_EPOCH001_CANONICAL_CURRENT_CLOSURE_NEGATIVE_CODES = frozenset(
    {
        "RECOVERY_CANONICAL_CURRENT_CLOSURE_ENTRY_INVALID",
        "RECOVERY_CANONICAL_CURRENT_CLOSURE_CANDIDATE_IDENTITY_INVALID",
        "RECOVERY_CANONICAL_CURRENT_CLOSURE_REQUIRED_SEED_MISSING",
        "RECOVERY_CANONICAL_CURRENT_CLOSURE_REQUIRED_FILE_MISSING",
        "RECOVERY_CANONICAL_CURRENT_CLOSURE_EXTRA_FILE",
        "RECOVERY_CANONICAL_CURRENT_CLOSURE_FILE_HASH_DRIFT",
        "RECOVERY_CANONICAL_CURRENT_CLOSURE_GIT_BLOB_DRIFT",
        "RECOVERY_CANONICAL_CURRENT_CLOSURE_EXISTING_LOCAL_IMPORT_UNLISTED",
        "RECOVERY_CANONICAL_CURRENT_CLOSURE_REQUIRED_EDGE_MISSING",
        "RECOVERY_CANONICAL_CURRENT_CLOSURE_EDGE_TARGET_UNRESOLVED",
        "RECOVERY_CANONICAL_CURRENT_CLOSURE_ROLE_BINDING_DRIFT",
        "RECOVERY_CANONICAL_CURRENT_CLOSURE_VIEW_BINDING_DRIFT",
        "RECOVERY_CANONICAL_CURRENT_CLOSURE_FORBIDDEN_EDGE",
        "RECOVERY_CANONICAL_CURRENT_CLOSURE_FORBIDDEN_CUE_INGRESS",
        "RECOVERY_CANONICAL_CURRENT_CLOSURE_PRIVATE_BODY_INGRESS",
        "RECOVERY_CANONICAL_CURRENT_CLOSURE_SELF_NORMALIZATION_SCOPE_DRIFT",
        "RECOVERY_CANONICAL_CURRENT_CLOSURE_START_END_DRIFT",
    }
)

_HERE = Path(__file__).resolve()
_REPO_ROOT = _HERE.parents[3]
_AI_ROOT = _REPO_ROOT / "ai"
_INFERENCE_ROOT = _AI_ROOT / "services" / "ai_inference"
_DEPENDENCY_ENTRY_PATH = (
    "ai/services/ai_inference/emlis_ai_reply_service.py"
)
_PRE_IMPLEMENTATION_DEPENDENCY_ROOT = (
    "7d15cc072ac4ac28b6b9ce90676c6238ba08d5f59fd1896a7273ce7d57a7f302"
)
_SUCCESSOR_PATH = (
    "ai/services/ai_inference/"
    "emlis_ai_step9_recovery_epoch001_successor_v3.py"
)
_SHA_RE = re.compile(r"^[0-9a-f]{64}$")
_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
_BLOB_RE = re.compile(r"^[0-9a-f]{40}$")

_CURRENT_OWNER_PATHS = (
    "ai/services/ai_inference/emlis_ai_grounded_observation_plan.py",
    "ai/services/ai_inference/emlis_ai_grounded_human_reception.py",
    "ai/services/ai_inference/emlis_ai_grounded_sentence_surface.py",
    "ai/services/ai_inference/emlis_ai_grounded_observation_gate.py",
    "ai/services/ai_inference/emlis_ai_reply_service.py",
)
_STOPPED_V2_ANCHORS = (
    "ai/services/ai_inference/emlis_ai_grounded_reception_content_plan_v2.py",
    "ai/services/ai_inference/emlis_ai_grounded_reception_candidate_plan_v2.py",
    "ai/services/ai_inference/emlis_ai_grounded_human_reception_v2.py",
    (
        "ai/services/ai_inference/"
        "emlis_ai_grounded_reception_candidate_selector_v2.py"
    ),
)
_HISTORICAL_EVIDENCE_SEEDS = frozenset(_STOPPED_V2_ANCHORS)
_STEP_SEEDS: dict[int, frozenset[str]] = {
    0: frozenset(
        {
            "ai/tests/helpers/emlis_nls_v3_s0_s1_baseline.py",
            "ai/tests/test_emlis_nls_v3_s0_s1.py",
            "ai/tests/fixtures/emlis_nls_v3_s0_boundary_20260714.json",
            (
                "ai/tests/test_emlis_nls_v3_recovery_epoch001_"
                "step00_independent_negative.py"
            ),
            *_CURRENT_OWNER_PATHS,
        }
    ),
    1: frozenset(
        {
            "ai/tests/helpers/emlis_nls_v3_s0_s1_baseline.py",
            "ai/tests/test_emlis_nls_v3_s0_s1.py",
            "ai/tests/fixtures/emlis_nls_v3_s1_input_contract_20260714.json",
            "ai/tests/fixtures/emlis_nls_v3_s1_baseline_receipt_20260714.json",
            (
                "ai/tests/test_emlis_nls_v3_recovery_epoch001_"
                "step01_independent_negative.py"
            ),
            *_CURRENT_OWNER_PATHS,
            "ai/services/ai_inference/api_emotion_submit.py",
            "ai/services/ai_inference/emotion_submit_service.py",
            "ai/services/ai_inference/emlis_ai_current_input_bundle.py",
            "ai/services/ai_inference/emlis_ai_public_feedback_meta.py",
            "ai/services/ai_inference/emlis_ai_evidence_ledger_service.py",
            "ai/services/ai_inference/emlis_ai_perspective_observers.py",
            (
                "ai/services/ai_inference/"
                "emlis_ai_observation_integrator_service.py"
            ),
            "ai/services/ai_inference/emlis_ai_safety_triage.py",
        }
    ),
    2: frozenset(
        {
            "ai/tests/helpers/emlis_nls_v3_s2_sample_registry.py",
            "ai/tests/test_emlis_nls_v3_s2_sample_registry.py",
            "ai/tests/schemas/emlis_nls_v3_sample_case_v1.schema.json",
            "ai/tests/schemas/emlis_nls_v3_coverage_matrix_v1.schema.json",
            (
                "ai/tests/schemas/"
                "emlis_nls_v3_sample_batch_manifest_v1.schema.json"
            ),
            "ai/tests/schemas/emlis_nls_v3_corpus_registry_v1.schema.json",
            "ai/tests/fixtures/emlis_nls_v3_s2_corpus_registry_20260714.json",
            "ai/tests/fixtures/emlis_nls_v3/contract/valid_v1.jsonl",
            "ai/tests/fixtures/emlis_nls_v3/contract/invalid_v1.jsonl",
            "ai/tests/fixtures/emlis_nls_v3/contract/legacy_v1.jsonl",
            (
                "ai/tests/test_emlis_nls_v3_recovery_epoch001_"
                "step02_independent_negative.py"
            ),
        }
    ),
    3: frozenset(
        {
            "ai/services/ai_inference/emlis_ai_nls_v3_artifact_contract.py",
            "ai/tests/test_emlis_nls_v3_s3_strict_artifact_contract.py",
            (
                "ai/tests/schemas/"
                "emlis_nls_v3_case_evidence_receipt_v2.schema.json"
            ),
            (
                "ai/tests/fixtures/emlis_nls_v3/contract/"
                "step3_valid_artifacts_v1.json"
            ),
            (
                "ai/tests/fixtures/"
                "emlis_nls_v3_s3_red_attack_catalog_20260715.json"
            ),
            (
                "ai/tests/fixtures/"
                "emlis_nls_v3_s3_contract_receipt_20260715.json"
            ),
            (
                "ai/tests/test_emlis_nls_v3_recovery_epoch001_"
                "step03_independent_negative.py"
            ),
        }
    ),
    4: frozenset(
        {
            "ai/services/ai_inference/emlis_ai_refined_source_partition_v3.py",
            (
                "ai/services/ai_inference/"
                "emlis_ai_semantic_obligation_inventory_v3.py"
            ),
            (
                "ai/services/ai_inference/"
                "emlis_ai_grounded_observation_semantic_restatement_v3.py"
            ),
            "ai/services/ai_inference/emlis_ai_evidence_ledger_service.py",
            "ai/services/ai_inference/emlis_ai_grounded_observation_plan.py",
            (
                "ai/services/ai_inference/"
                "emlis_ai_observation_stage_context_v3.py"
            ),
            "ai/tests/test_emlis_nls_v3_s4_semantic_obligation_inventory.py",
            (
                "ai/tests/test_emlis_nls_v3_recovery_epoch001_"
                "step04_independent_negative.py"
            ),
        }
    ),
    5: frozenset(
        {
            "ai/services/ai_inference/emlis_ai_refined_source_partition_v3.py",
            (
                "ai/services/ai_inference/"
                "emlis_ai_semantic_obligation_inventory_v3.py"
            ),
            "ai/services/ai_inference/emlis_ai_content_selection_v3.py",
            (
                "ai/services/ai_inference/"
                "emlis_ai_observation_stage_context_v3.py"
            ),
            "ai/tests/test_emlis_nls_v3_s5_content_selection_stage_context.py",
            (
                "ai/tests/test_emlis_nls_v3_recovery_epoch001_"
                "step05_independent_negative.py"
            ),
        }
    ),
    6: frozenset(
        {
            (
                "ai/services/ai_inference/"
                "emlis_ai_discourse_graph_planner_v3.py"
            ),
            "ai/services/ai_inference/emlis_ai_nls_v3_artifact_contract.py",
            "ai/tests/test_emlis_nls_v3_s6_discourse_graph_planner.py",
            (
                "ai/tests/test_emlis_nls_v3_recovery_epoch001_"
                "step06_independent_negative.py"
            ),
        }
    ),
    7: frozenset(
        {
            "ai/services/ai_inference/emlis_ai_typed_surface_ast_v3.py",
            "ai/services/ai_inference/emlis_ai_canonical_renderer_v3.py",
            (
                "ai/services/ai_inference/"
                "emlis_ai_surface_grammar_catalog_v3.py"
            ),
            "ai/services/ai_inference/emlis_ai_nls_v3_artifact_contract.py",
            "ai/tests/test_emlis_nls_v3_s7_typed_ast_canonical_renderer.py",
            (
                "ai/tests/test_emlis_nls_v3_recovery_epoch001_"
                "step07_independent_negative.py"
            ),
        }
    ),
    8: frozenset(
        {
            (
                "ai/services/ai_inference/"
                "emlis_ai_body_semantic_atom_parser_v3.py"
            ),
            (
                "ai/services/ai_inference/"
                "emlis_ai_independent_semantic_matcher_v3.py"
            ),
            (
                "ai/services/ai_inference/"
                "emlis_ai_step8_artifact_contract_v3.py"
            ),
            (
                "ai/services/ai_inference/"
                "emlis_ai_surface_grammar_catalog_v3.py"
            ),
            (
                "ai/services/ai_inference/"
                "emlis_ai_surface_grammar_catalog_v3_step8.py"
            ),
            (
                "ai/tests/"
                "test_emlis_nls_v3_s8_body_parser_independent_matcher.py"
            ),
            (
                "ai/tests/test_emlis_nls_v3_recovery_epoch001_"
                "step08_independent_negative.py"
            ),
        }
    ),
    9: frozenset(
        {
            (
                "ai/services/ai_inference/"
                "emlis_ai_step9_dependency_manifest_v3.py"
            ),
            (
                "ai/services/ai_inference/"
                "emlis_ai_step9_artifact_contract_v3.py"
            ),
            "ai/services/ai_inference/emlis_ai_semantic_hard_gate_v3.py",
            "ai/services/ai_inference/emlis_ai_lexicographic_selector_v3.py",
            "ai/services/ai_inference/emlis_ai_bounded_recovery_v3.py",
            (
                "ai/services/ai_inference/"
                "emlis_ai_step9_recovery_epoch001_successor_v3.py"
            ),
            "ai/tests/test_emlis_nls_v3_s9_hard_gate_selector_recovery.py",
            (
                "ai/tests/test_emlis_nls_v3_recovery_epoch001_"
                "step09_independent_negative.py"
            ),
        }
    ),
    10: frozenset(
        {
            (
                "ai/services/ai_inference/"
                "emlis_ai_dormant_runtime_adapter_v3.py"
            ),
            "ai/services/ai_inference/emlis_ai_reply_service.py",
            (
                "ai/services/ai_inference/"
                "emlis_ai_step10_app_reachable_contract_v3.py"
            ),
            "ai/services/ai_inference/emlis_ai_step10_evidence_v3.py",
            "ai/tools/emlis_nls_v3_batch_run.py",
            "ai/tools/emlis_nls_v3_cumulative_regression.py",
            "ai/tools/emlis_nls_v3_output_diff.py",
            "ai/tools/emlis_nls_v3_receipt_verify.py",
            (
                "ai/tests/schemas/"
                "emlis_nls_v3_case_evidence_receipt_v3.schema.json"
            ),
            (
                "ai/tests/"
                "test_emlis_nls_v3_s10_dormant_runtime_batch_evidence.py"
            ),
            (
                "ai/tests/test_emlis_nls_v3_recovery_epoch001_"
                "step10_independent_negative.py"
            ),
        }
    ),
}
_CROSS_STEP_SEEDS = frozenset(
    {
        (
            "ai/services/ai_inference/"
            "emlis_ai_recovery_epoch001_canonical_current_closure_v3.py"
        ),
        (
            "ai/services/ai_inference/"
            "emlis_ai_recovery_epoch001_step_completion_receipt_v3.py"
        ),
        (
            "ai/tools/"
            "emlis_nls_v3_recovery_epoch001_closure_receipt_verify.py"
        ),
        (
            "ai/services/ai_inference/"
            "emlis_ai_recovery_epoch001_current_step_requirement_registry_v3.py"
        ),
        (
            "ai/services/ai_inference/"
            "emlis_ai_recovery_epoch001_accepted_test_run_receipt_v3.py"
        ),
        (
            "ai/tools/"
            "emlis_nls_v3_recovery_epoch001_current_step_proof_run.py"
        ),
        (
            "ai/tools/"
            "emlis_nls_v3_recovery_epoch001_all11_receipt_issue.py"
        ),
        (
            "ai/tests/"
            "test_emlis_nls_v3_recovery_epoch001_current_closure_completion_red.py"
        ),
        (
            "ai/tests/"
            "test_emlis_nls_v3_recovery_epoch001_proved_receipt_contract_red.py"
        ),
        (
            "ai/tests/test_emlis_nls_v3_recovery_epoch001_"
            "step00_independent_negative.py"
        ),
        (
            "ai/tests/test_emlis_nls_v3_recovery_epoch001_"
            "step01_independent_negative.py"
        ),
        (
            "ai/tests/test_emlis_nls_v3_recovery_epoch001_"
            "step02_independent_negative.py"
        ),
        (
            "ai/tests/test_emlis_nls_v3_recovery_epoch001_"
            "step03_independent_negative.py"
        ),
        (
            "ai/tests/test_emlis_nls_v3_recovery_epoch001_"
            "step04_independent_negative.py"
        ),
        (
            "ai/tests/test_emlis_nls_v3_recovery_epoch001_"
            "step05_independent_negative.py"
        ),
        (
            "ai/tests/test_emlis_nls_v3_recovery_epoch001_"
            "step06_independent_negative.py"
        ),
        (
            "ai/tests/test_emlis_nls_v3_recovery_epoch001_"
            "step07_independent_negative.py"
        ),
        (
            "ai/tests/test_emlis_nls_v3_recovery_epoch001_"
            "step08_independent_negative.py"
        ),
        (
            "ai/tests/test_emlis_nls_v3_recovery_epoch001_"
            "step09_independent_negative.py"
        ),
        (
            "ai/tests/test_emlis_nls_v3_recovery_epoch001_"
            "step10_independent_negative.py"
        ),
        "ai/tests/conftest.py",
        (
            "ai/services/ai_inference/"
            "emlis_ai_recovery_epoch001_source_baseline_manifest_v3.py"
        ),
        "ai/tests/test_emlis_nls_v3_recovery_epoch001_prerequisite_red.py",
    }
)


def _canonical_json_bytes(value: Any) -> bytes:
    return canonical_json_bytes(value)


def _artifact_sha256(value: Any) -> str:
    return artifact_sha256(value)


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_blob_sha1(path: Path) -> str:
    payload = path.read_bytes()
    return hashlib.sha1(
        f"blob {len(payload)}\0".encode("ascii") + payload,
        usedforsecurity=False,
    ).hexdigest()


def _commit_tree_blob_index(
    repo_root: Path,
    source_commit: str,
    relative_paths: Iterable[str],
) -> dict[str, str]:
    wanted = set(relative_paths)
    completed = subprocess.run(
        ["git", "ls-tree", "-r", "-z", source_commit, "--", "ai"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        timeout=5,
    )
    result: dict[str, str] = {}
    for row in (item for item in completed.stdout.split(b"\0") if item):
        metadata, separator, encoded_path = row.partition(b"\t")
        fields = metadata.split()
        path = encoded_path.decode("utf-8", errors="strict")
        if (
            separator == b"\t"
            and len(fields) == 3
            and fields[0] in {b"100644", b"100755"}
            and fields[1] == b"blob"
            and path in wanted
        ):
            blob_sha1 = fields[2].decode("ascii", errors="strict")
            if _BLOB_RE.fullmatch(blob_sha1) is not None:
                result[path] = blob_sha1
    return result


def _module_index(
    repo_root: Path,
) -> tuple[dict[str, Path], dict[Path, str]]:
    ai_root = repo_root / "ai"
    aliases: dict[str, list[Path]] = {}
    by_path: dict[Path, str] = {}
    for path in sorted(ai_root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        relative = path.relative_to(repo_root)
        parts = list(relative.parts)
        if parts[-1] == "__init__.py":
            parts = parts[:-1]
        else:
            parts[-1] = Path(parts[-1]).stem
        if not parts:
            continue
        full_module = ".".join(parts)
        candidates = {full_module}
        for local_root in (
            ai_root / "services" / "ai_inference",
            ai_root / "tests",
            ai_root / "tests" / "helpers",
            ai_root / "tools",
        ):
            try:
                local = path.relative_to(local_root)
            except ValueError:
                continue
            local_parts = list(local.parts)
            if local_parts[-1] == "__init__.py":
                local_parts = local_parts[:-1]
            else:
                local_parts[-1] = Path(local_parts[-1]).stem
            if local_parts:
                candidates.add(".".join(local_parts))
        for candidate in candidates:
            aliases.setdefault(candidate, []).append(path)
        by_path[path] = full_module
    by_module = {
        module: paths[0]
        for module, paths in aliases.items()
        if len(set(paths)) == 1
    }
    return by_module, by_path


def _source_commit(repo_root: Path) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
        timeout=5,
    )
    value = completed.stdout.strip()
    if _COMMIT_RE.fullmatch(value) is None:
        raise ValueError("source_commit_invalid")
    return value


def _imported_local_modules(
    path: Path,
    module: str,
    index: Mapping[str, Path],
) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: set[str] = set()
    package = module.rpartition(".")[0]
    for node in ast.walk(tree):
        candidates: list[str]
        if isinstance(node, ast.Import):
            candidates = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            raw = node.module or ""
            if node.level:
                package_parts = package.split(".") if package else []
                keep = max(0, len(package_parts) - node.level + 1)
                prefix = ".".join(package_parts[:keep])
                base = ".".join(part for part in (prefix, raw) if part)
            else:
                base = raw
            candidates = [base]
            candidates.extend(
                ".".join(part for part in (base, alias.name) if part)
                for alias in node.names
                if alias.name != "*"
            )
        elif (
            isinstance(node, ast.Call)
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and type(node.args[0].value) is str
            and (
                (
                    isinstance(node.func, ast.Name)
                    and node.func.id in {"__import__", "import_module"}
                )
                or (
                    isinstance(node.func, ast.Attribute)
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "importlib"
                    and node.func.attr == "import_module"
                )
            )
        ):
            candidates = [node.args[0].value]
        else:
            continue
        for candidate in candidates:
            if candidate in index:
                found.add(candidate)
    return found


def _expanded_paths(
    repo_root: Path,
    seeds: Iterable[str],
    index: Mapping[str, Path],
    reverse: Mapping[Path, str],
) -> tuple[set[str], set[tuple[str, str]]]:
    paths = set(seeds)
    pending = list(sorted(paths))
    edges: set[tuple[str, str]] = set()
    while pending:
        relative = pending.pop()
        absolute = repo_root / relative
        if not absolute.is_file():
            raise FileNotFoundError(relative)
        if absolute.suffix != ".py":
            continue
        if absolute in reverse:
            module = reverse[absolute]
        else:
            module = absolute.stem
        for imported in sorted(
            _imported_local_modules(absolute, module, index)
        ):
            target = index[imported].relative_to(repo_root).as_posix()
            edges.add((relative, target))
            if target not in paths:
                paths.add(target)
                pending.append(target)
    return paths, edges


def _dependency_closure(
    repo_root: Path,
    index: Mapping[str, Path],
    reverse: Mapping[Path, str],
) -> list[dict[str, str]]:
    entry_path = repo_root / _DEPENDENCY_ENTRY_PATH
    entry_module = reverse[entry_path]
    pending = [entry_module]
    visited: set[str] = set()
    while pending:
        module = pending.pop()
        if module in visited:
            continue
        visited.add(module)
        pending.extend(
            sorted(
                _imported_local_modules(index[module], module, index)
                - visited
            )
        )
    return [
        {
            "path": index[module].relative_to(repo_root).as_posix(),
            "sha256": _file_sha256(index[module]),
        }
        for module in sorted(
            visited,
            key=lambda item: index[item].relative_to(repo_root).as_posix(),
        )
    ]


def _role(path: str) -> str:
    if path in _HISTORICAL_EVIDENCE_SEEDS:
        return "immutable_historical_evidence"
    if "current_step_requirement_registry" in path:
        return "requirement_registry_owner"
    if "accepted_test_run_receipt" in path:
        return "accepted_test_run_receipt_owner"
    if "step_completion_receipt" in path:
        return "current_step_completion_receipt_owner"
    if "closure_receipt_verify" in path:
        return "independent_verifier"
    if "current_step_proof_run" in path:
        return "current_step_proof_runner"
    if "all11_receipt_issue" in path:
        return "all11_receipt_issuer"
    if "independent_negative.py" in path:
        return "dedicated_independent_negative_source"
    if path.startswith("ai/tools/"):
        return "tool"
    if path.startswith("ai/tests/"):
        return "test_or_fixture"
    if path.endswith("_receipt_v3.py"):
        return "completion_receipt_owner"
    if "canonical_current_closure" in path:
        return "canonical_current_closure_owner"
    if "recovery_epoch001_successor" in path:
        return "standalone_step9_successor"
    if "runtime" in path or "step10" in path:
        return "dormant_runtime_or_evidence"
    return "semantic_or_shared_owner"


def _file_rows(repo_root: Path, paths: Iterable[str]) -> list[dict[str, str]]:
    return [
        {
            "path": path,
            "role": _role(path),
            "sha256": _file_sha256(repo_root / path),
            "git_blob_sha1": _git_blob_sha1(repo_root / path),
        }
        for path in sorted(set(paths))
    ]


def _graph_material(
    *,
    source_commit: str,
    dependency_rows: list[dict[str, str]],
    dependency_root: str,
    files: list[dict[str, str]],
    edges: list[dict[str, str]],
    step_views: dict[str, list[str]],
    views: dict[str, list[str]],
) -> dict[str, Any]:
    return {
        "schema_version": (
            RECOVERY_EPOCH001_CANONICAL_CURRENT_CLOSURE_SCHEMA
        ),
        "candidate_version_id": RECOVERY_EPOCH001_CANDIDATE_VERSION_ID,
        "scope": RECOVERY_EPOCH001_SCOPE,
        "disposition": RECOVERY_EPOCH001_DISPOSITION,
        "source_predecessor_commit": (
            RECOVERY_EPOCH001_SOURCE_PREDECESSOR_COMMIT
        ),
        "authority_entry_commit": RECOVERY_EPOCH001_AUTHORITY_ENTRY_COMMIT,
        "source_commit": source_commit,
        "dependency_entry_path": _DEPENDENCY_ENTRY_PATH,
        "dependency_closure_count": len(dependency_rows),
        "dependency_closure": dependency_rows,
        "source_dependency_closure_sha256": dependency_root,
        "files": files,
        "edges": edges,
        "step_views": step_views,
        "views": views,
    }


def _derive(repo_root: Path) -> dict[str, Any]:
    root = repo_root.resolve()
    source_commit = _source_commit(root)
    index, reverse = _module_index(root)
    step_views: dict[str, list[str]] = {}
    all_paths: set[str] = set()
    all_edges: set[tuple[str, str]] = set()
    for step, seeds in sorted(_STEP_SEEDS.items()):
        paths, edges = _expanded_paths(root, seeds, index, reverse)
        step_views[f"step_{step}"] = sorted(paths)
        all_paths.update(paths)
        all_edges.update(edges)
    proof_paths, proof_edges = _expanded_paths(
        root,
        _CROSS_STEP_SEEDS,
        index,
        reverse,
    )
    all_paths.update(proof_paths)
    all_edges.update(proof_edges)
    historical_paths, historical_edges = _expanded_paths(
        root,
        _HISTORICAL_EVIDENCE_SEEDS,
        index,
        reverse,
    )
    all_paths.update(historical_paths)
    all_edges.update(historical_edges)
    dependency_rows = _dependency_closure(root, index, reverse)
    dependency_paths = {row["path"] for row in dependency_rows}
    all_paths.update(dependency_paths)
    semantic_paths = set().union(
        *(set(step_views[f"step_{step}"]) for step in range(10))
    )
    runtime_paths = set(step_views["step_10"]) | dependency_paths
    views = {
        "semantic_execution": sorted(semantic_paths),
        "dormant_runtime": sorted(runtime_paths),
        "completion_proof": sorted(proof_paths),
        "all_relevant": sorted(all_paths),
    }
    files = _file_rows(root, all_paths)
    edges = [
        {"source": source, "target": target}
        for source, target in sorted(all_edges)
    ]
    dependency_root = _artifact_sha256(dependency_rows)
    graph_material = _graph_material(
        source_commit=source_commit,
        dependency_rows=dependency_rows,
        dependency_root=dependency_root,
        files=files,
        edges=edges,
        step_views=step_views,
        views=views,
    )
    canonical_root = _artifact_sha256(graph_material)
    return {
        "schema_version": (
            RECOVERY_EPOCH001_CANONICAL_CURRENT_CLOSURE_SCHEMA
        ),
        "candidate_version_id": RECOVERY_EPOCH001_CANDIDATE_VERSION_ID,
        "scope": RECOVERY_EPOCH001_SCOPE,
        "disposition": RECOVERY_EPOCH001_DISPOSITION,
        "source_predecessor_commit": (
            RECOVERY_EPOCH001_SOURCE_PREDECESSOR_COMMIT
        ),
        "authority_entry_commit": RECOVERY_EPOCH001_AUTHORITY_ENTRY_COMMIT,
        "source_commit": source_commit,
        "dependency_entry_path": _DEPENDENCY_ENTRY_PATH,
        "dependency_closure_count": len(dependency_rows),
        "dependency_closure": dependency_rows,
        "source_dependency_closure_sha256": dependency_root,
        "canonical_current_closure_sha256": canonical_root,
        "files": files,
        "edges": edges,
        "step_views": step_views,
        "views": views,
        "full_graph_sha256": canonical_root,
        "body_free": True,
    }


def fresh_recovery_epoch001_canonical_current_closure(
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Derive the canonical current graph from actual repository bytes."""

    return _derive(_REPO_ROOT if repo_root is None else Path(repo_root))


def fresh_recovery_epoch001_source_closure_sha256(
    *,
    repo_root: Path | None = None,
) -> str:
    return fresh_recovery_epoch001_canonical_current_closure(
        repo_root=repo_root
    )["source_dependency_closure_sha256"]


def fresh_recovery_epoch001_live_dependency_closure_sha256(
    *,
    repo_root: Path | None = None,
) -> str:
    return fresh_recovery_epoch001_canonical_current_closure(
        repo_root=repo_root
    )["source_dependency_closure_sha256"]


def recovery_epoch001_source_file_sha256(
    path: str,
    *,
    repo_root: Path | None = None,
) -> str | None:
    if type(path) is not str:
        return None
    graph = fresh_recovery_epoch001_canonical_current_closure(
        repo_root=repo_root
    )
    return next(
        (
            row["sha256"]
            for row in graph["files"]
            if row["path"] == path
        ),
        None,
    )


def _validate_recovery_epoch001_canonical_current_closure_shape_impl(
    value: Any,
    *,
    repo_root: Path | None = None,
) -> tuple[str, ...]:
    """Validate identity, actual bytes, graph edges, roles, and proof views."""

    if type(value) is not dict:
        return ("RECOVERY_CANONICAL_CURRENT_CLOSURE_ENTRY_INVALID",)
    issues: set[str] = set()
    expected: dict[str, Any] | None = None
    try:
        expected = fresh_recovery_epoch001_canonical_current_closure(
            repo_root=repo_root
        )
    except (
        FileNotFoundError,
        KeyError,
        OSError,
        subprocess.SubprocessError,
        SyntaxError,
        UnicodeError,
        ValueError,
    ):
        issues.add("RECOVERY_CANONICAL_CURRENT_CLOSURE_REQUIRED_SEED_MISSING")
    expected_keys = {
        "schema_version",
        "candidate_version_id",
        "scope",
        "disposition",
        "source_predecessor_commit",
        "authority_entry_commit",
        "source_commit",
        "dependency_entry_path",
        "dependency_closure_count",
        "dependency_closure",
        "source_dependency_closure_sha256",
        "canonical_current_closure_sha256",
        "files",
        "edges",
        "step_views",
        "views",
        "full_graph_sha256",
        "body_free",
    }
    if set(value) != expected_keys:
        issues.add("RECOVERY_CANONICAL_CURRENT_CLOSURE_ENTRY_INVALID")
    if (
        value.get("schema_version")
        != RECOVERY_EPOCH001_CANONICAL_CURRENT_CLOSURE_SCHEMA
        or value.get("candidate_version_id")
        != RECOVERY_EPOCH001_CANDIDATE_VERSION_ID
        or value.get("scope") != RECOVERY_EPOCH001_SCOPE
        or value.get("disposition") != RECOVERY_EPOCH001_DISPOSITION
        or value.get("source_predecessor_commit")
        != RECOVERY_EPOCH001_SOURCE_PREDECESSOR_COMMIT
        or value.get("authority_entry_commit")
        != RECOVERY_EPOCH001_AUTHORITY_ENTRY_COMMIT
        or type(value.get("source_commit")) is not str
        or _COMMIT_RE.fullmatch(value.get("source_commit", "")) is None
        or value.get("dependency_entry_path") != _DEPENDENCY_ENTRY_PATH
    ):
        issues.add(
            "RECOVERY_CANONICAL_CURRENT_CLOSURE_CANDIDATE_IDENTITY_INVALID"
        )
    if value.get("body_free") is not True:
        issues.add("RECOVERY_CANONICAL_CURRENT_CLOSURE_PRIVATE_BODY_INGRESS")
    if expected is not None:
        if value.get("source_commit") != expected["source_commit"]:
            issues.add(
                "RECOVERY_CANONICAL_CURRENT_CLOSURE_CANDIDATE_IDENTITY_INVALID"
            )
        actual_dependency = value.get("dependency_closure")
        if type(actual_dependency) is not list:
            issues.add("RECOVERY_CANONICAL_CURRENT_CLOSURE_ENTRY_INVALID")
        else:
            if any(
                type(row) is not dict
                or set(row) != {"path", "sha256"}
                or type(row.get("path")) is not str
                or type(row.get("sha256")) is not str
                for row in actual_dependency
            ):
                issues.add(
                    "RECOVERY_CANONICAL_CURRENT_CLOSURE_ENTRY_INVALID"
                )
            actual_paths = {
                row["path"]
                for row in actual_dependency
                if type(row) is dict and type(row.get("path")) is str
            }
            expected_paths = {
                row["path"] for row in expected["dependency_closure"]
            }
            if expected_paths - actual_paths:
                issues.add(
                    "RECOVERY_CANONICAL_CURRENT_CLOSURE_REQUIRED_FILE_MISSING"
                )
            if actual_paths - expected_paths:
                issues.add("RECOVERY_CANONICAL_CURRENT_CLOSURE_EXTRA_FILE")
            if actual_dependency != expected["dependency_closure"]:
                issues.add(
                    "RECOVERY_CANONICAL_CURRENT_CLOSURE_FILE_HASH_DRIFT"
                )
        if (
            value.get("dependency_closure_count")
            != expected["dependency_closure_count"]
            or value.get("source_dependency_closure_sha256")
            != expected["source_dependency_closure_sha256"]
            or value.get("canonical_current_closure_sha256")
            != expected["canonical_current_closure_sha256"]
            or _SHA_RE.fullmatch(
                str(value.get("canonical_current_closure_sha256", ""))
            )
            is None
        ):
            issues.add(
                "RECOVERY_CANONICAL_CURRENT_CLOSURE_FILE_HASH_DRIFT"
            )
        if (
            value.get("source_dependency_closure_sha256")
            == _PRE_IMPLEMENTATION_DEPENDENCY_ROOT
            or _SUCCESSOR_PATH
            not in {
                row["path"]
                for row in expected["dependency_closure"]
                if type(row) is dict and type(row.get("path")) is str
            }
        ):
            issues.add(
                "RECOVERY_CANONICAL_CURRENT_CLOSURE_VIEW_BINDING_DRIFT"
            )
        actual_files = value.get("files")
        if type(actual_files) is not list:
            issues.add("RECOVERY_CANONICAL_CURRENT_CLOSURE_ENTRY_INVALID")
            actual_files = []
        elif any(
            type(row) is not dict
            or set(row) != {"path", "role", "sha256", "git_blob_sha1"}
            or type(row.get("path")) is not str
            for row in actual_files
        ):
            issues.add("RECOVERY_CANONICAL_CURRENT_CLOSURE_ENTRY_INVALID")
        actual_file_by_path = {
            row.get("path"): row
            for row in actual_files
            if type(row) is dict and type(row.get("path")) is str
        }
        if len(actual_file_by_path) != len(actual_files):
            issues.add("RECOVERY_CANONICAL_CURRENT_CLOSURE_ENTRY_INVALID")
        expected_file_by_path = {
            row["path"]: row for row in expected["files"]
        }
        if expected_file_by_path.keys() - actual_file_by_path.keys():
            issues.add(
                "RECOVERY_CANONICAL_CURRENT_CLOSURE_REQUIRED_FILE_MISSING"
            )
        if actual_file_by_path.keys() - expected_file_by_path.keys():
            issues.add("RECOVERY_CANONICAL_CURRENT_CLOSURE_EXTRA_FILE")
        try:
            committed_blobs = _commit_tree_blob_index(
                (_REPO_ROOT if repo_root is None else Path(repo_root))
                .resolve(),
                expected["source_commit"],
                expected_file_by_path,
            )
        except (
            OSError,
            subprocess.SubprocessError,
            UnicodeError,
            ValueError,
        ):
            committed_blobs = {}
        for path in expected_file_by_path.keys() & actual_file_by_path.keys():
            actual_row = actual_file_by_path[path]
            expected_row = expected_file_by_path[path]
            if actual_row.get("sha256") != expected_row["sha256"]:
                issues.add(
                    "RECOVERY_CANONICAL_CURRENT_CLOSURE_FILE_HASH_DRIFT"
                )
            if actual_row.get("git_blob_sha1") != expected_row["git_blob_sha1"]:
                issues.add(
                    "RECOVERY_CANONICAL_CURRENT_CLOSURE_GIT_BLOB_DRIFT"
                )
            if actual_row.get("role") != expected_row["role"]:
                issues.add(
                    "RECOVERY_CANONICAL_CURRENT_CLOSURE_ROLE_BINDING_DRIFT"
                )
            if committed_blobs.get(path) != expected_row["git_blob_sha1"]:
                issues.add(
                    "RECOVERY_CANONICAL_CURRENT_CLOSURE_GIT_BLOB_DRIFT"
                )
        submitted_step_views = value.get("step_views")
        submitted_views = value.get("views")
        semantic_execution = (
            submitted_views.get("semantic_execution")
            if type(submitted_views) is dict
            else None
        )
        if (
            type(submitted_step_views) is not dict
            or any(
                type(paths) is not list
                or any(type(path) is not str for path in paths)
                for paths in (
                    submitted_step_views.values()
                    if type(submitted_step_views) is dict
                    else ()
                )
            )
            or type(semantic_execution) is not list
            or any(type(path) is not str for path in semantic_execution)
        ):
            issues.add(
                "RECOVERY_CANONICAL_CURRENT_CLOSURE_VIEW_BINDING_DRIFT"
            )
        semantic_execution_paths = (
            frozenset(semantic_execution)
            if type(semantic_execution) is list
            and all(type(path) is str for path in semantic_execution)
            else frozenset()
        )
        for historical_path in _HISTORICAL_EVIDENCE_SEEDS:
            historical_row = actual_file_by_path.get(historical_path)
            if (
                historical_row is None
                or historical_row.get("role")
                != "immutable_historical_evidence"
                or any(
                    historical_path in paths
                    for paths in (
                        submitted_step_views.values()
                        if type(submitted_step_views) is dict
                        else ()
                    )
                    if type(paths) is list
                )
                or historical_path in semantic_execution_paths
            ):
                issues.add(
                    "RECOVERY_CANONICAL_CURRENT_CLOSURE_ROLE_BINDING_DRIFT"
                )
        actual_edges = value.get("edges")
        if type(actual_edges) is not list:
            issues.add("RECOVERY_CANONICAL_CURRENT_CLOSURE_ENTRY_INVALID")
            actual_edges = []
        if actual_edges != expected["edges"]:
            issues.add(
                "RECOVERY_CANONICAL_CURRENT_CLOSURE_REQUIRED_EDGE_MISSING"
            )
        actual_edge_pairs: set[tuple[str, str]] = set()
        for edge in actual_edges:
            if (
                type(edge) is not dict
                or set(edge) != {"source", "target"}
                or type(edge.get("source")) is not str
                or type(edge.get("target")) is not str
            ):
                issues.add(
                    "RECOVERY_CANONICAL_CURRENT_CLOSURE_EDGE_TARGET_UNRESOLVED"
                )
                continue
            actual_edge_pairs.add((edge["source"], edge["target"]))
        expected_edge_pairs = {
            (edge["source"], edge["target"])
            for edge in expected["edges"]
        }
        if expected_edge_pairs - actual_edge_pairs:
            issues.add(
                "RECOVERY_CANONICAL_CURRENT_CLOSURE_"
                "EXISTING_LOCAL_IMPORT_UNLISTED"
            )
        if actual_edge_pairs - expected_edge_pairs:
            issues.add(
                "RECOVERY_CANONICAL_CURRENT_CLOSURE_FORBIDDEN_EDGE"
            )
        listed_paths = set(actual_file_by_path)
        for edge in actual_edges:
            if type(edge) is not dict:
                issues.add(
                    "RECOVERY_CANONICAL_CURRENT_CLOSURE_EDGE_TARGET_UNRESOLVED"
                )
                continue
            source = edge.get("source")
            target = edge.get("target")
            if (
                type(source) is not str
                or type(target) is not str
                or source not in listed_paths
                or target not in listed_paths
            ):
                issues.add(
                    "RECOVERY_CANONICAL_CURRENT_CLOSURE_EDGE_TARGET_UNRESOLVED"
                )
            if (
                type(source) is str
                and source.startswith("ai/services/ai_inference/")
                and type(target) is str
                and target.startswith(("ai/tests/", "ai/tools/"))
            ):
                issues.add(
                    "RECOVERY_CANONICAL_CURRENT_CLOSURE_FORBIDDEN_CUE_INGRESS"
                )
                issues.add(
                    "RECOVERY_CANONICAL_CURRENT_CLOSURE_PRIVATE_BODY_INGRESS"
                )
        if (
            submitted_step_views != expected["step_views"]
            or submitted_views != expected["views"]
        ):
            issues.add(
                "RECOVERY_CANONICAL_CURRENT_CLOSURE_VIEW_BINDING_DRIFT"
            )
        completion_view = (
            submitted_views.get("completion_proof")
            if type(submitted_views) is dict
            else None
        )
        if (
            type(completion_view) is not list
            or any(type(path) is not str for path in completion_view)
            or not _CROSS_STEP_SEEDS <= {
                path for path in completion_view if type(path) is str
            }
        ):
            issues.add(
                "RECOVERY_CANONICAL_CURRENT_CLOSURE_"
                "SELF_NORMALIZATION_SCOPE_DRIFT"
            )
        if value.get("full_graph_sha256") != expected["full_graph_sha256"]:
            issues.add(
                "RECOVERY_CANONICAL_CURRENT_CLOSURE_VIEW_BINDING_DRIFT"
            )
        try:
            submitted_material = {
                key: value[key]
                for key in expected
                if key
                not in {
                    "canonical_current_closure_sha256",
                    "full_graph_sha256",
                    "body_free",
                }
            }
            submitted_root = _artifact_sha256(submitted_material)
        except (
            KeyError,
            RecursionError,
            TypeError,
            UnicodeError,
            ValueError,
        ):
            submitted_root = None
        if (
            submitted_root is None
            or value.get("canonical_current_closure_sha256")
            != submitted_root
            or value.get("full_graph_sha256") != submitted_root
        ):
            issues.add(
                "RECOVERY_CANONICAL_CURRENT_CLOSURE_VIEW_BINDING_DRIFT"
            )
    return tuple(sorted(issues))


def validate_recovery_epoch001_canonical_current_closure_shape(
    value: Any,
    *,
    repo_root: Path | None = None,
) -> tuple[str, ...]:
    try:
        return _validate_recovery_epoch001_canonical_current_closure_shape_impl(
            value,
            repo_root=repo_root,
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
        return ("RECOVERY_CANONICAL_CURRENT_CLOSURE_ENTRY_INVALID",)


def validate_recovery_epoch001_canonical_current_closure(
    *,
    repo_root: Path | None = None,
) -> tuple[str, ...]:
    return validate_recovery_epoch001_canonical_current_closure_shape(
        fresh_recovery_epoch001_canonical_current_closure(
            repo_root=repo_root
        ),
        repo_root=repo_root,
    )


def validate_recovery_epoch001_closure_start_end(
    source_closure_start_sha256: Any,
    source_closure_end_sha256: Any,
) -> tuple[str, ...]:
    if (
        type(source_closure_start_sha256) is not str
        or type(source_closure_end_sha256) is not str
        or _SHA_RE.fullmatch(source_closure_start_sha256) is None
        or source_closure_start_sha256 != source_closure_end_sha256
    ):
        return ("RECOVERY_CANONICAL_CURRENT_CLOSURE_START_END_DRIFT",)
    return ()
