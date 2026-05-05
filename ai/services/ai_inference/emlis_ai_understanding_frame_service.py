# -*- coding: utf-8 -*-
from __future__ import annotations

"""Understanding-frame construction for EmlisAI.

This layer does not infer hidden causes.  It only connects words that are
present in the current input so the observation kernel can reply like a human
conversation instead of repeating an acknowledgement such as "受け取りました".
"""

import re
from typing import Any, Dict, Iterable, List, Optional, Sequence

from emlis_ai_types import EmotionDisplayItem, EvidenceRef, UnderstandingFrame, UserWordAnchor

_SPACE_RE = re.compile(r"\s+")


def _clean(value: Any) -> str:
    return _SPACE_RE.sub(" ", str(value or "").replace("\u3000", " ")).strip(" 、,。.!！?？\t\n\r")


def _compact(value: Any) -> str:
    return re.sub(r"[\s　、,。.!！?？\t\n\r]", "", str(value or ""))


def _first_anchor(anchors: Sequence[UserWordAnchor], roles: Iterable[str]) -> Optional[UserWordAnchor]:
    role_set = set(roles)
    return next((item for item in anchors if item.role in role_set), None)


def _make_anchor(*, text: str, role: str, source_field: str, evidence: EvidenceRef, key: str) -> Optional[UserWordAnchor]:
    clean = _clean(text)
    if not clean:
        return None
    return UserWordAnchor(
        anchor_key=f"understanding_raw:{source_field}:{key}",
        text=clean,
        source_field=source_field,
        role=role,
        evidence=[EvidenceRef(kind=evidence.kind, ref_id=evidence.ref_id, weight=evidence.weight, note=f"understanding_frame:{source_field}:{role}")],
        confidence=0.78,
    )


def _regex_anchor(
    *,
    raw: str,
    patterns: Sequence[str],
    role: str,
    source_field: str,
    evidence: EvidenceRef,
    key: str,
) -> Optional[UserWordAnchor]:
    for pattern in patterns:
        match = re.search(pattern, raw)
        if match:
            return _make_anchor(text=match.group(0), role=role, source_field=source_field, evidence=evidence, key=key)
    return None


def _ensure_role(
    *,
    anchors: Sequence[UserWordAnchor],
    roles: Sequence[str],
    raw: str,
    patterns: Sequence[str],
    role: str,
    source_field: str,
    evidence: EvidenceRef,
    key: str,
) -> Optional[UserWordAnchor]:
    existing = _first_anchor(anchors, roles)
    if existing is not None:
        return existing
    return _regex_anchor(raw=raw, patterns=patterns, role=role, source_field=source_field, evidence=evidence, key=key)


def _unique_evidence(anchors: Sequence[Optional[UserWordAnchor]]) -> List[EvidenceRef]:
    seen: set[tuple[str, str, str]] = set()
    out: List[EvidenceRef] = []
    for anchor in anchors:
        if anchor is None:
            continue
        for item in anchor.evidence:
            key = (item.kind, item.ref_id, str(item.note or ""))
            if key in seen:
                continue
            seen.add(key)
            out.append(item)
    return out


def _selected_emotion_text(selected_emotions: Sequence[EmotionDisplayItem]) -> str:
    labels = [_clean(getattr(item, "type", "")) for item in selected_emotions if _clean(getattr(item, "type", ""))]
    if not labels:
        return ""
    if len(labels) == 1:
        return labels[0]
    return "、".join(labels[:-1]) + "、そして" + labels[-1]


