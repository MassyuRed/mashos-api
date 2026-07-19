# -*- coding: utf-8 -*-
from __future__ import annotations

"""Declarative surface atoms for the runtime-disconnected rc0028 experiment.

The catalog contains only closed machine codes and short Japanese morphology
fragments.  It deliberately owns no case, family, topic, expected output, or
completed response.  Forward realization and the independent body-only parser
may read the same immutable values, but neither imports the other's helpers.
"""

import re
import unicodedata
from typing import Any, Final

from emlis_ai_nls_v3_artifact_contract import artifact_sha256


STEP11_RC0028_EXPERIMENT_SURFACE_CATALOG_SCHEMA: Final = (
    "cocolon.emlis.nls_v3.step11.rc0028_experiment_surface_catalog.v1"
)
STEP11_RC0028_EXPERIMENT_SURFACE_CATALOG_VERSION: Final = (
    "cocolon.emlis.nls_v3.step11.rc0028_experiment_surface_catalog."
    "20260719.v1"
)

# This is a parser resource bound, not a claim that every ordinal is visible.
# Values beyond it fail closed instead of extending the grammar at runtime.
STEP11_RC0028_OWNER_ORDINAL_MAX: Final = 24

_MACHINE_CODE_RE: Final = re.compile(r"^[a-z][a-z0-9_]{2,95}$")
_FORBIDDEN_VISIBLE_TOKEN_RE: Final = re.compile(
    r"[\r\n\x00-\x1f\x7f、，,。．.!！?？:：;；{}]"
)

_CONSTRUCTION_CODES: Final = (
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
)
_ROLE_POSITION_KEYS: Final = (
    "action_lifecycle:lifecycle",
    "antecedent_predication:antecedent",
    "consequent_predication:consequent",
    "predicate_or_event:predicate",
    "referent_primary:primary",
    "referent_secondary:secondary",
    "state_or_quality:quality",
    "transition_or_relation:connector",
    "unknown_or_limit:limit",
)
_RELATION_TYPES: Final = (
    "action_supports_change",
    "attempt_and_block",
    "coexistence",
    "continuation_or_refusal",
    "contrast",
    "evaluation_about_event",
    "preserves_despite",
    "self_evaluation_about_state",
    "shift_from_to",
    "temporal_before_after",
    "uncertain_connection",
    "user_stated_cause",
    "user_stated_result",
    "wish_and_constraint",
)
_DIRECTIONS: Final = ("bidirectional", "source_to_target")
_UNKNOWN_DIMENSIONS: Final = (
    "explicit_cause_unknown",
    "explicit_choice_decision_unknown",
    "explicit_temporal_referent_unknown",
    "explicit_unverbalized_unknown",
)
_SEMANTIC_LINK_TYPES: Final = (
    "coexists_with",
    "contrasts_with",
    "precedes",
    "qualifies",
    "supports_without_guarantee",
)

_CONSTRUCTION_ATOM_CODES: Final = {
    code: "construction_" + code for code in _CONSTRUCTION_CODES
}
_CONSTRUCTION_SURFACE_TOKENS: Final = {
    "balanced_consideration": "片方だけに寄せない捉え方",
    "choice_uncertainty": "選び切れない迷い",
    "comparative_assessment": "比べながら感じていること",
    "decision_timing": "決める時期を残していること",
    "explicit_coexistence": "二つの向きが同時にあること",
    "explicit_contrast": "違う向きが並んでいること",
    "nonreduction_boundary": "一つに決め切らないこと",
    "ordered_sequence": "前後を保った流れ",
    "parallel_addition": "二つの内容が並んでいること",
    "particle_object": "対象に向けた動き",
    "purpose_action": "目的に向けて動いたこと",
    "reported_self_assessment": "自分自身への見立て",
    "withheld_action": "すぐには動かない選択",
}
_ROLE_POSITION_ATOM_CODES: Final = {
    key: "role_" + key.replace(":", "_") for key in _ROLE_POSITION_KEYS
}
_ROLE_POSITION_SURFACE_TOKENS: Final = {
    "action_lifecycle:lifecycle": "行動の進み具合",
    "antecedent_predication:antecedent": "先にあること",
    "consequent_predication:consequent": "後に続くこと",
    "predicate_or_event:predicate": "起きたことや動き",
    "referent_primary:primary": "中心にあること",
    "referent_secondary:secondary": "もう一方のこと",
    "state_or_quality:quality": "状態や感じ方",
    "transition_or_relation:connector": "二つを結ぶ向き",
    "unknown_or_limit:limit": "まだ決まっていない部分",
}

