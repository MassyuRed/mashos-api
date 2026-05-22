# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step2 Runtime Surface Quality signature measurement for EmlisAI.

This module measures the *displayed observation surface* after Step1 source
lock.  It accepts a public observation body only as an in-memory input and
returns normalized key sequences, counts, hashes, and warning codes.  The output
must never contain raw input bodies or the public ``comment_text`` body.
"""

import hashlib
import json
import re
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, is_dataclass
from typing import Any

from emlis_ai_phrase_unit_grammar_normalizer import (
    PHRASE_UNIT_GRAMMAR_NORMALIZER_VERSION,
    collect_phrase_unit_grammar_warning_codes,
    detect_phrase_unit_grammar_warning_codes_for_text,
)

SURFACE_QUALITY_SIGNATURE_VERSION = "emlis.surface_quality_signature.v1"
SURFACE_QUALITY_SIGNATURE_STEP = "Step2_Surface_Signature_Measurement"
SURFACE_QUALITY_SIGNATURE_SOURCE = "surface_quality_signature"
SURFACE_QUALITY_SIGNATURE_HASH_PREFIX = "sha256:"

_FORBIDDEN_TEXT_PAYLOAD_KEYS = {
    "raw_input", "rawInput", "raw_text", "rawText", "source_text", "sourceText",
    "input", "input_text", "inputText", "user_input", "userInput", "memo",
    "memo_text", "memoText", "current_input", "currentInput", "comment_text",
    "commentText", "input_feedback_comment", "inputFeedbackComment",
    "public_comment_text", "candidate_comment_text", "reply_text", "replyText",
    "surface_text", "realized_text", "line_text", "body", "text", "sentence",
    "sentences", "phrase", "raw_quote", "raw_quotes", "matched_raw_quote_fragments",
}

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[。！？!?])\s*|\n+")
_LINE_SPLIT_RE = re.compile(r"\r\n|\r|\n")
_GREETING_RE = re.compile(r"^(?:[^。！？!?\n]{1,36}さん、?)?\s*Emlis\s*です[。.!！]?$", re.IGNORECASE)
_GENERIC_CENTER_RE = re.compile(r"中心(?:に|として|とし?ては)?(?:あります|見ています|出ています|置かれています|にある)")
_CONNECTOR_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("sono_nakademo", re.compile(r"^(?:その中でも|そのなかでも|中でも)[、,]?")),
    ("sono_nakade", re.compile(r"^(?:その中で|そのなかで)[、,]?")),
    ("douji", re.compile(r"^(?:同じ時間の中に|同じ時間に|同時に|同じ中に)[、,]?")),
    ("soredemo", re.compile(r"^(?:それでも|それでいて)[、,]?")),
    ("ippoude", re.compile(r"^(?:一方で|反対に|もう一方で)[、,]?")),
    ("tada", re.compile(r"^(?:ただ|ただし)[、,]?")),
    ("dakara", re.compile(r"^(?:だから|なので)[、,]?")),
    ("soshite", re.compile(r"^(?:そして|それから)[、,]?")),
    ("mata", re.compile(r"^(?:また|さらに)[、,]?")),
)
_RELATION_MARKER_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("overlap_time", re.compile(r"同じ時間|同時|重な")),
    ("coexistence", re.compile(r"一緒に|並んで|共に|同じ中")),
    ("connection", re.compile(r"つなが|繋が|結び")),
    ("residue", re.compile(r"残って|残り|余韻")),
    ("pressure", re.compile(r"負担|圧|しんど|重さ|先になる")),
    ("recovery", re.compile(r"回復|休む|整える|戻す")),
)
_MALFORMED_NOMINALIZATION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("stem_koto_hanareru", re.compile(r"離れこと")),
    ("malformed_nominalization_missing_ru", re.compile(r"(?:離れ|分かれ|外れ|崩れ|揺れ|流れ|逃げ|戻れ|向かえ|変われ|整え|貯め|決め|始め)こと")),
    ("malformed_nominalization_particle_before_koto", re.compile(r"(?:を|が|は|に|で|へ|から|まで|より)こと")),
    ("malformed_nominalization_auxiliary_fragment", re.compile(r"(?:なっ|し|い|見え|残っ|重なっ)こと(?:も|が|は|に|$)")),
)
_OBSERVATION_PREDICATE_FAMILIES = {"visible", "remain", "overlap", "important", "center", "generic_exists"}


class SurfaceQualitySignatureError(ValueError):
    """Raised when a surface quality signature violates meta-only contracts."""


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _safe_mapping(value: Any) -> dict[str, Any]:
    if is_dataclass(value):
        value = asdict(value)
    return {str(key): item for key, item in value.items()} if isinstance(value, Mapping) else {}


def _contains_forbidden_text_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key) in _FORBIDDEN_TEXT_PAYLOAD_KEYS:
                return True
            if _contains_forbidden_text_payload_key(item):
                return True
        return False
    if isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_text_payload_key(item) for item in value)
    return False


def assert_surface_quality_signature_meta_only(
    value: Mapping[str, Any],
    *,
    source: str = SURFACE_QUALITY_SIGNATURE_SOURCE,
) -> None:
    if _contains_forbidden_text_payload_key(value):
        raise SurfaceQualitySignatureError(f"{source} must stay meta-only and must not include text payload keys")
    for flag in (
        "raw_input_included", "raw_text_included", "input_text_included",
        "comment_text_included", "comment_text_body_included", "response_shape_changed",
        "public_response_key_change", "api_route_changed", "db_physical_name_changed",
        "rn_visible_contract_changed", "display_gate_relaxed", "grounding_gate_relaxed",
        "template_gate_relaxed", "reader_gate_relaxed", "gate_relaxed",
        "public_release_applied", "product_gate_achieved",
    ):
        if value.get(flag) is True:
            raise SurfaceQualitySignatureError(f"{source} violates fixed contract: {flag}=true")


def _split_lines(comment_text: Any) -> list[str]:
    return [line.strip() for line in _LINE_SPLIT_RE.split(_clean(comment_text)) if line.strip()]


def _split_sentences(comment_text: Any) -> list[str]:
    return [part.strip() for part in _SENTENCE_SPLIT_RE.split(_clean(comment_text)) if part.strip()]


def _role_for_line(line: str, *, index: int) -> str:
    if _GREETING_RE.match(line):
        return "greeting"
    if index <= 1 and _GENERIC_CENTER_RE.search(line):
        return "opening"
    if _GENERIC_CENTER_RE.search(line):
        return "opening"
    if re.search(r"同じ時間|同時|重な|つなが|繋が|並ん|残って", line):
        return "relation"
    if re.search(r"見えています|見ています|大切|重要|頑張|整える", line):
        return "support"
    if re.search(r"一緒に見|小さく扱|軽く扱|ここに置", line):
        return "closing"
    return "body"


def _connector_key(line: str) -> str:
    target = line.strip()
    for key, pattern in _CONNECTOR_PATTERNS:
        if pattern.search(target):
            return key
    if "その中でも" in target or "そのなかでも" in target:
        return "sono_nakademo"
    if "同じ時間" in target or "同時" in target:
        return "douji"
    return "none"


def _predicate_key(line: str) -> str:
    if _GENERIC_CENTER_RE.search(line):
        return "center"
    if re.search(r"見えています|見えます|見ています|見ます", line):
        return "visible"
    if re.search(r"残っています|残って|残ります", line):
        return "remain"
    if re.search(r"重なっています|重なって|重なります", line):
        return "overlap"
    if re.search(r"大切|大事|重要", line):
        return "important"
    if re.search(r"つながっています|つながって|繋がって", line):
        return "connected"
    if re.search(r"あります|ありました|にある", line):
        return "generic_exists"
    if _GREETING_RE.match(line):
        return "greeting"
    return "other"


def _ending_key(line: str) -> str:
    compact = line.rstrip("。.!！?？ ")
    if compact.endswith("ていますね"):
        return "teimasu_ne"
    if compact.endswith("ています"):
        return "teimasu"
    if compact.endswith("あります"):
        return "arimasu"
    if compact.endswith("です"):
        return "desu"
    if compact.endswith("ます"):
        return "masu"
    if compact.endswith("ました"):
        return "mashita"
    if compact.endswith("ですね"):
        return "desu_ne"
    return "other"


def _ending_family_key(key: str) -> str:
    if key in {"teimasu", "teimasu_ne", "arimasu", "masu", "mashita"}:
        return "masu_family"
    if key in {"desu", "desu_ne"}:
        return "desu_family"
    return key


def _relation_marker_keys(line: str) -> list[str]:
    out: list[str] = []
    for key, pattern in _RELATION_MARKER_PATTERNS:
        if pattern.search(line):
            out.append(key)
    return out or ["none"]


def _max_run(keys: Sequence[str], *, ignore: set[str] | None = None) -> int:
    ignore = ignore or set()
    best = 0
    current_key = ""
    current = 0
    for key in keys:
        if key in ignore:
            current_key = ""
            current = 0
            continue
        if key == current_key:
            current += 1
        else:
            current_key = key
            current = 1
        best = max(best, current)
    return best


def _max_frequency(keys: Sequence[str], *, ignore: set[str] | None = None) -> int:
    ignore = ignore or set()
    counter = Counter(key for key in keys if key not in ignore)
    return max(counter.values(), default=0)


def _grammar_warning_codes(lines: Sequence[str]) -> list[str]:
    codes: list[str] = []
    for line in lines:
        for code, pattern in _MALFORMED_NOMINALIZATION_PATTERNS:
            if pattern.search(line) and code not in codes:
                codes.append(code)
        for code in detect_phrase_unit_grammar_warning_codes_for_text(line):
            if code not in codes:
                codes.append(code)
    return codes


def _raw_echo_risk_from_meta(*metas: Mapping[str, Any]) -> bool:
    for meta in metas:
        safe = _safe_mapping(meta)
        if safe.get("raw_echo_risk") is True or safe.get("raw_input_included") is True:
            return True
        if safe.get("raw_input_sentence_ids") or safe.get("raw_echo_sentence_ids"):
            return True
    return False


def _signature_family_payload(signature: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "line_role_sequence": list(signature.get("line_role_sequence") or []),
        "opening_family_key": signature.get("opening_family_key") or "none",
        "connector_key_sequence": list(signature.get("connector_key_sequence") or []),
        "predicate_key_sequence": list(signature.get("predicate_key_sequence") or []),
        "ending_key_sequence": list(signature.get("ending_key_sequence") or []),
        "relation_marker_key_sequence": list(signature.get("relation_marker_key_sequence") or []),
        "generic_center_phrase_count": int(signature.get("generic_center_phrase_count") or 0),
        "same_connector_run_max": int(signature.get("same_connector_run_max") or 0),
        "same_predicate_family_count": int(signature.get("same_predicate_family_count") or 0),
        "same_ending_family_count": int(signature.get("same_ending_family_count") or 0),
        "grammar_warning_codes": list(signature.get("grammar_warning_codes") or []),
        "template_major": bool(signature.get("template_major")),
    }


def _hash_payload(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return SURFACE_QUALITY_SIGNATURE_HASH_PREFIX + hashlib.sha256(encoded).hexdigest()


def build_surface_quality_signature(
    *,
    comment_text: Any,
    sentence_bindings: Sequence[Mapping[str, Any]] | Mapping[str, Any] | None = None,
    relation_meta: Mapping[str, Any] | None = None,
    runtime_surface_source_lock: Mapping[str, Any] | None = None,
    raw_echo_meta: Mapping[str, Any] | None = None,
    coverage_group: Any = "",
    phrase_unit_grammar_meta: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return SurfaceQualitySignatureV1 for an in-memory observation body."""

    lines = _split_lines(comment_text)
    sentences = _split_sentences(comment_text)
    roles = [_role_for_line(line, index=index) for index, line in enumerate(lines)]
    connectors = [_connector_key(line) for line in lines]
    predicates = [_predicate_key(line) for line in lines]
    endings = [_ending_key(line) for line in lines]
    relation_keys_flat: list[str] = []
    for line in lines:
        for key in _relation_marker_keys(line):
            if key != "none":
                relation_keys_flat.append(key)
    if not relation_keys_flat:
        relation_keys_flat = ["none"]

    opening_family_key = "none"
    if any(key == "center" for key in predicates):
        opening_family_key = "center_phrase"
    elif any(role == "opening" for role in roles):
        opening_family_key = "state_phrase"
    elif relation_keys_flat != ["none"]:
        opening_family_key = "relation_start"

    generic_center_phrase_count = sum(1 for line in lines if _GENERIC_CENTER_RE.search(line))
    same_connector_run_max = _max_run(connectors, ignore={"none"})
    same_connector_family_count = _max_frequency(connectors, ignore={"none"})
    same_connector_repetition_count = max(0, same_connector_family_count - 1)
    observation_predicate_family_count = sum(1 for key in predicates if key in _OBSERVATION_PREDICATE_FAMILIES)
    same_predicate_family_count = _max_frequency([key for key in predicates if key in _OBSERVATION_PREDICATE_FAMILIES], ignore={"other", "greeting"})
    ending_families = [_ending_family_key(key) for key in endings]
    same_ending_family_count = _max_frequency(ending_families, ignore={"other"})
    line_grammar_codes = _grammar_warning_codes(lines)
    phrase_unit_grammar_warning_codes = list(collect_phrase_unit_grammar_warning_codes(phrase_unit_grammar_meta or {}))
    # Step8 grammar warnings can come either from material-stage meta or, for
    # legacy observation rows, from in-memory surface text analysis.  Both stay
    # body-free in the exported signature.
    phrase_unit_grammar_warning_codes = list(dict.fromkeys([*phrase_unit_grammar_warning_codes, *line_grammar_codes]))
    grammar_codes = list(dict.fromkeys([*line_grammar_codes, *phrase_unit_grammar_warning_codes]))
    malformed_nominalization_risk = bool(grammar_codes)
    relation = _safe_mapping(relation_meta)
    lock = _safe_mapping(runtime_surface_source_lock)
    bindings = _safe_mapping(sentence_bindings) if isinstance(sentence_bindings, Mapping) else {}
    raw_echo_risk = _raw_echo_risk_from_meta(relation, lock, bindings, _safe_mapping(raw_echo_meta))
    line_count = len(lines)
    body_sentence_count = len([sentence for sentence in sentences if not _GREETING_RE.match(sentence)])

    surface_major_reasons: list[str] = []
    if generic_center_phrase_count > 0:
        surface_major_reasons.append("generic_center_phrase")
    if same_connector_run_max >= 2:
        surface_major_reasons.append("same_connector_run")
        surface_major_reasons.append("connector_repetition")
    if same_connector_family_count >= 2 and line_count >= 3:
        surface_major_reasons.append("connector_family_repetition")
    if same_ending_family_count >= 3 and line_count >= 4:
        surface_major_reasons.append("same_ending_family")
    if observation_predicate_family_count >= max(3, body_sentence_count) and generic_center_phrase_count > 0:
        surface_major_reasons.append("observation_predicate_stack")
    if malformed_nominalization_risk:
        surface_major_reasons.append("grammar_warning")
    if raw_echo_risk:
        surface_major_reasons.append("raw_echo_risk")

    template_major = bool(
        (generic_center_phrase_count > 0 and same_connector_run_max >= 2)
        or (generic_center_phrase_count > 0 and same_ending_family_count >= 3 and observation_predicate_family_count >= 3)
        or (same_connector_family_count >= 3)
        or malformed_nominalization_risk
        or raw_echo_risk
    )

    signature: dict[str, Any] = {
        "schema_version": SURFACE_QUALITY_SIGNATURE_VERSION,
        "version": SURFACE_QUALITY_SIGNATURE_VERSION,
        "source_step": SURFACE_QUALITY_SIGNATURE_STEP,
        "step": SURFACE_QUALITY_SIGNATURE_STEP,
        "source": SURFACE_QUALITY_SIGNATURE_SOURCE,
        "signature_ready": True,
        "surface_quality_signature_ready": True,
        "step2_surface_quality_signature_ready": True,
        "surface_quality_signature_measured": True,
        "step2_surface_signature_measured": True,
        "surface_signature_measurement_only": True,
        "signature_hash_algorithm": "sha256",
        "signature_hash_input_kind": "normalized_surface_key_sequence_only",
        "line_count": line_count,
        "body_sentence_count": body_sentence_count,
        "line_role_sequence": roles,
        "opening_family_key": opening_family_key,
        "connector_key_sequence": connectors,
        "predicate_key_sequence": predicates,
        "ending_key_sequence": endings,
        "relation_marker_key_sequence": relation_keys_flat,
        "generic_center_phrase_count": generic_center_phrase_count,
        "same_connector_run_max": same_connector_run_max,
        "same_connector_family_count": same_connector_family_count,
        "same_connector_repetition_count": same_connector_repetition_count,
        "same_predicate_family_count": same_predicate_family_count,
        "observation_predicate_family_count": observation_predicate_family_count,
        "same_ending_family_count": same_ending_family_count,
        "malformed_nominalization_risk": malformed_nominalization_risk,
        "raw_echo_risk": raw_echo_risk,
        "grammar_warning_codes": grammar_codes,
        "surface_grammar_warning_codes": grammar_codes,
        "line_grammar_warning_codes": line_grammar_codes,
        "phrase_unit_grammar_warning_codes": phrase_unit_grammar_warning_codes,
        "phrase_unit_grammar_normalizer_version": PHRASE_UNIT_GRAMMAR_NORMALIZER_VERSION,
        "step8_phrase_unit_grammar_normalizer_connected": True,
        "grammar_warning_count": len(grammar_codes),
        "surface_grammar_warning_count": len(grammar_codes),
        "template_major": template_major,
        "surface_template_major": template_major,
        "grammar_major": malformed_nominalization_risk,
        "surface_major_reasons": surface_major_reasons,
        "template_major_reasons": surface_major_reasons,
        "coverage_group": _clean(coverage_group) or _clean(lock.get("coverage_group")),
        "raw_input_included": False,
        "raw_text_included": False,
        "input_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "text_body_used_only_in_memory": True,
        "response_shape_changed": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "gate_relaxed": False,
        "public_release_applied": False,
        "product_gate_achieved": False,
    }
    family_payload = _signature_family_payload(signature)
    signature["surface_signature_family_key"] = _hash_payload(family_payload)
    signature["signature_family_key"] = signature["surface_signature_family_key"]
    signature["surface_signature_id"] = _hash_payload(
        {
            "schema_version": SURFACE_QUALITY_SIGNATURE_VERSION,
            "family": family_payload,
            "line_count": line_count,
            "body_sentence_count": body_sentence_count,
        }
    )
    assert_surface_quality_signature_meta_only(signature)
    return signature


