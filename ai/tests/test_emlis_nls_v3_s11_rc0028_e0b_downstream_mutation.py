# -*- coding: utf-8 -*-
from __future__ import annotations

"""D0 section 6.2 mutation ledger for rc0028 E0b.

Each parametrized node locks one attack and its required closed failure code.
Dynamic imports make the predecessor fail in the test body at the exact owner
that still lacks an additive rc0028 consumer.  No source or output body is
embedded in this shareable RED suite.
"""

from dataclasses import dataclass
import importlib

import pytest


@dataclass(frozen=True, slots=True)
class _Attack:
    attack_id: str
    module_name: str
    api_name: str
    expected_closed_failure: str


_MATCHER = "emlis_ai_step11_natural_surface_matcher_v3"
_GATE = "emlis_ai_step11_hard_gate_v3"
_CATALOG = "emlis_ai_step11_rc0028_experiment_surface_catalog_v3"
_RUNTIME = "emlis_ai_step11_rc0028_experiment_runtime_adapter_v3"

_LEXICALIZE_API = "build_step11_rc0028_experiment_lexical_atom_specs"
_SURFACE_API = "build_step11_rc0028_experiment_surface_candidates"
_PARSE_API = "parse_step11_rc0028_experiment_surface"
_MATCH_API = "match_step11_rc0028_experiment_surface"
_GATE_API = "evaluate_step11_rc0028_experiment_candidate"
_SELECT_API = "select_step11_rc0028_experiment_candidates"
_CATALOG_VALIDATE_API = "validate_step11_rc0028_experiment_surface_catalog"
_RUNTIME_API = "run_step11_rc0028_experiment"


def _attack(
    attack_id: str,
    module_name: str,
    api_name: str,
    expected_closed_failure: str,
) -> _Attack:
    return _Attack(
        attack_id,
        module_name,
        api_name,
        expected_closed_failure,
    )


