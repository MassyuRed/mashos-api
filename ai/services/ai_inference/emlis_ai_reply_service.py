# -*- coding: utf-8 -*-
from __future__ import annotations

"""Top-level orchestration for EmlisAI reply rendering."""

from copy import deepcopy
import inspect
from dataclasses import asdict, is_dataclass
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping, Optional
from uuid import uuid4

from emlis_ai_capability import resolve_emlis_ai_capability_for_tier
from emlis_ai_context_service import build_emlis_ai_source_bundle
from emlis_ai_current_input_bundle import normalize_emlis_current_input
from emlis_ai_complete_initial_surface_availability import (
    COMPLETE_INITIAL_SURFACE_AVAILABILITY_PUBLIC_META_KEY,
    build_complete_initial_surface_availability_summary,
)
from emlis_ai_complete_initial_surface_recomposition import (
    COMPLETE_INITIAL_SURFACE_RECOMPOSITION_PUBLIC_META_KEY,
    build_complete_initial_surface_recomposition_candidate,
)
from emlis_ai_public_surface_requirement import resolve_public_surface_requirement
from emlis_ai_response_contract import ResponseKind, attach_emlis_internal_response_contract
from emlis_ai_quality_gate import attach_emlis_ai_quality_gate_meta, evaluate_emlis_ai_quality_gate
from emlis_ai_reply_final_review_service import review_emlis_ai_reply_text
from emlis_ai_style_profile_service import build_style_profile
from emlis_ai_user_address_service import build_emlis_observation_greeting, display_name_call
from emlis_ai_types import (
    DerivedModelHypothesis,
    DerivedUserModel,
    DiagnosticGateResult,
    EmlisAICapabilityConfig,
    EmlisAIDiagnosticSummary,
    EvidenceRef,
    ReplyEnvelope,
    ReplyLine,
    ReplyPlan,
    SourceBundle,
    StyleProfile,
    TopicAnchor,
    ValueAnchor,
    WorldModel,
)
from emlis_ai_user_model_store import (
    new_empty_derived_user_model,
    save_emlis_ai_user_model_for_user,
)
from emlis_ai_user_label_connection_public_meta import (
    USER_LABEL_CONNECTION_META_ONLY_META_KEY,
    USER_LABEL_CONNECTION_PUBLIC_META_KEY,
    USER_LABEL_CONNECTION_VISIBLE_SURFACE_META_KEY,
    attach_user_label_connection_meta_only_integration,
    build_user_label_connection_meta_only_integration,
    user_label_connection_public_summary,
)
from emlis_ai_user_label_connection_surface import (
    build_user_label_connection_visible_surface_binding_meta,
    user_label_connection_visible_surface_public_summary,
)
from emlis_ai_user_label_connection_p5_readiness import build_user_label_connection_p5_readiness
from emlis_ai_user_label_connection_p5_visibility_boundary import build_user_label_connection_p5_visibility_boundary
from emlis_ai_user_label_connection_p5_eligibility_matrix import build_user_label_connection_p5_eligibility_matrix
from emlis_ai_user_label_connection_p5_surface_role_plan import build_user_label_connection_p5_surface_role_plan
from emlis_ai_user_label_connection_p5_safety_guard import build_user_label_connection_p5_safety_guard
from emlis_ai_user_label_connection_p5_product_quality_review import build_user_label_connection_p5_product_quality_review
from emlis_ai_user_label_connection_p5_limited_visible_connection import build_user_label_connection_p5_limited_visible_connection
from emlis_ai_user_label_connection_p5_regression_handoff import build_user_label_connection_p5_regression_handoff
from emlis_ai_structure_insight_p6_entry_freeze import build_structure_insight_p6_entry_freeze
from emlis_ai_structure_insight_p6_inventory import build_structure_insight_p6_inventory
from emlis_ai_structure_insight_p6_family_boundary import build_structure_insight_p6_family_boundary
from emlis_ai_structure_insight_p6_relation_policy import build_structure_insight_p6_relation_policy
from emlis_ai_structure_insight_p6_quality_rubric import (
    P6_QUALITY_RUBRIC_DIMENSION_TARGETS,
    build_structure_insight_p6_quality_rubric,
)
from emlis_ai_structure_insight_p6_gate_hardening import build_structure_insight_p6_gate_hardening
from emlis_ai_structure_insight_p6_surface_role_plan import build_structure_insight_p6_surface_role_plan
from emlis_ai_structure_insight_p6_family_review import build_structure_insight_p6_family_review
from emlis_ai_structure_insight_p6_product_quality_review import build_structure_insight_p6_product_quality_review
from emlis_ai_structure_insight_p6_regression_handoff import build_structure_insight_p6_regression_handoff
from emlis_ai_structure_insight_p6_limited_surface_connection import (
    REASON_P6_POST_CONNECTION_GATE_BLOCKED,
    build_structure_insight_p6_limited_surface_candidate_probe,
    build_structure_insight_p6_limited_surface_connection,
    structure_insight_p6_limited_surface_connection_public_summary,
)
from emlis_ai_p5_p6_split_test_matrix import build_p5_p6_handoff_lock
from emlis_ai_world_model_service import build_emlis_ai_world_model

from emlis_ai_evidence_ledger_service import build_evidence_ledger
from emlis_ai_observation_structure_material_service import (
    build_observation_structure_material,
    observation_structure_material_forward_meta,
    observation_structure_material_gate_report,
)
from emlis_ai_composer_client_registry import default_composer_flag_state, resolve_emlis_ai_composer_client
from emlis_ai_conversation_composer_service import compose_emlis_conversation_candidate, phase6_composer_contract_ready
from emlis_ai_limited_observation_scope_service import build_limited_observation_scope, has_limited_scope_safety_boundary
from emlis_ai_limited_release_service import build_phase7_rollout_metrics, evaluate_limited_composer_release
from emlis_ai_limited_composer_extension_baseline import (
    build_limited_composer_binding_presence_meta,
    build_limited_composer_connection_visibility_meta,
    build_limited_composer_diagnostic_summary_extension_meta,
    build_limited_composer_extension_baseline_meta,
)
from emlis_ai_rollout_metrics_service import build_step16_rollout_metrics
from emlis_ai_ap0_migration_decision_service import (
    build_complete_initial_entry_ap0_decision,
    build_step18_ap0_migration_decision,
)
from emlis_ai_a_plan_equivalent_composer_service import build_step19_a_plan_equivalent_meta
from emlis_ai_long_term_quality_service import build_step20_long_term_quality_meta
from emlis_ai_complete_reply_diagnostics_service import (
    build_complete_reply_service_diagnostics,
    build_positive_recovery_relation_diagnostic,
)
from emlis_ai_diagnostic_failure_taxonomy import (
    attach_diagnostic_failure_taxonomy_meta,
    build_diagnostic_failure_taxonomy_meta,
)
from emlis_ai_complete_scorecard_service import build_complete_scorecard_harness
from emlis_ai_complete_product_quality_scorecard_service import (
    build_complete_product_quality_blind_qa_rubric,
    build_complete_product_quality_scorecard,
    build_complete_product_quality_scorecard_event_schema,
)
from emlis_ai_complete_release_ladder_service import build_complete_product_quality_release_ladder
from emlis_ai_runtime_surface_complete_activation_branch import build_runtime_surface_complete_activation_branch
from emlis_ai_runtime_surface_pre_return_gate import build_runtime_surface_pre_return_gate_report
from emlis_ai_visible_surface_acceptance_gate import build_visible_surface_acceptance_gate_report
from emlis_ai_bounded_repair_reroute import (
    ACTION_RERENDER_SHALLOW_V2 as BOUNDED_ACTION_RERENDER_SHALLOW_V2,
    ACTION_RERENDER_SURFACE as BOUNDED_ACTION_RERENDER_SURFACE,
    decide_bounded_repair_reroute,
)
from emlis_ai_complete_initial_fixture_qa_service import build_complete_initial_fixture_qa_run
from emlis_ai_coverage_matrix_service import build_emlis_coverage_matrix, build_emlis_limited_composer_scorecard_harness
from emlis_ai_limited_composer_e2e_contract import build_limited_composer_e2e_display_contract
from emlis_ai_limited_composer_extension_exit_gate import build_limited_composer_extension_e2e_exit_gate
from emlis_ai_safety_boundary_service import build_emlis_safety_boundary_report
from emlis_ai_safety_triage import (
    EMLIS_SAFETY_TRIAGE_META_KEY,
    TRIAGE_SAFE_OBSERVATION,
    TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER,
    build_emlis_safety_triage_decision,
)
from emlis_ai_self_denial_safe_state_answer import (
    SELF_DENIAL_SAFE_STATE_OBSERVATION_REPLY_KIND,
    build_self_denial_safe_state_answer_result,
)
from emlis_ai_input_material_bundle import EMLIS_INPUT_MATERIAL_BUNDLE_META_KEY
from emlis_ai_observation_eligibility_router import (
    EMLIS_OBSERVATION_ELIGIBILITY_ROUTER_META_KEY,
    attach_phase20_3_observation_eligibility_route_meta,
    route_emlis_observation_material_eligibility,
)
from emlis_ai_perspective_observers import phase4_observer_contract_ready, run_perspective_observers
from emlis_ai_perspective_board import build_perspective_board, phase5_board_contract_ready, validate_perspective_board
from emlis_ai_observation_integrator_service import integrate_perspective_board, phase5_observation_graph_ready, validate_observation_graph
from emlis_ai_observation_display_repair_integration import attach_observation_display_repair_meta, integrate_observation_display_repair
from emlis_ai_gate_recovery_loop import (
    attach_gate_recovery_loop_meta,
    build_gate_recovery_loop_decision,
    recover_emlis_gate_failure,
)
from emlis_ai_gate_recovery_public_boundary import (
    RECOVERY_CONTEXT_POST_FINAL_PRE_RETURN_GATE,
    RECOVERY_CONTEXT_PRE_PUBLIC_DISPLAY_GATE,
    decide_gate_recovery_public_boundary,
    gate_recovery_public_display_allowed,
)
from emlis_ai_gate_recovery_public_constants import (
    CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE,
)
from emlis_ai_listener_reader_judge import judge_listener_readability
from emlis_ai_limited_relation_taxonomy import allowed_relation_types, canonical_relation_type
from emlis_ai_relation_surface_contract import normalize_relation_surface_type
from emlis_ai_grounding_judge import judge_grounding
from emlis_ai_template_echo_guard import guard_template_echo
from emlis_ai_display_gate import GATE_BINDING_CONTRACT_VERSION, build_emlis_gate_trace, build_phase10_release_readiness, decide_emlis_observation_display, phase7_judge_contract_ready, phase8_display_gate_contract_ready
from emotion_history_search_service import build_open_topic_anchor_candidates, extract_repeated_categories
from cocolon_text_generation_core.policies import (
    CORE_ID_EMLIS,
    TEXT_GENERATION_CORE_PHASE8_NEXT_PHASE,
    TEXT_GENERATION_CORE_PHASE8_STOP_POINT,
)

_NEGATIVE_EMOTIONS = {"不安", "悲しみ", "怒り", "恐れ", "焦り"}

_COMPLETE_PRODUCT_QUALITY_DIAGNOSTIC_CONTRACT_VERSION = "emlis.complete_product_quality_connection.v1"
_BINDING_DECISION_GATES = {"grounding", "display"}
_OBSERVATION_DIAGNOSTIC_LOCKDOWN_REPLY_META_VERSION = "emlis.observation_diagnostic_lockdown.reply_meta.v1"
_STEP10_PHASE7_ROLLOUT_REJECTION_REASONS = {
    "limited_composer_rollout_not_allowed",
    "limited_composer_rollout_off",
    "complete_initial_rollout_not_allowed",
}
_STEP10_PHASE7_ROLLOUT_REASON_CODES = {"rollout_stage_off", "rollout_stage_not_matched"}

_PHASE20_13_POST_FINAL_GATE_RECOVERY_META_KEY = "phase20_13_post_final_gate_recovery"
_PHASE20_13_POST_FINAL_GATE_RECOVERY_SCHEMA_VERSION = "cocolon.emlis.post_final_gate_recovery.v1"
_PHASE20_13_POST_FINAL_GATE_RECOVERY_SOURCE_PHASE = "Phase20-13_Post_Final_Gate_Recovery"
_PHASE20_5_GATE_RECOVERY_PUBLIC_BOUNDARY_META_KEY = "phase20_5_gate_recovery_public_boundary"
_REPLY_SERVICE_GATE_RECOVERY_PUBLIC_BOUNDARY_SCHEMA_VERSION = (
    "cocolon.emlis.reply_service_gate_recovery_public_boundary.v1"
)
_REPLY_SERVICE_GATE_RECOVERY_PUBLIC_BOUNDARY_SOURCE_PHASE = (
    "ReplyService_GateRecovery_PublicBoundary_Insurance_P4"
)
_REPLY_SERVICE_RECOMPOSITION_EXISTING_GATE_CHAIN_SCHEMA_VERSION = (
    "cocolon.emlis.complete_initial_surface_recomposition.existing_gate_chain.v1"
)
_REPLY_SERVICE_RECOMPOSITION_EXISTING_GATE_CHAIN_SOURCE_PHASE = (
    "PublicObservationRecovery_P8_ReplyServiceExistingGateChain"
)
_PHASE20_13_DISPLAYABLE_RESPONSE_KINDS = {
    ResponseKind.NORMAL_OBSERVATION.value,
    ResponseKind.LOW_INFORMATION_OBSERVATION.value,
    ResponseKind.LIMITED_GROUNDING_OBSERVATION.value,
    ResponseKind.SELF_DENIAL_SAFE_STATE_ANSWER.value,
}
_PHASE20_13_RECOVERABLE_MATERIAL_QUALITIES = {"eligible", "low_information", "limited_grounding"}


_EMOTION_STRENGTH_DISPLAY_RE = re.compile(r"(喜び|悲しみ|怒り|不安|平穏|自己理解|恐れ|焦り)（(?:弱|中|強)）")


def _naturalize_reply_line(line: Any) -> str:
    text = str(line or "").strip()
    if not text:
        return ""
    # 強度は表示文から除外する。内部metaには残して互換性を維持する。
    text = _EMOTION_STRENGTH_DISPLAY_RE.sub(r"\1", text)
    text = re.sub(
        r"中心としては(.+?)を見ていますが、(.+?)もなかったことにせず一緒に受け取ります。?",
        r"\1だけでなく、\2も同じ場所にあったのですね。",
        text,
    )
    text = re.sub(
        r"(.+?かなぁ)のあと、(.+?したい)というところが残っていたのですね。?",
        r"「\1」という不確かさと、「\2」という願いを、同じ流れとして見ています。",
        text,
    )
    replacements = {
        "というところが、今回いちばん残っていた言葉なのだと思います": "と書いてくれたところに、今の気持ちが集まっていたのですね",
        "というところが残っていたのですね": "ことも、今回の流れの中にありました",
        "という部分も、流さずに見ています": "ことも、今回の流れの中にありました",
        "中心としては": "",
        "もなかったことにせず一緒に受け取ります": "も同じ場所にあったのですね",
        "入力として受け取ります": "今の気持ちとして見ます",
        "受け取りました": "見ています",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    text = text.replace("ですです", "です")
    text = re.sub(r"になるです([。！？!?]|$)", r"になります\1", text)
    text = re.sub(r"しているです([。！？!?]|$)", r"しています\1", text)
    text = re.sub(r"だったです([。！？!?]|$)", r"でした\1", text)
    text = re.sub(r"したです([。！？!?]|$)", r"しました\1", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _naturalize_reply_text(text: Any) -> str:
    return "\n".join(
        line for line in (_naturalize_reply_line(part) for part in str(text or "").splitlines()) if line
    ).strip()


def _now_iso_z() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _current_ref(bundle: SourceBundle) -> EvidenceRef:
    return EvidenceRef(
        kind="emotion",
        ref_id=str(bundle.current_input.get("id") or bundle.current_input.get("created_at") or "current"),
        weight=1.0,
    )


def _previous_emlis_outputs_from_bundle(bundle: SourceBundle) -> List[Dict[str, Any]]:
    """Collect optional same-user previous Emlis outputs for Step20 QA meta.

    This is intentionally read-only.  It does not fetch, infer, or write history;
    callers may pass already-owned history through side_state/debug/current_input.
    """

    outputs: List[Dict[str, Any]] = []

    def add_many(values: Any) -> None:
        if isinstance(values, (list, tuple)):
            for item in values:
                if isinstance(item, dict):
                    outputs.append(dict(item))
                elif str(item or "").strip():
                    outputs.append({"comment_text": str(item)})

    if isinstance(bundle.current_input, dict):
        add_many(bundle.current_input.get("previous_emlis_outputs"))
        add_many(bundle.current_input.get("previous_observation_outputs"))
    if isinstance(bundle.side_state, dict):
        add_many(bundle.side_state.get("previous_emlis_outputs"))
        add_many(bundle.side_state.get("previous_observation_outputs"))
    if isinstance(bundle.debug, dict):
        add_many(bundle.debug.get("previous_emlis_outputs"))
        add_many(bundle.debug.get("previous_observation_outputs"))
    # Keep the list bounded for QA meta size; Step20 needs trend signals, not a dump.
    return outputs[-12:]


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _phase20_13_response_kind_from_route(
    route_meta: Mapping[str, Any] | None,
    *,
    material_quality: str = "",
    safety_triage_kind: str = "",
) -> str:
    triage = _clean(safety_triage_kind)
    if triage == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER:
        return ResponseKind.SELF_DENIAL_SAFE_STATE_ANSWER.value
    meta = route_meta if isinstance(route_meta, Mapping) else {}
    quality = _clean(material_quality) or _clean(meta.get("material_quality"))
    if quality == "low_information":
        return ResponseKind.LOW_INFORMATION_OBSERVATION.value
    if quality == "limited_grounding":
        return ResponseKind.LIMITED_GROUNDING_OBSERVATION.value
    response_kind = _clean(meta.get("response_kind"))
    if response_kind in _PHASE20_13_DISPLAYABLE_RESPONSE_KINDS:
        return response_kind
    return ResponseKind.NORMAL_OBSERVATION.value


def _phase20_13_observation_quality_meta(*, material_quality: str, unknown_slots: Iterable[Any] | None = None) -> Dict[str, Any]:
    unknown = _dedupe_reason_codes([str(v) for v in list(unknown_slots or []) if str(v or "").strip()]) or ["event"]
    low_information = _clean(material_quality) == "low_information"
    return {
        "source_phase": _PHASE20_13_POST_FINAL_GATE_RECOVERY_SOURCE_PHASE,
        "material_quality": _clean(material_quality),
        "public_response_key_change": False,
        "body_non_empty": True,
        "comment_text_non_empty": True,
        "known_scope_observation_present": True,
        "low_info_known_scope_present": True,
        "contains_humility_marker": True,
        "humility_marker_present": True,
        "contains_question": low_information,
        "question_present": low_information,
        "low_info_question_present": low_information,
        "question_not_only": True,
        "question_only": False,
        "question_only_surface": False,
        "unknown_slots": unknown,
        "raw_input_included": False,
        "comment_text_body_included": False,
    }


def _phase20_13_final_gate_name(
    *,
    runtime_surface_pre_return_gate_report: Mapping[str, Any] | None = None,
    visible_surface_acceptance_gate_report: Mapping[str, Any] | None = None,
) -> str:
    visible = visible_surface_acceptance_gate_report if isinstance(visible_surface_acceptance_gate_report, Mapping) else {}
    runtime = runtime_surface_pre_return_gate_report if isinstance(runtime_surface_pre_return_gate_report, Mapping) else {}
    if visible and bool(visible.get("passed")) is False:
        return "final_visible_surface_acceptance_gate"
    if runtime and bool(runtime.get("passed")) is False:
        return "final_pre_return_gate"
    return "final_pre_return_gate"


def _should_attempt_post_final_gate_recovery(
    *,
    display_decision: Any,
    final_candidate_text: str,
    safety_requires_block: bool,
    safety_report: Any = None,
    safety_triage_kind: str = "",
    material_quality: str = "",
    response_kind: str = "",
    post_final_recovery_already_attempted: bool = False,
) -> bool:
    if bool(post_final_recovery_already_attempted):
        return False
    if str(getattr(display_decision, "observation_status", "") or "") == "passed":
        return False
    if not _clean(final_candidate_text):
        return False
    if bool(safety_requires_block) or bool(getattr(safety_report, "requires_block", False)):
        return False
    if _clean(safety_triage_kind) != TRIAGE_SAFE_OBSERVATION:
        return False
    if _clean(material_quality) not in _PHASE20_13_RECOVERABLE_MATERIAL_QUALITIES:
        return False
    if _clean(response_kind) not in _PHASE20_13_DISPLAYABLE_RESPONSE_KINDS:
        return False
    return True


def _build_phase20_13_post_final_gate_recovery_meta(
    *,
    attempted: bool,
    applied: bool,
    original_final_status: str,
    final_status_after_recovery: str,
    response_kind: str,
    material_quality: str,
    recovery_policy: str,
    from_gate: str,
    blocked_reasons: Iterable[Any] | None = None,
    public_boundary_meta: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    meta = {
        "schema_version": _PHASE20_13_POST_FINAL_GATE_RECOVERY_SCHEMA_VERSION,
        "source_phase": _PHASE20_13_POST_FINAL_GATE_RECOVERY_SOURCE_PHASE,
        "attempted": bool(attempted),
        "applied": bool(applied),
        "attempt_count": 1 if attempted else 0,
        "original_final_status": _clean(original_final_status),
        "final_status_after_recovery": _clean(final_status_after_recovery),
        "response_kind": _clean(response_kind),
        "material_quality": _clean(material_quality),
        "recovery_policy": _clean(recovery_policy),
        "from_gate": _clean(from_gate) or "final_pre_return_gate",
        "display_gate_relaxed": False,
        "safety_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "fixed_fallback_used": False,
        "public_response_key_change": False,
        "comment_text_body_included": False,
        "raw_input_included": False,
        "empty_comment_text_exit_allowed": False,
        "blocked_reasons": _dedupe_reason_codes(blocked_reasons or []),
    }
    if isinstance(public_boundary_meta, Mapping):
        boundary = dict(public_boundary_meta)
        decision = boundary.get("gate_recovery_public_boundary_decision")
        meta["reply_service_public_boundary"] = boundary
        meta["public_boundary_checked"] = True
        meta["public_boundary_blocked"] = bool(boundary.get("blocked"))
        meta["public_display_allowed_by_boundary"] = bool(boundary.get("public_display_allowed"))
        meta["public_boundary_blockers"] = _dedupe_reason_codes(boundary.get("blocked_reasons") or [])
        candidate_source_kind = _clean(
            boundary.get("candidate_source_kind")
            or boundary.get("adopted_candidate_source_kind")
            or boundary.get("final_surface_origin_candidate_source_kind")
        )
        if candidate_source_kind:
            meta["candidate_source_kind"] = candidate_source_kind
            meta["public_candidate_source_kind"] = candidate_source_kind
            meta["final_surface_origin_candidate_source_kind"] = (
                candidate_source_kind if bool(applied) else ""
            )
        if boundary.get("public_candidate_rebuilt_after_recovery") is not None:
            meta["public_candidate_rebuilt_after_recovery"] = bool(
                boundary.get("public_candidate_rebuilt_after_recovery")
            )
        if boundary.get("diagnostic_surface_used") is not None:
            meta["diagnostic_surface_used"] = bool(boundary.get("diagnostic_surface_used"))
        normal_rebuild_attempted = bool(
            boundary.get("normal_observation_rebuild_attempted")
            or candidate_source_kind == CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
        )
        if normal_rebuild_attempted:
            meta["normal_observation_rebuild_attempted"] = True
            meta["normal_observation_rebuild_applied"] = bool(
                applied and boundary.get("normal_observation_rebuild_applied") is not False
            )
            meta["normal_observation_rebuild_source_kind"] = (
                CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
            )
            meta["normal_observation_rebuild_blocked_reasons"] = _dedupe_reason_codes(
                boundary.get("normal_observation_rebuild_blocked_reasons")
                or ([] if applied else boundary.get("blocked_reasons") or [])
            )
        if isinstance(decision, Mapping):
            meta["gate_recovery_public_boundary_decision"] = dict(decision)
    return meta


def _composer_resolution_public_boundary_meta(composer_client_resolution: Any) -> Dict[str, Any]:
    """Return the minimal, text-free composer-resolution material for P4 boundary checks."""

    if isinstance(composer_client_resolution, Mapping):
        reasons = composer_client_resolution.get("rejection_reasons") or []
        return {"rejection_reasons": _dedupe_reason_codes(reasons)}
    reasons = getattr(composer_client_resolution, "rejection_reasons", ()) if composer_client_resolution is not None else ()
    as_meta = getattr(composer_client_resolution, "as_meta", None)
    if callable(as_meta):
        try:
            payload = as_meta()
            if isinstance(payload, Mapping):
                reasons = payload.get("rejection_reasons") or reasons
        except Exception:
            pass
    return {"rejection_reasons": _dedupe_reason_codes(reasons)}


def _reply_service_gate_recovery_public_boundary_decision(
    gate_recovery_loop_result: Any,
    *,
    recovery_context: str,
    composer_client_resolution: Any = None,
) -> Dict[str, Any]:
    """P4 insurance boundary before reply_service adopts a recovered candidate.

    The Gate Recovery Loop owns P3 blocking, but reply_service is the final place
    where a recovery candidate can replace the public candidate.  This check is
    intentionally body-free: it passes only candidate lineage/meta and a minimal
    composer-resolution reason list into the P2 boundary decision.
    """

    candidate = getattr(gate_recovery_loop_result, "composer_candidate", None)
    composer_meta: Dict[str, Any] = {}
    candidate_meta = getattr(candidate, "composer_meta", {}) if candidate is not None else {}
    if isinstance(candidate_meta, Mapping):
        composer_meta.update(dict(candidate_meta))
    surface_binding_meta = getattr(gate_recovery_loop_result, "surface_binding_meta", None)
    if isinstance(surface_binding_meta, Mapping):
        surface_binding_copy = dict(surface_binding_meta)
        candidate_public_role = str(composer_meta.get("public_surface_role") or "").strip()
        candidate_source_kind = str(composer_meta.get("candidate_source_kind") or "").strip()
        # P6 allows Gate Recovery to rebuild a public candidate through the
        # low-information composer.  The Gate Recovery loop still carries the
        # diagnostic material-surface binding as meta-only evidence, but that
        # diagnostic binding must not overwrite the rebuilt candidate lineage at
        # the final reply_service adoption boundary.
        if (
            candidate is not None
            and candidate_public_role == "public_observation_candidate"
            and candidate_source_kind
        ):
            composer_meta.setdefault("diagnostic_gate_recovery_surface_binding_meta", surface_binding_copy)
        else:
            composer_meta.update(surface_binding_copy)
    decision_candidate = candidate if candidate is not None else {"composer_meta": composer_meta}
    return decide_gate_recovery_public_boundary(
        candidate=decision_candidate,
        composer_meta=composer_meta,
        recovery_context=recovery_context,
        composer_resolution=_composer_resolution_public_boundary_meta(composer_client_resolution),
    )


def _build_reply_service_gate_recovery_public_boundary_meta(
    *,
    recovery_context: str,
    gate_recovery_loop_result: Any,
    public_boundary_decision: Mapping[str, Any],
    adopted: bool,
) -> Dict[str, Any]:
    """Build meta-only P4/P6 evidence without storing the candidate body."""

    result_meta = (
        gate_recovery_loop_result.as_meta()
        if gate_recovery_loop_result is not None and hasattr(gate_recovery_loop_result, "as_meta")
        else {}
    )
    if not isinstance(result_meta, Mapping):
        result_meta = {}
    blocked_reasons = _dedupe_reason_codes(
        public_boundary_decision.get("blockers") if isinstance(public_boundary_decision, Mapping) else []
    )
    public_display_allowed = gate_recovery_public_display_allowed(public_boundary_decision)
    candidate_summary = _reply_service_gate_recovery_candidate_summary(gate_recovery_loop_result)
    candidate_source_kind = _clean(candidate_summary.get("candidate_source_kind"))
    normal_rebuild_attempted = bool(candidate_summary.get("normal_observation_rebuild_attempted"))
    normal_rebuild_applied = bool(adopted and normal_rebuild_attempted and public_display_allowed)
    return {
        "schema_version": _REPLY_SERVICE_GATE_RECOVERY_PUBLIC_BOUNDARY_SCHEMA_VERSION,
        "source_phase": _REPLY_SERVICE_GATE_RECOVERY_PUBLIC_BOUNDARY_SOURCE_PHASE,
        "recovery_context": _clean(recovery_context),
        "attempted": gate_recovery_loop_result is not None,
        "gate_recovery_loop_applied": bool(getattr(gate_recovery_loop_result, "applied", False)),
        "public_display_allowed": public_display_allowed,
        "adopted": bool(adopted),
        "blocked": bool(not adopted),
        "blocked_reasons": blocked_reasons,
        "gate_recovery_public_boundary_decision": dict(public_boundary_decision or {}),
        "gate_recovery_loop_result": dict(result_meta),
        # P6: classify the actual public candidate selected by the loop.  The
        # loop-result meta still contains diagnostic material-surface evidence;
        # these fields keep reply_service/post-final diagnostics pointed at the
        # adopted public candidate without serializing any candidate body.
        "candidate_source_kind": candidate_source_kind,
        "public_candidate_source_kind": candidate_source_kind,
        "adopted_candidate_source_kind": candidate_source_kind if bool(adopted) else "",
        "final_surface_origin_candidate_source_kind": candidate_source_kind if bool(adopted) else "",
        "composer_model": _clean(candidate_summary.get("composer_model")),
        "generation_method": _clean(candidate_summary.get("generation_method")),
        "public_surface_role": _clean(candidate_summary.get("public_surface_role")),
        "public_candidate_rebuilt_after_recovery": bool(
            candidate_summary.get("public_candidate_rebuilt_after_recovery")
        ),
        "diagnostic_surface_used": bool(candidate_summary.get("diagnostic_surface_used")),
        "normal_observation_rebuild_attempted": normal_rebuild_attempted,
        "normal_observation_rebuild_applied": normal_rebuild_applied,
        "normal_observation_rebuild_source_kind": (
            CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
            if normal_rebuild_attempted
            else ""
        ),
        "normal_observation_rebuild_blocked_reasons": (
            [] if normal_rebuild_applied else list(blocked_reasons if normal_rebuild_attempted else [])
        ),
        "public_response_key_change": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "safety_gate_relaxed": False,
        "raw_input_included": False,
        "comment_text_body_included": False,
    }


def _reply_service_gate_recovery_public_boundary_allows(meta: Mapping[str, Any] | None) -> bool:
    return bool(isinstance(meta, Mapping) and meta.get("public_display_allowed") is True)


def _reply_service_gate_recovery_public_boundary_blockers(meta: Mapping[str, Any] | None) -> List[str]:
    if not isinstance(meta, Mapping):
        return []
    return _dedupe_reason_codes(meta.get("blocked_reasons") or [])


def _reply_service_gate_recovery_candidate_summary(gate_recovery_loop_result: Any) -> Dict[str, Any]:
    """Return body-free public candidate lineage selected by Gate Recovery.

    ``GateRecoveryLoopResult.as_meta()`` still carries the diagnostic material
    surface binding as meta-only evidence.  Reply service needs a separate
    source summary for the actual adopted public candidate so post-final
    diagnostics do not classify a rebuilt public observation as the blocked
    diagnostic surface.
    """

    candidate = getattr(gate_recovery_loop_result, "composer_candidate", None)
    candidate_meta = getattr(candidate, "composer_meta", {}) if candidate is not None else {}
    if not isinstance(candidate_meta, Mapping):
        candidate_meta = {}
    lineage = candidate_meta.get("candidate_lineage")
    if not isinstance(lineage, Mapping):
        lineage = {}
    candidate_source_kind = _clean(candidate_meta.get("candidate_source_kind"))
    composer_model = _clean(candidate_meta.get("composer_model") or getattr(candidate, "composer_model", ""))
    generation_method = _clean(
        candidate_meta.get("generation_method") or getattr(candidate, "generation_method", "")
    )
    normal_rebuild_attempted = bool(
        candidate_source_kind == CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
        or candidate_meta.get("normal_observation_rebuild_connected") is True
        or candidate_meta.get("normal_observation_rebuild_ready") is True
    )
    return {
        "candidate_source_kind": candidate_source_kind,
        "composer_model": composer_model,
        "generation_method": generation_method,
        "public_surface_role": _clean(candidate_meta.get("public_surface_role")),
        "public_candidate_rebuilt_after_recovery": bool(
            lineage.get("public_candidate_rebuilt_after_recovery") is True
            or candidate_meta.get("public_candidate_rebuilt_after_recovery") is True
        ),
        "diagnostic_surface_used": bool(
            lineage.get("diagnostic_surface_used") is True
            or candidate_meta.get("diagnostic_surface_used") is True
        ),
        "normal_observation_rebuild_attempted": normal_rebuild_attempted,
        "normal_observation_rebuild_source_kind": (
            CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
            if normal_rebuild_attempted
            else ""
        ),
        "raw_input_included": False,
        "comment_text_body_included": False,
    }
def _reply_service_gate_passed(report: Any) -> bool:
    if isinstance(report, Mapping):
        return bool(report.get("passed") is True)
    if hasattr(report, "passed"):
        return bool(getattr(report, "passed", False) is True)
    # ListenerReaderReport does not expose a `passed` field; the display gate
    # treats `understandable` as the reader gate pass signal.
    if hasattr(report, "understandable"):
        return bool(getattr(report, "understandable", False) is True)
    return False


def _reply_service_gate_rejection_reasons(report: Any) -> List[str]:
    if report is None:
        return []
    if isinstance(report, Mapping):
        reasons = (
            report.get("rejection_reasons")
            or report.get("blocked_reasons")
            or report.get("surface_blocker_reasons")
            or []
        )
        return _dedupe_reason_codes(reasons)
    return _dedupe_reason_codes(getattr(report, "rejection_reasons", []) or [])


def _reply_service_display_gate_passed(display_decision: Any) -> bool:
    return _clean(getattr(display_decision, "observation_status", "")) == "passed"


def _reply_service_gate_trace(display_decision: Any) -> Mapping[str, Any]:
    gate_trace = getattr(display_decision, "gate_trace", {}) if display_decision is not None else {}
    return gate_trace if isinstance(gate_trace, Mapping) else {}


def _reply_service_gate_trace_passed(
    gate_trace: Mapping[str, Any],
    gate_key: str,
    fallback_report: Any = None,
) -> bool:
    gate = gate_trace.get(gate_key)
    if isinstance(gate, Mapping) and isinstance(gate.get("passed"), bool):
        return bool(gate.get("passed"))
    return _reply_service_gate_passed(fallback_report)


def _reply_service_gate_trace_evaluated(
    gate_trace: Mapping[str, Any],
    gate_key: str,
    fallback_report: Any = None,
) -> bool:
    return isinstance(gate_trace.get(gate_key), Mapping) or fallback_report is not None


def _reply_service_gate_trace_rejection_reasons(
    gate_trace: Mapping[str, Any],
    gate_key: str,
) -> List[str]:
    gate = gate_trace.get(gate_key)
    if not isinstance(gate, Mapping):
        return []
    return _reply_service_gate_rejection_reasons(gate)


def _reply_service_recomposition_existing_gate_chain_summary(
    *,
    reader_report: Any = None,
    grounding_report: Any = None,
    template_echo_report: Any = None,
    runtime_surface_pre_return_gate_report: Mapping[str, Any] | None = None,
    visible_surface_acceptance_gate_report: Mapping[str, Any] | None = None,
    display_decision: Any = None,
    adopted: bool = False,
) -> Dict[str, Any]:
    """Summarise Step 8 gate passage without serialising candidate text.

    Recomposition may generate a candidate before the normal public observation
    is adopted.  Step 8 requires that the candidate is accepted only after the
    existing gates pass; this meta keeps that distinction explicit and
    fail-closed without relaxing any gate.
    """

    runtime_report = (
        dict(runtime_surface_pre_return_gate_report)
        if isinstance(runtime_surface_pre_return_gate_report, Mapping)
        else {}
    )
    visible_report = (
        dict(visible_surface_acceptance_gate_report)
        if isinstance(visible_surface_acceptance_gate_report, Mapping)
        else {}
    )
    display_status = _clean(getattr(display_decision, "observation_status", ""))
    display_rejection_reasons = _dedupe_reason_codes(
        getattr(display_decision, "rejection_reasons", []) or []
    )
    gate_trace = _reply_service_gate_trace(display_decision)
    reader_passed = _reply_service_gate_trace_passed(gate_trace, "reader", reader_report)
    grounding_passed = _reply_service_gate_trace_passed(gate_trace, "grounding", grounding_report)
    template_passed = _reply_service_gate_trace_passed(gate_trace, "template_echo", template_echo_report)
    runtime_passed = bool(runtime_report.get("passed") is True)
    visible_passed = bool(visible_report.get("passed") is True) or _reply_service_gate_trace_passed(
        gate_trace,
        "visible_surface_acceptance",
        visible_report,
    )
    display_passed = _reply_service_gate_trace_passed(
        gate_trace,
        "display",
    ) or _reply_service_display_gate_passed(display_decision)
    passed_by_all_existing_gates = all(
        (
            reader_passed,
            grounding_passed,
            template_passed,
            runtime_passed,
            visible_passed,
            display_passed,
        )
    )
    blocked_reasons = _dedupe_reason_codes(
        [
            *([] if reader_passed else ["reader_gate_failed"]),
            *([] if grounding_passed else ["grounding_gate_failed"]),
            *([] if template_passed else ["template_gate_failed"]),
            *([] if runtime_passed else ["runtime_surface_pre_return_gate_failed"]),
            *([] if visible_passed else ["visible_surface_acceptance_gate_failed"]),
            *([] if display_passed else ["display_gate_failed"]),
            *_reply_service_gate_rejection_reasons(reader_report),
            *_reply_service_gate_rejection_reasons(grounding_report),
            *_reply_service_gate_rejection_reasons(template_echo_report),
            *_reply_service_gate_rejection_reasons(runtime_report),
            *_reply_service_gate_rejection_reasons(visible_report),
            *_reply_service_gate_trace_rejection_reasons(gate_trace, "reader"),
            *_reply_service_gate_trace_rejection_reasons(gate_trace, "grounding"),
            *_reply_service_gate_trace_rejection_reasons(gate_trace, "template_echo"),
            *_reply_service_gate_trace_rejection_reasons(gate_trace, "visible_surface_acceptance"),
            *_reply_service_gate_trace_rejection_reasons(gate_trace, "display"),
            *display_rejection_reasons,
        ]
    )
    return {
        "schema_version": _REPLY_SERVICE_RECOMPOSITION_EXISTING_GATE_CHAIN_SCHEMA_VERSION,
        "source_phase": _REPLY_SERVICE_RECOMPOSITION_EXISTING_GATE_CHAIN_SOURCE_PHASE,
        "candidate_body_in_meta": False,
        "raw_input_included": False,
        "comment_text_body_included": False,
        "reader_gate_evaluated": _reply_service_gate_trace_evaluated(gate_trace, "reader", reader_report),
        "reader_gate_passed": reader_passed,
        "grounding_gate_evaluated": _reply_service_gate_trace_evaluated(gate_trace, "grounding", grounding_report),
        "grounding_gate_passed": grounding_passed,
        "template_gate_evaluated": _reply_service_gate_trace_evaluated(gate_trace, "template_echo", template_echo_report),
        "template_gate_passed": template_passed,
        "runtime_surface_pre_return_gate_evaluated": bool(runtime_report),
        "runtime_surface_pre_return_gate_passed": runtime_passed,
        "visible_surface_acceptance_gate_evaluated": bool(visible_report),
        "visible_surface_acceptance_gate_passed": visible_passed,
        "display_gate_evaluated": display_decision is not None,
        "display_gate_passed": display_passed,
        "display_observation_status": display_status,
        "passed_by_all_existing_gates": passed_by_all_existing_gates,
        "candidate_adopted_after_existing_gates": bool(adopted and passed_by_all_existing_gates),
        # Step 8 is fail-closed at the existing-gate boundary: even if a caller
        # has an adoption intent, the candidate is not considered adopted when
        # any existing gate failed.
        "fail_closed_when_gate_failed": bool(not passed_by_all_existing_gates),
        "blocked_reasons": blocked_reasons,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "runtime_surface_gate_relaxed": False,
        "visible_surface_gate_relaxed": False,
    }


def _evidence_ids_from_observation_graph(graph: Any) -> List[str]:
    """Collect evidence ids that belong to the graph currently being judged.

    Phase 4 uses this for scoped grounding: when the Limited Composer receives a
    scoped graph, Grounding should not validate sentences using evidence that
    only belongs to excluded full-graph claims.
    """

    out: List[str] = []

    def add(values: Any) -> None:
        for value in list(values or []):
            span_id = str(value or "").strip()
            if span_id and span_id not in out:
                out.append(span_id)

    primary = getattr(graph, "primary_state", None)
    add(getattr(primary, "evidence_span_ids", []) or [])
    for attr in ("pressure_sources", "limit_signals", "self_awareness", "value_or_strength_signals"):
        for claim in list(getattr(graph, attr, []) or []):
            add(getattr(claim, "evidence_span_ids", []) or [])
    for edge in list(getattr(graph, "core_tensions", []) or []):
        add(getattr(edge, "evidence_span_ids", []) or [])
    return out


_EXPECTED_RELATION_TYPE_ALLOWED = frozenset(
    {
        *allowed_relation_types(),
        "generic",
        "recovery",
        "positive_recovery",
        "recovering",
        "small_recovery",
        "contrast",
        "coexistence",
        "pressure",
        "approach_avoidance",
        "residue",
        "limit",
        "context",
        "center",
        "conflict",
        "relationship",
        "desire_fear",
        "long_meaning_arc",
    }
)
_EXPECTED_RELATION_EDGE_ID_RE = re.compile(r"(?:^|[._-])(?:e|edge|rel|relation)?\d+$")

# Retry only when the previous failure reason can actually be consumed by the
# selected Composer.  Display-phase reasons such as ``phase_not_complete`` are
# not Composer repair inputs; sending them into the next attempt can make the
# complete self-repair loop abort and overwrite a valid generated candidate with
# an unavailable one.
_COMPLETE_COMPOSER_RETRY_REASONS = frozenset(
    {
        "relation_not_expressed",
        "unsupported_sentence",
        "template_like",
        "raw_echo",
        "over_echo",
        "too_long",
        "overclaim",
        "unsupported_overclaim",
    }
)
_LIMITED_READER_RETRY_REASONS = frozenset({"addressee_not_clear", "relation_not_expressed"})
_RUNTIME_SURFACE_RERENDER_RETRY_REASONS = frozenset(
    {
        "runtime_surface_pre_return_gate_action_rerender_shallow_v2",
    }
)
_VISIBLE_SURFACE_RERENDER_RETRY_REASONS = frozenset(
    {
        "visible_surface_acceptance_gate_action_rerender_surface",
        "emotion_focus_unbridged_secondary",
        "positive_tone_over_burden_without_anchor",
    }
)


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _iter_relation_values(value: Any) -> Iterable[Any]:
    if value is None:
        return ()
    if isinstance(value, (str, bytes)):
        return (value,)
    if isinstance(value, Mapping):
        return ()
    if isinstance(value, Iterable):
        return value
    return (value,)


def _normalize_expected_relation_type_for_reader(value: Any) -> str:
    raw = re.sub(r"[^0-9a-zA-Z_\-.]+", "_", str(value or "").strip().lower()).strip("_")
    if not raw or raw in {"unknown", "none", "null"}:
        return ""
    # Edge ids such as conflict.e1 are graph-local ids, not Reader surface
    # relation types.  Passing them into Reader would mix routing ids with the
    # relation surface contract.
    if _EXPECTED_RELATION_EDGE_ID_RE.search(raw):
        return ""
    if raw.startswith(("edge_", "edge-", "relation_", "relation-", "rel_", "rel-")) and any(ch.isdigit() for ch in raw):
        return ""

    canonical = str(canonical_relation_type(raw) or raw).strip().lower()
    normalized = str(normalize_relation_surface_type(canonical or raw) or "").strip().lower()
    if normalized in {"", "unknown", "none", "null"}:
        return ""
    if raw in _EXPECTED_RELATION_TYPE_ALLOWED or canonical in _EXPECTED_RELATION_TYPE_ALLOWED or normalized in _EXPECTED_RELATION_TYPE_ALLOWED:
        return normalized
    return ""


def _expected_relation_types_for_reader(composer_candidate: Any) -> List[str]:
    """Extract Reader surface relation types from Composer candidate meta.

    The Reader must receive relation surface types, not graph edge ids.  Keep the
    extraction ordered from the strongest binding source to weaker supplemental
    metadata, and drop ids such as ``conflict.e1``.
    """

    meta = _as_mapping(getattr(composer_candidate, "composer_meta", {}) if composer_candidate is not None else {})
    out: List[str] = []

    def add_one(value: Any) -> None:
        relation_type = _normalize_expected_relation_type_for_reader(value)
        if relation_type and relation_type not in out:
            out.append(relation_type)

    def add_many(values: Any) -> None:
        for item in _iter_relation_values(values):
            add_one(item)

    # 1. sentence_binding_bundle.relation_types
    for bundle_key in ("sentence_binding_bundle", "binding_bundle", "binding"):
        bundle = _as_mapping(meta.get(bundle_key))
        add_many(bundle.get("relation_types"))

    # 2. sentence_bindings[*].relation_type
    sentence_bindings: List[Any] = []
    for bundle_key in ("sentence_binding_bundle", "binding_bundle", "binding"):
        bundle = _as_mapping(meta.get(bundle_key))
        for value in _iter_relation_values(bundle.get("bindings")):
            sentence_bindings.append(value)
    for value in _iter_relation_values(meta.get("sentence_bindings")):
        sentence_bindings.append(value)
    for binding in sentence_bindings:
        if isinstance(binding, Mapping):
            add_one(binding.get("relation_type") or binding.get("canonical_relation_type"))
        else:
            add_one(getattr(binding, "relation_type", "") or getattr(binding, "canonical_relation_type", ""))

    # 3. composer_meta.relation_types
    add_many(meta.get("relation_types"))
    add_many(meta.get("canonical_relation_types"))

    # 4. used_relation_ids are supplemental only; graph edge ids are excluded.
    add_many(meta.get("used_relation_ids"))
    add_many(getattr(composer_candidate, "used_relation_ids", []) if composer_candidate is not None else [])
    return out


def _reader_accepts_expected_relation_types() -> bool:
    try:
        signature = inspect.signature(judge_listener_readability)
    except (TypeError, ValueError):
        return True
    for parameter in signature.parameters.values():
        if parameter.kind == inspect.Parameter.VAR_KEYWORD:
            return True
        if parameter.name == "expected_relation_types":
            return True
    return False


def _judge_listener_readability_for_reply(comment_text: Any, composer_candidate: Any) -> Any:
    expected_relation_types = _expected_relation_types_for_reader(composer_candidate)
    if _reader_accepts_expected_relation_types():
        return judge_listener_readability(
            comment_text,
            expected_relation_types=expected_relation_types,
        )
    return judge_listener_readability(comment_text)


def _composer_retry_reason_allowlist(composer_client: Any) -> frozenset[str]:
    class_name = type(composer_client).__name__ if composer_client is not None else ""
    if class_name == "CocolonCompleteComposerClient":
        return _COMPLETE_COMPOSER_RETRY_REASONS
    return frozenset(
        (
            *_LIMITED_READER_RETRY_REASONS,
            *_RUNTIME_SURFACE_RERENDER_RETRY_REASONS,
            *_VISIBLE_SURFACE_RERENDER_RETRY_REASONS,
        )
    )


def _regeneration_reasons_for_retry(rejection_reasons: Iterable[Any], composer_client: Any) -> List[str]:
    allowed = _composer_retry_reason_allowlist(composer_client)
    out: List[str] = []
    for raw in list(rejection_reasons or []):
        reason = str(raw or "").strip()
        if reason and reason in allowed and reason not in out:
            out.append(reason)
    return out


def _collect_used_evidence(reply_lines: List[ReplyLine]) -> List[EvidenceRef]:
    seen: set[tuple[str, str, str]] = set()
    out: List[EvidenceRef] = []
    for line in reply_lines:
        for item in line.sentence_evidence.evidence:
            key = (item.kind, item.ref_id, str(item.note or ""))
            if key in seen:
                continue
            seen.add(key)
            out.append(item)
    return out


def _serialize_evidence_ref(item: EvidenceRef) -> Dict[str, Any]:
    return {
        "kind": item.kind,
        "ref_id": item.ref_id,
        "weight": float(item.weight),
        "note": item.note,
    }


def _serialize_emotion_display_item(item: Any) -> Dict[str, Any]:
    return {
        "type": _clean(getattr(item, "type", "")),
        "strength": _clean(getattr(item, "strength", "")),
        "strength_label": _clean(getattr(item, "strength_label", "")),
        "role": _clean(getattr(item, "role", "secondary")) or "secondary",
    }


def _serialize_user_word_anchor(item: Any) -> Dict[str, Any]:
    return {
        "anchor_key": _clean(getattr(item, "anchor_key", "")),
        "text": _clean(getattr(item, "text", "")),
        "source_field": _clean(getattr(item, "source_field", "")),
        "role": _clean(getattr(item, "role", "other")) or "other",
        "confidence": float(getattr(item, "confidence", 0.0) or 0.0),
        "evidence": [_serialize_evidence_ref(ev) for ev in list(getattr(item, "evidence", []) or [])],
    }


def _serialize_shaped_user_phrase(item: Any) -> Dict[str, Any]:
    return {
        "anchor_key": _clean(getattr(item, "anchor_key", "")),
        "raw_text": _clean(getattr(item, "raw_text", "")),
        "phrase": _clean(getattr(item, "phrase", "")),
        "sentence_fragment": _clean(getattr(item, "sentence_fragment", "")),
        "nominal": _clean(getattr(item, "nominal", "")),
        "role": _clean(getattr(item, "role", "other")) or "other",
        "source_field": _clean(getattr(item, "source_field", "")),
        "usability": _clean(getattr(item, "usability", "safe")) or "safe",
        "unsafe_reasons": [str(v) for v in list(getattr(item, "unsafe_reasons", []) or []) if str(v)],
    }


def _serialize_cross_core_anchor_packet(item: Any) -> Dict[str, Any]:
    groups = {
        "value_anchors": list(getattr(item, "value_anchors", []) or []),
        "state_anchors": list(getattr(item, "state_anchors", []) or []),
        "individuality_anchors": list(getattr(item, "individuality_anchors", []) or []),
        "boundary_anchors": list(getattr(item, "boundary_anchors", []) or []),
        "concept_anchors": list(getattr(item, "concept_anchors", []) or []),
        "reply_hints": list(getattr(item, "reply_hints", []) or []),
    }
    anchor_count = sum(len(values) for values in groups.values())
    labels: List[str] = []
    hints: List[str] = []
    for key, values in groups.items():
        for anchor in values:
            if not isinstance(anchor, dict):
                continue
            label = _clean(anchor.get("label") or anchor.get("user_definition") or anchor.get("recent_change") or anchor.get("role_pattern"),)
            if label and label not in labels:
                labels.append(label[:96])
            if key == "reply_hints":
                hint = _clean(anchor.get("hint") or anchor.get("receive_hint") or anchor.get("question_hint"),)
                if hint and hint not in hints:
                    hints.append(hint[:120])
            if len(labels) >= 6 and len(hints) >= 4:
                break
        if len(labels) >= 6 and len(hints) >= 4:
            break
    return {
        "schema_version": _clean(getattr(item, "schema_version", "")),
        "source_kind": _clean(getattr(item, "source_kind", "")),
        "source_id": _clean(getattr(item, "source_id", "")),
        "source_updated_at": _clean(getattr(item, "source_updated_at", "")),
        "anchor_count": anchor_count,
        "group_counts": {key: len(values) for key, values in groups.items()},
        "sample_labels": labels[:6],
        "sample_reply_hints": hints[:4],
    }


def _cross_core_source_key(source_kind: Any) -> str:
    kind = _clean(source_kind).lower()
    if kind in {"piece", "emotion_piece", "generated_piece"}:
        return "piece"
    if kind in {"emotion_report", "analysis_report", "emotion_analysis"}:
        return "emotion_report"
    if kind in {"self_structure_report", "self_report", "myprofile_report"}:
        return "self_structure_report"
    return kind or "cross_core_context"


def _cross_core_context_meta(world_model: WorldModel) -> Dict[str, Any]:
    packets = list(getattr(world_model.facts, "cross_core_context", []) or [])
    source_kinds = sorted({
        _cross_core_source_key(getattr(packet, "source_kind", ""))
        for packet in packets
        if _cross_core_source_key(getattr(packet, "source_kind", ""))
    })
    anchor_count = 0
    for packet in packets:
        for key in ("value_anchors", "state_anchors", "individuality_anchors", "boundary_anchors", "concept_anchors", "reply_hints"):
            anchor_count += len(list(getattr(packet, key, []) or []))
    return {
        "enabled": bool(packets),
        "matched_packet_count": len(packets),
        "source_kinds": source_kinds,
        "anchor_count": anchor_count,
        "current_input_filtered": True,
        "current_input_priority": True,
        "sample_packets": [_serialize_cross_core_anchor_packet(packet) for packet in packets[:5]],
    }


def _serialize_meaning_block(item: Any) -> Dict[str, Any]:
    return {
        "block_key": _clean(getattr(item, "block_key", "")),
        "role": _clean(getattr(item, "role", "")),
        "title": _clean(getattr(item, "title", "")),
        "summary": _clean(getattr(item, "summary", "")),
        "priority": float(getattr(item, "priority", 0.0) or 0.0),
        "clarity": float(getattr(item, "clarity", 0.0) or 0.0),
        "include_in_emlis_reply": bool(getattr(item, "include_in_emlis_reply", False)),
        "include_in_piece_core": bool(getattr(item, "include_in_piece_core", False)),
    }


def _serialize_whole_input_arc(item: Any) -> Dict[str, Any]:
    if item is None:
        return {}
    return {
        "arc_key": _clean(getattr(item, "arc_key", "")),
        "title": _clean(getattr(item, "title", "")),
        "summary": _clean(getattr(item, "summary", "")),
        "ordered_block_keys": list(getattr(item, "ordered_block_keys", []) or []),
        "core_wish_keys": list(getattr(item, "core_wish_keys", []) or []),
        "fear_keys": list(getattr(item, "fear_keys", []) or []),
        "present_action_keys": list(getattr(item, "present_action_keys", []) or []),
        "clarity": float(getattr(item, "clarity", 0.0) or 0.0),
    }


def _serialize_major_retention(item: Any) -> Dict[str, Any]:
    if item is None:
        return {}
    return {
        "clear_long_input": bool(getattr(item, "clear_long_input", False)),
        "total_block_count": int(getattr(item, "total_block_count", 0) or 0),
        "must_keep_block_keys": list(getattr(item, "must_keep_block_keys", []) or []),
        "should_keep_block_keys": list(getattr(item, "should_keep_block_keys", []) or []),
        "optional_block_keys": list(getattr(item, "optional_block_keys", []) or []),
        "forbidden_overcompression_targets": list(getattr(item, "forbidden_overcompression_targets", []) or []),
        "min_must_keep_coverage_ratio": float(getattr(item, "min_must_keep_coverage_ratio", 0.0) or 0.0),
        "reason": _clean(getattr(item, "reason", "")),
    }



def _serialize_observation_frame(item: Any) -> Dict[str, Any]:
    if item is None:
        return {"present": False}
    return {
        "present": True,
        "primary_state": _clean(getattr(item, "primary_state", "")),
        "tension_pairs": [
            {
                "left": _clean(getattr(pair, "left", "")),
                "right": _clean(getattr(pair, "right", "")),
                "relation": _clean(getattr(pair, "relation", "")),
            }
            for pair in list(getattr(item, "tension_pairs", []) or [])
        ],
        "pressure_sources": [_clean(v) for v in list(getattr(item, "pressure_sources", []) or []) if _clean(v)],
        "escape_or_limit_signal": _clean(getattr(item, "escape_or_limit_signal", "")),
        "self_awareness_signal": _clean(getattr(item, "self_awareness_signal", "")),
        "strength_signal": _clean(getattr(item, "strength_signal", "")),
        "companion_close": _clean(getattr(item, "companion_close", "")),
        "evidence_terms": [_clean(v) for v in list(getattr(item, "evidence_terms", []) or []) if _clean(v)],
        "required_line_roles": [_clean(v) for v in list(getattr(item, "required_line_roles", []) or []) if _clean(v)],
    }

def _serialize_value_observation_signal(item: Any) -> Dict[str, Any]:
    as_meta = getattr(item, "as_meta", None)
    if callable(as_meta):
        try:
            payload = as_meta()
            if isinstance(payload, dict):
                return dict(payload)
        except Exception:
            pass
    return {
        "signal_key": _clean(getattr(item, "signal_key", "")),
        "title": _clean(getattr(item, "title", "")),
        "observation_axis": _clean(getattr(item, "observation_axis", "")),
        "evidence_terms": list(getattr(item, "evidence_terms", []) or []),
        "target_cores": list(getattr(item, "target_cores", []) or []),
        "confidence": float(getattr(item, "confidence", 0.0) or 0.0),
        "no_diagnosis": bool(getattr(item, "no_diagnosis", True)),
        "no_personality_claim": bool(getattr(item, "no_personality_claim", True)),
    }


def _value_observation_meta(world_model: WorldModel) -> Dict[str, Any]:
    signals = list(getattr(world_model.facts, "value_observation_signals", []) or [])
    plan = getattr(world_model.facts, "value_observation_plan", None)
    as_meta = getattr(plan, "as_meta", None)
    if callable(as_meta):
        plan_payload = as_meta()
    else:
        plan_payload = {
            "input_level": "none",
            "signal_count": len(signals),
            "primary_signal_keys": [str(getattr(item, "signal_key", "") or "") for item in signals[:1]],
            "must_keep_signal_keys": [str(getattr(item, "signal_key", "") or "") for item in signals],
            "optional_signal_keys": [],
            "overcompression_risk": bool(signals),
            "grounding_terms": [],
        }
    return {
        "plan": dict(plan_payload or {}),
        "signals": [_serialize_value_observation_signal(item) for item in signals],
    }


def _composition_meta(world_model: WorldModel) -> Dict[str, Any]:
    plan = getattr(world_model.facts, "response_composition_plan", None)
    arc = getattr(world_model.facts, "reply_narrative_arc", None)
    frame = getattr(world_model.facts, "emlis_observation_frame", None)
    frame_payload = _serialize_observation_frame(frame)
    observation_fields = {
        "observation_frame_present": bool(frame_payload.get("present")),
        "observation_primary_state": _clean(frame_payload.get("primary_state")),
        "observation_required_line_roles": list(frame_payload.get("required_line_roles") or []),
    }
    if plan is None:
        return {
            "composition_key": "observation_frame.v1" if frame_payload.get("present") else "",
            "narrative_pattern": "emlis_observation_frame" if frame_payload.get("present") else "",
            "opening_thesis_present": bool(frame_payload.get("primary_state")),
            "response_composition_ok": True,
            "current_input_grounding_ok": True,
            "stale_meaning_block_leak_blocked": True,
            **observation_fields,
        }
    return {
        "composition_key": _clean(getattr(plan, "composition_key", "")),
        "narrative_pattern": _clean(getattr(plan, "narrative_pattern", "")),
        "ordered_line_roles": list(getattr(plan, "ordered_line_roles", []) or []),
        "required_line_roles": list(getattr(plan, "required_line_roles", []) or []),
        "opening_thesis": _clean(getattr(arc, "opening_thesis", "")) if arc is not None else "",
        "opening_thesis_present": bool(_clean(getattr(arc, "opening_thesis", "")) if arc is not None else "") or bool(frame_payload.get("primary_state")),
        "transition_policy": _clean(getattr(plan, "transition_policy", "")),
        "response_composition_ok": True,
        "current_input_grounding_ok": True,
        "stale_meaning_block_leak_blocked": True,
        **observation_fields,
    }

def _meaning_coverage_meta(world_model: WorldModel, plan: ReplyPlan) -> Dict[str, Any]:
    coverage = getattr(world_model.facts, "meaning_coverage_plan", None)
    frame = getattr(world_model.facts, "emlis_observation_frame", None)
    frame_payload = _serialize_observation_frame(frame)
    observation_meta = {
        "observation_frame_present": bool(frame_payload.get("present")),
        "observation_required_line_roles": list(frame_payload.get("required_line_roles") or []),
        "observation_evidence_terms": list(frame_payload.get("evidence_terms") or []),
    }
    blocks = list(getattr(world_model.facts, "meaning_blocks", []) or [])
    arc = getattr(world_model.facts, "whole_input_meaning_arc", None)
    retention = getattr(world_model.facts, "major_meaning_retention_plan", None)
    length_plan = plan.reply_length_plan
    if coverage is None:
        return {
            "input_level": "none",
            "clear_long_input": False,
            "meaning_block_count": len(blocks),
            "selected_block_count": 0,
            "selected_block_keys": [],
            "required_roles": [],
            "min_blocks_to_cover": 0,
            "coverage_ratio_target": 0.0,
            "sample_blocks": [_serialize_meaning_block(item) for item in blocks[:12]],
            "whole_input_meaning_arc": _serialize_whole_input_arc(arc),
            **observation_meta,
            **_serialize_major_retention(retention),
        }
    selected_keys = list(getattr(coverage, "selected_block_keys", []) or [])
    if length_plan is not None and int(getattr(length_plan, "selected_meaning_block_count", 0) or 0) > 0:
        selected_count = int(getattr(length_plan, "selected_meaning_block_count", 0) or 0)
    else:
        selected_count = len(selected_keys)
    return {
        "input_level": _clean(getattr(coverage, "input_level", "")),
        "clear_long_input": bool(getattr(coverage, "clear_long_input", False)),
        "meaning_block_count": int(getattr(coverage, "meaning_block_count", len(blocks)) or len(blocks)),
        "selected_block_count": selected_count,
        "selected_block_keys": selected_keys,
        "required_roles": list(getattr(coverage, "required_roles", []) or []),
        "min_blocks_to_cover": int(getattr(coverage, "min_blocks_to_cover", 0) or 0),
        "max_blocks_to_cover": int(getattr(coverage, "max_blocks_to_cover", 0) or 0),
        "coverage_ratio_target": float(getattr(coverage, "coverage_ratio_target", 0.0) or 0.0),
        "reason": _clean(getattr(coverage, "reason", "")),
        "sample_blocks": [_serialize_meaning_block(item) for item in blocks[:12]],
        "whole_input_meaning_arc": _serialize_whole_input_arc(arc),
        **observation_meta,
        **_serialize_major_retention(retention),
    }


def _reply_depth_meta(plan: ReplyPlan, capability: EmlisAICapabilityConfig) -> Dict[str, Any]:
    length_plan = plan.reply_length_plan
    if length_plan is None:
        return {
            "target_lines": 0,
            "max_lines": int(capability.max_reply_lines or 0),
            "tier_ceiling": int(capability.max_reply_lines or 0),
            "evidence_ceiling": 0,
            "history_usable": False,
            "interpretive_frame_usable": False,
            "cross_core_usable": False,
            "reason": "missing_reply_length_plan",
        }
    return {
        "target_lines": int(length_plan.target_lines or length_plan.max_lines or 0),
        "max_lines": int(length_plan.max_lines or 0),
        "tier_ceiling": int(length_plan.tier_ceiling or capability.max_reply_lines or 0),
        "evidence_ceiling": int(length_plan.evidence_ceiling or 0),
        "input_effort_score": float(length_plan.input_effort_score or 0.0),
        "memory_richness_score": float(length_plan.memory_richness_score or 0.0),
        "user_word_anchor_count": int(length_plan.user_word_anchor_count or 0),
        "history_usable": bool(length_plan.history_usable),
        "interpretive_frame_usable": bool(length_plan.interpretive_frame_usable),
        "cross_core_usable": bool(getattr(length_plan, "cross_core_usable", False)),
        "meaning_block_count": int(getattr(length_plan, "meaning_block_count", 0) or 0),
        "selected_meaning_block_count": int(getattr(length_plan, "selected_meaning_block_count", 0) or 0),
        "meaning_coverage_ratio": float(getattr(length_plan, "meaning_coverage_ratio", 0.0) or 0.0),
        "clear_long_input": bool(getattr(length_plan, "clear_long_input", False)),
        "major_must_keep_count": int(getattr(length_plan, "major_must_keep_count", 0) or 0),
        "major_must_keep_covered_count": int(getattr(length_plan, "major_must_keep_covered_count", 0) or 0),
        "major_must_keep_coverage_ratio": float(getattr(length_plan, "major_must_keep_coverage_ratio", 0.0) or 0.0),
        "reason": _clean(length_plan.reason),
    }


def _clone_or_create_working_model(
    *,
    capability: EmlisAICapabilityConfig,
    bundle: SourceBundle,
) -> Optional[DerivedUserModel]:
    if not capability.model_write_enabled and bundle.derived_user_model is None:
        return None
    if bundle.derived_user_model is not None:
        working_model = deepcopy(bundle.derived_user_model)
        if not working_model.schema_version:
            working_model.schema_version = "emlis_user_model.v2"
        if not working_model.model_tier:
            working_model.model_tier = capability.tier
        return working_model
    if not capability.model_write_enabled:
        return None
    return new_empty_derived_user_model(tier=capability.tier)


def _merge_counter_items(
    *,
    current_items: List[Dict[str, Any]],
    key_field: str,
    new_values: List[str],
    evidence: List[EvidenceRef],
    seen_at: str,
    limit: int,
) -> List[Dict[str, Any]]:
    merged: Dict[str, Dict[str, Any]] = {}
    for item in current_items:
        if not isinstance(item, dict):
            continue
        key = _clean(item.get(key_field))
        if not key:
            continue
        merged[key] = dict(item)
    for value in new_values:
        key = _clean(value)
        if not key:
            continue
        entry = merged.get(key) or {key_field: key, "count": 0, "evidence": []}
        entry["count"] = int(entry.get("count") or 0) + 1
        entry["last_seen_at"] = seen_at
        entry["evidence"] = list(entry.get("evidence") or []) + [_serialize_evidence_ref(item) for item in evidence[:2]]
        merged[key] = entry
    items = sorted(
        merged.values(),
        key=lambda item: (-int(item.get("count") or 0), _clean(item.get("last_seen_at")), _clean(item.get(key_field))),
        reverse=False,
    )
    items.sort(key=lambda item: (-int(item.get("count") or 0), _clean(item.get(key_field))))
    return items[: max(0, int(limit))]


def _update_value_anchor(value_anchors: List[ValueAnchor], *, key: str, evidence: List[EvidenceRef], seen_at: str) -> List[ValueAnchor]:
    existing = {item.key: deepcopy(item) for item in value_anchors if _clean(item.key)}
    entry = existing.get(key) or ValueAnchor(key=key, confidence=0.0)
    entry.confidence = min(1.0, max(float(entry.confidence), 0.45) + 0.05)
    entry.last_seen_at = seen_at
    entry.evidence = [*entry.evidence, *evidence[:2]][-4:]
    existing[key] = entry
    out = list(existing.values())
    out.sort(key=lambda item: (-float(item.confidence), _clean(item.key)))
    return out


def _merge_topic_anchor(existing: List[TopicAnchor], incoming: TopicAnchor, *, limit: int) -> List[TopicAnchor]:
    by_key = {item.anchor_key: deepcopy(item) for item in existing if _clean(item.anchor_key)}
    cur = by_key.get(incoming.anchor_key)
    if cur is None:
        by_key[incoming.anchor_key] = incoming
    else:
        cur.confidence = max(float(cur.confidence), float(incoming.confidence))
        cur.last_seen_at = incoming.last_seen_at or cur.last_seen_at
        cur.evidence = [*cur.evidence, *incoming.evidence][-4:]
        cur.label = incoming.label or cur.label
        by_key[incoming.anchor_key] = cur
    out = list(by_key.values())
    out.sort(key=lambda item: (-float(item.confidence), _clean(item.anchor_key)))
    return out[: max(0, int(limit))]


def _project_working_user_model(
    *,
    capability: EmlisAICapabilityConfig,
    bundle: SourceBundle,
    world_model: WorldModel,
) -> Optional[DerivedUserModel]:
    working_model = _clone_or_create_working_model(capability=capability, bundle=bundle)
    if working_model is None:
        return None

    current_ref = _current_ref(bundle)
    seen_at = _clean(bundle.current_input.get("created_at")) or _now_iso_z()
    current_categories = [str(v).strip() for v in (bundle.current_input.get("category") or []) if str(v).strip()] if isinstance(bundle.current_input.get("category"), list) else []
    current_emotions = list(world_model.facts.current_emotion_labels)
    dominant = _clean(world_model.facts.dominant_emotion)
    effort_score = float(bundle.input_effort.get("effort_score") or 0.0)
    history_density = float(bundle.memory_richness.get("history_density_score") or 0.0)

    working_model.model_tier = capability.tier
    working_model.updated_at = seen_at
    working_model.debug = dict(working_model.debug or {})
    working_model.debug.update(
        {
            "projected_from_current_input": True,
            "input_effort_score": effort_score,
            "history_density_score": history_density,
        }
    )

    facts = dict(working_model.factual_profile or {})
    facts["frequent_categories"] = _merge_counter_items(
        current_items=list(facts.get("frequent_categories") or []),
        key_field="label",
        new_values=current_categories,
        evidence=[current_ref],
        seen_at=seen_at,
        limit=max(4, capability.max_anchor_count),
    )
    facts["recurrent_emotion_labels"] = _merge_counter_items(
        current_items=list(facts.get("recurrent_emotion_labels") or []),
        key_field="label",
        new_values=current_emotions,
        evidence=[current_ref],
        seen_at=seen_at,
        limit=max(4, capability.max_anchor_count),
    )
    working_model.factual_profile = facts

    pref = working_model.interpretive_frame.response_preference_cues
    pref.prefers_receive_first = pref.prefers_receive_first or dominant in _NEGATIVE_EMOTIONS or not world_model.facts.has_memo_input
    pref.prefers_structure_when_long_memo = pref.prefers_structure_when_long_memo or int(bundle.input_effort.get("memo_char_count") or 0) >= 120
    pref.prefers_continuity_reference = pref.prefers_continuity_reference or bool(bundle.same_day_recent_inputs or bundle.similar_inputs)
    pref.evidence = [*pref.evidence, current_ref][-4:]

    partner = working_model.interpretive_frame.partner_expectation
    partner.wants_continuity = partner.wants_continuity or bool(bundle.same_day_recent_inputs or bundle.similar_inputs)
    partner.wants_non_judgmental_receive = partner.wants_non_judgmental_receive or dominant in _NEGATIVE_EMOTIONS or not world_model.facts.has_memo_input
    partner.wants_precise_observation = partner.wants_precise_observation or (capability.interpretation_mode == "precision_aligned" and history_density >= 0.55)
    partner.evidence = [*partner.evidence, current_ref][-4:]

    for category in current_categories:
        working_model.interpretive_frame.value_anchors = _update_value_anchor(
            working_model.interpretive_frame.value_anchors,
            key=f"category:{category}",
            evidence=[current_ref],
            seen_at=seen_at,
        )

    if capability.interpretation_mode != "current_only" and dominant:
        existing_entries = {item.trigger: deepcopy(item) for item in working_model.interpretive_frame.meaning_map if _clean(item.trigger)}
        for trigger in current_categories or current_emotions[:1]:
            key = _clean(trigger)
            if not key:
                continue
            entry = existing_entries.get(key)
            if entry is None:
                from emlis_ai_types import MeaningMapEntry  # local import to keep module import light

                entry = MeaningMapEntry(trigger=key, likely_meaning=dominant, confidence=0.48)
            if entry.likely_meaning == dominant:
                entry.confidence = min(1.0, max(float(entry.confidence), 0.48) + 0.06)
            else:
                entry.confidence = max(float(entry.confidence), 0.44)
            entry.last_seen_at = seen_at
            entry.evidence = [*entry.evidence, current_ref][-4:]
            existing_entries[key] = entry
        meaning_entries = list(existing_entries.values())
        meaning_entries.sort(key=lambda item: (-float(item.confidence), _clean(item.trigger)))
        working_model.interpretive_frame.meaning_map = meaning_entries[: max(0, int(capability.max_anchor_count or 0))]

    all_inputs = [*bundle.same_day_recent_inputs, *bundle.similar_inputs, bundle.current_input]
    for anchor_payload in build_open_topic_anchor_candidates(all_inputs, topn=max(1, int(capability.max_anchor_count or 1))):
        incoming = TopicAnchor(
            anchor_key=_clean(anchor_payload.get("anchor_key")) or "anchor:unknown",
            label=_clean(anchor_payload.get("label")) or "topic",
            confidence=min(1.0, float(anchor_payload.get("count") or 1) / 4.0),
            evidence=[current_ref],
            last_seen_at=_clean(anchor_payload.get("last_seen_at")) or seen_at,
        )
        working_model.open_topic_anchors = _merge_topic_anchor(
            working_model.open_topic_anchors,
            incoming,
            limit=max(0, int(capability.max_anchor_count or 0)),
        )

    if any(item.key == "recovery_signal" for item in world_model.hypotheses):
        incoming = TopicAnchor(
            anchor_key=f"recovery:{dominant or 'emotion'}",
            label=dominant or "回復",
            confidence=0.58,
            evidence=[current_ref],
            last_seen_at=seen_at,
        )
        working_model.recovery_anchors = _merge_topic_anchor(
            working_model.recovery_anchors,
            incoming,
            limit=max(0, int(capability.max_anchor_count or 0)),
        )

    derived_hypotheses: List[DerivedModelHypothesis] = []
    for item in world_model.hypotheses[: max(0, int(capability.max_hypothesis_count or 0))]:
        derived_hypotheses.append(
            DerivedModelHypothesis(
                key=item.key,
                text=item.text,
                confidence=float(item.confidence),
                evidence=list(item.evidence),
                status="active",
                last_seen_at=seen_at,
            )
        )
    working_model.hypotheses = derived_hypotheses

    working_model.source_cursor.last_emotion_id = _clean(bundle.current_input.get("id")) or working_model.source_cursor.last_emotion_id
    working_model.source_cursor.last_emotion_created_at = seen_at or working_model.source_cursor.last_emotion_created_at
    latest_tq_id = _clean(bundle.latest_today_question_answer.get("id"))
    if latest_tq_id:
        working_model.source_cursor.last_today_question_answer_id = latest_tq_id
    return working_model


def _render_comment_text_from_reply_lines(reply_lines: List[ReplyLine], *, greeting_text: str = "") -> str:
    normalized = [_naturalize_reply_line(greeting_text)] if str(greeting_text or "").strip() else []
    normalized.extend(_naturalize_reply_line(line.text) for line in reply_lines if str(line.text or "").strip())
    return "\n".join(line for line in normalized if line).strip()


def _build_reply_plan_from_decision(decision) -> ReplyPlan:
    reply_lines = list(decision.reply_lines)
    used_evidence = _collect_used_evidence(reply_lines)
    receive = next((line.text for line in reply_lines if line.key == "receive"), "")
    continuity = next((line.text for line in reply_lines if line.key in {"interpretation", "continuity", "topic_anchor"}), "")
    change = next((line.text for line in reply_lines if line.key in {"change", "recovery"}), "")
    partner_line = next((line.text for line in reply_lines if line.key == "partner_line"), "")
    return ReplyPlan(
        receive=receive,
        continuity=continuity,
        change=change,
        partner_line=partner_line,
        reply_lines=reply_lines,
        used_evidence=used_evidence,
        rejected_candidates=list(decision.rejected_candidates),
        reply_length_plan=decision.reply_length_plan,
        notes={
            "unknowns": list(decision.unknowns),
            "conflicts": list(decision.conflicts),
            **dict(decision.debug or {}),
        },
    )


async def _persist_working_user_model_best_effort(
    *,
    user_id: str,
    capability: EmlisAICapabilityConfig,
    working_model: Optional[DerivedUserModel],
) -> None:
    if not capability.model_write_enabled or working_model is None:
        return None
    try:
        await save_emlis_ai_user_model_for_user(user_id=user_id, model=working_model)
    except Exception:
        return None


def _understanding_meta(world_model: WorldModel, plan: ReplyPlan) -> Dict[str, Any]:
    frame = getattr(world_model.facts, "understanding_frame", None)
    patterns = list(getattr(world_model.facts, "understanding_patterns", []) or [])
    role_fields = (
        "event",
        "action",
        "relationship_or_other",
        "boundary_violation",
        "self_awareness",
        "self_fault_awareness",
        "self_avoidance",
        "justification",
        "fear_of_rejection",
        "self_dislike",
        "guilt_or_remorse",
        "explicit_emotion",
        "need_or_wish",
        "unresolved",
        "work_frustration",
        "mentor_attachment",
        "missing_guidance",
        "effort_confusion",
        "anger_surface",
        "sadness_surface",
        "relief_source",
        "chat_relief",
        "fatigue_accumulation",
    )
    roles_used: List[str] = []
    if frame is not None:
        for field_name in role_fields:
            anchor = getattr(frame, field_name, None)
            role = _clean(getattr(anchor, "role", "")) if anchor is not None else ""
            if role and role not in roles_used:
                roles_used.append(role)
    understanding_line_count = sum(
        1
        for line in list(plan.reply_lines or [])
        if line.key == "receive" or str(line.candidate_key or "").startswith("word_reflection.") or line.key == "selected_emotions"
    )
    return {
        "frame_version": "understanding_frame.v1",
        "patterns": patterns,
        "anchor_roles_used": roles_used,
        "understanding_line_count": understanding_line_count,
        "confidence": float(getattr(frame, "confidence", 0.0) or 0.0),
    }


def _build_meta(
    *,
    capability: EmlisAICapabilityConfig,
    bundle: SourceBundle,
    world_model: WorldModel,
    plan: ReplyPlan,
    fallback_used: bool,
    working_model: Optional[DerivedUserModel],
) -> Dict[str, Any]:
    used_sources: List[str] = ["current_input"]
    used_memory_layers: List[str] = ["canonical_history"]
    if capability.history_mode != "none" and (bundle.last_input or bundle.same_day_recent_inputs or bundle.similar_inputs):
        used_sources.append("history")
    if capability.include_input_summary:
        used_sources.append("input_summary")
    if capability.include_myweb_summary:
        used_sources.append("myweb_home_summary")
    if capability.include_today_question_history:
        used_sources.append("today_question")
    if bundle.greeting:
        used_sources.append("greeting_state")
    if bundle.derived_user_model is not None:
        used_sources.append("derived_user_model")
        used_memory_layers.append("derived_user_model")
    if bundle.side_state:
        used_memory_layers.append("side_state")
    matched_cross_core_context = list(getattr(world_model.facts, "cross_core_context", []) or [])
    if capability.cross_core_enabled and matched_cross_core_context:
        if "cross_core_context" not in used_memory_layers:
            used_memory_layers.append("cross_core_context")
        for packet in matched_cross_core_context:
            source_key = _cross_core_source_key(getattr(packet, "source_kind", ""))
            if source_key and source_key not in used_sources:
                used_sources.append(source_key)

    evidence_by_line: Dict[str, Any] = {}
    for line in plan.reply_lines:
        if not line.sentence_evidence.evidence:
            continue
        evidence_key = line.key
        if evidence_key in evidence_by_line:
            evidence_key = line.candidate_key or f"{line.key}:{len(evidence_by_line)}"
        evidence_by_line[evidence_key] = [_serialize_evidence_ref(item) for item in line.sentence_evidence.evidence]

    selected_emotions = [_serialize_emotion_display_item(item) for item in list(world_model.facts.selected_emotions or [])]
    dominant_emotion = next((item for item in selected_emotions if item.get("role") == "dominant"), None)
    secondary_emotions = [item for item in selected_emotions if item.get("role") != "dominant"]
    user_word_anchors = list(world_model.facts.user_word_anchors or [])
    shaped_user_phrases = list(getattr(world_model.facts, "shaped_user_phrases", []) or [])
    used_anchor_keys = {
        _clean((line.candidate_key or "").replace("word_reflection.", ""))
        for line in plan.reply_lines
        if line.key == "word_reflection"
    }

    return {
        "version": "emlis_ai_v2",
        "kernel_version": "observation_kernel.v2",
        "tier": capability.tier,
        "capability": {
            "history_mode": capability.history_mode,
            "continuity_mode": capability.continuity_mode,
            "style_mode": capability.style_mode,
            "partner_mode": capability.partner_mode,
            "model_mode": capability.model_mode,
            "interpretation_mode": capability.interpretation_mode,
            "source_scope": capability.source_scope,
            "cross_core_enabled": bool(capability.cross_core_enabled),
            "structure_model_enabled": bool(capability.structure_model_enabled),
        },
        "display": {
            "display_name_call": display_name_call(bundle.display_name),
            "selected_emotions": selected_emotions,
            "dominant_emotion": dominant_emotion,
            "secondary_emotions": secondary_emotions,
        },
        "reply_depth": _reply_depth_meta(plan, capability),
        "anchor_summary": {
            "user_word_anchor_count": len(user_word_anchors),
            "used_user_word_anchor_count": sum(1 for line in plan.reply_lines if line.key == "word_reflection"),
            "sample_user_word_anchors": [_serialize_user_word_anchor(item) for item in user_word_anchors[:8]],
            "used_anchor_keys": sorted(v for v in used_anchor_keys if v),
        },
        "phrase_shaping": {
            "version": "emlis.phrase_shaping.v1",
            "raw_anchor_count": len(user_word_anchors),
            "safe_phrase_count": sum(1 for item in shaped_user_phrases if _clean(getattr(item, "usability", "safe")) in {"safe", "needs_context"}),
            "unsafe_phrase_count": sum(1 for item in shaped_user_phrases if _clean(getattr(item, "usability", "safe")) == "unsafe"),
            "sample_shaped_phrases": [_serialize_shaped_user_phrase(item) for item in shaped_user_phrases[:8]],
            "unsafe_reasons": sorted({reason for item in shaped_user_phrases for reason in list(getattr(item, "unsafe_reasons", []) or []) if str(reason)}),
        },
        "meaning_coverage": _meaning_coverage_meta(world_model, plan),
        "whole_input_meaning_arc": _serialize_whole_input_arc(getattr(world_model.facts, "whole_input_meaning_arc", None)),
        "major_meaning_retention": _serialize_major_retention(getattr(world_model.facts, "major_meaning_retention_plan", None)),
        "value_observation": _value_observation_meta(world_model),
        "emlis_observation_frame": _serialize_observation_frame(getattr(world_model.facts, "emlis_observation_frame", None)),
        "composition": _composition_meta(world_model),
        "understanding": _understanding_meta(world_model, plan),
        "cross_core_context": _cross_core_context_meta(world_model),
        "used_sources": used_sources,
        "used_memory_layers": used_memory_layers,
        "reply_length_mode": plan.reply_length_plan.mode if plan.reply_length_plan else capability.reply_length_mode,
        "evidence_count": len(plan.used_evidence),
        "evidence_by_line": evidence_by_line,
        "rejected_candidate_count": len(plan.rejected_candidates),
        "fallback_used": fallback_used,
        "model_revision": working_model.updated_at if working_model is not None else None,
        "world_model_debug": {
            **dict(world_model.debug or {}),
            "unknown_count": len(world_model.unknowns),
            "conflict_count": len(world_model.conflicts),
        },
    }


def _final_review_meta(review: Any, *, repair_applied: bool) -> Dict[str, Any]:
    return {
        "version": _clean(getattr(review, "review_version", "emlis.final_reader.v1")) or "emlis.final_reader.v1",
        "passed": bool(getattr(review, "passed", False)),
        "repair_applied": bool(repair_applied),
        "issues": [
            {
                "code": _clean(getattr(issue, "code", "")),
                "severity": _clean(getattr(issue, "severity", "")),
                "line_index": getattr(issue, "line_index", None),
                "message": _clean(getattr(issue, "message", ""))[:160],
            }
            for issue in list(getattr(review, "issues", []) or [])
        ],
    }


def _issue_codes_from_review(review: Any) -> List[str]:
    return [
        _clean(getattr(issue, "code", ""))
        for issue in list(getattr(review, "issues", []) or [])
        if _clean(getattr(issue, "code", ""))
    ]


def _evaluate_pre_return_gate(
    *,
    comment_text: str,
    capability: EmlisAICapabilityConfig,
    meta: Dict[str, Any],
    fallback_used: bool,
    final_reader_passed: bool,
    repair_attempted: bool = False,
    repair_passed: bool = False,
    safe_fallback_used: bool = False,
    blocked_issue_codes: Optional[List[str]] = None,
):
    reply_depth = meta.get("reply_depth") if isinstance(meta.get("reply_depth"), dict) else {}
    anchor_summary = meta.get("anchor_summary") if isinstance(meta.get("anchor_summary"), dict) else {}
    understanding = meta.get("understanding") if isinstance(meta.get("understanding"), dict) else {}
    meaning_coverage = meta.get("meaning_coverage") if isinstance(meta.get("meaning_coverage"), dict) else {}
    composition = meta.get("composition") if isinstance(meta.get("composition"), dict) else {}
    allowed_line_count = int(reply_depth.get("tier_ceiling") or getattr(capability, "max_reply_lines", 3) or 3) + 1
    return evaluate_emlis_ai_quality_gate(
        comment_text=comment_text,
        capability=capability,
        used_sources=meta.get("used_sources") if isinstance(meta.get("used_sources"), list) else [],
        evidence_by_line=meta.get("evidence_by_line") if isinstance(meta.get("evidence_by_line"), dict) else {},
        fallback_used=fallback_used,
        allowed_line_count=allowed_line_count,
        sample_user_word_anchors=anchor_summary.get("sample_user_word_anchors") if isinstance(anchor_summary.get("sample_user_word_anchors"), list) else [],
        user_word_anchor_count=int(anchor_summary.get("user_word_anchor_count") or 0),
        understanding_patterns=understanding.get("patterns") if isinstance(understanding.get("patterns"), list) else [],
        final_reader_passed=final_reader_passed,
        pre_return_blocking_enabled=True,
        repair_attempted=repair_attempted,
        repair_passed=repair_passed,
        safe_fallback_used=safe_fallback_used,
        blocked_issue_codes=blocked_issue_codes or [],
        meaning_coverage=meaning_coverage,
        composition=composition,
    )



def _jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(v) for v in value]
    return value


def _composer_core_generation_meta(composer_candidate: Any) -> Dict[str, Any]:
    meta = getattr(composer_candidate, "composer_meta", {}) or {}
    if not isinstance(meta, dict):
        return {}
    core_meta = meta.get("text_generation_core") or meta.get("core_text_generation")
    return dict(core_meta or {}) if isinstance(core_meta, dict) else {}


def _as_meta_dict(value: Any) -> Dict[str, Any]:
    as_meta = getattr(value, "as_meta", None)
    if callable(as_meta):
        try:
            payload = as_meta()
            if isinstance(payload, dict):
                return dict(payload)
        except Exception:
            return {}
    return dict(value) if isinstance(value, dict) else {}


def _step10_runtime_scope_blocked(meta: Mapping[str, Any], reasons: List[str]) -> bool:
    reason_code = str(meta.get("reason_code") or "").strip()
    return bool(
        str(meta.get("connection_status") or "").strip() == "blocked_scope"
        or str(meta.get("pre_connection_stop_stage") or "").strip() == "scope"
        or str(meta.get("cohort") or "").strip() == "blocked_scope"
        or reason_code.startswith("scope_")
        or "limited_composer_scope_not_allowed" in reasons
        or any(str(reason or "").startswith("scope_") for reason in reasons)
    )


def _step10_repair_runtime_block_reason(
    *,
    composer_client_resolution: Any = None,
    limited_release_decision: Any = None,
) -> str:
    """Return the reply-service runtime block that Step10 repair must not override.

    This is a second guard behind the repair integration helper.  It only closes
    Phase7 rollout / pre-connection rollout stops; ordinary unavailable paths
    and feature-flag-disabled paths still flow to the repair integration, where
    the low-information eligibility check decides whether they may be repaired.
    """

    resolution_meta = _as_meta_dict(composer_client_resolution)
    release_meta = _as_meta_dict(limited_release_decision)
    gate_metas: List[Dict[str, Any]] = []
    for key in ("release_gate", "phase7_rollout_gate"):
        gate = resolution_meta.get(key)
        if isinstance(gate, Mapping):
            gate_metas.append(dict(gate))

    resolution_reasons = _dedupe_reason_codes(resolution_meta.get("rejection_reasons") or [])
    release_reasons = _dedupe_reason_codes(release_meta.get("rejection_reasons") or [])
    gate_reasons: List[str] = []
    for gate_meta in gate_metas:
        gate_reasons.extend(_dedupe_reason_codes(gate_meta.get("rejection_reasons") or []))
    reasons = _dedupe_reason_codes([*resolution_reasons, *release_reasons, *gate_reasons])

    if (
        _step10_runtime_scope_blocked(resolution_meta, resolution_reasons)
        or _step10_runtime_scope_blocked(release_meta, release_reasons)
        or any(
            _step10_runtime_scope_blocked(
                gate_meta,
                _dedupe_reason_codes(gate_meta.get("rejection_reasons") or []),
            )
            for gate_meta in gate_metas
        )
    ):
        return ""

    connection_status = str(resolution_meta.get("connection_status") or "").strip()
    stop_stage = str(resolution_meta.get("pre_connection_stop_stage") or "").strip()
    reason_codes = _dedupe_reason_codes(
        [
            release_meta.get("reason_code"),
            *(gate_meta.get("reason_code") for gate_meta in gate_metas),
        ]
    )

    if connection_status == "blocked_rollout" or stop_stage == "rollout":
        return "step10_blocked_by_phase7_rollout"
    if set(reasons).intersection(_STEP10_PHASE7_ROLLOUT_REJECTION_REASONS):
        return "step10_blocked_by_phase7_rollout"
    if set(reason_codes).intersection(_STEP10_PHASE7_ROLLOUT_REASON_CODES):
        return "step10_blocked_by_phase7_rollout"
    return ""


def _candidate_meta_value(composer_candidate: Any, key: str, default: Any = "") -> Any:
    if isinstance(composer_candidate, dict):
        return composer_candidate.get(key, default)
    return getattr(composer_candidate, key, default)


def _composer_candidate_meta_dict(composer_candidate: Any) -> Dict[str, Any]:
    meta = _candidate_meta_value(composer_candidate, "composer_meta", {})
    return dict(meta or {}) if isinstance(meta, dict) else {}


_TWO_STAGE_GATE_REQUIREMENT_KEYS = (
    "two_stage_reception_gate_required",
    "state_answer_two_stage_display_required",
    "state_answer_two_stage_reception_surface_required",
    "state_answer_joined_comment_text_required",
    "state_answer_section_labels_required",
    "state_answer_expected_comment_text_shape",
)


def _legacy_text_candidate_without_two_stage_surface(meta: Mapping[str, Any] | None) -> bool:
    source = dict(meta or {}) if isinstance(meta, Mapping) else {}
    if source.get("two_stage_surface_realization") or source.get("complete_composer"):
        return False
    model = str(source.get("composer_model") or source.get("model") or "").strip().lower()
    method = str(source.get("generation_method") or source.get("composer_method") or "").strip().lower()
    composer_source = str(source.get("composer_source") or "").strip().lower()
    if model == "cocolon.complete_composer.initial.v1" or method == "complete_composer_initial":
        return False
    if bool(source.get("limited_composer")):
        return True
    if method in {"test_composer", "step10_e2e_test_composer"}:
        return True
    if "text_composer" in model or "textcomposer" in model or "legacy_text" in model:
        return True
    if "text_composer" in method or "legacy_text" in method:
        return True
    if composer_source in {"legacy_text_composer", "text_composer"}:
        return True
    return False


def _without_unrealized_limited_two_stage_gate_requirement(meta: Mapping[str, Any] | None) -> Dict[str, Any]:
    """Return gate context for legacy one-stage candidates.

    Phase16/17 labelled two-stage rendering is owned by CompleteComposerClient.
    Older limited / test / legacy text composers may still carry state-answer
    role-plan material for diagnostics, but their one-stage surface must not be
    terminally blocked by stale labelled two-stage requirement meta.  This does
    not relax any Gate; it only removes an inapplicable TwoStage-required flag
    from the gate input for legacy one-stage candidate families.
    """

    source = dict(meta or {}) if isinstance(meta, Mapping) else {}
    if not _legacy_text_candidate_without_two_stage_surface(source):
        return source

    out = dict(source)
    for key in _TWO_STAGE_GATE_REQUIREMENT_KEYS:
        out.pop(key, None)

    for container_key in ("state_answer_composer_role_plan", "composition_contract", "composer_payload", "payload"):
        container = out.get(container_key)
        if not isinstance(container, Mapping):
            continue
        patched = dict(container)
        for key in (
            "two_stage_display_required",
            "two_stage_reception_surface_required",
            "joined_comment_text_required",
            "section_labels_required",
            "expected_comment_text_shape",
        ):
            patched.pop(key, None)
        out[container_key] = patched

    out["legacy_text_composer_two_stage_gate_context_suppressed"] = True
    out["limited_composer_two_stage_gate_context_suppressed"] = bool(source.get("limited_composer"))
    out["limited_composer_two_stage_surface_realization_connected"] = False
    return out


def _runtime_surface_composer_meta_for_candidate(composer_candidate: Any, composer_source: str = "") -> Dict[str, Any]:
    """Build meta-only composer context for the runtime surface pre-return gate."""

    out: Dict[str, Any] = dict(_composer_candidate_meta_dict(composer_candidate))
    for attr in ("composer_model", "generation_method", "generation_scope", "coverage_scope", "status"):
        value = getattr(composer_candidate, attr, None) if composer_candidate is not None else None
        if value is not None and str(value or "").strip():
            out.setdefault(attr, value)
    out.setdefault("composer_source", composer_source or getattr(composer_candidate, "composer_source", "") if composer_candidate is not None else composer_source)
    out = _without_unrealized_limited_two_stage_gate_requirement(out)
    coverage_scope = str(out.get("coverage_scope") or out.get("generation_scope") or "").strip()
    profile_key = str(out.get("profile_key") or out.get("composer_profile_key") or "").strip()
    if coverage_scope == "current_input_core" or profile_key == "current_input_core":
        out.setdefault("shallow_observation_path", True)
    return out


def _runtime_surface_phrase_unit_grammar_meta(composer_meta: Mapping[str, Any] | None) -> Dict[str, Any]:
    meta = dict(composer_meta or {}) if isinstance(composer_meta, Mapping) else {}
    for key in (
        "phrase_unit_grammar_normalizer",
        "phrase_unit_grammar_normalizer_report",
        "phrase_unit_grammar",
        "phrase_unit_grammar_summary",
    ):
        value = meta.get(key)
        if isinstance(value, Mapping):
            return dict(value)
    return meta


def _runtime_surface_signature_meta(composer_meta: Mapping[str, Any] | None) -> Dict[str, Any]:
    meta = dict(composer_meta or {}) if isinstance(composer_meta, Mapping) else {}
    for key in ("surface_quality_signature", "step2_surface_quality_signature", "surface_signature"):
        value = meta.get(key)
        if isinstance(value, Mapping):
            return dict(value)
    return {}


def _build_runtime_surface_pre_return_report_for_candidate(
    *,
    comment_text: str,
    composer_candidate: Any,
    composer_source: str,
    rerender_attempted: bool = False,
) -> Dict[str, Any]:
    composer_meta = _runtime_surface_composer_meta_for_candidate(composer_candidate, composer_source=composer_source)
    return build_runtime_surface_pre_return_gate_report(
        comment_text=comment_text,
        composer_meta=composer_meta,
        surface_quality_signature=_runtime_surface_signature_meta(composer_meta),
        phrase_unit_grammar_meta=_runtime_surface_phrase_unit_grammar_meta(composer_meta),
        rerender_allowed=True,
        rerender_attempted=bool(rerender_attempted),
        rerender_attempt_limit=1,
        low_information_reroute_allowed=False,
    )


def _visible_surface_current_text(current_input: Mapping[str, Any] | None) -> str:
    current = current_input if isinstance(current_input, Mapping) else {}
    for key in ("memo", "memo_text", "text", "input_text", "body"):
        value = str(current.get(key) or "").strip()
        if value:
            return value
    return ""


_PHASE19_LOW_INFORMATION_SENTENCE_SPLIT_RE = re.compile(r"[。！？!?]+")
_PHASE19_LOW_INFORMATION_STATE_SIGNAL_RE = re.compile(
    r"(だる|何もしたくない|疲|つかれ|しんど|つら|辛|きつ|無理|不安|悲し|怖|こわ|焦|重い|重さ|消耗)",
    re.IGNORECASE,
)
_PHASE19_LOW_INFORMATION_SAFETY_ADJACENT_RE = re.compile(
    r"(自分を傷つけ|傷つけてるのは私|死にたい|消えたい|自傷|自殺|殺したい|絶対にない)",
    re.IGNORECASE,
)


def _phase19_compact_low_information_sentence_count(text: str) -> int:
    return len([part for part in (_clean(part) for part in _PHASE19_LOW_INFORMATION_SENTENCE_SPLIT_RE.split(text)) if part])


def _phase19_current_input_action_text(current_input: Mapping[str, Any] | None) -> str:
    current = current_input if isinstance(current_input, Mapping) else {}
    for key in ("memo_action", "action_text", "action", "memoAction"):
        value = str(current.get(key) or "").strip()
        if value:
            return value
    return ""


def _phase19_safety_blocked_for_low_information_repair(
    *,
    safety_requires_block: bool = False,
    safety_report: Any = None,
    display_decision: Any = None,
) -> bool:
    if bool(safety_requires_block):
        return True
    if safety_report is not None and bool(getattr(safety_report, "requires_block", False)):
        return True
    if str(getattr(display_decision, "observation_status", "") or "") == "safety_blocked":
        return True
    reasons = _dedupe_reason_codes(getattr(display_decision, "rejection_reasons", []) if display_decision is not None else [])
    return any("safety" in reason or "self_harm" in reason or "harm" in reason for reason in reasons)


def _phase19_complete_initial_low_information_repair_ownership_meta(
    *,
    complete_initial_default_requested: bool,
    current_input: Mapping[str, Any] | None,
    safety_requires_block: bool,
    safety_report: Any = None,
    display_decision: Any = None,
) -> Dict[str, Any]:
    """Return internal Phase19-2 ownership meta for compact low-info repair."""

    current = current_input if isinstance(current_input, Mapping) else {}
    memo_text = _visible_surface_current_text(current)
    memo_action = _phase19_current_input_action_text(current)
    sentence_count = _phase19_compact_low_information_sentence_count(memo_text)
    safety_blocked = _phase19_safety_blocked_for_low_information_repair(
        safety_requires_block=safety_requires_block,
        safety_report=safety_report,
        display_decision=display_decision,
    )
    self_harm_adjacent = bool(_PHASE19_LOW_INFORMATION_SAFETY_ADJACENT_RE.search(memo_text))
    compact_signal = bool(memo_text and len(memo_text) <= 48 and sentence_count <= 2 and not memo_action)
    state_signal = bool(_PHASE19_LOW_INFORMATION_STATE_SIGNAL_RE.search(memo_text))
    has_specific_long_form_observation_material = bool(memo_action or len(memo_text) > 48 or sentence_count > 2)
    repair_allowed = bool(
        complete_initial_default_requested
        and compact_signal
        and state_signal
        and not has_specific_long_form_observation_material
        and not safety_blocked
        and not self_harm_adjacent
    )
    repair_block_reason = "" if repair_allowed else "complete_initial_runtime_contract_owns_display_failure"
    return {
        "schema_version": "cocolon.emlis.phase19.complete_initial_low_information_repair_ownership.v1",
        "source_phase": "Phase19-2_A_low_information_repair_ownership",
        "complete_initial_default_requested": bool(complete_initial_default_requested),
        "low_information_compact_signal_detected": bool(compact_signal),
        "low_information_state_signal_detected": bool(state_signal),
        "has_specific_long_form_observation_material": bool(has_specific_long_form_observation_material),
        "repair_allowed_under_complete_initial": bool(repair_allowed),
        "repair_block_reason": repair_block_reason or None,
        "safety_blocked": bool(safety_blocked),
        "self_harm_adjacent_signal_detected": bool(self_harm_adjacent),
        "public_contract_changed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "safety_gate_relaxed": False,
        "fixed_fallback_used": False,
        "raw_input_included": False,
        "reason": "compact_low_information_state_signal" if repair_allowed else repair_block_reason,
    }


def _build_visible_surface_acceptance_report_for_candidate(
    *,
    comment_text: str,
    current_input: Mapping[str, Any] | None,
    composer_candidate: Any = None,
    composer_source: str = "",
    composer_meta: Mapping[str, Any] | None = None,
    rerender_attempted: bool = False,
) -> Dict[str, Any]:
    """Build the Step4 visible-surface gate report for a public candidate.

    The candidate text and current input are used only in memory.  The returned
    report is the Step3 meta-only shape, so it can be attached to internal gate
    traces without leaking raw text or changing RN/API/DB contracts.
    """

    current = current_input if isinstance(current_input, Mapping) else {}
    candidate_meta = (
        dict(composer_meta or {})
        if isinstance(composer_meta, Mapping)
        else _runtime_surface_composer_meta_for_candidate(composer_candidate, composer_source=composer_source)
        if composer_candidate is not None
        else {}
    )
    return build_visible_surface_acceptance_gate_report(
        comment_text=comment_text,
        current_input=current,
        current_text=_visible_surface_current_text(current),
        composer_meta=candidate_meta,
        rerender_allowed=True,
        rerender_attempted=bool(rerender_attempted),
        low_information_reroute_allowed=False,
    )


def _step3_int(value: Any, default: int = 0) -> int:
    try:
        if isinstance(value, bool):
            return int(value)
        return int(value)
    except Exception:
        return default


def _build_observation_diagnostic_lockdown_reply_meta(
    *,
    trace_id: str,
    display_decision: Any,
    composer_candidate: Any,
    diagnostic_summary: Dict[str, Any],
    complete_reply_diagnostics: Dict[str, Any],
    complete_scorecard_event: Dict[str, Any],
    complete_repair_trace: List[Any],
) -> Dict[str, Any]:
    """Build Step3 additive reply meta for submit-level diagnostics.

    This meta intentionally contains only ids, counts, booleans, status values,
    and reason codes.  It does not add public response keys, does not relax any
    gate, and does not copy raw input or public comment text.
    """

    candidate_meta = _composer_candidate_meta_dict(composer_candidate)
    runtime_meta = dict(
        complete_reply_diagnostics.get("complete_runtime_meta")
        or complete_reply_diagnostics.get("complete_composer_initial_meta")
        or complete_reply_diagnostics.get("complete_composer_meta")
        or {}
    ) if isinstance(complete_reply_diagnostics, dict) else {}
    self_repair = dict(complete_reply_diagnostics.get("self_repair") or {}) if isinstance(complete_reply_diagnostics.get("self_repair"), dict) else {}
    limited_reader_repair_diagnostic = (
        dict(complete_reply_diagnostics.get("limited_reader_repair_diagnostic") or {})
        if isinstance(complete_reply_diagnostics.get("limited_reader_repair_diagnostic"), dict)
        else {}
    )
    limited_reader_repair = (
        dict(complete_reply_diagnostics.get("limited_reader_repair") or {})
        if isinstance(complete_reply_diagnostics.get("limited_reader_repair"), dict)
        else dict(limited_reader_repair_diagnostic.get("limited_reader_repair") or {})
        if isinstance(limited_reader_repair_diagnostic.get("limited_reader_repair"), dict)
        else {}
    )
    display_rejection_reasons = _dedupe_reason_codes(getattr(display_decision, "rejection_reasons", []) or [])
    composer_status = str(
        _candidate_meta_value(composer_candidate, "status", "")
        or complete_reply_diagnostics.get("composer_status")
        or complete_scorecard_event.get("composer_status")
        or diagnostic_summary.get("composer_status")
        or ""
    )
    composer_source = str(
        _candidate_meta_value(composer_candidate, "composer_source", "")
        or complete_reply_diagnostics.get("composer_source")
        or complete_scorecard_event.get("composer_source")
        or diagnostic_summary.get("composer_source")
        or ""
    )
    candidate_generated = bool(
        complete_reply_diagnostics.get("complete_candidate_generated")
        or complete_scorecard_event.get("complete_candidate_generated")
        or (composer_status == "generated" and composer_source == "ai_generated")
    )
    candidate_seen = bool(
        complete_reply_diagnostics.get("complete_candidate_seen")
        or complete_scorecard_event.get("complete_candidate_seen")
        or composer_status
        or candidate_generated
    )
    candidate_displayed = bool(
        complete_reply_diagnostics.get("complete_candidate_displayed")
        or complete_scorecard_event.get("complete_candidate_displayed")
        or (str(getattr(display_decision, "observation_status", "") or "") == "passed" and candidate_seen)
    )
    used_evidence_span_ids = _dedupe_reason_codes(
        _candidate_meta_value(composer_candidate, "used_evidence_span_ids", [])
        or candidate_meta.get("used_evidence_span_ids")
        or runtime_meta.get("used_evidence_span_ids")
    )
    used_phrase_unit_ids = _dedupe_reason_codes(
        candidate_meta.get("used_phrase_unit_ids")
        or runtime_meta.get("used_phrase_unit_ids")
        or complete_reply_diagnostics.get("used_phrase_unit_ids")
        or complete_scorecard_event.get("used_phrase_unit_ids")
    )
    relation_types = _dedupe_reason_codes(
        _candidate_meta_value(composer_candidate, "used_relation_ids", [])
        or candidate_meta.get("used_relation_ids")
        or candidate_meta.get("relation_types")
        or runtime_meta.get("used_relation_ids")
        or runtime_meta.get("relation_types")
        or complete_reply_diagnostics.get("relation_types")
        or complete_scorecard_event.get("relation_types")
    )
    repair_trace_count = _step3_int(
        complete_reply_diagnostics.get("repair_trace_count"),
        len(complete_repair_trace or []),
    )
    repair_aborted_count = _step3_int(
        complete_reply_diagnostics.get("repair_aborted_count")
        or self_repair.get("repair_aborted_count")
        or self_repair.get("aborted_count"),
        0,
    )
    repair_abort_reasons = _dedupe_reason_codes(
        complete_reply_diagnostics.get("repair_abort_reasons")
        or self_repair.get("repair_abort_reasons")
        or self_repair.get("abort_reasons")
    )
    limited_repair_attempted = bool(limited_reader_repair_diagnostic.get("attempted") or limited_reader_repair.get("attempted"))
    limited_repair_applied = bool(limited_reader_repair_diagnostic.get("applied") or limited_reader_repair.get("applied"))
    repair_attempted = bool(
        complete_reply_diagnostics.get("repair_attempted")
        or repair_trace_count
        or self_repair.get("repair_attempted")
        or self_repair.get("attempted")
        or limited_repair_attempted
    )
    self_repair_status = str(
        self_repair.get("status")
        or ("aborted" if repair_aborted_count else "limited_reader_repair_applied" if limited_repair_applied else "limited_reader_repair_attempted" if limited_repair_attempted else "attempted" if repair_attempted else "not_attempted")
    )

    return {
        "version": _OBSERVATION_DIAGNOSTIC_LOCKDOWN_REPLY_META_VERSION,
        "ready": True,
        "source": "reply_meta_step3",
        "trace_id": str(trace_id or ""),
        "observation_status": str(getattr(display_decision, "observation_status", "") or ""),
        "comment_text_length": len(str(getattr(display_decision, "comment_text", "") or "").strip()),
        "candidate_seen": candidate_seen,
        "candidate_generated": candidate_generated,
        "candidate_generated_before_display_gate": candidate_generated,
        "candidate_displayed": candidate_displayed,
        "candidate_status": composer_status,
        "candidate_source": composer_source,
        "composer_status": composer_status,
        "composer_source": composer_source,
        "display_rejection_reasons": display_rejection_reasons,
        "used_evidence_span_count": len(used_evidence_span_ids),
        "used_phrase_unit_count": len(used_phrase_unit_ids),
        "used_relation_count": len(relation_types),
        "used_phrase_unit_ids": used_phrase_unit_ids,
        "relation_types": relation_types,
        "limited_reader_repair": limited_reader_repair,
        "limited_reader_repair_attempted": bool(limited_reader_repair_diagnostic.get("attempted") or limited_reader_repair.get("attempted")),
        "limited_reader_repair_applied": bool(limited_reader_repair_diagnostic.get("applied") or limited_reader_repair.get("applied")),
        "limited_reader_repair_operations": _dedupe_reason_codes(limited_reader_repair_diagnostic.get("operations") or limited_reader_repair.get("operations") or []),
        "limited_reader_repair_relation_marker_key": str(limited_reader_repair_diagnostic.get("relation_marker_key") or limited_reader_repair.get("relation_marker_key") or ""),
        "limited_reader_repair_relation_marker_signal_keys": _dedupe_reason_codes(limited_reader_repair_diagnostic.get("relation_marker_signal_keys") or limited_reader_repair.get("relation_marker_signal_keys") or []),
        "limited_reader_repair_relation_type": str(limited_reader_repair_diagnostic.get("relation_type") or limited_reader_repair.get("relation_type") or ""),
        "limited_reader_repair_meaning_added": bool(limited_reader_repair_diagnostic.get("meaning_added") or limited_reader_repair.get("meaning_added")),
        "limited_reader_repair_gate_relaxed": bool(limited_reader_repair_diagnostic.get("gate_relaxed") or limited_reader_repair.get("gate_relaxed")),
        "limited_reader_repair_raw_input_included": False,
        "repair_attempted": repair_attempted,
        "self_repair_status": self_repair_status,
        "repair_trace_count": repair_trace_count,
        "repair_aborted_count": repair_aborted_count,
        "repair_abort_reasons": repair_abort_reasons,
        "gate_results_present": bool(diagnostic_summary.get("gate_results")),
        "gate_results_extractable": bool(diagnostic_summary.get("gate_results")),
        "repair_extractable": bool(
            repair_attempted
            or repair_trace_count
            or repair_aborted_count
            or repair_abort_reasons
            or self_repair
            or complete_repair_trace
            or limited_reader_repair
        ),
        "complete_reply_service_diagnostics_present": bool(complete_reply_diagnostics),
        "complete_reply_service_diagnostics_extractable": bool(complete_reply_diagnostics),
        "scorecard_event_present": bool(complete_scorecard_event),
        "scorecard_event_extractable": bool(complete_scorecard_event),
        "raw_input_included": False,
        "comment_text_included": False,
        "response_shape_changed": False,
        "public_response_key_change": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
    }


def _attach_observation_diagnostic_lockdown_reply_meta(
    *,
    diagnostic_summary: Dict[str, Any],
    phase_gate_meta: Dict[str, Any],
    lockdown_meta: Dict[str, Any],
) -> None:
    """Attach Step3 diagnostic-lockdown aliases into existing meta only."""

    diagnostic_summary["observation_diagnostic_lockdown_ready"] = True
    diagnostic_summary["step3_observation_diagnostic_lockdown_ready"] = True
    diagnostic_summary["observation_diagnostic_lockdown_meta"] = lockdown_meta
    diagnostic_summary["observation_diagnostic_lockdown"] = lockdown_meta
    diagnostic_summary["gate_results_extractable_for_observation_diagnostic"] = bool(
        lockdown_meta.get("gate_results_extractable") or lockdown_meta.get("gate_results_present")
    )
    diagnostic_summary["repair_extractable_for_observation_diagnostic"] = bool(lockdown_meta.get("repair_extractable"))
    diagnostic_summary["candidate_seen_before_display_gate"] = bool(lockdown_meta.get("candidate_seen"))
    diagnostic_summary["complete_candidate_seen_before_display_gate"] = bool(lockdown_meta.get("candidate_seen"))
    diagnostic_summary["candidate_status_before_display_gate"] = str(lockdown_meta.get("candidate_status") or "")
    diagnostic_summary["candidate_source_before_display_gate"] = str(lockdown_meta.get("candidate_source") or "")
    diagnostic_summary["candidate_generated_before_display_gate"] = bool(lockdown_meta.get("candidate_generated_before_display_gate"))
    diagnostic_summary["complete_candidate_generated_before_display_gate"] = bool(lockdown_meta.get("candidate_generated_before_display_gate"))
    diagnostic_summary["complete_candidate_seen"] = bool(lockdown_meta.get("candidate_seen"))
    diagnostic_summary["complete_candidate_generated"] = bool(lockdown_meta.get("candidate_generated"))
    diagnostic_summary["complete_candidate_displayed"] = bool(lockdown_meta.get("candidate_displayed"))
    diagnostic_summary["complete_candidate_status"] = str(lockdown_meta.get("candidate_status") or "")
    diagnostic_summary["complete_candidate_source"] = str(lockdown_meta.get("candidate_source") or "")
    diagnostic_summary["display_rejection_reasons"] = _dedupe_reason_codes(lockdown_meta.get("display_rejection_reasons") or [])
    diagnostic_summary["used_phrase_unit_ids"] = _dedupe_reason_codes(lockdown_meta.get("used_phrase_unit_ids") or [])
    diagnostic_summary["relation_types"] = _dedupe_reason_codes(lockdown_meta.get("relation_types") or [])
    diagnostic_summary["limited_reader_repair"] = dict(lockdown_meta.get("limited_reader_repair") or {}) if isinstance(lockdown_meta.get("limited_reader_repair"), dict) else {}
    diagnostic_summary["limited_reader_repair_attempted"] = bool(lockdown_meta.get("limited_reader_repair_attempted"))
    diagnostic_summary["limited_reader_repair_applied"] = bool(lockdown_meta.get("limited_reader_repair_applied"))
    diagnostic_summary["limited_reader_repair_operations"] = _dedupe_reason_codes(lockdown_meta.get("limited_reader_repair_operations") or [])
    diagnostic_summary["limited_reader_repair_relation_marker_key"] = str(lockdown_meta.get("limited_reader_repair_relation_marker_key") or "")
    diagnostic_summary["limited_reader_repair_relation_marker_signal_keys"] = _dedupe_reason_codes(lockdown_meta.get("limited_reader_repair_relation_marker_signal_keys") or [])
    diagnostic_summary["limited_reader_repair_relation_type"] = str(lockdown_meta.get("limited_reader_repair_relation_type") or "")
    diagnostic_summary["limited_reader_repair_meaning_added"] = bool(lockdown_meta.get("limited_reader_repair_meaning_added"))
    diagnostic_summary["limited_reader_repair_gate_relaxed"] = bool(lockdown_meta.get("limited_reader_repair_gate_relaxed"))
    diagnostic_summary["limited_reader_repair_raw_input_included"] = False
    diagnostic_summary["used_phrase_unit_count"] = _step3_int(lockdown_meta.get("used_phrase_unit_count"), 0)
    diagnostic_summary["used_relation_count"] = _step3_int(lockdown_meta.get("used_relation_count"), 0)
    diagnostic_summary["self_repair_status"] = str(lockdown_meta.get("self_repair_status") or "")
    diagnostic_summary["repair_trace_count"] = _step3_int(lockdown_meta.get("repair_trace_count"), 0)
    diagnostic_summary["repair_aborted_count"] = _step3_int(lockdown_meta.get("repair_aborted_count"), 0)
    diagnostic_summary["repair_abort_reasons"] = _dedupe_reason_codes(lockdown_meta.get("repair_abort_reasons") or [])

    phase_gate_meta["step3_observation_diagnostic_lockdown_ready"] = True
    phase_gate_meta["observation_diagnostic_lockdown_ready"] = True
    phase_gate_meta["step3_candidate_generated_before_display_gate"] = bool(lockdown_meta.get("candidate_generated_before_display_gate"))
    phase_gate_meta["candidate_generated_before_display_gate"] = bool(lockdown_meta.get("candidate_generated_before_display_gate"))
    phase_gate_meta["gate_results_extractable_for_observation_diagnostic"] = bool(
        lockdown_meta.get("gate_results_extractable") or lockdown_meta.get("gate_results_present")
    )
    phase_gate_meta["repair_extractable_for_observation_diagnostic"] = bool(lockdown_meta.get("repair_extractable"))
    phase_gate_meta["step7_limited_reader_repair_attempted"] = bool(lockdown_meta.get("limited_reader_repair_attempted"))
    phase_gate_meta["step7_limited_reader_repair_applied"] = bool(lockdown_meta.get("limited_reader_repair_applied"))
    phase_gate_meta["step7_limited_reader_repair_raw_input_included"] = False
    phase_gate_meta["step3_observation_diagnostic_lockdown_response_shape_changed"] = False
    phase_gate_meta["step3_observation_diagnostic_lockdown_raw_input_included"] = False
    phase_gate_meta["step3_observation_diagnostic_lockdown_comment_text_included"] = False


def _complete_initial_flag_seed(flag_state: Dict[str, Any]) -> Dict[str, Any]:
    allowed_keys = (
        "version",
        "enabled",
        "source_kind",
        "source",
        "explicitly_configured",
        "requested_composer",
        "requested_composer_model",
        "requested_source",
        "requested_composer_stage",
        "requested_composer_term",
        "canonical_requested_composer",
        "target_composer_term",
        "target_composer_stage_term",
        "complete_composer_initial_requested",
        "complete_initial_composer_requested",
        "complete_initial_client_requested",
        "complete_composer_client_requested",
        "step10_complete_composer_client_requested",
        "step19_a_plan_composer_requested",
        "a_plan_equivalent_compat_requested",
    )
    return {key: flag_state.get(key) for key in allowed_keys if key in flag_state}


def _build_complete_initial_contract_baseline_meta(*, safety_requires_block: bool) -> Dict[str, Any]:
    return {
        "version": "emlis.complete_initial.entry_contract_baseline.v1",
        "response_shape_changed": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_title_changed": False,
        "complete_meta_overrides_public_observation_status": False,
        "comment_text_contract": "passed_only",
        "external_ai_used": False,
        "external_ai_allowed": False,
        "local_llm_used": False,
        "local_llm_allowed": False,
        "fixed_sentence_template_used": False,
        "fixed_sentence_template_allowed": False,
        "fallback_observation_sentence_added": False,
        "fixed_observation_sentence_added": False,
        "completion_sentence_templates_added": False,
        "binding_infrastructure_ready": bool(phase6_composer_contract_ready()),
        "used_evidence_binding_ready": True,
        "used_phrase_unit_binding_ready": True,
        "relation_type_ready": True,
        "complete_initial_binding_ready": True,
        "binding_aware_grounding_ready": True,
        "safety_requires_block": bool(safety_requires_block),
        "safety_blocked": bool(safety_requires_block),
    }


def _build_frontend_passed_only_boundary_seed() -> Dict[str, Any]:
    return {
        "version": "emlis.complete_initial.entry_frontend_boundary.v1",
        "passed_only_contract_preserved": True,
        "frontend_modal_only_passed": True,
        "non_passed_comment_text_empty": True,
        "rejected_comment_text_empty": True,
        "unavailable_comment_text_empty": True,
        "safety_blocked_comment_text_empty": True,
        "complete_meta_cannot_override_public_status": True,
        "rn_contract_changed": False,
    }


def _complete_initial_scope_seed(limited_observation_scope: Any) -> Dict[str, Any]:
    scope_meta = _as_meta_dict(limited_observation_scope)
    nested = scope_meta.get("scope_diagnostic") if isinstance(scope_meta.get("scope_diagnostic"), dict) else {}
    scope_status = str(scope_meta.get("scope_status") or nested.get("scope_status") or "")
    coverage_scope = str(scope_meta.get("coverage_scope") or nested.get("coverage_scope") or "")
    included_claim_ids = list(scope_meta.get("included_claim_ids") or nested.get("included_claim_ids") or [])
    included_relation_ids = list(scope_meta.get("included_relation_ids") or nested.get("included_relation_ids") or [])
    excluded_claims = list(scope_meta.get("excluded_claims") or nested.get("excluded_claims") or [])
    reason_codes = _dedupe_reason_codes([
        *(scope_meta.get("rejection_reasons") or []),
        *(nested.get("rejection_reasons") or []),
        *(scope_meta.get("missing_information") or []),
        *(nested.get("missing_information") or []),
        *(scope_meta.get("safety_boundaries") or []),
        *(nested.get("safety_boundaries") or []),
    ])
    return {
        "version": "emlis.complete_initial.entry_scope_seed.v1",
        "scope_attempted": bool(scope_meta),
        "scope_status": scope_status,
        "coverage_scope": coverage_scope,
        "included_claim_count": int(scope_meta.get("included_claim_count") or nested.get("included_claim_count") or len(included_claim_ids)),
        "included_relation_count": int(scope_meta.get("included_relation_count") or nested.get("included_relation_count") or len(included_relation_ids)),
        "excluded_claim_count": int(scope_meta.get("excluded_claim_count") or nested.get("excluded_claim_count") or len(excluded_claims)),
        "reason_codes": reason_codes,
        "coverage_groups": list(scope_meta.get("coverage_groups") or nested.get("coverage_groups") or []),
        "safety_blocked_before_composer": bool(scope_status == "safety_blocked"),
    }


def _build_complete_initial_coverage_matrix_seed(
    *,
    evidence_spans: List[Any],
    reports: List[Any],
    board: Any,
    graph: Any,
    limited_observation_scope: Any,
) -> Dict[str, Any]:
    scope_seed = _complete_initial_scope_seed(limited_observation_scope)
    phase4_ready = bool(phase4_observer_contract_ready(reports, evidence_spans))
    phase5_board_ready = bool(phase5_board_contract_ready(board))
    phase5_graph_ready = bool(phase5_observation_graph_ready(board, graph))
    binding_ready = bool(phase6_composer_contract_ready())
    included_claim_count = int(scope_seed.get("included_claim_count") or 0)
    coverage_group = (
        str((scope_seed.get("coverage_groups") or [""])[0] or "")
        if isinstance(scope_seed.get("coverage_groups"), list)
        else ""
    )
    if not coverage_group:
        coverage_group = str(scope_seed.get("coverage_scope") or scope_seed.get("scope_status") or "pre_generation")
    return {
        "version": "emlis.complete_initial.entry_coverage_seed.v1",
        "step": "Step2_pre_generation_diagnostic_seed",
        "coverage_group": coverage_group,
        "primary_coverage_group": coverage_group,
        "scope_status": str(scope_seed.get("scope_status") or ""),
        "coverage_scope": str(scope_seed.get("coverage_scope") or ""),
        "source_bundle_ready": True,
        "evidence_ledger_ready": True,
        "evidence_span_count": len(evidence_spans),
        "observer_count": len(reports),
        "phase4_observer_contract_ready": phase4_ready,
        "phase5_board_contract_ready": phase5_board_ready,
        "phase5_observation_graph_ready": phase5_graph_ready,
        "phase6_composer_contract_ready": binding_ready,
        "binding_infrastructure_ready": binding_ready,
        "used_evidence_binding_ready": binding_ready,
        "used_phrase_unit_binding_ready": binding_ready,
        "relation_type_ready": binding_ready,
        "complete_initial_binding_ready": binding_ready,
        "binding_aware_grounding_ready": binding_ready,
        "sentence_binding_ready": binding_ready,
        "sentence_bindings_ready": binding_ready,
        "binding_count": max(1 if binding_ready else 0, included_claim_count),
        "included_claim_count": included_claim_count,
        "included_relation_count": int(scope_seed.get("included_relation_count") or 0),
        "excluded_claim_count": int(scope_seed.get("excluded_claim_count") or 0),
        "scope_seed": scope_seed,
        "raw_input_included": False,
    }


def _build_complete_initial_pre_generation_diagnostic_seed(
    *,
    composer_flag_state: Dict[str, Any],
    limited_release_decision: Any,
    limited_observation_scope: Any,
    evidence_spans: List[Any],
    reports: List[Any],
    board: Any,
    graph: Any,
    safety_requires_block: bool,
) -> Dict[str, Any]:
    release_meta = _as_meta_dict(limited_release_decision)
    contract_baseline_meta = _build_complete_initial_contract_baseline_meta(safety_requires_block=safety_requires_block)
    frontend_boundary_summary = _build_frontend_passed_only_boundary_seed()
    coverage_matrix_seed = _build_complete_initial_coverage_matrix_seed(
        evidence_spans=evidence_spans,
        reports=reports,
        board=board,
        graph=graph,
        limited_observation_scope=limited_observation_scope,
    )
    entry_ap0_decision = build_complete_initial_entry_ap0_decision(
        composer_flag_state=composer_flag_state,
        release_meta=release_meta,
        contract_baseline_meta=contract_baseline_meta,
        frontend_boundary_summary=frontend_boundary_summary,
        coverage_matrix_seed=coverage_matrix_seed,
    )
    return {
        "version": "emlis.complete_initial.pre_generation_diagnostic_seed.v1",
        "step": "Step2_pre_generation_diagnostic_seed",
        "purpose": "seed_entry_ap0_materials_before_registry_resolution",
        "built_after_source_evidence_scope_rollout": True,
        "built_before_registry_resolution": True,
        "built_before_candidate_generation": True,
        "created_before_registry_resolution": True,
        "created_before_candidate_generation": True,
        "entry_gate_only": True,
        "resolver_injection_deferred_to_step3": True,
        "resolver_ap0_injection_pending": True,
        "ap0_decision_not_injected_to_registry_in_step2": True,
        "ap0_decision_injected_to_registry_in_step3": False,
        "resolver_injection_completed_in_step3": False,
        "step3_resolver_ap0_decision_injection_ready": False,
        "step3_resolver_ap0_decision_source": "",
        "used_for_registry_resolution": False,
        "uses_post_generation_display_gate": False,
        "display_gate_relaxed": False,
        "comment_text_contract": "passed_only",
        "raw_input_included": False,
        "raw_input_required_for_improvement": False,
        "source_material_included": False,
        "generated_candidate_included": False,
        "generated_text_included": False,
        "composer_flag_state": _complete_initial_flag_seed(composer_flag_state),
        "release_meta": release_meta,
        "contract_baseline_meta": contract_baseline_meta,
        "frontend_boundary_summary": frontend_boundary_summary,
        "coverage_matrix_seed": coverage_matrix_seed,
        "complete_initial_entry_ap0_decision": entry_ap0_decision,
        "entry_ap0_green": bool(entry_ap0_decision.get("green")),
        "entry_ap0_status": str(entry_ap0_decision.get("status") or ""),
        "entry_ap0_unmet_checks": list(entry_ap0_decision.get("unmet_checks") or []),
        "entry_ap0_release_blockers": list(entry_ap0_decision.get("release_blockers") or []),
        "entry_ap0_next_step": str(entry_ap0_decision.get("next_step") or ""),
    }


def _attach_complete_initial_pre_generation_seed(
    *,
    diagnostic_summary: Dict[str, Any],
    phase_gate_meta: Dict[str, Any],
    seed: Dict[str, Any] | None,
) -> None:
    if not isinstance(seed, dict) or not seed:
        return
    entry_decision = dict(seed.get("complete_initial_entry_ap0_decision") or {})
    diagnostic_summary["complete_initial_pre_generation_diagnostic_seed"] = seed
    diagnostic_summary["complete_initial_entry_ap0_seed"] = seed
    diagnostic_summary["complete_initial_entry_ap0_materials"] = {
        "composer_flag_state": dict(seed.get("composer_flag_state") or {}),
        "release_meta": dict(seed.get("release_meta") or {}),
        "contract_baseline_meta": dict(seed.get("contract_baseline_meta") or {}),
        "frontend_boundary_summary": dict(seed.get("frontend_boundary_summary") or {}),
        "coverage_matrix_seed": dict(seed.get("coverage_matrix_seed") or {}),
    }
    diagnostic_summary["complete_initial_entry_ap0_decision"] = entry_decision
    diagnostic_summary["complete_initial_entry_ap0_decision_preview"] = entry_decision
    diagnostic_summary["complete_initial_entry_ap0_green"] = bool(seed.get("entry_ap0_green"))
    diagnostic_summary["complete_initial_entry_ap0_unmet_checks"] = list(seed.get("entry_ap0_unmet_checks") or [])
    diagnostic_summary["complete_initial_entry_ap0_release_blockers"] = list(seed.get("entry_ap0_release_blockers") or [])
    diagnostic_summary["complete_initial_entry_ap0_next_step"] = str(seed.get("entry_ap0_next_step") or "")
    diagnostic_summary["complete_initial_entry_ap0_seed_built_before_registry"] = bool(seed.get("built_before_registry_resolution") or seed.get("created_before_registry_resolution"))
    diagnostic_summary["complete_initial_entry_ap0_used_for_registry_resolution"] = bool(seed.get("used_for_registry_resolution"))
    diagnostic_summary["complete_initial_entry_ap0_resolver_injection_pending"] = bool(seed.get("resolver_ap0_injection_pending") or seed.get("resolver_injection_deferred_to_step3"))
    diagnostic_summary["complete_initial_entry_ap0_injected_to_registry_in_step3"] = bool(seed.get("ap0_decision_injected_to_registry_in_step3"))
    diagnostic_summary["complete_initial_entry_ap0_resolver_injection_completed_in_step3"] = bool(seed.get("resolver_injection_completed_in_step3") or seed.get("step3_resolver_ap0_decision_injection_ready"))
    diagnostic_summary["step3_resolver_ap0_decision_injection_ready"] = bool(seed.get("step3_resolver_ap0_decision_injection_ready"))
    diagnostic_summary["step3_resolver_ap0_decision_source"] = str(seed.get("step3_resolver_ap0_decision_source") or "")
    phase_gate_meta["step2_pre_generation_diagnostic_seed_ready"] = True
    phase_gate_meta["complete_initial_pre_generation_seed_ready"] = True
    phase_gate_meta["complete_initial_entry_ap0_green"] = bool(seed.get("entry_ap0_green"))
    phase_gate_meta["complete_initial_entry_ap0_resolver_injection_deferred_to_step3"] = bool(seed.get("resolver_injection_deferred_to_step3"))
    phase_gate_meta["complete_initial_entry_ap0_resolver_injection_pending"] = bool(seed.get("resolver_ap0_injection_pending") or seed.get("resolver_injection_deferred_to_step3"))
    phase_gate_meta["complete_initial_entry_ap0_used_for_registry_resolution"] = bool(seed.get("used_for_registry_resolution"))
    phase_gate_meta["complete_initial_entry_ap0_injected_to_registry_in_step3"] = bool(seed.get("ap0_decision_injected_to_registry_in_step3"))
    phase_gate_meta["complete_initial_entry_ap0_resolver_injection_completed_in_step3"] = bool(seed.get("resolver_injection_completed_in_step3") or seed.get("step3_resolver_ap0_decision_injection_ready"))
    phase_gate_meta["step3_resolver_ap0_decision_injection_ready"] = bool(seed.get("step3_resolver_ap0_decision_injection_ready"))
    phase_gate_meta["step3_resolver_ap0_decision_source"] = str(seed.get("step3_resolver_ap0_decision_source") or "")
    phase_gate_meta["complete_initial_entry_ap0_unmet_checks"] = list(seed.get("entry_ap0_unmet_checks") or [])


def _step4_complete_initial_resolution_reason_group(
    *,
    resolution_meta: Dict[str, Any],
    entry_ap0_decision: Dict[str, Any],
    complete_initial_gate: Dict[str, Any],
    rejection_reasons: List[str],
) -> str:
    """Classify complete-initial resolver stops without changing the resolver.

    Step4 is diagnostic-only.  It keeps the registry decision as-is, while
    separating ``composer_client_not_connected`` causes into AP0 / rollout /
    safety so the next work item can be chosen without raw input text.
    """

    connection_status = str(resolution_meta.get("connection_status") or "")
    stop_stage = str(resolution_meta.get("pre_connection_stop_stage") or "")
    gate_reason = str(complete_initial_gate.get("reason") or complete_initial_gate.get("primary_reason") or "")
    unmet_checks = {str(item or "") for item in list(entry_ap0_decision.get("unmet_checks") or [])}
    reason_set = {str(item or "") for item in list(rejection_reasons or [])}
    if gate_reason:
        reason_set.add(gate_reason)

    if (
        bool(resolution_meta.get("safety_blocked"))
        or connection_status == "blocked_safety"
        or stop_stage == "safety"
        or "safety_boundary" in reason_set
        or "composer_prevented_by_safety_boundary" in reason_set
        or "safety_boundary" in unmet_checks
    ):
        return "safety"
    if (
        connection_status == "blocked_rollout"
        or stop_stage == "rollout"
        or "complete_initial_rollout_not_allowed" in reason_set
        or "limited_composer_rollout_not_allowed" in reason_set
        or "rollout_allowed" in unmet_checks
    ):
        return "rollout"
    if (
        connection_status == "blocked_ap0"
        or stop_stage == "ap0"
        or "complete_initial_ap0_not_green" in reason_set
        or bool(entry_ap0_decision) and entry_ap0_decision.get("green") is False
    ):
        return "ap0"
    if bool(resolution_meta.get("complete_initial_client_used")) or connection_status in {"default_client_resolved", "provided_client"}:
        return "resolved"
    if connection_status == "blocked_feature_flag" or stop_stage == "flag":
        return "flag"
    if connection_status == "blocked_scope" or stop_stage == "scope":
        return "scope"
    return connection_status or stop_stage or "unknown"


def _build_step4_complete_initial_resolution_meta(
    *,
    resolution_meta: Dict[str, Any],
    entry_ap0_decision: Dict[str, Any],
) -> Dict[str, Any]:
    """Freeze Step4 resolution meta for complete-initial diagnostics.

    The payload is additive and developer-facing.  It mirrors the registry
    result, complete_initial_gate, and rejection reasons.  It never changes
    AP0, rollout, Gate, Display, RN, DB, or public API behavior.
    """

    resolution = dict(resolution_meta or {})
    entry_decision = dict(entry_ap0_decision or {})
    complete_gate = dict(resolution.get("complete_initial_gate") or {})
    default_resolution = dict(resolution.get("default_composer_resolution") or {})
    connection_status = str(
        resolution.get("connection_status")
        or default_resolution.get("connection_status")
        or ""
    )
    stop_stage = str(
        resolution.get("pre_connection_stop_stage")
        or default_resolution.get("pre_connection_stop_stage")
        or ""
    )
    gate_reason = str(complete_gate.get("reason") or complete_gate.get("primary_reason") or "")
    rejection_reasons = _dedupe_reason_codes([
        *(resolution.get("rejection_reasons") or []),
        gate_reason if gate_reason and gate_reason != "complete_initial_client_resolved" else "",
    ])
    reason_group = _step4_complete_initial_resolution_reason_group(
        resolution_meta=resolution,
        entry_ap0_decision=entry_decision,
        complete_initial_gate=complete_gate,
        rejection_reasons=rejection_reasons,
    )
    client_resolved = bool(
        resolution.get("complete_initial_client_used")
        or (
            resolution.get("requested_composer") == "complete_initial"
            and connection_status == "default_client_resolved"
        )
    )
    primary_reason = (
        "complete_initial_client_resolved"
        if client_resolved
        else _first_reason(rejection_reasons, default=gate_reason or connection_status or "composer_client_not_connected")
    )
    return {
        "version": "emlis.complete_initial.step4.resolution_meta.v1",
        "step": "Step4_resolution_meta_fixed",
        "ready": True,
        "meta_only": True,
        "additive": True,
        "raw_input_included": False,
        "source_material_included": False,
        "generated_candidate_included": False,
        "display_gate_relaxed": False,
        "rn_contract_changed": False,
        "public_response_shape_changed": False,
        "comment_text_contract": "passed_only",
        "composer_client_resolution": resolution,
        "complete_initial_gate": complete_gate,
        "requested_composer": str(resolution.get("requested_composer") or ""),
        "canonical_requested_composer": str(resolution.get("canonical_requested_composer") or ""),
        "connection_status": connection_status,
        "pre_connection_stop_stage": stop_stage,
        "resolution_source": str(resolution.get("resolution_source") or resolution.get("source") or ""),
        "resolved_client_class": str(resolution.get("resolved_client_class") or resolution.get("resolved_client_name") or ""),
        "composer_model": str(resolution.get("composer_model") or ""),
        "default_client_used": bool(resolution.get("default_client_used")),
        "default_client_resolved": bool(resolution.get("default_client_resolved")),
        "complete_initial_client_used": bool(resolution.get("complete_initial_client_used")),
        "complete_initial_client_resolved": client_resolved,
        "composer_client_not_connected": bool(not client_resolved),
        "composer_client_not_connected_reason": "" if client_resolved else primary_reason,
        "composer_client_not_connected_reason_group": "resolved" if client_resolved else reason_group,
        "reason_group": reason_group,
        "primary_reason": primary_reason,
        "rejection_reasons": rejection_reasons,
        "resolution_rejection_reasons": rejection_reasons,
        "entry_ap0_green": bool(entry_decision.get("green")),
        "entry_ap0_status": str(entry_decision.get("status") or ""),
        "entry_unmet_checks": list(entry_decision.get("unmet_checks") or []),
        "entry_release_blockers": list(entry_decision.get("release_blockers") or []),
        "blocked_by_ap0": bool(reason_group == "ap0"),
        "blocked_by_rollout": bool(reason_group == "rollout"),
        "blocked_by_safety": bool(reason_group == "safety"),
        "ap0_green_required": bool(complete_gate.get("ap0_green_required", True)),
        "rollout_allowed_required": bool(complete_gate.get("rollout_allowed_required", True)),
        "release_allowed": resolution.get("release_allowed"),
        "safety_blocked": bool(resolution.get("safety_blocked")),
    }


def _attach_step4_complete_initial_resolution_meta(
    *,
    diagnostic_summary: Dict[str, Any],
    phase_gate_meta: Dict[str, Any],
    resolution_meta: Dict[str, Any],
) -> Dict[str, Any]:
    entry_decision = dict(diagnostic_summary.get("complete_initial_entry_ap0_decision") or {})
    step4_meta = _build_step4_complete_initial_resolution_meta(
        resolution_meta=resolution_meta,
        entry_ap0_decision=entry_decision,
    )
    complete_gate = dict(step4_meta.get("complete_initial_gate") or {})
    resolution_reasons = list(step4_meta.get("rejection_reasons") or [])

    diagnostic_summary["composer_client_resolution"] = dict(resolution_meta or {})
    diagnostic_summary["composer_client_resolution_meta"] = dict(resolution_meta or {})
    diagnostic_summary["complete_initial_gate"] = complete_gate
    diagnostic_summary["complete_initial_resolution"] = step4_meta
    diagnostic_summary["step4_complete_initial_resolution"] = step4_meta
    diagnostic_summary["step4_resolution_meta"] = step4_meta
    diagnostic_summary["step4_resolution_meta_fixed"] = True
    diagnostic_summary["complete_initial_resolution_meta_fixed"] = True
    diagnostic_summary["composer_client_resolution_rejection_reasons"] = resolution_reasons
    diagnostic_summary["complete_initial_resolution_rejection_reasons"] = resolution_reasons
    diagnostic_summary["resolution_rejection_reasons"] = resolution_reasons
    diagnostic_summary["complete_initial_resolution_reason_group"] = str(step4_meta.get("reason_group") or "")
    diagnostic_summary["composer_client_not_connected_reason"] = str(step4_meta.get("composer_client_not_connected_reason") or "")
    diagnostic_summary["composer_client_not_connected_reason_group"] = str(step4_meta.get("composer_client_not_connected_reason_group") or "")
    diagnostic_summary["complete_initial_resolution_connection_status"] = str(step4_meta.get("connection_status") or "")
    diagnostic_summary["complete_initial_resolution_stop_stage"] = str(step4_meta.get("pre_connection_stop_stage") or "")
    diagnostic_summary["step4_resolution_connection_status"] = str(step4_meta.get("connection_status") or "")
    diagnostic_summary["step4_resolution_stop_stage"] = str(step4_meta.get("pre_connection_stop_stage") or "")
    diagnostic_summary["step4_resolution_reason_group"] = str(step4_meta.get("reason_group") or "")

    phase_gate_meta["step4_resolution_meta_fixed"] = True
    phase_gate_meta["complete_initial_resolution_meta_fixed"] = True
    phase_gate_meta["step4_complete_initial_resolution_ready"] = True
    phase_gate_meta["step4_resolution_connection_status"] = str(step4_meta.get("connection_status") or "")
    phase_gate_meta["step4_resolution_stop_stage"] = str(step4_meta.get("pre_connection_stop_stage") or "")
    phase_gate_meta["step4_resolution_reason_group"] = str(step4_meta.get("reason_group") or "")
    phase_gate_meta["step4_resolution_rejection_reasons"] = resolution_reasons
    phase_gate_meta["step4_composer_client_not_connected_reason"] = str(step4_meta.get("composer_client_not_connected_reason") or "")
    phase_gate_meta["step4_composer_client_not_connected_reason_group"] = str(step4_meta.get("composer_client_not_connected_reason_group") or "")
    phase_gate_meta["step4_complete_initial_gate_reason"] = str(complete_gate.get("reason") or "")
    phase_gate_meta["step4_blocked_by_ap0"] = bool(step4_meta.get("blocked_by_ap0"))
    phase_gate_meta["step4_blocked_by_rollout"] = bool(step4_meta.get("blocked_by_rollout"))
    phase_gate_meta["step4_blocked_by_safety"] = bool(step4_meta.get("blocked_by_safety"))
    return step4_meta


def _safe_step5_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        values = [value]
    elif isinstance(value, (list, tuple, set)):
        values = list(value)
    else:
        values = [value]
    out: List[str] = []
    seen: set[str] = set()
    for raw in values:
        item = str(raw or "").strip()
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _complete_initial_composer_meta(composer_candidate: Any) -> Dict[str, Any]:
    raw_meta = getattr(composer_candidate, "composer_meta", {}) if composer_candidate is not None else {}
    return dict(raw_meta) if isinstance(raw_meta, dict) else {}


def _complete_initial_binding_source(composer_meta: Dict[str, Any]) -> Dict[str, Any]:
    for key in (
        "complete_grounding_binding",
        "binding_meta",
        "grounding_input",
        "sentence_binding_bundle",
    ):
        value = composer_meta.get(key)
        if isinstance(value, dict):
            return dict(value)
    return {}


def _complete_initial_raw_sentence_bindings(composer_meta: Dict[str, Any]) -> List[Dict[str, Any]]:
    values: Any = composer_meta.get("sentence_bindings")
    if not isinstance(values, list):
        binding_source = _complete_initial_binding_source(composer_meta)
        values = binding_source.get("bindings") or binding_source.get("sentence_bindings") or []
    if not isinstance(values, list):
        return []
    return [dict(item) for item in values if isinstance(item, dict)]


def _sanitize_complete_initial_sentence_binding(binding: Dict[str, Any]) -> Dict[str, Any]:
    """Keep only source-binding identifiers for Step5 diagnostics.

    CompleteComposerClient may keep realized surface text inside internal
    binding objects. Step5 proves the generation path and the gate binding;
    it does not need to duplicate generated text or raw input into diagnostics.
    """

    surface_signature = binding.get("surface_signature") if isinstance(binding.get("surface_signature"), dict) else {}
    sanitized = {
        "version": str(binding.get("version") or ""),
        "sentence_id": str(binding.get("sentence_id") or ""),
        "line_role": str(binding.get("line_role") or ""),
        "relation_type": str(binding.get("relation_type") or surface_signature.get("relation_type") or ""),
        "canonical_relation_type": str(surface_signature.get("canonical_relation_type") or binding.get("canonical_relation_type") or ""),
        "relation_family": str(surface_signature.get("relation_family") or binding.get("relation_family") or ""),
        "used_evidence_span_ids": _safe_step5_list(binding.get("used_evidence_span_ids")),
        "used_phrase_unit_ids": _safe_step5_list(binding.get("used_phrase_unit_ids")),
        "used_relation_ids": _safe_step5_list(binding.get("used_relation_ids")),
        "source_step": str(binding.get("source_step") or ""),
        "target_step": str(binding.get("target_step") or ""),
        "raw_input_included": bool(binding.get("raw_input_included")),
    }
    return {key: value for key, value in sanitized.items() if value not in ("", [], None)}


def _complete_initial_gate_step5_trace(gate_trace: Dict[str, Any]) -> Dict[str, Any]:
    gates = {
        "reader": gate_trace.get("reader") if isinstance(gate_trace.get("reader"), dict) else {},
        "grounding": gate_trace.get("grounding") if isinstance(gate_trace.get("grounding"), dict) else {},
        "template_echo": gate_trace.get("template_echo") if isinstance(gate_trace.get("template_echo"), dict) else {},
        "display": gate_trace.get("display_gate") if isinstance(gate_trace.get("display_gate"), dict) else {},
    }
    return {
        key: {
            "evaluated": bool(value),
            "gate_binding_contract_version": GATE_BINDING_CONTRACT_VERSION,
            "binding_contract_version": GATE_BINDING_CONTRACT_VERSION,
            "passed": bool(value.get("passed")) if isinstance(value, dict) else False,
            "rejection_reasons": _safe_step5_list(value.get("rejection_reasons")) if isinstance(value, dict) else [],
            "binding_present": bool(value.get("binding_present") or value.get("binding_available")) if isinstance(value, dict) else False,
            "binding_available": bool(value.get("binding_available") or value.get("binding_present")) if isinstance(value, dict) else False,
            "binding_required": bool(key in _BINDING_DECISION_GATES and value.get("binding_required")) if isinstance(value, dict) else False,
            "binding_used": bool(key in _BINDING_DECISION_GATES and value.get("binding_used")) if isinstance(value, dict) else False,
            "binding_missing": bool(key in _BINDING_DECISION_GATES and value.get("binding_missing")) if isinstance(value, dict) else False,
            "binding_count": int(value.get("binding_count") or 0) if isinstance(value, dict) else 0,
            "expected_binding_count": int(value.get("expected_binding_count") or 0) if isinstance(value, dict) else 0,
            "binding_support_source": str(value.get("binding_support_source") or ("display_binding_aware_result" if key == "display" and value.get("binding_used") else "declared_relation_binding" if key == "grounding" and value.get("binding_used") else "none")) if isinstance(value, dict) else "none",
        }
        for key, value in gates.items()
    }


def _build_step5_complete_initial_candidate_generation_meta(
    *,
    resolution_meta: Dict[str, Any],
    composer_candidate: Any,
    display_decision: Any,
    gate_trace: Dict[str, Any],
) -> Dict[str, Any]:
    composer_meta = _complete_initial_composer_meta(composer_candidate)
    binding_source = _complete_initial_binding_source(composer_meta)
    raw_sentence_bindings = _complete_initial_raw_sentence_bindings(composer_meta)
    sentence_bindings = [_sanitize_complete_initial_sentence_binding(binding) for binding in raw_sentence_bindings]
    relation_types = _safe_step5_list(
        composer_meta.get("relation_types")
        or composer_meta.get("used_relation_ids")
        or getattr(composer_candidate, "used_relation_ids", [])
    )
    used_phrase_unit_ids = _safe_step5_list(
        composer_meta.get("used_phrase_unit_ids")
        or binding_source.get("used_phrase_unit_ids")
    )
    if not used_phrase_unit_ids and sentence_bindings:
        used_phrase_unit_ids = _dedupe_reason_codes(
            phrase_id
            for binding in sentence_bindings
            for phrase_id in _safe_step5_list(binding.get("used_phrase_unit_ids"))
        )
    used_evidence_span_ids = _safe_step5_list(
        getattr(composer_candidate, "used_evidence_span_ids", [])
        or composer_meta.get("used_evidence_span_ids")
        or binding_source.get("used_evidence_span_ids")
    )
    status = str(getattr(composer_candidate, "status", "") or "not_attempted")
    composer_source = str(getattr(composer_candidate, "composer_source", "") or "")
    display_status = str(getattr(display_decision, "observation_status", "") or "unavailable")
    public_comment_text = str(getattr(display_decision, "comment_text", "") or "").strip()
    candidate_comment_text_present = bool(str(getattr(composer_candidate, "comment_text", "") or "").strip())
    complete_initial_client_resolved = bool(
        resolution_meta.get("complete_initial_client_used")
        or (
            resolution_meta.get("requested_composer") == "complete_initial"
            and resolution_meta.get("connection_status") == "default_client_resolved"
        )
    )
    attempt_count = int(getattr(composer_candidate, "attempt_count", 0) or 0) if composer_candidate is not None else 0
    generate_called = bool(complete_initial_client_resolved and attempt_count > 0)
    candidate_generated = bool(status == "generated" and composer_source == "ai_generated" and candidate_comment_text_present)
    gate_results = _complete_initial_gate_step5_trace(gate_trace)
    existing_gates_preserved = all(bool(gate_results.get(key, {}).get("evaluated")) for key in ("reader", "grounding", "template_echo", "display"))
    non_passed_comment_text_empty = bool(display_status == "passed" or not public_comment_text)
    fallback_used = bool(
        composer_meta.get("fallback_observation_sentence_added")
        or composer_meta.get("fallback_observation_used")
        or composer_meta.get("safe_fallback_used")
    )
    fixed_string_renderer_used = bool(
        getattr(composer_candidate, "fixed_string_renderer_used", False)
        or composer_meta.get("fixed_string_renderer_used")
        or composer_meta.get("fixed_sentence_template_used")
    )
    phase18_candidate_path_contract_version = "cocolon.emlis.complete_initial.candidate_path.v2"
    generation_display_gate_separated = bool(
        composer_meta.get("complete_initial_candidate_generation_display_gate_separated")
        or (candidate_generated and display_status != "")
    )
    runtime = {
        "version": "emlis.complete_initial.runtime.v1",
        "step": "Step5_candidate_generation_path_confirmation",
        "client_status": "resolved" if complete_initial_client_resolved else "not_resolved",
        "phase18_candidate_path_contract_version": phase18_candidate_path_contract_version,
        "candidate_generation_attempted": generate_called,
        "complete_composer_client_generate_called": generate_called,
        "candidate_generated": candidate_generated,
        "candidate_generated_before_display_gate": candidate_generated,
        "candidate_status": status,
        "candidate_status_before_display_gate": status,
        "candidate_status_after_display_gate": display_status,
        "composer_source": composer_source,
        "complete_initial_candidate_generation_display_gate_separated": generation_display_gate_separated,
        "composer_model": str(getattr(composer_candidate, "composer_model", "") or resolution_meta.get("composer_model") or ""),
        "generation_method": str(getattr(composer_candidate, "generation_method", "") or composer_meta.get("generation_method") or ""),
        "generation_scope": str(getattr(composer_candidate, "generation_scope", "") or composer_meta.get("generation_scope") or ""),
        "coverage_scope": str(getattr(composer_candidate, "coverage_scope", "") or composer_meta.get("coverage_scope") or ""),
        "attempt_count": attempt_count,
        "used_evidence_span_ids": used_evidence_span_ids,
        "used_evidence_span_count": len(used_evidence_span_ids),
        "used_phrase_unit_ids": used_phrase_unit_ids,
        "used_phrase_unit_count": len(used_phrase_unit_ids),
        "relation_types": relation_types,
        "relation_type_count": len(relation_types),
        "sentence_bindings": sentence_bindings,
        "sentence_binding_count": len(sentence_bindings),
        "binding_present": bool(binding_source.get("binding_present") or sentence_bindings),
        "binding_missing": bool(binding_source.get("binding_missing")),
        "binding_count": int(binding_source.get("binding_count") or len(sentence_bindings) or 0),
        "expected_binding_count": int(binding_source.get("expected_binding_count") or len(sentence_bindings) or 0),
        "candidate_comment_text_present": candidate_comment_text_present,
        "public_comment_text_present": bool(public_comment_text),
        "comment_text_contract": "passed_only",
        "comment_text_publicly_assigned": bool(display_status == "passed" and public_comment_text),
        "raw_input_included": False,
        "generated_candidate_text_included": False,
    }
    return {
        "version": "emlis.complete_initial.step5.candidate_generation_path.v1",
        "step": "Step5_candidate_generation_path_confirmation",
        "complete_initial_client_resolved": complete_initial_client_resolved,
        "phase18_candidate_path_contract_version": phase18_candidate_path_contract_version,
        "candidate_generation_attempted": generate_called,
        "complete_composer_client_generate_called": generate_called,
        "candidate_generated": candidate_generated,
        "candidate_generated_before_display_gate": candidate_generated,
        "candidate_status": status,
        "candidate_status_before_display_gate": status,
        "candidate_status_after_display_gate": display_status,
        "composer_source": composer_source,
        "display_observation_status": display_status,
        "complete_initial_candidate_generation_display_gate_separated": generation_display_gate_separated,
        "public_comment_text_present": bool(public_comment_text),
        "candidate_comment_text_present": candidate_comment_text_present,
        "non_passed_comment_text_empty": non_passed_comment_text_empty,
        "passed_only_comment_text_contract_preserved": non_passed_comment_text_empty,
        "existing_reader_grounding_template_display_gates_preserved": existing_gates_preserved,
        "reader_gate_evaluated": bool(gate_results.get("reader", {}).get("evaluated")),
        "grounding_gate_evaluated": bool(gate_results.get("grounding", {}).get("evaluated")),
        "template_gate_evaluated": bool(gate_results.get("template_echo", {}).get("evaluated")),
        "display_gate_evaluated": bool(gate_results.get("display", {}).get("evaluated")),
        "gate_results": gate_results,
        "runtime": runtime,
        "fallback_observation_sentence_added": fallback_used,
        "fallback_used": fallback_used,
        "fixed_string_renderer_used": fixed_string_renderer_used,
        "display_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "comment_text_contract": "passed_only",
        "raw_input_included": False,
        "generated_candidate_text_included": False,
        "candidate_text_included": False,
    }



def _attach_p4_complete_initial_surface_availability_summary(
    *,
    diagnostic_summary: Dict[str, Any],
    phase_gate_meta: Dict[str, Any],
    candidate_generation_summary: Mapping[str, Any] | None = None,
    surface_requirement: Mapping[str, Any] | None = None,
    material_route: Mapping[str, Any] | None = None,
) -> None:
    """Attach P4 body-free source-availability summary.

    This is diagnostic-only.  It does not generate comment_text, does not relax
    gates, and keeps source-unavailable out of the normal rebuild lane.
    """

    try:
        resolved_candidate_generation_summary = (
            dict(candidate_generation_summary)
            if isinstance(candidate_generation_summary, Mapping)
            else dict(diagnostic_summary.get("complete_initial_candidate_generation_path") or {})
            or dict(diagnostic_summary.get("step5_candidate_generation_path") or {})
        )
        summary = build_complete_initial_surface_availability_summary(
            diagnostic_summary=diagnostic_summary,
            phase_gate=phase_gate_meta,
            candidate_generation_summary=resolved_candidate_generation_summary,
            surface_requirement=surface_requirement,
            material_route=material_route,
        )
    except Exception:
        return
    diagnostic_summary[COMPLETE_INITIAL_SURFACE_AVAILABILITY_PUBLIC_META_KEY] = dict(summary)
    phase_gate_meta[COMPLETE_INITIAL_SURFACE_AVAILABILITY_PUBLIC_META_KEY] = dict(summary)

def _attach_step5_complete_initial_candidate_generation_meta(
    *,
    diagnostic_summary: Dict[str, Any],
    phase_gate_meta: Dict[str, Any],
    resolution_meta: Dict[str, Any],
    composer_candidate: Any,
    display_decision: Any,
    gate_trace: Dict[str, Any],
) -> None:
    step5_meta = _build_step5_complete_initial_candidate_generation_meta(
        resolution_meta=resolution_meta,
        composer_candidate=composer_candidate,
        display_decision=display_decision,
        gate_trace=gate_trace,
    )
    runtime = dict(step5_meta.get("runtime") or {})
    diagnostic_summary["complete_initial_candidate_generation_path"] = step5_meta
    diagnostic_summary["step5_candidate_generation_path"] = step5_meta
    diagnostic_summary["complete_initial_runtime"] = runtime
    diagnostic_summary["step5_complete_initial_runtime"] = runtime
    diagnostic_summary["step5_candidate_generation_path_confirmed"] = True
    diagnostic_summary["complete_initial_candidate_generation_attempted"] = bool(step5_meta.get("candidate_generation_attempted"))
    diagnostic_summary["complete_initial_candidate_generated"] = bool(step5_meta.get("candidate_generated"))
    diagnostic_summary["complete_initial_candidate_status"] = str(step5_meta.get("candidate_status") or "")
    diagnostic_summary["complete_initial_existing_gates_preserved_after_generation"] = bool(step5_meta.get("existing_reader_grounding_template_display_gates_preserved"))
    diagnostic_summary["complete_initial_non_passed_comment_text_empty"] = bool(step5_meta.get("non_passed_comment_text_empty"))
    diagnostic_summary["complete_initial_fallback_used"] = bool(step5_meta.get("fallback_used"))

    phase_gate_meta["step5_candidate_generation_path_confirmed"] = True
    phase_gate_meta["step5_complete_initial_candidate_generation_attempted"] = bool(step5_meta.get("candidate_generation_attempted"))
    phase_gate_meta["step5_complete_composer_client_generate_called"] = bool(step5_meta.get("complete_composer_client_generate_called"))
    phase_gate_meta["step5_complete_initial_candidate_generated"] = bool(step5_meta.get("candidate_generated"))
    phase_gate_meta["step5_complete_initial_candidate_status"] = str(step5_meta.get("candidate_status") or "")
    phase_gate_meta["step5_existing_gates_preserved_after_generation"] = bool(step5_meta.get("existing_reader_grounding_template_display_gates_preserved"))
    phase_gate_meta["step5_non_passed_comment_text_empty"] = bool(step5_meta.get("non_passed_comment_text_empty"))
    phase_gate_meta["step5_fallback_used"] = bool(step5_meta.get("fallback_used"))
    phase_gate_meta["step5_no_fallback_used"] = not bool(step5_meta.get("fallback_used"))
    phase_gate_meta["step5_display_gate_relaxed"] = bool(step5_meta.get("display_gate_relaxed"))
    phase_gate_meta["step5_reader_gate_evaluated"] = bool(step5_meta.get("reader_gate_evaluated"))
    phase_gate_meta["step5_grounding_gate_evaluated"] = bool(step5_meta.get("grounding_gate_evaluated"))
    phase_gate_meta["step5_template_gate_evaluated"] = bool(step5_meta.get("template_gate_evaluated"))
    phase_gate_meta["step5_display_gate_evaluated"] = bool(step5_meta.get("display_gate_evaluated"))
    phase_gate_meta["step5_runtime_sentence_binding_count"] = int(runtime.get("sentence_binding_count") or 0)


def _safe_step6_int(value: Any, default: int = 0) -> int:
    try:
        return int(value if value is not None else default)
    except (TypeError, ValueError):
        return int(default)


def _safe_step6_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value if value is not None else default)
    except (TypeError, ValueError):
        return float(default)


def _build_step6_complete_initial_final_ap0_scorecard_connection_meta(
    *,
    diagnostic_summary: Dict[str, Any],
    step18_ap0_migration_decision: Dict[str, Any],
    complete_composer_initial_ap0_report: Dict[str, Any],
    complete_scorecard_event: Dict[str, Any],
    step12_complete_scorecard_harness: Dict[str, Any],
) -> Dict[str, Any]:
    """Connect Final AP0 and scorecard outputs for Step6 diagnostics.

    Step6 is meta-only. It records the execution-after-Gate AP0 decision and
    the scorecard event so the next improvement target is visible without
    changing comment_text, public response keys, or the passed-only display
    contract.
    """

    final_ap0 = dict(step18_ap0_migration_decision or {})
    report = dict(complete_composer_initial_ap0_report or final_ap0.get("complete_composer_initial_ap0_report") or {})
    scorecard_event = dict(complete_scorecard_event or {})
    scorecard_harness = dict(step12_complete_scorecard_harness or {})
    entry_ap0 = dict(diagnostic_summary.get("complete_initial_entry_ap0_decision") or {})
    step5_path = dict(diagnostic_summary.get("complete_initial_candidate_generation_path") or {})
    runtime = dict(diagnostic_summary.get("complete_initial_runtime") or {})

    final_return_steps = _safe_step5_list(final_ap0.get("return_steps"))
    final_unmet_checks = _safe_step5_list(final_ap0.get("unmet_checks"))
    report_blockers = _safe_step5_list(
        report.get("release_blocker_keys")
        or report.get("release_blockers")
        or final_unmet_checks
    )
    scorecard_reasons = _safe_step5_list(scorecard_event.get("top_rejection_reasons"))
    improvement_reasons = _dedupe_reason_codes([
        *(scorecard_reasons or []),
        str(diagnostic_summary.get("primary_reason") or ""),
        *(final_unmet_checks or []),
        *(report_blockers or []),
    ])
    coverage_group = str(
        scorecard_event.get("coverage_group")
        or diagnostic_summary.get("coverage_group")
        or runtime.get("coverage_scope")
        or ""
    )
    scorecard_event_connected = bool(
        scorecard_event.get("scorecard_event_connected")
        or scorecard_event.get("scorecard_event_added")
        or scorecard_event
    )
    scorecard_harness_connected = bool(
        scorecard_harness.get("scorecard_harness_added")
        or scorecard_harness.get("scorecard_ready")
        or scorecard_harness.get("ready")
        or scorecard_harness
    )
    display_passed = bool(scorecard_event.get("display_passed"))
    scorecard_display_status = str(scorecard_event.get("observation_status") or diagnostic_summary.get("observation_status") or "")
    candidate_generated = bool(
        scorecard_event.get("complete_candidate_generated")
        or step5_path.get("candidate_generated")
    )
    candidate_attempted = bool(step5_path.get("candidate_generation_attempted") or candidate_generated)
    next_improvement_meta = {
        "version": "emlis.complete_initial.step6.next_improvement_meta.v1",
        "source_step": "Step6_Final_AP0_scorecard_connection",
        "visible_from_meta_only": True,
        "raw_input_required": False,
        "raw_input_included": False,
        "return_steps": final_return_steps,
        "release_blockers": report_blockers,
        "unmet_checks": final_unmet_checks,
        "scorecard_top_rejection_reasons": scorecard_reasons,
        "improvement_reason_codes": improvement_reasons,
        "coverage_group": coverage_group,
        "primary_reason": improvement_reasons[0] if improvement_reasons else str(diagnostic_summary.get("primary_reason") or ""),
        "scorecard_event_kind": str(scorecard_event.get("event_kind") or ""),
        "scorecard_observation_status": scorecard_display_status,
        "final_ap0_decision": str(final_ap0.get("decision") or ""),
        "final_ap0_next_step": str(final_ap0.get("next_step") or ""),
    }
    return {
        "version": "emlis.complete_initial.step6.final_ap0_scorecard_connection.v1",
        "step": "Step6_Final_AP0_scorecard_connection",
        "ready": True,
        "meta_only": True,
        "additive": True,
        "built_after_registry_resolution": True,
        "built_after_candidate_generation_path_check": bool(step5_path),
        "built_after_display_gate": True,
        "built_before_rn_contract_regression": True,
        "entry_ap0_used_for_registry_resolution": bool(entry_ap0.get("used_for_registry_resolution")),
        "entry_ap0_gate_only": bool(entry_ap0.get("entry_gate_only", True)),
        "entry_ap0_green": bool(entry_ap0.get("green")),
        "final_ap0_decision_connected": bool(final_ap0),
        "final_ap0_decision_ready": bool(final_ap0.get("decision_ready") or final_ap0.get("ready")),
        "final_ap0_uses_post_generation_results": True,
        "final_ap0_green": bool(final_ap0.get("green")),
        "final_ap0_can_proceed_to_a1": bool(final_ap0.get("can_proceed_to_a1")),
        "final_ap0_can_proceed_to_complete_initial": bool(
            final_ap0.get("can_proceed_to_complete_initial")
            or final_ap0.get("can_proceed_to_a1")
        ),
        "final_ap0_decision": str(final_ap0.get("decision") or ""),
        "final_ap0_next_step": str(final_ap0.get("next_step") or ""),
        "final_ap0_return_steps": final_return_steps,
        "final_ap0_unmet_checks": final_unmet_checks,
        "complete_initial_ap0_report_connected": bool(report),
        "complete_initial_ap0_release_blocker_count": _safe_step6_int(
            report.get("release_blocker_count"),
            len(report_blockers),
        ),
        "complete_initial_ap0_release_blockers": report_blockers,
        "scorecard_event_connected": scorecard_event_connected,
        "scorecard_event_kind": str(scorecard_event.get("event_kind") or ""),
        "scorecard_observation_status": scorecard_display_status,
        "scorecard_candidate_generation_attempted": candidate_attempted,
        "scorecard_candidate_generated": candidate_generated,
        "scorecard_display_passed": display_passed,
        "scorecard_binding_pass": bool(scorecard_event.get("binding_pass")),
        "scorecard_binding_pass_rate": _safe_step6_float(scorecard_event.get("binding_pass_rate"), 0.0),
        "scorecard_template_major_count": _safe_step6_int(scorecard_event.get("template_major_count"), 0),
        "scorecard_safety_major_count": _safe_step6_int(scorecard_event.get("safety_major_count"), 0),
        "scorecard_coverage_group": coverage_group,
        "scorecard_top_rejection_reasons": scorecard_reasons,
        "scorecard_harness_connected": scorecard_harness_connected,
        "scorecard_ready": bool(scorecard_harness.get("scorecard_ready") or scorecard_harness.get("ready")),
        "scorecard_product_gate_evaluation": str(scorecard_harness.get("product_gate_evaluation") or ""),
        "scorecard_display_reach_rate": _safe_step6_float(scorecard_harness.get("display_reach_rate"), 0.0),
        "scorecard_harness_step": str(scorecard_harness.get("step") or ""),
        "next_improvement_meta_visible": True,
        "next_improvement_return_steps": final_return_steps,
        "next_improvement_reasons": improvement_reasons,
        "next_improvement_coverage_group": coverage_group,
        "next_improvement_meta": next_improvement_meta,
        "comment_text_contract": "passed_only",
        "passed_only_comment_text_contract_preserved": True,
        "public_comment_text_assigned_by_step6": False,
        "display_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "fixed_fallback_used": False,
        "fallback_observation_sentence_added": False,
        "fixed_string_renderer_used": False,
        "external_ai_used": False,
        "local_llm_used": False,
        "raw_input_included": False,
        "generated_candidate_text_included": False,
        "candidate_text_included": False,
        "response_shape_changed": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_title_changed": False,
    }


def _attach_step6_complete_initial_final_ap0_scorecard_meta(
    *,
    diagnostic_summary: Dict[str, Any],
    phase_gate_meta: Dict[str, Any],
    step18_ap0_migration_decision: Dict[str, Any],
    complete_composer_initial_ap0_report: Dict[str, Any],
    complete_scorecard_event: Dict[str, Any],
    step12_complete_scorecard_harness: Dict[str, Any],
) -> Dict[str, Any]:
    step6_meta = _build_step6_complete_initial_final_ap0_scorecard_connection_meta(
        diagnostic_summary=diagnostic_summary,
        step18_ap0_migration_decision=step18_ap0_migration_decision,
        complete_composer_initial_ap0_report=complete_composer_initial_ap0_report,
        complete_scorecard_event=complete_scorecard_event,
        step12_complete_scorecard_harness=step12_complete_scorecard_harness,
    )
    next_improvement_meta = dict(step6_meta.get("next_improvement_meta") or {})
    final_ap0 = dict(step18_ap0_migration_decision or {})
    final_report = dict(complete_composer_initial_ap0_report or {})
    scorecard_event = dict(complete_scorecard_event or {})
    scorecard_harness = dict(step12_complete_scorecard_harness or {})

    diagnostic_summary["step6_final_ap0_scorecard_connection"] = step6_meta
    diagnostic_summary["complete_initial_final_ap0_scorecard_connection"] = step6_meta
    diagnostic_summary["complete_initial_final_ap0_scorecard"] = step6_meta
    diagnostic_summary["complete_initial_final_ap0_decision"] = final_ap0
    diagnostic_summary["complete_initial_final_ap0_report"] = final_report
    diagnostic_summary["complete_initial_final_scorecard_event"] = scorecard_event
    diagnostic_summary["complete_initial_final_scorecard_harness"] = scorecard_harness
    diagnostic_summary["complete_initial_next_improvement_meta"] = next_improvement_meta
    diagnostic_summary["step6_next_improvement_meta"] = next_improvement_meta
    diagnostic_summary["step6_final_ap0_scorecard_connected"] = True
    diagnostic_summary["complete_initial_final_ap0_scorecard_connected"] = True

    phase_gate_meta["step6_final_ap0_scorecard_connection_ready"] = True
    phase_gate_meta["step6_final_ap0_scorecard_connected"] = True
    phase_gate_meta["step6_final_ap0_decision_ready"] = bool(step6_meta.get("final_ap0_decision_ready"))
    phase_gate_meta["step6_final_ap0_green"] = bool(step6_meta.get("final_ap0_green"))
    phase_gate_meta["step6_final_ap0_decision"] = str(step6_meta.get("final_ap0_decision") or "")
    phase_gate_meta["step6_final_ap0_return_steps"] = list(step6_meta.get("final_ap0_return_steps") or [])
    phase_gate_meta["step6_scorecard_event_connected"] = bool(step6_meta.get("scorecard_event_connected"))
    phase_gate_meta["step6_scorecard_harness_connected"] = bool(step6_meta.get("scorecard_harness_connected"))
    phase_gate_meta["step6_scorecard_ready"] = bool(step6_meta.get("scorecard_ready"))
    phase_gate_meta["step6_scorecard_candidate_generated"] = bool(step6_meta.get("scorecard_candidate_generated"))
    phase_gate_meta["step6_scorecard_display_passed"] = bool(step6_meta.get("scorecard_display_passed"))
    phase_gate_meta["step6_scorecard_binding_pass"] = bool(step6_meta.get("scorecard_binding_pass"))
    phase_gate_meta["step6_scorecard_coverage_group"] = str(step6_meta.get("scorecard_coverage_group") or "")
    phase_gate_meta["step6_next_improvement_meta_visible"] = bool(step6_meta.get("next_improvement_meta_visible"))
    phase_gate_meta["step6_next_improvement_reasons"] = list(step6_meta.get("next_improvement_reasons") or [])
    phase_gate_meta["step6_public_response_shape_preserved"] = not bool(step6_meta.get("response_shape_changed"))
    phase_gate_meta["step6_passed_only_contract_preserved"] = bool(step6_meta.get("passed_only_comment_text_contract_preserved"))
    phase_gate_meta["step6_raw_input_included"] = bool(step6_meta.get("raw_input_included"))
    phase_gate_meta["step6_display_gate_relaxed"] = bool(step6_meta.get("display_gate_relaxed"))
    return step6_meta


def _dedupe_reason_codes(values: Any) -> List[str]:
    out: List[str] = []
    for value in list(values or []):
        reason = str(value or "").strip()
        if reason and reason not in out:
            out.append(reason)
    return out


def _gate_reason_category_for_summary(gate_key: str, reason: str) -> str:
    value = str(reason or "").strip()
    if not value or value == "passed":
        return "passed"
    if gate_key == "reader":
        if "addressee" in value:
            return "reader_addressee"
        if "speaker" in value or "person" in value or "pronoun" in value or "hijack" in value:
            return "reader_speaker_integrity"
        if "too_short" in value or "too_long" in value or "empty" in value or "unclear" in value:
            return "reader_readability"
        if "report" in value or "listing" in value:
            return "reader_report_like"
        if "relation" in value:
            return "reader_relation"
        return "reader_general"
    if gate_key == "grounding":
        if "diagnosis" in value or "personality" in value or "overclaim" in value:
            return "grounding_overclaim"
        if "general_knowledge" in value:
            return "grounding_general_knowledge_completion"
        if "unsupported" in value or "no_evidence" in value:
            return "grounding_unsupported"
        if "relation" in value:
            return "grounding_relation"
        if "evidence" in value or "graph" in value or "scope" in value:
            return "grounding_evidence"
        if "empty" in value:
            return "grounding_empty_text"
        return "grounding_general"
    if gate_key == "template_echo":
        if "diagnosis" in value or "personality" in value or "overclaim" in value:
            return "template_echo_overclaim"
        if "general_knowledge" in value:
            return "template_echo_general_knowledge_completion"
        if "raw" in value or "quote" in value or "copy" in value or "echo" in value:
            return "template_echo_raw_copy"
        if "repeated" in value or "surface" in value or "template" in value or "fixed" in value:
            return "template_echo_repetition"
        if "emotion_label" in value or "unfinished" in value or "quality" in value:
            return "template_echo_quality"
        return "template_echo_general"
    if gate_key in {"visible_surface_acceptance", "visible_surface_acceptance_gate"}:
        if "malformed" in value or "phrase_unit" in value:
            return "visible_surface_malformed"
        if "emotion_focus" in value or "secondary" in value:
            return "visible_surface_emotion_focus"
        if "positive_tone" in value or "burden" in value:
            return "visible_surface_tone"
        if "action" in value or "classification" in value:
            return "visible_surface_action"
        return "visible_surface_general"
    if gate_key == "display":
        if "empty_comment" in value or "comment" in value:
            return "display_empty_comment"
        if "source" in value or "composer" in value:
            return "display_source"
        if "phase" in value:
            return "display_phase"
        if "reader" in value:
            return "display_reader"
        if "ground" in value or "evidence" in value:
            return "display_grounding"
        if "template" in value or "echo" in value:
            return "display_template_echo"
        if "safety" in value:
            return "display_safety"
        return "display_general"
    return "gate_general"


def _gate_diagnostics_from_trace(gate: Dict[str, Any], gate_key: str) -> Dict[str, Any]:
    if gate_key == "reader":
        keys = (
            "understandable",
            "addressee_clear",
            "speaker_integrity_ok",
            "conversational",
            "report_like",
            "confidence",
            "relation_surface_contract_version",
            "reader_relation_signal_detected",
            "reader_relation_signal_count",
            "reader_relation_signal_keys",
            "reader_relation_signal_relation_types",
            "expected_relation_types",
            "reader_relation_signal_raw_input_included",
            "binding_used",
            "binding_present",
            "binding_available",
            "binding_missing",
            "binding_required",
            "binding_count",
            "sentence_count",
            "expected_binding_count",
            "binding_version",
            "step7_gate_binding_reflection",
        )
    elif gate_key == "grounding":
        keys = (
            "coverage_ratio",
            "sentence_count",
            "unsupported_sentence_count",
            "grounding_scope",
            "allowed_evidence_span_count",
            "ignored_evidence_span_count",
            "binding_aware_grounding",
            "binding_present",
            "binding_available",
            "binding_used",
            "binding_missing",
            "binding_required",
            "binding_count",
            "expected_binding_count",
            "binding_version",
            "binding_supported_sentence_count",
            "step6_binding_aware_grounding",
            "step7_gate_binding_reflection",
            "step14_guard_rejection_reasons",
            "step14_guard_strengthening",
            "confidence",
        )
    elif gate_key == "template_echo":
        keys = (
            "matched_banned_patterns",
            "max_old_template_similarity",
            "max_previous_output_similarity",
            "raw_echo_ratio",
            "repeated_sentence_pattern_score",
            "max_sentence_echo_ratio",
            "raw_quote_span_count",
            "raw_copy_sentence_ratio",
            "limited_surface_repetition_score",
            "abstract_repetition_score",
            "abstract_phrase_repetition_score",
            "raw_quote_char_ratio",
            "matched_limited_surface_patterns",
            "phase8_emotion_label_body_line_count",
            "phase8_missing_must_keep_roles",
            "phase8_quality_rejection_reasons",
            "binding_used",
            "binding_present",
            "binding_available",
            "binding_missing",
            "binding_required",
            "binding_count",
            "sentence_count",
            "expected_binding_count",
            "binding_version",
            "step7_gate_binding_reflection",
            "step14_guard_rejection_reasons",
            "step14_guard_strengthening",
        )
    elif gate_key == "visible_surface_acceptance_gate":
        keys = (
            "evaluated",
            "classification",
            "action",
            "rerender_recommended",
            "reroute_low_information_recommended",
            "visible_header_dominant_emotion_present",
            "visible_header_dominant_emotion_source",
            "opening_emotion_focus_present",
            "dominant_emotion_bridge_present",
            "selected_emotion_count",
            "secondary_emotion_focus_detected",
            "unselected_emotion_focus_detected",
            "negative_text_anchor_present",
            "positive_tone_profile",
            "burden_surface_without_anchor_detected",
            "malformed_nominalization_detected",
            "malformed_nominalization_codes",
            "koto_splice_detected",
            "koto_splice_codes",
            "relation_skeleton_marker_count",
            "relation_skeleton_marker_codes",
            "relation_skeleton_major",
            "analytic_register_leak_count",
            "analytic_register_leak_codes",
            "analytic_register_leak",
            "surface_repair_requested",
            "repair_reason_family",
            "raw_input_included",
            "comment_text_body_included",
            "display_gate_relaxed",
        )
    elif gate_key == "display":
        keys = (
            "observation_status",
            "comment_text_allowed",
            "comment_text_present",
            "binding_used",
            "binding_present",
            "binding_available",
            "binding_missing",
            "binding_required",
            "binding_count",
            "sentence_count",
            "expected_binding_count",
            "binding_version",
            "step7_gate_binding_reflection",
        )
    else:
        keys = ()
    diagnostics = {key: deepcopy(gate.get(key)) for key in keys if key in gate}
    if gate_key == "template_echo":
        # Step05 diagnostic meta keeps counts/codes only and avoids raw quoted user fragments.
        diagnostics["matched_raw_quote_fragment_count"] = len(list(gate.get("matched_raw_quote_fragments") or []))
        diagnostics["matched_banned_pattern_count"] = len(list(gate.get("matched_banned_patterns") or []))
        diagnostics["matched_limited_surface_pattern_count"] = len(list(gate.get("matched_limited_surface_patterns") or []))
        diagnostics["phase8_missing_must_keep_role_count"] = len(list(gate.get("phase8_missing_must_keep_roles") or []))
        diagnostics["phase8_quality_rejection_reason_count"] = len(list(gate.get("phase8_quality_rejection_reasons") or []))
    return diagnostics


def _gate_result_from_trace(gate_trace: Dict[str, Any], key: str) -> DiagnosticGateResult:
    gate = gate_trace.get(key) if isinstance(gate_trace, dict) else None
    public_key = "display" if key == "display_gate" else key
    if not isinstance(gate, dict):
        return DiagnosticGateResult(
            passed=False,
            rejection_reasons=["gate_trace_missing"],
            primary_reason="gate_trace_missing",
            reason_category="gate_trace_missing",
            diagnostics={},
        )
    reasons = _dedupe_reason_codes(gate.get("rejection_reasons") or [])
    passed = bool(gate.get("passed"))
    primary_reason = str(gate.get("primary_reason") or ("passed" if passed else _first_reason(reasons, default=f"{public_key}_failed")))
    reason_category = str(gate.get("reason_category") or _gate_reason_category_for_summary(public_key, primary_reason))
    return DiagnosticGateResult(
        passed=passed,
        rejection_reasons=reasons,
        primary_reason=primary_reason,
        reason_category=reason_category,
        diagnostics=_gate_diagnostics_from_trace(gate, public_key),
    )


def _first_reason(*groups: Any, default: str = "unknown") -> str:
    for group in groups:
        for reason in _dedupe_reason_codes(group):
            return reason
    return default


def _diagnostic_gate_results(gate_trace: Dict[str, Any]) -> Dict[str, DiagnosticGateResult]:
    return {
        "reader": _gate_result_from_trace(gate_trace, "reader"),
        "grounding": _gate_result_from_trace(gate_trace, "grounding"),
        "template_echo": _gate_result_from_trace(gate_trace, "template_echo"),
        "visible_surface_acceptance": _gate_result_from_trace(gate_trace, "visible_surface_acceptance_gate"),
        "display": _gate_result_from_trace(gate_trace, "display_gate"),
    }


def _build_gate_diagnostic_summary(
    *,
    gate_results: Dict[str, DiagnosticGateResult],
    observation_status: str,
    composer_status: str,
) -> Dict[str, Any]:
    order = ["reader", "grounding", "template_echo", "visible_surface_acceptance", "display"]
    gate_meta = {key: value.as_meta() for key, value in dict(gate_results or {}).items()}
    failed_gates: List[str] = []
    gate_primary_reasons: Dict[str, str] = {}
    gate_rejection_reasons: Dict[str, List[str]] = {}
    first_failed_gate = ""
    first_failed_reason = ""
    first_failed_category = ""
    for key in order:
        result = gate_results.get(key)
        if result is None:
            continue
        gate_primary_reasons[key] = result.primary_reason or ("passed" if result.passed else f"{key}_failed")
        gate_rejection_reasons[key] = list(result.rejection_reasons or [])
        if not bool(result.passed):
            failed_gates.append(key)
            if not first_failed_gate:
                first_failed_gate = key
                first_failed_reason = result.primary_reason or _first_reason(result.rejection_reasons, default=f"{key}_failed")
                first_failed_category = result.reason_category or _gate_reason_category_for_summary(key, first_failed_reason)
    reason_codes = _dedupe_reason_codes(
        reason
        for key in order
        for reason in list((gate_results.get(key) or DiagnosticGateResult(False)).rejection_reasons or [])
    )
    reason_categories = _dedupe_reason_codes(
        (gate_results.get(key).reason_category if gate_results.get(key) is not None else "")
        for key in order
        if gate_results.get(key) is not None
    )
    display_result = gate_results.get("display")
    display_reason = ""
    display_category = ""
    if display_result is not None and not bool(display_result.passed):
        display_reason = str(display_result.primary_reason or _first_reason(display_result.rejection_reasons, default="display_failed"))
        display_category = str(display_result.reason_category or _gate_reason_category_for_summary("display", display_reason))
        # Phase18-7: visible-surface diagnostics can be nested in the same trace
        # as the final display decision.  When the final decision is the display
        # phase itself (for example ``phase_not_complete``), report display as
        # the failed stage only if no terminal upstream gate has already failed.
        upstream_terminal_gate_failed = any(gate in failed_gates for gate in ("reader", "grounding", "template_echo"))
        if (not upstream_terminal_gate_failed) and (first_failed_gate in {"", "visible_surface_acceptance"}) and (display_reason == "phase_not_complete" or display_category == "display_phase"):
            first_failed_gate = "display"
            first_failed_reason = display_reason
            first_failed_category = display_category

    # Phase18-7: a visible-surface yellow/warn report is diagnostic signal, not
    # a terminal display failure.  Keep the raw gate result visible in meta, but
    # do not let it make a final passed reply look failed.
    if str(observation_status or "") == "passed":
        failed_gates = []
        first_failed_gate = ""
        first_failed_reason = ""
        first_failed_category = ""

    return {
        "version": "emlis.gate_diagnostic.v1",
        "gate_order": order,
        "gate_results": gate_meta,
        "gate_primary_reasons": gate_primary_reasons,
        "gate_rejection_reasons": gate_rejection_reasons,
        "failed_gates": failed_gates,
        "all_gates_passed": not bool(failed_gates) if str(observation_status or "") == "passed" else all(bool(gate_results.get(key) and gate_results[key].passed) for key in order),
        "first_failed_gate": first_failed_gate,
        "first_failed_reason": first_failed_reason,
        "first_failed_category": first_failed_category,
        "reader_passed": bool(gate_results.get("reader") and gate_results["reader"].passed),
        "grounding_passed": bool(gate_results.get("grounding") and gate_results["grounding"].passed),
        "template_echo_passed": bool(gate_results.get("template_echo") and gate_results["template_echo"].passed),
        "display_passed": bool(gate_results.get("display") and gate_results["display"].passed),
        "display_observation_status": observation_status,
        "generated_but_not_displayed": bool(str(composer_status or "") == "generated" and str(observation_status or "") != "passed"),
        "reason_codes": reason_codes,
        "reason_categories": reason_categories,
        "coverage_matrix_hints": [first_failed_category] if first_failed_category else (["gate_passed"] if observation_status == "passed" else ["gate_not_classified"]),
    }


def _reason_count_map(values: Any) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for value in list(values or []):
        reason = str(value or "").strip()
        if reason:
            counts[reason] = int(counts.get(reason, 0)) + 1
    return counts


def _scope_reason_category(reason: str) -> str:
    value = str(reason or "").strip().lower()
    if not value:
        return "unknown"
    if "safety" in value:
        return "safety_boundary"
    if "required_structure" in value or "structure" in value:
        return "required_structure"
    if "no_current_input" in value or "missing" in value:
        return "minimum_claim"
    if "primary" in value:
        return "primary_state"
    if "evidence" in value or "ground" in value or "confidence" in value:
        return "evidence_grounding"
    if "relation" in value or "tension" in value:
        return "relation_complexity"
    if "claim_limit" in value or "optional_claim_limit" in value:
        return "scope_complexity"
    if "structured_label" in value:
        return "structured_label"
    return "scope_general"


def _scope_reason_categories(values: Any) -> List[str]:
    out: List[str] = []
    for value in list(values or []):
        category = _scope_reason_category(str(value or ""))
        if category and category not in out:
            out.append(category)
    return out


def _scope_coverage_matrix_hint(*, scope_status: str, coverage_scope: str, reason_codes: List[str]) -> str:
    if scope_status == "safety_blocked" or any("safety" in reason for reason in reason_codes):
        return "safety_boundary"
    if scope_status == "eligible":
        return "partial_observation" if coverage_scope == "partial_observation" else "current_input_core"
    categories = _scope_reason_categories(reason_codes)
    if "required_structure" in categories:
        return "required_structure"
    if "primary_state" in categories or "evidence_grounding" in categories:
        return "current_input_core_evidence"
    if "relation_complexity" in categories:
        return "core_tension"
    if "scope_complexity" in categories:
        return "scope_complexity"
    if scope_status:
        return scope_status
    return "not_evaluated"


def _scope_diagnostic_meta(*, scope_meta: Dict[str, Any], gate_trace: Dict[str, Any]) -> Dict[str, Any]:
    """Build Step 03 developer-facing scope diagnostics.

    This payload stays in meta only. It classifies why the limited scope was
    eligible, out_of_scope, or safety_blocked without adding user-facing text or
    weakening the fail-closed display gate.
    """

    scope_meta = scope_meta if isinstance(scope_meta, dict) else {}
    safety_gate = gate_trace.get("safety") if isinstance(gate_trace, dict) else {}
    safety_reason_codes = _dedupe_reason_codes(
        safety_gate.get("rejection_reasons") if isinstance(safety_gate, dict) else []
    )
    if not scope_meta:
        coverage_hint = "safety_boundary" if safety_reason_codes else "not_evaluated"
        categories = _scope_reason_categories(safety_reason_codes)
        return {
            "version": "emlis.scope_diagnostic.v1",
            "scope_attempted": False,
            "scope_status": "safety_blocked" if safety_reason_codes else "",
            "coverage_scope": "current_input_core" if safety_reason_codes else "",
            "scope_ready_for_composer": False,
            "included_claim_count": 0,
            "included_relation_count": 0,
            "excluded_claim_count": 0,
            "rejection_reasons": safety_reason_codes,
            "safety_reason_codes": safety_reason_codes,
            "safety_boundaries": safety_reason_codes,
            "missing_information": [],
            "excluded_reason_codes": [],
            "excluded_reason_counts": {},
            "excluded_source_counts": {},
            "scoped_claim_counts": {},
            "scoped_optional_claim_count": 0,
            "reason_codes": safety_reason_codes,
            "reason_categories": categories,
            "reason_category": categories[0] if categories else "",
            "coverage_matrix_hint": coverage_hint,
            "coverage_matrix_hints": [coverage_hint] if coverage_hint else [],
            "coverage_groups": [],
            "scope_expansion": {},
            "safety_boundary": {
                "version": "emlis.scope_safety_boundary.v1",
                "requires_block": bool(safety_reason_codes),
                "blocked_before_composer": bool(safety_reason_codes),
                "reason_codes": safety_reason_codes,
                "safety_boundaries": safety_reason_codes,
                "comment_text_allowed": False if safety_reason_codes else None,
                "composer_must_not_run": bool(safety_reason_codes),
            },
            "safety_pre_generation_block": {
                "version": "emlis.safety_pre_generation_block.v1",
                "target_step": "Step10_safety_boundary",
                "phase": "B-S1",
                "blocked_before_composer": bool(safety_reason_codes),
                "composer_generation_allowed": False if safety_reason_codes else True,
                "comment_text_allowed": False,
                "fixed_reply_allowed": False,
                "fallback_observation_allowed": False,
                "raw_user_text_included": False,
                "primary_reason": "safety_boundary" if safety_reason_codes else "",
            },
            "out_of_scope_reason": safety_reason_codes[0] if safety_reason_codes else "",
        }

    nested = scope_meta.get("scope_diagnostic") if isinstance(scope_meta.get("scope_diagnostic"), dict) else {}
    scope_status = str(scope_meta.get("scope_status") or nested.get("scope_status") or "")
    coverage_scope = str(scope_meta.get("coverage_scope") or nested.get("coverage_scope") or "")
    included_claim_ids = [str(v) for v in list(scope_meta.get("included_claim_ids") or nested.get("included_claim_ids") or []) if str(v)]
    included_relation_ids = [str(v) for v in list(scope_meta.get("included_relation_ids") or nested.get("included_relation_ids") or []) if str(v)]
    excluded_claims = list(scope_meta.get("excluded_claims") or nested.get("excluded_claims") or [])
    excluded_reason_codes: List[str] = []
    excluded_sources: List[str] = []
    for item in excluded_claims:
        if not isinstance(item, dict):
            continue
        reason = str(item.get("reason_code") or "").strip()
        source = str(item.get("source") or "").strip()
        if reason:
            excluded_reason_codes.append(reason)
        if source:
            excluded_sources.append(source)

    nested_excluded = nested.get("excluded_reason_codes") if isinstance(nested.get("excluded_reason_codes"), list) else []
    excluded_reason_codes = _dedupe_reason_codes([
        *(scope_meta.get("excluded_reason_codes") or []),
        *nested_excluded,
        *excluded_reason_codes,
    ])
    rejection_reasons = _dedupe_reason_codes([*(scope_meta.get("rejection_reasons") or []), *(nested.get("rejection_reasons") or []), *safety_reason_codes])
    missing_information = _dedupe_reason_codes([*(scope_meta.get("missing_information") or []), *(nested.get("missing_information") or [])])
    safety_boundaries = _dedupe_reason_codes([*(scope_meta.get("safety_boundaries") or []), *(nested.get("safety_boundaries") or [])])
    scope_expansion = scope_meta.get("scope_expansion") if isinstance(scope_meta.get("scope_expansion"), dict) else nested.get("scope_expansion") if isinstance(nested.get("scope_expansion"), dict) else {}
    safety_boundary = scope_meta.get("safety_boundary") if isinstance(scope_meta.get("safety_boundary"), dict) else nested.get("safety_boundary") if isinstance(nested.get("safety_boundary"), dict) else {}
    safety_pre_generation_block = (
        scope_meta.get("safety_pre_generation_block")
        if isinstance(scope_meta.get("safety_pre_generation_block"), dict)
        else nested.get("safety_pre_generation_block")
        if isinstance(nested.get("safety_pre_generation_block"), dict)
        else {}
    )
    expansion_groups = scope_expansion.get("coverage_groups") if isinstance(scope_expansion, dict) else []
    safety_groups = safety_boundary.get("coverage_groups") if isinstance(safety_boundary, dict) else []
    coverage_groups = _dedupe_reason_codes([
        *(scope_meta.get("coverage_groups") or []),
        *(nested.get("coverage_groups") or []),
        *(expansion_groups if isinstance(expansion_groups, list) else []),
        *(safety_groups if isinstance(safety_groups, list) else []),
    ])
    safety_boundary_codes = list(safety_boundary.get("reason_codes") or []) if isinstance(safety_boundary, dict) else []
    safety_pre_generation_block = scope_meta.get("safety_pre_generation_block") if isinstance(scope_meta.get("safety_pre_generation_block"), dict) else nested.get("safety_pre_generation_block") if isinstance(nested.get("safety_pre_generation_block"), dict) else {}
    safety_boundaries = _dedupe_reason_codes([
        *safety_boundaries,
        *(safety_boundary.get("safety_boundaries") or [] if isinstance(safety_boundary, dict) else []),
    ])
    reason_codes = _dedupe_reason_codes([
        *rejection_reasons,
        *safety_reason_codes,
        *safety_boundary_codes,
        *missing_information,
        *excluded_reason_codes,
    ])
    categories = _scope_reason_categories(reason_codes)
    if not safety_pre_generation_block and (
        scope_status == "safety_blocked"
        or bool(safety_boundary.get("requires_block") if isinstance(safety_boundary, dict) else False)
        or bool(safety_boundary.get("blocked_before_composer") if isinstance(safety_boundary, dict) else False)
        or bool(safety_boundaries)
    ):
        safety_pre_generation_block = {
            "version": "emlis.safety_pre_generation_block.v1",
            "target_step": "Step10_safety_boundary",
            "policy": "scope_pre_composer_block",
            "scope_status": scope_status,
            "blocked_before_composer": True,
            "composer_generation_allowed": False,
            "fixed_reply_allowed": False,
            "fallback_observation_allowed": False,
            "comment_text_allowed": False,
            "normal_observation_allowed": False,
            "user_facing_text_allowed": False,
            "safety_boundaries": list(safety_boundaries or ["safety_boundary"]),
            "reason_codes": list(reason_codes or safety_reason_codes or ["safety_boundary"]),
            "evidence_span_ids": list(safety_boundary.get("evidence_span_ids") or []) if isinstance(safety_boundary, dict) else [],
            "coverage_groups": list(safety_boundary.get("coverage_groups") or []) if isinstance(safety_boundary, dict) else [],
            "raw_user_text_included": False,
        }
    coverage_hint = _scope_coverage_matrix_hint(
        scope_status=scope_status,
        coverage_scope=coverage_scope,
        reason_codes=reason_codes,
    )
    if isinstance(nested.get("coverage_matrix_hint"), str) and nested.get("coverage_matrix_hint"):
        coverage_hint = str(nested.get("coverage_matrix_hint"))

    return {
        "version": "emlis.scope_diagnostic.v1",
        "scope_attempted": True,
        "scope_status": scope_status,
        "coverage_scope": coverage_scope,
        "scope_ready_for_composer": bool(scope_status == "eligible"),
        "included_claim_ids": included_claim_ids,
        "included_relation_ids": included_relation_ids,
        "included_claim_count": int(scope_meta.get("included_claim_count") or nested.get("included_claim_count") or len(included_claim_ids)),
        "included_relation_count": int(scope_meta.get("included_relation_count") or nested.get("included_relation_count") or len(included_relation_ids)),
        "excluded_claims": excluded_claims,
        "excluded_claim_count": int(scope_meta.get("excluded_claim_count") or nested.get("excluded_claim_count") or len(excluded_claims)),
        "excluded_reason_codes": excluded_reason_codes,
        "excluded_reason_counts": dict(scope_meta.get("excluded_reason_counts") or nested.get("excluded_reason_counts") or _reason_count_map(excluded_reason_codes)),
        "excluded_source_counts": dict(nested.get("excluded_source_counts") or _reason_count_map(excluded_sources)),
        "rejection_reasons": rejection_reasons,
        "rejection_reason_count": int(scope_meta.get("rejection_reason_count") or nested.get("rejection_reason_count") or len(rejection_reasons)),
        "safety_reason_codes": safety_reason_codes,
        "safety_boundaries": safety_boundaries,
        "safety_boundary_count": int(scope_meta.get("safety_boundary_count") or nested.get("safety_boundary_count") or len(safety_boundaries)),
        "missing_information": missing_information,
        "missing_information_count": int(scope_meta.get("missing_information_count") or nested.get("missing_information_count") or len(missing_information)),
        "scoped_claim_counts": dict(scope_meta.get("scoped_claim_counts") or nested.get("scoped_claim_counts") or {}),
        "scoped_optional_claim_count": int(scope_meta.get("scoped_optional_claim_count") or nested.get("scoped_optional_claim_count") or 0),
        "min_reply_sentence_count": int(scope_meta.get("min_reply_sentence_count") or nested.get("min_reply_sentence_count") or 0),
        "max_reply_sentence_count": int(scope_meta.get("max_reply_sentence_count") or nested.get("max_reply_sentence_count") or 0),
        "reason_codes": reason_codes,
        "reason_categories": categories,
        "reason_category": categories[0] if categories else "",
        "coverage_matrix_hint": coverage_hint,
        "coverage_matrix_hints": [coverage_hint] if coverage_hint else [],
        "coverage_groups": coverage_groups,
        "scope_expansion": dict(scope_expansion or {}),
        "safety_boundary": dict(safety_boundary or {}) if isinstance(safety_boundary, dict) else {},
        "safety_pre_generation_block": dict(safety_pre_generation_block or {}) if isinstance(safety_pre_generation_block, dict) else {},
        "safety_blocked_before_composer": bool(
            scope_status == "safety_blocked"
            or (safety_boundary.get("blocked_before_composer") if isinstance(safety_boundary, dict) else False)
            or (safety_pre_generation_block.get("blocked_before_composer") if isinstance(safety_pre_generation_block, dict) else False)
        ),
        "safety_evidence_span_ids": list(safety_boundary.get("evidence_span_ids") or []) if isinstance(safety_boundary, dict) else [],
        "out_of_scope_reason": _first_reason(rejection_reasons, excluded_reason_codes, safety_reason_codes, safety_boundaries, missing_information, default="") if scope_status in {"out_of_scope", "safety_blocked"} else "",
    }



def _composer_diagnostic_meta(
    *,
    composer_candidate: Any = None,
    composer_reasons: List[str] | None = None,
    composer_status: str = "",
    composer_model: str = "",
    coverage_scope: str = "",
) -> Dict[str, Any]:
    """Step04 summary view for Composer-side stop reasons.

    Composer diagnostics are developer-facing meta. They distinguish scoped
    graph availability from text-material failures such as missing PhraseUnits,
    missing required roles, shallow evidence, unmatched profiles, or unavailable
    SentencePlans.
    """

    reasons = _dedupe_reason_codes(composer_reasons or [])
    candidate_meta = getattr(composer_candidate, "composer_meta", {}) or {}
    if not isinstance(candidate_meta, dict):
        candidate_meta = {}
    raw = candidate_meta.get("composer_diagnostic") if isinstance(candidate_meta.get("composer_diagnostic"), dict) else {}
    diagnostic = dict(raw or {})
    if not diagnostic:
        categories = _dedupe_reason_codes(
            _composer_reason_category_for_summary(reason)
            for reason in reasons
            if _composer_reason_category_for_summary(reason)
        )
        diagnostic = {
            "version": "emlis.composer_diagnostic.v1",
            "composer_attempted": bool(composer_candidate is not None),
            "composer_status": composer_status,
            "composer_ready_for_gate": bool(composer_status == "generated"),
            "coverage_scope": coverage_scope,
            "profile_key": str(candidate_meta.get("profile_key") or ""),
            "source_profile_key": str(candidate_meta.get("source_profile_key") or ""),
            "profile_matched": False,
            "profile_unmatched": False,
            "shallow_observation_path": bool(candidate_meta.get("shallow_observation_path")),
            "phrase_unit_count": int(candidate_meta.get("phrase_unit_count") or 0),
            "sentence_plan_count": int(candidate_meta.get("sentence_plan_count") or 0),
            "required_roles": list(candidate_meta.get("required_roles") or []),
            "available_roles": list(candidate_meta.get("available_roles") or []),
            "covered_roles": list(candidate_meta.get("covered_roles") or []),
            "missing_roles": list(candidate_meta.get("missing_roles") or []),
            "required_role_missing": bool("required_role_missing" in categories),
            "missing_phrase_units": bool("missing_phrase_units" in categories),
            "shallow_insufficient_evidence": bool("shallow_insufficient_evidence" in categories),
            "sentence_plan_unavailable": bool("sentence_plan_unavailable" in categories),
            "reason_codes": reasons,
            "reason_categories": categories,
            "reason_category": categories[0] if categories else "",
            "coverage_matrix_hints": categories or (["composer_generated"] if composer_status == "generated" else ["composer_not_classified"]),
            "stop_reason": categories[0] if composer_status != "generated" and categories else "",
        }
    diagnostic.setdefault("version", "emlis.composer_diagnostic.v1")
    diagnostic.setdefault("composer_status", composer_status)
    diagnostic.setdefault("composer_model", composer_model)
    diagnostic.setdefault("coverage_scope", coverage_scope)
    diagnostic.setdefault("reason_codes", reasons)
    diagnostic.setdefault("reason_categories", [])
    diagnostic.setdefault("coverage_matrix_hints", [])
    return diagnostic


def _composer_reason_category_for_summary(reason: str) -> str:
    value = str(reason or "").strip()
    if not value:
        return ""
    if "required_role" in value:
        return "required_role_missing"
    if "phrase_unit" in value:
        return "missing_phrase_units"
    if "short_ambiguous" in value or ("shallow" in value and ("evidence" in value or "empty" in value)):
        return "shallow_insufficient_evidence" if "evidence" in value or "ambiguous" in value else "sentence_plan_unavailable"
    if "profile_unmatched" in value:
        return "profile_unmatched"
    if "sentence_plan" in value or "empty_candidate" in value or "minimum_body" in value:
        return "sentence_plan_unavailable"
    if "quality" in value or "core" in value or "forbidden" in value:
        return "composer_quality"
    if "evidence" in value:
        return "composer_evidence"
    if "scope" in value:
        return "scope_not_eligible"
    if "graph" in value:
        return "missing_graph"
    return "composer_general"



def _b_plan_normal_connection_meta(
    *,
    resolution_meta: Dict[str, Any],
    release_decision: Dict[str, Any],
    rollout_decision: Dict[str, Any],
    rollout_metrics: Dict[str, Any],
    composer_candidate: Any,
    observation_status: str,
) -> Dict[str, Any]:
    """Step06 developer-facing B-plan normal connection contract.

    This meta fixes the normal ``composer_client=None`` route without changing
    user-facing output.  It lets QA distinguish environment / rollout blocking
    from Composer, Scope, or Gate failures after the default client is connected.
    """

    resolution_meta = resolution_meta if isinstance(resolution_meta, dict) else {}
    release_decision = release_decision if isinstance(release_decision, dict) else {}
    rollout_decision = rollout_decision if isinstance(rollout_decision, dict) else {}
    rollout_metrics = rollout_metrics if isinstance(rollout_metrics, dict) else {}

    explicit_client_used = bool(resolution_meta.get("explicit_client_used") or resolution_meta.get("explicit_client_provided"))
    default_client_used = bool(resolution_meta.get("default_client_used"))
    default_client_resolved = bool(resolution_meta.get("default_client_resolved") or default_client_used)
    default_connection_active = bool(resolution_meta.get("default_connection_active") or default_client_used)
    connection_status = str(resolution_meta.get("connection_status") or "")
    feature_flag_enabled = bool(
        resolution_meta.get("feature_flag_enabled")
        or resolution_meta.get("feature_enabled")
        or release_decision.get("feature_flag_enabled")
    )
    release_enabled = bool(release_decision.get("enabled"))
    release_allowed = resolution_meta.get("release_allowed")
    rollout_stage = str(release_decision.get("stage") or rollout_decision.get("stage") or "")
    release_reason_code = str(release_decision.get("reason_code") or rollout_decision.get("reason_code") or "")
    release_rejections = _dedupe_reason_codes([
        *(release_decision.get("rejection_reasons") or []),
        *(resolution_meta.get("rejection_reasons") or []),
    ])
    composer_model = str(
        resolution_meta.get("composer_model")
        or getattr(composer_candidate, "composer_model", "")
        or ""
    )
    composer_status = str(getattr(composer_candidate, "status", "") or "not_attempted")
    composer_connection_attempted = bool(explicit_client_used or default_connection_active)
    if not composer_connection_attempted and composer_status == "unavailable":
        composer_status = "not_attempted"
    safety_blocked = bool(resolution_meta.get("safety_blocked") or observation_status == "safety_blocked")

    if safety_blocked:
        route = "blocked_safety_route"
        decision = "blocked_safety"
        composer_connection_attempted = False
        if composer_status == "unavailable":
            composer_status = "not_attempted"
    elif explicit_client_used:
        route = "provided_client_route"
        decision = "provided_client"
    elif default_connection_active and release_enabled:
        route = "default_composer_route"
        decision = "default_composer_connected"
    elif not feature_flag_enabled:
        route = "default_composer_route"
        decision = "blocked_feature_flag"
    elif release_allowed is False or not release_enabled:
        route = "default_composer_route"
        if connection_status == "blocked_scope" or release_reason_code.startswith("scope_") or str(release_decision.get("cohort") or "") == "blocked_scope":
            decision = "blocked_scope"
        else:
            decision = "blocked_rollout"
    else:
        route = "default_composer_route"
        decision = "not_resolved"

    if safety_blocked:
        allowed_observation_statuses = ["safety_blocked"]
    elif composer_connection_attempted:
        allowed_observation_statuses = ["passed", "rejected", "unavailable"]
    else:
        allowed_observation_statuses = ["unavailable"]

    if explicit_client_used:
        release_registry_consistent = True
    elif safety_blocked:
        release_registry_consistent = bool(connection_status in {"blocked_safety", ""} and not default_client_used)
    elif not feature_flag_enabled:
        release_registry_consistent = bool(connection_status == "blocked_feature_flag" and not default_client_used)
    elif release_enabled:
        release_registry_consistent = bool(connection_status == "default_client_resolved" and default_client_resolved)
    elif decision == "blocked_scope":
        release_registry_consistent = bool(connection_status == "blocked_scope" and not default_client_used)
    else:
        release_registry_consistent = bool(connection_status == "blocked_rollout" and not default_client_used)

    rollout_attempted = bool(rollout_metrics.get("attempted") or release_decision.get("attempted") or release_enabled)
    rollout_release_consistent = bool(rollout_attempted == bool(release_decision.get("attempted") or release_enabled))
    environment_blocked = bool(decision in {"blocked_feature_flag", "blocked_rollout"})
    scope_blocked = bool(decision == "blocked_scope")
    generator_or_gate_path = bool(composer_connection_attempted and not safety_blocked)

    if observation_status == "passed":
        status_family = "passed"
    elif scope_blocked:
        status_family = "scope_blocked"
    elif environment_blocked:
        status_family = "environment_blocked"
    elif decision == "blocked_scope":
        status_family = "scope_blocked"
    elif generator_or_gate_path:
        status_family = "composer_or_gate"
    elif safety_blocked:
        status_family = "safety_blocked"
    else:
        status_family = "unavailable"

    return {
        "version": "emlis.b_plan_normal_connection.v1",
        "phase": "B-D1",
        "route": route,
        "decision": decision,
        "feature_flag_enabled": feature_flag_enabled,
        "rollout_stage": rollout_stage,
        "release_gate_allowed": release_enabled,
        "release_enabled": release_enabled,
        "release_allowed": release_allowed,
        "release_cohort": str(release_decision.get("cohort") or ""),
        "release_reason_code": release_reason_code,
        "release_rejection_reasons": release_rejections,
        "registry_connection_status": connection_status,
        "connection_status": connection_status,
        "environment_stop_stage": str(resolution_meta.get("pre_connection_stop_stage") or ""),
        "environment_stop_reason": _first_reason(release_rejections, default=release_reason_code or decision),
        "explicit_client_used": explicit_client_used,
        "default_client_used": default_client_used,
        "default_client_resolved": default_client_resolved,
        "default_connection_active": default_connection_active,
        "composer_connection_attempted": composer_connection_attempted,
        "composer_attempted": composer_connection_attempted,
        "composer_model": composer_model,
        "composer_model_expected": "cocolon_limited_composer.v1" if default_client_resolved else composer_model,
        "composer_status": composer_status,
        "observation_status": observation_status,
        "status_branch": observation_status,
        "allowed_observation_statuses": allowed_observation_statuses,
        "environment_blocked": environment_blocked,
        "environment_blocked_before_composer": bool(not composer_connection_attempted),
        "scope_blocked": scope_blocked,
        "generator_or_gate_path": generator_or_gate_path,
        "blocked_before_composer": bool(not composer_connection_attempted),
        "rollout_attempted": rollout_attempted,
        "release_registry_consistent": release_registry_consistent,
        "rollout_release_consistent": rollout_release_consistent,
        "diagnostic_consistent": bool(release_registry_consistent and rollout_release_consistent),
        "diagnostic_consistency": {
            "release_stage_matches_summary": bool(rollout_stage == str(release_decision.get("stage") or "")),
            "release_enabled_matches_summary": bool(release_enabled == bool(release_decision.get("enabled"))),
            "release_enabled_matches_rollout": bool(release_enabled == bool(rollout_decision.get("enabled"))),
            "release_attempt_matches_rollout_metrics": bool(bool(release_decision.get("attempted") or release_enabled) == bool(rollout_metrics.get("attempted"))),
            "composer_attempt_matches_registry": bool(composer_connection_attempted == bool(resolution_meta.get("composer_attempted") or composer_connection_attempted)),
            "registry_status_matches_default_resolution": bool(connection_status == str(resolution_meta.get("connection_status") or connection_status)),
        },
        "status_family": status_family,
    }

def _step7_surface_code_list(*values: Any) -> List[str]:
    return _dedupe_reason_codes([item for value in values for item in (value if isinstance(value, (list, tuple, set)) else [value])])


def _build_step7_public_feedback_diagnostic_summary(
    *,
    display_decision: Any,
    gate_trace: Dict[str, Any],
    phase_gate_meta: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Build Step7 code-only display absence diagnostics.

    This is internal diagnostic meta. It does not copy comment_text or raw input,
    does not relax any gate, and does not change the public response shape.
    """

    gate_trace = gate_trace if isinstance(gate_trace, dict) else {}
    phase_gate_meta = phase_gate_meta if isinstance(phase_gate_meta, dict) else {}
    runtime_gate = gate_trace.get("runtime_surface_pre_return_gate")
    runtime_gate = dict(runtime_gate or {}) if isinstance(runtime_gate, dict) else {}
    visible_gate = gate_trace.get("visible_surface_acceptance_gate")
    visible_gate = dict(visible_gate or {}) if isinstance(visible_gate, dict) else {}
    display_gate = gate_trace.get("display") or gate_trace.get("display_gate")
    display_gate = dict(display_gate or {}) if isinstance(display_gate, dict) else {}

    observation_status = str(getattr(display_decision, "observation_status", "") or "")
    comment_present = bool(str(getattr(display_decision, "comment_text", "") or "").strip())
    display_reasons = _dedupe_reason_codes(getattr(display_decision, "rejection_reasons", []) or [])
    runtime_reasons = _dedupe_reason_codes(runtime_gate.get("rejection_reasons") or [])
    visible_reasons = _dedupe_reason_codes(visible_gate.get("rejection_reasons") or [])
    reason_codes = _dedupe_reason_codes([*display_reasons, *runtime_reasons, *visible_reasons])
    visible_koto_codes = _step7_surface_code_list(
        visible_gate.get("koto_splice_codes"),
        visible_gate.get("malformed_nominalization_codes"),
        visible_gate.get("surface_malformed_nominalization_codes"),
    )
    runtime_koto_codes = _step7_surface_code_list(
        runtime_gate.get("koto_splice_codes"),
        runtime_gate.get("malformed_nominalization_codes"),
        runtime_gate.get("surface_malformed_nominalization_codes"),
    )
    relation_codes = _step7_surface_code_list(
        visible_gate.get("relation_skeleton_marker_codes"),
        visible_gate.get("analytic_register_leak_codes"),
    )

    candidate_blocked_koto_splice = bool(
        visible_gate.get("koto_splice_detected")
        or runtime_gate.get("koto_splice_detected")
        or visible_koto_codes
        or runtime_koto_codes
        or any("koto" in reason or reason.startswith("malformed_nominalization_") or reason == "residual_koto_splice_fragment" for reason in reason_codes)
    )
    candidate_blocked_relation_skeleton = bool(
        visible_gate.get("relation_skeleton_major")
        or visible_gate.get("analytic_register_leak")
        or relation_codes
        or any(reason.startswith("surface_relation_skeleton") or reason == "analytic_register_leak" for reason in reason_codes)
    )
    candidate_blocked_surface_grammar = bool(
        candidate_blocked_koto_splice
        or (runtime_gate and runtime_gate.get("passed") is False)
        or visible_gate.get("malformed_nominalization_detected")
        or any(
            reason in reason_codes
            for reason in (
                "runtime_surface_pre_return_gate_failed",
                "surface_grammar_warning",
                "malformed_phrase_unit",
                "surface_template_major",
            )
        )
    )
    candidate_repair_attempted = bool(
        runtime_gate.get("rerender_attempted")
        or visible_gate.get("rerender_attempted")
        or "bounded_visible_surface_rerender_required" in reason_codes
        or "bounded_shallow_v2_rerender_required" in reason_codes
    )
    normal_observation_rebuild_attempted = bool(
        phase_gate_meta.get("normal_observation_rebuild_attempted")
        or phase_gate_meta.get("normal_observation_rebuild_source_kind")
        == CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
        or phase_gate_meta.get("candidate_source_kind")
        == CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
        or phase_gate_meta.get("final_surface_origin_candidate_source_kind")
        == CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
    )
    normal_observation_rebuild_applied = bool(
        normal_observation_rebuild_attempted
        and (
            phase_gate_meta.get("normal_observation_rebuild_applied") is True
            or phase_gate_meta.get("applied") is True
            or phase_gate_meta.get("public_display_allowed_by_boundary") is True
        )
    )
    if normal_observation_rebuild_attempted:
        candidate_repair_attempted = True
    candidate_repair_succeeded = bool(
        (candidate_repair_attempted or normal_observation_rebuild_attempted)
        and observation_status == "passed"
        and comment_present
    )
    candidate_repair_failed = bool(candidate_repair_attempted and not candidate_repair_succeeded)
    public_feedback_not_included_non_passed = bool(observation_status != "passed")
    public_feedback_not_included_empty_comment_text = bool(not comment_present)
    display_gate_failed = bool(display_gate and display_gate.get("passed") is False)
    candidate_fail_closed_display_absent = bool(
        public_feedback_not_included_non_passed
        or public_feedback_not_included_empty_comment_text
        or candidate_blocked_surface_grammar
        or candidate_blocked_relation_skeleton
        or display_gate_failed
    )
    if not candidate_fail_closed_display_absent and observation_status == "passed" and comment_present:
        reason_family = "displayed"
    elif candidate_blocked_koto_splice:
        reason_family = "koto_splice"
    elif candidate_blocked_relation_skeleton:
        reason_family = "relation_skeleton"
    elif candidate_blocked_surface_grammar:
        reason_family = "surface_grammar"
    elif public_feedback_not_included_empty_comment_text:
        reason_family = "empty_comment_text"
    elif public_feedback_not_included_non_passed:
        reason_family = "non_passed"
    else:
        reason_family = "display_absent"

    return {
        "version": "emlis.step7.public_feedback_diagnostic_summary.v1",
        "candidate_blocked_surface_grammar": candidate_blocked_surface_grammar,
        "candidate_blocked_koto_splice": candidate_blocked_koto_splice,
        "candidate_blocked_relation_skeleton": candidate_blocked_relation_skeleton,
        "candidate_repair_attempted": candidate_repair_attempted,
        "candidate_repair_succeeded": candidate_repair_succeeded,
        "candidate_repair_failed": candidate_repair_failed,
        "candidate_fail_closed_display_absent": candidate_fail_closed_display_absent,
        "public_feedback_not_included_non_passed": public_feedback_not_included_non_passed,
        "public_feedback_not_included_empty_comment_text": public_feedback_not_included_empty_comment_text,
        "rn_payload_absent": candidate_fail_closed_display_absent,
        "reason_family": reason_family,
        "reason_codes": reason_codes[:20],
        "normal_observation_rebuild_attempted": normal_observation_rebuild_attempted,
        "normal_observation_rebuild_applied": normal_observation_rebuild_applied,
        "normal_observation_rebuild_source_kind": (
            CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
            if normal_observation_rebuild_attempted
            else ""
        ),
        "raw_input_included": False,
        "comment_text_body_included": False,
        "display_gate_relaxed": False,
    }


def _diagnostic_summary_meta(
    *,
    display_decision: Any,
    gate_trace: Dict[str, Any],
    resolution_meta: Dict[str, Any],
    release_meta: Dict[str, Any],
    scope_meta: Dict[str, Any],
    composer_candidate: Any = None,
    phase_gate: Dict[str, Any] | None = None,
    rollout_metrics: Dict[str, Any] | None = None,
    current_input: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Build the developer-facing Step 01 diagnostic summary.

    The summary intentionally stores only status codes, counts, and reason codes.
    It is safe to keep in meta because it does not add user-visible text and it
    does not contain hidden reasoning or example replies.
    """

    phase_gate = phase_gate if isinstance(phase_gate, dict) else {}
    rollout_metrics = rollout_metrics if isinstance(rollout_metrics, dict) else {}
    gate_results = _diagnostic_gate_results(gate_trace)
    runtime_surface_gate = gate_trace.get("runtime_surface_pre_return_gate") if isinstance(gate_trace, dict) else {}
    runtime_surface_gate = dict(runtime_surface_gate or {}) if isinstance(runtime_surface_gate, dict) else {}
    observation_status = str(getattr(display_decision, "observation_status", "") or "unavailable")
    display_reasons = _dedupe_reason_codes(getattr(display_decision, "rejection_reasons", []) or [])
    resolution_reasons = _dedupe_reason_codes(resolution_meta.get("rejection_reasons") or [])
    release_reasons = _dedupe_reason_codes(release_meta.get("rejection_reasons") or [])
    scope_diagnostic = _scope_diagnostic_meta(scope_meta=scope_meta, gate_trace=gate_trace)
    scope_reasons = _dedupe_reason_codes([
        *(scope_meta.get("rejection_reasons") or []),
        *(scope_diagnostic.get("safety_reason_codes") or []),
        *(scope_diagnostic.get("missing_information") or []),
        *(scope_diagnostic.get("reason_codes") or []),
    ])
    composer_reasons = _dedupe_reason_codes(getattr(composer_candidate, "rejection_reasons", []) or [])

    feature_flag_enabled = bool(
        resolution_meta.get("feature_flag_enabled")
        or resolution_meta.get("feature_enabled")
        or release_meta.get("feature_flag_enabled")
        or False
    )
    rollout_stage = str(release_meta.get("stage") or phase_gate.get("phase7_rollout_stage") or "")
    scope_status = str(scope_diagnostic.get("scope_status") or scope_meta.get("scope_status") or "")
    coverage_scope = str(
        scope_diagnostic.get("coverage_scope")
        or scope_meta.get("coverage_scope")
        or getattr(composer_candidate, "coverage_scope", "")
        or ""
    )
    composer_model = str(
        getattr(composer_candidate, "composer_model", "")
        or resolution_meta.get("composer_model")
        or ""
    )
    feature_flag_state = dict(resolution_meta.get("feature_flag_state") or {}) if isinstance(resolution_meta.get("feature_flag_state"), dict) else {}
    default_composer_resolution = dict(resolution_meta.get("default_composer_resolution") or {}) if isinstance(resolution_meta.get("default_composer_resolution"), dict) else {
        "resolution_source": str(resolution_meta.get("resolution_source") or resolution_meta.get("source") or ""),
        "explicit_client_used": bool(resolution_meta.get("explicit_client_used") or resolution_meta.get("explicit_client_provided")),
        "default_client_used": bool(resolution_meta.get("default_client_used")),
        "default_connection_active": bool(resolution_meta.get("default_connection_active") or resolution_meta.get("default_client_used")),
        "resolved_client_class": str(resolution_meta.get("resolved_client_class") or resolution_meta.get("resolved_client_name") or ""),
        "composer_model": str(resolution_meta.get("composer_model") or ""),
        "release_allowed": resolution_meta.get("release_allowed"),
        "safety_blocked": bool(resolution_meta.get("safety_blocked")),
        "connection_status": str(resolution_meta.get("connection_status") or ""),
        "pre_connection_stop_stage": str(resolution_meta.get("pre_connection_stop_stage") or ""),
        "composer_attempted": bool(resolution_meta.get("composer_attempted")),
        "default_client_resolved": bool(resolution_meta.get("default_client_resolved")),
    }
    release_decision = {
        "stage": str(release_meta.get("stage") or ""),
        "enabled": bool(release_meta.get("enabled")),
        "attempted": bool(release_meta.get("attempted") or release_meta.get("enabled")),
        "composer_attempt_allowed": bool(release_meta.get("composer_attempt_allowed") or release_meta.get("enabled")),
        "rollout_allowed": bool(release_meta.get("rollout_allowed") or release_meta.get("enabled")),
        "cohort": str(release_meta.get("cohort") or ""),
        "reason_code": str(release_meta.get("reason_code") or ""),
        "rejection_reasons": _dedupe_reason_codes(release_meta.get("rejection_reasons") or []),
        "internal_user": bool(release_meta.get("internal_user")),
        "tutorial_case": bool(release_meta.get("tutorial_case")),
        "limited_case": bool(release_meta.get("limited_case")),
        "scope_status": str(release_meta.get("scope_status") or ""),
        "scope_coverage": str(release_meta.get("scope_coverage") or ""),
        "feature_flag_enabled": bool(release_meta.get("feature_flag_enabled")),
        "stage_source": str(release_meta.get("stage_source") or ""),
    }
    composer_connection_attempted = bool(
        default_composer_resolution.get("explicit_client_used")
        or default_composer_resolution.get("default_client_used")
        or default_composer_resolution.get("default_connection_active")
        or resolution_meta.get("composer_attempted")
    )
    if bool(default_composer_resolution.get("safety_blocked") or resolution_meta.get("safety_blocked") or observation_status == "safety_blocked"):
        composer_connection_attempted = False
    rollout_attempted = bool(rollout_metrics.get("attempted") or release_decision.get("attempted") or release_decision.get("enabled"))
    rollout_decision = dict(release_meta.get("rollout_decision") or release_decision) if isinstance(release_meta, dict) else dict(release_decision)
    registry_resolution = {
        "default_registry_version": str(resolution_meta.get("default_registry_version") or ""),
        "connection_status": str(resolution_meta.get("connection_status") or default_composer_resolution.get("connection_status") or ""),
        "pre_connection_stop_stage": str(resolution_meta.get("pre_connection_stop_stage") or default_composer_resolution.get("pre_connection_stop_stage") or ""),
        "resolution_source": str(resolution_meta.get("resolution_source") or resolution_meta.get("source") or ""),
        "explicit_client_used": bool(resolution_meta.get("explicit_client_used") or resolution_meta.get("explicit_client_provided")),
        "default_client_used": bool(resolution_meta.get("default_client_used")),
        "default_client_resolved": bool(resolution_meta.get("default_client_resolved") or default_composer_resolution.get("default_client_resolved")),
        "composer_attempted": bool(resolution_meta.get("composer_attempted") or composer_connection_attempted),
        "blocked_before_composer": bool(resolution_meta.get("blocked_before_composer") if "blocked_before_composer" in resolution_meta else not composer_connection_attempted),
        "resolved_client_class": str(resolution_meta.get("resolved_client_class") or resolution_meta.get("resolved_client_name") or ""),
        "composer_model": str(resolution_meta.get("composer_model") or ""),
        "release_allowed": resolution_meta.get("release_allowed"),
        "rejection_reasons": _dedupe_reason_codes(resolution_meta.get("rejection_reasons") or []),
    }
    pre_connection = {
        "version": "emlis.pre_connection_diagnostic.v1",
        "feature_flag_enabled": feature_flag_enabled,
        "feature_flag_state": feature_flag_state,
        "rollout_stage": rollout_stage,
        "rollout_decision": rollout_decision,
        "release_decision": release_decision,
        "registry_resolution": registry_resolution,
        "default_composer_resolution": default_composer_resolution,
        "composer_connection_attempted": composer_connection_attempted,
        "rollout_attempted": rollout_attempted,
        "composer_attempted": composer_connection_attempted,
        "blocked_before_composer": bool(not composer_connection_attempted),
    }
    b_plan_connection = _b_plan_normal_connection_meta(
        resolution_meta=resolution_meta,
        release_decision=release_decision,
        rollout_decision=rollout_decision,
        rollout_metrics=rollout_metrics,
        composer_candidate=composer_candidate,
        observation_status=observation_status,
    )
    pre_connection["b_plan_connection"] = b_plan_connection
    raw_composer_status = str(getattr(composer_candidate, "status", "") or "not_attempted")
    if not composer_connection_attempted and raw_composer_status == "unavailable" and "composer_client_not_connected" in composer_reasons:
        composer_status = "not_attempted"
    else:
        composer_status = raw_composer_status
    composer_diagnostic = _composer_diagnostic_meta(
        composer_candidate=composer_candidate,
        composer_reasons=composer_reasons,
        composer_status=composer_status,
        composer_model=composer_model,
        coverage_scope=coverage_scope,
    )
    composer_reason_categories = _dedupe_reason_codes(composer_diagnostic.get("reason_categories") or [])
    composer_coverage_matrix_hints = _dedupe_reason_codes(composer_diagnostic.get("coverage_matrix_hints") or [])
    gate_diagnostic = _build_gate_diagnostic_summary(
        gate_results=gate_results,
        observation_status=observation_status,
        composer_status=composer_status,
    )
    gate_rejection_reasons = _dedupe_reason_codes(gate_diagnostic.get("reason_codes") or [])
    gate_coverage_matrix_hints = _dedupe_reason_codes(gate_diagnostic.get("coverage_matrix_hints") or [])
    used_evidence_span_count = len(list(getattr(composer_candidate, "used_evidence_span_ids", []) or []))
    included_claim_count = int(scope_diagnostic.get("included_claim_count") or 0)
    excluded_claim_count = int(scope_diagnostic.get("excluded_claim_count") or 0)
    comment_text_allowed = bool(phase_gate.get("comment_text_allowed"))

    safety_gate = gate_trace.get("safety") if isinstance(gate_trace, dict) else {}
    safety_reasons = _dedupe_reason_codes(safety_gate.get("rejection_reasons") if isinstance(safety_gate, dict) else [])

    stage = "display"
    primary_reason = "passed" if observation_status == "passed" else _first_reason(display_reasons, default=observation_status or "unavailable")

    explicit_client_used = bool(resolution_meta.get("explicit_client_used") or resolution_meta.get("explicit_client_provided"))
    default_client_used = bool(resolution_meta.get("default_client_used"))
    rollout_not_allowed = (
        "limited_composer_rollout_not_allowed" in resolution_reasons
        or "limited_composer_rollout_not_allowed" in release_reasons
        or str(release_meta.get("reason_code") or "") in {"rollout_stage_off", "rollout_stage_not_matched"}
    )

    if observation_status == "passed":
        stage = "display"
        primary_reason = "passed"
    elif observation_status == "safety_blocked" or safety_reasons or scope_status == "safety_blocked":
        stage = "scope"
        primary_reason = _first_reason(safety_reasons, scope_reasons, display_reasons, default="safety_blocked")
    elif (not explicit_client_used) and (not default_client_used) and (not feature_flag_enabled):
        stage = "flag"
        primary_reason = _first_reason(resolution_reasons, release_reasons, display_reasons, default="default_limited_composer_feature_disabled")
    elif scope_status and scope_status not in {"eligible"}:
        stage = "scope"
        primary_reason = _first_reason(scope_reasons, release_reasons, display_reasons, default=f"scope_{scope_status}")
    elif (not explicit_client_used) and rollout_not_allowed:
        stage = "rollout"
        primary_reason = _first_reason(resolution_reasons, release_reasons, display_reasons, default="limited_composer_rollout_not_allowed")
    elif composer_status != "generated" or "composer_source_unavailable" in display_reasons:
        stage = "composer"
        primary_reason = _first_reason(composer_reasons, resolution_reasons, display_reasons, default=composer_status or "composer_unavailable")
    else:
        for gate_key, gate_stage in (("reader", "reader"), ("grounding", "grounding"), ("template_echo", "template")):
            result = gate_results.get(gate_key)
            if result is not None and not result.passed:
                stage = gate_stage
                primary_reason = str(getattr(result, "primary_reason", "") or _first_reason(result.rejection_reasons, display_reasons, default=f"{gate_stage}_failed"))
                break
        else:
            stage = "display"
            primary_reason = _first_reason(display_reasons, default=observation_status or "display_gate")

    gate_primary_reasons = [
        str(getattr(result, "primary_reason", "") or "")
        for result in dict(gate_results or {}).values()
        if str(getattr(result, "primary_reason", "") or "") and str(getattr(result, "primary_reason", "") or "") != "passed"
    ]
    secondary_reasons = _dedupe_reason_codes(
        [
            *display_reasons,
            *resolution_reasons,
            *release_reasons,
            *scope_reasons,
            *composer_reasons,
            *gate_rejection_reasons,
            *gate_primary_reasons,
        ]
    )
    if primary_reason and primary_reason not in secondary_reasons:
        secondary_reasons.insert(0, primary_reason)

    summary = EmlisAIDiagnosticSummary(
        observation_status=observation_status,  # type: ignore[arg-type]
        stage=stage,  # type: ignore[arg-type]
        primary_reason=primary_reason,
        secondary_reasons=secondary_reasons,
        feature_flag_enabled=feature_flag_enabled,
        rollout_stage=rollout_stage,
        scope_status=scope_status,
        coverage_scope=coverage_scope,
        composer_model=composer_model,
        composer_status=composer_status,
        composer_diagnostic=composer_diagnostic,
        composer_rejection_reasons=composer_reasons,
        composer_reason_category=composer_reason_categories[0] if composer_reason_categories else "",
        composer_coverage_matrix_hints=composer_coverage_matrix_hints,
        gate_diagnostic=gate_diagnostic,
        gate_rejection_reasons=gate_rejection_reasons,
        gate_reason_category=str(gate_diagnostic.get("first_failed_category") or ("passed" if observation_status == "passed" else "")),
        gate_coverage_matrix_hints=gate_coverage_matrix_hints,
        gate_failure_stage=str(gate_diagnostic.get("first_failed_gate") or ""),
        safety_boundary=dict(scope_diagnostic.get("safety_boundary") or {}),
        feature_flag_state=feature_flag_state,
        release_enabled=bool(release_decision.get("enabled")),
        release_cohort=str(release_decision.get("cohort") or ""),
        release_reason_code=str(release_decision.get("reason_code") or ""),
        release_decision=release_decision,
        default_composer_resolution=default_composer_resolution,
        rollout_decision=rollout_decision,
        registry_resolution=registry_resolution,
        pre_connection=pre_connection,
        b_plan_connection=b_plan_connection,
        normal_connection=b_plan_connection,
        scope_diagnostic=scope_diagnostic,
        scope_rejection_reasons=list(scope_diagnostic.get("rejection_reasons") or []),
        scope_safety_boundaries=list(scope_diagnostic.get("safety_boundaries") or []),
        scope_excluded_reason_codes=list(scope_diagnostic.get("excluded_reason_codes") or []),
        scope_reason_category=str(scope_diagnostic.get("reason_category") or ""),
        scope_coverage_matrix_hints=list(scope_diagnostic.get("coverage_matrix_hints") or []),
        composer_connection_attempted=composer_connection_attempted,
        rollout_attempted=rollout_attempted,
        used_evidence_span_count=used_evidence_span_count,
        included_claim_count=included_claim_count,
        excluded_claim_count=excluded_claim_count,
        comment_text_allowed=comment_text_allowed,
        gate_results=gate_results,
    )
    summary_meta = summary.as_meta()
    if runtime_surface_gate:
        summary_meta["runtime_surface_pre_return_gate"] = runtime_surface_gate
        summary_meta["runtime_surface_pre_return_gate_evaluated"] = bool(runtime_surface_gate.get("evaluated"))
        summary_meta["runtime_surface_pre_return_gate_passed"] = bool(runtime_surface_gate.get("passed"))
        summary_meta["runtime_surface_pre_return_gate_action"] = str(runtime_surface_gate.get("action") or "")
        summary_meta["runtime_surface_pre_return_gate_rejection_reasons"] = list(runtime_surface_gate.get("rejection_reasons") or [])
        summary_meta["surface_template_major_blocked"] = "surface_template_major" in list(runtime_surface_gate.get("rejection_reasons") or [])
        summary_meta["malformed_phrase_unit_blocked_count"] = int(runtime_surface_gate.get("malformed_phrase_unit_count") or 0)
        summary_meta["raw_input_included"] = False
        summary_meta["comment_text_body_included"] = False
    taxonomy_meta = build_diagnostic_failure_taxonomy_meta(
        observation_status=summary_meta.get("observation_status"),
        stage=summary_meta.get("stage"),
        primary_reason=summary_meta.get("primary_reason"),
        secondary_reasons=summary_meta.get("secondary_reasons"),
        composer_status=summary_meta.get("composer_status"),
        gate_results=summary_meta.get("gate_results") if isinstance(summary_meta.get("gate_results"), Mapping) else {},
        gate_failure_stage=summary_meta.get("gate_failure_stage"),
        display_rejection_reasons=display_reasons,
        runtime_surface=runtime_surface_gate,
        display_absence_summary={},
        comment_text_allowed=summary_meta.get("comment_text_allowed"),
        comment_text_length=0,
    )
    summary_meta["diagnostic_failure_taxonomy"] = taxonomy_meta
    summary_meta["classification"] = taxonomy_meta["classification"]
    summary_meta["canonical_classification"] = taxonomy_meta["canonical_classification"]
    summary_meta["legacy_classification_aliases"] = list(taxonomy_meta.get("legacy_classification_aliases") or [])
    summary_meta["diagnostic_contract_version"] = _COMPLETE_PRODUCT_QUALITY_DIAGNOSTIC_CONTRACT_VERSION
    summary_meta["gate_binding_contract_version"] = GATE_BINDING_CONTRACT_VERSION
    limited_composer_baseline = build_limited_composer_extension_baseline_meta()
    connection_visibility = build_limited_composer_connection_visibility_meta(
        resolution_meta=resolution_meta,
        release_meta=release_meta,
        scope_meta=scope_meta,
        composer_candidate=composer_candidate,
        gate_results=gate_results,
        observation_status=observation_status,
        composer_status=composer_status,
    )
    summary_meta["limited_composer_extension_baseline"] = limited_composer_baseline
    summary_meta["step0_baseline"] = limited_composer_baseline
    summary_meta["connection_visibility"] = connection_visibility
    summary_meta["limited_composer_connection_visibility"] = connection_visibility
    summary_meta["step1_connection_visibility"] = connection_visibility
    coverage_matrix = build_emlis_coverage_matrix(
        diagnostic_summary=summary_meta,
        current_input=current_input or {},
    )
    summary_meta["coverage_matrix"] = coverage_matrix
    summary_meta["coverage_groups"] = list(coverage_matrix.get("coverage_groups") or [])
    summary_meta["coverage_primary_group"] = str(coverage_matrix.get("primary_coverage_group") or "")
    summary_meta["coverage_next_steps"] = list(coverage_matrix.get("next_steps") or [])
    summary_meta["coverage_unclassified_reasons"] = list(coverage_matrix.get("unclassified_reasons") or [])
    summary_meta["coverage_unmapped_reasons"] = list(coverage_matrix.get("unmapped_reason_codes") or coverage_matrix.get("unclassified_reasons") or [])
    binding_presence = build_limited_composer_binding_presence_meta(
        composer_candidate=composer_candidate,
    )
    step2_extension = build_limited_composer_diagnostic_summary_extension_meta(
        diagnostic_summary=summary_meta,
        coverage_matrix=coverage_matrix,
        binding_presence=binding_presence,
        gate_results=gate_results,
    )
    summary_meta["diagnostic_summary_extension"] = step2_extension
    summary_meta["diagnostic_summary_v2"] = step2_extension
    summary_meta["limited_composer_diagnostic_summary_extension"] = step2_extension
    summary_meta["step2_diagnostic_summary_extension"] = step2_extension
    summary_meta["failed_stage"] = str(step2_extension.get("failed_stage") or "")
    summary_meta["coverage_group"] = str(step2_extension.get("coverage_group") or "")
    summary_meta["binding_present"] = bool(step2_extension.get("binding_present"))
    summary_meta["binding_missing"] = bool(step2_extension.get("binding_missing"))
    summary_meta["binding_count"] = int(step2_extension.get("binding_count") or 0)
    summary_meta["expected_binding_count"] = int(step2_extension.get("expected_binding_count") or 0)
    summary_meta["binding_diagnostic"] = dict(step2_extension.get("binding") or step2_extension.get("binding_presence") or {})
    for gate_name, gate in dict(summary_meta.get("gate_results") or {}).items():
        if isinstance(gate, dict):
            gate_key = "display" if str(gate_name) == "display_gate" else str(gate_name)
            diagnostics = gate.get("diagnostics") if isinstance(gate.get("diagnostics"), dict) else {}
            step7_trace = diagnostics.get("step7_gate_binding_reflection") if isinstance(diagnostics.get("step7_gate_binding_reflection"), dict) else {}
            binding_present = bool(
                gate.get("binding_present")
                or diagnostics.get("binding_present")
                or step7_trace.get("binding_present")
                or step2_extension.get("binding_present")
            )
            binding_used = bool(
                gate_key in _BINDING_DECISION_GATES
                and (
                    gate.get("binding_used")
                    or diagnostics.get("binding_used")
                    or step7_trace.get("binding_used")
                )
            )
            binding_required = bool(
                gate_key in _BINDING_DECISION_GATES
                and (
                    gate.get("binding_required")
                    or diagnostics.get("binding_required")
                    or step7_trace.get("binding_required")
                    or (step2_extension.get("binding") or {}).get("binding_expected")
                )
            )
            binding_missing = bool(
                binding_required
                and (
                    gate.get("binding_missing")
                    or diagnostics.get("binding_missing")
                    or step7_trace.get("binding_missing")
                    or step2_extension.get("binding_missing")
                )
            )
            binding_count = int(
                gate.get("binding_count")
                or diagnostics.get("binding_count")
                or step7_trace.get("binding_count")
                or step2_extension.get("binding_count")
                or 0
            )
            binding_support_source = str(
                gate.get("binding_support_source")
                or diagnostics.get("binding_support_source")
                or step7_trace.get("binding_support_source")
                or ("display_binding_aware_result" if gate_key == "display" and binding_used else "declared_relation_binding" if gate_key == "grounding" and binding_used else "none")
            )
            gate["gate_binding_contract_version"] = GATE_BINDING_CONTRACT_VERSION
            gate["binding_contract_version"] = GATE_BINDING_CONTRACT_VERSION
            gate["binding_used"] = binding_used
            gate["binding_present"] = binding_present
            gate["binding_available"] = binding_present
            gate["binding_missing"] = binding_missing
            gate["binding_required"] = binding_required
            gate["binding_count"] = binding_count
            gate["expected_binding_count"] = int(
                gate.get("expected_binding_count")
                or diagnostics.get("expected_binding_count")
                or step7_trace.get("expected_binding_count")
                or step2_extension.get("expected_binding_count")
                or 0
            )
            gate["binding_support_source"] = binding_support_source
            if step7_trace:
                enriched_trace = dict(step7_trace)
                enriched_trace.setdefault("gate_binding_contract_version", GATE_BINDING_CONTRACT_VERSION)
                enriched_trace.setdefault("binding_contract_version", GATE_BINDING_CONTRACT_VERSION)
                enriched_trace.setdefault("binding_support_source", binding_support_source)
                gate["step7_gate_binding_reflection"] = enriched_trace
    return summary_meta


def _multi_perspective_meta(
    *,
    trace_id: str,
    capability: EmlisAICapabilityConfig,
    bundle: SourceBundle,
    evidence_spans: List[Any],
    reports: List[Any],
    board: Any,
    graph: Any,
    reader_report: Any,
    grounding_report: Any,
    template_echo_report: Any,
    display_decision: Any,
    composer_source: str = "",
    composer_candidate: Any = None,
    composer_client_resolution: Any = None,
    limited_observation_scope: Any = None,
    limited_release_decision: Any = None,
    grounding_graph: Any = None,
    grounding_scope: str = "full_graph",
    grounding_allowed_evidence_span_ids: Optional[List[str]] = None,
    complete_initial_pre_generation_seed: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    used_sources: List[str] = ["current_input"]
    if bundle.greeting:
        used_sources.append("greeting_state")
    if capability.include_input_summary:
        used_sources.append("input_summary")
    if capability.history_mode != "none" and (bundle.last_input or bundle.same_day_recent_inputs or bundle.similar_inputs):
        used_sources.append("history")
    used_memory_layers: List[str] = ["canonical_history"]
    if bundle.derived_user_model is not None:
        used_memory_layers.append("derived_user_model")
    if bundle.side_state:
        used_memory_layers.append("side_state")
    phase4_ready = phase4_observer_contract_ready(reports, evidence_spans)
    phase5_board_ready = phase5_board_contract_ready(board)
    phase5_graph_ready = phase5_observation_graph_ready(board, graph)
    phase5_ready = bool(phase4_ready and phase5_board_ready and phase5_graph_ready)
    phase6_contract_ready = bool(phase5_ready and phase6_composer_contract_ready())
    composer_candidate_available = bool(
        composer_candidate is not None
        and str(getattr(composer_candidate, "composer_source", "") or "") == "ai_generated"
        and str(getattr(composer_candidate, "comment_text", "") or "").strip()
    )
    phase6_ready = bool(phase6_contract_ready and composer_candidate_available)
    phase7_ready = bool(
        phase6_ready
        and phase7_judge_contract_ready(
            reader_report=reader_report,
            grounding_report=grounding_report,
            template_echo_report=template_echo_report,
            composer_source=str(composer_source or ""),
        )
    )
    phase8_ready = bool(phase7_ready and phase8_display_gate_contract_ready(display_decision))
    release_readiness = build_phase10_release_readiness(
        display_decision=display_decision,
        frontend_display_control_ready=phase8_ready,
    )
    phase9_ready = bool(phase8_ready and release_readiness.get("phase9_frontend_display_control_ready"))
    phase10_ready = bool(phase9_ready and release_readiness.get("phase10_regression_release_ready"))
    completed_phases = (
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        if phase10_ready
        else (
            [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
            if phase9_ready
            else ([0, 1, 2, 3, 4, 5, 6, 7, 8] if phase8_ready else ([0, 1, 2, 3, 4, 5, 6, 7] if phase7_ready else ([0, 1, 2, 3, 4, 5, 6] if phase6_ready else ([0, 1, 2, 3, 4, 5] if phase5_ready else ([0, 1, 2, 3, 4] if phase4_ready else [0, 1, 2, 3])))))
        )
    )
    gate_trace = getattr(display_decision, "gate_trace", {}) or build_emlis_gate_trace(
        reader_report=reader_report,
        grounding_report=grounding_report,
        template_echo_report=template_echo_report,
        composer_source=str(composer_source or ""),
        phase_completion_ready=False,
    )
    runtime_surface_gate_trace = gate_trace.get("runtime_surface_pre_return_gate") if isinstance(gate_trace, dict) else {}
    runtime_surface_gate_trace = dict(runtime_surface_gate_trace or {}) if isinstance(runtime_surface_gate_trace, dict) else {}
    runtime_surface_gate_reasons = list(runtime_surface_gate_trace.get("rejection_reasons") or []) if runtime_surface_gate_trace else []
    visible_surface_gate_trace = gate_trace.get("visible_surface_acceptance_gate") if isinstance(gate_trace, dict) else {}
    visible_surface_gate_trace = dict(visible_surface_gate_trace or {}) if isinstance(visible_surface_gate_trace, dict) else {}
    visible_surface_gate_reasons = list(visible_surface_gate_trace.get("rejection_reasons") or []) if visible_surface_gate_trace else []
    resolution_meta: Dict[str, Any] = {}
    as_meta = getattr(composer_client_resolution, "as_meta", None)
    if callable(as_meta):
        try:
            payload = as_meta()
            resolution_meta = dict(payload or {}) if isinstance(payload, dict) else {}
        except Exception:
            resolution_meta = {}
    scope_meta: Dict[str, Any] = {}
    scope_as_meta = getattr(limited_observation_scope, "as_meta", None)
    if callable(scope_as_meta):
        try:
            payload = scope_as_meta()
            scope_meta = dict(payload or {}) if isinstance(payload, dict) else {}
        except Exception:
            scope_meta = {}
    release_meta: Dict[str, Any] = {}
    release_as_meta = getattr(limited_release_decision, "as_meta", None)
    if callable(release_as_meta):
        try:
            payload = release_as_meta()
            release_meta = dict(payload or {}) if isinstance(payload, dict) else {}
        except Exception:
            release_meta = {}
    phase7_rollout_metrics = build_phase7_rollout_metrics(
        release_decision=limited_release_decision,
        observation_status=getattr(display_decision, "observation_status", ""),
        rejection_reasons=list(getattr(display_decision, "rejection_reasons", []) or []),
    )
    allowed_grounding_ids = [str(v) for v in list(grounding_allowed_evidence_span_ids or []) if str(v)]
    grounding_graph_payload = _jsonable(grounding_graph) if grounding_graph is not None else {}
    scoped_grounding_meta = {
        "enabled": bool(str(grounding_scope or "") != "full_graph"),
        "grounding_scope": str(grounding_scope or "full_graph"),
        "allowed_evidence_span_ids": allowed_grounding_ids,
        "full_graph_retained_for_meta": bool(scope_meta),
        "excluded_claims_retained_for_meta": list(scope_meta.get("excluded_claims") or []) if isinstance(scope_meta, dict) else [],
    }
    core_generation_meta = _composer_core_generation_meta(composer_candidate)
    core_adapter_ready = bool(core_generation_meta.get("adapter_name") == "emlis_observation_composer_adapter.v1")
    core_generation_ready = bool(core_generation_meta.get("passed"))
    core_stabilization_meta = (
        core_generation_meta.get("step15_common_core_stabilization")
        or core_generation_meta.get("common_core_stabilization")
        or {}
    )
    if not isinstance(core_stabilization_meta, dict):
        core_stabilization_meta = {}
    core_stabilization_ready = bool(core_stabilization_meta.get("passed"))
    phase_gate_meta = {
        "completed_phases": completed_phases,
        "current_phase": 10 if phase10_ready else (9 if phase9_ready else (8 if phase8_ready else (7 if phase7_ready else (6 if phase6_ready else (5 if phase5_ready else (4 if phase4_ready else 3)))))),
        "next_phase": None if phase10_ready else (10 if phase9_ready else (9 if phase8_ready else (8 if phase7_ready else (7 if phase6_ready else (6 if phase5_ready else (5 if phase4_ready else 4)))))),
        "phase_completion_ready": phase10_ready,
        "release_ready": bool(release_readiness.get("release_ready")),
        "release_blockers": list(release_readiness.get("release_blockers") or []),
        "required_completed_phases": list(release_readiness.get("required_completed_phases") or []),
        "release_checks": dict(release_readiness.get("release_checks") or {}),
        "legacy_text_routes_sealed": True,
        "type_state_contract_ready": True,
        "evidence_ledger_ready": True,
        "specialist_observers_ready": phase4_ready,
        "observer_contract_only_structured": phase4_ready,
        "perspective_board_ready": phase5_board_ready,
        "observation_graph_ready": phase5_graph_ready,
        "composer_contract_ready": phase6_contract_ready,
        "emlis_observation_composer_adapter_ready": core_adapter_ready,
        "text_generation_core_ready": core_generation_ready,
        "step15_common_core_stabilization_ready": core_stabilization_ready,
        "common_core_stabilization_ready": core_stabilization_ready,
        "text_generation_core_stop_point": TEXT_GENERATION_CORE_PHASE8_STOP_POINT,
        "text_generation_core_next_phase": TEXT_GENERATION_CORE_PHASE8_NEXT_PHASE,
        "text_generation_core_current_connected_core": CORE_ID_EMLIS,
        "piece_composer_connected": False,
        "analysis_composer_connected": False,
        "piece_analysis_text_generation_unstarted": True,
        "reader_gate_ready": isinstance(gate_trace.get("reader"), dict),
        "grounding_gate_ready": isinstance(gate_trace.get("grounding"), dict),
        "template_echo_gate_ready": isinstance(gate_trace.get("template_echo"), dict),
        "judge_contract_ready": phase7_ready,
        "phase7_staged_release_ready": bool(release_meta.get("enabled", False)) if release_meta else False,
        "phase7_rollout_stage": str(release_meta.get("stage", "") or "") if release_meta else "",
        "phase7_rollout_cohort": str(release_meta.get("cohort", "") or "") if release_meta else "",
        "phase7_rollout_attempted": bool(phase7_rollout_metrics.get("attempted", False)),
        "phase7_rollout_rejection_reasons": list(phase7_rollout_metrics.get("rejection_reasons") or []),
        "composer_candidate_available": composer_candidate_available,
        "composer_status": str(getattr(composer_candidate, "status", "") or ""),
        "board_validation_issues": validate_perspective_board(board),
        "graph_validation_issues": validate_observation_graph(graph, board),
        "gate_trace": gate_trace,
        "display_gate_ready": phase8_ready,
        "display_gate_release_ready": bool(phase8_ready and release_readiness.get("display_gate_release_ready")),
        "frontend_display_control_ready": phase9_ready,
        "phase9_frontend_display_control_ready": bool(release_readiness.get("phase9_frontend_display_control_ready")),
        "phase10_regression_release_ready": phase10_ready,
        "regression_release_tests_ready": phase10_ready,
        "comment_text_allowed": bool(phase8_ready and display_decision.observation_status == "passed" and str(display_decision.comment_text or "").strip()),
        "runtime_surface_pre_return_gate_evaluated": bool(runtime_surface_gate_trace.get("evaluated")) if runtime_surface_gate_trace else False,
        "runtime_surface_pre_return_gate_passed": bool(runtime_surface_gate_trace.get("passed")) if runtime_surface_gate_trace else True,
        "runtime_surface_pre_return_gate_action": str(runtime_surface_gate_trace.get("action") or "") if runtime_surface_gate_trace else "",
        "runtime_surface_pre_return_gate_rejection_reasons": runtime_surface_gate_reasons,
        "surface_template_major_blocked": "surface_template_major" in runtime_surface_gate_reasons,
        "malformed_phrase_unit_blocked_count": int(runtime_surface_gate_trace.get("malformed_phrase_unit_count") or 0) if runtime_surface_gate_trace else 0,
        "runtime_surface_pre_return_gate_display_gate_relaxed": False,
        "runtime_surface_pre_return_gate_comment_text_body_included": False,
        "runtime_surface_pre_return_gate_raw_input_included": False,
        "visible_surface_acceptance_gate_evaluated": bool(visible_surface_gate_trace.get("evaluated")) if visible_surface_gate_trace else False,
        "visible_surface_acceptance_gate_passed": bool(visible_surface_gate_trace.get("passed")) if visible_surface_gate_trace else True,
        "visible_surface_acceptance_gate_action": str(visible_surface_gate_trace.get("action") or "") if visible_surface_gate_trace else "",
        "visible_surface_acceptance_gate_classification": str(visible_surface_gate_trace.get("classification") or "") if visible_surface_gate_trace else "",
        "visible_surface_acceptance_gate_rejection_reasons": visible_surface_gate_reasons,
        "visible_surface_acceptance_gate_display_gate_relaxed": False,
        "visible_surface_acceptance_gate_comment_text_body_included": False,
        "visible_surface_acceptance_gate_raw_input_included": False,
    }
    step7_public_feedback_summary = _build_step7_public_feedback_diagnostic_summary(
        display_decision=display_decision,
        gate_trace=gate_trace,
        phase_gate_meta=phase_gate_meta,
    )
    phase_gate_meta["step7_public_feedback_diagnostic_summary"] = step7_public_feedback_summary
    phase_gate_meta["public_feedback_diagnostic_summary"] = step7_public_feedback_summary

    diagnostic_summary = _diagnostic_summary_meta(
        display_decision=display_decision,
        gate_trace=gate_trace,
        resolution_meta=resolution_meta,
        release_meta=release_meta,
        scope_meta=scope_meta,
        composer_candidate=composer_candidate,
        phase_gate=phase_gate_meta,
        rollout_metrics=phase7_rollout_metrics,
        current_input=bundle.current_input,
    )
    diagnostic_summary["step7_public_feedback_diagnostic_summary"] = step7_public_feedback_summary
    diagnostic_summary["public_feedback_diagnostic_summary"] = step7_public_feedback_summary
    diagnostic_summary["display_absence_summary"] = step7_public_feedback_summary

    _attach_complete_initial_pre_generation_seed(
        diagnostic_summary=diagnostic_summary,
        phase_gate_meta=phase_gate_meta,
        seed=complete_initial_pre_generation_seed,
    )
    complete_initial_client_resolved = bool(
        resolution_meta.get("complete_initial_client_used")
        or (
            resolution_meta.get("requested_composer") == "complete_initial"
            and resolution_meta.get("connection_status") == "default_client_resolved"
        )
    )
    diagnostic_summary["complete_initial_client_resolved"] = complete_initial_client_resolved
    diagnostic_summary["step3_complete_initial_client_resolved"] = complete_initial_client_resolved
    diagnostic_summary["step3_resolver_connection_status"] = str(resolution_meta.get("connection_status") or "")
    diagnostic_summary["step3_resolver_resolution_source"] = str(resolution_meta.get("resolution_source") or "")
    phase_gate_meta["complete_initial_client_resolved"] = complete_initial_client_resolved
    phase_gate_meta["step3_complete_initial_client_resolved"] = complete_initial_client_resolved
    phase_gate_meta["step3_resolver_connection_status"] = str(resolution_meta.get("connection_status") or "")
    phase_gate_meta["step3_resolver_resolution_source"] = str(resolution_meta.get("resolution_source") or "")
    _attach_step4_complete_initial_resolution_meta(
        diagnostic_summary=diagnostic_summary,
        phase_gate_meta=phase_gate_meta,
        resolution_meta=resolution_meta,
    )
    _attach_step5_complete_initial_candidate_generation_meta(
        diagnostic_summary=diagnostic_summary,
        phase_gate_meta=phase_gate_meta,
        resolution_meta=resolution_meta,
        composer_candidate=composer_candidate,
        display_decision=display_decision,
        gate_trace=gate_trace,
    )

    _attach_p4_complete_initial_surface_availability_summary(
        diagnostic_summary=diagnostic_summary,
        phase_gate_meta=phase_gate_meta,
    )
    step16_rollout_metrics = build_step16_rollout_metrics(
        release_meta=release_meta,
        diagnostic_summary=diagnostic_summary,
        phase7_rollout_metrics=phase7_rollout_metrics,
        composer_candidate=composer_candidate,
    )
    phase_gate_meta["step16_rollout_metrics_ready"] = bool(step16_rollout_metrics.get("ready"))
    phase_gate_meta["step16_rollout_metrics_aggregation_ready"] = bool(step16_rollout_metrics.get("aggregation_ready"))
    phase_gate_meta["b_r1_rollout_metrics_ready"] = bool(step16_rollout_metrics.get("ready"))
    phase_gate_meta["step16_rollout_metric_fields"] = list(step16_rollout_metrics.get("metric_fields") or [])
    phase_gate_meta["step16_rollout_primary_reason"] = str(step16_rollout_metrics.get("primary_reason") or "")
    phase_gate_meta["step16_rollout_coverage_group"] = str(step16_rollout_metrics.get("coverage_group") or "")
    phase_gate_meta["step16_rollout_composer_model"] = str(step16_rollout_metrics.get("composer_model") or "")
    diagnostic_summary["step16_rollout_metrics"] = step16_rollout_metrics
    diagnostic_summary["rollout_metrics"] = step16_rollout_metrics
    step9_scorecard_harness = build_emlis_limited_composer_scorecard_harness(
        diagnostic_summary=diagnostic_summary,
    )
    phase_gate_meta["step9_scorecard_harness_ready"] = bool(step9_scorecard_harness.get("ready"))
    phase_gate_meta["limited_composer_scorecard_ready"] = bool(step9_scorecard_harness.get("scorecard_ready"))
    phase_gate_meta["step9_scorecard_coverage_group"] = str(step9_scorecard_harness.get("coverage_group") or "")
    phase_gate_meta["step9_scorecard_primary_reason"] = str(step9_scorecard_harness.get("primary_reason") or "")
    phase_gate_meta["step9_scorecard_binding_missing"] = bool(step9_scorecard_harness.get("binding_missing"))
    diagnostic_summary["step9_scorecard_harness"] = step9_scorecard_harness
    diagnostic_summary["limited_composer_scorecard"] = step9_scorecard_harness
    diagnostic_summary["limited_composer_scorecard_harness"] = step9_scorecard_harness
    diagnostic_summary["scorecard_harness"] = step9_scorecard_harness
    step10_e2e_display_contract = build_limited_composer_e2e_display_contract(
        observation_status=getattr(display_decision, "observation_status", ""),
        comment_text=getattr(display_decision, "comment_text", ""),
        diagnostic_summary=diagnostic_summary,
        gate_trace=gate_trace,
    )
    phase_gate_meta["step10_e2e_display_contract_ready"] = bool(step10_e2e_display_contract.get("contract_passed"))
    phase_gate_meta["e2e_display_contract_ready"] = bool(step10_e2e_display_contract.get("contract_passed"))
    phase_gate_meta["step10_e2e_release_blockers"] = list(step10_e2e_display_contract.get("release_blockers") or [])
    phase_gate_meta["step10_passed_only_contract"] = str(step10_e2e_display_contract.get("contract_name") or "")
    diagnostic_summary["step10_e2e_display_contract"] = step10_e2e_display_contract
    diagnostic_summary["limited_composer_e2e_display_contract"] = step10_e2e_display_contract
    diagnostic_summary["e2e_display_contract"] = step10_e2e_display_contract
    step11_e2e_exit_gate = build_limited_composer_extension_e2e_exit_gate(
        diagnostic_summary=diagnostic_summary,
        step10_display_contract=step10_e2e_display_contract,
        gate_trace=gate_trace,
    )
    phase_gate_meta["step11_e2e_exit_gate_ready"] = bool(step11_e2e_exit_gate.get("limited_extension_exit_gate_ready"))
    phase_gate_meta["limited_composer_extension_exit_gate_ready"] = bool(step11_e2e_exit_gate.get("limited_extension_exit_gate_ready"))
    phase_gate_meta["ready_for_complete_composer_initial"] = bool(step11_e2e_exit_gate.get("ready_for_complete_composer_initial"))
    phase_gate_meta["step11_e2e_release_blockers"] = list(step11_e2e_exit_gate.get("release_blockers") or [])
    phase_gate_meta["step11_e2e_contract_passed"] = bool(step11_e2e_exit_gate.get("contract_passed"))
    phase_gate_meta["step11_previous_steps_missing"] = list(step11_e2e_exit_gate.get("previous_steps_missing") or [])
    diagnostic_summary["step11_e2e_exit_gate"] = step11_e2e_exit_gate
    diagnostic_summary["step11_e2e_test_fixed"] = step11_e2e_exit_gate
    diagnostic_summary["limited_composer_extension_exit_gate"] = step11_e2e_exit_gate
    diagnostic_summary["limited_composer_extension_exit_gate_e2e"] = step11_e2e_exit_gate
    step18_ap0_migration_decision = build_step18_ap0_migration_decision(
        diagnostic_summary=diagnostic_summary,
        rollout_metrics=step16_rollout_metrics,
        coverage_matrix=diagnostic_summary.get("coverage_matrix") if isinstance(diagnostic_summary, dict) else {},
    )
    phase_gate_meta["step18_ap0_migration_decision_ready"] = bool(step18_ap0_migration_decision.get("decision_ready"))
    phase_gate_meta["step18_ap0_can_proceed_to_a1"] = bool(step18_ap0_migration_decision.get("can_proceed_to_a1"))
    complete_composer_initial_ap0_report = step18_ap0_migration_decision.get("complete_composer_initial_ap0_report") or {}
    if not isinstance(complete_composer_initial_ap0_report, dict):
        complete_composer_initial_ap0_report = {}
    phase_gate_meta["complete_composer_initial_ap0_can_proceed"] = bool(step18_ap0_migration_decision.get("can_proceed_to_complete_initial"))
    phase_gate_meta["complete_composer_initial_ap0_report_version"] = str(complete_composer_initial_ap0_report.get("version") or "")
    phase_gate_meta["complete_composer_initial_ap0_release_blocker_count"] = int(complete_composer_initial_ap0_report.get("release_blocker_count") or 0)
    phase_gate_meta["a_p0_migration_decision"] = str(step18_ap0_migration_decision.get("decision") or "")
    phase_gate_meta["a_p0_return_steps"] = list(step18_ap0_migration_decision.get("return_steps") or [])
    diagnostic_summary["step18_ap0_migration_decision"] = step18_ap0_migration_decision
    diagnostic_summary["a_p0_migration_decision"] = step18_ap0_migration_decision
    diagnostic_summary["complete_composer_initial_ap0_report"] = complete_composer_initial_ap0_report
    diagnostic_summary["ap0_decision_report"] = complete_composer_initial_ap0_report

    composer_candidate_payload = _jsonable(composer_candidate) if composer_candidate is not None else {}
    if not isinstance(composer_candidate_payload, dict):
        composer_candidate_payload = {}
    step19_a_plan_equivalent = build_step19_a_plan_equivalent_meta(
        composer_model=(
            str(getattr(composer_candidate, "composer_model", "") or "")
            or str(resolution_meta.get("composer_model") or "")
        ),
        response=composer_candidate_payload,
        release_meta=release_meta,
        display_status=getattr(display_decision, "observation_status", ""),
        ap0_decision=step18_ap0_migration_decision,
    )
    phase_gate_meta["step19_a_plan_equivalent_ready"] = bool(step19_a_plan_equivalent.get("ready"))
    phase_gate_meta["step19_complete_composer_initial_ready"] = bool(step19_a_plan_equivalent.get("complete_initial_ready"))
    phase_gate_meta["step19_complete_composer_initial_rollout_allowed"] = bool(step19_a_plan_equivalent.get("can_rollout_complete_initial"))
    phase_gate_meta["step19_a_plan_model"] = str(step19_a_plan_equivalent.get("composer_model") or "")
    phase_gate_meta["step19_a_plan_rollout_stage"] = str(step19_a_plan_equivalent.get("rollout_stage") or "")
    phase_gate_meta["step19_a_plan_rollout_allowed"] = bool(step19_a_plan_equivalent.get("rollout_allowed"))
    phase_gate_meta["step19_b_plan_gate_preserved"] = bool(step19_a_plan_equivalent.get("b_plan_gate_preserved"))
    phase_gate_meta["step19_scoped_graph_preserved"] = bool(step19_a_plan_equivalent.get("scoped_graph_preserved"))
    phase_gate_meta["step19_fail_closed_preserved"] = bool(step19_a_plan_equivalent.get("fail_closed_preserved"))
    phase_gate_meta["step19_passed_only_preserved"] = bool(step19_a_plan_equivalent.get("passed_only_preserved"))
    diagnostic_summary["step19_a_plan_equivalent"] = step19_a_plan_equivalent
    diagnostic_summary["step19_a_plan_equivalent_composer"] = step19_a_plan_equivalent
    diagnostic_summary["step19_complete_composer_initial"] = step19_a_plan_equivalent
    diagnostic_summary["complete_composer_initial_rollout"] = step19_a_plan_equivalent
    diagnostic_summary["a1_composer_introduction"] = step19_a_plan_equivalent

    current_evidence_span_ids = [
        str(getattr(span, "span_id", "") or "").strip()
        for span in evidence_spans
        if str(getattr(span, "span_id", "") or "").strip()
    ]
    step20_history_scope = {
        "same_day_recent_input_count": len(list(getattr(bundle, "same_day_recent_inputs", []) or [])),
        "similar_input_count": len(list(getattr(bundle, "similar_inputs", []) or [])),
        "derived_user_model_present": bool(getattr(bundle, "derived_user_model", None)),
        "history_mode": getattr(capability, "history_mode", ""),
        "continuity_mode": getattr(capability, "continuity_mode", ""),
        "source_scope": getattr(capability, "source_scope", ""),
        "policy": "history_is_evidence_only",
    }
    step20_cross_core_scope = {
        "cross_core_enabled": bool(getattr(capability, "cross_core_enabled", False)),
        "cross_core_context_count": len(list(getattr(bundle, "cross_core_context", []) or [])),
        "policy": "cross_core_context_is_evidence_only",
    }
    step20_long_term_quality = build_step20_long_term_quality_meta(
        response=composer_candidate_payload,
        comment_text=getattr(display_decision, "comment_text", "") or composer_candidate_payload.get("comment_text"),
        previous_outputs=_previous_emlis_outputs_from_bundle(bundle),
        evidence_spans=evidence_spans,
        used_evidence_span_ids=composer_candidate_payload.get("used_evidence_span_ids", []),
        current_evidence_span_ids=current_evidence_span_ids,
        history_scope=step20_history_scope,
        cross_core_scope=step20_cross_core_scope,
        step19_a_plan_equivalent=step19_a_plan_equivalent,
        diagnostic_summary=diagnostic_summary,
        current_input=bundle.current_input,
    )
    phase_gate_meta["step20_long_term_quality_ready"] = bool(step20_long_term_quality.get("ready"))
    phase_gate_meta["step20_long_term_operation_ready"] = bool(step20_long_term_quality.get("long_term_operation_ready"))
    phase_gate_meta["step20_previous_output_sample_available"] = bool(step20_long_term_quality.get("previous_output_sample_available"))
    phase_gate_meta["step20_primary_reason"] = str(step20_long_term_quality.get("primary_reason") or "")
    phase_gate_meta["step20_history_is_evidence_only"] = bool(step20_long_term_quality.get("history_is_evidence_only"))
    phase_gate_meta["step20_overclaim_history_completion"] = bool(step20_long_term_quality.get("overclaim_history_completion"))
    diagnostic_summary["step20_long_term_quality"] = step20_long_term_quality
    diagnostic_summary["a2_long_term_quality"] = step20_long_term_quality
    diagnostic_summary["long_term_quality"] = step20_long_term_quality

    step11_complete_reply_diagnostics = build_complete_reply_service_diagnostics(
        composer_candidate=composer_candidate,
        display_decision=display_decision,
        gate_trace=gate_trace,
        resolution_meta=resolution_meta,
        release_meta=release_meta,
        diagnostic_summary=diagnostic_summary,
        phase_gate=phase_gate_meta,
        scorecard_harness=step9_scorecard_harness,
    )
    complete_scorecard_event = dict(step11_complete_reply_diagnostics.get("scorecard_event") or {})
    runtime_surface_step8_diagnostics = dict(
        step11_complete_reply_diagnostics.get("runtime_surface_step8_diagnostics")
        or step11_complete_reply_diagnostics.get("runtime_surface_diagnostics_scorecard")
        or complete_scorecard_event.get("runtime_surface_step8_diagnostics")
        or complete_scorecard_event.get("runtime_surface_diagnostics_scorecard")
        or {}
    )
    if runtime_surface_step8_diagnostics:
        diagnostic_summary["runtime_surface_step8_diagnostics"] = runtime_surface_step8_diagnostics
        diagnostic_summary["runtime_surface_diagnostics_scorecard"] = runtime_surface_step8_diagnostics
        for _runtime_surface_step8_key in (
            "runtime_surface_pre_return_gate_evaluated",
            "runtime_surface_pre_return_gate_passed",
            "runtime_surface_pre_return_gate_action",
            "runtime_surface_pre_return_gate_rejection_reasons",
            "runtime_surface_pre_return_gate_final_passed",
            "runtime_surface_pre_return_gate_scorecard_connected",
            "runtime_surface_diagnostics_scorecard_updated",
            "step8_runtime_surface_diagnostics_ready",
            "surface_template_major_blocked",
            "malformed_phrase_unit_blocked_count",
            "shallow_realizer_version",
            "shallow_v2_used",
            "low_information_specificity_used",
            "step6_low_information_specificity_ready",
            "safe_anchor_count",
            "uses_safe_anchor",
            "safe_anchor_role",
            "safe_anchor_surface_kind",
            "safe_anchor_evidence_ids",
            "unsupported_event_assertion_present",
            "user_fact_promotion_attempt",
        ):
            if _runtime_surface_step8_key in runtime_surface_step8_diagnostics:
                diagnostic_summary[_runtime_surface_step8_key] = runtime_surface_step8_diagnostics[_runtime_surface_step8_key]
                phase_gate_meta[_runtime_surface_step8_key] = runtime_surface_step8_diagnostics[_runtime_surface_step8_key]
        phase_gate_meta["runtime_surface_step8_diagnostics_ready"] = bool(runtime_surface_step8_diagnostics.get("ready", True))
        phase_gate_meta["runtime_surface_step8_raw_input_included"] = False
        phase_gate_meta["runtime_surface_step8_comment_text_body_included"] = False
    complete_repair_trace = list(step11_complete_reply_diagnostics.get("complete_repair_trace") or [])
    complete_runtime_meta = dict(step11_complete_reply_diagnostics.get("complete_runtime_meta") or {})
    runtime_surface_source_lock = dict(
        step11_complete_reply_diagnostics.get("runtime_surface_source_lock")
        or step11_complete_reply_diagnostics.get("step1_runtime_surface_source_lock")
        or complete_scorecard_event.get("runtime_surface_source_lock")
        or {}
    )
    surface_quality_signature = dict(
        step11_complete_reply_diagnostics.get("surface_quality_signature")
        or step11_complete_reply_diagnostics.get("step2_surface_quality_signature")
        or complete_scorecard_event.get("surface_quality_signature")
        or complete_scorecard_event.get("step2_surface_quality_signature")
        or {}
    )
    step6_runtime_surface_complete_activation_branch = build_runtime_surface_complete_activation_branch(
        runtime_surface_quality_branch={
            "target_layer": "complete_runtime_activation"
            if str(runtime_surface_source_lock.get("composer_source") or "") not in {"complete_initial", "complete_composer_initial"}
            else "not_complete_runtime_activation",
            "selected_reason": "reply_service_runtime_source_check",
        },
        runtime_surface_source_lock=runtime_surface_source_lock,
        composer_client_resolution={
            "requested_composer": resolution_meta.get("requested_composer"),
            "canonical_requested_composer": resolution_meta.get("canonical_requested_composer"),
            "connection_status": resolution_meta.get("connection_status"),
            "resolution_source": resolution_meta.get("resolution_source") or resolution_meta.get("source"),
            "resolved_client_class": resolution_meta.get("resolved_client_class") or resolution_meta.get("resolved_client_name"),
            "composer_model": resolution_meta.get("composer_model"),
            "complete_initial_requested": bool(
                resolution_meta.get("complete_initial_requested")
                or resolution_meta.get("complete_composer_initial_requested")
                or resolution_meta.get("complete_initial_client_requested")
            ),
            "complete_initial_client_used": bool(
                resolution_meta.get("complete_initial_client_used")
                or resolution_meta.get("complete_composer_client_used")
            ),
            "default_client_used": bool(resolution_meta.get("default_client_used")),
            "release_allowed": resolution_meta.get("release_allowed"),
            "complete_initial_gate": dict(resolution_meta.get("complete_initial_gate") or {}),
            "default_composer_resolution": dict(resolution_meta.get("default_composer_resolution") or {}),
        },
        complete_initial_entry_ap0_decision={
            "phase": str((diagnostic_summary.get("complete_initial_entry_ap0_decision") or {}).get("phase") or "complete_initial_entry_ap0"),
            "green": bool((diagnostic_summary.get("complete_initial_entry_ap0_decision") or {}).get("green")),
            "can_proceed_to_a1": bool((diagnostic_summary.get("complete_initial_entry_ap0_decision") or {}).get("can_proceed_to_a1")),
            "can_proceed_to_complete_initial": bool((diagnostic_summary.get("complete_initial_entry_ap0_decision") or {}).get("can_proceed_to_complete_initial")),
            "unmet_checks": list((diagnostic_summary.get("complete_initial_entry_ap0_decision") or {}).get("unmet_checks") or []),
            "release_blocker_keys": list((diagnostic_summary.get("complete_initial_entry_ap0_decision") or {}).get("release_blocker_keys") or []),
        },
        release_meta={
            "release_allowed": release_meta.get("release_allowed") if isinstance(release_meta, dict) else None,
            "rollout_allowed": release_meta.get("rollout_allowed") if isinstance(release_meta, dict) else None,
            "enabled": release_meta.get("enabled") if isinstance(release_meta, dict) else None,
            "stage": release_meta.get("stage") if isinstance(release_meta, dict) else "",
        },
    )
    if runtime_surface_source_lock:
        diagnostic_summary["runtime_surface_source_lock"] = runtime_surface_source_lock
        diagnostic_summary["step1_runtime_surface_source_lock"] = runtime_surface_source_lock
        diagnostic_summary["runtime_surface_source_lock_ready"] = bool(runtime_surface_source_lock.get("runtime_surface_source_lock_ready"))
        diagnostic_summary["runtime_surface_source_locked"] = bool(runtime_surface_source_lock.get("runtime_surface_source_locked"))
        diagnostic_summary["runtime_composer_source"] = runtime_surface_source_lock.get("composer_source")
        diagnostic_summary["composer_requested"] = runtime_surface_source_lock.get("composer_requested")
        diagnostic_summary["composer_resolved"] = runtime_surface_source_lock.get("composer_resolved")
        diagnostic_summary["runtime_composer_model"] = runtime_surface_source_lock.get("composer_model")
        diagnostic_summary["runtime_surface_source_complete_initial_client_used"] = bool(runtime_surface_source_lock.get("complete_initial_client_used"))
        diagnostic_summary["runtime_surface_source_limited_reader_repair_applied"] = bool(runtime_surface_source_lock.get("limited_reader_repair_applied"))
        diagnostic_summary["sentence_plan_version"] = runtime_surface_source_lock.get("sentence_plan_version")
        diagnostic_summary["surface_realizer_version"] = runtime_surface_source_lock.get("surface_realizer_version")
        diagnostic_summary["tone_policy_version"] = runtime_surface_source_lock.get("tone_policy_version")
        diagnostic_summary["self_repair_version"] = runtime_surface_source_lock.get("self_repair_version")
        diagnostic_summary["comment_text_body_included"] = False
    diagnostic_summary["runtime_surface_complete_activation_branch"] = step6_runtime_surface_complete_activation_branch
    diagnostic_summary["step6_runtime_surface_complete_activation_branch"] = step6_runtime_surface_complete_activation_branch
    diagnostic_summary["runtime_surface_complete_activation_branch_ready"] = bool(
        step6_runtime_surface_complete_activation_branch.get("runtime_surface_complete_activation_branch_ready")
    )
    diagnostic_summary["step6_runtime_surface_complete_activation_branch_ready"] = bool(
        step6_runtime_surface_complete_activation_branch.get("step6_complete_runtime_activation_branch_ready")
    )
    diagnostic_summary["runtime_surface_complete_activation_status"] = step6_runtime_surface_complete_activation_branch.get("activation_status")
    diagnostic_summary["runtime_surface_complete_initial_resolved"] = bool(step6_runtime_surface_complete_activation_branch.get("complete_initial_resolved"))
    diagnostic_summary["runtime_surface_complete_initial_source_lock_aligned"] = bool(
        step6_runtime_surface_complete_activation_branch.get("complete_initial_source_lock_aligned")
    )
    diagnostic_summary["runtime_surface_complete_initial_resolution_safe_to_measure"] = bool(
        step6_runtime_surface_complete_activation_branch.get("complete_initial_resolution_safe_to_measure")
    )
    diagnostic_summary["runtime_surface_repair_deferred_until_complete_runtime_measurable"] = bool(
        step6_runtime_surface_complete_activation_branch.get("surface_repair_deferred_until_complete_runtime_measurable")
    )
    if surface_quality_signature:
        diagnostic_summary["surface_quality_signature"] = surface_quality_signature
        diagnostic_summary["step2_surface_quality_signature"] = surface_quality_signature
        diagnostic_summary["surface_quality_signature_version"] = str(
            surface_quality_signature.get("schema_version")
            or surface_quality_signature.get("version")
            or complete_scorecard_event.get("surface_quality_signature_version")
            or ""
        )
        diagnostic_summary["step2_surface_quality_signature_ready"] = bool(
            complete_scorecard_event.get("step2_surface_quality_signature_ready")
            or surface_quality_signature.get("surface_quality_signature_ready")
        )
        diagnostic_summary["surface_signature_id"] = surface_quality_signature.get("surface_signature_id")
        diagnostic_summary["surface_signature_family_key"] = surface_quality_signature.get("surface_signature_family_key")
        diagnostic_summary["surface_template_major"] = bool(surface_quality_signature.get("template_major"))
        diagnostic_summary["surface_grammar_warning_codes"] = list(surface_quality_signature.get("grammar_warning_codes") or [])
        diagnostic_summary["surface_grammar_warning_count"] = int(surface_quality_signature.get("grammar_warning_count") or 0)
    step5_relation_diagnostic = dict(
        step11_complete_reply_diagnostics.get("positive_recovery_relation_diagnostic")
        or step11_complete_reply_diagnostics.get("relation_surface_diagnostic")
        or build_positive_recovery_relation_diagnostic(composer_candidate=composer_candidate, gate_trace=gate_trace)
    )
    phase_gate_meta["step11_complete_reply_service_diagnostics_ready"] = bool(step11_complete_reply_diagnostics.get("complete_reply_service_diagnostics_added"))
    phase_gate_meta["complete_reply_service_integrated"] = bool(step11_complete_reply_diagnostics.get("complete_reply_service_integrated"))
    phase_gate_meta["complete_meta_connected"] = bool(step11_complete_reply_diagnostics.get("complete_meta_connected"))
    phase_gate_meta["complete_scorecard_event_connected"] = bool(step11_complete_reply_diagnostics.get("scorecard_event_connected"))
    phase_gate_meta["complete_repair_trace_connected"] = bool(step11_complete_reply_diagnostics.get("repair_trace_connected"))
    phase_gate_meta["complete_repair_trace_count"] = int(step11_complete_reply_diagnostics.get("repair_trace_count") or 0)
    phase_gate_meta["complete_comment_text_contract_preserved"] = bool(step11_complete_reply_diagnostics.get("comment_text_contract") == "passed_only")
    phase_gate_meta["complete_response_shape_changed"] = bool(step11_complete_reply_diagnostics.get("response_shape_changed"))
    phase_gate_meta["step11_reply_service_diagnostics_ready"] = bool(step11_complete_reply_diagnostics.get("complete_reply_service_diagnostics_added"))
    phase_gate_meta["step11_complete_meta_connected"] = bool(step11_complete_reply_diagnostics.get("complete_meta_connected"))
    phase_gate_meta["step11_repair_trace_connected"] = bool(step11_complete_reply_diagnostics.get("repair_trace_connected"))
    phase_gate_meta["step11_scorecard_event_connected"] = bool(step11_complete_reply_diagnostics.get("scorecard_event_connected"))
    phase_gate_meta["step1_runtime_surface_source_lock_ready"] = bool(runtime_surface_source_lock.get("runtime_surface_source_lock_ready"))
    phase_gate_meta["runtime_surface_source_lock_ready"] = bool(runtime_surface_source_lock.get("runtime_surface_source_lock_ready"))
    phase_gate_meta["runtime_composer_source"] = runtime_surface_source_lock.get("composer_source", "")
    phase_gate_meta["step2_surface_quality_signature_ready"] = bool(surface_quality_signature)
    phase_gate_meta["surface_quality_signature_ready"] = bool(surface_quality_signature)
    phase_gate_meta["surface_template_major"] = bool(surface_quality_signature.get("template_major")) if surface_quality_signature else False
    phase_gate_meta["step6_runtime_surface_complete_activation_branch_ready"] = bool(
        step6_runtime_surface_complete_activation_branch.get("step6_complete_runtime_activation_branch_ready")
    )
    phase_gate_meta["runtime_surface_complete_activation_branch_ready"] = bool(
        step6_runtime_surface_complete_activation_branch.get("runtime_surface_complete_activation_branch_ready")
    )
    phase_gate_meta["runtime_surface_complete_activation_status"] = str(
        step6_runtime_surface_complete_activation_branch.get("activation_status") or ""
    )
    phase_gate_meta["runtime_surface_complete_initial_resolved"] = bool(
        step6_runtime_surface_complete_activation_branch.get("complete_initial_resolved")
    )
    phase_gate_meta["runtime_surface_repair_deferred_until_complete_runtime_measurable"] = bool(
        step6_runtime_surface_complete_activation_branch.get("surface_repair_deferred_until_complete_runtime_measurable")
    )
    phase_gate_meta["step11_response_shape_changed"] = bool(step11_complete_reply_diagnostics.get("response_shape_changed"))
    phase_gate_meta["step11_public_response_key_change"] = bool(step11_complete_reply_diagnostics.get("public_response_key_change"))
    phase_gate_meta["step5_relation_diagnostic_connected"] = bool(step5_relation_diagnostic.get("diagnostic_connected"))
    phase_gate_meta["step5_reader_relation_signal_detected"] = bool(step5_relation_diagnostic.get("reader_relation_signal_detected"))
    phase_gate_meta["step5_self_repair_relation_marker_applied"] = bool(step5_relation_diagnostic.get("self_repair_relation_marker_applied"))
    phase_gate_meta["step5_relation_diagnostic_raw_input_included"] = bool(step5_relation_diagnostic.get("raw_input_included"))
    phase_gate_meta["step7_limited_reader_repair_attempted"] = bool(step5_relation_diagnostic.get("limited_reader_repair_attempted"))
    phase_gate_meta["step7_limited_reader_repair_applied"] = bool(step5_relation_diagnostic.get("limited_reader_repair_applied"))
    phase_gate_meta["step7_limited_reader_repair_raw_input_included"] = bool(step5_relation_diagnostic.get("limited_reader_repair_raw_input_included"))
    diagnostic_summary["step5_relation_diagnostic"] = step5_relation_diagnostic
    diagnostic_summary["positive_recovery_relation_diagnostic"] = step5_relation_diagnostic
    diagnostic_summary["relation_surface_diagnostic"] = step5_relation_diagnostic
    for _relation_key in (
        "relation_surface_contract_version",
        "strict_relation_trace",
        "strict_relation_fail_closed",
        "strict_relation_fail_closed_evaluated",
        "strict_relation_fail_closed_triggered",
        "strict_relation_fail_closed_applied",
        "strict_relation_type",
        "strict_relation_surface_present_after_repair",
        "strict_relation_surface_missing_after_repair",
        "fallback_public_recovery_attempted",
        "fallback_public_recovery_allowed_for_this_candidate",
        "relation_not_expressed_preserved",
        "relation_not_expressed_retained",
        "strict_relation_fail_closed_blocked_reasons",
        "relation_signal_source_records",
        "relation_signal_source_priority",
        "selected_relation_signal_source",
        "gate_recovery_synthesized_reader_report",
        "strict_relation_signal_required",
        "required_relation_signal_keys",
        "matched_relation_signal_keys",
        "broad_relation_type_only",
        "broad_relation_type_only_keys",
        "relation_surface_status",
        "relation_surface_missing",
        "relation_surface_missing_after_repair",
        "strict_relation_surface_present_anywhere",
        "reader_relation_signal_detected",
        "reader_relation_signal_count",
        "reader_relation_signal_keys",
        "reader_relation_signal_relation_types",
        "expected_relation_types",
        "self_repair_relation_marker_applied",
        "self_repair_relation_marker_key",
        "self_repair_relation_marker_keys",
        "self_repair_relation_marker_count",
        "self_repair_relation_marker_signal_detected",
        "self_repair_relation_marker_signal_keys",
        "self_repair_relation_marker_meaning_added",
        "self_repair_relation_marker_gate_relaxed",
        "limited_reader_repair_attempted",
        "limited_reader_repair_applied",
        "limited_reader_repair_requires_repair",
        "limited_reader_repair_operations",
        "limited_reader_repair_relation_marker_key",
        "limited_reader_repair_relation_marker_signal_detected",
        "limited_reader_repair_relation_marker_signal_keys",
        "limited_reader_repair_relation_type",
        "limited_reader_repair_meaning_added",
        "limited_reader_repair_gate_relaxed",
        "limited_reader_repair_raw_input_included",
    ):
        if _relation_key in step5_relation_diagnostic:
            diagnostic_summary[_relation_key] = step5_relation_diagnostic[_relation_key]
    diagnostic_summary["step11_complete_reply_diagnostics"] = step11_complete_reply_diagnostics
    diagnostic_summary["step11_complete_reply_service_diagnostics"] = step11_complete_reply_diagnostics
    diagnostic_summary["complete_reply_service_diagnostics"] = step11_complete_reply_diagnostics
    diagnostic_summary["complete_composer_reply_diagnostics"] = step11_complete_reply_diagnostics
    diagnostic_summary["complete_composer_initial_reply_diagnostics"] = step11_complete_reply_diagnostics
    diagnostic_summary["complete_composer_initial_runtime"] = complete_runtime_meta
    diagnostic_summary["complete_composer_initial_meta"] = complete_runtime_meta
    diagnostic_summary["complete_composer_meta"] = complete_runtime_meta
    diagnostic_summary["complete_repair_trace"] = complete_repair_trace
    diagnostic_summary["complete_composer_repair_trace"] = complete_repair_trace
    diagnostic_summary["complete_composer_initial_repair_trace"] = complete_repair_trace
    diagnostic_summary["complete_scorecard_event"] = complete_scorecard_event
    diagnostic_summary["complete_composer_scorecard_event"] = complete_scorecard_event
    diagnostic_summary["complete_composer_initial_scorecard_event"] = complete_scorecard_event
    diagnostic_summary["scorecard_event"] = complete_scorecard_event

    observation_diagnostic_lockdown_meta = _build_observation_diagnostic_lockdown_reply_meta(
        trace_id=trace_id,
        display_decision=display_decision,
        composer_candidate=composer_candidate,
        diagnostic_summary=diagnostic_summary,
        complete_reply_diagnostics=step11_complete_reply_diagnostics,
        complete_scorecard_event=complete_scorecard_event,
        complete_repair_trace=complete_repair_trace,
    )
    _attach_observation_diagnostic_lockdown_reply_meta(
        diagnostic_summary=diagnostic_summary,
        phase_gate_meta=phase_gate_meta,
        lockdown_meta=observation_diagnostic_lockdown_meta,
    )

    step12_complete_scorecard_harness = build_complete_scorecard_harness(
        scorecard_event=complete_scorecard_event,
        diagnostic_summary=diagnostic_summary,
    )
    phase_gate_meta["step12_complete_scorecard_ready"] = bool(step12_complete_scorecard_harness.get("scorecard_ready"))
    phase_gate_meta["complete_scorecard_harness_ready"] = bool(step12_complete_scorecard_harness.get("ready"))
    phase_gate_meta["complete_scorecard_fixture_suite_ready"] = bool((step12_complete_scorecard_harness.get("fixture_suite") or {}).get("ready"))
    phase_gate_meta["complete_scorecard_display_reach_rate"] = float(step12_complete_scorecard_harness.get("display_reach_rate") or 0.0)
    phase_gate_meta["complete_scorecard_binding_pass_rate"] = float(step12_complete_scorecard_harness.get("binding_pass_rate") or 0.0)
    phase_gate_meta["complete_scorecard_read_feeling_requires_blind_qa"] = bool(step12_complete_scorecard_harness.get("read_feeling_requires_blind_qa"))
    phase_gate_meta["complete_scorecard_response_shape_changed"] = bool(step12_complete_scorecard_harness.get("response_shape_changed"))
    phase_gate_meta["runtime_surface_scorecard_failed_count"] = int(step12_complete_scorecard_harness.get("runtime_surface_pre_return_gate_failed_count") or 0)
    phase_gate_meta["surface_template_major_blocked_scorecard_count"] = int(step12_complete_scorecard_harness.get("surface_template_major_blocked_count") or 0)
    phase_gate_meta["malformed_phrase_unit_blocked_scorecard_count"] = int(step12_complete_scorecard_harness.get("malformed_phrase_unit_blocked_count") or 0)
    phase_gate_meta["shallow_v2_used_scorecard_count"] = int(step12_complete_scorecard_harness.get("shallow_v2_used_count") or 0)
    phase_gate_meta["low_information_specificity_used_scorecard_count"] = int(step12_complete_scorecard_harness.get("low_information_specificity_used_count") or 0)
    phase_gate_meta["step12_product_gate_evaluation"] = str(step12_complete_scorecard_harness.get("product_gate_evaluation") or "")
    diagnostic_summary["step12_complete_scorecard_harness"] = step12_complete_scorecard_harness
    diagnostic_summary["complete_scorecard_harness"] = step12_complete_scorecard_harness
    diagnostic_summary["complete_composer_scorecard_harness"] = step12_complete_scorecard_harness
    diagnostic_summary["complete_composer_initial_scorecard_harness"] = step12_complete_scorecard_harness
    diagnostic_summary["complete_scorecard"] = step12_complete_scorecard_harness
    diagnostic_summary["complete_composer_scorecard"] = step12_complete_scorecard_harness
    diagnostic_summary["complete_composer_initial_scorecard"] = step12_complete_scorecard_harness
    diagnostic_summary["complete_scorecard_fixture_suite"] = dict(step12_complete_scorecard_harness.get("fixture_suite") or {})
    diagnostic_summary["complete_blind_qa_rubric"] = dict(step12_complete_scorecard_harness.get("blind_qa_rubric") or {})
    diagnostic_summary["runtime_surface_pre_return_gate_failed_scorecard_count"] = int(step12_complete_scorecard_harness.get("runtime_surface_pre_return_gate_failed_count") or 0)
    diagnostic_summary["surface_template_major_blocked_scorecard_count"] = int(step12_complete_scorecard_harness.get("surface_template_major_blocked_count") or 0)
    diagnostic_summary["malformed_phrase_unit_blocked_scorecard_count"] = int(step12_complete_scorecard_harness.get("malformed_phrase_unit_blocked_count") or 0)
    diagnostic_summary["shallow_v2_used_scorecard_count"] = int(step12_complete_scorecard_harness.get("shallow_v2_used_count") or 0)
    diagnostic_summary["low_information_specificity_used_scorecard_count"] = int(step12_complete_scorecard_harness.get("low_information_specificity_used_count") or 0)

    step6_final_ap0_scorecard_connection = _attach_step6_complete_initial_final_ap0_scorecard_meta(
        diagnostic_summary=diagnostic_summary,
        phase_gate_meta=phase_gate_meta,
        step18_ap0_migration_decision=step18_ap0_migration_decision,
        complete_composer_initial_ap0_report=complete_composer_initial_ap0_report,
        complete_scorecard_event=complete_scorecard_event,
        step12_complete_scorecard_harness=step12_complete_scorecard_harness,
    )

    step9_complete_initial_fixture_qa_run = build_complete_initial_fixture_qa_run(
        scorecard_event=complete_scorecard_event,
        fixture_suite=dict(step12_complete_scorecard_harness.get("fixture_suite") or {}),
        diagnostic_summary=diagnostic_summary,
    )
    step9_product_scorecard_seed = dict(step9_complete_initial_fixture_qa_run.get("product_scorecard_seed") or {})
    diagnostic_summary["step9_fixture_qa_run"] = step9_complete_initial_fixture_qa_run
    diagnostic_summary["step9_complete_initial_fixture_qa_run"] = step9_complete_initial_fixture_qa_run
    diagnostic_summary["complete_initial_fixture_qa_run"] = step9_complete_initial_fixture_qa_run
    diagnostic_summary["complete_composer_initial_fixture_qa_run"] = step9_complete_initial_fixture_qa_run
    diagnostic_summary["fixture_qa_run"] = step9_complete_initial_fixture_qa_run
    diagnostic_summary["complete_initial_qa_run"] = step9_complete_initial_fixture_qa_run
    diagnostic_summary["step9_product_scorecard_seed"] = step9_product_scorecard_seed
    diagnostic_summary["complete_initial_product_scorecard_seed"] = step9_product_scorecard_seed
    diagnostic_summary["step9_fixture_qa_run_ready"] = bool(step9_complete_initial_fixture_qa_run.get("qa_run_ready"))
    diagnostic_summary["step9_product_scorecard_input_ready"] = bool(step9_complete_initial_fixture_qa_run.get("product_scorecard_input_ready"))
    phase_gate_meta["step9_fixture_qa_run_ready"] = bool(step9_complete_initial_fixture_qa_run.get("qa_run_ready"))
    phase_gate_meta["step9_fixture_qa_data_ready"] = bool(step9_complete_initial_fixture_qa_run.get("fixture_qa_data_ready"))
    phase_gate_meta["step9_product_scorecard_input_ready"] = bool(step9_complete_initial_fixture_qa_run.get("product_scorecard_input_ready"))
    phase_gate_meta["step9_fixture_coverage_complete"] = bool(step9_complete_initial_fixture_qa_run.get("fixture_coverage_complete"))
    phase_gate_meta["step9_display_reach_rate"] = float(step9_complete_initial_fixture_qa_run.get("display_reach_rate") or 0.0)
    phase_gate_meta["step9_binding_pass_rate"] = float(step9_complete_initial_fixture_qa_run.get("binding_pass_rate") or 0.0)
    phase_gate_meta["step9_read_feeling_requires_blind_qa"] = bool(step9_complete_initial_fixture_qa_run.get("read_feeling_requires_blind_qa"))
    phase_gate_meta["step9_non_template_major_clear"] = bool(step9_complete_initial_fixture_qa_run.get("non_template_major_clear"))
    phase_gate_meta["step9_safety_major_clear"] = bool(step9_complete_initial_fixture_qa_run.get("safety_major_clear"))
    phase_gate_meta["step9_comment_text_contract_preserved"] = bool(step9_complete_initial_fixture_qa_run.get("comment_text_contract") == "passed_only")
    phase_gate_meta["step9_display_gate_relaxed"] = bool(step9_complete_initial_fixture_qa_run.get("display_gate_relaxed"))

    step6_product_quality_scorecard = build_complete_product_quality_scorecard(
        scorecard_event=complete_scorecard_event,
        scorecard_harness=step12_complete_scorecard_harness,
        fixture_qa_run=step9_complete_initial_fixture_qa_run,
        diagnostic_summary=diagnostic_summary,
    )
    step6_product_quality_event_schema = build_complete_product_quality_scorecard_event_schema()
    step6_product_quality_blind_qa_rubric = dict(
        step6_product_quality_scorecard.get("blind_qa_rubric")
        or build_complete_product_quality_blind_qa_rubric()
    )
    diagnostic_summary["step6_product_quality_scorecard"] = step6_product_quality_scorecard
    diagnostic_summary["product_quality_scorecard"] = step6_product_quality_scorecard
    diagnostic_summary["complete_product_quality_scorecard"] = step6_product_quality_scorecard
    diagnostic_summary["complete_composer_product_quality_scorecard"] = step6_product_quality_scorecard
    diagnostic_summary["complete_composer_initial_product_quality_scorecard"] = step6_product_quality_scorecard
    diagnostic_summary["product_quality_scorecard_event_schema"] = step6_product_quality_event_schema
    diagnostic_summary["complete_product_quality_scorecard_event_schema"] = step6_product_quality_event_schema
    diagnostic_summary["product_quality_blind_qa_rubric"] = step6_product_quality_blind_qa_rubric
    diagnostic_summary["complete_product_quality_blind_qa_rubric"] = step6_product_quality_blind_qa_rubric
    diagnostic_summary["step6_product_quality_machine_metrics"] = dict(step6_product_quality_scorecard.get("machine_metrics") or {})
    diagnostic_summary["step6_product_quality_blind_qa_metrics"] = dict(step6_product_quality_scorecard.get("blind_qa_metrics") or {})
    phase_gate_meta["step6_product_quality_scorecard_ready"] = bool(step6_product_quality_scorecard.get("product_quality_scorecard_ready"))
    phase_gate_meta["step6_product_quality_machine_metrics_ready"] = bool(step6_product_quality_scorecard.get("machine_metrics_ready"))
    phase_gate_meta["step6_product_quality_blind_qa_ready"] = bool(step6_product_quality_scorecard.get("blind_qa_ready"))
    phase_gate_meta["product_quality_scorecard_ready"] = bool(step6_product_quality_scorecard.get("scorecard_ready") or step6_product_quality_scorecard.get("product_quality_scorecard_ready"))
    phase_gate_meta["step6_product_quality_display_reach_rate"] = float(step6_product_quality_scorecard.get("display_reach_rate") or 0.0)
    phase_gate_meta["step6_product_quality_binding_pass_rate"] = float(step6_product_quality_scorecard.get("binding_pass_rate") or 0.0)
    phase_gate_meta["step6_product_quality_read_feeling_requires_blind_qa"] = bool(step6_product_quality_scorecard.get("read_feeling_requires_blind_qa"))
    phase_gate_meta["step6_product_quality_safety_major_count"] = int(step6_product_quality_scorecard.get("safety_major_count") or 0)
    phase_gate_meta["step6_product_quality_template_major_count"] = int(step6_product_quality_scorecard.get("template_major_count") or 0)
    phase_gate_meta["step6_product_quality_release_ladder_stage"] = str(step6_product_quality_scorecard.get("release_ladder_stage") or "")
    phase_gate_meta["step6_product_quality_product_gate_reached"] = bool(step6_product_quality_scorecard.get("product_gate_reached"))
    phase_gate_meta["step6_product_gate_ready"] = bool(step6_product_quality_scorecard.get("product_gate_ready"))
    phase_gate_meta["step6_product_quality_response_shape_changed"] = bool(step6_product_quality_scorecard.get("response_shape_changed"))
    phase_gate_meta["step6_product_quality_comment_text_written"] = bool(step6_product_quality_scorecard.get("comment_text_written_by_step6_product_quality"))
    phase_gate_meta["step6_product_quality_raw_input_included"] = bool(step6_product_quality_scorecard.get("raw_input_included"))
    phase_gate_meta["step6_product_quality_display_gate_relaxed"] = bool(step6_product_quality_scorecard.get("display_gate_relaxed"))

    step7_product_quality_release_ladder = build_complete_product_quality_release_ladder(
        product_quality_scorecard=step6_product_quality_scorecard,
        diagnostic_summary=diagnostic_summary,
        phase_gate=phase_gate_meta,
    )
    diagnostic_summary["step7_product_quality_release_ladder"] = step7_product_quality_release_ladder
    diagnostic_summary["product_quality_release_ladder"] = step7_product_quality_release_ladder
    diagnostic_summary["complete_product_quality_release_ladder"] = step7_product_quality_release_ladder
    diagnostic_summary["complete_composer_product_quality_release_ladder"] = step7_product_quality_release_ladder
    diagnostic_summary["complete_composer_initial_product_quality_release_ladder"] = step7_product_quality_release_ladder
    diagnostic_summary["release_ladder_guard"] = step7_product_quality_release_ladder
    phase_gate_meta["step7_product_quality_release_ladder_connected"] = bool(step7_product_quality_release_ladder.get("release_ladder_connected"))
    phase_gate_meta["step7_product_quality_release_ladder_guard_ready"] = bool(step7_product_quality_release_ladder.get("release_ladder_guard_ready"))
    phase_gate_meta["step7_product_quality_current_stage"] = str(step7_product_quality_release_ladder.get("current_stage") or "")
    phase_gate_meta["step7_product_quality_max_allowed_stage"] = str(step7_product_quality_release_ladder.get("max_allowed_stage") or "")
    phase_gate_meta["step7_product_quality_product_gate_ready"] = bool(step7_product_quality_release_ladder.get("product_gate_ready"))
    phase_gate_meta["step7_product_quality_product_gate_reached"] = bool(step7_product_quality_release_ladder.get("product_gate_reached"))
    phase_gate_meta["step7_product_quality_public_release_applied"] = bool(step7_product_quality_release_ladder.get("product_gate_public_release_applied"))
    phase_gate_meta["step7_product_quality_comment_text_written"] = bool(step7_product_quality_release_ladder.get("comment_text_written_by_step7_release_ladder"))
    phase_gate_meta["step7_product_quality_response_shape_changed"] = bool(step7_product_quality_release_ladder.get("response_shape_changed"))
    phase_gate_meta["step7_product_quality_display_gate_relaxed"] = bool(step7_product_quality_release_ladder.get("display_gate_relaxed"))
    phase_gate_meta["step7_product_quality_raw_input_included"] = bool(step7_product_quality_release_ladder.get("raw_input_included"))


    b_plan_connection_meta = (
        dict(diagnostic_summary.get("normal_connection") or diagnostic_summary.get("b_plan_connection") or {})
        if isinstance(diagnostic_summary, dict)
        else {}
    )
    return {
        "version": "emlis_ai_v3",
        "kernel_version": "multi_perspective_observation.v1",
        "tier": capability.tier,
        "observation_status": display_decision.observation_status,
        "observation_trace_id": trace_id,
        "rejection_reasons": list(display_decision.rejection_reasons),
        "diagnostic_summary": diagnostic_summary,
        "runtime_surface_source_lock": runtime_surface_source_lock,
        "step1_runtime_surface_source_lock": runtime_surface_source_lock,
        "runtime_surface_source_lock_ready": bool(runtime_surface_source_lock.get("runtime_surface_source_lock_ready")),
        "runtime_surface_source_locked": bool(runtime_surface_source_lock.get("runtime_surface_source_locked")),
        "runtime_composer_source": runtime_surface_source_lock.get("composer_source"),
        "composer_requested": runtime_surface_source_lock.get("composer_requested"),
        "composer_resolved": runtime_surface_source_lock.get("composer_resolved"),
        "runtime_composer_model": runtime_surface_source_lock.get("composer_model"),
        "runtime_surface_source_complete_initial_client_used": bool(runtime_surface_source_lock.get("complete_initial_client_used")),
        "runtime_surface_source_limited_reader_repair_applied": bool(runtime_surface_source_lock.get("limited_reader_repair_applied")),
        "sentence_plan_version": runtime_surface_source_lock.get("sentence_plan_version"),
        "surface_realizer_version": runtime_surface_source_lock.get("surface_realizer_version"),
        "tone_policy_version": runtime_surface_source_lock.get("tone_policy_version"),
        "self_repair_version": runtime_surface_source_lock.get("self_repair_version"),
        "runtime_surface_complete_activation_branch": step6_runtime_surface_complete_activation_branch,
        "step6_runtime_surface_complete_activation_branch": step6_runtime_surface_complete_activation_branch,
        "runtime_surface_complete_activation_branch_ready": bool(step6_runtime_surface_complete_activation_branch.get("runtime_surface_complete_activation_branch_ready")),
        "step6_runtime_surface_complete_activation_branch_ready": bool(step6_runtime_surface_complete_activation_branch.get("step6_complete_runtime_activation_branch_ready")),
        "runtime_surface_complete_activation_status": step6_runtime_surface_complete_activation_branch.get("activation_status"),
        "runtime_surface_complete_initial_resolved": bool(step6_runtime_surface_complete_activation_branch.get("complete_initial_resolved")),
        "runtime_surface_complete_initial_source_lock_aligned": bool(step6_runtime_surface_complete_activation_branch.get("complete_initial_source_lock_aligned")),
        "runtime_surface_complete_initial_resolution_safe_to_measure": bool(step6_runtime_surface_complete_activation_branch.get("complete_initial_resolution_safe_to_measure")),
        "runtime_surface_repair_deferred_until_complete_runtime_measurable": bool(step6_runtime_surface_complete_activation_branch.get("surface_repair_deferred_until_complete_runtime_measurable")),
        "surface_quality_signature": surface_quality_signature,
        "step2_surface_quality_signature": surface_quality_signature,
        "surface_quality_signature_version": str(
            surface_quality_signature.get("schema_version")
            or surface_quality_signature.get("version")
            or complete_scorecard_event.get("surface_quality_signature_version")
            or ""
        ),
        "step2_surface_quality_signature_ready": bool(surface_quality_signature),
        "surface_signature_id": surface_quality_signature.get("surface_signature_id"),
        "surface_signature_family_key": surface_quality_signature.get("surface_signature_family_key"),
        "surface_template_major": bool(surface_quality_signature.get("template_major")) if surface_quality_signature else False,
        "surface_grammar_warning_codes": list(surface_quality_signature.get("grammar_warning_codes") or []),
        "surface_grammar_warning_count": int(surface_quality_signature.get("grammar_warning_count") or 0) if surface_quality_signature else 0,
        "comment_text_body_included": False,
        "complete_initial_pre_generation_diagnostic_seed": dict(diagnostic_summary.get("complete_initial_pre_generation_diagnostic_seed") or {}),
        "complete_initial_entry_ap0_decision": dict(diagnostic_summary.get("complete_initial_entry_ap0_decision") or {}),
        "step6_final_ap0_scorecard_connection": dict(diagnostic_summary.get("step6_final_ap0_scorecard_connection") or {}),
        "complete_initial_final_ap0_scorecard_connection": dict(diagnostic_summary.get("complete_initial_final_ap0_scorecard_connection") or {}),
        "complete_initial_next_improvement_meta": dict(diagnostic_summary.get("complete_initial_next_improvement_meta") or {}),
        "limited_composer_extension_baseline": dict(diagnostic_summary.get("limited_composer_extension_baseline") or {}),
        "step0_baseline": dict(diagnostic_summary.get("step0_baseline") or diagnostic_summary.get("limited_composer_extension_baseline") or {}),
        "connection_visibility": dict(diagnostic_summary.get("connection_visibility") or {}),
        "limited_composer_connection_visibility": dict(diagnostic_summary.get("limited_composer_connection_visibility") or diagnostic_summary.get("connection_visibility") or {}),
        "step1_connection_visibility": dict(diagnostic_summary.get("step1_connection_visibility") or diagnostic_summary.get("connection_visibility") or {}),
        "diagnostic_summary_extension": dict(diagnostic_summary.get("diagnostic_summary_extension") or {}),
        "diagnostic_summary_v2": dict(diagnostic_summary.get("diagnostic_summary_v2") or {}),
        "limited_composer_diagnostic_summary_extension": dict(diagnostic_summary.get("limited_composer_diagnostic_summary_extension") or {}),
        "step2_diagnostic_summary_extension": dict(diagnostic_summary.get("step2_diagnostic_summary_extension") or {}),
        "binding_diagnostic": dict(diagnostic_summary.get("binding_diagnostic") or {}),
        "coverage_group": str(diagnostic_summary.get("coverage_group") or ""),
        "failed_stage": str(diagnostic_summary.get("failed_stage") or ""),
        "step16_rollout_metrics": step16_rollout_metrics,
        "step9_scorecard_harness": step9_scorecard_harness,
        "limited_composer_scorecard": step9_scorecard_harness,
        "limited_composer_scorecard_harness": step9_scorecard_harness,
        "scorecard_harness": step9_scorecard_harness,
        "step10_e2e_display_contract": step10_e2e_display_contract,
        "limited_composer_e2e_display_contract": step10_e2e_display_contract,
        "e2e_display_contract": step10_e2e_display_contract,
        "step11_e2e_exit_gate": step11_e2e_exit_gate,
        "step11_e2e_test_fixed": step11_e2e_exit_gate,
        "limited_composer_extension_exit_gate": step11_e2e_exit_gate,
        "limited_composer_extension_exit_gate_e2e": step11_e2e_exit_gate,
        "step18_ap0_migration_decision": step18_ap0_migration_decision,
        "a_p0_migration_decision": step18_ap0_migration_decision,
        "complete_composer_initial_ap0_report": complete_composer_initial_ap0_report,
        "ap0_decision_report": complete_composer_initial_ap0_report,
        "step19_a_plan_equivalent": step19_a_plan_equivalent,
        "step19_a_plan_equivalent_composer": step19_a_plan_equivalent,
        "step19_complete_composer_initial": step19_a_plan_equivalent,
        "complete_composer_initial_rollout": step19_a_plan_equivalent,
        "a1_composer_introduction": step19_a_plan_equivalent,
        "step20_long_term_quality": step20_long_term_quality,
        "a2_long_term_quality": step20_long_term_quality,
        "long_term_quality": step20_long_term_quality,
        "step11_complete_reply_diagnostics": step11_complete_reply_diagnostics,
        "step11_complete_reply_service_diagnostics": step11_complete_reply_diagnostics,
        "complete_reply_diagnostics": step11_complete_reply_diagnostics,
        "complete_reply_service_diagnostics": step11_complete_reply_diagnostics,
        "complete_composer_reply_diagnostics": step11_complete_reply_diagnostics,
        "complete_composer_initial_reply_diagnostics": step11_complete_reply_diagnostics,
        "complete_composer_initial_runtime": complete_runtime_meta,
        "complete_composer_initial_meta": complete_runtime_meta,
        "complete_composer_meta": complete_runtime_meta,
        "complete_repair_trace": complete_repair_trace,
        "complete_composer_repair_trace": complete_repair_trace,
        "complete_composer_initial_repair_trace": complete_repair_trace,
        "step5_relation_diagnostic": step5_relation_diagnostic,
        "positive_recovery_relation_diagnostic": step5_relation_diagnostic,
        "relation_surface_diagnostic": step5_relation_diagnostic,
        "complete_scorecard_event": complete_scorecard_event,
        "complete_composer_scorecard_event": complete_scorecard_event,
        "complete_composer_initial_scorecard_event": complete_scorecard_event,
        "scorecard_event": complete_scorecard_event,
        "step12_complete_scorecard_harness": step12_complete_scorecard_harness,
        "complete_scorecard_harness": step12_complete_scorecard_harness,
        "complete_composer_scorecard_harness": step12_complete_scorecard_harness,
        "complete_composer_initial_scorecard_harness": step12_complete_scorecard_harness,
        "complete_scorecard": step12_complete_scorecard_harness,
        "complete_composer_scorecard": step12_complete_scorecard_harness,
        "complete_composer_initial_scorecard": step12_complete_scorecard_harness,
        "complete_scorecard_fixture_suite": dict(step12_complete_scorecard_harness.get("fixture_suite") or {}),
        "complete_blind_qa_rubric": dict(step12_complete_scorecard_harness.get("blind_qa_rubric") or {}),
        "step6_product_quality_scorecard": step6_product_quality_scorecard,
        "product_quality_scorecard": step6_product_quality_scorecard,
        "complete_product_quality_scorecard": step6_product_quality_scorecard,
        "product_quality_scorecard_event_schema": step6_product_quality_event_schema,
        "complete_product_quality_scorecard_event_schema": step6_product_quality_event_schema,
        "product_quality_blind_qa_rubric": step6_product_quality_blind_qa_rubric,
        "complete_product_quality_blind_qa_rubric": step6_product_quality_blind_qa_rubric,
        "step7_product_quality_release_ladder": step7_product_quality_release_ladder,
        "product_quality_release_ladder": step7_product_quality_release_ladder,
        "complete_product_quality_release_ladder": step7_product_quality_release_ladder,
        "complete_composer_product_quality_release_ladder": step7_product_quality_release_ladder,
        "release_ladder_guard": step7_product_quality_release_ladder,
        "step9_fixture_qa_run": step9_complete_initial_fixture_qa_run,
        "step9_product_scorecard_seed": step9_product_scorecard_seed,
        "complete_initial_product_scorecard_seed": step9_product_scorecard_seed,
        "step9_complete_initial_fixture_qa_run": step9_complete_initial_fixture_qa_run,
        "complete_initial_fixture_qa_run": step9_complete_initial_fixture_qa_run,
        "complete_composer_initial_fixture_qa_run": step9_complete_initial_fixture_qa_run,
        "fixture_qa_run": step9_complete_initial_fixture_qa_run,
        "complete_initial_qa_run": step9_complete_initial_fixture_qa_run,
        "display": {
            "display_name_call": display_name_call(bundle.display_name),
            "visible_name": "Emlisの観測",
        },
        "capability": {
            "history_mode": capability.history_mode,
            "continuity_mode": capability.continuity_mode,
            "style_mode": capability.style_mode,
            "partner_mode": capability.partner_mode,
            "model_mode": capability.model_mode,
            "interpretation_mode": capability.interpretation_mode,
            "source_scope": capability.source_scope,
            "cross_core_enabled": bool(capability.cross_core_enabled),
            "structure_model_enabled": bool(capability.structure_model_enabled),
        },
        "multi_perspective": {
            "architecture_version": "emlis.multi_perspective.v1",
            "fail_closed": True,
            "legacy_observation_kernel_used": False,
            "legacy_safe_fallback_used": False,
            "legacy_input_feedback_template_used": False,
            "evidence_span_count": len(evidence_spans),
            "observer_count": len(reports),
            "observer_ids": [str(getattr(report, "observer_id", "")) for report in reports],
            "evidence_spans": _jsonable(evidence_spans[:12]),
            "perspective_reports": _jsonable(reports),
            "perspective_board": _jsonable(board),
            "observation_graph": _jsonable(graph),
            "reader_report": _jsonable(reader_report),
            "grounding_report": _jsonable(grounding_report),
            "template_echo_report": _jsonable(template_echo_report),
            "gate_trace": gate_trace,
            "composer_candidate": _jsonable(composer_candidate) if composer_candidate is not None else {},
            "composer_source": str(composer_source or ""),
            "composer_status": str(getattr(composer_candidate, "status", "") or ""),
            "composer_rejection_reasons": list(getattr(composer_candidate, "rejection_reasons", []) or []),
            "composer_client_resolution": resolution_meta,
            "complete_initial_pre_generation_diagnostic_seed": dict(diagnostic_summary.get("complete_initial_pre_generation_diagnostic_seed") or {}),
            "complete_initial_entry_ap0_decision": dict(diagnostic_summary.get("complete_initial_entry_ap0_decision") or {}),
            "step6_final_ap0_scorecard_connection": dict(diagnostic_summary.get("step6_final_ap0_scorecard_connection") or {}),
            "complete_initial_final_ap0_scorecard_connection": dict(diagnostic_summary.get("complete_initial_final_ap0_scorecard_connection") or {}),
            "complete_initial_next_improvement_meta": dict(diagnostic_summary.get("complete_initial_next_improvement_meta") or {}),
            "limited_composer_extension_baseline": dict(diagnostic_summary.get("limited_composer_extension_baseline") or {}),
            "step0_baseline": dict(diagnostic_summary.get("step0_baseline") or diagnostic_summary.get("limited_composer_extension_baseline") or {}),
            "connection_visibility": dict(diagnostic_summary.get("connection_visibility") or {}),
            "limited_composer_connection_visibility": dict(diagnostic_summary.get("limited_composer_connection_visibility") or diagnostic_summary.get("connection_visibility") or {}),
            "step1_connection_visibility": dict(diagnostic_summary.get("step1_connection_visibility") or diagnostic_summary.get("connection_visibility") or {}),
            "diagnostic_summary_extension": dict(diagnostic_summary.get("diagnostic_summary_extension") or {}),
            "diagnostic_summary_v2": dict(diagnostic_summary.get("diagnostic_summary_v2") or {}),
            "limited_composer_diagnostic_summary_extension": dict(diagnostic_summary.get("limited_composer_diagnostic_summary_extension") or {}),
            "step2_diagnostic_summary_extension": dict(diagnostic_summary.get("step2_diagnostic_summary_extension") or {}),
            "binding_diagnostic": dict(diagnostic_summary.get("binding_diagnostic") or {}),
            "coverage_group": str(diagnostic_summary.get("coverage_group") or ""),
            "failed_stage": str(diagnostic_summary.get("failed_stage") or ""),
            "limited_composer_release": release_meta,
            "phase7_rollout_metrics": phase7_rollout_metrics,
            "step16_rollout_metrics": step16_rollout_metrics,
            "rollout_metrics": step16_rollout_metrics,
            "step9_scorecard_harness": step9_scorecard_harness,
            "limited_composer_scorecard": step9_scorecard_harness,
            "limited_composer_scorecard_harness": step9_scorecard_harness,
            "scorecard_harness": step9_scorecard_harness,
            "step10_e2e_display_contract": step10_e2e_display_contract,
            "limited_composer_e2e_display_contract": step10_e2e_display_contract,
            "e2e_display_contract": step10_e2e_display_contract,
            "step11_e2e_exit_gate": step11_e2e_exit_gate,
            "step11_e2e_test_fixed": step11_e2e_exit_gate,
            "limited_composer_extension_exit_gate": step11_e2e_exit_gate,
            "limited_composer_extension_exit_gate_e2e": step11_e2e_exit_gate,
            "step18_ap0_migration_decision": step18_ap0_migration_decision,
            "a_p0_migration_decision": step18_ap0_migration_decision,
            "complete_composer_initial_ap0_report": complete_composer_initial_ap0_report,
            "ap0_decision_report": complete_composer_initial_ap0_report,
            "step19_a_plan_equivalent": step19_a_plan_equivalent,
            "step19_a_plan_equivalent_composer": step19_a_plan_equivalent,
            "step19_complete_composer_initial": step19_a_plan_equivalent,
            "complete_composer_initial_rollout": step19_a_plan_equivalent,
            "a1_composer_introduction": step19_a_plan_equivalent,
            "step20_long_term_quality": step20_long_term_quality,
            "a2_long_term_quality": step20_long_term_quality,
            "long_term_quality": step20_long_term_quality,
            "step11_complete_reply_diagnostics": step11_complete_reply_diagnostics,
            "step11_complete_reply_service_diagnostics": step11_complete_reply_diagnostics,
            "complete_reply_diagnostics": step11_complete_reply_diagnostics,
            "complete_reply_service_diagnostics": step11_complete_reply_diagnostics,
            "complete_composer_reply_diagnostics": step11_complete_reply_diagnostics,
            "complete_composer_initial_reply_diagnostics": step11_complete_reply_diagnostics,
            "runtime_surface_step8_diagnostics": runtime_surface_step8_diagnostics,
            "runtime_surface_diagnostics_scorecard": runtime_surface_step8_diagnostics,
            "runtime_surface_pre_return_gate_evaluated": bool(runtime_surface_step8_diagnostics.get("runtime_surface_pre_return_gate_evaluated")),
            "runtime_surface_pre_return_gate_passed": bool(runtime_surface_step8_diagnostics.get("runtime_surface_pre_return_gate_passed")),
            "runtime_surface_pre_return_gate_action": str(runtime_surface_step8_diagnostics.get("runtime_surface_pre_return_gate_action") or ""),
            "runtime_surface_pre_return_gate_rejection_reasons": list(runtime_surface_step8_diagnostics.get("runtime_surface_pre_return_gate_rejection_reasons") or []),
            "runtime_surface_pre_return_gate_final_passed": bool(runtime_surface_step8_diagnostics.get("runtime_surface_pre_return_gate_final_passed")),
            "runtime_surface_pre_return_gate_scorecard_connected": bool(runtime_surface_step8_diagnostics.get("runtime_surface_pre_return_gate_scorecard_connected")),
            "runtime_surface_diagnostics_scorecard_updated": bool(runtime_surface_step8_diagnostics.get("runtime_surface_diagnostics_scorecard_updated")),
            "step8_runtime_surface_diagnostics_ready": bool(runtime_surface_step8_diagnostics.get("step8_runtime_surface_diagnostics_ready")),
            "surface_template_major_blocked": bool(runtime_surface_step8_diagnostics.get("surface_template_major_blocked")),
            "malformed_phrase_unit_blocked_count": int(runtime_surface_step8_diagnostics.get("malformed_phrase_unit_blocked_count") or 0),
            "shallow_realizer_version": str(runtime_surface_step8_diagnostics.get("shallow_realizer_version") or ""),
            "shallow_v2_used": bool(runtime_surface_step8_diagnostics.get("shallow_v2_used")),
            "low_information_specificity_used": bool(runtime_surface_step8_diagnostics.get("low_information_specificity_used")),
            "step6_low_information_specificity_ready": bool(runtime_surface_step8_diagnostics.get("step6_low_information_specificity_ready")),
            "safe_anchor_count": int(runtime_surface_step8_diagnostics.get("safe_anchor_count") or 0),
            "uses_safe_anchor": bool(runtime_surface_step8_diagnostics.get("uses_safe_anchor")),
            "safe_anchor_role": str(runtime_surface_step8_diagnostics.get("safe_anchor_role") or ""),
            "safe_anchor_surface_kind": str(runtime_surface_step8_diagnostics.get("safe_anchor_surface_kind") or ""),
            "safe_anchor_evidence_ids": list(runtime_surface_step8_diagnostics.get("safe_anchor_evidence_ids") or []),
            "unsupported_event_assertion_present": bool(runtime_surface_step8_diagnostics.get("unsupported_event_assertion_present")),
            "user_fact_promotion_attempt": bool(runtime_surface_step8_diagnostics.get("user_fact_promotion_attempt")),
            "runtime_surface_source_lock": runtime_surface_source_lock,
            "step1_runtime_surface_source_lock": runtime_surface_source_lock,
            "runtime_surface_source_lock_ready": bool(runtime_surface_source_lock.get("runtime_surface_source_lock_ready")),
            "runtime_surface_source_locked": bool(runtime_surface_source_lock.get("runtime_surface_source_locked")),
            "runtime_composer_source": runtime_surface_source_lock.get("composer_source"),
            "composer_requested": runtime_surface_source_lock.get("composer_requested"),
            "composer_resolved": runtime_surface_source_lock.get("composer_resolved"),
            "runtime_composer_model": runtime_surface_source_lock.get("composer_model"),
            "runtime_surface_source_complete_initial_client_used": bool(runtime_surface_source_lock.get("complete_initial_client_used")),
            "runtime_surface_source_limited_reader_repair_applied": bool(runtime_surface_source_lock.get("limited_reader_repair_applied")),
            "sentence_plan_version": runtime_surface_source_lock.get("sentence_plan_version"),
            "surface_realizer_version": runtime_surface_source_lock.get("surface_realizer_version"),
            "tone_policy_version": runtime_surface_source_lock.get("tone_policy_version"),
            "self_repair_version": runtime_surface_source_lock.get("self_repair_version"),
            "runtime_surface_complete_activation_branch": step6_runtime_surface_complete_activation_branch,
            "step6_runtime_surface_complete_activation_branch": step6_runtime_surface_complete_activation_branch,
            "runtime_surface_complete_activation_branch_ready": bool(step6_runtime_surface_complete_activation_branch.get("runtime_surface_complete_activation_branch_ready")),
            "step6_runtime_surface_complete_activation_branch_ready": bool(step6_runtime_surface_complete_activation_branch.get("step6_complete_runtime_activation_branch_ready")),
            "runtime_surface_complete_activation_status": step6_runtime_surface_complete_activation_branch.get("activation_status"),
            "runtime_surface_complete_initial_resolved": bool(step6_runtime_surface_complete_activation_branch.get("complete_initial_resolved")),
            "runtime_surface_complete_initial_source_lock_aligned": bool(step6_runtime_surface_complete_activation_branch.get("complete_initial_source_lock_aligned")),
            "runtime_surface_complete_initial_resolution_safe_to_measure": bool(step6_runtime_surface_complete_activation_branch.get("complete_initial_resolution_safe_to_measure")),
            "runtime_surface_repair_deferred_until_complete_runtime_measurable": bool(step6_runtime_surface_complete_activation_branch.get("surface_repair_deferred_until_complete_runtime_measurable")),
            "comment_text_body_included": False,
            "complete_composer_initial_runtime": complete_runtime_meta,
            "complete_composer_initial_meta": complete_runtime_meta,
            "complete_composer_meta": complete_runtime_meta,
            "complete_repair_trace": complete_repair_trace,
            "complete_composer_repair_trace": complete_repair_trace,
            "complete_composer_initial_repair_trace": complete_repair_trace,
            "complete_scorecard_event": complete_scorecard_event,
            "complete_composer_scorecard_event": complete_scorecard_event,
            "complete_composer_initial_scorecard_event": complete_scorecard_event,
            "scorecard_event": complete_scorecard_event,
            "step12_complete_scorecard_harness": step12_complete_scorecard_harness,
            "complete_scorecard_harness": step12_complete_scorecard_harness,
            "complete_composer_scorecard_harness": step12_complete_scorecard_harness,
            "complete_composer_initial_scorecard_harness": step12_complete_scorecard_harness,
            "complete_scorecard": step12_complete_scorecard_harness,
            "complete_composer_scorecard": step12_complete_scorecard_harness,
            "complete_composer_initial_scorecard": step12_complete_scorecard_harness,
            "complete_scorecard_fixture_suite": dict(step12_complete_scorecard_harness.get("fixture_suite") or {}),
            "complete_blind_qa_rubric": dict(step12_complete_scorecard_harness.get("blind_qa_rubric") or {}),
            "product_quality_scorecard": step6_product_quality_scorecard,
            "complete_product_quality_scorecard": step6_product_quality_scorecard,
            "complete_composer_product_quality_scorecard": step6_product_quality_scorecard,
            "step6_product_quality_scorecard": step6_product_quality_scorecard,
            "step6_scorecard_blind_qa": step6_product_quality_scorecard,
            "product_quality_blind_qa_rubric": step6_product_quality_blind_qa_rubric,
            "complete_product_quality_blind_qa_rubric": step6_product_quality_blind_qa_rubric,
            "product_quality_machine_metrics": dict(step6_product_quality_scorecard.get("machine_metrics") or {}),
            "step7_product_quality_release_ladder": step7_product_quality_release_ladder,
            "product_quality_release_ladder": step7_product_quality_release_ladder,
            "complete_product_quality_release_ladder": step7_product_quality_release_ladder,
            "complete_composer_product_quality_release_ladder": step7_product_quality_release_ladder,
            "release_ladder_guard": step7_product_quality_release_ladder,
            "step9_fixture_qa_run": step9_complete_initial_fixture_qa_run,
            "step9_product_scorecard_seed": step9_product_scorecard_seed,
            "complete_initial_product_scorecard_seed": step9_product_scorecard_seed,
            "step9_complete_initial_fixture_qa_run": step9_complete_initial_fixture_qa_run,
            "complete_initial_fixture_qa_run": step9_complete_initial_fixture_qa_run,
            "complete_composer_initial_fixture_qa_run": step9_complete_initial_fixture_qa_run,
            "fixture_qa_run": step9_complete_initial_fixture_qa_run,
            "complete_initial_qa_run": step9_complete_initial_fixture_qa_run,
            "rollout_metrics_aggregate": dict(step16_rollout_metrics.get("rollout_metrics_aggregate") or {}),
            "internal_qa_rollout_metrics": dict(step16_rollout_metrics.get("internal_qa_aggregate") or {}),
            "b_plan_connection": b_plan_connection_meta,
            "b_plan_normal_connection": b_plan_connection_meta,
            "normal_connection": b_plan_connection_meta,
            "limited_observation_scope": scope_meta,
            "scoped_grounding": scoped_grounding_meta,
            "text_generation_core": core_generation_meta,
            "core_text_generation": core_generation_meta,
            "step15_common_core_stabilization": core_stabilization_meta,
            "common_core_stabilization": core_stabilization_meta,
            "grounding_graph": grounding_graph_payload,
            "phase_gate": phase_gate_meta,
            "diagnostic_summary": diagnostic_summary,
        },
        "used_sources": used_sources,
        "used_memory_layers": used_memory_layers,
        "reply_length_mode": capability.reply_length_mode,
        "evidence_count": len(evidence_spans),
        "evidence_by_line": {},
        "rejected_candidate_count": 0,
        "fallback_used": False,
        "world_model_debug": {
            "board_report_count": len(getattr(board, "reports", []) or []),
            "missing_information": list(getattr(graph, "missing_information", []) or []),
        },
    }


async def render_emlis_ai_reply(
    *,
    user_id: str,
    subscription_tier: Any,
    current_input: Dict[str, Any],
    display_name: Optional[str] = None,
    timezone_name: Optional[str] = None,
    composer_client: Any = None,
) -> ReplyEnvelope:
    """Render an immediate Emlis observation using the multi-perspective pipeline.

    This path deliberately does not call the legacy observation kernel, legacy
    safe fallback, or input_feedback_text_templates. Display, safety, grounding,
    template, runtime-surface, and visible-surface gates remain fail-closed.

    For displayable response kinds, gate failures are routed through bounded
    repair before any public empty exit is accepted: surface shortening,
    grounding narrowing, assertion softening, low-information observation, or a
    safe state answer. Empty ``comment_text`` is reserved for emergency safety,
    infrastructure failure, or unrecoverable non-displayable terminal states.
    """

    trace_id = f"emlisobs-{uuid4().hex[:16]}"
    capability = resolve_emlis_ai_capability_for_tier(subscription_tier)
    # Phase 1 internal normalization: callers may still pass the legacy dict,
    # but the EmlisAI pipeline reads a stable current-input bundle shape.
    current_input = normalize_emlis_current_input(current_input)
    bundle = await build_emlis_ai_source_bundle(
        user_id=user_id,
        current_input=current_input,
        capability=capability,
        display_name=display_name,
        timezone_name=timezone_name,
    )

    evidence_spans = build_evidence_ledger(current_input)
    observation_structure_material = build_observation_structure_material(
        current_input=current_input,
        evidence_ledger=evidence_spans,
    )
    observation_structure_meta = observation_structure_material_forward_meta(observation_structure_material)
    observation_structure_gate_report = observation_structure_material_gate_report(observation_structure_material)
    reports = run_perspective_observers(evidence_spans)
    board = build_perspective_board(evidence_spans=evidence_spans, reports=reports)
    graph = integrate_perspective_board(board=board, display_name=bundle.display_name or display_name)

    safety_triage_decision = build_emlis_safety_triage_decision(
        current_input=current_input,
        graph=graph,
        evidence_spans=evidence_spans,
    )
    safety_requires_block = bool(
        safety_triage_decision.requires_block
        or has_limited_scope_safety_boundary(graph=graph, evidence_spans=evidence_spans)
    )
    safety_report = None
    if safety_requires_block:
        safety_report = build_emlis_safety_boundary_report(graph=graph, evidence_spans=evidence_spans)
    safety_triage_meta = safety_triage_decision.as_meta()
    phase20_3_material_route = route_emlis_observation_material_eligibility(
        current_input=current_input,
        safety_triage_decision=safety_triage_decision,
    )
    phase20_3_material_route_meta = phase20_3_material_route.as_meta()

    composer_env = dict(os.environ)
    composer_flag_state = default_composer_flag_state(composer_env)
    explicit_complete_initial_client = bool(
        composer_client is not None
        and composer_client.__class__.__name__ == "CocolonCompleteComposerClient"
    )
    limited_observation_scope = None
    if (
        (composer_client is None and bool(composer_flag_state.get("enabled")))
        or explicit_complete_initial_client
        or safety_requires_block
    ):
        limited_observation_scope = build_limited_observation_scope(
            graph=graph,
            evidence_spans=evidence_spans,
        )
    limited_release_decision = evaluate_limited_composer_release(
        user_id=user_id,
        current_input=current_input,
        limited_observation_scope=limited_observation_scope,
        feature_flag_enabled=bool(composer_flag_state.get("enabled")),
        env=composer_env,
    )
    complete_initial_pre_generation_seed = _build_complete_initial_pre_generation_diagnostic_seed(
        composer_flag_state=composer_flag_state,
        limited_release_decision=limited_release_decision,
        limited_observation_scope=limited_observation_scope,
        evidence_spans=evidence_spans,
        reports=reports,
        board=board,
        graph=graph,
        safety_requires_block=safety_requires_block,
    )
    complete_initial_entry_ap0_decision = dict(
        complete_initial_pre_generation_seed.get("complete_initial_entry_ap0_decision") or {}
    )
    complete_initial_entry_ap0_decision["resolver_injection_deferred_to_step3"] = False
    complete_initial_entry_ap0_decision["resolver_ap0_injection_pending"] = False
    complete_initial_entry_ap0_decision["ap0_decision_injected_to_registry_in_step3"] = True
    complete_initial_entry_ap0_decision["used_for_registry_resolution"] = True
    complete_initial_entry_ap0_decision["resolver_injection_completed_in_step3"] = True
    complete_initial_entry_ap0_decision["step3_resolver_ap0_decision_injection_ready"] = True
    complete_initial_pre_generation_seed["complete_initial_entry_ap0_decision"] = complete_initial_entry_ap0_decision
    complete_initial_pre_generation_seed["resolver_injection_deferred_to_step3"] = False
    complete_initial_pre_generation_seed["resolver_ap0_injection_pending"] = False
    # Keep the Step2 historical fact intact, and record the Step3 injection separately.
    complete_initial_pre_generation_seed["ap0_decision_not_injected_to_registry_in_step2"] = True
    complete_initial_pre_generation_seed["ap0_decision_injected_to_registry_in_step3"] = True
    complete_initial_pre_generation_seed["used_for_registry_resolution"] = True
    complete_initial_pre_generation_seed["resolver_injection_completed_in_step3"] = True
    complete_initial_pre_generation_seed["step3_resolver_ap0_decision_injection_ready"] = True
    complete_initial_pre_generation_seed["step3_resolver_ap0_decision_source"] = "complete_initial_entry_ap0_decision"
    composer_client_resolution = resolve_emlis_ai_composer_client(
        composer_client=composer_client,
        safety_requires_block=safety_requires_block,
        env=composer_env,
        release_allowed=bool(getattr(limited_release_decision, "enabled", False)),
        release_meta=limited_release_decision.as_meta(),
        ap0_decision=complete_initial_entry_ap0_decision,
    )
    resolved_composer_client = composer_client_resolution.composer_client
    composer_graph = graph
    grounding_graph = graph
    grounding_scope = "full_graph"
    grounding_allowed_evidence_span_ids: List[str] = []
    complete_initial_candidate_client = bool(
        resolved_composer_client is not None
        and resolved_composer_client.__class__.__name__ == "CocolonCompleteComposerClient"
    )
    if (
        (
            bool(getattr(composer_client_resolution, "default_client_used", False))
            or complete_initial_candidate_client
        )
        and limited_observation_scope is not None
    ):
        composer_graph = limited_observation_scope.scoped_graph
        grounding_graph = composer_graph
        grounding_scope = "limited_scoped_graph"
        grounding_allowed_evidence_span_ids = _evidence_ids_from_observation_graph(grounding_graph)


    # Phase 8: run Display Gate as a fail-closed candidate boundary.  The gate may
    # allow a Composer AI candidate only when every judge passes, the source is
    # ai_generated, and the pipeline phases through Judge are structurally ready.
    # On judge rejection, this boundary may request regeneration with rejection
    # reason codes only.  It never emits sample text or fixed fallback observation;
    # later Phase20 bounded repair / gate recovery decides whether a displayable
    # response kind can still reach a safe ``passed + comment_text`` surface.
    phase5_ready = bool(phase4_observer_contract_ready(reports, evidence_spans) and phase5_board_contract_ready(board) and phase5_observation_graph_ready(board, graph))
    phase6_contract_ready = bool(phase5_ready and phase6_composer_contract_ready())
    composer_candidate = None
    comment_text = ""
    composer_source = ""
    reader_report = judge_listener_readability("")
    grounding_report = judge_grounding(
        comment_text="",
        graph=grounding_graph,
        evidence_spans=evidence_spans,
        allowed_evidence_span_ids=grounding_allowed_evidence_span_ids,
        grounding_scope=grounding_scope,
    )
    template_echo_report = guard_template_echo(comment_text="", evidence_spans=evidence_spans, composer_source="unavailable")
    runtime_surface_pre_return_gate_report: Dict[str, Any] = {}
    visible_surface_acceptance_gate_report: Dict[str, Any] = {}
    initial_binding_meta = build_limited_composer_binding_presence_meta(
        composer_candidate=None,
    )
    display_decision = decide_emlis_observation_display(
        comment_text="",
        reader_report=reader_report,
        grounding_report=grounding_report,
        template_echo_report=template_echo_report,
        safety_report=safety_report,
        trace_id=trace_id,
        composer_source="unavailable" if not safety_requires_block else "",
        phase_completion_ready=False,
        binding_meta=initial_binding_meta,
        observation_structure_gate_report=observation_structure_gate_report,
    )

    complete_initial_default_client = bool(
        getattr(composer_client_resolution, "default_client_used", False)
        and resolved_composer_client is not None
        and resolved_composer_client.__class__.__name__ == "CocolonCompleteComposerClient"
    )
    max_attempts = 0 if safety_requires_block else (1 if complete_initial_default_client else 2 if resolved_composer_client is not None else 1)
    regeneration_reasons: List[str] = []
    last_bounded_reroute_decision = None
    for attempt in range(1, max_attempts + 1):
        composer_candidate = compose_emlis_conversation_candidate(
            graph=composer_graph,
            evidence_spans=evidence_spans,
            display_name=bundle.display_name or display_name,
            greeting_text=build_emlis_observation_greeting(
                display_name=bundle.display_name or display_name,
                greeting_text=getattr(bundle.greeting, "greeting_text", "") if bundle.greeting else "",
            ),
            composer_client=None if safety_requires_block else resolved_composer_client,
            trace_id=trace_id,
            attempt_count=attempt,
            rejection_reasons=regeneration_reasons,
            limited_observation_scope=limited_observation_scope,
            observation_structure_material=observation_structure_material,
        )
        comment_text = "" if safety_requires_block else str(composer_candidate.comment_text or "").strip()
        composer_source = "" if safety_requires_block else str(composer_candidate.composer_source or "")
        reader_report = _judge_listener_readability_for_reply(comment_text, composer_candidate)
        composer_meta_for_grounding = getattr(composer_candidate, "composer_meta", {}) if composer_candidate is not None else {}
        grounding_report = judge_grounding(
            comment_text=comment_text,
            graph=grounding_graph,
            evidence_spans=evidence_spans,
            allowed_evidence_span_ids=grounding_allowed_evidence_span_ids,
            grounding_scope=grounding_scope,
            sentence_bindings=(composer_meta_for_grounding.get("sentence_bindings") if isinstance(composer_meta_for_grounding, dict) else None),
            binding_meta=composer_meta_for_grounding if isinstance(composer_meta_for_grounding, dict) else None,
        )
        template_echo_report = guard_template_echo(
            comment_text=comment_text,
            evidence_spans=evidence_spans,
            composer_source=composer_source,
            composer_model=getattr(composer_candidate, "composer_model", ""),
            generation_method=getattr(composer_candidate, "generation_method", ""),
            generation_scope=getattr(composer_candidate, "generation_scope", ""),
            coverage_scope=getattr(composer_candidate, "coverage_scope", ""),
            composer_meta=getattr(composer_candidate, "composer_meta", {}),
            used_evidence_span_ids=getattr(composer_candidate, "used_evidence_span_ids", []),
        )
        composer_candidate_available = bool(
            composer_source == "ai_generated"
            and str(getattr(composer_candidate, "comment_text", "") or "").strip()
        )
        phase6_ready = bool(phase6_contract_ready and composer_candidate_available)
        phase7_ready = bool(
            phase6_ready
            and phase7_judge_contract_ready(
                reader_report=reader_report,
                grounding_report=grounding_report,
                template_echo_report=template_echo_report,
                composer_source=composer_source,
            )
        )
        candidate_binding_presence = build_limited_composer_binding_presence_meta(
            composer_candidate=composer_candidate,
        )
        runtime_surface_pre_return_gate_report = _build_runtime_surface_pre_return_report_for_candidate(
            comment_text=comment_text,
            composer_candidate=composer_candidate,
            composer_source=composer_source,
            rerender_attempted=attempt > 1,
        )
        visible_surface_acceptance_gate_report = _build_visible_surface_acceptance_report_for_candidate(
            comment_text=comment_text,
            current_input=current_input,
            composer_candidate=composer_candidate,
            composer_source=composer_source,
            rerender_attempted=attempt > 1,
        )
        display_decision = decide_emlis_observation_display(
            comment_text=comment_text,
            reader_report=reader_report,
            grounding_report=grounding_report,
            template_echo_report=template_echo_report,
            safety_report=safety_report,
            trace_id=trace_id,
            composer_source=composer_source,
            phase_completion_ready=phase7_ready,
            binding_meta=candidate_binding_presence,
            observation_structure_gate_report=observation_structure_gate_report,
            runtime_surface_pre_return_gate_report=runtime_surface_pre_return_gate_report,
            visible_surface_acceptance_gate_report=visible_surface_acceptance_gate_report,
        )
        if display_decision.observation_status in {"passed", "safety_blocked"}:
            break
        bounded_reroute_decision = decide_bounded_repair_reroute(
            display_decision=display_decision,
            composer_source=composer_source,
            safety_report=safety_report,
            runtime_surface_pre_return_gate_report=runtime_surface_pre_return_gate_report,
            visible_surface_acceptance_gate_report=visible_surface_acceptance_gate_report,
            repair_allowed=True,
        )
        last_bounded_reroute_decision = bounded_reroute_decision
        if (
            bounded_reroute_decision.action in {BOUNDED_ACTION_RERENDER_SHALLOW_V2, BOUNDED_ACTION_RERENDER_SURFACE}
            and resolved_composer_client is not None
            and attempt < max_attempts
            and str(getattr(composer_candidate, "status", "") or "") != "unavailable"
        ):
            default_bounded_reason = (
                "visible_surface_acceptance_gate_action_rerender_surface"
                if bounded_reroute_decision.action == BOUNDED_ACTION_RERENDER_SURFACE
                else "runtime_surface_pre_return_gate_action_rerender_shallow_v2"
            )
            regeneration_reasons = _regeneration_reasons_for_retry(
                display_decision.rejection_reasons or [],
                resolved_composer_client,
            ) or _regeneration_reasons_for_retry(
                bounded_reroute_decision.repair_reasons or [],
                resolved_composer_client,
            ) or [default_bounded_reason]
            continue
        if resolved_composer_client is None or attempt >= max_attempts or str(getattr(composer_candidate, "status", "") or "") == "unavailable":
            break
        next_regeneration_reasons = _regeneration_reasons_for_retry(
            display_decision.rejection_reasons or [],
            resolved_composer_client,
        )
        if not next_regeneration_reasons:
            break
        regeneration_reasons = next_regeneration_reasons

    phase20_5_original_display_decision = display_decision

    # Step 10: low-information display/repair integration.  This does not
    # loosen Display Gate and does not expose non-passed text.  It now uses
    # Phase20-3 material_quality rather than Phase19 compact case signals to
    # route. Phase20-0 inventory token retained for audit only:
    # complete_initial_low_information_repair_ownership = _phase19_complete_initial_low_information_repair_ownership_meta
    # route into the low-information observation branch, then re-runs the existing passed-only
    # Display Gate with branch-specific reader/grounding/template reports.
    complete_initial_default_requested = str(
        composer_env.get("COCOLON_EMLIS_DEFAULT_COMPOSER")
        or composer_env.get("COCOLON_EMLIS_AI_DEFAULT_COMPOSER")
        or composer_env.get("EMLIS_AI_DEFAULT_COMPOSER")
        or ""
    ).strip().lower() == "complete_initial"
    complete_initial_low_information_repair_ownership = phase20_3_material_route.as_low_information_repair_context(
        complete_initial_default_requested=complete_initial_default_requested,
    )
    complete_initial_low_information_repair_allowed = bool(
        complete_initial_low_information_repair_ownership.get("repair_allowed_under_complete_initial")
    )
    step10_repair_block_reason = ""
    if complete_initial_default_requested and not complete_initial_low_information_repair_allowed:
        step10_repair_block_reason = "complete_initial_runtime_contract_owns_display_failure"
    runtime_repair_block_reason = _step10_repair_runtime_block_reason(
        composer_client_resolution=composer_client_resolution,
        limited_release_decision=limited_release_decision,
    )
    if runtime_repair_block_reason:
        step10_repair_block_reason = runtime_repair_block_reason
        complete_initial_low_information_repair_ownership["repair_allowed_under_complete_initial"] = False
        complete_initial_low_information_repair_ownership["repair_block_reason"] = runtime_repair_block_reason
    observation_display_repair_result = integrate_observation_display_repair(
        current_input=current_input,
        subscription_tier=subscription_tier,
        capability=capability,
        source_bundle=bundle,
        evidence_ledger=evidence_spans,
        observation_graph=graph,
        composer_client_resolution=composer_client_resolution,
        safety_report=safety_report,
        trace_id=trace_id,
        original_display_decision=display_decision,
        original_reader_report=reader_report,
        original_grounding_report=grounding_report,
        original_template_echo_report=template_echo_report,
        original_composer_source=composer_source,
        original_composer_candidate=composer_candidate,
        repair_allowed=not bool(step10_repair_block_reason),
        repair_block_reason=step10_repair_block_reason,
        repair_context=complete_initial_low_information_repair_ownership,
        runtime_surface_pre_return_gate_report=runtime_surface_pre_return_gate_report,
    )
    if observation_display_repair_result.applied:
        display_decision = observation_display_repair_result.display_decision
        reader_report = observation_display_repair_result.reader_report
        grounding_report = observation_display_repair_result.grounding_report
        template_echo_report = observation_display_repair_result.template_echo_report
        composer_source = observation_display_repair_result.composer_source
        composer_candidate = observation_display_repair_result.composer_candidate
        grounding_graph = graph
        grounding_scope = "low_information_known_scope"
        grounding_allowed_evidence_span_ids = list(getattr(grounding_report, "allowed_evidence_span_ids", []) or [])

    pre_public_complete_initial_availability_summary: Dict[str, Any] = {}
    pre_public_surface_requirement_decision: Dict[str, Any] = {}
    try:
        pre_public_binding_meta = build_limited_composer_binding_presence_meta(
            composer_candidate=composer_candidate,
        )
        pre_public_gate_trace = getattr(display_decision, "gate_trace", {}) or build_emlis_gate_trace(
            reader_report=reader_report,
            grounding_report=grounding_report,
            template_echo_report=template_echo_report,
            safety_report=safety_report,
            composer_source=composer_source,
            phase_completion_ready=str(getattr(display_decision, "observation_status", "") or "") == "passed",
            binding_meta=pre_public_binding_meta,
            observation_structure_gate_report=observation_structure_gate_report,
            runtime_surface_pre_return_gate_report=runtime_surface_pre_return_gate_report,
            visible_surface_acceptance_gate_report=visible_surface_acceptance_gate_report,
        )
        pre_public_resolution_meta = _as_meta_dict(composer_client_resolution)
        pre_public_candidate_generation_summary = _build_step5_complete_initial_candidate_generation_meta(
            resolution_meta=pre_public_resolution_meta,
            composer_candidate=composer_candidate,
            display_decision=display_decision,
            gate_trace=pre_public_gate_trace if isinstance(pre_public_gate_trace, dict) else {},
        )
        pre_public_candidate_meta = (
            getattr(composer_candidate, "composer_meta", {})
            if composer_candidate is not None
            else {}
        )
        if not isinstance(pre_public_candidate_meta, Mapping):
            pre_public_candidate_meta = {}
        pre_public_original_composer_diagnostic = (
            dict(pre_public_candidate_meta.get("composer_diagnostic") or {})
            if isinstance(pre_public_candidate_meta.get("composer_diagnostic"), Mapping)
            else {}
        )
        pre_public_candidate_reasons = _dedupe_reason_codes(getattr(composer_candidate, "rejection_reasons", []) or [])
        pre_public_composer_diagnostic_reasons = _dedupe_reason_codes(
            pre_public_original_composer_diagnostic.get("reason_codes") or []
        )
        pre_public_display_reasons = _dedupe_reason_codes(getattr(display_decision, "rejection_reasons", []) or [])
        pre_public_original_reason_codes = _dedupe_reason_codes(
            [
                *pre_public_candidate_reasons,
                *pre_public_composer_diagnostic_reasons,
                *pre_public_display_reasons,
            ]
        )
        pre_public_original_primary_reason = _first_reason(
            [
                value
                for value in pre_public_original_reason_codes
                if value
                in {
                    "limited_composer_shallow_empty_candidate",
                    "composer_source_unavailable",
                    "sentence_plan_unavailable",
                    "empty_comment_text_without_candidate",
                    "complete_initial_surface_unavailable",
                }
            ],
            default=_first_reason(pre_public_original_reason_codes, default=""),
        )
        pre_public_original_composer_status = str(
            getattr(composer_candidate, "status", "")
            or pre_public_original_composer_diagnostic.get("composer_status")
            or ""
        )
        pre_public_original_composer_source = str(
            pre_public_original_composer_diagnostic.get("composer_source")
            or composer_source
            or ""
        )
        if pre_public_original_composer_status in {"unavailable", "not_generated", "not_attempted"}:
            pre_public_original_composer_source = "unavailable"
        pre_public_diagnostic_summary = {
            "complete_initial_candidate_generation_path": pre_public_candidate_generation_summary,
            "step5_candidate_generation_path": pre_public_candidate_generation_summary,
            "complete_initial_runtime": dict(pre_public_candidate_generation_summary.get("runtime") or {}),
            "display_rejection_reasons": list(getattr(display_decision, "rejection_reasons", []) or []),
            "runtime_surface_pre_return_gate": dict(runtime_surface_pre_return_gate_report or {}),
            "visible_surface_acceptance_gate": dict(visible_surface_acceptance_gate_report or {}),
            "candidate_status": pre_public_original_composer_status or "unavailable",
            "composer_status": pre_public_original_composer_status or "unavailable",
            "composer_source": pre_public_original_composer_source or "unavailable",
            "primary_reason": pre_public_original_primary_reason,
            "reason_codes": pre_public_original_reason_codes,
            "composer_reason_category": str(
                pre_public_original_composer_diagnostic.get("reason_category")
                or pre_public_original_composer_diagnostic.get("reason_categories", [""])[0]
                if isinstance(pre_public_original_composer_diagnostic.get("reason_categories"), list)
                and pre_public_original_composer_diagnostic.get("reason_categories")
                else pre_public_original_composer_diagnostic.get("reason_category")
                or ""
            ),
            "composer_diagnostic": pre_public_original_composer_diagnostic,
        }
        pre_public_surface_requirement_decision = resolve_public_surface_requirement(
            current_input=current_input if isinstance(current_input, Mapping) else {},
            material_route=phase20_3_material_route,
            composer_meta=getattr(composer_candidate, "composer_meta", {}) if composer_candidate is not None else {},
            diagnostic_summary=pre_public_diagnostic_summary,
            comment_text_present=bool(str(getattr(composer_candidate, "comment_text", "") or "").strip()),
        )
        pre_public_complete_initial_availability_summary = build_complete_initial_surface_availability_summary(
            diagnostic_summary=pre_public_diagnostic_summary,
            phase_gate={
                "complete_initial_candidate_generation_path": pre_public_candidate_generation_summary,
                "step5_candidate_generation_path": pre_public_candidate_generation_summary,
            },
            candidate_generation_summary=pre_public_candidate_generation_summary,
            surface_requirement=pre_public_surface_requirement_decision,
            material_route=phase20_3_material_route_meta,
        )
    except Exception:
        pre_public_complete_initial_availability_summary = {}
        pre_public_surface_requirement_decision = {}

    gate_recovery_loop_result = None
    phase20_5_gate_recovery_public_boundary_meta: Dict[str, Any] | None = None
    complete_initial_surface_recomposition_result = None
    if (
        str(getattr(display_decision, "observation_status", "") or "") != "passed"
        and not bool(getattr(safety_report, "requires_block", False))
        and safety_triage_decision.safety_triage_kind == TRIAGE_SAFE_OBSERVATION
    ):
        gate_recovery_loop_result = recover_emlis_gate_failure(
            current_input=current_input if isinstance(current_input, Mapping) else {},
            display_decision=display_decision,
            reader_report=reader_report,
            grounding_report=grounding_report,
            template_echo_report=template_echo_report,
            material_route=phase20_3_material_route,
            safety_triage_kind=safety_triage_decision.safety_triage_kind,
            safety_report=safety_report,
            runtime_surface_pre_return_gate_report=runtime_surface_pre_return_gate_report,
            visible_surface_acceptance_gate_report=visible_surface_acceptance_gate_report,
            trace_id=trace_id,
            original_composer_candidate=composer_candidate,
            original_composer_source=composer_source,
            complete_initial_surface_availability_summary=pre_public_complete_initial_availability_summary,
        )
        if gate_recovery_loop_result.applied:
            pre_public_boundary_decision = _reply_service_gate_recovery_public_boundary_decision(
                gate_recovery_loop_result,
                recovery_context=RECOVERY_CONTEXT_PRE_PUBLIC_DISPLAY_GATE,
                composer_client_resolution=composer_client_resolution,
            )
            pre_public_boundary_allowed = gate_recovery_public_display_allowed(pre_public_boundary_decision)
            phase20_5_gate_recovery_public_boundary_meta = _build_reply_service_gate_recovery_public_boundary_meta(
                recovery_context=RECOVERY_CONTEXT_PRE_PUBLIC_DISPLAY_GATE,
                gate_recovery_loop_result=gate_recovery_loop_result,
                public_boundary_decision=pre_public_boundary_decision,
                adopted=pre_public_boundary_allowed,
            )
            if pre_public_boundary_allowed:
                display_decision = gate_recovery_loop_result.display_decision
                reader_report = gate_recovery_loop_result.reader_report
                grounding_report = gate_recovery_loop_result.grounding_report
                template_echo_report = gate_recovery_loop_result.template_echo_report
                composer_source = gate_recovery_loop_result.composer_source
                composer_candidate = gate_recovery_loop_result.composer_candidate
                runtime_surface_pre_return_gate_report = dict(gate_recovery_loop_result.runtime_surface_pre_return_gate_report or {})
                visible_surface_acceptance_gate_report = dict(gate_recovery_loop_result.visible_surface_acceptance_gate_report or {})
                grounding_graph = graph
                grounding_scope = "current_input_material_bundle_recovery"
                grounding_allowed_evidence_span_ids = list(getattr(grounding_report, "allowed_evidence_span_ids", []) or [])
                if (
                    isinstance(pre_public_boundary_decision, Mapping)
                    and str(pre_public_boundary_decision.get("candidate_source_kind") or "")
                    == "complete_initial_surface_recomposition_candidate"
                ):
                    gate_recovery_existing_gate_chain = _reply_service_recomposition_existing_gate_chain_summary(
                        reader_report=gate_recovery_loop_result.reader_report,
                        grounding_report=gate_recovery_loop_result.grounding_report,
                        template_echo_report=gate_recovery_loop_result.template_echo_report,
                        runtime_surface_pre_return_gate_report=dict(
                            gate_recovery_loop_result.runtime_surface_pre_return_gate_report or {}
                        ),
                        visible_surface_acceptance_gate_report=dict(
                            gate_recovery_loop_result.visible_surface_acceptance_gate_report or {}
                        ),
                        display_decision=gate_recovery_loop_result.display_decision,
                        adopted=True,
                    )
                    complete_initial_surface_recomposition_result = {
                        "schema_version": "cocolon.emlis.complete_initial_surface_recomposition.reply_service_result.v1",
                        "source_phase": "PublicObservationRecovery_P5_ReplyServiceGateRecoveryConnection",
                        "attempted": True,
                        "applied": bool(gate_recovery_existing_gate_chain.get("passed_by_all_existing_gates")),
                        "candidate_generated": True,
                        "candidate_source_kind": "complete_initial_surface_recomposition_candidate",
                        "build_reasons": ["complete_initial_surface_recomposition_candidate_built"],
                        "normal_observation_rebuild_used": False,
                        "gate_recovery_material_surface_used": False,
                        "display_gate_relaxed": False,
                        "raw_input_included": False,
                        "comment_text_body_included": False,
                        "candidate_body_in_meta": False,
                        "case_specific_route_used": False,
                        "existing_gate_chain": gate_recovery_existing_gate_chain,
                        "passed_by_all_existing_gates": bool(
                            gate_recovery_existing_gate_chain.get("passed_by_all_existing_gates")
                        ),
                        "candidate_adopted_after_existing_gates": bool(
                            gate_recovery_existing_gate_chain.get("candidate_adopted_after_existing_gates")
                        ),
                    }

    if (
        str(getattr(display_decision, "observation_status", "") or "") != "passed"
        and not bool(getattr(safety_report, "requires_block", False))
        and safety_triage_decision.safety_triage_kind == TRIAGE_SAFE_OBSERVATION
    ):
        (
            recomposition_candidate,
            recomposition_build_reasons,
        ) = build_complete_initial_surface_recomposition_candidate(
            current_input=current_input if isinstance(current_input, Mapping) else {},
            availability_summary=pre_public_complete_initial_availability_summary,
            surface_requirement=pre_public_surface_requirement_decision,
            material_route=phase20_3_material_route_meta,
            trace_id=trace_id,
            recovery_context=RECOVERY_CONTEXT_PRE_PUBLIC_DISPLAY_GATE,
            safety_requires_block=safety_requires_block,
            reply_timeout_or_error=False,
            composer_disabled=bool(
                isinstance(pre_public_complete_initial_availability_summary, Mapping)
                and (
                    str(pre_public_complete_initial_availability_summary.get("first_blocker_family") or "")
                    == "composer_disabled"
                    or str(pre_public_complete_initial_availability_summary.get("first_blocker_code") or "")
                    == "composer_disabled"
                )
            ),
        )
        recomposition_candidate_meta = (
            getattr(recomposition_candidate, "composer_meta", {})
            if recomposition_candidate is not None
            else {}
        )
        if not isinstance(recomposition_candidate_meta, Mapping):
            recomposition_candidate_meta = {}
        complete_initial_surface_recomposition_result = {
            "schema_version": "cocolon.emlis.complete_initial_surface_recomposition.reply_service_result.v1",
            "source_phase": "PublicObservationRecovery_P5_ReplyServiceConnection",
            "attempted": True,
            # Candidate generation and public adoption are intentionally
            # separate.  Step 8 allows adoption only after the recomposed
            # candidate passes the existing reader / grounding / template /
            # runtime / visible / display gates below.
            "applied": False,
            "candidate_generated": recomposition_candidate is not None,
            "candidate_source_kind": str(
                recomposition_candidate_meta.get("candidate_source_kind")
                or "complete_initial_surface_recomposition_candidate"
            ),
            "build_reasons": list(recomposition_build_reasons or []),
            "normal_observation_rebuild_used": False,
            "gate_recovery_material_surface_used": False,
            "display_gate_relaxed": False,
            "raw_input_included": False,
            "comment_text_body_included": False,
            "candidate_body_in_meta": False,
            "case_specific_route_used": False,
            "candidate_adopted_after_existing_gates": False,
        }
        if recomposition_candidate is not None:
            recomposed_candidate = recomposition_candidate
            recomposed_comment_text = str(getattr(recomposed_candidate, "comment_text", "") or "").strip()
            recomposed_composer_source = str(getattr(recomposed_candidate, "composer_source", "") or "")
            recomposed_reader_report = _judge_listener_readability_for_reply(
                recomposed_comment_text,
                recomposed_candidate,
            )
            recomposed_composer_meta = (
                getattr(recomposed_candidate, "composer_meta", {})
                if recomposed_candidate is not None
                else {}
            )
            if not isinstance(recomposed_composer_meta, dict):
                recomposed_composer_meta = {}
            recomposed_allowed_evidence_span_ids = list(
                getattr(recomposed_candidate, "used_evidence_span_ids", []) or grounding_allowed_evidence_span_ids
            )
            recomposed_grounding_report = judge_grounding(
                comment_text=recomposed_comment_text,
                graph=graph,
                evidence_spans=evidence_spans,
                allowed_evidence_span_ids=recomposed_allowed_evidence_span_ids,
                grounding_scope="complete_initial_surface_recomposition",
                sentence_bindings=recomposed_composer_meta.get("sentence_bindings"),
                binding_meta=recomposed_composer_meta,
            )
            recomposed_template_echo_report = guard_template_echo(
                comment_text=recomposed_comment_text,
                evidence_spans=evidence_spans,
                composer_source=recomposed_composer_source,
                composer_model=getattr(recomposed_candidate, "composer_model", ""),
                generation_method=getattr(recomposed_candidate, "generation_method", ""),
                generation_scope=getattr(recomposed_candidate, "generation_scope", ""),
                coverage_scope=getattr(recomposed_candidate, "coverage_scope", ""),
                composer_meta=recomposed_composer_meta,
                used_evidence_span_ids=getattr(recomposed_candidate, "used_evidence_span_ids", []),
            )
            recomposed_binding_presence = build_limited_composer_binding_presence_meta(
                composer_candidate=recomposed_candidate,
            )
            recomposed_runtime_surface_pre_return_gate_report = _build_runtime_surface_pre_return_report_for_candidate(
                comment_text=recomposed_comment_text,
                composer_candidate=recomposed_candidate,
                composer_source=recomposed_composer_source,
                rerender_attempted=False,
            )
            recomposed_visible_surface_acceptance_gate_report = _build_visible_surface_acceptance_report_for_candidate(
                comment_text=recomposed_comment_text,
                current_input=current_input,
                composer_candidate=recomposed_candidate,
                composer_source=recomposed_composer_source,
                rerender_attempted=False,
            )
            recomposed_phase6_ready = bool(recomposed_composer_source == "ai_generated" and recomposed_comment_text)
            recomposed_phase7_ready = bool(
                recomposed_phase6_ready
                and phase7_judge_contract_ready(
                    reader_report=recomposed_reader_report,
                    grounding_report=recomposed_grounding_report,
                    template_echo_report=recomposed_template_echo_report,
                    composer_source=recomposed_composer_source,
                )
            )
            recomposed_display_decision = decide_emlis_observation_display(
                comment_text=recomposed_comment_text,
                reader_report=recomposed_reader_report,
                grounding_report=recomposed_grounding_report,
                template_echo_report=recomposed_template_echo_report,
                safety_report=safety_report,
                trace_id=trace_id,
                composer_source=recomposed_composer_source,
                phase_completion_ready=recomposed_phase7_ready,
                binding_meta=recomposed_binding_presence,
                observation_structure_gate_report=observation_structure_gate_report,
                runtime_surface_pre_return_gate_report=recomposed_runtime_surface_pre_return_gate_report,
                visible_surface_acceptance_gate_report=recomposed_visible_surface_acceptance_gate_report,
            )
            recomposed_existing_gate_chain = _reply_service_recomposition_existing_gate_chain_summary(
                reader_report=recomposed_reader_report,
                grounding_report=recomposed_grounding_report,
                template_echo_report=recomposed_template_echo_report,
                runtime_surface_pre_return_gate_report=recomposed_runtime_surface_pre_return_gate_report,
                visible_surface_acceptance_gate_report=recomposed_visible_surface_acceptance_gate_report,
                display_decision=recomposed_display_decision,
                adopted=False,
            )
            complete_initial_surface_recomposition_result["existing_gate_chain"] = recomposed_existing_gate_chain
            complete_initial_surface_recomposition_result["passed_by_all_existing_gates"] = bool(
                recomposed_existing_gate_chain.get("passed_by_all_existing_gates")
            )
            complete_initial_surface_recomposition_result["candidate_adopted_after_existing_gates"] = False
            if bool(recomposed_existing_gate_chain.get("passed_by_all_existing_gates")):
                recomposed_existing_gate_chain = _reply_service_recomposition_existing_gate_chain_summary(
                    reader_report=recomposed_reader_report,
                    grounding_report=recomposed_grounding_report,
                    template_echo_report=recomposed_template_echo_report,
                    runtime_surface_pre_return_gate_report=recomposed_runtime_surface_pre_return_gate_report,
                    visible_surface_acceptance_gate_report=recomposed_visible_surface_acceptance_gate_report,
                    display_decision=recomposed_display_decision,
                    adopted=True,
                )
                complete_initial_surface_recomposition_result["existing_gate_chain"] = recomposed_existing_gate_chain
                complete_initial_surface_recomposition_result["applied"] = True
                complete_initial_surface_recomposition_result["candidate_adopted_after_existing_gates"] = True
                display_decision = recomposed_display_decision
                reader_report = recomposed_reader_report
                grounding_report = recomposed_grounding_report
                template_echo_report = recomposed_template_echo_report
                composer_source = recomposed_composer_source
                composer_candidate = recomposed_candidate
                runtime_surface_pre_return_gate_report = dict(
                    recomposed_runtime_surface_pre_return_gate_report or {}
                )
                visible_surface_acceptance_gate_report = dict(
                    recomposed_visible_surface_acceptance_gate_report or {}
                )
                grounding_graph = graph
                grounding_scope = "complete_initial_surface_recomposition"
                grounding_allowed_evidence_span_ids = list(
                    getattr(recomposed_grounding_report, "allowed_evidence_span_ids", [])
                    or recomposed_allowed_evidence_span_ids
                )

    self_denial_safe_state_answer_result = None
    phase20_13_post_final_gate_recovery_meta: Dict[str, Any] | None = None
    phase20_13_post_final_response_kind = ""
    phase20_13_post_final_gate_recovery_attempted = False

    # Step 2 final pre-return enforcement.  Low-information repair may replace
    # the candidate after the first display decision, so the exact final public
    # candidate is re-checked by the runtime surface gate before returning.
    final_candidate_text = str(display_decision.comment_text or "").strip()
    post_final_recovery_candidate_text = final_candidate_text
    post_final_precheck_reader_report = reader_report
    post_final_precheck_grounding_report = grounding_report
    post_final_precheck_template_echo_report = template_echo_report
    post_final_precheck_composer_candidate = composer_candidate
    post_final_precheck_composer_source = composer_source
    if final_candidate_text and str(display_decision.observation_status or "") == "passed":
        runtime_surface_pre_return_gate_report = _build_runtime_surface_pre_return_report_for_candidate(
            comment_text=final_candidate_text,
            composer_candidate=composer_candidate,
            composer_source=composer_source,
            rerender_attempted=bool(
                runtime_surface_pre_return_gate_report.get("rerender_attempted")
                if isinstance(runtime_surface_pre_return_gate_report, Mapping)
                else False
            ),
        )
        visible_surface_acceptance_gate_report = _build_visible_surface_acceptance_report_for_candidate(
            comment_text=final_candidate_text,
            current_input=current_input,
            composer_candidate=composer_candidate,
            composer_source=composer_source,
            rerender_attempted=bool(
                visible_surface_acceptance_gate_report.get("rerender_attempted")
                if isinstance(visible_surface_acceptance_gate_report, Mapping)
                else False
            ),
        )
        final_binding_meta = build_limited_composer_binding_presence_meta(
            composer_candidate=composer_candidate,
        )
        display_decision = decide_emlis_observation_display(
            comment_text=final_candidate_text,
            reader_report=reader_report,
            grounding_report=grounding_report,
            template_echo_report=template_echo_report,
            safety_report=safety_report,
            trace_id=trace_id,
            composer_source=composer_source,
            phase_completion_ready=True,
            binding_meta=final_binding_meta,
            observation_structure_gate_report=observation_structure_gate_report,
            runtime_surface_pre_return_gate_report=runtime_surface_pre_return_gate_report,
            visible_surface_acceptance_gate_report=visible_surface_acceptance_gate_report,
        )

    phase20_13_material_quality = str(phase20_3_material_route_meta.get("material_quality") or "").strip()
    phase20_13_response_kind = _phase20_13_response_kind_from_route(
        phase20_3_material_route_meta,
        material_quality=phase20_13_material_quality,
        safety_triage_kind=safety_triage_decision.safety_triage_kind,
    )
    phase20_13_original_final_status = str(getattr(display_decision, "observation_status", "") or "")
    phase20_13_original_final_reasons = _dedupe_reason_codes(getattr(display_decision, "rejection_reasons", []) or [])
    phase20_13_from_gate = _phase20_13_final_gate_name(
        runtime_surface_pre_return_gate_report=runtime_surface_pre_return_gate_report,
        visible_surface_acceptance_gate_report=visible_surface_acceptance_gate_report,
    )
    # P6: a pre-public normal-observation rebuild can survive final pre-return
    # enforcement without running a second post-final recovery attempt.  The
    # post-final origin meta still needs a stable recovery_policy in that
    # one-shot path, so compute the policy before the optional retry branch.
    phase20_13_recovery_policy = (
        "low_information_post_final_recheck"
        if phase20_13_material_quality == "low_information"
        else "limited_grounding_post_final_recheck"
        if phase20_13_material_quality == "limited_grounding"
        else "normal_observation_post_final_recheck"
    )
    if _should_attempt_post_final_gate_recovery(
        display_decision=display_decision,
        final_candidate_text=post_final_recovery_candidate_text,
        safety_requires_block=safety_requires_block,
        safety_report=safety_report,
        safety_triage_kind=safety_triage_decision.safety_triage_kind,
        material_quality=phase20_13_material_quality,
        response_kind=phase20_13_response_kind,
        post_final_recovery_already_attempted=phase20_13_post_final_gate_recovery_attempted,
    ):
        phase20_13_post_final_gate_recovery_attempted = True
        phase20_13_unknown_slots = []
        phase20_3_input_bundle = phase20_3_material_route_meta.get(EMLIS_INPUT_MATERIAL_BUNDLE_META_KEY)
        if isinstance(phase20_3_input_bundle, Mapping):
            phase20_13_unknown_slots = list(phase20_3_input_bundle.get("unknown_slots") or [])
        recovered_runtime_surface_pre_return_gate_report = _build_runtime_surface_pre_return_report_for_candidate(
            comment_text=post_final_recovery_candidate_text,
            composer_candidate=post_final_precheck_composer_candidate,
            composer_source=post_final_precheck_composer_source,
            rerender_attempted=True,
        )
        recovered_visible_surface_acceptance_gate_report = _build_visible_surface_acceptance_report_for_candidate(
            comment_text=post_final_recovery_candidate_text,
            current_input=current_input,
            composer_candidate=post_final_precheck_composer_candidate,
            composer_source=post_final_precheck_composer_source,
            rerender_attempted=True,
        )
        post_final_binding_meta = build_limited_composer_binding_presence_meta(
            composer_candidate=post_final_precheck_composer_candidate,
        )
        post_final_recovered_display_decision = decide_emlis_observation_display(
            comment_text=post_final_recovery_candidate_text,
            reader_report=post_final_precheck_reader_report,
            grounding_report=post_final_precheck_grounding_report,
            template_echo_report=post_final_precheck_template_echo_report,
            safety_report=safety_report,
            trace_id=trace_id,
            composer_source=post_final_precheck_composer_source,
            phase_completion_ready=True,
            binding_meta=post_final_binding_meta,
            observation_reply_kind=phase20_13_response_kind,
            observation_quality_meta=_phase20_13_observation_quality_meta(
                material_quality=phase20_13_material_quality,
                unknown_slots=phase20_13_unknown_slots,
            ),
            observation_structure_gate_report=observation_structure_gate_report,
            runtime_surface_pre_return_gate_report=recovered_runtime_surface_pre_return_gate_report,
            visible_surface_acceptance_gate_report=recovered_visible_surface_acceptance_gate_report,
        )
        if (
            phase20_13_material_quality != "low_information"
            and str(getattr(post_final_recovered_display_decision, "observation_status", "") or "") == "passed"
        ):
            display_decision = post_final_recovered_display_decision
            reader_report = post_final_precheck_reader_report
            grounding_report = post_final_precheck_grounding_report
            template_echo_report = post_final_precheck_template_echo_report
            composer_candidate = post_final_precheck_composer_candidate
            composer_source = post_final_precheck_composer_source
            runtime_surface_pre_return_gate_report = dict(recovered_runtime_surface_pre_return_gate_report or {})
            visible_surface_acceptance_gate_report = dict(recovered_visible_surface_acceptance_gate_report or {})
            phase20_13_post_final_response_kind = phase20_13_response_kind
            phase20_13_post_final_gate_recovery_meta = _build_phase20_13_post_final_gate_recovery_meta(
                attempted=True,
                applied=True,
                original_final_status=phase20_13_original_final_status,
                final_status_after_recovery=str(getattr(display_decision, "observation_status", "") or ""),
                response_kind=phase20_13_response_kind,
                material_quality=phase20_13_material_quality,
                recovery_policy=phase20_13_recovery_policy,
                from_gate=phase20_13_from_gate,
                blocked_reasons=phase20_13_original_final_reasons,
            )
        else:
            post_final_gate_recovery_seed_decision = (
                display_decision
                if phase20_13_material_quality == "low_information"
                and str(getattr(post_final_recovered_display_decision, "observation_status", "") or "") == "passed"
                else post_final_recovered_display_decision
            )
            post_final_gate_recovery_result = recover_emlis_gate_failure(
                current_input=current_input if isinstance(current_input, Mapping) else {},
                display_decision=post_final_gate_recovery_seed_decision,
                reader_report=post_final_precheck_reader_report,
                grounding_report=post_final_precheck_grounding_report,
                template_echo_report=post_final_precheck_template_echo_report,
                material_route=phase20_3_material_route,
                safety_triage_kind=safety_triage_decision.safety_triage_kind,
                safety_report=safety_report,
                runtime_surface_pre_return_gate_report=recovered_runtime_surface_pre_return_gate_report,
                visible_surface_acceptance_gate_report=recovered_visible_surface_acceptance_gate_report,
                trace_id=trace_id,
                recovery_context="post_final_pre_return_gate",
                post_final_gate_failure=True,
                allow_low_information_post_final_recovery=True,
                original_composer_candidate=post_final_precheck_composer_candidate,
                original_composer_source=post_final_precheck_composer_source,
                complete_initial_surface_availability_summary=pre_public_complete_initial_availability_summary,
            )
            if post_final_gate_recovery_result.applied:
                post_final_public_boundary_decision = _reply_service_gate_recovery_public_boundary_decision(
                    post_final_gate_recovery_result,
                    recovery_context=RECOVERY_CONTEXT_POST_FINAL_PRE_RETURN_GATE,
                    composer_client_resolution=composer_client_resolution,
                )
                post_final_public_boundary_allowed = gate_recovery_public_display_allowed(
                    post_final_public_boundary_decision
                )
                post_final_public_boundary_meta = _build_reply_service_gate_recovery_public_boundary_meta(
                    recovery_context=RECOVERY_CONTEXT_POST_FINAL_PRE_RETURN_GATE,
                    gate_recovery_loop_result=post_final_gate_recovery_result,
                    public_boundary_decision=post_final_public_boundary_decision,
                    adopted=post_final_public_boundary_allowed,
                )
                if post_final_public_boundary_allowed:
                    display_decision = post_final_gate_recovery_result.display_decision
                    reader_report = post_final_gate_recovery_result.reader_report
                    grounding_report = post_final_gate_recovery_result.grounding_report
                    template_echo_report = post_final_gate_recovery_result.template_echo_report
                    composer_candidate = post_final_gate_recovery_result.composer_candidate
                    composer_source = post_final_gate_recovery_result.composer_source
                    runtime_surface_pre_return_gate_report = dict(post_final_gate_recovery_result.runtime_surface_pre_return_gate_report or {})
                    visible_surface_acceptance_gate_report = dict(post_final_gate_recovery_result.visible_surface_acceptance_gate_report or {})
                    grounding_graph = graph
                    grounding_scope = "post_final_current_input_material_bundle_recovery"
                    grounding_allowed_evidence_span_ids = list(getattr(grounding_report, "allowed_evidence_span_ids", []) or [])
                    phase20_13_post_final_response_kind = phase20_13_response_kind
                    phase20_13_post_final_gate_recovery_meta = _build_phase20_13_post_final_gate_recovery_meta(
                        attempted=True,
                        applied=True,
                        original_final_status=phase20_13_original_final_status,
                        final_status_after_recovery=str(getattr(display_decision, "observation_status", "") or ""),
                        response_kind=phase20_13_response_kind,
                        material_quality=phase20_13_material_quality,
                        recovery_policy=str(post_final_gate_recovery_result.recovery_policy or "post_final_gate_recovery_loop"),
                        from_gate=phase20_13_from_gate,
                        blocked_reasons=phase20_13_original_final_reasons,
                        public_boundary_meta=post_final_public_boundary_meta,
                    )
                else:
                    phase20_13_post_final_gate_recovery_meta = _build_phase20_13_post_final_gate_recovery_meta(
                        attempted=True,
                        applied=False,
                        original_final_status=phase20_13_original_final_status,
                        final_status_after_recovery=str(getattr(display_decision, "observation_status", "") or ""),
                        response_kind=phase20_13_response_kind,
                        material_quality=phase20_13_material_quality,
                        recovery_policy=str(post_final_gate_recovery_result.recovery_policy or "post_final_gate_recovery_loop"),
                        from_gate=phase20_13_from_gate,
                        blocked_reasons=(
                            _reply_service_gate_recovery_public_boundary_blockers(post_final_public_boundary_meta)
                            or _dedupe_reason_codes(getattr(post_final_gate_recovery_result, "blocked_reasons", []) or [])
                            or phase20_13_original_final_reasons
                        ),
                        public_boundary_meta=post_final_public_boundary_meta,
                    )
            else:
                phase20_13_post_final_gate_recovery_meta = _build_phase20_13_post_final_gate_recovery_meta(
                    attempted=True,
                    applied=False,
                    original_final_status=phase20_13_original_final_status,
                    final_status_after_recovery=str(getattr(display_decision, "observation_status", "") or ""),
                    response_kind=phase20_13_response_kind,
                    material_quality=phase20_13_material_quality,
                    recovery_policy=phase20_13_recovery_policy,
                    from_gate=phase20_13_from_gate,
                    blocked_reasons=(
                        _dedupe_reason_codes(getattr(post_final_recovered_display_decision, "rejection_reasons", []) or [])
                        or _dedupe_reason_codes(getattr(post_final_gate_recovery_result, "blocked_reasons", []) or [])
                        or phase20_13_original_final_reasons
                    ),
                )

    if (
        phase20_13_post_final_gate_recovery_meta is None
        and gate_recovery_loop_result is not None
        and bool(getattr(gate_recovery_loop_result, "applied", False))
        and str(getattr(display_decision, "observation_status", "") or "") == "passed"
        and _clean(phase20_13_response_kind) in _PHASE20_13_DISPLAYABLE_RESPONSE_KINDS
        and _clean(
            _reply_service_gate_recovery_candidate_summary(gate_recovery_loop_result).get("candidate_source_kind")
        ) == CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
    ):
        # P6: a normal-observation rebuild may be selected by the pre-public
        # Gate Recovery loop and then survive the final pre-return enforcement.
        # Record the final-surface origin as post-final diagnostic evidence
        # without running a second recovery attempt or serializing any body.
        final_public_boundary_decision = _reply_service_gate_recovery_public_boundary_decision(
            gate_recovery_loop_result,
            recovery_context=RECOVERY_CONTEXT_POST_FINAL_PRE_RETURN_GATE,
            composer_client_resolution=composer_client_resolution,
        )
        final_public_boundary_allowed = gate_recovery_public_display_allowed(
            final_public_boundary_decision
        )
        final_public_boundary_meta = _build_reply_service_gate_recovery_public_boundary_meta(
            recovery_context=RECOVERY_CONTEXT_POST_FINAL_PRE_RETURN_GATE,
            gate_recovery_loop_result=gate_recovery_loop_result,
            public_boundary_decision=final_public_boundary_decision,
            adopted=final_public_boundary_allowed,
        )
        if final_public_boundary_allowed:
            phase20_13_post_final_response_kind = phase20_13_response_kind
            phase20_13_post_final_gate_recovery_meta = _build_phase20_13_post_final_gate_recovery_meta(
                attempted=True,
                applied=True,
                original_final_status=phase20_13_original_final_status,
                final_status_after_recovery=str(getattr(display_decision, "observation_status", "") or ""),
                response_kind=phase20_13_response_kind,
                material_quality=phase20_13_material_quality,
                recovery_policy=phase20_13_recovery_policy,
                from_gate=phase20_13_from_gate,
                blocked_reasons=phase20_13_original_final_reasons,
                public_boundary_meta=final_public_boundary_meta,
            )

    if (
        str(getattr(display_decision, "observation_status", "") or "") != "passed"
        and safety_triage_decision.safety_triage_kind == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER
        and safety_triage_decision.safe_state_answer_allowed
        and not safety_requires_block
    ):
        self_denial_safe_state_answer_result = build_self_denial_safe_state_answer_result(
            current_input=current_input,
            safety_triage_decision=safety_triage_decision,
            evidence_spans=evidence_spans,
            trace_id=trace_id,
        )
        self_denial_binding_meta = build_limited_composer_binding_presence_meta(
            composer_candidate=self_denial_safe_state_answer_result.candidate,
        )
        display_decision = decide_emlis_observation_display(
            comment_text=str(self_denial_safe_state_answer_result.candidate.comment_text or "").strip(),
            reader_report=self_denial_safe_state_answer_result.reader_report,
            grounding_report=self_denial_safe_state_answer_result.grounding_report,
            template_echo_report=self_denial_safe_state_answer_result.template_echo_report,
            safety_report=None,
            trace_id=trace_id,
            composer_source=str(self_denial_safe_state_answer_result.candidate.composer_source or ""),
            phase_completion_ready=True,
            binding_meta=self_denial_binding_meta,
            observation_reply_kind=SELF_DENIAL_SAFE_STATE_OBSERVATION_REPLY_KIND,
            observation_structure_gate_report=observation_structure_gate_report,
        )
        if str(getattr(display_decision, "observation_status", "") or "") == "passed":
            reader_report = self_denial_safe_state_answer_result.reader_report
            grounding_report = self_denial_safe_state_answer_result.grounding_report
            template_echo_report = self_denial_safe_state_answer_result.template_echo_report
            composer_candidate = self_denial_safe_state_answer_result.candidate
            composer_source = str(composer_candidate.composer_source or "")
            grounding_graph = graph
            grounding_scope = "current_input_self_denial_safe_state"
            grounding_allowed_evidence_span_ids = list(getattr(grounding_report, "allowed_evidence_span_ids", []) or [])

    # No fixed fallback. Display gates remain fail-closed; displayable response
    # kinds must pass bounded repair / recovery before any empty public exit is
    # accepted.
    final_text = str(display_decision.comment_text or "").strip()

    user_label_connection_phase8_visible_meta: Dict[str, Any] = {}
    user_label_connection_phase8_binding_meta: Dict[str, Any] = {}
    user_label_connection_p5_runtime_bridge_summary: Dict[str, Any] = {}
    user_label_connection_p5_regression_handoff_for_p6: Dict[str, Any] = {}
    structure_insight_p6_runtime_bridge_summary: Dict[str, Any] = {}
    p5_p6_split_test_matrix_handoff_summary: Dict[str, Any] = {}

    def _p5_passed_report(report: Any, *, default: bool = False) -> bool:
        if isinstance(report, Mapping):
            if report.get("passed") is True:
                return True
            if report.get("blocked") is True:
                return False
            action = str(report.get("action") or "").strip().lower()
            if action in {"allow", "pass", "passed", "accept"}:
                return True
            classification = str(report.get("classification") or "").strip().lower()
            if classification in {"green", "safe", "accepted", "passed", "pass"}:
                return True
            status = str(report.get("status") or "").strip().lower()
            if status in {"passed", "pass", "ok", "accepted"}:
                return True
            return default
        return default

    def _p5_generic_report_passed(report: Any, *, default: bool = True) -> bool:
        if isinstance(report, Mapping):
            return _p5_passed_report(report, default=default)
        if getattr(report, "passed", None) is True:
            return True
        if getattr(report, "blocked", None) is True:
            return False
        if list(getattr(report, "rejection_reasons", []) or []):
            return False
        return default

    def _p5_existing_gate_reports_for(
        *,
        display_status: str,
        reader: Any,
        grounding: Any,
        template_echo: Any = None,
        safety: Any = None,
        runtime_report: Mapping[str, Any] | None,
        visible_report: Mapping[str, Any] | None,
    ) -> Dict[str, Any]:
        display_passed = str(display_status or "") == "passed"
        return {
            "tone_guard": {
                "passed": bool(display_passed and not list(getattr(reader, "rejection_reasons", []) or [])),
                "primary_reason": "" if display_passed else "display_gate_not_passed",
            },
            "grounding": {
                "passed": bool(getattr(grounding, "passed", False)),
                "primary_reason": "" if bool(getattr(grounding, "passed", False)) else "grounding_not_passed",
            },
            "template_echo": {
                "passed": _p5_generic_report_passed(template_echo, default=True),
                "primary_reason": "" if _p5_generic_report_passed(template_echo, default=True) else "template_echo_not_passed",
            },
            "safety": {
                "passed": _p5_generic_report_passed(safety, default=True),
                "primary_reason": "" if _p5_generic_report_passed(safety, default=True) else "safety_not_passed",
            },
            "runtime_surface_pre_return_gate": {
                "passed": _p5_passed_report(runtime_report or {}, default=False),
                "primary_reason": "" if _p5_passed_report(runtime_report or {}, default=False) else "runtime_surface_pre_return_gate_not_passed",
            },
            "visible_surface_acceptance_gate": {
                "passed": _p5_passed_report(visible_report or {}, default=False),
                "primary_reason": "" if _p5_passed_report(visible_report or {}, default=False) else "visible_surface_acceptance_gate_not_passed",
            },
        }

    def _p5_step_decision(value: Mapping[str, Any] | None, *keys: str) -> str:
        source = value if isinstance(value, Mapping) else {}
        for key in keys or ("decision", "handoff_decision"):
            text = str(source.get(key) or "").strip()
            if text:
                return text
        return "evaluated"

    def _p5_runtime_bridge_contract_summary(
        *,
        p5_readiness: Mapping[str, Any] | None = None,
        p5_visibility_boundary: Mapping[str, Any] | None = None,
        p5_eligibility_matrix: Mapping[str, Any] | None = None,
        p5_surface_role_plan: Mapping[str, Any] | None = None,
        p5_safety_guard: Mapping[str, Any] | None = None,
        p5_product_quality_review: Mapping[str, Any] | None = None,
        p5_limited_visible_connection: Mapping[str, Any] | None = None,
        p5_regression_handoff: Mapping[str, Any] | None = None,
        evaluated: bool = False,
        error_code: str = "",
    ) -> Dict[str, Any]:
        readiness = p5_readiness if isinstance(p5_readiness, Mapping) else {}
        visibility = p5_visibility_boundary if isinstance(p5_visibility_boundary, Mapping) else {}
        eligibility = p5_eligibility_matrix if isinstance(p5_eligibility_matrix, Mapping) else {}
        role_plan = p5_surface_role_plan if isinstance(p5_surface_role_plan, Mapping) else {}
        safety_guard = p5_safety_guard if isinstance(p5_safety_guard, Mapping) else {}
        quality_review = p5_product_quality_review if isinstance(p5_product_quality_review, Mapping) else {}
        limited = p5_limited_visible_connection if isinstance(p5_limited_visible_connection, Mapping) else {}
        handoff_payload = p5_regression_handoff if isinstance(p5_regression_handoff, Mapping) else {}
        handoff_summary = handoff_payload.get("summary") if isinstance(handoff_payload.get("summary"), Mapping) else handoff_payload

        blocked_reason_codes: List[str] = []
        for source in (readiness, visibility, eligibility, role_plan, safety_guard, quality_review, limited, handoff_summary):
            if not isinstance(source, Mapping):
                continue
            blocked_reason_codes.extend(list(source.get("p5_hold_reason_codes") or []))
            blocked_reason_codes.extend(list(source.get("rejection_reasons") or []))
            blocked_reason_codes.extend(list(source.get("blocker_reason_codes") or []))
            blocked_reason_codes.extend(list(source.get("decision_reason_codes") or []))
            blocked_reason_codes.extend(list(source.get("p5_continue_material") or []))
            blocked_reason_codes.extend(list(source.get("p6_hold_material") or []))
        if error_code:
            blocked_reason_codes.append(error_code)
        if not quality_review or int(quality_review.get("review_count") or 0) <= 0:
            blocked_reason_codes.append("p5_product_quality_review_missing")
        blocked_reason_codes = _dedupe_reason_codes(blocked_reason_codes)

        visible_applied = bool(limited.get("limited_visible_connection_applied") is True or limited.get("applied") is True)
        review_count = int(quality_review.get("review_count") or 0)
        product_quality_confirmed = bool(
            quality_review.get("p5_limited_visible_allowed") is True
            and review_count > 0
            and not list(quality_review.get("blocker_reason_codes") or [])
        )
        human_qa_hold_reason_codes = _dedupe_reason_codes(
            [
                *(quality_review.get("blocker_reason_codes") or []),
                *([] if product_quality_confirmed else ["P5-HOLD-001", "p5_human_blind_qa_unconfirmed"]),
            ]
        )
        product_quality_confirmation_layer = {
            "layer": "product_quality_confirmation",
            "product_quality_confirmed": product_quality_confirmed,
            "product_quality_confirmation_source": "human_blind_qa_ratings" if product_quality_confirmed else "none",
            "human_qa_status": "confirmed" if product_quality_confirmed else "pending",
            "human_qa_required": True,
            "human_qa_completed": product_quality_confirmed,
            "human_qa_pending": not product_quality_confirmed,
            "human_qa_hold_id": "" if product_quality_confirmed else "P5-HOLD-001",
            "human_qa_hold_reason_codes": human_qa_hold_reason_codes,
            "review_count": review_count,
            "ratings_only": quality_review.get("ratings_only") is True,
            "machine_metrics_used_for_read_feeling": False,
            "read_feeling_auto_filled_from_machine_metrics": False,
            "release_allowed": False,
        }
        return {
            "schema_version": "cocolon.emlis.user_label_connection.p5_runtime_bridge.v1",
            "step": "P5_RuntimeBridge_Repair_R4_20260612",
            "previous_step": "P5_RuntimeBridge_Repair_R3_20260612",
            "r4_boundary_step": "P5_RuntimeBridge_PublicMetaHumanQABoundary_R4_20260612",
            "visible_connection_owner": "p5_6_limited_visible_connection_boundary",
            "legacy_phase8_connector_scope": "p5_6_internal_boundary_only",
            "reply_service_direct_phase8_call_allowed": False,
            "phase8_connector_internal_to_p5_6_boundary": bool(limited.get("phase8_connector_internal_to_p5_6_boundary") is True),
            "p5_runtime_evaluated": bool(evaluated),
            "runtime_evaluated": bool(evaluated),
            "p5_visible_applied": visible_applied,
            "visible_applied": visible_applied,
            "p5_product_quality_confirmed": product_quality_confirmed,
            "product_quality_confirmed": product_quality_confirmed,
            "p5_human_blind_qa_confirmed": product_quality_confirmed,
            "human_blind_qa_confirmed": product_quality_confirmed,
            "product_quality_complete_claim_allowed": False,
            "p5_completion_claim_allowed": False,
            "product_quality_confirmation_status": "confirmed" if product_quality_confirmed else "human_qa_pending",
            "product_quality_confirmation_source": product_quality_confirmation_layer["product_quality_confirmation_source"],
            "human_qa_status": product_quality_confirmation_layer["human_qa_status"],
            "human_qa_required": True,
            "human_qa_completed": product_quality_confirmed,
            "human_qa_pending": not product_quality_confirmed,
            "p5_hold_001_human_qa_unconfirmed": not product_quality_confirmed,
            "runtime_evaluated_is_not_product_quality_confirmed": bool(evaluated and not product_quality_confirmed),
            "visible_applied_is_not_product_quality_confirmed": bool(visible_applied and not product_quality_confirmed),
            "human_qa_hold_reason_codes": human_qa_hold_reason_codes,
            "runtime_evaluation_layer": {
                "layer": "runtime_evaluated",
                "runtime_evaluated": bool(evaluated),
                "runtime_complete_claim_allowed": False,
                "completion_claim_allowed": False,
            },
            "visible_application_layer": {
                "layer": "visible_applied",
                "visible_applied": visible_applied,
                "comment_text_owner": "input_feedback.comment_text",
                "visible_application_is_product_quality_confirmation": False,
                "rn_visible_contract_changed": False,
            },
            "product_quality_confirmation_layer": product_quality_confirmation_layer,
            "visible_connection_route": str(
                limited.get("visible_connection_route") or "p5_6_boundary_internal_phase8_connector"
            ),
            "phase8_connector_scope": str(limited.get("phase8_connector_scope") or "p5_6_internal_boundary_only"),
            "legacy_phase8_direct_call_used": False,
            "phase8_connector_called_inside_p5_6_boundary": bool(
                limited.get("phase8_connector_called_inside_p5_6_boundary") is True
            ),
            "post_connection_regate_required": True,
            "post_connection_gate_passed": bool(limited.get("post_connection_gate_passed") is True),
            "p5_red_002_closed_by_route": True,
            "p5_step_summary": {
                "p5_0_readiness": _p5_step_decision(readiness),
                "p5_1_visibility_boundary": _p5_step_decision(visibility),
                "p5_2_eligibility_matrix": _p5_step_decision(eligibility),
                "p5_3_surface_role_plan": _p5_step_decision(role_plan, "surface_plan_kind", "decision"),
                "p5_4_safety_guard": _p5_step_decision(safety_guard),
                "p5_5_product_quality_review": "allowed" if quality_review.get("p5_limited_visible_allowed") is True else "blocked",
                "p5_6_limited_visible_connection": "applied" if visible_applied else "blocked",
                "p5_7_regression_handoff": _p5_step_decision(handoff_summary, "handoff_decision", "decision"),
            },
            "blocked_reason_codes": blocked_reason_codes,
            "comment_text_owner": "input_feedback.comment_text",
            "release_allowed": False,
            "public_contract": {
                "public_response_key_added": False,
                "rn_visible_contract_changed": False,
                "api_route_changed": False,
                "db_schema_changed": False,
                "release_allowed": False,
            },
            "body_free": {
                "raw_input_included": False,
                "raw_text_included": False,
                "history_raw_text_included": False,
                "comment_text_body_included": False,
                "candidate_body_included": False,
                "surface_body_included": False,
                "reviewer_free_text_included": False,
                "actual_appended_line_included": False,
                "terminal_output_included": False,
            },
        }

    def _p6_safe_summary(value: Mapping[str, Any] | None) -> Dict[str, Any]:
        source = value if isinstance(value, Mapping) else {}
        summary = source.get("summary") if isinstance(source.get("summary"), Mapping) else None
        return dict(summary or source)

    def _p6_step_decision(value: Mapping[str, Any] | None, *keys: str) -> str:
        source = _p6_safe_summary(value)
        for key in keys or ("decision", "handoff_decision", "verdict"):
            raw_value = source.get(key)
            if isinstance(raw_value, bool):
                if raw_value is True:
                    if key == "p6_inventory_ready":
                        return "ready"
                    if key == "p6_entry_allowed":
                        return "p6_entry_allowed"
                    return "passed"
                continue
            text = str(raw_value or "").strip()
            if text:
                return text
        if source.get("p6_inventory_ready") is True:
            return "ready"
        if source.get("p6_entry_allowed") is True:
            return "p6_entry_allowed"
        if source.get("allow_limited_surface") is True:
            return "allow_limited_surface"
        return "evaluated"

    _P6_R8_NO_CONNECT_FAMILY_CATEGORY_MARKERS = {
        "low_information_short": "low_information_short",
        "low_information": "low_information_short",
        "limited_grounding": "limited_grounding",
        "daily_unpleasant": "daily_unpleasant",
        "daily_unpleasant_reception": "daily_unpleasant",
        "daily_positive": "daily_positive",
        "daily_positive_reception": "daily_positive",
        "positive_only": "positive_only",
        "positive_only_reception": "positive_only",
        "safety_adjacent": "safety_adjacent",
        "safety_triage_required": "safety_triage_required",
        "self_denial": "self_denial",
        "self_denial_safety_adjacent": "self_denial",
        "target_judgement": "target_judgement",
        "target_judgment": "target_judgement",
        "anger_or_boundary": "anger_or_boundary",
        "anger_attack_or_target_blame": "anger_or_boundary",
    }

    def _p6_normalize_runtime_marker(value: Any) -> str:
        return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")

    def _p6_current_tokens_for_runtime_family(current: Mapping[str, Any] | None) -> List[str]:
        cur = current if isinstance(current, Mapping) else {}
        values: List[str] = []
        for key in ("category", "categories", "emotions"):
            raw_value = cur.get(key)
            items = raw_value if isinstance(raw_value, list) else [raw_value]
            for item in items:
                token = _p6_normalize_runtime_marker(item)
                if token:
                    values.append(token)
        details = cur.get("emotion_details")
        if isinstance(details, list):
            for item in details:
                if isinstance(item, Mapping):
                    token = _p6_normalize_runtime_marker(item.get("type"))
                    if token:
                        values.append(token)
        return values

    def _p6_family_for_runtime_evaluation(
        *,
        current: Mapping[str, Any] | None,
        material_route: Mapping[str, Any] | None,
        safety_triage: Mapping[str, Any] | None,
    ) -> str:
        route = material_route if isinstance(material_route, Mapping) else {}
        safety = safety_triage if isinstance(safety_triage, Mapping) else {}
        material_quality_text = str(route.get("material_quality") or "").strip()
        safety_kind = str(safety.get("safety_triage_kind") or "").strip()
        if safety_kind and safety_kind != TRIAGE_SAFE_OBSERVATION:
            return "safety_triage_required"
        cur = current if isinstance(current, Mapping) else {}
        category_values: List[str] = []
        for raw in cur.get("category") if isinstance(cur.get("category"), list) else [cur.get("category")]:
            text = str(raw or "").strip()
            if text:
                category_values.append(text)
        runtime_tokens = _p6_current_tokens_for_runtime_family(cur)
        for token in runtime_tokens:
            mapped = _P6_R8_NO_CONNECT_FAMILY_CATEGORY_MARKERS.get(token)
            if mapped:
                return mapped
        if any(token in runtime_tokens for token in ("うれしい", "嬉しい", "喜び", "安心")):
            return "daily_positive"
        if any(token in runtime_tokens for token in ("自己否定", "消えたい", "もう無理")):
            return "self_denial"
        if material_quality_text == "low_information":
            return "low_information_short"
        if material_quality_text == "limited_grounding":
            return "limited_grounding"
        if route.get("question_required") is True or any(
            token in " ".join(category_values)
            for token in ("自己理解", "整理", "問い", "構造", "内省")
        ):
            return "structure_question"
        return "none"

    def _p6_family_from_current_input() -> str:
        return _p6_family_for_runtime_evaluation(
            current=current_input if isinstance(current_input, Mapping) else {},
            material_route=phase20_3_material_route_meta,
            safety_triage=safety_triage_meta,
        )

    def _p6_relation_family_for_runtime_evaluation(
        *,
        family: str,
        current: Mapping[str, Any] | None,
    ) -> str:
        if family != "structure_question":
            if family in {"low_information", "low_information_short", "limited_grounding"}:
                return "low_information_unspecified_weight"
            if family in {"safety_triage_required", "safety_adjacent", "self_denial"}:
                return "self_denial_identity_split"
            if family == "target_judgement":
                return "target_judgement_agreement"
            if family == "anger_or_boundary":
                return "value_line_crossed"
            if family in {"daily_positive", "positive_only"}:
                return "positive_change_recovery"
            if family == "daily_unpleasant":
                return "daily_discomfort_observation"
            return "history_fact_line_as_insight"
        cur = current if isinstance(current, Mapping) else {}
        emotions = [str(item or "") for item in (cur.get("emotions") or [])] if isinstance(cur.get("emotions"), list) else []
        emotion_details = cur.get("emotion_details") if isinstance(cur.get("emotion_details"), list) else []
        for item in emotion_details:
            if isinstance(item, Mapping):
                emotions.append(str(item.get("type") or ""))
        joined = " ".join(emotions)
        if any(token in joined for token in ("迷い", "怖", "不安", "焦り")):
            return "uncertainty_effort_pair"
        return "desire_blockage_conflict"

    def _p6_dependency_status_from_entry(p6_entry_freeze: Mapping[str, Any] | None) -> str:
        entry_summary = _p6_safe_summary(p6_entry_freeze)
        if entry_summary.get("p4_return_required") is True:
            return "p4_return_required"
        if entry_summary.get("p5_return_required") is True:
            return "p5_return_required"
        if entry_summary.get("p6_entry_allowed") is True:
            return "p5_ready"
        return "p5_hold"

    def _p6_collect_reason_codes(*sources: Mapping[str, Any] | None) -> List[str]:
        reason_codes: List[str] = []
        for source in sources:
            summary = _p6_safe_summary(source)
            for key in (
                "decision_reason_codes",
                "source_reason_codes",
                "blocker_reason_codes",
                "required_regression_missing_suites",
                "required_regression_red_suites",
                "p4_return_material",
                "p5_return_material",
                "p6_continue_material",
                "p7_hold_material",
                "no_connect_reason_codes",
                "blocked_reason_codes",
                "rejection_reasons",
            ):
                reason_codes.extend(list(summary.get(key) or []))
        return _dedupe_reason_codes(reason_codes)

    _P6_R7_ALLOWED_STRUCTURE_QUESTION_RELATIONS = {
        "desire_blockage_conflict",
        "effort_residue",
        "mixed_emotion_coexistence",
        "uncertainty_effort_pair",
    }

    def _p6_limited_surface_quality_rows_for_runtime(
        *,
        family: str,
        relation_family: str,
        p5_dependency_status: str,
        surface_candidate_available: bool,
    ) -> List[Dict[str, Any]]:
        if p5_dependency_status != "p5_ready":
            return []
        if family != "structure_question":
            return []
        if relation_family not in _P6_R7_ALLOWED_STRUCTURE_QUESTION_RELATIONS:
            return []
        if not surface_candidate_available:
            return []
        return [
            {
                "row_id": "p6_runtime_bridge_r7_structure_question_limited_surface_quality",
                "family": "structure_question",
                "relation_family": relation_family,
                "ratings": dict(P6_QUALITY_RUBRIC_DIMENSION_TARGETS),
                "red_flags": [],
                "repair_flags": [],
                "ratings_source": "runtime_limited_surface_safety_threshold",
                "human_blind_qa_completed": False,
                "release_allowed": False,
            }
        ]

    def _p6_runtime_bridge_contract_summary(
        *,
        p6_entry_freeze: Mapping[str, Any] | None = None,
        p6_inventory: Mapping[str, Any] | None = None,
        p6_family_boundary: Mapping[str, Any] | None = None,
        p6_relation_policy: Mapping[str, Any] | None = None,
        p6_quality_rubric: Mapping[str, Any] | None = None,
        p6_gate_hardening: Mapping[str, Any] | None = None,
        p6_surface_role_plan: Mapping[str, Any] | None = None,
        p6_family_review: Mapping[str, Any] | None = None,
        p6_product_quality_review: Mapping[str, Any] | None = None,
        p6_regression_handoff: Mapping[str, Any] | None = None,
        p6_limited_surface_connection: Mapping[str, Any] | None = None,
        p6_post_connection_regate: Mapping[str, Any] | None = None,
        evaluated: bool = False,
        family: str = "none",
        error_code: str = "",
    ) -> Dict[str, Any]:
        p5_dependency_status = _p6_dependency_status_from_entry(p6_entry_freeze)
        family_id = str(family or "none").strip() or "none"
        limited_surface_summary = structure_insight_p6_limited_surface_connection_public_summary(
            p6_limited_surface_connection
        ) or _p6_safe_summary(p6_limited_surface_connection)
        post_regate_summary = _p6_safe_summary(p6_post_connection_regate)
        visible_applied = bool(
            limited_surface_summary.get("visible_applied") is True
            or limited_surface_summary.get("p6_visible_applied") is True
            or limited_surface_summary.get("applied") is True
        )
        visible_family = str(limited_surface_summary.get("visible_family") or ("structure_question" if visible_applied else "none"))
        if visible_family not in {"structure_question", "none"}:
            visible_family = "none"
        raw_seed_count = limited_surface_summary.get("insight_seed_count")
        try:
            insight_seed_count = min(1, max(0, int(raw_seed_count))) if raw_seed_count is not None else (1 if visible_applied else 0)
        except (TypeError, ValueError):
            insight_seed_count = 1 if visible_applied else 0
        r7_attempted = bool(evaluated)
        r7_candidate_generated = bool(
            limited_surface_summary.get("surface_key")
            or limited_surface_summary.get("surface_candidate_key")
            or limited_surface_summary.get("structure_insight_surface_key")
        )
        post_blocked = bool(
            limited_surface_summary.get("p6_post_connection_gate_blocked") is True
            or (bool(post_regate_summary) and post_regate_summary.get("p6_candidate_kept") is False)
        )
        limited_surface_reasons = list(
            limited_surface_summary.get("blocked_reason_codes")
            or limited_surface_summary.get("rejection_reasons")
            or []
        )
        p6_visible_not_applied_reason_codes = _dedupe_reason_codes(
            [
                *([] if visible_applied else ["r7_limited_surface_not_applied"]),
                *(limited_surface_reasons if not visible_applied else []),
                *([REASON_P6_POST_CONNECTION_GATE_BLOCKED] if post_blocked else []),
                *([] if family_id == "structure_question" else [f"no_connect_family:{family_id}"]),
                *([error_code] if error_code else []),
            ]
        )
        blocked_reason_codes = _dedupe_reason_codes(
            [
                *p6_visible_not_applied_reason_codes,
                *_p6_collect_reason_codes(
                    p6_entry_freeze,
                    p6_inventory,
                    p6_family_boundary,
                    p6_relation_policy,
                    p6_quality_rubric,
                    p6_gate_hardening,
                    p6_surface_role_plan,
                    p6_family_review,
                    p6_product_quality_review,
                    p6_regression_handoff,
                    p6_limited_surface_connection,
                ),
            ]
        )[:20]
        p6_product_quality_summary = _p6_safe_summary(p6_product_quality_review)
        p6_product_quality_review_ratings_only = bool(
            p6_product_quality_summary.get("ratings_only") is True
            or (isinstance(p6_product_quality_review, Mapping) and p6_product_quality_review.get("ratings_only") is True)
        )
        limited_surface_meta = {
            "r7_limited_surface_meta_summary_only": True,
            "schema_version": str(limited_surface_summary.get("schema_version") or ""),
            "step": str(limited_surface_summary.get("step") or ""),
            "visible_applied": visible_applied,
            "visible_family": visible_family,
            "runtime_family": family_id,
            "relation_family": str(limited_surface_summary.get("relation_family") or ""),
            "surface_key": str(limited_surface_summary.get("surface_key") or ""),
            "section_placement": str(limited_surface_summary.get("section_placement") or "seen_section"),
            "insight_seed_count": insight_seed_count,
            "max_insight_seed_count": 1,
            "post_connection_gate_passed": bool(limited_surface_summary.get("post_connection_gate_passed") is True and not post_blocked),
            "p6_post_connection_gate_blocked": post_blocked,
            "gate_threshold_relaxed": False,
            "raw_input_included": False,
            "raw_text_included": False,
            "comment_text_body_included": False,
            "candidate_body_included": False,
            "surface_body_included": False,
            "release_allowed": False,
        }
        return {
            "schema_version": "cocolon.emlis.structure_insight.p6_runtime_bridge.v1",
            "step": "P6_RuntimeBridge_Repair_20260612",
            "r7_repair_step": "R7_LimitedSurfaceConnection_20260612",
            "p6_runtime_bridge": True,
            "structure_insight_p6_runtime_bridge": True,
            "runtime_evaluated": bool(evaluated),
            "p6_runtime_evaluated": bool(evaluated),
            "visible_applied": visible_applied,
            "p6_visible_applied": visible_applied,
            "visible_family": visible_family,
            "runtime_family": family_id,
            "r8_repair_step": "R8_NoConnectFamilySafetyLowInfoDailyPositiveRegression_20260612",
            "r8_no_connect_regression": True,
            "p6_product_quality_review_ratings_only": p6_product_quality_review_ratings_only,
            "product_quality_review_ratings_only": p6_product_quality_review_ratings_only,
            "no_connect_family_runtime": "" if family_id == "structure_question" else family_id,
            "no_connect_family_blocked": bool(family_id != "structure_question" and not visible_applied),
            "no_connect_family_runtime_blocked": bool(family_id != "structure_question" and not visible_applied),
            "no_connect_family_visible_applied": False,
            "no_deep_insight_for_daily": True,
            "no_deep_insight_for_low_information": True,
            "no_deep_insight_for_positive_only": True,
            "no_deep_insight_for_safety_adjacent": True,
            "p5_dependency_status": p5_dependency_status,
            "p6_step_summary": {
                "p6_0_entry_freeze": _p6_step_decision(p6_entry_freeze, "handoff_decision"),
                "p6_1_inventory": _p6_step_decision(p6_inventory, "p6_inventory_ready"),
                "p6_2_family_boundary": _p6_step_decision(p6_family_boundary, "decision"),
                "p6_3_relation_policy": _p6_step_decision(p6_relation_policy, "visibility_decision", "decision"),
                "p6_4_quality_rubric": _p6_step_decision(p6_quality_rubric, "verdict"),
                "p6_5_gate_hardening": _p6_step_decision(p6_gate_hardening, "decision"),
                "p6_6_surface_role_plan": _p6_step_decision(p6_surface_role_plan, "surface_plan_kind", "decision"),
                "p6_7_family_review": _p6_step_decision(p6_family_review, "classification", "decision"),
                "p6_8_product_quality_review": _p6_step_decision(p6_product_quality_review, "verdict"),
                "p6_9_regression_handoff": _p6_step_decision(p6_regression_handoff, "decision"),
                "r7_limited_surface_connection": "applied" if visible_applied else "blocked",
            },
            "no_connect_family_preserved": True,
            "r7_limited_surface_connection": True,
            "r7_structure_question_only": True,
            "structure_question_only": True,
            "r7_limited_surface_evaluated": r7_attempted,
            "r7_limited_surface_connected": visible_applied,
            "limited_surface_attempted": r7_attempted,
            "limited_surface_candidate_generated": r7_candidate_generated,
            "limited_surface_structure_question_only": True,
            "limited_surface_allowed_family_only": "structure_question",
            "limited_surface_section_placement": str(limited_surface_meta.get("section_placement") or "seen_section"),
            "limited_surface_meta": limited_surface_meta,
            "p6_visible_not_applied_reason_codes": p6_visible_not_applied_reason_codes,
            "blocked_reason_codes": blocked_reason_codes,
            "comment_text_owner": "input_feedback.comment_text",
            "diagnosis_blocked": True,
            "personality_classification_blocked": True,
            "cause_assertion_blocked": True,
            "future_prediction_blocked": True,
            "action_instruction_blocked": True,
            "target_judgement_blocked": True,
            "insight_seed_count": insight_seed_count,
            "max_insight_seed_count": 1,
            "p6_post_connection_gate_blocked": post_blocked,
            "post_connection_regate": dict(post_regate_summary),
            "gate_threshold_relaxed": False,
            "release_allowed": False,
            "public_contract": {
                "public_response_key_added": False,
                "rn_visible_contract_changed": False,
                "api_route_changed": False,
                "db_schema_changed": False,
                "release_allowed": False,
                "public_release_applied": False,
            },
            "body_free": {
                "raw_input_included": False,
                "raw_text_included": False,
                "comment_text_body_included": False,
                "candidate_body_included": False,
                "surface_body_included": False,
                "history_raw_text_included": False,
                "reviewer_free_text_included": False,
                "terminal_output_included": False,
            },
        }

    if final_text and str(getattr(display_decision, "observation_status", "") or "") == "passed":
        p5_readiness: Dict[str, Any] = {}
        p5_visibility_boundary: Dict[str, Any] = {}
        p5_eligibility_matrix: Dict[str, Any] = {}
        p5_surface_role_plan: Dict[str, Any] = {}
        p5_safety_guard: Dict[str, Any] = {}
        p5_product_quality_review: Dict[str, Any] = {}
        p5_limited_visible_connection_meta: Dict[str, Any] = {}
        p5_regression_handoff: Dict[str, Any] = {}
        try:
            user_label_connection_phase8_reply_meta = {
                "observation_reply_kind": str(
                    phase20_13_post_final_response_kind
                    or phase20_3_material_route_meta.get("response_kind")
                    or ""
                ),
                "eligibility_status": str(phase20_3_material_route_meta.get("material_quality") or ""),
                "material_quality": str(phase20_3_material_route_meta.get("material_quality") or ""),
                "safety_triage_kind": str(safety_triage_meta.get("safety_triage_kind") or ""),
                "observation_status": str(getattr(display_decision, "observation_status", "") or ""),
                "eligible_for_full_observation": phase20_3_material_route_meta.get("eligible_for_full_observation"),
                "question_required": phase20_3_material_route_meta.get("question_required"),
            }
            phase8_meta_only = build_user_label_connection_meta_only_integration(
                current_input,
                source_bundle=bundle,
                capability=capability,
                subscription_tier=subscription_tier,
                observation_reply_meta=user_label_connection_phase8_reply_meta,
                material_quality=phase20_3_material_route_meta.get("material_quality"),
                safety_triage_kind=safety_triage_meta.get("safety_triage_kind"),
                reply_flow_meta_only_connected=True,
            )
            phase8_material_summary = phase8_meta_only.get("material_summary") if isinstance(phase8_meta_only, Mapping) else {}
            phase8_candidate_summary = phase8_meta_only.get("candidate_summary") if isinstance(phase8_meta_only, Mapping) else {}
            phase8_gate_summary = phase8_meta_only.get("gate_summary") if isinstance(phase8_meta_only, Mapping) else {}
            phase8_surface_plan_summary = phase8_meta_only.get("surface_plan_summary") if isinstance(phase8_meta_only, Mapping) else {}
            p5_material_meta = {
                **(dict(phase8_material_summary) if isinstance(phase8_material_summary, Mapping) else {}),
                "source_scope": str(phase8_meta_only.get("source_scope") or phase8_meta_only.get("record_scope") or ""),
                "record_scope": str(phase8_meta_only.get("record_scope") or phase8_meta_only.get("source_scope") or ""),
                "capability_tier": str(phase8_meta_only.get("capability_tier") or subscription_tier or ""),
                "history_connection_evidence_record_count": int(phase8_meta_only.get("history_connection_evidence_record_count") or 0),
                "user_fact_grounding_boundary_passed": True,
            }
            p5_candidate_meta = dict(phase8_candidate_summary) if isinstance(phase8_candidate_summary, Mapping) else {}
            p5_gate_meta = dict(phase8_gate_summary) if isinstance(phase8_gate_summary, Mapping) else {}
            p5_surface_plan_meta = {
                **(dict(phase8_surface_plan_summary) if isinstance(phase8_surface_plan_summary, Mapping) else {}),
                "source_scope": str(phase8_meta_only.get("source_scope") or phase8_meta_only.get("record_scope") or ""),
                "scope_marker_required": True,
                "soft_marker_required": True,
            }
            p5_existing_gate_reports = _p5_existing_gate_reports_for(
                display_status=str(getattr(display_decision, "observation_status", "") or ""),
                reader=reader_report,
                grounding=grounding_report,
                template_echo=template_echo_report,
                safety=safety_report,
                runtime_report=runtime_surface_pre_return_gate_report,
                visible_report=visible_surface_acceptance_gate_report,
            )
            p5_readiness = build_user_label_connection_p5_readiness(
                None,
                connection_decision_summary=phase8_meta_only if isinstance(phase8_meta_only, Mapping) else {},
                user_label_connection_public_summary=user_label_connection_public_summary(phase8_meta_only if isinstance(phase8_meta_only, Mapping) else {}),
                run_id="p5_runtime_bridge_r2_readiness",
            )
            p5_visibility_boundary = build_user_label_connection_p5_visibility_boundary(
                p5_readiness=p5_readiness,
                material_meta=p5_material_meta,
                gate_meta=p5_gate_meta,
                surface_plan_meta=p5_surface_plan_meta,
                observation_reply_meta=user_label_connection_phase8_reply_meta,
                existing_comment_text_present=bool(final_text),
                existing_gate_reports=p5_existing_gate_reports,
                subscription_tier=subscription_tier,
                run_id="p5_runtime_bridge_r2_visibility_boundary",
            )
            p5_eligibility_matrix = build_user_label_connection_p5_eligibility_matrix(
                p5_visibility_boundary=p5_visibility_boundary,
                material_meta=p5_material_meta,
                candidate_meta=p5_candidate_meta,
                gate_meta=p5_gate_meta,
                surface_plan_meta=p5_surface_plan_meta,
                observation_reply_meta=user_label_connection_phase8_reply_meta,
                connectable_family=str(phase8_meta_only.get("connectable_family") or "") if isinstance(phase8_meta_only, Mapping) else "",
                run_id="p5_runtime_bridge_r2_eligibility_matrix",
            )
            p5_surface_role_plan = build_user_label_connection_p5_surface_role_plan(
                p5_eligibility_matrix=p5_eligibility_matrix,
                surface_plan_meta=p5_surface_plan_meta,
                run_id="p5_runtime_bridge_r2_surface_role_plan",
            )
            p5_safety_guard = build_user_label_connection_p5_safety_guard(
                p5_surface_role_plan=p5_surface_role_plan,
                observation_reply_meta=user_label_connection_phase8_reply_meta,
                run_id="p5_runtime_bridge_r2_safety_guard",
            )
            p5_product_quality_review = build_user_label_connection_p5_product_quality_review(
                p5_safety_guard=p5_safety_guard,
                review_rows=[],
                run_id="p5_runtime_bridge_r2_product_quality_review",
            )
            tentative_p5_connection = build_user_label_connection_p5_limited_visible_connection(
                final_text,
                observation_status=str(getattr(display_decision, "observation_status", "") or ""),
                p5_visibility_boundary=p5_visibility_boundary,
                p5_eligibility_matrix=p5_eligibility_matrix,
                p5_surface_role_plan=p5_surface_role_plan,
                p5_safety_guard=p5_safety_guard,
                p5_product_quality_review=p5_product_quality_review,
                existing_gate_reports=p5_existing_gate_reports,
                safety_context=safety_triage_meta.get("safety_triage_kind"),
                run_id="p5_runtime_bridge_r2_limited_visible_connection",
            )
            p5_limited_visible_connection_meta = tentative_p5_connection.as_meta()
            if tentative_p5_connection.applied:
                p5_candidate_text = tentative_p5_connection.comment_text
                p5_reader_report = _judge_listener_readability_for_reply(p5_candidate_text, composer_candidate)
                p5_composer_meta_for_grounding = getattr(composer_candidate, "composer_meta", {}) if composer_candidate is not None else {}
                p5_grounding_report = judge_grounding(
                    comment_text=p5_candidate_text,
                    graph=grounding_graph,
                    evidence_spans=evidence_spans,
                    allowed_evidence_span_ids=grounding_allowed_evidence_span_ids,
                    grounding_scope=grounding_scope,
                    sentence_bindings=(
                        p5_composer_meta_for_grounding.get("sentence_bindings")
                        if isinstance(p5_composer_meta_for_grounding, dict)
                        else None
                    ),
                    binding_meta=p5_composer_meta_for_grounding if isinstance(p5_composer_meta_for_grounding, dict) else None,
                )
                p5_template_echo_report = guard_template_echo(
                    comment_text=p5_candidate_text,
                    evidence_spans=evidence_spans,
                    composer_source=composer_source,
                    composer_model=getattr(composer_candidate, "composer_model", ""),
                    generation_method=getattr(composer_candidate, "generation_method", ""),
                    generation_scope=getattr(composer_candidate, "generation_scope", ""),
                    coverage_scope=getattr(composer_candidate, "coverage_scope", ""),
                    composer_meta=getattr(composer_candidate, "composer_meta", {}),
                    used_evidence_span_ids=getattr(composer_candidate, "used_evidence_span_ids", []),
                )
                p5_runtime_surface_pre_return_gate_report = _build_runtime_surface_pre_return_report_for_candidate(
                    comment_text=p5_candidate_text,
                    composer_candidate=composer_candidate,
                    composer_source=composer_source,
                    rerender_attempted=True,
                )
                p5_visible_surface_acceptance_gate_report = _build_visible_surface_acceptance_report_for_candidate(
                    comment_text=p5_candidate_text,
                    current_input=current_input,
                    composer_candidate=composer_candidate,
                    composer_source=composer_source,
                    rerender_attempted=True,
                )
                p5_binding_meta = build_limited_composer_binding_presence_meta(
                    composer_candidate=composer_candidate,
                )
                p5_display_decision = decide_emlis_observation_display(
                    comment_text=p5_candidate_text,
                    reader_report=p5_reader_report,
                    grounding_report=p5_grounding_report,
                    template_echo_report=p5_template_echo_report,
                    safety_report=safety_report,
                    trace_id=trace_id,
                    composer_source=composer_source,
                    phase_completion_ready=True,
                    binding_meta=p5_binding_meta,
                    observation_structure_gate_report=observation_structure_gate_report,
                    runtime_surface_pre_return_gate_report=p5_runtime_surface_pre_return_gate_report,
                    visible_surface_acceptance_gate_report=p5_visible_surface_acceptance_gate_report,
                )
                final_p5_reports = _p5_existing_gate_reports_for(
                    display_status=str(getattr(p5_display_decision, "observation_status", "") or ""),
                    reader=p5_reader_report,
                    grounding=p5_grounding_report,
                    template_echo=p5_template_echo_report,
                    safety=safety_report,
                    runtime_report=p5_runtime_surface_pre_return_gate_report,
                    visible_report=p5_visible_surface_acceptance_gate_report,
                )
                final_p5_connection = build_user_label_connection_p5_limited_visible_connection(
                    final_text,
                    observation_status=str(getattr(p5_display_decision, "observation_status", "") or ""),
                    p5_visibility_boundary=p5_visibility_boundary,
                    p5_eligibility_matrix=p5_eligibility_matrix,
                    p5_surface_role_plan=p5_surface_role_plan,
                    p5_safety_guard=p5_safety_guard,
                    p5_product_quality_review=p5_product_quality_review,
                    existing_gate_reports=final_p5_reports,
                    safety_context=safety_triage_meta.get("safety_triage_kind"),
                    run_id="p5_runtime_bridge_r2_limited_visible_connection_after_regate",
                )
                p5_limited_visible_connection_meta = final_p5_connection.as_meta()
                p5_post_connection_display_passed = (
                    str(getattr(p5_display_decision, "observation_status", "") or "") == "passed"
                )
                if not (final_p5_connection.applied and p5_post_connection_display_passed):
                    p5_limited_visible_connection_meta = dict(p5_limited_visible_connection_meta)
                    p5_limited_visible_connection_meta["rejection_reasons"] = _dedupe_reason_codes(
                        [
                            "p5_post_connection_gate_blocked",
                            *(p5_limited_visible_connection_meta.get("rejection_reasons") or []),
                            *(getattr(p5_display_decision, "rejection_reasons", []) or []),
                        ]
                    )
                    p5_limited_visible_connection_meta["post_connection_gate_passed"] = False
                    p5_limited_visible_connection_meta["post_connection_regate"] = {
                        "rechecked_after_p5_6_candidate": True,
                        "display_gate_passed": p5_post_connection_display_passed,
                        "reader_gate_passed": _p5_generic_report_passed(p5_reader_report, default=False),
                        "grounding_gate_passed": bool(getattr(p5_grounding_report, "passed", False)),
                        "template_echo_gate_passed": _p5_generic_report_passed(p5_template_echo_report, default=True),
                        "runtime_surface_pre_return_gate_passed": _p5_passed_report(
                            p5_runtime_surface_pre_return_gate_report or {},
                            default=False,
                        ),
                        "visible_surface_acceptance_gate_passed": _p5_passed_report(
                            p5_visible_surface_acceptance_gate_report or {},
                            default=False,
                        ),
                        "p5_candidate_kept": False,
                        "original_final_text_preserved": True,
                        "gate_threshold_relaxed": False,
                    }
                if (
                    final_p5_connection.applied
                    and p5_post_connection_display_passed
                ):
                    final_text = final_p5_connection.comment_text
                    display_decision = p5_display_decision
                    reader_report = p5_reader_report
                    grounding_report = p5_grounding_report
                    template_echo_report = p5_template_echo_report
                    runtime_surface_pre_return_gate_report = dict(p5_runtime_surface_pre_return_gate_report or {})
                    visible_surface_acceptance_gate_report = dict(p5_visible_surface_acceptance_gate_report or {})
                    phase8_meta_for_legacy_public = p5_limited_visible_connection_meta.get("phase8_meta")
                    if isinstance(phase8_meta_for_legacy_public, Mapping):
                        user_label_connection_phase8_visible_meta = dict(phase8_meta_for_legacy_public)
                        user_label_connection_phase8_binding_meta = build_user_label_connection_visible_surface_binding_meta(
                            user_label_connection_phase8_visible_meta,
                            evidence_span_ids=grounding_allowed_evidence_span_ids,
                        )
            p5_regression_handoff = build_user_label_connection_p5_regression_handoff(
                p5_limited_visible_connection=p5_limited_visible_connection_meta,
                p5_product_quality_review=p5_product_quality_review,
                p5_safety_guard=p5_safety_guard,
                p4_regression_handoff=None,
                regression_suite_statuses=[],
                p6_candidate_families=[_p6_family_from_current_input()],
                p6_scope_meta={"p5_runtime_bridge_r2": True, "p6_runtime_bridge_r6_candidate_family": _p6_family_from_current_input()},
                run_id="p5_runtime_bridge_r2_regression_handoff",
            )
            user_label_connection_p5_regression_handoff_for_p6 = (
                dict(p5_regression_handoff) if isinstance(p5_regression_handoff, Mapping) else {}
            )
            user_label_connection_p5_runtime_bridge_summary = _p5_runtime_bridge_contract_summary(
                p5_readiness=p5_readiness,
                p5_visibility_boundary=p5_visibility_boundary,
                p5_eligibility_matrix=p5_eligibility_matrix,
                p5_surface_role_plan=p5_surface_role_plan,
                p5_safety_guard=p5_safety_guard,
                p5_product_quality_review=p5_product_quality_review,
                p5_limited_visible_connection=p5_limited_visible_connection_meta,
                p5_regression_handoff=p5_regression_handoff,
                evaluated=True,
            )
        except Exception:
            user_label_connection_p5_runtime_bridge_summary = _p5_runtime_bridge_contract_summary(
                evaluated=True,
                error_code="p5_runtime_bridge_r2_exception",
            )


    if final_text and str(getattr(display_decision, "observation_status", "") or "") == "passed":
        try:
            p6_runtime_family = _p6_family_for_runtime_evaluation(
                current=current_input if isinstance(current_input, Mapping) else {},
                material_route=phase20_3_material_route_meta,
                safety_triage=safety_triage_meta,
            )
            p6_relation_family = _p6_relation_family_for_runtime_evaluation(
                family=p6_runtime_family,
                current=current_input if isinstance(current_input, Mapping) else {},
            )
            p6_inventory = build_structure_insight_p6_inventory(
                run_id="p6_runtime_bridge_r6_inventory",
            )
            p6_entry_freeze = build_structure_insight_p6_entry_freeze(
                p5_7_regression_handoff=user_label_connection_p5_regression_handoff_for_p6,
                structure_insight_inventory=p6_inventory,
                p6_candidate_families=[p6_runtime_family] if p6_runtime_family != "none" else [],
                p6_scope_meta={
                    "r6_runtime_evaluation_layer": True,
                    "r7_limited_surface_connection_layer": True,
                    "r7_structure_question_only": True,
                    "r8_no_connect_regression": True,
                    "r8_no_connect_families": [
                        "low_information_short",
                        "daily_unpleasant",
                        "daily_positive",
                        "positive_only",
                        "safety_triage_required",
                        "safety_adjacent",
                        "self_denial",
                        "target_judgement",
                        "anger_or_boundary",
                        "limited_grounding",
                    ],
                    "r7_visible_surface_not_started": False,
                    "release_allowed": False,
                    "public_response_key_added": False,
                    "comment_text_body_included": False,
                    "candidate_body_included": False,
                    "surface_body_included": False,
                },
                p6_relation_policy_fixed=True,
                run_id="p6_runtime_bridge_r6_entry_freeze",
            )
            p6_dependency_status = _p6_dependency_status_from_entry(p6_entry_freeze)
            p6_limited_surface_probe_text = ""
            p6_limited_surface_probe_meta: Dict[str, Any] = {}
            if p6_dependency_status == "p5_ready" and p6_runtime_family == "structure_question":
                try:
                    (
                        p6_limited_surface_probe_text,
                        p6_limited_surface_probe_meta,
                    ) = build_structure_insight_p6_limited_surface_candidate_probe(
                        family=p6_runtime_family,
                        relation_family=p6_relation_family,
                    )
                except Exception:
                    p6_limited_surface_probe_text = ""
                    p6_limited_surface_probe_meta = {}
            p6_limited_surface_candidate_generated = bool(
                p6_dependency_status == "p5_ready"
                and p6_runtime_family == "structure_question"
                and str(p6_limited_surface_probe_text or "").strip()
            )
            p6_limited_surface_quality_rows = _p6_limited_surface_quality_rows_for_runtime(
                family=p6_runtime_family,
                relation_family=p6_relation_family,
                p5_dependency_status=p6_dependency_status,
                surface_candidate_available=p6_limited_surface_candidate_generated,
            )

            p6_material_quality = str(phase20_3_material_route_meta.get("material_quality") or "").strip()
            if not p6_material_quality or p6_material_quality not in {"low_information", "limited_grounding", "safety_triage_required"}:
                p6_material_quality = "eligible"
            p6_family_boundary = build_structure_insight_p6_family_boundary(
                family=p6_runtime_family if p6_runtime_family != "none" else None,
                material_quality=p6_material_quality,
                current_input_grounded=True,
                observation_status=str(getattr(display_decision, "observation_status", "") or ""),
                observation_status_connectable=True,
                pre_gate_body_generated=False,
                user_dictionary_fact_assertion_required=False,
                target_judgement_required=False,
                safety_adjacent=bool(safety_triage_meta.get("safety_triage_kind") != TRIAGE_SAFE_OBSERVATION),
                emergency_safety=bool(safety_triage_meta.get("safety_triage_kind") == "safety_blocked_emergency"),
                source_unavailable=False,
                p6_entry_freeze=p6_entry_freeze,
                run_id="p6_runtime_bridge_r7_family_boundary",
            )
            p6_relation_policy = build_structure_insight_p6_relation_policy(
                relation_family=p6_relation_family,
                p6_family_boundary=p6_family_boundary,
                low_information_overread_risk=p6_runtime_family == "low_information",
                target_judgement_required=False,
                self_denial_identity_fact_required=False,
                period_tendency_required=False,
                user_dictionary_fact_claim_required=False,
                gate_required_bypassed=False,
                pre_gate_body_generated=False,
                run_id="p6_runtime_bridge_r7_relation_policy",
            )
            p6_quality_rubric = build_structure_insight_p6_quality_rubric(
                review_rows=p6_limited_surface_quality_rows,
                p6_relation_policy=p6_relation_policy,
                p6_family_boundary=p6_family_boundary,
                run_id="p6_runtime_bridge_r7_quality_rubric",
            )
            p6_gate_hardening = build_structure_insight_p6_gate_hardening(
                proposed_surface=p6_limited_surface_probe_text or None,
                surface_probe=(
                    {
                        "r7_limited_surface_candidate_generated": True,
                        "structure_insight_surface_family": "structure_question",
                        "relation_family": p6_relation_family,
                        "diagnosis_blocked": True,
                        "personality_classification_blocked": True,
                        "cause_assertion_blocked": True,
                        "future_prediction_blocked": True,
                        "action_instruction_blocked": True,
                        "target_judgement_blocked": True,
                    }
                    if p6_limited_surface_candidate_generated
                    else {
                        "r6_evaluation_only": True,
                        "r7_limited_surface_candidate_generated": False,
                        "visible_surface_not_generated": True,
                        "diagnosis_blocked": True,
                        "personality_classification_blocked": True,
                        "cause_assertion_blocked": True,
                        "future_prediction_blocked": True,
                        "action_instruction_blocked": True,
                        "target_judgement_blocked": True,
                    }
                ),
                relation_family=p6_relation_family,
                p6_relation_policy=p6_relation_policy,
                p6_quality_rubric=p6_quality_rubric,
                gate_meta={
                    "gate_threshold_relaxed": False,
                    "comment_text_body_included": False,
                    "candidate_body_included": False,
                    "surface_body_included": False,
                },
                user_dictionary_meta={"user_dictionary_fact_claim_required": False},
                run_id="p6_runtime_bridge_r7_gate_hardening",
            )
            p6_requested_insight_seed_count = 1 if p6_limited_surface_quality_rows else 0
            p6_surface_role_plan = build_structure_insight_p6_surface_role_plan(
                family=p6_runtime_family if p6_runtime_family != "none" else None,
                relation_family=p6_relation_family,
                p6_family_boundary=p6_family_boundary,
                p6_relation_policy=p6_relation_policy,
                p6_quality_rubric=p6_quality_rubric,
                p6_gate_hardening=p6_gate_hardening,
                requested_insight_seed_count=p6_requested_insight_seed_count,
                target_judgement_risk=False,
                surface_plan_meta={
                    "r7_limited_surface_connection": True,
                    "r7_limited_surface_structure_question_only": True,
                    "r8_no_connect_regression": True,
                    "structure_question": p6_runtime_family == "structure_question",
                    "daily_unpleasant": p6_runtime_family == "daily_unpleasant",
                    "daily_positive": p6_runtime_family == "daily_positive",
                    "positive_only": p6_runtime_family == "positive_only",
                    "low_information": p6_runtime_family in {"low_information", "low_information_short"},
                    "low_information_short": p6_runtime_family == "low_information_short",
                    "limited_grounding": p6_runtime_family == "limited_grounding",
                    "safety_triage_required": p6_runtime_family == "safety_triage_required",
                    "safety_adjacent": p6_runtime_family == "safety_adjacent",
                    "self_denial": p6_runtime_family == "self_denial",
                    "target_judgement": p6_runtime_family == "target_judgement",
                    "anger_or_boundary": p6_runtime_family == "anger_or_boundary",
                    "insight_seed_count": p6_requested_insight_seed_count,
                    "max_insight_seed_count": 1,
                    "fixed_sentence_template_added": False,
                },
                run_id="p6_runtime_bridge_r7_surface_role_plan",
            )
            p6_family_review = build_structure_insight_p6_family_review(
                family=p6_runtime_family if p6_runtime_family != "none" else None,
                relation_family=p6_relation_family,
                p6_surface_role_plan=p6_surface_role_plan,
                p6_relation_policy=p6_relation_policy,
                p6_quality_rubric=p6_quality_rubric,
                long_arc_core_count=0,
                long_arc_summary_only=True,
                long_arc_relation_flow_present=False,
                self_understanding_observation_intent=p6_runtime_family == "structure_question",
                self_understanding_uncertainty_boundary=True,
                self_denial_identity_fact_required=False,
                target_judgement_risk=False,
                run_id="p6_runtime_bridge_r7_family_review",
            )
            p6_product_quality_review = build_structure_insight_p6_product_quality_review(
                review_rows=p6_limited_surface_quality_rows,
                p6_quality_rubric=p6_quality_rubric,
                p6_surface_role_plan=p6_surface_role_plan,
                p6_family_review=p6_family_review,
                run_id="p6_runtime_bridge_r7_product_quality_review",
            )
            p6_existing_gate_reports = _p5_existing_gate_reports_for(
                display_status=str(getattr(display_decision, "observation_status", "") or ""),
                reader=reader_report,
                grounding=grounding_report,
                template_echo=template_echo_report,
                safety=safety_report,
                runtime_report=runtime_surface_pre_return_gate_report,
                visible_report=visible_surface_acceptance_gate_report,
            )
            p6_limited_surface_connection = build_structure_insight_p6_limited_surface_connection(
                final_text,
                observation_status=str(getattr(display_decision, "observation_status", "") or ""),
                p6_family_boundary=p6_family_boundary,
                p6_relation_policy=p6_relation_policy,
                p6_quality_rubric=p6_quality_rubric,
                p6_gate_hardening=p6_gate_hardening,
                p6_surface_role_plan=p6_surface_role_plan,
                existing_gate_reports=p6_existing_gate_reports,
                proposed_surface=p6_limited_surface_probe_text,
                structure_insight_surface_meta=p6_limited_surface_probe_meta,
                run_id="p6_runtime_bridge_r7_limited_surface_connection",
            )
            p6_limited_surface_connection_meta: Dict[str, Any] = p6_limited_surface_connection.as_meta()
            p6_post_connection_regate_meta: Dict[str, Any] = {}
            if p6_limited_surface_connection.applied:
                p6_candidate_text = p6_limited_surface_connection.comment_text
                p6_reader_report = _judge_listener_readability_for_reply(p6_candidate_text, composer_candidate)
                p6_composer_meta_for_grounding = getattr(composer_candidate, "composer_meta", {}) if composer_candidate is not None else {}
                p6_grounding_report = judge_grounding(
                    comment_text=p6_candidate_text,
                    graph=grounding_graph,
                    evidence_spans=evidence_spans,
                    allowed_evidence_span_ids=grounding_allowed_evidence_span_ids,
                    grounding_scope=grounding_scope,
                    sentence_bindings=(
                        p6_composer_meta_for_grounding.get("sentence_bindings")
                        if isinstance(p6_composer_meta_for_grounding, dict)
                        else None
                    ),
                    binding_meta=p6_composer_meta_for_grounding if isinstance(p6_composer_meta_for_grounding, dict) else None,
                )
                p6_template_echo_report = guard_template_echo(
                    comment_text=p6_candidate_text,
                    evidence_spans=evidence_spans,
                    composer_source=composer_source,
                    composer_model=getattr(composer_candidate, "composer_model", ""),
                    generation_method=getattr(composer_candidate, "generation_method", ""),
                    generation_scope=getattr(composer_candidate, "generation_scope", ""),
                    coverage_scope=getattr(composer_candidate, "coverage_scope", ""),
                    composer_meta=getattr(composer_candidate, "composer_meta", {}),
                    used_evidence_span_ids=getattr(composer_candidate, "used_evidence_span_ids", []),
                )
                p6_runtime_surface_pre_return_gate_report = _build_runtime_surface_pre_return_report_for_candidate(
                    comment_text=p6_candidate_text,
                    composer_candidate=composer_candidate,
                    composer_source=composer_source,
                    rerender_attempted=True,
                )
                p6_visible_surface_acceptance_gate_report = _build_visible_surface_acceptance_report_for_candidate(
                    comment_text=p6_candidate_text,
                    current_input=current_input,
                    composer_candidate=composer_candidate,
                    composer_source=composer_source,
                    rerender_attempted=True,
                )
                p6_binding_meta = build_limited_composer_binding_presence_meta(composer_candidate=composer_candidate)
                p6_display_decision = decide_emlis_observation_display(
                    comment_text=p6_candidate_text,
                    reader_report=p6_reader_report,
                    grounding_report=p6_grounding_report,
                    template_echo_report=p6_template_echo_report,
                    safety_report=safety_report,
                    trace_id=trace_id,
                    composer_source=composer_source,
                    phase_completion_ready=True,
                    binding_meta=p6_binding_meta,
                    observation_structure_gate_report=observation_structure_gate_report,
                    runtime_surface_pre_return_gate_report=p6_runtime_surface_pre_return_gate_report,
                    visible_surface_acceptance_gate_report=p6_visible_surface_acceptance_gate_report,
                )
                final_p6_reports = _p5_existing_gate_reports_for(
                    display_status=str(getattr(p6_display_decision, "observation_status", "") or ""),
                    reader=p6_reader_report,
                    grounding=p6_grounding_report,
                    template_echo=p6_template_echo_report,
                    safety=safety_report,
                    runtime_report=p6_runtime_surface_pre_return_gate_report,
                    visible_report=p6_visible_surface_acceptance_gate_report,
                )
                final_p6_limited_surface_connection = build_structure_insight_p6_limited_surface_connection(
                    final_text,
                    observation_status=str(getattr(p6_display_decision, "observation_status", "") or ""),
                    p6_family_boundary=p6_family_boundary,
                    p6_relation_policy=p6_relation_policy,
                    p6_quality_rubric=p6_quality_rubric,
                    p6_gate_hardening=p6_gate_hardening,
                    p6_surface_role_plan=p6_surface_role_plan,
                    existing_gate_reports=final_p6_reports,
                    proposed_surface=p6_limited_surface_probe_text,
                    structure_insight_surface_meta=p6_limited_surface_probe_meta,
                    run_id="p6_runtime_bridge_r7_limited_surface_connection_after_regate",
                )
                p6_limited_surface_connection_meta = final_p6_limited_surface_connection.as_meta()
                p6_post_connection_display_passed = str(getattr(p6_display_decision, "observation_status", "") or "") == "passed"
                p6_post_connection_regate_meta = {
                    "rechecked_after_p6_limited_surface_candidate": True,
                    "display_gate_passed": p6_post_connection_display_passed,
                    "reader_gate_passed": _p5_generic_report_passed(p6_reader_report, default=False),
                    "grounding_gate_passed": bool(getattr(p6_grounding_report, "passed", False)),
                    "template_echo_gate_passed": _p5_generic_report_passed(p6_template_echo_report, default=True),
                    "runtime_surface_pre_return_gate_passed": _p5_passed_report(p6_runtime_surface_pre_return_gate_report or {}, default=False),
                    "visible_surface_acceptance_gate_passed": _p5_passed_report(p6_visible_surface_acceptance_gate_report or {}, default=False),
                    "p6_candidate_kept": bool(final_p6_limited_surface_connection.applied and p6_post_connection_display_passed),
                    "original_final_text_preserved": not bool(final_p6_limited_surface_connection.applied and p6_post_connection_display_passed),
                    "gate_threshold_relaxed": False,
                }
                p6_limited_surface_connection_meta = dict(p6_limited_surface_connection_meta)
                p6_limited_surface_connection_meta["post_connection_regate"] = dict(p6_post_connection_regate_meta)
                if not (final_p6_limited_surface_connection.applied and p6_post_connection_display_passed):
                    p6_limited_surface_connection_meta["rejection_reasons"] = _dedupe_reason_codes(
                        [
                            REASON_P6_POST_CONNECTION_GATE_BLOCKED,
                            *(p6_limited_surface_connection_meta.get("rejection_reasons") or []),
                            *(getattr(p6_display_decision, "rejection_reasons", []) or []),
                        ]
                    )
                    p6_limited_surface_connection_meta["blocked_reason_codes"] = _dedupe_reason_codes(
                        p6_limited_surface_connection_meta.get("rejection_reasons") or []
                    )
                    p6_limited_surface_connection_meta["visible_applied"] = False
                    p6_limited_surface_connection_meta["p6_visible_applied"] = False
                    p6_limited_surface_connection_meta["r7_limited_surface_connected"] = False
                    p6_limited_surface_connection_meta["p6_limited_surface_r7_connected"] = False
                    p6_limited_surface_connection_meta["visible_family"] = "none"
                    p6_limited_surface_connection_meta["insight_seed_count"] = 0
                    p6_limited_surface_connection_meta["post_connection_gate_passed"] = False
                    p6_limited_surface_connection_meta["p6_post_connection_gate_blocked"] = True
                else:
                    final_text = final_p6_limited_surface_connection.comment_text
                    display_decision = p6_display_decision
                    reader_report = p6_reader_report
                    grounding_report = p6_grounding_report
                    template_echo_report = p6_template_echo_report
                    runtime_surface_pre_return_gate_report = dict(p6_runtime_surface_pre_return_gate_report or {})
                    visible_surface_acceptance_gate_report = dict(p6_visible_surface_acceptance_gate_report or {})
            p6_regression_handoff = build_structure_insight_p6_regression_handoff(
                p6_entry_freeze=p6_entry_freeze,
                p6_family_boundary=p6_family_boundary,
                p6_relation_policy=p6_relation_policy,
                p6_gate_hardening=p6_gate_hardening,
                p6_surface_role_plan=p6_surface_role_plan,
                p6_family_review=p6_family_review,
                p6_product_quality_review=p6_product_quality_review,
                regression_statuses=[],
                p7_review_meta={
                    "r6_runtime_evaluation_layer": True,
                    "r7_limited_surface_connection_layer": True,
                    "r7_structure_question_only": True,
                    "p7_not_started": True,
                    "manual_read_feel_confirmed": False,
                    "long_run_sequence_evaluated": False,
                    "release_allowed": False,
                },
                run_id="p6_runtime_bridge_r7_regression_handoff",
            )
            structure_insight_p6_runtime_bridge_summary = _p6_runtime_bridge_contract_summary(
                p6_entry_freeze=p6_entry_freeze,
                p6_inventory=p6_inventory,
                p6_family_boundary=p6_family_boundary,
                p6_relation_policy=p6_relation_policy,
                p6_quality_rubric=p6_quality_rubric,
                p6_gate_hardening=p6_gate_hardening,
                p6_surface_role_plan=p6_surface_role_plan,
                p6_family_review=p6_family_review,
                p6_product_quality_review=p6_product_quality_review,
                p6_regression_handoff=p6_regression_handoff,
                p6_limited_surface_connection=p6_limited_surface_connection_meta,
                p6_post_connection_regate=p6_post_connection_regate_meta,
                evaluated=True,
                family=p6_runtime_family,
            )
        except Exception:
            structure_insight_p6_runtime_bridge_summary = _p6_runtime_bridge_contract_summary(
                evaluated=True,
                family="none",
                error_code="p6_runtime_bridge_r7_exception",
            )

    if user_label_connection_p5_runtime_bridge_summary or structure_insight_p6_runtime_bridge_summary:
        p5_p6_split_test_matrix_handoff_summary = build_p5_p6_handoff_lock(
            p5_runtime_bridge_summary=user_label_connection_p5_runtime_bridge_summary,
            p6_runtime_bridge_summary=structure_insight_p6_runtime_bridge_summary,
        )

    meta = _multi_perspective_meta(
        trace_id=trace_id,
        capability=capability,
        bundle=bundle,
        evidence_spans=evidence_spans,
        reports=reports,
        board=board,
        graph=graph,
        reader_report=reader_report,
        grounding_report=grounding_report,
        template_echo_report=template_echo_report,
        display_decision=display_decision,
        composer_source=composer_source,
        composer_candidate=composer_candidate,
        composer_client_resolution=composer_client_resolution,
        limited_observation_scope=limited_observation_scope,
        limited_release_decision=limited_release_decision,
        grounding_graph=grounding_graph,
        grounding_scope=grounding_scope,
        grounding_allowed_evidence_span_ids=grounding_allowed_evidence_span_ids,
        complete_initial_pre_generation_seed=complete_initial_pre_generation_seed,
    )
    meta[EMLIS_SAFETY_TRIAGE_META_KEY] = dict(safety_triage_meta)
    meta = attach_phase20_3_observation_eligibility_route_meta(meta, phase20_3_material_route)
    if isinstance(meta.get("diagnostic_summary"), dict):
        meta["diagnostic_summary"][EMLIS_SAFETY_TRIAGE_META_KEY] = dict(safety_triage_meta)
        meta["diagnostic_summary"][EMLIS_OBSERVATION_ELIGIBILITY_ROUTER_META_KEY] = dict(phase20_3_material_route_meta)
        meta["diagnostic_summary"]["phase20_3_input_material_bundle"] = dict(
            phase20_3_material_route_meta.get(EMLIS_INPUT_MATERIAL_BUNDLE_META_KEY) or {}
        )
        try:
            phase20_3_surface_requirement_decision = resolve_public_surface_requirement(
                current_input=current_input if isinstance(current_input, Mapping) else {},
                material_route=phase20_3_material_route,
                composer_meta=getattr(composer_candidate, "composer_meta", {}) if composer_candidate is not None else {},
                diagnostic_summary=meta["diagnostic_summary"],
                comment_text_present=bool(str(getattr(composer_candidate, "comment_text", "") or "").strip()),
            )
            meta["diagnostic_summary"]["public_surface_requirement"] = dict(phase20_3_surface_requirement_decision)
            meta["diagnostic_summary"]["surface_requirement"] = dict(phase20_3_surface_requirement_decision)
            phase_gate_for_availability = meta.get("phase_gate") if isinstance(meta.get("phase_gate"), dict) else {}
            if isinstance(phase_gate_for_availability, dict):
                phase_gate_for_availability["public_surface_requirement"] = dict(phase20_3_surface_requirement_decision)
                phase_gate_for_availability["surface_requirement"] = dict(phase20_3_surface_requirement_decision)
                phase_gate_for_availability["phase20_3_material_route_available_for_p4"] = True
                phase_gate_for_availability["phase20_3_material_quality_for_p4"] = str(
                    phase20_3_material_route_meta.get("material_quality") or ""
                )
                phase_gate_for_availability["phase20_3_response_kind_for_p4"] = str(
                    phase20_3_material_route_meta.get("response_kind") or ""
                )
            _attach_p4_complete_initial_surface_availability_summary(
                diagnostic_summary=meta["diagnostic_summary"],
                phase_gate_meta=phase_gate_for_availability if isinstance(phase_gate_for_availability, dict) else {},
                surface_requirement=phase20_3_surface_requirement_decision,
                material_route=phase20_3_material_route_meta,
            )
        except Exception:
            pass
    if isinstance(meta.get("phase_gate"), dict):
        meta["phase_gate"].update(
            {
                "phase20_2_safety_triage_ready": True,
                "phase20_2_safety_triage_kind": str(safety_triage_meta.get("safety_triage_kind") or ""),
                "phase20_2_response_kind": str(safety_triage_meta.get("response_kind") or ""),
                "phase20_2_emergency_not_converted_to_observation": not bool(
                    safety_triage_meta.get("safety_triage_kind") == "safety_blocked_emergency"
                    and safety_triage_meta.get("public_emlis_observation_allowed") is True
                ),
                "phase20_2_self_denial_identity_fact_rejected": bool(
                    safety_triage_meta.get("safety_triage_kind") != "self_denial_safe_state_answer"
                    or safety_triage_meta.get("must_not_accept_identity_claim_as_fact") is True
                ),
                "phase20_3_input_material_bundle_ready": True,
                "phase20_3_material_quality": str(phase20_3_material_route_meta.get("material_quality") or ""),
                "phase20_3_response_kind": str(phase20_3_material_route_meta.get("response_kind") or ""),
                "phase20_3_case_specific_route_used": bool(
                    phase20_3_material_route_meta.get("case_specific_route_used")
                ),
                "phase20_3_c_d_specific_runtime_cue_used": bool(
                    phase20_3_material_route_meta.get("c_d_specific_runtime_cue_used")
                ),
            }
        )
    if self_denial_safe_state_answer_result is not None:
        meta["self_denial_safe_state_answer"] = self_denial_safe_state_answer_result.as_meta()
        if str(getattr(display_decision, "observation_status", "") or "") == "passed":
            meta["observation_reply_kind"] = SELF_DENIAL_SAFE_STATE_OBSERVATION_REPLY_KIND
    meta = attach_observation_display_repair_meta(meta, observation_display_repair_result)
    if phase20_5_gate_recovery_public_boundary_meta is not None:
        meta[_PHASE20_5_GATE_RECOVERY_PUBLIC_BOUNDARY_META_KEY] = dict(
            phase20_5_gate_recovery_public_boundary_meta
        )
        if isinstance(meta.get("diagnostic_summary"), dict):
            meta["diagnostic_summary"][_PHASE20_5_GATE_RECOVERY_PUBLIC_BOUNDARY_META_KEY] = dict(
                phase20_5_gate_recovery_public_boundary_meta
            )
        if isinstance(meta.get("phase_gate"), dict):
            meta["phase_gate"].update(
                {
                    "phase20_5_reply_service_gate_recovery_public_boundary_checked": True,
                    "phase20_5_reply_service_gate_recovery_public_boundary_blocked": bool(
                        phase20_5_gate_recovery_public_boundary_meta.get("blocked")
                    ),
                    "phase20_5_reply_service_gate_recovery_public_display_allowed": bool(
                        phase20_5_gate_recovery_public_boundary_meta.get("public_display_allowed")
                    ),
                    "phase20_5_reply_service_gate_recovery_adopted": bool(
                        phase20_5_gate_recovery_public_boundary_meta.get("adopted")
                    ),
                }
            )
    if complete_initial_surface_recomposition_result is not None:
        complete_initial_surface_recomposition_meta = dict(complete_initial_surface_recomposition_result)
        meta[COMPLETE_INITIAL_SURFACE_RECOMPOSITION_PUBLIC_META_KEY] = dict(
            complete_initial_surface_recomposition_meta
        )
        if bool(complete_initial_surface_recomposition_meta.get("applied")):
            meta["observation_reply_kind"] = "complete_initial_surface_recomposition"
        if isinstance(meta.get("diagnostic_summary"), dict):
            meta["diagnostic_summary"][COMPLETE_INITIAL_SURFACE_RECOMPOSITION_PUBLIC_META_KEY] = dict(
                complete_initial_surface_recomposition_meta
            )
        if isinstance(meta.get("phase_gate"), dict):
            meta["phase_gate"].update(
                {
                    "p5_complete_initial_surface_recomposition_attempted": bool(
                        complete_initial_surface_recomposition_meta.get("attempted")
                    ),
                    "p5_complete_initial_surface_recomposition_applied": bool(
                        complete_initial_surface_recomposition_meta.get("applied")
                    ),
                    "p5_complete_initial_surface_recomposition_candidate_generated": bool(
                        complete_initial_surface_recomposition_meta.get("candidate_generated")
                    ),
                    "p5_complete_initial_surface_recomposition_normal_rebuild_used": False,
                    "p5_complete_initial_surface_recomposition_gate_recovery_material_surface_used": False,
                    "p5_complete_initial_surface_recomposition_display_gate_relaxed": False,
                    "p5_complete_initial_surface_recomposition_comment_text_body_included": False,
                    "p5_complete_initial_surface_recomposition_raw_input_included": False,
                    "p5_complete_initial_surface_recomposition_candidate_body_in_meta": False,
                    "p5_complete_initial_surface_recomposition_case_specific_route_used": False,
                }
            )

    if phase20_13_post_final_gate_recovery_meta is not None:
        meta[_PHASE20_13_POST_FINAL_GATE_RECOVERY_META_KEY] = dict(phase20_13_post_final_gate_recovery_meta)
        if phase20_13_post_final_response_kind:
            meta["observation_reply_kind"] = phase20_13_post_final_response_kind
        if isinstance(meta.get("diagnostic_summary"), dict):
            meta["diagnostic_summary"][_PHASE20_13_POST_FINAL_GATE_RECOVERY_META_KEY] = dict(
                phase20_13_post_final_gate_recovery_meta
            )
        if isinstance(meta.get("phase_gate"), dict):
            meta["phase_gate"].update(
                {
                    "phase20_13_post_final_gate_recovery_attempted": bool(
                        phase20_13_post_final_gate_recovery_meta.get("attempted")
                    ),
                    "phase20_13_post_final_gate_recovery_applied": bool(
                        phase20_13_post_final_gate_recovery_meta.get("applied")
                    ),
                    "phase20_13_post_final_gate_recovery_public_response_key_change": False,
                    "phase20_13_post_final_gate_recovery_fixed_fallback_used": False,
                }
            )
    phase20_5_gate_recovery_loop = build_gate_recovery_loop_decision(
        original_display_decision=phase20_5_original_display_decision,
        final_display_decision=display_decision,
        safety_report=safety_report,
        safety_triage_kind=str(safety_triage_meta.get("safety_triage_kind") or ""),
        material_quality=phase20_3_material_route_meta,
        observation_display_repair_result=observation_display_repair_result,
        bounded_repair_reroute_decision=last_bounded_reroute_decision,
    )
    meta = attach_gate_recovery_loop_meta(meta, phase20_5_gate_recovery_loop)
    meta = attach_emlis_internal_response_contract(
        meta,
        observation_status=str(getattr(display_decision, "observation_status", "") or "unavailable"),
        observation_reply_kind=str(
            meta.get("observation_reply_kind")
            or (
                meta.get("step10_observation_display_repair_integration", {})
                if isinstance(meta.get("step10_observation_display_repair_integration"), Mapping)
                else {}
            ).get("observation_reply_kind")
            or ""
        ),
        rejection_reasons=list(getattr(display_decision, "rejection_reasons", []) or []),
        reason="phase20_5_gate_recovery_loop_bridge",
        repair_attempts=phase20_5_gate_recovery_loop.repair_attempts_for_internal_contract(),
    )
    meta["emlis_observation_structure_dictionary"] = observation_structure_meta
    meta["observation_structure_gate"] = observation_structure_gate_report
    if isinstance(meta.get("phase_gate"), dict):
        meta["phase_gate"].update(
            {
                "observation_structure_dictionary_connected": True,
                "observation_structure_gate_ready": True,
                "observation_structure_gate_passed": bool(observation_structure_gate_report.get("passed", True)),
                "observation_structure_composer_connected": True,
                "observation_structure_material_ready": bool(observation_structure_meta.get("structure_dictionary_material_ready")),
                "observation_structure_dictionary_generated_comment_text": False,
            }
        )
    if isinstance(meta.get("diagnostic_summary"), dict):
        meta["diagnostic_summary"]["emlis_observation_structure_dictionary"] = observation_structure_meta
        meta["diagnostic_summary"]["observation_structure_gate"] = observation_structure_gate_report
        meta["diagnostic_summary"] = attach_diagnostic_failure_taxonomy_meta(meta["diagnostic_summary"])
    user_label_connection_observation_reply_meta = {
        "observation_reply_kind": str(
            meta.get("observation_reply_kind")
            or phase20_3_material_route_meta.get("response_kind")
            or ""
        ),
        "eligibility_status": str(phase20_3_material_route_meta.get("material_quality") or ""),
        "material_quality": str(phase20_3_material_route_meta.get("material_quality") or ""),
        "safety_triage_kind": str(safety_triage_meta.get("safety_triage_kind") or ""),
        "observation_status": str(getattr(display_decision, "observation_status", "") or ""),
        "eligible_for_full_observation": phase20_3_material_route_meta.get("eligible_for_full_observation"),
        "question_required": phase20_3_material_route_meta.get("question_required"),
    }
    meta = attach_user_label_connection_meta_only_integration(
        meta,
        current_input=current_input,
        source_bundle=bundle,
        capability=capability,
        subscription_tier=subscription_tier,
        observation_reply_meta=user_label_connection_observation_reply_meta,
        material_quality=phase20_3_material_route_meta.get("material_quality"),
        safety_triage_kind=safety_triage_meta.get("safety_triage_kind"),
    )

    if user_label_connection_p5_runtime_bridge_summary:
        meta["user_label_connection_p5_runtime_bridge"] = dict(user_label_connection_p5_runtime_bridge_summary)
        meta["p5_runtime_bridge"] = dict(user_label_connection_p5_runtime_bridge_summary)
        if isinstance(meta.get("diagnostic_summary"), dict):
            meta["diagnostic_summary"]["user_label_connection_p5_runtime_bridge"] = dict(user_label_connection_p5_runtime_bridge_summary)
        if isinstance(meta.get("phase_gate"), dict):
            meta["phase_gate"].update(
                {
                    "p5_runtime_bridge_r2_evaluated": bool(
                        user_label_connection_p5_runtime_bridge_summary.get("runtime_evaluated") is True
                    ),
                    "p5_runtime_bridge_r2_visible_applied": bool(
                        user_label_connection_p5_runtime_bridge_summary.get("visible_applied") is True
                    ),
                    "p5_runtime_bridge_r2_product_quality_confirmed": bool(
                        user_label_connection_p5_runtime_bridge_summary.get("product_quality_confirmed") is True
                    ),
                    "p5_runtime_bridge_r2_release_allowed": False,
                    "p5_runtime_bridge_r2_public_response_key_added": False,
                    "p5_runtime_bridge_r2_comment_text_body_included": False,
                    "p5_runtime_bridge_r2_candidate_body_included": False,
                    "p5_runtime_bridge_r2_surface_body_included": False,
                    "p5_runtime_bridge_r4_human_qa_required": True,
                    "p5_runtime_bridge_r4_human_qa_completed": bool(
                        user_label_connection_p5_runtime_bridge_summary.get("human_qa_completed") is True
                    ),
                    "p5_runtime_bridge_r4_human_qa_pending": bool(
                        user_label_connection_p5_runtime_bridge_summary.get("human_qa_pending") is True
                    ),
                    "p5_runtime_bridge_r4_product_quality_confirmation_status": str(
                        user_label_connection_p5_runtime_bridge_summary.get("product_quality_confirmation_status")
                        or "human_qa_pending"
                    ),
                    "p5_runtime_bridge_r4_release_allowed": False,
                    "p5_runtime_bridge_r4_public_response_key_added": False,
                    "p5_runtime_bridge_r4_comment_text_body_included": False,
                    "p5_runtime_bridge_r4_candidate_body_included": False,
                    "p5_runtime_bridge_r4_surface_body_included": False,
                    "p5_runtime_bridge_r4_reviewer_free_text_included": False,
                    "p5_visible_connection_r3_route": str(
                        user_label_connection_p5_runtime_bridge_summary.get("visible_connection_route")
                        or "p5_6_boundary_internal_phase8_connector"
                    ),
                    "p5_visible_connection_r3_phase8_connector_scope": str(
                        user_label_connection_p5_runtime_bridge_summary.get("phase8_connector_scope")
                        or "p5_6_internal_boundary_only"
                    ),
                    "p5_visible_connection_r3_old_phase8_direct_call_used": False,
                    "p5_visible_connection_r3_phase8_internal_only": True,
                    "p5_visible_connection_r3_post_connection_regate_required": True,
                    "p5_visible_connection_r3_public_response_key_added": False,
                    "p5_visible_connection_r3_comment_text_body_included": False,
                }
            )


    if structure_insight_p6_runtime_bridge_summary:
        meta["structure_insight_p6_runtime_bridge"] = dict(structure_insight_p6_runtime_bridge_summary)
        meta["p6_runtime_bridge"] = dict(structure_insight_p6_runtime_bridge_summary)
        if isinstance(meta.get("diagnostic_summary"), dict):
            meta["diagnostic_summary"]["structure_insight_p6_runtime_bridge"] = dict(
                structure_insight_p6_runtime_bridge_summary
            )
        if isinstance(meta.get("phase_gate"), dict):
            meta["phase_gate"].update(
                {
                    "p6_runtime_bridge_r6_evaluated": bool(
                        structure_insight_p6_runtime_bridge_summary.get("runtime_evaluated") is True
                    ),
                    "p6_runtime_bridge_r6_visible_applied": bool(
                        structure_insight_p6_runtime_bridge_summary.get("visible_applied") is True
                    ),
                    "p6_runtime_bridge_r6_visible_family": str(
                        structure_insight_p6_runtime_bridge_summary.get("visible_family") or "none"
                    ),
                    "p6_runtime_bridge_r6_p5_dependency_status": str(
                        structure_insight_p6_runtime_bridge_summary.get("p5_dependency_status") or "p5_hold"
                    ),
                    "p6_runtime_bridge_r6_no_connect_family_preserved": bool(
                        structure_insight_p6_runtime_bridge_summary.get("no_connect_family_preserved") is True
                    ),
                    "p6_runtime_bridge_r6_release_allowed": False,
                    "p6_runtime_bridge_r6_public_response_key_added": False,
                    "p6_runtime_bridge_r6_comment_text_body_included": False,
                    "p6_runtime_bridge_r6_candidate_body_included": False,
                    "p6_runtime_bridge_r6_surface_body_included": False,
                    "p6_runtime_bridge_r6_gate_threshold_relaxed": False,
                }
            )

    if p5_p6_split_test_matrix_handoff_summary:
        meta["p5_p6_split_test_matrix_handoff"] = dict(p5_p6_split_test_matrix_handoff_summary)
        meta["p5_p6_handoff_lock"] = dict(p5_p6_split_test_matrix_handoff_summary)
        if isinstance(meta.get("diagnostic_summary"), dict):
            meta["diagnostic_summary"]["p5_p6_split_test_matrix_handoff"] = dict(
                p5_p6_split_test_matrix_handoff_summary
            )
        if isinstance(meta.get("phase_gate"), dict):
            meta["phase_gate"].update(
                {
                    "r9_p5_p6_split_matrix_fixed": True,
                    "r9_repair_step": "R9_P5P6SplitTestMatrixHandoff_20260612",
                    "r9_full_backend_suite_green_claim_allowed": False,
                    "r9_combined_pytest_timeout_is_not_green": True,
                    "r9_p5_runtime_evaluated": bool(
                        p5_p6_split_test_matrix_handoff_summary.get("p5_handoff", {}).get("runtime_evaluated") is True
                    ),
                    "r9_p6_runtime_evaluated": bool(
                        p5_p6_split_test_matrix_handoff_summary.get("p6_handoff", {}).get("runtime_evaluated") is True
                    ),
                    "r9_p6_visible_family": str(
                        p5_p6_split_test_matrix_handoff_summary.get("p6_handoff", {}).get("visible_family") or "none"
                    ),
                    "r9_no_connect_family_regression_green": bool(
                        p5_p6_split_test_matrix_handoff_summary.get("p6_handoff", {}).get(
                            "no_connect_family_regression_green"
                        )
                        is True
                    ),
                    "r9_p7_ready": False,
                    "r9_release_allowed": False,
                    "r9_public_response_key_added": False,
                    "r9_comment_text_body_included": False,
                    "r9_candidate_body_included": False,
                    "r9_surface_body_included": False,
                }
            )

    if user_label_connection_phase8_visible_meta:
        meta[USER_LABEL_CONNECTION_VISIBLE_SURFACE_META_KEY] = dict(user_label_connection_phase8_visible_meta)
        if user_label_connection_phase8_binding_meta:
            meta["user_label_connection_visible_surface_binding"] = dict(user_label_connection_phase8_binding_meta)
        phase8_public_summary = user_label_connection_visible_surface_public_summary(user_label_connection_phase8_visible_meta)
        meta_only_payload = meta.get(USER_LABEL_CONNECTION_META_ONLY_META_KEY)
        if isinstance(meta_only_payload, dict):
            meta_only_payload[USER_LABEL_CONNECTION_VISIBLE_SURFACE_META_KEY] = dict(user_label_connection_phase8_visible_meta)
            meta_only_payload["phase8_limited_visible_surface_connection"] = dict(user_label_connection_phase8_visible_meta)
        if isinstance(meta.get("diagnostic_summary"), dict):
            meta["diagnostic_summary"][USER_LABEL_CONNECTION_VISIBLE_SURFACE_META_KEY] = dict(phase8_public_summary)
            if isinstance(meta_only_payload, Mapping):
                meta["diagnostic_summary"][USER_LABEL_CONNECTION_PUBLIC_META_KEY] = user_label_connection_public_summary(meta_only_payload)
        if isinstance(meta.get("phase_gate"), dict):
            meta["phase_gate"].update(
                {
                    "phase8_user_label_connection_limited_visible_surface_evaluated": True,
                    "phase8_user_label_connection_limited_visible_surface_connected": bool(
                        phase8_public_summary.get("limited_visible_surface_connection_applied") is True
                    ),
                    "phase8_user_label_connection_history_connection_applied": bool(
                        phase8_public_summary.get("history_connection_applied") is True
                    ),
                    "phase8_user_label_connection_comment_text_connected": bool(
                        phase8_public_summary.get("comment_text_connected") is True
                    ),
                    "phase8_user_label_connection_visible_surface_connected": bool(
                        phase8_public_summary.get("visible_surface_connected") is True
                    ),
                    "phase8_user_label_connection_runtime_surface_connected": bool(
                        phase8_public_summary.get("runtime_surface_connected") is True
                    ),
                    "phase8_user_label_connection_public_response_key_added": False,
                    "phase8_user_label_connection_raw_text_included": False,
                    "phase8_user_label_connection_comment_text_body_included": False,
                    "phase8_user_label_connection_scope_marker_present": bool(
                        phase8_public_summary.get("scope_marker_present") is True
                    ),
                    "phase8_user_label_connection_soft_marker_present": bool(
                        phase8_public_summary.get("soft_marker_present") is True
                    ),
                }
            )

    multi_perspective_meta = meta.get("multi_perspective")
    if isinstance(multi_perspective_meta, dict) and isinstance(meta.get("diagnostic_summary"), dict):
        # Keep the nested diagnostic summary in lockstep with the top-level
        # internal diagnostic summary after additive Step10 / observation
        # structure meta attachments.  Public sanitization still happens at
        # the input_feedback boundary; this is internal meta consistency only.
        multi_perspective_meta["diagnostic_summary"] = dict(meta["diagnostic_summary"])

    return ReplyEnvelope(
        comment_text=final_text,
        meta=meta,
        used_evidence=[],
        evidence_by_line={},
        used_memory_layers=meta.get("used_memory_layers") if isinstance(meta.get("used_memory_layers"), list) else ["canonical_history"],
        fallback_used=False,
    )
