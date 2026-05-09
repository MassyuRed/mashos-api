# -*- coding: utf-8 -*-
from __future__ import annotations

"""Compatibility structure builder for the retired single-frame path.

The previous frame service stored ready-to-show observation sentences.  The new
architecture keeps user-facing language inside Conversation Composer only, so
this file now returns evidence-linked structure values without fixed wording.
"""

import re
from typing import Any, Dict, List, Optional, Sequence

from emlis_ai_types import (
    EmlisObservationFrame,
    EvidenceRef,
    InputMeaningBlock,
    ObservationTensionPair,
    WholeInputMeaningArc,
)

_SPACE_RE = re.compile(r"\s+")


def _clean(value: Any) -> str:
    text = str(value or "").replace("\u3000", " ")
    text = _SPACE_RE.sub(" ", text)
    return text.strip(" 、,。.!！?？\t\n\r")


def _blocks_by_role(blocks: Sequence[InputMeaningBlock]) -> Dict[str, List[InputMeaningBlock]]:
    out: Dict[str, List[InputMeaningBlock]] = {}
    for block in blocks or []:
        role = str(getattr(block, "role", "") or "current_expression")
        out.setdefault(role, []).append(block)
    return out


def _summary(block: Optional[InputMeaningBlock]) -> str:
    return _clean(getattr(block, "summary", "") if block is not None else "")


def _first(by_role: Dict[str, List[InputMeaningBlock]], *roles: str) -> Optional[InputMeaningBlock]:
    for role in roles:
        values = by_role.get(role) or []
        if values:
            return values[0]
    return None


def _evidence_from_blocks(blocks: Sequence[InputMeaningBlock], fallback: Optional[EvidenceRef]) -> List[EvidenceRef]:
    refs: List[EvidenceRef] = []
    seen: set[tuple[str, str]] = set()
    for block in blocks or []:
        for ref in list(getattr(block, "evidence", []) or []):
            key = (str(getattr(ref, "kind", "") or ""), str(getattr(ref, "ref_id", "") or ""))
            if key not in seen:
                seen.add(key)
                refs.append(ref)
    if not refs and fallback is not None:
        refs.append(fallback)
    return refs


def _evidence_terms(blocks: Sequence[InputMeaningBlock]) -> List[str]:
    terms: List[str] = []
    for block in blocks or []:
        text = _summary(block)
        if not text:
            continue
        for chunk in re.split(r"[、,\s]+", text):
            chunk = _clean(chunk)
            if 3 <= len(chunk) <= 24 and chunk not in terms:
                terms.append(chunk)
            if len(terms) >= 12:
                break
        if len(terms) >= 12:
            break
    return terms[:12]


def _join_summaries(*blocks: Optional[InputMeaningBlock]) -> str:
    values: List[str] = []
    for block in blocks:
        value = _summary(block)
        if value and value not in values:
            values.append(value[:60])
    return " / ".join(values)


def build_emlis_observation_frame(
    *,
    meaning_blocks: Sequence[InputMeaningBlock],
    whole_input_meaning_arc: Optional[WholeInputMeaningArc] = None,
    evidence: Optional[EvidenceRef] = None,
) -> Optional[EmlisObservationFrame]:
    """Return structural slots only; no user-facing observation text."""

    blocks = list(meaning_blocks or [])
    if not blocks:
        return None

    by_role = _blocks_by_role(blocks)
    roles = set(by_role.keys())
    observation_roles = {
        "relief_or_benefit_in_constraint",
        "reality_gap_or_inconvenience",
        "restriction_pressure",
        "normal_life_wish",
        "worsening_awareness",
        "escape_or_limit",
        "balanced_self_awareness",
    }
    if not (roles & observation_roles):
        return None

    benefit = _first(by_role, "relief_or_benefit_in_constraint", "relief_source")
    inconvenience = _first(by_role, "reality_gap_or_inconvenience", "collapse_anxiety", "fatigue_or_limit", "limit_or_exhaustion")
    restriction = _first(by_role, "restriction_pressure", "self_suppression", "burden_avoidance")
    normal_wish = _first(by_role, "normal_life_wish", "wish_or_hope", "continuation_wish")
    worsening = _first(by_role, "worsening_awareness", "state_awareness", "self_understanding")
    escape = _first(by_role, "escape_or_limit", "fatigue_or_limit", "limit_or_exhaustion")

    required_roles: List[str] = ["primary_state"]
    primary_state = _join_summaries(benefit, inconvenience, normal_wish, worsening) or _join_summaries(*blocks[:2])
    tension_pairs: List[ObservationTensionPair] = []

    if benefit is not None and inconvenience is not None:
        tension_pairs.append(ObservationTensionPair(left=_summary(benefit), right=_summary(inconvenience), relation="both_true"))
        required_roles.append("tension_relation")
    if normal_wish is not None and worsening is not None:
        tension_pairs.append(ObservationTensionPair(left=_summary(normal_wish), right=_summary(worsening), relation="tension"))
        if "tension_relation" not in required_roles:
            required_roles.append("tension_relation")
    if not tension_pairs and whole_input_meaning_arc is not None:
        for left, right in list(getattr(whole_input_meaning_arc, "tension_pairs", []) or [])[:2]:
            if str(left).strip() and str(right).strip():
                tension_pairs.append(ObservationTensionPair(left=str(left).strip(), right=str(right).strip(), relation="tension"))
                if "tension_relation" not in required_roles:
                    required_roles.append("tension_relation")

    pressure_sources: List[str] = []
    if restriction is not None:
        pressure_sources.append(_summary(restriction))
        required_roles.append("pressure_state")

    escape_signal = _summary(escape)
    if escape_signal:
        required_roles.append("escape_signal")

    self_awareness = _summary(worsening)
    if self_awareness:
        required_roles.append("self_awareness")

    strength_signal = _join_summaries(benefit, worsening)
    if strength_signal:
        required_roles.append("strength")

    frame_evidence = _evidence_from_blocks(blocks, evidence)
    return EmlisObservationFrame(
        primary_state=primary_state,
        tension_pairs=tension_pairs,
        pressure_sources=pressure_sources,
        escape_or_limit_signal=escape_signal,
        self_awareness_signal=self_awareness,
        strength_signal=strength_signal,
        companion_close="",
        evidence_terms=_evidence_terms(blocks),
        required_line_roles=required_roles,
        evidence=frame_evidence,
    )


__all__ = ["build_emlis_observation_frame"]
