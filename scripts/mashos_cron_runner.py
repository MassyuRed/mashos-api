#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mashos_cron_runner.py (Phase 4.5)

目的
- MashOS の Cron エンドポイントを「分割（offset/limit）」で安全に叩くためのランナー。
- Render Cron Jobs / GitHub Actions / どのCronサービスでも使える「薄い実行スクリプト」。

特徴
- offset/limit を使い、レスポンスの next_offset/done を見て最後まで回す
- shard_total / shard_index に対応（並列Cronで分割したいとき用）
- 失敗時は exit code != 0 にして監視しやすくする

使い方（例）
  # 1) 日次（全ユーザー）
  python scripts/mashos_cron_runner.py myweb-daily

  # 2) 週次（シャード4分割の2番目）
  CRON_SHARD_TOTAL=4 CRON_SHARD_INDEX=1 python scripts/mashos_cron_runner.py myweb-weekly

  # 3) 1日1回の「自動」モード（毎日0:00 JSTに実行するCronを1つだけ作る）
  python scripts/mashos_cron_runner.py auto

必要ENV
- MASHOS_BASE_URL: 例) https://mashos-api.onrender.com
- MASHOS_CRON_TOKEN: /cron/* 用のトークン（X-Cron-Tokenに入れる）
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import httpx


JST = timezone(timedelta(hours=9))

JOB_TO_ENDPOINT = {
    "myweb-daily": "/cron/myweb/daily",
    "myweb-weekly": "/cron/myweb/weekly",
    "myweb-monthly": "/cron/myweb/monthly",
    "myprofile-monthly": "/cron/myprofile/monthly",
}


@dataclass
class RunConfig:
    base_url: str
    token: str
    limit: int
    max_pages: int
    force: bool
    dry_run: bool
    include_astor: bool
    shard_total: int
    shard_index: int
    timeout_sec: float
    sleep_sec: float
    retries: int


def _env_bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    v = v.strip().lower()
    return v not in ("0", "false", "no", "off", "")


def _pick_jobs(job: str) -> List[str]:
    if job != "auto":
        return [job]

    # 1日1回のCronで「必要なものだけ実行」したい場合用
    now_jst = datetime.now(JST)
    jobs = ["myweb-daily"]

    # 週報: 日曜 0:00 JST 配布想定 → そのタイミングで weekly を走らせる
    if now_jst.weekday() == 6:  # Sunday (Mon=0 ... Sun=6)
        jobs.append("myweb-weekly")

    # 月報/自己構造(月次): 毎月1日 0:00 JST 配布
    if now_jst.day == 1:
        jobs.append("myweb-monthly")
        jobs.append("myprofile-monthly")

    return jobs


def _post_json(
    client: httpx.Client,
    url: str,
    token: str,
    payload: Dict[str, Any],
    retries: int,
) -> Dict[str, Any]:
    headers = {"Content-Type": "application/json", "X-Cron-Token": token}

    last_err: Optional[Exception] = None
    for i in range(retries + 1):
        try:
            r = client.post(url, headers=headers, json=payload)
            if r.status_code >= 300:
                # 返り値がjsonならdetail拾う
                try:
                    j = r.json()
                    detail = j.get("detail") if isinstance(j, dict) else None
                except Exception:
                    detail = None
                raise RuntimeError(f"HTTP {r.status_code} {detail or r.text[:300]}")
            j = r.json()
            if not isinstance(j, dict):
                raise RuntimeError("Invalid JSON response (not an object)")
            return j
        except Exception as e:
            last_err = e
            # 最終試行でなければバックオフ
            if i < retries:
                time.sleep(min(2 ** i, 10))
                continue
            break

    raise RuntimeError(f"Request failed after retries: {last_err}")


def _run_one_job(cfg: RunConfig, job: str) -> Tuple[int, int, int]:
    endpoint = JOB_TO_ENDPOINT[job]
    base = cfg.base_url.rstrip("/")
    url = f"{base}{endpoint}"

    print(f"\n=== RUN {job} => {url} ===")
    print(
        f"limit={cfg.limit} max_pages={cfg.max_pages} force={cfg.force} dry_run={cfg.dry_run} "
        f"include_astor={cfg.include_astor} shard={cfg.shard_index}/{cfg.shard_total}"
    )

    processed_total = 0
    generated_total = 0
    errors_total = 0

    offset = 0
    page = 0

    with httpx.Client(timeout=cfg.timeout_sec) as client:
        while True:
            page += 1
            payload = {
                "offset": offset,
                "limit": cfg.limit,
                "force": cfg.force,
                "dry_run": cfg.dry_run,
                "include_astor": cfg.include_astor,
                "shard_total": cfg.shard_total,
                "shard_index": cfg.shard_index,
            }

            j = _post_json(client, url, cfg.token, payload, retries=cfg.retries)

            processed = int(j.get("processed") or 0)
            generated = int(j.get("generated") or 0)
            errors = int(j.get("errors") or 0)
            done = bool(j.get("done"))
            next_offset = j.get("next_offset")

            processed_total += processed
            generated_total += generated
            errors_total += errors

            print(
                f"[page {page}] offset={offset} -> next_offset={next_offset} "
                f"processed={processed} generated={generated} errors={errors} done={done}"
            )

            if done:
                break

            if next_offset is None:
                # safety
                raise RuntimeError("done=false but next_offset is null")

            offset = int(next_offset)

            if page >= cfg.max_pages:
                raise RuntimeError(
                    f"Reached max_pages={cfg.max_pages} before done=true. "
                    f"Consider increasing CRON_MAX_PAGES or using sharding."
                )

            if cfg.sleep_sec > 0:
                time.sleep(cfg.sleep_sec)

    print(
        f"=== DONE {job}: processed_total={processed_total} generated_total={generated_total} errors_total={errors_total} ==="
    )
    return processed_total, generated_total, errors_total


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "job",
        choices=list(JOB_TO_ENDPOINT.keys()) + ["auto"],
        help="実行するCronジョブ（autoはJST日付から必要なジョブだけ実行）",
    )

    parser.add_argument("--base-url", default=os.getenv("MASHOS_BASE_URL") or os.getenv("API_BASE_URL") or "")
    parser.add_argument("--token", default=os.getenv("MASHOS_CRON_TOKEN") or os.getenv("MYMODEL_CRON_TOKEN") or os.getenv("COCOLON_CRON_TOKEN") or "")

    parser.add_argument("--limit", type=int, default=int(os.getenv("CRON_BATCH_SIZE") or "200"))
    parser.add_argument("--max-pages", type=int, default=int(os.getenv("CRON_MAX_PAGES") or "200"))
    parser.add_argument("--timeout-sec", type=float, default=float(os.getenv("CRON_HTTP_TIMEOUT_SEC") or "120"))
    parser.add_argument("--sleep-sec", type=float, default=float(os.getenv("CRON_SLEEP_SEC") or "0.2"))
    parser.add_argument("--retries", type=int, default=int(os.getenv("CRON_RETRIES") or "2"))

    parser.add_argument("--force", action="store_true", default=_env_bool("CRON_FORCE", False))
    parser.add_argument("--dry-run", action="store_true", default=_env_bool("CRON_DRY_RUN", False))
    parser.add_argument("--include-astor", action="store_true", default=_env_bool("CRON_INCLUDE_ASTOR", True))

    parser.add_argument("--shard-total", type=int, default=int(os.getenv("CRON_SHARD_TOTAL") or "1"))
    parser.add_argument("--shard-index", type=int, default=int(os.getenv("CRON_SHARD_INDEX") or "0"))

    args = parser.parse_args(argv)

    base_url = (args.base_url or "").strip().rstrip("/")
    token = (args.token or "").strip()

    if not base_url:
        print("ERROR: base_url is empty. Set MASHOS_BASE_URL.", file=sys.stderr)
        return 2
    if not token:
        print("ERROR: token is empty. Set MASHOS_CRON_TOKEN.", file=sys.stderr)
        return 2

    cfg = RunConfig(
        base_url=base_url,
        token=token,
        limit=max(1, min(args.limit, 2000)),
        max_pages=max(1, args.max_pages),
        force=bool(args.force),
        dry_run=bool(args.dry_run),
        include_astor=bool(args.include_astor),
        shard_total=max(1, min(args.shard_total, 64)),
        shard_index=max(0, min(args.shard_index, 63)),
        timeout_sec=max(5.0, float(args.timeout_sec)),
        sleep_sec=max(0.0, float(args.sleep_sec)),
        retries=max(0, int(args.retries)),
    )

    if cfg.shard_index >= cfg.shard_total:
        print("ERROR: shard_index must be within 0..shard_total-1", file=sys.stderr)
        return 2

    jobs = _pick_jobs(args.job)

    total_errors = 0
    for job in jobs:
        _, _, e = _run_one_job(cfg, job)
        total_errors += e

    # Cron監視で検知できるように：errorsが1件でもあれば非0で落とす
    if total_errors > 0:
        print(f"ERROR: total_errors={total_errors}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
