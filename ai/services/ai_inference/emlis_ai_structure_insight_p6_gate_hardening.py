# -*- coding: utf-8 -*-
from __future__ import annotations

"""P6-5 gate hardening and soft-expression boundary.

This module is a P6-only hardening layer around Structure Insight visible
candidates.  It inspects a proposed surface string only in memory, then returns
body-free reason codes and contract flags.  It never writes ``comment_text``,
never returns the inspected surface body, and never changes public response
contracts.
"""

from collections import Counter
from collections.abc import Iterable, Mapping
import json
import re
from typing import Any, Final


STRUCTURE_INSIGHT_P6_GATE_HARDENING_SCHEMA_VERSION: Final = (
    "cocolon.emlis.structure_insight.p6_gate_hardening.v1"
)
STRUCTURE_INSIGHT_P6_GATE_HARDENING_SUMMARY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.structure_insight.p6_gate_hardening_summary.v1"
)
STRUCTURE_INSIGHT_P6_GATE_HARDENING_STEP: Final = "P6-5_GateHardeningSoftExpressionBoundary"
STRUCTURE_INSIGHT_P6_GATE_HARDENING_SOURCE: Final = (
    "Cocolon_EmlisAI_P6_StructureInsight_GateHardening_20260611"
)

GATE_DECISION_ALLOW_INTERNAL_SURFACE_CANDIDATE: Final = "allow_internal_surface_candidate"
GATE_DECISION_REVIEW_REQUIRED: Final = "review_required"
GATE_DECISION_BLOCK_SURFACE_CANDIDATE: Final = "block_surface_candidate"

REASON_SURFACE_CANDIDATE_MISSING: Final = "surface_candidate_missing"
REASON_SOFT_EXPRESSION_MISSING: Final = "soft_expression_missing"
REASON_DIAGNOSIS_SURFACE: Final = "diagnosis_surface"
REASON_PERSONALITY_CLAIM_SURFACE: Final = "personality_claim_surface"
REASON_CAUSE_CLAIM_WITHOUT_EVIDENCE_SURFACE: Final = "cause_claim_without_evidence_surface"
REASON_ADVICE_SURFACE: Final = "advice_surface"
REASON_FUTURE_PREDICTION_SURFACE: Final = "future_prediction_surface"
REASON_PERIOD_TENDENCY_FROM_SINGLE_RECORD_SURFACE: Final = "period_tendency_from_single_record_surface"
REASON_TARGET_JUDGEMENT_AGREEMENT_SURFACE: Final = "target_judgement_agreement_surface"
REASON_TARGET_INTENT_ASSERTION_SURFACE: Final = "target_intent_assertion_surface"
REASON_SELF_DENIAL_IDENTITY_CLAIM_AS_FACT_SURFACE: Final = "self_denial_identity_claim_as_fact_surface"
REASON_LOW_INFORMATION_OVERREAD_SURFACE: Final = "low_information_overread_surface"
REASON_USER_DICTIONARY_FACT_CLAIM_BLOCKED: Final = "user_dictionary_fact_claim_blocked"
REASON_HISTORY_FACT_ASSERTION_SURFACE: Final = "history_fact_assertion_surface"
REASON_RAW_TEXT_PAYLOAD_DETECTED: Final = "raw_text_payload_detected"
REASON_COMMENT_TEXT_BODY_IN_META_DETECTED: Final = "comment_text_body_in_meta_detected"
REASON_PUBLIC_CONTRACT_MUTATION_DETECTED: Final = "public_contract_mutation_detected"
REASON_GATE_RELAXATION_DETECTED: Final = "gate_relaxation_detected"
REASON_P6_RELATION_POLICY_NOT_INITIAL_VISIBLE: Final = "p6_relation_policy_not_initial_visible"
REASON_P6_RELATION_POLICY_BLOCKED: Final = "p6_relation_policy_blocked"
REASON_P6_QUALITY_RUBRIC_NOT_SAFE_PASS: Final = "p6_quality_rubric_not_safe_pass"
REASON_P6_QUALITY_RUBRIC_RED: Final = "p6_quality_rubric_red"
REASON_P6_QUALITY_RUBRIC_REPAIR_REQUIRED: Final = "p6_quality_rubric_repair_required"

VISIBILITY_ALLOW_INITIAL_VISIBLE: Final = "allow_initial_visible"
VISIBILITY_REVIEW_REQUIRED: Final = "review_required"
VISIBILITY_META_ONLY: Final = "meta_only"
VISIBILITY_BLOCKED: Final = "blocked"

