"""Finite source-only cognition scopes for the existing natural reply owner.

Adapted responsibility: retain the outer cognition and its embedded content
as separate source ranges, as the old current-cognition/temporal productions
do. Their old SELF default and intended_future mapping are not reused.

This is not an event extractor or a reply author. It does not decide who the
omitted knower is, whether the content later occurred, or whether another
source has corrected it. The admitted-record caller still owns those checks.
"""
from __future__ import annotations

import re


_RELATIVE_TIME = (
    r"(?:一昨日|昨日|今日|明日|明後日)"
    r"(?:の(?:朝|午前|昼|午後|夕方|夜))?"
)
_NOUN = r"[一-鿿々ァ-ヺA-Za-z0-9ー]{1,48}"
_NOUN_PHRASE = _NOUN + r"(?:の" + _NOUN + r"){0,2}"
# Closed productions only. An arbitrary string before ``と知った`` could
# itself be an unknown, another cognitive host, a wish, or a quotation.
_TIMED_PROPOSITION = (
    r"(?:(?:" + _NOUN_PHRASE + r"(?:が|で))?" + _NOUN + r"(?:する|しない)|"
    + _NOUN_PHRASE + r"が" + _NOUN_PHRASE + r"で(?:使えない|利用できない|通れない))"
)
_POSITIVE_AFTER_EVENT = (
    _NOUN_PHRASE + r"が(?:止まって|閉まって|終わって|始まって|" + _NOUN + r"して)"
)
_NOMINAL_CONTENT = r"(?:" + _NOUN_PHRASE + r"のための" + _NOUN_PHRASE + r"|" + _NOUN_PHRASE + r")"
_PRIOR_NOTICE = re.compile(
    r"(?P<knowledge_time>" + _RELATIVE_TIME + r")[、,]"
    r"(?P<content>(?P<content_time>" + _RELATIVE_TIME + r")(?:に|は)"
    + _TIMED_PROPOSITION + r")と(?P<cognition>知った)"
)
_AFTER_EVENT = re.compile(
    r"(?P<prior_event>(?P<event_time>" + _RELATIVE_TIME + r")(?:に|は)"
    + _POSITIVE_AFTER_EVENT + r")"
    r"(?P<after_link>から)[、,]"
    r"(?P<content>" + _NOMINAL_CONTENT + r"(?:だった|ではない|だ))と(?P<cognition>知った)"
)
# A closed matching span is not independent when its field explicitly opens
# quotation, speculation, an example, a condition, a report or a correction.
# Conservative exclusion is preferable to turning such material into a fact.
_UNQUALIFIED_CONTEXT = re.compile(
    r"[「」『』\"'（）()【】!?！？\r\n]"
    r"|もし|仮に|仮定|架空|例として|例えば|たとえば|という例|なら|たら|とすれば"
    r"|かもしれ|らしい|そうだ|そうです|ようだ|ようです|はず"
    r"|によると|によれば|曰く|いわく|と言|という|と話|って話|と聞|って聞"
    r"|と伝|と思|と考|つもり|したい|してほしい|願|望|祈|知りたい|知ら|分から|わから|不明|未定|未確定|不確か"
    r"|の話|の説明|の報告|取り消|取消|撤回|訂正|ではなく|じゃなく|嘘|うそ|誤り|勘違い|間違"
    r"|想像|空想|仮説|仮想|夢|例文|例話|真偽|事実か|本当か|未確認"
    r"|確かめていない|確かではない|確かでない|確かな記憶がない"
    r"|断定できない|断定しない|わけではない|確信がない|確信はない"
)
_DAY = re.compile(r"^(一昨日|昨日|今日|明日|明後日)")
_DAY_OFFSET = {"一昨日": -2, "昨日": -1, "今日": 0, "明日": 1, "明後日": 2}


