# -*- coding: utf-8 -*-
from __future__ import annotations

"""Meaning-layer readers used by EmlisAI.

EmlisAI should depend on stable read contracts, not route modules.
This boundary is intentionally thin so context collection only sees canonical
reader functions for input status, analysis summary artifacts, and internal
cross-core anchors owned by the current user.
"""

import os
from typing import Any, Dict, List, Mapping, Optional

from analysis_summary_reader import get_myweb_home_summary_from_artifacts
from emlis_ai_types import EmlisContextAnchorPacket
from emlis_context_anchor_service import extract_emlis_context_anchors, packet_anchor_count
from input_summary_reader import get_input_summary_snapshot
from supabase_client import sb_get

PIECES_READ_TABLE = (
    os.getenv("COCOLON_PIECES_READ_TABLE")
    or os.getenv("COCOLON_MYMODEL_REFLECTIONS_READ_TABLE")
    or os.getenv("MYMODEL_REFLECTIONS_READ_TABLE")
    or "pieces"
).strip() or "pieces"
ANALYSIS_REPORTS_READ_TABLE = (
    os.getenv("COCOLON_ANALYSIS_REPORTS_READ_TABLE")
    or os.getenv("ANALYSIS_REPORTS_READ_TABLE")
    or os.getenv("COCOLON_MYWEB_REPORTS_READ_TABLE")
    or os.getenv("MYWEB_REPORTS_READ_TABLE")
    or "analysis_reports"
).strip() or "analysis_reports"
SELF_STRUCTURE_REPORTS_READ_TABLE = (
    os.getenv("COCOLON_SELF_STRUCTURE_REPORTS_READ_TABLE")
    or os.getenv("SELF_STRUCTURE_REPORTS_READ_TABLE")
    or os.getenv("COCOLON_MYPROFILE_REPORTS_READ_TABLE")
    or os.getenv("MYPROFILE_REPORTS_READ_TABLE")
    or "self_structure_reports"
).strip() or "self_structure_reports"


def _pick_rows(resp: Any) -> List[Dict[str, Any]]:
    try:
        data = resp.json()
    except Exception:
        return []
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        return [data]
    return []


def _content_json(row: Mapping[str, Any]) -> Dict[str, Any]:
    raw = row.get("content_json")
    return dict(raw) if isinstance(raw, Mapping) else {}


def _packet_from_mapping(packet: Mapping[str, Any], *, row: Mapping[str, Any], fallback_kind: str) -> EmlisContextAnchorPacket:
    source_kind = str(packet.get("source_kind") or fallback_kind or "unknown").strip()
    source_id = str(packet.get("source_id") or row.get("id") or row.get("public_id") or "").strip() or None
    source_updated_at = str(row.get("updated_at") or row.get("generated_at") or row.get("published_at") or row.get("created_at") or "").strip() or None
    return EmlisContextAnchorPacket(
        schema_version=str(packet.get("schema_version") or "emlis_context_anchor.v1"),
        source_kind=source_kind,
        source_id=source_id,
        source_updated_at=source_updated_at,
        value_anchors=list(packet.get("value_anchors") or []) if isinstance(packet.get("value_anchors"), list) else [],
        state_anchors=list(packet.get("state_anchors") or []) if isinstance(packet.get("state_anchors"), list) else [],
        individuality_anchors=list(packet.get("individuality_anchors") or []) if isinstance(packet.get("individuality_anchors"), list) else [],
        boundary_anchors=list(packet.get("boundary_anchors") or []) if isinstance(packet.get("boundary_anchors"), list) else [],
        concept_anchors=list(packet.get("concept_anchors") or []) if isinstance(packet.get("concept_anchors"), list) else [],
        reply_hints=list(packet.get("reply_hints") or []) if isinstance(packet.get("reply_hints"), list) else [],
        evidence_refs=list(packet.get("evidence_refs") or []) if isinstance(packet.get("evidence_refs"), list) else [],
        safety=dict(packet.get("safety") or {}) if isinstance(packet.get("safety"), Mapping) else {},
    )


