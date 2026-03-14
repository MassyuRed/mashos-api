from __future__ import annotations

import subprocess
import sys
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
TARGETS = (ROOT / "App.js", ROOT / "lib", ROOT / "screens")
FORBIDDEN = (
    ("supabase.from(", re.compile(r"\bsupabase\.from\s*\(")),
    ("supabase.rpc(", re.compile(r"\bsupabase\.rpc\s*\(")),
    ("supabase.channel(", re.compile(r"\bsupabase\.channel\s*\(")),
    ("raw fetch(", re.compile(r"(?<![\w$.])fetch\s*\(")),
)



def _iter_files():
    for target in TARGETS:
        if target.is_file():
            yield target
        elif target.is_dir():
            yield from sorted(target.rglob("*.js"))



def test_rn_surface_has_no_direct_supabase_usage():
    hits = []
    for file_path in _iter_files():
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        rel = file_path.relative_to(ROOT)
        for label, pattern in FORBIDDEN:
            if label == "raw fetch(" and rel.as_posix() == "lib/apiClient.js":
                continue
            if pattern.search(text):
                hits.append(f"{rel}::{label}")
    assert not hits, f"Forbidden direct Supabase usage found: {hits}"



def test_guard_script_passes():
    script = ROOT / "scripts" / "check_no_direct_supabase.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    output = (result.stdout or "") + (result.stderr or "")
    assert result.returncode == 0, output