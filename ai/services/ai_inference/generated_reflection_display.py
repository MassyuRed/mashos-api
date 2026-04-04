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

GENERATED_REFLECTION_DISPLAY_VERSION = "reflection.generated.display.v2"

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



def _contains_any(text: str, keywords: Sequence[str]) -> bool:
    return any(k and k in text for k in (keywords or []))



def _infer_mode(*, question: Any, focus_key: Any) -> str:
    q = str(question or "")
    fk = str(focus_key or "").strip().lower()
    if re.search(r"関わり|人との|人と", q):
        return "relationship"
    if re.search(r"大切|大事", q):
        return "values"
    if re.search(r"整え|休まる|落ち着く|しんど", q):
        return "stress"
    if re.search(r"伸ば|続ける|成長", q):
        return "growth"
    if re.search(r"夢中|楽し|明るくなる", q):
        return "fun"
    if re.search(r"気になる|気づいた", q):
        return "generic"
    if fk in {"relationship", "values", "stress", "relief", "growth", "fun", "generic"}:
        return "stress" if fk == "relief" else fk
    return "generic"



def _infer_semantic_core_phrase(
    *,
    mode: str,
    question: str,
    category: str,
    raw_answer: str,
    topic_summary_text: str,
    text_candidates: Sequence[str],
) -> str:
    combined = " ".join(
        [
            _collapse_ws(question),
            _collapse_ws(category),
            _collapse_ws(topic_summary_text),
            _collapse_ws(raw_answer),
            *[_collapse_ws(x) for x in (text_candidates or [])],
        ]
    )

    conversation_keys = ("配信", "枠", "コメント", "話", "交流", "関わ", "会話", "聞")
    health_keys = ("耳", "難聴", "体調", "薬", "休", "寝", "だる", "疲", "整")

    if mode == "fun":
        if _contains_any(combined, conversation_keys) and _contains_any(combined, ("配信", "コメント", "話", "交流")):
            return "配信を通して人と話すこと"
        if _contains_any(combined, ("写真", "投稿", "Sky", "ハートピア")):
            return "写真を撮って投稿すること"
        if _contains_any(combined, ("料理", "服", "可愛い")):
            return "好きなものを選んだり作ったりすること"

    if mode == "relationship":
        if _contains_any(combined, ("安心", "落ち着")) and _contains_any(combined, ("話", "関わ", "一緒")):
            return "安心してやり取りできる関係をつくること"
        if _contains_any(combined, conversation_keys):
            return "少しずつ交流を広げること"

    if mode == "values":
        if _contains_any(combined, health_keys):
            return "無理をしすぎず心と体を整えること"
        if _contains_any(combined, ("できた", "できなかった", "振り返")):
            return "できたことと課題の両方を振り返ること"

    if mode == "stress":
        if _contains_any(combined, health_keys):
            return "無理のないペースで休むこと"
        if _contains_any(combined, conversation_keys):
            return "安心できる場所で少し話すこと"

    if mode == "growth":
        if _contains_any(combined, ("配信", "話", "コメント", "練習", "30分")):
            return "無理のない範囲で話す練習を続けること"

    fragments = _split_fragments(topic_summary_text, raw_answer, *text_candidates)
    candidates: List[Tuple[int, str]] = []
    mode_keywords = {
        "relationship": ("話", "交流", "関わ", "コメント", "安心", "聞", "一緒"),
        "values": ("大切", "大事", "整", "休", "守", "続"),
        "stress": ("整", "休", "寝", "落ち着", "薬", "だる", "疲"),
        "growth": ("練習", "挑戦", "伸ば", "続け", "少しずつ", "できるよう", "増や"),
        "fun": ("楽しい", "夢中", "配信", "写真", "ゲーム", "料理", "歌", "話"),
        "generic": ("気", "最近", "意識", "考え"),
    }
    for fragment in fragments:
        s = _normalize_phrase(fragment)
        if _is_low_quality_core_phrase(s):
            continue
        score = 0
        if len(s) <= 26:
            score += 1
        if _contains_any(s, mode_keywords.get(mode, ())):
            score += 2
        if _contains_any(s, ("したい", "してみたい", "楽しい", "嬉しい", "安心", "大切", "整", "休", "配信", "話")):
            score += 2
        if _SHORT_PARTICLE_TAIL_RE.search(s):
            score -= 3
        candidates.append((score, s))

    candidates.sort(key=lambda item: (item[0], -len(item[1])), reverse=True)
    if not candidates:
        return ""
    candidate = candidates[0][1]
    return "" if _is_low_quality_core_phrase(candidate) else candidate



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



