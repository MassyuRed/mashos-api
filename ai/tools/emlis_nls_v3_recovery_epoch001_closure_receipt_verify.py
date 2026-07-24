#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""Independent verifier for Recovery Epoch 001 closure and step receipts.

The verifier intentionally does not import either production owner.  It keeps
its own seed/identity tables and independently walks current repository bytes.
"""

import ast
import hashlib
from pathlib import Path
import re
import subprocess
from typing import Any, Iterable, Mapping


_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch001."
    "canonical_current_closure.v1"
)
_CANDIDATE = "nls_v3_rc_0034"
_SCOPE = "RECOVERY_EPOCH001_CANONICAL_CURRENT_CLOSURE_CANDIDATE_ONLY"
_DISPOSITION = "CURRENT_CLOSURE_CANDIDATE_NOT_BASELINE_NOT_CYCLE_ACCEPTANCE"
_PREDECESSOR = "bd62ef0eec2348e3b190ec2a39c3794886ccd10d"
_AUTHORITY_ENTRY = "7a771247ca26ce435d325b5eb484197b1bdec7c2"
_DEPENDENCY_ENTRY = "ai/services/ai_inference/emlis_ai_reply_service.py"
_PRE_IMPLEMENTATION_DEPENDENCY_ROOT = (
    "7d15cc072ac4ac28b6b9ce90676c6238ba08d5f59fd1896a7273ce7d57a7f302"
)
_SUCCESSOR_PATH = (
    "ai/services/ai_inference/"
    "emlis_ai_step9_recovery_epoch001_successor_v3.py"
)
_RECEIPT_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch001."
    "current_step_completion_receipt.v1"
)
_NEXT_BY_STEP = {
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
_RECEIPT_KEYS = frozenset(
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
_SHA_RE = re.compile(r"^[0-9a-f]{64}$")
_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
_BLOB_RE = re.compile(r"^[0-9a-f]{40}$")
_MACHINE_RE = re.compile(r"^[A-Z][A-Z0-9_]{2,127}$")
_BODY_FREE_TOKEN_RE = re.compile(r"^[A-Za-z0-9_./:-]{1,512}$")

_CURRENT_OWNERS = (
    "ai/services/ai_inference/emlis_ai_grounded_observation_plan.py",
    "ai/services/ai_inference/emlis_ai_grounded_human_reception.py",
    "ai/services/ai_inference/emlis_ai_grounded_sentence_surface.py",
    "ai/services/ai_inference/emlis_ai_grounded_observation_gate.py",
    "ai/services/ai_inference/emlis_ai_reply_service.py",
)
_STOPPED_V2 = (
    "ai/services/ai_inference/emlis_ai_grounded_reception_content_plan_v2.py",
    "ai/services/ai_inference/emlis_ai_grounded_reception_candidate_plan_v2.py",
    "ai/services/ai_inference/emlis_ai_grounded_human_reception_v2.py",
    (
        "ai/services/ai_inference/"
        "emlis_ai_grounded_reception_candidate_selector_v2.py"
    ),
)
_HISTORICAL_EVIDENCE = frozenset(_STOPPED_V2)
_STEP_SEEDS: dict[int, frozenset[str]] = {
    0: frozenset(
        {
            "ai/tests/helpers/emlis_nls_v3_s0_s1_baseline.py",
            "ai/tests/test_emlis_nls_v3_s0_s1.py",
            "ai/tests/fixtures/emlis_nls_v3_s0_boundary_20260714.json",
            *_CURRENT_OWNERS,
        }
    ),
    1: frozenset(
        {
            "ai/tests/helpers/emlis_nls_v3_s0_s1_baseline.py",
            "ai/tests/test_emlis_nls_v3_s0_s1.py",
            "ai/tests/fixtures/emlis_nls_v3_s1_input_contract_20260714.json",
            "ai/tests/fixtures/emlis_nls_v3_s1_baseline_receipt_20260714.json",
            *_CURRENT_OWNERS,
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
        }
    ),
    6: frozenset(
        {
            "ai/services/ai_inference/emlis_ai_discourse_graph_planner_v3.py",
            "ai/services/ai_inference/emlis_ai_nls_v3_artifact_contract.py",
            "ai/tests/test_emlis_nls_v3_s6_discourse_graph_planner.py",
        }
    ),
    7: frozenset(
        {
            "ai/services/ai_inference/emlis_ai_typed_surface_ast_v3.py",
            "ai/services/ai_inference/emlis_ai_canonical_renderer_v3.py",
            "ai/services/ai_inference/emlis_ai_surface_grammar_catalog_v3.py",
            "ai/services/ai_inference/emlis_ai_nls_v3_artifact_contract.py",
            "ai/tests/test_emlis_nls_v3_s7_typed_ast_canonical_renderer.py",
        }
    ),
    8: frozenset(
        {
            "ai/services/ai_inference/emlis_ai_body_semantic_atom_parser_v3.py",
            (
                "ai/services/ai_inference/"
                "emlis_ai_independent_semantic_matcher_v3.py"
            ),
            "ai/services/ai_inference/emlis_ai_step8_artifact_contract_v3.py",
            "ai/services/ai_inference/emlis_ai_surface_grammar_catalog_v3.py",
            (
                "ai/services/ai_inference/"
                "emlis_ai_surface_grammar_catalog_v3_step8.py"
            ),
            (
                "ai/tests/"
                "test_emlis_nls_v3_s8_body_parser_independent_matcher.py"
            ),
        }
    ),
    9: frozenset(
        {
            "ai/services/ai_inference/emlis_ai_step9_dependency_manifest_v3.py",
            "ai/services/ai_inference/emlis_ai_step9_artifact_contract_v3.py",
            "ai/services/ai_inference/emlis_ai_semantic_hard_gate_v3.py",
            "ai/services/ai_inference/emlis_ai_lexicographic_selector_v3.py",
            "ai/services/ai_inference/emlis_ai_bounded_recovery_v3.py",
            (
                "ai/services/ai_inference/"
                "emlis_ai_step9_recovery_epoch001_successor_v3.py"
            ),
            "ai/tests/test_emlis_nls_v3_s9_hard_gate_selector_recovery.py",
        }
    ),
    10: frozenset(
        {
            "ai/services/ai_inference/emlis_ai_dormant_runtime_adapter_v3.py",
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
        }
    ),
}
_PROOF_SEEDS = frozenset(
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
            "ai/tests/"
            "test_emlis_nls_v3_recovery_epoch001_current_closure_completion_red.py"
        ),
        "ai/tests/conftest.py",
        (
            "ai/services/ai_inference/"
            "emlis_ai_recovery_epoch001_source_baseline_manifest_v3.py"
        ),
        "ai/tests/test_emlis_nls_v3_recovery_epoch001_prerequisite_red.py",
    }
)


def _normalise_json(value: Any) -> Any:
    import unicodedata

    if value is None or type(value) in (bool, int):
        return value
    if type(value) is str:
        value.encode("utf-8", errors="strict")
        return unicodedata.normalize(
            "NFC",
            value.replace("\r\n", "\n").replace("\r", "\n"),
        )
    if type(value) is list:
        return [_normalise_json(item) for item in value]
    if type(value) is dict:
        result: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("non_string_key")
            normalised_key = _normalise_json(key)
            if normalised_key in result:
                raise ValueError("duplicate_key")
            result[normalised_key] = _normalise_json(item)
        return result
    raise ValueError("unsupported_json_type")


def _canonical_bytes(value: Any) -> bytes:
    import json

    return json.dumps(
        _normalise_json(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8", errors="strict")


def _artifact_sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _top_level_symbols(path: Path) -> set[str]:
    if path.suffix != ".py":
        return set()
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    result: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            result.add(node.name)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = (
                node.targets if isinstance(node, ast.Assign) else [node.target]
            )
            result.update(
                target.id
                for target in targets
                if isinstance(target, ast.Name)
            )
    return result


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
        return all(
            type(key) is str
            and not any(
                token in key.lower()
                for token in (
                    "raw_body",
                    "candidate_body",
                    "prompt_text",
                    "response_text",
                    "user_text",
                )
            )
            and _body_free(item, seen)
            for key, item in value.items()
        )
    finally:
        seen.remove(identity)


def _file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _blob_sha(path: Path) -> str:
    payload = path.read_bytes()
    return hashlib.sha1(
        f"blob {len(payload)}\0".encode("ascii") + payload,
        usedforsecurity=False,
    ).hexdigest()


def _tree_blob_index(
    root: Path,
    source_commit: str,
    relative_paths: Iterable[str],
) -> dict[str, str]:
    wanted = set(relative_paths)
    completed = subprocess.run(
        ["git", "ls-tree", "-r", "-z", source_commit, "--", "ai"],
        cwd=root,
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


def _source_commit(root: Path) -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        timeout=5,
    )
    value = completed.stdout.strip()
    if _COMMIT_RE.fullmatch(value) is None:
        raise ValueError("source_commit_invalid")
    return value


def _index(root: Path) -> tuple[dict[str, Path], dict[Path, str]]:
    aliases: dict[str, list[Path]] = {}
    reverse: dict[Path, str] = {}
    ai_root = root / "ai"
    for path in sorted(ai_root.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        relative = path.relative_to(root)
        parts = list(relative.parts)
        if parts[-1] == "__init__.py":
            parts = parts[:-1]
        else:
            parts[-1] = Path(parts[-1]).stem
        if not parts:
            continue
        full = ".".join(parts)
        names = {full}
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
                names.add(".".join(local_parts))
        for name in names:
            aliases.setdefault(name, []).append(path)
        reverse[path] = full
    return (
        {
            name: paths[0]
            for name, paths in aliases.items()
            if len(set(paths)) == 1
        },
        reverse,
    )


def _imports(path: Path, module: str, index: Mapping[str, Path]) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    package = module.rpartition(".")[0]
    found: set[str] = set()
    for node in ast.walk(tree):
        candidates: list[str]
        if isinstance(node, ast.Import):
            candidates = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            raw = node.module or ""
            if node.level:
                parent = package.split(".") if package else []
                keep = max(0, len(parent) - node.level + 1)
                prefix = ".".join(parent[:keep])
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
        found.update(candidate for candidate in candidates if candidate in index)
    return found


def _expand(
    root: Path,
    seeds: Iterable[str],
    index: Mapping[str, Path],
    reverse: Mapping[Path, str],
) -> tuple[set[str], set[tuple[str, str]]]:
    paths = set(seeds)
    pending = list(sorted(paths))
    edges: set[tuple[str, str]] = set()
    while pending:
        relative = pending.pop()
        absolute = root / relative
        if not absolute.is_file():
            raise FileNotFoundError(relative)
        if absolute.suffix != ".py":
            continue
        module = reverse.get(absolute, absolute.stem)
        for imported in sorted(_imports(absolute, module, index)):
            target = index[imported].relative_to(root).as_posix()
            edges.add((relative, target))
            if target not in paths:
                paths.add(target)
                pending.append(target)
    return paths, edges


def _dependency(
    root: Path,
    index: Mapping[str, Path],
    reverse: Mapping[Path, str],
) -> list[dict[str, str]]:
    entry = root / _DEPENDENCY_ENTRY
    pending = [reverse[entry]]
    seen: set[str] = set()
    while pending:
        module = pending.pop()
        if module in seen:
            continue
        seen.add(module)
        pending.extend(sorted(_imports(index[module], module, index) - seen))
    return [
        {
            "path": index[module].relative_to(root).as_posix(),
            "sha256": _file_sha(index[module]),
        }
        for module in sorted(
            seen,
            key=lambda name: index[name].relative_to(root).as_posix(),
        )
    ]


def _role(path: str) -> str:
    if path in _HISTORICAL_EVIDENCE:
        return "immutable_historical_evidence"
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


def fresh_recovery_epoch001_canonical_current_closure(
    *,
    repo_root: Path,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    index, reverse = _index(root)
    step_views: dict[str, list[str]] = {}
    all_paths: set[str] = set()
    all_edges: set[tuple[str, str]] = set()
    for step, seeds in sorted(_STEP_SEEDS.items()):
        paths, edges = _expand(root, seeds, index, reverse)
        step_views[f"step_{step}"] = sorted(paths)
        all_paths.update(paths)
        all_edges.update(edges)
    proof_paths, proof_edges = _expand(root, _PROOF_SEEDS, index, reverse)
    all_paths.update(proof_paths)
    all_edges.update(proof_edges)
    historical_paths, historical_edges = _expand(
        root,
        _HISTORICAL_EVIDENCE,
        index,
        reverse,
    )
    all_paths.update(historical_paths)
    all_edges.update(historical_edges)
    dependency = _dependency(root, index, reverse)
    dependency_paths = {row["path"] for row in dependency}
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
    files = [
        {
            "path": path,
            "role": _role(path),
            "sha256": _file_sha(root / path),
            "git_blob_sha1": _blob_sha(root / path),
        }
        for path in sorted(all_paths)
    ]
    edges = [
        {"source": source, "target": target}
        for source, target in sorted(all_edges)
    ]
    dependency_root = _artifact_sha256(dependency)
    material = {
        "schema_version": _SCHEMA,
        "candidate_version_id": _CANDIDATE,
        "scope": _SCOPE,
        "disposition": _DISPOSITION,
        "source_predecessor_commit": _PREDECESSOR,
        "authority_entry_commit": _AUTHORITY_ENTRY,
        "source_commit": _source_commit(root),
        "dependency_entry_path": _DEPENDENCY_ENTRY,
        "dependency_closure_count": len(dependency),
        "dependency_closure": dependency,
        "source_dependency_closure_sha256": dependency_root,
        "files": files,
        "edges": edges,
        "step_views": step_views,
        "views": views,
    }
    graph_root = _artifact_sha256(material)
    return {
        **material,
        "canonical_current_closure_sha256": graph_root,
        "full_graph_sha256": graph_root,
        "body_free": True,
    }


def _verify_recovery_epoch001_canonical_current_closure_impl(
    value: Any,
    *,
    repo_root: Path,
) -> tuple[str, ...]:
    if type(value) is not dict:
        return ("RECOVERY_CANONICAL_CURRENT_CLOSURE_ENTRY_INVALID",)
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
        return ("RECOVERY_CANONICAL_CURRENT_CLOSURE_REQUIRED_SEED_MISSING",)
    issues: set[str] = set()
    if set(value) != set(expected):
        issues.add("RECOVERY_CANONICAL_CURRENT_CLOSURE_ENTRY_INVALID")
    if (
        value.get("schema_version") != _SCHEMA
        or value.get("candidate_version_id") != _CANDIDATE
        or value.get("scope") != _SCOPE
        or value.get("disposition") != _DISPOSITION
        or value.get("source_predecessor_commit") != _PREDECESSOR
        or value.get("authority_entry_commit") != _AUTHORITY_ENTRY
        or value.get("dependency_entry_path") != _DEPENDENCY_ENTRY
        or value.get("source_commit") != expected["source_commit"]
        or _COMMIT_RE.fullmatch(str(value.get("source_commit", ""))) is None
    ):
        issues.add(
            "RECOVERY_CANONICAL_CURRENT_CLOSURE_CANDIDATE_IDENTITY_INVALID"
        )
    if value.get("body_free") is not True:
        issues.add("RECOVERY_CANONICAL_CURRENT_CLOSURE_PRIVATE_BODY_INGRESS")
    actual_dependency = value.get("dependency_closure")
    if type(actual_dependency) is not list:
        issues.add("RECOVERY_CANONICAL_CURRENT_CLOSURE_ENTRY_INVALID")
        actual_dependency = []
    elif any(
        type(row) is not dict
        or set(row) != {"path", "sha256"}
        or type(row.get("path")) is not str
        or type(row.get("sha256")) is not str
        for row in actual_dependency
    ):
        issues.add("RECOVERY_CANONICAL_CURRENT_CLOSURE_ENTRY_INVALID")
    dependency_paths = {
        row["path"]
        for row in actual_dependency
        if type(row) is dict and type(row.get("path")) is str
    }
    expected_dependency_paths = {
        row["path"] for row in expected["dependency_closure"]
    }
    if expected_dependency_paths - dependency_paths:
        issues.add("RECOVERY_CANONICAL_CURRENT_CLOSURE_REQUIRED_FILE_MISSING")
    if dependency_paths - expected_dependency_paths:
        issues.add("RECOVERY_CANONICAL_CURRENT_CLOSURE_EXTRA_FILE")
    if (
        actual_dependency != expected["dependency_closure"]
        or value.get("dependency_closure_count")
        != expected["dependency_closure_count"]
        or value.get("source_dependency_closure_sha256")
        != expected["source_dependency_closure_sha256"]
    ):
        issues.add("RECOVERY_CANONICAL_CURRENT_CLOSURE_FILE_HASH_DRIFT")
    if (
        value.get("source_dependency_closure_sha256")
        == _PRE_IMPLEMENTATION_DEPENDENCY_ROOT
        or _SUCCESSOR_PATH not in expected_dependency_paths
    ):
        issues.add("RECOVERY_CANONICAL_CURRENT_CLOSURE_VIEW_BINDING_DRIFT")
    actual_files = value.get("files")
    expected_files = expected["files"]
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
    actual_by_path = {
        row["path"]: row
        for row in actual_files
        if type(row) is dict and type(row.get("path")) is str
    }
    expected_by_path = {row["path"]: row for row in expected_files}
    if len(actual_by_path) != len(actual_files):
        issues.add("RECOVERY_CANONICAL_CURRENT_CLOSURE_ENTRY_INVALID")
    if expected_by_path.keys() - actual_by_path.keys():
        issues.add("RECOVERY_CANONICAL_CURRENT_CLOSURE_REQUIRED_FILE_MISSING")
    if actual_by_path.keys() - expected_by_path.keys():
        issues.add("RECOVERY_CANONICAL_CURRENT_CLOSURE_EXTRA_FILE")
    for path in expected_by_path.keys() & actual_by_path.keys():
        actual_row = actual_by_path[path]
        expected_row = expected_by_path[path]
        if actual_row.get("sha256") != expected_row["sha256"]:
            issues.add("RECOVERY_CANONICAL_CURRENT_CLOSURE_FILE_HASH_DRIFT")
        if actual_row.get("git_blob_sha1") != expected_row["git_blob_sha1"]:
            issues.add("RECOVERY_CANONICAL_CURRENT_CLOSURE_GIT_BLOB_DRIFT")
        if actual_row.get("role") != expected_row["role"]:
            issues.add("RECOVERY_CANONICAL_CURRENT_CLOSURE_ROLE_BINDING_DRIFT")
    try:
        committed_blobs = _tree_blob_index(
            Path(repo_root).resolve(),
            expected["source_commit"],
            expected_by_path,
        )
    except (
        OSError,
        subprocess.SubprocessError,
        UnicodeError,
        ValueError,
    ):
        committed_blobs = {}
    if any(
        committed_blobs.get(path) != row["git_blob_sha1"]
        for path, row in expected_by_path.items()
    ):
        issues.add("RECOVERY_CANONICAL_CURRENT_CLOSURE_GIT_BLOB_DRIFT")
    step_views = value.get("step_views")
    views = value.get("views")
    semantic_execution = (
        views.get("semantic_execution") if type(views) is dict else None
    )
    if (
        type(step_views) is not dict
        or any(
            type(paths) is not list
            or any(type(path) is not str for path in paths)
            for paths in (
                step_views.values() if type(step_views) is dict else ()
            )
        )
        or type(semantic_execution) is not list
        or any(type(path) is not str for path in semantic_execution)
    ):
        issues.add("RECOVERY_CANONICAL_CURRENT_CLOSURE_VIEW_BINDING_DRIFT")
    semantic_execution_paths = (
        frozenset(semantic_execution)
        if type(semantic_execution) is list
        and all(type(path) is str for path in semantic_execution)
        else frozenset()
    )
    for historical_path in _HISTORICAL_EVIDENCE:
        historical_row = actual_by_path.get(historical_path)
        if (
            historical_row is None
            or historical_row.get("role") != "immutable_historical_evidence"
            or any(
                historical_path in paths
                for paths in (
                    step_views.values() if type(step_views) is dict else ()
                )
                if type(paths) is list
            )
            or historical_path in semantic_execution_paths
        ):
            issues.add("RECOVERY_CANONICAL_CURRENT_CLOSURE_ROLE_BINDING_DRIFT")
    actual_edges = value.get("edges")
    if type(actual_edges) is not list:
        issues.add("RECOVERY_CANONICAL_CURRENT_CLOSURE_ENTRY_INVALID")
        actual_edges = []
    actual_pairs: set[tuple[str, str]] = set()
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
        source = edge["source"]
        target = edge["target"]
        actual_pairs.add((source, target))
        if source not in actual_by_path or target not in actual_by_path:
            issues.add(
                "RECOVERY_CANONICAL_CURRENT_CLOSURE_EDGE_TARGET_UNRESOLVED"
            )
        if (
            source.startswith("ai/services/ai_inference/")
            and target.startswith(("ai/tests/", "ai/tools/"))
        ):
            issues.add(
                "RECOVERY_CANONICAL_CURRENT_CLOSURE_FORBIDDEN_CUE_INGRESS"
            )
            issues.add(
                "RECOVERY_CANONICAL_CURRENT_CLOSURE_PRIVATE_BODY_INGRESS"
            )
    expected_pairs = {
        (edge["source"], edge["target"]) for edge in expected["edges"]
    }
    if expected_pairs - actual_pairs:
        issues.add(
            "RECOVERY_CANONICAL_CURRENT_CLOSURE_"
            "EXISTING_LOCAL_IMPORT_UNLISTED"
        )
    if actual_pairs - expected_pairs:
        issues.add("RECOVERY_CANONICAL_CURRENT_CLOSURE_FORBIDDEN_EDGE")
    if actual_edges != expected["edges"]:
        issues.add("RECOVERY_CANONICAL_CURRENT_CLOSURE_REQUIRED_EDGE_MISSING")
    if (
        step_views != expected["step_views"]
        or views != expected["views"]
    ):
        issues.add("RECOVERY_CANONICAL_CURRENT_CLOSURE_VIEW_BINDING_DRIFT")
    completion_view = (
        views.get("completion_proof") if type(views) is dict else None
    )
    if (
        type(completion_view) is not list
        or any(type(path) is not str for path in completion_view)
        or not _PROOF_SEEDS
        <= {path for path in completion_view if type(path) is str}
    ):
        issues.add(
            "RECOVERY_CANONICAL_CURRENT_CLOSURE_"
            "SELF_NORMALIZATION_SCOPE_DRIFT"
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
        or value.get("canonical_current_closure_sha256")
        != expected["canonical_current_closure_sha256"]
    ):
        issues.add("RECOVERY_CANONICAL_CURRENT_CLOSURE_VIEW_BINDING_DRIFT")
    return tuple(sorted(issues))


def verify_recovery_epoch001_canonical_current_closure(
    value: Any,
    *,
    repo_root: Path,
) -> tuple[str, ...]:
    try:
        return _verify_recovery_epoch001_canonical_current_closure_impl(
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


def _verify_recovery_epoch001_current_step_completion_receipt_impl(
    value: Any,
    *,
    repo_root: Path,
    previous_receipt: Mapping[str, Any] | None = None,
    step0_parent_authority: Mapping[str, Any] | None = None,
    accepted_test_results: Mapping[str, Any] | None = None,
) -> tuple[str, ...]:
    """Independently reject unbound or self-declared completion receipts."""

    if type(value) is not dict:
        return ("RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_ENTRY_INVALID",)
    issues: set[str] = set()
    if set(value) != _RECEIPT_KEYS:
        issues.add("RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_ENTRY_INVALID")
    if (
        value.get("schema_version") != _RECEIPT_SCHEMA
        or value.get("candidate_version_id") != _CANDIDATE
    ):
        issues.add(
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_"
            "HISTORICAL_AS_CURRENT_FORBIDDEN"
        )
    step = value.get("step_number")
    valid_step = (
        type(step) is int
        and not isinstance(step, bool)
        and step in range(11)
    )
    if not valid_step:
        issues.add("RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_STEP_INVALID")
    lineage = value.get("lineage")
    if (
        type(lineage) is not dict
        or set(lineage)
        != {
            "kind",
            "historical_disposition",
            "historical_rewrite",
            "historical_as_current",
            "backfill",
        }
        or lineage.get("kind") != "current"
        or lineage.get("historical_disposition")
        != "IMMUTABLE_NONCURRENT_EVIDENCE"
    ):
        issues.add("RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_LINEAGE_INVALID")
    elif (
        lineage.get("historical_rewrite") is not False
        or lineage.get("backfill") is not False
    ):
        issues.add(
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_"
            "HISTORICAL_REWRITE_FORBIDDEN"
        )
    if type(lineage) is dict and lineage.get("historical_as_current") is not False:
        issues.add(
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_"
            "HISTORICAL_AS_CURRENT_FORBIDDEN"
        )
    try:
        closure = fresh_recovery_epoch001_canonical_current_closure(
            repo_root=repo_root
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
        closure = None
    file_rows = (
        {
            row["path"]: row
            for row in closure["files"]
            if type(row) is dict and type(row.get("path")) is str
        }
        if closure is not None
        else {}
    )
    binding = value.get("current_binding")
    step_key = f"step_{step}" if valid_step else None
    step_view = (
        closure["step_views"].get(step_key)
        if closure is not None and step_key is not None
        else None
    )
    allowed_paths = frozenset(
        path for path in (step_view or ()) if type(path) is str
    )
    if (
        closure is None
        or type(binding) is not dict
        or set(binding)
        != {
            "source_commit",
            "canonical_current_closure_sha256",
            "source_dependency_closure_sha256",
            "step_view_key",
            "step_view_sha256",
        }
        or binding.get("source_commit") != closure["source_commit"]
        or binding.get("canonical_current_closure_sha256")
        != closure["canonical_current_closure_sha256"]
        or binding.get("source_dependency_closure_sha256")
        != closure["source_dependency_closure_sha256"]
        or binding.get("step_view_key") != step_key
        or binding.get("step_view_sha256") != _artifact_sha256(step_view)
    ):
        issues.add(
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_CURRENT_BINDING_INVALID"
        )
        issues.add(
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_"
            "SOURCE_OR_VIEW_ROOT_MISMATCH"
        )

    owners = value.get("actual_owners")
    if type(owners) is not list or not owners:
        issues.add(
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_"
            "ACTUAL_OWNER_BINDING_INVALID"
        )
    else:
        owner_paths: set[str] = set()
        for owner in owners:
            path = owner.get("path") if type(owner) is dict else None
            row = file_rows.get(path) if type(path) is str else None
            if (
                type(owner) is not dict
                or set(owner)
                != {"path", "git_blob_sha1", "sha256", "symbol", "role"}
                or row is None
                or path not in allowed_paths
                or row.get("role") == "immutable_historical_evidence"
                or path in owner_paths
                or owner.get("git_blob_sha1") != row.get("git_blob_sha1")
                or owner.get("sha256") != row.get("sha256")
                or owner.get("role") != row.get("role")
                or owner.get("symbol") not in _top_level_symbols(
                    Path(repo_root) / path
                )
            ):
                issues.add(
                    "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_"
                    "ACTUAL_OWNER_BINDING_INVALID"
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
                "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_"
                "ACTUAL_OWNER_BINDING_INVALID"
            )

    contracts = value.get("strict_contracts")
    if type(contracts) is not list or not contracts:
        issues.add(
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_"
            "STRICT_CONTRACT_BINDING_INVALID"
        )
    else:
        contract_ids: set[str] = set()
        for contract in contracts:
            path = (
                contract.get("validator_path")
                if type(contract) is dict
                else None
            )
            row = file_rows.get(path) if type(path) is str else None
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
                or set(contract)
                != {
                    "contract_id",
                    "schema_version",
                    "validator_path",
                    "validator_blob_sha1",
                    "validator_symbol",
                    "invariant_ids",
                }
                or row is None
                or path not in allowed_paths
                or row.get("role") == "immutable_historical_evidence"
                or contract.get("validator_blob_sha1")
                != row.get("git_blob_sha1")
                or contract.get("validator_symbol")
                not in _top_level_symbols(Path(repo_root) / path)
                or type(contract_id) is not str
                or _MACHINE_RE.fullmatch(contract_id) is None
                or contract_id in contract_ids
                or type(contract.get("schema_version")) is not str
                or not contract.get("schema_version")
                or type(invariants) is not list
                or not invariants
                or any(
                    type(item) is not str
                    or _MACHINE_RE.fullmatch(item) is None
                    for item in (invariants if type(invariants) is list else ())
                )
                or invariants != sorted(invariants)
                or len(invariants) != len(set(invariants))
            ):
                issues.add(
                    "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_"
                    "STRICT_CONTRACT_BINDING_INVALID"
                )
            if type(contract_id) is str:
                contract_ids.add(contract_id)
        if all(type(item) is dict for item in contracts) and contracts != sorted(
            contracts,
            key=lambda item: str(item.get("contract_id")),
        ):
            issues.add(
                "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_"
                "STRICT_CONTRACT_BINDING_INVALID"
            )

    proof_paths: list[Any] = []
    for field, code in (
        (
            "positive_proof",
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_POSITIVE_PROOF_INVALID",
        ),
        (
            "independent_negative_proof",
            (
                "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_"
                "INDEPENDENT_NEGATIVE_PROOF_INVALID"
            ),
        ),
    ):
        proof = value.get(field)
        node_id = proof.get("test_node_id") if type(proof) is dict else None
        path = proof.get("source_path") if type(proof) is dict else None
        row = file_rows.get(path) if type(path) is str else None
        accepted = (
            accepted_test_results.get(node_id)
            if type(accepted_test_results) is dict
            and type(node_id) is str
            else None
        )
        if (
            type(proof) is not dict
            or set(proof)
            != {
                "test_node_id",
                "result",
                "source_path",
                "source_blob_sha1",
                "source_sha256",
                "evidence_sha256",
            }
            or row is None
            or path not in allowed_paths
            or row.get("role") == "immutable_historical_evidence"
            or proof.get("result") != "PASSED"
            or proof.get("source_blob_sha1") != row.get("git_blob_sha1")
            or proof.get("source_sha256") != row.get("sha256")
            or not _SHA_RE.fullmatch(str(proof.get("evidence_sha256", "")))
            or type(node_id) is not str
            or not node_id.startswith(f"{path}::test_")
            or node_id.rpartition("::")[2]
            not in _top_level_symbols(Path(repo_root) / path)
            or type(accepted) is not dict
            or accepted.get("result") != "PASSED"
            or accepted.get("evidence_sha256")
            != proof.get("evidence_sha256")
        ):
            issues.add(code)
        proof_paths.append(path)
    if len(proof_paths) == 2 and proof_paths[0] == proof_paths[1]:
        issues.add(
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_"
            "INDEPENDENT_NEGATIVE_PROOF_INVALID"
        )

    artifact = value.get("artifact_receipt")
    artifact_path = (
        artifact.get("path") if type(artifact) is dict else None
    )
    artifact_row = (
        file_rows.get(artifact_path)
        if type(artifact_path) is str
        else None
    )
    if (
        type(artifact) is not dict
        or set(artifact)
        != {"path", "git_blob_sha1", "sha256", "schema_version", "body_free"}
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
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_"
            "ARTIFACT_BINDING_INVALID"
        )

    parent = value.get("parent_binding")
    if step == 0:
        parent_keys = {
            "kind",
            "detailed_design_sha256",
            "parent_receipt_path",
            "parent_receipt_git_blob_sha1",
            "parent_receipt_sha256",
            "canonical_current_closure_sha256",
        }
        parent_ok = (
            type(parent) is dict
            and set(parent) == parent_keys
            and type(step0_parent_authority) is dict
            and parent == step0_parent_authority
            and parent.get("kind") == "step0_design_parent"
            and _SHA_RE.fullmatch(
                str(parent.get("detailed_design_sha256", ""))
            )
            is not None
            and _BLOB_RE.fullmatch(
                str(parent.get("parent_receipt_git_blob_sha1", ""))
            )
            is not None
            and _SHA_RE.fullmatch(
                str(parent.get("parent_receipt_sha256", ""))
            )
            is not None
            and parent.get("canonical_current_closure_sha256")
            == (closure or {}).get("canonical_current_closure_sha256")
        )
    elif valid_step:
        parent_keys = {
            "kind",
            "previous_step",
            "previous_receipt_sha256",
            "source_commit",
            "canonical_current_closure_sha256",
        }
        parent_ok = (
            type(parent) is dict
            and set(parent) == parent_keys
            and type(previous_receipt) is dict
            and set(previous_receipt) == _RECEIPT_KEYS
            and parent.get("kind") == "previous_current_step_receipt"
            and parent.get("previous_step") == step - 1
            and previous_receipt.get("step_number") == step - 1
            and previous_receipt.get("verdict") == "PROVED"
            and parent.get("previous_receipt_sha256")
            == previous_receipt.get("receipt_sha256")
            and _SHA_RE.fullmatch(
                str(previous_receipt.get("receipt_sha256", ""))
            )
            is not None
            and parent.get("source_commit")
            == (closure or {}).get("source_commit")
            and parent.get("canonical_current_closure_sha256")
            == (closure or {}).get("canonical_current_closure_sha256")
            and type(previous_receipt.get("current_binding")) is dict
            and previous_receipt["current_binding"].get("source_commit")
            == (closure or {}).get("source_commit")
            and previous_receipt["current_binding"].get(
                "canonical_current_closure_sha256"
            )
            == (closure or {}).get("canonical_current_closure_sha256")
        )
        if parent_ok:
            try:
                parent_ok = (
                    _artifact_sha256(
                        {
                            key: previous_receipt[key]
                            for key in sorted(
                                _RECEIPT_KEYS - {"receipt_sha256"}
                            )
                        }
                    )
                    == previous_receipt["receipt_sha256"]
                )
            except (
                KeyError,
                RecursionError,
                TypeError,
                UnicodeError,
                ValueError,
            ):
                parent_ok = False
    else:
        parent_ok = False
    if not parent_ok:
        issues.add(
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_PARENT_CHAIN_INVALID"
        )

    completion = value.get("completion_condition")
    completion_shape_invalid = (
        type(completion) is not dict
        or set(completion)
        != {"condition_id", "required", "satisfied", "evidence_sha256"}
        or type(completion.get("condition_id")) is not str
        or _MACHINE_RE.fullmatch(completion.get("condition_id", "")) is None
        or completion.get("required") is not True
        or type(completion.get("satisfied")) is not bool
        or not _SHA_RE.fullmatch(str(completion.get("evidence_sha256", "")))
    )
    if completion_shape_invalid:
        issues.add("RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_VERDICT_INVALID")
    stops = value.get("stop_conditions")
    stop_shape_invalid = (
        type(stops) is not list
        or not stops
        or any(
            type(row) is not dict
            or set(row) != {"condition_id", "triggered", "evidence_sha256"}
            or type(row.get("condition_id")) is not str
            or _MACHINE_RE.fullmatch(row.get("condition_id", "")) is None
            or type(row.get("triggered")) is not bool
            or not _SHA_RE.fullmatch(str(row.get("evidence_sha256", "")))
            for row in (stops if type(stops) is list else ())
        )
    )
    if not stop_shape_invalid:
        stop_ids = [row["condition_id"] for row in stops]
        stop_shape_invalid = (
            stop_ids != sorted(stop_ids)
            or len(stop_ids) != len(set(stop_ids))
        )
    if stop_shape_invalid:
        issues.add("RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_STOP_NOT_FALSE")
    verdict = value.get("verdict")
    if verdict not in {
        "PROVED",
        "NOT_PROVED",
        "FAILED",
        "CONFLICT",
    }:
        issues.add("RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_VERDICT_INVALID")
    elif verdict == "PROVED":
        issues.add("RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_VERDICT_INVALID")
        if (
            completion_shape_invalid
            or completion.get("satisfied") is not True
            or stop_shape_invalid
            or any(row["triggered"] is not False for row in stops)
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
            triggered = [row["triggered"] for row in stops]
            if verdict == "NOT_PROVED" and any(triggered):
                issues.add(
                    "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_VERDICT_INVALID"
                )
            if verdict in {"FAILED", "CONFLICT"} and not any(triggered):
                issues.add(
                    "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_VERDICT_INVALID"
                )
    expected_next = (
        _NEXT_BY_STEP.get(step)
        if verdict == "PROVED" and valid_step
        else None
    )
    if value.get("next_authority") != expected_next:
        issues.add(
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_NEXT_AUTHORITY_INVALID"
        )
    if value.get("body_free") is not True or not _body_free(value):
        issues.add(
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_BODY_FREE_REQUIRED"
        )
    receipt_hash = value.get("receipt_sha256")
    try:
        material = {
            key: item
            for key, item in value.items()
            if key != "receipt_sha256"
        }
        expected_hash = _artifact_sha256(material)
    except (RecursionError, TypeError, UnicodeError, ValueError):
        expected_hash = None
    if (
        type(receipt_hash) is not str
        or _SHA_RE.fullmatch(receipt_hash) is None
        or receipt_hash != expected_hash
    ):
        issues.add("RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_HASH_MISMATCH")
    return tuple(sorted(issues))


def verify_recovery_epoch001_current_step_completion_receipt(
    value: Any,
    *,
    repo_root: Path,
    previous_receipt: Mapping[str, Any] | None = None,
    step0_parent_authority: Mapping[str, Any] | None = None,
    accepted_test_results: Mapping[str, Any] | None = None,
) -> tuple[str, ...]:
    try:
        return _verify_recovery_epoch001_current_step_completion_receipt_impl(
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
