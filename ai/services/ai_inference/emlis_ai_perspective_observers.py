# -*- coding: utf-8 -*-
from __future__ import annotations

"""Specialist observers for the new EmlisAI observation pipeline.

Each observer returns structured claims and relations only. No observer writes
final user-facing sentences.
"""

import re
from typing import Iterable, List, Sequence

from emlis_ai_types import EvidenceSpan, ObservationClaim, PerspectiveReport, RelationEdge


def _short(text: str, limit: int = 44) -> str:
    value = re.sub(r"\s+", " ", str(text or "")).strip(" 、,。.!！?？")
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip("、,") + "…"


def _claims_by_type(spans: Sequence[EvidenceSpan], types: Iterable[str]) -> List[EvidenceSpan]:
    wanted = set(types)
    return [span for span in spans if span.detected_type in wanted]


def _claim(prefix: str, idx: int, claim_type: str, span: EvidenceSpan, *, subject: str = "current_user", risk: str = "low") -> ObservationClaim:
    return ObservationClaim(
        claim_id=f"{prefix}.c{idx}",
        claim_type=claim_type,
        subject=subject,
        object=_short(span.raw_text),
        evidence_span_ids=[span.span_id],
        confidence=float(span.confidence or 0.0),
        risk_level=risk,  # type: ignore[arg-type]
    )


def _report(observer_id: str, viewpoint: str, claims: List[ObservationClaim], relations: List[RelationEdge] | None = None, *, uncertainty: List[str] | None = None, do_not_say: List[str] | None = None) -> PerspectiveReport:
    evidence_ids: List[str] = []
    for item in claims:
        for span_id in item.evidence_span_ids:
            if span_id not in evidence_ids:
                evidence_ids.append(span_id)
    for edge in relations or []:
        for span_id in edge.evidence_span_ids:
            if span_id not in evidence_ids:
                evidence_ids.append(span_id)
    confidence = sum(float(item.confidence or 0.0) for item in claims) / max(1, len(claims))
    return PerspectiveReport(
        observer_id=observer_id,
        viewpoint=viewpoint,
        claims=claims,
        relations=list(relations or []),
        evidence_span_ids=evidence_ids,
        confidence=round(confidence, 3),
        uncertainty=list(uncertainty or []),
        do_not_say=list(do_not_say or []),
    )


def _explicit_content_observer(spans: Sequence[EvidenceSpan]) -> PerspectiveReport:
    content_spans = [span for span in spans if span.source_field in {"memo", "memo_action"} and span.detected_type != "safety_risk"]
    claims = [_claim("explicit", idx + 1, "explicit_content", span) for idx, span in enumerate(content_spans[:10])]
    return _report("explicit_content", "ユーザーが明示した内容だけを拾う", claims, do_not_say=["原文にない本音を足さない"])


def _emotion_state_observer(spans: Sequence[EvidenceSpan]) -> PerspectiveReport:
    emotion_spans = _claims_by_type(spans, {"emotion"})
    claims = [_claim("emotion", idx + 1, "emotion_signal", span) for idx, span in enumerate(emotion_spans[:6])]
    return _report("emotion_state", "選択感情と本文中の感情語を分けて扱う", claims, do_not_say=["感情を診断名へ変換しない"])


def _conflict_observer(spans: Sequence[EvidenceSpan]) -> PerspectiveReport:
    claims: List[ObservationClaim] = []
    relations: List[RelationEdge] = []
    memo_spans = [span for span in spans if span.source_field in {"memo", "memo_action"}]
    marker_spans = _claims_by_type(memo_spans, {"relation_marker"})
    wish_spans = _claims_by_type(memo_spans, {"wish", "value"})
    for marker in marker_spans:
        if re.search(r"(嬉し|リラックス|優先|整え|したい|いたい|生活したい|楽しい|安心)", marker.raw_text):
            wish_spans.append(marker)
    constraint_spans = _claims_by_type(memo_spans, {"constraint", "fear", "self_awareness", "limit_signal"})
    for marker in marker_spans:
        if re.search(r"(悪化|不便|怖|こわ|気をつけ|無視|ダメージ)", marker.raw_text):
            constraint_spans.append(marker)

    # Keep enough material for nearby relation edges; final composer will trim.
    for idx, span in enumerate([*wish_spans[:6], *constraint_spans[:8], *marker_spans[:4]]):
        ctype = "relation_material"
        if span in wish_spans:
            ctype = "wish_or_value"
        elif span in constraint_spans:
            ctype = "constraint_or_limit"
        claims.append(_claim("conflict", idx + 1, ctype, span))

    # Pair nearby wish/value material with constraint/self-awareness/limit material.
    edge_idx = 1
    for left in wish_spans[:4]:
        closest = None
        closest_gap = 10**9
        for right in constraint_spans[:6]:
            gap = abs(int(right.start_index or 0) - int(left.start_index or 0))
            if gap < closest_gap:
                closest = right
                closest_gap = gap
        if closest is None:
            continue
        left_claim = next((claim for claim in claims if left.span_id in claim.evidence_span_ids), None)
        right_claim = next((claim for claim in claims if closest.span_id in claim.evidence_span_ids), None)
        if left_claim is None or right_claim is None:
            continue
        relation_type = "coexistence"
        if closest.detected_type in {"constraint", "fear", "self_awareness"}:
            relation_type = "tension"
        if closest.detected_type == "limit_signal":
            relation_type = "limit_tension"
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

    # If the user wrote an explicit marker, connect surrounding claims.
    for marker in marker_spans[:3]:
        before = next((span for span in reversed(memo_spans) if span.start_index >= 0 and span.start_index < marker.start_index and span.detected_type != "relation_marker"), None)
        after = next((span for span in memo_spans if span.start_index > marker.start_index and span.detected_type != "relation_marker"), None)
        if before and after:
            before_claim = next((claim for claim in claims if before.span_id in claim.evidence_span_ids), None)
            after_claim = next((claim for claim in claims if after.span_id in claim.evidence_span_ids), None)
            if before_claim and after_claim:
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

    return _report("conflict_coexistence", "願い・制約・自己認識の並存や葛藤を見る", claims, relations, uncertainty=[] if relations else ["関係を作るには根拠が少ない"])


