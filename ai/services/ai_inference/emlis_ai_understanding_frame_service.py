# -*- coding: utf-8 -*-
from __future__ import annotations

"""Generic understanding-frame builder for EmlisAI.

The frame groups current-input anchors into broad relation patterns.  It must
not synthesize anchors from sample-specific phrases; it only reuses extracted
anchors and assigns them to reusable slots.
"""

from typing import Any, Iterable, List, Optional, Sequence

from emlis_ai_types import EmotionDisplayItem, EvidenceRef, UnderstandingFrame, UserWordAnchor


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _first_anchor(anchors: Sequence[UserWordAnchor], roles: Iterable[str]) -> Optional[UserWordAnchor]:
    role_set = set(roles)
    return next((anchor for anchor in anchors if getattr(anchor, "role", "") in role_set), None)


def _unique_evidence(anchors: Sequence[Optional[UserWordAnchor]], fallback: EvidenceRef) -> List[EvidenceRef]:
    refs: List[EvidenceRef] = []
    seen: set[tuple[str, str]] = set()
    for anchor in anchors:
        for ref in list(getattr(anchor, "evidence", []) or []):
            key = (str(getattr(ref, "kind", "") or ""), str(getattr(ref, "ref_id", "") or ""))
            if key in seen:
                continue
            seen.add(key)
            refs.append(ref)
    if not refs:
        refs.append(fallback)
    return refs


def _selected_emotion_text(selected_emotions: Sequence[EmotionDisplayItem]) -> str:
    labels = [str(getattr(item, "type", "") or "").strip() for item in selected_emotions or [] if str(getattr(item, "type", "") or "").strip()]
    return "、".join(labels)


def build_understanding_frame(
    *,
    anchors: List[UserWordAnchor],
    selected_emotions: List[EmotionDisplayItem],
    current_input: dict[str, Any],
    evidence: EvidenceRef,
) -> UnderstandingFrame:
    anchors = list(anchors or [])
    action = _first_anchor(anchors, {"action"})
    event = _first_anchor(anchors, {"event", "current_expression"})
    relationship = _first_anchor(anchors, {"relationship_context", "relationship", "mismatch_or_boundary"})
    boundary = _first_anchor(anchors, {"mismatch_or_boundary", "self_protection"})
    awareness = _first_anchor(anchors, {"self_awareness", "self_view"})
    self_fault = _first_anchor(anchors, {"self_view"})
    avoidance = _first_anchor(anchors, {"self_suppression", "burden_avoidance"})
    justification = _first_anchor(anchors, {"burden_avoidance"})
    rejection = _first_anchor(anchors, {"fear_or_disappointment"})
    dislike = _first_anchor(anchors, {"self_view"})
    explicit = _first_anchor(anchors, {"sadness_or_pain", "anger_or_frustration", "fear_or_disappointment"})
    need = _first_anchor(anchors, {"wish", "support_need", "effort_direction"})
    unresolved = _first_anchor(anchors, {"dual_feeling", "current_expression"})
    work_frustration = _first_anchor(anchors, {"anger_or_frustration"})
    missing_guidance = _first_anchor(anchors, {"support_need"})
    effort_confusion = _first_anchor(anchors, {"effort_direction"})
    relief_source = _first_anchor(anchors, {"relief_source"})
    relation_patterns: List[str] = []
    roles = {str(getattr(anchor, "role", "") or "") for anchor in anchors}
    if {"self_suppression", "support_need"} & roles:
        relation_patterns.append("suppression_and_support_need")
    if "wish" in roles and "fear_or_disappointment" in roles:
        relation_patterns.append("wish_and_fear")
    if "self_protection" in roles and "self_suppression" in roles:
        relation_patterns.append("self_protection_after_suppression")
    if "effort_direction" in roles and "sadness_or_pain" in roles:
        relation_patterns.append("effort_with_pain")
    if _selected_emotion_text(selected_emotions):
        relation_patterns.append("selected_emotions_present")
    selected_anchors = [action, event, relationship, boundary, awareness, self_fault, avoidance, justification, rejection, dislike, explicit, need, unresolved, work_frustration, missing_guidance, effort_confusion, relief_source]
    return UnderstandingFrame(
        event=event,
        action=action,
        relationship_or_other=relationship,
        boundary_violation=boundary,
        self_awareness=awareness,
        self_fault_awareness=self_fault,
        self_avoidance=avoidance,
        justification=justification,
        fear_of_rejection=rejection,
        self_dislike=dislike,
        guilt_or_remorse=_first_anchor(anchors, {"self_view", "action"}),
        explicit_emotion=explicit,
        need_or_wish=need,
        unresolved=unresolved,
        work_frustration=work_frustration,
        mentor_attachment=relationship,
        missing_guidance=missing_guidance,
        effort_confusion=effort_confusion,
        anger_surface=_first_anchor(anchors, {"anger_or_frustration"}),
        sadness_surface=_first_anchor(anchors, {"sadness_or_pain"}),
        relief_source=relief_source,
        chat_relief=relief_source,
        fatigue_accumulation=_first_anchor(anchors, {"limit_or_exhaustion", "sadness_or_pain"}),
        relation_patterns=relation_patterns,
        confidence=0.72 if anchors else 0.0,
        evidence=_unique_evidence(selected_anchors, evidence),
    )


__all__ = ["build_understanding_frame"]
