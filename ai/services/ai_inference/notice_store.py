# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping, Optional

from fastapi import HTTPException

from client_compat import normalize_optional_str_list
from subscription_store import get_subscription_tier_for_user
from supabase_client import ensure_supabase_config, sb_get, sb_post
from response_microcache import get_or_compute

APP_NOTICES_TABLE = (os.getenv("APP_NOTICES_TABLE") or "app_notices").strip() or "app_notices"
APP_NOTICE_USER_STATES_TABLE = (os.getenv("APP_NOTICE_USER_STATES_TABLE") or "app_notice_user_states").strip() or "app_notice_user_states"
APP_NOTICES_ENABLED = (os.getenv("APP_NOTICES_ENABLED") or "true").strip().lower() in ("1", "true", "yes", "on")
APP_NOTICE_FETCH_LIMIT = int(os.getenv("APP_NOTICE_FETCH_LIMIT", "300") or "300")
APP_NOTICE_HISTORY_MAX_LIMIT = int(os.getenv("APP_NOTICE_HISTORY_MAX_LIMIT", "100") or "100")

logger = logging.getLogger("notice_store")


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(str(raw).strip())
    except Exception:
        return default


NOTICE_CURRENT_CATALOG_CACHE_TTL_SECONDS = max(0.0, _env_float("APP_NOTICE_CURRENT_CATALOG_CACHE_TTL_SECONDS", 20.0))
NOTICE_CURRENT_ROW_SELECT = ",".join([
    "id",
    "notice_key",
    "version",
    "title",
    "category",
    "priority",
    "published_at",
    "created_at",
    "start_at_utc",
    "end_at_utc",
    "status",
    "requires_popup",
    "popup_once",
    "target_platform_json",
    "target_tiers_json",
    "min_app_version",
    "max_app_version",
])
NOTICE_CURRENT_STATE_SELECT = "notice_id,read_at,popup_seen_at"
NOTICE_STATE_MUTATION_SELECT = "notice_id,read_at,popup_seen_at,created_at"

_VERSION_SPLIT_RE = re.compile(r"[^0-9A-Za-z]+")
_BODY_ACTION_TOKEN_RE = re.compile(r"\{\{\s*([A-Za-z0-9_.:-]+)\s*\}\}")


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _iso_utc(dt: Optional[datetime] = None) -> str:
    return (dt or _now_utc()).astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(value)
    except Exception:
        return default


def _safe_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    s = str(value).strip().lower()
    if s in {"1", "true", "yes", "on"}:
        return True
    if s in {"0", "false", "no", "off"}:
        return False
    return default


def _parse_jsonish(value: Any, default: Any) -> Any:
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return default
        try:
            return json.loads(s)
        except Exception:
            return default
    return default


def _normalize_platform(value: Any) -> Optional[str]:
    s = str(value or "").strip().lower()
    return s or None


def _normalize_tier(value: Any) -> str:
    s = str(getattr(value, "value", value) or "free").strip().lower() or "free"
    return s


def _extract_version_parts(value: Any) -> List[int]:
    raw = str(value or "").strip()
    if not raw:
        return []
    out: List[int] = []
    for piece in _VERSION_SPLIT_RE.split(raw):
        if not piece:
            continue
        if piece.isdigit():
            out.append(int(piece))
            continue
        digit_prefix = ""
        for ch in piece:
            if ch.isdigit():
                digit_prefix += ch
            else:
                break
        if digit_prefix:
            out.append(int(digit_prefix))
    return out


def _compare_versions(left: Any, right: Any) -> int:
    left_parts = _extract_version_parts(left)
    right_parts = _extract_version_parts(right)
    if not left_parts or not right_parts:
        return 0
    length = max(len(left_parts), len(right_parts))
    for idx in range(length):
        l_val = left_parts[idx] if idx < len(left_parts) else 0
        r_val = right_parts[idx] if idx < len(right_parts) else 0
        if l_val < r_val:
            return -1
        if l_val > r_val:
            return 1
    return 0


def _version_matches(client_version: Optional[str], *, min_version: Optional[str], max_version: Optional[str]) -> bool:
    cur = str(client_version or "").strip()
    if min_version and cur:
        if _compare_versions(cur, min_version) < 0:
            return False
    if max_version and cur:
        if _compare_versions(cur, max_version) > 0:
            return False
    return True


