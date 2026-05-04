#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate Cocolon/Emlis tutorial fixtures from the actual generation services.

This script is intentionally outside the runtime UI path. It creates the fixed
fixtures displayed during the tutorial, while keeping the displayed data aligned
with the same generation services used by the product.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, MutableMapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
AI_SERVICES_DIR = REPO_ROOT / "ai" / "services" / "ai_inference"
if str(AI_SERVICES_DIR) not in sys.path:
    sys.path.insert(0, str(AI_SERVICES_DIR))

from emotion_piece_generation_service import generate_emotion_reflection_preview  # noqa: E402
from emlis_ai_reply_service import render_emlis_ai_reply  # noqa: E402
from api_analysis_reports import (  # noqa: E402
    _render_daily_standard_v3_text,
    _render_monthly_standard_v3_text,
    _render_weekly_standard_v3_text,
)

DISPLAY_NAME_PLACEHOLDER = "__DISPLAY_NAME__"
GENERATED_AT = "2026-05-02T09:30:00.000Z"

TUTORIAL_INPUT = {
    "memo": "なんか少しだけ気分が軽い。\nやること全部はできてないけど、ひとつ片づいたからまあいいかって感じ。\nこういう小さいことで落ち着く日もあるんだな。",
    "memo_action": "机の上を少し片づけた。\n好きな飲み物を用意して、少しゆっくりした。",
    "emotions": [
        {"type": "平穏", "strength": "medium"},
        {"type": "喜び", "strength": "weak"},
        {"type": "不安", "strength": "weak"},
    ],
    "category": ["生活", "健康", "価値観"],
    "send_emotion_notification": True,
}

FOLLOWED_USER_INPUT = {
    "memo": "なんか少しほっとした。\nやることは残ってるけど、ベッド周りを整えたら気持ちが落ち着いた。\n今日はこれで十分かも。",
    "memo_action": "温かい飲み物を用意して、少し休んだ。",
    "emotions": [
        {"type": "平穏", "strength": "medium"},
        {"type": "喜び", "strength": "weak"},
    ],
    "category": ["生活", "健康"],
    "send_emotion_notification": False,
}


