from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

from supabase_client import sb_delete, sb_delete_auth_user, sb_get

logger = logging.getLogger("account_delete_service")

_DELETE_TIMEOUT = 10.0
_SELECT_TIMEOUT = 8.0
_IN_FILTER_CHUNK_SIZE = 100
_RANKING_METRIC_KEYS: Sequence[str] = (
    "emotions",
    "input_count",
    "input_length",
    "login_streak",
    "mymodel_questions",
    "mymodel_resonances",
    "mymodel_discoveries",
)


@dataclass
class AccountDeleteExecutionResult:
    user_id: str
    deleted_tables: List[str] = field(default_factory=list)
    related_user_ids: Set[str] = field(default_factory=set)
    auth_user_deleted: bool = False


def _normalize_user_id(user_id: str) -> str:
    return str(user_id or "").strip()


def _quote_in(values: Iterable[str]) -> str:
    quoted: List[str] = []
    for raw in values or []:
        value = str(raw or "").strip()
        if not value:
            continue
        quoted.append('"' + value.replace('"', "") + '"')
    return f"in.({','.join(quoted)})"


def _chunked(values: Sequence[str], chunk_size: int = _IN_FILTER_CHUNK_SIZE) -> List[List[str]]:
    chunk = max(1, int(chunk_size or _IN_FILTER_CHUNK_SIZE))
    items = [str(value or "").strip() for value in values if str(value or "").strip()]
    return [items[index:index + chunk] for index in range(0, len(items), chunk)]


async def _select_rows(path: str, *, params: Dict[str, str], timeout: float = _SELECT_TIMEOUT) -> List[Dict[str, object]]:
    resp = await sb_get(path, params=params, timeout=timeout)
    if resp.status_code >= 300:
        raise RuntimeError(f"select failed path={path} status={resp.status_code} body={(resp.text or '')[:1000]}")
    try:
        data = resp.json()
    except Exception:
        return []
    if isinstance(data, list):
        return [row for row in data if isinstance(row, dict)]
    if isinstance(data, dict):
        return [data]
    return []


async def _delete_required(path: str, *, params: Dict[str, str], timeout: float = _DELETE_TIMEOUT) -> None:
    resp = await sb_delete(path, params=params, prefer="return=minimal", timeout=timeout)
    if resp.status_code >= 300:
        raise RuntimeError(f"delete failed path={path} status={resp.status_code} body={(resp.text or '')[:1000]}")


async def _delete_group(
    label: str,
    result: AccountDeleteExecutionResult,
    calls: Sequence[Tuple[str, Dict[str, str]]],
) -> None:
    for path, params in calls:
        await _delete_required(path, params=params)
    result.deleted_tables.append(label)


async def _delete_many_by_in_filter(
    path: str,
    *,
    field: str,
    values: Sequence[str],
    chunk_size: int = _IN_FILTER_CHUNK_SIZE,
) -> List[Tuple[str, Dict[str, str]]]:
    calls: List[Tuple[str, Dict[str, str]]] = []
    for chunk in _chunked(list(values), chunk_size=chunk_size):
        if not chunk:
            continue
        calls.append((path, {field: _quote_in(chunk)}))
    return calls


async def _collect_related_ids_from_pair_table(
    *,
    table: str,
    left_field: str,
    right_field: str,
    user_id: str,
) -> Set[str]:
    uid = _normalize_user_id(user_id)
    if not uid:
        return set()
    rows = await _select_rows(
        f"/rest/v1/{table}",
        params={
            "select": f"{left_field},{right_field}",
            "or": f"({left_field}.eq.{uid},{right_field}.eq.{uid})",
            "limit": "2000",
        },
    )
    related: Set[str] = set()
    for row in rows:
        left_value = str(row.get(left_field) or "").strip()
        right_value = str(row.get(right_field) or "").strip()
        for candidate in (left_value, right_value):
            if candidate and candidate != uid:
                related.add(candidate)
    return related


