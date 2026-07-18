# -*- coding: utf-8 -*-
from __future__ import annotations

"""Declarative controlled-surface catalog for the Step 11 rc0027 successor.

This owner intentionally contains no corpus, case, family, expected response,
or executable traversal logic.  The forward renderer and inverse body parser
may share these tokens and rule identifiers, but not each other's algorithms.
"""

from typing import Any

from emlis_ai_nls_v3_artifact_contract import artifact_sha256


_RELATION_TYPES = (
    "precedes",
    "contrasts_with",
    "coexists_with",
    "qualifies",
    "supports_without_guarantee",
)
_RELATION_DIRECTIONS = (
    "source_to_target",
    "target_to_source",
    "bidirectional",
)
_ENDPOINT_ROLES = ("action", "affect", "proposition")
_ENDPOINT_ROLE_LABELS = {
    "action": "行動",
    "affect": "感情",
    "proposition": "記述内容",
}
_REFERENCE_ORDINAL_PATTERN = r"[1-9][0-9]*"
_REFERENCE_TOKEN_TEMPLATE = "{ordinal}つ目の{role_label}"
_GROUP_CLAUSE_SEPARATOR = "。あわせて、"
_GROUP_SENTENCE_SUFFIX = "。"


def _build_fused_relation_forms() -> dict[str, Any]:
    """Return the closed literal-owning relation lattice used by rc0027.

    Every row owns both endpoint positions in one sentence.  The renderer may
    replace exactly one position with a local anaphor after that source
    identity has already been introduced; it never emits a visible ordinal or
    a typed placeholder.
    """

    rows = {
        "precedes": {
            "source_to_target": [
                "{from_endpoint}が先にあり、その後に{to_endpoint}が続いています",
                "{from_endpoint}から{to_endpoint}へと、この順序で続いています",
            ],
            "target_to_source": [
                "{to_endpoint}が先にあり、その後に{from_endpoint}が続いています",
                "{to_endpoint}から{from_endpoint}へと、逆向きの順序が示されています",
            ],
            "bidirectional": [
                "{from_endpoint}と{to_endpoint}の間に、往復する順序が示されています",
                "{from_endpoint}と{to_endpoint}は、双方向の前後を保っています",
            ],
        },
        "contrasts_with": {
            "source_to_target": [
                "{from_endpoint}に対して{to_endpoint}が別の向きとして並んでいます",
                "{from_endpoint}から見た{to_endpoint}との対照が保たれています",
            ],
            "target_to_source": [
                "{to_endpoint}に対して{from_endpoint}が別の向きとして並んでいます",
                "{to_endpoint}から見た{from_endpoint}との対照が保たれています",
            ],
            "bidirectional": [
                "{from_endpoint}と{to_endpoint}が、互いの違いを消さず並んでいます",
                "{from_endpoint}と{to_endpoint}は、どちらかに寄せず対照を保っています",
            ],
        },
        "coexists_with": {
            "source_to_target": [
                "{from_endpoint}を残したまま、{to_endpoint}も同時にあります",
                "{from_endpoint}がある中で、{to_endpoint}も併存しています",
            ],
            "target_to_source": [
                "{to_endpoint}を残したまま、{from_endpoint}も同時にあります",
                "{to_endpoint}がある中で、{from_endpoint}も併存しています",
            ],
            "bidirectional": [
                "{from_endpoint}と{to_endpoint}が、どちらも消されず並んでいます",
                "{from_endpoint}と{to_endpoint}は、片方にまとめず併存しています",
            ],
        },
        "qualifies": {
            "source_to_target": [
                "{from_endpoint}が範囲を限りながら、{to_endpoint}を補足しています",
                "{from_endpoint}を前提の範囲として、{to_endpoint}の読み取りが限定されています",
            ],
            "target_to_source": [
                "{to_endpoint}が範囲を限りながら、{from_endpoint}を補足しています",
                "{to_endpoint}を前提の範囲として、{from_endpoint}の読み取りが限定されています",
            ],
            "bidirectional": [
                "{from_endpoint}と{to_endpoint}が、互いの範囲を限りながら補足し合っています",
                "{from_endpoint}と{to_endpoint}は、双方向の限定を伴っています",
            ],
        },
        "supports_without_guarantee": {
            "source_to_target": [
                "{from_endpoint}が{to_endpoint}を支えていますが、結果までは決めません",
                "{from_endpoint}から{to_endpoint}へ支えが向いていますが、先の展開は補いません",
            ],
            "target_to_source": [
                "{to_endpoint}が{from_endpoint}を支えていますが、結果までは決めません",
                "{to_endpoint}から{from_endpoint}へ支えが向いていますが、先の展開は補いません",
            ],
            "bidirectional": [
                "{from_endpoint}と{to_endpoint}が支え合っていますが、結果までは決めません",
                "{from_endpoint}と{to_endpoint}に双方向の支えがありますが、成功は確定しません",
            ],
        },
    }
    return {
        relation_type: {
            direction: [
                {
                    "stem": stem,
                    "endpoint_realization": (
                        "two_exact_literals_or_one_local_anaphor_and_one_exact_literal"
                    ),
                    "relation_type": relation_type,
                    "relation_direction": direction,
                }
                for stem in stems
            ]
            for direction, stems in directions.items()
        }
        for relation_type, directions in rows.items()
    }


def _legacy_quoted_relation_rule(
    from_role: str,
    to_role: str,
    middle_tail: str,
    suffix_tail: str,
) -> dict[str, str]:
    """Build one frozen rc0018 quote-bearing endpoint rule.

    The role marker is adjacent to its quoted endpoint.  This lets the inverse
    parser recover endpoint roles from the body instead of guessing them from
    a generic relation phrase.
    """

    return {
        "middle": (
            f"という{_ENDPOINT_ROLE_LABELS[from_role]}{middle_tail}"
        ),
        "suffix": (
            f"という{_ENDPOINT_ROLE_LABELS[to_role]}{suffix_tail}"
        ),
    }


def _legacy_quoted_relation_family(
    relation_type: str,
    direction: str,
    from_role: str,
    to_role: str,
) -> list[dict[str, str]]:
    """Return a closed, role-safe family without input-specific vocabulary."""

    if relation_type == "precedes":
        tails = {
            "source_to_target": (
                ("のあとに、", "が続いています。"),
                ("が先にあり、その後に", "が置かれています。"),
            ),
            "target_to_source": (
                ("より前に、", "が先にあります。"),
                ("へ至る前に、", "が先行しています。"),
            ),
            "bidirectional": (
                ("と、", "の双方に前後の往復が示されています。"),
                ("と、", "の間に双方向の順序があります。"),
            ),
        }[direction]
    elif relation_type == "contrasts_with":
        tails = {
            "source_to_target": (
                ("から見て、", "との対照が示されています。"),
                ("を前者として、", "が後者の別の向きとして並んでいます。"),
            ),
            "target_to_source": (
                ("に対して、", "の側から前者への対照が示されています。"),
                ("を前者に置き、", "を後者側の起点とする違いがあります。"),
            ),
            "bidirectional": (
                ("と、", "が双方向の対照を保って並んでいます。"),
                ("と、", "が互いの違いを消さずに残っています。"),
            ),
        }[direction]
    elif relation_type == "coexists_with":
        tails = {
            "source_to_target": (
                ("を残したまま、", "も同時にあります。"),
                ("がある中で、", "も併せて残っています。"),
                ("と並行して、", "も後者側に併存しています。"),
            ),
            "target_to_source": (
                ("とともに、", "が後者側から併存しています。"),
                ("を消さず、", "も後者の側から残っています。"),
                ("に並ぶものとして、", "が後者側の起点にあります。"),
            ),
            "bidirectional": (
                ("と、", "が双方とも消されずに残っています。"),
                ("と、", "が同時に併存しています。"),
                ("と、", "が互いをまとめずに並んでいます。"),
            ),
        }[direction]
    elif relation_type == "qualifies":
        tails = {
            "source_to_target": (
                ("が範囲を限りながら、", "を補足しています。"),
                ("を前提の範囲に置き、", "の読み取りを限定しています。"),
            ),
            "target_to_source": (
                ("が限定されるものとして、", "が後者側から補足しています。"),
                ("を前者に置き、", "の側から読み取りを限定しています。"),
            ),
            "bidirectional": (
                ("と、", "が互いの範囲を限りながら補足し合っています。"),
                ("と、", "が双方向の限定を伴って並んでいます。"),
            ),
        }[direction]
    elif relation_type == "supports_without_guarantee":
        tails = {
            "source_to_target": (
                ("が、", "を支える関係ですが、その結果までは決めません。"),
                ("から、", "へ支えが向いていますが、先の展開は補いません。"),
                ("が支えの起点となり、", "へ続いていますが、成功は確定しません。"),
            ),
            "target_to_source": (
                ("が支えられる側としてあり、", "が後者側から支えますが、結果は決めません。"),
                ("へ向かうものとして、", "から支えがありますが、先は補いません。"),
                ("が前者側にあり、", "が支えの起点ですが、成功は確定しません。"),
            ),
            "bidirectional": (
                ("と、", "が互いを支えていますが、結果までは決めません。"),
                ("と、", "が双方向の支えを作っていますが、先は補いません。"),
                ("と、", "が支え合う関係ですが、成功は確定しません。"),
            ),
        }[direction]
    else:  # pragma: no cover - the closed caller lattice makes this unreachable
        raise ValueError("unsupported relation type")
    return [
        _legacy_quoted_relation_rule(
            from_role, to_role, middle_tail, suffix_tail
        )
        for middle_tail, suffix_tail in tails
    ]


def _reference_relation_family(
    relation_type: str,
    direction: str,
    from_role: str,
    to_role: str,
) -> list[dict[str, str]]:
    """Project the closed rc0018 phrase family onto ref/ref-only stems.

    The lexical relation meanings stay unchanged, but both quoted endpoint
    positions are replaced by typed references.  A group renderer owns the
    one terminal sentence mark, so these are deliberately punctuation-free
    clause stems.
    """

    from_prefix = "という" + _ENDPOINT_ROLE_LABELS[from_role]
    to_prefix = "という" + _ENDPOINT_ROLE_LABELS[to_role]
    result: list[dict[str, str]] = []
    for row in _legacy_quoted_relation_family(
        relation_type,
        direction,
        from_role,
        to_role,
    ):
        middle = row["middle"]
        suffix = row["suffix"]
        if (
            not middle.startswith(from_prefix)
            or not suffix.startswith(to_prefix)
            or not suffix.endswith(_GROUP_SENTENCE_SUFFIX)
        ):  # pragma: no cover - closed literals above make this unreachable
            raise ValueError("legacy relation phrase cannot be projected")
        result.append(
            {
                "stem": (
                    "{from_ref}"
                    + middle[len(from_prefix) :]
                    + "{to_ref}"
                    + suffix[len(to_prefix) : -len(_GROUP_SENTENCE_SUFFIX)]
                ),
                "endpoint_realization": "typed_reference_only",
            }
        )
    return result


def _build_reference_relation_forms() -> dict[str, Any]:
    return {
        relation_type: {
            direction: {
                from_role: {
                    to_role: _reference_relation_family(
                        relation_type,
                        direction,
                        from_role,
                        to_role,
                    )
                    for to_role in _ENDPOINT_ROLES
                }
                for from_role in _ENDPOINT_ROLES
            }
            for direction in _RELATION_DIRECTIONS
        }
        for relation_type in _RELATION_TYPES
    }


def _build_legacy_quoted_relation_forms() -> dict[str, Any]:
    return {
        relation_type: {
            direction: {
                from_role: {
                    to_role: _legacy_quoted_relation_family(
                        relation_type,
                        direction,
                        from_role,
                        to_role,
                    )
                    for to_role in _ENDPOINT_ROLES
                }
                for from_role in _ENDPOINT_ROLES
            }
            for direction in _RELATION_DIRECTIONS
        }
        for relation_type in _RELATION_TYPES
    }


