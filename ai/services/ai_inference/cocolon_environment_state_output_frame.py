# -*- coding: utf-8 -*-
from __future__ import annotations

"""Cocolon environment/state/output observation frame builder.

Phase 3 materializes the internal single-record frame proposed by the
Cocolon environment-state-output observation structure.  It reads the typed
Emlis current-input bundle and returns text-free structural material:

- environment axis: category labels and memo_action evidence ids
- state axis: emotion labels and strength summary
- output axis: memo evidence ids and bounded output-theme candidates
- time axis: single-record scope only
- evidence: source-field ids and hashes, never raw memo/memo_action text

This module does not change public API routes, response keys, DB physical names,
RN display conditions, or json/schema files.  It also does not generate
user-facing sentences.  Phase 4 owns connection into the Emlis observation
structure material path.
"""

from collections.abc import Mapping
from hashlib import sha256
import re
from typing import Any, Final

from emlis_ai_current_input_bundle import (
    EMLIS_CURRENT_INPUT_BUNDLE_SCHEMA_VERSION,
    EmlisCurrentInputBundle,
    build_emlis_current_input_bundle,
)
from emlis_ai_evidence_ledger_service import build_evidence_ledger

ENVIRONMENT_STATE_OUTPUT_FRAME_SCHEMA_VERSION: Final = "cocolon.environment_state_output_frame.v1"
ENVIRONMENT_STATE_OUTPUT_FRAME_MATERIAL_ID: Final = "environment_state_output_frame"
ENVIRONMENT_STATE_OUTPUT_FRAME_PHASE: Final = "Phase3_environment_state_output_frame_builder"

_FORBIDDEN_CLAIMS: Final = (
    "personality_tendency",
    "diagnosis",
    "cause_from_category",
    "cause_from_emotion_strength",
    "period_tendency_from_single_record",
    "recovery_prescription",
)

_SPACE_RE: Final = re.compile(r"\s+")
_GAP_WORD_RE: Final = re.compile(r"(大丈夫|平気|なんでもない|何でもない|大したことない|大丈夫なはず|まあいいか)")
_CONTINUATION_CONCERN_RE: Final = re.compile(
    r"(やっていける|続けられる|続けていける|続くかな|継続でき|ここにいていい|耐えられる|持つかな|このまま.*続|続ける.*不安)"
)
_RELATION_LOSS_CONCERN_RE: Final = re.compile(r"(嫌われ|きらわれ|離れ|失う|見捨て|関係.*なくなる)")
_MAINTENANCE_CONCERN_RE: Final = re.compile(r"(足りる|足りない|維持でき|生活でき|払える|続けて払|暮らせ)")
_DIRECTION_CONCERN_RE: Final = re.compile(r"(このままでいい|このままでよい|どうしたらいい|方向|先が見え|将来.*不安)")
_UNFAIRNESS_CONCERN_RE: Final = re.compile(r"(自分ばかり|私ばかり|俺ばかり|不公平|理不尽|なんで.*だけ)")
_UNREWARDED_EFFORT_RE: Final = re.compile(r"(報われ|意味なかった|意味がなかった|返ってこない|伝わらない|頑張っても)")
_REASON_VISIBLE_RE: Final = re.compile(r"(理由が.*見え|理由.*わか|理由.*分か|納得|整理でき|少し見えた)")
_UNFORMED_SELF_INSIGHT_RE: Final = re.compile(
    r"(わからない|分からない|どうしたらいいかわからない|どうしたらいいか分からない|しっくりこない|違和感がある)"
)