async def _collect_related_user_ids(user_id: str) -> Set[str]:
    uid = _normalize_user_id(user_id)
    if not uid:
        return set()

    collectors = [
        ("friendships", "user_id", "friend_user_id"),
        ("friend_requests", "requester_user_id", "requested_user_id"),
        ("follow_requests", "requester_user_id", "target_user_id"),
        ("myprofile_links", "owner_user_id", "viewer_user_id"),
        ("friend_notification_settings", "viewer_user_id", "owner_user_id"),
        ("friend_emotion_feed", "viewer_user_id", "owner_user_id"),
    ]
    related: Set[str] = set()
    for table, left_field, right_field in collectors:
        try:
            related.update(
                await _collect_related_ids_from_pair_table(
                    table=table,
                    left_field=left_field,
                    right_field=right_field,
                    user_id=uid,
                )
            )
        except Exception as exc:
            logger.warning(
                "account_delete related user collection skipped table=%s user_id=%s err=%r",
                table,
                uid,
                exc,
            )
    return related


async def _collect_today_question_answer_ids(user_id: str) -> List[str]:
    uid = _normalize_user_id(user_id)
    if not uid:
        return []
    rows = await _select_rows(
        "/rest/v1/today_question_answers",
        params={
            "select": "id",
            "user_id": f"eq.{uid}",
            "limit": "2000",
        },
    )
    ids = []
    for row in rows:
        value = str(row.get("id") or "").strip()
        if value:
            ids.append(value)
    return ids


async def _collect_generated_reflection_instance_ids(user_id: str) -> List[str]:
    uid = _normalize_user_id(user_id)
    if not uid:
        return []
    rows = await _select_rows(
        "/rest/v1/mymodel_reflections",
        params={
            "select": "public_id",
            "owner_user_id": f"eq.{uid}",
            "limit": "1000",
        },
    )
    seen: Set[str] = set()
    values: List[str] = []
    for row in rows:
        public_id = str(row.get("public_id") or "").strip()
        if not public_id:
            continue
        for candidate in (public_id, f"reflection:{public_id}"):
            if candidate and candidate not in seen:
                seen.add(candidate)
                values.append(candidate)
    return values


async def _collect_owned_q_instance_ids(user_id: str) -> List[str]:
    uid = _normalize_user_id(user_id)
    if not uid:
        return []
    rows = await _select_rows(
        "/rest/v1/mymodel_create_answers",
        params={
            "select": "question_id",
            "user_id": f"eq.{uid}",
            "limit": "1000",
        },
    )
    seen: Set[str] = set()
    values: List[str] = []
    for row in rows:
        question_id = str(row.get("question_id") or "").strip()
        if not question_id:
            continue
        q_instance_id = f"{uid}:{question_id}"
        if q_instance_id not in seen:
            seen.add(q_instance_id)
            values.append(q_instance_id)
    return values


async def _collect_report_ids(user_id: str) -> List[str]:
    uid = _normalize_user_id(user_id)
    if not uid:
        return []

    report_ids: List[str] = []
    seen: Set[str] = set()
    for table in ("myweb_reports", "myprofile_reports"):
        rows = await _select_rows(
            f"/rest/v1/{table}",
            params={
                "select": "id",
                "user_id": f"eq.{uid}",
                "limit": "2000",
            },
        )
        for row in rows:
            report_id = str(row.get("id") or "").strip()
            if report_id and report_id not in seen:
                seen.add(report_id)
                report_ids.append(report_id)
    return report_ids


