# -*- coding: utf-8 -*-
from __future__ import annotations

"""P8 H/I/J E2E regression for reception-required EmlisAI public feedback.

These are regression fixtures from the H/I/J screenshots/input text.  The test
must not introduce H/I/J runtime branches, exact fixed output strings, RN/API/DB
contract changes, or public body/meta leakage.  Assertions stay at public
contract + semantic direction level.
"""

import json
import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import pytest

import emlis_ai_context_service as context_service
import emlis_ai_reply_service as reply_service
import emotion_submit_service as submit_service
from emlis_ai_observation_eligibility_router import route_emlis_observation_material_eligibility
from emlis_ai_public_feedback_meta import should_include_public_input_feedback
from emlis_ai_public_surface_requirement import resolve_public_surface_requirement
from emlis_ai_question_dominance_guard import build_question_dominance_guard_summary
from emlis_ai_types import GreetingDecision


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
_PUBLIC_BODY_FORBIDDEN_KEYS = ("observation_text", "reception_text")
_PUBLIC_META_FORBIDDEN_FRAGMENTS = (
    '"raw_input"',
    '"raw_text"',
    '"current_input"',
    '"candidate_comment_text"',
    '"generated_candidate_text"',
    '"surface_text"',
)
_FORBIDDEN_QUESTION_LED_FRAGMENTS = (
    "詳しい出来事では見えていません",
    "詳しい出来事まではまだ見えていません",
    "詳しく残せそうなら",
    "何があったか残してみませんか",
    "何が変わったのか残してみませんか",
)
_WALK_MAX_DEPTH = 12
_WALK_MAX_NODES = 6000
_WALK_MAX_SEQUENCE_ITEMS = 200


@dataclass(frozen=True)
class P8HijCase:
    case_id: str
    memo: str
    emotions: tuple[str, ...]
    categories: tuple[str, ...]
    expected_material_quality: str
    expected_surface_requirement_family: str
    expected_comment_fragments: tuple[str, ...]
    forbidden_comment_fragments: tuple[str, ...] = _FORBIDDEN_QUESTION_LED_FRAGMENTS


P8_HIJ_CASES: tuple[P8HijCase, ...] = (
    P8HijCase(
        case_id="p8_H_recovered_energy_future_direction",
        memo=(
            "ふとした時に、これやってみたいなとか\n"
            "自分にも出来るかもしれないって思う瞬間がある\n"
            "でもそのあとに、なんで私はそう思ったんだろうって考えることが多い\n"
            "きっと今までの経験とか気持ちとか\n"
            "色んなものが重なってその考えが出てきてるんだと思う\n"
            "だから私は、その「やりたい」と思った気持ちを大事にしたい\n"
            "頑張って良かった もっと色々挑戦したい\n"
            "そう思えることが大きな一歩だと思う\n"
            "ずっと落ち込んでて何もしたくなくて\n"
            "自信をなくして諦めていたから\n"
            "この気持ちになれたことを大切にして\n"
            "つぎどう頑張るか知って行きたい"
        ),
        emotions=("平穏",),
        categories=("生活",),
        expected_material_quality="eligible",
        expected_surface_requirement_family="plain_state_answer",
        expected_comment_fragments=("やってみたい", "次の頑張り方", "出来るかもしれない"),
        forbidden_comment_fragments=_FORBIDDEN_QUESTION_LED_FRAGMENTS + ("生活について、平穏の動き",),
    ),
    P8HijCase(
        case_id="p8_I_limited_recovered_energy_relationship_wish",
        memo=(
            "沢山甘えられて寂しい時にそばに居てくれるような\n"
            "存在やっぱりいいなって思う 気力が出てきた時は恋愛も\n"
            "したくなる。でもやる気力が出てきたのが嬉しいし\n"
            "このタイミング逃したら、また気力なくなって\n"
            "何も出来なくなくからこのタイミングでいろんな事に\n"
            "挑戦して、いずれは素敵な人と出会えたらいいな"
        ),
        emotions=("平穏",),
        categories=("生活", "人生"),
        expected_material_quality="limited_grounding",
        expected_surface_requirement_family="labelled_two_stage",
        expected_comment_fragments=("気力", "人と近く", "挑戦"),
    ),
    P8HijCase(
        case_id="p8_J_limited_comparison_baseline_small_change",
        memo=(
            "「いきなり大きく変わろう」とするよりも、\n"
            "「昨日の自分よりほんの少し前に進めたらいい」\n"
            "そういう気持ちで過ごしていきたい。\n"
            "人と比べてしまうと、どうしても焦ったり、自分が遅い気がしてしまう。\n"
            "でも、本当は比べる相手は他の誰かじゃなくて、昨日の自分なんだと思う。\n"
            "昨日より少し出来たことが増えた。\n"
            "昨日より少し勇気が出せた。\n"
            "昨日より少し気持ちを言葉に出来た。\n"
            "そういう小さな変化を大切にしていきたい"
        ),
        emotions=("自己理解",),
        categories=("健康", "人生"),
        expected_material_quality="limited_grounding",
        expected_surface_requirement_family="labelled_two_stage",
        expected_comment_fragments=("昨日の自分", "小さな変化", "少し"),
    ),
)


