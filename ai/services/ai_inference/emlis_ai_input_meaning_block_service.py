# -*- coding: utf-8 -*-
from __future__ import annotations

"""Structure-first meaning-block extraction for EmlisAI and Piece.

I2 removes the former example-heavy role keyword table. This module keeps
source-order clauses and chooses broad compatibility roles from grammar,
modality, polarity, time/change and source-field structure. Fixture nouns,
case ids and completed-answer cues cannot select a role.
"""

from collections.abc import Mapping, Sequence
import re
from typing import Any, List

from emlis_ai_types import (
    EvidenceRef,
    InputMeaningBlock,
    MajorMeaningRetentionPlan,
    MeaningCoveragePlan,
    ShapedUserPhrase,
    WholeInputMeaningArc,
)

_SPACE_RE = re.compile(r"\s+")
_CLAUSE_SPLIT_RE = re.compile(r"[。！？!?\n\r]+")
_CONNECTOR_RE = re.compile(r"^(?:でも|だけど|けれど|ただ|一方で?|それでも|とはいえ|そして)[、,\s]*")
_CONTRAST_RE = re.compile(r"(?:でも|だけど|けれど|一方|なのに|とはいえ|その一方)")
_COEXISTENCE_RE = re.compile(r"(?:同時に|両方|どちらも|どっちも|抱えたまま)")
_WISH_RE = re.compile(r"(?:したい|なりたい|していきたい|ほしい|欲しい|願|つもり|(?<!み)たい(?:って|と|気持ち|と思|[、,\s]|$)|たらいい)")
_REFUSAL_RE = re.compile(r"(?:したくない|続けたくない|終わらせたくない|やめたい|投げ出したくない|諦めたくない|拒み|拒否)")
_CONSTRAINT_RE = re.compile(r"(?:できない|出来ない|難しい|無理|限界|しかない|なければ|ないと|せざるを得|取れなく|作れない)")
_NEGATION_RE = re.compile(r"(?:ない|なかった|なく|ません|できず|出来ず)")
_CHANGE_RE = re.compile(r"(?:になった|くなった|変わ|減った|増えた|戻った|進んだ|進めた|できるよう|出来るよう|改善|進歩)")
_SHIFT_RE = re.compile(r"(?:今までは|これまでは|以前は|前は|今は|現在は|昨日|今日|より|一方で)")
_CAUSE_RESULT_RE = re.compile(r"(?:ので|ため|ことで|からこそ|だから|その結果|結果として)")
_UNCERTAIN_RE = re.compile(r"(?:気がする|かもしれ|と思う|かな|憶測|わからない|分からない|不明)")
_SELF_REFERENCE_RE = re.compile(r"(?:自分|私|わたし|僕|ぼく|俺|おれ)")
_SELF_EVALUATION_RE = re.compile(r"(?:だと思|と感じ|弱|悪|責め|傷つ|遅|価値|中途半端|自分は|私は)")
_FEELING_STATE_RE = re.compile(r"(?:感じ|気持ち|不安|悲し|怒|怖|焦|もやもや|しんど|つら|辛|だる|疲|重い|安心|嬉|うれ)")
_CONTINUATION_RE = re.compile(r"(?:続け|ずっと|少しずつ|これから|今後|残って)")
_ACTION_FORM_RE = re.compile(r"(?:した|している|していった|始めた|続けた|試した|行った|動いた|終えた)$")

_ROLE_INFO: dict[str, tuple[str, float, bool]] = {
    "effort_direction": ("入力にある行動や進み方", 0.92, True),
    "self_view": ("入力にある自己評価", 0.94, True),
    "dual_holding": ("入力に併置された二つの向き", 0.93, True),
    "not_want_to_quit": ("入力にある拒否や継続の向き", 0.92, True),
    "continuation_wish": ("入力にある継続意図", 0.91, True),
    "wish_or_hope": ("入力にある願い", 0.90, True),
    "limit_or_exhaustion": ("入力にある制約や限界", 0.91, True),
    "paced_progress": ("入力にある変化", 0.90, True),
    "dual_feeling": ("入力にある対比や併存", 0.89, True),
    "state_awareness": ("入力にある状態認識", 0.86, True),
    "current_expression": ("今の言葉", 0.62, False),
}
_MAJOR_ROLES = frozenset(role for role in _ROLE_INFO if role != "current_expression")


def _clean(value: Any) -> str:
    text = str(value or "").replace("\u3000", " ")
    return _SPACE_RE.sub(" ", text).strip(" 、,。.!！?？\t\n\r")


def _compact(value: Any) -> str:
    return re.sub(r"[\s　、,。.!！?？\t\n\r「」『』（）()]", "", str(value or ""))


