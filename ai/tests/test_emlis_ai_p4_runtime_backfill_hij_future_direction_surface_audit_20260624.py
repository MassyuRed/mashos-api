# -*- coding: utf-8 -*-
from __future__ import annotations

"""P4 runtime backfill R0/R1 audit for the H future-direction surface red.

This file is intentionally test-only.  R0/R1 must freeze the currently open
H/I/J H-case red and separate material presence from the public surface lane
that drops the current-input future-direction nucleus.  It must not repair the
surface yet, change runtime contracts, or add body-bearing audit payloads.
"""

from collections.abc import Mapping, Sequence
from typing import Any, Final
import json

import pytest

import emotion_submit_service as submit_service
from emlis_ai_gate_recovery_public_constants import (
    CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_COMPOSER,
    CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE,
)
from emlis_ai_observation_eligibility_router import route_emlis_observation_material_eligibility
from emlis_ai_public_surface_requirement import resolve_public_surface_requirement
import test_emlis_ai_hij_reception_required_regression_p8 as p8_regression

P4_RUNTIME_BACKFILL_HIJ_SURFACE_AUDIT_SCHEMA_VERSION: Final = (
    "cocolon.emlis.p4_runtime_backfill.hij_future_direction_surface_audit.20260624.v1"
)
P4_RUNTIME_BACKFILL_HIJ_RED_ID: Final = "P4-HIJ-FUTURE-DIRECTION-SURFACE-001"
_TARGET_CASE_ID: Final = "p8_H_recovered_energy_future_direction"

_EXPECTED_SURFACE_ROLES: Final[tuple[tuple[str, str], ...]] = (
    ("やってみたい", "future_intention_visible"),
    ("次の頑張り方", "future_direction_visible"),
    ("出来るかもしれない", "self_possibility_visible"),
)
_GENERIC_SURFACE_SIGNATURES: Final[tuple[tuple[str, str], ...]] = (
    ("生活について、平穏の動き", "category_emotion_action_generic"),
    ("次にどう扱うかを探している動き", "next_handling_generic"),
    ("良かった動きも迷いもどちらかに寄せず", "positive_generic_reception"),
)
_REQUIRED_SEMANTIC_MATERIAL_IDS: Final[frozenset[str]] = frozenset(
    {"recovered_energy", "future_intention", "value_preservation", "self_observation"}
)
_REQUIRED_VISIBLE_MATERIAL_SLOT_IDS: Final[frozenset[str]] = frozenset(
    {"event", "emotion_direction", "target", "action", "time", "value"}
)
_PUBLIC_CONTRACT_FALSE_KEYS: Final[tuple[str, ...]] = (
    "public_response_key_added",
    "response_shape_changed",
    "api_route_changed",
    "db_physical_name_changed",
    "rn_visible_contract_changed",
    "display_gate_relaxed",
    "fixed_fallback_used",
    "case_specific_route_used",
    "case_id_runtime_condition_used",
)
_BODY_FREE_FALSE_KEYS: Final[tuple[str, ...]] = (
    "raw_input_included",
    "raw_text_included",
    "comment_text_body_included",
    "candidate_body_included",
    "expected_surface_text_included",
    "generic_surface_text_included",
)


def _target_case() -> p8_regression.P8HijCase:
    for case in p8_regression.P8_HIJ_CASES:
        if case.case_id == _TARGET_CASE_ID:
            return case
    raise AssertionError(f"target case not found: {_TARGET_CASE_ID}")


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _as_sequence(value: Any) -> tuple[Any, ...]:
    if value is None:
        return ()
    if isinstance(value, (str, bytes, bytearray)):
        return (value,)
    if isinstance(value, Sequence):
        return tuple(value)
    return (value,)


def _string_ids(value: Any) -> tuple[str, ...]:
    out: list[str] = []
    for item in _as_sequence(value):
        text = str(item or "").strip()
        if text and text not in out:
            out.append(text)
    return tuple(out)


def _material_route_meta(material_route: Any) -> Mapping[str, Any]:
    as_meta = getattr(material_route, "as_meta", None)
    if callable(as_meta):
        meta = as_meta()
        if isinstance(meta, Mapping):
            return meta
    return _as_mapping(material_route)