def coerce_surface_quality_signature_meta(value: Mapping[str, Any] | None) -> dict[str, Any]:
    data = _safe_mapping(value)
    if not data:
        return {}
    nested = _safe_mapping(data.get("surface_quality_signature") or data.get("step2_surface_quality_signature"))
    if nested:
        data = nested
    if not data.get("surface_signature_id") and data.get("schema_version") != SURFACE_QUALITY_SIGNATURE_VERSION and data.get("version") != SURFACE_QUALITY_SIGNATURE_VERSION:
        return {}
    data = dict(data)
    data.setdefault("schema_version", SURFACE_QUALITY_SIGNATURE_VERSION)
    data.setdefault("version", data.get("schema_version") or SURFACE_QUALITY_SIGNATURE_VERSION)
    data.setdefault("source_step", SURFACE_QUALITY_SIGNATURE_STEP)
    data.setdefault("step", SURFACE_QUALITY_SIGNATURE_STEP)
    data.setdefault("source", SURFACE_QUALITY_SIGNATURE_SOURCE)
    data.setdefault("signature_ready", bool(data.get("surface_signature_id")))
    data.setdefault("surface_quality_signature_ready", bool(data.get("surface_signature_id")))
    data.setdefault("step2_surface_quality_signature_ready", bool(data.get("surface_signature_id")))
    data.setdefault("raw_input_included", False)
    data.setdefault("raw_text_included", False)
    data.setdefault("input_text_included", False)
    data.setdefault("comment_text_included", False)
    data.setdefault("comment_text_body_included", False)
    assert_surface_quality_signature_meta_only(data, source="coerced_surface_quality_signature")
    return data


