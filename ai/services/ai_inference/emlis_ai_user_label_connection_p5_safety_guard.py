# -*- coding: utf-8 -*-
from __future__ import annotations

"""P5-4 creepy / overclaim / self-blame guard.

This guard is the last body-free check before a P5 history-line candidate may
move toward limited visible connection.  It does not rewrite wording, add
templates, generate visible text, or relax existing gates.  Initial P5 defaults
to blocking visible output when risk is ambiguous.
"""

from collections.abc import Iterable, Mapping
import json
from typing import Any, Final

from emlis_ai_user_label_connection_p5_surface_role_plan import (
    SURFACE_PLAN_KIND_BLOCKED,
    SURFACE_PLAN_KIND_LIMITED_HISTORY_LINE_OBSERVATION,
    assert_user_label_connection_p5_surface_role_plan_contract,
)


USER_LABEL_CONNECTION_P5_SAFETY_GUARD_SCHEMA_VERSION: Final = (
    "cocolon.emlis.user_label_connection.p5_safety_guard.v1"
)
USER_LABEL_CONNECTION_P5_SAFETY_GUARD_STEP: Final = (
    "P5-4_CreepyOverclaimSelfBlameGuard"
)
USER_LABEL_CONNECTION_P5_SAFETY_GUARD_SOURCE: Final = (
    "Cocolon_EmlisAI_P5_UserLabelConnection_CreepyOverclaimSelfBlameGuard_20260611"
)

DECISION_ALLOW: Final = "allow"
DECISION_WARN: Final = "warn"
DECISION_BLOCK: Final = "block"

REASON_P5_SURFACE_ROLE_PLAN_MISSING: Final = "p5_surface_role_plan_missing"
REASON_P5_SURFACE_ROLE_PLAN_NOT_READY: Final = "p5_surface_role_plan_not_ready"
REASON_P5_SURFACE_ROLE_PLAN_BLOCKED: Final = "p5_surface_role_plan_blocked"
REASON_CREEPY_RISK_DETECTED: Final = "creepy_risk_detected"
REASON_OVERCLAIM_RISK_DETECTED: Final = "overclaim_risk_detected"
REASON_SELF_BLAME_AMPLIFICATION_DETECTED: Final = "self_blame_amplification_detected"
REASON_PERIOD_TENDENCY_FROM_SINGLE_RECORD: Final = "period_tendency_from_single_record"
REASON_ALWAYS_CLAIM_DETECTED: Final = "always_claim_detected"
REASON_CAUSE_CLAIM_DETECTED: Final = "cause_claim_detected"
REASON_PERSONALITY_OR_DIAGNOSIS_CLAIM_DETECTED: Final = "personality_or_diagnosis_claim_detected"
REASON_FUTURE_PREDICTION_DETECTED: Final = "future_prediction_detected"
REASON_ADVICE_OR_SHOULD_STATEMENT_DETECTED: Final = "advice_or_should_statement_detected"
REASON_TARGET_JUDGEMENT_AGREEMENT_DETECTED: Final = "target_judgement_agreement_detected"
REASON_HISTORY_MASKS_CURRENT_INPUT_GAP: Final = "history_masks_current_input_gap"
REASON_SAFETY_OR_SELF_DENIAL_CONTEXT_DETECTED: Final = "safety_or_self_denial_context_detected"
REASON_RAW_TEXT_PAYLOAD_DETECTED: Final = "raw_text_payload_detected"
REASON_CONTRACT_MUTATION_DETECTED: Final = "contract_mutation_detected"

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
        "current_input",
        "currentInput",
        "history_context",
        "historyContext",
        "history_records",
        "historyRecords",
        "history_raw_text",
        "historyRawText",
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
        "surface_body",
        "surfaceBody",
        "surface_text",
        "surfaceText",
        "visible_text",
        "visibleText",
        "reply_text",
        "replyText",
        "display_text",
        "displayText",
        "fixed_sentence",
        "fixedSentence",
        "template_text",
        "templateText",
        "sentence_template",
        "sentenceTemplate",
        "body",
        "text",
    }
)
_FORBIDDEN_TRUE_FLAGS: Final[frozenset[str]] = frozenset(
    {
        "api_route_changed",
        "request_key_changed",
        "response_shape_changed",
        "public_response_key_added",
        "public_response_key_change",
        "db_schema_changed",
        "db_physical_name_changed",
        "rn_contract_changed",
        "rn_visible_contract_changed",
        "rn_visible_title_changed",
        "display_gate_relaxed",
        "grounding_gate_relaxed",
        "reader_gate_relaxed",
        "template_gate_relaxed",
        "runtime_surface_gate_relaxed",
        "visible_surface_gate_relaxed",
        "safety_gate_relaxed",
        "gate_relaxed",
        "existing_gate_relaxed",
        "raw_input_included",
        "raw_text_included",
        "comment_text_included",
        "comment_text_body_included",
        "candidate_body_included",
        "surface_body_included",
        "history_raw_text_included",
        "fixed_sentence_template_added",
        "input_specific_template_added",
        "diagnosis_allowed",
        "personality_claim_allowed",
        "cause_claim_allowed",
        "advice_allowed",
        "future_prediction_allowed",
        "always_claim_allowed",
        "should_statement_allowed",
        "opponent_intent_claim_allowed",
        "target_judgement_agreement_allowed",
        "period_tendency_from_single_record_allowed",
        "self_blame_amplification_allowed",
        "public_release_applied",
        "release_allowed",
        "p5_visible_surface_strengthened",
        "p5_runtime_change_applied",
        "p5_limited_visible_connection_applied",
        "external_ai_used",
        "local_llm_used",
    }
)

