# -*- coding: utf-8 -*-
from __future__ import annotations

"""R7 limited visible surface connection for P6 Structure Insight.

This module is the narrow bridge from the P6 runtime-evaluation chain into the
already-passed ``input_feedback.comment_text`` visible body.  It only permits one
soft Structure Insight seed for ``structure_question``.  It never adds public
response keys, never changes RN/API/DB contracts, and never places the generated
surface body inside metadata.
"""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
import json
from types import SimpleNamespace
from typing import Any, Final

from emlis_ai_structure_insight_p6_family_boundary import (
    DECISION_ALLOW_LIMITED_SURFACE,
    assert_structure_insight_p6_family_boundary_contract,
)
from emlis_ai_structure_insight_p6_gate_hardening import (
    GATE_DECISION_ALLOW_INTERNAL_SURFACE_CANDIDATE,
    assert_structure_insight_p6_gate_hardening_contract,
)
from emlis_ai_structure_insight_p6_quality_rubric import (
    VERDICT_PASS,
    VERDICT_STRUCTURE_INSIGHT_READY,
    assert_structure_insight_p6_quality_rubric_contract,
)
from emlis_ai_structure_insight_p6_relation_policy import (
    VISIBILITY_ALLOW_INITIAL_VISIBLE,
    assert_structure_insight_p6_relation_policy_contract,
)
from emlis_ai_structure_insight_p6_surface_role_plan import (
    SURFACE_PLAN_LIMITED_STRUCTURE_INSIGHT_SEED,
    assert_structure_insight_p6_surface_role_plan_contract,
)
from emlis_ai_structure_insight_surface import build_structure_insight_surface_for_line


STRUCTURE_INSIGHT_P6_LIMITED_SURFACE_CONNECTION_SCHEMA_VERSION: Final = (
    "cocolon.emlis.structure_insight.p6_limited_surface_connection.r7.v1"
)
STRUCTURE_INSIGHT_P6_LIMITED_SURFACE_CONNECTION_STEP: Final = (
    "R7_P6_LimitedSurfaceStructureQuestionOnly_20260612"
)
STRUCTURE_INSIGHT_P6_LIMITED_SURFACE_CONNECTION_SOURCE: Final = (
    "Cocolon_EmlisAI_P5_P6_RedLedger_RuntimeRepair_R7_20260612"
)
STRUCTURE_INSIGHT_P6_NO_CONNECT_REGRESSION_STEP: Final = (
    "R8_NoConnectFamilySafetyLowInfoDailyPositiveRegression_20260612"
)

FAMILY_STRUCTURE_QUESTION: Final = "structure_question"
VISIBLE_FAMILY_NONE: Final = "none"
SECTION_PLACEMENT_SEEN_SECTION: Final = "seen_section"
SURFACE_ROUTE_R7_LIMITED_STRUCTURE_QUESTION: Final = "p6_r7_structure_question_limited_surface"

REASON_EXISTING_COMMENT_TEXT_MISSING: Final = "existing_comment_text_missing"
REASON_OBSERVATION_STATUS_NOT_PASSED: Final = "observation_status_not_passed"
REASON_EXISTING_GATE_REPORT_MISSING: Final = "existing_gate_report_missing"
REASON_EXISTING_GATE_BLOCKED: Final = "existing_gate_blocked"
REASON_FAMILY_NOT_STRUCTURE_QUESTION: Final = "p6_limited_surface_family_not_structure_question"
REASON_P6_FAMILY_BOUNDARY_NOT_ALLOWING_SURFACE: Final = "p6_family_boundary_not_allowing_surface"
REASON_P6_RELATION_POLICY_NOT_INITIAL_VISIBLE: Final = "p6_relation_policy_not_initial_visible"
REASON_P6_QUALITY_RUBRIC_NOT_READY: Final = "p6_quality_rubric_not_structure_ready"
REASON_P6_GATE_HARDENING_NOT_PASSED: Final = "p6_gate_hardening_not_passed"
REASON_P6_SURFACE_ROLE_PLAN_NOT_LIMITED_SEED: Final = "p6_surface_role_plan_not_limited_structure_insight_seed"
REASON_INSIGHT_SEED_COUNT_ABOVE_LIMIT: Final = "p6_insight_seed_count_above_limit"
REASON_SURFACE_CANDIDATE_NOT_AVAILABLE: Final = "p6_surface_candidate_not_available"
REASON_STRUCTURE_SURFACE_GATE_NOT_PASSED: Final = "structure_insight_surface_gate_not_passed"
REASON_RAW_TEXT_PAYLOAD_DETECTED: Final = "raw_text_payload_detected"
REASON_CONTRACT_MUTATION_DETECTED: Final = "contract_mutation_detected"
REASON_UPSTREAM_CONTRACT_INVALID: Final = "upstream_contract_invalid"
REASON_P6_POST_CONNECTION_GATE_BLOCKED: Final = "p6_post_connection_gate_blocked"

