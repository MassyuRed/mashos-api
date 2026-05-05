# -*- coding: utf-8 -*-
from __future__ import annotations

"""Generic response composition planning for EmlisAI immediate replies.

This layer orders meanings for the reader.  It is not tied to a sample input:
patterns are selected from reusable role clusters, and the opening thesis is
composed from extracted meaning blocks.
"""

from typing import Dict, List, Sequence

from emlis_ai_types import (
    CompositionLinePlan,
    EvidenceRef,
    InputMeaningBlock,
    ReplyNarrativeArc,
    ResponseCompositionPlan,
)

_MIDSTREAM_CONNECTORS = ("ただ同時に", "でも同時に", "それでも", "だから", "だからこそ", "そのため", "一方で", "ただ")

_PATTERN_ROLE_ORDER: dict[str, list[str]] = {
    "old_strategy_limit_realization_new_boundary": [
        "opening_thesis",
        "old_strategy",
        "limit_of_strategy",
        "need_or_realization",
        "new_direction",
        "presence",
    ],
    "wish_fear_present_effort": [
        "opening_thesis",
        "value_or_wish",
        "fear_or_resignation",
        "concrete_wish",
        "present_effort",
        "presence",
    ],
    "limit_but_continue_balanced_progress": [
        "opening_thesis",
        "state_and_effort",
        "continuation_wish",
        "fatigue_or_anxiety",
        "dual_holding",
        "paced_progress",
        "self_understanding",
        "presence",
    ],
    "generic_long_meaning_flow": [
        "opening_thesis",
        "meaning_background",
        "meaning_conflict_or_need",
        "meaning_direction",
        "presence",
    ],
}

_ROLE_GROUPS: dict[str, set[str]] = {
    "old_strategy": {"self_sacrifice_no_worry", "self_sacrifice_rounds_off", "old_strategy_ease"},
    "limit_of_strategy": {"alone_burden", "capacity_runs_out"},
    "need_or_realization": {"talk_or_rely_when_hard", "sustainable_by_relying"},
    "new_direction": {"protective_distance", "no_overdoing_choice", "not_only_patience", "state_based_action"},
    "value_or_wish": {"other_contribution", "others_happiness_as_own_happiness", "own_happiness_wish"},
    "fear_or_resignation": {"future_not_giving_up", "resignation_self", "betrayal_fear"},
    "concrete_wish": {"existing_happiness_and_more", "concrete_life_wishes", "unreachable_wish"},
    "present_effort": {"present_effort_toward_wish"},
    "state_and_effort": {"state_awareness", "effort_history"},
    "continuation_wish": {"continuation_wish", "not_want_to_quit"},
    "fatigue_or_anxiety": {"fatigue_or_limit", "collapse_anxiety"},
    "dual_holding": {"dual_holding"},
    "paced_progress": {"paced_progress", "self_permission"},
    "self_understanding": {"self_understanding"},
}

_ROLE_GROUP_ORDER: dict[str, tuple[str, ...]] = {
    "old_strategy": ("self_sacrifice_no_worry", "self_sacrifice_rounds_off", "old_strategy_ease"),
    "limit_of_strategy": ("alone_burden", "capacity_runs_out"),
    "need_or_realization": ("talk_or_rely_when_hard", "sustainable_by_relying"),
    "new_direction": ("not_only_patience", "protective_distance", "no_overdoing_choice", "state_based_action"),
    "value_or_wish": ("other_contribution", "others_happiness_as_own_happiness", "own_happiness_wish"),
    "fear_or_resignation": ("future_not_giving_up", "resignation_self", "betrayal_fear"),
    "concrete_wish": ("existing_happiness_and_more", "concrete_life_wishes", "unreachable_wish"),
    "present_effort": ("present_effort_toward_wish",),
    "state_and_effort": ("state_awareness", "effort_history"),
    "continuation_wish": ("continuation_wish", "not_want_to_quit"),
    "fatigue_or_anxiety": ("fatigue_or_limit", "collapse_anxiety"),
    "dual_holding": ("dual_holding",),
    "paced_progress": ("paced_progress", "self_permission"),
    "self_understanding": ("self_understanding",),
}


def _block_by_role(blocks: Sequence[InputMeaningBlock]) -> Dict[str, InputMeaningBlock]:
    return {str(getattr(block, "role", "") or ""): block for block in blocks or []}