_POLICY_LIST_KEYS: Final[frozenset[str]] = frozenset(
    {
        "must_not_include_roles",
        "forbidden_roles",
        "forbidden_claims",
        "claim_contract",
        "public_contract",
        "body_free",
    }
)
_CREEPY_MARKERS: Final[frozenset[str]] = frozenset(
    {
        "creepy",
        "creepy_risk",
        "creepy_risk_detected",
        "too_personal",
        "surveillance_feeling",
        "private_history_overreach",
        "history_overreach",
        "unwanted_history_intimacy",
    }
)
_OVERCLAIM_MARKERS: Final[frozenset[str]] = frozenset(
    {
        "overclaim",
        "overclaim_risk",
        "overclaim_risk_detected",
        "hard_claim",
        "identity_claim_as_fact",
        "fact_claim_without_evidence",
    }
)
_SELF_BLAME_MARKERS: Final[frozenset[str]] = frozenset(
    {
        "self_blame",
        "self_blame_risk",
        "self_blame_amplification",
        "self_blame_amplification_detected",
        "self_denial_identity_claim",
        "self_denial_identity_claim_risk",
    }
)
_ALWAYS_MARKERS: Final[frozenset[str]] = frozenset({"always_claim", "always_claim_surface", "always", "every_time_claim"})
_CAUSE_MARKERS: Final[frozenset[str]] = frozenset({"cause_claim", "cause_claim_without_evidence", "causal_overclaim"})
_PERSONALITY_DIAGNOSIS_MARKERS: Final[frozenset[str]] = frozenset(
    {"personality_claim", "diagnosis_claim", "diagnosis_surface", "personality_or_diagnosis_claim"}
)
_FUTURE_MARKERS: Final[frozenset[str]] = frozenset({"future_prediction", "future_prediction_claim", "future_prediction_surface"})
_ADVICE_MARKERS: Final[frozenset[str]] = frozenset(
    {"advice_claim", "advice_surface", "should_statement", "should_statement_surface", "must_statement"}
)
_TARGET_MARKERS: Final[frozenset[str]] = frozenset(
    {
        "target_judgement",
        "target_judgement_context",
        "target_judgement_agreement",
        "target_judgement_agreement_blocked",
        "opponent_intent_claim",
        "target_attack_agreement",
    }
)
_HISTORY_MASKING_MARKERS: Final[frozenset[str]] = frozenset(
    {
        "history_line_masks_current_input_gap",
        "history_line_masks_current_input",
        "history_line_masking_observed",
        "current_input_masked_by_history",
    }
)
_SAFETY_SELF_DENIAL_MARKERS: Final[frozenset[str]] = frozenset(
    {
        "safety_triage_required",
        "safety_adjacent",
        "safety_required",
        "emergency_safety_required",
        "self_denial",
        "self_denial_context",
        "self_denial_safe_state_answer",
    }
)