_REQUIRED_EXISTING_GATE_ALIASES: Final[dict[str, tuple[str, ...]]] = {
    "display_gate": ("tone_guard", "display_gate", "reader_gate", "reader"),
    "grounding": ("grounding", "grounding_gate", "grounding_report"),
    "template_echo": ("template_echo", "template_gate", "template_echo_report"),
    "safety": ("safety", "safety_gate", "safety_report"),
    "runtime_surface_pre_return_gate": ("runtime_surface_pre_return_gate", "runtime_surface_gate"),
    "visible_surface_acceptance_gate": ("visible_surface_acceptance_gate", "visible_surface_gate"),
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
        "observation_text",
        "reception_text",
        "reviewer_note",
        "reviewer_notes",
        "reviewer_free_text",
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
        "comment_text_body_included",
        "candidate_body_included",
        "surface_body_included",
        "history_raw_text_included",
        "reviewer_free_text_included",
        "fixed_sentence_template_added",
        "fixed_sentence_template_used",
        "input_specific_template_added",
        "input_specific_template_used",
        "diagnosis_allowed",
        "personality_claim_allowed",
        "cause_claim_allowed",
        "advice_allowed",
        "future_prediction_allowed",
        "target_judgement_allowed",
        "public_release_applied",
        "release_allowed",
        "product_quality_released",
        "machine_metrics_used_for_read_feeling",
        "read_feeling_auto_filled_from_machine_metrics",
        "external_ai_used",
        "local_llm_used",
    }
)


@dataclass(frozen=True)
class StructureInsightP6LimitedSurfaceConnection:
    comment_text: str
    applied: bool
    meta: dict[str, Any]

    def as_meta(self) -> dict[str, Any]:
        return dict(self.meta)


def _clean(value: Any) -> str:
    if value is None or isinstance(value, (Mapping, list, tuple, set)):
        return ""
    return str(value).replace("\u3000", " ").strip()


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


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _summary(value: Mapping[str, Any]) -> dict[str, Any]:
    return _safe_mapping(value.get("summary")) or dict(value)


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


def _contract_invalid(name: str, value: Mapping[str, Any], checker: Any) -> list[str]:
    if not value:
        return []
    try:
        checker(value, allow_partial=True)
    except (TypeError, ValueError):
        return [f"{REASON_UPSTREAM_CONTRACT_INVALID}:{name}"]
    return []


def _gate_passed(report: Any) -> bool:
    if isinstance(report, bool):
        return report is True
    meta = _safe_mapping(report)
    if not meta:
        return False
    if meta.get("blocked") is True or meta.get("passed") is False:
        return False
    if meta.get("passed") is True or meta.get("safe") is True:
        return True
    action = _clean(meta.get("action")).lower()
    classification = _clean(meta.get("classification")).lower()
    status = _clean(meta.get("status")).lower()
    if action in {"allow", "pass", "passed", "accept", "ok"}:
        return True
    if classification in {"green", "safe", "accepted", "passed", "pass", "ok"}:
        return True
    if status in {"passed", "pass", "ok", "accepted", "safe"}:
        return True
    return False


def _primary_reason(report: Any, fallback: str) -> str:
    meta = _safe_mapping(report)
    reason = _clean(meta.get("primary_reason") or meta.get("reason") or meta.get("blocker_reason"))
    if reason:
        return reason
    reasons = _dedupe(meta.get("rejection_reasons") or meta.get("blocker_reason_codes"))
    return reasons[0] if reasons else fallback


def _resolve_gate_report(reports: Mapping[str, Any], aliases: Sequence[str]) -> tuple[str, Any]:
    for alias in aliases:
        if alias in reports:
            return alias, reports[alias]
    return "", None


def _existing_gate_summary(existing_gate_reports: Mapping[str, Any] | None) -> tuple[bool, dict[str, dict[str, Any]], list[str]]:
    reports = _safe_mapping(existing_gate_reports)
    summary: dict[str, dict[str, Any]] = {}
    reasons: list[str] = []
    for gate_name, aliases in _REQUIRED_EXISTING_GATE_ALIASES.items():
        matched_name, report = _resolve_gate_report(reports, aliases)
        if not matched_name:
            summary[gate_name] = {"passed": False, "source_gate": "", "primary_reason": REASON_EXISTING_GATE_REPORT_MISSING}
            reasons.append(f"{REASON_EXISTING_GATE_REPORT_MISSING}:{gate_name}")
            continue
        passed = _gate_passed(report)
        primary = "" if passed else _primary_reason(report, f"{REASON_EXISTING_GATE_BLOCKED}:{gate_name}")
        summary[gate_name] = {
            "passed": passed,
            "source_gate": matched_name,
            "primary_reason": primary or None,
        }
        if not passed:
            reasons.append(primary or f"{REASON_EXISTING_GATE_BLOCKED}:{gate_name}")
    return not reasons, summary, _dedupe(reasons)


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
        "input_specific_template_added": False,
        "release_allowed": False,
        "public_release_applied": False,
        "product_quality_released": False,
    }


def _body_free_contract() -> dict[str, bool]:
    return {
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_body_included": False,
        "comment_text_body_in_meta_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "surface_text_body_included": False,
        "history_raw_text_included": False,
        "reviewer_free_text_included": False,
        "actual_appended_line_included": False,
    }


