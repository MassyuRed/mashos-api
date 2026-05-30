# -*- coding: utf-8 -*-
from __future__ import annotations

import json

import pytest

from emlis_ai_diagnostic_failure_taxonomy import (
    CLASS_CANDIDATE_BLOCKED_SURFACE_GRAMMAR,
    CLASS_CANDIDATE_BLOCKED_TWO_STAGE_CONTRACT,
    CLASS_CANDIDATE_GENERATED_DISPLAY_PASSED,
    DIAGNOSTIC_FAILURE_TAXONOMY_SCHEMA_VERSION,
    build_diagnostic_failure_taxonomy_meta,
)
from emlis_ai_observation_diagnostic_branching import resolve_observation_diagnostic_next_branch
from emlis_ai_observation_diagnostic_lockdown import build_observation_diagnostic_lockdown


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

PASSING_PUBLIC_TEXT = (
    "Mashさん、Emlisです。\n"
    "今回の入力では、リラックスできて自分のことを優先できる嬉しさと、現実と向き合うダメージが同じ場所で重なっています。\n"
    "気をつけなきゃ行けないことを分かりながら普通に生活したい願いも離れていない中で、たまに逃げ出したくなる言葉は今の生活不便だなと感じる重さとつながっています。"
)


class _TextComposer:
    def generate(self, payload):
        return {
            "response_schema_version": "emlis.composer.response.v1",
            "composer_source": "ai_generated",
            "composer_model": "diagnostic_phase18_fake_text_composer.v1",
            "generation_method": "test_composer",
            "generation_scope": "scoped_graph_only",
            "coverage_scope": "current_input_core",
            "fixed_string_renderer_used": False,
            "comment_text": PASSING_TEXT,
            "used_evidence_span_ids": [item["span_id"] for item in payload["evidence_spans"][:4]],
        }


def _input(memo: str) -> dict:
    return {
        "id": "phase18-diagnostic-taxonomy-emotion",
        "created_at": "2026-05-30T00:00:00Z",
        "memo": memo,
        "memo_action": "",
        "emotion_details": [{"type": "自己理解", "strength": "medium"}],
        "emotions": ["自己理解"],
        "category": ["生活"],
    }


def _clear_limited_composer_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
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
    ):
        monkeypatch.delenv(name, raising=False)


