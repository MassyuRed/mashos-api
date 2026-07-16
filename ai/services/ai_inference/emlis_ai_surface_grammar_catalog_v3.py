# -*- coding: utf-8 -*-
from __future__ import annotations

"""Frozen declarative grammar fragments shared by NLS v3 surface stages.

This catalog contains bounded tokens and feature mappings, never expected
sentences, case cues or traversal code.  Step 7 renders from it; a future
independent parser may consume the same data without sharing renderer logic.
"""

import re
import unicodedata
from typing import Any

from emlis_ai_nls_v3_artifact_contract import artifact_sha256


SURFACE_GRAMMAR_CATALOG_VERSION = (
    "cocolon.emlis.nls_v3.surface_grammar_catalog.20260715.v1"
)

SURFACE_GRAMMAR_CATALOG: dict[str, Any] = {
    "catalog_version": SURFACE_GRAMMAR_CATALOG_VERSION,
    "document": {
        "observation_label": "見えたこと：",
        "reception_label": "Emlisから：",
        "section_separator": "\n\n",
        "sentence_separator": "\n",
        "terminal": "。",
    },
    "source_anchor": {
        "open": "「",
        "close": "」",
        "binding": "に表れた",
    },
    "source_field": {
        "memo": "書かれた考えにある",
        "memo_action": "書かれた行動にある",
        "emotion_details": "選ばれた感情にある",
        "emotions": "感情の記録にある",
        "category": "選ばれた分類にある",
        "mixed": "現在入力にある",
    },
    "temporal_scope": {
        "current_input": "今の",
        "reported_past": "過去として伝えられた",
        "intended_future": "これからに向けた",
        "atemporal": "時点を限定しない",
        "unknown": "時点が未確定の",
    },
    "polarity": {
        "positive": "明るさを含む",
        "negative": "重さを含む",
        "mixed": "異なる向きをともに含む",
        "neutral": "述べられた",
        "unknown": "向きが未確定の",
    },
    "referent_scope": {
        "self": "自己についての内容",
        "other": "相手についての内容",
        "event": "出来事",
        "action": "行動",
        "state": "状態",
        "relation": "二つの内容の関係",
        "unknown": "分からない点",
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
    "semantic_role": {
        "antecedent": "先に置かれた",
        "consequent": "その後に続く",
        "none": "",
    },
    "source_semantic_role": {
        "concrete_action_evidence": "具体的な行動の記録として示された",
        "concrete_action": "具体的な行動として示された",
        "contrast_before": "対照の前側に置かれた",
        "contrast_after": "対照の後側に置かれた",
        "embedded_turn": "折り返しに置かれた",
        "initial_condition": "前提として置かれた",
        "retained_intention": "保たれた意向を表す",
    },
    "source_operator": {
        "constraint": "条件として示された",
        "continuation": "続いていることを表す",
        "shift": "変化を表す",
        "action": "行動として示された",
        "wish": "願いとして示された",
    },
    "meaning_block_kind": {
        "current_expression": "現在の表れとして分けられた",
        "constraint": "条件として分けられた",
        "action": "行動として分けられた",
        "wish": "願いとして分けられた",
    },
    "predicate": {
        "nucleus_observed": "が見えます",
        "coexisting_meanings_observed": "結びつきが保たれています",
        "shift_observed": "が見えます",
        "action_intended": "が未来を保証しない意図または行動として残っています",
        "bounded_counterposition_observed": "だけを確定した事実にはしません",
    },
    "relation": {
        "precedes": "前後の順序があります",
        "contrasts_with": "対照が保たれています",
        "coexists_with": "両方が同時に保たれています",
        "qualifies": "一方が他方を限定しています",
        "supports_without_guarantee": "保証しない結びつきがあります",
    },
    "directed_relation_joiner": {
        "precedes": {"left": "が", "right": "より前に置かれています"},
        "contrasts_with": {"left": "と", "right": "の対照が保たれています"},
        "coexists_with": {"left": "と", "right": "が同時に保たれています"},
        "qualifies": {"left": "が", "right": "を限定しています"},
        "supports_without_guarantee": {
            "left": "が",
            "right": "を保証せず支える関係として示されています",
        },
    },
    "unknown": {
        "preserve_unknown": "については分からないまま保ちます",
        "bounded_uncertainty": "については確定できる範囲を越えません",
    },
    "unknown_dimension": {
        "cause": "原因",
        "choice": "選択や判断",
        "referent": "対象",
        "relation": "関係",
        "outcome": "結果",
        "other": "その範囲",
    },
    "unknown_dimension_joiner": "と",
    "self_denial": {
        "separate_claim_from_observation": "という自己評価を観測事実とは分けます",
    },
    "stance": {
        "hold_in_attention": "気に留めます",
        "do_not_dismiss": "軽く扱いません",
        "receive_without_deciding": "決めつけず受け取ります",
        "honor_concrete_action": "具体的な行動として大切に受け取ります",
        "stay_with_mixed_meaning": "異なる向きの両方として受け取ります",
    },
    "antecedent_referent": {
        "grounded_nucleus_notice": "その点",
        "grounded_relation_preservation": "その結びつき",
        "unknown_boundary_preservation": "その分からない点",
        "significance_or_shift": "その変化",
        "intention_or_next_action": "その行動",
        "self_denial_boundary": "その自己評価との切り分け",
        "bounded_counterposition": "その限定",
    },
    "connector": {
        "precedes": "その順序を保つと、",
        "explains_without_causation": "原因と決めつけずに、",
        "contrasts_with": "対照を保って、",
        "coexists_with": "両方を保って、",
        "qualifies": "その限定のもとで、",
        "receives": "",
        "separates_self_denial_from": "切り分けると、",
        "preserves_unknown_before": "分からなさを先に保つと、",
    },
    "modality": {
        "observed": "",
        "reported": "伝えられた範囲で、",
        "intended": "未来を保証せず、",
        "possible": "可能性の範囲で、",
        "unknown": "未確定のまま、",
    },
    "clause_joiner": "、また、",
    "production_node_sequences": {
        "grounded_nucleus_notice": [
            "grounded_referent", "observation_predicate", "modality"
        ],
        "grounded_relation_preservation": [
            "grounded_referent", "grounded_relation", "modality"
        ],
        "unknown_boundary_preservation": [
            "grounded_referent", "unknown_boundary", "modality"
        ],
        "significance_or_shift": [
            "grounded_referent", "observation_predicate", "modality"
        ],
        "intention_or_next_action": [
            "grounded_referent", "observation_predicate", "modality"
        ],
        "self_denial_boundary": [
            "grounded_referent", "self_denial_boundary", "modality"
        ],
        "bounded_counterposition": [
            "grounded_referent", "observation_predicate", "modality"
        ],
        "bound_emlis_reception": [
            "grounded_referent", "emlis_stance", "modality"
        ],
    },
    "body_free": True,
}

SURFACE_GRAMMAR_CATALOG_SHA256 = artifact_sha256(SURFACE_GRAMMAR_CATALOG)
FROZEN_SURFACE_GRAMMAR_CATALOG_SHA256 = (
    "af4a49bc08437cbd6ab968d52acf45971eb8a51f1468c87328717398e7f067e4"
)

_FORBIDDEN_CUE_RE = re.compile(
    r"(?:case_id|batch_id|family_id|expected_|nls3s_b|structural_variation)",
    re.IGNORECASE,
)
_CATALOG_UNSET = object()


def validate_surface_grammar_catalog(
    value: Any = _CATALOG_UNSET,
) -> tuple[str, ...]:
    if value is _CATALOG_UNSET:
        value = SURFACE_GRAMMAR_CATALOG
    issues: list[str] = []
    if type(value) is not dict or value.get("body_free") is not True:
        return ("GRAMMAR_CATALOG_SHAPE_INVALID",)
    if value.get("catalog_version") != SURFACE_GRAMMAR_CATALOG_VERSION:
        issues.append("GRAMMAR_CATALOG_VERSION_MISMATCH")
    tokens: list[str] = []

    def walk(item: Any) -> None:
        if type(item) is str:
            tokens.append(item)
        elif type(item) is list:
            for child in item:
                walk(child)
        elif type(item) is dict:
            for key, child in item.items():
                tokens.append(str(key))
                walk(child)
        elif item is not True:
            issues.append("GRAMMAR_CATALOG_NON_DECLARATIVE_VALUE")

    walk(value)
    for token in tokens:
        if unicodedata.normalize("NFC", token) != token or "\r" in token:
            issues.append("GRAMMAR_CATALOG_NON_CANONICAL_TOKEN")
        if _FORBIDDEN_CUE_RE.search(token):
            issues.append("GRAMMAR_CATALOG_FIXTURE_CUE_FORBIDDEN")
    if artifact_sha256(value) != FROZEN_SURFACE_GRAMMAR_CATALOG_SHA256:
        issues.append("GRAMMAR_CATALOG_FROZEN_HASH_MISMATCH")
    return tuple(sorted(set(issues)))


def catalog_token(group: str, key: str) -> str:
    """Read one closed token after validating the frozen catalog."""

    if validate_surface_grammar_catalog():
        raise ValueError("GRAMMAR_CATALOG_INVALID")
    value = SURFACE_GRAMMAR_CATALOG.get(group)
    if type(value) is not dict or type(value.get(key)) is not str:
        raise KeyError("GRAMMAR_CATALOG_TOKEN_UNRESOLVED")
    return value[key]


__all__ = [
    "FROZEN_SURFACE_GRAMMAR_CATALOG_SHA256",
    "SURFACE_GRAMMAR_CATALOG",
    "SURFACE_GRAMMAR_CATALOG_SHA256",
    "SURFACE_GRAMMAR_CATALOG_VERSION",
    "catalog_token",
    "validate_surface_grammar_catalog",
]
