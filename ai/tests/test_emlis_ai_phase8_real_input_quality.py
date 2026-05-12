# -*- coding: utf-8 -*-
from __future__ import annotations

import inspect

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

import emlis_ai_limited_composer_client as limited_composer_module

from cocolon_text_generation_core.adapters.emlis_observation_composer import ADAPTER_NAME as COMMON_CORE_ADAPTER_NAME
from cocolon_text_generation_core.policies import (
    CORE_ID_EMLIS,
    STATUS_GENERATED,
    TEXT_GENERATION_CORE_PHASE8_NEXT_PHASE,
    TEXT_GENERATION_CORE_PHASE8_STOP_POINT,
)
from emlis_ai_conversation_composer_service import build_conversation_composer_payload
from emlis_ai_evidence_ledger_service import build_evidence_ledger
from emlis_ai_grounding_judge import judge_grounding
from emlis_ai_limited_composer_client import CocolonLimitedComposerClient
from emlis_ai_limited_observation_scope_service import build_limited_observation_scope
from emlis_ai_limited_sentence_quality_guard import detect_phase8_profile
from emlis_ai_listener_reader_judge import judge_listener_readability
from emlis_ai_observation_integrator_service import integrate_perspective_board
from emlis_ai_perspective_board import build_perspective_board
from emlis_ai_perspective_observers import run_perspective_observers
from emlis_ai_template_echo_guard import guard_template_echo
from fixtures.emlis_ai_phase8_cases import (
    PHASE8_CASES,
    PHASE8_FORBIDDEN_SURFACES,
    PHASE8_GENERALIZATION_CASES,
)


def _current_input(case: dict) -> dict:
    return {
        "id": f"phase8-{case['case_id']}",
        "created_at": "2026-05-10T00:00:00Z",
        "memo": case["memo"],
        "memo_action": "",
        "emotion_details": [{"type": case.get("emotion") or "自己理解", "strength": "medium"}],
        "emotions": [case.get("emotion") or "自己理解"],
        "category": [case.get("category") or "生活"],
    }


def _candidate_for(case: dict):
    evidence = build_evidence_ledger(_current_input(case))
    reports = run_perspective_observers(evidence)
    board = build_perspective_board(evidence_spans=evidence, reports=reports)
    graph = integrate_perspective_board(board=board, display_name="Mash")
    scope = build_limited_observation_scope(graph=graph, evidence_spans=evidence)
    payload = build_conversation_composer_payload(
        graph=scope.scoped_graph,
        evidence_spans=evidence,
        display_name="Mash",
        greeting_text="Emlisです。",
        trace_id=f"phase8-{case['case_id']}",
    )
    return CocolonLimitedComposerClient().generate(payload), evidence, scope


def _compact(value: str) -> str:
    for ch in "\n\r\t 　、,。.!！?？『』「」（）()[]【】":
        value = value.replace(ch, "")
    return value


def _body_lines(text: str) -> list[str]:
    return [line.strip() for line in str(text or "").splitlines() if line.strip() and "Emlis" not in line]


def _r5_tail_signature(line: str) -> str:
    normalized = str(line or "").strip(" 　、,。.!！?？")
    for suffix in (
        "表に出ています",
        "中心として書かれています",
        "書かれています",
        "残っています",
        "残されています",
        "重なっています",
        "混ざっています",
        "続いています",
        "ぶつかっています",
        "言葉になっています",
        "形になっています",
        "大きく響いています",
        "来ています",
        "あります",
    ):
        if normalized.endswith(suffix):
            return suffix
    return normalized[-12:]