def _dump(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def test_phase18_7_taxonomy_maps_two_stage_contract_to_canonical_class_with_legacy_alias() -> None:
    taxonomy = build_diagnostic_failure_taxonomy_meta(
        observation_status="rejected",
        stage="display",
        primary_reason="two_stage_label_missing",
        secondary_reasons=["two_stage_required_but_unrealized", "two_stage_complete_surface_blocked_by_gate"],
        composer_status="generated",
        candidate_generated=True,
        gate_results={"display": {"passed": False, "primary_reason": "two_stage_label_missing"}},
        display_rejection_reasons=["two_stage_label_missing"],
    )

    assert taxonomy["schema_version"] == DIAGNOSTIC_FAILURE_TAXONOMY_SCHEMA_VERSION
    assert taxonomy["classification"] == CLASS_CANDIDATE_BLOCKED_TWO_STAGE_CONTRACT
    assert taxonomy["canonical_classification"] == CLASS_CANDIDATE_BLOCKED_TWO_STAGE_CONTRACT
    assert "candidate_generated_but_display_rejected" in taxonomy["legacy_classification_aliases"]
    assert taxonomy["public_contract"]["comment_text_body_included"] is False
    assert taxonomy["public_contract"]["generated_candidate_text_included"] is False
    assert taxonomy["public_contract"]["raw_input_included"] is False
    dumped = _dump(taxonomy)
    assert SAMPLE_MEMO.strip().split("\n")[0] not in dumped
    assert PASSING_TEXT not in dumped


def test_phase18_7_surface_grammar_class_routes_to_meta_safe_branch() -> None:
    taxonomy = build_diagnostic_failure_taxonomy_meta(
        observation_status="rejected",
        stage="display",
        primary_reason="runtime_surface_pre_return_gate_failed",
        secondary_reasons=["malformed_phrase_unit"],
        composer_status="generated",
        candidate_generated=True,
        gate_results={"display": {"passed": False, "primary_reason": "runtime_surface_pre_return_gate_failed"}},
        display_rejection_reasons=["runtime_surface_pre_return_gate_failed"],
    )

    assert taxonomy["classification"] == CLASS_CANDIDATE_BLOCKED_SURFACE_GRAMMAR
    assert "candidate_generated_but_display_rejected" in taxonomy["legacy_classification_aliases"]
    branch = resolve_observation_diagnostic_next_branch(
        {
            "classification": taxonomy["classification"],
            "raw_input_included": False,
            "comment_text_included": False,
        }
    )
    assert branch["classification"] == CLASS_CANDIDATE_BLOCKED_SURFACE_GRAMMAR
    assert branch["ready_for_cause_repair"] is True
    assert branch["raw_input_included"] is False
    assert branch["comment_text_included"] is False


@pytest.mark.asyncio
async def test_phase18_7_legacy_text_composer_candidate_keeps_passed_diagnostic_summary(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_limited_composer_env(monkeypatch)
    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="phase18-diagnostic-taxonomy-passed-user",
        subscription_tier="free",
        current_input=_input(SAMPLE_MEMO),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
        composer_client=_TextComposer(),
    )

    summary = reply.meta["diagnostic_summary"]
    taxonomy = summary["diagnostic_failure_taxonomy"]
    assert summary["observation_status"] == "passed"
    assert summary["stage"] == "display"
    assert summary["primary_reason"] == "passed"
    assert summary["classification"] == CLASS_CANDIDATE_GENERATED_DISPLAY_PASSED
    assert taxonomy["classification"] == CLASS_CANDIDATE_GENERATED_DISPLAY_PASSED
    assert taxonomy["public_contract"]["public_response_key_added"] is False
    assert taxonomy["public_contract"]["comment_text_body_included"] is False
    assert taxonomy["public_contract"]["raw_input_included"] is False
    assert reply.comment_text == PASSING_PUBLIC_TEXT


def test_phase18_7_lockdown_keeps_legacy_classification_and_adds_canonical_taxonomy() -> None:
    record = build_observation_diagnostic_lockdown(
        input_feedback_comment="",
        input_feedback_meta={
            "observation_status": "rejected",
            "diagnostic_summary": {
                "observation_status": "rejected",
                "stage": "display",
                "primary_reason": "two_stage_label_missing",
                "secondary_reasons": ["two_stage_required_but_unrealized"],
                "composer_status": "generated",
                "registry_resolution": {"connection_status": "connected"},
                "gate_results": {
                    "reader": {"passed": True, "primary_reason": "passed"},
                    "grounding": {"passed": True, "primary_reason": "passed"},
                    "template_echo": {"passed": True, "primary_reason": "passed"},
                    "display": {
                        "passed": False,
                        "primary_reason": "two_stage_label_missing",
                        "rejection_reasons": ["two_stage_label_missing"],
                    },
                },
            },
        },
        emotion_log_id="phase18-taxonomy-lockdown",
        created_at="2026-05-30T00:00:00Z",
    )

    assert record["classification"] == "candidate_generated_but_display_rejected"
    assert record["canonical_classification"] == CLASS_CANDIDATE_BLOCKED_TWO_STAGE_CONTRACT
    assert record["diagnostic_failure_taxonomy"]["classification"] == CLASS_CANDIDATE_BLOCKED_TWO_STAGE_CONTRACT
    assert "candidate_generated_but_display_rejected" in record["legacy_classification_aliases"]
    dumped = _dump(record)
    assert PASSING_TEXT not in dumped
    assert SAMPLE_MEMO.strip().split("\n")[0] not in dumped
