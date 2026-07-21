# -*- coding: utf-8 -*-
from __future__ import annotations

"""P3 pre-freeze RED for the rc0031 final body inverse.

Production is intentionally unchanged.  The suite retains the exact10 GREEN
composition contract, detects the missing Step8 body-dimension recovery
contract before schema freeze, and specifies provisional body-only Parser /
independent Matcher behavior for the next separately approved design pass.
Public reuse remains closed and projected hashes are not signatures.
"""

import ast
import base64
from collections import Counter
from dataclasses import replace
from functools import lru_cache
import hashlib
import importlib
import inspect
import json
from pathlib import Path
import re
from typing import Any
import unicodedata

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
_SURFACE_MUTABLE_SLOT_BYTES = 5_178
_SURFACE_MUTABLE_SLOT_SHA256 = (
    "3356cecd99d65009c34e512966ae154857c4f167afe714c6907744d68a33ddea"
)
_SURFACE_MUTABLE_SLOT_BYTE_MAX = 8_192
_SERVICE_PY_PATH_COUNT = 546
_SERVICE_PY_PATH_LIST_SHA256 = (
    "46db0d14852dde6ebb6012596234cbb935243b27ed227465d9e94876ce4f5d56"
)
_REPOSITORY_PY_FROZEN_FILE_COUNT = 1_532
_REPOSITORY_PY_FROZEN_MATERIAL_SHA256 = (
    "1170f36dcd2a1e1d96d4c550c6ca62e0522ccebc26015b1827de14b8f391a851"
)
_MATCHER_PREDECESSOR_BYTES = 722_658
_MATCHER_PREDECESSOR_SHA256 = (
    "648a3a6690f8df860053c811a5416fcfc9983524e5ff880a0e6921a122a52e30"
)
_MATCHER_APPEND_BYTE_MAX = 131_072
_MATCHER_APPEND_MARKER = b"# rc0031 experiment-only final body inverse"
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
_FINAL_MATCH_BASIS = {
    "construction": "construction_instance_role_layout_exact",
    "relation": "relation_id_endpoint_direction_type_exact",
    "semantic_link": "semantic_link_id_endpoint_direction_type_exact",
    "explicit_unknown": "unknown_id_dimension_exact_target",
}
_FINAL_INVERSE_RED_CODE = "STEP11_RC0031_P3_FINAL_INVERSE_NOT_AVAILABLE"
_FINAL_OWNER_CANDIDATE_COMMITMENT_SCHEMA = (
    "cocolon.emlis.nls_v3.step11.rc0031_owner_expression_candidate.v1"
)
_FINAL_INVERSE_REQUIRED_EXPORTS = (
    "STEP11_RC0031_EXPERIMENT_PARSED_WITNESS_SCHEMA",
    "STEP11_RC0031_EXPERIMENT_VERIFIED_BINDING_SCHEMA",
    "Step11Rc0031ExperimentInverseSurfaceError",
    "Step11Rc0031ParsedSemanticAtom",
    "Step11Rc0031ParsedReceptionBinding",
    "Step11Rc0031ExperimentParsedSurfaceWitness",
    "Step11Rc0031VerifiedSemanticBinding",
    "Step11Rc0031VerifiedReceptionBinding",
    "Step11Rc0031ExperimentVerifiedSurfaceBinding",
    "parse_step11_rc0031_experiment_surface",
    "step11_rc0031_experiment_parsed_witness_material",
    "match_step11_rc0031_experiment_surface",
    "step11_rc0031_experiment_verified_binding_material",
)
_FINAL_PARSER_SIGNATURE = ("body",)
_FINAL_MATCHER_SIGNATURE = (
    "witness",
    "base_body_witness",
    "successor_snapshot",
    "inventory_result",
    "content_plan",
    "discourse_plan_set",
    "current_input",
)
_FINAL_MATCHER_POSITIONAL = ("witness",)
_FINAL_MATCHER_KEYWORD_ONLY = _FINAL_MATCHER_SIGNATURE[1:]
_FINAL_INVERSE_FORBIDDEN_PARAMETERS = frozenset(
    {
        "base_body",
        "base_body_bytes",
        "candidate",
        "candidate_ast",
        "candidate_metadata",
        "covered_obligation_ids",
        "final_bytes",
        "forward_plan",
        "gate_status",
        "generator_span_map",
        "lexical_atom_specs",
        "rendered_surface",
        "soft_score",
        "verified_base_reuse_bindings",
    }
)
_FINAL_PARSED_ATOM_REQUIRED_FIELDS = frozenset(
    {
        "atom_id",
        "semantic_family",
        "semantic_key",
        "direction",
        "sentence_group_ordinal",
        "grammatical_chunk_ordinal",
        "pack_ordinal",
        "item_ordinal",
        "utf8_byte_start",
        "utf8_byte_end",
        "span_sha256",
    }
)
_FINAL_PARSED_RECEPTION_REQUIRED_FIELDS = frozenset(
    {
        "binding_id",
        "reception_line_ordinal",
        "move_ordinal",
        "reception_act",
        "utf8_byte_start",
        "utf8_byte_end",
        "span_sha256",
    }
)
_FINAL_PARSED_ATOM_FIELDS = (
    "atom_id",
    "semantic_family",
    "semantic_key",
    "direction",
    "owner_expressions",
    "sentence_group_ordinal",
    "grammatical_chunk_ordinal",
    "pack_ordinal",
    "item_ordinal",
    "utf8_byte_start",
    "utf8_byte_end",
    "span_sha256",
    "owner_expression_candidate_commitments",
    "owner_expression_prefix_sha256",
)
_FINAL_PARSED_RECEPTION_FIELDS = (
    "binding_id",
    "reception_line_ordinal",
    "move_ordinal",
    "reception_act",
    "target_expression",
    "supporting_expression",
    "target_expression_sha256",
    "supporting_expression_sha256",
    "utf8_byte_start",
    "utf8_byte_end",
    "span_sha256",
)
_FINAL_PARSED_WITNESS_FIELDS = (
    "schema_version",
    "body_sha256",
    "experiment_catalog_sha256",
    "semantic_atoms",
    "reception_bindings",
    "observation_group_count",
    "reception_group_count",
    "base_prefix_commitments",
    "decomposition_locus_count",
    "evaluated_decomposition_count",
    "peak_stored_decomposition_count",
    "body_scan_pass_count",
    "body_free_export_allowed",
)
_FINAL_VERIFIED_SEMANTIC_FIELDS = (
    "source_atom_id",
    "semantic_family",
    "parsed_atom_id",
    "verified_reuse_binding_sha256",
    "match_basis",
)
_FINAL_VERIFIED_RECEPTION_FIELDS = (
    "source_reception_opportunity_id",
    "source_scope",
    "parsed_binding_id",
    "reception_line_ordinal",
    "move_ordinal",
    "reception_act",
    "target_owner_count",
    "supporting_owner_count",
    "association_basis",
)
_FINAL_VERIFIED_BINDING_FIELDS = (
    "schema_version",
    "parsed_witness_sha256",
    "base_witness_sha256",
    "successor_snapshot_sha256",
    "source_authority_sha256",
    "experiment_catalog_sha256",
    "semantic_bindings",
    "reception_bindings",
    "reception_binding_count",
    "owner_binding_comparison_count",
    "unique_solution_count",
    "semantic_coverage_authorized",
    "issue_codes",
    "hard_verified",
    "body_free_export_allowed",
)
_FINAL_PARSED_FORBIDDEN_FIELDS = frozenset(
    {
        "candidate_id",
        "covered_obligation_ids",
        "evidence_ids",
        "obligation_id",
        "relation_id",
        "source_atom_id",
        "source_reception_opportunity_id",
    }
)
_FINAL_INVERSE_FORBIDDEN_MODULES = (
    "emlis_ai_step11_grounded_lexicalization_v3",
    "emlis_ai_step11_hard_gate_v3",
    "emlis_ai_step11_natural_surface_v3",
    "emlis_ai_step11_rc0031_experiment_runtime_adapter_v3",
    "emlis_ai_step11_runtime_adapter_v3",
)
_FINAL_INVERSE_FORBIDDEN_CALLS = frozenset(
    {
        "breakpoint",
        "bytearray",
        "bytes",
        "chr",
        "compile",
        "delattr",
        "dir",
        "eval",
        "exec",
        "getattr",
        "globals",
        "help",
        "input",
        "locals",
        "evaluate_step11_natural_surface_candidate",
        "match_step11_rc0030_experiment_surface",
        "match_step11_natural_surface",
        "match_step11_rc0028_experiment_surface",
        "match_step11_rc0029_experiment_surface",
        "open",
        "permutations",
        "parse_step11_rc0030_experiment_surface",
        "parse_step11_natural_surface",
        "parse_step11_rc0028_experiment_surface",
        "parse_step11_rc0029_experiment_surface",
        "print",
        "product",
        "select_step11_natural_surface_candidates",
        "setattr",
        "vars",
    }
)
_FINAL_INVERSE_FORBIDDEN_NAME_REFERENCES = (
    _FINAL_INVERSE_FORBIDDEN_CALLS - {"bytes"}
)
_FINAL_INVERSE_ALLOWED_RC0030_CALLS = frozenset(
    {
        "_step11_rc0030_derive_allowed_base_reuse",
        "_step11_rc0030_expected_base_prefix_commitments",
        "_step11_rc0030_owner_candidate_commitment",
        "_step11_rc0030_owner_expression_prefix_commitment",
        "_step11_rc0030_reception_schedule",
        "_step11_rc0030_resolve_owner_candidate",
        "_step11_rc0030_revalidated_base_binding",
        "_step11_rc0030_validate_base_witness_origin",
        "_step11_rc0030_validate_semantic_placement",
        "_step11_rc0030_validated_source_records",
        "_step11_rc0030_visible_phrase_registry",
        "_step11_rc0030_visible_signature",
        "match_step11_rc0030_base_body_exact_reuse",
        "step11_rc0030_base_body_parsed_witness_material",
        "step11_rc0030_verified_base_body_reuse_material",
    }
)
_FINAL_INVERSE_ALLOWED_NON_ASCII_LITERALS = frozenset(
    {"見えたこと：\n", "\n\nEmlisから：\n"}
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


def _ast_call_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def _literal_join_value(node: ast.AST) -> str | None:
    if not (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "join"
        and isinstance(node.func.value, ast.Constant)
        and type(node.func.value.value) is str
        and len(node.args) == 1
        and not node.keywords
        and isinstance(node.args[0], (ast.List, ast.Tuple))
        and all(
            isinstance(row, ast.Constant) and type(row.value) is str
            for row in node.args[0].elts
        )
    ):
        return None
    return node.func.value.value.join(
        row.value for row in node.args[0].elts
    )


def _matcher_append_is_closed(value: bytes) -> bool:
    if not value:
        return True
    try:
        text = value.decode("utf-8", errors="strict")
        tree = ast.parse(text)
    except (UnicodeError, SyntaxError):
        return False
    if not value.lstrip(b"\n").startswith(_MATCHER_APPEND_MARKER):
        return False
    parent_by_id = {
        id(child): parent
        for parent in ast.walk(tree)
        for child in ast.iter_child_nodes(parent)
    }
    if any(
        isinstance(
            node,
            (
                ast.AsyncFunctionDef,
                ast.Await,
                ast.Global,
                ast.Import,
                ast.ImportFrom,
                ast.Lambda,
                ast.Nonlocal,
                ast.While,
                ast.Yield,
                ast.YieldFrom,
            ),
        )
        for node in ast.walk(tree)
    ):
        return False
    if any(
        module_name in text
        for module_name in _FINAL_INVERSE_FORBIDDEN_MODULES
    ):
        return False
    if any(
        isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and (
            "nls3s_b001_" in node.value
            or "expected_output" in node.value
            or "review_family" in node.value
            or "semantic_unknown:" in node.value
            or re.fullmatch(r"[0-9a-f]{16,64}", node.value) is not None
            or (
                any(ord(char) > 127 for char in node.value)
                and node.value
                not in _FINAL_INVERSE_ALLOWED_NON_ASCII_LITERALS
            )
        )
        for node in ast.walk(tree)
    ):
        return False
    if any(
        isinstance(node, ast.Constant)
        and isinstance(node.value, bytes)
        and (len(node.value) > 32 or any(row > 127 for row in node.value))
        for node in ast.walk(tree)
    ):
        return False
    if any(
        isinstance(node, ast.Constant)
        and type(node.value) is int
        and not -1_000_001 <= node.value <= 1_000_001
        for node in ast.walk(tree)
    ):
        return False
    if any(
        (literal := _literal_join_value(node)) is not None
        and len(literal) >= 16
        for node in ast.walk(tree)
    ):
        return False
    if any(
        isinstance(node, ast.BinOp)
        and (
            (
                isinstance(node.left, ast.Constant)
                and type(node.left.value) in {str, bytes}
            )
            or (
                isinstance(node.right, ast.Constant)
                and type(node.right.value) in {str, bytes}
            )
        )
        for node in ast.walk(tree)
    ):
        return False
    for node in ast.walk(tree):
        reference_name = (
            node.id
            if isinstance(node, ast.Name)
            else node.attr
            if isinstance(node, ast.Attribute)
            else None
        )
        if reference_name is not None and (
            reference_name.startswith(
                ("_step11_rc0028_", "_step11_rc0029_")
            )
            or (
                reference_name.startswith(
                    ("_step11_rc0030_", "step11_rc0030_")
                )
                and reference_name
                not in _FINAL_INVERSE_ALLOWED_RC0030_CALLS
            )
        ):
            return False
        if isinstance(node, ast.FunctionDef):
            parameter_names = {
                row.arg
                for row in (
                    *node.args.posonlyargs,
                    *node.args.args,
                    *node.args.kwonlyargs,
                )
            }
            if node.args.vararg is not None:
                parameter_names.add(node.args.vararg.arg)
            if node.args.kwarg is not None:
                parameter_names.add(node.args.kwarg.arg)
            if parameter_names & _FINAL_INVERSE_FORBIDDEN_PARAMETERS:
                return False
        if isinstance(node, ast.Call):
            call_name = _ast_call_name(node)
            if call_name in _FINAL_INVERSE_FORBIDDEN_CALLS:
                return False
            if (
                call_name is not None
                and call_name.startswith(
                    ("_step11_rc0030_", "step11_rc0030_")
                )
                and call_name not in _FINAL_INVERSE_ALLOWED_RC0030_CALLS
            ):
                return False
            if call_name is not None and (
                "final_parse" in call_name
                or "final_match" in call_name
                or call_name.startswith("_step11_rc0028_")
                or call_name.startswith("_step11_rc0029_")
            ):
                return False
            if not isinstance(node.func, (ast.Name, ast.Attribute)):
                return False
            if call_name == "__import__":
                if (
                    not node.args
                    or not isinstance(node.args[0], ast.Constant)
                    or node.args[0].value
                    != "emlis_ai_step11_rc0031_experiment_surface_catalog_v3"
                ):
                    return False
        if isinstance(node, ast.Name) and node.id in (
            _FINAL_INVERSE_FORBIDDEN_NAME_REFERENCES
            | {
                "__builtins__",
                "builtins",
            }
        ):
            return False
        if isinstance(node, ast.Name) and node.id == "__import__":
            parent = parent_by_id.get(id(node))
            if not (isinstance(parent, ast.Call) and parent.func is node):
                return False
        if isinstance(node, ast.Name) and node.id == "bytes":
            parent = parent_by_id.get(id(node))
            if not (
                isinstance(parent, (ast.Compare, ast.arg, ast.Subscript))
                or (
                    isinstance(parent, ast.Call)
                    and _ast_call_name(parent) == "isinstance"
                    and node in parent.args[1:]
                )
            ):
                return False
        if (
            isinstance(node, ast.Name)
            and node.id.startswith("__")
            and node.id not in {"__all__", "__import__"}
        ):
            return False
        if isinstance(node, ast.Name) and node.id in {
            "itertools",
            "logger",
            "logging",
            "os",
            "pathlib",
            "requests",
            "socket",
            "subprocess",
            "sys",
        }:
            return False
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            return False
    for function in (
        row for row in ast.walk(tree) if isinstance(row, ast.FunctionDef)
    ):
        if any(
            isinstance(child, ast.Call)
            and isinstance(child.func, ast.Name)
            and child.func.id == function.name
            for child in ast.walk(function)
        ):
            return False
    functions = {
        row.name: row
        for row in ast.walk(tree)
        if isinstance(row, ast.FunctionDef)
    }
    call_graph = {
        name: {
            call_name
            for child in ast.walk(function)
            if isinstance(child, ast.Call)
            and (call_name := _ast_call_name(child)) in functions
        }
        for name, function in functions.items()
    }
    for start in call_graph:
        pending = list(call_graph[start])
        visited: set[str] = set()
        while pending:
            current = pending.pop()
            if current == start:
                return False
            if current not in visited:
                visited.add(current)
                pending.extend(call_graph[current])
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
            if "rc0031" not in node.name.lower():
                return False
            if isinstance(node, ast.FunctionDef) and node.decorator_list:
                return False
            if isinstance(node, ast.ClassDef) and any(
                not (
                    isinstance(decorator, ast.Call)
                    and isinstance(decorator.func, ast.Name)
                    and decorator.func.id == "dataclass"
                )
                for decorator in node.decorator_list
            ):
                return False
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = (
                node.targets if isinstance(node, ast.Assign) else (node.target,)
            )
            names = {
                child.id
                for target in targets
                for child in ast.walk(target)
                if isinstance(child, ast.Name)
            }
            if any(
                name != "__all__" and "rc0031" not in name.lower()
                for name in names
            ):
                return False
        elif isinstance(node, ast.AugAssign):
            if not (
                isinstance(node.target, ast.Name)
                and node.target.id == "__all__"
                and isinstance(node.op, ast.Add)
            ):
                return False
        elif isinstance(node, ast.Expr):
            if not (
                isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)
            ):
                return False
        else:
            return False
    return True


