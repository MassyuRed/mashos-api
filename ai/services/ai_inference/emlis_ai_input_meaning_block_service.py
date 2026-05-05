# -*- coding: utf-8 -*-
from __future__ import annotations

"""Meaning-block extraction for clear long EmlisAI / Piece inputs.

User-word anchors are small fragments.  When a user writes a clear long entry,
this service groups the current input into meaning blocks so the reply and the
Piece preview do not collapse the whole entry into one generic focus.
"""

import re
from typing import Any, Iterable, List, Mapping, Sequence

from emlis_ai_types import EvidenceRef, InputMeaningBlock, MeaningCoveragePlan, ShapedUserPhrase

_SPACE_RE = re.compile(r"\s+")

_REQUIRED_ROLE_ORDER = (
    "state_awareness",
    "effort_history",
    "continuation_wish",
    "not_want_to_quit",
    "fatigue_or_limit",
    "collapse_anxiety",
    "dual_holding",
    "paced_progress",
    "self_permission",
    "self_understanding",
)


def _clean(value: Any) -> str:
    return _SPACE_RE.sub(" ", str(value or "").replace("\u3000", " ")).strip()


def _compact(value: Any) -> str:
    return re.sub(r"[\s　、,。.!！?？\t\n\r]", "", str(value or ""))


def _current_text(current_input: Mapping[str, Any]) -> str:
    return "\n\n".join(
        part
        for part in (
            str(current_input.get("memo") or "").strip(),
            str(current_input.get("memo_action") or "").strip(),
        )
        if part
    )


def _paragraph_count(text: str) -> int:
    # Blank lines are meaningful in the Cocolon input.  If there are no blank
    # lines, still treat punctuation/newline separated chunks as light hints.
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n+", text) if p.strip()]
    if len(paragraphs) >= 2:
        return len(paragraphs)
    return len([p.strip() for p in text.splitlines() if p.strip()])


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


def _connector_count(compact_text: str) -> int:
    connectors = ("それでも", "でも同時に", "だからこそ", "どっちも", "両方", "今の自分", "頑張れる日は", "しんどい日は")
    return sum(1 for token in connectors if token in compact_text)


def _has(compact_text: str, *tokens: str) -> bool:
    return any(token and token in compact_text for token in tokens)


def _matching_phrases(phrases: Sequence[ShapedUserPhrase], *tokens: str) -> List[ShapedUserPhrase]:
    out: List[ShapedUserPhrase] = []
    for phrase in phrases or []:
        combined = _compact(" ".join([getattr(phrase, "raw_text", ""), getattr(phrase, "phrase", ""), getattr(phrase, "summary", "")]))
        if any(token in combined for token in tokens if token):
            out.append(phrase)
    return out


def _block(
    *,
    block_key: str,
    role: str,
    title: str,
    summary: str,
    evidence: EvidenceRef,
    priority: float,
    clarity: float = 0.90,
    phrases: Sequence[ShapedUserPhrase] = (),
    include_in_piece_core: bool = True,
) -> InputMeaningBlock:
    return InputMeaningBlock(
        block_key=block_key,
        role=role,
        title=title,
        summary=summary,
        user_phrases=list(phrases or []),
        evidence=[evidence],
        priority=priority,
        clarity=clarity,
        include_in_emlis_reply=True,
        include_in_piece_core=include_in_piece_core,
    )


