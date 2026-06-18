from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "services" / "ai_inference"))

from emlis_ai_limited_composer_e2e_contract import build_limited_composer_e2e_display_contract


SAMPLE_MEMO = """
ずっと家にいて、リラックスできて自分のことを優先して色々整えたりお家のことも出来るから嬉しいんだけど、ふっと気が抜けたときに現実と向き合うことがあるからその時にダメージでかい。
今の生活不便だな、と。
気をつけなきゃ行けないこと、全部無視して普通に生活したい。でもそうしたらもっと悪化する。
そんなの分かってる。たまに逃げ出したくなる。
"""

PASSING_TEXT = (
    "Mashさん、Emlisです。\n"
    "リラックスできて自分のことを優先できる嬉しさと、現実と向き合うダメージが同じ場所で重なっています。\n"
    "気をつけなきゃ行けないことを分かりながら普通に生活したい願いも離れていない中で、たまに逃げ出したくなる言葉は今の生活不便だなと感じる重さとつながっています。"
)

SCOPED_PASSING_TEXT = (
    "Mashさん、Emlisです。\n"
    "今回の入力では、リラックスできて自分のことを優先できる嬉しさと、現実と向き合うダメージが同じ場所で重なっています。\n"
    "気をつけなきゃ行けないことを分かりながら普通に生活したい願いも離れていない中で、たまに逃げ出したくなる言葉は今の生活不便だなと感じる重さとつながっています。"
)

UNSUPPORTED_TEXT = (
    "Mashさん、Emlisです。\n"
    "世界のすべてが明日から完全に良くなります。"
)

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
    "COCOLON_EMLIS_LIMITED_COMPOSER_INTERNAL_USER_IDS",
    "COCOLON_EMLIS_AI_LIMITED_COMPOSER_INTERNAL_USER_IDS",
    "EMLIS_AI_LIMITED_COMPOSER_INTERNAL_USER_IDS",
)


def _clear_limited_composer_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in _LIMITED_COMPOSER_ENV_KEYS:
        monkeypatch.delenv(name, raising=False)


def _input(memo: str = SAMPLE_MEMO) -> dict:
    return {
        "id": "step10-e2e-input",
        "created_at": "2026-05-15T00:00:00Z",
        "memo": memo,
        "memo_action": "",
        "emotion_details": [{"type": "自己理解", "strength": "medium"}],
        "emotions": ["自己理解"],
        "category": ["生活"],
    }


def _body_lines(text: str) -> list[str]:
    return [line.strip() for line in str(text or "").splitlines()[1:] if line.strip()]


def _public_meta_keys(value) -> set[str]:
    if isinstance(value, dict):
        keys: set[str] = set()
        for key, nested in value.items():
            keys.add(str(key))
            keys.update(_public_meta_keys(nested))
        return keys
    if isinstance(value, list):
        keys: set[str] = set()
        for item in value:
            keys.update(_public_meta_keys(item))
        return keys
    return set()


def _public_meta_values_for_key(value, target_key: str) -> list[object]:
    values: list[object] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            if str(key) == target_key:
                values.append(nested)
            values.extend(_public_meta_values_for_key(nested, target_key))
    elif isinstance(value, list):
        for item in value:
            values.extend(_public_meta_values_for_key(item, target_key))
    return values