def _append_packets_from_rows(
    out: List[EmlisContextAnchorPacket],
    rows: List[Dict[str, Any]],
    *,
    fallback_kind: str,
    max_anchor_count: int,
) -> None:
    for row in rows or []:
        for packet in extract_emlis_context_anchors(_content_json(row)):
            item = _packet_from_mapping(packet, row=row, fallback_kind=fallback_kind)
            if packet_anchor_count(packet.__dict__ if hasattr(packet, "__dict__") else packet) <= 0:
                continue
            out.append(item)
            if len(out) >= max(1, int(max_anchor_count or 1)):
                return


async def get_input_summary_for_emlis_ai(user_id: str) -> Dict[str, Any]:
    try:
        return await get_input_summary_snapshot(user_id)
    except Exception:
        return {}


async def get_myweb_home_summary_for_emlis_ai(user_id: str) -> Dict[str, Any]:
    try:
        return await get_myweb_home_summary_from_artifacts(user_id)
    except Exception:
        return {}


async def _fetch_piece_anchor_rows(user_id: str, *, limit: int) -> List[Dict[str, Any]]:
    resp = await sb_get(
        f"/rest/v1/{PIECES_READ_TABLE}",
        params={
            "select": "id,public_id,source_type,question,answer,content_json,updated_at,created_at,published_at",
            "owner_user_id": f"eq.{user_id}",
            "is_active": "eq.true",
            "order": "updated_at.desc,created_at.desc",
            "limit": str(max(1, min(int(limit or 8), 30))),
        },
        timeout=6.0,
    )
    if resp.status_code >= 300:
        return []
    return _pick_rows(resp)


async def _fetch_emotion_report_anchor_rows(user_id: str, *, limit: int) -> List[Dict[str, Any]]:
    resp = await sb_get(
        f"/rest/v1/{ANALYSIS_REPORTS_READ_TABLE}",
        params={
            "select": "id,report_type,period_start,period_end,content_json,generated_at,updated_at",
            "user_id": f"eq.{user_id}",
            "order": "generated_at.desc,updated_at.desc",
            "limit": str(max(1, min(int(limit or 4), 12))),
        },
        timeout=6.0,
    )
    if resp.status_code >= 300:
        return []
    return _pick_rows(resp)


async def _fetch_self_structure_report_anchor_rows(user_id: str, *, limit: int) -> List[Dict[str, Any]]:
    resp = await sb_get(
        f"/rest/v1/{SELF_STRUCTURE_REPORTS_READ_TABLE}",
        params={
            "select": "id,report_type,period_start,period_end,content_json,generated_at,updated_at",
            "user_id": f"eq.{user_id}",
            "order": "generated_at.desc,updated_at.desc",
            "limit": str(max(1, min(int(limit or 4), 12))),
        },
        timeout=6.0,
    )
    if resp.status_code >= 300:
        return []
    return _pick_rows(resp)


async def get_cross_core_context_for_emlis_ai(user_id: str, *, max_anchor_count: Optional[int] = None) -> List[EmlisContextAnchorPacket]:
    """Read current user's Piece / report anchors for Premium EmlisAI.

    The caller is responsible for capability gating.  This reader is best-effort:
    failures return an empty list so the immediate reply path falls back to the
    existing current-input / history pipeline.
    """
    uid = str(user_id or "").strip()
    if not uid:
        return []
    limit = max(1, int(max_anchor_count or 12))
    try:
        piece_rows = await _fetch_piece_anchor_rows(uid, limit=min(limit, 8))
        emotion_rows = await _fetch_emotion_report_anchor_rows(uid, limit=min(limit, 4))
        self_rows = await _fetch_self_structure_report_anchor_rows(uid, limit=min(limit, 4))
    except Exception:
        return []

    packets: List[EmlisContextAnchorPacket] = []
    _append_packets_from_rows(packets, piece_rows, fallback_kind="piece", max_anchor_count=limit)
    if len(packets) < limit:
        _append_packets_from_rows(packets, emotion_rows, fallback_kind="emotion_report", max_anchor_count=limit)
    if len(packets) < limit:
        _append_packets_from_rows(packets, self_rows, fallback_kind="self_structure_report", max_anchor_count=limit)
    return packets[:limit]