_ATTACKS = (
    _attack(
        "generic-body-replacement-retaining-forward-metadata",
        _GATE,
        _GATE_API,
        "STEP11_RC0028_REQUIRED_ATOM_MISSING",
    ),
    _attack(
        "candidate-metadata-deletion",
        _MATCHER,
        _PARSE_API,
        "STEP11_RC0028_PARSER_FORWARD_METADATA_FORBIDDEN",
    ),
    _attack(
        "covered-ids-deletion",
        _MATCHER,
        _PARSE_API,
        "STEP11_RC0028_PARSER_FORWARD_METADATA_FORBIDDEN",
    ),
    _attack(
        "generator-span-map-deletion",
        _MATCHER,
        _PARSE_API,
        "STEP11_RC0028_PARSER_FORWARD_METADATA_FORBIDDEN",
    ),
    _attack(
        "relation-from-to-swap",
        _MATCHER,
        _MATCH_API,
        "STEP11_RC0028_RELATION_ENDPOINT_MISMATCH",
    ),
    _attack(
        "relation-endpoint-role-swap",
        _MATCHER,
        _MATCH_API,
        "STEP11_RC0028_RELATION_ENDPOINT_ROLE_MISMATCH",
    ),
    _attack(
        "relation-direction-reverse",
        _MATCHER,
        _MATCH_API,
        "STEP11_RC0028_RELATION_DIRECTION_MISMATCH",
    ),
    _attack(
        "source-relation-type-mutation",
        _MATCHER,
        _MATCH_API,
        "STEP11_RC0028_SOURCE_RELATION_TYPE_MISMATCH",
    ),
    _attack(
        "effective-relation-type-mutation",
        _MATCHER,
        _MATCH_API,
        "STEP11_RC0028_EFFECTIVE_RELATION_TYPE_MISMATCH",
    ),
    _attack(
        "coexistence-refinement-forged-as-base-required-relation",
        _MATCHER,
        _MATCH_API,
        "STEP11_RC0028_RELATION_REFINEMENT_AUTHORITY_MISMATCH",
    ),
    _attack(
        "inner-construction-deletion",
        _GATE,
        _GATE_API,
        "STEP11_RC0028_CONSTRUCTION_CARDINALITY_MISMATCH",
    ),
    _attack(
        "overlap-flattened-to-one-construction",
        _GATE,
        _GATE_API,
        "STEP11_RC0028_CONSTRUCTION_CARDINALITY_MISMATCH",
    ),
    _attack(
        "construction-slot-duplicate",
        _MATCHER,
        _MATCH_API,
        "STEP11_RC0028_CONSTRUCTION_SLOT_BINDING_MISMATCH",
    ),
    _attack(
        "construction-slot-orphan",
        _MATCHER,
        _MATCH_API,
        "STEP11_RC0028_CONSTRUCTION_SLOT_BINDING_MISMATCH",
    ),
    _attack(
        "participation-owner-mutation",
        _MATCHER,
        _MATCH_API,
        "STEP11_RC0028_PARTICIPATION_OWNER_MISMATCH",
    ),
    _attack(
        "participation-range-mutation",
        _MATCHER,
        _MATCH_API,
        "STEP11_RC0028_PARTICIPATION_RANGE_MISMATCH",
    ),
    _attack(
        "participation-semantic-equivalence-flag-mutation",
        _MATCHER,
        _MATCH_API,
        "STEP11_RC0028_PARTICIPATION_EQUIVALENCE_MISMATCH",
    ),
    _attack(
        "semantic-link-endpoint-mutation",
        _MATCHER,
        _MATCH_API,
        "STEP11_RC0028_SEMANTIC_LINK_ENDPOINT_MISMATCH",
    ),
    _attack(
        "semantic-link-type-mutation",
        _MATCHER,
        _MATCH_API,
        "STEP11_RC0028_SEMANTIC_LINK_TYPE_MISMATCH",
    ),
    _attack(
        "semantic-link-direction-mutation",
        _MATCHER,
        _MATCH_API,
        "STEP11_RC0028_SEMANTIC_LINK_DIRECTION_MISMATCH",
    ),
    _attack(
        "explicit-unknown-drop",
        _MATCHER,
        _MATCH_API,
        "STEP11_RC0028_EXPLICIT_UNKNOWN_MISSING",
    ),
    _attack(
        "explicit-unknown-duplicate",
        _MATCHER,
        _MATCH_API,
        "STEP11_RC0028_EXPLICIT_UNKNOWN_DUPLICATE",
    ),
    _attack(
        "explicit-unknown-valid-other-dimension",
        _MATCHER,
        _MATCH_API,
        "STEP11_RC0028_EXPLICIT_UNKNOWN_DIMENSION_MISMATCH",
    ),
    _attack(
        "explicit-unknown-affected-owner-order-mutation",
        _MATCHER,
        _MATCH_API,
        "STEP11_RC0028_EXPLICIT_UNKNOWN_OWNER_MISMATCH",
    ),
    _attack(
        "semantic-coverage-authorized-bool-true",
        _GATE,
        _GATE_API,
        "STEP11_RC0028_SEMANTIC_COVERAGE_SELF_CLAIM",
    ),
    _attack(
        "semantic-coverage-authorized-int-one",
        _GATE,
        _GATE_API,
        "STEP11_RC0028_SEMANTIC_COVERAGE_SELF_CLAIM",
    ),
    _attack(
        "semantic-coverage-authorized-string-false",
        _GATE,
        _GATE_API,
        "STEP11_RC0028_SEMANTIC_COVERAGE_SELF_CLAIM",
    ),
    _attack(
        "unknown-field-injection",
        _GATE,
        _GATE_API,
        "STEP11_RC0028_UNKNOWN_FIELD_FORBIDDEN",
    ),
    _attack(
        "stale-artifact-hash",
        _GATE,
        _GATE_API,
        "STEP11_RC0028_ARTIFACT_COMMITMENT_MISMATCH",
    ),
    _attack(
        "valid-other-input-source-owner-swap",
        _MATCHER,
        _MATCH_API,
        "STEP11_RC0028_SOURCE_COMMITMENT_MISMATCH",
    ),
    _attack(
        "evidence-alias-cross-input-swap",
        _MATCHER,
        _MATCH_API,
        "STEP11_RC0028_SOURCE_COMMITMENT_MISMATCH",
    ),
    _attack(
        "catalog-token-mutation",
        _CATALOG,
        _CATALOG_VALIDATE_API,
        "STEP11_RC0028_CATALOG_TOKEN_MISMATCH",
    ),
    _attack(
        "catalog-atom-code-mutation",
        _CATALOG,
        _CATALOG_VALIDATE_API,
        "STEP11_RC0028_CATALOG_ATOM_CODE_MISMATCH",
    ),
    _attack(
        "forward-helper-imported-by-parser",
        _MATCHER,
        _PARSE_API,
        "STEP11_RC0028_FORWARD_INVERSE_IMPORT_FORBIDDEN",
    ),
    _attack(
        "forward-helper-imported-by-matcher",
        _MATCHER,
        _MATCH_API,
        "STEP11_RC0028_FORWARD_INVERSE_IMPORT_FORBIDDEN",
    ),
    _attack(
        "resource-bound-plus-one",
        _GATE,
        _GATE_API,
        "STEP11_RC0028_RESOURCE_BOUND_EXCEEDED",
    ),
    _attack(
        "candidate-count-thirteen",
        _GATE,
        _SELECT_API,
        "STEP11_RC0028_CANDIDATE_BOUND_EXCEEDED",
    ),
    _attack(
        "replan-count-two",
        _GATE,
        _SELECT_API,
        "STEP11_RC0028_REPLAN_BOUND_EXCEEDED",
    ),
    _attack(
        "raw-body-in-shareable-material",
        _RUNTIME,
        _RUNTIME_API,
        "STEP11_RC0028_SHAREABLE_RAW_BODY_FORBIDDEN",
    ),
    _attack(
        "output-body-in-shareable-material",
        _RUNTIME,
        _RUNTIME_API,
        "STEP11_RC0028_SHAREABLE_OUTPUT_BODY_FORBIDDEN",
    ),
    _attack(
        "source-fragment-in-shareable-material",
        _RUNTIME,
        _RUNTIME_API,
        "STEP11_RC0028_SHAREABLE_SOURCE_FRAGMENT_FORBIDDEN",
    ),
    _attack(
        "unsalted-body-digest-in-shareable-material",
        _RUNTIME,
        _RUNTIME_API,
        "STEP11_RC0028_SHAREABLE_UNSALTED_DIGEST_FORBIDDEN",
    ),
)


