# -*- coding: utf-8 -*-
"""Piece generation policy for the new national core system.

This module keeps the Emotion -> Piece preview/publish contract additive.
It does not generate text and does not mutate publish-time text.  It only
classifies the already generated public-safe preview text and builds stable
metadata that can be stored with the draft and echoed by the write API.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

PIECE_CORE_SCHEMA_VERSION = "piece.core.v1"
PIECE_SOURCE_INPUT_SCOPE_CURRENT_ONLY = "current_input_only"

VISIBILITY_PREVIEW_READY = "preview_ready"
VISIBILITY_PUBLISHED = "published"
VISIBILITY_DELETED = "deleted"
VISIBILITY_SYSTEM_HIDDEN = "system_hidden"

GENERATION_GENERATED = "generated"
GENERATION_FALLBACK_GENERATED = "fallback_generated"
GENERATION_FAILED = "generation_failed"

TRANSFORM_AS_IS = "as_is"
TRANSFORM_NORMALIZED = "normalized"
TRANSFORM_ABSTRACTED = "abstracted"
TRANSFORM_LOW_INFO = "low_info"

SAFETY_SAFE = "safe"
SAFETY_NEEDS_TRANSFORM = "needs_transform"
SAFETY_HIGH_RISK_TRANSFORMED = "high_risk_transformed"
SAFETY_BLOCKED_INTERNAL = "blocked_internal"

_ZERO_WIDTH_RE = re.compile(r"[\u200B-\u200D\uFEFF]")
_WS_RE = re.compile(r"\s+")
_URL_TOKEN_RE = re.compile(r"\[URL\]|https?://|www\.", re.IGNORECASE)
_PHONE_TOKEN_RE = re.compile(r"\[電話番号\]")
_EMAIL_TOKEN_RE = re.compile(r"\[メールアドレス\]")
_ADDRESS_TOKEN_RE = re.compile(r"\[住所\]")
_SNS_TOKEN_RE = re.compile(r"\[SNS ID\]|@\[SNS ID\]")
_RAW_EMAIL_RE = re.compile(r"(?i)\b[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}\b")
_RAW_PHONE_RE = re.compile(r"(?<!\d)(?:\+?81[-\s]?)?0\d{1,4}[-\s]?\d{1,4}[-\s]?\d{3,4}(?!\d)")
_RAW_POSTAL_RE = re.compile(r"(?<!\d)(?:〒\s*)?\d{3}-\d{4}(?!\d)")
_ATTACK_TERMS = ("ムカつく", "むかつく", "腹が立", "消えてほしい", "消えろ", "死ね", "殺", "晒", "許せない", "クソ", "ゴミ")


@dataclass(frozen=True)
class PieceGenerationPolicyResult:
    visibility_status: str
    generation_status: str
    transform_mode: str
    safety_level: str
    safety_flags: List[str]
    piece_text_hash: str
    source_input_scope: str = PIECE_SOURCE_INPUT_SCOPE_CURRENT_ONLY
    schema_version: str = PIECE_CORE_SCHEMA_VERSION

    def as_storage_meta(self) -> Dict[str, Any]:
        return {
            "schema_version": str(self.schema_version),
            "core_id": "piece",
            "visibility_status": str(self.visibility_status),
            "generation_status": str(self.generation_status),
            "transform_mode": str(self.transform_mode),
            "safety_level": str(self.safety_level),
            "safety_flags": list(self.safety_flags),
            "piece_text_hash": str(self.piece_text_hash),
            "source_input_scope": str(self.source_input_scope),
            "preview_text_hash": str(self.piece_text_hash),
        }

    def as_public_contract(self, *, include_safety_flags: bool = False) -> Dict[str, Any]:
        payload = {
            "visibility_status": str(self.visibility_status),
            "generation_status": str(self.generation_status),
            "transform_mode": str(self.transform_mode),
            "safety_level": str(self.safety_level),
        }
        if include_safety_flags:
            payload["safety_flags"] = list(self.safety_flags)
        return payload


def _collapse(text: Any) -> str:
    value = _ZERO_WIDTH_RE.sub("", str(text or ""))
    return _WS_RE.sub(" ", value.replace("\r", " ").replace("\n", " ")).strip()


def _compact(text: Any) -> str:
    return _collapse(text).replace(" ", "")


def _append_once(values: List[str], value: str) -> None:
    text = str(value or "").strip()
    if text and text not in values:
        values.append(text)


def _ordered_unique(values: Iterable[Any]) -> List[str]:
    out: List[str] = []
    for value in values or []:
        _append_once(out, str(value or ""))
    return out


def compute_piece_text_hash(text: Any) -> str:
    normalized = _compact(text)
    if not normalized:
        return ""
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _extract_display_meta(display_result: Any) -> Dict[str, Any]:
    if display_result is None:
        return {}
    as_storage_meta = getattr(display_result, "as_storage_meta", None)
    if callable(as_storage_meta):
        try:
            value = as_storage_meta()
            if isinstance(value, dict):
                return dict(value)
        except Exception:
            return {}
    return {}


def _extract_flags(display_result: Any, display_text: Any) -> List[str]:
    flags: List[str] = []
    for attr in ("flags", "actions"):
        raw = getattr(display_result, attr, None)
        if isinstance(raw, (list, tuple, set)):
            for item in raw:
                _append_once(flags, str(item or ""))
    meta = _extract_display_meta(display_result)
    for key in ("flags", "actions", "normalization_flags", "normalization_actions", "core_theme_reject_flags"):
        raw = meta.get(key)
        if isinstance(raw, (list, tuple, set)):
            for item in raw:
                _append_once(flags, str(item or ""))
    text = str(display_text or "")
    if _URL_TOKEN_RE.search(text):
        _append_once(flags, "pii:url")
    if _PHONE_TOKEN_RE.search(text):
        _append_once(flags, "pii:phone")
    if _EMAIL_TOKEN_RE.search(text):
        _append_once(flags, "pii:email")
    if _ADDRESS_TOKEN_RE.search(text):
        _append_once(flags, "pii:address")
    if _SNS_TOKEN_RE.search(text):
        _append_once(flags, "pii:account")
    return flags


def _source_texts_from_emotion_input(emotion_input: Mapping[str, Any] | None) -> List[str]:
    if not isinstance(emotion_input, Mapping):
        return []
    values: List[str] = []
    for key in ("memo", "memo_action", "created_at"):
        text = _collapse(emotion_input.get(key))
        if text:
            values.append(text)
    categories = emotion_input.get("category")
    if isinstance(categories, list):
        values.extend(_collapse(item) for item in categories if _collapse(item))
    emotions = emotion_input.get("emotions")
    if isinstance(emotions, list):
        for item in emotions:
            if isinstance(item, Mapping):
                text = _collapse(item.get("type"))
            else:
                text = _collapse(item)
            if text:
                values.append(text)
    return _ordered_unique(values)


def _is_low_info_source(*, source_texts: Sequence[Any], raw_answer: Any) -> bool:
    combined = _compact(" ".join(_collapse(x) for x in list(source_texts or []) if _collapse(x)))
    raw = _compact(raw_answer)
    source = combined or raw
    if not source:
        return True
    # Japanese inputs have no whitespace; compact length is a safer low-info signal.
    return len(source) <= 8


def _append_source_detection_flags(internal_flags: List[str], *, raw_answer: Any, source_texts: Sequence[Any]) -> None:
    source = " ".join(_collapse(value) for value in [raw_answer, *(source_texts or [])] if _collapse(value))
    lower = source.lower()
    if "http://" in lower or "https://" in lower or "www." in lower:
        _append_once(internal_flags, "pii:url")
        _append_once(internal_flags, "mask:url")
    if _RAW_EMAIL_RE.search(source):
        _append_once(internal_flags, "pii:email")
        _append_once(internal_flags, "mask:email")
    if _RAW_PHONE_RE.search(source):
        _append_once(internal_flags, "pii:phone")
        _append_once(internal_flags, "mask:phone")
    if _RAW_POSTAL_RE.search(source):
        _append_once(internal_flags, "pii:postal")
        _append_once(internal_flags, "mask:postal")
    if any(token in source for token in ("住所", "連絡先", "LINE", "ライン")):
        _append_once(internal_flags, "pii:contact_or_location")
    if any(token in source for token in _ATTACK_TERMS):
        _append_once(internal_flags, "abuse:attack")
        _append_once(internal_flags, "mask:abuse")


def _map_safety_flags(internal_flags: Sequence[str], *, low_info: bool) -> List[str]:
    mapped: List[str] = []
    joined = " ".join(str(flag or "") for flag in internal_flags)

    if low_info:
        _append_once(mapped, "low_info")

    if "preview:fallback_display" in joined:
        _append_once(mapped, "fallback_generated")

    if "pii:url" in joined or "mask:url" in joined:
        _append_once(mapped, "url_detected")
        _append_once(mapped, "url_removed")
        _append_once(mapped, "external_redirect_removed")

    if any(token in joined for token in ("pii:email", "pii:phone", "pii:postal", "pii:line_id", "pii:handle", "pii:account", "pii:address", "pii:contact_or_location")):
        _append_once(mapped, "pii_detected")
        _append_once(mapped, "pii_removed")
    if any(token in joined for token in ("pii:email", "pii:phone", "pii:line_id", "pii:contact_or_location")):
        _append_once(mapped, "contact_removed")
    if any(token in joined for token in ("pii:handle", "pii:account")):
        _append_once(mapped, "account_removed")
    if any(token in joined for token in ("pii:address", "pii:postal", "pii:contact_or_location")):
        _append_once(mapped, "location_removed")

    if any(token in joined for token in ("abuse:", "mask:abuse", "privacy:doxxing")):
        _append_once(mapped, "target_detected")
        _append_once(mapped, "target_removed")
        _append_once(mapped, "attack_detected")
        _append_once(mapped, "attack_removed")
    if any(token in joined for token in ("abuse:slur", "mask:abuse")):
        _append_once(mapped, "insult_removed")
    if any(token in joined for token in ("abuse:threat", "violence", "殺", "刺")):
        _append_once(mapped, "violence_detected")
        _append_once(mapped, "violence_softened")
    if any(token in joined for token in ("doxxing", "privacy:address_plus_contact")):
        _append_once(mapped, "doxxing_context_removed")

    if any(token in joined for token in ("quality:", "normalize:", "format:", "realize:", "rewrite")):
        _append_once(mapped, "normalized")
    if any(token in joined for token in ("abstract", "block:severe", "quality:block")):
        _append_once(mapped, "abstracted")

    return mapped


def _resolve_transform_mode(*, low_info: bool, safety_flags: Sequence[str], internal_flags: Sequence[str], changed: bool) -> str:
    if low_info or "low_info" in safety_flags:
        return TRANSFORM_LOW_INFO
    high_risk_tokens = {
        "url_removed",
        "pii_removed",
        "target_removed",
        "attack_removed",
        "violence_softened",
        "doxxing_context_removed",
        "abstracted",
    }
    if any(flag in high_risk_tokens for flag in safety_flags):
        return TRANSFORM_ABSTRACTED
    if changed or any(str(flag).startswith(("normalize:", "format:", "realize:", "quality:")) for flag in internal_flags):
        return TRANSFORM_NORMALIZED
    return TRANSFORM_AS_IS


def _resolve_generation_status(*, transform_mode: str, internal_flags: Sequence[str], display_state: str) -> str:
    joined = " ".join(str(flag or "") for flag in internal_flags)
    if str(display_state or "").lower() == "blocked":
        return GENERATION_FAILED
    if transform_mode in {TRANSFORM_LOW_INFO, TRANSFORM_ABSTRACTED}:
        return GENERATION_FALLBACK_GENERATED
    if "preview:fallback_display" in joined or "quality:block" in joined:
        return GENERATION_FALLBACK_GENERATED
    return GENERATION_GENERATED


def _resolve_safety_level(*, safety_flags: Sequence[str], display_state: str, transform_mode: str) -> str:
    if str(display_state or "").lower() == "blocked":
        return SAFETY_BLOCKED_INTERNAL
    high_risk = {
        "url_removed",
        "pii_removed",
        "target_removed",
        "attack_removed",
        "violence_softened",
        "doxxing_context_removed",
    }
    if any(flag in high_risk for flag in safety_flags):
        return SAFETY_HIGH_RISK_TRANSFORMED
    if safety_flags or transform_mode != TRANSFORM_AS_IS:
        return SAFETY_NEEDS_TRANSFORM
    return SAFETY_SAFE


def build_piece_generation_policy(
    *,
    piece_text: Any,
    raw_answer: Any,
    display_result: Any = None,
    source_texts: Optional[Sequence[Any]] = None,
    emotion_input: Mapping[str, Any] | None = None,
    visibility_status: str = VISIBILITY_PREVIEW_READY,
) -> PieceGenerationPolicyResult:
    text = _collapse(piece_text)
    state = str(getattr(display_result, "answer_display_state", "") or "").strip().lower()
    if not state:
        state = "ready" if text else "blocked"
    changed = bool(getattr(display_result, "changed", False))
    source_values = _ordered_unique([*(source_texts or []), *_source_texts_from_emotion_input(emotion_input)])
    low_info = _is_low_info_source(source_texts=source_values, raw_answer=raw_answer)
    internal_flags = _extract_flags(display_result, text)
    _append_source_detection_flags(internal_flags, raw_answer=raw_answer, source_texts=source_values)
    safety_flags = _map_safety_flags(internal_flags, low_info=low_info)
    transform_mode = _resolve_transform_mode(
        low_info=low_info,
        safety_flags=safety_flags,
        internal_flags=internal_flags,
        changed=changed,
    )
    generation_status = _resolve_generation_status(
        transform_mode=transform_mode,
        internal_flags=internal_flags,
        display_state=state,
    )
    safety_level = _resolve_safety_level(
        safety_flags=safety_flags,
        display_state=state,
        transform_mode=transform_mode,
    )
    return PieceGenerationPolicyResult(
        visibility_status=str(visibility_status or VISIBILITY_PREVIEW_READY),
        generation_status=generation_status,
        transform_mode=transform_mode,
        safety_level=safety_level,
        safety_flags=safety_flags,
        piece_text_hash=compute_piece_text_hash(text),
    )


def piece_policy_from_content_json(content_json: Mapping[str, Any] | None) -> PieceGenerationPolicyResult:
    source = content_json if isinstance(content_json, Mapping) else {}
    national_core = source.get("national_core") if isinstance(source.get("national_core"), Mapping) else {}
    piece_core = source.get("piece_core") if isinstance(source.get("piece_core"), Mapping) else {}
    core = {**dict(piece_core), **dict(national_core)}
    return PieceGenerationPolicyResult(
        visibility_status=str(core.get("visibility_status") or VISIBILITY_PREVIEW_READY),
        generation_status=str(core.get("generation_status") or GENERATION_GENERATED),
        transform_mode=str(core.get("transform_mode") or TRANSFORM_NORMALIZED),
        safety_level=str(core.get("safety_level") or SAFETY_NEEDS_TRANSFORM),
        safety_flags=[str(x).strip() for x in (core.get("safety_flags") or []) if str(x).strip()],
        piece_text_hash=str(core.get("piece_text_hash") or core.get("preview_text_hash") or ""),
        source_input_scope=str(core.get("source_input_scope") or PIECE_SOURCE_INPUT_SCOPE_CURRENT_ONLY),
        schema_version=str(core.get("schema_version") or PIECE_CORE_SCHEMA_VERSION),
    )


def with_piece_policy_visibility(
    policy: PieceGenerationPolicyResult,
    *,
    visibility_status: str,
    piece_text: Any = None,
) -> PieceGenerationPolicyResult:
    text_hash = compute_piece_text_hash(piece_text) if piece_text is not None else policy.piece_text_hash
    return PieceGenerationPolicyResult(
        visibility_status=str(visibility_status or policy.visibility_status),
        generation_status=policy.generation_status,
        transform_mode=policy.transform_mode,
        safety_level=policy.safety_level,
        safety_flags=list(policy.safety_flags),
        piece_text_hash=text_hash or policy.piece_text_hash,
        source_input_scope=policy.source_input_scope,
        schema_version=policy.schema_version,
    )


def public_piece_contract_from_content_json(content_json: Mapping[str, Any] | None, *, include_safety_flags: bool = False) -> Dict[str, Any]:
    return piece_policy_from_content_json(content_json).as_public_contract(include_safety_flags=include_safety_flags)


__all__ = [
    "GENERATION_FAILED",
    "GENERATION_FALLBACK_GENERATED",
    "GENERATION_GENERATED",
    "PIECE_CORE_SCHEMA_VERSION",
    "SAFETY_BLOCKED_INTERNAL",
    "SAFETY_HIGH_RISK_TRANSFORMED",
    "SAFETY_NEEDS_TRANSFORM",
    "SAFETY_SAFE",
    "TRANSFORM_ABSTRACTED",
    "TRANSFORM_AS_IS",
    "TRANSFORM_LOW_INFO",
    "TRANSFORM_NORMALIZED",
    "VISIBILITY_DELETED",
    "VISIBILITY_PREVIEW_READY",
    "VISIBILITY_PUBLISHED",
    "VISIBILITY_SYSTEM_HIDDEN",
    "PieceGenerationPolicyResult",
    "build_piece_generation_policy",
    "compute_piece_text_hash",
    "piece_policy_from_content_json",
    "public_piece_contract_from_content_json",
    "with_piece_policy_visibility",
]
