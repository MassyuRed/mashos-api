# -*- coding: utf-8 -*-
from __future__ import annotations

"""Generate R8 local-only comparison and body-free R9 decision artifacts."""

import asyncio
import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from helpers.emlis_ai_gate0_r9_r10_boundary import (
    Gate0ValidationEvidence,
    build_gate0_local_decision,
    validate_gate0_validation_evidence,
)
from helpers.emlis_ai_grounded_observation_i0_inventory import (
    GROUND_OBSERVATION_I0_KNOWN_REGRESSION_CASES,
)
from helpers.emlis_ai_grounded_observation_i6_cases import (
    GROUND_OBSERVATION_I6_BLIND_CASES,
)
from helpers.emlis_ai_grounded_observation_i7_readfeel import (
    I7KarenLocalReview,
    assess_i7_local_surface,
)
from emlis_ai_current_input_bundle import normalize_emlis_current_input
from emlis_ai_evidence_ledger_service import (
    build_evidence_ledger,
    build_evidence_span_resolver,
)
from emlis_ai_grounded_observation_plan import build_grounded_observation_plan
from emlis_ai_grounded_sentence_surface import (
    build_grounded_sentence_plan,
    realize_grounded_sentence_plan,
)
from emlis_ai_reply_service import render_emlis_ai_reply


_TEST_ROOT = Path(__file__).resolve().parents[1]
_BASELINE_PATH = _TEST_ROOT / "local_only" / "emlis_gate0_r0_baseline_20260711.json"
_RECEIPT_PATH = _TEST_ROOT / "fixtures" / "emlis_gate0_r8_karen_local_review_receipt_20260711.json"
_COMPARISON_PATH = _TEST_ROOT / "local_only" / "emlis_gate0_r8_local_comparison_20260711.json"
_DECISION_PATH = _TEST_ROOT / "fixtures" / "emlis_gate0_r9_decision_20260711.json"


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _reviews(payload: dict[str, Any]) -> tuple[I7KarenLocalReview, ...]:
    snapshot = str(payload["snapshot_fingerprint"])
    return tuple(
        I7KarenLocalReview(snapshot_fingerprint=snapshot, **review)
        for review in payload["reviews"]
    )


