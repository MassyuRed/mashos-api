# -*- coding: utf-8 -*-
from __future__ import annotations

"""Generate the Gate A GA0 body-free baseline and local-only body material.

The source root must be an untouched extraction of the received archive.  The
output root may be the working tree.  This preserves the pre-GA1 fingerprint
without adding a self-reference through the generated evidence.
"""

import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any, Sequence
import xml.etree.ElementTree as ET


SOURCE_ARCHIVE_REF = "mashos-api(214).zip"
SOURCE_ARCHIVE_SHA256 = "9fbe8ed2ba6b0d245a60aa4f6f0c6a73cce5c58f77adfbaa4f6a5769ba72b9f7"
SOURCE_SNAPSHOT_FINGERPRINT = "394b5da7a9546d5f893e00fe27417e2e10231dcc267a2d728e6f11025d2aa0c3"
SOURCE_SNAPSHOT_FILE_COUNT = 1359
SAME16_BODY_FREE_SIGNATURE_SHA256 = "33b2431216abb243c0fcee43dbe8dfe6bf81546c1df6e37b453d04ce449e475b"
HISTORICAL_FB172_LEDGER_SHA256 = "7a166e785c387c30cf89c6935da4c086cee6d870d8a121b4f6d7ffa796a3587c"

BODY_FREE_SCHEMA_VERSION = "cocolon.emlis.gatea.freeze.bodyfree.v1"
BODY_LOCAL_SCHEMA_VERSION = "cocolon.emlis.gatea.freeze.local_bodyfull.v1"
CYCLE_ID = "p7_gatea_post_fb172_current_input_closure_20260711"

_OWNER_SOURCE_PATHS = (
    "ai/services/ai_inference/emlis_ai_grounded_observation_plan.py",
    "ai/services/ai_inference/emlis_ai_grounded_sentence_surface.py",
    "ai/services/ai_inference/emlis_ai_grounded_observation_gate.py",
    "ai/services/ai_inference/emlis_ai_reply_service.py",
)
_DIAGNOSTIC_REASON_REFS_BY_CASE: dict[str, tuple[str, ...]] = {
    "A": (),
    "B": (
        "mechanical_relation_surface_stem_repetition",
        "relation_line_pairwise_fragmentation",
        "dependent_clause_or_quote_join_readability",
    ),
    "C": (
        "mechanical_relation_surface_stem_repetition",
        "relation_line_pairwise_fragmentation",
        "generic_retained_intention_tail_overused",
        "generic_tail_role_or_scope_mismatch",
    ),
    "D": (
        "human_follow_repeats_already_delivered_target",
        "self_denial_counterdirection_duplicate",
    ),
    "I6-S01": ("short_state_depth_requires_actual_human_review",),
    "I6-S02": ("short_state_depth_requires_actual_human_review",),
    "I6-S03": ("short_state_depth_requires_actual_human_review",),
    "I6-L01": (
        "relation_line_pairwise_fragmentation",
        "generic_retained_intention_tail_overused",
        "generic_tail_role_or_scope_mismatch",
    ),
    "I6-L02": (
        "relation_line_pairwise_fragmentation",
        "generic_retained_intention_tail_overused",
        "generic_tail_role_or_scope_mismatch",
    ),
    "I6-L03": (
        "relation_line_pairwise_fragmentation",
        "generic_retained_intention_tail_overused",
        "generic_tail_role_or_scope_mismatch",
    ),
    "I6-C01": (
        "generic_retained_intention_tail_overused",
        "generic_tail_role_or_scope_mismatch",
    ),
    "I6-C02": (
        "generic_retained_intention_tail_overused",
        "generic_tail_role_or_scope_mismatch",
    ),
    "I6-C03": (
        "generic_retained_intention_tail_overused",
        "generic_tail_role_or_scope_mismatch",
    ),
    "I6-D01": (
        "human_follow_repeats_already_delivered_target",
        "self_denial_counterdirection_duplicate",
    ),
    "I6-D02": ("human_follow_repeats_already_delivered_target",),
    "I6-D03": ("human_follow_repeats_already_delivered_target",),
}
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


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
        if "__pycache__" in parts or ".pytest_cache" in parts or "local_only" in parts:
            continue
        if path.name.startswith(("emlis_gate0_r8_", "emlis_gate0_r9_", "emlis_gate0_r10_", "gate0_rr")):
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


def _pytest_node_ref(testcase: ET.Element) -> str:
    classname = testcase.attrib.get("classname", "").strip()
    name = testcase.attrib.get("name", "").strip()
    if not classname or not name:
        raise RuntimeError("junit_testcase_missing_classname_or_name")
    parts = classname.split(".")
    class_parts: list[str] = []
    while parts and parts[-1][:1].isupper():
        class_parts.insert(0, parts.pop())
    path = "/".join(parts) + ".py"
    suffix = "::".join((*class_parts, name))
    return f"ai/{path}::{suffix}"