class _BoundPassingComposer:
    composer_model = "step10_e2e_bound_passing_composer.v1"

    def generate(self, payload):
        evidence_ids = [item["span_id"] for item in payload["evidence_spans"][:2]]
        return {
            "response_schema_version": "emlis.composer.response.v1",
            "composer_source": "ai_generated",
            "composer_model": self.composer_model,
            "generation_method": "step10_e2e_test_composer",
            "generation_scope": "scoped_graph_only",
            "coverage_scope": "current_input_core",
            "fixed_string_renderer_used": False,
            "confidence": 0.91,
            "comment_text": PASSING_TEXT,
            "used_evidence_span_ids": evidence_ids,
            "composer_meta": {
                "profile_key": "mixed_positive_anxiety",
                "sentence_binding_bundle": {
                    "version": "emlis.sentence_binding_bundle.test.v1",
                    "binding_version": "step10.test.binding.v1",
                    "binding_count": 2,
                    "coverage_scope": "current_input_core",
                    "profile_key": "mixed_positive_anxiety",
                    "relation_taxonomy_version": "step10.test.relation_taxonomy.v1",
                    "bindings": [
                        {
                            "sentence_id": "s1",
                            "text": "binding text must not be copied into diagnostic rows",
                            "line_role": "coexistence",
                            "relation_type": "coexistence",
                            "used_evidence_span_ids": evidence_ids[:1],
                            "used_phrase_unit_ids": ["pu_positive", "pu_impact"],
                            "coverage_scope": "current_input_core",
                            "must_include": True,
                        },
                        {
                            "sentence_id": "s2",
                            "text": "binding text must not be copied into diagnostic rows either",
                            "line_role": "limit_escape",
                            "relation_type": "approach_avoidance",
                            "used_evidence_span_ids": evidence_ids[1:2],
                            "used_phrase_unit_ids": ["pu_limit", "pu_escape"],
                            "coverage_scope": "current_input_core",
                            "must_include": True,
                        },
                    ],
                },
            },
        }


class _UnsupportedComposer:
    composer_model = "step10_e2e_unsupported_composer.v1"

    def generate(self, payload):
        return {
            "response_schema_version": "emlis.composer.response.v1",
            "composer_source": "ai_generated",
            "composer_model": self.composer_model,
            "generation_method": "step10_e2e_test_composer",
            "generation_scope": "scoped_graph_only",
            "coverage_scope": "current_input_core",
            "fixed_string_renderer_used": False,
            "confidence": 0.91,
            "comment_text": UNSUPPORTED_TEXT,
            "used_evidence_span_ids": [item["span_id"] for item in payload["evidence_spans"][:1]],
        }


def _assert_step10_contract_attached(reply, *, expected_status: str) -> dict:
    summary = reply.meta["diagnostic_summary"]
    step10 = summary["step10_e2e_display_contract"]
    display_trace = reply.meta["multi_perspective"]["gate_trace"]["display_gate"]
    phase_gate = reply.meta["multi_perspective"]["phase_gate"]

    assert step10["version"] == "emlis.limited_composer_e2e_display_contract.v1"
    assert step10["step"] == "10_E2E_test_fixed"
    assert step10["contract_name"] == "input_feedback.comment_text_passed_only"
    assert step10 == summary["limited_composer_e2e_display_contract"]
    assert step10 == summary["e2e_display_contract"]
    assert step10 == reply.meta["step10_e2e_display_contract"]
    assert step10 == reply.meta["limited_composer_e2e_display_contract"]
    assert step10 == reply.meta["e2e_display_contract"]
    assert step10 == reply.meta["multi_perspective"]["step10_e2e_display_contract"]

    assert step10["observation_status"] == expected_status
    assert step10["contract_passed"] is True
    assert step10["passed_only_contract_passed"] is True
    assert step10["limited_extension_exit_gate_step10_passed"] is True
    assert step10["release_blockers"] == []
    assert step10["diagnostic_summary_present"] is True
    assert step10["gate_results_present"] is True
    assert step10["scorecard_harness_present"] is True
    assert step10["raw_input_included"] is False
    assert step10["raw_input_required_for_debug"] is False
    assert step10["input_specific_template_added"] is False
    assert step10["fixed_completion_template_added"] is False
    assert step10["display_gate_relaxed"] is False
    assert step10["reader_grounding_template_relaxed"] is False
    assert step10["db_api_rename_performed"] is False
    assert step10["response_key_rename_performed"] is False

    assert phase_gate["step10_e2e_display_contract_ready"] is True
    assert phase_gate["e2e_display_contract_ready"] is True
    assert phase_gate["step10_e2e_release_blockers"] == []
    assert phase_gate["step10_passed_only_contract"] == "input_feedback.comment_text_passed_only"
    assert summary["observation_status"] == expected_status
    assert display_trace["observation_status"] == expected_status
    assert bool(reply.comment_text.strip()) is (expected_status == "passed")
    assert summary["comment_text_allowed"] is (expected_status == "passed")
    assert display_trace["comment_text_allowed"] is (expected_status == "passed")
    assert summary["gate_results"]["display"]["diagnostics"]["comment_text_allowed"] is (expected_status == "passed")
    assert reply.meta["fallback_used"] is False
    assert reply.meta["multi_perspective"]["legacy_safe_fallback_used"] is False
    assert reply.meta["multi_perspective"]["legacy_input_feedback_template_used"] is False

    for gate_name in ("reader", "grounding", "template_echo", "display"):
        gate = summary["gate_results"][gate_name]
        assert isinstance(gate["passed"], bool)
        assert isinstance(gate["rejection_reasons"], list)
        assert isinstance(gate["primary_reason"], str)

    return step10