def build_input_meaning_blocks(
    *,
    current_input: Mapping[str, Any],
    shaped_user_phrases: Sequence[ShapedUserPhrase] = (),
    evidence: EvidenceRef,
) -> List[InputMeaningBlock]:
    """Extract source-bound meaning blocks from the current input.

    The rules intentionally stay conservative.  A block is created only when the
    user's own words clearly contain the corresponding meaning.
    """

    text = _current_text(current_input)
    compact = _compact(text)
    if not compact:
        return []

    blocks: List[InputMeaningBlock] = []
    add = blocks.append

    if _has(compact, "体も心もボロボロ", "心も体もボロボロ", "ボロボロになってきてる", "ボロボロになってきている"):
        add(_block(
            block_key="state_awareness",
            role="state_awareness",
            title="体と心の限界への自覚",
            summary="体も心もボロボロになってきていることを、自分でもちゃんと分かっている",
            evidence=evidence,
            priority=0.96,
            phrases=_matching_phrases(shaped_user_phrases, "ボロボロ", "体も心"),
        ))

    if _has(compact, "ここまで頑張ってきた", "無理してきた時間", "積み重なってる", "積み重なっている"):
        add(_block(
            block_key="effort_history",
            role="effort_history",
            title="ここまで頑張ってきた積み重ね",
            summary="ここまで頑張ってきた時間や、無理してきた時間が積み重なっている",
            evidence=evidence,
            priority=0.88,
            phrases=_matching_phrases(shaped_user_phrases, "頑張ってきた", "無理してきた", "積み重"),
            include_in_piece_core=False,
        ))

    if _has(compact, "もう少し頑張りたい", "もう少しがんばりたい"):
        add(_block(
            block_key="continuation_wish",
            role="continuation_wish",
            title="まだ頑張りたい本音",
            summary="それでも、もう少し頑張りたい気持ちが残っている",
            evidence=evidence,
            priority=0.96,
            phrases=_matching_phrases(shaped_user_phrases, "もう少し頑張りたい"),
        ))

    if _has(compact, "投げ出したいわけじゃない", "ここで終わりにしたくない", "終わりにしたくない"):
        add(_block(
            block_key="not_want_to_quit",
            role="not_want_to_quit",
            title="投げ出したくない気持ち",
            summary="投げ出したいわけではなく、ここで終わりにしたくない気持ちもある",
            evidence=evidence,
            priority=0.92,
            phrases=_matching_phrases(shaped_user_phrases, "投げ出", "終わりにしたくない"),
        ))

    if _has(compact, "しんどい", "体が重", "気持ちがついてこない", "気持ちがついてこなかった"):
        add(_block(
            block_key="fatigue_or_limit",
            role="fatigue_or_limit",
            title="しんどさと体の重さ",
            summary="しんどさがあり、体が重かったり気持ちがついてこなかったりしている",
            evidence=evidence,
            priority=0.94,
            phrases=_matching_phrases(shaped_user_phrases, "しんど", "体が重", "気持ちがついてこな"),
        ))

    if _has(compact, "崩れてしまいそう", "崩れそう", "このまま無理したら"):
        add(_block(
            block_key="collapse_anxiety",
            role="collapse_anxiety",
            title="崩れそうな不安",
            summary="このまま無理を続けたら崩れてしまいそうな不安がある",
            evidence=evidence,
            priority=0.95,
            phrases=_matching_phrases(shaped_user_phrases, "崩れ", "無理したら"),
        ))

    if _has(compact, "頑張りたい気持ちもしんどい気持ちも", "どっちもちゃんと抱え", "両方抱え", "抱えたまま"):
        add(_block(
            block_key="dual_holding",
            role="dual_holding",
            title="頑張りたい気持ちとしんどさの両方保持",
            summary="頑張りたい気持ちもしんどい気持ちも、どちらかに切り捨てず抱えたまま進みたい",
            evidence=evidence,
            priority=1.0,
            clarity=1.0,
            phrases=_matching_phrases(shaped_user_phrases, "頑張りたい気持ち", "しんどい気持ち", "どっちも", "抱え"),
        ))

    if _has(compact, "頑張れる日は", "しんどい日は", "立ち止まってもいい", "整えながら進", "無理に削る"):
        add(_block(
            block_key="paced_progress",
            role="paced_progress",
            title="整えながら進む",
            summary="頑張れる日は少し前に進み、しんどい日は立ち止まりながら整えて進みたい",
            evidence=evidence,
            priority=0.97,
            phrases=_matching_phrases(shaped_user_phrases, "頑張れる日は", "しんどい日は", "立ち止", "整えながら"),
        ))

    if _has(compact, "立ち止まってもいい", "自分に許し", "許しながら"):
        add(_block(
            block_key="self_permission",
            role="self_permission",
            title="立ち止まる自己許可",
            summary="しんどい日は立ち止まってもいいと、自分に許しながら進もうとしている",
            evidence=evidence,
            priority=0.84,
            phrases=_matching_phrases(shaped_user_phrases, "立ち止", "許し"),
            include_in_piece_core=False,
        ))

    if _has(compact, "弱いわけじゃなく", "弱いわけではなく", "限界に気づけて", "限界に気付けて"):
        add(_block(
            block_key="self_understanding",
            role="self_understanding",
            title="弱さではなく限界への気づき",
            summary="今の自分は弱いのではなく、限界に気づけている状態だと理解している",
            evidence=evidence,
            priority=0.96,
            phrases=_matching_phrases(shaped_user_phrases, "弱いわけ", "限界に気づ"),
        ))

    # Existing shorter work/frustration material can also be grouped when present.
    if _has(compact, "どう頑張ればいい", "教えてくんない", "教えてもらえない") and not any(b.role == "missing_guidance" for b in blocks):
        add(_block(
            block_key="missing_guidance",
            role="missing_guidance",
            title="頑張り方が見えないしんどさ",
            summary="どう頑張ればいいのか分からず、教えてもらえないしんどさがある",
            evidence=evidence,
            priority=0.90,
            phrases=_matching_phrases(shaped_user_phrases, "どう頑張ればいい", "教えて"),
        ))

    blocks.sort(key=lambda item: (-float(item.priority), _REQUIRED_ROLE_ORDER.index(item.role) if item.role in _REQUIRED_ROLE_ORDER else 99, item.block_key))
    return blocks