def _parse_iso_datetime(value: Any) -> Optional[datetime]:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        normalized = raw.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _started_at(row: Mapping[str, Any]) -> Optional[datetime]:
    return _parse_iso_datetime(row.get("start_at_utc")) or _parse_iso_datetime(row.get("published_at"))


def _has_started(row: Mapping[str, Any], now_utc: datetime) -> bool:
    start_dt = _started_at(row)
    if start_dt is None:
        return True
    return start_dt <= now_utc


def _is_currently_active(row: Mapping[str, Any], now_utc: datetime) -> bool:
    if str(row.get("status") or "").strip().lower() != "active":
        return False
    if not _has_started(row, now_utc):
        return False
    end_dt = _parse_iso_datetime(row.get("end_at_utc"))
    if end_dt is not None and end_dt <= now_utc:
        return False
    return True


def _priority_rank(value: Any) -> int:
    priority = str(value or "").strip().lower()
    if priority == "high":
        return 3
    if priority == "normal":
        return 2
    if priority == "low":
        return 1
    return 0


def _notice_sort_key(row: Mapping[str, Any]) -> tuple:
    published = str(row.get("published_at") or row.get("start_at_utc") or row.get("created_at") or "")
    return (_priority_rank(row.get("priority")), published)


def _normalize_platform_targets(value: Any) -> List[str]:
    parsed = _parse_jsonish(value, value)
    targets = normalize_optional_str_list(parsed)
    return [str(v).strip().lower() for v in targets if str(v).strip()]


def _normalize_tier_targets(value: Any) -> List[str]:
    parsed = _parse_jsonish(value, value)
    targets = normalize_optional_str_list(parsed)
    return [str(v).strip().lower() for v in targets if str(v).strip()]


def _platform_matches(client_platform: Optional[str], target_platforms: Iterable[str]) -> bool:
    targets = [str(v).strip().lower() for v in target_platforms if str(v).strip()]
    if not targets:
        return True
    cur = _normalize_platform(client_platform)
    if not cur:
        return False
    return cur in targets


def _tier_matches(client_tier: str, target_tiers: Iterable[str]) -> bool:
    targets = [str(v).strip().lower() for v in target_tiers if str(v).strip()]
    if not targets or "all" in targets:
        return True
    return _normalize_tier(client_tier) in targets


def _raise_http_from_supabase(resp, default_detail: str) -> None:
    detail = default_detail
    try:
        js = resp.json()
        if isinstance(js, dict):
            detail = str(js.get("message") or js.get("hint") or js.get("details") or js.get("detail") or default_detail)
        elif js:
            detail = str(js)
    except Exception:
        txt = (getattr(resp, "text", "") or "").strip()
        if txt:
            detail = txt[:500]
    raise HTTPException(status_code=502, detail=detail)


def _normalize_notice_action_kind(value: Any) -> str:
    kind = str(value or "none").strip().lower() or "none"
    if kind in {"url", "internal_route"}:
        return kind
    return "none"


def _normalize_notice_action_placement(value: Any) -> str:
    placement = str(value or "button").strip().lower() or "button"
    if placement in {"inline", "button", "both"}:
        return placement
    return "button"


def _cta_public(row: Mapping[str, Any]) -> Dict[str, Any]:
    raw_params = _parse_jsonish(row.get("cta_params_json"), {})
    params = raw_params if isinstance(raw_params, dict) else {}
    kind = _normalize_notice_action_kind(row.get("cta_kind"))
    return {
        "kind": kind,
        "label": str(row.get("cta_label") or "").strip() or None,
        "route": str(row.get("cta_route") or "").strip() or None,
        "params": params,
        "url": str(row.get("cta_url") or "").strip() or None,
    }


def _notice_actions_public(row: Mapping[str, Any]) -> List[Dict[str, Any]]:
    raw_actions = _parse_jsonish(row.get("actions_json"), [])
    if not isinstance(raw_actions, list):
        return []

    out: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for idx, raw in enumerate(raw_actions):
        if not isinstance(raw, dict):
            continue
        kind = _normalize_notice_action_kind(raw.get("kind"))
        if kind == "none":
            continue
        label = str(raw.get("label") or "").strip() or None
        if not label:
            continue
        route = str(raw.get("route") or "").strip() or None
        url = str(raw.get("url") or "").strip() or None
        if kind == "url" and not url:
            continue
        if kind == "internal_route" and not route:
            continue
        params = raw.get("params") if isinstance(raw.get("params"), dict) else {}
        key = str(raw.get("key") or "").strip() or f"action_{idx + 1}"
        signature = f"{key}|{kind}|{route or ''}|{url or ''}|{label}"
        if signature in seen:
            continue
        seen.add(signature)
        out.append({
            "key": key,
            "label": label,
            "kind": kind,
            "route": route,
            "params": params,
            "url": url,
            "placement": _normalize_notice_action_placement(raw.get("placement")),
        })
    return out