VERDICT_RED: Final = "RED"
VERDICT_REPAIR_REQUIRED: Final = "REPAIR_REQUIRED"
VERDICT_YELLOW: Final = "YELLOW"
VERDICT_PASS: Final = "PASS"
VERDICT_STRUCTURE_INSIGHT_READY: Final = "STRUCTURE_INSIGHT_READY"

RELATION_SELF_DENIAL_IDENTITY_SPLIT: Final = "self_denial_identity_split"
RELATION_LOW_INFORMATION_UNSPECIFIED_WEIGHT: Final = "low_information_unspecified_weight"
RELATION_TARGET_JUDGEMENT_AGREEMENT: Final = "target_judgement_agreement"
RELATION_PERIOD_TENDENCY_FROM_SINGLE_RECORD: Final = "period_tendency_from_single_record"
RELATION_USER_DICTIONARY_FACT_CLAIM: Final = "user_dictionary_fact_claim"
RELATION_HISTORY_FACT_LINE_AS_INSIGHT: Final = "history_fact_line_as_insight"

_SPACE_RE: Final = re.compile(r"\s+")
_SOFT_MARKER_RE: Final = re.compile(
    r"(?:ように見えます|ようにも見えます|かもしれません|ではないでしょうか|ではないかと思います|"
    r"近い状態かもしれません|重なっているように見えます|残っているのかもしれません|"
    r"として残っているのかもしれません)"
)
_DIAGNOSIS_RE: Final = re.compile(
    r"(?:診断|治療|病気|症状|トラウマ|障害|発達障害|ADHD|うつ|鬱|PTSD|医学的|心理学的)"
)
_PERSONALITY_CLAIM_RE: Final = re.compile(
    r"(?:あなたは(?:[^。！？!?\n]{0,28})(?:人です|タイプです|性格です|本質です|依存しています|"
    r"弱い人|強い人|ダメな人|駄目な人)|(?:性格|人格|本質|タイプ)(?:です|だから))"
)
_CAUSE_CLAIM_RE: Final = re.compile(
    r"(?:原因は|原因です|原因になっています|本当の原因|根本原因|理由はひとつ|カテゴリが原因|"
    r"感情の強さが原因|だからあなたは|だから本当は)"
)
_ADVICE_RE: Final = re.compile(
    r"(?:してください|しましょう|するべき|すべき|しなければ|しなくてはいけません|必要があります|"
    r"距離を取(?:った|る)方がいい|連絡しましょう|相談しましょう|決めましょう)"
)
_FUTURE_PREDICTION_RE: Final = re.compile(
    r"(?:これから|今後|次は|将来|この先|必ず|きっと|絶対に|うまくいきます|失敗します|"
    r"続くでしょう|変わります|起きます|戻ります|悪化します|良くなります)"
)
_PERIOD_TENDENCY_RE: Final = re.compile(
    r"(?:いつも|毎回|ずっと|長い間|たびに|度に|繰り返し|くり返し|傾向|パターン|"
    r"なりやすい|しやすい|出やすい)"
)
_TARGET_JUDGEMENT_RE: Final = re.compile(
    r"(?:(?:相手|上司|あの人|その人|彼|彼女|会社|職場)[^。！？!?\n]{0,32}"
    r"(?:悪い|ひどい|最低|おかしい|間違って|軽く見て|見下して|敵)|あなたの怒りは"
    r"(?:正しい|当然)|相手が悪い|上司が悪い|攻撃していい)"
)
_TARGET_INTENT_RE: Final = re.compile(
    r"(?:(?:相手|上司|あの人|その人|彼|彼女|会社|職場)[^。！？!?\n]{0,32}"
    r"(?:思っています|思っている|考えています|考えている|わざと|意図して|見下しています|軽く見ています))"
)
_SELF_DENIAL_IDENTITY_FACT_RE: Final = re.compile(
    r"(?:あなたは(?:[^。！？!?\n]{0,20})(?:ダメ|駄目|価値がない|何もできない|弱い|嫌な人)|"
    r"自分が嫌なのは事実|何もできない状態です|価値がない状態です)"
)
_LOW_INFORMATION_OVERREAD_RE: Final = re.compile(
    r"(?:本当は|深いところでは|根本には|背景には|原因は|ずっと我慢してきた|隠れた意味)"
)
_HISTORY_FACT_ASSERTION_RE: Final = re.compile(
    r"(?:以前から|過去にも|前にも|これまでも|昔から|履歴では|記録では|前回も)"
)

