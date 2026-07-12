# -*- coding: utf-8 -*-
from __future__ import annotations

"""Focused regression for D-equivalent source-unavailable normal observation recovery.

This file intentionally does not add a runtime case route or a fixed public text.
It locks the D-equivalent failure as a generic boundary:

safe_observation + material eligible + limited composer shallow empty
must be recoverable as a normal public observation through complete-initial
surface recomposition, while preserving the existing gates and RN contract.
"""

from collections.abc import Mapping
import os
from typing import Any

import pytest

import emlis_ai_context_service as context_service
import emlis_ai_reply_service as reply_service
from emlis_ai_input_material_bundle import MATERIAL_QUALITY_ELIGIBLE
from emlis_ai_observation_eligibility_router import EMLIS_OBSERVATION_ELIGIBILITY_ROUTER_META_KEY
from emlis_ai_public_feedback_meta import should_include_public_input_feedback
from emlis_ai_response_contract import EMLIS_INTERNAL_RESPONSE_CONTRACT_META_KEY
from emlis_ai_safety_triage import EMLIS_SAFETY_TRIAGE_META_KEY, TRIAGE_SAFE_OBSERVATION
from emlis_ai_types import GreetingDecision


_LIMITED_COMPOSER_ENV_KEYS = (
    "COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED",
    "COCOLON_EMLIS_AI_LIMITED_COMPOSER_ENABLED",
    "EMLIS_AI_LIMITED_COMPOSER_ENABLED",
    "COCOLON_LIMITED_COMPOSER_ENABLED",
    "COCOLON_EMLIS_AI_DEFAULT_LIMITED_COMPOSER_ENABLED",
    "EMLIS_AI_DEFAULT_LIMITED_COMPOSER_ENABLED",
    "COCOLON_EMLIS_DEFAULT_COMPOSER",
    "COCOLON_EMLIS_AI_DEFAULT_COMPOSER",
    "EMLIS_AI_DEFAULT_COMPOSER",
    "COCOLON_EMLIS_LIMITED_COMPOSER_ROLLOUT_STAGE",
    "COCOLON_EMLIS_AI_LIMITED_COMPOSER_ROLLOUT_STAGE",
    "EMLIS_AI_LIMITED_COMPOSER_ROLLOUT_STAGE",
    "COCOLON_EMLIS_LIMITED_COMPOSER_ROLLOUT",
    "EMLIS_AI_LIMITED_COMPOSER_ROLLOUT",
)
_FORBIDDEN_PHASE19_OR_CASE_ROUTE_TOKENS = (
    "relationship_gratitude_recovery",
    "phase19_real_device_D_relationship_gratitude_recovery",
    "phase19_case_specific_route_used': True",
    'phase19_case_specific_route_used": true',
    "case_id_runtime_condition_used': True",
    'case_id_runtime_condition_used": true',
)
_REQUIRED_VISIBLE_MATERIAL_SLOTS = {"relationship", "action", "change", "value"}
_SOURCE_UNAVAILABLE_BLOCKER = "limited_composer_shallow_empty_candidate"
_SENTENCE_PLAN_UNAVAILABLE = "sentence_plan_unavailable"
_D_SOURCE_UNAVAILABLE_INPUT = {
    "memo": (
        "悲しい気持ちばかりで身の回りにある優しさを見逃してしまいそうになるが、"
        "ちゃんと優しさに触れてそれを実感出来ていることが嬉しい。"
        "そして私のために怒ってくれる存在に感謝の気持ちが溢れてくる。"
        "1つの関係の終わりが、もうひとつの友達という関係を強くしてくれたと考えれば、"
        "少し自分の中で区切りがついて成長出来るように感じる。"
        "そしてその優しさを今回受け止めて別の形で必ず返していきたい。"
    ),
    "memo_action": "彼氏と別れたが、友達が変わらず今も優しくしてくれている。そして私のために怒ってくれている。",
    "emotions": ["喜び"],
    "category": ["恋愛", "人間関係", "価値観"],
}


