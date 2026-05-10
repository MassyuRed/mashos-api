# -*- coding: utf-8 -*-
from __future__ import annotations

"""Final reader review for EmlisAI replies.

The review is generic: it blocks broken grammar, midstream openings,
mechanical/meta language, missing presence, and under-answering.  It does not
look for sample-specific phrases.
"""

import re
from typing import Any, List, Optional

from emlis_ai_types import FinalReviewIssue, FinalReviewResult, WorldModel

BROKEN_CONNECTION_RE = re.compile(
    r"(それだと|けど|けれど|でも|から|ので|のに|だって)こと"
    r"|ことが、今回(?:大きく|いちばん)残っていたのですね"
    r"|というところが残っていたのですね"
    r"|今回いちばん残っていた言葉"
    r"|かなぁのあと"
    r"|になるです|だったです|したです|ですです"
)
MECHANICAL_META_RE = re.compile(r"(入力として|認識しています|構造として|分析すると|理解しました|受け取りました)")
BROKEN_GENERIC_PHRASE_RE = re.compile(r"(大切な場所として見えています|生活したいことも大切な場所)")
INTERNAL_OBSERVATION_LANGUAGE_RE = re.compile(r"(コンフォートゾーン|スペック|精神の問題|皮算用|要求と期待が膨れ上が|本質は|あなたの本質)")
ABSTRACT_HISTORY_RE = re.compile(r"(最近の履歴の中でも、近いテーマ|最近の流れも踏まえて|今の気持ちを見ます|近いテーマがまた顔を出して)")
STALE_MEANING_BLOCK_RE = re.compile(r"(前回入力|前回の入力|以前の入力|別の入力|過去の入力|前の入力)")
PRESENCE_RE = re.compile(r"(軽く扱いません|雑に扱いません|小さく扱いません|そのまま置いて大丈夫|きれいにしなくて大丈夫|そばに置いて|大切にします|大切に扱います|一緒に見ていきます|一緒に向き合います|苦しさと、その中に残っている強さ)")
SECOND_PERSON_PRONOUN_RE = re.compile(r"(あなたは|あなたの|あなたが|あなたに)")
BROKEN_NOUN_PHRASE_RE = re.compile(r"(だ|だから|けど|けれど|から)(気持ち|思い|願い|状態)")
MIDSTREAM_OPENING_RE = re.compile(r"^(ただ同時に|でも同時に|それでも|だから|だからこそ|そのため|一方で|ただ)[、,]")


def _lines(text: Any) -> List[str]:
    return [line.strip() for line in str(text or "").splitlines() if line.strip()]


def _presence_line(world_model: Optional[WorldModel]) -> str:
    """Retired: final review must not add user-facing Emlis body text."""

    return ""


def _ending_group(line: str) -> str:
    if line.endswith("のですね。") or line.endswith("のですね"):
        return "ne_desu"
    if line.endswith("のだと思います。") or line.endswith("と思います。"):
        return "omoimasu"
    if line.endswith("ありました。") or line.endswith("いました。"):
        return "arimashita"
    if line.endswith("ません。"):
        return "masen"
    return "other"


def _repair_ending_repetition(lines: List[str]) -> List[str]:
    repaired: List[str] = []
    ne_count = 0
    groups: List[str] = []
    for line in lines:
        cur = line
        group = _ending_group(cur)
        if group == "ne_desu":
            ne_count += 1
            if ne_count > 2:
                cur = re.sub(r"のですね。?$", "のだと思います。", cur)
                group = _ending_group(cur)
        if len(groups) >= 2 and groups[-1] == groups[-2] == group and group != "other":
            if group == "arimashita":
                cur = re.sub(r"ありました。?$", "あります。", cur)
                cur = re.sub(r"いました。?$", "います。", cur)
            elif group == "omoimasu":
                cur = re.sub(r"と思います。?$", "と見ています。", cur)
            elif group == "masen":
                cur = re.sub(r"ません。?$", "ない場所です。", cur)
            elif group == "ne_desu":
                cur = re.sub(r"のですね。?$", "のだと思います。", cur)
            group = _ending_group(cur)
        repaired.append(cur)
        groups.append(group)
    return repaired


def _has_three_same_endings(lines: List[str]) -> bool:
    groups = [_ending_group(line) for line in lines]
    return any(a == b == c and a != "other" for a, b, c in zip(groups, groups[1:], groups[2:]))


def _first_content_index(lines: List[str]) -> int | None:
    for idx, line in enumerate(lines):
        if line == "Emlisです。" or line.endswith("Emlisです。"):  # greeting
            continue
        return idx
    return None


def _summary_covered(text: str, summary: str) -> bool:
    compact_text = re.sub(r"[\s　、,。.!！?？「」『』（）()]", "", str(text or ""))
    compact_summary = re.sub(r"[\s　、,。.!！?？「」『』（）()]", "", str(summary or ""))
    if compact_summary and compact_summary[:18] in compact_text:
        return True
    for token in re.split(r"[\s　、,。.!！?？]+", str(summary or "")):
        token = token.strip()
        if len(token) >= 3 and token in text:
            return True
    return False