async def _invalidate_deleted_user_cache(user_id: str) -> None:
    uid = _normalize_user_id(user_id)
    if not uid:
        return

    tasks = []
    try:
        from response_microcache import invalidate_prefix

        prefixes = (
            f"input_summary:{uid}",
            f"myweb_home_summary:{uid}",
            f"myweb:ready:{uid}",
            f"myweb:detail:{uid}",
            f"report_reads:myweb_unread:{uid}",
            f"friends:manage:{uid}",
            f"friends:unread:{uid}",
            f"emotion_log:unread:{uid}",
            f"notices:current:{uid}",
            f"today_question:current:{uid}",
            f"today_question:status:{uid}",
        )
        tasks.extend(invalidate_prefix(prefix) for prefix in prefixes)
    except Exception as exc:
        logger.warning("account_delete cache invalidation helper unavailable user_id=%s err=%r", uid, exc)

    try:
        from startup_snapshot_store import invalidate_startup_snapshot

        tasks.append(invalidate_startup_snapshot(uid))
    except Exception as exc:
        logger.warning("account_delete startup snapshot invalidation unavailable user_id=%s err=%r", uid, exc)

    try:
        from today_question_store import invalidate_today_question_user_runtime_cache

        tasks.append(invalidate_today_question_user_runtime_cache(uid))
    except Exception as exc:
        logger.warning("account_delete today question cache invalidation unavailable user_id=%s err=%r", uid, exc)

    if not tasks:
        return

    results = await asyncio.gather(*tasks, return_exceptions=True)
    for item in results:
        if isinstance(item, Exception):
            logger.warning("account_delete cache invalidation failed user_id=%s err=%r", uid, item)


async def _refresh_related_users(related_user_ids: Set[str], deleted_user_id: str) -> None:
    targets = {str(user_id or "").strip() for user_id in related_user_ids or set() if str(user_id or "").strip()}
    if not targets:
        return

    tasks = []
    try:
        from response_microcache import invalidate_prefix

        for related_user_id in sorted(targets):
            tasks.append(invalidate_prefix(f"friends:manage:{related_user_id}"))
            tasks.append(invalidate_prefix(f"friends:unread:{related_user_id}"))
            tasks.append(invalidate_prefix(f"emotion_log:unread:{related_user_id}"))
            tasks.append(invalidate_prefix(f"startup_snapshot:{related_user_id}"))
    except Exception as exc:
        logger.warning("account_delete related cache invalidation helper unavailable deleted_user_id=%s err=%r", deleted_user_id, exc)

    try:
        from astor_emotion_log_feed_enqueue import enqueue_emotion_log_feed_refresh

        for related_user_id in sorted(targets):
            tasks.append(
                enqueue_emotion_log_feed_refresh(
                    viewer_user_id=related_user_id,
                    trigger="account_delete",
                    owner_user_id=deleted_user_id,
                    debounce=True,
                )
            )
    except Exception as exc:
        logger.warning("account_delete friend feed enqueue unavailable deleted_user_id=%s err=%r", deleted_user_id, exc)

    if not tasks:
        return

    results = await asyncio.gather(*tasks, return_exceptions=True)
    for item in results:
        if isinstance(item, Exception):
            logger.warning("account_delete related refresh failed deleted_user_id=%s err=%r", deleted_user_id, item)


async def _refresh_global_surfaces(user_id: str) -> None:
    uid = _normalize_user_id(user_id)
    if not uid:
        return

    tasks = []
    try:
        from astor_ranking_enqueue import enqueue_ranking_board_refresh_many

        tasks.append(
            enqueue_ranking_board_refresh_many(
                metric_keys=_RANKING_METRIC_KEYS,
                user_id=uid,
                trigger="account_delete",
                debounce=True,
            )
        )
    except Exception as exc:
        logger.warning("account_delete ranking refresh enqueue unavailable user_id=%s err=%r", uid, exc)

    try:
        from astor_global_summary_enqueue import enqueue_global_summary_refresh

        tasks.append(
            enqueue_global_summary_refresh(
                trigger="account_delete",
                actor_user_id=uid,
                debounce=True,
            )
        )
    except Exception as exc:
        logger.warning("account_delete global summary enqueue unavailable user_id=%s err=%r", uid, exc)

    if not tasks:
        return

    results = await asyncio.gather(*tasks, return_exceptions=True)
    for item in results:
        if isinstance(item, Exception):
            logger.warning("account_delete global refresh failed user_id=%s err=%r", uid, item)


