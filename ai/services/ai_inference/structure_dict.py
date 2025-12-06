# -*- coding: utf-8 -*-
"""
Mash構造辞書ローダー & 簡易応答エンジン

- ai/data/processed/structure_dictionary.json を読み込み
- 「◯◯とは？」「◯◯って何？」のような“定義質問”に対して
  Mash構造辞書ベースの説明文を返す。
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("mymodel.structure_dict")

_STRUCTURE_CACHE: Optional[Dict[str, Any]] = None


def _candidate_paths() -> list[Path]:
    """
    structure_dictionary.json を探す候補パス。
    - 通常レイアウト: mashos-api/ai/data/processed/structure_dictionary.json
    - そのほか、開発環境のルートが異なる場合も一応考慮。
    """
    here = Path(__file__).resolve()
    # .../ai/services/ai_inference/app.py -> parents[2] = .../ai
    ai_root = here.parents[2]
    candidates = [
        ai_root / "data" / "processed" / "structure_dictionary.json",                # mashos-api/ai/...
        ai_root.parent / "mashos" / "ai" / "data" / "processed" / "structure_dictionary.json",  # mashos/ai/...
        Path.cwd() / "ai" / "data" / "processed" / "structure_dictionary.json",
        Path.cwd() / "mashos" / "ai" / "data" / "processed" / "structure_dictionary.json",
    ]
    return candidates


def load_structure_dict() -> Dict[str, Any]:
    """
    Mash構造辞書(JSON)を読み込んで返す。
    JSON 形式は以下どちらにも対応する：
      A) { "meta": {...}, "entries": { "罪悪感": {...}, ... } }
      B) { "罪悪感": {...}, ... }
    """
    global _STRUCTURE_CACHE
    if _STRUCTURE_CACHE is not None:
        return _STRUCTURE_CACHE

    for p in _candidate_paths():
        if p.exists():
            try:
                raw = json.loads(p.read_text(encoding="utf-8"))
                if isinstance(raw, dict) and "entries" in raw and isinstance(raw["entries"], dict):
                    entries = raw["entries"]
                elif isinstance(raw, dict):
                    entries = raw
                else:
                    logger.warning("structure_dictionary.json is not a dict: %r", type(raw))
                    entries = {}
                _STRUCTURE_CACHE = entries
                logger.info("Loaded structure_dictionary.json from %s (entries=%d)", p, len(entries))
                return _STRUCTURE_CACHE
            except Exception as e:
                logger.warning("Failed to load structure_dictionary.json at %s: %s", p, e)

    logger.info("structure_dictionary.json not found; proceeding without structure dict.")
    _STRUCTURE_CACHE = {}
    return _STRUCTURE_CACHE


def _is_definition_query(instr: str, lang: str) -> bool:
    """
    「◯◯とは？」「◯◯って何？」のような“定義を聞いている”照会かどうかをざっくり判定。
    """
    t = instr.strip()
    if lang == "ja":
        patterns = ["とは？", "とは何", "とはなに", "って何", "ってなに", "ってなんですか"]
        return any(p in t for p in patterns)
    else:
        lower = t.lower()
        patterns_en = ["what is ", "what's ", "explain ", "definition of "]
        return any(p in lower for p in patterns_en)


def _find_matching_entries(instr: str, lang: str) -> Dict[str, Any]:
    """
    照会文に含まれている構造語（日本語/英語ラベル）を辞書から探す。
    戻り値は {term_jp: entry, ...}
    """
    entries = load_structure_dict()
    if not entries:
        return {}

    text = instr
    lower = instr.lower()
    hits: Dict[str, Any] = {}

    for key, entry in entries.items():
        term_jp = str(entry.get("term_jp") or key).strip()
        term_en = str(entry.get("term_en") or "").strip()

        if term_jp and term_jp in text:
            hits[term_jp] = entry
            continue
        if term_en and term_en.lower() in lower:
            hits[term_jp] = entry
            continue

    return hits


def build_structure_answer(instr: str, lang: str = "ja") -> Optional[str]:
    """
    照会文が「定義質問」で、かつ構造語がヒットした場合に、
    Mash構造辞書をもとにした説明文を返す。該当しなければ None。
    """
    if not _is_definition_query(instr, lang):
        return None

    hits = _find_matching_entries(instr, lang)
    if not hits:
        return None

    term_jp, entry = next(iter(hits.items()))
    term_en = (entry.get("term_en") or "").strip()
    sections: Dict[str, str] = entry.get("sections") or {}

    if term_en:
        title = f"構造語：{term_jp}（{term_en}）"
    else:
        title = f"構造語：{term_jp}"

    order = ["定義", "構成要素", "類似構造との違い", "観測視点", "注記"]
    parts = [title]

    for key in order:
        content = (sections.get(key) or "").strip()
        if content:
            parts.append(f"■ {key}\n{content}")

    if len(parts) == 1:
        raw_block = str(entry.get("raw_block") or "").strip()
        if raw_block:
            parts.append(raw_block)

    return "\n\n".join(parts) if len(parts) > 1 else None
