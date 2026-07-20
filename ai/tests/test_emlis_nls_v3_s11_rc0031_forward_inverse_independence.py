# -*- coding: utf-8 -*-
from __future__ import annotations

"""P3 RED-first contract for verified base-reuse composition.

Production is intentionally unchanged in this phase.  The suite proves the
body-free denominator, keeps every public P2 reuse input closed, and reserves
one exact private validator slot for a separately approved implementation.
The test-local trusted orchestrator obtains a fresh base-body proof before
forward planning.  The projected fields are not an authenticity boundary.
"""

import ast
from collections import Counter
from dataclasses import replace
from functools import lru_cache
import hashlib
import importlib
import json
from pathlib import Path
from typing import Any

import pytest


_TEST_ROOT = Path(__file__).resolve().parent
_REPO_ROOT = _TEST_ROOT.parents[1]
_SERVICE_ROOT = _REPO_ROOT / "ai" / "services" / "ai_inference"
_CYCLE_ROOT = _TEST_ROOT / "fixtures" / "emlis_nls_v3" / "cycle_001"

_LEXICAL_PATH = _SERVICE_ROOT / "emlis_ai_step11_grounded_lexicalization_v3.py"
_SURFACE_PATH = _SERVICE_ROOT / "emlis_ai_step11_natural_surface_v3.py"
_MATCHER_PATH = _SERVICE_ROOT / "emlis_ai_step11_natural_surface_matcher_v3.py"
_GATE_PATH = _SERVICE_ROOT / "emlis_ai_step11_hard_gate_v3.py"
_CATALOG_PATH = (
    _SERVICE_ROOT / "emlis_ai_step11_rc0031_experiment_surface_catalog_v3.py"
)
_P1_FIXTURE = _CYCLE_ROOT / "rc0031_representative8_body_free.json"
_P1_TEST = _TEST_ROOT / "test_emlis_nls_v3_s11_rc0031_proposition_surface_red.py"
_P2_TEST = (
    _TEST_ROOT / "test_emlis_nls_v3_s11_rc0031_proposition_surface_mutation.py"
)

