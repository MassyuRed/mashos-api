# -*- coding: utf-8 -*-
from __future__ import annotations

import gc

import pytest

import emotion_submit_service as submit_service
import emlis_ai_reply_service as reply_service
from emlis_ai_complete_composer_client import CocolonCompleteComposerClient
from emlis_ai_types import GreetingDecision, SourceBundle
from fixtures.emlis_ai_two_stage_reception_cases import (
    evaluate_forbidden_surface_fragments,
    two_stage_reception_case_by_id,
)
from helpers.emlis_ai_two_stage_product_visible_fixture_assertions import (
    PHASE17_PRODUCT_VISIBLE_REQUIRED_CASE_IDS,
)


@pytest.fixture
def daily_a_current_input() -> dict:
    return dict(two_stage_reception_case_by_id("daily_unpleasant_encounter_A")["current_input"])


def _patch_submit_persistence(monkeypatch, current_input: dict | None = None) -> None:
    fixture_input = dict(current_input or two_stage_reception_case_by_id("daily_unpleasant_encounter_A")["current_input"])

    def fake_normalize_submission_payload(**_kwargs):
        return {
            "emotions_tags": list(fixture_input.get("emotions") or ["怒り"]),
            "emotion_details": list(fixture_input.get("emotion_details") or []),
            "emotion_strength_avg": 2.0,
            "category": list(fixture_input.get("category") or []),
            "has_memo_input": bool(str(fixture_input.get("memo") or "").strip() or str(fixture_input.get("memo_action") or "").strip()),
        }

    monkeypatch.setattr(
        submit_service,
        "normalize_submission_payload",
        fake_normalize_submission_payload,
    )

    async def fake_insert_emotion_row(**_kwargs):
        return {
            "id": str(fixture_input.get("id") or "phase17-emotion-log-1"),
            "created_at": str(fixture_input.get("created_at") or "2026-05-28T00:00:00.000000+00:00"),
        }

    async def fake_subscription_tier_for_user(*_args, **_kwargs):
        return "free"

    monkeypatch.setattr(submit_service, "_insert_emotion_row", fake_insert_emotion_row)
    monkeypatch.setattr(submit_service, "invalidate_prefix", lambda _prefix: None)
    monkeypatch.setattr(submit_service, "_global_summary_activity_date_from_created_at", lambda _created_at: "2026-05-28")
    monkeypatch.setattr(submit_service, "_start_post_submit_background_tasks", lambda **_kwargs: None)
    monkeypatch.setattr(submit_service, "get_subscription_tier_for_user", fake_subscription_tier_for_user)


def _patch_reply_rendering(monkeypatch) -> None:
    async def fake_source_bundle(**kwargs):
        return SourceBundle(
            user_id=kwargs["user_id"],
            display_name="Mash",
            current_input=dict(kwargs["current_input"]),
            greeting=GreetingDecision(
                slot_name="phase17-test",
                slot_key="phase17-test",
                greeting_text="Emlisです。",
                first_in_slot=False,
            ),
            side_state={},
            input_effort={},
            memory_richness={},
            debug={"tier": "free"},
        )

    monkeypatch.setattr(reply_service, "build_emlis_ai_source_bundle", fake_source_bundle)

    async def actual_render_with_complete_client(**kwargs):
        return await reply_service.render_emlis_ai_reply(
            **kwargs,
            composer_client=CocolonCompleteComposerClient(ap0_green=True, rollout_allowed=True),
        )

    monkeypatch.setattr(submit_service, "render_emlis_ai_reply", actual_render_with_complete_client)