def _family_from_sources(*sources: Mapping[str, Any]) -> str:
    for source in sources:
        summary = _summary(source)
        family = _clean(summary.get("family") or summary.get("runtime_family") or summary.get("visible_family"))
        if family:
            return family
    return VISIBLE_FAMILY_NONE


def _relation_from_sources(*sources: Mapping[str, Any]) -> str:
    for source in sources:
        summary = _summary(source)
        relation = _clean(summary.get("relation_family"))
        if relation:
            return relation
    return ""


def _surface_key(meta: Mapping[str, Any]) -> str:
    return _clean(
        meta.get("structure_insight_surface_key")
        or meta.get("structure_insight_surface_ending_key")
        or meta.get("surface_key")
    )


def _relation_type_for_surface_probe(relation_family: str) -> str:
    relation = _clean(relation_family)
    if relation in {"mixed_emotion_coexistence", "uncertainty_effort_pair"}:
        return "coexistence"
    if relation == "effort_residue":
        return "recovery"
    if relation == "value_line_crossed":
        return "boundary"
    return "approach_avoidance"


def _build_surface_candidate(
    *,
    family: str,
    relation_family: str,
    proposed_surface: Any,
    structure_insight_surface_meta: Mapping[str, Any] | None,
) -> tuple[str, dict[str, Any]]:
    explicit = _clean(proposed_surface)
    existing_meta = _safe_mapping(structure_insight_surface_meta)
    if explicit:
        return explicit, existing_meta
    if family != FAMILY_STRUCTURE_QUESTION:
        return "", existing_meta

    line = SimpleNamespace(
        roles=["observation_insight_seed", "soft_inference_surface_required"],
        relation_type=_relation_type_for_surface_probe(relation_family),
        meta={
            "relation_type": relation_family,
            "connectable_family": FAMILY_STRUCTURE_QUESTION,
            "coverage_group": "structure_question",
        },
    )
    surface, generated_meta = build_structure_insight_surface_for_line(
        line,
        section_id="observation",
        two_stage_meta={
            "two_stage_reception_mode_id": "structure_question_observation",
            "mode_id": "structure_question_observation",
            "connectable_family": FAMILY_STRUCTURE_QUESTION,
            "fixture_family": "structure_question",
            "coverage_group": "structure_question",
            "section_id": "observation",
        },
    )
    safe_meta = dict(existing_meta)
    safe_meta.update(_safe_mapping(generated_meta))
    return _clean(surface), safe_meta



def build_structure_insight_p6_limited_surface_candidate_probe(
    *,
    family: Any = FAMILY_STRUCTURE_QUESTION,
    relation_family: Any = "",
) -> tuple[str, dict[str, Any]]:
    """Build an internal one-seed probe for P6-5 gate hardening.

    The returned surface is for in-memory gate evaluation only.  The returned
    metadata is body-free and may be carried into R7 summaries.
    """

    resolved_family = _clean(family) or VISIBLE_FAMILY_NONE
    resolved_relation = _clean(relation_family)
    return _build_surface_candidate(
        family=resolved_family,
        relation_family=resolved_relation,
        proposed_surface="",
        structure_insight_surface_meta=None,
    )


def propose_structure_insight_p6_limited_surface_seed(
    *,
    family: Any = FAMILY_STRUCTURE_QUESTION,
    relation_family: Any = "",
) -> str:
    """Return only the in-memory seed text; no body text is serialized in meta."""

    surface, _meta = build_structure_insight_p6_limited_surface_candidate_probe(
        family=family,
        relation_family=relation_family,
    )
    return _clean(surface)


def _insert_seed_into_seen_section(existing_comment_text: str, seed: str) -> str:
    base = _clean(existing_comment_text)
    candidate = _clean(seed)
    if not base or not candidate:
        return base
    if "Emlisから:" in base:
        before, after = base.split("Emlisから:", 1)
        prefix = before.rstrip()
        if "見えたこと:" in prefix:
            updated_before = f"{prefix}\n{candidate}"
        else:
            updated_before = f"{prefix}\n\n見えたこと:\n{candidate}"
        return f"{updated_before}\n\nEmlisから:{after}"
    if "見えたこと:" in base:
        return f"{base}\n{candidate}"
    return f"{base}\n\n見えたこと:\n{candidate}"


