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
import platform
import re
import subprocess
from typing import Any, Iterable, Mapping, Sequence


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
            (
                "ai/tests/test_emlis_nls_v3_recovery_epoch001_"
                "step00_independent_negative.py"
            ),
            *_CURRENT_OWNERS,
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
            "ai/services/ai_inference/emlis_ai_discourse_graph_planner_v3.py",
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
            "ai/services/ai_inference/emlis_ai_surface_grammar_catalog_v3.py",
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
            (
                "ai/tests/test_emlis_nls_v3_recovery_epoch001_"
                "step08_independent_negative.py"
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
            (
                "ai/tests/test_emlis_nls_v3_recovery_epoch001_"
                "step09_independent_negative.py"
            ),
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
            (
                "ai/tests/test_emlis_nls_v3_recovery_epoch001_"
                "step10_independent_negative.py"
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


# Recovery Epoch 001 proved-issuance reconciliation.
# These definitions intentionally override the predecessor receipt wrapper
# above while preserving it as immutable implementation history in this file.

_REGISTRY_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch001."
    "current_step_requirement_registry.v1"
)
_ACCEPTED_RUN_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch001."
    "accepted_test_run_receipt.v1"
)
_ALL11_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch001."
    "all11_completion_chain.v1"
)
_BASELINE_EVENT_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch001."
    "source_baseline_event.v1"
)
_REGISTRY_SHA256 = (
    "70a75ae561fad0846604d05b1262615be4c4a16b36b332150f8c7dc04ee71728"
)
_FORMAL_NODE_REGISTRY_SHA256 = (
    "fbe29ce0b819563cb5db2dc79fec8277b32ae0dea5a3a5cba64230ba4a1f73cf"
)
_SELECTED_FORMAL_P1_AUTHORITY_TOKEN: str | None = None
_PROOF_RUN_PROTOCOL = "RECOVERY_EPOCH001_PYTEST_EXACT134_BODY_FREE_V1"
_FORMAL_RUN_TIMEOUT_SECONDS = 3600
_RUNNER_PATH = (
    "ai/tools/"
    "emlis_nls_v3_recovery_epoch001_current_step_proof_run.py"
)
_CURRENT_STEP_ARTIFACT_EVIDENCE_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch001."
    "current_step_artifact_evidence.v1"
)
_CHALLENGE_RE = re.compile(r"^[0-9a-f]{64}$")
_ACCEPTED_OUTCOME_STATES = frozenset(
    {"PASSED", "FAILED", "SKIPPED", "XFAILED", "XPASSED", "NOT_EXECUTED"}
)
_PYTEST_OPTIONS = (
    "-q",
    "--disable-warnings",
    "-p",
    "no:cacheprovider",
)
_REGISTRY_KEYS = frozenset(
    {
        "schema_version",
        "candidate_version_id",
        "recovery_epoch",
        "red_freeze_authority",
        "detailed_design_sha256",
        "required_sequence_event_1",
        "completion_sequence_event_2",
        "steps",
        "automatic_progression",
        "body_free",
        "registry_sha256",
    }
)
_REGISTRY_ROW_KEYS = frozenset(
    {
        "step_number",
        "actual_owners",
        "strict_contracts",
        "positive_proof",
        "independent_negative_proof",
        "formal_completion_node_ids",
        "artifact_receipt_schema_version",
        "parent_binding_kind",
        "source_binding_kind",
        "completion_condition_ids",
        "stop_condition_ids",
        "next_authority",
        "lineage",
    }
)
_ACCEPTED_KEYS = frozenset(
    {
        "schema_version",
        "candidate_version_id",
        "recovery_epoch",
        "authority_token",
        "challenge_id",
        "source_baseline_event_sha256",
        "baseline_id",
        "source_commit",
        "source_tree",
        "canonical_current_closure_sha256",
        "source_dependency_closure_sha256",
        "step_view_sha256_by_step",
        "registry_sha256",
        "formal_node_registry_sha256",
        "collection_node_ids",
        "collection_sha256",
        "executed_node_ids",
        "executed_node_sha256",
        "proof_sources",
        "proof_source_closure_sha256",
        "proof_run_sha256",
        "runner_environment",
        "run_start",
        "run_end",
        "outcomes",
        "counts",
        "exit_code",
        "timed_out",
        "accepted",
        "body_free",
        "accepted_test_run_receipt_sha256",
    }
)
_ACCEPTED_OUTCOME_KEYS = frozenset(
    {
        "test_node_id",
        "source_path",
        "source_blob_sha1",
        "source_sha256",
        "result",
        "expected_closed_code",
        "actual_closed_code",
        "evidence_sha256",
    }
)
_ACCEPTED_COUNT_KEYS = frozenset(
    {
        "collected",
        "executed",
        "passed",
        "failed",
        "skipped",
        "xfailed",
        "xpassed",
        "deselected",
        "collection_errors",
        "timeouts",
    }
)
_ACCEPTED_BINDING_KEYS = frozenset(
    {
        "source_commit",
        "source_tree",
        "canonical_current_closure_sha256",
        "source_dependency_closure_sha256",
        "registry_sha256",
        "worktree_clean",
    }
)
_ACCEPTED_RUNNER_ENVIRONMENT_KEYS = frozenset(
    {
        "protocol",
        "python_version",
        "pytest_version",
        "plugin_autoload_disabled",
        "runner_path",
        "runner_git_blob_sha1",
        "runner_sha256",
        "worker_isolated",
        "source_materialization",
        "pytest_addopts_ignored",
        "pytest_plugins_ignored",
        "timeout_seconds",
        "worker_argv_sha256",
        "environment_profile_sha256",
    }
)
_RECONCILED_CURRENT_KEYS = frozenset(
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
_RECONCILED_ARTIFACT_KEYS = frozenset(
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
_RECONCILED_STOP_KEYS = frozenset(
    {
        "condition_id",
        "proof_scope",
        "proof_node_registry_sha256",
        "accepted_test_run_receipt_sha256",
        "triggered",
        "evidence_sha256",
    }
)
_ALL11_KEYS = frozenset(
    {
        "schema_version",
        "candidate_version_id",
        "recovery_epoch",
        "source_baseline_event_sha256",
        "baseline_id",
        "source_commit",
        "source_tree",
        "canonical_current_closure_sha256",
        "source_dependency_closure_sha256",
        "registry_sha256",
        "accepted_test_run_receipt_sha256",
        "receipt_count",
        "ordered_steps",
        "receipts",
        "receipt_sha256s",
        "required_sequence_event_2",
        "next_authority",
        "publication_state",
        "automatic_progression",
        "body_free",
        "all11_completion_chain_sha256",
    }
)


def _hash_material(
    value: Mapping[str, Any],
    hash_key: str,
) -> dict[str, Any]:
    return {
        key: value[key]
        for key in sorted(set(value) - {hash_key})
    }


def _git_final_identity(root: Path) -> tuple[str, str, bool]:
    source_commit = _source_commit(root)
    source_tree = subprocess.run(
        ["git", "rev-parse", "HEAD^{tree}"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        timeout=5,
    ).stdout.strip()
    status = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        timeout=5,
    ).stdout
    if _COMMIT_RE.fullmatch(source_tree) is None:
        raise ValueError("source_tree_invalid")
    return source_commit, source_tree, status == ""


def _registry_nodes(value: Mapping[str, Any]) -> list[str]:
    steps = value.get("steps")
    if type(steps) is not list:
        return []
    return [
        node
        for row in steps
        if type(row) is dict
        for node in row.get("formal_completion_node_ids", [])
        if type(node) is str
    ]


def verify_recovery_epoch001_current_step_requirement_registry(
    value: Any,
    *,
    repo_root: Path,
) -> tuple[str, ...]:
    """Verify the fixed registry by shape and both frozen canonical roots."""

    if type(value) is not dict:
        return ("RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_ENTRY_INVALID",)
    issues: set[str] = set()
    if set(value) != _REGISTRY_KEYS:
        issues.add("RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_ENTRY_INVALID")
    if (
        value.get("schema_version") != _REGISTRY_SCHEMA
        or value.get("candidate_version_id") != _CANDIDATE
        or value.get("recovery_epoch") != 1
    ):
        issues.add("RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_ENTRY_INVALID")
    if (
        value.get("required_sequence_event_1") != "SOURCE_BASELINE_LOCKED"
        or value.get("completion_sequence_event_2")
        != "STEP0_10_PREREQUISITES_PROVED"
    ):
        issues.add(
            "RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_"
            "PARENT_OR_SOURCE_INVALID"
        )
    steps = value.get("steps")
    if type(steps) is not list or len(steps) != 11:
        issues.add("RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_STEP_INVALID")
        steps = []
    if [
        row.get("step_number")
        for row in steps
        if type(row) is dict
    ] != list(range(11)):
        issues.add("RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_ORDER_INVALID")
    root = Path(repo_root).resolve()
    seen_nodes: set[str] = set()
    step_nodes: dict[str, list[str]] = {}
    for step, row in enumerate(steps):
        if type(row) is not dict or set(row) != _REGISTRY_ROW_KEYS:
            issues.add(
                "RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_ENTRY_INVALID"
            )
            continue
        owners = row.get("actual_owners")
        if type(owners) is not list or not owners:
            issues.add(
                "RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_OWNER_INVALID"
            )
        else:
            for owner in owners:
                path = owner.get("path") if type(owner) is dict else None
                symbol = owner.get("symbol") if type(owner) is dict else None
                if (
                    type(path) is not str
                    or type(symbol) is not str
                    or not (root / path).is_file()
                ):
                    issues.add(
                        "RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_"
                        "OWNER_INVALID"
                    )
        contracts = row.get("strict_contracts")
        if type(contracts) is not list or not contracts:
            issues.add(
                "RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_CONTRACT_INVALID"
            )
        proofs = (
            row.get("positive_proof"),
            row.get("independent_negative_proof"),
        )
        for proof in proofs:
            path = proof.get("source_path") if type(proof) is dict else None
            node_id = proof.get("test_node_id") if type(proof) is dict else None
            if (
                type(path) is not str
                or type(node_id) is not str
                or not node_id.startswith(f"{path}::test_")
                or not (root / path).is_file()
            ):
                issues.add(
                    "RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_PROOF_INVALID"
                )
        if (
            type(proofs[0]) is dict
            and type(proofs[1]) is dict
            and proofs[0].get("source_path")
            == proofs[1].get("source_path")
        ):
            issues.add(
                "RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_PROOF_INVALID"
            )
        nodes = row.get("formal_completion_node_ids")
        if (
            type(nodes) is not list
            or not nodes
            or any(type(node) is not str for node in nodes)
            or any(node in seen_nodes for node in nodes)
        ):
            issues.add(
                "RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_NODE_SET_INVALID"
            )
            nodes = []
        seen_nodes.update(nodes)
        step_nodes[str(step)] = list(nodes)
        if (
            row.get("parent_binding_kind")
            != (
                "SOURCE_BASELINE_LOCKED_EVENT_1"
                if step == 0
                else "PREVIOUS_CURRENT_STEP_PROVED_RECEIPT"
            )
            or row.get("source_binding_kind")
            != "SAME_BASELINE_FINAL_COMMIT_AND_STEP_VIEW"
        ):
            issues.add(
                "RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_"
                "PARENT_OR_SOURCE_INVALID"
            )
        if row.get("completion_condition_ids") != [
            f"STEP_{step}_CURRENT_COMPLETION_REQUIREMENTS_SATISFIED"
        ]:
            issues.add(
                "RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_"
                "COMPLETION_INVALID"
            )
        if (
            type(row.get("stop_condition_ids")) is not list
            or not row["stop_condition_ids"]
        ):
            issues.add(
                "RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_STOP_INVALID"
            )
        if row.get("next_authority") != _NEXT_BY_STEP.get(step):
            issues.add(
                "RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_"
                "NEXT_AUTHORITY_INVALID"
            )
        lineage = row.get("lineage")
        if (
            type(lineage) is not dict
            or lineage.get("kind") != "current"
            or lineage.get("recovery_epoch") != 1
            or lineage.get("historical_rewrite") is not False
            or lineage.get("historical_as_current") is not False
            or lineage.get("backfill") is not False
        ):
            issues.add(
                "RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_LINEAGE_INVALID"
            )
    if len(seen_nodes) != 134:
        issues.add("RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_NODE_SET_INVALID")
    if _artifact_sha256({"step_nodes": step_nodes}) != (
        _FORMAL_NODE_REGISTRY_SHA256
    ):
        issues.add("RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_NODE_SET_INVALID")
    if value.get("automatic_progression") is not False:
        issues.add(
            "RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_"
            "NEXT_AUTHORITY_INVALID"
        )
    if value.get("body_free") is not True or not _body_free(value):
        issues.add(
            "RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_BODY_FREE_REQUIRED"
        )
    try:
        expected_hash = _artifact_sha256(
            _hash_material(value, "registry_sha256")
        )
    except (KeyError, RecursionError, TypeError, UnicodeError, ValueError):
        expected_hash = None
    if (
        expected_hash is None
        or value.get("registry_sha256") != expected_hash
        or value.get("registry_sha256") != _REGISTRY_SHA256
    ):
        issues.add("RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_HASH_MISMATCH")
    return tuple(sorted(issues))


def _baseline_event_valid_independent(
    event: Any,
    *,
    source_commit: str,
    source_tree: str,
    closure: Mapping[str, Any],
    registry: Mapping[str, Any],
) -> bool:
    if type(event) is not dict:
        return False
    required = {
        "schema_version",
        "event_name",
        "event_ordinal",
        "candidate_version_id",
        "recovery_epoch",
        "formal_p1_authority",
        "challenge_id",
        "source_commit",
        "source_tree",
        "canonical_current_closure_sha256",
        "source_dependency_closure_sha256",
        "registry_sha256",
        "automatic_progression",
        "body_free",
        "event_sha256",
    }
    try:
        expected_hash = _artifact_sha256(
            _hash_material(event, "event_sha256")
        )
    except (KeyError, RecursionError, TypeError, UnicodeError, ValueError):
        return False
    return (
        set(event) == required
        and event.get("schema_version") == _BASELINE_EVENT_SCHEMA
        and event.get("event_name") == "SOURCE_BASELINE_LOCKED"
        and event.get("event_ordinal") == 1
        and event.get("candidate_version_id") == _CANDIDATE
        and event.get("recovery_epoch") == 1
        and _SELECTED_FORMAL_P1_AUTHORITY_TOKEN is not None
        and event.get("formal_p1_authority")
        == _SELECTED_FORMAL_P1_AUTHORITY_TOKEN
        and _CHALLENGE_RE.fullmatch(str(event.get("challenge_id", "")))
        is not None
        and event.get("source_commit") == source_commit
        and event.get("source_tree") == source_tree
        and event.get("canonical_current_closure_sha256")
        == closure.get("canonical_current_closure_sha256")
        and event.get("source_dependency_closure_sha256")
        == closure.get("source_dependency_closure_sha256")
        and event.get("registry_sha256") == registry.get("registry_sha256")
        and event.get("automatic_progression") is False
        and event.get("body_free") is True
        and _body_free(event)
        and event.get("event_sha256") == expected_hash
    )


def _accepted_expected_worker_argv_sha256(nodes: list[str]) -> str:
    return _artifact_sha256(
        {
            "python_flags": ["-I", "-B"],
            "runner_path": _RUNNER_PATH,
            "worker_mode": "--internal-exact134-child",
            "node_ids": nodes,
            "pytest_options": list(_PYTEST_OPTIONS),
        }
    )


def _accepted_expected_counts(
    *,
    expected_nodes: list[str],
    collection: list[str],
    executed: list[str],
    outcomes: list[Mapping[str, Any]],
    collection_errors: int,
    timed_out: bool,
) -> dict[str, int]:
    states = {
        row["test_node_id"]: row["result"]
        for row in outcomes
        if type(row) is dict
        and type(row.get("test_node_id")) is str
        and type(row.get("result")) is str
    }
    ordered = [
        states.get(node_id, "NOT_EXECUTED") for node_id in expected_nodes
    ]
    return {
        "collected": len(collection),
        "executed": len(
            [node_id for node_id in expected_nodes if node_id in executed]
        ),
        "passed": ordered.count("PASSED"),
        "failed": ordered.count("FAILED") + ordered.count("NOT_EXECUTED"),
        "skipped": ordered.count("SKIPPED"),
        "xfailed": ordered.count("XFAILED"),
        "xpassed": ordered.count("XPASSED"),
        "deselected": max(0, len(collection) - len(expected_nodes)),
        "collection_errors": collection_errors,
        "timeouts": 1 if timed_out else 0,
    }


def _accepted_proof_material(
    value: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "protocol": value["runner_environment"]["protocol"],
        "candidate_version_id": value["candidate_version_id"],
        "recovery_epoch": value["recovery_epoch"],
        "source_baseline_event_sha256": value[
            "source_baseline_event_sha256"
        ],
        "source_commit": value["source_commit"],
        "source_tree": value["source_tree"],
        "canonical_current_closure_sha256": value[
            "canonical_current_closure_sha256"
        ],
        "source_dependency_closure_sha256": value[
            "source_dependency_closure_sha256"
        ],
        "registry_sha256": value["registry_sha256"],
        "formal_node_registry_sha256": value[
            "formal_node_registry_sha256"
        ],
        "collection_node_ids": value["collection_node_ids"],
        "executed_node_ids": value["executed_node_ids"],
        "runner_environment": value["runner_environment"],
        "run_start": value["run_start"],
        "run_end": value["run_end"],
        "outcomes": value["outcomes"],
        "counts": value["counts"],
        "exit_code": value["exit_code"],
        "timed_out": value["timed_out"],
        "body_free": value["body_free"],
    }


def verify_recovery_epoch001_accepted_test_run_receipt(
    value: Any,
    *,
    repo_root: Path,
    requirement_registry: Mapping[str, Any] | None = None,
    source_baseline_event: Mapping[str, Any] | None = None,
) -> tuple[str, ...]:
    """Independently verify event 1, exact134 outcomes, and clean bindings."""

    if type(value) is not dict:
        return ("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_ENTRY_INVALID",)
    issues: set[str] = set()
    if set(value) != _ACCEPTED_KEYS:
        issues.add("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_ENTRY_INVALID")
    root = Path(repo_root).resolve()
    registry = (
        dict(requirement_registry)
        if type(requirement_registry) is dict
        else {}
    )
    if verify_recovery_epoch001_current_step_requirement_registry(
        registry,
        repo_root=root,
    ):
        issues.add("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_REGISTRY_ROOT_MISMATCH")
    try:
        closure = fresh_recovery_epoch001_canonical_current_closure(
            repo_root=root
        )
        source_commit, source_tree, clean = _git_final_identity(root)
    except (
        FileNotFoundError,
        OSError,
        subprocess.SubprocessError,
        SyntaxError,
        UnicodeError,
        ValueError,
    ):
        closure = {}
        source_commit = ""
        source_tree = ""
        clean = False
    event = (
        dict(source_baseline_event)
        if type(source_baseline_event) is dict
        else {}
    )
    if not _baseline_event_valid_independent(
        event,
        source_commit=source_commit,
        source_tree=source_tree,
        closure=closure,
        registry=registry,
    ):
        issues.add("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_BASELINE_EVENT_INVALID")
    if (
        value.get("schema_version") != _ACCEPTED_RUN_SCHEMA
        or value.get("candidate_version_id") != _CANDIDATE
        or value.get("recovery_epoch") != 1
        or value.get("authority_token") != event.get("formal_p1_authority")
        or value.get("challenge_id") != event.get("challenge_id")
        or value.get("source_baseline_event_sha256")
        != event.get("event_sha256")
        or value.get("baseline_id") != event.get("event_sha256")
    ):
        issues.add("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_AUTHORITY_INVALID")
    if (
        value.get("source_commit") != source_commit
        or value.get("source_tree") != source_tree
    ):
        issues.add(
            "RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_"
            "SOURCE_COMMIT_OR_TREE_MISMATCH"
        )
    if (
        value.get("canonical_current_closure_sha256")
        != closure.get("canonical_current_closure_sha256")
        or value.get("source_dependency_closure_sha256")
        != closure.get("source_dependency_closure_sha256")
    ):
        issues.add("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_CLOSURE_ROOT_MISMATCH")
    expected_views = (
        {
            str(step): _artifact_sha256(
                closure["step_views"][f"step_{step}"]
            )
            for step in range(11)
        }
        if type(closure.get("step_views")) is dict
        else {}
    )
    if value.get("step_view_sha256_by_step") != expected_views:
        issues.add("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_CLOSURE_ROOT_MISMATCH")
    nodes = _registry_nodes(registry)
    if (
        value.get("collection_node_ids") != nodes
        or value.get("collection_sha256")
        != _artifact_sha256({"node_ids": nodes})
    ):
        issues.add("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_COLLECTION_MISMATCH")
    if (
        value.get("executed_node_ids") != nodes
        or value.get("executed_node_sha256")
        != _artifact_sha256({"node_ids": nodes})
    ):
        issues.add("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_EXECUTED_NODE_MISMATCH")
    if (
        value.get("registry_sha256") != _REGISTRY_SHA256
        or value.get("formal_node_registry_sha256")
        != _FORMAL_NODE_REGISTRY_SHA256
    ):
        issues.add("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_REGISTRY_ROOT_MISMATCH")
    negative_codes = {
        row["independent_negative_proof"]["test_node_id"]: (
            row["independent_negative_proof"]["expected_closed_code"]
        )
        for row in registry.get("steps", [])
        if type(row) is dict
        and type(row.get("independent_negative_proof")) is dict
    }
    closure_files = {
        row["path"]: row
        for row in closure.get("files", [])
        if type(row) is dict
        and type(row.get("path")) is str
        and set(row) == {"path", "role", "sha256", "git_blob_sha1"}
    }
    outcomes = value.get("outcomes")
    if (
        type(outcomes) is not list
        or len(outcomes) != 134
        or [
            row.get("test_node_id")
            for row in outcomes
            if type(row) is dict
        ]
        != nodes
    ):
        issues.add("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_OUTCOME_INVALID")
        outcomes = []
    proof_source_by_path: dict[str, dict[str, str]] = {}
    for outcome in outcomes:
        if type(outcome) is not dict or set(outcome) != _ACCEPTED_OUTCOME_KEYS:
            issues.add("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_OUTCOME_INVALID")
            continue
        node_id = outcome.get("test_node_id")
        path_value = outcome.get("source_path")
        path = root / str(path_value)
        source_row = closure_files.get(path_value)
        expected_closed_code = negative_codes.get(node_id)
        if (
            type(path_value) is not str
            or path_value != str(node_id).partition("::")[0]
            or source_row is None
            or not path.is_file()
            or outcome.get("source_blob_sha1")
            != source_row.get("git_blob_sha1")
            or outcome.get("source_blob_sha1") != _blob_sha(path)
            or outcome.get("source_sha256") != source_row.get("sha256")
            or outcome.get("source_sha256") != _file_sha(path)
            or outcome.get("result") not in _ACCEPTED_OUTCOME_STATES
            or outcome.get("expected_closed_code") != expected_closed_code
            or outcome.get("actual_closed_code")
            != (
                expected_closed_code
                if expected_closed_code is not None
                and outcome.get("result") == "PASSED"
                else None
            )
            or outcome.get("evidence_sha256")
            != _artifact_sha256(
                _hash_material(outcome, "evidence_sha256")
            )
        ):
            issues.add("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_OUTCOME_INVALID")
            continue
        proof_source = {
            "path": path_value,
            "git_blob_sha1": outcome["source_blob_sha1"],
            "sha256": outcome["source_sha256"],
        }
        previous_source = proof_source_by_path.setdefault(
            path_value,
            proof_source,
        )
        if previous_source != proof_source:
            issues.add("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_OUTCOME_INVALID")
    proof_sources = [
        proof_source_by_path[path] for path in sorted(proof_source_by_path)
    ]
    if (
        value.get("proof_sources") != proof_sources
        or value.get("proof_source_closure_sha256")
        != _artifact_sha256(proof_sources)
    ):
        issues.add("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_OUTCOME_INVALID")
    counts = value.get("counts")
    collection_errors = (
        counts.get("collection_errors") if type(counts) is dict else None
    )
    timed_out = value.get("timed_out")
    expected_counts = (
        _accepted_expected_counts(
            expected_nodes=nodes,
            collection=(
                value["collection_node_ids"]
                if type(value.get("collection_node_ids")) is list
                else []
            ),
            executed=(
                value["executed_node_ids"]
                if type(value.get("executed_node_ids")) is list
                else []
            ),
            outcomes=outcomes,
            collection_errors=collection_errors,
            timed_out=timed_out,
        )
        if type(collection_errors) is int
        and not isinstance(collection_errors, bool)
        and collection_errors >= 0
        and type(timed_out) is bool
        else None
    )
    if (
        type(counts) is not dict
        or set(counts) != _ACCEPTED_COUNT_KEYS
        or counts != expected_counts
        or type(value.get("exit_code")) is not int
        or isinstance(value.get("exit_code"), bool)
        or timed_out is not False
        or counts.get("timeouts") != 0
        or counts.get("collection_errors") != 0
        or (
            counts.get("passed") == 134
            and value.get("exit_code") != 0
        )
        or (
            counts.get("failed", 0) > 0
            and value.get("exit_code") == 0
        )
        or value.get("accepted") is not True
    ):
        issues.add("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_PARTIAL")
    expected_binding = {
        "source_commit": source_commit,
        "source_tree": source_tree,
        "canonical_current_closure_sha256": (
            closure.get("canonical_current_closure_sha256")
        ),
        "source_dependency_closure_sha256": (
            closure.get("source_dependency_closure_sha256")
        ),
        "registry_sha256": _REGISTRY_SHA256,
        "worktree_clean": True,
    }
    if (
        type(value.get("run_start")) is not dict
        or type(value.get("run_end")) is not dict
        or set(value["run_start"]) != _ACCEPTED_BINDING_KEYS
        or set(value["run_end"]) != _ACCEPTED_BINDING_KEYS
        or value["run_start"] != expected_binding
        or value["run_end"] != expected_binding
    ):
        issues.add("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_START_END_DRIFT")
    if not clean:
        issues.add("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_WORKTREE_NOT_CLEAN")
    environment = value.get("runner_environment")
    runner = root / _RUNNER_PATH
    runner_row = closure_files.get(_RUNNER_PATH)
    if (
        type(environment) is not dict
        or set(environment) != _ACCEPTED_RUNNER_ENVIRONMENT_KEYS
        or environment.get("protocol")
        != _PROOF_RUN_PROTOCOL
        or environment.get("plugin_autoload_disabled") is not True
        or environment.get("runner_path") != _RUNNER_PATH
        or runner_row is None
        or not runner.is_file()
        or environment.get("runner_git_blob_sha1")
        != runner_row.get("git_blob_sha1")
        or environment.get("runner_git_blob_sha1") != _blob_sha(runner)
        or environment.get("runner_sha256") != runner_row.get("sha256")
        or environment.get("runner_sha256") != _file_sha(runner)
        or environment.get("worker_isolated") is not True
        or environment.get("source_materialization")
        != "DETACHED_PINNED_GIT_WORKTREE"
        or environment.get("pytest_addopts_ignored") is not True
        or environment.get("pytest_plugins_ignored") is not True
        or environment.get("timeout_seconds")
        != _FORMAL_RUN_TIMEOUT_SECONDS
        or environment.get("worker_argv_sha256")
        != _accepted_expected_worker_argv_sha256(nodes)
        or not _SHA_RE.fullmatch(
            str(environment.get("environment_profile_sha256", ""))
        )
        or environment.get("python_version") != platform.python_version()
        or type(environment.get("pytest_version")) is not str
        or not environment.get("pytest_version")
    ):
        issues.add("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_OUTCOME_INVALID")
    try:
        proof_hash = _artifact_sha256(_accepted_proof_material(value))
    except (
        KeyError,
        RecursionError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        proof_hash = None
    if (
        proof_hash is None
        or value.get("proof_run_sha256") != proof_hash
        or not _SHA_RE.fullmatch(str(value.get("proof_run_sha256", "")))
    ):
        issues.add("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_HASH_MISMATCH")
    if value.get("body_free") is not True or not _body_free(value):
        issues.add("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_BODY_FREE_REQUIRED")
    try:
        expected_hash = _artifact_sha256(
            _hash_material(value, "accepted_test_run_receipt_sha256")
        )
    except (KeyError, RecursionError, TypeError, UnicodeError, ValueError):
        expected_hash = None
    if (
        expected_hash is None
        or value.get("accepted_test_run_receipt_sha256") != expected_hash
    ):
        issues.add("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_HASH_MISMATCH")
    return tuple(sorted(issues))


def _accepted_formal_run_complete_independent(
    accepted: Mapping[str, Any],
    nodes: Sequence[str],
) -> bool:
    outcomes = {
        row["test_node_id"]: row
        for row in accepted.get("outcomes", [])
        if type(row) is dict and type(row.get("test_node_id")) is str
    }
    return (
        accepted.get("accepted") is True
        and accepted.get("counts")
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
        and accepted.get("exit_code") == 0
        and accepted.get("timed_out") is False
        and all(
            node_id in outcomes
            and outcomes[node_id].get("result") == "PASSED"
            for node_id in nodes
        )
    )


def _global_stop_ids_independent(
    registry: Mapping[str, Any],
) -> frozenset[str]:
    rows = registry.get("steps")
    if type(rows) is not list or not rows:
        return frozenset()
    stop_sets = [
        frozenset(
            item
            for item in row.get("stop_condition_ids", [])
            if type(item) is str
        )
        for row in rows
        if type(row) is dict
    ]
    if len(stop_sets) != len(rows):
        return frozenset()
    return frozenset.intersection(*stop_sets)


def _stop_material_independent(
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
            node_id not in outcomes
            or outcomes[node_id].get("result") != "PASSED"
            for node_id in proof_nodes
        )
    ):
        return None
    proof_scope = (
        "GLOBAL_EXACT134"
        if condition_id in global_stop_ids
        else "STEP_EXACT_REQUIRED_NODES"
    )
    node_root = _artifact_sha256({"node_ids": proof_nodes})
    evidence = {
        "condition_id": condition_id,
        "proof_scope": proof_scope,
        "proof_node_registry_sha256": node_root,
        "outcome_evidence_sha256s": [
            outcomes[node_id]["evidence_sha256"] for node_id in proof_nodes
        ],
        "accepted_test_run_receipt_sha256": accepted_hash,
        "triggered": False,
    }
    return {
        "condition_id": condition_id,
        "proof_scope": proof_scope,
        "proof_node_registry_sha256": node_root,
        "accepted_test_run_receipt_sha256": accepted_hash,
        "triggered": False,
        "evidence_sha256": _artifact_sha256(evidence),
    }


def _reconciled_expected_receipt_material(
    *,
    step: int,
    registry: Mapping[str, Any],
    accepted: Mapping[str, Any],
    closure: Mapping[str, Any],
    root: Path,
) -> dict[str, Any] | None:
    rows = registry.get("steps")
    if type(rows) is not list or step not in range(len(rows)):
        return None
    row = rows[step]
    files = {
        item["path"]: item
        for item in closure.get("files", [])
        if type(item) is dict and type(item.get("path")) is str
    }
    step_key = f"step_{step}"
    step_view = closure.get("step_views", {}).get(step_key)
    if type(step_view) is not list:
        return None
    allowed = frozenset(step_view)
    outcomes = {
        item["test_node_id"]: item
        for item in accepted.get("outcomes", [])
        if type(item) is dict and type(item.get("test_node_id")) is str
    }
    nodes = row.get("formal_completion_node_ids")
    all_nodes = [
        node_id
        for registry_row in rows
        if type(registry_row) is dict
        for node_id in registry_row.get("formal_completion_node_ids", [])
        if type(node_id) is str
    ]
    if (
        type(nodes) is not list
        or len(all_nodes) != 134
        or not _accepted_formal_run_complete_independent(
            accepted,
            all_nodes,
        )
    ):
        return None
    owners: list[dict[str, Any]] = []
    for owner in row.get("actual_owners", []):
        source = files.get(owner.get("path"))
        if source is None or owner.get("path") not in allowed:
            return None
        owners.append(
            {
                "path": owner["path"],
                "git_blob_sha1": source["git_blob_sha1"],
                "sha256": source["sha256"],
                "symbol": owner["symbol"],
                "role": owner["role"],
            }
        )
    contracts: list[dict[str, Any]] = []
    for contract in row.get("strict_contracts", []):
        source = files.get(contract.get("validator_path"))
        validator_path = contract.get("validator_path")
        if (
            source is None
            or validator_path not in allowed
            or contract.get("validator_symbol")
            not in _top_level_symbols(root / str(validator_path))
        ):
            return None
        contracts.append(
            {
                "contract_id": contract["contract_id"],
                "schema_version": contract["schema_version"],
                "validator_path": contract["validator_path"],
                "validator_blob_sha1": source["git_blob_sha1"],
                "validator_symbol": contract["validator_symbol"],
                "invariant_ids": list(contract["invariant_ids"]),
            }
        )

    def proof_material(proof: Mapping[str, Any]) -> dict[str, Any] | None:
        outcome = outcomes.get(proof.get("test_node_id"))
        source = files.get(proof.get("source_path"))
        if (
            type(outcome) is not dict
            or source is None
            or proof.get("source_path") not in allowed
            or outcome.get("source_blob_sha1") != source["git_blob_sha1"]
            or outcome.get("source_sha256") != source["sha256"]
        ):
            return None
        return {
            "test_node_id": proof["test_node_id"],
            "result": "PASSED",
            "source_path": proof["source_path"],
            "source_blob_sha1": source["git_blob_sha1"],
            "source_sha256": source["sha256"],
            "evidence_sha256": outcome["evidence_sha256"],
        }

    positive = proof_material(row["positive_proof"])
    negative = proof_material(row["independent_negative_proof"])
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
    accepted_hash = accepted["accepted_test_run_receipt_sha256"]
    formal_evidence = _artifact_sha256(
        {
            "step_number": step,
            "formal_node_ids": nodes,
            "outcome_evidence_sha256s": [
                outcomes[node]["evidence_sha256"] for node in nodes
            ],
            "accepted_test_run_receipt_sha256": accepted_hash,
        }
    )
    global_stop_ids = _global_stop_ids_independent(registry)
    stops = [
        _stop_material_independent(
            condition_id=condition_id,
            step_nodes=nodes,
            all_nodes=all_nodes,
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
        "current_binding": {
            "source_commit": closure["source_commit"],
            "source_tree": accepted["source_tree"],
            "source_baseline_event_sha256": accepted[
                "source_baseline_event_sha256"
            ],
            "canonical_current_closure_sha256": closure[
                "canonical_current_closure_sha256"
            ],
            "source_dependency_closure_sha256": closure[
                "source_dependency_closure_sha256"
            ],
            "full_graph_sha256": closure["full_graph_sha256"],
            "step_view_key": step_key,
            "step_view_sha256": _artifact_sha256(step_view),
            "requirement_registry_sha256": registry["registry_sha256"],
            "formal_node_registry_sha256": (
                _FORMAL_NODE_REGISTRY_SHA256
            ),
            "accepted_test_run_receipt_sha256": accepted_hash,
        },
        "actual_owners": owners,
        "strict_contracts": contracts,
        "positive_proof": positive,
        "independent_negative_proof": negative,
        "artifact_receipt": {
            "schema_version": _CURRENT_STEP_ARTIFACT_EVIDENCE_SCHEMA,
            "step_number": step,
            "required_artifact_schema_version": (
                row["artifact_receipt_schema_version"]
            ),
            "owner_binding_sha256": _artifact_sha256(owners),
            "strict_contract_binding_sha256": _artifact_sha256(contracts),
            "requirement_registry_sha256": registry["registry_sha256"],
            "accepted_test_run_receipt_sha256": accepted_hash,
            "formal_completion_evidence_sha256": formal_evidence,
            "body_free": True,
        },
        "completion_condition": {
            "condition_id": row["completion_condition_ids"][0],
            "required": True,
            "satisfied": True,
            "evidence_sha256": formal_evidence,
        },
        "stop_conditions": [stop for stop in stops if stop is not None],
    }


def _valid_prior_chain_independent(
    values: Any,
    *,
    step: int,
    previous_receipt: Mapping[str, Any] | None,
    repo_root: Path,
    event: Mapping[str, Any],
    registry: Mapping[str, Any],
    accepted: Mapping[str, Any],
) -> bool:
    if type(values) not in (list, tuple) or len(values) != step:
        return False
    chain = [dict(item) for item in values if type(item) is dict]
    if len(chain) != step:
        return False
    if step > 0 and (
        type(previous_receipt) is not dict
        or chain[-1] != dict(previous_receipt)
    ):
        return False
    for index, receipt in enumerate(chain):
        if _verify_receipt_reconciled_impl(
            receipt,
            repo_root=repo_root,
            previous_receipt=(chain[index - 1] if index else None),
            step0_parent_authority=event,
            requirement_registry=registry,
            accepted_test_run_receipt=accepted,
            prior_receipts=chain[:index],
            _prior_chain_validated=True,
        ):
            return False
    return True


def verify_recovery_epoch001_current_step_completion_receipt(
    value: Any,
    *,
    repo_root: Path,
    previous_receipt: Mapping[str, Any] | None = None,
    step0_parent_authority: Mapping[str, Any] | None = None,
    requirement_registry: Mapping[str, Any] | None = None,
    accepted_test_run_receipt: Mapping[str, Any] | None = None,
    accepted_test_results: Mapping[str, Any] | None = None,
    prior_receipts: Sequence[Mapping[str, Any]] | None = None,
    _prior_chain_validated: bool = False,
) -> tuple[str, ...]:
    """Verify a derived receipt without trusting owner builders or result maps."""

    if type(value) is not dict:
        return ("RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_ENTRY_INVALID",)
    issues: set[str] = set()
    if set(value) != _RECEIPT_KEYS:
        issues.add("RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_ENTRY_INVALID")
    if accepted_test_results is not None:
        issues.add("RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_VERDICT_INVALID")
    root = Path(repo_root).resolve()
    step = value.get("step_number")
    valid_step = (
        type(step) is int
        and not isinstance(step, bool)
        and step in range(11)
    )
    if not valid_step:
        issues.add("RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_STEP_INVALID")
    if (
        value.get("schema_version") != _RECEIPT_SCHEMA
        or value.get("candidate_version_id") != _CANDIDATE
    ):
        issues.add(
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_"
            "HISTORICAL_AS_CURRENT_FORBIDDEN"
        )
    lineage = value.get("lineage")
    if type(lineage) is not dict:
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
        dict(requirement_registry)
        if type(requirement_registry) is dict
        else {}
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
    context_valid = not (
        verify_recovery_epoch001_current_step_requirement_registry(
            registry,
            repo_root=root,
        )
        or verify_recovery_epoch001_accepted_test_run_receipt(
            accepted,
            repo_root=root,
            requirement_registry=registry,
            source_baseline_event=event,
        )
    )
    try:
        closure = fresh_recovery_epoch001_canonical_current_closure(
            repo_root=root
        )
    except (
        FileNotFoundError,
        OSError,
        subprocess.SubprocessError,
        SyntaxError,
        UnicodeError,
        ValueError,
    ):
        closure = {}
        context_valid = False
    expected = (
        _reconciled_expected_receipt_material(
            step=step,
            registry=registry,
            accepted=accepted,
            closure=closure,
            root=root,
        )
        if valid_step and context_valid
        else None
    )
    current = value.get("current_binding")
    if (
        expected is None
        or type(current) is not dict
        or set(current) != _RECONCILED_CURRENT_KEYS
        or current != expected["current_binding"]
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
        or type(owners) is not list
        or owners != expected["actual_owners"]
    ):
        issues.add(
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_"
            "ACTUAL_OWNER_BINDING_INVALID"
        )
    contracts = value.get("strict_contracts")
    if (
        expected is None
        or type(contracts) is not list
        or contracts != expected["strict_contracts"]
        or any(
            type(contract) is not dict
            or type(contract.get("invariant_ids")) is not list
            or any(
                not _MACHINE_RE.fullmatch(str(item))
                for item in contract.get("invariant_ids", [])
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
    if (
        expected is None
        or value.get("positive_proof") != expected["positive_proof"]
    ):
        issues.add(
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_POSITIVE_PROOF_INVALID"
        )
    if (
        expected is None
        or value.get("independent_negative_proof")
        != expected["independent_negative_proof"]
    ):
        issues.add(
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_"
            "INDEPENDENT_NEGATIVE_PROOF_INVALID"
        )
    artifact = value.get("artifact_receipt")
    if (
        expected is None
        or type(artifact) is not dict
        or set(artifact) != _RECONCILED_ARTIFACT_KEYS
        or artifact != expected["artifact_receipt"]
    ):
        issues.add(
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_"
            "ARTIFACT_BINDING_INVALID"
        )
    parent = value.get("parent_binding")
    if step == 0 and expected is not None:
        expected_parent = {
            "kind": "source_baseline_locked_event_1",
            "event_name": "SOURCE_BASELINE_LOCKED",
            "event_ordinal": 1,
            "source_baseline_event_sha256": event["event_sha256"],
            "source_commit": accepted["source_commit"],
            "source_tree": accepted["source_tree"],
            "canonical_current_closure_sha256": accepted[
                "canonical_current_closure_sha256"
            ],
        }
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
    elif valid_step and step > 0 and expected is not None:
        previous_valid = (
            type(previous_receipt) is dict
            and set(previous_receipt) == _RECEIPT_KEYS
            and previous_receipt.get("step_number") == step - 1
            and previous_receipt.get("verdict") == "PROVED"
            and previous_receipt.get("receipt_sha256")
            == _artifact_sha256(
                _hash_material(previous_receipt, "receipt_sha256")
            )
        )
        chain_valid = (
            True
            if _prior_chain_validated
            else _valid_prior_chain_independent(
                prior_receipts,
                step=step,
                previous_receipt=previous_receipt,
                repo_root=root,
                event=event,
                registry=registry,
                accepted=accepted,
            )
        )
        expected_parent = (
            {
                "kind": "previous_current_step_receipt",
                "previous_step": step - 1,
                "previous_receipt_sha256": previous_receipt[
                    "receipt_sha256"
                ],
                "source_commit": accepted["source_commit"],
                "source_tree": accepted["source_tree"],
                "source_baseline_event_sha256": accepted[
                    "source_baseline_event_sha256"
                ],
                "canonical_current_closure_sha256": accepted[
                    "canonical_current_closure_sha256"
                ],
            }
            if previous_valid
            else None
        )
        parent_valid = (
            previous_valid and chain_valid and parent == expected_parent
        )
    else:
        parent_valid = False
    if not parent_valid:
        issues.add(
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_PARENT_CHAIN_INVALID"
        )
    if (
        expected is None
        or value.get("completion_condition")
        != expected["completion_condition"]
        or value.get("verdict") != "PROVED"
    ):
        issues.add(
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_VERDICT_INVALID"
        )
    if (
        expected is None
        or value.get("stop_conditions") != expected["stop_conditions"]
        or type(value.get("stop_conditions")) is not list
        or any(
            type(stop) is not dict
            or set(stop) != _RECONCILED_STOP_KEYS
            or stop.get("triggered") is not False
            for stop in value.get("stop_conditions", [])
            if type(value.get("stop_conditions")) is list
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
    if value.get("body_free") is not True or not _body_free(value):
        issues.add(
            "RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_BODY_FREE_REQUIRED"
        )
    try:
        expected_hash = _artifact_sha256(
            _hash_material(value, "receipt_sha256")
        )
    except (KeyError, RecursionError, TypeError, UnicodeError, ValueError):
        expected_hash = None
    if expected_hash is None or value.get("receipt_sha256") != expected_hash:
        issues.add("RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_HASH_MISMATCH")
    return tuple(sorted(issues))


def verify_recovery_epoch001_all11_completion_chain(
    value: Any,
    *,
    repo_root: Path,
    requirement_registry: Mapping[str, Any] | None = None,
    accepted_test_run_receipt: Mapping[str, Any] | None = None,
    source_baseline_event: Mapping[str, Any] | None = None,
) -> tuple[str, ...]:
    """Verify exact11 ordering and atomic staged-not-published state."""

    if type(value) is not dict:
        return ("ALL11_INCOMPLETE",)
    issues: set[str] = set()
    if set(value) != _ALL11_KEYS:
        issues.add("ALL11_INCOMPLETE")
    if (
        value.get("schema_version") != _ALL11_SCHEMA
        or value.get("candidate_version_id") != _CANDIDATE
        or value.get("recovery_epoch") != 1
    ):
        issues.add("ALL11_INCOMPLETE")
    root = Path(repo_root).resolve()
    registry = (
        dict(requirement_registry)
        if type(requirement_registry) is dict
        else {}
    )
    accepted = (
        dict(accepted_test_run_receipt)
        if type(accepted_test_run_receipt) is dict
        else {}
    )
    event = (
        dict(source_baseline_event)
        if type(source_baseline_event) is dict
        else {}
    )
    if verify_recovery_epoch001_current_step_requirement_registry(
        registry,
        repo_root=root,
    ) or verify_recovery_epoch001_accepted_test_run_receipt(
        accepted,
        repo_root=root,
        requirement_registry=registry,
        source_baseline_event=event,
    ):
        issues.add("SOURCE_OR_ROOT_MISMATCH")
    receipts = value.get("receipts")
    if type(receipts) is not list or len(receipts) != 11:
        issues.add("ALL11_INCOMPLETE")
        receipts = []
    if (
        value.get("receipt_count") != 11
        or value.get("ordered_steps") != list(range(11))
        or [
            receipt.get("step_number")
            for receipt in receipts
            if type(receipt) is dict
        ]
        != list(range(11))
    ):
        issues.add("RECEIPT_ORDER_INVALID")
    previous: Mapping[str, Any] | None = None
    for step, receipt in enumerate(receipts):
        receipt_issues = (
            verify_recovery_epoch001_current_step_completion_receipt(
                receipt,
                repo_root=root,
                previous_receipt=previous,
                step0_parent_authority=event,
                requirement_registry=registry,
                accepted_test_run_receipt=accepted,
                prior_receipts=tuple(receipts[:step]),
            )
        )
        if receipt_issues:
            issues.add("OWNER_VERIFIER_CONFLICT")
        previous = receipt if type(receipt) is dict else None
    receipt_hashes = [
        receipt.get("receipt_sha256")
        for receipt in receipts
        if type(receipt) is dict
    ]
    if value.get("receipt_sha256s") != receipt_hashes:
        issues.add("PARENT_CHAIN_INVALID")
    root_fields = {
        "source_baseline_event_sha256": event.get("event_sha256"),
        "baseline_id": accepted.get("baseline_id"),
        "source_commit": accepted.get("source_commit"),
        "source_tree": accepted.get("source_tree"),
        "canonical_current_closure_sha256": accepted.get(
            "canonical_current_closure_sha256"
        ),
        "source_dependency_closure_sha256": accepted.get(
            "source_dependency_closure_sha256"
        ),
        "registry_sha256": registry.get("registry_sha256"),
        "accepted_test_run_receipt_sha256": accepted.get(
            "accepted_test_run_receipt_sha256"
        ),
    }
    if any(value.get(key) != expected for key, expected in root_fields.items()):
        issues.add("SOURCE_OR_ROOT_MISMATCH")
    if value.get("required_sequence_event_2") != {
        "event_name": "STEP0_10_PREREQUISITES_PROVED",
        "event_ordinal": 2,
        "event_1_sha256": event.get("event_sha256"),
    }:
        issues.add("SEQUENCE_INVALID")
    if value.get("next_authority") != _NEXT_BY_STEP[10]:
        issues.add("NEXT_AUTHORITY_INVALID")
    if value.get("publication_state") != "STAGED_NOT_PUBLISHED":
        issues.add("PUBLICATION_CONFLICT")
    if value.get("automatic_progression") is not False:
        issues.add("P2_NOT_AUTHORIZED")
    if value.get("body_free") is not True or not _body_free(value):
        issues.add("BODY_FREE_VIOLATION")
    try:
        expected_hash = _artifact_sha256(
            _hash_material(value, "all11_completion_chain_sha256")
        )
    except (KeyError, RecursionError, TypeError, UnicodeError, ValueError):
        expected_hash = None
    if (
        expected_hash is None
        or value.get("all11_completion_chain_sha256") != expected_hash
    ):
        issues.add("HASH_MISMATCH")
    return tuple(sorted(issues))


_verify_registry_reconciled_impl = (
    verify_recovery_epoch001_current_step_requirement_registry
)
_verify_accepted_run_reconciled_impl = (
    verify_recovery_epoch001_accepted_test_run_receipt
)
_verify_receipt_reconciled_impl = (
    verify_recovery_epoch001_current_step_completion_receipt
)
_verify_all11_reconciled_impl = (
    verify_recovery_epoch001_all11_completion_chain
)


def verify_recovery_epoch001_current_step_requirement_registry(
    value: Any,
    *,
    repo_root: Path,
) -> tuple[str, ...]:
    try:
        return _verify_registry_reconciled_impl(
            value,
            repo_root=repo_root,
        )
    except (
        AttributeError,
        KeyError,
        OSError,
        RecursionError,
        subprocess.SubprocessError,
        SyntaxError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        return ("RECOVERY_CURRENT_STEP_REQUIREMENT_REGISTRY_ENTRY_INVALID",)


def verify_recovery_epoch001_accepted_test_run_receipt(
    value: Any,
    *,
    repo_root: Path,
    requirement_registry: Mapping[str, Any] | None = None,
    source_baseline_event: Mapping[str, Any] | None = None,
) -> tuple[str, ...]:
    try:
        return _verify_accepted_run_reconciled_impl(
            value,
            repo_root=repo_root,
            requirement_registry=requirement_registry,
            source_baseline_event=source_baseline_event,
        )
    except (
        AttributeError,
        KeyError,
        OSError,
        RecursionError,
        subprocess.SubprocessError,
        SyntaxError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        return ("RECOVERY_ACCEPTED_TEST_RUN_RECEIPT_ENTRY_INVALID",)


def verify_recovery_epoch001_current_step_completion_receipt(
    value: Any,
    *,
    repo_root: Path,
    previous_receipt: Mapping[str, Any] | None = None,
    step0_parent_authority: Mapping[str, Any] | None = None,
    requirement_registry: Mapping[str, Any] | None = None,
    accepted_test_run_receipt: Mapping[str, Any] | None = None,
    accepted_test_results: Mapping[str, Any] | None = None,
    prior_receipts: Sequence[Mapping[str, Any]] | None = None,
) -> tuple[str, ...]:
    try:
        return _verify_receipt_reconciled_impl(
            value,
            repo_root=repo_root,
            previous_receipt=previous_receipt,
            step0_parent_authority=step0_parent_authority,
            requirement_registry=requirement_registry,
            accepted_test_run_receipt=accepted_test_run_receipt,
            accepted_test_results=accepted_test_results,
            prior_receipts=prior_receipts,
        )
    except (
        AttributeError,
        KeyError,
        OSError,
        RecursionError,
        subprocess.SubprocessError,
        SyntaxError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        return ("RECOVERY_CURRENT_STEP_COMPLETION_RECEIPT_ENTRY_INVALID",)


def verify_recovery_epoch001_all11_completion_chain(
    value: Any,
    *,
    repo_root: Path,
    requirement_registry: Mapping[str, Any] | None = None,
    accepted_test_run_receipt: Mapping[str, Any] | None = None,
    source_baseline_event: Mapping[str, Any] | None = None,
) -> tuple[str, ...]:
    try:
        return _verify_all11_reconciled_impl(
            value,
            repo_root=repo_root,
            requirement_registry=requirement_registry,
            accepted_test_run_receipt=accepted_test_run_receipt,
            source_baseline_event=source_baseline_event,
        )
    except (
        AttributeError,
        KeyError,
        OSError,
        RecursionError,
        subprocess.SubprocessError,
        SyntaxError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        return ("ALL11_INCOMPLETE",)
