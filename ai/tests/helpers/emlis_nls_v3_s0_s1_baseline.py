# -*- coding: utf-8 -*-
from __future__ import annotations

"""Build and verify the NLS v3 Step 0/1 freeze artifacts.

This helper is test-only.  It does not implement the v3 surface and it never
imports the stopped v2 implementation.  Step 0 freezes the version boundary;
Step 1 captures the current canonical-v1 output, Gate, latency, actual RN input
contract, backend compatibility gap, and known-regression provenance.

Body-full known-fixture inputs and v1 replies stay in the local-only artifact.
The shareable receipt contains HMAC commitments and metrics only.
"""

import argparse
import ast
import asyncio
from collections import Counter
from dataclasses import dataclass
import hashlib
import hmac
import json
import math
from pathlib import Path
import platform
import re
import secrets
import statistics
import sys
import time
from typing import Any, Iterable, Mapping, Sequence


_AI_ROOT = Path(__file__).resolve().parents[2]
_REPO_ROOT = _AI_ROOT.parent
_TEST_ROOT = _AI_ROOT / "tests"
_INFERENCE_ROOT = _AI_ROOT / "services" / "ai_inference"
if str(_INFERENCE_ROOT) not in sys.path:
    sys.path.insert(0, str(_INFERENCE_ROOT))

from emlis_ai_public_feedback_meta import (  # noqa: E402
    build_public_emlis_input_feedback_meta,
    should_include_public_input_feedback,
)
from emlis_ai_grounded_observation_plan import (  # noqa: E402
    build_grounded_observation_plan,
)
from emlis_ai_reply_service import render_emlis_ai_reply  # noqa: E402
from emlis_ai_grounded_sentence_surface import split_two_stage_surface  # noqa: E402
from helpers.emlis_ai_grounded_human_reception_r6_qa import (  # noqa: E402
    split_reception_sentences,
)
from helpers.emlis_ai_grounded_observation_i6_cases import (  # noqa: E402
    GROUND_OBSERVATION_I6_BLIND_CASES,
)


S0_SCHEMA_VERSION = "cocolon.emlis.nls_v3.step0_version_boundary.v1"
S1_INPUT_SCHEMA_VERSION = "cocolon.emlis.nls_v3.step1_input_contract.v1"
S1_VISIBLE_SCHEMA_VERSION = "cocolon.emlis.nls_v3.step1_v1_visible.local_only.v1"
S1_RECEIPT_SCHEMA_VERSION = "cocolon.emlis.nls_v3.step1_baseline_receipt.v1"

S0_PATH = _TEST_ROOT / "fixtures" / "emlis_nls_v3_s0_boundary_20260714.json"
S1_INPUT_PATH = (
    _TEST_ROOT / "fixtures" / "emlis_nls_v3_s1_input_contract_20260714.json"
)
S1_VISIBLE_PATH = (
    _TEST_ROOT / "local_only" / "emlis_nls_v3_s1_v1_visible_20260714.json"
)
S1_RECEIPT_PATH = (
    _TEST_ROOT / "fixtures" / "emlis_nls_v3_s1_baseline_receipt_20260714.json"
)

EXACT8_PATH = _TEST_ROOT / "fixtures" / "grounded_human_reception_exact8_v2_20260712.json"
UNSEEN12_PATH = _TEST_ROOT / "local_only" / "grounded_human_reception_rr8_unseen12_20260713.json"
I6_PATH = _TEST_ROOT / "helpers" / "emlis_ai_grounded_observation_i6_cases.py"
V2_AUDIT_PATH = _TEST_ROOT / "fixtures" / "emlis_nls_v2_all_steps_audit_20260713.json"
KNOWN_DEVICE4_RECEIPT_PATH = (
    _TEST_ROOT / "fixtures" / "emlis_nls_v2_s12_s13_device_blocked_20260713.json"
)
KNOWN_DEVICE4_TEST_PATH = _TEST_ROOT / "test_emlis_nls_v2_s12_s13_device_blocked.py"
KNOWN_DEVICE4_RESULT_PATH = (
    _AI_ROOT
    / "docs"
    / "Cocolon_EmlisAI_NLSv2_S12_S13_DeviceCheck_Blocked_Result_20260713.md"
)
RR10_READINESS_PATH = (
    _TEST_ROOT
    / "fixtures"
    / "grounded_human_reception_rr10_representative4_device_readiness_20260713.json"
)
RR10_EXPECTED_PACKET_PATH = (
    _TEST_ROOT
    / "local_only"
    / "grounded_human_reception_rr10_representative4_expected_packet_20260713.json"
)
RR10_EVIDENCE_TEMPLATE_PATH = (
    _TEST_ROOT
    / "local_only"
    / "grounded_human_reception_rr10_actual_device_evidence_template_20260713.json"
)
RR10_EVIDENCE_VERIFIER_PATH = (
    _AI_ROOT / "tools" / "emlis_grounded_human_reception_rr10_verify_device_evidence.py"
)

DESIGN_SHA256 = "6aa3fb799919ac30b0eb84571ac4009d62a2bd799c84322272a59bba533f13bc"
BACKEND_ARCHIVE_SHA256 = "f97df95b5f7065854826051636d7d8223db49f7b1fce958697c4ae20f6a42415"
RN_ARCHIVE_SHA256 = "2287550897799bee5ce1ac8a4235f4aa364ed7ef088c1bd3ef7d84fd2d009100"
PREMISE_ARCHIVE_SHA256 = "c2c2f3d4d71127b5ee7e029f3240dfb2b8f33c3e34b1c0b47c28c20ec73d4d5b"
IMPLEMENTED_DOCS_ARCHIVE_SHA256 = "d3e756cea48b817f28ce38a9cdefac889d93ba5ecf33261152d4083197313a4d"
ROADMAP_SHA256 = "04fb9e4e11af2b1530d03d95d8e959ba644503722f72094a289bde1d4368ce5b"
KNOWN_DEVICE4_RECEIPT_SHA256 = (
    "5677675b30cdf32a5cb56a52b81a12766ba2902af8e24237111d53bf0988fb29"
)
KNOWN_DEVICE4_TEST_SHA256 = (
    "222ce7cd5c29bfc64668a2d1c04dab7cf0b60f811a790c5b79f41c3f79ece94c"
)
KNOWN_DEVICE4_RESULT_SHA256 = (
    "e1e88b98c20d762417bf77a7ed491dfdf0056bc2f3b90df2d40956baa845fbdb"
)
RR10_READINESS_SHA256 = (
    "fdb7d67b075cb78cbb2e3cd0170d88fb489fccf22c80ef35a271329984a52f82"
)
RR10_EXPECTED_PACKET_SHA256 = (
    "f4f03dd10088ad18a56e925a02a4aebd06e31b126c6c2230869d5e17c6d03576"
)
RR10_EVIDENCE_TEMPLATE_SHA256 = (
    "b0be832a8e55238523620a99b1a282c4517c36bdb8afb481ac08698623a01241"
)
RR10_EVIDENCE_VERIFIER_SHA256 = (
    "6185bcea0e7f900f7aec805af9c05349b88d8aff2ce5e98af79a4d062211bc82"
)
HISTORICAL_SOURCE_OWNER_SNAPSHOT_SHA256 = (
    "ed9d7463778909c97115096345d25d6ce260d21ed737a72d7c06ccd8e08687ac"
)
HISTORICAL_DEPENDENCY_CLOSURE_SHA256 = (
    "3d42e942239666dc37d14c9c2969d548988c02e38ac497bb65b825d9b4c1f3bd"
)

SOURCE_OWNER_PATHS = (
    "ai/services/ai_inference/emlis_ai_grounded_observation_plan.py",
    "ai/services/ai_inference/emlis_ai_grounded_human_reception.py",
    "ai/services/ai_inference/emlis_ai_grounded_sentence_surface.py",
    "ai/services/ai_inference/emlis_ai_grounded_observation_gate.py",
    "ai/services/ai_inference/emlis_ai_reply_service.py",
)
DEPENDENCY_ENTRY_PATH = "ai/services/ai_inference/emlis_ai_reply_service.py"
PUBLIC_BACKEND_PATHS = (
    "ai/services/ai_inference/api_emotion_submit.py",
    "ai/services/ai_inference/emotion_submit_service.py",
    "ai/services/ai_inference/emlis_ai_current_input_bundle.py",
    "ai/services/ai_inference/emlis_ai_public_feedback_meta.py",
)
RESOURCE_BOUND_OWNER_PATHS = (
    "ai/services/ai_inference/api_emotion_submit.py",
    "ai/services/ai_inference/emlis_ai_evidence_ledger_service.py",
    "ai/services/ai_inference/emlis_ai_perspective_observers.py",
    "ai/services/ai_inference/emlis_ai_observation_integrator_service.py",
    "ai/services/ai_inference/emlis_ai_safety_triage.py",
    "ai/services/ai_inference/emlis_ai_grounded_observation_plan.py",
)
V2_SOURCE_PATHS = (
    "ai/services/ai_inference/emlis_ai_grounded_reception_content_plan_v2.py",
    "ai/services/ai_inference/emlis_ai_grounded_reception_candidate_plan_v2.py",
    "ai/services/ai_inference/emlis_ai_grounded_human_reception_v2.py",
    "ai/services/ai_inference/emlis_ai_grounded_reception_candidate_selector_v2.py",
)

RUNTIME_STATES = (
    "disabled",
    "offline",
    "shadow",
    "tester_only_preview",
    "owner",
    "stopped",
)
OBSERVATION_STAGES = (
    "normal_observation",
    "pre_question_observation",
    "refined_observation",
)
EMOTION_TYPES = ("喜び", "悲しみ", "怒り", "不安", "平穏", "自己理解")
STRENGTHS = ("weak", "medium", "strong")
CATEGORY_TYPES = (
    "生活",
    "仕事",
    "趣味",
    "人間関係",
    "恋愛",
    "健康",
    "学習",
    "価値観",
    "人生",
)

RN_OWNER_ROWS = (
    ("screens/input/inputOptions.js", "8463777a6d44eb7047cba18b80ceb15697d8815daf5d06f34b012b32271ac2a7"),
    ("screens/InputScreen.js", "6c82c1ac5bdd9a8eef06f64986f3a054ed6971f01a5ed154f3ddc6d63874e04d"),
    ("screens/input/InputEmotionSection.js", "0621aa08a3e4be728b06bb65792165661614b7d429bde947f3a91ae29bf54cbe"),
    ("screens/input/InputCategorySection.js", "1a805e8d01586cb501219f92dc7b7df00e79e0de1c2370601520e9f5459efa7f"),
    ("screens/input/InputMemoSection.js", "9f0663def2703e04be7259fa6a2d2fcb2f3f20238deb718c2d5bf56c9cbc700c"),
    ("screens/input/inputDraftModel.js", "c57a95de2351fea3bdfcb3b3848bc0036820090d23bb23096762a5d18941e15d"),
)

_EXACT8_I6_CASE_IDS = frozenset({"I6-S03", "I6-L03", "I6-C01", "I6-D02"})
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_QUOTE_RE = re.compile(r"「([^」]+)」|『([^』]+)』")
_WHITESPACE_RE = re.compile(r"\s+")
_FORBIDDEN_BODY_KEYS = frozenset(
    {
        "memo",
        "memo_action",
        "current_input",
        "raw_input",
        "raw_text",
        "source_text",
        "comment_text",
        "visible_surface",
        "observation_section",
        "reception_section",
        "candidate_text",
        "candidate_surface",
        "commitment_key_hex",
    }
)


