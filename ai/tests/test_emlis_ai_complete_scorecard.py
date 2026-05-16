from __future__ import annotations

from emlis_ai_complete_scorecard_service import (
    COMPLETE_COVERAGE_GROUP_ORDER,
    aggregate_complete_scorecard_events,
    build_complete_blind_qa_rubric,
    build_complete_initial_fixture_suite,
    build_complete_scorecard_contract_meta,
    build_complete_scorecard_harness,
    normalize_complete_scorecard_event,
)


def _event(group: str, *, displayed: bool, binding: bool = True, read_score=None, reasons=None, safety=0, template=0):
    return {
        "version": "emlis.complete_scorecard_event.v1",
        "event_kind": "complete_composer_initial_reply_attempt",
        "complete_candidate_seen": True,
        "complete_candidate_generated": True,
        "complete_candidate_displayed": displayed,
        "eligible_count": 1,
        "passed_display_count": 1 if displayed else 0,
        "candidate_generated_count": 1,
        "observation_status": "passed" if displayed else "rejected",
        "coverage_group": group,
        "coverage_scope": group,
        "binding_pass": binding,
        "binding_count": 2 if binding else 1,
        "used_evidence_span_count": 2,
        "used_phrase_unit_count": 2 if binding else 0,
        "used_relation_count": 1,
        "relation_types": ["coexistence"],
        "read_feeling_score": read_score,
        "safety_major_count": safety,
        "template_major_count": template,
        "gate_rejection_reasons": list(reasons or []),
        "top_rejection_reasons": list(reasons or []),
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
    }


def test_step12_fixture_suite_groups_complete_initial_cases_without_raw_text() -> None:
    suite = build_complete_initial_fixture_suite()

    assert suite["version"] == "emlis.complete_scorecard_fixture_suite.v1"
    assert suite["fixture_suite_ready"] is True
    assert tuple(suite["coverage_groups"]) == tuple(COMPLETE_COVERAGE_GROUP_ORDER)
    assert suite["fixture_count"] >= len(COMPLETE_COVERAGE_GROUP_ORDER)
    assert suite["missing_coverage_groups"] == []
    assert suite["raw_input_included"] is False
    assert suite["raw_text_included"] is False
    for case in suite["fixtures"]:
        assert case["coverage_group"] in COMPLETE_COVERAGE_GROUP_ORDER
        assert case["raw_input_included"] is False
        assert case["raw_text_included"] is False
        assert "raw_text" not in case
        assert case["target_relations"]


def test_step12_normalizes_step11_scorecard_event_and_sanitizes_text_payload() -> None:
    normalized = normalize_complete_scorecard_event(
        {
            "complete_scorecard_event": {
                **_event("pressure", displayed=False, binding=False, reasons=["unsupported_sentence", "raw_echo"]),
                "comment_text": "should not leak",
                "raw_input": "should not leak",
            }
        }
    )

    assert normalized["version"] == "emlis.complete_scorecard_normalized_event.v1"
    assert normalized["coverage_group"] == "pressure"
    assert normalized["eligible_count"] == 1
    assert normalized["passed_display_count"] == 0
    assert normalized["binding_pass"] is False
    assert normalized["template_major_count"] >= 1
    assert normalized["raw_input_included"] is False
    assert normalized["raw_text_included"] is False
    assert normalized["comment_text_included"] is False
    assert "raw_input" not in normalized
    assert "comment_text" not in normalized


def test_step12_aggregate_tracks_display_binding_read_feeling_safety_and_template() -> None:
    aggregate = aggregate_complete_scorecard_events(
        [
            _event("short_daily", displayed=True, binding=True, read_score=1.0),
            _event("pressure", displayed=True, binding=True, read_score=0.8),
            _event("relationship", displayed=False, binding=False, read_score=0.4, reasons=["unsupported_sentence"], template=1),
        ]
    )

    assert aggregate["version"] == "emlis.complete_scorecard_aggregate.v1"
    assert aggregate["record_count"] == 3
    assert round(aggregate["display_reach_rate"], 4) == 0.6667
    assert round(aggregate["binding_pass_rate"], 4) == 0.6667
    assert round(aggregate["read_feeling_pass_rate"], 4) == 0.6667
    assert aggregate["template_major_count"] if "template_major_count" in aggregate else aggregate["totals"]["template_major_count"] >= 1
    assert "binding_target_not_met" in aggregate["release_blockers"]
    assert aggregate["by_coverage_group"]["relationship"]["passed_display_count"] == 0
    assert "relationship" in aggregate["groups_with_events"]
    assert aggregate["raw_input_included"] is False
    assert aggregate["display_gate_relaxed"] is False


def test_step12_blind_qa_rubric_is_present_without_comment_or_raw_input() -> None:
    rubric = build_complete_blind_qa_rubric()

    assert rubric["version"] == "emlis.complete_blind_qa_rubric.v1"
    assert set(rubric["dimensions"]) == {
        "input_specific_structure_reflected",
        "relation_kept",
        "evidence_bound",
        "natural_but_not_template",
        "no_diagnosis_or_personality_claim",
    }
    all_checks = {
        check
        for dimension in rubric["dimensions"].values()
        for check in dimension.get("checks", [])
    }
    assert "input_specific_structure_reflected" in all_checks
    assert "sentence_binding_present" in all_checks
    assert "no_fixed_output" in all_checks
    assert rubric["read_feeling_initial_target"] == 0.8
    assert rubric["read_feeling_product_target"] == 0.9
    assert rubric["exact_comment_text_locked"] is False
    assert rubric["raw_input_included"] is False
    assert rubric["comment_text_included"] is False


def test_step12_harness_combines_event_fixture_suite_and_contract_meta() -> None:
    harness = build_complete_scorecard_harness(
        scorecard_event=_event("recovery", displayed=True, binding=True),
        records=[_event("conflict", displayed=False, binding=False, reasons=["relation_not_expressed"])],
    )
    contract = build_complete_scorecard_contract_meta()

    assert harness["version"] == "emlis.complete_scorecard_harness.v1"
    assert harness["scorecard_ready"] is True
    assert harness["fixture_suite"]["fixture_suite_ready"] is True
    assert harness["coverage_group"] == "recovery"
    assert harness["coverage_group_scorecard"]["passed_display_count"] == 1
    assert harness["aggregate"]["record_count"] == 2
    assert harness["ready_for_step13_rn_contract_regression"] is True
    assert harness["comment_text_contract"] == "passed_only"
    assert harness["response_shape_changed"] is False
    assert harness["raw_input_included"] is False
    assert harness["external_ai_allowed"] is False
    assert contract["fixture_suite_added"] is True
