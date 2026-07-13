# -*- coding: utf-8 -*-
from __future__ import annotations

"""Generate and verify the local-only Natural Language Surface v2 v1 baseline.

This helper is test-only.  It captures the current production v1 owner before
any v2 candidate generator exists.  User input and visible text are written
only to the local-only artifact; the receipt contains hashes and metrics only.
"""

import argparse
import asyncio
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import platform
import re
import statistics
import sys
import time
from typing import Any, Iterable, Mapping, Sequence


_AI_ROOT = Path(__file__).resolve().parents[2]
_TEST_ROOT = _AI_ROOT / "tests"
_INFERENCE_ROOT = _AI_ROOT / "services" / "ai_inference"
if str(_INFERENCE_ROOT) not in sys.path:
    sys.path.insert(0, str(_INFERENCE_ROOT))

from emlis_ai_public_feedback_meta import (  # noqa: E402
    build_public_emlis_input_feedback_meta,
    should_include_public_input_feedback,
)
from emlis_ai_reply_service import render_emlis_ai_reply  # noqa: E402
from emlis_ai_grounded_sentence_surface import split_two_stage_surface  # noqa: E402
from helpers.emlis_ai_grounded_human_reception_r6_qa import (  # noqa: E402
    split_reception_sentences,
)
from helpers.emlis_ai_grounded_observation_i6_cases import (  # noqa: E402
    GROUND_OBSERVATION_I6_BLIND_CASES,
)


S0_SCHEMA_VERSION = "cocolon.emlis.nls_v2.step0_design_freeze.v1"
S1_VISIBLE_SCHEMA_VERSION = "cocolon.emlis.nls_v2.v1_visible_baseline.local_only.v1"
S1_RECEIPT_SCHEMA_VERSION = "cocolon.emlis.nls_v2.v1_baseline_receipt.v1"

S0_FREEZE_PATH = _TEST_ROOT / "fixtures" / "emlis_nls_v2_s0_freeze_20260713.json"
S1_VISIBLE_PATH = _TEST_ROOT / "local_only" / "emlis_nls_v2_s1_visible_20260713.json"
S1_RECEIPT_PATH = _TEST_ROOT / "fixtures" / "emlis_nls_v2_s1_receipt_20260713.json"
EXACT8_PATH = _TEST_ROOT / "fixtures" / "grounded_human_reception_exact8_v2_20260712.json"
UNSEEN12_PATH = _TEST_ROOT / "local_only" / "grounded_human_reception_rr8_unseen12_20260713.json"
I6_PROBE_SOURCE_PATH = _TEST_ROOT / "helpers" / "emlis_ai_grounded_observation_i6_cases.py"

SOURCE_OWNER_PATHS = (
    "ai/services/ai_inference/emlis_ai_grounded_observation_plan.py",
    "ai/services/ai_inference/emlis_ai_grounded_human_reception.py",
    "ai/services/ai_inference/emlis_ai_grounded_sentence_surface.py",
    "ai/services/ai_inference/emlis_ai_grounded_observation_gate.py",
    "ai/services/ai_inference/emlis_ai_reply_service.py",
)
PUBLIC_BACKEND_OWNER_PATHS = (
    "ai/services/ai_inference/api_emotion_submit.py",
    "ai/services/ai_inference/emotion_submit_service.py",
    "ai/services/ai_inference/emlis_ai_public_feedback_meta.py",
    "ai/services/ai_inference/emlis_ai_reply_service.py",
)

_EXACT8_I6_CASE_IDS = frozenset({"I6-S03", "I6-L03", "I6-C01", "I6-D02"})
_QUOTE_RE = re.compile(r"「([^」]+)」|『([^』]+)』")
_WHITESPACE_RE = re.compile(r"\s+")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
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
    }
)
_BODY_FLAGS = frozenset(
    {
        "raw_input_included",
        "raw_text_included",
        "source_text_included",
        "comment_text_included",
        "surface_body_included",
        "visible_text_included",
        "observation_text_included",
        "reception_text_included",
        "candidate_body_included",
    }
)