def build_meaning_coverage_plan(
    *,
    current_input: Mapping[str, Any],
    meaning_blocks: Sequence[InputMeaningBlock],
) -> MeaningCoveragePlan:
    text = _current_text(current_input)
    char_count = len(_clean(text))
    level = _input_level(char_count)
    compact = _compact(text)
    p_count = _paragraph_count(text)
    c_count = _connector_count(compact)
    block_count = len(meaning_blocks or [])
    clear_long_input = level in {"long", "very_long"} and (p_count >= 3 or c_count >= 2 or block_count >= 4)

    if level == "none":
        min_blocks = max_blocks = 0
        ratio = 0.0
    elif level == "short":
        min_blocks, max_blocks, ratio = 1, 2, 0.35
    elif level == "medium":
        min_blocks, max_blocks, ratio = 2, 3, 0.45
    elif level == "long":
        min_blocks, max_blocks, ratio = 3, 5, 0.60
    else:
        min_blocks, max_blocks, ratio = 5, 7, 0.65

    if clear_long_input and block_count >= 6:
        min_blocks = max(min_blocks, 5)
        max_blocks = max(max_blocks, min(7, block_count))

    required_roles = [role for role in _REQUIRED_ROLE_ORDER if any(block.role == role for block in meaning_blocks)]
    priority_blocks = sorted(
        [block for block in meaning_blocks if block.include_in_emlis_reply],
        key=lambda item: (-float(item.priority), _REQUIRED_ROLE_ORDER.index(item.role) if item.role in _REQUIRED_ROLE_ORDER else 99),
    )
    selected = [block.block_key for block in priority_blocks[: max_blocks]]

    return MeaningCoveragePlan(
        input_level=level,
        clear_long_input=clear_long_input,
        meaning_block_count=block_count,
        required_roles=required_roles,
        selected_block_keys=selected,
        min_blocks_to_cover=min(min_blocks, block_count) if block_count else 0,
        max_blocks_to_cover=min(max_blocks, block_count) if block_count else 0,
        coverage_ratio_target=ratio,
        reason=f"chars={char_count};paragraphs={p_count};connectors={c_count};blocks={block_count}",
    )


def selected_meaning_blocks_for_reply(
    blocks: Sequence[InputMeaningBlock],
    plan: MeaningCoveragePlan | None,
) -> List[InputMeaningBlock]:
    if not blocks:
        return []
    if plan is None or not plan.selected_block_keys:
        return list(blocks)
    by_key = {block.block_key: block for block in blocks}
    out = [by_key[key] for key in plan.selected_block_keys if key in by_key]
    return out or list(blocks)


__all__ = [
    "build_input_meaning_blocks",
    "build_meaning_coverage_plan",
    "selected_meaning_blocks_for_reply",
]