def _assert_public_two_stage_input_feedback_contract(
    *,
    result: dict,
    case_id: str,
    current_input: dict,
) -> None:
    comment_text = result["input_feedback_comment"]
    meta = result["input_feedback_meta"]
    assert meta["observation_status"] == "passed", {
        "case_id": case_id,
        "meta": meta,
    }
    assert comment_text.startswith("見えたこと：\n"), {
        "case_id": case_id,
        "comment_text": comment_text,
    }
    assert "\n\nEmlisから：\n" in comment_text, {
        "case_id": case_id,
        "comment_text": comment_text,
    }
    assert comment_text.count("見えたこと：") == 1, comment_text
    assert comment_text.count("Emlisから：") == 1, comment_text
    assert not evaluate_forbidden_surface_fragments(comment_text, two_stage_reception_case_by_id(case_id)), {
        "case_id": case_id,
        "comment_text": comment_text,
    }

    for forbidden in (
        "achievement",
        "positive state",
        "perfection fear",
        "pressure or limit",
        "同じ流れ",
        "同じ場所",
        "別々の向き",
        "片方だけに寄らず",
    ):
        assert forbidden not in comment_text, {
            "case_id": case_id,
            "forbidden": forbidden,
            "comment_text": comment_text,
        }

    for raw_fragment in (
        str(current_input.get("memo") or ""),
        str(current_input.get("memo_action") or ""),
    ):
        if raw_fragment.strip():
            assert not _contains_text_recursive(meta, raw_fragment), {"case_id": case_id, "raw_fragment_leaked": raw_fragment}
    assert not _contains_text_recursive(meta, comment_text), {"case_id": case_id, "comment_text_leaked": True}
    assert meta["public_feedback_meta_boundary"]["raw_input_included"] is False
    assert meta["public_feedback_meta_boundary"]["comment_text_included"] is False
    assert meta["submit_speed_regression"]["comment_text_body_included"] is False
    assert meta["submit_speed_regression"]["public_response_key_added"] is False
    assert meta["submit_speed_regression"]["saved_emotion_success"] is True
    assert meta["submit_speed_regression"].get("reply_timeout") is False
    assert meta["submit_speed_regression"].get("public_feedback_included") is True




def _contains_text_recursive(value, needle: str, *, _seen: set[int] | None = None) -> bool:
    cleaned_needle = _clean_text(needle)
    if not cleaned_needle:
        return False
    seen = _seen if _seen is not None else set()
    value_id = id(value)
    if value_id in seen:
        return False
    if isinstance(value, (dict, list, tuple, set)):
        seen.add(value_id)
    if isinstance(value, dict):
        return any(_contains_text_recursive(item, cleaned_needle, _seen=seen) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_text_recursive(item, cleaned_needle, _seen=seen) for item in value)
    if isinstance(value, str):
        return cleaned_needle in _clean_text(value)
    return False


def _clean_text(value: str) -> str:
    return " ".join(str(value or "").split())


def _phase17_10_release_memory() -> None:
    """Best-effort release for large CompleteComposer E2E objects."""

    gc.collect()
    try:
        import ctypes

        ctypes.CDLL("libc.so.6").malloc_trim(0)
    except Exception:
        pass


@pytest.mark.asyncio
async def test_phase16_8_emotion_submit_path_returns_public_two_stage_input_feedback(monkeypatch, daily_a_current_input: dict) -> None:
    _patch_submit_persistence(monkeypatch, daily_a_current_input)
    _patch_reply_rendering(monkeypatch)

    result = await submit_service.persist_emotion_submission(
        user_id="phase16-user",
        emotions=daily_a_current_input["emotions"],
        memo=daily_a_current_input["memo"],
        memo_action=daily_a_current_input["memo_action"],
        category=daily_a_current_input["category"],
    )

    _assert_public_two_stage_input_feedback_contract(
        result=result,
        case_id="daily_unpleasant_encounter_A",
        current_input=daily_a_current_input,
    )
    assert "先を考え続ける流れ" not in result["input_feedback_comment"]
    del result
    _phase17_10_release_memory()


@pytest.mark.asyncio
@pytest.mark.parametrize("case_id", PHASE17_PRODUCT_VISIBLE_REQUIRED_CASE_IDS)
async def test_phase17_8_emotion_submit_five_fixtures_return_public_two_stage_input_feedback(monkeypatch, case_id: str) -> None:
    case = two_stage_reception_case_by_id(case_id)
    current_input = dict(case["current_input"])
    _patch_submit_persistence(monkeypatch, current_input)
    _patch_reply_rendering(monkeypatch)

    result = await submit_service.persist_emotion_submission(
        user_id=f"phase17-user-{case_id}",
        emotions=current_input["emotions"],
        memo=current_input["memo"],
        memo_action=current_input["memo_action"],
        category=current_input["category"],
        created_at=current_input["created_at"],
        is_secret=bool(current_input.get("is_secret")),
    )

    _assert_public_two_stage_input_feedback_contract(
        result=result,
        case_id=case_id,
        current_input=current_input,
    )
    del result
    _phase17_10_release_memory()