def _semantic_focus_id(semantic_material_ids: Sequence[str]) -> str:
    ids = set(semantic_material_ids)
    if {"recovered_energy", "future_intention"}.issubset(ids):
        return "recovered_energy_future_direction"
    if {"relationship_wish", "recovered_energy"}.issubset(ids):
        return "recovered_energy_relationship_wish"
    if {"comparison_baseline_shift", "small_change_preservation"}.issubset(ids):
        return "comparison_baseline_small_change"
    return "generic_visible_material"


def _missing_surface_role_ids(comment_text: str) -> tuple[str, ...]:
    return tuple(role_id for fragment, role_id in _EXPECTED_SURFACE_ROLES if fragment not in comment_text)


def _forbidden_generic_signature_ids(comment_text: str) -> tuple[str, ...]:
    return tuple(signature_id for fragment, signature_id in _GENERIC_SURFACE_SIGNATURES if fragment in comment_text)


def _public_contract_flags(*, public_meta: Mapping[str, Any], reply_meta: Mapping[str, Any]) -> dict[str, bool]:
    speed = _as_mapping(public_meta.get("submit_speed_regression"))
    boundary = _as_mapping(public_meta.get("public_feedback_meta_boundary"))
    gate_loop = _as_mapping(reply_meta.get("phase20_5_gate_recovery_loop"))
    candidate_boundary = _as_mapping(reply_meta.get("phase20_5_gate_recovery_public_boundary"))
    builder = _public_candidate_builder(reply_meta)
    builder_flags = _as_mapping(builder.get("contract_flags"))
    return {
        "public_response_key_added": bool(speed.get("public_response_key_added") or builder_flags.get("public_response_key_added")),
        "response_shape_changed": bool(speed.get("response_shape_changed") or builder_flags.get("response_shape_changed")),
        "api_route_changed": bool(builder_flags.get("api_route_changed")),
        "db_physical_name_changed": bool(builder_flags.get("db_physical_name_changed")),
        "rn_visible_contract_changed": bool(speed.get("rn_visible_contract_changed") or builder_flags.get("rn_visible_contract_changed")),
        "display_gate_relaxed": bool(
            speed.get("display_gate_relaxed")
            or gate_loop.get("display_gate_relaxed")
            or candidate_boundary.get("display_gate_relaxed")
            or builder_flags.get("display_gate_relaxed")
        ),
        "fixed_fallback_used": bool(gate_loop.get("fixed_fallback_used")),
        "case_specific_route_used": bool(gate_loop.get("case_specific_route_used") or builder_flags.get("case_specific_route_used")),
        "case_id_runtime_condition_used": bool(gate_loop.get("case_id_runtime_condition_used")),
        "raw_input_included": bool(boundary.get("raw_input_included") or speed.get("raw_input_included")),
        "comment_text_body_included": bool(
            boundary.get("comment_text_body_included")
            or boundary.get("comment_text_included")
            or speed.get("comment_text_body_included")
        ),
    }


def _body_boundary(public_meta: Mapping[str, Any]) -> dict[str, Any]:
    boundary = _as_mapping(public_meta.get("public_feedback_meta_boundary"))
    speed = _as_mapping(public_meta.get("submit_speed_regression"))
    return {
        "body_free": True,
        "raw_input_included": bool(boundary.get("raw_input_included") or speed.get("raw_input_included")),
        "raw_text_included": bool(speed.get("raw_text_included")),
        "comment_text_body_included": bool(
            boundary.get("comment_text_body_included")
            or boundary.get("comment_text_included")
            or speed.get("comment_text_body_included")
        ),
        "candidate_body_included": bool(boundary.get("candidate_body_included")),
        "expected_surface_text_included": False,
        "generic_surface_text_included": False,
    }


def _public_candidate_builder(reply_meta: Mapping[str, Any]) -> Mapping[str, Any]:
    public_boundary = _as_mapping(reply_meta.get("phase20_5_gate_recovery_public_boundary"))
    loop_result = _as_mapping(public_boundary.get("gate_recovery_loop_result"))
    binding = _as_mapping(
        loop_result.get("gate_recovery_surface_binding")
        or loop_result.get("phase20_15_gate_recovery_surface_binding")
    )
    return _as_mapping(binding.get("phase20_5_gate_recovery_public_candidate_builder"))