@lru_cache(maxsize=1)
def _rc0031_final_inverse_api_or_red() -> dict[str, Any]:
    inverse = _inverse_module()
    if any(
        not hasattr(inverse, name) for name in _FINAL_INVERSE_REQUIRED_EXPORTS
    ) or not set(_FINAL_INVERSE_REQUIRED_EXPORTS).issubset(
        set(getattr(inverse, "__all__", ()))
    ):
        pytest.fail(_FINAL_INVERSE_RED_CODE, pytrace=False)
    return {
        name: getattr(inverse, name)
        for name in _FINAL_INVERSE_REQUIRED_EXPORTS
    }


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


def _material_is_body_free(value: Any) -> bool:
    if type(value) is dict:
        return all(
            type(key) is str
            and key.isascii()
            and _material_is_body_free(child)
            for key, child in value.items()
        )
    if type(value) in {list, tuple}:
        return not (
            value and all(type(child) is int for child in value)
        ) and all(_material_is_body_free(child) for child in value)
    if type(value) is str:
        return value.isascii() and not any(
            ord(char) < 32 or ord(char) == 127 for char in value
        )
    return (
        value is None
        or type(value) is bool
        or (type(value) is int and 0 <= value <= 1_000_000)
    )


def _expected_rc0031_parsed_witness_material(value: Any) -> dict[str, Any]:
    semantic_atoms: list[dict[str, Any]] = []
    for row in value.semantic_atoms:
        material = {
            "atom_id": row.atom_id,
            "semantic_family": row.semantic_family,
            "semantic_key": row.semantic_key,
            "direction": row.direction,
            "owner_expression_count": len(row.owner_expressions),
            "owner_expression_sha256": [
                hashlib.sha256(item.encode("utf-8")).hexdigest()
                for item in row.owner_expressions
            ],
            "sentence_group_ordinal": row.sentence_group_ordinal,
            "grammatical_chunk_ordinal": row.grammatical_chunk_ordinal,
            "pack_ordinal": row.pack_ordinal,
            "item_ordinal": row.item_ordinal,
            "utf8_byte_start": row.utf8_byte_start,
            "utf8_byte_end": row.utf8_byte_end,
            "span_sha256": row.span_sha256,
        }
        if row.owner_expression_candidate_commitments:
            material["owner_expression_candidate_count"] = len(
                row.owner_expression_candidate_commitments
            )
            material["owner_expression_candidate_commitments"] = list(
                row.owner_expression_candidate_commitments
            )
            material["owner_expression_prefix_sha256"] = (
                row.owner_expression_prefix_sha256
            )
        semantic_atoms.append(material)
    return {
        "schema_version": value.schema_version,
        "body_sha256": value.body_sha256,
        "experiment_catalog_sha256": value.experiment_catalog_sha256,
        "semantic_atoms": semantic_atoms,
        "reception_bindings": [
            {
                "binding_id": row.binding_id,
                "reception_line_ordinal": row.reception_line_ordinal,
                "move_ordinal": row.move_ordinal,
                "reception_act": row.reception_act,
                "target_expression_sha256": row.target_expression_sha256,
                "supporting_expression_sha256": (
                    row.supporting_expression_sha256
                ),
                "utf8_byte_start": row.utf8_byte_start,
                "utf8_byte_end": row.utf8_byte_end,
                "span_sha256": row.span_sha256,
            }
            for row in value.reception_bindings
        ],
        "observation_group_count": value.observation_group_count,
        "reception_group_count": value.reception_group_count,
        "base_prefix_commitments": list(value.base_prefix_commitments),
        "decomposition_locus_count": value.decomposition_locus_count,
        "evaluated_decomposition_count": (
            value.evaluated_decomposition_count
        ),
        "peak_stored_decomposition_count": (
            value.peak_stored_decomposition_count
        ),
        "body_scan_pass_count": value.body_scan_pass_count,
        "body_free_export_allowed": value.body_free_export_allowed,
    }


