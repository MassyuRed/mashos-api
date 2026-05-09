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
    {"role": "relief_or_benefit_in_constraint", "title": "制約の中にもある安心や良さ", "keywords": ("家にいて", "家にいる", "家のこと", "お家のこと", "リラックス", "自分のことを優先", "優先して", "整え", "嬉しい", "うれしい"), "priority": 0.989},
    {"role": "reality_gap_or_inconvenience", "title": "現実に戻った時の不便さ", "keywords": ("現実", "向き合", "気が抜け", "ダメージ", "不便", "ふっと", "ふって"), "priority": 0.987},
    {"role": "restriction_pressure", "title": "気をつけ続ける圧迫感", "keywords": ("気をつけなきゃ", "気をつけないと", "気をつけ", "気を付け", "全部無視", "無視して", "制約", "注意し"), "priority": 0.983},
    {"role": "normal_life_wish", "title": "普通に生活したい願い", "keywords": ("普通に生活", "普通に", "生活したい", "全部無視して普通", "自由に生活"), "priority": 0.981},
    {"role": "worsening_awareness", "title": "悪化することへの理解", "keywords": ("悪化", "分かってる", "わかってる", "分かっている", "わかっている", "そんなの分か", "そんなのわか"), "priority": 0.979},
    {"role": "escape_or_limit", "title": "逃げたい限界感", "keywords": ("逃げ出したく", "逃げ出したい", "逃げたい", "投げ出したい", "全部投げ", "限界"), "priority": 0.978},
    {"role": "balanced_self_awareness", "title": "良さと苦しさの両方を見ていること", "keywords": ("嬉しいんだけど", "うれしいんだけど", "嬉しいけど", "うれしいけど", "両方"), "priority": 0.845},
    {"role": "other_contribution", "title": "誰かの役に立つこと", "keywords": ("誰かの役に立", "役に立て", "人たちが幸せ", "幸せに笑", "その人たちの役"), "priority": 0.995},
    {"role": "self_dislike_from_halfway", "title": "自分を中途半端だと見てしまうこと", "keywords": ("中途半端", "好きになれない", "自分のことは好き"), "priority": 0.992},
    {"role": "future_not_giving_up", "title": "今後をまだ諦めたくないこと", "keywords": ("まだ諦めたくない", "諦めたくない", "今後のこと"), "priority": 0.99},
    {"role": "betrayal_fear", "title": "期待して裏切られたくない怖さ", "keywords": ("裏切られたくない", "期待して", "諦めている自分", "諦めてる自分"), "priority": 0.988},
    {"role": "own_happiness_wish", "title": "自分自身も幸せになりたい願い", "keywords": ("私も幸せになりたい", "自分も幸せ", "幸せになりたい"), "priority": 0.986},
    {"role": "concrete_life_wishes", "title": "具体的に楽しみたいことや出会いたいこと", "keywords": ("好きなこと", "たのしみたい", "楽しみたい", "パートナー", "出会って", "十分に"), "priority": 0.984},
    {"role": "unreachable_wish", "title": "手の届かないように見える願い", "keywords": ("手の届かない", "手の届かい", "届かない所", "届きにく"), "priority": 0.982},
    {"role": "present_effort_toward_wish", "title": "願いに届くために今できること", "keywords": ("今頑張れること", "届くように", "今できること", "大切にしたい"), "priority": 0.98},
    {"role": "state_awareness", "title": "今の状態への気づき", "keywords": ("自分でも", "分かって", "わかって", "状態", "気づけ", "気づいて", "見えて"), "priority": 0.98},
    {"role": "effort_history", "title": "ここまで積み重ねてきた努力", "keywords": ("ここまで頑張", "頑張ってきた", "無理してきた", "積み重な", "時間もちゃんと", "続けてきた"), "priority": 0.97},
    {"role": "continuation_wish", "title": "まだ続けたい願い", "keywords": ("もう少し頑張りたい", "もう少し", "頑張りたい", "続けたい", "進みたい", "残ってるのも本音"), "priority": 0.96},
    {"role": "not_want_to_quit", "title": "投げ出したくない気持ち", "keywords": ("投げ出したいわけじゃ", "終わりにしたくない", "ここで終わり", "諦めたくない", "終わらせたくない"), "priority": 0.955},
    {"role": "fatigue_or_limit", "title": "しんどさや限界感", "keywords": ("しんど", "疲", "つら", "辛", "余裕", "限界", "体が重", "気持ちがついてこ", "ボロボロ", "消耗"), "priority": 0.95},
    {"role": "collapse_anxiety", "title": "崩れてしまいそうな不安", "keywords": ("崩れて", "崩れ", "無理したら", "不安", "壊れ", "倒れ"), "priority": 0.945},
    {"role": "dual_holding", "title": "両方を抱えたまま進みたいこと", "keywords": ("どっちも", "両方", "抱えたまま", "無理やり選", "片方", "同時"), "priority": 0.94},
    {"role": "paced_progress", "title": "自分のペースで整えながら進むこと", "keywords": ("頑張れる日", "しんどい日", "立ち止", "整えながら", "前に進", "少しだけ", "無理に削"), "priority": 0.935},
    {"role": "self_understanding", "title": "弱さではなく状態理解として見ること", "keywords": ("弱いわけじゃ", "弱いわけでは", "限界に気づ", "状態なんだ", "自分は弱", "気づけてる"), "priority": 0.93},
    {"role": "self_suppression", "title": "自分を抑えてきたこと", "keywords": ("我慢", "抑え", "飲み込", "耐え"), "priority": 0.90},
    {"role": "burden_avoidance", "title": "心配や負担を避けたいこと", "keywords": ("心配", "負担", "迷惑", "丸く", "収ま"), "priority": 0.86},
    {"role": "limit_or_exhaustion", "title": "しんどさや限界感", "keywords": ("しんど", "疲", "つら", "辛", "余裕", "限界", "重", "崩", "消耗", "抱え込"), "priority": 0.90},
    {"role": "support_need", "title": "話すことや頼ることの必要", "keywords": ("頼", "相談", "話", "助け", "支え"), "priority": 0.92},
    {"role": "self_protection", "title": "自分を守る選択", "keywords": ("守", "距離", "境界", "離れ", "無理しない"), "priority": 0.90},
    {"role": "wish_or_hope", "title": "願いや望み", "keywords": ("したい", "なりたい", "ほしい", "欲しい", "願", "叶", "求め"), "priority": 0.89},
    {"role": "fear_or_disappointment", "title": "怖さや傷つきへの警戒", "keywords": ("怖", "恐", "不安", "裏切", "嫌われ", "見捨", "傷つ", "期待"), "priority": 0.88},
    {"role": "self_view", "title": "自分への見方", "keywords": ("自分", "好きになれ", "弱", "中途", "責任", "非", "気づ"), "priority": 0.87},
    {"role": "effort_direction", "title": "今できることや進み方", "keywords": ("頑張", "進", "続け", "整え", "大切", "立ち止", "諦め"), "priority": 0.86},
    {"role": "dual_feeling", "title": "両方の気持ち", "keywords": ("両方", "どっちも", "同時", "一方", "それでも", "でも"), "priority": 0.85},
    {"role": "relationship_or_others", "title": "人との関係や他者への思い", "keywords": ("相手", "恋人", "友達", "家族", "職場", "上司", "同僚", "他者", "周り", "先輩"), "priority": 0.84},
    {"role": "relief_source", "title": "安心や癒しになるもの", "keywords": ("チャット", "お話", "癒", "安心", "落ち着", "楽になる"), "priority": 0.925},
    {"role": "anger_or_frustration", "title": "怒りや悔しさ", "keywords": ("怒", "むかつ", "イライラ", "悔", "腹立"), "priority": 0.82},
    {"role": "sadness_or_pain", "title": "悲しさや痛み", "keywords": ("悲", "泣", "苦し", "痛", "寂", "つら", "辛"), "priority": 0.82},
)

