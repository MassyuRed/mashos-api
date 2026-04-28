# -*- coding: utf-8 -*-
"""EmlisAI quality gate for the new national core system.

The gate is intentionally additive: it records whether the immediate reply kept
EmlisAI inside its contract without rewriting ``input_feedback.comment_text``.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Dict, Mapping, Sequence

EMLIS_AI_QUALITY_GATE_SCHEMA_VERSION = "emlis.quality.v1"

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


def evaluate_emlis_ai_quality_gate(
    *,
    comment_text: Any,
    capability: Any,
    used_sources: Sequence[Any],
    evidence_by_line: Mapping[str, Any] | None,
    fallback_used: bool,
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
    reply_length_within_limit = _line_count(text) <= max_reply_lines

    capability_profile = {
        "tier": tier,
        "history_mode": history_mode,
        "model_mode": str(getattr(capability, "model_mode", "off") or "off"),
        "interpretation_mode": str(getattr(capability, "interpretation_mode", "current_only") or "current_only"),
        "source_scope": source_scope,
        "cross_core_enabled": bool(getattr(capability, "cross_core_enabled", False)),
        "structure_model_enabled": bool(getattr(capability, "structure_model_enabled", False)),
        "max_reply_lines": max_reply_lines,
    }
    passed = all(
        [
            current_input_central,
            history_allowed,
            evidence_required_satisfied,
            overclaim_suppressed,
            diagnosis_blocked,
            reply_length_within_limit,
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
    gate = evaluate_emlis_ai_quality_gate(
        comment_text=comment_text,
        capability=capability,
        used_sources=used_sources,
        evidence_by_line=evidence_by_line,
        fallback_used=fallback_used,
    )
    capability_meta = dict(updated.get("capability") or {}) if isinstance(updated.get("capability"), dict) else {}
    capability_meta.update(gate.capability_profile)
    updated["capability"] = capability_meta
    updated["quality_gate"] = gate.as_meta()
    return updated


__all__ = [
    "EMLIS_AI_QUALITY_GATE_SCHEMA_VERSION",
    "EmlisAIQualityGateResult",
    "attach_emlis_ai_quality_gate_meta",
    "evaluate_emlis_ai_quality_gate",
]