def normalize_surface_quality_signature_from_meta(value: Mapping[str, Any] | None) -> dict[str, Any]:
    return coerce_surface_quality_signature_meta(value)


def surface_quality_signature_from_meta(*sources: Mapping[str, Any] | None) -> dict[str, Any]:
    for source in sources:
        meta = _safe_mapping(source)
        if not meta:
            continue
        for key in ("surface_quality_signature", "step2_surface_quality_signature", "surface_signature_v1"):
            nested = _safe_mapping(meta.get(key))
            if nested:
                coerced = coerce_surface_quality_signature_meta(nested)
                if coerced.get("surface_signature_id"):
                    return coerced
        signature_id = _clean(meta.get("surface_signature_id"))
        if signature_id:
            return coerce_surface_quality_signature_meta({"surface_signature_id": signature_id})
    return {}


def normalize_surface_signature_to_scorecard_event(signature: Mapping[str, Any] | None) -> dict[str, Any]:
    sig = coerce_surface_quality_signature_meta(signature)
    if not sig:
        return {
            "surface_quality_signature_version": SURFACE_QUALITY_SIGNATURE_VERSION,
            "surface_quality_signature_ready": False,
            "step2_surface_quality_signature_ready": False,
            "step2_surface_signature_measurement_ready": False,
            "step2_surface_signature_measured": False,
            "surface_signature_id": "",
            "raw_input_included": False,
            "comment_text_body_included": False,
        }
    fields = {
        "surface_quality_signature_version": sig.get("schema_version") or SURFACE_QUALITY_SIGNATURE_VERSION,
        "surface_quality_signature_ready": True,
        "step2_surface_quality_signature_ready": True,
        "step2_surface_signature_measurement_ready": True,
        "step2_surface_signature_measured": True,
        "surface_quality_signature": sig,
        "step2_surface_quality_signature": sig,
        "surface_signature_id": _clean(sig.get("surface_signature_id")),
        "surface_signature_family_key": _clean(sig.get("surface_signature_family_key") or sig.get("signature_family_key")),
        "surface_line_count": int(sig.get("line_count") or 0),
        "surface_body_sentence_count": int(sig.get("body_sentence_count") or 0),
        "surface_line_role_sequence": list(sig.get("line_role_sequence") or []),
        "surface_connector_key_sequence": list(sig.get("connector_key_sequence") or []),
        "surface_predicate_key_sequence": list(sig.get("predicate_key_sequence") or []),
        "surface_ending_key_sequence": list(sig.get("ending_key_sequence") or []),
        "surface_relation_marker_key_sequence": list(sig.get("relation_marker_key_sequence") or []),
        "surface_opening_family_key": sig.get("opening_family_key", "none"),
        "surface_generic_center_phrase_count": int(sig.get("generic_center_phrase_count") or 0),
        "generic_center_phrase_count": int(sig.get("generic_center_phrase_count") or 0),
        "surface_same_connector_run_max": int(sig.get("same_connector_run_max") or 0),
        "same_connector_run_max": int(sig.get("same_connector_run_max") or 0),
        "surface_same_connector_family_count": int(sig.get("same_connector_family_count") or 0),
        "surface_same_connector_repetition_count": int(sig.get("same_connector_repetition_count") or 0),
        "same_connector_repetition_count": int(sig.get("same_connector_repetition_count") or 0),
        "surface_same_predicate_family_count": int(sig.get("same_predicate_family_count") or 0),
        "same_predicate_family_count": int(sig.get("same_predicate_family_count") or 0),
        "surface_observation_predicate_family_count": int(sig.get("observation_predicate_family_count") or 0),
        "surface_same_ending_family_count": int(sig.get("same_ending_family_count") or 0),
        "same_ending_family_count": int(sig.get("same_ending_family_count") or 0),
        "surface_malformed_nominalization_risk": bool(sig.get("malformed_nominalization_risk")),
        "malformed_nominalization_risk": bool(sig.get("malformed_nominalization_risk")),
        "surface_raw_echo_risk": bool(sig.get("raw_echo_risk")),
        "raw_echo_risk": bool(sig.get("raw_echo_risk")),
        "surface_grammar_warning_codes": list(sig.get("surface_grammar_warning_codes") or sig.get("grammar_warning_codes") or []),
        "grammar_warning_codes": list(sig.get("grammar_warning_codes") or []),
        "phrase_unit_grammar_warning_codes": list(sig.get("phrase_unit_grammar_warning_codes") or sig.get("grammar_warning_codes") or []),
        "phrase_unit_grammar_normalizer_version": sig.get("phrase_unit_grammar_normalizer_version") or PHRASE_UNIT_GRAMMAR_NORMALIZER_VERSION,
        "step8_phrase_unit_grammar_normalizer_connected": bool(sig.get("step8_phrase_unit_grammar_normalizer_connected", True)),
        "surface_grammar_warning_count": int(sig.get("surface_grammar_warning_count") or sig.get("grammar_warning_count") or len(sig.get("grammar_warning_codes") or [])),
        "grammar_warning_count": int(sig.get("grammar_warning_count") or len(sig.get("grammar_warning_codes") or [])),
        "surface_template_major": bool(sig.get("surface_template_major", sig.get("template_major"))),
        "template_major": bool(sig.get("template_major")),
        "grammar_major": bool(sig.get("grammar_major")),
        "surface_major_reasons": list(sig.get("surface_major_reasons") or sig.get("template_major_reasons") or []),
        "template_major_reasons": list(sig.get("template_major_reasons") or sig.get("surface_major_reasons") or []),
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
    }
    assert_surface_quality_signature_meta_only(fields, source="surface_quality_signature_scorecard_event")
    return fields


def dump_surface_quality_signature(signature: Mapping[str, Any]) -> str:
    data = coerce_surface_quality_signature_meta(signature) or dict(signature or {})
    data["raw_input_included"] = False
    data["raw_text_included"] = False
    data["input_text_included"] = False
    data["comment_text_included"] = False
    data["comment_text_body_included"] = False
    assert_surface_quality_signature_meta_only(data)
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


__all__ = [
    "SURFACE_QUALITY_SIGNATURE_HASH_PREFIX",
    "SURFACE_QUALITY_SIGNATURE_SOURCE",
    "SURFACE_QUALITY_SIGNATURE_STEP",
    "SURFACE_QUALITY_SIGNATURE_VERSION",
    "SurfaceQualitySignatureError",
    "assert_surface_quality_signature_meta_only",
    "build_surface_quality_signature",
    "coerce_surface_quality_signature_meta",
    "dump_surface_quality_signature",
    "normalize_surface_quality_signature_from_meta",
    "normalize_surface_signature_to_scorecard_event",
    "surface_quality_signature_from_meta",
]
