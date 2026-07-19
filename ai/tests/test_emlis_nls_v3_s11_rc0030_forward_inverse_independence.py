# -*- coding: utf-8 -*-
from __future__ import annotations

"""P3 body-only Parser / Independent Matcher boundary for rc0030.

The helper may create private candidates inside the test process, but the
inverse APIs receive only final bytes, an inverse-owned base-body witness, and
validated source authority.  No body is embedded in a parameter id or failure.
"""

import ast
from dataclasses import replace
from functools import lru_cache
import hashlib
import importlib
import inspect
from pathlib import Path
from typing import Any, Callable

import pytest


_TEST_ROOT = Path(__file__).resolve().parent
_REPO_ROOT = _TEST_ROOT.parents[1]
_SERVICE_ROOT = _REPO_ROOT / "ai" / "services" / "ai_inference"
_MATCHER_PATH = _SERVICE_ROOT / "emlis_ai_step11_natural_surface_matcher_v3.py"
_GATE_PATH = _SERVICE_ROOT / "emlis_ai_step11_hard_gate_v3.py"
_P1_FIXTURE = (
    _TEST_ROOT
    / "fixtures"
    / "emlis_nls_v3"
    / "cycle_001"
    / "rc0030_representative8_body_free.json"
)
_P1_TEST = _TEST_ROOT / "test_emlis_nls_v3_s11_rc0030_surface_planning_red.py"
_P2_FILES = {
    _SERVICE_ROOT / "emlis_ai_step11_grounded_lexicalization_v3.py": (
        129_615,
        "592f3ab7c90831c3191f51e9e7dd9a1f8c3fe4add1fd31bba9fdc65dccaecc28",
    ),
    _SERVICE_ROOT / "emlis_ai_step11_natural_surface_v3.py": (
        357_476,
        "8f8ea6f197bac02edc8ee3594165625e1e8f06e5a6a7bb44e41445d880ae9c37",
    ),
    _SERVICE_ROOT / "emlis_ai_step11_rc0030_experiment_surface_catalog_v3.py": (
        15_593,
        "d51b8df3a7914aaa095a8b5249dd799f3dab2d8c706b07cea93e71a5b01ceb86",
    ),
    _TEST_ROOT / "test_emlis_nls_v3_s11_rc0030_surface_planning_mutation.py": (
        39_563,
        "b04e8a6c6038ebc0dfde8b15d520ec9454f290977f611b295c7765299035925e",
    ),
}
_MATCHER_P2_PREFIX_BYTES = 589_793
_MATCHER_P2_PREFIX_SHA256 = (
    "9bdae4b5c3d99e99dd01b622b9b191afbfa0e601789fba082a03c069b70028b5"
)
_MATCHER_P3_FULL_BYTES = 696_912
_MATCHER_P3_FULL_SHA256 = (
    "629305364ac50530265d7d87a6ca28678eb3e1be6ac7289ae770b3b5f871d8c9"
)
_MATCHER_P3_SUFFIX_BYTES = 107_119
_MATCHER_P3_SUFFIX_SHA256 = (
    "16da3059e90655b4048e7ff300aa68fa06bc9fe51397a963824c435daef07e34"
)
_GATE_SHA256 = "6911291682508bcd6df66d39acb7a6b29b1cfc411434d1ff13160125c9af6c9a"
_P1_FIXTURE_SHA256 = (
    "9cfbdafaf43a3caed8b5dc00e68b56cd2b24003a002f0a7cbd1c3ec06d598fa5"
)
_P1_TEST_SHA256 = (
    "56bc3603392df982ae748c9c4ae635fc7eca7867213f77bab1de051f35f38191"
)
_DIRECT_CASE_IDS = (
    "nls3s_b001_0001",
    "nls3s_b001_0009",
    "nls3s_b001_0035",
    "nls3s_b001_0100",
)
_FORBIDDEN_INVERSE_IMPORTS = frozenset(
    {
        "emlis_ai_step11_grounded_lexicalization_v3",
        "emlis_ai_step11_natural_surface_v3",
        "emlis_ai_step11_hard_gate_v3",
        "emlis_ai_step11_runtime_adapter_v3",
        "emlis_ai_step11_rc0030_experiment_runtime_adapter_v3",
    }
)
_FORBIDDEN_INVERSE_PARAMETERS = frozenset(
    {
        "candidate",
        "forward_plan",
        "surface_realization_plan",
        "candidate_ast",
        "surface_ast",
        "span_map",
        "candidate_owner_ids",
        "covered_ids",
        "selected",
        "lexical_atom_specs",
    }
)
_EXPECTED_PUBLIC_SYMBOLS = frozenset(
    {
        "Step11Rc0030BaseBodyParsedWitness",
        "Step11Rc0030ExperimentParsedSurfaceWitness",
        "Step11Rc0030ExperimentVerifiedSurfaceBinding",
        "Step11Rc0030VerifiedBaseBodyReuse",
        "Step11Rc0030VerifiedReceptionBinding",
        "match_step11_rc0030_base_body_exact_reuse",
        "match_step11_rc0030_experiment_surface",
        "parse_step11_rc0030_base_body_exact_reuse",
        "parse_step11_rc0030_experiment_surface",
        "step11_rc0030_base_body_parsed_witness_material",
        "step11_rc0030_experiment_parsed_witness_material",
        "step11_rc0030_experiment_verified_binding_material",
        "step11_rc0030_verified_base_body_reuse_material",
    }
)
_FORBIDDEN_EXPORT_KEYS = frozenset(
    {
        "body",
        "base_body",
        "final_utf8_bytes",
        "raw_text",
        "surface_text",
        "owner_expressions",
        "target_expression",
        "supporting_expression",
        "current_input",
        "unsalted_body_digest",
    }
)


