# -*- coding: utf-8 -*-
"""watashi_map_service.py

Cocolon 自己分析「わたしマップ」payload builder.

This service is intentionally presentation-oriented. It converts the existing
self-structure report basis into content_json.watashiMap without changing DB
physical names, public routes, report families, or legacy payloads.
"""

from __future__ import annotations

from copy import deepcopy
import re
from typing import Any, Dict, Iterable, List, Optional, Tuple

WATASHI_MAP_VERSION = "watashi.map.v1"
WATASHI_MAP_LABEL = "わたしマップ"
WATASHI_MAP_OVERVIEW_TITLE = "今のわたしマップ"
DETAIL_REPORT_TITLE = "詳しい自己分析レポート"
DETAIL_REPORT_LOCK_LABEL = "詳しい自己分析レポートは Plus プラン以上で読めます。"
PREMIUM_LOCK_LABEL = "長期の変化と深い分かれ道は Premium プランで見られます。"
SAFE_NOTE = "これは性格タイプではなく、この場面で見えた動き方です。"
NOT_ENOUGH_TITLE = "まだ地図にできる観測が少なめです"
NOT_ENOUGH_BODY = "入力が増えると、場面ごとの役割スイッチや、よく通るルートが見えやすくなります。"
NOT_ENOUGH_ACTION = "今日の入力をする"

ROLE_LABEL_FALLBACKS: Dict[str, str] = {
    "Organizer": "整える役割",
    "整理者": "整える役割",
    "Supporter": "受け止める役割",
    "支援者": "受け止める役割",
    "Defender": "守る役割",
    "防御者": "守る役割",
    "Mediator": "合わせる役割",
    "調整者": "合わせる役割",
    "Challenger": "進める役割",
    "挑戦者": "進める役割",
    "Analyzer": "確かめる役割",
    "分析者": "確かめる役割",
    "Observer": "観察する役割",
    "観察者": "観察する役割",
    "Maintainer": "維持する役割",
    "維持者": "維持する役割",
    "Explorer": "探る役割",
    "探索者": "探る役割",
    "Creator": "生み出す役割",
    "創造者": "生み出す役割",
    "organizer": "整える役割",
    "organize": "整える役割",
    "arranger": "整える役割",
    "coordinator": "整える役割",
    "listener": "受け止める役割",
    "receiver": "受け止める役割",
    "supporter": "受け止める役割",
    "support": "受け止める役割",
    "driver": "進める役割",
    "mover": "進める役割",
    "starter": "進める役割",
    "progress": "進める役割",
    "guardian": "守る役割",
    "guard": "守る役割",
    "protector": "守る役割",
    "adjuster": "合わせる役割",
    "adapter": "合わせる役割",
    "matcher": "合わせる役割",
    "checker": "確かめる役割",
    "verifier": "確かめる役割",
    "observer": "確かめる役割",
    "holder": "預かる役割",
    "caretaker": "預かる役割",
    "keeper": "預かる役割",
}

ACTION_LABEL_FALLBACKS: Dict[str, str] = {
    "prioritize": "先に整理する",
    "organize": "状況を整理する",
    "listen": "相手の話を聞く",
    "support": "相手を支える",
    "distance": "一度距離を置く",
    "adjust": "場に合わせて言葉を選ぶ",
    "confirm": "意味や背景を確かめる",
    "hold": "一時的に引き受ける",
}

UNKNOWN_KIND_LABELS: Dict[str, str] = {
    "real_world_role_missing": "現実での役割がまだ薄い場所",
    "desired_role_missing": "理想の役割がまだ薄い場所",
    "self_world_role_missing": "自己認識の役割がまだ薄い場所",
    "role_gap_unclear": "役割のズレがまだ曖昧な場所",
    "target_missing": "対象の切り分けがまだ薄い場所",
}


def normalize_report_mode(mode: Any) -> str:
    s = str(mode or "").strip().lower()
    if s == "structural":
        return "deep"
    if s in {"light", "standard", "deep"}:
        return s
    return "standard"


def normalize_viewer_tier(tier: Any, *, report_mode: Any = None) -> str:
    s = str(tier or "").strip().lower()
    if s in {"free", "plus", "premium"}:
        return s
    mode = normalize_report_mode(report_mode)
    if mode == "light":
        return "free"
    if mode == "deep":
        return "premium"
    return "plus"


def _as_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _first_text(*values: Any) -> str:
    for value in values:
        if isinstance(value, (list, tuple)):
            for item in value:
                s = _clean(item)
                if s:
                    return s
        else:
            s = _clean(value)
            if s:
                return s
    return ""


def _coerce_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def _coerce_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(value)
    except Exception:
        return default


def _unique_keep_order(values: Iterable[Any], *, limit: Optional[int] = None) -> List[str]:
    out: List[str] = []
    for raw in values:
        s = _clean(raw)
        if not s or s in out:
            continue
        out.append(s)
        if limit is not None and len(out) >= limit:
            break
    return out


