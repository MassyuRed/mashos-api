# -*- coding: utf-8 -*-
from __future__ import annotations

import json

import pytest

from emlis_ai_complete_surface_quality_signature import build_surface_quality_signature
from emlis_ai_runtime_surface_pre_return_gate import (
    ACTION_ALLOW,
    ACTION_BLOCK,
    ACTION_RERENDER_SHALLOW_V2,
    RUNTIME_SURFACE_PRE_RETURN_GATE_ACTIONS,
    RUNTIME_SURFACE_PRE_RETURN_GATE_VERSION,
    assert_runtime_surface_pre_return_gate_meta_only,
    build_runtime_surface_pre_return_gate_contract_meta,
    build_runtime_surface_pre_return_gate_contract_schema,
    build_runtime_surface_pre_return_gate_report,
    dump_runtime_surface_pre_return_gate_report,
)
from fixtures.emlis_ai_runtime_surface_red_fixtures import (
    RUNTIME_SURFACE_BASELINE_RED_FIXTURES,
    RUNTIME_SURFACE_PRODUCT_RED_INVENTORY_FIXTURES,
    RUNTIME_SURFACE_PRODUCT_RED_INVENTORY_VERSION,
    RUNTIME_SURFACE_RED_FIXTURE_VERSION,
)
from fixtures.emlis_ai_visible_surface_acceptance_fixtures import (
    VISIBLE_SURFACE_ACCEPTANCE_SCREENSHOT_INVENTORY,
)

_NATURAL_SURFACE = (
    "Emlisです。\n"
    "今は、自分の特技を探そうとしている感じが出ています。\n"
    "好きで続けているものはあるのに、それを得意と呼べるかで止まっているように見えます。"
)


def _visible_surface_fixture_by_id(fixture_id: str):
    for fixture in VISIBLE_SURFACE_ACCEPTANCE_SCREENSHOT_INVENTORY:
        if fixture.fixture_id == fixture_id:
            return fixture
    raise AssertionError(f"visible surface fixture not found: {fixture_id}")




def _environment_state_output_runtime_meta() -> dict[str, object]:
    return {
        "profile_key": "current_input_core",
        "composer_source": "ai_generated",
        "shallow_observation_path": True,
        "environment_state_output_frame_limited_use": True,
        "environment_state_output_surface_contract": {
            "connected": True,
            "single_record_only": True,
            "scope_marker_required": True,
            "required_scope_marker": "今回の入力では",
            "allowed_scope_markers": ["今回の入力では", "今の入力では", "この入力では", "今回の記録では", "この記録では"],
            "allowed_surface_claim_strength": "single_observation",
            "forbidden_surface_claims": [
                "period_tendency_from_single_record",
                "personality_tendency",
                "diagnosis",
                "cause_from_category",
                "cause_from_emotion_strength",
                "recovery_prescription",
            ],
        },
    }


def test_phase4_runtime_gate_allows_completed_environment_state_output_marker_candidate_only() -> None:
    report = build_runtime_surface_pre_return_gate_report(
        comment_text="今回の入力では、仕事という場面で不安が置かれています。",
        composer_meta=_environment_state_output_runtime_meta(),
    )

    assert report["passed"] is True
    assert report["action"] == ACTION_ALLOW
    assert report["environment_state_output_runtime_double_check_active"] is True
    assert report["environment_state_output_runtime_marker_check_performed"] is True
    assert report["environment_state_output_scope_marker_present"] is True
    assert report["environment_state_output_terminal_surface_block"] is False
    assert report["environment_state_output_surface_rejection_reasons"] == []
    assert report["display_gate_relaxed"] is False
    assert_runtime_surface_pre_return_gate_meta_only(report)


def test_phase4_runtime_gate_blocks_uncompleted_environment_state_output_marker_without_rerendering() -> None:
    report = build_runtime_surface_pre_return_gate_report(
        comment_text="仕事という場面で不安が置かれています。",
        composer_meta=_environment_state_output_runtime_meta(),
        rerender_allowed=True,
    )

    assert report["passed"] is False
    assert report["action"] == ACTION_BLOCK
    assert report["rerender_recommended"] is False
    assert report["environment_state_output_runtime_double_check_active"] is True
    assert report["environment_state_output_runtime_marker_check_performed"] is True
    assert report["environment_state_output_scope_marker_present"] is False
    assert report["environment_state_output_terminal_surface_block"] is True
    assert "environment_state_output_scope_marker_missing" in report["rejection_reasons"]
    assert "environment_state_output_scope_marker_missing" in report["environment_state_output_surface_rejection_reasons"]
    assert report["display_gate_relaxed"] is False
    assert_runtime_surface_pre_return_gate_meta_only(report)


