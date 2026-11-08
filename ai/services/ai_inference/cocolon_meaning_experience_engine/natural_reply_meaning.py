"""Scoped reuse of source/evidence grammar for recipient replies.

This is not a general Japanese parser. Written cases and finite voice prove
only the declared roles; an omitted writer never becomes ``current_user``.
The caller owns source admission, Safety, access and the current source prefix.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from bisect import bisect_right
import hashlib
import json
import re

from emlis_ai_evidence_ledger_service import _split_source_text
from emlis_ai_grounded_observation_plan import _top_level_text
from .cores.analysis.intent_compiler import _FINITE_PREDICATES

SCHEMA = "cocolon.emlis.natural_meaning_comparison.v1"
SUPPORT_SCHEMA = "cocolon.emlis.source_role_support.v1"
REUSED_ASSETS = (
    "emlis_ai_evidence_ledger_service._split_source_text",
    "emlis_ai_grounded_observation_plan._top_level_text",
    "cocolon_meaning_experience_engine.cores.analysis.intent_compiler._FINITE_PREDICATES",
)
_SELF = frozenset(("私", "わたし", "僕", "ぼく", "俺", "おれ"))
_NOUN = r"[ぁ-ゖァ-ヺ一-鿿々A-Za-z0-9ー]{1,48}"
_SUBJECT = re.compile(r"(?P<noun>" + _NOUN + r"?)(?P<case>は|が)[、，, ]?")
_ARGUMENT = re.compile(r"(?P<noun>" + _NOUN + r"?)(?P<case>から|を|に|で|と)")
_DAY = re.compile(r"^(今日|昨日|明日|当時|その時|今回|以前|前回|翌日|前日|後日|先日|今朝|昨夜|今夜)(?:は|も)?[、，, ]*")
_ACK = re.compile(r"(?:のですね|んですね|のです|ということですね|ですね|ね)$")
_UNREAD = re.compile(r"[「」『』\"'（）()【】!?！？\n\r]|(?:かもしれ|らしい|そうです|はず|と思|と言|という|なら|もし|けれど|けど|のに|ので|からこそ|曰く|いわく|例えば|たとえば|例として|仮定)")
_SOURCE_UPDATE = re.compile(r"取り消|取消|撤回|訂正|ではなく|じゃなく|嘘|うそ|誤り|勘違い|間違|そう思っただけ|そうではない|なかったことに|違(?:う|った|います)|(?:事実|本当)(?:では|じゃ)ない")
_AMBIGUOUS_PASSIVE = frozenset(("教える", "助ける", "褒める", "伝える", "責める"))
_HARD_END = re.compile(r"[。.!！?？；;]")
_TEMPORAL_CASE = re.compile(r"^(?:今日|昨日|明日|今朝|今夜|昨夜|朝|昼|夜|夕方|当時|その時|午前|午後|先週|今週|来週|週末|平日|[月火水木金土日]曜日|[0-9〇零一二三四五六七八九十百千万]+(?:年|か月|ヶ月|月|週間|週|日|時間|時|分|秒)(?:前|後|間|頃|ごろ)?)$")


def _forms():
    # The existing complete-clause inflection inventory remains authoritative
    # for its nine verbs. Extra lexical verbs describe voice, not reply prose.
    rows = [(surface, lemma, polarity, modality, time, "active", False)
            for surface, lemma, polarity, modality, time in _FINITE_PREDICATES]
    for lemma, stem, group, canonical, receiving in (
        ("頼む", "頼", "m", "頼む", False),
        ("頼る", "頼", "r", "頼る", False),
        ("相談する", "相談", "suru", "相談する", False),
        ("教える", "教え", "vowel", "教える", False),
        ("教わる", "教わ", "r", "教える", True),
        ("貸す", "貸", "s", "貸す", False),
        ("借りる", "借り", "vowel", "貸す", True),
        ("助ける", "助け", "vowel", "助ける", False),
        ("手伝う", "手伝", "u", "手伝う", False),
        ("褒める", "褒め", "vowel", "褒める", False),
        ("ほめる", "ほめ", "vowel", "褒める", False),
        ("怒る", "怒", "r", "怒る", False),
        ("叱る", "叱", "r", "叱る", False),
        ("注意する", "注意", "suru", "注意する", False),
        ("責める", "責め", "vowel", "責める", False),
        ("伝える", "伝え", "vowel", "伝える", False),
    ):
        i, a, past = {"m": (stem + "み", stem + "ま", stem + "んだ"),
            "r": (stem + "り", stem + "ら", stem + "った"),
            "s": (stem + "し", stem + "さ", stem + "した"),
            "u": (stem + "い", stem + "わ", stem + "った"),
            "vowel": (stem, stem, stem + "た"),
            "suru": (stem + "し", stem + "し", stem + "した")}[group]
        for surface, polarity, time in ((past, "positive", "past"),
                (i + "ました", "positive", "past"),
                (a + "なかった", "negative", "past"),
                (i + "ませんでした", "negative", "past")):
            rows.append((surface, canonical, polarity, "fact", time, "active", receiving))
        if not receiving:
            passive = stem + "され" if group == "suru" else (stem + "られ" if group == "vowel" else a + "れ")
            for suffix, polarity in (("た", "positive"), ("ました", "positive"),
                                     ("なかった", "negative"), ("ませんでした", "negative")):
                rows.append((passive + suffix, canonical, polarity, "fact", "past", "passive", False))
    return tuple(sorted(set(rows), key=lambda row: (-len(row[0]), row)))


_FORMS = _forms()
_RELATIONAL_PREDICATES = frozenset(row[1] for row in _FORMS if row[5] == "passive")


@dataclass(frozen=True, slots=True)
class MeaningWitness:
    source_path: str
    source_group: str
    scalar_start: int
    scalar_end: int
    utf8_start: int
    utf8_end: int
    raw_text: str
    subject: str
    agent: str
    counterpart: str
    arguments: tuple[tuple[str, str], ...]
    predicate: str
    polarity: str
    modality: str
    temporal_scope: str
    relative_day: str
    voice: str
    recipient_acknowledgement: bool
    source_context_complete: bool = False


@dataclass(frozen=True, slots=True)
class MeaningCheck:
    reply_start: int
    reply_end: int
    source_path: str
    source_start: int
    source_end: int
    verdict: str
    assessed_axes: tuple[str, ...]
    reason_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MeaningComparison:
    schema_version: str
    source_prefix_ref: str
    material_sha256: str
    reply_sha256: str
    verdict: str
    source_witness_count: int
    reply_segment_count: int
    parsed_reply_count: int
    checked_reply_count: int
    unassessed_reply_count: int
    excluded_source_count: int
    full_reply_semantic_coverage: bool
    checks: tuple[MeaningCheck, ...]

    def as_private_dict(self):
        """No user prose or participant names are copied into the report."""
        return asdict(self)


def _participant(noun, *, reply):
    # Reflexive 自分 may be bound to a third party in either source or reply.
    # The finite reader has no discourse binder, so it cannot mean SELF here.
    if noun in {"自分", "自分自身", "自身", "ご自身"}:
        return "UNRESOLVED"
    if reply and noun == "あなた":
        return "SELF"
    if not reply and noun in _SELF:
        return "SELF"
    if reply and noun in _SELF | {"Emlis"}:
        return "ASSISTANT"
    if any(noun.endswith(token) for token in _SELF | {"あなた"}):
        return "UNRESOLVED"  # unparsed day/adverb + pronoun is not a name
    return "WRITTEN:" + re.sub(r"(?:さん|くん|ちゃん|様|氏)$", "", noun)


def _arguments(text):
    result, cursor = [], 0
    while cursor < len(text):
        match = _ARGUMENT.match(text, cursor)
        if match is None:
            return None
        noun = match["noun"]
        # Do not swallow an unparsed topic, dependent predicate, or case
        # particle into an invented noun. Unknown nominal grammar stays open.
        if re.search(r"[はがをにでとも]|(?:って|いて|した|ない|たい)$", noun):
            return None
        if match["case"] in {"に", "から"} and _TEMPORAL_CASE.fullmatch(noun):
            return None  # ni/kara can be a time adjunct, not a participant
        result.append((match["case"], noun))
        cursor = match.end()
    return tuple(result) if len({case for case, _ in result}) == len(result) else None


def _read_clause(raw, *, reply):
    if _top_level_text(raw) != raw:
        return None
    day = _DAY.match(raw)
    relative_day = day[1] if day else ""
    value = raw[day.end():] if day else raw
    acknowledgement = bool(reply and _ACK.search(value))
    if reply:
        value = _ACK.sub("", value)
    if _UNREAD.search(value):
        return None
    subjects = [(match["noun"], match.end()) for match in _SUBJECT.finditer(value)
                if match.start() == 0]
    # A simple omitted passive may prove its written ni-agent, but never
    # assigns an unstated experiencer to the writer.
    subjects.append(("", 0))
    readings = []
    for subject, start in subjects:
        if subject and re.search(r"[はがをにでとも]", subject) and subject not in _SELF | {"あなた", "ご自身"}:
            continue
        for finite, predicate, polarity, modality, time, voice, receiving in _FORMS:
            if not value.endswith(finite) or len(value) - len(finite) < start:
                continue
            arguments = _arguments(value[start:len(value) - len(finite)])
            if arguments is None:
                continue
            counterpart = next((noun for case, noun in arguments if case in {"に", "から"}), "")
            if sum(case in {"に", "から"} for case, _ in arguments) > 1:
                continue
            if not subject and (voice != "passive" or not counterpart):
                continue
            # Ichidan -rareru can also mean ability. A ni-case alone cannot
            # prove passive agency ("新人に教えられた" has two readings).
            if voice == "passive" and predicate in _AMBIGUOUS_PASSIVE and not any(case == "から" for case, _ in arguments):
                continue
            who = _participant(subject, reply=reply) if subject else "UNSTATED"
            other = _participant(counterpart, reply=reply) if counterpart else ""
            if "UNRESOLVED" in {who, other}:
                continue
            agent, target = (other, who) if voice == "passive" or receiving else (who, other)
            if voice == "passive" and not other:
                continue
            # The finite grammar proves case positions, not the semantic
            # role of arbitrary ni-cases on the old nine nonrelational verbs.
            relational = predicate in _RELATIONAL_PREDICATES
            if not relational:
                agent, target = who, ""
            remaining = tuple((case, noun) for case, noun in arguments
                              if not relational or case not in {"に", "から"})
            readings.append((who, agent, target, remaining, predicate, polarity,
                             modality, time, relative_day, voice, acknowledgement))
    unique = tuple(dict.fromkeys(readings))
    return unique[0] if len(unique) == 1 else None


def _clauses(text, path, group, *, reply=False):
    if not isinstance(text, str):
        raise ValueError("natural_meaning_material_invalid")
    # The old splitter supplies scalar coordinates; do not use its whitespace
    # normalized display text, truncate long fields, or inspect quoted text.
    visible = _top_level_text(text)
    rows = _split_source_text(text, max_len=max(1, len(text)))
    hard_ends = [0, *(match.end() for match in _HARD_END.finditer(text)), len(text)]
    witnesses = []
    for row in rows:
        raw = text[row.start:row.end]
        block_index = bisect_right(hard_ends, row.start) - 1
        block_start, block_end = hard_ends[block_index:block_index + 2]
        block = text[block_start:block_end]
        outside = text[block_start:row.start] + text[row.end:block_end]
        # Ledger newline boundaries locate text; they do not assert that a
        # finite stem before a newline is independent of a following hedge,
        # report, question or condition. Keep a connected multiline clause
        # unassessed instead of silently dropping its unparsed continuation.
        if ("\n" in block or "\r" in block) and outside.strip(" \t\r\n\u3000。.!！?？；;"):
            continue
        if visible is None or visible[row.start:row.end] != raw:
            continue
        if re.match(r"[!?！？]", text[row.end:]):
            continue
        reading = _read_clause(raw, reply=reply)
        if reading is not None:
            witnesses.append(MeaningWitness(path, group, row.start, row.end,
                len(text[:row.start].encode("utf-8")), len(text[:row.end].encode("utf-8")),
                raw, *reading))
    return tuple(replace(row, source_context_complete=len(witnesses) == len(rows))
                 for row in witnesses), len(rows)


def _source_witnesses(material):
    if type(material) is not dict or type(material.get("current")) is not dict:
        raise ValueError("natural_meaning_material_invalid")
    records = [("current", "CURRENT", material.get("current_input_id"),
                material["current"], material.get("current_answers", []))]
    histories = material.get("past_user_records", [])
    feedback = material.get("user_frame_feedback", [])
    if not isinstance(histories, list) or not isinstance(feedback, list):
        raise ValueError("natural_meaning_material_invalid")
    for index, item in enumerate(histories):
        if type(item) is not dict or type(item.get("original")) is not dict:
            raise ValueError("natural_meaning_material_invalid")
        records.append((f"past_user_records[{index}].original", "PAST", item.get("input_id"),
                        item["original"], item.get("answers", [])))
    if any(type(item) is not dict for item in feedback):
        raise ValueError("natural_meaning_material_invalid")
    changed = {item.get("input_id") for item in feedback
               if item.get("status") in {"REVISED", "REJECTED"}}
    witnesses, excluded = [], 0
    for path, group, identity, original, answers in records:
        if not isinstance(answers, list):
            raise ValueError("natural_meaning_material_invalid")
        # Reuse of standalone facts cannot decide the active target of an
        # answer/correction. Until that owner is connected, skip the record.
        texts = tuple(original.get(field) or "" for field in ("memo", "memo_action"))
        if any(not isinstance(text, str) for text in texts):
            raise ValueError("natural_meaning_material_invalid")
        if answers or identity in changed or any(_SOURCE_UPDATE.search(text) for text in texts):
            excluded += 1
            continue
        record_witnesses, context_complete = [], True
        for field in ("memo", "memo_action"):
            text = original.get(field, "")
            if text is None:
                text = ""
            rows, segment_count = _clauses(text, path + "." + field, group)
            record_witnesses.extend(rows)
            context_complete = context_complete and len(rows) == segment_count
        witnesses.extend(replace(row, source_context_complete=context_complete)
                         for row in record_witnesses)
    return tuple(witnesses), excluded


def prepare_meaning_support(material: dict) -> dict:
    """Private source snippets, never a model-written meaning certificate.

    Consume the *admitted* natural_reply material; this does not authenticate
    callers, determine entitlement, replace Safety, or parse AI questions.
    """
    witnesses, excluded = _source_witnesses(material)
    return {"schema_version": SUPPORT_SCHEMA, "reused_assets": list(REUSED_ASSETS),
            "witnesses": [asdict(row) for row in witnesses],
            "excluded_source_count": excluded,
            "coverage": "EXPLICIT_FINITE_ROLES_ONLY_NOT_GENERAL_SEMANTICS"}


def _event_key(witness):
    return witness.predicate, tuple(sorted(witness.arguments))


def _compatible_roles(source, reply):
    if not source.counterpart and not reply.counterpart:
        return source.agent == reply.agent
    source_people = {source.agent, source.counterpart} - {"", "UNSTATED"}
    reply_people = {reply.agent, reply.counterpart} - {"", "UNSTATED"}
    return bool(source_people and source_people <= reply_people)


def _compatible_event_scope(source, reply):
    # A past non-performance and a later wish can both be true. Neither the
    # same noun nor one matching source record proves they are one event.
    if source.modality != reply.modality or source.temporal_scope != reply.temporal_scope:
        return False
    if source.source_group == "PAST" and reply.relative_day:
        return False  # relative days have different record-time anchors
    if reply.relative_day and source.relative_day != reply.relative_day:
        return False
    return True


def compare_reply_meaning(material_json: str, reply_text: str, source_prefix_ref: str) -> MeaningComparison:
    """Read final free text independently and compare only unique witnesses.

    Unmatched prose and permitted omission never become semantic failure.
    Source/JSON/integrity errors deliberately propagate to their caller.
    """
    if not isinstance(material_json, str) or not isinstance(reply_text, str) or not isinstance(source_prefix_ref, str) or not source_prefix_ref:
        raise ValueError("natural_meaning_material_invalid")
    material = json.loads(material_json)
    sources, excluded = _source_witnesses(material)
    replies, segment_count = _clauses(reply_text, "reply", "REPLY", reply=True)
    checks = []
    for reply in replies:
        candidates = [source for source in sources if _event_key(source) == _event_key(reply)
                      and _compatible_roles(source, reply)
                      and _compatible_event_scope(source, reply)
                      and (reply.relative_day not in {"今回", "以前", "前回"}
                           or source.source_group == ("CURRENT" if reply.relative_day == "今回" else "PAST"))]
        if len(candidates) != 1:
            continue
        source = candidates[0]
        reasons = []
        if source.agent != reply.agent or (source.counterpart not in {"", "UNSTATED"}
                                           and reply.counterpart != source.counterpart):
            reasons.append("WRITTEN_PARTICIPANT_ROLES_REVERSED")
        if source.polarity != reply.polarity:
            reasons.append("POLARITY_CHANGED")
        if reasons and (not reply.recipient_acknowledgement or not source.source_context_complete):
            continue  # no scoped confirmation of this source event
        axes = ["predicate", "written_arguments", "polarity", "modality", "finite_tense"]
        if source.agent not in {"", "UNSTATED"}:
            axes.append("written_agent")
        if source.counterpart not in {"", "UNSTATED"}:
            axes.append("written_counterpart")
        checks.append(MeaningCheck(reply.scalar_start, reply.scalar_end, source.source_path,
            source.scalar_start, source.scalar_end,
            "CONFLICT" if reasons else "NO_CONFLICT_IN_CHECKED_SCOPE",
            tuple(axes),
            tuple(reasons)))
    verdict = ("CONFLICT" if any(row.verdict == "CONFLICT" for row in checks)
               else "NO_CONFLICT_IN_CHECKED_SCOPE" if checks else "UNASSESSED")
    return MeaningComparison(SCHEMA, source_prefix_ref,
        hashlib.sha256(material_json.encode("utf-8")).hexdigest(),
        hashlib.sha256(reply_text.encode("utf-8")).hexdigest(), verdict,
        len(sources), segment_count, len(replies), len(checks), segment_count - len(checks),
        excluded, False, tuple(checks))