def _pressure_observer(spans: Sequence[EvidenceSpan]) -> PerspectiveReport:
    pressure_spans = _claims_by_type(spans, {"constraint", "fear"})
    claims = [_claim("pressure", idx + 1, "pressure_source", span) for idx, span in enumerate(pressure_spans[:6])]
    return _report("pressure_constraint", "何が負荷や制約になっているかを見る", claims, do_not_say=["助言で片づけない"])


def _limit_observer(spans: Sequence[EvidenceSpan]) -> PerspectiveReport:
    limit_spans = _claims_by_type(spans, {"limit_signal"})
    claims = [_claim("limit", idx + 1, "limit_signal", span, risk="medium") for idx, span in enumerate(limit_spans[:5])]
    return _report("limit_signal", "逃げたい・休みたい・分からない等の限界サインを見る", claims, do_not_say=["危険度を過剰断定しない"])


def _self_awareness_observer(spans: Sequence[EvidenceSpan]) -> PerspectiveReport:
    aware_spans = _claims_by_type(spans, {"self_awareness"})
    claims = [_claim("selfaware", idx + 1, "self_awareness", span) for idx, span in enumerate(aware_spans[:6])]
    return _report("self_awareness", "本人が既に分かっていることを尊重する", claims, do_not_say=["Emlisが上から説明しない"])


def _value_strength_observer(spans: Sequence[EvidenceSpan]) -> PerspectiveReport:
    value_spans = _claims_by_type(spans, {"value", "wish", "self_awareness"})
    for span in spans:
        if span.detected_type == "relation_marker" and re.search(r"(嬉し|リラックス|優先|整え|家のこと|安心|楽しい)", span.raw_text):
            value_spans.append(span)
    claims: List[ObservationClaim] = []
    for idx, span in enumerate(value_spans[:8]):
        claim_type = "value_signal" if span.detected_type in {"value", "wish", "relation_marker"} else "grounded_strength_signal"
        claims.append(_claim("value", idx + 1, claim_type, span))
    return _report("value_strength", "苦しさの中にある価値や向き合い方を根拠つきで見る", claims, do_not_say=["根拠なしに強いと言わない"])


def _addressee_model_observer(spans: Sequence[EvidenceSpan]) -> PerspectiveReport:
    body_count = sum(len(span.raw_text) for span in spans if span.source_field in {"memo", "memo_action"})
    claims = [
        ObservationClaim(
            claim_id="addressee.c1",
            claim_type="addressee_need",
            subject="emlis_output",
            object="short_conversational" if body_count < 180 else "paced_conversational",
            evidence_span_ids=[span.span_id for span in spans[:3]],
            confidence=0.74,
            risk_level="low",
        )
    ]
    return _report("addressee_model", "観測結果ではなく相手に話す文として届くかを見る", claims, do_not_say=["箇条書きの結果羅列にしない"])


def _safety_boundary_observer(spans: Sequence[EvidenceSpan]) -> PerspectiveReport:
    safety_spans = _claims_by_type(spans, {"safety_risk"})
    claims = [_claim("safety", idx + 1, "safety_boundary", span, risk="high") for idx, span in enumerate(safety_spans)]
    return _report("safety_boundary", "診断・危険表現・安全境界を見る", claims, do_not_say=["通常の観測文で済ませない"])


def run_perspective_observers(evidence_spans: Sequence[EvidenceSpan]) -> List[PerspectiveReport]:
    spans = list(evidence_spans or [])
    return [
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


__all__ = ["run_perspective_observers"]
