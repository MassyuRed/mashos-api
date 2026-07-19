# -*- coding: utf-8 -*-
from __future__ import annotations

"""P2-only GREEN checks for the disconnected rc0030 forward Surface.

These tests intentionally do not import or exercise a rc0030 Parser, Matcher,
Hard Gate, selector, runtime adapter, E2, or Product Read.  The frozen P1
integration suite remains RED until those later phases are implemented.
Body-bearing representative material is used only inside the test process;
failures expose one closed code and never a source or rendered body.
"""

import ast
from functools import lru_cache
import hashlib
import importlib
import inspect
import json
from pathlib import Path
import re
from typing import Any, Iterable

import pytest


_TEST_ROOT = Path(__file__).resolve().parent
_REPO_ROOT = _TEST_ROOT.parents[1]
_SERVICE_ROOT = _REPO_ROOT / "ai" / "services" / "ai_inference"
_CYCLE_ROOT = _TEST_ROOT / "fixtures" / "emlis_nls_v3" / "cycle_001"
_GENERATED_ROOT = _TEST_ROOT / "fixtures" / "emlis_nls_v3" / "generated"

_LEXICAL_PATH = _SERVICE_ROOT / "emlis_ai_step11_grounded_lexicalization_v3.py"
_SURFACE_PATH = _SERVICE_ROOT / "emlis_ai_step11_natural_surface_v3.py"
_MATCHER_PATH = _SERVICE_ROOT / "emlis_ai_step11_natural_surface_matcher_v3.py"
_GATE_PATH = _SERVICE_ROOT / "emlis_ai_step11_hard_gate_v3.py"
_CATALOG_PATH = (
    _SERVICE_ROOT / "emlis_ai_step11_rc0030_experiment_surface_catalog_v3.py"
)
_P1_FIXTURE = _CYCLE_ROOT / "rc0030_representative8_body_free.json"
_P1_TEST = _TEST_ROOT / "test_emlis_nls_v3_s11_rc0030_surface_planning_red.py"
_BATCH = _GENERATED_ROOT / "batch_001.jsonl"

_P1_FIXTURE_SHA256 = (
    "9cfbdafaf43a3caed8b5dc00e68b56cd2b24003a002f0a7cbd1c3ec06d598fa5"
)
_P1_TEST_SHA256 = (
    "56bc3603392df982ae748c9c4ae635fc7eca7867213f77bab1de051f35f38191"
)
_FROZEN_PREFIX = {
    _LEXICAL_PATH: (
        103805,
        "43e99c6077e93db61908e11672d08122cb5928fe63fe64ae0ca565659b43bff4",
    ),
    _SURFACE_PATH: (
        290131,
        "2f797d7aad7f16b234b8a8dad57204b5788e4ae23e43306ac8ca5da790eba7a2",
    ),
    _MATCHER_PATH: (
        589793,
        "9bdae4b5c3d99e99dd01b622b9b191afbfa0e601789fba082a03c069b70028b5",
    ),
    _GATE_PATH: (
        129756,
        "6911291682508bcd6df66d39acb7a6b29b1cfc411434d1ff13160125c9af6c9a",
    ),
}
_EXPECTED_CATALOG_DENOMINATOR = {
    "construction_key_count": 13,
    "construction_layout_count": 13,
    "role_position_key_count": 9,
    "relation_type_direction_key_count": 28,
    "semantic_link_type_direction_key_count": 10,
    "unknown_dimension_key_count": 4,
    "owner_role_key_count": 8,
    "owner_kind_key_count": 12,
    "reception_act_key_count": 3,
}
_CATALOG_MAPPING_COUNTS = {
    "construction_clause_fragments": 13,
    "construction_role_layouts": 13,
    "role_position_clause_fragments": 9,
    "relation_clause_fragments": 28,
    "semantic_link_clause_fragments": 10,
    "unknown_clause_fragments": 4,
    "owner_role_clause_fragments": 8,
    "owner_kind_referent_heads": 12,
    "reception_act_predicate_fragments": 3,
}
_EXPECTED_FORWARD_SYMBOLS = {
    _LEXICAL_PATH: {
        "STEP11_RC0030_CLAUSE_READY_LEXICAL_SPECS_SCHEMA",
        "Step11Rc0030ClauseReadyLexeme",
        "Step11Rc0030ClauseReadyLexicalSpecs",
        "build_step11_rc0030_clause_ready_lexical_specs",
        "step11_rc0030_clause_ready_lexical_specs_material",
        "validate_step11_rc0030_clause_ready_lexical_specs",
    },
    _SURFACE_PATH: {
        # The surface-specific names are checked again by the direct P2 tests.
        # This stable minimum prevents a callable-presence-only implementation.
        "build_step11_rc0030_experiment_surface_candidate",
        "build_step11_rc0030_experiment_surface_candidates",
    },
}
_FORBIDDEN_FORWARD_IMPORTS = frozenset(
    {
        "emlis_ai_step11_natural_surface_matcher_v3",
        "emlis_ai_step11_hard_gate_v3",
        "emlis_ai_step11_runtime_adapter_v3",
        "emlis_ai_step11_rc0030_experiment_runtime_adapter_v3",
    }
)
_FORBIDDEN_PARAMETER_PARTS = (
    "case_id",
    "control_id",
    "review_family",
    "failure_family",
    "corpus_row",
    "expected_output",
)
_FORBIDDEN_ORACLE_LITERALS = (
    "nls3s_b001_",
    "MAIN_MEANING_OBSCURED",
    "SCHEMA_EXPOSITION",
    "OPAQUE_ORDINAL_REFERENTS",
    "SURFACE_DISTRIBUTION_OVERCONCENTRATED",
    "EMLIS_RECEPTION_UNBOUND",
    "GENERIC_RECEPTION",
)
_FORBIDDEN_VISIBLE_MARKERS = (
    "構造を見ると",
    "そこには、",
    "、さらに、",
    "つ目の内容",
    "owner",
    "relation record",
    "case_id",
    "control",
    "corpus",
    "review",
    "reason_code",
    "expected_output",
    "「",
    "」",
)
_HIDDEN_MARKERS = ("\u200b", "\u200c", "\u200d", "\ufeff")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_DIRECT_CASE_IDS = (
    "nls3s_b001_0001",
    "nls3s_b001_0009",
    "nls3s_b001_0035",
    "nls3s_b001_0100",
)
_EXACT_RECEPTION_ONLY_CASE_IDS = frozenset(_DIRECT_CASE_IDS[:-1])
_EXACT_MATCH_BASIS_BY_SEMANTIC_FAMILY = {
    "construction": "construction_instance_role_layout_exact",
    "relation": "relation_id_endpoint_direction_type_exact",
    "semantic_link": "semantic_link_id_endpoint_direction_type_exact",
    "explicit_unknown": "unknown_id_dimension_exact_target",
}