@pytest.fixture(autouse=True)
def _patch_source_bundle(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_display_name(_user_id: str) -> str:
        return "Mash"

    async def fake_timezone(_user_id: str, *, fallback: str | None = None) -> str:
        return str(fallback or "Asia/Tokyo")

    async def fake_greeting(**_kwargs: Any) -> GreetingDecision:
        return GreetingDecision(
            slot_name="d-source-unavailable-normal-observation-recovery",
            slot_key="d-source-unavailable-normal-observation-recovery",
            greeting_text="Emlisです。",
            first_in_slot=False,
        )

    async def empty_dict(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        return {}

    async def empty_list(*_args: Any, **_kwargs: Any) -> list[Any]:
        return []

    async def none_value(*_args: Any, **_kwargs: Any) -> None:
        return None

    monkeypatch.setattr(context_service, "_resolve_display_name_for_user", fake_display_name)
    monkeypatch.setattr(context_service, "_resolve_timezone_name_for_user", fake_timezone)
    monkeypatch.setattr(context_service, "decide_greeting_for_user", fake_greeting)
    for name, replacement in {
        "_get_input_summary_for_user": empty_dict,
        "_get_myweb_home_summary_for_user": empty_dict,
        "_get_latest_today_question_answer_for_user": empty_dict,
        "_list_recent_today_question_answers_for_user": empty_list,
        "get_last_input_for_user": none_value,
        "list_same_day_recent_inputs": empty_list,
        "search_similar_inputs": empty_list,
        "load_emlis_ai_user_model_for_user": none_value,
        "get_cross_core_context_for_emlis_ai": empty_list,
    }.items():
        if hasattr(context_service, name):
            monkeypatch.setattr(context_service, name, replacement)


@pytest.fixture()
def limited_composer_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in _LIMITED_COMPOSER_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED", "true")


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _diagnostic_summary(meta: Mapping[str, Any]) -> Mapping[str, Any]:
    return _mapping(meta.get("diagnostic_summary"))


def _availability_summary(meta: Mapping[str, Any]) -> Mapping[str, Any]:
    return _mapping(_diagnostic_summary(meta).get("complete_initial_surface_availability_summary"))


def _gate_recovery_public_boundary(meta: Mapping[str, Any]) -> Mapping[str, Any]:
    return _mapping(
        meta.get("phase20_5_gate_recovery_public_boundary")
        or _diagnostic_summary(meta).get("phase20_5_gate_recovery_public_boundary")
    )


def _gate_recovery_candidate_builder(meta: Mapping[str, Any]) -> Mapping[str, Any]:
    boundary = _gate_recovery_public_boundary(meta)
    loop_result = _mapping(boundary.get("gate_recovery_loop_result"))
    surface_binding = _mapping(
        loop_result.get("phase20_15_gate_recovery_surface_binding")
        or loop_result.get("gate_recovery_surface_binding")
    )
    return _mapping(surface_binding.get("phase20_5_gate_recovery_public_candidate_builder"))


def _gate_results(meta: Mapping[str, Any]) -> Mapping[str, Any]:
    return _mapping(_diagnostic_summary(meta).get("gate_results"))


def _source_unavailable_availability_summary(meta: Mapping[str, Any]) -> Mapping[str, Any]:
    builder = _gate_recovery_candidate_builder(meta)
    recovery_plan = _mapping(builder.get("recovery_plan"))
    pre_public = _mapping(recovery_plan.get("complete_initial_surface_availability_summary"))
    if pre_public:
        return pre_public
    return _availability_summary(meta)


def _recomposition_boundary_decision(meta: Mapping[str, Any]) -> Mapping[str, Any]:
    return _mapping(_gate_recovery_public_boundary(meta).get("gate_recovery_public_boundary_decision"))


def _recomposition_summary(meta: Mapping[str, Any]) -> Mapping[str, Any]:
    top_level = _mapping(
        meta.get("complete_initial_surface_recomposition_summary")
        or _diagnostic_summary(meta).get("complete_initial_surface_recomposition_summary")
    )
    if top_level:
        return top_level

    boundary = _gate_recovery_public_boundary(meta)
    builder = _gate_recovery_candidate_builder(meta)
    decision = _recomposition_boundary_decision(meta)
    if not boundary and not builder and not decision:
        return {}
    contract_flags = _mapping(decision.get("contract_flags"))
    return {
        "attempted": bool(boundary.get("attempted")),
        "applied": bool(boundary.get("adopted")),
        "candidate_generated": bool(builder.get("candidate_available")),
        "candidate_source_kind": str(
            decision.get("candidate_source_kind")
            or builder.get("source_kind")
            or ""
        ),
        "normal_observation_rebuild_used": False,
        "gate_recovery_material_surface_used": False,
        "display_gate_relaxed": bool(contract_flags.get("display_gate_relaxed")),
        "raw_input_included": bool(contract_flags.get("raw_input_included")),
        "comment_text_body_included": bool(contract_flags.get("comment_text_body_included")),
        "candidate_body_in_meta": bool(contract_flags.get("candidate_body_in_meta")),
        "case_specific_route_used": bool(contract_flags.get("case_specific_route_used")),
    }


def _rn_modal_opened(comment_text: str, meta: Mapping[str, Any]) -> bool:
    return bool(should_include_public_input_feedback(comment_text, meta) and meta.get("observation_status") == "passed")


async def _render_d_source_unavailable_reply() -> Any:
    return await reply_service.render_emlis_ai_reply(
        user_id="d-source-unavailable-normal-observation-recovery-user",
        subscription_tier="free",
        current_input=dict(_D_SOURCE_UNAVAILABLE_INPUT),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )


@pytest.mark.asyncio
async def test_d_source_unavailable_input_locks_safe_eligible_material_and_limited_shallow_empty(
    limited_composer_env: None,
) -> None:
    assert os.environ["COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED"] == "true"

    reply = await _render_d_source_unavailable_reply()
    meta = _mapping(getattr(reply, "meta", {}))
    safety = _mapping(meta.get(EMLIS_SAFETY_TRIAGE_META_KEY))
    material_route = _mapping(meta.get(EMLIS_OBSERVATION_ELIGIBILITY_ROUTER_META_KEY))
    diagnostic = _diagnostic_summary(meta)
    composer_diagnostic = _mapping(diagnostic.get("composer_diagnostic"))
    availability = _source_unavailable_availability_summary(meta)
    recomposition = _recomposition_summary(meta)

    assert safety.get("safety_triage_kind") == TRIAGE_SAFE_OBSERVATION
    assert safety.get("requires_block") is False
    assert material_route.get("safety_triage_kind") == TRIAGE_SAFE_OBSERVATION
    assert material_route.get("material_quality") == MATERIAL_QUALITY_ELIGIBLE
    assert material_route.get("response_kind") == "normal_observation"
    assert material_route.get("public_observation_status") == "passed"
    assert material_route.get("comment_text_required") is True
    assert material_route.get("public_input_feedback_allowed") is True
    assert _REQUIRED_VISIBLE_MATERIAL_SLOTS.issubset(set(material_route.get("visible_material_slots") or []))
    # I4 withdraws relation semantics synthesized by the legacy material route.
    # Canonical-plan ownership/path-truth metadata is connected at I5, so this
    # integration regression only freezes the absence of legacy relation IDs.
    assert material_route.get("relation_material_ids") == []

    assert availability.get("first_blocker_family") == "source_unavailable"
    assert availability.get("first_blocker_code") == _SOURCE_UNAVAILABLE_BLOCKER
    assert availability.get("candidate_status") == "unavailable"
    assert availability.get("composer_source") == "unavailable"
    assert availability.get("material_sufficient") is True
    assert availability.get("material_quality_family") == MATERIAL_QUALITY_ELIGIBLE
    assert availability.get("surface_requirement_family") == "labelled_two_stage"
    assert availability.get("recovery_lane") == "complete_initial_surface_recomposition"

    if diagnostic.get("primary_reason") == _SOURCE_UNAVAILABLE_BLOCKER:
        assert diagnostic.get("composer_status") == "unavailable"
        assert composer_diagnostic.get("composer_model") == "cocolon_limited_composer.v1"
        assert composer_diagnostic.get("composer_status") == "unavailable"
        assert composer_diagnostic.get("sentence_plan_unavailable") is True
        assert composer_diagnostic.get("reason_category") == _SENTENCE_PLAN_UNAVAILABLE
    else:
        assert diagnostic.get("primary_reason") == "passed"
        assert recomposition.get("applied") is True
        assert recomposition.get("candidate_generated") is True
        assert recomposition.get("candidate_source_kind") == "complete_initial_surface_recomposition_candidate"


@pytest.mark.asyncio
async def test_d_source_unavailable_normal_observation_recovers_via_complete_initial_surface_recomposition(
    limited_composer_env: None,
) -> None:
    reply = await _render_d_source_unavailable_reply()
    meta = _mapping(getattr(reply, "meta", {}))
    internal = _mapping(meta.get(EMLIS_INTERNAL_RESPONSE_CONTRACT_META_KEY))
    material_route = _mapping(meta.get(EMLIS_OBSERVATION_ELIGIBILITY_ROUTER_META_KEY))
    availability = _source_unavailable_availability_summary(meta)
    recomposition = _recomposition_summary(meta)
    comment_text = str(getattr(reply, "comment_text", "") or "")

    assert material_route.get("safety_triage_kind") == TRIAGE_SAFE_OBSERVATION
    assert material_route.get("material_quality") == MATERIAL_QUALITY_ELIGIBLE
    assert material_route.get("response_kind") == "normal_observation"
    assert _REQUIRED_VISIBLE_MATERIAL_SLOTS.issubset(set(material_route.get("visible_material_slots") or []))

    assert availability.get("first_blocker_family") == "source_unavailable"
    assert availability.get("first_blocker_code") == _SOURCE_UNAVAILABLE_BLOCKER
    assert availability.get("normal_observation_rebuild_allowed") is False
    assert availability.get("normal_observation_rebuild_blocker") == "source_unavailable_not_rebuildable"
    assert availability.get("body_free") is True
    assert availability.get("raw_input_included") is False
    assert availability.get("comment_text_body_included") is False

    assert availability.get("material_sufficient") is True
    assert availability.get("material_quality_family") == MATERIAL_QUALITY_ELIGIBLE
    assert availability.get("surface_requirement_family") == "labelled_two_stage"
    assert availability.get("recovery_lane") == "complete_initial_surface_recomposition"

    assert recomposition.get("attempted") is True
    assert recomposition.get("applied") is True
    assert recomposition.get("candidate_generated") is True
    assert recomposition.get("candidate_source_kind") == "complete_initial_surface_recomposition_candidate"
    assert recomposition.get("normal_observation_rebuild_used") is False
    assert recomposition.get("gate_recovery_material_surface_used") is False
    assert recomposition.get("display_gate_relaxed") is False
    assert recomposition.get("raw_input_included") is False
    assert recomposition.get("comment_text_body_included") is False
    assert recomposition.get("candidate_body_in_meta") is False
    assert recomposition.get("case_specific_route_used") is False
    assert recomposition.get("passed_by_all_existing_gates") is True
    assert recomposition.get("candidate_adopted_after_existing_gates") is True
    gate_chain = _mapping(recomposition.get("existing_gate_chain"))
    assert gate_chain.get("reader_gate_passed") is True
    assert gate_chain.get("grounding_gate_passed") is True
    assert gate_chain.get("template_gate_passed") is True
    assert gate_chain.get("runtime_surface_pre_return_gate_passed") is True
    assert gate_chain.get("visible_surface_acceptance_gate_passed") is True
    assert gate_chain.get("display_gate_passed") is True
    assert gate_chain.get("passed_by_all_existing_gates") is True
    assert gate_chain.get("candidate_adopted_after_existing_gates") is True
    assert gate_chain.get("display_gate_relaxed") is False
    assert gate_chain.get("grounding_gate_relaxed") is False
    assert gate_chain.get("template_gate_relaxed") is False
    assert gate_chain.get("reader_gate_relaxed") is False
    assert gate_chain.get("candidate_body_in_meta") is False
    assert gate_chain.get("raw_input_included") is False
    assert gate_chain.get("comment_text_body_included") is False

    assert internal.get("response_kind") == "normal_observation"
    assert meta.get("observation_status") == "passed"
    assert internal.get("public_observation_status") == "passed"
    assert internal.get("safety_triage_kind") == TRIAGE_SAFE_OBSERVATION
    assert internal.get("comment_text_required") is True
    assert internal.get("public_input_feedback_allowed") is True
    assert comment_text.strip()
    assert "見えたこと：" in comment_text
    assert "Emlisから：" in comment_text
    assert _rn_modal_opened(comment_text, meta) is True

    dumped_meta = str(meta)
    for token in _FORBIDDEN_PHASE19_OR_CASE_ROUTE_TOKENS:
        assert token not in dumped_meta
        assert token not in comment_text


@pytest.mark.asyncio
async def test_d_source_unavailable_recomposition_candidate_passes_existing_gate_path_without_relaxing_gates(
    limited_composer_env: None,
) -> None:
    reply = await _render_d_source_unavailable_reply()
    meta = _mapping(getattr(reply, "meta", {}))
    diagnostic = _diagnostic_summary(meta)
    recomposition = _recomposition_summary(meta)
    runtime_gate = _mapping(diagnostic.get("runtime_surface_pre_return_gate"))
    gate_results = _gate_results(meta)

    assert recomposition.get("attempted") is True
    assert recomposition.get("applied") is True
    assert recomposition.get("candidate_generated") is True
    assert recomposition.get("candidate_source_kind") == "complete_initial_surface_recomposition_candidate"
    assert recomposition.get("display_gate_relaxed") is False
    assert recomposition.get("gate_recovery_material_surface_used") is False
    assert recomposition.get("normal_observation_rebuild_used") is False

    assert diagnostic.get("complete_initial_existing_gates_preserved_after_generation") is True

    assert runtime_gate.get("evaluated") is True
    assert runtime_gate.get("passed") is True
    assert runtime_gate.get("action") == "allow"
    assert runtime_gate.get("rejection_reasons") == []
    assert runtime_gate.get("display_gate_relaxed") is False
    assert runtime_gate.get("raw_input_included") is False
    assert runtime_gate.get("comment_text_body_included") is False

    for gate_key in (
        "reader",
        "grounding",
        "template_echo",
        "visible_surface_acceptance",
        "display",
    ):
        gate = _mapping(gate_results.get(gate_key))
        assert gate.get("passed") is True
        assert gate.get("status") == "passed"
        assert gate.get("primary_reason") == "passed"
        assert gate.get("rejection_reasons") == []
        reflection = _mapping(gate.get("step7_gate_binding_reflection"))
        if reflection:
            assert reflection.get("gate_threshold_relaxed") is False
            assert reflection.get("display_contract_relaxed") is False
            assert reflection.get("raw_text_included") is False
            assert reflection.get("raw_input_required_for_debug") is False

    assert meta.get("observation_status") == "passed"
    assert str(getattr(reply, "comment_text", "") or "").strip()
