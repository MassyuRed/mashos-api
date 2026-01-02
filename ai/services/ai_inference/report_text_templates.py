# -*- coding: utf-8 -*-
"""report_text_templates.py (Phase9)

目的
----
- MyWeb / MyProfile の「本文（content_text）」をサーバ側テンプレIDで切り替え可能にする。
- アプリ（JS）は表示だけに徹し、文面調整は MashOS 側の更新・ENV切替で回せるようにする。

位置づけ
--------
- prompt_templates.py: LLM向け instruction（/mymodel/infer で使用）
- ui_text_templates.py: DeepInsight質問文などのUIテキスト
- 本ファイル: レポート本文（content_text）のレンダリング

注意
----
- ここは LLM への instruction ではない（/mymodel/infer のガード対象外）。
- テンプレは「本文の見せ方」を変えるためのもの。データ生成（metrics算出など）には影響しない。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional


class ReportTextTemplateError(ValueError):
    """Report text template rendering error."""


@dataclass(frozen=True)
class ReportTextTemplateInfo:
    template_id: str
    description: str
    required_vars: List[str]
    optional_vars: List[str]


# JST fixed
_JST = timezone(timedelta(hours=9))


# Emotion mapping (server-side MyWeb uses these keys)
_EMOTION_KEYS: List[str] = ["joy", "sadness", "anxiety", "anger", "calm"]
_KEY_TO_JP: Dict[str, str] = {
    "joy": "喜び",
    "sadness": "悲しみ",
    "anxiety": "不安",
    "anger": "怒り",
    "calm": "平穏",
}


_TEMPLATES: Dict[str, ReportTextTemplateInfo] = {
    # --- MyWeb report body ---
    "myweb_report_text_ja_v1": ReportTextTemplateInfo(
        template_id="myweb_report_text_ja_v1",
        description="MyWeb本文（従来互換の詳細版）",
        required_vars=[
            "report_type",
            "title",
            "period_start_iso",
            "period_end_iso",
            "metrics",
        ],
        optional_vars=["astor_text"],
    ),
    "myweb_report_text_ja_compact_v1": ReportTextTemplateInfo(
        template_id="myweb_report_text_ja_compact_v1",
        description="MyWeb本文（短め）",
        required_vars=[
            "report_type",
            "title",
            "period_start_iso",
            "period_end_iso",
            "metrics",
        ],
        optional_vars=["astor_text"],
    ),

    # --- MyProfile report body (wrapper) ---
    "myprofile_report_text_passthrough_v1": ReportTextTemplateInfo(
        template_id="myprofile_report_text_passthrough_v1",
        description="MyProfile本文（そのまま返す）",
        required_vars=["raw_text"],
        optional_vars=["title", "range_label"],
    ),
    "myprofile_report_text_wrap_ja_v1": ReportTextTemplateInfo(
        template_id="myprofile_report_text_wrap_ja_v1",
        description="MyProfile本文（先頭ヘッダだけ整形して包む。内部本文は維持）",
        required_vars=["raw_text"],
        optional_vars=["title", "range_label"],
    ),
}


def list_report_text_templates() -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for tid, info in sorted(_TEMPLATES.items(), key=lambda kv: kv[0]):
        out.append(
            {
                "template_id": info.template_id,
                "description": info.description,
                "required_vars": list(info.required_vars),
                "optional_vars": list(info.optional_vars),
            }
        )
    return out


def _parse_iso_to_dt_utc(iso_z: str) -> Optional[datetime]:
    s = str(iso_z or "").strip()
    if not s:
        return None
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _format_range_jst(period_start_iso: str, period_end_iso: str) -> Optional[str]:
    s_dt = _parse_iso_to_dt_utc(period_start_iso)
    e_dt = _parse_iso_to_dt_utc(period_end_iso)
    if not s_dt or not e_dt:
        return None
    s = s_dt.astimezone(_JST)
    e = e_dt.astimezone(_JST)
    # period_end is inclusive (23:59:59.999) in design; show as 23:59
    return f"対象期間（JST）: {s.year}/{s.month}/{s.day} 00:00 〜 {e.year}/{e.month}/{e.day} 23:59"


def _dominant_label(metrics: Dict[str, Any]) -> str:
    try:
        dom = metrics.get("dominantKey") or None
        if dom:
            return _KEY_TO_JP.get(str(dom), str(dom))
    except Exception:
        pass

    totals = metrics.get("totals") if isinstance(metrics, dict) else None
    if isinstance(totals, dict):
        best_k: Optional[str] = None
        best_v = 0
        for k in _EMOTION_KEYS:
            try:
                v = int(totals.get(k, 0))
            except Exception:
                v = 0
            if v > best_v:
                best_v = v
                best_k = k
        if best_k and best_v > 0:
            return _KEY_TO_JP.get(best_k, best_k)
    return "—"


def render_myweb_report_text(
    template_id: str,
    *,
    report_type: str,
    title: str,
    period_start_iso: str,
    period_end_iso: str,
    metrics: Dict[str, Any],
    astor_text: Optional[str] = None,
    lang: str = "ja",
) -> str:
    """Render MyWeb report body text (content_text)."""

    tid = str(template_id or "").strip() or "myweb_report_text_ja_v1"
    rt = str(report_type or "").strip().lower()
    if rt not in ("daily", "weekly", "monthly"):
        rt = "daily"

    vars_: Dict[str, Any] = {
        "report_type": rt,
        "title": str(title or "").strip(),
        "period_start_iso": str(period_start_iso or "").strip(),
        "period_end_iso": str(period_end_iso or "").strip(),
        "metrics": metrics or {},
        "astor_text": (str(astor_text).strip() if astor_text else None),
        "lang": str(lang or "ja").strip().lower() or "ja",
    }

    try:
        if tid == "myweb_report_text_ja_compact_v1":
            return _tpl_myweb_report_text_ja_compact_v1(vars_)
        # default
        return _tpl_myweb_report_text_ja_v1(vars_)
    except Exception:
        # fail-safe
        try:
            return _tpl_myweb_report_text_ja_v1(vars_)
        except Exception:
            return str(title or "").strip()


def _tpl_myweb_report_text_ja_v1(vars_: Dict[str, Any]) -> str:
    title = str(vars_.get("title") or "").strip()
    ps = str(vars_.get("period_start_iso") or "").strip()
    pe = str(vars_.get("period_end_iso") or "").strip()
    metrics = vars_.get("metrics") or {}
    astor_text = str(vars_.get("astor_text") or "").strip() or None

    lines: List[str] = []
    if title:
        lines.append(title)
        lines.append("")

    range_line = _format_range_jst(ps, pe)
    if range_line:
        lines.append(range_line)
        lines.append("")

    lines.append("【感情の重み付け合計】")
    totals = metrics.get("totals") if isinstance(metrics, dict) else None
    totals = totals if isinstance(totals, dict) else {}
    for k in _EMOTION_KEYS:
        try:
            v = int(totals.get(k, 0))
        except Exception:
            v = 0
        lines.append(f"- {_KEY_TO_JP.get(k, k)}: {v}")

    lines.append("")
    lines.append(f"中心に出ている傾向: {_dominant_label(metrics if isinstance(metrics, dict) else {})}")

    if astor_text:
        lines.append("")
        lines.append("【ASTOR 構造洞察（補足）】")
        lines.append(astor_text)

    return "\n".join(lines).strip()


def _tpl_myweb_report_text_ja_compact_v1(vars_: Dict[str, Any]) -> str:
    title = str(vars_.get("title") or "").strip()
    ps = str(vars_.get("period_start_iso") or "").strip()
    pe = str(vars_.get("period_end_iso") or "").strip()
    metrics = vars_.get("metrics") or {}
    astor_text = str(vars_.get("astor_text") or "").strip() or None

    totals = metrics.get("totals") if isinstance(metrics, dict) else None
    totals = totals if isinstance(totals, dict) else {}

    # 1行サマリ
    parts: List[str] = []
    parts.append(f"傾向: {_dominant_label(metrics if isinstance(metrics, dict) else {})}")
    # 例: 合計: 喜10 悲2 不安0 ...
    sums = []
    for k in _EMOTION_KEYS:
        try:
            v = int(totals.get(k, 0))
        except Exception:
            v = 0
        jp = _KEY_TO_JP.get(k, k)
        sums.append(f"{jp}{v}")
    parts.append("合計: " + " ".join(sums))

    lines: List[str] = []
    if title:
        lines.append(title)
    range_line = _format_range_jst(ps, pe)
    if range_line:
        lines.append(range_line)
    lines.append(" / ".join(parts))

    if astor_text:
        # compact: 1行だけ添える
        short = astor_text.replace("\n", " ").strip()
        if len(short) > 120:
            short = short[:120] + "…"
        lines.append(f"ASTOR: {short}")

    return "\n".join([x for x in lines if str(x or "").strip()]).strip()


def apply_myprofile_report_text_template(
    template_id: str,
    *,
    raw_text: str,
    title: Optional[str] = None,
    range_label: Optional[str] = None,
    lang: str = "ja",
) -> str:
    """Apply a text template to MyProfile report body.

    現段階（Phase9）では、ASTORが生成した本文（raw_text）を「包む」程度に留め、
    大規模な本文構造の変更はしない（互換性を優先）。
    """

    tid = str(template_id or "").strip() or "myprofile_report_text_passthrough_v1"
    text = str(raw_text or "").strip()
    if not text:
        return ""

    if tid == "myprofile_report_text_passthrough_v1":
        return text

    if tid == "myprofile_report_text_wrap_ja_v1":
        # 先頭の見出しだけ整えて包む（内部の章立ては raw_text のまま）
        # 例: ASTORは先頭に "【自己構造分析レポート（月次）】" を付けるので、二重を避ける
        body_lines = text.splitlines()
        # drop leading empty
        while body_lines and not str(body_lines[0]).strip():
            body_lines.pop(0)
        if body_lines and str(body_lines[0]).strip().startswith("【自己構造分析レポート"):
            body_lines.pop(0)
            while body_lines and not str(body_lines[0]).strip():
                body_lines.pop(0)

        header = "【自己構造分析レポート】"
        if title and "月次" in str(title):
            header = "【自己構造分析レポート（月次）】"
        elif title and "最新版" in str(title):
            header = "【自己構造レポート（最新版）】"

        lines: List[str] = []
        lines.append(header)
        if title:
            # title はUI用なので軽く添える
            lines.append(f"{str(title).strip()}")
        if range_label:
            lines.append(f"期間: {str(range_label).strip()}")
        lines.append("")
        lines.extend(body_lines)
        return "\n".join(lines).strip()

    # unknown template -> passthrough
    return text