@dataclass(frozen=True)
class BaselineCase:
    case_id: str
    cohort: str
    family: str
    current_input: Mapping[str, Any]
    source_ref: str


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(str(value).encode("utf-8"))


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_json(value: Any) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def hmac_commit_json(key_hex: str, domain: str, value: Any) -> str:
    key = bytes.fromhex(key_hex)
    payload = domain.encode("utf-8") + b"\0" + canonical_json_bytes(value)
    return hmac.new(key, payload, hashlib.sha256).hexdigest()


def hmac_commit_text(key_hex: str, domain: str, value: str) -> str:
    key = bytes.fromhex(key_hex)
    payload = domain.encode("utf-8") + b"\0" + str(value).encode("utf-8")
    return hmac.new(key, payload, hashlib.sha256).hexdigest()


def _rows(paths: Iterable[str]) -> list[dict[str, str]]:
    return [
        {"path": path, "sha256": sha256_file(_REPO_ROOT / path)}
        for path in paths
    ]


def current_source_owner_snapshot() -> tuple[list[dict[str, str]], str]:
    """Return a fresh hash snapshot of the currently checked-out owners."""

    rows = _rows(SOURCE_OWNER_PATHS)
    return rows, sha256_json(rows)


def historical_source_owner_snapshot() -> tuple[list[dict[str, str]], str]:
    """Return the owner snapshot frozen by Step 0 on 2026-07-14.

    Step 0 records the then-current production boundary.  Later dormant
    integration work may legitimately change the wrapper source without
    rewriting that historical claim, so this verifier reads the immutable
    fixture instead of silently redefining Step 0 as the current checkout.
    """

    frozen = load_json(S0_PATH)
    runtime = frozen.get("current_runtime")
    if not isinstance(runtime, Mapping):
        raise ValueError("step0_historical_runtime_missing")
    raw_rows = runtime.get("source_owner_files")
    frozen_hash = runtime.get("source_owner_snapshot_sha256")
    if not isinstance(raw_rows, list) or not isinstance(frozen_hash, str):
        raise ValueError("step0_historical_owner_snapshot_missing")
    rows = [dict(row) for row in raw_rows if isinstance(row, Mapping)]
    if (
        len(rows) != len(raw_rows)
        or frozen_hash != HISTORICAL_SOURCE_OWNER_SNAPSHOT_SHA256
        or sha256_json(rows) != frozen_hash
    ):
        raise ValueError("step0_historical_owner_snapshot_invalid")
    return rows, frozen_hash


def source_owner_snapshot() -> tuple[list[dict[str, str]], str]:
    """Compatibility name for the Step 0 historical snapshot."""

    return historical_source_owner_snapshot()


def public_backend_snapshot() -> tuple[list[dict[str, str]], str]:
    rows = _rows(PUBLIC_BACKEND_PATHS)
    return rows, sha256_json(rows)