def _read_junit_failure_set(junit_path: Path) -> dict[str, Any]:
    root = ET.parse(junit_path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.findall("testsuite"))
    testcases = [case for suite in suites for case in suite.iter("testcase")]
    failure_refs = [
        _pytest_node_ref(case)
        for case in testcases
        if case.find("failure") is not None or case.find("error") is not None
    ]
    skipped_count = sum(case.find("skipped") is not None for case in testcases)
    if len(failure_refs) != len(set(failure_refs)):
        raise RuntimeError("baseline_failure_node_ref_duplicate")
    if failure_refs != sorted(failure_refs):
        order = "pytest_execution_order"
    else:
        order = "lexicographic"
    node_refs_sha256 = _sha256_json(failure_refs)
    return {
        "passed_count": len(testcases) - len(failure_refs) - skipped_count,
        "failed_count": len(failure_refs),
        "skipped_count": skipped_count,
        "failure_node_ref_order": order,
        "failure_node_refs": failure_refs,
        "failure_node_refs_sha256": node_refs_sha256,
        "failure_set_id": f"post_fb172_residual_{node_refs_sha256[:12]}",
        "failure_node_ref_duplicate_count": 0,
    }


async def _build_same16(source_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    _install_source_imports(source_root)
    from helpers.emlis_ai_grounded_observation_i0_inventory import (  # noqa: PLC0415
        GROUND_OBSERVATION_I0_KNOWN_REGRESSION_CASES,
    )
    from helpers.emlis_ai_grounded_observation_i6_cases import (  # noqa: PLC0415
        GROUND_OBSERVATION_I6_BLIND_CASES,
    )
    from emlis_ai_current_input_bundle import normalize_emlis_current_input  # noqa: PLC0415
    from emlis_ai_grounded_observation_gate import (  # noqa: PLC0415
        GROUND_OBSERVATION_GATE_SCHEMA_VERSION,
    )
    from emlis_ai_grounded_observation_plan import (  # noqa: PLC0415
        GROUND_OBSERVATION_PLAN_GENERATION_PATH,
        GROUND_OBSERVATION_PLAN_SCHEMA_VERSION,
        GROUND_OBSERVATION_PLAN_SEMANTIC_VERSION,
    )
    from emlis_ai_grounded_sentence_surface import (  # noqa: PLC0415
        GROUND_SENTENCE_PLAN_SCHEMA_VERSION,
        GROUND_SURFACE_GENERATION_PATH,
        GROUND_SURFACE_RESULT_SCHEMA_VERSION,
    )
    from emlis_ai_reply_service import render_emlis_ai_reply  # noqa: PLC0415

    rows: list[dict[str, Any]] = []
    local_rows: list[dict[str, Any]] = []
    cases = (
        *GROUND_OBSERVATION_I0_KNOWN_REGRESSION_CASES,
        *GROUND_OBSERVATION_I6_BLIND_CASES,
    )
    for case in cases:
        current_input = case.as_current_input()
        normalized = normalize_emlis_current_input(current_input)
        reply = await render_emlis_ai_reply(
            user_id="gatea-ga0-readonly",
            subscription_tier="free",
            current_input=current_input,
        )
        body_sha256 = _sha256_bytes(reply.comment_text.encode("utf-8"))
        row = {
            "case_id": case.case_id,
            "body_sha256": body_sha256,
            "character_count": len(reply.comment_text),
            "line_count": len(reply.comment_text.splitlines()),
        }
        rows.append(row)
        local_rows.append(
            {
                **row,
                "normalized_current_input": normalized,
                "current_body": reply.comment_text,
            }
        )
    if _sha256_json(rows) != SAME16_BODY_FREE_SIGNATURE_SHA256:
        raise RuntimeError("same16_body_free_signature_mismatch")
    body_free_cases = [
        {**row, "reason_refs": list(_DIAGNOSTIC_REASON_REFS_BY_CASE[row["case_id"]])}
        for row in rows
    ]
    versions = {
        "semantic": GROUND_OBSERVATION_PLAN_SEMANTIC_VERSION,
        "plan_schema": GROUND_OBSERVATION_PLAN_SCHEMA_VERSION,
        "plan_generation_path": GROUND_OBSERVATION_PLAN_GENERATION_PATH,
        "sentence_plan_schema": GROUND_SENTENCE_PLAN_SCHEMA_VERSION,
        "surface_schema": GROUND_SURFACE_RESULT_SCHEMA_VERSION,
        "surface_generation_path": GROUND_SURFACE_GENERATION_PATH,
        "gate_schema": GROUND_OBSERVATION_GATE_SCHEMA_VERSION,
        "public_generation_path": "grounded_observation_plan_sentence_surface_canonical_v1",
        "composer_source": "grounded_plan_realizer",
    }
    return (
        {
            "case_order": [row["case_id"] for row in rows],
            "case_count": len(rows),
            "body_free_signature_sha256": _sha256_json(rows),
            "diagnostic_claim": "read_only_diagnostic_not_official_human_pass",
            "official_local_review_started": False,
            "cases": body_free_cases,
            "canonical_versions": versions,
        },
        {
            "schema_version": BODY_LOCAL_SCHEMA_VERSION,
            "cycle_id": CYCLE_ID,
            "artifact_scope": "local_only_body_full_do_not_copy_to_public_meta",
            "source_archive_ref": SOURCE_ARCHIVE_REF,
            "source_snapshot_fingerprint": SOURCE_SNAPSHOT_FINGERPRINT,
            "case_count": len(local_rows),
            "cases": local_rows,
        },
    )


async def _build_artifacts(
    source_root: Path,
    junit_path: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    fingerprint, file_count = _snapshot_fingerprint(source_root)
    if (fingerprint, file_count) != (
        SOURCE_SNAPSHOT_FINGERPRINT,
        SOURCE_SNAPSHOT_FILE_COUNT,
    ):
        raise RuntimeError("received_source_snapshot_mismatch")
    same16, local = await _build_same16(source_root)
    backend = _read_junit_failure_set(junit_path)
    if (backend["passed_count"], backend["failed_count"], backend["skipped_count"]) != (
        12543,
        169,
        2,
    ):
        raise RuntimeError("official_full_backend_count_mismatch")
    ledger_path = source_root / "ai" / "tests" / "fixtures" / "fb172_owner_ledger_20260712.json"
    ledger_sha256 = _sha256_bytes(ledger_path.read_bytes())
    if ledger_sha256 != HISTORICAL_FB172_LEDGER_SHA256:
        raise RuntimeError("historical_fb172_ledger_hash_mismatch")
    payload = {
        "schema_version": BODY_FREE_SCHEMA_VERSION,
        "cycle_id": CYCLE_ID,
        "source_archive_ref": SOURCE_ARCHIVE_REF,
        "source_archive_sha256": SOURCE_ARCHIVE_SHA256,
        "source_snapshot_fingerprint": fingerprint,
        "source_snapshot_file_count": file_count,
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
        "source_file_sha256s": {
            path: _file_sha256(source_root, path) for path in _OWNER_SOURCE_PATHS
        },
        "canonical_versions": same16.pop("canonical_versions"),
        "same16": same16,
        "full_collect": {
            "return_code": 0,
            "collected_test_count": 12714,
            "collection_error_count": 0,
            "collection_error_refs": [],
        },
        "full_backend": {"return_code": 1, **backend},
        "historical_fb172": {
            "ledger_ref": "ai/tests/fixtures/fb172_owner_ledger_20260712.json",
            "ledger_sha256": ledger_sha256,
            "mutated": False,
        },
        "environment": {
            "python_version": "3.12.13",
            "pytest_version": "8.4.2",
            "pytest_asyncio_version": "1.0.0",
            "fastapi_version": "0.115.12",
            "starlette_version": "0.46.2",
            "pydantic_version": "2.11.7",
            "httpx_version": "0.28.1",
            "worker_count": 1,
            "import_mode": "prepend",
            "cwd_ref": "mashos-api/ai",
            "dependency_precedence_ref": "cocolon_test_deps_before_cocolon_pytest",
            "nonbaseline_probe": {
                "fastapi_version": "0.139.0",
                "observed_failed_count": 171,
                "extra_failure_count": 2,
                "extra_failure_owner": "fastapi_include_router_internal_representation_drift",
                "source_change_required": False,
            },
        },
        "raw_input_included": False,
        "returned_surface_included": False,
        "comment_text_included": False,
    }
    return payload, local


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
    parser.add_argument("--junitxml", type=Path, required=True)
    args = parser.parse_args(argv)
    body_free, body_local = asyncio.run(
        _build_artifacts(
            args.source_root.resolve(),
            args.junitxml.resolve(),
        )
    )
    output_root = args.output_root.resolve()
    _write_json(
        output_root / "ai" / "tests" / "local_only" / "gatea_ga0_freeze_bodyfree_20260712.json",
        body_free,
    )
    _write_json(
        output_root / "ai" / "tests" / "local_only" / "gatea_ga0_body_local_20260712.json",
        body_local,
    )


if __name__ == "__main__":
    main()
