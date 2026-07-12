# -*- coding: utf-8 -*-
from __future__ import annotations

"""Generate the immutable pre-repair Gate 0 RR0 freeze.

The source root may point at a separately extracted received archive.  This is
intentional: once RR1/RR2 files are added, the historical pre-repair snapshot
must not be silently redefined as the modified working tree.
"""

import argparse
import asyncio
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Sequence


SOURCE_ARCHIVE_REF = "mashos-api(207).zip"
SOURCE_ARCHIVE_SHA256 = "cfb378d93a7ff9d65542012ca3176cea6fb5f20f1a49756df16971eb37e93b00"
BODY_FREE_SCHEMA_VERSION = "cocolon.emlis.gate0.repair_freeze.bodyfree.v1"
BODY_LOCAL_SCHEMA_VERSION = "cocolon.emlis.gate0.repair_freeze.local_bodyfull.v1"
CYCLE_ID = "gate0_readfeel_repair_20260711"

_OWNER_SOURCE_PATHS = (
    "ai/services/ai_inference/emlis_ai_grounded_observation_plan.py",
    "ai/services/ai_inference/emlis_ai_grounded_sentence_surface.py",
    "ai/services/ai_inference/emlis_ai_grounded_observation_gate.py",
    "ai/services/ai_inference/emlis_ai_reply_service.py",
)
_RELEVANT_TEST_HELPER_PATHS = (
    "ai/tests/helpers/emlis_ai_grounded_observation_i0_inventory.py",
    "ai/tests/helpers/emlis_ai_grounded_observation_i6_cases.py",
    "ai/tests/helpers/emlis_ai_grounded_observation_i7_readfeel.py",
    "ai/tests/helpers/generate_emlis_ai_gate0_r8_r9_artifacts.py",
    "ai/tests/test_emlis_ai_gate0_r1_semantic_retention.py",
    "ai/tests/test_emlis_ai_gate0_r5_semantic_subchecks.py",
    "ai/tests/test_emlis_ai_gate0_r8_r10_boundary.py",
)
_REPAIR_CASE_IDS = (
    "A",
    "B",
    "C",
    "I6-L01",
    "I6-L02",
    "I6-L03",
    "I6-C01",
    "I6-C02",
    "I6-C03",
)
_COLLECTION_BLOCKERS = (
    {
        "test_path": "ai/tests/test_emlis_ai_bounded_repair_reroute_step7.py",
        "missing_symbol": "_regeneration_reasons_for_retry",
        "obsolete_import_owner": "emlis_ai_reply_service",
        "canonical_replacement_owners": [
            "emlis_ai_grounded_sentence_surface.build_plan_preserving_recovery_sequence",
            "emlis_ai_reply_service.render_emlis_ai_reply",
        ],
        "production_restore_allowed": False,
    },
    {
        "test_path": "ai/tests/test_emlis_ai_complete_initial_surface_recomposition_existing_gate_chain_p8.py",
        "missing_symbol": "_reply_service_recomposition_existing_gate_chain_summary",
        "obsolete_import_owner": "emlis_ai_reply_service",
        "canonical_replacement_owners": [
            "emlis_ai_grounded_sentence_surface.build_grounded_sentence_plan",
            "emlis_ai_grounded_sentence_surface.realize_grounded_sentence_plan",
            "emlis_ai_grounded_observation_gate.evaluate_grounded_observation_gate",
            "emlis_ai_reply_service.render_emlis_ai_reply",
        ],
        "production_restore_allowed": False,
    },
)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256_json(value: Any) -> str:
    return _sha256_bytes(_canonical_json_bytes(value))


def _file_sha256(root: Path, relative_path: str) -> str:
    return _sha256_bytes((root / relative_path).read_bytes())