def test_phase4_runtime_gate_blocks_environment_state_output_when_marker_cannot_be_verified_from_signature_only() -> None:
    signature = build_surface_quality_signature(
        comment_text="今回の入力では、仕事という場面で不安が置かれています。"
    )

    report = build_runtime_surface_pre_return_gate_report(
        surface_quality_signature=signature,
        composer_meta=_environment_state_output_runtime_meta(),
        rerender_allowed=True,
    )

    assert report["surface_signature_ready"] is True
    assert report["passed"] is False
    assert report["action"] == ACTION_BLOCK
    assert report["rerender_recommended"] is False
    assert report["environment_state_output_runtime_marker_check_performed"] is True
    assert report["environment_state_output_scope_marker_present"] is False
    assert report["environment_state_output_terminal_surface_block"] is True
    assert "environment_state_output_scope_marker_missing" in report["rejection_reasons"]
    assert report["display_gate_relaxed"] is False
    assert_runtime_surface_pre_return_gate_meta_only(report)


def test_phase4_runtime_gate_blocks_forbidden_environment_state_output_claim_even_when_rerender_allowed() -> None:
    report = build_runtime_surface_pre_return_gate_report(
        comment_text="今回の入力では、これは不安障害の症状です。",
        composer_meta=_environment_state_output_runtime_meta(),
        rerender_allowed=True,
    )

    assert report["passed"] is False
    assert report["action"] == ACTION_BLOCK
    assert report["rerender_recommended"] is False
    assert report["environment_state_output_scope_marker_present"] is True
    assert report["environment_state_output_terminal_surface_block"] is True
    assert "diagnosis_surface" in report["rejection_reasons"]
    assert report["diagnosis_surface_blocked"] is True
    assert report["display_gate_relaxed"] is False
    assert_runtime_surface_pre_return_gate_meta_only(report)

def test_step0_baseline_red_fixtures_are_fixed_without_good_sentence_locking() -> None:
    assert RUNTIME_SURFACE_RED_FIXTURE_VERSION == "emlis.runtime_surface_red_fixtures.v2"
    assert len(RUNTIME_SURFACE_BASELINE_RED_FIXTURES) >= 5
    assert len({fixture.fixture_id for fixture in RUNTIME_SURFACE_BASELINE_RED_FIXTURES}) == len(RUNTIME_SURFACE_BASELINE_RED_FIXTURES)

    for fixture in RUNTIME_SURFACE_BASELINE_RED_FIXTURES:
        assert fixture.expected_public_status_after_step1 == "not_passed"
        assert fixture.expected_action == ACTION_RERENDER_SHALLOW_V2
        assert fixture.expected_rejection_reasons
        assert fixture.forbidden_surface_markers
        # Step 0 locks bad surfaces only. It does not prescribe a replacement
        # body, so future realizer work remains free to improve wording.
        assert not hasattr(fixture, "expected_good_body")


def test_step1_runtime_surface_product_red_inventory_locks_koto_splice_without_good_sentence_locking() -> None:
    assert RUNTIME_SURFACE_PRODUCT_RED_INVENTORY_VERSION == "emlis.runtime_surface_product_red_inventory.v1.20260524"
    assert len(RUNTIME_SURFACE_PRODUCT_RED_INVENTORY_FIXTURES) >= 3
    assert len({fixture.fixture_id for fixture in RUNTIME_SURFACE_PRODUCT_RED_INVENTORY_FIXTURES}) == len(RUNTIME_SURFACE_PRODUCT_RED_INVENTORY_FIXTURES)

    fixture_ids = {fixture.fixture_id for fixture in RUNTIME_SURFACE_PRODUCT_RED_INVENTORY_FIXTURES}
    assert "runtime_surface_red_conditional_koto_splice_20260524" in fixture_ids
    assert "runtime_surface_red_prediction_noun_koto_splice_20260524" in fixture_ids
    assert "runtime_surface_red_long_clause_koto_attachment_20260524" in fixture_ids

    for fixture in RUNTIME_SURFACE_PRODUCT_RED_INVENTORY_FIXTURES:
        assert fixture.expected_public_status_after_step1 == "not_passed"
        assert fixture.expected_action == ACTION_RERENDER_SHALLOW_V2
        assert fixture.expected_rejection_reasons
        assert fixture.forbidden_surface_markers
        assert fixture.composer_meta.get("composer_source") == "ai_generated"
        assert fixture.composer_meta.get("shallow_observation_path") is True
        # Step 1 adds inventory only.  It does not prescribe a replacement
        # body and does not add a runtime special case.
        assert not hasattr(fixture, "expected_good_body")

    conditional = next(
        fixture
        for fixture in RUNTIME_SURFACE_PRODUCT_RED_INVENTORY_FIXTURES
        if fixture.fixture_id == "runtime_surface_red_conditional_koto_splice_20260524"
    )
    assert "malformed_nominalization_conditional_fragment" in conditional.expected_rejection_reasons
    assert "取らなければこと" in conditional.forbidden_surface_markers

    prediction = next(
        fixture
        for fixture in RUNTIME_SURFACE_PRODUCT_RED_INVENTORY_FIXTURES
        if fixture.fixture_id == "runtime_surface_red_prediction_noun_koto_splice_20260524"
    )
    assert "malformed_nominalization_prediction_noun_fragment" in prediction.expected_rejection_reasons
    assert "予感こと" in prediction.forbidden_surface_markers