def _expected_rc0031_verified_binding_material(value: Any) -> dict[str, Any]:
    return {
        "schema_version": value.schema_version,
        "parsed_witness_sha256": value.parsed_witness_sha256,
        "base_witness_sha256": value.base_witness_sha256,
        "successor_snapshot_sha256": value.successor_snapshot_sha256,
        "source_authority_sha256": value.source_authority_sha256,
        "experiment_catalog_sha256": value.experiment_catalog_sha256,
        "semantic_bindings": [
            {
                "source_atom_id": row.source_atom_id,
                "semantic_family": row.semantic_family,
                "parsed_atom_id": row.parsed_atom_id,
                "verified_reuse_binding_sha256": (
                    row.verified_reuse_binding_sha256
                ),
                "match_basis": row.match_basis,
            }
            for row in value.semantic_bindings
        ],
        "reception_bindings": [
            {
                "source_reception_opportunity_id": (
                    row.source_reception_opportunity_id
                ),
                "source_scope": row.source_scope,
                "parsed_binding_id": row.parsed_binding_id,
                "reception_line_ordinal": row.reception_line_ordinal,
                "move_ordinal": row.move_ordinal,
                "reception_act": row.reception_act,
                "target_owner_count": row.target_owner_count,
                "supporting_owner_count": row.supporting_owner_count,
                "association_basis": row.association_basis,
            }
            for row in value.reception_bindings
        ],
        "reception_binding_count": value.reception_binding_count,
        "owner_binding_comparison_count": (
            value.owner_binding_comparison_count
        ),
        "unique_solution_count": value.unique_solution_count,
        "semantic_coverage_authorized": value.semantic_coverage_authorized,
        "issue_codes": list(value.issue_codes),
        "hard_verified": value.hard_verified,
        "body_free_export_allowed": value.body_free_export_allowed,
    }


def _material_contains_body_encoding(value: Any, body: bytes) -> bool:
    serialized = json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    return any(
        token and token in serialized
        for token in (
            body.hex(),
            base64.b64encode(body).decode("ascii"),
        )
    )


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
def _rc0031_catalog_authority() -> tuple[dict[str, Any], str]:
    owner = importlib.import_module(
        "emlis_ai_step11_rc0031_experiment_surface_catalog_v3"
    )
    catalog = owner.STEP11_RC0031_EXPERIMENT_SURFACE_CATALOG
    _closed_assert(
        owner.validate_step11_rc0031_experiment_surface_catalog(catalog) == (),
        "STEP11_RC0031_P3_FINAL_CATALOG_INVALID",
    )
    return catalog, owner.STEP11_RC0031_EXPERIMENT_SURFACE_CATALOG_SHA256


def _independent_rc0031_source_projection(
    context: tuple[Any, ...],
) -> tuple[
    dict[str, tuple[str, str, str, tuple[str, ...]]],
    dict[str, tuple[str, str, tuple[str, ...], tuple[str, ...], int, int, str]],
    str,
    str,
    str,
    int,
]:
    (
        _case_id,
        baseline,
        successor,
        _lexical_specs,
        _candidate,
        base_body_witness,
    ) = context
    inverse = _inverse_module()
    base_witness = base_body_witness.base_witness
    discourse_plan, base_binding = _independent_base_plan_binding(
        baseline, base_body_witness
    )
    (
        records,
        receptions,
        aliases,
        successor_snapshot_sha256,
        source_authority_sha256,
        _exact_aliases,
    ) = inverse._step11_rc0030_validated_source_records(
        successor,
        inventory_result=baseline.inventory_result,
    )
    required_owner_ids = {
        owner_id for row in records for owner_id in row[4]
    } | {
        owner_id
        for row in receptions
        for owner_id in (*row[3], *row[4])
    }
    owner_text, comparison_count = (
        inverse._step11_rc0030_visible_phrase_registry(
            base_witness,
            base_binding,
            source_owner_aliases={
                owner_id: aliases[owner_id]
                for owner_id in required_owner_ids
            },
        )
    )
    catalog, _catalog_sha256 = _rc0031_catalog_authority()
    semantic_by_source = {
        source_id: (
            family,
            key,
            direction,
            tuple(owner_text[row] for row in owner_ids),
        )
        for source_id, family, key, direction, owner_ids in records
    }
    _ledger, obligation_by_id = inverse._validated_parents(
        baseline.inventory_result,
        baseline.content_plan,
        discourse_plan,
    )
    scheduled_receptions = inverse._step11_rc0030_reception_schedule(
        base_body_witness,
        base_binding,
        inventory_result=baseline.inventory_result,
        discourse_plan=discourse_plan,
        current_input=baseline.projected_current_input,
        obligation_by_id=obligation_by_id,
        receptions=receptions,
    )
    joiner = catalog["clause_morphology"]["target_owner_join"]
    reception_by_source = {
        source_id: (
            scope,
            act,
            tuple(owner_text[row] for row in targets),
            tuple(owner_text[row] for row in supports),
            line_ordinal,
            move_ordinal,
            association_basis,
        )
        for (
            source_id,
            scope,
            act,
            targets,
            supports,
            line_ordinal,
            move_ordinal,
            association_basis,
        ) in scheduled_receptions
    }
    _closed_assert(
        len(semantic_by_source) == len(records)
        and len(reception_by_source) == len(scheduled_receptions)
        and all(
            joiner.join(row[2])
            and (not row[3] or joiner.join(row[3]))
            for row in reception_by_source.values()
        ),
        "STEP11_RC0031_P3_FINAL_SOURCE_PROJECTION_INVALID",
    )
    return (
        semantic_by_source,
        reception_by_source,
        successor_snapshot_sha256,
        source_authority_sha256,
        inverse.artifact_sha256(inverse._witness_material(base_witness)),
        comparison_count,
    )


def _parsed_owner_matches_source(
    parsed: Any,
    expected: tuple[str, str, str, tuple[str, ...]],
) -> bool:
    family, key, direction, owner_expressions = expected
    if (
        parsed.semantic_family != family
        or parsed.semantic_key != key
        or parsed.direction != direction
    ):
        return False
    if parsed.owner_expression_candidate_commitments:
        inverse = _inverse_module()
        expected_commitment = inverse.artifact_sha256(
            {
                "schema_version": (
                    _FINAL_OWNER_CANDIDATE_COMMITMENT_SCHEMA
                ),
                "owner_expression_sha256": [
                    hashlib.sha256(row.encode("utf-8")).hexdigest()
                    for row in owner_expressions
                ],
            }
        )
        return (
            parsed.owner_expressions == ()
            and expected_commitment
            in parsed.owner_expression_candidate_commitments
            and type(parsed.owner_expression_prefix_sha256) is str
            and re.fullmatch(
                r"[0-9a-f]{64}", parsed.owner_expression_prefix_sha256
            )
            is not None
        )
    return (
        parsed.owner_expressions == owner_expressions
        and parsed.owner_expression_prefix_sha256 is None
    )


def _render_rc0031_source_clause_for_attack(
    *,
    family: str,
    key: str,
    direction: str,
    owner_expressions: tuple[str, ...],
) -> str:
    catalog, _catalog_sha256 = _rc0031_catalog_authority()
    morphology = catalog["clause_morphology"]
    if family == "construction":
        return (
            owner_expressions[0]
            + catalog["construction_predicate_fragments"][key]
            + morphology["construction_standalone_predicate"]
        )
    if family in {"relation", "semantic_link"}:
        registry = (
            catalog["relation_predicate_fragments"]
            if family == "relation"
            else catalog["semantic_link_predicate_fragments"]
        )
        return registry[f"{key}:{direction}"].format(
            source=owner_expressions[0],
            target=owner_expressions[1],
        )
    if family == "explicit_unknown":
        return (
            morphology["unknown_owner_join"].join(owner_expressions)
            + catalog["unknown_predicate_fragments"][key]
        )
    raise AssertionError("STEP11_RC0031_P3_ATTACK_FAMILY_INVALID")