STEP11_SURFACE_CATALOG: dict[str, Any] = {
    "schema_version": "cocolon.emlis.nls_v3.step11_surface_catalog.v10",
    "candidate_version_id": "nls_v3_rc_0027",
    "labels": {
        "observation": "見えたこと：",
        "reception": "Emlisから：",
    },
    "layout": {
        "section_separator": "\n\n",
        "sentence_separator": "\n",
        "line_ending": "\n",
        "quote_open": "『",
        "quote_close": "』",
        "quote_pairs": [
            {"open": "『", "close": "』"},
            {"open": "「", "close": "」"},
        ],
        "quote_pair_selection": "primary_unless_source_contains_primary",
        "quote_escape": "backslash_primary_pair_only_when_both_pairs_present",
    },
    "grounded_lexicalization": {
        "schema_version": (
            "cocolon.emlis.nls_v3.step11_grounded_lexicalization.rc0027.v2"
        ),
        "feature_order": [
            "semantic_role",
            "temporal_scope",
            "modality",
            "source_field",
            "referent_scope",
            "label_strength",
            "polarity",
            "semantic_qualifier",
            "action_lifecycle",
            "nucleus_kind",
        ],
        "concatenation": "ordered_attributive_atoms_without_separator",
        "forward_emission": True,
        "source_realization_policy": (
            "one_grounded_feature_phrase_per_render_reachable_nucleus"
        ),
        "visible_source_anchor_policy": (
            "exactly_one_input_specific_anchor_or_fail_closed"
        ),
        "lifecycle_authority_policy": {
            "authority_order": [
                "exact_source_fragment_realization_status",
                "inventory_nucleus_semantics",
            ],
            "action_projection": {
                "reported_completed": {
                    "modality": "reported",
                    "temporal_scope": "reported_past",
                },
                "reported_ongoing": {
                    "modality": "reported",
                    "temporal_scope": "current_input",
                },
                "reported_not_completed": {
                    "modality": "reported",
                    "temporal_scope": "current_input",
                },
                "intended": {
                    "modality": "intended",
                    "temporal_scope": "intended_future",
                },
            },
            "multiple_exact_statuses": "fail_closed",
            "observation_reception_lifecycle_equality_required": True,
        },
        "anchor_owner_priority_policy": {
            "ordered_classes": [
                "residual_information_loss_risk",
                "remaining_render_reachable",
            ],
            "within_class_order": [
                "anchor_risk_rank_desc",
                "source_snapshot_order",
                "nucleus_id",
            ],
            "selector_score_dependency": False,
        },
        "residual_information_loss_policy": {
            "semantic_attribute_prefixes": [
                "operator:",
                "semantic_role:",
                "unit_role:",
            ],
            "high_signal_attribute_codes": [
                "operator:action",
                "operator:negation",
                "operator:shift",
                "operator:continuation",
                "operator:contrast",
                "operator:coexistence",
                "semantic_role:embedded_turn",
                "semantic_role:retained_intention",
                "unit_role:antecedent",
                "unit_role:consequent",
            ],
            "concrete_action_attribute_code": (
                "semantic_role:concrete_action_evidence"
            ),
            "kind_implied_attribute_codes": {
                "action": [
                    "operator:action",
                    "semantic_role:concrete_action_evidence",
                ],
            },
            "ordered_factors": [
                "required_kind_only_generic",
                "required_relation_or_unknown_owner",
                "required_owner",
                "uncaptured_high_signal_attribute_count",
                "qualified_concrete_action_evidence",
                "uncaptured_semantic_attribute_count",
                "kind_only_generic",
                "static_anchor_risk_rank",
                "source_snapshot_order",
                "nucleus_id",
            ],
            "dynamic_score_in_visible_fingerprint": False,
        },
        "anchor_segment_policy": {
            "unicode_category_c_forbidden": True,
            "mechanical_prefix_truncation": False,
            "complete_run_first": True,
            "minimum_scalars": 2,
            "maximum_scalars": 16,
            "accepted_segment_authorities": [
                "trusted_fragment_entire_text",
                "complete_punctuation_delimited_run",
            ],
            "long_run_subrange_authority": "forbidden",
            "whitespace_or_control_disposition": "fail_closed",
            "unsafe_result": "fail_closed",
            "dangling_prefixes": [
                "そして",
                "また",
                "ただ",
                "それでも",
                "けれど",
                "けど",
                "だけ",
                "は",
                "が",
                "を",
                "に",
                "へ",
                "と",
                "の",
                "も",
                "や",
                "で",
                "から",
                "ので",
            ],
            "dangling_suffixes": [
                "は",
                "が",
                "を",
                "に",
                "へ",
                "と",
                "の",
                "も",
                "や",
                "て",
                "で",
                "し",
                "から",
                "ので",
                "けれど",
                "けど",
                "ながら",
                "つつ",
                "たり",
                "なら",
                "れば",
                "たら",
            ],
        },
        "source_anchor_binding_families": {
            "reported_profile": "に表れている",
            "action_lifecycle": "として示された",
            "relation_shift": "を起点にした",
        },
        "source_anchor_binding_family_order": [
            "relation_shift",
            "reported_profile",
            "action_lifecycle",
        ],
        "phrase_profile_registry": {
            "selection": "first_exact_matching_profile_by_priority",
            "visible_feature_reconstruction": (
                "singleton_from_profile_match_or_lifecycle_projection"
            ),
            "specificity_policy": {
                "kind_only_generic_profile_ids": [
                    "self_evaluation_neutral",
                    "constraint_generic",
                    "event_generic",
                    "state_generic",
                    "other_explicit_generic",
                    "wish_generic",
                    "value_generic",
                    "change_generic",
                    "uncertainty_generic",
                    "conclusion_generic",
                    "action_fallback",
                    "reaction_fallback",
                ],
                "unanchored_required_kind_only_generic": "fail_closed",
            },
            "completed_sentence_bank": False,
            "profiles": [
                {
                    "profile_id": "change_antecedent",
                    "match": {
                        "nucleus_kinds": ["change"],
                        "all_attribute_codes": [
                            "adapter:semantic_decomposition_v3",
                            "unit_role:antecedent",
                        ],
                    },
                    "noun_phrase": "先に示された変化",
                    "visible_feature_names": ["nucleus_kind"],
                    "anchor_risk_rank": 98,
                    "binding_family": "reported_profile",
                },
                {
                    "profile_id": "reaction_consequent",
                    "match": {
                        "nucleus_kinds": ["reaction"],
                        "all_attribute_codes": [
                            "adapter:semantic_decomposition_v3",
                            "unit_role:consequent",
                        ],
                    },
                    "noun_phrase": "その後に続いた気持ち",
                    "visible_feature_names": ["nucleus_kind"],
                    "anchor_risk_rank": 98,
                    "binding_family": "reported_profile",
                },
                {
                    "profile_id": "state_embedded_contrast",
                    "match": {
                        "nucleus_kinds": ["state"],
                        "all_attribute_codes": [
                            "semantic_role:embedded_turn",
                            "operator:contrast",
                        ],
                    },
                    "noun_phrase": "異なる面を含む状態",
                    "visible_feature_names": ["nucleus_kind"],
                    "anchor_risk_rank": 98,
                    "binding_family": "reported_profile",
                },
                {
                    "profile_id": "event_continuation",
                    "match": {
                        "nucleus_kinds": ["event"],
                        "all_attribute_codes": ["operator:continuation"],
                    },
                    "noun_phrase": "継続に関わること",
                    "visible_feature_names": ["nucleus_kind"],
                    "anchor_risk_rank": 96,
                    "binding_family": "reported_profile",
                },
                {
                    "profile_id": "retained_wish",
                    "match": {
                        "nucleus_kinds": ["wish"],
                        "all_attribute_codes": [
                            "semantic_role:retained_intention",
                            "operator:wish",
                        ],
                    },
                    "noun_phrase": "継続中の望み",
                    "visible_feature_names": ["nucleus_kind"],
                    "anchor_risk_rank": 96,
                    "binding_family": "reported_profile",
                },
                {
                    "profile_id": "retained_embedded_intention",
                    "match": {
                        "nucleus_kinds": ["other_explicit"],
                        "all_attribute_codes": [
                            "semantic_role:retained_intention",
                            "semantic_role:embedded_turn",
                            "operator:wish",
                        ],
                    },
                    "noun_phrase": "継続中の意向",
                    "visible_feature_names": ["nucleus_kind"],
                    "anchor_risk_rank": 98,
                    "binding_family": "reported_profile",
                },
                {
                    "profile_id": "embedded_shift_constraint",
                    "match": {
                        "nucleus_kinds": ["constraint"],
                        "all_attribute_codes": [
                            "semantic_role:embedded_turn",
                            "operator:shift",
                            "operator:contrast",
                        ],
                    },
                    "noun_phrase": "以前とは異なる条件",
                    "visible_feature_names": ["nucleus_kind"],
                    "anchor_risk_rank": 98,
                    "binding_family": "relation_shift",
                },
                {
                    "profile_id": "self_denial_constraint",
                    "match": {
                        "nucleus_kinds": ["constraint"],
                        "polarities": ["negative"],
                        "all_attribute_codes": [
                            "operator:negation",
                            "semantic_role:initial_condition",
                            "source_claim:addressee.c1",
                        ],
                    },
                    "noun_phrase": "自分に向けられた否定的な見方",
                    "visible_feature_names": ["polarity", "nucleus_kind"],
                    "anchor_risk_rank": 100,
                    "binding_family": "reported_profile",
                },
                {
                    "profile_id": "self_denial_self_evaluation",
                    "match": {
                        "nucleus_kinds": ["self_evaluation"],
                        "polarities": ["negative"],
                        "all_attribute_codes": ["operator:negation"],
                        "any_attribute_codes": [
                            "semantic_role:initial_condition",
                            "source_claim:identity.c1",
                        ],
                    },
                    "noun_phrase": "自分への厳しい見方",
                    "visible_feature_names": ["polarity", "nucleus_kind"],
                    "anchor_risk_rank": 100,
                    "binding_family": "reported_profile",
                },
                {
                    "profile_id": "embedded_turn_coexistence",
                    "match": {
                        "nucleus_kinds": ["other_explicit"],
                        "all_attribute_codes": [
                            "semantic_role:embedded_turn",
                            "operator:coexistence",
                        ],
                    },
                    "noun_phrase": "異なる面をともに含む考え",
                    "visible_feature_names": ["nucleus_kind"],
                    "anchor_risk_rank": 96,
                    "binding_family": "reported_profile",
                },
                {
                    "profile_id": "fear_constraint",
                    "match": {
                        "nucleus_kinds": ["constraint"],
                        "all_attribute_codes": ["detected_type:fear"],
                    },
                    "noun_phrase": "怖さを含む気がかり",
                    "visible_feature_names": ["nucleus_kind"],
                    "anchor_risk_rank": 94,
                    "binding_family": "reported_profile",
                },
                {
                    "profile_id": "continuation_value_uncertain",
                    "match": {
                        "nucleus_kinds": ["value"],
                        "polarities": ["negative"],
                        "all_attribute_codes": [
                            "operator:continuation",
                            "operator:negation",
                            "operator:uncertainty",
                        ],
                    },
                    "noun_phrase": "続けるかどうかを決め切らない見方",
                    "visible_feature_names": ["polarity", "nucleus_kind"],
                    "anchor_risk_rank": 92,
                    "binding_family": "reported_profile",
                },
                {
                    "profile_id": "self_evaluation_negative",
                    "match": {
                        "nucleus_kinds": ["self_evaluation"],
                        "polarities": ["negative"],
                    },
                    "noun_phrase": "自分についての見立て",
                    "visible_feature_names": ["nucleus_kind"],
                    "anchor_risk_rank": 90,
                    "binding_family": "reported_profile",
                },
                {
                    "profile_id": "self_evaluation_positive",
                    "match": {
                        "nucleus_kinds": ["self_evaluation"],
                        "polarities": ["positive"],
                    },
                    "noun_phrase": "自分との合い方への前向きな見立て",
                    "visible_feature_names": ["polarity", "nucleus_kind"],
                    "anchor_risk_rank": 90,
                    "binding_family": "reported_profile",
                },
                {
                    "profile_id": "self_evaluation_neutral",
                    "match": {"nucleus_kinds": ["self_evaluation"]},
                    "noun_phrase": "自分との合い方についての見立て",
                    "visible_feature_names": ["nucleus_kind"],
                    "anchor_risk_rank": 90,
                    "binding_family": "reported_profile",
                },
                {
                    "profile_id": "action_completed",
                    "match": {
                        "nucleus_kinds": ["action"],
                        "lifecycles": ["reported_completed"],
                    },
                    "noun_phrase": "完了済みの行動",
                    "visible_feature_names": [
                        "temporal_scope",
                        "modality",
                        "action_lifecycle",
                        "nucleus_kind",
                    ],
                    "anchor_risk_rank": 82,
                    "binding_family": "action_lifecycle",
                },
                {
                    "profile_id": "action_ongoing",
                    "match": {
                        "nucleus_kinds": ["action"],
                        "lifecycles": ["reported_ongoing"],
                    },
                    "noun_phrase": "継続中の行動",
                    "visible_feature_names": [
                        "temporal_scope",
                        "modality",
                        "action_lifecycle",
                        "nucleus_kind",
                    ],
                    "anchor_risk_rank": 82,
                    "binding_family": "action_lifecycle",
                },
                {
                    "profile_id": "action_not_completed",
                    "match": {
                        "nucleus_kinds": ["action"],
                        "lifecycles": ["reported_not_completed"],
                    },
                    "noun_phrase": "未完了の行動",
                    "visible_feature_names": [
                        "temporal_scope",
                        "modality",
                        "action_lifecycle",
                        "nucleus_kind",
                    ],
                    "anchor_risk_rank": 82,
                    "binding_family": "action_lifecycle",
                },
                {
                    "profile_id": "action_intended",
                    "match": {
                        "nucleus_kinds": ["action"],
                        "lifecycles": ["intended"],
                    },
                    "noun_phrase": "これからの予定",
                    "visible_feature_names": [
                        "temporal_scope",
                        "modality",
                        "action_lifecycle",
                        "nucleus_kind",
                    ],
                    "anchor_risk_rank": 82,
                    "binding_family": "action_lifecycle",
                },
                {
                    "profile_id": "constraint_possible",
                    "match": {
                        "nucleus_kinds": ["constraint"],
                        "modalities": ["possible", "unknown"],
                    },
                    "noun_phrase": "確定していない条件",
                    "visible_feature_names": ["nucleus_kind"],
                    "anchor_risk_rank": 86,
                    "binding_family": "reported_profile",
                },
                {
                    "profile_id": "constraint_reported_negative",
                    "match": {
                        "nucleus_kinds": ["constraint"],
                        "modalities": ["reported"],
                        "polarities": ["negative"],
                    },
                    "noun_phrase": "気がかりな条件",
                    "visible_feature_names": [
                        "modality",
                        "polarity",
                        "nucleus_kind",
                    ],
                    "anchor_risk_rank": 84,
                    "binding_family": "reported_profile",
                },
                {
                    "profile_id": "constraint_generic",
                    "match": {"nucleus_kinds": ["constraint"]},
                    "noun_phrase": "条件",
                    "visible_feature_names": ["nucleus_kind"],
                    "anchor_risk_rank": 86,
                    "binding_family": "reported_profile",
                },
                {
                    "profile_id": "reaction_negative_strong",
                    "match": {
                        "nucleus_kinds": ["reaction"],
                        "polarities": ["negative"],
                        "label_strengths": ["strong"],
                    },
                    "noun_phrase": "強い重さを伴う気持ち",
                    "visible_feature_names": [
                        "label_strength",
                        "polarity",
                        "nucleus_kind",
                    ],
                    "anchor_risk_rank": 48,
                    "binding_family": "reported_profile",
                },
                {
                    "profile_id": "reaction_negative_medium",
                    "match": {
                        "nucleus_kinds": ["reaction"],
                        "polarities": ["negative"],
                        "label_strengths": ["medium"],
                    },
                    "noun_phrase": "中ほどの重さを伴う気持ち",
                    "visible_feature_names": [
                        "label_strength",
                        "polarity",
                        "nucleus_kind",
                    ],
                    "anchor_risk_rank": 46,
                    "binding_family": "reported_profile",
                },
                {
                    "profile_id": "reaction_negative_weak",
                    "match": {
                        "nucleus_kinds": ["reaction"],
                        "polarities": ["negative"],
                        "label_strengths": ["weak"],
                    },
                    "noun_phrase": "かすかな重さを伴う気持ち",
                    "visible_feature_names": [
                        "label_strength",
                        "polarity",
                        "nucleus_kind",
                    ],
                    "anchor_risk_rank": 44,
                    "binding_family": "reported_profile",
                },
                {
                    "profile_id": "reaction_positive",
                    "match": {
                        "nucleus_kinds": ["reaction"],
                        "polarities": ["positive"],
                    },
                    "noun_phrase": "前向きさを含む気持ち",
                    "visible_feature_names": ["polarity", "nucleus_kind"],
                    "anchor_risk_rank": 42,
                    "binding_family": "reported_profile",
                },
                {
                    "profile_id": "event_negative",
                    "match": {
                        "nucleus_kinds": ["event"],
                        "polarities": ["negative"],
                    },
                    "noun_phrase": "負担を伴う出来事",
                    "visible_feature_names": ["polarity", "nucleus_kind"],
                    "anchor_risk_rank": 88,
                    "binding_family": "reported_profile",
                },
                {
                    "profile_id": "event_positive",
                    "match": {
                        "nucleus_kinds": ["event"],
                        "polarities": ["positive"],
                    },
                    "noun_phrase": "前向きな出来事",
                    "visible_feature_names": ["polarity", "nucleus_kind"],
                    "anchor_risk_rank": 88,
                    "binding_family": "reported_profile",
                },
                {
                    "profile_id": "event_generic",
                    "match": {"nucleus_kinds": ["event"]},
                    "noun_phrase": "出来事",
                    "visible_feature_names": ["nucleus_kind"],
                    "anchor_risk_rank": 88,
                    "binding_family": "reported_profile",
                },
                {
                    "profile_id": "state_negative",
                    "match": {
                        "nucleus_kinds": ["state"],
                        "polarities": ["negative"],
                    },
                    "noun_phrase": "負担を伴う状態",
                    "visible_feature_names": ["polarity", "nucleus_kind"],
                    "anchor_risk_rank": 88,
                    "binding_family": "reported_profile",
                },
                {
                    "profile_id": "state_positive",
                    "match": {
                        "nucleus_kinds": ["state"],
                        "polarities": ["positive"],
                    },
                    "noun_phrase": "前向きに示された状態",
                    "visible_feature_names": ["polarity", "nucleus_kind"],
                    "anchor_risk_rank": 88,
                    "binding_family": "reported_profile",
                },
                {
                    "profile_id": "state_generic",
                    "match": {"nucleus_kinds": ["state"]},
                    "noun_phrase": "状態",
                    "visible_feature_names": ["nucleus_kind"],
                    "anchor_risk_rank": 88,
                    "binding_family": "reported_profile",
                },
                {
                    "profile_id": "other_explicit_generic",
                    "match": {"nucleus_kinds": ["other_explicit"]},
                    "noun_phrase": "明示された内容",
                    "visible_feature_names": ["nucleus_kind"],
                    "anchor_risk_rank": 88,
                    "binding_family": "reported_profile",
                },
                {
                    "profile_id": "wish_generic",
                    "match": {"nucleus_kinds": ["wish"]},
                    "noun_phrase": "望んでいること",
                    "visible_feature_names": ["nucleus_kind"],
                    "anchor_risk_rank": 72,
                    "binding_family": "reported_profile",
                },
                {
                    "profile_id": "value_positive",
                    "match": {
                        "nucleus_kinds": ["value"],
                        "polarities": ["positive"],
                    },
                    "noun_phrase": "前向きに示された価値に関わる考え",
                    "visible_feature_names": ["polarity", "nucleus_kind"],
                    "anchor_risk_rank": 78,
                    "binding_family": "reported_profile",
                },
                {
                    "profile_id": "value_negative",
                    "match": {
                        "nucleus_kinds": ["value"],
                        "polarities": ["negative"],
                    },
                    "noun_phrase": "慎重に示された価値に関わる考え",
                    "visible_feature_names": ["polarity", "nucleus_kind"],
                    "anchor_risk_rank": 78,
                    "binding_family": "reported_profile",
                },
                {
                    "profile_id": "value_generic",
                    "match": {"nucleus_kinds": ["value"]},
                    "noun_phrase": "価値に関わる考え",
                    "visible_feature_names": ["nucleus_kind"],
                    "anchor_risk_rank": 78,
                    "binding_family": "reported_profile",
                },
                {
                    "profile_id": "change_generic",
                    "match": {"nucleus_kinds": ["change"]},
                    "noun_phrase": "変化",
                    "visible_feature_names": ["nucleus_kind"],
                    "anchor_risk_rank": 76,
                    "binding_family": "reported_profile",
                },
                {
                    "profile_id": "uncertainty_generic",
                    "match": {"nucleus_kinds": ["uncertainty"]},
                    "noun_phrase": "まだ決め切れない部分",
                    "visible_feature_names": ["nucleus_kind"],
                    "anchor_risk_rank": 80,
                    "binding_family": "reported_profile",
                },
                {
                    "profile_id": "conclusion_generic",
                    "match": {"nucleus_kinds": ["conclusion"]},
                    "noun_phrase": "結論",
                    "visible_feature_names": ["nucleus_kind"],
                    "anchor_risk_rank": 70,
                    "binding_family": "reported_profile",
                },
                {
                    "profile_id": "action_fallback",
                    "match": {
                        "nucleus_kinds": ["action"],
                        "lifecycles": ["not_applicable"],
                    },
                    "noun_phrase": "行動",
                    "visible_feature_names": ["nucleus_kind"],
                    "anchor_risk_rank": 84,
                    "binding_family": "action_lifecycle",
                },
                {
                    "profile_id": "reaction_fallback",
                    "match": {"nucleus_kinds": ["reaction"]},
                    "noun_phrase": "気持ち",
                    "visible_feature_names": ["nucleus_kind"],
                    "anchor_risk_rank": 50,
                    "binding_family": "reported_profile",
                },
            ],
        },
        "completed_sentence_bank": False,
        "random_synonym_selection": False,
        "source_anchor_open": "「",
        "source_anchor_close": "」",
        "maximum_source_anchor_scalars": 16,
        "observation_predicate": "が見えます",
        "coexisting_joiner": "と",
        "coexisting_predicate": "が、どちらもそのまま現れています",
        "local_anaphors": {
            "action": "その行動",
            "affect": "その感情",
            "proposition": "その思い",
        },
        "unknown_dimension_atoms": {
            "decision_state": "まだ決めていない部分",
            "post_decision_comparative_merit": "決定後の比べ方",
            "other_person_awareness": "相手からどう見えるか",
            "cause": "理由や背景",
            "referent": "それが指すもの",
            "future": "先の展開",
            "outcome": "結果",
            "relation": "二つの関係",
            "generic": "その範囲",
        },
        "unknown_predicate": "は、開いたままです",
        "relation_atoms": {
            "precedes": {
                "source_to_target": {
                    "endpoint_order": ["from", "to"],
                    "left": "の後に、",
                    "right": "が続いています",
                },
                "target_to_source": {
                    "endpoint_order": ["to", "from"],
                    "left": "の後に、",
                    "right": "が続いています",
                },
                "bidirectional": {
                    "endpoint_order": ["from", "to"],
                    "left": "と",
                    "right": "の間を行き来する流れがあります",
                },
            },
            "contrasts_with": {
                "source_to_target": {
                    "endpoint_order": ["from", "to"],
                    "left": "と",
                    "right": "は、異なる面として並んでいます",
                },
                "target_to_source": {
                    "endpoint_order": ["to", "from"],
                    "left": "と",
                    "right": "は、異なる面として並んでいます",
                },
                "bidirectional": {
                    "endpoint_order": ["from", "to"],
                    "left": "と",
                    "right": "は、違いを消さずに並んでいます",
                },
            },
            "coexists_with": {
                "source_to_target": {
                    "endpoint_order": ["from", "to"],
                    "left": "がある一方で、",
                    "right": "もあります",
                },
                "target_to_source": {
                    "endpoint_order": ["to", "from"],
                    "left": "がある一方で、",
                    "right": "もあります",
                },
                "bidirectional": {
                    "endpoint_order": ["from", "to"],
                    "left": "と",
                    "right": "は、どちらもそのままあります",
                },
            },
            "qualifies": {
                "source_to_target": {
                    "endpoint_order": ["from", "to"],
                    "left": "によって、",
                    "right": "の範囲が絞られています",
                },
                "target_to_source": {
                    "endpoint_order": ["to", "from"],
                    "left": "によって、",
                    "right": "の範囲が絞られています",
                },
                "bidirectional": {
                    "endpoint_order": ["from", "to"],
                    "left": "と",
                    "right": "が、互いの範囲を確かめ合っています",
                },
            },
            "supports_without_guarantee": {
                "source_to_target": {
                    "endpoint_order": ["from", "to"],
                    "left": "が",
                    "right": "を支えていますが、その先までは決めません",
                },
                "target_to_source": {
                    "endpoint_order": ["to", "from"],
                    "left": "が",
                    "right": "を支えていますが、その先までは決めません",
                },
                "bidirectional": {
                    "endpoint_order": ["from", "to"],
                    "left": "と",
                    "right": "が支え合っていますが、結果までは決めません",
                },
            },
        },
        "feature_tokens": {
            "temporal_scope": {
                "current_input": "",
                "reported_past": "過去からの",
                "intended_future": "先の時点に向けた",
                "atemporal": "時点を限らない",
                "unknown": "時点を決めない",
            },
            "source_field": {
                "memo": "考えの中の",
                "memo_action": "行動としての",
                "emotion_details": "詳しく選ばれた感情としての",
                "emotions": "選ばれた感情としての",
                "category": "分類に表れた",
                "mixed": "入力全体に表れた",
            },
            "semantic_role": {
                "antecedent": "先にある",
                "consequent": "その後に続く",
                "none": "",
            },
            "polarity": {
                "positive": "明るさを帯びた",
                "negative": "重さを帯びた",
                "mixed": "異なる向きをともに含む",
                "neutral": "",
            },
            "semantic_qualifier": {
                "source_semantic_role:concrete_action_evidence": "具体的な",
                "source_semantic_role:concrete_action": "はっきり示された",
                "source_semantic_role:contrast_before": "対照の前側にある",
                "source_semantic_role:contrast_after": "対照の後側にある",
                "source_semantic_role:embedded_turn": "折り返しを含む",
                "source_semantic_role:initial_condition": "前提となる",
                "source_semantic_role:retained_intention": "保たれている",
                "source_operator:constraint": "条件を含む",
                "source_operator:continuation": "続いている",
                "source_operator:shift": "移り変わりを含む",
                "source_operator:action": "実行に向けた",
                "source_operator:wish": "望みとして示された",
                "meaning_block_kind:current_expression": "今の表れとしての",
                "meaning_block_kind:constraint": "条件としての",
                "meaning_block_kind:action": "動きとして分けられた",
                "meaning_block_kind:wish": "望みとして分けられた",
                "none": "",
            },
            "modality": {
                "observed": "",
                "reported": "伝えられた",
                "intended": "これからに向けた",
                "possible": "可能性として示された",
                "unknown": "まだ確定しない",
            },
            "referent_scope": {
                "self": "自分についての",
                "other": "相手についての",
                "event": "出来事についての",
                "action": "行動についての",
                "state": "状態についての",
                "relation": "関係についての",
                "unknown": "対象を決めない",
            },
            "label_strength": {
                "strong": "強く",
                "medium": "中ほどの強さで",
                "weak": "かすかに",
                "none": "",
            },
            "action_lifecycle": {
                "not_applicable": "",
                "intended": "予定としての",
                "reported_ongoing": "継続中としての",
                "reported_not_completed": "未完了としての",
                "reported_completed": "完了済みとしての",
            },
            "nucleus_kind": {
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
            },
        },
    },
    "group_grammar": {
        "schema_version": (
            "cocolon.emlis.nls_v3.step11_group_grammar.rc0027.v1"
        ),
        "clause_separator": _GROUP_CLAUSE_SEPARATOR,
        "sentence_suffix": _GROUP_SENTENCE_SUFFIX,
        "grammatical_chunk_separator": _GROUP_SENTENCE_SUFFIX,
        "one_line_per_discourse_sentence_group": True,
        "split_outside_quotes_only": True,
        "clause_stems_exclude_sentence_suffix": True,
        "maximum_observation_clauses_per_sentence": 4,
        "maximum_visible_clauses_per_grammatical_sentence": 2,
        "maximum_grammatical_complexity_load": 4,
        "maximum_repeated_joiner_per_group": 2,
        "maximum_repeated_joiner_per_sentence": 2,
    },
    "obligation_fused_grammar": {
        "schema_version": (
            "cocolon.emlis.nls_v3.step11_obligation_fused_surface.legacy_rc0026.v1"
        ),
        "forward_emission": False,
        "literal_owner_policy": "legacy_exact_literal_regression_only",
        "reception_literal_policy": "legacy_zero",
        "reference_realization_policy": "legacy_registry_only",
        "relation_unit_policy": "legacy_completed_relation_forms",
        "unknown_unit_policy": "legacy_completed_unknown_tails",
        "shared_endpoint_policy": "legacy_local_anaphora_and_literal",
        "neutral_pair_policy": "legacy_thought_action_literal_pair",
        "forbidden_generated_fragments": [
            "〔", "〕", "前者", "後者", "記述内容", "、また、"
        ],
        "forbidden_generated_patterns": [r"[1-9][0-9]*つ目の"],
        "relation_forms": _build_fused_relation_forms(),
        "local_anaphors": {
            "action": ["その動き", "その行動"],
            "affect": ["その気持ち", "その感情"],
            "proposition": ["その思い", "その言葉"],
        },
        "neutral_pair_forms": [
            "{thought_literal}という思いと、{action_literal}という動きを、どちらもここにあるものとして受け取りました",
            "{thought_literal}と思っていることと、{action_literal}という行動とが、いずれも示されています",
        ],
        "standalone_forms": {
            "thought": [
                "{literal}と感じている今の位置を、そのまま見ています",
                "{literal}という思いが、今ここに示されています",
                "{literal}という言葉を、後ろの意味を足さず見ています",
            ],
            "action": [
                "{literal}という動きが、書かれた状態のまま示されています",
                "{literal}という行動を、完了か予定かを足さず見ています",
                "{literal}という具体的な動きが、ここに示されています",
            ],
            "emotion": [
                "{literal}が、選ばれた気持ちとしてここにあります",
                "{literal}を、今の感情の一つとして受け取りました",
                "{literal}という感情が、他の向きにまとめられず残っています",
            ],
            "category": [
                "{literal}が、今の話題として選ばれています",
                "{literal}という話題を、他の意味を足さず見ています",
                "{literal}についての話題が、ここにあります",
            ],
        },
        "mixed_emotion_forms": [
            "{first_literal}と{second_literal}という異なる気持ちが、片方にまとめられず併存しています",
            "{first_literal}と{second_literal}を、どちらも選ばれた感情として受け取りました",
            "{first_literal}と{second_literal}が、一つに絞られないまま同時にあります",
        ],
        "unknown_tails": {
            "cause": [
                "ただ、理由や背景まではまだ決められません",
                "ただ、なぜそうなのかは分からないままです",
            ],
            "referent": [
                "ただ、それが指すものは書かれた以上に特定しません",
                "ただ、何を示すのかは分からないまま残します",
            ],
            "other_person_awareness": [
                "ただ、相手にどう見えているかはまだ分かりません",
                "ただ、相手が実際にどう\u6349えるかまでは決めません",
            ],
            "decision_state": [
                "ただ、決定済みか未決定かはまだ定まっていません",
                "ただ、決定の状態は書かれた範囲を超えて補いません",
            ],
            "post_decision_comparative_merit": [
                "ただ、決めた後の比較上の良し悪しはまだ分かりません",
                "ただ、選ばなかった案との優劣はここでは確定しません",
            ],
            "future": [
                "ただ、この先どうなるかはまだ分かりません",
                "ただ、これからの展開までは決めません",
            ],
            "outcome": [
                "ただ、その結果がどうなるかはまだ分かりません",
                "ただ、動きの先の結果まではここで決めません",
            ],
            "relation": [
                "ただ、その関わりの先は書かれた以上に決めません",
                "ただ、その結びつきにはまだ分からない部分があります",
            ],
            "generic": [
                "ただ、まだ分からない部分はそのまま残します",
                "ただ、書かれていないことまではここで決めません",
            ],
        },
    },
    "mixed_emotion_compound_grammar": {
        "schema_version": (
            "cocolon.emlis.nls_v3.step11_mixed_emotion_surface.rc0026.v1"
        ),
        "adjacent_policy": "consecutive_reference_ordinals",
        "display_order": "ascending_reference_ordinal",
        "endpoint_role": "affect",
        "relation_type": "coexists_with",
        "relation_direction": "bidirectional",
        "adjacent_forms": [
            (
                "{first_literal}と{second_literal}が、"
                "どちらも選ばれた感情としてあります"
            ),
            (
                "選ばれた感情には{first_literal}と"
                "{second_literal}があります"
            ),
            (
                "{first_literal}と{second_literal}を、"
                "片方にまとめず受け取っています"
            ),
        ],
        "nonadjacent_relation_forms": [
            (
                "選ばれた感情には異なる向きがあり、"
                "どちらか一方にまとめず並んでいます"
            ),
            (
                "選ばれた感情の異なる向きを、"
                "片方にまとめず併存させています"
            ),
        ],
    },
    "endpoint_reference_grammar": {
        "schema_version": (
            "cocolon.emlis.nls_v3.step11_endpoint_reference_grammar.v2"
        ),
        "ordinal_pattern": _REFERENCE_ORDINAL_PATTERN,
        "minimum_ordinal": 1,
        "maximum_policy": "independently_recomputed_active_registry_size",
        "reference_token_template": _REFERENCE_TOKEN_TEMPLATE,
        "role_labels": dict(_ENDPOINT_ROLE_LABELS),
        "natural_introduction": {
            "forms": {
                "thought": {
                    "proposition": [
                        "{quoted_literal}という思いがあります",
                        "{quoted_literal}という言葉を受け取りました",
                    ],
                    "action": [
                        "{quoted_literal}という動きについての思いがあります",
                        "{quoted_literal}という行動への言葉を受け取りました",
                    ],
                    "affect": [
                        "{quoted_literal}という感情についての思いがあります",
                        "{quoted_literal}という気持ちへの言葉を受け取りました",
                    ],
                },
                "action": {
                    "action": [
                        "{quoted_literal}という行動があります",
                        "{quoted_literal}という動きを受け取りました",
                    ],
                    "proposition": [
                        "{quoted_literal}という言葉と行動が示されています",
                        "{quoted_literal}という動きへの言葉を受け取りました",
                    ],
                    "affect": [
                        "{quoted_literal}という感情を伴う行動記述があります",
                        "{quoted_literal}という気持ちの動きを行動欄から受け取りました",
                    ],
                },
                "emotion": {
                    "affect": [
                        "感情として{quoted_literal}が選ばれています",
                        "選ばれた感情には{quoted_literal}があります",
                    ],
                    "proposition": [
                        "感情とともに{quoted_literal}という言葉が示されています",
                        "{quoted_literal}という言葉が、気持ちとともにあります",
                    ],
                    "action": [
                        "気持ちとともに{quoted_literal}という動きが示されています",
                        "{quoted_literal}という動きを、気持ちの表現として受け取りました",
                    ],
                },
                "category": {
                    "proposition": [
                        "話題として{quoted_literal}が選ばれています",
                        "選ばれた話題は{quoted_literal}です",
                    ],
                    "action": [
                        "行動の話題として{quoted_literal}が選ばれています",
                        "選ばれた行動の話題は{quoted_literal}です",
                    ],
                    "affect": [
                        "感情の話題として{quoted_literal}が選ばれています",
                        "選ばれた感情の話題は{quoted_literal}です",
                    ],
                },
            },
            "literal_owner_policy": "exact_source_identity_once",
            "terminal_owned_by_group": True,
        },
        "relation_endpoint_policy": "typed_reference_only",
        "reference_before_use_required": True,
    },
    "fragment_policy": {
        "whole_text_max_chars": 72,
        "whole_text_requires_single_meaningful_sentence": True,
        "endpoint_max_chars": 42,
        "minimum_meaningful_chars": 2,
        "sentence_boundaries": ["。", "！", "？", "!", "?"],
        "long_text_roles": ["opening", "closing"],
        "fragment_must_be_contiguous_in_normalized_source": True,
        "ellipsis_is_never_stored_inside_source_fragment": True,
    },
    "source_slots": ["thought", "action", "emotion", "category"],
    "observation_forms": {
        "thought": [
            {"prefix": "", "suffix": "という思いが、ここにあるのですね。"},
            {"prefix": "", "suffix": "という気持ちを、まず受け取りました。"},
            {"prefix": "", "suffix": "という言葉が、今ここにあるのですね。"},
            {"prefix": "", "suffix": "という問いが、今ここにあるのですね。"},
            {"prefix": "", "suffix": "と問いかける気持ちを受け取りました。"},
        ],
        "action": [
            {"prefix": "", "suffix": "という行動についても受け取りました。"},
            {"prefix": "", "suffix": "という動きも、ここにあるのですね。"},
            {"prefix": "", "suffix": "という行動も見失わずにいます。"},
        ],
        "thought_action": [
            {"prefix": "", "middle": "という思いと、行動としての", "suffix": "が、どちらも書かれています。"},
            {"prefix": "思いには", "middle": "があり、行動として書かれた内容には", "suffix": "があります。"},
            {"prefix": "", "middle": "という言葉と、", "suffix": "という行動を、分けずに見ています。"},
        ],
        "mixed_emotion": [
            {
                "prefix": "選ばれた感情には",
                "middle": "と",
                "suffix": "が、どちらもあります。",
            },
            {
                "prefix": "感情の欄には",
                "middle": "と",
                "suffix": "が、重なったまま置かれています。",
            },
            {
                "prefix": "感情として選ばれているのは",
                "middle": "と",
                "suffix": "の二つです。",
            },
        ],
        "thought_transition": [
            {"prefix": "思いの冒頭に", "middle": "があり、終わりには", "suffix": "があります。"},
            {"prefix": "思いは", "middle": "から始まり、", "suffix": "へ続いています。"},
            {"prefix": "書かれた思いの最初は", "middle": "で、最後は", "suffix": "です。"},
        ],
        "action_transition": [
            {"prefix": "行動の記述は", "middle": "から始まり、終わりには", "suffix": "があります。"},
            {"prefix": "行動の記述の冒頭は", "middle": "で、最後は", "suffix": "です。"},
            {"prefix": "行動として書かれた範囲は", "middle": "から", "suffix": "へ続いています。"},
        ],
        "thought_action_transition": [
            {"prefix": "思いは", "middle": "から", "middle2": "へ続き、行動として", "suffix": "が書かれています。"},
            {"prefix": "思いの冒頭には", "middle": "、終わりには", "middle2": "があり、行動として", "suffix": "と書かれています。"},
            {"prefix": "", "middle": "から", "middle2": "までの思いと、", "suffix": "という行動があります。"},
        ],
        "thought_unknown": [
            {"prefix": "", "suffix": "という感覚がありますが、理由や背景はまだ決められません。"},
            {"prefix": "", "suffix": "という思いがあり、その理由は分からないままです。"},
            {"prefix": "", "suffix": "という言葉を、その背景まで決めずに見ています。"},
        ],
        "action_unknown": [
            {"prefix": "行動には", "suffix": "がありますが、その背景はまだ決められません。"},
            {"prefix": "実際の動きは", "suffix": "で、その理由は分からないままです。"},
            {"prefix": "", "suffix": "という行動を、その先まで決めずに見ています。"},
        ],
        "thought_action_unknown": [
            {"prefix": "", "middle": "という思いと、", "suffix": "という行動があり、その関わりは書かれた範囲を越えて決めません。"},
            {"prefix": "思いには", "middle": "があり、行動には", "suffix": "がありますが、その背景はまだ分かりません。"},
            {"prefix": "", "middle": "という言葉と", "suffix": "という動きを、その理由まで決めずに見ています。"},
        ],
        "thought_self_denial": [
            {"prefix": "", "suffix": "と自分を捉える言葉がありますが、それをあなた自身の事実とは決めません。"},
            {"prefix": "", "suffix": "という自己評価は、あなた全体を表す事実とは分けて見ます。"},
            {"prefix": "", "suffix": "という自分への言葉を、そのままあなたの事実にはしません。"},
        ],
        "action_self_denial": [
            {"prefix": "行動には", "suffix": "があります。その行動と、自分を否定する評価とは分けて受け取ります。"},
            {"prefix": "行動としては", "suffix": "と書かれており、自己評価だけでその記述を消しません。"},
            {"prefix": "", "suffix": "という行動は、自分への否定的な評価とは別に残っています。"},
        ],
        "thought_action_self_denial": [
            {"prefix": "", "middle": "という思いがある一方で、", "suffix": "という行動もあり、自己評価だけをあなた自身の事実とは決めません。"},
            {"prefix": "自分への言葉として", "middle": "があり、行動としては", "suffix": "とも書かれています。前者だけをあなた全体の事実にはしません。"},
            {"prefix": "", "middle": "という自己評価と、", "suffix": "という行動を分けて見ます。自己評価はあなた自身の確定した事実ではありません。"},
        ],
        "unknown_only": {
            "thought": [
                {"prefix": "", "suffix": "について、理由や背景はまだ分からないままです。"},
                {"prefix": "", "suffix": "という思いの背景は、ここでは決めません。"},
                {"prefix": "", "suffix": "から先の理由は、分からない部分として残します。"},
            ],
            "action": [
                {"prefix": "", "suffix": "という行動の背景は、まだ分からないままです。"},
                {"prefix": "", "suffix": "という動きの理由は、ここでは決めません。"},
                {"prefix": "", "suffix": "から先の結果は、まだ分からない部分として残します。"},
            ],
            "generic": [
                "まだ言葉になっていない部分は、分からないまま残します。",
                "書かれていない理由や背景は、ここでは決めません。",
                "この先の意味は、分からない部分として残します。",
            ],
        },
        "unknown_dimension": {
            "cause": [
                "書かれていない理由や原因は、ここでは決めません。",
                "その背景が何かは、分からないまま残します。",
                "理由については、書かれた範囲を越えて補いません。",
            ],
            "referent": [
                "その言葉が指す内容は、書かれた範囲では特定しません。",
                "何を示しているかは、分からないまま残します。",
                "示されていない対象を、ここで補いません。",
            ],
            "decision_state": [
                "決定済みか未決定かは、まだ定まっていません。",
                "決定の状態は、書かれた範囲を越えて補いません。",
                "まだ確定していない決定状態を、先回りして決めません。",
            ],
            "post_decision_comparative_merit": [
                "決定後に別の案がより良かったかは、まだ分かりません。",
                "決めた後の比較上の良し悪しは、ここでは確定しません。",
                "選ばなかった案との優劣は、書かれた範囲を越えて補いません。",
            ],
            "future": [
                "この先どうなるかは、まだ分からないままです。",
                "これからの展開は、ここでは決めません。",
                "先のことは、書かれた範囲を越えて補いません。",
            ],
            "outcome": [
                "その結果がどうなるかは、まだ決められません。",
                "行動の先の結果は、分からないまま残します。",
                "結果については、ここにない情報を補いません。",
            ],
            "relation": [
                "二つのことの関わりは、書かれた範囲を越えて決めません。",
                "その結びつきの先は、分からないまま残します。",
                "関係については、ここにない意味を補いません。",
            ],
            "generic": [
                "まだ分からない部分は、分からないまま残します。",
                "書かれていないことは、ここでは決めません。",
                "この先の意味を、書かれた範囲を越えて補いません。",
            ],
        },
        "unknown_bound": {
            "cause": [
                {"prefix": "", "suffix": "と書かれていますが、その理由はまだ分からないままです。"},
                {"prefix": "", "suffix": "について、その背景はまだ分かりません。"},
            ],
            "referent": [
                {"prefix": "", "suffix": "で示されている内容は、書かれた以上には特定しません。"},
                {"prefix": "", "suffix": "が何を指すのかは、まだ分からないままです。"},
            ],
            "other_person_awareness": [
                {"prefix": "", "suffix": "について、相手にどう見えているかは、まだ分かりません。"},
                {"prefix": "", "suffix": "と書かれていますが、相手が実際にどう捉えているかは、まだ決められません。"},
            ],
            "decision_state": [
                {"prefix": "", "suffix": "について、決定済みか未決定かはまだ定まっていません。"},
                {"prefix": "", "suffix": "で示された決定の状態は、書かれた以上には決めません。"},
            ],
            "post_decision_comparative_merit": [
                {"prefix": "", "suffix": "について、決定後の比較上の良し悪しはまだ分かりません。"},
                {"prefix": "", "suffix": "と別の案の優劣は、ここでは確定しません。"},
            ],
            "future": [
                {"prefix": "", "suffix": "の先がどうなるかは、まだ分かりません。"},
                {"prefix": "", "suffix": "から先の展開は、ここでは決めません。"},
            ],
            "outcome": [
                {"prefix": "", "suffix": "の結果がどうなるかは、まだ分かりません。"},
                {"prefix": "", "suffix": "の先の結果は、ここでは決めません。"},
            ],
            "relation": [
                {"prefix": "", "suffix": "から先の関わりは、書かれた以上には決めません。"},
                {"prefix": "", "suffix": "の関わりには、まだ分からない部分があります。"},
            ],
            "generic": [
                {"prefix": "", "suffix": "について、まだ分からない部分はそのまま残します。"},
                {"prefix": "", "suffix": "について、書かれていないことまでは決めません。"},
            ],
        },
        "unknown_anaphora": {
            "cause": [
                {"stem": "{target_ref}について、理由や原因は、書かれた以上には決めません。"},
                {"stem": "{target_ref}について、その背景は、まだ分からないままです。"},
            ],
            "referent": [
                {"stem": "{target_ref}について、その言葉が指す内容は、書かれた以上には特定しません。"},
                {"stem": "{target_ref}が何を示しているかは、まだ分からないままです。"},
            ],
            "referent_other": [
                {"stem": "{target_ref}について、誰にどう思われるかは、書かれた以上には決めません。"},
                {"stem": "{target_ref}を相手がどう受け取るかは、まだ分からないままです。"},
            ],
            "future": [
                {"stem": "{target_ref}の先がどうなるかは、まだ分かりません。"},
                {"stem": "{target_ref}から先の展開は、ここでは決めません。"},
            ],
            "decision_state": [
                {"stem": "{target_ref}について、その決定が済んでいるかは、まだ定まっていません。"},
                {"stem": "{target_ref}について、決定の状態は、書かれた以上には決めません。"},
            ],
            "post_decision_comparative_merit": [
                {"stem": "{target_ref}について、決めた後に別の案がより良かったかは、まだ分かりません。"},
                {"stem": "{target_ref}について、その決定と別の案の優劣は、ここでは確定しません。"},
            ],
            "outcome": [
                {"stem": "{target_ref}の結果がどうなるかは、まだ分かりません。"},
                {"stem": "{target_ref}の先の結果は、ここでは決めません。"},
            ],
            "relation": [
                {"stem": "{from_ref}と{to_ref}の関わりの先は、書かれた以上には決めません。"},
                {"stem": "{from_ref}と{to_ref}の関わりには、まだ分からない部分があります。"},
            ],
            "generic": [
                {"stem": "{target_ref}について、まだ分からない部分は、そのまま残します。"},
                {"stem": "{target_ref}について、書かれていないことまでは決めません。"},
            ],
        },
        "self_denial_only": [
            {"prefix": "", "suffix": "という自分への評価は、あなた自身の確定した事実とは分けて見ます。"},
            {"prefix": "", "suffix": "という自己評価を、そのままあなた全体の事実にはしません。"},
            {"prefix": "", "suffix": "と感じていることと、あなた自身の事実とは同じにしません。"},
        ],
        "self_denial_anaphora": [
            "その自己評価を、あなた自身の事実とは決めません。",
            "その自分への評価を、あなた全体の事実にはしません。",
            "ここにある自己評価と、あなた自身の事実とは分けて見ます。",
        ],
        "bounded_counter_anaphora": [
            "その自己評価だけで、あなた自身の全体は決まりません。",
            "その自分への評価を、あなた全体へ広げません。",
            "その評価と、あなた自身の全体とは同じものにしません。",
        ],
        "self_denial_bound": [
            {"prefix": "", "suffix": "という見方は、あなた自身の事実とは分けて受け取ります。"},
            {"prefix": "", "suffix": "という評価を、そのままあなた自身の事実にはしません。"},
            {"prefix": "", "suffix": "という自分への言葉だけで、あなた全体を決めません。"},
        ],
        "emotion": [
            {"prefix": "選ばれた感情には", "suffix": "があります。"},
            {"prefix": "感情として選ばれているのは", "suffix": "です。"},
            {"prefix": "今の感情の欄には", "suffix": "が置かれています。"},
        ],
        "category": [
            {"prefix": "", "suffix": "のこととして書かれています。"},
            {"prefix": "選ばれた話題は", "suffix": "です。"},
            {"prefix": "話題の欄では", "suffix": "が選ばれています。"},
        ],
    },
    "legacy_unknown_aliases": {
        "choice": {
            "forward_emission": False,
            "replacement_dimensions": [
                "decision_state",
                "post_decision_comparative_merit",
            ],
        },
    },
    "relation_forms": _build_reference_relation_forms(),
    "legacy_quoted_relation_forms_rc0018": {
        "candidate_version_id": "nls_v3_rc_0018",
        "forward_emission": False,
        "forms": _build_legacy_quoted_relation_forms(),
    },
    "reception_forms": {
        "typed_reference_grammar": {
            "schema_version": (
                "cocolon.emlis.nls_v3.step11_reception_typed_reference."
                "rc0022.v1"
            ),
            "reference_wrapper": "〔{endpoint_ref}〕",
            "parser_visible_delimiters": {
                "open": "〔",
                "close": "〕",
            },
            "literal_quotes_forbidden": True,
            "forbidden_literal_quote_tokens": ["『", "』", "「", "」"],
            "reference_before_reception_required": True,
            "generic_relation_only_forbidden": True,
            "content_forms": {
                "thought": {
                    "reported_content": [
                        "〔{thought_ref}〕の思いを",
                        "〔{thought_ref}〕として示された思いを",
                    ],
                },
                "action": {
                    "undetermined": [
                        "〔{action_ref}〕の行動記述を、完了か予定かを決めずに",
                    ],
                    "intended": [
                        "〔{action_ref}〕の予定を、実行済みとは決めずに",
                    ],
                    "reported_ongoing": [
                        "〔{action_ref}〕の続いている動きを",
                    ],
                    "reported_not_completed": [
                        "〔{action_ref}〕の未完了の動きを、済んだことにはせずに",
                    ],
                    "reported_completed": [
                        "〔{action_ref}〕の完了した動きを",
                    ],
                },
                "thought_action": {
                    "undetermined": [
                        "〔{thought_ref}〕の思いと〔{action_ref}〕の動きを、完了か予定かを決めずに",
                    ],
                    "intended": [
                        "〔{thought_ref}〕の思いと〔{action_ref}〕の予定を、実行済みとは決めずに",
                    ],
                    "reported_ongoing": [
                        "〔{thought_ref}〕の思いと〔{action_ref}〕の続いている動きを",
                    ],
                    "reported_not_completed": [
                        "〔{thought_ref}〕の思いと〔{action_ref}〕の未完了の動きを、済んだことにはせずに",
                    ],
                    "reported_completed": [
                        "〔{thought_ref}〕の思いと〔{action_ref}〕の完了した動きを",
                    ],
                },
                "relation": {
                    "status_neutral": [
                        "〔{from_ref}〕から〔{to_ref}〕への関わりを",
                    ],
                    "undetermined": [
                        "〔{from_ref}〕から〔{to_ref}〕への関わりを、行動の状態を足さずに",
                    ],
                    "intended": [
                        "〔{from_ref}〕から〔{to_ref}〕への関わりを、予定を完了とはせずに",
                    ],
                    "reported_ongoing": [
                        "〔{from_ref}〕から〔{to_ref}〕への続いている関わりを",
                    ],
                    "reported_not_completed": [
                        "〔{from_ref}〕から〔{to_ref}〕への関わりを、未完了の動きを済んだことにはせずに",
                    ],
                    "reported_completed": [
                        "〔{from_ref}〕から〔{to_ref}〕への完了した関わりを",
                    ],
                },
                "relation_action": {
                    "status_neutral": [
                        "〔{from_ref}〕から〔{to_ref}〕への関わりと、具体的な行動である〔{action_ref}〕を",
                    ],
                    "undetermined": [
                        "〔{from_ref}〕から〔{to_ref}〕への関わりと〔{action_ref}〕の動きを、完了か予定かを決めずに",
                    ],
                    "intended": [
                        "〔{from_ref}〕から〔{to_ref}〕への関わりと〔{action_ref}〕の予定を、完了とはせずに",
                    ],
                    "reported_ongoing": [
                        "〔{from_ref}〕から〔{to_ref}〕への関わりと〔{action_ref}〕の続いている動きを",
                    ],
                    "reported_not_completed": [
                        "〔{from_ref}〕から〔{to_ref}〕への関わりと〔{action_ref}〕の未完了の動きを、済んだことにはせずに",
                    ],
                    "reported_completed": [
                        "〔{from_ref}〕から〔{to_ref}〕への関わりと〔{action_ref}〕の完了した動きを",
                    ],
                },
            },
            "optional_concrete_action_support": {
                "allowed_primary_scopes": ["thought", "relation"],
                "support_endpoint_role": "action",
                "forms": {
                    "thought": [
                        "〔{thought_ref}〕の思いと、具体的な行動である〔{support_action_ref}〕を",
                    ],
                    "relation": [
                        "〔{from_ref}〕から〔{to_ref}〕への関わりと、具体的な行動である〔{support_action_ref}〕を",
                    ],
                },
            },
        },
        "sentence_templates": [
            "{content}{predicate}",
            "ここでは、{content}{predicate}",
            "今は、{content}{predicate}",
        ],
        "content_forms": {
            "thought": {
                "reported_content": [
                    "{first}という思いを",
                    "{first}と書かれた思いを",
                ],
            },
            "action": {
                "undetermined": [
                    "{first}という行動の記述を、実行済みかどうかを足さずに",
                    "{first}と書かれた動きを、完了か予定かを決めずに",
                ],
                "intended": [
                    "{first}というこれからの意図を、実行済みとは決めずに",
                    "{first}と書かれた予定を、まだ完了した動きとはせずに",
                ],
                "reported_ongoing": [
                    "{first}という続いている動きを",
                    "{first}と書かれた継続中の行動を",
                ],
                "reported_not_completed": [
                    "{first}という、まだ完了していない行動の記述を",
                    "{first}と書かれた未完了の動きを、済んだことにはせずに",
                ],
                "reported_completed": [
                    "{first}という完了の報告を",
                    "{first}と書かれた、終えた動きを",
                ],
            },
            "thought_action": {
                "undetermined": [
                    "{first}という思いと、{second}という行動の記述を、実行済みかどうかを足さずに",
                    "{first}と書かれた思いと、{second}と書かれた動きを、完了か予定かを決めずに",
                ],
                "intended": [
                    "{first}という思いと、{second}というこれからの意図を、実行済みとは決めずに",
                    "{first}と書かれた思いと、{second}と書かれた予定を、まだ完了した動きとはせずに",
                ],
                "reported_ongoing": [
                    "{first}という思いと、{second}という続いている動きを",
                    "{first}と書かれた思いと、{second}と書かれた継続中の行動を",
                ],
                "reported_not_completed": [
                    "{first}という思いと、{second}という、まだ完了していない行動の記述を",
                    "{first}と書かれた思いと、{second}と書かれた未完了の動きを、済んだことにはせずに",
                ],
                "reported_completed": [
                    "{first}という思いと、{second}という完了の報告を",
                    "{first}と書かれた思いと、{second}と書かれた、終えた動きを",
                ],
            },
            "relation": {
                "status_neutral": [
                    "{first}と{second}という二つの記述の関わりを",
                    "{first}と{second}の間に書かれたつながりを",
                ],
                "undetermined": [
                    "{first}と{second}という二つの記述の関わりを、行動が完了か予定かを決めずに",
                    "{first}と{second}の間に書かれたつながりを、行動の状態を足さずに",
                ],
                "intended": [
                    "{first}と{second}という二つの記述の関わりを、行動を実行済みとは決めずに",
                    "{first}と{second}の間に書かれたつながりを、予定として書かれた動きをまだ完了とはせずに",
                ],
                "reported_ongoing": [
                    "{first}と{second}という二つの記述の関わりを、続いている動きを含むものとして",
                    "{first}と{second}の間に書かれたつながりを、継続中の行動を含む記述として",
                ],
                "reported_not_completed": [
                    "{first}と{second}という二つの記述の関わりを、行動を済んだことにはせずに",
                    "{first}と{second}の間に書かれたつながりを、未完了の動きを含むものとして",
                ],
                "reported_completed": [
                    "{first}と{second}という二つの記述の関わりを、完了の報告を含むものとして",
                    "{first}と{second}の間に書かれたつながりを、終えた動きを含む記述として",
                ],
            },
        },
        "anaphoric_content_forms": {
            "thought": {
                "reported_content": [
                    "そこで示された思いを",
                    "今ここにあるその気持ちを",
                ],
            },
            "action": {
                "undetermined": [
                    "その行動を、完了か予定かは決めず、",
                    "その動きを、済んだことかこれからかを足さずに",
                ],
                "intended": [
                    "これから行うその予定を、まだ完了とはせず、",
                    "そのこれからの意図を、まだ完了した動きとはせずに",
                ],
                "reported_ongoing": [
                    "今も続いているその行動を",
                    "その継続中の動きを",
                ],
                "reported_not_completed": [
                    "まだ終えていないその行動を",
                    "まだ終えていないその動きを、完了とはせずに",
                ],
                "reported_completed": [
                    "すでに行ったその行動を",
                    "その終えた動きを",
                ],
            },
            "thought_action": {
                "undetermined": [
                    "そこで示された思いと行動を、状態は決めつけず、",
                    "そこにある思いと動きを、状態を決めつけずに",
                ],
                "intended": [
                    "そこで示された思いと予定を、まだ完了とはせず、",
                    "その気持ちと予定を、まだ完了した動きとはせずに",
                ],
                "reported_ongoing": [
                    "そこで示された思いと、今も続いている行動を",
                    "その気持ちと継続中の動きを",
                ],
                "reported_not_completed": [
                    "そこで示された思いと、まだ終えていない行動を",
                    "その気持ちとまだ終えていない動きを、完了とはせずに",
                ],
                "reported_completed": [
                    "そこで示された思いと、すでに行った行動を",
                    "その気持ちと終えた動きを",
                ],
            },
            "relation": {
                "status_neutral": [
                    "そこで見えた二つのつながりを",
                    "そのつながりを",
                ],
                "undetermined": [
                    "そこで見えたつながりを、行動の状態は決めず、",
                    "そのつながりを、完了か予定かを決めずに",
                ],
                "intended": [
                    "そこで見えたつながりを、予定はまだ完了とはせず、",
                    "そのつながりを、これからの動きを完了とはせずに",
                ],
                "reported_ongoing": [
                    "今も続いているそのつながりを",
                    "継続中の動きを含むそのつながりを",
                ],
                "reported_not_completed": [
                    "まだ終えていない動きを含むそのつながりを",
                    "そのつながりを、まだ終えていない動きを完了とはせずに",
                ],
                "reported_completed": [
                    "すでに行った動きを含むそのつながりを",
                    "終えた行動を含むそのつながりを",
                ],
            },
            "relation_action": {
                "status_neutral": [
                    "そこで見えたつながりと行動を",
                    "そのつながりと具体的な行動を",
                ],
                "undetermined": [
                    "そこで見えたつながりと行動を、状態は決めず、",
                    "そのつながりと行動を、状態を足さずに",
                ],
                "intended": [
                    "そこで見えたつながりと予定を、まだ完了とはせず、",
                    "そのつながりとこれからの動きを、完了とはせずに",
                ],
                "reported_ongoing": [
                    "そこで見えたつながりと、今も続いている行動を",
                    "そのつながりと継続中の行動を",
                ],
                "reported_not_completed": [
                    "そこで見えたつながりと、まだ終えていない行動を",
                    "そのつながりとまだ終えていない行動を、完了とはせずに",
                ],
                "reported_completed": [
                    "そこで見えたつながりと、すでに行った行動を",
                    "そのつながりと終えた行動を",
                ],
            },
        },
        "act_predicates": {
            "hold_in_attention": [
                "見失わないよう受け止めています。",
                "見失わずにいます。",
                "注意深く見ています。",
            ],
            "do_not_dismiss": [
                "小さく片づけずに受け止めています。",
                "小さく片づけないまま受け止めています。",
                "記述として残したまま見ています。",
            ],
            "receive_without_deciding": [
                "一つに決めつけず受け止めています。",
                "背景まで決めつけずに受け止めています。",
                "先回りして結論づけずに見ています。",
            ],
            "honor_concrete_action": [
                "そのまま尊重して受け止めています。",
                "具体的に受け止めています。",
                "記述にないことを足さずに受け取っています。",
            ],
            "stay_with_mixed_meaning": [
                "どちらか一方に寄せず受け止めています。",
                "どれか一つの向きに絞らずに見ています。",
                "重なったまま受け止めています。",
            ],
        },
    },
    "observation_form_indices": {
        "thought": {
            "default": [0, 1, 2],
            "question": [3, 4],
        },
    },
    "relation_types": list(_RELATION_TYPES),
    "relation_directions": list(_RELATION_DIRECTIONS),
    "relation_endpoint_roles": list(_ENDPOINT_ROLES),
    "reception_acts": [
        "hold_in_attention",
        "do_not_dismiss",
        "receive_without_deciding",
        "honor_concrete_action",
        "stay_with_mixed_meaning",
    ],
    "forbidden_surface_claim_fragments": [
        "あなたの性格は",
        "病気です",
        "障害です",
        "必ずうまくいく",
        "原因は明らか",
        "に違いありません",
    ],
    "body_free": True,
}