def _node_id(attack: _Attack) -> str:
    return (
        f"{attack.attack_id}__expects__"
        f"{attack.expected_closed_failure}"
    )


@pytest.mark.parametrize("attack", _ATTACKS, ids=_node_id)
def test_rc0028_e0b_mandatory_attack_has_closed_consumer(
    attack: _Attack,
) -> None:
    try:
        module = importlib.import_module(attack.module_name)
    except ModuleNotFoundError as error:
        if error.name != attack.module_name:
            raise
        pytest.fail(
            "E0B_ATTACK_OWNER_MISSING:"
            f"{attack.attack_id}:{attack.module_name}:"
            f"EXPECTED_CLOSED_FAILURE={attack.expected_closed_failure}",
            pytrace=False,
        )
    api = getattr(module, attack.api_name, None)
    assert callable(api), (
        "E0B_ATTACK_CONSUMER_MISSING:"
        f"{attack.attack_id}:{attack.module_name}.{attack.api_name}:"
        f"EXPECTED_CLOSED_FAILURE={attack.expected_closed_failure}"
    )


def test_rc0028_e0b_attack_ledger_is_exact_nonempty_and_unique() -> None:
    assert len(_ATTACKS) == 42
    assert len({row.attack_id for row in _ATTACKS}) == 42
    assert all(row.expected_closed_failure for row in _ATTACKS)
    assert all(
        row.expected_closed_failure.startswith("STEP11_RC0028_")
        for row in _ATTACKS
    )
    assert {
        "generic-body-replacement-retaining-forward-metadata",
        "candidate-metadata-deletion",
        "covered-ids-deletion",
        "generator-span-map-deletion",
        "relation-from-to-swap",
        "relation-endpoint-role-swap",
        "relation-direction-reverse",
        "source-relation-type-mutation",
        "effective-relation-type-mutation",
        "coexistence-refinement-forged-as-base-required-relation",
        "inner-construction-deletion",
        "overlap-flattened-to-one-construction",
        "construction-slot-duplicate",
        "construction-slot-orphan",
        "participation-owner-mutation",
        "participation-range-mutation",
        "participation-semantic-equivalence-flag-mutation",
        "semantic-link-endpoint-mutation",
        "semantic-link-type-mutation",
        "semantic-link-direction-mutation",
        "explicit-unknown-drop",
        "explicit-unknown-duplicate",
        "explicit-unknown-valid-other-dimension",
        "explicit-unknown-affected-owner-order-mutation",
        "semantic-coverage-authorized-bool-true",
        "semantic-coverage-authorized-int-one",
        "semantic-coverage-authorized-string-false",
        "unknown-field-injection",
        "stale-artifact-hash",
        "valid-other-input-source-owner-swap",
        "evidence-alias-cross-input-swap",
        "catalog-token-mutation",
        "catalog-atom-code-mutation",
        "forward-helper-imported-by-parser",
        "forward-helper-imported-by-matcher",
        "resource-bound-plus-one",
        "candidate-count-thirteen",
        "replan-count-two",
        "raw-body-in-shareable-material",
        "output-body-in-shareable-material",
        "source-fragment-in-shareable-material",
        "unsalted-body-digest-in-shareable-material",
    } == {row.attack_id for row in _ATTACKS}


def test_rc0028_e0b_no_assertion_weakening_empty_expectation_or_gate_downgrade(
) -> None:
    expected = tuple(row.expected_closed_failure for row in _ATTACKS)
    assert expected
    assert all(expected)
    assert len(expected) == len(_ATTACKS)
    assert "STEP11_RC0028_REQUIRED_ATOM_MISSING" in expected
    assert "STEP11_RC0028_RESOURCE_BOUND_EXCEEDED" in expected
    assert "STEP11_RC0028_SHAREABLE_RAW_BODY_FORBIDDEN" in expected


def test_rc0028_e0b_forward_owner_api_names_are_not_inverse_import_hooks() -> None:
    inverse_attacks = tuple(
        row
        for row in _ATTACKS
        if row.expected_closed_failure
        == "STEP11_RC0028_FORWARD_INVERSE_IMPORT_FORBIDDEN"
    )
    assert {row.api_name for row in inverse_attacks} == {
        _PARSE_API,
        _MATCH_API,
    }
    assert all(row.module_name == _MATCHER for row in inverse_attacks)
    assert _LEXICALIZE_API not in {row.api_name for row in inverse_attacks}
    assert _SURFACE_API not in {row.api_name for row in inverse_attacks}