def _closed_assert(condition: bool, code: str) -> None:
    if not condition:
        pytest.fail(code, pytrace=False)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _top_level_definitions(tree: ast.Module) -> dict[str, int]:
    counts: dict[str, int] = {}
    for node in tree.body:
        names: tuple[str, ...] = ()
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names = (node.name,)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else (node.target,)
            names = tuple(
                target.id for target in targets if isinstance(target, ast.Name)
            )
        for name in names:
            counts[name] = counts.get(name, 0) + 1
    return counts


def _imported_modules(tree: ast.AST) -> frozenset[str]:
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "__import__"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and type(node.args[0].value) is str
        ):
            modules.add(node.args[0].value)
    return frozenset(modules)


def _function_parameter_names(tree: ast.AST) -> tuple[str, ...]:
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            arguments = node.args
            names.extend(row.arg for row in arguments.posonlyargs)
            names.extend(row.arg for row in arguments.args)
            names.extend(row.arg for row in arguments.kwonlyargs)
            if arguments.vararg is not None:
                names.append(arguments.vararg.arg)
            if arguments.kwarg is not None:
                names.append(arguments.kwarg.arg)
    return tuple(names)


def _non_docstring_literals(tree: ast.AST) -> tuple[str, ...]:
    docstrings = {
        id(node.body[0].value)
        for node in ast.walk(tree)
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        and node.body
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
        and type(node.body[0].value.value) is str
    }
    return tuple(
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and type(node.value) is str
        and id(node) not in docstrings
    )


def _leaf_strings(value: Any) -> tuple[str, ...]:
    if type(value) is dict:
        return tuple(
            child
            for item in value.values()
            for child in _leaf_strings(item)
        )
    if type(value) in {list, tuple}:
        return tuple(child for item in value for child in _leaf_strings(item))
    return (value,) if type(value) is str else ()


def _surface_sections(body: bytes) -> tuple[tuple[str, ...], tuple[str, ...]]:
    try:
        text = body.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        pytest.fail("STEP11_RC0030_P2_RENDER_UTF8_INVALID", pytrace=False)
    _closed_assert(text.encode("utf-8") == body, "STEP11_RC0030_P2_RENDER_UTF8_NONCANONICAL")
    prefix = "見えたこと：\n"
    separator = "\n\nEmlisから：\n"
    _closed_assert(
        text.startswith(prefix) and text.count(separator) == 1,
        "STEP11_RC0030_P2_RENDER_LAYOUT_INVALID",
    )
    observation, reception = text[len(prefix) :].split(separator)
    observation_lines = tuple(observation.split("\n"))
    reception_lines = tuple(reception.split("\n"))
    _closed_assert(
        bool(observation_lines)
        and bool(reception_lines)
        and all((*observation_lines, *reception_lines)),
        "STEP11_RC0030_P2_RENDER_LAYOUT_INVALID",
    )
    return observation_lines, reception_lines