def _render_rc0031_reception_for_attack(
    expected: tuple[
        str,
        str,
        tuple[str, ...],
        tuple[str, ...],
        int,
        int,
        str,
    ],
) -> str:
    _scope, act, targets, supports, _line, _move, _basis = expected
    catalog, _catalog_sha256 = _rc0031_catalog_authority()
    morphology = catalog["clause_morphology"]
    support_prefix = (
        morphology["support_owner_join"].join(supports)
        + morphology["support_target_link"]
        if supports
        else ""
    )
    return (
        support_prefix
        + morphology["target_owner_join"].join(targets)
        + morphology["reception_object_particle"]
        + catalog["reception_act_predicate_fragments"][act]
    )


def _independent_base_plan_binding(
    baseline: Any,
    base_body_witness: Any,
) -> tuple[dict[str, Any], Any]:
    inverse = _inverse_module()
    matches: list[tuple[dict[str, Any], Any]] = []
    for discourse_plan in baseline.discourse_plan_set.plans:
        try:
            binding = inverse._step11_rc0030_revalidated_base_binding(
                base_body_witness.base_witness,
                inventory_result=baseline.inventory_result,
                content_plan=baseline.content_plan,
                discourse_plan=discourse_plan,
                current_input=baseline.projected_current_input,
            )
        except inverse.Step11Rc0030ExperimentInverseSurfaceError:
            continue
        if binding.verified is True and binding.issue_codes == ():
            matches.append((discourse_plan, binding))
    _closed_assert(
        len(matches) == 1,
        "STEP11_RC0031_P3_BASE_DISCOURSE_BINDING_NOT_UNIQUE",
    )
    return matches[0]


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


@lru_cache(maxsize=1)
def _rc0031_final_candidate_contexts() -> tuple[tuple[Any, ...], ...]:
    p2 = _p2_test_module()
    surface = _surface_module()
    inverse = _inverse_module()
    contexts: list[tuple[Any, ...]] = []
    for case_id in _REPRESENTATIVE_CASE_IDS:
        baseline, successor, lexical_specs = p2._forward_authority(case_id)
        candidates = surface.build_step11_rc0031_experiment_surface_candidates(
            tuple(baseline.natural_candidates),
            successor_snapshot=successor,
            lexical_atom_specs=lexical_specs,
        )
        for public_candidate in candidates:
            candidate = public_candidate
            base = public_candidate.base_candidate
            base_witness = inverse.parse_step11_rc0030_base_body_exact_reuse(
                base.final_utf8_bytes
            )
            if case_id == "nls3s_b001_0001":
                verified = inverse.match_step11_rc0030_base_body_exact_reuse(
                    base_witness,
                    successor_snapshot=successor,
                    inventory_result=baseline.inventory_result,
                    content_plan=baseline.content_plan,
                    discourse_plan=base.discourse_plan,
                    current_input=baseline.projected_current_input,
                )
                candidate = (
                    surface
                    ._step11_rc0031_build_candidate_from_verified_reuse_composition(
                        base,
                        successor_snapshot=successor,
                        lexical_atom_specs=lexical_specs,
                        verified_base_body_exact_reuse_bindings=tuple(
                            _project_verified_proof(row) for row in verified
                        ),
                        validate_output=True,
                    )
                )
            contexts.append(
                (
                    case_id,
                    baseline,
                    successor,
                    lexical_specs,
                    candidate,
                    base_witness,
                )
            )
    _closed_assert(
        len(contexts) == 10
        and sum(
            candidate.rendered_surface.semantic_atom_count
            for _case, _base, _successor, _lexical, candidate, _witness
            in contexts
        )
        == 38
        and sum(
            candidate.rendered_surface.exact_reuse_count
            for _case, _base, _successor, _lexical, candidate, _witness
            in contexts
        )
        == 1
        and sum(
            len(candidate.reception_bindings)
            for _case, _base, _successor, _lexical, candidate, _witness
            in contexts
        )
        == 11,
        "STEP11_RC0031_P3_FINAL_DENOMINATOR_DRIFT",
    )
    return tuple(contexts)


def _call_rc0031_final_matcher(
    api: dict[str, Any],
    witness: Any,
    context: tuple[Any, ...],
    **unexpected: Any,
) -> Any:
    (
        _case_id,
        baseline,
        successor,
        _lexical_specs,
        _candidate,
        base_witness,
    ) = context
    return api["match_step11_rc0031_experiment_surface"](
        witness,
        base_body_witness=base_witness,
        successor_snapshot=successor,
        inventory_result=baseline.inventory_result,
        content_plan=baseline.content_plan,
        discourse_plan_set=baseline.discourse_plan_set,
        current_input=baseline.projected_current_input,
        **unexpected,
    )


def _assert_rc0031_inverse_error_is_body_free(
    exc: BaseException,
    error_type: type[BaseException],
    *,
    capsys: Any,
    failure_code: str,
) -> None:
    _assert_no_captured_output(
        capsys, "STEP11_RC0031_P3_FINAL_INVERSE_BODY_OUTPUT_LEAK"
    )
    code = getattr(exc, "code", None)
    _closed_assert(
        type(exc) is error_type
        and type(code) is str
        and re.fullmatch(r"STEP11_RC0031_[A-Z0-9_]{2,95}", code) is not None
        and str(exc) == code,
        failure_code,
    )
    _closed_assert(
        exc.args == (code,)
        and set(vars(exc)) <= {"code"}
        and exc.__cause__ is None
        and exc.__context__ is None
        and not getattr(exc, "__notes__", ())
        and all(
            name.startswith("_")
            or name in {"add_note", "args", "code", "with_traceback"}
            for name in dir(exc)
        )
        and repr(exc).isascii(),
        failure_code,
    )


def _expect_rc0031_inverse_error(
    api: dict[str, Any],
    call: Any,
    *,
    capsys: Any,
    failure_code: str,
    expected_code: str | None = None,
) -> None:
    error_type = api["Step11Rc0031ExperimentInverseSurfaceError"]
    try:
        call()
    except error_type as exc:
        _assert_rc0031_inverse_error_is_body_free(
            exc, error_type, capsys=capsys, failure_code=failure_code
        )
        _closed_assert(
            expected_code is None or exc.code == expected_code,
            failure_code,
        )
    except Exception:
        _assert_no_captured_output(
            capsys, "STEP11_RC0031_P3_FINAL_INVERSE_BODY_OUTPUT_LEAK"
        )
        pytest.fail(failure_code, pytrace=False)
    else:
        _assert_no_captured_output(
            capsys, "STEP11_RC0031_P3_FINAL_INVERSE_BODY_OUTPUT_LEAK"
        )
        pytest.fail(failure_code, pytrace=False)


def _assert_body_span(body: bytes, row: Any, code: str) -> None:
    start = getattr(row, "utf8_byte_start", None)
    end = getattr(row, "utf8_byte_end", None)
    span_sha256 = getattr(row, "span_sha256", None)
    _closed_assert(type(start) is int and type(end) is int, code)
    try:
        span = body[start:end]
        span.decode("utf-8", errors="strict")
    except (TypeError, UnicodeError):
        pytest.fail(code, pytrace=False)
    _closed_assert(
        0 <= start < end <= len(body)
        and hashlib.sha256(span).hexdigest() == span_sha256,
        code,
    )


