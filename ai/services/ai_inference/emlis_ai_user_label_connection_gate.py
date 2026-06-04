# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase 5 User Label Connection Gate for EmlisAI.

The gate evaluates whether Phase 4 User Label Connection candidates may advance
only to a later Surface Plan.  It is backend-internal and meta-only: it never
writes ``comment_text``, never adds public response keys, never changes RN/API/DB
contracts, and does not relax the existing Structure Insight Gate.
"""

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
import json
import re
from typing import Any, Final

from emlis_ai_user_label_connection_candidate import (
    CANDIDATE_QUALITY_BLOCKED,
    CANDIDATE_QUALITY_GATE_CANDIDATE,
    CANDIDATE_QUALITY_INSUFFICIENT_EVIDENCE,
    FORBIDDEN_CLAIMS,
    USER_LABEL_CONNECTION_CANDIDATE_SCHEMA_VERSION,
    build_user_label_connection_candidates,
)
from emlis_ai_user_label_connection_types import (
    MATERIAL_QUALITY_LOW_INFORMATION_PROTECTED,
    MATERIAL_QUALITY_SAFETY_TRIAGE_REQUIRED,
    RECORD_SCOPE_BLOCKED_FREE_TIER,
    RECORD_SCOPE_BLOCKED_GROUNDING_BOUNDARY,
    SOURCE_SCOPE_CURRENT_ONLY,
    SOURCE_SCOPE_OWNED_HISTORY,
    SOURCE_SCOPE_OWNED_HISTORY_AND_CROSS_CORE,
)

USER_LABEL_CONNECTION_GATE_SCHEMA_VERSION: Final = "cocolon.emlis.user_label_connection_gate.v1"
USER_LABEL_CONNECTION_GATE_STEP: Final = "UserLabelConnection_Gate_v1"

GATE_ACTION_ALLOW_LIMITED_SURFACE_PLAN: Final = "allow_limited_surface_plan"
GATE_ACTION_BLOCK_SURFACE_PLAN: Final = "block_surface_plan"
GATE_ACTION_META_ONLY: Final = "meta_only"
GATE_ACTION_NO_CANDIDATE: Final = "no_candidate"

MINIMUM_EVIDENCE_RECORD_COUNT: Final = 2

REJECTION_FREE_HISTORY_BLOCKED: Final = "free_history_blocked"
REJECTION_USER_FACT_GROUNDING_BOUNDARY_BLOCKED: Final = "user_fact_grounding_boundary_blocked"
REJECTION_LOW_INFORMATION_HISTORY_PROMOTION_BLOCKED: Final = "low_information_history_promotion_blocked"
REJECTION_CURRENT_INPUT_MISSING: Final = "current_input_missing"
REJECTION_HISTORY_RECORD_COUNT_INSUFFICIENT: Final = "history_record_count_insufficient"
REJECTION_SOURCE_SCOPE_MARKER_MISSING: Final = "source_scope_marker_missing"
REJECTION_SOFT_MARKER_MISSING: Final = "soft_marker_missing"
REJECTION_RAW_TEXT_PAYLOAD_DETECTED: Final = "raw_text_payload_detected"
REJECTION_COMMENT_TEXT_BODY_IN_META_DETECTED: Final = "comment_text_body_in_meta_detected"
REJECTION_PERIOD_TENDENCY_FROM_SINGLE_RECORD: Final = "period_tendency_from_single_record"
REJECTION_PERSONALITY_CLAIM_SURFACE: Final = "personality_claim_surface"
REJECTION_DIAGNOSIS_SURFACE: Final = "diagnosis_surface"
REJECTION_CAUSE_CLAIM_WITHOUT_EVIDENCE_SURFACE: Final = "cause_claim_without_evidence_surface"
REJECTION_ADVICE_SURFACE: Final = "advice_surface"
REJECTION_FUTURE_PREDICTION_SURFACE: Final = "future_prediction_surface"
REJECTION_ALWAYS_CLAIM_SURFACE: Final = "always_claim_surface"
REJECTION_SHOULD_STATEMENT_SURFACE: Final = "should_statement_surface"
REJECTION_SAFETY_ADJACENT_HISTORY_CONNECTION_BLOCKED: Final = "safety_adjacent_history_connection_blocked"
REJECTION_SELF_DENIAL_IDENTITY_CLAIM_BLOCKED: Final = "self_denial_identity_claim_blocked"
REJECTION_TARGET_JUDGEMENT_AGREEMENT_BLOCKED: Final = "target_judgement_agreement_blocked"

_ALLOWED_ACTIONS: Final = frozenset(
    {
        GATE_ACTION_ALLOW_LIMITED_SURFACE_PLAN,
        GATE_ACTION_BLOCK_SURFACE_PLAN,
        GATE_ACTION_META_ONLY,
        GATE_ACTION_NO_CANDIDATE,
    }
)
_ALLOWED_SOURCE_SCOPES: Final = frozenset(
    {SOURCE_SCOPE_CURRENT_ONLY, SOURCE_SCOPE_OWNED_HISTORY, SOURCE_SCOPE_OWNED_HISTORY_AND_CROSS_CORE}
)
_ALLOWED_CANDIDATE_QUALITIES: Final = frozenset(
    {CANDIDATE_QUALITY_INSUFFICIENT_EVIDENCE, CANDIDATE_QUALITY_GATE_CANDIDATE, CANDIDATE_QUALITY_BLOCKED}
)
_ALLOWED_TIERS: Final = frozenset({"free", "plus", "premium"})

_SCOPE_MARKER_RE: Final = re.compile(
    r"(?:この期間の記録では|以前の近い記録にも|今回と近い記録の範囲では|残っている記録を並べると|Emlisから見える範囲では)"
)
_SOFT_MARKER_RE: Final = re.compile(
    r"(?:ように見えます|ように思います|かもしれません|近い形に見えます|線として見え始めています|ようにも見えます|のかもしれません)"
)
_DIAGNOSIS_RE: Final = re.compile(r"(?:診断|診断すると|治療|病気|症状|障害|ADHD|うつ|鬱|PTSD|トラウマ|医学的|心理学的)")
_PERSONALITY_RE: Final = re.compile(
    r"(?:あなたは[^。！？!?\n]{0,32}(?:こういう人|人です|タイプです|性格です|本質です|弱い人|ダメな人|駄目な人)|性格(?:です|だから|として))"
)
_CAUSE_RE: Final = re.compile(r"(?:原因は|原因です|原因になっています|本当の原因|理由はひとつ|カテゴリが原因|感情の強さが原因|だから本当は)")
_ADVICE_RE: Final = re.compile(
    r"(?:ください|してください|しましょう|しなければ|しなくてはいけません|必要があります|方がいい|決めましょう|相談しましょう)"
)
_SHOULD_RE: Final = re.compile(r"(?:こうするべき|するべき|すべき|べき|should|must)", re.IGNORECASE)
_FUTURE_RE: Final = re.compile(r"(?:今後も|これからも|必ずまた|また同じように|続いていきます|治ります|治りません|回復します)")
_ALWAYS_RE: Final = re.compile(r"(?:いつも|毎回|ずっと|必ず|絶対に|たびに|度に|なりやすい|しやすい|出やすい|パターンです|傾向です)")
_SELF_DENIAL_RE: Final = re.compile(
    r"(?:あなたは[^。！？!?\n]{0,24}(?:自分を責める人|変われない|何もできない|価値がない|ダメ|駄目)|自己否定があなたの性格|価値がない状態です)"
)
_TARGET_JUDGEMENT_RE: Final = re.compile(
    r"(?:(?:相手|あの人|その人|彼|彼女|上司|会社|職場)[^。！？!?\n]{0,28}(?:悪い|ひどい|最低|おかしい|敵|見下している|軽く見ている)|相手が悪い|上司が悪い|あなたの怒りは正しい)"
)
_TARGET_INTENT_RE: Final = re.compile(
    r"(?:(?:相手|あの人|その人|彼|彼女|上司|会社|職場)[^。！？!?\n]{0,28}(?:思っています|思っている|考えています|考えている|わざと|意図して|見下しています|軽く見ています))"
)

_TEXT_PAYLOAD_KEYS: Final = frozenset(
    {
        "raw_input",
        "rawInput",
        "raw_text",
        "rawText",
        "raw_user_text",
        "rawUserText",
        "source_text",
        "sourceText",
        "input",
        "input_text",
        "inputText",
        "user_input",
        "userInput",
        "current_input",
        "currentInput",
        "history_input",
        "historyInput",
        "memo",
        "memo_text",
        "memoText",
        "memo_action",
        "memoAction",
        "memo_action_text",
        "memoActionText",
        "thought_text",
        "thoughtText",
        "action_text",
        "actionText",
        "comment_text",
        "commentText",
        "comment_text_body",
        "commentTextBody",
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
        "realized_text",
        "realizedText",
        "display_text",
        "observation_text",
        "reception_text",
        "internal_question_body",
        "private_user_dictionary_text",
        "body",
        "text",
    }
)
_COMMENT_BODY_KEYS: Final = frozenset({"comment_text_body", "commentTextBody"})
_FORBIDDEN_TRUE_FLAGS: Final = frozenset(
    {
        "api_route_changed",
        "request_key_changed",
        "response_shape_changed",
        "public_response_key_added",
        "public_payload_changed",
        "db_physical_name_changed",
        "rn_visible_contract_changed",
        "rn_visible_title_changed",
        "structure_insight_gate_relaxed",
        "display_gate_relaxed",
        "grounding_gate_relaxed",
        "reader_gate_relaxed",
        "template_gate_relaxed",
        "gate_relaxed",
        "existing_gate_relaxed",
        "raw_input_included",
        "raw_text_included",
        "history_raw_text_included",
        "raw_fact_text_included",
        "comment_text_body_included",
        "candidate_body_included",
        "surface_body_included",
        "internal_question_body_included",
        "private_user_dictionary_text_included",
        "record_ids_included",
        "comment_text_generated",
        "comment_text_written_by_gate",
        "comment_text_generated_by_this_layer",
        "fixed_sentence_template_added",
        "diagnosis_allowed",
        "personality_claim_allowed",
        "cause_claim_allowed",
        "advice_allowed",
        "future_prediction_allowed",
        "always_claim_allowed",
        "should_statement_allowed",
        "target_judgement_agreement_allowed",
        "period_tendency_from_single_record_allowed",
        "user_dictionary_fact_claim_allowed",
        "external_ai_added",
        "local_llm_added",
        "public_release_applied",
    }
)
_LOW_INFORMATION_MARKERS: Final = frozenset({"low_information", "insufficient_information", MATERIAL_QUALITY_LOW_INFORMATION_PROTECTED})
_SAFETY_MARKERS: Final = frozenset({"safety_triage_required", "safety_blocked", "emergency_safety_required", MATERIAL_QUALITY_SAFETY_TRIAGE_REQUIRED})
_SELF_DENIAL_MARKERS: Final = frozenset({"self_denial", "self_denial_context", "self_denial_safe_state_answer", "self_denial_identity", "identity_claim_as_fact"})
_TARGET_JUDGEMENT_MARKERS: Final = frozenset({"target_judgement", "target_judgement_context", "anger_or_boundary", "anger_or_boundary_strict_context", "opponent_intent_claim", "target_attack_agreement"})


def _clean(value: Any) -> str:
    if value is None or isinstance(value, (Mapping, list, tuple, set)):
        return ""
    return re.sub(r"\s+", " ", str(value).replace("\u3000", " ").replace("\r", " ").replace("\n", " ")).strip()


def _safe_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    as_meta = getattr(value, "as_meta", None)
    if callable(as_meta):
        meta = as_meta()
        if isinstance(meta, Mapping):
            return {str(key): item for key, item in meta.items()}
    return {}


def _listify(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        return [value]
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


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _contains_text_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key) in _TEXT_PAYLOAD_KEYS:
                return True
            if _contains_text_payload_key(item):
                return True
    elif isinstance(value, (list, tuple, set)):
        return any(_contains_text_payload_key(item) for item in value)
    return False


def _contains_comment_body_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized = str(key)
            if normalized in _COMMENT_BODY_KEYS:
                return True
            if normalized in {"comment_text_body_included", "commentTextBodyIncluded", "comment_text_body_in_meta", "comment_text_body_detected"} and item is True:
                return True
            if _contains_comment_body_key(item):
                return True
    elif isinstance(value, (list, tuple, set)):
        return any(_contains_comment_body_key(item) for item in value)
    return False


def _flag_true(value: Any, names: Iterable[str]) -> bool:
    wanted = {str(name) for name in names}
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key) in wanted and item is True:
                return True
            if _flag_true(item, wanted):
                return True
    elif isinstance(value, (list, tuple, set)):
        return any(_flag_true(item, wanted) for item in value)
    return False


def _has_marker(value: Any, markers: frozenset[str]) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if _clean(key).lower() in markers:
                return True
            if _has_marker(item, markers):
                return True
    elif isinstance(value, (list, tuple, set)):
        return any(_has_marker(item, markers) for item in value)
    elif _clean(value).lower() in markers:
        return True
    return False


def _as_material_meta(material: Any) -> dict[str, Any]:
    return _safe_mapping(material)


def _normalize_tier(*, material_meta: Mapping[str, Any], capability: Any = None, subscription_tier: Any = None) -> str:
    for value in (
        subscription_tier,
        getattr(capability, "tier", None),
        getattr(capability, "subscription_tier", None),
        material_meta.get("capability_tier"),
    ):
        text = _clean(value).lower()
        if text in _ALLOWED_TIERS:
            return text
        if text in {"subscription", "subscriber"}:
            return "plus"
    if getattr(capability, "cross_core_enabled", False):
        return "premium"
    if getattr(capability, "model_read_enabled", False) or getattr(capability, "include_derived_user_model", False):
        return "plus"
    return "free"


def _candidate_metas_from_inputs(
    candidates: Any = None,
    *,
    candidate: Any = None,
    material: Any = None,
    max_candidates: int = 4,
) -> list[dict[str, Any]]:
    values: list[Any] = []
    if candidate is not None:
        values.append(candidate)
    if candidates is not None:
        if isinstance(candidates, Mapping) or callable(getattr(candidates, "as_meta", None)):
            values.append(candidates)
        else:
            values.extend(_listify(candidates))
    if not values and material is not None:
        try:
            values.extend(build_user_label_connection_candidates(material, max_candidates=max_candidates))
        except Exception:
            values = []
    metas = [_safe_mapping(value) for value in values]
    return [meta for meta in metas if meta]


def _candidate_evidence(candidate_meta: Mapping[str, Any]) -> dict[str, Any]:
    return _safe_mapping(candidate_meta.get("evidence"))


def _candidate_surface_permission(candidate_meta: Mapping[str, Any]) -> dict[str, Any]:
    return _safe_mapping(candidate_meta.get("surface_permission"))


def _source_scope(candidate_meta: Mapping[str, Any], material_meta: Mapping[str, Any]) -> str:
    value = _clean(candidate_meta.get("source_scope")) or _clean(material_meta.get("source_scope"))
    return value if value in _ALLOWED_SOURCE_SCOPES else SOURCE_SCOPE_CURRENT_ONLY


def _user_fact_boundary_passed(material_meta: Mapping[str, Any]) -> bool:
    if material_meta.get("record_scope") == RECORD_SCOPE_BLOCKED_GROUNDING_BOUNDARY:
        return False
    if material_meta.get("user_fact_grounding_boundary_passed") is False:
        return False
    if material_meta.get("user_fact_read_enabled") is False:
        return False
    if material_meta.get("user_fact_may_promote_to_eligible") is True:
        return False
    return True


def _low_information_protected(material_meta: Mapping[str, Any], observation_reply_meta: Mapping[str, Any]) -> bool:
    if material_meta.get("low_information_protected") is True:
        return True
    for key in ("material_quality", "eligibility_status", "observation_reply_kind", "status"):
        if _clean(material_meta.get(key)).lower() in _LOW_INFORMATION_MARKERS:
            return True
        if _clean(observation_reply_meta.get(key)).lower() in _LOW_INFORMATION_MARKERS:
            return True
    if observation_reply_meta.get("eligible_for_full_observation") is False and observation_reply_meta.get("question_required") is True:
        return True
    return False


def _safety_context(material_meta: Mapping[str, Any], observation_reply_meta: Mapping[str, Any]) -> bool:
    for key in ("material_quality", "safety_triage_kind", "eligibility_status", "observation_status", "status"):
        if _clean(material_meta.get(key)).lower() in _SAFETY_MARKERS:
            return True
        if _clean(observation_reply_meta.get(key)).lower() in _SAFETY_MARKERS:
            return True
    return False


def _strict_context_rejection_reasons(material_meta: Mapping[str, Any], observation_reply_meta: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    if _has_marker(material_meta, _SELF_DENIAL_MARKERS) or _has_marker(observation_reply_meta, _SELF_DENIAL_MARKERS):
        reasons.append(REJECTION_SELF_DENIAL_IDENTITY_CLAIM_BLOCKED)
    if _has_marker(material_meta, _TARGET_JUDGEMENT_MARKERS) or _has_marker(observation_reply_meta, _TARGET_JUDGEMENT_MARKERS):
        reasons.append(REJECTION_TARGET_JUDGEMENT_AGREEMENT_BLOCKED)
    return _dedupe(reasons)


def _claim_surface_rejection_reasons(surface: str) -> list[str]:
    if not surface:
        return []
    reasons: list[str] = []
    if _ALWAYS_RE.search(surface):
        reasons.append(REJECTION_ALWAYS_CLAIM_SURFACE)
    if _FUTURE_RE.search(surface):
        reasons.append(REJECTION_FUTURE_PREDICTION_SURFACE)
    if _DIAGNOSIS_RE.search(surface):
        reasons.append(REJECTION_DIAGNOSIS_SURFACE)
    if _PERSONALITY_RE.search(surface):
        reasons.append(REJECTION_PERSONALITY_CLAIM_SURFACE)
    if _CAUSE_RE.search(surface):
        reasons.append(REJECTION_CAUSE_CLAIM_WITHOUT_EVIDENCE_SURFACE)
    if _ADVICE_RE.search(surface):
        reasons.append(REJECTION_ADVICE_SURFACE)
    if _SHOULD_RE.search(surface):
        reasons.append(REJECTION_SHOULD_STATEMENT_SURFACE)
    if _SELF_DENIAL_RE.search(surface):
        reasons.append(REJECTION_SELF_DENIAL_IDENTITY_CLAIM_BLOCKED)
    if _TARGET_JUDGEMENT_RE.search(surface) or _TARGET_INTENT_RE.search(surface):
        reasons.append(REJECTION_TARGET_JUDGEMENT_AGREEMENT_BLOCKED)
    return _dedupe(reasons)


def _marker_rejection_reasons(surface: str) -> list[str]:
    if not surface:
        return []
    reasons: list[str] = []
    if not _SCOPE_MARKER_RE.search(surface):
        reasons.append(REJECTION_SOURCE_SCOPE_MARKER_MISSING)
    if not _SOFT_MARKER_RE.search(surface):
        reasons.append(REJECTION_SOFT_MARKER_MISSING)
    return reasons


def _merge_probe_meta(*metas: Mapping[str, Any] | None) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for index, meta in enumerate(metas, start=1):
        item = _safe_mapping(meta)
        if item:
            merged[f"probe_meta_{index}"] = item
    return merged


def _runtime_adjusted_metas(
    *,
    material: Any = None,
    explicit_material_meta: Mapping[str, Any] | None = None,
    observation_reply_meta: Mapping[str, Any] | None = None,
    capability_tier: Any = None,
    user_fact_grounding_boundary_passed: bool | None = None,
    low_information: bool | None = None,
    safety_adjacent: bool = False,
    self_denial_context: bool = False,
    target_judgement_context: bool = False,
    safety_context_reasons: Sequence[Any] | None = None,
    surface_candidate_meta: Mapping[str, Any] | None = None,
    public_meta: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], Any]:
    material_meta = _as_material_meta(material)
    material_meta.update(_safe_mapping(explicit_material_meta))
    observation_meta = _safe_mapping(observation_reply_meta)
    surface_meta = _merge_probe_meta(surface_candidate_meta, public_meta)
    override_tier = capability_tier
    if capability_tier is not None:
        material_meta["capability_tier"] = _clean(capability_tier).lower()
    if user_fact_grounding_boundary_passed is not None:
        material_meta["user_fact_grounding_boundary_passed"] = bool(user_fact_grounding_boundary_passed)
    if low_information is True:
        material_meta["low_information_protected"] = True
        material_meta.setdefault("material_quality", MATERIAL_QUALITY_LOW_INFORMATION_PROTECTED)
    reason_values = set(_clean(item).lower() for item in _listify(safety_context_reasons))
    if safety_adjacent or "safety_adjacent" in reason_values or "safety" in reason_values:
        observation_meta["safety_triage_kind"] = "safety_triage_required"
    if self_denial_context or "self_denial" in reason_values or "self_denial_context" in reason_values:
        observation_meta["self_denial"] = True
    if target_judgement_context or "target_judgement" in reason_values or "target_judgement_context" in reason_values:
        observation_meta["target_judgement"] = True
    return material_meta, observation_meta, surface_meta, override_tier


def _evidence_contract(candidate_meta: Mapping[str, Any]) -> dict[str, Any]:
    evidence = _candidate_evidence(candidate_meta)
    return {
        "evidence_record_count": _int(evidence.get("evidence_record_count")),
        "minimum_evidence_record_count": MINIMUM_EVIDENCE_RECORD_COUNT,
        "current_record_included": evidence.get("current_record_included") is True,
        "history_record_count": _int(evidence.get("history_record_count")),
        "period_tendency_from_single_record_allowed": False,
    }


def _empty_evidence_contract() -> dict[str, Any]:
    return {
        "evidence_record_count": 0,
        "minimum_evidence_record_count": MINIMUM_EVIDENCE_RECORD_COUNT,
        "current_record_included": False,
        "history_record_count": 0,
        "period_tendency_from_single_record_allowed": False,
    }


def _required_surface_markers() -> dict[str, bool]:
    return {
        "scope_marker_required": True,
        "soft_marker_required": True,
        "advice_marker_forbidden": True,
        "future_prediction_forbidden": True,
    }


def _public_contract() -> dict[str, bool]:
    return {
        "api_route_changed": False,
        "request_key_changed": False,
        "response_shape_changed": False,
        "public_response_key_added": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "comment_text_body_included": False,
        "raw_input_included": False,
        "raw_text_included": False,
    }


def _claim_contract() -> dict[str, bool]:
    return {
        "diagnosis_allowed": False,
        "personality_claim_allowed": False,
        "cause_claim_allowed": False,
        "advice_allowed": False,
        "future_prediction_allowed": False,
        "always_claim_allowed": False,
        "should_statement_allowed": False,
    }


def _capability_contract(*, tier: str, material_meta: Mapping[str, Any], candidate_meta: Mapping[str, Any] | None = None) -> dict[str, Any]:
    source_scope = _source_scope(candidate_meta or {}, material_meta)
    return {
        "tier": tier,
        "free_history_used": False,
        "owned_history_only": source_scope in {SOURCE_SCOPE_OWNED_HISTORY, SOURCE_SCOPE_OWNED_HISTORY_AND_CROSS_CORE},
        "user_fact_grounding_boundary_passed": _user_fact_boundary_passed(material_meta),
    }


def _decorate_gate_meta(meta: dict[str, Any]) -> dict[str, Any]:
    reasons = set(_dedupe(meta.get("rejection_reasons") or []))
    unsafe_reasons = {
        REJECTION_ALWAYS_CLAIM_SURFACE,
        REJECTION_CAUSE_CLAIM_WITHOUT_EVIDENCE_SURFACE,
        REJECTION_PERSONALITY_CLAIM_SURFACE,
        REJECTION_DIAGNOSIS_SURFACE,
        REJECTION_ADVICE_SURFACE,
        REJECTION_FUTURE_PREDICTION_SURFACE,
        REJECTION_SHOULD_STATEMENT_SURFACE,
        REJECTION_SAFETY_ADJACENT_HISTORY_CONNECTION_BLOCKED,
        REJECTION_SELF_DENIAL_IDENTITY_CLAIM_BLOCKED,
        REJECTION_TARGET_JUDGEMENT_AGREEMENT_BLOCKED,
    }
    meta.update(
        {
            "gate_is_independent_from_structure_insight_gate": True,
            "independent_user_label_connection_gate": True,
            "user_label_connection_gate_independent": True,
            "surface_plan_deferred_to_phase6": True,
            "public_surface_connected": False,
            "history_connection_applied": bool(meta.get("passed") is True),
            "history_connection_blocked": bool(meta.get("blocked") is True),
            "scope_marker_missing_blocked": REJECTION_SOURCE_SCOPE_MARKER_MISSING in reasons,
            "soft_marker_missing_blocked": REJECTION_SOFT_MARKER_MISSING in reasons,
            "low_information_history_promotion_blocked": REJECTION_LOW_INFORMATION_HISTORY_PROMOTION_BLOCKED in reasons,
            "unsafe_history_surface_blocked": bool(reasons & unsafe_reasons),
        }
    )
    return meta


def _candidate_rejection_reasons(
    *,
    candidate_meta: Mapping[str, Any],
    material_meta: Mapping[str, Any],
    observation_reply_meta: Mapping[str, Any],
    surface_candidate_meta: Mapping[str, Any],
    surface: str,
    tier: str,
) -> list[str]:
    reasons: list[str] = []
    evidence = _candidate_evidence(candidate_meta)
    permission = _candidate_surface_permission(candidate_meta)
    source_scope = _source_scope(candidate_meta, material_meta)
    quality = _clean(candidate_meta.get("candidate_quality"))
    if quality not in _ALLOWED_CANDIDATE_QUALITIES:
        reasons.append("candidate_quality_invalid")

    requires_history = candidate_meta.get("requires_user_history") is True or source_scope != SOURCE_SCOPE_CURRENT_ONLY
    if tier == "free" and requires_history:
        reasons.append(REJECTION_FREE_HISTORY_BLOCKED)
    if material_meta.get("record_scope") == RECORD_SCOPE_BLOCKED_FREE_TIER:
        reasons.append(REJECTION_FREE_HISTORY_BLOCKED)

    if not _user_fact_boundary_passed(material_meta):
        reasons.append(REJECTION_USER_FACT_GROUNDING_BOUNDARY_BLOCKED)
    if _low_information_protected(material_meta, observation_reply_meta):
        reasons.append(REJECTION_LOW_INFORMATION_HISTORY_PROMOTION_BLOCKED)
    if _safety_context(material_meta, observation_reply_meta):
        reasons.append(REJECTION_SAFETY_ADJACENT_HISTORY_CONNECTION_BLOCKED)
    reasons.extend(_strict_context_rejection_reasons(material_meta, observation_reply_meta))

    evidence_record_count = _int(evidence.get("evidence_record_count"))
    current_record_included = evidence.get("current_record_included") is True
    history_record_count = _int(evidence.get("history_record_count"))
    if not current_record_included:
        reasons.append(REJECTION_CURRENT_INPUT_MISSING)
    if evidence_record_count < MINIMUM_EVIDENCE_RECORD_COUNT or history_record_count < 1:
        reasons.append(REJECTION_HISTORY_RECORD_COUNT_INSUFFICIENT)
    if quality == CANDIDATE_QUALITY_BLOCKED:
        reasons.append("candidate_blocked_before_gate")
    if permission and permission.get("may_surface_after_user_label_connection_gate") is not True:
        if quality == CANDIDATE_QUALITY_GATE_CANDIDATE:
            reasons.append("candidate_surface_permission_blocked")
    if permission and permission.get("must_use_scope_marker") is not True:
        reasons.append(REJECTION_SOURCE_SCOPE_MARKER_MISSING)
    if permission and permission.get("must_use_soft_expression") is not True:
        reasons.append(REJECTION_SOFT_MARKER_MISSING)

    missing_forbidden = set(FORBIDDEN_CLAIMS) - set(_dedupe(candidate_meta.get("forbidden_claims") or []))
    if missing_forbidden:
        reasons.append("forbidden_claim_policy_incomplete")

    if _contains_text_payload_key(candidate_meta) or _contains_text_payload_key(material_meta) or _contains_text_payload_key(surface_candidate_meta):
        reasons.append(REJECTION_RAW_TEXT_PAYLOAD_DETECTED)
    if _flag_true(candidate_meta, _FORBIDDEN_TRUE_FLAGS) or _flag_true(material_meta, _FORBIDDEN_TRUE_FLAGS) or _flag_true(surface_candidate_meta, _FORBIDDEN_TRUE_FLAGS):
        reasons.append(REJECTION_RAW_TEXT_PAYLOAD_DETECTED)
    if _contains_comment_body_key(candidate_meta) or _contains_comment_body_key(material_meta) or _contains_comment_body_key(surface_candidate_meta):
        reasons.append(REJECTION_COMMENT_TEXT_BODY_IN_META_DETECTED)

    if surface:
        reasons.extend(_marker_rejection_reasons(surface))
        reasons.extend(_claim_surface_rejection_reasons(surface))
        if evidence_record_count <= 1 and (_ALWAYS_RE.search(surface) or "記録" in surface or "線" in surface):
            reasons.append(REJECTION_PERIOD_TENDENCY_FROM_SINGLE_RECORD)
    if _flag_true(surface_candidate_meta, ("diagnosis_claim", "personality_claim", "cause_claim", "advice_claim", "future_prediction_claim", "always_claim", "should_statement")):
        reasons.append("surface_candidate_meta_hard_claim_blocked")
    if _flag_true(surface_candidate_meta, ("self_denial_identity_claim",)):
        reasons.append(REJECTION_SELF_DENIAL_IDENTITY_CLAIM_BLOCKED)
    if _flag_true(surface_candidate_meta, ("target_judgement_agreement", "opponent_intent_claim")):
        reasons.append(REJECTION_TARGET_JUDGEMENT_AGREEMENT_BLOCKED)

    return _dedupe(reasons)


def _base_decision_flags() -> dict[str, Any]:
    return {
        "phase5_user_label_connection_gate_ready": True,
        "structure_insight_gate_relaxed": False,
        "existing_structure_insight_gate_relaxed": False,
        "surface_plan_generated": False,
        "comment_text_generated": False,
        "comment_text_generated_by_this_layer": False,
        "public_response_key_added": False,
        "api_route_changed": False,
        "request_key_changed": False,
        "response_shape_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "raw_fact_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "internal_question_body_included": False,
        "private_user_dictionary_text_included": False,
        "record_ids_included": False,
        "diagnosis_allowed": False,
        "personality_claim_allowed": False,
        "cause_claim_allowed": False,
        "advice_allowed": False,
        "future_prediction_allowed": False,
        "always_claim_allowed": False,
        "should_statement_allowed": False,
        "target_judgement_agreement_allowed": False,
        "period_tendency_from_single_record_allowed": False,
        "external_ai_added": False,
        "local_llm_added": False,
    }


def _decision_for_candidate(
    *,
    candidate_meta: Mapping[str, Any],
    material_meta: Mapping[str, Any],
    observation_reply_meta: Mapping[str, Any],
    surface_candidate_meta: Mapping[str, Any],
    surface: str,
    tier: str,
) -> dict[str, Any]:
    reasons = _candidate_rejection_reasons(
        candidate_meta=candidate_meta,
        material_meta=material_meta,
        observation_reply_meta=observation_reply_meta,
        surface_candidate_meta=surface_candidate_meta,
        surface=surface,
        tier=tier,
    )
    quality = _clean(candidate_meta.get("candidate_quality"))
    permission = _candidate_surface_permission(candidate_meta)
    passed = bool(
        not reasons
        and quality == CANDIDATE_QUALITY_GATE_CANDIDATE
        and permission.get("may_surface_after_user_label_connection_gate") is True
    )
    meta_only = bool(not reasons and not passed)
    action = GATE_ACTION_ALLOW_LIMITED_SURFACE_PLAN if passed else GATE_ACTION_META_ONLY if meta_only else GATE_ACTION_BLOCK_SURFACE_PLAN
    decision = {
        "schema_version": USER_LABEL_CONNECTION_GATE_SCHEMA_VERSION,
        "step": USER_LABEL_CONNECTION_GATE_STEP,
        "candidate_id": _clean(candidate_meta.get("candidate_id")) or "ulc.candidate.unknown",
        "candidate_schema_version": _clean(candidate_meta.get("schema_version")) or USER_LABEL_CONNECTION_CANDIDATE_SCHEMA_VERSION,
        "candidate_quality": quality,
        "mechanism_family": _clean(candidate_meta.get("mechanism_family")),
        "source_scope": _source_scope(candidate_meta, material_meta),
        "action": action,
        "passed": passed,
        "blocked": bool(reasons),
        "rejection_reasons": reasons,
        "required_surface_markers": _required_surface_markers(),
        "evidence_contract": _evidence_contract(candidate_meta),
        "capability_contract": _capability_contract(tier=tier, material_meta=material_meta, candidate_meta=candidate_meta),
        "public_contract": _public_contract(),
        "claim_contract": _claim_contract(),
        "surface_candidate_evaluated": bool(surface),
        "scope_marker_detected": bool(_SCOPE_MARKER_RE.search(surface)) if surface else False,
        "soft_marker_detected": bool(_SOFT_MARKER_RE.search(surface)) if surface else False,
        "may_surface_after_user_label_connection_gate": passed,
        "allow_limited_surface_plan": passed,
        "meta_only": meta_only,
        **_base_decision_flags(),
    }
    _decorate_gate_meta(decision)
    assert_user_label_connection_gate_meta_contract(decision)
    return decision


def _fallback_boundary_decision(
    *,
    material_meta: Mapping[str, Any],
    observation_reply_meta: Mapping[str, Any],
    surface_candidate_meta: Mapping[str, Any],
    surface: str,
    tier: str,
) -> dict[str, Any]:
    reasons: list[str] = []
    if tier == "free" or material_meta.get("record_scope") == RECORD_SCOPE_BLOCKED_FREE_TIER:
        reasons.append(REJECTION_FREE_HISTORY_BLOCKED)
    if not _user_fact_boundary_passed(material_meta):
        reasons.append(REJECTION_USER_FACT_GROUNDING_BOUNDARY_BLOCKED)
    if _low_information_protected(material_meta, observation_reply_meta):
        reasons.append(REJECTION_LOW_INFORMATION_HISTORY_PROMOTION_BLOCKED)
    if _safety_context(material_meta, observation_reply_meta):
        reasons.append(REJECTION_SAFETY_ADJACENT_HISTORY_CONNECTION_BLOCKED)
    reasons.extend(_strict_context_rejection_reasons(material_meta, observation_reply_meta))
    if _contains_text_payload_key(material_meta) or _contains_text_payload_key(surface_candidate_meta):
        reasons.append(REJECTION_RAW_TEXT_PAYLOAD_DETECTED)
    if _flag_true(material_meta, _FORBIDDEN_TRUE_FLAGS) or _flag_true(surface_candidate_meta, _FORBIDDEN_TRUE_FLAGS):
        reasons.append(REJECTION_RAW_TEXT_PAYLOAD_DETECTED)
    if _contains_comment_body_key(material_meta) or _contains_comment_body_key(surface_candidate_meta):
        reasons.append(REJECTION_COMMENT_TEXT_BODY_IN_META_DETECTED)
    if surface:
        reasons.extend(_marker_rejection_reasons(surface))
        reasons.extend(_claim_surface_rejection_reasons(surface))
    reasons = _dedupe(reasons)
    action = GATE_ACTION_BLOCK_SURFACE_PLAN if reasons else GATE_ACTION_NO_CANDIDATE
    decision = {
        "schema_version": USER_LABEL_CONNECTION_GATE_SCHEMA_VERSION,
        "step": USER_LABEL_CONNECTION_GATE_STEP,
        "candidate_id": "",
        "candidate_schema_version": "",
        "candidate_quality": "",
        "mechanism_family": "",
        "source_scope": _clean(material_meta.get("source_scope")) or SOURCE_SCOPE_CURRENT_ONLY,
        "action": action,
        "passed": False,
        "blocked": bool(reasons),
        "rejection_reasons": reasons,
        "required_surface_markers": _required_surface_markers(),
        "evidence_contract": _empty_evidence_contract(),
        "capability_contract": _capability_contract(tier=tier, material_meta=material_meta),
        "public_contract": _public_contract(),
        "claim_contract": _claim_contract(),
        "surface_candidate_evaluated": bool(surface),
        "scope_marker_detected": bool(_SCOPE_MARKER_RE.search(surface)) if surface else False,
        "soft_marker_detected": bool(_SOFT_MARKER_RE.search(surface)) if surface else False,
        "may_surface_after_user_label_connection_gate": False,
        "allow_limited_surface_plan": False,
        "meta_only": False,
        **_base_decision_flags(),
    }
    _decorate_gate_meta(decision)
    assert_user_label_connection_gate_meta_contract(decision)
    return decision


def build_user_label_connection_gate_decision(
    candidate: Any = None,
    *,
    material: Any = None,
    material_meta: Mapping[str, Any] | None = None,
    capability: Any = None,
    capability_tier: Any = None,
    subscription_tier: Any = None,
    user_fact_grounding_boundary_passed: bool | None = None,
    low_information: bool | None = None,
    safety_adjacent: bool = False,
    self_denial_context: bool = False,
    target_judgement_context: bool = False,
    safety_context_reasons: Sequence[Any] | None = None,
    public_meta: Mapping[str, Any] | None = None,
    proposed_surface: Any = "",
    surface_candidate: Any = "",
    surface_candidate_meta: Mapping[str, Any] | None = None,
    observation_reply_meta: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    material_meta_resolved, observation_meta, surface_meta, override_tier = _runtime_adjusted_metas(
        material=material,
        explicit_material_meta=material_meta,
        observation_reply_meta=observation_reply_meta,
        capability_tier=capability_tier,
        user_fact_grounding_boundary_passed=user_fact_grounding_boundary_passed,
        low_information=low_information,
        safety_adjacent=safety_adjacent,
        self_denial_context=self_denial_context,
        target_judgement_context=target_judgement_context,
        safety_context_reasons=safety_context_reasons,
        surface_candidate_meta=surface_candidate_meta,
        public_meta=public_meta,
    )
    tier = _normalize_tier(material_meta=material_meta_resolved, capability=capability, subscription_tier=override_tier or subscription_tier)
    candidates = _candidate_metas_from_inputs(candidate=candidate, material=material)
    surface = _clean(surface_candidate) or _clean(proposed_surface)
    if not candidates:
        return _fallback_boundary_decision(
            material_meta=material_meta_resolved,
            observation_reply_meta=observation_meta,
            surface_candidate_meta=surface_meta,
            surface=surface,
            tier=tier,
        )
    return _decision_for_candidate(
        candidate_meta=candidates[0],
        material_meta=material_meta_resolved,
        observation_reply_meta=observation_meta,
        surface_candidate_meta=surface_meta,
        surface=surface,
        tier=tier,
    )


def build_user_label_connection_gate_report(
    candidates: Any = None,
    *,
    candidate: Any = None,
    material: Any = None,
    material_meta: Mapping[str, Any] | None = None,
    capability: Any = None,
    capability_tier: Any = None,
    subscription_tier: Any = None,
    user_fact_grounding_boundary_passed: bool | None = None,
    low_information: bool | None = None,
    safety_adjacent: bool = False,
    self_denial_context: bool = False,
    target_judgement_context: bool = False,
    safety_context_reasons: Sequence[Any] | None = None,
    public_meta: Mapping[str, Any] | None = None,
    proposed_surface: Any = "",
    surface_candidate: Any = "",
    surface_candidate_meta: Mapping[str, Any] | None = None,
    observation_reply_meta: Mapping[str, Any] | None = None,
    max_candidates: int = 4,
) -> dict[str, Any]:
    material_meta_resolved, observation_meta, surface_meta, override_tier = _runtime_adjusted_metas(
        material=material,
        explicit_material_meta=material_meta,
        observation_reply_meta=observation_reply_meta,
        capability_tier=capability_tier,
        user_fact_grounding_boundary_passed=user_fact_grounding_boundary_passed,
        low_information=low_information,
        safety_adjacent=safety_adjacent,
        self_denial_context=self_denial_context,
        target_judgement_context=target_judgement_context,
        safety_context_reasons=safety_context_reasons,
        surface_candidate_meta=surface_candidate_meta,
        public_meta=public_meta,
    )
    tier = _normalize_tier(material_meta=material_meta_resolved, capability=capability, subscription_tier=override_tier or subscription_tier)
    surface = _clean(surface_candidate) or _clean(proposed_surface)
    candidate_metas = _candidate_metas_from_inputs(candidates, candidate=candidate, material=material, max_candidates=max_candidates)
    if not candidate_metas:
        decision = _fallback_boundary_decision(
            material_meta=material_meta_resolved,
            observation_reply_meta=observation_meta,
            surface_candidate_meta=surface_meta,
            surface=surface,
            tier=tier,
        )
        report = dict(decision)
        report.update(
            {
                "candidate_count": 0,
                "allowed_candidate_count": 0,
                "blocked_candidate_count": 1 if report["blocked"] else 0,
                "candidate_gate_results": [],
                "allowed_candidate_ids": [],
                "blocked_candidate_ids": [],
                "rejection_reason_counts": {reason: 1 for reason in report["rejection_reasons"]},
            }
        )
        _decorate_gate_meta(report)
        assert_user_label_connection_gate_meta_contract(report)
        return report

    decisions = [
        _decision_for_candidate(
            candidate_meta=meta,
            material_meta=material_meta_resolved,
            observation_reply_meta=observation_meta,
            surface_candidate_meta=surface_meta,
            surface=surface,
            tier=tier,
        )
        for meta in candidate_metas[: max(1, int(max_candidates))]
    ]
    allowed = [decision for decision in decisions if decision.get("passed") is True]
    blocked = [decision for decision in decisions if decision.get("blocked") is True]
    counter = Counter(reason for decision in decisions for reason in _dedupe(decision.get("rejection_reasons") or []))
    primary = allowed[0] if allowed else decisions[0]
    aggregate_action = (
        GATE_ACTION_ALLOW_LIMITED_SURFACE_PLAN
        if allowed and not blocked
        else GATE_ACTION_BLOCK_SURFACE_PLAN
        if blocked
        else GATE_ACTION_META_ONLY
    )
    report = dict(primary)
    report.update(
        {
            "action": aggregate_action,
            "passed": bool(allowed and not blocked),
            "blocked": bool(blocked),
            "candidate_count": len(decisions),
            "allowed_candidate_count": len(allowed),
            "blocked_candidate_count": len(blocked),
            "candidate_gate_results": [
                {
                    "candidate_id": decision["candidate_id"],
                    "candidate_quality": decision["candidate_quality"],
                    "mechanism_family": decision["mechanism_family"],
                    "action": decision["action"],
                    "passed": decision["passed"],
                    "blocked": decision["blocked"],
                    "rejection_reasons": list(decision["rejection_reasons"]),
                    "evidence_contract": dict(decision["evidence_contract"]),
                }
                for decision in decisions
            ],
            "allowed_candidate_ids": [decision["candidate_id"] for decision in allowed],
            "blocked_candidate_ids": [decision["candidate_id"] for decision in blocked],
            "rejection_reasons": sorted(counter),
            "rejection_reason_counts": dict(counter),
            "may_surface_after_user_label_connection_gate": bool(allowed and not blocked),
            "allow_limited_surface_plan": bool(allowed and not blocked),
            "meta_only": bool(not allowed and not blocked),
        }
    )
    _decorate_gate_meta(report)
    assert_user_label_connection_gate_meta_contract(report)
    return report


def user_label_connection_gate_public_summary(value: Mapping[str, Any] | None) -> dict[str, Any]:
    source = _safe_mapping(value)
    if not source:
        return {}
    if _contains_text_payload_key(source) or _flag_true(source, _FORBIDDEN_TRUE_FLAGS):
        return {
            "evaluated": True,
            "passed": False,
            "blocked": True,
            "rejection_reasons": ["user_label_connection_gate_public_meta_unsafe"],
            "public_meta_summary_only": True,
        }
    summary: dict[str, Any] = {}
    for key in (
        "passed",
        "blocked",
        "phase5_user_label_connection_gate_ready",
        "may_surface_after_user_label_connection_gate",
        "allow_limited_surface_plan",
        "surface_candidate_evaluated",
    ):
        if isinstance(source.get(key), bool):
            summary[key] = bool(source.get(key))
    if _clean(source.get("action")):
        summary["action"] = _clean(source.get("action"))
    for key in ("candidate_count", "allowed_candidate_count", "blocked_candidate_count"):
        if key in source:
            summary[key] = _int(source.get(key))
    reasons = _dedupe(source.get("rejection_reasons") or [])
    if reasons:
        summary["rejection_reasons"] = reasons[:20]
    if summary:
        summary.update(
            {
                "public_meta_summary_only": True,
                "raw_text_included": False,
                "comment_text_body_included": False,
                "public_response_key_added": False,
            }
        )
    assert_user_label_connection_gate_meta_contract(summary, allow_partial=True)
    return summary


def assert_user_label_connection_gate_meta_contract(value: Any, *, allow_partial: bool = False) -> None:
    if _contains_text_payload_key(value):
        raise ValueError("UserLabelConnectionGate meta must not include raw text/comment/surface payload keys")
    if _flag_true(value, _FORBIDDEN_TRUE_FLAGS):
        raise ValueError("UserLabelConnectionGate meta contains a forbidden true flag")
    if allow_partial:
        json.dumps(value, ensure_ascii=False, sort_keys=True)
        return
    if not isinstance(value, Mapping):
        raise ValueError("UserLabelConnectionGate meta must be a mapping")
    if value.get("schema_version") != USER_LABEL_CONNECTION_GATE_SCHEMA_VERSION:
        raise ValueError("unexpected UserLabelConnectionGate schema_version")
    if value.get("step") != USER_LABEL_CONNECTION_GATE_STEP:
        raise ValueError("unexpected UserLabelConnectionGate step")
    if value.get("action") not in _ALLOWED_ACTIONS:
        raise ValueError("unexpected UserLabelConnectionGate action")
    if value.get("passed") is True and value.get("blocked") is True:
        raise ValueError("UserLabelConnectionGate cannot both pass and block")
    if value.get("passed") is True and value.get("action") != GATE_ACTION_ALLOW_LIMITED_SURFACE_PLAN:
        raise ValueError("passed gate must allow limited surface plan")
    if value.get("blocked") is True and not value.get("rejection_reasons"):
        raise ValueError("blocked gate must include rejection reasons")
    markers = _safe_mapping(value.get("required_surface_markers"))
    for key in ("scope_marker_required", "soft_marker_required", "advice_marker_forbidden", "future_prediction_forbidden"):
        if markers.get(key) is not True:
            raise ValueError(f"UserLabelConnectionGate marker contract requires {key}=true")
    evidence = _safe_mapping(value.get("evidence_contract"))
    if evidence.get("minimum_evidence_record_count") != MINIMUM_EVIDENCE_RECORD_COUNT:
        raise ValueError("UserLabelConnectionGate minimum evidence count changed")
    if evidence.get("period_tendency_from_single_record_allowed") is not False:
        raise ValueError("period tendency from a single record must be forbidden")
    if value.get("passed") is True:
        if _int(evidence.get("evidence_record_count")) < MINIMUM_EVIDENCE_RECORD_COUNT:
            raise ValueError("passed gate requires evidence_record_count >= 2")
        if evidence.get("current_record_included") is not True:
            raise ValueError("passed gate requires current input evidence")
        if _int(evidence.get("history_record_count")) < 1:
            raise ValueError("passed gate requires history evidence")
    capability = _safe_mapping(value.get("capability_contract"))
    if capability.get("tier") not in _ALLOWED_TIERS:
        raise ValueError("unexpected capability tier")
    if capability.get("free_history_used") is not False:
        raise ValueError("free_history_used must remain false")
    public = _safe_mapping(value.get("public_contract"))
    for key in _public_contract():
        if public.get(key) is not False:
            raise ValueError(f"public contract violates {key}=false")
    claims = _safe_mapping(value.get("claim_contract"))
    for key in _claim_contract():
        if claims.get(key) is not False:
            raise ValueError(f"claim contract violates {key}=false")
    json.dumps(value, ensure_ascii=False, sort_keys=True)


# Compatibility aliases for later phases/tests.
def assert_user_label_connection_gate_meta(value: Any) -> None:
    assert_user_label_connection_gate_meta_contract(value)


def build_user_label_connection_gate_meta(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return build_user_label_connection_gate_decision(*args, **kwargs)


__all__ = [
    "USER_LABEL_CONNECTION_GATE_SCHEMA_VERSION",
    "USER_LABEL_CONNECTION_GATE_STEP",
    "GATE_ACTION_ALLOW_LIMITED_SURFACE_PLAN",
    "GATE_ACTION_BLOCK_SURFACE_PLAN",
    "GATE_ACTION_META_ONLY",
    "GATE_ACTION_NO_CANDIDATE",
    "REJECTION_FREE_HISTORY_BLOCKED",
    "REJECTION_USER_FACT_GROUNDING_BOUNDARY_BLOCKED",
    "REJECTION_LOW_INFORMATION_HISTORY_PROMOTION_BLOCKED",
    "REJECTION_CURRENT_INPUT_MISSING",
    "REJECTION_HISTORY_RECORD_COUNT_INSUFFICIENT",
    "REJECTION_SOURCE_SCOPE_MARKER_MISSING",
    "REJECTION_SOFT_MARKER_MISSING",
    "REJECTION_RAW_TEXT_PAYLOAD_DETECTED",
    "REJECTION_COMMENT_TEXT_BODY_IN_META_DETECTED",
    "REJECTION_PERIOD_TENDENCY_FROM_SINGLE_RECORD",
    "REJECTION_PERSONALITY_CLAIM_SURFACE",
    "REJECTION_DIAGNOSIS_SURFACE",
    "REJECTION_CAUSE_CLAIM_WITHOUT_EVIDENCE_SURFACE",
    "REJECTION_ADVICE_SURFACE",
    "REJECTION_FUTURE_PREDICTION_SURFACE",
    "REJECTION_ALWAYS_CLAIM_SURFACE",
    "REJECTION_SHOULD_STATEMENT_SURFACE",
    "REJECTION_SAFETY_ADJACENT_HISTORY_CONNECTION_BLOCKED",
    "REJECTION_SELF_DENIAL_IDENTITY_CLAIM_BLOCKED",
    "REJECTION_TARGET_JUDGEMENT_AGREEMENT_BLOCKED",
    "MINIMUM_EVIDENCE_RECORD_COUNT",
    "build_user_label_connection_gate_decision",
    "build_user_label_connection_gate_report",
    "build_user_label_connection_gate_meta",
    "user_label_connection_gate_public_summary",
    "assert_user_label_connection_gate_meta",
    "assert_user_label_connection_gate_meta_contract",
]