def build_understanding_frame(
    *,
    anchors: List[UserWordAnchor],
    selected_emotions: List[EmotionDisplayItem],
    current_input: Dict[str, Any],
    evidence: EvidenceRef,
) -> Optional[UnderstandingFrame]:
    """Build a source-bound relationship frame for the immediate reply."""

    raw_memo = str(current_input.get("memo") or "")
    raw_action = str(current_input.get("memo_action") or "")
    raw_all = f"{raw_memo}\n{raw_action}"
    if not raw_all.strip() and not selected_emotions:
        return None

    event = _ensure_role(
        anchors=anchors,
        roles=("event",),
        raw=raw_memo,
        patterns=(r"[^。！？!?\n\r]{1,24}(?:喧嘩|けんか)した",),
        role="event",
        source_field="memo",
        evidence=evidence,
        key="event",
    )
    action = _ensure_role(
        anchors=anchors,
        roles=("action",),
        raw=raw_action,
        patterns=(r"[^。！？!?\n\r]{1,48}",),
        role="action",
        source_field="memo_action",
        evidence=evidence,
        key="action",
    )
    boundary_violation = _ensure_role(
        anchors=anchors,
        roles=("boundary_violation",),
        raw=raw_all,
        patterns=(
            r"パーソナルスペースに触れてしまった",
            r"パーソナルスペースに入ってしまった",
            r"[^。！？!?、,\n\r]{0,16}パーソナルスペース[^。！？!?、,\n\r]{0,18}",
            r"距離感[^。！？!?、,\n\r]{0,18}",
        ),
        role="boundary_violation",
        source_field="memo_action" if "パーソナルスペース" in raw_action else "memo",
        evidence=evidence,
        key="boundary",
    )
    self_awareness = _ensure_role(
        anchors=anchors,
        roles=("self_awareness",),
        raw=raw_memo,
        patterns=(
            r"(?:きっと)?怒ると知っていながら",
            r"[^。！？!?、,\n\r]{0,14}知っていながら",
            r"[^。！？!?、,\n\r]{0,14}分かっていながら",
            r"[^。！？!?、,\n\r]{0,14}わかっていながら",
        ),
        role="self_awareness",
        source_field="memo",
        evidence=evidence,
        key="self_awareness",
    )
    justification = _ensure_role(
        anchors=anchors,
        roles=("justification",),
        raw=raw_memo,
        patterns=(
            r"女の子との絡みがあったからという理由を掲げて",
            r"女の子との絡みがあったから",
            r"[^。！？!?、,\n\r]{1,24}という理由を掲げて",
            r"[^。！？!?、,\n\r]{1,24}理由にして",
        ),
        role="justification",
        source_field="memo",
        evidence=evidence,
        key="justification",
    )
    self_fault_awareness = _ensure_role(
        anchors=anchors,
        roles=("self_fault_awareness",),
        raw=raw_memo,
        patterns=(r"自分の非", r"自分が悪[^。！？!?、,\n\r]{0,12}", r"自分のせい"),
        role="self_fault_awareness",
        source_field="memo",
        evidence=evidence,
        key="self_fault",
    )
    self_avoidance = _ensure_role(
        anchors=anchors,
        roles=("self_avoidance",),
        raw=raw_memo,
        patterns=(r"自分の非を見たくない", r"見たくない", r"向き合いたくない", r"認めたくない"),
        role="self_avoidance",
        source_field="memo",
        evidence=evidence,
        key="self_avoidance",
    )
    fear_of_rejection = _ensure_role(
        anchors=anchors,
        roles=("fear_of_rejection",),
        raw=raw_memo,
        patterns=(r"嫌われてしまいそう", r"嫌われそう", r"否定され[^。！？!?、,\n\r]{0,12}", r"見捨てられ[^。！？!?、,\n\r]{0,12}"),
        role="fear_of_rejection",
        source_field="memo",
        evidence=evidence,
        key="fear_rejection",
    )
    self_dislike = _ensure_role(
        anchors=anchors,
        roles=("self_dislike",),
        raw=raw_memo,
        patterns=(r"自分が嫌[^。！？!?、,\n\r]{0,18}", r"そんな自分[^。！？!?、,\n\r]{0,18}"),
        role="self_dislike",
        source_field="memo",
        evidence=evidence,
        key="self_dislike",
    )
    guilt_or_remorse = _ensure_role(
        anchors=anchors,
        roles=("guilt_or_remorse",),
        raw=raw_all,
        patterns=(r"[^。！？!?、,\n\r]{0,18}してしまった", r"申し訳[^。！？!?、,\n\r]{0,18}", r"後悔[^。！？!?、,\n\r]{0,18}"),
        role="guilt_or_remorse",
        source_field="memo_action" if raw_action else "memo",
        evidence=evidence,
        key="guilt",
    )
    explicit_emotion = _ensure_role(
        anchors=anchors,
        roles=("explicit_emotion",),
        raw=raw_memo,
        patterns=(
            r"悲しくて不安な気持ち",
            r"悲しくて不安",
            r"悲し[^。！？!?、,\n\r]{0,10}不安[^。！？!?、,\n\r]{0,10}",
            r"不安[^。！？!?、,\n\r]{0,10}悲し[^。！？!?、,\n\r]{0,10}",
        ),
        role="explicit_emotion",
        source_field="memo",
        evidence=evidence,
        key="explicit_emotion",
    )
    need_or_wish = _first_anchor(anchors, ("wish", "need"))
    unresolved = _first_anchor(anchors, ("unresolved", "mismatch"))
    relationship_or_other = _first_anchor(anchors, ("relationship",))

    patterns: List[str] = []
    if (action or boundary_violation) and self_awareness:
        patterns.append("action_and_awareness")
    if justification and (self_fault_awareness or self_avoidance):
        patterns.append("justification_vs_fault")
    if fear_of_rejection and (self_fault_awareness or self_avoidance or self_dislike):
        patterns.append("rejection_fear_from_self_view")
    if explicit_emotion and patterns:
        patterns.append("emotion_from_conflict")
    if action and raw_memo.strip():
        patterns.append("action_thought_split")
    if not patterns and selected_emotions:
        patterns.append("simple_emotion")

    frame_anchors = [
        event,
        action,
        relationship_or_other,
        boundary_violation,
        self_awareness,
        self_fault_awareness,
        self_avoidance,
        justification,
        fear_of_rejection,
        self_dislike,
        guilt_or_remorse,
        explicit_emotion,
        need_or_wish,
        unresolved,
    ]
    present_count = sum(1 for item in frame_anchors if item is not None)
    if present_count <= 0 and not selected_emotions:
        return None

    confidence = min(1.0, 0.24 + present_count * 0.07 + len(patterns) * 0.08)
    if "emotion_from_conflict" in patterns:
        confidence = max(confidence, 0.78)
    elif "simple_emotion" in patterns:
        confidence = max(confidence, 0.38)

    return UnderstandingFrame(
        event=event,
        action=action,
        relationship_or_other=relationship_or_other,
        boundary_violation=boundary_violation,
        self_awareness=self_awareness,
        self_fault_awareness=self_fault_awareness,
        self_avoidance=self_avoidance,
        justification=justification,
        fear_of_rejection=fear_of_rejection,
        self_dislike=self_dislike,
        guilt_or_remorse=guilt_or_remorse,
        explicit_emotion=explicit_emotion,
        need_or_wish=need_or_wish,
        unresolved=unresolved,
        relation_patterns=patterns,
        confidence=confidence,
        evidence=_unique_evidence(frame_anchors) or [evidence],
    )


__all__ = ["build_understanding_frame"]