def _closed_assert(condition: bool, code: str) -> None:
    if not condition:
        pytest.fail(code, pytrace=False)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _definition_counts(tree: ast.Module) -> dict[str, int]:
    result: dict[str, int] = {}
    for node in tree.body:
        names: tuple[str, ...] = ()
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            names = (node.name,)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else (node.target,)
            names = tuple(row.id for row in targets if isinstance(row, ast.Name))
        for name in names:
            result[name] = result.get(name, 0) + 1
    return result


def _imported_modules(tree: ast.AST) -> frozenset[str]:
    result: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            result.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            result.add(node.module)
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "__import__"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and type(node.args[0].value) is str
        ):
            result.add(node.args[0].value)
    return frozenset(result)


def _all_keys(value: Any) -> frozenset[str]:
    if type(value) is dict:
        return frozenset(value) | frozenset(
            key for child in value.values() for key in _all_keys(child)
        )
    if type(value) in {tuple, list}:
        return frozenset(key for child in value for key in _all_keys(child))
    return frozenset()


@lru_cache(maxsize=1)
def _p2_test_module() -> Any:
    return importlib.import_module(
        "test_emlis_nls_v3_s11_rc0030_surface_planning_mutation"
    )


@lru_cache(maxsize=None)
def _authority(case_id: str) -> tuple[Any, Any, Any]:
    return _p2_test_module()._forward_authority(case_id)


def _source_kwargs(baseline: Any, successor: Any, base: Any) -> dict[str, Any]:
    return {
        "successor_snapshot": successor,
        "inventory_result": baseline.inventory_result,
        "content_plan": baseline.content_plan,
        "discourse_plan": base.discourse_plan,
        "current_input": baseline.projected_current_input,
    }


@lru_cache(maxsize=None)
def _direct(case_id: str) -> tuple[Any, Any, Any, Any, Any, Any]:
    surface = importlib.import_module("emlis_ai_step11_natural_surface_v3")
    inverse = importlib.import_module(
        "emlis_ai_step11_natural_surface_matcher_v3"
    )
    baseline, successor, lexical_specs = _authority(case_id)
    candidate = surface.build_step11_rc0030_experiment_surface_candidates(
        tuple(baseline.natural_candidates),
        successor_snapshot=successor,
        lexical_atom_specs=lexical_specs,
    )[0]
    base = candidate.base_candidate
    witness = inverse.parse_step11_rc0030_experiment_surface(
        candidate.final_utf8_bytes
    )
    base_body_witness = inverse.parse_step11_rc0030_base_body_exact_reuse(
        base.final_utf8_bytes
    )
    binding = inverse.match_step11_rc0030_experiment_surface(
        witness,
        base_body_witness=base_body_witness,
        **_source_kwargs(baseline, successor, base),
    )
    return baseline, successor, lexical_specs, candidate, witness, binding


