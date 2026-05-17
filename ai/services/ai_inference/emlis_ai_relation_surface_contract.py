# -*- coding: utf-8 -*-
from __future__ import annotations

"""Shared relation surface contract for EmlisAI generated observations.

This module is intentionally small and dependency-light so Reader, Surface
Realizer and Self-Repair can share the same relation cue vocabulary without
creating import cycles.  It does not read or store raw user input; callers pass
only generated candidate text or relation metadata.
"""

import re
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence, Tuple

RELATION_SURFACE_CONTRACT_VERSION = "emlis.relation_surface_contract.v1"

RAW_INPUT_META_KEYS = {
    "raw_text",
    "raw_input",
    "input_text",
    "user_input",
    "current_input",
    "memo",
    "memo_text",
    "memo_action",
    "raw_user_text",
    "original_text",
    "source_text",
}

# Generic relation cues that already represent a relation surface rather than a
# single label.  Do not add broad words such as "関係" here; that would turn the
# Reader Gate into a lexical pass-through and weaken product-quality metrics.
GENERIC_RELATION_SURFACE_PATTERNS: tuple[tuple[str, str], ...] = (
    ("generic_connected", r"つなが(?:って|り|る|っています|れて|った)"),
    ("generic_same_flow", r"同じ(?:時間|場所|流れ|線上|中)"),
    ("generic_both_sides", r"(?:両方|片方|もう一方|一方)"),
    ("generic_overlap", r"(?:重な|並ん|混ざ|同時に|せめぎ合|抱えて)"),
    ("generic_not_one_side", r"(?:片方だけ|一方向|寄らず)"),
)

# Recovery relation cues are stricter.  A mere "回復" or "戻る" is not enough;
# the sentence should surface a bridge between a return/recovery motion and
# prior load, weight, pressure, fatigue, or flow.
RECOVERY_RELATION_SURFACE_PATTERNS: tuple[tuple[str, str], ...] = (
    (
        "recovery_load_bridge",
        r"(?:戻ってくる動き|戻る流れ|少し戻(?:って|る)?|形を取り直(?:す|し)|回復)"
        r".{0,32}"
        r"(?:前段|その前|前の|負荷|重さ|圧力|疲れ|流れ)",
    ),
    (
        "recovery_load_bridge_reverse",
        r"(?:前段|その前|前の|負荷|重さ|圧力|疲れ)"
        r".{0,32}"
        r"(?:戻ってくる|戻る|回復|取り直)",
    ),
    (
        "recovery_connected_flow",
        r"(?:戻る流れ|戻ってくる動き|少し戻る動き).{0,32}(?:つなが|同じ流れ|切り離されず)",
    ),
    (
        "recovery_connected_flow_reverse",
        r"(?:つなが|同じ流れ|切り離されず).{0,32}(?:戻る流れ|戻ってくる動き|回復)",
    ),
)

_RELATION_TYPE_ALIASES = {
    "positive_recovery": "recovery",
    "recovering": "recovery",
    "small_recovery": "recovery",
    "repair": "recovery",
}
_CONTEXT_TRUE_VALUES = {"1", "true", "yes", "on", "present", "detected"}


@dataclass(frozen=True)
class RelationSurfaceSignal:
    """Diagnostic-only result of relation surface detection."""

    detected: bool
    count: int = 0
    keys: Tuple[str, ...] = field(default_factory=tuple)
    relation_types: Tuple[str, ...] = field(default_factory=tuple)
    contract_version: str = RELATION_SURFACE_CONTRACT_VERSION
    strict_recovery_bridge_required: bool = True

    def as_meta(self) -> dict[str, Any]:
        return {
            "relation_surface_contract_version": self.contract_version,
            "contract_version": self.contract_version,
            "detected": bool(self.detected),
            "count": int(self.count),
            "keys": list(self.keys),
            "relation_types": list(self.relation_types),
            "reader_relation_signal_detected": bool(self.detected),
            "reader_relation_signal_count": int(self.count),
            "reader_relation_signal_keys": list(self.keys),
            "reader_relation_signal_relation_types": list(self.relation_types),
            "strict_recovery_bridge_required": bool(self.strict_recovery_bridge_required),
            "raw_input_included": False,
        }


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").replace("\u3000", " ")).strip()


def normalize_relation_surface_type(value: Any) -> str:
    relation = re.sub(r"[^0-9a-zA-Z_\-.]+", "_", str(value or "").strip().lower()).strip("_")
    return _RELATION_TYPE_ALIASES.get(relation, relation or "unknown")


def _dedupe(values: Iterable[Any]) -> Tuple[str, ...]:
    out: list[str] = []
    for raw in values or ():
        item = str(raw or "").strip()
        if item and item not in out:
            out.append(item)
    return tuple(out)


def _expected_relation_types(values: Iterable[Any] | Any = ()) -> Tuple[str, ...]:
    if values is None:
        return tuple()
    if isinstance(values, (str, bytes)):
        values = (values,)
    return _dedupe(normalize_relation_surface_type(value) for value in values)


def _pattern_hits(text: str, patterns: Sequence[tuple[str, str]]) -> Tuple[str, ...]:
    return _dedupe(key for key, pattern in patterns if re.search(pattern, text))