def _replace_body_span(
    body: bytes,
    row: Any,
    replacement: bytes,
) -> bytes:
    return (
        body[: row.utf8_byte_start]
        + replacement
        + body[row.utf8_byte_end :]
    )


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
            if path
            not in {
                _MATCHER_PATH,
                _SURFACE_PATH,
                Path(__file__).resolve(),
            }
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
        and len(mutable_slot) == _SURFACE_MUTABLE_SLOT_BYTES
        and hashlib.sha256(mutable_slot).hexdigest()
        == _SURFACE_MUTABLE_SLOT_SHA256
        and len(mutable_slot) <= _SURFACE_MUTABLE_SLOT_BYTE_MAX
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

    matcher_bytes = _MATCHER_PATH.read_bytes()
    matcher_predecessor = matcher_bytes[:_MATCHER_PREDECESSOR_BYTES]
    matcher_append = matcher_bytes[_MATCHER_PREDECESSOR_BYTES:]
    _closed_assert(
        len(matcher_predecessor) == _MATCHER_PREDECESSOR_BYTES
        and hashlib.sha256(matcher_predecessor).hexdigest()
        == _MATCHER_PREDECESSOR_SHA256
        and len(matcher_append) <= _MATCHER_APPEND_BYTE_MAX
        and _matcher_append_is_closed(matcher_append),
        "STEP11_RC0031_P3_MATCHER_APPEND_SCOPE_INVALID",
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


def test_rc0031_p3_p2_grammar_has_explicit_step8_dimension_recovery_contract() -> None:
    baseline, _successor, _lexical = _p2_test_module()._forward_authority(
        "nls3s_b001_0035"
    )
    source_snapshot = baseline.inventory_result.source_snapshot
    obligations = tuple(baseline.inventory_result.ledger["obligations"])
    required_obligation_dimensions = {
        "polarity",
        "modality",
        "temporal_scope",
        "topic_scope_ids",
        "referent_scope",
        "evidence_ids",
        "source_refs",
    }
    source_side_is_complete = (
        source_snapshot.observation_stage == "normal_observation"
        and source_snapshot.semantic_source_roles == ("original_input",)
        and obligations
        and all(
            required_obligation_dimensions <= set(row)
            for row in obligations
        )
    )
    catalog_owner = importlib.import_module(
        "emlis_ai_step11_rc0031_experiment_surface_catalog_v3"
    )
    recovery_contract = getattr(
        catalog_owner,
        "STEP11_RC0031_EXPERIMENT_BODY_DIMENSION_RECOVERY_CONTRACT",
        None,
    )
    required_body_dimensions = {
        "observation_stage",
        "source_role",
        "polarity",
        "modality",
        "temporal_scope",
        "topic_fingerprint",
        "referent_scope",
    }
    _closed_assert(
        source_side_is_complete
        and type(recovery_contract) is dict
        and required_body_dimensions <= set(recovery_contract)
        and all(
            type(key) is str
            and type(value) is str
            and key.isascii()
            and value.isascii()
            and bool(value)
            for key, value in recovery_contract.items()
        ),
        "STEP11_RC0031_P3_STEP8_DIMENSION_CONTRACT_NOT_AVAILABLE",
    )


def test_rc0031_p3_base_body_selects_one_source_discourse_plan_without_candidate_metadata() -> None:
    baseline, _successor, _lexical = _p2_test_module()._forward_authority(
        "nls3s_b001_0009"
    )
    base_candidate = baseline.natural_candidates[0]
    base_body_witness = (
        _inverse_module().parse_step11_rc0030_base_body_exact_reuse(
            base_candidate.final_utf8_bytes
        )
    )
    _closed_assert(
        len(baseline.discourse_plan_set.plans) == 8,
        "STEP11_RC0031_P3_BASE_DISCOURSE_DENOMINATOR_DRIFT",
    )
    _independent_base_plan_binding(baseline, base_body_witness)


def test_rc0031_p3_final_inverse_symbols_and_body_only_signatures_are_exact() -> None:
    api = _rc0031_final_inverse_api_or_red()
    parser = api["parse_step11_rc0031_experiment_surface"]
    matcher = api["match_step11_rc0031_experiment_surface"]
    parser_material = api[
        "step11_rc0031_experiment_parsed_witness_material"
    ]
    binding_material = api[
        "step11_rc0031_experiment_verified_binding_material"
    ]
    parser_parameters = inspect.signature(parser).parameters
    matcher_parameters = inspect.signature(matcher).parameters
    _closed_assert(
        api["STEP11_RC0031_EXPERIMENT_PARSED_WITNESS_SCHEMA"]
        == (
            "cocolon.emlis.nls_v3.step11."
            "rc0031_experiment_parsed_witness.v1"
        )
        and api["STEP11_RC0031_EXPERIMENT_VERIFIED_BINDING_SCHEMA"]
        == (
            "cocolon.emlis.nls_v3.step11."
            "rc0031_experiment_verified_binding.v1"
        )
        and issubclass(
            api["Step11Rc0031ExperimentInverseSurfaceError"], ValueError
        )
        and tuple(parser_parameters) == _FINAL_PARSER_SIGNATURE
        and parser_parameters["body"].kind
        is inspect.Parameter.POSITIONAL_OR_KEYWORD
        and tuple(matcher_parameters) == _FINAL_MATCHER_SIGNATURE
        and tuple(
            name
            for name, row in matcher_parameters.items()
            if row.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
        )
        == _FINAL_MATCHER_POSITIONAL
        and tuple(
            name
            for name, row in matcher_parameters.items()
            if row.kind is inspect.Parameter.KEYWORD_ONLY
        )
        == _FINAL_MATCHER_KEYWORD_ONLY
        and not (
            set(parser_parameters) | set(matcher_parameters)
        )
        & _FINAL_INVERSE_FORBIDDEN_PARAMETERS
        and tuple(inspect.signature(parser_material).parameters) == ("value",)
        and tuple(inspect.signature(binding_material).parameters) == ("value",),
        "STEP11_RC0031_P3_FINAL_INVERSE_API_INVALID",
    )
    error_type = api["Step11Rc0031ExperimentInverseSurfaceError"]
    _closed_assert(
        set(error_type.__dict__)
        <= {
            "__dict__",
            "__doc__",
            "__init__",
            "__module__",
            "__weakref__",
        },
        "STEP11_RC0031_P3_FINAL_INVERSE_API_INVALID",
    )

    parsed_atom_field_order = tuple(
        api["Step11Rc0031ParsedSemanticAtom"].__dataclass_fields__
    )
    parsed_reception_field_order = tuple(
        api["Step11Rc0031ParsedReceptionBinding"].__dataclass_fields__
    )
    witness_field_order = tuple(
        api[
            "Step11Rc0031ExperimentParsedSurfaceWitness"
        ].__dataclass_fields__
    )
    verified_semantic_field_order = tuple(
        api["Step11Rc0031VerifiedSemanticBinding"].__dataclass_fields__
    )
    verified_reception_field_order = tuple(
        api["Step11Rc0031VerifiedReceptionBinding"].__dataclass_fields__
    )
    verified_binding_field_order = tuple(
        api[
            "Step11Rc0031ExperimentVerifiedSurfaceBinding"
        ].__dataclass_fields__
    )
    parsed_atom_fields = frozenset(parsed_atom_field_order)
    parsed_reception_fields = frozenset(parsed_reception_field_order)
    witness_fields = frozenset(witness_field_order)
    _closed_assert(
        parsed_atom_field_order == _FINAL_PARSED_ATOM_FIELDS
        and parsed_reception_field_order == _FINAL_PARSED_RECEPTION_FIELDS
        and witness_field_order == _FINAL_PARSED_WITNESS_FIELDS
        and verified_semantic_field_order == _FINAL_VERIFIED_SEMANTIC_FIELDS
        and verified_reception_field_order
        == _FINAL_VERIFIED_RECEPTION_FIELDS
        and verified_binding_field_order == _FINAL_VERIFIED_BINDING_FIELDS
        and _FINAL_PARSED_ATOM_REQUIRED_FIELDS <= parsed_atom_fields
        and _FINAL_PARSED_RECEPTION_REQUIRED_FIELDS <= parsed_reception_fields
        and not (
            parsed_atom_fields
            | parsed_reception_fields
            | witness_fields
        )
        & _FINAL_PARSED_FORBIDDEN_FIELDS,
        "STEP11_RC0031_P3_FINAL_INVERSE_SCHEMA_INVALID",
    )
    dataclass_types = tuple(
        api[name]
        for name in (
            "Step11Rc0031ParsedSemanticAtom",
            "Step11Rc0031ParsedReceptionBinding",
            "Step11Rc0031ExperimentParsedSurfaceWitness",
            "Step11Rc0031VerifiedSemanticBinding",
            "Step11Rc0031VerifiedReceptionBinding",
            "Step11Rc0031ExperimentVerifiedSurfaceBinding",
        )
    )
    _closed_assert(
        all(
            value.__dataclass_params__.frozen is True
            and "__slots__" in value.__dict__
            and value.__repr__ is object.__repr__
            for value in dataclass_types
        )
        and "__weakref__"
        in api[
            "Step11Rc0031ExperimentParsedSurfaceWitness"
        ].__slots__,
        "STEP11_RC0031_P3_FINAL_INVERSE_SCHEMA_INVALID",
    )


def test_rc0031_p3_representative10_final_round_trip_is_unique_deterministic_body_only(
    capsys: Any,
) -> None:
    api = _rc0031_final_inverse_api_or_red()
    parser = api["parse_step11_rc0031_experiment_surface"]
    parsed_material = api[
        "step11_rc0031_experiment_parsed_witness_material"
    ]
    verified_material = api[
        "step11_rc0031_experiment_verified_binding_material"
    ]
    parsed_total = 0
    reuse_total = 0
    reception_total = 0
    deterministic_count = 0
    for context in _rc0031_final_candidate_contexts():
        _case_id, _baseline, _successor, _lexical, candidate, base = context
        body = candidate.final_utf8_bytes
        witness = parser(body)
        binding = _call_rc0031_final_matcher(api, witness, context)
        witness_material = parsed_material(witness)
        binding_material = verified_material(binding)
        expected_witness_material = (
            _expected_rc0031_parsed_witness_material(witness)
        )
        expected_binding_material = (
            _expected_rc0031_verified_binding_material(binding)
        )
        semantic_rows = tuple(binding.semantic_bindings)
        parsed_rows = tuple(
            row for row in semantic_rows if row.parsed_atom_id is not None
        )
        reuse_rows = tuple(
            row
            for row in semantic_rows
            if row.verified_reuse_binding_sha256 is not None
        )
        (
            semantic_by_source,
            expected_receptions_by_source,
            successor_snapshot_sha256,
            source_authority_sha256,
            base_witness_sha256,
            source_comparison_count,
        ) = _independent_rc0031_source_projection(context)
        source_ids = tuple(semantic_by_source)
        catalog, catalog_sha256 = _rc0031_catalog_authority()
        joiner = catalog["clause_morphology"]["target_owner_join"]
        witness_atoms_by_id = {
            row.atom_id: row for row in witness.semantic_atoms
        }
        parsed_receptions_by_id = {
            row.binding_id: row for row in witness.reception_bindings
        }
        changed_groups = {
            row.sentence_group_ordinal for row in witness.semantic_atoms
        }
        expected_base_prefix_commitments = tuple(
            (
                base.observation_stem_sha256[ordinal - 1]
                if ordinal in changed_groups
                else base.observation_line_sha256[ordinal - 1]
            )
            for ordinal in range(1, witness.observation_group_count + 1)
        )
        ordered_spans = sorted(
            (
                (row.utf8_byte_start, row.utf8_byte_end)
                for row in (*witness.semantic_atoms, *witness.reception_bindings)
            )
        )
        for row in (*witness.semantic_atoms, *witness.reception_bindings):
            _assert_body_span(
                body, row, "STEP11_RC0031_P3_FINAL_SPAN_INVALID"
            )
        _closed_assert(
            0 < len(body) <= 1_000_000
            and witness.schema_version
            == api["STEP11_RC0031_EXPERIMENT_PARSED_WITNESS_SCHEMA"]
            and witness.body_sha256 == hashlib.sha256(body).hexdigest()
            and witness.experiment_catalog_sha256 == catalog_sha256
            and witness.base_prefix_commitments
            == expected_base_prefix_commitments
            and witness.body_scan_pass_count == 2
            and witness.decomposition_locus_count <= 38
            and witness.evaluated_decomposition_count <= 76
            and witness.peak_stored_decomposition_count <= 2
            and witness.body_free_export_allowed is False
            and binding.schema_version
            == api["STEP11_RC0031_EXPERIMENT_VERIFIED_BINDING_SCHEMA"]
            and binding.parsed_witness_sha256
            == _inverse_module().artifact_sha256(expected_witness_material)
            and binding.base_witness_sha256 == base_witness_sha256
            and binding.successor_snapshot_sha256
            == successor_snapshot_sha256
            and binding.source_authority_sha256
            == source_authority_sha256
            and binding.experiment_catalog_sha256 == catalog_sha256
            and binding.unique_solution_count == 1
            and binding.hard_verified is True
            and binding.semantic_coverage_authorized is False
            and binding.issue_codes == ()
            and binding.body_free_export_allowed is False
            and source_comparison_count
            + len(parsed_rows)
            + len(binding.reception_bindings)
            <= binding.owner_binding_comparison_count
            <= 576
            and len(witness.semantic_atoms) + len(reuse_rows)
            == len(source_ids)
            and len(witness.reception_bindings)
            == len(expected_receptions_by_source)
            and len(binding.reception_bindings)
            == len(expected_receptions_by_source)
            and binding.reception_binding_count
            == len(binding.reception_bindings)
            and len(witness_atoms_by_id) == len(witness.semantic_atoms)
            and len(parsed_receptions_by_id) == len(witness.reception_bindings)
            and all(
                left[1] <= right[0]
                for left, right in zip(ordered_spans, ordered_spans[1:])
            )
            and len(semantic_rows) == len(source_ids)
            and len(parsed_rows) + len(reuse_rows) == len(source_ids)
            and not (
                {row.source_atom_id for row in parsed_rows}
                & {row.source_atom_id for row in reuse_rows}
            )
            and {
                row.source_atom_id for row in semantic_rows
            }
            == set(source_ids)
            and {row.parsed_atom_id for row in parsed_rows}
            == set(witness_atoms_by_id)
            and all(
                row.semantic_family
                == semantic_by_source[row.source_atom_id][0]
                == witness_atoms_by_id[row.parsed_atom_id].semantic_family
                and _parsed_owner_matches_source(
                    witness_atoms_by_id[row.parsed_atom_id],
                    semantic_by_source[row.source_atom_id],
                )
                and row.match_basis == _FINAL_MATCH_BASIS[row.semantic_family]
                for row in parsed_rows
            )
            and {
                row.source_reception_opportunity_id
                for row in binding.reception_bindings
            }
            == set(expected_receptions_by_source)
            and {
                row.parsed_binding_id for row in binding.reception_bindings
            }
            == set(parsed_receptions_by_id)
            and all(
                row.source_scope
                == expected_receptions_by_source[
                    row.source_reception_opportunity_id
                ][0]
                and row.reception_act
                == expected_receptions_by_source[
                    row.source_reception_opportunity_id
                ][1]
                == parsed_receptions_by_id[
                    row.parsed_binding_id
                ].reception_act
                and row.reception_line_ordinal
                == expected_receptions_by_source[
                    row.source_reception_opportunity_id
                ][4]
                == parsed_receptions_by_id[
                    row.parsed_binding_id
                ].reception_line_ordinal
                and row.move_ordinal
                == expected_receptions_by_source[
                    row.source_reception_opportunity_id
                ][5]
                == parsed_receptions_by_id[row.parsed_binding_id].move_ordinal
                and parsed_receptions_by_id[
                    row.parsed_binding_id
                ].target_expression
                == joiner.join(
                    expected_receptions_by_source[
                        row.source_reception_opportunity_id
                    ][2]
                )
                and parsed_receptions_by_id[
                    row.parsed_binding_id
                ].target_expression_sha256
                == hashlib.sha256(
                    parsed_receptions_by_id[
                        row.parsed_binding_id
                    ].target_expression.encode("utf-8")
                ).hexdigest()
                and parsed_receptions_by_id[
                    row.parsed_binding_id
                ].supporting_expression
                == (
                    joiner.join(
                        expected_receptions_by_source[
                            row.source_reception_opportunity_id
                        ][3]
                    )
                    if expected_receptions_by_source[
                        row.source_reception_opportunity_id
                    ][3]
                    else None
                )
                and parsed_receptions_by_id[
                    row.parsed_binding_id
                ].supporting_expression_sha256
                == (
                    hashlib.sha256(
                        parsed_receptions_by_id[
                            row.parsed_binding_id
                        ].supporting_expression.encode("utf-8")
                    ).hexdigest()
                    if parsed_receptions_by_id[
                        row.parsed_binding_id
                    ].supporting_expression
                    is not None
                    else None
                )
                and row.target_owner_count
                == len(
                    expected_receptions_by_source[
                        row.source_reception_opportunity_id
                    ][2]
                )
                and row.supporting_owner_count
                == len(
                    expected_receptions_by_source[
                        row.source_reception_opportunity_id
                    ][3]
                )
                and row.association_basis
                == expected_receptions_by_source[
                    row.source_reception_opportunity_id
                ][6]
                for row in binding.reception_bindings
            )
            and all(
                (row.parsed_atom_id is None)
                ^ (row.verified_reuse_binding_sha256 is None)
                for row in semantic_rows
            )
            and not (_all_mapping_keys(witness_material) & _FORBIDDEN_BODY_KEYS)
            and not (_all_mapping_keys(binding_material) & _FORBIDDEN_BODY_KEYS)
            and witness_material == expected_witness_material
            and binding_material == expected_binding_material
            and _material_is_body_free(witness_material)
            and _material_is_body_free(binding_material)
            and not _material_contains_body_encoding(witness_material, body)
            and not _material_contains_body_encoding(binding_material, body)
            and body.decode("utf-8", errors="strict")
            not in repr(witness_material)
            and body.decode("utf-8", errors="strict")
            not in repr(binding_material),
            "STEP11_RC0031_P3_FINAL_ROUND_TRIP_INVALID",
        )
        parsed_total += len(parsed_rows)
        reuse_total += len(reuse_rows)
        reception_total += len(binding.reception_bindings)
        second_witness = parser(body)
        second_binding = _call_rc0031_final_matcher(
            api, second_witness, context
        )
        _closed_assert(
            witness == second_witness and binding == second_binding,
            "STEP11_RC0031_P3_FINAL_DETERMINISM_INVALID",
        )
        deterministic_count += 1
    _assert_no_captured_output(
        capsys, "STEP11_RC0031_P3_FINAL_INVERSE_BODY_OUTPUT_LEAK"
    )
    _closed_assert(
        deterministic_count == 10
        and (parsed_total, reuse_total, reception_total) == (38, 1, 11),
        "STEP11_RC0031_P3_FINAL_DENOMINATOR_DRIFT",
    )


def test_rc0031_p3_0001_final_rederives_reuse_and_source_xor_without_forward_claim(
    capsys: Any,
) -> None:
    api = _rc0031_final_inverse_api_or_red()
    context = next(
        row
        for row in _rc0031_final_candidate_contexts()
        if row[0] == "nls3s_b001_0001"
    )
    (
        _case_id,
        baseline,
        successor,
        _lexical,
        candidate,
        base_witness,
    ) = context
    witness = api["parse_step11_rc0031_experiment_surface"](
        candidate.final_utf8_bytes
    )
    binding = _call_rc0031_final_matcher(api, witness, context)
    expected_source_ids = tuple(
        _independent_rc0031_source_projection(context)[0]
    )
    parsed_source_ids = tuple(
        row.source_atom_id
        for row in binding.semantic_bindings
        if row.parsed_atom_id is not None
    )
    reuse_rows = tuple(
        row
        for row in binding.semantic_bindings
        if row.verified_reuse_binding_sha256 is not None
    )
    discourse_plan, _base_binding = _independent_base_plan_binding(
        baseline, base_witness
    )
    expected_proof = _inverse_module().match_step11_rc0030_base_body_exact_reuse(
        base_witness,
        successor_snapshot=successor,
        inventory_result=baseline.inventory_result,
        content_plan=baseline.content_plan,
        discourse_plan=discourse_plan,
        current_input=baseline.projected_current_input,
    )
    expected_material = (
        _inverse_module().step11_rc0030_verified_base_body_reuse_material(
            expected_proof[0]
        )
    )
    _closed_assert(
        len(witness.semantic_atoms) == 0
        and len(witness.reception_bindings) == 1
        and parsed_source_ids == ()
        and len(expected_proof) == 1
        and _material_is_body_free(expected_material)
        and len(reuse_rows) == 1
        and reuse_rows[0].source_atom_id == _EXPECTED_REUSE_SOURCE_ID
        == expected_proof[0].source_atom_id
        and reuse_rows[0].semantic_family
        == expected_proof[0].semantic_family
        and reuse_rows[0].match_basis == expected_proof[0].match_basis
        and reuse_rows[0].parsed_atom_id is None
        and type(reuse_rows[0].verified_reuse_binding_sha256) is str
        and re.fullmatch(
            r"[0-9a-f]{64}", reuse_rows[0].verified_reuse_binding_sha256
        )
        is not None
        and reuse_rows[0].verified_reuse_binding_sha256
        == expected_proof[0].independent_binding_sha256
        and tuple(row.source_atom_id for row in reuse_rows)
        == expected_source_ids
        and candidate.rendered_surface.semantic_atom_count == 0
        and candidate.rendered_surface.exact_reuse_count == 1
        and not candidate.surface_realization_plan.proposition_clause_bindings,
        "STEP11_RC0031_P3_FINAL_0001_REUSE_XOR_INVALID",
    )
    with pytest.raises(TypeError):
        _call_rc0031_final_matcher(
            api,
            witness,
            context,
            verified_base_reuse_bindings=(
                candidate
                .surface_realization_plan
                .base_body_exact_reuse_bindings
            ),
        )
    _assert_no_captured_output(
        capsys, "STEP11_RC0031_P3_FINAL_INVERSE_BODY_OUTPUT_LEAK"
    )


def test_rc0031_p3_parser_rejects_forward_metadata_hidden_markers_utf8_and_bounds(
    capsys: Any,
    monkeypatch: Any,
) -> None:
    api = _rc0031_final_inverse_api_or_red()
    parser = api["parse_step11_rc0031_experiment_surface"]
    context = _rc0031_final_candidate_contexts()[0]
    body = context[4].final_utf8_bytes
    for kwargs in (
        {"candidate": context[4]},
        {"candidate_metadata": {}},
        {"covered_obligation_ids": ()},
        {"generator_span_map": ()},
        {"gate_status": "pass"},
        {"soft_score": 1.0},
    ):
        with pytest.raises(TypeError):
            parser(body, **kwargs)
    nfd_body = unicodedata.normalize(
        "NFD", body.decode("utf-8")
    ).encode("utf-8")
    invalid_bodies = (
        None,
        bytearray(body),
        b"",
        b"x" * 1_000_000,
        b"x" * 1_000_001,
        (b"x," * 499_999) + b"x",
        b"\xff",
        b"\xef\xbb\xbf" + body,
        body + b"\n",
        body.replace(b"\n", b"\r\n", 1),
        body + "\u200b".encode("utf-8"),
        "か\u3099".encode("utf-8") + body,
        body + b"\ncovered_obligation_ids",
    ) + ((nfd_body,) if nfd_body != body else ())
    for malformed in invalid_bodies:
        _expect_rc0031_inverse_error(
            api,
            lambda value=malformed: parser(value),
            capsys=capsys,
            failure_code="STEP11_RC0031_P3_FINAL_PARSER_ATTACK_ACCEPTED",
        )

    catalog, _catalog_sha256 = _rc0031_catalog_authority()
    registry = catalog["unknown_predicate_fragments"]
    mutation_key = sorted(registry)[0]
    monkeypatch.setitem(
        registry,
        mutation_key,
        registry[mutation_key] + "x",
    )
    _expect_rc0031_inverse_error(
        api,
        lambda: parser(body),
        capsys=capsys,
        failure_code="STEP11_RC0031_P3_FINAL_CATALOG_MUTATION_ACCEPTED",
        expected_code="STEP11_RC0031_CATALOG_COMMITMENT_MISMATCH",
    )


def test_rc0031_p3_renderer_mutation_and_generator_metadata_are_differentially_isolated(
    capsys: Any,
    monkeypatch: Any,
) -> None:
    api = _rc0031_final_inverse_api_or_red()
    context = _rc0031_final_candidate_contexts()[0]
    body = context[4].final_utf8_bytes
    first_witness = api["parse_step11_rc0031_experiment_surface"](body)
    first_binding = _call_rc0031_final_matcher(
        api, first_witness, context
    )
    surface = _surface_module()

    def renderer_mutation(*_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError(
            "STEP11_RC0031_P3_INVERSE_CALLED_FORWARD_RENDERER"
        )

    for name in dir(surface):
        if (
            name.startswith("_step11_rc0031_")
            or name == "build_step11_rc0031_experiment_surface_candidates"
        ) and callable(getattr(surface, name)):
            monkeypatch.setattr(surface, name, renderer_mutation)
    second_witness = api["parse_step11_rc0031_experiment_surface"](body)
    second_binding = _call_rc0031_final_matcher(
        api, second_witness, context
    )
    _closed_assert(
        first_witness == second_witness
        and first_binding == second_binding,
        "STEP11_RC0031_P3_FORWARD_INVERSE_DIFFERENTIAL_INVALID",
    )
    _assert_no_captured_output(
        capsys, "STEP11_RC0031_P3_FINAL_INVERSE_BODY_OUTPUT_LEAK"
    )


def test_rc0031_p3_rehashed_witness_base_and_source_authority_attacks_fail_closed(
    capsys: Any,
    monkeypatch: Any,
) -> None:
    api = _rc0031_final_inverse_api_or_red()
    parser = api["parse_step11_rc0031_experiment_surface"]
    contexts = _rc0031_final_candidate_contexts()
    primary = next(row for row in contexts if row[0] == "nls3s_b001_0035")
    foreign = next(row for row in contexts if row[0] == "nls3s_b001_0002")
    body = primary[4].final_utf8_bytes
    witness = parser(body)
    first_binding = _call_rc0031_final_matcher(api, witness, primary)
    second_binding = _call_rc0031_final_matcher(api, witness, primary)
    _closed_assert(
        first_binding == second_binding,
        "STEP11_RC0031_P3_FINAL_WITNESS_NOT_IDEMPOTENT",
    )
    forged_atom = replace(witness.semantic_atoms[0])
    forged_witnesses = (
        replace(witness),
        replace(witness, body_sha256="f" * 64),
        replace(witness, semantic_atoms=tuple(reversed(witness.semantic_atoms))),
        replace(
            witness,
            semantic_atoms=(forged_atom, *witness.semantic_atoms[1:]),
        ),
        replace(
            witness,
            experiment_catalog_sha256="e" * 64,
        ),
    )
    for forged in forged_witnesses:
        _expect_rc0031_inverse_error(
            api,
            lambda value=forged: _call_rc0031_final_matcher(
                api, value, primary
            ),
            capsys=capsys,
            failure_code="STEP11_RC0031_P3_FINAL_WITNESS_FORGERY_ACCEPTED",
        )

    for forged_base in (
        replace(primary[5]),
        replace(primary[5], body_sha256="d" * 64),
    ):
        attack_context = (*primary[:5], forged_base)
        fresh_witness = parser(body)
        _expect_rc0031_inverse_error(
            api,
            lambda value=attack_context: _call_rc0031_final_matcher(
                api, fresh_witness, value
            ),
            capsys=capsys,
            failure_code="STEP11_RC0031_P3_FINAL_AUTHORITY_FORGERY_ACCEPTED",
        )

    primary_baseline = primary[1]
    foreign_baseline = foreign[1]
    matcher = api["match_step11_rc0031_experiment_surface"]
    parent_attacks = (
        {
            "base_body_witness": foreign[5],
            "successor_snapshot": primary[2],
            "inventory_result": primary_baseline.inventory_result,
            "content_plan": primary_baseline.content_plan,
            "discourse_plan_set": primary_baseline.discourse_plan_set,
            "current_input": primary_baseline.projected_current_input,
        },
        {
            "base_body_witness": primary[5],
            "successor_snapshot": foreign[2],
            "inventory_result": primary_baseline.inventory_result,
            "content_plan": primary_baseline.content_plan,
            "discourse_plan_set": primary_baseline.discourse_plan_set,
            "current_input": primary_baseline.projected_current_input,
        },
        {
            "base_body_witness": primary[5],
            "successor_snapshot": primary[2],
            "inventory_result": foreign_baseline.inventory_result,
            "content_plan": primary_baseline.content_plan,
            "discourse_plan_set": primary_baseline.discourse_plan_set,
            "current_input": primary_baseline.projected_current_input,
        },
        {
            "base_body_witness": primary[5],
            "successor_snapshot": primary[2],
            "inventory_result": primary_baseline.inventory_result,
            "content_plan": foreign_baseline.content_plan,
            "discourse_plan_set": primary_baseline.discourse_plan_set,
            "current_input": primary_baseline.projected_current_input,
        },
        {
            "base_body_witness": primary[5],
            "successor_snapshot": primary[2],
            "inventory_result": primary_baseline.inventory_result,
            "content_plan": primary_baseline.content_plan,
            "discourse_plan_set": foreign_baseline.discourse_plan_set,
            "current_input": primary_baseline.projected_current_input,
        },
        {
            "base_body_witness": primary[5],
            "successor_snapshot": primary[2],
            "inventory_result": primary_baseline.inventory_result,
            "content_plan": primary_baseline.content_plan,
            "discourse_plan_set": primary_baseline.discourse_plan_set,
            "current_input": foreign_baseline.projected_current_input,
        },
    )
    for attack in parent_attacks:
        fresh_witness = parser(body)
        _expect_rc0031_inverse_error(
            api,
            lambda value=attack: matcher(fresh_witness, **value),
            capsys=capsys,
            failure_code="STEP11_RC0031_P3_FINAL_AUTHORITY_FORGERY_ACCEPTED",
        )

    inverse = _inverse_module()
    original_records = inverse._step11_rc0030_validated_source_records

    def without_semantic_records(*args: Any, **kwargs: Any) -> tuple[Any, ...]:
        result = original_records(*args, **kwargs)
        return ((), *result[1:])

    monkeypatch.setattr(
        inverse,
        "_step11_rc0030_validated_source_records",
        without_semantic_records,
    )
    _expect_rc0031_inverse_error(
        api,
        lambda: _call_rc0031_final_matcher(api, parser(body), primary),
        capsys=capsys,
        failure_code="STEP11_RC0031_P3_FINAL_ZERO_BINDING_NOT_CLOSED",
        expected_code="STEP11_RC0031_NO_SEMANTIC_BINDING",
    )
    monkeypatch.setattr(
        inverse,
        "_step11_rc0030_validated_source_records",
        original_records,
    )

    def duplicate_semantic_records(
        *args: Any, **kwargs: Any
    ) -> tuple[Any, ...]:
        result = original_records(*args, **kwargs)
        records = result[0]
        ambiguous = (
            records[0],
            (records[1][0], *records[0][1:]),
            *records[2:],
        )
        return (ambiguous, *result[1:])

    monkeypatch.setattr(
        inverse,
        "_step11_rc0030_validated_source_records",
        duplicate_semantic_records,
    )
    _expect_rc0031_inverse_error(
        api,
        lambda: _call_rc0031_final_matcher(api, parser(body), primary),
        capsys=capsys,
        failure_code="STEP11_RC0031_P3_FINAL_AMBIGUOUS_BINDING_NOT_CLOSED",
        expected_code="STEP11_RC0031_AMBIGUOUS_SEMANTIC_BINDING",
    )


def test_rc0031_p3_relation_distribution_reception_and_reuse_body_mutations_fail_closed_and_private(
    capsys: Any,
) -> None:
    api = _rc0031_final_inverse_api_or_red()
    parser = api["parse_step11_rc0031_experiment_surface"]
    error_type = api["Step11Rc0031ExperimentInverseSurfaceError"]
    parsed_contexts: list[tuple[tuple[Any, ...], Any]] = []
    for context in _rc0031_final_candidate_contexts():
        parsed_contexts.append(
            (context, parser(context[4].final_utf8_bytes))
        )
    semantic_context, semantic_witness = next(
        row for row in parsed_contexts if len(row[1].semantic_atoms) >= 2
    )
    reception_context, reception_witness = next(
        row for row in parsed_contexts if row[1].reception_bindings
    )
    donor_context, donor_witness = next(
        row
        for row in parsed_contexts
        if row[0] is not semantic_context and row[1].semantic_atoms
    )
    semantic_body = semantic_context[4].final_utf8_bytes
    reception_body = reception_context[4].final_utf8_bytes
    donor_body = donor_context[4].final_utf8_bytes
    first, second = sorted(
        semantic_witness.semantic_atoms[:2],
        key=lambda row: row.utf8_byte_start,
    )
    first_span = semantic_body[first.utf8_byte_start : first.utf8_byte_end]
    second_span = semantic_body[second.utf8_byte_start : second.utf8_byte_end]
    donor = donor_witness.semantic_atoms[0]
    donor_span = donor_body[donor.utf8_byte_start : donor.utf8_byte_end]
    reception = reception_witness.reception_bindings[0]
    reception_span = reception_body[
        reception.utf8_byte_start : reception.utf8_byte_end
    ]
    swapped = (
        semantic_body[: first.utf8_byte_start]
        + second_span
        + semantic_body[first.utf8_byte_end : second.utf8_byte_start]
        + first_span
        + semantic_body[second.utf8_byte_end :]
    )
    reuse_context, _reuse_witness = next(
        row for row in parsed_contexts if row[0][0] == "nls3s_b001_0001"
    )
    reuse_body = reuse_context[4].final_utf8_bytes
    observation_prefix = "見えたこと：\n".encode("utf-8")
    section_separator = "\n\nEmlisから：\n".encode("utf-8")
    observation = reuse_body[
        len(observation_prefix) : reuse_body.index(section_separator)
    ]
    mutations = (
        (
            _replace_body_span(semantic_body, first, b""),
            semantic_context,
        ),
        (
            _replace_body_span(semantic_body, first, first_span + first_span),
            semantic_context,
        ),
        (swapped, semantic_context),
        (
            _replace_body_span(semantic_body, first, donor_span),
            semantic_context,
        ),
        (
            _replace_body_span(reception_body, reception, b""),
            reception_context,
        ),
        (
            _replace_body_span(
                reception_body,
                reception,
                reception_span + reception_span,
            ),
            reception_context,
        ),
        (
            reuse_body.replace(
                section_separator,
                b"\n" + observation + section_separator,
                1,
            ),
            reuse_context,
        ),
    )
    matcher_only_mutations: list[
        tuple[bytes, tuple[Any, ...], str]
    ] = []
    for context, _parsed in parsed_contexts:
        body = context[4].final_utf8_bytes
        semantic_by_source, reception_by_source, *_commitments = (
            _independent_rc0031_source_projection(context)
        )
        for family, key, direction, owners in semantic_by_source.values():
            if (
                family not in {"relation", "semantic_link"}
                or direction != "source_to_target"
                or len(owners) != 2
                or owners[0] == owners[1]
            ):
                continue
            original = _render_rc0031_source_clause_for_attack(
                family=family,
                key=key,
                direction=direction,
                owner_expressions=owners,
            ).encode("utf-8")
            if body.count(original) != 1:
                continue
            swapped_clause = _render_rc0031_source_clause_for_attack(
                family=family,
                key=key,
                direction=direction,
                owner_expressions=tuple(reversed(owners)),
            ).encode("utf-8")
            matcher_only_mutations.append(
                (
                    body.replace(original, swapped_clause, 1),
                    context,
                    "STEP11_RC0031_NO_SEMANTIC_BINDING",
                )
            )
            catalog, _catalog_sha256 = _rc0031_catalog_authority()
            registry = (
                catalog["relation_predicate_fragments"]
                if family == "relation"
                else catalog["semantic_link_predicate_fragments"]
            )
            alternate = next(
                row.rsplit(":", 1)[0]
                for row in sorted(registry)
                if row.endswith(":" + direction)
                and row.rsplit(":", 1)[0] != key
            )
            alternate_clause = _render_rc0031_source_clause_for_attack(
                family=family,
                key=alternate,
                direction=direction,
                owner_expressions=owners,
            ).encode("utf-8")
            matcher_only_mutations.append(
                (
                    body.replace(original, alternate_clause, 1),
                    context,
                    "STEP11_RC0031_NO_SEMANTIC_BINDING",
                )
            )
            break
        owner_pool = tuple(
            dict.fromkeys(
                owner
                for _family, _key, _direction, owners
                in semantic_by_source.values()
                for owner in owners
            )
        )
        for expected_reception in reception_by_source.values():
            original = _render_rc0031_reception_for_attack(
                expected_reception
            ).encode("utf-8")
            donor = next(
                (
                    row
                    for row in owner_pool
                    if row
                    not in {
                        *expected_reception[2],
                        *expected_reception[3],
                    }
                    and not any(
                        marker in row
                        for marker in (
                            "\r",
                            "\n",
                            "「",
                            "」",
                            "、",
                            "。",
                            "！",
                            "？",
                            "!",
                            "?",
                        )
                    )
                ),
                None,
            )
            if body.count(original) != 1 or donor is None:
                continue
            altered_reception = (
                expected_reception[0],
                expected_reception[1],
                (donor, *expected_reception[2][1:]),
                expected_reception[3],
                *expected_reception[4:],
            )
            replacement = _render_rc0031_reception_for_attack(
                altered_reception
            ).encode("utf-8")
            matcher_only_mutations.append(
                (
                    body.replace(original, replacement, 1),
                    context,
                    "STEP11_RC0031_NO_RECEPTION_BINDING",
                )
            )
            break
        if len(matcher_only_mutations) >= 3:
            break
    _closed_assert(
        len({hashlib.sha256(row[0]).hexdigest() for row in mutations})
        == len(mutations)
        and all(row[0] != row[1][4].final_utf8_bytes for row in mutations),
        "STEP11_RC0031_P3_FINAL_MUTATION_DENOMINATOR_INVALID",
    )
    _closed_assert(
        len(matcher_only_mutations) >= 3
        and len(
            {
                hashlib.sha256(row[0]).hexdigest()
                for row in matcher_only_mutations
            }
        )
        == len(matcher_only_mutations),
        "STEP11_RC0031_P3_FINAL_MATCHER_MUTATION_DENOMINATOR_INVALID",
    )
    for mutated_body, context in mutations:
        try:
            mutated_witness = parser(mutated_body)
            _call_rc0031_final_matcher(api, mutated_witness, context)
        except error_type as exc:
            _assert_rc0031_inverse_error_is_body_free(
                exc,
                error_type,
                capsys=capsys,
                failure_code=(
                    "STEP11_RC0031_P3_FINAL_MUTATION_ERROR_INVALID"
                ),
            )
        except Exception:
            _assert_no_captured_output(
                capsys, "STEP11_RC0031_P3_FINAL_INVERSE_BODY_OUTPUT_LEAK"
            )
            pytest.fail(
                "STEP11_RC0031_P3_FINAL_MUTATION_ERROR_INVALID",
                pytrace=False,
            )
        else:
            _assert_no_captured_output(
                capsys, "STEP11_RC0031_P3_FINAL_INVERSE_BODY_OUTPUT_LEAK"
            )
            pytest.fail(
                "STEP11_RC0031_P3_FINAL_BODY_MUTATION_ACCEPTED",
                pytrace=False,
            )
    for mutated_body, context, expected_code in matcher_only_mutations:
        try:
            mutated_witness = parser(mutated_body)
        except Exception:
            _assert_no_captured_output(
                capsys, "STEP11_RC0031_P3_FINAL_INVERSE_BODY_OUTPUT_LEAK"
            )
            pytest.fail(
                "STEP11_RC0031_P3_FINAL_VALID_GRAMMAR_MUTATION_REJECTED",
                pytrace=False,
            )
        _expect_rc0031_inverse_error(
            api,
            lambda value=mutated_witness, authority=context: (
                _call_rc0031_final_matcher(api, value, authority)
            ),
            capsys=capsys,
            failure_code=(
                "STEP11_RC0031_P3_FINAL_VALID_GRAMMAR_MUTATION_ACCEPTED"
            ),
            expected_code=expected_code,
        )
