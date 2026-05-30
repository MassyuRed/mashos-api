# -*- coding: utf-8 -*-
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import pytest

from emlis_ai_observation_display_repair_integration import (
    LOW_INFORMATION_PUBLIC_REPAIR_CONTRACT_SCHEMA_VERSION,
    LOW_INFORMATION_PUBLIC_REPAIR_SOURCE_PHASE,
    assert_low_information_public_repair_contract_meta_only,
    integrate_observation_display_repair,
)
from emlis_ai_observation_reply_contract import OBSERVATION_REPLY_KIND_LOW_INFORMATION
from emlis_ai_reply_service import render_emlis_ai_reply
from emlis_ai_types import (
    ConversationComposerCandidate,
    DisplayDecision,
    GroundingReport,
    ListenerReaderReport,
    SafetyBoundaryReport,
    TemplateEchoReport,
)


def _input(memo: str, *, emotions: list[str] | None = None) -> dict[str, Any]:
    labels = list(emotions if emotions is not None else ["疲れ"])
    return {
        "id": f"phase18-low-information-{abs(hash((memo, tuple(labels))))}",
        "created_at": "2026-05-30T00:00:00Z",
        "memo": memo,
        "memo_action": "",
        "emotion_details": [{"type": label, "strength": "medium"} for label in labels],
        "emotions": labels,
        "category": ["生活"],
    }


def _unavailable_display(*reasons: str) -> DisplayDecision:
    return DisplayDecision(
        observation_status="unavailable",
        comment_text="",
        rejection_reasons=list(reasons),
        trace_id="phase18-low-info-unavailable",
    )


def _rejected_display(*reasons: str) -> DisplayDecision:
    return DisplayDecision(
        observation_status="rejected",
        comment_text="",
        rejection_reasons=list(reasons),
        trace_id="phase18-low-info-rejected",
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
    return GroundingReport(
        passed=False,
        rejection_reasons=list(reasons),
    )


def _contract_from_step10(step10: Mapping[str, Any]) -> Mapping[str, Any]:
    contract = step10.get("low_information_public_repair_contract")
    assert isinstance(contract, Mapping)
    assert step10.get("phase18_low_information_public_repair_contract") == contract
    return contract


def _walk(value: Any) -> list[tuple[str, Any]]:
    out: list[tuple[str, Any]] = []

    def rec(item: Any, path: str) -> None:
        if isinstance(item, Mapping):
            for key, child in item.items():
                rec(child, f"{path}.{key}")
        elif isinstance(item, Sequence) and not isinstance(item, (str, bytes, bytearray)):
            for index, child in enumerate(item):
                rec(child, f"{path}[{index}]")
        else:
            out.append((path, item))

    rec(value, "$")
    return out


def _assert_contract_has_no_body_or_raw_input(
    contract: Mapping[str, Any],
    *,
    raw_input: str,
    comment_text: str = "",
) -> None:
    forbidden_exact_keys = {"raw_input", "raw_text", "comment_text", "body", "text", "candidate_text", "generated_text"}
    for key in contract.keys():
        assert str(key) not in forbidden_exact_keys
    for path, value in _walk(contract):
        if isinstance(value, str):
            assert raw_input not in value
            if comment_text:
                assert comment_text not in value


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "memo,expected_fragment",
    [
        ("疲れた", "疲れの重さ"),
        ("なんか無理", "無理かもしれない感じ"),
        ("大丈夫かどうか不安", "大丈夫かどうか"),
    ],
)
async def test_phase18_4_public_low_information_repair_contract_is_attached_without_contract_change(
    memo: str,
    expected_fragment: str,
) -> None:
    reply = await render_emlis_ai_reply(
        user_id="phase18-low-information-public-repair-user",
        subscription_tier="free",
        current_input=_input(memo),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
        composer_client=None,
    )

    assert reply.meta["observation_status"] == "passed"
    assert expected_fragment in reply.comment_text
    step10 = reply.meta["step10_observation_display_repair_integration"]
    assert step10["applied"] is True
    contract = _contract_from_step10(step10)

    assert contract["schema_version"] == LOW_INFORMATION_PUBLIC_REPAIR_CONTRACT_SCHEMA_VERSION
    assert contract["source_phase"] == LOW_INFORMATION_PUBLIC_REPAIR_SOURCE_PHASE
    assert contract["eligible"] is True
    assert contract["eligibility_reason"] == "low_information_current_input_with_user_signal"
    assert contract["repair_route_allowed"] is True
    assert contract["repair_route_reason"] == "ordinary_unavailable_low_information_route"
    assert contract["final_observation_status"] == "passed"
    assert contract["observation_reply_kind"] == OBSERVATION_REPLY_KIND_LOW_INFORMATION
    assert contract["question_required"] is True
    assert contract["question_surface_family"] == "詳しく残せそうなら"
    assert contract["blocked_by_safety"] is False
    assert contract["blocked_by_scope"] is False
    assert contract["blocked_by_ap0"] is False
    assert contract["blocked_by_rollout"] is False
    assert contract["blocked_by_non_repairable_ai_candidate"] is False
    assert contract["public_contract"] == {
        "public_status_extended": False,
        "public_response_key_added": False,
        "observation_status_enum_extended": False,
        "rn_visible_contract_changed": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "comment_text_body_included_in_meta": False,
        "raw_input_included": False,
        "raw_text_included": False,
    }
    assert contract["gate_policy"] == {
        "display_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
    }
    assert_low_information_public_repair_contract_meta_only(contract)
    _assert_contract_has_no_body_or_raw_input(contract, raw_input=memo, comment_text=reply.comment_text)