def _current_input(case: P8HijCase) -> dict[str, Any]:
    return {
        "memo": case.memo,
        "memo_action": "",
        "emotions": list(case.emotions),
        "category": list(case.categories),
    }


def _clear_emlis_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in tuple(os.environ):
        if "EMLIS" in name or name.startswith("COCOLON_"):
            monkeypatch.delenv(name, raising=False)
    for name in _COMPLETE_INITIAL_ENV_KEYS:
        monkeypatch.delenv(name, raising=False)


def _enable_complete_initial(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_emlis_flags(monkeypatch)
    for key, value in _COMPLETE_INITIAL_ENV.items():
        monkeypatch.setenv(key, value)


def _patch_submit_persistence(monkeypatch: pytest.MonkeyPatch, *, inserted_id: str) -> None:
    async def fake_insert_emotion_row(**kwargs: Any) -> dict[str, Any]:
        return {
            "id": inserted_id,
            "created_at": str(kwargs.get("created_at") or "2026-06-07T00:00:00.000000+00:00"),
        }

    async def fake_invalidate_prefix(_prefix: str) -> None:
        return None

    async def fake_subscription_tier_for_user(*_args: Any, **_kwargs: Any) -> str:
        return "free"

    monkeypatch.setattr(submit_service, "_insert_emotion_row", fake_insert_emotion_row)
    monkeypatch.setattr(submit_service, "invalidate_prefix", fake_invalidate_prefix)
    monkeypatch.setattr(submit_service, "_global_summary_activity_date_from_created_at", lambda _created_at: "2026-06-07")
    monkeypatch.setattr(submit_service, "_start_post_submit_background_tasks", lambda **_kwargs: None)
    monkeypatch.setattr(submit_service, "get_subscription_tier_for_user", fake_subscription_tier_for_user)


def _patch_real_reply_source_bundle(monkeypatch: pytest.MonkeyPatch, captured: dict[str, Any]) -> None:
    async def fake_display_name(_user_id: str) -> str:
        return "Mash"

    async def fake_timezone(_user_id: str, *, fallback: str | None = None) -> str:
        return str(fallback or "Asia/Tokyo")

    async def fake_greeting(**_kwargs: Any) -> GreetingDecision:
        return GreetingDecision(
            slot_name="p8-hij-reception-required",
            slot_key="p8-hij-reception-required",
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


def _is_walkable_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))