@pytest.mark.parametrize("case", PHASE8_CASES, ids=[case["case_id"] for case in PHASE8_CASES])
def test_phase8_real_input_profiles_and_output_quality(case):
    candidate, evidence, scope = _candidate_for(case)
    assert detect_phase8_profile(evidence) == case["expected_profile"]

    if not case["expected_passed"]:
        assert candidate["composer_source"] == "unavailable"
        assert candidate["comment_text"] == ""
        assert "short_ambiguous" in " ".join(candidate.get("rejection_reasons") or [candidate.get("composer_meta", {}).get("profile_key", "")])
        return

    assert scope.scope_status == "eligible"
    assert candidate["composer_source"] == "ai_generated"
    assert candidate["composer_model"] == "cocolon_limited_composer.v1"
    assert candidate["comment_text"]
    assert candidate["composer_meta"]["profile_key"] == case["expected_profile"]
    assert candidate["composer_meta"]["body_line_count"] >= 2

    text = candidate["comment_text"]
    compact = _compact(text)
    for forbidden in PHASE8_FORBIDDEN_SURFACES:
        assert forbidden not in text
    for alternatives in case["must_contain_any"]:
        assert any(_compact(term) in compact for term in alternatives), (case["case_id"], alternatives, text)

    guard = guard_template_echo(
        comment_text=text,
        evidence_spans=evidence,
        composer_source=candidate["composer_source"],
        composer_model=candidate["composer_model"],
        generation_method=candidate["generation_method"],
        generation_scope=candidate["generation_scope"],
        coverage_scope=candidate["coverage_scope"],
        composer_meta=candidate["composer_meta"],
        used_evidence_span_ids=candidate["used_evidence_span_ids"],
    )
    assert guard.passed is True
    assert not guard.phase8_quality_rejection_reasons


def test_phase8_current_bad_outputs_are_rejected_by_guard():
    evidence = build_evidence_ledger(_current_input(PHASE8_CASES[-1]))
    bad_outputs = [
        "Emlisです。\n不安。\nまた急に不安になったがつながっています。",
        "Emlisです。\n怒り。\nこっちはちゃんと考えて話してるのに、なんであがつながっています。",
        "Emlisです。\n自己理解。\n先のことを考え始めがつながっています。",
        "Emlisです。\n生活したい、そうしたらもっと悪化するが同じ中にあります。",
    ]
    for output in bad_outputs:
        guard = guard_template_echo(
            comment_text=output,
            evidence_spans=evidence,
            composer_source="ai_generated",
            composer_model="cocolon_limited_composer.v1",
            generation_method="scoped_graph_evidence_composer",
            generation_scope="scoped_graph_only",
            coverage_scope="partial_observation",
            composer_meta={"limited_composer": True},
            used_evidence_span_ids=[],
        )
        assert guard.passed is False
        assert any(str(reason).startswith("phase8_") for reason in guard.rejection_reasons)


def test_phase8_generalization_cases_are_registered_as_regression_fixtures():
    assert len(PHASE8_GENERALIZATION_CASES) == 6
    assert {case["expected_profile"] for case in PHASE8_GENERALIZATION_CASES} == {
        "mixed_positive_anxiety",
        "anger_hurt_boundary",
        "self_understanding_loop",
        "positive_progress",
        "relationship_approach_avoidance",
        "reality_escape_tension",
    }
    assert all(case.get("must_not_contain") for case in PHASE8_GENERALIZATION_CASES)


@pytest.mark.parametrize(
    "case",
    PHASE8_GENERALIZATION_CASES,
    ids=[case["case_id"] for case in PHASE8_GENERALIZATION_CASES],
)
def test_phase8_semantic_variants_are_not_example_phrase_dependent(case):
    candidate, evidence, scope = _candidate_for(case)

    assert detect_phase8_profile(evidence) == case["expected_profile"]
    assert scope.scope_status == "eligible"
    assert candidate["composer_source"] == "ai_generated"
    assert candidate["composer_model"] == "cocolon_limited_composer.v1"
    assert candidate["comment_text"]
    assert candidate["composer_meta"]["profile_key"] == case["expected_profile"]
    assert candidate["composer_meta"]["body_line_count"] >= 2

    text = candidate["comment_text"]
    compact = _compact(text)
    for forbidden in PHASE8_FORBIDDEN_SURFACES:
        assert forbidden not in text
    for forbidden in case.get("must_not_contain") or []:
        assert _compact(forbidden) not in compact, (case["case_id"], forbidden, text)
    for alternatives in case["must_contain_any"]:
        assert any(_compact(term) in compact for term in alternatives), (case["case_id"], alternatives, text)

    guard = guard_template_echo(
        comment_text=text,
        evidence_spans=evidence,
        composer_source=candidate["composer_source"],
        composer_model=candidate["composer_model"],
        generation_method=candidate["generation_method"],
        generation_scope=candidate["generation_scope"],
        coverage_scope=candidate["coverage_scope"],
        composer_meta=candidate["composer_meta"],
        used_evidence_span_ids=candidate["used_evidence_span_ids"],
    )
    assert guard.passed is True
    assert not guard.phase8_quality_rejection_reasons