def _build_p4_r0_r1_audit(
    *,
    case: p8_regression.P8HijCase,
    result: Mapping[str, Any],
    captured: Mapping[str, Any],
) -> dict[str, Any]:
    current_input = p8_regression._current_input(case)
    material_route = route_emlis_observation_material_eligibility(current_input)
    material_meta = _material_route_meta(material_route)
    direct_requirement = resolve_public_surface_requirement(
        current_input=current_input,
        material_route=material_route,
        composer_meta=None,
        diagnostic_summary=None,
    )
    comment_text = str(result.get("input_feedback_comment") or "").strip()
    public_meta = _as_mapping(result.get("input_feedback_meta"))
    reply_meta = _as_mapping(captured.get("reply_meta"))
    public_lineage = _as_mapping(public_meta.get("public_surface_lineage"))
    builder = _public_candidate_builder(reply_meta)
    builder_lineage = _as_mapping(builder.get("candidate_lineage"))
    recovery_plan = _as_mapping(builder.get("recovery_plan"))
    runtime_requirement = _as_mapping(recovery_plan.get("surface_requirement"))
    runtime_material_summary = _as_mapping(recovery_plan.get("input_material_summary"))
    complete_initial_availability = _as_mapping(recovery_plan.get("complete_initial_surface_availability_summary"))
    public_contract_flags = _public_contract_flags(public_meta=public_meta, reply_meta=reply_meta)
    body_boundary = _body_boundary(public_meta)
    semantic_material_ids = _string_ids(
        material_meta.get("relation_material_ids") or material_meta.get("generic_relation_material_ids")
    )
    visible_material_slot_ids = _string_ids(material_meta.get("visible_material_slots"))
    missing_role_ids = _missing_surface_role_ids(comment_text)
    generic_signature_ids = _forbidden_generic_signature_ids(comment_text)
    specificity_met = not missing_role_ids and not generic_signature_ids
    direct_family = str(direct_requirement.get("surface_requirement_family") or "")
    runtime_family = str(runtime_requirement.get("surface_requirement_family") or public_lineage.get("surface_requirement_family") or "")

    return {
        "schema_version": P4_RUNTIME_BACKFILL_HIJ_SURFACE_AUDIT_SCHEMA_VERSION,
        "red_id": P4_RUNTIME_BACKFILL_HIJ_RED_ID,
        "case_id": case.case_id,
        "phase": "P4_runtime_backfill_red_repair",
        "target_scope": {
            "family": "change_future_intention",
            "repair_kind": "current_only_surface_specificity",
            "target_runtime_lane": "eligible_non_limited_labelled_two_stage_recomposition",
            "not_release_decision": True,
        },
        "r0_red_ledger": {
            "status": "CLOSED_BY_R2_R3" if specificity_met else "OPEN_RED",
            "red_classification": "current_only_surface_specificity_red",
            "repair_stage": "R2_R3_eligible_future_direction_surface_specificity" if specificity_met else "R0_R1_lineage_audit_only",
            "public_feedback_arrived": bool(comment_text),
            "observation_status": str(public_meta.get("observation_status") or ""),
            "specificity_required": True,
            "specificity_met": specificity_met,
            "generic_surface_detected": bool(generic_signature_ids),
            "expected_surface_role_ids": tuple(role_id for _, role_id in _EXPECTED_SURFACE_ROLES),
            "missing_surface_role_ids": missing_role_ids,
            "forbidden_generic_signature_ids": generic_signature_ids,
            "public_contract_changed": any(bool(public_contract_flags.get(key)) for key in _PUBLIC_CONTRACT_FALSE_KEYS),
            "body_boundary_passed": body_boundary["body_free"]
            and not any(bool(body_boundary.get(key)) for key in _BODY_FREE_FALSE_KEYS),
        },
        "r1_material_audit": {
            "material_quality": str(material_meta.get("material_quality") or ""),
            "visible_material_slot_ids": visible_material_slot_ids,
            "semantic_material_ids": semantic_material_ids,
            "semantic_focus_id": _semantic_focus_id(semantic_material_ids),
            "semantic_material_count": len(semantic_material_ids),
            "required_semantic_material_present": _REQUIRED_SEMANTIC_MATERIAL_IDS.issubset(set(semantic_material_ids)),
            "required_visible_slots_present": _REQUIRED_VISIBLE_MATERIAL_SLOT_IDS.issubset(set(visible_material_slot_ids)),
            "direct_surface_requirement_family": direct_family,
            "direct_two_stage_required": bool(direct_requirement.get("two_stage_required")),
            "direct_plain_state_answer_allowed": bool(direct_requirement.get("plain_state_answer_allowed")),
            "runtime_material_quality": str(runtime_material_summary.get("material_quality") or ""),
            "runtime_material_relation_ids": _string_ids(runtime_material_summary.get("relation_material_ids")),
        },
        "r1_candidate_lineage_audit": {
            "direct_requirement_to_runtime_requirement_shift_detected": bool(direct_family and runtime_family and direct_family != runtime_family),
            "runtime_surface_requirement_family": runtime_family,
            "runtime_two_stage_required": bool(runtime_requirement.get("two_stage_required") or public_lineage.get("two_stage_required")),
            "runtime_plain_state_answer_allowed": bool(runtime_requirement.get("plain_state_answer_allowed")),
            "selected_public_candidate_source_kind": str(
                builder_lineage.get("selected_public_candidate_source_kind")
                or public_lineage.get("selected_public_candidate_source_kind")
                or ""
            ),
            "final_public_candidate_source_kind": str(
                builder_lineage.get("final_public_candidate_source_kind")
                or public_lineage.get("final_public_candidate_source_kind")
                or ""
            ),
            "recovery_input_candidate_source_kind": str(
                builder_lineage.get("recovery_input_candidate_source_kind")
                or public_lineage.get("recovery_input_candidate_source_kind")
                or ""
            ),
            "root_candidate_source_kind": str(builder_lineage.get("root_candidate_source_kind") or public_lineage.get("root_candidate_source_kind") or ""),
            "complete_initial_candidate_generated_before_display_gate": bool(
                complete_initial_availability.get("candidate_generated_before_display_gate")
            ),
            "complete_initial_first_blocker_family": str(complete_initial_availability.get("first_blocker_family") or ""),
            "complete_initial_first_blocker_code": str(complete_initial_availability.get("first_blocker_code") or ""),
            "labelled_two_stage_surface_recomposition_used": bool(public_lineage.get("labelled_two_stage_surface_recomposition_used")),
            "limited_grounding_reception_surface_used": bool(
                _as_mapping(public_meta.get("labelled_two_stage_surface_recomposition_summary")).get(
                    "limited_grounding_reception_surface_used"
                )
            ),
            "normal_observation_rebuild_used": bool(public_lineage.get("normal_observation_rebuild_used")),
            "gate_recovery_loop_applied": bool(
                _as_mapping(reply_meta.get("phase20_5_gate_recovery_public_boundary")).get("gate_recovery_loop_applied")
            ),
        },
        "public_contract_flags": public_contract_flags,
        "body_boundary": body_boundary,
    }


