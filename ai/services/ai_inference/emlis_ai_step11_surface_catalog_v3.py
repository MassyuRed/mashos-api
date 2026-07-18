# -*- coding: utf-8 -*-
from __future__ import annotations

"""Declarative controlled-surface catalog for the Step 11 rc0025 successor.

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
_GROUP_CLAUSE_SEPARATOR = "、また、"
_GROUP_SENTENCE_SUFFIX = "。"


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
    "schema_version": "cocolon.emlis.nls_v3.step11_surface_catalog.v6",
    "candidate_version_id": "nls_v3_rc_0025",
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
    "group_grammar": {
        "schema_version": (
            "cocolon.emlis.nls_v3.step11_group_grammar.rc0022.v1"
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
    "mixed_emotion_compound_grammar": {
        "schema_version": (
            "cocolon.emlis.nls_v3.step11_mixed_emotion_compound.rc0022.v1"
        ),
        "positive_before_negative_required": True,
        "endpoint_role": "affect",
        "relation_type": "coexists_with",
        "relation_direction": "bidirectional",
        "forms": [
            (
                "{positive_ref}として{positive_literal}と"
                "{negative_ref}として{negative_literal}があり、"
                "二つはどちらも選ばれています"
            ),
            (
                "{positive_ref}の{positive_literal}と"
                "{negative_ref}の{negative_literal}を、"
                "どちらも選ばれた感情として受け取っています"
            ),
            (
                "{positive_ref}に{positive_literal}、"
                "{negative_ref}に{negative_literal}があり、"
                "片方にまとめず並んでいます"
            ),
        ],
    },
    "endpoint_reference_grammar": {
        "schema_version": (
            "cocolon.emlis.nls_v3.step11_endpoint_reference_grammar.v1"
        ),
        "ordinal_pattern": _REFERENCE_ORDINAL_PATTERN,
        "minimum_ordinal": 1,
        "maximum_policy": "independently_recomputed_active_registry_size",
        "reference_token_template": _REFERENCE_TOKEN_TEMPLATE,
        "role_labels": dict(_ENDPOINT_ROLE_LABELS),
        "direct_introduction": {
            "wrapper": "{reference}{stem}",
            "stems": [
                "として、{quoted_literal}があります",
                "として、{quoted_literal}がここにあります",
                "として、{quoted_literal}が示されています",
                "として、{quoted_literal}をそのまま受け取っています",
            ],
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
            "Emlisは、{content}、{predicate}",
            "{content}、Emlisは{predicate}",
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
                    "その思いを",
                    "今ここにあるその気持ちを",
                ],
            },
            "action": {
                "undetermined": [
                    "その行動の記述を、完了か予定かを決めずに",
                    "その動きを、済んだことかこれからかを足さずに",
                ],
                "intended": [
                    "その予定を、実行済みとは決めずに",
                    "そのこれからの意図を、まだ完了した動きとはせずに",
                ],
                "reported_ongoing": [
                    "その続いている行動を",
                    "その継続中の動きを",
                ],
                "reported_not_completed": [
                    "その未完了の行動を、済んだことにはせずに",
                    "まだ終えていないその動きを、完了とはせずに",
                ],
                "reported_completed": [
                    "その完了した行動を",
                    "その終えた動きを",
                ],
            },
            "thought_action": {
                "undetermined": [
                    "その思いと行動を、完了か予定かを足さずに",
                    "そこにある思いと動きを、状態を決めつけずに",
                ],
                "intended": [
                    "その思いとこれからの意図を、実行済みとは決めずに",
                    "その気持ちと予定を、まだ完了した動きとはせずに",
                ],
                "reported_ongoing": [
                    "その思いと続いている行動を",
                    "その気持ちと継続中の動きを",
                ],
                "reported_not_completed": [
                    "その思いと未完了の行動を、済んだことにはせずに",
                    "その気持ちとまだ終えていない動きを、完了とはせずに",
                ],
                "reported_completed": [
                    "その思いと完了した行動を",
                    "その気持ちと終えた動きを",
                ],
            },
            "relation": {
                "status_neutral": [
                    "そこにある関わりを",
                    "そのつながりを",
                ],
                "undetermined": [
                    "その関わりを、行動の状態を足さずに",
                    "そのつながりを、完了か予定かを決めずに",
                ],
                "intended": [
                    "その関わりを、予定を実行済みとは決めずに",
                    "そのつながりを、これからの動きを完了とはせずに",
                ],
                "reported_ongoing": [
                    "その続いている関わりを",
                    "継続中の動きを含むそのつながりを",
                ],
                "reported_not_completed": [
                    "その関わりを、未完了の動きを済んだことにはせずに",
                    "そのつながりを、まだ終えていない動きを完了とはせずに",
                ],
                "reported_completed": [
                    "その完了した動きを含む関わりを",
                    "終えた行動を含むそのつながりを",
                ],
            },
        },
        "act_predicates": {
            "hold_in_attention": [
                "気に留めています。",
                "見失わずにいます。",
                "注意深く見ています。",
            ],
            "do_not_dismiss": [
                "軽く扱わないまま受け取っています。",
                "小さく片づけないまま受け止めています。",
                "記述として残したまま見ています。",
            ],
            "receive_without_deciding": [
                "一つの意味に決めずに受け取っています。",
                "背景まで決めつけずに受け止めています。",
                "先回りして結論づけずに見ています。",
            ],
            "honor_concrete_action": [
                "書かれた状態のまま受け取っています。",
                "具体的に受け止めています。",
                "記述にないことを足さずに受け取っています。",
            ],
            "stay_with_mixed_meaning": [
                "一つの意味にまとめずに受け取っています。",
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
    "9b00e442e812885265f7170917a2c6529dbdbf647eb1a8a5cae9fa1ba5a05903"
)
STEP11_SURFACE_CATALOG_SHA256 = artifact_sha256(STEP11_SURFACE_CATALOG)


def validate_step11_surface_catalog() -> tuple[str, ...]:
    issues: list[str] = []
    if (
        STEP11_SURFACE_CATALOG.get("schema_version")
        != "cocolon.emlis.nls_v3.step11_surface_catalog.v6"
    ):
        issues.append("STEP11_SURFACE_CATALOG_SCHEMA_INVALID")
    if STEP11_SURFACE_CATALOG.get("candidate_version_id") != "nls_v3_rc_0025":
        issues.append("STEP11_SURFACE_CATALOG_VERSION_INVALID")
    if STEP11_SURFACE_CATALOG.get("body_free") is not True:
        issues.append("STEP11_SURFACE_CATALOG_BODY_FREE_REQUIRED")
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
        != "cocolon.emlis.nls_v3.step11_group_grammar.rc0022.v1"
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
    compound_placeholders = (
        "{positive_ref}",
        "{positive_literal}",
        "{negative_ref}",
        "{negative_literal}",
    )
    if (
        type(compound) is not dict
        or set(compound)
        != {
            "schema_version",
            "positive_before_negative_required",
            "endpoint_role",
            "relation_type",
            "relation_direction",
            "forms",
        }
        or compound.get("schema_version")
        != "cocolon.emlis.nls_v3.step11_mixed_emotion_compound.rc0022.v1"
        or compound.get("positive_before_negative_required") is not True
        or compound.get("endpoint_role") != "affect"
        or compound.get("relation_type") != "coexists_with"
        or compound.get("relation_direction") != "bidirectional"
        or type(compound.get("forms")) is not list
        or len(compound.get("forms", [])) < 3
        or any(
            type(row) is not str
            or not row
            or any(row.count(token) != 1 for token in compound_placeholders)
            or row.endswith(_GROUP_SENTENCE_SUFFIX)
            or _GROUP_CLAUSE_SEPARATOR in row
            for row in compound.get("forms", [])
        )
    ):
        issues.append(
            "STEP11_SURFACE_CATALOG_MIXED_EMOTION_COMPOUND_INVALID"
        )

    reference_grammar = STEP11_SURFACE_CATALOG.get(
        "endpoint_reference_grammar", {}
    )
    direct_introduction = (
        reference_grammar.get("direct_introduction", {})
        if type(reference_grammar) is dict
        else {}
    )
    role_labels = (
        reference_grammar.get("role_labels", {})
        if type(reference_grammar) is dict
        else {}
    )
    reference_stems = (
        direct_introduction.get("stems", [])
        if type(direct_introduction) is dict
        else []
    )
    reference_wrapper = (
        direct_introduction.get("wrapper")
        if type(direct_introduction) is dict
        else None
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
            "direct_introduction",
            "relation_endpoint_policy",
            "reference_before_use_required",
        }
        or reference_grammar.get("schema_version")
        != "cocolon.emlis.nls_v3.step11_endpoint_reference_grammar.v1"
        or reference_grammar.get("ordinal_pattern")
        != _REFERENCE_ORDINAL_PATTERN
        or reference_grammar.get("minimum_ordinal") != 1
        or reference_grammar.get("maximum_policy")
        != "independently_recomputed_active_registry_size"
        or reference_template != _REFERENCE_TOKEN_TEMPLATE
        or type(role_labels) is not dict
        or role_labels != _ENDPOINT_ROLE_LABELS
        or len(set(role_labels.values())) != len(_ENDPOINT_ROLES)
        or type(direct_introduction) is not dict
        or set(direct_introduction)
        != {
            "wrapper",
            "stems",
            "literal_owner_policy",
            "terminal_owned_by_group",
        }
        or reference_wrapper != "{reference}{stem}"
        or type(reference_stems) is not list
        or len(reference_stems) < 4
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
                )
            )
            or stem.endswith(_GROUP_SENTENCE_SUFFIX)
            for stem in reference_stems
        )
        or direct_introduction.get("literal_owner_policy")
        != "exact_source_identity_once"
        or direct_introduction.get("terminal_owned_by_group") is not True
        or reference_grammar.get("relation_endpoint_policy")
        != "typed_reference_only"
        or reference_grammar.get("reference_before_use_required") is not True
    )
    if not reference_grammar_invalid:
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
        for text in strings([forms, reception, direct_introduction])
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
    if (
        type(anaphoric_content_forms) is not dict
        or set(anaphoric_content_forms) != set(expected_statuses)
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
            for scope, statuses in expected_statuses.items()
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