_OUTPUT_THEME_PATTERNS: Final = (
    {
        "theme_id": "continuation_concern",
        "label": "継続できるかへの心配",
        "pattern": _CONTINUATION_CONCERN_RE,
        "supporting_relation_ids": ("pressure_gap", "action_blocked"),
    },
    {
        "theme_id": "relation_loss_concern",
        "label": "関係が離れることへの心配",
        "pattern": _RELATION_LOSS_CONCERN_RE,
        "supporting_relation_ids": ("pressure_gap",),
    },
    {
        "theme_id": "maintenance_concern",
        "label": "維持できるかへの心配",
        "pattern": _MAINTENANCE_CONCERN_RE,
        "supporting_relation_ids": ("pressure_gap", "action_blocked"),
    },
    {
        "theme_id": "direction_concern",
        "label": "方向性への心配",
        "pattern": _DIRECTION_CONCERN_RE,
        "supporting_relation_ids": ("pressure_gap", "unformed_self_insight"),
    },
    {
        "theme_id": "unfairness_concern",
        "label": "不公平さへの反応",
        "pattern": _UNFAIRNESS_CONCERN_RE,
        "supporting_relation_ids": ("priority_pressure", "pressure_gap"),
    },
    {
        "theme_id": "unrewarded_effort",
        "label": "報われなさへの反応",
        "pattern": _UNREWARDED_EFFORT_RE,
        "supporting_relation_ids": ("pressure_gap", "conversion_history_closure"),
    },
    {
        "theme_id": "reason_became_visible",
        "label": "理由が見えたこと",
        "pattern": _REASON_VISIBLE_RE,
        "supporting_relation_ids": ("self_insight_discovery", "unformed_self_insight"),
    },
    {
        "theme_id": "unformed_self_insight",
        "label": "まだ形になりきっていない自己理解",
        "pattern": _UNFORMED_SELF_INSIGHT_RE,
        "supporting_relation_ids": ("unformed_self_insight", "low_information_weight"),
    },
)


def _clean(value: Any) -> str:
    return _SPACE_RE.sub(" ", str(value or "").replace("\u3000", " ")).strip()


def _stable_hash(*parts: Any) -> str:
    value = "\0".join(_clean(part) for part in parts)
    return "sha256:" + sha256(value.encode("utf-8")).hexdigest()


def _span_id(span: Any, index: int) -> str:
    return _clean(getattr(span, "span_id", "")) or f"s{index + 1}"


def _span_source_field(span: Any) -> str:
    return _clean(getattr(span, "source_field", ""))


def _span_raw_text(span: Any) -> str:
    # Internal-only. Never place this value into the returned frame.
    return _clean(getattr(span, "raw_text", ""))


def _span_ids_for_fields(spans: list[Any], *fields: str) -> list[str]:
    allowed = {field for field in fields if field}
    out: list[str] = []
    for index, span in enumerate(spans):
        if _span_source_field(span) in allowed:
            sid = _span_id(span, index)
            if sid not in out:
                out.append(sid)
    return out