@lru_cache(maxsize=1)
def _reuse_context() -> tuple[Any, ...]:
    surface = importlib.import_module("emlis_ai_step11_natural_surface_v3")
    inverse = importlib.import_module(
        "emlis_ai_step11_natural_surface_matcher_v3"
    )
    baseline, successor, lexical_specs = _authority("nls3s_b001_0001")
    base = tuple(baseline.natural_candidates)[0]
    base_body_witness = inverse.parse_step11_rc0030_base_body_exact_reuse(
        base.final_utf8_bytes
    )
    reuse = inverse.match_step11_rc0030_base_body_exact_reuse(
        base_body_witness,
        **_source_kwargs(baseline, successor, base),
    )
    forward_reuse = tuple(
        surface.Step11Rc0030BaseBodyExactReuseBinding(
            source_atom_id=row.source_atom_id,
            semantic_family=row.semantic_family,
            base_parsed_atom_id=row.base_parsed_atom_id,
            base_obligation_id=row.base_obligation_id,
            match_basis=row.match_basis,
            base_surface_sha256=row.base_surface_sha256,
            source_authority_sha256=row.source_authority_sha256,
            independent_binding_sha256=row.independent_binding_sha256,
        )
        for row in reuse
    )
    candidate = surface.build_step11_rc0030_experiment_surface_candidate(
        base,
        successor_snapshot=successor,
        lexical_atom_specs=lexical_specs,
        base_body_exact_reuse_bindings=forward_reuse,
    )
    witness = inverse.parse_step11_rc0030_experiment_surface(
        candidate.final_utf8_bytes
    )
    binding = inverse.match_step11_rc0030_experiment_surface(
        witness,
        base_body_witness=base_body_witness,
        verified_base_reuse_bindings=reuse,
        **_source_kwargs(baseline, successor, base),
    )
    return (
        baseline,
        successor,
        lexical_specs,
        base,
        base_body_witness,
        reuse,
        candidate,
        witness,
        binding,
    )


def _match_mutated(case_id: str, witness: Any) -> Any:
    inverse = importlib.import_module(
        "emlis_ai_step11_natural_surface_matcher_v3"
    )
    baseline, successor, _lexical, candidate, _witness, _binding = _direct(
        case_id
    )
    base = candidate.base_candidate
    base_body_witness = inverse.parse_step11_rc0030_base_body_exact_reuse(
        base.final_utf8_bytes
    )
    return inverse.match_step11_rc0030_experiment_surface(
        witness,
        base_body_witness=base_body_witness,
        **_source_kwargs(baseline, successor, base),
    )


def _assert_closed_inverse(call: Callable[[], Any], code: str) -> str:
    inverse = importlib.import_module(
        "emlis_ai_step11_natural_surface_matcher_v3"
    )
    try:
        call()
    except inverse.Step11Rc0030ExperimentInverseSurfaceError as exc:
        _closed_assert(
            exc.code == str(exc)
            and exc.code.startswith("STEP11_RC0030_")
            and "\n" not in exc.code
            and "\r" not in exc.code,
            code,
        )
        return exc.code
    except Exception:
        pytest.fail(code, pytrace=False)
    pytest.fail(code, pytrace=False)


def test_rc0030_p3_p2_predecessor_and_inverse_scope_are_exact() -> None:
    for path, (byte_count, expected_sha256) in _P2_FILES.items():
        _closed_assert(
            path.stat().st_size == byte_count and _sha256(path) == expected_sha256,
            "STEP11_RC0030_P3_P2_PREDECESSOR_DRIFT",
        )
    matcher = _MATCHER_PATH.read_bytes()
    _closed_assert(
        hashlib.sha256(matcher[:_MATCHER_P2_PREFIX_BYTES]).hexdigest()
        == _MATCHER_P2_PREFIX_SHA256,
        "STEP11_RC0030_P3_MATCHER_PREFIX_DRIFT",
    )
    _closed_assert(
        len(matcher) == _MATCHER_P3_FULL_BYTES
        and hashlib.sha256(matcher).hexdigest() == _MATCHER_P3_FULL_SHA256
        and len(matcher[_MATCHER_P2_PREFIX_BYTES:])
        == _MATCHER_P3_SUFFIX_BYTES
        and hashlib.sha256(matcher[_MATCHER_P2_PREFIX_BYTES:]).hexdigest()
        == _MATCHER_P3_SUFFIX_SHA256,
        "STEP11_RC0030_P3_MATCHER_SUFFIX_DRIFT",
    )
    _closed_assert(
        _sha256(_GATE_PATH) == _GATE_SHA256
        and _sha256(_P1_FIXTURE) == _P1_FIXTURE_SHA256
        and _sha256(_P1_TEST) == _P1_TEST_SHA256,
        "STEP11_RC0030_P3_FROZEN_AUTHORITY_DRIFT",
    )


