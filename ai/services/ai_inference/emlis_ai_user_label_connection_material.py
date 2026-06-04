# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase 2/3 material builder for EmlisAI User Label Connection Observation v1.

The builder normalizes the current input and capability-allowed owned history
into User Label Points, then derives text-free edge-family and private score
material when history use is allowed.  It intentionally does not connect to the
reply runtime, generate ``comment_text``, add public response keys, change
DB/RN/API contracts, or implement later candidate/gate/surface phases.
"""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any, Final

from emlis_ai_current_input_bundle import EmlisCurrentInputBundle, build_emlis_current_input_bundle
from emlis_ai_user_fact_grounding_boundary import (
    assert_user_fact_grounding_decision_contract,
    resolve_user_fact_grounding_boundary,
)
from emlis_ai_user_label_connection_types import (
    EDGE_FAMILY_ACTION_STATE_BRIDGE,
    EDGE_FAMILY_CATEGORY_OUTPUT_ROUTE,
    EDGE_FAMILY_CATEGORY_STATE_RECURRENCE,
    EDGE_FAMILY_CONTRAST_LINE_SHIFT,
    EDGE_FAMILY_LABEL_ROUTE_CURRENT_ALIGNMENT,
    EDGE_FAMILY_STATE_OUTPUT_ATTACHMENT,
    EDGE_FAMILY_UNRESOLVED_WEIGHT_REAPPEARANCE,
    EDGE_FAMILY_VALUE_LINE_REAPPEARANCE,
    MATERIAL_QUALITY_HISTORY_CONNECTION_BLOCKED,
    MATERIAL_QUALITY_HISTORY_CONNECTION_CANDIDATE,
    MATERIAL_QUALITY_LOW_INFORMATION_PROTECTED,
    MATERIAL_QUALITY_NO_HISTORY_AVAILABLE,
    MATERIAL_QUALITY_SAFETY_TRIAGE_REQUIRED,
    RECORD_SCOPE_BLOCKED_FREE_TIER,
    RECORD_SCOPE_BLOCKED_GROUNDING_BOUNDARY,
    RECORD_SCOPE_CURRENT_ONLY,
    RECORD_SCOPE_CURRENT_PLUS_OWNED_HISTORY,
    SOURCE_KIND_CURRENT_INPUT,
    SOURCE_KIND_LAST_INPUT,
    SOURCE_KIND_SAME_DAY_RECENT_INPUT,
    SOURCE_KIND_SIMILAR_INPUT,
    SOURCE_SCOPE_CURRENT_ONLY,
    SOURCE_SCOPE_OWNED_HISTORY,
    SOURCE_SCOPE_OWNED_HISTORY_AND_CROSS_CORE,
    USER_LABEL_CONNECTION_EDGE_SCORE_SCHEMA_VERSION,
    USER_LABEL_CONNECTION_MATERIAL_SCHEMA_VERSION,
    USER_LABEL_CONNECTION_MATERIAL_STEP,
    USER_LABEL_POINT_SCHEMA_VERSION,
    UserLabelConnectionEdge,
    UserLabelConnectionMaterial,
    UserLabelPoint,
)

_SPACE_RE: Final = re.compile(r"\s+")
_TOKEN_RE: Final = re.compile(r"[0-9A-Za-zぁ-んァ-ンー一-龠]+")

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
        "input_text",
        "inputText",
        "user_input",
        "userInput",
        "current_input",
        "currentInput",
        "history_input",
        "historyInput",
        "memo_text",
        "memoText",
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
        "reply_text",
        "replyText",
        "realized_text",
        "realizedText",
        "body",
        "text",
    }
)
_ALLOWED_SOURCE_FIELD_VALUES: Final = frozenset(
    {"category", "emotion_details", "emotions", "strength", "memo_action", "memo", "created_at", "selected_at"}
)
_FORBIDDEN_TRUE_FLAGS: Final = frozenset(
    {
        "api_route_changed",
        "request_key_changed",
        "response_shape_changed",
        "public_response_key_added",
        "db_physical_name_changed",
        "rn_visible_contract_changed",
        "rn_visible_title_changed",
        "raw_input_included",
        "raw_text_included",
        "history_raw_text_included",
        "comment_text_body_included",
        "candidate_body_included",
        "surface_body_included",
        "comment_text_generated",
        "comment_text_generated_by_this_layer",
        "fixed_sentence_template_added",
        "external_ai_added",
        "local_llm_added",
    }
)
_LOW_INFORMATION_STATUSES: Final = frozenset({"low_information", "insufficient_information"})
_SAFETY_QUALITIES: Final = frozenset({"safety_triage_required", "safety_blocked", "emergency_safety_required"})
_PHASE3_MIN_EDGE_SCORE: Final = 0.42
_UNRESOLVED_MARKERS: Final = (
    "わからない",
    "分からない",
    "できない",
    "出来ない",
    "動けない",
    "進めない",
    "続けられ",
    "無理",
    "限界",
    "詰ま",
    "止ま",
    "迷",
    "未完",
    "整理しきれ",
    "言い切れ",
    "変えられ",
)


@dataclass(frozen=True)
class _UserLabelPointContext:
    point: UserLabelPoint
    categories: frozenset[str]
    emotions: frozenset[str]
    output_fingerprints: frozenset[str]
    action_fingerprints: frozenset[str]
    unresolved_marker_fingerprints: frozenset[str]
    source_field_ids: frozenset[str]


def _clean(value: Any) -> str:
    return _SPACE_RE.sub(" ", str(value or "").replace("\u3000", " ")).strip()


def _dedupe(values: Iterable[Any] | Any | None) -> tuple[str, ...]:
    if values is None:
        iterable: Iterable[Any] = ()
    elif isinstance(values, (str, bytes, bytearray)):
        iterable = (values,)
    elif isinstance(values, Iterable):
        iterable = values
    else:
        iterable = (values,)
    out: list[str] = []
    for value in iterable:
        item = _clean(value)
        if item and item not in out:
            out.append(item)
    return tuple(out)


def _contains_text_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if _clean(key) in _TEXT_PAYLOAD_KEYS:
                return True
            if _contains_text_payload_key(item):
                return True
        return False
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_text_payload_key(item) for item in value)
    return False


def _field_contains_raw_text_key(key: str) -> bool:
    return _clean(key) in _TEXT_PAYLOAD_KEYS


def _token_fingerprint_count(text: Any) -> int:
    value = _clean(text)
    if not value:
        return 0
    tokens = {match.group(0).lower() for match in _TOKEN_RE.finditer(value) if match.group(0).strip()}
    if tokens:
        return len(tokens)
    return 1


def _fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _token_fingerprints(text: Any) -> frozenset[str]:
    """Return private comparison fingerprints without exposing raw text.

    Japanese user text often has no spaces, so Phase 3 compares hashed n-gram
    fingerprints internally.  The fingerprints are used only while building
    edge scores and are never emitted in material meta.
    """

    value = _clean(text).lower()
    if not value:
        return frozenset()
    pieces: set[str] = set()
    for match in _TOKEN_RE.finditer(value):
        token = match.group(0).strip().lower()
        if not token:
            continue
        pieces.add(token)
        if len(token) >= 5:
            for size in (2, 3, 4):
                for index in range(0, max(0, len(token) - size + 1)):
                    pieces.add(token[index : index + size])
    compact = re.sub(r"\s+", "", value)
    if len(compact) >= 5:
        for size in (2, 3, 4):
            for index in range(0, max(0, len(compact) - size + 1)):
                pieces.add(compact[index : index + size])
    return frozenset(_fingerprint(piece) for piece in pieces if len(piece) >= 2)


def _marker_fingerprints(*texts: Any) -> frozenset[str]:
    joined = " ".join(_clean(text) for text in texts if _clean(text))
    if not joined:
        return frozenset()
    markers = {marker for marker in _UNRESOLVED_MARKERS if marker in joined}
    return frozenset(_fingerprint(marker) for marker in markers)


def _overlap_score(left: Iterable[str], right: Iterable[str]) -> float:
    left_set = set(left)
    right_set = set(right)
    if not left_set or not right_set:
        return 0.0
    return min(1.0, len(left_set & right_set) / max(1, min(len(left_set), len(right_set))))


def _jaccard_score(left: Iterable[str], right: Iterable[str]) -> float:
    left_set = set(left)
    right_set = set(right)
    if not left_set or not right_set:
        return 0.0
    return min(1.0, len(left_set & right_set) / max(1, len(left_set | right_set)))


def _clamp_score(value: float) -> float:
    return round(max(0.0, min(1.0, float(value))), 4)


def _edge_record_count(current: _UserLabelPointContext, histories: Sequence[_UserLabelPointContext]) -> int:
    count = 1 if current.point.source_record_id_present else 0
    count += sum(1 for history in histories if history.point.source_record_id_present)
    return int(count)


def _edge_point_ids(current: _UserLabelPointContext, histories: Sequence[_UserLabelPointContext]) -> tuple[str, ...]:
    point_ids: list[str] = []
    if current.point.source_record_id_present:
        point_ids.append(current.point.point_id)
    for history in histories:
        if history.point.source_record_id_present:
            point_ids.append(history.point.point_id)
    return _dedupe(point_ids)


def _bundle_get(value: Any, key: str, default: Any = None) -> Any:
    if isinstance(value, Mapping):
        return value.get(key, default)
    return getattr(value, key, default)


def _as_meta(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    as_meta = getattr(value, "as_meta", None)
    if callable(as_meta):
        meta = as_meta()
        return dict(meta) if isinstance(meta, Mapping) else {}
    return {}


def _normalize_tier(*, capability: Any = None, subscription_tier: Any = None) -> str:
    for value in (subscription_tier, getattr(capability, "tier", None), getattr(capability, "subscription_tier", None)):
        text = _clean(value).lower()
        if text in {"free", "plus", "premium"}:
            return text
        if text in {"subscription", "subscriber"}:
            return "plus"
    if getattr(capability, "cross_core_enabled", False):
        return "premium"
    if getattr(capability, "model_read_enabled", False) or getattr(capability, "include_derived_user_model", False):
        return "plus"
    return "free"


def _capability_source_scope(capability: Any = None, *, tier: str = "free") -> str:
    source_scope = _clean(getattr(capability, "source_scope", ""))
    if source_scope in {SOURCE_SCOPE_CURRENT_ONLY, SOURCE_SCOPE_OWNED_HISTORY, SOURCE_SCOPE_OWNED_HISTORY_AND_CROSS_CORE}:
        return source_scope
    if tier == "premium":
        return SOURCE_SCOPE_OWNED_HISTORY_AND_CROSS_CORE
    if tier == "plus":
        return SOURCE_SCOPE_OWNED_HISTORY
    return SOURCE_SCOPE_CURRENT_ONLY


def _capability_allows_history(capability: Any = None, *, tier: str = "free") -> bool:
    if tier not in {"plus", "premium"}:
        return False
    if capability is None:
        return True
    history_mode = _clean(getattr(capability, "history_mode", "extended")).lower()
    if history_mode == "none":
        return False
    source_scope = _capability_source_scope(capability, tier=tier)
    return source_scope in {SOURCE_SCOPE_OWNED_HISTORY, SOURCE_SCOPE_OWNED_HISTORY_AND_CROSS_CORE}


def _resolve_grounding_decision_meta(
    *,
    capability: Any = None,
    subscription_tier: Any = None,
    source_bundle: Any = None,
    current_input: Any = None,
    user_fact_grounding_decision: Any = None,
    observation_reply_meta: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if user_fact_grounding_decision is not None:
        meta = _as_meta(user_fact_grounding_decision)
        if meta:
            assert_user_fact_grounding_decision_contract(meta)
            return meta
    reply_meta = dict(observation_reply_meta or {})
    decision = resolve_user_fact_grounding_boundary(
        subscription_tier=subscription_tier,
        capability=capability,
        source_bundle=source_bundle,
        current_input=current_input,
        observation_reply_kind=reply_meta.get("observation_reply_kind"),
        eligibility_status=reply_meta.get("eligibility_status") or reply_meta.get("status"),
        unknown_slots=reply_meta.get("unknown_slots"),
    )
    return decision.as_meta()


def _grounding_boundary_passed_for_history(meta: Mapping[str, Any], *, tier: str, capability_history_allowed: bool) -> bool:
    if not capability_history_allowed:
        return True
    if tier not in {"plus", "premium"}:
        return True
    if meta.get("user_fact_read_enabled") is not True:
        return False
    if meta.get("user_fact_may_promote_to_eligible") is True:
        return False
    if meta.get("assert_current_event_from_user_fact") is True:
        return False
    if meta.get("personality_tendency_allowed") is True:
        return False
    return True


def _low_information_protected(*, grounding_meta: Mapping[str, Any], observation_reply_meta: Mapping[str, Any] | None) -> bool:
    if grounding_meta.get("low_information_protected") is True:
        return True
    for key in ("eligibility_status", "observation_reply_kind", "material_quality", "status"):
        if _clean(grounding_meta.get(key)).lower() in _LOW_INFORMATION_STATUSES:
            return True
        if observation_reply_meta and _clean(observation_reply_meta.get(key)).lower() in _LOW_INFORMATION_STATUSES:
            return True
    if grounding_meta.get("eligible_for_full_observation") is False and grounding_meta.get("question_required") is True:
        return True
    if observation_reply_meta and observation_reply_meta.get("eligible_for_full_observation") is False and observation_reply_meta.get("question_required") is True:
        return True
    return False


def _safety_triage_required(*, material_quality: Any = None, observation_reply_meta: Mapping[str, Any] | None = None) -> bool:
    if _clean(material_quality).lower() in _SAFETY_QUALITIES:
        return True
    if not observation_reply_meta:
        return False
    for key in ("material_quality", "safety_triage_kind", "eligibility_status", "observation_status"):
        if _clean(observation_reply_meta.get(key)).lower() in _SAFETY_QUALITIES:
            return True
    return False


def _strength_bucket(bundle: EmlisCurrentInputBundle) -> str:
    strengths = [emotion.strength for emotion in bundle.emotions if _clean(emotion.strength)]
    if not bundle.emotions:
        return "unknown"
    unique = set(strengths)
    if len(unique) > 1:
        return "mixed"
    if not strengths:
        return ""
    value = strengths[0]
    if value in {"weak", "medium", "strong"}:
        return value
    return "unknown"


def _emotion_source_fields(bundle: EmlisCurrentInputBundle) -> tuple[str, ...]:
    fields: list[str] = []
    for emotion in bundle.emotions:
        source_field = _clean(emotion.source_field) or "emotion_details"
        if source_field in {"emotion_details", "emotions"}:
            fields.append(source_field)
        else:
            fields.append("emotion_details")
        if _clean(emotion.strength):
            fields.append("strength")
    return _dedupe(fields)


def _environment_source_fields(bundle: EmlisCurrentInputBundle) -> tuple[str, ...]:
    fields: list[str] = []
    if bundle.categories:
        fields.append("category")
    if _clean(bundle.action_text):
        fields.append("memo_action")
    return _dedupe(fields)


def _output_source_fields(bundle: EmlisCurrentInputBundle) -> tuple[str, ...]:
    return ("memo",) if _clean(bundle.thought_text) else tuple()


def _time_source_fields(bundle: EmlisCurrentInputBundle) -> tuple[str, ...]:
    return ("created_at",) if _clean(bundle.selected_at) else tuple()


def _point_has_material(point: UserLabelPoint) -> bool:
    axes = point.as_meta()["label_axes"]
    return bool(
        point.source_record_id_present
        or point.selected_at_present
        or axes["environment"]["source_field_ids"]
        or axes["state"]["source_field_ids"]
        or axes["output"]["source_field_ids"]
    )


def _build_user_label_point_from_bundle(
    bundle: EmlisCurrentInputBundle,
    *,
    source_kind: str,
    point_id: str,
    source_scope: str,
    selected_at_bucket: str,
) -> UserLabelPoint:
    return UserLabelPoint(
        point_id=point_id,
        source_kind=source_kind,
        source_scope=source_scope,
        source_record_id_present=bool(_clean(bundle.source_record_id)),
        selected_at_present=bool(_clean(bundle.selected_at)),
        category_labels=_dedupe(bundle.categories),
        emotion_labels=_dedupe(emotion.type for emotion in bundle.emotions),
        strength_bucket=_strength_bucket(bundle),
        has_action_axis=bool(_clean(bundle.action_text)),
        has_thought_axis=bool(_clean(bundle.thought_text)),
        thought_token_fingerprint_count=_token_fingerprint_count(bundle.thought_text),
        selected_at_bucket=selected_at_bucket,
        environment_source_field_ids=_environment_source_fields(bundle),
        state_source_field_ids=_emotion_source_fields(bundle),
        output_source_field_ids=_output_source_fields(bundle),
        time_source_field_ids=_time_source_fields(bundle),
        point_is_tendency=False,
        raw_text_included=False,
        raw_input_included=False,
        comment_text_body_included=False,
    )


def build_user_label_point(
    value: Any,
    *,
    source_kind: str = SOURCE_KIND_CURRENT_INPUT,
    point_id: str = "current:present",
    source_scope: str = SOURCE_SCOPE_CURRENT_ONLY,
    selected_at_bucket: str = "unknown",
) -> UserLabelPoint:
    """Normalize a current/history row into a text-free UserLabelPoint."""

    bundle = build_emlis_current_input_bundle(value)
    return _build_user_label_point_from_bundle(
        bundle,
        source_kind=source_kind,
        point_id=point_id,
        source_scope=source_scope,
        selected_at_bucket=selected_at_bucket,
    )


def _build_point_context(
    value: Any,
    *,
    source_kind: str,
    point_id: str,
    source_scope: str,
    selected_at_bucket: str,
) -> _UserLabelPointContext:
    bundle = build_emlis_current_input_bundle(value)
    point = _build_user_label_point_from_bundle(
        bundle,
        source_kind=source_kind,
        point_id=point_id,
        source_scope=source_scope,
        selected_at_bucket=selected_at_bucket,
    )
    source_fields = set(point.environment_source_field_ids)
    source_fields.update(point.state_source_field_ids)
    source_fields.update(point.output_source_field_ids)
    source_fields.update(point.time_source_field_ids)
    return _UserLabelPointContext(
        point=point,
        categories=frozenset(_clean(item) for item in bundle.categories if _clean(item)),
        emotions=frozenset(_clean(emotion.type) for emotion in bundle.emotions if _clean(emotion.type)),
        output_fingerprints=_token_fingerprints(bundle.thought_text),
        action_fingerprints=_token_fingerprints(bundle.action_text),
        unresolved_marker_fingerprints=_marker_fingerprints(bundle.thought_text, bundle.action_text, *(emotion.type for emotion in bundle.emotions)),
        source_field_ids=frozenset(source_fields),
    )


def _iter_history_values(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        return [value]
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return list(value)
    return [value]


def _record_identity(value: Any) -> str:
    if isinstance(value, Mapping):
        return _clean(value.get("id") or value.get("emotion_id") or value.get("source_record_id") or value.get("created_at"))
    return _clean(getattr(value, "id", None) or getattr(value, "emotion_id", None) or getattr(value, "source_record_id", None) or getattr(value, "created_at", None))


def _build_history_point_contexts(
    source_bundle: Any,
    *,
    source_scope: str,
) -> tuple[tuple[_UserLabelPointContext, ...], int, int, bool]:
    contexts: list[_UserLabelPointContext] = []
    seen_identities: set[str] = set()
    same_day_count = 0
    similar_count = 0
    last_input_present = False

    def add(raw: Any, *, source_kind: str, bucket: str, ordinal: int) -> bool:
        identity = _record_identity(raw)
        if identity and identity in seen_identities:
            return False
        context = _build_point_context(
            raw,
            source_kind=source_kind,
            point_id=f"history:{source_kind}:{ordinal:03d}",
            source_scope=source_scope,
            selected_at_bucket=bucket,
        )
        if not _point_has_material(context.point):
            return False
        if identity:
            seen_identities.add(identity)
        contexts.append(context)
        return True

    last_input = _bundle_get(source_bundle, "last_input")
    if last_input:
        last_input_present = add(last_input, source_kind=SOURCE_KIND_LAST_INPUT, bucket="history", ordinal=1)

    for index, item in enumerate(_iter_history_values(_bundle_get(source_bundle, "same_day_recent_inputs", [])), start=1):
        if add(item, source_kind=SOURCE_KIND_SAME_DAY_RECENT_INPUT, bucket="same_day", ordinal=index):
            same_day_count += 1

    for index, item in enumerate(_iter_history_values(_bundle_get(source_bundle, "similar_inputs", [])), start=1):
        if add(item, source_kind=SOURCE_KIND_SIMILAR_INPUT, bucket="history", ordinal=index):
            similar_count += 1

    return tuple(contexts), same_day_count, similar_count, last_input_present


def _derived_anchor_count(source_bundle: Any) -> int:
    model = _bundle_get(source_bundle, "derived_user_model")
    if not model:
        return 0
    count = 0
    for key in ("open_topic_anchors", "recovery_anchors", "hypotheses"):
        values = _bundle_get(model, key, []) or []
        if isinstance(values, Sequence) and not isinstance(values, (str, bytes, bytearray)):
            count += len(values)
    frame = _bundle_get(model, "interpretive_frame")
    if frame:
        for key in ("value_anchors", "meaning_map"):
            values = _bundle_get(frame, key, []) or []
            if isinstance(values, Sequence) and not isinstance(values, (str, bytes, bytearray)):
                count += len(values)
    return int(count)


def _edge_time_scope(histories: Sequence[_UserLabelPointContext]) -> str:
    if histories and all(history.point.selected_at_bucket == "same_day" for history in histories):
        return "same_day"
    return "owned_history_window"


def _score_edge(
    *,
    label_overlap_score: float,
    axis_overlap_score: float,
    evidence_record_count: int,
    low_information_penalty: float = 0.0,
    safety_penalty: float = 0.0,
) -> tuple[float, float, float, float, float, float, float]:
    label = _clamp_score(label_overlap_score)
    axis = _clamp_score(axis_overlap_score)
    evidence = _clamp_score(min(1.0, evidence_record_count / 3.0))
    current_alignment = 1.0 if evidence_record_count >= 2 else 0.0
    low_penalty = _clamp_score(low_information_penalty)
    safety = _clamp_score(safety_penalty)
    final = _clamp_score((label * 0.4) + (axis * 0.3) + (evidence * 0.2) + (current_alignment * 0.1) - low_penalty - safety)
    return label, axis, evidence, current_alignment, low_penalty, safety, final


def _make_edge(
    *,
    family: str,
    source_field_ids: Sequence[str],
    current: _UserLabelPointContext,
    histories: Sequence[_UserLabelPointContext],
    label_overlap_score: float,
    axis_overlap_score: float,
    ordinal: int,
    low_information_penalty: float = 0.0,
    safety_penalty: float = 0.0,
) -> UserLabelConnectionEdge | None:
    evidence_record_count = _edge_record_count(current, histories)
    if evidence_record_count < 2:
        return None
    label, axis, evidence, current_alignment, low_penalty, safety, final = _score_edge(
        label_overlap_score=label_overlap_score,
        axis_overlap_score=axis_overlap_score,
        evidence_record_count=evidence_record_count,
        low_information_penalty=low_information_penalty,
        safety_penalty=safety_penalty,
    )
    if final < _PHASE3_MIN_EDGE_SCORE:
        return None
    return UserLabelConnectionEdge(
        edge_id=f"edge.{family}.{ordinal:03d}",
        edge_family=family,
        source_field_ids=tuple(_dedupe(source_field_ids)),
        evidence_record_count=evidence_record_count,
        evidence_point_ids=_edge_point_ids(current, histories),
        time_scope=_edge_time_scope(histories),
        source_scope_marker_required=True,
        soft_marker_required=True,
        line_is_candidate=True,
        line_is_fact=False,
        label_overlap_score=label,
        axis_overlap_score=axis,
        evidence_record_count_score=evidence,
        current_alignment_score=current_alignment,
        low_information_penalty=low_penalty,
        safety_penalty=safety,
        final_score=final,
        score_is_public=False,
        raw_text_included=False,
        comment_text_body_included=False,
    )


def _average(values: Iterable[float]) -> float:
    clean_values = [float(value) for value in values if value > 0.0]
    if not clean_values:
        return 0.0
    return sum(clean_values) / len(clean_values)


def _top_matches(
    histories: Sequence[_UserLabelPointContext],
    predicate: Any,
    *,
    limit: int = 4,
) -> tuple[_UserLabelPointContext, ...]:
    matches: list[tuple[float, _UserLabelPointContext]] = []
    for history in histories:
        score = float(predicate(history) or 0.0)
        if score > 0.0:
            matches.append((score, history))
    matches.sort(key=lambda item: (-item[0], item[1].point.point_id))
    return tuple(history for _, history in matches[:limit])


def _connection_strength(current: _UserLabelPointContext, history: _UserLabelPointContext) -> float:
    category = _overlap_score(current.categories, history.categories)
    emotion = _overlap_score(current.emotions, history.emotions)
    output = _overlap_score(current.output_fingerprints, history.output_fingerprints)
    action = _overlap_score(current.action_fingerprints, history.action_fingerprints)
    unresolved = _overlap_score(current.unresolved_marker_fingerprints, history.unresolved_marker_fingerprints)
    return _clamp_score((category * 0.25) + (emotion * 0.25) + (output * 0.2) + (action * 0.15) + (unresolved * 0.15))


def _build_user_label_connection_edges(
    *,
    current: _UserLabelPointContext,
    histories: Sequence[_UserLabelPointContext],
    derived_anchor_count: int,
    low_information: bool,
    safety_required: bool,
) -> tuple[UserLabelConnectionEdge, ...]:
    if not histories or low_information or safety_required:
        return tuple()

    edges: list[UserLabelConnectionEdge] = []
    ordinal = 1

    def append(edge: UserLabelConnectionEdge | None) -> None:
        nonlocal ordinal
        if edge is None:
            return
        edges.append(edge)
        ordinal += 1

    category_state_matches = _top_matches(
        histories,
        lambda history: _average(
            [
                _overlap_score(current.categories, history.categories),
                _overlap_score(current.emotions, history.emotions),
            ]
        )
        if _overlap_score(current.categories, history.categories) > 0.0 and _overlap_score(current.emotions, history.emotions) > 0.0
        else 0.0,
    )
    if category_state_matches:
        append(
            _make_edge(
                family=EDGE_FAMILY_CATEGORY_STATE_RECURRENCE,
                source_field_ids=("category", "emotion_details", "created_at"),
                current=current,
                histories=category_state_matches,
                label_overlap_score=_average(
                    _average(
                        [
                            _overlap_score(current.categories, history.categories),
                            _overlap_score(current.emotions, history.emotions),
                        ]
                    )
                    for history in category_state_matches
                ),
                axis_overlap_score=1.0,
                ordinal=ordinal,
            )
        )

    state_output_matches = _top_matches(
        histories,
        lambda history: min(
            _overlap_score(current.emotions, history.emotions),
            max(_overlap_score(current.output_fingerprints, history.output_fingerprints), _jaccard_score(current.output_fingerprints, history.output_fingerprints) * 4.0),
        ),
    )
    if state_output_matches:
        append(
            _make_edge(
                family=EDGE_FAMILY_STATE_OUTPUT_ATTACHMENT,
                source_field_ids=("emotion_details", "memo"),
                current=current,
                histories=state_output_matches,
                label_overlap_score=_average([_overlap_score(current.emotions, history.emotions) for history in state_output_matches]),
                axis_overlap_score=_average([_overlap_score(current.output_fingerprints, history.output_fingerprints) for history in state_output_matches]),
                ordinal=ordinal,
            )
        )

    action_state_matches = _top_matches(
        histories,
        lambda history: min(
            _overlap_score(current.emotions, history.emotions),
            max(_overlap_score(current.action_fingerprints, history.action_fingerprints), _jaccard_score(current.action_fingerprints, history.action_fingerprints) * 4.0),
        ),
    )
    if action_state_matches:
        append(
            _make_edge(
                family=EDGE_FAMILY_ACTION_STATE_BRIDGE,
                source_field_ids=("memo_action", "emotion_details"),
                current=current,
                histories=action_state_matches,
                label_overlap_score=_average([_overlap_score(current.emotions, history.emotions) for history in action_state_matches]),
                axis_overlap_score=_average([_overlap_score(current.action_fingerprints, history.action_fingerprints) for history in action_state_matches]),
                ordinal=ordinal,
            )
        )

    category_output_matches = _top_matches(
        histories,
        lambda history: min(
            _overlap_score(current.categories, history.categories),
            max(_overlap_score(current.output_fingerprints, history.output_fingerprints), _jaccard_score(current.output_fingerprints, history.output_fingerprints) * 4.0),
        ),
    )
    if category_output_matches:
        append(
            _make_edge(
                family=EDGE_FAMILY_CATEGORY_OUTPUT_ROUTE,
                source_field_ids=("category", "memo"),
                current=current,
                histories=category_output_matches,
                label_overlap_score=_average([_overlap_score(current.categories, history.categories) for history in category_output_matches]),
                axis_overlap_score=_average([_overlap_score(current.output_fingerprints, history.output_fingerprints) for history in category_output_matches]),
                ordinal=ordinal,
            )
        )

    unresolved_matches = _top_matches(
        histories,
        lambda history: _overlap_score(current.unresolved_marker_fingerprints, history.unresolved_marker_fingerprints)
        or (
            0.5
            if current.unresolved_marker_fingerprints
            and history.unresolved_marker_fingerprints
            and (
                _overlap_score(current.categories, history.categories) > 0.0
                or _overlap_score(current.emotions, history.emotions) > 0.0
                or _overlap_score(current.output_fingerprints, history.output_fingerprints) > 0.0
                or _overlap_score(current.action_fingerprints, history.action_fingerprints) > 0.0
            )
            else 0.0
        ),
    )
    if unresolved_matches:
        append(
            _make_edge(
                family=EDGE_FAMILY_UNRESOLVED_WEIGHT_REAPPEARANCE,
                source_field_ids=("memo", "memo_action", "emotion_details"),
                current=current,
                histories=unresolved_matches,
                label_overlap_score=_average(
                    [
                        max(
                            _overlap_score(current.categories, history.categories),
                            _overlap_score(current.emotions, history.emotions),
                        )
                        for history in unresolved_matches
                    ]
                )
                or 0.5,
                axis_overlap_score=_average(
                    [
                        max(
                            _overlap_score(current.unresolved_marker_fingerprints, history.unresolved_marker_fingerprints),
                            _overlap_score(current.output_fingerprints, history.output_fingerprints),
                            _overlap_score(current.action_fingerprints, history.action_fingerprints),
                        )
                        for history in unresolved_matches
                    ]
                )
                or 0.5,
                ordinal=ordinal,
            )
        )

    value_matches = tuple()
    if derived_anchor_count > 0:
        value_matches = _top_matches(
            histories,
            lambda history: max(
                _overlap_score(current.categories, history.categories),
                _overlap_score(current.output_fingerprints, history.output_fingerprints),
                _overlap_score(current.action_fingerprints, history.action_fingerprints),
            ),
        )
    if value_matches:
        append(
            _make_edge(
                family=EDGE_FAMILY_VALUE_LINE_REAPPEARANCE,
                source_field_ids=("category", "memo"),
                current=current,
                histories=value_matches,
                label_overlap_score=_average([_overlap_score(current.categories, history.categories) for history in value_matches]) or 0.5,
                axis_overlap_score=0.5 + min(0.5, derived_anchor_count / 6.0),
                ordinal=ordinal,
            )
        )

    label_route_matches = _top_matches(histories, lambda history: _connection_strength(current, history))
    if label_route_matches:
        append(
            _make_edge(
                family=EDGE_FAMILY_LABEL_ROUTE_CURRENT_ALIGNMENT,
                source_field_ids=("category", "emotion_details", "memo_action", "memo", "created_at"),
                current=current,
                histories=label_route_matches,
                label_overlap_score=_average(
                    [
                        max(
                            _overlap_score(current.categories, history.categories),
                            _overlap_score(current.emotions, history.emotions),
                        )
                        for history in label_route_matches
                    ]
                ),
                axis_overlap_score=_average([_connection_strength(current, history) for history in label_route_matches]),
                ordinal=ordinal,
            )
        )

    contrast_matches = _top_matches(
        histories,
        lambda history: _overlap_score(current.categories, history.categories)
        if _overlap_score(current.categories, history.categories) > 0.0
        and current.emotions
        and history.emotions
        and _overlap_score(current.emotions, history.emotions) == 0.0
        else 0.0,
        limit=3,
    )
    if contrast_matches:
        append(
            _make_edge(
                family=EDGE_FAMILY_CONTRAST_LINE_SHIFT,
                source_field_ids=("category", "emotion_details", "memo", "created_at"),
                current=current,
                histories=contrast_matches,
                label_overlap_score=_average([_overlap_score(current.categories, history.categories) for history in contrast_matches]),
                axis_overlap_score=0.45,
                ordinal=ordinal,
            )
        )

    return tuple(edges)


def build_user_label_connection_material(
    current_input: Any,
    *,
    source_bundle: Any = None,
    capability: Any = None,
    subscription_tier: Any = None,
    user_fact_grounding_decision: Any = None,
    observation_reply_meta: Mapping[str, Any] | None = None,
    material_quality: Any = None,
) -> UserLabelConnectionMaterial:
    """Build Phase 2/3 User Label Connection material.

    The return value is internal-only.  ``as_meta`` can be passed through later
    internal/public meta sanitizers, but this function itself does not attach the
    material to ``/emotion/submit`` responses or to RN-visible text.
    """

    tier = _normalize_tier(capability=capability, subscription_tier=subscription_tier)
    capability_source_scope = _capability_source_scope(capability, tier=tier)
    capability_history_allowed = _capability_allows_history(capability, tier=tier)
    reply_meta = dict(observation_reply_meta or {})
    grounding_meta = _resolve_grounding_decision_meta(
        capability=capability,
        subscription_tier=subscription_tier or tier,
        source_bundle=source_bundle,
        current_input=current_input,
        user_fact_grounding_decision=user_fact_grounding_decision,
        observation_reply_meta=reply_meta,
    )
    boundary_passed_for_history = _grounding_boundary_passed_for_history(
        grounding_meta,
        tier=tier,
        capability_history_allowed=capability_history_allowed,
    )
    low_information = _low_information_protected(grounding_meta=grounding_meta, observation_reply_meta=reply_meta)
    safety_required = _safety_triage_required(material_quality=material_quality, observation_reply_meta=reply_meta)

    history_read_allowed = bool(capability_history_allowed and boundary_passed_for_history and not low_information and not safety_required)
    material_source_scope = capability_source_scope if history_read_allowed else SOURCE_SCOPE_CURRENT_ONLY

    current_context = _build_point_context(
        current_input,
        source_kind=SOURCE_KIND_CURRENT_INPUT,
        point_id="current:present",
        source_scope=SOURCE_SCOPE_CURRENT_ONLY,
        selected_at_bucket="current",
    )
    current_point = current_context.point

    owned_history_points: tuple[UserLabelPoint, ...] = tuple()
    owned_history_contexts: tuple[_UserLabelPointContext, ...] = tuple()
    connection_edges: tuple[UserLabelConnectionEdge, ...] = tuple()
    same_day_count = 0
    similar_count = 0
    last_input_present = False
    derived_anchor_count = 0
    if history_read_allowed and source_bundle is not None:
        owned_history_contexts, same_day_count, similar_count, last_input_present = _build_history_point_contexts(
            source_bundle,
            source_scope=capability_source_scope,
        )
        owned_history_points = tuple(context.point for context in owned_history_contexts)
        derived_anchor_count = _derived_anchor_count(source_bundle)
        connection_edges = _build_user_label_connection_edges(
            current=current_context,
            histories=owned_history_contexts,
            derived_anchor_count=derived_anchor_count,
            low_information=low_information,
            safety_required=safety_required,
        )

    if safety_required:
        record_scope = RECORD_SCOPE_CURRENT_ONLY
        quality = MATERIAL_QUALITY_SAFETY_TRIAGE_REQUIRED
    elif low_information:
        record_scope = RECORD_SCOPE_CURRENT_ONLY
        quality = MATERIAL_QUALITY_LOW_INFORMATION_PROTECTED
    elif not capability_history_allowed and tier == "free":
        record_scope = RECORD_SCOPE_BLOCKED_FREE_TIER
        quality = MATERIAL_QUALITY_HISTORY_CONNECTION_BLOCKED
    elif capability_history_allowed and not boundary_passed_for_history:
        record_scope = RECORD_SCOPE_BLOCKED_GROUNDING_BOUNDARY
        quality = MATERIAL_QUALITY_HISTORY_CONNECTION_BLOCKED
    elif owned_history_points:
        record_scope = RECORD_SCOPE_CURRENT_PLUS_OWNED_HISTORY
        quality = MATERIAL_QUALITY_HISTORY_CONNECTION_CANDIDATE
    else:
        record_scope = RECORD_SCOPE_CURRENT_ONLY
        quality = MATERIAL_QUALITY_NO_HISTORY_AVAILABLE

    material = UserLabelConnectionMaterial(
        source_scope=material_source_scope,
        record_scope=record_scope,
        capability_tier=tier,
        history_read_allowed=history_read_allowed,
        user_fact_grounding_boundary_passed=boundary_passed_for_history,
        low_information_protected=low_information,
        current_point=current_point,
        owned_history_points=owned_history_points,
        connection_edges=connection_edges,
        material_quality=quality,
        same_day_count=same_day_count,
        similar_count=similar_count,
        last_input_present=last_input_present,
        derived_user_model_anchor_count=derived_anchor_count,
    )
    assert_user_label_connection_material_meta_contract(material.as_meta())
    return material


def build_user_label_connection_material_meta(current_input: Any, **kwargs: Any) -> dict[str, Any]:
    return build_user_label_connection_material(current_input, **kwargs).as_meta()


def assert_user_label_connection_point_meta_contract(meta: Mapping[str, Any]) -> None:
    if meta.get("schema_version") != USER_LABEL_POINT_SCHEMA_VERSION:
        raise ValueError("unexpected UserLabelPoint schema_version")
    if meta.get("point_is_tendency") is not False:
        raise ValueError("a UserLabelPoint must not be a tendency")
    evidence_anchor = meta.get("evidence_anchor") or {}
    for key in ("raw_text_included", "raw_input_included", "comment_text_body_included"):
        if evidence_anchor.get(key) is not False:
            raise ValueError(f"UserLabelPoint evidence anchor violates {key}=false")
    axes = meta.get("label_axes") or {}
    for axis in ("environment", "state", "output", "time"):
        if axis not in axes:
            raise ValueError(f"missing UserLabelPoint axis: {axis}")
        for field_id in axes.get(axis, {}).get("source_field_ids") or []:
            if field_id not in _ALLOWED_SOURCE_FIELD_VALUES:
                raise ValueError(f"unsupported source field id: {field_id}")


def assert_user_label_connection_material_meta_contract(meta: Mapping[str, Any]) -> None:
    if meta.get("schema_version") != USER_LABEL_CONNECTION_MATERIAL_SCHEMA_VERSION:
        raise ValueError("unexpected UserLabelConnectionMaterial schema_version")
    if meta.get("step") != USER_LABEL_CONNECTION_MATERIAL_STEP:
        raise ValueError("unexpected UserLabelConnectionMaterial step")
    if meta.get("current_point_present") is not True:
        raise ValueError("current point must be present")
    if meta.get("current_point"):
        assert_user_label_connection_point_meta_contract(meta["current_point"])
    for point_meta in meta.get("owned_history_points") or []:
        assert_user_label_connection_point_meta_contract(point_meta)
    summary = meta.get("owned_history_points_summary") or {}
    if summary.get("raw_text_included") is not False:
        raise ValueError("owned history summary must not include raw text")
    for edge in meta.get("connection_edges") or []:
        for key in ("raw_text_included", "comment_text_body_included", "line_is_fact"):
            if edge.get(key) is True:
                raise ValueError(f"connection edge violates {key}=false")
        score = edge.get("edge_score") or {}
        if score.get("schema_version") != USER_LABEL_CONNECTION_EDGE_SCORE_SCHEMA_VERSION:
            raise ValueError("connection edge score schema_version is required")
        if score.get("score_is_public") is not False:
            raise ValueError("connection edge score must not be public")
        for score_key in (
            "label_overlap_score",
            "axis_overlap_score",
            "evidence_record_count_score",
            "current_alignment_score",
            "low_information_penalty",
            "safety_penalty",
            "final_score",
        ):
            score_value = score.get(score_key)
            if not isinstance(score_value, (int, float)) or not 0.0 <= float(score_value) <= 1.0:
                raise ValueError(f"connection edge score out of range: {score_key}")
    for flag in _FORBIDDEN_TRUE_FLAGS:
        if meta.get(flag) is True:
            raise ValueError(f"forbidden true flag in UserLabelConnectionMaterial meta: {flag}")
    if _contains_text_payload_key(meta):
        raise ValueError("UserLabelConnectionMaterial meta must not contain raw text/comment payload keys")
    json.dumps(dict(meta), ensure_ascii=False, sort_keys=True)


# Compatibility aliases for later phases/tests.
def assert_user_label_connection_material_meta(meta: Mapping[str, Any]) -> None:
    assert_user_label_connection_material_meta_contract(meta)


__all__ = [
    "build_user_label_point",
    "build_user_label_connection_material",
    "build_user_label_connection_material_meta",
    "assert_user_label_connection_point_meta_contract",
    "assert_user_label_connection_material_meta",
    "assert_user_label_connection_material_meta_contract",
]
