from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple

from fastapi import HTTPException

from piece_generated_display import get_public_generated_reflection_text
from piece_generated_identity import compute_generated_question_q_key
from piece_public_read_store import MYMODEL_REFLECTIONS_READ_TABLE, has_myprofile_link, quoted_in, sb_get_json

EMOTION_GENERATED_SOURCE_TYPE = "emotion_generated"


def row_source_type(row: Dict[str, Any]) -> str:
    return str((row or {}).get("source_type") or "").strip()


def is_generated_reflection_instance_id(q_instance_id: str) -> bool:
    return str(q_instance_id or "").strip().startswith("reflection:")


def generated_lookup_values(q_instance_id: str) -> Set[str]:
    raw = str(q_instance_id or "").strip()
    if not raw:
        return set()
    values: Set[str] = {raw}
    if raw.startswith("reflection:"):
        values.add(raw.split(":", 1)[1].strip())
    else:
        values.add(f"reflection:{raw}")
    return {value for value in values if str(value or "").strip()}


def generated_lookup_id(q_instance_id: str) -> str:
    for value in generated_lookup_values(q_instance_id):
        if value.startswith("reflection:"):
            candidate = value.split(":", 1)[1].strip()
            if candidate:
                return candidate
    values = list(generated_lookup_values(q_instance_id))
    return values[0] if values else ""


def build_generated_q_key(row: Dict[str, Any]) -> str:
    qk = str((row or {}).get("q_key") or "").strip()
    if qk:
        return qk
    question = str((row or {}).get("question") or "").strip()
    if question:
        return compute_generated_question_q_key(question)
    topic_key = str((row or {}).get("topic_key") or "").strip()
    if topic_key:
        return f"generated:{topic_key}"
    rid = str((row or {}).get("id") or "").strip()
    return f"generated:{rid}" if rid else "generated:unknown"


def generated_public_id(row: Dict[str, Any]) -> str:
    raw = str((row or {}).get("public_id") or (row or {}).get("id") or "").strip()
    if not raw:
        return ""
    return raw if raw.startswith("reflection:") else f"reflection:{raw}"


def generated_row_sort_key(row: Dict[str, Any]) -> Tuple[str, str]:
    return (
        str((row or {}).get("published_at") or (row or {}).get("updated_at") or (row or {}).get("created_at") or "").strip(),
        str((row or {}).get("id") or "").strip(),
    )


async def fetch_emotion_generated_row_by_instance_id(q_instance_id: str) -> Optional[Dict[str, Any]]:
    lookup_values = generated_lookup_values(q_instance_id)
    lookup_id = generated_lookup_id(q_instance_id)
    merged: Dict[str, Dict[str, Any]] = {}
    if lookup_id:
        rows = await sb_get_json(
            f"/rest/v1/{MYMODEL_REFLECTIONS_READ_TABLE}",
            params={
                "select": "*",
                "id": f"eq.{lookup_id}",
                "source_type": f"eq.{EMOTION_GENERATED_SOURCE_TYPE}",
                "is_active": "eq.true",
                "status": "in.(ready,published)",
                "limit": "1",
            },
        )
        for row in rows:
            rid = str((row or {}).get("id") or "").strip()
            if rid:
                merged[rid] = row
    if lookup_values:
        rows = await sb_get_json(
            f"/rest/v1/{MYMODEL_REFLECTIONS_READ_TABLE}",
            params={
                "select": "*",
                "public_id": quoted_in(lookup_values),
                "source_type": f"eq.{EMOTION_GENERATED_SOURCE_TYPE}",
                "is_active": "eq.true",
                "status": "in.(ready,published)",
                "limit": str(max(1, len(lookup_values))),
            },
        )
        for row in rows:
            rid = str((row or {}).get("id") or "").strip()
            if rid:
                merged[rid] = row
    visible = [row for row in merged.values() if get_public_generated_reflection_text(row)]
    if not visible:
        return None
    visible.sort(key=generated_row_sort_key, reverse=True)
    return visible[0]


async def fetch_active_emotion_generated_reflections_for_owner(owner_user_id: str, *, limit: int = 200) -> List[Dict[str, Any]]:
    oid = str(owner_user_id or "").strip()
    if not oid:
        return []
    rows = await sb_get_json(
        f"/rest/v1/{MYMODEL_REFLECTIONS_READ_TABLE}",
        params={
            "select": "*",
            "owner_user_id": f"eq.{oid}",
            "source_type": f"eq.{EMOTION_GENERATED_SOURCE_TYPE}",
            "is_active": "eq.true",
            "status": "in.(ready,published)",
            "order": "published_at.desc,updated_at.desc",
            "limit": str(max(1, int(limit))),
        },
    )
    visible_rows = [row for row in rows if get_public_generated_reflection_text(row)]
    return sorted(visible_rows, key=generated_row_sort_key, reverse=True)


async def resolve_generated_reflection_access(*, viewer_user_id: str, q_instance_id: str) -> Dict[str, Any]:
    row = await fetch_emotion_generated_row_by_instance_id(q_instance_id)
    if not row:
        raise HTTPException(status_code=404, detail="Reflection not found")
    if row_source_type(row) != EMOTION_GENERATED_SOURCE_TYPE:
        raise HTTPException(status_code=404, detail="Reflection not found")
    owner_user_id = str((row or {}).get("owner_user_id") or "").strip()
    if not owner_user_id:
        raise HTTPException(status_code=404, detail="Reflection not found")
    if owner_user_id != str(viewer_user_id):
        allowed = await has_myprofile_link(viewer_user_id=viewer_user_id, owner_user_id=owner_user_id)
        if not allowed:
            raise HTTPException(status_code=403, detail="You are not allowed to query this MyProfile")
    if not get_public_generated_reflection_text(row):
        raise HTTPException(status_code=404, detail="Reflection not found")
    return row


__all__ = [
    "EMOTION_GENERATED_SOURCE_TYPE",
    "build_generated_q_key",
    "fetch_active_emotion_generated_reflections_for_owner",
    "fetch_emotion_generated_row_by_instance_id",
    "generated_public_id",
    "generated_row_sort_key",
    "is_generated_reflection_instance_id",
    "resolve_generated_reflection_access",
    "row_source_type",
]