PHASE8_R4_UNKNOWN_PROFILE_CASES = [
    {
        "case_id": "unknown_profile_shallow_work_walk_anxiety",
        "emotion": "不安",
        "category": "生活",
        "memo": """今日は仕事で疲れたけど、帰ってから少し散歩したら落ち着いた。
明日の準備もしたいけど、また失敗しそうで不安。""",
        "must_contain_any": [["仕事", "疲れ"], ["散歩", "落ち着"], ["失敗", "不安"]],
    },
    {
        "case_id": "unknown_profile_shallow_busy_day_small_action",
        "emotion": "不安",
        "category": "生活",
        "memo": """朝から予定が詰まっていて、昼過ぎにはもう集中が切れていた。
それでも少しだけ机を整えた。""",
        "must_contain_any": [["予定", "集中"], ["机", "整え"]],
    },
]


@pytest.mark.parametrize(
    "case",
    PHASE8_R4_UNKNOWN_PROFILE_CASES,
    ids=[case["case_id"] for case in PHASE8_R4_UNKNOWN_PROFILE_CASES],
)
def test_phase8_r4_unknown_profile_uses_shallow_current_input_core_path(case):
    candidate, evidence, scope = _candidate_for(case)

    assert detect_phase8_profile(evidence) == "unknown"
    assert scope.scope_status == "eligible"
    assert candidate["composer_source"] == "ai_generated"
    assert candidate["coverage_scope"] == "current_input_core"
    assert candidate["composer_meta"]["profile_key"] == "current_input_core"
    assert candidate["composer_meta"]["source_profile_key"] == "unknown"
    assert candidate["composer_meta"]["shallow_observation_path"] is True
    assert candidate["composer_meta"]["body_line_count"] >= 2
    assert candidate["used_evidence_span_ids"]

    text = candidate["comment_text"]
    compact = _compact(text)
    for forbidden in (*PHASE8_FORBIDDEN_SURFACES, "本当の願い", "性格", "診断", "治療", "あなた"):
        assert forbidden not in text
    for alternatives in case["must_contain_any"]:
        assert any(_compact(term) in compact for term in alternatives), (case["case_id"], alternatives, text)

    reader = judge_listener_readability(text)
    assert reader.understandable is True, reader.rejection_reasons

    grounding = judge_grounding(
        comment_text=text,
        graph=scope.scoped_graph,
        evidence_spans=evidence,
        allowed_evidence_span_ids=candidate["used_evidence_span_ids"],
        grounding_scope="limited_scoped_graph",
    )
    assert grounding.passed is True, grounding.rejection_reasons

    guard = guard_template_echo(
        comment_text=text,
        evidence_spans=evidence,
        composer_source=candidate["composer_source"],
        composer_model=candidate["composer_model"],
        generation_method=candidate["generation_method"],
        generation_scope=candidate["generation_scope"],
        coverage_scope=candidate["coverage_scope"],
        composer_meta=candidate["composer_meta"],
        used_evidence_span_ids=candidate["used_evidence_span_ids"],
    )
    assert guard.passed is True
    assert not guard.phase8_quality_rejection_reasons

def test_phase8_r5_realizer_uses_sentence_plan_parts_without_profile_branching():
    source = inspect.getsource(limited_composer_module._realize_sentence)
    source += inspect.getsource(limited_composer_module._surface_parts_for_plan)

    assert "profile.profile_key" not in source
    assert "if key ==" not in source
    assert "role_template" not in source