def source_context_allows_finite_hints(*texts: str) -> bool:
    """Conservatively decline new hints when another field qualifies them."""
    if any(not isinstance(text, str) for text in texts):
        raise ValueError("natural_cognition_source_invalid")
    return not any(_UNQUALIFIED_CONTEXT.search(text) for text in texts)


def _part(source_text: str, start: int, end: int) -> dict:
    return {
        "raw_text": source_text[start:end],
        "scalar_start": start,
        "scalar_end": end,
        "utf8_start": len(source_text[:start].encode("utf-8")),
        "utf8_end": len(source_text[:end].encode("utf-8")),
    }


def read_cognition_clause(
    source_text: str,
    scalar_start: int,
    scalar_end: int,
    *,
    source_path: str,
    source_group: str = "CURRENT",
) -> dict | None:
    """Read one complete punctuation-free ledger span in an unchanged field.

    Supported shapes are a written relative-time knowledge host containing
    a timed nominal ``suru`` notice or a closed unavailability proposition,
    and a positive finite change followed by ``te-kara`` and nominal content.
    Positive past ``知った`` is required. This is not arbitrary complement
    parsing, and the event/availability inventories are deliberately finite.
    All returned offsets remain field-local, with exact original UTF-8 ranges.
    Unknown, wishes, nested attribution and unsupported prose return None.
    """
    if (
        not isinstance(source_text, str)
        or type(scalar_start) is not int
        or type(scalar_end) is not int
        or not 0 <= scalar_start < scalar_end <= len(source_text)
        or not isinstance(source_path, str)
        or not source_path
        or source_group not in {"CURRENT", "PAST"}
    ):
        raise ValueError("natural_cognition_source_invalid")
    if _UNQUALIFIED_CONTEXT.search(source_text):
        return None
    raw = source_text[scalar_start:scalar_end]
    # The caller may supply a ledger span; it may not carve a matching
    # substring out of a larger connected cognition/report/question clause.
    before = source_text[:scalar_start]
    after = source_text[scalar_end:]
    if before.strip() and not re.search(r"[。．.!！?？；;]\s*$", before):
        return None
    if after.strip() and not re.match(r"\s*[。．.!！?？；;]", after):
        return None
    match = _PRIOR_NOTICE.fullmatch(raw)
    kind = "TIMED_KNOWLEDGE_CONTENT"
    if match is None:
        match = _AFTER_EVENT.fullmatch(raw)
        kind = "KNOWLEDGE_AFTER_WRITTEN_EVENT"
    if match is None:
        return None

    def part(name: str):
        if name not in match.groupdict() or match[name] is None:
            return None
        start, end = match.span(name)
        return _part(source_text, scalar_start + start, scalar_start + end)

    knowledge_time = part("knowledge_time")
    content_time = part("content_time")
    day_order = None
    if knowledge_time is not None and content_time is not None:
        host_day = _DAY_OFFSET[_DAY.match(knowledge_time["raw_text"])[1]]
        content_day = _DAY_OFFSET[_DAY.match(content_time["raw_text"])[1]]
        day_order = (
            "KNOWLEDGE_BEFORE_CONTENT_DAY" if host_day < content_day else
            "SAME_WRITTEN_DAY" if host_day == content_day else
            "KNOWLEDGE_AFTER_CONTENT_DAY"
        )
    return {
        "kind": kind,
        "source_path": source_path,
        "source_group": source_group,
        "raw": _part(source_text, scalar_start, scalar_end),
        "cognitive_host": part("cognition"),
        "knowledge_holder": "UNSTATED",
        "knowledge_time": knowledge_time,
        "content": part("content"),
        "content_time": content_time,
        "prior_event": part("prior_event"),
        "prior_event_time": part("event_time"),
        "after_link": part("after_link"),
        "explicit_day_order": day_order,
        "content_status": "AS_WRITTEN_NOT_ASSERTED_AS_COMPLETED",
        "full_semantic_coverage": False,
    }