@lru_cache(maxsize=1)
def _p1_authority() -> tuple[dict[str, Any], dict[str, dict[str, Any]], str]:
    fixture = json.loads(_P1_FIXTURE.read_text(encoding="utf-8"))
    _closed_assert(type(fixture) is dict, "STEP11_RC0030_P2_FIXTURE_TYPE_INVALID")
    rows = fixture.get("rows")
    _closed_assert(type(rows) is list, "STEP11_RC0030_P2_FIXTURE_ROWS_INVALID")
    row_by_id = {
        row.get("case_id"): row
        for row in rows
        if type(row) is dict and type(row.get("case_id")) is str
    }
    _closed_assert(
        set(_DIRECT_CASE_IDS) <= set(row_by_id),
        "STEP11_RC0030_P2_FIXTURE_ROWS_INVALID",
    )
    samples: dict[str, dict[str, Any]] = {}
    for line in _BATCH.read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        row = json.loads(line)
        if type(row) is dict and row.get("case_id") in _DIRECT_CASE_IDS:
            samples[row["case_id"]] = row
    _closed_assert(
        set(samples) == set(_DIRECT_CASE_IDS),
        "STEP11_RC0030_P2_PRIVATE_SOURCE_SET_INVALID",
    )
    closure = fixture.get("predecessor", {}).get(
        "rc0029_source_dependency_closure_sha256"
    )
    _closed_assert(
        type(closure) is str and _SHA256_RE.fullmatch(closure) is not None,
        "STEP11_RC0030_P2_PREDECESSOR_CLOSURE_INVALID",
    )
    return row_by_id, samples, closure


@lru_cache(maxsize=None)
def _forward_authority(case_id: str) -> tuple[Any, Any, Any]:
    _rows, samples, closure = _p1_authority()
    from emlis_ai_evidence_ledger_service import (
        build_evidence_ledger,
        build_evidence_span_resolver,
    )
    from emlis_ai_grounded_lexical_role_experiment_snapshot_successor_v3 import (
        build_grounded_lexical_role_experiment_snapshot_successor,
        validate_grounded_lexical_role_experiment_snapshot_successor,
    )
    from emlis_ai_step11_grounded_lexicalization_v3 import (
        build_step11_rc0028_experiment_lexical_atom_specs,
        validate_step11_rc0028_experiment_lexical_atom_specs,
    )
    from emlis_ai_step11_runtime_adapter_v3 import (
        execute_step11_offline_v3,
        validate_step11_runtime_execution,
    )

    baseline = execute_step11_offline_v3(
        samples[case_id]["input"],
        candidate_version_id="nls_v3_rc_0027",
        source_dependency_closure_sha256=closure,
    )
    _closed_assert(
        validate_step11_runtime_execution(baseline) == ()
        and baseline.status == "selected"
        and bool(baseline.natural_candidates)
        and len(baseline.natural_candidates) <= 12,
        "STEP11_RC0030_P2_BASE_RUNTIME_INVALID",
    )
    evidence_spans = tuple(build_evidence_ledger(baseline.normalized_input))
    resolver = build_evidence_span_resolver(
        evidence_spans,
        current_input=baseline.normalized_input,
    )
    successor = build_grounded_lexical_role_experiment_snapshot_successor(
        baseline.grounded_plan,
        resolver,
        observation_stage_context=baseline.observation_stage_context,
        original_input_bundle=baseline.normalized_input,
    )
    _closed_assert(
        validate_grounded_lexical_role_experiment_snapshot_successor(successor)
        == (),
        "STEP11_RC0030_P2_SUCCESSOR_INVALID",
    )
    lexical_specs = build_step11_rc0028_experiment_lexical_atom_specs(successor)
    _closed_assert(
        validate_step11_rc0028_experiment_lexical_atom_specs(
            lexical_specs,
            successor_snapshot=successor,
        )
        == (),
        "STEP11_RC0030_P2_TYPED_LEXICAL_AUTHORITY_INVALID",
    )
    return baseline, successor, lexical_specs


