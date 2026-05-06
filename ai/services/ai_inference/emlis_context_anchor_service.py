# -*- coding: utf-8 -*-
from __future__ import annotations

"""Shared helpers for EmlisAI cross-core context anchors.

The user-facing Piece / report text stays the canonical artifact.  This module
only stores and reads short, explainable anchors that can be traced back to that
visible artifact.  Anchors are intentionally conservative and small; they are not
second long reports and they are not hidden personality claims.
"""

from copy import deepcopy
import re
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

EMLIS_CONTEXT_ANCHOR_SCHEMA_VERSION = "emlis_context_anchor.v1"
EMLIS_CONTEXT_ANCHORS_KEY = "emlis_context_anchors"

_SAFETY_META = {
    "user_visible_basis_required": True,
    "current_input_priority": True,
    "no_hidden_personality_claim": True,
}

_VALUE_TERMS = (
    "大切", "大事", "守りたい", "安心", "納得", "信頼", "自由", "限界", "責任",
    "迷惑", "怖", "不安", "願", "幸せ", "好き", "楽し", "期待", "傷", "努力",
)
_BOUNDARY_TERMS = ("限界", "無理", "断", "距離", "境界", "我慢", "踏み込", "守り")
_ROLE_TERMS = ("役割", "支え", "助け", "整理", "向き合", "責任", "選", "行動", "環境", "対象")
_EMOTION_TERMS = ("喜び", "悲しみ", "怒り", "不安", "平穏", "恐れ", "焦り", "落ち着き", "安心")
_GENERIC_STOP_TERMS = {
    "こと", "気持ち", "思い", "状態", "今日", "最近", "自分", "あなた", "入力", "感情", "レポート", "分析",
}


def _clean(value: Any, *, limit: int = 240) -> str:
    text = re.sub(r"\s+", " ", str(value or "").strip())
    if limit > 0 and len(text) > limit:
        return text[:limit].rstrip() + "…"
    return text


def _compact(value: Any) -> str:
    return re.sub(r"[\s　、,。.!！?？\t\n\r『』「」（）()\[\]【】]", "", str(value or ""))