def test_rc0030_p3_inverse_suffix_is_forward_import_free_and_unique() -> None:
    suffix = _MATCHER_PATH.read_bytes()[_MATCHER_P2_PREFIX_BYTES:]
    tree = ast.parse(suffix.decode("utf-8"))
    imports = _imported_modules(tree)
    definitions = _definition_counts(tree)
    _closed_assert(
        not (imports & _FORBIDDEN_INVERSE_IMPORTS),
        "STEP11_RC0030_P3_FORWARD_IMPORT_FORBIDDEN",
    )
    _closed_assert(
        all(definitions.get(name) == 1 for name in _EXPECTED_PUBLIC_SYMBOLS),
        "STEP11_RC0030_P3_INVERSE_SYMBOL_COUNT_INVALID",
    )
    rc0030_definitions = {
        name: count
        for name, count in definitions.items()
        if "rc0030" in name.lower() or name.startswith("Step11Rc0030")
    }
    _closed_assert(
        bool(rc0030_definitions)
        and all(count == 1 for count in rc0030_definitions.values()),
        "STEP11_RC0030_P3_INVERSE_SYMBOL_SHADOW",
    )
    inverse = importlib.import_module(
        "emlis_ai_step11_natural_surface_matcher_v3"
    )
    final_parser_parameters = tuple(
        inspect.signature(inverse.parse_step11_rc0030_experiment_surface).parameters
    )
    base_parser_parameters = tuple(
        inspect.signature(
            inverse.parse_step11_rc0030_base_body_exact_reuse
        ).parameters
    )
    final_matcher_parameters = set(
        inspect.signature(inverse.match_step11_rc0030_experiment_surface).parameters
    )
    _closed_assert(
        final_parser_parameters == ("body",)
        and base_parser_parameters == ("base_body",)
        and not (final_matcher_parameters & _FORBIDDEN_INVERSE_PARAMETERS)
        and "base_body" not in final_matcher_parameters
        and "base_body_witness" in final_matcher_parameters,
        "STEP11_RC0030_P3_INVERSE_INPUT_BOUNDARY_INVALID",
    )


@pytest.mark.parametrize(
    "api_name",
    (
        "parse_step11_rc0030_experiment_surface",
        "parse_step11_rc0030_base_body_exact_reuse",
    ),
)
@pytest.mark.parametrize(
    "metadata_name",
    (
        "candidate",
        "forward_plan",
        "candidate_ast",
        "span_map",
        "candidate_owner_ids",
        "covered_ids",
    ),
)
def test_rc0030_p3_body_parser_rejects_forward_metadata(
    api_name: str, metadata_name: str
) -> None:
    inverse = importlib.import_module(
        "emlis_ai_step11_natural_surface_matcher_v3"
    )
    with pytest.raises(TypeError):
        getattr(inverse, api_name)(b"x", **{metadata_name: object()})


@pytest.mark.parametrize("case_id", _DIRECT_CASE_IDS)
def test_rc0030_p3_representative_parse_and_match_are_deterministic_body_only(
    case_id: str,
) -> None:
    inverse = importlib.import_module(
        "emlis_ai_step11_natural_surface_matcher_v3"
    )
    baseline, successor, _lexical, candidate, witness, binding = _direct(case_id)
    base = candidate.base_candidate
    second_witness = inverse.parse_step11_rc0030_experiment_surface(
        candidate.final_utf8_bytes
    )
    second_base = inverse.parse_step11_rc0030_base_body_exact_reuse(
        base.final_utf8_bytes
    )
    second_binding = inverse.match_step11_rc0030_experiment_surface(
        second_witness,
        base_body_witness=second_base,
        **_source_kwargs(baseline, successor, base),
    )
    _closed_assert(
        second_witness == witness
        and second_binding == binding
        and witness.body_scan_pass_count == 2
        and 0 <= witness.decomposition_locus_count <= 38
        and 0 <= witness.evaluated_decomposition_count <= 76
        and 0 <= witness.peak_stored_decomposition_count < 2
        and binding.owner_binding_comparison_count <= 576
        and binding.unique_solution_count == 1
        and binding.semantic_coverage_authorized is False
        and binding.hard_verified is True
        and binding.issue_codes == (),
        "STEP11_RC0030_P3_DIRECT_INVERSE_CONTRACT_INVALID",
    )


def test_rc0030_p3_0001_unknown_base_reuse_is_exact_unique_and_body_only() -> None:
    inverse = importlib.import_module(
        "emlis_ai_step11_natural_surface_matcher_v3"
    )
    (
        _baseline,
        successor,
        _lexical,
        _base,
        base_body_witness,
        reuse,
        _candidate,
        _witness,
        binding,
    ) = _reuse_context()
    _closed_assert(
        len(reuse) == 1,
        "STEP11_RC0030_P3_0001_REUSE_CARDINALITY_INVALID",
    )
    row = reuse[0]
    _closed_assert(
        row.source_atom_id == "semantic_unknown:u2fddc7083cf9a9f771ab8c08"
        and row.semantic_family == "explicit_unknown"
        and row.base_parsed_atom_id == "nls3s11atom_9b08974106c89751"
        and row.base_obligation_id == "obl_95d35127c3f9d6d0"
        and row.match_basis == "unknown_id_dimension_exact_target"
        and row.base_surface_sha256 == base_body_witness.body_sha256
        and row.source_authority_sha256
        == successor.relation_construction_authority.authority_sha256
        and binding.semantic_coverage_authorized is False
        and sum(
            item.verified_reuse_binding_sha256 == row.independent_binding_sha256
            for item in binding.semantic_bindings
        )
        == 1,
        "STEP11_RC0030_P3_0001_REUSE_CHAIN_INVALID",
    )
    material = inverse.step11_rc0030_verified_base_body_reuse_material(row)
    _closed_assert(
        not (_all_keys(material) & _FORBIDDEN_EXPORT_KEYS),
        "STEP11_RC0030_P3_REUSE_MATERIAL_BODY_LEAK",
    )


