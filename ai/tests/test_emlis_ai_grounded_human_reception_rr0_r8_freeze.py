# -*- coding: utf-8 -*-
from __future__ import annotations

"""RR0 R8 actual-device failure evidence and closed progression contract."""

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
_FREEZE = _FIXTURE_ROOT / "grounded_human_reception_rr0_r8_freeze_20260712.json"
_EXACT8 = _FIXTURE_ROOT / "grounded_human_reception_exact8_v2_20260712.json"
_R6_RECEIPT = _FIXTURE_ROOT / "grounded_human_reception_r6_karen_review_receipt_20260712.json"
_VISIBLE_PACKET = (
    Path(__file__).resolve().parent
    / "local_only"
    / "grounded_human_reception_r6_exact8_visible_packet_20260712.json"
)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_FORBIDDEN_BODY_KEYS = frozenset(
    {
        "raw_text",
        "comment_text",
        "surface_text",
        "visible_surface",
        "exact_current_input",
        "memo",
        "memo_action",
        "anchor_text",
        "sentence_text",
    }
)


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


def _render(current_input):
    normalized = normalize_emlis_current_input(current_input)
    spans = tuple(build_evidence_ledger(normalized))
    resolver = build_evidence_span_resolver(spans, current_input=normalized)
    plan = build_grounded_observation_plan(normalized, evidence_spans=spans)
    sentence_plan = build_grounded_sentence_plan(plan, resolver)
    surface = realize_grounded_sentence_plan(sentence_plan, plan, resolver)
    full_comment = surface.text.strip()
    observation, reception, issues = split_two_stage_surface(full_comment)
    assert issues == ()
    return observation.strip(), reception.strip(), full_comment


def _assert_body_free(value) -> None:
    if isinstance(value, dict):
        assert not _FORBIDDEN_BODY_KEYS.intersection(value)
        for nested in value.values():
            _assert_body_free(nested)
    elif isinstance(value, list):
        for nested in value:
            _assert_body_free(nested)


def test_rr0_freeze_has_exact_r8_failure_state_and_closed_progression() -> None:
    freeze = _load(_FREEZE)
    assert freeze["schema_version"] == (
        "cocolon.emlis.grounded_human_reception."
        "rr0_r8_failure_freeze.v1"
    )
    assert freeze["r8_status"] == {
        "actual_device_layout": "visual_pass",
        "actual_device_two_stage_display": "pass",
        "human_reception_language_variety": "repair_required",
        "human_reception_response_depth": "repair_required",
        "human_reception_role_distinctness": "direction_pass",
        "r8_progression": "blocked",
    }
    assert freeze["progression_authority"] == "none"
    assert freeze["valid_for_progression"] is False
    assert freeze["p5_formal_24_start_allowed"] is False
    assert freeze["p6_start_allowed"] is False
    assert freeze["p8_start_allowed"] is False
    assert freeze["actual_device_evidence"]["raw_comment_sha256_machine_match"] == (
        "not_confirmed"
    )
    assert freeze["actual_device_evidence"][
        "screenshot_review_is_raw_body_hash_proof"
    ] is False


def test_rr0_source_snapshot_and_referenced_artifacts_are_hash_bound() -> None:
    freeze = _load(_FREEZE)
    manifest = freeze["source_snapshot_files"]
    assert [row["path"] for row in manifest] == [
        "ai/services/ai_inference/emlis_ai_grounded_observation_plan.py",
        "ai/services/ai_inference/emlis_ai_grounded_human_reception.py",
        "ai/services/ai_inference/emlis_ai_grounded_sentence_surface.py",
        "ai/services/ai_inference/emlis_ai_grounded_observation_gate.py",
        "ai/services/ai_inference/emlis_ai_reply_service.py",
    ]
    for row in manifest:
        assert _SHA256_RE.fullmatch(row["sha256"])
    assert _sha256_json(manifest) == freeze["source_snapshot_sha256"]
    assert _sha256_file(_EXACT8) == freeze["exact8_fixture_sha256"]
    assert _sha256_file(_VISIBLE_PACKET) == freeze["visible_packet_sha256"]
    assert _sha256_file(_R6_RECEIPT) == freeze["r6_karen_review_receipt_sha256"]


def test_rr0_exact8_historical_surface_and_live_observation_freeze_are_unique() -> None:
    freeze = _load(_FREEZE)
    exact8 = _load(_EXACT8)
    packet = _load(_VISIBLE_PACKET)
    exact_by_id = {row["case_id"]: row for row in exact8["cases"]}
    packet_by_id = {row["case_id"]: row for row in packet["cases"]}

    assert freeze["case_order"] == exact8["case_order"] == packet["case_order"]
    assert [row["case_id"] for row in freeze["cases"]] == freeze["case_order"]
    identities: set[tuple[str, str]] = set()
    observations: set[str] = set()

    for row in freeze["cases"]:
        case_id = row["case_id"]
        exact = exact_by_id[case_id]
        current = packet_by_id[case_id]
        observation, _reception, _full_comment = _render(
            exact["exact_current_input"]
        )

        assert row["current_input_sha256"] == exact["current_input_sha256"]
        assert row["current_input_sha256"] == current["current_input_sha256"]
        assert row["current_visible_surface_sha256"] == current["visible_surface_sha256"]
        assert row["current_observation_section_sha256"] == current[
            "observation_section_sha256"
        ]
        assert row["current_reception_section_sha256"] == current[
            "reception_section_sha256"
        ]
        assert _sha256_text(observation) == row["current_observation_section_sha256"]

        # Reception and full-Surface hashes freeze the RR0/R8 historical
        # failure baseline.  RR4/RR5 intentionally change those sections;
        # only the observation freeze remains a live-runtime comparison.

        # The v2 fixture's local_comment_sha256 is the pre-distinctness
        # historical failure body, never this RR0 current surface.
        assert row["current_visible_surface_sha256"] != exact["local_comment_sha256"]
        assert row["failure_baseline_only"] is True
        assert row["actual_device_raw_comment_sha256"] is None
        assert row["actual_device_visual_match_to_current_surface"] == "pass"
        identities.add(
            (row["current_input_sha256"], row["current_visible_surface_sha256"])
        )
        observations.add(row["current_observation_section_sha256"])

    assert len(identities) == len(freeze["case_order"]) == 8
    assert len(observations) == 8


def test_rr0_evidence_inventory_is_hash_only_and_complete() -> None:
    freeze = _load(_FREEZE)
    refs: list[tuple[str, str]] = []
    for row in freeze["cases"]:
        refs.append((row["backend_log_ref"]["path"], row["backend_log_ref"]["sha256"]))
        refs.extend((item["path"], item["sha256"]) for item in row["screenshot_refs"])
    assert len(refs) == len(set(refs)) == 22
    assert all(_SHA256_RE.fullmatch(sha256) for _path, sha256 in refs)
    assert freeze["raw_input_included"] is False
    assert freeze["returned_surface_included"] is False
    _assert_body_free(freeze)


def test_rr0_old_r6_human_pass_is_history_not_progression_authority() -> None:
    freeze = _load(_FREEZE)
    receipt = _load(_R6_RECEIPT)
    assert receipt["product_readfeel_status"] == "human_pass"
    assert receipt["progression_authority"] == "none"
    assert receipt["valid_for_progression"] is False
    assert freeze["artifact_roles"]["r6_karen_review_receipt"] == (
        "historical_read_evidence_not_progression_owner"
    )
    assert freeze["r6_karen_review_valid_for_current_progression"] is False
