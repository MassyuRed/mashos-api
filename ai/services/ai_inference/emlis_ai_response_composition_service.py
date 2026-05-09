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
    ("opening_thesis", {"state_awareness", "effort_history", "continuation_wish", "self_suppression", "wish_or_hope", "limit_or_exhaustion", "fatigue_or_limit", "self_view", "fear_or_disappointment", "collapse_anxiety", "dual_feeling", "dual_holding"}),
    ("background", {"state_awareness", "effort_history", "burden_avoidance", "relationship_or_others", "self_view", "self_suppression"}),
    ("limit_or_tension", {"fatigue_or_limit", "collapse_anxiety", "not_want_to_quit", "limit_or_exhaustion", "fear_or_disappointment", "anger_or_frustration", "sadness_or_pain", "dual_feeling", "dual_holding"}),
    ("realization_or_need", {"support_need", "self_protection", "relief_source", "self_understanding"}),
    ("new_direction", {"continuation_wish", "paced_progress", "effort_direction", "wish_or_hope", "self_protection"}),
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
    roles = _role_set(blocks)
    if "other_contribution" in roles and "own_happiness_wish" in roles:
        return "あなたは、誰かの役に立ちたい気持ちと、自分自身も幸せになりたい願いを、同じ場所で言葉にしているのですね。"
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


def _role_set(blocks: Sequence[InputMeaningBlock]) -> set[str]:
    return {str(getattr(block, "role", "") or "") for block in blocks or []}


def _is_self_sacrifice_boundary_flow(blocks: Sequence[InputMeaningBlock]) -> bool:
    roles = _role_set(blocks)
    has_old_strategy = bool({"self_suppression", "burden_avoidance"} & roles)
    has_limit = bool({"limit_or_exhaustion", "fatigue_or_limit"} & roles)
    has_next_care = bool({"support_need", "self_protection", "state_awareness"} & roles)
    return has_old_strategy and has_limit and has_next_care


def _self_sacrifice_opening_thesis(blocks: Sequence[InputMeaningBlock]) -> str:
    roles = _blocks_by_role(blocks)
    old = roles.get("burden_avoidance", []) or roles.get("self_suppression", [])
    limit = roles.get("limit_or_exhaustion", []) or roles.get("fatigue_or_limit", [])
    old_text = str(getattr(old[0], "summary", "") or "我慢して丸く収めようとしてきたこと").rstrip("。")
    limit_text = str(getattr(limit[0], "summary", "") or "一人で抱え込むしんどさ").rstrip("。")
    if "抱え" not in limit_text:
        limit_text = f"{limit_text}、一人で抱え込むしんどさ"
    if "我慢" not in old_text:
        old_text = f"我慢してきたことや、{old_text}"
    return f"あなたは、{old_text}ことと、{limit_text}ことを同じ流れとして言葉にしているのですね。"


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
    if _is_self_sacrifice_boundary_flow(blocks):
        return ResponseCompositionPlan(
            composition_key="self_sacrifice_boundary_care.v1",
            input_level=input_level,
            clear_long_input=bool(clear_long_input),
            narrative_pattern="old_strategy_limit_realization_new_boundary",
            opening_role="opening_thesis",
            ordered_line_roles=["greeting", "opening_thesis", "old_strategy", "limit_or_tension", "realization_or_need", "new_boundary", "state_awareness", "presence"],
            required_line_roles=["opening_thesis", "old_strategy", "limit_or_tension", "realization_or_need", "new_boundary", "presence"],
            optional_line_roles=["state_awareness"],
            transition_policy="guarded",
            require_opening_thesis=True,
            require_presence_line=True,
            allow_paragraph_breaks=bool(clear_long_input),
            max_lines=9 if clear_long_input else 6,
            min_lines=6 if clear_long_input else 4,
            reason="generic_self_sacrifice_boundary_flow",
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
    if getattr(composition_plan, "narrative_pattern", "") == "old_strategy_limit_realization_new_boundary":
        by_role = _blocks_by_role(blocks)
        role_to_keys: Dict[str, List[str]] = {
            "opening_thesis": [block.block_key for block in blocks[:2]],
            "old_strategy": [block.block_key for block in (by_role.get("burden_avoidance", []) + by_role.get("self_suppression", []))[:3]],
            "limit_or_tension": [block.block_key for block in (by_role.get("limit_or_exhaustion", []) + by_role.get("fatigue_or_limit", []))[:2]],
            "realization_or_need": [block.block_key for block in by_role.get("support_need", [])[:2]],
            "new_boundary": [block.block_key for block in by_role.get("self_protection", [])[:2]],
            "state_awareness": [block.block_key for block in by_role.get("state_awareness", [])[:1]],
            "presence": [],
        }
        return ReplyNarrativeArc(
            arc_key="self_sacrifice_boundary_care_arc",
            title="我慢して抱え込む旧い方法から、自分を守る境界へ移る流れ",
            opening_thesis=_self_sacrifice_opening_thesis(blocks),
            ordered_roles=[role for role in composition_plan.ordered_line_roles if role != "greeting"],
            role_to_block_keys=role_to_keys,
            transition_groups={role: "guarded" for role in composition_plan.ordered_line_roles},
            grounding_required=True,
            clarity=0.88,
            evidence=_evidence(blocks),
        )

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