def test_phase8_r5_quality_guard_rejects_repeated_sentence_tail():
    evidence = build_evidence_ledger(_current_input(PHASE8_CASES[4]))
    output = "Emlisです。\n片付けられたことが残っています。\n気持ちが軽くなった感覚が残っています。"

    guard = guard_template_echo(
        comment_text=output,
        evidence_spans=evidence,
        composer_source="ai_generated",
        composer_model="cocolon_limited_composer.v1",
        generation_method="scoped_graph_evidence_composer",
        generation_scope="scoped_graph_only",
        coverage_scope="partial_observation",
        composer_meta={"limited_composer": True},
        used_evidence_span_ids=[],
    )

    assert guard.passed is False
    assert "phase8_repeated_sentence_tail" in guard.rejection_reasons


@pytest.mark.parametrize(
    "case",
    [case for case in PHASE8_CASES if case.get("expected_passed")] + PHASE8_GENERALIZATION_CASES + PHASE8_R4_UNKNOWN_PROFILE_CASES,
    ids=[case["case_id"] for case in [case for case in PHASE8_CASES if case.get("expected_passed")] + PHASE8_GENERALIZATION_CASES + PHASE8_R4_UNKNOWN_PROFILE_CASES],
)
def test_phase8_r5_generated_outputs_do_not_reuse_fixed_role_tails(case):
    candidate, evidence, _scope = _candidate_for(case)

    assert candidate["composer_source"] == "ai_generated"
    body_lines = _body_lines(candidate["comment_text"])
    signatures = [_r5_tail_signature(line) for line in body_lines]
    assert len(signatures) == len(set(signatures)), (case["case_id"], signatures, candidate["comment_text"])

    for old_tail in ("が出ています", "も出ています", "が残っています", "も書かれています"):
        assert candidate["comment_text"].count(old_tail) <= 1, (case["case_id"], old_tail, candidate["comment_text"])

    guard = guard_template_echo(
        comment_text=candidate["comment_text"],
        evidence_spans=evidence,
        composer_source=candidate["composer_source"],
        composer_model=candidate["composer_model"],
        generation_method=candidate["generation_method"],
        generation_scope=candidate["generation_scope"],
        coverage_scope=candidate["coverage_scope"],
        composer_meta=candidate["composer_meta"],
        used_evidence_span_ids=candidate["used_evidence_span_ids"],
    )
    assert guard.passed is True
    assert "phase8_repeated_sentence_tail" not in guard.rejection_reasons


def test_phase8_r6_quality_guard_rejects_template_and_example_replacement_meta_flags():
    evidence = build_evidence_ledger(_current_input(PHASE8_CASES[4]))
    output = "Mashさん、Emlisです。\n片付けられたことが書かれています。\nちゃんとできた嬉しさが形になっています。"

    guard = guard_template_echo(
        comment_text=output,
        evidence_spans=evidence,
        composer_source="ai_generated",
        composer_model="cocolon_limited_composer.v1",
        generation_method="scoped_graph_evidence_composer",
        generation_scope="scoped_graph_only",
        coverage_scope="partial_observation",
        composer_meta={
            "limited_composer": True,
            "phase8_quality_path": True,
            "profile_key": "positive_progress",
            "required_roles": ["small_action", "achievement"],
            "covered_roles": ["small_action", "achievement"],
            "role_template_used": True,
            "example_phrase_replacement_used": True,
        },
        used_evidence_span_ids=[span.span_id for span in evidence],
    )

    assert guard.passed is False
    assert "phase8_role_template_renderer_used" in guard.rejection_reasons
    assert "phase8_example_phrase_replacement_used" in guard.rejection_reasons


def test_phase8_r6_guard_rejects_known_profile_missing_must_keep_role_coverage():
    evidence = build_evidence_ledger(_current_input(PHASE8_CASES[0]))
    output = "Mashさん、Emlisです。\n友達と話せた楽しさが書かれています。\n笑えたことも重なっています。"

    guard = guard_template_echo(
        comment_text=output,
        evidence_spans=evidence,
        composer_source="ai_generated",
        composer_model="cocolon_limited_composer.v1",
        generation_method="scoped_graph_evidence_composer",
        generation_scope="scoped_graph_only",
        coverage_scope="partial_observation",
        composer_meta={
            "limited_composer": True,
            "profile_key": "mixed_positive_anxiety",
            "required_roles": ["positive_state", "anxiety_return"],
            "covered_roles": ["positive_state"],
        },
        used_evidence_span_ids=[getattr(span, "span_id", "") for span in evidence[:2]],
    )

    assert guard.passed is False
    assert "phase8_missing_must_keep_roles" in guard.rejection_reasons
    assert guard.phase8_missing_must_keep_roles == ["anxiety_return"]