def _meta(
    *,
    run_id: str,
    applied: bool,
    family: str,
    relation_family: str,
    surface_key: str,
    base_text_present: bool,
    observation_status: str,
    gate_summary: Mapping[str, Mapping[str, Any]],
    gate_reports_passed: bool,
    rejection_reasons: Sequence[Any],
    p6_family_boundary_allows_surface: bool,
    p6_relation_policy_initial_visible: bool,
    p6_quality_rubric_ready: bool,
    p6_gate_hardening_passed: bool,
    p6_surface_role_plan_limited_seed: bool,
    structure_surface_meta: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    safe_surface_meta = _safe_mapping(structure_surface_meta)
    seed_count = 1 if applied else 0
    meta = {
        "schema_version": STRUCTURE_INSIGHT_P6_LIMITED_SURFACE_CONNECTION_SCHEMA_VERSION,
        "version": STRUCTURE_INSIGHT_P6_LIMITED_SURFACE_CONNECTION_SCHEMA_VERSION,
        "step": STRUCTURE_INSIGHT_P6_LIMITED_SURFACE_CONNECTION_STEP,
        "source": STRUCTURE_INSIGHT_P6_LIMITED_SURFACE_CONNECTION_SOURCE,
        "run_id": run_id,
        "r7_limited_surface_evaluated": True,
        "r7_limited_surface_connected": bool(applied),
        "p6_limited_surface_r7_evaluated": True,
        "p6_limited_surface_r7_connected": bool(applied),
        "evaluated": True,
        "applied": bool(applied),
        "visible_applied": bool(applied),
        "p6_visible_applied": bool(applied),
        "limited_surface_applied": bool(applied),
        "comment_text_connected": bool(applied),
        "runtime_surface_connected": bool(applied),
        "visible_surface_connected": bool(applied),
        "visible_family": FAMILY_STRUCTURE_QUESTION if applied else VISIBLE_FAMILY_NONE,
        "runtime_family": family or VISIBLE_FAMILY_NONE,
        "family": family or VISIBLE_FAMILY_NONE,
        "r8_no_connect_regression": True,
        "r8_regression_step": STRUCTURE_INSIGHT_P6_NO_CONNECT_REGRESSION_STEP,
        "no_connect_family_runtime": "" if family == FAMILY_STRUCTURE_QUESTION else (family or VISIBLE_FAMILY_NONE),
        "no_connect_family_blocked": bool(family != FAMILY_STRUCTURE_QUESTION and not applied),
        "no_connect_family_runtime_blocked": bool(family != FAMILY_STRUCTURE_QUESTION and not applied),
        "no_deep_insight_for_daily": True,
        "no_deep_insight_for_low_information": True,
        "no_deep_insight_for_positive_only": True,
        "no_deep_insight_for_safety_adjacent": True,
        "structure_question_only": True,
        "limited_to_structure_question": True,
        "no_connect_family_preserved": family == FAMILY_STRUCTURE_QUESTION or not applied,
        "no_connect_family_visible_applied": False,
        "relation_family": relation_family,
        "surface_key": surface_key,
        "surface_candidate_key": surface_key,
        "structure_insight_surface_key": surface_key,
        "section_placement": SECTION_PLACEMENT_SEEN_SECTION,
        "p6_limited_surface_route": SURFACE_ROUTE_R7_LIMITED_STRUCTURE_QUESTION,
        "comment_text_owner": "input_feedback.comment_text",
        "input_feedback_comment_text_only_visible_body": True,
        "existing_comment_text_present": bool(base_text_present),
        "observation_status": observation_status,
        "observation_status_passed": observation_status == "passed",
        "existing_gate_reports_passed": bool(gate_reports_passed),
        "existing_gate_reports": {key: dict(value) for key, value in gate_summary.items()},
        "p6_family_boundary_allows_surface": bool(p6_family_boundary_allows_surface),
        "p6_relation_policy_initial_visible": bool(p6_relation_policy_initial_visible),
        "p6_quality_rubric_ready": bool(p6_quality_rubric_ready),
        "p6_gate_hardening_passed": bool(p6_gate_hardening_passed),
        "p6_surface_role_plan_limited_seed": bool(p6_surface_role_plan_limited_seed),
        "insight_seed_count": seed_count,
        "requested_insight_seed_count": 1 if family == FAMILY_STRUCTURE_QUESTION else 0,
        "max_insight_seed_count": 1,
        "planned_insight_seed_count": seed_count,
        "actual_appended_line_in_meta_included": False,
        "surface_body_returned_in_meta": False,
        "candidate_body_returned_in_meta": False,
        "post_connection_regate_required": True,
        "post_connection_gate_passed": bool(applied),
        "p6_post_connection_gate_blocked": False,
        "gate_threshold_relaxed": False,
        "diagnosis_blocked": True,
        "personality_classification_blocked": True,
        "cause_assertion_blocked": True,
        "future_prediction_blocked": True,
        "action_instruction_blocked": True,
        "target_judgement_blocked": True,
        "fixed_sentence_template_added": False,
        "input_specific_template_added": False,
        "release_allowed": False,
        "public_release_applied": False,
        "product_quality_released": False,
        "structure_insight_surface_meta_summary": {
            "structure_insight_surface_key": _surface_key(safe_surface_meta),
            "structure_insight_surface_applied": safe_surface_meta.get("structure_insight_surface_applied") is True,
            "structure_insight_surface_gate_passed": safe_surface_meta.get("structure_insight_surface_gate_passed") is True,
            "structure_insight_surface_insight_seed_added": safe_surface_meta.get("structure_insight_surface_insight_seed_added") is True,
            "structure_insight_surface_public_response_key_added": False,
            "structure_insight_surface_comment_text_body_included": False,
            "structure_insight_surface_raw_input_included": False,
            "structure_insight_surface_candidate_body_included": False,
            "structure_insight_surface_surface_text_body_included": False,
        },
        "rejection_reasons": _dedupe(rejection_reasons),
        "blocked_reason_codes": _dedupe(rejection_reasons),
        "public_contract": _public_contract(),
        "body_free": _body_free_contract(),
    }
    assert_structure_insight_p6_limited_surface_connection_contract(meta)
    return meta


def _blocked_result(
    *,
    existing_comment_text: str,
    run_id: str,
    family: str,
    relation_family: str,
    surface_key: str,
    base_text_present: bool,
    observation_status: str,
    gate_summary: Mapping[str, Mapping[str, Any]],
    gate_reports_passed: bool,
    rejection_reasons: Sequence[Any],
    p6_family_boundary_allows_surface: bool,
    p6_relation_policy_initial_visible: bool,
    p6_quality_rubric_ready: bool,
    p6_gate_hardening_passed: bool,
    p6_surface_role_plan_limited_seed: bool,
    structure_surface_meta: Mapping[str, Any] | None = None,
) -> StructureInsightP6LimitedSurfaceConnection:
    meta = _meta(
        run_id=run_id,
        applied=False,
        family=family,
        relation_family=relation_family,
        surface_key=surface_key,
        base_text_present=base_text_present,
        observation_status=observation_status,
        gate_summary=gate_summary,
        gate_reports_passed=gate_reports_passed,
        rejection_reasons=rejection_reasons,
        p6_family_boundary_allows_surface=p6_family_boundary_allows_surface,
        p6_relation_policy_initial_visible=p6_relation_policy_initial_visible,
        p6_quality_rubric_ready=p6_quality_rubric_ready,
        p6_gate_hardening_passed=p6_gate_hardening_passed,
        p6_surface_role_plan_limited_seed=p6_surface_role_plan_limited_seed,
        structure_surface_meta=structure_surface_meta,
    )
    return StructureInsightP6LimitedSurfaceConnection(comment_text=existing_comment_text, applied=False, meta=meta)


def build_structure_insight_p6_limited_surface_connection(
    existing_comment_text: Any,
    *,
    observation_status: Any = "",
    p6_entry_freeze: Mapping[str, Any] | None = None,
    p6_family_boundary: Mapping[str, Any] | None = None,
    p6_relation_policy: Mapping[str, Any] | None = None,
    p6_quality_rubric: Mapping[str, Any] | None = None,
    p6_gate_hardening: Mapping[str, Any] | None = None,
    p6_surface_role_plan: Mapping[str, Any] | None = None,
    existing_gate_reports: Mapping[str, Any] | None = None,
    proposed_surface: Any = "",
    insight_seed_text: Any = "",
    structure_insight_surface_meta: Mapping[str, Any] | None = None,
    upstream_meta: Mapping[str, Any] | None = None,
    safety_context: Any = None,
    run_id: str | None = None,
) -> StructureInsightP6LimitedSurfaceConnection:
    """Apply one R7 Structure Insight seed only for safe ``structure_question``."""

    base_text = _clean(existing_comment_text)
    status = _clean(observation_status).lower()
    family_boundary = _safe_mapping(p6_family_boundary)
    relation_policy = _safe_mapping(p6_relation_policy)
    quality_rubric = _safe_mapping(p6_quality_rubric)
    gate_hardening = _safe_mapping(p6_gate_hardening)
    surface_role_plan = _safe_mapping(p6_surface_role_plan)
    upstream = _safe_mapping(upstream_meta)
    entry_freeze = _safe_mapping(p6_entry_freeze)
    sources = [
        entry_freeze,
        family_boundary,
        relation_policy,
        quality_rubric,
        gate_hardening,
        surface_role_plan,
        _safe_mapping(existing_gate_reports),
        upstream,
    ]

    boundary_summary = _summary(family_boundary)
    policy_summary = _summary(relation_policy)
    quality_summary = _summary(quality_rubric)
    gate_summary_source = _summary(gate_hardening)
    surface_plan_summary = _summary(surface_role_plan)

    family = _family_from_sources(surface_role_plan, family_boundary)
    relation_family = _relation_from_sources(surface_role_plan, relation_policy)
    gate_reports_passed, gate_summary, gate_reasons = _existing_gate_summary(existing_gate_reports)

    surface_candidate, structure_surface_meta = _build_surface_candidate(
        family=family,
        relation_family=relation_family,
        proposed_surface=proposed_surface or insight_seed_text,
        structure_insight_surface_meta=structure_insight_surface_meta,
    )
    surface_key = _surface_key(structure_surface_meta)

    p6_family_boundary_allows_surface = (
        family == FAMILY_STRUCTURE_QUESTION
        and boundary_summary.get("decision") == DECISION_ALLOW_LIMITED_SURFACE
        and boundary_summary.get("allow_limited_surface") is True
    )
    p6_relation_policy_initial_visible = policy_summary.get("visibility_decision") == VISIBILITY_ALLOW_INITIAL_VISIBLE
    p6_quality_rubric_ready = _clean(quality_summary.get("verdict")) in {VERDICT_PASS, VERDICT_STRUCTURE_INSIGHT_READY}
    p6_gate_hardening_passed = (
        gate_summary_source.get("decision") == GATE_DECISION_ALLOW_INTERNAL_SURFACE_CANDIDATE
        and gate_summary_source.get("passed") is True
    )
    p6_surface_role_plan_limited_seed = (
        surface_plan_summary.get("surface_plan_kind") == SURFACE_PLAN_LIMITED_STRUCTURE_INSIGHT_SEED
        and surface_plan_summary.get("limited_surface_candidate") is True
        and _int(surface_plan_summary.get("planned_insight_seed_count")) <= 1
        and _int(surface_plan_summary.get("requested_insight_seed_count")) <= 1
        and surface_plan_summary.get("fixed_sentence_template_added") is not True
    )
    boundary_no_connect_reasons = _dedupe(boundary_summary.get("no_connect_reason_codes"))

    reasons: list[str] = []
    if any(_contains_text_payload_key(source) for source in sources):
        reasons.append(REASON_RAW_TEXT_PAYLOAD_DETECTED)
    if any(_flag_true(source) for source in sources):
        reasons.append(REASON_CONTRACT_MUTATION_DETECTED)
    reasons.extend(_contract_invalid("p6_family_boundary", family_boundary, assert_structure_insight_p6_family_boundary_contract))
    reasons.extend(_contract_invalid("p6_relation_policy", relation_policy, assert_structure_insight_p6_relation_policy_contract))
    reasons.extend(_contract_invalid("p6_quality_rubric", quality_rubric, assert_structure_insight_p6_quality_rubric_contract))
    reasons.extend(_contract_invalid("p6_gate_hardening", gate_hardening, assert_structure_insight_p6_gate_hardening_contract))
    reasons.extend(_contract_invalid("p6_surface_role_plan", surface_role_plan, assert_structure_insight_p6_surface_role_plan_contract))
    if not base_text:
        reasons.append(REASON_EXISTING_COMMENT_TEXT_MISSING)
    if status != "passed":
        reasons.append(REASON_OBSERVATION_STATUS_NOT_PASSED)
    if not gate_reports_passed:
        reasons.extend(gate_reasons)
    if family != FAMILY_STRUCTURE_QUESTION:
        reasons.append(f"{REASON_FAMILY_NOT_STRUCTURE_QUESTION}:{family or VISIBLE_FAMILY_NONE}")
        reasons.extend(boundary_no_connect_reasons or [f"no_connect_family:{family or VISIBLE_FAMILY_NONE}"])
    if not p6_family_boundary_allows_surface:
        reasons.append(REASON_P6_FAMILY_BOUNDARY_NOT_ALLOWING_SURFACE)
    if not p6_relation_policy_initial_visible:
        reasons.append(REASON_P6_RELATION_POLICY_NOT_INITIAL_VISIBLE)
    if not p6_quality_rubric_ready:
        reasons.append(REASON_P6_QUALITY_RUBRIC_NOT_READY)
    if not p6_gate_hardening_passed:
        reasons.append(REASON_P6_GATE_HARDENING_NOT_PASSED)
    if not p6_surface_role_plan_limited_seed:
        reasons.append(REASON_P6_SURFACE_ROLE_PLAN_NOT_LIMITED_SEED)
    if _int(surface_plan_summary.get("requested_insight_seed_count")) > 1:
        reasons.append(REASON_INSIGHT_SEED_COUNT_ABOVE_LIMIT)
    if not surface_candidate:
        reasons.append(REASON_SURFACE_CANDIDATE_NOT_AVAILABLE)
    if structure_surface_meta and structure_surface_meta.get("structure_insight_surface_gate_passed") is False:
        reasons.append(REASON_STRUCTURE_SURFACE_GATE_NOT_PASSED)
    reasons = _dedupe(reasons)

    run = run_id or "p6_limited_surface_connection_r7"
    if reasons:
        return _blocked_result(
            existing_comment_text=base_text,
            run_id=run,
            family=family,
            relation_family=relation_family,
            surface_key=surface_key,
            base_text_present=bool(base_text),
            observation_status=status,
            gate_summary=gate_summary,
            gate_reports_passed=gate_reports_passed,
            rejection_reasons=reasons,
            p6_family_boundary_allows_surface=p6_family_boundary_allows_surface,
            p6_relation_policy_initial_visible=p6_relation_policy_initial_visible,
            p6_quality_rubric_ready=p6_quality_rubric_ready,
            p6_gate_hardening_passed=p6_gate_hardening_passed,
            p6_surface_role_plan_limited_seed=p6_surface_role_plan_limited_seed,
            structure_surface_meta=structure_surface_meta,
        )

    connected_text = _insert_seed_into_seen_section(base_text, surface_candidate)
    meta = _meta(
        run_id=run,
        applied=True,
        family=family,
        relation_family=relation_family,
        surface_key=surface_key,
        base_text_present=True,
        observation_status=status,
        gate_summary=gate_summary,
        gate_reports_passed=gate_reports_passed,
        rejection_reasons=[],
        p6_family_boundary_allows_surface=p6_family_boundary_allows_surface,
        p6_relation_policy_initial_visible=p6_relation_policy_initial_visible,
        p6_quality_rubric_ready=p6_quality_rubric_ready,
        p6_gate_hardening_passed=p6_gate_hardening_passed,
        p6_surface_role_plan_limited_seed=p6_surface_role_plan_limited_seed,
        structure_surface_meta=structure_surface_meta,
    )
    return StructureInsightP6LimitedSurfaceConnection(comment_text=connected_text, applied=True, meta=meta)


def structure_insight_p6_limited_surface_connection_public_summary(
    value: Mapping[str, Any] | StructureInsightP6LimitedSurfaceConnection | None,
) -> dict[str, Any]:
    meta = _safe_mapping(value)
    if not meta:
        return {}
    if _contains_text_payload_key(meta) or _flag_true(meta):
        return {
            "schema_version": STRUCTURE_INSIGHT_P6_LIMITED_SURFACE_CONNECTION_SCHEMA_VERSION,
            "step": STRUCTURE_INSIGHT_P6_LIMITED_SURFACE_CONNECTION_STEP,
            "r7_limited_surface_evaluated": True,
            "r7_limited_surface_connected": False,
            "p6_limited_surface_r7_connected": False,
            "visible_applied": False,
            "visible_family": VISIBLE_FAMILY_NONE,
            "rejection_reasons": ["p6_limited_surface_public_meta_unsafe"],
            "public_meta_summary_only": True,
            "public_response_key_added": False,
            "response_shape_changed": False,
            "raw_text_included": False,
            "comment_text_body_included": False,
            "candidate_body_included": False,
            "surface_body_included": False,
            "release_allowed": False,
        }
    summary = {
        "schema_version": STRUCTURE_INSIGHT_P6_LIMITED_SURFACE_CONNECTION_SCHEMA_VERSION,
        "step": STRUCTURE_INSIGHT_P6_LIMITED_SURFACE_CONNECTION_STEP,
        "r7_limited_surface_evaluated": meta.get("r7_limited_surface_evaluated") is True,
        "r7_limited_surface_connected": meta.get("r7_limited_surface_connected") is True,
        "p6_limited_surface_r7_connected": meta.get("p6_limited_surface_r7_connected") is True,
        "evaluated": meta.get("evaluated") is True,
        "applied": meta.get("applied") is True,
        "visible_applied": meta.get("visible_applied") is True,
        "p6_visible_applied": meta.get("p6_visible_applied") is True,
        "visible_family": _clean(meta.get("visible_family")) or VISIBLE_FAMILY_NONE,
        "runtime_family": _clean(meta.get("runtime_family")) or VISIBLE_FAMILY_NONE,
        "r8_no_connect_regression": True,
        "r8_regression_step": STRUCTURE_INSIGHT_P6_NO_CONNECT_REGRESSION_STEP,
        "no_connect_family_runtime": _clean(meta.get("no_connect_family_runtime")),
        "no_connect_family_blocked": meta.get("no_connect_family_blocked") is True,
        "no_connect_family_runtime_blocked": meta.get("no_connect_family_runtime_blocked") is True,
        "no_connect_family_visible_applied": False,
        "no_deep_insight_for_daily": True,
        "no_deep_insight_for_low_information": True,
        "no_deep_insight_for_positive_only": True,
        "no_deep_insight_for_safety_adjacent": True,
        "structure_question_only": True,
        "limited_to_structure_question": True,
        "no_connect_family_preserved": meta.get("no_connect_family_preserved") is True,
        "no_connect_family_visible_applied": meta.get("no_connect_family_visible_applied") is True,
        "relation_family": _clean(meta.get("relation_family")),
        "surface_key": _clean(meta.get("surface_key")),
        "section_placement": _clean(meta.get("section_placement")) or SECTION_PLACEMENT_SEEN_SECTION,
        "p6_limited_surface_route": _clean(meta.get("p6_limited_surface_route")) or SURFACE_ROUTE_R7_LIMITED_STRUCTURE_QUESTION,
        "comment_text_owner": "input_feedback.comment_text",
        "insight_seed_count": _int(meta.get("insight_seed_count")),
        "max_insight_seed_count": 1,
        "post_connection_regate_required": True,
        "post_connection_gate_passed": meta.get("post_connection_gate_passed") is True,
        "p6_post_connection_gate_blocked": meta.get("p6_post_connection_gate_blocked") is True,
        "gate_threshold_relaxed": False,
        "diagnosis_blocked": True,
        "personality_classification_blocked": True,
        "cause_assertion_blocked": True,
        "future_prediction_blocked": True,
        "action_instruction_blocked": True,
        "target_judgement_blocked": True,
        "fixed_sentence_template_added": False,
        "input_specific_template_added": False,
        "rejection_reasons": _dedupe(meta.get("rejection_reasons")),
        "blocked_reason_codes": _dedupe(meta.get("blocked_reason_codes") or meta.get("rejection_reasons")),
        "public_response_key_added": False,
        "response_shape_changed": False,
        "rn_visible_contract_changed": False,
        "api_route_changed": False,
        "db_schema_changed": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "reviewer_free_text_included": False,
        "actual_appended_line_included": False,
        "release_allowed": False,
    }
    assert_structure_insight_p6_limited_surface_connection_contract(summary, allow_partial=True)
    return summary


def assert_structure_insight_p6_limited_surface_connection_contract(value: Any, *, allow_partial: bool = False) -> None:
    meta = _safe_mapping(value)
    if _contains_text_payload_key(meta):
        raise ValueError("P6 limited surface connection meta must not include raw/comment/surface body keys")
    if _flag_true(meta):
        raise ValueError("P6 limited surface connection meta contains a forbidden true flag")
    json.dumps(meta, ensure_ascii=False, sort_keys=True)
    if allow_partial:
        return
    if not meta:
        raise ValueError("P6 limited surface connection meta must be a mapping")
    if meta.get("schema_version") != STRUCTURE_INSIGHT_P6_LIMITED_SURFACE_CONNECTION_SCHEMA_VERSION:
        raise ValueError("unexpected P6 limited surface connection schema_version")
    if meta.get("step") != STRUCTURE_INSIGHT_P6_LIMITED_SURFACE_CONNECTION_STEP:
        raise ValueError("unexpected P6 limited surface connection step")
    if meta.get("structure_question_only") is not True or meta.get("limited_to_structure_question") is not True:
        raise ValueError("P6 limited surface must stay restricted to structure_question")
    if _int(meta.get("max_insight_seed_count")) != 1:
        raise ValueError("P6 limited surface max_insight_seed_count must stay one")
    public_contract = _safe_mapping(meta.get("public_contract"))
    body_free = _safe_mapping(meta.get("body_free"))
    for key in (
        "rn_visible_contract_changed",
        "rn_visible_title_changed",
        "public_response_key_added",
        "response_shape_changed",
        "api_route_changed",
        "request_key_changed",
        "db_schema_changed",
        "fixed_sentence_template_added",
        "input_specific_template_added",
        "release_allowed",
        "public_release_applied",
        "product_quality_released",
    ):
        if public_contract.get(key) is not False:
            raise ValueError(f"P6 limited surface public_contract.{key} must be false")
    for key in (
        "raw_input_included",
        "raw_text_included",
        "comment_text_body_included",
        "comment_text_body_in_meta_included",
        "candidate_body_included",
        "surface_body_included",
        "surface_text_body_included",
        "history_raw_text_included",
        "reviewer_free_text_included",
        "actual_appended_line_included",
    ):
        if body_free.get(key) is not False:
            raise ValueError(f"P6 limited surface body_free.{key} must be false")
    applied = meta.get("applied") is True
    for key in (
        "visible_applied",
        "p6_visible_applied",
        "limited_surface_applied",
        "comment_text_connected",
        "runtime_surface_connected",
        "visible_surface_connected",
    ):
        if meta.get(key) is not applied:
            raise ValueError(f"P6 limited surface meta requires {key}=applied")
    if applied:
        if meta.get("visible_family") != FAMILY_STRUCTURE_QUESTION:
            raise ValueError("P6 limited surface applied meta must be structure_question only")
        for key in (
            "existing_comment_text_present",
            "observation_status_passed",
            "existing_gate_reports_passed",
            "p6_family_boundary_allows_surface",
            "p6_relation_policy_initial_visible",
            "p6_quality_rubric_ready",
            "p6_gate_hardening_passed",
            "p6_surface_role_plan_limited_seed",
        ):
            if meta.get(key) is not True:
                raise ValueError(f"P6 limited surface applied meta requires {key}=true")
        if _int(meta.get("insight_seed_count")) != 1:
            raise ValueError("P6 limited surface applied meta must have exactly one insight seed")
        if _dedupe(meta.get("rejection_reasons")):
            raise ValueError("P6 limited surface applied meta must not have rejection reasons")
    else:
        if meta.get("visible_family") not in {VISIBLE_FAMILY_NONE, ""}:
            raise ValueError("P6 limited surface blocked meta must not expose non-none visible_family")
    if meta.get("release_allowed") is not False or meta.get("public_release_applied") is not False:
        raise ValueError("P6 limited surface must not set release flags")
    if meta.get("fixed_sentence_template_added") is not False:
        raise ValueError("P6 limited surface must not add fixed sentence template flags")
    if meta.get("comment_text_owner") != "input_feedback.comment_text":
        raise ValueError("P6 limited surface must keep input_feedback.comment_text as visible body owner")


__all__ = [
    "STRUCTURE_INSIGHT_P6_LIMITED_SURFACE_CONNECTION_SCHEMA_VERSION",
    "STRUCTURE_INSIGHT_P6_LIMITED_SURFACE_CONNECTION_STEP",
    "STRUCTURE_INSIGHT_P6_LIMITED_SURFACE_CONNECTION_SOURCE",
    "FAMILY_STRUCTURE_QUESTION",
    "SURFACE_ROUTE_R7_LIMITED_STRUCTURE_QUESTION",
    "REASON_P6_POST_CONNECTION_GATE_BLOCKED",
    "StructureInsightP6LimitedSurfaceConnection",
    "build_structure_insight_p6_limited_surface_candidate_probe",
    "propose_structure_insight_p6_limited_surface_seed",
    "build_structure_insight_p6_limited_surface_connection",
    "structure_insight_p6_limited_surface_connection_public_summary",
    "assert_structure_insight_p6_limited_surface_connection_contract",
]
