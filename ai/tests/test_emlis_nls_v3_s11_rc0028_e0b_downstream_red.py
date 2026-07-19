# -*- coding: utf-8 -*-
from __future__ import annotations

"""E0b semantic RED for the rc0028 downstream experiment boundary.

The predecessor intentionally has no rc0028-prefixed downstream APIs.  Keep
imports dynamic so that this file collects normally and fails at the missing
semantic-consumption boundary instead of failing during test collection.
All diagnostics are body-free closed codes.
"""

from dataclasses import dataclass
import importlib
from types import ModuleType
from typing import Any

import pytest


_OWNER_MODULES = {
    "lexicalization": "emlis_ai_step11_grounded_lexicalization_v3",
    "surface": "emlis_ai_step11_natural_surface_v3",
    "matcher": "emlis_ai_step11_natural_surface_matcher_v3",
    "gate": "emlis_ai_step11_hard_gate_v3",
}
_EXPERIMENT_CATALOG_MODULE = (
    "emlis_ai_step11_rc0028_experiment_surface_catalog_v3"
)
_EXPERIMENT_CATALOG_ATTRIBUTE = (
    "STEP11_RC0028_EXPERIMENT_SURFACE_CATALOG"
)

_SUCCESSOR_CONSTRUCTION_CODES = frozenset(
    {
        "balanced_consideration",
        "choice_uncertainty",
        "comparative_assessment",
        "decision_timing",
        "explicit_coexistence",
        "explicit_contrast",
        "nonreduction_boundary",
        "ordered_sequence",
        "parallel_addition",
        "particle_object",
        "purpose_action",
        "reported_self_assessment",
        "withheld_action",
    }
)
_KNOWN_BODY_ONLY_COLLISIONS = frozenset(
    {
        frozenset({"explicit_coexistence", "balanced_consideration"}),
        frozenset({"choice_uncertainty", "decision_timing"}),
        frozenset(
            {"comparative_assessment", "reported_self_assessment"}
        ),
    }
)


@dataclass(frozen=True, slots=True)
class _ClosureContract:
    contract_id: str
    owner: str
    api_name: str
    expected_closed_failure: str


_CLOSURE_CONTRACTS = (
    _ClosureContract(
        "construction-instance-cardinality-and-overlap",
        "surface",
        "build_step11_rc0028_experiment_surface_candidates",
        "STEP11_RC0028_CONSTRUCTION_CARDINALITY_MISMATCH",
    ),
    _ClosureContract(
        "relation-exactly-two-endpoints-and-direction",
        "matcher",
        "match_step11_rc0028_experiment_surface",
        "STEP11_RC0028_RELATION_ENDPOINT_CARDINALITY_MISMATCH",
    ),
    _ClosureContract(
        "coexistence-refinement-retains-source-authority",
        "matcher",
        "match_step11_rc0028_experiment_surface",
        "STEP11_RC0028_RELATION_REFINEMENT_AUTHORITY_MISMATCH",
    ),
    _ClosureContract(
        "semantic-link-one-to-one-binding",
        "matcher",
        "match_step11_rc0028_experiment_surface",
        "STEP11_RC0028_SEMANTIC_LINK_BINDING_MISMATCH",
    ),
    _ClosureContract(
        "explicit-unknown-exact-owner-binding",
        "matcher",
        "match_step11_rc0028_experiment_surface",
        "STEP11_RC0028_EXPLICIT_UNKNOWN_BINDING_MISMATCH",
    ),
    _ClosureContract(
        "covered-is-not-semantic-coverage",
        "gate",
        "evaluate_step11_rc0028_experiment_candidate",
        "STEP11_RC0028_SEMANTIC_COVERAGE_SELF_CLAIM",
    ),
    _ClosureContract(
        "final-bytes-bind-parser-matcher-and-gate",
        "gate",
        "evaluate_step11_rc0028_experiment_candidate",
        "STEP11_RC0028_FINAL_BYTES_COMMITMENT_MISMATCH",
    ),
    _ClosureContract(
        "parser-is-body-only-and-forward-metadata-blind",
        "matcher",
        "parse_step11_rc0028_experiment_surface",
        "STEP11_RC0028_PARSER_FORWARD_METADATA_FORBIDDEN",
    ),
)


def _load_module(module_name: str, *, expected_code: str) -> ModuleType:
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError as error:
        if error.name != module_name:
            raise
        pytest.fail(
            "E0B_EXPERIMENT_OWNER_MISSING:"
            f"{module_name}:EXPECTED_CLOSED_FAILURE={expected_code}",
            pytrace=False,
        )


def _require_callable(
    owner: str,
    api_name: str,
    *,
    expected_code: str,
) -> Any:
    module_name = _OWNER_MODULES[owner]
    module = _load_module(module_name, expected_code=expected_code)
    value = getattr(module, api_name, None)
    assert callable(value), (
        "E0B_DOWNSTREAM_API_MISSING:"
        f"{module_name}.{api_name}:"
        f"EXPECTED_CLOSED_FAILURE={expected_code}"
    )
    return value