_RELATION_BASE_TOKENS: Final = {
    "action_supports_change": "行動が変化を支えているつながり",
    "attempt_and_block": "試みと妨げが並ぶつながり",
    "coexistence": "二つの向きが同時にあるつながり",
    "continuation_or_refusal": "続けることと拒むことの分かれ目",
    "contrast": "違う向きが並ぶつながり",
    "evaluation_about_event": "出来事に向けた見立て",
    "preserves_despite": "それでも残っているつながり",
    "self_evaluation_about_state": "状態についての自分への見立て",
    "shift_from_to": "捉え方や動きが移っていくつながり",
    "temporal_before_after": "時間の前後を保つつながり",
    "uncertain_connection": "まだ決め切らないつながり",
    "user_stated_cause": "語られた理由から続くつながり",
    "user_stated_result": "語られた結果へ続くつながり",
    "wish_and_constraint": "願いと制約が並ぶつながり",
}
_RELATION_SURFACE_TOKENS: Final = {
    f"{relation_type}:{direction}": (
        ("互いに結び合う" if direction == "bidirectional" else "一方向に続く")
        + token
    )
    for relation_type, token in _RELATION_BASE_TOKENS.items()
    for direction in _DIRECTIONS
}
_UNKNOWN_SURFACE_TOKENS: Final = {
    "explicit_cause_unknown": "理由がまだ分からないところ",
    "explicit_choice_decision_unknown": "選択がまだ決まっていないところ",
    "explicit_temporal_referent_unknown": "時点がまだはっきりしないところ",
    "explicit_unverbalized_unknown": "まだ言葉になっていないところ",
}
_SEMANTIC_LINK_BASE_TOKENS: Final = {
    "coexists_with": "意味の併存",
    "contrasts_with": "意味の対照",
    "precedes": "意味の前後",
    "qualifies": "意味を限定する関係",
    "supports_without_guarantee": "保証せず支える意味関係",
}
_SEMANTIC_LINK_SURFACE_TOKENS: Final = {
    f"{relation_type}:{direction}": (
        ("互いに結び合う" if direction == "bidirectional" else "一方向に続く")
        + token
    )
    for relation_type, token in _SEMANTIC_LINK_BASE_TOKENS.items()
    for direction in _DIRECTIONS
}
_OWNER_ORDINAL_TOKENS: Final = {
    "1": "その",
    "2": "もう一方の",
    "3": "さらに別の",
    **{
        str(ordinal): f"{ordinal}つ目の"
        for ordinal in range(4, STEP11_RC0028_OWNER_ORDINAL_MAX + 1)
    },
}
_LINE_MORPHOLOGY: Final = {
    "atom_separator": "とともに",
    "clause_separator": "、",
    "construction_open": "には",
    "construction_prefix": "構造を見ると",
    "construction_suffix": "が含まれています。",
    "owner_noun": "内容",
    "owner_possessive": "の",
    "owner_separator": "と",
    "relation_from_to_separator": "から",
    "relation_suffix": "が見えます。",
    "relation_to_suffix": "へ",
    "semantic_link_between": "の間には",
    "semantic_link_join": "と",
    "semantic_link_suffix": "が見えます。",
    "unknown_owner_suffix": "については",
    "unknown_prefix": "まだ定まらない点として",
    "unknown_suffix": "が残っています。",
}