def test_phase18_4_two_stage_synthetic_reasons_do_not_block_low_information_public_repair() -> None:
    result = integrate_observation_display_repair(
        current_input={"memo": "疲れた", "memo_action": "", "emotions": ["疲れ"], "category": ["生活"]},
        subscription_tier="free",
        safety_report=SafetyBoundaryReport(),
        trace_id="phase18-two-stage-synthetic-low-info",
        original_display_decision=_unavailable_display(
            "empty_text",
            "too_short_for_observation",
            "two_stage_required_but_unrealized",
            "two_stage_label_missing",
        ),
        original_reader_report=_reader("two_stage_label_missing"),
        original_grounding_report=_grounding("empty_text"),
        original_template_echo_report=TemplateEchoReport(passed=True),
        original_composer_source="unavailable",
        original_composer_candidate=None,
    )

    assert result.applied is True
    assert result.display_decision.observation_status == "passed"
    contract = _contract_from_step10(result.as_meta())
    assert contract["repair_route_allowed"] is True
    assert contract["repair_route_reason"] == "ordinary_unavailable_low_information_route"
    assert set(contract["ignored_synthetic_reasons"]).issuperset(
        {
            "empty_text",
            "too_short_for_observation",
            "two_stage_required_but_unrealized",
            "two_stage_label_missing",
        }
    )
    assert contract["blocked_by_safety"] is False
    assert contract["blocked_by_non_repairable_ai_candidate"] is False
    assert_low_information_public_repair_contract_meta_only(contract)


def test_phase18_4_safety_block_keeps_low_information_repair_fail_closed() -> None:
    result = integrate_observation_display_repair(
        current_input={"memo": "危険なことをしたい", "memo_action": "", "emotions": ["疲れ"]},
        subscription_tier="free",
        safety_report=SafetyBoundaryReport(requires_block=True, reasons=["safety_blocked"]),
        trace_id="phase18-low-info-safety-blocked",
        original_display_decision=DisplayDecision(
            observation_status="safety_blocked",
            comment_text="",
            rejection_reasons=["safety_boundary"],
            trace_id="phase18-low-info-safety-blocked",
        ),
        original_reader_report=_reader("safety_boundary"),
        original_grounding_report=_grounding("safety_boundary"),
        original_template_echo_report=TemplateEchoReport(passed=True),
        original_composer_source="",
        original_composer_candidate=None,
    )

    assert result.applied is False
    assert result.display_decision.observation_status == "safety_blocked"
    contract = _contract_from_step10(result.as_meta())
    assert contract["repair_route_allowed"] is False
    assert contract["blocked_by_safety"] is True
    assert contract["final_observation_status"] == "safety_blocked"
    assert contract["public_contract"]["public_status_extended"] is False
    assert contract["gate_policy"]["display_gate_relaxed"] is False
    assert_low_information_public_repair_contract_meta_only(contract)