_REQUIRED_LONG_ROLES = (
    "relief_or_benefit_in_constraint",
    "reality_gap_or_inconvenience",
    "restriction_pressure",
    "normal_life_wish",
    "worsening_awareness",
    "escape_or_limit",
    "balanced_self_awareness",
    "other_contribution",
    "self_dislike_from_halfway",
    "future_not_giving_up",
    "betrayal_fear",
    "own_happiness_wish",
    "concrete_life_wishes",
    "unreachable_wish",
    "present_effort_toward_wish",
    "state_awareness",
    "effort_history",
    "continuation_wish",
    "not_want_to_quit",
    "fatigue_or_limit",
    "collapse_anxiety",
    "dual_holding",
    "paced_progress",
    "self_understanding",
    "limit_or_exhaustion",
    "wish_or_hope",
    "fear_or_disappointment",
    "self_view",
    "effort_direction",
    "support_need",
    "self_protection",
    "dual_feeling",
    "relationship_or_others",
    "relief_source",
)


def _clean(value: Any) -> str:
    text = str(value or "").replace("\u3000", " ")
    text = _SPACE_RE.sub(" ", text)
    return text.strip(" 、,。.!！?？\t\n\r")


def _compact(value: Any) -> str:
    return re.sub(r"[\s　、,。.!！?？\t\n\r「」『』（）()]", "", str(value or ""))


