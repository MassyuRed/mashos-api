#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lightweight Cocolon API load-test runner.

This script intentionally stays small and dependency-light.  It is meant for
staging / pre-release checks of endpoint latency, status-code distribution, and
basic queue pressure around the Cocolon hot paths.

Examples:
  python scripts/cocolon_load_test.py --base-url https://api.example.com --scenario app-bootstrap --token "$TOKEN" --requests 100 --concurrency 20
  python scripts/cocolon_load_test.py --base-url https://api.example.com --scenario emotion-submit --token "$TOKEN" --requests 50 --concurrency 10 --no-notify-friends
  python scripts/cocolon_load_test.py --base-url https://api.example.com --scenario emotion-submit --token-file tokens.txt --requests 300 --concurrency 30 --notify-friends
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import statistics
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:
    import httpx
except Exception as exc:  # pragma: no cover - runtime environment guard
    print("httpx is required. Install project dependencies before running this script.", file=sys.stderr)
    print(str(exc), file=sys.stderr)
    raise SystemExit(2)


READ_SCENARIOS = {"app-bootstrap", "startup", "home-state", "custom-get"}
WRITE_SCENARIOS = {"emotion-submit", "piece-preview", "custom-post"}
SCENARIOS = sorted(READ_SCENARIOS | WRITE_SCENARIOS | {"mix"})


@dataclass
class RequestResult:
    ok: bool
    status_code: int
    elapsed_ms: float
    method: str
    path: str
    error: str = ""
    response_bytes: int = 0


def _load_tokens(args: argparse.Namespace) -> List[str]:
    tokens: List[str] = []
    if args.token:
        tokens.extend([t.strip() for t in args.token if str(t or "").strip()])

    env_token = os.getenv("COCOLON_LOAD_BEARER_TOKEN", "").strip()
    if env_token:
        tokens.append(env_token)

    if args.token_file:
        path = Path(args.token_file)
        if not path.exists():
            raise SystemExit(f"token file not found: {path}")
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            tokens.append(line)

    # Keep order but dedupe.
    out: List[str] = []
    seen = set()
    for token in tokens:
        if token not in seen:
            seen.add(token)
            out.append(token)
    return out


def _normalize_base_url(value: str) -> str:
    base = str(value or "").strip().rstrip("/")
    if not base:
        raise SystemExit("--base-url or COCOLON_LOAD_BASE_URL is required")
    if not (base.startswith("http://") or base.startswith("https://")):
        raise SystemExit("--base-url must start with http:// or https://")
    return base