def _blocks_for_group(blocks_by_role: Dict[str, InputMeaningBlock], group_role: str) -> List[InputMeaningBlock]:
    if group_role.startswith("meaning_"):
        return []
    ordered = _ROLE_GROUP_ORDER.get(group_role)
    if ordered is not None:
        return [blocks_by_role[role] for role in ordered if role in blocks_by_role]
    return [block for role, block in blocks_by_role.items() if role in _ROLE_GROUPS.get(group_role, set())]


def _evidence_for_blocks(blocks: Sequence[InputMeaningBlock]) -> List[EvidenceRef]:
    evidence: List[EvidenceRef] = []
    for block in blocks:
        evidence.extend(list(getattr(block, "evidence", []) or []))
    return evidence


def _roles(blocks_by_role: Dict[str, InputMeaningBlock]) -> set[str]:
    return set(blocks_by_role)


def _pattern_for_roles(roles: set[str]) -> str:
    if {"self_sacrifice_no_worry", "alone_burden"} & roles and {"talk_or_rely_when_hard", "protective_distance", "no_overdoing_choice", "not_only_patience"} & roles:
        return "old_strategy_limit_realization_new_boundary"
    if {"own_happiness_wish", "concrete_life_wishes", "present_effort_toward_wish"} & roles and {"betrayal_fear", "resignation_self", "future_not_giving_up", "other_contribution"} & roles:
        return "wish_fear_present_effort"
    if {"dual_holding", "paced_progress", "continuation_wish", "state_awareness", "fatigue_or_limit", "collapse_anxiety"} & roles and len(roles & {"dual_holding", "paced_progress", "continuation_wish", "fatigue_or_limit", "collapse_anxiety", "self_understanding"}) >= 2:
        return "limit_but_continue_balanced_progress"
    return "generic_long_meaning_flow"


def _block_summary(block: InputMeaningBlock) -> str:
    return str(getattr(block, "summary", "") or getattr(block, "title", "") or "").strip("。")


def _opening_thesis(pattern: str, blocks_by_role: Dict[str, InputMeaningBlock], all_blocks: Sequence[InputMeaningBlock]) -> str:
    if pattern == "old_strategy_limit_realization_new_boundary":
        old = next((blocks_by_role.get(role) for role in ("self_sacrifice_no_worry", "self_sacrifice_rounds_off") if blocks_by_role.get(role)), None)
        limit = next((blocks_by_role.get(role) for role in ("alone_burden", "capacity_runs_out") if blocks_by_role.get(role)), None)
        if old and limit:
            return f"あなたは、{_block_summary(old)}けれど、{_block_summary(limit)}ことにも気づいているのですね。"
    if pattern == "wish_fear_present_effort":
        wish = next((blocks_by_role.get(role) for role in ("own_happiness_wish", "concrete_life_wishes", "present_effort_toward_wish") if blocks_by_role.get(role)), None)
        fear = next((blocks_by_role.get(role) for role in ("betrayal_fear", "resignation_self", "future_not_giving_up") if blocks_by_role.get(role)), None)
        if wish and fear:
            return f"あなたは、{_block_summary(fear)}中でも、{_block_summary(wish)}のですね。"
    if pattern == "limit_but_continue_balanced_progress":
        state = next((blocks_by_role.get(role) for role in ("state_awareness", "fatigue_or_limit", "collapse_anxiety") if blocks_by_role.get(role)), None)
        direction = next((blocks_by_role.get(role) for role in ("continuation_wish", "dual_holding", "paced_progress") if blocks_by_role.get(role)), None)
        if state and direction:
            return f"あなたは、{_block_summary(state)}ことと、{_block_summary(direction)}ことを両方見ているのですね。"
    selected = [block for block in all_blocks if str(getattr(block, "summary", "") or "").strip()]
    if selected:
        first = _block_summary(selected[0])
        if len(selected) >= 2:
            second = _block_summary(selected[1])
            return f"あなたは、{first}ことと、{second}ことを、少しでも言葉にしたかったのですね。"
        return f"あなたは、{first}ことを、少しでも言葉にしたかったのですね。"
    return "あなたは、今の気持ちを少しでも言葉にしたかったのですね。"


