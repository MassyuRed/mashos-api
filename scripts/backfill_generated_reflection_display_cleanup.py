from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_IMPORT_CANDIDATES = (
    ROOT,
    ROOT / "ai",
    ROOT / "ai" / "services",
    ROOT / "ai" / "services" / "ai_inference",
    ROOT / "services",
    ROOT / "services" / "ai_inference",
)
_seen_paths: set[str] = set()
for candidate in _IMPORT_CANDIDATES:
    if not candidate.exists():
        continue
    path_str = str(candidate)
    if path_str in _seen_paths:
        continue
    _seen_paths.add(path_str)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from generated_reflection_maintenance import run_generated_reflection_backfill_cleanup



def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Backfill persisted display bundles for Premium generated reflections and clean up exact archived clones."
        )
    )
    parser.add_argument("--user-id", dest="user_id", default="", help="Limit the job to a single owner_user_id.")
    parser.add_argument("--batch-size", dest="batch_size", type=int, default=500, help="Fetch batch size for Supabase paging.")
    parser.add_argument("--max-rows", dest="max_rows", type=int, default=None, help="Optional hard cap for scanned rows.")
    parser.add_argument("--sample-limit", dest="sample_limit", type=int, default=20, help="How many unresolved multi-answer groups to include in the summary.")
    parser.add_argument("--no-backfill", dest="do_backfill", action="store_false", help="Skip display bundle backfill and report cleanup only.")
    parser.add_argument("--no-cleanup", dest="do_cleanup", action="store_false", help="Skip duplicate cleanup planning and execution.")
    parser.add_argument(
        "--canonicalize-active-only",
        dest="canonicalize_active_only",
        action="store_true",
        help="Canonicalize active generated reflections per owner_user_id + q_key only; skip inactive duplicate delete planning.",
    )
    parser.add_argument(
        "--leave-active-duplicates",
        dest="archive_active_duplicates",
        action="store_false",
        help="Do not archive exact active duplicates; only delete inactive clones.",
    )
    parser.add_argument(
        "--allow-delete",
        dest="allow_delete",
        action="store_true",
        help="Allow physical DELETE for inactive duplicate clones. Default cleanup is archive-only.",
    )
    parser.add_argument(
        "--apply",
        dest="apply",
        action="store_true",
        help="Apply the planned changes. Without this flag the script runs in dry-run mode.",
    )
    return parser


async def _async_main(args: argparse.Namespace) -> int:
    summary = await run_generated_reflection_backfill_cleanup(
        user_id=str(args.user_id or "").strip() or None,
        batch_size=int(args.batch_size or 500),
        max_rows=args.max_rows,
        apply=bool(args.apply),
        do_backfill=bool(args.do_backfill),
        do_cleanup=bool(args.do_cleanup),
        archive_active_duplicates=bool(args.archive_active_duplicates),
        canonicalize_active_only=bool(args.canonicalize_active_only),
        allow_delete=bool(args.allow_delete),
        sample_limit=int(args.sample_limit or 20),
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0



def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return asyncio.run(_async_main(args))


if __name__ == "__main__":
    raise SystemExit(main())
