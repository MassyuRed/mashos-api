# -*- coding: utf-8 -*-
from __future__ import annotations

"""Closed predicate morphology for the disconnected rc0031 experiment.

The catalog owns exactly one predicate/connective choice for each frozen
typed semantic key.  It contains no completed response, case cue, expected
output, or review result.  Visible referents are supplied from the validated
rc0027/E1b lexical projection and are never invented here.

Construction entries are non-finite noun-phrase suffixes.  The canonical
renderer either attaches one to an exact head endpoint or closes an unpaired
construction with the single standalone predicate owned below.
"""

import re
import unicodedata
from typing import Any, Final

from emlis_ai_nls_v3_artifact_contract import artifact_sha256


STEP11_RC0031_EXPERIMENT_SURFACE_CATALOG_SCHEMA: Final = (
    "cocolon.emlis.nls_v3.step11.rc0031_experiment_surface_catalog.v1"
)
STEP11_RC0031_EXPERIMENT_SURFACE_CATALOG_VERSION: Final = (
    "cocolon.emlis.nls_v3.step11.rc0031_experiment_surface_catalog."
    "20260720.v1"
)
STEP11_RC0031_OWNER_MAX: Final = 24
STEP11_RC0031_REFERENT_SCALAR_MAX: Final = 32

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

_ROLE_POSITION_PREDICATE_PATTERNS: Final = {
    "action_lifecycle:lifecycle": "topic_referent",
    "antecedent_predication:antecedent": "ordered_source_referent",
    "consequent_predication:consequent": "ordered_target_referent",
    "predicate_or_event:predicate": "finite_predicate",
    "referent_primary:primary": "primary_referent",
    "referent_secondary:secondary": "secondary_referent",
    "state_or_quality:quality": "predicative_modifier",
    "transition_or_relation:connector": "typed_connective",
    "unknown_or_limit:limit": "epistemic_predicate",
}

_OWNER_ROLE_PARTICLE_PATTERNS: Final = {
    "relation_from": "directed_source_particle",
    "relation_to": "directed_target_particle",
    "semantic_link_from": "directed_source_particle",
    "semantic_link_to": "directed_target_particle",
    "explicit_unknown": "unknown_topic_particle",
    "reception_antecedent": "support_target_link",
    "reception_target": "reception_object_particle",
    "reception_support": "support_source_particle",
}

_OWNER_KIND_INFLECTION_PATTERNS: Final = {
    "event": "grounded_referent_uninflected",
    "state": "grounded_referent_uninflected",
    "reaction": "grounded_referent_uninflected",
    "wish": "grounded_referent_uninflected",
    "constraint": "grounded_referent_uninflected",
    "action": "grounded_referent_uninflected",
    "change": "grounded_referent_uninflected",
    "self_evaluation": "grounded_referent_uninflected",
    "value": "grounded_referent_uninflected",
    "uncertainty": "grounded_referent_uninflected",
    "conclusion": "grounded_referent_uninflected",
    "other_explicit": "grounded_referent_uninflected",
}

_CONSTRUCTION_PREDICATE_FRAGMENTS: Final = {
    "balanced_consideration": "を両方とも視野に入れている向き",
    "choice_uncertainty": "をまだ選び切れていない局面",
    "comparative_assessment": "を照らし合わせている捉え方",
    "decision_timing": "を決める時をまだ定めていない段階",
    "explicit_coexistence": "を同時に認めている捉え方",
    "explicit_contrast": "を異なるものとして並べている捉え方",
    "nonreduction_boundary": "を単一の答えに縮めていない捉え方",
    "ordered_sequence": "を示された順に辿っている捉え方",
    "parallel_addition": "を等しく並べている捉え方",
    "particle_object": "へ向けられている働きかけ",
    "purpose_action": "を目指して進めている歩み",
    "reported_self_assessment": "を自分への評価として述べている受け止め",
    "withheld_action": "に対してすぐには踏み出さずにいる構え",
}