def build_response_composition_plan(*, input_level: str, clear_long_input: bool, meaning_blocks: Sequence[InputMeaningBlock]) -> ResponseCompositionPlan | None:
    blocks_by_role = _block_by_role(meaning_blocks)
    if not clear_long_input or not blocks_by_role:
        return None
    pattern = _pattern_for_roles(_roles(blocks_by_role))
    ordered_roles = ["greeting", *_PATTERN_ROLE_ORDER.get(pattern, _PATTERN_ROLE_ORDER["generic_long_meaning_flow"])]
    required = [role for role in ordered_roles if role not in {"greeting", "presence"}]
    if "presence" in ordered_roles:
        required.append("presence")
    return ResponseCompositionPlan(
        composition_key=f"{pattern}.generic.v1",
        input_level=input_level,
        clear_long_input=True,
        narrative_pattern=pattern,
        opening_role="opening_thesis",
        ordered_line_roles=ordered_roles,
        required_line_roles=required,
        optional_line_roles=[],
        transition_policy="guarded",
        require_opening_thesis=True,
        require_presence_line=True,
        allow_paragraph_breaks=True,
        max_lines=9,
        min_lines=4,
        reason=f"generic_pattern_from_roles:{pattern}",
    )


def build_reply_narrative_arc(*, composition_plan: ResponseCompositionPlan | None, meaning_blocks: Sequence[InputMeaningBlock]) -> ReplyNarrativeArc | None:
    if composition_plan is None:
        return None
    blocks_by_role = _block_by_role(meaning_blocks)
    pattern = str(getattr(composition_plan, "narrative_pattern", "") or "generic_long_meaning_flow")
    role_to_block_keys: Dict[str, List[str]] = {}
    remaining = list(meaning_blocks or [])
    for role in _PATTERN_ROLE_ORDER.get(pattern, _PATTERN_ROLE_ORDER["generic_long_meaning_flow"]):
        if role in {"opening_thesis", "presence"}:
            role_to_block_keys[role] = []
            continue
        group_blocks = _blocks_for_group(blocks_by_role, role)
        if role.startswith("meaning_"):
            group_blocks = remaining[:2]
            remaining = remaining[2:]
        role_to_block_keys[role] = [block.block_key for block in group_blocks]
    evidence = _evidence_for_blocks(meaning_blocks)
    opening = _opening_thesis(pattern, blocks_by_role, meaning_blocks)
    return ReplyNarrativeArc(
        arc_key=pattern,
        title="現在入力の意味を読める順番に並べる流れ",
        opening_thesis=opening,
        ordered_roles=[role for role in _PATTERN_ROLE_ORDER.get(pattern, _PATTERN_ROLE_ORDER["generic_long_meaning_flow"]) if role != "opening_thesis"],
        role_to_block_keys=role_to_block_keys,
        transition_groups={role: role for role in role_to_block_keys},
        grounding_required=True,
        clarity=0.86,
        evidence=evidence,
    )


def build_composition_line_plans(*, narrative_arc: ReplyNarrativeArc | None, composition_plan: ResponseCompositionPlan | None) -> List[CompositionLinePlan]:
    if narrative_arc is None or composition_plan is None:
        return []
    line_plans: List[CompositionLinePlan] = []
    for role in composition_plan.ordered_line_roles:
        if role == "greeting":
            continue
        block_keys = [] if role == "opening_thesis" else list((narrative_arc.role_to_block_keys or {}).get(role, []) or [])
        line_plans.append(
            CompositionLinePlan(
                line_role=role,
                candidate_key=f"word_reflection.meaning.composition.{role}",
                required=role in set(composition_plan.required_line_roles),
                block_keys=block_keys,
                allowed_opening_connectors=[] if role == "opening_thesis" else list(_MIDSTREAM_CONNECTORS),
                forbidden_when_first_content_line=role != "opening_thesis",
                evidence=list(narrative_arc.evidence or []),
            )
        )
    return line_plans


def first_content_line_starts_midstream(text: str) -> bool:
    lines = [line.strip() for line in str(text or "").splitlines() if line.strip()]
    content = [line for line in lines if line != "Emlisです。" and not line.endswith("Emlisです。")] or lines
    if not content:
        return False
    first = content[0]
    return any(first.startswith(connector) for connector in _MIDSTREAM_CONNECTORS)


__all__ = [
    "build_response_composition_plan",
    "build_reply_narrative_arc",
    "build_composition_line_plans",
    "first_content_line_starts_midstream",
]