def test_rc0030_p2_frozen_prefix_p1_and_forward_source_scope_are_exact() -> None:
    _closed_assert(_sha256(_P1_FIXTURE) == _P1_FIXTURE_SHA256, "STEP11_RC0030_P2_P1_FIXTURE_DRIFT")
    _closed_assert(_sha256(_P1_TEST) == _P1_TEST_SHA256, "STEP11_RC0030_P2_P1_TEST_DRIFT")

    for path, (byte_count, expected_sha256) in _FROZEN_PREFIX.items():
        prefix = path.read_bytes()[:byte_count]
        _closed_assert(len(prefix) == byte_count, "STEP11_RC0030_P2_FROZEN_PREFIX_TRUNCATED")
        _closed_assert(
            hashlib.sha256(prefix).hexdigest() == expected_sha256,
            "STEP11_RC0030_P2_FROZEN_PREFIX_MISMATCH",
        )

    for path, expected_symbols in _EXPECTED_FORWARD_SYMBOLS.items():
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        definitions = _top_level_definitions(tree)
        for symbol in expected_symbols:
            _closed_assert(
                definitions.get(symbol) == 1,
                "STEP11_RC0030_P2_SYMBOL_DEFINITION_COUNT_INVALID",
            )
        rc0030_definitions = {
            name: count
            for name, count in definitions.items()
            if "rc0030" in name.lower()
            or name.startswith("STEP11_RC0030_")
            or name.startswith("Step11Rc0030")
        }
        _closed_assert(
            bool(rc0030_definitions)
            and all(count == 1 for count in rc0030_definitions.values()),
            "STEP11_RC0030_P2_SYMBOL_SHADOW_DEFINITION",
        )

        imported = _imported_modules(tree)
        _closed_assert(
            not (imported & _FORBIDDEN_FORWARD_IMPORTS),
            "STEP11_RC0030_P2_FORWARD_REVERSE_IMPORT",
        )
        parameters = _function_parameter_names(tree)
        _closed_assert(
            not any(
                forbidden in name.lower()
                for name in parameters
                for forbidden in _FORBIDDEN_PARAMETER_PARTS
            ),
            "STEP11_RC0030_P2_FORBIDDEN_ORACLE_PARAMETER",
        )
        literals = _non_docstring_literals(tree)
        _closed_assert(
            not any(
                marker in literal
                for literal in literals
                for marker in _FORBIDDEN_ORACLE_LITERALS
            ),
            "STEP11_RC0030_P2_FORBIDDEN_ORACLE_LITERAL",
        )

    # P2 must not introduce the later-phase adapter: its presence would make
    # the frozen P1 suite switch subjects before Parser/Gate synchronization.
    _closed_assert(
        not (
            _SERVICE_ROOT
            / "emlis_ai_step11_rc0030_experiment_runtime_adapter_v3.py"
        ).exists(),
        "STEP11_RC0030_P2_RUNTIME_ADAPTER_EARLY",
    )


def test_rc0030_p2_catalog_denominator_is_closed_schema_free_and_single_choice() -> None:
    module = importlib.import_module(
        "emlis_ai_step11_rc0030_experiment_surface_catalog_v3"
    )
    catalog = module.STEP11_RC0030_EXPERIMENT_SURFACE_CATALOG
    _closed_assert(
        module.validate_step11_rc0030_experiment_surface_catalog(catalog) == (),
        "STEP11_RC0030_P2_CATALOG_INVALID",
    )
    _closed_assert(
        type(module.STEP11_RC0030_EXPERIMENT_SURFACE_CATALOG_SHA256) is str
        and _SHA256_RE.fullmatch(
            module.STEP11_RC0030_EXPERIMENT_SURFACE_CATALOG_SHA256
        )
        is not None,
        "STEP11_RC0030_P2_CATALOG_COMMITMENT_INVALID",
    )
    _closed_assert(
        catalog.get("realization_alternatives_per_semantic_key") == 1,
        "STEP11_RC0030_P2_CATALOG_ALTERNATIVE_BOUND_CHANGED",
    )
    _closed_assert(
        catalog.get("resource_bounds")
        == {
            "owner_max": 24,
            "referent_scalar_max": 32,
            **_EXPECTED_CATALOG_DENOMINATOR,
        },
        "STEP11_RC0030_P2_CATALOG_DENOMINATOR_CHANGED",
    )
    for key, expected_count in _CATALOG_MAPPING_COUNTS.items():
        value = catalog.get(key)
        _closed_assert(
            type(value) is dict and len(value) == expected_count,
            "STEP11_RC0030_P2_CATALOG_DENOMINATOR_CHANGED",
        )

    visible_keys = (*_CATALOG_MAPPING_COUNTS, "clause_morphology")
    visible_values = tuple(
        value
        for key in visible_keys
        for value in _leaf_strings(catalog[key])
    )
    _closed_assert(
        all(
            not any(marker in value for marker in _FORBIDDEN_VISIBLE_MARKERS)
            and not any(marker in value for marker in _HIDDEN_MARKERS)
            and "\n" not in value
            and "\r" not in value
            for value in visible_values
        ),
        "STEP11_RC0030_P2_CATALOG_VISIBLE_SCHEMA_MARKER",
    )