def _role_terms(role: str) -> tuple[str, ...]:
    return {
        "burden_avoidance": ("心配", "負担", "我慢", "丸く収"),
        "self_suppression": ("我慢", "正しい"),
        "limit_or_exhaustion": ("一人で抱え込", "余裕がなく", "しんど"),
        "fatigue_or_limit": ("しんど", "疲", "余裕"),
        "support_need": ("話したり頼ったり", "頼る", "話す"),
        "self_protection": ("距離を取", "無理しない選択", "自分を守"),
        "state_awareness": ("自分の状態", "状態を見"),
        "other_contribution": ("誰かの役に立", "役に立つ"),
        "self_dislike_from_halfway": ("中途半端", "好きになれない"),
        "future_not_giving_up": ("諦めたくない",),
        "betrayal_fear": ("諦めている自分", "裏切られたくない", "裏切られるのが怖"),
        "own_happiness_wish": ("幸せになりたい",),
        "concrete_life_wishes": ("好きなこと", "パートナー", "たのしみたい", "楽しみたい"),
        "unreachable_wish": ("手の届かない",),
        "present_effort_toward_wish": ("今頑張れること", "今できること"),
        "relief_or_benefit_in_constraint": ("リラックス", "自分のことを優先", "家のこと", "嬉しい", "良さ"),
        "reality_gap_or_inconvenience": ("現実", "不便", "ダメージ", "気が抜け"),
        "restriction_pressure": ("気をつけ", "圧迫", "無視"),
        "normal_life_wish": ("普通に生活", "生活したい"),
        "worsening_awareness": ("悪化", "分かって", "わかって"),
        "escape_or_limit": ("逃げ出したく", "逃げたい", "弱さではなく"),
        "balanced_self_awareness": ("両方", "同時", "良さ", "苦しさ"),
    }.get(str(role or ""), ())


def _block_covered(text: str, block: object) -> bool:
    summary = str(getattr(block, "summary", "") or "")
    if _summary_covered(text, summary):
        return True
    terms = _role_terms(str(getattr(block, "role", "") or ""))
    if not terms:
        return False
    return any(term and term in text for term in terms)



def _observation_frame_sufficient(lines: List[str], world_model: Optional[WorldModel]) -> bool:
    frame = getattr(getattr(world_model, "facts", None), "emlis_observation_frame", None) if world_model is not None else None
    if frame is None:
        return False
    content_lines = [line for line in lines if line and not line.endswith("Emlisです。") and line != "Emlisです。"]
    if len(content_lines) < 4:
        return False
    text = "\n".join(content_lines)
    has_state = bool(str(getattr(frame, "primary_state", "") or "") and ("状態" in text or "見ています" in text))
    has_relation = bool(list(getattr(frame, "tension_pairs", []) or [])) and any(word in text for word in ("間で", "同時", "重なって", "両方"))
    has_strength = bool(str(getattr(frame, "strength_signal", "") or "")) and ("強さ" in text or "向き合" in text)
    has_close = bool(PRESENCE_RE.search(text))
    return bool(has_state and has_close and (has_relation or has_strength))

def _long_input_underanswered(lines: List[str], world_model: Optional[WorldModel]) -> bool:
    coverage = getattr(getattr(world_model, "facts", None), "meaning_coverage_plan", None) if world_model is not None else None
    blocks = list(getattr(getattr(world_model, "facts", None), "meaning_blocks", []) or []) if world_model is not None else []
    if _observation_frame_sufficient(lines, world_model):
        return False
    if coverage is None or not bool(getattr(coverage, "clear_long_input", False)):
        return False
    min_blocks = int(getattr(coverage, "min_blocks_to_cover", 0) or 0)
    if len(lines) < max(5, min_blocks + 1):
        return True
    text = "\n".join(lines)
    required = min(max(3, min_blocks), len(blocks)) if blocks else 0
    if required <= 0:
        return False
    covered = sum(1 for block in blocks if _block_covered(text, block))
    return covered < required


