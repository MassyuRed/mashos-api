# -*- coding: utf-8 -*-
from __future__ import annotations

"""Generic meaning-block extraction for EmlisAI and Piece.

The block extractor is intentionally category-based, not example-answer-based.
It maps current-input paragraphs/clauses into reusable semantic roles and keeps
source summaries for the reply generator.  Example texts should only live in
tests; runtime rules here remain broad.
"""

import re
from typing import Any, List, Mapping, Sequence

from emlis_ai_types import (
    EvidenceRef,
    InputMeaningBlock,
    MajorMeaningRetentionPlan,
    MeaningCoveragePlan,
    ShapedUserPhrase,
    WholeInputMeaningArc,
)

_SPACE_RE = re.compile(r"\s+")
_SENTENCE_SPLIT_RE = re.compile(r"[。！？!?\n\r]+")

_ROLE_DEFINITIONS: tuple[dict[str, Any], ...] = (
    {"role": "self_suppression", "title": "自分を抑えてきたこと", "keywords": ("我慢", "抑え", "飲み込", "耐え"), "priority": 0.90},
    {"role": "burden_avoidance", "title": "心配や負担を避けたいこと", "keywords": ("心配", "負担", "迷惑", "丸く", "収ま"), "priority": 0.86},
    {"role": "limit_or_exhaustion", "title": "しんどさや限界感", "keywords": ("しんど", "疲", "つら", "辛", "余裕", "限界", "重", "崩", "消耗"), "priority": 0.94},
    {"role": "support_need", "title": "話すことや頼ることの必要", "keywords": ("頼", "相談", "話", "助け", "支え"), "priority": 0.92},
    {"role": "self_protection", "title": "自分を守る選択", "keywords": ("守", "距離", "境界", "離れ", "無理しない"), "priority": 0.90},
    {"role": "wish_or_hope", "title": "願いや望み", "keywords": ("したい", "なりたい", "ほしい", "欲しい", "願", "叶", "求め"), "priority": 0.93},
    {"role": "fear_or_disappointment", "title": "怖さや傷つきへの警戒", "keywords": ("怖", "恐", "不安", "裏切", "嫌われ", "見捨", "傷つ", "期待"), "priority": 0.91},
    {"role": "self_view", "title": "自分への見方", "keywords": ("自分", "好きになれ", "弱", "中途", "責任", "非", "気づ"), "priority": 0.88},
    {"role": "effort_direction", "title": "今できることや進み方", "keywords": ("頑張", "進", "続け", "整え", "大切", "立ち止", "諦め"), "priority": 0.89},
    {"role": "dual_feeling", "title": "両方の気持ち", "keywords": ("両方", "どっちも", "同時", "一方", "それでも", "でも"), "priority": 0.86},
    {"role": "relationship_or_others", "title": "人との関係や他者への思い", "keywords": ("相手", "恋人", "友達", "家族", "職場", "上司", "同僚", "他者", "周り"), "priority": 0.84},
    {"role": "relief_source", "title": "安心や癒しになるもの", "keywords": ("癒", "安心", "落ち着", "楽になる"), "priority": 0.80},
    {"role": "anger_or_frustration", "title": "怒りや悔しさ", "keywords": ("怒", "むかつ", "イライラ", "悔", "腹立"), "priority": 0.82},
    {"role": "sadness_or_pain", "title": "悲しさや痛み", "keywords": ("悲", "泣", "苦し", "痛", "寂", "つら", "辛"), "priority": 0.82},
)

_REQUIRED_LONG_ROLES = (
    "limit_or_exhaustion",
    "wish_or_hope",
    "fear_or_disappointment",
    "self_view",
    "effort_direction",
    "support_need",
    "self_protection",
    "dual_feeling",
    "relationship_or_others",
)


def _clean(value: Any) -> str:
    text = str(value or "").replace("\u3000", " ")
    text = _SPACE_RE.sub(" ", text)
    return text.strip(" 、,。.!！?？\t\n\r")