def _build_head_sentence(*, mode: str, core_phrase: str) -> str:
    core = _nominalize_phrase(core_phrase)
    if not core or _is_low_quality_core_phrase(core):
        return ""
    if mode == "relationship":
        return _ensure_sentence(f"人との関わりでは、{core}を大切にしたいです")
    if mode == "values":
        return _ensure_sentence(f"大切にしているのは、{core}です")
    if mode == "stress":
        if core.endswith("こと"):
            core = core[:-2] + "ことで"
        else:
            core = core + "ことで"
        return _ensure_sentence(f"しんどい時は、{core}気持ちを整えています")
    if mode == "growth":
        return _ensure_sentence(f"少しずつ伸ばしたいのは、{core}です")
    if mode == "fun":
        return _ensure_sentence(f"最近夢中なのは、{core}です")
    return _ensure_sentence(f"最近気になっているのは、{core}です")



def _build_support_sentence(*, mode: str, question: str, category: str, raw_answer: str, topic_summary_text: str, text_candidates: Sequence[str]) -> str:
    combined = " ".join(
        [
            _collapse_ws(question),
            _collapse_ws(category),
            _collapse_ws(topic_summary_text),
            _collapse_ws(raw_answer),
            *[_collapse_ws(x) for x in (text_candidates or [])],
        ]
    )

    if mode in {"fun", "relationship", "growth"} and _contains_any(combined, ("配信", "枠", "コメント", "話", "交流")):
        if _contains_any(combined, ("怖", "不安")) and mode == "relationship":
            return _ensure_sentence("無理のない範囲で、コメントや会話の機会を少しずつ増やしていきたいです")
        if _contains_any(combined, ("怖", "不安")):
            return _ensure_sentence("不安はあっても、少しずつ関わってみたい気持ちがあります")
        if _contains_any(combined, ("楽しい", "嬉しい")):
            return _ensure_sentence("実際にやってみると、少し楽しいと感じる瞬間もあります")
        return _ensure_sentence("無理のない範囲で、少しずつ会話の時間を増やしていきたいです")

    if mode in {"values", "stress"} and _contains_any(combined, ("耳", "難聴", "体調", "薬", "休", "寝", "だる", "疲")):
        return _ensure_sentence("今の状態を見ながら、焦らず整えていきたいと思っています")

    if mode == "fun" and _contains_any(combined, ("写真", "投稿")):
        return _ensure_sentence("気になる景色や好きなものを、自分のペースで形にしてみたいです")

    return ""