def test_step1_runtime_surface_pre_return_gate_blocks_all_baseline_red_fixtures() -> None:
    for fixture in RUNTIME_SURFACE_BASELINE_RED_FIXTURES:
        report = build_runtime_surface_pre_return_gate_report(
            comment_text=fixture.public_body,
            composer_meta=fixture.composer_meta,
        )

        assert report["version"] == RUNTIME_SURFACE_PRE_RETURN_GATE_VERSION
        assert report["evaluated"] is True
        assert report["passed"] is False
        assert report["blocked"] is True
        assert report["action"] == ACTION_RERENDER_SHALLOW_V2
        assert report["rerender_recommended"] is True
        assert report["display_gate_relaxed"] is False
        assert report["rn_visible_contract_changed"] is False
        assert set(fixture.expected_rejection_reasons).issubset(set(report["rejection_reasons"]))
        assert_runtime_surface_pre_return_gate_meta_only(report)

        dumped = dump_runtime_surface_pre_return_gate_report(report)
        payload = json.loads(dumped)
        assert payload["comment_text_body_included"] is False
        assert payload["raw_input_included"] is False
        for marker in fixture.forbidden_surface_markers:
            assert marker not in dumped



def test_step3_runtime_surface_pre_return_gate_blocks_product_red_inventory_with_koto_splice_codes() -> None:
    for fixture in RUNTIME_SURFACE_PRODUCT_RED_INVENTORY_FIXTURES:
        report = build_runtime_surface_pre_return_gate_report(
            comment_text=fixture.public_body,
            composer_meta=fixture.composer_meta,
            # Step 3 must catch the full candidate surface even when upstream
            # material-stage meta did not supply the new koto-splice codes.
            phrase_unit_grammar_meta={"malformed_phrase_unit_count": 0, "grammar_warning_codes": []},
        )

        assert report["evaluated"] is True
        assert report["passed"] is False
        assert report["blocked"] is True
        assert report["action"] == ACTION_RERENDER_SHALLOW_V2
        assert report["rerender_recommended"] is True
        assert report["malformed_phrase_unit_count"] >= 1
        assert report["malformed_nominalization_risk"] is True
        assert report["koto_splice_detected"] is True
        assert report["koto_splice_codes"]
        assert "malformed_phrase_unit" in report["rejection_reasons"]
        assert_runtime_surface_pre_return_gate_meta_only(report)

        expected_runtime_reasons = [
            reason
            for reason in fixture.expected_rejection_reasons
            # relation skeleton is a Visible Surface Acceptance concern in the
            # next step; Runtime Step 3 only locks the malformed koto surface.
            if reason != "surface_relation_skeleton_major"
        ]
        assert set(expected_runtime_reasons).issubset(set(report["rejection_reasons"]))

        dumped = dump_runtime_surface_pre_return_gate_report(report)
        payload = json.loads(dumped)
        assert payload["comment_text_body_included"] is False
        assert payload["raw_input_included"] is False
        assert payload["koto_splice_detected"] is True
        for marker in fixture.forbidden_surface_markers:
            assert marker not in dumped


