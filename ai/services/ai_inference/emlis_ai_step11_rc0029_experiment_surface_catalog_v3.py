# -*- coding: utf-8 -*-
from __future__ import annotations

"""Closed morphology for the disconnected rc0029 Surface repair.

The predecessor's semantic token vocabulary is reused by value, while this
owner replaces ordinal/schema exposition with grounded natural handles and a
single compact clause.  It owns no case, family, corpus, or completed body.
"""

import re
import unicodedata
from typing import Any, Final

from emlis_ai_nls_v3_artifact_contract import artifact_sha256
from emlis_ai_step11_rc0028_experiment_surface_catalog_v3 import (
    STEP11_RC0028_EXPERIMENT_SURFACE_CATALOG,
)


STEP11_RC0029_EXPERIMENT_SURFACE_CATALOG_SCHEMA: Final = (
    "cocolon.emlis.nls_v3.step11.rc0029_experiment_surface_catalog.v1"
)
STEP11_RC0029_EXPERIMENT_SURFACE_CATALOG_VERSION: Final = (
    "cocolon.emlis.nls_v3.step11.rc0029_experiment_surface_catalog."
    "20260719.v1"
)

_MORPHOLOGY: Final = {
    "handle_open": "「",
    "handle_close": "」",
    "structural_prefix": "そこには、",
    "family_join": "、さらに、",
    "construction_handle_link": "にある",
    "construction_token_join": "と",
    "construction_owner_group_join": "、あわせて、",
    "construction_suffix": "が重なっています",
    "relation_from": "から",
    "relation_to": "へ",
    "relation_chain_step": "、そこから",
    "relation_chain_join": "、別のつながりでは、",
    "relation_suffix": "があります",
    "link_handle_join": "と",
    "link_between": "の間に",
    "link_item_join": "、別の組では、",
    "link_suffix": "があります",
    "unknown_owner_join": "と",
    "unknown_between": "について、",
    "unknown_item_join": "、別の点では、",
    "unknown_suffix": "が残っています",
    "observation_insert": "。",
    "reception_target_join": "と",
    "reception_target_suffix": "について、",
    "reception_support_join": "と",
    "reception_support_suffix": "を支えに、",
    "reception_additional_join": "、また、",
}

_OWNER_ROLE_SURFACE_TOKENS: Final = {
    "relation_from": "起点となる",
    "relation_to": "受け手となる",
    "semantic_link_from": "結びつきを支える",
    "semantic_link_to": "結ばれる",
    "explicit_unknown": "まだ定まらない",
    "reception_antecedent": "受け止めたい",
    "reception_target": "応答を向ける",
    "reception_support": "応答の支えとなる",
}

_ROLE_POSITION_SURFACE_TOKENS: Final = {
    "action_lifecycle:lifecycle": "進み具合をもつ",
    "antecedent_predication:antecedent": "先にある",
    "consequent_predication:consequent": "後に続く",
    "predicate_or_event:predicate": "動きとしての",
    "referent_primary:primary": "中心にある",
    "referent_secondary:secondary": "もう一方の",
    "state_or_quality:quality": "感じ方としての",
    "transition_or_relation:connector": "結び目となる",
    "unknown_or_limit:limit": "未確定な",
}

# The public body names only the natural construction.  The inverse parser
# recovers the exact slot/participation layout from this versioned,
# declarative value instead of exposing role records in the prose or reading
# the forward AST.  These layouts are the closed `_Pattern.groups` projection
# of the immutable E1b successor authority.
_CONSTRUCTION_ROLE_LAYOUTS: Final = {
    "balanced_consideration": (
        "referent_primary:primary",
        "referent_secondary:secondary",
        "transition_or_relation:connector",
    ),
    "choice_uncertainty": (
        "referent_primary:primary",
        "unknown_or_limit:limit",
    ),
    "comparative_assessment": (
        "referent_primary:primary",
        "state_or_quality:quality",
    ),
    "decision_timing": (
        "referent_primary:primary",
        "unknown_or_limit:limit",
    ),
    "explicit_coexistence": (
        "referent_primary:primary",
        "referent_secondary:secondary",
        "transition_or_relation:connector",
    ),
    "explicit_contrast": (
        "antecedent_predication:antecedent",
        "transition_or_relation:connector",
        "consequent_predication:consequent",
    ),
    "nonreduction_boundary": (
        "referent_primary:primary",
        "transition_or_relation:connector",
        "unknown_or_limit:limit",
    ),
    "ordered_sequence": (
        "antecedent_predication:antecedent",
        "transition_or_relation:connector",
        "consequent_predication:consequent",
    ),
    "parallel_addition": (
        "antecedent_predication:antecedent",
        "transition_or_relation:connector",
        "consequent_predication:consequent",
    ),
    "particle_object": (
        "referent_primary:primary",
        "predicate_or_event:predicate",
    ),
    "purpose_action": (
        "transition_or_relation:connector",
        "predicate_or_event:predicate",
    ),
    "reported_self_assessment": (
        "referent_primary:primary",
        "state_or_quality:quality",
    ),
    "withheld_action": ("action_lifecycle:lifecycle",),
}