def _source_units(current_input: Mapping[str, Any]) -> list[tuple[str, str]]:
    units: list[tuple[str, str]] = []
    for source_field in ("memo", "memo_action"):
        raw = str(current_input.get(source_field) or "").replace("\r", "\n")
        for part in _CLAUSE_SPLIT_RE.split(raw):
            text = _clean(part)
            if text:
                units.append((source_field, text))
    return units


def _current_text(current_input: Mapping[str, Any]) -> str:
    return "\n".join(text for _field, text in _source_units(current_input))


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


def _role_for_text(text: str, *, source_field: str = "memo") -> str:
    """Choose a compatibility role from broad structural operators only."""

    if source_field == "memo_action" or _ACTION_FORM_RE.search(text):
        return "effort_direction"
    has_wish = bool(_WISH_RE.search(text))
    has_constraint = bool(_CONSTRAINT_RE.search(text) or _NEGATION_RE.search(text))
    if _SELF_REFERENCE_RE.search(text) and _SELF_EVALUATION_RE.search(text):
        return "self_view"
    if (has_wish and has_constraint) or _COEXISTENCE_RE.search(text):
        return "dual_holding"
    if _REFUSAL_RE.search(text):
        return "not_want_to_quit"
    if has_wish:
        return "continuation_wish" if _CONTINUATION_RE.search(text) else "wish_or_hope"
    if has_constraint:
        return "limit_or_exhaustion"
    if _CHANGE_RE.search(text) or _SHIFT_RE.search(text):
        return "paced_progress"
    if _CONTRAST_RE.search(text):
        return "dual_feeling"
    if _FEELING_STATE_RE.search(text) or _UNCERTAIN_RE.search(text) or _CAUSE_RESULT_RE.search(text):
        return "state_awareness"
    return "current_expression"


def _matching_phrases(phrases: Sequence[ShapedUserPhrase], text: str) -> List[ShapedUserPhrase]:
    compact_text = _compact(text)
    out: List[ShapedUserPhrase] = []
    for item in phrases or []:
        phrase = _compact(getattr(item, "phrase", "") or getattr(item, "sentence_fragment", ""))
        if phrase and compact_text and (phrase in compact_text or compact_text in phrase):
            out.append(item)
    return out[:3]


def _summary(text: str) -> str:
    return _CONNECTOR_RE.sub("", _clean(text))


def _block(*, role: str, summary: str, phrases: Sequence[ShapedUserPhrase], evidence: EvidenceRef, order: int) -> InputMeaningBlock:
    title, priority, piece_core = _ROLE_INFO.get(role, _ROLE_INFO["current_expression"])
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
        include_in_piece_core=piece_core,
    )


def build_input_meaning_blocks(*, current_input: Mapping[str, Any], shaped_user_phrases: Sequence[ShapedUserPhrase], evidence: EvidenceRef) -> List[InputMeaningBlock]:
    units = _source_units(current_input)
    if not units:
        return []
    blocks: List[InputMeaningBlock] = []
    seen: set[tuple[str, str]] = set()
    for order, (source_field, text) in enumerate(units):
        role = _role_for_text(text, source_field=source_field)
        summary = _summary(text)
        key = (source_field, _compact(summary))
        if not summary or key in seen:
            continue
        seen.add(key)
        blocks.append(
            _block(
                role=role,
                summary=summary,
                phrases=_matching_phrases(shaped_user_phrases, text),
                evidence=evidence,
                order=order,
            )
        )
    # Shaped phrases are provenance only; their legacy role cannot manufacture
    # an additional semantic block outside the source clauses.
    return blocks[:24]


def build_meaning_coverage_plan(*, current_input: Mapping[str, Any], meaning_blocks: Sequence[InputMeaningBlock]) -> MeaningCoveragePlan:
    blocks = list(meaning_blocks or [])
    text = _current_text(current_input)
    level = _input_level(len(text))
    structural_count = sum(1 for block in blocks if block.role in _MAJOR_ROLES)
    connector_count = sum(bool(pattern.search(text)) for pattern in (_CONTRAST_RE, _COEXISTENCE_RE, _CAUSE_RESULT_RE, _SHIFT_RE))
    clear_long = level in {"long", "very_long"} and (
        len(blocks) >= 4 or structural_count >= 3 or connector_count >= 2
    )
    roles: list[str] = []
    for block in blocks:
        if block.role in _MAJOR_ROLES and block.role not in roles:
            roles.append(block.role)
    if not roles and blocks:
        roles.append(blocks[0].role)

    if clear_long:
        min_blocks = min(max(5, len(roles)), len(blocks))
        max_blocks = min(16, len(blocks))
        target_ratio = 1.0 if len(blocks) <= 8 else 0.75
    elif level == "medium":
        min_blocks = min(3, len(blocks))
        max_blocks = min(8, len(blocks))
        target_ratio = 0.70
    elif level == "short":
        min_blocks = min(2, len(blocks))
        max_blocks = min(5, len(blocks))
        target_ratio = 0.60
    else:
        min_blocks = max_blocks = 0
        target_ratio = 0.0

    selected = selected_meaning_blocks_for_reply(
        meaning_blocks=blocks,
        coverage_plan=None,
        limit=max_blocks or min_blocks or 1,
    )
    return MeaningCoveragePlan(
        input_level=level,
        clear_long_input=clear_long,
        meaning_block_count=len(blocks),
        required_roles=roles,
        selected_block_keys=[block.block_key for block in selected],
        min_blocks_to_cover=min_blocks,
        max_blocks_to_cover=max_blocks,
        coverage_ratio_target=target_ratio,
        reason="structure_operator_and_source_anchor_coverage",
    )