@dataclass(frozen=True)
class BaselineCase:
    case_id: str
    cohort: str
    family: str
    current_input: Mapping[str, Any]
    source_ref: str


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(str(value).encode("utf-8"))


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_json(value: Any) -> str:
    return sha256_text(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    )


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _repo_root() -> Path:
    return _AI_ROOT.parent


def source_snapshot() -> tuple[list[dict[str, str]], str]:
    root = _repo_root()
    rows = [
        {"path": path, "sha256": sha256_file(root / path)}
        for path in SOURCE_OWNER_PATHS
    ]
    return rows, sha256_json(rows)


def public_backend_snapshot() -> tuple[list[dict[str, str]], str]:
    root = _repo_root()
    rows = [
        {"path": path, "sha256": sha256_file(root / path)}
        for path in PUBLIC_BACKEND_OWNER_PATHS
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
                cohort="existing_unseen12",
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
                cohort="existing_i6_probe8",
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
        "existing_unseen12": 12,
        "existing_i6_probe8": 8,
    }:
        raise ValueError("baseline_cohort_shape_invalid")
    return tuple(rows)


def _quote_metrics(value: str) -> dict[str, int]:
    spans = [left or right for left, right in _QUOTE_RE.findall(str(value or ""))]
    compact = _WHITESPACE_RE.sub("", str(value or ""))
    quoted_chars = sum(len(item) for item in spans)
    return {
        "span_count": len(spans),
        "quoted_character_count": quoted_chars,
        "section_character_count": len(compact),
        "dependency_basis_points": round(10_000 * quoted_chars / max(1, len(compact))),
    }


def _nearest_rank(values: Sequence[float], percentile: float) -> float:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        return 0.0
    index = max(0, math.ceil(percentile * len(ordered)) - 1)
    return ordered[index]


def _latency_summary(samples: Sequence[float]) -> dict[str, float | int]:
    values = tuple(round(float(value), 6) for value in samples)
    return {
        "sample_count": len(values),
        "min_ms": round(min(values, default=0.0), 6),
        "median_ms": round(statistics.median(values), 6) if values else 0.0,
        "p95_ms": round(_nearest_rank(values, 0.95), 6),
        "max_ms": round(max(values, default=0.0), 6),
    }


async def _render(current_input: Mapping[str, Any], *, user_id: str):
    return await render_emlis_ai_reply(
        user_id=user_id,
        subscription_tier="free",
        current_input=dict(current_input),
    )