def test_rc0030_p3_inverse_placement_matches_p2_plan_without_runtime_dependency() -> None:
    for case_id in _DIRECT_CASE_IDS:
        (
            _baseline,
            _successor,
            _lexical,
            candidate,
            witness,
            binding,
        ) = _direct(case_id)
        parsed_by_id = {row.atom_id: row for row in witness.semantic_atoms}
        planned_by_source = {
            row.source_atom_id: row
            for row in candidate.surface_realization_plan.semantic_chunk_bindings
        }
        seen_positions: list[tuple[int, int, int, int]] = []
        for row in binding.semantic_bindings:
            if row.parsed_atom_id is None:
                continue
            parsed = parsed_by_id[row.parsed_atom_id]
            planned = planned_by_source[row.source_atom_id]
            _closed_assert(
                parsed.sentence_group_ordinal == planned.sentence_group_ordinal
                and parsed.grammatical_chunk_ordinal == planned.chunk_ordinal,
                "STEP11_RC0030_P3_INVERSE_PLACEMENT_MISMATCH",
            )
            seen_positions.append(
                (
                    parsed.sentence_group_ordinal,
                    parsed.grammatical_chunk_ordinal,
                    parsed.pack_ordinal,
                    parsed.item_ordinal,
                )
            )
        _closed_assert(
            seen_positions == sorted(seen_positions)
            and len(seen_positions) == len(set(seen_positions)),
            "STEP11_RC0030_P3_INVERSE_ORDER_INVALID",
        )


@pytest.mark.parametrize(
    "attack",
    ("base_stem", "final_body_sha", "final_prefix", "final_atom_id"),
)
def test_rc0030_p3_parser_issued_witness_origin_rejects_coherent_replacement(
    attack: str,
) -> None:
    inverse = importlib.import_module(
        "emlis_ai_step11_natural_surface_matcher_v3"
    )
    baseline, successor, _lexical, candidate, witness, _binding = _direct(
        "nls3s_b001_0001"
    )
    base = candidate.base_candidate
    base_body_witness = inverse.parse_step11_rc0030_base_body_exact_reuse(
        base.final_utf8_bytes
    )
    if attack == "base_stem":
        forged_base = replace(
            base_body_witness,
            observation_stem_sha256=(
                "1" * 64,
                *base_body_witness.observation_stem_sha256[1:],
            ),
        )
        _assert_closed_inverse(
            lambda: inverse.match_step11_rc0030_base_body_exact_reuse(
                forged_base,
                **_source_kwargs(baseline, successor, base),
            ),
            "STEP11_RC0030_P3_BASE_WITNESS_ORIGIN_FORGERY_ACCEPTED",
        )
        return
    if attack == "final_body_sha":
        forged = replace(witness, body_sha256="1" * 64)
    elif attack == "final_prefix":
        forged = replace(
            witness,
            base_prefix_commitments=(
                "1" * 64,
                *witness.base_prefix_commitments[1:],
            ),
        )
    else:
        forged_atom = replace(witness.semantic_atoms[0], atom_id="nls3s11rc0030atom_deadbeefdeadbeef")
        forged = replace(
            witness,
            semantic_atoms=(forged_atom, *witness.semantic_atoms[1:]),
        )
    _assert_closed_inverse(
        lambda: inverse.match_step11_rc0030_experiment_surface(
            forged,
            base_body_witness=base_body_witness,
            **_source_kwargs(baseline, successor, base),
        ),
        "STEP11_RC0030_P3_FINAL_WITNESS_ORIGIN_FORGERY_ACCEPTED",
    )