def _compact(value: Any) -> str:
    return re.sub(r"[\s　、,。.!！?？\t\n\r「」『』（）()]", "", str(value or ""))


def _current_text(current_input: Mapping[str, Any]) -> str:
    return "\n".join(_clean(current_input.get(field)) for field in ("memo", "memo_action") if _clean(current_input.get(field)))


def _paragraphs(text: str) -> List[str]:
    raw_parts = re.split(r"\n\s*\n+", str(text or ""))
    if len([p for p in raw_parts if _clean(p)]) <= 1:
        raw_parts = _SENTENCE_SPLIT_RE.split(str(text or ""))
    out: List[str] = []
    for part in raw_parts:
        clean = _clean(part)
        if clean:
            out.append(clean)
    return out


def _input_level(char_count: int) -> str:
    if char_count <= 0:
        return "none"
    if char_count < 120:
        return "short"
    if char_count < 240:
        return "medium"
    if char_count < 420:
        return "long"
    return "very_long"


def _role_for_text(text: str) -> tuple[str, dict[str, Any]]:
    compact = _compact(text)
    best = _ROLE_DEFINITIONS[-1]
    best_score = -1
    for definition in _ROLE_DEFINITIONS:
        hits = sum(1 for keyword in definition["keywords"] if keyword in compact)
        if hits > best_score:
            best = definition
            best_score = hits
    if best_score <= 0:
        return "current_expression", {"role": "current_expression", "title": "今の言葉", "priority": 0.55, "keywords": ()}
    return str(best["role"]), best


def _matching_phrases(phrases: Sequence[ShapedUserPhrase], text: str, role: str) -> List[ShapedUserPhrase]:
    compact_text = _compact(text)
    out: List[ShapedUserPhrase] = []
    for item in phrases or []:
        phrase = str(getattr(item, "phrase", "") or "")
        if not phrase:
            continue
        if getattr(item, "role", "") == role or _compact(phrase) in compact_text or compact_text in _compact(phrase):
            out.append(item)
    return out[:3]


def _summary(text: str) -> str:
    clean = _clean(text)
    clean = re.sub(r"^(ただ同時に|でも同時に|それでも|だからこそ|だから|一方で|でも|ただ)[、,\s]*", "", clean)
    if len(clean) <= 88:
        return clean
    return clean[:86].rstrip("、,") + "…"


def _block(*, role: str, title: str, summary: str, phrases: Sequence[ShapedUserPhrase], evidence: EvidenceRef, order: int, priority: float) -> InputMeaningBlock:
    return InputMeaningBlock(
        block_key=f"meaning:{order}:{role}",
        role=role,
        title=title,
        summary=summary,
        user_phrases=list(phrases),
        evidence=[evidence],
        priority=priority,
        clarity=0.86 if role != "current_expression" else 0.62,
        include_in_emlis_reply=True,
        include_in_piece_core=role in {"wish_or_hope", "fear_or_disappointment", "self_view", "effort_direction", "dual_feeling", "relationship_or_others"},
    )


