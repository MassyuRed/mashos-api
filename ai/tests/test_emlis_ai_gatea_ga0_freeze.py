# -*- coding: utf-8 -*-
from __future__ import annotations

"""Integrity guards for the immutable Gate A GA0 pre-GA1 baseline."""

import hashlib
import json
from pathlib import Path
import re

_TEST_ROOT = Path(__file__).resolve().parent
_FREEZE_PATH = _TEST_ROOT / "local_only" / "gatea_ga0_freeze_bodyfree_20260712.json"
_SOURCE_ROOT = _TEST_ROOT.parents[1]
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_EXPECTED_OWNER_HASHES = {
    "ai/services/ai_inference/emlis_ai_grounded_observation_plan.py": "b32a17e98036ceea1568145d344a631c070c37a669f5c7aa8ba1e3f92b9b5f40",
    "ai/services/ai_inference/emlis_ai_grounded_sentence_surface.py": "5d27e21c244f4e99c2659cde3a3b65250dcd19e53b9073bce1ad6dd4230027d6",
    "ai/services/ai_inference/emlis_ai_grounded_observation_gate.py": "c45824254228e9f118b235b6e2d651ea9cc1f7d6b187ce2b1df34db40709ecd5",
    "ai/services/ai_inference/emlis_ai_reply_service.py": "1eb3d7b65c72c6c7ba5aee44c2138ae6e7ea38b20228f16821f1a5d2e17ef80c",
}


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_json(value) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def test_ga0_freezes_received_archive_source_and_canonical_versions() -> None:
    freeze = _load(_FREEZE_PATH)
    assert freeze["schema_version"] == "cocolon.emlis.gatea.freeze.bodyfree.v1"
    assert freeze["source_archive_ref"] == "mashos-api(214).zip"
    assert freeze["source_archive_sha256"] == "9fbe8ed2ba6b0d245a60aa4f6f0c6a73cce5c58f77adfbaa4f6a5769ba72b9f7"
    assert freeze["source_snapshot_fingerprint"] == "394b5da7a9546d5f893e00fe27417e2e10231dcc267a2d728e6f11025d2aa0c3"
    assert freeze["source_snapshot_file_count"] == 1359
    versions = freeze["canonical_versions"]
    assert versions["semantic"] == "cocolon.emlis.grounded_semantics.i2.v2"
    assert versions["plan_generation_path"] == "grounded_observation_plan_canonical_v1"
    assert versions["surface_generation_path"] == "grounded_sentence_surface_canonical_v1"
    assert versions["composer_source"] == "grounded_plan_realizer"


def test_ga0_owner_production_source_hashes_remain_frozen_as_baseline() -> None:
    freeze = _load(_FREEZE_PATH)
    assert freeze["source_file_sha256s"] == _EXPECTED_OWNER_HASHES
    assert all(_SHA256_RE.fullmatch(value) for value in _EXPECTED_OWNER_HASHES.values())


def test_ga0_same16_body_free_baseline_signature_is_complete() -> None:
    freeze = _load(_FREEZE_PATH)
    same16 = freeze["same16"]
    assert same16["case_count"] == 16
    assert len(same16["case_order"]) == len(set(same16["case_order"])) == 16
    rows = [
        {
            key: case[key]
            for key in ("case_id", "body_sha256", "character_count", "line_count")
        }
        for case in same16["cases"]
    ]
    assert _sha256_json(rows) == same16["body_free_signature_sha256"]
    assert same16["body_free_signature_sha256"] == "33b2431216abb243c0fcee43dbe8dfe6bf81546c1df6e37b453d04ce449e475b"
    for case in same16["cases"]:
        assert _SHA256_RE.fullmatch(case["body_sha256"])
        if case["case_id"] == "A":
            assert case["reason_refs"] == []
        else:
            assert case["reason_refs"]


def test_ga0_body_free_evidence_contains_no_raw_input_or_returned_body() -> None:
    freeze = _load(_FREEZE_PATH)
    assert freeze["raw_input_included"] is False
    assert freeze["returned_surface_included"] is False
    assert freeze["comment_text_included"] is False
    assert all(
        set(case)
        == {
            "body_sha256",
            "case_id",
            "character_count",
            "line_count",
            "reason_refs",
        }
        for case in freeze["same16"]["cases"]
    )


def test_ga0_freezes_collect_and_complete_unique_169_failure_set() -> None:
    freeze = _load(_FREEZE_PATH)
    collect = freeze["full_collect"]
    backend = freeze["full_backend"]
    assert collect == {
        "collected_test_count": 12714,
        "collection_error_count": 0,
        "collection_error_refs": [],
        "return_code": 0,
    }
    assert (backend["passed_count"], backend["failed_count"], backend["skipped_count"]) == (12543, 169, 2)
    refs = backend["failure_node_refs"]
    assert len(refs) == len(set(refs)) == 169
    assert backend["failure_node_ref_duplicate_count"] == 0
    assert backend["failure_node_refs_sha256"] == _sha256_json(refs)
    assert backend["failure_set_id"] == f"post_fb172_residual_{backend['failure_node_refs_sha256'][:12]}"


def test_ga0_keeps_historical_fb172_ledger_immutable_and_explains_env_probe() -> None:
    freeze = _load(_FREEZE_PATH)
    historical = freeze["historical_fb172"]
    assert historical["mutated"] is False
    assert historical["ledger_sha256"] == "7a166e785c387c30cf89c6935da4c086cee6d870d8a121b4f6d7ffa796a3587c"
    assert _sha256(_SOURCE_ROOT / historical["ledger_ref"]) == historical["ledger_sha256"]
    environment = freeze["environment"]
    assert environment["fastapi_version"] == "0.115.12"
    assert environment["import_mode"] == "prepend"
    assert environment["worker_count"] == 1
    probe = environment["nonbaseline_probe"]
    assert probe["observed_failed_count"] == 171
    assert probe["extra_failure_count"] == 2
    assert probe["source_change_required"] is False
