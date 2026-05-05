# -*- coding: utf-8 -*-
from __future__ import annotations

"""Final reader review for EmlisAI replies.

This module reads the fully rendered reply before it is returned to the user.
It blocks broken template joins, repairs minor ending repetition, removes vague
history boilerplate, and guarantees a companion presence line when possible.
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
ABSTRACT_HISTORY_RE = re.compile(r"(最近の履歴の中でも、近いテーマ|最近の流れも踏まえて|今の気持ちを見ます|近いテーマがまた顔を出して)")
PRESENCE_RE = re.compile(r"(軽く扱いません|雑に扱いません|小さく扱いません|そのまま置いて大丈夫|きれいにしなくて大丈夫|そばに置いて|大切にします|大切に扱います)")
BROKEN_NOUN_PHRASE_RE = re.compile(
    r"(だ|だから|けど|けれど|から)(気持ち|思い|願い|状態)"
    r"|中途半端だ気持ち|中途半端だから気持ち|好きになれないけど気持ち"
    r"|諦めたくないけれど気持ち|期待して裏切られたくないから気持ち"
)


def _lines(text: Any) -> List[str]:
    return [line.strip() for line in str(text or "").splitlines() if line.strip()]


def _presence_line(world_model: Optional[WorldModel]) -> str:
    selected = " ".join(str(getattr(item, "type", "") or "") for item in list(getattr(getattr(world_model, "facts", None), "selected_emotions", []) or [])) if world_model is not None else ""
    roles = {str(getattr(item, "role", "") or "") for item in list(getattr(getattr(world_model, "facts", None), "shaped_user_phrases", []) or [])} if world_model is not None else set()
    if {"other_contribution", "own_happiness_wish", "present_effort_toward_wish"} & roles:
        return "ここでは、誰かの幸せを願う気持ちも、自分の幸せを諦めたくない気持ちも、どちらも小さく扱いません。"
    if {"work_frustration", "anger_surface", "chat_relief"} & roles:
        return "ここでは、悔しさも、むかつきも、癒されたい気持ちも、雑に扱いません。"
    if "怒り" in selected and "悲しみ" in selected:
        return "ここでは、悲しみも怒りも、無理にきれいにしなくて大丈夫です。"
    return "ここに置いてくれた言葉を、Emlisは軽く扱いません。"


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
    previous_group = ""
    for line in lines:
        cur = line
        group = _ending_group(cur)
        if group == "ne_desu":
            ne_count += 1
            if previous_group == "ne_desu" or ne_count > 2:
                if "癒し" in cur:
                    cur = re.sub(r"になっていたのですね。?$", "になっていたのだと思います。", cur)
                elif "重なって" in cur or "同じ場所" in cur:
                    cur = re.sub(r"のですね。?$", "いました。", cur)
                elif "気持ち" in cur or "しんど" in cur:
                    cur = re.sub(r"のですね。?$", "のだと思います。", cur)
                else:
                    cur = re.sub(r"のですね。?$", "のだと思います。", cur)
                group = _ending_group(cur)
        repaired.append(cur)
        previous_group = group
    return repaired


def _has_three_same_endings(lines: List[str]) -> bool:
    groups = [_ending_group(line) for line in lines]
    for a, b, c in zip(groups, groups[1:], groups[2:]):
        if a == b == c and a != "other":
            return True
    return False


def review_emlis_ai_reply_text(*, comment_text: Any, world_model: Optional[WorldModel] = None) -> FinalReviewResult:
    issues: List[FinalReviewIssue] = []
    lines = _lines(comment_text)
    repaired_lines: List[str] = []
    changed = False

    for idx, line in enumerate(lines):
        if BROKEN_CONNECTION_RE.search(line):
            issues.append(FinalReviewIssue(code="raw_anchor_broken_connection", severity="block", line_index=idx, message=line))
            changed = True
            continue
        if BROKEN_NOUN_PHRASE_RE.search(line):
            issues.append(FinalReviewIssue(code="broken_noun_phrase", severity="block", line_index=idx, message=line))
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
        repaired_lines.append(line)

    if not repaired_lines and lines:
        repaired_lines = []

    original_ne_count = sum(line.count("のですね") for line in repaired_lines)
    repaired_lines = _repair_ending_repetition(repaired_lines)
    if original_ne_count > 2 or _has_three_same_endings(repaired_lines):
        issues.append(FinalReviewIssue(code="sentence_ending_repetition", severity="repair", line_index=None, message="のですね repetition repaired"))
        changed = True

    if not any(PRESENCE_RE.search(line) for line in repaired_lines):
        issues.append(FinalReviewIssue(code="presence_line_missing", severity="repair", line_index=None, message="presence line added"))
        repaired_lines.append(_presence_line(world_model))
        changed = True

    coverage = getattr(getattr(world_model, "facts", None), "meaning_coverage_plan", None) if world_model is not None else None
    retention = getattr(getattr(world_model, "facts", None), "major_meaning_retention_plan", None) if world_model is not None else None
    if coverage is not None and bool(getattr(coverage, "clear_long_input", False)):
        min_blocks = int(getattr(coverage, "min_blocks_to_cover", 0) or 0)
        if retention is not None and getattr(retention, "must_keep_block_keys", None):
            min_blocks = max(min_blocks, min(7, len(getattr(retention, "must_keep_block_keys", []) or [])))
        if len(repaired_lines) < max(5, min_blocks + 1):
            issues.append(FinalReviewIssue(code="long_input_underanswered", severity="block", line_index=None, message="clear long input reply is too short"))

    repaired_text = "\n".join(repaired_lines).strip() if changed else None
    final_text = repaired_text if repaired_text is not None else "\n".join(lines).strip()
    block_remaining = bool(BROKEN_CONNECTION_RE.search(final_text) or BROKEN_NOUN_PHRASE_RE.search(final_text) or MECHANICAL_META_RE.search(final_text))
    repetition_remaining = sum(line.count("のですね") for line in _lines(final_text)) > 2 or _has_three_same_endings(_lines(final_text))
    long_input_underanswered = any(issue.code == "long_input_underanswered" for issue in issues)
    passed = bool(final_text) and not block_remaining and not repetition_remaining and not long_input_underanswered and any(PRESENCE_RE.search(line) for line in _lines(final_text))
    if block_remaining:
        issues.append(FinalReviewIssue(code="final_block_issue_remaining", severity="block", line_index=None, message="unrepaired block issue remains"))
    if repetition_remaining:
        issues.append(FinalReviewIssue(code="sentence_ending_repetition_remaining", severity="block", line_index=None, message="ending repetition remains"))
    return FinalReviewResult(
        passed=passed,
        issues=issues,
        repaired_text=repaired_text,
        review_version="emlis.final_reader.v1",
    )


__all__ = ["BROKEN_CONNECTION_RE", "PRESENCE_RE", "BROKEN_NOUN_PHRASE_RE", "review_emlis_ai_reply_text"]
