# -*- coding: utf-8 -*-
from __future__ import annotations

"""Surface Realizer 2.1 Anti-Template helpers for EmlisAI.

This module is deliberately meta-only.  It does not contain completed fallback
observations and it does not inspect raw user input.  Surface Realizer passes
component keys to it so connector / predicate / opening repetition can be
measured and avoided without adding fixture-specific branches.
"""

import re
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_VERSION = "emlis.complete_surface_realizer_anti_template.v2_1"
COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_POLICY_VERSION = "emlis.complete_surface_realizer_anti_template_policy.v2_1"
COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_REPORT_VERSION = "emlis.complete_surface_realizer_anti_template_report.v2_1"
COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_STEP = "Step7_Surface_Realizer_2_1_Anti_Template"

_FORBIDDEN_TEXT_PAYLOAD_KEYS = {
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
    "realized_text",
    "line_text",
    "body",
    "text",
    "sentence",
    "sentences",
    "phrase",
}

_GENERIC_CENTER_OPENING_PREDICATES = {"center_core"}


def _clean(value: Any) -> str:
    if value is None or isinstance(value, Mapping):
        return ""
    return str(value).strip()


def _clean_token(value: Any) -> str:
    return re.sub(r"[^0-9a-zA-Z_\-.]+", "_", _clean(value).lower()).strip("_")


