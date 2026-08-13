#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""Run the frozen exact-100 corpus through the current rc0031 Product builder.

This is a one-shot, private G8 runner.  It deliberately bypasses G7 and emits
one current-RC output only for each selected rc0027 base case.  It does not
activate the production route and it does not add a checker, controller,
file-descriptor protocol, or approval authority.  Body-full rows are written
only beside a body-free HMAC summary in an existing caller-owned 0700
directory outside the repository.
"""

import argparse
import ast
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from contextlib import redirect_stderr, redirect_stdout
import hashlib
import hmac
import io
import json
import os
from pathlib import Path
import re
import stat as stat_module
import sys
from typing import Any, Mapping, Sequence


AI_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = AI_ROOT.parent.resolve()
SERVICES = AI_ROOT / "services" / "ai_inference"
HELPERS = AI_ROOT / "tests" / "helpers"
TOOLS = AI_ROOT / "tools"
for entry in (SERVICES, HELPERS, TOOLS):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

_BATCH_PATH = (
    AI_ROOT
    / "tests"
    / "fixtures"
    / "emlis_nls_v3"
    / "generated"
    / "batch_001.jsonl"
)
_MANIFEST_PATH = _BATCH_PATH.with_name("batch_001_manifest.json")
_PRIVATE_FILENAME = "current_rc_g8_exact100_private.json"
_BODY_FREE_FILENAME = "current_rc_g8_exact100_body_free.json"
_PRIVATE_SCHEMA = "cocolon.emlis.nls_v3.current_rc.g8.private_exact100.v3"
_BODY_FREE_SCHEMA = (
    "cocolon.emlis.nls_v3.current_rc.g8.body_free_exact100.v3"
)
_CASE_RE = re.compile(r"^nls3s_b001_[0-9]{4}$")
_RUN_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{2,63}$")
_CODE_RE = re.compile(r"^[A-Z][A-Z0-9_]{2,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ALLOWED_DISPOSITIONS = frozenset(
    {"selected", "no_valid_candidate", "fail_close"}
)
_TRUST_PROJECTION_FIELDS = (
    "source_atom_id",
    "semantic_family",
    "base_parsed_atom_id",
    "base_obligation_id",
    "match_basis",
    "base_surface_sha256",
    "source_authority_sha256",
    "independent_binding_sha256",
)
_CHECK_KEYS = (
    "input_projected",
    "base_runtime_valid",
    "current_builder_called",
    "final_utf8_valid",
    "inverse_layout_exact",
    "semantic_atoms_exact",
    "construction_modifiers_exact",
    "reception_bindings_exact",
    "dimension_loci_exact",
)
_PRIVATE_ROW_KEYS = frozenset(
    {
        "case_id",
        "source_case_commitment",
        "source_input",
        "disposition",
        "current_candidate_id",
        "candidate_output_utf8",
        "machine_checks",
        "failure_code",
        "exception_captured",
    }
)
_PUBLIC_FAILURE_CODES = frozenset(
    {
        "CURRENT_RC_G8_BASE_RUNTIME_INVALID",
        "CURRENT_RC_G8_BASE_STATUS_INVALID",
        "CURRENT_RC_G8_CASE_REJECTED",
        "CURRENT_RC_G8_CURRENT_BUILDER_UNAVAILABLE",
        "CURRENT_RC_G8_INVERSE_REJECTED",
        "CURRENT_RC_G8_PRIVATE_OUTPUT_INVALID",
        "STEP11_GROUNDED_PHRASE_AMBIGUOUS",
        "STEP11_INPUT_SPECIFIC_ANCHOR_UNRESOLVED",
        "STEP11_RC0031_OWNER_ROLE_TYPED_RECOMPOSITION_INVALID",
        "STEP11_RC0031_PRODUCT_OWNER_EXPRESSION_INVALID",
        "STEP11_RELATION_MULTI_EDGE_LOCAL_ANAPHORA_AMBIGUOUS",
        "STEP11_REQUIRED_OWNER_INPUT_SPECIFICITY_UNRESOLVED",
    }
)
_PAIR_KEYS = frozenset({"body_free_core_sha256", "run_hmac"})
_SOURCE_SEARCH_ROOTS = (SERVICES, HELPERS, TOOLS)


class CurrentRcG8RunError(RuntimeError):
    """Path-free runner failure containing one closed code."""

    def __init__(self, code: str) -> None:
        if type(code) is not str or _CODE_RE.fullmatch(code) is None:
            code = "CURRENT_RC_G8_RUN_FAILED"
        self.code = code
        super().__init__(code)


def _canonical_json_bytes(value: Any) -> bytes:
    try:
        return (
            json.dumps(
                value,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode("utf-8", errors="strict")
            + b"\n"
        )
    except Exception as exc:
        raise CurrentRcG8RunError(
            "CURRENT_RC_G8_RESULT_NOT_CANONICAL"
        ) from exc


def _closed_code(exc: BaseException) -> str:
    code = getattr(exc, "code", None)
    if type(code) is str and _CODE_RE.fullmatch(code) is not None:
        return code
    return "CURRENT_RC_G8_CASE_REJECTED"


def _empty_checks() -> dict[str, bool]:
    return {key: False for key in _CHECK_KEYS}


def _exact100_sources(
    batch_path: Path,
    manifest_path: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, str]]:
    from emlis_ai_step10_app_reachable_contract_v3 import (
        project_app_reachable_input,
    )
    from emlis_nls_v3_batch_run import load_validated_batch

    samples, manifest = load_validated_batch(
        batch_path.resolve(), manifest_path.resolve()
    )
    expected_ids = tuple(f"nls3s_b001_{index:04d}" for index in range(1, 101))
    actual_ids = tuple(row.get("case_id") for row in samples)
    manifest_ids = tuple(manifest.get("case_ids", ()))
    commitments = manifest.get("case_commitments")
    if (
        len(samples) != 100
        or manifest.get("case_count") != 100
        or actual_ids != expected_ids
        or manifest_ids != expected_ids
        or type(commitments) is not list
        or len(commitments) != 100
    ):
        raise CurrentRcG8RunError("CURRENT_RC_G8_EXACT100_REQUIRED")
    commitment_by_case: dict[str, str] = {}
    for row in commitments:
        if type(row) is not dict:
            raise CurrentRcG8RunError("CURRENT_RC_G8_CASE_COMMITMENT_INVALID")
        case_id = row.get("case_id")
        commitment = row.get("case_commitment")
        if (
            type(case_id) is not str
            or _CASE_RE.fullmatch(case_id) is None
            or type(commitment) is not str
            or re.fullmatch(r"[0-9a-f]{64}", commitment) is None
            or case_id in commitment_by_case
        ):
            raise CurrentRcG8RunError("CURRENT_RC_G8_CASE_COMMITMENT_INVALID")
        commitment_by_case[case_id] = commitment
    if tuple(commitment_by_case) != expected_ids:
        raise CurrentRcG8RunError("CURRENT_RC_G8_CASE_COMMITMENT_INVALID")
    for sample in samples:
        if type(sample) is not dict or type(sample.get("input")) is not dict:
            raise CurrentRcG8RunError("CURRENT_RC_G8_SAMPLE_INVALID")
        try:
            project_app_reachable_input(sample["input"])
        except Exception as exc:
            raise CurrentRcG8RunError("CURRENT_RC_G8_SAMPLE_INVALID") from exc
    return samples, manifest, commitment_by_case


def _repo_relative(path: Path) -> tuple[Path, str]:
    try:
        resolved = path.resolve(strict=True)
        relative = resolved.relative_to(REPO_ROOT).as_posix()
    except Exception as exc:
        raise CurrentRcG8RunError("CURRENT_RC_G8_SOURCE_UNAVAILABLE") from exc
    if (
        not relative
        or relative.startswith("../")
        or "/../" in relative
        or resolved != REPO_ROOT / relative
    ):
        raise CurrentRcG8RunError("CURRENT_RC_G8_SOURCE_UNAVAILABLE")
    return resolved, relative


def _module_name(root: Path, path: Path) -> str:
    relative = path.relative_to(root)
    parts = list(relative.parts)
    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    else:
        parts[-1] = Path(parts[-1]).stem
    return ".".join(parts)


def _local_module_index() -> tuple[dict[str, Path], dict[Path, str]]:
    by_name: dict[str, Path] = {}
    by_path: dict[Path, str] = {}
    for root in _SOURCE_SEARCH_ROOTS:
        for path in sorted(root.rglob("*.py")):
            resolved, _relative = _repo_relative(path)
            name = _module_name(root, resolved)
            if not name:
                continue
            prior = by_name.get(name)
            if prior is not None and prior != resolved:
                raise CurrentRcG8RunError(
                    "CURRENT_RC_G8_SOURCE_MODULE_AMBIGUOUS"
                )
            by_name[name] = resolved
            by_path[resolved] = name
    return by_name, by_path


def _import_candidates(
    tree: ast.AST,
    *,
    module_name: str,
    is_package: bool,
) -> tuple[str, ...]:
    names: set[str] = set()
    package = module_name.split(".") if is_package else module_name.split(".")[:-1]
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
            continue
        if isinstance(node, ast.ImportFrom):
            if node.level:
                drop = node.level - 1
                if drop > len(package):
                    continue
                base_parts = package[: len(package) - drop]
                if node.module:
                    base_parts.extend(node.module.split("."))
                base = ".".join(base_parts)
            else:
                base = node.module or ""
            if base:
                names.add(base)
            for alias in node.names:
                if alias.name != "*":
                    names.add(".".join(row for row in (base, alias.name) if row))
            continue
        if (
            isinstance(node, ast.Call)
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and type(node.args[0].value) is str
            and (
                isinstance(node.func, ast.Name)
                and node.func.id in {"import_module", "__import__"}
                or isinstance(node.func, ast.Attribute)
                and node.func.attr == "import_module"
            )
        ):
            names.add(node.args[0].value)
    return tuple(sorted(name for name in names if name))


def _transitive_local_python_sources(starts: Sequence[Path]) -> set[Path]:
    by_name, by_path = _local_module_index()
    pending = [path.resolve() for path in starts]
    sources: set[Path] = set()
    while pending:
        path = pending.pop()
        if path in sources:
            continue
        if path.suffix != ".py":
            continue
        _resolved, _relative = _repo_relative(path)
        try:
            tree = ast.parse(path.read_bytes(), filename=path.name)
        except Exception as exc:
            raise CurrentRcG8RunError("CURRENT_RC_G8_SOURCE_UNAVAILABLE") from exc
        sources.add(path)
        module_name = by_path.get(path, path.stem)
        for candidate in _import_candidates(
            tree,
            module_name=module_name,
            is_package=path.name == "__init__.py",
        ):
            name = candidate
            while name:
                imported = by_name.get(name)
                if imported is not None:
                    if imported not in sources:
                        pending.append(imported)
                    break
                name = name.rpartition(".")[0]
    return sources


def _closure_data_paths(batch_path: Path, manifest_path: Path) -> set[Path]:
    fixture_root = AI_ROOT / "tests" / "fixtures"
    schema_root = AI_ROOT / "tests" / "schemas"
    paths = {
        batch_path.resolve(),
        manifest_path.resolve(),
        batch_path.with_name("batch_001_coverage_matrix.json").resolve(),
        batch_path.with_name("batch_001_duplicate_report.json").resolve(),
    }
    paths.update(
        path.resolve()
        for path in (fixture_root / "emlis_nls_v3").rglob("*")
        if path.is_file()
    )
    paths.update(
        path.resolve()
        for path in fixture_root.glob("emlis_nls_v3_s*.json")
        if path.is_file()
    )
    paths.update(
        path.resolve()
        for path in schema_root.glob("emlis_nls_v3*.json")
        if path.is_file()
    )
    return paths


def _source_closure_paths(batch_path: Path, manifest_path: Path) -> tuple[Path, ...]:
    roots = (
        Path(__file__),
        SERVICES / "emlis_ai_step10_app_reachable_contract_v3.py",
        SERVICES / "emlis_ai_step11_runtime_adapter_v3.py",
        SERVICES / "emlis_ai_evidence_ledger_service.py",
        SERVICES
        / "emlis_ai_grounded_lexical_role_experiment_snapshot_successor_v3.py",
        SERVICES / "emlis_ai_step11_grounded_lexicalization_v3.py",
        SERVICES / "emlis_ai_step11_natural_surface_v3.py",
        SERVICES / "emlis_ai_step11_natural_surface_matcher_v3.py",
        SERVICES / "emlis_ai_step11_rc0031_experiment_surface_catalog_v3.py",
        SERVICES / "emlis_ai_step11_rc0031_reception_focus_authority_v3.py",
        TOOLS / "emlis_nls_v3_batch_run.py",
        TOOLS / "emlis_nls_v3_rc0029_surface_repair_bounded_experiment.py",
        HELPERS / "emlis_nls_v3_s2_sample_registry.py",
    )
    for path in roots:
        _repo_relative(path)
    paths = _transitive_local_python_sources(roots)
    paths.update(_closure_data_paths(batch_path, manifest_path))
    return tuple(sorted(paths, key=lambda path: _repo_relative(path)[1]))


def _closure_digest(files: Sequence[Mapping[str, Any]]) -> str:
    return hashlib.sha256(
        b"cocolon.current-rc.g8.source-closure.v3\0"
        + _canonical_json_bytes(list(files))
    ).hexdigest()


def _source_closure_snapshot(
    batch_path: Path,
    manifest_path: Path,
) -> dict[str, Any]:
    rows: list[dict[str, str]] = []
    try:
        for path in _source_closure_paths(batch_path, manifest_path):
            resolved, relative = _repo_relative(path)
            rows.append(
                {
                    "path": relative,
                    "sha256": hashlib.sha256(resolved.read_bytes()).hexdigest(),
                }
            )
    except CurrentRcG8RunError:
        raise
    except Exception as exc:
        raise CurrentRcG8RunError("CURRENT_RC_G8_SOURCE_UNAVAILABLE") from exc
    return {
        "source_closure_sha256": _closure_digest(rows),
        "source_closure_file_count": len(rows),
        "source_closure_files": rows,
    }


def _source_closure(batch_path: Path, manifest_path: Path) -> str:
    """Compatibility projection of the recomputable v3 closure."""

    return str(
        _source_closure_snapshot(batch_path, manifest_path)[
            "source_closure_sha256"
        ]
    )


def _validated_source_snapshot(value: Any) -> dict[str, Any]:
    if type(value) is not dict or set(value) != {
        "source_closure_sha256",
        "source_closure_file_count",
        "source_closure_files",
    }:
        raise CurrentRcG8RunError("CURRENT_RC_G8_SOURCE_CLOSURE_INVALID")
    files = value.get("source_closure_files")
    if (
        type(value.get("source_closure_sha256")) is not str
        or _SHA256_RE.fullmatch(value["source_closure_sha256"]) is None
        or type(value.get("source_closure_file_count")) is not int
        or type(files) is not list
        or not files
    ):
        raise CurrentRcG8RunError("CURRENT_RC_G8_SOURCE_CLOSURE_INVALID")
    previous = ""
    for row in files:
        if type(row) is not dict or set(row) != {"path", "sha256"}:
            raise CurrentRcG8RunError("CURRENT_RC_G8_SOURCE_CLOSURE_INVALID")
        path = row.get("path")
        sha256 = row.get("sha256")
        if (
            type(path) is not str
            or not path
            or Path(path).is_absolute()
            or ".." in Path(path).parts
            or path <= previous
            or type(sha256) is not str
            or _SHA256_RE.fullmatch(sha256) is None
        ):
            raise CurrentRcG8RunError("CURRENT_RC_G8_SOURCE_CLOSURE_INVALID")
        previous = path
    if (
        value.get("source_closure_file_count") != len(files)
        or value.get("source_closure_sha256") != _closure_digest(files)
    ):
        raise CurrentRcG8RunError("CURRENT_RC_G8_SOURCE_CLOSURE_INVALID")
    return {
        "source_closure_sha256": value["source_closure_sha256"],
        "source_closure_file_count": len(files),
        "source_closure_files": [dict(row) for row in files],
    }


def _assert_source_unchanged(
    expected: Mapping[str, Any],
    batch_path: Path,
    manifest_path: Path,
    *,
    code: str,
) -> None:
    expected_snapshot = _validated_source_snapshot(expected)
    current = _source_closure_snapshot(batch_path, manifest_path)
    if _canonical_json_bytes(current) != _canonical_json_bytes(expected_snapshot):
        raise CurrentRcG8RunError(code)


def _bound_exact100_sources(
    batch_path: Path,
    manifest_path: Path,
) -> tuple[
    list[dict[str, Any]],
    dict[str, Any],
    dict[str, str],
    tuple[tuple[str, str, bytes], ...],
    dict[str, Any],
]:
    """Load exact100 only inside one stable, recomputable source closure."""

    source_snapshot = _source_closure_snapshot(batch_path, manifest_path)
    samples, manifest, commitment_by_case = _exact100_sources(
        batch_path, manifest_path
    )
    _assert_source_unchanged(
        source_snapshot,
        batch_path,
        manifest_path,
        code="CURRENT_RC_G8_SOURCE_CHANGED_DURING_PREFLIGHT",
    )
    case_sources = _exact100_source_bindings(samples, commitment_by_case)
    return (
        samples,
        manifest,
        commitment_by_case,
        case_sources,
        source_snapshot,
    )


def _exact100_source_bindings(
    samples: Sequence[Mapping[str, Any]],
    commitment_by_case: Mapping[str, str],
) -> tuple[tuple[str, str, bytes], ...]:
    """Bind each exact100 row to its validated frozen input and manifest row."""

    expected_ids = tuple(
        f"nls3s_b001_{index:04d}" for index in range(1, 101)
    )
    if len(samples) != 100 or tuple(commitment_by_case) != expected_ids:
        raise CurrentRcG8RunError(
            "CURRENT_RC_G8_CASE_SOURCE_BINDING_INVALID"
        )
    bindings: list[tuple[str, str, bytes]] = []
    for expected_id, sample in zip(expected_ids, samples, strict=True):
        commitment = commitment_by_case.get(expected_id)
        if (
            type(sample) is not dict
            or sample.get("case_id") != expected_id
            or type(sample.get("input")) is not dict
            or type(commitment) is not str
            or _SHA256_RE.fullmatch(commitment) is None
        ):
            raise CurrentRcG8RunError(
                "CURRENT_RC_G8_CASE_SOURCE_BINDING_INVALID"
            )
        bindings.append(
            (
                expected_id,
                commitment,
                _canonical_json_bytes(sample["input"]),
            )
        )
    return tuple(bindings)


def _owner_term(
    value: str,
    owner_lexicon: Mapping[str, tuple[str, str, str, str]],
    catalog: Mapping[str, Any],
    grammar: Mapping[str, Any],
) -> tuple[str, tuple[str, ...]] | None:
    referent_tokens = tuple(
        sorted(
            {
                str(row)
                for row in grammar["referent_scope_cues"].values()
                if row
            },
            key=len,
            reverse=True,
        )
    )
    normalized = value
    for _bound in range(2):
        token = next(
            (row for row in referent_tokens if normalized.startswith(row)),
            None,
        )
        if token is None:
            break
        normalized = normalized[len(token) :]
    fragments = tuple(
        (str(code), str(fragment))
        for code, fragment in catalog[
            "construction_predicate_fragments"
        ].items()
    )
    matches: list[tuple[str, tuple[str, ...]]] = []
    for expression, owner in owner_lexicon.items():
        if normalized == expression:
            matches.append((owner[0], ()))
        for first_code, first_fragment in fragments:
            if normalized == expression + first_fragment:
                matches.append((owner[0], (first_code,)))
            for second_code, second_fragment in fragments:
                if normalized == expression + first_fragment + second_fragment:
                    matches.append((owner[0], (first_code, second_code)))
    unique = tuple(dict.fromkeys(matches))
    return unique[0] if len(unique) == 1 else None


def _owner_sequence(
    value: str,
    joiner: str,
    owner_lexicon: Mapping[str, tuple[str, str, str, str]],
    catalog: Mapping[str, Any],
    grammar: Mapping[str, Any],
) -> tuple[tuple[str, tuple[str, ...]], ...] | None:
    fragments = tuple(
        str(row)
        for row in catalog["construction_predicate_fragments"].values()
    )
    visible_terms = tuple(
        sorted(
            set(owner_lexicon)
            | {
                expression + first
                for expression in owner_lexicon
                for first in fragments
            }
            | {
                expression + first + second
                for expression in owner_lexicon
                for first in fragments
                for second in fragments
            },
            key=len,
            reverse=True,
        )
    )
    solutions: list[tuple[tuple[str, tuple[str, ...]], ...]] = []

    def walk(
        remaining: str,
        rows: tuple[tuple[str, tuple[str, ...]], ...],
    ) -> None:
        if not remaining:
            solutions.append(rows)
            return
        for visible in visible_terms:
            if remaining != visible and not remaining.startswith(visible + joiner):
                continue
            parsed = _owner_term(visible, owner_lexicon, catalog, grammar)
            if parsed is None:
                continue
            tail = "" if remaining == visible else remaining[len(visible + joiner) :]
            walk(tail, rows + (parsed,))

    walk(value, ())
    unique = tuple(dict.fromkeys(solutions))
    return unique[0] if len(unique) == 1 and unique[0] else None


def _template_match(template: str, value: str) -> tuple[str, str] | None:
    parts = re.split(r"(\{source\}|\{target\})", template)
    if parts.count("{source}") != 1 or parts.count("{target}") != 1:
        return None
    pattern = ""
    for part in parts:
        if part == "{source}":
            pattern += r"(?P<source>.+?)"
        elif part == "{target}":
            pattern += r"(?P<target>.+?)"
        else:
            pattern += re.escape(part)
    match = re.fullmatch(pattern, value)
    if match is None:
        return None
    return match.group("source"), match.group("target")


def _strip_dimension_prefixes(
    value: str,
    grammar: Mapping[str, Any],
) -> tuple[str, tuple[tuple[str, str], ...]]:
    registries = (
        ("temporal", grammar["temporal_scope_cues"]),
        ("modality", grammar["modality_cues"]),
        ("polarity", grammar["polarity_cues"]),
        ("referent", grammar["referent_scope_cues"]),
    )
    tokens = tuple(
        sorted(
            (
                (str(token), family, str(code))
                for family, registry in registries
                for code, token in registry.items()
                if token
            ),
            key=lambda row: len(row[0]),
            reverse=True,
        )
    )
    remainder = value
    recovered: list[tuple[str, str]] = []
    for _bound in range(8):
        match = next(
            (row for row in tokens if remainder.startswith(row[0])), None
        )
        if match is None:
            break
        token, family, code = match
        remainder = remainder[len(token) :]
        recovered.append((family, code))
    return remainder, tuple(recovered)


def _plan_owned_regions(
    actual_body: bytes,
    catalog: Mapping[str, Any],
    grammar: Mapping[str, Any],
    *,
    observation_group_ordinals: Sequence[int],
) -> tuple[tuple[str, ...], tuple[str, ...]] | None:
    try:
        actual = actual_body.decode("utf-8", errors="strict")
    except (AttributeError, UnicodeDecodeError):
        return None
    separator = str(grammar["section_separator"])
    header = str(grammar["observation_header"])
    suffix = str(catalog["clause_morphology"]["sentence_suffix"])
    if (
        actual.count(separator) != 1
        or not actual.startswith(header)
        or not header.endswith("\n")
    ):
        return None
    actual_observation, actual_reception = actual.split(separator, 1)
    observation_material = actual_observation[len(header) :]
    actual_lines = observation_material.split("\n")
    if any(not line for line in actual_lines):
        return None
    expected_groups = tuple(sorted(set(observation_group_ordinals)))
    if any(not 1 <= group <= len(actual_lines) for group in expected_groups):
        return None
    clusters: list[str] = []
    for group in expected_groups:
        actual_line = actual_lines[group - 1]
        if not actual_line.endswith(suffix):
            return None
        product = actual_line[: -len(suffix)]
        if not product:
            return None
        clusters.append(product)
    sentence_join = str(
        catalog["clause_morphology"]["grammatical_sentence_join"]
    )
    receptions: list[str] = []
    for line in actual_reception.split("\n"):
        if not line:
            continue
        if not line.endswith(suffix):
            return None
        receptions.extend(
            row for row in line[: -len(suffix)].split(sentence_join) if row
        )
    return tuple(clusters), tuple(receptions)


def _parse_observation(
    clusters: Sequence[str],
    owner_lexicon: Mapping[str, tuple[str, str, str, str]],
    catalog: Mapping[str, Any],
    grammar: Mapping[str, Any],
) -> dict[str, Any]:
    atoms: Counter[Any] = Counter()
    modifiers: Counter[Any] = Counter()
    unparsed = 0
    ambiguous = 0
    temporal_loci = 0
    separators = {
        str(grammar["clause_join"]),
        *(str(row) for row in grammar["atom_joiners"]),
        str(catalog["clause_morphology"]["within_sentence_clause_join"]),
        str(catalog["clause_morphology"]["grammatical_sentence_join"]),
    }
    split_pattern = "|".join(
        re.escape(row) for row in sorted(separators, key=len, reverse=True) if row
    )
    for cluster in clusters:
        pieces = tuple(row for row in re.split(split_pattern, cluster) if row)
        temporal_seen = False
        parsed_in_cluster = 0
        for raw_piece in pieces:
            piece, dimensions = _strip_dimension_prefixes(raw_piece, grammar)
            temporal_seen = temporal_seen or any(
                row[0] == "temporal" for row in dimensions
            )
            matches: list[
                tuple[str, str, str, tuple[str, ...], tuple[Any, ...]]
            ] = []
            for family, registry in (
                ("relation", catalog["relation_predicate_fragments"]),
                ("semantic_link", catalog["semantic_link_predicate_fragments"]),
            ):
                for compound_key, template in registry.items():
                    endpoints = _template_match(str(template), piece)
                    if endpoints is None:
                        continue
                    source = _owner_term(
                        endpoints[0], owner_lexicon, catalog, grammar
                    )
                    target = _owner_term(
                        endpoints[1], owner_lexicon, catalog, grammar
                    )
                    if source is None or target is None:
                        continue
                    semantic_key, direction = str(compound_key).rsplit(":", 1)
                    matches.append(
                        (
                            family,
                            semantic_key,
                            direction,
                            (source[0], target[0]),
                            (source, target),
                        )
                    )
            unknown_join = str(
                catalog["clause_morphology"]["unknown_owner_join"]
            )
            for semantic_key, fragment in catalog[
                "unknown_predicate_fragments"
            ].items():
                fragment = str(fragment)
                if not piece.endswith(fragment):
                    continue
                owners = _owner_sequence(
                    piece[: -len(fragment)],
                    unknown_join,
                    owner_lexicon,
                    catalog,
                    grammar,
                )
                if owners is not None:
                    matches.append(
                        (
                            "explicit_unknown",
                            str(semantic_key),
                            "unknown",
                            tuple(row[0] for row in owners),
                            owners,
                        )
                    )
            standalone = str(
                catalog["clause_morphology"]["construction_standalone_predicate"]
            )
            for semantic_key, fragment in catalog[
                "construction_predicate_fragments"
            ].items():
                suffix = str(fragment) + standalone
                if not piece.endswith(suffix):
                    continue
                owner = _owner_term(
                    piece[: -len(suffix)], owner_lexicon, catalog, grammar
                )
                if owner is not None and not owner[1]:
                    matches.append(
                        (
                            "construction",
                            str(semantic_key),
                            "",
                            (owner[0],),
                            (owner,),
                        )
                    )
            unique = tuple(dict.fromkeys(matches))
            if len(unique) != 1:
                ambiguous += len(unique) > 1
                if parsed_in_cluster:
                    unparsed += len(unique) == 0
                continue
            family, semantic_key, direction, owners, owner_rows = unique[0]
            parsed_in_cluster += 1
            atoms[(family, semantic_key, direction, owners)] += 1
            for owner_id, construction_codes in owner_rows:
                for code in construction_codes:
                    atoms[("construction", code, "", (owner_id,))] += 1
                    modifiers[(code, owner_id)] += 1
        if not parsed_in_cluster:
            unparsed += 1
        temporal_loci += temporal_seen and bool(parsed_in_cluster)
    return {
        "atoms": atoms,
        "modifiers": modifiers,
        "unparsed": unparsed,
        "ambiguous": ambiguous,
        "temporal_loci": temporal_loci,
    }


def _parse_reception(
    clauses: Sequence[str],
    owner_lexicon: Mapping[str, tuple[str, str, str, str]],
    catalog: Mapping[str, Any],
    grammar: Mapping[str, Any],
) -> tuple[Counter[Any], int]:
    actual: Counter[Any] = Counter()
    ambiguous = 0
    morphology = catalog["clause_morphology"]
    for clause in clauses:
        candidates: list[tuple[str, tuple[str, ...], tuple[str, ...]]] = []
        for act_code, act in catalog[
            "reception_act_predicate_fragments"
        ].items():
            suffix = str(morphology["reception_object_particle"]) + str(act)
            if not clause.endswith(suffix):
                continue
            owner_material = clause[: -len(suffix)]
            support_split = str(morphology["support_target_link"])
            variants: tuple[tuple[str, str], ...] = (("", owner_material),)
            if support_split in owner_material:
                variants += (tuple(owner_material.split(support_split, 1)),)
            for support_material, target_material in variants:
                targets = _owner_sequence(
                    target_material,
                    str(morphology["target_owner_join"]),
                    owner_lexicon,
                    catalog,
                    grammar,
                )
                supports = (
                    _owner_sequence(
                        support_material,
                        str(morphology["support_owner_join"]),
                        owner_lexicon,
                        catalog,
                        grammar,
                    )
                    if support_material
                    else ()
                )
                if (
                    targets is not None
                    and supports is not None
                    and all(not row[1] for row in (*supports, *targets))
                ):
                    candidates.append(
                        (
                            str(act_code),
                            tuple(row[0] for row in supports),
                            tuple(row[0] for row in targets),
                        )
                    )
        unique = tuple(dict.fromkeys(candidates))
        if len(unique) != 1:
            ambiguous += 1
            continue
        actual[unique[0]] += 1
    return actual, ambiguous


def _inverse_checks(
    candidate: Any,
    *,
    successor_snapshot: Any,
    lexical_atom_specs: Any,
    reception_focus_authority: Any,
) -> dict[str, bool]:
    from emlis_ai_step11_natural_surface_v3 import (
        _step11_rc0031_product_owner_projection,
        _step11_rc0031_product_surface_authorities,
    )

    body = candidate.rendered_surface.utf8_bytes
    try:
        utf8_valid = (
            type(body) is bytes
            and bool(body)
            and body.decode("utf-8", errors="strict").encode(
                "utf-8", errors="strict"
            )
            == body
            and hashlib.sha256(body).hexdigest()
            == candidate.rendered_surface.sha256
        )
        _catalog_owner, catalog, grammar, _catalog_sha = (
            _step11_rc0031_product_surface_authorities()
        )
        owner_rows = _step11_rc0031_product_owner_projection(
            candidate.base_candidate,
            successor_snapshot=successor_snapshot,
            lexical_atom_specs=lexical_atom_specs,
        )
        owner_lexicon = {
            str(row[3]): (
                str(row[0]),
                str(row[1]),
                str(row[2]),
                str(row[4]),
            )
            for row in owner_rows
        }
        product_bindings = tuple(
            candidate.surface_realization_plan.proposition_clause_bindings
        )
        regions = _plan_owned_regions(
            body,
            catalog,
            grammar,
            observation_group_ordinals=tuple(
                row.sentence_group_ordinal for row in product_bindings
            ),
        )
        if len(owner_lexicon) != len(owner_rows) or regions is None:
            raise ValueError("inverse_layout")
        parsed = _parse_observation(
            regions[0], owner_lexicon, catalog, grammar
        )
        actual_receptions, reception_ambiguous = _parse_reception(
            regions[1], owner_lexicon, catalog, grammar
        )

        expected_atoms: Counter[Any] = Counter()
        expected_modifiers: Counter[Any] = Counter()
        for binding in product_bindings:
            key_by_id = {
                str(atom_id): str(semantic_key)
                for atom_id, semantic_key in zip(
                    binding.source_atom_ids,
                    binding.semantic_keys,
                    strict=True,
                )
            }
            for family, semantic_key, direction, owners in zip(
                binding.semantic_families,
                binding.semantic_keys,
                binding.directions,
                binding.source_atom_owner_ids,
                strict=True,
            ):
                normalized_direction = (
                    str(direction)
                    if family in {"relation", "semantic_link"}
                    else "unknown"
                    if family == "explicit_unknown"
                    else ""
                )
                expected_atoms[
                    (
                        str(family),
                        str(semantic_key),
                        normalized_direction,
                        tuple(str(row) for row in owners),
                    )
                ] += 1
            for atom_id, owner_id in zip(
                binding.construction_modifier_atom_ids,
                binding.construction_modifier_target_owner_ids,
                strict=True,
            ):
                expected_modifiers[
                    (key_by_id[str(atom_id)], str(owner_id))
                ] += 1
        authority_by_opportunity = {
            str(row.source_reception_opportunity_id): row
            for row in reception_focus_authority.bindings
        }
        expected_receptions: Counter[Any] = Counter()
        for row in candidate.surface_realization_plan.reception_predication_bindings:
            authority = authority_by_opportunity[
                str(row.source_reception_opportunity_id)
            ]
            targets = tuple(str(owner) for owner in row.source_target_owner_ids)
            supports = tuple(
                owner
                for owner in dict.fromkeys(
                    (
                        *(str(owner) for owner in authority.source_focus_owner_ids),
                        *(
                            str(owner)
                            for owner in row.supporting_source_owner_ids
                        ),
                    )
                )
                if owner not in targets
            )
            expected_receptions[(str(row.reception_act), supports, targets)] += 1
        layout_exact = parsed["unparsed"] == 0 and parsed["ambiguous"] == 0
        semantic_exact = parsed["atoms"] == expected_atoms
        modifier_exact = parsed["modifiers"] == expected_modifiers
        reception_exact = (
            reception_ambiguous == 0
            and actual_receptions == expected_receptions
        )
        dimension_exact = parsed["temporal_loci"] == len(regions[0])
        return {
            "final_utf8_valid": bool(utf8_valid),
            "inverse_layout_exact": layout_exact,
            "semantic_atoms_exact": semantic_exact,
            "construction_modifiers_exact": modifier_exact,
            "reception_bindings_exact": reception_exact,
            "dimension_loci_exact": dimension_exact,
        }
    except Exception:
        return {
            "final_utf8_valid": False,
            "inverse_layout_exact": False,
            "semantic_atoms_exact": False,
            "construction_modifiers_exact": False,
            "reception_bindings_exact": False,
            "dimension_loci_exact": False,
        }


def _current_candidate(
    projected_input: Mapping[str, Any],
    *,
    source_closure: str,
) -> tuple[str, Any | None, dict[str, bool], str | None]:
    from emlis_ai_evidence_ledger_service import (
        build_evidence_ledger,
        build_evidence_span_resolver,
    )
    from emlis_ai_grounded_lexical_role_experiment_snapshot_successor_v3 import (
        build_grounded_lexical_role_experiment_snapshot_successor,
    )
    from emlis_ai_step11_grounded_lexicalization_v3 import (
        build_step11_rc0028_experiment_lexical_atom_specs,
    )
    from emlis_ai_step11_natural_surface_matcher_v3 import (
        match_step11_rc0030_base_body_exact_reuse,
        parse_step11_rc0030_base_body_exact_reuse,
    )
    import emlis_ai_step11_natural_surface_v3 as surface
    import emlis_ai_step11_rc0031_reception_focus_authority_v3 as authority_owner
    from emlis_ai_step11_runtime_adapter_v3 import (
        execute_step11_offline_v3,
    )

    checks = _empty_checks()
    checks["input_projected"] = True
    execution = execute_step11_offline_v3(
        dict(projected_input),
        candidate_version_id="nls_v3_rc_0027",
        source_dependency_closure_sha256=source_closure,
    )
    if execution.status == "v3_no_valid_candidate":
        if (
            execution.selected_candidate is not None
            or execution.final_utf8_bytes is not None
            or execution.selection_result.selected_candidate_id is not None
        ):
            return "fail_close", None, checks, "CURRENT_RC_G8_BASE_RUNTIME_INVALID"
        checks["base_runtime_valid"] = True
        return "no_valid_candidate", None, checks, None
    if (
        execution.status != "selected"
        or execution.selected_candidate is None
        or execution.selection_result.selected_candidate_id
        != execution.selected_candidate.candidate_id
        or execution.final_utf8_bytes
        != execution.selected_candidate.rendered_surface.utf8_bytes
        or not 1 <= len(execution.natural_candidates) <= 12
        or execution.v1_fallback_used is not False
    ):
        return "fail_close", None, checks, "CURRENT_RC_G8_BASE_STATUS_INVALID"
    checks["base_runtime_valid"] = True

    resolver = build_evidence_span_resolver(
        tuple(build_evidence_ledger(execution.normalized_input)),
        current_input=execution.normalized_input,
    )
    successor = build_grounded_lexical_role_experiment_snapshot_successor(
        execution.grounded_plan,
        resolver,
        observation_stage_context=execution.observation_stage_context,
        original_input_bundle=execution.normalized_input,
    )
    lexical_specs = build_step11_rc0028_experiment_lexical_atom_specs(successor)

    base = execution.selected_candidate
    witness = parse_step11_rc0030_base_body_exact_reuse(base.final_utf8_bytes)
    proof = match_step11_rc0030_base_body_exact_reuse(
        witness,
        successor_snapshot=successor,
        inventory_result=execution.inventory_result,
        content_plan=execution.content_plan,
        discourse_plan=base.discourse_plan,
        current_input=execution.projected_current_input,
    )
    if proof:
        bindings = tuple(
            surface.Step11Rc0031BaseBodyExactReuseBinding(
                **{
                    field: getattr(row, field)
                    for field in _TRUST_PROJECTION_FIELDS
                }
            )
            for row in proof
        )
        predecessor = (
            surface._step11_rc0031_build_candidate_from_verified_reuse_composition(
                base,
                successor_snapshot=successor,
                lexical_atom_specs=lexical_specs,
                verified_base_body_exact_reuse_bindings=bindings,
                validate_output=True,
            )
        )
    else:
        predecessor = surface.build_step11_rc0031_experiment_surface_candidate(
            base,
            successor_snapshot=successor,
            lexical_atom_specs=lexical_specs,
        )
    dimension_candidate = (
        surface.build_step11_rc0031_dimension_bearing_experiment_surface_candidate(
            predecessor,
            successor_snapshot=successor,
            lexical_atom_specs=lexical_specs,
        )
    )
    authority = authority_owner.build_step11_rc0031_reception_focus_authority(
        execution.grounded_plan,
        resolver,
        successor_snapshot=successor,
        base_candidate=dimension_candidate.base_candidate,
        inventory_result=execution.inventory_result,
        content_plan=execution.content_plan,
        current_input=execution.projected_current_input,
    )
    builder = getattr(
        surface,
        "_step11_rc0031_build_owner_role_inflected_typed_recomposition_candidate",
        None,
    )
    if not callable(builder):
        return "fail_close", None, checks, "CURRENT_RC_G8_CURRENT_BUILDER_UNAVAILABLE"
    current = builder(
        dimension_candidate,
        successor_snapshot=successor,
        lexical_atom_specs=lexical_specs,
        reception_focus_authority=authority,
        plan=execution.grounded_plan,
        resolver=resolver,
        inventory_result=execution.inventory_result,
        content_plan=execution.content_plan,
        current_input=execution.projected_current_input,
    )
    checks["current_builder_called"] = True
    checks.update(
        _inverse_checks(
            current,
            successor_snapshot=successor,
            lexical_atom_specs=lexical_specs,
            reception_focus_authority=authority,
        )
    )
    if not all(checks.values()):
        return "fail_close", current, checks, "CURRENT_RC_G8_INVERSE_REJECTED"
    return "selected", current, checks, None


def _case_row(
    sample: Mapping[str, Any],
    source_case_commitment: str,
    source_closure: str,
) -> dict[str, Any]:
    from emlis_ai_step10_app_reachable_contract_v3 import (
        project_app_reachable_input,
    )

    case_id = sample.get("case_id")
    checks = _empty_checks()
    exception_captured = False
    if type(case_id) is not str or _CASE_RE.fullmatch(case_id) is None:
        raise CurrentRcG8RunError("CURRENT_RC_G8_SAMPLE_INVALID")
    try:
        projected = project_app_reachable_input(sample["input"])
        checks["input_projected"] = True
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            disposition, candidate, checks, failure_code = _current_candidate(
                projected, source_closure=source_closure
            )
    except Exception as exc:
        disposition = "fail_close"
        candidate = None
        failure_code = _closed_code(exc)
        exception_captured = True
    output = None
    candidate_id = None
    if candidate is not None:
        candidate_id = str(candidate.candidate_id)
        try:
            output = candidate.rendered_surface.utf8_bytes.decode(
                "utf-8", errors="strict"
            )
        except Exception:
            disposition = "fail_close"
            failure_code = "CURRENT_RC_G8_PRIVATE_OUTPUT_INVALID"
            checks["final_utf8_valid"] = False
            exception_captured = True
    return {
        "case_id": case_id,
        "source_case_commitment": source_case_commitment,
        "source_input": dict(sample["input"]),
        "disposition": disposition,
        "current_candidate_id": candidate_id,
        "candidate_output_utf8": output,
        "machine_checks": checks,
        "failure_code": failure_code,
        "exception_captured": exception_captured,
    }


def _case_row_job(args: tuple[dict[str, Any], str, str]) -> dict[str, Any]:
    return _case_row(*args)


def _run_cases(
    samples: Sequence[dict[str, Any]],
    commitment_by_case: Mapping[str, str],
    source_closure: str,
    *,
    workers: int,
) -> list[dict[str, Any]]:
    jobs = tuple(
        (sample, commitment_by_case[str(sample["case_id"])], source_closure)
        for sample in samples
    )
    if workers == 1:
        return [_case_row_job(job) for job in jobs]
    with ProcessPoolExecutor(max_workers=workers) as executor:
        return list(executor.map(_case_row_job, jobs, chunksize=1))


def _validate_private_rows(
    rows: Any,
    *,
    expected_case_sources: Sequence[tuple[str, str, bytes]],
) -> list[dict[str, Any]]:
    if type(rows) is not list or len(rows) != 100:
        raise CurrentRcG8RunError("CURRENT_RC_G8_EXACT100_REQUIRED")
    expected_ids = tuple(f"nls3s_b001_{index:04d}" for index in range(1, 101))
    if (
        type(expected_case_sources) not in {list, tuple}
        or len(expected_case_sources) != 100
    ):
        raise CurrentRcG8RunError(
            "CURRENT_RC_G8_CASE_SOURCE_BINDING_INVALID"
        )
    actual: list[dict[str, Any]] = []
    for expected_id, raw, source_binding in zip(
        expected_ids, rows, expected_case_sources, strict=True
    ):
        if (
            type(source_binding) is not tuple
            or len(source_binding) != 3
            or source_binding[0] != expected_id
            or type(source_binding[1]) is not str
            or _SHA256_RE.fullmatch(source_binding[1]) is None
            or type(source_binding[2]) is not bytes
            or not source_binding[2]
        ):
            raise CurrentRcG8RunError(
                "CURRENT_RC_G8_CASE_SOURCE_BINDING_INVALID"
            )
        if type(raw) is not dict or set(raw) != _PRIVATE_ROW_KEYS:
            raise CurrentRcG8RunError("CURRENT_RC_G8_PRIVATE_ROW_INVALID")
        row = dict(raw)
        checks = row.get("machine_checks")
        candidate_id = row.get("current_candidate_id")
        output = row.get("candidate_output_utf8")
        failure = row.get("failure_code")
        disposition = row.get("disposition")
        exception_captured = row.get("exception_captured")
        if (
            row.get("case_id") != expected_id
            or type(row.get("source_case_commitment")) is not str
            or _SHA256_RE.fullmatch(row["source_case_commitment"]) is None
            or type(row.get("source_input")) is not dict
            or disposition not in _ALLOWED_DISPOSITIONS
            or type(exception_captured) is not bool
            or type(checks) is not dict
            # Canonical JSON sorts object keys, so validate the exact key set
            # rather than relying on the producer's insertion order.
            or set(checks) != set(_CHECK_KEYS)
            or any(type(value) is not bool for value in checks.values())
            or (
                candidate_id is not None
                and (type(candidate_id) is not str or not candidate_id)
            )
            or (output is not None and (type(output) is not str or not output))
            or (
                failure is not None
                and (
                    type(failure) is not str
                    or _CODE_RE.fullmatch(failure) is None
                )
            )
        ):
            raise CurrentRcG8RunError("CURRENT_RC_G8_PRIVATE_ROW_INVALID")
        if disposition == "selected":
            valid_state = (
                type(candidate_id) is str
                and type(output) is str
                and failure is None
                and exception_captured is False
                and all(checks.values())
            )
        elif disposition == "no_valid_candidate":
            valid_state = (
                candidate_id is None
                and output is None
                and failure is None
                and exception_captured is False
                and checks["input_projected"]
                and checks["base_runtime_valid"]
                and not checks["current_builder_called"]
                and not any(
                    checks[key]
                    for key in _CHECK_KEYS
                    if key
                    not in {"input_projected", "base_runtime_valid"}
                )
            )
        else:
            candidate_absent = (
                candidate_id is None
                and output is None
                and checks["current_builder_called"] is False
            )
            inverse_rejected = (
                type(candidate_id) is str
                and type(output) is str
                and failure == "CURRENT_RC_G8_INVERSE_REJECTED"
                and exception_captured is False
                and checks["input_projected"]
                and checks["base_runtime_valid"]
                and checks["current_builder_called"]
            )
            output_rejected = (
                type(candidate_id) is str
                and output is None
                and failure == "CURRENT_RC_G8_PRIVATE_OUTPUT_INVALID"
                and exception_captured is True
                and checks["input_projected"]
                and checks["base_runtime_valid"]
                and checks["current_builder_called"]
                and checks["final_utf8_valid"] is False
            )
            check_progression_exact = bool(
                (
                    checks["input_projected"]
                    or not any(
                        checks[key]
                        for key in _CHECK_KEYS
                        if key != "input_projected"
                    )
                )
                and (
                    checks["base_runtime_valid"]
                    or not any(
                        checks[key]
                        for key in _CHECK_KEYS
                        if key
                        not in {"input_projected", "base_runtime_valid"}
                    )
                )
                and (
                    checks["current_builder_called"]
                    or not any(
                        checks[key]
                        for key in _CHECK_KEYS
                        if key
                        not in {
                            "input_projected",
                            "base_runtime_valid",
                            "current_builder_called",
                        }
                    )
                )
            )
            valid_state = bool(
                type(failure) is str
                and not all(checks.values())
                and check_progression_exact
                and (candidate_absent or inverse_rejected or output_rejected)
            )
        if not valid_state:
            raise CurrentRcG8RunError("CURRENT_RC_G8_PRIVATE_STATE_INVALID")
        if (
            not hmac.compare_digest(
                row["source_case_commitment"], source_binding[1]
            )
            or _canonical_json_bytes(row["source_input"])
            != source_binding[2]
        ):
            raise CurrentRcG8RunError(
                "CURRENT_RC_G8_CASE_SOURCE_BINDING_INVALID"
            )
        actual.append(row)
    return actual


def _public_failure_reason(row: Mapping[str, Any]) -> str:
    disposition = row["disposition"]
    if disposition == "selected":
        return "CURRENT_RC_G8_SELECTED"
    if disposition == "no_valid_candidate":
        return "CURRENT_RC_G8_NO_VALID_CANDIDATE"
    code = row.get("failure_code")
    return (
        str(code)
        if code in _PUBLIC_FAILURE_CODES
        else "CURRENT_RC_G8_CASE_REJECTED"
    )


def _case_commitment(
    key: bytes,
    run_id: str,
    source_closure: str,
    ordinal: int,
    row: Mapping[str, Any],
) -> str:
    if type(key) is not bytes or len(key) != 32:
        raise CurrentRcG8RunError("CURRENT_RC_G8_COMMITMENT_KEY_INVALID")
    material = (
        b"cocolon.current-rc.g8.case-result.v3\0"
        + run_id.encode("ascii", errors="strict")
        + b"\0"
        + source_closure.encode("ascii", errors="strict")
        + b"\0"
        + str(ordinal).encode("ascii", errors="strict")
        + b"\0"
        + _canonical_json_bytes(row)
    )
    return hmac.new(key, material, hashlib.sha256).hexdigest()


def _public_case_row(
    row: Mapping[str, Any],
    *,
    ordinal: int,
    case_hmac: str,
) -> dict[str, Any]:
    return {
        "ordinal": ordinal,
        "case_id": row["case_id"],
        "source_case_commitment": row["source_case_commitment"],
        "disposition": row["disposition"],
        "candidate_present": row["current_candidate_id"] is not None,
        "output_present": row["candidate_output_utf8"] is not None,
        "exception_present": row["exception_captured"],
        "failure_reason_code": _public_failure_reason(row),
        "machine_checks": dict(row["machine_checks"]),
        "case_hmac": case_hmac,
    }


def _run_commitment(
    key: bytes,
    *,
    run_id: str,
    source_closure: str,
    private_core_sha256: str,
    body_free_core_sha256: str,
) -> str:
    material = (
        b"cocolon.current-rc.g8.run-pair.v3\0"
        + run_id.encode("ascii", errors="strict")
        + b"\0"
        + source_closure.encode("ascii", errors="strict")
        + b"\0"
        + private_core_sha256.encode("ascii", errors="strict")
        + b"\0"
        + body_free_core_sha256.encode("ascii", errors="strict")
    )
    return hmac.new(key, material, hashlib.sha256).hexdigest()


def _artifact_source_snapshot(value: Mapping[str, Any]) -> dict[str, Any]:
    return _validated_source_snapshot(
        {
            "source_closure_sha256": value.get("source_closure_sha256"),
            "source_closure_file_count": value.get(
                "source_closure_file_count"
            ),
            "source_closure_files": value.get("source_closure_files"),
        }
    )


def _validate_pair(
    private: Any,
    body_free: Any,
    *,
    key: bytes,
    expected_source: Mapping[str, Any],
    expected_case_sources: Sequence[tuple[str, str, bytes]],
) -> None:
    private_keys = {
        "schema_version",
        "run_id",
        "source_closure_sha256",
        "source_closure_file_count",
        "source_closure_files",
        "case_count",
        "cases",
        "pair_integrity",
    }
    body_free_keys = private_keys | {"disposition_counts"}
    body_free_keys.add("exception_count")
    if (
        type(private) is not dict
        or set(private) != private_keys
        or type(body_free) is not dict
        or set(body_free) != body_free_keys
        or private.get("schema_version") != _PRIVATE_SCHEMA
        or body_free.get("schema_version") != _BODY_FREE_SCHEMA
        or private.get("run_id") != body_free.get("run_id")
        or type(private.get("run_id")) is not str
        or _RUN_ID_RE.fullmatch(private["run_id"]) is None
        or private.get("case_count") != 100
        or body_free.get("case_count") != 100
    ):
        raise CurrentRcG8RunError("CURRENT_RC_G8_PAIR_SHAPE_INVALID")
    expected = _validated_source_snapshot(expected_source)
    private_source = _artifact_source_snapshot(private)
    body_free_source = _artifact_source_snapshot(body_free)
    if not (
        _canonical_json_bytes(private_source)
        == _canonical_json_bytes(body_free_source)
        == _canonical_json_bytes(expected)
    ):
        raise CurrentRcG8RunError("CURRENT_RC_G8_SOURCE_CLOSURE_INVALID")
    private_cases = private.get("cases")
    public_cases = body_free.get("cases")
    if (
        type(private_cases) is not list
        or len(private_cases) != 100
        or type(public_cases) is not list
        or len(public_cases) != 100
    ):
        raise CurrentRcG8RunError("CURRENT_RC_G8_EXACT100_REQUIRED")
    rows: list[dict[str, Any]] = []
    for ordinal, envelope in enumerate(private_cases, start=1):
        if (
            type(envelope) is not dict
            or set(envelope) != {"ordinal", "result", "case_hmac"}
            or envelope.get("ordinal") != ordinal
            or type(envelope.get("result")) is not dict
            or type(envelope.get("case_hmac")) is not str
            or _SHA256_RE.fullmatch(envelope["case_hmac"]) is None
        ):
            raise CurrentRcG8RunError("CURRENT_RC_G8_PRIVATE_ROW_INVALID")
        rows.append(dict(envelope["result"]))
    rows = _validate_private_rows(
        rows, expected_case_sources=expected_case_sources
    )
    source_closure = expected["source_closure_sha256"]
    for ordinal, (row, private_envelope, public_row) in enumerate(
        zip(rows, private_cases, public_cases, strict=True), start=1
    ):
        expected_hmac = _case_commitment(
            key,
            private["run_id"],
            source_closure,
            ordinal,
            row,
        )
        if not hmac.compare_digest(
            expected_hmac, private_envelope["case_hmac"]
        ):
            raise CurrentRcG8RunError(
                "CURRENT_RC_G8_HMAC_VERIFICATION_FAILED"
            )
        expected_public = _public_case_row(
            row, ordinal=ordinal, case_hmac=expected_hmac
        )
        if (
            type(public_row) is not dict
            or _canonical_json_bytes(public_row)
            != _canonical_json_bytes(expected_public)
        ):
            raise CurrentRcG8RunError(
                "CURRENT_RC_G8_BODY_FREE_PROJECTION_INVALID"
            )
    counts = Counter(row["disposition"] for row in rows)
    expected_counts = {
        disposition: counts.get(disposition, 0)
        for disposition in sorted(_ALLOWED_DISPOSITIONS)
    }
    if body_free.get("disposition_counts") != expected_counts:
        raise CurrentRcG8RunError("CURRENT_RC_G8_ACCOUNTING_INVALID")
    if body_free.get("exception_count") != sum(
        row["exception_captured"] for row in rows
    ):
        raise CurrentRcG8RunError("CURRENT_RC_G8_ACCOUNTING_INVALID")
    private_pair = private.get("pair_integrity")
    body_free_pair = body_free.get("pair_integrity")
    if (
        type(private_pair) is not dict
        or set(private_pair) != _PAIR_KEYS
        or type(body_free_pair) is not dict
        or set(body_free_pair) != _PAIR_KEYS
        or private_pair != body_free_pair
        or any(
            type(value) is not str or _SHA256_RE.fullmatch(value) is None
            for value in private_pair.values()
        )
    ):
        raise CurrentRcG8RunError("CURRENT_RC_G8_PAIR_INTEGRITY_INVALID")
    private_core = dict(private)
    body_free_core = dict(body_free)
    private_core.pop("pair_integrity")
    body_free_core.pop("pair_integrity")
    private_sha = hashlib.sha256(
        _canonical_json_bytes(private_core)
    ).hexdigest()
    body_free_sha = hashlib.sha256(
        _canonical_json_bytes(body_free_core)
    ).hexdigest()
    expected_run_hmac = _run_commitment(
        key,
        run_id=private["run_id"],
        source_closure=source_closure,
        private_core_sha256=private_sha,
        body_free_core_sha256=body_free_sha,
    )
    if (
        private_pair["body_free_core_sha256"] != body_free_sha
        or not hmac.compare_digest(
            private_pair["run_hmac"], expected_run_hmac
        )
    ):
        raise CurrentRcG8RunError(
            "CURRENT_RC_G8_HMAC_VERIFICATION_FAILED"
        )


def _decode_canonical_payload(payload: bytes) -> dict[str, Any]:
    try:
        if payload.startswith(b"\xef\xbb\xbf"):
            raise ValueError("bom")
        value = json.loads(payload.decode("utf-8", errors="strict"))
    except Exception as exc:
        raise CurrentRcG8RunError(
            "CURRENT_RC_G8_RESULT_NOT_CANONICAL"
        ) from exc
    if type(value) is not dict or _canonical_json_bytes(value) != payload:
        raise CurrentRcG8RunError("CURRENT_RC_G8_RESULT_NOT_CANONICAL")
    return value


def _result_payloads(
    rows: Sequence[dict[str, Any]],
    *,
    key: bytes,
    run_id: str,
    source_snapshot: Mapping[str, Any],
    expected_case_sources: Sequence[tuple[str, str, bytes]],
) -> tuple[bytes, bytes, dict[str, Any]]:
    if type(run_id) is not str or _RUN_ID_RE.fullmatch(run_id) is None:
        raise CurrentRcG8RunError("CURRENT_RC_G8_ARGUMENT_INVALID")
    source = _validated_source_snapshot(source_snapshot)
    private_rows = _validate_private_rows(
        list(rows), expected_case_sources=expected_case_sources
    )
    source_closure = source["source_closure_sha256"]
    private_cases: list[dict[str, Any]] = []
    body_free_cases: list[dict[str, Any]] = []
    for ordinal, row in enumerate(private_rows, start=1):
        commitment = _case_commitment(
            key, run_id, source_closure, ordinal, row
        )
        private_cases.append(
            {"ordinal": ordinal, "result": row, "case_hmac": commitment}
        )
        body_free_cases.append(
            _public_case_row(row, ordinal=ordinal, case_hmac=commitment)
        )
    disposition_counts = Counter(
        row["disposition"] for row in body_free_cases
    )
    common = {
        "run_id": run_id,
        "source_closure_sha256": source_closure,
        "source_closure_file_count": source["source_closure_file_count"],
        "source_closure_files": source["source_closure_files"],
        "case_count": 100,
    }
    private_core = {
        "schema_version": _PRIVATE_SCHEMA,
        **common,
        "cases": private_cases,
    }
    body_free_core = {
        "schema_version": _BODY_FREE_SCHEMA,
        **common,
        "disposition_counts": {
            disposition: disposition_counts.get(disposition, 0)
            for disposition in sorted(_ALLOWED_DISPOSITIONS)
        },
        "exception_count": sum(
            row["exception_captured"] for row in private_rows
        ),
        "cases": body_free_cases,
    }
    private_core_sha256 = hashlib.sha256(
        _canonical_json_bytes(private_core)
    ).hexdigest()
    body_free_core_sha256 = hashlib.sha256(
        _canonical_json_bytes(body_free_core)
    ).hexdigest()
    pair = {
        "body_free_core_sha256": body_free_core_sha256,
        "run_hmac": _run_commitment(
            key,
            run_id=run_id,
            source_closure=source_closure,
            private_core_sha256=private_core_sha256,
            body_free_core_sha256=body_free_core_sha256,
        ),
    }
    private = {**private_core, "pair_integrity": pair}
    body_free = {**body_free_core, "pair_integrity": pair}
    _validate_pair(
        private,
        body_free,
        key=key,
        expected_source=source,
        expected_case_sources=expected_case_sources,
    )
    return (
        _canonical_json_bytes(private),
        _canonical_json_bytes(body_free),
        body_free,
    )


def _write_outputs(
    output_dir: Path,
    private_payload: bytes,
    body_free_payload: bytes,
    *,
    key: bytes,
    source_snapshot: Mapping[str, Any],
    expected_case_sources: Sequence[tuple[str, str, bytes]],
    batch_path: Path,
    manifest_path: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    from emlis_nls_v3_rc0029_surface_repair_bounded_experiment import (
        _open_private_directory,
        _write_private_pair,
    )

    _assert_source_unchanged(
        source_snapshot,
        batch_path,
        manifest_path,
        code="CURRENT_RC_G8_SOURCE_CHANGED_BEFORE_WRITE",
    )
    private = _decode_canonical_payload(private_payload)
    body_free = _decode_canonical_payload(body_free_payload)
    _validate_pair(
        private,
        body_free,
        key=key,
        expected_source=source_snapshot,
        expected_case_sources=expected_case_sources,
    )
    directory_fd: int | None = None
    pair_written = False

    def discard_written_pair() -> None:
        if directory_fd is None or not pair_written:
            return
        for name in (_PRIVATE_FILENAME, _BODY_FREE_FILENAME):
            try:
                os.unlink(name, dir_fd=directory_fd)
            except FileNotFoundError:
                pass
            except OSError:
                pass
        try:
            os.fsync(directory_fd)
        except OSError:
            pass

    try:
        directory_fd = _open_private_directory(
            output_dir,
            output_names=(_PRIVATE_FILENAME, _BODY_FREE_FILENAME),
        )
        if os.listdir(directory_fd):
            raise CurrentRcG8RunError(
                "CURRENT_RC_G8_PRIVATE_DIRECTORY_NOT_FRESH"
            )
        _write_private_pair(
            directory_fd,
            private_payload,
            body_free_payload,
            private_name=_PRIVATE_FILENAME,
            body_free_name=_BODY_FREE_FILENAME,
        )
        pair_written = True
        reread: dict[str, bytes] = {}
        flags = os.O_RDONLY | os.O_NOFOLLOW
        if hasattr(os, "O_CLOEXEC"):
            flags |= os.O_CLOEXEC
        for name in (_PRIVATE_FILENAME, _BODY_FREE_FILENAME):
            descriptor: int | None = None
            try:
                descriptor = os.open(name, flags, dir_fd=directory_fd)
                status = os.fstat(descriptor)
                if (
                    not stat_module.S_ISREG(status.st_mode)
                    or stat_module.S_IMODE(status.st_mode) != 0o600
                    or status.st_uid != os.getuid()
                    or status.st_nlink != 1
                ):
                    raise CurrentRcG8RunError(
                        "CURRENT_RC_G8_PRIVATE_OUTPUT_POSTVERIFY_FAILED"
                    )
                chunks: list[bytes] = []
                while True:
                    chunk = os.read(descriptor, 1024 * 1024)
                    if not chunk:
                        break
                    chunks.append(chunk)
                reread[name] = b"".join(chunks)
            finally:
                if descriptor is not None:
                    os.close(descriptor)
        if (
            reread[_PRIVATE_FILENAME] != private_payload
            or reread[_BODY_FREE_FILENAME] != body_free_payload
        ):
            raise CurrentRcG8RunError(
                "CURRENT_RC_G8_PRIVATE_OUTPUT_POSTVERIFY_FAILED"
            )
        private = _decode_canonical_payload(reread[_PRIVATE_FILENAME])
        body_free = _decode_canonical_payload(reread[_BODY_FREE_FILENAME])
        _validate_pair(
            private,
            body_free,
            key=key,
            expected_source=source_snapshot,
            expected_case_sources=expected_case_sources,
        )
        _assert_source_unchanged(
            source_snapshot,
            batch_path,
            manifest_path,
            code="CURRENT_RC_G8_SOURCE_CHANGED_DURING_WRITE",
        )
        if set(os.listdir(directory_fd)) != {
            _PRIVATE_FILENAME,
            _BODY_FREE_FILENAME,
        }:
            raise CurrentRcG8RunError(
                "CURRENT_RC_G8_PRIVATE_DIRECTORY_POSTVERIFY_FAILED"
            )
        return private, body_free
    except CurrentRcG8RunError:
        discard_written_pair()
        raise
    except Exception as exc:
        discard_written_pair()
        raise CurrentRcG8RunError(
            "CURRENT_RC_G8_PRIVATE_OUTPUT_REJECTED"
        ) from exc
    finally:
        if directory_fd is not None:
            os.close(directory_fd)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Bypass G7, run each rc0027-selected case in the frozen exact-100 "
            "corpus through the current rc0031 builder, and save a private "
            "body-full/HMAC body-free pair."
        )
    )
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--commitment-key-file",
        required=True,
        type=Path,
        help="Existing outside-repo 0600 file containing exactly 32 key bytes.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Existing absolute outside-repo directory owned by the caller (0700).",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=min(8, max(1, os.cpu_count() or 1)),
        help="Parallel case workers (1-32; default: min(CPU count, 8)).",
    )
    parser.add_argument("--batch", type=Path, default=_BATCH_PATH)
    parser.add_argument("--manifest", type=Path, default=_MANIFEST_PATH)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if (
        type(args.run_id) is not str
        or _RUN_ID_RE.fullmatch(args.run_id) is None
        or type(args.workers) is not int
        or not 1 <= args.workers <= 32
    ):
        raise CurrentRcG8RunError("CURRENT_RC_G8_ARGUMENT_INVALID")
    batch_path = args.batch.resolve()
    manifest_path = args.manifest.resolve()
    (
        samples,
        _manifest,
        commitment_by_case,
        expected_case_sources,
        source_snapshot,
    ) = _bound_exact100_sources(batch_path, manifest_path)
    source_closure = source_snapshot["source_closure_sha256"]
    from emlis_nls_v3_batch_run import _read_key

    key = _read_key(args.commitment_key_file)
    rows = _run_cases(
        samples,
        commitment_by_case,
        source_closure,
        workers=args.workers,
    )
    _assert_source_unchanged(
        source_snapshot,
        batch_path,
        manifest_path,
        code="CURRENT_RC_G8_SOURCE_CHANGED_DURING_EXECUTION",
    )
    private_payload, body_free_payload, _summary = _result_payloads(
        rows,
        key=key,
        run_id=args.run_id,
        source_snapshot=source_snapshot,
        expected_case_sources=expected_case_sources,
    )
    _write_outputs(
        args.output_dir,
        private_payload,
        body_free_payload,
        key=key,
        source_snapshot=source_snapshot,
        expected_case_sources=expected_case_sources,
        batch_path=batch_path,
        manifest_path=manifest_path,
    )
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
    except CurrentRcG8RunError as exc:
        print(exc.code, file=sys.stderr)
        raise SystemExit(2) from None
    except Exception:
        print("CURRENT_RC_G8_RUN_FAILED", file=sys.stderr)
        raise SystemExit(2) from None
    print("CURRENT_RC_G8_RESULTS_SAVED")
    raise SystemExit(exit_code)