@pytest.mark.parametrize(
    "attack",
    ("lexical_only", "partial_match", "covered", "forged_ids"),
)
def test_rc0030_p3_forged_base_reuse_is_independently_rejected(
    attack: str,
) -> None:
    from emlis_ai_nls_v3_artifact_contract import artifact_sha256

    inverse = importlib.import_module(
        "emlis_ai_step11_natural_surface_matcher_v3"
    )
    (
        baseline,
        successor,
        _lexical,
        base,
        base_body_witness,
        reuse,
        _candidate,
        witness,
        _binding,
    ) = _reuse_context()
    clean = reuse[0]
    forged = replace(
        clean,
        match_basis=(attack if attack != "forged_ids" else clean.match_basis),
        base_parsed_atom_id=(
            "nls3s11atom_deadbeefdeadbeef"
            if attack == "forged_ids"
            else clean.base_parsed_atom_id
        ),
        base_obligation_id=(
            "obl_deadbeefdeadbeef"
            if attack == "forged_ids"
            else clean.base_obligation_id
        ),
        independent_binding_sha256="0" * 64,
    )
    forged = replace(
        forged,
        independent_binding_sha256=artifact_sha256(
            {
                "schema_version": forged.schema_version,
                "source_atom_id": forged.source_atom_id,
                "semantic_family": forged.semantic_family,
                "base_parsed_atom_id": forged.base_parsed_atom_id,
                "base_obligation_id": forged.base_obligation_id,
                "match_basis": forged.match_basis,
                "base_surface_sha256": forged.base_surface_sha256,
                "source_authority_sha256": forged.source_authority_sha256,
                "body_free": forged.body_free,
            }
        ),
    )
    with pytest.raises(inverse.Step11Rc0030ExperimentInverseSurfaceError):
        inverse.match_step11_rc0030_experiment_surface(
            witness,
            base_body_witness=base_body_witness,
            verified_base_reuse_bindings=(forged,),
            **_source_kwargs(baseline, successor, base),
        )


def test_rc0030_p3_duplicate_reexposition_and_reuse_credit_is_rejected() -> None:
    inverse = importlib.import_module(
        "emlis_ai_step11_natural_surface_matcher_v3"
    )
    baseline, successor, _lexical, candidate, witness, _binding = _direct(
        "nls3s_b001_0001"
    )
    base = candidate.base_candidate
    base_body_witness = inverse.parse_step11_rc0030_base_body_exact_reuse(
        base.final_utf8_bytes
    )
    reuse = inverse.match_step11_rc0030_base_body_exact_reuse(
        base_body_witness,
        **_source_kwargs(baseline, successor, base),
    )
    _closed_assert(bool(reuse), "STEP11_RC0030_P3_REUSE_ATTACK_DENOMINATOR_EMPTY")
    with pytest.raises(inverse.Step11Rc0030ExperimentInverseSurfaceError):
        inverse.match_step11_rc0030_experiment_surface(
            witness,
            base_body_witness=base_body_witness,
            verified_base_reuse_bindings=reuse,
            **_source_kwargs(baseline, successor, base),
        )


@pytest.mark.parametrize(
    "attack",
    (
        "owner",
        "direction",
        "sentence_group",
        "grammatical_chunk",
        "semantic_reorder",
        "semantic_duplicate",
        "reception_binding_id",
        "reception_move",
        "reception_target",
        "reception_act",
        "reception_drop",
    ),
)
def test_rc0030_p3_semantic_chunk_and_reception_mutations_fail_closed(
    attack: str,
) -> None:
    inverse = importlib.import_module(
        "emlis_ai_step11_natural_surface_matcher_v3"
    )
    _baseline, _successor, _lexical, _candidate, witness, _binding = _direct(
        "nls3s_b001_0035"
    )
    atoms = list(witness.semantic_atoms)
    receptions = list(witness.reception_bindings)
    if attack == "owner":
        atoms[0] = replace(atoms[0], owner_expressions=("forged_owner",))
    elif attack == "direction":
        index = next(i for i, row in enumerate(atoms) if row.direction)
        atoms[index] = replace(
            atoms[index],
            direction=(
                "bidirectional"
                if atoms[index].direction == "source_to_target"
                else "source_to_target"
            ),
        )
    elif attack == "sentence_group":
        atoms[0] = replace(
            atoms[0], sentence_group_ordinal=atoms[0].sentence_group_ordinal + 1
        )
    elif attack == "grammatical_chunk":
        atoms[0] = replace(
            atoms[0],
            grammatical_chunk_ordinal=atoms[0].grammatical_chunk_ordinal + 1,
        )
    elif attack == "semantic_reorder":
        _closed_assert(
            len(atoms) > 1,
            "STEP11_RC0030_P3_REORDER_ATTACK_DENOMINATOR_INVALID",
        )
        atoms = list(reversed(atoms))
    elif attack == "semantic_duplicate":
        atoms.append(atoms[0])
    elif attack == "reception_binding_id":
        receptions[0] = replace(
            receptions[0], binding_id="nls3s11rc0030recv_deadbeefdeadbeef"
        )
    elif attack == "reception_move":
        receptions[0] = replace(
            receptions[0], move_ordinal=receptions[0].move_ordinal + 1
        )
    elif attack == "reception_target":
        receptions[0] = replace(receptions[0], target_expression="forged_target")
    elif attack == "reception_act":
        receptions[0] = replace(receptions[0], reception_act="forged_act")
    else:
        receptions = receptions[1:]
    forged = replace(
        witness,
        semantic_atoms=tuple(atoms),
        reception_bindings=tuple(receptions),
    )
    with pytest.raises(inverse.Step11Rc0030ExperimentInverseSurfaceError):
        _match_mutated("nls3s_b001_0035", forged)


