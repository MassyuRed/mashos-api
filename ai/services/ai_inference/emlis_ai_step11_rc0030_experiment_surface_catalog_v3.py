# -*- coding: utf-8 -*-
from __future__ import annotations

"""Closed clause fragments for the disconnected rc0030 experiment.

The catalog owns one declarative realization alternative for each frozen
semantic key.  Values are noun heads, particles, connectives, or predicate
fragments rather than completed responses or input-specific cues.
"""

import re
import unicodedata
from typing import Any, Final

from emlis_ai_nls_v3_artifact_contract import artifact_sha256


STEP11_RC0030_EXPERIMENT_SURFACE_CATALOG_SCHEMA: Final = (
    "cocolon.emlis.nls_v3.step11.rc0030_experiment_surface_catalog.v1"
)
STEP11_RC0030_EXPERIMENT_SURFACE_CATALOG_VERSION: Final = (
    "cocolon.emlis.nls_v3.step11.rc0030_experiment_surface_catalog."
    "20260719.v1"
)
STEP11_RC0030_OWNER_MAX: Final = 24
STEP11_RC0030_REFERENT_SCALAR_MAX: Final = 32

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

_CONSTRUCTION_CLAUSE_FRAGMENTS: Final = {
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

_ROLE_POSITION_CLAUSE_FRAGMENTS: Final = {
    "action_lifecycle:lifecycle": "進み具合",
    "antecedent_predication:antecedent": "先にある内容",
    "consequent_predication:consequent": "後に続く内容",
    "predicate_or_event:predicate": "動き",
    "referent_primary:primary": "中心となる内容",
    "referent_secondary:secondary": "もう一方の内容",
    "state_or_quality:quality": "感じ方",
    "transition_or_relation:connector": "つながり",
    "unknown_or_limit:limit": "まだ定まらない部分",
}

_RELATION_BASE_FRAGMENTS: Final = {
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
_RELATION_CLAUSE_FRAGMENTS: Final = {
    relation_type + ":" + direction: (
        ("双方向の" if direction == "bidirectional" else "一方向の")
        + fragment
    )
    for relation_type, fragment in _RELATION_BASE_FRAGMENTS.items()
    for direction in ("bidirectional", "source_to_target")
}

_SEMANTIC_LINK_BASE_FRAGMENTS: Final = {
    "coexists_with": "共にある関係",
    "contrasts_with": "対照になる関係",
    "precedes": "前後になる関係",
    "qualifies": "一方が他方を限定する関係",
    "supports_without_guarantee": "保証せず支える関係",
}
_SEMANTIC_LINK_CLAUSE_FRAGMENTS: Final = {
    relation_type + ":" + direction: (
        ("双方向の" if direction == "bidirectional" else "一方向の")
        + fragment
    )
    for relation_type, fragment in _SEMANTIC_LINK_BASE_FRAGMENTS.items()
    for direction in ("bidirectional", "source_to_target")
}

_UNKNOWN_CLAUSE_FRAGMENTS: Final = {
    "explicit_cause_unknown": "理由がまだ分からないところ",
    "explicit_choice_decision_unknown": "選択がまだ決まっていないところ",
    "explicit_temporal_referent_unknown": "時点がまだはっきりしないところ",
    "explicit_unverbalized_unknown": "まだ言葉になっていないところ",
}

_OWNER_ROLE_CLAUSE_FRAGMENTS: Final = {
    "relation_from": "起点",
    "relation_to": "到達先",
    "semantic_link_from": "結びつきの起点",
    "semantic_link_to": "結びつきの到達先",
    "explicit_unknown": "未確定の対象",
    "reception_antecedent": "受け止める対象",
    "reception_target": "応答を向ける対象",
    "reception_support": "応答を支える内容",
}

_OWNER_KIND_REFERENT_HEADS: Final = {
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

_RECEPTION_ACT_PREDICATE_FRAGMENTS: Final = {
    "hold_in_attention": "気に留めます",
    "do_not_dismiss": "軽く扱いません",
    "honor_concrete_action": "具体的な行動として大切に受け取ります",
}

_CLAUSE_MORPHOLOGY: Final = {
    "topic_particle": "は",
    "object_particle": "を",
    "source_particle": "から",
    "target_particle": "へ",
    "symmetric_join": "と",
    "support_particle": "を踏まえ",
    "support_join": "と",
    "target_join": "と",
    "construction_item_link": "にある",
    "directed_item_link": "へ続く",
    "bidirectional_item_link": "を結ぶ",
    "unknown_item_link": "についての",
    "semantic_item_join": "と",
    "semantic_pack_predicate_suffix": "が見えます",
    "clause_join": "、",
    "grammatical_chunk_join": "。",
    "sentence_suffix": "。",
}

_RESOURCE_BOUNDS: Final = {
    "owner_max": STEP11_RC0030_OWNER_MAX,
    "referent_scalar_max": STEP11_RC0030_REFERENT_SCALAR_MAX,
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

_EXPECTED_CATALOG: Final = {
    "schema_version": STEP11_RC0030_EXPERIMENT_SURFACE_CATALOG_SCHEMA,
    "catalog_version": STEP11_RC0030_EXPERIMENT_SURFACE_CATALOG_VERSION,
    "construction_clause_fragments": dict(_CONSTRUCTION_CLAUSE_FRAGMENTS),
    "construction_role_layouts": {
        code: list(layout) for code, layout in _CONSTRUCTION_ROLE_LAYOUTS.items()
    },
    "role_position_clause_fragments": dict(
        _ROLE_POSITION_CLAUSE_FRAGMENTS
    ),
    "relation_clause_fragments": dict(_RELATION_CLAUSE_FRAGMENTS),
    "semantic_link_clause_fragments": dict(
        _SEMANTIC_LINK_CLAUSE_FRAGMENTS
    ),
    "unknown_clause_fragments": dict(_UNKNOWN_CLAUSE_FRAGMENTS),
    "owner_role_clause_fragments": dict(_OWNER_ROLE_CLAUSE_FRAGMENTS),
    "owner_kind_referent_heads": dict(_OWNER_KIND_REFERENT_HEADS),
    "reception_act_predicate_fragments": dict(
        _RECEPTION_ACT_PREDICATE_FRAGMENTS
    ),
    "clause_morphology": dict(_CLAUSE_MORPHOLOGY),
    "resource_bounds": dict(_RESOURCE_BOUNDS),
    "realization_alternatives_per_semantic_key": 1,
    "experimental_only": True,
    "runtime_connected": False,
    "body_free": True,
}


def _copy_catalog(value: dict[str, Any]) -> dict[str, Any]:
    return {
        key: (
            {
                child_key: (
                    list(child_value)
                    if type(child_value) is list
                    else child_value
                )
                for child_key, child_value in child.items()
            }
            if type(child) is dict
            else child
        )
        for key, child in value.items()
    }


STEP11_RC0030_EXPERIMENT_SURFACE_CATALOG: dict[str, Any] = _copy_catalog(
    _EXPECTED_CATALOG
)
STEP11_RC0030_EXPERIMENT_SURFACE_CATALOG_SHA256: Final = artifact_sha256(
    _EXPECTED_CATALOG
)

_MACHINE_KEY_RE: Final = re.compile(r"^[a-z][a-z0-9_:]{1,95}$")
_CONTROL_RE: Final = re.compile(r"[\r\n\x00-\x1f\x7f\u200b-\u200f\u2028\u2029\ufeff]")
_FORBIDDEN_TEXT_MARKERS: Final = (
    "見えたこと",
    "Emlisから",
    "構造を見ると",
    "そこには",
    "つ目",
    "owner",
    "relation record",
)


def _fragment_valid(value: Any, *, allow_sentence_suffix: bool = False) -> bool:
    return bool(
        type(value) is str
        and value == value.strip()
        and 1 <= len(value) <= 96
        and unicodedata.normalize("NFC", value) == value
        and _CONTROL_RE.search(value) is None
        and not any(marker in value for marker in _FORBIDDEN_TEXT_MARKERS)
        and not any(unicodedata.category(char).startswith("C") for char in value)
        and (
            allow_sentence_suffix
            or not value.endswith(("。", "！", "？", "!", "?"))
        )
    )


def _exact_fragment_mapping(
    value: Any,
    expected: dict[str, str],
) -> bool:
    return bool(
        type(value) is dict
        and value == expected
        and set(value) == set(expected)
        and all(
            type(key) is str
            and _MACHINE_KEY_RE.fullmatch(key) is not None
            and _fragment_valid(fragment)
            for key, fragment in value.items()
        )
    )


def validate_step11_rc0030_experiment_surface_catalog(
    value: Any,
) -> tuple[str, ...]:
    """Validate exact denominator, fragments, and immutable commitment."""

    if type(value) is not dict:
        return ("STEP11_RC0030_CATALOG_SHAPE_INVALID",)
    issues: set[str] = set()
    if set(value) != set(_EXPECTED_CATALOG):
        return ("STEP11_RC0030_CATALOG_SHAPE_INVALID",)
    if (
        value.get("schema_version")
        != STEP11_RC0030_EXPERIMENT_SURFACE_CATALOG_SCHEMA
        or value.get("catalog_version")
        != STEP11_RC0030_EXPERIMENT_SURFACE_CATALOG_VERSION
        or value.get("realization_alternatives_per_semantic_key") != 1
        or value.get("experimental_only") is not True
        or value.get("runtime_connected") is not False
        or value.get("body_free") is not True
    ):
        issues.add("STEP11_RC0030_CATALOG_CONTRACT_MISMATCH")

    fragment_mappings = (
        ("construction_clause_fragments", _CONSTRUCTION_CLAUSE_FRAGMENTS),
        ("role_position_clause_fragments", _ROLE_POSITION_CLAUSE_FRAGMENTS),
        ("relation_clause_fragments", _RELATION_CLAUSE_FRAGMENTS),
        (
            "semantic_link_clause_fragments",
            _SEMANTIC_LINK_CLAUSE_FRAGMENTS,
        ),
        ("unknown_clause_fragments", _UNKNOWN_CLAUSE_FRAGMENTS),
        ("owner_role_clause_fragments", _OWNER_ROLE_CLAUSE_FRAGMENTS),
        ("owner_kind_referent_heads", _OWNER_KIND_REFERENT_HEADS),
        (
            "reception_act_predicate_fragments",
            _RECEPTION_ACT_PREDICATE_FRAGMENTS,
        ),
    )
    for name, expected in fragment_mappings:
        if not _exact_fragment_mapping(value.get(name), expected):
            issues.add("STEP11_RC0030_CATALOG_FRAGMENT_MISMATCH")

    layouts = value.get("construction_role_layouts")
    expected_layouts = _EXPECTED_CATALOG["construction_role_layouts"]
    if (
        type(layouts) is not dict
        or layouts != expected_layouts
        or set(layouts) != set(_CONSTRUCTION_CLAUSE_FRAGMENTS)
        or any(
            type(rows) is not list
            or not rows
            or len(rows) != len(set(rows))
            or any(
                role_key not in _ROLE_POSITION_CLAUSE_FRAGMENTS
                for role_key in rows
            )
            for rows in layouts.values()
        )
    ):
        issues.add("STEP11_RC0030_CATALOG_ROLE_LAYOUT_MISMATCH")

    morphology = value.get("clause_morphology")
    if (
        type(morphology) is not dict
        or morphology != _CLAUSE_MORPHOLOGY
        or set(morphology) != set(_CLAUSE_MORPHOLOGY)
        or any(
            not _fragment_valid(
                fragment,
                allow_sentence_suffix=(key in {
                    "grammatical_chunk_join",
                    "sentence_suffix",
                }),
            )
            for key, fragment in morphology.items()
        )
    ):
        issues.add("STEP11_RC0030_CATALOG_MORPHOLOGY_MISMATCH")

    bounds = value.get("resource_bounds")
    if type(bounds) is not dict or bounds != _RESOURCE_BOUNDS:
        issues.add("STEP11_RC0030_CATALOG_RESOURCE_MISMATCH")

    visible_fragments = tuple(
        fragment
        for _name, expected in fragment_mappings
        for fragment in expected.values()
    )
    if len(set(visible_fragments)) != len(visible_fragments):
        issues.add("STEP11_RC0030_CATALOG_FRAGMENT_COLLISION")
    try:
        current_sha256 = artifact_sha256(value)
    except (TypeError, ValueError):
        current_sha256 = ""
    if current_sha256 != STEP11_RC0030_EXPERIMENT_SURFACE_CATALOG_SHA256:
        issues.add("STEP11_RC0030_CATALOG_HASH_MISMATCH")
    return tuple(sorted(issues))


__all__ = [
    "STEP11_RC0030_EXPERIMENT_SURFACE_CATALOG",
    "STEP11_RC0030_EXPERIMENT_SURFACE_CATALOG_SCHEMA",
    "STEP11_RC0030_EXPERIMENT_SURFACE_CATALOG_SHA256",
    "STEP11_RC0030_EXPERIMENT_SURFACE_CATALOG_VERSION",
    "STEP11_RC0030_OWNER_MAX",
    "STEP11_RC0030_REFERENT_SCALAR_MAX",
    "validate_step11_rc0030_experiment_surface_catalog",
]