def build_input_meaning_blocks(*, current_input: Mapping[str, Any], shaped_user_phrases: Sequence[ShapedUserPhrase], evidence: EvidenceRef) -> List[InputMeaningBlock]:
    text = _current_text(current_input)
    if not text:
        return []
    parts = _paragraphs(text)
    blocks: List[InputMeaningBlock] = []
    seen: set[tuple[str, str]] = set()
    for order, part in enumerate(parts):
        role, definition = _role_for_text(part)
        summary = _summary(part)
        key = (role, _compact(summary))
        if key in seen:
            continue
        seen.add(key)
        blocks.append(_block(role=role, title=str(definition.get("title") or "今の言葉"), summary=summary, phrases=_matching_phrases(shaped_user_phrases, part, role), evidence=evidence, order=order, priority=float(definition.get("priority") or 0.60)))
    # Also promote safe shaped phrases that represent distinct roles not covered by paragraphs.
    covered_roles = {block.role for block in blocks}
    for item in shaped_user_phrases or []:
        role = str(getattr(item, "role", "") or "current_expression")
        if role in covered_roles or role == "current_expression":
            continue
        phrase = _clean(getattr(item, "sentence_fragment", "") or getattr(item, "phrase", ""))
        if not phrase:
            continue
        phrase_key = _compact(phrase)
        if any(phrase_key and (phrase_key in _compact(block.summary) or _compact(block.summary) in phrase_key) for block in blocks):
            continue
        role2, definition = _role_for_text(phrase)
        if role2 == "current_expression":
            role2 = role
        blocks.append(_block(role=role2, title=str(definition.get("title") or "今の言葉"), summary=_summary(phrase), phrases=[item], evidence=evidence, order=len(blocks), priority=float(definition.get("priority") or 0.70)))
        covered_roles.add(role)
        covered_roles.add(role2)
    # Keep enough breadth for long inputs without turning every clause into a line.
    # Preserve source order here; selection can use priority but the reply should
    # still read in the user's own order.
    return blocks[:10]


def build_meaning_coverage_plan(*, current_input: Mapping[str, Any], meaning_blocks: Sequence[InputMeaningBlock]) -> MeaningCoveragePlan:
    text = _current_text(current_input)
    char_count = len(text)
    level = _input_level(char_count)
    paragraph_count = len(_paragraphs(text))
    connector_count = sum(text.count(token) for token in ("でも", "それでも", "同時", "だから", "一方", "どちら", "両方"))
    clear_long = level in {"long", "very_long"} and (paragraph_count >= 3 or connector_count >= 2 or len(meaning_blocks) >= 4)
    roles = [block.role for block in meaning_blocks]
    required_roles = [role for role in _REQUIRED_LONG_ROLES if role in roles]
    if not required_roles and meaning_blocks:
        required_roles = roles[: min(4, len(roles))]
    min_blocks = 0
    max_blocks = 0
    target_ratio = 0.0
    if clear_long:
        min_blocks = min(5 if level == "long" else 6, max(3, len(meaning_blocks)))
        max_blocks = min(8, max(min_blocks, len(meaning_blocks)))
        target_ratio = 0.60 if level == "long" else 0.68
    elif level == "medium":
        min_blocks = min(3, len(meaning_blocks))
        max_blocks = min(4, len(meaning_blocks))
        target_ratio = 0.45
    elif level == "short":
        min_blocks = min(2, len(meaning_blocks))
        max_blocks = min(3, len(meaning_blocks))
        target_ratio = 0.30
    selected = selected_meaning_blocks_for_reply(meaning_blocks=meaning_blocks, coverage_plan=None, limit=max_blocks or min_blocks or 2)
    return MeaningCoveragePlan(
        input_level=level,
        clear_long_input=clear_long,
        meaning_block_count=len(meaning_blocks),
        required_roles=required_roles,
        selected_block_keys=[block.block_key for block in selected],
        min_blocks_to_cover=min_blocks,
        max_blocks_to_cover=max_blocks,
        coverage_ratio_target=target_ratio,
        reason="generic_paragraph_and_semantic_role_coverage",
    )


def selected_meaning_blocks_for_reply(*, meaning_blocks: Sequence[InputMeaningBlock], coverage_plan: MeaningCoveragePlan | None = None, limit: int | None = None) -> List[InputMeaningBlock]:
    blocks = list(meaning_blocks or [])
    if not blocks:
        return []
    keyed = {block.block_key: block for block in blocks}
    selected: List[InputMeaningBlock] = []
    if coverage_plan is not None:
        for key in getattr(coverage_plan, "selected_block_keys", []) or []:
            block = keyed.get(key)
            if block is not None and block not in selected:
                selected.append(block)
    def _order(block: InputMeaningBlock) -> int:
        try:
            return int(str(block.block_key).split(":")[1])
        except Exception:
            return 999
    cap = int(limit or getattr(coverage_plan, "max_blocks_to_cover", 0) or 5)
    if not selected:
        top = sorted(blocks, key=lambda block: (-float(block.priority or 0), _order(block)))[: max(1, cap)]
        selected = sorted(top, key=_order)
    else:
        selected = sorted(selected, key=_order)
    return selected[: max(1, cap)]