_P2_IMMUTABLE_FILES = {
    _LEXICAL_PATH: (
        129_615,
        "592f3ab7c90831c3191f51e9e7dd9a1f8c3fe4add1fd31bba9fdc65dccaecc28",
    ),
    _GATE_PATH: (
        208_041,
        "88514bb2a179e8d726f36e1666d2618330d95979107403ededc93aa35655943b",
    ),
    _CATALOG_PATH: (
        19_951,
        "a4e8bc9753a1398571d511d5d0c1219a886c498661b3a4f702d3b20b5672c6cc",
    ),
    _P1_FIXTURE: (
        19_889,
        "15e8047cd95b453fba4a7a677b428955ea2819e6738e4e1fc1488d24952b78a8",
    ),
    _P1_TEST: (
        24_327,
        "14e90025a18f1fcab8b2d4d8571e7d2be31b271ec2d4ca8e3a22fa56f14f193c",
    ),
    _P2_TEST: (
        94_573,
        "2d71f9241abb7f38ad9de41633c89b7c257b461df2b3e7df92e2d74df4b684a2",
    ),
}
_SURFACE_MUTABLE_START = (
    b"def _step11_rc0031_validate_verified_reuse_composition("
)
_SURFACE_MUTABLE_END = b"def _step11_rc0031_composition_units("
_SURFACE_PREFIX_BYTES = 404_481
_SURFACE_PREFIX_SHA256 = (
    "50cd281d79619f785d8065f411eaa020cb3ed8c335025983e5068ea29672e7ed"
)
_SURFACE_SUFFIX_BYTES = 75_831
_SURFACE_SUFFIX_SHA256 = (
    "f2f8e3f0201efddf6c197618a8a5f31e8dd823d352ca6241bd331a88e1962985"
)
_SURFACE_MUTABLE_SLOT_BYTE_MAX = 8_192
_SERVICE_PY_PATH_COUNT = 546
_SERVICE_PY_PATH_LIST_SHA256 = (
    "46db0d14852dde6ebb6012596234cbb935243b27ed227465d9e94876ce4f5d56"
)
_REPOSITORY_PY_FROZEN_FILE_COUNT = 1_533
_REPOSITORY_PY_FROZEN_MATERIAL_SHA256 = (
    "ff684888cb4ca3b92494ba5128fdd3ca16ea9bc08a9d263ee2ea0c9f35c47573"
)
_MATCHER_FROZEN_BYTES = 722_658
_MATCHER_FROZEN_SHA256 = (
    "648a3a6690f8df860053c811a5416fcfc9983524e5ff880a0e6921a122a52e30"
)
_EXPECTED_P3_ACTIVE = frozenset(
    {
        "ai/services/ai_inference/emlis_ai_step11_rc0031_experiment_surface_catalog_v3.py",
        "ai/tests/fixtures/emlis_nls_v3/cycle_001/rc0031_representative8_body_free.json",
        "ai/tests/test_emlis_nls_v3_s11_rc0031_proposition_surface_red.py",
        "ai/tests/test_emlis_nls_v3_s11_rc0031_proposition_surface_mutation.py",
        "ai/tests/test_emlis_nls_v3_s11_rc0031_forward_inverse_independence.py",
    }
)
_EXPECTED_FORWARD_RESOURCE_BOUNDS = {
    "owner_max": 24,
    "referent_scalar_max": 32,
    "construction_key_count": 13,
    "construction_layout_count": 13,
    "role_position_key_count": 9,
    "relation_type_direction_key_count": 28,
    "semantic_link_type_direction_key_count": 10,
    "unknown_dimension_key_count": 4,
    "owner_role_key_count": 8,
    "owner_kind_key_count": 12,
    "reception_act_key_count": 3,
    "visible_clauses_per_grammatical_sentence_max": 2,
    "grammatical_complexity_load_max": 4,
    "repeated_joiner_per_group_max": 2,
}
_EXPECTED_INVERSE_RESOURCE_BOUNDS = (
    1_000_000,
    38,
    76,
    2,
    2,
    24,
    576,
    3,
    2,
)
_REPRESENTATIVE_CASE_IDS = (
    "nls3s_b001_0001",
    "nls3s_b001_0002",
    "nls3s_b001_0009",
    "nls3s_b001_0019",
    "nls3s_b001_0035",
    "nls3s_b001_0043",
    "nls3s_b001_0063",
    "nls3s_b001_0100",
)
_EXPECTED_EMITTED_CANDIDATES = {
    "nls3s_b001_0001": 1,
    "nls3s_b001_0002": 1,
    "nls3s_b001_0009": 1,
    "nls3s_b001_0019": 2,
    "nls3s_b001_0035": 1,
    "nls3s_b001_0043": 2,
    "nls3s_b001_0063": 1,
    "nls3s_b001_0100": 1,
}
_EXPECTED_SEMANTIC_ATOMS = {
    "nls3s_b001_0001": (1,),
    "nls3s_b001_0002": (0,),
    "nls3s_b001_0009": (1,),
    "nls3s_b001_0019": (3, 3),
    "nls3s_b001_0035": (7,),
    "nls3s_b001_0043": (3, 3),
    "nls3s_b001_0063": (10,),
    "nls3s_b001_0100": (8,),
}
_EXPECTED_REUSE_SOURCE_ID = "semantic_unknown:u2fddc7083cf9a9f771ab8c08"
_EXPECTED_REUSE_SCHEMA = (
    "cocolon.emlis.nls_v3.step11.rc0030_verified_base_reuse.v1"
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
_PRIVATE_COMPOSITION_SEAMS = frozenset(
    {
        "_step11_rc0031_validate_verified_reuse_composition",
        "_step11_rc0031_build_plan_from_verified_reuse_composition",
        "_step11_rc0031_render_from_verified_reuse_composition",
        "_step11_rc0031_build_candidate_from_verified_reuse_composition",
        "_step11_rc0031_validate_candidate_from_verified_reuse_composition",
    }
)
_FORBIDDEN_RUNTIME_NAMES = frozenset(
    {"__builtins__", "logger", "logging", "os", "subprocess", "sys"}
)
_ALLOWED_PATCH_NAME_CALLS = frozenset(
    {
        "Step11NaturalSurfaceError",
        "all",
        "any",
        "artifact_sha256",
        "bool",
        "dict",
        "enumerate",
        "frozenset",
        "isinstance",
        "len",
        "list",
        "max",
        "min",
        "next",
        "range",
        "set",
        "sorted",
        "str",
        "sum",
        "tuple",
        "type",
        "zip",
    }
)
_ALLOWED_PATCH_ATTRIBUTE_CALLS = frozenset(
    {"fullmatch", "get", "hexdigest", "items", "keys", "sha256", "values"}
)
_FORBIDDEN_BODY_KEYS = frozenset(
    {
        "action_text",
        "base_body",
        "body",
        "candidate_text",
        "comment_text",
        "current_input",
        "final_utf8_bytes",
        "input",
        "input_text",
        "memo",
        "memo_action",
        "normalized_input",
        "output",
        "output_text",
        "owner_expressions",
        "parsed_span",
        "parsed_witness",
        "raw_text",
        "rendered_surface",
        "source_fragment",
        "supporting_expression",
        "surface_text",
        "target_expression",
        "thought_text",
        "unsalted_body_digest",
        "utf8_bytes",
    }
)


def _closed_assert(condition: bool, code: str) -> None:
    if not condition:
        pytest.fail(code, pytrace=False)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _all_mapping_keys(value: Any) -> frozenset[str]:
    if type(value) is dict:
        return frozenset(value) | frozenset(
            key for child in value.values() for key in _all_mapping_keys(child)
        )
    if type(value) in {list, tuple}:
        return frozenset(
            key for child in value for key in _all_mapping_keys(child)
        )
    return frozenset()


@lru_cache(maxsize=1)
def _p2_test_module() -> Any:
    return importlib.import_module(
        "test_emlis_nls_v3_s11_rc0031_proposition_surface_mutation"
    )


@lru_cache(maxsize=1)
def _surface_module() -> Any:
    return importlib.import_module("emlis_ai_step11_natural_surface_v3")


@lru_cache(maxsize=1)
def _inverse_module() -> Any:
    return importlib.import_module("emlis_ai_step11_natural_surface_matcher_v3")


@lru_cache(maxsize=1)
def _0001_authority() -> tuple[Any, Any, Any, Any]:
    baseline, successor, lexical_specs = _p2_test_module()._forward_authority(
        "nls3s_b001_0001"
    )
    _closed_assert(
        len(baseline.natural_candidates) == 1,
        "STEP11_RC0031_P3_0001_BASE_DENOMINATOR_INVALID",
    )
    return baseline, successor, lexical_specs, baseline.natural_candidates[0]


def _fresh_0001_proof() -> tuple[Any, tuple[Any, ...]]:
    baseline, successor, _lexical_specs, base = _0001_authority()
    inverse = _inverse_module()
    witness = inverse.parse_step11_rc0030_base_body_exact_reuse(
        base.final_utf8_bytes
    )
    proof = inverse.match_step11_rc0030_base_body_exact_reuse(
        witness,
        successor_snapshot=successor,
        inventory_result=baseline.inventory_result,
        content_plan=baseline.content_plan,
        discourse_plan=base.discourse_plan,
        current_input=baseline.projected_current_input,
    )
    return witness, proof


def _project_verified_proof(proof: Any) -> Any:
    surface = _surface_module()
    return surface.Step11Rc0031BaseBodyExactReuseBinding(
        **{field: getattr(proof, field) for field in _TRUST_PROJECTION_FIELDS}
    )


def _rehash_projected_binding(binding: Any) -> Any:
    inverse = _inverse_module()
    material = {
        "schema_version": _EXPECTED_REUSE_SCHEMA,
        **{
            field: getattr(binding, field)
            for field in _TRUST_PROJECTION_FIELDS
            if field != "independent_binding_sha256"
        },
        "body_free": True,
    }
    return replace(
        binding,
        independent_binding_sha256=inverse.artifact_sha256(material),
    )


def _assert_no_captured_output(capsys: Any, code: str) -> None:
    captured = capsys.readouterr()
    _closed_assert(captured.out == "" and captured.err == "", code)


def _private_candidate_or_red(
    code: str,
    *,
    capsys: Any,
    binding: Any | None = None,
) -> Any:
    _witness, proof = _fresh_0001_proof()
    _closed_assert(
        len(proof) == 1,
        "STEP11_RC0031_P3_0001_REUSE_DENOMINATOR_INVALID",
    )
    projected = _project_verified_proof(proof[0]) if binding is None else binding
    _baseline, successor, lexical_specs, base = _0001_authority()
    surface = _surface_module()
    try:
        result = surface._step11_rc0031_build_candidate_from_verified_reuse_composition(
            base,
            successor_snapshot=successor,
            lexical_atom_specs=lexical_specs,
            verified_base_body_exact_reuse_bindings=(projected,),
            validate_output=True,
        )
    except surface.Step11NaturalSurfaceError as exc:
        _assert_no_captured_output(
            capsys, "STEP11_RC0031_P3_COMPOSITION_BODY_OUTPUT_LEAK"
        )
        _closed_assert(
            exc.code == "STEP11_RC0031_P3_EXACT_REUSE_NOT_AVAILABLE",
            "STEP11_RC0031_P3_VERIFIED_REUSE_RED_CAUSE_INVALID",
        )
        pytest.fail(code, pytrace=False)
    except Exception:
        _assert_no_captured_output(
            capsys, "STEP11_RC0031_P3_COMPOSITION_BODY_OUTPUT_LEAK"
        )
        pytest.fail(
            "STEP11_RC0031_P3_VERIFIED_REUSE_RED_CAUSE_INVALID",
            pytrace=False,
        )
    _assert_no_captured_output(
        capsys, "STEP11_RC0031_P3_COMPOSITION_BODY_OUTPUT_LEAK"
    )
    return result


def _expect_surface_error(
    call: Any,
    expected_code: str,
    failure_code: str,
    *,
    capsys: Any | None = None,
) -> None:
    surface = _surface_module()
    try:
        call()
    except surface.Step11NaturalSurfaceError as exc:
        if capsys is not None:
            _assert_no_captured_output(
                capsys, "STEP11_RC0031_P3_COMPOSITION_BODY_OUTPUT_LEAK"
            )
        _closed_assert(exc.code == expected_code, failure_code)
    except Exception:
        if capsys is not None:
            _assert_no_captured_output(
                capsys, "STEP11_RC0031_P3_COMPOSITION_BODY_OUTPUT_LEAK"
            )
        pytest.fail(failure_code, pytrace=False)
    else:
        if capsys is not None:
            _assert_no_captured_output(
                capsys, "STEP11_RC0031_P3_COMPOSITION_BODY_OUTPUT_LEAK"
            )
        pytest.fail(failure_code, pytrace=False)


def test_rc0031_p3_freeze_scope_and_single_private_patch_hole_are_exact() -> None:
    for path, (byte_count, expected_sha256) in _P2_IMMUTABLE_FILES.items():
        _closed_assert(
            path.stat().st_size == byte_count
            and _sha256(path) == expected_sha256,
            "STEP11_RC0031_P3_P2_IMMUTABLE_FILE_DRIFT",
        )

    surface_bytes = _SURFACE_PATH.read_bytes()
    _closed_assert(
        surface_bytes.count(_SURFACE_MUTABLE_START) == 1
        and surface_bytes.count(_SURFACE_MUTABLE_END) == 1,
        "STEP11_RC0031_P3_SURFACE_PATCH_HOLE_INVALID",
    )
    mutable_start = surface_bytes.index(_SURFACE_MUTABLE_START)
    mutable_end = surface_bytes.index(_SURFACE_MUTABLE_END, mutable_start)
    prefix = surface_bytes[:mutable_start]
    mutable_slot = surface_bytes[mutable_start:mutable_end]
    suffix = surface_bytes[mutable_end:]
    service_py_paths = tuple(
        sorted(
            path.relative_to(_REPO_ROOT).as_posix()
            for path in _SERVICE_ROOT.rglob("*.py")
            if "__pycache__" not in path.parts
        )
    )
    service_py_path_material = (
        "\n".join(service_py_paths) + "\n"
    ).encode("utf-8")
    repository_py_paths = tuple(
        sorted(
            path
            for path in _REPO_ROOT.rglob("*.py")
            if path not in {_SURFACE_PATH, Path(__file__).resolve()}
            and "__pycache__" not in path.parts
            and ".git" not in path.parts
        )
    )
    repository_py_material = b"".join(
        (
            path.relative_to(_REPO_ROOT).as_posix()
            + "\0"
            + str(path.stat().st_size)
            + "\0"
            + _sha256(path)
            + "\n"
        ).encode("utf-8")
        for path in repository_py_paths
    )
    try:
        mutable_tree = ast.parse(mutable_slot.decode("utf-8"))
    except (UnicodeError, SyntaxError):
        pytest.fail(
            "STEP11_RC0031_P3_SURFACE_PATCH_HOLE_INVALID", pytrace=False
        )
    mutable_function = (
        mutable_tree.body[0] if len(mutable_tree.body) == 1 else None
    )
    _closed_assert(
        len(prefix) == _SURFACE_PREFIX_BYTES
        and hashlib.sha256(prefix).hexdigest() == _SURFACE_PREFIX_SHA256
        and 0 < len(mutable_slot) <= _SURFACE_MUTABLE_SLOT_BYTE_MAX
        and len(suffix) == _SURFACE_SUFFIX_BYTES
        and hashlib.sha256(suffix).hexdigest() == _SURFACE_SUFFIX_SHA256
        and type(mutable_function) is ast.FunctionDef
        and mutable_function.name
        == "_step11_rc0031_validate_verified_reuse_composition"
        and tuple(row.arg for row in mutable_function.args.args) == ("rows",)
        and tuple(row.arg for row in mutable_function.args.kwonlyargs)
        == ("records", "base_candidate", "successor_snapshot")
        and mutable_function.args.vararg is None
        and mutable_function.args.kwarg is None
        and not mutable_function.decorator_list
        and sum(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            for node in ast.walk(mutable_tree)
        )
        == 1
        and not any(
            isinstance(
                node,
                (
                    ast.AsyncFunctionDef,
                    ast.ClassDef,
                    ast.Global,
                    ast.Import,
                    ast.ImportFrom,
                    ast.Lambda,
                    ast.Nonlocal,
                ),
            )
            for node in ast.walk(mutable_tree)
        )
        and not any(
            isinstance(node, (ast.Await, ast.Yield, ast.YieldFrom))
            for node in ast.walk(mutable_tree)
        )
        and not any(
            isinstance(node, ast.Name)
            and (
                node.id in _FORBIDDEN_RUNTIME_NAMES
                or node.id.startswith("__")
            )
            for node in ast.walk(mutable_tree)
        )
        and not any(
            isinstance(node, ast.Attribute) and node.attr.startswith("__")
            for node in ast.walk(mutable_tree)
        )
        and all(
            (
                (
                    isinstance(node.func, ast.Name)
                    and node.func.id in _ALLOWED_PATCH_NAME_CALLS
                )
                or (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr in _ALLOWED_PATCH_ATTRIBUTE_CALLS
                )
            )
            for node in ast.walk(mutable_tree)
            if isinstance(node, ast.Call)
        )
        and len(service_py_paths) == _SERVICE_PY_PATH_COUNT
        and hashlib.sha256(service_py_path_material).hexdigest()
        == _SERVICE_PY_PATH_LIST_SHA256
        and len(repository_py_paths) == _REPOSITORY_PY_FROZEN_FILE_COUNT
        and hashlib.sha256(repository_py_material).hexdigest()
        == _REPOSITORY_PY_FROZEN_MATERIAL_SHA256,
        "STEP11_RC0031_P3_SURFACE_OUTSIDE_PATCH_HOLE_DRIFT",
    )

    _closed_assert(
        _MATCHER_PATH.stat().st_size == _MATCHER_FROZEN_BYTES
        and _sha256(_MATCHER_PATH) == _MATCHER_FROZEN_SHA256,
        "STEP11_RC0031_P3_MATCHER_DRIFT",
    )
    active = frozenset(
        path.relative_to(_REPO_ROOT).as_posix()
        for path in (_REPO_ROOT / "ai").rglob("*rc0031*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix != ".pyc"
    )
    _closed_assert(
        active == _EXPECTED_P3_ACTIVE,
        "STEP11_RC0031_P3_PATH_SCOPE_INVALID",
    )

    fixture = json.loads(_P1_FIXTURE.read_text(encoding="utf-8"))
    catalog_owner = importlib.import_module(
        "emlis_ai_step11_rc0031_experiment_surface_catalog_v3"
    )
    catalog = catalog_owner.STEP11_RC0031_EXPERIMENT_SURFACE_CATALOG
    surface = _surface_module()
    inverse = _inverse_module()
    _closed_assert(
        type(fixture) is dict
        and fixture.get("body_free") is True
        and not (_all_mapping_keys(fixture) & _FORBIDDEN_BODY_KEYS)
        and catalog_owner.validate_step11_rc0031_experiment_surface_catalog(
            catalog
        )
        == ()
        and catalog["resource_bounds"] == _EXPECTED_FORWARD_RESOURCE_BOUNDS
        and surface._STEP11_RC0031_CANDIDATE_MAX == 12
        and surface._STEP11_RC0031_REPLAN_MAX == 1
        and surface._STEP11_RC0031_OWNER_MAX == 24
        and (
            inverse._STEP11_RC0030_BODY_BYTE_MAX,
            inverse._STEP11_RC0030_DECOMPOSITION_LOCUS_MAX,
            inverse._STEP11_RC0030_EVALUATED_DECOMPOSITION_MAX,
            inverse._STEP11_RC0030_STORED_DECOMPOSITION_MAX,
            inverse._STEP11_RC0030_BODY_SCAN_PASS_MAX,
            inverse._STEP11_RC0030_OWNER_MAX,
            inverse._STEP11_RC0030_OWNER_COMPARISON_MAX,
            inverse._STEP11_RC0030_RECEPTION_MOVE_MAX,
            inverse._STEP11_RC0030_RECEPTION_MOVES_PER_SENTENCE_MAX,
        )
        == _EXPECTED_INVERSE_RESOURCE_BOUNDS,
        "STEP11_RC0031_P3_RESOURCE_OR_BODY_FREE_CONTRACT_DRIFT",
    )


def test_rc0031_p3_representative8_base_reuse_denominator_is_exact() -> None:
    p2 = _p2_test_module()
    surface = _surface_module()
    inverse = _inverse_module()
    emitted_count: dict[str, int] = {}
    semantic_counts: dict[str, tuple[int, ...]] = {}
    base_candidate_total = 0
    semantic_family_counts = {
        "construction": 0,
        "relation": 0,
        "semantic_link": 0,
        "explicit_unknown": 0,
    }
    reuse_rows: list[Any] = []
    duplicate_count = 0
    body_byte_count = 0
    body_scan_count = 0
    case_0063 = None

    for case_id in _REPRESENTATIVE_CASE_IDS:
        baseline, successor, lexical_specs = p2._forward_authority(case_id)
        base_candidate_total += len(baseline.natural_candidates)
        verified_by_base_id: dict[str, tuple[Any, ...]] = {}
        for base in baseline.natural_candidates:
            witness = inverse.parse_step11_rc0030_base_body_exact_reuse(
                base.final_utf8_bytes
            )
            verified = inverse.match_step11_rc0030_base_body_exact_reuse(
                witness,
                successor_snapshot=successor,
                inventory_result=baseline.inventory_result,
                content_plan=baseline.content_plan,
                discourse_plan=base.discourse_plan,
                current_input=baseline.projected_current_input,
            )
            verified_by_base_id[base.candidate_id] = verified
            reuse_rows.extend(verified)
            body_byte_count += len(base.final_utf8_bytes)
            body_scan_count += witness.body_scan_pass_count

        candidates = surface.build_step11_rc0031_experiment_surface_candidates(
            tuple(baseline.natural_candidates),
            successor_snapshot=successor,
            lexical_atom_specs=lexical_specs,
        )
        emitted_count[case_id] = len(candidates)
        semantic_counts[case_id] = tuple(
            candidate.rendered_surface.semantic_atom_count
            for candidate in candidates
        )
        if case_id == "nls3s_b001_0063":
            case_0063 = candidates[0]
        for candidate in candidates:
            records = p2._atom_records(candidate)
            for family, _ordinals, _direction, _key in records.values():
                semantic_family_counts[family] += 1
            verified = verified_by_base_id[candidate.base_candidate.candidate_id]
            duplicate_count += len(
                set(records) & {row.source_atom_id for row in verified}
            )

    _closed_assert(
        emitted_count == _EXPECTED_EMITTED_CANDIDATES
        and semantic_counts == _EXPECTED_SEMANTIC_ATOMS
        and base_candidate_total == 13
        and sum(emitted_count.values()) == 10
        and sum(sum(rows) for rows in semantic_counts.values()) == 39
        and semantic_family_counts
        == {
            "construction": 22,
            "relation": 13,
            "semantic_link": 1,
            "explicit_unknown": 3,
        }
        and len(reuse_rows) == 1
        and reuse_rows[0].source_atom_id == _EXPECTED_REUSE_SOURCE_ID
        and reuse_rows[0].semantic_family == "explicit_unknown"
        and reuse_rows[0].match_basis == "unknown_id_dimension_exact_target"
        and duplicate_count == 1
        and body_byte_count == 6_249
        and body_scan_count == 26,
        "STEP11_RC0031_P3_REPRESENTATIVE_REUSE_DENOMINATOR_INVALID",
    )
    _closed_assert(
        case_0063 is not None
        and case_0063.rendered_surface.semantic_atom_count == 10
        and case_0063.rendered_surface.exact_reuse_count == 0
        and len(case_0063.reception_bindings) == 1
        and (
            case_0063.surface_realization_plan.peak_observation_clause_count,
            case_0063.surface_realization_plan.peak_grammatical_clause_count,
            case_0063.surface_realization_plan.peak_grammatical_complexity_load,
            case_0063.surface_realization_plan.peak_group_repeated_joiner_count,
        )
        == (4, 2, 4, 1),
        "STEP11_RC0031_P3_0063_DENOMINATOR_DRIFT",
    )


def test_rc0031_p3_public_reuse_claim_stays_closed_and_private_seam_unexported() -> None:
    _witness, proof = _fresh_0001_proof()
    binding = _project_verified_proof(proof[0])
    baseline, successor, lexical_specs, base = _0001_authority()
    surface = _surface_module()
    _expect_surface_error(
        lambda: surface.build_step11_rc0031_experiment_surface_candidate(
            base,
            successor_snapshot=successor,
            lexical_atom_specs=lexical_specs,
            base_body_exact_reuse_bindings=(binding,),
        ),
        "STEP11_RC0031_P3_EXACT_REUSE_NOT_AVAILABLE",
        "STEP11_RC0031_P3_PUBLIC_REUSE_BOUNDARY_OPENED",
    )
    _expect_surface_error(
        lambda: surface.build_step11_rc0031_experiment_surface_candidates(
            tuple(baseline.natural_candidates),
            successor_snapshot=successor,
            lexical_atom_specs=lexical_specs,
            base_body_exact_reuse_bindings=(binding,),
        ),
        "STEP11_RC0031_P3_EXACT_REUSE_NOT_AVAILABLE",
        "STEP11_RC0031_P3_PUBLIC_REUSE_BOUNDARY_OPENED",
    )
    _closed_assert(
        _PRIVATE_COMPOSITION_SEAMS.isdisjoint(surface.__all__),
        "STEP11_RC0031_P3_PRIVATE_COMPOSITION_EXPORTED",
    )


def test_rc0031_p3_reuse_envelope_and_bound_fail_closed() -> None:
    _witness, proof = _fresh_0001_proof()
    binding = _project_verified_proof(proof[0])
    _baseline, successor, lexical_specs, base = _0001_authority()
    surface = _surface_module()
    validator = surface._step11_rc0031_validate_verified_reuse_composition
    for malformed in ([binding], (object(),), (binding,) * 65):
        _expect_surface_error(
            lambda value=malformed: validator(
                value,
                records=(),
                base_candidate=base,
                successor_snapshot=successor,
            ),
            "STEP11_RC0031_VERIFIED_REUSE_COMPOSITION_INVALID",
            "STEP11_RC0031_P3_REUSE_ENVELOPE_NOT_CLOSED",
        )
    public_candidate = surface.build_step11_rc0031_experiment_surface_candidate(
        base,
        successor_snapshot=successor,
        lexical_atom_specs=lexical_specs,
    )
    _closed_assert(
        public_candidate.replan_count == 0
        and public_candidate.rendered_surface.semantic_atom_count == 1
        and public_candidate.rendered_surface.exact_reuse_count == 0
        and (
            public_candidate.surface_realization_plan.peak_observation_clause_count,
            public_candidate.surface_realization_plan.peak_grammatical_clause_count,
            public_candidate.surface_realization_plan.peak_grammatical_complexity_load,
            public_candidate.surface_realization_plan.peak_group_repeated_joiner_count,
        )
        == (2, 1, 1, 0),
        "STEP11_RC0031_P3_0001_CURRENT_FORWARD_DENOMINATOR_DRIFT",
    )


def test_rc0031_p3_fresh_proof_material_is_body_free_and_bounded(capsys: Any) -> None:
    witness, proof = _fresh_0001_proof()
    inverse = _inverse_module()
    _closed_assert(
        len(proof) == 1,
        "STEP11_RC0031_P3_0001_REUSE_DENOMINATOR_INVALID",
    )
    material = inverse.step11_rc0030_verified_base_body_reuse_material(proof[0])
    projected = _project_verified_proof(proof[0])
    captured = capsys.readouterr()
    _closed_assert(
        proof[0].schema_version == _EXPECTED_REUSE_SCHEMA
        and proof[0].body_free is True
        and witness.body_free_export_allowed is False
        and witness.body_scan_pass_count == 2
        and set(material)
        == {
            "schema_version",
            *_TRUST_PROJECTION_FIELDS,
            "body_free",
        }
        and not (_all_mapping_keys(material) & _FORBIDDEN_BODY_KEYS)
        and all(
            getattr(projected, field) == getattr(proof[0], field)
            for field in _TRUST_PROJECTION_FIELDS
        )
        and captured.out == ""
        and captured.err == "",
        "STEP11_RC0031_P3_PROOF_PRIVACY_OR_RESOURCE_INVALID",
    )


def test_rc0031_p3_trusted_reuse_is_consumed_before_forward_planning(
    capsys: Any,
) -> None:
    candidate = _private_candidate_or_red(
        "STEP11_RC0031_P3_VERIFIED_REUSE_PREPLAN_CONSUMPTION_MISSING",
        capsys=capsys,
    )
    _closed_assert(
        candidate.rendered_surface.exact_reuse_count == 1,
        "STEP11_RC0031_P3_VERIFIED_REUSE_PREPLAN_CONSUMPTION_MISSING",
    )


def test_rc0031_p3_reuse_and_rendered_atoms_form_exact_xor(capsys: Any) -> None:
    candidate = _private_candidate_or_red(
        "STEP11_RC0031_P3_VERIFIED_REUSE_XOR_INVALID", capsys=capsys
    )
    all_ids = tuple(_p2_test_module()._atom_records(candidate))
    reused_ids = tuple(
        row.source_atom_id
        for row in candidate.surface_realization_plan.base_body_exact_reuse_bindings
    )
    rendered_ids = tuple(
        source_id
        for row in candidate.surface_realization_plan.proposition_clause_bindings
        for source_id in row.source_atom_ids
    )
    _closed_assert(
        not (set(reused_ids) & set(rendered_ids))
        and Counter((*reused_ids, *rendered_ids)) == Counter(all_ids)
        and all(count == 1 for count in Counter(reused_ids).values())
        and all(count == 1 for count in Counter(rendered_ids).values()),
        "STEP11_RC0031_P3_VERIFIED_REUSE_XOR_INVALID",
    )


def test_rc0031_p3_0001_duplicate_reexposition_is_absent(capsys: Any) -> None:
    candidate = _private_candidate_or_red(
        "STEP11_RC0031_P3_DUPLICATE_BASE_REEXPOSITION_NOT_RESOLVED",
        capsys=capsys,
    )
    plan = candidate.surface_realization_plan
    _closed_assert(
        tuple(
            row.source_atom_id for row in plan.base_body_exact_reuse_bindings
        )
        == (_EXPECTED_REUSE_SOURCE_ID,)
        and not plan.proposition_clause_bindings
        and candidate.rendered_surface.semantic_atom_count == 0
        and candidate.rendered_surface.proposition_clause_count == 0
        and candidate.rendered_surface.exact_reuse_count == 1
        and len(candidate.reception_bindings) == 1,
        "STEP11_RC0031_P3_DUPLICATE_BASE_REEXPOSITION_NOT_RESOLVED",
    )


def test_rc0031_p3_verified_composition_is_canonical_and_deterministic(
    capsys: Any,
) -> None:
    first = _private_candidate_or_red(
        "STEP11_RC0031_P3_VERIFIED_REUSE_CANONICAL_MISMATCH", capsys=capsys
    )
    second = _private_candidate_or_red(
        "STEP11_RC0031_P3_VERIFIED_REUSE_CANONICAL_MISMATCH", capsys=capsys
    )
    _baseline, successor, lexical_specs, _base = _0001_authority()
    surface = _surface_module()
    issues = surface._step11_rc0031_validate_candidate_from_verified_reuse_composition(
        first,
        successor_snapshot=successor,
        lexical_atom_specs=lexical_specs,
        verified_base_body_exact_reuse_bindings=(
            first.surface_realization_plan.base_body_exact_reuse_bindings
        ),
    )
    plan = first.surface_realization_plan
    _closed_assert(
        first == second
        and issues == ()
        and first.replan_count == 0
        and first.semantic_coverage_authorized is False
        and first.runtime_connected is False
        and (
            plan.peak_observation_clause_count,
            plan.peak_grammatical_clause_count,
            plan.peak_grammatical_complexity_load,
            plan.peak_group_repeated_joiner_count,
        )
        == (1, 1, 1, 0)
        and plan.maximum_observation_clauses_per_sentence == 4
        and plan.maximum_visible_clauses_per_grammatical_sentence == 2
        and plan.maximum_grammatical_complexity_load == 4
        and plan.maximum_repeated_joiner_per_group == 2,
        "STEP11_RC0031_P3_VERIFIED_REUSE_CANONICAL_MISMATCH",
    )


def test_rc0031_p3_shape_valid_wrong_authority_attacks_are_distinguished(
    capsys: Any,
) -> None:
    _witness, proof = _fresh_0001_proof()
    binding = _project_verified_proof(proof[0])
    attacks = (
        _rehash_projected_binding(
            replace(binding, base_surface_sha256="f" * 64)
        ),
        _rehash_projected_binding(
            replace(binding, source_authority_sha256="e" * 64)
        ),
        _rehash_projected_binding(
            replace(binding, source_atom_id="semantic_unknown:source_swap")
        ),
        _rehash_projected_binding(
            replace(
                binding,
                semantic_family="relation",
                match_basis="relation_id_endpoint_direction_type_exact",
            )
        ),
        _rehash_projected_binding(
            replace(
                binding,
                match_basis="relation_id_endpoint_direction_type_exact",
            )
        ),
        replace(binding, independent_binding_sha256="d" * 64),
        (binding, binding),
    )
    _baseline, successor, lexical_specs, base = _0001_authority()
    surface = _surface_module()
    for attack in attacks:
        rows = attack if type(attack) is tuple else (attack,)
        _expect_surface_error(
            lambda value=rows: (
                surface._step11_rc0031_build_candidate_from_verified_reuse_composition(
                    base,
                    successor_snapshot=successor,
                    lexical_atom_specs=lexical_specs,
                    verified_base_body_exact_reuse_bindings=value,
                    validate_output=True,
                )
            ),
            "STEP11_RC0031_VERIFIED_REUSE_COMPOSITION_INVALID",
            "STEP11_RC0031_P3_VERIFIED_REUSE_ATTACK_NOT_CLOSED",
            capsys=capsys,
        )

    foreign_baseline, foreign_successor, foreign_lexical_specs = (
        _p2_test_module()._forward_authority("nls3s_b001_0002")
    )
    for foreign_base in foreign_baseline.natural_candidates:
        _expect_surface_error(
            lambda value=foreign_base: (
                surface._step11_rc0031_build_candidate_from_verified_reuse_composition(
                    value,
                    successor_snapshot=foreign_successor,
                    lexical_atom_specs=foreign_lexical_specs,
                    verified_base_body_exact_reuse_bindings=(binding,),
                    validate_output=True,
                )
            ),
            "STEP11_RC0031_VERIFIED_REUSE_COMPOSITION_INVALID",
            "STEP11_RC0031_P3_VERIFIED_REUSE_ATTACK_NOT_CLOSED",
            capsys=capsys,
        )
