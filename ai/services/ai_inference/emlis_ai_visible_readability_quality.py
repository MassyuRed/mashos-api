# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase18 visible readability quality helper for EmlisAI.

The helper evaluates already-realized visible text in memory and returns only a
meta-safe report.  It does not generate or rewrite reply text, does not store
raw input, and does not change public response / RN / DB contracts.
"""

import re
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from typing import Any, Final

VISIBLE_READABILITY_QUALITY_SCHEMA_VERSION: Final = "cocolon.emlis.visible_readability_quality.v1"
VISIBLE_READABILITY_QUALITY_SOURCE_PHASE: Final = "Phase18_product_quality_stabilization"
VISIBLE_READABILITY_QUALITY_TARGET_LABELLED_TWO_STAGE: Final = "labelled_two_stage_comment_text"
VISIBLE_READABILITY_QUALITY_TARGET_PLAIN_SURFACE: Final = "plain_visible_surface"

CLASSIFICATION_PASS: Final = "passed"
CLASSIFICATION_REPAIR_REQUIRED: Final = "repair_required"
CLASSIFICATION_RED: Final = "red"
ACTION_ALLOW: Final = "allow"
ACTION_RERENDER_SURFACE_ONCE: Final = "rerender_surface_once"
ACTION_FAIL_CLOSED: Final = "fail_closed"

MAX_SAME_CONNECTOR_PER_COMMENT: Final = 1
MAX_RELATION_CONVENIENCE_PHRASE_PER_COMMENT: Final = 1
OBSERVATION_RECEPTION_JACCARD_MAX: Final = 0.72

_LABEL_OBSERVATION_RE = re.compile(r"見えたこと\s*[:：]")
_LABEL_RECEPTION_RE = re.compile(r"Emlisから\s*[:：]")
_SENTENCE_SPLIT_RE = re.compile(r"[。！？!?]+|[\r\n]+")
_TOKEN_RE = re.compile(r"[0-9A-Za-z_\-]+|[一-龥ぁ-んァ-ンー]{2,}")

_INTERNAL_ROLE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("internal_role_achievement", re.compile(r"\bachievement\b", re.IGNORECASE)),
    ("internal_role_positive_state", re.compile(r"positive[\s_]+state", re.IGNORECASE)),
    ("internal_role_perfection_fear", re.compile(r"perfection[\s_]+fear", re.IGNORECASE)),
    ("internal_role_pressure_or_limit", re.compile(r"pressure[\s_]+or[\s_]+limit", re.IGNORECASE)),
    ("internal_role_role_key", re.compile(r"\brole_[0-9a-zA-Z_\-]*", re.IGNORECASE)),
)
_RELATION_SKELETON_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("relation_skeleton_same_flow", re.compile(r"同じ流れ")),
    ("relation_skeleton_same_place", re.compile(r"同じ場所")),
    ("relation_skeleton_one_side", re.compile(r"片方だけに(?:寄らず|減らさず)")),
    ("relation_skeleton_separate_directions", re.compile(r"別々の向き")),
    ("relation_skeleton_overlap_kept", re.compile(r"重なりを保っています")),
    ("relation_skeleton_one_direction", re.compile(r"一方向には決まりきっていません")),
)

_SOFT_LIMITED_RULES: tuple[tuple[str, tuple[str, ...], int], ...] = (
    ("connector_ippoude", ("一方で", "その一方で"), MAX_SAME_CONNECTOR_PER_COMMENT),
    ("predicate_narandeimasu", ("並んでいます",), MAX_RELATION_CONVENIENCE_PHRASE_PER_COMMENT),
    ("phrase_sukoshi_modoru_ugoki", ("少し戻る動き",), MAX_RELATION_CONVENIENCE_PHRASE_PER_COMMENT),
    ("phrase_mae_no_omosa", ("前の重さ",), MAX_RELATION_CONVENIENCE_PHRASE_PER_COMMENT),
    ("phrase_mi_nagara", ("見ながら",), MAX_RELATION_CONVENIENCE_PHRASE_PER_COMMENT),
)
_COMMON_TOKENS = {
    "見えたこと",
    "Emlisから",
    "見えます",
    "見えています",
    "受け取れます",
    "残っています",
    "ように",
    "として",
    "こと",
    "もの",
    "状態",
    "方向",
    "動き",
    "気持ち",
}
_FORBIDDEN_META_KEYS = {
    "raw_input",
    "rawInput",
    "raw_text",
    "rawText",
    "input_text",
    "inputText",
    "user_input",
    "userInput",
    "memo",
    "memo_text",
    "memoText",
    "current_input",
    "currentInput",
    "comment_text",
    "commentText",
    "surface_text",
    "realized_text",
    "line_text",
    "body",
    "text",
    "sentence",
    "sentences",
    "phrase",
    "raw_quote",
    "evidence_text",
}
_TRUE_FORBIDDEN_FLAGS = {
    "raw_input_included",
    "raw_text_included",
    "input_text_included",
    "comment_text_included",
    "comment_text_body_included",
    "comment_text_body_included_in_meta",
    "public_response_key_added",
    "public_response_key_change",
    "response_shape_changed",
    "rn_visible_contract_changed",
    "api_route_changed",
    "db_physical_name_changed",
    "display_gate_relaxed",
    "grounding_gate_relaxed",
    "template_gate_relaxed",
    "reader_gate_relaxed",
    "gate_relaxed",
    "fixed_sentence_template_used",
    "completed_reply_template_used",
    "input_specific_template_used",
    "external_ai_used",
    "local_llm_used",
}


def _clean(value: Any) -> str:
    return " ".join(str(value or "").replace("\u3000", " ").split()).strip()


def _count_occurrences(text: str, fragments: Sequence[str]) -> int:
    return sum(text.count(fragment) for fragment in fragments if fragment)


def _dedupe(values: Iterable[Any]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        item = str(value or "")
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _split_two_stage_sections(comment_text: str) -> tuple[str, str, bool]:
    text = str(comment_text or "")
    observation_match = _LABEL_OBSERVATION_RE.search(text)
    reception_match = _LABEL_RECEPTION_RE.search(text)
    if not observation_match or not reception_match or observation_match.start() > reception_match.start():
        return "", "", False
    observation = text[observation_match.end() : reception_match.start()]
    reception = text[reception_match.end() :]
    return observation, reception, True


def _tokens_for_similarity(text: str) -> set[str]:
    tokens: set[str] = set()
    for raw in _TOKEN_RE.findall(text):
        token = _clean(raw)
        if len(token) < 2 or token in _COMMON_TOKENS:
            continue
        tokens.add(token)
        if re.fullmatch(r"[一-龥ぁ-んァ-ンー]+", token) and len(token) >= 4:
            tokens.update(token[index : index + 3] for index in range(0, max(0, len(token) - 2)))
    return {token for token in tokens if token and token not in _COMMON_TOKENS}


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / max(1, len(left | right))


def _soft_repetition_report(text: str) -> tuple[list[str], dict[str, int]]:
    reasons: list[str] = []
    counts: dict[str, int] = {}
    for rule_id, fragments, limit in _SOFT_LIMITED_RULES:
        count = _count_occurrences(text, fragments)
        counts[rule_id] = count
        if count > limit:
            reasons.append(f"visible_readability_soft_repetition:{rule_id}")
    return reasons, counts


def _pattern_hits(text: str, patterns: Sequence[tuple[str, re.Pattern[str]]]) -> list[str]:
    return [rule_id for rule_id, pattern in patterns if pattern.search(text)]


def _contains_forbidden_meta_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key) in _FORBIDDEN_META_KEYS:
                return True
            if _contains_forbidden_meta_key(item):
                return True
        return False
    if isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_meta_key(item) for item in value)
    return False


def assert_visible_readability_quality_meta_only(report: Mapping[str, Any]) -> None:
    if _contains_forbidden_meta_key(report):
        raise ValueError("visible readability quality report must not include raw/comment body payload keys")
    for key in _TRUE_FORBIDDEN_FLAGS:
        if report.get(key) is True:
            raise ValueError(f"visible readability quality report violates public contract: {key}=true")


def build_visible_readability_quality_report(
    *,
    comment_text: Any = "",
    target: str | None = None,
    observation_reception_jaccard_max: float = OBSERVATION_RECEPTION_JACCARD_MAX,
) -> dict[str, Any]:
    """Return a meta-only Phase18 readability QA report.

    The visible surface is used only while computing counts and similarity.  The
    returned report stores rule identifiers and numeric counts, not the body.
    """

    text = str(comment_text or "")
    observation, reception, labelled_two_stage = _split_two_stage_sections(text)
    target_id = target or (
        VISIBLE_READABILITY_QUALITY_TARGET_LABELLED_TWO_STAGE
        if labelled_two_stage
        else VISIBLE_READABILITY_QUALITY_TARGET_PLAIN_SURFACE
    )
    hard_block_reasons: list[str] = []
    hard_block_reasons.extend(f"visible_readability:{hit}" for hit in _pattern_hits(text, _INTERNAL_ROLE_PATTERNS))
    # Relation skeleton wording is a hard blocker for labelled two-stage comment
    # text, where Phase18-8 evaluates the public observation/reception surface.
    # Legacy plain composer text can contain natural phrases such as 「同じ場所で」
    # and must keep the Phase18-7 passed diagnostic contract.
    if labelled_two_stage:
        hard_block_reasons.extend(f"visible_readability:{hit}" for hit in _pattern_hits(text, _RELATION_SKELETON_PATTERNS))

    soft_repair_reasons, soft_counts = _soft_repetition_report(text)
    observation_tokens = _tokens_for_similarity(observation)
    reception_tokens = _tokens_for_similarity(reception)
    similarity = _jaccard(observation_tokens, reception_tokens)
    observation_reception_too_similar = bool(
        labelled_two_stage
        and observation_tokens
        and reception_tokens
        and similarity > float(observation_reception_jaccard_max)
    )
    if observation_reception_too_similar:
        soft_repair_reasons.append("visible_readability:observation_reception_too_similar")

    same_connector_repetition_detected = any(
        reason.endswith(":connector_ippoude") for reason in soft_repair_reasons
    )
    relation_convenience_phrase_repetition_detected = any(
        reason.endswith((":predicate_narandeimasu", ":phrase_sukoshi_modoru_ugoki", ":phrase_mae_no_omosa", ":phrase_mi_nagara"))
        for reason in soft_repair_reasons
    )
    hard_block_reasons = _dedupe(hard_block_reasons)
    soft_repair_reasons = _dedupe(soft_repair_reasons)
    if hard_block_reasons:
        classification = CLASSIFICATION_RED
        action = ACTION_FAIL_CLOSED
    elif soft_repair_reasons:
        classification = CLASSIFICATION_REPAIR_REQUIRED
        action = ACTION_RERENDER_SURFACE_ONCE
    else:
        classification = CLASSIFICATION_PASS
        action = ACTION_ALLOW
    report: dict[str, Any] = {
        "schema_version": VISIBLE_READABILITY_QUALITY_SCHEMA_VERSION,
        "source_phase": VISIBLE_READABILITY_QUALITY_SOURCE_PHASE,
        "target": target_id,
        "evaluated": True,
        "passed": classification == CLASSIFICATION_PASS,
        "classification": classification,
        "action": action,
        "hard_block_reasons": hard_block_reasons,
        "soft_repair_reasons": soft_repair_reasons,
        "same_connector_repetition_detected": same_connector_repetition_detected,
        "relation_convenience_phrase_repetition_detected": relation_convenience_phrase_repetition_detected,
        "soft_limited_rule_counts": dict(soft_counts),
        "max_same_connector_per_comment": MAX_SAME_CONNECTOR_PER_COMMENT,
        "max_relation_convenience_phrase_per_comment": MAX_RELATION_CONVENIENCE_PHRASE_PER_COMMENT,
        "observation_reception_jaccard": round(similarity, 4),
        "observation_reception_jaccard_max": float(observation_reception_jaccard_max),
        "observation_reception_too_similar": observation_reception_too_similar,
        "labelled_two_stage_comment_text_detected": labelled_two_stage,
        "question_sentence_allowed": bool("詳しく残せそうなら" in text),
        "internal_role_terms_forbidden": True,
        "relation_skeleton_forbidden": True,
        "exact_match_required": False,
        "comment_text_body_included_in_meta": False,
        "comment_text_body_included": False,
        "comment_text_included": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "input_text_included": False,
        "public_response_key_added": False,
        "rn_visible_contract_changed": False,
        "response_shape_changed": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "gate_relaxed": False,
        "fixed_sentence_template_used": False,
        "completed_reply_template_used": False,
        "input_specific_template_used": False,
        "external_ai_used": False,
        "local_llm_used": False,
    }
    assert_visible_readability_quality_meta_only(report)
    return report


def visible_readability_quality_public_summary(report: Mapping[str, Any] | None = None) -> dict[str, Any]:
    safe = dict(report or {})
    summary = {
        "schema_version": VISIBLE_READABILITY_QUALITY_SCHEMA_VERSION,
        "source_phase": VISIBLE_READABILITY_QUALITY_SOURCE_PHASE,
        "evaluated": bool(safe.get("evaluated")),
        "passed": bool(safe.get("passed")),
        "classification": str(safe.get("classification") or CLASSIFICATION_PASS),
        "action": str(safe.get("action") or ACTION_ALLOW),
        "hard_block_reasons": list(safe.get("hard_block_reasons") or []),
        "soft_repair_reasons": list(safe.get("soft_repair_reasons") or []),
        "same_connector_repetition_detected": bool(safe.get("same_connector_repetition_detected")),
        "relation_convenience_phrase_repetition_detected": bool(safe.get("relation_convenience_phrase_repetition_detected")),
        "observation_reception_too_similar": bool(safe.get("observation_reception_too_similar")),
        "comment_text_body_included_in_meta": False,
        "raw_input_included": False,
        "public_response_key_added": False,
        "rn_visible_contract_changed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
    }
    assert_visible_readability_quality_meta_only(summary)
    return summary


__all__ = [
    "ACTION_ALLOW",
    "ACTION_FAIL_CLOSED",
    "ACTION_RERENDER_SURFACE_ONCE",
    "CLASSIFICATION_PASS",
    "CLASSIFICATION_RED",
    "CLASSIFICATION_REPAIR_REQUIRED",
    "VISIBLE_READABILITY_QUALITY_SCHEMA_VERSION",
    "VISIBLE_READABILITY_QUALITY_SOURCE_PHASE",
    "VISIBLE_READABILITY_QUALITY_TARGET_LABELLED_TWO_STAGE",
    "assert_visible_readability_quality_meta_only",
    "build_visible_readability_quality_report",
    "visible_readability_quality_public_summary",
]