def _current_text(current_input: Mapping[str, Any]) -> str:
    parts: List[str] = []
    for field in ("memo", "memo_action"):
        raw = str(current_input.get(field) or "").replace("\r", "\n").strip()
        if raw:
            parts.append(raw)
    return "\n".join(parts)


def _paragraphs(text: str) -> List[str]:
    # Keep source order while avoiding over-compressed paragraph blocks.
    # Long diary-like inputs often use line breaks rather than punctuation; each
    # line can carry a distinct meaning that must remain available to EmlisAI.
    raw_units: List[str] = []
    for paragraph in re.split(r"\n\s*\n+", str(text or "")):
        for part in re.split(r"[。！？!?\n\r]+", paragraph):
            clean = _clean(part)
            if clean:
                raw_units.append(clean)

    out: List[str] = []
    for unit in raw_units:
        if out and out[-1].endswith(("一人で", "話したり", "無理せず", "ことも")):
            out[-1] = _clean(f"{out[-1]}{unit}")
        else:
            out.append(unit)
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
    clean = clean.replace("時ある", "時がある").replace("ことある", "ことがある")
    clean = clean.replace("めっちゃ", "かなり").replace("くんない", "もらえない")
    clean = clean.replace("1番", "一番").replace("届かい", "届かない").replace("諦めてる", "諦めている")
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
        include_in_piece_core=role in {
            "other_contribution",
            "self_dislike_from_halfway",
            "future_not_giving_up",
            "betrayal_fear",
            "own_happiness_wish",
            "concrete_life_wishes",
            "unreachable_wish",
            "present_effort_toward_wish",
            "continuation_wish",
            "not_want_to_quit",
            "collapse_anxiety",
            "dual_holding",
            "paced_progress",
            "self_understanding",
            "wish_or_hope",
            "fear_or_disappointment",
            "self_view",
            "effort_direction",
            "dual_feeling",
            "relationship_or_others",
            "relief_source",
            "relief_or_benefit_in_constraint",
            "reality_gap_or_inconvenience",
            "restriction_pressure",
            "normal_life_wish",
            "worsening_awareness",
            "escape_or_limit",
            "balanced_self_awareness",
        },
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
    return blocks[:16]


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
        min_blocks = min(8 if level == "long" else 9, max(3, len(meaning_blocks)))
        max_blocks = min(18, max(min_blocks, len(meaning_blocks)))
        target_ratio = 0.60 if level == "long" else 0.68
    elif level == "medium":
        min_blocks = min(4, len(meaning_blocks))
        max_blocks = min(6, len(meaning_blocks))
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
    if selected:
        for block in blocks:
            if len(selected) >= max(1, cap):
                break
            if block not in selected:
                selected.append(block)
        selected = sorted(selected, key=_order)
    else:
        top = sorted(blocks, key=lambda block: (-float(block.priority or 0), _order(block)))[: max(1, cap)]
        selected = sorted(top, key=_order)
    return selected[: max(1, cap)]