@pytest.mark.parametrize("case_id", _DIRECT_CASE_IDS)
def test_rc0030_p2_clause_ready_projection_is_deterministic_owner_connected(
    case_id: str,
) -> None:
    from emlis_ai_step11_grounded_lexicalization_v3 import (
        build_step11_rc0030_clause_ready_lexical_specs,
        validate_step11_rc0030_clause_ready_lexical_specs,
    )

    baseline, successor, lexical_specs = _forward_authority(case_id)
    for base_candidate in tuple(baseline.natural_candidates):
        first = build_step11_rc0030_clause_ready_lexical_specs(
            base_candidate,
            successor_snapshot=successor,
            lexical_atom_specs=lexical_specs,
        )
        second = build_step11_rc0030_clause_ready_lexical_specs(
            base_candidate,
            successor_snapshot=successor,
            lexical_atom_specs=lexical_specs,
        )
        _closed_assert(first == second, "STEP11_RC0030_P2_LEXICAL_NONDETERMINISTIC")
        _closed_assert(
            validate_step11_rc0030_clause_ready_lexical_specs(
                first,
                base_candidate=base_candidate,
                successor_snapshot=successor,
                lexical_atom_specs=lexical_specs,
            )
            == (),
            "STEP11_RC0030_P2_LEXICAL_REVALIDATION_FAILED",
        )
        _closed_assert(
            first.semantic_coverage_authority == "none"
            and first.experimental_only is True
            and first.runtime_connected is False
            and first.max_source_owners == 24
            and first.max_referent_scalars == 32
            and 1 <= len(first.lexemes) <= first.max_source_owners,
            "STEP11_RC0030_P2_LEXICAL_CONTRACT_INVALID",
        )

        plan = base_candidate.surface_ast.surface_realization_plan
        observation_units = tuple(
            sorted(
                (row for row in plan.units if row.section_role == "observation"),
                key=lambda row: row.source_order,
            )
        )
        _closed_assert(
            bool(observation_units)
            and first.base_leading_observation_unit_id
            == observation_units[0].semantic_unit_id,
            "STEP11_RC0030_P2_BASE_LEADING_WITNESS_INVALID",
        )
        groups_by_nucleus: dict[str, set[str]] = {}
        for unit in observation_units:
            for nucleus_id in unit.owner_nucleus_ids:
                groups_by_nucleus.setdefault(str(nucleus_id), set()).add(
                    unit.assigned_sentence_group_id
                )
        for lexeme in first.lexemes:
            _closed_assert(
                bool(lexeme.base_observation_sentence_group_ids)
                and set(lexeme.base_observation_sentence_group_ids)
                <= groups_by_nucleus.get(lexeme.base_source_nucleus_id, set())
                and lexeme.referent_text == lexeme.grounded_phrase_text
                and 1 <= len(lexeme.referent_text) <= 32
                and not any(
                    marker in lexeme.referent_text
                    for marker in (*_FORBIDDEN_VISIBLE_MARKERS, *_HIDDEN_MARKERS)
                )
                and not lexeme.referent_text.endswith(("。", "！", "？", "!", "?")),
                "STEP11_RC0030_P2_LEXICAL_OWNER_GROUP_INVALID",
            )


