# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step 8 inverse-grammar authority layered beside the frozen Step 7 v1.

The Step 7 catalog and renderer are already frozen release inputs.  Step 8
therefore derives an independent v2 catalog without mutating either v1 byte.
The extension only names morphology and inverse classifications that the
existing controlled surface already emits; it contains no fixture cue, case
identifier, expected sentence, traversal code, or source identifier.
"""

from copy import deepcopy
import unicodedata
from typing import Any

from emlis_ai_nls_v3_artifact_contract import artifact_sha256
from emlis_ai_surface_grammar_catalog_v3 import (
    FROZEN_SURFACE_GRAMMAR_CATALOG_SHA256 as FROZEN_STEP7_CATALOG_SHA256,
    SURFACE_GRAMMAR_CATALOG as STEP7_SURFACE_GRAMMAR_CATALOG,
    SURFACE_GRAMMAR_CATALOG_VERSION as STEP7_CATALOG_VERSION,
    validate_surface_grammar_catalog as validate_step7_catalog,
)


STEP8_SURFACE_GRAMMAR_CATALOG_VERSION = (
    "cocolon.emlis.nls_v3.surface_grammar_catalog.20260715.v2"
)
_EXPECTED_STEP7_CATALOG_VERSION = (
    "cocolon.emlis.nls_v3.surface_grammar_catalog.20260715.v1"
)
_EXPECTED_STEP7_CATALOG_SHA256 = (
    "af4a49bc08437cbd6ab968d52acf45971eb8a51f1468c87328717398e7f067e4"
)

_STEP8_EXTENSION: dict[str, Any] = {
    "document": {"label_body_separator": "\n"},
    "source_role": {
        "original_input": "",
        "question_need_decision": "問いの必要性判断にある",
        "supplemental_answer": "補足回答にある",
    },
    "unknown_dimension_classification": [
        {"code": "cause", "contains": ["cause", "reason"]},
        {
            "code": "choice",
            "contains": ["choice", "decision", "alternative"],
        },
        {"code": "referent", "contains": ["referent", "target"]},
        {"code": "relation", "contains": ["relation", "connection"]},
        {"code": "outcome", "contains": ["outcome", "future"]},
        {"code": "other", "contains": []},
    ],
    "graph_role": {
        "none": "",
        "precedes_source": "順序の前側にある",
        "precedes_target": "順序の後側にある",
        "relation_source": "関係の一方にある",
        "relation_target": "関係のもう一方にある",
        "unknown_related": "分からなさが関わる",
    },
    "morphology": {
        "referent_joiner": "と",
        "unknown_binding": "に関わる",
        "bidirectional_binding": "には",
        "reception_object_particle": "を",
    },
    "inverse_kind_rule": {
        "accepted_predicate_forms": [
            "action_intended",
            "bounded_counterposition_observed",
            "nucleus_observed",
            "shift_observed",
        ],
        "accepted_unknown_dimension_codes": [
            "cause",
            "choice",
            "other",
            "outcome",
            "referent",
            "relation",
        ],
        "shared_seen_predicate_special_nucleus_kinds": ["change", "value"],
    },
    "parser_compatibility": {
        "observation_stages": ["normal_observation"],
        "source_roles": ["original_input"],
    },
}


def _build_catalog() -> dict[str, Any]:
    catalog = deepcopy(STEP7_SURFACE_GRAMMAR_CATALOG)
    catalog["catalog_version"] = STEP8_SURFACE_GRAMMAR_CATALOG_VERSION
    catalog["document"].update(deepcopy(_STEP8_EXTENSION["document"]))
    for key, value in _STEP8_EXTENSION.items():
        if key != "document":
            catalog[key] = deepcopy(value)
    return catalog


STEP8_SURFACE_GRAMMAR_CATALOG = _build_catalog()
STEP8_SURFACE_GRAMMAR_CATALOG_SHA256 = artifact_sha256(
    STEP8_SURFACE_GRAMMAR_CATALOG
)
FROZEN_STEP8_SURFACE_GRAMMAR_CATALOG_SHA256 = (
    "482a45a3f4962af996aed70dc407cab05e03013a4612e1f13c853151f8d68148"
)

_CATALOG_UNSET = object()


def validate_step8_surface_grammar_catalog(
    value: Any = _CATALOG_UNSET,
) -> tuple[str, ...]:
    """Validate both the frozen v1 parent and the side-by-side v2 overlay."""

    if value is _CATALOG_UNSET:
        value = STEP8_SURFACE_GRAMMAR_CATALOG
    issues: list[str] = []
    if (
        STEP7_CATALOG_VERSION != _EXPECTED_STEP7_CATALOG_VERSION
        or FROZEN_STEP7_CATALOG_SHA256 != _EXPECTED_STEP7_CATALOG_SHA256
        or validate_step7_catalog()
        or validate_step7_catalog(STEP7_SURFACE_GRAMMAR_CATALOG)
    ):
        issues.append("STEP7_GRAMMAR_PARENT_DRIFT")
    if type(value) is not dict or value.get("body_free") is not True:
        return tuple(sorted(set(issues + ["GRAMMAR_CATALOG_SHAPE_INVALID"])))
    if value.get("catalog_version") != STEP8_SURFACE_GRAMMAR_CATALOG_VERSION:
        issues.append("GRAMMAR_CATALOG_VERSION_MISMATCH")

    def walk(item: Any) -> None:
        if type(item) is str:
            if unicodedata.normalize("NFC", item) != item or "\r" in item:
                issues.append("GRAMMAR_CATALOG_NON_CANONICAL_TOKEN")
        elif type(item) is list:
            for child in item:
                walk(child)
        elif type(item) is dict:
            for key, child in item.items():
                walk(str(key))
                walk(child)
        elif item is not True:
            issues.append("GRAMMAR_CATALOG_NON_DECLARATIVE_VALUE")

    walk(value)
    if artifact_sha256(value) != FROZEN_STEP8_SURFACE_GRAMMAR_CATALOG_SHA256:
        issues.append("GRAMMAR_CATALOG_FROZEN_HASH_MISMATCH")
    return tuple(sorted(set(issues)))


__all__ = [
    "FROZEN_STEP7_CATALOG_SHA256",
    "FROZEN_STEP8_SURFACE_GRAMMAR_CATALOG_SHA256",
    "STEP8_SURFACE_GRAMMAR_CATALOG",
    "STEP8_SURFACE_GRAMMAR_CATALOG_SHA256",
    "STEP8_SURFACE_GRAMMAR_CATALOG_VERSION",
    "validate_step8_surface_grammar_catalog",
]
