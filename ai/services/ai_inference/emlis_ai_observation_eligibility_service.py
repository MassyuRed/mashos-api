# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step 2 Observation Eligibility Router for EmlisAI observation replies.

This service classifies the *current input* into either a full eligible
observation branch or the low-information observation branch.  It intentionally
stays pre-composer and meta-oriented:

* it does not generate ``comment_text``;
* it does not change the public ``observation_status`` enum;
* it does not relax Display Gate;
* it does not promote low-information input to eligible from user facts alone.

The router uses current-input evidence first.  Subscription user facts may be
kept as sanitized identifiers for focus hints, but Free always blocks them and
no user fact can turn a low-information input such as ``疲れた`` into an eligible
observation.
"""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
import json
import re
from typing import Any, Final

from emlis_ai_evidence_ledger_service import build_evidence_ledger
from emlis_ai_observation_structure_connection_service import (
    ObservationStructureConnection,
    build_observation_structure_connection,
    observation_structure_connection_forward_meta,
)
from emlis_ai_observation_reply_contract import (
    OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE,
    OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION,
    OBSERVATION_REPLY_KIND_ELIGIBLE,
    OBSERVATION_REPLY_KIND_LOW_INFORMATION,
    UNKNOWN_SLOT_CAUSE,
    UNKNOWN_SLOT_CURRENT_FEELING_TARGET,
    UNKNOWN_SLOT_DESIRED_DIRECTION,
    UNKNOWN_SLOT_EVENT,
    UNKNOWN_SLOT_RELATION,
    UNKNOWN_SLOT_TARGET,
    USER_FACT_GROUNDING_MODE_DISABLED,
    USER_FACT_GROUNDING_MODE_IMPLICIT_FOCUS,
    assert_observation_reply_meta_contract,
    build_observation_reply_meta,
)

OBSERVATION_ELIGIBILITY_ROUTER_VERSION: Final = "emlis.observation_eligibility_router.v1"
OBSERVATION_ELIGIBILITY_ROUTER_STEP: Final = "Step2_Observation_Eligibility_Router"

OBSERVATION_ELIGIBILITY_STATUS_SAFETY_BLOCKED: Final = "safety_blocked"

# The thresholds are deliberately conservative.  Step 2 owns routing only; later
# composer/display steps may add richer evidence, but user facts must never push
# low-information current input over this line by themselves.
ELIGIBLE_EVIDENCE_THRESHOLD: Final = 0.58
LOW_INFORMATION_EVIDENCE_THRESHOLD: Final = 0.34
RELATION_CONFIDENCE_THRESHOLD: Final = 0.42
ELIGIBLE_RELATION_THRESHOLD: Final = RELATION_CONFIDENCE_THRESHOLD

_SIGNAL_STATE: Final = "state"
_SIGNAL_TARGET: Final = "target"
_SIGNAL_WISH: Final = "wish"
_SIGNAL_BLOCKAGE: Final = "blockage"
_SIGNAL_CONTRAST: Final = "contrast"
_SIGNAL_REPETITION: Final = "repetition"
_SIGNAL_SELF_AWARENESS: Final = "self_awareness"
_SIGNAL_RELATION_GRAPH: Final = "relation_graph"
_SIGNAL_SAFETY_RISK: Final = "safety_risk"

_SPACE_RE: Final = re.compile(r"\s+")
_STATE_RE: Final = re.compile(
    r"(疲れ|つかれ|しんど|つら|辛|苦し|怖|こわ|不安|焦|迷|消耗|限界|無理|嫌だ|いやだ|やばい|重い|動けない|行動できない)"
)
_TARGET_RE: Final = re.compile(
    r"(環境|仕事|職場|学校|人間関係|関係|相手|家族|友達|友人|恋人|明日|今の状況|状況|生活|家|部屋|身体|体調|予定|やりたいこと|自分のこと)"
)
_WISH_RE: Final = re.compile(
    r"(変えたい|変わりたい|進みたい|逃げたい|続けたい|やめたい|辞めたい|離れたい|休みたい|頼りたい|したい|ありたい|欲しい|ほしい|このままじゃいけない|このままではいけない)"
)
_BLOCKAGE_RE: Final = re.compile(
    r"(変えられない|変えられな|変われない|変われな|できない|できな|出来ない|出来な|動けない|動けな|行動できない|行動できな|進めない|進めな|決められない|決められな|言えない|言えな|やれない|やれな|分からない|分からな|わからない|わからな|追いつかない|追いつかな|抜け出せない|抜け出せな)"
)
_CONTRAST_RE: Final = re.compile(
    r"(けど|だけど|なのに|のに|でも|一方|同時に|とはいえ|分かっているのに|わかっているのに|分かっていても|わかっていても|からこそ)"
)
_REPETITION_RE: Final = re.compile(r"(ずっと|また|何度も|何回も|最近ずっと|同じ|繰り返|繰りかえ|前にも|以前にも)")
_SELF_AWARENESS_RE: Final = re.compile(r"(分かって|わかって|理解して|気づいて|このままじゃいけない|このままではいけない)")
_VAGUE_REFERENCE_RE: Final = re.compile(r"(あれ|それ|これ|あの|その|こうな|そうな|なんか|なんとなく|結局|よくわから|よく分から)")
_LOW_INFO_SOLO_RE: Final = re.compile(
    r"^(疲れた|つかれた|しんどい|つらい|辛い|なんか無理|もう無理|無理|やばい|もう嫌だ|もういやだ|嫌だ|いやだ|怖い|こわい)$"
)
_SAFETY_RISK_RE: Final = re.compile(
    r"(死にたい|消えたい|自殺|自傷|自分を傷つけたい|殺したい|OD|過量服薬|首を吊|首吊|飛び降り|リスカ|生きていたくない|生きるのをやめたい)",
    re.IGNORECASE,
)

_TEXT_PAYLOAD_KEYS: Final = frozenset(
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
        "memo",
        "memo_text",
        "memoText",
        "current_input",
        "currentInput",
        "comment_text",
        "commentText",
        "input_feedback_comment",
        "inputFeedbackComment",
        "candidate_comment_text",
        "public_comment_text",
        "reply_text",
        "replyText",
        "surface_text",
        "realized_text",
        "body",
        "text",
    }
)
_FORBIDDEN_TRUE_FLAGS: Final = frozenset(
    {
        "raw_input_included",
        "raw_text_included",
        "comment_text_included",
        "comment_text_body_included",
        "public_status_extended",
        "observation_status_enum_extended",
        "public_response_key_change",
        "api_response_key_change",
        "api_route_changed",
        "db_physical_name_changed",
        "rn_visible_contract_changed",
        "rn_visible_title_changed",
        "display_gate_relaxed",
        "reader_gate_relaxed",
        "grounding_gate_relaxed",
        "template_gate_relaxed",
        "gate_relaxed",
        "fixed_fallback_used",
        "fixed_sentence_template_used",
        "external_ai_used",
        "local_llm_used",
        "user_fact_may_promote_to_eligible",
        "promote_low_info_to_eligible",
        "assert_current_event_from_user_fact",
        "personality_tendency_allowed",
    }
)
_SUBSCRIPTION_PLAN_KEYS: Final = frozenset({"plus", "premium", "subscription", "subscriber"})
_FREE_PLAN_KEYS: Final = frozenset({"", "free"})


def _clean(value: Any) -> str:
    return _SPACE_RE.sub(" ", str(value or "").replace("\u3000", " ")).strip()


def _clamp(value: float, *, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, float(value)))


def _dedupe(values: Iterable[Any] | Any | None) -> list[str]:
    if values is None:
        return []
    if isinstance(values, (str, bytes, bytearray)):
        iterable: Iterable[Any] = [values]
    elif isinstance(values, Iterable):
        iterable = values
    else:
        iterable = [values]
    out: list[str] = []
    for value in iterable:
        item = _clean(value)
        if item and item not in out:
            out.append(item)
    return out


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


def _current_input_for_ledger(current_input: Any) -> dict[str, Any]:
    if isinstance(current_input, Mapping):
        return dict(current_input)
    return {"memo": _clean(current_input)}


def _current_input_text(current_input: Any) -> str:
    if isinstance(current_input, Mapping):
        parts = [current_input.get("memo"), current_input.get("memo_action")]
        return _clean("。".join(_clean(part) for part in parts if _clean(part)))
    return _clean(current_input)


def _normalize_plan(raw_plan: Any = None, capability: Any = None) -> str:
    candidates = [raw_plan]
    if capability is not None:
        candidates.extend(
            [
                getattr(capability, "tier", None),
                getattr(capability, "subscription_tier", None),
                getattr(capability, "plan", None),
            ]
        )
        if getattr(capability, "model_read_enabled", False) or getattr(capability, "include_derived_user_model", False):
            candidates.append("subscription")
    saw_explicit_free = False
    for candidate in candidates:
        value = _clean(candidate).lower()
        if value in _SUBSCRIPTION_PLAN_KEYS:
            return "subscription"
        if value == "free":
            saw_explicit_free = True
    return "free" if saw_explicit_free or not candidates else "free"


def _sanitize_fact_refs(user_facts: Any) -> list[dict[str, Any]]:
    if user_facts is None:
        return []
    if isinstance(user_facts, Mapping):
        iterable: Iterable[Any] = [user_facts]
    elif isinstance(user_facts, Sequence) and not isinstance(user_facts, (str, bytes, bytearray)):
        iterable = user_facts
    else:
        iterable = [user_facts]

    refs: list[dict[str, Any]] = []
    for index, item in enumerate(iterable):
        if isinstance(item, Mapping):
            fact_id = _clean(item.get("fact_id") or item.get("id") or item.get("ref_id") or item.get("source_id"))
            if not fact_id:
                fact_id = f"user_fact_ref_{index + 1}"
            ref: dict[str, Any] = {"fact_id": fact_id}
            for key in ("source", "source_kind", "kind", "ref_id", "mode", "role"):
                value = _clean(item.get(key))
                if value:
                    ref[key] = value
            refs.append(ref)
        else:
            fact_id = _clean(item)
            if fact_id:
                refs.append({"fact_id": fact_id})
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for ref in refs:
        key = json.dumps(ref, ensure_ascii=False, sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(ref)
    return deduped


def _iter_relation_graph_items(observation_graph: Any) -> list[Any]:
    if observation_graph is None:
        return []
    if isinstance(observation_graph, Mapping):
        items: list[Any] = []
        for key in ("edges", "relations", "relation_edges", "graph_edges"):
            value = observation_graph.get(key)
            if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
                items.extend(value)
        return items
    items = []
    for attr in ("edges", "relations", "relation_edges", "graph_edges"):
        value = getattr(observation_graph, attr, None)
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            items.extend(value)
    return items


def _relation_graph_confidence(observation_graph: Any) -> tuple[float, list[str]]:
    relation_types: list[str] = []
    confidences: list[float] = []
    for item in _iter_relation_graph_items(observation_graph):
        if isinstance(item, Mapping):
            relation_type = _clean(item.get("relation_type") or item.get("type") or item.get("edge_role"))
            raw_confidence = item.get("confidence", 0.0)
        else:
            relation_type = _clean(getattr(item, "relation_type", None) or getattr(item, "type", None) or getattr(item, "edge_role", None))
            raw_confidence = getattr(item, "confidence", 0.0)
        if relation_type:
            relation_types.append(relation_type)
        try:
            confidences.append(_clamp(float(raw_confidence)))
        except (TypeError, ValueError):
            confidences.append(0.5)
    if not relation_types:
        return 0.0, []
    base = max(confidences or [0.5])
    return _clamp(max(0.42, base)), _dedupe(relation_types)


def _mapping_get(value: Any, *keys: str) -> Any:
    if isinstance(value, Mapping):
        for key in keys:
            if key in value:
                return value.get(key)
    for key in keys:
        item = getattr(value, key, None)
        if item is not None:
            return item
    return None


def _span_id(span: Any, index: int) -> str:
    return _clean(_mapping_get(span, "span_id", "id", "ref_id")) or f"s{index + 1}"


def _span_source(span: Any) -> str:
    return _clean(_mapping_get(span, "source_field", "source", "field")) or "memo"


def _span_type(span: Any) -> str:
    return _clean(_mapping_get(span, "detected_type", "type", "role")) or "event"


def _span_text(span: Any) -> str:
    return _clean(_mapping_get(span, "raw_text", "source_text", "value"))


def _span_confidence(span: Any) -> float:
    try:
        return _clamp(float(_mapping_get(span, "confidence") if _mapping_get(span, "confidence") is not None else 1.0))
    except (TypeError, ValueError):
        return 1.0


def _detect_signals_for_text(text: str, detected_type: str = "") -> set[str]:
    signals: set[str] = set()
    if _SAFETY_RISK_RE.search(text) or detected_type == "safety_risk":
        signals.add(_SIGNAL_SAFETY_RISK)
    if _STATE_RE.search(text) or detected_type in {"emotion", "fear", "limit_signal"}:
        signals.add(_SIGNAL_STATE)
    if _TARGET_RE.search(text):
        signals.add(_SIGNAL_TARGET)
    if _WISH_RE.search(text) or detected_type == "wish":
        signals.add(_SIGNAL_WISH)
    if _BLOCKAGE_RE.search(text) or detected_type == "constraint":
        signals.add(_SIGNAL_BLOCKAGE)
    if _CONTRAST_RE.search(text) or detected_type == "relation_marker":
        signals.add(_SIGNAL_CONTRAST)
    if _REPETITION_RE.search(text):
        signals.add(_SIGNAL_REPETITION)
    if _SELF_AWARENESS_RE.search(text) or detected_type == "self_awareness":
        signals.add(_SIGNAL_SELF_AWARENESS)
    return signals


def _roles_for_signals(signals: Iterable[str]) -> list[str]:
    role_by_signal = {
        _SIGNAL_STATE: "state",
        _SIGNAL_TARGET: "target",
        _SIGNAL_WISH: "wish",
        _SIGNAL_BLOCKAGE: "blockage",
        _SIGNAL_CONTRAST: "contrast",
        _SIGNAL_REPETITION: "repetition",
        _SIGNAL_SELF_AWARENESS: "self_awareness",
        _SIGNAL_RELATION_GRAPH: "relation_graph",
        _SIGNAL_SAFETY_RISK: "safety_risk",
    }
    return [role_by_signal[signal] for signal in signals if signal in role_by_signal]


@dataclass(frozen=True)
class ObservationEligibilityDecision:
    """Current-input routing decision produced by Step 2."""

    status: str
    observation_reply_kind: str
    eligibility_status: str
    eligible_for_full_observation: bool
    question_required: bool
    primary_reason: str
    current_input_evidence_score: float
    relation_confidence: float
    ambiguity_reasons: tuple[str, ...] = field(default_factory=tuple)
    known_fragments: tuple[Mapping[str, Any], ...] = field(default_factory=tuple)
    unknown_slots: tuple[str, ...] = field(default_factory=tuple)
    detected_signal_roles: tuple[str, ...] = field(default_factory=tuple)
    relation_types: tuple[str, ...] = field(default_factory=tuple)
    plan: str = "free"
    user_fact_allowed: bool = False
    user_fact_read_enabled: bool = False
    user_fact_may_hint: bool = False
    user_fact_may_promote_to_eligible: bool = False
    facts_used: tuple[Mapping[str, Any], ...] = field(default_factory=tuple)
    facts_ignored: tuple[Mapping[str, Any], ...] = field(default_factory=tuple)
    free_user_fact_blocked: bool = False
    observation_reply_meta: Mapping[str, Any] = field(default_factory=dict)
    user_fact_raw_text_stripped: bool = False
    observation_structure_connection: Mapping[str, Any] = field(default_factory=dict)

    @property
    def version(self) -> str:
        return OBSERVATION_ELIGIBILITY_ROUTER_VERSION

    @property
    def step(self) -> str:
        return OBSERVATION_ELIGIBILITY_ROUTER_STEP

    def as_meta(self) -> dict[str, Any]:
        meta: dict[str, Any] = {
            "version": OBSERVATION_ELIGIBILITY_ROUTER_VERSION,
            "schema_version": OBSERVATION_ELIGIBILITY_ROUTER_VERSION,
            "source_step": OBSERVATION_ELIGIBILITY_ROUTER_STEP,
            "step": OBSERVATION_ELIGIBILITY_ROUTER_STEP,
            "observation_eligibility_router_ready": True,
            "status": self.status,
            "observation_reply_kind": self.observation_reply_kind,
            "eligibility_status": self.eligibility_status,
            "eligible_for_full_observation": bool(self.eligible_for_full_observation),
            "question_required": bool(self.question_required),
            "primary_reason": self.primary_reason,
            "current_input_evidence_score": round(float(self.current_input_evidence_score), 4),
            "relation_confidence": round(float(self.relation_confidence), 4),
            "ambiguity_reasons": list(self.ambiguity_reasons),
            "known_fragments": [dict(item) for item in self.known_fragments],
            "unknown_slots": list(self.unknown_slots),
            "detected_signal_roles": list(self.detected_signal_roles),
            "relation_types": list(self.relation_types),
            "plan": self.plan,
            "user_fact_allowed": bool(self.user_fact_allowed),
            "user_fact_read_enabled": bool(self.user_fact_read_enabled),
            "user_fact_may_hint": bool(self.user_fact_may_hint),
            "user_fact_may_promote_to_eligible": False,
            "must_not_promote_low_info_to_eligible": True,
            "must_not_assert_current_event_from_user_fact": True,
            "free_user_fact_blocked": bool(self.free_user_fact_blocked),
            "facts_used": [dict(item) for item in self.facts_used],
            "facts_ignored": [dict(item) for item in self.facts_ignored],
            "user_fact_raw_text_stripped": bool(self.user_fact_raw_text_stripped),
            "observation_reply_meta": dict(self.observation_reply_meta or {}),
            "observation_structure_connection": dict(self.observation_structure_connection or {}),
            "observation_structure_gate": dict((self.observation_structure_connection or {}).get("gate_material") or {}),
            "observation_structure_dictionary_connected": bool(self.observation_structure_connection),
            "phase4_gate_composer_connection_ready": bool(
                (self.observation_structure_connection or {}).get("phase4_gate_composer_connection_ready")
                or (self.observation_structure_connection or {}).get("connection_ready")
            ),
            "structure_gate_policy_connected": bool(self.observation_structure_connection),
            "structure_relation_ids": list((self.observation_structure_connection or {}).get("selected_relation_ids") or []),
            "structure_entry_ids": list((self.observation_structure_connection or {}).get("selected_entry_ids") or []),
            "structure_question_ids": list((self.observation_structure_connection or {}).get("selected_question_ids") or []),
            "structure_low_information_candidate": bool(
                (self.observation_structure_connection or {}).get("low_information_unknown_slots")
            ),
            "structure_dictionary_candidates_do_not_promote_low_information": True,
            "current_input_only_eligibility": True,
            "user_fact_used_for_current_event_assertion": False,
            "raw_input_included": False,
            "raw_text_included": False,
            "comment_text_included": False,
            "comment_text_body_included": False,
            "comment_text_generated": False,
            "public_status_extended": False,
            "observation_status_enum_extended": False,
            "api_response_key_change": False,
            "api_route_changed": False,
            "db_physical_name_changed": False,
            "rn_visible_contract_changed": False,
            "rn_visible_title_changed": False,
            "display_gate_relaxed": False,
            "reader_gate_relaxed": False,
            "grounding_gate_relaxed": False,
            "template_gate_relaxed": False,
            "fixed_fallback_used": False,
            "fixed_sentence_template_used": False,
            "external_ai_used": False,
            "local_llm_used": False,
        }
        assert_observation_eligibility_decision_contract(meta)
        return meta


def _known_fragment(span: Any, index: int, role: str) -> dict[str, Any]:
    return {
        "evidence_span_id": _span_id(span, index),
        "source_field": _span_source(span),
        "role": role,
        "confidence": round(_span_confidence(span), 4),
        "current_input_evidence": True,
        "raw_input_included": False,
    }


def _analyze_current_input(current_input: Any, evidence_ledger: Any = None) -> tuple[set[str], list[dict[str, Any]], str, list[Any]]:
    data = _current_input_for_ledger(current_input)
    spans = list(evidence_ledger) if evidence_ledger is not None else list(build_evidence_ledger(data))
    text = _current_input_text(current_input)
    aggregate_signals = _detect_signals_for_text(text)
    known_fragments: list[dict[str, Any]] = []

    # Score only current-input textual and emotion evidence. Category labels such
    # as ``生活`` may be useful later, but should not make an otherwise vague
    # input eligible.
    for index, span in enumerate(spans):
        source_field = _span_source(span)
        detected_type = _span_type(span)
        raw_text = _span_text(span)
        if source_field not in {"memo", "memo_action", "emotion_details", "emotions"}:
            continue
        signals = _detect_signals_for_text(raw_text, detected_type)
        aggregate_signals.update(signals)
        for role in _roles_for_signals(signals):
            if role == "safety_risk":
                continue
            fragment = _known_fragment(span, index, role)
            if fragment not in known_fragments:
                known_fragments.append(fragment)
    return aggregate_signals, known_fragments, text, spans


def _score_current_evidence(signals: set[str], known_fragments: Sequence[Mapping[str, Any]]) -> float:
    score = 0.0
    if _SIGNAL_STATE in signals:
        score += 0.22
    if _SIGNAL_TARGET in signals:
        score += 0.18
    if _SIGNAL_WISH in signals:
        score += 0.18
    if _SIGNAL_BLOCKAGE in signals:
        score += 0.18
    if _SIGNAL_CONTRAST in signals:
        score += 0.12
    if _SIGNAL_REPETITION in signals:
        score += 0.10
    if _SIGNAL_SELF_AWARENESS in signals:
        score += 0.08
    if _SIGNAL_RELATION_GRAPH in signals:
        score += 0.08
    # Multiple grounded fragments help, but only slightly; the branch remains
    # current-input structure driven rather than length driven.
    score += min(0.08, len(known_fragments) * 0.015)
    return _clamp(score)


def _score_relation_confidence(signals: set[str], graph_confidence: float) -> float:
    confidence = graph_confidence
    if _SIGNAL_CONTRAST in signals and (_SIGNAL_WISH in signals or _SIGNAL_BLOCKAGE in signals):
        confidence = max(confidence, 0.58)
    if _SIGNAL_WISH in signals and _SIGNAL_BLOCKAGE in signals:
        confidence = max(confidence, 0.62)
    if _SIGNAL_STATE in signals and _SIGNAL_TARGET in signals:
        confidence = max(confidence, 0.44)
    if _SIGNAL_SELF_AWARENESS in signals and _SIGNAL_BLOCKAGE in signals:
        confidence = max(confidence, 0.50)
    if _SIGNAL_REPETITION in signals and (_SIGNAL_STATE in signals or _SIGNAL_TARGET in signals):
        confidence = max(confidence, 0.38)
    return _clamp(confidence)


def _detect_ambiguity(text: str, signals: set[str], evidence_score: float, relation_confidence: float) -> tuple[list[str], list[str]]:
    reasons: list[str] = []
    unknown_slots: list[str] = []
    normalized = _clean(text)
    vague_matches = _VAGUE_REFERENCE_RE.findall(normalized)
    low_info_solo = bool(_LOW_INFO_SOLO_RE.match(normalized)) or len(normalized) <= 5

    if _SIGNAL_TARGET not in signals:
        reasons.append("target_missing")
        unknown_slots.extend([UNKNOWN_SLOT_TARGET, UNKNOWN_SLOT_CURRENT_FEELING_TARGET])
    if _SIGNAL_STATE in signals and _SIGNAL_TARGET not in signals:
        reasons.append("event_missing_for_state")
        unknown_slots.append(UNKNOWN_SLOT_EVENT)
    if _SIGNAL_WISH not in signals and _SIGNAL_BLOCKAGE not in signals and _SIGNAL_STATE in signals:
        reasons.append("cause_or_direction_missing")
        unknown_slots.extend([UNKNOWN_SLOT_CAUSE, UNKNOWN_SLOT_DESIRED_DIRECTION])
    if relation_confidence < RELATION_CONFIDENCE_THRESHOLD:
        reasons.append("relation_confidence_low")
        unknown_slots.append(UNKNOWN_SLOT_RELATION)
    if vague_matches and _SIGNAL_TARGET not in signals:
        reasons.append("vague_reference_without_target")
        unknown_slots.extend([UNKNOWN_SLOT_EVENT, UNKNOWN_SLOT_TARGET, UNKNOWN_SLOT_RELATION])
    if low_info_solo and evidence_score < ELIGIBLE_EVIDENCE_THRESHOLD:
        reasons.append("short_or_single_emotion_only")
        reasons.append("short_emotion_or_load_only")
        unknown_slots.append(UNKNOWN_SLOT_EVENT)
    if not normalized:
        reasons.append("empty_current_input")
        unknown_slots.extend([UNKNOWN_SLOT_EVENT, UNKNOWN_SLOT_TARGET])
    return _dedupe(reasons), _dedupe(unknown_slots)


def _has_strong_current_relation(signals: set[str], relation_confidence: float) -> bool:
    if _SIGNAL_WISH in signals and _SIGNAL_BLOCKAGE in signals:
        return True
    if _SIGNAL_CONTRAST in signals and (
        (_SIGNAL_WISH in signals and _SIGNAL_STATE in signals)
        or (_SIGNAL_BLOCKAGE in signals and (_SIGNAL_STATE in signals or _SIGNAL_SELF_AWARENESS in signals))
    ):
        return True
    if _SIGNAL_STATE in signals and _SIGNAL_TARGET in signals and relation_confidence >= RELATION_CONFIDENCE_THRESHOLD:
        return True
    if _SIGNAL_RELATION_GRAPH in signals and relation_confidence >= RELATION_CONFIDENCE_THRESHOLD:
        return True
    return False


def _build_decision(
    *,
    status: str,
    observation_reply_kind: str,
    primary_reason: str,
    current_input_evidence_score: float,
    relation_confidence: float,
    ambiguity_reasons: Sequence[str],
    known_fragments: Sequence[Mapping[str, Any]],
    unknown_slots: Sequence[str],
    detected_signal_roles: Sequence[str],
    relation_types: Sequence[str],
    plan: str,
    sanitized_facts: Sequence[Mapping[str, Any]],
    facts_ignored: Sequence[Mapping[str, Any]],
    free_user_fact_blocked: bool,
    user_fact_raw_text_stripped: bool = False,
    observation_structure_connection: Mapping[str, Any] | None = None,
) -> ObservationEligibilityDecision:
    eligible = observation_reply_kind == OBSERVATION_REPLY_KIND_ELIGIBLE
    low_info = observation_reply_kind == OBSERVATION_REPLY_KIND_LOW_INFORMATION
    user_fact_allowed = plan == "subscription"
    facts_used = tuple(dict(item) for item in sanitized_facts) if user_fact_allowed else tuple()
    user_fact_may_hint = bool(user_fact_allowed and facts_used)
    fact_mode = USER_FACT_GROUNDING_MODE_IMPLICIT_FOCUS if user_fact_may_hint else USER_FACT_GROUNDING_MODE_DISABLED

    # Pass attempted Free facts into the Step 1 contract builder as sanitized
    # identifiers so its own guard can mark free_user_fact_blocked=true, while
    # still returning facts_used=[] in the resulting contract.
    facts_for_contract = list(sanitized_facts) if free_user_fact_blocked else list(facts_used)
    observation_reply_meta = build_observation_reply_meta(
        observation_reply_kind=observation_reply_kind,
        plan=plan,
        eligible_for_full_observation=eligible,
        question_required=low_info,
        user_fact_grounding_mode=fact_mode,
        user_fact_allowed=user_fact_allowed or free_user_fact_blocked,
        user_fact_may_hint=user_fact_may_hint,
        facts_used=facts_for_contract,
        unknown_slots=list(unknown_slots),
        inference_depths=[1, 2, 3] if eligible else [],
        primary_reason=primary_reason,
    )
    assert_observation_reply_meta_contract(observation_reply_meta)

    normalized_ambiguity = list(_dedupe(ambiguity_reasons))
    if low_info and user_fact_may_hint and "user_fact_not_allowed_to_promote_low_information" not in normalized_ambiguity:
        normalized_ambiguity.append("user_fact_not_allowed_to_promote_low_information")

    return ObservationEligibilityDecision(
        status=status,
        observation_reply_kind=observation_reply_kind,
        eligibility_status=(
            OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE if eligible else OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION
        ),
        eligible_for_full_observation=eligible,
        question_required=low_info,
        primary_reason=primary_reason,
        current_input_evidence_score=current_input_evidence_score,
        relation_confidence=relation_confidence,
        ambiguity_reasons=normalized_ambiguity,
        known_fragments=[dict(item) for item in known_fragments],
        unknown_slots=_dedupe(unknown_slots),
        detected_signal_roles=_dedupe(detected_signal_roles),
        relation_types=_dedupe(relation_types),
        plan=plan,
        user_fact_allowed=user_fact_allowed,
        user_fact_read_enabled=user_fact_allowed,
        user_fact_may_hint=user_fact_may_hint,
        user_fact_may_promote_to_eligible=False,
        facts_used=[dict(item) for item in facts_used],
        facts_ignored=[dict(item) for item in facts_ignored],
        free_user_fact_blocked=free_user_fact_blocked,
        observation_reply_meta=observation_reply_meta,
        user_fact_raw_text_stripped=bool(user_fact_raw_text_stripped),
        observation_structure_connection=dict(observation_structure_connection or {}),
    )


def _structure_signal_to_internal_signal(role: str) -> str | None:
    mapping = {
        "state": _SIGNAL_STATE,
        "target": _SIGNAL_TARGET,
        "wish": _SIGNAL_WISH,
        "blockage": _SIGNAL_BLOCKAGE,
        "contrast": _SIGNAL_CONTRAST,
        "repetition": _SIGNAL_REPETITION,
        "self_awareness": _SIGNAL_SELF_AWARENESS,
        "relation_graph": _SIGNAL_RELATION_GRAPH,
    }
    return mapping.get(_clean(role))


def _structure_roles_from_relation_ids(relation_ids: Sequence[str]) -> list[str]:
    roles: list[str] = []
    if any(item in relation_ids for item in ("state_text_gap", "emotion_nesting", "low_information_weight")):
        roles.append("state")
    if any(item in relation_ids for item in ("thought_action_discrepancy", "category_overlap", "category_parallel")):
        roles.append("relation_graph")
    if "thought_action_discrepancy" in relation_ids:
        roles.extend(["target", "contrast"])
    if any(item in relation_ids for item in ("desire_stagnation", "action_blocked", "pressure_gap")):
        roles.extend(["wish", "blockage"])
    if "self_insight_discovery" in relation_ids:
        roles.append("self_awareness")
    return _dedupe(roles)


def _structure_relation_confidence_hint(relation_ids: Sequence[str], *, low_information: bool = False) -> float:
    ids = set(relation_ids)
    if low_information or "low_information_weight" in ids:
        return 0.33
    if "thought_action_discrepancy" in ids:
        return 0.62
    if "category_overlap" in ids:
        return 0.52
    if "state_text_gap" in ids:
        return 0.44
    if ids.intersection({"desire_stagnation", "action_blocked", "pressure_gap"}):
        return 0.50
    return 0.0


def _merge_structure_connection_into_gate(
    *,
    signals: set[str],
    known_fragments: list[dict[str, Any]],
    relation_types: Sequence[str],
    structure_connection: ObservationStructureConnection | Mapping[str, Any] | None,
) -> tuple[list[str], dict[str, Any]]:
    if structure_connection is None:
        return _dedupe(relation_types), {}
    meta = observation_structure_connection_forward_meta(structure_connection)
    selected_relation_ids = _dedupe(meta.get("selected_relation_ids") or [])
    derived_roles = _structure_roles_from_relation_ids(selected_relation_ids)
    for role in _dedupe([*(meta.get("gate_signal_roles") or []), *derived_roles]):
        signal = _structure_signal_to_internal_signal(role)
        if signal:
            signals.add(signal)
    for relation_id in selected_relation_ids:
        safe_fragment = {
            "evidence_span_id": f"structure_dictionary:{relation_id}",
            "source_field": "observation_structure_dictionary",
            "role": "relation_graph",
            "confidence": 0.33,
            "current_input_evidence": False,
            "dictionary_material_only": True,
            "raw_input_included": False,
        }
        if safe_fragment not in known_fragments:
            known_fragments.append(safe_fragment)
    for fragment in meta.get("gate_known_fragments") or []:
        if not isinstance(fragment, Mapping):
            continue
        safe_fragment = dict(fragment)
        safe_fragment["raw_input_included"] = False
        safe_fragment.setdefault("current_input_evidence", False)
        safe_fragment.setdefault("dictionary_material_only", True)
        if safe_fragment not in known_fragments:
            known_fragments.append(safe_fragment)
    input_summary = meta.get("input_bundle_summary") if isinstance(meta.get("input_bundle_summary"), Mapping) else {}
    low_information = bool(input_summary.get("is_low_information") or "low_information_weight" in selected_relation_ids)
    if low_information:
        meta["low_information_unknown_slots"] = [
            UNKNOWN_SLOT_EVENT,
            UNKNOWN_SLOT_TARGET,
            UNKNOWN_SLOT_RELATION,
            UNKNOWN_SLOT_CAUSE,
        ]
    meta["gate_relation_ids"] = selected_relation_ids
    meta["gate_signal_roles"] = _dedupe([*(meta.get("gate_signal_roles") or []), *derived_roles])
    meta["relation_confidence_hint"] = _structure_relation_confidence_hint(selected_relation_ids, low_information=low_information)
    meta["current_input_evidence_bonus"] = 0.0
    merged_relation_types = _dedupe([*relation_types, *selected_relation_ids])
    return merged_relation_types, meta


def route_observation_eligibility(
    *,
    current_input: Any,
    evidence_ledger: Any = None,
    observation_graph: Any = None,
    capability: Any = None,
    subscription_tier: Any = None,
    user_facts: Any = None,
    observation_structure_connection: ObservationStructureConnection | Mapping[str, Any] | None = None,
    observation_structure_dictionary: Any = None,
) -> ObservationEligibilityDecision:
    """Route the current input to eligible or low-information observation.

    Phase 4 attaches the structure-observation dictionary as Gate material only:
    relation ids and forbidden-inference boundaries may strengthen or soften the
    routing decision, but dictionary surface policy is never returned as a
    completed reply and user facts still cannot promote low-information input.
    """

    plan = _normalize_plan(subscription_tier, capability)
    sanitized_facts = _sanitize_fact_refs(user_facts)
    user_fact_raw_text_stripped = _contains_text_payload_key(user_facts)
    facts_ignored = sanitized_facts if plan == "free" else []
    free_user_fact_blocked = bool(plan == "free" and sanitized_facts)

    signals, known_fragments, text, _spans = _analyze_current_input(current_input, evidence_ledger)
    structure_connection = observation_structure_connection or build_observation_structure_connection(
        current_input=current_input,
        evidence_ledger=_spans,
        dictionary=observation_structure_dictionary,
    )
    graph_confidence, relation_types = _relation_graph_confidence(observation_graph)
    if graph_confidence > 0.0:
        signals.add(_SIGNAL_RELATION_GRAPH)
        known_fragments.append(
            {
                "evidence_span_id": "relation_graph",
                "source_field": "observation_graph",
                "role": "relation_graph",
                "confidence": round(graph_confidence, 4),
                "current_input_evidence": True,
                "raw_input_included": False,
            }
        )

    relation_types, structure_connection_meta = _merge_structure_connection_into_gate(
        signals=signals,
        known_fragments=known_fragments,
        relation_types=relation_types,
        structure_connection=structure_connection,
    )
    try:
        structure_relation_hint = float(structure_connection_meta.get("relation_confidence_hint") or 0.0)
    except (TypeError, ValueError):
        structure_relation_hint = 0.0
    try:
        structure_evidence_bonus = float(structure_connection_meta.get("current_input_evidence_bonus") or 0.0)
    except (TypeError, ValueError):
        structure_evidence_bonus = 0.0

    if _SIGNAL_SAFETY_RISK in signals:
        # Step 2 observes the safety boundary and does not turn it into an
        # ordinary Emlis observation branch. Runtime handling stays owned by the
        # existing safety/error path.
        return ObservationEligibilityDecision(
            status=OBSERVATION_ELIGIBILITY_STATUS_SAFETY_BLOCKED,
            observation_reply_kind=OBSERVATION_ELIGIBILITY_STATUS_SAFETY_BLOCKED,
            eligibility_status=OBSERVATION_ELIGIBILITY_STATUS_SAFETY_BLOCKED,
            eligible_for_full_observation=False,
            question_required=False,
            primary_reason="safety_boundary_required",
            current_input_evidence_score=0.0,
            relation_confidence=0.0,
            ambiguity_reasons=("safety_boundary_required",),
            known_fragments=(),
            unknown_slots=(),
            detected_signal_roles=("safety_risk",),
            relation_types=(),
            plan=plan,
            user_fact_allowed=plan == "subscription",
            user_fact_read_enabled=plan == "subscription",
            user_fact_may_hint=False,
            user_fact_may_promote_to_eligible=False,
            facts_used=(),
            facts_ignored=tuple(dict(item) for item in facts_ignored),
            free_user_fact_blocked=free_user_fact_blocked,
            observation_reply_meta={},
            observation_structure_connection=structure_connection_meta,
        )

    evidence_score = _clamp(_score_current_evidence(signals, known_fragments) + max(0.0, structure_evidence_bonus))
    relation_confidence = max(_score_relation_confidence(signals, graph_confidence), structure_relation_hint)
    relation_confidence = _clamp(relation_confidence)
    if structure_connection_meta.get("low_information_unknown_slots") and "state_text_gap" not in relation_types:
        # Dictionary-only low-information candidates such as word_muri must not
        # turn a short input into a high-confidence relation.
        relation_confidence = min(relation_confidence, structure_relation_hint or 0.33)
    ambiguity_reasons, unknown_slots = _detect_ambiguity(text, signals, evidence_score, relation_confidence)
    structure_unknown_slots = _dedupe(structure_connection_meta.get("low_information_unknown_slots") or [])
    if structure_unknown_slots:
        unknown_slots = _dedupe([*unknown_slots, *structure_unknown_slots])
        if "structure_dictionary_low_information_boundary" not in ambiguity_reasons:
            ambiguity_reasons.append("structure_dictionary_low_information_boundary")
    signal_roles = _roles_for_signals(signals)

    has_strong_relation = _has_strong_current_relation(signals, relation_confidence)
    high_ambiguity = "vague_reference_without_target" in ambiguity_reasons or "empty_current_input" in ambiguity_reasons
    low_information = high_ambiguity or evidence_score < LOW_INFORMATION_EVIDENCE_THRESHOLD
    # The structure dictionary may mark relations such as state_text_gap as
    # meaningful while still preserving low-information unknown slots.  Keep the
    # branch low-information whenever the dictionary says the event/relation is
    # still not grounded enough; dictionary relations alone must not upgrade it.
    if structure_unknown_slots:
        low_information = True
        has_strong_relation = False

    if has_strong_relation and not high_ambiguity and evidence_score >= LOW_INFORMATION_EVIDENCE_THRESHOLD:
        primary_reason = "current_input_has_strong_relation"
        return _build_decision(
            status=OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE,
            observation_reply_kind=OBSERVATION_REPLY_KIND_ELIGIBLE,
            primary_reason=primary_reason,
            current_input_evidence_score=evidence_score,
            relation_confidence=relation_confidence,
            ambiguity_reasons=(),
            known_fragments=known_fragments,
            unknown_slots=(),
            detected_signal_roles=signal_roles,
            relation_types=relation_types,
            plan=plan,
            sanitized_facts=sanitized_facts,
            facts_ignored=facts_ignored,
            free_user_fact_blocked=free_user_fact_blocked,
            user_fact_raw_text_stripped=user_fact_raw_text_stripped,
            observation_structure_connection=structure_connection_meta,
        )

    if not low_information and evidence_score >= ELIGIBLE_EVIDENCE_THRESHOLD and relation_confidence >= RELATION_CONFIDENCE_THRESHOLD:
        primary_reason = "current_input_evidence_threshold_met"
        return _build_decision(
            status=OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE,
            observation_reply_kind=OBSERVATION_REPLY_KIND_ELIGIBLE,
            primary_reason=primary_reason,
            current_input_evidence_score=evidence_score,
            relation_confidence=relation_confidence,
            ambiguity_reasons=(),
            known_fragments=known_fragments,
            unknown_slots=(),
            detected_signal_roles=signal_roles,
            relation_types=relation_types,
            plan=plan,
            sanitized_facts=sanitized_facts,
            facts_ignored=facts_ignored,
            free_user_fact_blocked=free_user_fact_blocked,
            user_fact_raw_text_stripped=user_fact_raw_text_stripped,
            observation_structure_connection=structure_connection_meta,
        )

    reason = "insufficient_current_input_evidence"
    if high_ambiguity:
        reason = "current_input_ambiguous"
    elif relation_confidence < RELATION_CONFIDENCE_THRESHOLD:
        reason = "insufficient_relation_confidence"

    return _build_decision(
        status=OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION,
        observation_reply_kind=OBSERVATION_REPLY_KIND_LOW_INFORMATION,
        primary_reason=reason,
        current_input_evidence_score=evidence_score,
        relation_confidence=relation_confidence,
        ambiguity_reasons=ambiguity_reasons,
        known_fragments=known_fragments,
        unknown_slots=unknown_slots or [UNKNOWN_SLOT_EVENT],
        detected_signal_roles=signal_roles,
        relation_types=relation_types,
        plan=plan,
        sanitized_facts=sanitized_facts,
        facts_ignored=facts_ignored,
        free_user_fact_blocked=free_user_fact_blocked,
        observation_structure_connection=structure_connection_meta,
    )

def route_emlis_observation_eligibility(
    current_input: Any = None,
    **kwargs: Any,
) -> ObservationEligibilityDecision:
    """Named wrapper for the EmlisAI Step 2 router."""

    return route_observation_eligibility(current_input=current_input, **kwargs)


def assert_observation_eligibility_decision_meta(
    value: Mapping[str, Any],
    *,
    source: str = "observation_eligibility_decision",
) -> None:
    """Alias kept for callers that refer to the decision payload as meta."""

    assert_observation_eligibility_decision_contract(value, source=source)


def dump_observation_eligibility_decision_meta(value: ObservationEligibilityDecision | Mapping[str, Any]) -> str:
    """Alias kept for callers that refer to the decision payload as meta."""

    return dump_observation_eligibility_decision(value)


def route_emlis_observation_eligibility(
    current_input: Any,
    **kwargs: Any,
) -> ObservationEligibilityDecision:
    """Backward-friendly positional alias for Step 2 router integration/tests."""

    return route_observation_eligibility(current_input=current_input, **kwargs)


def assert_observation_eligibility_decision_contract(
    value: Mapping[str, Any] | ObservationEligibilityDecision,
    *,
    source: str = "observation_eligibility_decision",
) -> None:
    """Validate Step 2 decision meta without permitting text or contract drift."""

    if isinstance(value, ObservationEligibilityDecision):
        value = value.as_meta()
    if not isinstance(value, Mapping):
        raise ValueError(f"{source} must be a mapping")
    if _contains_text_payload_key(value):
        raise ValueError(f"{source} must stay meta-only and must not include raw/comment text keys")
    for key in _FORBIDDEN_TRUE_FLAGS:
        if value.get(key) is True:
            raise ValueError(f"{source} violates fixed contract: {key}=true")
    status = _clean(value.get("status"))
    if status == OBSERVATION_ELIGIBILITY_STATUS_SAFETY_BLOCKED:
        return
    if status not in {OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE, OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION}:
        raise ValueError(f"{source} has unsupported status: {status or '<empty>'}")
    kind = _clean(value.get("observation_reply_kind"))
    if status == OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE:
        if kind != OBSERVATION_REPLY_KIND_ELIGIBLE:
            raise ValueError("eligible decision must use eligible_observation reply kind")
        if value.get("eligible_for_full_observation") is not True:
            raise ValueError("eligible decision must be full-observation eligible")
    if status == OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION:
        if kind != OBSERVATION_REPLY_KIND_LOW_INFORMATION:
            raise ValueError("low-information decision must use low_information_observation reply kind")
        if value.get("eligible_for_full_observation") is True:
            raise ValueError("low-information decision must not be full-observation eligible")
        if value.get("question_required") is not True:
            raise ValueError("low-information decision must require question")
    if value.get("user_fact_may_promote_to_eligible") is True:
        raise ValueError("user facts must never promote low-information input to eligible")
    if _clean(value.get("plan")) == "free":
        if value.get("user_fact_allowed") is True or value.get("facts_used"):
            raise ValueError("free plan must not carry user facts")
    reply_meta = value.get("observation_reply_meta") or {}
    if reply_meta:
        assert_observation_reply_meta_contract(reply_meta, source=f"{source}.observation_reply_meta")


def dump_observation_eligibility_decision(value: ObservationEligibilityDecision | Mapping[str, Any]) -> str:
    meta = value.as_meta() if isinstance(value, ObservationEligibilityDecision) else dict(value)
    assert_observation_eligibility_decision_contract(meta)
    return json.dumps(meta, ensure_ascii=False, sort_keys=True)


__all__ = [
    "OBSERVATION_ELIGIBILITY_ROUTER_VERSION",
    "OBSERVATION_ELIGIBILITY_ROUTER_STEP",
    "OBSERVATION_ELIGIBILITY_STATUS_SAFETY_BLOCKED",
    "ELIGIBLE_EVIDENCE_THRESHOLD",
    "LOW_INFORMATION_EVIDENCE_THRESHOLD",
    "RELATION_CONFIDENCE_THRESHOLD",
    "ELIGIBLE_RELATION_THRESHOLD",
    "ObservationEligibilityDecision",
    "route_observation_eligibility",
    "route_emlis_observation_eligibility",
    "route_emlis_observation_eligibility",
    "assert_observation_eligibility_decision_contract",
    "assert_observation_eligibility_decision_meta",
    "dump_observation_eligibility_decision",
    "dump_observation_eligibility_decision_meta",
]
