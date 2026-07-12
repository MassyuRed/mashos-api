# -*- coding: utf-8 -*-
from __future__ import annotations

"""GA5 residual inventory and current-owner closure contracts."""

from collections import Counter
import hashlib
import json
from pathlib import Path

import pytest

from helpers.emlis_ai_fb172_migration import _ASSERTIONS, _migration_map


_TEST_ROOT = Path(__file__).resolve().parent
_MANIFEST_PATH = _TEST_ROOT / "fixtures" / "gatea_ga5_residual_closure_20260712.json"
_FREEZE_PATH = _TEST_ROOT / "local_only" / "gatea_ga0_freeze_bodyfree_20260712.json"
_OWNER_LEDGER_PATH = _TEST_ROOT / "fixtures" / "fb172_owner_ledger_20260712.json"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _ga5_batch(record: dict) -> str:
    source_batch = record["planned_repair_batch"]
    if source_batch == "B3":
        return "O2"
    if source_batch in {"B4", "B5"}:
        return "O3"
    if source_batch == "B6" and record["primary_classification"] == (
        "CURRENT_CONTRACT_REGRESSION"
    ):
        return "O4"
    if source_batch == "B7":
        return "O5"
    return "O1"


def _owner_family(record: dict) -> str:
    refs = " ".join(record["current_owner_refs"]).lower()
    obligations = " ".join(record["valid_protected_obligations"]).lower()
    combined = f"{refs} {obligations}"
    if "negative_reachability" in combined or "inventory" in combined:
        return "inventory_negative_reachability"
    if "emotion_submit" in combined:
        return "emotion_submit_e2e"
    if "safety" in combined:
        return "safety_owner"
    if "public" in combined:
        return "public_feedback_contract"
    if "grounded_observation_gate" in combined:
        return "grounded_semantic_gate"
    if "grounded_sentence" in combined:
        return "current_sentence_surface"
    if "grounded_observation_plan" in combined:
        return "current_grounded_plan"
    if "rn_" in combined or "rn contract" in combined:
        return "rn_contract"
    return "historical_test_migration"


def _projected_records() -> tuple[dict, ...]:
    frozen_refs = set(_load(_FREEZE_PATH)["full_backend"]["failure_node_refs"])
    owner_records = {
        record["baseline_failure_ref"]: record
        for record in _load(_OWNER_LEDGER_PATH)["records"]
    }
    assert frozen_refs <= set(owner_records)
    return tuple(owner_records[ref] for ref in sorted(frozen_refs))


def test_ga5_a_residual_inventory_projects_all_frozen_nodes_without_mutating_history() -> None:
    manifest = _load(_MANIFEST_PATH)
    freeze = _load(_FREEZE_PATH)
    records = _projected_records()
    baseline = manifest["baseline_failure_set"]
    owner_source = manifest["current_owner_record_source"]

    assert manifest["schema_version"] == (
        "cocolon.emlis.gatea.ga5.residual_closure.bodyfree.v1"
    )
    assert _sha256(_FREEZE_PATH) == baseline["freeze_sha256"]
    assert _sha256(_OWNER_LEDGER_PATH) == owner_source["ledger_sha256"]
    assert baseline["failure_set_id"] == freeze["full_backend"]["failure_set_id"]
    assert baseline["failure_refs_sha256"] == (
        freeze["full_backend"]["failure_node_refs_sha256"]
    )
    assert len(records) == baseline["failure_ref_count"] == 169
    assert len({record["baseline_failure_ref"] for record in records}) == 169


def test_ga5_a_every_record_has_reachability_and_contract_evidence() -> None:
    manifest = _load(_MANIFEST_PATH)
    allowed_families = set(manifest["owner_families"])
    records = _projected_records()

    assert all(record["current_owner_refs"] for record in records)
    assert all(record["valid_protected_obligations"] for record in records)
    assert all(record["replacement_test_refs"] for record in records)
    assert {_owner_family(record) for record in records} <= allowed_families
    assert all(record["closure_state"] == "MIGRATED_CURRENT_OWNER" for record in records)
    assert not any(record["old_owner_restored"] for record in records)
    assert not any(record["skip_or_xfail_used"] for record in records)
    assert not any(record["exact_body_assert_added"] for record in records)


def test_ga5_b_f_o0_o5_projection_matches_declared_closure_counts() -> None:
    manifest = _load(_MANIFEST_PATH)
    counts = Counter(_ga5_batch(record) for record in _projected_records())
    declared = {
        batch: details["record_count"]
        for batch, details in manifest["closure_batches"].items()
    }
    assert {batch: counts.get(batch, 0) for batch in declared} == declared
    assert declared == {"O0": 0, "O1": 128, "O2": 11, "O3": 26, "O4": 1, "O5": 3}


def test_ga5_b_o0_migration_is_stable_from_backend_or_ai_pytest_root() -> None:
    migration = _migration_map()
    for record in _projected_records():
        canonical = record["baseline_failure_ref"]
        assert migration[canonical] == record["planned_repair_batch"]
        assert migration[canonical.removeprefix("ai/")] == (
            record["planned_repair_batch"]
        )


@pytest.mark.parametrize("source_batch", ("B1", "B2", "B3", "B4", "B5", "B6", "B7"))
def test_ga5_b_f_each_current_owner_assertion_is_green(source_batch: str) -> None:
    _ASSERTIONS[source_batch]()


def test_ga5_g_final_candidate_contract_is_fail_closed_and_body_free() -> None:
    manifest = _load(_MANIFEST_PATH)
    requirements = manifest["final_candidate_requirements"]
    boundary = manifest["execution_boundary"]

    assert requirements == {
        "ga3_v1_v3_green": True,
        "ga4_collection_error_count": 0,
        "ga5_failed_count": 0,
        "ga5_error_count": 0,
        "unclassified_failure_count": 0,
        "current_owner_missing_count": 0,
        "unresolved_stop_count": 0,
        "new_skip_or_xfail_count": 0,
        "source_fingerprint_stable_during_validation": True,
        "rn_app_source_required_for_v4": True,
    }
    assert boundary["old_owner_restored"] is False
    assert boundary["skip_or_xfail_used"] is False
    assert boundary["exact_body_assert_added"] is False
    assert boundary["production_contract_relaxed"] is False
    serialized = json.dumps(manifest, ensure_ascii=False, sort_keys=True)
    assert "comment_text" not in serialized
    assert "raw_input" not in serialized
    assert "surface_text" not in serialized