def build_whole_input_meaning_arc(*, meaning_blocks: Sequence[InputMeaningBlock], evidence: EvidenceRef) -> WholeInputMeaningArc | None:
    blocks = list(meaning_blocks or [])
    if not blocks:
        return None
    roles = [block.role for block in blocks]
    summary_parts = [block.summary for block in blocks[:4] if block.summary]
    title = "現在入力の意味の流れ"
    summary = " / ".join(summary_parts) if summary_parts else "現在入力に含まれる複数の気持ちや考え"
    tension_pairs: list[tuple[str, str]] = []
    if "wish_or_hope" in roles and "fear_or_disappointment" in roles:
        tension_pairs.append(("wish_or_hope", "fear_or_disappointment"))
    if "self_suppression" in roles and "self_protection" in roles:
        tension_pairs.append(("self_suppression", "self_protection"))
    if "limit_or_exhaustion" in roles and "effort_direction" in roles:
        tension_pairs.append(("limit_or_exhaustion", "effort_direction"))
    return WholeInputMeaningArc(
        arc_key="generic_current_input_arc",
        title=title,
        summary=summary,
        ordered_block_keys=[block.block_key for block in blocks],
        tension_pairs=tension_pairs,
        core_wish_keys=[block.block_key for block in blocks if block.role in {"wish_or_hope", "effort_direction"}],
        fear_keys=[block.block_key for block in blocks if block.role in {"fear_or_disappointment", "limit_or_exhaustion"}],
        present_action_keys=[block.block_key for block in blocks if block.role in {"effort_direction", "self_protection", "support_need"}],
        clarity=0.82,
        evidence=[evidence],
    )


def build_major_meaning_retention_plan(*, meaning_blocks: Sequence[InputMeaningBlock], coverage_plan: MeaningCoveragePlan, whole_input_meaning_arc: WholeInputMeaningArc | None) -> MajorMeaningRetentionPlan:
    blocks = list(meaning_blocks or [])
    if not blocks:
        return MajorMeaningRetentionPlan(clear_long_input=False, total_block_count=0)
    selected = selected_meaning_blocks_for_reply(meaning_blocks=blocks, coverage_plan=coverage_plan)
    must = [block.block_key for block in selected if block.role in set(getattr(coverage_plan, "required_roles", []) or [])]
    if getattr(coverage_plan, "clear_long_input", False) and len(must) < min(4, len(selected)):
        must = [block.block_key for block in selected[: min(6, len(selected))]]
    should = [block.block_key for block in selected if block.block_key not in must]
    return MajorMeaningRetentionPlan(
        clear_long_input=bool(getattr(coverage_plan, "clear_long_input", False)),
        total_block_count=len(blocks),
        must_keep_block_keys=must,
        should_keep_block_keys=should,
        optional_block_keys=[block.block_key for block in blocks if block.block_key not in must and block.block_key not in should],
        forbidden_overcompression_targets=["single_topic_summary", "category_only_reply", "fixed_example_answer"],
        min_must_keep_coverage_ratio=0.65 if must else 0.0,
        reason="generic_major_meaning_retention",
    )


__all__ = [
    "build_input_meaning_blocks",
    "build_meaning_coverage_plan",
    "selected_meaning_blocks_for_reply",
    "build_whole_input_meaning_arc",
    "build_major_meaning_retention_plan",
]