def _as_list(value: Any) -> List[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if value is None:
        return []
    return [value]


def _dict(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _take_texts(values: Iterable[Any], *, limit: int = 6) -> List[str]:
    out: List[str] = []
    for value in values or []:
        text = _clean(value, limit=120)
        if text and text not in out:
            out.append(text)
        if len(out) >= limit:
            break
    return out


def _merge_unique(*groups: Sequence[Any], limit: int = 10) -> List[str]:
    out: List[str] = []
    for group in groups:
        for value in group or []:
            text = _clean(value, limit=96)
            if not text or text in out:
                continue
            out.append(text)
            if len(out) >= limit:
                return out
    return out


def _contains_any(text: Any, terms: Sequence[str]) -> bool:
    compact = _compact(text)
    return any(term and term in compact for term in terms)


def _extract_terms_from_text(text: Any, *, preferred: Sequence[str] = (), limit: int = 8) -> List[str]:
    raw = _clean(text, limit=500)
    compact = _compact(raw)
    out: List[str] = []
    for term in preferred:
        if term and term in compact and term not in out:
            out.append(term)
    for chunk in re.split(r"[、,。.!！?？\s　『』「」（）()\[\]【】]+", raw):
        part = chunk.strip()
        if not part:
            continue
        if part in _GENERIC_STOP_TERMS:
            continue
        if 2 <= len(part) <= 18 and part not in out:
            out.append(part)
        if len(out) >= limit:
            break
    return out[:limit]


def _evidence_ref(kind: str, ref_id: Any, note: Optional[str] = None) -> Dict[str, Any]:
    return {
        "kind": _clean(kind, limit=40),
        "ref_id": _clean(ref_id, limit=120) or "pending",
        "note": _clean(note, limit=160) or None,
    }


def _base_packet(*, source_kind: str, source_id: Any = None, evidence_note: Optional[str] = None) -> Dict[str, Any]:
    source_kind_clean = _clean(source_kind, limit=48) or "unknown"
    source_id_clean = _clean(source_id, limit=120) or None
    return {
        "schema_version": EMLIS_CONTEXT_ANCHOR_SCHEMA_VERSION,
        "source_kind": source_kind_clean,
        "source_id": source_id_clean,
        "value_anchors": [],
        "state_anchors": [],
        "individuality_anchors": [],
        "boundary_anchors": [],
        "concept_anchors": [],
        "reply_hints": [],
        "evidence_refs": [_evidence_ref(source_kind_clean, source_id_clean or "pending", evidence_note)],
        "safety": dict(_SAFETY_META),
    }


def _normalize_confidence(value: Any, default: float = 0.62) -> float:
    try:
        number = float(value)
    except Exception:
        number = default
    return max(0.0, min(1.0, number))


def _reply_hints_from_text(text: Any, *, source_kind: str) -> List[Dict[str, Any]]:
    compact = _compact(text)
    hints: List[str] = []
    if any(term in compact for term in ("怖", "不安", "傷", "期待", "裏切")):
        hints.append("怖さや不安を責めず、現在入力を優先して受け止める")
    if any(term in compact for term in _BOUNDARY_TERMS):
        hints.append("境界線や限界の確認を急がせず、選択肢を狭めない")
    if any(term in compact for term in ("幸せ", "願", "好き", "楽し", "大切")):
        hints.append("願いや大切にしたいものを小さく扱わない")
    if source_kind == "emotion_report":
        hints.append("感情の推移は断定せず、直近の状態として扱う")
    if source_kind == "self_structure_report":
        hints.append("役割や行動傾向を固定せず、今の入力を最優先にする")
    if not hints:
        hints.append("過去資料は決めつけではなく、言葉選びの補助としてだけ扱う")
    return [{"hint": hint} for hint in _merge_unique(hints, limit=4)]


def build_piece_emlis_context_anchors(
    *,
    question: Any,
    answer: Any,
    category: Any = None,
    source_id: Any = None,
    source_kind: str = "piece",
    emotion_input: Optional[Mapping[str, Any]] = None,
    focus_key: Any = None,
    source_refs: Optional[Sequence[Mapping[str, Any]]] = None,
) -> Dict[str, Any]:
    """Build a short anchor packet from the user-visible Piece question/answer."""
    q = _clean(question, limit=220)
    a = _clean(answer, limit=420)
    cat_values = _take_texts(_as_list(category), limit=4)
    emotion_payload = _dict(emotion_input)
    emotion_labels: List[str] = []
    for item in _as_list(emotion_payload.get("emotions")):
        if isinstance(item, Mapping):
            label = item.get("type") or item.get("emotion_type") or item.get("emotion")
        else:
            label = item
        label_text = _clean(label, limit=32)
        if label_text and label_text not in emotion_labels:
            emotion_labels.append(label_text)
    trigger_conditions = _merge_unique(cat_values, emotion_labels, _extract_terms_from_text(q, preferred=_VALUE_TERMS, limit=4), limit=8)
    packet = _base_packet(source_kind=source_kind, source_id=source_id, evidence_note="ユーザー向けPieceの問いと答えから作成")
    combined = " ".join([q, a, " ".join(cat_values)])

    label_terms = _extract_terms_from_text(combined, preferred=_VALUE_TERMS, limit=5)
    label = label_terms[0] if label_terms else (q or "Pieceの問い")
    if q or a:
        packet["value_anchors"].append(
            {
                "label": _clean(label, limit=80),
                "user_definition": a or q,
                "trigger_conditions": trigger_conditions,
                "confidence": _normalize_confidence(0.72 if a else 0.58),
                "evidence_refs": [_evidence_ref(source_kind, source_id or _clean(focus_key, limit=80) or "piece", "question_answer")],
            }
        )
    if _contains_any(combined, _BOUNDARY_TERMS):
        packet["boundary_anchors"].append(
            {
                "label": "境界線・限界に関わる言葉",
                "user_definition": a or q,
                "trigger_conditions": trigger_conditions,
                "confidence": 0.66,
                "evidence_refs": [_evidence_ref(source_kind, source_id or "piece", "boundary_terms")],
            }
        )
    if q:
        packet["concept_anchors"].append(
            {
                "label": q,
                "answer_summary": a,
                "focus_key": _clean(focus_key, limit=80) or None,
                "confidence": 0.64,
                "evidence_refs": [_evidence_ref(source_kind, source_id or "piece", "visible_question")],
            }
        )
    packet["reply_hints"] = _reply_hints_from_text(combined, source_kind="piece")
    if source_refs:
        packet["evidence_refs"].extend(
            _evidence_ref("source_ref", ref.get("id") or ref.get("ref_id") or ref.get("source_id") or idx, ref.get("note"))
            for idx, ref in enumerate(source_refs[:4])
            if isinstance(ref, Mapping)
        )
    return prune_empty_anchor_packet(packet)


def _section_texts(report: Mapping[str, Any]) -> List[str]:
    texts: List[str] = []
    headline = _clean(report.get("headline"), limit=180)
    if headline:
        texts.append(headline)
    for section in _as_list(report.get("sections")):
        if not isinstance(section, Mapping):
            continue
        title = _clean(section.get("title"), limit=80)
        text = _clean(section.get("text"), limit=360)
        if title:
            texts.append(title)
        if text:
            texts.append(text)
        for item in _as_list(section.get("items")):
            if not isinstance(item, Mapping):
                continue
            item_text = _clean(item.get("text") or item.get("relative_desc") or item.get("label"), limit=220)
            if item_text:
                texts.append(item_text)
    return _take_texts(texts, limit=12)


def build_emotion_report_emlis_context_anchors(
    *,
    report: Optional[Mapping[str, Any]] = None,
    content_json: Optional[Mapping[str, Any]] = None,
    source_id: Any = None,
    report_type: Any = None,
    period: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Build state anchors from an emotion analysis report payload."""
    cj = _dict(content_json)
    report_payload = _dict(report) or _dict(cj.get("deepReport")) or _dict(cj.get("standardReport")) or _dict(cj.get("astorReport"))
    astor_text = _clean(cj.get("astorText"), limit=520)
    packet = _base_packet(source_kind="emotion_report", source_id=source_id, evidence_note="ユーザー向け感情分析レポートから作成")
    period_payload = _dict(period) or _dict(report_payload.get("period"))
    section_texts = _section_texts(report_payload)
    combined = " ".join([astor_text, " ".join(section_texts), _clean(cj.get("content_text"), limit=360)])
    metrics = _dict(cj.get("metrics"))

    top_labels: List[str] = []
    for source in (metrics.get("top_emotions"), metrics.get("top"), metrics.get("emotion_counts")):
        if isinstance(source, Mapping):
            for key in source.keys():
                label = _clean(key, limit=40)
                if label and label not in top_labels:
                    top_labels.append(label)
        else:
            for item in _as_list(source):
                if isinstance(item, (list, tuple)) and item:
                    label = _clean(item[0], limit=40)
                elif isinstance(item, Mapping):
                    label = _clean(item.get("label") or item.get("emotion") or item.get("type"), limit=40)
                else:
                    label = _clean(item, limit=40)
                if label and label not in top_labels:
                    top_labels.append(label)
    top_labels = top_labels[:4]
    movement_terms = _extract_terms_from_text(combined, preferred=_EMOTION_TERMS, limit=6)
    state_label = top_labels[0] if top_labels else (movement_terms[0] if movement_terms else "感情の推移")
    packet["state_anchors"].append(
        {
            "label": state_label,
            "emotion_cycle": _clean(section_texts[0] if section_texts else astor_text, limit=220) or None,
            "frequency": _clean(metrics.get("density") or metrics.get("frequency") or "", limit=80) or None,
            "recent_change": _clean(report_payload.get("headline") or astor_text or combined, limit=220) or None,
            "sensitive_contexts": _merge_unique(top_labels, movement_terms, limit=8),
            "period": dict(period_payload or {}),
            "confidence": 0.66 if combined or top_labels else 0.48,
            "evidence_refs": [_evidence_ref("emotion_report", source_id or _clean(report_type, limit=60) or "report", "visible_report")],
        }
    )
    packet["reply_hints"] = _reply_hints_from_text(combined, source_kind="emotion_report")
    return prune_empty_anchor_packet(packet)


def build_self_structure_report_emlis_context_anchors(
    *,
    content_json: Optional[Mapping[str, Any]] = None,
    source_id: Any = None,
    report_type: Any = None,
) -> Dict[str, Any]:
    """Build individuality anchors from a self-structure report content_json."""
    cj = _dict(content_json)
    packet = _base_packet(source_kind="self_structure_report", source_id=source_id, evidence_note="ユーザー向け自己分析レポートから作成")
    sections = _dict(cj.get("sections"))
    summary = _clean(cj.get("summaryText") or cj.get("summary_text"), limit=360)
    role_lines = _take_texts(_as_list(sections.get("role_content")) + _as_list(sections.get("current_structure")), limit=4)
    background_lines = _take_texts(_as_list(sections.get("role_background")), limit=3)
    reaction_lines = _take_texts(_as_list(sections.get("reaction_flow")), limit=3)
    emotion_lines = _take_texts(_as_list(sections.get("emotion_bridge")), limit=3)
    combined = " ".join([summary, " ".join(role_lines + background_lines + reaction_lines + emotion_lines)])
    if summary or role_lines or reaction_lines:
        packet["individuality_anchors"].append(
            {
                "label": _clean(summary or (role_lines[0] if role_lines else "役割・行動傾向"), limit=120),
                "role_pattern": _clean(" / ".join(role_lines), limit=280) or None,
                "environment_context": _clean(" / ".join(background_lines), limit=240) or None,
                "choice_pattern": _clean(" / ".join(reaction_lines), limit=240) or None,
                "target_context": _clean(" / ".join(emotion_lines), limit=240) or None,
                "confidence": 0.66 if combined else 0.48,
                "evidence_refs": [_evidence_ref("self_structure_report", source_id or _clean(report_type, limit=60) or "report", "visible_report")],
            }
        )
    if _contains_any(combined, _ROLE_TERMS):
        packet["concept_anchors"].append(
            {
                "label": "役割・環境・選択傾向",
                "answer_summary": _clean(combined, limit=320),
                "confidence": 0.60,
                "evidence_refs": [_evidence_ref("self_structure_report", source_id or "report", "role_terms")],
            }
        )
    packet["reply_hints"] = _reply_hints_from_text(combined, source_kind="self_structure_report")
    return prune_empty_anchor_packet(packet)


def prune_empty_anchor_packet(packet: Mapping[str, Any]) -> Dict[str, Any]:
    out = dict(packet or {})
    for key in ("value_anchors", "state_anchors", "individuality_anchors", "boundary_anchors", "concept_anchors", "reply_hints", "evidence_refs"):
        value = out.get(key)
        if isinstance(value, list):
            out[key] = [item for item in value if item]
        else:
            out[key] = []
    if not any(out.get(key) for key in ("value_anchors", "state_anchors", "individuality_anchors", "boundary_anchors", "concept_anchors", "reply_hints")):
        out["reply_hints"] = [{"hint": "過去資料は決めつけではなく、言葉選びの補助としてだけ扱う"}]
    out["schema_version"] = EMLIS_CONTEXT_ANCHOR_SCHEMA_VERSION
    out["safety"] = {**_SAFETY_META, **_dict(out.get("safety"))}
    return out


def attach_emlis_context_anchors(content_json: Mapping[str, Any], packet: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    updated = dict(content_json or {})
    if not packet:
        return updated
    normalized = prune_empty_anchor_packet(packet)
    updated[EMLIS_CONTEXT_ANCHORS_KEY] = normalized
    return updated


def extract_emlis_context_anchors(content_json: Any) -> List[Dict[str, Any]]:
    source = _dict(content_json)
    raw = source.get(EMLIS_CONTEXT_ANCHORS_KEY)
    if isinstance(raw, Mapping):
        return [prune_empty_anchor_packet(raw)]
    if isinstance(raw, list):
        return [prune_empty_anchor_packet(item) for item in raw if isinstance(item, Mapping)]
    return []


def sanitize_content_json_for_public_read(raw: Any) -> Dict[str, Any]:
    """Remove internal EmlisAI anchor payloads from public/user read responses."""
    if not isinstance(raw, Mapping):
        return {}

    def _sanitize(value: Any) -> Any:
        if isinstance(value, Mapping):
            return {
                str(k): _sanitize(v)
                for k, v in value.items()
                if str(k) != EMLIS_CONTEXT_ANCHORS_KEY
            }
        if isinstance(value, list):
            return [_sanitize(item) for item in value]
        return deepcopy(value)

    sanitized = _sanitize(raw)
    return sanitized if isinstance(sanitized, dict) else {}


def packet_anchor_count(packet: Mapping[str, Any]) -> int:
    return sum(
        len(packet.get(key) if isinstance(packet.get(key), list) else [])
        for key in ("value_anchors", "state_anchors", "individuality_anchors", "boundary_anchors", "concept_anchors", "reply_hints")
    )


def packet_text_for_matching(packet: Mapping[str, Any]) -> str:
    parts: List[str] = []
    for key in ("value_anchors", "state_anchors", "individuality_anchors", "boundary_anchors", "concept_anchors", "reply_hints"):
        for item in _as_list(packet.get(key)):
            if not isinstance(item, Mapping):
                continue
            for v in item.values():
                if isinstance(v, (str, int, float)):
                    parts.append(str(v))
                elif isinstance(v, list):
                    parts.extend(str(x) for x in v if isinstance(x, (str, int, float)))
    return " ".join(parts)


__all__ = [
    "EMLIS_CONTEXT_ANCHOR_SCHEMA_VERSION",
    "EMLIS_CONTEXT_ANCHORS_KEY",
    "attach_emlis_context_anchors",
    "build_emotion_report_emlis_context_anchors",
    "build_piece_emlis_context_anchors",
    "build_self_structure_report_emlis_context_anchors",
    "extract_emlis_context_anchors",
    "packet_anchor_count",
    "packet_text_for_matching",
    "prune_empty_anchor_packet",
    "sanitize_content_json_for_public_read",
]