def test_rc0030_p3_cross_group_bridge_placement_mutation_fails_closed() -> None:
    inverse = importlib.import_module(
        "emlis_ai_step11_natural_surface_matcher_v3"
    )
    _baseline, _successor, _lexical, candidate, witness, binding = _direct(
        "nls3s_b001_0100"
    )
    planned = {
        row.source_atom_id: row
        for row in candidate.surface_realization_plan.semantic_chunk_bindings
    }
    bridge = next(
        row
        for row in binding.semantic_bindings
        if row.parsed_atom_id is not None
        and planned[row.source_atom_id].cross_group_bridge
    )
    atoms = list(witness.semantic_atoms)
    index = next(i for i, row in enumerate(atoms) if row.atom_id == bridge.parsed_atom_id)
    atoms[index] = replace(
        atoms[index],
        sentence_group_ordinal=(
            atoms[index].sentence_group_ordinal % witness.observation_group_count
        )
        + 1,
    )
    forged = replace(witness, semantic_atoms=tuple(atoms))
    _assert_closed_inverse(
        lambda: _match_mutated("nls3s_b001_0100", forged),
        "STEP11_RC0030_P3_BRIDGE_PLACEMENT_FORGERY_ACCEPTED",
    )


def _mutated_body_match(
    case_id: str, mutate_text: Callable[[str], str]
) -> Any:
    inverse = importlib.import_module(
        "emlis_ai_step11_natural_surface_matcher_v3"
    )
    baseline, successor, _lexical, candidate, _witness, _binding = _direct(case_id)
    base = candidate.base_candidate
    text = candidate.final_utf8_bytes.decode("utf-8", errors="strict")
    changed = mutate_text(text)
    _closed_assert(
        changed != text,
        "STEP11_RC0030_P3_BODY_ATTACK_NOT_APPLIED",
    )
    parsed = inverse.parse_step11_rc0030_experiment_surface(
        changed.encode("utf-8", errors="strict")
    )
    base_body_witness = inverse.parse_step11_rc0030_base_body_exact_reuse(
        base.final_utf8_bytes
    )
    return inverse.match_step11_rc0030_experiment_surface(
        parsed,
        base_body_witness=base_body_witness,
        **_source_kwargs(baseline, successor, base),
    )


def test_rc0030_p3_visible_delimiter_chunk_mutation_fails_closed() -> None:
    catalog = importlib.import_module(
        "emlis_ai_step11_rc0030_experiment_surface_catalog_v3"
    ).STEP11_RC0030_EXPERIMENT_SURFACE_CATALOG
    predicate = catalog["clause_morphology"]["semantic_pack_predicate_suffix"]

    def mutate(text: str) -> str:
        observation, reception = text.split("\n\nEmlisから：\n", 1)
        terminal = observation.index(predicate)
        comma = observation.rfind("、", 0, terminal)
        period = observation.rfind("。", 0, terminal)
        boundary = max(comma, period)
        _closed_assert(
            boundary >= 0,
            "STEP11_RC0030_P3_DELIMITER_ATTACK_DENOMINATOR_INVALID",
        )
        replacement = "。" if observation[boundary] == "、" else "、"
        observation = observation[:boundary] + replacement + observation[boundary + 1 :]
        return observation + "\n\nEmlisから：\n" + reception

    _assert_closed_inverse(
        lambda: _mutated_body_match("nls3s_b001_0035", mutate),
        "STEP11_RC0030_P3_VISIBLE_DELIMITER_MUTATION_ACCEPTED",
    )