def test_phase8_r6_guard_rejects_shallow_current_input_core_without_used_evidence():
    evidence = build_evidence_ledger(_current_input(PHASE8_R4_UNKNOWN_PROFILE_CASES[0]))
    output = "Mashさん、Emlisです。\n仕事で疲れたことが中心として書かれています。\n散歩して落ち着いたことも続いています。"

    guard = guard_template_echo(
        comment_text=output,
        evidence_spans=evidence,
        composer_source="ai_generated",
        composer_model="cocolon_limited_composer.v1",
        generation_method="scoped_graph_evidence_composer",
        generation_scope="scoped_graph_only",
        coverage_scope="current_input_core",
        composer_meta={"limited_composer": True, "profile_key": "current_input_core", "shallow_observation_path": True},
        used_evidence_span_ids=[],
    )

    assert guard.passed is False
    assert "phase8_missing_used_text_evidence" in guard.rejection_reasons


def test_phase8_r6_guard_rejects_shallow_overclaim_without_source_grounding():
    evidence = build_evidence_ledger(_current_input(PHASE8_R4_UNKNOWN_PROFILE_CASES[0]))
    used_ids = [getattr(span, "span_id", "") for span in evidence if getattr(span, "source_field", "") == "memo"][:2]
    output = "Mashさん、Emlisです。\n仕事で疲れたことが中心として書かれています。\n本当の願いや性格の問題も書かれています。"

    guard = guard_template_echo(
        comment_text=output,
        evidence_spans=evidence,
        composer_source="ai_generated",
        composer_model="cocolon_limited_composer.v1",
        generation_method="scoped_graph_evidence_composer",
        generation_scope="scoped_graph_only",
        coverage_scope="current_input_core",
        composer_meta={"limited_composer": True, "profile_key": "current_input_core", "shallow_observation_path": True},
        used_evidence_span_ids=used_ids,
    )

    assert guard.passed is False
    assert "phase8_shallow_overclaim" in guard.rejection_reasons
    assert "phase8_deep_overclaim" in guard.rejection_reasons


def test_phase8_r6_guard_rejects_raw_source_sentence_copy_as_quality_issue():
    evidence = build_evidence_ledger(_current_input(PHASE8_R4_UNKNOWN_PROFILE_CASES[0]))
    used_ids = [getattr(span, "span_id", "") for span in evidence if getattr(span, "source_field", "") == "memo"][:2]
    output = "Mashさん、Emlisです。\n今日は仕事で疲れたけど、帰ってから少し散歩したら落ち着いた。\n明日の準備もしたいけど、また失敗しそうで不安。"

    guard = guard_template_echo(
        comment_text=output,
        evidence_spans=evidence,
        composer_source="ai_generated",
        composer_model="cocolon_limited_composer.v1",
        generation_method="scoped_graph_evidence_composer",
        generation_scope="scoped_graph_only",
        coverage_scope="current_input_core",
        composer_meta={"limited_composer": True, "profile_key": "current_input_core", "shallow_observation_path": True},
        used_evidence_span_ids=used_ids,
    )

    assert guard.passed is False
    assert "phase8_raw_evidence_sentence_copy" in guard.rejection_reasons


