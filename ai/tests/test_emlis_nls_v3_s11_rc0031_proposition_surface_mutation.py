# -*- coding: utf-8 -*-
from __future__ import annotations

"""P2-only checks for the disconnected rc0031 Proposition Surface.

The suite exercises the real forward plan and renderer, but deliberately does
not import or execute the P3 Parser/Matcher, P4 Gate/runtime, P5 attacks, E2,
or Product Read.  Failures expose one body-free closed code only.
"""

import ast
from collections import Counter
from copy import deepcopy
from dataclasses import replace
from functools import lru_cache
import hashlib
import importlib
import json
from pathlib import Path
import re
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
_P1_TEST = _TEST_ROOT / (
    "test_emlis_nls_v3_s11_rc0031_proposition_surface_red.py"
)
_SUPPORT_FIXTURE = (
    _TEST_ROOT / "fixtures" / "grounded_human_reception_exact8_v2_20260712.json"
)

_P1_FIXTURE_SHA256 = (
    "15e8047cd95b453fba4a7a677b428955ea2819e6738e4e1fc1488d24952b78a8"
)
_P1_TEST_SHA256 = (
    "14e90025a18f1fcab8b2d4d8571e7d2be31b271ec2d4ca8e3a22fa56f14f193c"
)
_SUPPORT_FIXTURE_SHA256 = (
    "cb601019dc2c7e4e46281133d3965addf04adf4f6af8defaf715f91f522e3efb"
)
_FROZEN_PREFIX = {
    _LEXICAL_PATH: (
        129615,
        "592f3ab7c90831c3191f51e9e7dd9a1f8c3fe4add1fd31bba9fdc65dccaecc28",
    ),
    _SURFACE_PATH: (
        360675,
        "5f548499e05e5a982f375dde5f059d7eba08f06fbc59bd0a76d9ed788a1e8eaf",
    ),
    _MATCHER_PATH: (
        722658,
        "648a3a6690f8df860053c811a5416fcfc9983524e5ff880a0e6921a122a52e30",
    ),
    _GATE_PATH: (
        208041,
        "88514bb2a179e8d726f36e1666d2618330d95979107403ededc93aa35655943b",
    ),
}
_DIRECT_CASE_IDS = (
    "nls3s_b001_0001",
    "nls3s_b001_0002",
    "nls3s_b001_0009",
    "nls3s_b001_0019",
    "nls3s_b001_0035",
    "nls3s_b001_0043",
    "nls3s_b001_0100",
)
_DISTRIBUTED_CASE_IDS = frozenset(
    {"nls3s_b001_0035", "nls3s_b001_0100"}
)
_SUPPORT_CASE_IDS = ("D", "I6-D02")
_SUPPORT_INPUT_SHA256 = {
    "D": "233f853d6f5f59fff3e1e4667b8b1c02c474785e285612605a9319acfe373dd3",
    "I6-D02": (
        "9a0aa76ecd7d411699edcfb176005e01ae662e89ea74af4c93b2261149369920"
    ),
}
_SUPPORT_DENOMINATOR = {
    "D": (2, 2, 1),
    "I6-D02": (2, 3, 1),
}
_SUPPORT_BASE_CANDIDATES = {"D": 2, "I6-D02": 4}
_SUPPORT_FORWARD_CANDIDATES = {"D": 2, "I6-D02": 2}
_EXPECTED_EXACT18 = (
    "ai/services/ai_inference/emlis_ai_rc0031_proposition_surface_experiment_dependency_manifest_v3.py",
    "ai/services/ai_inference/emlis_ai_step11_rc0031_experiment_runtime_adapter_v3.py",
    "ai/services/ai_inference/emlis_ai_step11_rc0031_experiment_surface_catalog_v3.py",
    "ai/tools/emlis_nls_v3_rc0031_proposition_surface_dependency_manifest.py",
    "ai/tools/emlis_nls_v3_rc0031_proposition_surface_bounded_experiment.py",
    "ai/tests/fixtures/emlis_nls_v3/cycle_001/cycle001_dependency_manifest_rc0031_proposition_surface_experiment.json",
    "ai/tests/fixtures/emlis_nls_v3/cycle_001/rc0031_representative8_body_free.json",
    "ai/tests/test_emlis_nls_v3_s11_rc0031_proposition_surface_red.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0031_proposition_surface_mutation.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0031_e2_integration.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0031_forward_inverse_independence.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0031_runtime_disconnect.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0031_predecessor_immutability.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0031_predecessor_behavior_regression.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0031_control_non_regression.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0031_e3_representative8.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0031_e4_frozen100_read_only.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0031_dependency_closure.py",
)
_EXPECTED_P2_ACTIVE = frozenset(
    {
        _EXPECTED_EXACT18[2],
        _EXPECTED_EXACT18[6],
        _EXPECTED_EXACT18[7],
        _EXPECTED_EXACT18[8],
    }
)
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
_EXPECTED_RESOURCE_BOUNDS = {
    "owner_max": 24,
    "referent_scalar_max": 32,
    **_EXPECTED_CATALOG_DENOMINATOR,
    "visible_clauses_per_grammatical_sentence_max": 2,
    "grammatical_complexity_load_max": 4,
    "repeated_joiner_per_group_max": 2,
}
_CATALOG_MAPPING_COUNTS = {
    "construction_predicate_fragments": 13,
    "construction_role_layouts": 13,
    "role_position_predicate_patterns": 9,
    "relation_predicate_fragments": 28,
    "semantic_link_predicate_fragments": 10,
    "unknown_predicate_fragments": 4,
    "owner_role_particle_patterns": 8,
    "owner_kind_inflection_patterns": 12,
    "reception_act_predicate_fragments": 3,
}
_FORBIDDEN_FORWARD_IMPORTS = (
    "emlis_ai_step11_natural_surface_matcher_v3",
    "emlis_ai_step11_hard_gate_v3",
    "emlis_ai_step11_rc0031_experiment_runtime_adapter_v3",
    "emlis_ai_step11_runtime_adapter_v3",
)
_FORBIDDEN_RC0030_SURFACE_CALLS = (
    "build_step11_rc0030_experiment_surface_candidate",
    "build_step11_rc0030_experiment_surface_candidates",
    "render_step11_rc0030_experiment_surface",
    "STEP11_RC0030_EXPERIMENT_SURFACE_CATALOG",
)
_FORBIDDEN_PARAMETER_PARTS = (
    "case_id",
    "control_id",
    "review_family",
    "failure_family",
    "expected_output",
)
_FORBIDDEN_ORACLE_LITERALS = (
    "nls3s_b001_",
    "MAIN_MEANING_OBSCURED",
    "SCHEMA_EXPOSITION",
    "EMLIS_RECEPTION_UNBOUND",
    "GENERIC_RECEPTION",
)
_FORBIDDEN_VISIBLE_MARKERS = (
    "構造を見ると",
    "つ目の内容",
    "owner",
    "relation record",
    "case_id",
    "control",
    "review",
    "reason_code",
    "expected_output",
    "が見えます",
    "「",
    "」",
    "\u200b",
    "\u200c",
    "\u200d",
    "\ufeff",
)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_EXACT_MATCH_BASIS = {
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


def _surface_sections(body: bytes) -> tuple[tuple[str, ...], tuple[str, ...]]:
    try:
        text = body.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        pytest.fail("STEP11_RC0031_P2_RENDER_UTF8_INVALID", pytrace=False)
    prefix = "見えたこと：\n"
    separator = "\n\nEmlisから：\n"
    _closed_assert(
        text.encode("utf-8") == body
        and text.startswith(prefix)
        and text.count(separator) == 1,
        "STEP11_RC0031_P2_RENDER_LAYOUT_INVALID",
    )
    observation, reception = text[len(prefix) :].split(separator)
    observation_lines = tuple(observation.split("\n"))
    reception_lines = tuple(reception.split("\n"))
    _closed_assert(
        bool(observation_lines)
        and bool(reception_lines)
        and all((*observation_lines, *reception_lines)),
        "STEP11_RC0031_P2_RENDER_LAYOUT_INVALID",
    )
    return observation_lines, reception_lines


def _leaf_strings(value: Any) -> tuple[str, ...]:
    if type(value) is dict:
        return tuple(
            child for item in value.values() for child in _leaf_strings(item)
        )
    if type(value) in {list, tuple}:
        return tuple(child for item in value for child in _leaf_strings(item))
    return (value,) if type(value) is str else ()


def _function_parameter_names(tree: ast.AST) -> tuple[str, ...]:
    names: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        names.extend(row.arg for row in node.args.posonlyargs)
        names.extend(row.arg for row in node.args.args)
        names.extend(row.arg for row in node.args.kwonlyargs)
        if node.args.vararg is not None:
            names.append(node.args.vararg.arg)
        if node.args.kwarg is not None:
            names.append(node.args.kwarg.arg)
    return tuple(names)


@lru_cache(maxsize=1)
def _p1_module() -> Any:
    return importlib.import_module(
        "test_emlis_nls_v3_s11_rc0031_proposition_surface_red"
    )


@lru_cache(maxsize=None)
def _forward_authority(case_id: str) -> tuple[Any, Any, Any]:
    _fixture, samples, closure = _p1_module()._authority()
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
        and 1 <= len(baseline.natural_candidates) <= 12,
        "STEP11_RC0031_P2_BASE_RUNTIME_INVALID",
    )
    evidence_spans = tuple(build_evidence_ledger(baseline.normalized_input))
    resolver = build_evidence_span_resolver(
        evidence_spans, current_input=baseline.normalized_input
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
        "STEP11_RC0031_P2_SUCCESSOR_INVALID",
    )
    lexical_specs = build_step11_rc0028_experiment_lexical_atom_specs(successor)
    _closed_assert(
        validate_step11_rc0028_experiment_lexical_atom_specs(
            lexical_specs, successor_snapshot=successor
        )
        == (),
        "STEP11_RC0031_P2_TYPED_LEXICAL_AUTHORITY_INVALID",
    )
    return baseline, successor, lexical_specs