def build_whole_input_meaning_arc(*, meaning_blocks: Sequence[InputMeaningBlock], evidence: EvidenceRef) -> WholeInputMeaningArc | None:
    blocks = list(meaning_blocks or [])
    if not blocks:
        return None
    roles = [block.role for block in blocks]
    if "other_contribution" in roles and "own_happiness_wish" in roles:
        summary_parts = [block.summary for block in blocks[:6] if block.summary]
        return WholeInputMeaningArc(
            arc_key="self_and_others_happiness_toward_unreachable_wish",
            title="誰かの幸せと自分自身の願いを同時に扱う流れ",
            summary=" / ".join(summary_parts) if summary_parts else "誰かの役に立つ気持ちと自分自身の幸せへの願い",
            ordered_block_keys=[block.block_key for block in blocks],
            tension_pairs=[("other_contribution", "own_happiness_wish"), ("future_not_giving_up", "betrayal_fear")],
            core_wish_keys=[block.block_key for block in blocks if block.role in {"own_happiness_wish", "concrete_life_wishes", "unreachable_wish", "present_effort_toward_wish"}],
            fear_keys=[block.block_key for block in blocks if block.role in {"betrayal_fear", "self_dislike_from_halfway"}],
            present_action_keys=[block.block_key for block in blocks if block.role in {"present_effort_toward_wish"}],
            clarity=0.86,
            evidence=[evidence],
        )
    summary_parts = [block.summary for block in blocks[:4] if block.summary]
    title = "現在入力の意味の流れ"
    summary = " / ".join(summary_parts) if summary_parts else "現在入力に含まれる複数の気持ちや考え"
    tension_pairs: list[tuple[str, str]] = []
    if "relief_or_benefit_in_constraint" in roles and "reality_gap_or_inconvenience" in roles:
        tension_pairs.append(("relief_or_benefit_in_constraint", "reality_gap_or_inconvenience"))
    if "normal_life_wish" in roles and "worsening_awareness" in roles:
        tension_pairs.append(("normal_life_wish", "worsening_awareness"))
    if "restriction_pressure" in roles and "escape_or_limit" in roles:
        tension_pairs.append(("restriction_pressure", "escape_or_limit"))
    if ("wish_or_hope" in roles or "continuation_wish" in roles) and ("fear_or_disappointment" in roles or "collapse_anxiety" in roles):
        tension_pairs.append(("continuation_wish" if "continuation_wish" in roles else "wish_or_hope", "collapse_anxiety" if "collapse_anxiety" in roles else "fear_or_disappointment"))
    if "self_suppression" in roles and "self_protection" in roles:
        tension_pairs.append(("self_suppression", "self_protection"))
    if ("fatigue_or_limit" in roles or "limit_or_exhaustion" in roles) and ("paced_progress" in roles or "effort_direction" in roles):
        tension_pairs.append(("fatigue_or_limit" if "fatigue_or_limit" in roles else "limit_or_exhaustion", "paced_progress" if "paced_progress" in roles else "effort_direction"))
    return WholeInputMeaningArc(
        arc_key="generic_current_input_arc",
        title=title,
        summary=summary,
        ordered_block_keys=[block.block_key for block in blocks],
        tension_pairs=tension_pairs,
        core_wish_keys=[block.block_key for block in blocks if block.role in {"wish_or_hope", "continuation_wish", "effort_direction", "paced_progress"}],
        fear_keys=[block.block_key for block in blocks if block.role in {"fear_or_disappointment", "collapse_anxiety", "limit_or_exhaustion", "fatigue_or_limit"}],
        present_action_keys=[block.block_key for block in blocks if block.role in {"effort_direction", "paced_progress", "self_protection", "support_need"}],
        clarity=0.82,
        evidence=[evidence],
    )


def build_major_meaning_retention_plan(*, meaning_blocks: Sequence[InputMeaningBlock], coverage_plan: MeaningCoveragePlan, whole_input_meaning_arc: WholeInputMeaningArc | None) -> MajorMeaningRetentionPlan:
    blocks = list(meaning_blocks or [])
    if not blocks:
        return MajorMeaningRetentionPlan(clear_long_input=False, total_block_count=0)
    selected = selected_meaning_blocks_for_reply(meaning_blocks=blocks, coverage_plan=coverage_plan)
    roles = [block.role for block in blocks]
    if "other_contribution" in roles and "own_happiness_wish" in roles:
        must_roles = [
            role for role in (
                "other_contribution",
                "self_dislike_from_halfway",
                "future_not_giving_up",
                "betrayal_fear",
                "own_happiness_wish",
                "concrete_life_wishes",
                "unreachable_wish",
                "present_effort_toward_wish",
            ) if role in roles
        ]
        return MajorMeaningRetentionPlan(
            clear_long_input=bool(getattr(coverage_plan, "clear_long_input", False)),
            total_block_count=len(blocks),
            must_keep_block_keys=must_roles,
            should_keep_block_keys=[],
            optional_block_keys=[block.block_key for block in blocks if block.role not in set(must_roles)],
            forbidden_overcompression_targets=["single_topic_summary", "category_only_reply", "fixed_example_answer"],
            min_must_keep_coverage_ratio=0.82,
            reason="self_and_others_happiness_major_meaning_retention",
        )

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