async def _run_target_case(monkeypatch: pytest.MonkeyPatch) -> tuple[p8_regression.P8HijCase, dict[str, Any], dict[str, Any]]:
    case = _target_case()
    p8_regression._enable_complete_initial(monkeypatch)
    p8_regression._patch_submit_persistence(monkeypatch, inserted_id=f"p4-r0-r1-{case.case_id}")
    captured: dict[str, Any] = {}
    p8_regression._patch_real_reply_source_bundle(monkeypatch, captured)
    result = await submit_service.persist_emotion_submission(
        user_id=f"p4-r0-r1-user-{case.case_id}",
        emotions=list(case.emotions),
        memo=case.memo,
        memo_action="",
        category=list(case.categories),
    )
    return case, dict(result), captured


def _assert_body_free_audit(*, audit: Mapping[str, Any], case: p8_regression.P8HijCase, comment_text: str) -> None:
    dumped = json.dumps(audit, ensure_ascii=False, sort_keys=True)
    compact_dumped = " ".join(dumped.split())
    assert case.memo not in dumped
    assert " ".join(case.memo.split()) not in compact_dumped
    assert comment_text not in dumped
    assert " ".join(comment_text.split()) not in compact_dumped
    for fragment, _role_id in _EXPECTED_SURFACE_ROLES:
        assert fragment not in dumped
    for fragment, _signature_id in _GENERIC_SURFACE_SIGNATURES:
        assert fragment not in dumped
    assert '"comment_text":' not in dumped
    assert '"raw_input":' not in dumped
    assert '"candidate_body":' not in dumped
    assert '"surface_body":' not in dumped


