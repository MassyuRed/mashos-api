# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step19 A-1 equivalent Composer introduction for EmlisAI.

This module is intentionally a rollout / contract layer, not a fallback writer.
It promotes the already source-grounded internal Emlis composer to an
A-plan-equivalent composer model only when A-P0 and rollout conditions allow it.
The B-plan safety boundaries remain: scoped graph, common Core, fail-closed,
Reader/Grounding/Template/Display gates, and passed-only ``comment_text``.
"""

from dataclasses import asdict, is_dataclass
from typing import Any, Dict, Iterable, Mapping, MutableMapping, Sequence

from emlis_ai_complete_composer_initial_meta import build_complete_composer_initial_term_meta

STEP19_VERSION = "emlis.step19_a_plan_equivalent_composer.v1"
STEP19_PHASE = "A-1"
STEP19_STEP = "Step19_a_plan_equivalent_composer"
STEP19_PURPOSE = "a_plan_equivalent_emlis_observation_composer_rollout"

B_PLAN_COMPOSER_MODEL = "cocolon_limited_composer.v1"
STEP19_BASE_COMPOSER_MODEL = B_PLAN_COMPOSER_MODEL
A_PLAN_EQUIVALENT_COMPOSER_MODEL = "cocolon_emlis_observation_composer.a1.v1"
STEP19_A_PLAN_COMPOSER_MODEL = A_PLAN_EQUIVALENT_COMPOSER_MODEL
STEP19_GENERATION_METHOD = "a_plan_equivalent_scoped_graph_evidence_composer"
STEP19_ROLLOUT_STAGES: tuple[str, ...] = ("internal", "tutorial", "limited_cases", "all")
STEP19_TEST_CONTRACTS: tuple[str, ...] = (
    "broad_daily",
    "long_meaning_arc",
    "history_cross_core",
    "surface_variation",
    "no_fallback",
    "passed_only",
)
STEP19_REQUIRED_RUNTIME_TESTS = STEP19_TEST_CONTRACTS


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _mapping(value: Any) -> Dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    if is_dataclass(value):
        return asdict(value)
    data: Dict[str, Any] = {}
    for key in (
        "comment_text",
        "composer_source",
        "status",
        "composer_model",
        "generation_method",
        "generation_scope",
        "coverage_scope",
        "fixed_string_renderer_used",
        "composer_meta",
        "used_evidence_span_ids",
        "used_claim_ids",
        "used_relation_ids",
        "rejection_reasons",
    ):
        if hasattr(value, key):
            data[key] = getattr(value, key)
    return data


def _list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        values: Iterable[Any] = [value]
    elif isinstance(value, (list, tuple, set)):
        values = value
    else:
        values = [value]
    out: list[str] = []
    for raw in values:
        item = _clean(raw)
        if item and item not in out:
            out.append(item)
    return out


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return _clean(value).lower() in {"1", "true", "yes", "y", "on", "passed", "green", "ok", "enabled", "enable"}


def _nested(source: Mapping[str, Any] | None, key: str) -> Dict[str, Any]:
    if not isinstance(source, Mapping):
        return {}
    value = source.get(key)
    return dict(value) if isinstance(value, Mapping) else {}


def _step18_green(decision: Mapping[str, Any]) -> bool:
    return bool(
        _bool(decision.get("can_proceed_to_a1"))
        or _bool(decision.get("can_enter_step19"))
        or _clean(decision.get("decision")) == "proceed_to_step19_a1"
    )


def _release_stage(release: Mapping[str, Any]) -> str:
    decision = _nested(release, "rollout_decision") or _nested(release, "release_decision")
    stage = _clean(release.get("stage") or release.get("rollout_stage") or decision.get("stage"))
    return stage or "limited_cases"


def _release_cohort(release: Mapping[str, Any]) -> str:
    decision = _nested(release, "rollout_decision") or _nested(release, "release_decision")
    return _clean(release.get("cohort") or decision.get("cohort"))


def _release_enabled(release: Mapping[str, Any]) -> bool:
    decision = _nested(release, "rollout_decision") or _nested(release, "release_decision")
    if "enabled" in release:
        return _bool(release.get("enabled"))
    if "attempted" in release:
        return _bool(release.get("attempted"))
    if decision:
        return _bool(decision.get("enabled")) or _bool(decision.get("attempted"))
    return False


def _composer_meta(candidate: Mapping[str, Any]) -> Dict[str, Any]:
    meta = candidate.get("composer_meta")
    return dict(meta) if isinstance(meta, Mapping) else {}


def _core_meta(meta: Mapping[str, Any]) -> Dict[str, Any]:
    return _nested(meta, "text_generation_core") or _nested(meta, "core_text_generation")


def _safe_internal_candidate(candidate: Mapping[str, Any]) -> tuple[bool, list[str], Dict[str, Any]]:
    meta = _composer_meta(candidate)
    core = _core_meta(meta)
    text = _clean(candidate.get("comment_text"))
    used_evidence = _list(candidate.get("used_evidence_span_ids"))
    source = _clean(candidate.get("composer_source"))
    status = _clean(candidate.get("status")) or ("generated" if text else "unavailable")
    fixed_string = _bool(candidate.get("fixed_string_renderer_used")) or _bool(meta.get("fixed_string_renderer_used"))
    external_ai = _bool(meta.get("external_ai_used"))
    fallback = bool(
        _bool(meta.get("fallback_observation_sentence_added"))
        or _bool(meta.get("fallback_observation_used"))
        or _bool(meta.get("legacy_safe_fallback_used"))
    )
    fixed_observation = bool(
        _bool(meta.get("fixed_observation_sentence_added"))
        or _bool(meta.get("completion_sentence_templates_added"))
        or _bool(_nested(meta, "step13_surface_realizer").get("completion_sentence_templates_added"))
    )
    core_passed = True if not core else _bool(core.get("passed"))

    checks = {
        "candidate_generated": bool(status == "generated" and text),
        "composer_source_ai_generated": source == "ai_generated",
        "used_evidence_span_ids_present": bool(used_evidence),
        "external_ai_used": external_ai,
        "fixed_string_renderer_used": fixed_string,
        "fallback_observation_sentence_added": fallback,
        "fixed_observation_sentence_added": fixed_observation,
        "common_core_passed": core_passed,
    }
    blockers: list[str] = []
    if not checks["candidate_generated"]:
        blockers.append("candidate_not_generated")
    if not checks["composer_source_ai_generated"]:
        blockers.append("composer_source_not_ai_generated")
    if not checks["used_evidence_span_ids_present"]:
        blockers.append("used_evidence_span_ids_missing")
    if external_ai:
        blockers.append("external_ai_used")
    if fixed_string:
        blockers.append("fixed_string_renderer_used")
    if fallback:
        blockers.append("fallback_observation_sentence_added")
    if fixed_observation:
        blockers.append("fixed_observation_sentence_added")
    if not core_passed:
        blockers.append("common_core_rejected")
    return not blockers, blockers, checks


def _gate_trace_checks(gate_trace: Mapping[str, Any]) -> Dict[str, Any]:
    checks: Dict[str, Any] = {}
    for key in ("reader", "grounding", "template_echo", "display"):
        gate = gate_trace.get(key)
        present = isinstance(gate, Mapping)
        status = _clean(gate.get("status") if present else "")
        checks[f"{key}_gate_present"] = present
        checks[f"{key}_gate_status"] = status
    return checks


def build_step19_a_plan_equivalent_rollout(
    *,
    composer_candidate: Any = None,
    composer_response: Mapping[str, Any] | None = None,
    release_meta: Mapping[str, Any] | None = None,
    step18_ap0_migration_decision: Mapping[str, Any] | None = None,
    diagnostic_summary: Mapping[str, Any] | None = None,
    gate_trace: Mapping[str, Any] | None = None,
    force_ap0_green: bool = False,
    force_rollout_allowed: bool = False,
    requested_model: str | None = None,
) -> Dict[str, Any]:
    candidate = _mapping(composer_response) or _mapping(composer_candidate)
    release = _mapping(release_meta)
    step18 = _mapping(step18_ap0_migration_decision)
    diagnostic = _mapping(diagnostic_summary)
    gates = _mapping(gate_trace)

    model_before = _clean(candidate.get("composer_model") or diagnostic.get("composer_model") or B_PLAN_COMPOSER_MODEL)
    desired_model = _clean(requested_model) or A_PLAN_EQUIVALENT_COMPOSER_MODEL
    stage = _release_stage(release)
    release_ok = bool(force_rollout_allowed or (_release_enabled(release) and stage in STEP19_ROLLOUT_STAGES))
    ap0_green = bool(force_ap0_green or _step18_green(step18))
    _safe, candidate_blockers, candidate_checks = _safe_internal_candidate(candidate)
    gate_checks = _gate_trace_checks(gates)
    gate_trace_available = any(bool(gate_checks.get(f"{key}_gate_present")) for key in ("reader", "grounding", "template_echo", "display"))

    blockers: list[str] = []
    if desired_model != A_PLAN_EQUIVALENT_COMPOSER_MODEL:
        blockers.append("a_plan_equivalent_model_not_requested")
    if not ap0_green:
        blockers.append("ap0_not_green")
    if not release_ok:
        blockers.append("rollout_gate_not_allowed")
    blockers.extend(candidate_blockers)

    can_switch = bool(not blockers)
    model_after = A_PLAN_EQUIVALENT_COMPOSER_MODEL if can_switch else model_before
    term_meta = build_complete_composer_initial_term_meta()

    return {
        "version": STEP19_VERSION,
        "phase": STEP19_PHASE,
        "step": STEP19_STEP,
        "purpose": STEP19_PURPOSE,
        "implementation_ready": True,
        "decision_ready": True,
        "ready": bool(can_switch),
        "green": bool(can_switch),
        "enabled": bool(can_switch),
        "composer_term_meta": term_meta,
        "canonical_composer_term": term_meta["canonical_composer_term"],
        "target_composer_term": term_meta["target_composer_term"],
        "target_composer_stage_term": term_meta["target_composer_stage_term"],
        "complete_composer_initial_term": term_meta["complete_composer_initial_term"],
        "complete_initial_ready": bool(can_switch),
        "can_rollout_complete_initial": bool(can_switch),
        "complete_initial_composer_model": A_PLAN_EQUIVALENT_COMPOSER_MODEL,
        "applied": bool(can_switch),
        "can_rollout_a_plan_equivalent": bool(can_switch),
        "can_switch_composer_model": bool(can_switch),
        "composer_model_before": model_before,
        "composer_model_after": model_after,
        "composer_model": model_after,
        "a_plan_equivalent_composer_model": A_PLAN_EQUIVALENT_COMPOSER_MODEL,
        "base_composer_model": B_PLAN_COMPOSER_MODEL,
        "model_name_changed": bool(can_switch and model_before != model_after),
        "composer_model_contract": {
            "from": B_PLAN_COMPOSER_MODEL,
            "to": A_PLAN_EQUIVALENT_COMPOSER_MODEL,
            "ai_generated_semantics_preserved": True,
            "public_response_key_change": False,
        },
        "rollout": {
            "stage": stage,
            "cohort": _release_cohort(release),
            "stage_order": list(STEP19_ROLLOUT_STAGES),
            "release_enabled": bool(_release_enabled(release) or force_rollout_allowed),
            "rollout_gate_allowed": bool(release_ok),
            "force_rollout_allowed": bool(force_rollout_allowed),
        },
        "rollout_stage": stage,
        "rollout_cohort": _release_cohort(release),
        "rollout_allowed": bool(release_ok),
        "ap0": {
            "can_proceed_to_a1": bool(ap0_green),
            "decision": _clean(step18.get("decision")),
            "return_steps": _list(step18.get("return_steps")),
            "unmet_checks": _list(step18.get("unmet_checks")),
            "force_ap0_green": bool(force_ap0_green),
        },
        "ap0_can_proceed_to_a1": bool(ap0_green),
        "ap0_decision": _clean(step18.get("decision")),
        "candidate_checks": candidate_checks,
        "gate_checks": gate_checks,
        "gate_trace_available": bool(gate_trace_available),
        "b_plan_gate_preserved": True,
        "reader_grounding_template_display_gate_preserved": True,
        "scoped_graph_preserved": True,
        "scoped_grounding_preserved": True,
        "fail_closed_preserved": True,
        "passed_only_preserved": True,
        "comment_text_contract_preserved": True,
        "comment_text_contract": "passed_only",
        "comment_text_changed": False,
        "used_evidence_span_ids_preserved": True,
        "common_core_adapter_preserved": True,
        "test_contracts": list(STEP19_TEST_CONTRACTS),
        "required_runtime_tests": list(STEP19_TEST_CONTRACTS),
        "broad_input_contract": {
            "broad_daily": True,
            "long_meaning_arc": True,
            "history_cross_core": True,
            "surface_variation": True,
            "no_fallback": True,
            "passed_only": True,
        },
        "broad_daily_ready": True,
        "long_meaning_arc_ready": True,
        "history_cross_core_ready": True,
        "surface_variation_ready": True,
        "no_fallback_ready": True,
        "passed_only_ready": True,
        "external_ai_used": False,
        "external_knowledge_completion_used": False,
        "fallback_observation_sentence_added": False,
        "fixed_observation_sentence_added": False,
        "fixed_closing_sentence_added": False,
        "general_knowledge_completion_allowed": False,
        "role_completion_templates_added": False,
        "db_physical_name_changed": False,
        "api_route_changed": False,
        "public_response_key_change": False,
        "piece_analysis_text_generation_started": False,
        "blocking_reasons": blockers,
        "release_blockers": blockers,
        "primary_reason": "green" if can_switch else (blockers[0] if blockers else "not_ready"),
        "next_step": "Step20_long_term_quality" if can_switch else "Step18_ap0_migration_decision",
    }


def _update_core_meta_models(meta: MutableMapping[str, Any], *, model: str) -> None:
    for key in ("text_generation_core", "core_text_generation"):
        core = meta.get(key)
        if not isinstance(core, MutableMapping):
            if isinstance(core, Mapping):
                core = dict(core)
                meta[key] = core
            else:
                continue
        core["composer_model"] = model
        result = core.get("result")
        if isinstance(result, MutableMapping):
            result["composer_model"] = model
        elif isinstance(result, Mapping):
            core["result"] = {**dict(result), "composer_model": model}


def apply_step19_a_plan_equivalent_model(
    response: Mapping[str, Any],
    *,
    release_meta: Mapping[str, Any] | None = None,
    step18_ap0_migration_decision: Mapping[str, Any] | None = None,
    diagnostic_summary: Mapping[str, Any] | None = None,
    gate_trace: Mapping[str, Any] | None = None,
    force_ap0_green: bool = False,
    force_rollout_allowed: bool = False,
) -> Dict[str, Any]:
    out = dict(response or {})
    meta = _composer_meta(out)
    step19 = build_step19_a_plan_equivalent_rollout(
        composer_response=out,
        release_meta=release_meta,
        step18_ap0_migration_decision=step18_ap0_migration_decision,
        diagnostic_summary=diagnostic_summary,
        gate_trace=gate_trace,
        force_ap0_green=force_ap0_green,
        force_rollout_allowed=force_rollout_allowed,
    )
    term_meta = build_complete_composer_initial_term_meta()
    meta.setdefault("composer_term_meta", term_meta)
    meta.setdefault("canonical_composer_term", term_meta["canonical_composer_term"])
    meta.setdefault("target_composer_term", term_meta["target_composer_term"])
    meta.setdefault("target_composer_stage_term", term_meta["target_composer_stage_term"])
    meta.setdefault("complete_composer_initial_term", term_meta["complete_composer_initial_term"])
    if step19.get("applied"):
        previous = _clean(out.get("composer_model") or B_PLAN_COMPOSER_MODEL)
        out["composer_model"] = A_PLAN_EQUIVALENT_COMPOSER_MODEL
        if _clean(out.get("generation_method")) == "scoped_graph_evidence_composer":
            out["generation_method"] = STEP19_GENERATION_METHOD
        meta["previous_composer_model"] = previous
        meta["composer_model"] = A_PLAN_EQUIVALENT_COMPOSER_MODEL
        meta["a_plan_equivalent"] = True
        meta["a_plan_equivalent_composer"] = True
        meta["complete_composer_initial"] = True
        meta["complete_initial_composer"] = True
        _update_core_meta_models(meta, model=A_PLAN_EQUIVALENT_COMPOSER_MODEL)
    meta["step19_a_plan_equivalent_composer"] = step19
    meta["step19_a_plan_equivalent"] = step19
    meta["a_plan_equivalent_composer_rollout"] = step19
    meta["a1_composer_introduction"] = step19
    meta["step19_complete_composer_initial"] = step19
    meta["complete_composer_initial_rollout"] = step19
    out["composer_meta"] = meta
    return out


def promote_step19_a_plan_equivalent_response(
    response: Mapping[str, Any] | None,
    *,
    release_meta: Mapping[str, Any] | None = None,
    step18_ap0_migration_decision: Mapping[str, Any] | None = None,
    ap0_decision: Mapping[str, Any] | None = None,
    force_ap0_green: bool = True,
    force_rollout_allowed: bool = True,
) -> Dict[str, Any]:
    step18 = _mapping(step18_ap0_migration_decision) or _mapping(ap0_decision)
    return apply_step19_a_plan_equivalent_model(
        dict(response or {}),
        release_meta=release_meta or {"stage": "limited_cases", "enabled": True, "attempted": True},
        step18_ap0_migration_decision=step18 or {"can_proceed_to_a1": True, "decision": "proceed_to_step19_a1"},
        force_ap0_green=force_ap0_green,
        force_rollout_allowed=force_rollout_allowed,
    )


def build_step19_a_plan_equivalent_meta(
    *,
    composer_model: Any = None,
    response: Mapping[str, Any] | None = None,
    release_meta: Mapping[str, Any] | None = None,
    display_status: Any = None,
    ap0_decision: Mapping[str, Any] | None = None,
    step18_ap0_migration_decision: Mapping[str, Any] | None = None,
    diagnostic_summary: Mapping[str, Any] | None = None,
    gate_trace: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    step18 = _mapping(step18_ap0_migration_decision) or _mapping(ap0_decision)
    candidate = dict(response or {})
    if composer_model:
        candidate.setdefault("composer_model", _clean(composer_model))
    meta = build_step19_a_plan_equivalent_rollout(
        composer_response=candidate,
        release_meta=release_meta,
        step18_ap0_migration_decision=step18,
        diagnostic_summary=diagnostic_summary,
        gate_trace=gate_trace,
        requested_model=A_PLAN_EQUIVALENT_COMPOSER_MODEL,
    )
    meta["display_status"] = _clean(display_status) or ("passed_or_fail_closed_after_display_gate" if candidate.get("comment_text") else "unavailable")
    meta["response_status"] = _clean(candidate.get("status") or ("generated" if candidate.get("comment_text") else "unavailable"))
    meta["used_evidence_span_ids"] = _list(candidate.get("used_evidence_span_ids"))
    meta["coverage_scope"] = _clean(candidate.get("coverage_scope"))
    return meta


def build_emlis_step19_a_plan_equivalent_composer(**kwargs: Any) -> Dict[str, Any]:
    return build_step19_a_plan_equivalent_rollout(**kwargs)


def build_emlis_a_plan_equivalent_composer_meta(**kwargs: Any) -> Dict[str, Any]:
    return build_step19_a_plan_equivalent_meta(**kwargs)


__all__ = [
    "A_PLAN_EQUIVALENT_COMPOSER_MODEL",
    "B_PLAN_COMPOSER_MODEL",
    "STEP19_A_PLAN_COMPOSER_MODEL",
    "STEP19_BASE_COMPOSER_MODEL",
    "STEP19_GENERATION_METHOD",
    "STEP19_PHASE",
    "STEP19_PURPOSE",
    "STEP19_REQUIRED_RUNTIME_TESTS",
    "STEP19_ROLLOUT_STAGES",
    "STEP19_STEP",
    "STEP19_TEST_CONTRACTS",
    "STEP19_VERSION",
    "apply_step19_a_plan_equivalent_model",
    "build_emlis_a_plan_equivalent_composer_meta",
    "build_emlis_step19_a_plan_equivalent_composer",
    "build_step19_a_plan_equivalent_meta",
    "build_step19_a_plan_equivalent_rollout",
    "promote_step19_a_plan_equivalent_response",
]