def test_phase18_4_scope_block_keeps_low_information_repair_fail_closed() -> None:
    result = integrate_observation_display_repair(
        current_input={"memo": "疲れた", "memo_action": "", "emotions": ["疲れ"]},
        subscription_tier="free",
        safety_report=SafetyBoundaryReport(),
        trace_id="phase18-low-info-scope-blocked",
        original_display_decision=_unavailable_display("composer_source_unavailable"),
        original_reader_report=_reader("composer_source_unavailable"),
        original_grounding_report=_grounding("composer_source_unavailable"),
        original_template_echo_report=TemplateEchoReport(passed=True),
        original_composer_source="unavailable",
        original_composer_candidate=None,
        composer_client_resolution={
            "connection_status": "blocked_scope",
            "pre_connection_stop_stage": "scope",
            "release_allowed": False,
            "default_client_used": False,
            "rejection_reasons": ["limited_composer_scope_not_allowed"],
        },
    )

    assert result.applied is False
    assert result.display_decision.observation_status == "unavailable"
    assert result.display_decision.comment_text == ""
    assert "composer_resolution_blocked_scope" in result.blocked_reasons
    assert "limited_composer_scope_not_allowed" in result.blocked_reasons
    contract = _contract_from_step10(result.as_meta())
    assert contract["repair_route_allowed"] is False
    assert contract["blocked_by_scope"] is True
    assert contract["final_observation_status"] == "unavailable"
    assert contract["public_contract"]["public_status_extended"] is False
    assert contract["gate_policy"]["display_gate_relaxed"] is False
    assert_low_information_public_repair_contract_meta_only(contract)

def test_phase18_4_non_repairable_ai_generated_candidate_is_not_promoted_to_low_information() -> None:
    failed_candidate = ConversationComposerCandidate(
        comment_text="あなたはいつも環境で疲れているのでしょう。",
        composer_source="ai_generated",
        status="generated",
        ai_generated=True,
        trace_id="phase18-low-info-non-repairable-ai",
        rejection_reasons=["unsupported_sentence"],
    )

    result = integrate_observation_display_repair(
        current_input={"memo": "環境を変えたいけど変えられなくて疲れた", "memo_action": "", "emotions": ["疲れ"]},
        subscription_tier="free",
        safety_report=SafetyBoundaryReport(),
        trace_id="phase18-low-info-non-repairable-ai",
        original_display_decision=_rejected_display("relation_confidence_low", "unsupported_sentence"),
        original_reader_report=_reader("relation_confidence_low"),
        original_grounding_report=_grounding("unsupported_sentence"),
        original_template_echo_report=TemplateEchoReport(passed=True),
        original_composer_source="ai_generated",
        original_composer_candidate=failed_candidate,
    )

    assert result.applied is False
    assert result.display_decision.observation_status == "rejected"
    contract = _contract_from_step10(result.as_meta())
    assert contract["repair_route_allowed"] is False
    assert contract["blocked_by_non_repairable_ai_candidate"] is True
    assert contract["final_observation_status"] == "rejected"
    assert contract["public_contract"]["rn_visible_contract_changed"] is False
    assert contract["gate_policy"]["grounding_gate_relaxed"] is False
    assert_low_information_public_repair_contract_meta_only(contract)