def _closure_id(contract: _ClosureContract) -> str:
    return (
        f"{contract.contract_id}__expects__"
        f"{contract.expected_closed_failure}"
    )


def test_rc0028_e0b_requires_exact_additive_api_surface_after_predecessor() -> None:
    expected = {
        "lexicalization": (
            "build_step11_rc0028_experiment_lexical_atom_specs",
        ),
        "surface": (
            "build_step11_rc0028_experiment_surface_candidate",
            "build_step11_rc0028_experiment_surface_candidates",
            "render_step11_rc0028_experiment_surface",
            "validate_step11_rc0028_experiment_surface_candidate",
        ),
        "matcher": (
            "parse_step11_rc0028_experiment_surface",
            "match_step11_rc0028_experiment_surface",
        ),
        "gate": (
            "evaluate_step11_rc0028_experiment_candidate",
            "select_step11_rc0028_experiment_candidates",
        ),
    }
    missing = []
    for owner, names in expected.items():
        module = _load_module(
            _OWNER_MODULES[owner],
            expected_code="STEP11_RC0028_ADDITIVE_API_REQUIRED",
        )
        for name in names:
            if not callable(getattr(module, name, None)):
                missing.append(f"{owner}:{name}")

    assert not missing, (
        "E0B_DOWNSTREAM_ADDITIVE_API_SET_MISSING:"
        "EXPECTED_CLOSED_FAILURE=STEP11_RC0028_ADDITIVE_API_REQUIRED:"
        + ",".join(sorted(missing))
    )


def test_rc0028_e0b_optional_catalog_is_proven_required_for_13_codes() -> None:
    module = _load_module(
        _EXPERIMENT_CATALOG_MODULE,
        expected_code="STEP11_RC0028_EXPERIMENT_CATALOG_REQUIRED",
    )
    catalog = getattr(module, _EXPERIMENT_CATALOG_ATTRIBUTE, None)
    assert type(catalog) is dict, (
        "E0B_EXPERIMENT_CATALOG_MISSING:"
        "EXPECTED_CLOSED_FAILURE=STEP11_RC0028_EXPERIMENT_CATALOG_REQUIRED"
    )
    construction_atoms = catalog.get("construction_atom_codes")
    assert type(construction_atoms) is dict, (
        "E0B_EXPERIMENT_CONSTRUCTION_ATOMS_MISSING:"
        "EXPECTED_CLOSED_FAILURE=STEP11_RC0028_EXPERIMENT_CATALOG_REQUIRED"
    )
    assert frozenset(construction_atoms) == _SUCCESSOR_CONSTRUCTION_CODES, (
        "E0B_EXPERIMENT_CONSTRUCTION_ATOM_SET_MISMATCH:"
        "EXPECTED_CLOSED_FAILURE=STEP11_RC0028_EXPERIMENT_CATALOG_REQUIRED"
    )
    assert all(
        type(value) is str and value
        for value in construction_atoms.values()
    ), (
        "E0B_EXPERIMENT_CONSTRUCTION_ATOM_INVALID:"
        "EXPECTED_CLOSED_FAILURE=STEP11_RC0028_CATALOG_ATOM_CODE_INVALID"
    )


def test_rc0028_e0b_catalog_breaks_known_body_only_collisions() -> None:
    module = _load_module(
        _EXPERIMENT_CATALOG_MODULE,
        expected_code="STEP11_RC0028_EXPERIMENT_CATALOG_REQUIRED",
    )
    catalog = getattr(module, _EXPERIMENT_CATALOG_ATTRIBUTE, None)
    construction_atoms = (
        catalog.get("construction_atom_codes", {})
        if type(catalog) is dict
        else {}
    )
    unresolved = tuple(
        sorted(
            tuple(sorted(pair))
            for pair in _KNOWN_BODY_ONLY_COLLISIONS
            if len({construction_atoms.get(code) for code in pair}) != 2
        )
    )
    assert unresolved == (), (
        "E0B_EXPERIMENT_CONSTRUCTION_COLLISION:"
        "EXPECTED_CLOSED_FAILURE=STEP11_RC0028_CATALOG_ATOM_COLLISION"
    )


@pytest.mark.parametrize(
    "contract",
    _CLOSURE_CONTRACTS,
    ids=_closure_id,
)
def test_rc0028_e0b_forward_inverse_closure_requires_additive_consumer(
    contract: _ClosureContract,
) -> None:
    _require_callable(
        contract.owner,
        contract.api_name,
        expected_code=contract.expected_closed_failure,
    )


def test_rc0028_e0b_contract_ledger_is_exact_and_nonempty() -> None:
    assert len(_CLOSURE_CONTRACTS) == 8
    assert len({row.contract_id for row in _CLOSURE_CONTRACTS}) == 8
    assert all(row.expected_closed_failure for row in _CLOSURE_CONTRACTS)
    assert frozenset(_OWNER_MODULES) == {
        "lexicalization",
        "surface",
        "matcher",
        "gate",
    }