def _compact_body_segments(segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not segments:
        return []
    out: List[Dict[str, Any]] = []
    for segment in segments:
        seg_type = str(segment.get("type") or "text").strip().lower() or "text"
        seg_text = str(segment.get("text") or "")
        if not seg_text:
            continue
        if seg_type == "text" and out and str(out[-1].get("type") or "text") == "text":
            out[-1]["text"] = str(out[-1].get("text") or "") + seg_text
            continue
        item = {"type": seg_type, "text": seg_text}
        action_key = str(segment.get("action_key") or "").strip() or None
        if action_key:
            item["action_key"] = action_key
        out.append(item)
    return out


def _resolved_notice_body(raw_body: Any, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
    body_template = str(raw_body or "").strip()
    if not body_template:
        return {
            "body": "",
            "body_format": "plain_text",
            "body_segments": [],
        }

    if not actions:
        return {
            "body": body_template,
            "body_format": "plain_text",
            "body_segments": [],
        }

    actions_by_key = {
        str(action.get("key") or "").strip(): action
        for action in actions
        if str(action.get("key") or "").strip()
    }
    inline_actions_by_key = {
        key: action
        for key, action in actions_by_key.items()
        if str(action.get("placement") or "button").strip().lower() in {"inline", "both"}
    }

    resolved_parts: List[str] = []
    segments: List[Dict[str, Any]] = []
    cursor = 0
    inline_segment_count = 0

    for match in _BODY_ACTION_TOKEN_RE.finditer(body_template):
        start, end = match.span()
        token_key = str(match.group(1) or "").strip()
        if start > cursor:
            plain = body_template[cursor:start]
            if plain:
                resolved_parts.append(plain)
                segments.append({"type": "text", "text": plain})
        action = actions_by_key.get(token_key)
        fallback_text = str((action or {}).get("label") or match.group(0) or "")
        if fallback_text:
            resolved_parts.append(fallback_text)
        inline_action = inline_actions_by_key.get(token_key)
        if inline_action and fallback_text:
            segments.append({
                "type": "action",
                "text": fallback_text,
                "action_key": token_key,
            })
            inline_segment_count += 1
        elif fallback_text:
            segments.append({"type": "text", "text": fallback_text})
        cursor = end

    if cursor < len(body_template):
        tail = body_template[cursor:]
        if tail:
            resolved_parts.append(tail)
            segments.append({"type": "text", "text": tail})

    if not resolved_parts:
        resolved_parts.append(body_template)
        segments.append({"type": "text", "text": body_template})

    compact_segments = _compact_body_segments(segments)
    return {
        "body": "".join(resolved_parts).strip(),
        "body_format": "inline_links_v1" if inline_segment_count > 0 else "plain_text",
        "body_segments": compact_segments if inline_segment_count > 0 else [],
    }


def _notice_public(row: Mapping[str, Any], state_row: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    read_at = str((state_row or {}).get("read_at") or "").strip() or None
    popup_seen_at = str((state_row or {}).get("popup_seen_at") or "").strip() or None
    actions = _notice_actions_public(row)
    resolved_body = _resolved_notice_body(row.get("body"), actions)
    body_format = str(row.get("body_format") or resolved_body.get("body_format") or "plain_text").strip() or "plain_text"
    if resolved_body.get("body_segments"):
        body_format = "inline_links_v1"
    return {
        "notice_id": str(row.get("id") or ""),
        "notice_key": str(row.get("notice_key") or "").strip() or None,
        "version": int(row.get("version") or 1),
        "title": str(row.get("title") or "").strip(),
        "body": str(resolved_body.get("body") or "").strip(),
        "body_format": body_format,
        "body_segments": resolved_body.get("body_segments") or [],
        "actions": actions,
        "category": str(row.get("category") or "other").strip() or "other",
        "priority": str(row.get("priority") or "normal").strip() or "normal",
        "published_at": str(row.get("published_at") or row.get("start_at_utc") or row.get("created_at") or "").strip() or None,
        "is_read": bool(read_at),
        "read_at": read_at,
        "popup_seen_at": popup_seen_at,
        "cta": _cta_public(row),
    }


class NoticeStore:
    async def _select_rows(self, table_or_path: str, *, params: Dict[str, str]) -> List[Dict[str, Any]]:
        ensure_supabase_config()
        path = str(table_or_path or "").strip()
        if not path.startswith("/"):
            path = f"/rest/v1/{path}"
        resp = await sb_get(path, params=params, timeout=10.0)
        if resp.status_code not in (200, 206):
            _raise_http_from_supabase(resp, f"Failed to query {table_or_path}")
        data = resp.json()
        if isinstance(data, list):
            return [row for row in data if isinstance(row, dict)]
        if isinstance(data, dict):
            return [data]
        return []

    async def _upsert_state_rows(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not rows:
            return []
        ensure_supabase_config()
        resp = await sb_post(
            f"/rest/v1/{APP_NOTICE_USER_STATES_TABLE}?on_conflict=user_id,notice_id",
            json=rows,
            prefer="resolution=merge-duplicates,return=representation",
            timeout=10.0,
        )
        if resp.status_code >= 300:
            _raise_http_from_supabase(resp, f"Failed to upsert {APP_NOTICE_USER_STATES_TABLE}")
        if resp.status_code == 204:
            return []
        data = resp.json()
        if isinstance(data, list):
            return [row for row in data if isinstance(row, dict)]
        if isinstance(data, dict):
            return [data]
        return []

    async def _fetch_notice_rows(self, *, include_draft: bool = False, select: str = "*") -> List[Dict[str, Any]]:
        params = {
            "select": str(select or "*") or "*",
            "order": "published_at.desc,created_at.desc",
            "limit": str(max(1, APP_NOTICE_FETCH_LIMIT)),
        }
        if not include_draft:
            params["status"] = "neq.draft"
        return await self._select_rows(APP_NOTICES_TABLE, params=params)

    async def _fetch_notice_rows_by_ids(self, notice_ids: Iterable[str], *, select: str = "*") -> List[Dict[str, Any]]:
        ids = [str(value or "").strip() for value in notice_ids if str(value or "").strip()]
        if not ids:
            return []
        quoted = ",".join('"' + value.replace('"', '') + '"' for value in ids)
        return await self._select_rows(
            APP_NOTICES_TABLE,
            params={
                "select": str(select or "*") or "*",
                "id": f"in.({quoted})",
                "limit": str(max(len(ids), 1)),
            },
        )

    async def _fetch_state_rows_for_user(
        self,
        user_id: str,
        notice_ids: Iterable[str],
        *,
        select: str = "*",
    ) -> Dict[str, Dict[str, Any]]:
        ids = [str(value or "").strip() for value in notice_ids if str(value or "").strip()]
        uid = str(user_id or "").strip()
        if not uid or not ids:
            return {}
        quoted = ",".join('"' + value.replace('"', '') + '"' for value in ids)
        rows = await self._select_rows(
            APP_NOTICE_USER_STATES_TABLE,
            params={
                "select": str(select or "*") or "*",
                "user_id": f"eq.{uid}",
                "notice_id": f"in.({quoted})",
                "limit": str(max(len(ids), 1)),
            },
        )
        out: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            notice_id = str(row.get("notice_id") or "").strip()
            if not notice_id:
                continue
            out[notice_id] = row
        return out

    async def _fetch_current_notice_catalog_rows(self) -> List[Dict[str, Any]]:
        async def _producer() -> List[Dict[str, Any]]:
            try:
                return await self._fetch_notice_rows(include_draft=False, select=NOTICE_CURRENT_ROW_SELECT)
            except Exception as exc:
                logger.warning("notice current slim-select fallback activated: err=%r", exc)
                return await self._fetch_notice_rows(include_draft=False, select="*")

        return await get_or_compute(
            "notice_catalog:current",
            NOTICE_CURRENT_CATALOG_CACHE_TTL_SECONDS,
            _producer,
        )

    async def _fetch_current_state_rows_for_user(self, user_id: str, notice_ids: Iterable[str]) -> Dict[str, Dict[str, Any]]:
        uid = str(user_id or "").strip()
        ids = [str(value or "").strip() for value in notice_ids if str(value or "").strip()]
        if not uid or not ids:
            return {}
        try:
            return await self._fetch_state_rows_for_user(uid, ids, select=NOTICE_CURRENT_STATE_SELECT)
        except Exception as exc:
            logger.warning(
                "notice current state slim-select fallback activated: user_id=%s err=%r",
                uid,
                exc,
            )
            return await self._fetch_state_rows_for_user(uid, ids, select="*")

    async def _fetch_notice_row_for_popup(self, notice_id: str) -> Optional[Dict[str, Any]]:
        rows = await self._fetch_notice_rows_by_ids([notice_id], select="*")
        if not rows:
            return None
        row0 = rows[0]
        return row0 if isinstance(row0, dict) else None

    async def _client_tier(self, user_id: str) -> str:
        tier = await get_subscription_tier_for_user(user_id)
        return _normalize_tier(tier)

    def _matches_client(self, row: Mapping[str, Any], *, client_meta: Mapping[str, Any], tier: str) -> bool:
        target_platforms = _normalize_platform_targets(row.get("target_platform_json"))
        if not _platform_matches(client_meta.get("platform"), target_platforms):
            return False
        target_tiers = _normalize_tier_targets(row.get("target_tiers_json"))
        if not _tier_matches(tier, target_tiers):
            return False
        if not _version_matches(
            client_meta.get("app_version"),
            min_version=str(row.get("min_app_version") or "").strip() or None,
            max_version=str(row.get("max_app_version") or "").strip() or None,
        ):
            return False
        return True

    def _filter_visible_rows(
        self,
        rows: Iterable[Mapping[str, Any]],
        *,
        client_meta: Mapping[str, Any],
        tier: str,
        include_expired_history: bool,
    ) -> List[Dict[str, Any]]:
        now_utc = _now_utc()
        visible: List[Dict[str, Any]] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            if not self._matches_client(row, client_meta=client_meta, tier=tier):
                continue
            if not _has_started(row, now_utc):
                continue
            if (not include_expired_history) and (not _is_currently_active(row, now_utc)):
                continue
            visible.append(dict(row))
        visible.sort(key=_notice_sort_key, reverse=True)
        return visible

    @staticmethod
    def _has_full_notice_payload(row: Mapping[str, Any]) -> bool:
        return any(key in row for key in ("body", "actions_json", "cta_kind", "cta_label", "cta_route", "cta_url", "body_format"))

    async def _visible_notice_rows(self, user_id: str, client_meta: Mapping[str, Any], *, include_expired_history: bool) -> List[Dict[str, Any]]:
        if not APP_NOTICES_ENABLED:
            return []
        tier = await self._client_tier(user_id)
        rows = await self._fetch_notice_rows(include_draft=False)
        return self._filter_visible_rows(
            rows,
            client_meta=client_meta,
            tier=tier,
            include_expired_history=include_expired_history,
        )

    async def fetch_current_notice_bundle(self, user_id: str, client_meta: Mapping[str, Any]) -> Dict[str, Any]:
        if not APP_NOTICES_ENABLED:
            return {
                "feature_enabled": False,
                "unread_count": 0,
                "has_unread": False,
                "badge": {"show": False, "count": 0},
                "popup_notice": None,
            }

        tier = await self._client_tier(user_id)
        catalog_rows = await self._fetch_current_notice_catalog_rows()
        visible_rows = self._filter_visible_rows(
            catalog_rows,
            client_meta=client_meta,
            tier=tier,
            include_expired_history=True,
        )
        notice_ids = [str(row.get("id") or "") for row in visible_rows if str(row.get("id") or "").strip()]
        state_rows = await self._fetch_current_state_rows_for_user(user_id, notice_ids)

        unread_count = 0
        popup_candidate: Optional[Dict[str, Any]] = None
        popup_state: Optional[Dict[str, Any]] = None
        now_utc = _now_utc()

        for row in visible_rows:
            notice_id = str(row.get("id") or "").strip()
            state = state_rows.get(notice_id) if notice_id else None
            if not str((state or {}).get("read_at") or "").strip():
                unread_count += 1

            if popup_candidate is not None:
                continue
            if not _is_currently_active(row, now_utc):
                continue
            if not _safe_bool(row.get("requires_popup"), False):
                continue
            popup_once = _safe_bool(row.get("popup_once"), True)
            popup_seen_at = str((state or {}).get("popup_seen_at") or "").strip() or None
            if popup_once and popup_seen_at:
                continue
            popup_candidate = row
            popup_state = state

        popup_notice = None
        if popup_candidate is not None:
            materialized_row: Mapping[str, Any] = popup_candidate
            if not self._has_full_notice_payload(popup_candidate):
                notice_id = str(popup_candidate.get("id") or "").strip()
                if notice_id:
                    try:
                        full_row = await self._fetch_notice_row_for_popup(notice_id)
                        if full_row is not None:
                            materialized_row = full_row
                    except Exception as exc:
                        logger.warning(
                            "notice current popup full-fetch failed: user_id=%s notice_id=%s err=%r",
                            user_id,
                            notice_id,
                            exc,
                        )
            popup_notice = _notice_public(materialized_row, popup_state)

        return {
            "feature_enabled": bool(APP_NOTICES_ENABLED),
            "unread_count": unread_count,
            "has_unread": unread_count > 0,
            "badge": {
                "show": unread_count > 0,
                "count": unread_count,
            },
            "popup_notice": popup_notice,
        }

    async def list_notice_history(
        self,
        user_id: str,
        client_meta: Mapping[str, Any],
        *,
        limit: int = 30,
        offset: int = 0,
    ) -> Dict[str, Any]:
        safe_limit = max(1, min(_safe_int(limit, 30), APP_NOTICE_HISTORY_MAX_LIMIT))
        safe_offset = max(0, _safe_int(offset, 0))
        visible_rows = await self._visible_notice_rows(user_id, client_meta, include_expired_history=True)
        notice_ids = [str(row.get("id") or "") for row in visible_rows if str(row.get("id") or "").strip()]
        state_rows = await self._fetch_state_rows_for_user(user_id, notice_ids, select=NOTICE_CURRENT_STATE_SELECT)

        items = [_notice_public(row, state_rows.get(str(row.get("id") or "").strip())) for row in visible_rows]
        unread_count = sum(1 for item in items if not item.get("is_read"))
        page = items[safe_offset : safe_offset + safe_limit]
        has_more = safe_offset + safe_limit < len(items)
        next_offset = safe_offset + safe_limit if has_more else None
        return {
            "feature_enabled": bool(APP_NOTICES_ENABLED),
            "items": page,
            "limit": safe_limit,
            "offset": safe_offset,
            "has_more": has_more,
            "next_offset": next_offset,
            "unread_count": unread_count,
        }

    async def mark_notices_read(self, user_id: str, notice_ids: Iterable[str]) -> int:
        uid = str(user_id or "").strip()
        ids = [str(value or "").strip() for value in notice_ids if str(value or "").strip()]
        if not uid:
            raise HTTPException(status_code=401, detail="Unauthorized")
        if not ids:
            raise HTTPException(status_code=400, detail="notice_ids is required")

        notice_rows = await self._fetch_notice_rows_by_ids(ids, select="id")
        valid_ids = [str(row.get("id") or "").strip() for row in notice_rows if str(row.get("id") or "").strip()]
        if not valid_ids:
            return 0

        existing = await self._fetch_state_rows_for_user(uid, valid_ids, select=NOTICE_STATE_MUTATION_SELECT)
        now_iso = _iso_utc()
        payload: List[Dict[str, Any]] = []
        updated_count = 0
        for notice_id in valid_ids:
            row = existing.get(notice_id) or {}
            read_at = str(row.get("read_at") or "").strip() or None
            popup_seen_at = str(row.get("popup_seen_at") or "").strip() or None
            if not read_at:
                updated_count += 1
            payload.append({
                "user_id": uid,
                "notice_id": notice_id,
                "read_at": read_at or now_iso,
                "popup_seen_at": popup_seen_at,
                "created_at": str(row.get("created_at") or now_iso),
                "updated_at": now_iso,
            })

        await self._upsert_state_rows(payload)
        return updated_count

    async def mark_notice_popup_seen(self, user_id: str, notice_id: str) -> bool:
        uid = str(user_id or "").strip()
        nid = str(notice_id or "").strip()
        if not uid:
            raise HTTPException(status_code=401, detail="Unauthorized")
        if not nid:
            raise HTTPException(status_code=400, detail="notice_id is required")

        notice_rows = await self._fetch_notice_rows_by_ids([nid], select="id")
        if not notice_rows:
            return False

        existing = await self._fetch_state_rows_for_user(uid, [nid], select=NOTICE_STATE_MUTATION_SELECT)
        row = existing.get(nid) or {}
        now_iso = _iso_utc()
        await self._upsert_state_rows([
            {
                "user_id": uid,
                "notice_id": nid,
                "read_at": str(row.get("read_at") or "").strip() or None,
                "popup_seen_at": str(row.get("popup_seen_at") or "").strip() or now_iso,
                "created_at": str(row.get("created_at") or now_iso),
                "updated_at": now_iso,
            }
        ])
        return True

