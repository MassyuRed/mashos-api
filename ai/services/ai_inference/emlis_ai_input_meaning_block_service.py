# -*- coding: utf-8 -*-
from __future__ import annotations

"""Generic meaning-block extraction for EmlisAI / Piece inputs.

The user examples are used only by tests.  Runtime extraction in this module is
category based: raw input is converted into broad, reusable meaning roles, then
reply / Piece generation consumes those roles.  This keeps the pipeline from
memorising one example answer.
"""

import re
from dataclasses import dataclass
from typing import Any, Iterable, List, Mapping, Sequence

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
    "self_sacrifice_no_worry",
    "self_sacrifice_rounds_off",
    "old_strategy_ease",
    "alone_burden",
    "capacity_runs_out",
    "talk_or_rely_when_hard",
    "sustainable_by_relying",
    "protective_distance",
    "no_overdoing_choice",
    "not_only_patience",
    "state_based_action",
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
    "missing_guidance",
    "anger_or_frustration",
    "relief_source",
)

_ROLE_PRIORITY = {role: idx for idx, role in enumerate(_REQUIRED_ROLE_ORDER)}

_WISH_AND_FEAR_ROLES = {
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
}

_SELF_SACRIFICE_ROLES = {
    "self_sacrifice_no_worry",
    "self_sacrifice_rounds_off",
    "old_strategy_ease",
    "alone_burden",
    "capacity_runs_out",
    "talk_or_rely_when_hard",
    "sustainable_by_relying",
    "protective_distance",
    "no_overdoing_choice",
    "not_only_patience",
    "state_based_action",
}

_BALANCED_PROGRESS_ROLES = {
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
}


@dataclass(frozen=True)
class _RoleRule:
    role: str
    title: str
    summary: str
    any_groups: Sequence[Sequence[str]]
    all_groups: Sequence[Sequence[str]] = ()
    priority: float = 0.80
    include_in_piece_core: bool = True


