# -*- coding: utf-8 -*-
"""piece_text_formatter.py

Deterministic formatter for MyModel Create -> Reflections public display text.

Goals
- keep raw authoring text intact
- apply only light, deterministic cleanup for public display
- mask high-confidence PII and a small set of explicit abusive expressions
- block only clearly unsafe / severe cases (threats, doxxing-like disclosure)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import re
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

REFLECTION_DISPLAY_VERSION = "reflection.display.v1"
STATE_READY = "ready"
STATE_MASKED = "masked"
STATE_BLOCKED = "blocked"
_VALID_STATES = {STATE_READY, STATE_MASKED, STATE_BLOCKED}

_ZERO_WIDTH_RE = re.compile(r"[\u200B-\u200D\uFEFF]")
_TRAILING_SPACE_RE = re.compile(r"[ \t\u3000]+\n")
_BLANK_LINES_RE = re.compile(r"\n[\t \u3000]*\n(?:[\t \u3000]*\n)+")

_EMAIL_RE = re.compile(r"(?i)\b[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}\b")
_URL_RE = re.compile(r"(?i)\b(?:https?://|www\.)[^\s<>()]+")
_PHONE_RE = re.compile(r"(?<!\d)(?:\+?81[-\s]?)?0\d{1,4}[-\s]?\d{1,4}[-\s]?\d{3,4}(?!\d)")
_POSTAL_RE = re.compile(r"(?<!\d)(?:〒\s*)?\d{3}-\d{4}(?!\d)")
_HANDLE_RE = re.compile(r"(?<![\w@])@[A-Za-z0-9_](?:[A-Za-z0-9_.-]{1,31})")
_LINE_ID_RE = re.compile(
    r"(?i)((?:line|ライン)\s*(?:id|アイディー)?\s*[:：]\s*)([A-Za-z0-9][A-Za-z0-9_.-]{2,31})"
)
_ADDRESS_LABEL_RE = re.compile(r"((?:住所|住まい|住居)\s*[:：]\s*)([^\n]{6,100})")

_SEVERE_BLOCK_PATTERNS: Sequence[Tuple[str, re.Pattern[str]]] = (
    ("abuse:threat", re.compile(r"(?:ぶっ?殺|殺してやる|死ね|刺してやる|殴ってやる|痛い目に遭わせ)")),
    ("abuse:doxxing", re.compile(r"(?:住所|本名|電話番号|連絡先|学校|勤務先).{0,10}(?:晒|公開|特定)")),
    ("privacy:doxxing", re.compile(r"(?:個人情報).{0,8}(?:晒|公開|流す|拡散)")),
)

_ABUSE_MASK_PATTERNS: Sequence[Tuple[str, re.Pattern[str], str]] = (
    ("abuse:slur", re.compile(r"人間のクズ"), "[不適切表現]"),
    ("abuse:slur", re.compile(r"ゴミ人間"), "[不適切表現]"),
    ("abuse:slur", re.compile(r"クソ野郎"), "[不適切表現]"),
    ("abuse:slur", re.compile(r"最低なやつ"), "[不適切表現]"),
)


@dataclass(frozen=True)
class ReflectionDisplayResult:
    raw_text: str
    normalized_text: str
    display_text: Optional[str]
    display_state: str
    changed: bool
    flags: List[str]
    actions: List[str]
    version: str = REFLECTION_DISPLAY_VERSION

    def as_storage_meta(self) -> Dict[str, Any]:
        display_text = str(self.display_text or "")
        return {
            "version": str(self.version),
            "changed": bool(self.changed),
            "flags": list(self.flags),
            "actions": list(self.actions),
            "raw_length": int(len(self.raw_text)),
            "normalized_length": int(len(self.normalized_text)),
            "display_length": int(len(display_text)),
            "display_state": str(self.display_state),
            "masked_count": int(sum(1 for action in self.actions if str(action).startswith("mask:"))),
            "blocked": bool(self.display_state == STATE_BLOCKED),
        }


def _ordered_unique(values: Sequence[str]) -> List[str]:
    out: List[str] = []
    seen = set()
    for value in values or []:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


def _append_once(values: List[str], value: str) -> None:
    text = str(value or "").strip()
    if text and text not in values:
        values.append(text)


def _parse_meta(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
            if isinstance(parsed, dict):
                return dict(parsed)
        except Exception:
            return {}
    return {}


def _parse_iso(value: Any) -> Optional[datetime]:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return None


def _compress_repeated_punctuation(text: str, actions: List[str]) -> str:
    before = text
    text = re.sub(r"([!！])(?:[!！]{2,})", lambda m: m.group(1) * 2, text)
    text = re.sub(r"([?？])(?:[?？]{2,})", lambda m: m.group(1) * 2, text)
    text = re.sub(r"([。])(?:[。]{1,})", lambda m: m.group(1), text)
    text = re.sub(r"([…])(?:[…]{2,})", lambda m: m.group(1) * 2, text)
    if text != before:
        _append_once(actions, "normalize:punctuation_runs")
    return text


def _soft_sentence_breaks(text: str, actions: List[str]) -> str:
    if "\n" in text or len(text) < 80:
        return text
    parts = re.split(r"([。！？!?])", text)
    if len(parts) < 4:
        return text

    out: List[str] = []
    line_len = 0
    sentence_count = 0
    inserted = False
    for idx in range(0, len(parts), 2):
        frag = parts[idx]
        punct = parts[idx + 1] if idx + 1 < len(parts) else ""
        seg = f"{frag}{punct}"
        if not seg:
            continue
        out.append(seg)
        line_len += len(seg)
        if punct:
            sentence_count += 1
            remaining = "".join(parts[idx + 2 :]).strip()
            if remaining and (sentence_count >= 2 or line_len >= 42):
                out.append("\n")
                line_len = 0
                sentence_count = 0
                inserted = True
    new_text = "".join(out)
    new_text = _BLANK_LINES_RE.sub("\n\n", new_text)
    if inserted and new_text != text:
        _append_once(actions, "format:sentence_breaks")
    return new_text


def _normalize_text(raw_text: Any) -> Tuple[str, List[str]]:
    text = str(raw_text or "")
    actions: List[str] = []

    cleaned = _ZERO_WIDTH_RE.sub("", text)
    if cleaned != text:
        _append_once(actions, "normalize:zero_width")
        text = cleaned

    newline_text = text.replace("\r\n", "\n").replace("\r", "\n")
    if newline_text != text:
        _append_once(actions, "normalize:newlines")
        text = newline_text

    trailing_trimmed = _TRAILING_SPACE_RE.sub("\n", text)
    if trailing_trimmed != text:
        _append_once(actions, "normalize:line_trailing_spaces")
        text = trailing_trimmed

    stripped = text.strip()
    if stripped != text:
        _append_once(actions, "normalize:trim")
        text = stripped

    collapsed_blank_lines = _BLANK_LINES_RE.sub("\n\n", text)
    if collapsed_blank_lines != text:
        _append_once(actions, "normalize:blank_lines")
        text = collapsed_blank_lines

    text = _compress_repeated_punctuation(text, actions)
    text = _soft_sentence_breaks(text, actions)
    return text, actions


def _mask_phone_match(match: re.Match[str]) -> str:
    raw = match.group(0)
    digits = re.sub(r"\D", "", raw)
    if digits.startswith("81"):
        if 10 <= len(digits) <= 12:
            return "[電話番号]"
        return raw
    if 10 <= len(digits) <= 11:
        return "[電話番号]"
    return raw


def _replace_with_token(text: str, pattern: re.Pattern[str], token: str) -> Tuple[str, int]:
    count = 0

    def _repl(_match: re.Match[str]) -> str:
        nonlocal count
        count += 1
        return token

    return pattern.sub(_repl, text), count


def _replace_line_id(text: str) -> Tuple[str, int]:
    count = 0

    def _repl(match: re.Match[str]) -> str:
        nonlocal count
        count += 1
        return f"{match.group(1)}[SNS ID]"

    return _LINE_ID_RE.sub(_repl, text), count


def _replace_address_label(text: str) -> Tuple[str, int]:
    count = 0

    def _repl(match: re.Match[str]) -> str:
        nonlocal count
        count += 1
        return f"{match.group(1)}[住所]"

    return _ADDRESS_LABEL_RE.sub(_repl, text), count


def _replace_phone(text: str) -> Tuple[str, int]:
    count = 0

    def _repl(match: re.Match[str]) -> str:
        nonlocal count
        replaced = _mask_phone_match(match)
        if replaced != match.group(0):
            count += 1
        return replaced

    return _PHONE_RE.sub(_repl, text), count


def _mask_explicit_abuse(text: str, flags: List[str], actions: List[str]) -> str:
    out = text
    for flag, pattern, token in _ABUSE_MASK_PATTERNS:
        out, count = _replace_with_token(out, pattern, token)
        if count > 0:
            _append_once(flags, flag)
            _append_once(actions, "mask:abuse")
    return out


def format_reflection_text(raw_text: Any) -> ReflectionDisplayResult:
    raw = str(raw_text or "")
    normalized, actions = _normalize_text(raw)
    flags: List[str] = []
    display = normalized

    # High-confidence PII masks.
    display, email_count = _replace_with_token(display, _EMAIL_RE, "[メールアドレス]")
    if email_count > 0:
        _append_once(flags, "pii:email")
        _append_once(actions, "mask:email")

    display, url_count = _replace_with_token(display, _URL_RE, "[URL]")
    if url_count > 0:
        _append_once(flags, "pii:url")
        _append_once(actions, "mask:url")

    display, phone_count = _replace_phone(display)
    if phone_count > 0:
        _append_once(flags, "pii:phone")
        _append_once(actions, "mask:phone")

    display, postal_count = _replace_with_token(display, _POSTAL_RE, "[郵便番号]")
    if postal_count > 0:
        _append_once(flags, "pii:postal")
        _append_once(actions, "mask:postal")

    display, line_count = _replace_line_id(display)
    if line_count > 0:
        _append_once(flags, "pii:line_id")
        _append_once(actions, "mask:line_id")

    display, handle_count = _replace_with_token(display, _HANDLE_RE, "@[SNS ID]")
    if handle_count > 0:
        _append_once(flags, "pii:handle")
        _append_once(actions, "mask:handle")

    display, address_count = _replace_address_label(display)
    if address_count > 0:
        _append_once(flags, "pii:address")
        _append_once(actions, "mask:address")

    display = _mask_explicit_abuse(display, flags, actions)

    severe_flags: List[str] = []
    for flag, pattern in _SEVERE_BLOCK_PATTERNS:
        if pattern.search(normalized):
            _append_once(severe_flags, flag)

    pii_flags = {flag for flag in flags if flag.startswith("pii:")}
    if "pii:address" in pii_flags and len(pii_flags) >= 2:
        _append_once(severe_flags, "privacy:address_plus_contact")

    if severe_flags:
        flags = _ordered_unique([*flags, *severe_flags])
        actions = _ordered_unique([*actions, "block:severe"])
        changed = bool((normalized != raw) or actions)
        return ReflectionDisplayResult(
            raw_text=raw,
            normalized_text=normalized,
            display_text=None,
            display_state=STATE_BLOCKED,
            changed=changed,
            flags=flags,
            actions=actions,
        )

    display_state = STATE_MASKED if any(action.startswith("mask:") for action in actions) else STATE_READY
    changed = bool((normalized != raw) or (display != normalized) or actions)
    return ReflectionDisplayResult(
        raw_text=raw,
        normalized_text=normalized,
        display_text=display,
        display_state=display_state,
        changed=changed,
        flags=_ordered_unique(flags),
        actions=_ordered_unique(actions),
    )


def apply_reflection_storage_fields(
    row: Mapping[str, Any],
    *,
    raw_text: Any,
    display_updated_at: Optional[str],
) -> Tuple[Dict[str, Any], ReflectionDisplayResult]:
    result = format_reflection_text(raw_text)
    updated: Dict[str, Any] = dict(row or {})
    updated["reflection_display_text"] = result.display_text
    updated["reflection_display_state"] = result.display_state
    updated["reflection_format_version"] = result.version
    updated["reflection_format_meta"] = result.as_storage_meta()
    if display_updated_at:
        updated["reflection_display_updated_at"] = str(display_updated_at)
    return updated, result


def _stored_display_result_from_row(row: Mapping[str, Any]) -> Optional[ReflectionDisplayResult]:
    if not isinstance(row, Mapping):
        return None
    state = str(row.get("reflection_display_state") or "").strip().lower()
    if state not in _VALID_STATES:
        return None

    updated_at = _parse_iso(row.get("updated_at"))
    display_updated_at = _parse_iso(row.get("reflection_display_updated_at"))
    if updated_at and display_updated_at and display_updated_at < updated_at:
        return None

    raw = str(row.get("answer_text") or "")
    stored_text = row.get("reflection_display_text")
    if state != STATE_BLOCKED:
        stored_value = str(stored_text or "").strip()
        if not stored_value:
            return None
        display_text: Optional[str] = stored_value
    else:
        display_text = None

    meta = _parse_meta(row.get("reflection_format_meta"))
    flags = [str(x).strip() for x in (meta.get("flags") or []) if str(x).strip()]
    actions = [str(x).strip() for x in (meta.get("actions") or []) if str(x).strip()]
    changed_meta = meta.get("changed")
    changed = bool(changed_meta) if changed_meta is not None else bool(display_text != raw or state != STATE_READY)
    version = str(meta.get("version") or row.get("reflection_format_version") or REFLECTION_DISPLAY_VERSION).strip() or REFLECTION_DISPLAY_VERSION
    return ReflectionDisplayResult(
        raw_text=raw,
        normalized_text=str(meta.get("normalized_text") or raw),
        display_text=display_text,
        display_state=state,
        changed=changed,
        flags=_ordered_unique(flags),
        actions=_ordered_unique(actions),
        version=version,
    )


def resolve_create_reflection_display(row: Mapping[str, Any]) -> ReflectionDisplayResult:
    stored = _stored_display_result_from_row(row)
    if stored is not None:
        return stored
    return format_reflection_text((row or {}).get("answer_text"))


def get_public_create_reflection_text(row: Mapping[str, Any]) -> Optional[str]:
    result = resolve_create_reflection_display(row)
    if str(result.display_state) == STATE_BLOCKED:
        return None
    text = str(result.display_text or "").strip()
    return text or None


def sanitize_reflection_context_text(value: Any) -> Optional[str]:
    result = format_reflection_text(value)
    if str(result.display_state) == STATE_BLOCKED:
        return None
    text = str(result.display_text or "").strip()
    return text or None