def _clean(value: Any) -> str:
    if value is None or isinstance(value, (Mapping, list, tuple, set)):
        return ""
    return str(value).strip()


def _safe_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    as_meta = getattr(value, "as_meta", None)
    if callable(as_meta):
        meta = as_meta()
        if isinstance(meta, Mapping):
            return {str(key): item for key, item in meta.items()}
    return {}


def _listify(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        return [value]
    if isinstance(value, list):
        return list(value)
    if isinstance(value, (tuple, set)):
        return list(value)
    if isinstance(value, (str, bytes, bytearray)):
        return [value]
    try:
        return list(value)
    except TypeError:
        return [value]


def _dedupe(values: Iterable[Any] | Any | None) -> list[str]:
    out: list[str] = []
    for value in _listify(values):
        item = _clean(value)
        if item and item not in out:
            out.append(item)
    return out


def _contains_text_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in _TEXT_PAYLOAD_KEYS:
                return True
            if _contains_text_payload_key(child):
                return True
    elif isinstance(value, (list, tuple, set)):
        return any(_contains_text_payload_key(child) for child in value)
    return False


def _flag_true(value: Any, names: frozenset[str] = _FORBIDDEN_TRUE_FLAGS) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in names and child is True:
                return True
            if _flag_true(child, names):
                return True
    elif isinstance(value, (list, tuple, set)):
        return any(_flag_true(child, names) for child in value)
    return False


def _has_marker(value: Any, markers: frozenset[str]) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = _clean(key).lower()
            if key_text in _POLICY_LIST_KEYS:
                continue
            if key_text in markers:
                if child is True:
                    return True
                if child in (False, None, "", (), [], {}):
                    continue
                if _has_marker(child, markers):
                    return True
            elif _has_marker(child, markers):
                return True
        return False
    if isinstance(value, (list, tuple, set)):
        return any(_has_marker(child, markers) for child in value)
    text = _clean(value).lower()
    return bool(text and any(marker == text or marker in text for marker in markers))


def _numeric_below(value: Any, keys: frozenset[str], threshold: float) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = _clean(key).lower()
            if key_text in keys:
                try:
                    if float(child) < threshold:
                        return True
                except (TypeError, ValueError):
                    continue
            if _numeric_below(child, keys, threshold):
                return True
    elif isinstance(value, (list, tuple, set)):
        return any(_numeric_below(child, keys, threshold) for child in value)
    return False


def _public_contract() -> dict[str, bool]:
    return {
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "api_route_changed": False,
        "request_key_changed": False,
        "response_shape_changed": False,
        "public_response_key_added": False,
        "db_schema_changed": False,
        "fixed_sentence_template_added": False,
        "gate_relaxed": False,
        "release_allowed": False,
    }


def _body_free_contract() -> dict[str, bool]:
    return {
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "history_raw_text_included": False,
    }


def _risk_summary(*sources: Mapping[str, Any]) -> dict[str, bool]:
    creepy = any(_has_marker(source, _CREEPY_MARKERS) for source in sources) or any(
        _numeric_below(source, frozenset({"creepy_absence"}), 0.95) for source in sources
    )
    overclaim = (
        any(_has_marker(source, _OVERCLAIM_MARKERS) for source in sources)
        or any(_numeric_below(source, frozenset({"overclaim_absence"}), 0.95) for source in sources)
    )
    self_blame = any(_has_marker(source, _SELF_BLAME_MARKERS) for source in sources) or any(
        _numeric_below(source, frozenset({"self_blame_non_amplification"}), 0.95) for source in sources
    )
    return {
        "creepy_risk_detected": creepy,
        "overclaim_risk_detected": overclaim,
        "self_blame_amplification_detected": self_blame,
        "period_tendency_from_single_record_detected": any(
            _has_marker(source, frozenset({"period_tendency_from_single_record"})) for source in sources
        ),
        "always_claim_detected": any(_has_marker(source, _ALWAYS_MARKERS) for source in sources),
        "cause_claim_detected": any(_has_marker(source, _CAUSE_MARKERS) for source in sources),
        "personality_or_diagnosis_claim_detected": any(_has_marker(source, _PERSONALITY_DIAGNOSIS_MARKERS) for source in sources),
        "future_prediction_detected": any(_has_marker(source, _FUTURE_MARKERS) for source in sources),
        "advice_or_should_statement_detected": any(_has_marker(source, _ADVICE_MARKERS) for source in sources),
        "target_judgement_agreement_detected": any(_has_marker(source, _TARGET_MARKERS) for source in sources),
        "history_masks_current_input_gap": any(_has_marker(source, _HISTORY_MASKING_MARKERS) for source in sources),
        "safety_or_self_denial_context_detected": any(_has_marker(source, _SAFETY_SELF_DENIAL_MARKERS) for source in sources),
    }


def _reasons_from_risks(risks: Mapping[str, bool]) -> list[str]:
    mapping = {
        "creepy_risk_detected": REASON_CREEPY_RISK_DETECTED,
        "overclaim_risk_detected": REASON_OVERCLAIM_RISK_DETECTED,
        "self_blame_amplification_detected": REASON_SELF_BLAME_AMPLIFICATION_DETECTED,
        "period_tendency_from_single_record_detected": REASON_PERIOD_TENDENCY_FROM_SINGLE_RECORD,
        "always_claim_detected": REASON_ALWAYS_CLAIM_DETECTED,
        "cause_claim_detected": REASON_CAUSE_CLAIM_DETECTED,
        "personality_or_diagnosis_claim_detected": REASON_PERSONALITY_OR_DIAGNOSIS_CLAIM_DETECTED,
        "future_prediction_detected": REASON_FUTURE_PREDICTION_DETECTED,
        "advice_or_should_statement_detected": REASON_ADVICE_OR_SHOULD_STATEMENT_DETECTED,
        "target_judgement_agreement_detected": REASON_TARGET_JUDGEMENT_AGREEMENT_DETECTED,
        "history_masks_current_input_gap": REASON_HISTORY_MASKS_CURRENT_INPUT_GAP,
        "safety_or_self_denial_context_detected": REASON_SAFETY_OR_SELF_DENIAL_CONTEXT_DETECTED,
    }
    return [reason for key, reason in mapping.items() if risks.get(key) is True]


def build_user_label_connection_p5_safety_guard(
    *,
    p5_surface_role_plan: Mapping[str, Any] | None = None,
    guard_signal_meta: Mapping[str, Any] | None = None,
    product_quality_meta: Mapping[str, Any] | None = None,
    observation_reply_meta: Mapping[str, Any] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Build a body-free P5-4 guard decision."""

    role_plan = _safe_mapping(p5_surface_role_plan)
    guard_signal = _safe_mapping(guard_signal_meta)
    product_quality = _safe_mapping(product_quality_meta)
    observation = _safe_mapping(observation_reply_meta)
    if role_plan:
        assert_user_label_connection_p5_surface_role_plan_contract(role_plan, allow_partial=True)

    sources = [role_plan, guard_signal, product_quality, observation]
    unsafe_payload = any(_contains_text_payload_key(source) for source in sources)
    contract_mutation = any(_flag_true(source) for source in sources)
    risks = _risk_summary(*sources)

    role_plan_present = bool(role_plan)
    role_plan_ready = role_plan.get("role_plan_ready") is True
    surface_plan_kind = _clean(role_plan.get("surface_plan_kind"))
    role_plan_blocked = role_plan.get("blocked") is True or surface_plan_kind == SURFACE_PLAN_KIND_BLOCKED
    limited_candidate_ready = role_plan_ready and surface_plan_kind == SURFACE_PLAN_KIND_LIMITED_HISTORY_LINE_OBSERVATION

    reasons: list[str] = []
    if unsafe_payload:
        reasons.append(REASON_RAW_TEXT_PAYLOAD_DETECTED)
    if contract_mutation:
        reasons.append(REASON_CONTRACT_MUTATION_DETECTED)
    if not role_plan_present:
        reasons.append(REASON_P5_SURFACE_ROLE_PLAN_MISSING)
    if role_plan_blocked:
        reasons.append(REASON_P5_SURFACE_ROLE_PLAN_BLOCKED)
    if not limited_candidate_ready:
        reasons.append(REASON_P5_SURFACE_ROLE_PLAN_NOT_READY)
        reasons.extend(f"p5_surface_role_plan:{reason}" for reason in _dedupe(role_plan.get("rejection_reasons")))
    reasons.extend(_reasons_from_risks(risks))
    reasons = _dedupe(reasons)

    hard_block_reasons = {
        REASON_RAW_TEXT_PAYLOAD_DETECTED,
        REASON_CONTRACT_MUTATION_DETECTED,
        REASON_P5_SURFACE_ROLE_PLAN_BLOCKED,
        REASON_CREEPY_RISK_DETECTED,
        REASON_OVERCLAIM_RISK_DETECTED,
        REASON_SELF_BLAME_AMPLIFICATION_DETECTED,
        REASON_PERIOD_TENDENCY_FROM_SINGLE_RECORD,
        REASON_ALWAYS_CLAIM_DETECTED,
        REASON_CAUSE_CLAIM_DETECTED,
        REASON_PERSONALITY_OR_DIAGNOSIS_CLAIM_DETECTED,
        REASON_FUTURE_PREDICTION_DETECTED,
        REASON_ADVICE_OR_SHOULD_STATEMENT_DETECTED,
        REASON_TARGET_JUDGEMENT_AGREEMENT_DETECTED,
        REASON_HISTORY_MASKS_CURRENT_INPUT_GAP,
        REASON_SAFETY_OR_SELF_DENIAL_CONTEXT_DETECTED,
    }
    if any(reason in hard_block_reasons for reason in reasons):
        decision = DECISION_BLOCK
    elif reasons:
        decision = DECISION_WARN
    else:
        decision = DECISION_ALLOW

    summary = {
        "schema_version": USER_LABEL_CONNECTION_P5_SAFETY_GUARD_SCHEMA_VERSION,
        "version": USER_LABEL_CONNECTION_P5_SAFETY_GUARD_SCHEMA_VERSION,
        "step": USER_LABEL_CONNECTION_P5_SAFETY_GUARD_STEP,
        "source": USER_LABEL_CONNECTION_P5_SAFETY_GUARD_SOURCE,
        "run_id": run_id or "p5_safety_guard",
        "decision": decision,
        "allow_limited_visible_candidate": decision == DECISION_ALLOW,
        "hold_for_product_quality_qa": decision == DECISION_WARN,
        "blocked": decision == DECISION_BLOCK,
        "rejection_reasons": reasons,
        "risk_summary": risks,
        "role_plan": {
            "surface_plan_kind": surface_plan_kind,
            "role_plan_ready": role_plan_ready,
            "connectable_family": _clean(role_plan.get("connectable_family")),
            "edge_family": _clean(role_plan.get("edge_family")),
        },
        "guard_contract": {
            "false_positive_policy": "initial_p5_blocks_visible_when_ambiguous",
            "wording_repair_allowed": False,
            "gate_relaxation_allowed": False,
            "history_masking_current_input_allowed": False,
        },
        "fixed_sentence_template_added": False,
        "comment_text_generated_by_this_layer": False,
        "visible_text_generated": False,
        "visible_surface_connected": False,
        "runtime_change_applied": False,
        "public_contract": _public_contract(),
        "body_free": _body_free_contract(),
    }
    assert_user_label_connection_p5_safety_guard_contract(summary)
    return summary


def user_label_connection_p5_safety_guard_public_summary(value: Mapping[str, Any] | None) -> dict[str, Any]:
    meta = _safe_mapping(value)
    summary = {
        "schema_version": USER_LABEL_CONNECTION_P5_SAFETY_GUARD_SCHEMA_VERSION,
        "step": USER_LABEL_CONNECTION_P5_SAFETY_GUARD_STEP,
        "decision": _clean(meta.get("decision")) or DECISION_BLOCK,
        "allow_limited_visible_candidate": meta.get("allow_limited_visible_candidate") is True,
        "hold_for_product_quality_qa": meta.get("hold_for_product_quality_qa") is True,
        "blocked": meta.get("blocked") is True,
        "rejection_reasons": _dedupe(meta.get("rejection_reasons")),
        "public_meta_summary_only": True,
        "public_response_key_added": False,
        "response_shape_changed": False,
        "raw_text_included": False,
        "comment_text_body_included": False,
        "history_raw_text_included": False,
    }
    assert_user_label_connection_p5_safety_guard_contract(summary, allow_partial=True)
    return summary


def assert_user_label_connection_p5_safety_guard_contract(value: Any, *, allow_partial: bool = False) -> None:
    if _contains_text_payload_key(value):
        raise ValueError("P5 safety guard must not include raw text/comment/surface payload keys")
    if _flag_true(value):
        raise ValueError("P5 safety guard contains a forbidden true flag")
    json.dumps(value, ensure_ascii=False, sort_keys=True)
    if allow_partial:
        return
    if not isinstance(value, Mapping):
        raise ValueError("P5 safety guard must be a mapping")
    if value.get("schema_version") != USER_LABEL_CONNECTION_P5_SAFETY_GUARD_SCHEMA_VERSION:
        raise ValueError("unexpected P5 safety guard schema_version")
    if value.get("step") != USER_LABEL_CONNECTION_P5_SAFETY_GUARD_STEP:
        raise ValueError("unexpected P5 safety guard step")
    if value.get("decision") not in {DECISION_ALLOW, DECISION_WARN, DECISION_BLOCK}:
        raise ValueError("unexpected P5 safety guard decision")
    if value.get("decision") == DECISION_ALLOW:
        if value.get("allow_limited_visible_candidate") is not True:
            raise ValueError("P5 safety guard allow decision must allow limited visible candidate")
        risks = _safe_mapping(value.get("risk_summary"))
        if any(item is True for item in risks.values()):
            raise ValueError("P5 safety guard allow decision must not carry detected risk")
    public_contract = _safe_mapping(value.get("public_contract"))
    body_free = _safe_mapping(value.get("body_free"))
    for key in ("rn_visible_contract_changed", "public_response_key_added", "response_shape_changed", "db_schema_changed", "fixed_sentence_template_added", "gate_relaxed"):
        if public_contract.get(key) is not False:
            raise ValueError(f"P5 safety public_contract.{key} must be false")
    for key in ("raw_text_included", "comment_text_body_included", "candidate_body_included", "surface_body_included", "history_raw_text_included"):
        if body_free.get(key) is not False:
            raise ValueError(f"P5 safety body_free.{key} must be false")


__all__ = [
    "USER_LABEL_CONNECTION_P5_SAFETY_GUARD_SCHEMA_VERSION",
    "USER_LABEL_CONNECTION_P5_SAFETY_GUARD_STEP",
    "USER_LABEL_CONNECTION_P5_SAFETY_GUARD_SOURCE",
    "DECISION_ALLOW",
    "DECISION_WARN",
    "DECISION_BLOCK",
    "build_user_label_connection_p5_safety_guard",
    "user_label_connection_p5_safety_guard_public_summary",
    "assert_user_label_connection_p5_safety_guard_contract",
]