def test_step3_runtime_surface_pre_return_gate_uses_precomputed_signature_koto_codes_without_candidate_body() -> None:
    fixture = next(
        item
        for item in RUNTIME_SURFACE_PRODUCT_RED_INVENTORY_FIXTURES
        if item.fixture_id == "runtime_surface_red_conditional_koto_splice_20260524"
    )
    signature = build_surface_quality_signature(comment_text=fixture.public_body)

    assert "malformed_nominalization_conditional_fragment" in signature["surface_malformed_nominalization_codes"]
    assert "residual_koto_splice_fragment" in signature["surface_malformed_nominalization_codes"]
    assert signature["malformed_phrase_unit_count"] >= 1

    report = build_runtime_surface_pre_return_gate_report(
        surface_quality_signature=signature,
        composer_meta=fixture.composer_meta,
    )

    assert report["passed"] is False
    assert report["action"] == ACTION_RERENDER_SHALLOW_V2
    assert report["koto_splice_detected"] is True
    assert "malformed_phrase_unit" in report["rejection_reasons"]
    assert "malformed_nominalization_conditional_fragment" in report["rejection_reasons"]
    assert "residual_koto_splice_fragment" in report["rejection_reasons"]
    dumped = dump_runtime_surface_pre_return_gate_report(report)
    assert "取らなければこと" not in dumped
    assert '"comment_text"' not in dumped


def test_step3_runtime_surface_pre_return_gate_blocks_after_rerender_attempt_or_when_rerender_disallowed() -> None:
    fixture = next(
        item
        for item in RUNTIME_SURFACE_PRODUCT_RED_INVENTORY_FIXTURES
        if item.fixture_id == "runtime_surface_red_prediction_noun_koto_splice_20260524"
    )

    already_attempted = build_runtime_surface_pre_return_gate_report(
        comment_text=fixture.public_body,
        composer_meta=fixture.composer_meta,
        rerender_attempted=True,
    )
    assert already_attempted["passed"] is False
    assert already_attempted["action"] == "block"
    assert already_attempted["rerender_recommended"] is False
    assert "malformed_nominalization_prediction_noun_fragment" in already_attempted["rejection_reasons"]

    disallowed = build_runtime_surface_pre_return_gate_report(
        comment_text=fixture.public_body,
        composer_meta=fixture.composer_meta,
        rerender_allowed=False,
    )
    assert disallowed["passed"] is False
    assert disallowed["action"] == "block"
    assert disallowed["rerender_recommended"] is False
    assert "malformed_nominalization_prediction_noun_fragment" in disallowed["rejection_reasons"]


@pytest.mark.parametrize(
    "safe_surface",
    (
        "Emlisです。\n今は、しなければならないことを一つずつ見ようとしています。",
        "Emlisです。\n今は、予感があることも含めて慎重に見ようとしています。",
        "Emlisです。\n今は、予定のことを急がず整理しようとしています。",
        "Emlisです。\n今は、必要なことを小さく置こうとしています。",
        "Emlisです。\n今は、感じたことを残そうとしているように見えます。",
    ),
)
def test_step3_runtime_surface_pre_return_gate_does_not_flag_safe_koto_nominalizations(safe_surface: str) -> None:
    report = build_runtime_surface_pre_return_gate_report(
        comment_text=safe_surface,
        composer_meta={"profile_key": "complete_initial", "composer_source": "ai_generated"},
    )

    assert report["passed"] is True
    assert report["action"] == ACTION_ALLOW
    assert report["koto_splice_detected"] is False
    assert report["koto_splice_codes"] == []
    assert "malformed_nominalization_conditional_fragment" not in report["rejection_reasons"]
    assert "malformed_nominalization_prediction_noun_fragment" not in report["rejection_reasons"]
    assert "residual_koto_splice_fragment" not in report["rejection_reasons"]
    assert "long_clause_koto_attachment_risk" not in report["rejection_reasons"]

def test_step2_runtime_surface_pre_return_gate_blocks_screenshot_tari_koto_surface() -> None:
    fixture = _visible_surface_fixture_by_id("visible_surface_red_malformed_tari_koto_20260524")

    report = build_runtime_surface_pre_return_gate_report(
        comment_text=fixture.public_body,
        composer_meta={"profile_key": "current_input_core", "composer_source": "ai_generated"},
        # The pre-return surface must still catch visible-surface breakage even
        # when upstream phrase-unit meta has no explicit malformed count.
        phrase_unit_grammar_meta={"malformed_phrase_unit_count": 0, "grammar_warning_codes": []},
    )

    assert report["evaluated"] is True
    assert report["passed"] is False
    assert report["blocked"] is True
    assert report["action"] == ACTION_RERENDER_SHALLOW_V2
    assert report["rerender_recommended"] is True
    assert report["malformed_phrase_unit_count"] >= 1
    assert report["malformed_nominalization_risk"] is True
    assert "malformed_phrase_unit" in report["rejection_reasons"]
    assert "malformed_nominalization_tari_fragment" in report["rejection_reasons"]
    assert set(fixture.expected_rejection_reasons).issubset(set(report["rejection_reasons"]))
    assert_runtime_surface_pre_return_gate_meta_only(report)

    dumped = dump_runtime_surface_pre_return_gate_report(report)
    assert "たりこと" not in dumped
    assert "無理に変えよう" not in dumped
    assert '"comment_text"' not in dumped


