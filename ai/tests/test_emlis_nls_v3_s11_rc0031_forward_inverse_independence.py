# -*- coding: utf-8 -*-
from __future__ import annotations

"""P3 pre-freeze RED for the rc0031 final body inverse.

Production is intentionally unchanged.  The suite retains the exact10 GREEN
composition contract, proves that the current Step8 body-dimension projection
is non-injective before schema freeze, and counts exact-one source solutions by
body-relevant verified projection rather than discourse-plan identity.  It
also proves, without adopting it in production, that a closed prefix-free
Surface dimension lattice and a source-authoritative topic projection can make
the missing dimensions injective.  It specifies provisional body-only Parser /
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
from itertools import product
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
    _GATE_PATH: (
        208_041,
        "88514bb2a179e8d726f36e1666d2618330d95979107403ededc93aa35655943b",
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
_LEXICAL_PREDECESSOR_BYTES = 129_615
_LEXICAL_PREDECESSOR_SHA256 = (
    "592f3ab7c90831c3191f51e9e7dd9a1f8c3fe4add1fd31bba9fdc65dccaecc28"
)
_LEXICAL_APPEND_BYTE_MAX = 32_768
_LEXICAL_APPEND_MARKER = (
    b"# rc0031 experiment-only Product owner projection "
    b"(append-only B5 owner)"
)
_CATALOG_PREDECESSOR_BYTES = 19_951
_CATALOG_PREDECESSOR_SHA256 = (
    "a4e8bc9753a1398571d511d5d0c1219a886c498661b3a4f702d3b20b5672c6cc"
)
_CATALOG_APPEND_BYTE_MAX = 16_384
_CATALOG_APPEND_MARKER = (
    b"# rc0031 experiment-only body-dimension grammar (append-only P3 owner)"
)
_SURFACE_PREDECESSOR_BYTES = 485_490
_SURFACE_PREDECESSOR_SHA256 = (
    "ee2f4bc0ab260e8cf1ce2b87acf499e84712ed6b3e639a6a1a6a0141bd3ea520"
)
_SURFACE_APPEND_BYTE_MAX = 65_536
_SURFACE_APPEND_MARKER = (
    b"# rc0031 experiment-only dimension-bearing Surface successor "
    b"(append-only P3 owner)"
)
_SERVICE_PY_PATH_COUNT = 546
_SERVICE_PY_PATH_LIST_SHA256 = (
    "46db0d14852dde6ebb6012596234cbb935243b27ed227465d9e94876ce4f5d56"
)
_REPOSITORY_PY_FROZEN_FILE_COUNT = 1_530
_REPOSITORY_PY_FROZEN_MATERIAL_SHA256 = (
    "e349323507c8c5b798c7fe70f6776700f4384ad2207d152c2515f41a913e17ac"
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
_DIMENSION_RECOVERY_CONTRACT_SCHEMA = (
    "cocolon.emlis.nls_v3.step11.rc0031_body_dimension_recovery.v1"
)
_DIMENSION_RECOVERY_CONTRACT_EXPORT = (
    "STEP11_RC0031_EXPERIMENT_BODY_DIMENSION_RECOVERY_CONTRACT"
)
_DIMENSION_RECOVERY_VALIDATOR_EXPORT = (
    "validate_step11_rc0031_experiment_body_dimension_recovery_contract"
)
_DIMENSION_SURFACE_BUILDER_EXPORT = (
    "build_step11_rc0031_dimension_bearing_experiment_surface_candidate"
)
_DIMENSION_SURFACE_VALIDATOR_EXPORT = (
    "validate_step11_rc0031_dimension_bearing_experiment_surface_candidate"
)
_DIMENSION_SURFACE_SIGNATURE = (
    "value",
    "successor_snapshot",
    "lexical_atom_specs",
)
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
_PRELIMINARY_BODY_DIMENSION_FIELDS = (
    "observation_stage",
    "source_role",
    "polarity",
    "modality",
    "temporal_scope",
    "topic_fingerprint_sha256",
    "referent_scope",
)
_PROPOSED_CATALOG_DERIVED_DIMENSION_DOMAINS = {
    "observation_stage": ("normal_observation",),
    "source_role": ("original_input",),
}
_PROPOSED_VISIBLE_DIMENSION_ORDER = (
    "temporal_scope",
    "modality",
    "polarity",
    "referent_scope",
)
_PROPOSED_VISIBLE_DIMENSION_TOKENS = {
    "temporal_scope": {
        "current_input": "今の入力で",
        "reported_past": "過去から",
        "intended_future": "先の時点に向けて",
        "atemporal": "時点を限らず",
        "unknown": "時点を決めず",
    },
    "modality": {
        "observed": "見えている",
        "reported": "伝えられた",
        "intended": "これからに向けた",
        "possible": "可能性として示された",
        "unknown": "まだ確定しない",
    },
    "polarity": {
        "positive": "明るさを帯びた",
        "negative": "重さを帯びた",
        "mixed": "異なる向きをともに含む",
        "neutral": "どちらにも寄せない",
        "unknown": "向きをまだ定めない",
    },
    "referent_scope": {
        "self": "自分について",
        "other": "相手について",
        "event": "出来事について",
        "action": "行動について",
        "state": "状態について",
        "relation": "関係について",
        "unknown": "対象を決めず",
    },
}
_PROPOSED_VISIBLE_DIMENSION_CLOSE = "、"
_PROPOSED_TOPIC_FINGERPRINT_SCHEMA = (
    "cocolon.emlis.nls_v3.step11.rc0031_body_topic_projection.v1"
)
_FINAL_PARSED_ATOM_REQUIRED_FIELDS = frozenset(
    {
        "atom_id",
        "semantic_family",
        "semantic_key",
        "direction",
        *_PRELIMINARY_BODY_DIMENSION_FIELDS,
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
    *_PRELIMINARY_BODY_DIMENSION_FIELDS,
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


def _top_level_bound_names(tree: ast.Module) -> tuple[str, ...]:
    result: list[str] = []
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            result.append(node.name)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = (
                node.targets if isinstance(node, ast.Assign) else (node.target,)
            )
            result.extend(
                child.id
                for target in targets
                for child in ast.walk(target)
                if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store)
            )
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            result.extend(
                alias.asname or alias.name.split(".", 1)[0]
                for alias in node.names
            )
    return tuple(result)


def _rc0031_owner_append_is_closed(
    value: bytes,
    marker: bytes,
    predecessor: bytes,
    *,
    allowed_dynamic_imports: frozenset[str],
    allow_non_ascii_literals: bool,
) -> bool:
    if not value:
        return True
    try:
        text = value.decode("utf-8", errors="strict")
        tree = ast.parse(text)
        predecessor_tree = ast.parse(predecessor.decode("utf-8", errors="strict"))
    except (UnicodeError, SyntaxError):
        return False
    lines = value.lstrip(b"\n").splitlines()
    if not lines or lines[0] != marker:
        return False
    parent_by_id = {
        id(child): parent
        for parent in ast.walk(tree)
        for child in ast.iter_child_nodes(parent)
    }
    observed_dynamic_imports: set[str] = set()
    if any(
        token in text
        for token in (
            "nls3s_b001_",
            "expected_output",
            "review_family",
        )
    ):
        return False
    if any(
        isinstance(
            node,
            (
                ast.AsyncFunctionDef,
                ast.Await,
                ast.ClassDef,
                ast.Global,
                ast.Import,
                ast.ImportFrom,
                ast.Lambda,
                ast.NamedExpr,
                ast.Nonlocal,
                ast.While,
                ast.Yield,
                ast.YieldFrom,
            ),
        )
        for node in ast.walk(tree)
    ):
        return False
    append_bound_names = _top_level_bound_names(tree)
    predecessor_bound_names = frozenset(_top_level_bound_names(predecessor_tree))
    if (
        len(append_bound_names) != len(set(append_bound_names))
        or bool(set(append_bound_names) & predecessor_bound_names)
    ):
        return False
    if any(
        isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and (
            any(ord(char) < 32 and char not in "\t\n\r" for char in node.value)
            or (
                not allow_non_ascii_literals
                and any(ord(char) > 127 for char in node.value)
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
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and (
            node.id in _FORBIDDEN_RUNTIME_NAMES
            or (
                node.id.startswith("__")
                and node.id not in {"__all__", "__import__"}
            )
        ):
            return False
        if isinstance(node, ast.Name) and node.id == "__import__":
            parent = parent_by_id.get(id(node))
            if not (
                isinstance(parent, ast.Call)
                and parent.func is node
            ):
                return False
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            return False
        if isinstance(node, ast.Call):
            call_name = _ast_call_name(node)
            if call_name in {
                "breakpoint",
                "compile",
                "delattr",
                "eval",
                "exec",
                "getattr",
                "globals",
                "input",
                "locals",
                "open",
                "print",
                "setattr",
                "vars",
            }:
                return False
            if call_name == "__import__":
                if (
                    len(node.args) != 1
                    or node.keywords
                    or not isinstance(node.args[0], ast.Constant)
                    or type(node.args[0].value) is not str
                    or node.args[0].value not in allowed_dynamic_imports
                ):
                    return False
                observed_dynamic_imports.add(node.args[0].value)
        if isinstance(node, ast.FunctionDef) and (
            node.args.defaults
            or any(default is not None for default in node.args.kw_defaults)
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
        if isinstance(node, ast.FunctionDef):
            if "rc0031" not in node.name.lower():
                return False
            if node.decorator_list:
                return False
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = (
                node.targets if isinstance(node, ast.Assign) else (node.target,)
            )
            if not all(isinstance(target, ast.Name) for target in targets):
                return False
            assignment_value = node.value
            if assignment_value is None or any(
                isinstance(child, ast.Call)
                for child in ast.walk(assignment_value)
            ):
                return False
            names = {target.id for target in targets}
            if any(
                name == "__all__" or "rc0031" not in name.lower()
                for name in names
            ):
                return False
        elif isinstance(node, ast.AugAssign):
            if not (
                isinstance(node.target, ast.Name)
                and node.target.id == "__all__"
                and isinstance(node.op, ast.Add)
                and isinstance(node.value, (ast.List, ast.Tuple))
                and all(
                    isinstance(child, ast.Constant)
                    and type(child.value) is str
                    and child.value in append_bound_names
                    for child in node.value.elts
                )
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
    return observed_dynamic_imports == set(allowed_dynamic_imports)


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
            "observation_stage": row.observation_stage,
            "source_role": row.source_role,
            "polarity": row.polarity,
            "modality": row.modality,
            "temporal_scope": row.temporal_scope,
            "topic_fingerprint_sha256": row.topic_fingerprint_sha256,
            "referent_scope": row.referent_scope,
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


@lru_cache(maxsize=1)
def _proposed_visible_dimension_codewords() -> tuple[
    tuple[str, tuple[tuple[str, str], ...]], ...
]:
    value_domains = tuple(
        tuple(_PROPOSED_VISIBLE_DIMENSION_TOKENS[name])
        for name in _PROPOSED_VISIBLE_DIMENSION_ORDER
    )
    return tuple(
        (
            "".join(
                _PROPOSED_VISIBLE_DIMENSION_TOKENS[name][value]
                for name, value in zip(
                    _PROPOSED_VISIBLE_DIMENSION_ORDER,
                    values,
                )
            )
            + _PROPOSED_VISIBLE_DIMENSION_CLOSE,
            tuple(zip(_PROPOSED_VISIBLE_DIMENSION_ORDER, values)),
        )
        for values in product(*value_domains)
    )


def _proposed_visible_dimension_prefix(
    values: dict[str, str],
) -> str:
    if set(values) != set(_PROPOSED_VISIBLE_DIMENSION_ORDER):
        raise ValueError("STEP11_RC0031_P3_SURFACE_DIMENSION_INVALID")
    try:
        return (
            "".join(
                _PROPOSED_VISIBLE_DIMENSION_TOKENS[name][values[name]]
                for name in _PROPOSED_VISIBLE_DIMENSION_ORDER
            )
            + _PROPOSED_VISIBLE_DIMENSION_CLOSE
        )
    except (KeyError, TypeError):
        raise ValueError(
            "STEP11_RC0031_P3_SURFACE_DIMENSION_INVALID"
        ) from None


def _proposed_parse_visible_dimension_prefix(
    value: str,
) -> tuple[dict[str, str], str]:
    if type(value) is not str:
        raise ValueError("STEP11_RC0031_P3_SURFACE_DIMENSION_UNPARSEABLE")
    matches = tuple(
        (fields, value[len(prefix) :])
        for prefix, fields in _proposed_visible_dimension_codewords()
        if value.startswith(prefix)
    )
    if len(matches) != 1 or not matches[0][1]:
        raise ValueError("STEP11_RC0031_P3_SURFACE_DIMENSION_UNPARSEABLE")
    fields, remainder = matches[0]
    return dict(fields), remainder


def _proposed_topic_fingerprint(
    owner_expressions: tuple[str, ...],
) -> str:
    if (
        type(owner_expressions) is not tuple
        or not owner_expressions
        or any(type(row) is not str or not row for row in owner_expressions)
    ):
        raise ValueError("STEP11_RC0031_P3_TOPIC_PROJECTION_INVALID")
    material = {
        "schema_version": _PROPOSED_TOPIC_FINGERPRINT_SCHEMA,
        "owner_expression_sha256": [
            hashlib.sha256(row.encode("utf-8")).hexdigest()
            for row in owner_expressions
        ],
    }
    return hashlib.sha256(
        json.dumps(
            material,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _proposed_rc0031_source_dimension_projection(
    context: tuple[Any, ...],
) -> tuple[dict[str, Any], ...]:
    (
        _case_id,
        baseline,
        successor,
        _lexical_specs,
        _candidate,
        _base_body_witness,
    ) = context
    inverse = _inverse_module()
    snapshot = baseline.inventory_result.source_snapshot
    (
        records,
        _receptions,
        aliases,
        _successor_sha256,
        _source_authority_sha256,
        _exact_aliases,
    ) = inverse._step11_rc0030_validated_source_records(
        successor,
        inventory_result=baseline.inventory_result,
    )
    semantic_by_source = _independent_rc0031_source_projection(context)[0]
    relation_authority_by_id = {
        str(row.experiment_relation_id): row
        for row in successor.relation_construction_authority.relation_authorities
    }

    def nucleus_aliases(value: Any) -> frozenset[str]:
        return frozenset(
            {str(value.source_id), str(value.actual_source_id)}
        )

    def relation_parent(source_atom_id: str) -> Any:
        authority = relation_authority_by_id.get(source_atom_id)
        if authority is None:
            raise ValueError(
                "STEP11_RC0031_P3_SOURCE_DIMENSION_AUTHORITY_INVALID"
            )
        identity_aliases = {str(authority.source_relation_id)}
        if authority.refines_source_relation_id is not None:
            identity_aliases.add(str(authority.refines_source_relation_id))
        matches = tuple(
            row
            for row in snapshot.relations
            if identity_aliases
            & {str(row.source_id), str(row.actual_source_id)}
        )
        if not matches:
            direct_aliases = {
                *identity_aliases,
                *(str(row) for row in authority.source_relation_ids),
            }
            matches = tuple(
                row
                for row in snapshot.relations
                if direct_aliases
                & {
                    str(row.source_id),
                    str(row.actual_source_id),
                    *(str(value) for value in row.source_relation_ids),
                }
            )
        if len(matches) != 1:
            raise ValueError(
                "STEP11_RC0031_P3_SOURCE_DIMENSION_AUTHORITY_INVALID"
            )
        return matches[0]

    result: list[dict[str, Any]] = []
    for source_atom_id, family, key, direction, owner_ids in records:
        referent_scope: str
        if family == "construction":
            if len(owner_ids) != 1 or owner_ids[0] not in aliases:
                raise ValueError(
                    "STEP11_RC0031_P3_SOURCE_DIMENSION_AUTHORITY_INVALID"
                )
            owner_aliases = aliases[owner_ids[0]]
            matches = tuple(
                row
                for row in snapshot.nuclei
                if nucleus_aliases(row) & owner_aliases
            )
            if len(matches) != 1:
                raise ValueError(
                    "STEP11_RC0031_P3_SOURCE_DIMENSION_AUTHORITY_INVALID"
                )
            source = matches[0]
            referent_scope = str(source.referent_scope)
        elif family == "relation":
            source = relation_parent(source_atom_id)
            referent_scope = "relation"
        elif family == "semantic_link":
            matches = tuple(
                row
                for row in snapshot.relations
                if source_atom_id
                in {str(row.source_id), str(row.actual_source_id)}
            )
            if len(matches) != 1:
                raise ValueError(
                    "STEP11_RC0031_P3_SOURCE_DIMENSION_AUTHORITY_INVALID"
                )
            source = matches[0]
            referent_scope = "relation"
        elif family == "explicit_unknown":
            matches = tuple(
                row
                for row in snapshot.unknowns
                if source_atom_id
                in {str(row.source_id), str(row.actual_source_id)}
            )
            if len(matches) != 1:
                raise ValueError(
                    "STEP11_RC0031_P3_SOURCE_DIMENSION_AUTHORITY_INVALID"
                )
            source = matches[0]
            referent_scope = "unknown"
        else:
            raise ValueError(
                "STEP11_RC0031_P3_SOURCE_DIMENSION_AUTHORITY_INVALID"
            )
        owner_expressions = semantic_by_source[source_atom_id][3]
        is_unknown = family == "explicit_unknown"
        result.append(
            {
                "source_atom_id": source_atom_id,
                "semantic_family": family,
                "semantic_key": key,
                "direction": direction,
                "owner_expressions": owner_expressions,
                "observation_stage": str(snapshot.observation_stage),
                "source_role": str(source.source_role),
                "polarity": (
                    "unknown" if is_unknown else str(source.polarity)
                ),
                "modality": (
                    "unknown" if is_unknown else str(source.modality)
                ),
                "temporal_scope": (
                    "unknown" if is_unknown else str(source.temporal_scope)
                ),
                "topic_scope_ids": tuple(
                    str(row) for row in source.topic_scope_ids
                ),
                "topic_fingerprint_sha256": (
                    _proposed_topic_fingerprint(owner_expressions)
                ),
                "referent_scope": referent_scope,
                "base_exact_reuse": (
                    source_atom_id == _EXPECTED_REUSE_SOURCE_ID
                ),
            }
        )
    return tuple(result)


def _independent_rc0031_source_projection(
    context: tuple[Any, ...],
    *,
    plan_solutions: tuple[tuple[dict[str, Any], Any], ...] | None = None,
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
    if plan_solutions is None:
        plan_solutions = _independent_base_plan_solutions(
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
    catalog, _catalog_sha256 = _rc0031_catalog_authority()
    joiner = catalog["clause_morphology"]["target_owner_join"]
    projections: list[
        tuple[
            dict[str, tuple[str, str, str, tuple[str, ...]]],
            dict[
                str,
                tuple[
                    str,
                    str,
                    tuple[str, ...],
                    tuple[str, ...],
                    int,
                    int,
                    str,
                ],
            ],
            int,
        ]
    ] = []
    for discourse_plan, base_binding in plan_solutions:
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
        projections.append(
            (semantic_by_source, reception_by_source, comparison_count)
        )
    projection_material = {
        json.dumps(
            {
                "semantic_by_source": semantic_by_source,
                "reception_by_source": reception_by_source,
            },
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
        for semantic_by_source, reception_by_source, _count in projections
    }
    _closed_assert(
        len(projection_material) == 1
        and len({row[2] for row in projections}) == 1,
        "STEP11_RC0031_P3_SOURCE_PLAN_SOLUTION_AMBIGUOUS",
    )
    semantic_by_source, reception_by_source, comparison_count = projections[0]
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


def _body_relevant_base_solution_material(
    base_witness: Any,
    binding: Any,
) -> dict[str, Any]:
    inverse = _inverse_module()
    material = dict(inverse._binding_material(binding))
    material.pop("discourse_plan_sha256", None)
    atom_by_id = {row.atom_id: row for row in base_witness.atoms}
    bound_atom_ids = tuple(
        sorted(
            {
                atom_id
                for binding_row in binding.binding_rows
                for atom_id in binding_row.atom_ids
            }
        )
    )
    _closed_assert(
        set(bound_atom_ids) <= set(atom_by_id),
        "STEP11_RC0031_P3_SOURCE_PLAN_PROJECTION_INVALID",
    )
    material["body_relevant_placements"] = [
        {
            "atom_id": atom_id,
            "section_role": atom_by_id[atom_id].section_role,
            "sentence_ordinal": atom_by_id[atom_id].sentence_ordinal,
            "grammatical_chunk_ordinal": (
                atom_by_id[atom_id].grammatical_chunk_ordinal
            ),
            "clause_ordinal": atom_by_id[atom_id].clause_ordinal,
        }
        for atom_id in bound_atom_ids
    ]
    return material


def _independent_base_plan_solutions(
    baseline: Any,
    base_body_witness: Any,
) -> tuple[tuple[dict[str, Any], Any], ...]:
    inverse = _inverse_module()
    planner = importlib.import_module("emlis_ai_discourse_graph_planner_v3")
    _closed_assert(
        planner.validate_discourse_graph_plan_set(
            baseline.discourse_plan_set,
            inventory_result=baseline.inventory_result,
            content_plan=baseline.content_plan,
        )
        == (),
        "STEP11_RC0031_P3_SOURCE_PLAN_SET_INVALID",
    )
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
        bool(matches),
        "STEP11_RC0031_P3_SOURCE_PLAN_SOLUTION_NOT_FOUND",
    )
    solution_material = {
        json.dumps(
            _body_relevant_base_solution_material(
                base_body_witness.base_witness,
                binding,
            ),
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
        for _discourse_plan, binding in matches
    }
    _closed_assert(
        len(solution_material) == 1,
        "STEP11_RC0031_P3_SOURCE_PLAN_SOLUTION_AMBIGUOUS",
    )
    return tuple(matches)


def _independent_base_plan_binding(
    baseline: Any,
    base_body_witness: Any,
) -> tuple[dict[str, Any], Any]:
    # Authority order supplies only a representative after equivalence is
    # proved; it is not a recovered or candidate-selected plan identity.
    return _independent_base_plan_solutions(baseline, base_body_witness)[0]


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
    dimension_builder = getattr(
        surface,
        _DIMENSION_SURFACE_BUILDER_EXPORT,
        None,
    )
    dimension_validator = getattr(
        surface,
        _DIMENSION_SURFACE_VALIDATOR_EXPORT,
        None,
    )
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
            if callable(dimension_builder):
                _closed_assert(
                    callable(dimension_validator),
                    "STEP11_RC0031_P3_DIMENSION_SURFACE_CANDIDATE_INVALID",
                )
                try:
                    candidate = dimension_builder(
                        candidate,
                        successor_snapshot=successor,
                        lexical_atom_specs=lexical_specs,
                    )
                    candidate_issues = dimension_validator(
                        candidate,
                        successor_snapshot=successor,
                        lexical_atom_specs=lexical_specs,
                    )
                except Exception:
                    pytest.fail(
                        "STEP11_RC0031_P3_DIMENSION_SURFACE_CANDIDATE_INVALID",
                        pytrace=False,
                    )
                _closed_assert(
                    candidate_issues == (),
                    "STEP11_RC0031_P3_DIMENSION_SURFACE_CANDIDATE_INVALID",
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


def test_rc0031_p3_freeze_scope_and_bounded_eof_seams_are_exact() -> None:
    for path, (byte_count, expected_sha256) in _P2_IMMUTABLE_FILES.items():
        _closed_assert(
            path.stat().st_size == byte_count
            and _sha256(path) == expected_sha256,
            "STEP11_RC0031_P3_P2_IMMUTABLE_FILE_DRIFT",
        )

    lexical_bytes = _LEXICAL_PATH.read_bytes()
    lexical_predecessor = lexical_bytes[:_LEXICAL_PREDECESSOR_BYTES]
    lexical_append = lexical_bytes[_LEXICAL_PREDECESSOR_BYTES:]
    _closed_assert(
        len(lexical_predecessor) == _LEXICAL_PREDECESSOR_BYTES
        and hashlib.sha256(lexical_predecessor).hexdigest()
        == _LEXICAL_PREDECESSOR_SHA256
        and len(lexical_append) <= _LEXICAL_APPEND_BYTE_MAX
        and _rc0031_owner_append_is_closed(
            lexical_append,
            _LEXICAL_APPEND_MARKER,
            lexical_predecessor,
            allowed_dynamic_imports=frozenset(),
            allow_non_ascii_literals=True,
        ),
        "STEP11_RC0031_P3_LEXICAL_APPEND_SCOPE_INVALID",
    )

    catalog_bytes = _CATALOG_PATH.read_bytes()
    catalog_predecessor = catalog_bytes[:_CATALOG_PREDECESSOR_BYTES]
    catalog_append = catalog_bytes[_CATALOG_PREDECESSOR_BYTES:]
    _closed_assert(
        len(catalog_predecessor) == _CATALOG_PREDECESSOR_BYTES
        and hashlib.sha256(catalog_predecessor).hexdigest()
        == _CATALOG_PREDECESSOR_SHA256
        and len(catalog_append) <= _CATALOG_APPEND_BYTE_MAX
        and _rc0031_owner_append_is_closed(
            catalog_append,
            _CATALOG_APPEND_MARKER,
            catalog_predecessor,
            allowed_dynamic_imports=frozenset(),
            allow_non_ascii_literals=True,
        ),
        "STEP11_RC0031_P3_CATALOG_APPEND_SCOPE_INVALID",
    )

    surface_bytes = _SURFACE_PATH.read_bytes()
    surface_predecessor = surface_bytes[:_SURFACE_PREDECESSOR_BYTES]
    surface_append = surface_bytes[_SURFACE_PREDECESSOR_BYTES:]
    _closed_assert(
        len(surface_predecessor) == _SURFACE_PREDECESSOR_BYTES
        and hashlib.sha256(surface_predecessor).hexdigest()
        == _SURFACE_PREDECESSOR_SHA256
        and len(surface_append) <= _SURFACE_APPEND_BYTE_MAX
        and _rc0031_owner_append_is_closed(
            surface_append,
            _SURFACE_APPEND_MARKER,
            surface_predecessor,
            allowed_dynamic_imports=frozenset(
                {
                    "emlis_ai_step11_grounded_lexicalization_v3",
                    "emlis_ai_step11_rc0031_experiment_surface_catalog_v3",
                }
            ),
            allow_non_ascii_literals=False,
        ),
        "STEP11_RC0031_P3_SURFACE_APPEND_SCOPE_INVALID",
    )

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
                _CATALOG_PATH,
                _LEXICAL_PATH,
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
    _closed_assert(
        len(service_py_paths) == _SERVICE_PY_PATH_COUNT
        and hashlib.sha256(service_py_path_material).hexdigest()
        == _SERVICE_PY_PATH_LIST_SHA256
        and len(repository_py_paths) == _REPOSITORY_PY_FROZEN_FILE_COUNT
        and hashlib.sha256(repository_py_material).hexdigest()
        == _REPOSITORY_PY_FROZEN_MATERIAL_SHA256,
        "STEP11_RC0031_P3_OUTSIDE_APPEND_SCOPE_DRIFT",
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


def test_rc0031_p3_predecessor_phase_projection_is_exact() -> None:
    """Keep the P2 closure claim pinned to P2 while later reserved paths exist."""

    p2 = _p2_test_module()
    current_test = Path(__file__).resolve().relative_to(_REPO_ROOT).as_posix()
    discovered = frozenset(
        path.relative_to(_REPO_ROOT).as_posix()
        for path in (_REPO_ROOT / "ai").rglob("*rc0031*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix != ".pyc"
    )
    _closed_assert(
        discovered == _EXPECTED_P3_ACTIVE
        and p2._EXPECTED_P2_ACTIVE
        == _EXPECTED_P3_ACTIVE - {current_test}
        and current_test in p2._EXPECTED_EXACT18
        and current_test not in p2._EXPECTED_P2_ACTIVE,
        "STEP11_RC0031_P3_PREDECESSOR_PHASE_PROJECTION_INVALID",
    )


def test_rc0031_p3_dimension_catalog_and_surface_successor_are_available() -> None:
    catalog_append = _CATALOG_PATH.read_bytes()[_CATALOG_PREDECESSOR_BYTES:]
    surface_append = _SURFACE_PATH.read_bytes()[_SURFACE_PREDECESSOR_BYTES:]
    catalog_append_lines = catalog_append.lstrip(b"\n").splitlines()
    surface_append_lines = surface_append.lstrip(b"\n").splitlines()
    catalog_owner = importlib.import_module(
        "emlis_ai_step11_rc0031_experiment_surface_catalog_v3"
    )
    surface = _surface_module()
    contract = getattr(
        catalog_owner,
        _DIMENSION_RECOVERY_CONTRACT_EXPORT,
        None,
    )
    contract_validator = getattr(
        catalog_owner,
        _DIMENSION_RECOVERY_VALIDATOR_EXPORT,
        None,
    )
    builder = getattr(surface, _DIMENSION_SURFACE_BUILDER_EXPORT, None)
    candidate_validator = getattr(
        surface,
        _DIMENSION_SURFACE_VALIDATOR_EXPORT,
        None,
    )
    catalog_all = tuple(getattr(catalog_owner, "__all__", ()))
    surface_all = tuple(getattr(surface, "__all__", ()))
    catalog_exports = set(catalog_all)
    surface_exports = set(surface_all)
    required_contract = {
        "schema_version": _DIMENSION_RECOVERY_CONTRACT_SCHEMA,
        "catalog_derived_dimensions": [
            "observation_stage",
            "source_role",
        ],
        "body_recovered_dimensions": [
            "polarity",
            "modality",
            "temporal_scope",
            "topic_fingerprint_sha256",
            "referent_scope",
        ],
        "topic_projection": "owner_expression_sha256_sequence",
        "candidate_metadata_required": False,
        "fixed_slot_prefix_max_per_candidate": 1,
        "schema_free_natural_language_surface_required": True,
    }
    available = (
        bool(catalog_append_lines)
        and catalog_append_lines[0] == _CATALOG_APPEND_MARKER
        and bool(surface_append_lines)
        and surface_append_lines[0] == _SURFACE_APPEND_MARKER
        and type(contract) is dict
        and contract == required_contract
        and callable(contract_validator)
        and callable(builder)
        and callable(candidate_validator)
        and {
            _DIMENSION_RECOVERY_CONTRACT_EXPORT,
            _DIMENSION_RECOVERY_VALIDATOR_EXPORT,
        }
        <= catalog_exports
        and all(
            catalog_all.count(name) == 1
            for name in (
                _DIMENSION_RECOVERY_CONTRACT_EXPORT,
                _DIMENSION_RECOVERY_VALIDATOR_EXPORT,
            )
        )
        and {
            _DIMENSION_SURFACE_BUILDER_EXPORT,
            _DIMENSION_SURFACE_VALIDATOR_EXPORT,
        }
        <= surface_exports
        and all(
            surface_all.count(name) == 1
            for name in (
                _DIMENSION_SURFACE_BUILDER_EXPORT,
                _DIMENSION_SURFACE_VALIDATOR_EXPORT,
            )
        )
    )
    _closed_assert(
        available,
        "STEP11_RC0031_P3_DIMENSION_SURFACE_NOT_AVAILABLE",
    )
    try:
        contract_issues = contract_validator(contract)
        builder_parameters = inspect.signature(builder).parameters
        validator_parameters = inspect.signature(candidate_validator).parameters
    except Exception:
        pytest.fail(
            "STEP11_RC0031_P3_DIMENSION_SURFACE_CONTRACT_INVALID",
            pytrace=False,
        )
    _closed_assert(
        contract_issues == ()
        and tuple(builder_parameters) == _DIMENSION_SURFACE_SIGNATURE
        and tuple(validator_parameters) == _DIMENSION_SURFACE_SIGNATURE
        and builder_parameters["value"].kind
        is inspect.Parameter.POSITIONAL_OR_KEYWORD
        and validator_parameters["value"].kind
        is inspect.Parameter.POSITIONAL_OR_KEYWORD
        and all(
            parameters[name].kind is inspect.Parameter.KEYWORD_ONLY
            for parameters in (builder_parameters, validator_parameters)
            for name in _DIMENSION_SURFACE_SIGNATURE[1:]
        ),
        "STEP11_RC0031_P3_DIMENSION_SURFACE_CONTRACT_INVALID",
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


def test_rc0031_p3_historical_p2_body_dimension_projection_is_noninjective() -> None:
    baseline, successor, lexical_specs = _p2_test_module()._forward_authority(
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
    base_catalog_owner = importlib.import_module(
        "emlis_ai_step11_surface_catalog_v3"
    )
    lexical_grammar = base_catalog_owner.STEP11_SURFACE_CATALOG[
        "grounded_lexicalization"
    ]
    profiles = tuple(lexical_grammar["phrase_profile_registry"]["profiles"])
    profiles_by_id = {row["profile_id"]: row for row in profiles}
    visible_counts = {
        name: sum(name in row["visible_feature_names"] for row in profiles)
        for name in ("polarity", "modality", "temporal_scope", "referent_scope")
    }
    event_profile = profiles_by_id["event_continuation"]
    constraint_profile = profiles_by_id["constraint_possible"]
    action_completed = profiles_by_id["action_completed"]
    action_intended = profiles_by_id["action_intended"]
    alternatives = (
        {
            "nucleus_kind": "event",
            "referent_scope": "event",
            "polarity": "positive",
            "modality": "observed",
            "temporal_scope": "current_input",
            "attribute_codes": ("operator:continuation",),
        },
        {
            "nucleus_kind": "event",
            "referent_scope": "event",
            "polarity": "negative",
            "modality": "reported",
            "temporal_scope": "reported_past",
            "attribute_codes": ("operator:continuation",),
        },
    )
    condition_to_field = {
        "nucleus_kinds": "nucleus_kind",
        "referent_scopes": "referent_scope",
        "polarities": "polarity",
        "modalities": "modality",
        "temporal_scopes": "temporal_scope",
    }

    def profile_matches_dimensions(
        profile: dict[str, Any], dimensions: dict[str, Any]
    ) -> bool:
        match = profile["match"]
        attribute_codes = set(dimensions["attribute_codes"])
        return (
            all(
                condition not in match
                or dimensions[field_name] in match[condition]
                for condition, field_name in condition_to_field.items()
            )
            and set(match.get("all_attribute_codes", ())) <= attribute_codes
            and (
                not match.get("any_attribute_codes")
                or bool(
                    set(match["any_attribute_codes"]) & attribute_codes
                )
            )
        )

    visible_projections = tuple(
        tuple(
            (name, dimensions[name])
            for name in event_profile["visible_feature_names"]
            if name in dimensions
        )
        for dimensions in alternatives
    )
    event_phrase = event_profile["noun_phrase"].encode("utf-8")
    historical_candidates = (
        _surface_module().build_step11_rc0031_experiment_surface_candidates(
            tuple(baseline.natural_candidates),
            successor_snapshot=successor,
            lexical_atom_specs=lexical_specs,
        )
    )
    representative_event_seen = any(
        event_phrase in candidate.final_utf8_bytes
        for candidate in historical_candidates
    )
    _closed_assert(
        source_side_is_complete
        and len(profiles) == 42
        and len(profiles_by_id) == 42
        and visible_counts
        == {
            "polarity": 15,
            "modality": 5,
            "temporal_scope": 4,
            "referent_scope": 0,
        }
        and sum(
            all(
                name in row["visible_feature_names"]
                for name in visible_counts
            )
            for row in profiles
        )
        == 0
        and sum(
            all(
                name not in row["visible_feature_names"]
                for name in visible_counts
            )
            for row in profiles
        )
        == 23
        and event_profile["match"]
        == {
            "nucleus_kinds": ["event"],
            "all_attribute_codes": ["operator:continuation"],
        }
        and event_profile["visible_feature_names"] == ["nucleus_kind"]
        and all(
            profile_matches_dimensions(event_profile, row)
            for row in alternatives
        )
        and len(set(visible_projections)) == 1
        and representative_event_seen
        and constraint_profile["match"]["modalities"]
        == ["possible", "unknown"]
        and "modality" not in constraint_profile["visible_feature_names"]
        and action_completed["match"]["lifecycles"]
        == ["reported_completed"]
        and action_intended["match"]["lifecycles"] == ["intended"]
        and {"modality", "temporal_scope"}
        <= set(action_completed["visible_feature_names"])
        and {"modality", "temporal_scope"}
        <= set(action_intended["visible_feature_names"]),
        "STEP11_RC0031_P3_BODY_DIMENSION_PROBE_DRIFT",
    )
    _closed_assert(
        len(set(visible_projections)) == 1 < len(alternatives),
        "STEP11_RC0031_P3_P2_BODY_DIMENSION_COLLISION_DRIFT",
    )


def test_rc0031_p3_proposed_surface_dimension_lattice_is_prefix_free_and_attack_closed() -> None:
    codewords = _proposed_visible_dimension_codewords()
    prefixes = tuple(row[0] for row in codewords)
    sorted_prefixes = tuple(sorted(prefixes))
    token_values = tuple(
        token
        for name in _PROPOSED_VISIBLE_DIMENSION_ORDER
        for token in _PROPOSED_VISIBLE_DIMENSION_TOKENS[name].values()
    )
    expected_domains = {
        "temporal_scope": {
            "current_input",
            "reported_past",
            "intended_future",
            "atemporal",
            "unknown",
        },
        "modality": {
            "observed",
            "reported",
            "intended",
            "possible",
            "unknown",
        },
        "polarity": {
            "positive",
            "negative",
            "mixed",
            "neutral",
            "unknown",
        },
        "referent_scope": {
            "self",
            "other",
            "event",
            "action",
            "state",
            "relation",
            "unknown",
        },
    }
    round_trips = tuple(
        _proposed_parse_visible_dimension_prefix(prefix + "意味単位")
        for prefix in prefixes
    )
    _closed_assert(
        tuple(_PROPOSED_VISIBLE_DIMENSION_TOKENS)
        == _PROPOSED_VISIBLE_DIMENSION_ORDER
        and {
            name: set(tokens)
            for name, tokens in _PROPOSED_VISIBLE_DIMENSION_TOKENS.items()
        }
        == expected_domains
        and len(codewords) == 875
        and len(prefixes) == len(set(prefixes))
        and len(token_values) == 22
        and len(token_values) == len(set(token_values))
        and all(
            token
            and token == token.strip()
            and unicodedata.normalize("NFC", token) == token
            and "\r" not in token
            and "\n" not in token
            for token in token_values
        )
        and all(
            not right.startswith(left)
            for left, right in zip(
                sorted_prefixes,
                sorted_prefixes[1:],
            )
        )
        and all(
            parsed == dict(fields) and remainder == "意味単位"
            for (_prefix, fields), (parsed, remainder) in zip(
                codewords,
                round_trips,
            )
        )
        and _PROPOSED_CATALOG_DERIVED_DIMENSION_DOMAINS
        == {
            "observation_stage": ("normal_observation",),
            "source_role": ("original_input",),
        },
        "STEP11_RC0031_P3_SURFACE_DIMENSION_LATTICE_INVALID",
    )

    source_values = {
        "temporal_scope": "current_input",
        "modality": "observed",
        "polarity": "neutral",
        "referent_scope": "event",
    }
    ordered_tokens = tuple(
        _PROPOSED_VISIBLE_DIMENSION_TOKENS[name][source_values[name]]
        for name in _PROPOSED_VISIBLE_DIMENSION_ORDER
    )
    valid_prefix = _proposed_visible_dimension_prefix(source_values)
    attacks = (
        valid_prefix[len(ordered_tokens[0]) :] + "意味単位",
        "".join(
            (
                ordered_tokens[1],
                ordered_tokens[0],
                *ordered_tokens[2:],
                _PROPOSED_VISIBLE_DIMENSION_CLOSE,
                "意味単位",
            )
        ),
        valid_prefix[: -len(_PROPOSED_VISIBLE_DIMENSION_CLOSE)]
        + "；意味単位",
        "任意" + valid_prefix + "意味単位",
    )
    attack_results: list[str] = []
    for attack in attacks:
        try:
            _proposed_parse_visible_dimension_prefix(attack)
        except ValueError as error:
            attack_results.append(str(error))
        else:
            attack_results.append("accepted")
    substituted_values = dict(source_values)
    substituted_values["polarity"] = "negative"
    substituted, remainder = _proposed_parse_visible_dimension_prefix(
        _proposed_visible_dimension_prefix(substituted_values) + "意味単位"
    )
    _closed_assert(
        attack_results
        == [
            "STEP11_RC0031_P3_SURFACE_DIMENSION_UNPARSEABLE",
            "STEP11_RC0031_P3_SURFACE_DIMENSION_UNPARSEABLE",
            "STEP11_RC0031_P3_SURFACE_DIMENSION_UNPARSEABLE",
            "STEP11_RC0031_P3_SURFACE_DIMENSION_UNPARSEABLE",
        ]
        and substituted == substituted_values
        and substituted != source_values
        and remainder == "意味単位"
        and "pre_question_observation"
        not in _PROPOSED_CATALOG_DERIVED_DIMENSION_DOMAINS[
            "observation_stage"
        ]
        and "refined_observation"
        not in _PROPOSED_CATALOG_DERIVED_DIMENSION_DOMAINS[
            "observation_stage"
        ]
        and "supplemental_answer"
        not in _PROPOSED_CATALOG_DERIVED_DIMENSION_DOMAINS["source_role"],
        "STEP11_RC0031_P3_SURFACE_DIMENSION_ATTACK_NOT_CLOSED",
    )


def test_rc0031_p3_fixed_slot_dimension_bundle_respects_schema_free_product_boundary() -> None:
    """A mathematically injective probe is not yet a product Surface grammar."""

    source_atom_counts = tuple(
        sum(
            not row["base_exact_reuse"]
            for row in _proposed_rc0031_source_dimension_projection(context)
        )
        for context in _rc0031_final_candidate_contexts()
    )
    _closed_assert(
        source_atom_counts == (0, 0, 1, 3, 3, 7, 3, 3, 10, 8)
        and sum(source_atom_counts) == 38
        and sum(count > 1 for count in source_atom_counts) == 7
        and max(source_atom_counts) == 10,
        "STEP11_RC0031_P3_FIXED_SLOT_PRODUCT_PROBE_DRIFT",
    )
    builder = getattr(
        _surface_module(),
        _DIMENSION_SURFACE_BUILDER_EXPORT,
        None,
    )
    _closed_assert(
        callable(builder),
        "STEP11_RC0031_P3_FIXED_SLOT_PREFIX_PRODUCT_CONTRACT_NOT_SATISFIED",
    )
    fixed_prefixes = tuple(
        prefix.encode("utf-8")
        for prefix, _fields in _proposed_visible_dimension_codewords()
    )
    fixed_bundle_counts = tuple(
        sum(
            candidate.final_utf8_bytes.count(prefix)
            for prefix in fixed_prefixes
        )
        for _case, _base, _next, _lexical, candidate, _witness
        in _rc0031_final_candidate_contexts()
    )
    _closed_assert(
        all(count <= 1 for count in fixed_bundle_counts),
        "STEP11_RC0031_P3_FIXED_SLOT_PREFIX_PRODUCT_CONTRACT_NOT_SATISFIED",
    )


def test_rc0031_p3_source_dimensions_and_body_topic_projection_are_exact_without_candidate_metadata() -> None:
    contexts = _rc0031_final_candidate_contexts()
    expected_source_counts = (1, 0, 1, 3, 3, 7, 3, 3, 10, 8)
    observed_source_counts: list[int] = []
    total_source_atoms = 0
    total_prefixed_atoms = 0
    total_base_reuse_atoms = 0
    observed_polarities: set[str] = set()
    observed_modalities: set[str] = set()
    observed_temporal_scopes: set[str] = set()
    observed_referent_scopes: set[str] = set()
    mutation_row: dict[str, Any] | None = None

    for context in contexts:
        rows = _proposed_rc0031_source_dimension_projection(context)
        observed_source_counts.append(len(rows))
        total_source_atoms += len(rows)
        topic_scope_by_fingerprint: dict[str, set[tuple[str, ...]]] = {}
        semantic_signatures: list[tuple[Any, ...]] = []
        for row in rows:
            body_dimensions = {
                name: row[name]
                for name in _PROPOSED_VISIBLE_DIMENSION_ORDER
            }
            parsed_projection = {
                "observation_stage": row["observation_stage"],
                "source_role": row["source_role"],
                "polarity": row["polarity"],
                "modality": row["modality"],
                "temporal_scope": row["temporal_scope"],
                "topic_fingerprint_sha256": row[
                    "topic_fingerprint_sha256"
                ],
                "referent_scope": row["referent_scope"],
            }
            if row["base_exact_reuse"]:
                total_base_reuse_atoms += 1
                dimension_round_trip = (
                    row["polarity"],
                    row["modality"],
                    row["temporal_scope"],
                    row["referent_scope"],
                ) == ("unknown", "unknown", "unknown", "unknown")
            else:
                total_prefixed_atoms += 1
                parsed_dimensions, remainder = (
                    _proposed_parse_visible_dimension_prefix(
                        _proposed_visible_dimension_prefix(body_dimensions)
                        + "意味単位"
                    )
                )
                dimension_round_trip = (
                    parsed_dimensions == body_dimensions
                    and remainder == "意味単位"
                )
                if mutation_row is None:
                    mutation_row = row
            topic_scope_by_fingerprint.setdefault(
                row["topic_fingerprint_sha256"], set()
            ).add(row["topic_scope_ids"])
            semantic_signatures.append(
                (
                    row["semantic_family"],
                    row["semantic_key"],
                    row["direction"],
                    row["topic_fingerprint_sha256"],
                    row["polarity"],
                    row["modality"],
                    row["temporal_scope"],
                    row["referent_scope"],
                )
            )
            observed_polarities.add(row["polarity"])
            observed_modalities.add(row["modality"])
            observed_temporal_scopes.add(row["temporal_scope"])
            observed_referent_scopes.add(row["referent_scope"])
            _closed_assert(
                set(parsed_projection)
                == set(_PRELIMINARY_BODY_DIMENSION_FIELDS)
                and row["observation_stage"]
                in _PROPOSED_CATALOG_DERIVED_DIMENSION_DOMAINS[
                    "observation_stage"
                ]
                and row["source_role"]
                in _PROPOSED_CATALOG_DERIVED_DIMENSION_DOMAINS[
                    "source_role"
                ]
                and row["topic_scope_ids"]
                and re.fullmatch(
                    r"[0-9a-f]{64}",
                    row["topic_fingerprint_sha256"],
                )
                is not None
                and row["topic_fingerprint_sha256"]
                == _proposed_topic_fingerprint(row["owner_expressions"])
                and dimension_round_trip,
                "STEP11_RC0031_P3_SOURCE_DIMENSION_PROJECTION_INVALID",
            )
        _closed_assert(
            all(len(values) == 1 for values in topic_scope_by_fingerprint.values())
            and len(semantic_signatures) == len(set(semantic_signatures)),
            "STEP11_RC0031_P3_TOPIC_PROJECTION_NOT_INJECTIVE",
        )

    _closed_assert(
        tuple(observed_source_counts) == expected_source_counts
        and total_source_atoms == 39
        and total_prefixed_atoms == 38
        and total_base_reuse_atoms == 1
        and observed_polarities
        == {"positive", "negative", "mixed", "neutral", "unknown"}
        and observed_modalities
        == {"observed", "reported", "intended", "possible", "unknown"}
        and observed_temporal_scopes
        == {"current_input", "reported_past", "unknown"}
        and observed_referent_scopes
        == {"event", "state", "action", "relation", "unknown"},
        "STEP11_RC0031_P3_SOURCE_DIMENSION_DENOMINATOR_DRIFT",
    )

    _closed_assert(
        mutation_row is not None,
        "STEP11_RC0031_P3_SOURCE_DIMENSION_ATTACK_NOT_CLOSED",
    )
    original_body_dimensions = {
        name: mutation_row[name]
        for name in _PROPOSED_VISIBLE_DIMENSION_ORDER
    }
    substituted_body_dimensions = dict(original_body_dimensions)
    polarity_domain = tuple(_PROPOSED_VISIBLE_DIMENSION_TOKENS["polarity"])
    substituted_body_dimensions["polarity"] = next(
        value
        for value in polarity_domain
        if value != original_body_dimensions["polarity"]
    )
    parsed_substitution, _remainder = (
        _proposed_parse_visible_dimension_prefix(
            _proposed_visible_dimension_prefix(substituted_body_dimensions)
            + "意味単位"
        )
    )
    transplanted_owner_expressions = (
        mutation_row["owner_expressions"][0] + "別",
        *mutation_row["owner_expressions"][1:],
    )
    _closed_assert(
        parsed_substitution == substituted_body_dimensions
        and parsed_substitution != original_body_dimensions
        and _proposed_topic_fingerprint(transplanted_owner_expressions)
        != mutation_row["topic_fingerprint_sha256"],
        "STEP11_RC0031_P3_SOURCE_DIMENSION_ATTACK_NOT_CLOSED",
    )


def test_rc0031_p3_source_plan_set_has_exact_one_body_relevant_solution_without_candidate_metadata() -> None:
    contexts = _rc0031_final_candidate_contexts()
    expected = (
        ("nls3s_b001_0001", 1, 1),
        ("nls3s_b001_0002", 1, 1),
        ("nls3s_b001_0009", 8, 4),
        ("nls3s_b001_0019", 2, 1),
        ("nls3s_b001_0019", 2, 1),
        ("nls3s_b001_0035", 12, 6),
        ("nls3s_b001_0043", 2, 1),
        ("nls3s_b001_0043", 2, 1),
        ("nls3s_b001_0063", 12, 4),
        ("nls3s_b001_0100", 12, 4),
    )
    observed: list[tuple[str, int, int]] = []
    source_semantic_total = 0
    source_reception_total = 0
    for context in contexts:
        case_id, baseline, _successor, _lexical, _candidate, base_witness = (
            context
        )
        solutions = _independent_base_plan_solutions(
            baseline, base_witness
        )
        source_projection = _independent_rc0031_source_projection(
            context,
            plan_solutions=solutions,
        )
        _closed_assert(
            type(source_projection[0]) is dict
            and type(source_projection[1]) is dict
            and 0 <= source_projection[5] <= 576,
            "STEP11_RC0031_P3_SOURCE_PLAN_PROJECTION_INVALID",
        )
        source_semantic_total += len(source_projection[0])
        source_reception_total += len(source_projection[1])
        observed.append(
            (
                case_id,
                len(baseline.discourse_plan_set.plans),
                len(solutions),
            )
        )
    _closed_assert(
        tuple(observed) == expected
        and (source_semantic_total, source_reception_total) == (39, 11),
        "STEP11_RC0031_P3_SOURCE_PLAN_DENOMINATOR_DRIFT",
    )

    planner = importlib.import_module("emlis_ai_discourse_graph_planner_v3")
    baseline = contexts[2][1]
    plan_set = baseline.discourse_plan_set
    subset = replace(plan_set, plans=plan_set.plans[:1])
    reordered = replace(plan_set, plans=tuple(reversed(plan_set.plans)))
    duplicated = replace(
        plan_set,
        plans=(*plan_set.plans, plan_set.plans[0]),
    )
    mutated_plan = dict(plan_set.plans[0])
    mutated_plan["structural_signature"] = "0" * 64
    mutated = replace(
        plan_set,
        plans=(mutated_plan, *plan_set.plans[1:]),
    )

    def plan_set_issues(value: Any) -> frozenset[str]:
        return frozenset(
            planner.validate_discourse_graph_plan_set(
                value,
                inventory_result=baseline.inventory_result,
                content_plan=baseline.content_plan,
            )
        )

    _closed_assert(
        plan_set_issues(plan_set) == frozenset()
        and "DISCOURSE_PLAN_SET_MISMATCH" in plan_set_issues(subset)
        and "DISCOURSE_PLAN_SET_MISMATCH" in plan_set_issues(reordered)
        and {
            "DISCOURSE_PLAN_SET_MISMATCH",
            "DISCOURSE_SIGNATURE_SET_INVALID",
        }
        <= plan_set_issues(duplicated)
        and {
            "DISCOURSE_PLAN_SET_MISMATCH",
            "DISCOURSE_CONTRACT_REJECTED",
        }
        <= plan_set_issues(mutated),
        "STEP11_RC0031_P3_SOURCE_PLAN_SET_ATTACK_NOT_CLOSED",
    )


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
# ---------------------------------------------------------------------------
# rc0031 P3 B5 owner-boundary design freeze and RED-only
# ---------------------------------------------------------------------------

_B5_TEST_PREFIX_BYTES = 162_521
_B5_TEST_PREFIX_SHA256 = (
    "f4922b32d76816e615fb2e448b61a780185800440fc1cbdb9fad0f43117b0d91"
)
_B5_PREDECESSOR_TEST_COUNT = 24
_B5_PREDECESSOR_TEST_NAMES_SHA256 = (
    "15132dea6318370f3f63dda2deb2977125253da34a70e15529a97137836f458b"
)
_B5_NEW_TEST_NAMES = frozenset(
    {
        "test_rc0031_p3_b5_freeze_scope_and_predecessor_behavior_are_exact",
        "test_rc0031_p3_b5_design_denominators_and_resource_envelope_are_exact",
        "test_rc0031_p3_b5_source_fragment_product_owner_expression_is_unique_or_fails_closed",
        "test_rc0031_p3_b5_relation_connected_product_clusters_account_exact38_with_load4",
        "test_rc0031_p3_b5_ast_first_reception_preserves_bound10_and_adds_unmatched1",
        "test_rc0031_p3_b5_product_surface_is_schema_free_metadata_free_and_case_agnostic",
    }
)
_B5_CLUSTER_LOADS_BY_CONTEXT = (
    (),
    (),
    (1,),
    (3,),
    (3,),
    (3, 4),
    (3,),
    (3,),
    (3, 4, 3),
    (3, 2, 3),
)
_B5_EXPECTED_FAMILY_COUNTS = {
    "construction": 22,
    "relation": 13,
    "semantic_link": 1,
    "explicit_unknown": 2,
}
_B5_DESIGN_CONTRACT = {
    "schema_version": (
        "cocolon.emlis.nls_v3.step11.rc0031_product_surface_b5.v1"
    ),
    "final_candidate_context_count": 10,
    "unique_case_count": 8,
    "new_semantic_atom_count": 38,
    "verified_base_reuse_count": 1,
    "clause_ready_owner_occurrence_count": 24,
    "product_proposition_cluster_max": 13,
    "product_proposition_cluster_load_max": 4,
    "required_reception_opportunity_count": 11,
    "base_ast_reception_binding_count": 10,
    "unmatched_required_reception_count": 1,
    "visible_source_anchor_max": 1,
    "visible_clauses_per_grammatical_sentence_max": 2,
    "grammatical_complexity_load_max": 4,
    "repeated_joiner_per_group_max": 2,
    "realization_units_per_group_max": 4,
    "schema_free_natural_language_surface_required": True,
    "candidate_metadata_required": False,
    "case_family_review_severity_branch_count": 0,
}
_B5_OWNER_PROJECTION_EXPORT = (
    "_step11_rc0031_product_owner_expression_projection"
)
_B5_LEXICAL_PREDECESSOR_BYTES = 129_615
_B5_SURFACE_PREDECESSOR_BYTES = 485_490
_B5_OWNER_PROJECTION_SIGNATURE = (
    "base_candidate",
    "successor_snapshot",
    "lexical_atom_specs",
)
_B5_OWNER_NOT_AVAILABLE = (
    "STEP11_RC0031_P3_B5_PRODUCT_OWNER_EXPRESSION_NOT_AVAILABLE"
)
_B5_CLUSTER_NOT_AVAILABLE = (
    "STEP11_RC0031_P3_B5_PRODUCT_PROPOSITION_CLUSTER_NOT_AVAILABLE"
)
_B5_RECEPTION_NOT_AVAILABLE = (
    "STEP11_RC0031_P3_B5_AST_BOUND_RECEPTION_NOT_AVAILABLE"
)
_B5_BOUNDARY_NOT_AVAILABLE = (
    "STEP11_RC0031_P3_B5_PRODUCT_BOUNDARY_NOT_AVAILABLE"
)


@lru_cache(maxsize=1)
def _b5_predecessor_candidate_contexts() -> tuple[tuple[Any, ...], ...]:
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
        for candidate in candidates:
            base = candidate.base_candidate
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
        len(contexts) == _B5_DESIGN_CONTRACT["final_candidate_context_count"]
        and len({row[0] for row in contexts})
        == _B5_DESIGN_CONTRACT["unique_case_count"],
        "STEP11_RC0031_P3_B5_PREDECESSOR_CONTEXT_DRIFT",
    )
    return tuple(contexts)


def _b5_normalize_nucleus_id(successor: Any, value: Any) -> str:
    actual_by_source = {
        str(row.source_id): str(row.actual_source_id)
        for row in successor.base_snapshot.nuclei
    }
    return actual_by_source.get(str(value), str(value))


@lru_cache(maxsize=1)
def _b5_design_probe() -> dict[str, Any]:
    contexts = _b5_predecessor_candidate_contexts()
    family_counts: Counter[str] = Counter()
    current_proposition_unit_count = 0
    owner_occurrence_count = 0
    exactly_one_source_fragment_count = 0
    current_generic_projection_count = 0
    required_reception_count = 0
    base_ast_binding_count = 0
    matched_opportunity_count = 0
    unmatched_required_count = 0
    richer_ast_binding_count = 0
    resource_envelopes: set[tuple[int, int, int, int]] = set()
    visible_source_anchor_counts: list[int] = []

    family_rows = (
        ("construction", "construction_atoms", "construction_instance_id"),
        ("relation", "relation_atoms", "experiment_relation_id"),
        ("semantic_link", "semantic_link_atoms", "source_semantic_link_id"),
        ("explicit_unknown", "explicit_unknown_atoms", "source_unknown_id"),
    )
    for _case, _baseline, successor, _specs, candidate, _witness in contexts:
        for family, collection_name, source_id_name in family_rows:
            for atom in getattr(candidate, collection_name):
                if str(getattr(atom, source_id_name)) != _EXPECTED_REUSE_SOURCE_ID:
                    family_counts[family] += 1

        plan = candidate.surface_realization_plan
        current_proposition_unit_count += len(plan.proposition_clause_bindings)
        resource_envelopes.add(
            (
                plan.maximum_visible_clauses_per_grammatical_sentence,
                plan.maximum_grammatical_complexity_load,
                plan.maximum_repeated_joiner_per_group,
                plan.maximum_observation_clauses_per_sentence,
            )
        )
        visible_source_anchor_counts.append(
            candidate.base_candidate.rendered_surface.visible_source_anchor_count
        )

        lexemes = tuple(candidate.natural_handle_specs.lexemes)
        fragments = tuple(candidate.base_candidate.surface_ast.source_fragments)
        owner_occurrence_count += len(lexemes)
        for lexeme in lexemes:
            matches = tuple(
                fragment
                for fragment in fragments
                if lexeme.base_source_nucleus_id in fragment.source_nucleus_ids
                and fragment.evidence_grade == "exact_source_span"
            )
            exactly_one_source_fragment_count += len(matches) == 1
            current_generic_projection_count += (
                lexeme.referent_text == lexeme.grounded_phrase_text
            )

        required = tuple(
            row
            for row in successor.base_snapshot.reception_opportunities
            if row.retention == "required" or row.safety_required is True
        )
        bindings = tuple(
            candidate.base_candidate.surface_ast.reception_antecedent_bindings
        )
        binding_by_opportunity: dict[str, Any] = {}
        duplicate_binding_ids: set[str] = set()
        for binding in bindings:
            for source_id in binding.source_reception_opportunity_ids:
                key = str(source_id)
                if key in binding_by_opportunity:
                    duplicate_binding_ids.add(key)
                binding_by_opportunity[key] = binding
        required_reception_count += len(required)
        base_ast_binding_count += len(bindings)
        for opportunity in required:
            binding = binding_by_opportunity.get(str(opportunity.source_id))
            if binding is None:
                unmatched_required_count += 1
                continue
            matched_opportunity_count += 1
            raw_visible = {
                _b5_normalize_nucleus_id(successor, row)
                for row in (
                    *opportunity.target_nucleus_ids,
                    *opportunity.support_nucleus_ids,
                )
            }
            selected_ast_visible = {
                _b5_normalize_nucleus_id(successor, row)
                for row in (
                    *binding.source_target_nucleus_ids,
                    *binding.antecedent_nucleus_ids,
                    *binding.supporting_nucleus_ids,
                )
            }
            richer_ast_binding_count += bool(selected_ast_visible - raw_visible)
        _closed_assert(
            not duplicate_binding_ids,
            "STEP11_RC0031_P3_B5_RECEPTION_SOURCE_BINDING_AMBIGUOUS",
        )

    return {
        "context_count": len(contexts),
        "unique_case_count": len({row[0] for row in contexts}),
        "family_counts": dict(family_counts),
        "new_semantic_atom_count": sum(family_counts.values()),
        "verified_base_reuse_count": sum(
            row[4].rendered_surface.exact_reuse_count for row in contexts
        ),
        "current_proposition_unit_count": current_proposition_unit_count,
        "owner_occurrence_count": owner_occurrence_count,
        "exactly_one_source_fragment_count": (
            exactly_one_source_fragment_count
        ),
        "current_generic_projection_count": current_generic_projection_count,
        "required_reception_count": required_reception_count,
        "base_ast_binding_count": base_ast_binding_count,
        "matched_opportunity_count": matched_opportunity_count,
        "unmatched_required_count": unmatched_required_count,
        "richer_ast_binding_count": richer_ast_binding_count,
        "resource_envelopes": resource_envelopes,
        "visible_source_anchor_max": max(visible_source_anchor_counts),
    }


def _b5_owner_projection_or_red() -> Any:
    lexical_owner = importlib.import_module(
        "emlis_ai_step11_grounded_lexicalization_v3"
    )
    projection = getattr(lexical_owner, _B5_OWNER_PROJECTION_EXPORT, None)
    _closed_assert(callable(projection), _B5_OWNER_NOT_AVAILABLE)
    try:
        parameters = inspect.signature(projection).parameters
    except Exception:
        pytest.fail(
            "STEP11_RC0031_P3_B5_PRODUCT_OWNER_EXPRESSION_CONTRACT_INVALID",
            pytrace=False,
        )
    _closed_assert(
        tuple(parameters) == _B5_OWNER_PROJECTION_SIGNATURE
        and parameters["base_candidate"].kind
        is inspect.Parameter.POSITIONAL_OR_KEYWORD
        and all(
            parameters[name].kind is inspect.Parameter.KEYWORD_ONLY
            for name in _B5_OWNER_PROJECTION_SIGNATURE[1:]
        )
        and _B5_OWNER_PROJECTION_EXPORT
        not in tuple(getattr(lexical_owner, "__all__", ())),
        "STEP11_RC0031_P3_B5_PRODUCT_OWNER_EXPRESSION_CONTRACT_INVALID",
    )
    return projection


def _b5_surface_api_or_red(code: str) -> tuple[Any, Any]:
    surface = _surface_module()
    builder = getattr(surface, _DIMENSION_SURFACE_BUILDER_EXPORT, None)
    validator = getattr(surface, _DIMENSION_SURFACE_VALIDATOR_EXPORT, None)
    _closed_assert(callable(builder) and callable(validator), code)
    try:
        builder_parameters = inspect.signature(builder).parameters
        validator_parameters = inspect.signature(validator).parameters
    except Exception:
        pytest.fail(code, pytrace=False)
    _closed_assert(
        tuple(builder_parameters) == _DIMENSION_SURFACE_SIGNATURE
        and tuple(validator_parameters) == _DIMENSION_SURFACE_SIGNATURE
        and all(
            parameters[name].kind is inspect.Parameter.KEYWORD_ONLY
            for parameters in (builder_parameters, validator_parameters)
            for name in _DIMENSION_SURFACE_SIGNATURE[1:]
        )
        and not (
            set(builder_parameters) | set(validator_parameters)
        )
        & (_FINAL_INVERSE_FORBIDDEN_PARAMETERS - {"lexical_atom_specs"}),
        code,
    )
    return builder, validator


def _b5_owner_sets_are_connected(
    owner_rows: tuple[tuple[str, ...], ...],
) -> bool:
    if not owner_rows or any(not row for row in owner_rows):
        return False
    pending = [0]
    visited: set[int] = set()
    while pending:
        current = pending.pop()
        if current in visited:
            continue
        visited.add(current)
        current_owners = set(owner_rows[current])
        pending.extend(
            index
            for index, owners in enumerate(owner_rows)
            if index not in visited and bool(current_owners & set(owners))
        )
    return len(visited) == len(owner_rows)


def test_rc0031_p3_b5_freeze_scope_and_predecessor_behavior_are_exact() -> None:
    source = Path(__file__).resolve().read_bytes()
    marker = (
        b"# ---------------------------------------------------------------------------\n"
        b"# rc0031 P3 B5 owner-boundary design freeze and RED-only\n"
        b"# ---------------------------------------------------------------------------\n"
    )
    _closed_assert(
        source.count(marker) == 1,
        "STEP11_RC0031_P3_B5_TEST_PREFIX_INVALID",
    )
    prefix = source[: source.index(marker)]
    tree = ast.parse(source.decode("utf-8", errors="strict"))
    test_names = frozenset(
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    )
    predecessor_names = tuple(sorted(test_names - _B5_NEW_TEST_NAMES))
    predecessor_name_material = (
        "\n".join(predecessor_names) + "\n"
    ).encode("utf-8")
    _closed_assert(
        len(prefix) == _B5_TEST_PREFIX_BYTES
        and hashlib.sha256(prefix).hexdigest() == _B5_TEST_PREFIX_SHA256
        and len(predecessor_names) == _B5_PREDECESSOR_TEST_COUNT
        and hashlib.sha256(predecessor_name_material).hexdigest()
        == _B5_PREDECESSOR_TEST_NAMES_SHA256
        and _B5_NEW_TEST_NAMES <= test_names
        and len(test_names) == _B5_PREDECESSOR_TEST_COUNT + len(_B5_NEW_TEST_NAMES)
        and _EXPECTED_P3_ACTIVE
        == frozenset(
            {
                "ai/services/ai_inference/emlis_ai_step11_rc0031_experiment_surface_catalog_v3.py",
                "ai/tests/fixtures/emlis_nls_v3/cycle_001/rc0031_representative8_body_free.json",
                "ai/tests/test_emlis_nls_v3_s11_rc0031_proposition_surface_red.py",
                "ai/tests/test_emlis_nls_v3_s11_rc0031_proposition_surface_mutation.py",
                "ai/tests/test_emlis_nls_v3_s11_rc0031_forward_inverse_independence.py",
            }
        ),
        "STEP11_RC0031_P3_B5_TEST_SCOPE_DRIFT",
    )


def test_rc0031_p3_b5_design_denominators_and_resource_envelope_are_exact() -> None:
    probe = _b5_design_probe()
    cluster_loads = tuple(
        load
        for context_loads in _B5_CLUSTER_LOADS_BY_CONTEXT
        for load in context_loads
    )
    _closed_assert(
        probe["context_count"]
        == _B5_DESIGN_CONTRACT["final_candidate_context_count"]
        and probe["unique_case_count"]
        == _B5_DESIGN_CONTRACT["unique_case_count"]
        and probe["family_counts"] == _B5_EXPECTED_FAMILY_COUNTS
        and probe["new_semantic_atom_count"]
        == _B5_DESIGN_CONTRACT["new_semantic_atom_count"]
        and probe["verified_base_reuse_count"]
        == _B5_DESIGN_CONTRACT["verified_base_reuse_count"]
        and probe["current_proposition_unit_count"] == 18
        and len(cluster_loads)
        == _B5_DESIGN_CONTRACT["product_proposition_cluster_max"]
        and sum(cluster_loads)
        == _B5_DESIGN_CONTRACT["new_semantic_atom_count"]
        and max(cluster_loads)
        == _B5_DESIGN_CONTRACT["product_proposition_cluster_load_max"]
        and probe["owner_occurrence_count"]
        == _B5_DESIGN_CONTRACT["clause_ready_owner_occurrence_count"]
        and probe["exactly_one_source_fragment_count"]
        == probe["owner_occurrence_count"]
        and probe["current_generic_projection_count"]
        == probe["owner_occurrence_count"]
        and probe["required_reception_count"]
        == _B5_DESIGN_CONTRACT["required_reception_opportunity_count"]
        and probe["base_ast_binding_count"]
        == _B5_DESIGN_CONTRACT["base_ast_reception_binding_count"]
        and probe["matched_opportunity_count"] == 10
        and probe["unmatched_required_count"]
        == _B5_DESIGN_CONTRACT["unmatched_required_reception_count"]
        and probe["richer_ast_binding_count"] == 2
        and probe["resource_envelopes"]
        == {
            (
                _B5_DESIGN_CONTRACT[
                    "visible_clauses_per_grammatical_sentence_max"
                ],
                _B5_DESIGN_CONTRACT["grammatical_complexity_load_max"],
                _B5_DESIGN_CONTRACT["repeated_joiner_per_group_max"],
                _B5_DESIGN_CONTRACT["realization_units_per_group_max"],
            )
        }
        and probe["visible_source_anchor_max"]
        <= _B5_DESIGN_CONTRACT["visible_source_anchor_max"],
        "STEP11_RC0031_P3_B5_DESIGN_DENOMINATOR_DRIFT",
    )


def test_rc0031_p3_b5_source_fragment_product_owner_expression_is_unique_or_fails_closed() -> None:
    projection = _b5_owner_projection_or_red()
    lexical_owner = importlib.import_module(
        "emlis_ai_step11_grounded_lexicalization_v3"
    )
    contexts = _b5_predecessor_candidate_contexts()
    projected_occurrence_count = 0
    for _case, _base, successor, lexical_specs, candidate, _witness in contexts:
        base_candidate = candidate.base_candidate
        try:
            rows = projection(
                base_candidate,
                successor_snapshot=successor,
                lexical_atom_specs=lexical_specs,
            )
            rows_again = projection(
                base_candidate,
                successor_snapshot=successor,
                lexical_atom_specs=lexical_specs,
            )
        except Exception:
            pytest.fail(
                "STEP11_RC0031_P3_B5_PRODUCT_OWNER_EXPRESSION_CONTRACT_INVALID",
                pytrace=False,
            )
        lexemes = tuple(candidate.natural_handle_specs.lexemes)
        fragments = {
            row.source_anchor_id: row
            for row in base_candidate.surface_ast.source_fragments
        }
        _closed_assert(
            type(rows) is tuple
            and rows_again == rows
            and len(rows) == len(lexemes)
            and all(type(row) is tuple and len(row) == 5 for row in rows)
            and len({row[0] for row in rows}) == len(rows)
            and len({row[3] for row in rows}) == len(rows),
            "STEP11_RC0031_P3_B5_PRODUCT_OWNER_EXPRESSION_CONTRACT_INVALID",
        )
        for lexeme, row in zip(lexemes, rows):
            owner_id, nucleus_id, anchor_id, expression, digest = row
            fragment = fragments.get(anchor_id)
            expected_fragments = tuple(
                value
                for value in base_candidate.surface_ast.source_fragments
                if lexeme.base_source_nucleus_id in value.source_nucleus_ids
                and value.evidence_grade == "exact_source_span"
            )
            _closed_assert(
                type(owner_id) is str
                and owner_id == lexeme.source_owner_id
                and type(nucleus_id) is str
                and nucleus_id == lexeme.base_source_nucleus_id
                and len(expected_fragments) == 1
                and anchor_id == expected_fragments[0].source_anchor_id
                and fragment is not None
                and nucleus_id in fragment.source_nucleus_ids
                and fragment.evidence_grade == "exact_source_span"
                and type(expression) is str
                and expression == expression.strip()
                and unicodedata.normalize("NFC", expression) == expression
                and 1 <= len(expression)
                <= _EXPECTED_FORWARD_RESOURCE_BOUNDS["referent_scalar_max"]
                and "\r" not in expression
                and "\n" not in expression
                and type(digest) is str
                and digest
                == hashlib.sha256(expression.encode("utf-8")).hexdigest(),
                "STEP11_RC0031_P3_B5_PRODUCT_OWNER_EXPRESSION_CONTRACT_INVALID",
            )
        projected_occurrence_count += len(rows)

        attacked_lexeme = lexemes[0]
        matching = tuple(
            row
            for row in base_candidate.surface_ast.source_fragments
            if attacked_lexeme.base_source_nucleus_id in row.source_nucleus_ids
            and row.evidence_grade == "exact_source_span"
        )
        _closed_assert(
            len(matching) == 1,
            "STEP11_RC0031_P3_B5_OWNER_ATTACK_PRECONDITION_INVALID",
        )
        without_fragment_ast = replace(
            base_candidate.surface_ast,
            source_fragments=tuple(
                row
                for row in base_candidate.surface_ast.source_fragments
                if row is not matching[0]
            ),
        )
        duplicate_fragment_ast = replace(
            base_candidate.surface_ast,
            source_fragments=(
                *base_candidate.surface_ast.source_fragments,
                replace(
                    matching[0],
                    source_anchor_id=matching[0].source_anchor_id + "_b5dup",
                ),
            ),
        )
        attacks = (
            (
                replace(base_candidate, surface_ast=without_fragment_ast),
                "STEP11_RC0031_PRODUCT_OWNER_SOURCE_FRAGMENT_UNRESOLVED",
            ),
            (
                replace(base_candidate, surface_ast=duplicate_fragment_ast),
                "STEP11_RC0031_PRODUCT_OWNER_SOURCE_FRAGMENT_AMBIGUOUS",
            ),
        )
        for attacked_candidate, expected_code in attacks:
            try:
                projection(
                    attacked_candidate,
                    successor_snapshot=successor,
                    lexical_atom_specs=lexical_specs,
                )
            except lexical_owner.Step11GroundedLexicalizationError as exc:
                allowed_codes = {
                    expected_code,
                    "STEP11_RC0031_PRODUCT_OWNER_BASE_CANDIDATE_INVALID",
                }
                _closed_assert(
                    exc.code in allowed_codes
                    and str(exc) == exc.code
                    and exc.args == (exc.code,),
                    "STEP11_RC0031_P3_B5_PRODUCT_OWNER_EXPRESSION_ATTACK_INVALID",
                )
            except Exception:
                pytest.fail(
                    "STEP11_RC0031_P3_B5_PRODUCT_OWNER_EXPRESSION_ATTACK_INVALID",
                    pytrace=False,
                )
            else:
                pytest.fail(
                    "STEP11_RC0031_P3_B5_PRODUCT_OWNER_EXPRESSION_ATTACK_ACCEPTED",
                    pytrace=False,
                )
    _closed_assert(
        projected_occurrence_count
        == _B5_DESIGN_CONTRACT["clause_ready_owner_occurrence_count"],
        "STEP11_RC0031_P3_B5_PRODUCT_OWNER_EXPRESSION_DENOMINATOR_INVALID",
    )


def test_rc0031_p3_b5_relation_connected_product_clusters_account_exact38_with_load4() -> None:
    _b5_surface_api_or_red(_B5_CLUSTER_NOT_AVAILABLE)
    observed_loads: list[tuple[int, ...]] = []
    source_atom_ids: list[str] = []
    for context in _rc0031_final_candidate_contexts():
        _case, baseline, successor, _specs, candidate, _witness = context
        records, *_source_authority = (
            _inverse_module()._step11_rc0030_validated_source_records(
                successor,
                inventory_result=baseline.inventory_result,
            )
        )
        expected_by_source = {
            str(source_id): (
                str(family),
                str(key),
                str(direction),
                tuple(str(owner_id) for owner_id in owner_ids),
            )
            for source_id, family, key, direction, owner_ids in records
            if str(source_id) != _EXPECTED_REUSE_SOURCE_ID
        }
        candidate = context[4]
        bindings = tuple(candidate.surface_realization_plan.proposition_clause_bindings)
        context_loads: list[int] = []
        context_source_atom_ids: list[str] = []
        for binding in bindings:
            _closed_assert(
                _EXPECTED_REUSE_SOURCE_ID not in binding.source_atom_ids
                and len(
                    {
                        len(binding.source_atom_ids),
                        len(binding.semantic_families),
                        len(binding.semantic_keys),
                        len(binding.directions),
                        len(binding.source_atom_owner_ids),
                    }
                )
                == 1,
                "STEP11_RC0031_P3_B5_PRODUCT_PROPOSITION_CLUSTER_INVALID",
            )
            new_rows = tuple(
                (source_id, family, key, direction, owners)
                for source_id, family, key, direction, owners in zip(
                    binding.source_atom_ids,
                    binding.semantic_families,
                    binding.semantic_keys,
                    binding.directions,
                    binding.source_atom_owner_ids,
                )
                if source_id != _EXPECTED_REUSE_SOURCE_ID
            )
            if not new_rows:
                continue
            context_loads.append(len(new_rows))
            context_source_atom_ids.extend(row[0] for row in new_rows)
            _closed_assert(
                len(new_rows)
                <= _B5_DESIGN_CONTRACT[
                    "product_proposition_cluster_load_max"
                ]
                and all(
                    expected_by_source.get(str(source_id))
                    == (
                        str(family),
                        str(key),
                        str(direction),
                        tuple(str(owner_id) for owner_id in owners),
                    )
                    for source_id, family, key, direction, owners in new_rows
                )
                and _b5_owner_sets_are_connected(
                    tuple(
                        expected_by_source[str(row[0])][3]
                        for row in new_rows
                        if str(row[0]) in expected_by_source
                    )
                ),
                "STEP11_RC0031_P3_B5_PRODUCT_PROPOSITION_CLUSTER_INVALID",
            )
        _closed_assert(
            len(context_source_atom_ids) == len(set(context_source_atom_ids))
            and set(context_source_atom_ids) == set(expected_by_source),
            "STEP11_RC0031_P3_B5_PRODUCT_PROPOSITION_CLUSTER_INVALID",
        )
        source_atom_ids.extend(context_source_atom_ids)
        observed_loads.append(tuple(context_loads))
    product_cluster_loads = tuple(
        load for context_loads in observed_loads for load in context_loads
    )
    _closed_assert(
        len(product_cluster_loads)
        <= _B5_DESIGN_CONTRACT["product_proposition_cluster_max"]
        and sum(product_cluster_loads)
        == _B5_DESIGN_CONTRACT["new_semantic_atom_count"]
        and max(product_cluster_loads, default=0)
        <= _B5_DESIGN_CONTRACT["product_proposition_cluster_load_max"]
        and len(source_atom_ids)
        == _B5_DESIGN_CONTRACT["new_semantic_atom_count"],
        "STEP11_RC0031_P3_B5_PRODUCT_PROPOSITION_CLUSTER_INVALID",
    )


def test_rc0031_p3_b5_ast_first_reception_preserves_bound10_and_adds_unmatched1() -> None:
    _b5_surface_api_or_red(_B5_RECEPTION_NOT_AVAILABLE)
    represented_base_bindings = 0
    additional_bindings = 0
    total_bindings = 0
    for _case, _base, successor, _specs, candidate, _witness in (
        _rc0031_final_candidate_contexts()
    ):
        product_rows = tuple(candidate.reception_bindings)
        base_bindings = tuple(
            candidate.base_candidate.surface_ast.reception_antecedent_bindings
        )
        required_opportunities = tuple(
            row
            for row in successor.base_snapshot.reception_opportunities
            if row.retention == "required" or row.safety_required is True
        )
        required_opportunity_ids = {
            str(row.source_id) for row in required_opportunities
        }
        opportunity_by_id = {
            str(row.source_id): row for row in required_opportunities
        }
        base_opportunity_ids = {
            str(source_id)
            for binding in base_bindings
            for source_id in binding.source_reception_opportunity_ids
        }
        product_opportunity_ids = tuple(
            str(row.source_reception_opportunity_id) for row in product_rows
        )
        by_base_id = {
            str(row.source_base_binding_id): row
            for row in product_rows
            if row.source_base_binding_id is not None
        }
        _closed_assert(
            len(by_base_id)
            == sum(row.source_base_binding_id is not None for row in product_rows)
            and len(product_opportunity_ids)
            == len(set(product_opportunity_ids))
            and set(product_opportunity_ids) == required_opportunity_ids,
            "STEP11_RC0031_P3_B5_AST_BOUND_RECEPTION_INVALID",
        )
        for binding in base_bindings:
            row = by_base_id.get(str(binding.binding_id))
            opportunity = (
                opportunity_by_id.get(str(row.source_reception_opportunity_id))
                if row is not None
                else None
            )
            expected_targets = tuple(
                _b5_normalize_nucleus_id(successor, value)
                for value in binding.source_target_nucleus_ids
            )
            expected_supports = tuple(
                dict.fromkeys(
                    _b5_normalize_nucleus_id(successor, value)
                    for value in (
                        *binding.antecedent_nucleus_ids,
                        *binding.supporting_nucleus_ids,
                    )
                )
            )
            _closed_assert(
                row is not None
                and opportunity is not None
                and str(row.source_reception_opportunity_id)
                in {str(value) for value in binding.source_reception_opportunity_ids}
                and row.source_scope == str(opportunity.family)
                and row.source_target_owner_ids == expected_targets
                and row.supporting_source_owner_ids == expected_supports
                and row.reception_act in binding.allowed_response_acts
                and row.association_basis
                == "exact_base_ast_antecedent_binding"
                and row.additional_clause is False,
                "STEP11_RC0031_P3_B5_AST_BOUND_RECEPTION_INVALID",
            )
            represented_base_bindings += 1
        additional = tuple(
            row for row in product_rows if row.source_base_binding_id is None
        )
        _closed_assert(
            all(
                row.additional_clause is True
                and row.association_basis == "unmatched_required_opportunity"
                and (
                    opportunity := opportunity_by_id.get(
                        str(row.source_reception_opportunity_id)
                    )
                )
                is not None
                and row.source_scope == str(opportunity.family)
                and row.reception_act == str(opportunity.reception_act)
                and row.source_target_owner_ids
                == tuple(
                    _b5_normalize_nucleus_id(successor, value)
                    for value in opportunity.target_nucleus_ids
                )
                and row.supporting_source_owner_ids
                == tuple(
                    _b5_normalize_nucleus_id(successor, value)
                    for value in opportunity.support_nucleus_ids
                )
                for row in additional
            )
            and {str(row.source_reception_opportunity_id) for row in additional}
            == required_opportunity_ids - base_opportunity_ids,
            "STEP11_RC0031_P3_B5_ADDITIONAL_RECEPTION_INVALID",
        )
        additional_bindings += len(additional)
        total_bindings += len(product_rows)
    _closed_assert(
        represented_base_bindings
        == _B5_DESIGN_CONTRACT["base_ast_reception_binding_count"]
        and additional_bindings
        == _B5_DESIGN_CONTRACT["unmatched_required_reception_count"]
        and total_bindings
        == _B5_DESIGN_CONTRACT["required_reception_opportunity_count"],
        "STEP11_RC0031_P3_B5_AST_BOUND_RECEPTION_INVALID",
    )


def test_rc0031_p3_b5_product_surface_is_schema_free_metadata_free_and_case_agnostic() -> None:
    builder, _validator = _b5_surface_api_or_red(_B5_BOUNDARY_NOT_AVAILABLE)
    projection = _b5_owner_projection_or_red()
    try:
        lexical_text = _LEXICAL_PATH.read_bytes()[
            _B5_LEXICAL_PREDECESSOR_BYTES:
        ].decode("utf-8", errors="strict")
        surface_text = _SURFACE_PATH.read_bytes()[
            _B5_SURFACE_PREDECESSOR_BYTES:
        ].decode("utf-8", errors="strict")
        lexical_tree = ast.parse(lexical_text)
        surface_tree = ast.parse(surface_text)
    except (UnicodeError, SyntaxError):
        pytest.fail(_B5_BOUNDARY_NOT_AVAILABLE, pytrace=False)
    lexical_functions = tuple(
        node
        for node in lexical_tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    )
    surface_functions = tuple(
        node
        for node in surface_tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    )
    _closed_assert(
        sum(node.name == projection.__name__ for node in lexical_functions) == 1
        and sum(node.name == builder.__name__ for node in surface_functions) == 1,
        "STEP11_RC0031_P3_B5_CASE_BRANCH_SCAN_INVALID",
    )

    def branch_selector_names(function: ast.AST) -> set[str]:
        selectors: list[ast.AST] = []
        for node in ast.walk(function):
            if isinstance(node, (ast.If, ast.IfExp)):
                selectors.append(node.test)
            elif isinstance(node, ast.Match):
                selectors.append(node.subject)
            elif isinstance(node, ast.Subscript):
                selectors.append(node.slice)
            elif (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "get"
                and node.args
            ):
                selectors.append(node.args[0])
            elif isinstance(
                node,
                (ast.DictComp, ast.GeneratorExp, ast.ListComp, ast.SetComp),
            ):
                selectors.extend(
                    condition
                    for generator in node.generators
                    for condition in generator.ifs
                )
        return {
            value
            for selector in selectors
            for child in ast.walk(selector)
            for value in (
                child.id.lower()
                if isinstance(child, ast.Name)
                else child.attr.lower()
                if isinstance(child, ast.Attribute)
                else "",
            )
            if value
        }

    lexical_forbidden_branch_names = {
        "case",
        "case_id",
        "candidate_id",
        "candidate_version_id",
        "family",
        "input_word",
        "review",
        "review_family",
        "semantic_family",
        "severity",
        "source_base_candidate_id",
        "source_word",
    }
    surface_forbidden_branch_names = {
        "case",
        "case_id",
        "candidate_id",
        "candidate_version_id",
        "input_word",
        "review",
        "review_family",
        "severity",
        "source_base_candidate_id",
        "source_word",
    }
    lexical_function_texts = tuple(
        ast.get_source_segment(lexical_text, function)
        for function in lexical_functions
    )
    surface_function_texts = tuple(
        ast.get_source_segment(surface_text, function)
        for function in surface_functions
    )
    _closed_assert(
        all(type(value) is str for value in lexical_function_texts)
        and all(type(value) is str for value in surface_function_texts)
        and not set().union(
            *(branch_selector_names(function) for function in lexical_functions)
        )
        & lexical_forbidden_branch_names
        and not set().union(
            *(branch_selector_names(function) for function in surface_functions)
        )
        & surface_forbidden_branch_names
        and all(
            marker not in value
            for value in (*lexical_function_texts, *surface_function_texts)
            for marker in (
                "nls3s_b001_",
                "expected_output",
                "candidate_metadata",
                "review_family",
                "severity",
            )
        ),
        "STEP11_RC0031_P3_B5_CASE_BRANCH_PRESENT",
    )

    forbidden_body_tokens = (
        b"cocolon.emlis",
        b"schema_version",
        b"candidate_id",
        b"source_atom_id",
        b"source_reception_opportunity_id",
        b"nls3s_b001_",
    )
    semantic_count = 0
    reuse_count = 0
    reception_count = 0
    for context in _rc0031_final_candidate_contexts():
        candidate = context[4]
        body = candidate.final_utf8_bytes
        plan = candidate.surface_realization_plan
        _closed_assert(
            not any(token in body for token in forbidden_body_tokens)
            and candidate.base_candidate.rendered_surface.visible_source_anchor_count
            <= _B5_DESIGN_CONTRACT["visible_source_anchor_max"]
            and plan.maximum_visible_clauses_per_grammatical_sentence
            == _B5_DESIGN_CONTRACT[
                "visible_clauses_per_grammatical_sentence_max"
            ]
            and plan.maximum_grammatical_complexity_load
            == _B5_DESIGN_CONTRACT["grammatical_complexity_load_max"]
            and plan.maximum_repeated_joiner_per_group
            == _B5_DESIGN_CONTRACT["repeated_joiner_per_group_max"]
            and plan.maximum_observation_clauses_per_sentence
            == _B5_DESIGN_CONTRACT["realization_units_per_group_max"]
            and plan.peak_grammatical_complexity_load
            <= plan.maximum_grammatical_complexity_load
            and plan.peak_group_repeated_joiner_count
            <= plan.maximum_repeated_joiner_per_group,
            "STEP11_RC0031_P3_B5_PRODUCT_BOUNDARY_INVALID",
        )
        semantic_count += candidate.rendered_surface.semantic_atom_count
        reuse_count += candidate.rendered_surface.exact_reuse_count
        reception_count += candidate.rendered_surface.reception_predication_count
    _closed_assert(
        semantic_count == _B5_DESIGN_CONTRACT["new_semantic_atom_count"]
        and reuse_count == _B5_DESIGN_CONTRACT["verified_base_reuse_count"]
        and reception_count
        == _B5_DESIGN_CONTRACT["required_reception_opportunity_count"],
        "STEP11_RC0031_P3_B5_PRODUCT_BOUNDARY_INVALID",
    )
# ---------------------------------------------------------------------------
# rc0031 P3 B6 source-congruence / role-inflection design freeze and RED-only
# ---------------------------------------------------------------------------

_B6_TEST_PREFIX_BYTES = 202_968
_B6_TEST_PREFIX_SHA256 = (
    "0821ec5408c43208bdef2c776d3d6c13363ad6c3b21cd79779e95d0aa8ff3813"
)
_B6_PREDECESSOR_TOP_LEVEL_TEST_COUNT = 30
_B6_PREDECESSOR_TOP_LEVEL_TEST_NAMES_SHA256 = (
    "c517fb179395a9f099cffa1c95ded175c337aba7af269bab228508da407a089e"
)
_B6_TEST_CLASS_NAME = "TestRc0031P3B6DesignFreezeRedOnly"
_B6_NEW_TEST_NAMES = frozenset(
    {
        "test_rc0031_p3_b6_freeze_scope_and_predecessor_behavior_are_exact",
        "test_rc0031_p3_b6_denominators_authority_chain_resource_and_privacy_are_exact",
        "test_rc0031_p3_b6_required_meaning_source_successor_and_atom_authorities_are_congruent_or_fail_closed",
        "test_rc0031_p3_b6_product_owner_expressions_are_boundary_safe_and_role_inflected_or_fail_closed",
        "test_rc0031_p3_b6_reception_focus_target_support_act_and_aspect_are_congruent_or_fail_closed",
        "test_rc0031_p3_b6_typed_recomposition_is_body_only_recoverable_resource_bounded_and_private",
    }
)
_B6_SOURCE_CONGRUENCE_RED = (
    "STEP11_RC0031_P3_B6_SOURCE_CONGRUENCE_NOT_PROVED"
)
_B6_OWNER_ROLE_INFLECTION_RED = (
    "STEP11_RC0031_P3_B6_OWNER_ROLE_INFLECTION_NOT_PROVED"
)
_B6_RECEPTION_FOCUS_RED = (
    "STEP11_RC0031_P3_B6_RECEPTION_FOCUS_AUTHORITY_NOT_PROVED"
)
_B6_TYPED_RECOMPOSITION_RED = (
    "STEP11_RC0031_P3_B6_TYPED_RECOMPOSITION_NOT_PROVED"
)


def _b6_context(case_id: str) -> tuple[Any, ...]:
    matches = tuple(
        row for row in _b5_predecessor_candidate_contexts() if row[0] == case_id
    )
    _closed_assert(
        bool(matches),
        "STEP11_RC0031_P3_B6_PREDECESSOR_CONTEXT_DRIFT",
    )
    return matches[0]


def _b6_function_tree(value: Any, code: str) -> ast.AST:
    try:
        source = inspect.getsource(value)
        return ast.parse(source)
    except (OSError, TypeError, UnicodeError, SyntaxError):
        pytest.fail(code, pytrace=False)


def _b6_function_symbols(value: Any, code: str) -> frozenset[str]:
    tree = _b6_function_tree(value, code)
    return frozenset(
        child.id
        if isinstance(child, ast.Name)
        else child.attr
        if isinstance(child, ast.Attribute)
        else child.value
        if isinstance(child, ast.Constant) and type(child.value) is str
        else ""
        for child in ast.walk(tree)
        if isinstance(child, (ast.Name, ast.Attribute, ast.Constant))
    )


def _b6_has_visible_support_difference(value: Any) -> bool:
    tree = _b6_function_tree(value, _B6_RECEPTION_FOCUS_RED)
    return any(
        (
            isinstance(child, ast.Call)
            and isinstance(child.func, ast.Attribute)
            and child.func.attr == "difference"
        )
        or (isinstance(child, ast.BinOp) and isinstance(child.op, ast.Sub))
        or (
            isinstance(child, ast.Compare)
            and any(isinstance(operator, ast.NotIn) for operator in child.ops)
        )
        for child in ast.walk(tree)
    )


def _b6_has_per_atom_explanatory_bundle(value: Any) -> bool:
    tree = _b6_function_tree(value, _B6_TYPED_RECOMPOSITION_RED)
    symbols = _b6_function_symbols(value, _B6_TYPED_RECOMPOSITION_RED)
    return bool(
        any(
            isinstance(child, (ast.For, ast.comprehension))
            for child in ast.walk(tree)
        )
        and {
            "source_atom_ids",
            "modality_cues",
            "polarity_cues",
            "referent_scope_cues",
        }
        <= symbols
    )


def _b6_has_arbitrary_scalar_cut(value: Any) -> bool:
    tree = _b6_function_tree(value, _B6_OWNER_ROLE_INFLECTION_RED)
    integer_slice_bounds = {
        child.value
        for child in ast.walk(tree)
        if isinstance(child, ast.Constant)
        and type(child.value) is int
        and child.value > 0
        and any(
            isinstance(parent, ast.Slice)
            and child in {parent.lower, parent.upper, parent.step}
            for parent in ast.walk(tree)
            if isinstance(parent, ast.Slice)
        )
    }
    has_mid_fragment_ellipsis = any(
        isinstance(child, ast.Constant) and child.value == "…"
        for child in ast.walk(tree)
    )
    return bool(integer_slice_bounds and has_mid_fragment_ellipsis)


def _b6_required_relation_chain_is_exact(context: tuple[Any, ...]) -> bool:
    _case, _baseline, successor, lexical_specs, candidate, _witness = context
    authority_rows = tuple(
        row
        for row in successor.relation_construction_authority.relation_authorities
        if row.source_retention == "required"
        and tuple(row.source_meaning_arc_keys) == ("whole_input:source_order",)
    )
    if len(authority_rows) != 1:
        return False
    authority = authority_rows[0]
    endpoint_rows = tuple(
        row
        for row in lexical_specs.relation_endpoint_atoms
        if row.experiment_relation_id == authority.experiment_relation_id
    )
    atom_rows = tuple(
        row
        for row in candidate.relation_atoms
        if row.experiment_relation_id == authority.experiment_relation_id
    )
    return bool(
        len(endpoint_rows) == 2
        and {row.relation_endpoint_role for row in endpoint_rows}
        == {"from", "to"}
        and all(
            row.source_relation_type == authority.source_relation_type
            and row.effective_relation_type == authority.effective_relation_type
            and row.relation_direction == authority.direction
            and row.authority_basis == authority.authority_basis
            for row in endpoint_rows
        )
        and len(atom_rows) == 1
        and atom_rows[0].source_relation_type == authority.source_relation_type
        and atom_rows[0].effective_relation_type
        == authority.effective_relation_type
        and atom_rows[0].direction == authority.direction
        and atom_rows[0].authority_basis == authority.authority_basis
    )


def _b6_atom_authority_chain_accounting() -> tuple[int, int]:
    accounted_ids: list[str] = []
    exact_join_count = 0
    for _case, baseline, successor, _specs, candidate, _witness in (
        _b5_predecessor_candidate_contexts()
    ):
        records, *_source_authority = (
            _inverse_module()._step11_rc0030_validated_source_records(
                successor,
                inventory_result=baseline.inventory_result,
            )
        )
        expected_by_id = {
            str(source_id): (
                str(family),
                str(key),
                str(direction),
                tuple(str(owner_id) for owner_id in owner_ids),
            )
            for source_id, family, key, direction, owner_ids in records
            if str(source_id) != _EXPECTED_REUSE_SOURCE_ID
        }
        context_ids: list[str] = []
        for binding in candidate.surface_realization_plan.proposition_clause_bindings:
            for source_id, family, key, direction, owners in zip(
                binding.source_atom_ids,
                binding.semantic_families,
                binding.semantic_keys,
                binding.directions,
                binding.source_atom_owner_ids,
                strict=True,
            ):
                if source_id == _EXPECTED_REUSE_SOURCE_ID:
                    continue
                context_ids.append(str(source_id))
                exact_join_count += expected_by_id.get(str(source_id)) == (
                    str(family),
                    str(key),
                    str(direction),
                    tuple(str(owner_id) for owner_id in owners),
                )
        _closed_assert(
            len(context_ids) == len(set(context_ids))
            and set(context_ids) == set(expected_by_id),
            "STEP11_RC0031_P3_B6_AUTHORITY_CHAIN_DRIFT",
        )
        accounted_ids.extend(context_ids)
    return len(accounted_ids), exact_join_count


def _b6_required_relation_is_meaning_congruent(
    context: tuple[Any, ...],
) -> bool:
    _case, _baseline, successor, _lexical_specs, _candidate, _witness = context
    rows = tuple(
        row
        for row in successor.relation_construction_authority.relation_authorities
        if row.source_retention == "required"
        and tuple(row.source_meaning_arc_keys) == ("whole_input:source_order",)
    )
    if len(rows) != 1:
        return False
    row = rows[0]
    # This is a negative semantic contract over body-free authority codes.  A
    # source-order relation may not turn the frozen independent-unit meaning
    # into a directional continuation/subordination claim.
    return (
        row.source_relation_type,
        row.effective_relation_type,
        row.direction,
        row.authority_basis,
    ) != (
        "continuation_or_refusal",
        "continuation_or_refusal",
        "source_to_target",
        "grounded_plan_projection",
    )


def _b6_owner_role_evidence() -> tuple[int, int]:
    multi_role_owner_occurrences = 0
    projected_owner_occurrences = 0
    projection = _b5_owner_projection_or_red()
    for _case, _baseline, successor, lexical_specs, candidate, _witness in (
        _b5_predecessor_candidate_contexts()
    ):
        projected = projection(
            candidate.base_candidate,
            successor_snapshot=successor,
            lexical_atom_specs=lexical_specs,
        )
        projected_owner_occurrences += len(projected)
        roles_by_owner: dict[str, set[str]] = {}
        for binding in candidate.surface_realization_plan.proposition_clause_bindings:
            for family, direction, owners in zip(
                binding.semantic_families,
                binding.directions,
                binding.source_atom_owner_ids,
                strict=True,
            ):
                if family in {"relation", "semantic_link"} and len(owners) == 2:
                    role_names = (
                        ("relation_source", "relation_target")
                        if direction == "source_to_target"
                        else ("relation_peer", "relation_peer")
                    )
                elif family == "construction":
                    role_names = tuple("construction_role" for _row in owners)
                else:
                    role_names = tuple("terminal_role" for _row in owners)
                for owner, role_name in zip(owners, role_names, strict=True):
                    roles_by_owner.setdefault(str(owner), set()).add(role_name)
        for reception in candidate.reception_bindings:
            for owner in reception.source_target_owner_ids:
                roles_by_owner.setdefault(str(owner), set()).add(
                    "reception_target"
                )
            for owner in reception.supporting_source_owner_ids:
                roles_by_owner.setdefault(str(owner), set()).add(
                    "reception_support"
                )
        multi_role_owner_occurrences += sum(
            len(role_names) > 1 for role_names in roles_by_owner.values()
        )
    return projected_owner_occurrences, multi_role_owner_occurrences


def _b6_reception_focus_evidence() -> tuple[int, int, int, int]:
    total = 0
    visible_overlap = 0
    missing_distinct_focus = 0
    incompatible_aspect = 0
    for case_id, _baseline, successor, _lexical, candidate, _witness in (
        _b5_predecessor_candidate_contexts()
    ):
        nucleus_by_id = {
            str(key): row
            for row in successor.base_snapshot.nuclei
            for key in (row.source_id, row.actual_source_id)
        }
        for row in candidate.reception_bindings:
            total += 1
            targets = set(row.source_target_owner_ids)
            supports = set(row.supporting_source_owner_ids)
            focuses = set(getattr(row, "source_focus_owner_ids", ()))
            visible_overlap += bool(targets & supports)
            if case_id == "nls3s_b001_0063" and not (
                focuses or supports - targets
            ):
                missing_distinct_focus += 1
            target_nuclei = tuple(
                nucleus_by_id[owner]
                for owner in targets
                if owner in nucleus_by_id
            )
            incompatible_aspect += bool(
                row.reception_act == "honor_concrete_action"
                and any(
                    nucleus.modality == "intended"
                    or nucleus.temporal_scope in {"future", "present_to_future"}
                    for nucleus in target_nuclei
                )
            )
    return total, visible_overlap, missing_distinct_focus, incompatible_aspect


def _b6_typed_recomposition_evidence() -> tuple[int, int, int]:
    source_atom_count = 0
    required_modifier_count = 0
    actual_modifier_count = 0
    for context in _b5_predecessor_candidate_contexts():
        candidate = context[4]
        body = candidate.final_utf8_bytes
        if type(body) is not bytes:
            return (0, 0, 0)
        for binding in candidate.surface_realization_plan.proposition_clause_bindings:
            source_atom_count += len(binding.source_atom_ids)
            construction_ids = tuple(
                source_id
                for source_id, family in zip(
                    binding.source_atom_ids,
                    binding.semantic_families,
                    strict=True,
                )
                if family == "construction"
            )
            nonconstruction_ids = tuple(
                source_id
                for source_id, family in zip(
                    binding.source_atom_ids,
                    binding.semantic_families,
                    strict=True,
                )
                if family != "construction"
            )
            required_modifier_count += (
                len(construction_ids)
                if nonconstruction_ids
                else max(0, len(construction_ids) - 1)
            )
            actual_modifier_count += len(binding.construction_modifier_atom_ids)
    return (
        source_atom_count,
        required_modifier_count,
        actual_modifier_count,
    )


class TestRc0031P3B6DesignFreezeRedOnly:
    def test_rc0031_p3_b6_freeze_scope_and_predecessor_behavior_are_exact(
        self,
    ) -> None:
        source = Path(__file__).resolve().read_bytes()
        marker = (
            b"# ---------------------------------------------------------------------------\n"
            b"# rc0031 P3 B6 source-congruence / role-inflection design freeze and RED-only\n"
            b"# ---------------------------------------------------------------------------\n"
        )
        _closed_assert(
            source.count(marker) == 1,
            "STEP11_RC0031_P3_B6_TEST_PREFIX_INVALID",
        )
        prefix = source[: source.index(marker)]
        tree = ast.parse(source.decode("utf-8", errors="strict"))
        top_level_test_names = tuple(
            sorted(
                node.name
                for node in tree.body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name.startswith("test_")
            )
        )
        class_rows = tuple(
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == _B6_TEST_CLASS_NAME
        )
        b6_test_names = frozenset(
            child.name
            for row in class_rows
            for child in row.body
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            and child.name.startswith("test_")
        )
        top_level_name_material = (
            "\n".join(top_level_test_names) + "\n"
        ).encode("utf-8")
        _closed_assert(
            len(prefix) == _B6_TEST_PREFIX_BYTES
            and hashlib.sha256(prefix).hexdigest() == _B6_TEST_PREFIX_SHA256
            and len(top_level_test_names)
            == _B6_PREDECESSOR_TOP_LEVEL_TEST_COUNT
            and hashlib.sha256(top_level_name_material).hexdigest()
            == _B6_PREDECESSOR_TOP_LEVEL_TEST_NAMES_SHA256
            and len(class_rows) == 1
            and b6_test_names == _B6_NEW_TEST_NAMES
            and _EXPECTED_P3_ACTIVE
            == frozenset(
                {
                    "ai/services/ai_inference/emlis_ai_step11_rc0031_experiment_surface_catalog_v3.py",
                    "ai/tests/fixtures/emlis_nls_v3/cycle_001/rc0031_representative8_body_free.json",
                    "ai/tests/test_emlis_nls_v3_s11_rc0031_proposition_surface_red.py",
                    "ai/tests/test_emlis_nls_v3_s11_rc0031_proposition_surface_mutation.py",
                    "ai/tests/test_emlis_nls_v3_s11_rc0031_forward_inverse_independence.py",
                }
            ),
            "STEP11_RC0031_P3_B6_TEST_SCOPE_DRIFT",
        )

    def test_rc0031_p3_b6_denominators_authority_chain_resource_and_privacy_are_exact(
        self,
    ) -> None:
        probe = _b5_design_probe()
        authority_count, exact_authority_join_count = (
            _b6_atom_authority_chain_accounting()
        )
        fixture = json.loads(_P1_FIXTURE.read_text(encoding="utf-8"))
        privacy = fixture.get("privacy_contract", {})
        _closed_assert(
            probe["context_count"] == 10
            and probe["unique_case_count"] == 8
            and probe["new_semantic_atom_count"] == 38
            and authority_count == 38
            and exact_authority_join_count == 38
            and probe["verified_base_reuse_count"] == 1
            and probe["family_counts"] == _B5_EXPECTED_FAMILY_COUNTS
            and probe["owner_occurrence_count"] == 24
            and probe["exactly_one_source_fragment_count"] == 24
            and probe["required_reception_count"] == 11
            and probe["base_ast_binding_count"] == 10
            and probe["unmatched_required_count"] == 1
            and probe["resource_envelopes"] == {(2, 4, 2, 4)}
            and probe["visible_source_anchor_max"] <= 1
            and fixture.get("body_free") is True
            and privacy.get("body_or_quote_exported") is False
            and privacy.get("parsed_span_or_binding_detail_exported") is False
            and privacy.get("unsalted_body_digest_exported") is False
            and privacy.get("runtime_connected") is False
            and privacy.get("formal_or_production_eligible") is False,
            "STEP11_RC0031_P3_B6_DENOMINATOR_AUTHORITY_RESOURCE_PRIVACY_DRIFT",
        )

    def test_rc0031_p3_b6_required_meaning_source_successor_and_atom_authorities_are_congruent_or_fail_closed(
        self,
    ) -> None:
        context = _b6_context("nls3s_b001_0035")
        _closed_assert(
            _b6_required_relation_chain_is_exact(context)
            and _b6_required_relation_is_meaning_congruent(context),
            _B6_SOURCE_CONGRUENCE_RED,
        )

    def test_rc0031_p3_b6_product_owner_expressions_are_boundary_safe_and_role_inflected_or_fail_closed(
        self,
    ) -> None:
        projection = _b5_owner_projection_or_red()
        projected_count, multi_role_count = _b6_owner_role_evidence()
        surface = _surface_module()
        render_names = _b6_function_symbols(
            surface._step11_rc0031_product_render_cluster,
            _B6_OWNER_ROLE_INFLECTION_RED,
        ) | _b6_function_symbols(
            surface._step11_rc0031_product_render,
            _B6_OWNER_ROLE_INFLECTION_RED,
        )
        _closed_assert(
            projected_count == 24
            and multi_role_count > 0
            and not _b6_has_arbitrary_scalar_cut(projection)
            and {
                "head_source_atom_id",
                "construction_modifier_atom_ids",
                "construction_modifier_target_owner_ids",
                "owner_role_particle_patterns",
                "owner_kind_inflection_patterns",
            }
            <= render_names,
            _B6_OWNER_ROLE_INFLECTION_RED,
        )

    def test_rc0031_p3_b6_reception_focus_target_support_act_and_aspect_are_congruent_or_fail_closed(
        self,
    ) -> None:
        total, overlap, missing_focus, incompatible_aspect = (
            _b6_reception_focus_evidence()
        )
        renderer = _surface_module()._step11_rc0031_product_render
        render_names = _b6_function_symbols(
            renderer,
            _B6_RECEPTION_FOCUS_RED,
        )
        _closed_assert(
            total == 11
            and missing_focus == 0
            and incompatible_aspect == 0
            and {"source_target_owner_ids", "supporting_source_owner_ids"}
            <= render_names
            and _b6_has_visible_support_difference(renderer)
            and overlap >= 0,
            _B6_RECEPTION_FOCUS_RED,
        )

    def test_rc0031_p3_b6_typed_recomposition_is_body_only_recoverable_resource_bounded_and_private(
        self,
    ) -> None:
        source_count, required_modifiers, actual_modifiers = (
            _b6_typed_recomposition_evidence()
        )
        renderer = _surface_module()._step11_rc0031_product_render_cluster
        render_names = _b6_function_symbols(
            renderer,
            _B6_TYPED_RECOMPOSITION_RED,
        )
        _closed_assert(
            source_count == 38
            and required_modifiers > 0
            and actual_modifiers == required_modifiers
            and {
                "head_source_atom_id",
                "construction_modifier_atom_ids",
                "construction_modifier_target_owner_ids",
            }
            <= render_names
            and not _b6_has_per_atom_explanatory_bundle(renderer),
            _B6_TYPED_RECOMPOSITION_RED,
        )