_RELATION_PREDICATE_FRAGMENTS: Final = {
    "action_supports_change:source_to_target": (
        "{source}が{target}を後押ししています"
    ),
    "action_supports_change:bidirectional": (
        "{source}と{target}が互いを後押ししています"
    ),
    "attempt_and_block:source_to_target": (
        "{source}を進めようとする力を{target}が阻んでいます"
    ),
    "attempt_and_block:bidirectional": (
        "{source}と{target}が進む力と阻む力としてせめぎ合っています"
    ),
    "coexistence:source_to_target": (
        "{source}に加えて{target}も同時に保たれています"
    ),
    "coexistence:bidirectional": (
        "{source}と{target}が異なるまま同時に成り立っています"
    ),
    "continuation_or_refusal:source_to_target": (
        "{source}を続けようとする向きに{target}が歯止めをかけています"
    ),
    "continuation_or_refusal:bidirectional": (
        "{source}と{target}が続ける向きと退く向きとして並んでいます"
    ),
    "contrast:source_to_target": (
        "{source}に対して{target}は別の側を示しています"
    ),
    "contrast:bidirectional": (
        "{source}と{target}が互いに異なる側を示しています"
    ),
    "evaluation_about_event:source_to_target": (
        "{source}を受けて{target}には受け止め方が表れています"
    ),
    "evaluation_about_event:bidirectional": (
        "{source}と{target}が起きたこととその受け止め方として結ばれています"
    ),
    "preserves_despite:source_to_target": (
        "{target}があっても{source}はそれでもなお保たれています"
    ),
    "preserves_despite:bidirectional": (
        "{source}と{target}が互いを消さずに残っています"
    ),
    "self_evaluation_about_state:source_to_target": (
        "{source}を自分に重ねた{target}には自分への見方が表れています"
    ),
    "self_evaluation_about_state:bidirectional": (
        "{source}と{target}が自分への見方として関わり合っています"
    ),
    "shift_from_to:source_to_target": (
        "{source}から{target}へ捉え方が移っています"
    ),
    "shift_from_to:bidirectional": (
        "{source}と{target}の間を捉え方が行き来しています"
    ),
    "temporal_before_after:source_to_target": (
        "{source}の後に{target}が現れています"
    ),
    "temporal_before_after:bidirectional": (
        "{source}と{target}が時間の前後を持って並んでいます"
    ),
    "uncertain_connection:source_to_target": (
        "{source}に続いて{target}がありますが、因果までは確定していません"
    ),
    "uncertain_connection:bidirectional": (
        "{source}と{target}には関わりがありますが、因果までは確定していません"
    ),
    "user_stated_cause:source_to_target": (
        "{source}を理由として{target}が語られています"
    ),
    "user_stated_cause:bidirectional": (
        "{source}と{target}が本人の述べた理由によって結ばれています"
    ),
    "user_stated_result:source_to_target": (
        "{source}を受けた結果として{target}が語られています"
    ),
    "user_stated_result:bidirectional": (
        "{source}と{target}が本人の述べた結果によって結ばれています"
    ),
    "wish_and_constraint:source_to_target": (
        "{source}から{target}へ、望む力と歩みを抑える力のせめぎ合いが続いています"
    ),
    "wish_and_constraint:bidirectional": (
        "{source}と{target}が望む力と歩みを抑える力としてせめぎ合っています"
    ),
}

_SEMANTIC_LINK_PREDICATE_FRAGMENTS: Final = {
    "coexists_with:source_to_target": (
        "{source}に加えて{target}も共に置かれています"
    ),
    "coexists_with:bidirectional": (
        "{source}と{target}が異なるまま共に置かれています"
    ),
    "contrasts_with:source_to_target": (
        "{source}に対して{target}は異なる側を示しています"
    ),
    "contrasts_with:bidirectional": (
        "{source}と{target}が互いに異なる側を保っています"
    ),
    "precedes:source_to_target": "{source}を経て{target}が続いています",
    "precedes:bidirectional": (
        "{source}と{target}が前後を持って続いています"
    ),
    "qualifies:source_to_target": "{source}が{target}の範囲を定めています",
    "qualifies:bidirectional": (
        "{source}と{target}が互いの範囲を定めています"
    ),
    "supports_without_guarantee:source_to_target": (
        "{source}が{target}を支えていますが、確実だとはしていません"
    ),
    "supports_without_guarantee:bidirectional": (
        "{source}と{target}が互いを支えていますが、確実だとはしていません"
    ),
}

_UNKNOWN_PREDICATE_FRAGMENTS: Final = {
    "explicit_cause_unknown": "の理由はまだ特定できません",
    "explicit_choice_decision_unknown": "でどれを選ぶかはまだ確定していません",
    "explicit_temporal_referent_unknown": "がいつかはまだ確定していません",
    "explicit_unverbalized_unknown": "にはまだ言葉にできない箇所があります",
}