async def _delete_auth_user(user_id: str) -> None:
    uid = _normalize_user_id(user_id)
    if not uid:
        raise RuntimeError("user_id is required")
    resp = await sb_delete_auth_user(uid, timeout=8.0)
    if resp.status_code in (200, 204, 404):
        return
    raise RuntimeError(
        f"auth delete failed user_id={uid} status={resp.status_code} body={(resp.text or '')[:1000]}"
    )


async def execute_account_delete(user_id: str) -> AccountDeleteExecutionResult:
    uid = _normalize_user_id(user_id)
    if not uid:
        raise RuntimeError("user_id is required")

    logger.info("account_delete_started user_id=%s", uid)
    result = AccountDeleteExecutionResult(user_id=uid)

    related_user_ids = await _collect_related_user_ids(uid)
    today_question_answer_ids = await _collect_today_question_answer_ids(uid)
    generated_reflection_instance_ids = await _collect_generated_reflection_instance_ids(uid)
    owned_create_instance_ids = await _collect_owned_q_instance_ids(uid)
    owned_report_ids = await _collect_report_ids(uid)
    owned_q_instance_ids = list(dict.fromkeys([*owned_create_instance_ids, *generated_reflection_instance_ids]))
    result.related_user_ids = related_user_ids

    try:
        await _delete_group(
            "astor_jobs",
            result,
            [("/rest/v1/astor_jobs", {"user_id": f"eq.{uid}"})],
        )

        await _delete_group(
            "friend_requests",
            result,
            [("/rest/v1/friend_requests", {"or": f"(requester_user_id.eq.{uid},requested_user_id.eq.{uid})"})],
        )
        await _delete_group(
            "friendships",
            result,
            [("/rest/v1/friendships", {"or": f"(user_id.eq.{uid},friend_user_id.eq.{uid})"})],
        )
        await _delete_group(
            "follow_requests",
            result,
            [("/rest/v1/follow_requests", {"or": f"(requester_user_id.eq.{uid},target_user_id.eq.{uid})"})],
        )
        await _delete_group(
            "myprofile_requests",
            result,
            [("/rest/v1/myprofile_requests", {"or": f"(requester_user_id.eq.{uid},requested_user_id.eq.{uid})"})],
        )
        await _delete_group(
            "myprofile_links",
            result,
            [("/rest/v1/myprofile_links", {"or": f"(owner_user_id.eq.{uid},viewer_user_id.eq.{uid})"})],
        )
        await _delete_group(
            "friend_notification_settings",
            result,
            [("/rest/v1/friend_notification_settings", {"or": f"(viewer_user_id.eq.{uid},owner_user_id.eq.{uid})"})],
        )
        await _delete_group(
            "friend_emotion_feed",
            result,
            [("/rest/v1/friend_emotion_feed", {"or": f"(viewer_user_id.eq.{uid},owner_user_id.eq.{uid})"})],
        )

        await _delete_group("emotions", result, [("/rest/v1/emotions", {"user_id": f"eq.{uid}"})])
        await _delete_group("deep_insight_answers", result, [("/rest/v1/deep_insight_answers", {"user_id": f"eq.{uid}"})])
        await _delete_group(
            "today_question_push_deliveries",
            result,
            [("/rest/v1/today_question_push_deliveries", {"user_id": f"eq.{uid}"})],
        )
        await _delete_group(
            "today_question_user_settings",
            result,
            [("/rest/v1/today_question_user_settings", {"user_id": f"eq.{uid}"})],
        )
        await _delete_group(
            "today_question_user_progress",
            result,
            [("/rest/v1/today_question_user_progress", {"user_id": f"eq.{uid}"})],
        )
        await _delete_group(
            "today_question_answer_revisions",
            result,
            await _delete_many_by_in_filter(
                "/rest/v1/today_question_answer_revisions",
                field="answer_id",
                values=today_question_answer_ids,
            ),
        )
        await _delete_group(
            "today_question_answers",
            result,
            [("/rest/v1/today_question_answers", {"user_id": f"eq.{uid}"})],
        )
        await _delete_group(
            "mymodel_create_answers",
            result,
            [("/rest/v1/mymodel_create_answers", {"user_id": f"eq.{uid}"})],
        )

        qna_reads_calls: List[Tuple[str, Dict[str, str]]] = [
            ("/rest/v1/mymodel_qna_reads", {"viewer_user_id": f"eq.{uid}"}),
            ("/rest/v1/mymodel_qna_reads", {"q_instance_id": f"like.{uid}:*"}),
        ]
        qna_reads_calls.extend(
            await _delete_many_by_in_filter(
                "/rest/v1/mymodel_qna_reads",
                field="q_instance_id",
                values=owned_q_instance_ids,
            )
        )
        await _delete_group("mymodel_qna_reads", result, qna_reads_calls)

        qna_resonances_calls: List[Tuple[str, Dict[str, str]]] = [
            ("/rest/v1/mymodel_qna_resonances", {"viewer_user_id": f"eq.{uid}"}),
            ("/rest/v1/mymodel_qna_resonances", {"q_instance_id": f"like.{uid}:*"}),
        ]
        qna_resonances_calls.extend(
            await _delete_many_by_in_filter(
                "/rest/v1/mymodel_qna_resonances",
                field="q_instance_id",
                values=owned_q_instance_ids,
            )
        )
        await _delete_group("mymodel_qna_resonances", result, qna_resonances_calls)

        qna_echoes_calls: List[Tuple[str, Dict[str, str]]] = [
            ("/rest/v1/mymodel_qna_echoes", {"viewer_user_id": f"eq.{uid}"}),
            ("/rest/v1/mymodel_qna_echoes", {"target_user_id": f"eq.{uid}"}),
            ("/rest/v1/mymodel_qna_echoes", {"q_instance_id": f"like.{uid}:*"}),
        ]
        qna_echoes_calls.extend(
            await _delete_many_by_in_filter(
                "/rest/v1/mymodel_qna_echoes",
                field="q_instance_id",
                values=owned_q_instance_ids,
            )
        )
        await _delete_group("mymodel_qna_echoes", result, qna_echoes_calls)

        qna_discovery_calls: List[Tuple[str, Dict[str, str]]] = [
            ("/rest/v1/mymodel_qna_discovery_logs", {"viewer_user_id": f"eq.{uid}"}),
            ("/rest/v1/mymodel_qna_discovery_logs", {"target_user_id": f"eq.{uid}"}),
            ("/rest/v1/mymodel_qna_discovery_logs", {"q_instance_id": f"like.{uid}:*"}),
        ]
        qna_discovery_calls.extend(
            await _delete_many_by_in_filter(
                "/rest/v1/mymodel_qna_discovery_logs",
                field="q_instance_id",
                values=owned_q_instance_ids,
            )
        )
        await _delete_group("mymodel_qna_discovery_logs", result, qna_discovery_calls)

        qna_view_calls: List[Tuple[str, Dict[str, str]]] = [
            ("/rest/v1/mymodel_qna_view_logs", {"viewer_user_id": f"eq.{uid}"}),
            ("/rest/v1/mymodel_qna_view_logs", {"target_user_id": f"eq.{uid}"}),
            ("/rest/v1/mymodel_qna_view_logs", {"q_instance_id": f"like.{uid}:*"}),
        ]
        qna_view_calls.extend(
            await _delete_many_by_in_filter(
                "/rest/v1/mymodel_qna_view_logs",
                field="q_instance_id",
                values=owned_q_instance_ids,
            )
        )
        await _delete_group("mymodel_qna_view_logs", result, qna_view_calls)

        qna_resonance_log_calls: List[Tuple[str, Dict[str, str]]] = [
            ("/rest/v1/mymodel_qna_resonance_logs", {"viewer_user_id": f"eq.{uid}"}),
            ("/rest/v1/mymodel_qna_resonance_logs", {"target_user_id": f"eq.{uid}"}),
            ("/rest/v1/mymodel_qna_resonance_logs", {"q_instance_id": f"like.{uid}:*"}),
        ]
        qna_resonance_log_calls.extend(
            await _delete_many_by_in_filter(
                "/rest/v1/mymodel_qna_resonance_logs",
                field="q_instance_id",
                values=owned_q_instance_ids,
            )
        )
        await _delete_group("mymodel_qna_resonance_logs", result, qna_resonance_log_calls)

        qna_metrics_calls: List[Tuple[str, Dict[str, str]]] = [
            ("/rest/v1/mymodel_qna_metrics", {"q_instance_id": f"like.{uid}:*"}),
        ]
        qna_metrics_calls.extend(
            await _delete_many_by_in_filter(
                "/rest/v1/mymodel_qna_metrics",
                field="q_instance_id",
                values=owned_q_instance_ids,
            )
        )
        await _delete_group("mymodel_qna_metrics", result, qna_metrics_calls)

        await _delete_group(
            "mymodel_reflections",
            result,
            [("/rest/v1/mymodel_reflections", {"owner_user_id": f"eq.{uid}"})],
        )

        report_read_calls: List[Tuple[str, Dict[str, str]]] = [
            ("/rest/v1/report_reads", {"user_id": f"eq.{uid}"}),
        ]
        report_read_calls.extend(
            await _delete_many_by_in_filter(
                "/rest/v1/report_reads",
                field="report_id",
                values=owned_report_ids,
            )
        )
        await _delete_group("report_reads", result, report_read_calls)

        await _delete_group(
            "analysis_results",
            result,
            [("/rest/v1/analysis_results", {"target_user_id": f"eq.{uid}"})],
        )
        await _delete_group(
            "material_snapshots",
            result,
            [("/rest/v1/material_snapshots", {"user_id": f"eq.{uid}"})],
        )
        await _delete_group("myweb_reports", result, [("/rest/v1/myweb_reports", {"user_id": f"eq.{uid}"})])
        await _delete_group("myprofile_reports", result, [("/rest/v1/myprofile_reports", {"user_id": f"eq.{uid}"})])
        await _delete_group("user_login_days", result, [("/rest/v1/user_login_days", {"user_id": f"eq.{uid}"})])
        await _delete_group("active_users", result, [("/rest/v1/active_users", {"user_id": f"eq.{uid}"})])
        await _delete_group(
            "app_notice_user_states",
            result,
            [("/rest/v1/app_notice_user_states", {"user_id": f"eq.{uid}"})],
        )
        await _delete_group(
            "report_distribution_user_settings",
            result,
            [("/rest/v1/report_distribution_user_settings", {"user_id": f"eq.{uid}"})],
        )
        await _delete_group(
            "report_distribution_push_candidates",
            result,
            [("/rest/v1/report_distribution_push_candidates", {"user_id": f"eq.{uid}"})],
        )
        await _delete_group(
            "report_distribution_push_deliveries",
            result,
            [("/rest/v1/report_distribution_push_deliveries", {"user_id": f"eq.{uid}"})],
        )
        await _delete_group(
            "account_status_summaries",
            result,
            [("/rest/v1/account_status_summaries", {"target_user_id": f"eq.{uid}"})],
        )
        await _delete_group(
            "friend_feed_summaries",
            result,
            [("/rest/v1/friend_feed_summaries", {"viewer_user_id": f"eq.{uid}"})],
        )
        await _delete_group(
            "account_visibility_settings",
            result,
            [("/rest/v1/account_visibility_settings", {"user_id": f"eq.{uid}"})],
        )
        await _delete_group("profiles", result, [("/rest/v1/profiles", {"id": f"eq.{uid}"})])

        await _invalidate_deleted_user_cache(uid)
        await _refresh_related_users(related_user_ids, uid)
        await _refresh_global_surfaces(uid)
        await _delete_auth_user(uid)
        result.auth_user_deleted = True
    except Exception as exc:
        logger.exception("account_delete_step_failed user_id=%s err=%r", uid, exc)
        raise

    logger.info(
        "account_delete_completed user_id=%s deleted_tables=%s related_user_ids=%s auth_user_deleted=%s",
        uid,
        ",".join(result.deleted_tables),
        len(result.related_user_ids),
        result.auth_user_deleted,
    )
    return result
