# -*- coding: utf-8 -*-
from __future__ import annotations

"""Persistence helpers for the EmlisAI derived user model.

This store is best-effort by design. Failure to load or persist the model must
never block the immediate reply path.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, Optional

from emlis_ai_types import (
    DerivedModelHypothesis,
    DerivedUserModel,
    EvidenceRef,
    InterpretiveFrameProfile,
    MeaningMapEntry,
    PartnerExpectationProfile,
    ResponsePreferenceCues,
    SourceCursor,
    TopicAnchor,
    ValueAnchor,
)

try:
    from supabase_client import sb_get, sb_patch, sb_post
except Exception:  # pragma: no cover
    sb_get = None  # type: ignore
    sb_patch = None  # type: ignore
    sb_post = None  # type: ignore

MODEL_TABLE = "emlis_ai_user_models"
MODEL_SCHEMA_VERSION = "emlis_user_model.v2"
_MEMORY_MODELS: Dict[str, Dict[str, Any]] = {}


def _now_iso_z() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _pick_rows(resp: Any) -> List[Dict[str, Any]]:
    try:
        data = resp.json()
    except Exception:
        return []
    if isinstance(data, list):
        return [row for row in data if isinstance(row, dict)]
    if isinstance(data, dict):
        return [data]
    return []


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _parse_evidence_refs(value: Any) -> List[EvidenceRef]:
    if not isinstance(value, list):
        return []
    out: List[EvidenceRef] = []
    for item in value:
        if isinstance(item, EvidenceRef):
            out.append(item)
            continue
        if not isinstance(item, Mapping):
            continue
        out.append(
            EvidenceRef(
                kind=_clean(item.get("kind")) or "unknown",
                ref_id=_clean(item.get("ref_id")) or "unknown",
                weight=float(item.get("weight") or 1.0),
                note=_clean(item.get("note")) or None,
            )
        )
    return out


def _serialize_evidence_refs(items: List[EvidenceRef]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for item in items:
        out.append(
            {
                "kind": item.kind,
                "ref_id": item.ref_id,
                "weight": float(item.weight),
                "note": item.note,
            }
        )
    return out


def _parse_source_cursor(value: Any) -> SourceCursor:
    raw = value if isinstance(value, Mapping) else {}
    return SourceCursor(
        last_emotion_id=_clean(raw.get("last_emotion_id")) or None,
        last_emotion_created_at=_clean(raw.get("last_emotion_created_at")) or None,
        last_today_question_answer_id=_clean(raw.get("last_today_question_answer_id")) or None,
    )


def _serialize_source_cursor(cursor: SourceCursor) -> Dict[str, Any]:
    return {
        "last_emotion_id": cursor.last_emotion_id,
        "last_emotion_created_at": cursor.last_emotion_created_at,
        "last_today_question_answer_id": cursor.last_today_question_answer_id,
    }


def _parse_value_anchors(value: Any) -> List[ValueAnchor]:
    if not isinstance(value, list):
        return []
    out: List[ValueAnchor] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        key = _clean(item.get("key"))
        if not key:
            continue
        out.append(
            ValueAnchor(
                key=key,
                confidence=float(item.get("confidence") or 0.0),
                evidence=_parse_evidence_refs(item.get("evidence")),
                last_seen_at=_clean(item.get("last_seen_at")) or None,
            )
        )
    return out


def _serialize_value_anchors(items: List[ValueAnchor]) -> List[Dict[str, Any]]:
    return [
        {
            "key": item.key,
            "confidence": float(item.confidence),
            "evidence": _serialize_evidence_refs(item.evidence),
            "last_seen_at": item.last_seen_at,
        }
        for item in items
    ]


def _parse_meaning_map(value: Any) -> List[MeaningMapEntry]:
    if not isinstance(value, list):
        return []
    out: List[MeaningMapEntry] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        trigger = _clean(item.get("trigger"))
        meaning = _clean(item.get("likely_meaning"))
        if not trigger or not meaning:
            continue
        out.append(
            MeaningMapEntry(
                trigger=trigger,
                likely_meaning=meaning,
                confidence=float(item.get("confidence") or 0.0),
                evidence=_parse_evidence_refs(item.get("evidence")),
                last_seen_at=_clean(item.get("last_seen_at")) or None,
            )
        )
    return out


def _serialize_meaning_map(items: List[MeaningMapEntry]) -> List[Dict[str, Any]]:
    return [
        {
            "trigger": item.trigger,
            "likely_meaning": item.likely_meaning,
            "confidence": float(item.confidence),
            "evidence": _serialize_evidence_refs(item.evidence),
            "last_seen_at": item.last_seen_at,
        }
        for item in items
    ]


def _parse_response_preference_cues(value: Any) -> ResponsePreferenceCues:
    raw = value if isinstance(value, Mapping) else {}
    return ResponsePreferenceCues(
        prefers_receive_first=bool(raw.get("prefers_receive_first")),
        prefers_structure_when_long_memo=bool(raw.get("prefers_structure_when_long_memo")),
        prefers_continuity_reference=bool(raw.get("prefers_continuity_reference")),
        evidence=_parse_evidence_refs(raw.get("evidence")),
    )


def _serialize_response_preference_cues(value: ResponsePreferenceCues) -> Dict[str, Any]:
    return {
        "prefers_receive_first": bool(value.prefers_receive_first),
        "prefers_structure_when_long_memo": bool(value.prefers_structure_when_long_memo),
        "prefers_continuity_reference": bool(value.prefers_continuity_reference),
        "evidence": _serialize_evidence_refs(value.evidence),
    }


def _parse_partner_expectation(value: Any) -> PartnerExpectationProfile:
    raw = value if isinstance(value, Mapping) else {}
    return PartnerExpectationProfile(
        wants_continuity=bool(raw.get("wants_continuity")),
        wants_non_judgmental_receive=bool(raw.get("wants_non_judgmental_receive")),
        wants_precise_observation=bool(raw.get("wants_precise_observation")),
        evidence=_parse_evidence_refs(raw.get("evidence")),
    )


def _serialize_partner_expectation(value: PartnerExpectationProfile) -> Dict[str, Any]:
    return {
        "wants_continuity": bool(value.wants_continuity),
        "wants_non_judgmental_receive": bool(value.wants_non_judgmental_receive),
        "wants_precise_observation": bool(value.wants_precise_observation),
        "evidence": _serialize_evidence_refs(value.evidence),
    }


def _parse_interpretive_frame(value: Any) -> InterpretiveFrameProfile:
    raw = value if isinstance(value, Mapping) else {}
    return InterpretiveFrameProfile(
        value_anchors=_parse_value_anchors(raw.get("value_anchors")),
        meaning_map=_parse_meaning_map(raw.get("meaning_map")),
        response_preference_cues=_parse_response_preference_cues(raw.get("response_preference_cues")),
        partner_expectation=_parse_partner_expectation(raw.get("partner_expectation") or raw.get("partner_expectation_cues")),
        sensitivity_cues=dict(raw.get("sensitivity_cues") or {}) if isinstance(raw.get("sensitivity_cues"), Mapping) else {},
        expression_style_cues=dict(raw.get("expression_style_cues") or {}) if isinstance(raw.get("expression_style_cues"), Mapping) else {},
    )


def _serialize_interpretive_frame(value: InterpretiveFrameProfile) -> Dict[str, Any]:
    return {
        "value_anchors": _serialize_value_anchors(value.value_anchors),
        "meaning_map": _serialize_meaning_map(value.meaning_map),
        "response_preference_cues": _serialize_response_preference_cues(value.response_preference_cues),
        "partner_expectation": _serialize_partner_expectation(value.partner_expectation),
        "sensitivity_cues": dict(value.sensitivity_cues or {}),
        "expression_style_cues": dict(value.expression_style_cues or {}),
    }


def _parse_hypotheses(value: Any) -> List[DerivedModelHypothesis]:
    if not isinstance(value, list):
        return []
    out: List[DerivedModelHypothesis] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        key = _clean(item.get("key"))
        text = _clean(item.get("text"))
        if not key or not text:
            continue
        out.append(
            DerivedModelHypothesis(
                key=key,
                text=text,
                confidence=float(item.get("confidence") or 0.0),
                evidence=_parse_evidence_refs(item.get("evidence")),
                status=_clean(item.get("status")) or "active",
                last_seen_at=_clean(item.get("last_seen_at")) or None,
            )
        )
    return out


def _serialize_hypotheses(items: List[DerivedModelHypothesis]) -> List[Dict[str, Any]]:
    return [
        {
            "key": item.key,
            "text": item.text,
            "confidence": float(item.confidence),
            "evidence": _serialize_evidence_refs(item.evidence),
            "status": item.status,
            "last_seen_at": item.last_seen_at,
        }
        for item in items
    ]


def _parse_topic_anchors(value: Any) -> List[TopicAnchor]:
    if not isinstance(value, list):
        return []
    out: List[TopicAnchor] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        anchor_key = _clean(item.get("anchor_key"))
        label = _clean(item.get("label"))
        if not anchor_key or not label:
            continue
        out.append(
            TopicAnchor(
                anchor_key=anchor_key,
                label=label,
                confidence=float(item.get("confidence") or 0.0),
                evidence=_parse_evidence_refs(item.get("evidence")),
                last_seen_at=_clean(item.get("last_seen_at")) or None,
            )
        )
    return out


def _serialize_topic_anchors(items: List[TopicAnchor]) -> List[Dict[str, Any]]:
    return [
        {
            "anchor_key": item.anchor_key,
            "label": item.label,
            "confidence": float(item.confidence),
            "evidence": _serialize_evidence_refs(item.evidence),
            "last_seen_at": item.last_seen_at,
        }
        for item in items
    ]


def new_empty_derived_user_model(*, tier: str) -> DerivedUserModel:
    return DerivedUserModel(
        schema_version=MODEL_SCHEMA_VERSION,
        model_tier=_clean(tier).lower() or "plus",
        updated_at=_now_iso_z(),
        debug={"created_empty": True},
    )


def parse_derived_user_model(payload: Mapping[str, Any]) -> DerivedUserModel:
    raw = dict(payload or {})
    model_payload = raw.get("model_json") if isinstance(raw.get("model_json"), Mapping) else raw
    facts_value = model_payload.get("facts") if isinstance(model_payload.get("facts"), Mapping) else model_payload.get("factual_profile")
    return DerivedUserModel(
        schema_version=_clean(model_payload.get("schema_version") or raw.get("schema_version")) or MODEL_SCHEMA_VERSION,
        model_tier=_clean(model_payload.get("model_tier") or raw.get("model_tier")) or "plus",
        source_cursor=_parse_source_cursor(model_payload.get("source_cursor") or raw.get("source_cursor")),
        factual_profile=dict(facts_value or {}) if isinstance(facts_value, Mapping) else {},
        interpretive_frame=_parse_interpretive_frame(model_payload.get("interpretive_frame")),
        hypotheses=_parse_hypotheses(model_payload.get("hypotheses")),
        open_topic_anchors=_parse_topic_anchors(model_payload.get("open_topic_anchors") or (model_payload.get("anchors") or {}).get("open_loops")),
        recovery_anchors=_parse_topic_anchors(model_payload.get("recovery_anchors") or (model_payload.get("anchors") or {}).get("recovery_anchors")),
        updated_at=_clean(model_payload.get("updated_at") or raw.get("updated_at")) or None,
        debug=dict(model_payload.get("debug") or {}) if isinstance(model_payload.get("debug"), Mapping) else {},
    )


def serialize_derived_user_model(model: DerivedUserModel) -> Dict[str, Any]:
    model_payload = {
        "schema_version": _clean(model.schema_version) or MODEL_SCHEMA_VERSION,
        "model_tier": _clean(model.model_tier) or "plus",
        "source_cursor": _serialize_source_cursor(model.source_cursor),
        "facts": dict(model.factual_profile or {}),
        "interpretive_frame": _serialize_interpretive_frame(model.interpretive_frame),
        "hypotheses": _serialize_hypotheses(model.hypotheses),
        "open_topic_anchors": _serialize_topic_anchors(model.open_topic_anchors),
        "recovery_anchors": _serialize_topic_anchors(model.recovery_anchors),
        "updated_at": _clean(model.updated_at) or _now_iso_z(),
        "debug": dict(model.debug or {}),
    }
    return {
        "schema_version": model_payload["schema_version"],
        "model_tier": model_payload["model_tier"],
        "source_cursor": model_payload["source_cursor"],
        "model_json": model_payload,
        "updated_at": model_payload["updated_at"],
    }


async def load_emlis_ai_user_model_for_user(
    user_id: str,
    *,
    expected_tier: Optional[str] = None,
) -> Optional[DerivedUserModel]:
    uid = _clean(user_id)
    if not uid:
        return None

    if sb_get is not None:
        try:
            resp = await sb_get(
                f"/rest/v1/{MODEL_TABLE}",
                params={
                    "select": "user_id,schema_version,model_tier,source_cursor,model_json,updated_at",
                    "user_id": f"eq.{uid}",
                    "limit": "1",
                },
                timeout=4.0,
            )
            if resp.status_code < 300:
                rows = _pick_rows(resp)
                if rows:
                    row = rows[0]
                    _MEMORY_MODELS[uid] = dict(row)
                    model = parse_derived_user_model(row)
                    if expected_tier and _clean(expected_tier).lower() != _clean(model.model_tier).lower():
                        model.model_tier = _clean(expected_tier).lower() or model.model_tier
                    return model
        except Exception:
            pass

    memory_row = _MEMORY_MODELS.get(uid)
    if isinstance(memory_row, Mapping):
        model = parse_derived_user_model(memory_row)
        if expected_tier and _clean(expected_tier).lower() != _clean(model.model_tier).lower():
            model.model_tier = _clean(expected_tier).lower() or model.model_tier
        return model
    return None


async def save_emlis_ai_user_model_for_user(
    user_id: str,
    *,
    model: DerivedUserModel,
) -> None:
    uid = _clean(user_id)
    if not uid:
        return None
    row = {"user_id": uid, **serialize_derived_user_model(model)}
    _MEMORY_MODELS[uid] = dict(row)
    if sb_patch is None or sb_post is None:
        return None

    try:
        resp = await sb_patch(
            f"/rest/v1/{MODEL_TABLE}",
            params={"user_id": f"eq.{uid}"},
            json=row,
            prefer="return=representation",
            timeout=4.0,
        )
        if resp.status_code < 300 and _pick_rows(resp):
            return None
        await sb_post(
            f"/rest/v1/{MODEL_TABLE}",
            json=row,
            params={"on_conflict": "user_id"},
            prefer="resolution=merge-duplicates,return=minimal",
            timeout=4.0,
        )
    except Exception:
        return None