def _walk_values(value: Any) -> list[Any]:
    out: list[Any] = []
    visited: set[int] = set()
    stack: list[tuple[Any, int]] = [(value, 0)]
    visited_nodes = 0
    while stack and visited_nodes < _WALK_MAX_NODES:
        item, depth = stack.pop()
        visited_nodes += 1
        if isinstance(item, Mapping):
            marker = id(item)
            if marker in visited:
                continue
            visited.add(marker)
            if depth >= _WALK_MAX_DEPTH:
                continue
            for child in reversed(list(item.values())[:_WALK_MAX_SEQUENCE_ITEMS]):
                stack.append((child, depth + 1))
        elif _is_walkable_sequence(item):
            marker = id(item)
            if marker in visited:
                continue
            visited.add(marker)
            if depth >= _WALK_MAX_DEPTH:
                continue
            for child in reversed(list(item)[:_WALK_MAX_SEQUENCE_ITEMS]):
                stack.append((child, depth + 1))
        else:
            out.append(item)
    return out


def _contains_text_recursive(value: Any, needle: str) -> bool:
    target = " ".join(str(needle or "").split())
    if not target:
        return False
    for item in _walk_values(value):
        if isinstance(item, str) and target in " ".join(item.split()):
            return True
    return False


def _assert_public_response_shape_unchanged(body: Mapping[str, Any]) -> None:
    assert set(body.keys()) == {"status", "id", "created_at", "input_feedback"}
    for key in _PUBLIC_BODY_FORBIDDEN_KEYS:
        assert key not in body
    feedback = body.get("input_feedback")
    assert isinstance(feedback, Mapping)
    assert set(feedback.keys()) == {"comment_text", "emlis_ai"}
    for key in _PUBLIC_BODY_FORBIDDEN_KEYS:
        assert key not in feedback


def _assert_public_meta_body_free(*, body: Mapping[str, Any], result: Mapping[str, Any], case: P8HijCase) -> None:
    public_meta = result.get("input_feedback_meta") if isinstance(result.get("input_feedback_meta"), Mapping) else {}
    dumped = json.dumps(body, ensure_ascii=False, sort_keys=True)
    for fragment in _PUBLIC_META_FORBIDDEN_FRAGMENTS:
        assert fragment not in dumped, {"case_id": case.case_id, "fragment": fragment, "body": body}
    assert not _contains_text_recursive(public_meta, case.memo), {"case_id": case.case_id, "raw_memo_leaked": True}
    assert not _contains_text_recursive(public_meta, str(result.get("input_feedback_comment") or "")), {
        "case_id": case.case_id,
        "comment_text_leaked": True,
    }
    boundary = public_meta.get("public_feedback_meta_boundary") if isinstance(public_meta.get("public_feedback_meta_boundary"), Mapping) else {}
    speed = public_meta.get("submit_speed_regression") if isinstance(public_meta.get("submit_speed_regression"), Mapping) else {}
    assert boundary.get("raw_input_included") is False, {"case_id": case.case_id, "meta": public_meta}
    assert boundary.get("comment_text_included") is False, {"case_id": case.case_id, "meta": public_meta}
    assert speed.get("comment_text_body_included") is False, {"case_id": case.case_id, "meta": public_meta}
    assert speed.get("public_response_key_added") is False, {"case_id": case.case_id, "meta": public_meta}


def _assert_material_and_requirement(case: P8HijCase) -> None:
    current_input = _current_input(case)
    route = route_emlis_observation_material_eligibility(current_input)
    requirement = resolve_public_surface_requirement(
        current_input=current_input,
        material_route=route,
        composer_meta=None,
        diagnostic_summary=None,
    )
    route_meta = route.as_meta()
    assert route_meta.get("material_quality") == case.expected_material_quality, {
        "case_id": case.case_id,
        "route_meta": route_meta,
    }
    assert requirement.get("surface_requirement_family") == case.expected_surface_requirement_family, {
        "case_id": case.case_id,
        "requirement": requirement,
    }
    if case.expected_material_quality == "limited_grounding":
        assert requirement.get("two_stage_required") is True, requirement
        assert requirement.get("low_information_allowed") is False, requirement