_EXPECTED_CATALOG: Final = {
    "schema_version": STEP11_RC0028_EXPERIMENT_SURFACE_CATALOG_SCHEMA,
    "catalog_version": STEP11_RC0028_EXPERIMENT_SURFACE_CATALOG_VERSION,
    "max_owner_ordinal": STEP11_RC0028_OWNER_ORDINAL_MAX,
    "construction_atom_codes": dict(_CONSTRUCTION_ATOM_CODES),
    "construction_surface_tokens": dict(_CONSTRUCTION_SURFACE_TOKENS),
    "role_position_atom_codes": dict(_ROLE_POSITION_ATOM_CODES),
    "role_position_surface_tokens": dict(_ROLE_POSITION_SURFACE_TOKENS),
    "relation_surface_tokens": dict(_RELATION_SURFACE_TOKENS),
    "unknown_surface_tokens": dict(_UNKNOWN_SURFACE_TOKENS),
    "semantic_link_surface_tokens": dict(_SEMANTIC_LINK_SURFACE_TOKENS),
    "owner_ordinal_tokens": dict(_OWNER_ORDINAL_TOKENS),
    "line_morphology": dict(_LINE_MORPHOLOGY),
    "experimental_only": True,
    "runtime_connected": False,
    "body_free": True,
}

# Public dictionaries are distinct from the validator's frozen comparison
# dictionaries so in-process mutation cannot rewrite the expected authority.
STEP11_RC0028_EXPERIMENT_SURFACE_CATALOG: dict[str, Any] = {
    key: dict(value) if type(value) is dict else value
    for key, value in _EXPECTED_CATALOG.items()
}
STEP11_RC0028_EXPERIMENT_SURFACE_CATALOG_SHA256: Final = artifact_sha256(
    _EXPECTED_CATALOG
)


def _visible_token_valid(value: Any) -> bool:
    return (
        type(value) is str
        and value == value.strip()
        and 1 <= len(value) <= 64
        and unicodedata.normalize("NFC", value) == value
        and _FORBIDDEN_VISIBLE_TOKEN_RE.search(value) is None
        and not any(unicodedata.category(char).startswith("C") for char in value)
    )


def _morphology_token_valid(value: Any) -> bool:
    return (
        type(value) is str
        and value == value.strip()
        and 1 <= len(value) <= 64
        and unicodedata.normalize("NFC", value) == value
        and "\r" not in value
        and "\n" not in value
        and not any(unicodedata.category(char).startswith("C") for char in value)
    )


def _mapping_has_exact_strings(
    value: Any,
    expected: dict[str, str],
    *,
    machine_codes: bool,
) -> bool:
    if type(value) is not dict or set(value) != set(expected):
        return False
    if any(type(key) is not str or type(item) is not str for key, item in value.items()):
        return False
    if machine_codes:
        return all(_MACHINE_CODE_RE.fullmatch(item) is not None for item in value.values())
    return all(_visible_token_valid(item) for item in value.values())