def compose_generated_answer_raw(
    *,
    question: Any,
    raw_answer: Any,
    category: Any = None,
    focus_key: Any = None,
    topic_summary_text: Any = None,
    text_candidates: Optional[Sequence[Any]] = None,
) -> Tuple[str, List[str]]:
    q = _collapse_ws(question)
    raw = _collapse_ws(raw_answer)
    cat = _collapse_ws(category)
    summary = _collapse_ws(topic_summary_text)
    candidates = [_collapse_ws(x) for x in (text_candidates or []) if _collapse_ws(x)]

    mode = _infer_mode(question=q, focus_key=focus_key)
    actions: List[str] = []
    core = _infer_semantic_core_phrase(
        mode=mode,
        question=q,
        category=cat,
        raw_answer=raw,
        topic_summary_text=summary,
        text_candidates=candidates,
    )
    if core:
        _append_once(actions, "rewrite:question_aware")
    head = _build_head_sentence(mode=mode, core_phrase=core)
    support = _build_support_sentence(
        mode=mode,
        question=q,
        category=cat,
        raw_answer=raw,
        topic_summary_text=summary,
        text_candidates=candidates,
    )
    rewritten = " ".join([seg for seg in [head, support] if seg]).strip()
    if rewritten:
        rewritten = _ensure_sentence(rewritten.replace("。 。", "。 ").strip())
    if not rewritten:
        if mode == "relationship":
            rewritten = "人との関わりについて、まだうまく言葉にしきれていない気持ちがあります。"
        elif mode == "values":
            rewritten = "大切にしていることを、まだうまく言葉にしきれていません。"
        elif mode == "stress":
            rewritten = "今の整え方を、まだうまく言葉にしきれていません。"
        elif mode == "fun":
            rewritten = "最近夢中なことを、まだうまく言葉にしきれていません。"
        else:
            rewritten = "最近の気持ちを、まだうまく言葉にしきれていません。"
        _append_once(actions, "rewrite:fallback_generic")
    return rewritten, actions



def _collect_quality_flags(text: str) -> List[str]:
    s = _collapse_ws(text)
    flags: List[str] = []
    if not s:
        _append_once(flags, "quality:empty")
        return flags
    if len(s) < 8:
        _append_once(flags, "quality:too_short")
    lowered = s.rstrip("。！？!? ")
    compact = lowered.replace(" ", "")
    if lowered in _BAD_EXACTS:
        _append_once(flags, "quality:noun_only")
    if _SHORT_PARTICLE_TAIL_RE.search(lowered):
        _append_once(flags, "quality:unfinished")
    if lowered.startswith(("でも", "ただ", "は")) and len(lowered) < 24:
        _append_once(flags, "quality:broken_answer")
    if _is_low_quality_core_phrase(lowered):
        _append_once(flags, "quality:broken_answer")
    if re.search(r"(?:だ|です)です$", compact):
        _append_once(flags, "quality:broken_answer")
    if re.search(r"(?:今まで|今の|さっきまで)?私(?:は|が)?です$", compact):
        _append_once(flags, "quality:broken_answer")
    if re.search(r"(?:自分|私自身)(?:は|が)?です$", compact):
        _append_once(flags, "quality:broken_answer")
    return flags



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
    format_version: str = GENERATED_REFLECTION_DISPLAY_VERSION

    def as_storage_meta(self) -> Dict[str, Any]:
        display_text = str(self.answer_display_text or "")
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
    rewritten, rewrite_actions = compose_generated_answer_raw(
        question=question,
        raw_answer=raw,
        category=category,
        focus_key=focus_key,
        topic_summary_text=topic_summary_text,
        text_candidates=text_candidates,
    )
    safety = format_reflection_text(rewritten or raw)
    flags = _ordered_unique([*_collect_quality_flags(str(safety.display_text or rewritten or "")), *safety.flags])
    actions = _ordered_unique([*rewrite_actions, *safety.actions])
    norm_source = safety.display_text if safety.display_text is not None else (rewritten or raw)
    changed = bool(raw != rewritten or safety.changed or actions)
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
        answer_display_text=safety.display_text,
        answer_display_state=str(safety.display_state),
        changed=changed,
        flags=flags,
        actions=actions,
        answer_norm_hash=compute_generated_answer_norm_hash(norm_source),
        display_source_signature=source_signature,
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
        flags=_ordered_unique(flags),
        actions=_ordered_unique(actions),
        answer_norm_hash=norm_hash,
        display_source_signature=display_source_signature,
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
    "compose_generated_answer_raw",
    "compute_generated_answer_norm_hash",
    "compute_generated_display_source_signature",
    "get_public_generated_reflection_text",
    "resolve_generated_reflection_display",
]
