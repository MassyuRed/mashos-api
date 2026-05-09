# -*- coding: utf-8 -*-
from __future__ import annotations

"""Build a relationship/state frame for EmlisAI observation text.

The frame is intentionally generic.  It does not store sample-specific replies;
it converts current-input meaning blocks into reusable observation slots such
as primary state, tension, pressure, limit signal, self-awareness, strength, and
companion close.
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


def _as_topic(value: Any) -> str:
    text = _clean(value)
    if not text:
        return ""
    if text.endswith(("こと", "気持ち", "願い", "状態", "感覚", "現実", "不便さ", "圧迫感", "強さ")):
        return text
    return f"{text}こと"


def _evidence_from_blocks(blocks: Sequence[InputMeaningBlock], fallback: Optional[EvidenceRef]) -> List[EvidenceRef]:
    refs: List[EvidenceRef] = []
    seen: set[tuple[str, str]] = set()
    for block in blocks or []:
        for ref in list(getattr(block, "evidence", []) or []):
            key = (str(getattr(ref, "kind", "") or ""), str(getattr(ref, "ref_id", "") or ""))
            if key in seen:
                continue
            seen.add(key)
            refs.append(ref)
    if not refs and fallback is not None:
        refs.append(fallback)
    return refs


def _evidence_terms(blocks: Sequence[InputMeaningBlock]) -> List[str]:
    terms: List[str] = []
    for block in blocks or []:
        role = str(getattr(block, "role", "") or "")
        text = _clean(getattr(block, "summary", ""))
        if not text:
            continue
        if role in {
            "relief_or_benefit_in_constraint",
            "reality_gap_or_inconvenience",
            "restriction_pressure",
            "normal_life_wish",
            "worsening_awareness",
            "escape_or_limit",
            "balanced_self_awareness",
        }:
            terms.append(text[:48])
        for chunk in re.split(r"[、,\s]+", text):
            chunk = _clean(chunk)
            if 3 <= len(chunk) <= 18 and chunk not in terms:
                terms.append(chunk)
            if len(terms) >= 12:
                break
        if len(terms) >= 12:
            break
    return terms[:12]


def _generic_primary_state(blocks: Sequence[InputMeaningBlock]) -> str:
    summaries = [_summary(block) for block in blocks if _summary(block)]
    if len(summaries) >= 2:
        return f"{_as_topic(summaries[0])}だけでなく、{_as_topic(summaries[1])}も同じ場所にある状態として見ています。"
    if summaries:
        return f"{_as_topic(summaries[0])}が、今ここに強く出ている状態として見ています。"
    return "言葉にしきれない気持ちを、今ここに置こうとしている状態として見ています。"


def build_emlis_observation_frame(
    *,
    meaning_blocks: Sequence[InputMeaningBlock],
    whole_input_meaning_arc: Optional[WholeInputMeaningArc] = None,
    evidence: Optional[EvidenceRef] = None,
) -> Optional[EmlisObservationFrame]:
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
    tension_pairs: List[ObservationTensionPair] = []

    if benefit is not None and inconvenience is not None:
        primary_state = "今の生活にある良さと、ふっと現実に戻った時の不便さを同時に抱えている状態として見ています。"
        tension_pairs.append(ObservationTensionPair(left="今の生活の良さ", right="現実の不便さ", relation="both_true"))
        required_roles.append("tension_relation")
    elif normal_wish is not None and worsening is not None:
        primary_state = "普通に生活したい願いと、無視すると悪化すると分かっている現実が同時にある状態として見ています。"
        required_roles.append("tension_relation")
    else:
        primary_state = _generic_primary_state(blocks)

    if normal_wish is not None and worsening is not None:
        tension_pairs.append(ObservationTensionPair(left="普通に生活したい願い", right="無視すると悪化すると分かっている現実", relation="tension"))
        if "tension_relation" not in required_roles:
            required_roles.append("tension_relation")
    elif whole_input_meaning_arc is not None:
        for left, right in list(getattr(whole_input_meaning_arc, "tension_pairs", []) or [])[:2]:
            if str(left) and str(right):
                tension_pairs.append(ObservationTensionPair(left=str(left), right=str(right), relation="tension"))
                if "tension_relation" not in required_roles:
                    required_roles.append("tension_relation")

    pressure_sources: List[str] = []
    if restriction is not None:
        if "restriction_pressure" in roles:
            pressure_sources.append("気をつけなきゃいけないことが多く、圧迫感が強くなっている")
        else:
            pressure_sources.append(_as_topic(_summary(restriction)))
        required_roles.append("pressure_state")

    escape_signal = ""
    if escape is not None:
        if "escape_or_limit" in roles:
            escape_signal = "逃げ出したくなる気持ちは、弱さではなく、それだけ気を張ってきた反応として見ています。"
        else:
            escape_signal = f"{_as_topic(_summary(escape))}も、限界に近いサインとして見ています。"
        required_roles.append("escape_signal")

    self_awareness = ""
    if worsening is not None:
        if "worsening_awareness" in roles:
            self_awareness = "無視すると悪化すると分かっているところに、現実を見ている自己認識があります。"
        else:
            self_awareness = f"{_as_topic(_summary(worsening))}を、自分の状態への気づきとして見ています。"
        required_roles.append("self_awareness")

    strength = ""
    if benefit is not None and inconvenience is not None:
        strength = "生活の良さも現実の不便さも両方見ようとしているところに、今を投げ出さず向き合おうとしている強さがあります。"
    elif normal_wish is not None and worsening is not None:
        strength = "願いと現実の両方を見ているところに、今を投げ出さず向き合おうとしている強さがあります。"
    elif worsening is not None or "self_understanding" in roles or "effort_direction" in roles:
        strength = "自分の状態を見ようとしていること自体に、今を投げ出さず向き合おうとしている強さがあります。"
    if strength:
        required_roles.append("strength")

    close = "Emlisは、その苦しさと、その中に残っている強さを一緒に見ていきます。" if strength else "Emlisは、ここに置いてくれた言葉を軽く扱わず、一緒に見ていきます。"
    required_roles.append("companion_close")

    frame_evidence = _evidence_from_blocks(blocks, evidence)
    return EmlisObservationFrame(
        primary_state=primary_state,
        tension_pairs=tension_pairs,
        pressure_sources=pressure_sources,
        escape_or_limit_signal=escape_signal,
        self_awareness_signal=self_awareness,
        strength_signal=strength,
        companion_close=close,
        evidence_terms=_evidence_terms(blocks),
        required_line_roles=required_roles,
        evidence=frame_evidence,
    )


__all__ = ["build_emlis_observation_frame"]