def selected_meaning_blocks_for_reply(*, meaning_blocks: Sequence[InputMeaningBlock], coverage_plan: MeaningCoveragePlan | None = None, limit: int | None = None) -> List[InputMeaningBlock]:
    blocks = list(meaning_blocks or [])
    if not blocks:
        return []
    keyed = {block.block_key: block for block in blocks}
    selected: List[InputMeaningBlock] = []
    if coverage_plan is not None:
        for key in coverage_plan.selected_block_keys or []:
            block = keyed.get(key)
            if block is not None and block not in selected:
                selected.append(block)
    cap = max(1, int(limit or getattr(coverage_plan, "max_blocks_to_cover", 0) or 5))
    for block in blocks:
        if len(selected) >= cap:
            break
        if block not in selected:
            selected.append(block)
    return selected[:cap]


def build_whole_input_meaning_arc(*, meaning_blocks: Sequence[InputMeaningBlock], evidence: EvidenceRef) -> WholeInputMeaningArc | None:
    blocks = list(meaning_blocks or [])
    if not blocks:
        return None
    tension_pairs: list[tuple[str, str]] = []
    for left, right in zip(blocks, blocks[1:]):
        if left.role != right.role and (
            left.role in {"dual_holding", "dual_feeling", "limit_or_exhaustion", "self_view"}
            or right.role in {"dual_holding", "dual_feeling", "limit_or_exhaustion", "not_want_to_quit"}
        ):
            pair = (left.block_key, right.block_key)
            if pair not in tension_pairs:
                tension_pairs.append(pair)
    return WholeInputMeaningArc(
        arc_key="generic_current_input_source_order",
        title="現在入力の意味の流れ",
        summary="",
        ordered_block_keys=[block.block_key for block in blocks],
        tension_pairs=tension_pairs,
        core_wish_keys=[block.block_key for block in blocks if block.role in {"wish_or_hope", "continuation_wish", "dual_holding"}],
        fear_keys=[block.block_key for block in blocks if block.role in {"limit_or_exhaustion", "self_view", "dual_feeling"}],
        present_action_keys=[block.block_key for block in blocks if block.role in {"effort_direction", "paced_progress"}],
        clarity=0.84,
        evidence=[evidence],
    )


def build_major_meaning_retention_plan(*, meaning_blocks: Sequence[InputMeaningBlock], coverage_plan: MeaningCoveragePlan, whole_input_meaning_arc: WholeInputMeaningArc | None) -> MajorMeaningRetentionPlan:
    del whole_input_meaning_arc
    blocks = list(meaning_blocks or [])
    if not blocks:
        return MajorMeaningRetentionPlan(clear_long_input=False, total_block_count=0)
    selected = selected_meaning_blocks_for_reply(
        meaning_blocks=blocks,
        coverage_plan=coverage_plan,
    )
    required_roles = set(coverage_plan.required_roles or [])
    must = [block.block_key for block in selected if block.role in required_roles]
    for boundary in (blocks[0].block_key, blocks[-1].block_key):
        if boundary not in must:
            must.append(boundary)
    if coverage_plan.clear_long_input and len(must) < min(5, len(selected)):
        for block in selected:
            if block.block_key not in must:
                must.append(block.block_key)
            if len(must) >= min(8, len(selected)):
                break
    should = [block.block_key for block in selected if block.block_key not in must]
    optional = [block.block_key for block in blocks if block.block_key not in must and block.block_key not in should]
    return MajorMeaningRetentionPlan(
        clear_long_input=bool(coverage_plan.clear_long_input),
        total_block_count=len(blocks),
        must_keep_block_keys=must,
        should_keep_block_keys=should,
        optional_block_keys=optional,
        forbidden_overcompression_targets=[
            "single_topic_summary",
            "category_only_reply",
            "fixed_example_answer",
            "source_order_loss",
        ],
        min_must_keep_coverage_ratio=1.0 if must else 0.0,
        reason="structural_retention_without_example_roles",
    )


__all__ = [
    "build_input_meaning_blocks",
    "build_meaning_coverage_plan",
    "selected_meaning_blocks_for_reply",
    "build_whole_input_meaning_arc",
    "build_major_meaning_retention_plan",
]