def validate_step11_rc0028_experiment_surface_catalog(
    value: Any,
) -> tuple[str, ...]:
    """Validate exact catalog closure without interpreting visible bodies."""

    if type(value) is not dict:
        return ("STEP11_RC0028_CATALOG_SHAPE_INVALID",)
    issues: set[str] = set()
    if set(value) != set(_EXPECTED_CATALOG):
        issues.add("STEP11_RC0028_CATALOG_SHAPE_INVALID")
        return tuple(sorted(issues))
    if (
        value.get("schema_version")
        != STEP11_RC0028_EXPERIMENT_SURFACE_CATALOG_SCHEMA
        or value.get("catalog_version")
        != STEP11_RC0028_EXPERIMENT_SURFACE_CATALOG_VERSION
        or value.get("max_owner_ordinal")
        != STEP11_RC0028_OWNER_ORDINAL_MAX
        or value.get("experimental_only") is not True
        or value.get("runtime_connected") is not False
        or value.get("body_free") is not True
    ):
        issues.add("STEP11_RC0028_CATALOG_CONTRACT_MISMATCH")

    machine_mappings = (
        ("construction_atom_codes", _CONSTRUCTION_ATOM_CODES),
        ("role_position_atom_codes", _ROLE_POSITION_ATOM_CODES),
    )
    for key, expected in machine_mappings:
        current = value.get(key)
        if not _mapping_has_exact_strings(current, expected, machine_codes=True):
            issues.add("STEP11_RC0028_CATALOG_ATOM_CODE_MISMATCH")
        elif current != expected or len(set(current.values())) != len(current):
            issues.add("STEP11_RC0028_CATALOG_ATOM_CODE_MISMATCH")

    visible_mappings = (
        ("construction_surface_tokens", _CONSTRUCTION_SURFACE_TOKENS),
        ("role_position_surface_tokens", _ROLE_POSITION_SURFACE_TOKENS),
        ("relation_surface_tokens", _RELATION_SURFACE_TOKENS),
        ("unknown_surface_tokens", _UNKNOWN_SURFACE_TOKENS),
        ("semantic_link_surface_tokens", _SEMANTIC_LINK_SURFACE_TOKENS),
        ("owner_ordinal_tokens", _OWNER_ORDINAL_TOKENS),
    )
    for key, expected in visible_mappings:
        current = value.get(key)
        if not _mapping_has_exact_strings(current, expected, machine_codes=False):
            issues.add("STEP11_RC0028_CATALOG_TOKEN_MISMATCH")
        elif current != expected:
            issues.add("STEP11_RC0028_CATALOG_TOKEN_MISMATCH")

    morphology = value.get("line_morphology")
    if (
        type(morphology) is not dict
        or set(morphology) != set(_LINE_MORPHOLOGY)
        or any(
            type(key) is not str or not _morphology_token_valid(token)
            for key, token in morphology.items()
        )
        or morphology != _LINE_MORPHOLOGY
    ):
        issues.add("STEP11_RC0028_CATALOG_TOKEN_MISMATCH")

    for key in (
        "construction_surface_tokens",
        "role_position_surface_tokens",
        "relation_surface_tokens",
        "unknown_surface_tokens",
        "semantic_link_surface_tokens",
        "owner_ordinal_tokens",
    ):
        current = value.get(key)
        if type(current) is dict and len(set(current.values())) != len(current):
            issues.add("STEP11_RC0028_CATALOG_TOKEN_COLLISION")

    separator = (
        morphology.get("atom_separator")
        if type(morphology) is dict
        else None
    )
    visible_values = tuple(
        token
        for key in (
            "construction_surface_tokens",
            "role_position_surface_tokens",
            "relation_surface_tokens",
            "unknown_surface_tokens",
            "semantic_link_surface_tokens",
            "owner_ordinal_tokens",
        )
        for token in (
            value.get(key, {}).values()
            if type(value.get(key)) is dict
            else ()
        )
    )
    if (
        type(separator) is not str
        or not separator
        or any(separator in token for token in visible_values)
    ):
        issues.add("STEP11_RC0028_CATALOG_TOKEN_COLLISION")

    try:
        current_sha256 = artifact_sha256(value)
    except (TypeError, ValueError):
        current_sha256 = ""
    if current_sha256 != STEP11_RC0028_EXPERIMENT_SURFACE_CATALOG_SHA256:
        issues.add("STEP11_RC0028_CATALOG_HASH_MISMATCH")
    return tuple(sorted(issues))


__all__ = [
    "STEP11_RC0028_EXPERIMENT_SURFACE_CATALOG",
    "STEP11_RC0028_EXPERIMENT_SURFACE_CATALOG_SCHEMA",
    "STEP11_RC0028_EXPERIMENT_SURFACE_CATALOG_SHA256",
    "STEP11_RC0028_EXPERIMENT_SURFACE_CATALOG_VERSION",
    "STEP11_RC0028_OWNER_ORDINAL_MAX",
    "validate_step11_rc0028_experiment_surface_catalog",
]