def _listify(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    if isinstance(value, (tuple, set)):
        return list(value)
    return [value]


def _dedupe(values: Iterable[Any] | Any) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for value in _listify(values):
        item = _clean(value)
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


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


def assert_surface_realizer_anti_template_meta_only(
    value: Mapping[str, Any],
    *,
    source: str = "surface_realizer_anti_template",
) -> None:
    if _contains_forbidden_text_payload_key(value):
        raise ValueError(f"{source} must stay meta-only and must not include text payload keys")
    for key in (
        "raw_input_included",
        "raw_text_included",
        "comment_text_included",
        "comment_text_body_included",
        "response_shape_changed",
        "public_response_key_change",
        "api_route_changed",
        "db_physical_name_changed",
        "rn_visible_contract_changed",
        "display_gate_relaxed",
        "grounding_gate_relaxed",
        "template_gate_relaxed",
        "reader_gate_relaxed",
        "gate_relaxed",
        "public_release_applied",
        "product_gate_achieved",
        "fixed_sentence_template_used",
        "input_specific_template_used",
        "role_completed_sentence_template_used",
        "completion_sentence_template_used",
        "external_ai_used",
        "local_llm_used",
    ):
        if value.get(key) is True:
            raise ValueError(f"{source} violates fixed contract: {key}=true")


def connector_family_key(connector_key: Any, connector_text: Any = "") -> str:
    """Return a broad connector family for repetition avoidance.

    Families are based on connector component keys, not raw input.  The return
    value is coarse enough to prevent repeated surface skeletons but not used to
    choose a completed observation sentence.
    """

    key = _clean_token(connector_key)
    text = _clean(connector_text)
    if not key or key == "none":
        return "none"
    if "sono_nakademo" in key or "inside" in key or "core_inside" in key or "その中" in text:
        return "inside_connector"
    if "same_time" in key or "douji" in key or "同時" in text or "同じ時間" in text:
        return "same_time_connector"
    if "contrast" in key or "other_side" in key or "tada" in key or "一方" in text or "ただ" in text:
        return "contrast_connector"
    if "pressure" in key or "圧力" in text or "重さ" in text:
        return "pressure_connector"
    if "recovery" in key or "戻" in text or "それでも" in text:
        return "recovery_connector"
    if "approach_avoidance" in key or "近づ" in text or "止まり" in text:
        return "approach_avoidance_connector"
    if "closing" in key:
        return "closing_connector"
    if "relation" in key:
        return "relation_connector"
    return re.sub(r"(?:_v\d+|_\d+)$", "", key) or "other_connector"


def predicate_family_key(predicate_key: Any, ending_key: Any = "") -> str:
    key = _clean_token(predicate_key)
    ending = _clean_token(ending_key)
    if not key:
        return "unknown_predicate"
    # The screenshot-like backbone is not every predicate in the center relation;
    # it is the generic "中心にあります" opening.  Keep alternative center predicates
    # distinct so the realizer can still render a source-bound central role.
    if key == "center_core":
        return "generic_center_predicate"
    if key == "center_front":
        return "front_predicate"
    if key == "center_axis":
        return "axis_predicate"
    if "visible" in key or "see" in key:
        return "visible_predicate"
    if "overlap" in key:
        return "overlap_predicate"
    if "remain" in key or "residue" in key or key.endswith("_after") or ending in {"nokoru", "remain"}:
        return "remain_predicate"
    if "same_time" in key or "same_flow" in key:
        return "relation_flow_predicate"
    if "not_one" in key:
        return "not_one_side_predicate"
    if "both" in key:
        return "both_motion_predicate"
    if key.endswith("_line"):
        return "line_predicate"
    if "pressure" in key:
        return "pressure_predicate"
    if "recovery" in key:
        return "recovery_predicate"
    if "contrast" in key:
        return "contrast_predicate"
    if "coexistence" in key:
        return "coexistence_predicate"
    if "limit" in key:
        return "limit_predicate"
    if "context" in key or "grounded" in key:
        return "grounded_predicate"
    return key


def ending_family_key(ending_key: Any) -> str:
    key = _clean_token(ending_key)
    if key in {"teimasu", "arimasu", "masu", "mashita"}:
        return "masu_family"
    if key in {"aru", "exists"}:
        return "aru_family"
    if key in {"nokoru", "remain"}:
        return "remain_family"
    if key in {"tsuzuku", "tamotsu", "motsu", "kimaranai", "tsunagaru", "atsukau"}:
        return key
    return key or "unknown_ending"


def opening_family_key(line_role: Any, predicate_key: Any, role_phrase_key: Any = "") -> str:
    role = _clean_token(line_role)
    predicate = _clean_token(predicate_key)
    phrase = _clean_token(role_phrase_key)
    if role != "opening":
        return "not_opening"
    if predicate in _GENERIC_CENTER_OPENING_PREDICATES:
        return "generic_center_opening"
    if phrase == "primary_phrase":
        return "primary_phrase_opening"
    return "source_bound_opening"


def _value_counts(values: Sequence[str]) -> dict[str, int]:
    return dict(Counter(value for value in values if value))


def _max_run(values: Sequence[str], *, ignore: set[str] | None = None) -> int:
    ignored = ignore or set()
    best = 0
    current_key = ""
    current_count = 0
    for value in values:
        if value in ignored:
            current_key = ""
            current_count = 0
            continue
        if value == current_key:
            current_count += 1
        else:
            current_key = value
            current_count = 1
        best = max(best, current_count)
    return best


def _max_frequency(values: Sequence[str], *, ignore: set[str] | None = None) -> int:
    ignored = ignore or set()
    counts = Counter(value for value in values if value and value not in ignored)
    return max(counts.values(), default=0)


def _row_value(row: Mapping[str, Any], key: str) -> str:
    return _clean(row.get(key))


def build_surface_realizer_anti_template_report(rows: Sequence[Mapping[str, Any]] | None) -> dict[str, Any]:
    row_list = [dict(row) for row in tuple(rows or ()) if isinstance(row, Mapping)]
    connector_families = [
        _row_value(row, "connector_family_key") or connector_family_key(row.get("connector_key"))
        for row in row_list
    ]
    predicate_families = [
        _row_value(row, "predicate_family_key") or predicate_family_key(row.get("predicate_key"), row.get("ending_key"))
        for row in row_list
    ]
    ending_families = [
        _row_value(row, "ending_family_key") or ending_family_key(row.get("ending_key"))
        for row in row_list
    ]
    opening_families = [
        _row_value(row, "opening_family_key") or opening_family_key(row.get("line_role"), row.get("predicate_key"), row.get("role_phrase_key"))
        for row in row_list
    ]
    connector_keys = [_row_value(row, "connector_key") for row in row_list]
    predicate_keys = [_row_value(row, "predicate_key") for row in row_list]
    ending_keys = [_row_value(row, "ending_key") for row in row_list]

    generic_center_opening_count = sum(1 for key in opening_families if key == "generic_center_opening")
    same_connector_family_run_max = _max_run(connector_families, ignore={"", "none"})
    same_connector_key_run_max = _max_run(connector_keys, ignore={"", "none"})
    same_predicate_family_count = _max_frequency(predicate_families, ignore={"", "unknown_predicate"})
    same_ending_family_count = _max_frequency(ending_families, ignore={"", "unknown_ending"})

    major_reasons: list[str] = []
    if generic_center_opening_count > 0:
        major_reasons.append("generic_center_opening")
    if same_connector_key_run_max >= 2:
        major_reasons.append("same_connector_key_run")
    if same_connector_family_run_max >= 3:
        major_reasons.append("same_connector_family_run")
    if same_predicate_family_count >= 3 and len(row_list) >= 3:
        major_reasons.append("same_predicate_family_stack")
    if same_ending_family_count >= 3 and len(row_list) >= 4:
        major_reasons.append("same_ending_family_stack")

    report = {
        "version": COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_REPORT_VERSION,
        "source_step": COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_STEP,
        "surface_realizer_anti_template_version": COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_VERSION,
        "anti_template_policy_version": COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_POLICY_VERSION,
        "surface_realizer_2_1_anti_template": True,
        "surface_realizer_2_1_anti_template_applied": True,
        "row_count": len(row_list),
        "connector_family_keys": connector_families,
        "connector_family_counts": _value_counts(connector_families),
        "predicate_family_keys": predicate_families,
        "predicate_family_counts": _value_counts(predicate_families),
        "ending_family_keys": ending_families,
        "ending_family_counts": _value_counts(ending_families),
        "opening_family_keys": opening_families,
        "generic_center_opening_count": generic_center_opening_count,
        "same_connector_family_run_max": same_connector_family_run_max,
        "same_connector_key_run_max": same_connector_key_run_max,
        "same_predicate_family_count": same_predicate_family_count,
        "same_ending_family_count": same_ending_family_count,
        "anti_template_major_detected": bool(major_reasons),
        "surface_anti_template_major_detected": bool(major_reasons),
        "anti_template_major_reasons": major_reasons,
        "completion_sentence_template_used": False,
        "role_completed_sentence_template_used": False,
        "input_specific_template_used": False,
        "fixed_sentence_template_used": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
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
    assert_surface_realizer_anti_template_meta_only(report, source="surface_realizer_anti_template_report")
    return report


def build_surface_realizer_anti_template_policy_meta() -> dict[str, Any]:
    meta = {
        "version": COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_POLICY_VERSION,
        "source_step": COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_STEP,
        "surface_realizer_anti_template_version": COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_VERSION,
        "surface_realizer_2_1_anti_template": True,
        "avoid_generic_center_opening": True,
        "avoid_same_connector_key_run": True,
        "avoid_same_connector_family_run": True,
        "avoid_predicate_family_stack": True,
        "avoid_ending_family_stack": True,
        "relation_line_forced_for_all_inputs": False,
        "completed_sentence_templates_added": False,
        "fixed_sentence_template_added": False,
        "input_specific_template_used": False,
        "runtime_branching_uses_fixture_strings": False,
        "fixture_text_used_for_runtime_branching": False,
        "raw_input_included": False,
        "comment_text_body_included": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "gate_relaxed": False,
    }
    assert_surface_realizer_anti_template_meta_only(meta, source="surface_realizer_anti_template_policy")
    return meta


__all__ = [
    "COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_POLICY_VERSION",
    "COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_REPORT_VERSION",
    "COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_STEP",
    "COMPLETE_SURFACE_REALIZER_ANTI_TEMPLATE_VERSION",
    "assert_surface_realizer_anti_template_meta_only",
    "build_surface_realizer_anti_template_policy_meta",
    "build_surface_realizer_anti_template_report",
    "connector_family_key",
    "ending_family_key",
    "opening_family_key",
    "predicate_family_key",
]
