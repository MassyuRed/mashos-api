# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase 11 Long-run QA / Product Gate material for EmlisAI Product Read Feel.

This module connects Product Read Feel v1 and Structure Insight v2 to long-run
QA material without making a release decision.  It checks 5/10 consecutive
surface quality, family-cross repetition, and insight-surface syntax repetition
as meta-only scorecard material.  It never writes ``comment_text``, never adds
public response keys, and never flips Product Gate / release flags.
"""

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
import json
from typing import Any, Final

from emlis_ai_product_readfeel_current_output_inventory import (
    PRODUCT_READFEEL_REQUIRED_FAMILIES,
)
from emlis_ai_product_readfeel_rubric import (
    VERDICT_PASS,
    VERDICT_PRODUCT_PASS,
    VERDICT_RED,
    VERDICT_REPAIR_REQUIRED,
    VERDICT_STRUCTURE_INSIGHT_READY,
    VERDICT_YELLOW,
)
from emlis_ai_product_readfeel_scorecard import (
    PRODUCT_READFEEL_SCORECARD_VERSION,
    normalize_product_readfeel_scorecard_to_scorecard_fields,
)

PRODUCT_READFEEL_LONG_RUN_PRODUCT_GATE_VERSION: Final = (
    "cocolon.emlis.product_readfeel.long_run_product_gate.v1"
)
PRODUCT_READFEEL_LONG_RUN_PRODUCT_GATE_FIELDS_VERSION: Final = (
    "cocolon.emlis.product_readfeel.long_run_product_gate.fields.v1"
)
PRODUCT_READFEEL_LONG_RUN_PRODUCT_GATE_STEP: Final = "Phase11_Long_Run_QA_Product_Gate"
PRODUCT_READFEEL_LONG_RUN_PRODUCT_GATE_TARGET_STEP: Final = "ProductReadFeel_v1_and_StructureInsight_v2"
PRODUCT_READFEEL_LONG_RUN_SEQUENCE_WINDOWS: Final[tuple[int, int]] = (5, 10)
PRODUCT_READFEEL_LONG_RUN_INSIGHT_FAMILIES: Final[frozenset[str]] = frozenset(
    {
        "structure_question",
        "long_meaning_arc",
        "self_understanding_follow",
    }
)

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
        "memo_action_body",
        "emotion_details",
        "emotion_details_body",
        "current_input",
        "currentInput",
        "evidence_text",
        "comment_text",
        "commentText",
        "comment_text_body",
        "input_feedback_comment",
        "inputFeedbackComment",
        "public_comment_text",
        "candidate_comment_text",
        "reply_text",
        "replyText",
        "surface_text",
        "surfaceText",
        "accepted_surface_probe",
        "blocked_surface_probe",
        "proposed_surface",
        "realized_text",
        "display_text",
        "candidate_body",
        "response_body",
        "text_body",
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
    "surface_text_included",
    "machine_metrics_used_for_read_feeling",
    "read_feeling_auto_filled_from_machine_metrics",
    "read_feeling_auto_estimation_allowed",
    "comment_text_generated",
    "comment_text_key_written",
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
    "release_allowed",
    "release_decision_applied",
    "fixed_sentence_template_used",
    "fixed_completed_sentence_template_added",
    "input_specific_template_added",
    "external_ai_used",
    "local_llm_used",
)
_V1_PASS_VERDICTS: Final[frozenset[str]] = frozenset({VERDICT_PASS, VERDICT_PRODUCT_PASS})
_V2_PASS_VERDICTS: Final[frozenset[str]] = frozenset({VERDICT_STRUCTURE_INSIGHT_READY, VERDICT_PRODUCT_PASS})
_V1_BLOCKER_VERDICTS: Final[frozenset[str]] = frozenset({VERDICT_RED, VERDICT_REPAIR_REQUIRED})


class ProductReadFeelLongRunProductGateMetaOnlyError(ValueError):
    """Raised when Phase 11 Product Gate material violates meta-only contract."""


def _clean(value: Any) -> str:
    if value is None or isinstance(value, (Mapping, list, tuple, set)):
        return ""
    return str(value).strip()


def _safe_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    return {}


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(max(0.0, min(1.0, float(numerator) / float(denominator))), 4)


def _machine_metrics_from_events(events: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    eligible = 0
    displayed = 0
    expected_binding = 0
    supported_binding = 0
    reason_required = 0
    reason_covered = 0
    template_major = 0
    safety_major = 0
    signatures: list[str] = []
    for event in events:
        event_eligible = _safe_int(event.get("eligible_count"), 1 if event else 0)
        eligible += event_eligible
        if (
            event.get("display_confirmed") is True
            or event.get("public_passed") is True
            or event.get("backend_public_passed") is True
            or _clean(event.get("observation_status")).lower() == "passed"
            or _safe_int(event.get("passed_display_count"), 0) > 0
        ):
            displayed += max(1, _safe_int(event.get("passed_display_count"), 1))
        expected_binding += _safe_int(event.get("expected_binding_count"), _safe_int(event.get("binding_count"), 0))
        supported_binding += _safe_int(
            event.get("binding_supported_sentence_count"),
            _safe_int(event.get("binding_count"), 0),
        )
        reason_required += _safe_int(event.get("reason_required_count"), 0)
        reason_covered += _safe_int(event.get("reason_covered_count"), 0)
        template_major += _safe_int(event.get("template_major_count"), 0) + _safe_int(
            event.get("surface_template_major_count"), 0
        )
        safety_major += _safe_int(event.get("safety_major_count"), 0)
        signature = _surface_signature(event)
        if signature:
            signatures.append(signature)
    repeat_count = sum(max(0, count - 1) for count in Counter(signatures).values())
    return {
        "display_reach_rate": _rate(displayed, eligible),
        "binding_pass_rate": _rate(supported_binding, expected_binding) if expected_binding else 1.0,
        "reason_coverage_rate": _rate(reason_covered, reason_required) if reason_required else 1.0,
        "template_major_count": template_major,
        "safety_major_count": safety_major,
        "surface_signature_repeat_rate": _rate(repeat_count, len(signatures)),
        "surface_signature_repeat_count": repeat_count,
    }


def _safe_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _listify(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    if isinstance(value, (tuple, set)):
        return list(value)
    return [value]


def _dedupe(values: Iterable[Any] | Any | None) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in _listify(values):
        text = _clean(item)
        if text and text not in seen:
            seen.add(text)
            out.append(text)
    return out


def _contains_text_payload_key(value: Any, *, path: str = "payload") -> str | None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            if key_text in _TEXT_PAYLOAD_KEYS:
                return f"{path}.{key_text}"
            nested = _contains_text_payload_key(item, path=f"{path}.{key_text}")
            if nested:
                return nested
    elif isinstance(value, (list, tuple)):
        for idx, item in enumerate(value):
            nested = _contains_text_payload_key(item, path=f"{path}[{idx}]")
            if nested:
                return nested
    return None


def _forbidden_true_flag_path(value: Any, *, path: str = "payload") -> str | None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            if key_text in _FORBIDDEN_TRUE_FLAGS and item is True:
                return f"{path}.{key_text}"
            nested = _forbidden_true_flag_path(item, path=f"{path}.{key_text}")
            if nested:
                return nested
    elif isinstance(value, (list, tuple)):
        for idx, item in enumerate(value):
            nested = _forbidden_true_flag_path(item, path=f"{path}[{idx}]")
            if nested:
                return nested
    return None


def assert_product_readfeel_long_run_product_gate_meta_only(
    payload: Mapping[str, Any] | None,
    *,
    source: str = "product_readfeel_phase11_long_run_product_gate",
) -> None:
    """Validate that Phase 11 material contains no text body or release mutation."""

    data = _safe_mapping(payload)
    text_path = _contains_text_payload_key(data, path=source)
    if text_path:
        raise ProductReadFeelLongRunProductGateMetaOnlyError(
            f"Phase 11 Product Gate material must be meta-only; text payload key found at {text_path}"
        )
    flag_path = _forbidden_true_flag_path(data, path=source)
    if flag_path:
        raise ProductReadFeelLongRunProductGateMetaOnlyError(
            f"Phase 11 Product Gate material cannot change public/release contract; true flag at {flag_path}"
        )


def _rating_score(value: Any) -> float | None:
    text = _clean(value).lower()
    if text in {"green", "g", "pass", "passed", "ok", "product_pass", "structure_insight_ready"}:
        return 1.0
    if text in {"yellow", "y", "warn", "warning"}:
        return 0.65
    if text in {"red", "r", "fail", "failed", "ng", "repair_required"}:
        return 0.0
    return _safe_float(value)


def _normalize_verdict(value: Any) -> str:
    text = _clean(value).upper()
    if text in {
        VERDICT_RED,
        VERDICT_REPAIR_REQUIRED,
        VERDICT_YELLOW,
        VERDICT_PASS,
        VERDICT_PRODUCT_PASS,
        VERDICT_STRUCTURE_INSIGHT_READY,
    }:
        return text
    lowered = _clean(value).lower()
    if lowered in {"green", "pass", "passed", "ok"}:
        return VERDICT_PASS
    if lowered in {"yellow", "warn", "warning"}:
        return VERDICT_YELLOW
    if lowered in {"red", "fail", "failed", "ng"}:
        return VERDICT_RED
    return "NOT_EVALUATED"


def _row_id(event: Mapping[str, Any], index: int) -> str:
    for key in ("row_id", "event_id", "candidate_id", "id", "trace_id", "emotion_log_id"):
        text = _clean(event.get(key))
        if text:
            return text
    return f"phase11-row-{index + 1}"


def _family(event: Mapping[str, Any]) -> str:
    for key in (
        "product_readfeel_family",
        "fixture_family",
        "family",
        "coverage_group",
        "mode_family",
    ):
        text = _clean(event.get(key))
        if text:
            if text == "low_information":
                return "low_information_short"
            return text
    return "unclassified"


def _surface_signature(event: Mapping[str, Any], row_id: str = "") -> str:
    for key in (
        "surface_signature_family_key",
        "surface_signature_key",
        "signature_family_key",
        "surface_signature_id",
        "complete_surface_signature_key",
    ):
        text = _clean(event.get(key))
        if text:
            return text
    # Missing signature should not create false repetition between unrelated rows.
    return f"missing_surface_signature:{row_id or id(event)}"


def _insight_signature(event: Mapping[str, Any], family: str, row_id: str) -> str:
    for key in (
        "structure_insight_surface_signature_key",
        "insight_surface_signature_key",
        "insight_surface_family_key",
        "structure_insight_surface_role",
        "observation_insight_seed_signature_key",
    ):
        text = _clean(event.get(key))
        if text:
            return text
    relations = _dedupe(
        event.get("structure_insight_relation_families")
        or event.get("relation_candidate_families")
        or event.get("relation_families")
        or event.get("used_relation_types")
        or event.get("relation_types")
    )
    if relations:
        return "relation:" + "+".join(relations[:3])
    # Missing insight signature matters only for v2 insight families; keep rows distinct otherwise.
    if family in PRODUCT_READFEEL_LONG_RUN_INSIGHT_FAMILIES:
        return "missing_insight_surface_signature"
    return f"not_insight_family:{row_id}"


def _ratings(event: Mapping[str, Any]) -> dict[str, Any]:
    ratings = _safe_mapping(event.get("ratings")) or _safe_mapping(event.get("dimension_ratings"))
    if ratings:
        return ratings
    out: dict[str, Any] = {}
    for key in (
        "read_feeling",
        "self_report_retention",
        "state_structure_retention",
        "emotion_temperature_retention",
        "follow_depth",
        "evidence_boundary",
        "soft_inference_surface",
        "naturalness",
        "non_template",
        "insight_delta",
        "structure_insight_candidate_quality",
    ):
        if key in event:
            out[key] = event.get(key)
    return out


def _v1_verdict(event: Mapping[str, Any]) -> str:
    for key in (
        "product_readfeel_v1_verdict",
        "v1_verdict",
        "product_readfeel_verdict",
        "verdict",
        "family_verdict",
    ):
        text = _clean(event.get(key))
        if text:
            return _normalize_verdict(text)
    if event.get("mirror_only_detected") is True or event.get("self_report_only_detected") is True:
        return VERDICT_REPAIR_REQUIRED
    if event.get("display_confirmed") is False or event.get("public_passed") is False:
        return VERDICT_REPAIR_REQUIRED
    if _safe_int(event.get("safety_major_count"), 0) > 0 or _safe_int(event.get("template_major_count"), 0) > 0:
        return VERDICT_RED
    ratings = _ratings(event)
    v1_scores = [
        _rating_score(ratings.get(key))
        for key in (
            "read_feeling",
            "self_report_retention",
            "state_structure_retention",
            "emotion_temperature_retention",
            "follow_depth",
            "evidence_boundary",
            "soft_inference_surface",
            "naturalness",
            "non_template",
        )
        if key in ratings
    ]
    if v1_scores:
        if any(score == 0.0 for score in v1_scores):
            return VERDICT_REPAIR_REQUIRED
        if all(score is not None and score >= 0.9 for score in v1_scores):
            return VERDICT_PASS
        return VERDICT_YELLOW
    return VERDICT_PASS


def _v2_verdict(event: Mapping[str, Any]) -> str:
    for key in (
        "product_readfeel_v2_verdict",
        "v2_verdict",
        "structure_insight_verdict",
        "structure_insight_ready_verdict",
    ):
        text = _clean(event.get(key))
        if text:
            return _normalize_verdict(text)
    if event.get("structure_insight_ready") is True or event.get("structure_insight_surface_applied") is True:
        return VERDICT_STRUCTURE_INSIGHT_READY
    ratings = _ratings(event)
    scores = [
        _rating_score(ratings.get(key))
        for key in ("insight_delta", "structure_insight_candidate_quality")
        if key in ratings
    ]
    if scores and all(score is not None and score >= 0.9 for score in scores):
        return VERDICT_STRUCTURE_INSIGHT_READY
    if scores and any(score == 0.0 for score in scores):
        return VERDICT_RED
    if scores:
        return VERDICT_YELLOW
    return "NOT_EVALUATED"


def _has_public_passed(event: Mapping[str, Any]) -> bool:
    if event.get("public_passed") is False or event.get("backend_public_passed") is False:
        return False
    if event.get("observation_status") and _clean(event.get("observation_status")).lower() != "passed":
        return False
    return True


def _event_row(event: Mapping[str, Any], index: int) -> dict[str, Any]:
    data = _safe_mapping(event)
    row_id = _row_id(data, index)
    family = _family(data)
    v1 = _v1_verdict(data)
    v2 = _v2_verdict(data)
    signature = _surface_signature(data, row_id)
    insight_signature = _insight_signature(data, family, row_id)
    public_passed = _has_public_passed(data)
    overclaim_count = _safe_int(data.get("overclaim_count"), 0) + _safe_int(
        data.get("structure_insight_surface_overclaim_count"), 0
    )
    diagnosis_count = _safe_int(data.get("diagnosis_count"), 0) + _safe_int(
        data.get("structure_insight_surface_diagnosis_count"), 0
    )
    personality_count = _safe_int(data.get("personality_claim_count"), 0) + _safe_int(
        data.get("structure_insight_surface_personality_claim_count"), 0
    )
    unsafe_count = max(
        0,
        overclaim_count + diagnosis_count + personality_count + _safe_int(data.get("unsafe_insight_count"), 0),
    )
    return {
        "row_id": row_id,
        "family": family,
        "surface_signature_key": signature,
        "insight_surface_signature_key": insight_signature,
        "public_passed": public_passed,
        "v1_verdict": v1,
        "v1_product_pass_row": public_passed and v1 in _V1_PASS_VERDICTS,
        "v2_verdict": v2,
        "v2_structure_insight_row": public_passed and v2 in _V2_PASS_VERDICTS,
        "v2_required_family": family in PRODUCT_READFEEL_LONG_RUN_INSIGHT_FAMILIES,
        "unsafe_insight_count": unsafe_count,
        "mirror_only_detected": bool(data.get("mirror_only_detected") or data.get("self_report_only_detected")),
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
    }


def _longest_consecutive(rows: Sequence[Mapping[str, Any]], key: str) -> int:
    longest = 0
    current = 0
    for row in rows:
        if row.get(key) is True:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest


def _window_status(rows: Sequence[Mapping[str, Any]], key: str, window: int) -> dict[str, Any]:
    total_windows = max(0, len(rows) - window + 1)
    pass_windows = 0
    first_failing_index: int | None = None
    for start in range(total_windows):
        chunk = rows[start:start + window]
        if all(row.get(key) is True for row in chunk):
            pass_windows += 1
        elif first_failing_index is None:
            first_failing_index = start
    return {
        "window_size": window,
        "total_window_count": total_windows,
        "pass_window_count": pass_windows,
        "ready": bool(pass_windows > 0),
        "first_failing_window_index": first_failing_index,
    }


def _repeat_report(rows: Sequence[Mapping[str, Any]], key: str, *, ignore_prefixes: Sequence[str] = ()) -> dict[str, Any]:
    values: list[str] = []
    for row in rows:
        value = _clean(row.get(key))
        if not value:
            continue
        if any(value.startswith(prefix) for prefix in ignore_prefixes):
            continue
        values.append(value)
    counter = Counter(values)
    repeated = {key: count for key, count in sorted(counter.items()) if count > 1}
    ready_count = sum(counter.values())
    unique_count = len(counter)
    return {
        "ready_count": ready_count,
        "unique_count": unique_count,
        "repeat_count": sum(count - 1 for count in repeated.values()),
        "repeat_detected": bool(repeated),
        "top_repeated_keys": [
            {"signature_key": key, "count": count}
            for key, count in sorted(repeated.items(), key=lambda item: (-item[1], item[0]))[:10]
        ],
    }


def _scorecard_fields(scorecard: Mapping[str, Any] | None) -> dict[str, Any]:
    if isinstance(scorecard, Mapping):
        try:
            return normalize_product_readfeel_scorecard_to_scorecard_fields(scorecard)
        except Exception:
            # Existing callers may pass an already-normalized field projection.
            return dict(scorecard)
    return {}


def _runtime_long_run_ready(summary: Mapping[str, Any] | None) -> bool:
    data = _safe_mapping(summary)
    if not data:
        return True
    if data.get("runtime_surface_blind_qa_long_run_ready") is False:
        return False
    if data.get("step11_blind_qa_long_run_ready") is False:
        return False
    if data.get("long_run_surface_signature_repeat_detected") is True:
        return False
    blockers = _dedupe(data.get("step11_release_blockers") or data.get("release_blockers"))
    blocking = [blocker for blocker in blockers if "insight_delta" not in blocker]
    return not blocking


def build_product_readfeel_long_run_product_gate(
    *,
    events: Sequence[Mapping[str, Any]] | None = None,
    product_readfeel_scorecard: Mapping[str, Any] | None = None,
    runtime_long_run_summary: Mapping[str, Any] | None = None,
    blind_qa_aggregate: Mapping[str, Any] | None = None,
    sequence_windows: Sequence[int] = PRODUCT_READFEEL_LONG_RUN_SEQUENCE_WINDOWS,
) -> dict[str, Any]:
    """Build Phase 11 long-run / Product Gate meta material.

    The returned report can say that v1 is a Product Pass *candidate* and that
    v2 is Structure Insight Ready.  It deliberately never applies release or
    public Product Gate state.
    """

    rows = [_event_row(event, index) for index, event in enumerate(events or [])]
    families_seen = sorted({str(row.get("family")) for row in rows if row.get("family")})
    required_families = list(PRODUCT_READFEEL_REQUIRED_FAMILIES)
    missing_required_families = [family for family in required_families if family not in families_seen]

    v1_longest = _longest_consecutive(rows, "v1_product_pass_row")
    v2_longest = _longest_consecutive(rows, "v2_structure_insight_row")
    v1_windows = [_window_status(rows, "v1_product_pass_row", _safe_int(window, 0)) for window in sequence_windows]
    v2_windows = [_window_status(rows, "v2_structure_insight_row", _safe_int(window, 0)) for window in sequence_windows]
    v1_window_ready = {str(item["window_size"]): bool(item["ready"]) for item in v1_windows if item["window_size"] > 0}
    v2_window_ready = {str(item["window_size"]): bool(item["ready"]) for item in v2_windows if item["window_size"] > 0}

    surface_repeat = _repeat_report(rows, "surface_signature_key", ignore_prefixes=("missing_surface_signature:",))
    insight_repeat = _repeat_report(
        [row for row in rows if row.get("v2_required_family") is True],
        "insight_surface_signature_key",
        ignore_prefixes=("not_insight_family:",),
    )
    insight_missing_count = sum(
        1
        for row in rows
        if row.get("v2_required_family") is True
        and _clean(row.get("insight_surface_signature_key")) == "missing_insight_surface_signature"
    )
    unsafe_insight_count = sum(_safe_int(row.get("unsafe_insight_count"), 0) for row in rows)
    mirror_only_count = sum(1 for row in rows if row.get("mirror_only_detected") is True)

    scorecard_fields = _scorecard_fields(product_readfeel_scorecard)
    scorecard_v1_ready = bool(
        scorecard_fields.get("product_readfeel_v1_product_pass_candidate")
        or scorecard_fields.get("product_readfeel_product_pass_candidate")
        or scorecard_fields.get("product_readfeel_v1_product_pass_ready")
        or (product_readfeel_scorecard or {}).get("v1_product_pass_ready") is True
        or _normalize_verdict((product_readfeel_scorecard or {}).get("aggregate_verdict")) == VERDICT_PRODUCT_PASS
    )
    scorecard_v2_ready = bool(
        scorecard_fields.get("product_readfeel_v2_structure_insight_ready")
        or scorecard_fields.get("product_readfeel_v2_structure_insight_ready_candidate")
        or (product_readfeel_scorecard or {}).get("v2_structure_insight_ready") is True
        or (product_readfeel_scorecard or {}).get("v2_structure_insight_ready_candidate") is True
    )
    scorecard_release_blockers = _dedupe(
        scorecard_fields.get("product_readfeel_scorecard_release_blockers")
        or scorecard_fields.get("release_blockers")
        or (product_readfeel_scorecard or {}).get("release_blockers")
    )
    scorecard_v1_blockers = [
        blocker for blocker in scorecard_release_blockers if "insight_delta" not in blocker and "v2" not in blocker
    ]
    blind_qa_ready = bool(
        (blind_qa_aggregate or {}).get("blind_qa_ready")
        or scorecard_fields.get("product_readfeel_scorecard_blind_qa_ready")
        or scorecard_fields.get("product_readfeel_blind_qa_ready")
        or (product_readfeel_scorecard or {}).get("blind_qa_ready")
    )

    runtime_ready = _runtime_long_run_ready(runtime_long_run_summary)
    red_or_repair_row_present = any(_clean(row.get("v1_verdict")) in _V1_BLOCKER_VERDICTS for row in rows)
    row_level_v1_ready = bool(
        rows
        and not missing_required_families
        and bool(v1_window_ready.get("5"))
        and bool(v1_window_ready.get("10"))
        and not surface_repeat["repeat_detected"]
        and runtime_ready
        and unsafe_insight_count == 0
        and not red_or_repair_row_present
        and blind_qa_ready
    )
    v1_blockers: list[str] = []
    if not rows:
        v1_blockers.append("phase11_events_missing")
    # Phase 11 may produce a v1 candidate from long-run rows even when the
    # earlier Phase 4 scorecard still carries v2/backlog-oriented fixture
    # blockers.  Release remains deferred; this does not flip Product Gate.
    if not scorecard_v1_ready and not row_level_v1_ready:
        v1_blockers.append("product_readfeel_v1_scorecard_not_product_pass")
    if scorecard_v1_blockers and not row_level_v1_ready:
        v1_blockers.append("product_readfeel_v1_scorecard_blockers_present")
    if missing_required_families:
        v1_blockers.append("required_family_cross_coverage_incomplete")
    if not v1_window_ready.get("5"):
        v1_blockers.append("five_consecutive_v1_product_pass_not_observed")
    if not v1_window_ready.get("10"):
        v1_blockers.append("ten_consecutive_v1_product_pass_not_observed")
    if surface_repeat["repeat_detected"]:
        v1_blockers.append("family_cross_surface_repetition_detected")
    if not runtime_ready:
        v1_blockers.append("runtime_surface_blind_qa_long_run_not_ready")
    if unsafe_insight_count > 0:
        v1_blockers.append("unsafe_insight_surface_detected")
    if red_or_repair_row_present:
        v1_blockers.append("red_or_repair_required_row_present")
    if not blind_qa_ready:
        v1_blockers.append("blind_qa_not_ready")

    v1_product_pass_candidate = not v1_blockers

    v2_blockers: list[str] = []
    if not v1_product_pass_candidate:
        v2_blockers.append("v1_product_pass_required_first")
    if not scorecard_v2_ready:
        v2_blockers.append("product_readfeel_v2_scorecard_not_ready")
    if not v2_window_ready.get("5"):
        v2_blockers.append("five_consecutive_structure_insight_ready_not_observed")
    if not v2_window_ready.get("10"):
        v2_blockers.append("ten_consecutive_structure_insight_ready_not_observed")
    if insight_missing_count > 0:
        v2_blockers.append("insight_surface_signature_missing")
    if insight_repeat["repeat_detected"]:
        v2_blockers.append("insight_surface_same_syntax_repetition_detected")
    if unsafe_insight_count > 0:
        v2_blockers.append("unsafe_insight_surface_detected")
    v2_structure_insight_ready = not v2_blockers

    phase11_ready = bool(rows)
    report = {
        "version": PRODUCT_READFEEL_LONG_RUN_PRODUCT_GATE_VERSION,
        "schema_version": PRODUCT_READFEEL_LONG_RUN_PRODUCT_GATE_VERSION,
        "step": PRODUCT_READFEEL_LONG_RUN_PRODUCT_GATE_STEP,
        "target_step": PRODUCT_READFEEL_LONG_RUN_PRODUCT_GATE_TARGET_STEP,
        "phase11_product_readfeel_long_run_product_gate_ready": phase11_ready,
        "product_readfeel_phase11_ready": phase11_ready,
        "scorecard_source_version": PRODUCT_READFEEL_SCORECARD_VERSION,
        "product_readfeel_v1_and_structure_insight_v2_separated": True,
        "row_level_v1_long_run_ready": row_level_v1_ready,
        "scorecard_v1_product_pass_ready": scorecard_v1_ready,
        "machine_metrics_separated_from_blind_qa": True,
        "blind_qa_ready": blind_qa_ready,
        "runtime_long_run_summary_connected": bool(runtime_long_run_summary),
        "runtime_long_run_ready": runtime_ready,
        "required_families": required_families,
        "observed_families": families_seen,
        "missing_required_families": missing_required_families,
        "family_cross_coverage_ready": not missing_required_families,
        "event_count": len(rows),
        "sequence_windows": list(sequence_windows),
        "sequence_report": {
            "v1_product_pass": {
                "longest_consecutive_count": v1_longest,
                "windows": v1_windows,
                "consecutive_5_ready": bool(v1_window_ready.get("5")),
                "consecutive_10_ready": bool(v1_window_ready.get("10")),
            },
            "v2_structure_insight_ready": {
                "longest_consecutive_count": v2_longest,
                "windows": v2_windows,
                "consecutive_5_ready": bool(v2_window_ready.get("5")),
                "consecutive_10_ready": bool(v2_window_ready.get("10")),
            },
        },
        "surface_repetition_report": {
            "family_cross_surface_repetition_detected": bool(surface_repeat["repeat_detected"]),
            **surface_repeat,
        },
        "insight_surface_repetition_report": {
            "insight_surface_same_syntax_repetition_detected": bool(insight_repeat["repeat_detected"]),
            "insight_surface_signature_missing_count": insight_missing_count,
            **insight_repeat,
        },
        "v1_product_pass_candidate": v1_product_pass_candidate,
        "v1_product_pass_blockers": _dedupe(v1_blockers),
        "v2_structure_insight_ready": v2_structure_insight_ready,
        "v2_structure_insight_ready_blockers": _dedupe(v2_blockers),
        "v2_structure_insight_ready_required_conditions_met_only": v2_structure_insight_ready,
        "release_judgment_deferred": True,
        "release_decision_deferred_to_later_phase": True,
        "release_judgment": {
            "release_allowed": False,
            "reason": "release_judgment_remains_separate_phase",
        },
        "product_gate_candidate_material_ready": v1_product_pass_candidate,
        "product_gate_ready": False,
        "public_release_applied": False,
        "comment_text_generated": False,
        "comment_text_key_written": False,
        "comment_text_written_by_scorecard": False,
        "public_response_key_added": False,
        "public_response_key_change": False,
        "response_shape_changed": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "gate_relaxed": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "mirror_only_detected_count": mirror_only_count,
        "unsafe_insight_surface_count": unsafe_insight_count,
        "rows": rows,
    }
    assert_product_readfeel_long_run_product_gate_meta_only(report)
    return report


def normalize_product_readfeel_long_run_product_gate_to_scorecard_fields(
    report: Mapping[str, Any] | None,
) -> dict[str, Any]:
    data = _safe_mapping(report) or build_product_readfeel_long_run_product_gate()
    assert_product_readfeel_long_run_product_gate_meta_only(data, source="phase11_product_gate_fields_source")
    sequence = _safe_mapping(data.get("sequence_report"))
    v1_sequence = _safe_mapping(sequence.get("v1_product_pass"))
    v2_sequence = _safe_mapping(sequence.get("v2_structure_insight_ready"))
    surface = _safe_mapping(data.get("surface_repetition_report"))
    insight = _safe_mapping(data.get("insight_surface_repetition_report"))
    fields = {
        "product_readfeel_phase11_long_run_product_gate_version": _clean(data.get("version")) or PRODUCT_READFEEL_LONG_RUN_PRODUCT_GATE_VERSION,
        "product_readfeel_phase11_long_run_product_gate_step": _clean(data.get("step")) or PRODUCT_READFEEL_LONG_RUN_PRODUCT_GATE_STEP,
        "phase11_product_readfeel_long_run_product_gate_ready": bool(data.get("phase11_product_readfeel_long_run_product_gate_ready")),
        "product_readfeel_phase11_ready": bool(data.get("product_readfeel_phase11_ready")),
        "product_readfeel_phase11_event_count": _safe_int(data.get("event_count"), 0),
        "product_readfeel_phase11_observed_families": list(data.get("observed_families") or []),
        "product_readfeel_phase11_missing_required_families": list(data.get("missing_required_families") or []),
        "product_readfeel_phase11_family_cross_coverage_ready": bool(data.get("family_cross_coverage_ready")),
        "product_readfeel_phase11_max_consecutive_v1_product_pass_count": _safe_int(v1_sequence.get("longest_consecutive_count"), 0),
        "product_readfeel_phase11_max_consecutive_v2_structure_insight_ready_count": _safe_int(v2_sequence.get("longest_consecutive_count"), 0),
        "product_readfeel_phase11_consecutive_5_v1_product_pass_ready": bool(v1_sequence.get("consecutive_5_ready")),
        "product_readfeel_phase11_consecutive_10_v1_product_pass_ready": bool(v1_sequence.get("consecutive_10_ready")),
        "product_readfeel_phase11_consecutive_5_structure_insight_ready": bool(v2_sequence.get("consecutive_5_ready")),
        "product_readfeel_phase11_consecutive_10_structure_insight_ready": bool(v2_sequence.get("consecutive_10_ready")),
        "product_readfeel_phase11_family_cross_surface_repetition_detected": bool(surface.get("family_cross_surface_repetition_detected") or surface.get("repeat_detected")),
        "product_readfeel_phase11_surface_signature_repeat_count": _safe_int(surface.get("repeat_count"), 0),
        "product_readfeel_phase11_insight_surface_same_syntax_repetition_detected": bool(insight.get("insight_surface_same_syntax_repetition_detected") or insight.get("repeat_detected")),
        "product_readfeel_phase11_insight_surface_signature_missing_count": _safe_int(insight.get("insight_surface_signature_missing_count"), 0),
        "product_readfeel_phase11_v1_product_pass_candidate": bool(data.get("v1_product_pass_candidate")),
        "product_readfeel_phase11_v1_product_pass_blockers": list(data.get("v1_product_pass_blockers") or []),
        "product_readfeel_phase11_v2_structure_insight_ready": bool(data.get("v2_structure_insight_ready")),
        "product_readfeel_phase11_v2_structure_insight_ready_blockers": list(data.get("v2_structure_insight_ready_blockers") or []),
        "product_readfeel_phase11_v2_ready_only_when_required_conditions_met": bool(data.get("v2_structure_insight_ready_required_conditions_met_only")),
        "product_readfeel_phase11_product_gate_candidate_material_ready": bool(data.get("product_gate_candidate_material_ready")),
        "product_readfeel_phase11_release_judgment_deferred": bool(data.get("release_judgment_deferred")),
        "product_readfeel_phase11_product_gate_ready": False,
        "product_readfeel_phase11_public_release_applied": False,
        "product_readfeel_phase11_comment_text_written_by_scorecard": False,
        "product_readfeel_phase11_public_response_key_added": False,
        "product_readfeel_phase11_gate_relaxed": False,
        "product_gate_ready": False,
        "public_release_applied": False,
        "comment_text_generated": False,
        "comment_text_key_written": False,
        "comment_text_written_by_scorecard": False,
        "public_response_key_added": False,
        "public_response_key_change": False,
        "response_shape_changed": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "gate_relaxed": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
    }
    assert_product_readfeel_long_run_product_gate_meta_only(fields, source="phase11_product_gate_fields")
    return fields


def dump_product_readfeel_long_run_product_gate(report: Mapping[str, Any] | None = None) -> str:
    data = dict(report or build_product_readfeel_long_run_product_gate())
    assert_product_readfeel_long_run_product_gate_meta_only(data)
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


__all__ = [
    "PRODUCT_READFEEL_LONG_RUN_PRODUCT_GATE_VERSION",
    "PRODUCT_READFEEL_LONG_RUN_PRODUCT_GATE_FIELDS_VERSION",
    "PRODUCT_READFEEL_LONG_RUN_PRODUCT_GATE_STEP",
    "PRODUCT_READFEEL_LONG_RUN_SEQUENCE_WINDOWS",
    "ProductReadFeelLongRunProductGateMetaOnlyError",
    "assert_product_readfeel_long_run_product_gate_meta_only",
    "build_product_readfeel_long_run_product_gate",
    "normalize_product_readfeel_long_run_product_gate_to_scorecard_fields",
    "dump_product_readfeel_long_run_product_gate",
]