def review_emlis_ai_reply_text(*, comment_text: Any, world_model: Optional[WorldModel] = None) -> FinalReviewResult:
    issues: List[FinalReviewIssue] = []
    lines = _lines(comment_text)
    first_content_idx = _first_content_index(lines)
    if first_content_idx is not None and MIDSTREAM_OPENING_RE.search(lines[first_content_idx]):
        issues.append(FinalReviewIssue(code="first_content_line_midstream", severity="block", line_index=first_content_idx, message=lines[first_content_idx]))

    repaired_lines: List[str] = []
    changed = False
    for idx, line in enumerate(lines):
        if SECOND_PERSON_PRONOUN_RE.search(line):
            issues.append(FinalReviewIssue(code="second_person_pronoun", severity="block", line_index=idx, message=line))
            changed = True
            continue
        if BROKEN_GENERIC_PHRASE_RE.search(line):
            issues.append(FinalReviewIssue(code="broken_generic_phrase", severity="block", line_index=idx, message=line))
            changed = True
            continue
        if BROKEN_CONNECTION_RE.search(line):
            issues.append(FinalReviewIssue(code="raw_anchor_broken_connection", severity="block", line_index=idx, message=line))
            changed = True
            continue
        if BROKEN_NOUN_PHRASE_RE.search(line):
            issues.append(FinalReviewIssue(code="broken_noun_phrase", severity="block", line_index=idx, message=line))
            changed = True
            continue
        if STALE_MEANING_BLOCK_RE.search(line):
            issues.append(FinalReviewIssue(code="stale_meaning_block_leak", severity="block", line_index=idx, message=line))
            changed = True
            continue
        if ABSTRACT_HISTORY_RE.search(line):
            issues.append(FinalReviewIssue(code="abstract_history_reference", severity="repair", line_index=idx, message=line))
            changed = True
            continue
        if MECHANICAL_META_RE.search(line):
            issues.append(FinalReviewIssue(code="mechanical_meta_language", severity="block", line_index=idx, message=line))
            changed = True
            continue
        if INTERNAL_OBSERVATION_LANGUAGE_RE.search(line):
            issues.append(FinalReviewIssue(code="internal_observation_language", severity="block", line_index=idx, message=line))
            changed = True
            continue
        repaired_lines.append(line)

    original_ne_count = sum(line.count("のですね") for line in repaired_lines)
    original_ending_repetition = original_ne_count > 2 or _has_three_same_endings(repaired_lines)
    repaired_lines = _repair_ending_repetition(repaired_lines)
    if original_ending_repetition:
        issues.append(FinalReviewIssue(code="sentence_ending_repetition", severity="repair", line_index=None, message="ending repetition repaired"))
        changed = True

    if not any(PRESENCE_RE.search(line) for line in repaired_lines):
        # Phase 1 seal: final review must not add replacement / presence
        # sentences.  It can only judge.  Missing presence is a blocking issue
        # for legacy text, and Display Gate will fail closed.
        issues.append(FinalReviewIssue(code="presence_line_missing", severity="block", line_index=None, message="presence line missing"))

    if _long_input_underanswered(repaired_lines, world_model):
        issues.append(FinalReviewIssue(code="long_input_underanswered", severity="block", line_index=None, message="clear long input reply is too short"))

    # Phase 1 seal: final review does not rewrite, delete, or append
    # user-facing Emlis observation text.  It only reports pass/fail issues.
    repaired_text = None
    final_text = "\n".join(lines).strip()
    final_lines = _lines(final_text)
    final_first_idx = _first_content_index(final_lines)
    midstream_remaining = final_first_idx is not None and MIDSTREAM_OPENING_RE.search(final_lines[final_first_idx])
    stale_remaining = bool(STALE_MEANING_BLOCK_RE.search(final_text))
    block_remaining = bool(SECOND_PERSON_PRONOUN_RE.search(final_text) or BROKEN_GENERIC_PHRASE_RE.search(final_text) or BROKEN_CONNECTION_RE.search(final_text) or BROKEN_NOUN_PHRASE_RE.search(final_text) or MECHANICAL_META_RE.search(final_text) or INTERNAL_OBSERVATION_LANGUAGE_RE.search(final_text) or stale_remaining or midstream_remaining)
    repetition_remaining = sum(line.count("のですね") for line in final_lines) > 2 or _has_three_same_endings(final_lines)
    underanswered = _long_input_underanswered(final_lines, world_model)
    presence_missing = not any(PRESENCE_RE.search(line) for line in final_lines)
    passed = bool(final_text) and not block_remaining and not repetition_remaining and not underanswered and not presence_missing
    if stale_remaining:
        issues.append(FinalReviewIssue(code="stale_meaning_block_leak_remaining", severity="block", line_index=None, message="stale current-input leak remains"))
    if presence_missing:
        issues.append(FinalReviewIssue(code="presence_line_missing_remaining", severity="block", line_index=None, message="presence line missing"))
    if block_remaining:
        issues.append(FinalReviewIssue(code="final_block_issue_remaining", severity="block", line_index=None, message="unrepaired block issue remains"))
    if repetition_remaining:
        issues.append(FinalReviewIssue(code="sentence_ending_repetition_remaining", severity="block", line_index=None, message="ending repetition remains"))
    return FinalReviewResult(passed=passed, issues=issues, repaired_text=repaired_text, review_version="emlis.final_reader.v1")


__all__ = ["BROKEN_CONNECTION_RE", "PRESENCE_RE", "BROKEN_NOUN_PHRASE_RE", "INTERNAL_OBSERVATION_LANGUAGE_RE", "STALE_MEANING_BLOCK_RE", "SECOND_PERSON_PRONOUN_RE", "review_emlis_ai_reply_text"]