def _build_public_input_feedback_payload(reply) -> dict | None:
    from emlis_ai_public_feedback_meta import (
        build_public_emlis_input_feedback_meta,
        should_include_public_input_feedback,
    )

    public_meta = build_public_emlis_input_feedback_meta(
        reply.meta,
        comment_text_present=bool(str(reply.comment_text or "").strip()),
        subscription_tier="free",
    )
    if not should_include_public_input_feedback(reply.comment_text, public_meta):
        return None
    return {
        "comment_text": reply.comment_text,
        "emlis_ai": public_meta,
    }


def _assert_public_input_feedback_meta_body_free(
    input_feedback_payload: dict,
    *forbidden_texts: str,
) -> None:
    public_meta = input_feedback_payload["emlis_ai"]
    boundary = public_meta["public_feedback_meta_boundary"]
    assert boundary["sanitized"] is True
    assert boundary["internal_meta_returned"] is False
    assert boundary["raw_input_included"] is False
    assert boundary["comment_text_included"] is False
    assert boundary["comment_text_body_included"] is False
    assert boundary["candidate_body_included"] is False

    public_keys = _public_meta_keys(public_meta)
    for forbidden_key in (
        "comment_text",
        "composer_candidate",
        "current_input",
        "environment_state_output_scope_marker_completion",
        "environment_state_output_surface_contract",
        "internal_completion_result",
        "multi_perspective",
        "raw_input",
        "text",
        "body",
        "candidate_comment_text",
        "public_comment_text",
        "realized_text",
    ):
        assert forbidden_key not in public_keys

    for leak_flag in (
        "internal_meta_returned",
        "raw_input_included",
        "raw_text_included",
        "input_text_included",
        "comment_text_included",
        "comment_text_body_included",
        "candidate_body_included",
        "surface_body_included",
    ):
        assert all(
            value is False
            for value in _public_meta_values_for_key(public_meta, leak_flag)
        )

    serialized_public_meta = json.dumps(public_meta, ensure_ascii=False, sort_keys=True)
    for forbidden_text in forbidden_texts:
        if forbidden_text:
            assert forbidden_text not in serialized_public_meta


def test_step10_e2e_contract_marks_non_passed_text_exposure_as_blocker() -> None:
    contract = build_limited_composer_e2e_display_contract(
        observation_status="rejected",
        comment_text="表示してはいけない本文",
        diagnostic_summary={
            "observation_status": "rejected",
            "comment_text_allowed": False,
            "gate_results": {"display": {"passed": False, "diagnostics": {"comment_text_allowed": False}}},
        },
    )

    assert contract["contract_passed"] is False
    assert "non_passed_comment_text_exposed" in contract["release_blockers"]
    assert contract["raw_input_included"] is False
    assert contract["display_gate_relaxed"] is False