_RECEPTION_ACT_PREDICATE_FRAGMENTS: Final = {
    "hold_in_attention": "見失わず受け止めます",
    "do_not_dismiss": "小さくせず受け止めます",
    "honor_concrete_action": "重みのある実行として受け止めます",
}

_CLAUSE_MORPHOLOGY: Final = {
    "directed_source_particle": "から",
    "directed_target_particle": "へ",
    "bidirectional_endpoint_join": "と",
    "bidirectional_relation_particle": "の間で",
    "unknown_owner_join": "と",
    "support_owner_join": "と",
    "support_target_link": "に支えられた",
    "target_owner_join": "と",
    "reception_object_particle": "を",
    "construction_standalone_predicate": "があります",
    "within_sentence_clause_join": "、そして",
    "grammatical_sentence_join": "。",
    "sentence_suffix": "。",
}

_RESOURCE_BOUNDS: Final = {
    "owner_max": STEP11_RC0031_OWNER_MAX,
    "referent_scalar_max": STEP11_RC0031_REFERENT_SCALAR_MAX,
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

_EXPECTED_CATALOG: Final = {
    "schema_version": STEP11_RC0031_EXPERIMENT_SURFACE_CATALOG_SCHEMA,
    "catalog_version": STEP11_RC0031_EXPERIMENT_SURFACE_CATALOG_VERSION,
    "construction_predicate_fragments": dict(
        _CONSTRUCTION_PREDICATE_FRAGMENTS
    ),
    "construction_role_layouts": {
        code: list(layout) for code, layout in _CONSTRUCTION_ROLE_LAYOUTS.items()
    },
    "role_position_predicate_patterns": dict(
        _ROLE_POSITION_PREDICATE_PATTERNS
    ),
    "relation_predicate_fragments": dict(_RELATION_PREDICATE_FRAGMENTS),
    "semantic_link_predicate_fragments": dict(
        _SEMANTIC_LINK_PREDICATE_FRAGMENTS
    ),
    "unknown_predicate_fragments": dict(_UNKNOWN_PREDICATE_FRAGMENTS),
    "owner_role_particle_patterns": dict(_OWNER_ROLE_PARTICLE_PATTERNS),
    "owner_kind_inflection_patterns": dict(_OWNER_KIND_INFLECTION_PATTERNS),
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


STEP11_RC0031_EXPERIMENT_SURFACE_CATALOG: dict[str, Any] = _copy_catalog(
    _EXPECTED_CATALOG
)
STEP11_RC0031_EXPERIMENT_SURFACE_CATALOG_SHA256: Final = artifact_sha256(
    _EXPECTED_CATALOG
)

_MACHINE_KEY_RE: Final = re.compile(r"^[a-z][a-z0-9_:]{1,95}$")
_CONTROL_RE: Final = re.compile(
    r"[\r\n\x00-\x1f\x7f\u200b-\u200f\u2028\u2029\ufeff]"
)
_FORBIDDEN_TEXT_MARKERS: Final = (
    "見えたこと",
    "Emlisから",
    "構造を見ると",
    "そこには",
    "つ目",
    "owner",
    "relation record",
    "case_id",
    "control",
    "review",
    "reason_code",
    "expected_output",
    "「",
    "」",
)
_FORBIDDEN_COMPLETED_SUFFIXES: Final = ("。", "！", "？", "!", "?")


def _fragment_valid(value: Any, *, punctuation: bool = False) -> bool:
    return bool(
        type(value) is str
        and value == value.strip()
        and 1 <= len(value) <= 96
        and unicodedata.normalize("NFC", value) == value
        and _CONTROL_RE.search(value) is None
        and not any(marker in value for marker in _FORBIDDEN_TEXT_MARKERS)
        and not any(unicodedata.category(char).startswith("C") for char in value)
        and (punctuation or not value.endswith(_FORBIDDEN_COMPLETED_SUFFIXES))
    )


def _machine_mapping(value: Any, expected: dict[str, str]) -> bool:
    return bool(
        type(value) is dict
        and value == expected
        and set(value) == set(expected)
        and all(
            type(key) is str
            and _MACHINE_KEY_RE.fullmatch(key) is not None
            and type(pattern) is str
            and _MACHINE_KEY_RE.fullmatch(pattern) is not None
            for key, pattern in value.items()
        )
    )


def _fragment_mapping(value: Any, expected: dict[str, str]) -> bool:
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


def validate_step11_rc0031_experiment_surface_catalog(
    value: Any,
) -> tuple[str, ...]:
    """Validate exact semantic denominator and immutable commitment."""

    if type(value) is not dict or set(value) != set(_EXPECTED_CATALOG):
        return ("STEP11_RC0031_CATALOG_SHAPE_INVALID",)
    issues: set[str] = set()
    if (
        value.get("schema_version")
        != STEP11_RC0031_EXPERIMENT_SURFACE_CATALOG_SCHEMA
        or value.get("catalog_version")
        != STEP11_RC0031_EXPERIMENT_SURFACE_CATALOG_VERSION
        or value.get("realization_alternatives_per_semantic_key") != 1
        or value.get("experimental_only") is not True
        or value.get("runtime_connected") is not False
        or value.get("body_free") is not True
    ):
        issues.add("STEP11_RC0031_CATALOG_CONTRACT_MISMATCH")

    fragment_mappings = (
        ("construction_predicate_fragments", _CONSTRUCTION_PREDICATE_FRAGMENTS),
        ("relation_predicate_fragments", _RELATION_PREDICATE_FRAGMENTS),
        (
            "semantic_link_predicate_fragments",
            _SEMANTIC_LINK_PREDICATE_FRAGMENTS,
        ),
        ("unknown_predicate_fragments", _UNKNOWN_PREDICATE_FRAGMENTS),
        (
            "reception_act_predicate_fragments",
            _RECEPTION_ACT_PREDICATE_FRAGMENTS,
        ),
    )
    for name, expected in fragment_mappings:
        if not _fragment_mapping(value.get(name), expected):
            issues.add("STEP11_RC0031_CATALOG_FRAGMENT_MISMATCH")

    machine_mappings = (
        ("role_position_predicate_patterns", _ROLE_POSITION_PREDICATE_PATTERNS),
        ("owner_role_particle_patterns", _OWNER_ROLE_PARTICLE_PATTERNS),
        ("owner_kind_inflection_patterns", _OWNER_KIND_INFLECTION_PATTERNS),
    )
    for name, expected in machine_mappings:
        if not _machine_mapping(value.get(name), expected):
            issues.add("STEP11_RC0031_CATALOG_PATTERN_MISMATCH")

    layouts = value.get("construction_role_layouts")
    expected_layouts = _EXPECTED_CATALOG["construction_role_layouts"]
    if (
        type(layouts) is not dict
        or layouts != expected_layouts
        or set(layouts) != set(_CONSTRUCTION_PREDICATE_FRAGMENTS)
        or any(
            type(rows) is not list
            or not rows
            or len(rows) != len(set(rows))
            or any(
                role_key not in _ROLE_POSITION_PREDICATE_PATTERNS
                for role_key in rows
            )
            for rows in layouts.values()
        )
    ):
        issues.add("STEP11_RC0031_CATALOG_ROLE_LAYOUT_MISMATCH")

    morphology = value.get("clause_morphology")
    if (
        type(morphology) is not dict
        or morphology != _CLAUSE_MORPHOLOGY
        or any(
            not _fragment_valid(
                fragment,
                punctuation=(key in {
                    "grammatical_sentence_join",
                    "sentence_suffix",
                }),
            )
            for key, fragment in morphology.items()
        )
    ):
        issues.add("STEP11_RC0031_CATALOG_MORPHOLOGY_MISMATCH")
    if value.get("resource_bounds") != _RESOURCE_BOUNDS:
        issues.add("STEP11_RC0031_CATALOG_RESOURCE_MISMATCH")
    try:
        current_sha256 = artifact_sha256(value)
    except (TypeError, ValueError):
        current_sha256 = ""
    if current_sha256 != STEP11_RC0031_EXPERIMENT_SURFACE_CATALOG_SHA256:
        issues.add("STEP11_RC0031_CATALOG_HASH_MISMATCH")
    return tuple(sorted(issues))


__all__ = [
    "STEP11_RC0031_EXPERIMENT_SURFACE_CATALOG",
    "STEP11_RC0031_EXPERIMENT_SURFACE_CATALOG_SCHEMA",
    "STEP11_RC0031_EXPERIMENT_SURFACE_CATALOG_SHA256",
    "STEP11_RC0031_EXPERIMENT_SURFACE_CATALOG_VERSION",
    "STEP11_RC0031_OWNER_MAX",
    "STEP11_RC0031_REFERENT_SCALAR_MAX",
    "validate_step11_rc0031_experiment_surface_catalog",
]
