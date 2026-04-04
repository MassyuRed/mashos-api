# -*- coding: utf-8 -*-
"""generated_reflection_display.py

Deterministic public-display builder for Premium generated reflections.

Goals
-----
- keep generated/raw answer text intact in storage
- build a stronger public-facing answer for generated reflections
- make broken diary fragments look like answers to the question when possible
- reuse the existing public safety formatter for masking / blocking
- provide a stable normalized hash for same-as-active duplicate suppression

This module is intentionally deterministic and rule-based.
It does not call any external model.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import re
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from reflection_text_formatter import (
    STATE_BLOCKED,
    STATE_MASKED,
    STATE_READY,
    format_reflection_text,
)

GENERATED_REFLECTION_DISPLAY_VERSION = "reflection.generated.display.v3"

_ZERO_WIDTH_RE = re.compile(r"[\u200B-\u200D\uFEFF]")
_WS_RE = re.compile(r"\s+")
_SENTENCE_SPLIT_RE = re.compile(r"[。！？!?\n]+|\s*[、,/／]\s*")
_BAD_TAIL_RE = re.compile(r"(?:けど.*|けれど.*|から.*|ので.*|のに.*)$")
_SHORT_PARTICLE_TAIL_RE = re.compile(r"(?:のは|だけ|とか|って感じ|みたい|ことや)$")

_BAD_EXACTS = {
    "お話",
    "コメント",
    "まだコメントという形だけ",
    "まず一番大事なのは",
    "一番大事なのは",
}

_BAD_CORE_PATTERNS: Sequence[re.Pattern[str]] = (
    re.compile(r"^(?:今まで|今の|さっきまで)?私(?:は|が)?$"),
    re.compile(r"^(?:自分|私自身)(?:は|が)?$"),
    re.compile(r"^(?:不器用だ|最悪なんだ|疲れた|減ったのは|娯楽の排除|自身への無価値観|10)$"),
)
_GENERIC_FALLBACK_RE = re.compile(r"まだうまく言葉にしきれていません")
_PAST_EVENT_TAIL_RE = re.compile(r"(?:た|だった|してた|していた|ていた|なった)$")
_EVENT_TIME_MARKERS: Sequence[str] = (
    "今日",
    "昨日",
    "今朝",
    "今夜",
    "明日",
    "本日",
    "さっき",
    "さっきまで",
    "久々",
    "久しぶり",
)
_STABLE_CORE_HINTS: Sequence[str] = (
    "こと",
    "時間",
    "関係",
    "交流",
    "会話",
    "配信",
    "写真",
    "料理",
    "歌う",
    "休む",
    "整える",
    "振り返る",
    "続ける",
    "増やす",
    "広げる",
    "自分を知",
    "挑戦",
    "練習",
    "安心",
    "体調",
    "ペース",
)
_HEAD_CORE_PATTERNS: Sequence[re.Pattern[str]] = (
    re.compile(r"^人との関わりでは、(?P<core>.+?)を大切にしたいです(?:。|$)"),
    re.compile(r"^大切にしているのは、(?P<core>.+?)です(?:。|$)"),
    re.compile(r"^少しずつ伸ばしたいのは、(?P<core>.+?)です(?:。|$)"),
    re.compile(r"^最近夢中なのは、(?P<core>.+?)です(?:。|$)"),
    re.compile(r"^最近気になっているのは、(?P<core>.+?)です(?:。|$)"),
    re.compile(r"^しんどい時は、(?P<core>.+?)気持ちを整えています(?:。|$)"),
)

_PREFIX_FILLERS: Sequence[str] = (
    "でも",
    "ただ",
    "あと",
    "それで",
    "そして",
    "今日は",
    "最近は",
    "最近",
    "今は",
    "まだ",
    "ちょっと",
    "やたら",
    "まず",
    "少し",
    "その",
    "この",
    "は",
)


def _ordered_unique(values: Iterable[str]) -> List[str]:
    out: List[str] = []
    seen = set()
    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out



def _append_once(values: List[str], value: str) -> None:
    text = str(value or "").strip()
    if text and text not in values:
        values.append(text)



def _collapse_ws(text: Any) -> str:
    s = str(text or "")
    s = _ZERO_WIDTH_RE.sub("", s)
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = _WS_RE.sub(" ", s).strip()
    return s



def _normalize_for_hash(text: Any) -> str:
    s = _collapse_ws(text).lower()
    s = re.sub(r"[。．\.、,！!？?]+", "", s)
    return s



def compute_generated_answer_norm_hash(text: Any) -> str:
    normalized = _normalize_for_hash(text)
    if not normalized:
        return ""
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()



def compute_generated_display_source_signature(
    *,
    question: Any,
    raw_answer: Any,
    category: Any = None,
    focus_key: Any = None,
    topic_summary_text: Any = None,
    text_candidates: Optional[Sequence[Any]] = None,
) -> str:
    payload = {
        "question": _collapse_ws(question),
        "raw_answer": _collapse_ws(raw_answer),
        "category": _collapse_ws(category),
        "focus_key": _collapse_ws(focus_key),
        "topic_summary_text": _collapse_ws(topic_summary_text),
        "text_candidates": _ordered_unique([_collapse_ws(x) for x in (text_candidates or []) if _collapse_ws(x)]),
    }
    if not any(payload.values()):
        return ""
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()



def _parse_iso(value: Any) -> Optional[datetime]:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return None



def _parse_mapping(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
            if isinstance(parsed, dict):
                return dict(parsed)
        except Exception:
            return {}
    return {}



def _ensure_sentence(text: str) -> str:
    s = _collapse_ws(text)
    if not s:
        return ""
    if s.endswith(("。", "！", "？", "!", "?")):
        return s
    return s + "。"



def _split_fragments(*texts: Any) -> List[str]:
    out: List[str] = []
    for text in texts:
        raw = _collapse_ws(text)
        if not raw:
            continue
        for part in _SENTENCE_SPLIT_RE.split(raw):
            s = _collapse_ws(part).strip(" ・")
            if s:
                out.append(s)
    return _ordered_unique(out)



def _strip_prefix_fillers(text: str) -> str:
    s = _collapse_ws(text)
    changed = True
    while changed and s:
        changed = False
        for prefix in _PREFIX_FILLERS:
            if prefix == "少し" and s.startswith("少しずつ"):
                continue
            if s.startswith(prefix) and len(s) > len(prefix) + 1:
                s = s[len(prefix) :].lstrip(" ・")
                changed = True
    return s



def _normalize_phrase(text: str) -> str:
    s = _strip_prefix_fillers(text)
    s = _BAD_TAIL_RE.sub("", s).strip(" ・")
    s = re.sub(r"(?:かな|かも)$", "", s).strip(" ・")
    return s



def _is_low_quality_core_phrase(text: str) -> bool:
    s = _normalize_phrase(text)
    if not s:
        return True
    lowered = s.rstrip("。！？!? ")
    compact = lowered.replace(" ", "")
    if len(compact) < 4:
        return True
    if lowered in _BAD_EXACTS:
        return True
    if _SHORT_PARTICLE_TAIL_RE.search(lowered):
        return True
    if _BAD_TAIL_RE.search(lowered):
        return True
    if any(pattern.fullmatch(compact) for pattern in _BAD_CORE_PATTERNS):
        return True
    if compact.endswith(("だけ", "のは", "ことや", "って感じ", "みたい")):
        return True
    if re.fullmatch(r"(?:今まで|今の|さっきまで)?私(?:は|が)?です?", compact):
        return True
    if re.fullmatch(r"(?:自分|私自身)(?:は|が)?です?", compact):
        return True
    if compact.endswith(("だ", "です")) and len(compact) <= 10:
        return True
    return False



def _looks_like_oneoff_event_fragment(text: str) -> bool:
    s = _normalize_phrase(text)
    if not s:
        return True
    lowered = s.rstrip("。！？!? ")
    compact = lowered.replace(" ", "")
    if not compact:
        return True
    if _contains_any(compact, _EVENT_TIME_MARKERS) and _PAST_EVENT_TAIL_RE.search(compact):
        return True
    if _PAST_EVENT_TAIL_RE.search(compact) and not _contains_any(compact, _STABLE_CORE_HINTS):
        return True
    return False



def _extract_head_core_phrase(text: str) -> str:
    s = _collapse_ws(text)
    if not s:
        return ""
    for pattern in _HEAD_CORE_PATTERNS:
        match = pattern.match(s)
        if not match:
            continue
        core = _collapse_ws(match.group("core")).rstrip("。")
        if core.endswith("ことで"):
            core = core[:-3]
        return core.rstrip("。")
    return ""



def _contains_any(text: str, keywords: Sequence[str]) -> bool:
    return any(k and k in text for k in (keywords or []))



def _contains_all(text: str, keywords: Sequence[str]) -> bool:
    return all(k and k in text for k in (keywords or []))



def _compact_text(text: Any) -> str:
    return _collapse_ws(text).replace(" ", "")



@dataclass(frozen=True)
class GeneratedQuestionSpec:
    question_family: str
    canonical_prompt: str
    head_prefix: str
    head_suffix: str
    allowed_head_prefixes: Tuple[str, ...]
    forbidden_head_prefixes: Tuple[str, ...]
    require_method_like: bool = False
    require_time_like: bool = False
    require_value_like: bool = False
    require_concern_like: bool = False
    require_notice_like: bool = False



@dataclass(frozen=True)
class GeneratedAnswerEvidence:
    text: str
    score: int
    role: str  # core | support
    reasons: Tuple[str, ...]



@dataclass(frozen=True)
class GeneratedAnswerPlan:
    spec: GeneratedQuestionSpec
    answerable: bool
    block_reason: str
    core_theme: str
    support_theme: str
    temporal_scope: str
    source_quality: str
    evidence: Tuple[GeneratedAnswerEvidence, ...]

    def as_meta(self) -> Dict[str, Any]:
        return {
            "question_family": str(self.spec.question_family),
            "canonical_prompt": str(self.spec.canonical_prompt),
            "core_theme": str(self.core_theme),
            "support_theme": str(self.support_theme),
            "temporal_scope": str(self.temporal_scope),
            "source_quality": str(self.source_quality),
            "block_reason": str(self.block_reason),
            "answerable": bool(self.answerable),
            "evidence": [
                {
                    "text": str(item.text),
                    "score": int(item.score),
                    "role": str(item.role),
                    "reasons": list(item.reasons),
                }
                for item in (self.evidence or ())
            ],
        }



@dataclass(frozen=True)
class GeneratedAnswerValidationResult:
    answer_display_text: Optional[str]
    answer_display_state: str
    flags: List[str]
    actions: List[str]
    rewrite_needed: bool



_METHOD_LIKE_HINTS: Sequence[str] = (
    "休む",
    "整える",
    "整えて",
    "落ち着",
    "大事にして",
    "大切にして",
    "話して",
    "話す",
    "食生活",
    "寝る",
    "休みながら",
)
_TIME_LIKE_HINTS: Sequence[str] = (
    "時間",
    "とき",
    "時",
    "夜",
    "夜中",
    "寝る前",
    "朝",
    "ASMR",
    "音",
    "LINE",
)
_VALUE_LIKE_HINTS: Sequence[str] = (
    "大切",
    "大事",
    "振り返",
    "整える",
    "守",
    "続け",
    "自分を知",
)
_OPERATIONAL_MARKERS: Sequence[str] = (
    "不具合",
    "エラー",
    "SQL",
    "Render",
    "デプロイ",
    "アプリ",
)
_RELATIONSHIP_KEYS: Sequence[str] = (
    "関わ",
    "交流",
    "会話",
    "コメント",
    "話",
    "連絡",
    "一緒",
)
_STRESS_KEYS: Sequence[str] = (
    "休",
    "整",
    "寝",
    "落ち着",
    "薬",
    "だる",
    "疲",
    "体調",
)
_HEALTH_KEYS: Sequence[str] = (
    "耳",
    "難聴",
    "体調",
    "薬",
    "休",
    "寝",
    "だる",
    "疲",
    "焦",
)
_FAMILY_KEYWORDS: Dict[str, Tuple[str, ...]] = {
    "relationship_value": ("関わ", "交流", "会話", "コメント", "話", "安心", "連絡"),
    "value_general": ("大切", "整", "振り返", "守", "自分を知", "体調"),
    "work_value": ("仕事", "働", "体調", "整", "振り返", "ミス", "焦"),
    "growth_general": ("伸ば", "挑戦", "練習", "少しずつ", "整える", "踏み出"),
    "work_growth": ("仕事", "働", "出勤", "続け", "ミス", "効率", "安定", "頑張"),
    "work_concern": ("仕事", "ミス", "反省", "振り返", "負担", "迷惑", "焦", "スピード", "体力"),
    "notice_general": ("気づ", "分か", "見えてき", "感じ", "焦", "余裕"),
    "concern_general": ("気にな", "引っかか", "焦", "余裕", "やってみたい"),
    "fun_general": ("楽しい", "夢中", "配信", "話", "コメント", "歌", "写真", "料理", "服"),
    "fun_recent": ("楽しい", "楽しみ", "配信", "話", "歌", "写真", "料理", "服"),
    "stress_method": ("休", "整", "落ち着", "話", "食生活", "薬", "寝", "ペース"),
    "stress_time": ("時間", "とき", "時", "夜", "夜中", "寝る前", "ASMR", "音", "LINE", "話"),
    "work_stress_method": ("仕事", "しんど", "休", "整", "落ち着", "ペース"),
}



def _derive_question_spec(*, question: Any, focus_key: Any) -> GeneratedQuestionSpec:
    q = _collapse_ws(question)
    compact = _compact_text(q)
    fk = str(focus_key or "").strip().lower()

    if "人との関わりで大切なこと" in compact:
        return GeneratedQuestionSpec(
            question_family="relationship_value",
            canonical_prompt=q or "人との関わりで大切なことは？",
            head_prefix="人との関わりでは、",
            head_suffix="を大切にしたいです",
            allowed_head_prefixes=("人との関わりでは、",),
            forbidden_head_prefixes=("最近気づいたのは、", "最近気になっているのは、"),
            require_value_like=True,
        )
    if "仕事で大切にしていること" in compact:
        return GeneratedQuestionSpec(
            question_family="work_value",
            canonical_prompt=q or "仕事で大切にしていることは？",
            head_prefix="仕事では、",
            head_suffix="を大切にしています",
            allowed_head_prefixes=("仕事では、",),
            forbidden_head_prefixes=("大切にしているのは、", "最近気になっているのは、"),
            require_value_like=True,
        )
    if "仕事で気にしていること" in compact:
        return GeneratedQuestionSpec(
            question_family="work_concern",
            canonical_prompt=q or "仕事で気にしていることは？",
            head_prefix="仕事では、",
            head_suffix="を気にしています",
            allowed_head_prefixes=("仕事では、",),
            forbidden_head_prefixes=("最近気づいたのは、", "最近気になっているのは、"),
            require_concern_like=True,
        )
    if "仕事で伸ばしたいこと" in compact:
        return GeneratedQuestionSpec(
            question_family="work_growth",
            canonical_prompt=q or "仕事で伸ばしたいことは？",
            head_prefix="仕事で伸ばしたいのは、",
            head_suffix="です",
            allowed_head_prefixes=("仕事で伸ばしたいのは、",),
            forbidden_head_prefixes=("少しずつ伸ばしたいのは、",),
        )
    if "仕事でしんどい時の整え方" in compact:
        return GeneratedQuestionSpec(
            question_family="work_stress_method",
            canonical_prompt=q or "仕事でしんどい時の整え方は？",
            head_prefix="仕事でしんどい時は、",
            head_suffix="で気持ちを整えています",
            allowed_head_prefixes=("仕事でしんどい時は、",),
            forbidden_head_prefixes=("心と体を整えるために、", "気持ちを整えるために、", "心が休まるのは、"),
            require_method_like=True,
        )
    if "心がほどける時間" in compact:
        return GeneratedQuestionSpec(
            question_family="stress_time",
            canonical_prompt=q or "心がほどける時間は？",
            head_prefix="心がほどけるのは、",
            head_suffix="です",
            allowed_head_prefixes=("心がほどけるのは、",),
            forbidden_head_prefixes=("しんどい時は、", "心と体を整えるために、", "気持ちを整えるために、"),
            require_time_like=True,
        )
    if "心が休まる時間" in compact:
        return GeneratedQuestionSpec(
            question_family="stress_time",
            canonical_prompt=q or "心が休まる時間は？",
            head_prefix="心が休まるのは、",
            head_suffix="です",
            allowed_head_prefixes=("心が休まるのは、",),
            forbidden_head_prefixes=("しんどい時は、", "心と体を整えるために、", "気持ちを整えるために、"),
            require_time_like=True,
        )
    if "心と体を整える方法" in compact:
        return GeneratedQuestionSpec(
            question_family="stress_method",
            canonical_prompt=q or "心と体を整える方法は？",
            head_prefix="心と体を整えるために、",
            head_suffix="を大事にしています",
            allowed_head_prefixes=("心と体を整えるために、",),
            forbidden_head_prefixes=("しんどい時は、", "心が休まるのは、", "心がほどけるのは、"),
            require_method_like=True,
        )
    if "気持ちを整える方法" in compact:
        return GeneratedQuestionSpec(
            question_family="stress_method",
            canonical_prompt=q or "気持ちを整える方法は？",
            head_prefix="気持ちを整えるために、",
            head_suffix="を大事にしています",
            allowed_head_prefixes=("気持ちを整えるために、",),
            forbidden_head_prefixes=("しんどい時は、", "心が休まるのは、", "心がほどけるのは、"),
            require_method_like=True,
        )
    if "最近気づいたこと" in compact:
        return GeneratedQuestionSpec(
            question_family="notice_general",
            canonical_prompt=q or "最近気づいたことは？",
            head_prefix="最近気づいたのは、",
            head_suffix="です",
            allowed_head_prefixes=("最近気づいたのは、",),
            forbidden_head_prefixes=("最近気になっているのは、",),
            require_notice_like=True,
        )
    if "最近気になること" in compact:
        return GeneratedQuestionSpec(
            question_family="concern_general",
            canonical_prompt=q or "最近気になることは？",
            head_prefix="最近気になっているのは、",
            head_suffix="です",
            allowed_head_prefixes=("最近気になっているのは、",),
            forbidden_head_prefixes=("最近気づいたのは、",),
            require_concern_like=True,
        )
    if "最近夢中なこと" in compact:
        return GeneratedQuestionSpec(
            question_family="fun_general",
            canonical_prompt=q or "最近夢中なことは？",
            head_prefix="最近夢中なのは、",
            head_suffix="です",
            allowed_head_prefixes=("最近夢中なのは、",),
            forbidden_head_prefixes=("最近の楽しみは、",),
        )
    if "最近の楽しみ" in compact:
        return GeneratedQuestionSpec(
            question_family="fun_recent",
            canonical_prompt=q or "最近の楽しみは？",
            head_prefix="最近の楽しみは、",
            head_suffix="です",
            allowed_head_prefixes=("最近の楽しみは、",),
            forbidden_head_prefixes=("最近夢中なのは、",),
        )
    if "伸ばしたいこと" in compact:
        return GeneratedQuestionSpec(
            question_family="growth_general",
            canonical_prompt=q or "伸ばしたいことは？",
            head_prefix="少しずつ伸ばしたいのは、",
            head_suffix="です",
            allowed_head_prefixes=("少しずつ伸ばしたいのは、",),
            forbidden_head_prefixes=("最近気づいたのは、", "最近気になっているのは、"),
        )
    if "大切にしていること" in compact or fk == "values":
        return GeneratedQuestionSpec(
            question_family="value_general",
            canonical_prompt=q or "大切にしていることは？",
            head_prefix="大切にしているのは、",
            head_suffix="です",
            allowed_head_prefixes=("大切にしているのは、",),
            forbidden_head_prefixes=("最近気づいたのは、", "最近気になっているのは、"),
            require_value_like=True,
        )
    return GeneratedQuestionSpec(
        question_family="concern_general",
        canonical_prompt=q or "最近気になることは？",
        head_prefix="最近気になっているのは、",
        head_suffix="です",
        allowed_head_prefixes=("最近気になっているのは、",),
        forbidden_head_prefixes=("最近気づいたのは、",),
        require_concern_like=True,
    )



def _collect_source_fragments(*, raw_answer: str, topic_summary_text: str, text_candidates: Sequence[str]) -> List[str]:
    return _ordered_unique(_split_fragments(topic_summary_text, raw_answer, *list(text_candidates or [])))



def _score_fragment_for_spec(spec: GeneratedQuestionSpec, fragment: str) -> Tuple[int, Tuple[str, ...]]:
    s = _normalize_phrase(fragment)
    compact = _compact_text(s)
    reasons: List[str] = []
    score = 0
    if not compact:
        return -10, tuple(reasons)
    if 4 <= len(compact) <= 32:
        score += 1
        _append_once(reasons, "length:reasonable")
    family_keys = _FAMILY_KEYWORDS.get(spec.question_family, ())
    if _contains_any(compact, family_keys):
        score += 3
        _append_once(reasons, "family:keyword_match")
    if _contains_any(compact, _STABLE_CORE_HINTS):
        score += 2
        _append_once(reasons, "shape:stable_hint")
    if _looks_like_oneoff_event_fragment(compact):
        score -= 4
        _append_once(reasons, "quality:oneoff_event")
    if _contains_any(compact, _OPERATIONAL_MARKERS):
        score -= 4
        _append_once(reasons, "quality:operational")
    if _is_low_quality_core_phrase(compact):
        score -= 4
        _append_once(reasons, "quality:low_core")
    return score, tuple(reasons)



def _nominalize_phrase(text: str) -> str:
    s = _normalize_phrase(text)
    if not s:
        return ""

    replacements = (
        ("してみたい", "してみること"),
        ("話してみたい", "話してみること"),
        ("聞いてみたい", "聞いてみること"),
        ("やってみたい", "やってみること"),
        ("したい", "すること"),
        ("なりたい", "なること"),
        ("増やしたい", "増やすこと"),
        ("続けたい", "続けること"),
        ("していきたい", "続けていくこと"),
    )
    for src, dst in replacements:
        if s.endswith(src):
            return s[: -len(src)] + dst

    if s.endswith("しようかな"):
        return s[: -len("しようかな")] + "すること"
    if s.endswith("しよう"):
        return s[: -len("しよう")] + "すること"
    if s.endswith("楽しい"):
        return s[: -len("楽しい")] + "時間"
    if s.endswith("嬉しい"):
        return s[: -len("嬉しい")] + "こと"
    if s.endswith(("こと", "時間", "関係")):
        return s
    if re.search(r"(する|した|している|してる|できる|話す|聞く|休む|整える|続ける|広げる)$", s):
        return s + "こと"
    return s



def _evidence_entry(text: str, score: int, role: str, *reasons: str) -> GeneratedAnswerEvidence:
    return GeneratedAnswerEvidence(
        text=_collapse_ws(text),
        score=int(score),
        role=str(role),
        reasons=tuple(_ordered_unique([r for r in reasons if str(r or "").strip()])),
    )



def _match_relationship_rule(combined: str) -> Optional[Tuple[str, str, Tuple[str, ...]]]:
    if _contains_any(combined, ("安心",)) and _contains_any(combined, _RELATIONSHIP_KEYS):
        support = "無理のない範囲で、コメントや会話の機会を少しずつ増やしていきたい"
        if not _contains_any(combined, ("コメント",)):
            support = "無理のない範囲で、少しずつ会話の時間を増やしていきたい"
        return "安心してやり取りできる関係をつくること", support, ("relationship:stable",)
    if _contains_any(combined, _RELATIONSHIP_KEYS):
        support = "無理のない範囲で、コメントや会話の機会を少しずつ増やしていきたい"
        if not _contains_any(combined, ("コメント",)):
            support = "無理のない範囲で、少しずつ会話の時間を増やしていきたい"
        if _contains_any(combined, ("楽しい", "嬉しい")):
            support = "実際にやってみると、少し楽しいと感じる瞬間もあります"
        return "少しずつ交流を広げること", support, ("relationship:expand",)
    return None



def _match_value_rule(spec: GeneratedQuestionSpec, combined: str) -> Optional[Tuple[str, str, Tuple[str, ...]]]:
    if spec.question_family == "work_value":
        if _contains_any(combined, _HEALTH_KEYS) or _contains_any(combined, ("仕事", "働")):
            return (
                "無理をしすぎず、今の体調に合わせて働くこと",
                "今の状態を見ながら、焦らず整えていきたいと思っています",
                ("work_value:health",),
            )
        if _contains_any(combined, ("できた", "できなかった", "振り返", "反省", "ミス")):
            return "できたことと課題の両方を振り返ること", "", ("work_value:review",)
        if _contains_any(combined, ("焦", "スピード", "余裕")):
            return "焦りすぎず落ち着いて働くこと", "", ("work_value:pace",)
        return None

    if _contains_any(combined, _HEALTH_KEYS):
        return (
            "無理をしすぎず心と体を整えること",
            "今の状態を見ながら、焦らず整えていきたいと思っています",
            ("values:health",),
        )
    if _contains_any(combined, ("できた", "できなかった", "振り返", "反省")):
        return "できたことと課題の両方を振り返ること", "", ("values:review",)
    if _contains_any(combined, ("自分を知", "何ができる", "できること", "できないこと")):
        return "自分を知ろうとすること", "", ("values:self_knowledge",)
    if _contains_any(combined, ("感情の感じ方", "気持ちを受け止め")):
        return "自分の気持ちを受け止めること", "", ("values:emotion",)
    return None



def _match_growth_rule(spec: GeneratedQuestionSpec, combined: str) -> Optional[Tuple[str, str, Tuple[str, ...]]]:
    if spec.question_family == "work_growth":
        if _contains_any(combined, ("今週", "来週", "頑張れた", "頑張れる")):
            return "仕事の波があっても安定して頑張れるようになること", "", ("work_growth:stability",)
        if _contains_any(combined, ("体調", "休めない", "休んだ方", "出勤", "週4", "働く")):
            return "体調を見ながら安定して働けるようになること", "", ("work_growth:health",)
        if _contains_any(combined, ("ミス", "効率", "容量良く")):
            return "落ち着いて仕事をこなせるようになること", "", ("work_growth:skill",)
        return None

    if _contains_any(combined, ("美容室",)):
        return "気になっていたことに一歩踏み出すこと", "", ("growth:first_step",)
    if _contains_any(combined, _HEALTH_KEYS):
        return "体調を大事にしながら生活を整えること", "", ("growth:health",)
    if _contains_any(combined, ("配信", "話", "コメント", "練習")):
        return "無理のない範囲で話す練習を続けること", "", ("growth:conversation",)
    if _contains_any(combined, ("一人暮らし", "自立")):
        return "少しずつ生活の基盤を整えていくこと", "", ("growth:life_base",)
    return None



def _match_concern_rule(spec: GeneratedQuestionSpec, combined: str) -> Optional[Tuple[str, str, Tuple[str, ...]]]:
    if spec.question_family == "work_concern":
        if _contains_any(combined, ("どこがダメ", "できなかった", "反省", "振り返")):
            return (
                "できなかった点を振り返ること",
                "毎日の仕事を振り返りながら、次にどう動くかを考えることがあります",
                ("work_concern:review",),
            )
        if _contains_any(combined, ("ミス",)):
            return "ミスを減らすこと", "落ち着いて仕事を進められるか気になることがあります", ("work_concern:mistake",)
        if _contains_any(combined, ("迷惑", "負担", "心苦しい")):
            return "周りに負担をかけないこと", "休んだ時に迷惑をかけていないか気になることがあります", ("work_concern:burden",)
        if _contains_any(combined, ("スピード", "体力", "焦", "余裕")):
            return "仕事のペースについていくこと", "体力や集中力とのバランスが気になることがあります", ("work_concern:pace",)
        return None

    if _contains_any(combined, _OPERATIONAL_MARKERS):
        return None
    if _contains_any(combined, ("焦", "余裕がない", "余裕ない", "慌ただ")):
        return "どこか焦っていて余裕が少ないこと", "毎日を慌ただしく感じることがあります", ("concern:pace",)
    if _contains_any(combined, ("やってみたい", "写真", "投稿", "Sky", "ハートピア")):
        return "お休みの日にやってみたいこと", "気になる景色や好きなものを形にしてみたいと思っています", ("concern:future_fun",)
    if _contains_any(combined, _HEALTH_KEYS):
        return "体調の波があること", "", ("concern:health",)
    return None



def _match_notice_rule(combined: str) -> Optional[Tuple[str, str, Tuple[str, ...]]]:
    if _contains_any(combined, _OPERATIONAL_MARKERS):
        return None
    if _contains_any(combined, ("焦", "余裕がない", "余裕ない", "慌ただ")):
        return "どこか焦っていて余裕が少ないこと", "毎日を慌ただしく感じることがあります", ("notice:pace",)
    if _contains_any(combined, ("前向", "楽しい", "嬉しい", "湧いてきた")):
        return "少し前向きな気持ちが戻ってきていること", "", ("notice:positive_shift",)
    if _contains_any(combined, ("不具合",)):
        return None
    return None



def _match_fun_rule(spec: GeneratedQuestionSpec, combined: str) -> Optional[Tuple[str, str, Tuple[str, ...]]]:
    if _contains_any(combined, ("配信",)) and _contains_any(combined, ("話", "コメント", "交流")):
        support = ""
        if _contains_any(combined, ("楽しい", "嬉しい")):
            support = "実際にやってみると、少し楽しいと感じる瞬間もあります"
        return "配信を通して人と話すこと", support, ("fun:stream_talk",)
    if _contains_any(combined, ("歌", "枠", "歌う")):
        return "歌うこと", "", ("fun:song",)
    if _contains_any(combined, ("写真", "投稿", "Sky", "ハートピア")):
        return "写真を撮って投稿すること", "気になる景色や好きなものを形にしてみたいと思っています", ("fun:photo",)
    if _contains_any(combined, ("料理", "服", "可愛い")):
        return "好きなものを選んだり作ったりすること", "", ("fun:making",)
    return None



def _match_stress_rule(spec: GeneratedQuestionSpec, combined: str) -> Optional[Tuple[str, str, Tuple[str, ...]]]:
    if spec.question_family == "stress_time":
        if _contains_any(combined, ("ASMR", "キーボード", "音")) and _contains_any(combined, ("夜", "夜中", "寝る前", "LINE", "話")):
            return "寝る前や夜に、安心できるやり取りや音に触れている時間", "そういう時間があると、少し落ち着けます", ("stress_time:night_audio",)
        if _contains_any(combined, ("ASMR", "キーボード", "音")):
            return "安心できる音に触れている時間", "そういう時間があると、少し落ち着けます", ("stress_time:audio",)
        if _contains_any(combined, ("LINE", "話")):
            return "安心できる人と話している時間", "そういう時間があると、少し落ち着けます", ("stress_time:talk",)
        if _contains_any(combined, _STRESS_KEYS):
            return "無理をせず落ち着ける時間", "そういう時間があると、少し落ち着けます", ("stress_time:rest",)
        return None

    if spec.question_family == "work_stress_method":
        if _contains_any(combined, ("仕事", "働")) and _contains_any(combined, _STRESS_KEYS):
            return "無理のないペースで休むこと", "仕事のことを抱え込みすぎないように、少しずつ整えています", ("work_stress:rest",)
        return None

    if _contains_any(combined, ("食生活", "ロールキャベツ", "豆腐ハンバーグ")):
        return "食生活や過ごし方を整えること", "楽しみながら続けられる形を大事にしています", ("stress_method:lifestyle",)
    if _contains_any(combined, ("休", "寝", "無理", "ペース", "薬")):
        return "無理のないペースで休むこと", "今の状態を見ながら、焦らず整えています", ("stress_method:rest",)
    if _contains_any(combined, ("話", "LINE", "ASMR", "音", "キーボード")):
        return "安心できる人や音に触れて落ち着くこと", "無理のない範囲で、少しずつ気持ちを整えています", ("stress_method:safe_contact",)
    return None



def _canonicalize_fragment_for_spec(spec: GeneratedQuestionSpec, fragment: str, combined: str) -> str:
    compact = _compact_text(fragment)
    if not compact:
        return ""
    family = spec.question_family

    if family in {"fun_general", "fun_recent"}:
        if _contains_any(compact, ("歌", "枠", "歌う")):
            return "歌うこと"
        if _contains_any(compact, ("配信",)) and _contains_any(compact, ("話", "コメント", "交流")):
            return "配信を通して人と話すこと"
        if _contains_any(compact, ("写真", "投稿", "Sky", "ハートピア")):
            return "写真を撮って投稿すること"
        if _contains_any(compact, ("料理", "服", "可愛い")):
            return "好きなものを選んだり作ったりすること"

    if family == "relationship_value":
        if _contains_any(compact, ("安心",)) and _contains_any(compact, _RELATIONSHIP_KEYS):
            return "安心してやり取りできる関係をつくること"
        if _contains_any(compact, _RELATIONSHIP_KEYS):
            return "少しずつ交流を広げること"
        return ""

    if family == "work_concern":
        if _contains_any(compact, ("どこがダメ", "できなかった", "反省", "振り返")):
            return "できなかった点を振り返ること"
        if _contains_any(compact, ("ミス",)):
            return "ミスを減らすこと"
        if _contains_any(compact, ("迷惑", "負担", "心苦しい")):
            return "周りに負担をかけないこと"
        if _contains_any(compact, ("スピード", "体力", "焦", "余裕")):
            return "仕事のペースについていくこと"

    if family in {"notice_general", "concern_general"}:
        if _contains_any(compact, ("焦", "余裕がない", "余裕ない", "慌ただ")):
            return "どこか焦っていて余裕が少ないこと"

    if family == "growth_general" and _contains_any(compact, ("美容室",)):
        return "気になっていたことに一歩踏み出すこと"

    if family == "work_growth":
        if _contains_any(compact, ("頑張れた", "今週", "来週")):
            return "仕事の波があっても安定して頑張れるようになること"
        if _contains_any(compact, ("体調", "休めない", "休んだ方", "出勤", "働く")):
            return "体調を見ながら安定して働けるようになること"

    if family == "stress_time":
        if _contains_any(compact, ("ASMR", "キーボード", "音")):
            return "安心できる音に触れている時間"
        if _contains_any(compact, ("LINE", "話")):
            return "安心できる人と話している時間"
        if _contains_any(compact, _STRESS_KEYS):
            return "無理をせず落ち着ける時間"

    if family in {"stress_method", "work_stress_method"}:
        if _contains_any(compact, ("食生活", "ロールキャベツ", "豆腐ハンバーグ")):
            return "食生活や過ごし方を整えること"
        if _contains_any(compact, ("休", "寝", "無理", "ペース", "薬")):
            return "無理のないペースで休むこと"
        if _contains_any(compact, ("LINE", "話", "ASMR", "音", "キーボード")):
            return "安心できる人や音に触れて落ち着くこと"

    if family in {"value_general", "work_value"} and _contains_any(compact, _HEALTH_KEYS):
        return "無理をしすぎず心と体を整えること" if family == "value_general" else "無理をしすぎず、今の体調に合わせて働くこと"

    theme = _nominalize_phrase(fragment)
    if _is_low_quality_core_phrase(theme) or _looks_like_oneoff_event_fragment(theme):
        return ""
    return theme



def _maybe_support_from_combined(spec: GeneratedQuestionSpec, combined: str, core_theme: str) -> str:
    family = spec.question_family
    if family == "relationship_value":
        if _contains_any(combined, ("楽しい", "嬉しい")):
            return "実際にやってみると、少し楽しいと感じる瞬間もあります"
        if _contains_any(combined, ("コメント",)):
            return "無理のない範囲で、コメントや会話の機会を少しずつ増やしていきたい"
        return "無理のない範囲で、少しずつ会話の時間を増やしていきたい"
    if family in {"value_general", "work_value"} and _contains_any(core_theme, ("整える", "体調")):
        return "今の状態を見ながら、焦らず整えていきたいと思っています"
    if family == "work_concern":
        if _contains_any(combined, ("どこがダメ", "できなかった", "反省", "振り返")):
            return "毎日の仕事を振り返りながら、次にどう動くかを考えることがあります"
        if _contains_any(combined, ("ミス",)):
            return "落ち着いて仕事を進められるか気になることがあります"
        if _contains_any(combined, ("迷惑", "負担", "心苦しい")):
            return "休んだ時に迷惑をかけていないか気になることがあります"
        if _contains_any(combined, ("スピード", "体力", "焦", "余裕")):
            return "体力や集中力とのバランスが気になることがあります"
    if family in {"notice_general", "concern_general"} and _contains_any(core_theme, ("焦っていて余裕が少ない",)):
        return "毎日を慌ただしく感じることがあります"
    if family in {"fun_general", "fun_recent"} and _contains_any(combined, ("楽しい", "嬉しい")):
        return "実際にやってみると、少し楽しいと感じる瞬間もあります"
    if family == "stress_time":
        return "そういう時間があると、少し落ち着けます"
    if family == "stress_method":
        if _contains_any(core_theme, ("食生活",)):
            return "楽しみながら続けられる形を大事にしています"
        return "今の状態を見ながら、焦らず整えています"
    if family == "work_stress_method":
        return "仕事のことを抱え込みすぎないように、少しずつ整えています"
    return ""



def _should_block_operational_source(spec: GeneratedQuestionSpec, combined: str) -> bool:
    if spec.question_family not in {"notice_general", "concern_general", "fun_general", "fun_recent", "value_general"}:
        return False
    if not _contains_any(combined, _OPERATIONAL_MARKERS):
        return False
    if _contains_any(combined, ("自分", "気持ち", "焦", "余裕", "楽しい")):
        return False
    return True



def build_generated_answer_plan(
    *,
    question: Any,
    raw_answer: Any,
    category: Any = None,
    focus_key: Any = None,
    topic_summary_text: Any = None,
    text_candidates: Optional[Sequence[Any]] = None,
) -> GeneratedAnswerPlan:
    q = _collapse_ws(question)
    raw = _collapse_ws(raw_answer)
    summary = _collapse_ws(topic_summary_text)
    candidates = [_collapse_ws(x) for x in (text_candidates or []) if _collapse_ws(x)]
    spec = _derive_question_spec(question=q, focus_key=focus_key)

    combined = " ".join([q, _collapse_ws(category), summary, raw, *candidates]).strip()
    compact_combined = _compact_text(combined)
    fragments = _collect_source_fragments(raw_answer=raw, topic_summary_text=summary, text_candidates=candidates)

    if _should_block_operational_source(spec, compact_combined):
        return GeneratedAnswerPlan(
            spec=spec,
            answerable=False,
            block_reason="operational_source",
            core_theme="",
            support_theme="",
            temporal_scope="latest",
            source_quality="blocked",
            evidence=(),
        )

    matcher_map = {
        "relationship_value": _match_relationship_rule,
        "value_general": lambda c: _match_value_rule(spec, c),
        "work_value": lambda c: _match_value_rule(spec, c),
        "growth_general": lambda c: _match_growth_rule(spec, c),
        "work_growth": lambda c: _match_growth_rule(spec, c),
        "work_concern": lambda c: _match_concern_rule(spec, c),
        "notice_general": _match_notice_rule,
        "concern_general": lambda c: _match_concern_rule(spec, c),
        "fun_general": lambda c: _match_fun_rule(spec, c),
        "fun_recent": lambda c: _match_fun_rule(spec, c),
        "stress_method": lambda c: _match_stress_rule(spec, c),
        "stress_time": lambda c: _match_stress_rule(spec, c),
        "work_stress_method": lambda c: _match_stress_rule(spec, c),
    }
    rule_matcher = matcher_map.get(spec.question_family)
    if callable(rule_matcher):
        matched = rule_matcher(compact_combined)
        if matched is not None:
            core_theme, support_theme, reasons = matched
            evidence = (
                _evidence_entry(raw or summary or q, 10, "core", *reasons),
            )
            if support_theme:
                evidence = evidence + (_evidence_entry(support_theme, 8, "support", *(tuple(reasons) + ("support:rule",))),)
            return GeneratedAnswerPlan(
                spec=spec,
                answerable=bool(core_theme),
                block_reason="" if core_theme else "no_rule_theme",
                core_theme=str(core_theme or ""),
                support_theme=str(support_theme or ""),
                temporal_scope="latest",
                source_quality="usable" if core_theme else "weak",
                evidence=evidence,
            )

    scored: List[Tuple[int, str, Tuple[str, ...], str]] = []
    for fragment in fragments:
        score, reasons = _score_fragment_for_spec(spec, fragment)
        theme = _canonicalize_fragment_for_spec(spec, fragment, compact_combined)
        if not theme:
            continue
        if _is_low_quality_core_phrase(theme):
            continue
        if spec.require_method_like and not _contains_any(_compact_text(theme), _METHOD_LIKE_HINTS):
            score -= 2
        if spec.require_time_like and not _contains_any(_compact_text(theme), _TIME_LIKE_HINTS):
            score -= 2
        scored.append((score, fragment, reasons, theme))

    scored.sort(key=lambda item: (item[0], -len(item[3]), -len(item[1])), reverse=True)
    if not scored or scored[0][0] <= 0:
        return GeneratedAnswerPlan(
            spec=spec,
            answerable=False,
            block_reason="no_usable_theme",
            core_theme="",
            support_theme="",
            temporal_scope="latest",
            source_quality="weak",
            evidence=tuple(
                _evidence_entry(fragment, score, "core", *reasons)
                for score, fragment, reasons, _theme in scored[:2]
            ),
        )

    best_score, best_fragment, best_reasons, best_theme = scored[0]
    support_theme = _maybe_support_from_combined(spec, compact_combined, best_theme)
    evidence_list = [_evidence_entry(best_fragment, best_score, "core", *best_reasons)]
    if support_theme:
        evidence_list.append(_evidence_entry(support_theme, max(best_score - 1, 1), "support", "support:derived"))
    return GeneratedAnswerPlan(
        spec=spec,
        answerable=True,
        block_reason="",
        core_theme=str(best_theme or ""),
        support_theme=str(support_theme or ""),
        temporal_scope="latest",
        source_quality="usable" if best_score >= 2 else "weak",
        evidence=tuple(evidence_list),
    )



def _render_support_sentence(plan: GeneratedAnswerPlan) -> str:
    support = _collapse_ws(plan.support_theme)
    if not support:
        return ""
    if support.endswith(("。", "！", "？", "!", "?")):
        return support
    if plan.spec.question_family == "stress_time":
        return _ensure_sentence(support)
    return _ensure_sentence(support)



def realize_generated_answer_text(plan: GeneratedAnswerPlan) -> Tuple[str, List[str]]:
    actions: List[str] = [f"plan:{plan.spec.question_family}"]
    if not plan.answerable or not str(plan.core_theme or "").strip():
        _append_once(actions, f"plan:block:{plan.block_reason or 'no_usable_theme'}")
        return "", actions

    core = _collapse_ws(plan.core_theme)
    head = _ensure_sentence(f"{plan.spec.head_prefix}{core}{plan.spec.head_suffix}")
    support = _render_support_sentence(plan)
    rewritten = " ".join([segment for segment in (head, support) if segment]).strip()
    if rewritten:
        _append_once(actions, "rewrite:plan_realize")
    return rewritten, actions



def compose_generated_answer_raw(
    *,
    question: Any,
    raw_answer: Any,
    category: Any = None,
    focus_key: Any = None,
    topic_summary_text: Any = None,
    text_candidates: Optional[Sequence[Any]] = None,
) -> Tuple[str, List[str]]:
    plan = build_generated_answer_plan(
        question=question,
        raw_answer=raw_answer,
        category=category,
        focus_key=focus_key,
        topic_summary_text=topic_summary_text,
        text_candidates=text_candidates,
    )
    return realize_generated_answer_text(plan)



def _collect_quality_flags(text: str) -> List[str]:
    s = _collapse_ws(text)
    flags: List[str] = []
    if not s:
        _append_once(flags, "quality:empty")
        return flags
    lowered = s.rstrip("。！？!? ")
    compact = lowered.replace(" ", "")
    if len(compact) < 8:
        _append_once(flags, "quality:too_short")
    if _SHORT_PARTICLE_TAIL_RE.search(lowered):
        _append_once(flags, "quality:unfinished")
    if lowered in _BAD_EXACTS:
        _append_once(flags, "quality:noun_only")
    if _GENERIC_FALLBACK_RE.search(lowered):
        _append_once(flags, "quality:fallback_generic")
    if re.search(r"(?:だ|です)です$", compact):
        _append_once(flags, "quality:broken_answer")
    if re.search(r"(?:今まで|今の|さっきまで)?私(?:は|が)?です$", compact):
        _append_once(flags, "quality:broken_answer")
    if re.search(r"(?:自分|私自身)(?:は|が)?です$", compact):
        _append_once(flags, "quality:broken_answer")
    if _contains_any(compact, _OPERATIONAL_MARKERS):
        _append_once(flags, "quality:operational_source")
    if "?" in compact or "？" in compact:
        _append_once(flags, "quality:broken_answer")
    return flags



def _collect_question_family_flags(spec: GeneratedQuestionSpec, text: str) -> List[str]:
    s = _collapse_ws(text)
    compact = _compact_text(s)
    flags: List[str] = []
    if not s:
        _append_once(flags, "quality:empty")
        return flags
    if spec.allowed_head_prefixes and not any(s.startswith(prefix) for prefix in spec.allowed_head_prefixes):
        _append_once(flags, "quality:question_head_mismatch")
    if spec.forbidden_head_prefixes and any(s.startswith(prefix) for prefix in spec.forbidden_head_prefixes):
        _append_once(flags, "quality:question_head_mismatch")
    if spec.require_notice_like and "気づ" not in compact:
        _append_once(flags, "quality:question_shape_mismatch")
    if spec.require_concern_like and not _contains_any(compact, ("気にな", "気にして")):
        _append_once(flags, "quality:question_shape_mismatch")
    if spec.require_method_like and not _contains_any(compact, _METHOD_LIKE_HINTS):
        _append_once(flags, "quality:question_shape_mismatch")
    if spec.require_time_like and not _contains_any(compact, _TIME_LIKE_HINTS):
        _append_once(flags, "quality:question_shape_mismatch")
    if spec.require_value_like and not _contains_any(compact, _VALUE_LIKE_HINTS):
        _append_once(flags, "quality:question_shape_mismatch")
    return flags



def validate_generated_answer_text(
    *,
    plan: GeneratedAnswerPlan,
    display_text: Optional[str],
    display_state: str,
    flags: Sequence[str],
    actions: Sequence[str],
    quality_source_text: str,
) -> GeneratedAnswerValidationResult:
    state = str(display_state or STATE_READY).strip().lower() or STATE_READY
    merged_flags = _ordered_unique([
        *list(flags or []),
        *_collect_quality_flags(quality_source_text),
        *_collect_question_family_flags(plan.spec, quality_source_text),
    ])
    merged_actions = _ordered_unique([*list(actions or [])])
    rewrite_needed = any(
        flag in {
            "quality:question_head_mismatch",
            "quality:question_shape_mismatch",
            "quality:broken_answer",
            "quality:unfinished",
            "quality:fallback_generic",
            "quality:operational_source",
        }
        for flag in merged_flags
    )

    if not plan.answerable:
        _append_once(merged_flags, f"quality:block_reason:{plan.block_reason or 'no_usable_theme'}")
        _append_once(merged_actions, "quality:block")
        return GeneratedAnswerValidationResult(
            answer_display_text=None,
            answer_display_state=STATE_BLOCKED,
            flags=merged_flags,
            actions=merged_actions,
            rewrite_needed=True,
        )

    if state == STATE_BLOCKED:
        _append_once(merged_actions, "quality:block")
        return GeneratedAnswerValidationResult(
            answer_display_text=None,
            answer_display_state=STATE_BLOCKED,
            flags=merged_flags,
            actions=merged_actions,
            rewrite_needed=True,
        )

    display_value = str(display_text or "").strip()
    blocking_flags = {
        "quality:empty",
        "quality:too_short",
        "quality:unfinished",
        "quality:noun_only",
        "quality:broken_answer",
        "quality:fallback_generic",
        "quality:question_head_mismatch",
        "quality:question_shape_mismatch",
        "quality:operational_source",
    }
    if not display_value or any(
        flag in blocking_flags or str(flag).startswith("quality:block_reason:")
        for flag in merged_flags
    ):
        _append_once(merged_actions, "quality:block")
        return GeneratedAnswerValidationResult(
            answer_display_text=None,
            answer_display_state=STATE_BLOCKED,
            flags=merged_flags,
            actions=merged_actions,
            rewrite_needed=True,
        )

    return GeneratedAnswerValidationResult(
        answer_display_text=display_value,
        answer_display_state=STATE_MASKED if state == STATE_MASKED else STATE_READY,
        flags=merged_flags,
        actions=merged_actions,
        rewrite_needed=rewrite_needed,
    )



@dataclass(frozen=True)
class GeneratedReflectionDisplayResult:
    raw_answer_text: str
    rewritten_answer_text: str
    answer_display_text: Optional[str]
    answer_display_state: str
    changed: bool
    flags: List[str]
    actions: List[str]
    answer_norm_hash: str
    display_source_signature: str
    rewrite_needed: bool = False
    plan_meta: Optional[Dict[str, Any]] = None
    format_version: str = GENERATED_REFLECTION_DISPLAY_VERSION

    def as_storage_meta(self) -> Dict[str, Any]:
        display_text = str(self.answer_display_text or "")
        plan_meta = dict(self.plan_meta or {})
        return {
            "version": str(self.format_version),
            "changed": bool(self.changed),
            "flags": list(self.flags),
            "actions": list(self.actions),
            "raw_length": int(len(self.raw_answer_text)),
            "rewritten_length": int(len(self.rewritten_answer_text)),
            "display_length": int(len(display_text)),
            "display_state": str(self.answer_display_state),
            "answer_norm_hash": str(self.answer_norm_hash),
            "display_source_signature": str(self.display_source_signature),
            "blocked": bool(self.answer_display_state == STATE_BLOCKED),
            "rewrite_needed": bool(self.rewrite_needed),
            **plan_meta,
        }



def build_generated_reflection_display(
    *,
    question: Any,
    raw_answer: Any,
    category: Any = None,
    focus_key: Any = None,
    topic_summary_text: Any = None,
    text_candidates: Optional[Sequence[Any]] = None,
) -> GeneratedReflectionDisplayResult:
    raw = _collapse_ws(raw_answer)
    plan = build_generated_answer_plan(
        question=question,
        raw_answer=raw,
        category=category,
        focus_key=focus_key,
        topic_summary_text=topic_summary_text,
        text_candidates=text_candidates,
    )
    rewritten, realize_actions = realize_generated_answer_text(plan)

    if rewritten:
        safety = format_reflection_text(rewritten)
        validation = validate_generated_answer_text(
            plan=plan,
            display_text=safety.display_text,
            display_state=str(safety.display_state),
            flags=safety.flags,
            actions=[*realize_actions, *safety.actions],
            quality_source_text=str(safety.display_text or rewritten or ""),
        )
        safety_changed = bool(safety.changed)
    else:
        validation = validate_generated_answer_text(
            plan=plan,
            display_text=None,
            display_state=STATE_BLOCKED if not plan.answerable else STATE_READY,
            flags=[],
            actions=realize_actions,
            quality_source_text="",
        )
        safety_changed = False

    norm_source = validation.answer_display_text if validation.answer_display_text is not None else (rewritten or raw)
    changed = bool(
        raw != rewritten
        or safety_changed
        or validation.actions
        or validation.answer_display_state != (STATE_BLOCKED if not plan.answerable else STATE_READY)
    )
    source_signature = compute_generated_display_source_signature(
        question=question,
        raw_answer=raw,
        category=category,
        focus_key=focus_key,
        topic_summary_text=topic_summary_text,
        text_candidates=text_candidates,
    )
    return GeneratedReflectionDisplayResult(
        raw_answer_text=raw,
        rewritten_answer_text=rewritten,
        answer_display_text=validation.answer_display_text,
        answer_display_state=validation.answer_display_state,
        changed=changed,
        flags=validation.flags,
        actions=validation.actions,
        answer_norm_hash=compute_generated_answer_norm_hash(norm_source),
        display_source_signature=source_signature,
        rewrite_needed=validation.rewrite_needed,
        plan_meta=plan.as_meta(),
    )



def apply_generated_display_to_content_json(
    content_json: Mapping[str, Any],
    *,
    result: GeneratedReflectionDisplayResult,
    display_updated_at: Optional[str],
) -> Dict[str, Any]:
    updated = dict(content_json or {})
    display_payload = {
        "answer_display_text": result.answer_display_text,
        "answer_display_state": result.answer_display_state,
        "answer_format_version": result.format_version,
        "answer_format_meta": result.as_storage_meta(),
        "answer_display_updated_at": str(display_updated_at or "").strip() or None,
        "rewritten_answer_text": result.rewritten_answer_text,
        "answer_norm_hash": result.answer_norm_hash,
        "display_source_signature": result.display_source_signature,
    }
    updated["display"] = dict(display_payload)
    # keep flat keys too so legacy helpers / SQL probes can inspect content_json easily
    updated.update(display_payload)
    return updated



def _extract_display_bundle(row: Mapping[str, Any]) -> Dict[str, Any]:
    content_json = _parse_mapping((row or {}).get("content_json"))
    display_bundle = _parse_mapping(content_json.get("display"))

    out: Dict[str, Any] = {}
    for key in (
        "answer_display_text",
        "answer_display_state",
        "answer_format_version",
        "answer_format_meta",
        "answer_display_updated_at",
        "rewritten_answer_text",
        "answer_norm_hash",
        "display_source_signature",
    ):
        if key in row and (row or {}).get(key) is not None:
            out[key] = (row or {}).get(key)
        elif key in display_bundle and display_bundle.get(key) is not None:
            out[key] = display_bundle.get(key)
        elif key in content_json and content_json.get(key) is not None:
            out[key] = content_json.get(key)
    return out



def _stored_generated_display_result_from_row(row: Mapping[str, Any]) -> Optional[GeneratedReflectionDisplayResult]:
    if not isinstance(row, Mapping):
        return None
    content_json = _parse_mapping((row or {}).get("content_json"))
    bundle = _extract_display_bundle(row)
    state = str(bundle.get("answer_display_state") or "").strip().lower()
    if state not in {STATE_READY, STATE_MASKED, STATE_BLOCKED}:
        return None

    topic_summary_text = content_json.get("topic_summary_text") or (row or {}).get("topic_summary_text")
    focus_key = content_json.get("focus_key") or (row or {}).get("focus_key")
    text_candidates: List[str] = []
    source_refs = content_json.get("source_refs")
    if isinstance(source_refs, list):
        for ref in source_refs:
            if isinstance(ref, dict):
                for key in ("text_primary", "text_secondary", "question_text"):
                    value = _collapse_ws(ref.get(key))
                    if value:
                        text_candidates.append(value)

    stored_signature = str(bundle.get("display_source_signature") or "").strip()
    current_signature = compute_generated_display_source_signature(
        question=(row or {}).get("question"),
        raw_answer=(row or {}).get("answer"),
        category=(row or {}).get("category"),
        focus_key=focus_key,
        topic_summary_text=topic_summary_text,
        text_candidates=text_candidates,
    )

    updated_at = _parse_iso((row or {}).get("updated_at"))
    display_updated_at = _parse_iso(bundle.get("answer_display_updated_at"))
    if updated_at and display_updated_at and display_updated_at < updated_at:
        if not stored_signature or not current_signature or stored_signature != current_signature:
            return None

    display_text: Optional[str]
    if state == STATE_BLOCKED:
        display_text = None
    else:
        display_value = str(bundle.get("answer_display_text") or "").strip()
        if not display_value:
            return None
        display_text = display_value

    meta = _parse_mapping(bundle.get("answer_format_meta"))
    version = str(bundle.get("answer_format_version") or meta.get("version") or GENERATED_REFLECTION_DISPLAY_VERSION).strip() or GENERATED_REFLECTION_DISPLAY_VERSION
    if version != GENERATED_REFLECTION_DISPLAY_VERSION:
        return None

    flags = [str(x).strip() for x in (meta.get("flags") or []) if str(x).strip()]
    actions = [str(x).strip() for x in (meta.get("actions") or []) if str(x).strip()]
    raw = _collapse_ws((row or {}).get("answer"))
    rewritten = _collapse_ws(bundle.get("rewritten_answer_text") or display_text or raw)
    plan = build_generated_answer_plan(
        question=(row or {}).get("question"),
        raw_answer=(row or {}).get("answer"),
        category=(row or {}).get("category"),
        focus_key=focus_key,
        topic_summary_text=topic_summary_text,
        text_candidates=text_candidates,
    )
    validation = validate_generated_answer_text(
        plan=plan,
        display_text=display_text,
        display_state=state,
        flags=flags,
        actions=actions,
        quality_source_text=display_text or rewritten or raw,
    )
    if validation.answer_display_state != state or validation.answer_display_text != display_text:
        return None

    norm_hash = str(bundle.get("answer_norm_hash") or meta.get("answer_norm_hash") or compute_generated_answer_norm_hash(display_text or rewritten or raw)).strip()
    changed_meta = meta.get("changed")
    changed = bool(changed_meta) if changed_meta is not None else bool(rewritten != raw or state != STATE_READY)
    display_source_signature = stored_signature or str(meta.get("display_source_signature") or current_signature or "").strip()
    return GeneratedReflectionDisplayResult(
        raw_answer_text=raw,
        rewritten_answer_text=rewritten,
        answer_display_text=display_text,
        answer_display_state=state,
        changed=changed,
        flags=_ordered_unique(validation.flags),
        actions=_ordered_unique(validation.actions),
        answer_norm_hash=norm_hash,
        display_source_signature=display_source_signature,
        rewrite_needed=validation.rewrite_needed,
        plan_meta=plan.as_meta(),
        format_version=version,
    )



def resolve_generated_reflection_display(row: Mapping[str, Any]) -> GeneratedReflectionDisplayResult:
    stored = _stored_generated_display_result_from_row(row)
    if stored is not None:
        return stored

    content_json = _parse_mapping((row or {}).get("content_json"))
    topic_summary_text = content_json.get("topic_summary_text") or (row or {}).get("topic_summary_text")
    focus_key = content_json.get("focus_key") or (row or {}).get("focus_key")
    text_candidates: List[str] = []
    source_refs = content_json.get("source_refs")
    if isinstance(source_refs, list):
        for ref in source_refs:
            if isinstance(ref, dict):
                for key in ("text_primary", "text_secondary", "question_text"):
                    value = _collapse_ws(ref.get(key))
                    if value:
                        text_candidates.append(value)
    return build_generated_reflection_display(
        question=(row or {}).get("question"),
        raw_answer=(row or {}).get("answer"),
        category=(row or {}).get("category"),
        focus_key=focus_key,
        topic_summary_text=topic_summary_text,
        text_candidates=text_candidates,
    )



def get_public_generated_reflection_text(row: Mapping[str, Any]) -> Optional[str]:
    result = resolve_generated_reflection_display(row)
    if str(result.answer_display_state) == STATE_BLOCKED:
        return None
    text = str(result.answer_display_text or "").strip()
    return text or None


__all__ = [
    "GENERATED_REFLECTION_DISPLAY_VERSION",
    "GeneratedReflectionDisplayResult",
    "apply_generated_display_to_content_json",
    "build_generated_reflection_display",
    "build_generated_answer_plan",
    "compose_generated_answer_raw",
    "realize_generated_answer_text",
    "validate_generated_answer_text",
    "compute_generated_answer_norm_hash",
    "compute_generated_display_source_signature",
    "get_public_generated_reflection_text",
    "resolve_generated_reflection_display",
]