async def _capture_case(
    case: BaselineCase,
    *,
    warmup_runs: int,
    latency_samples: int,
) -> tuple[dict[str, Any], dict[str, Any], tuple[float, ...]]:
    reply = await _render(case.current_input, user_id=f"nls-v2-s1-{case.case_id}")
    visible = str(reply.comment_text or "").strip()
    observation, reception, issues = split_two_stage_surface(visible)
    if issues:
        raise ValueError(f"baseline_two_stage_split_failed:{case.case_id}:{issues}")
    observation = observation.strip()
    reception = reception.strip()

    public = build_public_emlis_input_feedback_meta(
        reply.meta,
        comment_text_present=bool(visible),
        subscription_tier="free",
    )
    if not should_include_public_input_feedback(visible, public):
        raise ValueError(f"baseline_public_contract_failed:{case.case_id}")
    if public.get("observation_status") != "passed":
        raise ValueError(f"baseline_public_status_failed:{case.case_id}")

    gate = dict(reply.meta.get("grounded_observation") or {})
    if gate.get("runtime_final_contract_guard") != "passed":
        raise ValueError(f"baseline_runtime_guard_failed:{case.case_id}")

    visible_sha256 = sha256_text(visible)
    for index in range(max(0, warmup_runs)):
        warm = await _render(
            case.current_input,
            user_id=f"nls-v2-s1-warm-{case.case_id}-{index}",
        )
        if sha256_text(str(warm.comment_text or "").strip()) != visible_sha256:
            raise ValueError(f"baseline_warmup_nondeterministic:{case.case_id}")

    samples: list[float] = []
    for index in range(max(1, latency_samples)):
        started = time.perf_counter_ns()
        measured = await _render(
            case.current_input,
            user_id=f"nls-v2-s1-measure-{case.case_id}-{index}",
        )
        elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000
        if sha256_text(str(measured.comment_text or "").strip()) != visible_sha256:
            raise ValueError(f"baseline_measure_nondeterministic:{case.case_id}")
        samples.append(elapsed_ms)

    observation_sentences = split_reception_sentences(observation)
    reception_sentences = split_reception_sentences(reception)
    if len(reception_sentences) != int(gate.get("reception_sentence_count") or 0):
        raise ValueError(f"baseline_reception_sentence_count_mismatch:{case.case_id}")

    current_input = dict(case.current_input)
    input_sha256 = sha256_json(current_input)
    visible_row = {
        "case_id": case.case_id,
        "cohort": case.cohort,
        "family": case.family,
        "source_ref": case.source_ref,
        "current_input": current_input,
        "current_input_sha256": input_sha256,
        "visible_surface": visible,
        "visible_surface_sha256": visible_sha256,
        "observation_section": observation,
        "observation_section_sha256": sha256_text(observation),
        "reception_section": reception,
        "reception_section_sha256": sha256_text(reception),
        "public_observation_status": str(public["observation_status"]),
        "generation_method": str(reply.meta.get("generation_method") or ""),
        "composer_source": str(reply.meta.get("composer_source") or ""),
        "generation_path": str(reply.meta.get("generation_path") or ""),
    }
    metric_row = {
        "case_id": case.case_id,
        "cohort": case.cohort,
        "current_input_sha256": input_sha256,
        "visible_surface_sha256": visible_sha256,
        "observation_section_sha256": sha256_text(observation),
        "reception_section_sha256": sha256_text(reception),
        "observation_sentence_count": len(observation_sentences),
        "reception_sentence_count": len(reception_sentences),
        "visible_sentence_count": len(observation_sentences) + len(reception_sentences),
        "observation_quote_dependency": _quote_metrics(observation),
        "reception_quote_dependency": _quote_metrics(reception),
        "reception_depth_level": str(gate.get("reception_depth_level") or ""),
        "reception_terminal_predicate_families": list(
            gate.get("reception_terminal_predicate_families") or ()
        ),
        "runtime_latency": _latency_summary(samples),
        "public_observation_status": str(public["observation_status"]),
        "public_comment_present": bool(visible),
    }
    return visible_row, metric_row, tuple(samples)


def _case_order(rows: Iterable[BaselineCase], cohort: str) -> list[str]:
    return [row.case_id for row in rows if row.cohort == cohort]


def _distribution(values: Iterable[Any]) -> dict[str, int]:
    return dict(sorted(Counter(str(value) for value in values).items()))


