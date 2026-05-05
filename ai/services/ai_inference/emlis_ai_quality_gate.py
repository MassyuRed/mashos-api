# -*- coding: utf-8 -*-
"""EmlisAI quality gate for the new national core system.

The gate is intentionally additive: it records whether the immediate reply kept
EmlisAI inside its contract without rewriting ``input_feedback.comment_text``.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Dict, Mapping, Sequence

EMLIS_AI_QUALITY_GATE_SCHEMA_VERSION = "emlis.quality.v2"

_DIAGNOSIS_OR_OVERCLAIM_RE = re.compile(
    r"(うつ病|鬱病|双極性障害|発達障害|ADHD|ASD|診断|病気です|確実に|絶対に|本質的に|あなたは.*タイプ)"
)
_HISTORY_SOURCE_KEYS = {
    "history",
    "input_summary",
    "myweb_home_summary",
    "today_question",
    "derived_user_model",
}

_EMOTION_STRENGTH_DISPLAY_RE = re.compile(r"(喜び|悲しみ|怒り|不安|平穏|自己理解|恐れ|焦り)（(?:弱|中|強)）")
_UNNATURAL_REPLY_RE = re.compile(
    r"(になるです|しているです|だったです|したです|ですです|かなぁのあと|というところが残っていた|今回いちばん残っていた言葉|中心としては.*（(?:弱|中|強)）)"
)
_MECHANICAL_META_LANGUAGE_RE = re.compile(r"(認識しています|入力として|構造として|分析すると|理解しました|受け取りました|受理しました)")
_EMPTY_ACK_LINE_RE = re.compile(r"^(?:今回は、?)?(?:書いてくれた)?(?:内容|入力|言葉|気持ち|感情).{0,18}受け取(?:り|る|ります|りました|っています).{0,4}$")
_RELATION_WORDS = ("一方で", "だけでなく", "からこそ", "重なって", "つながって", "その自分ごと", "切り離さず", "気づいていて")
_UNDERSTANDING_WORDS = ("のですね", "だったのですね", "苦しかった", "重なって", "気づいていて", "見ていた", "見ます", "軽く扱いません", "大切にします")


@dataclass(frozen=True)
class EmlisAIQualityGateResult:
    passed: bool
    current_input_central: bool
    history_allowed: bool
    evidence_required_satisfied: bool
    overclaim_suppressed: bool
    diagnosis_blocked: bool
    reply_length_within_limit: bool
    capability_profile: Dict[str, Any]
    understanding_language_ok: bool = True
    receive_repetition_ok: bool = True
    user_word_usage_ok: bool = True
    relationship_line_ok: bool = True
    empty_ack_blocked: bool = True
    mechanical_meta_language_ok: bool = True
    raw_echo_only_blocked: bool = True

    def as_meta(self) -> Dict[str, Any]:
        return {
            "schema_version": EMLIS_AI_QUALITY_GATE_SCHEMA_VERSION,
            "passed": bool(self.passed),
            "current_input_central": bool(self.current_input_central),
            "history_allowed": bool(self.history_allowed),
            "evidence_required_satisfied": bool(self.evidence_required_satisfied),
            "overclaim_suppressed": bool(self.overclaim_suppressed),
            "diagnosis_blocked": bool(self.diagnosis_blocked),
            "reply_length_within_limit": bool(self.reply_length_within_limit),
            "understanding_language_ok": bool(self.understanding_language_ok),
            "receive_repetition_ok": bool(self.receive_repetition_ok),
            "user_word_usage_ok": bool(self.user_word_usage_ok),
            "relationship_line_ok": bool(self.relationship_line_ok),
            "empty_ack_blocked": bool(self.empty_ack_blocked),
            "mechanical_meta_language_ok": bool(self.mechanical_meta_language_ok),
            "raw_echo_only_blocked": bool(self.raw_echo_only_blocked),
            "capability_profile": dict(self.capability_profile or {}),
        }


def _line_count(text: Any) -> int:
    value = str(text or "").strip()
    if not value:
        return 0
    explicit_lines = [line for line in value.splitlines() if line.strip()]
    if len(explicit_lines) > 1:
        return len(explicit_lines)
    return max(1, len([chunk for chunk in re.split(r"[。！？!?]+", value) if chunk.strip()]))


def _used_history_sources(used_sources: Sequence[Any]) -> set[str]:
    return {str(item or "").strip() for item in (used_sources or []) if str(item or "").strip()} & _HISTORY_SOURCE_KEYS


def _compact(value: Any) -> str:
    return re.sub(r"[\s　、,。.!！?？\t\n\r「」『』（）()]", "", str(value or ""))


def _anchor_terms(sample_user_word_anchors: Sequence[Any]) -> list[str]:
    terms: list[str] = []
    for item in sample_user_word_anchors or []:
        if not isinstance(item, Mapping):
            continue
        text = str(item.get("text") or "").strip()
        if not text:
            continue
        for marker in ("パーソナルスペース", "怒ると知っていながら", "自分の非", "見たくない", "嫌われ", "悲しくて不安", "連絡の頻度", "わかり合え"):
            if marker in text and marker not in terms:
                terms.append(marker)
        if len(text) <= 18 and text not in terms:
            terms.append(text)
    return terms


def _user_word_usage_ok(text: str, sample_user_word_anchors: Sequence[Any], user_word_anchor_count: int) -> bool:
    if int(user_word_anchor_count or 0) < 2:
        return True
    compact_text = _compact(text)
    terms = _anchor_terms(sample_user_word_anchors)
    if not terms:
        return True
    used = sum(1 for term in terms if _compact(term) and _compact(term) in compact_text)
    required = 2 if int(user_word_anchor_count or 0) >= 3 else 1
    return used >= required


def _relationship_line_ok(text: str, patterns: Sequence[Any]) -> bool:
    pattern_set = {str(item or "") for item in (patterns or [])}
    if not (pattern_set & {"justification_vs_fault", "rejection_fear_from_self_view", "emotion_from_conflict", "action_and_awareness"}):
        return True
    return any(word in text for word in _RELATION_WORDS)


def _raw_echo_only_blocked(text: str) -> bool:
    for line in [line.strip() for line in str(text or "").splitlines() if line.strip()]:
        if "受け取" in line and re.fullmatch(r"「[^」]{1,60}」(?:と書いてくれた)?(?:こと|ところ)?を?.{0,14}受け取(?:ります|りました|りたいです)。?", line):
            return False
    return True


def evaluate_emlis_ai_quality_gate(
    *,
    comment_text: Any,
    capability: Any,
    used_sources: Sequence[Any],
    evidence_by_line: Mapping[str, Any] | None,
    fallback_used: bool,
    allowed_line_count: int | None = None,
    sample_user_word_anchors: Sequence[Any] | None = None,
    user_word_anchor_count: int = 0,
    understanding_patterns: Sequence[Any] | None = None,
) -> EmlisAIQualityGateResult:
    tier = str(getattr(capability, "tier", "free") or "free").strip().lower()
    history_mode = str(getattr(capability, "history_mode", "none") or "none").strip().lower()
    max_reply_lines = int(getattr(capability, "max_reply_lines", 3) or 3)
    strict_evidence_mode = bool(getattr(capability, "strict_evidence_mode", True))
    source_scope = str(getattr(capability, "source_scope", "current_input_only") or "current_input_only")

    sources = [str(item or "").strip() for item in (used_sources or []) if str(item or "").strip()]
    history_sources = _used_history_sources(sources)
    current_input_central = "current_input" in set(sources)
    history_allowed = not history_sources or history_mode != "none"
    if tier == "free" and history_sources:
        history_allowed = False

    evidence_line_count = len(evidence_by_line or {})
    evidence_required_satisfied = True
    if strict_evidence_mode and not fallback_used:
        evidence_required_satisfied = evidence_line_count > 0

    text = str(comment_text or "")
    has_diagnosis_or_overclaim = bool(_DIAGNOSIS_OR_OVERCLAIM_RE.search(text))
    overclaim_suppressed = not has_diagnosis_or_overclaim
    diagnosis_blocked = not has_diagnosis_or_overclaim
    effective_max_reply_lines = int(allowed_line_count or 0) or (max_reply_lines + 1)
    reply_length_within_limit = _line_count(text) <= effective_max_reply_lines

    receive_repetition_ok = text.count("受け取") <= 1
    empty_ack_blocked = not any(_EMPTY_ACK_LINE_RE.search(line.strip()) for line in text.splitlines() if line.strip())
    mechanical_meta_language_ok = not bool(_MECHANICAL_META_LANGUAGE_RE.search(text))
    raw_echo_only_blocked = _raw_echo_only_blocked(text)
    user_word_usage_ok = _user_word_usage_ok(text, sample_user_word_anchors or [], int(user_word_anchor_count or 0))
    relationship_line_ok = _relationship_line_ok(text, understanding_patterns or [])
    understanding_language_ok = any(word in text for word in _UNDERSTANDING_WORDS) and not text.strip().endswith("理解しました。")

    capability_profile = {
        "tier": tier,
        "history_mode": history_mode,
        "model_mode": str(getattr(capability, "model_mode", "off") or "off"),
        "interpretation_mode": str(getattr(capability, "interpretation_mode", "current_only") or "current_only"),
        "source_scope": source_scope,
        "cross_core_enabled": bool(getattr(capability, "cross_core_enabled", False)),
        "structure_model_enabled": bool(getattr(capability, "structure_model_enabled", False)),
        "max_reply_lines": max_reply_lines,
        "effective_max_reply_lines": effective_max_reply_lines,
    }
    passed = all(
        [
            current_input_central,
            history_allowed,
            evidence_required_satisfied,
            overclaim_suppressed,
            diagnosis_blocked,
            reply_length_within_limit,
            understanding_language_ok,
            receive_repetition_ok,
            user_word_usage_ok,
            relationship_line_ok,
            empty_ack_blocked,
            mechanical_meta_language_ok,
            raw_echo_only_blocked,
        ]
    )
    return EmlisAIQualityGateResult(
        passed=passed,
        current_input_central=current_input_central,
        history_allowed=history_allowed,
        evidence_required_satisfied=evidence_required_satisfied,
        overclaim_suppressed=overclaim_suppressed,
        diagnosis_blocked=diagnosis_blocked,
        reply_length_within_limit=reply_length_within_limit,
        capability_profile=capability_profile,
        understanding_language_ok=understanding_language_ok,
        receive_repetition_ok=receive_repetition_ok,
        user_word_usage_ok=user_word_usage_ok,
        relationship_line_ok=relationship_line_ok,
        empty_ack_blocked=empty_ack_blocked,
        mechanical_meta_language_ok=mechanical_meta_language_ok,
        raw_echo_only_blocked=raw_echo_only_blocked,
    )


def attach_emlis_ai_quality_gate_meta(
    meta: Mapping[str, Any],
    *,
    comment_text: Any,
    capability: Any,
    fallback_used: bool,
) -> Dict[str, Any]:
    updated = dict(meta or {})
    used_sources = updated.get("used_sources") if isinstance(updated.get("used_sources"), list) else []
    evidence_by_line = updated.get("evidence_by_line") if isinstance(updated.get("evidence_by_line"), dict) else {}
    reply_depth = updated.get("reply_depth") if isinstance(updated.get("reply_depth"), dict) else {}
    anchor_summary = updated.get("anchor_summary") if isinstance(updated.get("anchor_summary"), dict) else {}
    understanding = updated.get("understanding") if isinstance(updated.get("understanding"), dict) else {}
    allowed_line_count = int(reply_depth.get("tier_ceiling") or getattr(capability, "max_reply_lines", 3) or 3) + 1
    gate = evaluate_emlis_ai_quality_gate(
        comment_text=comment_text,
        capability=capability,
        used_sources=used_sources,
        evidence_by_line=evidence_by_line,
        fallback_used=fallback_used,
        allowed_line_count=allowed_line_count,
        sample_user_word_anchors=anchor_summary.get("sample_user_word_anchors") if isinstance(anchor_summary.get("sample_user_word_anchors"), list) else [],
        user_word_anchor_count=int(anchor_summary.get("user_word_anchor_count") or 0),
        understanding_patterns=understanding.get("patterns") if isinstance(understanding.get("patterns"), list) else [],
    )
    capability_meta = dict(updated.get("capability") or {}) if isinstance(updated.get("capability"), dict) else {}
    capability_meta.update(gate.capability_profile)
    updated["capability"] = capability_meta

    reply_text = str(comment_text or "")
    strength_display_suppressed = not bool(_EMOTION_STRENGTH_DISPLAY_RE.search(reply_text))
    natural_language_ok = not bool(_UNNATURAL_REPLY_RE.search(reply_text))
    quality_meta = gate.as_meta()
    quality_meta["strength_display_suppressed"] = strength_display_suppressed
    quality_meta["natural_language_ok"] = natural_language_ok
    quality_meta["passed"] = bool(quality_meta.get("passed") and strength_display_suppressed and natural_language_ok)
    updated["quality_gate"] = quality_meta
    return updated


__all__ = [
    "EMLIS_AI_QUALITY_GATE_SCHEMA_VERSION",
    "EmlisAIQualityGateResult",
    "attach_emlis_ai_quality_gate_meta",
    "evaluate_emlis_ai_quality_gate",
]
