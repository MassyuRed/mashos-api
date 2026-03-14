#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[1]
TARGETS: Sequence[Path] = (
    ROOT / "App.js",
    ROOT / "lib",
    ROOT / "screens",
)
FORBIDDEN_PATTERNS: Sequence[Tuple[str, re.Pattern[str]]] = (
    ("supabase.from(", re.compile(r"\bsupabase\.from\s*\(")),
    ("supabase.rpc(", re.compile(r"\bsupabase\.rpc\s*\(")),
    ("supabase.channel(", re.compile(r"\bsupabase\.channel\s*\(")),
    ("raw fetch(", re.compile(r"(?<![\w$.])fetch\s*\(")),
)


def iter_js_files(paths: Iterable[Path]) -> Iterable[Path]:
    for path in paths:
        if not path.exists():
            continue
        if path.is_file() and path.suffix in {".js", ".jsx", ".ts", ".tsx"}:
            yield path
            continue
        if path.is_dir():
            for file_path in sorted(path.rglob("*")):
                if file_path.is_file() and file_path.suffix in {".js", ".jsx", ".ts", ".tsx"}:
                    yield file_path


def find_violations() -> List[str]:
    violations: List[str] = []
    for file_path in iter_js_files(TARGETS):
        try:
            text = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = file_path.read_text(encoding="utf-8", errors="ignore")

        rel = file_path.relative_to(ROOT)
        for label, pattern in FORBIDDEN_PATTERNS:
            if label == "raw fetch(" and rel.as_posix() == "lib/apiClient.js":
                continue
            for match in pattern.finditer(text):
                line_no = text.count("\n", 0, match.start()) + 1
                violations.append(f"{rel}:{line_no}: {label}")
    return violations


def main() -> int:
    violations = find_violations()
    if violations:
        print("Forbidden RN surface usage detected:", file=sys.stderr)
        for violation in violations:
            print(f" - {violation}", file=sys.stderr)
        return 1

    print("OK: no direct supabase.from/rpc/channel or raw fetch usage found in App.js/lib/screens")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())