@pytest.mark.parametrize(
    "case",
    [case for case in PHASE8_CASES if case.get("expected_passed")] + PHASE8_GENERALIZATION_CASES + PHASE8_R4_UNKNOWN_PROFILE_CASES,
    ids=[case["case_id"] for case in [case for case in PHASE8_CASES if case.get("expected_passed")] + PHASE8_GENERALIZATION_CASES + PHASE8_R4_UNKNOWN_PROFILE_CASES],
)
def test_phase8_r6_generated_outputs_pass_generic_quality_guard(case):
    candidate, evidence, _scope = _candidate_for(case)

    guard = guard_template_echo(
        comment_text=candidate["comment_text"],
        evidence_spans=evidence,
        composer_source=candidate["composer_source"],
        composer_model=candidate["composer_model"],
        generation_method=candidate["generation_method"],
        generation_scope=candidate["generation_scope"],
        coverage_scope=candidate["coverage_scope"],
        composer_meta=candidate["composer_meta"],
        used_evidence_span_ids=candidate["used_evidence_span_ids"],
    )

    assert guard.passed is True, (case["case_id"], guard.rejection_reasons, candidate["comment_text"])
    assert not guard.phase8_missing_must_keep_roles
    assert "phase8_shallow_overclaim" not in guard.rejection_reasons
    assert "phase8_raw_evidence_sentence_copy" not in guard.rejection_reasons



def test_phase8_regression_candidates_keep_common_core_meta_additive():
    cases = [case for case in PHASE8_CASES if case.get("expected_passed")] + PHASE8_GENERALIZATION_CASES + PHASE8_R4_UNKNOWN_PROFILE_CASES

    for case in cases:
        candidate, _evidence, _scope = _candidate_for(case)

        assert candidate["composer_source"] == "ai_generated"
        assert candidate["status"] == STATUS_GENERATED
        assert candidate["comment_text"]

        meta = candidate["composer_meta"]
        for preserved_key in (
            "limited_composer",
            "generation_scope",
            "external_ai_used",
            "phase8_quality_path",
            "profile_key",
            "covered_roles",
            "body_line_count",
            "phrase_unit_count",
            "phase8_quality",
        ):
            assert preserved_key in meta

        core_meta = meta["text_generation_core"]
        assert meta["core_text_generation"] == core_meta
        assert core_meta["adapter_name"] == COMMON_CORE_ADAPTER_NAME
        assert core_meta["core_id"] == CORE_ID_EMLIS
        assert core_meta["status"] == STATUS_GENERATED
        assert core_meta["passed"] is True
        assert core_meta["quality_flags"] == []
        assert core_meta["rejection_reasons"] == []
        assert set(core_meta["used_evidence_span_ids"]) == set(candidate["used_evidence_span_ids"])
        assert core_meta["payload"]["evidence_span_count"] > 0
        assert core_meta["payload"]["phrase_unit_count"] > 0
        assert core_meta["payload"]["sentence_plan_count"] > 0


@pytest.mark.asyncio
async def test_phase8_render_meta_marks_emlis_stop_point_before_piece_analysis(monkeypatch):
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED", "true")
    from emlis_ai_reply_service import render_emlis_ai_reply

    case = next(case for case in PHASE8_CASES if case["case_id"] == "real_user_reality_escape_tension")
    reply = await render_emlis_ai_reply(
        user_id="phase8-stop-point-user",
        subscription_tier="free",
        current_input=_current_input(case),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    multi = reply.meta["multi_perspective"]
    phase_gate = multi["phase_gate"]
    core_meta = multi["text_generation_core"]

    assert reply.meta["observation_status"] == "passed"
    assert reply.meta["display"]["visible_name"] == "Emlisの観測"
    assert reply.comment_text
    assert multi["core_text_generation"] == core_meta
    assert core_meta["adapter_name"] == COMMON_CORE_ADAPTER_NAME
    assert core_meta["core_id"] == CORE_ID_EMLIS
    assert core_meta["passed"] is True

    assert phase_gate["text_generation_core_ready"] is True
    assert phase_gate["text_generation_core_stop_point"] == TEXT_GENERATION_CORE_PHASE8_STOP_POINT
    assert phase_gate["text_generation_core_next_phase"] == TEXT_GENERATION_CORE_PHASE8_NEXT_PHASE
    assert phase_gate["text_generation_core_current_connected_core"] == CORE_ID_EMLIS
    assert phase_gate["piece_composer_connected"] is False
    assert phase_gate["analysis_composer_connected"] is False
    assert phase_gate["piece_analysis_text_generation_unstarted"] is True
