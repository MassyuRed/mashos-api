# -*- coding: utf-8 -*-
from __future__ import annotations

"""R0 evidence, app-valid identity, and immutable observation baselines."""

import hashlib
import json
from pathlib import Path
import re

from emlis_ai_current_input_bundle import normalize_emlis_current_input
from emlis_ai_evidence_ledger_service import (
    build_evidence_ledger,
    build_evidence_span_resolver,
)
from emlis_ai_grounded_observation_plan import build_grounded_observation_plan
from emlis_ai_grounded_sentence_surface import (
    build_grounded_sentence_plan,
    realize_grounded_sentence_plan,
    split_two_stage_surface,
)


_FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures"
_APP_VALID_FIXTURE = _FIXTURE_ROOT / "grounded_human_reception_exact8_v2_20260712.json"
_HASH_MANIFEST = _FIXTURE_ROOT / "grounded_human_reception_section_hashes_20260712.json"
_DEVICE_STATUS = _FIXTURE_ROOT / "grounded_human_reception_device_status_20260712.json"
_HISTORICAL_FIXTURE = _FIXTURE_ROOT / "gatea_mandatory_two_stage_exact8_recheck_20260712.json"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_APP_EMOTIONS = {"喜び", "悲しみ", "怒り", "不安", "平穏", "自己理解"}
_APP_CATEGORIES = {"生活", "仕事", "趣味", "人間関係", "恋愛", "健康", "学習", "価値観", "人生"}


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256_json(value) -> str:
    return _sha256_text(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    )


def _render_sections(current_input):
    normalized = normalize_emlis_current_input(current_input)
    spans = tuple(build_evidence_ledger(normalized))
    resolver = build_evidence_span_resolver(spans, current_input=normalized)
    plan = build_grounded_observation_plan(normalized, evidence_spans=spans)
    sentence_plan = build_grounded_sentence_plan(plan, resolver)
    surface = realize_grounded_sentence_plan(sentence_plan, plan, resolver)
    full_comment = surface.text.strip()
    observation, reception, issues = split_two_stage_surface(full_comment)
    assert issues == ()
    return plan, observation.strip(), reception.strip(), full_comment


def test_r0_app_valid_exact8_v2_is_the_current_fixture_identity() -> None:
    fixture = _load(_APP_VALID_FIXTURE)
    assert fixture["schema_version"] == "cocolon.emlis.grounded_human_reception.exact8.app_valid.v2"
    assert fixture["fixture_identity_status"] == "current_superseding_app_valid_input_owner"
    assert fixture["supersedes"] == _HISTORICAL_FIXTURE.name
    assert fixture["valid_for_progression"] is False
    assert fixture["progression_authority"] == "none_until_reception_repair_and_new_device_validation"
    assert len(fixture["case_order"]) == len(set(fixture["case_order"])) == 8
    assert [case["case_id"] for case in fixture["cases"]] == fixture["case_order"]

    for case in fixture["cases"]:
        current_input = case["exact_current_input"]
        assert current_input["emotions"]
        assert current_input["category"]
        assert set(current_input["emotions"]) <= _APP_EMOTIONS
        assert set(current_input["category"]) <= _APP_CATEGORIES
        if "自己理解" in current_input["emotions"]:
            assert current_input["emotions"] == ["自己理解"]
        assert _sha256_json(current_input) == case["current_input_sha256"]


def test_r0_old_invalid_fixture_remains_immutable_historical_evidence() -> None:
    historical = _load(_HISTORICAL_FIXTURE)
    current = _load(_APP_VALID_FIXTURE)
    assert _sha256_file(_HISTORICAL_FIXTURE) == "8de881fb66577efe1c30556754ca178c211737f8e1218f0a5825bba9a4831e6e"
    assert historical["valid_for_progression"] is False
    assert current["supersedes"] == _HISTORICAL_FIXTURE.name

    historical_by_id = {case["case_id"]: case for case in historical["cases"]}
    current_by_id = {case["case_id"]: case for case in current["cases"]}
    changed = {
        case_id
        for case_id in current_by_id
        if historical_by_id[case_id]["current_input_sha256"]
        != current_by_id[case_id]["current_input_sha256"]
    }
    assert changed == {"I6-S03", "I6-L03", "I6-C01", "I6-D02"}


def test_r0_exact8_freezes_observation_and_keeps_old_reception_as_failure_evidence() -> None:
    fixture = _load(_APP_VALID_FIXTURE)
    manifest = _load(_HASH_MANIFEST)
    assert manifest["schema_version"] == "cocolon.emlis.grounded_human_reception.section_hashes.v1"
    assert manifest["fixture_ref"] == _APP_VALID_FIXTURE.name
    assert manifest["fixture_sha256"] == _sha256_file(_APP_VALID_FIXTURE)
    assert manifest["observation_baseline_role"] == "frozen_green_during_reception_repair"
    assert manifest["reception_baseline_role"] == "failure_baseline_not_acceptance_expectation"
    assert manifest["valid_for_progression"] is False
    expected_by_id = {case["case_id"]: case for case in manifest["cases"]}

    for case in fixture["cases"]:
        plan, observation, reception, full_comment = _render_sections(case["exact_current_input"])
        expected = expected_by_id[case["case_id"]]
        assert _sha256_text(observation) == expected["observation_section_sha256"]
        assert _sha256_text(reception) != expected["reception_section_sha256"]
        assert _sha256_text(full_comment) != expected["full_comment_sha256"]
        assert expected["full_comment_sha256"] == case["local_comment_sha256"]
        assert expected["current_input_sha256"] == case["current_input_sha256"]
        assert _SHA256_RE.fullmatch(expected["observation_section_sha256"])
        assert plan.response_plan.surface_shape == "two_stage"


def test_r0_actual_device_status_keeps_product_and_progression_closed() -> None:
    receipt = _load(_DEVICE_STATUS)
    assert receipt["schema_version"] == "cocolon.emlis.grounded_human_reception.actual_device_status.v1"
    assert receipt["actual_device_two_stage_display"] == "pass"
    assert receipt["current_input_comprehension_foundation"] == "pass"
    assert receipt["human_reception_distinctness"] == "repair_required"
    assert receipt["product_readfeel"] == "human_fail_or_repair_required"
    assert receipt["technical_gate_pass_is_product_pass"] is False
    assert receipt["evidence_basis"]["raw_comment_sha256_machine_match"] == "not_confirmed"
    assert receipt["section_hash_manifest_sha256"] == _sha256_file(_HASH_MANIFEST)
    assert receipt["fixture_sha256"] == _sha256_file(_APP_VALID_FIXTURE)
    assert receipt["valid_for_progression"] is False
    assert receipt["p5_formal_24_start_allowed"] is False
    assert receipt["p6_start_allowed"] is False
    assert receipt["p8_start_allowed"] is False


def test_r0_hash_manifest_and_device_receipt_are_body_free() -> None:
    for path in (_HASH_MANIFEST, _DEVICE_STATUS):
        payload = _load(path)
        assert payload["raw_input_included"] is False
        assert payload["returned_surface_included"] is False
        serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        assert "memo" not in serialized
        assert "memo_action" not in serialized

        def visit(value) -> None:
            if isinstance(value, dict):
                assert not {
                    "raw_text",
                    "comment_text",
                    "surface_text",
                    "thought_text",
                    "action_text",
                }.intersection(value)
                for nested in value.values():
                    visit(nested)
            elif isinstance(value, list):
                for nested in value:
                    visit(nested)

        visit(payload)