def _module_index() -> tuple[dict[str, Path], dict[Path, str]]:
    by_module: dict[str, Path] = {}
    by_path: dict[Path, str] = {}
    for path in sorted(_INFERENCE_ROOT.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        rel = path.relative_to(_INFERENCE_ROOT)
        parts = list(rel.parts)
        if parts[-1] == "__init__.py":
            parts = parts[:-1]
        else:
            parts[-1] = Path(parts[-1]).stem
        if not parts:
            continue
        module = ".".join(parts)
        by_module[module] = path
        by_path[path] = module
    return by_module, by_path


def _imported_local_modules(path: Path, module: str, index: Mapping[str, Path]) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: set[str] = set()
    package = module.rpartition(".")[0]
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            candidates = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            raw = node.module or ""
            if node.level:
                package_parts = package.split(".") if package else []
                keep = max(0, len(package_parts) - node.level + 1)
                prefix = ".".join(package_parts[:keep])
                base = ".".join(part for part in (prefix, raw) if part)
            else:
                base = raw
            candidates = [base]
            candidates.extend(
                ".".join(part for part in (base, alias.name) if part)
                for alias in node.names
                if alias.name != "*"
            )
        else:
            continue
        for candidate in candidates:
            if candidate in index:
                found.add(candidate)
    return found


def current_dependency_closure() -> tuple[list[dict[str, str]], str]:
    """Return the live transitive local dependency closure of the v1 entry."""

    index, reverse = _module_index()
    entry_path = _REPO_ROOT / DEPENDENCY_ENTRY_PATH
    entry_module = reverse[entry_path]
    pending = [entry_module]
    visited: set[str] = set()
    while pending:
        module = pending.pop()
        if module in visited:
            continue
        visited.add(module)
        pending.extend(
            sorted(_imported_local_modules(index[module], module, index) - visited)
        )
    paths = sorted(
        str(index[module].relative_to(_REPO_ROOT)).replace("\\", "/")
        for module in visited
    )
    rows = _rows(paths)
    return rows, sha256_json(rows)


def historical_dependency_closure() -> tuple[list[dict[str, str]], str]:
    """Return the dependency closure frozen in the Step 1 receipt."""

    frozen = load_json(S1_RECEIPT_PATH)
    raw_rows = frozen.get("source_dependency_closure")
    frozen_hash = frozen.get("source_dependency_closure_sha256")
    if not isinstance(raw_rows, list) or not isinstance(frozen_hash, str):
        raise ValueError("step1_historical_dependency_closure_missing")
    rows = [dict(row) for row in raw_rows if isinstance(row, Mapping)]
    if (
        len(rows) != len(raw_rows)
        or frozen_hash != HISTORICAL_DEPENDENCY_CLOSURE_SHA256
        or sha256_json(rows) != frozen_hash
    ):
        raise ValueError("step1_historical_dependency_closure_invalid")
    return rows, frozen_hash


def dependency_closure() -> tuple[list[dict[str, str]], str]:
    """Compatibility name for the Step 1 historical dependency closure."""

    return historical_dependency_closure()


def _v2_role(path: str) -> str:
    if path in V2_SOURCE_PATHS:
        return "stopped_source"
    if "/docs/" in path:
        return "historical_result_doc"
    if "/fixtures/" in path:
        return "frozen_fixture_or_receipt"
    if "/local_only/" in path:
        return "historical_body_full_local_only"
    if "/helpers/" in path:
        return "historical_helper"
    if "/tests/test_" in path:
        return "historical_test"
    return "historical_artifact"


def discover_v2_immutable_manifest() -> tuple[list[dict[str, str]], str]:
    paths: set[str] = set(V2_SOURCE_PATHS)
    for path in _AI_ROOT.rglob("*"):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        rel = str(path.relative_to(_REPO_ROOT)).replace("\\", "/")
        name = path.name
        if "emlis_nls_v2" in name or "NLSv2" in name:
            paths.add(rel)
    rows = [
        {"path": path, "role": _v2_role(path), "sha256": sha256_file(_REPO_ROOT / path)}
        for path in sorted(paths)
    ]
    return rows, sha256_json(rows)


def _canonical_input(value: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "memo": str(value.get("memo") or ""),
        "memo_action": str(value.get("memo_action") or ""),
        "emotions": [str(item) for item in value.get("emotions") or ()],
        "category": [str(item) for item in value.get("category") or ()],
    }


def load_baseline_cases() -> tuple[BaselineCase, ...]:
    exact8 = load_json(EXACT8_PATH)
    unseen12 = load_json(UNSEEN12_PATH)
    rows: list[BaselineCase] = []
    exact_by_id = {row["case_id"]: row for row in exact8["cases"]}
    for case_id in exact8["case_order"]:
        row = exact_by_id[case_id]
        current_input = _canonical_input(row["exact_current_input"])
        if sha256_json(current_input) != row["current_input_sha256"]:
            raise ValueError(f"exact8_input_identity_mismatch:{case_id}")
        rows.append(
            BaselineCase(
                case_id=case_id,
                cohort="exact8",
                family="exact8_regression",
                current_input=current_input,
                source_ref="grounded_human_reception_exact8_v2_20260712.json",
            )
        )
    unseen_by_id = {row["case_id"]: row for row in unseen12["cases"]}
    for case_id in unseen12["case_order"]:
        row = unseen_by_id[case_id]
        rows.append(
            BaselineCase(
                case_id=case_id,
                cohort="rr8_unseen12",
                family=str(row["input_family"]),
                current_input=_canonical_input(row["current_input"]),
                source_ref="grounded_human_reception_rr8_unseen12_20260713.json",
            )
        )
    for case in GROUND_OBSERVATION_I6_BLIND_CASES:
        if case.case_id in _EXACT8_I6_CASE_IDS:
            continue
        rows.append(
            BaselineCase(
                case_id=case.case_id,
                cohort="i6_probe8",
                family=str(case.family),
                current_input=_canonical_input(case.as_current_input()),
                source_ref="emlis_ai_grounded_observation_i6_cases.py",
            )
        )
    identities = [(row.cohort, row.case_id) for row in rows]
    if len(identities) != len(set(identities)):
        raise ValueError("baseline_case_identity_duplicate")
    if Counter(row.cohort for row in rows) != {
        "exact8": 8,
        "rr8_unseen12": 12,
        "i6_probe8": 8,
    }:
        raise ValueError("baseline_cohort_shape_invalid")
    return tuple(rows)


def _nearest_rank(values: Sequence[float], percentile: float) -> float:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        return 0.0
    return ordered[max(0, math.ceil(percentile * len(ordered)) - 1)]


def _latency_summary(values: Sequence[float]) -> dict[str, float | int]:
    samples = tuple(round(float(value), 6) for value in values)
    return {
        "sample_count": len(samples),
        "min_ms": round(min(samples, default=0.0), 6),
        "median_ms": round(statistics.median(samples), 6) if samples else 0.0,
        "p95_ms": round(_nearest_rank(samples, 0.95), 6),
        "max_ms": round(max(samples, default=0.0), 6),
    }


def _quote_metrics(value: str) -> dict[str, int]:
    spans = [left or right for left, right in _QUOTE_RE.findall(value)]
    compact = _WHITESPACE_RE.sub("", value)
    quoted = sum(len(item) for item in spans)
    return {
        "span_count": len(spans),
        "quoted_character_count": quoted,
        "section_character_count": len(compact),
        "dependency_basis_points": round(10_000 * quoted / max(1, len(compact))),
    }


def _distribution(values: Iterable[Any]) -> dict[str, int]:
    return dict(sorted(Counter(str(value) for value in values).items()))


def _case_order(cases: Iterable[BaselineCase], cohort: str) -> list[str]:
    return [case.case_id for case in cases if case.cohort == cohort]


def assert_body_free(value: Any) -> None:
    if isinstance(value, Mapping):
        for raw_key, nested in value.items():
            key = str(raw_key)
            if key in _FORBIDDEN_BODY_KEYS:
                raise ValueError(f"body_free_forbidden_key:{key}")
            if key.endswith("_included") and nested is not False:
                raise ValueError(f"body_free_flag_true:{key}")
            assert_body_free(nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            assert_body_free(nested)


def build_step0() -> dict[str, Any]:
    owners, owner_hash = historical_source_owner_snapshot()
    v2_rows, v2_hash = discover_v2_immutable_manifest()
    return {
        "schema_version": S0_SCHEMA_VERSION,
        "created_date": "2026-07-14",
        "design_stage": "step0_revised_design_version_boundary_freeze",
        "design": {
            "received_ref": "Cocolon_EmlisAI_ModelFreeNaturalLanguageSurfaceV3_DetailedDesign_ImplementationOrder_20260714_Revised_Cycle(1).md",
            "sha256": DESIGN_SHA256,
            "status": "revised_cycle_adopted",
        },
        "received_artifacts": [
            {"role": "backend_source", "received_ref": "mashos-api(224).zip", "design_basis_ref": "mashos-api(223).zip", "sha256": BACKEND_ARCHIVE_SHA256, "byte_identical_to_design_basis": True},
            {"role": "rn_source", "received_ref": "Cocolon(299).zip", "design_basis_ref": "Cocolon(298).zip", "sha256": RN_ARCHIVE_SHA256, "byte_identical_to_design_basis": True},
            {"role": "premise", "received_ref": "Cocolon_前提資料(338).zip", "design_basis_ref": "Cocolon_前提資料(337).zip", "sha256": PREMISE_ARCHIVE_SHA256, "byte_identical_to_design_basis": True},
            {"role": "implemented_docs", "received_ref": "EmlisAIの実装済み資料(134).zip", "sha256": IMPLEMENTED_DOCS_ARCHIVE_SHA256},
            {"role": "question_roadmap", "received_ref": "Cocolon_EmlisAI_longterm_roadmap_20260608_P7P8_question_need_observation_20260619(16).md", "sha256": ROADMAP_SHA256},
        ],
        "version_identity": {
            "product_name": "Cocolon EmlisAI",
            "feature_name": "Natural Language Surface",
            "candidate_version": "nls_v3",
            "generation_path": "grounded_natural_language_surface_v3",
            "runtime_state": "offline",
            "allowed_runtime_states": list(RUNTIME_STATES),
            "current_observation_stage": "normal_observation",
            "allowed_observation_stages": list(OBSERVATION_STAGES),
            "runtime_connected": False,
            "runtime_owner": False,
        },
        "current_runtime": {
            "production_surface_owner": "grounded_sentence_surface_canonical_v1",
            "production_generation_path": "grounded_observation_plan_sentence_surface_canonical_v1",
            "reply_meta_emlis_ai_version_is_not_nls_version": True,
            "source_owner_files": owners,
            "source_owner_snapshot_sha256": owner_hash,
        },
        "v2_boundary": {
            "state": "offline_only_stopped",
            "reopen_allowed": False,
            "repair_allowed": False,
            "import_from_v3_allowed": False,
            "immutable_files": v2_rows,
            "immutable_manifest_sha256": v2_hash,
            "holdout_a_status": "stop",
            "holdout_b_status": "not_evaluated",
        },
        "unchanged_contracts": {
            "route": "POST /emotion/submit",
            "public_body_path": "input_feedback.comment_text",
            "public_status_path": "input_feedback.emlis_ai.observation_status",
            "rn_visibility_predicate": "observation_status_passed_and_comment_text_nonempty",
            "section_order": "observation_blankline_reception",
            "section_labels": ["見えたこと：", "Emlisから："],
            "greeting_and_address_owner": "unchanged_existing_owner",
            "db_physical_names_changed": False,
            "db_write_paths_changed": False,
            "rn_production_changed": False,
            "public_response_keys_changed": False,
            "account_subscription_access_deletion_changed": False,
            "safety_emergency_owner_changed": False,
            "raw_or_candidate_body_added_to_public_meta": False,
        },
        "evaluation_policy": {
            "new_cases_per_cycle": 100,
            "minimum_cycle_count": 10,
            "minimum_karen_generated_valid_cases": 1000,
            "minimum_is_not_completion_guarantee": True,
            "cumulative_full_rerun_after_text_change": True,
            "secret_input_required": False,
            "open_once_cohort_required": False,
            "external_reviewer_required": False,
            "actual_device_after_local_stability": True,
            "recent_first_run_major_defect_free_batch_count": 2,
        },
        "completion_condition": "design_receipt_and_immutable_boundaries_verified",
        "step0_status": "completed",
        "next_step_authority": "step1_only",
        "valid_for_step1": True,
        "valid_for_step2": False,
        "valid_for_runtime_switch": False,
        "body_free": True,
        "raw_input_included": False,
        "comment_text_included": False,
        "candidate_body_included": False,
    }


def build_source_resource_bound_policy() -> dict[str, Any]:
    """Freeze lossless source-relative bounds without inventing an input cap.

    Current RN and API owners do not impose a memo/memo_action character
    maximum.  Consequently Nucleus and Relation have no honest finite global
    maximum.  The v3 policy instead binds them to the current request's source
    inventory.  Fixed bounds are used only where the received source has a
    finite construction vocabulary/count.
    """

    owner_rows = _rows(RESOURCE_BOUND_OWNER_PATHS)
    return {
        "schema_version": "cocolon.emlis.nls_v3.source_resource_bound_policy.v1",
        "authority": "received_canonical_v1_source_and_current_rn_api_contract",
        "owner_files": owner_rows,
        "owner_snapshot_sha256": sha256_json(owner_rows),
        "rn_text_limit_owner": {
            "path": "screens/input/InputMemoSection.js",
            "sha256": dict(RN_OWNER_ROWS)["screens/input/InputMemoSection.js"],
        },
        "symbols": {
            "E": "current_request_evidence_span_count",
            "T": "current_request_text_source_evidence_span_count",
            "N": "validated_current_request_nucleus_count",
            "R": "validated_current_request_relation_count",
            "U": "validated_current_request_unknown_boundary_count",
            "S": "validated_current_request_safety_policy_count",
            "K": "validated_current_request_safety_required_boundary_code_count",
            "O": "validated_current_request_reception_opportunity_count",
        },
        "global_finite_text_character_limit_present": False,
        "global_finite_nucleus_limit_derivable": False,
        "global_finite_relation_limit_derivable": False,
        "fixed_finite_global_limit_must_not_be_invented": True,
        "app_reachable_structured_label_max": {
            "non_self_insight_emotion_count": 5,
            "self_insight_emotion_count": 1,
            "category_count": 9,
            "maximum_emotion_plus_category_count": 14,
        },
        "backend_ui_unreachable_list_length_limit_present": False,
        "source_component_bounds": {
            "nucleus_count": {
                "bound_kind": "request_relative_lossless",
                "upper_bound_formula": "E",
                "derivation": "one_nucleus_per_evidence_span",
            },
            "relation_count": {
                "bound_kind": "request_relative_conservative_lossless",
                "upper_bound_formula": "min(N * (N - 1), T + 9)",
                "derivation": "distinct_directed_nucleus_pairs_intersect_source_order_at_most_T_minus_1_plus_memo_action_1_plus_observer_edges_9",
            },
            "unknown_boundary_count": {
                "bound_kind": "fixed_source_conservative",
                "upper_bound": 11,
                "app_reachable_upper_bound": 7,
                "derivation": "nine_observer_uncertainty_slots_plus_three_graph_missing_information_slots_minus_the_shared_relation_not_confident_code",
            },
            "safety_policy_count": {
                "bound_kind": "fixed_source_exact",
                "upper_bound": 1,
                "derivation": "one_GroundedSafetyPolicy_per_observation_plan",
            },
            "safety_required_boundary_code_count": {
                "bound_kind": "fixed_source_vocabulary",
                "upper_bound": 9,
                "derivation": "deduped_current_safety_reason_and_boundary_code_vocabulary",
            },
            "reception_opportunity_count": {
                "bound_kind": "fixed_source_exact",
                "upper_bound": 4,
                "derivation": "canonical_family_mapping_and_pruning_allow_at_most_four_simultaneous_opportunity_rows",
            },
        },
        "canonical_obligation_identity_policy": {
            "base_nonstance": {
                "nucleus_identity": ["kind", "nucleus_id"],
                "relation_identity": [
                    "grounded_relation_preservation",
                    "relation_id",
                ],
                "unknown_identity": [
                    "unknown_boundary_preservation",
                    "unknown_id",
                ],
                "maximum_per_exact_identity": 1,
                "maximum_formula": "B = 4*N + R + U",
                "nucleus_owned_kinds": [
                    "grounded_nucleus_notice",
                    "significance_or_shift",
                    "intention_or_next_action",
                    "self_denial_boundary",
                ],
                "relation_owned_kinds": ["grounded_relation_preservation"],
                "unknown_boundary_owned_kinds": [
                    "unknown_boundary_preservation"
                ],
            },
            "bounded_counterposition": {
                "identity": [
                    "safety_authority_token",
                    "target_base_obligation_id",
                ],
                "maximum_per_identity": 1,
                "safety_authority_token": (
                    "safety_policy_default_or_one_required_boundary_code"
                ),
                "safety_authority_token_count_formula": "S + K",
                "maximum_formula": "C = (S + K) * B",
                "per_target_capacity_required": True,
            },
            "bound_emlis_reception": {
                "identity": [
                    "reception_authority_token",
                    "target_nonstance_obligation_id",
                ],
                "maximum_per_identity": 1,
                "reception_authority_token": (
                    "default_reception_authority_or_one_opportunity_id"
                ),
                "reception_authority_token_count_formula": "O + 1",
                "default_authority_present_when_O_is_zero": True,
                "conservative_target_capacity_formula": "P = B + C",
                "maximum_formula": "Q = (O + 1) * P",
                "runtime_target_must_be_base_nonstance": True,
                "counterposition_capacity_is_not_runtime_reception_target": True,
                "capacity_superset_is_intentionally_conservative": True,
            },
            "canonical_merge": {
                "same_identity_duplicate_allowed": False,
                "same_primary_source_same_kind_scalar_projection_must_be_identical": True,
                "counting_identity_does_not_narrow_source_authority_codes": True,
                "secondary_source_authorities_must_be_lossless_union": True,
                "array_fields_lossless_union": [
                    "evidence_ids",
                    "nucleus_ids",
                    "relation_ids",
                    "unknown_boundary_ids",
                    "target_obligation_ids",
                    "topic_scope_ids",
                    "must_not_merge_with",
                    "allowed_response_acts",
                    "forbidden_claim_codes",
                    "source_authority_codes",
                ],
                "scalar_conflict_failure_code": "OBLIGATION_CANONICAL_PROJECTION_CONFLICT",
                "semantic_duplicate_failure_code": "OBLIGATION_CANONICAL_DUPLICATE",
                "canonical_failure_must_not_truncate": True,
                "semantic_information_drop_allowed": False,
            },
            "normal_surface_eligibility": {
                "minimum_base_nonstance_obligation_count": 1,
                "zero_base_failure_code": "OBLIGATION_SOURCE_UNAVAILABLE",
                "zero_base_visible_text_allowed": False,
                "separate_safety_owner_excluded": True,
            },
        },
        "per_request_obligation_inventory_upper_bound_formula": "(4*N + R + U) * (S + K + 1) * (O + 2)",
        "per_request_obligation_inventory_upper_bound_derivation": {
            "B": "4*N + R + U",
            "C": "(S + K) * B",
            "P": "B + C",
            "Q": "(O + 1) * P",
            "I": "P + Q",
        },
        "obligation_kind_added_requires_policy_version_change": True,
        "candidate_count_limit": 12,
        "candidate_count_is_obligation_inventory_limit": False,
        "truncate_source_or_obligation_inventory_at_bound": False,
        "overflow_failure_code": "OBLIGATION_INVENTORY_OVERFLOW",
        "required_boundary_tests": ["bound_minus_one", "bound", "bound_plus_one"],
        "step4_must_derive_obligation_inventory_bound_from_these_components": True,
    }


_SOURCE_RESOURCE_COUNT_KEYS = frozenset(
    {
        "evidence_span_count",
        "text_evidence_span_count",
        "nucleus_count",
        "relation_count",
        "unknown_boundary_count",
        "safety_policy_count",
        "safety_required_boundary_code_count",
        "reception_opportunity_count",
    }
)


def validate_source_resource_counts(value: Mapping[str, Any]) -> tuple[str, ...]:
    """Validate one body-free current-source count row against the freeze."""

    if set(value) != _SOURCE_RESOURCE_COUNT_KEYS:
        return ("source_resource_count_shape_invalid",)
    if any(type(value[key]) is not int or int(value[key]) < 0 for key in value):
        return ("source_resource_count_type_invalid",)
    evidence_count = int(value["evidence_span_count"])
    text_count = int(value["text_evidence_span_count"])
    if text_count > evidence_count:
        return ("source_resource_text_count_invalid",)
    upper_bounds = {
        "nucleus_count": evidence_count,
        "relation_count": min(
            int(value["nucleus_count"]) * max(0, int(value["nucleus_count"]) - 1),
            text_count + 9,
        ),
        "unknown_boundary_count": 11,
        "safety_policy_count": 1,
        "safety_required_boundary_code_count": 9,
        "reception_opportunity_count": 4,
    }
    if any(int(value[key]) > limit for key, limit in upper_bounds.items()):
        return ("OBLIGATION_INVENTORY_OVERFLOW",)
    return ()


def obligation_inventory_upper_bound(source_counts: Mapping[str, Any]) -> int:
    issues = validate_source_resource_counts(source_counts)
    if issues:
        raise ValueError("invalid_source_resource_counts:" + ",".join(issues))
    return (
        (
            4 * int(source_counts["nucleus_count"])
            + int(source_counts["relation_count"])
            + int(source_counts["unknown_boundary_count"])
        )
        * (
            int(source_counts["safety_policy_count"])
            + int(source_counts["safety_required_boundary_code_count"])
            + 1
        )
        * (int(source_counts["reception_opportunity_count"]) + 2)
    )


def validate_obligation_inventory_count(
    source_counts: Mapping[str, Any],
    obligation_count: Any,
) -> tuple[str, ...]:
    if type(obligation_count) is not int or int(obligation_count) < 0:
        return ("obligation_inventory_count_type_invalid",)
    try:
        upper_bound = obligation_inventory_upper_bound(source_counts)
    except ValueError:
        return ("source_resource_counts_invalid",)
    if int(obligation_count) > upper_bound:
        return ("OBLIGATION_INVENTORY_OVERFLOW",)
    return ()


def build_input_contract() -> dict[str, Any]:
    rn_rows = [{"path": path, "sha256": digest} for path, digest in RN_OWNER_ROWS]
    backend_rows, backend_hash = public_backend_snapshot()
    return {
        "schema_version": S1_INPUT_SCHEMA_VERSION,
        "created_date": "2026-07-14",
        "contract_version": "cocolon.input_contract.20260714",
        "authority": "current_rn_production_files",
        "rn_archive_sha256": RN_ARCHIVE_SHA256,
        "rn_owner_files": rn_rows,
        "rn_owner_snapshot_sha256": sha256_json(rn_rows),
        "field_mapping": {
            "thought_text": "memo",
            "action_text": "memo_action",
            "emotions": "emotion_details_or_emotions",
            "categories": "category",
        },
        "app_reachable": {
            "text_requirement": "trimmed_memo_or_memo_action_nonempty",
            "emotion_min_count": 1,
            "emotion_unique": True,
            "emotion_types": list(EMOTION_TYPES),
            "strength_types": list(STRENGTHS),
            "self_insight_type": "自己理解",
            "self_insight_exclusive": True,
            "self_insight_strength": "medium",
            "non_self_insight_multiple_allowed": True,
            "category_min_count": 1,
            "category_unique": True,
            "category_types": list(CATEGORY_TYPES),
            "category_multiple_allowed": True,
            "text_length_limit_added_by_nls_v3": False,
            "submit_condition": "not_submitting_and_text_and_emotion_and_category",
        },
        "backend_compatibility_boundary": {
            "owner_files": backend_rows,
            "owner_snapshot_sha256": backend_hash,
            "legacy_string_emotion_accepted": True,
            "unknown_emotion_type_rejected": False,
            "unknown_strength_coerced_to_medium": True,
            "self_insight_mixed_rejected": False,
            "self_insight_nonmedium_rejected": False,
            "duplicate_emotion_rejected": False,
            "duplicate_category_rejected": False,
            "duplicate_category_deduplicated": True,
            "blank_thought_and_action_rejected": False,
            "memo_without_category_rejected": False,
            "empty_emotions_rejected": True,
            "unknown_category_rejected": True,
            "backend_permissiveness_is_app_valid_authority": False,
        },
        "baseline_fixture_boundary": {
            "known_fixture_string_emotions_are_legacy_comparison_inputs": True,
            "known_fixture_strength_omission_is_not_app_contract_authority": True,
            "known_fixture_cases_count_toward_karen_1000": False,
        },
        "source_resource_bound_policy": build_source_resource_bound_policy(),
        "supabase_future_intake": {
            "current_status": "not_received_not_blocking",
            "required_intake_checks": [
                "header",
                "row_count",
                "missing_fields",
                "exact_duplicates",
                "near_duplicates",
                "legacy_ratio",
                "current_valid_ratio",
                "personal_information",
                "usage_scope",
            ],
            "excluded_fields": [
                "user_id",
                "auth",
                "email",
                "notification_data",
                "historical_emlis_output",
            ],
            "raw_corpus_repo_allowed": False,
            "raw_corpus_public_receipt_allowed": False,
            "private_local_workspace_required": True,
            "current_valid_and_legacy_separated": True,
            "replaces_karen_generated_1000": False,
        },
        "step1_input_contract_status": "completed",
        "body_free": True,
        "raw_input_included": False,
        "comment_text_included": False,
        "candidate_body_included": False,
    }


def _source_resource_counts(current_input: Mapping[str, Any]) -> dict[str, int]:
    plan = build_grounded_observation_plan(dict(current_input))
    evidence_ids = {
        span_id
        for nucleus in plan.nuclei
        for span_id in nucleus.source_span_ids
    }
    text_evidence_ids = {
        span_id
        for nucleus in plan.nuclei
        if set(nucleus.source_fields) & {"memo", "memo_action"}
        for span_id in nucleus.source_span_ids
    }
    reception_plan = plan.response_plan.human_reception_plan
    row = {
        "evidence_span_count": len(evidence_ids),
        "text_evidence_span_count": len(text_evidence_ids),
        "nucleus_count": len(plan.nuclei),
        "relation_count": len(plan.relations),
        "unknown_boundary_count": len(plan.unknown_boundaries),
        "safety_policy_count": 1,
        "safety_required_boundary_code_count": len(
            plan.safety_policy.required_boundary_codes
        ),
        "reception_opportunity_count": len(
            reception_plan.opportunities if reception_plan is not None else ()
        ),
    }
    issues = validate_source_resource_counts(row)
    if issues:
        raise ValueError("source_resource_bound_failed:" + ",".join(issues))
    return row


def _known_device4_regression_row() -> dict[str, Any]:
    if sha256_file(KNOWN_DEVICE4_RECEIPT_PATH) != KNOWN_DEVICE4_RECEIPT_SHA256:
        raise ValueError("known_device4_receipt_drift")
    if sha256_file(KNOWN_DEVICE4_TEST_PATH) != KNOWN_DEVICE4_TEST_SHA256:
        raise ValueError("known_device4_raw_input_owner_drift")
    if sha256_file(KNOWN_DEVICE4_RESULT_PATH) != KNOWN_DEVICE4_RESULT_SHA256:
        raise ValueError("known_device4_result_doc_drift")
    source = load_json(KNOWN_DEVICE4_RECEIPT_PATH)
    review = source.get("representative4_review") or {}
    evidence = source.get("device_evidence") or {}
    if {
        "evidence_intake_status": review.get("evidence_intake_status"),
        "device_baseline_owner": review.get("device_baseline_owner"),
        "product_read_status": review.get("product_read_status"),
        "case_count": review.get("case_count"),
        "product_pass_count": review.get("product_pass_count"),
        "product_failure_count": review.get("product_failure_count"),
    } != {
        "evidence_intake_status": "complete",
        "device_baseline_owner": "grounded_sentence_surface_canonical_v1",
        "product_read_status": "fail",
        "case_count": 4,
        "product_pass_count": 0,
        "product_failure_count": 4,
    }:
        raise ValueError("known_device4_summary_mismatch")
    if {
        "screenshot_review_is_raw_body_hash_proof": evidence.get(
            "screenshot_review_is_raw_body_hash_proof"
        ),
        "actual_device_raw_comment_sha256_machine_match": evidence.get(
            "actual_device_raw_comment_sha256_machine_match"
        ),
        "evidence_role": evidence.get("evidence_role"),
        "v2_runtime_generation_count": evidence.get("v2_runtime_generation_count"),
    } != {
        "screenshot_review_is_raw_body_hash_proof": False,
        "actual_device_raw_comment_sha256_machine_match": (
            "not_available_from_screenshots"
        ),
        "evidence_role": "canonical_v1_actual_device_baseline_not_v2_acceptance",
        "v2_runtime_generation_count": 0,
    } or review.get("formal_v2_evaluation_status") != "not_executed":
        raise ValueError("known_device4_evidence_limit_mismatch")
    expected_cases = (
        (
            1,
            "low_information_short",
            "5ff92167f1474258f68d2e120f1273480ae249f2fb6e687dc381e3c9804d055b",
            (
                "EMLIS_CONTENT_GENERIC",
                "EMLIS_SEMANTIC_DENSITY_LOW",
                "TWO_STAGE_RATIO_OUTSIDE_GUIDE_LOW_INFORMATION_SHORT",
            ),
        ),
        (
            2,
            "daily_positive",
            "ceb9d9a92a8865584f4cf17e4d8af08bac26126a4efb64bd95fd62d6464d4cb4",
            (
                "OBSERVATION_QUOTE_REPLAY_EXCESS",
                "SECTION_ROLE_DISTINCTNESS_LOW",
                "EMLIS_SEMANTIC_DENSITY_LOW",
                "TWO_STAGE_RATIO_OUTSIDE_GUIDE_DAILY_POSITIVE",
            ),
        ),
        (
            3,
            "rich_change_long_arc",
            "1ca9ee3fde883d13e044f629352688781869b279f6514dda52eaf59538217e74",
            (
                "LONG_INPUT_ENUMERATION_REPLAY",
                "OBSERVATION_TEMPLATE_CLAUSE_DUPLICATION",
                "SEMANTIC_RELATION_DISTORTION",
                "EMLIS_REFERENCE_AMBIGUOUS",
                "EMLIS_ANCHOR_CONTEXT_LOSS",
                "EMLIS_SEMANTIC_DENSITY_LOW",
                "TWO_STAGE_RATIO_OUTSIDE_GUIDE_RICH_LONG",
                "SCROLL_REQUIRED",
            ),
        ),
        (
            4,
            "self_denial_with_concrete_action",
            "d6d0c20b4b1770322005375c19233ea4ede9f87c654c7155b5c4641079a7227e",
            (
                "OBSERVATION_QUOTE_REPLAY_EXCESS",
                "EMLIS_GENERIC_RECEPTION_OPENING",
                "SECTION_ROLE_DISTINCTNESS_LOW",
                "EMLIS_SEMANTIC_DENSITY_LOW",
                "TWO_STAGE_RATIO_OUTSIDE_GUIDE_SELF_DENIAL",
                "SCROLL_REQUIRED",
            ),
        ),
    )
    actual_cases = tuple(
        (
            row.get("case_number"),
            row.get("family"),
            row.get("input_identity_sha256"),
            tuple(row.get("failure_codes") or ()),
        )
        for row in review.get("cases") or ()
    )
    if actual_cases != expected_cases or any(
        row.get("product_status") != "fail"
        or row.get("actual_device_visual_match_to_local_v1") != "pass"
        for row in review.get("cases") or ()
    ):
        raise ValueError("known_device4_case_mismatch")
    return {
        "regression_id": "V1_KNOWN_DEVICE_REPRESENTATIVE4_20260713",
        "classification": "known_legacy_ui_unreachable_device_product_failure",
        "status": "confirmed_product_failure",
        "source_ref": KNOWN_DEVICE4_RECEIPT_PATH.name,
        "source_sha256": KNOWN_DEVICE4_RECEIPT_SHA256,
        "raw_input_owner": {
            "ref": "../" + KNOWN_DEVICE4_TEST_PATH.name,
            "sha256": KNOWN_DEVICE4_TEST_SHA256,
            "imported_by_v3": False,
        },
        "result_doc": {
            "ref": (
                "../../docs/"
                "Cocolon_EmlisAI_NLSv2_S12_S13_DeviceCheck_Blocked_Result_20260713.md"
            ),
            "sha256": KNOWN_DEVICE4_RESULT_SHA256,
        },
        "device_baseline_owner": "grounded_sentence_surface_canonical_v1",
        "case_count": 4,
        "local_v1_visual_match_count": 4,
        "product_pass_count": 0,
        "product_failure_count": 4,
        "app_reachable_under_current_contract": False,
        "counts_toward_v3_minimum": False,
        "formal_v2_evaluation_status": "not_executed",
        "input_identity_binding": {
            "exact_case_order_and_identity_verified_by_helper": True,
            "raw_input_owner_file_sha256_bound": True,
            "raw_unsalted_short_input_sha256_republished": False,
        },
        "evidence_limitations": {
            "screenshot_review_is_raw_body_hash_proof": False,
            "actual_device_raw_comment_sha256_machine_match": (
                "not_available_from_screenshots"
            ),
            "evidence_role": "canonical_v1_actual_device_baseline_not_v2_acceptance",
            "v2_runtime_generation_count": 0,
        },
        "cases": [
            {
                "case_number": case_number,
                "family": family,
                "failure_codes": list(failure_codes),
            }
            for case_number, family, _identity, failure_codes in expected_cases
        ],
    }


def _rr10_not_run_regression_row() -> dict[str, Any]:
    frozen_files = (
        (RR10_READINESS_PATH, RR10_READINESS_SHA256),
        (RR10_EXPECTED_PACKET_PATH, RR10_EXPECTED_PACKET_SHA256),
        (RR10_EVIDENCE_TEMPLATE_PATH, RR10_EVIDENCE_TEMPLATE_SHA256),
        (RR10_EVIDENCE_VERIFIER_PATH, RR10_EVIDENCE_VERIFIER_SHA256),
    )
    if any(sha256_file(path) != expected for path, expected in frozen_files):
        raise ValueError("rr10_device_packet_or_verifier_drift")
    readiness = load_json(RR10_READINESS_PATH)
    packet = load_json(RR10_EXPECTED_PACKET_PATH)
    evidence_template = load_json(RR10_EVIDENCE_TEMPLATE_PATH)
    case_order = ["A", "B", "I6-L03", "I6-D02"]
    if (
        readiness.get("representative_case_order") != case_order
        or packet.get("representative_case_order") != case_order
        or evidence_template.get("representative_case_order") != case_order
        or [row.get("case_id") for row in readiness.get("cases") or ()]
        != case_order
        or [row.get("case_id") for row in packet.get("cases") or ()] != case_order
        or [row.get("case_id") for row in evidence_template.get("cases") or ()]
        != case_order
    ):
        raise ValueError("rr10_device_case_order_drift")
    summary = evidence_template.get("execution_summary") or {}
    if {
        "readiness_status": readiness.get("readiness_status"),
        "readiness_actual_device_status": readiness.get("actual_device_status"),
        "packet_actual_device_status": packet.get("actual_device_execution_status"),
        "template_actual_device_status": summary.get(
            "actual_device_execution_status"
        ),
        "template_case_statuses": [
            row.get("status") for row in evidence_template.get("cases") or ()
        ],
        "actual_device_result_included": readiness.get(
            "actual_device_result_included"
        ),
        "progression_authority": readiness.get("progression_authority"),
        "valid_for_progression": readiness.get("valid_for_progression"),
    } != {
        "readiness_status": "ready_for_mash_actual_device_execution",
        "readiness_actual_device_status": "not_run",
        "packet_actual_device_status": "not_run",
        "template_actual_device_status": "not_run",
        "template_case_statuses": ["not_run"] * 4,
        "actual_device_result_included": False,
        "progression_authority": "none",
        "valid_for_progression": False,
    }:
        raise ValueError("rr10_device_not_run_boundary_drift")
    if (
        readiness.get("expected_packet_sha256") != RR10_EXPECTED_PACKET_SHA256
        or readiness.get("evidence_template_sha256")
        != RR10_EVIDENCE_TEMPLATE_SHA256
        or readiness.get("evidence_verifier_sha256")
        != RR10_EVIDENCE_VERIFIER_SHA256
        or evidence_template.get("expected_packet_sha256")
        != RR10_EXPECTED_PACKET_SHA256
    ):
        raise ValueError("rr10_device_lineage_drift")
    return {
        "regression_id": "R8_RR10_V1_DEVICE_BASELINE",
        "classification": "actual_device_operator_required_later",
        "status": "not_run",
        "distinct_from_historical_device4": True,
        "representative_case_order": case_order,
        "readiness": {
            "ref": RR10_READINESS_PATH.name,
            "sha256": RR10_READINESS_SHA256,
        },
        "expected_packet": {
            "ref": "../local_only/" + RR10_EXPECTED_PACKET_PATH.name,
            "sha256": RR10_EXPECTED_PACKET_SHA256,
        },
        "evidence_template": {
            "ref": "../local_only/" + RR10_EVIDENCE_TEMPLATE_PATH.name,
            "sha256": RR10_EVIDENCE_TEMPLATE_SHA256,
        },
        "evidence_verifier": {
            "ref": "../../tools/" + RR10_EVIDENCE_VERIFIER_PATH.name,
            "sha256": RR10_EVIDENCE_VERIFIER_SHA256,
        },
        "actual_device_result_included": False,
        "progression_authority": "none",
        "valid_for_progression": False,
    }


def _known_regression_inventory() -> list[dict[str, Any]]:
    return [
        {
            "regression_id": "V1_KNOWN_COMPARISON_28",
            "classification": "executable_known_regression",
            "case_count": 28,
            "counts_toward_v3_minimum": False,
        },
        {
            "regression_id": "V2_DEVELOPMENT_42",
            "classification": "known_regression_not_novel_evidence",
            "case_count": 42,
            "counts_toward_v3_minimum": False,
        },
        {
            "regression_id": "V2_STEP3_STRICT_CONTRACT_GAP",
            "classification": "body_free_historical_failure",
            "status": "confirmed_underimplementation",
        },
        {
            "regression_id": "V2_STEP4_DISCOURSE_VARIATION_GAP",
            "classification": "body_free_historical_failure",
            "status": "confirmed_partial",
        },
        {
            "regression_id": "V2_STEP5_GENERIC_SURFACE_CONVERGENCE",
            "classification": "body_free_historical_failure",
            "status": "confirmed_product_failure",
        },
        {
            "regression_id": "V2_STEP6_METADATA_SELF_REPORT_ATTACK",
            "classification": "body_free_historical_failure",
            "status": "confirmed_gate_failure",
        },
        {
            "regression_id": "V2_STEP7_CASE_EVIDENCE_GAP",
            "classification": "body_free_historical_failure",
            "status": "completion_withdrawn",
        },
        {
            "regression_id": "V2_HOLDOUT_A",
            "classification": "sealed_historical_only_do_not_reopen",
            "status": "stop",
        },
        {
            "regression_id": "V2_HOLDOUT_B",
            "classification": "sealed_historical_only_do_not_open",
            "status": "not_evaluated",
        },
        _known_device4_regression_row(),
        _rr10_not_run_regression_row(),
    ]


async def _capture_case(
    case: BaselineCase,
    *,
    key_hex: str,
    warmup_runs: int,
    latency_samples: int,
) -> tuple[dict[str, Any], dict[str, Any], tuple[float, ...]]:
    async def render(suffix: str):
        return await render_emlis_ai_reply(
            user_id=f"nls-v3-s1-{case.case_id}-{suffix}",
            subscription_tier="free",
            current_input=dict(case.current_input),
        )

    reply = await render("capture")
    visible = str(reply.comment_text or "").strip()
    observation, reception, issues = split_two_stage_surface(visible)
    if issues:
        raise ValueError(f"v1_two_stage_split_failed:{case.case_id}:{issues}")
    observation = observation.strip()
    reception = reception.strip()
    public = build_public_emlis_input_feedback_meta(
        reply.meta,
        comment_text_present=bool(visible),
        subscription_tier="free",
    )
    if not should_include_public_input_feedback(visible, public):
        raise ValueError(f"v1_public_contract_failed:{case.case_id}")
    gate = dict(reply.meta.get("grounded_observation") or {})
    gate_keys = (
        "plan_validity_gate",
        "evidence_resolution_gate",
        "required_coverage_gate",
        "text_semantic_retention_gate",
        "anti_template_gate",
        "mechanical_restatement_gate",
        "two_stage_contract_gate",
        "reception_all_gates_passed",
        "semantic_quality_gate",
        "runtime_final_contract_guard",
    )
    gate_status = {key: gate.get(key) for key in gate_keys}
    if gate_status["reception_all_gates_passed"] is not True:
        raise ValueError(f"v1_reception_gate_failed:{case.case_id}")
    if any(
        value != "passed"
        for key, value in gate_status.items()
        if key != "reception_all_gates_passed"
    ):
        raise ValueError(f"v1_gate_failed:{case.case_id}")
    if public.get("observation_status") != "passed":
        raise ValueError(f"v1_public_status_failed:{case.case_id}")
    source_resource_counts = _source_resource_counts(case.current_input)

    expected_commitment = hmac_commit_text(key_hex, f"visible:{case.cohort}:{case.case_id}", visible)
    for index in range(max(0, warmup_runs)):
        warm = await render(f"warm-{index}")
        if hmac_commit_text(
            key_hex,
            f"visible:{case.cohort}:{case.case_id}",
            str(warm.comment_text or "").strip(),
        ) != expected_commitment:
            raise ValueError(f"v1_nondeterministic_warmup:{case.case_id}")
    samples: list[float] = []
    for index in range(max(1, latency_samples)):
        started = time.perf_counter_ns()
        measured = await render(f"measure-{index}")
        samples.append((time.perf_counter_ns() - started) / 1_000_000)
        if hmac_commit_text(
            key_hex,
            f"visible:{case.cohort}:{case.case_id}",
            str(measured.comment_text or "").strip(),
        ) != expected_commitment:
            raise ValueError(f"v1_nondeterministic_measure:{case.case_id}")

    observation_sentences = split_reception_sentences(observation)
    reception_sentences = split_reception_sentences(reception)
    visible_row = {
        "case_id": case.case_id,
        "cohort": case.cohort,
        "family": case.family,
        "source_ref": case.source_ref,
        "current_input": dict(case.current_input),
        "visible_surface": visible,
        "observation_section": observation,
        "reception_section": reception,
        "public_observation_status": public["observation_status"],
        "generation_method": str(reply.meta.get("generation_method") or ""),
        "composer_source": str(reply.meta.get("composer_source") or ""),
        "generation_path": str(reply.meta.get("generation_path") or ""),
        "reception_depth_level": str(gate.get("reception_depth_level") or ""),
        "reception_terminal_predicate_families": list(
            gate.get("reception_terminal_predicate_families") or ()
        ),
        "commitments": {
            "input": hmac_commit_json(key_hex, f"input:{case.cohort}:{case.case_id}", dict(case.current_input)),
            "visible": expected_commitment,
            "observation": hmac_commit_text(key_hex, f"observation:{case.cohort}:{case.case_id}", observation),
            "reception": hmac_commit_text(key_hex, f"reception:{case.cohort}:{case.case_id}", reception),
        },
    }
    metric_row = {
        "case_id": case.case_id,
        "cohort": case.cohort,
        "input_identity_commitment": visible_row["commitments"]["input"],
        "v1_body_commitment": visible_row["commitments"]["visible"],
        "observation_commitment": visible_row["commitments"]["observation"],
        "reception_commitment": visible_row["commitments"]["reception"],
        "observation_sentence_count": len(observation_sentences),
        "reception_sentence_count": len(reception_sentences),
        "visible_sentence_count": len(observation_sentences) + len(reception_sentences),
        "observation_quote_dependency": _quote_metrics(observation),
        "reception_quote_dependency": _quote_metrics(reception),
        "reception_depth_level": str(gate.get("reception_depth_level") or ""),
        "reception_terminal_predicate_families": list(gate.get("reception_terminal_predicate_families") or ()),
        "source_resource_counts": source_resource_counts,
        "gate_status": gate_status,
        "runtime_latency": {
            **_latency_summary(samples),
            "samples_ms": [round(float(value), 6) for value in samples],
        },
        "public_observation_status": public["observation_status"],
        "public_comment_present": bool(visible),
    }
    return visible_row, metric_row, tuple(samples)


async def capture_step1(
    *,
    warmup_runs: int = 1,
    latency_samples: int = 5,
) -> tuple[dict[str, Any], dict[str, Any]]:
    step0 = load_json(S0_PATH)
    input_contract = load_json(S1_INPUT_PATH)
    owners, owner_hash = historical_source_owner_snapshot()
    closure, closure_hash = historical_dependency_closure()
    if step0["current_runtime"]["source_owner_snapshot_sha256"] != owner_hash:
        raise ValueError("step0_source_owner_snapshot_drift")
    key_hex = secrets.token_hex(32)
    cases = load_baseline_cases()
    visible_rows: list[dict[str, Any]] = []
    metric_rows: list[dict[str, Any]] = []
    all_latency: list[float] = []
    for case in cases:
        visible, metric, samples = await _capture_case(
            case,
            key_hex=key_hex,
            warmup_runs=warmup_runs,
            latency_samples=latency_samples,
        )
        visible_rows.append(visible)
        metric_rows.append(metric)
        all_latency.extend(samples)

    visible_artifact = {
        "schema_version": S1_VISIBLE_SCHEMA_VERSION,
        "created_date": "2026-07-14",
        "local_only": True,
        "known_synthetic_or_app_validated_inputs_only": True,
        "contains_real_user_supabase_corpus": False,
        "commitment_algorithm": "hmac-sha256-domain-separated",
        "commitment_key_hex": key_hex,
        "source_dependency_closure_sha256": closure_hash,
        "cohorts": [
            {"cohort": cohort, "case_order": _case_order(cases, cohort)}
            for cohort in ("exact8", "rr8_unseen12", "i6_probe8")
        ],
        "cases": visible_rows,
        "artifact_role": "canonical_v1_comparison_and_rollback_baseline_not_v3_expected_text",
        "counts_toward_karen_generated_v3_minimum": False,
        "v3_runtime_executed": False,
        "progression_authority": "none",
    }

    predicate_counts: Counter[str] = Counter()
    for row in metric_rows:
        predicate_counts.update(row["reception_terminal_predicate_families"])
    source_resource_maxima = {
        key: max(int(row["source_resource_counts"][key]) for row in metric_rows)
        for key in sorted(_SOURCE_RESOURCE_COUNT_KEYS)
    }
    receipt = {
        "schema_version": S1_RECEIPT_SCHEMA_VERSION,
        "created_date": "2026-07-14",
        "design_stage": "step1_baseline_actual_input_contract_freeze",
        "parent_step0_ref": S0_PATH.name,
        "parent_step0_sha256": sha256_file(S0_PATH),
        "input_contract_ref": S1_INPUT_PATH.name,
        "input_contract_sha256": sha256_file(S1_INPUT_PATH),
        "backend_archive_sha256": BACKEND_ARCHIVE_SHA256,
        "source_owner_files": owners,
        "source_owner_snapshot_sha256": owner_hash,
        "source_dependency_entry": DEPENDENCY_ENTRY_PATH,
        "source_dependency_closure": closure,
        "source_dependency_closure_sha256": closure_hash,
        "visible_artifact_ref": "../local_only/emlis_nls_v3_s1_v1_visible_20260714.json",
        "visible_artifact_sha256": "pending_write",
        "commitment_policy": {
            "algorithm": "hmac-sha256",
            "domain_separated": True,
            "key_location": "body_full_local_only_artifact",
            "key_in_body_free_receipt": False,
            "raw_sha256_used_for_short_body_commitment": False,
        },
        "cohort_case_counts": {
            "exact8": 8,
            "rr8_unseen12": 12,
            "i6_probe8": 8,
            "total": 28,
        },
        "cohort_sources": {
            "exact8": {"ref": "grounded_human_reception_exact8_v2_20260712.json", "sha256": sha256_file(EXACT8_PATH), "classification": "known_legacy_or_app_validated_v1_comparison"},
            "rr8_unseen12": {"ref": "../local_only/grounded_human_reception_rr8_unseen12_20260713.json", "sha256": sha256_file(UNSEEN12_PATH), "classification": "known_legacy_v1_comparison"},
            "i6_probe8": {"ref": "../helpers/emlis_ai_grounded_observation_i6_cases.py", "sha256": sha256_file(I6_PATH), "classification": "known_legacy_v1_comparison"},
        },
        "cases": metric_rows,
        "aggregate_metrics": {
            "runtime_latency": {
                "measurement_scope": "render_emlis_ai_reply_local_process_no_http_route_db_or_network",
                "clock": "perf_counter_ns",
                "warmup_runs_per_case": max(0, warmup_runs),
                "samples_per_case": max(1, latency_samples),
                "python_version": platform.python_version(),
                "platform": f"{sys.platform}_{platform.machine() or 'unknown'}",
                **_latency_summary(all_latency),
                "acceptance_budget_status": "not_invented_pending_step15_protocol",
            },
            "observation_sentence_count_distribution": _distribution(row["observation_sentence_count"] for row in metric_rows),
            "reception_sentence_count_distribution": _distribution(row["reception_sentence_count"] for row in metric_rows),
            "visible_sentence_count_distribution": _distribution(row["visible_sentence_count"] for row in metric_rows),
            "reception_terminal_predicate_family_counts": dict(sorted(predicate_counts.items())),
            "source_resource_maxima_in_known_28": source_resource_maxima,
        },
        "generation_contract": {
            "runtime_owner": "grounded_sentence_surface_canonical_v1",
            "generation_method": "functional_atom_grounded_realizer",
            "composer_source": "grounded_plan_realizer",
            "generation_path": "grounded_observation_plan_sentence_surface_canonical_v1",
            "v3_runtime_connected": False,
            "v3_runtime_executed": False,
        },
        "known_regression_inventory": _known_regression_inventory(),
        "known_regression_source": {"ref": "emlis_nls_v2_all_steps_audit_20260713.json", "sha256": sha256_file(V2_AUDIT_PATH)},
        "supabase_corpus_status": input_contract["supabase_future_intake"]["current_status"],
        "source_modified_by_step1": False,
        "performance_budget_invented": False,
        "step1_status": "completed",
        "completion_condition": "source_v1_gate_latency_input_contract_and_known_regression_frozen",
        "next_step_authority": "step2_only",
        "valid_for_step2": True,
        "valid_for_runtime_switch": False,
        "body_free": True,
        "raw_input_included": False,
        "comment_text_included": False,
        "candidate_body_included": False,
    }
    assert_body_free(receipt)
    return visible_artifact, receipt


_S1_RECEIPT_KEYS = frozenset(
    {
        "schema_version",
        "created_date",
        "design_stage",
        "parent_step0_ref",
        "parent_step0_sha256",
        "input_contract_ref",
        "input_contract_sha256",
        "backend_archive_sha256",
        "source_owner_files",
        "source_owner_snapshot_sha256",
        "source_dependency_entry",
        "source_dependency_closure",
        "source_dependency_closure_sha256",
        "visible_artifact_ref",
        "visible_artifact_sha256",
        "commitment_policy",
        "cohort_case_counts",
        "cohort_sources",
        "cases",
        "aggregate_metrics",
        "generation_contract",
        "known_regression_inventory",
        "known_regression_source",
        "supabase_corpus_status",
        "source_modified_by_step1",
        "performance_budget_invented",
        "step1_status",
        "completion_condition",
        "next_step_authority",
        "valid_for_step2",
        "valid_for_runtime_switch",
        "body_free",
        "raw_input_included",
        "comment_text_included",
        "candidate_body_included",
    }
)
_S1_VISIBLE_KEYS = frozenset(
    {
        "schema_version",
        "created_date",
        "local_only",
        "known_synthetic_or_app_validated_inputs_only",
        "contains_real_user_supabase_corpus",
        "commitment_algorithm",
        "commitment_key_hex",
        "source_dependency_closure_sha256",
        "cohorts",
        "cases",
        "artifact_role",
        "counts_toward_karen_generated_v3_minimum",
        "v3_runtime_executed",
        "progression_authority",
    }
)
_S1_VISIBLE_CASE_KEYS = frozenset(
    {
        "case_id",
        "cohort",
        "family",
        "source_ref",
        "current_input",
        "visible_surface",
        "observation_section",
        "reception_section",
        "public_observation_status",
        "generation_method",
        "composer_source",
        "generation_path",
        "reception_depth_level",
        "reception_terminal_predicate_families",
        "commitments",
    }
)
_S1_RECEIPT_CASE_KEYS = frozenset(
    {
        "case_id",
        "cohort",
        "input_identity_commitment",
        "v1_body_commitment",
        "observation_commitment",
        "reception_commitment",
        "observation_sentence_count",
        "reception_sentence_count",
        "visible_sentence_count",
        "observation_quote_dependency",
        "reception_quote_dependency",
        "reception_depth_level",
        "reception_terminal_predicate_families",
        "source_resource_counts",
        "gate_status",
        "runtime_latency",
        "public_observation_status",
        "public_comment_present",
    }
)
_QUOTE_METRIC_KEYS = frozenset(
    {
        "span_count",
        "quoted_character_count",
        "section_character_count",
        "dependency_basis_points",
    }
)
_GATE_STATUS_KEYS = frozenset(
    {
        "plan_validity_gate",
        "evidence_resolution_gate",
        "required_coverage_gate",
        "text_semantic_retention_gate",
        "anti_template_gate",
        "mechanical_restatement_gate",
        "two_stage_contract_gate",
        "reception_all_gates_passed",
        "semantic_quality_gate",
        "runtime_final_contract_guard",
    }
)
_CASE_LATENCY_KEYS = frozenset(
    {"sample_count", "min_ms", "median_ms", "p95_ms", "max_ms", "samples_ms"}
)
_AGGREGATE_KEYS = frozenset(
    {
        "runtime_latency",
        "observation_sentence_count_distribution",
        "reception_sentence_count_distribution",
        "visible_sentence_count_distribution",
        "reception_terminal_predicate_family_counts",
        "source_resource_maxima_in_known_28",
    }
)
_AGGREGATE_LATENCY_KEYS = frozenset(
    {
        "measurement_scope",
        "clock",
        "warmup_runs_per_case",
        "samples_per_case",
        "python_version",
        "platform",
        "sample_count",
        "min_ms",
        "median_ms",
        "p95_ms",
        "max_ms",
        "acceptance_budget_status",
    }
)


def _has_exact_keys(value: Any, keys: frozenset[str]) -> bool:
    return isinstance(value, Mapping) and set(value) == keys


def _valid_latency_record(value: Any, *, expected_count: int) -> bool:
    if not _has_exact_keys(value, _CASE_LATENCY_KEYS):
        return False
    samples = value.get("samples_ms")
    if not isinstance(samples, list) or len(samples) != expected_count:
        return False
    if any(type(item) not in {int, float} or float(item) < 0 for item in samples):
        return False
    return {
        key: value.get(key)
        for key in ("sample_count", "min_ms", "median_ms", "p95_ms", "max_ms")
    } == _latency_summary([float(item) for item in samples])


def _strict_step1_issues(value: Mapping[str, Any]) -> tuple[str, ...]:
    issues: list[str] = []
    if not _has_exact_keys(value, _S1_RECEIPT_KEYS):
        issues.append("receipt_keyset_mismatch")
        return tuple(issues)

    fixed = {
        "schema_version": S1_RECEIPT_SCHEMA_VERSION,
        "created_date": "2026-07-14",
        "design_stage": "step1_baseline_actual_input_contract_freeze",
        "parent_step0_ref": S0_PATH.name,
        "parent_step0_sha256": sha256_file(S0_PATH),
        "input_contract_ref": S1_INPUT_PATH.name,
        "input_contract_sha256": sha256_file(S1_INPUT_PATH),
        "backend_archive_sha256": BACKEND_ARCHIVE_SHA256,
        "source_dependency_entry": DEPENDENCY_ENTRY_PATH,
        "visible_artifact_ref": "../local_only/emlis_nls_v3_s1_v1_visible_20260714.json",
        "visible_artifact_sha256": sha256_file(S1_VISIBLE_PATH),
        "supabase_corpus_status": "not_received_not_blocking",
        "source_modified_by_step1": False,
        "performance_budget_invented": False,
        "step1_status": "completed",
        "completion_condition": "source_v1_gate_latency_input_contract_and_known_regression_frozen",
        "next_step_authority": "step2_only",
        "valid_for_step2": True,
        "valid_for_runtime_switch": False,
        "body_free": True,
        "raw_input_included": False,
        "comment_text_included": False,
        "candidate_body_included": False,
    }
    if any(value.get(key) != expected for key, expected in fixed.items()):
        issues.append("receipt_fixed_value_mismatch")

    owners, owner_hash = historical_source_owner_snapshot()
    closure, closure_hash = historical_dependency_closure()
    if value.get("source_owner_files") != owners or value.get(
        "source_owner_snapshot_sha256"
    ) != owner_hash:
        issues.append("receipt_source_owner_mismatch")
    if value.get("source_dependency_closure") != closure or value.get(
        "source_dependency_closure_sha256"
    ) != closure_hash:
        issues.append("receipt_dependency_closure_mismatch")
    if value.get("commitment_policy") != {
        "algorithm": "hmac-sha256",
        "domain_separated": True,
        "key_location": "body_full_local_only_artifact",
        "key_in_body_free_receipt": False,
        "raw_sha256_used_for_short_body_commitment": False,
    }:
        issues.append("receipt_commitment_policy_mismatch")
    if value.get("cohort_case_counts") != {
        "exact8": 8,
        "rr8_unseen12": 12,
        "i6_probe8": 8,
        "total": 28,
    }:
        issues.append("receipt_cohort_counts_mismatch")
    if value.get("cohort_sources") != {
        "exact8": {
            "ref": "grounded_human_reception_exact8_v2_20260712.json",
            "sha256": sha256_file(EXACT8_PATH),
            "classification": "known_legacy_or_app_validated_v1_comparison",
        },
        "rr8_unseen12": {
            "ref": "../local_only/grounded_human_reception_rr8_unseen12_20260713.json",
            "sha256": sha256_file(UNSEEN12_PATH),
            "classification": "known_legacy_v1_comparison",
        },
        "i6_probe8": {
            "ref": "../helpers/emlis_ai_grounded_observation_i6_cases.py",
            "sha256": sha256_file(I6_PATH),
            "classification": "known_legacy_v1_comparison",
        },
    }:
        issues.append("receipt_cohort_sources_mismatch")
    if value.get("generation_contract") != {
        "runtime_owner": "grounded_sentence_surface_canonical_v1",
        "generation_method": "functional_atom_grounded_realizer",
        "composer_source": "grounded_plan_realizer",
        "generation_path": "grounded_observation_plan_sentence_surface_canonical_v1",
        "v3_runtime_connected": False,
        "v3_runtime_executed": False,
    }:
        issues.append("receipt_generation_contract_mismatch")
    if value.get("known_regression_inventory") != _known_regression_inventory():
        issues.append("known_regression_inventory_mismatch")
    if value.get("known_regression_source") != {
        "ref": "emlis_nls_v2_all_steps_audit_20260713.json",
        "sha256": sha256_file(V2_AUDIT_PATH),
    }:
        issues.append("known_regression_source_mismatch")

    visible = load_json(S1_VISIBLE_PATH)
    if not _has_exact_keys(visible, _S1_VISIBLE_KEYS):
        issues.append("visible_keyset_mismatch")
        return tuple(issues)
    visible_fixed = {
        "schema_version": S1_VISIBLE_SCHEMA_VERSION,
        "created_date": "2026-07-14",
        "local_only": True,
        "known_synthetic_or_app_validated_inputs_only": True,
        "contains_real_user_supabase_corpus": False,
        "commitment_algorithm": "hmac-sha256-domain-separated",
        "source_dependency_closure_sha256": closure_hash,
        "artifact_role": "canonical_v1_comparison_and_rollback_baseline_not_v3_expected_text",
        "counts_toward_karen_generated_v3_minimum": False,
        "v3_runtime_executed": False,
        "progression_authority": "none",
    }
    if any(visible.get(key) != expected for key, expected in visible_fixed.items()):
        issues.append("visible_fixed_value_mismatch")
    key_hex = visible.get("commitment_key_hex")
    if not isinstance(key_hex, str) or not _SHA256_RE.fullmatch(key_hex):
        issues.append("visible_commitment_key_invalid")
        key_hex = "0" * 64

    baseline_cases = load_baseline_cases()
    expected_cohorts = [
        {"cohort": cohort, "case_order": _case_order(baseline_cases, cohort)}
        for cohort in ("exact8", "rr8_unseen12", "i6_probe8")
    ]
    if visible.get("cohorts") != expected_cohorts:
        issues.append("visible_cohort_order_mismatch")
    visible_rows = visible.get("cases")
    receipt_rows = value.get("cases")
    if not isinstance(visible_rows, list) or not isinstance(receipt_rows, list):
        issues.append("step1_case_list_type_invalid")
        return tuple(issues)
    if len(visible_rows) != 28 or len(receipt_rows) != 28:
        issues.append("step1_case_count_mismatch")
        return tuple(issues)

    aggregate = value.get("aggregate_metrics")
    if not _has_exact_keys(aggregate, _AGGREGATE_KEYS):
        issues.append("aggregate_keyset_mismatch")
        return tuple(dict.fromkeys(issues))
    aggregate_latency = aggregate.get("runtime_latency")
    if not _has_exact_keys(aggregate_latency, _AGGREGATE_LATENCY_KEYS):
        issues.append("aggregate_latency_keyset_mismatch")
        return tuple(dict.fromkeys(issues))

    expected_gate = {key: "passed" for key in _GATE_STATUS_KEYS}
    expected_gate["reception_all_gates_passed"] = True
    predicate_counts: Counter[str] = Counter()
    all_latency: list[float] = []
    expected_observation_counts: list[int] = []
    expected_reception_counts: list[int] = []
    expected_visible_counts: list[int] = []
    resource_rows: list[dict[str, int]] = []
    seen_ids: set[tuple[str, str]] = set()
    for case, visible_row, receipt_row in zip(
        baseline_cases, visible_rows, receipt_rows
    ):
        if not _has_exact_keys(visible_row, _S1_VISIBLE_CASE_KEYS):
            issues.append("visible_case_keyset_mismatch")
            continue
        if not _has_exact_keys(receipt_row, _S1_RECEIPT_CASE_KEYS):
            issues.append("receipt_case_keyset_mismatch")
            continue
        identity = (case.cohort, case.case_id)
        if identity in seen_ids:
            issues.append("receipt_case_identity_duplicate")
        seen_ids.add(identity)
        if (
            visible_row.get("case_id") != case.case_id
            or visible_row.get("cohort") != case.cohort
            or visible_row.get("family") != case.family
            or visible_row.get("source_ref") != case.source_ref
            or visible_row.get("current_input") != dict(case.current_input)
            or receipt_row.get("case_id") != case.case_id
            or receipt_row.get("cohort") != case.cohort
        ):
            issues.append("step1_case_identity_or_input_mismatch")
        visible_text = str(visible_row.get("visible_surface") or "")
        observation, reception, split_issues = split_two_stage_surface(visible_text)
        observation = observation.strip()
        reception = reception.strip()
        if (
            split_issues
            or visible_row.get("observation_section") != observation
            or visible_row.get("reception_section") != reception
        ):
            issues.append("visible_two_stage_body_mismatch")
        expected_commitments = {
            "input": hmac_commit_json(
                key_hex, f"input:{case.cohort}:{case.case_id}", dict(case.current_input)
            ),
            "visible": hmac_commit_text(
                key_hex, f"visible:{case.cohort}:{case.case_id}", visible_text
            ),
            "observation": hmac_commit_text(
                key_hex, f"observation:{case.cohort}:{case.case_id}", observation
            ),
            "reception": hmac_commit_text(
                key_hex, f"reception:{case.cohort}:{case.case_id}", reception
            ),
        }
        if visible_row.get("commitments") != expected_commitments:
            issues.append("visible_commitment_mismatch")
        if {
            "input": receipt_row.get("input_identity_commitment"),
            "visible": receipt_row.get("v1_body_commitment"),
            "observation": receipt_row.get("observation_commitment"),
            "reception": receipt_row.get("reception_commitment"),
        } != expected_commitments:
            issues.append("receipt_commitment_mismatch")
        if any(
            visible_row.get(key) != expected
            for key, expected in {
                "public_observation_status": "passed",
                "generation_method": "functional_atom_grounded_realizer",
                "composer_source": "grounded_plan_realizer",
                "generation_path": "grounded_observation_plan_sentence_surface_canonical_v1",
            }.items()
        ):
            issues.append("visible_generation_contract_mismatch")
        observation_count = len(split_reception_sentences(observation))
        reception_count = len(split_reception_sentences(reception))
        visible_count = observation_count + reception_count
        expected_observation_counts.append(observation_count)
        expected_reception_counts.append(reception_count)
        expected_visible_counts.append(visible_count)
        if (
            receipt_row.get("observation_sentence_count") != observation_count
            or receipt_row.get("reception_sentence_count") != reception_count
            or receipt_row.get("visible_sentence_count") != visible_count
            or receipt_row.get("observation_quote_dependency")
            != _quote_metrics(observation)
            or receipt_row.get("reception_quote_dependency")
            != _quote_metrics(reception)
            or not _has_exact_keys(
                receipt_row.get("observation_quote_dependency"), _QUOTE_METRIC_KEYS
            )
            or not _has_exact_keys(
                receipt_row.get("reception_quote_dependency"), _QUOTE_METRIC_KEYS
            )
        ):
            issues.append("receipt_case_metric_mismatch")
        if receipt_row.get("gate_status") != expected_gate:
            issues.append("receipt_gate_status_mismatch")
        visible_depth = visible_row.get("reception_depth_level")
        visible_predicates = visible_row.get(
            "reception_terminal_predicate_families"
        )
        depth = receipt_row.get("reception_depth_level")
        predicates = receipt_row.get("reception_terminal_predicate_families")
        if (
            visible_depth not in {"minimal", "focused", "layered"}
            or not isinstance(visible_predicates, list)
            or not visible_predicates
            or any(
                not isinstance(item, str)
                or not re.fullmatch(r"[a-z0-9_]+", item)
                for item in visible_predicates
            )
            or depth not in {"minimal", "focused", "layered"}
            or not isinstance(predicates, list)
            or not predicates
            or any(
                not isinstance(item, str)
                or not re.fullmatch(r"[a-z0-9_]+", item)
                for item in predicates
            )
        ):
            issues.append("receipt_reception_metric_shape_invalid")
        elif depth != visible_depth or predicates != visible_predicates:
            issues.append("receipt_reception_metric_mismatch")
        else:
            predicate_counts.update(predicates)
        resource_counts = _source_resource_counts(case.current_input)
        resource_rows.append(resource_counts)
        if receipt_row.get("source_resource_counts") != resource_counts:
            issues.append("receipt_source_resource_count_mismatch")
        samples_per_case = aggregate_latency.get("samples_per_case")
        if type(samples_per_case) is not int or samples_per_case < 1 or not _valid_latency_record(
            receipt_row.get("runtime_latency"), expected_count=samples_per_case
        ):
            issues.append("receipt_case_latency_invalid")
        else:
            all_latency.extend(
                float(item)
                for item in receipt_row["runtime_latency"]["samples_ms"]
            )
        if (
            receipt_row.get("public_observation_status") != "passed"
            or receipt_row.get("public_comment_present") is not True
        ):
            issues.append("receipt_public_status_mismatch")

    samples_per_case = aggregate_latency.get("samples_per_case")
    warmup_runs = aggregate_latency.get("warmup_runs_per_case")
    static_latency = {
        "measurement_scope": "render_emlis_ai_reply_local_process_no_http_route_db_or_network",
        "clock": "perf_counter_ns",
        "python_version": platform.python_version(),
        "platform": f"{sys.platform}_{platform.machine() or 'unknown'}",
        "acceptance_budget_status": "not_invented_pending_step15_protocol",
    }
    if (
        type(samples_per_case) is not int
        or samples_per_case < 1
        or type(warmup_runs) is not int
        or warmup_runs < 0
        or any(
            aggregate_latency.get(key) != expected
            for key, expected in static_latency.items()
        )
        or {
            key: aggregate_latency.get(key)
            for key in ("sample_count", "min_ms", "median_ms", "p95_ms", "max_ms")
        }
        != _latency_summary(all_latency)
    ):
        issues.append("aggregate_latency_mismatch")
    if aggregate.get("observation_sentence_count_distribution") != _distribution(
        expected_observation_counts
    ) or aggregate.get("reception_sentence_count_distribution") != _distribution(
        expected_reception_counts
    ) or aggregate.get("visible_sentence_count_distribution") != _distribution(
        expected_visible_counts
    ) or aggregate.get("reception_terminal_predicate_family_counts") != dict(
        sorted(predicate_counts.items())
    ):
        issues.append("aggregate_semantic_distribution_mismatch")
    expected_resource_maxima = {
        key: max(row[key] for row in resource_rows)
        for key in sorted(_SOURCE_RESOURCE_COUNT_KEYS)
    }
    if aggregate.get("source_resource_maxima_in_known_28") != expected_resource_maxima:
        issues.append("aggregate_source_resource_mismatch")
    return tuple(dict.fromkeys(issues))


def validate_step0(value: Mapping[str, Any]) -> tuple[str, ...]:
    issues: list[str] = []
    if dict(value) != build_step0():
        issues.append("strict_contract_mismatch")
    identity = dict(value.get("version_identity") or {})
    boundary = dict(value.get("v2_boundary") or {})
    if value.get("schema_version") != S0_SCHEMA_VERSION:
        issues.append("schema_mismatch")
    if value.get("design", {}).get("sha256") != DESIGN_SHA256:
        issues.append("design_hash_mismatch")
    if identity.get("candidate_version") != "nls_v3":
        issues.append("candidate_identity_mismatch")
    if tuple(identity.get("allowed_runtime_states") or ()) != RUNTIME_STATES:
        issues.append("runtime_state_enum_mismatch")
    if tuple(identity.get("allowed_observation_stages") or ()) != OBSERVATION_STAGES:
        issues.append("observation_stage_enum_mismatch")
    if identity.get("runtime_connected") is not False or identity.get("runtime_owner") is not False:
        issues.append("runtime_boundary_changed")
    if boundary.get("state") != "offline_only_stopped":
        issues.append("v2_not_stopped")
    if boundary.get("repair_allowed") is not False or boundary.get("reopen_allowed") is not False:
        issues.append("v2_repair_or_reopen_allowed")
    live_v2, live_v2_hash = discover_v2_immutable_manifest()
    if boundary.get("immutable_files") != live_v2 or boundary.get("immutable_manifest_sha256") != live_v2_hash:
        issues.append("v2_immutable_manifest_drift")
    _, frozen_owner_hash = historical_source_owner_snapshot()
    if value.get("current_runtime", {}).get("source_owner_snapshot_sha256") != frozen_owner_hash:
        issues.append("source_owner_snapshot_drift")
    if value.get("current_runtime", {}).get("production_surface_owner") != "grounded_sentence_surface_canonical_v1":
        issues.append("production_owner_changed")
    if value.get("step0_status") != "completed" or value.get("next_step_authority") != "step1_only":
        issues.append("completion_or_authority_invalid")
    try:
        assert_body_free(value)
    except ValueError as exc:
        issues.append(str(exc))
    return tuple(issues)


def validate_input_contract(value: Mapping[str, Any]) -> tuple[str, ...]:
    issues: list[str] = []
    if dict(value) != build_input_contract():
        issues.append("strict_contract_mismatch")
    app = dict(value.get("app_reachable") or {})
    backend = dict(value.get("backend_compatibility_boundary") or {})
    if value.get("schema_version") != S1_INPUT_SCHEMA_VERSION:
        issues.append("schema_mismatch")
    if tuple(app.get("emotion_types") or ()) != EMOTION_TYPES:
        issues.append("emotion_options_mismatch")
    if tuple(app.get("strength_types") or ()) != STRENGTHS:
        issues.append("strength_options_mismatch")
    if tuple(app.get("category_types") or ()) != CATEGORY_TYPES:
        issues.append("category_options_mismatch")
    if app.get("self_insight_exclusive") is not True or app.get("self_insight_strength") != "medium":
        issues.append("self_insight_contract_mismatch")
    if app.get("text_requirement") != "trimmed_memo_or_memo_action_nonempty" or app.get("category_min_count") != 1 or app.get("emotion_min_count") != 1:
        issues.append("submit_condition_mismatch")
    if app.get("text_length_limit_added_by_nls_v3") is not False:
        issues.append("invented_text_limit")
    _, backend_hash = public_backend_snapshot()
    if backend.get("owner_snapshot_sha256") != backend_hash:
        issues.append("backend_boundary_snapshot_drift")
    if backend.get("backend_permissiveness_is_app_valid_authority") is not False:
        issues.append("backend_promoted_to_app_authority")
    try:
        assert_body_free(value)
    except ValueError as exc:
        issues.append(str(exc))
    return tuple(issues)


def validate_step1(value: Mapping[str, Any]) -> tuple[str, ...]:
    issues: list[str] = list(_strict_step1_issues(value))
    if value.get("schema_version") != S1_RECEIPT_SCHEMA_VERSION:
        issues.append("schema_mismatch")
    if value.get("parent_step0_sha256") != sha256_file(S0_PATH):
        issues.append("parent_step0_hash_mismatch")
    if value.get("input_contract_sha256") != sha256_file(S1_INPUT_PATH):
        issues.append("input_contract_hash_mismatch")
    owners, owner_hash = historical_source_owner_snapshot()
    closure, closure_hash = historical_dependency_closure()
    if value.get("source_owner_files") != owners or value.get("source_owner_snapshot_sha256") != owner_hash:
        issues.append("source_owner_snapshot_drift")
    if value.get("source_dependency_closure") != closure or value.get("source_dependency_closure_sha256") != closure_hash:
        issues.append("source_dependency_closure_drift")
    if value.get("visible_artifact_sha256") != sha256_file(S1_VISIBLE_PATH):
        issues.append("visible_artifact_hash_mismatch")
    if value.get("cohort_case_counts") != {"exact8": 8, "rr8_unseen12": 12, "i6_probe8": 8, "total": 28}:
        issues.append("baseline_case_count_mismatch")
    aggregate = value.get("aggregate_metrics")
    latency = aggregate.get("runtime_latency") if isinstance(aggregate, Mapping) else {}
    if not isinstance(latency, Mapping):
        latency = {}
    if latency.get("sample_count") != 28 * int(latency.get("samples_per_case") or 0):
        issues.append("latency_sample_count_mismatch")
    if value.get("performance_budget_invented") is not False:
        issues.append("performance_budget_invented")
    if value.get("step1_status") != "completed" or value.get("next_step_authority") != "step2_only":
        issues.append("completion_or_authority_invalid")
    try:
        assert_body_free(value)
    except ValueError as exc:
        issues.append(str(exc))
    return tuple(issues)


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_all(*, warmup_runs: int = 1, latency_samples: int = 5) -> None:
    step0 = build_step0()
    if validate_step0(step0):
        raise ValueError("step0_contract_invalid:" + ",".join(validate_step0(step0)))
    _write_json(S0_PATH, step0)
    input_contract = build_input_contract()
    if validate_input_contract(input_contract):
        raise ValueError("input_contract_invalid:" + ",".join(validate_input_contract(input_contract)))
    _write_json(S1_INPUT_PATH, input_contract)
    visible, receipt = asyncio.run(
        capture_step1(warmup_runs=warmup_runs, latency_samples=latency_samples)
    )
    _write_json(S1_VISIBLE_PATH, visible)
    receipt["visible_artifact_sha256"] = sha256_file(S1_VISIBLE_PATH)
    if validate_step1(receipt):
        raise ValueError("step1_contract_invalid:" + ",".join(validate_step1(receipt)))
    _write_json(S1_RECEIPT_PATH, receipt)


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--warmup-runs", type=int, default=1)
    parser.add_argument("--latency-samples", type=int, default=5)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    if not args.write:
        raise SystemExit("use --write to create the Step 0/1 artifacts")
    write_all(
        warmup_runs=max(0, args.warmup_runs),
        latency_samples=max(1, args.latency_samples),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "S0_PATH",
    "S1_INPUT_PATH",
    "S1_VISIBLE_PATH",
    "S1_RECEIPT_PATH",
    "S0_SCHEMA_VERSION",
    "S1_INPUT_SCHEMA_VERSION",
    "S1_VISIBLE_SCHEMA_VERSION",
    "S1_RECEIPT_SCHEMA_VERSION",
    "assert_body_free",
    "build_input_contract",
    "build_step0",
    "current_dependency_closure",
    "current_source_owner_snapshot",
    "dependency_closure",
    "discover_v2_immutable_manifest",
    "historical_dependency_closure",
    "historical_source_owner_snapshot",
    "hmac_commit_json",
    "hmac_commit_text",
    "load_baseline_cases",
    "load_json",
    "sha256_file",
    "sha256_json",
    "source_owner_snapshot",
    "validate_input_contract",
    "validate_step0",
    "validate_step1",
    "write_all",
]
