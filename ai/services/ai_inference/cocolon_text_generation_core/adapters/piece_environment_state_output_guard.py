# -*- coding: utf-8 -*-
from __future__ import annotations

"""Piece overcompression guard material for environment/state/output frames.

Phase 6 connects the Cocolon environment-state-output observation frame to
PieceComposer without turning it into an Emlis-like reply or an Analysis-like
period tendency.  The material produced here is internal only: it contains no
raw memo/memo_action text, creates no public response key, and only exposes the
axis labels/theme ids needed to prevent Piece from collapsing a grounded input
into a category/emotion-only answer such as ``不安です``.
"""

from collections.abc import Mapping
import re
from typing import Any, Final

from cocolon_text_generation_core.result import json_safe_mapping

PIECE_ENVIRONMENT_STATE_OUTPUT_GUARD_SCHEMA_VERSION: Final = "cocolon.piece.environment_state_output_overcompression_guard.v1"
PIECE_ENVIRONMENT_STATE_OUTPUT_GUARD_MATERIAL_ID: Final = "piece_environment_state_output_overcompression_guard"
PIECE_ENVIRONMENT_STATE_OUTPUT_GUARD_PHASE: Final = "Phase6_piece_overcompression_prevention_connection"

_SPACE_RE: Final = re.compile(r"\s+")
_KEY_SAFE_RE: Final = re.compile(r"[^0-9A-Za-z_\-\u3040-\u30ff\u3400-\u9fff]+")


def _clean(value: Any) -> str:
    return _SPACE_RE.sub(" ", str(value or "").replace("\r", " ").replace("\n", " ").replace("\u3000", " ")).strip()


def _compact_key(value: Any) -> str:
    text = _clean(value)
    text = _KEY_SAFE_RE.sub("_", text).strip("_")
    return text or "unknown"


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]


def _dedupe(values: list[Any]) -> list[str]:
    out: list[str] = []
    for value in values:
        text = _clean(value)
        if text and text not in out:
            out.append(text)
    return out


def _category_labels(frame: Mapping[str, Any]) -> list[str]:
    env = _as_mapping(frame.get("environment_axis"))
    labels: list[str] = []
    for item in _as_list(env.get("category_labels")):
        mapping = _as_mapping(item)
        label = _clean(mapping.get("label"))
        if label:
            labels.append(label)
    return _dedupe(labels)


def _emotion_labels(frame: Mapping[str, Any]) -> list[str]:
    state = _as_mapping(frame.get("state_axis"))
    labels: list[str] = []
    for item in _as_list(state.get("emotion_labels")):
        mapping = _as_mapping(item)
        label = _clean(mapping.get("type"))
        if label:
            labels.append(label)
    return _dedupe(labels)


def _output_theme_candidates(frame: Mapping[str, Any]) -> list[dict[str, Any]]:
    output = _as_mapping(frame.get("output_axis"))
    out: list[dict[str, Any]] = []
    for item in _as_list(output.get("output_theme_candidates")):
        mapping = _as_mapping(item)
        theme_id = _clean(mapping.get("theme_id"))
        if not theme_id:
            continue
        label = _clean(mapping.get("label"))
        out.append(
            {
                "theme_id": theme_id,
                "label": label,
                "source_field": _clean(mapping.get("source_field")) or "memo",
                "evidence_span_ids": _dedupe(_as_list(mapping.get("evidence_span_ids"))),
                "confidence_kind": _clean(mapping.get("confidence_kind")) or "explicit_text_evidence",
                "raw_text_included": False,
            }
        )
    return out


def _axis_presence(frame: Mapping[str, Any], *, categories: list[str], emotions: list[str], output_themes: list[dict[str, Any]]) -> dict[str, bool]:
    raw = _as_mapping(frame.get("axis_presence"))
    has_environment = bool(raw.get("has_environment_axis", False) or categories)
    has_state = bool(raw.get("has_state_axis", False) or emotions)
    has_output = bool(raw.get("has_output_axis", False) or output_themes)
    return {
        "has_environment_axis": has_environment,
        "has_state_axis": has_state,
        "has_output_axis": has_output,
        "has_all_single_record_axes": bool(has_environment and has_state and has_output),
    }


def _source_field_requirements(*, categories: list[str], emotions: list[str], output_themes: list[dict[str, Any]]) -> list[str]:
    fields: list[str] = []
    if categories:
        fields.append("category")
    if emotions:
        fields.append("emotion_details")
    if output_themes:
        fields.append("memo")
    return fields


