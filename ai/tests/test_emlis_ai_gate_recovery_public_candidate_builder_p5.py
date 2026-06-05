# -*- coding: utf-8 -*-
from __future__ import annotations

"""P5 public candidate builder tests.

P5 adds the builder/result contract only. It must not build Gate Recovery text,
must not serialize raw input/body text into meta, and must only allow candidates
with explicit public-source lineage through the P2 boundary.
"""

from typing import Any, Mapping, Sequence

from emlis_ai_gate_recovery_public_candidate_builder import (
    GATE_RECOVERY_PUBLIC_CANDIDATE_BUILDER_META_KEY,
    PUBLIC_RECOVERY_CANDIDATE_BUILDER_SCHEMA_VERSION,
    assert_public_recovery_candidate_result_meta,
    build_public_candidate_after_gate_recovery,
)
from emlis_ai_gate_recovery_public_constants import (
    BLOCKER_BOUNDED_RECOVERY_PUBLIC_CANDIDATE_MISSING,
    BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK,
    CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE,
    CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER,
    CANDIDATE_SOURCE_KIND_SELF_DENIAL_SAFE_STATE_ANSWER,
    GATE_RECOVERY_MATERIAL_SURFACE_GENERATION_METHOD,
    GATE_RECOVERY_MATERIAL_SURFACE_MODEL,
    PUBLIC_SURFACE_ROLE_DIAGNOSTIC_RECOVERY,
    PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
)
from emlis_ai_gate_recovery_loop import recover_emlis_gate_failure
from emlis_ai_types import (
    ConversationComposerCandidate,
    DisplayDecision,
    GroundingReport,
    ListenerReaderReport,
    SafetyBoundaryReport,
    TemplateEchoReport,
)


def _display_decision() -> DisplayDecision:
    return DisplayDecision(
        observation_status="rejected",
        comment_text="",
        rejection_reasons=["surface_relation_skeleton_major"],
        trace_id="p5-public-candidate-builder",
    )


def _result(**kwargs: Any):
    defaults = {
        "current_input": {"memo": "このraw入力はP5 metaへ保存しない。"},
        "material_route": {"material_quality": "eligible"},
        "original_composer_candidate": None,
        "original_display_decision": _display_decision(),
        "safety_triage_kind": "safe_observation",
        "safety_report": None,
        "recovery_plan": {},
        "trace_id": "p5-public-candidate-builder",
    }
    defaults.update(kwargs)
    return build_public_candidate_after_gate_recovery(**defaults)


def _assert_meta_body_free(meta: Mapping[str, Any]) -> None:
    text_keys = {
        "raw_input",
        "current_input",
        "memo",
        "comment_text",
        "candidate_comment_text",
        "public_comment_text",
        "body",
        "text",
        "candidate_body",
    }

    def walk(value: Any) -> None:
        if isinstance(value, Mapping):
            assert not (set(value.keys()) & text_keys)
            for item in value.values():
                walk(item)
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            for item in value:
                walk(item)

    walk(meta)


def _assert_result_meta(meta: Mapping[str, Any]) -> None:
    _assert_meta_body_free(meta)
    assert meta["schema_version"] == PUBLIC_RECOVERY_CANDIDATE_BUILDER_SCHEMA_VERSION
    assert meta["contract_flags"]["raw_input_included"] is False
    assert meta["contract_flags"]["comment_text_body_included"] is False
    assert_public_recovery_candidate_result_meta(meta)


def test_p5_returns_blocked_result_when_no_allowed_public_candidate_exists() -> None:
    result = _result(
        recovery_plan={
            "target_public_candidate_source": CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER,
            "fallback_public_candidate_source_order": [
                CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER,
                CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE,
            ],
        }
    )

    assert result.candidate is None
    assert result.public_display_allowed is False
    assert BLOCKER_BOUNDED_RECOVERY_PUBLIC_CANDIDATE_MISSING in result.blocked_reasons
    meta = result.as_meta()
    assert meta["candidate_available"] is False
    assert meta["selection_kind"] == "no_public_candidate"
    _assert_result_meta(meta)