_ROLE_RULES: tuple[_RoleRule, ...] = (
    _RoleRule(
        role="state_awareness",
        title="自分の状態への気づき",
        summary="自分の状態や限界に気づいている",
        any_groups=(("疲れ", "しんど", "限界", "ボロボロ", "余裕がない", "ついてこない", "重い"),),
        all_groups=(("分か", "わか", "気づ", "見えて", "状態"),),
        priority=0.94,
    ),
    _RoleRule(
        role="effort_history",
        title="ここまで積み重ねてきた時間",
        summary="ここまで頑張ってきた時間や無理してきた積み重ねがある",
        any_groups=(("頑張ってき", "がんばってき", "無理してき", "積み重", "続けてき"),),
        priority=0.86,
        include_in_piece_core=False,
    ),
    _RoleRule(
        role="continuation_wish",
        title="まだ続けたい気持ち",
        summary="まだ続けたい気持ちや、もう少し頑張りたい本音が残っている",
        any_groups=(("もう少し", "まだ", "続けたい", "頑張りたい", "がんばりたい"),),
        all_groups=(("頑張", "がんば", "続け", "やりたい"),),
        priority=0.94,
    ),
    _RoleRule(
        role="not_want_to_quit",
        title="終わりにしたくない気持ち",
        summary="投げ出したいわけではなく、ここで終わりにしたくない気持ちがある",
        any_groups=(("投げ出したく", "終わりにしたく", "諦めたく", "やめたくない"),),
        priority=0.92,
    ),
    _RoleRule(
        role="fatigue_or_limit",
        title="しんどさや限界感",
        summary="しんどさや心身の重さも近くにある",
        any_groups=(("しんど", "つら", "辛", "疲れ", "重い", "ついてこない", "余裕がない"),),
        priority=0.92,
    ),
    _RoleRule(
        role="collapse_anxiety",
        title="無理を続ける不安",
        summary="このまま無理を続けることへの不安がある",
        any_groups=(("崩れ", "壊れ", "倒れ", "限界", "無理したら", "無理を続け", "怖"),),
        all_groups=(("不安", "怖", "崩", "壊", "限界"),),
        priority=0.93,
    ),
    _RoleRule(
        role="dual_holding",
        title="両方の気持ちを持つこと",
        summary="どちらか一方に切り捨てず、両方の気持ちを抱えている",
        any_groups=(("どっちも", "どちらも", "両方", "抱えたまま", "同時に"),),
        priority=0.98,
    ),
    _RoleRule(
        role="paced_progress",
        title="整えながら進むこと",
        summary="進める時は進み、しんどい時は立ち止まりながら整えていきたい",
        any_groups=(("立ち止", "整え", "少しずつ", "休む", "休ん", "無理に削", "ペース", "頑張れる日"),),
        priority=0.96,
    ),
    _RoleRule(
        role="self_permission",
        title="自分への許可",
        summary="立ち止まることや休むことを自分に許そうとしている",
        any_groups=(("許し", "許す", "休んでもいい", "立ち止まってもいい", "無理しなくていい"),),
        priority=0.82,
        include_in_piece_core=False,
    ),
    _RoleRule(
        role="self_understanding",
        title="自分の状態への意味づけ",
        summary="弱さではなく、自分の状態や限界に気づけていると見ている",
        any_groups=(("弱いわけ", "弱いのでは", "限界に気づ", "状態なんだ", "自己理解"),),
        priority=0.94,
    ),
    _RoleRule(
        role="self_sacrifice_no_worry",
        title="心配や負担をかけないための我慢",
        summary="周りに心配や負担をかけないために、自分が我慢すればいいと思っていた",
        any_groups=(("我慢",),),
        all_groups=(("心配", "負担", "迷惑", "丸く"),),
        priority=0.96,
    ),
    _RoleRule(
        role="self_sacrifice_rounds_off",
        title="自分が我慢すれば収まるという考え",
        summary="自分が我慢すれば物事が収まると考えていた",
        any_groups=(("丸く収", "収まる", "うまく収", "平和に", "波風"),),
        all_groups=(("我慢",),),
        priority=0.96,
    ),
    _RoleRule(
        role="old_strategy_ease",
        title="楽に見えていたやり方",
        summary="我慢することが一番負担の少ないやり方に見えていた",
        any_groups=(("楽なやり方", "楽だ", "楽に", "一番楽", "いちばん楽"),),
        priority=0.80,
        include_in_piece_core=False,
    ),
    _RoleRule(
        role="alone_burden",
        title="一人で抱え込むこと",
        summary="しんどさを一人で抱え込み続けることになる",
        any_groups=(("一人", "ひとり", "自分だけ"),),
        all_groups=(("抱え", "背負", "抱え込", "溜め"),),
        priority=0.96,
    ),
    _RoleRule(
        role="capacity_runs_out",
        title="余裕がなくなること",
        summary="抱え込み続けると余裕がなくなっていく",
        any_groups=(("余裕がなく", "余裕なく", "余裕がない", "余裕をなく"),),
        priority=0.90,
    ),
    _RoleRule(
        role="talk_or_rely_when_hard",
        title="話したり頼ったりする必要",
        summary="しんどい時に話したり頼ったりすることも必要だと気づいている",
        any_groups=(("話", "頼", "相談", "伝え", "助け"),),
        all_groups=(("必要", "大切", "してもいい", "できる方", "無理せず"),),
        priority=0.97,
    ),
    _RoleRule(
        role="sustainable_by_relying",
        title="頼れる方が続けやすいこと",
        summary="誰かに頼れる方が、無理せず続けていけると感じている",
        any_groups=(("無理せず続", "続けていけ", "続けられ"),),
        all_groups=(("頼", "話", "相談"),),
        priority=0.84,
        include_in_piece_core=False,
    ),
    _RoleRule(
        role="protective_distance",
        title="自分を守る距離",
        summary="自分を守るために距離を取ることも必要だと感じている",
        any_groups=(("距離", "離れ", "境界", "離れる"),),
        all_groups=(("守る", "自分", "無理しない", "必要"),),
        priority=0.95,
    ),
    _RoleRule(
        role="no_overdoing_choice",
        title="無理しない選択",
        summary="無理しない選択をすることも必要だと感じている",
        any_groups=(("無理しない", "無理をしない", "休む選択", "離れる選択", "選択"),),
        priority=0.92,
    ),
    _RoleRule(
        role="not_only_patience",
        title="我慢だけが正しいわけではない気づき",
        summary="我慢だけが正しいわけではないと気づいている",
        any_groups=(("我慢だけ", "我慢することだけ", "正しいわけじゃ", "正解じゃ"),),
        priority=0.96,
    ),
    _RoleRule(
        role="state_based_action",
        title="自分の状態を見ながら動くこと",
        summary="自分の状態を見ながら、どう動くかを考えようとしている",
        any_groups=(("自分の状態", "状態を見", "どう動", "様子を見"),),
        priority=0.94,
    ),
    _RoleRule(
        role="other_contribution",
        title="誰かの役に立ちたい気持ち",
        summary="誰かの役に立つことを大切に感じている",
        any_groups=(("役に立", "助け", "支え", "誰かのため", "人のため", "貢献"),),
        priority=0.92,
    ),
    _RoleRule(
        role="self_dislike_from_halfway",
        title="自分を好きになれない気持ち",
        summary="自分の頑張り方や楽しみ方に不足を感じて、自分を好きになれない気持ちがある",
        any_groups=(("好きになれない", "自分が嫌", "自己嫌悪", "中途半端", "足りない"),),
        all_groups=(("自分", "私", "僕", "俺", "中途半端", "好きになれない"),),
        priority=0.92,
    ),
    _RoleRule(
        role="others_happiness_as_own_happiness",
        title="他者の幸せが自分の幸せに近いこと",
        summary="周りの人が幸せでいてくれることを、自分の幸せに近いものとして見ている",
        any_groups=(("幸せ", "笑って", "笑顔"),),
        all_groups=(("役に立", "助け", "支え", "人たち", "誰か"),),
        priority=0.88,
    ),
    _RoleRule(
        role="future_not_giving_up",
        title="まだ諦めたくない気持ち",
        summary="自分のことやこれからのことを、まだ諦めたくない気持ちがある",
        any_groups=(("諦めたくない", "諦めない", "まだ諦", "終わりにしたくない"),),
        priority=0.95,
    ),
    _RoleRule(
        role="resignation_self",
        title="諦めようとする自分",
        summary="傷つかないために諦めようとする自分もいる",
        any_groups=(("諦めて", "諦めよう", "期待しない", "もういい"),),
        all_groups=(("自分", "私", "僕", "俺", "傷つ", "裏切"),),
        priority=0.88,
    ),
    _RoleRule(
        role="betrayal_fear",
        title="期待して傷つく怖さ",
        summary="期待して傷ついたり裏切られたりするのが怖い",
        any_groups=(("裏切", "期待", "傷つきたく", "傷つくのが怖", "怖い"),),
        all_groups=(("期待", "裏切", "傷つ"),),
        priority=0.96,
    ),
    _RoleRule(
        role="own_happiness_wish",
        title="自分も幸せになりたい願い",
        summary="自分自身も幸せになりたい気持ちが残っている",
        any_groups=(("幸せになりたい", "自分も幸せ", "私も幸せ", "自分自身の幸せ", "幸せでいたい"),),
        priority=0.98,
    ),
    _RoleRule(
        role="existing_happiness_and_more",
        title="既にある幸せと、それ以上の願い",
        summary="既にある幸せに気づきながらも、それ以上を求める気持ちがある",
        any_groups=(("既に幸せ", "すでに幸せ", "もう幸せ", "それ以上", "もっと求め", "求めて"),),
        priority=0.84,
    ),
    _RoleRule(
        role="concrete_life_wishes",
        title="具体的な幸せへの願い",
        summary="好きなことや大切な関係を、もっと納得いく形で楽しみたい願いがある",
        any_groups=(("好きなこと", "楽しみたい", "たのしみたい", "納得いく", "大切な人", "恋人", "出会", "家族", "暮らし"),),
        all_groups=(("したい", "なりたい", "願い", "幸せ", "楽し"),),
        priority=0.96,
    ),
    _RoleRule(
        role="unreachable_wish",
        title="遠く見える願い",
        summary="その願いが今は遠く、手が届きにくいもののように見えている",
        any_groups=(("届かない", "遠い", "難しい", "叶わない", "届きにく"),),
        all_groups=(("願", "幸せ", "夢", "目標", "届"),),
        priority=0.86,
    ),
    _RoleRule(
        role="present_effort_toward_wish",
        title="願いに向かう今の行動",
        summary="願いに近づくために、今できることを大切にしようとしている",
        any_groups=(("今", "できること", "頑張れること", "大切にしたい", "積み重ね", "近づく"),),
        all_groups=(("願", "届", "幸せ", "目標", "大切"),),
        priority=0.96,
    ),
    _RoleRule(
        role="missing_guidance",
        title="頑張り方が見えないしんどさ",
        summary="どう頑張ればいいのか分からず、必要な助けや説明がほしい気持ちがある",
        any_groups=(("どう頑張", "頑張り方", "分から", "教えて", "教わ", "説明"),),
        priority=0.86,
    ),
    _RoleRule(
        role="anger_or_frustration",
        title="怒りや悔しさ",
        summary="納得できない気持ちや悔しさが近くにある",
        any_groups=(("むかつ", "イライラ", "怒", "悔し", "腹立", "納得できない"),),
        priority=0.82,
    ),
    _RoleRule(
        role="relief_source",
        title="癒しや落ち着ける場所",
        summary="重さを少し和らげられる時間や場所も大切に感じている",
        any_groups=(("癒", "落ち着", "安心", "話すと", "話していると", "チャット", "休まる"),),
        priority=0.78,
    ),
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
        "でも", "それでも", "ただ", "同時に", "だから", "だからこそ", "一方で", "けれど", "だけど",
        "本当は", "それに", "そのため", "どちらも", "どっちも", "両方", "今の自分", "一方",
    )
    return sum(1 for token in connectors if token in compact_text)