def _snapshot_paths(source_root: Path) -> tuple[str, ...]:
    paths: list[str] = []
    for path in (source_root / "ai").rglob("*"):
        if not path.is_file() or path.suffix not in {".py", ".json"}:
            continue
        relative = path.relative_to(source_root).as_posix()
        parts = set(path.relative_to(source_root).parts)
        name = path.name
        if "__pycache__" in parts or ".pytest_cache" in parts or "local_only" in parts:
            continue
        if name.startswith(("emlis_gate0_r8_", "emlis_gate0_r9_", "emlis_gate0_r10_", "gate0_rr")):
            continue
        paths.append(relative)
    for name in ("pytest.ini", "pyproject.toml", "setup.cfg", "tox.ini"):
        if (source_root / name).is_file():
            paths.append(name)
    paths.extend(
        path.relative_to(source_root).as_posix()
        for path in source_root.glob("requirements*.txt")
        if path.is_file()
    )
    return tuple(sorted(set(paths)))


def _snapshot_fingerprint(source_root: Path) -> tuple[str, int]:
    paths = _snapshot_paths(source_root)
    digest = hashlib.sha256()
    for relative_path in paths:
        digest.update(relative_path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(_file_sha256(source_root, relative_path).encode("ascii"))
    return digest.hexdigest(), len(paths)


def _install_source_imports(source_root: Path) -> None:
    for path in (
        source_root / "ai" / "services" / "ai_inference",
        source_root / "ai" / "tests",
    ):
        sys.path.insert(0, str(path))


async def _build_artifacts(source_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    _install_source_imports(source_root)

    from helpers.emlis_ai_grounded_observation_i0_inventory import (  # noqa: PLC0415
        GROUND_OBSERVATION_I0_KNOWN_REGRESSION_CASES,
    )
    from helpers.emlis_ai_grounded_observation_i6_cases import (  # noqa: PLC0415
        GROUND_OBSERVATION_I6_BLIND_CASES,
    )
    from emlis_ai_current_input_bundle import normalize_emlis_current_input  # noqa: PLC0415
    from emlis_ai_evidence_ledger_service import (  # noqa: PLC0415
        build_evidence_ledger,
        build_evidence_span_resolver,
    )
    from emlis_ai_grounded_observation_plan import (  # noqa: PLC0415
        GROUND_OBSERVATION_PLAN_GENERATION_PATH,
        GROUND_OBSERVATION_PLAN_SCHEMA_VERSION,
        GROUND_OBSERVATION_PLAN_SEMANTIC_VERSION,
        build_grounded_observation_plan,
    )
    from emlis_ai_grounded_sentence_surface import (  # noqa: PLC0415
        GROUND_SENTENCE_PLAN_SCHEMA_VERSION,
        GROUND_SURFACE_RESULT_SCHEMA_VERSION,
        build_grounded_sentence_plan,
        expected_human_follow_role,
        realize_grounded_sentence_plan,
    )
    from emlis_ai_reply_service import render_emlis_ai_reply  # noqa: PLC0415

    test_root = source_root / "ai" / "tests"
    receipt_path = test_root / "fixtures" / "emlis_gate0_r8_karen_local_review_receipt_20260711.json"
    decision_path = test_root / "fixtures" / "emlis_gate0_r9_decision_20260711.json"
    comparison_path = test_root / "local_only" / "emlis_gate0_r8_local_comparison_20260711.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    decision = json.loads(decision_path.read_text(encoding="utf-8"))
    comparison = json.loads(comparison_path.read_text(encoding="utf-8"))
    comparison_by_case = {item["case_id"]: item for item in comparison["cases"]}

    snapshot_fingerprint, snapshot_file_count = _snapshot_fingerprint(source_root)
    source_hashes = {
        path: _file_sha256(source_root, path)
        for path in (*_OWNER_SOURCE_PATHS, *_RELEVANT_TEST_HELPER_PATHS)
    }
    cases = (
        *GROUND_OBSERVATION_I0_KNOWN_REGRESSION_CASES,
        *GROUND_OBSERVATION_I6_BLIND_CASES,
    )
    body_free_cases: list[dict[str, Any]] = []
    body_local_cases: list[dict[str, Any]] = []
    for case in cases:
        normalized = normalize_emlis_current_input(case.as_current_input())
        spans = tuple(build_evidence_ledger(normalized))
        resolver = build_evidence_span_resolver(spans, current_input=normalized)
        plan = build_grounded_observation_plan(normalized, evidence_spans=spans)
        sentence_plan = build_grounded_sentence_plan(plan, resolver)
        surface = realize_grounded_sentence_plan(sentence_plan, plan, resolver)
        reply = await render_emlis_ai_reply(
            user_id="gate0-rr0-current-freeze",
            subscription_tier="free",
            current_input=case.as_current_input(),
        )
        plan_meta = plan.as_body_free_meta()
        sentence_meta = sentence_plan.as_body_free_meta()
        surface_meta = surface.as_body_free_meta()
        nucleus_index = {item.nucleus_id: item for item in plan.nuclei}
        follow_ids = tuple(plan.response_plan.human_follow_target_ids)
        follow_role = (
            expected_human_follow_role(plan, follow_ids, nucleus_index)
            if follow_ids
            else ""
        )
        anchor_occurrences: dict[str, list[str]] = {
            nucleus.nucleus_id: [] for nucleus in plan.nuclei
        }
        for line in sentence_plan.lines:
            for nucleus_id in line.binding.nucleus_ids:
                anchor_occurrences.setdefault(nucleus_id, []).append(line.binding.sentence_id)
        body_hash = _sha256_bytes(reply.comment_text.encode("utf-8"))
        input_hash = _sha256_json(normalized)
        prior = comparison_by_case[case.case_id]
        if body_hash != prior["after_body_sha256"]:
            raise RuntimeError(f"current_receipt_generated_body_hash_mismatch:{case.case_id}")
        if input_hash != prior["normalized_current_input_sha256"]:
            raise RuntimeError(f"current_receipt_input_hash_mismatch:{case.case_id}")
        review = next(item for item in receipt["reviews"] if item["case_id"] == case.case_id)
        body_free_cases.append(
            {
                "case_id": case.case_id,
                "normalized_current_input_sha256": input_hash,
                "current_body_sha256": body_hash,
                "plan_signature_sha256": _sha256_json(plan_meta),
                "sentence_plan_signature_sha256": _sha256_json(sentence_meta),
                "surface_signature_sha256": _sha256_json(surface_meta),
                "follow_target_ids": list(follow_ids),
                "follow_role_atom": follow_role,
                "relations": [
                    {
                        "relation_id": item.relation_id,
                        "type": item.type,
                        "from_nucleus_id": item.from_nucleus_id,
                        "to_nucleus_id": item.to_nucleus_id,
                        "retention": item.retention,
                    }
                    for item in plan.relations
                ],
                "anchor_to_line_occurrence_signature_sha256": _sha256_json(anchor_occurrences),
                "reason_refs": list(review["fatal_reason_refs"]),
                "verdict": review["verdict"],
            }
        )
        body_local_cases.append(
            {
                "case_id": case.case_id,
                "normalized_current_input": normalized,
                "current_body": reply.comment_text,
                "current_body_sha256": body_hash,
                "current_plan_body_free_debug": plan_meta,
                "current_sentence_plan_body_free_debug": sentence_meta,
                "current_surface_body_free_debug": surface_meta,
            }
        )

    case_order = [item["case_id"] for item in body_free_cases]
    repair_ids = [item["case_id"] for item in body_free_cases if item["verdict"] == "repair_required"]
    if len(case_order) != 16 or tuple(repair_ids) != _REPAIR_CASE_IDS:
        raise RuntimeError("current_16_or_repair_9_mismatch")
    if (
        receipt["local_human_pass_count"],
        receipt["repair_required_count"],
        receipt["hard_fatal_count"],
    ) != (7, 9, 0):
        raise RuntimeError("current_review_count_mismatch")
    if decision.get("decision_code") != "GATE0_REPAIR_RETURN_STOPPED":
        raise RuntimeError("current_r9_decision_mismatch")

    body_free = {
        "schema_version": BODY_FREE_SCHEMA_VERSION,
        "cycle_id": CYCLE_ID,
        "source_archive_ref": SOURCE_ARCHIVE_REF,
        "source_archive_sha256": SOURCE_ARCHIVE_SHA256,
        "source_snapshot_fingerprint": snapshot_fingerprint,
        "source_snapshot_file_count": snapshot_file_count,
        "source_snapshot_algorithm": "sha256(relative_path_utf8 + NUL + lowercase_file_sha256_ascii), path_sorted",
        "source_snapshot_includes": [
            "ai/**/*.py",
            "ai/**/*.json",
            "requirements*.txt",
            "pytest configuration",
        ],
        "source_snapshot_excludes": [
            "__pycache__",
            ".pytest_cache",
            "*.pyc",
            "ai/tests/local_only/**",
            "R8/R9/R10 and RR generated artifacts",
        ],
        "source_file_sha256s": source_hashes,
        "canonical_versions": {
            "grounded_observation_plan_schema": GROUND_OBSERVATION_PLAN_SCHEMA_VERSION,
            "grounded_observation_plan_semantic": GROUND_OBSERVATION_PLAN_SEMANTIC_VERSION,
            "grounded_observation_generation_path": GROUND_OBSERVATION_PLAN_GENERATION_PATH,
            "grounded_sentence_plan_schema": GROUND_SENTENCE_PLAN_SCHEMA_VERSION,
            "grounded_surface_result_schema": GROUND_SURFACE_RESULT_SCHEMA_VERSION,
        },
        "case_order": case_order,
        "case_count": len(case_order),
        "repair_case_ids": repair_ids,
        "cases": body_free_cases,
        "review": {
            "r8_receipt_sha256": _file_sha256(
                source_root,
                receipt_path.relative_to(source_root).as_posix(),
            ),
            "r9_decision_sha256": _file_sha256(
                source_root,
                decision_path.relative_to(source_root).as_posix(),
            ),
            "review_source_archive_sha256": receipt["snapshot_fingerprint"],
            "local_human_pass_count": 7,
            "repair_required_count": 9,
            "hard_fatal_count": 0,
            "decision_code": decision["decision_code"],
            "generated_body_hashes_match_current_r8_comparison": True,
        },
        "collection_blockers": list(_COLLECTION_BLOCKERS),
        "raw_input_included": False,
        "returned_surface_included": False,
        "comment_text_included": False,
    }
    body_local = {
        "schema_version": BODY_LOCAL_SCHEMA_VERSION,
        "cycle_id": CYCLE_ID,
        "artifact_scope": "local_only_body_full_do_not_copy_to_public_meta",
        "source_archive_ref": SOURCE_ARCHIVE_REF,
        "source_archive_sha256": SOURCE_ARCHIVE_SHA256,
        "source_snapshot_fingerprint": snapshot_fingerprint,
        "case_count": len(body_local_cases),
        "subscription_tier": "free",
        "history_context_used": False,
        "cases": body_local_cases,
    }
    return body_free, body_local


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args(argv)
    source_root = args.source_root.resolve()
    output_root = args.output_root.resolve()
    body_free, body_local = asyncio.run(_build_artifacts(source_root))
    _write_json(
        output_root / "ai" / "tests" / "fixtures" / "gate0_rr0_freeze_20260711.json",
        body_free,
    )
    _write_json(
        output_root / "ai" / "tests" / "local_only" / "gate0_rr0_body_local_20260711.json",
        body_local,
    )


if __name__ == "__main__":
    main()
