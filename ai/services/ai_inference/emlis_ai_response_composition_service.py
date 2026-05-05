# -*- coding: utf-8 -*-
from __future__ import annotations

"""Generic response composition planning for EmlisAI.

This layer decides reading order.  It must not encode sample-specific flows; it
uses broad semantic roles produced by the meaning-block extractor.
"""

import re
from typing import Dict, List, Sequence

from emlis_ai_types import CompositionLinePlan, EvidenceRef, InputMeaningBlock, ReplyNarrativeArc, ResponseCompositionPlan

_MIDSTREAM_RE = re.compile(r"^(ただ同時に|でも同時に|それでも|だから|だからこそ|そのため|一方で|ただ)[、,]")

_ROLE_PHASES: tuple[tuple[str, set[str]], ...] = (
    ("opening_thesis", {"self_suppression", "wish_or_hope", "limit_or_exhaustion", "self_view", "fear_or_disappointment", "dual_feeling"}),
    ("background", {"burden_avoidance", "relationship_or_others", "self_view", "self_suppression"}),
    ("limit_or_tension", {"limit_or_exhaustion", "fear_or_disappointment", "anger_or_frustration", "sadness_or_pain", "dual_feeling"}),
    ("realization_or_need", {"support_need", "self_protection", "relief_source"}),
    ("new_direction", {"effort_direction", "wish_or_hope", "self_protection"}),
    ("presence", set()),
)


def _blocks_by_role(blocks: Sequence[InputMeaningBlock]) -> Dict[str, List[InputMeaningBlock]]:
    out: Dict[str, List[InputMeaningBlock]] = {}
    for block in blocks or []:
        out.setdefault(str(block.role or "current_expression"), []).append(block)
    return out


def _evidence(blocks: Sequence[InputMeaningBlock]) -> List[EvidenceRef]:
    refs: List[EvidenceRef] = []
    seen: set[tuple[str, str]] = set()
    for block in blocks or []:
        for ref in list(getattr(block, "evidence", []) or []):
            key = (str(getattr(ref, "kind", "") or ""), str(getattr(ref, "ref_id", "") or ""))
            if key in seen:
                continue
            seen.add(key)
            refs.append(ref)
    return refs


def _phase_blocks(blocks: Sequence[InputMeaningBlock], roles: set[str], used: set[str]) -> List[InputMeaningBlock]:
    selected: List[InputMeaningBlock] = []
    for block in blocks or []:
        if block.block_key in used:
            continue
        if block.role in roles:
            selected.append(block)
            used.add(block.block_key)
            if len(selected) >= 2:
                break
    return selected


def _opening_thesis(blocks: Sequence[InputMeaningBlock]) -> str:
    selected = [block for block in blocks if str(block.summary or "").strip()][:3]
    if not selected:
        return "あなたは、今の気持ちや考えを少しずつ言葉にしようとしているのですね。"
    first = selected[0].summary.rstrip("。")
    if len(selected) == 1:
        return f"あなたは、{first}ことを、今ここに置こうとしているのですね。"
    second = selected[1].summary.rstrip("。")
    if len(selected) == 2:
        return f"あなたは、{first}ことだけでなく、{second}ことも一緒に言葉にしているのですね。"
    third = selected[2].summary.rstrip("。")
    return f"あなたは、{first}ことを入口にしながら、{second}ことや、{third}ことまで含めて言葉にしているのですね。"


