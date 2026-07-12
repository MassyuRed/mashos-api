# -*- coding: utf-8 -*-
from __future__ import annotations

"""Integrity guards for the immutable Gate 0 RR0 pre-repair freeze."""

import hashlib
import json
from pathlib import Path
import re


_TEST_ROOT = Path(__file__).resolve().parent
_FREEZE_PATH = _TEST_ROOT / "fixtures" / "gate0_rr0_freeze_20260711.json"
_LOCAL_PATH = _TEST_ROOT / "local_only" / "gate0_rr0_body_local_20260711.json"
_R8_RECEIPT_PATH = (
    _TEST_ROOT / "fixtures" / "emlis_gate0_r8_karen_local_review_receipt_20260711.json"
)
_R9_DECISION_PATH = _TEST_ROOT / "fixtures" / "emlis_gate0_r9_decision_20260711.json"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_rr0_freezes_current_16_repair_9_and_two_collection_blockers() -> None:
    freeze = _load(_FREEZE_PATH)
    assert freeze["schema_version"] == "cocolon.emlis.gate0.repair_freeze.bodyfree.v1"
    assert freeze["case_count"] == 16
    assert len(freeze["case_order"]) == 16
    assert len(set(freeze["case_order"])) == 16
    assert len(freeze["repair_case_ids"]) == 9
    assert freeze["review"]["local_human_pass_count"] == 7
    assert freeze["review"]["repair_required_count"] == 9
    assert freeze["review"]["hard_fatal_count"] == 0
    assert freeze["review"]["decision_code"] == "GATE0_REPAIR_RETURN_STOPPED"
    assert len(freeze["collection_blockers"]) == 2
    assert all(
        blocker["production_restore_allowed"] is False
        and blocker["canonical_replacement_owners"]
        for blocker in freeze["collection_blockers"]
    )


def test_rr0_source_and_case_hashes_are_complete_and_recomputable() -> None:
    freeze = _load(_FREEZE_PATH)
    assert _SHA256_RE.fullmatch(freeze["source_archive_sha256"])
    assert _SHA256_RE.fullmatch(freeze["source_snapshot_fingerprint"])
    assert freeze["source_snapshot_file_count"] > 0
    assert "relative_path_utf8" in freeze["source_snapshot_algorithm"]
    assert freeze["source_file_sha256s"]
    assert all(
        _SHA256_RE.fullmatch(value)
        for value in freeze["source_file_sha256s"].values()
    )
    assert all(
        _SHA256_RE.fullmatch(case[key])
        for case in freeze["cases"]
        for key in (
            "normalized_current_input_sha256",
            "current_body_sha256",
            "plan_signature_sha256",
            "sentence_plan_signature_sha256",
            "surface_signature_sha256",
            "anchor_to_line_occurrence_signature_sha256",
        )
    )


def test_rr0_body_free_freeze_matches_local_hashes_without_copying_body() -> None:
    freeze = _load(_FREEZE_PATH)
    local = _load(_LOCAL_PATH)
    assert freeze["raw_input_included"] is False
    assert freeze["returned_surface_included"] is False
    assert freeze["comment_text_included"] is False
    freeze_text = json.dumps(freeze, ensure_ascii=False, sort_keys=True)
    local_by_case = {item["case_id"]: item for item in local["cases"]}
    assert tuple(local_by_case) == tuple(freeze["case_order"])
    for frozen_case in freeze["cases"]:
        current = local_by_case[frozen_case["case_id"]]
        assert frozen_case["current_body_sha256"] == current["current_body_sha256"]
        assert current["current_body"] not in freeze_text
        normalized_text = json.dumps(
            current["normalized_current_input"],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        assert normalized_text not in freeze_text


def test_rr0_keeps_existing_r8_and_r9_artifacts_immutable() -> None:
    freeze = _load(_FREEZE_PATH)
    review = freeze["review"]
    assert review["r8_receipt_sha256"] == _sha256(_R8_RECEIPT_PATH)
    assert review["r9_decision_sha256"] == _sha256(_R9_DECISION_PATH)
    assert review["generated_body_hashes_match_current_r8_comparison"] is True