def _int_attr(value: Any, *, default: int = -1) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_evidence_spans(spans: list[Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for index, span in enumerate(spans):
        source_field = _span_source_field(span)
        raw_text = _span_raw_text(span)
        if not source_field or not raw_text:
            continue
        out.append(
            {
                "span_id": _span_id(span, index),
                "source_field": source_field,
                "text_hash": _stable_hash(source_field, raw_text),
                "detected_type": _clean(getattr(span, "detected_type", "")) or "event",
                "confidence": float(getattr(span, "confidence", 0.0) or 0.0),
                "start_index": _int_attr(getattr(span, "start_index", None)),
                "end_index": _int_attr(getattr(span, "end_index", None)),
                "raw_text_included": False,
                "redacted_preview_included": False,
            }
        )
    return out


def _environment_confidence_kind(bundle: EmlisCurrentInputBundle) -> str:
    if bundle.categories and bundle.action_text:
        return "category_plus_action_evidence"
    if bundle.categories:
        return "category_only_topic_direction"
    if bundle.action_text:
        return "action_only_environment_evidence"
    return "environment_axis_missing"


def _state_confidence_kind(bundle: EmlisCurrentInputBundle) -> str:
    return "explicit_emotion_selection" if bundle.emotions else "state_axis_missing"


def _output_confidence_kind(bundle: EmlisCurrentInputBundle) -> str:
    return "thought_text_present" if bundle.thought_text else "output_axis_missing"


def _selected_relation_ids_from_material(material: Any) -> list[str]:
    if material is None:
        return []
    if isinstance(material, Mapping):
        values = material.get("selected_relation_ids") or material.get("structure_relation_ids") or []
    else:
        values = getattr(material, "selected_relation_ids", ()) or ()
    out: list[str] = []
    for value in values:
        item = _clean(value)
        if item and item not in out:
            out.append(item)
    return out


def _build_observation_structure_relation_ids(current_input: Any) -> list[str]:
    """Return existing Emlis dictionary relation ids when safely available.

    The frame must not depend on this material to be useful.  If the dictionary
    bridge is unavailable in a local test environment, Phase 3 still returns a
    valid frame and marks the bridge as unavailable rather than adding text or
    causes.
    """

    try:
        from emlis_ai_observation_structure_material_service import build_observation_structure_material

        material = build_observation_structure_material(current_input=current_input)
        return _selected_relation_ids_from_material(material)
    except Exception:
        return []


def _output_theme_candidates(bundle: EmlisCurrentInputBundle, *, thought_span_ids: list[str], relation_ids: list[str]) -> list[dict[str, Any]]:
    if not bundle.thought_text or not thought_span_ids:
        return []
    text = _clean(bundle.thought_text)
    out: list[dict[str, Any]] = []
    relation_set = set(relation_ids)
    for spec in _OUTPUT_THEME_PATTERNS:
        pattern = spec["pattern"]
        if not pattern.search(text):
            continue
        supporting = [rid for rid in spec["supporting_relation_ids"] if rid in relation_set]
        out.append(
            {
                "theme_id": spec["theme_id"],
                "label": spec["label"],
                "source_field": "memo",
                "evidence_span_ids": list(thought_span_ids),
                "confidence_kind": "explicit_text_evidence",
                "allowed_surface_strength": "soft",
                "supporting_observation_relation_ids": supporting,
                "must_not_read_as": ["personality_tendency", "period_tendency", "diagnosis"],
            }
        )
    return out


def _state_text_gap_candidates(bundle: EmlisCurrentInputBundle, *, evidence_span_ids: list[str]) -> list[dict[str, Any]]:
    if not bundle.emotions or not bundle.thought_text:
        return []
    if not _GAP_WORD_RE.search(bundle.thought_text):
        return []
    strongest = bundle.emotion_strength_summary.strongest_strength or bundle.emotion_strength_summary.primary_strength
    return [
        {
            "candidate_id": "state_text_gap",
            "source_fields": ["memo", "emotion_details"],
            "evidence_span_ids": list(evidence_span_ids),
            "confidence_kind": "explicit_emotion_and_gap_word",
            "strength_context": strongest,
            "allowed_surface_strength": "soft",
            "must_not_read_as": ["hidden_truth", "lie", "diagnosis", "cause"],
        }
    ]


def build_environment_state_output_frame(
    current_input: Any,
    *,
    observation_structure_relation_ids: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Build the Phase 3 single-record environment/state/output frame.

    The returned dict is internal material, not public response data and not a
    completed reply.  It contains no raw memo/memo_action text.  It is scoped to
    one current input and explicitly forbids period tendency, causal reading from
    category or emotion strength, diagnosis, personality inference, and recovery
    prescription.
    """

    bundle = build_emlis_current_input_bundle(current_input)
    current_payload = bundle.to_current_input_payload()
    spans = list(build_evidence_ledger(current_payload))

    category_span_ids = _span_ids_for_fields(spans, "category")
    action_span_ids = _span_ids_for_fields(spans, "memo_action")
    emotion_span_ids = _span_ids_for_fields(spans, "emotion_details", "emotions")
    thought_span_ids = _span_ids_for_fields(spans, "memo")

    relation_ids = list(observation_structure_relation_ids or [])
    if observation_structure_relation_ids is None:
        relation_ids = _build_observation_structure_relation_ids(current_payload)

    all_state_gap_evidence = []
    for sid in thought_span_ids + emotion_span_ids:
        if sid not in all_state_gap_evidence:
            all_state_gap_evidence.append(sid)

    has_environment_axis = bool(bundle.categories or bundle.action_text)
    has_state_axis = bool(bundle.emotions)
    has_output_axis = bool(bundle.thought_text)

    frame: dict[str, Any] = {
        "schema_version": ENVIRONMENT_STATE_OUTPUT_FRAME_SCHEMA_VERSION,
        "material_id": ENVIRONMENT_STATE_OUTPUT_FRAME_MATERIAL_ID,
        "phase": ENVIRONMENT_STATE_OUTPUT_FRAME_PHASE,
        "source": {
            "source_record_id": bundle.source_record_id,
            "selected_at": bundle.selected_at,
            "source_kind": "current_input",
            "bundle_schema_version": EMLIS_CURRENT_INPUT_BUNDLE_SCHEMA_VERSION,
        },
        "axis_presence": {
            "has_environment_axis": has_environment_axis,
            "has_state_axis": has_state_axis,
            "has_output_axis": has_output_axis,
            "has_all_single_record_axes": bool(has_environment_axis and has_state_axis and has_output_axis),
        },
        "environment_axis": {
            "category_labels": [
                {
                    "label": label,
                    "source_field": "category",
                    "evidence_span_ids": list(category_span_ids),
                    "read_as": "topic_direction",
                    "must_not_read_as": "cause",
                }
                for label in bundle.categories
            ],
            "action_evidence": {
                "has_action_text": bool(bundle.action_text),
                "source_field": "memo_action",
                "evidence_span_ids": list(action_span_ids),
                "raw_text_included": False,
                "event_or_action_summary_included": False,
                "environment_targets": [],
            },
            "confidence_kind": _environment_confidence_kind(bundle),
            "ambiguity_flags": [] if has_environment_axis else ["environment_axis_missing"],
        },
        "state_axis": {
            "emotion_labels": [
                {
                    "type": emotion.type,
                    "strength": emotion.strength,
                    "source_field": _clean(emotion.source_field) or "emotion_details",
                    "evidence_span_ids": list(emotion_span_ids),
                    "read_as": "state_label",
                    "must_not_read_as": "diagnosis",
                }
                for emotion in bundle.emotions
            ],
            "strength_summary": bundle.emotion_strength_summary.to_dict(),
            "state_text_gap_candidates": _state_text_gap_candidates(bundle, evidence_span_ids=all_state_gap_evidence),
            "confidence_kind": _state_confidence_kind(bundle),
        },
        "output_axis": {
            "thought_evidence": {
                "has_thought_text": bool(bundle.thought_text),
                "source_field": "memo",
                "evidence_span_ids": list(thought_span_ids),
                "raw_text_included": False,
            },
            "output_theme_candidates": _output_theme_candidates(
                bundle,
                thought_span_ids=thought_span_ids,
                relation_ids=relation_ids,
            ),
            "unexpressed_output_candidates": [],
            "action_conversion_candidates": [],
            "confidence_kind": _output_confidence_kind(bundle),
        },
        "time_axis": {
            "selected_at": bundle.selected_at,
            "period_scope": "single_record",
            "must_not_use_for_period_tendency": True,
        },
        "observation_structure_bridge": {
            "selected_relation_ids": relation_ids,
            "bridge_used_for_surface_text": False,
            "relation_ids_are_candidates_only": True,
        },
        "evidence": {
            "spans": _safe_evidence_spans(spans),
            "raw_text_included": False,
            "redacted_preview_included": False,
        },
        "surface_policy": {
            "single_record_only": True,
            "must_use_scope_marker": True,
            "scope_marker": "今回の入力では",
            "forbidden_claims": list(_FORBIDDEN_CLAIMS),
            "completed_reply_generated": False,
            "comment_text_generated": False,
            "public_payload_changed": False,
            "public_response_key_added": False,
            "api_route_changed": False,
            "response_key_changed": False,
            "db_physical_name_changed": False,
            "rn_visible_contract_changed": False,
            "raw_input_included": False,
            "raw_text_included": False,
            "cause_from_category": False,
            "cause_from_emotion_strength": False,
            "period_tendency_from_single_record": False,
            "personality_tendency_allowed": False,
            "recovery_prescription_allowed": False,
        },
    }
    return frame


# Alias with the project name for later cross-core call sites.
build_cocolon_environment_state_output_frame = build_environment_state_output_frame


__all__ = [
    "ENVIRONMENT_STATE_OUTPUT_FRAME_SCHEMA_VERSION",
    "ENVIRONMENT_STATE_OUTPUT_FRAME_MATERIAL_ID",
    "ENVIRONMENT_STATE_OUTPUT_FRAME_PHASE",
    "build_environment_state_output_frame",
    "build_cocolon_environment_state_output_frame",
]
