#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_PATTERNS: Sequence[Tuple[str, re.Pattern[str]]] = (
    ("supabase.from(", re.compile(r"\bsupabase\.from\s*\(")),
    ("supabase.rpc(", re.compile(r"\bsupabase\.rpc\s*\(")),
    ("supabase.channel(", re.compile(r"\bsupabase\.channel\s*\(")),
    ("raw fetch(", re.compile(r"(?<![\w$.])fetch\s*\(")),
)
SOURCE_SUFFIXES = {".js", ".jsx", ".ts", ".tsx"}
RN_ROOT_ENV_VARS = ("COCOLON_RN_ROOT", "RN_ROOT")


def _looks_like_rn_root(path: Path) -> bool:
    return (
        path.is_dir()
        and (path / "App.js").is_file()
        and (path / "lib").is_dir()
        and (path / "screens").is_dir()
    )



def _iter_candidate_rn_roots() -> Iterable[Path]:
    seen: set[str] = set()

    def _yield(path: Path) -> Iterable[Path]:
        try:
            resolved = path.resolve()
        except FileNotFoundError:
            resolved = path.absolute()
        key = str(resolved)
        if key in seen:
            return
        seen.add(key)
        yield path

    for env_name in RN_ROOT_ENV_VARS:
        value = os.environ.get(env_name)
        if value:
            yield from _yield(Path(value).expanduser())

    anchors = [ROOT, ROOT.parent, *ROOT.parents[:2]]
    candidate_names = ("cocolon-mvp", "RN(アプリ側)")
    for anchor in anchors:
        yield from _yield(anchor)
        for name in candidate_names:
            yield from _yield(anchor / name)



def _find_rn_root() -> Path | None:
    for candidate in _iter_candidate_rn_roots():
        if _looks_like_rn_root(candidate):
            return candidate.resolve()
    return None


RN_ROOT = _find_rn_root()



def iter_js_files(paths: Iterable[Path]) -> Iterable[Path]:
    for path in paths:
        if not path.exists():
            continue
        if path.is_file() and path.suffix in SOURCE_SUFFIXES:
            yield path
            continue
        if path.is_dir():
            for file_path in sorted(path.rglob("*")):
                if file_path.is_file() and file_path.suffix in SOURCE_SUFFIXES:
                    yield file_path



def find_violations() -> List[str]:
    if RN_ROOT is None:
        return []

    targets: Sequence[Path] = (
        RN_ROOT / "App.js",
        RN_ROOT / "lib",
        RN_ROOT / "screens",
    )
    violations: List[str] = []
    for file_path in iter_js_files(targets):
        try:
            text = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = file_path.read_text(encoding="utf-8", errors="ignore")

        rel = file_path.relative_to(RN_ROOT)
        for label, pattern in FORBIDDEN_PATTERNS:
            if label == "raw fetch(" and rel.as_posix() == "lib/apiClient.js":
                continue
            for match in pattern.finditer(text):
                line_no = text.count("\n", 0, match.start()) + 1
                violations.append(f"{rel}:{line_no}: {label}")
    return violations



def main() -> int:
    if RN_ROOT is None:
        print(
            "Unable to locate the RN surface root (App.js/lib/screens). "
            "Set COCOLON_RN_ROOT if you want to override auto-detection.",
            file=sys.stderr,
        )
        return 2

    violations = find_violations()
    if violations:
        print(f"Forbidden RN surface usage detected under: {RN_ROOT}", file=sys.stderr)
        for violation in violations:
            print(f" - {violation}", file=sys.stderr)
        return 1

    print(f"OK: no direct supabase.from/rpc/channel or raw fetch usage found in {RN_ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