_SOFT_MARKER_EXAMPLES: Final[tuple[str, ...]] = (
    "ように見えます",
    "かもしれません",
    "ではないでしょうか",
    "重なっているように見えます",
    "残っているのかもしれません",
)
_HARD_BLOCK_REASONS: Final[frozenset[str]] = frozenset(
    {
        REASON_SURFACE_CANDIDATE_MISSING,
        REASON_SOFT_EXPRESSION_MISSING,
        REASON_DIAGNOSIS_SURFACE,
        REASON_PERSONALITY_CLAIM_SURFACE,
        REASON_CAUSE_CLAIM_WITHOUT_EVIDENCE_SURFACE,
        REASON_ADVICE_SURFACE,
        REASON_FUTURE_PREDICTION_SURFACE,
        REASON_PERIOD_TENDENCY_FROM_SINGLE_RECORD_SURFACE,
        REASON_TARGET_JUDGEMENT_AGREEMENT_SURFACE,
        REASON_TARGET_INTENT_ASSERTION_SURFACE,
        REASON_SELF_DENIAL_IDENTITY_CLAIM_AS_FACT_SURFACE,
        REASON_LOW_INFORMATION_OVERREAD_SURFACE,
        REASON_USER_DICTIONARY_FACT_CLAIM_BLOCKED,
        REASON_HISTORY_FACT_ASSERTION_SURFACE,
        REASON_RAW_TEXT_PAYLOAD_DETECTED,
        REASON_COMMENT_TEXT_BODY_IN_META_DETECTED,
        REASON_PUBLIC_CONTRACT_MUTATION_DETECTED,
        REASON_GATE_RELAXATION_DETECTED,
        REASON_P6_RELATION_POLICY_BLOCKED,
        REASON_P6_QUALITY_RUBRIC_RED,
        REASON_P6_QUALITY_RUBRIC_REPAIR_REQUIRED,
    }
)
_UNSAFE_SURFACE_REASONS: Final[frozenset[str]] = frozenset(
    {
        REASON_DIAGNOSIS_SURFACE,
        REASON_PERSONALITY_CLAIM_SURFACE,
        REASON_CAUSE_CLAIM_WITHOUT_EVIDENCE_SURFACE,
        REASON_ADVICE_SURFACE,
        REASON_FUTURE_PREDICTION_SURFACE,
        REASON_PERIOD_TENDENCY_FROM_SINGLE_RECORD_SURFACE,
        REASON_TARGET_JUDGEMENT_AGREEMENT_SURFACE,
        REASON_TARGET_INTENT_ASSERTION_SURFACE,
        REASON_SELF_DENIAL_IDENTITY_CLAIM_AS_FACT_SURFACE,
        REASON_LOW_INFORMATION_OVERREAD_SURFACE,
        REASON_USER_DICTIONARY_FACT_CLAIM_BLOCKED,
        REASON_HISTORY_FACT_ASSERTION_SURFACE,
    }
)
_RAW_TEXT_PAYLOAD_KEYS: Final[frozenset[str]] = frozenset(
    {
        "raw_input",
        "rawInput",
        "raw_text",
        "rawText",
        "source_text",
        "sourceText",
        "input",
        "input_text",
        "inputText",
        "user_input",
        "userInput",
        "current_input",
        "currentInput",
        "history_context",
        "historyContext",
        "history_records",
        "historyRecords",
        "history_raw_text",
        "historyRawText",
        "memo",
        "memo_text",
        "memoText",
        "memo_action",
        "memoAction",
        "thought_text",
        "thoughtText",
        "action_text",
        "actionText",
        "candidate_body",
        "candidateBody",
        "surface_body",
        "surfaceBody",
        "surface_text",
        "surfaceText",
        "visible_text",
        "visibleText",
        "reply_text",
        "replyText",
        "display_text",
        "displayText",
        "observation_text",
        "reception_text",
        "raw_test_output",
        "test_output",
        "command_output",
        "terminal_output",
        "stdout",
        "stderr",
        "traceback",
        "body",
        "text",
    }
)
_COMMENT_TEXT_PAYLOAD_KEYS: Final[frozenset[str]] = frozenset(
    {"comment_text", "commentText", "comment_text_body", "commentTextBody", "candidate_comment_text"}
)
_TEXT_PAYLOAD_KEYS: Final[frozenset[str]] = _RAW_TEXT_PAYLOAD_KEYS | _COMMENT_TEXT_PAYLOAD_KEYS
_PUBLIC_CONTRACT_TRUE_FLAGS: Final[frozenset[str]] = frozenset(
    {
        "api_route_changed",
        "request_key_changed",
        "response_shape_changed",
        "public_response_key_added",
        "public_response_key_change",
        "public_payload_changed",
        "db_schema_changed",
        "db_physical_name_changed",
        "rn_visible_contract_changed",
        "rn_visible_title_changed",
        "fixed_sentence_template_added",
        "input_specific_template_added",
        "public_release_applied",
        "release_allowed",
        "product_quality_released",
    }
)
_GATE_RELAXATION_TRUE_FLAGS: Final[frozenset[str]] = frozenset(
    {
        "display_gate_relaxed",
        "grounding_gate_relaxed",
        "reader_gate_relaxed",
        "template_gate_relaxed",
        "runtime_surface_gate_relaxed",
        "visible_surface_gate_relaxed",
        "safety_gate_relaxed",
        "structure_insight_gate_relaxed",
        "gate_relaxed",
        "existing_gate_relaxed",
        "soft_expression_not_required",
        "soft_expression_requirement_relaxed",
        "diagnosis_allowed",
        "personality_claim_allowed",
        "cause_claim_allowed",
        "advice_allowed",
        "future_prediction_allowed",
        "target_judgement_agreement_allowed",
        "period_tendency_from_single_record_allowed",
        "user_dictionary_fact_claim_allowed",
    }
)
_FORBIDDEN_TRUE_FLAGS: Final[frozenset[str]] = _PUBLIC_CONTRACT_TRUE_FLAGS | _GATE_RELAXATION_TRUE_FLAGS | frozenset(
    {
        "raw_input_included",
        "raw_text_included",
        "input_text_included",
        "comment_text_included",
        "comment_text_body_included",
        "candidate_body_included",
        "surface_body_included",
        "history_raw_text_included",
        "reviewer_free_text_included",
        "raw_test_output_included",
        "command_output_included",
        "terminal_output_included",
        "comment_text_generated",
        "comment_text_key_written",
        "comment_text_written_by_gate",
        "surface_body_returned",
        "candidate_body_returned",
        "external_ai_used",
        "local_llm_used",
    }
)