# Exact historical rc0022 catalog commitment; retained for frozen evidence.
FROZEN_RC0022_STEP11_SURFACE_CATALOG_SHA256 = (
    "68d524e3da5949974c5f7985fb27592b948a246d91a0a25704c7cdde7ac75cee"
)
FROZEN_RC0023_STEP11_SURFACE_CATALOG_SHA256 = (
    "96305ca538159f9f19b1397d3ab0063285ed0b1d253643be19e7659024436d7a"
)
FROZEN_RC0024_STEP11_SURFACE_CATALOG_SHA256 = (
    "30b449931b3933531ad9716b6e73dc317d4145a38328f8ef2309ac2a0a7d92c6"
)
# Patched only after the declarative current artifact above is finalised.
FROZEN_STEP11_SURFACE_CATALOG_SHA256 = (
    "1beec18839ed77abd1e52b0a06eb60c5867223fd54183c251a8f0efbc37ccc08"
)
STEP11_SURFACE_CATALOG_SHA256 = artifact_sha256(STEP11_SURFACE_CATALOG)


def validate_step11_surface_catalog() -> tuple[str, ...]:
    issues: list[str] = []
    if (
        STEP11_SURFACE_CATALOG.get("schema_version")
        != "cocolon.emlis.nls_v3.step11_surface_catalog.v10"
    ):
        issues.append("STEP11_SURFACE_CATALOG_SCHEMA_INVALID")
    if STEP11_SURFACE_CATALOG.get("candidate_version_id") != "nls_v3_rc_0027":
        issues.append("STEP11_SURFACE_CATALOG_VERSION_INVALID")
    if STEP11_SURFACE_CATALOG.get("body_free") is not True:
        issues.append("STEP11_SURFACE_CATALOG_BODY_FREE_REQUIRED")
    lexical = STEP11_SURFACE_CATALOG.get("grounded_lexicalization", {})
    feature_order = [
        "semantic_role",
        "temporal_scope",
        "modality",
        "source_field",
        "referent_scope",
        "label_strength",
        "polarity",
        "semantic_qualifier",
        "action_lifecycle",
        "nucleus_kind",
    ]
    token_maps = lexical.get("feature_tokens", {}) if type(lexical) is dict else {}
    lifecycle_policy = (
        lexical.get("lifecycle_authority_policy", {})
        if type(lexical) is dict
        else {}
    )
    anchor_policy = (
        lexical.get("anchor_segment_policy", {})
        if type(lexical) is dict
        else {}
    )
    binding_families = (
        lexical.get("source_anchor_binding_families", {})
        if type(lexical) is dict
        else {}
    )
    profile_registry = (
        lexical.get("phrase_profile_registry", {})
        if type(lexical) is dict
        else {}
    )
    specificity_policy = (
        profile_registry.get("specificity_policy", {})
        if type(profile_registry) is dict
        else {}
    )
    residual_policy = (
        lexical.get("residual_information_loss_policy", {})
        if type(lexical) is dict
        else {}
    )
    profiles = (
        profile_registry.get("profiles", [])
        if type(profile_registry) is dict
        else []
    )

    def profile_singleton_values(row: Any) -> dict[str, str] | None:
        if type(row) is not dict or type(row.get("match")) is not dict:
            return None
        match = row["match"]
        singleton_values: dict[str, str] = {}
        direct_conditions = {
            "nucleus_kind": "nucleus_kinds",
            "modality": "modalities",
            "polarity": "polarities",
            "label_strength": "label_strengths",
            "action_lifecycle": "lifecycles",
        }
        for feature_name, condition_name in direct_conditions.items():
            values = match.get(condition_name)
            if type(values) is list and len(values) == 1:
                singleton_values[feature_name] = str(values[0])
        lifecycles = match.get("lifecycles")
        if type(lifecycles) is list and len(lifecycles) == 1:
            projection = lifecycle_policy.get("action_projection", {}).get(
                str(lifecycles[0])
            )
            if type(projection) is dict:
                modality = projection.get("modality")
                temporal_scope = projection.get("temporal_scope")
                if type(modality) is str:
                    singleton_values["modality"] = modality
                if type(temporal_scope) is str:
                    singleton_values["temporal_scope"] = temporal_scope
        visible_names = row.get("visible_feature_names")
        if not (
            type(visible_names) is list
            and visible_names
            and visible_names[-1] == "nucleus_kind"
            and set(str(value) for value in visible_names)
            <= set(singleton_values)
        ):
            return None
        return {
            str(name): singleton_values[str(name)]
            for name in visible_names
        }

    if (
        type(lexical) is not dict
        or lexical.get("schema_version")
        != "cocolon.emlis.nls_v3.step11_grounded_lexicalization.rc0027.v2"
        or lexical.get("feature_order") != feature_order
        or lexical.get("concatenation")
        != "ordered_attributive_atoms_without_separator"
        or lexical.get("forward_emission") is not True
        or lexical.get("source_realization_policy")
        != "one_grounded_feature_phrase_per_render_reachable_nucleus"
        or lexical.get("visible_source_anchor_policy")
        != "exactly_one_input_specific_anchor_or_fail_closed"
        or lexical.get("completed_sentence_bank") is not False
        or lexical.get("random_synonym_selection") is not False
        or lexical.get("source_anchor_open") != "「"
        or lexical.get("source_anchor_close") != "」"
        or "source_anchor_binding" in lexical
        or lexical.get("maximum_source_anchor_scalars") != 16
        or lifecycle_policy.get("authority_order")
        != [
            "exact_source_fragment_realization_status",
            "inventory_nucleus_semantics",
        ]
        or set(lifecycle_policy.get("action_projection", {}))
        != {
            "reported_completed",
            "reported_ongoing",
            "reported_not_completed",
            "intended",
        }
        or lifecycle_policy.get("multiple_exact_statuses") != "fail_closed"
        or lifecycle_policy.get(
            "observation_reception_lifecycle_equality_required"
        )
        is not True
        or anchor_policy.get("unicode_category_c_forbidden") is not True
        or anchor_policy.get("mechanical_prefix_truncation") is not False
        or anchor_policy.get("maximum_scalars") != 16
        or anchor_policy.get("accepted_segment_authorities")
        != [
            "trusted_fragment_entire_text",
            "complete_punctuation_delimited_run",
        ]
        or anchor_policy.get("long_run_subrange_authority") != "forbidden"
        or anchor_policy.get("whitespace_or_control_disposition")
        != "fail_closed"
        or "clause_boundary_tokens" in anchor_policy
        or "safe_subrange_terminal_suffixes" in anchor_policy
        or anchor_policy.get("unsafe_result") != "fail_closed"
        or binding_families
        != {
            "reported_profile": "に表れている",
            "action_lifecycle": "として示された",
            "relation_shift": "を起点にした",
        }
        or len(set(binding_families.values())) != 3
        or profile_registry.get("selection")
        != "first_exact_matching_profile_by_priority"
        or profile_registry.get("visible_feature_reconstruction")
        != "singleton_from_profile_match_or_lifecycle_projection"
        or profile_registry.get("completed_sentence_bank") is not False
        or specificity_policy.get(
            "unanchored_required_kind_only_generic"
        )
        != "fail_closed"
        or type(profiles) is not list
        or not profiles
        or len(
            {
                row.get("profile_id")
                for row in profiles
                if type(row) is dict
            }
        )
        != len(profiles)
        or len(
            {
                row.get("noun_phrase")
                for row in profiles
                if type(row) is dict
            }
        )
        != len(profiles)
        or any(
            type(row) is not dict
            or set(row)
            != {
                "profile_id",
                "match",
                "noun_phrase",
                "visible_feature_names",
                "anchor_risk_rank",
                "binding_family",
            }
            or type(row.get("profile_id")) is not str
            or type(row.get("match")) is not dict
            or type(row.get("noun_phrase")) is not str
            or not row.get("noun_phrase")
            or type(row.get("visible_feature_names")) is not list
            or not set(row.get("visible_feature_names", []))
            <= set(feature_order)
            or type(row.get("anchor_risk_rank")) is not int
            or row.get("binding_family") not in binding_families
            for row in profiles
        )
        or any(
            profile_singleton_values(row) is None
            for row in profiles
        )
        or type(
            specificity_policy.get("kind_only_generic_profile_ids")
        )
        is not list
        or len(
            set(specificity_policy.get("kind_only_generic_profile_ids", []))
        )
        != len(specificity_policy.get("kind_only_generic_profile_ids", []))
        or not set(
            specificity_policy.get("kind_only_generic_profile_ids", [])
        )
        <= {
            row.get("profile_id")
            for row in profiles
            if type(row) is dict
        }
        or {
            "action_completed_negative",
            "action_ongoing_negative",
            "action_not_completed_negative",
            "action_intended_negative",
        }
        & {
            row.get("profile_id")
            for row in profiles
            if type(row) is dict
        }
        or any(
            row.get("binding_family") == "relation_shift"
            and "operator:shift" not in set(
                row.get("match", {}).get("all_attribute_codes", [])
            )
            for row in profiles
            if type(row) is dict
        )
        or residual_policy.get("semantic_attribute_prefixes")
        != ["operator:", "semantic_role:", "unit_role:"]
        or residual_policy.get("concrete_action_attribute_code")
        != "semantic_role:concrete_action_evidence"
        or residual_policy.get("kind_implied_attribute_codes")
        != {
            "action": [
                "operator:action",
                "semantic_role:concrete_action_evidence",
            ]
        }
        or residual_policy.get("ordered_factors")
        != [
            "required_kind_only_generic",
            "required_relation_or_unknown_owner",
            "required_owner",
            "uncaptured_high_signal_attribute_count",
            "qualified_concrete_action_evidence",
            "uncaptured_semantic_attribute_count",
            "kind_only_generic",
            "static_anchor_risk_rank",
            "source_snapshot_order",
            "nucleus_id",
        ]
        or residual_policy.get("dynamic_score_in_visible_fingerprint")
        is not False
        or type(token_maps) is not dict
        or set(token_maps) != set(feature_order)
        or any(
            type(rows) is not dict
            or not rows
            or any(type(key) is not str or type(value) is not str for key, value in rows.items())
            for rows in token_maps.values()
        )
        or any(
            not token
            for token in token_maps.get("nucleus_kind", {}).values()
        )
        or any(
            len([token for token in rows.values() if token])
            != len(set(token for token in rows.values() if token))
            for rows in token_maps.values()
        )
    ):
        issues.append("STEP11_GROUNDED_LEXICALIZATION_CATALOG_INVALID")
    if (
        STEP11_SURFACE_CATALOG_SHA256
        != FROZEN_STEP11_SURFACE_CATALOG_SHA256
        or artifact_sha256(STEP11_SURFACE_CATALOG)
        != FROZEN_STEP11_SURFACE_CATALOG_SHA256
        or FROZEN_STEP11_SURFACE_CATALOG_SHA256 == "0" * 64
    ):
        issues.append("STEP11_SURFACE_CATALOG_HASH_DRIFT")
    forms = STEP11_SURFACE_CATALOG.get("observation_forms", {})
    if type(forms) is not dict:
        issues.append("STEP11_SURFACE_CATALOG_OBSERVATION_FORMS_INVALID")
        forms = {}

    unknown_owners = ("unknown_dimension", "unknown_bound", "unknown_anaphora")
    independent_unknowns = {
        "decision_state",
        "post_decision_comparative_merit",
    }
    for owner in unknown_owners:
        family = forms.get(owner, {})
        if (
            type(family) is not dict
            or "choice" in family
            or not independent_unknowns.issubset(family)
            or family.get("decision_state")
            == family.get("post_decision_comparative_merit")
        ):
            issues.append(
                "STEP11_SURFACE_CATALOG_UNKNOWN_DIMENSION_BOUNDARY_INVALID"
            )
            continue
        for dimension in independent_unknowns:
            rows = family[dimension]
            if owner == "unknown_bound":
                rows_invalid = (
                    type(rows) is not list
                    or len(rows) < 2
                    or any(
                        type(row) is not dict
                        or set(row) != {"prefix", "suffix"}
                        or type(row.get("prefix")) is not str
                        or type(row.get("suffix")) is not str
                        or not row["suffix"]
                        for row in rows
                    )
                )
            elif owner == "unknown_anaphora":
                rows_invalid = (
                    type(rows) is not list
                    or len(rows) < 2
                    or any(
                        type(row) is not dict
                        or set(row) != {"stem"}
                        or type(row.get("stem")) is not str
                        or row["stem"].count("{target_ref}") != 1
                        or "{from_ref}" in row["stem"]
                        or "{to_ref}" in row["stem"]
                        for row in rows
                    )
                )
            else:
                minimum_rows = 3 if owner == "unknown_dimension" else 2
                rows_invalid = (
                    type(rows) is not list
                    or len(rows) < minimum_rows
                    or any(type(row) is not str or not row for row in rows)
                )
            if rows_invalid:
                issues.append(
                    "STEP11_SURFACE_CATALOG_UNKNOWN_DIMENSION_BOUNDARY_INVALID"
                )
    if STEP11_SURFACE_CATALOG.get("legacy_unknown_aliases") != {
        "choice": {
            "forward_emission": False,
            "replacement_dimensions": [
                "decision_state",
                "post_decision_comparative_merit",
            ],
        },
    }:
        issues.append("STEP11_SURFACE_CATALOG_LEGACY_CHOICE_ALIAS_INVALID")

    mixed_emotion_rows = forms.get("mixed_emotion", [])
    if (
        type(mixed_emotion_rows) is not list
        or len(mixed_emotion_rows) < 3
        or any(
            type(row) is not dict
            or set(row) != {"prefix", "middle", "suffix"}
            or any(type(row[key]) is not str or not row[key] for key in row)
            or not row["suffix"].endswith("。")
            for row in mixed_emotion_rows
        )
    ):
        issues.append("STEP11_SURFACE_CATALOG_MIXED_EMOTION_INVALID")

    unknown_bound_forms = forms.get("unknown_bound", {})
    if type(unknown_bound_forms) is not dict:
        unknown_bound_forms = {}
    unknown_anaphora_forms = forms.get("unknown_anaphora", {})
    if type(unknown_anaphora_forms) is not dict:
        unknown_anaphora_forms = {}
    for dimension, rows in unknown_anaphora_forms.items():
        if type(rows) is not list or len(rows) < 2:
            issues.append(
                "STEP11_SURFACE_CATALOG_UNKNOWN_TARGET_REFERENCE_INVALID"
            )
            continue
        expected = (
            (0, 1, 1) if dimension == "relation" else (1, 0, 0)
        )
        if any(
            type(row) is not dict
            or set(row) != {"stem"}
            or type(row.get("stem")) is not str
            or (
                row["stem"].count("{target_ref}"),
                row["stem"].count("{from_ref}"),
                row["stem"].count("{to_ref}"),
            )
            != expected
            for row in rows
        ):
            issues.append(
                "STEP11_SURFACE_CATALOG_UNKNOWN_TARGET_REFERENCE_INVALID"
            )
    awareness_rows = unknown_bound_forms.get("other_person_awareness", [])
    if (
        type(awareness_rows) is not list
        or len(awareness_rows) < 2
        or any(
            type(row) is not dict
            or set(row) != {"prefix", "suffix"}
            or type(row["prefix"]) is not str
            or type(row["suffix"]) is not str
            or "相手" not in row["suffix"]
            or not any(token in row["suffix"] for token in ("見え", "捉え"))
            for row in awareness_rows
        )
        or "other_person_awareness" in unknown_anaphora_forms
    ):
        issues.append(
            "STEP11_SURFACE_CATALOG_OTHER_PERSON_AWARENESS_BOUND_INVALID"
        )

    def strings(value: Any) -> list[str]:
        if type(value) is str:
            return [value]
        if type(value) is list:
            return [item for child in value for item in strings(child)]
        if type(value) is dict:
            return [item for child in value.values() for item in strings(child)]
        return []

    group_grammar = STEP11_SURFACE_CATALOG.get("group_grammar", {})
    group_grammar_invalid = (
        type(group_grammar) is not dict
        or set(group_grammar)
        != {
            "schema_version",
            "clause_separator",
            "sentence_suffix",
            "grammatical_chunk_separator",
            "one_line_per_discourse_sentence_group",
            "split_outside_quotes_only",
            "clause_stems_exclude_sentence_suffix",
            "maximum_observation_clauses_per_sentence",
            "maximum_visible_clauses_per_grammatical_sentence",
            "maximum_grammatical_complexity_load",
            "maximum_repeated_joiner_per_group",
            "maximum_repeated_joiner_per_sentence",
        }
        or group_grammar.get("schema_version")
        != "cocolon.emlis.nls_v3.step11_group_grammar.rc0027.v1"
        or group_grammar.get("clause_separator")
        != _GROUP_CLAUSE_SEPARATOR
        or group_grammar.get("sentence_suffix") != _GROUP_SENTENCE_SUFFIX
        or group_grammar.get("grammatical_chunk_separator")
        != _GROUP_SENTENCE_SUFFIX
        or group_grammar.get("one_line_per_discourse_sentence_group")
        is not True
        or group_grammar.get("split_outside_quotes_only") is not True
        or group_grammar.get("clause_stems_exclude_sentence_suffix")
        is not True
        or group_grammar.get("maximum_observation_clauses_per_sentence") != 4
        or group_grammar.get(
            "maximum_visible_clauses_per_grammatical_sentence"
        )
        != 2
        or group_grammar.get("maximum_grammatical_complexity_load") != 4
        or group_grammar.get("maximum_repeated_joiner_per_group") != 2
        or group_grammar.get("maximum_repeated_joiner_per_sentence") != 2
        or any(
            type(group_grammar.get(key)) is not str
            or not group_grammar[key]
            or "\n" in group_grammar[key]
            for key in (
                "clause_separator",
                "sentence_suffix",
                "grammatical_chunk_separator",
            )
        )
        or group_grammar.get("clause_separator")
        == group_grammar.get("sentence_suffix")
    )
    if group_grammar_invalid:
        issues.append("STEP11_SURFACE_CATALOG_GROUP_GRAMMAR_INVALID")

    compound = STEP11_SURFACE_CATALOG.get(
        "mixed_emotion_compound_grammar", {}
    )
    compound_placeholders = ("{first_literal}", "{second_literal}")
    if (
        type(compound) is not dict
        or set(compound)
        != {
            "schema_version",
            "adjacent_policy",
            "display_order",
            "endpoint_role",
            "relation_type",
            "relation_direction",
            "adjacent_forms",
            "nonadjacent_relation_forms",
        }
        or compound.get("schema_version")
        != "cocolon.emlis.nls_v3.step11_mixed_emotion_surface.rc0026.v1"
        or compound.get("adjacent_policy")
        != "consecutive_reference_ordinals"
        or compound.get("display_order")
        != "ascending_reference_ordinal"
        or compound.get("endpoint_role") != "affect"
        or compound.get("relation_type") != "coexists_with"
        or compound.get("relation_direction") != "bidirectional"
        or type(compound.get("adjacent_forms")) is not list
        or len(compound.get("adjacent_forms", [])) < 3
        or any(
            type(row) is not str
            or not row
            or any(row.count(token) != 1 for token in compound_placeholders)
            or any(
                forbidden in row
                for forbidden in (
                    "{positive_ref}",
                    "{negative_ref}",
                    "{first_ref}",
                    "{second_ref}",
                )
            )
            or row.endswith(_GROUP_SENTENCE_SUFFIX)
            or _GROUP_CLAUSE_SEPARATOR in row
            for row in compound.get("adjacent_forms", [])
        )
        or type(compound.get("nonadjacent_relation_forms")) is not list
        or len(compound.get("nonadjacent_relation_forms", [])) < 2
        or any(
            type(row) is not str
            or not row
            or "{" in row
            or "}" in row
            or row.endswith(_GROUP_SENTENCE_SUFFIX)
            or _GROUP_CLAUSE_SEPARATOR in row
            for row in compound.get("nonadjacent_relation_forms", [])
        )
    ):
        issues.append(
            "STEP11_SURFACE_CATALOG_MIXED_EMOTION_COMPOUND_INVALID"
        )

    reference_grammar = STEP11_SURFACE_CATALOG.get(
        "endpoint_reference_grammar", {}
    )
    natural_introduction = (
        reference_grammar.get("natural_introduction", {})
        if type(reference_grammar) is dict
        else {}
    )
    role_labels = (
        reference_grammar.get("role_labels", {})
        if type(reference_grammar) is dict
        else {}
    )
    introduction_forms = (
        natural_introduction.get("forms", {})
        if type(natural_introduction) is dict
        else {}
    )
    reference_template = (
        reference_grammar.get("reference_token_template")
        if type(reference_grammar) is dict
        else None
    )
    reference_grammar_invalid = (
        type(reference_grammar) is not dict
        or set(reference_grammar)
        != {
            "schema_version",
            "ordinal_pattern",
            "minimum_ordinal",
            "maximum_policy",
            "reference_token_template",
            "role_labels",
            "natural_introduction",
            "relation_endpoint_policy",
            "reference_before_use_required",
        }
        or reference_grammar.get("schema_version")
        != "cocolon.emlis.nls_v3.step11_endpoint_reference_grammar.v2"
        or reference_grammar.get("ordinal_pattern")
        != _REFERENCE_ORDINAL_PATTERN
        or reference_grammar.get("minimum_ordinal") != 1
        or reference_grammar.get("maximum_policy")
        != "independently_recomputed_active_registry_size"
        or reference_template != _REFERENCE_TOKEN_TEMPLATE
        or type(role_labels) is not dict
        or role_labels != _ENDPOINT_ROLE_LABELS
        or len(set(role_labels.values())) != len(_ENDPOINT_ROLES)
        or type(natural_introduction) is not dict
        or set(natural_introduction)
        != {
            "forms",
            "literal_owner_policy",
            "terminal_owned_by_group",
        }
        or type(introduction_forms) is not dict
        or set(introduction_forms) != set(STEP11_SURFACE_CATALOG["source_slots"])
        or any(
            type(by_role) is not dict
            or set(by_role) != set(_ENDPOINT_ROLES)
            or any(
                type(stems) is not list
                or len(stems) < 2
                or any(
                    type(stem) is not str
                    or not stem
                    or stem.count("{quoted_literal}") != 1
                    or any(
                        placeholder in stem
                        for placeholder in (
                            "{reference}",
                            "{from_ref}",
                            "{to_ref}",
                            "{ordinal}",
                        )
                    )
                    or stem.endswith(_GROUP_SENTENCE_SUFFIX)
                    for stem in stems
                )
                for stems in by_role.values()
            )
            for by_role in introduction_forms.values()
        )
        or natural_introduction.get("literal_owner_policy")
        != "exact_source_identity_once"
        or natural_introduction.get("terminal_owned_by_group") is not True
        or reference_grammar.get("relation_endpoint_policy")
        != "typed_reference_only"
        or reference_grammar.get("reference_before_use_required") is not True
    )
    if not reference_grammar_invalid:
        introduction_skeletons = tuple(
            stem
            for by_role in introduction_forms.values()
            for stems in by_role.values()
            for stem in stems
        )
        try:
            samples = tuple(
                reference_template.format(
                    ordinal="1",
                    role_label=role_labels[role],
                )
                for role in _ENDPOINT_ROLES
            )
        except (KeyError, ValueError):
            reference_grammar_invalid = True
        else:
            if (
                len(samples) != len(set(samples))
                or len(introduction_skeletons)
                != len(set(introduction_skeletons))
                or any(
                    not sample
                    or "{" in sample
                    or "}" in sample
                    or _GROUP_CLAUSE_SEPARATOR in sample
                    for sample in samples
                )
            ):
                reference_grammar_invalid = True
    if reference_grammar_invalid:
        issues.append(
            "STEP11_SURFACE_CATALOG_ENDPOINT_REFERENCE_GRAMMAR_INVALID"
        )

    legacy_relations = STEP11_SURFACE_CATALOG.get(
        "legacy_quoted_relation_forms_rc0018", {}
    )
    if (
        type(legacy_relations) is not dict
        or set(legacy_relations)
        != {"candidate_version_id", "forward_emission", "forms"}
        or legacy_relations.get("candidate_version_id") != "nls_v3_rc_0018"
        or legacy_relations.get("forward_emission") is not False
        or type(legacy_relations.get("forms")) is not dict
    ):
        issues.append("STEP11_SURFACE_CATALOG_LEGACY_RELATION_OWNER_INVALID")

    if any(
        key in STEP11_SURFACE_CATALOG
        for key in ("relation_chain_forms", "relation_context_forms")
    ):
        issues.append("STEP11_SURFACE_CATALOG_OPEN_RELATION_FORMS_FORBIDDEN")

    if STEP11_SURFACE_CATALOG.get("relation_types") != list(_RELATION_TYPES):
        issues.append("STEP11_SURFACE_CATALOG_RELATION_TYPES_INVALID")
    if STEP11_SURFACE_CATALOG.get("relation_directions") != list(
        _RELATION_DIRECTIONS
    ):
        issues.append("STEP11_SURFACE_CATALOG_RELATION_DIRECTIONS_INVALID")
    if STEP11_SURFACE_CATALOG.get("relation_endpoint_roles") != list(
        _ENDPOINT_ROLES
    ):
        issues.append("STEP11_SURFACE_CATALOG_RELATION_ROLES_INVALID")

    relation_forms = STEP11_SURFACE_CATALOG.get("relation_forms", {})
    relation_lattice_invalid = (
        type(relation_forms) is not dict
        or set(relation_forms) != set(_RELATION_TYPES)
    )
    relation_skeletons: list[str] = []
    quote_tokens = tuple(
        token
        for pair in STEP11_SURFACE_CATALOG.get("layout", {}).get(
            "quote_pairs", []
        )
        if type(pair) is dict
        for token in (pair.get("open"), pair.get("close"))
        if type(token) is str and token
    )
    if not relation_lattice_invalid:
        for relation_type in _RELATION_TYPES:
            directions = relation_forms.get(relation_type, {})
            if (
                type(directions) is not dict
                or set(directions) != set(_RELATION_DIRECTIONS)
            ):
                relation_lattice_invalid = True
                continue
            minimum_variants = (
                3
                if relation_type
                in {"coexists_with", "supports_without_guarantee"}
                else 2
            )
            for direction in _RELATION_DIRECTIONS:
                from_roles = directions.get(direction, {})
                if (
                    type(from_roles) is not dict
                    or set(from_roles) != set(_ENDPOINT_ROLES)
                ):
                    relation_lattice_invalid = True
                    continue
                for from_role in _ENDPOINT_ROLES:
                    to_roles = from_roles.get(from_role, {})
                    if (
                        type(to_roles) is not dict
                        or set(to_roles) != set(_ENDPOINT_ROLES)
                    ):
                        relation_lattice_invalid = True
                        continue
                    for to_role in _ENDPOINT_ROLES:
                        rows = to_roles.get(to_role, [])
                        if (
                            type(rows) is not list
                            or len(rows) < minimum_variants
                        ):
                            relation_lattice_invalid = True
                            continue
                        for row in rows:
                            if (
                                type(row) is not dict
                                or set(row)
                                != {"stem", "endpoint_realization"}
                                or type(row.get("stem")) is not str
                                or not row["stem"]
                                or row["stem"].count("{from_ref}") != 1
                                or row["stem"].count("{to_ref}") != 1
                                or "{" in row["stem"].replace(
                                    "{from_ref}", ""
                                ).replace("{to_ref}", "")
                                or "}" in row["stem"].replace(
                                    "{from_ref}", ""
                                ).replace("{to_ref}", "")
                                or row.get("endpoint_realization")
                                != "typed_reference_only"
                                or row["stem"].endswith(
                                    _GROUP_SENTENCE_SUFFIX
                                )
                            ):
                                relation_lattice_invalid = True
                                continue
                            if (
                                any(token in row["stem"] for token in quote_tokens)
                                or "{quoted_literal}" in row["stem"]
                                or "{first}" in row["stem"]
                                or "{second}" in row["stem"]
                            ):
                                issues.append(
                                    "STEP11_SURFACE_CATALOG_RELATION_LITERAL_FORBIDDEN"
                                )
                            if _GROUP_CLAUSE_SEPARATOR in row["stem"]:
                                issues.append(
                                    "STEP11_SURFACE_CATALOG_GROUP_SEPARATOR_COLLISION"
                                )
                            try:
                                skeleton = row["stem"].format(
                                    from_ref=_REFERENCE_TOKEN_TEMPLATE.format(
                                        ordinal="1",
                                        role_label=_ENDPOINT_ROLE_LABELS[
                                            from_role
                                        ],
                                    ),
                                    to_ref=_REFERENCE_TOKEN_TEMPLATE.format(
                                        ordinal="2",
                                        role_label=_ENDPOINT_ROLE_LABELS[
                                            to_role
                                        ],
                                    ),
                                )
                            except (KeyError, ValueError):
                                relation_lattice_invalid = True
                                continue
                            relation_skeletons.append(skeleton)
                            if (
                                from_role == "action"
                                and any(
                                    unsafe in row["stem"]
                                    for unsafe in ("気持ち", "感覚", "感情")
                                )
                            ) or (
                                to_role == "action"
                                and any(
                                    unsafe in row["stem"]
                                    for unsafe in ("気持ち", "感覚", "感情")
                                )
                            ):
                                issues.append(
                                    "STEP11_SURFACE_CATALOG_ACTION_ROLE_LEXEME_UNSAFE"
                                )
    if relation_lattice_invalid:
        issues.append("STEP11_SURFACE_CATALOG_RELATION_LATTICE_INVALID")
    if len(relation_skeletons) != len(set(relation_skeletons)):
        issues.append("STEP11_SURFACE_CATALOG_RELATION_SKELETON_NOT_UNIQUE")

    reception = STEP11_SURFACE_CATALOG.get("reception_forms", {})
    if any(
        _GROUP_CLAUSE_SEPARATOR in text
        for text in strings([forms, reception, natural_introduction])
    ):
        issues.append("STEP11_SURFACE_CATALOG_GROUP_SEPARATOR_COLLISION")
    if (
        type(reception) is not dict
        or set(reception)
        != {
            "typed_reference_grammar",
            "sentence_templates",
            "content_forms",
            "anaphoric_content_forms",
            "act_predicates",
        }
        or type(reception.get("sentence_templates")) is not list
        or not reception.get("sentence_templates")
        or any(
            type(row) is not str
            or row.count("{content}") != 1
            or row.count("{predicate}") != 1
            for row in reception.get("sentence_templates", [])
        )
    ):
        issues.append("STEP11_SURFACE_CATALOG_RECEPTION_TEMPLATE_INVALID")
    content_forms = reception.get("content_forms", {})
    expected_statuses = {
        "thought": {"reported_content"},
        "action": {
            "undetermined",
            "intended",
            "reported_ongoing",
            "reported_not_completed",
            "reported_completed",
        },
        "thought_action": {
            "undetermined",
            "intended",
            "reported_ongoing",
            "reported_not_completed",
            "reported_completed",
        },
        "relation": {
            "status_neutral",
            "undetermined",
            "intended",
            "reported_ongoing",
            "reported_not_completed",
            "reported_completed",
        },
    }
    typed_reception = reception.get("typed_reference_grammar", {})
    typed_content_forms = (
        typed_reception.get("content_forms", {})
        if type(typed_reception) is dict
        else {}
    )
    typed_expected_statuses = {
        **expected_statuses,
        "relation_action": set(expected_statuses["relation"]),
    }
    typed_placeholders = {
        "thought": ("{thought_ref}",),
        "action": ("{action_ref}",),
        "thought_action": ("{thought_ref}", "{action_ref}"),
        "relation": ("{from_ref}", "{to_ref}"),
        "relation_action": (
            "{from_ref}",
            "{to_ref}",
            "{action_ref}",
        ),
    }
    typed_support = (
        typed_reception.get("optional_concrete_action_support", {})
        if type(typed_reception) is dict
        else {}
    )
    typed_support_forms = (
        typed_support.get("forms", {})
        if type(typed_support) is dict
        else {}
    )

    def typed_row_invalid(row: Any, placeholders: tuple[str, ...]) -> bool:
        if type(row) is not str or not row:
            return True
        remainder = row
        for placeholder in placeholders:
            if row.count(placeholder) != 1:
                return True
            if f"〔{placeholder}〕" not in row:
                return True
            remainder = remainder.replace(placeholder, "")
        return bool(
            "{" in remainder
            or "}" in remainder
            or _GROUP_CLAUSE_SEPARATOR in row
            or row.endswith(_GROUP_SENTENCE_SUFFIX)
            or any(token in row for token in ("『", "』", "「", "」"))
        )

    typed_reception_invalid = (
        type(typed_reception) is not dict
        or set(typed_reception)
        != {
            "schema_version",
            "reference_wrapper",
            "parser_visible_delimiters",
            "literal_quotes_forbidden",
            "forbidden_literal_quote_tokens",
            "reference_before_reception_required",
            "generic_relation_only_forbidden",
            "content_forms",
            "optional_concrete_action_support",
        }
        or typed_reception.get("schema_version")
        != (
            "cocolon.emlis.nls_v3.step11_reception_typed_reference."
            "rc0022.v1"
        )
        or typed_reception.get("reference_wrapper")
        != "〔{endpoint_ref}〕"
        or typed_reception.get("parser_visible_delimiters")
        != {"open": "〔", "close": "〕"}
        or typed_reception.get("literal_quotes_forbidden") is not True
        or typed_reception.get("forbidden_literal_quote_tokens")
        != ["『", "』", "「", "」"]
        or typed_reception.get("reference_before_reception_required")
        is not True
        or typed_reception.get("generic_relation_only_forbidden") is not True
        or type(typed_content_forms) is not dict
        or set(typed_content_forms) != set(typed_expected_statuses)
        or any(
            type(typed_content_forms.get(scope)) is not dict
            or set(typed_content_forms[scope]) != statuses
            or any(
                type(rows) is not list
                or not rows
                or any(
                    typed_row_invalid(row, typed_placeholders[scope])
                    for row in rows
                )
                for rows in typed_content_forms.get(scope, {}).values()
            )
            for scope, statuses in typed_expected_statuses.items()
        )
        or type(typed_support) is not dict
        or set(typed_support)
        != {"allowed_primary_scopes", "support_endpoint_role", "forms"}
        or typed_support.get("allowed_primary_scopes")
        != ["thought", "relation"]
        or typed_support.get("support_endpoint_role") != "action"
        or type(typed_support_forms) is not dict
        or set(typed_support_forms) != {"thought", "relation"}
        or any(
            type(rows) is not list
            or not rows
            or any(
                typed_row_invalid(
                    row,
                    (
                        ("{thought_ref}", "{support_action_ref}")
                        if scope == "thought"
                        else (
                            "{from_ref}",
                            "{to_ref}",
                            "{support_action_ref}",
                        )
                    ),
                )
                for row in rows
            )
            for scope, rows in typed_support_forms.items()
        )
    )
    if typed_reception_invalid:
        issues.append(
            "STEP11_SURFACE_CATALOG_RECEPTION_TYPED_REFERENCE_INVALID"
        )
    if (
        type(content_forms) is not dict
        or set(content_forms) != set(expected_statuses)
        or any(
            type(content_forms.get(scope)) is not dict
            or set(content_forms[scope]) != statuses
            or any(
                type(rows) is not list
                or not rows
                or any(
                    type(row) is not str
                    or row.count("{first}") != 1
                    or (
                        row.count("{second}") != 1
                        if scope in {"thought_action", "relation"}
                        else "{second}" in row
                    )
                    for row in rows
                )
                for rows in content_forms.get(scope, {}).values()
            )
            for scope, statuses in expected_statuses.items()
        )
    ):
        issues.append("STEP11_SURFACE_CATALOG_RECEPTION_CONTENT_INVALID")
    anaphoric_content_forms = reception.get("anaphoric_content_forms", {})
    anaphoric_expected_statuses = {
        **expected_statuses,
        "relation_action": set(expected_statuses["relation"]),
    }
    if (
        type(anaphoric_content_forms) is not dict
        or set(anaphoric_content_forms) != set(anaphoric_expected_statuses)
        or any(
            type(anaphoric_content_forms.get(scope)) is not dict
            or set(anaphoric_content_forms[scope]) != statuses
            or any(
                type(rows) is not list
                or not rows
                or any(
                    type(row) is not str
                    or not row.strip()
                    or any(
                        placeholder in row
                        for placeholder in (
                            "{first}",
                            "{second}",
                            "{content}",
                            "{predicate}",
                        )
                    )
                    for row in rows
                )
                for rows in anaphoric_content_forms.get(scope, {}).values()
            )
            for scope, statuses in anaphoric_expected_statuses.items()
        )
    ):
        issues.append(
            "STEP11_SURFACE_CATALOG_RECEPTION_ANAPHORA_INVALID"
        )
    act_predicates = reception.get("act_predicates", {})
    if (
        type(act_predicates) is not dict
        or set(act_predicates)
        != set(STEP11_SURFACE_CATALOG.get("reception_acts", []))
        or any(
            type(rows) is not list
            or len(rows) < 2
            or any(type(row) is not str or not row.endswith("。") for row in rows)
            for rows in act_predicates.values()
        )
    ):
        issues.append("STEP11_SURFACE_CATALOG_RECEPTION_ACT_INVALID")

    action_material = [
        forms.get(key, [])
        for key in (
            "action",
            "thought_action",
            "action_transition",
            "thought_action_transition",
            "action_unknown",
            "thought_action_unknown",
            "action_self_denial",
            "thought_action_self_denial",
        )
    ]
    action_material.extend(
        content_forms.get(scope, {})
        for scope in ("action", "thought_action")
    )
    action_material.extend(
        anaphoric_content_forms.get(scope, {})
        for scope in ("action", "thought_action")
    )
    if any(
        unsafe in text
        for text in strings(action_material)
        for unsafe in ("実際に動いた", "行ったこと", "実行した")
    ):
        issues.append("STEP11_SURFACE_CATALOG_ACTION_STATUS_UPCAST")
    if any(
        "感覚" in text
        for text in strings(forms.get("unknown_bound", {}).get("cause", []))
    ):
        issues.append("STEP11_SURFACE_CATALOG_CAUSE_ROLE_MISMATCH")

    fused = STEP11_SURFACE_CATALOG.get("obligation_fused_grammar", {})
    fused_relations = (
        fused.get("relation_forms", {}) if type(fused) is dict else {}
    )
    fused_invalid = (
        type(fused) is not dict
        or set(fused)
        != {
            "schema_version",
            "forward_emission",
            "literal_owner_policy",
            "reception_literal_policy",
            "reference_realization_policy",
            "relation_unit_policy",
            "unknown_unit_policy",
            "shared_endpoint_policy",
            "neutral_pair_policy",
            "forbidden_generated_fragments",
            "forbidden_generated_patterns",
            "relation_forms",
            "local_anaphors",
            "neutral_pair_forms",
            "standalone_forms",
            "mixed_emotion_forms",
            "unknown_tails",
        }
        or fused.get("schema_version")
        != "cocolon.emlis.nls_v3.step11_obligation_fused_surface.legacy_rc0026.v1"
        or fused.get("forward_emission") is not False
        or fused.get("literal_owner_policy")
        != "legacy_exact_literal_regression_only"
        or fused.get("reception_literal_policy") != "legacy_zero"
        or fused.get("reference_realization_policy")
        != "legacy_registry_only"
        or fused.get("relation_unit_policy")
        != "legacy_completed_relation_forms"
        or fused.get("unknown_unit_policy")
        != "legacy_completed_unknown_tails"
        or fused.get("shared_endpoint_policy")
        != "legacy_local_anaphora_and_literal"
        or fused.get("neutral_pair_policy")
        != "legacy_thought_action_literal_pair"
        or fused.get("forbidden_generated_fragments")
        != ["〔", "〕", "前者", "後者", "記述内容", "、また、"]
        or fused.get("forbidden_generated_patterns")
        != [r"[1-9][0-9]*つ目の"]
        or type(fused_relations) is not dict
        or set(fused_relations) != set(_RELATION_TYPES)
        or type(fused.get("local_anaphors")) is not dict
        or set(fused.get("local_anaphors", {})) != set(_ENDPOINT_ROLES)
        or any(
            type(rows) is not list
            or len(rows) < 2
            or any(type(row) is not str or not row for row in rows)
            for rows in fused.get("local_anaphors", {}).values()
        )
        or type(fused.get("neutral_pair_forms")) is not list
        or len(fused.get("neutral_pair_forms", [])) < 2
        or any(
            type(row) is not str
            or row.count("{thought_literal}") != 1
            or row.count("{action_literal}") != 1
            for row in fused.get("neutral_pair_forms", [])
        )
        or type(fused.get("standalone_forms")) is not dict
        or set(fused.get("standalone_forms", {}))
        != set(STEP11_SURFACE_CATALOG.get("source_slots", []))
        or any(
            type(rows) is not list
            or len(rows) < 3
            or any(
                type(row) is not str
                or row.count("{literal}") != 1
                or "{" in row.replace("{literal}", "")
                or "}" in row.replace("{literal}", "")
                for row in rows
            )
            for rows in fused.get("standalone_forms", {}).values()
        )
        or type(fused.get("mixed_emotion_forms")) is not list
        or len(fused.get("mixed_emotion_forms", [])) < 3
        or any(
            type(row) is not str
            or row.count("{first_literal}") != 1
            or row.count("{second_literal}") != 1
            for row in fused.get("mixed_emotion_forms", [])
        )
        or type(fused.get("unknown_tails")) is not dict
        or set(fused.get("unknown_tails", {}))
        != {
            "cause",
            "referent",
            "other_person_awareness",
            "decision_state",
            "post_decision_comparative_merit",
            "future",
            "outcome",
            "relation",
            "generic",
        }
        or any(
            type(rows) is not list
            or len(rows) < 2
            or any(
                type(row) is not str
                or not row
                or "{" in row
                or "}" in row
                for row in rows
            )
            for rows in fused.get("unknown_tails", {}).values()
        )
    )
    if not fused_invalid:
        for relation_type in _RELATION_TYPES:
            by_direction = fused_relations.get(relation_type, {})
            if (
                type(by_direction) is not dict
                or set(by_direction) != set(_RELATION_DIRECTIONS)
            ):
                fused_invalid = True
                continue
            for direction in _RELATION_DIRECTIONS:
                rows = by_direction.get(direction, [])
                if type(rows) is not list or len(rows) < 2:
                    fused_invalid = True
                    continue
                for row in rows:
                    if (
                        type(row) is not dict
                        or set(row)
                        != {
                            "stem",
                            "endpoint_realization",
                            "relation_type",
                            "relation_direction",
                        }
                        or type(row.get("stem")) is not str
                        or row["stem"].count("{from_endpoint}") != 1
                        or row["stem"].count("{to_endpoint}") != 1
                        or row.get("endpoint_realization")
                        != (
                            "two_exact_literals_or_one_local_anaphor_"
                            "and_one_exact_literal"
                        )
                        or row.get("relation_type") != relation_type
                        or row.get("relation_direction") != direction
                    ):
                        fused_invalid = True
    generated_rows = strings(
        [
            fused_relations,
            fused.get("local_anaphors", {}),
            fused.get("neutral_pair_forms", []),
            fused.get("standalone_forms", {}),
            fused.get("mixed_emotion_forms", []),
            fused.get("unknown_tails", {}),
            reception.get("anaphoric_content_forms", {}),
            reception.get("act_predicates", {}),
            reception.get("sentence_templates", []),
        ]
    )
    if any(
        fragment in row
        for row in generated_rows
        for fragment in fused.get("forbidden_generated_fragments", [])
    ):
        fused_invalid = True
    if fused_invalid:
        issues.append("STEP11_SURFACE_CATALOG_OBLIGATION_FUSED_GRAMMAR_INVALID")
    return tuple(sorted(set(issues)))


__all__ = [
    "FROZEN_RC0022_STEP11_SURFACE_CATALOG_SHA256",
    "FROZEN_RC0023_STEP11_SURFACE_CATALOG_SHA256",
    "FROZEN_RC0024_STEP11_SURFACE_CATALOG_SHA256",
    "FROZEN_STEP11_SURFACE_CATALOG_SHA256",
    "STEP11_SURFACE_CATALOG",
    "STEP11_SURFACE_CATALOG_SHA256",
    "validate_step11_surface_catalog",
]