@pytest.mark.asyncio
async def test_step10_e2e_passed_candidate_exposes_comment_text_only_after_display_gate(monkeypatch):
    _clear_limited_composer_env(monkeypatch)
    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="step10-e2e-passed-user",
        subscription_tier="free",
        current_input=_input(),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
        composer_client=_BoundPassingComposer(),
    )

    step10 = _assert_step10_contract_attached(reply, expected_status="passed")
    summary = reply.meta["diagnostic_summary"]
    display_trace = reply.meta["multi_perspective"]["gate_trace"]["display_gate"]

    candidate = reply.meta["multi_perspective"]["composer_candidate"]
    completion = candidate["composer_meta"]["environment_state_output_scope_marker_completion"]

    assert reply.comment_text == SCOPED_PASSING_TEXT
    assert completion["applied"] is True
    assert completion["display_gate_relaxed"] is False
    assert summary["primary_reason"] == "passed"
    assert display_trace["passed"] is True
    assert display_trace["comment_text_present"] is True
    assert step10["comment_text_present"] is True
    assert step10["comment_text_exposed"] is True
    assert step10["display_gate_passed"] is True
    assert step10["passed_comment_text_visible"] is True
    assert step10["non_passed_comment_text_suppressed"] is False
    assert step10["binding_present"] is True
    assert step10["binding_missing"] is False
    assert step10["binding_count"] == len(_body_lines(PASSING_TEXT))
    assert step10["expected_binding_count"] == len(_body_lines(PASSING_TEXT))
    assert step10["relation_taxonomy_present"] is True


@pytest.mark.asyncio
async def test_phase5_passed_candidate_keeps_public_meta_sanitized(monkeypatch):
    _clear_limited_composer_env(monkeypatch)
    from emlis_ai_public_feedback_meta import (
        build_public_emlis_input_feedback_meta,
        should_include_public_input_feedback,
    )
    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="phase5-public-meta-boundary-passed-user",
        subscription_tier="free",
        current_input=_input(),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
        composer_client=_BoundPassingComposer(),
    )

    public_meta = build_public_emlis_input_feedback_meta(
        reply.meta,
        comment_text_present=bool(str(reply.comment_text or "").strip()),
        subscription_tier="free",
    )
    input_feedback_payload = None
    if should_include_public_input_feedback(reply.comment_text, public_meta):
        input_feedback_payload = {
            "comment_text": reply.comment_text,
            "emlis_ai": public_meta,
        }

    assert reply.comment_text == SCOPED_PASSING_TEXT
    assert input_feedback_payload is not None
    assert input_feedback_payload["comment_text"] == SCOPED_PASSING_TEXT
    assert input_feedback_payload["emlis_ai"]["observation_status"] == "passed"

    boundary = input_feedback_payload["emlis_ai"]["public_feedback_meta_boundary"]
    assert boundary["sanitized"] is True
    assert boundary["internal_meta_returned"] is False
    assert boundary["raw_input_included"] is False
    assert boundary["comment_text_included"] is False

    public_keys = _public_meta_keys(input_feedback_payload["emlis_ai"])
    for forbidden_key in (
        "comment_text",
        "composer_candidate",
        "current_input",
        "environment_state_output_scope_marker_completion",
        "environment_state_output_surface_contract",
        "internal_completion_result",
        "multi_perspective",
        "raw_input",
        "text",
        "body",
        "candidate_comment_text",
        "public_comment_text",
        "realized_text",
    ):
        assert forbidden_key not in public_keys

    for leak_flag in (
        "internal_meta_returned",
        "raw_input_included",
        "raw_text_included",
        "input_text_included",
        "comment_text_included",
        "comment_text_body_included",
        "candidate_body_included",
        "surface_body_included",
    ):
        assert all(
            value is False
            for value in _public_meta_values_for_key(input_feedback_payload["emlis_ai"], leak_flag)
        )

    serialized_public_meta = json.dumps(
        input_feedback_payload["emlis_ai"],
        ensure_ascii=False,
        sort_keys=True,
    )
    assert SCOPED_PASSING_TEXT not in serialized_public_meta
    assert PASSING_TEXT not in serialized_public_meta
    assert "全部無視して普通に生活したい" not in serialized_public_meta
    assert "binding text must not be copied into diagnostic rows" not in serialized_public_meta


