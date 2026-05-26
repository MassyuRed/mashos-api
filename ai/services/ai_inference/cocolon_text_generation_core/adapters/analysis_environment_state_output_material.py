# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase 7 Analysis internal material for environment/state/output observation.

This module builds Analysis-facing *internal material* from saved Cocolon input
records.  It does not generate or attach public Analysis report text.

Phase 7 scope:
- build safe single-record frame projections from saved records
- aggregate conditional output recurrence candidates over a period
- detect recovery-label path sequence candidates as observation-only material
- keep emotion/self-structure domains separated

It intentionally does not change public API routes, response keys, DB physical
names, RN display contracts, json/schema files, or Analysis content payloads.
"""

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from hashlib import sha256
import re
from typing import Any, Final

from cocolon_environment_state_output_frame import build_environment_state_output_frame

ANALYSIS_ENVIRONMENT_STATE_OUTPUT_MATERIAL_SCHEMA_VERSION: Final = "cocolon.analysis.environment_state_output_period_material.v1"
ANALYSIS_ENVIRONMENT_STATE_OUTPUT_MATERIAL_ID: Final = "analysis_environment_state_output_period_material"
CONDITIONAL_OUTPUT_TENDENCY_SCHEMA_VERSION: Final = "cocolon.conditional_output_tendency.v1"
CONDITIONAL_OUTPUT_TENDENCY_MATERIAL_ID: Final = "conditional_output_tendency"
RECOVERY_LABEL_PATH_SCHEMA_VERSION: Final = "cocolon.recovery_label_path.v1"
RECOVERY_LABEL_PATH_MATERIAL_ID: Final = "recovery_label_path"
ANALYSIS_ENVIRONMENT_STATE_OUTPUT_PHASE: Final = "Phase7_analysis_internal_tendency_material_design"

ANALYSIS_ENVIRONMENT_STATE_OUTPUT_DOMAIN: Final = "environment_state_output_period_observation"
RECURRENCE_LEVEL_NO_BASIS: Final = "no_basis"
RECURRENCE_LEVEL_SINGLE_OBSERVATION: Final = "single_observation"
RECURRENCE_LEVEL_RECURRENCE_CANDIDATE: Final = "recurrence_candidate"
RECURRENCE_LEVEL_PERIOD_TENDENCY_CANDIDATE: Final = "period_tendency_candidate"
RECURRENCE_LEVEL_STRONG_PERIOD_SIGNAL: Final = "strong_period_signal"
RECURRENCE_LEVEL_SINGLE_PATH_OBSERVATION: Final = "single_path_observation"
RECURRENCE_LEVEL_PATH_RECURRENCE_CANDIDATE: Final = "path_recurrence_candidate"

_FORBIDDEN_CLAIMS: Final = (
    "personality_type",
    "diagnosis",
    "medical_psychological_diagnosis",
    "always_claim",
    "cause_claim",
    "cause_from_category",
    "cause_from_emotion_strength",
    "treatment_or_solution_claim",
    "recovery_prescription_claim",
    "public_analysis_text_from_phase7_material",
)
_RECOVERY_FORBIDDEN_CLAIMS: Final = (
    "recovered",
    "cured",
    "this_is_the_solution",
    "treatment_claim",
    "recovery_prescription_claim",
    "personality_type",
)

_SPACE_RE: Final = re.compile(r"\s+")
_TRIM: Final = " \t\r\n　、,。.!！?？『』「」\"'"
_SELF_STRUCTURE_ONLY_FIELDS: Final = frozenset(
    {
        "text_primary",
        "text_secondary",
        "question_text",
        "answer_text",
        "answer",
        "role_hint",
        "target_hint",
        "world_kind_hint",
        "value_observation_signal_keys",
        "value_observation_signals",
        "thinking_signals",
        "action_signals",
        "social_signals",
        "analysis_tags",
    }
)
_EMOTION_LOG_FIELDS: Final = frozenset(
    {
        "id",
        "source_id",
        "created_at",
        "selected_at",
        "timestamp",
        "date",
        "memo",
        "memo_action",
        "emotion_details",
        "emotions",
        "emotion",
        "label",
        "intensity",
        "strength",
        "category",
        "categories",
    }
)
_RECOVERY_FROM_STATE_KEYS: Final = frozenset({"不安", "anxiety", "悲しみ", "sadness", "怒り", "anger", "消耗", "疲れ", "tired"})
_RECOVERY_TO_STATE_KEYS: Final = frozenset({"平穏", "peace", "calm", "安心", "喜び", "joy", "自己理解", "納得", "整理", "understanding"})
_RECOVERY_TO_OUTPUT_THEME_KEYS: Final = frozenset({"reason_became_visible"})


def _clean(value: Any, *, limit: int = 0) -> str:
    text = _SPACE_RE.sub(" ", str(value or "").replace("\r", " ").replace("\n", " ").replace("\u3000", " ")).strip(_TRIM)
    if limit > 0 and len(text) > limit:
        text = text[:limit].rstrip(_TRIM)
    return text


def _stable_hash(*parts: Any) -> str:
    value = "\0".join(_clean(part) for part in parts)
    return "sha256:" + sha256(value.encode("utf-8")).hexdigest()


def _as_mapping(record: Any) -> dict[str, Any]:
    if isinstance(record, Mapping):
        return dict(record)
    if is_dataclass(record):
        return asdict(record)
    data: dict[str, Any] = {}
    for field in _EMOTION_LOG_FIELDS | _SELF_STRUCTURE_ONLY_FIELDS:
        try:
            value = getattr(record, field)
        except Exception:
            continue
        if value not in (None, "", [], {}):
            data[field] = value
    return data


def _sequence(value: Any) -> list[Any]:
    if value in (None, ""):
        return []
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return list(value)
    return [value]


def _dict_sequence(value: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for item in _sequence(value):
        if isinstance(item, Mapping):
            out.append(dict(item))
        elif item not in (None, ""):
            out.append({"type": _clean(item)})
    return out


def _strength_from_intensity(value: Any) -> str:
    try:
        n = int(value)
    except Exception:
        return _clean(value) or "medium"
    if n >= 3:
        return "strong"
    if n <= 1:
        return "weak"
    return "medium"


def _record_field_names(data: Mapping[str, Any]) -> set[str]:
    return {str(key) for key, value in data.items() if value not in (None, "", [], {})}


def _domain_violation_for_record(data: Mapping[str, Any]) -> str:
    fields = _record_field_names(data)
    self_only = fields.intersection(_SELF_STRUCTURE_ONLY_FIELDS)
    emotion_like = fields.intersection(_EMOTION_LOG_FIELDS)
    if self_only and not emotion_like:
        return "self_structure_material_without_emotion_log_fields"
    if self_only and emotion_like:
        # Phase 7 must not silently mix self-structure source material into this
        # Analysis-period observation material.  memo_action is not part of the
        # self-only set and remains allowed as environment evidence.
        return "self_structure_material_mixed_into_environment_state_output_period_material"
    return ""


def _categories_from_record(data: Mapping[str, Any]) -> list[str]:
    values = data.get("category", None)
    if values in (None, "", [], {}):
        values = data.get("categories", None)
    out: list[str] = []
    for item in _sequence(values):
        label = _clean(item, limit=80)
        if label and label not in out:
            out.append(label)
    return out


def _emotion_details_from_record(data: Mapping[str, Any]) -> list[dict[str, Any]]:
    existing = _dict_sequence(data.get("emotion_details"))
    if existing:
        return existing
    existing = _dict_sequence(data.get("emotions"))
    if existing:
        strength = _strength_from_intensity(data.get("intensity") or data.get("strength"))
        return [{**item, "strength": item.get("strength") or strength} for item in existing]
    for key in ("emotion", "label"):
        label = _clean(data.get(key), limit=80)
        if label:
            return [{"type": label, "strength": _strength_from_intensity(data.get("intensity") or data.get("strength"))}]
    return []


def _record_to_frame_input(record: Any) -> tuple[dict[str, Any], str]:
    data = _as_mapping(record)
    violation = _domain_violation_for_record(data)
    source_id = _clean(data.get("id") or data.get("source_id") or data.get("record_id") or _stable_hash(data.get("memo"), data.get("created_at")), limit=120)
    created_at = _clean(data.get("created_at") or data.get("selected_at") or data.get("timestamp"), limit=80)
    return (
        {
            "id": source_id,
            "created_at": created_at,
            "memo": _clean(data.get("memo") or data.get("thought_text"), limit=10000),
            "memo_action": _clean(data.get("memo_action") or data.get("action_text"), limit=10000),
            "emotion_details": _emotion_details_from_record(data),
            "emotions": [item.get("type") for item in _emotion_details_from_record(data) if item.get("type")],
            "category": _categories_from_record(data),
            "is_secret": bool(data.get("is_secret", False)),
        },
        violation,
    )


def _date_key(value: Any) -> str:
    text = _clean(value, limit=80)
    if not text:
        return ""
    if len(text) >= 10 and text[4:5] == "-" and text[7:8] == "-":
        return text[:10]
    try:
        raw = text[:-1] + "+00:00" if text.endswith("Z") else text
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).date().isoformat()
    except Exception:
        return text[:10]


def _source_record_id(frame: Mapping[str, Any]) -> str:
    source = frame.get("source") if isinstance(frame.get("source"), Mapping) else {}
    return _clean(source.get("source_record_id"), limit=120)


def _selected_at(frame: Mapping[str, Any]) -> str:
    source = frame.get("source") if isinstance(frame.get("source"), Mapping) else {}
    return _clean(source.get("selected_at"), limit=80)


def _frame_id(frame: Mapping[str, Any], index: int) -> str:
    base = _source_record_id(frame) or f"analysis-frame-{index}"
    return "analysis_eso_frame_" + _stable_hash(base, _selected_at(frame))[-16:]


def _environment_keys(frame: Mapping[str, Any]) -> list[str]:
    axis = frame.get("environment_axis") if isinstance(frame.get("environment_axis"), Mapping) else {}
    labels = axis.get("category_labels") if isinstance(axis.get("category_labels"), list) else []
    out: list[str] = []
    for item in labels:
        if not isinstance(item, Mapping):
            continue
        label = _clean(item.get("label"), limit=80)
        if label and label not in out:
            out.append(label)
    return out


def _state_keys(frame: Mapping[str, Any]) -> list[str]:
    axis = frame.get("state_axis") if isinstance(frame.get("state_axis"), Mapping) else {}
    labels = axis.get("emotion_labels") if isinstance(axis.get("emotion_labels"), list) else []
    out: list[str] = []
    for item in labels:
        if not isinstance(item, Mapping):
            continue
        label = _clean(item.get("type"), limit=80)
        if label and label not in out:
            out.append(label)
    return out


def _output_theme_keys(frame: Mapping[str, Any]) -> list[str]:
    axis = frame.get("output_axis") if isinstance(frame.get("output_axis"), Mapping) else {}
    labels = axis.get("output_theme_candidates") if isinstance(axis.get("output_theme_candidates"), list) else []
    out: list[str] = []
    for item in labels:
        if not isinstance(item, Mapping):
            continue
        theme = _clean(item.get("theme_id"), limit=100)
        if theme and theme not in out:
            out.append(theme)
    return out


def _theme_evidence_ids(frame: Mapping[str, Any], theme_id: str) -> list[str]:
    axis = frame.get("output_axis") if isinstance(frame.get("output_axis"), Mapping) else {}
    labels = axis.get("output_theme_candidates") if isinstance(axis.get("output_theme_candidates"), list) else []
    out: list[str] = []
    for item in labels:
        if not isinstance(item, Mapping) or _clean(item.get("theme_id"), limit=100) != theme_id:
            continue
        for sid in _sequence(item.get("evidence_span_ids")):
            text = _clean(sid, limit=120)
            if text and text not in out:
                out.append(text)
    return out


def _axis_presence(frame: Mapping[str, Any]) -> dict[str, bool]:
    axis = frame.get("axis_presence") if isinstance(frame.get("axis_presence"), Mapping) else {}
    return {
        "has_environment_axis": bool(axis.get("has_environment_axis", False)),
        "has_state_axis": bool(axis.get("has_state_axis", False)),
        "has_output_axis": bool(axis.get("has_output_axis", False)),
        "has_all_single_record_axes": bool(axis.get("has_all_single_record_axes", False)),
    }


def _project_frame(frame: Mapping[str, Any], index: int) -> dict[str, Any]:
    fid = _frame_id(frame, index)
    env_keys = _environment_keys(frame)
    state_keys = _state_keys(frame)
    theme_keys = _output_theme_keys(frame)
    evidence_ids: list[str] = []
    for theme in theme_keys:
        for sid in _theme_evidence_ids(frame, theme):
            if sid not in evidence_ids:
                evidence_ids.append(sid)
    return {
        "frame_id": fid,
        "source_record_id": _source_record_id(frame),
        "selected_at": _selected_at(frame),
        "date_key": _date_key(_selected_at(frame)),
        "source_kind": "saved_record",
        "environment_keys": env_keys,
        "state_keys": state_keys,
        "output_theme_keys": theme_keys,
        "axis_presence": _axis_presence(frame),
        "representative_evidence_span_ids": evidence_ids[:3],
        "raw_text_included": False,
        "public_surface_text_generated": False,
    }


def _period_scope(period_kind: str, period_label: str = "", start_at: str = "", end_at: str = "") -> dict[str, Any]:
    return {
        "kind": _clean(period_kind, limit=40) or "custom",
        "label": _clean(period_label, limit=120),
        "start_at": _clean(start_at, limit=80),
        "end_at": _clean(end_at, limit=80),
    }


def _recurrence_level(record_count: int, distinct_day_count: int) -> str:
    if record_count >= 4 and distinct_day_count >= 2:
        return RECURRENCE_LEVEL_STRONG_PERIOD_SIGNAL
    if record_count >= 3 or distinct_day_count >= 2:
        return RECURRENCE_LEVEL_PERIOD_TENDENCY_CANDIDATE
    if record_count >= 2:
        return RECURRENCE_LEVEL_RECURRENCE_CANDIDATE
    if record_count == 1:
        return RECURRENCE_LEVEL_SINGLE_OBSERVATION
    return RECURRENCE_LEVEL_NO_BASIS


def _conditional_output_tendencies(
    projections: Sequence[Mapping[str, Any]],
    *,
    period_scope: Mapping[str, Any],
    min_record_count: int,
) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for frame in projections:
        for env in frame.get("environment_keys") or []:
            for state in frame.get("state_keys") or []:
                for theme in frame.get("output_theme_keys") or []:
                    groups[(_clean(env, limit=80), _clean(state, limit=80), _clean(theme, limit=100))].append(frame)

    rows: list[dict[str, Any]] = []
    for (environment_key, state_key, output_theme_key), items in sorted(groups.items(), key=lambda pair: (-len(pair[1]), pair[0])):
        if len(items) < min_record_count:
            continue
        dates = sorted({str(item.get("date_key") or "") for item in items if item.get("date_key")})
        evidence_ids: list[str] = []
        for item in items:
            for sid in item.get("representative_evidence_span_ids") or []:
                sid_text = _clean(sid, limit=120)
                if sid_text and sid_text not in evidence_ids:
                    evidence_ids.append(sid_text)
        rows.append(
            {
                "schema_version": CONDITIONAL_OUTPUT_TENDENCY_SCHEMA_VERSION,
                "material_id": CONDITIONAL_OUTPUT_TENDENCY_MATERIAL_ID,
                "period_scope": dict(period_scope),
                "query_key": {
                    "environment_key": environment_key,
                    "state_key": state_key,
                    "output_theme_key": output_theme_key,
                },
                "recurrence_level": _recurrence_level(len(items), len(dates)),
                "record_count": len(items),
                "distinct_day_count": len(dates),
                "matching_frame_ids": [str(item.get("frame_id")) for item in items],
                "representative_evidence_span_ids": evidence_ids[:5],
                "allowed_surface": {
                    "scope_marker": "この期間の記録では",
                    "max_claim_strength": "observed_recurrence",
                    "must_include_record_scope": True,
                    "public_analysis_text_connected": False,
                },
                "forbidden_claims": list(_FORBIDDEN_CLAIMS),
                "cause_from_category": False,
                "cause_from_emotion_strength": False,
                "personality_type_allowed": False,
                "diagnosis_allowed": False,
            }
        )
    return rows


def _is_recovery_from_frame(frame: Mapping[str, Any]) -> bool:
    states = {_clean(x, limit=80) for x in frame.get("state_keys") or []}
    return bool(states.intersection(_RECOVERY_FROM_STATE_KEYS))


def _is_recovery_to_frame(frame: Mapping[str, Any]) -> bool:
    states = {_clean(x, limit=80) for x in frame.get("state_keys") or []}
    themes = {_clean(x, limit=100) for x in frame.get("output_theme_keys") or []}
    return bool(states.intersection(_RECOVERY_TO_STATE_KEYS) or themes.intersection(_RECOVERY_TO_OUTPUT_THEME_KEYS))


def _first_or_empty(values: Any) -> str:
    for value in values or []:
        text = _clean(value, limit=100)
        if text:
            return text
    return ""


def _recovery_label_paths(projections: Sequence[Mapping[str, Any]], *, period_scope: Mapping[str, Any]) -> list[dict[str, Any]]:
    ordered = sorted(enumerate(projections), key=lambda pair: (_selected_sort_key(pair[1]), pair[0]))
    paths: list[dict[str, Any]] = []
    key_counts: Counter[tuple[str, str, str, str, str, str]] = Counter()
    pending: list[tuple[Mapping[str, Any], Mapping[str, Any], int, int, tuple[str, str, str, str, str, str]]] = []
    for idx in range(len(ordered) - 1):
        _, before = ordered[idx]
        _, after = ordered[idx + 1]
        if not _is_recovery_from_frame(before) or not _is_recovery_to_frame(after):
            continue
        key = (
            _first_or_empty(before.get("environment_keys")),
            _first_or_empty(before.get("state_keys")),
            _first_or_empty(before.get("output_theme_keys")),
            _first_or_empty(after.get("environment_keys")),
            _first_or_empty(after.get("state_keys")),
            _first_or_empty(after.get("output_theme_keys")),
        )
        key_counts[key] += 1
        pending.append((before, after, idx, idx + 1, key))

    for before, after, before_order, after_order, key in pending:
        count = key_counts[key]
        paths.append(
            {
                "schema_version": RECOVERY_LABEL_PATH_SCHEMA_VERSION,
                "material_id": RECOVERY_LABEL_PATH_MATERIAL_ID,
                "period_scope": dict(period_scope),
                "path_candidate": {
                    "from": {
                        "frame_id": before.get("frame_id"),
                        "environment_key": key[0],
                        "state_key": key[1],
                        "output_theme_key": key[2],
                    },
                    "to": {
                        "frame_id": after.get("frame_id"),
                        "environment_key": key[3],
                        "state_key": key[4],
                        "output_theme_key": key[5],
                    },
                    "elapsed_kind": "within_period",
                    "record_order_evidence": True,
                    "adjacent_record_order": [before_order, after_order],
                },
                "recurrence_level": RECURRENCE_LEVEL_PATH_RECURRENCE_CANDIDATE if count >= 2 else RECURRENCE_LEVEL_SINGLE_PATH_OBSERVATION,
                "allowed_surface": {
                    "max_claim_strength": "sequence_observation",
                    "must_not_call_cure": True,
                    "must_not_prescribe": True,
                    "public_analysis_text_connected": False,
                },
                "forbidden_claims": list(_RECOVERY_FORBIDDEN_CLAIMS),
                "diagnosis_allowed": False,
                "treatment_claim_allowed": False,
                "recovery_prescription_allowed": False,
            }
        )
    return paths


def _selected_sort_key(frame: Mapping[str, Any]) -> str:
    return _clean(frame.get("selected_at"), limit=80) or _clean(frame.get("source_record_id"), limit=80)


def build_analysis_environment_state_output_material(
    records: Sequence[Any],
    *,
    period_kind: str = "custom",
    period_label: str = "",
    start_at: str = "",
    end_at: str = "",
    min_tendency_record_count: int = 2,
) -> dict[str, Any]:
    """Build Phase 7 Analysis-facing internal tendency material.

    ``records`` should be saved Cocolon emotion/input records.  The function is
    deterministic and side-effect free.  The returned payload is internal-only:
    it does not create public Analysis text and it does not attach anything to
    ``content_json`` / ``standardReport`` / ``contentText``.
    """

    scope = _period_scope(period_kind, period_label=period_label, start_at=start_at, end_at=end_at)
    safe_frames: list[dict[str, Any]] = []
    violations: list[dict[str, Any]] = []

    for index, record in enumerate(records or [], start=1):
        frame_input, violation = _record_to_frame_input(record)
        if violation:
            violations.append(
                {
                    "source_record_id": frame_input.get("id") or f"record-{index}",
                    "reason": violation,
                }
            )
            continue
        try:
            frame = build_environment_state_output_frame(frame_input, observation_structure_relation_ids=[])
        except Exception as exc:
            violations.append(
                {
                    "source_record_id": frame_input.get("id") or f"record-{index}",
                    "reason": "frame_builder_failed",
                    "error_type": type(exc).__name__,
                }
            )
            continue
        safe_frames.append(_project_frame(frame, index))

    frame_count_with_all_axes = sum(1 for frame in safe_frames if (frame.get("axis_presence") or {}).get("has_all_single_record_axes"))
    tendencies = _conditional_output_tendencies(safe_frames, period_scope=scope, min_record_count=max(2, int(min_tendency_record_count or 2)))
    paths = _recovery_label_paths(safe_frames, period_scope=scope)
    source_domain_separated = not violations

    return {
        "schema_version": ANALYSIS_ENVIRONMENT_STATE_OUTPUT_MATERIAL_SCHEMA_VERSION,
        "material_id": ANALYSIS_ENVIRONMENT_STATE_OUTPUT_MATERIAL_ID,
        "phase": ANALYSIS_ENVIRONMENT_STATE_OUTPUT_PHASE,
        "analysis_domain": ANALYSIS_ENVIRONMENT_STATE_OUTPUT_DOMAIN,
        "period_scope": scope,
        "source_summary": {
            "input_record_count": len(records or []),
            "usable_frame_count": len(safe_frames),
            "frame_count_with_all_axes": frame_count_with_all_axes,
            "conditional_output_tendency_count": len(tendencies),
            "recovery_label_path_count": len(paths),
        },
        "frame_projections": safe_frames,
        "conditional_output_tendencies": tendencies,
        "recovery_label_paths": paths,
        "domain_boundary": {
            "source_domain_separated": source_domain_separated,
            "rejected_source_count": len(violations),
            "rejected_sources": violations,
            "emotion_structure_material_output_connected": False,
            "self_structure_material_output_connected": False,
            "emotion_self_structure_material_mixing_allowed": False,
            "public_analysis_text_connected": False,
            "analysis_composer_surface_connected": False,
        },
        "surface_policy": {
            "internal_material_only": True,
            "public_analysis_text_connected": False,
            "analysis_content_payload_changed": False,
            "standardReport_contract_untouched": True,
            "contentText_contract_untouched": True,
            "json_schema_file_materialized": False,
            "raw_text_included": False,
            "cause_from_category": False,
            "cause_from_emotion_strength": False,
            "diagnosis_allowed": False,
            "personality_type_allowed": False,
            "recovery_prescription_allowed": False,
            "forbidden_claims": list(_FORBIDDEN_CLAIMS),
        },
    }


def summarize_analysis_environment_state_output_material(material: Mapping[str, Any]) -> dict[str, Any]:
    """Return a compact internal summary safe for meta-only diagnostics."""

    return {
        "schema_version": _clean(material.get("schema_version"), limit=120),
        "material_id": _clean(material.get("material_id"), limit=120),
        "phase": _clean(material.get("phase"), limit=120),
        "analysis_domain": _clean(material.get("analysis_domain"), limit=120),
        "period_scope": dict(material.get("period_scope") or {}),
        "source_summary": dict(material.get("source_summary") or {}),
        "domain_boundary": dict(material.get("domain_boundary") or {}),
        "conditional_output_tendency_count": len(material.get("conditional_output_tendencies") or []),
        "recovery_label_path_count": len(material.get("recovery_label_paths") or []),
        "public_analysis_text_connected": False,
        "raw_text_included": False,
    }


__all__ = [
    "ANALYSIS_ENVIRONMENT_STATE_OUTPUT_MATERIAL_SCHEMA_VERSION",
    "ANALYSIS_ENVIRONMENT_STATE_OUTPUT_MATERIAL_ID",
    "CONDITIONAL_OUTPUT_TENDENCY_SCHEMA_VERSION",
    "CONDITIONAL_OUTPUT_TENDENCY_MATERIAL_ID",
    "RECOVERY_LABEL_PATH_SCHEMA_VERSION",
    "RECOVERY_LABEL_PATH_MATERIAL_ID",
    "ANALYSIS_ENVIRONMENT_STATE_OUTPUT_PHASE",
    "ANALYSIS_ENVIRONMENT_STATE_OUTPUT_DOMAIN",
    "build_analysis_environment_state_output_material",
    "summarize_analysis_environment_state_output_material",
]
