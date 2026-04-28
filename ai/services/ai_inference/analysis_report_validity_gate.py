from __future__ import annotations

"""Validity gate for Cocolon's Analysis core reports.

This module is intentionally deterministic and additive.  It does not rewrite
report text and it does not decide access policy; it records whether the
analysis artifact has enough owned material and whether the generated display
payload stays within Cocolon's non-diagnostic observation boundary.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence

ANALYSIS_REPORT_VALIDITY_SCHEMA_VERSION = "analysis.validity.v1"

ANALYSIS_DOMAIN_EMOTION = "emotion_structure"
ANALYSIS_DOMAIN_SELF_STRUCTURE = "self_structure"

_DOMAIN_ALIASES = {
    "emotion": ANALYSIS_DOMAIN_EMOTION,
    "emotion_structure": ANALYSIS_DOMAIN_EMOTION,
    "myweb": ANALYSIS_DOMAIN_EMOTION,
    "analysis": ANALYSIS_DOMAIN_EMOTION,
    "self": ANALYSIS_DOMAIN_SELF_STRUCTURE,
    "self_structure": ANALYSIS_DOMAIN_SELF_STRUCTURE,
    "myprofile": ANALYSIS_DOMAIN_SELF_STRUCTURE,
}

_DIAGNOSIS_TERMS = (
    "うつ病",
    "鬱病",
    "双極性障害",
    "発達障害",
    "adhd",
    "asd",
    "ptsd",
    "パーソナリティ障害",
    "境界性",
    "病気です",
    "診断できます",
    "diagnosis",
    "disorder",
)

_OVERCLAIM_TERMS = (
    "必ず",
    "絶対に",
    "完全に",
    "断定できます",
    "間違いなく",
    "本当の性格",
    "あなたの本質は",
    "全て説明できます",
)

_SELF_STRUCTURE_MATERIAL_FIELDS = {
    "target_hint",
    "target",
    "role_hint",
    "role",
    "thinking",
    "thinking_signals",
    "action",
    "action_signals",
    "text_secondary",
    "memo_action",
    "question_text",
    "text_primary",
}

_EMOTION_ALLOWED_MATERIAL_FIELDS = {
    "emotion_details",
    "emotions",
    "emotion_signals",
    "emotion",
    "label",
    "intensity",
    "strength",
    "timestamp",
    "created_at",
    "memo",
    "category",
    "categories",
}

_EMOTION_FORBIDDEN_MATERIAL_FIELDS = {"memo_action", "action_text", "action_signals", "role_hint", "target_hint"}


def _safe_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def normalize_analysis_domain(domain: Any) -> str:
    raw = _safe_str(domain).lower()
    if not raw:
        return ANALYSIS_DOMAIN_EMOTION
    return _DOMAIN_ALIASES.get(raw, raw)


def _normalize_field_names(values: Optional[Iterable[Any]]) -> set[str]:
    out: set[str] = set()
    for raw in values or []:
        s = _safe_str(raw)
        if s:
            out.add(s)
    return out


def _extract_text_values(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        s = value.strip()
        return [s] if s else []
    if isinstance(value, Mapping):
        out: list[str] = []
        for item in value.values():
            out.extend(_extract_text_values(item))
        return out
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        out: list[str] = []
        for item in value:
            out.extend(_extract_text_values(item))
        return out
    s = _safe_str(value)
    return [s] if s else []


def _contains_any(text: str, terms: Iterable[str]) -> bool:
    lowered = text.lower()
    return any(str(term).lower() in lowered for term in terms if str(term or "").strip())


@dataclass(frozen=True)
class AnalysisReportValidityResult:
    domain: str
    material_count: int
    material_sufficient: bool
    domain_separated: bool
    diagnosis_checked: bool
    overclaim_checked: bool
    display_valid: bool
    save_allowed: bool
    blocked_reasons: list[str] = field(default_factory=list)
    material_fields: list[str] = field(default_factory=list)
    target_period: Optional[str] = None
    schema_version: str = ANALYSIS_REPORT_VALIDITY_SCHEMA_VERSION

    def as_meta(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "domain": self.domain,
            "target_period": self.target_period,
            "material_count": self.material_count,
            "material_sufficient": self.material_sufficient,
            "domain_separated": self.domain_separated,
            "diagnosis_checked": self.diagnosis_checked,
            "overclaim_checked": self.overclaim_checked,
            "display_valid": self.display_valid,
            "save_allowed": self.save_allowed,
            "blocked_reasons": list(self.blocked_reasons),
            "material_fields": list(self.material_fields),
        }


def evaluate_analysis_report_validity(
    *,
    domain: Any,
    material_count: Any,
    output_text: Any = None,
    output_payload: Any = None,
    material_fields: Optional[Iterable[Any]] = None,
    target_period: Any = None,
    save_requested: bool = True,
    min_material_count: Optional[int] = None,
) -> AnalysisReportValidityResult:
    """Evaluate whether an analysis artifact is valid to save/display.

    The gate is conservative and additive: callers can store the returned meta
    under ``content_json.reportValidity`` without changing legacy payloads.
    """

    normalized_domain = normalize_analysis_domain(domain)
    try:
        count = max(0, int(material_count or 0))
    except Exception:
        count = 0

    required_count = 1 if min_material_count is None else max(0, int(min_material_count or 0))
    fields = _normalize_field_names(material_fields)
    reasons: list[str] = []

    material_sufficient = count >= required_count
    if not material_sufficient:
        reasons.append("material_insufficient")

    domain_separated = True
    if normalized_domain == ANALYSIS_DOMAIN_EMOTION:
        forbidden = sorted(fields.intersection(_EMOTION_FORBIDDEN_MATERIAL_FIELDS))
        if forbidden:
            domain_separated = False
            reasons.append("emotion_domain_contains_self_structure_material")
    elif normalized_domain == ANALYSIS_DOMAIN_SELF_STRUCTURE:
        if fields and not fields.intersection(_SELF_STRUCTURE_MATERIAL_FIELDS):
            domain_separated = False
            reasons.append("self_structure_material_boundary_missing")

    text_values = _extract_text_values(output_text) + _extract_text_values(output_payload)
    joined_text = "\n".join(text_values)
    text_present = bool(joined_text.strip())

    diagnosis_checked = not _contains_any(joined_text, _DIAGNOSIS_TERMS)
    if not diagnosis_checked:
        reasons.append("diagnosis_like_output")

    overclaim_checked = not _contains_any(joined_text, _OVERCLAIM_TERMS)
    if not overclaim_checked:
        reasons.append("overclaim_output")

    display_valid = True
    if save_requested:
        display_valid = text_present
        if not display_valid:
            reasons.append("display_output_empty")

    save_allowed = bool(material_sufficient and domain_separated and diagnosis_checked and overclaim_checked and display_valid)

    return AnalysisReportValidityResult(
        domain=normalized_domain,
        material_count=count,
        material_sufficient=material_sufficient,
        domain_separated=domain_separated,
        diagnosis_checked=diagnosis_checked,
        overclaim_checked=overclaim_checked,
        display_valid=display_valid,
        save_allowed=save_allowed,
        blocked_reasons=reasons,
        material_fields=sorted(fields),
        target_period=_safe_str(target_period) or None,
    )


def attach_report_validity_meta(
    content_json: Optional[Mapping[str, Any]],
    result: AnalysisReportValidityResult,
) -> Dict[str, Any]:
    base = dict(content_json or {})
    base["reportValidity"] = result.as_meta()
    return base


def infer_emotion_material_fields_from_rows(rows: Optional[Sequence[Mapping[str, Any]]]) -> list[str]:
    fields: set[str] = set()
    for row in rows or []:
        if not isinstance(row, Mapping):
            continue
        for key in row.keys():
            if key in _EMOTION_ALLOWED_MATERIAL_FIELDS or key in _EMOTION_FORBIDDEN_MATERIAL_FIELDS:
                fields.add(str(key))
    return sorted(fields)


def infer_self_structure_material_fields_from_items(items: Optional[Sequence[Any]]) -> list[str]:
    fields: set[str] = set()
    for item in items or []:
        raw: Mapping[str, Any]
        if isinstance(item, Mapping):
            raw = item
            keys = raw.keys()
        else:
            keys = (
                "target_hint",
                "role_hint",
                "text_primary",
                "text_secondary",
                "action_signals",
                "emotion_signals",
                "question_text",
            )
            raw = {key: getattr(item, key, None) for key in keys}
        for key, value in raw.items():
            if key in _SELF_STRUCTURE_MATERIAL_FIELDS and value not in (None, "", [], {}):
                fields.add(str(key))
    return sorted(fields)


__all__ = [
    "ANALYSIS_REPORT_VALIDITY_SCHEMA_VERSION",
    "ANALYSIS_DOMAIN_EMOTION",
    "ANALYSIS_DOMAIN_SELF_STRUCTURE",
    "AnalysisReportValidityResult",
    "attach_report_validity_meta",
    "evaluate_analysis_report_validity",
    "infer_emotion_material_fields_from_rows",
    "infer_self_structure_material_fields_from_items",
    "normalize_analysis_domain",
]