@lru_cache(maxsize=1)
def _support_authority() -> tuple[dict[str, dict[str, Any]], str]:
    fixture, _samples, closure = _p1_module()._authority()
    reference = fixture.get("support_positive_authority_reference")
    _closed_assert(
        type(reference) is dict
        and reference.get("representative8_support_positive_count") == 0
        and tuple(reference.get("source_authority_case_ids", ()))
        == _SUPPORT_CASE_IDS
        and reference.get("support_positive_required_for_rc0031_mutation")
        is True
        and reference.get("service_case_branch_authorized") is False
        and reference.get("fixture_sha256") == _SUPPORT_FIXTURE_SHA256
        and _sha256(_SUPPORT_FIXTURE) == _SUPPORT_FIXTURE_SHA256,
        "STEP11_RC0031_P2_SUPPORT_AUTHORITY_INVALID",
    )
    try:
        payload = json.loads(_SUPPORT_FIXTURE.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        pytest.fail("STEP11_RC0031_P2_SUPPORT_AUTHORITY_INVALID", pytrace=False)
    rows = {
        row.get("case_id"): row
        for row in payload.get("cases", ())
        if type(row) is dict and row.get("case_id") in _SUPPORT_CASE_IDS
    }
    _closed_assert(
        set(rows) == set(_SUPPORT_CASE_IDS),
        "STEP11_RC0031_P2_SUPPORT_AUTHORITY_INVALID",
    )
    return rows, closure


def _project_support_current_input(value: Any) -> dict[str, Any]:
    _closed_assert(
        type(value) is dict
        and set(value) == {"memo", "memo_action", "emotions", "category"}
        and type(value.get("memo")) is str
        and type(value.get("memo_action")) is str
        and type(value.get("emotions")) is list
        and bool(value["emotions"])
        and all(type(row) is str and row for row in value["emotions"])
        and type(value.get("category")) is list
        and bool(value["category"])
        and all(type(row) is str and row for row in value["category"]),
        "STEP11_RC0031_P2_SUPPORT_INPUT_AUTHORITY_INVALID",
    )
    return {
        "thought_text": value["memo"],
        "action_text": value["memo_action"],
        "emotions": [
            {"type": row, "strength": "medium"} for row in value["emotions"]
        ],
        "categories": list(value["category"]),
    }


@lru_cache(maxsize=None)
def _support_forward_authority(case_id: str) -> tuple[Any, Any, Any]:
    rows, closure = _support_authority()
    row = rows[case_id]
    current_input = row.get("exact_current_input")
    commitment = hashlib.sha256(
        json.dumps(
            current_input,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    _closed_assert(
        commitment == row.get("current_input_sha256")
        == _SUPPORT_INPUT_SHA256[case_id],
        "STEP11_RC0031_P2_SUPPORT_INPUT_COMMITMENT_MISMATCH",
    )
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
        _project_support_current_input(current_input),
        candidate_version_id="nls_v3_rc_0027",
        source_dependency_closure_sha256=closure,
    )
    _closed_assert(
        validate_step11_runtime_execution(baseline) == ()
        and baseline.status == "v3_no_valid_candidate"
        and len(baseline.natural_candidates)
        == _SUPPORT_BASE_CANDIDATES[case_id],
        "STEP11_RC0031_P2_SUPPORT_BASE_RUNTIME_INVALID",
    )
    evidence_spans = tuple(build_evidence_ledger(baseline.normalized_input))
    resolver = build_evidence_span_resolver(
        evidence_spans, current_input=baseline.normalized_input
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
        "STEP11_RC0031_P2_SUPPORT_SUCCESSOR_INVALID",
    )
    lexical_specs = build_step11_rc0028_experiment_lexical_atom_specs(successor)
    _closed_assert(
        validate_step11_rc0028_experiment_lexical_atom_specs(
            lexical_specs, successor_snapshot=successor
        )
        == (),
        "STEP11_RC0031_P2_SUPPORT_LEXICAL_AUTHORITY_INVALID",
    )
    return baseline, successor, lexical_specs


@lru_cache(maxsize=None)
def _direct_candidates(case_id: str) -> tuple[Any, Any, Any, tuple[Any, ...]]:
    from emlis_ai_step11_natural_surface_v3 import (
        build_step11_rc0031_experiment_surface_candidates,
    )

    baseline, successor, lexical_specs = _forward_authority(case_id)
    first = build_step11_rc0031_experiment_surface_candidates(
        tuple(baseline.natural_candidates),
        successor_snapshot=successor,
        lexical_atom_specs=lexical_specs,
    )
    second = build_step11_rc0031_experiment_surface_candidates(
        tuple(baseline.natural_candidates),
        successor_snapshot=successor,
        lexical_atom_specs=lexical_specs,
    )
    _closed_assert(
        first == second
        and 1 <= len(first) <= len(baseline.natural_candidates) <= 12,
        "STEP11_RC0031_P2_FORWARD_NONDETERMINISTIC",
    )
    return baseline, successor, lexical_specs, first


@lru_cache(maxsize=None)
def _support_candidates(case_id: str) -> tuple[Any, Any, Any, tuple[Any, ...]]:
    from emlis_ai_step11_natural_surface_v3 import (
        build_step11_rc0031_experiment_surface_candidates,
    )

    baseline, successor, lexical_specs = _support_forward_authority(case_id)
    first = build_step11_rc0031_experiment_surface_candidates(
        tuple(baseline.natural_candidates),
        successor_snapshot=successor,
        lexical_atom_specs=lexical_specs,
    )
    second = build_step11_rc0031_experiment_surface_candidates(
        tuple(baseline.natural_candidates),
        successor_snapshot=successor,
        lexical_atom_specs=lexical_specs,
    )
    _closed_assert(
        first == second
        and len(first) == _SUPPORT_FORWARD_CANDIDATES[case_id],
        "STEP11_RC0031_P2_SUPPORT_FORWARD_NONDETERMINISTIC",
    )
    return baseline, successor, lexical_specs, first


def _atom_records(
    candidate: Any,
) -> dict[str, tuple[str, tuple[int, ...], str, str]]:
    rows: dict[str, tuple[str, tuple[int, ...], str, str]] = {}
    for atom in candidate.construction_atoms:
        ordinals = tuple(
            dict.fromkeys(
                int(value)
                for role in atom.role_atoms
                for value in role.target_owner_ordinals
            )
        )
        rows[str(atom.construction_instance_id)] = (
            "construction",
            ordinals,
            "",
            str(atom.construction_code),
        )
    for atom in candidate.relation_atoms:
        rows[str(atom.experiment_relation_id)] = (
            "relation",
            (int(atom.from_owner_ordinal), int(atom.to_owner_ordinal)),
            str(atom.direction),
            str(atom.effective_relation_type),
        )
    for atom in candidate.semantic_link_atoms:
        rows[str(atom.source_semantic_link_id)] = (
            "semantic_link",
            (int(atom.from_owner_ordinal), int(atom.to_owner_ordinal)),
            str(atom.direction),
            str(atom.relation_type),
        )
    for atom in candidate.explicit_unknown_atoms:
        rows[str(atom.source_unknown_id)] = (
            "explicit_unknown",
            tuple(int(value) for value in atom.affected_owner_ordinals),
            "",
            str(atom.dimension),
        )
    return rows


def _assert_typed_composition_binding(
    binding: Any,
    atoms: dict[str, tuple[str, tuple[int, ...], str, str]],
    lexeme_by_ordinal: dict[int, Any],
    *,
    code: str,
) -> None:
    try:
        atom_owner_rows = tuple(
            tuple(
                str(lexeme_by_ordinal[ordinal].source_owner_id)
                for ordinal in atoms[atom_id][1]
            )
            for atom_id in binding.source_atom_ids
        )
        expected_families = tuple(
            atoms[atom_id][0] for atom_id in binding.source_atom_ids
        )
        expected_keys = tuple(
            atoms[atom_id][3] for atom_id in binding.source_atom_ids
        )
        expected_directions = tuple(
            atoms[atom_id][2] for atom_id in binding.source_atom_ids
        )
    except (AttributeError, KeyError, TypeError):
        pytest.fail(code, pytrace=False)

    pending = [set(row) for row in atom_owner_rows]
    connected_owners = pending.pop(0) if pending else set()
    while pending:
        connected_index = next(
            (
                index
                for index, owner_ids in enumerate(pending)
                if owner_ids & connected_owners
            ),
            None,
        )
        if connected_index is None:
            break
        connected_owners.update(pending.pop(connected_index))
    common_valid = bool(
        binding.source_atom_ids
        and not pending
        and binding.source_atom_owner_ids == atom_owner_rows
        and set(binding.source_owner_ids) == connected_owners
        and binding.semantic_families == expected_families
        and binding.semantic_keys == expected_keys
        and binding.directions == expected_directions
        and binding.owner_ready_group_ordinal
        == max(binding.owner_sentence_group_ordinals)
        and binding.sentence_group_ordinal
        >= binding.owner_ready_group_ordinal
    )
    if binding.composition_mode == "construction_modified_head":
        modifier_ids = binding.construction_modifier_atom_ids
        target_owner_ids = binding.construction_modifier_target_owner_ids
        head_id = binding.head_source_atom_id
        try:
            head_family, head_ordinals, _direction, _key = atoms[head_id]
            head_owner_ids = tuple(
                str(lexeme_by_ordinal[ordinal].source_owner_id)
                for ordinal in head_ordinals
            )
            modifier_owner_ids = tuple(
                tuple(
                    str(lexeme_by_ordinal[ordinal].source_owner_id)
                    for ordinal in atoms[modifier_id][1]
                )
                for modifier_id in modifier_ids
            )
        except (KeyError, TypeError):
            pytest.fail(code, pytrace=False)
        mode_valid = bool(
            1 <= len(modifier_ids) <= 2
            and len(binding.source_atom_ids) <= 3
            and binding.source_atom_ids == (*modifier_ids, head_id)
            and head_family != "construction"
            and all(atoms[modifier_id][0] == "construction" for modifier_id in modifier_ids)
            and len(target_owner_ids) == len(modifier_ids)
            and len(set(target_owner_ids)) == len(target_owner_ids)
            and all(target in head_owner_ids for target in target_owner_ids)
            and all(
                owner_ids == (target,)
                for owner_ids, target in zip(
                    modifier_owner_ids, target_owner_ids, strict=True
                )
            )
            and binding.visible_clause_count == 1
        )
    elif binding.composition_mode == "independent_clauses":
        mode_valid = bool(
            len(binding.source_atom_ids) <= 2
            and binding.head_source_atom_id == ""
            and binding.construction_modifier_atom_ids == ()
            and binding.construction_modifier_target_owner_ids == ()
            and binding.visible_clause_count == len(binding.source_atom_ids)
        )
    else:
        mode_valid = False
    expected_complexity = max(
        len(binding.source_atom_ids),
        len(connected_owners),
        binding.visible_clause_count,
    )
    _closed_assert(
        common_valid
        and mode_valid
        and binding.complexity_load == expected_complexity
        and binding.complexity_load <= 4,
        code,
    )


def _expected_semantic_clauses(
    candidate: Any, catalog: dict[str, Any]
) -> tuple[str, ...]:
    lexeme_by_ordinal = {
        int(row.source_owner_ordinal): row
        for row in candidate.natural_handle_specs.lexemes
    }
    referent_by_owner = {
        str(row.source_owner_id): str(row.referent_text)
        for row in candidate.natural_handle_specs.lexemes
    }
    morphology = catalog["clause_morphology"]
    construction_by_id = {
        str(row.construction_instance_id): row
        for row in candidate.construction_atoms
    }
    relation_by_id = {
        str(row.experiment_relation_id): row for row in candidate.relation_atoms
    }
    link_by_id = {
        str(row.source_semantic_link_id): row
        for row in candidate.semantic_link_atoms
    }
    unknown_by_id = {
        str(row.source_unknown_id): row
        for row in candidate.explicit_unknown_atoms
    }

    def construction_endpoint(atom_id: str, target_owner_id: str) -> str:
        atom = construction_by_id[atom_id]
        return (
            referent_by_owner[target_owner_id]
            + catalog["construction_predicate_fragments"][
                atom.construction_code
            ]
        )

    def clause(
        atom_id: str,
        decorated_endpoints: dict[str, str] | None = None,
    ) -> str:
        endpoints = decorated_endpoints or {}
        if atom_id in construction_by_id:
            atom = construction_by_id[atom_id]
            ordinals = tuple(
                dict.fromkeys(
                    int(value)
                    for role in atom.role_atoms
                    for value in role.target_owner_ordinals
                )
            )
            _closed_assert(
                len(ordinals) == 1,
                "STEP11_RC0031_P2_CONSTRUCTION_OWNER_AMBIGUOUS",
            )
            owner_id = str(lexeme_by_ordinal[ordinals[0]].source_owner_id)
            return (
                construction_endpoint(atom_id, owner_id)
                + morphology["construction_standalone_predicate"]
            )
        if atom_id in relation_by_id:
            atom = relation_by_id[atom_id]
            source_owner = str(
                lexeme_by_ordinal[int(atom.from_owner_ordinal)].source_owner_id
            )
            target_owner = str(
                lexeme_by_ordinal[int(atom.to_owner_ordinal)].source_owner_id
            )
            return catalog["relation_predicate_fragments"][
                str(atom.effective_relation_type) + ":" + str(atom.direction)
            ].format(
                source=endpoints.get(
                    source_owner, referent_by_owner[source_owner]
                ),
                target=endpoints.get(
                    target_owner, referent_by_owner[target_owner]
                ),
            )
        if atom_id in link_by_id:
            atom = link_by_id[atom_id]
            source_owner = str(
                lexeme_by_ordinal[int(atom.from_owner_ordinal)].source_owner_id
            )
            target_owner = str(
                lexeme_by_ordinal[int(atom.to_owner_ordinal)].source_owner_id
            )
            return catalog["semantic_link_predicate_fragments"][
                str(atom.relation_type) + ":" + str(atom.direction)
            ].format(
                source=endpoints.get(
                    source_owner, referent_by_owner[source_owner]
                ),
                target=endpoints.get(
                    target_owner, referent_by_owner[target_owner]
                ),
            )
        atom = unknown_by_id[atom_id]
        owner_ids = tuple(
            str(lexeme_by_ordinal[int(value)].source_owner_id)
            for value in atom.affected_owner_ordinals
        )
        return (
            morphology["unknown_owner_join"].join(
                endpoints.get(owner_id, referent_by_owner[owner_id])
                for owner_id in owner_ids
            )
            + catalog["unknown_predicate_fragments"][atom.dimension]
        )

    clauses: list[str] = []
    for binding in candidate.surface_realization_plan.proposition_clause_bindings:
        if binding.composition_mode == "construction_modified_head":
            decorated = {
                target_owner_id: construction_endpoint(
                    modifier_atom_id, target_owner_id
                )
                for modifier_atom_id, target_owner_id in zip(
                    binding.construction_modifier_atom_ids,
                    binding.construction_modifier_target_owner_ids,
                    strict=True,
                )
            }
            clauses.append(clause(binding.head_source_atom_id, decorated))
        else:
            clauses.extend(clause(atom_id) for atom_id in binding.source_atom_ids)
    return tuple(clauses)


def _assert_reception_source_exact(candidate: Any, successor: Any) -> None:
    from emlis_ai_step11_rc0031_experiment_surface_catalog_v3 import (
        STEP11_RC0031_EXPERIMENT_SURFACE_CATALOG as catalog,
    )

    required = tuple(
        row
        for row in successor.base_snapshot.reception_opportunities
        if row.retention == "required" or row.safety_required is True
    )
    actual_by_source = {
        str(row.source_id): str(row.actual_source_id)
        for row in successor.base_snapshot.nuclei
    }
    by_source = {
        row.source_reception_opportunity_id: row
        for row in candidate.reception_bindings
    }
    _closed_assert(
        len(by_source) == len(candidate.reception_bindings) == len(required)
        and set(by_source) == {str(row.source_id) for row in required}
        and candidate.reception_bindings
        == candidate.surface_realization_plan.reception_predication_bindings
        == candidate.proposition_surface_ast.reception_predication_bindings,
        "STEP11_RC0031_P2_RECEPTION_DENOMINATOR_INVALID",
    )
    referent_by_owner = {
        str(row.source_owner_id): str(row.referent_text)
        for row in candidate.natural_handle_specs.lexemes
    }
    morphology = catalog["clause_morphology"]
    final_text = candidate.final_utf8_bytes.decode("utf-8", errors="strict")
    for opportunity in required:
        binding = by_source[str(opportunity.source_id)]
        targets = tuple(
            actual_by_source[str(value)] for value in opportunity.target_nucleus_ids
        )
        supports = tuple(
            actual_by_source[str(value)] for value in opportunity.support_nucleus_ids
        )
        _closed_assert(
            binding.source_target_owner_ids == targets
            and binding.supporting_source_owner_ids == supports
            and binding.source_scope == str(opportunity.family)
            and binding.reception_act == str(opportunity.reception_act),
            "STEP11_RC0031_P2_RECEPTION_SOURCE_BINDING_INVALID",
        )
        support_prefix = (
            morphology["support_owner_join"].join(
                referent_by_owner[value] for value in supports
            )
            + morphology["support_target_link"]
            if supports
            else ""
        )
        predication = (
            support_prefix
            + morphology["target_owner_join"].join(
                referent_by_owner[value] for value in targets
            )
            + morphology["reception_object_particle"]
            + catalog["reception_act_predicate_fragments"][
                binding.reception_act
            ]
        )
        _closed_assert(
            final_text.count(predication) == 1,
            "STEP11_RC0031_P2_RECEPTION_PREDICATION_NOT_INTEGRATED",
        )


def _assert_candidate(candidate: Any, successor: Any, lexical_specs: Any) -> None:
    from emlis_ai_step11_natural_surface_v3 import (
        validate_step11_rc0031_experiment_surface_candidate,
    )
    from emlis_ai_step11_rc0031_experiment_surface_catalog_v3 import (
        STEP11_RC0031_EXPERIMENT_SURFACE_CATALOG as catalog,
        STEP11_RC0031_EXPERIMENT_SURFACE_CATALOG_SHA256,
    )

    _closed_assert(
        validate_step11_rc0031_experiment_surface_candidate(
            candidate,
            successor_snapshot=successor,
            lexical_atom_specs=lexical_specs,
        )
        == (),
        "STEP11_RC0031_P2_FORWARD_REVALIDATION_FAILED",
    )
    _closed_assert(
        candidate.semantic_coverage_authorized is False
        and candidate.replan_count == 0
        and candidate.experimental_only is True
        and candidate.private_body_full is True
        and candidate.shareable is False
        and candidate.runtime_connected is False
        and candidate.experiment_catalog_sha256
        == STEP11_RC0031_EXPERIMENT_SURFACE_CATALOG_SHA256
        and candidate.source_lexical_projection_catalog_sha256
        != candidate.experiment_catalog_sha256,
        "STEP11_RC0031_P2_FORWARD_BOUNDARY_INVALID",
    )
    atoms = _atom_records(candidate)
    plan = candidate.surface_realization_plan
    realized = tuple(
        atom_id
        for binding in plan.proposition_clause_bindings
        for atom_id in binding.source_atom_ids
    )
    assigned = tuple(
        atom_id
        for assignment in plan.proposition_chunk_assignments
        for atom_id in assignment.source_atom_ids
    )
    _closed_assert(
        not plan.base_body_exact_reuse_bindings
        and len(realized) == len(set(realized)) == len(atoms)
        and set(realized) == set(atoms)
        and Counter(assigned) == Counter(realized)
        and candidate.rendered_surface.semantic_atom_count == len(atoms)
        and candidate.rendered_surface.exact_reuse_count == 0,
        "STEP11_RC0031_P2_TYPED_ATOM_EXACTLY_ONCE_INVALID",
    )
    lexeme_by_ordinal = {
        int(row.source_owner_ordinal): row
        for row in candidate.natural_handle_specs.lexemes
    }
    for binding in plan.proposition_clause_bindings:
        _assert_typed_composition_binding(
            binding,
            atoms,
            lexeme_by_ordinal,
            code="STEP11_RC0031_P2_OWNER_CONNECTED_DISTRIBUTION_INVALID",
        )
    base_plan = (
        candidate.base_candidate.surface_ast.surface_realization_plan
    )
    group_index = {
        group_id: ordinal
        for ordinal, group_id in enumerate(
            base_plan.observation_sentence_group_ids, start=1
        )
    }
    base_by_chunk: dict[tuple[int, int], list[Any]] = {}
    for unit in base_plan.units:
        if unit.section_role != "observation":
            continue
        key = (
            group_index[unit.assigned_sentence_group_id],
            int(unit.assigned_grammatical_chunk_ordinal),
        )
        base_by_chunk.setdefault(key, []).append(unit)
    props_by_chunk: dict[tuple[int, int], list[Any]] = {}
    for binding in plan.proposition_clause_bindings:
        key = (
            binding.sentence_group_ordinal,
            binding.grammatical_chunk_ordinal,
        )
        props_by_chunk.setdefault(key, []).append(binding)
    assignment_by_chunk = {
        (row.sentence_group_ordinal, row.grammatical_chunk_ordinal): row
        for row in plan.proposition_chunk_assignments
    }
    _closed_assert(
        len(assignment_by_chunk) == len(plan.proposition_chunk_assignments)
        and set(assignment_by_chunk) == set(base_by_chunk) | set(props_by_chunk)
        and all(len(rows) == 1 for rows in props_by_chunk.values()),
        "STEP11_RC0031_P2_RESOURCE_ACCOUNTING_INVALID",
    )
    actual_visible: list[int] = []
    actual_complexity: list[int] = []
    for key, assignment in assignment_by_chunk.items():
        base_rows = tuple(
            sorted(
                base_by_chunk.get(key, ()),
                key=lambda row: (row.source_order, row.semantic_unit_id),
            )
        )
        prop_rows = tuple(
            sorted(
                props_by_chunk.get(key, ()),
                key=lambda row: row.proposition_unit_id,
            )
        )
        visible = len(base_rows) + sum(
            row.visible_clause_count for row in prop_rows
        )
        complexity = sum(
            row.body_free_complexity_weight for row in base_rows
        ) + sum(
            max(
                len(row.source_atom_ids),
                len(row.source_owner_ids),
                row.visible_clause_count,
            )
            for row in prop_rows
        )
        expected_source_units = (
            *(row.semantic_unit_id for row in base_rows),
            *(row.proposition_unit_id for row in prop_rows),
        )
        _closed_assert(
            assignment.visible_clause_count == visible
            and assignment.complexity_load == complexity
            and assignment.source_unit_ids == expected_source_units,
            "STEP11_RC0031_P2_RESOURCE_ACCOUNTING_INVALID",
        )
        actual_visible.append(visible)
        actual_complexity.append(complexity)
    group_unit_counts: dict[int, int] = {}
    group_joiners: dict[int, int] = {}
    for group in range(1, len(group_index) + 1):
        group_unit_counts[group] = sum(
            len(rows)
            for (candidate_group, _chunk), rows in base_by_chunk.items()
            if candidate_group == group
        ) + sum(
            len(rows)
            for (candidate_group, _chunk), rows in props_by_chunk.items()
            if candidate_group == group
        )
        group_joiners[group] = sum(
            max(0, len(rows) - 1)
            for (candidate_group, _chunk), rows in base_by_chunk.items()
            if candidate_group == group
        ) + sum(
            max(0, row.visible_clause_count - 1)
            for (candidate_group, _chunk), rows in props_by_chunk.items()
            if candidate_group == group
            for row in rows
        )
    reception_complexity = tuple(
        len(row.source_target_owner_ids)
        + len(row.supporting_source_owner_ids)
        for row in plan.reception_predication_bindings
    )
    actual_peaks = (
        max(group_unit_counts.values(), default=0),
        max(
            max(actual_visible, default=0),
            1 if plan.reception_predication_bindings else 0,
        ),
        max(
            max(actual_complexity, default=0),
            max(reception_complexity, default=0),
        ),
        max(group_joiners.values(), default=0),
    )
    reported_peaks = (
        plan.peak_observation_clause_count,
        plan.peak_grammatical_clause_count,
        plan.peak_grammatical_complexity_load,
        plan.peak_group_repeated_joiner_count,
    )
    _closed_assert(
        plan.maximum_visible_clauses_per_grammatical_sentence == 2
        and plan.maximum_observation_clauses_per_sentence == 4
        and plan.maximum_grammatical_complexity_load == 4
        and plan.maximum_repeated_joiner_per_group == 2
        and actual_peaks == reported_peaks
        and all(
            actual <= maximum
            for actual, maximum in zip(
                actual_peaks, (4, 2, 4, 2), strict=True
            )
        ),
        "STEP11_RC0031_P2_RESOURCE_BOUND_INVALID",
    )
    base_units = tuple(
        sorted(
            (row for rows in base_by_chunk.values() for row in rows),
            key=lambda row: (row.source_order, row.semantic_unit_id),
        )
    )
    root = plan.root_proposition_binding
    base_observation, _base_reception = _surface_sections(
        candidate.base_candidate.final_utf8_bytes
    )
    final_observation, _final_reception = _surface_sections(
        candidate.final_utf8_bytes
    )
    _closed_assert(
        bool(base_units)
        and sum(row.source_order == base_units[0].source_order for row in base_units)
        == 1
        and root.source_semantic_unit_id == base_units[0].semantic_unit_id
        and root.sentence_group_ordinal == 1
        and root.grammatical_chunk_ordinal == 1
        and root.complete_base_proposition_preserved is True
        and final_observation[0].startswith(base_observation[0])
        and final_observation[0].count(base_observation[0]) == 1,
        "STEP11_RC0031_P2_ROOT_PROPOSITION_INVALID",
    )
    expected_clauses = _expected_semantic_clauses(candidate, catalog)
    final_text = candidate.final_utf8_bytes.decode("utf-8", errors="strict")
    base_text = candidate.base_candidate.final_utf8_bytes.decode(
        "utf-8", errors="strict"
    )
    _closed_assert(
        len(expected_clauses)
        == sum(
            row.visible_clause_count
            for row in plan.proposition_clause_bindings
        )
        == candidate.rendered_surface.proposition_clause_count
        and all(
            final_text.count(clause) == count
            for clause, count in Counter(expected_clauses).items()
        )
        and not any(
            final_text.count(marker) > base_text.count(marker)
            for marker in _FORBIDDEN_VISIBLE_MARKERS
        ),
        "STEP11_RC0031_P2_SCHEMA_FREE_RENDER_INVALID",
    )
    _assert_reception_source_exact(candidate, successor)


def test_rc0031_p2_frozen_prefix_path_scope_and_forward_source_are_exact() -> None:
    _closed_assert(
        _sha256(_P1_FIXTURE) == _P1_FIXTURE_SHA256
        and _sha256(_P1_TEST) == _P1_TEST_SHA256,
        "STEP11_RC0031_P2_P1_FREEZE_DRIFT",
    )
    for path, (byte_count, expected_sha256) in _FROZEN_PREFIX.items():
        prefix = path.read_bytes()[:byte_count]
        _closed_assert(
            len(prefix) == byte_count
            and hashlib.sha256(prefix).hexdigest() == expected_sha256,
            "STEP11_RC0031_P2_FROZEN_PREFIX_MISMATCH",
        )
    _closed_assert(
        all(
            path.stat().st_size == _FROZEN_PREFIX[path][0]
            for path in (_LEXICAL_PATH, _MATCHER_PATH, _GATE_PATH)
        )
        and _SURFACE_PATH.stat().st_size > _FROZEN_PREFIX[_SURFACE_PATH][0],
        "STEP11_RC0031_P2_MODIFIED_EXISTING_SCOPE_INVALID",
    )
    active = frozenset(
        path for path in _EXPECTED_EXACT18 if (_REPO_ROOT / path).exists()
    )
    _closed_assert(
        active == _EXPECTED_P2_ACTIVE,
        "STEP11_RC0031_P2_PATH_SCOPE_INVALID",
    )
    discovered_rc0031 = frozenset(
        path.relative_to(_REPO_ROOT).as_posix()
        for path in (_REPO_ROOT / "ai").rglob("*rc0031*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix != ".pyc"
    )
    _closed_assert(
        discovered_rc0031 == _EXPECTED_P2_ACTIVE,
        "STEP11_RC0031_P2_UNEXPECTED_PATH_PRESENT",
    )
    appended = _SURFACE_PATH.read_bytes()[360675:].decode("utf-8")
    tree = ast.parse(appended)
    parameter_names = _function_parameter_names(tree)
    literals = tuple(
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and type(node.value) is str
    )
    _closed_assert(
        all(value not in appended for value in _FORBIDDEN_FORWARD_IMPORTS)
        and all(value not in appended for value in _FORBIDDEN_RC0030_SURFACE_CALLS)
        and not any(
            marker in name
            for name in parameter_names
            for marker in _FORBIDDEN_PARAMETER_PARTS
        )
        and not any(
            marker in literal
            for literal in literals
            for marker in _FORBIDDEN_ORACLE_LITERALS
        )
        and "build_step11_rc0030_clause_ready_lexical_specs" in appended
        and "validate_step11_rc0030_clause_ready_lexical_specs" in appended,
        "STEP11_RC0031_P2_FORWARD_SOURCE_SCOPE_INVALID",
    )


def test_rc0031_p2_catalog_is_closed_schema_free_and_exact() -> None:
    from emlis_ai_step11_rc0030_experiment_surface_catalog_v3 import (
        STEP11_RC0030_EXPERIMENT_SURFACE_CATALOG as old_catalog,
    )
    from emlis_ai_step11_rc0031_experiment_surface_catalog_v3 import (
        STEP11_RC0031_EXPERIMENT_SURFACE_CATALOG as catalog,
        STEP11_RC0031_EXPERIMENT_SURFACE_CATALOG_SHA256,
        validate_step11_rc0031_experiment_surface_catalog,
    )

    predecessor_key_authorities = {
        "construction_predicate_fragments": "construction_clause_fragments",
        "construction_role_layouts": "construction_role_layouts",
        "role_position_predicate_patterns": (
            "role_position_clause_fragments"
        ),
        "relation_predicate_fragments": "relation_clause_fragments",
        "semantic_link_predicate_fragments": (
            "semantic_link_clause_fragments"
        ),
        "unknown_predicate_fragments": "unknown_clause_fragments",
        "owner_role_particle_patterns": "owner_role_clause_fragments",
        "owner_kind_inflection_patterns": "owner_kind_referent_heads",
        "reception_act_predicate_fragments": (
            "reception_act_predicate_fragments"
        ),
    }
    _closed_assert(
        validate_step11_rc0031_experiment_surface_catalog(catalog) == ()
        and _SHA256_RE.fullmatch(
            STEP11_RC0031_EXPERIMENT_SURFACE_CATALOG_SHA256
        )
        is not None
        and catalog["resource_bounds"] == _EXPECTED_RESOURCE_BOUNDS
        and catalog["realization_alternatives_per_semantic_key"] == 1
        and catalog["experimental_only"] is True
        and catalog["runtime_connected"] is False
        and catalog["body_free"] is True
        and all(
            len(catalog[name]) == count
            for name, count in _CATALOG_MAPPING_COUNTS.items()
        )
        and all(
            set(catalog[current_name]) == set(old_catalog[old_name])
            for current_name, old_name in predecessor_key_authorities.items()
        )
        and catalog["construction_role_layouts"]
        == old_catalog["construction_role_layouts"]
        and all(
            "{" not in fragment
            and "}" not in fragment
            and not fragment.endswith(("ます", "ません", "でした"))
            for fragment in catalog[
                "construction_predicate_fragments"
            ].values()
        )
        and catalog["clause_morphology"][
            "construction_standalone_predicate"
        ]
        == "があります"
        and "reception_scope_fragments" not in catalog
        and "reception_scope_key_count" not in catalog["resource_bounds"],
        "STEP11_RC0031_P2_CATALOG_DENOMINATOR_INVALID",
    )
    relation_patterns = tuple(
        catalog[name].values()
        for name in (
            "relation_predicate_fragments",
            "semantic_link_predicate_fragments",
        )
    )
    relation_patterns_flat = tuple(
        value for rows in relation_patterns for value in rows
    )
    new_visible = tuple(
        value
        for name in (
            "construction_predicate_fragments",
            "relation_predicate_fragments",
            "semantic_link_predicate_fragments",
            "unknown_predicate_fragments",
            "reception_act_predicate_fragments",
        )
        for value in catalog[name].values()
    )
    old_visible = tuple(
        value
        for name in (
            "construction_clause_fragments",
            "role_position_clause_fragments",
            "relation_clause_fragments",
            "semantic_link_clause_fragments",
            "unknown_clause_fragments",
            "owner_role_clause_fragments",
            "owner_kind_referent_heads",
            "reception_act_predicate_fragments",
        )
        for value in old_catalog[name].values()
    )
    _closed_assert(
        len(new_visible) == len(set(new_visible))
        and all(
            value.count("{source}") == 1
            and value.count("{target}") == 1
            for value in relation_patterns_flat
        )
        and not any(
            marker in value
            for value in new_visible
            for marker in _FORBIDDEN_VISIBLE_MARKERS
        )
        and not any(
            old in new or new in old
            for old in old_visible
            for new in new_visible
        ),
        "STEP11_RC0031_P2_CATALOG_SCHEMA_COLLISION",
    )


def test_rc0031_p2_catalog_mutations_fail_closed() -> None:
    from emlis_ai_step11_rc0031_experiment_surface_catalog_v3 import (
        STEP11_RC0031_EXPERIMENT_SURFACE_CATALOG as catalog,
        validate_step11_rc0031_experiment_surface_catalog,
    )

    completed = deepcopy(catalog)
    first_relation = next(iter(completed["relation_predicate_fragments"]))
    completed["relation_predicate_fragments"][first_relation] = (
        "{source}から{target}へ関係があります。"
    )
    expanded = deepcopy(catalog)
    expanded["resource_bounds"][
        "visible_clauses_per_grammatical_sentence_max"
    ] = 3
    alternatives = deepcopy(catalog)
    alternatives["realization_alternatives_per_semantic_key"] = 2
    hidden = deepcopy(catalog)
    first_construction = next(iter(hidden["construction_predicate_fragments"]))
    hidden["construction_predicate_fragments"][first_construction] += "\u200b"
    standalone = deepcopy(catalog)
    standalone["clause_morphology"][
        "construction_standalone_predicate"
    ] = "が存在します"
    _closed_assert(
        all(
            validate_step11_rc0031_experiment_surface_catalog(value)
            for value in (
                completed,
                expanded,
                alternatives,
                hidden,
                standalone,
            )
        ),
        "STEP11_RC0031_P2_CATALOG_MUTATION_ACCEPTED",
    )


@pytest.mark.parametrize("case_id", _DIRECT_CASE_IDS)
def test_rc0031_p2_forward_root_relation_and_distribution_are_exact(
    case_id: str,
) -> None:
    _baseline, successor, lexical_specs, candidates = _direct_candidates(case_id)
    for candidate in candidates:
        _assert_candidate(candidate, successor, lexical_specs)
        if case_id in _DISTRIBUTED_CASE_IDS:
            _closed_assert(
                len(
                    {
                        row.sentence_group_ordinal
                        for row in (
                            candidate.surface_realization_plan
                            .proposition_clause_bindings
                        )
                    }
                )
                >= 2,
                "STEP11_RC0031_P2_PROPOSITION_DISTRIBUTION_NOT_PROVED",
            )


@pytest.mark.parametrize("case_id", _SUPPORT_CASE_IDS)
def test_rc0031_p2_support_positive_source_binding_is_exact(case_id: str) -> None:
    _baseline, successor, lexical_specs, candidates = _support_candidates(case_id)
    semantic_count, reception_count, support_count = _SUPPORT_DENOMINATOR[
        case_id
    ]
    for candidate in candidates:
        _assert_candidate(candidate, successor, lexical_specs)
        _closed_assert(
            len(_atom_records(candidate)) == semantic_count
            and len(candidate.reception_bindings) == reception_count
            and sum(
                bool(row.supporting_source_owner_ids)
                for row in candidate.reception_bindings
            )
            == support_count,
            "STEP11_RC0031_P2_SUPPORT_DENOMINATOR_INVALID",
        )


def test_rc0031_p2_candidate_self_claim_and_resource_mutations_fail_closed() -> None:
    from emlis_ai_step11_natural_surface_v3 import (
        validate_step11_rc0031_experiment_surface_candidate,
    )

    _baseline, successor, lexical_specs, candidates = _direct_candidates(
        "nls3s_b001_0001"
    )
    clean = candidates[0]

    class ExplosiveEquality:
        def __eq__(self, _other: Any) -> bool:
            raise RuntimeError("must be normalized by the candidate validator")

    class AlwaysEqual:
        def __eq__(self, _other: Any) -> bool:
            return True

    mutations = (
        (
            replace(clean, semantic_coverage_authorized=True),
            "STEP11_RC0031_SEMANTIC_COVERAGE_SELF_CLAIM",
        ),
        (
            replace(clean, replan_count=2),
            "STEP11_RC0031_REPLAN_BOUND_EXCEEDED",
        ),
        (
            replace(clean, runtime_connected=True),
            "STEP11_RC0031_RUNTIME_BOUNDARY_INVALID",
        ),
        (
            replace(
                clean,
                rendered_surface=replace(clean.rendered_surface, sha256="0" * 64),
            ),
            "STEP11_RC0031_CANONICAL_RENDER_MISMATCH",
        ),
        (
            replace(clean, rendered_surface=None),
            "STEP11_RC0031_CANONICAL_RENDER_MISMATCH",
        ),
        (
            replace(clean, proposition_surface_ast=None),
            "STEP11_RC0031_CANONICAL_RENDER_MISMATCH",
        ),
        (
            replace(clean, owner_registry=(ExplosiveEquality(),)),
            "STEP11_RC0031_CANDIDATE_REVALIDATION_FAILED",
        ),
        (
            replace(clean, candidate_id=AlwaysEqual()),
            "STEP11_RC0031_CANDIDATE_SOURCE_MISMATCH",
        ),
        (
            replace(
                clean,
                surface_realization_plan=replace(
                    clean.surface_realization_plan,
                    root_proposition_binding=replace(
                        clean.surface_realization_plan.root_proposition_binding,
                        predicate_grounding_basis=AlwaysEqual(),
                    ),
                ),
            ),
            "STEP11_RC0031_CANONICAL_RENDER_MISMATCH",
        ),
    )
    for mutated, expected_code in mutations:
        issues = validate_step11_rc0031_experiment_surface_candidate(
            mutated,
            successor_snapshot=successor,
            lexical_atom_specs=lexical_specs,
        )
        _closed_assert(
            expected_code in issues,
            "STEP11_RC0031_P2_CANDIDATE_MUTATION_ACCEPTED",
        )


def test_rc0031_p2_same_ast_canonical_inputs_are_committed() -> None:
    from emlis_ai_step11_natural_surface_v3 import (
        Step11NaturalSurfaceError,
        render_step11_rc0031_experiment_surface,
    )

    _baseline, successor, lexical_specs, candidates = _direct_candidates(
        "nls3s_b001_0001"
    )
    clean = candidates[0]

    class ExplosiveIterable:
        def __iter__(self) -> Any:
            raise RuntimeError("must be normalized by the renderer boundary")

    render_kwargs = {
        "successor_snapshot": successor,
        "lexical_atom_specs": lexical_specs,
        "clause_ready_lexical_specs": clean.natural_handle_specs,
        "proposition_surface_ast": clean.proposition_surface_ast,
        "surface_realization_plan": clean.surface_realization_plan,
        "construction_atoms": clean.construction_atoms,
        "relation_atoms": clean.relation_atoms,
        "semantic_link_atoms": clean.semantic_link_atoms,
        "explicit_unknown_atoms": clean.explicit_unknown_atoms,
        "reception_predications": clean.reception_bindings,
    }
    first = render_step11_rc0031_experiment_surface(
        clean.base_candidate, **render_kwargs
    )
    second = render_step11_rc0031_experiment_surface(
        clean.base_candidate, **render_kwargs
    )
    _closed_assert(
        first == second == clean.rendered_surface,
        "STEP11_RC0031_P2_CANONICAL_RERENDER_MISMATCH",
    )

    lexeme = clean.natural_handle_specs.lexemes[0]
    replacement = "甲" if not lexeme.referent_text.startswith("甲") else "乙"
    mutated_lexeme = replace(
        lexeme,
        referent_text=replacement + lexeme.referent_text[1:],
    )
    mutated_specs = replace(
        clean.natural_handle_specs,
        lexemes=(mutated_lexeme, *clean.natural_handle_specs.lexemes[1:]),
    )
    with pytest.raises(Step11NaturalSurfaceError) as caught:
        render_step11_rc0031_experiment_surface(
            clean.base_candidate,
            **{
                **render_kwargs,
                "clause_ready_lexical_specs": mutated_specs,
            },
        )
    _closed_assert(
        caught.value.code
        == "STEP11_RC0031_RENDER_LEXICAL_AUTHORITY_MISMATCH",
        "STEP11_RC0031_P2_MUTATED_LEXICAL_RENDER_ACCEPTED",
    )

    mutated_body = clean.base_candidate.final_utf8_bytes.replace(
        "見えたこと".encode("utf-8"),
        "見えた事実".encode("utf-8"),
        1,
    )
    mutated_base = replace(
        clean.base_candidate,
        rendered_surface=replace(
            clean.base_candidate.rendered_surface,
            utf8_bytes=mutated_body,
            sha256=hashlib.sha256(mutated_body).hexdigest(),
        ),
    )
    with pytest.raises(Step11NaturalSurfaceError) as caught:
        render_step11_rc0031_experiment_surface(
            mutated_base, **render_kwargs
        )
    _closed_assert(
        caught.value.code
        == "STEP11_RC0031_BASE_CANDIDATE_COMMITMENT_INVALID",
        "STEP11_RC0031_P2_MUTATED_BASE_RENDER_ACCEPTED",
    )
    malformed_base = replace(clean.base_candidate, surface_ast=None)
    with pytest.raises(Step11NaturalSurfaceError) as caught:
        render_step11_rc0031_experiment_surface(
            malformed_base, **render_kwargs
        )
    _closed_assert(
        caught.value.code
        == "STEP11_RC0031_BASE_CANDIDATE_COMMITMENT_INVALID",
        "STEP11_RC0031_P2_MALFORMED_BASE_ERROR_LEAKED",
    )
    malformed_bytes = replace(
        clean.base_candidate,
        rendered_surface=replace(
            clean.base_candidate.rendered_surface,
            utf8_bytes=None,
        ),
    )
    with pytest.raises(Step11NaturalSurfaceError) as caught:
        render_step11_rc0031_experiment_surface(
            malformed_bytes, **render_kwargs
        )
    _closed_assert(
        caught.value.code
        == "STEP11_RC0031_BASE_CANDIDATE_COMMITMENT_INVALID",
        "STEP11_RC0031_P2_MALFORMED_BASE_BYTES_ERROR_LEAKED",
    )
    with pytest.raises(Step11NaturalSurfaceError) as caught:
        render_step11_rc0031_experiment_surface(
            clean.base_candidate,
            **{
                **render_kwargs,
                "construction_atoms": ExplosiveIterable(),
            },
        )
    _closed_assert(
        caught.value.code == "STEP11_RC0031_RENDER_INPUT_INVALID",
        "STEP11_RC0031_P2_RENDER_INPUT_ERROR_LEAKED",
    )


def test_rc0031_p2_plan_ast_root_mismatch_fails_closed() -> None:
    from emlis_ai_step11_natural_surface_v3 import (
        Step11NaturalSurfaceError,
        render_step11_rc0031_experiment_surface,
    )

    _baseline, successor, lexical_specs, candidates = _direct_candidates(
        "nls3s_b001_0001"
    )
    clean = candidates[0]
    mutated_ast = replace(
        clean.proposition_surface_ast,
        root_proposition_binding=replace(
            clean.proposition_surface_ast.root_proposition_binding,
            source_order=(
                clean.proposition_surface_ast.root_proposition_binding.source_order
                + 1
            ),
        ),
    )
    with pytest.raises(Step11NaturalSurfaceError) as caught:
        render_step11_rc0031_experiment_surface(
            clean.base_candidate,
            successor_snapshot=successor,
            lexical_atom_specs=lexical_specs,
            clause_ready_lexical_specs=clean.natural_handle_specs,
            proposition_surface_ast=mutated_ast,
            surface_realization_plan=clean.surface_realization_plan,
            construction_atoms=clean.construction_atoms,
            relation_atoms=clean.relation_atoms,
            semantic_link_atoms=clean.semantic_link_atoms,
            explicit_unknown_atoms=clean.explicit_unknown_atoms,
            reception_predications=clean.reception_bindings,
        )
    _closed_assert(
        caught.value.code == "STEP11_RC0031_AST_PLAN_MISMATCH",
        "STEP11_RC0031_P2_AST_PLAN_MISMATCH_ACCEPTED",
    )


def test_rc0031_p2_same_ast_rejects_relation_authority_mutation() -> None:
    from emlis_ai_step11_natural_surface_v3 import (
        Step11NaturalSurfaceError,
        render_step11_rc0031_experiment_surface,
    )
    from emlis_ai_step11_rc0031_experiment_surface_catalog_v3 import (
        STEP11_RC0031_EXPERIMENT_SURFACE_CATALOG as catalog,
    )

    _baseline, successor, lexical_specs, candidates = _direct_candidates(
        "nls3s_b001_0035"
    )
    clean = next(candidate for candidate in candidates if candidate.relation_atoms)
    relation = clean.relation_atoms[0]
    relation_types = tuple(
        key.rsplit(":", 1)[0]
        for key in catalog["relation_predicate_fragments"]
        if key.endswith(":" + relation.direction)
        and not key.startswith(relation.effective_relation_type + ":")
    )
    _closed_assert(
        bool(relation_types)
        and relation.from_owner_ordinal != relation.to_owner_ordinal,
        "STEP11_RC0031_P2_RELATION_MUTATION_AUTHORITY_INVALID",
    )
    mutations = (
        replace(relation, effective_relation_type=relation_types[0]),
        replace(
            relation,
            direction=(
                "bidirectional"
                if relation.direction == "source_to_target"
                else "source_to_target"
            ),
        ),
        replace(
            relation,
            from_owner_ordinal=relation.to_owner_ordinal,
            to_owner_ordinal=relation.from_owner_ordinal,
        ),
    )
    relation_index = clean.relation_atoms.index(relation)
    for mutation in mutations:
        mutated_relations = tuple(
            mutation if index == relation_index else row
            for index, row in enumerate(clean.relation_atoms)
        )
        with pytest.raises(Step11NaturalSurfaceError) as caught:
            render_step11_rc0031_experiment_surface(
                clean.base_candidate,
                successor_snapshot=successor,
                lexical_atom_specs=lexical_specs,
                clause_ready_lexical_specs=clean.natural_handle_specs,
                proposition_surface_ast=clean.proposition_surface_ast,
                surface_realization_plan=clean.surface_realization_plan,
                construction_atoms=clean.construction_atoms,
                relation_atoms=mutated_relations,
                semantic_link_atoms=clean.semantic_link_atoms,
                explicit_unknown_atoms=clean.explicit_unknown_atoms,
                reception_predications=clean.reception_bindings,
            )
        _closed_assert(
            caught.value.code
            == "STEP11_RC0031_RENDER_SOURCE_ATOM_MISMATCH",
            "STEP11_RC0031_P2_SAME_AST_RELATION_MUTATION_ACCEPTED",
        )


def test_rc0031_p2_same_ast_rejects_semantic_link_authority_mutation() -> None:
    from emlis_ai_step11_natural_surface_v3 import (
        Step11NaturalSurfaceError,
        render_step11_rc0031_experiment_surface,
    )
    from emlis_ai_step11_rc0031_experiment_surface_catalog_v3 import (
        STEP11_RC0031_EXPERIMENT_SURFACE_CATALOG as catalog,
    )

    _baseline, successor, lexical_specs, candidates = _direct_candidates(
        "nls3s_b001_0009"
    )
    clean = next(
        candidate for candidate in candidates if candidate.semantic_link_atoms
    )
    link = clean.semantic_link_atoms[0]
    link_types = tuple(
        key.rsplit(":", 1)[0]
        for key in catalog["semantic_link_predicate_fragments"]
        if key.endswith(":" + link.direction)
        and not key.startswith(link.relation_type + ":")
    )
    _closed_assert(
        bool(link_types) and link.from_owner_ordinal != link.to_owner_ordinal,
        "STEP11_RC0031_P2_LINK_MUTATION_AUTHORITY_INVALID",
    )
    link_index = clean.semantic_link_atoms.index(link)
    mutations = (
        replace(link, relation_type=link_types[0]),
        replace(
            link,
            direction=(
                "bidirectional"
                if link.direction == "source_to_target"
                else "source_to_target"
            ),
        ),
        replace(
            link,
            from_owner_ordinal=link.to_owner_ordinal,
            to_owner_ordinal=link.from_owner_ordinal,
        ),
    )
    for mutation in mutations:
        mutated_links = tuple(
            mutation if index == link_index else row
            for index, row in enumerate(clean.semantic_link_atoms)
        )
        with pytest.raises(Step11NaturalSurfaceError) as caught:
            render_step11_rc0031_experiment_surface(
                clean.base_candidate,
                successor_snapshot=successor,
                lexical_atom_specs=lexical_specs,
                clause_ready_lexical_specs=clean.natural_handle_specs,
                proposition_surface_ast=clean.proposition_surface_ast,
                surface_realization_plan=clean.surface_realization_plan,
                construction_atoms=clean.construction_atoms,
                relation_atoms=clean.relation_atoms,
                semantic_link_atoms=mutated_links,
                explicit_unknown_atoms=clean.explicit_unknown_atoms,
                reception_predications=clean.reception_bindings,
            )
        _closed_assert(
            caught.value.code
            == "STEP11_RC0031_RENDER_SOURCE_ATOM_MISMATCH",
            "STEP11_RC0031_P2_SAME_AST_LINK_MUTATION_ACCEPTED",
        )


def test_rc0031_p2_unverified_exact_reuse_mutations_fail_closed() -> None:
    from emlis_ai_step11_natural_surface_v3 import (
        Step11NaturalSurfaceError,
        Step11Rc0031BaseBodyExactReuseBinding,
        __all__ as surface_exports,
        _step11_rc0031_exact_reuse_material,
        _step11_rc0031_validate_verified_reuse_composition,
        build_step11_rc0031_experiment_surface_candidate,
    )

    _closed_assert(
        not {
            "_step11_rc0031_build_plan_from_verified_reuse_composition",
            "_step11_rc0031_build_candidate_from_verified_reuse_composition",
            "_step11_rc0031_render_from_verified_reuse_composition",
            "_step11_rc0031_validate_candidate_from_verified_reuse_composition",
            "_step11_rc0031_validate_verified_reuse_composition",
        }
        & set(surface_exports),
        "STEP11_RC0031_P2_VERIFIED_REUSE_SEAM_EXPORTED",
    )

    _baseline, successor, lexical_specs, candidates = _direct_candidates(
        "nls3s_b001_0001"
    )
    clean = candidates[0]
    atom_id, (family, _ordinals, _direction, _semantic_key) = next(
        iter(_atom_records(clean).items())
    )
    valid_shape = Step11Rc0031BaseBodyExactReuseBinding(
        source_atom_id=atom_id,
        semantic_family=family,
        base_parsed_atom_id="nls3s11atom_0123456789abcdef",
        base_obligation_id="obl_0123456789abcdef",
        match_basis=_EXACT_MATCH_BASIS[family],
        base_surface_sha256=hashlib.sha256(
            clean.base_candidate.final_utf8_bytes
        ).hexdigest(),
        source_authority_sha256=(
            successor.relation_construction_authority.authority_sha256
        ),
        independent_binding_sha256="1" * 64,
    )
    private_material = _step11_rc0031_exact_reuse_material(valid_shape)
    _closed_assert(
        "base_surface_sha256" not in private_material
        and valid_shape.base_surface_sha256 not in repr(valid_shape),
        "STEP11_RC0031_P2_UNSALTED_BODY_DIGEST_EXPOSED",
    )
    with pytest.raises(Step11NaturalSurfaceError) as caught:
        _step11_rc0031_validate_verified_reuse_composition(
            (replace(valid_shape, source_atom_id=[]),),
            records=(),
            base_candidate=clean.base_candidate,
            successor_snapshot=successor,
        )
    _closed_assert(
        caught.value.code
        == "STEP11_RC0031_VERIFIED_REUSE_COMPOSITION_INVALID",
        "STEP11_RC0031_P2_VERIFIED_REUSE_ENVELOPE_ERROR_LEAKED",
    )
    with pytest.raises(Step11NaturalSurfaceError) as caught:
        _step11_rc0031_validate_verified_reuse_composition(
            (valid_shape,),
            records=(),
            base_candidate=clean.base_candidate,
            successor_snapshot=successor,
        )
    _closed_assert(
        caught.value.code == "STEP11_RC0031_P3_EXACT_REUSE_NOT_AVAILABLE",
        "STEP11_RC0031_P2_PRIVATE_UNGROUNDED_REUSE_ACCEPTED",
    )
    mutations = (
        replace(valid_shape, base_parsed_atom_id=""),
        replace(valid_shape, match_basis="lexical_only"),
        replace(valid_shape, semantic_family="relation"),
        replace(valid_shape, base_surface_sha256="0" * 64),
        replace(valid_shape, source_authority_sha256="0" * 64),
        replace(valid_shape, independent_binding_sha256="0" * 64),
    )
    for mutation in mutations:
        with pytest.raises(Step11NaturalSurfaceError) as caught:
            build_step11_rc0031_experiment_surface_candidate(
                clean.base_candidate,
                successor_snapshot=successor,
                lexical_atom_specs=lexical_specs,
                base_body_exact_reuse_bindings=(mutation,),
            )
        _closed_assert(
            caught.value.code
            == "STEP11_RC0031_P3_EXACT_REUSE_NOT_AVAILABLE",
            "STEP11_RC0031_P2_UNVERIFIED_REUSE_ACCEPTED",
        )


@pytest.mark.parametrize("case_id", _SUPPORT_CASE_IDS)
def test_rc0031_p2_support_omission_fails_source_revalidation(
    case_id: str,
) -> None:
    from emlis_ai_step11_natural_surface_v3 import (
        Step11NaturalSurfaceError,
        build_step11_rc0031_surface_realization_plan,
        validate_step11_rc0031_experiment_surface_candidate,
    )

    _baseline, successor, lexical_specs, candidates = _support_candidates(case_id)
    clean = candidates[0]
    supported = next(
        row
        for row in clean.reception_bindings
        if row.supporting_source_owner_ids
    )
    omitted = replace(supported, supporting_source_owner_ids=())
    mutated = tuple(
        omitted
        if row.source_reception_opportunity_id
        == supported.source_reception_opportunity_id
        else row
        for row in clean.reception_bindings
    )
    with pytest.raises(Step11NaturalSurfaceError) as caught:
        build_step11_rc0031_surface_realization_plan(
            clean.base_candidate,
            successor_snapshot=successor,
            lexical_atom_specs=lexical_specs,
            clause_ready_lexical_specs=clean.natural_handle_specs,
            construction_atoms=clean.construction_atoms,
            relation_atoms=clean.relation_atoms,
            semantic_link_atoms=clean.semantic_link_atoms,
            explicit_unknown_atoms=clean.explicit_unknown_atoms,
            reception_predications=mutated,
        )
    _closed_assert(
        caught.value.code == "STEP11_RC0031_RECEPTION_SOURCE_BINDING_INVALID",
        "STEP11_RC0031_P2_SUPPORT_OMISSION_ACCEPTED",
    )
    mutated_candidate = replace(
        clean,
        reception_bindings=mutated,
        surface_realization_plan=replace(
            clean.surface_realization_plan,
            reception_predication_bindings=mutated,
        ),
        proposition_surface_ast=replace(
            clean.proposition_surface_ast,
            reception_predication_bindings=mutated,
        ),
    )
    _closed_assert(
        bool(
            validate_step11_rc0031_experiment_surface_candidate(
                mutated_candidate,
                successor_snapshot=successor,
                lexical_atom_specs=lexical_specs,
            )
        ),
        "STEP11_RC0031_P2_SUPPORT_OMISSION_REVALIDATED",
    )


def test_rc0031_p2_candidate_and_replan_bounds_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from emlis_ai_step11_natural_surface_v3 import (
        Step11NaturalSurfaceError,
        build_step11_rc0031_experiment_surface_candidate,
        build_step11_rc0031_experiment_surface_candidates,
        build_step11_rc0031_surface_realization_plan,
    )

    baseline, successor, lexical_specs, candidates = _direct_candidates(
        "nls3s_b001_0001"
    )
    base = baseline.natural_candidates[0]
    with pytest.raises(Step11NaturalSurfaceError) as caught:
        build_step11_rc0031_experiment_surface_candidates(
            (base,) * 13,
            successor_snapshot=successor,
            lexical_atom_specs=lexical_specs,
        )
    _closed_assert(
        caught.value.code == "STEP11_RC0031_CANDIDATE_BOUND_INVALID",
        "STEP11_RC0031_P2_CANDIDATE_BOUND_EXPANDED",
    )
    clean = candidates[0]
    expanded_base = replace(
        clean.base_candidate,
        surface_ast=replace(
            clean.base_candidate.surface_ast,
            surface_realization_plan=replace(
                clean.base_candidate.surface_ast.surface_realization_plan,
                maximum_observation_clauses_per_sentence=5,
            ),
        ),
    )
    with pytest.raises(Step11NaturalSurfaceError) as caught:
        build_step11_rc0031_surface_realization_plan(
            expanded_base,
            successor_snapshot=successor,
            lexical_atom_specs=lexical_specs,
            clause_ready_lexical_specs=clean.natural_handle_specs,
            construction_atoms=clean.construction_atoms,
            relation_atoms=clean.relation_atoms,
            semantic_link_atoms=clean.semantic_link_atoms,
            explicit_unknown_atoms=clean.explicit_unknown_atoms,
            reception_predications=clean.reception_bindings,
        )
    _closed_assert(
        caught.value.code == "STEP11_RC0031_RESOURCE_CONTRACT_MISMATCH",
        "STEP11_RC0031_P2_GROUP_UNIT_BOUND_EXPANDED",
    )
    malformed_clause_ready = replace(
        clean.natural_handle_specs,
        lexemes=(object(),),
    )
    with pytest.raises(Step11NaturalSurfaceError) as caught:
        build_step11_rc0031_surface_realization_plan(
            clean.base_candidate,
            successor_snapshot=successor,
            lexical_atom_specs=lexical_specs,
            clause_ready_lexical_specs=malformed_clause_ready,
            construction_atoms=clean.construction_atoms,
            relation_atoms=clean.relation_atoms,
            semantic_link_atoms=clean.semantic_link_atoms,
            explicit_unknown_atoms=clean.explicit_unknown_atoms,
            reception_predications=clean.reception_bindings,
        )
    _closed_assert(
        caught.value.code == "STEP11_RC0031_PLAN_INPUT_INVALID",
        "STEP11_RC0031_P2_PLAN_INPUT_ERROR_LEAKED",
    )
    with pytest.raises(Step11NaturalSurfaceError) as caught:
        build_step11_rc0031_experiment_surface_candidate(
            clean.base_candidate,
            successor_snapshot=successor,
            lexical_atom_specs=object(),
        )
    _closed_assert(
        caught.value.code == "STEP11_RC0031_CANDIDATE_INPUT_INVALID",
        "STEP11_RC0031_P2_CANDIDATE_INPUT_ERROR_LEAKED",
    )
    import emlis_ai_step11_natural_surface_v3 as surface

    def raise_unknown(*_args: Any, **_kwargs: Any) -> Any:
        raise surface.Step11NaturalSurfaceError(
            "STEP11_RC0031_CALLER_CONTROLLED_UNKNOWN"
        )

    with monkeypatch.context() as context:
        context.setattr(
            surface,
            "_step11_rc0031_build_candidate_from_verified_reuse_composition",
            raise_unknown,
        )
        with pytest.raises(surface.Step11NaturalSurfaceError) as caught:
            surface.build_step11_rc0031_experiment_surface_candidate(
                clean.base_candidate,
                successor_snapshot=successor,
                lexical_atom_specs=lexical_specs,
            )
        _closed_assert(
            caught.value.code == "STEP11_RC0031_CANDIDATE_INPUT_INVALID",
            "STEP11_RC0031_P2_CANDIDATE_UNKNOWN_CODE_LEAKED",
        )

    with monkeypatch.context() as context:
        context.setattr(
            surface,
            "_step11_rc0031_render_from_verified_reuse_composition",
            raise_unknown,
        )
        with pytest.raises(surface.Step11NaturalSurfaceError) as caught:
            surface.render_step11_rc0031_experiment_surface(
                clean.base_candidate,
                successor_snapshot=successor,
                lexical_atom_specs=lexical_specs,
                clause_ready_lexical_specs=clean.natural_handle_specs,
                proposition_surface_ast=clean.proposition_surface_ast,
                surface_realization_plan=clean.surface_realization_plan,
                construction_atoms=clean.construction_atoms,
                relation_atoms=clean.relation_atoms,
                semantic_link_atoms=clean.semantic_link_atoms,
                explicit_unknown_atoms=clean.explicit_unknown_atoms,
                reception_predications=clean.reception_bindings,
            )
        _closed_assert(
            caught.value.code == "STEP11_RC0031_RENDER_INPUT_INVALID",
            "STEP11_RC0031_P2_RENDER_UNKNOWN_CODE_LEAKED",
        )

    with monkeypatch.context() as context:
        context.setattr(
            surface,
            "_step11_rc0031_build_plan_from_verified_reuse_composition",
            raise_unknown,
        )
        with pytest.raises(surface.Step11NaturalSurfaceError) as caught:
            surface.build_step11_rc0031_surface_realization_plan(
                clean.base_candidate,
                successor_snapshot=successor,
                lexical_atom_specs=lexical_specs,
                clause_ready_lexical_specs=clean.natural_handle_specs,
                construction_atoms=clean.construction_atoms,
                relation_atoms=clean.relation_atoms,
                semantic_link_atoms=clean.semantic_link_atoms,
                explicit_unknown_atoms=clean.explicit_unknown_atoms,
                reception_predications=clean.reception_bindings,
            )
        _closed_assert(
            caught.value.code == "STEP11_RC0031_PLAN_INPUT_INVALID",
            "STEP11_RC0031_P2_PLAN_UNKNOWN_CODE_LEAKED",
        )


def test_rc0031_p2_reception_five_owner_complexity_fails_closed() -> None:
    from emlis_ai_step11_natural_surface_v3 import (
        Step11NaturalSurfaceError,
        _step11_rc0031_clause_ready_projection,
        _step11_rc0031_reception_predications,
    )
    from emlis_ai_step11_rc0031_experiment_surface_catalog_v3 import (
        STEP11_RC0031_EXPERIMENT_SURFACE_CATALOG as catalog,
    )

    baseline, successor, lexical_specs = _forward_authority(
        "nls3s_b001_0063"
    )
    base_candidate = baseline.natural_candidates[0]
    clause_ready = _step11_rc0031_clause_ready_projection(
        base_candidate,
        successor_snapshot=successor,
        lexical_atom_specs=lexical_specs,
    )
    known_actual_ids = {
        str(row.source_owner_id)
        for row in clause_ready.lexemes
    }
    source_ids = tuple(
        str(row.source_id)
        for row in successor.base_snapshot.nuclei
        if str(row.actual_source_id) in known_actual_ids
    )
    _closed_assert(
        len(source_ids) >= 5 and len(set(source_ids[:5])) == 5,
        "STEP11_RC0031_P2_RECEPTION_COMPLEXITY_MUTATION_INVALID",
    )
    opportunity = next(
        row
        for row in successor.base_snapshot.reception_opportunities
        if row.retention == "required" or row.safety_required is True
    )
    mutated_opportunity = replace(
        opportunity,
        target_nucleus_ids=(source_ids[0],),
        support_nucleus_ids=source_ids[1:5],
    )
    mutated_base_snapshot = replace(
        successor.base_snapshot,
        reception_opportunities=tuple(
            mutated_opportunity
            if row.source_id == opportunity.source_id
            else row
            for row in successor.base_snapshot.reception_opportunities
        ),
    )
    mutated_successor = replace(
        successor,
        base_snapshot=mutated_base_snapshot,
    )
    with pytest.raises(Step11NaturalSurfaceError) as caught:
        _step11_rc0031_reception_predications(
            base_candidate,
            successor_snapshot=mutated_successor,
            lexemes=clause_ready.lexemes,
            catalog=catalog,
        )
    _closed_assert(
        caught.value.code
        == "STEP11_RC0031_RECEPTION_COMPLEXITY_BOUND_EXCEEDED",
        "STEP11_RC0031_P2_RECEPTION_COMPLEXITY_EXPANSION_ACCEPTED",
    )


def test_rc0031_p2_reception_three_moves_on_one_line_fails_closed() -> None:
    from emlis_ai_step11_natural_surface_v3 import (
        Step11NaturalSurfaceError,
        _step11_rc0031_reception_predications,
    )
    from emlis_ai_step11_rc0031_experiment_surface_catalog_v3 import (
        STEP11_RC0031_EXPERIMENT_SURFACE_CATALOG as catalog,
    )

    _baseline, successor, _lexical_specs, candidates = _support_candidates(
        "I6-D02"
    )
    clean = candidates[0]
    opportunities = tuple(
        row
        for row in successor.base_snapshot.reception_opportunities
        if row.retention == "required" or row.safety_required is True
    )
    base_bindings = tuple(
        clean.base_candidate.surface_ast.reception_antecedent_bindings
    )
    _closed_assert(
        len(opportunities) == 3 and bool(base_bindings),
        "STEP11_RC0031_P2_RECEPTION_DENSITY_MUTATION_INVALID",
    )
    first_binding = replace(
        base_bindings[0],
        source_reception_opportunity_ids=tuple(
            str(row.source_id) for row in opportunities
        ),
        allowed_response_acts=tuple(
            dict.fromkeys(str(row.reception_act) for row in opportunities)
        ),
    )
    mutated_base = replace(
        clean.base_candidate,
        surface_ast=replace(
            clean.base_candidate.surface_ast,
            reception_antecedent_bindings=(first_binding,),
        ),
    )
    with pytest.raises(Step11NaturalSurfaceError) as caught:
        _step11_rc0031_reception_predications(
            mutated_base,
            successor_snapshot=successor,
            lexemes=clean.natural_handle_specs.lexemes,
            catalog=catalog,
        )
    _closed_assert(
        caught.value.code
        == "STEP11_RC0031_RECEPTION_DENSITY_UNSATISFIABLE",
        "STEP11_RC0031_P2_RECEPTION_LINE_DENSITY_EXPANSION_ACCEPTED",
    )


def test_rc0031_p2_density_case_uses_owner_connected_composition() -> None:
    from emlis_ai_step11_natural_surface_v3 import (
        _step11_rc0031_composition_units,
        build_step11_rc0031_experiment_surface_candidates,
        validate_step11_rc0031_experiment_surface_candidate,
    )

    prospective_five_owner_rows = (
        (
            "synthetic_unknown",
            "explicit_unknown",
            ("owner_1", "owner_2", "owner_3", "owner_4"),
            ("nucleus_1", "nucleus_2", "nucleus_3", "nucleus_4"),
            (1, 1, 1, 1),
            1,
            1,
            False,
            "",
            "explicit_cause_unknown",
            1,
        ),
        (
            "synthetic_relation",
            "relation",
            ("owner_4", "owner_5"),
            ("nucleus_4", "nucleus_5"),
            (1, 1),
            1,
            1,
            False,
            "source_to_target",
            "contrast",
            2,
        ),
    )
    guarded_units = _step11_rc0031_composition_units(
        prospective_five_owner_rows,
        maximum_complexity_load=4,
    )
    _closed_assert(
        len(guarded_units) == 2
        and all(len(unit[4]) == 1 for unit in guarded_units),
        "STEP11_RC0031_P2_COMMON_COMPLEXITY_PARTITION_INVALID",
    )

    baseline, successor, lexical_specs = _forward_authority(
        "nls3s_b001_0063"
    )
    _closed_assert(
        len(baseline.natural_candidates) == 2,
        "STEP11_RC0031_P2_DENSITY_DENOMINATOR_INVALID",
    )
    candidates = build_step11_rc0031_experiment_surface_candidates(
        tuple(baseline.natural_candidates),
        successor_snapshot=successor,
        lexical_atom_specs=lexical_specs,
    )
    _closed_assert(
        len(candidates) == 1
        and all(
            candidate.base_candidate in baseline.natural_candidates
            for candidate in candidates
        ),
        "STEP11_RC0031_P2_0063_PUBLIC_CANDIDATE_MISSING",
    )

    composition_witnesses: list[tuple[Any, Any]] = []
    for candidate in candidates:
        atoms = _atom_records(candidate)
        raw_atom_count = (
            len(candidate.construction_atoms)
            + len(candidate.relation_atoms)
            + len(candidate.semantic_link_atoms)
            + len(candidate.explicit_unknown_atoms)
        )
        family_counts = Counter(row[0] for row in atoms.values())
        _closed_assert(
            raw_atom_count == len(atoms) == 10
            and family_counts
            == Counter({"construction": 6, "relation": 4})
            and len(candidate.reception_bindings) == 1
            and len(
                tuple(
                    row
                    for row in successor.base_snapshot.reception_opportunities
                    if row.retention == "required"
                    or row.safety_required is True
                )
            )
            == 1,
            "STEP11_RC0031_P2_0063_S10_R1_DENOMINATOR_INVALID",
        )
        plan = candidate.surface_realization_plan
        realized = tuple(
            atom_id
            for binding in plan.proposition_clause_bindings
            for atom_id in binding.source_atom_ids
        )
        assigned = tuple(
            atom_id
            for assignment in plan.proposition_chunk_assignments
            for atom_id in assignment.source_atom_ids
        )
        _closed_assert(
            not plan.base_body_exact_reuse_bindings
            and candidate.rendered_surface.exact_reuse_count == 0
            and candidate.rendered_surface.semantic_atom_count == 10
            and Counter(realized) == Counter(atoms.keys())
            and all(count == 1 for count in Counter(realized).values())
            and Counter(assigned) == Counter(realized),
            "STEP11_RC0031_P2_0063_ATOM_EXACTLY_ONCE_INVALID",
        )

        lexeme_by_ordinal = {
            int(row.source_owner_ordinal): row
            for row in candidate.natural_handle_specs.lexemes
        }
        for binding in plan.proposition_clause_bindings:
            _assert_typed_composition_binding(
                binding,
                atoms,
                lexeme_by_ordinal,
                code=(
                    "STEP11_RC0031_P2_0063_"
                    "OWNER_CONNECTED_COMPOSITION_INVALID"
                ),
            )
            if binding.composition_mode == "construction_modified_head":
                composition_witnesses.append((candidate, binding))
        expected_witness = {
            (
                "successor_construction:i768b2ca12fb3cd2458d03810",
                "successor_relation:rdbfe4ba7da4a50a9ae822870",
            ): ("construction_modified_head", 1, 1),
            (
                "successor_construction:i0bc8083a4fa79e01aa026a00",
                "successor_relation:r1d0d95f11ed5f4aa30da3fe0",
            ): ("construction_modified_head", 1, 1),
            (
                "successor_construction:ibe702c737e4c6a015e0f0de7",
                "successor_relation:re94ecbc9a38921fc8d31b707",
            ): ("construction_modified_head", 2, 1),
            (
                "successor_construction:i5ed7e9751737670368f2f508",
                "successor_construction:i2b256c1bf148b36d8c9cb0be",
                "successor_relation:red5e7781a6a2b8210a889baf",
            ): ("construction_modified_head", 3, 1),
            (
                "successor_construction:i84da601f4fc6a0bbf50a79be",
            ): ("independent_clauses", 3, 1),
        }
        actual_witness = {
            binding.source_atom_ids: (
                binding.composition_mode,
                binding.sentence_group_ordinal,
                binding.visible_clause_count,
            )
            for binding in plan.proposition_clause_bindings
        }
        _closed_assert(
            actual_witness == expected_witness,
            "STEP11_RC0031_P2_0063_EXACT_FIVE_UNIT_WITNESS_INVALID",
        )

        base_plan = candidate.base_candidate.surface_ast.surface_realization_plan
        group_index = {
            group_id: ordinal
            for ordinal, group_id in enumerate(
                base_plan.observation_sentence_group_ids, start=1
            )
        }
        base_by_chunk: dict[tuple[int, int], list[Any]] = {}
        for unit in base_plan.units:
            if unit.section_role != "observation":
                continue
            key = (
                group_index[unit.assigned_sentence_group_id],
                int(unit.assigned_grammatical_chunk_ordinal),
            )
            base_by_chunk.setdefault(key, []).append(unit)
        props_by_chunk: dict[tuple[int, int], list[Any]] = {}
        for binding in plan.proposition_clause_bindings:
            key = (
                binding.sentence_group_ordinal,
                binding.grammatical_chunk_ordinal,
            )
            props_by_chunk.setdefault(key, []).append(binding)
        assignments = {
            (row.sentence_group_ordinal, row.grammatical_chunk_ordinal): row
            for row in plan.proposition_chunk_assignments
        }
        _closed_assert(
            len(assignments) == len(plan.proposition_chunk_assignments)
            and set(assignments) == set(base_by_chunk) | set(props_by_chunk)
            and all(len(rows) == 1 for rows in props_by_chunk.values()),
            "STEP11_RC0031_P2_0063_RESOURCE_ACCOUNTING_INVALID",
        )
        visible_by_chunk: list[int] = []
        complexity_by_chunk: list[int] = []
        for key, assignment in assignments.items():
            base_rows = tuple(base_by_chunk.get(key, ()))
            prop_rows = tuple(props_by_chunk.get(key, ()))
            visible = len(base_rows) + sum(
                row.visible_clause_count for row in prop_rows
            )
            complexity = sum(
                int(row.body_free_complexity_weight) for row in base_rows
            ) + sum(
                max(
                    len(row.source_atom_ids),
                    len(row.source_owner_ids),
                    row.visible_clause_count,
                )
                for row in prop_rows
            )
            _closed_assert(
                assignment.visible_clause_count == visible
                and assignment.complexity_load == complexity,
                "STEP11_RC0031_P2_0063_RESOURCE_ACCOUNTING_INVALID",
            )
            visible_by_chunk.append(visible)
            complexity_by_chunk.append(complexity)
        unit_count_by_group: dict[int, int] = {}
        joiner_count_by_group: dict[int, int] = {}
        for group in range(1, len(group_index) + 1):
            unit_count_by_group[group] = sum(
                len(rows)
                for (owner_group, _chunk), rows in base_by_chunk.items()
                if owner_group == group
            ) + sum(
                len(rows)
                for (owner_group, _chunk), rows in props_by_chunk.items()
                if owner_group == group
            )
            joiner_count_by_group[group] = sum(
                max(0, len(rows) - 1)
                for (owner_group, _chunk), rows in base_by_chunk.items()
                if owner_group == group
            ) + sum(
                max(0, row.visible_clause_count - 1)
                for (owner_group, _chunk), rows in props_by_chunk.items()
                if owner_group == group
                for row in rows
            )
        _closed_assert(
            unit_count_by_group == {1: 4, 2: 3, 3: 4}
            and {
                group: sum(
                    len(rows)
                    for (owner_group, _chunk), rows in props_by_chunk.items()
                    if owner_group == group
                )
                for group in range(1, len(group_index) + 1)
            }
            == {1: 2, 2: 1, 3: 2},
            "STEP11_RC0031_P2_0063_EXACT_FIVE_UNIT_WITNESS_INVALID",
        )
        reception_complexity = tuple(
            len(row.source_target_owner_ids)
            + len(row.supporting_source_owner_ids)
            for row in candidate.reception_bindings
        )
        recomputed_peaks = (
            max(unit_count_by_group.values(), default=0),
            max(
                max(visible_by_chunk, default=0),
                1 if candidate.reception_bindings else 0,
            ),
            max(
                max(complexity_by_chunk, default=0),
                max(reception_complexity, default=0),
            ),
            max(joiner_count_by_group.values(), default=0),
        )
        _closed_assert(
            recomputed_peaks == (4, 2, 4, 1)
            and recomputed_peaks
            == (
                plan.peak_observation_clause_count,
                plan.peak_grammatical_clause_count,
                plan.peak_grammatical_complexity_load,
                plan.peak_group_repeated_joiner_count,
            )
            and all(
                actual <= maximum
                for actual, maximum in zip(
                    recomputed_peaks, (4, 2, 4, 2), strict=True
                )
            ),
            "STEP11_RC0031_P2_0063_RESOURCE_BOUND_INVALID",
        )

    _closed_assert(
        bool(composition_witnesses),
        "STEP11_RC0031_P2_0063_COMPOSITION_NOT_PROVED",
    )
    clean, composition = composition_witnesses[0]
    plan = clean.surface_realization_plan
    false_composition = replace(
        composition,
        construction_modifier_target_owner_ids=(
            "nls3s11rc0031_unknown_owner",
            *composition.construction_modifier_target_owner_ids[1:],
        ),
    )
    mutated_plan = replace(
        plan,
        proposition_clause_bindings=tuple(
            false_composition if row == composition else row
            for row in plan.proposition_clause_bindings
        ),
    )
    mutated_ast = replace(
        clean.proposition_surface_ast,
        proposition_clause_bindings=tuple(
            false_composition if row == composition else row
            for row in clean.proposition_surface_ast.proposition_clause_bindings
        ),
    )
    false_fusion_issues = validate_step11_rc0031_experiment_surface_candidate(
        replace(
            clean,
            surface_realization_plan=mutated_plan,
            proposition_surface_ast=mutated_ast,
        ),
        successor_snapshot=successor,
        lexical_atom_specs=lexical_specs,
    )
    false_resource_issues = validate_step11_rc0031_experiment_surface_candidate(
        replace(
            clean,
            surface_realization_plan=replace(
                plan,
                peak_observation_clause_count=0,
            ),
        ),
        successor_snapshot=successor,
        lexical_atom_specs=lexical_specs,
    )
    _closed_assert(
        bool(false_fusion_issues) and bool(false_resource_issues),
        "STEP11_RC0031_P2_0063_FALSE_COMPOSITION_CLAIM_ACCEPTED",
    )