@pytest.mark.parametrize("case_id", _DIRECT_CASE_IDS)
def test_rc0030_p2_forward_plan_and_schema_free_render_are_deterministic(
    case_id: str,
) -> None:
    from emlis_ai_step11_natural_surface_v3 import (
        build_step11_rc0030_experiment_surface_candidates,
        validate_step11_rc0030_experiment_surface_candidate,
    )

    baseline, successor, lexical_specs = _forward_authority(case_id)
    base_candidates = tuple(baseline.natural_candidates)
    first = build_step11_rc0030_experiment_surface_candidates(
        base_candidates,
        successor_snapshot=successor,
        lexical_atom_specs=lexical_specs,
    )
    second = build_step11_rc0030_experiment_surface_candidates(
        base_candidates,
        successor_snapshot=successor,
        lexical_atom_specs=lexical_specs,
    )
    _closed_assert(
        first == second and 1 <= len(first) <= len(base_candidates) <= 12,
        "STEP11_RC0030_P2_FORWARD_NONDETERMINISTIC",
    )

    for candidate in first:
        _closed_assert(
            validate_step11_rc0030_experiment_surface_candidate(
                candidate,
                successor_snapshot=successor,
                lexical_atom_specs=lexical_specs,
            )
            == (),
            "STEP11_RC0030_P2_FORWARD_REVALIDATION_FAILED",
        )
        _closed_assert(
            candidate.semantic_coverage_authorized is False
            and candidate.replan_count <= 1
            and candidate.experimental_only is True
            and candidate.runtime_connected is False,
            "STEP11_RC0030_P2_FORWARD_BOUNDARY_INVALID",
        )
        plan = candidate.surface_realization_plan
        typed_atom_count = sum(
            len(getattr(candidate, field))
            for field in (
                "construction_atoms",
                "relation_atoms",
                "semantic_link_atoms",
                "explicit_unknown_atoms",
            )
        )
        binding_ids = tuple(
            row.source_atom_id for row in plan.semantic_chunk_bindings
        )
        reuse_ids = tuple(
            row.source_atom_id for row in plan.base_body_exact_reuse_bindings
        )
        _closed_assert(
            len(binding_ids) + len(reuse_ids) == typed_atom_count
            and len(set((*binding_ids, *reuse_ids))) == typed_atom_count
            and not (set(binding_ids) & set(reuse_ids)),
            "STEP11_RC0030_P2_TYPED_ATOM_EXACTLY_ONCE_INVALID",
        )
        assigned_atom_ids = tuple(
            atom_id
            for row in plan.observation_chunk_assignments
            for atom_id in row.source_atom_ids
        )
        _closed_assert(
            sorted(assigned_atom_ids) == sorted(binding_ids)
            and len(assigned_atom_ids) == len(set(assigned_atom_ids)),
            "STEP11_RC0030_P2_CHUNK_ATOM_ACCOUNTING_INVALID",
        )

        assignments = tuple(
            sorted(
                plan.observation_chunk_assignments,
                key=lambda row: (
                    row.sentence_group_ordinal,
                    row.chunk_ordinal,
                ),
            )
        )
        _closed_assert(
            bool(assignments)
            and plan.base_leading_observation_unit_id
            in assignments[0].source_unit_ids
            and not any(
                unit_id in plan.structure_only_unit_ids
                for unit_id in assignments[0].source_unit_ids[
                    : assignments[0].source_unit_ids.index(
                        plan.base_leading_observation_unit_id
                    )
                ]
            ),
            "STEP11_RC0030_P2_BASE_LEADING_ORDER_INVALID",
        )
        _closed_assert(
            plan.maximum_visible_clauses_per_grammatical_sentence == 2
            and plan.maximum_grammatical_complexity_load == 4
            and plan.maximum_repeated_joiner_per_group == 2
            and plan.peak_grammatical_clause_count <= 2
            and plan.peak_grammatical_complexity_load <= 4
            and plan.peak_group_repeated_joiner_count <= 2,
            "STEP11_RC0030_P2_RESOURCE_BOUND_CHANGED",
        )
        for row in assignments:
            _closed_assert(
                1 <= row.visible_clause_count <= 2
                and 1 <= row.complexity_load <= 4
                and len(row.source_unit_ids) == len(set(row.source_unit_ids))
                and len(row.source_atom_ids) <= 4,
                "STEP11_RC0030_P2_CHUNK_RESOURCE_BOUND_EXCEEDED",
            )
        group_units: dict[int, set[str]] = {}
        for row in assignments:
            group_units.setdefault(row.sentence_group_ordinal, set()).update(
                row.source_unit_ids
            )
        _closed_assert(
            all(len(unit_ids) <= 4 for unit_ids in group_units.values()),
            "STEP11_RC0030_P2_GROUP_UNIT_BOUND_EXCEEDED",
        )
        for binding in plan.semantic_chunk_bindings:
            _closed_assert(
                bool(binding.source_owner_ids)
                and len(binding.source_owner_ids)
                == len(binding.owner_base_nucleus_ids)
                == len(binding.owner_sentence_group_ordinals)
                and binding.sentence_group_ordinal
                in binding.owner_sentence_group_ordinals
                and binding.cross_group_bridge
                == (len(set(binding.owner_sentence_group_ordinals)) > 1)
                and (
                    not binding.cross_group_bridge
                    or binding.direction
                    in {"source_to_target", "bidirectional"}
                ),
                "STEP11_RC0030_P2_OWNER_CONNECTED_CHUNK_INVALID",
            )

        required_reception_ids = {
            str(row.source_id)
            for row in successor.base_snapshot.reception_opportunities
            if row.retention == "required" or row.safety_required is True
        }
        _closed_assert(
            {
                row.source_reception_opportunity_id
                for row in candidate.reception_bindings
            }
            == required_reception_ids,
            "STEP11_RC0030_P2_RECEPTION_SOURCE_SET_MISMATCH",
        )
        for reception in candidate.reception_bindings:
            _closed_assert(
                bool(reception.source_target_owner_ids)
                and len(reception.source_target_owner_ids)
                == len(reception.target_referent_texts)
                and len(reception.supporting_source_owner_ids)
                == len(reception.supporting_referent_texts)
                and (
                    (
                        reception.association_basis
                        == "exact_base_opportunity_id"
                        and reception.additional_clause is False
                        and bool(reception.source_base_binding_id)
                    )
                    or (
                        reception.association_basis
                        == "required_opportunity_bounded_schedule"
                        and reception.additional_clause is True
                        and reception.source_base_binding_id is None
                    )
                ),
                "STEP11_RC0030_P2_RECEPTION_ASSOCIATION_INVALID",
            )
        if case_id in _EXACT_RECEPTION_ONLY_CASE_IDS:
            _closed_assert(
                all(
                    row.association_basis == "exact_base_opportunity_id"
                    and row.additional_clause is False
                    for row in candidate.reception_bindings
                ),
                "STEP11_RC0030_P2_RECEPTION_EXACT_ASSOCIATION_REQUIRED",
            )
        else:
            _closed_assert(
                sum(
                    row.association_basis == "exact_base_opportunity_id"
                    for row in candidate.reception_bindings
                )
                == 1
                and sum(
                    row.association_basis
                    == "required_opportunity_bounded_schedule"
                    for row in candidate.reception_bindings
                )
                == 1,
                "STEP11_RC0030_P2_RECEPTION_BOUNDED_SCHEDULE_INVALID",
            )

        base_observation, base_reception = _surface_sections(
            candidate.base_candidate.final_utf8_bytes
        )
        final_observation, final_reception = _surface_sections(
            candidate.final_utf8_bytes
        )
        base_text = "\n".join((*base_observation, *base_reception))
        final_text = "\n".join((*final_observation, *final_reception))
        _closed_assert(
            len(base_observation) == len(final_observation)
            and len(base_reception) == len(final_reception)
            and all(marker not in final_text for marker in _FORBIDDEN_VISIBLE_MARKERS[:-2])
            and all(marker not in final_text for marker in _HIDDEN_MARKERS)
            and final_text.count("「") <= base_text.count("「")
            and final_text.count("」") <= base_text.count("」"),
            "STEP11_RC0030_P2_SCHEMA_FREE_RENDER_INVALID",
        )
        catalog = importlib.import_module(
            "emlis_ai_step11_rc0030_experiment_surface_catalog_v3"
        ).STEP11_RC0030_EXPERIMENT_SURFACE_CATALOG
        pack_suffix = catalog["clause_morphology"][
            "semantic_pack_predicate_suffix"
        ]
        bindings_by_group: dict[int, set[tuple[int, str]]] = {}
        for binding in plan.semantic_chunk_bindings:
            bindings_by_group.setdefault(
                binding.sentence_group_ordinal, set()
            ).add((binding.chunk_ordinal, binding.clause_unit_id))
        structure_only_unit_ids = set(plan.structure_only_unit_ids)
        for group_ordinal, unit_keys in bindings_by_group.items():
            base_line = base_observation[group_ordinal - 1]
            final_line = final_observation[group_ordinal - 1]
            ordered_unit_keys = tuple(sorted(unit_keys))
            base_chunk_ordinals = tuple(
                row.chunk_ordinal
                for row in assignments
                if row.sentence_group_ordinal == group_ordinal
                and any(
                    unit_id not in structure_only_unit_ids
                    for unit_id in row.source_unit_ids
                )
            )
            _closed_assert(
                bool(base_chunk_ordinals)
                and base_line.endswith("。")
                and ordered_unit_keys[0][0] >= max(base_chunk_ordinals)
                and final_line.startswith(base_line.removesuffix("。"))
                and final_line.endswith("。"),
                "STEP11_RC0030_P2_SCHEMA_FREE_PACK_LAYOUT_INVALID",
            )
            base_stem = base_line.removesuffix("。")
            addition = final_line[len(base_stem) :]
            clause_join = catalog["clause_morphology"]["clause_join"]
            chunk_join = catalog["clause_morphology"][
                "grammatical_chunk_join"
            ]
            leading_join = next(
                (
                    joiner
                    for joiner in (clause_join, chunk_join)
                    if addition.startswith(joiner)
                ),
                None,
            )
            _closed_assert(
                leading_join is not None,
                "STEP11_RC0030_P2_RENDERED_CHUNK_BOUNDARY_INVALID",
            )
            pack_pattern = re.compile(
                rf"(.+?{re.escape(pack_suffix)})"
                rf"({re.escape(clause_join)}|{re.escape(chunk_join)})"
            )
            payload = addition[len(leading_join) :]
            pack_matches = tuple(pack_pattern.finditer(payload))
            _closed_assert(
                bool(pack_matches)
                and pack_matches[0].start() == 0
                and all(
                    left.end() == right.start()
                    for left, right in zip(pack_matches, pack_matches[1:])
                )
                and pack_matches[-1].end() == len(payload),
                "STEP11_RC0030_P2_RENDERED_CHUNK_BOUNDARY_INVALID",
            )
            packs = tuple(row.group(1) for row in pack_matches)
            trailing_joiners = tuple(row.group(2) for row in pack_matches)
            unit_chunk_ordinals = tuple(row[0] for row in ordered_unit_keys)
            expected_boundary_joiners = (
                (
                    clause_join
                    if max(base_chunk_ordinals) == unit_chunk_ordinals[0]
                    else chunk_join
                ),
                *(
                    clause_join if left == right else chunk_join
                    for left, right in zip(
                        unit_chunk_ordinals, unit_chunk_ordinals[1:]
                    )
                ),
            )
            rendered_boundary_joiners = (
                leading_join,
                *trailing_joiners[:-1],
            )
            _closed_assert(
                rendered_boundary_joiners == expected_boundary_joiners
                and trailing_joiners[-1]
                == catalog["clause_morphology"]["sentence_suffix"]
                and len(packs) == len(ordered_unit_keys)
                and all(
                    pack.endswith(pack_suffix)
                    and len(re.findall(r"(?:ません|ます)", pack)) == 1
                    for pack in packs
                ),
                "STEP11_RC0030_P2_RENDERED_CHUNK_BOUNDARY_INVALID",
            )


