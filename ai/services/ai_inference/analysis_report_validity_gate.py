from __future__ import annotations

"""Validity gate for Cocolon's Analysis core reports.

This module is intentionally deterministic and additive.  It does not rewrite
report text and it does not decide access policy; it records whether the
analysis artifact has enough owned material and whether the generated display
payload stays within Cocolon's non-diagnostic observation boundary.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence

# Optional Phase12: common text-generation core for Analysis reports.
try:
    from cocolon_text_generation_core.adapters.analysis_composer import (
        ADAPTER_NAME as ANALYSIS_COMPOSER_ADAPTER_NAME,
        ANALYSIS_COMPOSER_META_KEY,
        ANALYSIS_COMPOSER_MODEL,
        PHASE_LABEL as ANALYSIS_COMPOSER_PHASE_LABEL,
        REJECTION_ANALYSIS_COMMON_TEXT_SAFETY_REJECTED,
        evaluate_analysis_composer,
        evaluate_analysis_report_text_safety,
    )
    from cocolon_text_generation_core.adapters.analysis_composer_input_contract import TEXT_GENERATION_META_KEY
except Exception:  # pragma: no cover
    ANALYSIS_COMPOSER_ADAPTER_NAME = "analysis_composer.unavailable"  # type: ignore
    ANALYSIS_COMPOSER_META_KEY = "analysis_composer"  # type: ignore
    ANALYSIS_COMPOSER_MODEL = "cocolon_text_generation_core.analysis_composer.v1"  # type: ignore
    ANALYSIS_COMPOSER_PHASE_LABEL = "phase12_analysis_composer_unavailable"  # type: ignore
    REJECTION_ANALYSIS_COMMON_TEXT_SAFETY_REJECTED = "analysis_common_text_safety_rejected"  # type: ignore
    TEXT_GENERATION_META_KEY = "textGenerationCore"  # type: ignore
    evaluate_analysis_composer = None  # type: ignore
    evaluate_analysis_report_text_safety = None  # type: ignore

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
    "いつも",
    "原因です",
    "原因は",
    "戻りやすい",
    "回復方法",
    "治ります",
    "治る",
    "処方",
    "対処法です",
    "解決策です",
    "今回の入力では",
    "今回の入力",
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
    "value_observation_signals",
    "value_observation_signal_keys",
    "value_observation_plan",
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

_EMOTION_FORBIDDEN_MATERIAL_FIELDS = {
    "memo_action",
    "action_text",
    "action_signals",
    "role_hint",
    "target_hint",
    "value_observation_signals",
    "value_observation_signal_keys",
    "value_observation_plan",
}


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


def _extract_value_observation_signal_keys(payload: Any) -> list[str]:
    if not isinstance(payload, Mapping):
        return []
    raw_signals = payload.get("value_observation_signals") or payload.get("valueObservationSignals")
    raw_keys = payload.get("value_observation_signal_keys") or payload.get("valueObservationSignalKeys")
    out: list[str] = []
    for item in list(raw_keys or []):
        s = _safe_str(item)
        if s and s not in out:
            out.append(s)
    if isinstance(raw_signals, Sequence) and not isinstance(raw_signals, (str, bytes, bytearray)):
        for item in raw_signals:
            if isinstance(item, Mapping):
                key = item.get("signal_key") or item.get("key")
            else:
                key = getattr(item, "signal_key", None)
            s = _safe_str(key)
            if s and s not in out:
                out.append(s)
    return out


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
    value_observation_signal_keys: list[str] = field(default_factory=list)
    value_observation_domain_ok: bool = True
    text_generation_core_checked: bool = False
    text_generation_core_passed: bool = False
    text_generation_core_meta: Dict[str, Any] = field(default_factory=dict)
    analysis_composer_connected: bool = False
    target_period: Optional[str] = None
    schema_version: str = ANALYSIS_REPORT_VALIDITY_SCHEMA_VERSION

    @property
    def analysis_text_generation_checked(self) -> bool:
        return bool(self.text_generation_core_checked)

    @property
    def analysis_text_generation_passed(self) -> bool:
        return bool(self.text_generation_core_passed)

    @property
    def analysis_text_generation_meta(self) -> Dict[str, Any]:
        return dict(self.text_generation_core_meta)

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
            "value_observation_signal_keys": list(self.value_observation_signal_keys),
            "value_observation_domain_ok": bool(self.value_observation_domain_ok),
            "text_generation_core_checked": bool(self.text_generation_core_checked),
            "text_generation_core_passed": bool(self.text_generation_core_passed),
            "analysis_text_generation_checked": bool(self.text_generation_core_checked),
            "analysis_text_generation_passed": bool(self.text_generation_core_passed),
            "analysis_composer_connected": bool(self.analysis_composer_connected),
            "analysis_text_generation": dict(self.text_generation_core_meta),
            "textGenerationCore": dict(self.text_generation_core_meta),
        }


def evaluate_analysis_report_validity(
    *,
    domain: Any,
    material_count: Any,
    output_text: Any = None,
    output_payload: Any = None,
    material_fields: Optional[Iterable[Any]] = None,
    material_sources: Optional[Iterable[Any]] = None,
    target_period: Any = None,
    save_requested: bool = True,
    min_material_count: Optional[int] = None,
    enforce_text_generation_core: bool = False,
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
    value_observation_signal_keys = _extract_value_observation_signal_keys(output_payload)
    if value_observation_signal_keys:
        fields.add("value_observation_signals")
    reasons: list[str] = []

    material_sufficient = count >= required_count
    if not material_sufficient:
        reasons.append("material_insufficient")

    domain_separated = True
    value_observation_domain_ok = True
    if normalized_domain == ANALYSIS_DOMAIN_EMOTION:
        forbidden = sorted(fields.intersection(_EMOTION_FORBIDDEN_MATERIAL_FIELDS))
        if forbidden:
            domain_separated = False
            value_observation_domain_ok = "value_observation_signals" not in forbidden
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

    text_generation_core_checked = False
    text_generation_core_passed = True
    analysis_composer_connected = False
    text_generation_core_meta: Dict[str, Any] = {
        "adapter_name": ANALYSIS_COMPOSER_ADAPTER_NAME,
        "phase": ANALYSIS_COMPOSER_PHASE_LABEL,
        "composer_model": ANALYSIS_COMPOSER_MODEL,
        "analysis_composer_available": evaluate_analysis_report_text_safety is not None,
        "analysis_composer_connected": evaluate_analysis_report_text_safety is not None,
        "validity_gate_connected": evaluate_analysis_report_text_safety is not None,
        "runtime_connected": evaluate_analysis_report_text_safety is not None,
        "checked": False,
        "passed": True,
        "enforced": True,
        "cross_core_enabled": False,
        "mode": "text_safety_only",
    }
    if evaluate_analysis_report_text_safety is not None:
        try:
            safety_result = evaluate_analysis_report_text_safety(
                joined_text,
                domain=normalized_domain,
                material_fields=fields,
                target_period=target_period,
            )
            text_generation_core_checked = True
            text_generation_core_passed = bool(safety_result.passed)
            analysis_composer_connected = True
            text_generation_core_meta.update(safety_result.as_meta())
            text_generation_core_meta.update(
                {
                    "adapter_name": ANALYSIS_COMPOSER_ADAPTER_NAME,
                    "phase": ANALYSIS_COMPOSER_PHASE_LABEL,
                    "composer_model": ANALYSIS_COMPOSER_MODEL,
                    "analysis_composer_connected": True,
                    "validity_gate_connected": True,
                    "runtime_connected": True,
                    "checked": True,
                    "passed": bool(safety_result.passed),
                    "enforced": True,
                    "cross_core_enabled": False,
                    "mode": "text_safety_only",
                }
            )
            if not safety_result.passed:
                reasons.append(REJECTION_ANALYSIS_COMMON_TEXT_SAFETY_REJECTED)
                reasons.extend(str(reason) for reason in safety_result.rejection_reasons)
        except Exception as exc:  # pragma: no cover - defensive additive meta
            text_generation_core_checked = True
            text_generation_core_passed = False
            text_generation_core_meta.update({"checked": True, "passed": False, "error": exc.__class__.__name__})
            reasons.append("analysis_text_generation_core_unavailable")

    if evaluate_analysis_composer is not None and material_sources is not None:
        try:
            evaluation = evaluate_analysis_composer(
                domain=normalized_domain,
                material_sources=material_sources,
                output_text=joined_text,
                output_payload=output_payload if isinstance(output_payload, Mapping) else None,
                material_fields=sorted(fields),
                target_period=target_period,
                source_id="analysis-report-validity-gate",
            )
            analysis_composer_connected = True
            full_meta = evaluation.as_meta()
            text_generation_core_meta["full_analysis_composer"] = full_meta
            if enforce_text_generation_core and not evaluation.passed:
                text_generation_core_passed = False
                reasons.append("analysis_text_generation_core_rejected")
        except Exception as exc:  # pragma: no cover - defensive additive meta
            text_generation_core_meta["full_analysis_composer"] = {"checked": True, "error": exc.__class__.__name__}
            if enforce_text_generation_core:
                text_generation_core_passed = False
                reasons.append("analysis_text_generation_core_unavailable")

    save_allowed = bool(
        material_sufficient
        and domain_separated
        and diagnosis_checked
        and overclaim_checked
        and display_valid
        and text_generation_core_passed
    )

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
        value_observation_signal_keys=value_observation_signal_keys,
        value_observation_domain_ok=value_observation_domain_ok,
        text_generation_core_checked=text_generation_core_checked,
        text_generation_core_passed=text_generation_core_passed,
        text_generation_core_meta=text_generation_core_meta,
        analysis_composer_connected=analysis_composer_connected,
        target_period=_safe_str(target_period) or None,
    )


def attach_report_validity_meta(
    content_json: Optional[Mapping[str, Any]],
    result: AnalysisReportValidityResult,
) -> Dict[str, Any]:
    base = dict(content_json or {})
    base["reportValidity"] = result.as_meta()
    if result.text_generation_core_meta:
        core_meta = dict(base.get(TEXT_GENERATION_META_KEY) or {}) if isinstance(base.get(TEXT_GENERATION_META_KEY), Mapping) else {}
        composer_meta = {
            "adapter_name": ANALYSIS_COMPOSER_ADAPTER_NAME,
            "phase": ANALYSIS_COMPOSER_PHASE_LABEL,
            "composer_model": ANALYSIS_COMPOSER_MODEL,
            "analysis_composer_connected": bool(result.analysis_composer_connected),
            "validity_gate_connected": bool(result.text_generation_core_checked),
            "runtime_connected": bool(result.text_generation_core_checked),
            "cross_core_enabled": False,
            "status": "passed" if result.text_generation_core_passed else "rejected",
            "rejection_reasons": list(result.text_generation_core_meta.get("rejection_reasons") or ()),
            "text_generation_result": dict(result.text_generation_core_meta),
            "content_json_shape_changed": False,
            "content_json_contract_touched": False,
            "standardReport_contract_untouched": True,
            "contentText_contract_untouched": True,
        }
        core_meta[ANALYSIS_COMPOSER_META_KEY] = composer_meta
        core_meta["analysis_report_validity_gate"] = dict(result.text_generation_core_meta)
        core_meta["analysis_composer_connected"] = bool(result.analysis_composer_connected)
        core_meta["runtime_connected"] = bool(result.text_generation_core_checked)
        core_meta["cross_core_enabled"] = False
        base[TEXT_GENERATION_META_KEY] = core_meta
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
                "value_observation_signals",
                "value_observation_signal_keys",
                "value_observation_plan",
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