@pytest.mark.asyncio
async def test_step10_e2e_rejected_candidate_recovers_without_exposing_generated_body(monkeypatch):
    _clear_limited_composer_env(monkeypatch)
    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="step10-e2e-rejected-user",
        subscription_tier="free",
        current_input=_input(),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
        composer_client=_UnsupportedComposer(),
    )

    step10 = _assert_step10_contract_attached(reply, expected_status="passed")
    summary = reply.meta["diagnostic_summary"]
    display_trace = reply.meta["multi_perspective"]["gate_trace"]["display_gate"]
    candidate = reply.meta["multi_perspective"]["composer_candidate"]
    composer_meta = candidate["composer_meta"]
    input_feedback_payload = _build_public_input_feedback_payload(reply)

    assert input_feedback_payload is not None
    assert input_feedback_payload["comment_text"] == reply.comment_text
    assert reply.comment_text.strip()
    assert UNSUPPORTED_TEXT not in reply.comment_text
    assert "世界のすべてが明日から完全に良くなります" not in reply.comment_text

    assert summary["stage"] == "display"
    assert summary["primary_reason"] == "passed"
    assert display_trace["passed"] is True
    assert display_trace["comment_text_present"] is True
    assert step10["comment_text_present"] is True
    assert step10["comment_text_exposed"] is True
    assert step10["display_gate_passed"] is True
    assert step10["passed_comment_text_visible"] is True
    assert step10["non_passed_comment_text_suppressed"] is False

    assert candidate["composer_model"] == "labelled_two_stage_surface_recomposition_v1"
    assert composer_meta["candidate_source_kind"] == "labelled_two_stage_surface_recomposition_candidate"
    assert composer_meta["public_surface_role"] == "public_observation_candidate"
    assert composer_meta["original_candidate_present"] is True
    assert composer_meta["original_candidate_source_kind"] == "ai_generated"
    assert composer_meta["original_candidate_status"] == "generated"
    assert composer_meta["original_display_status"] == "rejected"
    assert composer_meta["original_surface_plain_or_unlabelled"] is True
    assert composer_meta["original_surface_labelled_two_stage"] is False
    assert composer_meta["labelled_two_stage_surface_recomposition_used"] is True
    assert composer_meta["normal_observation_rebuild_used"] is False
    assert composer_meta["complete_initial_surface_recomposition_used"] is False
    assert composer_meta["gate_recovery_material_surface_used"] is False
    assert composer_meta["raw_input_included"] is False
    assert composer_meta["comment_text_body_included"] is False

    public_lineage = input_feedback_payload["emlis_ai"]["public_surface_lineage"]
    assert public_lineage["candidate_source_kind"] == "labelled_two_stage_surface_recomposition_candidate"
    assert public_lineage["public_candidate_source_allowed"] is True
    assert public_lineage["public_candidate_source_forbidden"] is False
    assert public_lineage["public_surface_role"] == "public_observation_candidate"
    assert public_lineage["labelled_two_stage_surface_recomposition_used"] is True
    assert public_lineage["complete_initial_surface_recomposition_used"] is False
    assert public_lineage["normal_observation_rebuild_used"] is False
    assert public_lineage["gate_recovery_material_surface_used_as_public_body"] is False
    assert public_lineage["diagnostic_recovery_surface_used_as_public_body"] is False
    assert public_lineage["body_free"] is True
    assert public_lineage["raw_input_included"] is False
    assert public_lineage["comment_text_body_included"] is False
    assert public_lineage["candidate_body_included"] is False

    _assert_public_input_feedback_meta_body_free(
        input_feedback_payload,
        reply.comment_text,
        UNSUPPORTED_TEXT,
        "世界のすべてが明日から完全に良くなります",
        "全部無視して普通に生活したい",
    )