_OWNER_KIND_SURFACE_TOKENS: Final = {
    "event": "出来事",
    "state": "状態",
    "reaction": "気持ちの動き",
    "wish": "願い",
    "constraint": "制約",
    "action": "行動",
    "change": "変化",
    "self_evaluation": "自己評価",
    "value": "大切さ",
    "uncertainty": "迷い",
    "conclusion": "結論",
    "other_explicit": "明示された内容",
}

_RECEPTION_ACT_SURFACE_TOKENS: Final = {
    "hold_in_attention": "気に留めます",
    "do_not_dismiss": "軽く扱いません",
    "honor_concrete_action": "具体的な行動として大切に受け取ります",
}

_PARENT = STEP11_RC0028_EXPERIMENT_SURFACE_CATALOG
_RELATION_BASE_TOKENS: Final = {
    "action_supports_change": "行動が変化を支えるつながり",
    "attempt_and_block": "試みと妨げが並ぶつながり",
    "coexistence": "二つの向きが共にあるつながり",
    "continuation_or_refusal": "続けることと拒むことの分かれ目",
    "contrast": "違う向きが並ぶつながり",
    "evaluation_about_event": "出来事への見立てのつながり",
    "preserves_despite": "それでも残るつながり",
    "self_evaluation_about_state": "状態への自分の見立てのつながり",
    "shift_from_to": "捉え方や動きが移るつながり",
    "temporal_before_after": "時間の前後を保つつながり",
    "uncertain_connection": "まだ決め切らないつながり",
    "user_stated_cause": "語られた理由から続くつながり",
    "user_stated_result": "語られた結果へ続くつながり",
    "wish_and_constraint": "願いと制約が並ぶつながり",
}
_RELATION_SURFACE_TOKENS: Final = {
    relation_type + ":" + direction: (
        ("互いに" if direction == "bidirectional" else "") + token
    )
    for relation_type, token in _RELATION_BASE_TOKENS.items()
    for direction in ("bidirectional", "source_to_target")
}
_LINK_BASE_TOKENS: Final = {
    "coexists_with": "共にある関係",
    "contrasts_with": "対照になる関係",
    "precedes": "前後になる関係",
    "qualifies": "一方が他方を限定する関係",
    "supports_without_guarantee": "保証せず支える関係",
}
_LINK_SURFACE_TOKENS: Final = {
    relation_type + ":" + direction: (
        ("互いに" if direction == "bidirectional" else "") + token
    )
    for relation_type, token in _LINK_BASE_TOKENS.items()
    for direction in ("bidirectional", "source_to_target")
}
_EXPECTED_CATALOG: Final = {
    "schema_version": STEP11_RC0029_EXPERIMENT_SURFACE_CATALOG_SCHEMA,
    "catalog_version": STEP11_RC0029_EXPERIMENT_SURFACE_CATALOG_VERSION,
    "construction_surface_tokens": dict(
        _PARENT["construction_surface_tokens"]
    ),
    "construction_role_layouts": {
        code: list(role_keys)
        for code, role_keys in _CONSTRUCTION_ROLE_LAYOUTS.items()
    },
    "role_position_surface_tokens": dict(_ROLE_POSITION_SURFACE_TOKENS),
    "relation_surface_tokens": dict(_RELATION_SURFACE_TOKENS),
    "semantic_link_surface_tokens": dict(_LINK_SURFACE_TOKENS),
    "unknown_surface_tokens": dict(_PARENT["unknown_surface_tokens"]),
    "owner_role_surface_tokens": dict(_OWNER_ROLE_SURFACE_TOKENS),
    "owner_kind_surface_tokens": dict(_OWNER_KIND_SURFACE_TOKENS),
    "reception_act_surface_tokens": dict(
        _RECEPTION_ACT_SURFACE_TOKENS
    ),
    "morphology": dict(_MORPHOLOGY),
    "experimental_only": True,
    "runtime_connected": False,
    "body_free": True,
}

