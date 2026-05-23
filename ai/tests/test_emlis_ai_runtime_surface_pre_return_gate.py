# -*- coding: utf-8 -*-
from __future__ import annotations

import json

import pytest

from emlis_ai_complete_surface_quality_signature import build_surface_quality_signature
from emlis_ai_runtime_surface_pre_return_gate import (
    ACTION_ALLOW,
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
    RUNTIME_SURFACE_RED_FIXTURE_VERSION,
)

_NATURAL_SURFACE = (
    "Emlisです。\n"
    "今は、自分の特技を探そうとしている感じが出ています。\n"
    "好きで続けているものはあるのに、それを得意と呼べるかで止まっているように見えます。"
)


def test_step0_baseline_red_fixtures_are_fixed_without_good_sentence_locking() -> None:
    assert RUNTIME_SURFACE_RED_FIXTURE_VERSION == "emlis.runtime_surface_red_fixtures.v1"
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