@pytest.mark.parametrize(
    (
        "match_basis,base_surface_sha256,source_authority_sha256,"
        "independent_binding_sha256"
    ),
    (
        ("lexical_only", None, None, "1" * 64),
        ("partial_match", None, None, "1" * 64),
        ("covered", None, None, "1" * 64),
        (
            "unknown_id_dimension_exact_target",
            "1" * 64,
            None,
            "1" * 64,
        ),
        (
            "unknown_id_dimension_exact_target",
            None,
            "1" * 64,
            "1" * 64,
        ),
        ("unknown_id_dimension_exact_target", None, None, "0" * 64),
    ),
)
def test_rc0030_p2_invalid_exact_reuse_commitment_fails_closed(
    match_basis: str,
    base_surface_sha256: str | None,
    source_authority_sha256: str | None,
    independent_binding_sha256: str,
) -> None:
    from emlis_ai_step11_natural_surface_v3 import (
        Step11NaturalSurfaceError,
        Step11Rc0030BaseBodyExactReuseBinding,
        build_step11_rc0030_experiment_surface_candidate,
    )

    baseline, successor, lexical_specs = _forward_authority(
        "nls3s_b001_0001"
    )
    base_candidate = tuple(baseline.natural_candidates)[0]
    clean = build_step11_rc0030_experiment_surface_candidate(
        base_candidate,
        successor_snapshot=successor,
        lexical_atom_specs=lexical_specs,
    )
    _closed_assert(
        len(clean.surface_realization_plan.semantic_chunk_bindings) == 1,
        "STEP11_RC0030_P2_REUSE_ATTACK_DENOMINATOR_INVALID",
    )
    source_binding = clean.surface_realization_plan.semantic_chunk_bindings[0]
    forged = Step11Rc0030BaseBodyExactReuseBinding(
        source_atom_id=source_binding.source_atom_id,
        semantic_family=source_binding.semantic_family,
        base_parsed_atom_id="forged_base_atom",
        base_obligation_id="forged_obligation",
        match_basis=match_basis,
        base_surface_sha256=(
            base_surface_sha256
            if base_surface_sha256 is not None
            else hashlib.sha256(base_candidate.final_utf8_bytes).hexdigest()
        ),
        source_authority_sha256=(
            source_authority_sha256
            if source_authority_sha256 is not None
            else successor.relation_construction_authority.authority_sha256
        ),
        independent_binding_sha256=independent_binding_sha256,
    )
    with pytest.raises(Step11NaturalSurfaceError) as caught:
        build_step11_rc0030_experiment_surface_candidate(
            base_candidate,
            successor_snapshot=successor,
            lexical_atom_specs=lexical_specs,
            base_body_exact_reuse_bindings=(forged,),
        )
    _closed_assert(
        caught.value.code == "STEP11_RC0030_BASE_REUSE_COMMITMENT_INVALID",
        "STEP11_RC0030_P2_INVALID_REUSE_NOT_FAIL_CLOSED",
    )