def _read_json_arg(raw: Optional[str], *, name: str) -> Dict[str, Any]:
    if not raw:
        return {}
    text = raw.strip()
    if not text:
        return {}
    if text.startswith("@"):
        path = Path(text[1:])
        if not path.exists():
            raise SystemExit(f"{name} json file not found: {path}")
        text = path.read_text(encoding="utf-8")
    try:
        value = json.loads(text)
    except Exception as exc:
        raise SystemExit(f"invalid {name} JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"{name} JSON must be an object")
    return value


def _auth_headers(tokens: List[str], index: int) -> Dict[str, str]:
    if not tokens:
        return {}
    token = tokens[index % len(tokens)]
    return {"Authorization": f"Bearer {token}"}


def _emotion_payload(args: argparse.Namespace, index: int) -> Dict[str, Any]:
    created_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    payload: Dict[str, Any] = {
        "emotions": [{"type": args.emotion_type, "strength": args.emotion_strength}],
        "memo": f"load-test {args.run_id} #{index}",
        "memoAction": "負荷試験用の短い入力を送信した",
        "category": [args.category],
        "created_at": created_at,
        "is_secret": True,
        "send_friend_notification": bool(args.notify_friends),
    }
    if args.legacy_user_id:
        payload["user_id"] = args.legacy_user_id
    return payload


def _piece_preview_payload(args: argparse.Namespace, index: int) -> Dict[str, Any]:
    payload = _emotion_payload(args, index)
    # Piece preview accepts the same emotion input shape but does not use is_secret.
    payload.pop("is_secret", None)
    return payload


def _scenario_request(args: argparse.Namespace, scenario: str, index: int) -> Tuple[str, str, Optional[Dict[str, Any]]]:
    if scenario == "app-bootstrap":
        return "GET", "/app/bootstrap", None
    if scenario == "startup":
        return "GET", "/app/startup", None
    if scenario == "home-state":
        return "GET", "/home/state", None
    if scenario == "emotion-submit":
        return "POST", "/emotion/submit", _emotion_payload(args, index)
    if scenario == "piece-preview":
        return "POST", "/emotion/piece/preview", _piece_preview_payload(args, index)
    if scenario == "custom-get":
        if not args.endpoint:
            raise SystemExit("--endpoint is required for custom-get")
        return "GET", args.endpoint, None
    if scenario == "custom-post":
        if not args.endpoint:
            raise SystemExit("--endpoint is required for custom-post")
        payload = _read_json_arg(args.payload_json, name="payload")
        return "POST", args.endpoint, payload
    raise SystemExit(f"unknown scenario: {scenario}")


def _pick_scenario(args: argparse.Namespace, index: int) -> str:
    if args.scenario != "mix":
        return args.scenario
    # Mix focuses on read-heavy startup behavior with a smaller write sample.
    cycle = ["app-bootstrap", "startup", "home-state", "emotion-submit"]
    return cycle[index % len(cycle)]


async def _one_request(
    client: "httpx.AsyncClient",
    *,
    args: argparse.Namespace,
    base_url: str,
    tokens: List[str],
    index: int,
) -> RequestResult:
    scenario = _pick_scenario(args, index)
    method, path, payload = _scenario_request(args, scenario, index)
    if not path.startswith("/"):
        path = "/" + path
    url = base_url + path
    headers = _auth_headers(tokens, index)
    headers.setdefault("X-Cocolon-Load-Test", args.run_id)

    start = time.perf_counter()
    try:
        if method == "GET":
            resp = await client.get(url, headers=headers)
        else:
            resp = await client.post(url, headers=headers, json=payload or {})
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        ok = 200 <= int(resp.status_code) < 300
        return RequestResult(
            ok=ok,
            status_code=int(resp.status_code),
            elapsed_ms=elapsed_ms,
            method=method,
            path=path,
            response_bytes=len(resp.content or b""),
            error="" if ok else (resp.text or "")[:240].replace("\n", " "),
        )
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        return RequestResult(
            ok=False,
            status_code=0,
            elapsed_ms=elapsed_ms,
            method=method,
            path=path,
            error=str(exc)[:240],
        )


async def _run_fixed_count(args: argparse.Namespace, base_url: str, tokens: List[str]) -> List[RequestResult]:
    queue: "asyncio.Queue[Optional[int]]" = asyncio.Queue()
    for index in range(int(args.requests)):
        queue.put_nowait(index)
    for _ in range(int(args.concurrency)):
        queue.put_nowait(None)

    results: List[RequestResult] = []
    result_lock = asyncio.Lock()

    async with httpx.AsyncClient(timeout=float(args.timeout), follow_redirects=False) as client:
        async def worker(worker_index: int) -> None:
            if args.ramp_up_seconds > 0 and args.concurrency > 1:
                await asyncio.sleep(float(args.ramp_up_seconds) * (worker_index / max(1, args.concurrency - 1)))
            while True:
                item = await queue.get()
                if item is None:
                    return
                result = await _one_request(client, args=args, base_url=base_url, tokens=tokens, index=int(item))
                async with result_lock:
                    results.append(result)

        await asyncio.gather(*(worker(i) for i in range(int(args.concurrency))))
    return results


async def _run_duration(args: argparse.Namespace, base_url: str, tokens: List[str]) -> List[RequestResult]:
    deadline = time.perf_counter() + float(args.duration_seconds)
    counter = 0
    counter_lock = asyncio.Lock()
    results: List[RequestResult] = []
    result_lock = asyncio.Lock()

    async with httpx.AsyncClient(timeout=float(args.timeout), follow_redirects=False) as client:
        async def next_index() -> Optional[int]:
            nonlocal counter
            async with counter_lock:
                if args.requests and counter >= int(args.requests):
                    return None
                if time.perf_counter() >= deadline:
                    return None
                idx = counter
                counter += 1
                return idx

        async def worker(worker_index: int) -> None:
            if args.ramp_up_seconds > 0 and args.concurrency > 1:
                await asyncio.sleep(float(args.ramp_up_seconds) * (worker_index / max(1, args.concurrency - 1)))
            while time.perf_counter() < deadline:
                idx = await next_index()
                if idx is None:
                    return
                result = await _one_request(client, args=args, base_url=base_url, tokens=tokens, index=idx)
                async with result_lock:
                    results.append(result)

        await asyncio.gather(*(worker(i) for i in range(int(args.concurrency))))
    return results


def _percentile(values: List[float], pct: float) -> Optional[float]:
    if not values:
        return None
    sorted_values = sorted(values)
    if len(sorted_values) == 1:
        return sorted_values[0]
    rank = (len(sorted_values) - 1) * (pct / 100.0)
    lower = int(rank)
    upper = min(lower + 1, len(sorted_values) - 1)
    weight = rank - lower
    return sorted_values[lower] * (1.0 - weight) + sorted_values[upper] * weight


def _summarize(results: List[RequestResult], started_at: float, finished_at: float, args: argparse.Namespace) -> Dict[str, Any]:
    elapsed = max(0.001, finished_at - started_at)
    latencies = [r.elapsed_ms for r in results]
    ok_count = sum(1 for r in results if r.ok)
    status_counts: Dict[str, int] = {}
    path_counts: Dict[str, int] = {}
    error_samples: List[Dict[str, Any]] = []

    for result in results:
        status_counts[str(result.status_code)] = status_counts.get(str(result.status_code), 0) + 1
        key = f"{result.method} {result.path}"
        path_counts[key] = path_counts.get(key, 0) + 1
        if not result.ok and len(error_samples) < int(args.error_samples):
            error_samples.append({
                "method": result.method,
                "path": result.path,
                "status_code": result.status_code,
                "elapsed_ms": round(result.elapsed_ms, 2),
                "error": result.error,
            })

    return {
        "run_id": args.run_id,
        "scenario": args.scenario,
        "requests_attempted": len(results),
        "ok": ok_count,
        "failed": len(results) - ok_count,
        "success_rate": round(ok_count / len(results), 4) if results else 0.0,
        "elapsed_seconds": round(elapsed, 3),
        "requests_per_second": round(len(results) / elapsed, 3),
        "concurrency": int(args.concurrency),
        "status_counts": status_counts,
        "path_counts": path_counts,
        "latency_ms": {
            "min": round(min(latencies), 2) if latencies else None,
            "avg": round(statistics.fmean(latencies), 2) if latencies else None,
            "p50": round(_percentile(latencies, 50) or 0.0, 2) if latencies else None,
            "p90": round(_percentile(latencies, 90) or 0.0, 2) if latencies else None,
            "p95": round(_percentile(latencies, 95) or 0.0, 2) if latencies else None,
            "p99": round(_percentile(latencies, 99) or 0.0, 2) if latencies else None,
            "max": round(max(latencies), 2) if latencies else None,
        },
        "error_samples": error_samples,
        "notify_friends": bool(args.notify_friends),
    }


def _print_summary(summary: Dict[str, Any]) -> None:
    latency = summary.get("latency_ms") if isinstance(summary.get("latency_ms"), dict) else {}
    print("Cocolon load test summary")
    print(f"  run_id: {summary.get('run_id')}")
    print(f"  scenario: {summary.get('scenario')}")
    print(f"  attempted: {summary.get('requests_attempted')}  ok: {summary.get('ok')}  failed: {summary.get('failed')}  success_rate: {summary.get('success_rate')}")
    print(f"  elapsed_seconds: {summary.get('elapsed_seconds')}  rps: {summary.get('requests_per_second')}  concurrency: {summary.get('concurrency')}")
    print(
        "  latency_ms: "
        f"p50={latency.get('p50')} p90={latency.get('p90')} p95={latency.get('p95')} "
        f"p99={latency.get('p99')} max={latency.get('max')} avg={latency.get('avg')}"
    )
    print(f"  status_counts: {json.dumps(summary.get('status_counts') or {}, ensure_ascii=False, sort_keys=True)}")
    print(f"  path_counts: {json.dumps(summary.get('path_counts') or {}, ensure_ascii=False, sort_keys=True)}")
    errors = summary.get("error_samples") or []
    if errors:
        print("  error_samples:")
        for item in errors:
            print(f"    - {item}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run lightweight Cocolon API load tests.")
    parser.add_argument("--base-url", default=os.getenv("COCOLON_LOAD_BASE_URL", ""), help="API base URL, e.g. https://api.example.com")
    parser.add_argument("--scenario", choices=SCENARIOS, default="app-bootstrap")
    parser.add_argument("--endpoint", help="Endpoint path for custom-get/custom-post, e.g. /home/state")
    parser.add_argument("--payload-json", help="JSON object or @file.json for custom-post")
    parser.add_argument("--token", action="append", help="Bearer token. Repeatable. Env: COCOLON_LOAD_BEARER_TOKEN")
    parser.add_argument("--token-file", help="Text file containing one bearer token per line")
    parser.add_argument("--legacy-user-id", default=os.getenv("COCOLON_LOAD_LEGACY_USER_ID", ""), help="Only for local legacy-user-id environments")
    parser.add_argument("--requests", type=int, default=100, help="Total request count. In duration mode, this is an optional upper bound.")
    parser.add_argument("--duration-seconds", type=float, default=0.0, help="Run for this many seconds instead of fixed count when > 0.")
    parser.add_argument("--concurrency", type=int, default=10)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--ramp-up-seconds", type=float, default=0.0)
    parser.add_argument("--json", action="store_true", help="Print JSON summary only.")
    parser.add_argument("--output-json", help="Write summary JSON to this path.")
    parser.add_argument("--error-samples", type=int, default=5)
    parser.add_argument("--run-id", default=os.getenv("COCOLON_LOAD_RUN_ID", ""), help="Run label; defaults to load-<timestamp>.")
    parser.add_argument("--emotion-type", default="喜び")
    parser.add_argument("--emotion-strength", default="medium")
    parser.add_argument("--category", default="生活")

    notify = parser.add_mutually_exclusive_group()
    notify.add_argument("--notify-friends", action="store_true", dest="notify_friends", help="Enable friend notification path. Use to test FCM queue.")
    notify.add_argument("--no-notify-friends", action="store_false", dest="notify_friends", help="Disable friend notification path.")
    parser.set_defaults(notify_friends=False)
    return parser


async def _main_async(args: argparse.Namespace) -> Dict[str, Any]:
    base_url = _normalize_base_url(args.base_url)
    args.concurrency = max(1, int(args.concurrency or 1))
    args.requests = max(1, int(args.requests or 1))
    if not args.run_id:
        args.run_id = f"load-{int(time.time())}"

    tokens = _load_tokens(args)
    if args.scenario in (WRITE_SCENARIOS | {"mix"}) and not tokens and not args.legacy_user_id:
        raise SystemExit("write scenarios require --token/--token-file or --legacy-user-id for local legacy environments")

    started_at = time.perf_counter()
    if args.duration_seconds and args.duration_seconds > 0:
        results = await _run_duration(args, base_url, tokens)
    else:
        results = await _run_fixed_count(args, base_url, tokens)
    finished_at = time.perf_counter()
    return _summarize(results, started_at, finished_at, args)


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    summary = asyncio.run(_main_async(args))
    if args.output_json:
        Path(args.output_json).write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        _print_summary(summary)
    if summary.get("failed"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
