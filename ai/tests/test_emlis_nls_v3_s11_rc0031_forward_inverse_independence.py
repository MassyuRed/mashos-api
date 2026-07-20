# -*- coding: utf-8 -*-
from __future__ import annotations

"""P3 RED-first viability boundary for the rc0031 inverse path.

This exact-two suite does not implement or import an rc0031 Parser/Matcher.
It first freezes the P2 predecessor and the inverse resource/privacy boundary,
then uses the already-frozen rc0030 body-only base parser and independent base
matcher to test whether P2 re-exposes meaning that is already exact in the
base body.  No body is embedded in a parameter id, assertion, or exception.
"""

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

_P2_FROZEN_FILES = {
    _LEXICAL_PATH: (
        129_615,
        "592f3ab7c90831c3191f51e9e7dd9a1f8c3fe4add1fd31bba9fdc65dccaecc28",
    ),
    _SURFACE_PATH: (
        482_504,
        "e19eae9a62068ec3095785fc20aafda6c277df96470a7b1e48ca51ca3142d7d4",
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
_MATCHER_P2_PREFIX_BYTES = 722_658
_MATCHER_P2_PREFIX_SHA256 = (
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


def test_rc0031_p3_p2_freeze_scope_and_inherited_inverse_bounds_are_exact() -> None:
    for path, (byte_count, expected_sha256) in _P2_FROZEN_FILES.items():
        _closed_assert(
            path.stat().st_size == byte_count
            and _sha256(path) == expected_sha256,
            "STEP11_RC0031_P3_P2_FREEZE_DRIFT",
        )
    matcher_prefix = _MATCHER_PATH.read_bytes()[:_MATCHER_P2_PREFIX_BYTES]
    _closed_assert(
        len(matcher_prefix) == _MATCHER_P2_PREFIX_BYTES
        and hashlib.sha256(matcher_prefix).hexdigest()
        == _MATCHER_P2_PREFIX_SHA256,
        "STEP11_RC0031_P3_MATCHER_PREFIX_DRIFT",
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
    _closed_assert(
        type(fixture) is dict
        and fixture.get("body_free") is True
        and not (_all_mapping_keys(fixture) & _FORBIDDEN_BODY_KEYS),
        "STEP11_RC0031_P3_BODY_FREE_AUTHORITY_INVALID",
    )

    catalog_owner = importlib.import_module(
        "emlis_ai_step11_rc0031_experiment_surface_catalog_v3"
    )
    catalog = catalog_owner.STEP11_RC0031_EXPERIMENT_SURFACE_CATALOG
    surface = importlib.import_module("emlis_ai_step11_natural_surface_v3")
    inverse = importlib.import_module("emlis_ai_step11_natural_surface_matcher_v3")
    _closed_assert(
        catalog_owner.validate_step11_rc0031_experiment_surface_catalog(catalog)
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
        "STEP11_RC0031_P3_RESOURCE_CONTRACT_DRIFT",
    )


def test_rc0031_p3_0001_base_reuse_and_duplicate_reexposition_is_resolved() -> None:
    p2 = _p2_test_module()
    surface = importlib.import_module("emlis_ai_step11_natural_surface_v3")
    inverse = importlib.import_module("emlis_ai_step11_natural_surface_matcher_v3")
    baseline, successor, lexical_specs = p2._forward_authority(
        "nls3s_b001_0001"
    )
    candidates = surface.build_step11_rc0031_experiment_surface_candidates(
        tuple(baseline.natural_candidates),
        successor_snapshot=successor,
        lexical_atom_specs=lexical_specs,
    )
    _closed_assert(
        len(candidates) == 1,
        "STEP11_RC0031_P3_0001_FORWARD_DENOMINATOR_INVALID",
    )
    candidate = candidates[0]
    base = candidate.base_candidate
    base_witness = inverse.parse_step11_rc0030_base_body_exact_reuse(
        base.final_utf8_bytes
    )
    independently_verified_reuse = (
        inverse.match_step11_rc0030_base_body_exact_reuse(
            base_witness,
            successor_snapshot=successor,
            inventory_result=baseline.inventory_result,
            content_plan=baseline.content_plan,
            discourse_plan=base.discourse_plan,
            current_input=baseline.projected_current_input,
        )
    )
    proposition_records = p2._atom_records(candidate)
    reexposed_source_ids = frozenset(proposition_records)
    verified_reuse_source_ids = frozenset(
        row.source_atom_id for row in independently_verified_reuse
    )
    duplicate_source_ids = reexposed_source_ids & verified_reuse_source_ids

    _closed_assert(
        len(independently_verified_reuse) == 1
        and tuple(row.semantic_family for row in independently_verified_reuse)
        == ("explicit_unknown",)
        and len(verified_reuse_source_ids) == 1,
        "STEP11_RC0031_P3_0001_REUSE_DENOMINATOR_INVALID",
    )
    _closed_assert(
        not duplicate_source_ids,
        "STEP11_RC0031_P3_DUPLICATE_BASE_REEXPOSITION_NOT_RESOLVED",
    )