def build_response_composition_plan(*, input_level: str, clear_long_input: bool, meaning_blocks: Sequence[InputMeaningBlock]) -> ResponseCompositionPlan | None:
    blocks = list(meaning_blocks or [])
    if not blocks:
        return None
    if not clear_long_input and input_level not in {"medium", "long", "very_long"}:
        return ResponseCompositionPlan(
            composition_key="simple_current_reply.v1",
            input_level=input_level,
            clear_long_input=False,
            narrative_pattern="simple_current_receive",
            opening_role="simple_understanding",
            ordered_line_roles=["greeting", "simple_understanding", "presence"],
            required_line_roles=["simple_understanding", "presence"],
            max_lines=3,
            min_lines=2,
            reason="short_or_sparse_current_input",
        )
    used: set[str] = set()
    ordered = ["greeting", "opening_thesis"]
    required = ["opening_thesis"]
    for phase, roles in _ROLE_PHASES[1:-1]:
        picked = _phase_blocks(blocks, roles, used)
        if picked:
            ordered.append(phase)
            if phase in {"limit_or_tension", "realization_or_need", "new_direction"} or clear_long_input:
                required.append(phase)
    ordered.append("presence")
    required.append("presence")
    return ResponseCompositionPlan(
        composition_key="generic_current_input_composition.v1",
        input_level=input_level,
        clear_long_input=bool(clear_long_input),
        narrative_pattern="opening_background_tension_realization_direction_presence",
        opening_role="opening_thesis",
        ordered_line_roles=ordered,
        required_line_roles=required,
        optional_line_roles=[role for role in ordered if role not in required],
        transition_policy="guarded",
        require_opening_thesis=bool(clear_long_input),
        require_presence_line=True,
        allow_paragraph_breaks=bool(clear_long_input),
        max_lines=9 if clear_long_input else 5,
        min_lines=5 if clear_long_input else 2,
        reason="generic_response_composition",
    )


def build_reply_narrative_arc(*, composition_plan: ResponseCompositionPlan | None, meaning_blocks: Sequence[InputMeaningBlock]) -> ReplyNarrativeArc | None:
    if composition_plan is None:
        return None
    blocks = list(meaning_blocks or [])
    used: set[str] = set()
    role_to_keys: Dict[str, List[str]] = {}
    for phase, roles in _ROLE_PHASES:
        if phase == "opening_thesis":
            role_to_keys[phase] = [block.block_key for block in blocks[:3]]
            continue
        if phase == "presence":
            role_to_keys[phase] = []
            continue
        picked = _phase_blocks(blocks, roles, used)
        if picked:
            role_to_keys[phase] = [block.block_key for block in picked]
    return ReplyNarrativeArc(
        arc_key="generic_current_input_narrative",
        title="現在入力を読みやすい順番へ並べる流れ",
        opening_thesis=_opening_thesis(blocks),
        ordered_roles=[role for role in composition_plan.ordered_line_roles if role != "greeting"],
        role_to_block_keys=role_to_keys,
        transition_groups={role: "guarded" for role in composition_plan.ordered_line_roles},
        grounding_required=True,
        clarity=0.82,
        evidence=_evidence(blocks),
    )


def build_composition_line_plans(*, narrative_arc: ReplyNarrativeArc | None, composition_plan: ResponseCompositionPlan | None) -> List[CompositionLinePlan]:
    if narrative_arc is None or composition_plan is None:
        return []
    out: List[CompositionLinePlan] = []
    for role in composition_plan.ordered_line_roles:
        if role == "greeting":
            continue
        out.append(
            CompositionLinePlan(
                line_role=role,
                candidate_key=f"word_reflection.meaning.composition.{role}",
                required=role in set(composition_plan.required_line_roles or []),
                block_keys=list(narrative_arc.role_to_block_keys.get(role, []) or []),
                allowed_opening_connectors=[] if role == "opening_thesis" else ["でも", "それでも", "ただ同時に", "だからこそ", "一方で"],
                forbidden_when_first_content_line=role != "opening_thesis",
                evidence=list(narrative_arc.evidence),
            )
        )
    return out


def first_content_line_starts_midstream(text: str) -> bool:
    for line in [line.strip() for line in str(text or "").splitlines() if line.strip()]:
        if line == "Emlisです。" or line.endswith("Emlisです。"):  # greeting
            continue
        return bool(_MIDSTREAM_RE.search(line))
    return False


__all__ = [
    "build_response_composition_plan",
    "build_reply_narrative_arc",
    "build_composition_line_plans",
    "first_content_line_starts_midstream",
]