async def capture_baseline(
    *,
    warmup_runs: int = 1,
    latency_samples: int = 5,
) -> tuple[dict[str, Any], dict[str, Any]]:
    cases = load_baseline_cases()
    manifest, snapshot_sha256 = source_snapshot()
    public_owners, public_owners_sha256 = public_backend_snapshot()
    freeze = load_json(S0_FREEZE_PATH)
    if freeze.get("source_snapshot_sha256") != snapshot_sha256:
        raise ValueError("step0_source_snapshot_mismatch")

    visible_rows: list[dict[str, Any]] = []
    metric_rows: list[dict[str, Any]] = []
    all_latency_samples: list[float] = []
    for case in cases:
        visible, metric, samples = await _capture_case(
            case,
            warmup_runs=warmup_runs,
            latency_samples=latency_samples,
        )
        visible_rows.append(visible)
        metric_rows.append(metric)
        all_latency_samples.extend(samples)

    visible_artifact = {
        "schema_version": S1_VISIBLE_SCHEMA_VERSION,
        "created_date": "2026-07-13",
        "local_only": True,
        "source_snapshot_files": manifest,
        "source_snapshot_sha256": snapshot_sha256,
        "cohorts": [
            {
                "cohort": "exact8",
                "case_order": _case_order(cases, "exact8"),
                "source_ref": "../fixtures/grounded_human_reception_exact8_v2_20260712.json",
                "source_sha256": sha256_file(EXACT8_PATH),
            },
            {
                "cohort": "existing_unseen12",
                "case_order": _case_order(cases, "existing_unseen12"),
                "source_ref": "grounded_human_reception_rr8_unseen12_20260713.json",
                "source_sha256": sha256_file(UNSEEN12_PATH),
            },
            {
                "cohort": "existing_i6_probe8",
                "case_order": _case_order(cases, "existing_i6_probe8"),
                "source_ref": "../helpers/emlis_ai_grounded_observation_i6_cases.py",
                "source_sha256": sha256_file(I6_PROBE_SOURCE_PATH),
            },
        ],
        "cases": visible_rows,
        "artifact_role": "v1_comparison_baseline_not_v2_expected_text",
        "v2_expected_text": False,
        "holdout_a_opened": False,
        "holdout_b_opened": False,
        "progression_authority": "none",
        "valid_for_progression": False,
    }

    predicate_counts: Counter[str] = Counter()
    for row in metric_rows:
        predicate_counts.update(row["reception_terminal_predicate_families"])
    receipt = {
        "schema_version": S1_RECEIPT_SCHEMA_VERSION,
        "created_date": "2026-07-13",
        "design_stage": "step1_v1_baseline_receipt",
        "step0_freeze_ref": "emlis_nls_v2_s0_freeze_20260713.json",
        "step0_freeze_sha256": sha256_file(S0_FREEZE_PATH),
        "source_snapshot_files": manifest,
        "source_snapshot_sha256": snapshot_sha256,
        "visible_artifact_ref": "../local_only/emlis_nls_v2_s1_visible_20260713.json",
        "visible_artifact_sha256": "pending_write",
        "cohort_case_counts": {
            "exact8": 8,
            "existing_unseen12": 12,
            "existing_i6_probe8": 8,
            "total": 28,
        },
        "cohort_sources": {
            "exact8": {
                "ref": "grounded_human_reception_exact8_v2_20260712.json",
                "sha256": sha256_file(EXACT8_PATH),
            },
            "existing_unseen12": {
                "ref": "../local_only/grounded_human_reception_rr8_unseen12_20260713.json",
                "sha256": sha256_file(UNSEEN12_PATH),
            },
            "existing_i6_probe8": {
                "ref": "../helpers/emlis_ai_grounded_observation_i6_cases.py",
                "sha256": sha256_file(I6_PROBE_SOURCE_PATH),
            },
        },
        "cohort_case_order_sha256": {
            cohort: sha256_text("\n".join(_case_order(cases, cohort)))
            for cohort in ("exact8", "existing_unseen12", "existing_i6_probe8")
        },
        "cases": metric_rows,
        "aggregate_metrics": {
            "runtime_latency": {
                "measurement_scope": "render_emlis_ai_reply_local_process_no_route_db_or_network",
                "clock": "perf_counter_ns",
                "warmup_runs_per_case": max(0, warmup_runs),
                "samples_per_case": max(1, latency_samples),
                "python_version": platform.python_version(),
                "platform": f"{sys.platform}_{platform.machine() or 'unknown'}",
                **_latency_summary(all_latency_samples),
                "acceptance_budget_status": "not_fixed_before_step10_shadow",
            },
            "observation_sentence_count_distribution": _distribution(
                row["observation_sentence_count"] for row in metric_rows
            ),
            "reception_sentence_count_distribution": _distribution(
                row["reception_sentence_count"] for row in metric_rows
            ),
            "visible_sentence_count_distribution": _distribution(
                row["visible_sentence_count"] for row in metric_rows
            ),
            "observation_quote_dependency_basis_points": {
                "median": round(
                    statistics.median(
                        row["observation_quote_dependency"]["dependency_basis_points"]
                        for row in metric_rows
                    )
                ),
                "max": max(
                    row["observation_quote_dependency"]["dependency_basis_points"]
                    for row in metric_rows
                ),
            },
            "reception_quote_dependency_basis_points": {
                "median": round(
                    statistics.median(
                        row["reception_quote_dependency"]["dependency_basis_points"]
                        for row in metric_rows
                    )
                ),
                "max": max(
                    row["reception_quote_dependency"]["dependency_basis_points"]
                    for row in metric_rows
                ),
            },
            "reception_terminal_predicate_family_counts": dict(
                sorted(predicate_counts.items())
            ),
            "predicate_concentration_limit_status": "pending_step2_development42_baseline",
        },
        "public_contract_snapshot": {
            "route": "/emotion/submit",
            "response_container": "input_feedback",
            "comment_path": "input_feedback.comment_text",
            "status_path": "input_feedback.emlis_ai.observation_status",
            "visibility_predicate": "status_passed_and_comment_nonempty",
            "two_stage_order": "observation_then_reception",
            "backend_owner_files": public_owners,
            "backend_owner_snapshot_sha256": public_owners_sha256,
            "rn_owner_snapshot_ref": "step0_freeze.public_contract_snapshot.rn_owner_files",
            "api_response_key_changed": False,
            "rn_visibility_contract_changed": False,
            "db_write_path_changed": False,
        },
        "generation_contract": {
            "generation_method": "functional_atom_grounded_realizer",
            "composer_source": "grounded_plan_realizer",
            "generation_path": "grounded_observation_plan_sentence_surface_canonical_v1",
            "runtime_owner": "v1",
            "v2_runtime_connected": False,
        },
        "v1_baseline_role": "comparison_only_not_v2_expected_text",
        "v1_expected_text_for_v2": False,
        "body_free_metadata": True,
        "raw_input_included": False,
        "raw_text_included": False,
        "source_text_included": False,
        "comment_text_included": False,
        "surface_body_included": False,
        "visible_text_included": False,
        "observation_text_included": False,
        "reception_text_included": False,
        "candidate_body_included": False,
        "holdout_a_opened": False,
        "holdout_b_opened": False,
        "current_product_status": "repair_required",
        "step1_status": "completed",
        "progression_authority": "none",
        "valid_for_progression": False,
    }
    return visible_artifact, receipt