def build_piece_environment_state_output_overcompression_guard(
    frame: Any,
    *,
    apply_must_keep: bool = True,
) -> dict[str, Any]:
    """Return internal Piece must-keep material derived from a single frame.

    The returned data is intentionally structural.  It does not contain raw
    current-input text and it must not be surfaced as a public response key.
    """

    source = _as_mapping(frame)
    if not source:
        return {
            "schema_version": PIECE_ENVIRONMENT_STATE_OUTPUT_GUARD_SCHEMA_VERSION,
            "material_id": PIECE_ENVIRONMENT_STATE_OUTPUT_GUARD_MATERIAL_ID,
            "phase": PIECE_ENVIRONMENT_STATE_OUTPUT_GUARD_PHASE,
            "connected": False,
            "reason": "environment_state_output_frame_missing",
            "must_keep_signal_keys": [],
            "source_claim_values": [],
            "raw_text_included": False,
            "public_response_key_added": False,
        }

    if _clean(source.get("schema_version")) == PIECE_ENVIRONMENT_STATE_OUTPUT_GUARD_SCHEMA_VERSION:
        material = dict(json_safe_mapping(source))
        material.setdefault("connected", True)
        material.setdefault("raw_text_included", False)
        material.setdefault("public_response_key_added", False)
        return material

    categories = _category_labels(source)
    emotions = _emotion_labels(source)
    output_themes = _output_theme_candidates(source)
    presence = _axis_presence(source, categories=categories, emotions=emotions, output_themes=output_themes)
    single_record_only = bool(_as_mapping(source.get("surface_policy")).get("single_record_only", True))
    has_output_theme = bool(output_themes)
    guard_enabled = bool(apply_must_keep and single_record_only and presence["has_all_single_record_axes"] and has_output_theme)

    keys: list[str] = []
    if guard_enabled and categories:
        keys.append(f"eso_environment:{_compact_key(categories[0])}")
    if guard_enabled and emotions:
        keys.append(f"eso_state:{_compact_key(emotions[0])}")
    if guard_enabled and output_themes:
        keys.append(f"eso_output:{_compact_key(output_themes[0].get('theme_id'))}")

    source_claim_values: list[str] = []
    # Only explicit labels are exposed here.  Raw memo/memo_action text remains
    # owned by the caller as source_texts/current_input evidence.
    source_claim_values.extend(categories[:1])
    source_claim_values.extend(emotions[:1])

    return {
        "schema_version": PIECE_ENVIRONMENT_STATE_OUTPUT_GUARD_SCHEMA_VERSION,
        "material_id": PIECE_ENVIRONMENT_STATE_OUTPUT_GUARD_MATERIAL_ID,
        "phase": PIECE_ENVIRONMENT_STATE_OUTPUT_GUARD_PHASE,
        "connected": True,
        "source_frame_schema_version": _clean(source.get("schema_version")),
        "source_frame_material_id": _clean(source.get("material_id")),
        "single_record_only": True,
        "axis_presence": presence,
        "category_labels": list(categories),
        "emotion_labels": list(emotions),
        "output_theme_ids": [str(item.get("theme_id") or "") for item in output_themes if str(item.get("theme_id") or "")],
        "output_theme_candidates": output_themes,
        "source_claim_values": _dedupe(source_claim_values),
        "source_field_requirements": _source_field_requirements(categories=categories, emotions=emotions, output_themes=output_themes),
        "must_keep_signal_keys": _dedupe(keys),
        "must_keep_signal_keys_applied": bool(guard_enabled and keys),
        "overcompression_risk": bool(guard_enabled),
        "answer_preservation_policy": "preserve_user_claims" if guard_enabled else "source_scaled",
        "minimum_detail_level": "source_scaled",
        "forbidden_surface_claims": [
            "emlis_voice",
            "analysis_period_tendency",
            "personality_tendency",
            "diagnosis",
            "cause_from_category",
            "cause_from_emotion_strength",
            "recovery_prescription",
        ],
        "raw_text_included": False,
        "public_response_key_added": False,
        "preview_publish_contract_touched": False,
        "preview_publish_contract_untouched": True,
    }


# Short alias used by Piece adapter call sites.
build_piece_environment_state_output_guard = build_piece_environment_state_output_overcompression_guard


__all__ = [
    "PIECE_ENVIRONMENT_STATE_OUTPUT_GUARD_SCHEMA_VERSION",
    "PIECE_ENVIRONMENT_STATE_OUTPUT_GUARD_MATERIAL_ID",
    "PIECE_ENVIRONMENT_STATE_OUTPUT_GUARD_PHASE",
    "build_piece_environment_state_output_guard",
    "build_piece_environment_state_output_overcompression_guard",
]
