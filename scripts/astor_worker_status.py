#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Print ASTOR worker queue pressure and optional stale-job recovery.

Usage:
  python scripts/astor_worker_status.py
  python scripts/astor_worker_status.py --json
  python scripts/astor_worker_status.py --profile analysis
  python scripts/astor_worker_status.py --requeue-stale --stale-running-seconds 900
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
AI_INF = ROOT / "ai" / "services" / "ai_inference"
if str(AI_INF) not in sys.path:
    sys.path.insert(0, str(AI_INF))

from astor_job_queue import fetch_queue_stats, requeue_stale_running_jobs  # type: ignore

JOB_TYPE_PROFILES: Dict[str, List[str]] = {
    "all": [
        "myprofile_latest_refresh_v1",
        "snapshot_generate_v1",
        "analyze_emotion_structure_standard_v1",
        "analyze_emotion_structure_deep_v1",
        "analyze_self_structure_standard_v1",
        "analyze_self_structure_deep_v1",
        "generate_premium_reflections_v1",
        "inspect_reflection_v1",
        "generate_emotion_report_v2",
        "inspect_emotion_report_v1",
        "refresh_ranking_board_v1",
        "inspect_ranking_board_v1",
        "refresh_account_status_v1",
        "inspect_account_status_v1",
        "refresh_friend_feed_v1",
        "inspect_friend_feed_v1",
        "refresh_global_summary_v1",
        "inspect_global_summary_v1",
        "send_fcm_push_v1",
    ],
    "core": [
        "myprofile_latest_refresh_v1",
        "snapshot_generate_v1",
        "refresh_account_status_v1",
        "refresh_friend_feed_v1",
        "refresh_global_summary_v1",
        "refresh_ranking_board_v1",
    ],
    "analysis": [
        "analyze_emotion_structure_standard_v1",
        "analyze_emotion_structure_deep_v1",
        "analyze_self_structure_standard_v1",
        "analyze_self_structure_deep_v1",
        "generate_emotion_report_v2",
        "generate_premium_reflections_v1",
    ],
    "inspect": [
        "inspect_reflection_v1",
        "inspect_emotion_report_v1",
        "inspect_ranking_board_v1",
        "inspect_account_status_v1",
        "inspect_friend_feed_v1",
        "inspect_global_summary_v1",
    ],
    "ranking": ["refresh_ranking_board_v1", "inspect_ranking_board_v1"],
    "summary": [
        "refresh_account_status_v1",
        "inspect_account_status_v1",
        "refresh_friend_feed_v1",
        "inspect_friend_feed_v1",
        "refresh_global_summary_v1",
        "inspect_global_summary_v1",
    ],
    "notification": ["send_fcm_push_v1"],
}


def _parse_job_types(raw: Optional[str], profile: str) -> Optional[List[str]]:
    if raw:
        return [p.strip() for p in raw.split(",") if p.strip()]
    prof = (profile or "all").strip().lower()
    return list(JOB_TYPE_PROFILES.get(prof) or JOB_TYPE_PROFILES["all"])


def _print_text(stats: Dict[str, object], *, requeued: int = 0) -> None:
    by_status = stats.get("by_status") if isinstance(stats.get("by_status"), dict) else {}
    print("ASTOR worker queue status")
    print(f"  checked_at: {stats.get('checked_at')}")
    print(f"  table: {stats.get('table')}")
    print(f"  sampled_rows: {stats.get('sampled_rows')} / limit={stats.get('row_sample_limit')}")
    print(f"  ready_queued: {stats.get('ready_queued')}")
    print(f"  delayed_queued: {stats.get('delayed_queued')}")
    print(f"  running: {by_status.get('running', 0)}")
    print(f"  failed: {by_status.get('failed', 0)}")
    print(f"  oldest_ready_age_seconds: {stats.get('oldest_ready_age_seconds')}")
    print(f"  oldest_running_age_seconds: {stats.get('oldest_running_age_seconds')}")
    print(f"  stale_running_count: {stats.get('stale_running_count')} (threshold={stats.get('stale_running_seconds')}s)")
    if requeued:
        print(f"  stale_requeued_now: {requeued}")
    by_type = stats.get("by_type") if isinstance(stats.get("by_type"), dict) else {}
    if by_type:
        print("\nBy job_type:")
        for job_type in sorted(by_type.keys()):
            bucket = by_type.get(job_type) if isinstance(by_type.get(job_type), dict) else {}
            ready = bucket.get("queued", 0)
            running = bucket.get("running", 0)
            failed = bucket.get("failed", 0)
            if ready or running or failed:
                print(f"  {job_type}: queued={ready} running={running} failed={failed}")


async def _main_async(args: argparse.Namespace) -> int:
    job_types = _parse_job_types(args.job_types, args.profile)
    requeued = 0
    if args.requeue_stale:
        requeued = await requeue_stale_running_jobs(
            job_types=job_types,
            stale_running_seconds=args.stale_running_seconds,
            limit=args.requeue_limit,
            worker_id=args.worker_id or "astor-worker-status",
        )

    stats = await fetch_queue_stats(
        job_types=job_types,
        stale_running_seconds=args.stale_running_seconds,
        limit=args.limit,
    )
    payload = {"stats": stats, "requeued": requeued}
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        _print_text(stats, requeued=requeued)

    if args.fail_on_pressure:
        ready = int(stats.get("ready_queued") or 0)
        stale = int(stats.get("stale_running_count") or 0)
        if ready >= args.ready_threshold or stale >= args.stale_threshold:
            return 2
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Show ASTOR worker queue pressure.")
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    parser.add_argument("--profile", default=os.getenv("ASTOR_WORKER_PROFILE", "all"), choices=sorted(JOB_TYPE_PROFILES.keys()))
    parser.add_argument("--job-types", default=os.getenv("ASTOR_WORKER_JOB_TYPES"), help="Comma separated job_type filter.")
    parser.add_argument("--stale-running-seconds", type=int, default=int(os.getenv("ASTOR_WORKER_STALE_RUNNING_SECONDS", "900") or "900"))
    parser.add_argument("--limit", type=int, default=int(os.getenv("ASTOR_QUEUE_STATS_LIMIT", "5000") or "5000"))
    parser.add_argument("--requeue-stale", action="store_true", help="Move stale running jobs back to queued.")
    parser.add_argument("--requeue-limit", type=int, default=int(os.getenv("ASTOR_WORKER_STALE_REQUEUE_LIMIT", "25") or "25"))
    parser.add_argument("--worker-id", default=os.getenv("ASTOR_WORKER_ID", ""))
    parser.add_argument("--fail-on-pressure", action="store_true", help="Exit 2 when backlog/stale thresholds are exceeded.")
    parser.add_argument("--ready-threshold", type=int, default=int(os.getenv("ASTOR_WORKER_READY_THRESHOLD", "50") or "50"))
    parser.add_argument("--stale-threshold", type=int, default=int(os.getenv("ASTOR_WORKER_STALE_THRESHOLD", "1") or "1"))
    args = parser.parse_args()
    raise SystemExit(asyncio.run(_main_async(args)))


if __name__ == "__main__":
    main()
