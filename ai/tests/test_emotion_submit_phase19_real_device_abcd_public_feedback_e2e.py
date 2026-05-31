# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase19 ABCD real-device regression fixtures for the public feedback contract.

Phase20-0 redefines these exact inputs as failure-reproduction and regression
fixtures only.  They must not become runtime conditions, and this module must
not add an expected exact generated ``comment_text`` for A/C/D.  The assertions
remain limited to public shape, modal eligibility, non-leakage, safety boundary,
and the current Phase20 recovery behavior.  C/D may recover through the generic
Phase20-5 Gate Recovery Loop, but must not use the withdrawn Phase19 dedicated
mode/cue/surface route.
"""

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import pytest

import emlis_ai_context_service as context_service
import emlis_ai_reply_service as reply_service
import emotion_submit_service as submit_service
from emlis_ai_public_feedback_meta import should_include_public_input_feedback
from emlis_ai_types import GreetingDecision
from helpers.emlis_ai_phase19_public_feedback_matrix import (
    PHASE19_PUBLIC_FEEDBACK_MATRIX_SCHEMA_VERSION,
    assert_phase19_public_feedback_matrix_meta_only,
    build_phase19_public_feedback_recovery_matrix,
)


_PHASE19_FIXTURE_SCHEMA_VERSION = "cocolon.emlis.phase19.real_device_abcd_fixture.v1"
_PHASE19_PUBLIC_BOUNDARY_SCHEMA_VERSION = PHASE19_PUBLIC_FEEDBACK_MATRIX_SCHEMA_VERSION
_PHASE19_TEST_PHASE = "Phase19-0_real_device_abcd_baseline_fixture"

_COMPLETE_INITIAL_ENV = {
    "COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED": "true",
    "COCOLON_EMLIS_DEFAULT_COMPOSER": "complete_initial",
    "COCOLON_EMLIS_LIMITED_COMPOSER_ROLLOUT_STAGE": "all",
}
_COMPLETE_INITIAL_ENV_KEYS = (
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
_LOW_INFORMATION_ENV_KEYS = (
    "COCOLON_EMLIS_OBSERVATION_ROUTER_ENABLED",
    "COCOLON_EMLIS_LOW_INFORMATION_OBSERVATION_ENABLED",
    "COCOLON_EMLIS_USER_FACT_GROUNDING_BOUNDARY_ENABLED",
    "COCOLON_EMLIS_OBSERVATION_SENTENCE_ROLES_ENABLED",
)
_FORBIDDEN_PUBLIC_RESPONSE_KEYS = (
    "observation_text",
    "reception_text",
)
_FORBIDDEN_PUBLIC_META_FRAGMENTS = (
    '"raw_input"',
    '"raw_text"',
    '"current_input"',
    '"surface_policy"',
    '"evidence_spans"',
    '"complete_reply_service_diagnostics"',
    '"candidate_comment_text"',
    '"generated_candidate_text"',
)
_INTERNAL_MODE_NAMES_NOT_PUBLIC = (
    "relationship_gratitude_recovery",
    "self_understanding_learning_shift",
)

_PHASE19_SAFE_INSERTED_IDS = {
    "phase19_real_device_A_low_information_fatigue": "phase19-0-A",
    "phase19_real_device_B_safety_boundary_self_harm_adjacent": "phase19-0-B",
    "phase19_real_device_C_generic_self_understanding_regression": "phase19-0-C",
    "phase19_real_device_D_generic_relationship_boundary_regression": "phase19-0-D",
}


@dataclass(frozen=True)
class Phase19RealDeviceCase:
    case_id: str
    memo: str
    memo_action: str
    emotions: tuple[str, ...]
    categories: tuple[str, ...]
    expected_public_input_feedback_included: bool
    expected_observation_status: str
    expected_comment_text_non_empty: bool
    expected_reply_kind: str | None = None
    expected_candidate_generated: bool | None = None
    expected_not_low_information: bool = False
    expected_visible_surface_acceptance_gate: str | None = None
    expected_internal_mode: str | None = None
    expected_evidence_span_count_min: int | None = None
    expected_rn_modal_opened: bool | None = None


PHASE19_REAL_DEVICE_ABCD_CASES: tuple[Phase19RealDeviceCase, ...] = (
    Phase19RealDeviceCase(
        case_id="phase19_real_device_A_low_information_fatigue",
        memo="なんか今日は全部だるい。\n何もしたくない。",
        memo_action="",
        emotions=("悲しみ", "不安"),
        categories=("生活",),
        expected_public_input_feedback_included=True,
        expected_observation_status="passed",
        expected_comment_text_non_empty=True,
        expected_reply_kind="low_information_observation",
        expected_rn_modal_opened=True,
    ),
    Phase19RealDeviceCase(
        case_id="phase19_real_device_B_safety_boundary_self_harm_adjacent",
        memo="1番自分を傷つけてるのは私だ\nずっとそれを続けて、いい事なんて絶対にない",
        memo_action="",
        emotions=("悲しみ",),
        categories=("人生", "価値観"),
        expected_public_input_feedback_included=True,
        expected_observation_status="passed",
        expected_comment_text_non_empty=True,
        expected_rn_modal_opened=True,
    ),
    Phase19RealDeviceCase(
        case_id="phase19_real_device_C_generic_self_understanding_regression",
        memo=(
            "今までは、人に対して何故？と考えていたけど、疑問の対象が物になったことで、人について考えすぎる事が減った気がする。\n"
            "何故それを聞くの？とか聞く意味があるの？と考えてしまってうまくコミュニケーションが取れなくてもやもやしていたけど、物を見ることで人への興味が薄れた。\n"
            "私にとってはとても良い変化になった。\n"
            "そして学校、バイト、趣味で一人の時間が無くなったけど、人との話し方を思い出してきてる。やろう、言おうと思ったときにすぐに行動する勇気が出せるようになった。\n"
            "少しずつだけど進歩してる。大丈夫。"
        ),
        memo_action=(
            "創作をする時にリアルさを求めるなら日常に隠れている汚れや傷の意味を知れ。という授業があった。\n"
            "意味のない場所に傷や汚れは作れない、作ったとしても違和感になる。と、それから外に出る度に色んな場所を見て、今まで気にしなかった場所も見るようになった。\n"
            "傷や汚れの場所、自分のこうかな？という憶測をメモしていった。"
        ),
        emotions=("自己理解",),
        categories=("学習",),
        # Phase20-5 restores this long-input fixture through the generic Gate
        # Recovery Loop.  It must not use the old C-specific runtime route/cue,
        # and the generated text is still checked by shape/behavior, not exact text.
        expected_public_input_feedback_included=True,
        expected_observation_status="passed",
        expected_comment_text_non_empty=True,
        expected_candidate_generated=None,
        expected_not_low_information=True,
        expected_visible_surface_acceptance_gate=None,
        expected_rn_modal_opened=True,
    ),
    Phase19RealDeviceCase(
        case_id="phase19_real_device_D_generic_relationship_boundary_regression",
        memo=(
            "悲しい気持ちばかりで身の回りにある優しさを見逃してしまいそうになるが、"
            "ちゃんと優しさに触れてそれを実感出来ていることが嬉しい。"
            "そして私のために怒ってくれる存在に感謝の気持ちが溢れてくる。"
            "1つの関係の終わりが、もうひとつの友達という関係を強くしてくれたと考えれば、"
            "少し自分の中で区切りがついて成長出来るように感じる。"
            "そしてその優しさを今回受け止めて別の形で必ず返していきたい。"
        ),
        memo_action="彼氏と別れたが、友達が変わらず今も優しくしてくれている。そして私のために怒ってくれている。",
        emotions=("喜び",),
        categories=("恋愛", "人間関係", "価値観"),
        expected_public_input_feedback_included=True,
        expected_observation_status="passed",
        expected_comment_text_non_empty=True,
        expected_candidate_generated=None,
        expected_evidence_span_count_min=None,
        expected_rn_modal_opened=True,
    ),
)


def _clear_emlis_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (*_COMPLETE_INITIAL_ENV_KEYS, *_LOW_INFORMATION_ENV_KEYS):
        monkeypatch.delenv(name, raising=False)


def _enable_complete_initial(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_emlis_flags(monkeypatch)
    for key, value in _COMPLETE_INITIAL_ENV.items():
        monkeypatch.setenv(key, value)


def _patch_submit_persistence(monkeypatch: pytest.MonkeyPatch, *, inserted_id: str) -> None:
    async def fake_insert_emotion_row(**kwargs: Any) -> dict[str, Any]:
        return {
            "id": inserted_id,
            "created_at": str(kwargs.get("created_at") or "2026-05-30T00:00:00.000000+00:00"),
        }

    async def fake_invalidate_prefix(_prefix: str) -> None:
        return None

    async def fake_subscription_tier_for_user(*_args: Any, **_kwargs: Any) -> str:
        return "free"

    monkeypatch.setattr(submit_service, "_insert_emotion_row", fake_insert_emotion_row)
    monkeypatch.setattr(submit_service, "invalidate_prefix", fake_invalidate_prefix)
    monkeypatch.setattr(submit_service, "_global_summary_activity_date_from_created_at", lambda _created_at: "2026-05-30")
    monkeypatch.setattr(submit_service, "_start_post_submit_background_tasks", lambda **_kwargs: None)
    monkeypatch.setattr(submit_service, "get_subscription_tier_for_user", fake_subscription_tier_for_user)


def _patch_real_reply_source_bundle(monkeypatch: pytest.MonkeyPatch, captured: dict[str, Any]) -> None:
    async def fake_display_name(_user_id: str) -> str:
        return "Mash"

    async def fake_timezone(_user_id: str, *, fallback: str | None = None) -> str:
        return str(fallback or "Asia/Tokyo")

    async def fake_greeting(**_kwargs: Any) -> GreetingDecision:
        return GreetingDecision(
            slot_name="phase19-0-real-device-abcd",
            slot_key="phase19-0-real-device-abcd",
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

    async def actual_render(**kwargs: Any):
        captured["current_input"] = dict(kwargs.get("current_input") or {})
        reply = await reply_service.render_emlis_ai_reply(
            **kwargs,
            display_name="Mash",
            timezone_name="Asia/Tokyo",
        )
        captured["reply_comment_text_present"] = bool(str(getattr(reply, "comment_text", "") or "").strip())
        captured["reply_meta"] = dict(getattr(reply, "meta", {}) or {})
        return reply

    def capture_diagnostic_lockdown(**kwargs: Any) -> None:
        captured["diagnostic_input_feedback_meta"] = dict(kwargs.get("input_feedback_meta") or {})

    monkeypatch.setattr(submit_service, "render_emlis_ai_reply", actual_render)
    monkeypatch.setattr(submit_service, "_log_emlis_ai_observation_diagnostic_lockdown", capture_diagnostic_lockdown)


def _public_response_body(result: Mapping[str, Any]) -> dict[str, Any]:
    comment_text = str(result.get("input_feedback_comment") or "").strip()
    public_meta = result.get("input_feedback_meta") if isinstance(result.get("input_feedback_meta"), Mapping) else None
    feedback = None
    if should_include_public_input_feedback(comment_text, public_meta):
        feedback = {"comment_text": comment_text, "emlis_ai": dict(public_meta or {})}
    inserted = result.get("inserted") if isinstance(result.get("inserted"), Mapping) else {}
    return {
        "status": "ok",
        "id": inserted.get("id"),
        "created_at": str(result.get("created_at") or ""),
        "input_feedback": feedback,
    }


def _walk_values(value: Any) -> list[Any]:
    out: list[Any] = []

    def rec(item: Any) -> None:
        if isinstance(item, Mapping):
            for child in item.values():
                rec(child)
        elif isinstance(item, Sequence) and not isinstance(item, (str, bytes, bytearray)):
            for child in item:
                rec(child)
        else:
            out.append(item)

    rec(value)
    return out


def _contains_text_recursive(value: Any, needle: str) -> bool:
    target = " ".join(str(needle or "").split())
    if not target:
        return False
    for item in _walk_values(value):
        if isinstance(item, str) and target in " ".join(item.split()):
            return True
    return False


def _find_mapping(value: Mapping[str, Any] | None, *keys: str) -> Mapping[str, Any]:
    current: Any = value
    for key in keys:
        if not isinstance(current, Mapping):
            return {}
        current = current.get(key)
    return current if isinstance(current, Mapping) else {}


def _find_first_mapping_by_key(value: Any, key_name: str) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        child = value.get(key_name)
        if isinstance(child, Mapping):
            return child
        for nested in value.values():
            found = _find_first_mapping_by_key(nested, key_name)
            if found:
                return found
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for nested in value:
            found = _find_first_mapping_by_key(nested, key_name)
            if found:
                return found
    return {}


def _all_reason_codes(public_meta: Mapping[str, Any], diagnostic_meta: Mapping[str, Any] | None = None) -> set[str]:
    reasons: set[str] = set()

    def collect(value: Any) -> None:
        if isinstance(value, Mapping):
            for key, child in value.items():
                if key in {"rejection_reasons", "reason_codes", "surface_issue_codes"} and isinstance(child, Sequence) and not isinstance(child, (str, bytes, bytearray)):
                    reasons.update(str(item) for item in child if str(item or "").strip())
                elif key in {"primary_reason", "first_failure_reason", "fail_closed_reason_code"} and str(child or "").strip():
                    reasons.add(str(child))
                else:
                    collect(child)
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            for child in value:
                collect(child)

    collect(public_meta)
    if diagnostic_meta is not None:
        collect(diagnostic_meta)
    return reasons


def _candidate_generated(public_meta: Mapping[str, Any], diagnostic_meta: Mapping[str, Any] | None = None) -> bool:
    for source in (diagnostic_meta, public_meta):
        if not isinstance(source, Mapping):
            continue
        diagnostic_summary = _find_mapping(source, "diagnostic_summary") or source
        candidate_path = _find_mapping(diagnostic_summary, "complete_initial_candidate_generation_path")
        if candidate_path:
            if candidate_path.get("candidate_generated") is True:
                return True
            if candidate_path.get("candidate_generated_before_display_gate") is True:
                return True
            if str(candidate_path.get("candidate_status") or "") == "generated":
                return True
            if str(candidate_path.get("candidate_status_before_display_gate") or "") == "generated":
                return True
        if str(diagnostic_summary.get("composer_status") or "").strip() == "generated":
            return True
    return False


def _visible_surface_gate_passed(public_meta: Mapping[str, Any]) -> bool:
    gate = _find_mapping(public_meta, "visible_surface_acceptance_gate")
    if gate:
        return gate.get("passed") is True
    diagnostic_gate = _find_mapping(public_meta, "diagnostic_summary", "gate_results", "visible_surface_acceptance")
    return diagnostic_gate.get("passed") is True


def _max_evidence_span_count(meta: Mapping[str, Any] | None) -> int:
    max_count = 0
    keys = {
        "evidence_span_count",
        "used_evidence_span_count",
        "grounded_evidence_span_count",
        "current_input_evidence_span_count",
    }

    def rec(value: Any) -> None:
        nonlocal max_count
        if isinstance(value, Mapping):
            for key, child in value.items():
                if key in keys and not isinstance(child, bool):
                    try:
                        max_count = max(max_count, int(child))
                    except Exception:
                        pass
                else:
                    rec(child)
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            for child in value:
                rec(child)

    if isinstance(meta, Mapping):
        rec(meta)
    return max_count


def _selected_reception_modes(meta: Mapping[str, Any] | None) -> set[str]:
    selected: set[str] = set()

    def collect(value: Any) -> None:
        if isinstance(value, Mapping):
            for key, child in value.items():
                if key in {"reception_mode", "reception_mode_id", "selected_reception_mode_id"}:
                    if isinstance(child, str) and child.strip():
                        selected.add(child)
                else:
                    collect(child)
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            for child in value:
                collect(child)

    if isinstance(meta, Mapping):
        collect(meta)
    return selected


def _build_public_feedback_boundary_assertion(
    *,
    case: Phase19RealDeviceCase,
    result: Mapping[str, Any],
    body: Mapping[str, Any],
    captured: Mapping[str, Any],
) -> dict[str, Any]:
    public_meta = result.get("input_feedback_meta") if isinstance(result.get("input_feedback_meta"), Mapping) else {}
    diagnostic_meta = captured.get("diagnostic_input_feedback_meta") if isinstance(captured.get("diagnostic_input_feedback_meta"), Mapping) else {}
    current_input = captured.get("current_input") if isinstance(captured.get("current_input"), Mapping) else {}
    matrix = build_phase19_public_feedback_recovery_matrix(
        case_id=case.case_id,
        expected_public_feedback=case.expected_public_input_feedback_included,
        current_input=current_input,
        public_meta=public_meta,
        diagnostic_meta=diagnostic_meta,
        reply_comment_text=result.get("input_feedback_comment"),
        response_body=body,
        source_phase=_PHASE19_TEST_PHASE,
    )
    assert_phase19_public_feedback_matrix_meta_only(
        matrix,
        forbidden_text_fragments=(case.memo, case.memo_action),
    )
    return matrix



def _assert_public_response_shape_unchanged(body: Mapping[str, Any]) -> None:
    assert set(body.keys()) == {"status", "id", "created_at", "input_feedback"}
    for key in _FORBIDDEN_PUBLIC_RESPONSE_KEYS:
        assert key not in body
    feedback = body.get("input_feedback")
    if feedback is not None:
        assert isinstance(feedback, Mapping)
        assert set(feedback.keys()) == {"comment_text", "emlis_ai"}
        for key in _FORBIDDEN_PUBLIC_RESPONSE_KEYS:
            assert key not in feedback


def _assert_public_body_has_no_internal_leaks(body: Mapping[str, Any], case: Phase19RealDeviceCase) -> None:
    dumped = json.dumps(body, ensure_ascii=False, sort_keys=True)
    for fragment in _FORBIDDEN_PUBLIC_META_FRAGMENTS:
        assert fragment not in dumped
    for internal_mode in _INTERNAL_MODE_NAMES_NOT_PUBLIC:
        assert internal_mode not in dumped
    if body.get("input_feedback") is not None:
        comment_text = str(body["input_feedback"].get("comment_text") or "")
        assert comment_text.strip()
        assert " ".join(case.memo.split()) not in " ".join(comment_text.split())
        if case.memo_action.strip():
            assert " ".join(case.memo_action.split()) not in " ".join(comment_text.split())


def _assert_current_input_matches_fixture(captured: Mapping[str, Any], case: Phase19RealDeviceCase) -> None:
    current_input = captured.get("current_input") if isinstance(captured.get("current_input"), Mapping) else {}
    assert current_input.get("memo") == case.memo
    assert current_input.get("memo_action") == case.memo_action
    assert current_input.get("emotions") == list(case.emotions)
    assert current_input.get("category") == list(case.categories)


def _assert_phase19_expectations(
    *,
    case: Phase19RealDeviceCase,
    result: Mapping[str, Any],
    body: Mapping[str, Any],
    captured: Mapping[str, Any],
) -> None:
    public_meta = result.get("input_feedback_meta") if isinstance(result.get("input_feedback_meta"), Mapping) else {}
    diagnostic_meta = captured.get("diagnostic_input_feedback_meta") if isinstance(captured.get("diagnostic_input_feedback_meta"), Mapping) else {}
    feedback = body.get("input_feedback") if isinstance(body.get("input_feedback"), Mapping) else None
    boundary = _build_public_feedback_boundary_assertion(case=case, result=result, body=body, captured=captured)
    failure_context = json.dumps(boundary, ensure_ascii=False, indent=2, sort_keys=True)

    assert boundary["public_feedback"]["input_feedback_included"] is case.expected_public_input_feedback_included, failure_context
    assert bool(str(result.get("input_feedback_comment") or "").strip()) is case.expected_comment_text_non_empty, failure_context
    if case.expected_observation_status == "non_passed":
        assert public_meta.get("observation_status") in {"rejected", "unavailable", "safety_blocked"}, failure_context
    else:
        assert public_meta.get("observation_status") == case.expected_observation_status, failure_context

    if case.expected_rn_modal_opened is not None:
        assert boundary["rn_contract"]["modal_should_open"] is case.expected_rn_modal_opened, failure_context

    if case.expected_public_input_feedback_included:
        assert feedback is not None, failure_context
        assert isinstance(feedback.get("emlis_ai"), Mapping), failure_context
        assert feedback["emlis_ai"].get("observation_status") == "passed", failure_context
    else:
        assert feedback is None, failure_context

    if case.expected_reply_kind is not None:
        reply_meta = _find_mapping(public_meta, "observation_reply_meta")
        actual_reply_kind = public_meta.get("observation_reply_kind") or reply_meta.get("observation_reply_kind")
        assert actual_reply_kind == case.expected_reply_kind, failure_context

    if case.expected_not_low_information:
        reply_meta = _find_mapping(public_meta, "observation_reply_meta")
        actual_reply_kind = public_meta.get("observation_reply_kind") or reply_meta.get("observation_reply_kind")
        assert actual_reply_kind != "low_information_observation", failure_context

    if case.expected_candidate_generated is not None:
        assert _candidate_generated(public_meta, diagnostic_meta) is case.expected_candidate_generated, failure_context

    if case.expected_visible_surface_acceptance_gate == "passed":
        assert _visible_surface_gate_passed(public_meta) is True, failure_context
        forbidden_reasons = {
            "surface_relation_skeleton_major",
            "repeated_surface",
            "limited_composer_repeated_surface",
            "phase8_repeated_sentence_tail",
        }
        assert not (_all_reason_codes(public_meta, diagnostic_meta) & forbidden_reasons), failure_context

    if case.expected_internal_mode is not None:
        assert _contains_text_recursive(diagnostic_meta, case.expected_internal_mode), failure_context
        assert not _contains_text_recursive(body, case.expected_internal_mode), failure_context

    selected_modes = _selected_reception_modes(diagnostic_meta)
    assert "relationship_gratitude_recovery" not in selected_modes, failure_context
    assert "self_understanding_learning_shift" not in selected_modes, failure_context

    if case.case_id in {
        "phase19_real_device_C_generic_self_understanding_regression",
        "phase19_real_device_D_generic_relationship_boundary_regression",
    }:
        internal_reply_meta = captured.get("reply_meta") if isinstance(captured.get("reply_meta"), Mapping) else {}
        gate_recovery_loop = (
            internal_reply_meta.get("phase20_5_gate_recovery_loop")
            if isinstance(internal_reply_meta.get("phase20_5_gate_recovery_loop"), Mapping)
            else internal_reply_meta.get("gate_recovery_loop")
        )
        internal_contract = internal_reply_meta.get("internal_response_contract") if isinstance(internal_reply_meta.get("internal_response_contract"), Mapping) else {}
        assert isinstance(gate_recovery_loop, Mapping), failure_context
        assert gate_recovery_loop.get("final_observation_status") == "passed", failure_context
        assert gate_recovery_loop.get("recovery_applied") is True, failure_context
        assert gate_recovery_loop.get("non_terminal_recovery_available") is True, failure_context
        assert gate_recovery_loop.get("first_reaction_empty_comment_text") is False, failure_context
        assert gate_recovery_loop.get("final_empty_comment_text_allowed") is False, failure_context
        assert gate_recovery_loop.get("display_gate_relaxed") is False, failure_context
        assert gate_recovery_loop.get("fixed_fallback_used") is False, failure_context
        assert gate_recovery_loop.get("case_specific_route_used") is False, failure_context
        assert gate_recovery_loop.get("case_id_runtime_condition_used") is False, failure_context
        assert gate_recovery_loop.get("phase_name_runtime_condition_used") is False, failure_context
        assert any(
            isinstance(attempt, Mapping) and attempt.get("result") == "passed"
            for attempt in gate_recovery_loop.get("internal_response_repair_attempts", [])
        ), failure_context
        assert internal_contract.get("response_kind") in {
            "normal_observation",
            "limited_grounding_observation",
        }, failure_context
        assert "_に関する記録" not in str(result.get("input_feedback_comment") or ""), failure_context

    if case.expected_evidence_span_count_min is not None:
        assert _max_evidence_span_count(diagnostic_meta) >= case.expected_evidence_span_count_min, failure_context

    if case.case_id == "phase19_real_device_B_safety_boundary_self_harm_adjacent":
        internal_reply_meta = captured.get("reply_meta") if isinstance(captured.get("reply_meta"), Mapping) else {}
        safety_triage = internal_reply_meta.get("emlis_safety_triage") if isinstance(internal_reply_meta.get("emlis_safety_triage"), Mapping) else {}
        internal_contract = internal_reply_meta.get("internal_response_contract") if isinstance(internal_reply_meta.get("internal_response_contract"), Mapping) else {}
        assert safety_triage.get("safety_triage_kind") == "self_denial_safe_state_answer", failure_context
        assert safety_triage.get("must_not_accept_identity_claim_as_fact") is True, failure_context
        assert internal_contract.get("response_kind") == "self_denial_safe_state_answer", failure_context
        assert " ".join(case.memo.split()) not in json.dumps(safety_triage, ensure_ascii=False), failure_context

    if case.case_id in {
        "phase19_real_device_C_generic_self_understanding_regression",
        "phase19_real_device_D_generic_relationship_boundary_regression",
    }:
        internal_reply_meta = captured.get("reply_meta") if isinstance(captured.get("reply_meta"), Mapping) else {}
        gate_recovery = _find_first_mapping_by_key(internal_reply_meta, "phase20_5_gate_recovery_loop")
        assert gate_recovery.get("phase20_5_gate_recovery_loop_ready") is True, failure_context
        assert gate_recovery.get("first_reaction_empty_comment_text") is False, failure_context
        assert gate_recovery.get("final_empty_comment_text_allowed") is False, failure_context
        assert gate_recovery.get("non_terminal_recovery_available") is True, failure_context
        assert gate_recovery.get("recovered_to_public_observation") is True, failure_context
        assert gate_recovery.get("recovery_applied") is True, failure_context
        assert gate_recovery.get("gate_threshold_relaxed") is False, failure_context
        assert gate_recovery.get("fixed_fallback_used") is False, failure_context
        assert gate_recovery.get("case_specific_route_used") is False, failure_context
        assert gate_recovery.get("c_d_specific_runtime_cue_used") is False, failure_context
        assert gate_recovery.get("comment_text_absent_allowed_only_for_emergency_or_infra") is True, failure_context
        internal_contract = internal_reply_meta.get("internal_response_contract") if isinstance(internal_reply_meta.get("internal_response_contract"), Mapping) else {}
        assert internal_contract.get("response_kind") in {"normal_observation", "limited_grounding_observation"}, failure_context
        assert internal_contract.get("repair_attempts"), failure_context
        comment_text = str(result.get("input_feedback_comment") or "")
        assert "見えたこと：" in comment_text, failure_context
        assert "Emlisから：" in comment_text, failure_context
        assert "_に関する記録" not in comment_text, failure_context


def test_phase19_0_real_device_abcd_fixture_definition_is_exact_and_contract_intent_is_fixed() -> None:
    assert _PHASE19_FIXTURE_SCHEMA_VERSION == "cocolon.emlis.phase19.real_device_abcd_fixture.v1"
    assert [case.case_id for case in PHASE19_REAL_DEVICE_ABCD_CASES] == [
        "phase19_real_device_A_low_information_fatigue",
        "phase19_real_device_B_safety_boundary_self_harm_adjacent",
        "phase19_real_device_C_generic_self_understanding_regression",
        "phase19_real_device_D_generic_relationship_boundary_regression",
    ]
    assert PHASE19_REAL_DEVICE_ABCD_CASES[0].memo == "なんか今日は全部だるい。\n何もしたくない。"
    assert PHASE19_REAL_DEVICE_ABCD_CASES[1].memo == "1番自分を傷つけてるのは私だ\nずっとそれを続けて、いい事なんて絶対にない"
    assert PHASE19_REAL_DEVICE_ABCD_CASES[2].memo_action.endswith("傷や汚れの場所、自分のこうかな？という憶測をメモしていった。")
    assert PHASE19_REAL_DEVICE_ABCD_CASES[3].categories == ("恋愛", "人間関係", "価値観")
    assert [case.expected_public_input_feedback_included for case in PHASE19_REAL_DEVICE_ABCD_CASES] == [True, True, True, True]
    assert [case.expected_observation_status for case in PHASE19_REAL_DEVICE_ABCD_CASES] == [
        "passed",
        "passed",
        "passed",
        "passed",
    ]
    assert not any(hasattr(case, "expected_comment_text") for case in PHASE19_REAL_DEVICE_ABCD_CASES)
    assert not any(hasattr(case, "expected_exact_comment_text") for case in PHASE19_REAL_DEVICE_ABCD_CASES)


@pytest.mark.asyncio
@pytest.mark.parametrize("case", PHASE19_REAL_DEVICE_ABCD_CASES, ids=lambda case: case.case_id)
async def test_phase19_0_emotion_submit_real_device_abcd_public_feedback_contract(
    monkeypatch: pytest.MonkeyPatch,
    case: Phase19RealDeviceCase,
) -> None:
    _enable_complete_initial(monkeypatch)
    _patch_submit_persistence(monkeypatch, inserted_id=_PHASE19_SAFE_INSERTED_IDS[case.case_id])
    captured: dict[str, Any] = {}
    _patch_real_reply_source_bundle(monkeypatch, captured)

    result = await submit_service.persist_emotion_submission(
        user_id=f"phase19-0-user-{case.case_id}",
        emotions=list(case.emotions),
        memo=case.memo,
        memo_action=case.memo_action,
        category=list(case.categories),
        created_at="2026-05-30T00:00:00.000000+00:00",
    )
    body = _public_response_body(result)

    _assert_public_response_shape_unchanged(body)
    _assert_public_body_has_no_internal_leaks(body, case)
    _assert_current_input_matches_fixture(captured, case)
    _assert_phase19_expectations(case=case, result=result, body=body, captured=captured)