@pytest.mark.parametrize("attack", ("move_swap", "line_scope", "target", "act"))
def test_rc0030_p3_visible_reception_schedule_mutation_fails_closed(
    attack: str,
) -> None:
    catalog = importlib.import_module(
        "emlis_ai_step11_rc0030_experiment_surface_catalog_v3"
    ).STEP11_RC0030_EXPERIMENT_SURFACE_CATALOG
    acts = tuple(catalog["reception_act_predicate_fragments"].values())

    def mutate(text: str) -> str:
        observation, reception = text.split("\n\nEmlisから：\n", 1)
        _closed_assert(
            "\n" not in reception and reception.endswith("。"),
            "STEP11_RC0030_P3_RECEPTION_ATTACK_DENOMINATOR_INVALID",
        )
        moves = reception[:-1].split("。")
        _closed_assert(
            len(moves) == 2,
            "STEP11_RC0030_P3_RECEPTION_ATTACK_DENOMINATOR_INVALID",
        )
        if attack == "move_swap":
            reception = "。".join(reversed(moves)) + "。"
        elif attack == "line_scope":
            reception = moves[0] + "。\n" + moves[1] + "。"
        elif attack == "target":
            reception = "偽" + reception
        else:
            current = next(value for value in acts if moves[0].endswith(value))
            other = next(value for value in acts if value != current)
            moves[0] = moves[0][: -len(current)] + other
            reception = "。".join(moves) + "。"
        return observation + "\n\nEmlisから：\n" + reception

    _assert_closed_inverse(
        lambda: _mutated_body_match("nls3s_b001_0100", mutate),
        "STEP11_RC0030_P3_VISIBLE_RECEPTION_MUTATION_ACCEPTED",
    )


def test_rc0030_p3_valid_other_source_authority_swap_fails_closed() -> None:
    inverse = importlib.import_module(
        "emlis_ai_step11_natural_surface_matcher_v3"
    )
    baseline, _successor, _lexical, candidate, witness, _binding = _direct(
        "nls3s_b001_0001"
    )
    _other_baseline, other_successor, _other_lexical = _authority(
        "nls3s_b001_0009"
    )
    base = candidate.base_candidate
    base_body_witness = inverse.parse_step11_rc0030_base_body_exact_reuse(
        base.final_utf8_bytes
    )
    _assert_closed_inverse(
        lambda: inverse.match_step11_rc0030_experiment_surface(
            witness,
            base_body_witness=base_body_witness,
            successor_snapshot=other_successor,
            inventory_result=baseline.inventory_result,
            content_plan=baseline.content_plan,
            discourse_plan=base.discourse_plan,
            current_input=baseline.projected_current_input,
        ),
        "STEP11_RC0030_P3_VALID_OTHER_SOURCE_SWAP_ACCEPTED",
    )


@pytest.mark.parametrize(
    "field,value",
    (
        ("decomposition_locus_count", 39),
        ("evaluated_decomposition_count", 77),
        ("peak_stored_decomposition_count", 2),
        ("body_scan_pass_count", 3),
    ),
)
def test_rc0030_p3_frozen_parser_counter_mutation_is_rejected(
    field: str, value: int
) -> None:
    inverse = importlib.import_module(
        "emlis_ai_step11_natural_surface_matcher_v3"
    )
    _baseline, _successor, _lexical, _candidate, witness, _binding = _direct(
        "nls3s_b001_0001"
    )
    forged = replace(witness, **{field: value})
    with pytest.raises(inverse.Step11Rc0030ExperimentInverseSurfaceError):
        inverse.step11_rc0030_experiment_parsed_witness_material(forged)


@pytest.mark.parametrize(
    "api_name",
    (
        "parse_step11_rc0030_experiment_surface",
        "parse_step11_rc0030_base_body_exact_reuse",
    ),
)
def test_rc0030_p3_parser_body_and_utf8_bounds_fail_closed(api_name: str) -> None:
    inverse = importlib.import_module(
        "emlis_ai_step11_natural_surface_matcher_v3"
    )
    api: Callable[..., Any] = getattr(inverse, api_name)
    for body in (b"x" * 1_000_001, b"\xff"):
        with pytest.raises(inverse.Step11Rc0030ExperimentInverseSurfaceError):
            api(body)


def test_rc0030_p3_parsed_and_verified_material_are_body_free() -> None:
    inverse = importlib.import_module(
        "emlis_ai_step11_natural_surface_matcher_v3"
    )
    _baseline, _successor, _lexical, _candidate, witness, binding = _direct(
        "nls3s_b001_0009"
    )
    parsed_material = inverse.step11_rc0030_experiment_parsed_witness_material(
        witness
    )
    binding_material = inverse.step11_rc0030_experiment_verified_binding_material(
        binding
    )
    _closed_assert(
        not (_all_keys(parsed_material) & _FORBIDDEN_EXPORT_KEYS)
        and not (_all_keys(binding_material) & _FORBIDDEN_EXPORT_KEYS)
        and witness.body_free_export_allowed is False
        and binding.body_free_export_allowed is False,
        "STEP11_RC0030_P3_BODY_FREE_MATERIAL_INVALID",
    )