def _fallback_role_label(key: str) -> str:
    s = _clean(key)
    if not s:
        return ""
    low = s.lower()
    if low in ROLE_LABEL_FALLBACKS:
        return ROLE_LABEL_FALLBACKS[low]
    for needle, label in ROLE_LABEL_FALLBACKS.items():
        if needle in low:
            return label
    return s


def _fallback_action_label(key: str) -> str:
    s = _clean(key)
    if not s:
        return ""
    low = s.lower()
    if low in ACTION_LABEL_FALLBACKS:
        return ACTION_LABEL_FALLBACKS[low]
    for needle, label in ACTION_LABEL_FALLBACKS.items():
        if needle in low:
            return label
    return s


def _role_key(row: Any) -> str:
    d = _as_dict(row)
    return _first_text(d.get("role_key"), d.get("key"), d.get("template_role"), d.get("top_role_key"), d.get("role"))


def _role_label(row: Any) -> str:
    d = _as_dict(row)
    label = _first_text(
        d.get("role_label_ja"),
        d.get("label_ja"),
        d.get("template_role_label_ja"),
        d.get("top_role_label_ja"),
        d.get("label"),
    )
    if label:
        if label in ROLE_LABEL_FALLBACKS:
            return ROLE_LABEL_FALLBACKS[label]
        low = label.lower()
        if low in ROLE_LABEL_FALLBACKS:
            return ROLE_LABEL_FALLBACKS[low]
        if "役割" in label:
            return label
        if label.endswith("者"):
            return f"{label}の役割"
        return label
    return _fallback_role_label(_role_key(d))


def _target_key(row: Any) -> str:
    d = _as_dict(row)
    return _first_text(d.get("target_key"), d.get("key"), d.get("context_key"), d.get("target"))


def _target_label(row: Any) -> str:
    d = _as_dict(row)
    return _first_text(d.get("target_label_ja"), d.get("label_ja"), d.get("context_label"), d.get("label"), _target_key(d))


def _target_kind(row: Any) -> str:
    d = _as_dict(row)
    return _first_text(d.get("target_type"), d.get("kind"), "environment")


def _pattern_label(row: Any) -> str:
    d = _as_dict(row)
    label = _first_text(d.get("label_ja"), d.get("action_label_ja"), d.get("thinking_label_ja"), d.get("label"))
    if label:
        return label
    return _fallback_action_label(_first_text(d.get("key"), d.get("action_key"), d.get("thinking_key")))


def _score_display(score: Any, evidence_count: Any = None) -> str:
    val = _coerce_float(score, 0.0)
    count = _coerce_int(evidence_count, 0)
    if val >= 0.75 or count >= 8:
        return "●●●"
    if val >= 0.35 or count >= 3:
        return "●●"
    if val > 0 or count > 0:
        return "●"
    return "—"


def _period_label_from_period(period: Any) -> str:
    s = _clean(period)
    if not s:
        return "直近 28 日"
    m = re.fullmatch(r"(\d+)d", s.lower())
    if m:
        return f"直近 {int(m.group(1))} 日"
    m = re.fullmatch(r"(\d+)w", s.lower())
    if m:
        return f"直近 {int(m.group(1))} 週"
    m = re.fullmatch(r"(\d+)m", s.lower())
    if m:
        return f"直近 {int(m.group(1))} か月"
    return s


def build_watashi_visibility(report_mode: Any, viewer_tier: Any = None) -> Dict[str, Any]:
    mode = normalize_report_mode(report_mode)
    tier = normalize_viewer_tier(viewer_tier, report_mode=mode)

    if tier == "free" or mode == "light":
        locked = ["routes", "crossroads", "detail_report"]
        return {
            "viewer_tier": "free",
            "summary_visible": True,
            "role_switches_visible": True,
            "routes_visible": False,
            "crossroads_visible": False,
            "unknown_areas_visible": True,
            "detail_report_visible": False,
            "locked_sections": locked,
            "lock_label": DETAIL_REPORT_LOCK_LABEL,
        }

    if tier == "plus" or mode == "standard":
        return {
            "viewer_tier": "plus",
            "summary_visible": True,
            "role_switches_visible": True,
            "routes_visible": True,
            "crossroads_visible": True,
            "unknown_areas_visible": True,
            "detail_report_visible": True,
            "locked_sections": ["long_term_changes", "premium_crossroads"],
            "lock_label": PREMIUM_LOCK_LABEL,
        }

    return {
        "viewer_tier": "premium",
        "summary_visible": True,
        "role_switches_visible": True,
        "routes_visible": True,
        "crossroads_visible": True,
        "unknown_areas_visible": True,
        "detail_report_visible": True,
        "locked_sections": [],
        "lock_label": None,
    }