def detect_relation_surface(text: Any, expected_relation_types: Iterable[Any] | Any = ()) -> dict[str, Any]:
    """Detect relation surface cues in generated candidate text.

    Recovery is strict: when recovery is expected, generic cues alone are not
    enough.  This preserves Reader Gate safety and avoids passing on a bare word
    such as "関係" or "回復".
    """

    candidate = _clean(text)
    expected = _expected_relation_types(expected_relation_types)
    expects_recovery = "recovery" in expected
    generic_keys = _pattern_hits(candidate, GENERIC_RELATION_SURFACE_PATTERNS)
    recovery_keys = _pattern_hits(candidate, RECOVERY_RELATION_SURFACE_PATTERNS)

    keys: list[str] = []
    relation_types: list[str] = []
    if recovery_keys:
        keys.extend(recovery_keys)
        relation_types.append("recovery")
    if generic_keys and not expects_recovery:
        keys.extend(generic_keys)
        if expected:
            relation_types.extend(rt for rt in expected if rt != "unknown")
        else:
            relation_types.append("generic")

    signal = RelationSurfaceSignal(
        detected=bool(keys),
        count=len(_dedupe(keys)),
        keys=_dedupe(keys),
        relation_types=_dedupe(relation_types),
    )
    meta = signal.as_meta()
    meta.update(
        {
            "expected_relation_types": list(expected),
            "generic_relation_signal_keys": list(generic_keys),
            "recovery_relation_signal_keys": list(recovery_keys),
        }
    )
    return meta


def _context_flag(context_flags: Mapping[str, Any] | None, key: str) -> bool:
    if not isinstance(context_flags, Mapping):
        return False
    value = context_flags.get(key)
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    return str(value or "").strip().lower() in _CONTEXT_TRUE_VALUES


def relation_marker_key(relation_type: Any, context_flags: Mapping[str, Any] | None = None) -> str:
    relation = normalize_relation_surface_type(relation_type)
    if relation == "recovery":
        if _context_flag(context_flags, "prior_load_present"):
            return "recovery_load_bridge_v1"
        return "recovery_connected_flow_v1"
    if relation:
        return f"{relation}_relation_marker_v1"
    return "generic_relation_marker_v1"


def relation_marker_phrase(relation_type: Any, context_flags: Mapping[str, Any] | None = None) -> str:
    """Return a short relation marker phrase for Self-Repair.

    This is a relation-surface grammar part, not a fixed fallback observation.
    It only clarifies an already declared relation type.
    """

    relation = normalize_relation_surface_type(relation_type)
    if relation == "recovery":
        if _context_flag(context_flags, "prior_load_present"):
            return "戻ってくる動きと、その前の重さが同じ流れの中でつながっています。"
        return "戻る流れが、前の流れと切り離されずにつながっています。"
    if relation == "contrast":
        return "別々の向きが片方だけに寄らず、同じ場所に並んでいます。"
    if relation == "coexistence":
        return "同じ時間の中に重なっていることも残っています。"
    if relation == "pressure":
        return "圧力として前面に出ていることも残っています。"
    if relation == "approach_avoidance":
        return "近づく動きと止まる動きの両方が同じ線上に残っています。"
    if relation == "residue":
        return "あとに残る余韻として、前の流れとつながっています。"
    return "根拠のある範囲の関係だけを同じ流れの中に置いています。"


def relation_marker_meta(relation_type: Any, context_flags: Mapping[str, Any] | None = None) -> dict[str, Any]:
    relation = normalize_relation_surface_type(relation_type)
    phrase = relation_marker_phrase(relation, context_flags=context_flags)
    return {
        "relation_surface_contract_version": RELATION_SURFACE_CONTRACT_VERSION,
        "contract_version": RELATION_SURFACE_CONTRACT_VERSION,
        "relation_type": relation,
        "relation_marker_key": relation_marker_key(relation, context_flags=context_flags),
        "relation_marker_phrase": phrase,
        "relation_marker_signal": detect_relation_surface(phrase, expected_relation_types=(relation,)),
        "meaning_added": False,
        "raw_input_included": False,
        "gate_relaxed": False,
    }


def build_relation_surface_contract_meta() -> dict[str, Any]:
    return {
        "version": RELATION_SURFACE_CONTRACT_VERSION,
        "contract_version": RELATION_SURFACE_CONTRACT_VERSION,
        "generic_relation_cue_keys": [key for key, _ in GENERIC_RELATION_SURFACE_PATTERNS],
        "recovery_relation_cue_keys": [key for key, _ in RECOVERY_RELATION_SURFACE_PATTERNS],
        "recovery_marker_key": relation_marker_key("recovery", {"prior_load_present": True}),
        "strict_matching": True,
        "relation_word_alone_passes": False,
        "raw_input_included": False,
    }


__all__ = [
    "GENERIC_RELATION_SURFACE_PATTERNS",
    "RECOVERY_RELATION_SURFACE_PATTERNS",
    "RELATION_SURFACE_CONTRACT_VERSION",
    "RAW_INPUT_META_KEYS",
    "RelationSurfaceSignal",
    "build_relation_surface_contract_meta",
    "detect_relation_surface",
    "normalize_relation_surface_type",
    "relation_marker_key",
    "relation_marker_meta",
    "relation_marker_phrase",
]
