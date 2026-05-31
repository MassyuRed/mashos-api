# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase20-4 generic low-information observation recovery contract tests.

Phase20-4 restores low-information inputs as Emlis observations without turning
A-like short text into a case route.  The branch must use the Phase20-3 input
material bundle, separate visible material from unknown slots, avoid raw-input
echo, and keep the existing public ``passed + comment_text`` contract.
"""

from collections.abc import Mapping
from typing import Any

from emlis_ai_input_material_bundle import (
    EMLIS_INPUT_MATERIAL_BUNDLE_META_KEY,
    MATERIAL_QUALITY_LOW_INFORMATION,
)
from emlis_ai_low_information_observation_composer import (
    compose_low_information_observation,
)
from emlis_ai_observation_display_repair_integration import (
    integrate_observation_display_repair,
)
from emlis_ai_observation_eligibility_router import (
    route_emlis_observation_eligibility_by_material,
)
from emlis_ai_observation_reply_contract import OBSERVATION_REPLY_KIND_LOW_INFORMATION
from emlis_ai_types import (
    DisplayDecision,
    GroundingReport,
    ListenerReaderReport,
    SafetyBoundaryReport,
    TemplateEchoReport,
)


_PHASE19_A_CURRENT_INPUT = {
    "memo": "なんか今日は全部だるい。\n何もしたくない。",
    "memo_action": "",
    "emotions": ["悲しみ", "不安"],
    "emotion_details": [
        {"type": "悲しみ", "strength": "medium"},
        {"type": "不安", "strength": "medium"},
    ],
    "category": ["生活"],
}

_LOW_INFORMATION_SHORT_VARIANTS = (
    {
        "memo": "なんか無理",
        "memo_action": "",
        "emotions": ["疲れ"],
        "emotion_details": [{"type": "疲れ", "strength": "medium"}],
        "category": ["生活"],
    },
    {
        "memo": "もう考えたくない",
        "memo_action": "",
        "emotions": ["疲れ"],
        "emotion_details": [{"type": "疲れ", "strength": "weak"}],
        "category": ["生活"],
    },
    {
        "memo": "",
        "memo_action": "",
        "emotions": ["悲しみ"],
        "emotion_details": [{"type": "悲しみ", "strength": "weak"}],
        "category": ["生活"],
    },
)

_FORBIDDEN_SURFACE_FRAGMENTS = (
    "なんか今日は全部だるい",
    "何もしたくない",
    "なんか無理",
    "もう考えたくない",
    "Emlisでは観測できません",
    "もっと詳しく教えてください",
    "よければ、何がありましたか",
    "あなたは十分頑張っています",
    "あなたはいつも",
    "診断",
    "人格",
)


def _rejected_display(*reasons: str) -> DisplayDecision:
    return DisplayDecision(
        observation_status="rejected",
        comment_text="",
        rejection_reasons=list(reasons),
        trace_id="phase20-4-low-info",
    )


def _reader(*reasons: str) -> ListenerReaderReport:
    return ListenerReaderReport(
        understandable=False,
        addressee_clear=False,
        speaker_integrity_ok=True,
        conversational=False,
        report_like=False,
        rejection_reasons=list(reasons),
    )


def _grounding(*reasons: str) -> GroundingReport:
    return GroundingReport(passed=False, rejection_reasons=list(reasons))


def _assert_low_information_surface(text: str) -> None:
    assert text.strip()
    assert "ここから見えているのは" in text or "まだ詳しい出来事までは見えません" in text
    assert "詳しく残せそうなら" in text
    assert "残してみませんか" in text
    assert "?" not in text
    for fragment in _FORBIDDEN_SURFACE_FRAGMENTS:
        assert fragment not in text


def _composer_meta_from_result(result: Any) -> Mapping[str, Any]:
    meta = result.as_meta()
    composer_meta = meta.get("low_information_observation_composer_meta")
    assert isinstance(composer_meta, Mapping)
    return composer_meta


def test_phase20_4_a_exact_fixture_becomes_generic_low_information_observation() -> None:
    draft = compose_low_information_observation(
        current_input=_PHASE19_A_CURRENT_INPUT,
        subscription_tier="free",
    )

    _assert_low_information_surface(draft.body)
    meta = draft.as_meta()
    assert meta["observation_reply_kind"] == OBSERVATION_REPLY_KIND_LOW_INFORMATION
    assert meta["eligibility_status"] == "low_information"
    assert meta["phase20_4_low_information_material_surface_ready"] is True
    assert meta["low_information_surface_from_visible_material_slots"] is True
    assert meta["unknown_prompt_from_unknown_slots"] is True
    assert meta["question_not_only"] is True
    assert meta["visible_material_slots"]
    assert meta["unknown_slots"]
    assert meta["fixed_fallback_used"] is False
    assert meta["raw_input_included"] is False
    assert meta["comment_text_generated"] is False

    material_plan = meta["low_information_material_surface_plan"]
    assert material_plan["selected_by_input_material_bundle"] is True
    assert material_plan["material_quality"] == MATERIAL_QUALITY_LOW_INFORMATION
    assert material_plan["known_scope_surface_from_visible_material_slots"] is True
    assert material_plan["question_surface_from_unknown_slots"] is True
    assert material_plan["question_only"] is False
    assert material_plan["case_specific_route_used"] is False
    assert material_plan["phase19_case_specific_route_used"] is False



def test_phase20_4_short_variants_recover_without_fixed_fallback_or_raw_echo() -> None:
    for current_input in _LOW_INFORMATION_SHORT_VARIANTS:
        draft = compose_low_information_observation(
            current_input=current_input,
            subscription_tier="free",
        )
        _assert_low_information_surface(draft.body)
        meta = draft.as_meta()
        assert meta["observation_reply_kind"] == OBSERVATION_REPLY_KIND_LOW_INFORMATION
        assert meta["phase20_4_low_information_material_surface_ready"] is True
        assert meta["low_information_surface_from_visible_material_slots"] is True
        assert meta["unknown_prompt_from_unknown_slots"] is True
        assert meta["question_not_only"] is True
        assert meta["raw_input_included"] is False
        assert meta["fixed_fallback_used"] is False
        assert meta["unsupported_assertion_allowed"] is False
        assert meta["personality_tendency_allowed"] is False



def test_phase20_4_display_repair_uses_material_bundle_and_keeps_public_contract() -> None:
    material_route = route_emlis_observation_eligibility_by_material(
        _PHASE19_A_CURRENT_INPUT,
    )
    repair_context = material_route.as_low_information_repair_context(
        complete_initial_default_requested=True,
    )
    assert repair_context["repair_allowed_under_complete_initial"] is True
    assert repair_context["material_quality"] == MATERIAL_QUALITY_LOW_INFORMATION

    result = integrate_observation_display_repair(
        current_input=_PHASE19_A_CURRENT_INPUT,
        subscription_tier="free",
        safety_report=SafetyBoundaryReport(),
        trace_id="phase20-4-a-exact-display-repair",
        original_display_decision=_rejected_display("too_short_for_observation"),
        original_reader_report=_reader("too_short_for_observation"),
        original_grounding_report=_grounding("graph_evidence_not_used"),
        original_template_echo_report=TemplateEchoReport(passed=True),
        original_composer_source="unavailable",
        original_composer_candidate=None,
        repair_context=repair_context,
    )

    assert result.applied is True
    assert result.display_decision.observation_status == "passed"
    _assert_low_information_surface(result.display_decision.comment_text)

    meta = result.as_meta()
    assert meta["public_status_extended"] is False
    assert meta["rn_visible_contract_changed"] is False
    assert meta["api_route_changed"] is False
    assert meta["db_physical_name_changed"] is False
    assert meta["phase20_3_low_information_repair_allowed"] is True
    assert meta["phase20_3_input_material_bundle"]
    assert meta["phase20_3_input_material_bundle"]["material_quality"] == MATERIAL_QUALITY_LOW_INFORMATION

    composer_meta = _composer_meta_from_result(result)
    assert composer_meta["phase20_4_low_information_material_surface_ready"] is True
    assert composer_meta["low_information_surface_from_visible_material_slots"] is True
    assert composer_meta["unknown_prompt_from_unknown_slots"] is True
    assert composer_meta["low_information_material_surface_plan"]["input_material_bundle_meta"] == repair_context[
        EMLIS_INPUT_MATERIAL_BUNDLE_META_KEY
    ]
    assert composer_meta["raw_input_included"] is False
    assert composer_meta["fixed_fallback_used"] is False
