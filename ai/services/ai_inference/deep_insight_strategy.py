# -*- coding: utf-8 -*-
"""deep_insight_strategy.py

Phase5.4:
DeepInsight の戦略（deep_dive / unexplored）の判定ロジックを
サーバ側の設定（ENV）で切り替え可能にする。

狙い:
- JS側のロジックを増やさず、MashOS側の設定変更だけで
  DeepInsight の質問戦略を調整できるようにする。

主なENV:
- DEEP_INSIGHT_RICH_THRESHOLD (default: 8)
- DEEP_INSIGHT_RICH_THRESHOLD_FREE / _PLUS / _PREMIUM
- DEEP_INSIGHT_FREE_ALWAYS_UNEXPLORED (default: false)
- DEEP_INSIGHT_STRATEGY_FORCE (deep_dive|unexplored)
- DEEP_INSIGHT_STRATEGY_FORCE_FREE / _PLUS / _PREMIUM

注意:
- ここでの "rich" は「構造パターン(triggers)から推定した入力イベント数」が
  threshold 以上であることを指す。
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional, Tuple


def _env_bool(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return bool(default)
    s = str(v).strip().lower()
    if s in ("1", "true", "yes", "y", "on"):
        return True
    if s in ("0", "false", "no", "n", "off"):
        return False
    return bool(default)


def _env_int(name: str, default: int) -> int:
    v = os.getenv(name)
    if v is None or str(v).strip() == "":
        return int(default)
    try:
        return int(float(str(v).strip()))
    except Exception:
        return int(default)


def normalize_tier(tier: Optional[str]) -> str:
    t = str(tier or "").strip().lower()
    if t in ("premium", "pro"):
        return "premium"
    if t in ("plus", "paid"):
        return "plus"
    return "free"


def _normalize_strategy(s: Optional[str]) -> Optional[str]:
    x = str(s or "").strip().lower()
    if x in ("deep_dive", "deep", "dive"):
        return "deep_dive"
    if x in ("unexplored", "explore", "exploration", "sparse"):
        return "unexplored"
    return None


def build_deep_insight_strategy_config() -> Dict[str, Any]:
    """Return sanitized strategy config for debug/UI meta."""
    free_always = _env_bool("DEEP_INSIGHT_FREE_ALWAYS_UNEXPLORED", False)

    global_force = _normalize_strategy(os.getenv("DEEP_INSIGHT_STRATEGY_FORCE"))
    force_free = _normalize_strategy(os.getenv("DEEP_INSIGHT_STRATEGY_FORCE_FREE"))
    force_plus = _normalize_strategy(os.getenv("DEEP_INSIGHT_STRATEGY_FORCE_PLUS"))
    force_premium = _normalize_strategy(os.getenv("DEEP_INSIGHT_STRATEGY_FORCE_PREMIUM"))

    base_thr = max(0, _env_int("DEEP_INSIGHT_RICH_THRESHOLD", 8))
    thr_free = max(0, _env_int("DEEP_INSIGHT_RICH_THRESHOLD_FREE", base_thr))
    thr_plus = max(0, _env_int("DEEP_INSIGHT_RICH_THRESHOLD_PLUS", base_thr))
    thr_premium = max(0, _env_int("DEEP_INSIGHT_RICH_THRESHOLD_PREMIUM", base_thr))

    return {
        "version": "deep_insight.strategy.v1",
        "free_always_unexplored": bool(free_always),
        "force": {
            "all": global_force,
            "free": force_free,
            "plus": force_plus,
            "premium": force_premium,
        },
        "rich_threshold": {
            "default": int(base_thr),
            "free": int(thr_free),
            "plus": int(thr_plus),
            "premium": int(thr_premium),
        },
    }


def decide_deep_insight_strategy(
    *,
    unique_events: int,
    tier: Optional[str],
) -> Tuple[str, Dict[str, Any]]:
    """Decide strategy and return (strategy, decision_meta)."""
    t = normalize_tier(tier)

    cfg = build_deep_insight_strategy_config()

    # 1) forced (global -> tier)
    forced_global = _normalize_strategy(cfg.get("force", {}).get("all"))
    forced_tier = _normalize_strategy(cfg.get("force", {}).get(t))

    forced = forced_tier or forced_global
    if forced in ("deep_dive", "unexplored"):
        # density still reported for debug
        thr = int(cfg.get("rich_threshold", {}).get(t) or cfg.get("rich_threshold", {}).get("default") or 8)
        density = "rich" if int(unique_events) >= int(thr) else "sparse"
        return forced, {
            "tier": t,
            "unique_events": int(unique_events),
            "rich_threshold": int(thr),
            "density": density,
            "forced": True,
            "forced_by": "tier" if forced_tier else "global",
        }

    # 2) free always unexplored
    if t == "free" and bool(cfg.get("free_always_unexplored")):
        thr = int(cfg.get("rich_threshold", {}).get("free") or cfg.get("rich_threshold", {}).get("default") or 8)
        density = "rich" if int(unique_events) >= int(thr) else "sparse"
        return "unexplored", {
            "tier": t,
            "unique_events": int(unique_events),
            "rich_threshold": int(thr),
            "density": density,
            "forced": True,
            "forced_by": "free_always_unexplored",
        }

    # 3) threshold decision
    thr = int(cfg.get("rich_threshold", {}).get(t) or cfg.get("rich_threshold", {}).get("default") or 8)
    thr = max(0, int(thr))
    density = "rich" if int(unique_events) >= int(thr) else "sparse"
    strategy = "deep_dive" if density == "rich" else "unexplored"

    return strategy, {
        "tier": t,
        "unique_events": int(unique_events),
        "rich_threshold": int(thr),
        "density": density,
        "forced": False,
    }