def test_rc0030_p2_exact_reuse_match_basis_cannot_cross_semantic_family() -> None:
    from emlis_ai_step11_natural_surface_v3 import (
        Step11NaturalSurfaceError,
        Step11Rc0030BaseBodyExactReuseBinding,
        build_step11_rc0030_experiment_surface_candidate,
    )

    baseline, successor, lexical_specs = _forward_authority(
        "nls3s_b001_0001"
    )
    base_candidate = tuple(baseline.natural_candidates)[0]
    clean = build_step11_rc0030_experiment_surface_candidate(
        base_candidate,
        successor_snapshot=successor,
        lexical_atom_specs=lexical_specs,
    )
    _closed_assert(
        len(clean.surface_realization_plan.semantic_chunk_bindings) == 1,
        "STEP11_RC0030_P2_REUSE_ATTACK_DENOMINATOR_INVALID",
    )
    source_binding = clean.surface_realization_plan.semantic_chunk_bindings[0]
    expected_basis = _EXACT_MATCH_BASIS_BY_SEMANTIC_FAMILY.get(
        source_binding.semantic_family
    )
    _closed_assert(
        expected_basis is not None,
        "STEP11_RC0030_P2_REUSE_ATTACK_DENOMINATOR_INVALID",
    )
    wrong_basis = next(
        basis
        for family, basis in _EXACT_MATCH_BASIS_BY_SEMANTIC_FAMILY.items()
        if family != source_binding.semantic_family
    )
    witness_suffix = hashlib.sha256(
        source_binding.source_atom_id.encode("utf-8")
    ).hexdigest()[:16]
    forged = Step11Rc0030BaseBodyExactReuseBinding(
        source_atom_id=source_binding.source_atom_id,
        semantic_family=source_binding.semantic_family,
        base_parsed_atom_id=f"nls3s11atom_{witness_suffix}",
        base_obligation_id=f"obl_{witness_suffix}",
        match_basis=wrong_basis,
        base_surface_sha256=hashlib.sha256(
            base_candidate.final_utf8_bytes
        ).hexdigest(),
        source_authority_sha256=(
            successor.relation_construction_authority.authority_sha256
        ),
        independent_binding_sha256="1" * 64,
    )
    with pytest.raises(Step11NaturalSurfaceError) as caught:
        build_step11_rc0030_experiment_surface_candidate(
            base_candidate,
            successor_snapshot=successor,
            lexical_atom_specs=lexical_specs,
            base_body_exact_reuse_bindings=(forged,),
        )
    _closed_assert(
        caught.value.code == "STEP11_RC0030_BASE_REUSE_COMMITMENT_INVALID",
        "STEP11_RC0030_P2_CROSS_FAMILY_REUSE_BASIS_NOT_FAIL_CLOSED",
    )