@pytest.mark.asyncio
@pytest.mark.parametrize("case", P8_HIJ_CASES, ids=[case.case_id for case in P8_HIJ_CASES])
async def test_p8_hij_submit_e2e_returns_reception_required_public_feedback(
    monkeypatch: pytest.MonkeyPatch,
    case: P8HijCase,
) -> None:
    _assert_material_and_requirement(case)
    _enable_complete_initial(monkeypatch)
    _patch_submit_persistence(monkeypatch, inserted_id=f"p8-{case.case_id}")
    captured: dict[str, Any] = {}
    _patch_real_reply_source_bundle(monkeypatch, captured)

    result = await submit_service.persist_emotion_submission(
        user_id=f"p8-user-{case.case_id}",
        emotions=list(case.emotions),
        memo=case.memo,
        memo_action="",
        category=list(case.categories),
    )
    body = _public_response_body(result)
    _assert_public_response_shape_unchanged(body)

    public_meta = result.get("input_feedback_meta") if isinstance(result.get("input_feedback_meta"), Mapping) else {}
    comment_text = str(result.get("input_feedback_comment") or "").strip()
    feedback = body.get("input_feedback") if isinstance(body.get("input_feedback"), Mapping) else {}
    assert feedback.get("comment_text") == comment_text, {"case_id": case.case_id, "body": body}
    assert public_meta.get("observation_status") == "passed", {"case_id": case.case_id, "meta": public_meta}
    assert feedback.get("emlis_ai", {}).get("observation_status") == "passed", {
        "case_id": case.case_id,
        "body": body,
    }
    assert comment_text.startswith("見えたこと：\n"), {"case_id": case.case_id, "comment_text": comment_text}
    assert "\n\nEmlisから：\n" in comment_text, {"case_id": case.case_id, "comment_text": comment_text}
    assert comment_text.count("見えたこと：") == 1, comment_text
    assert comment_text.count("Emlisから：") == 1, comment_text
    for fragment in case.expected_comment_fragments:
        assert fragment in comment_text, {"case_id": case.case_id, "fragment": fragment, "comment_text": comment_text}
    for forbidden in case.forbidden_comment_fragments:
        assert forbidden not in comment_text, {
            "case_id": case.case_id,
            "forbidden": forbidden,
            "comment_text": comment_text,
        }

    guard = build_question_dominance_guard_summary(
        comment_text,
        surface_requirement_family=case.expected_surface_requirement_family,
        material_quality_family=case.expected_material_quality,
        reception_required=True,
        question_required=False,
    )
    assert guard["passed"] is True, {"case_id": case.case_id, "guard": guard, "comment_text": comment_text}
    assert guard["question_dominant"] is False, {"case_id": case.case_id, "guard": guard}
    _assert_public_meta_body_free(body=body, result=result, case=case)

    captured_input = captured.get("current_input") if isinstance(captured.get("current_input"), Mapping) else {}
    expected_input = _current_input(case)
    for key, value in expected_input.items():
        assert captured_input.get(key) == value, {
            "case_id": case.case_id,
            "key": key,
            "captured_input": captured_input,
        }
    reply_meta = captured.get("reply_meta") if isinstance(captured.get("reply_meta"), Mapping) else {}
    gate_loop = reply_meta.get("phase20_5_gate_recovery_loop") if isinstance(reply_meta.get("phase20_5_gate_recovery_loop"), Mapping) else {}
    assert gate_loop.get("final_observation_status") == "passed", {"case_id": case.case_id, "reply_meta": reply_meta}
    assert gate_loop.get("display_gate_relaxed") is False, {"case_id": case.case_id, "gate_loop": gate_loop}
    assert gate_loop.get("fixed_fallback_used") is False, {"case_id": case.case_id, "gate_loop": gate_loop}
    assert gate_loop.get("case_specific_route_used") is False, {"case_id": case.case_id, "gate_loop": gate_loop}
    assert gate_loop.get("case_id_runtime_condition_used") is False, {"case_id": case.case_id, "gate_loop": gate_loop}