@pytest.mark.asyncio
async def test_step10_e2e_pre_connection_recovery_exposes_safe_surface_without_body_leak(monkeypatch):
    _clear_limited_composer_env(monkeypatch)
    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="step10-e2e-unavailable-user",
        subscription_tier="free",
        current_input=_input(),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    step10 = _assert_step10_contract_attached(reply, expected_status="passed")
    summary = reply.meta["diagnostic_summary"]
    display_trace = reply.meta["multi_perspective"]["gate_trace"]["display_gate"]
    connection_visibility = summary["connection_visibility"]
    candidate = reply.meta["multi_perspective"]["composer_candidate"]
    composer_meta = candidate["composer_meta"]
    input_feedback_payload = _build_public_input_feedback_payload(reply)

    assert input_feedback_payload is not None
    assert input_feedback_payload["comment_text"] == reply.comment_text
    assert reply.comment_text.startswith("見えたこと：\n")
    assert "\n\nEmlisから：\n" in reply.comment_text

    assert summary["stage"] == "display"
    assert summary["primary_reason"] == "passed"
    assert connection_visibility["connection_status"] == "blocked_feature_flag"
    assert connection_visibility["pre_connection_stop"] is True
    assert connection_visibility["blocked_before_composer"] is True
    assert connection_visibility["composer_connection_attempted"] is False
    assert connection_visibility["composer_generation_attempted"] is False
    assert connection_visibility["primary_stage"] == "flag"
    assert connection_visibility["primary_reason"] == "default_limited_composer_feature_disabled"
    assert connection_visibility["release_enabled"] is False
    assert connection_visibility["release_reason_code"] == "feature_flag_disabled"

    assert display_trace["passed"] is True
    assert display_trace["comment_text_present"] is True
    assert step10["comment_text_present"] is True
    assert step10["comment_text_exposed"] is True
    assert step10["display_gate_passed"] is True
    assert step10["passed_comment_text_visible"] is True
    assert step10["non_passed_comment_text_suppressed"] is False

    # R6/R7: this case protects the split between the pre-public complete-initial
    # attempt and the final public labelled two-stage surface.  The old single
    # composer_model assertion treated complete-initial as final and hid RED-DC-002.
    assert candidate["composer_model"] == "labelled_two_stage_surface_recomposition_v1"
    assert composer_meta["candidate_source_kind"] == "labelled_two_stage_surface_recomposition_candidate"
    assert composer_meta["public_surface_role"] == "public_observation_candidate"
    assert composer_meta["original_candidate_present"] is True
    assert composer_meta["original_candidate_source_kind"] == "unavailable"
    assert composer_meta["root_candidate_source_kind"] == "unavailable"
    assert composer_meta["recovery_input_candidate_source_kind"] == "complete_initial_surface_recomposition_candidate"
    assert composer_meta["pre_public_candidate_source_kind"] == "complete_initial_surface_recomposition_candidate"
    assert composer_meta["selected_public_candidate_source_kind"] == "labelled_two_stage_surface_recomposition_candidate"
    assert composer_meta["final_public_candidate_source_kind"] == "labelled_two_stage_surface_recomposition_candidate"
    assert composer_meta["source_unavailable_recovered"] is False
    assert composer_meta["complete_initial_surface_recomposition_used"] is False
    assert composer_meta["labelled_two_stage_surface_recomposition_used"] is True
    assert composer_meta["normal_observation_rebuild_used"] is False
    assert composer_meta["gate_recovery_material_surface_used"] is False
    assert composer_meta["raw_input_included"] is False
    assert composer_meta["comment_text_body_included"] is False

    complete_initial_summary = summary["complete_initial_surface_recomposition_summary"]
    assert complete_initial_summary["attempted"] is True
    assert complete_initial_summary["candidate_generated"] is True
    assert complete_initial_summary["applied"] is False
    assert complete_initial_summary["candidate_adopted_after_existing_gates"] is False
    assert complete_initial_summary["passed_by_all_existing_gates"] is False
    assert "visible_surface_acceptance_gate_failed" in complete_initial_summary["existing_gate_chain"]["blocked_reasons"]
    assert complete_initial_summary["existing_gate_chain"]["visible_surface_acceptance_gate_passed"] is False
    assert complete_initial_summary["raw_input_included"] is False
    assert complete_initial_summary["comment_text_body_included"] is False

    body_free_lineage = composer_meta["body_free_public_source_lineage"]
    assert body_free_lineage["candidate_source_kind"] == "labelled_two_stage_surface_recomposition_candidate"
    assert body_free_lineage["recovery_input_candidate_source_kind"] == "complete_initial_surface_recomposition_candidate"
    assert body_free_lineage["pre_public_candidate_source_kind"] == "complete_initial_surface_recomposition_candidate"
    assert body_free_lineage["final_public_candidate_source_kind"] == "labelled_two_stage_surface_recomposition_candidate"
    assert body_free_lineage["complete_initial_surface_recomposition_attempted"] is True
    assert body_free_lineage["complete_initial_surface_recomposition_final_used"] is False
    assert body_free_lineage["labelled_two_stage_surface_recomposition_final_used"] is True
    assert body_free_lineage["lineage_consistency_passed"] is True
    assert body_free_lineage["body_free"] is True
    assert body_free_lineage["raw_input_included"] is False
    assert body_free_lineage["comment_text_body_included"] is False
    assert body_free_lineage["candidate_body_included"] is False

    public_lineage = input_feedback_payload["emlis_ai"]["public_surface_lineage"]
    assert public_lineage["candidate_source_kind"] == "labelled_two_stage_surface_recomposition_candidate"
    assert public_lineage["public_candidate_source_allowed"] is True
    assert public_lineage["public_candidate_source_forbidden"] is False
    assert public_lineage["public_surface_role"] == "public_observation_candidate"
    assert public_lineage["root_candidate_source_kind"] == "unavailable"
    assert public_lineage["recovery_input_candidate_source_kind"] == "complete_initial_surface_recomposition_candidate"
    assert public_lineage["pre_public_candidate_source_kind"] == "complete_initial_surface_recomposition_candidate"
    assert public_lineage["selected_public_candidate_source_kind"] == "labelled_two_stage_surface_recomposition_candidate"
    assert public_lineage["final_public_candidate_source_kind"] == "labelled_two_stage_surface_recomposition_candidate"
    assert public_lineage["lineage_consistency_passed"] is True
    assert public_lineage["complete_initial_surface_recomposition_attempted"] is True
    assert public_lineage["complete_initial_surface_recomposition_used"] is False
    assert public_lineage["complete_initial_surface_recomposition_final_used"] is False
    assert public_lineage["labelled_two_stage_surface_recomposition_used"] is True
    assert public_lineage["labelled_two_stage_surface_recomposition_final_used"] is True
    assert public_lineage["normal_observation_rebuild_used"] is False
    assert public_lineage["gate_recovery_material_surface_used_as_public_body"] is False
    assert public_lineage["diagnostic_recovery_surface_used_as_public_body"] is False
    assert public_lineage["body_free"] is True
    assert public_lineage["raw_input_included"] is False
    assert public_lineage["comment_text_body_included"] is False
    assert public_lineage["candidate_body_included"] is False

    _assert_public_input_feedback_meta_body_free(
        input_feedback_payload,
        reply.comment_text,
        "全部無視して普通に生活したい",
    )
