# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase 6 meta-only detector for mirror-only EmlisAI surfaces.

The detector inspects an already-realized visible surface only in memory, then
returns a sanitized report.  It is intentionally not a writer: it does not
rewrite ``comment_text``, does not add public response keys, and does not retain
raw user input or the displayed body.  Its job is to mark cases where enough
input material exists, but the surface ends at summary / restatement / generic
empathy instead of reflecting a safe relation or insight delta.
"""

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
import json
import re
from typing import Any, Final

MIRROR_ONLY_SURFACE_DETECTOR_VERSION: Final = "cocolon.emlis.mirror_only_surface_detector.v1"
MIRROR_ONLY_SURFACE_DETECTOR_STEP: Final = "Phase6_Mirror_Only_Surface_Detector"
MIRROR_ONLY_SURFACE_DETECTOR_SOURCE: Final = "Cocolon_EmlisAI_ProductReadFeel_Phase6_MirrorOnlySurfaceDetector"
MIRROR_ONLY_SURFACE_SCORECARD_FIELDS_VERSION: Final = "cocolon.emlis.mirror_only_surface_detector.scorecard_fields.v1"
MIRROR_ONLY_SURFACE_SUMMARY_VERSION: Final = "cocolon.emlis.mirror_only_surface_detector.summary.v1"

VERDICT_REPAIR_REQUIRED: Final = "REPAIR_REQUIRED"
VERDICT_YELLOW: Final = "YELLOW"
VERDICT_PASS: Final = "PASS"

FAMILY_LOW_INFORMATION_SHORT: Final = "low_information_short"
FAMILY_DAILY_UNPLEASANT: Final = "daily_unpleasant"
FAMILY_DAILY_POSITIVE: Final = "daily_positive"
FAMILY_POSITIVE_ONLY: Final = "positive_only"
FAMILY_LONG_MEANING_ARC: Final = "long_meaning_arc"
FAMILY_STRUCTURE_QUESTION: Final = "structure_question"
FAMILY_SELF_UNDERSTANDING_FOLLOW: Final = "self_understanding_follow"
FAMILY_INPUT_SELF_REPORT_ONLY_FAILURE: Final = "input_self_report_only_failure"
FAMILY_SELF_DENIAL: Final = "self_denial"
FAMILY_MIXED_EMOTION: Final = "mixed_emotion"
FAMILY_UNCERTAINTY: Final = "uncertainty"
FAMILY_RELATIONSHIP_BOUNDARY: Final = "relationship_boundary"
FAMILY_UNCLASSIFIED: Final = "unclassified"

STRICT_MIRROR_ONLY_FAMILIES: Final[frozenset[str]] = frozenset(
    {
        FAMILY_LONG_MEANING_ARC,
        FAMILY_STRUCTURE_QUESTION,
        FAMILY_SELF_UNDERSTANDING_FOLLOW,
        FAMILY_INPUT_SELF_REPORT_ONLY_FAILURE,
    }
)
LOW_INFORMATION_FAMILIES: Final[frozenset[str]] = frozenset({FAMILY_LOW_INFORMATION_SHORT, "low_information"})
LIGHT_RECEPTION_FAMILIES: Final[frozenset[str]] = frozenset(
    {
        FAMILY_LOW_INFORMATION_SHORT,
        FAMILY_DAILY_UNPLEASANT,
        FAMILY_DAILY_POSITIVE,
        FAMILY_POSITIVE_ONLY,
    }
)
DAILY_RECEPTION_FAMILIES: Final[frozenset[str]] = frozenset(
    {FAMILY_DAILY_UNPLEASANT, FAMILY_DAILY_POSITIVE, FAMILY_POSITIVE_ONLY}
)

_FAMILY_ALIASES: Final[dict[str, str]] = {
    "low_information": FAMILY_LOW_INFORMATION_SHORT,
    "low_info": FAMILY_LOW_INFORMATION_SHORT,
    "low_information_short": FAMILY_LOW_INFORMATION_SHORT,
    "daily_unpleasant": FAMILY_DAILY_UNPLEASANT,
    "daily_unpleasant_reception": FAMILY_DAILY_UNPLEASANT,
    "anger_hurt": FAMILY_DAILY_UNPLEASANT,
    "relationship_boundary": FAMILY_RELATIONSHIP_BOUNDARY,
    "daily_positive": FAMILY_DAILY_POSITIVE,
    "daily_positive_reception": FAMILY_DAILY_POSITIVE,
    "positive_recovery": FAMILY_DAILY_POSITIVE,
    "positive_only": FAMILY_POSITIVE_ONLY,
    "self_denial": FAMILY_SELF_DENIAL,
    "self_denial_support": FAMILY_SELF_DENIAL,
    "uncertainty": FAMILY_UNCERTAINTY,
    "uncertainty_support": FAMILY_UNCERTAINTY,
    "mixed_emotion": FAMILY_MIXED_EMOTION,
    "long_meaning_arc": FAMILY_LONG_MEANING_ARC,
    "long_arc_multiple_core": FAMILY_LONG_MEANING_ARC,
    "structure_question": FAMILY_STRUCTURE_QUESTION,
    "structure_question_observation": FAMILY_STRUCTURE_QUESTION,
    "self_understanding_follow": FAMILY_SELF_UNDERSTANDING_FOLLOW,
    "input_self_report_only_failure": FAMILY_INPUT_SELF_REPORT_ONLY_FAILURE,
    "self_report_only_failure": FAMILY_INPUT_SELF_REPORT_ONLY_FAILURE,
}

_TEXT_PAYLOAD_KEYS: Final[frozenset[str]] = frozenset(
    {
        "raw_input",
        "rawInput",
        "raw_text",
        "rawText",
        "source_text",
        "sourceText",
        "input",
        "input_text",
        "inputText",
        "user_input",
        "userInput",
        "memo",
        "memo_text",
        "memoText",
        "memo_action",
        "memoAction",
        "emotion_details",
        "current_input",
        "currentInput",
        "comment_text",
        "commentText",
        "input_feedback_comment",
        "inputFeedbackComment",
        "public_comment_text",
        "candidate_comment_text",
        "reply_text",
        "replyText",
        "surface_text",
        "surfaceText",
        "visible_text",
        "visibleText",
        "realized_text",
        "display_text",
        "candidate_body",
        "body",
        "text",
    }
)
_FORBIDDEN_TRUE_FLAGS: Final[tuple[str, ...]] = (
    "raw_input_included",
    "raw_text_included",
    "input_text_included",
    "comment_text_included",
    "comment_text_body_included",
    "candidate_body_included",
    "comment_text_generated",
    "comment_text_key_written",
    "comment_text_written_by_detector",
    "comment_text_written_by_scorecard",
    "public_response_key_added",
    "public_response_key_change",
    "response_shape_changed",
    "api_route_changed",
    "db_physical_name_changed",
    "rn_visible_contract_changed",
    "rn_visible_title_changed",
    "display_gate_relaxed",
    "grounding_gate_relaxed",
    "reader_gate_relaxed",
    "template_gate_relaxed",
    "gate_relaxed",
    "product_gate_ready",
    "product_gate_reached",
    "product_gate_public_release_applied",
    "public_release_applied",
    "product_quality_released",
    "external_ai_used",
    "local_llm_used",
)

_SURFACE_BODY_KEYS: Final[tuple[str, ...]] = (
    "comment_text",
    "commentText",
    "public_comment_text",
    "candidate_comment_text",
    "reply_text",
    "replyText",
    "surface_text",
    "surfaceText",
    "visible_text",
    "visibleText",
    "realized_text",
    "display_text",
    "candidate_body",
    "body",
    "text",
)

_SENTENCE_SPLIT_RE: Final = re.compile(r"[。！？!?]+|[\r\n]+")
_LABEL_RE: Final = re.compile(r"(?:見えたこと|Emlisから)\s*[:：]")
_SPACE_RE: Final = re.compile(r"\s+")

_RELATION_PATTERNS: Final[tuple[tuple[str, re.Pattern[str]], ...]] = (
    ("relation_connection", re.compile(r"つなが|繋が|結び|関係|影響")),
    ("relation_overlap", re.compile(r"重な|同時|同じ時間|一緒に|並ん")),
    ("relation_conflict", re.compile(r"ぶつか|衝突|矛盾|板挟み|引っかか|詰まり")),
    ("relation_gap", re.compile(r"差|距離|ギャップ|隔たり")),
    ("relation_desire_blockage", re.compile(r"変えたい|進みたい|したい.{0,18}(?:できない|動けない)|できない.{0,18}したい")),
    ("relation_residue", re.compile(r"残って|残り|残る|余韻|引きず")),
    ("relation_value_line", re.compile(r"大事な線|大切な線|軽く扱|境界|期待|傷つき")),
    ("relation_effort", re.compile(r"努力|向き合|試し|言葉にして|悩んで|考えよう")),
    ("relation_positive_change", re.compile(r"変化|回復|安心|ほっと|戻って|動いた|小さな達成")),
)
_INSIGHT_SURFACE_PATTERNS: Final[tuple[tuple[str, re.Pattern[str]], ...]] = (
    ("soft_miemasu", re.compile(r"ように見え|ようにも見え|見えて")),
    ("soft_kamoshire", re.compile(r"かもしれ|のかもしれ")),
    ("soft_dewanai", re.compile(r"ではないでしょうか|に近い状態")),
    ("structure_word", re.compile(r"構造|位置関係|関係として|入口|背景ではなく")),
    ("insight_seed", re.compile(r"ただ.{0,18}ではなく|だけではなく|分だけ|そのぶん|その分")),
)
_SUMMARY_ONLY_PATTERNS: Final[tuple[tuple[str, re.Pattern[str]], ...]] = (
    ("summary_dattandesune", re.compile(r"(?:だった|あった|感じた|思った|起きた)んですね")),
    ("summary_nanodesune", re.compile(r"(?:なのですね|なんですね|ですね$)")),
    ("summary_sounandesune", re.compile(r"そうだったんですね|そうなんですね")),
    ("summary_teimasune", re.compile(r"(?:している|感じている|思っている|残っている)んですね")),
    ("summary_recap", re.compile(r"(?:ことが|気持ちが|状態が).{0,18}(?:あった|あります|出ている)んですね")),
)
_GENERIC_EMPATHY_PATTERNS: Final[tuple[tuple[str, re.Pattern[str]], ...]] = (
    ("generic_tsurai", re.compile(r"つらかったですね|大変でしたね|しんどかったですね|苦しかったですね")),
    ("generic_daijoubu", re.compile(r"大丈夫|無理しないで|ゆっくり休んで|自分を責めないで")),
    ("generic_yokatta", re.compile(r"よかったですね|嬉しいですね|素敵ですね|安心しましたね")),
    ("generic_otsukare", re.compile(r"お疲れさま|頑張りましたね|よく頑張")),
)
_EXPLICIT_MIRROR_REASON_MARKERS: Final[tuple[str, ...]] = (
    "mirror_only",
    "mirror-only",
    "self_report_only",
    "input_self_report_only",
    "summary_only",
    "rephrase_only",
    "recap_only",
    "input_material_relation_missing",
    "structure_relation_missing",
    "insight_missing",
    "insight_delta_missing",
)
_DIMENSION_ALIASES: Final[dict[str, str]] = {
    "insight": "insight_delta",
    "insight_delta": "insight_delta",
    "structure_insight_delta": "insight_delta",
    "read_feeling": "read_feeling",
    "read_feeling_score": "read_feeling",
    "self_report_retention": "self_report_retention",
    "state_structure_retention": "state_structure_retention",
    "relation_retention": "state_structure_retention",
    "follow_depth": "follow_depth",
}
_VERDICT_SCORES: Final[dict[str, float]] = {
    "green": 1.0,
    "g": 1.0,
    "pass": 1.0,
    "passed": 1.0,
    "ok": 1.0,
    "product_pass": 1.0,
    "yellow": 0.65,
    "y": 0.65,
    "warn": 0.65,
    "warning": 0.65,
    "repair_required": 0.4,
    "repair": 0.4,
    "red": 0.0,
    "r": 0.0,
    "fail": 0.0,
    "failed": 0.0,
    "ng": 0.0,
}


class MirrorOnlySurfaceDetectorMetaOnlyError(ValueError):
    """Raised when a Phase 6 detector report leaks text or mutates contracts."""


def _clean(value: Any) -> str:
    if value is None or isinstance(value, (Mapping, list, tuple, set)):
        return ""
    return _SPACE_RE.sub(" ", str(value).replace("\u3000", " ")).strip()


def _safe_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    return {}


def _listify(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    if isinstance(value, (tuple, set)):
        return list(value)
    return [value]


def _dedupe(values: Iterable[Any] | Any | None) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in _listify(values):
        text = _clean(value)
        if text and text not in seen:
            seen.add(text)
            out.append(text)
    return out


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return None


def _score_from_verdict(value: Any) -> float | None:
    text = _clean(value).lower().replace(" ", "_").replace("-", "_")
    if text in _VERDICT_SCORES:
        return _VERDICT_SCORES[text]
    return _safe_float(value)


def _contains_text_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key) in _TEXT_PAYLOAD_KEYS:
                return True
            if _contains_text_payload_key(item):
                return True
        return False
    if isinstance(value, (list, tuple, set)):
        return any(_contains_text_payload_key(item) for item in value)
    return False


def _strip_text_payload_keys(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _strip_text_payload_keys(item)
            for key, item in value.items()
            if str(key) not in _TEXT_PAYLOAD_KEYS
        }
    if isinstance(value, list):
        return [_strip_text_payload_keys(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_strip_text_payload_keys(item) for item in value)
    if isinstance(value, set):
        return {_strip_text_payload_keys(item) for item in value}
    return value


def assert_mirror_only_surface_detector_meta_only(
    payload: Mapping[str, Any] | Sequence[Any],
    *,
    source: str = "mirror_only_surface_detector",
) -> None:
    if _contains_text_payload_key(payload):
        raise MirrorOnlySurfaceDetectorMetaOnlyError(f"{source}: comment_text/raw input body must not be retained")
    if isinstance(payload, Mapping):
        for flag in _FORBIDDEN_TRUE_FLAGS:
            if payload.get(flag) is True:
                raise MirrorOnlySurfaceDetectorMetaOnlyError(f"{source}: forbidden true flag {flag}")
        for item in payload.values():
            if isinstance(item, (Mapping, list, tuple)):
                assert_mirror_only_surface_detector_meta_only(item, source=source)
    elif isinstance(payload, (list, tuple)):
        for item in payload:
            if isinstance(item, (Mapping, list, tuple)):
                assert_mirror_only_surface_detector_meta_only(item, source=source)


def _family_from_record(record: Mapping[str, Any], explicit_family: str = "") -> str:
    for raw in (
        explicit_family,
        record.get("product_readfeel_family"),
        record.get("readfeel_family"),
        record.get("fixture_family"),
        record.get("case_family"),
        record.get("family"),
        record.get("coverage_group"),
        record.get("fixture_group"),
        record.get("observation_fixture_group"),
        record.get("reception_mode"),
        record.get("mode"),
    ):
        key = _clean(raw).lower()
        if not key:
            continue
        return _FAMILY_ALIASES.get(key, key)
    return FAMILY_UNCLASSIFIED


def _surface_body_from_record(record: Mapping[str, Any], explicit_body: Any = None) -> str:
    explicit = _clean(explicit_body)
    if explicit:
        return explicit
    for key in _SURFACE_BODY_KEYS:
        value = _clean(record.get(key))
        if value:
            return value
    return ""


def _sentences(surface: str) -> list[str]:
    return [part.strip() for part in _SENTENCE_SPLIT_RE.split(surface) if part.strip()]


def _pattern_hits(surface: str, patterns: Sequence[tuple[str, re.Pattern[str]]]) -> tuple[int, list[str]]:
    codes: list[str] = []
    count = 0
    for code, pattern in patterns:
        matches = pattern.findall(surface)
        if matches:
            codes.append(code)
            count += len(matches)
    return count, codes


def _reason_values(record: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    for key in (
        "mirror_only_reason_codes",
        "mirror_only_detector_reason_codes",
        "reason_codes",
        "top_rejection_reasons",
        "rejection_reasons",
        "repair_reasons",
        "red_flags",
        "qa_gaps",
        "release_blockers",
        "failure_reasons",
        "inventory_reasons",
    ):
        value = record.get(key)
        if isinstance(value, Mapping):
            reasons.extend(value.keys())
        else:
            reasons.extend(_dedupe(value))
    nested = _safe_mapping(record.get("mirror_only_surface_detection") or record.get("phase6_mirror_only_surface_detection"))
    if nested:
        reasons.extend(_dedupe(nested.get("mirror_only_reason_codes")))
    for key in ("reason_code", "primary_reason", "v1_repair_reason", "v2_backlog_reason"):
        text = _clean(record.get(key))
        if text:
            reasons.append(text)
    return _dedupe(reasons)


def _has_explicit_mirror_marker(reasons: Iterable[str]) -> bool:
    return any(any(marker in reason.lower() for marker in _EXPLICIT_MIRROR_REASON_MARKERS) for reason in reasons)


def _material_flag_count(flags: Mapping[str, Any]) -> int:
    return sum(
        1
        for key in (
            "memo_present",
            "memo_action_present",
            "selected_emotions_present",
            "emotion_details_present",
            "category_present",
            "event_fact_present",
            "explicit_reaction_present",
            "long_input",
            "structure_question_requested",
            "self_understanding_present",
        )
        if flags.get(key) is True
    )


def _material_sufficient(record: Mapping[str, Any], flags: Mapping[str, Any], family: str) -> bool:
    if family in LOW_INFORMATION_FAMILIES and record.get("mirror_only_strict_for_low_information") is not True:
        return False
    if family in STRICT_MIRROR_ONLY_FAMILIES:
        return True
    if any(
        flags.get(key) is True
        for key in (
            "long_input",
            "structure_question_requested",
            "self_understanding_present",
            "memo_action_present",
            "emotion_details_present",
        )
    ):
        if family in DAILY_RECEPTION_FAMILIES and not (
            flags.get("long_input") is True or flags.get("structure_question_requested") is True
        ):
            return False
        return True
    slot_count = max(
        _safe_int(record.get("material_slot_count"), 0),
        _safe_int(record.get("evidence_slot_count"), 0),
        len(_dedupe(record.get("source_field_ids") or record.get("evidence_slot_ids"))),
        _material_flag_count(flags),
    )
    if family in DAILY_RECEPTION_FAMILIES:
        return slot_count >= 4 and bool(record.get("mirror_only_detection_strict") is True)
    return slot_count >= 3


def _signature_meta(record: Mapping[str, Any]) -> dict[str, Any]:
    nested = _safe_mapping(record.get("surface_quality_signature") or record.get("step2_surface_quality_signature"))
    if nested:
        return nested
    return {}


def _signature_relation_count(record: Mapping[str, Any]) -> int:
    signature = _signature_meta(record)
    keys = _dedupe(
        record.get("surface_relation_marker_key_sequence")
        or record.get("relation_marker_key_sequence")
        or signature.get("relation_marker_key_sequence")
        or signature.get("surface_relation_marker_key_sequence")
    )
    return len([key for key in keys if key and key != "none"])


def _signature_sentence_count(record: Mapping[str, Any]) -> int:
    signature = _signature_meta(record)
    return max(
        _safe_int(record.get("surface_body_sentence_count"), 0),
        _safe_int(record.get("body_sentence_count"), 0),
        _safe_int(signature.get("body_sentence_count"), 0),
        _safe_int(signature.get("surface_body_sentence_count"), 0),
    )


def _signature_ready(record: Mapping[str, Any]) -> bool:
    signature = _signature_meta(record)
    return bool(
        record.get("surface_quality_signature_ready")
        or record.get("step2_surface_quality_signature_ready")
        or record.get("step2_surface_signature_measurement_ready")
        or signature.get("surface_quality_signature_ready")
        or signature.get("step2_surface_quality_signature_ready")
        or signature.get("surface_signature_id")
    )


def _rating_scores(record: Mapping[str, Any]) -> dict[str, float | None]:
    ratings = _safe_mapping(record.get("ratings") or record.get("dimension_ratings"))
    if not ratings:
        ratings = {key: value for key, value in record.items() if _DIMENSION_ALIASES.get(str(key).strip().lower())}
    out: dict[str, float | None] = {}
    for raw_key, raw_value in ratings.items():
        dimension = _DIMENSION_ALIASES.get(str(raw_key).strip().lower())
        if not dimension:
            continue
        out[dimension] = _score_from_verdict(raw_value)
    return out


def _existing_detector_report(record: Mapping[str, Any]) -> dict[str, Any]:
    for key in (
        "phase6_mirror_only_surface_detection",
        "mirror_only_surface_detection",
        "phase6_mirror_only_detector_report",
        "mirror_only_detector_report",
    ):
        nested = _safe_mapping(record.get(key))
        if nested:
            return nested
    return {}


def detect_mirror_only_surface(
    record: Mapping[str, Any] | None = None,
    *,
    comment_text: str | None = None,
    surface_text: str | None = None,
    product_readfeel_family: str = "",
    input_material_flags: Mapping[str, Any] | None = None,
    source_field_ids: Sequence[str] | None = None,
    evidence_slot_count: int | None = None,
    material_slot_count: int | None = None,
    run_id: str = "",
) -> dict[str, Any]:
    """Detect mirror-only output and return a meta-only Phase 6 report.

    ``comment_text`` / ``surface_text`` may be supplied for in-memory inspection;
    neither is retained in the returned report.  When no display body, signature,
    rating, or explicit mirror-only marker exists in meta, the detector stays
    silent while still returning a schema-valid meta report.
    """

    source = _safe_mapping(record)
    existing = _existing_detector_report(source)
    if existing and existing.get("schema_version") == MIRROR_ONLY_SURFACE_DETECTOR_VERSION:
        data = _strip_text_payload_keys(existing)
        data = dict(data)
        data.setdefault("raw_input_included", False)
        data.setdefault("raw_text_included", False)
        data.setdefault("comment_text_included", False)
        data.setdefault("comment_text_body_included", False)
        assert_mirror_only_surface_detector_meta_only(data, source="existing_mirror_only_surface_detector_report")
        return data

    explicit_body = comment_text if comment_text is not None else surface_text
    surface = _surface_body_from_record(source, explicit_body)
    family = _family_from_record(source, product_readfeel_family)
    flags = _safe_mapping(source.get("input_material_flags") or source.get("material_flags"))
    flags.update(_safe_mapping(input_material_flags))
    if source_field_ids is not None:
        source = {**source, "source_field_ids": list(source_field_ids)}
    if evidence_slot_count is not None:
        source = {**source, "evidence_slot_count": evidence_slot_count}
    if material_slot_count is not None:
        source = {**source, "material_slot_count": material_slot_count}

    reasons = _reason_values(source)
    explicit_mirror = bool(
        source.get("mirror_only_detected") is True
        or source.get("self_report_only_detected") is True
        or source.get("input_self_report_only_detected") is True
        or _has_explicit_mirror_marker(reasons)
    )
    sentences_from_body = _sentences(surface)
    sentence_count = max(len(sentences_from_body), _signature_sentence_count(source))
    section_count = len(_LABEL_RE.findall(surface))
    relation_count_from_body, relation_codes = _pattern_hits(surface, _RELATION_PATTERNS)
    insight_count_from_body, insight_codes = _pattern_hits(surface, _INSIGHT_SURFACE_PATTERNS)
    summary_count, summary_codes = _pattern_hits(surface, _SUMMARY_ONLY_PATTERNS)
    generic_empathy_count, generic_empathy_codes = _pattern_hits(surface, _GENERIC_EMPATHY_PATTERNS)
    signature_relation_count = _signature_relation_count(source)
    relation_marker_count = max(
        relation_count_from_body,
        signature_relation_count,
        _safe_int(source.get("relation_marker_count"), 0),
        _safe_int(source.get("surface_relation_marker_count"), 0),
        _safe_int(source.get("relation_candidate_surface_count"), 0),
    )
    insight_marker_count = max(
        insight_count_from_body,
        _safe_int(source.get("insight_marker_count"), 0),
        _safe_int(source.get("surface_insight_marker_count"), 0),
        _safe_int(source.get("insight_seed_surface_count"), 0),
    )
    scores = _rating_scores(source)
    insight_delta_score = scores.get("insight_delta")
    insight_delta_below_target = bool(insight_delta_score is not None and insight_delta_score < 0.90)
    material_sufficient = _material_sufficient(source, flags, family)
    low_information_family = family in LOW_INFORMATION_FAMILIES
    daily_reception_family = family in DAILY_RECEPTION_FAMILIES
    strict_family = family in STRICT_MIRROR_ONLY_FAMILIES

    reason_codes: list[str] = []
    if explicit_mirror:
        reason_codes.append("explicit_mirror_only_marker")
    if material_sufficient:
        reason_codes.append("sufficient_input_material")
    if strict_family:
        reason_codes.append("strict_structure_family")
    if low_information_family:
        reason_codes.append("low_information_over_detection_guard")
    if daily_reception_family:
        reason_codes.append("daily_reception_light_receive_guard")
    if relation_marker_count <= 0:
        reason_codes.append("relation_marker_absent")
    if insight_marker_count <= 0:
        reason_codes.append("insight_marker_absent")
    if summary_count > 0:
        reason_codes.append("summary_or_recap_surface_marker")
    if generic_empathy_count > 0:
        reason_codes.append("generic_empathy_surface_marker")
    if insight_delta_below_target:
        reason_codes.append("insight_delta_below_structure_target")

    # Low-information and ordinary daily reception can be intentionally light;
    # do not label them mirror-only unless the caller explicitly opts into strict
    # handling.  This keeps Phase 6 from undoing the Phase 5 surface repairs.
    protected_light_reception = bool(
        (low_information_family or daily_reception_family)
        and not strict_family
        and source.get("mirror_only_detection_strict") is not True
    )
    surface_available = bool(surface) or _signature_ready(source) or sentence_count > 0
    no_relation_or_insight = relation_marker_count <= 0 and insight_marker_count <= 0
    summary_like = summary_count > 0 or generic_empathy_count > 0

    mirror_only_detected = False
    if explicit_mirror and not protected_light_reception:
        mirror_only_detected = True
    elif surface_available and material_sufficient and no_relation_or_insight and not protected_light_reception:
        if strict_family or summary_like or sentence_count <= 2:
            mirror_only_detected = True
    elif insight_delta_below_target and material_sufficient and strict_family and no_relation_or_insight and not protected_light_reception:
        mirror_only_detected = True
    elif family == FAMILY_INPUT_SELF_REPORT_ONLY_FAILURE and not protected_light_reception:
        mirror_only_detected = True

    if mirror_only_detected:
        reason_codes.extend(["mirror_only", "mirror_only_detected"])
        if strict_family or material_sufficient:
            v1_verdict = VERDICT_REPAIR_REQUIRED
            v1_action = "repair_v1_surface_or_relation_seed"
        else:
            v1_verdict = VERDICT_YELLOW
            v1_action = "monitor_readfeel_weakness"
    else:
        v1_verdict = VERDICT_PASS
        v1_action = "no_mirror_only_action"

    v2_gap = bool((mirror_only_detected or insight_delta_below_target) and material_sufficient and not protected_light_reception)
    if v2_gap:
        reason_codes.append("v2_insight_delta_gap")

    report = {
        "version": MIRROR_ONLY_SURFACE_DETECTOR_VERSION,
        "schema_version": MIRROR_ONLY_SURFACE_DETECTOR_VERSION,
        "scorecard_fields_version": MIRROR_ONLY_SURFACE_SCORECARD_FIELDS_VERSION,
        "source": MIRROR_ONLY_SURFACE_DETECTOR_SOURCE,
        "step": MIRROR_ONLY_SURFACE_DETECTOR_STEP,
        "source_step": MIRROR_ONLY_SURFACE_DETECTOR_STEP,
        "run_id": _clean(run_id or source.get("run_id")),
        "phase6_mirror_only_detector_ready": True,
        "mirror_only_detector_ready": True,
        "product_readfeel_family": family,
        "input_material_sufficient_for_insight": material_sufficient,
        "strict_mirror_only_family": strict_family,
        "low_information_family": low_information_family,
        "daily_reception_family": daily_reception_family,
        "light_reception_family": family in LIGHT_RECEPTION_FAMILIES,
        "protected_light_reception": protected_light_reception,
        "surface_body_seen_for_in_memory_detection": bool(surface),
        "surface_signature_seen_for_detection": bool(_signature_ready(source)),
        "surface_body_retained": False,
        "surface_sentence_count": sentence_count,
        "surface_section_label_count": section_count,
        "relation_marker_count": relation_marker_count,
        "signature_relation_marker_count": signature_relation_count,
        "insight_marker_count": insight_marker_count,
        "summary_only_marker_count": summary_count,
        "generic_empathy_marker_count": generic_empathy_count,
        "relation_marker_codes": relation_codes,
        "insight_marker_codes": insight_codes,
        "summary_only_marker_codes": summary_codes,
        "generic_empathy_marker_codes": generic_empathy_codes,
        "insight_delta_score": insight_delta_score,
        "insight_delta_below_structure_target": insight_delta_below_target,
        "mirror_only_detected": mirror_only_detected,
        "self_report_only_detected": mirror_only_detected,
        "v1_verdict_hint": v1_verdict,
        "v1_classification": v1_verdict,
        "v1_action": v1_action,
        "v1_yellow_or_repair_connected": mirror_only_detected and v1_verdict in {VERDICT_YELLOW, VERDICT_REPAIR_REQUIRED},
        "v2_insight_delta_gap": v2_gap,
        "insight_delta_gap": v2_gap,
        "v2_action": "structure_insight_delta_backlog" if v2_gap else "not_required_for_phase6",
        "mirror_only_reason_codes": _dedupe(reason_codes),
        "meta_only_detection": True,
        "exact_comment_text_required": False,
        "runtime_branching_uses_fixture_strings": False,
        "fixture_text_used_for_runtime_branching": False,
        "comment_text_generated": False,
        "comment_text_key_written": False,
        "comment_text_written_by_detector": False,
        "comment_text_written_by_scorecard": False,
        "public_response_key_added": False,
        "public_response_key_change": False,
        "response_shape_changed": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "template_gate_relaxed": False,
        "gate_relaxed": False,
        "product_gate_ready": False,
        "product_gate_reached": False,
        "product_gate_public_release_applied": False,
        "public_release_applied": False,
        "product_quality_released": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "input_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "external_ai_used": False,
        "local_llm_used": False,
    }
    assert_mirror_only_surface_detector_meta_only(report, source="mirror_only_surface_detector_report")
    return report


build_mirror_only_surface_detection = detect_mirror_only_surface


def normalize_mirror_only_surface_to_scorecard_event(report: Mapping[str, Any] | None) -> dict[str, Any]:
    """Project a Phase 6 detector report to safe scorecard event fields."""

    data = _safe_mapping(_strip_text_payload_keys(_safe_mapping(report)))
    if not data:
        data = detect_mirror_only_surface({})
    fields = {
        "mirror_only_surface_detector_version": _clean(data.get("version")) or MIRROR_ONLY_SURFACE_DETECTOR_VERSION,
        "mirror_only_surface_detector_step": _clean(data.get("step")) or MIRROR_ONLY_SURFACE_DETECTOR_STEP,
        "phase6_mirror_only_detector_ready": bool(data.get("phase6_mirror_only_detector_ready") or data.get("mirror_only_detector_ready")),
        "mirror_only_detector_ready": bool(data.get("mirror_only_detector_ready") or data.get("phase6_mirror_only_detector_ready")),
        "mirror_only_detected": bool(data.get("mirror_only_detected")),
        "self_report_only_detected": bool(data.get("self_report_only_detected") or data.get("mirror_only_detected")),
        "mirror_only_v1_verdict_hint": _clean(data.get("v1_verdict_hint")),
        "mirror_only_v1_classification": _clean(data.get("v1_classification") or data.get("v1_verdict_hint")),
        "mirror_only_v1_action": _clean(data.get("v1_action")),
        "mirror_only_v1_yellow_or_repair_connected": bool(data.get("v1_yellow_or_repair_connected")),
        "mirror_only_v2_insight_delta_gap": bool(data.get("v2_insight_delta_gap") or data.get("insight_delta_gap")),
        "insight_delta_gap": bool(data.get("v2_insight_delta_gap") or data.get("insight_delta_gap")),
        "mirror_only_v2_action": _clean(data.get("v2_action")),
        "mirror_only_reason_codes": _dedupe(data.get("mirror_only_reason_codes")),
        "mirror_only_relation_marker_count": _safe_int(data.get("relation_marker_count"), 0),
        "mirror_only_signature_relation_marker_count": _safe_int(data.get("signature_relation_marker_count"), 0),
        "mirror_only_insight_marker_count": _safe_int(data.get("insight_marker_count"), 0),
        "mirror_only_summary_marker_count": _safe_int(data.get("summary_only_marker_count"), 0),
        "mirror_only_generic_empathy_marker_count": _safe_int(data.get("generic_empathy_marker_count"), 0),
        "mirror_only_input_material_sufficient_for_insight": bool(data.get("input_material_sufficient_for_insight")),
        "mirror_only_strict_family": bool(data.get("strict_mirror_only_family")),
        "mirror_only_low_information_family": bool(data.get("low_information_family")),
        "mirror_only_daily_reception_family": bool(data.get("daily_reception_family")),
        "mirror_only_protected_light_reception": bool(data.get("protected_light_reception")),
        "product_readfeel_family": _clean(data.get("product_readfeel_family")) or FAMILY_UNCLASSIFIED,
        "surface_body_retained": False,
        "comment_text_generated": False,
        "comment_text_key_written": False,
        "comment_text_written_by_detector": False,
        "comment_text_written_by_scorecard": False,
        "public_response_key_added": False,
        "public_response_key_change": False,
        "response_shape_changed": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "template_gate_relaxed": False,
        "gate_relaxed": False,
        "product_gate_ready": False,
        "product_gate_reached": False,
        "product_gate_public_release_applied": False,
        "public_release_applied": False,
        "product_quality_released": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "input_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "external_ai_used": False,
        "local_llm_used": False,
    }
    assert_mirror_only_surface_detector_meta_only(fields, source="mirror_only_surface_scorecard_fields")
    return fields


def normalize_mirror_only_surface_detector_to_scorecard_fields(
    report: Mapping[str, Any] | None,
) -> dict[str, Any]:
    return normalize_mirror_only_surface_to_scorecard_event(report)


def _report_for_event(event: Mapping[str, Any] | None, *, run_id: str = "") -> dict[str, Any]:
    source = _safe_mapping(event)
    existing = _existing_detector_report(source)
    if existing:
        return detect_mirror_only_surface({**source, "phase6_mirror_only_surface_detection": existing}, run_id=run_id)
    return detect_mirror_only_surface(source, run_id=run_id)


def enrich_events_with_mirror_only_surface_detection(
    events: Iterable[Mapping[str, Any] | None] | None = None,
    *,
    run_id: str = "",
) -> list[dict[str, Any]]:
    """Return scorecard events enriched with Phase 6 meta-only detector fields.

    The source body can be inspected by the detector, but the returned event is
    stripped of raw input and visible body keys before being passed to inventory
    or scorecards.
    """

    enriched: list[dict[str, Any]] = []
    for event in list(events or []):
        source = _safe_mapping(event)
        if not source:
            continue
        report = _report_for_event(source, run_id=run_id)
        fields = normalize_mirror_only_surface_to_scorecard_event(report)
        safe_source = _safe_mapping(_strip_text_payload_keys(source))
        safe_source["phase6_mirror_only_surface_detection"] = report
        safe_source["mirror_only_surface_detection"] = report
        safe_source.update(fields)
        # Keep Product Read Feel inventory compatibility aliases.
        safe_source["mirror_only_detected"] = bool(fields.get("mirror_only_detected"))
        safe_source["self_report_only_detected"] = bool(fields.get("self_report_only_detected"))
        if fields.get("mirror_only_v2_insight_delta_gap"):
            reasons = _dedupe(safe_source.get("reason_codes"))
            safe_source["reason_codes"] = _dedupe([*reasons, "mirror_only", "insight_delta_missing"])
        enriched.append(safe_source)
    return enriched


def build_mirror_only_surface_detector_summary(
    *,
    events: Iterable[Mapping[str, Any] | None] | None = None,
    reports: Iterable[Mapping[str, Any] | None] | None = None,
    run_id: str = "",
) -> dict[str, Any]:
    detector_reports: list[dict[str, Any]] = []
    for event in list(events or []):
        source = _safe_mapping(event)
        if not source:
            continue
        detector_reports.append(_report_for_event(source, run_id=run_id))
    for report in list(reports or []):
        data = _safe_mapping(report)
        if not data:
            continue
        detector_reports.append(detect_mirror_only_surface({"phase6_mirror_only_surface_detection": data}, run_id=run_id))

    family_counter: Counter[str] = Counter()
    family_detected_counter: Counter[str] = Counter()
    for report in detector_reports:
        family = _clean(report.get("product_readfeel_family")) or FAMILY_UNCLASSIFIED
        family_counter[family] += 1
        if report.get("mirror_only_detected") is True:
            family_detected_counter[family] += 1

    detected_reports = [report for report in detector_reports if report.get("mirror_only_detected") is True]
    v1_yellow_or_repair = [
        report
        for report in detector_reports
        if report.get("v1_classification") in {VERDICT_YELLOW, VERDICT_REPAIR_REQUIRED}
    ]
    v1_repair_required = [
        report
        for report in detector_reports
        if report.get("v1_classification") == VERDICT_REPAIR_REQUIRED
    ]
    v2_gaps = [report for report in detector_reports if report.get("v2_insight_delta_gap") is True]
    completion_conditions = {
        "mirror_only_detected_meta_only": True,
        "v1_yellow_or_repair_connected": True,
        "v2_insight_delta_gap_connected": True,
        "comment_text_body_retained": False,
        "low_information_over_detection_guarded": all(
            not (report.get("low_information_family") is True and report.get("mirror_only_detected") is True)
            or report.get("protected_light_reception") is False
            for report in detector_reports
        ),
        "daily_reception_light_receive_guarded": all(
            not (report.get("daily_reception_family") is True and report.get("mirror_only_detected") is True)
            or report.get("protected_light_reception") is False
            for report in detector_reports
        ),
    }
    phase6_ready = bool(
        completion_conditions["mirror_only_detected_meta_only"]
        and completion_conditions["v1_yellow_or_repair_connected"]
        and completion_conditions["v2_insight_delta_gap_connected"]
        and completion_conditions["comment_text_body_retained"] is False
    )
    summary = {
        "version": MIRROR_ONLY_SURFACE_SUMMARY_VERSION,
        "schema_version": MIRROR_ONLY_SURFACE_SUMMARY_VERSION,
        "detector_version": MIRROR_ONLY_SURFACE_DETECTOR_VERSION,
        "source": MIRROR_ONLY_SURFACE_DETECTOR_SOURCE,
        "step": MIRROR_ONLY_SURFACE_DETECTOR_STEP,
        "source_step": MIRROR_ONLY_SURFACE_DETECTOR_STEP,
        "run_id": _clean(run_id),
        "phase6_mirror_only_detector_ready": phase6_ready,
        "phase6_product_readfeel_mirror_only_detector_ready": phase6_ready,
        "product_readfeel_phase6_ready": phase6_ready,
        "completion_conditions": completion_conditions,
        "report_count": len(detector_reports),
        "evaluated_count": len(detector_reports),
        "mirror_only_detected_count": len(detected_reports),
        "mirror_only_v1_yellow_or_repair_connected_count": len(v1_yellow_or_repair),
        "mirror_only_v1_repair_required_count": len(v1_repair_required),
        "mirror_only_v2_insight_delta_gap_count": len(v2_gaps),
        "mirror_only_detected_families": sorted(family_detected_counter.keys()),
        "family_counts": dict(family_counter),
        "family_detected_counts": dict(family_detected_counter),
        "reports": detector_reports,
        "raw_input_included": False,
        "raw_text_included": False,
        "input_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "comment_text_generated": False,
        "comment_text_key_written": False,
        "comment_text_written_by_detector": False,
        "comment_text_written_by_scorecard": False,
        "public_response_key_added": False,
        "public_response_key_change": False,
        "response_shape_changed": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "template_gate_relaxed": False,
        "gate_relaxed": False,
        "product_gate_ready": False,
        "product_gate_reached": False,
        "product_gate_public_release_applied": False,
        "public_release_applied": False,
        "product_quality_released": False,
        "external_ai_used": False,
        "local_llm_used": False,
    }
    assert_mirror_only_surface_detector_meta_only(summary, source="mirror_only_surface_detector_summary")
    return summary


def normalize_mirror_only_surface_detector_summary_to_scorecard_fields(
    summary: Mapping[str, Any] | None,
) -> dict[str, Any]:
    data = _safe_mapping(summary)
    if not data:
        data = build_mirror_only_surface_detector_summary(events=[])
    assert_mirror_only_surface_detector_meta_only(data, source="mirror_only_surface_detector_summary_fields_source")
    fields = {
        "mirror_only_surface_detector_summary_version": _clean(data.get("version")) or MIRROR_ONLY_SURFACE_SUMMARY_VERSION,
        "mirror_only_surface_detector_version": _clean(data.get("detector_version")) or MIRROR_ONLY_SURFACE_DETECTOR_VERSION,
        "mirror_only_surface_detector_step": _clean(data.get("step")) or MIRROR_ONLY_SURFACE_DETECTOR_STEP,
        "phase6_mirror_only_detector_ready": bool(data.get("phase6_mirror_only_detector_ready")),
        "phase6_product_readfeel_mirror_only_detector_ready": bool(
            data.get("phase6_product_readfeel_mirror_only_detector_ready")
        ),
        "product_readfeel_phase6_ready": bool(data.get("product_readfeel_phase6_ready")),
        "product_readfeel_mirror_only_report_count": _safe_int(data.get("report_count"), 0),
        "product_readfeel_mirror_only_evaluated_count": _safe_int(data.get("evaluated_count"), 0),
        "product_readfeel_mirror_only_detected_count": _safe_int(data.get("mirror_only_detected_count"), 0),
        "product_readfeel_mirror_only_v1_yellow_or_repair_connected_count": _safe_int(
            data.get("mirror_only_v1_yellow_or_repair_connected_count"), 0
        ),
        "product_readfeel_mirror_only_v1_repair_required_count": _safe_int(
            data.get("mirror_only_v1_repair_required_count"), 0
        ),
        "product_readfeel_mirror_only_v2_insight_delta_gap_count": _safe_int(
            data.get("mirror_only_v2_insight_delta_gap_count"), 0
        ),
        "product_readfeel_mirror_only_detected_families": list(data.get("mirror_only_detected_families") or []),
        "product_readfeel_mirror_only_family_counts": dict(data.get("family_counts") or {}),
        "product_readfeel_mirror_only_family_detected_counts": dict(data.get("family_detected_counts") or {}),
        "raw_input_included": False,
        "raw_text_included": False,
        "input_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "comment_text_generated": False,
        "comment_text_key_written": False,
        "comment_text_written_by_detector": False,
        "comment_text_written_by_scorecard": False,
        "public_response_key_added": False,
        "public_response_key_change": False,
        "response_shape_changed": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "template_gate_relaxed": False,
        "gate_relaxed": False,
        "product_gate_ready": False,
        "product_gate_reached": False,
        "product_gate_public_release_applied": False,
        "public_release_applied": False,
        "product_quality_released": False,
    }
    assert_mirror_only_surface_detector_meta_only(fields, source="mirror_only_surface_detector_summary_fields")
    return fields


def dump_mirror_only_surface_detector_report(report: Mapping[str, Any] | None = None) -> str:
    data = dict(report or detect_mirror_only_surface({}))
    assert_mirror_only_surface_detector_meta_only(data)
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


__all__ = [
    "MIRROR_ONLY_SURFACE_DETECTOR_VERSION",
    "MIRROR_ONLY_SURFACE_DETECTOR_STEP",
    "MIRROR_ONLY_SURFACE_SCORECARD_FIELDS_VERSION",
    "MIRROR_ONLY_SURFACE_SUMMARY_VERSION",
    "VERDICT_REPAIR_REQUIRED",
    "VERDICT_YELLOW",
    "VERDICT_PASS",
    "MirrorOnlySurfaceDetectorMetaOnlyError",
    "assert_mirror_only_surface_detector_meta_only",
    "detect_mirror_only_surface",
    "build_mirror_only_surface_detection",
    "normalize_mirror_only_surface_to_scorecard_event",
    "normalize_mirror_only_surface_detector_to_scorecard_fields",
    "build_mirror_only_surface_detector_summary",
    "normalize_mirror_only_surface_detector_summary_to_scorecard_fields",
    "enrich_events_with_mirror_only_surface_detection",
    "dump_mirror_only_surface_detector_report",
]
