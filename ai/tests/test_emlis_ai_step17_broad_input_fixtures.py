# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step17 broad-input fixture tests for EmlisAI B-R1.

The contract here is intentionally structural.  These tests do not lock exact
Emlis observation sentences; they verify coverage scope, evidence grounding via
used_evidence_span_ids, common Core quality flags, forbidden surfaces, and
history / cross-core boundary separation.
"""

from typing import Any

import pytest

from cocolon_text_generation_core.adapters.emlis_observation_composer import ADAPTER_NAME
from emlis_ai_conversation_composer_service import build_conversation_composer_payload
from emlis_ai_coverage_matrix_service import build_emlis_coverage_matrix
from emlis_ai_evidence_ledger_service import build_evidence_ledger
from emlis_ai_limited_composer_client import CocolonLimitedComposerClient
from emlis_ai_limited_observation_scope_service import build_limited_observation_scope
from emlis_ai_limited_sentence_quality_guard import detect_phase8_profile
from emlis_ai_observation_integrator_service import integrate_perspective_board
from emlis_ai_perspective_board import build_perspective_board
from emlis_ai_perspective_observers import run_perspective_observers
from emlis_ai_template_echo_guard import guard_template_echo
from emlis_ai_types import EvidenceSpan
from fixtures.emlis_ai_step17_broad_input_cases import (
    STEP17_BROAD_DAILY_INPUT_CASES,
    STEP17_CONTEXT_SCOPE_CASES,
    STEP17_FIXTURE_VERSION,
    STEP17_FORBIDDEN_SURFACES,
    STEP17_GENERAL_KNOWLEDGE_COMPLETION_BAD_OUTPUTS,
    STEP17_LONG_MEANING_ARC_CASE,
    STEP17_REQUIRED_COVERAGE_GROUPS,
    STEP17_REQUIRED_INPUT_AREAS,
    STEP17_SURFACE_VARIATION_SERIES,
)


def _current_input(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": case["case_id"],
        "created_at": "2026-05-15T00:00:00Z",
        "memo": case["memo"],
        "memo_action": "",
        "emotion_details": [{"type": case.get("emotion") or "自己理解", "strength": "medium"}],
        "emotions": [case.get("emotion") or "自己理解"],
        "category": [case.get("category") or "生活"],
    }


def _external_spans(case: dict[str, Any]) -> list[EvidenceSpan]:
    spans: list[EvidenceSpan] = []
    for raw in case.get("external_context_spans") or []:
        text = str(raw["raw_text"])
        spans.append(
            EvidenceSpan(
                span_id=str(raw["span_id"]),
                raw_text=text,
                start_index=0,
                end_index=len(text),
                detected_type=str(raw.get("detected_type") or "context"),
                confidence=1.0,
                source_field=str(raw.get("source_field") or "history"),
            )
        )
    return spans


def _build_candidate(case: dict[str, Any], *, include_external_context: bool = False):
    current_input = _current_input(case)
    current_evidence = build_evidence_ledger(current_input)
    reports = run_perspective_observers(current_evidence)
    board = build_perspective_board(evidence_spans=current_evidence, reports=reports)
    graph = integrate_perspective_board(board=board, display_name="Mash")
    scope = build_limited_observation_scope(graph=graph, evidence_spans=current_evidence)
    evidence_for_payload = [*current_evidence, *(_external_spans(case) if include_external_context else [])]
    payload = build_conversation_composer_payload(
        graph=scope.scoped_graph,
        evidence_spans=evidence_for_payload,
        display_name="Mash",
        greeting_text="Emlisです。",
        trace_id=case["case_id"],
        limited_observation_scope=scope,
    )
    candidate = CocolonLimitedComposerClient().generate(payload)
    current_evidence_ids = {span.span_id for span in current_evidence}
    external_evidence_ids = {span.span_id for span in evidence_for_payload if span.span_id not in current_evidence_ids}
    return candidate, current_evidence, scope, current_evidence_ids, external_evidence_ids


def _assert_structural_candidate(
    case: dict[str, Any],
    candidate: dict[str, Any],
    current_evidence: list[EvidenceSpan],
    scope: Any,
    current_evidence_ids: set[str],
) -> None:
    assert detect_phase8_profile(current_evidence) == case["expected_profile"]
    assert scope.scope_status == "eligible"
    assert candidate["composer_source"] == "ai_generated"
    assert candidate["composer_model"] == "cocolon_limited_composer.v1"
    assert candidate["coverage_scope"] == case["expected_coverage_scope"]
    assert candidate["comment_text"].strip()
    assert candidate["used_evidence_span_ids"]
    assert set(candidate["used_evidence_span_ids"]).issubset(current_evidence_ids)
    assert len(set(candidate["used_evidence_span_ids"]) & current_evidence_ids) >= int(case.get("min_used_current_evidence") or 1)

    meta = candidate["composer_meta"]
    assert meta["profile_key"] == case["expected_profile"]
    if "fixed_observation_sentence_added" in meta:
        assert meta["fixed_observation_sentence_added"] is False
    assert meta["external_ai_used"] is False
    assert meta["phase8_quality"]["passed"] is True
    assert not meta["phase8_quality"]["rejection_reasons"]

    surface = meta["step13_surface_realizer"]
    assert surface["grammar_parts_only"] is True
    assert surface["completion_sentence_templates_added"] is False
    assert surface["example_sentence_match_used"] is False
    assert surface["tail_variation_enabled"] is True
    assert not surface["repeated_tail_keys"]

    core = meta["text_generation_core"]
    assert core["adapter_name"] == ADAPTER_NAME
    assert core["passed"] is True
    assert set(core["used_evidence_span_ids"]) == set(candidate["used_evidence_span_ids"])
    assert core["coverage_scope"] == candidate["coverage_scope"]
    assert core["quality_flags"] == []
    assert core["rejection_reasons"] == []
    assert core["payload"]["evidence_span_count"] >= int(case.get("min_used_current_evidence") or 1)
    assert core["result"]["quality_flags"] == []
    assert core["result"]["rejection_reasons"] == []

    for forbidden in STEP17_FORBIDDEN_SURFACES:
        assert forbidden not in candidate["comment_text"]

    template_guard = guard_template_echo(
        comment_text=candidate["comment_text"],
        evidence_spans=current_evidence,
        composer_source=candidate["composer_source"],
        composer_model=candidate["composer_model"],
        generation_method=candidate["generation_method"],
        generation_scope=candidate["generation_scope"],
        coverage_scope=candidate["coverage_scope"],
        composer_meta=candidate["composer_meta"],
        used_evidence_span_ids=candidate["used_evidence_span_ids"],
    )
    assert template_guard.passed is True, template_guard.rejection_reasons


def test_step17_fixture_registry_covers_required_input_areas_without_exact_text_contracts() -> None:
    cases = [*STEP17_BROAD_DAILY_INPUT_CASES, STEP17_LONG_MEANING_ARC_CASE, *STEP17_CONTEXT_SCOPE_CASES]
    covered = {case["input_area"] for case in cases}
    coverage_groups = {group for case in cases for group in case.get("required_coverage_groups", [])}

    assert STEP17_FIXTURE_VERSION == "emlis.step17_broad_input_fixtures.v1"
    assert set(STEP17_REQUIRED_INPUT_AREAS).issubset(covered)
    assert set(STEP17_REQUIRED_COVERAGE_GROUPS).issubset(coverage_groups)
    assert all("expected_comment_text" not in case for case in cases)
    assert all("must_equal_text" not in case for case in cases)
    assert all(case.get("min_used_current_evidence", 0) >= 1 for case in cases)


@pytest.mark.parametrize("case", STEP17_BROAD_DAILY_INPUT_CASES, ids=[case["case_id"] for case in STEP17_BROAD_DAILY_INPUT_CASES])
def test_step17_broad_daily_inputs_pass_by_structure_not_exact_sentence(case: dict[str, Any]) -> None:
    candidate, current_evidence, scope, current_ids, _external_ids = _build_candidate(case)
    _assert_structural_candidate(case, candidate, current_evidence, scope, current_ids)

    coverage = build_emlis_coverage_matrix(
        diagnostic_summary={"observation_status": "passed", "stage": "display", "primary_reason": "passed"},
        current_input=_current_input(case),
    )
    for group in case["required_coverage_groups"]:
        assert group in coverage["coverage_groups"], (case["case_id"], group, coverage["coverage_groups"])


def test_step17_long_meaning_arc_fixture_uses_multiple_current_spans_and_common_core_guards() -> None:
    case = STEP17_LONG_MEANING_ARC_CASE
    candidate, current_evidence, scope, current_ids, _external_ids = _build_candidate(case)
    _assert_structural_candidate(case, candidate, current_evidence, scope, current_ids)

    meta = candidate["composer_meta"]
    assert meta["profile_key"] == "long_meaning_arc"
    assert meta["body_line_count"] >= case["min_body_lines"]
    assert meta["sentence_plan_count"] >= case["min_sentence_plans"]
    assert len(candidate["used_evidence_span_ids"]) >= case["min_used_current_evidence"]

    surface = meta["step13_surface_realizer"]
    assert surface["length_mode"] == "long"
    assert surface["line_count"] >= case["min_sentence_plans"]
    assert surface["relation_aware"] is True
    assert surface["role_aware"] is True

    core = meta["text_generation_core"]
    assert core["payload"]["sentence_plan_count"] >= case["min_sentence_plans"]
    assert core["payload"]["phrase_unit_count"] >= case["min_used_current_evidence"]
    assert core["quality_flags"] == []


@pytest.mark.parametrize("case", STEP17_CONTEXT_SCOPE_CASES, ids=[case["case_id"] for case in STEP17_CONTEXT_SCOPE_CASES])
def test_step17_history_and_cross_core_context_stay_outside_current_observation_grounding(case: dict[str, Any]) -> None:
    candidate, current_evidence, scope, current_ids, external_ids = _build_candidate(case, include_external_context=True)
    _assert_structural_candidate(case, candidate, current_evidence, scope, current_ids)

    assert external_ids
    assert set(candidate["used_evidence_span_ids"]).isdisjoint(external_ids)
    assert set(candidate["composer_meta"]["text_generation_core"]["used_evidence_span_ids"]).isdisjoint(external_ids)

    for span in case["external_context_spans"]:
        assert span["span_id"] in external_ids
        for term in span["must_not_surface_terms"]:
            assert term not in candidate["comment_text"]


def test_step17_surface_variation_series_does_not_repeat_one_fixed_template() -> None:
    outputs: list[str] = []
    tail_sequences: list[tuple[str, ...]] = []

    for case in STEP17_SURFACE_VARIATION_SERIES:
        candidate, current_evidence, scope, current_ids, _external_ids = _build_candidate(case)
        _assert_structural_candidate(
            {
                **case,
                "expected_coverage_scope": candidate["coverage_scope"],
                "required_coverage_groups": [],
                "min_used_current_evidence": 1,
            },
            candidate,
            current_evidence,
            scope,
            current_ids,
        )
        outputs.append(candidate["comment_text"])
        tail_sequences.append(tuple(candidate["composer_meta"]["step13_surface_realizer"]["used_tail_keys"]))

    assert len(set(outputs)) == len(outputs)
    assert len(set(tail_sequences)) == len(tail_sequences)
    for sequence in tail_sequences:
        assert len(sequence) == len(set(sequence))


@pytest.mark.parametrize(
    "bad_output",
    STEP17_GENERAL_KNOWLEDGE_COMPLETION_BAD_OUTPUTS,
    ids=[case["case_id"] for case in STEP17_GENERAL_KNOWLEDGE_COMPLETION_BAD_OUTPUTS],
)
def test_step17_no_general_knowledge_completion_guard_fixture_rejects_unbacked_output(bad_output: dict[str, Any]) -> None:
    current_evidence = build_evidence_ledger(_current_input(STEP17_BROAD_DAILY_INPUT_CASES[0]))
    guard = guard_template_echo(
        comment_text=bad_output["comment_text"],
        evidence_spans=current_evidence,
        composer_source="ai_generated",
        composer_model="cocolon_limited_composer.v1",
        generation_method="scoped_graph_evidence_composer",
        generation_scope="scoped_graph_only",
        coverage_scope="partial_observation",
        composer_meta={"limited_composer": True, "profile_key": "current_input_core", "shallow_observation_path": True},
        used_evidence_span_ids=[span.span_id for span in current_evidence[:2]],
    )

    assert guard.passed is False
    assert any(reason in guard.rejection_reasons for reason in bad_output["expected_reasons_any"]), guard.rejection_reasons
