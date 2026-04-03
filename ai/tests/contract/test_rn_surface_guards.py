from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

API_ROOT = Path(__file__).resolve().parents[3]
FORBIDDEN = (
    ("supabase.from(", re.compile(r"\bsupabase\.from\s*\(")),
    ("supabase.rpc(", re.compile(r"\bsupabase\.rpc\s*\(")),
    ("supabase.channel(", re.compile(r"\bsupabase\.channel\s*\(")),
    ("raw fetch(", re.compile(r"(?<![\w$.])fetch\s*\(")),
)
RN_ROOT_ENV_VARS = ("COCOLON_RN_ROOT", "RN_ROOT")


def _looks_like_rn_root(path: Path) -> bool:
    return (
        path.is_dir()
        and (path / "App.js").is_file()
        and (path / "lib").is_dir()
        and (path / "screens").is_dir()
    )



def _iter_candidate_rn_roots():
    seen: set[str] = set()

    def _yield(path: Path):
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

    anchors = [API_ROOT, API_ROOT.parent, *API_ROOT.parents[:2]]
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
pytestmark = pytest.mark.skipif(
    RN_ROOT is None,
    reason="RN sources are not available for the RN surface guard tests.",
)
SOURCE_SUFFIXES = {".js", ".jsx", ".ts", ".tsx"}



def _iter_files():
    assert RN_ROOT is not None
    targets = (RN_ROOT / "App.js", RN_ROOT / "lib", RN_ROOT / "screens")
    for target in targets:
        if target.is_file() and target.suffix in SOURCE_SUFFIXES:
            yield target
        elif target.is_dir():
            for file_path in sorted(target.rglob("*")):
                if file_path.is_file() and file_path.suffix in SOURCE_SUFFIXES:
                    yield file_path



def test_rn_surface_has_no_direct_supabase_usage():
    assert RN_ROOT is not None
    hits = []
    for file_path in _iter_files():
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        rel = file_path.relative_to(RN_ROOT)
        for label, pattern in FORBIDDEN:
            if label == "raw fetch(" and rel.as_posix() == "lib/apiClient.js":
                continue
            if pattern.search(text):
                hits.append(f"{rel}::{label}")
    assert not hits, f"Forbidden direct Supabase usage found: {hits}"



def test_guard_script_passes():
    script = API_ROOT / "scripts" / "check_no_direct_supabase.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=API_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    output = (result.stdout or "") + (result.stderr or "")
    assert result.returncode == 0, output