@pytest.mark.parametrize(
    "safe_surface",
    (
        "Emlisです。\n今は、考えたりすることを急がず見ようとしている感じが出ています。",
        "Emlisです。\n今は、見たり聞いたりすることの中に手がかりが残っています。",
        "Emlisです。\n今は、無理に変えようとしたことも含めて見ようとしている感じが出ています。",
    ),
)
def test_step2_runtime_surface_pre_return_gate_does_not_flag_safe_tari_nominalizations(safe_surface: str) -> None:
    report = build_runtime_surface_pre_return_gate_report(
        comment_text=safe_surface,
        composer_meta={"profile_key": "complete_initial", "composer_source": "ai_generated"},
    )

    assert "malformed_nominalization_tari_fragment" not in report["rejection_reasons"]
    assert "malformed_phrase_unit" not in report["rejection_reasons"]
    assert report["malformed_phrase_unit_count"] == 0


def test_step1_runtime_surface_pre_return_gate_allows_clean_surface_contract() -> None:
    report = build_runtime_surface_pre_return_gate_report(
        comment_text=_NATURAL_SURFACE,
        composer_meta={"profile_key": "complete_initial", "composer_source": "ai_generated"},
    )

    assert report["passed"] is True
    assert report["action"] == ACTION_ALLOW
    assert report["rejection_reasons"] == []
    assert report["surface_template_major"] is False
    assert report["generic_center_phrase_count"] == 0
    assert report["same_connector_run_max"] <= 1
    assert report["comment_text_body_included"] is False
    assert report["display_gate_relaxed"] is False


def test_step1_gate_can_use_precomputed_signature_without_exporting_candidate_body() -> None:
    fixture = RUNTIME_SURFACE_BASELINE_RED_FIXTURES[1]
    signature = build_surface_quality_signature(comment_text=fixture.public_body)

    report = build_runtime_surface_pre_return_gate_report(
        surface_quality_signature=signature,
        composer_meta=fixture.composer_meta,
    )

    assert report["passed"] is False
    assert report["action"] == ACTION_RERENDER_SHALLOW_V2
    assert "surface_template_major" in report["rejection_reasons"]
    dumped = dump_runtime_surface_pre_return_gate_report(report)
    assert "今までこと" not in dumped
    assert "大丈夫こと" not in dumped
    assert '"comment_text"' not in dumped


def test_step1_gate_contract_meta_schema_and_dump_are_meta_only() -> None:
    meta = build_runtime_surface_pre_return_gate_contract_meta()
    schema = build_runtime_surface_pre_return_gate_contract_schema()
    dumped = dump_runtime_surface_pre_return_gate_report(meta)

    assert json.loads(dumped)["version"] == RUNTIME_SURFACE_PRE_RETURN_GATE_VERSION
    assert json.loads(dumped)["comment_text_body_included"] is False
    assert '"comment_text"' not in dumped
    assert '"raw_input"' not in dumped
    assert schema["$id"] == RUNTIME_SURFACE_PRE_RETURN_GATE_VERSION
    assert set(schema["required"]) >= {
        "version",
        "evaluated",
        "passed",
        "action",
        "rejection_reasons",
        "raw_input_included",
        "comment_text_body_included",
        "display_gate_relaxed",
    }
    assert tuple(schema["properties"]["action"]["enum"]) == RUNTIME_SURFACE_PRE_RETURN_GATE_ACTIONS
    assert schema["properties"]["comment_text_body_included"]["const"] is False
    assert schema["properties"]["display_gate_relaxed"]["const"] is False

    unsafe_text_payload = dict(meta)
    unsafe_text_payload["comment_text"] = "出してはいけない本文"
    with pytest.raises(ValueError):
        assert_runtime_surface_pre_return_gate_meta_only(unsafe_text_payload)

    unsafe_relaxed_gate = dict(meta)
    unsafe_relaxed_gate["display_gate_relaxed"] = True
    with pytest.raises(ValueError):
        assert_runtime_surface_pre_return_gate_meta_only(unsafe_relaxed_gate)
