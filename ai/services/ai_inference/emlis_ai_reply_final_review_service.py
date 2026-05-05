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
ABSTRACT_HISTORY_RE = re.compile(r"(最近の履歴の中でも、近いテーマ|最近の流れも踏まえて|今の気持ちを見ます|近いテーマがまた顔を出して)")
PRESENCE_RE = re.compile(r"(軽く扱いません|雑に扱いません|小さく扱いません|そのまま置いて大丈夫|きれいにしなくて大丈夫|そばに置いて|大切にします|大切に扱います)")
BROKEN_NOUN_PHRASE_RE = re.compile(r"(だ|だから|けど|けれど|から)(気持ち|思い|願い|状態)")
MIDSTREAM_OPENING_RE = re.compile(r"^(ただ同時に|でも同時に|それでも|だから|だからこそ|そのため|一方で|ただ)[、,]")


def _lines(text: Any) -> List[str]:
    return [line.strip() for line in str(text or "").splitlines() if line.strip()]


def _presence_line(world_model: Optional[WorldModel]) -> str:
    roles = {str(getattr(item, "role", "") or "") for item in list(getattr(getattr(world_model, "facts", None), "meaning_blocks", []) or [])} if world_model is not None else set()
    if {"self_suppression", "self_protection", "support_need", "burden_avoidance"} & roles:
        return "ここでは、抑えてきた気持ちも、自分を守ろうとしている気持ちも、どちらも大切に扱います。"
    if {"wish_or_hope", "fear_or_disappointment", "effort_direction"} & roles:
        return "ここでは、願いも怖さも、今できることを大切にしたい気持ちも、小さく扱いません。"
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
                cur = re.sub(r"のですね。?$", "のだと思います。", cur)
                group = _ending_group(cur)
        repaired.append(cur)
        previous_group = group
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


def _long_input_underanswered(lines: List[str], world_model: Optional[WorldModel]) -> bool:
    coverage = getattr(getattr(world_model, "facts", None), "meaning_coverage_plan", None) if world_model is not None else None
    blocks = list(getattr(getattr(world_model, "facts", None), "meaning_blocks", []) or []) if world_model is not None else []
    if coverage is None or not bool(getattr(coverage, "clear_long_input", False)):
        return False
    min_blocks = int(getattr(coverage, "min_blocks_to_cover", 0) or 0)
    if len(lines) < max(5, min_blocks + 1):
        return True
    text = "\n".join(lines)
    required = min(max(3, min_blocks), len(blocks)) if blocks else 0
    if required <= 0:
        return False
    covered = sum(1 for block in blocks if _summary_covered(text, str(getattr(block, "summary", "") or "")))
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

    original_ne_count = sum(line.count("のですね") for line in repaired_lines)
    repaired_lines = _repair_ending_repetition(repaired_lines)
    if original_ne_count > 2 or _has_three_same_endings(repaired_lines):
        issues.append(FinalReviewIssue(code="sentence_ending_repetition", severity="repair", line_index=None, message="ending repetition repaired"))
        changed = True

    if not any(PRESENCE_RE.search(line) for line in repaired_lines):
        issues.append(FinalReviewIssue(code="presence_line_missing", severity="repair", line_index=None, message="presence line added"))
        repaired_lines.append(_presence_line(world_model))
        changed = True

    if _long_input_underanswered(repaired_lines, world_model):
        issues.append(FinalReviewIssue(code="long_input_underanswered", severity="block", line_index=None, message="clear long input reply is too short"))

    repaired_text = "\n".join(repaired_lines).strip() if changed else None
    final_text = repaired_text if repaired_text is not None else "\n".join(lines).strip()
    final_lines = _lines(final_text)
    final_first_idx = _first_content_index(final_lines)
    midstream_remaining = final_first_idx is not None and MIDSTREAM_OPENING_RE.search(final_lines[final_first_idx])
    block_remaining = bool(BROKEN_CONNECTION_RE.search(final_text) or BROKEN_NOUN_PHRASE_RE.search(final_text) or MECHANICAL_META_RE.search(final_text) or midstream_remaining)
    repetition_remaining = sum(line.count("のですね") for line in final_lines) > 2 or _has_three_same_endings(final_lines)
    underanswered = _long_input_underanswered(final_lines, world_model)
    passed = bool(final_text) and not block_remaining and not repetition_remaining and not underanswered and any(PRESENCE_RE.search(line) for line in final_lines)
    if block_remaining:
        issues.append(FinalReviewIssue(code="final_block_issue_remaining", severity="block", line_index=None, message="unrepaired block issue remains"))
    if repetition_remaining:
        issues.append(FinalReviewIssue(code="sentence_ending_repetition_remaining", severity="block", line_index=None, message="ending repetition remains"))
    return FinalReviewResult(passed=passed, issues=issues, repaired_text=repaired_text, review_version="emlis.final_reader.v1")


__all__ = ["BROKEN_CONNECTION_RE", "PRESENCE_RE", "BROKEN_NOUN_PHRASE_RE", "review_emlis_ai_reply_text"]
