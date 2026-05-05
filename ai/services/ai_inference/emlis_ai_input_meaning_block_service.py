# -*- coding: utf-8 -*-
from __future__ import annotations

"""Meaning-block extraction for clear long EmlisAI / Piece inputs.

User-word anchors are small fragments.  When a user writes a clear long entry,
this service groups the current input into meaning blocks and an ordered meaning
arc so EmlisAI and Piece do not collapse the whole entry into one generic focus.
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

_REQUIRED_ROLE_ORDER = (
    # Existing long self-understanding flow.
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
    # Whole-input self/other happiness flow.
    "other_contribution",
    "self_dislike_from_halfway",
    "others_happiness_as_own_happiness",
    "future_not_giving_up",
    "resignation_self",
    "betrayal_fear",
    "own_happiness_wish",
    "existing_happiness_and_more",
    "concrete_life_wishes",
    "unreachable_wish",
    "present_effort_toward_wish",
    # Shorter companion/material roles.
    "missing_guidance",
    "anger_or_frustration",
    "relief_source",
)

_WHOLE_ARC_ORDER = (
    "other_contribution",
    "self_dislike_from_halfway",
    "others_happiness_as_own_happiness",
    "future_not_giving_up",
    "resignation_self",
    "betrayal_fear",
    "own_happiness_wish",
    "existing_happiness_and_more",
    "concrete_life_wishes",
    "unreachable_wish",
    "present_effort_toward_wish",
)

_MUST_KEEP_SELF_AND_OTHERS = (
    "other_contribution",
    "self_dislike_from_halfway",
    "future_not_giving_up",
    "betrayal_fear",
    "own_happiness_wish",
    "concrete_life_wishes",
    "present_effort_toward_wish",
)

_SHOULD_KEEP_SELF_AND_OTHERS = (
    "others_happiness_as_own_happiness",
    "resignation_self",
    "existing_happiness_and_more",
    "unreachable_wish",
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
    connectors = (
        "それでも", "でも同時に", "だからこそ", "どっちも", "両方", "今の自分",
        "頑張れる日は", "しんどい日は", "けれど", "そう思う中でも", "それ以上",
        "でもその願い", "もう既に幸せ",
    )
    return sum(1 for token in connectors if token in compact_text)


def _has(compact_text: str, *tokens: str) -> bool:
    return any(token and token in compact_text for token in tokens)


def _matching_phrases(phrases: Sequence[ShapedUserPhrase], *tokens: str) -> List[ShapedUserPhrase]:
    out: List[ShapedUserPhrase] = []
    for phrase in phrases or []:
        combined = _compact(" ".join([getattr(phrase, "raw_text", ""), getattr(phrase, "phrase", "")]))
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
    """Extract source-bound meaning blocks from the current input."""

    text = _current_text(current_input)
    compact = _compact(text)
    if not compact:
        return []

    blocks: List[InputMeaningBlock] = []
    add = blocks.append

    # Existing long self-understanding / balanced-progress flow.
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

    # Whole-input self / others happiness flow.
    if _has(compact, "誰かの役に立", "人たちの役に立"):
        add(_block(
            block_key="other_contribution",
            role="other_contribution",
            title="誰かの役に立ちたい気持ち",
            summary="誰かの役に立てるならそれでいいと思っている",
            evidence=evidence,
            priority=0.96,
            phrases=_matching_phrases(shaped_user_phrases, "役に立"),
        ))

    if _has(compact, "中途半端", "好きになれない") and _has(compact, "自分のことは好きになれない", "好きになれないけど", "中途半端だから"):
        add(_block(
            block_key="self_dislike_from_halfway",
            role="self_dislike_from_halfway",
            title="中途半端に感じて自分を好きになれない",
            summary="頑張ることも楽しむことも中途半端に感じて、自分のことを好きになれない",
            evidence=evidence,
            priority=0.95,
            phrases=_matching_phrases(shaped_user_phrases, "中途半端", "好きになれない"),
        ))

    if _has(compact, "幸せに笑って", "一番それが幸せ", "1番それが幸せ") and _has(compact, "役に立"):
        add(_block(
            block_key="others_happiness_as_own_happiness",
            role="others_happiness_as_own_happiness",
            title="他者の幸せが自分の幸せに近い",
            summary="他の人が幸せに笑っていて、その人たちの役に立てることが一番幸せに近い",
            evidence=evidence,
            priority=0.90,
            phrases=_matching_phrases(shaped_user_phrases, "幸せに笑", "一番それが幸せ", "1番それが幸せ"),
        ))

    if _has(compact, "諦めたくない", "諦めたくないけれど", "まだ諦めたくない"):
        add(_block(
            block_key="future_not_giving_up",
            role="future_not_giving_up",
            title="自分のことも今後も諦めたくない",
            summary="自分のことも今後のことも、まだ諦めたくない気持ちがある",
            evidence=evidence,
            priority=0.97,
            phrases=_matching_phrases(shaped_user_phrases, "諦めたくない"),
        ))

    if _has(compact, "諦めてる自分", "諦めている自分"):
        add(_block(
            block_key="resignation_self",
            role="resignation_self",
            title="諦めている自分もいる",
            summary="期待して傷つきたくないから、諦めている自分もいる",
            evidence=evidence,
            priority=0.91,
            phrases=_matching_phrases(shaped_user_phrases, "諦めてる自分", "諦めている自分"),
        ))

    if _has(compact, "裏切られたくない", "期待して裏切"):
        add(_block(
            block_key="betrayal_fear",
            role="betrayal_fear",
            title="期待して裏切られたくない怖さ",
            summary="期待してまた裏切られるのが怖い",
            evidence=evidence,
            priority=0.98,
            phrases=_matching_phrases(shaped_user_phrases, "裏切られたくない", "期待"),
        ))

    if _has(compact, "私も幸せになりたい", "自分も幸せになりたい", "幸せになりたいって思う自分"):
        add(_block(
            block_key="own_happiness_wish",
            role="own_happiness_wish",
            title="自分も幸せになりたい願い",
            summary="それでも自分も幸せになりたい気持ちが残っている",
            evidence=evidence,
            priority=1.0,
            phrases=_matching_phrases(shaped_user_phrases, "幸せになりたい"),
        ))

    if _has(compact, "既に幸せ", "すでに幸せ", "それ以上に求め"):
        add(_block(
            block_key="existing_happiness_and_more",
            role="existing_happiness_and_more",
            title="既にある幸せ以上の願い",
            summary="もう既に幸せなことはあると分かっていても、それ以上を求めている",
            evidence=evidence,
            priority=0.88,
            phrases=_matching_phrases(shaped_user_phrases, "既に幸せ", "それ以上"),
        ))

    if _has(compact, "好きなことをもっとしたい", "十分にたのしみたい", "十分に楽しみたい", "パートナーと出会って幸せになりたい"):
        add(_block(
            block_key="concrete_life_wishes",
            role="concrete_life_wishes",
            title="好きなこととパートナーへの具体的な願い",
            summary="好きなことをもっとして、納得いくまで楽しみ、素敵なパートナーと出会って幸せになりたい",
            evidence=evidence,
            priority=1.0,
            phrases=_matching_phrases(shaped_user_phrases, "好きなこと", "たのしみたい", "楽しみたい", "パートナー"),
        ))

    if _has(compact, "手の届か", "手の届かい", "手の届かない"):
        add(_block(
            block_key="unreachable_wish",
            role="unreachable_wish",
            title="手の届かない願い",
            summary="その願いが今は手の届かないところにあるように感じている",
            evidence=evidence,
            priority=0.90,
            phrases=_matching_phrases(shaped_user_phrases, "手の届"),
        ))

    if _has(compact, "今頑張れること", "今がんばれること", "願いに届くように", "大切にしたい"):
        add(_block(
            block_key="present_effort_toward_wish",
            role="present_effort_toward_wish",
            title="願いに届くための今",
            summary="その願いに届くように、今頑張れることを大切にしたい",
            evidence=evidence,
            priority=1.0,
            phrases=_matching_phrases(shaped_user_phrases, "今頑張れる", "願いに届", "大切にしたい"),
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
        min_blocks, max_blocks, ratio = 3, 6, 0.60
    else:
        min_blocks, max_blocks, ratio = 5, 9, 0.70

    roles = {block.role for block in meaning_blocks or []}
    whole_self_other_flow = bool({"own_happiness_wish", "betrayal_fear", "concrete_life_wishes", "present_effort_toward_wish"} & roles)
    if clear_long_input and block_count >= 6:
        min_blocks = max(min_blocks, 5)
        max_blocks = max(max_blocks, min(9 if whole_self_other_flow else 7, block_count))
    if clear_long_input and whole_self_other_flow:
        min_blocks = max(min_blocks, min(7, block_count))
        ratio = max(ratio, 0.75)

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
        reason=f"chars={char_count};paragraphs={p_count};connectors={c_count};blocks={block_count};whole_self_other_flow={whole_self_other_flow}",
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


def build_whole_input_meaning_arc(*, meaning_blocks: Sequence[InputMeaningBlock], evidence: EvidenceRef) -> WholeInputMeaningArc | None:
    keys = {block.block_key for block in meaning_blocks or []}
    has_self_other_arc = {"other_contribution", "own_happiness_wish", "present_effort_toward_wish"} <= keys and (
        "betrayal_fear" in keys or "future_not_giving_up" in keys or "concrete_life_wishes" in keys
    )
    if not has_self_other_arc:
        return None
    ordered = [key for key in _WHOLE_ARC_ORDER if key in keys]
    return WholeInputMeaningArc(
        arc_key="self_and_others_happiness_toward_unreachable_wish",
        title="誰かの幸せと自分自身の幸せの両方を諦めたくない流れ",
        summary=(
            "誰かの役に立つことを幸せに感じながらも、自分自身も好きなことを楽しみ、"
            "パートナーと幸せになりたい願いを諦めたくない。"
            "期待して裏切られる怖さがある中で、その願いへ届くために今できることを大切にしたい。"
        ),
        ordered_block_keys=ordered,
        tension_pairs=[
            ("other_contribution", "own_happiness_wish"),
            ("future_not_giving_up", "resignation_self"),
            ("betrayal_fear", "present_effort_toward_wish"),
        ],
        core_wish_keys=[key for key in ("own_happiness_wish", "concrete_life_wishes", "present_effort_toward_wish") if key in keys],
        fear_keys=[key for key in ("betrayal_fear", "resignation_self") if key in keys],
        present_action_keys=[key for key in ("present_effort_toward_wish",) if key in keys],
        clarity=0.95,
        evidence=[evidence],
    )


def build_major_meaning_retention_plan(
    *,
    meaning_blocks: Sequence[InputMeaningBlock],
    coverage_plan: MeaningCoveragePlan,
    whole_input_meaning_arc: WholeInputMeaningArc | None,
) -> MajorMeaningRetentionPlan:
    keys = {block.block_key for block in meaning_blocks or []}
    if whole_input_meaning_arc is None:
        return MajorMeaningRetentionPlan(
            clear_long_input=bool(coverage_plan.clear_long_input),
            total_block_count=len(meaning_blocks or []),
            must_keep_block_keys=[],
            should_keep_block_keys=[],
            optional_block_keys=[block.block_key for block in meaning_blocks or []],
            min_must_keep_coverage_ratio=0.0,
            reason="no_whole_input_arc",
        )

    must = [key for key in _MUST_KEEP_SELF_AND_OTHERS if key in keys]
    should = [key for key in _SHOULD_KEEP_SELF_AND_OTHERS if key in keys]
    optional = [key for key in (getattr(whole_input_meaning_arc, "ordered_block_keys", []) or []) if key not in set(must) | set(should)]
    return MajorMeaningRetentionPlan(
        clear_long_input=bool(coverage_plan.clear_long_input),
        total_block_count=len(meaning_blocks or []),
        must_keep_block_keys=must,
        should_keep_block_keys=should,
        optional_block_keys=optional,
        forbidden_overcompression_targets=["人間関係", "伸ばしたいこと", "誰かの役に立ちたいだけ", "自分を好きになれないだけ"],
        min_must_keep_coverage_ratio=0.80,
        reason="self_and_others_happiness_arc",
    )


__all__ = [
    "build_input_meaning_blocks",
    "build_meaning_coverage_plan",
    "build_whole_input_meaning_arc",
    "build_major_meaning_retention_plan",
    "selected_meaning_blocks_for_reply",
]