def test_p5_allows_low_information_candidate_without_body_in_meta() -> None:
    body = "まだ詳しい出来事までは見えませんが、不安の重さは軽く流せるものではなさそうです。詳しく残せそうなら、何があったか残してみませんか。"
    low_info_candidate = ConversationComposerCandidate(
        comment_text=body,
        composer_source="low_information_observation_composer",
        status="generated",
        composer_model="low_information_observation_composer_recovery",
        generation_method="low_information_observation_recovery_after_gate_recovery",
        composer_meta={
            "body": body,
            "line_metas": [
                {"line_id": "receive", "text": body[:10]},
                {"line_id": "known", "candidate_body": body},
            ],
            "candidate_source_kind": CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER,
            "public_surface_role": PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
    )
    result = _result(
        recovery_plan={
            "target_public_candidate_source": CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER,
        },
        low_information_candidate=low_info_candidate,
    )

    assert result.candidate is not None
    assert result.public_display_allowed is True
    assert result.source_kind == CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER
    assert result.candidate.comment_text == body
    assert result.candidate.composer_meta["candidate_source_kind"] == CANDIDATE_SOURCE_KIND_LOW_INFORMATION_OBSERVATION_COMPOSER
    assert result.candidate.composer_meta["public_surface_role"] == PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION
    assert result.candidate.composer_meta["candidate_lineage"]["public_candidate_rebuilt_after_recovery"] is True
    _assert_meta_body_free(result.candidate.composer_meta)
    _assert_result_meta(result.as_meta())


def test_p5_blocks_gate_recovery_material_candidate_even_when_passed_as_bounded_candidate() -> None:
    diagnostic = ConversationComposerCandidate(
        comment_text="今回の入力では、という本文はP5で採用しない。",
        composer_source="ai_generated",
        status="generated",
        composer_model=GATE_RECOVERY_MATERIAL_SURFACE_MODEL,
        generation_method=GATE_RECOVERY_MATERIAL_SURFACE_GENERATION_METHOD,
        composer_meta={
            "candidate_source_kind": "gate_recovery_material_surface",
            "public_surface_role": PUBLIC_SURFACE_ROLE_DIAGNOSTIC_RECOVERY,
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
    )

    result = _result(
        recovery_plan={
            "target_public_candidate_source": CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE,
        },
        bounded_repaired_original_candidate=diagnostic,
    )

    assert result.candidate is None
    assert result.public_display_allowed is False
    assert BLOCKER_GATE_RECOVERY_MATERIAL_SURFACE_PUBLIC_LEAK in result.blocked_reasons
    _assert_result_meta(result.as_meta())


def test_p5_allows_explicitly_rebuilt_original_candidate() -> None:
    original = ConversationComposerCandidate(
        comment_text="Emlisです。ここでは、予定変更に対して気持ちが追いつかないまま残っているところが見えます。",
        composer_source="limited_composer",
        status="generated",
        composer_model="bounded_repaired_original_candidate_v1",
        generation_method="bounded_repair_after_gate_recovery",
        composer_meta={
            "candidate_source_kind": CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE,
            "public_surface_role": PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
            "candidate_lineage": {
                "original_candidate_present": True,
                "original_candidate_source": "limited_composer",
                "recovery_plan_used": True,
                "diagnostic_surface_used": True,
                "public_candidate_rebuilt_after_recovery": True,
            },
        },
    )

    result = _result(
        original_composer_candidate=original,
        recovery_plan={
            "target_public_candidate_source": CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE,
        },
    )

    assert result.candidate is not None
    assert result.public_display_allowed is True
    assert result.source_kind == CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE
    assert result.candidate.comment_text == original.comment_text
    _assert_result_meta(result.as_meta())


def test_p5_allows_explicit_self_denial_safe_state_answer_candidate_only_with_triage() -> None:
    safe_candidate = ConversationComposerCandidate(
        comment_text="Emlisです。ここでは、自分を決めつけるより先に、いま苦しさが強くなっている状態として受け取ります。",
        composer_source="self_denial_safe_state_answer",
        status="generated",
        composer_model="self_denial_safe_state_answer_recovery",
        generation_method="self_denial_safe_state_answer_after_gate_recovery",
        composer_meta={
            "candidate_source_kind": CANDIDATE_SOURCE_KIND_SELF_DENIAL_SAFE_STATE_ANSWER,
            "public_surface_role": PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
        },
    )

    blocked = _result(
        safety_triage_kind="safe_observation",
        recovery_plan={
            "target_public_candidate_source": CANDIDATE_SOURCE_KIND_SELF_DENIAL_SAFE_STATE_ANSWER,
        },
        self_denial_safe_state_answer_candidate=safe_candidate,
    )
    allowed = _result(
        safety_triage_kind=CANDIDATE_SOURCE_KIND_SELF_DENIAL_SAFE_STATE_ANSWER,
        recovery_plan={
            "target_public_candidate_source": CANDIDATE_SOURCE_KIND_SELF_DENIAL_SAFE_STATE_ANSWER,
        },
        self_denial_safe_state_answer_candidate=safe_candidate,
    )

    assert blocked.candidate is None
    assert BLOCKER_BOUNDED_RECOVERY_PUBLIC_CANDIDATE_MISSING in blocked.blocked_reasons
    assert allowed.candidate is not None
    assert allowed.public_display_allowed is True
    assert allowed.source_kind == CANDIDATE_SOURCE_KIND_SELF_DENIAL_SAFE_STATE_ANSWER
    _assert_result_meta(allowed.as_meta())

from emlis_ai_gate_recovery_loop import recover_emlis_gate_failure
from emlis_ai_gate_recovery_public_candidate_builder import GATE_RECOVERY_PUBLIC_CANDIDATE_BUILDER_META_KEY
from emlis_ai_types import GroundingReport, ListenerReaderReport, SafetyBoundaryReport, TemplateEchoReport


class _MaterialRoute:
    material_quality = "eligible"
    visible_material_slots = ("relationship", "action", "emotion_direction")
    unknown_slots = ("cause",)
    generic_relation_material_ids = ("relationship_material",)

    def as_meta(self) -> dict[str, object]:
        return {
            "material_quality": self.material_quality,
            "visible_material_slots": list(self.visible_material_slots),
            "unknown_slots": list(self.unknown_slots),
            "generic_relation_material_ids": list(self.generic_relation_material_ids),
            "safety_triage_kind": "safe_observation",
        }


def _reader_report() -> ListenerReaderReport:
    return ListenerReaderReport(
        understandable=False,
        addressee_clear=False,
        speaker_integrity_ok=True,
        conversational=False,
        report_like=True,
        rejection_reasons=["original_gate_failed"],
    )


def test_p5_gate_recovery_loop_attaches_public_candidate_builder_meta() -> None:
    result = recover_emlis_gate_failure(
        current_input={
            "memo": "public candidate builder metaに本文を保存しない入力",
            "emotions": ["平穏", "不安"],
            "category": ["生活"],
        },
        display_decision=_display_decision(),
        reader_report=_reader_report(),
        grounding_report=GroundingReport(passed=False, rejection_reasons=["graph_evidence_not_used"]),
        template_echo_report=TemplateEchoReport(passed=False, rejection_reasons=["phase8_repeated_sentence_tail"]),
        material_route=_MaterialRoute(),
        safety_triage_kind="safe_observation",
        safety_report=SafetyBoundaryReport(requires_block=False),
        trace_id="p5-loop-meta",
    )

    assert result.applied is False
    meta = dict(result.surface_binding_meta.get(GATE_RECOVERY_PUBLIC_CANDIDATE_BUILDER_META_KEY) or {})
    assert meta["schema_version"] == PUBLIC_RECOVERY_CANDIDATE_BUILDER_SCHEMA_VERSION
    assert meta["candidate_available"] is False
    assert BLOCKER_BOUNDED_RECOVERY_PUBLIC_CANDIDATE_MISSING in meta["blocked_reasons"]
    assert meta["contract_flags"]["raw_input_included"] is False
    assert meta["contract_flags"]["comment_text_body_included"] is False
    assert_public_recovery_candidate_result_meta(meta)


class _MaterialRoute:
    material_quality = "eligible"
    visible_material_slots = ("event", "action", "emotion_direction")
    unknown_slots = ("cause",)
    generic_relation_material_ids = ("current_input_material",)

    def as_meta(self) -> dict[str, Any]:
        return {
            "material_quality": self.material_quality,
            "visible_material_slots": list(self.visible_material_slots),
            "unknown_slots": list(self.unknown_slots),
            "generic_relation_material_ids": list(self.generic_relation_material_ids),
            "safety_triage_kind": "safe_observation",
        }


def test_p5_gate_recovery_loop_attaches_builder_meta_without_promoting_material_surface() -> None:
    result = recover_emlis_gate_failure(
        current_input={
            "memo": "このraw入力はP5 builder metaに保存しない。",
            "memo_action": "行動本文も保存しない。",
            "emotions": ["不安"],
            "category": ["仕事"],
        },
        display_decision=_display_decision(),
        reader_report=ListenerReaderReport(
            understandable=False,
            addressee_clear=False,
            speaker_integrity_ok=True,
            conversational=False,
            report_like=True,
            rejection_reasons=["original_gate_failed"],
        ),
        grounding_report=GroundingReport(passed=False, rejection_reasons=["graph_evidence_not_used"]),
        template_echo_report=TemplateEchoReport(passed=False, rejection_reasons=["surface_relation_skeleton_major"]),
        material_route=_MaterialRoute(),
        safety_triage_kind="safe_observation",
        safety_report=SafetyBoundaryReport(requires_block=False),
        trace_id="p5-loop-builder-meta",
    )

    assert result.applied is False
    assert result.composer_candidate is None
    assert GATE_RECOVERY_PUBLIC_CANDIDATE_BUILDER_META_KEY in result.surface_binding_meta
    builder_meta = result.surface_binding_meta[GATE_RECOVERY_PUBLIC_CANDIDATE_BUILDER_META_KEY]
    assert builder_meta["candidate_available"] is False
    assert builder_meta["selection_kind"] == "no_public_candidate"
    assert BLOCKER_BOUNDED_RECOVERY_PUBLIC_CANDIDATE_MISSING in result.blocked_reasons
    _assert_result_meta(builder_meta)