async def _generate(
    *,
    validation_evidence: Gate0ValidationEvidence,
    expected_source_snapshot_fingerprint: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    baseline = json.loads(_BASELINE_PATH.read_text(encoding="utf-8"))
    baseline_by_case = {item["case_id"]: item for item in baseline["cases"]}
    receipt = json.loads(_RECEIPT_PATH.read_text(encoding="utf-8"))
    evidence_issues = validate_gate0_validation_evidence(
        validation_evidence,
        expected_source_snapshot_fingerprint=expected_source_snapshot_fingerprint,
    )
    if evidence_issues:
        raise RuntimeError(
            "invalid_gate0_validation_evidence:" + ",".join(evidence_issues)
        )
    if str(receipt.get("snapshot_fingerprint") or "") != expected_source_snapshot_fingerprint:
        raise RuntimeError("gate0_review_source_snapshot_mismatch")
    reviews = _reviews(receipt)
    review_by_case = {item.case_id: item for item in reviews}
    cases = (
        *GROUND_OBSERVATION_I0_KNOWN_REGRESSION_CASES,
        *GROUND_OBSERVATION_I6_BLIND_CASES,
    )
    comparison_cases: list[dict[str, Any]] = []
    assessments = []
    for case in cases:
        first = await render_emlis_ai_reply(
            user_id="gate0-r8-karen-local-read",
            subscription_tier="free",
            current_input=case.as_current_input(),
        )
        second = await render_emlis_ai_reply(
            user_id="gate0-r8-karen-local-read",
            subscription_tier="free",
            current_input=case.as_current_input(),
        )
        if first.comment_text != second.comment_text:
            raise RuntimeError(f"nondeterministic_surface:{case.case_id}")
        normalized = normalize_emlis_current_input(case.as_current_input())
        spans = tuple(build_evidence_ledger(normalized))
        resolver = build_evidence_span_resolver(spans, current_input=normalized)
        plan = build_grounded_observation_plan(normalized, evidence_spans=spans)
        sentence_plan = build_grounded_sentence_plan(plan, resolver)
        surface = realize_grounded_sentence_plan(sentence_plan, plan, resolver)
        prior = baseline_by_case[case.case_id]
        prior_plan = prior["current_plan_body_free_debug"]
        prior_sentence = prior["current_sentence_plan_body_free_debug"]
        before_required = tuple(
            prior_plan["coverage_requirements"]["required_nucleus_ids"]
        )
        after_required = tuple(plan.coverage_requirements.required_nucleus_ids)
        before_relations = tuple(
            prior_plan["coverage_requirements"]["required_relation_ids"]
        )
        after_relations = tuple(plan.coverage_requirements.required_relation_ids)
        before_follow_atoms = tuple(
            atom
            for line in prior_sentence["lines"]
            for atom in line["binding"]["functional_atom_ids"]
            if atom.startswith("human_follow:")
        )
        after_follow_atoms = tuple(
            atom
            for line in sentence_plan.lines
            for atom in line.binding.functional_atom_ids
            if atom.startswith("human_follow:")
        )
        review = review_by_case[case.case_id]
        comparison_cases.append(
            {
                "case_id": case.case_id,
                "before_body": prior["current_comment_text"],
                "after_body": first.comment_text,
                "before_body_sha256": prior["current_comment_text_sha256"],
                "after_body_sha256": _sha256_text(first.comment_text),
                "normalized_current_input_sha256": prior["normalized_current_input_sha256"],
                "deterministic_rerun_match": True,
                "required_nucleus_delta": {
                    "before": list(before_required),
                    "after": list(after_required),
                    "added": [item for item in after_required if item not in before_required],
                    "removed": [item for item in before_required if item not in after_required],
                },
                "required_relation_delta": {
                    "before": list(before_relations),
                    "after": list(after_relations),
                    "added": [item for item in after_relations if item not in before_relations],
                    "removed": [item for item in before_relations if item not in after_relations],
                },
                "lexical_outcome": review.lexical_fidelity,
                "follow_atom_delta": {
                    "before": list(before_follow_atoms),
                    "after": list(after_follow_atoms),
                },
                "repetition_outcome": review.non_template_readfeel,
                "karen_verdict": review.verdict,
                "reason_refs": list(review.fatal_reason_refs),
                "current_plan_body_free_debug": plan.as_body_free_meta(),
                "current_sentence_plan_body_free_debug": sentence_plan.as_body_free_meta(),
                "current_surface_body_free_debug": surface.as_body_free_meta(),
            }
        )
        assessments.append(
            assess_i7_local_surface(
                case_id=case.case_id,
                surface_text=first.comment_text,
                grounded_meta=first.meta["grounded_observation"],
            )
        )
    comparison = {
        "schema_version": "cocolon.emlis.gate0.r8.local_comparison.bodyfull.v1",
        "artifact_scope": "local_only_body_full_not_public_meta",
        "snapshot_fingerprint": receipt["snapshot_fingerprint"],
        "case_count": len(comparison_cases),
        "subscription_tier": "free",
        "history_context_used": False,
        "deterministic_all": all(item["deterministic_rerun_match"] for item in comparison_cases),
        "cases": comparison_cases,
    }
    decision = build_gate0_local_decision(
        local_assessments=assessments,
        actual_local_reviews=reviews,
        validation_evidence=validation_evidence,
        expected_source_snapshot_fingerprint=expected_source_snapshot_fingerprint,
    )
    return comparison, decision


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validation-evidence", type=Path, required=True)
    parser.add_argument("--expected-source-snapshot", required=True)
    args = parser.parse_args()
    evidence_payload = json.loads(
        args.validation_evidence.read_text(encoding="utf-8")
    )
    validation_evidence = Gate0ValidationEvidence.from_body_free_mapping(
        evidence_payload
    )
    comparison, decision = asyncio.run(
        _generate(
            validation_evidence=validation_evidence,
            expected_source_snapshot_fingerprint=args.expected_source_snapshot,
        )
    )
    _COMPARISON_PATH.write_text(
        json.dumps(comparison, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _DECISION_PATH.write_text(
        json.dumps(decision, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