def _json_dumps_for_content(value: Mapping[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _quota() -> Dict[str, Any]:
    return {
        "status": "ok",
        "tier": "free",
        "subscription_tier": "free",
        "month_key": "2026-05",
        "publish_limit": 5,
        "published_count": 0,
        "remaining_count": 5,
        "is_unlimited": False,
        "can_publish": True,
        "display_text": "今月のピース生成回数：Freeの５回",
    }


def _piece_policy_to_dict(policy: Any) -> Dict[str, Any]:
    return {
        "visibility_status": str(getattr(policy, "visibility_status", "visible") or "visible"),
        "reason_code": str(getattr(policy, "reason_code", "visible") or "visible"),
        "user_message": str(getattr(policy, "user_message", "") or ""),
        "allow_publish": bool(getattr(policy, "allow_publish", True)),
    }


def _build_piece_generation(input_payload: Mapping[str, Any]) -> Dict[str, Any]:
    return generate_emotion_reflection_preview(
        emotion_details=list(input_payload.get("emotions") or []),
        memo=str(input_payload.get("memo") or ""),
        memo_action=str(input_payload.get("memo_action") or ""),
        categories=list(input_payload.get("category") or []),
    )


def _build_piece_preview(input_payload: Mapping[str, Any], *, preview_id: str) -> Dict[str, Any]:
    generated = _build_piece_generation(input_payload)
    question = str(generated.get("question") or "").strip()
    piece_text = str(generated.get("answer_display_text") or generated.get("reflection_text") or "").strip()
    return {
        "preview_id": preview_id,
        "question": question,
        "title": question,
        "q_key": str(generated.get("q_key") or ""),
        "reflection_text": str(generated.get("reflection_text") or piece_text),
        "piece_text": piece_text,
        "answer_display_text": piece_text,
        "answer_display_state": str(generated.get("answer_display_state") or "ready"),
        "answer_norm_hash": str(generated.get("answer_norm_hash") or ""),
        "quota": _quota(),
        "meta": {
            "source": "emotion_piece_generation_service.generate_emotion_reflection_preview",
            "answer_display_source": str(generated.get("answer_display_source") or ""),
        },
        "piece_policy": _piece_policy_to_dict(generated.get("piece_policy")),
    }


def _build_piece_publish(preview: Mapping[str, Any], *, reflection_id: str, input_feedback: Mapping[str, Any] | None = None) -> Dict[str, Any]:
    data = {
        "reflection_id": reflection_id,
        "question": preview.get("question"),
        "title": preview.get("title") or preview.get("question"),
        "q_key": preview.get("q_key"),
        "reflection_text": preview.get("reflection_text"),
        "piece_text": preview.get("piece_text"),
        "answer_display_text": preview.get("answer_display_text"),
        "answer_display_state": preview.get("answer_display_state"),
        "answer_norm_hash": preview.get("answer_norm_hash"),
        "quota": _quota(),
        "meta": {
            "source": "home_gateway.emotion_reflection_publish_service.publish_preview",
            "preview_id": preview.get("preview_id"),
        },
    }
    if input_feedback is not None:
        data["input_feedback"] = dict(input_feedback)
    return data


def _build_feed_item(
    preview: Mapping[str, Any],
    *,
    item_id: str,
    owner_user_id: str,
    display_name: str,
    share_code: str,
    created_at: str,
    resonances: int,
    views: int,
    is_new: bool,
) -> Dict[str, Any]:
    question = str(preview.get("question") or preview.get("title") or "").strip()
    body = str(preview.get("piece_text") or preview.get("answer_display_text") or "").strip()
    return {
        "id": item_id,
        "q_instance_id": item_id,
        "q_key": preview.get("q_key"),
        "title": question,
        "question": {"title": question},
        "body": body,
        "piece_text": body,
        "answer_display_text": body,
        "answer_display_state": preview.get("answer_display_state") or "ready",
        "answer_norm_hash": preview.get("answer_norm_hash"),
        "owner_user_id": owner_user_id,
        "display_name": display_name,
        "share_code": share_code,
        "owner": {
            "user_id": owner_user_id,
            "display_name": display_name,
            "share_code": share_code,
        },
        "metrics": {"resonances": resonances, "views": views},
        "viewer_state": {"resonated": False},
        "created_at": created_at,
        "resonances": resonances,
        "views": views,
        "is_new": is_new,
    }


async def _build_emlis_reply() -> Dict[str, Any]:
    envelope = await render_emlis_ai_reply(
        user_id="tutorial-fixture-self",
        subscription_tier="free",
        current_input={
            "memo": TUTORIAL_INPUT["memo"],
            "memo_action": TUTORIAL_INPUT["memo_action"],
            "emotion_details": TUTORIAL_INPUT["emotions"],
            "category": TUTORIAL_INPUT["category"],
        },
        display_name=DISPLAY_NAME_PLACEHOLDER,
        timezone_name="Asia/Tokyo",
    )
    return {
        "source": "emlis_ai_reply_service.render_emlis_ai_reply",
        "comment_text": str(envelope.comment_text or ""),
        "emlis_ai": dict(envelope.meta or {}),
        "fallback_used": bool(envelope.fallback_used),
    }


def _report_record(
    *,
    report_type: str,
    title: str,
    period_start: str,
    period_end: str,
    content_text: str,
    content_json: Mapping[str, Any],
) -> Dict[str, Any]:
    return {
        "id": f"tutorial-analysis-{report_type}-20260502",
        "report_type": report_type,
        "title": title,
        "period_start": period_start,
        "period_end": period_end,
        "generated_at": GENERATED_AT,
        "updated_at": GENERATED_AT,
        "viewer_tier": "plus",
        "content_text": str(content_text or "").strip(),
        "content_json": _json_dumps_for_content(content_json),
    }


def _build_analysis_reports() -> Dict[str, Any]:
    daily_title = "日報：小さく整えた一日"
    daily_metrics = {
        "totalAll": 4,
        "dominantKey": "calm",
        "totals": {"joy": 1, "sadness": 0, "anxiety": 1, "anger": 0, "calm": 2},
        "sharePct": {"joy": 25, "sadness": 0, "anxiety": 25, "anger": 0, "calm": 50},
    }
    daily_summary = {"emotions_public": 4, "emotions_total": 4}
    daily_movement = {
        "peak_bucket": "夜",
        "bucket_dominants": [
            {"bucket": "朝", "label": "朝", "dominantKey": "calm"},
            {"bucket": "昼", "label": "昼", "dominantKey": "joy"},
            {"bucket": "夜", "label": "夜", "dominantKey": "calm"},
        ],
    }
    daily_text = _render_daily_standard_v3_text(
        title=daily_title,
        period_start_iso="2026-05-02",
        period_end_iso="2026-05-02",
        metrics=daily_metrics,
        summary=daily_summary,
        movement=daily_movement,
    )

    weekly_title = "週報：小さな切り替えが増えた週"
    weekly_days: List[Dict[str, Any]] = [
        {"label": "月", "joy": 2, "sadness": 0, "anxiety": 2, "anger": 0, "calm": 3, "dominantKey": "calm"},
        {"label": "火", "joy": 2, "sadness": 1, "anxiety": 2, "anger": 0, "calm": 4, "dominantKey": "calm"},
        {"label": "水", "joy": 3, "sadness": 0, "anxiety": 1, "anger": 0, "calm": 3, "dominantKey": "joy"},
        {"label": "木", "joy": 2, "sadness": 0, "anxiety": 2, "anger": 0, "calm": 4, "dominantKey": "calm"},
        {"label": "金", "joy": 3, "sadness": 0, "anxiety": 1, "anger": 0, "calm": 4, "dominantKey": "calm"},
        {"label": "土", "joy": 3, "sadness": 0, "anxiety": 1, "anger": 0, "calm": 5, "dominantKey": "calm"},
        {"label": "日", "joy": 2, "sadness": 0, "anxiety": 1, "anger": 0, "calm": 3, "dominantKey": "calm"},
    ]
    weekly_metrics = {
        "totalAll": 45,
        "totals": {"joy": 17, "sadness": 1, "anxiety": 10, "anger": 0, "calm": 27},
    }
    weekly_text = _render_weekly_standard_v3_text(
        title=weekly_title,
        period_start_iso="2026-04-27",
        period_end_iso="2026-05-03",
        metrics=weekly_metrics,
        days=weekly_days,
    )

    monthly_title = "月報：整える行動が感情を支えた月"
    monthly_weeks: List[Dict[str, Any]] = [
        {"label": "第1週", "joy": 10, "sadness": 2, "anxiety": 11, "anger": 0, "calm": 16},
        {"label": "第2週", "joy": 12, "sadness": 2, "anxiety": 9, "anger": 1, "calm": 20},
        {"label": "第3週", "joy": 14, "sadness": 1, "anxiety": 7, "anger": 0, "calm": 24},
        {"label": "第4週", "joy": 13, "sadness": 1, "anxiety": 8, "anger": 0, "calm": 22},
    ]
    monthly_metrics = {
        "totalAll": 154,
        "totals": {"joy": 49, "sadness": 6, "anxiety": 35, "anger": 1, "calm": 63},
        "topMotifs": [
            {"label": "不安→平穏", "count": 8},
            {"label": "平穏→喜び", "count": 6},
            {"label": "喜び→平穏", "count": 4},
        ],
    }
    monthly_text = _render_monthly_standard_v3_text(
        title=monthly_title,
        period_start_iso="2026-05-01",
        period_end_iso="2026-05-31",
        metrics=monthly_metrics,
        weeks=monthly_weeks,
    )

    return {
        "counts": {"today": 4, "week": 21, "month": 72},
        "reports": {
            "daily": _report_record(
                report_type="daily",
                title=daily_title,
                period_start="2026-05-02",
                period_end="2026-05-02",
                content_text=daily_text,
                content_json={
                    "standardReport": {"title": daily_title, "contentText": daily_text},
                    "metrics": daily_metrics,
                    "summary": daily_summary,
                    "movement": daily_movement,
                },
            ),
            "weekly": _report_record(
                report_type="weekly",
                title=weekly_title,
                period_start="2026-04-27",
                period_end="2026-05-03",
                content_text=weekly_text,
                content_json={
                    "standardReport": {"title": weekly_title, "contentText": weekly_text, "days": weekly_days},
                    "metrics": weekly_metrics,
                    "days": weekly_days,
                },
            ),
            "monthly": _report_record(
                report_type="monthly",
                title=monthly_title,
                period_start="2026-05-01",
                period_end="2026-05-31",
                content_text=monthly_text,
                content_json={
                    "standardReport": {"title": monthly_title, "contentText": monthly_text, "weeks": monthly_weeks},
                    "metrics": monthly_metrics,
                    "weeks": monthly_weeks,
                },
            ),
        },
    }


def _validate_fixture(fixture: MutableMapping[str, Any]) -> Dict[str, Any]:
    checks: List[Dict[str, Any]] = []

    def check(name: str, passed: bool, detail: str = "") -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    emlis = fixture.get("emlis_reply") or {}
    comment = str(emlis.get("comment_text") or "")
    meta = emlis.get("emlis_ai") if isinstance(emlis.get("emlis_ai"), dict) else {}
    check("emlis.comment_non_empty", bool(comment.strip()))
    check("emlis.meta_present", bool(meta))
    check("emlis.fallback_false", emlis.get("fallback_used") is False or meta.get("fallback_used") is False)
    check("emlis.name_placeholder", f"{DISPLAY_NAME_PLACEHOLDER}さん" in comment)
    check("emlis.identity", "Emlisです" in comment)

    piece = fixture.get("piece") if isinstance(fixture.get("piece"), dict) else {}
    preview = piece.get("preview") if isinstance(piece.get("preview"), dict) else {}
    publish = piece.get("publish") if isinstance(piece.get("publish"), dict) else {}
    feed_items = piece.get("feed_items") if isinstance(piece.get("feed_items"), list) else []
    check("piece.preview_question", bool(str(preview.get("question") or "").strip()))
    check("piece.preview_text", bool(str(preview.get("piece_text") or "").strip()))
    check("piece.publish_question", bool(str(publish.get("question") or "").strip()))
    check("piece.publish_text", bool(str(publish.get("piece_text") or "").strip()))
    check("piece.preview_publish_same", str(preview.get("piece_text") or "") == str(publish.get("piece_text") or ""))
    check("piece.free_quota", int((preview.get("quota") or {}).get("publish_limit") or 0) == 5)
    check("piece.feed_items", len(feed_items) >= 2)

    analysis = fixture.get("analysis") if isinstance(fixture.get("analysis"), dict) else {}
    reports = analysis.get("reports") if isinstance(analysis.get("reports"), dict) else {}
    for report_type in ("daily", "weekly", "monthly"):
        report = reports.get(report_type) if isinstance(reports.get(report_type), dict) else {}
        check(f"analysis.{report_type}", bool(str(report.get("content_text") or "").strip()))

    passed = all(item["passed"] for item in checks)
    return {"passed": passed, "checks": checks}


async def _build_fixture() -> Dict[str, Any]:
    emlis_reply = await _build_emlis_reply()
    self_preview = _build_piece_preview(TUTORIAL_INPUT, preview_id="tutorial-preview-self-20260502")
    self_publish = _build_piece_publish(
        self_preview,
        reflection_id="tutorial-piece-self-20260502",
        input_feedback=emlis_reply,
    )
    followed_preview = _build_piece_preview(FOLLOWED_USER_INPUT, preview_id="tutorial-preview-user-20260502")

    feed_items = [
        _build_feed_item(
            self_preview,
            item_id="tutorial-piece-self-20260502",
            owner_user_id="tutorial-self",
            display_name="自分",
            share_code="YOU",
            created_at=GENERATED_AT,
            resonances=0,
            views=0,
            is_new=True,
        ),
        _build_feed_item(
            followed_preview,
            item_id="tutorial-piece-user-20260502",
            owner_user_id="tutorial-follow-1",
            display_name="User",
            share_code="USER",
            created_at="2026-05-02T09:20:00.000Z",
            resonances=4,
            views=12,
            is_new=True,
        ),
    ]

    fixture: Dict[str, Any] = {
        "schema_version": "tutorial.fixture.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": {
            "api_routes": [
                "POST /emotion/piece/preview",
                "POST /emotion/piece/publish",
                "GET /nexus/pieces",
                "POST /analysis/reports/ensure",
                "GET /analysis/reports/ready",
            ],
            "services": [
                "emotion_piece_generation_service.generate_emotion_reflection_preview",
                "emlis_ai_reply_service.render_emlis_ai_reply",
                "api_analysis_reports._render_daily_standard_v3_text",
                "api_analysis_reports._render_weekly_standard_v3_text",
                "api_analysis_reports._render_monthly_standard_v3_text",
            ],
            "display_name_placeholder": DISPLAY_NAME_PLACEHOLDER,
        },
        "input": TUTORIAL_INPUT,
        "piece": {
            "preview": self_preview,
            "publish": self_publish,
            "feed_items": feed_items,
        },
        "emlis_reply": emlis_reply,
        "analysis": _build_analysis_reports(),
    }
    fixture["validation"] = _validate_fixture(fixture)
    return fixture


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate tutorial fixture JSON from actual Cocolon/Emlis services.")
    parser.add_argument("--output", type=Path, required=True, help="Output JSON path")
    args = parser.parse_args(argv)

    fixture = asyncio.run(_build_fixture())
    if not fixture.get("validation", {}).get("passed"):
        print(json.dumps(fixture.get("validation"), ensure_ascii=False, indent=2), file=sys.stderr)
        return 2

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(fixture, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
