# -*- coding: utf-8 -*-
from __future__ import annotations

"""P4-8 self_denial yellow safety-adjacent review material.

P4-8 does not render user-facing text and does not broaden any public/RN/API
contract.  It reviews whether self-denial family inputs keep the P4-4 policy
boundary: treat self-denial as a felt state rather than a fact, keep a careful
observation/reception balance, and preserve existing safety/emergency paths.
"""

from collections.abc import Iterable, Mapping, Sequence
import copy
import json
from typing import Any, Final

from emlis_ai_product_readfeel_current_output_inventory import FAMILY_SELF_DENIAL
from emlis_ai_product_readfeel_p4_family_tuning_policy import (
    build_product_readfeel_p4_family_policy_registry_20260610,
)
from emlis_ai_reception_mode_resolver import MODE_LOW_INFORMATION, MODE_SELF_DENIAL, resolve_emlis_reception_mode_meta
from emlis_ai_safety_triage import (
    TRIAGE_SAFE_OBSERVATION,
    TRIAGE_SAFETY_BLOCKED_EMERGENCY,
    TRIAGE_SAFETY_SUPPORT_REQUIRED,
    TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER,
    build_emlis_safety_triage_decision,
)
from emlis_ai_shared_reception_evidence import build_emlis_shared_reception_evidence_meta
from emlis_ai_state_answer_ratio_policy import build_emlis_ai_state_answer_ratio_policy
from emlis_ai_state_answer_special_cases import build_emlis_ai_state_answer_special_cases

PRODUCT_READFEEL_P4_SELF_DENIAL_YELLOW_REVIEW_VERSION_20260610: Final = (
    "cocolon.emlis.product_readfeel.p4.self_denial_yellow_review.20260610.v1"
)
PRODUCT_READFEEL_P4_SELF_DENIAL_YELLOW_REVIEW_ITEM_VERSION_20260610: Final = (
    "cocolon.emlis.product_readfeel.p4.self_denial_yellow_review_item.20260610.v1"
)
PRODUCT_READFEEL_P4_SELF_DENIAL_YELLOW_REVIEW_STEP_20260610: Final = (
    "P4-8_Self_Denial_Yellow_Safety_Adjacent_Review"
)
PRODUCT_READFEEL_P4_SELF_DENIAL_YELLOW_REVIEW_PROFILE_20260610: Final = (
    "p4_8_self_denial_state_not_fact_safety_adjacent_review"
)

_FORBIDDEN_BODY_KEYS_20260610: Final[frozenset[str]] = frozenset(
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
        "current_input",
        "currentInput",
        "memo",
        "memo_text",
        "memoText",
        "memo_action",
        "memoAction",
        "thought_text",
        "thoughtText",
        "action_text",
        "actionText",
        "comment_text",
        "commentText",
        "comment_text_body",
        "commentTextBody",
        "candidate_body",
        "candidateBody",
        "surface_text",
        "surfaceText",
        "reply_text",
        "replyText",
        "display_text",
        "displayText",
        "body",
        "text",
        "sentence",
        "sentences",
        "phrase",
        "raw_quote",
        "raw_quotes",
        "evidence_text",
        "matched_raw_quote_fragments",
        "history_raw_text",
        "historyRawText",
    }
)

_FORBIDDEN_TRUE_FLAGS_20260610: Final[frozenset[str]] = frozenset(
    {
        "api_route_changed",
        "request_key_changed",
        "response_shape_changed",
        "public_response_key_added",
        "public_response_key_change",
        "db_physical_name_changed",
        "rn_visible_contract_changed",
        "rn_visible_title_changed",
        "display_gate_relaxed",
        "grounding_gate_relaxed",
        "reader_gate_relaxed",
        "template_gate_relaxed",
        "visible_surface_gate_relaxed",
        "safety_gate_relaxed",
        "gate_relaxed",
        "raw_input_included",
        "raw_text_included",
        "input_text_included",
        "comment_text_included",
        "comment_text_body_included",
        "candidate_body_included",
        "surface_body_included",
        "history_raw_text_included",
        "product_quality_released",
        "public_release_applied",
        "exact_comment_text_locked",
        "exact_comment_text_required",
        "case_specific_runtime_branch",
        "case_specific_runtime_condition_allowed",
        "runtime_branching_uses_fixture_strings",
        "fixture_text_used_for_runtime_branching",
        "fixed_sentence_template_added",
        "fixed_sentence_template_used",
        "input_specific_template_added",
        "p5_visible_surface_strengthened",
        "p5_runtime_change_applied",
        "external_ai_used",
        "local_llm_used",
        "schema_file_materialized",
        "identity_claim_accepted_as_fact",
        "identity_claim_as_fact_allowed",
        "overpositive_template_allowed",
        "emergency_bypass_allowed",
        "safety_path_bypassed",
        "cause_overclaim_allowed",
        "comfort_only_allowed",
        "question_only_allowed",
    }
)


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _dedupe(values: Iterable[Any] | Any | None) -> list[str]:
    if values is None:
        iterable: Iterable[Any] = ()
    elif isinstance(values, (str, bytes, bytearray)):
        iterable = (values,)
    else:
        try:
            iterable = values  # type: ignore[assignment]
        except TypeError:
            iterable = (values,)
    out: list[str] = []
    for value in iterable:
        item = _clean(value)
        if item and item not in out:
            out.append(item)
    return out


