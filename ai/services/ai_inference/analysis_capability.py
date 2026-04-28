from __future__ import annotations

"""Capability profile for the Analysis core.

Plan labels can change, but the core should reason from capabilities.  These
profiles are intentionally additive and keep current plan behavior unchanged.
"""

from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class AnalysisCapabilityConfig:
    tier: str
    emotion_report_enabled: bool
    self_structure_report_enabled: bool
    deep_analysis_enabled: bool
    report_validity_gate_required: bool
    source_scope: str
    cross_core_enabled: bool = False
    max_history_days: int = 28

    def as_public_meta(self) -> Dict[str, Any]:
        return {
            "tier": self.tier,
            "emotion_report_enabled": self.emotion_report_enabled,
            "self_structure_report_enabled": self.self_structure_report_enabled,
            "deep_analysis_enabled": self.deep_analysis_enabled,
            "report_validity_gate_required": self.report_validity_gate_required,
            "source_scope": self.source_scope,
            "cross_core_enabled": self.cross_core_enabled,
            "max_history_days": self.max_history_days,
        }


def _normalize_tier(value: Any) -> str:
    raw = str(getattr(value, "value", value) or "free").strip().lower()
    if raw in {"premium", "plus", "free"}:
        return raw
    return "free"


def resolve_analysis_capability_for_tier(tier: Any) -> AnalysisCapabilityConfig:
    normalized = _normalize_tier(tier)
    if normalized == "premium":
        return AnalysisCapabilityConfig(
            tier="premium",
            emotion_report_enabled=True,
            self_structure_report_enabled=True,
            deep_analysis_enabled=True,
            report_validity_gate_required=True,
            source_scope="owned_history_snapshot",
            cross_core_enabled=False,
            max_history_days=28,
        )
    if normalized == "plus":
        return AnalysisCapabilityConfig(
            tier="plus",
            emotion_report_enabled=True,
            self_structure_report_enabled=True,
            deep_analysis_enabled=False,
            report_validity_gate_required=True,
            source_scope="owned_history_snapshot",
            cross_core_enabled=False,
            max_history_days=28,
        )
    return AnalysisCapabilityConfig(
        tier="free",
        emotion_report_enabled=True,
        self_structure_report_enabled=False,
        deep_analysis_enabled=False,
        report_validity_gate_required=True,
        source_scope="owned_current_period",
        cross_core_enabled=False,
        max_history_days=7,
    )


__all__ = ["AnalysisCapabilityConfig", "resolve_analysis_capability_for_tier"]