STEP11_RC0029_EXPERIMENT_SURFACE_CATALOG: dict[str, Any] = {
    key: (
        {
            child_key: (
                list(child_value)
                if type(child_value) is list
                else child_value
            )
            for child_key, child_value in value.items()
        }
        if type(value) is dict
        else value
    )
    for key, value in _EXPECTED_CATALOG.items()
}
STEP11_RC0029_EXPERIMENT_SURFACE_CATALOG_SHA256: Final = artifact_sha256(
    _EXPECTED_CATALOG
)

_CONTROL_RE: Final = re.compile(r"[\r\n\x00-\x1f\x7f\u2028\u2029]")
_FORBIDDEN_EXPOSITION = (
    "構造を見ると",
    "まだ定まらない点として",
    "つ目の内容",
)


def _token_valid(value: Any) -> bool:
    return (
        type(value) is str
        and value == value.strip()
        and 1 <= len(value) <= 96
        and unicodedata.normalize("NFC", value) == value
        and _CONTROL_RE.search(value) is None
        and not any(unicodedata.category(char).startswith("C") for char in value)
        and not any(marker in value for marker in _FORBIDDEN_EXPOSITION)
    )


def validate_step11_rc0029_experiment_surface_catalog(
    value: Any,
) -> tuple[str, ...]:
    if type(value) is not dict:
        return ("STEP11_RC0029_CATALOG_SHAPE_INVALID",)
    issues: set[str] = set()
    if set(value) != set(_EXPECTED_CATALOG):
        return ("STEP11_RC0029_CATALOG_SHAPE_INVALID",)
    if (
        value.get("schema_version")
        != STEP11_RC0029_EXPERIMENT_SURFACE_CATALOG_SCHEMA
        or value.get("catalog_version")
        != STEP11_RC0029_EXPERIMENT_SURFACE_CATALOG_VERSION
        or value.get("experimental_only") is not True
        or value.get("runtime_connected") is not False
        or value.get("body_free") is not True
    ):
        issues.add("STEP11_RC0029_CATALOG_CONTRACT_MISMATCH")
    for name in (
        "construction_surface_tokens",
        "role_position_surface_tokens",
        "relation_surface_tokens",
        "semantic_link_surface_tokens",
        "unknown_surface_tokens",
        "owner_role_surface_tokens",
        "owner_kind_surface_tokens",
        "reception_act_surface_tokens",
        "morphology",
    ):
        current = value.get(name)
        expected = _EXPECTED_CATALOG[name]
        if (
            type(current) is not dict
            or current != expected
            or set(current) != set(expected)
            or any(not _token_valid(key) or not _token_valid(token) for key, token in current.items())
        ):
            issues.add("STEP11_RC0029_CATALOG_TOKEN_MISMATCH")
    layouts = value.get("construction_role_layouts")
    if (
        type(layouts) is not dict
        or layouts != _EXPECTED_CATALOG["construction_role_layouts"]
        or set(layouts) != set(value.get("construction_surface_tokens", {}))
        or any(
            type(rows) is not list
            or not rows
            or len(rows) != len(set(rows))
            or any(
                type(role_key) is not str
                or role_key not in value.get(
                    "role_position_surface_tokens", {}
                )
                for role_key in rows
            )
            for rows in layouts.values()
        )
    ):
        issues.add("STEP11_RC0029_CATALOG_ROLE_LAYOUT_MISMATCH")
    visible = tuple(
        token
        for name in (
            "construction_surface_tokens",
            "role_position_surface_tokens",
            "relation_surface_tokens",
            "semantic_link_surface_tokens",
            "unknown_surface_tokens",
            "owner_role_surface_tokens",
            "owner_kind_surface_tokens",
            "reception_act_surface_tokens",
        )
        for token in value.get(name, {}).values()
    )
    if len(set(visible)) != len(visible):
        # Cross-registry collisions make the inverse grammar ambiguous.
        issues.add("STEP11_RC0029_CATALOG_TOKEN_COLLISION")
    try:
        current_sha256 = artifact_sha256(value)
    except (TypeError, ValueError):
        current_sha256 = ""
    if current_sha256 != STEP11_RC0029_EXPERIMENT_SURFACE_CATALOG_SHA256:
        issues.add("STEP11_RC0029_CATALOG_HASH_MISMATCH")
    return tuple(sorted(issues))


__all__ = [
    "STEP11_RC0029_EXPERIMENT_SURFACE_CATALOG",
    "STEP11_RC0029_EXPERIMENT_SURFACE_CATALOG_SCHEMA",
    "STEP11_RC0029_EXPERIMENT_SURFACE_CATALOG_SHA256",
    "STEP11_RC0029_EXPERIMENT_SURFACE_CATALOG_VERSION",
    "validate_step11_rc0029_experiment_surface_catalog",
]