def _contains_forbidden_body_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if _clean(key) in _FORBIDDEN_BODY_KEYS_20260610:
                return True
            if _contains_forbidden_body_key(item):
                return True
        return False
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_forbidden_body_key(item) for item in value)
    return False


def _assert_no_forbidden_true_flags(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if _clean(key) in _FORBIDDEN_TRUE_FLAGS_20260610 and item is True:
                raise ValueError(f"forbidden true flag in P4-8 self_denial review: {key}")
            _assert_no_forbidden_true_flags(item)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for item in value:
            _assert_no_forbidden_true_flags(item)


def assert_product_readfeel_p4_self_denial_yellow_review_meta_only_20260610(
    payload: Mapping[str, Any], *, source: str = "p4_8_self_denial_yellow_review"
) -> None:
    if _contains_forbidden_body_key(payload):
        raise ValueError(f"forbidden raw/body key in {source}")
    _assert_no_forbidden_true_flags(payload)
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    for forbidden in (
        "また途中で止まって",
        "挑戦する前から",
        "周りは進んでいる",
        "大丈夫なふり",
        "できない自分を隠す",
        "あなたはダメ",
        "素晴らしい人",
    ):
        if forbidden in encoded:
            raise ValueError(f"forbidden raw/body fragment leaked in {source}")


def _self_denial_policy() -> Mapping[str, Any]:
    for policy in build_product_readfeel_p4_family_policy_registry_20260610():
        if policy.get("family") == FAMILY_SELF_DENIAL:
            return policy
    return {}


def _false_contract_flags() -> dict[str, bool]:
    return {
        "api_route_changed": False,
        "request_key_changed": False,
        "response_shape_changed": False,
        "public_response_key_added": False,
        "public_response_key_change": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "template_gate_relaxed": False,
        "visible_surface_gate_relaxed": False,
        "safety_gate_relaxed": False,
        "gate_relaxed": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "history_raw_text_included": False,
        "exact_comment_text_locked": False,
        "exact_comment_text_required": False,
        "case_specific_runtime_branch": False,
        "runtime_branching_uses_fixture_strings": False,
        "fixed_sentence_template_added": False,
        "fixed_sentence_template_used": False,
        "input_specific_template_added": False,
        "p5_visible_surface_strengthened": False,
        "p5_runtime_change_applied": False,
        "identity_claim_accepted_as_fact": False,
        "identity_claim_as_fact_allowed": False,
        "overpositive_template_allowed": False,
        "emergency_bypass_allowed": False,
        "safety_path_bypassed": False,
        "cause_overclaim_allowed": False,
        "comfort_only_allowed": False,
        "question_only_allowed": False,
        "external_ai_used": False,
        "local_llm_used": False,
        "schema_file_materialized": False,
    }


def _review_case(case: Mapping[str, Any], *, policy: Mapping[str, Any]) -> dict[str, Any]:
    case_id = _clean(case.get("case_id") or case.get("id"))
    family = _clean(case.get("family"))
    current_input = case.get("current_input") or case

    evidence = build_emlis_shared_reception_evidence_meta(current_input)
    mode = resolve_emlis_reception_mode_meta(current_input)
    ratio = build_emlis_ai_state_answer_ratio_policy(current_input, reception_mode_resolution=mode).as_meta()
    special = build_emlis_ai_state_answer_special_cases(current_input, ratio_policy=ratio).as_meta()
    triage = build_emlis_safety_triage_decision(current_input=current_input).as_meta()

    resolved_ratio = ratio.get("resolved_ratio") if isinstance(ratio.get("resolved_ratio"), Mapping) else {}
    obs = float(resolved_ratio.get("observation") or 0.0)
    follow = float(resolved_ratio.get("human_follow") or 0.0)
    ratio_profile = policy.get("ratio_profile") if isinstance(policy.get("ratio_profile"), Mapping) else {}
    ratio_in_range = bool(
        float(ratio_profile.get("observation_ratio_min") or 0.0) <= obs <= float(ratio_profile.get("observation_ratio_max") or 1.0)
        and float(ratio_profile.get("reception_ratio_min") or 0.0) <= follow <= float(ratio_profile.get("reception_ratio_max") or 1.0)
    )

    triage_kind = _clean(triage.get("safety_triage_kind"))
    emergency_or_support_required = triage_kind in {TRIAGE_SAFETY_BLOCKED_EMERGENCY, TRIAGE_SAFETY_SUPPORT_REQUIRED}
    special_enabled = bool(special.get("self_denial_special_handling_enabled"))
    self_denial_signal = bool(
        "self_denial" in set(_dedupe(evidence.get("explicit_reaction_cue_ids") or []))
        or "self_denial" in set(_dedupe(evidence.get("explicit_emotion_label_ids") or []))
        or special_enabled
    )
    reception_mode_id = _clean(mode.get("reception_mode") or mode.get("reception_mode_id"))
    ratio_reason = _clean(resolved_ratio.get("reason"))
    low_information_overroute = bool(
        self_denial_signal
        and not emergency_or_support_required
        and (reception_mode_id == MODE_LOW_INFORMATION or ratio_reason == "low_information_light_prompt")
    )

    item = {
        "schema_version": PRODUCT_READFEEL_P4_SELF_DENIAL_YELLOW_REVIEW_ITEM_VERSION_20260610,
        "case_ref_id": case_id,
        "family": family,
        "review_group": "yellow_review",
        "self_denial_signal_detected": self_denial_signal,
        "event_fact_present": bool(evidence.get("event_fact_present")),
        "reaction_present": bool(evidence.get("reaction_present")),
        "reaction_cue_ids": _dedupe(evidence.get("explicit_reaction_cue_ids") or []),
        "emotion_label_ids": _dedupe(evidence.get("explicit_emotion_label_ids") or []),
        "reception_mode_id": reception_mode_id,
        "reception_primary_reason": _clean(mode.get("primary_reason")),
        "low_information_question_required": bool(mode.get("low_information_question_required")),
        "low_information_overroute_detected": low_information_overroute,
        "ratio_reason": ratio_reason,
        "observation_ratio": obs,
        "reception_ratio": follow,
        "self_denial_ratio_in_policy_range": ratio_in_range,
        "special_handling_enabled": special_enabled,
        "self_denial_phrase_as_state_not_fact": bool(special.get("identity_claim_is_not_accepted")),
        "identity_claim_accepted_as_fact": False,
        "identity_claim_as_fact_allowed": False,
        "limited_counter_observation_or_reception_allowed": bool(special.get("limited_counter_opinion_allowed")),
        "overpositive_template_allowed": False,
        "emergency_bypass_allowed": False,
        "safety_path_bypassed": False,
        "safety_triage_kind": triage_kind,
        "emergency_or_support_required": emergency_or_support_required,
        "existing_safety_boundary_kept": bool(
            (triage_kind == TRIAGE_SAFE_OBSERVATION)
            or (triage_kind == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER)
            or emergency_or_support_required
        ),
        "requires_separate_safety_surface": bool(triage.get("requires_separate_safety_surface")),
        "normal_observation_allowed": bool(triage.get("normal_observation_allowed")),
        "safe_state_answer_allowed": bool(triage.get("safe_state_answer_allowed")),
        "forbidden_surface_classes_guarded": [
            "identity_claim_as_fact",
            "overpositive_template",
            "emergency_bypass",
            "cause_claim_without_evidence",
        ],
        "p4_8_self_denial_yellow_review_ready": bool(
            family == FAMILY_SELF_DENIAL
            and self_denial_signal
            and not emergency_or_support_required
            and not low_information_overroute
            and ratio_in_range
            and special_enabled
            and bool(special.get("identity_claim_is_not_accepted"))
        ),
        **_false_contract_flags(),
    }
    assert_product_readfeel_p4_self_denial_yellow_review_meta_only_20260610(item, source=f"p4_8.case.{case_id}")
    return item


def build_product_readfeel_p4_self_denial_yellow_review_20260610(
    cases: Sequence[Mapping[str, Any]], *, run_id: str | None = None
) -> dict[str, Any]:
    policy = _self_denial_policy()
    review_items = [_review_case(case, policy=policy) for case in cases if _clean(case.get("family")) == FAMILY_SELF_DENIAL]
    ready_count = sum(1 for item in review_items if item.get("p4_8_self_denial_yellow_review_ready"))
    low_info_count = sum(1 for item in review_items if item.get("low_information_overroute_detected"))
    emergency_boundary_cases = sum(1 for item in review_items if item.get("emergency_or_support_required"))
    payload = {
        "schema_version": PRODUCT_READFEEL_P4_SELF_DENIAL_YELLOW_REVIEW_VERSION_20260610,
        "run_id": _clean(run_id) or "p4_8_self_denial_yellow_review",
        "source_step": PRODUCT_READFEEL_P4_SELF_DENIAL_YELLOW_REVIEW_STEP_20260610,
        "source_phase": PRODUCT_READFEEL_P4_SELF_DENIAL_YELLOW_REVIEW_STEP_20260610,
        "review_profile": PRODUCT_READFEEL_P4_SELF_DENIAL_YELLOW_REVIEW_PROFILE_20260610,
        "family": FAMILY_SELF_DENIAL,
        "policy_ref": {
            "policy_id": _clean(policy.get("policy_id")),
            "temperature_profile": _clean(policy.get("temperature_profile")),
            "ratio_profile": copy.deepcopy(dict(policy.get("ratio_profile") or {})),
            "required_anchor_roles": _dedupe(policy.get("required_anchor_roles") or []),
            "forbidden_surface_classes": _dedupe(policy.get("forbidden_surface_classes") or []),
        },
        "review_items": review_items,
        "summary": {
            "schema_version": PRODUCT_READFEEL_P4_SELF_DENIAL_YELLOW_REVIEW_VERSION_20260610,
            "reviewed_case_count": len(review_items),
            "ready_case_count": ready_count,
            "low_information_overroute_count": low_info_count,
            "emergency_boundary_case_count": emergency_boundary_cases,
            "identity_claim_accepted_as_fact_count": 0,
            "overpositive_template_allowed_count": 0,
            "safety_path_bypassed_count": 0,
            "self_denial_yellow_review_policy_ready": bool(policy),
            "p4_8_self_denial_yellow_review_ready": bool(review_items and ready_count == len(review_items) and low_info_count == 0),
            "p5_visible_surface_strengthened": False,
            **_false_contract_flags(),
        },
        "p4_8_self_denial_yellow_review_ready": bool(review_items and ready_count == len(review_items) and low_info_count == 0),
        "p5_connection_allowed": False,
        **_false_contract_flags(),
    }
    assert_product_readfeel_p4_self_denial_yellow_review_meta_only_20260610(payload)
    return payload


def build_product_readfeel_p4_self_denial_boundary_sample_review_20260610(
    *, sample_id: str, current_input: Mapping[str, Any]
) -> dict[str, Any]:
    case = {"case_id": sample_id, "family": FAMILY_SELF_DENIAL, "current_input": current_input}
    item = _review_case(case, policy=_self_denial_policy())
    assert_product_readfeel_p4_self_denial_yellow_review_meta_only_20260610(item, source="p4_8.boundary_sample")
    return item


__all__ = [
    "PRODUCT_READFEEL_P4_SELF_DENIAL_YELLOW_REVIEW_VERSION_20260610",
    "PRODUCT_READFEEL_P4_SELF_DENIAL_YELLOW_REVIEW_ITEM_VERSION_20260610",
    "PRODUCT_READFEEL_P4_SELF_DENIAL_YELLOW_REVIEW_STEP_20260610",
    "PRODUCT_READFEEL_P4_SELF_DENIAL_YELLOW_REVIEW_PROFILE_20260610",
    "assert_product_readfeel_p4_self_denial_yellow_review_meta_only_20260610",
    "build_product_readfeel_p4_self_denial_yellow_review_20260610",
    "build_product_readfeel_p4_self_denial_boundary_sample_review_20260610",
]