def assert_body_free_metadata(value: Any) -> None:
    if isinstance(value, Mapping):
        for raw_key, nested in value.items():
            key = str(raw_key)
            if key in _FORBIDDEN_BODY_KEYS:
                raise ValueError(f"body_free_forbidden_key:{key}")
            if key in _BODY_FLAGS and nested is not False:
                raise ValueError(f"body_free_flag_true:{key}")
            assert_body_free_metadata(nested)
        return
    if isinstance(value, (list, tuple)):
        for nested in value:
            assert_body_free_metadata(nested)


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_baseline(*, warmup_runs: int = 1, latency_samples: int = 5) -> None:
    visible, receipt = asyncio.run(
        capture_baseline(
            warmup_runs=warmup_runs,
            latency_samples=latency_samples,
        )
    )
    _write_json(S1_VISIBLE_PATH, visible)
    receipt["visible_artifact_sha256"] = sha256_file(S1_VISIBLE_PATH)
    assert _SHA256_RE.fullmatch(receipt["visible_artifact_sha256"])
    assert_body_free_metadata(receipt)
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
        raise SystemExit("use --write to regenerate the Step 1 baseline artifacts")
    write_baseline(
        warmup_runs=max(0, args.warmup_runs),
        latency_samples=max(1, args.latency_samples),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "S0_SCHEMA_VERSION",
    "S1_VISIBLE_SCHEMA_VERSION",
    "S1_RECEIPT_SCHEMA_VERSION",
    "S0_FREEZE_PATH",
    "S1_VISIBLE_PATH",
    "S1_RECEIPT_PATH",
    "SOURCE_OWNER_PATHS",
    "PUBLIC_BACKEND_OWNER_PATHS",
    "BaselineCase",
    "assert_body_free_metadata",
    "capture_baseline",
    "load_baseline_cases",
    "load_json",
    "public_backend_snapshot",
    "sha256_file",
    "sha256_json",
    "sha256_text",
    "source_snapshot",
    "write_baseline",
]