def _target_lookup_from_basis(basis: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    lookup: Dict[str, Dict[str, Any]] = {}

    def remember(row: Any) -> None:
        d = _as_dict(row)
        key = _target_key(d)
        if not key:
            return
        cur = dict(lookup.get(key) or {})
        cur["key"] = key
        label = _target_label(d)
        kind = _target_kind(d)
        if label:
            cur["label"] = label
        if kind:
            cur["kind"] = kind
        lookup[key] = cur

    remember(_as_dict(basis.get("core_target")))
    for field in (
        "top_targets",
        "target_role_map",
        "target_signatures",
        "generated_roles",
        "self_world_roles",
        "real_world_roles",
        "desired_roles",
        "role_gaps",
        "question_candidates",
    ):
        for row in _as_list(basis.get(field)):
            remember(row)
    return lookup


def _context_from_row(row: Any, target_lookup: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, Any]:
    d = _as_dict(row)
    key = _target_key(d)
    meta = (target_lookup or {}).get(key, {}) if key else {}
    label = _target_label(d) or _clean(meta.get("label")) or "全体"
    kind = _target_kind(d) or _clean(meta.get("kind")) or "environment"
    return {"key": key or "overall", "label": label, "kind": kind}


def _role_from_row(row: Any) -> Dict[str, Any]:
    d = _as_dict(row)
    key = _role_key(d)
    label = _role_label(d) or "役割"
    return {"key": key or label, "label": label}


def _role_switch_rows_from_basis(basis: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = [dict(x) for x in _as_list(basis.get("target_role_map")) if isinstance(x, dict)]
    if rows:
        rows.sort(key=lambda d: (-_coerce_float(d.get("score")), _target_label(d), _role_label(d)))
        return rows

    generated_by_target = {
        _target_key(x): x
        for x in _as_list(basis.get("generated_roles"))
        if isinstance(x, dict) and _target_key(x)
    }
    fallback_rows: List[Dict[str, Any]] = []
    for sig in _as_list(basis.get("target_signatures")):
        if not isinstance(sig, dict):
            continue
        target_key = _target_key(sig)
        if not target_key:
            continue
        generated = _as_dict(generated_by_target.get(target_key))
        fallback_rows.append(
            {
                "target_key": target_key,
                "target_label_ja": _target_label(sig) or _target_label(generated),
                "target_type": _target_kind(sig) or _target_kind(generated),
                "role_key": _first_text(sig.get("top_role_key"), generated.get("template_role"), generated.get("role_key")),
                "role_label_ja": _first_text(sig.get("top_role_label_ja"), generated.get("template_role_label_ja"), generated.get("role_label_ja")),
                "score": sig.get("top_role_score") or generated.get("score"),
                "evidence_count": sig.get("evidence_count") or generated.get("evidence_count"),
                "top_action_keys": sig.get("top_action_keys") or generated.get("top_action_keys") or [],
            }
        )
    if fallback_rows:
        fallback_rows.sort(key=lambda d: (-_coerce_float(d.get("score")), _target_label(d), _role_label(d)))
        return fallback_rows

    core_target = _as_dict(basis.get("core_target"))
    core_role = _as_dict(basis.get("core_role"))
    if core_target or core_role:
        return [
            {
                "target_key": _target_key(core_target) or "overall",
                "target_label_ja": _target_label(core_target) or "全体",
                "target_type": _target_kind(core_target),
                "role_key": _role_key(core_role),
                "role_label_ja": _role_label(core_role),
                "score": core_role.get("score") or core_target.get("score") or 0.0,
                "evidence_count": core_role.get("count") or core_target.get("count") or None,
            }
        ]
    return []


def _action_label_for_row(row: Any, basis: Dict[str, Any]) -> str:
    d = _as_dict(row)
    action_keys = []
    for key_name in ("top_action_keys", "action_keys", "actions"):
        values = d.get(key_name)
        if isinstance(values, list):
            action_keys.extend(values)
        elif values:
            action_keys.append(values)
    for action in action_keys:
        label = _fallback_action_label(_clean(action))
        if label:
            return label

    for item in _as_list(basis.get("action_patterns")):
        label = _pattern_label(item)
        if label:
            return label

    core_action = _as_dict(basis.get("core_action"))
    label = _pattern_label(core_action)
    if label:
        return label

    return "状況を整理する"


def _route_preview(context_label: str, role_label: str, action_label: str) -> str:
    context = _clean(context_label) or "この場面"
    role = _clean(role_label) or "役割"
    action = _clean(action_label) or "行動を選ぶ"
    if context == "全体":
        return f"{role}が立ち上がると、{action}流れが見えます。"
    return f"{context}の場面では、{role}が立ち上がりやすく、{action}流れが見えます。"


def build_role_switches(basis: Dict[str, Any], limit: Optional[int] = None) -> List[Dict[str, Any]]:
    basis = _as_dict(basis)
    target_lookup = _target_lookup_from_basis(basis)
    rows = _role_switch_rows_from_basis(basis)
    out: List[Dict[str, Any]] = []
    seen: set[Tuple[str, str]] = set()

    for row in rows:
        context = _context_from_row(row, target_lookup)
        role = _role_from_row(row)
        uniq = (str(context.get("key") or ""), str(role.get("key") or role.get("label") or ""))
        if uniq in seen:
            continue
        seen.add(uniq)
        action_label = _action_label_for_row(row, basis)
        out.append(
            {
                "context": context,
                "role": role,
                "tendency_label": "立ち上がりやすい",
                "score_display": _score_display(row.get("score"), row.get("evidence_count")),
                "evidence_count": _coerce_int(row.get("evidence_count"), 0) or None,
                "route_preview": _route_preview(str(context.get("label") or ""), str(role.get("label") or ""), action_label),
                "safe_note": SAFE_NOTE,
            }
        )
        if limit is not None and len(out) >= limit:
            break

    return out


def _observation_amount(role_switches: List[Dict[str, Any]], basis: Dict[str, Any]) -> Dict[str, str]:
    evidence = 0
    for item in role_switches:
        evidence += _coerce_int(item.get("evidence_count"), 0)
    if not evidence:
        evidence = len(role_switches) + len(_as_list(basis.get("top_roles"))) + len(_as_list(basis.get("top_targets")))
    if evidence >= 10:
        return {"level": "high", "label": "はっきり見えてきました"}
    if evidence >= 3:
        return {"level": "medium", "label": "少し見えてきました"}
    return {"level": "low", "label": "まだ少なめです"}


def build_watashi_map_overview(
    basis: Dict[str, Any],
    *,
    sections: Optional[Dict[str, Any]] = None,
    role_switches: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    basis = _as_dict(basis)
    role_switches_all = role_switches if isinstance(role_switches, list) else build_role_switches(basis)
    sections = _as_dict(sections)

    contexts: List[Dict[str, str]] = []
    roles: List[Dict[str, str]] = []
    actions: List[Dict[str, str]] = []

    for item in role_switches_all[:3]:
        ctx = _as_dict(item.get("context"))
        role = _as_dict(item.get("role"))
        if _clean(ctx.get("label")) and not any(x.get("label") == ctx.get("label") for x in contexts):
            contexts.append({"key": _clean(ctx.get("key")) or _clean(ctx.get("label")), "label": _clean(ctx.get("label")), "share_label": "よく見えています"})
        if _clean(role.get("label")) and not any(x.get("label") == role.get("label") for x in roles):
            roles.append({"key": _clean(role.get("key")) or _clean(role.get("label")), "label": _clean(role.get("label"))})

    if not contexts:
        for row in _as_list(basis.get("top_targets"))[:3]:
            label = _target_label(row)
            if label and not any(x.get("label") == label for x in contexts):
                contexts.append({"key": _target_key(row) or label, "label": label, "share_label": "見えはじめています"})

    if not roles:
        for row in (_as_list(basis.get("top_roles")) or [_as_dict(basis.get("core_role"))])[:3]:
            label = _role_label(row)
            if label and not any(x.get("label") == label for x in roles):
                roles.append({"key": _role_key(row) or label, "label": label})

    for row in (_as_list(basis.get("action_patterns")) or [_as_dict(basis.get("core_action"))])[:3]:
        label = _pattern_label(row)
        if label and not any(x.get("label") == label for x in actions):
            actions.append({"key": _first_text(_as_dict(row).get("key"), label), "label": label})

    summary = ""
    if contexts and roles:
        summary = f"{contexts[0]['label']}の場面では、{roles[0]['label']}が立ち上がりやすく見えます。"
    elif roles:
        summary = f"今見えている範囲では、{roles[0]['label']}に近い動きが見えています。"
    elif contexts:
        summary = f"{contexts[0]['label']}の場面で、自分の動き方が見えはじめています。"
    else:
        current = sections.get("current_structure")
        if isinstance(current, list):
            summary = _first_text(current)
        summary = summary or _first_text(sections.get("summary"))

    return {
        "title": WATASHI_MAP_OVERVIEW_TITLE,
        "summary": summary or None,
        "active_contexts": contexts[:3],
        "active_roles": roles[:3],
        "action_tendencies": actions[:3],
        "observation_amount": _observation_amount(role_switches_all, basis),
    }


def build_route_patterns(basis: Dict[str, Any], role_switches: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
    basis = _as_dict(basis)
    switches = role_switches if isinstance(role_switches, list) else build_role_switches(basis)
    rows = _role_switch_rows_from_basis(basis)
    routes: List[Dict[str, Any]] = []

    for idx, switch in enumerate(switches[:4]):
        row = rows[idx] if idx < len(rows) else {}
        context = _as_dict(switch.get("context"))
        role = _as_dict(switch.get("role"))
        context_label = _clean(context.get("label")) or "場面"
        role_label = _clean(role.get("label")) or "役割"
        action_label = _action_label_for_row(row, basis)
        result_text = "その場を整えようとする流れが見えます"
        if "聞" in action_label or "支" in action_label or "受" in role_label:
            result_text = "相手の状態を先に受け止めようとする流れが見えます"
        elif "距離" in action_label or "守" in role_label:
            result_text = "一度距離を置いてから考えようとする流れが見えます"
        elif "確" in action_label:
            result_text = "意味や背景を確かめてから動こうとする流れが見えます"

        routes.append(
            {
                "title": f"{context_label}でよく通るルート",
                "steps": [
                    {"label": "場面", "text": f"{context_label}に触れる"},
                    {"label": "役割スイッチ", "text": role_label},
                    {"label": "選びやすい行動", "text": action_label},
                    {"label": "起こりやすい結果", "text": result_text},
                ],
            }
        )
    return routes


def _world_role_by_target(rows: List[Any]) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Any]]:
    by_target: Dict[str, Dict[str, Any]] = {}
    global_best: Dict[str, Any] = {}
    for row in rows:
        d = _as_dict(row)
        if not d:
            continue
        key = _target_key(d)
        score = _coerce_float(d.get("score"))
        if key:
            prev = by_target.get(key)
            if prev is None or score > _coerce_float(prev.get("score")):
                by_target[key] = d
        elif not global_best or score > _coerce_float(global_best.get("score")):
            global_best = d
    return by_target, global_best


def _role_obj(label: Any, key: Any = None) -> Dict[str, Any]:
    out_label = _clean(label) or _fallback_role_label(_clean(key))
    return {"key": _clean(key) or out_label, "label": out_label or "役割"}


def build_crossroads(basis: Dict[str, Any]) -> List[Dict[str, Any]]:
    basis = _as_dict(basis)
    target_lookup = _target_lookup_from_basis(basis)
    self_by_target, self_global = _world_role_by_target(_as_list(basis.get("self_world_roles")))
    real_by_target, real_global = _world_role_by_target(_as_list(basis.get("real_world_roles")))
    desired_by_target, desired_global = _world_role_by_target(_as_list(basis.get("desired_roles")))

    out: List[Dict[str, Any]] = []
    for gap in _as_list(basis.get("role_gaps"))[:5]:
        g = _as_dict(gap)
        if not g:
            continue
        key = _target_key(g)
        ctx = _context_from_row(g, target_lookup)
        self_row = self_by_target.get(key) or self_global or {}
        real_row = real_by_target.get(key) or real_global or {}
        desired_row = desired_by_target.get(key) or desired_global or {}

        self_label = _role_label(self_row) or _first_text(g.get("self_role_label_ja"), g.get("left_role_label_ja"), "こうありたい自分")
        observed_label = _role_label(real_row) or _first_text(g.get("observed_role_label_ja"), g.get("right_role_label_ja"), _role_label(g), "実際に出やすい役割")
        desired_label = _role_label(desired_row) or _first_text(g.get("desired_role_label_ja"), "余白を持って関わる役割")
        note = _first_text(g.get("note"))
        if not note:
            note = f"{ctx.get('label') or 'この場面'}では、思っている役割と実際に出やすい役割の間に分かれ道が見えます。"

        out.append(
            {
                "context": ctx,
                "self_role": _role_obj(self_label),
                "observed_role": _role_obj(observed_label),
                "desired_role": _role_obj(desired_label),
                "note": note,
            }
        )
    return out


def build_unknown_areas(basis: Dict[str, Any]) -> List[Dict[str, Any]]:
    basis = _as_dict(basis)
    target_lookup = _target_lookup_from_basis(basis)
    out: List[Dict[str, Any]] = []
    for row in _as_list(basis.get("question_candidates"))[:4]:
        d = _as_dict(row)
        if not d:
            continue
        ctx = _context_from_row(d, target_lookup)
        label = _first_text(ctx.get("label"), UNKNOWN_KIND_LABELS.get(_clean(d.get("kind"))), "まだ地図にない場所")
        reason = _first_text(d.get("reason"), "入力がまだ少なく、役割を言い切らない状態です。")
        hint = _first_text(d.get("hint"), f"次に{label}について入力すると、地図が見えやすくなります。")
        out.append({"label": label, "reason": reason, "next_observation_hint": hint})

    if not out and not _role_switch_rows_from_basis(basis):
        out.append(
            {
                "label": "まだ地図にない場所",
                "reason": "入力がまだ少なく、場面ごとの役割を言い切らない状態です。",
                "next_observation_hint": "次に相手や場所との関わりを入力すると、地図が見えやすくなります。",
            }
        )
    return out


def build_watashi_map(
    content_basis: Optional[Dict[str, Any]] = None,
    *,
    report_mode: Any = "standard",
    viewer_tier: Any = None,
    period_label: Optional[str] = None,
    period: Optional[str] = None,
    sections: Optional[Dict[str, Any]] = None,
    detail_report_text: Optional[str] = None,
) -> Dict[str, Any]:
    root = _as_dict(content_basis)
    basis = _as_dict(root.get("basis")) or root
    if sections is None and isinstance(root.get("sections"), dict):
        sections = _as_dict(root.get("sections"))
    if period is None and root.get("period"):
        period = _clean(root.get("period"))
    if period_label is None and root.get("period_label"):
        period_label = _clean(root.get("period_label"))
    mode = normalize_report_mode(report_mode or root.get("report_mode") or basis.get("report_mode"))
    tier = normalize_viewer_tier(viewer_tier, report_mode=mode)
    visibility = build_watashi_visibility(mode, tier)
    period_label_value = _period_label_from_period(period_label or period or "28d")

    all_role_switches = build_role_switches(basis)
    role_limit = 2 if visibility.get("viewer_tier") == "free" or mode == "light" else None
    role_switches = all_role_switches[:role_limit] if role_limit is not None else all_role_switches
    overview = build_watashi_map_overview(basis, sections=sections, role_switches=all_role_switches)
    routes = build_route_patterns(basis, all_role_switches) if visibility.get("routes_visible") else []
    crossroads = build_crossroads(basis) if visibility.get("crossroads_visible") else []
    unknown_areas = build_unknown_areas(basis)

    has_observation = bool(
        _clean(overview.get("summary"))
        or role_switches
        or routes
        or crossroads
    )

    payload: Dict[str, Any] = {
        "version": WATASHI_MAP_VERSION,
        "status": "ok" if has_observation else "not_enough_observation",
        "label": WATASHI_MAP_LABEL,
        "period_label": period_label_value,
        "report_mode": mode,
        "visibility": visibility,
        "overview": overview,
        "role_switches": role_switches,
        "routes": routes,
        "crossroads": crossroads,
        "unknown_areas": unknown_areas,
        "detail_report": {
            "title": DETAIL_REPORT_TITLE,
            "visible": bool(visibility.get("detail_report_visible")),
            "source": "content_text",
            "text": str(detail_report_text or "").strip() or None if visibility.get("detail_report_visible") else None,
            "lock_label": None if visibility.get("detail_report_visible") else DETAIL_REPORT_LOCK_LABEL,
        },
    }

    if not has_observation:
        payload["empty_title"] = NOT_ENOUGH_TITLE
        payload["empty_body"] = NOT_ENOUGH_BODY
        payload["empty_action_label"] = NOT_ENOUGH_ACTION
        payload["overview"] = {
            "title": WATASHI_MAP_OVERVIEW_TITLE,
            "summary": None,
            "active_contexts": [],
            "active_roles": [],
            "action_tendencies": [],
            "observation_amount": {"level": "low", "label": "まだ少なめです"},
        }

    return payload


def build_not_enough_watashi_map(
    *,
    report_mode: Any = "light",
    viewer_tier: Any = "free",
    period_label: Optional[str] = None,
) -> Dict[str, Any]:
    return build_watashi_map(
        {},
        report_mode=report_mode,
        viewer_tier=viewer_tier,
        period_label=period_label,
    )


def _project_existing_watashi_map_for_viewer(existing: Dict[str, Any], *, report_mode: Any, viewer_tier: Any) -> Dict[str, Any]:
    mode = normalize_report_mode(report_mode or existing.get("report_mode"))
    tier = normalize_viewer_tier(viewer_tier, report_mode=mode)
    visibility = build_watashi_visibility(mode, tier)
    out = deepcopy(existing)
    out["version"] = _clean(out.get("version")) or WATASHI_MAP_VERSION
    out["label"] = _clean(out.get("label")) or WATASHI_MAP_LABEL
    out["report_mode"] = mode
    out["visibility"] = visibility
    if tier == "free" or mode == "light":
        out["role_switches"] = _as_list(out.get("role_switches"))[:2]
        out["routes"] = []
        out["crossroads"] = []
        detail = _as_dict(out.get("detail_report"))
        detail.update({"visible": False, "text": None, "lock_label": DETAIL_REPORT_LOCK_LABEL})
        out["detail_report"] = detail or {"title": DETAIL_REPORT_TITLE, "visible": False, "lock_label": DETAIL_REPORT_LOCK_LABEL}
    return out


def build_watashi_map_from_content_json(
    content_json: Optional[Dict[str, Any]],
    *,
    content_text: Optional[str] = None,
    report_mode: Any = "light",
    viewer_tier: Any = "free",
    period_label: Optional[str] = None,
) -> Dict[str, Any]:
    cj = _as_dict(content_json)
    existing = cj.get("watashiMap")
    if isinstance(existing, dict) and existing:
        return _project_existing_watashi_map_for_viewer(existing, report_mode=report_mode, viewer_tier=viewer_tier)

    distribution = _as_dict(cj.get("distribution"))
    sections = _as_dict(cj.get("sections"))
    summary = _clean(cj.get("summaryText"))
    if not summary:
        current = sections.get("current_structure")
        if isinstance(current, list):
            summary = _first_text(current)
    if not summary and content_text:
        for line in str(content_text or "").splitlines():
            s = _clean(line)
            if s and not (s.startswith("【") and s.endswith("】")):
                summary = s
                break

    if summary:
        basis = {
            "report_mode": normalize_report_mode(report_mode),
            "core_target": {"target_key": "observed", "target_label_ja": "見えている場面", "target_type": "environment"},
            "core_role": {"role_key": "observed", "role_label_ja": "見えている役割"},
        }
        payload = build_watashi_map(
            basis,
            report_mode=report_mode,
            viewer_tier=viewer_tier,
            period_label=period_label or _period_label_from_period(distribution.get("period") or cj.get("period") or "28d"),
            sections={"current_structure": [summary]},
        )
        payload["overview"]["summary"] = summary
        return payload

    return build_not_enough_watashi_map(
        report_mode=report_mode,
        viewer_tier=viewer_tier,
        period_label=period_label or _period_label_from_period(distribution.get("period") or cj.get("period") or "28d"),
    )


def adapt_self_structure_deep_visual_to_watashi_map(
    visual: Optional[Dict[str, Any]],
    *,
    report_mode: Any = "deep",
    viewer_tier: Any = "premium",
    period_label: Optional[str] = None,
) -> Dict[str, Any]:
    v = _as_dict(visual)
    if not v:
        return build_not_enough_watashi_map(report_mode=report_mode, viewer_tier=viewer_tier, period_label=period_label)

    summary_card = _as_dict(v.get("summaryCard"))
    role_map = _as_dict(v.get("roleSwitchMap"))
    behavior_cards = _as_list(v.get("behaviorCards"))
    role_gap_cards = _as_list(v.get("roleGapCards"))
    unknown_area = _as_dict(v.get("unknownArea"))

    role_switches: List[Dict[str, Any]] = []
    role_switch_rows = (
        _as_list(role_map.get("dominant_by_target"))
        or _as_list(role_map.get("items"))
        or _as_list(role_map.get("cells"))
    )
    for row in role_switch_rows:
        d = _as_dict(row)
        if not d:
            continue
        ctx = {"key": _target_key(d) or "overall", "label": _target_label(d) or "全体", "kind": _target_kind(d)}
        role = {"key": _role_key(d) or _role_label(d), "label": _role_label(d) or "役割"}
        role_switches.append(
            {
                "context": ctx,
                "role": role,
                "tendency_label": "立ち上がりやすい",
                "score_display": _score_display(d.get("score"), d.get("evidence_count")),
                "evidence_count": _coerce_int(d.get("evidence_count"), 0) or None,
                "route_preview": _route_preview(ctx["label"], role["label"], "行動を選ぶ"),
                "safe_note": SAFE_NOTE,
            }
        )

    overview = {
        "title": WATASHI_MAP_OVERVIEW_TITLE,
        "summary": _first_text(summary_card.get("headline"), summary_card.get("summary"), summary_card.get("text"), summary_card.get("title")) or None,
        "active_contexts": [],
        "active_roles": [],
        "action_tendencies": [],
        "observation_amount": _observation_amount(role_switches, {}),
    }
    for item in role_switches[:3]:
        ctx = _as_dict(item.get("context"))
        role = _as_dict(item.get("role"))
        if _clean(ctx.get("label")):
            overview["active_contexts"].append({"key": _clean(ctx.get("key")), "label": _clean(ctx.get("label")), "share_label": "よく見えています"})
        if _clean(role.get("label")):
            overview["active_roles"].append({"key": _clean(role.get("key")), "label": _clean(role.get("label"))})

    routes: List[Dict[str, Any]] = []
    for card in behavior_cards[:4]:
        c = _as_dict(card)
        ctx_label = _target_label(c) or "場面"
        role_label = _first_text(c.get("template_role_label_ja"), c.get("generated_role_description"), "役割")
        action_texts = [_clean(x.get("label_ja")) for x in _as_list(c.get("actions")) if isinstance(x, dict)]
        action_label = _first_text(action_texts, "行動を選ぶ")
        routes.append(
            {
                "title": f"{ctx_label}でよく通るルート",
                "steps": [
                    {"label": "場面", "text": f"{ctx_label}に触れる"},
                    {"label": "役割スイッチ", "text": role_label},
                    {"label": "選びやすい行動", "text": action_label},
                    {"label": "起こりやすい結果", "text": "その場で見えた動き方が表れやすくなります"},
                ],
            }
        )

    crossroads: List[Dict[str, Any]] = []
    for card in role_gap_cards[:4]:
        c = _as_dict(card)
        ctx = {"key": _target_key(c) or "overall", "label": _target_label(c) or "全体", "kind": _target_kind(c)}
        crossroads.append(
            {
                "context": ctx,
                "self_role": _role_obj(_clean(_as_dict(c.get("self_role")).get("role_label_ja")) or "自己認識の役割"),
                "observed_role": _role_obj(_clean(_as_dict(c.get("real_role")).get("role_label_ja")) or "実際に出やすい役割"),
                "desired_role": _role_obj(_clean(_as_dict(c.get("desired_role")).get("role_label_ja")) or "理想の役割"),
                "note": _clean(_as_dict(c.get("primary_gap")).get("note")) or "自己認識・実際・理想の間に分かれ道が見えます。",
            }
        )

    unknown_areas = []
    for item in _as_list(unknown_area.get("items"))[:4]:
        d = _as_dict(item)
        label = _target_label(d) or _clean(d.get("kind_label_ja")) or "まだ地図にない場所"
        unknown_areas.append(
            {
                "label": label,
                "reason": _clean(d.get("reason")) or "観測がまだ少ない場所です。",
                "next_observation_hint": _clean(d.get("hint")) or f"次に{label}を入力すると、地図が見えやすくなります。",
            }
        )

    mode = normalize_report_mode(report_mode)
    tier = normalize_viewer_tier(viewer_tier, report_mode=mode)
    visibility = build_watashi_visibility(mode, tier)
    return {
        "version": WATASHI_MAP_VERSION,
        "status": "ok" if overview.get("summary") or role_switches else "not_enough_observation",
        "label": WATASHI_MAP_LABEL,
        "period_label": _clean(period_label) or "直近 28 日",
        "report_mode": mode,
        "visibility": visibility,
        "overview": overview,
        "role_switches": role_switches[:2] if tier == "free" else role_switches,
        "routes": [] if not visibility.get("routes_visible") else routes,
        "crossroads": [] if not visibility.get("crossroads_visible") else crossroads,
        "unknown_areas": unknown_areas,
        "detail_report": {
            "title": DETAIL_REPORT_TITLE,
            "visible": bool(visibility.get("detail_report_visible")),
            "source": "content_text",
            "text": None,
            "lock_label": None if visibility.get("detail_report_visible") else DETAIL_REPORT_LOCK_LABEL,
        },
    }


def period_label_from_period(period: Any) -> str:
    """Public wrapper used by report builders."""

    return _period_label_from_period(period)


def project_watashi_map_for_viewer(
    existing: Dict[str, Any],
    *,
    report_mode: Any = "light",
    viewer_tier: Any = "free",
) -> Dict[str, Any]:
    """Return a viewer-safe projection of an existing watashiMap payload."""

    return _project_existing_watashi_map_for_viewer(
        existing,
        report_mode=report_mode,
        viewer_tier=viewer_tier,
    )


def project_watashi_map_for_light(
    source_map: Optional[Dict[str, Any]] = None,
    *,
    summary_text: Optional[str] = None,
    period_label: Optional[str] = None,
) -> Dict[str, Any]:
    """Return a Free-safe light watashiMap projection.

    Used by /self-structure/latest when a saved standard/deep row satisfies a
    Free light read at response time.
    """

    if isinstance(source_map, dict) and source_map:
        out = project_watashi_map_for_viewer(source_map, report_mode="light", viewer_tier="free")
        if period_label:
            out["period_label"] = period_label
        if summary_text:
            overview = _as_dict(out.get("overview"))
            overview["summary"] = str(summary_text or "").strip()
            out["overview"] = overview
            out["status"] = "ok"
        return out

    payload = build_watashi_map_from_content_json(
        {
            "summaryText": str(summary_text or "").strip() or None,
            "distribution": {"period": period_label or "28d"},
        },
        report_mode="light",
        viewer_tier="free",
        period_label=period_label,
    )
    if summary_text:
        overview = _as_dict(payload.get("overview"))
        overview["summary"] = str(summary_text or "").strip()
        payload["overview"] = overview
        payload["status"] = "ok"
    return payload


__all__ = [
    "WATASHI_MAP_VERSION",
    "build_watashi_map",
    "build_watashi_map_from_content_json",
    "build_watashi_map_overview",
    "build_role_switches",
    "build_route_patterns",
    "build_crossroads",
    "build_unknown_areas",
    "build_watashi_visibility",
    "adapt_self_structure_deep_visual_to_watashi_map",
    "build_not_enough_watashi_map",
    "period_label_from_period",
    "project_watashi_map_for_light",
    "project_watashi_map_for_viewer",
    "normalize_report_mode",
    "normalize_viewer_tier",
]
