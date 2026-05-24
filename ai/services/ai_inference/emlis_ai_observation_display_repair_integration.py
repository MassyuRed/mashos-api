# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step 10 Display / Repair Integration for EmlisAI observation replies.

This module wires the already-defined observation reply branch into the public
``passed + comment_text`` display contract for the low-information branch.  It
is intentionally narrow:

* it only promotes inputs that Step 2 has routed as low-information;
* it never changes the public ``observation_status`` enum;
* it never changes RN/API/DB contracts;
* it does not use fixed fallback text or legacy safe fallback;
* it keeps Display Gate fail-closed by building branch-specific reader,
  grounding, and template reports, then passing them through the existing
  ``decide_emlis_observation_display`` function.
"""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
import re
from typing import Any, Final

from emlis_ai_bounded_repair_reroute import (
    ACTION_NO_REPAIR as BOUNDED_ACTION_NO_REPAIR,
    ACTION_RERENDER_SHALLOW_V2 as BOUNDED_ACTION_RERENDER_SHALLOW_V2,
    ACTION_REROUTE_LOW_INFORMATION as BOUNDED_ACTION_REROUTE_LOW_INFORMATION,
    BoundedRepairRerouteDecision,
    decide_bounded_repair_reroute,
)
from emlis_ai_display_gate import decide_emlis_observation_display
from emlis_ai_low_information_observation_composer import (
    LowInformationObservationDraft,
    compose_low_information_observation,
)
from emlis_ai_observation_eligibility_service import route_observation_eligibility
from emlis_ai_observation_reply_contract import (
    OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION,
    OBSERVATION_REPLY_KIND_LOW_INFORMATION,
    OBSERVATION_ROLE_LOW_INFO_KNOWN_SCOPE,
    OBSERVATION_ROLE_LOW_INFO_QUESTION,
    OBSERVATION_ROLE_LOW_INFO_RECEIVE,
    UNKNOWN_SLOT_EVENT,
    USER_FACT_GROUNDING_MODE_DISABLED,
    build_observation_reply_meta,
)
from emlis_ai_observation_surface_realizer_tone import (
    ObservationSurfaceRealization,
    realize_low_information_observation_surface,
)
from emlis_ai_runtime_surface_pre_return_gate import build_runtime_surface_pre_return_gate_report
from emlis_ai_types import (
    ConversationComposerCandidate,
    DisplayDecision,
    GroundingReport,
    GroundingSentenceClaim,
    ListenerReaderReport,
    SafetyBoundaryReport,
    TemplateEchoReport,
)

OBSERVATION_DISPLAY_REPAIR_INTEGRATION_VERSION: Final = "emlis.observation_display_repair_integration.v1"
OBSERVATION_DISPLAY_REPAIR_INTEGRATION_STEP: Final = "Step10_Display_Repair_Integration"
OBSERVATION_DISPLAY_REPAIR_GENERATION_METHOD: Final = "observation_reply_step10_low_information_branch"
OBSERVATION_DISPLAY_REPAIR_COMPOSER_MODEL: Final = "emlis.low_information_observation_display_branch.v1"

_SENTENCE_SPLIT_RE: Final = re.compile(r"[。！？!?]+")
_QUESTION_RE: Final = re.compile(
    r"(詳しく残せそうなら、(?:何があったか|どのあたりが重くなっているか|何が変わったのか|どこから言いにくくなっているか|何について大丈夫か気になっているのか)残してみませんか|残してみませんか|何がありましたか|何が起きたか|どの部分が重くなっていますか|何が変わりましたか|どこから言いにくくなっていますか|何を言いにくく感じていますか|どうしましたか|何について大丈夫か気になっていますか)"
)
_LEGACY_LOW_INFORMATION_PROMPT_RE: Final = re.compile(r"(よければ、|何がありましたか[。！？!?]?)")
_HUMILITY_RE: Final = re.compile(r"(ように見えます|かもしれません|まだ見えていません|まだ決められません|なさそうです)")
_UNSUPPORTED_ASSERTION_RE: Final = re.compile(
    r"(前と同じことで疲れている|環境の件で疲れている|あなたはいつも|しやすい人|診断|治療|症状|トラウマ|障害|ADHD|うつ|鬱|PTSD)"
)
_FORBIDDEN_FIXED_TEXT_RE: Final = re.compile(
    r"(Emlisでは観測できません|もっと詳しく教えてください|つらかったですね[。\s]*無理しないでくださいね|無理しないでくださいね|あなたは十分頑張っています|よければ、何がありましたか|何がありましたか)"
)


_LOW_INFORMATION_REROUTE_REASONS: Final = frozenset(
    {
        "too_short_for_observation",
        "missing_information",
        "relation_confidence_low",
        "insufficient_relation_confidence",
        "candidate_overclaim",
        "overclaim_candidate",
        "overclaim",
    }
)
_SAFETY_REASON_MARKERS: Final = frozenset(
    {
        "safety_boundary",
        "safety_blocked",
        "self_harm",
        "suicide",
        "harm",
        "violence",
    }
)
_NON_REPAIRABLE_AI_GENERATED_REJECTION_REASONS: Final = frozenset(
    {
        "unsupported_sentence",
        "graph_evidence_not_used",
        "core_relation_not_reflected",
        "phase8_body_too_short",
    }
)


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").replace("\u3000", " ")).strip()


def _dedupe(values: Iterable[Any] | Any | None) -> list[str]:
    if values is None:
        return []
    if isinstance(values, (str, bytes, bytearray)):
        iterable: Iterable[Any] = [values]
    elif isinstance(values, Iterable):
        iterable = values
    else:
        iterable = [values]
    out: list[str] = []
    for value in iterable:
        item = _clean(value)
        if item and item not in out:
            out.append(item)
    return out




def _composer_resolution_block_reasons(composer_client_resolution: Any) -> list[str]:
    """Return infrastructure / rollout / AP0 blockers that Step 10 must not override."""

    meta = _meta(composer_client_resolution)
    if not meta:
        return []
    reasons: list[str] = []
    if bool(
        meta.get("complete_initial_client_requested")
        or meta.get("complete_composer_client_requested")
        or meta.get("complete_composer_initial_requested")
        or meta.get("complete_initial_requested")
    ):
        reasons.append("complete_initial_diagnostic_path")
    rejection_reasons = _dedupe(meta.get("rejection_reasons"))
    connection_status = _clean(meta.get("connection_status"))
    stop_stage = _clean(meta.get("pre_connection_stop_stage"))
    reason_group = _clean(meta.get("composer_client_not_connected_reason_group"))
    rollout_reasons = {
        "limited_composer_rollout_not_allowed",
        "complete_initial_rollout_not_allowed",
    }
    release_gate_rollout_reason_codes = {"rollout_stage_off", "rollout_stage_not_matched"}
    scope_blocked = bool(
        connection_status == "blocked_scope"
        or stop_stage == "scope"
        or any(str(reason).startswith("scope_") for reason in rejection_reasons)
        or "limited_composer_scope_not_allowed" in rejection_reasons
    )
    if connection_status == "blocked_ap0" or stop_stage == "ap0":
        reasons.append("composer_resolution_blocked_ap0")
    if connection_status == "blocked_rollout":
        reasons.append("composer_resolution_blocked_rollout")
    if stop_stage == "rollout":
        reasons.append("composer_resolution_pre_connection_rollout_stop")
    if "complete_initial_ap0_not_green" in rejection_reasons:
        reasons.append("complete_initial_ap0_not_green")
    if "complete_initial_rollout_not_allowed" in rejection_reasons:
        reasons.append("complete_initial_rollout_not_allowed")
    if not scope_blocked and "limited_composer_rollout_not_allowed" in rejection_reasons:
        reasons.append("limited_composer_rollout_not_allowed")
    if reason_group in {"ap0", "rollout"}:
        reasons.append(f"complete_initial_{reason_group}_block")
    for gate_key in ("release_gate", "phase7_rollout_gate"):
        gate = meta.get(gate_key)
        if not isinstance(gate, Mapping):
            continue
        gate_reasons = _dedupe(gate.get("rejection_reasons"))
        gate_reason_code = _clean(gate.get("reason_code"))
        gate_scope_blocked = bool(
            gate_reason_code.startswith("scope_")
            or _clean(gate.get("cohort")) == "blocked_scope"
            or any(str(reason).startswith("scope_") for reason in gate_reasons)
            or "limited_composer_scope_not_allowed" in gate_reasons
        )
        if (
            gate.get("enabled") is False
            and not gate_scope_blocked
            and (set(gate_reasons).intersection(rollout_reasons) or gate_reason_code in release_gate_rollout_reason_codes)
        ):
            reasons.append("phase7_rollout_gate_blocked")
    if bool(meta.get("blocked_by_ap0")):
        reasons.append("complete_initial_blocked_by_ap0")
    if bool(meta.get("blocked_by_rollout")):
        reasons.append("complete_initial_blocked_by_rollout")
    return _dedupe(reasons)


def _composer_resolution_feature_flag_block_reasons(composer_client_resolution: Any) -> list[str]:
    """Return feature-flag pre-connection stops.

    These are not hard blockers for a genuine low-information input, but they
    must not be used to reroute an otherwise eligible candidate into the
    low-information repair branch.
    """

    meta = _meta(composer_client_resolution)
    if not meta:
        return []
    reasons: list[str] = []
    rejection_reasons = _dedupe(meta.get("rejection_reasons"))
    connection_status = _clean(meta.get("connection_status"))
    stop_stage = _clean(meta.get("pre_connection_stop_stage"))
    if connection_status == "blocked_feature_flag" or stop_stage == "flag":
        reasons.append("composer_resolution_blocked_feature_flag")
    if "default_limited_composer_feature_disabled" in rejection_reasons:
        reasons.append("default_limited_composer_feature_disabled")
    return _dedupe(reasons)


def _display_repair_route_allowed(
    *,
    original_display_decision: DisplayDecision,
    original_composer_source: str = "",
    original_composer_candidate: Any = None,
) -> tuple[bool, tuple[str, ...]]:
    """Decide whether Step 10 may move a failed path to low-information.

    Unavailable ordinary paths may enter low-information. AI-generated eligible
    candidates may enter only for missing-information style failures named in
    the design. This keeps older fail-closed candidate quality tests intact.
    """

    status = _clean(getattr(original_display_decision, "observation_status", ""))
    source = _clean(original_composer_source)
    reasons = _dedupe(getattr(original_display_decision, "rejection_reasons", []) or [])
    candidate_available = bool(original_composer_candidate is not None and source == "ai_generated")
    if status == "unavailable" and source in {"", "unavailable", "empty"}:
        return True, ("ordinary_unavailable_low_information_route",)
    allowed_markers = {"too_short_for_observation", "missing_information", "relation_confidence_low"}
    if status == "rejected" and any(reason in allowed_markers or "overclaim" in reason for reason in reasons):
        if candidate_available:
            non_repairable_candidate_reasons = [
                reason
                for reason in reasons
                if reason in _NON_REPAIRABLE_AI_GENERATED_REJECTION_REASONS
            ]
            if non_repairable_candidate_reasons:
                return False, tuple(
                    [
                        "ai_generated_candidate_non_repairable_rejection",
                        *non_repairable_candidate_reasons,
                    ]
                )
            return True, ("eligible_candidate_missing_information_repair",)
        if source in {"", "unavailable", "empty"}:
            return True, ("ordinary_rejected_low_information_route",)
    return False, tuple(["display_repair_route_not_allowed", *reasons])

def _meta(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    as_meta = getattr(value, "as_meta", None)
    if callable(as_meta):
        payload = as_meta()
        return dict(payload) if isinstance(payload, Mapping) else {}
    return {}


def _has_safety_reason(reasons: Iterable[Any] | Any | None) -> bool:
    for reason in _dedupe(reasons):
        lowered = reason.lower()
        if any(marker in lowered for marker in _SAFETY_REASON_MARKERS):
            return True
    return False




def _complete_initial_diagnostic_path_requested(composer_client_resolution: Any = None) -> bool:
    """Return True for legacy complete-initial diagnostic runs that must stay fail-closed.

    Step 10 is the observation-reply branch.  The complete-initial AP0/rollout
    diagnostic route has its own fail-closed contract, so this repair branch must
    not turn those pre-connection diagnostics into displayed observations.
    """

    resolution = _meta(composer_client_resolution)
    return bool(
        resolution.get("complete_initial_client_requested")
        or resolution.get("complete_composer_client_requested")
        or resolution.get("complete_composer_initial_requested")
        or resolution.get("complete_initial_requested")
    )

def should_reroute_to_low_information(
    *,
    eligibility_decision: Any = None,
    display_decision: DisplayDecision | None = None,
    safety_report: SafetyBoundaryReport | None = None,
) -> bool:
    """Return whether Step 10 may move a failed candidate to low-info branch."""

    if safety_report is not None and bool(getattr(safety_report, "requires_block", False)):
        return False
    reasons = _dedupe(getattr(display_decision, "rejection_reasons", []) if display_decision is not None else [])
    if _has_safety_reason(reasons):
        return False
    eligibility = _meta(eligibility_decision)
    kind = _clean(eligibility.get("observation_reply_kind"))
    status = _clean(eligibility.get("eligibility_status") or eligibility.get("status"))
    if kind == OBSERVATION_REPLY_KIND_LOW_INFORMATION or status == OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION:
        return True
    return bool(set(reasons).intersection(_LOW_INFORMATION_REROUTE_REASONS))


def _repair_low_information_eligibility_meta(
    eligibility_meta: Mapping[str, Any],
    *,
    repair_reasons: Iterable[Any] | None = None,
) -> dict[str, Any]:
    """Build a low-information routing meta for repairable eligible failures."""

    base = dict(eligibility_meta or {})
    reasons = _dedupe(repair_reasons) or ["step10_display_repair"]
    unknown_slots = _dedupe(base.get("unknown_slots")) or [UNKNOWN_SLOT_EVENT]
    plan = "subscription" if _clean(base.get("plan")) == "subscription" else "free"
    facts_used = base.get("facts_used") if plan == "subscription" and isinstance(base.get("facts_used"), list) else []
    user_fact_mode = _clean(base.get("user_fact_grounding_mode") or base.get("mode")) or USER_FACT_GROUNDING_MODE_DISABLED
    if plan != "subscription":
        user_fact_mode = USER_FACT_GROUNDING_MODE_DISABLED
        facts_used = []
    observation_reply_meta = build_observation_reply_meta(
        observation_reply_kind=OBSERVATION_REPLY_KIND_LOW_INFORMATION,
        eligibility_status=OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION,
        plan=plan,
        eligible_for_full_observation=False,
        question_required=True,
        user_fact_grounding_mode=user_fact_mode,
        user_fact_allowed=bool(plan == "subscription" and facts_used),
        user_fact_may_hint=bool(plan == "subscription" and facts_used),
        facts_used=facts_used,
        unknown_slots=unknown_slots,
        inference_depths=[1],
        primary_reason="step10_repair_rerouted_to_low_information",
    )
    ambiguity = _dedupe(base.get("ambiguity_reasons"))
    for reason in ["step10_repair_reroute", *reasons]:
        if reason not in ambiguity:
            ambiguity.append(reason)
    base.update(
        {
            "version": OBSERVATION_DISPLAY_REPAIR_INTEGRATION_VERSION,
            "schema_version": OBSERVATION_DISPLAY_REPAIR_INTEGRATION_VERSION,
            "source_step": OBSERVATION_DISPLAY_REPAIR_INTEGRATION_STEP,
            "step": OBSERVATION_DISPLAY_REPAIR_INTEGRATION_STEP,
            "status": OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION,
            "observation_reply_kind": OBSERVATION_REPLY_KIND_LOW_INFORMATION,
            "eligibility_status": OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION,
            "eligible_for_full_observation": False,
            "question_required": True,
            "primary_reason": "step10_repair_rerouted_to_low_information",
            "ambiguity_reasons": ambiguity,
            "unknown_slots": unknown_slots,
            "plan": plan,
            "user_fact_grounding_mode": user_fact_mode,
            "user_fact_allowed": bool(plan == "subscription" and facts_used),
            "user_fact_read_enabled": bool(plan == "subscription" and facts_used),
            "user_fact_may_hint": bool(plan == "subscription" and facts_used),
            "user_fact_may_promote_to_eligible": False,
            "must_not_promote_low_info_to_eligible": True,
            "must_not_assert_current_event_from_user_fact": True,
            "facts_used": facts_used,
            "observation_reply_meta": observation_reply_meta,
            "low_information_repair_from_eligible": True,
            "repair_reasons": reasons,
            "display_gate_relaxed": False,
            "public_status_extended": False,
            "api_route_changed": False,
            "db_physical_name_changed": False,
            "rn_visible_contract_changed": False,
            "raw_input_included": False,
            "raw_text_included": False,
            "comment_text_generated": False,
        }
    )
    return base


def _body_sentences(body: Any) -> list[str]:
    return [part for part in (_clean(part) for part in _SENTENCE_SPLIT_RE.split(_clean(body))) if part]


def _line_metas(surface: ObservationSurfaceRealization) -> list[dict[str, Any]]:
    meta = surface.as_meta()
    lines = meta.get("line_metas")
    return [dict(line) for line in lines if isinstance(line, Mapping)] if isinstance(lines, Sequence) else []


def _evidence_ids_from_surface(surface: ObservationSurfaceRealization) -> list[str]:
    ids: list[str] = []
    for line in _line_metas(surface):
        for value in line.get("supporting_evidence_ids") or []:
            item = _clean(value)
            if item and item not in ids:
                ids.append(item)
    return ids


def _binding_meta_for_surface(surface: ObservationSurfaceRealization) -> dict[str, Any]:
    lines = _line_metas(surface)
    count = max(1, len(lines))
    return {
        "version": "emlis.observation_display_repair_binding.v1",
        "binding_version": "emlis.observation_display_repair_binding.v1",
        "binding_contract_version": "emlis.gate_binding_contract.v2",
        "gate_binding_contract_version": "emlis.gate_binding_contract.v2",
        "binding_required": True,
        "binding_present": True,
        "binding_used": True,
        "binding_missing": False,
        "binding_count": count,
        "expected_binding_count": count,
        "sentence_count": count,
        "binding_support_source": "low_information_observation_roles",
    }


def _sentence_bindings_for_surface(surface: ObservationSurfaceRealization) -> list[dict[str, Any]]:
    bindings: list[dict[str, Any]] = []
    for index, line in enumerate(_line_metas(surface), start=1):
        roles = _dedupe(line.get("observation_roles"))
        bindings.append(
            {
                "sentence_id": f"low_info_s{index}",
                "line_id": _clean(line.get("line_id")) or f"low_info_line_{index}",
                "line_role": _clean(line.get("line_role")) or "core",
                "observation_roles": roles,
                "relation_type": _clean(line.get("relation_type")) or "low_information_known_scope",
                "used_evidence_span_ids": _dedupe(line.get("supporting_evidence_ids")),
                "used_phrase_unit_ids": _dedupe(line.get("material_entry_ids")),
                "must_include": True,
                "raw_input_included": False,
            }
        )
    return bindings


def _low_information_quality_reasons(surface: ObservationSurfaceRealization) -> list[str]:
    meta = surface.as_meta()
    body = _clean(surface.body)
    roles = set(_dedupe(meta.get("sentence_plan_observation_roles")))
    reasons: list[str] = []
    if not body:
        reasons.append("empty_low_information_body")
    sentence_count = len(_body_sentences(body))
    if sentence_count < 2 or sentence_count > 3:
        reasons.append("low_information_body_sentence_count_out_of_range")
    required_roles = {
        OBSERVATION_ROLE_LOW_INFO_RECEIVE,
        OBSERVATION_ROLE_LOW_INFO_KNOWN_SCOPE,
        OBSERVATION_ROLE_LOW_INFO_QUESTION,
    }
    missing = sorted(required_roles.difference(roles))
    reasons.extend(f"missing_role:{role}" for role in missing)
    if not meta.get("unknown_slots"):
        reasons.append("unknown_slots_missing")
    if _LEGACY_LOW_INFORMATION_PROMPT_RE.search(body):
        reasons.append("legacy_low_information_question_wording")
    if not _QUESTION_RE.search(body):
        reasons.append("low_information_question_missing")
    if not _HUMILITY_RE.search(body):
        reasons.append("humility_marker_missing")
    if _UNSUPPORTED_ASSERTION_RE.search(body):
        reasons.append("unsupported_current_event_or_personality_assertion")
    if _FORBIDDEN_FIXED_TEXT_RE.search(body):
        reasons.append("fixed_fallback_or_forbidden_template_text")
    if meta.get("tone_guard_passed") is False:
        reasons.append("observation_surface_tone_guard_failed")
    if meta.get("template_guard_passed") is False:
        reasons.append("observation_surface_template_guard_failed")
    return _dedupe(reasons)


def _reader_report_for_low_information(surface: ObservationSurfaceRealization) -> ListenerReaderReport:
    reasons = _low_information_quality_reasons(surface)
    passed = not reasons
    roles = surface.observation_roles
    return ListenerReaderReport(
        understandable=passed,
        addressee_clear=passed,
        speaker_integrity_ok=True,
        conversational=passed,
        report_like=False,
        summary_of_output="low_information_observation_with_known_scope_and_question" if passed else "low_information_observation_rejected",
        unclear_sentences=[] if passed else reasons,
        rejection_reasons=[] if passed else reasons,
        confidence=0.91 if passed else 0.28,
        relation_surface_contract_version="emlis.observation_display_repair.low_information_reader.v1",
        reader_relation_signal_detected=True,
        reader_relation_signal_count=len(roles),
        reader_relation_signal_keys=list(roles),
        reader_relation_signal_relation_types=["low_information_known_scope"],
        expected_relation_types=["low_information_known_scope"],
        reader_relation_signal_meta={
            "version": "emlis.observation_display_repair.low_information_reader.v1",
            "observation_reply_kind": OBSERVATION_REPLY_KIND_LOW_INFORMATION,
            "low_information_roles_present": bool(roles),
            "raw_input_included": False,
        },
        raw_input_included=False,
    )


def _grounding_report_for_low_information(surface: ObservationSurfaceRealization) -> GroundingReport:
    reasons = _low_information_quality_reasons(surface)
    passed = not reasons
    evidence_ids = _evidence_ids_from_surface(surface)
    sentence_count = max(1, len(_body_sentences(surface.body)))
    claims: list[GroundingSentenceClaim] = []
    bindings = _sentence_bindings_for_surface(surface)
    for index, sentence in enumerate(_body_sentences(surface.body)):
        binding = bindings[index] if index < len(bindings) else {}
        relation_type = _clean(binding.get("relation_type")) or "low_information_known_scope"
        claim_evidence_ids = _dedupe(binding.get("used_evidence_span_ids") or evidence_ids[:1])
        claims.append(
            GroundingSentenceClaim(
                sentence_index=index,
                sentence="",
                evidence_span_ids=claim_evidence_ids,
                relation_supported=passed,
                unsupported_reason="" if passed else "low_information_quality_guard_failed",
                binding_used=True,
                binding_sentence_id=_clean(binding.get("sentence_id")) or f"low_info_s{index + 1}",
                binding_evidence_span_ids=claim_evidence_ids,
                binding_phrase_unit_ids=_dedupe(binding.get("used_phrase_unit_ids")),
                binding_relation_type=relation_type,
                declared_evidence_span_ids=claim_evidence_ids,
                declared_phrase_unit_ids=_dedupe(binding.get("used_phrase_unit_ids")),
                declared_relation_type=relation_type,
                grounding_support_source="low_information_observation_roles",
                binding_support_reason="known_scope_observation_and_unknown_slot_question" if passed else "quality_guard_failed",
                used_phrase_unit_ids=_dedupe(binding.get("used_phrase_unit_ids")),
                relation_type=relation_type,
            )
        )
    binding_meta = _binding_meta_for_surface(surface)
    return GroundingReport(
        passed=passed,
        sentence_claims=claims,
        rejection_reasons=[] if passed else reasons,
        coverage_ratio=1.0 if passed else 0.0,
        confidence=0.91 if passed else 0.24,
        grounding_scope="low_information_known_scope",
        allowed_evidence_span_ids=evidence_ids,
        ignored_evidence_span_ids=[],
        binding_used=True,
        binding_present=True,
        binding_missing=False,
        binding_count=sentence_count,
        expected_binding_count=sentence_count,
        binding_version="emlis.observation_display_repair_binding.v1",
        relation_types=["low_information_known_scope", "low_information_question"],
        binding_supported_sentence_count=sentence_count if passed else 0,
        binding_diagnostics={
            **binding_meta,
            "observation_reply_kind": OBSERVATION_REPLY_KIND_LOW_INFORMATION,
            "low_information_known_scope_only": True,
            "display_gate_relaxed": False,
            "raw_input_included": False,
        },
        binding_aware_grounding={
            **binding_meta,
            "observation_reply_kind": OBSERVATION_REPLY_KIND_LOW_INFORMATION,
            "binding_aware_grounding": True,
            "complete_binding_aware_grounding": True,
            "display_gate_relaxed": False,
            "raw_input_included": False,
        },
        binding_rejection_reasons=[] if passed else reasons,
        declared_relation_types=["low_information_known_scope", "low_information_question"],
        declared_phrase_unit_ids=_dedupe(
            phrase_id
            for binding in bindings
            for phrase_id in (binding.get("used_phrase_unit_ids") or [])
        ),
        grounding_report_contract_version="emlis.observation_display_repair.low_information_grounding.v1",
        gate_binding_contract_version="emlis.gate_binding_contract.v2",
        binding_contract_version="emlis.gate_binding_contract.v2",
        binding_support_source="low_information_observation_roles",
        binding_pass_rate=1.0 if passed else 0.0,
        unsupported_sentence_ids=[] if passed else [f"low_info_s{i + 1}" for i in range(sentence_count)],
        relation_not_expressed_sentence_ids=[],
        phrase_unit_missing_sentence_ids=[],
        weak_material_sentence_ids=[],
        raw_echo_sentence_ids=[],
        overclaim_sentence_ids=[],
        release_blocker=not passed,
        grounding_report_v2={
            **binding_meta,
            "version": "emlis.observation_display_repair.low_information_grounding.v1",
            "observation_reply_kind": OBSERVATION_REPLY_KIND_LOW_INFORMATION,
            "binding_pass_rate": 1.0 if passed else 0.0,
            "fail_reasons": [] if passed else reasons,
            "display_gate_relaxed": False,
            "raw_input_included": False,
        },
    )


def _template_report_for_low_information(surface: ObservationSurfaceRealization) -> TemplateEchoReport:
    reasons = _low_information_quality_reasons(surface)
    passed = not reasons
    surface_meta = surface.as_meta()
    template_meta = surface_meta.get("template_guard_report") if isinstance(surface_meta.get("template_guard_report"), Mapping) else {}
    return TemplateEchoReport(
        passed=passed,
        max_old_template_similarity=0.0,
        max_previous_output_similarity=0.0,
        raw_echo_ratio=0.0,
        repeated_sentence_pattern_score=float(template_meta.get("surface_skeleton_repeat_count") or 0.0),
        max_sentence_echo_ratio=0.0,
        raw_quote_span_count=0,
        raw_copy_sentence_ratio=0.0,
        limited_surface_repetition_score=0.0,
        abstract_repetition_score=0.0,
        abstract_phrase_repetition_score=0.0,
        surface_signature_row_count=len(surface.lines),
        surface_signature_repeat_count=int(template_meta.get("surface_skeleton_repeat_count") or 0),
        same_ending_major_count=0,
        surface_connector_repetition_count=0,
        repeated_surface_signature_keys=list(template_meta.get("repeated_surface_signature_keys") or []),
        repeated_surface_ending_keys=[],
        repeated_surface_connector_keys=[],
        raw_quote_char_ratio=0.0,
        matched_raw_quote_fragments=[],
        repeated_limited_surface_score=0.0,
        matched_limited_surface_patterns=[],
        phase8_emotion_label_body_line_count=0,
        phase8_missing_must_keep_roles=[],
        phase8_quality_rejection_reasons=[] if passed else reasons,
        matched_banned_patterns=[],
        rejection_reasons=[] if passed else reasons,
    )


def _candidate_for_low_information(
    *,
    trace_id: str,
    surface: ObservationSurfaceRealization,
    draft: LowInformationObservationDraft,
    eligibility_meta: Mapping[str, Any],
) -> ConversationComposerCandidate:
    surface_meta = surface.as_meta()
    draft_meta = draft.as_meta()
    used_evidence_ids = _evidence_ids_from_surface(surface)
    bindings = _sentence_bindings_for_surface(surface)
    binding_meta = _binding_meta_for_surface(surface)
    composer_meta = {
        "version": OBSERVATION_DISPLAY_REPAIR_INTEGRATION_VERSION,
        "source_step": OBSERVATION_DISPLAY_REPAIR_INTEGRATION_STEP,
        "observation_reply_kind": OBSERVATION_REPLY_KIND_LOW_INFORMATION,
        "eligibility_status": OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION,
        "eligible_for_full_observation": False,
        "question_required": True,
        "observation_reply_meta": dict(draft_meta.get("observation_reply_meta") or {}),
        "observation_eligibility_decision": dict(eligibility_meta),
        "low_information_observation_composer": {k: v for k, v in draft_meta.items() if k not in {"line_metas"}},
        "observation_surface_realizer_tone": {k: v for k, v in surface_meta.items() if k not in {"line_metas"}},
        "sentence_bindings": bindings,
        "sentence_binding_bundle": {
            **binding_meta,
            "bindings": bindings,
            "relation_types": ["low_information_known_scope", "low_information_question"],
            "coverage_scope": "low_information_known_scope",
            "raw_input_included": False,
        },
        "display_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "fixed_fallback_used": False,
        "legacy_safe_fallback_used": False,
        "legacy_input_feedback_template_used": False,
        "external_ai_used": False,
        "local_llm_used": False,
        "raw_input_included": False,
    }
    return ConversationComposerCandidate(
        comment_text=surface.body,
        composer_source="ai_generated",
        status="generated",
        ai_generated=True,
        trace_id=trace_id,
        attempt_count=1,
        used_evidence_span_ids=used_evidence_ids,
        confidence=0.91,
        rejection_reasons=[],
        response_schema_version="emlis.observation_display_repair.response.v1",
        fixed_string_renderer_used=False,
        composer_model=OBSERVATION_DISPLAY_REPAIR_COMPOSER_MODEL,
        generation_method=OBSERVATION_DISPLAY_REPAIR_GENERATION_METHOD,
        coverage_scope="low_information_known_scope",
        generation_scope="low_information_observation",
        composer_meta=composer_meta,
        used_claim_ids=[],
        used_relation_ids=["low_information_known_scope", "low_information_question"],
    )


@dataclass(frozen=True)
class ObservationDisplayRepairIntegrationResult:
    applied: bool
    display_decision: DisplayDecision
    reader_report: Any
    grounding_report: Any
    template_echo_report: Any
    composer_source: str
    composer_candidate: Any = None
    eligibility_decision: Any = None
    low_information_draft: LowInformationObservationDraft | None = None
    surface_realization: ObservationSurfaceRealization | None = None
    original_observation_status: str = ""
    repair_reasons: Sequence[str] = field(default_factory=tuple)
    blocked_reasons: Sequence[str] = field(default_factory=tuple)
    bounded_repair_reroute_decision: BoundedRepairRerouteDecision | None = None

    def as_meta(self) -> dict[str, Any]:
        eligibility_meta = _meta(self.eligibility_decision)
        draft_meta = self.low_information_draft.as_meta() if self.low_information_draft is not None else {}
        surface_meta = self.surface_realization.as_meta() if self.surface_realization is not None else {}
        observation_reply_meta = dict(
            draft_meta.get("observation_reply_meta")
            or surface_meta.get("observation_reply_meta")
            or eligibility_meta.get("observation_reply_meta")
            or {}
        )
        if not observation_reply_meta and eligibility_meta:
            observation_reply_meta = {
                "observation_reply_kind": eligibility_meta.get("observation_reply_kind"),
                "eligibility_status": eligibility_meta.get("eligibility_status"),
                "eligible_for_full_observation": eligibility_meta.get("eligible_for_full_observation"),
                "question_required": eligibility_meta.get("question_required"),
                "user_fact_may_promote_to_eligible": False,
            }
        status = str(getattr(self.display_decision, "observation_status", "") or "")
        bounded_meta = (
            self.bounded_repair_reroute_decision.as_meta()
            if self.bounded_repair_reroute_decision is not None
            else {
                "version": "emlis.bounded_repair_reroute.v1",
                "source_step": "Step7_Bounded_Repair_Reroute",
                "step7_bounded_repair_reroute_ready": True,
                "evaluated": False,
                "allowed": False,
                "action": BOUNDED_ACTION_NO_REPAIR,
                "runtime_surface_gate_evaluated": False,
                "runtime_surface_gate_passed": False,
                "runtime_surface_gate_action": "",
                "rejection_reasons": [],
                "repair_reasons": [],
                "blocked_reasons": [],
                "raw_input_included": False,
                "comment_text_body_included": False,
                "display_gate_relaxed": False,
            }
        )
        return {
            "version": OBSERVATION_DISPLAY_REPAIR_INTEGRATION_VERSION,
            "schema_version": OBSERVATION_DISPLAY_REPAIR_INTEGRATION_VERSION,
            "source_step": OBSERVATION_DISPLAY_REPAIR_INTEGRATION_STEP,
            "step": OBSERVATION_DISPLAY_REPAIR_INTEGRATION_STEP,
            "display_repair_integration_ready": True,
            "step10_display_repair_integration_ready": True,
            "step7_bounded_repair_reroute": bounded_meta,
            "bounded_repair_reroute": bounded_meta,
            "step7_bounded_repair_reroute_ready": True,
            "bounded_repair_reroute_action": bounded_meta.get("action"),
            "bounded_repair_reroute_allowed": bool(bounded_meta.get("allowed")),
            "applied": bool(self.applied),
            "low_information_repair_applied": bool(self.applied),
            "rerouted_from_eligible": bool("eligible_branch_repaired_to_low_information" in self.repair_reasons),
            "original_observation_status": self.original_observation_status,
            "final_observation_status": status,
            "observation_status": status,
            "comment_text_present": bool(str(getattr(self.display_decision, "comment_text", "") or "").strip()),
            "comment_text_allowed": bool(status == "passed" and str(getattr(self.display_decision, "comment_text", "") or "").strip()),
            "public_observation_status": "passed" if self.applied else status,
            "public_status_extended": False,
            "observation_status_enum_extended": False,
            "api_route_changed": False,
            "db_physical_name_changed": False,
            "rn_visible_contract_changed": False,
            "rn_visible_title_changed": False,
            "response_shape_changed": False,
            "display_gate_relaxed": False,
            "reader_gate_relaxed": False,
            "grounding_gate_relaxed": False,
            "template_gate_relaxed": False,
            "gate_relaxed": False,
            "fixed_fallback_used": False,
            "legacy_safe_fallback_used": False,
            "legacy_input_feedback_template_used": False,
            "external_ai_used": False,
            "local_llm_used": False,
            "raw_input_included": False,
            "raw_text_included": False,
            "observation_reply_kind": observation_reply_meta.get("observation_reply_kind") or eligibility_meta.get("observation_reply_kind"),
            "eligibility_status": observation_reply_meta.get("eligibility_status") or eligibility_meta.get("eligibility_status"),
            "eligible_for_full_observation": bool(observation_reply_meta.get("eligible_for_full_observation") is True),
            "question_required": bool(observation_reply_meta.get("question_required") is True),
            "unknown_slots": list(observation_reply_meta.get("unknown_slots") or eligibility_meta.get("unknown_slots") or surface_meta.get("unknown_slots") or []),
            "user_fact_may_promote_to_eligible": False,
            "must_not_promote_low_info_to_eligible": True,
            "must_not_assert_current_event_from_user_fact": True,
            "observation_reply_meta": observation_reply_meta,
            "low_information_observation_composer_meta": {k: v for k, v in draft_meta.items() if k not in {"line_metas"}},
            "observation_surface_realizer_tone_meta": {k: v for k, v in surface_meta.items() if k not in {"line_metas"}},
            "repair_reasons": list(self.repair_reasons),
            "blocked_reasons": list(self.blocked_reasons),
        }


def integrate_observation_display_repair(
    *,
    current_input: Any,
    subscription_tier: Any = None,
    capability: Any = None,
    source_bundle: Any = None,
    evidence_ledger: Any = None,
    observation_graph: Any = None,
    composer_client_resolution: Any = None,
    safety_report: SafetyBoundaryReport | None = None,
    trace_id: str = "",
    original_display_decision: DisplayDecision,
    original_reader_report: Any,
    original_grounding_report: Any,
    original_template_echo_report: Any,
    original_composer_source: str = "",
    original_composer_candidate: Any = None,
    repair_allowed: bool = True,
    repair_block_reason: str = "",
    runtime_surface_pre_return_gate_report: Mapping[str, Any] | None = None,
) -> ObservationDisplayRepairIntegrationResult:
    """Apply the Step 10 low-information display repair, when appropriate."""

    original_status = str(getattr(original_display_decision, "observation_status", "") or "")
    if not repair_allowed:
        runtime_block_reason = _clean(repair_block_reason) or "repair_disabled_by_runtime_contract"
        runtime_block_reasons = _dedupe(
            [
                runtime_block_reason,
                *_composer_resolution_block_reasons(composer_client_resolution),
            ]
        )
        return ObservationDisplayRepairIntegrationResult(
            applied=False,
            display_decision=original_display_decision,
            reader_report=original_reader_report,
            grounding_report=original_grounding_report,
            template_echo_report=original_template_echo_report,
            composer_source=original_composer_source,
            composer_candidate=original_composer_candidate,
            original_observation_status=original_status,
            blocked_reasons=tuple(runtime_block_reasons),
        )

    if original_status == "passed":
        return ObservationDisplayRepairIntegrationResult(
            applied=False,
            display_decision=original_display_decision,
            reader_report=original_reader_report,
            grounding_report=original_grounding_report,
            template_echo_report=original_template_echo_report,
            composer_source=original_composer_source,
            composer_candidate=original_composer_candidate,
            original_observation_status=original_status,
            blocked_reasons=("already_passed",),
        )
    if original_status == "safety_blocked" or bool(getattr(safety_report, "requires_block", False)):
        return ObservationDisplayRepairIntegrationResult(
            applied=False,
            display_decision=original_display_decision,
            reader_report=original_reader_report,
            grounding_report=original_grounding_report,
            template_echo_report=original_template_echo_report,
            composer_source=original_composer_source,
            composer_candidate=original_composer_candidate,
            original_observation_status=original_status,
            blocked_reasons=("safety_boundary",),
        )

    resolution_meta = _meta(composer_client_resolution)
    complete_initial_requested = bool(
        resolution_meta.get("complete_initial_client_requested")
        or resolution_meta.get("complete_composer_client_requested")
        or resolution_meta.get("complete_initial_requested")
        or resolution_meta.get("complete_initial_composer_requested")
    )
    pre_connection_stop = bool(
        resolution_meta.get("blocked_before_composer")
        or resolution_meta.get("pre_connection_stop")
        or _clean(resolution_meta.get("pre_connection_stop_stage")) in {"ap0", "flag", "rollout"}
    )
    if complete_initial_requested and pre_connection_stop:
        return ObservationDisplayRepairIntegrationResult(
            applied=False,
            display_decision=original_display_decision,
            reader_report=original_reader_report,
            grounding_report=original_grounding_report,
            template_echo_report=original_template_echo_report,
            composer_source=original_composer_source,
            composer_candidate=original_composer_candidate,
            original_observation_status=original_status,
            blocked_reasons=("composer_resolution_pre_connection_stop",),
        )

    resolution_blockers = _composer_resolution_block_reasons(composer_client_resolution)
    if resolution_blockers:
        return ObservationDisplayRepairIntegrationResult(
            applied=False,
            display_decision=original_display_decision,
            reader_report=original_reader_report,
            grounding_report=original_grounding_report,
            template_echo_report=original_template_echo_report,
            composer_source=original_composer_source,
            composer_candidate=original_composer_candidate,
            original_observation_status=original_status,
            blocked_reasons=tuple(resolution_blockers),
        )

    bounded_reroute_decision = decide_bounded_repair_reroute(
        display_decision=original_display_decision,
        composer_source=original_composer_source,
        safety_report=safety_report,
        runtime_surface_pre_return_gate_report=runtime_surface_pre_return_gate_report,
        repair_allowed=True,
    )
    bounded_action = str(bounded_reroute_decision.action or "")
    if bounded_reroute_decision.runtime_surface_gate_evaluated and bounded_action == BOUNDED_ACTION_RERENDER_SHALLOW_V2:
        return ObservationDisplayRepairIntegrationResult(
            applied=False,
            display_decision=original_display_decision,
            reader_report=original_reader_report,
            grounding_report=original_grounding_report,
            template_echo_report=original_template_echo_report,
            composer_source=original_composer_source,
            composer_candidate=original_composer_candidate,
            original_observation_status=original_status,
            blocked_reasons=tuple(bounded_reroute_decision.repair_reasons or ("bounded_shallow_v2_rerender_required",)),
            bounded_repair_reroute_decision=bounded_reroute_decision,
        )
    if bounded_reroute_decision.runtime_surface_gate_evaluated and bounded_action not in {BOUNDED_ACTION_NO_REPAIR, BOUNDED_ACTION_REROUTE_LOW_INFORMATION}:
        return ObservationDisplayRepairIntegrationResult(
            applied=False,
            display_decision=original_display_decision,
            reader_report=original_reader_report,
            grounding_report=original_grounding_report,
            template_echo_report=original_template_echo_report,
            composer_source=original_composer_source,
            composer_candidate=original_composer_candidate,
            original_observation_status=original_status,
            blocked_reasons=tuple(bounded_reroute_decision.blocked_reasons or ("bounded_surface_repair_not_available",)),
            bounded_repair_reroute_decision=bounded_reroute_decision,
        )

    route_allowed, route_reasons = _display_repair_route_allowed(
        original_display_decision=original_display_decision,
        original_composer_source=original_composer_source,
        original_composer_candidate=original_composer_candidate,
    )
    if bounded_action == BOUNDED_ACTION_REROUTE_LOW_INFORMATION:
        route_allowed = True
        route_reasons = tuple(bounded_reroute_decision.repair_reasons or ("bounded_low_information_reroute",))
    if not route_allowed:
        return ObservationDisplayRepairIntegrationResult(
            applied=False,
            display_decision=original_display_decision,
            reader_report=original_reader_report,
            grounding_report=original_grounding_report,
            template_echo_report=original_template_echo_report,
            composer_source=original_composer_source,
            composer_candidate=original_composer_candidate,
            original_observation_status=original_status,
            blocked_reasons=tuple(route_reasons),
            bounded_repair_reroute_decision=bounded_reroute_decision if bounded_reroute_decision.runtime_surface_gate_evaluated else None,
        )

    eligibility_decision = route_observation_eligibility(
        current_input=current_input,
        subscription_tier=subscription_tier,
        capability=capability,
        user_facts=None,
        evidence_ledger=evidence_ledger,
        observation_graph=observation_graph,
    )
    eligibility_meta = _meta(eligibility_decision)
    feature_flag_blockers = _composer_resolution_feature_flag_block_reasons(composer_client_resolution)
    if feature_flag_blockers and (
        eligibility_meta.get("observation_reply_kind") != OBSERVATION_REPLY_KIND_LOW_INFORMATION
        and eligibility_meta.get("eligibility_status") != OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION
        and eligibility_meta.get("status") != OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION
    ):
        return ObservationDisplayRepairIntegrationResult(
            applied=False,
            display_decision=original_display_decision,
            reader_report=original_reader_report,
            grounding_report=original_grounding_report,
            template_echo_report=original_template_echo_report,
            composer_source=original_composer_source,
            composer_candidate=original_composer_candidate,
            eligibility_decision=eligibility_decision,
            original_observation_status=original_status,
            blocked_reasons=tuple(feature_flag_blockers),
            bounded_repair_reroute_decision=bounded_reroute_decision if bounded_reroute_decision.runtime_surface_gate_evaluated else None,
        )
    original_rejection_reasons = _dedupe(getattr(original_display_decision, "rejection_reasons", []))
    eligibility_for_composer: Any = eligibility_decision
    if eligibility_meta.get("observation_reply_kind") != OBSERVATION_REPLY_KIND_LOW_INFORMATION:
        if not should_reroute_to_low_information(
            eligibility_decision=eligibility_decision,
            display_decision=original_display_decision,
            safety_report=safety_report,
        ):
            return ObservationDisplayRepairIntegrationResult(
                applied=False,
                display_decision=original_display_decision,
                reader_report=original_reader_report,
                grounding_report=original_grounding_report,
                template_echo_report=original_template_echo_report,
                composer_source=original_composer_source,
                composer_candidate=original_composer_candidate,
                eligibility_decision=eligibility_decision,
                original_observation_status=original_status,
                blocked_reasons=("not_low_information",),
                bounded_repair_reroute_decision=bounded_reroute_decision if bounded_reroute_decision.runtime_surface_gate_evaluated else None,
            )
        eligibility_meta = _repair_low_information_eligibility_meta(
            eligibility_meta,
            repair_reasons=original_rejection_reasons,
        )
        eligibility_for_composer = eligibility_meta

    if not _dedupe(eligibility_meta.get("detected_signal_roles")) and not list(eligibility_meta.get("known_fragments") or []):
        return ObservationDisplayRepairIntegrationResult(
            applied=False,
            display_decision=original_display_decision,
            reader_report=original_reader_report,
            grounding_report=original_grounding_report,
            template_echo_report=original_template_echo_report,
            composer_source=original_composer_source,
            composer_candidate=original_composer_candidate,
            eligibility_decision=eligibility_for_composer,
            original_observation_status=original_status,
            blocked_reasons=("no_current_input_low_information_signal",),
            bounded_repair_reroute_decision=bounded_reroute_decision if bounded_reroute_decision.runtime_surface_gate_evaluated else None,
        )

    try:
        draft = compose_low_information_observation(
            current_input=current_input,
            eligibility_decision=eligibility_for_composer,
            subscription_tier=subscription_tier,
            capability=capability,
            source_bundle=source_bundle,
            evidence_ledger=evidence_ledger,
            observation_graph=observation_graph,
        )
        surface = realize_low_information_observation_surface(draft, current_input=current_input)
    except Exception as exc:  # pragma: no cover - defensive fail-closed path
        return ObservationDisplayRepairIntegrationResult(
            applied=False,
            display_decision=original_display_decision,
            reader_report=original_reader_report,
            grounding_report=original_grounding_report,
            template_echo_report=original_template_echo_report,
            composer_source=original_composer_source,
            composer_candidate=original_composer_candidate,
            eligibility_decision=eligibility_decision,
            original_observation_status=original_status,
            blocked_reasons=(f"low_information_repair_build_failed:{exc.__class__.__name__}",),
            bounded_repair_reroute_decision=bounded_reroute_decision if bounded_reroute_decision.runtime_surface_gate_evaluated else None,
        )

    quality_reasons = _low_information_quality_reasons(surface)
    reader_report = _reader_report_for_low_information(surface)
    grounding_report = _grounding_report_for_low_information(surface)
    template_echo_report = _template_report_for_low_information(surface)
    candidate = _candidate_for_low_information(
        trace_id=trace_id,
        surface=surface,
        draft=draft,
        eligibility_meta=eligibility_meta,
    )
    runtime_surface_pre_return_gate_report = build_runtime_surface_pre_return_gate_report(
        comment_text=surface.body,
        composer_meta={
            **_meta(getattr(candidate, "composer_meta", {})),
            "composer_source": "ai_generated",
            "observation_reply_kind": OBSERVATION_REPLY_KIND_LOW_INFORMATION,
            "shallow_observation_path": False,
        },
        phrase_unit_grammar_meta=surface.as_meta(),
        rerender_allowed=False,
        rerender_attempted=True,
        rerender_attempt_limit=1,
        low_information_reroute_allowed=False,
    )
    display_decision = decide_emlis_observation_display(
        comment_text=surface.body,
        reader_report=reader_report,
        grounding_report=grounding_report,
        template_echo_report=template_echo_report,
        safety_report=safety_report,
        trace_id=trace_id,
        composer_source="ai_generated",
        phase_completion_ready=True,
        binding_meta=_binding_meta_for_surface(surface),
        observation_reply_kind=OBSERVATION_REPLY_KIND_LOW_INFORMATION,
        observation_quality_meta=surface.as_meta(),
        runtime_surface_pre_return_gate_report=runtime_surface_pre_return_gate_report,
    )
    applied = bool(display_decision.observation_status == "passed" and str(display_decision.comment_text or "").strip())
    return ObservationDisplayRepairIntegrationResult(
        applied=applied,
        display_decision=display_decision if applied else original_display_decision,
        reader_report=reader_report if applied else original_reader_report,
        grounding_report=grounding_report if applied else original_grounding_report,
        template_echo_report=template_echo_report if applied else original_template_echo_report,
        composer_source="ai_generated" if applied else original_composer_source,
        composer_candidate=candidate if applied else original_composer_candidate,
        eligibility_decision=eligibility_for_composer,
        low_information_draft=draft,
        surface_realization=surface,
        original_observation_status=original_status,
        repair_reasons=tuple(
            _dedupe(
                [
                    "low_information_regular_branch" if not eligibility_meta.get("low_information_repair_from_eligible") else "eligible_branch_repaired_to_low_information",
                    "display_gate_passed_with_branch_reports",
                    *original_rejection_reasons,
                ]
            )
        ) if applied else tuple(),
        blocked_reasons=tuple(quality_reasons if quality_reasons else getattr(display_decision, "rejection_reasons", []) or []),
        bounded_repair_reroute_decision=bounded_reroute_decision if bounded_reroute_decision.runtime_surface_gate_evaluated else None,
    )


def attach_observation_display_repair_meta(
    meta: Mapping[str, Any],
    result: ObservationDisplayRepairIntegrationResult,
) -> dict[str, Any]:
    """Attach Step 10 meta without changing public response keys."""

    out = dict(meta or {})
    integration_meta = result.as_meta()
    observation_reply_meta = dict(integration_meta.get("observation_reply_meta") or {})
    out["observation_display_repair_integration"] = integration_meta
    out["step10_observation_display_repair_integration"] = integration_meta
    if observation_reply_meta:
        out["observation_reply_meta"] = observation_reply_meta
        out["observation_reply_contract"] = observation_reply_meta

    diagnostic = out.get("diagnostic_summary")
    if isinstance(diagnostic, Mapping):
        diagnostic = dict(diagnostic)
        diagnostic["observation_display_repair_integration"] = integration_meta
        diagnostic["step10_observation_display_repair_integration"] = integration_meta
        if observation_reply_meta:
            diagnostic["observation_reply_meta"] = observation_reply_meta
            diagnostic["observation_reply_contract"] = observation_reply_meta
        if result.applied:
            diagnostic["observation_status"] = "passed"
            diagnostic["primary_reason"] = "passed"
            diagnostic["comment_text_allowed"] = True
        out["diagnostic_summary"] = diagnostic

    multi = out.get("multi_perspective")
    if isinstance(multi, Mapping):
        multi = dict(multi)
        multi["observation_display_repair_integration"] = integration_meta
        multi["step10_observation_display_repair_integration"] = integration_meta
        if observation_reply_meta:
            multi["observation_reply_meta"] = observation_reply_meta
            multi["observation_reply_contract"] = observation_reply_meta
        phase_gate = multi.get("phase_gate")
        if isinstance(phase_gate, Mapping):
            phase_gate = dict(phase_gate)
            phase_gate["step10_observation_display_repair_integration_ready"] = True
            phase_gate["step10_low_information_display_repair_applied"] = bool(result.applied)
            phase_gate["step10_display_gate_relaxed"] = False
            phase_gate["step10_public_status_extended"] = False
            multi["phase_gate"] = phase_gate
        out["multi_perspective"] = multi

    return out


__all__ = [
    "OBSERVATION_DISPLAY_REPAIR_INTEGRATION_VERSION",
    "OBSERVATION_DISPLAY_REPAIR_INTEGRATION_STEP",
    "ObservationDisplayRepairIntegrationResult",
    "attach_observation_display_repair_meta",
    "integrate_observation_display_repair",
    "should_reroute_to_low_information",
]
