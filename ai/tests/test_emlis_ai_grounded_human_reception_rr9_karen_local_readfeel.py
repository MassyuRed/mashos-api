# -*- coding: utf-8 -*-
from __future__ import annotations

"""RR9 visible-body read binding and 13-axis Karen local receipt contract."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re

import pytest

from helpers.emlis_ai_grounded_human_reception_rr8_qa import (
    RR9_REVIEW_AXES,
    sha256_json,
    sha256_text,
    validate_rr9_karen_review_receipt,
)
from emlis_ai_current_input_bundle import normalize_emlis_current_input
from emlis_ai_evidence_ledger_service import (
    build_evidence_ledger,
    build_evidence_span_resolver,
)
from emlis_ai_grounded_observation_gate import (
    RECEPTION_GATE_REPORT_FIELDS,
    evaluate_grounded_observation_gate,
)
from emlis_ai_grounded_observation_plan import build_grounded_observation_plan
from emlis_ai_grounded_sentence_surface import (
    build_grounded_sentence_plan,
    realize_grounded_sentence_plan,
    split_two_stage_surface,
)


_TEST_ROOT = Path(__file__).resolve().parent
_REPO_ROOT = _TEST_ROOT.parents[1]
_EXACT8 = (
    _TEST_ROOT / "fixtures" / "grounded_human_reception_exact8_v2_20260712.json"
)
_UNSEEN12 = (
    _TEST_ROOT
    / "local_only"
    / "grounded_human_reception_rr8_unseen12_20260713.json"
)
_PACKET = (
    _TEST_ROOT
    / "local_only"
    / "grounded_human_reception_rr9_visible_packet_20260713.json"
)
_RECEIPT = (
    _TEST_ROOT
    / "fixtures"
    / "grounded_human_reception_rr9_karen_review_receipt_20260713.json"
)
_SOURCE_OWNER_PATHS = (
    "ai/services/ai_inference/emlis_ai_grounded_observation_plan.py",
    "ai/services/ai_inference/emlis_ai_grounded_human_reception.py",
    "ai/services/ai_inference/emlis_ai_grounded_sentence_surface.py",
    "ai/services/ai_inference/emlis_ai_grounded_observation_gate.py",
    "ai/services/ai_inference/emlis_ai_reply_service.py",
)
_EXACT_PRIORITY_DEPTH = {
    "B": 2,
    "C": 2,
    "I6-L03": 2,
    "I6-C01": 2,
}
_SHORT_PRIORITY = {"A", "I6-S03"}
_SAFETY_PRIORITY = {"D", "I6-D02"}
_QUOTE_RE = re.compile(r"「([^」]+)」")


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_snapshot():
    manifest = [
        {"path": path, "sha256": _sha256_file(_REPO_ROOT / path)}
        for path in _SOURCE_OWNER_PATHS
    ]
    return manifest, sha256_json(manifest)


def _artifacts(current_input):
    normalized = normalize_emlis_current_input(current_input)
    spans = tuple(build_evidence_ledger(normalized))
    resolver = build_evidence_span_resolver(spans, current_input=normalized)
    plan = build_grounded_observation_plan(normalized, evidence_spans=spans)
    sentence_plan = build_grounded_sentence_plan(plan, resolver)
    surface = realize_grounded_sentence_plan(sentence_plan, plan, resolver)
    report = evaluate_grounded_observation_gate(
        plan=plan,
        sentence_plan=sentence_plan,
        surface_result=surface,
        resolver=resolver,
    )
    observation, reception, issues = split_two_stage_surface(surface.text)
    assert issues == ()
    return plan, surface, report, observation.strip(), reception.strip()


def _review_inputs():
    exact = _load(_EXACT8)
    unseen = _load(_UNSEEN12)
    rows = [
        (
            row["case_id"],
            "exact8",
            row["exact_current_input"],
            row["current_input_sha256"],
        )
        for row in exact["cases"]
    ]
    representative = next(
        row for row in unseen["cases"] if row["case_id"] == "RR8-U05"
    )
    rows.append(
        (
            representative["case_id"],
            "unseen12_representative",
            representative["current_input"],
            sha256_json(representative["current_input"]),
        )
    )
    return tuple(rows)


def test_rr9_visible_packet_is_live_surface_and_source_snapshot_bound() -> None:
    packet = _load(_PACKET)
    source_manifest, source_snapshot_sha256 = _source_snapshot()
    inputs = _review_inputs()
    packet_by_id = {row["case_id"]: row for row in packet["cases"]}

    assert packet["schema_version"] == (
        "cocolon.emlis.grounded_human_reception.rr9_visible_packet.local_only.v1"
    )
    assert packet["local_only"] is True
    assert packet["review_scope"] == (
        "exact8_plus_unseen_representative_visible_surface"
    )
    assert packet["source_snapshot_files"] == source_manifest
    assert packet["source_snapshot_sha256"] == source_snapshot_sha256
    assert packet["exact8_fixture_sha256"] == _sha256_file(_EXACT8)
    assert packet["unseen12_fixture_sha256"] == _sha256_file(_UNSEEN12)
    assert packet["case_order"] == [case_id for case_id, *_rest in inputs]
    assert set(packet_by_id) == set(packet["case_order"])

    for case_id, cohort, current_input, input_sha256 in inputs:
        plan, surface, report, observation, reception = _artifacts(current_input)
        reception_plan = plan.response_plan.human_reception_plan
        assert reception_plan is not None
        row = packet_by_id[case_id]
        assert row["cohort"] == cohort
        assert row["current_input_sha256"] == input_sha256
        assert row["visible_surface"] == surface.text
        assert row["visible_surface_sha256"] == sha256_text(surface.text)
        assert row["observation_section_sha256"] == sha256_text(observation)
        assert row["reception_section_sha256"] == sha256_text(reception)
        assert row["depth_level"] == report.reception_depth_level
        assert row["opportunity_count"] == report.reception_opportunity_count
        assert row["planned_move_count"] == report.reception_planned_move_count
        assert row["realized_move_count"] == report.reception_realized_move_count
        assert row["sentence_count"] == report.reception_sentence_count
        assert row["automated_reception_gates"] == "passed"
        assert row["product_readfeel_status"] == "pending_human_read"
        assert report.passed is True
        assert all(
            getattr(report, field_name) == "passed"
            for field_name in RECEPTION_GATE_REPORT_FIELDS
        )


def test_rr9_priority_depth_shortness_safety_and_quote_read_boundaries() -> None:
    packet_by_id = {row["case_id"]: row for row in _load(_PACKET)["cases"]}
    input_by_id = {
        case_id: current_input
        for case_id, _cohort, current_input, _sha256 in _review_inputs()
    }

    for case_id, expected_sentences in _EXACT_PRIORITY_DEPTH.items():
        row = packet_by_id[case_id]
        assert row["sentence_count"] == expected_sentences
        assert row["realized_move_count"] == 2
    for case_id in _SHORT_PRIORITY:
        row = packet_by_id[case_id]
        assert row["sentence_count"] == 1
        assert row["realized_move_count"] == 1
    for case_id in _SAFETY_PRIORITY:
        row = packet_by_id[case_id]
        assert row["sentence_count"] == 2
        assert row["realized_move_count"] == 2
        assert "Emlis" in row["visible_surface"]
        assert "診断" not in row["visible_surface"]
        assert "危険度" not in row["visible_surface"]

    for case_id, row in packet_by_id.items():
        assert "…」" not in row["visible_surface"]
        _observation, reception, issues = split_two_stage_surface(
            row["visible_surface"]
        )
        assert issues == ()
        source = " ".join(
            str(input_by_id[case_id].get(field) or "")
            for field in ("memo", "memo_action")
        )
        for quote in _QUOTE_RE.findall(reception):
            assert len(quote) <= 16
            source_cursor = 0
            for segment in quote.split("…"):
                index = source.find(segment, source_cursor)
                assert index >= 0
                source_cursor = index + len(segment)


def test_rr9_karen_receipt_has_all_13_axes_and_binds_visible_packet() -> None:
    packet = _load(_PACKET)
    receipt = _load(_RECEIPT)
    _source_manifest, source_snapshot_sha256 = _source_snapshot()
    surface_hashes = {
        row["case_id"]: row["visible_surface_sha256"]
        for row in packet["cases"]
    }
    issues = validate_rr9_karen_review_receipt(
        receipt,
        expected_surface_hashes=surface_hashes,
        expected_packet_sha256=_sha256_file(_PACKET),
        expected_source_snapshot_sha256=source_snapshot_sha256,
    )
    assert issues == ()
    assert receipt["review_axes"] == list(RR9_REVIEW_AXES)
    assert len(receipt["reviews"]) == 9
    assert all(row["verdict"] == "human_pass" for row in receipt["reviews"])
    assert all(
        set(row["axes"]) == set(RR9_REVIEW_AXES)
        and set(row["axes"].values()) == {"pass"}
        for row in receipt["reviews"]
    )
    assert receipt["product_readfeel_status"] == "human_pass"
    assert receipt["technical_pass_is_product_readfeel_pass"] is False
    assert receipt["automatic_gate_result_used_as_human_result"] is False
    assert receipt["progression_authority"] == "none"
    assert receipt["valid_for_progression"] is False
    assert receipt["representative4_actual_device_status"] == "not_run"
    assert receipt["exact8_actual_device_status"] == "not_run"


@pytest.mark.parametrize(
    ("mutation", "expected_issue"),
    [
        (
            lambda receipt: receipt.update(
                {"automatic_gate_result_used_as_human_result": True}
            ),
            "rr9_karen_review_automatic_result_boundary_missing",
        ),
        (
            lambda receipt: receipt.update({"progression_authority": "granted"}),
            "rr9_karen_review_progression_authority_invalid",
        ),
        (
            lambda receipt: receipt.update({"raw_input": "body"}),
            "rr9_karen_review_top_level_schema_mismatch",
        ),
        (
            lambda receipt: receipt["reviews"].append(
                deepcopy(receipt["reviews"][0])
            ),
            "rr9_karen_review_case_id_duplicate",
        ),
    ],
)
def test_rr9_receipt_rejects_automatic_progression_body_and_duplicate_rows(
    mutation,
    expected_issue: str,
) -> None:
    packet = _load(_PACKET)
    receipt = _load(_RECEIPT)
    mutation(receipt)
    _manifest, source_snapshot_sha256 = _source_snapshot()
    issues = validate_rr9_karen_review_receipt(
        receipt,
        expected_surface_hashes={
            row["case_id"]: row["visible_surface_sha256"]
            for row in packet["cases"]
        },
        expected_packet_sha256=_sha256_file(_PACKET),
        expected_source_snapshot_sha256=source_snapshot_sha256,
    )
    assert expected_issue in issues
