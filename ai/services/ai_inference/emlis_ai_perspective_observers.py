# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase 4 specialist observers for the EmlisAI observation pipeline.

The observer layer is intentionally structural. It reads EvidenceSpan rows and
returns PerspectiveReport objects only. It must not compose user-facing Emlis
observation text, fixed conversation lines, or fallback sentences.
"""

from dataclasses import dataclass
import re
from typing import Iterable, List, Sequence, Tuple

from emlis_ai_types import EvidenceSpan, ObservationClaim, PerspectiveReport, RelationEdge


@dataclass(frozen=True)
class SpecialistObserverSpec:
    """Internal contract for a specialist observer.

    ``prompt_contract`` is a role/contract label, not user-facing copy. In the
    live AI-connected phase it is the boundary that keeps each call's role,
    schema and responsibility separate.
    """

    observer_id: str
    viewpoint: str
    prompt_contract: str
    input_span_types: Tuple[str, ...]
    output_claim_types: Tuple[str, ...]
    relation_types: Tuple[str, ...] = ()
    do_not_say: Tuple[str, ...] = ()


SPECIALIST_OBSERVER_SPECS: Tuple[SpecialistObserverSpec, ...] = (
    SpecialistObserverSpec(
        observer_id="explicit_content",
        viewpoint="explicit_content_only",
        prompt_contract="observe_only_user_stated_content",
        input_span_types=("event", "wish", "constraint", "fear", "self_awareness", "limit_signal", "value", "relation_marker"),
        output_claim_types=(
            "explicit_event",
            "explicit_wish",
            "explicit_constraint",
            "explicit_fear",
            "explicit_self_awareness",
            "explicit_limit_signal",
            "explicit_value",
            "explicit_relation_marker",
        ),
        do_not_say=("unsupported_hidden_intent", "unsupported_strength_claim"),
    ),
    SpecialistObserverSpec(
        observer_id="emotion_state",
        viewpoint="selected_and_textual_emotion_only",
        prompt_contract="observe_emotion_labels_without_diagnosis",
        input_span_types=("emotion",),
        output_claim_types=("selected_emotion_signal", "textual_emotion_signal"),
        do_not_say=("diagnosis", "personality_label", "emotion_overstatement"),
    ),
    SpecialistObserverSpec(
        observer_id="conflict_coexistence",
        viewpoint="relation_between_evidence_spans",
        prompt_contract="observe_tension_coexistence_transition_edges",
        input_span_types=("wish", "value", "constraint", "fear", "self_awareness", "limit_signal", "relation_marker"),
        output_claim_types=("wish_or_value", "constraint_or_limit", "relation_marker"),
        relation_types=("explicit_transition", "coexistence", "tension", "limit_tension"),
        do_not_say=("word_list_report", "relation_without_evidence"),
    ),
    SpecialistObserverSpec(
        observer_id="pressure_constraint",
        viewpoint="pressure_and_constraint_only",
        prompt_contract="observe_pressure_sources_without_advice",
        input_span_types=("constraint", "fear"),
        output_claim_types=("pressure_source",),
        do_not_say=("advice", "forced_reframe"),
    ),
    SpecialistObserverSpec(
        observer_id="limit_signal",
        viewpoint="limit_signals_only",
        prompt_contract="observe_limit_signals_without_medical_judgment",
        input_span_types=("limit_signal",),
        output_claim_types=("limit_signal",),
        do_not_say=("medical_judgment", "risk_overstatement"),
    ),
    SpecialistObserverSpec(
        observer_id="self_awareness",
        viewpoint="user_self_awareness_only",
        prompt_contract="observe_existing_user_awareness_without_explaining_over_it",
        input_span_types=("self_awareness",),
        output_claim_types=("self_awareness",),
        do_not_say=("speak_above_user", "claim_emlis_knows_better"),
    ),
    SpecialistObserverSpec(
        observer_id="value_strength",
        viewpoint="grounded_value_or_strength_signal_only",
        prompt_contract="observe_value_signals_without_positive_invention",
        input_span_types=("value", "wish", "self_awareness"),
        output_claim_types=("value_signal", "grounded_strength_signal"),
        do_not_say=("unsupported_positive_reframe", "generic_strength_phrase"),
    ),
    SpecialistObserverSpec(
        observer_id="addressee_model",
        viewpoint="conversation_delivery_constraints_only",
        prompt_contract="observe_output_distance_length_and_report_like_risk",
        input_span_types=("event", "wish", "constraint", "fear", "self_awareness", "limit_signal", "value", "emotion"),
        output_claim_types=("addressee_need",),
        do_not_say=("bullet_report", "observation_result_list"),
    ),
    SpecialistObserverSpec(
        observer_id="safety_boundary",
        viewpoint="safety_boundary_only",
        prompt_contract="observe_safety_boundary_without_normal_observation_text",
        input_span_types=("safety_risk",),
        output_claim_types=("safety_boundary",),
        do_not_say=("通常の観測文で済ませない", "normal_observation_for_safety_risk"),
    ),
)

SPECIALIST_OBSERVER_IDS: Tuple[str, ...] = tuple(spec.observer_id for spec in SPECIALIST_OBSERVER_SPECS)

_EXPLICIT_CLAIM_TYPE_BY_SPAN_TYPE = {
    "event": "explicit_event",
    "wish": "explicit_wish",
    "constraint": "explicit_constraint",
    "fear": "explicit_fear",
    "self_awareness": "explicit_self_awareness",
    "limit_signal": "explicit_limit_signal",
    "value": "explicit_value",
    "relation_marker": "explicit_relation_marker",
}

_CONFLICT_WISH_VALUE_RE = re.compile(r"(嬉し|うれし|リラックス|優先|整え|したい|いたい|生活したい|楽しい|安心|幸せ|繋が|つなが|過ごしたい)")
_CONFLICT_CONSTRAINT_RE = re.compile(r"(悪化|不便|怖|こわ|気をつけ|気を付け|無視|ダメージ|できない|出来ない|疲れ|しんど|責め|ミス|分からな|わからな)")
_TEXT_FIELDS = {"memo", "memo_action"}


def expected_phase4_observer_ids() -> Tuple[str, ...]:
    """Return the ordered Phase 4 specialist observer contract."""

    return SPECIALIST_OBSERVER_IDS


def _spec(observer_id: str) -> SpecialistObserverSpec:
    for item in SPECIALIST_OBSERVER_SPECS:
        if item.observer_id == observer_id:
            return item
    raise KeyError(observer_id)


def _short(text: str, limit: int = 48) -> str:
    value = re.sub(r"\s+", " ", str(text or "")).strip(" 、,。.!！?？")
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip("、,") + "…"


def _memo_spans(spans: Sequence[EvidenceSpan]) -> List[EvidenceSpan]:
    return [span for span in spans if span.source_field in _TEXT_FIELDS]


def _sort_spans(spans: Iterable[EvidenceSpan]) -> List[EvidenceSpan]:
    return sorted(
        list(spans or []),
        key=lambda span: (
            999999 if int(getattr(span, "start_index", -1) or -1) < 0 else int(getattr(span, "start_index", 0) or 0),
            str(getattr(span, "source_field", "") or ""),
            str(getattr(span, "raw_text", "") or ""),
        ),
    )


def _dedupe_spans(spans: Iterable[EvidenceSpan]) -> List[EvidenceSpan]:
    out: List[EvidenceSpan] = []
    seen = set()
    for span in spans:
        key = (span.span_id, span.source_field, span.raw_text, span.start_index, span.end_index)
        if key in seen:
            continue
        seen.add(key)
        out.append(span)
    return out


def _spans_by_type(spans: Sequence[EvidenceSpan], types: Iterable[str], *, text_fields_only: bool = False) -> List[EvidenceSpan]:
    wanted = set(types)
    selected = [span for span in spans if span.detected_type in wanted]
    if text_fields_only:
        selected = [span for span in selected if span.source_field in _TEXT_FIELDS]
    return _sort_spans(_dedupe_spans(selected))


def _span_ids(spans: Iterable[EvidenceSpan], *, limit: int | None = None) -> List[str]:
    ids: List[str] = []
    for span in spans:
        if span.span_id and span.span_id not in ids:
            ids.append(span.span_id)
            if limit is not None and len(ids) >= limit:
                break
    return ids


def _claim(
    prefix: str,
    idx: int,
    claim_type: str,
    span: EvidenceSpan,
    *,
    subject: str = "current_user",
    risk: str = "low",
    confidence: float | None = None,
) -> ObservationClaim:
    return ObservationClaim(
        claim_id=f"{prefix}.c{idx}",
        claim_type=claim_type,
        subject=subject,
        object=_short(span.raw_text),
        evidence_span_ids=[span.span_id],
        confidence=float(span.confidence if confidence is None else confidence),
        risk_level=risk,  # type: ignore[arg-type]
    )


def _report(
    spec: SpecialistObserverSpec,
    claims: Sequence[ObservationClaim],
    relations: Sequence[RelationEdge] | None = None,
    *,
    uncertainty: Sequence[str] | None = None,
) -> PerspectiveReport:
    relation_list = list(relations or [])
    claim_list = list(claims or [])
    evidence_ids: List[str] = []
    for item in claim_list:
        for span_id in item.evidence_span_ids:
            if span_id not in evidence_ids:
                evidence_ids.append(span_id)
    for edge in relation_list:
        for span_id in edge.evidence_span_ids:
            if span_id not in evidence_ids:
                evidence_ids.append(span_id)
    confidence = 0.0
    if claim_list:
        confidence = sum(float(item.confidence or 0.0) for item in claim_list) / max(1, len(claim_list))
    elif relation_list:
        confidence = sum(float(item.confidence or 0.0) for item in relation_list) / max(1, len(relation_list))
    return PerspectiveReport(
        observer_id=spec.observer_id,
        viewpoint=spec.viewpoint,
        claims=claim_list,
        relations=relation_list,
        evidence_span_ids=evidence_ids,
        confidence=round(confidence, 3),
        uncertainty=list(uncertainty or []),
        do_not_say=list(spec.do_not_say),
    )


def _explicit_content_observer(spans: Sequence[EvidenceSpan]) -> PerspectiveReport:
    spec = _spec("explicit_content")
    content_spans = _spans_by_type(spans, spec.input_span_types, text_fields_only=True)
    claims = [
        _claim("explicit", idx + 1, _EXPLICIT_CLAIM_TYPE_BY_SPAN_TYPE.get(span.detected_type, "explicit_event"), span)
        for idx, span in enumerate(content_spans[:12])
    ]
    uncertainty = [] if claims else ["no_explicit_text_span"]
    return _report(spec, claims, uncertainty=uncertainty)


def _emotion_state_observer(spans: Sequence[EvidenceSpan]) -> PerspectiveReport:
    spec = _spec("emotion_state")
    emotion_spans = _spans_by_type(spans, spec.input_span_types)
    claims: List[ObservationClaim] = []
    for idx, span in enumerate(emotion_spans[:8]):
        claim_type = "selected_emotion_signal" if span.source_field in {"emotion_details", "emotions"} else "textual_emotion_signal"
        claims.append(_claim("emotion", idx + 1, claim_type, span))
    uncertainty = [] if claims else ["no_selected_or_textual_emotion"]
    return _report(spec, claims, uncertainty=uncertainty)


def _conflict_observer(spans: Sequence[EvidenceSpan]) -> PerspectiveReport:
    spec = _spec("conflict_coexistence")
    text_spans = _memo_spans(spans)
    marker_spans = _spans_by_type(text_spans, {"relation_marker"})
    wish_value_spans = _spans_by_type(text_spans, {"wish", "value"})
    constraint_limit_spans = _spans_by_type(text_spans, {"constraint", "fear", "self_awareness", "limit_signal"})

    # Some source slices may carry relation words and value/constraint words in
    # the same source span. Keep them as relation material without rewriting the
    # EvidenceSpan itself.
    for span in text_spans:
        if span.detected_type == "relation_marker" and _CONFLICT_WISH_VALUE_RE.search(span.raw_text):
            wish_value_spans.append(span)
        if span.detected_type == "relation_marker" and _CONFLICT_CONSTRAINT_RE.search(span.raw_text):
            constraint_limit_spans.append(span)
    wish_value_spans = _dedupe_spans(_sort_spans(wish_value_spans))
    constraint_limit_spans = _dedupe_spans(_sort_spans(constraint_limit_spans))

    materials = _dedupe_spans(_sort_spans([*wish_value_spans, *constraint_limit_spans, *marker_spans]))
    claims: List[ObservationClaim] = []
    span_to_claim: dict[str, ObservationClaim] = {}
    wish_ids = {span.span_id for span in wish_value_spans}
    constraint_ids = {span.span_id for span in constraint_limit_spans}
    for span in materials[:14]:
        if span.span_id in wish_ids:
            claim_type = "wish_or_value"
        elif span.span_id in constraint_ids:
            claim_type = "constraint_or_limit"
        else:
            claim_type = "relation_marker"
        claim = _claim("conflict", len(claims) + 1, claim_type, span)
        claims.append(claim)
        span_to_claim[span.span_id] = claim

    relations: List[RelationEdge] = []
    edge_idx = 1

    # Explicit transition markers get priority: connect the nearest previous and
    # following evidence spans around the marker.
    for marker in marker_spans[:4]:
        before = next(
            (span for span in reversed(text_spans) if span.start_index >= 0 and span.start_index < marker.start_index and span.detected_type != "relation_marker"),
            None,
        )
        after = next(
            (span for span in text_spans if span.start_index > marker.start_index and span.detected_type != "relation_marker"),
            None,
        )
        if not before or not after:
            continue
        before_claim = span_to_claim.get(before.span_id)
        after_claim = span_to_claim.get(after.span_id)
        if before_claim is None or after_claim is None:
            continue
        relations.append(
            RelationEdge(
                edge_id=f"conflict.e{edge_idx}",
                from_claim_id=before_claim.claim_id,
                to_claim_id=after_claim.claim_id,
                relation_type="explicit_transition",
                evidence_span_ids=list(dict.fromkeys([before.span_id, marker.span_id, after.span_id])),
                confidence=0.84,
            )
        )
        edge_idx += 1

    # Connect nearby wish/value material to nearby constraint/limit/self-awareness
    # material so later layers can see coexistence/tension without text templates.
    for left in wish_value_spans[:5]:
        left_claim = span_to_claim.get(left.span_id)
        if left_claim is None:
            continue
        closest = None
        closest_gap = 10**9
        for right in constraint_limit_spans[:8]:
            right_claim = span_to_claim.get(right.span_id)
            if right_claim is None:
                continue
            gap = abs(int(right.start_index or 0) - int(left.start_index or 0))
            if gap < closest_gap:
                closest = right
                closest_gap = gap
        if closest is None:
            continue
        right_claim = span_to_claim.get(closest.span_id)
        if right_claim is None or right_claim.claim_id == left_claim.claim_id:
            continue
        relation_type = "coexistence"
        if closest.detected_type in {"constraint", "fear", "self_awareness"}:
            relation_type = "tension"
        if closest.detected_type == "limit_signal":
            relation_type = "limit_tension"
        edge_key = (left_claim.claim_id, right_claim.claim_id, relation_type)
        if any((edge.from_claim_id, edge.to_claim_id, edge.relation_type) == edge_key for edge in relations):
            continue
        relations.append(
            RelationEdge(
                edge_id=f"conflict.e{edge_idx}",
                from_claim_id=left_claim.claim_id,
                to_claim_id=right_claim.claim_id,
                relation_type=relation_type,
                evidence_span_ids=list(dict.fromkeys([left.span_id, closest.span_id])),
                confidence=0.78,
            )
        )
        edge_idx += 1

    uncertainty = [] if relations else ["relation_not_confident"]
    return _report(spec, claims, relations, uncertainty=uncertainty)


def _pressure_observer(spans: Sequence[EvidenceSpan]) -> PerspectiveReport:
    spec = _spec("pressure_constraint")
    pressure_spans = _spans_by_type(spans, spec.input_span_types, text_fields_only=True)
    claims = [_claim("pressure", idx + 1, "pressure_source", span) for idx, span in enumerate(pressure_spans[:7])]
    uncertainty = [] if claims else ["no_pressure_evidence"]
    return _report(spec, claims, uncertainty=uncertainty)


def _limit_observer(spans: Sequence[EvidenceSpan]) -> PerspectiveReport:
    spec = _spec("limit_signal")
    limit_spans = _spans_by_type(spans, spec.input_span_types, text_fields_only=True)
    claims = [_claim("limit", idx + 1, "limit_signal", span, risk="medium") for idx, span in enumerate(limit_spans[:6])]
    uncertainty = [] if claims else ["no_limit_signal_evidence"]
    return _report(spec, claims, uncertainty=uncertainty)


def _self_awareness_observer(spans: Sequence[EvidenceSpan]) -> PerspectiveReport:
    spec = _spec("self_awareness")
    aware_spans = _spans_by_type(spans, spec.input_span_types, text_fields_only=True)
    claims = [_claim("selfaware", idx + 1, "self_awareness", span) for idx, span in enumerate(aware_spans[:7])]
    uncertainty = [] if claims else ["no_self_awareness_evidence"]
    return _report(spec, claims, uncertainty=uncertainty)


def _value_strength_observer(spans: Sequence[EvidenceSpan]) -> PerspectiveReport:
    spec = _spec("value_strength")
    value_spans = _spans_by_type(spans, {"value", "wish"}, text_fields_only=True)
    self_awareness_spans = _spans_by_type(spans, {"self_awareness"}, text_fields_only=True)
    claims: List[ObservationClaim] = []
    for span in value_spans[:8]:
        claims.append(_claim("value", len(claims) + 1, "value_signal", span))
    # Self-awareness can support strength only as a grounded signal. It is not a
    # license to add a generic positive reframe.
    for span in self_awareness_spans[:3]:
        claims.append(_claim("value", len(claims) + 1, "grounded_strength_signal", span, confidence=min(0.72, float(span.confidence or 0.0))))
    uncertainty = [] if claims else ["no_value_or_strength_evidence"]
    return _report(spec, claims, uncertainty=uncertainty)


def _addressee_model_observer(spans: Sequence[EvidenceSpan]) -> PerspectiveReport:
    spec = _spec("addressee_model")
    text_spans = _memo_spans(spans)
    body_count = sum(len(span.raw_text) for span in text_spans)
    relation_count = len([span for span in text_spans if span.detected_type == "relation_marker"])
    object_value = "paced_conversational" if body_count >= 180 or relation_count >= 2 else "short_conversational"
    confidence = 0.76 if text_spans else 0.42
    claim = ObservationClaim(
        claim_id="addressee.c1",
        claim_type="addressee_need",
        subject="emlis_output",
        object=object_value,
        evidence_span_ids=_span_ids(text_spans or spans, limit=5),
        confidence=confidence,
        risk_level="low",
    )
    uncertainty = [] if text_spans else ["no_text_for_addressee_model"]
    return _report(spec, [claim], uncertainty=uncertainty)


def _safety_boundary_observer(spans: Sequence[EvidenceSpan]) -> PerspectiveReport:
    spec = _spec("safety_boundary")
    safety_spans = _spans_by_type(spans, spec.input_span_types, text_fields_only=True)
    claims = [_claim("safety", idx + 1, "safety_boundary", span, risk="high") for idx, span in enumerate(safety_spans[:6])]
    uncertainty = [] if claims else ["no_safety_boundary_evidence"]
    return _report(spec, claims, uncertainty=uncertainty)


def run_perspective_observers(evidence_spans: Sequence[EvidenceSpan]) -> List[PerspectiveReport]:
    """Run the Phase 4 observer set.

    The function returns one PerspectiveReport per specialist observer in a
    stable order. No report contains or creates final ``comment_text``.
    """

    spans = list(evidence_spans or [])
    reports = [
        _explicit_content_observer(spans),
        _emotion_state_observer(spans),
        _conflict_observer(spans),
        _pressure_observer(spans),
        _limit_observer(spans),
        _self_awareness_observer(spans),
        _value_strength_observer(spans),
        _addressee_model_observer(spans),
        _safety_boundary_observer(spans),
    ]
    if tuple(report.observer_id for report in reports) != SPECIALIST_OBSERVER_IDS:
        raise RuntimeError("emlis_specialist_observer_contract_mismatch")
    return reports


def validate_perspective_reports(reports: Sequence[PerspectiveReport], evidence_spans: Sequence[EvidenceSpan]) -> List[str]:
    """Validate Phase 4 observer structure without approving display text."""

    issues: List[str] = []
    report_list = list(reports or [])
    evidence_ids = {span.span_id for span in evidence_spans or []}
    if tuple(report.observer_id for report in report_list) != SPECIALIST_OBSERVER_IDS:
        issues.append("observer_order_or_count_mismatch")
    spec_by_id = {spec.observer_id: spec for spec in SPECIALIST_OBSERVER_SPECS}
    for report in report_list:
        spec = spec_by_id.get(report.observer_id)
        if spec is None:
            issues.append(f"unknown_observer:{report.observer_id}")
            continue
        allowed_claims = set(spec.output_claim_types)
        allowed_relations = set(spec.relation_types)
        claim_ids = {claim.claim_id for claim in report.claims}
        for claim in report.claims:
            if claim.claim_type not in allowed_claims:
                issues.append(f"{report.observer_id}:unexpected_claim_type:{claim.claim_type}")
            if report.observer_id != "addressee_model" and not claim.evidence_span_ids:
                issues.append(f"{report.observer_id}:claim_without_evidence:{claim.claim_id}")
            for span_id in claim.evidence_span_ids:
                if evidence_ids and span_id not in evidence_ids:
                    issues.append(f"{report.observer_id}:unknown_evidence:{span_id}")
        for edge in report.relations:
            if edge.relation_type not in allowed_relations:
                issues.append(f"{report.observer_id}:unexpected_relation_type:{edge.relation_type}")
            if edge.from_claim_id not in claim_ids or edge.to_claim_id not in claim_ids:
                issues.append(f"{report.observer_id}:relation_points_outside_report:{edge.edge_id}")
            if not edge.evidence_span_ids:
                issues.append(f"{report.observer_id}:relation_without_evidence:{edge.edge_id}")
            for span_id in edge.evidence_span_ids:
                if evidence_ids and span_id not in evidence_ids:
                    issues.append(f"{report.observer_id}:unknown_relation_evidence:{span_id}")
    return issues


def phase4_observer_contract_ready(reports: Sequence[PerspectiveReport], evidence_spans: Sequence[EvidenceSpan] | None = None) -> bool:
    """Return True when Phase 4 produced all required structured reports.

    This is not a Display Gate approval. It only confirms that the observer
    layer exists, each observer stayed in its schema, and no text-generation
    responsibility moved into Phase 4.
    """

    return not validate_perspective_reports(list(reports or []), list(evidence_spans or []))


__all__ = [
    "SPECIALIST_OBSERVER_IDS",
    "SPECIALIST_OBSERVER_SPECS",
    "SpecialistObserverSpec",
    "expected_phase4_observer_ids",
    "phase4_observer_contract_ready",
    "run_perspective_observers",
    "validate_perspective_reports",
]