def _clean(value: Any) -> str:
    if value is None or isinstance(value, (Mapping, list, tuple, set)):
        return ""
    return _SPACE_RE.sub(" ", str(value).replace("\u3000", " ").replace("\r", " ").replace("\n", " ")).strip()


def _safe_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    return {}


def _listify(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    if isinstance(value, (tuple, set)):
        return list(value)
    if isinstance(value, (str, bytes, bytearray)):
        return [value]
    try:
        return list(value)
    except TypeError:
        return [value]


def _dedupe(values: Iterable[Any] | Any | None) -> list[str]:
    out: list[str] = []
    for value in _listify(values):
        item = _clean(value)
        if item and item not in out:
            out.append(item)
    return out


def _safe_id(value: Any, *, default: str = "", max_length: int = 96) -> str:
    text = _clean(value) or default
    safe = "".join(ch if ch.isalnum() or ch in "._:-" else "_" for ch in text)
    safe = safe.strip("_")
    return (safe or default)[:max_length]


def _contains_key(value: Any, names: frozenset[str]) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in names:
                return True
            if _contains_key(child, names):
                return True
    elif isinstance(value, (list, tuple, set)):
        return any(_contains_key(child, names) for child in value)
    return False


def _flag_true(value: Any, names: frozenset[str]) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in names and child is True:
                return True
            if _flag_true(child, names):
                return True
    elif isinstance(value, (list, tuple, set)):
        return any(_flag_true(child, names) for child in value)
    return False


def _public_contract() -> dict[str, bool]:
    return {
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "api_route_changed": False,
        "request_key_changed": False,
        "response_shape_changed": False,
        "public_response_key_added": False,
        "db_schema_changed": False,
        "fixed_sentence_template_added": False,
        "release_allowed": False,
        "public_release_applied": False,
        "product_quality_released": False,
    }


def _body_free_contract() -> dict[str, bool]:
    return {
        "raw_input_included": False,
        "raw_text_included": False,
        "input_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "history_raw_text_included": False,
        "reviewer_free_text_included": False,
        "raw_test_output_included": False,
        "command_output_included": False,
        "terminal_output_included": False,
    }


def _source_summary(value: Mapping[str, Any]) -> dict[str, Any]:
    return _safe_mapping(value.get("summary")) or dict(value)


def _relation_family_from_sources(*, relation_family: Any, p6_relation_policy: Mapping[str, Any]) -> str:
    relation = _clean(relation_family).lower().replace(" ", "_").replace("-", "_")
    if relation:
        return relation
    source = _source_summary(p6_relation_policy)
    return _clean(source.get("relation_family")).lower().replace(" ", "_").replace("-", "_")


def _visibility_decision_from_policy(policy: Mapping[str, Any]) -> str:
    if not policy:
        return ""
    return _clean(_source_summary(policy).get("visibility_decision"))


def _quality_verdict_from_rubric(rubric: Mapping[str, Any]) -> str:
    if not rubric:
        return ""
    return _clean(_source_summary(rubric).get("verdict"))


def _surface_rejection_reasons(surface: str, *, relation_family: str) -> list[str]:
    reasons: list[str] = []
    if not surface:
        reasons.extend((REASON_SURFACE_CANDIDATE_MISSING, REASON_SOFT_EXPRESSION_MISSING))
        return reasons
    if not _SOFT_MARKER_RE.search(surface):
        reasons.append(REASON_SOFT_EXPRESSION_MISSING)
    if _DIAGNOSIS_RE.search(surface):
        reasons.append(REASON_DIAGNOSIS_SURFACE)
    if _PERSONALITY_CLAIM_RE.search(surface):
        reasons.append(REASON_PERSONALITY_CLAIM_SURFACE)
    if _CAUSE_CLAIM_RE.search(surface):
        reasons.append(REASON_CAUSE_CLAIM_WITHOUT_EVIDENCE_SURFACE)
    if _ADVICE_RE.search(surface):
        reasons.append(REASON_ADVICE_SURFACE)
    if _FUTURE_PREDICTION_RE.search(surface):
        reasons.append(REASON_FUTURE_PREDICTION_SURFACE)
    if _PERIOD_TENDENCY_RE.search(surface) or relation_family == RELATION_PERIOD_TENDENCY_FROM_SINGLE_RECORD:
        reasons.append(REASON_PERIOD_TENDENCY_FROM_SINGLE_RECORD_SURFACE)
    if _TARGET_JUDGEMENT_RE.search(surface) or relation_family == RELATION_TARGET_JUDGEMENT_AGREEMENT:
        reasons.append(REASON_TARGET_JUDGEMENT_AGREEMENT_SURFACE)
    if _TARGET_INTENT_RE.search(surface):
        reasons.append(REASON_TARGET_INTENT_ASSERTION_SURFACE)
    if relation_family == RELATION_SELF_DENIAL_IDENTITY_SPLIT and _SELF_DENIAL_IDENTITY_FACT_RE.search(surface):
        reasons.append(REASON_SELF_DENIAL_IDENTITY_CLAIM_AS_FACT_SURFACE)
    if relation_family == RELATION_LOW_INFORMATION_UNSPECIFIED_WEIGHT and _LOW_INFORMATION_OVERREAD_RE.search(surface):
        reasons.append(REASON_LOW_INFORMATION_OVERREAD_SURFACE)
    if relation_family == RELATION_USER_DICTIONARY_FACT_CLAIM:
        reasons.append(REASON_USER_DICTIONARY_FACT_CLAIM_BLOCKED)
    if relation_family == RELATION_HISTORY_FACT_LINE_AS_INSIGHT or _HISTORY_FACT_ASSERTION_RE.search(surface):
        reasons.append(REASON_HISTORY_FACT_ASSERTION_SURFACE)
    return _dedupe(reasons)


def _meta_rejection_reasons(sources: Iterable[Mapping[str, Any]]) -> list[str]:
    reasons: list[str] = []
    for source in sources:
        if _contains_key(source, _RAW_TEXT_PAYLOAD_KEYS):
            reasons.append(REASON_RAW_TEXT_PAYLOAD_DETECTED)
        if _contains_key(source, _COMMENT_TEXT_PAYLOAD_KEYS):
            reasons.append(REASON_COMMENT_TEXT_BODY_IN_META_DETECTED)
        if _flag_true(source, _PUBLIC_CONTRACT_TRUE_FLAGS):
            reasons.append(REASON_PUBLIC_CONTRACT_MUTATION_DETECTED)
        if _flag_true(source, _GATE_RELAXATION_TRUE_FLAGS):
            reasons.append(REASON_GATE_RELAXATION_DETECTED)
    return _dedupe(reasons)


def _policy_rejection_reasons(visibility_decision: str) -> list[str]:
    if not visibility_decision or visibility_decision == VISIBILITY_ALLOW_INITIAL_VISIBLE:
        return []
    if visibility_decision == VISIBILITY_BLOCKED:
        return [REASON_P6_RELATION_POLICY_BLOCKED]
    if visibility_decision in {VISIBILITY_REVIEW_REQUIRED, VISIBILITY_META_ONLY}:
        return [REASON_P6_RELATION_POLICY_NOT_INITIAL_VISIBLE]
    return [REASON_P6_RELATION_POLICY_NOT_INITIAL_VISIBLE]


def _quality_rejection_reasons(
    verdict: str,
    *,
    visibility_decision: str,
    p6_quality_rubric: Mapping[str, Any],
) -> list[str]:
    if not verdict or verdict in {VERDICT_PASS, VERDICT_STRUCTURE_INSIGHT_READY}:
        return []
    if verdict == VERDICT_RED:
        return [REASON_P6_QUALITY_RUBRIC_RED]
    if verdict == VERDICT_REPAIR_REQUIRED:
        quality_summary = _source_summary(p6_quality_rubric)
        quality_reasons = set(_dedupe(quality_summary.get("decision_reason_codes")))
        policy_review_only = quality_reasons and quality_reasons.issubset(
            {"relation_policy_review_required", REASON_P6_RELATION_POLICY_NOT_INITIAL_VISIBLE}
        )
        if visibility_decision in {VISIBILITY_REVIEW_REQUIRED, VISIBILITY_META_ONLY} and policy_review_only:
            return []
        return [REASON_P6_QUALITY_RUBRIC_REPAIR_REQUIRED]
    return [REASON_P6_QUALITY_RUBRIC_NOT_SAFE_PASS]


def _decision_for(reasons: Iterable[str]) -> str:
    reason_set = set(reasons)
    if reason_set.intersection(_HARD_BLOCK_REASONS):
        return GATE_DECISION_BLOCK_SURFACE_CANDIDATE
    if reason_set:
        return GATE_DECISION_REVIEW_REQUIRED
    return GATE_DECISION_ALLOW_INTERNAL_SURFACE_CANDIDATE


def build_structure_insight_p6_gate_hardening(
    *,
    proposed_surface: Any = "",
    surface_probe: Any = "",
    relation_family: Any = None,
    p6_relation_policy: Mapping[str, Any] | None = None,
    p6_quality_rubric: Mapping[str, Any] | None = None,
    gate_meta: Mapping[str, Any] | None = None,
    user_dictionary_meta: Mapping[str, Any] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Build a body-free P6-5 gate hardening report."""

    run = _safe_id(run_id, default="p6_gate_hardening")
    policy = _safe_mapping(p6_relation_policy)
    quality = _safe_mapping(p6_quality_rubric)
    gate = _safe_mapping(gate_meta)
    dictionary = _safe_mapping(user_dictionary_meta)
    surface = _clean(surface_probe) or _clean(proposed_surface)
    resolved_relation = _relation_family_from_sources(relation_family=relation_family, p6_relation_policy=policy)
    visibility_decision = _visibility_decision_from_policy(policy)
    quality_verdict = _quality_verdict_from_rubric(quality)

    reasons = _dedupe(
        [
            *_meta_rejection_reasons((policy, quality, gate, dictionary)),
            *_surface_rejection_reasons(surface, relation_family=resolved_relation),
            *_policy_rejection_reasons(visibility_decision),
            *_quality_rejection_reasons(
                quality_verdict,
                visibility_decision=visibility_decision,
                p6_quality_rubric=quality,
            ),
        ]
    )
    if _flag_true(
        dictionary,
        frozenset(
            {
                "user_dictionary_used_as_fact",
                "user_dictionary_fact_claim",
                "asserted_from_user_dictionary",
                "user_history_used_as_fact",
                "period_tendency_from_user_dictionary",
            }
        ),
    ):
        reasons = _dedupe([*reasons, REASON_USER_DICTIONARY_FACT_CLAIM_BLOCKED])

    reason_counts = Counter(reasons)
    decision = _decision_for(reasons)
    passed = decision == GATE_DECISION_ALLOW_INTERNAL_SURFACE_CANDIDATE
    blocked = decision == GATE_DECISION_BLOCK_SURFACE_CANDIDATE
    review_required = decision == GATE_DECISION_REVIEW_REQUIRED
    unsafe_surface_blocked = bool(set(reasons).intersection(_UNSAFE_SURFACE_REASONS))

    summary = {
        "schema_version": STRUCTURE_INSIGHT_P6_GATE_HARDENING_SUMMARY_SCHEMA_VERSION,
        "version": STRUCTURE_INSIGHT_P6_GATE_HARDENING_SUMMARY_SCHEMA_VERSION,
        "source": STRUCTURE_INSIGHT_P6_GATE_HARDENING_SOURCE,
        "step": STRUCTURE_INSIGHT_P6_GATE_HARDENING_STEP,
        "run_id": run,
        "p6_gate_hardening_ready": True,
        "gate_hardening_only": True,
        "relation_family": resolved_relation,
        "p6_relation_policy_visibility_decision": visibility_decision,
        "p6_quality_rubric_verdict": quality_verdict,
        "decision": decision,
        "passed": passed,
        "blocked": blocked,
        "review_required": review_required,
        "surface_candidate_evaluated": bool(surface),
        "surface_body_returned": False,
        "candidate_body_returned": False,
        "soft_expression_required": True,
        "soft_expression_required_enforced": True,
        "soft_expression_marker_detected": bool(_SOFT_MARKER_RE.search(surface)) if surface else False,
        "soft_expression_missing_blocked": REASON_SOFT_EXPRESSION_MISSING in reason_counts,
        "unsafe_insight_surface_blocked": unsafe_surface_blocked,
        "diagnosis_surface_blocked": REASON_DIAGNOSIS_SURFACE in reason_counts,
        "personality_claim_surface_blocked": REASON_PERSONALITY_CLAIM_SURFACE in reason_counts,
        "cause_claim_without_evidence_surface_blocked": REASON_CAUSE_CLAIM_WITHOUT_EVIDENCE_SURFACE in reason_counts,
        "advice_surface_blocked": REASON_ADVICE_SURFACE in reason_counts,
        "future_prediction_surface_blocked": REASON_FUTURE_PREDICTION_SURFACE in reason_counts,
        "period_tendency_from_single_record_surface_blocked": REASON_PERIOD_TENDENCY_FROM_SINGLE_RECORD_SURFACE in reason_counts,
        "target_judgement_agreement_surface_blocked": REASON_TARGET_JUDGEMENT_AGREEMENT_SURFACE in reason_counts,
        "target_intent_assertion_surface_blocked": REASON_TARGET_INTENT_ASSERTION_SURFACE in reason_counts,
        "self_denial_identity_claim_as_fact_surface_blocked": (
            REASON_SELF_DENIAL_IDENTITY_CLAIM_AS_FACT_SURFACE in reason_counts
        ),
        "low_information_overread_surface_blocked": REASON_LOW_INFORMATION_OVERREAD_SURFACE in reason_counts,
        "user_dictionary_fact_claim_blocked": REASON_USER_DICTIONARY_FACT_CLAIM_BLOCKED in reason_counts,
        "history_fact_assertion_surface_blocked": REASON_HISTORY_FACT_ASSERTION_SURFACE in reason_counts,
        "raw_text_payload_blocked": REASON_RAW_TEXT_PAYLOAD_DETECTED in reason_counts,
        "comment_text_body_in_meta_blocked": REASON_COMMENT_TEXT_BODY_IN_META_DETECTED in reason_counts,
        "public_contract_mutation_blocked": REASON_PUBLIC_CONTRACT_MUTATION_DETECTED in reason_counts,
        "gate_relaxation_blocked": REASON_GATE_RELAXATION_DETECTED in reason_counts,
        "comment_text_written_by_gate": False,
        "comment_text_generated": False,
        "comment_text_key_written": False,
        "public_response_key_added": False,
        "rn_visible_contract_changed": False,
        "response_shape_changed": False,
        "release_allowed": False,
        "public_release_applied": False,
        "decision_reason_codes": reasons,
        "decision_reason_counts": dict(reason_counts),
        "soft_marker_examples": list(_SOFT_MARKER_EXAMPLES),
        "public_contract": _public_contract(),
        "body_free": _body_free_contract(),
    }
    report = {
        "schema_version": STRUCTURE_INSIGHT_P6_GATE_HARDENING_SCHEMA_VERSION,
        "version": STRUCTURE_INSIGHT_P6_GATE_HARDENING_SCHEMA_VERSION,
        "source": STRUCTURE_INSIGHT_P6_GATE_HARDENING_SOURCE,
        "step": STRUCTURE_INSIGHT_P6_GATE_HARDENING_STEP,
        "run_id": run,
        "p6_gate_hardening_ready": True,
        "gate_hardening_only": True,
        "decision": decision,
        "passed": passed,
        "blocked": blocked,
        "review_required": review_required,
        "relation_family": resolved_relation,
        "p6_relation_policy_visibility_decision": visibility_decision,
        "p6_quality_rubric_verdict": quality_verdict,
        "surface_candidate_evaluated": bool(surface),
        "soft_expression_required": True,
        "soft_expression_required_enforced": True,
        "soft_expression_marker_detected": bool(_SOFT_MARKER_RE.search(surface)) if surface else False,
        "soft_expression_missing_blocked": REASON_SOFT_EXPRESSION_MISSING in reason_counts,
        "unsafe_insight_surface_blocked": unsafe_surface_blocked,
        "decision_reason_codes": reasons,
        "decision_reason_counts": dict(reason_counts),
        "comment_text_written_by_gate": False,
        "comment_text_generated": False,
        "comment_text_key_written": False,
        "surface_body_returned": False,
        "candidate_body_returned": False,
        "public_response_key_added": False,
        "rn_visible_contract_changed": False,
        "response_shape_changed": False,
        "release_allowed": False,
        "public_release_applied": False,
        "public_contract": _public_contract(),
        "body_free": _body_free_contract(),
        "summary": summary,
    }
    assert_structure_insight_p6_gate_hardening_contract(report)
    return report


def assert_structure_insight_p6_gate_hardening_contract(
    report: Mapping[str, Any],
    *,
    allow_partial: bool = False,
) -> bool:
    """Validate that a P6-5 gate hardening report stays body-free."""

    if not isinstance(report, Mapping):
        raise TypeError("P6 gate hardening report must be a mapping")
    data = _safe_mapping(report)
    if not allow_partial and data.get("schema_version") != STRUCTURE_INSIGHT_P6_GATE_HARDENING_SCHEMA_VERSION:
        raise ValueError("Unexpected P6 gate hardening schema version")
    if not allow_partial and data.get("step") != STRUCTURE_INSIGHT_P6_GATE_HARDENING_STEP:
        raise ValueError("Unexpected P6 gate hardening step")
    if _contains_key(data, _TEXT_PAYLOAD_KEYS):
        raise ValueError("P6 gate hardening report must not include text body keys")
    if _flag_true(data, _FORBIDDEN_TRUE_FLAGS):
        raise ValueError("P6 gate hardening report contains forbidden true flags")
    public_contract = _safe_mapping(data.get("public_contract"))
    body_free = _safe_mapping(data.get("body_free"))
    if public_contract and _flag_true(public_contract, _PUBLIC_CONTRACT_TRUE_FLAGS):
        raise ValueError("P6 gate hardening report mutates public contract")
    if body_free and _flag_true(body_free, _FORBIDDEN_TRUE_FLAGS):
        raise ValueError("P6 gate hardening report includes body payload flags")
    summary = _safe_mapping(data.get("summary"))
    if summary:
        if not allow_partial and summary.get("schema_version") != STRUCTURE_INSIGHT_P6_GATE_HARDENING_SUMMARY_SCHEMA_VERSION:
            raise ValueError("Unexpected P6 gate hardening summary schema version")
        if _contains_key(summary, _TEXT_PAYLOAD_KEYS):
            raise ValueError("P6 gate hardening summary must not include text body keys")
        if _flag_true(summary, _FORBIDDEN_TRUE_FLAGS):
            raise ValueError("P6 gate hardening summary contains forbidden true flags")
    return True


def dump_structure_insight_p6_gate_hardening_public_summary(report: Mapping[str, Any]) -> str:
    """Serialize the body-free P6-5 summary for review artifacts."""

    data = _safe_mapping(report)
    assert_structure_insight_p6_gate_hardening_contract(data)
    summary = _safe_mapping(data.get("summary")) or data
    assert_structure_insight_p6_gate_hardening_contract(summary, allow_partial=True)
    safe_summary = {
        "schema_version": summary.get("schema_version"),
        "step": summary.get("step"),
        "run_id": summary.get("run_id"),
        "decision": summary.get("decision"),
        "passed": summary.get("passed"),
        "blocked": summary.get("blocked"),
        "review_required": summary.get("review_required"),
        "relation_family": summary.get("relation_family"),
        "p6_relation_policy_visibility_decision": summary.get("p6_relation_policy_visibility_decision"),
        "p6_quality_rubric_verdict": summary.get("p6_quality_rubric_verdict"),
        "soft_expression_required_enforced": summary.get("soft_expression_required_enforced"),
        "soft_expression_marker_detected": summary.get("soft_expression_marker_detected"),
        "unsafe_insight_surface_blocked": summary.get("unsafe_insight_surface_blocked"),
        "comment_text_written_by_gate": False,
        "public_response_key_added": False,
        "decision_reason_codes": list(summary.get("decision_reason_codes") or []),
        "body_free": _safe_mapping(summary.get("body_free")),
        "public_contract": _safe_mapping(summary.get("public_contract")),
    }
    assert_structure_insight_p6_gate_hardening_contract(safe_summary, allow_partial=True)
    return json.dumps(safe_summary, ensure_ascii=False, sort_keys=True)