@pytest.mark.asyncio
async def test_p4_r0_red_ledger_tracks_h_future_direction_surface_specificity_repair_body_free(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    case, result, captured = await _run_target_case(monkeypatch)
    body = p8_regression._public_response_body(result)
    p8_regression._assert_public_response_shape_unchanged(body)
    p8_regression._assert_public_meta_body_free(body=body, result=result, case=case)

    comment_text = str(result.get("input_feedback_comment") or "").strip()
    audit = _build_p4_r0_r1_audit(case=case, result=result, captured=captured)

    assert audit["schema_version"] == P4_RUNTIME_BACKFILL_HIJ_SURFACE_AUDIT_SCHEMA_VERSION
    assert audit["red_id"] == P4_RUNTIME_BACKFILL_HIJ_RED_ID
    assert audit["phase"] == "P4_runtime_backfill_red_repair"
    assert audit["target_scope"] == {
        "family": "change_future_intention",
        "repair_kind": "current_only_surface_specificity",
        "target_runtime_lane": "eligible_non_limited_labelled_two_stage_recomposition",
        "not_release_decision": True,
    }
    red = _as_mapping(audit["r0_red_ledger"])
    assert red["status"] == "CLOSED_BY_R2_R3"
    assert red["red_classification"] == "current_only_surface_specificity_red"
    assert red["repair_stage"] == "R2_R3_eligible_future_direction_surface_specificity"
    assert red["public_feedback_arrived"] is True
    assert red["observation_status"] == "passed"
    assert red["specificity_required"] is True
    assert red["specificity_met"] is True
    assert red["generic_surface_detected"] is False
    assert set(red["expected_surface_role_ids"]) == {role_id for _fragment, role_id in _EXPECTED_SURFACE_ROLES}
    assert red["missing_surface_role_ids"] == ()
    assert red["forbidden_generic_signature_ids"] == ()
    assert red["public_contract_changed"] is False
    assert red["body_boundary_passed"] is True
    assert all(audit["public_contract_flags"].get(key) is False for key in _PUBLIC_CONTRACT_FALSE_KEYS)
    assert audit["body_boundary"]["body_free"] is True
    assert all(audit["body_boundary"].get(key) is False for key in _BODY_FREE_FALSE_KEYS)
    _assert_body_free_audit(audit=audit, case=case, comment_text=comment_text)


@pytest.mark.asyncio
async def test_p4_r1_material_candidate_lineage_audit_keeps_material_presence_separate_from_surface_drop(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    case, result, captured = await _run_target_case(monkeypatch)
    audit = _build_p4_r0_r1_audit(case=case, result=result, captured=captured)
    material = _as_mapping(audit["r1_material_audit"])
    lineage = _as_mapping(audit["r1_candidate_lineage_audit"])

    assert material["material_quality"] == "eligible"
    assert material["semantic_focus_id"] == "recovered_energy_future_direction"
    assert material["required_semantic_material_present"] is True
    assert material["required_visible_slots_present"] is True
    assert set(material["semantic_material_ids"]) == set(_REQUIRED_SEMANTIC_MATERIAL_IDS)
    assert set(material["visible_material_slot_ids"]) == set(_REQUIRED_VISIBLE_MATERIAL_SLOT_IDS)
    assert material["direct_surface_requirement_family"] == "plain_state_answer"
    assert material["direct_two_stage_required"] is False
    assert material["direct_plain_state_answer_allowed"] is True
    assert material["runtime_material_quality"] == "eligible"
    assert set(material["runtime_material_relation_ids"]) == set(_REQUIRED_SEMANTIC_MATERIAL_IDS)

    assert lineage["direct_requirement_to_runtime_requirement_shift_detected"] is True
    assert lineage["runtime_surface_requirement_family"] == "labelled_two_stage"
    assert lineage["runtime_two_stage_required"] is True
    assert lineage["runtime_plain_state_answer_allowed"] is False
    assert lineage["selected_public_candidate_source_kind"] == CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE
    assert lineage["final_public_candidate_source_kind"] == CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE
    assert lineage["recovery_input_candidate_source_kind"] == CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_COMPOSER
    assert lineage["root_candidate_source_kind"] == "ai_generated"
    assert lineage["complete_initial_candidate_generated_before_display_gate"] is True
    assert lineage["complete_initial_first_blocker_family"] == "surface_failure"
    assert lineage["complete_initial_first_blocker_code"] == "unsupported_sentence"
    assert lineage["labelled_two_stage_surface_recomposition_used"] is True
    assert lineage["limited_grounding_reception_surface_used"] is False
    assert lineage["normal_observation_rebuild_used"] is False
    assert lineage["gate_recovery_loop_applied"] is True
    assert all(audit["public_contract_flags"].get(key) is False for key in _PUBLIC_CONTRACT_FALSE_KEYS)