def _contains_any(compact_text: str, tokens: Sequence[str]) -> bool:
    return any(token and token in compact_text for token in tokens)


def _group_matches(compact_text: str, group: Sequence[str]) -> bool:
    return not group or _contains_any(compact_text, group)


def _rule_matches(compact_text: str, rule: _RoleRule) -> bool:
    if rule.any_groups and not any(_group_matches(compact_text, group) for group in rule.any_groups):
        return False
    for group in rule.all_groups or ():
        if not _group_matches(compact_text, group):
            return False
    return True


def _matching_phrases(phrases: Sequence[ShapedUserPhrase], role: str) -> List[ShapedUserPhrase]:
    out: List[ShapedUserPhrase] = []
    for phrase in phrases or []:
        if getattr(phrase, "role", "") == role:
            out.append(phrase)
    return out


def _block_key_for_role(role: str) -> str:
    return role


def _block(
    *,
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
        block_key=_block_key_for_role(role),
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
    """Extract reusable, source-bound meaning blocks from the current input."""

    text = _current_text(current_input)
    compact = _compact(text)
    if not compact:
        return []

    blocks: List[InputMeaningBlock] = []
    seen_roles: set[str] = set()
    for rule in _ROLE_RULES:
        if rule.role in seen_roles:
            continue
        if not _rule_matches(compact, rule):
            continue
        seen_roles.add(rule.role)
        blocks.append(
            _block(
                role=rule.role,
                title=rule.title,
                summary=rule.summary,
                evidence=evidence,
                priority=rule.priority,
                phrases=_matching_phrases(shaped_user_phrases, rule.role),
                include_in_piece_core=rule.include_in_piece_core,
            )
        )

    blocks.sort(key=lambda item: (-float(item.priority), _ROLE_PRIORITY.get(item.role, 99), item.block_key))
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
        min_blocks, max_blocks, ratio = 2, 4, 0.45
    elif level == "long":
        min_blocks, max_blocks, ratio = 3, 6, 0.60
    else:
        min_blocks, max_blocks, ratio = 5, 9, 0.70

    roles = {block.role for block in meaning_blocks or []}
    if clear_long_input and len(roles & _WISH_AND_FEAR_ROLES) >= 3:
        min_blocks = max(min_blocks, min(6, block_count))
        max_blocks = max(max_blocks, min(9, block_count))
        ratio = max(ratio, 0.70)
    if clear_long_input and len(roles & _SELF_SACRIFICE_ROLES) >= 3:
        min_blocks = max(min_blocks, min(5, block_count))
        max_blocks = max(max_blocks, min(8, block_count))
    if clear_long_input and len(roles & _BALANCED_PROGRESS_ROLES) >= 4:
        min_blocks = max(min_blocks, min(5, block_count))
        max_blocks = max(max_blocks, min(8, block_count))

    required_roles = [role for role in _REQUIRED_ROLE_ORDER if role in roles]
    priority_blocks = sorted(
        [block for block in meaning_blocks if block.include_in_emlis_reply],
        key=lambda item: (-float(item.priority), _ROLE_PRIORITY.get(item.role, 99)),
    )
    selected = [block.block_key for block in priority_blocks[: min(max_blocks, block_count)]]

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


def _arc_key_for_roles(roles: set[str]) -> str:
    if len(roles & _SELF_SACRIFICE_ROLES) >= 3:
        return "self_sacrifice_to_boundary_care"
    if len(roles & _WISH_AND_FEAR_ROLES) >= 3:
        return "wish_fear_and_present_effort"
    if len(roles & _BALANCED_PROGRESS_ROLES) >= 4:
        return "limit_but_continue_balanced_progress"
    return "clear_long_input_meaning_flow"


def _arc_title(arc_key: str) -> str:
    return {
        "self_sacrifice_to_boundary_care": "我慢だけではなく、自分を守る選択にも気づく流れ",
        "wish_fear_and_present_effort": "怖さや諦めがありながらも、願いへ向かう流れ",
        "limit_but_continue_balanced_progress": "限界と続けたい気持ちを両方見ながら進む流れ",
    }.get(arc_key, "現在入力の主要な意味の流れ")


def build_whole_input_meaning_arc(*, meaning_blocks: Sequence[InputMeaningBlock], evidence: EvidenceRef) -> WholeInputMeaningArc | None:
    if not meaning_blocks:
        return None
    roles = {block.role for block in meaning_blocks or []}
    clear_candidate = len(meaning_blocks or []) >= 4 or len(roles & (_WISH_AND_FEAR_ROLES | _SELF_SACRIFICE_ROLES | _BALANCED_PROGRESS_ROLES)) >= 3
    if not clear_candidate:
        return None
    arc_key = _arc_key_for_roles(roles)
    ordered = [block.block_key for block in sorted(meaning_blocks, key=lambda item: _ROLE_PRIORITY.get(item.role, 99))]
    summary_parts = [block.summary for block in sorted(meaning_blocks, key=lambda item: _ROLE_PRIORITY.get(item.role, 99))[:4]]
    return WholeInputMeaningArc(
        arc_key=arc_key,
        title=_arc_title(arc_key),
        summary="。".join(part.strip("。") for part in summary_parts if part) + "。",
        ordered_block_keys=ordered,
        tension_pairs=[
            pair for pair in (
                ("continuation_wish", "fatigue_or_limit"),
                ("future_not_giving_up", "resignation_self"),
                ("other_contribution", "own_happiness_wish"),
                ("self_sacrifice_no_worry", "talk_or_rely_when_hard"),
            )
            if pair[0] in roles and pair[1] in roles
        ],
        core_wish_keys=[block.block_key for block in meaning_blocks if block.role in {"own_happiness_wish", "concrete_life_wishes", "present_effort_toward_wish", "continuation_wish", "paced_progress"}],
        fear_keys=[block.block_key for block in meaning_blocks if block.role in {"betrayal_fear", "collapse_anxiety", "resignation_self"}],
        present_action_keys=[block.block_key for block in meaning_blocks if block.role in {"present_effort_toward_wish", "paced_progress", "state_based_action", "no_overdoing_choice"}],
        clarity=0.85,
        evidence=[evidence],
    )


def build_major_meaning_retention_plan(
    *,
    meaning_blocks: Sequence[InputMeaningBlock],
    coverage_plan: MeaningCoveragePlan,
    whole_input_meaning_arc: WholeInputMeaningArc | None,
) -> MajorMeaningRetentionPlan:
    blocks = list(meaning_blocks or [])
    if whole_input_meaning_arc is None or not coverage_plan.clear_long_input:
        return MajorMeaningRetentionPlan(
            clear_long_input=bool(coverage_plan.clear_long_input),
            total_block_count=len(blocks),
            optional_block_keys=[block.block_key for block in blocks],
            min_must_keep_coverage_ratio=0.0,
            reason="no_clear_whole_input_arc",
        )

    roles = {block.role for block in blocks}
    must_roles: set[str]
    if whole_input_meaning_arc.arc_key == "self_sacrifice_to_boundary_care":
        must_roles = {"self_sacrifice_no_worry", "alone_burden", "talk_or_rely_when_hard", "protective_distance", "no_overdoing_choice", "not_only_patience", "state_based_action"}
    elif whole_input_meaning_arc.arc_key == "wish_fear_and_present_effort":
        must_roles = {"other_contribution", "future_not_giving_up", "betrayal_fear", "own_happiness_wish", "concrete_life_wishes", "present_effort_toward_wish"}
    elif whole_input_meaning_arc.arc_key == "limit_but_continue_balanced_progress":
        must_roles = {"state_awareness", "continuation_wish", "fatigue_or_limit", "dual_holding", "paced_progress", "self_understanding"}
    else:
        sorted_blocks = sorted(blocks, key=lambda item: (-float(item.priority), _ROLE_PRIORITY.get(item.role, 99)))
        must_roles = {block.role for block in sorted_blocks[: min(5, len(sorted_blocks))]}

    must = [block.block_key for block in blocks if block.role in must_roles]
    should = [block.block_key for block in blocks if block.role not in must_roles and float(block.priority) >= 0.88]
    optional = [block.block_key for block in blocks if block.block_key not in set(must) | set(should)]
    return MajorMeaningRetentionPlan(
        clear_long_input=bool(coverage_plan.clear_long_input),
        total_block_count=len(blocks),
        must_keep_block_keys=must,
        should_keep_block_keys=should,
        optional_block_keys=optional,
        forbidden_overcompression_targets=["generic_category_only", "single_fragment_only", "short_ack_only"],
        min_must_keep_coverage_ratio=0.70,
        reason=f"arc={whole_input_meaning_arc.arc_key}",
    )


__all__ = [
    "build_input_meaning_blocks",
    "build_meaning_coverage_plan",
    "build_whole_input_meaning_arc",
    "build_major_meaning_retention_plan",
    "selected_meaning_blocks_for_reply",
]
