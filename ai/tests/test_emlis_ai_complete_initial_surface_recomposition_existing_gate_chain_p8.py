# -*- coding: utf-8 -*-
from __future__ import annotations

"""Historical file name retained for lineage.

Current assertion owner is canonical Grounded Plan / Surface / Gate; this is
not a resurrection of the former recomposition route.
"""

import asyncio
from dataclasses import replace
import inspect
import json

from helpers.emlis_ai_grounded_observation_i0_inventory import (
    GROUND_OBSERVATION_I0_KNOWN_REGRESSION_CASES,
)
from emlis_ai_current_input_bundle import normalize_emlis_current_input
from emlis_ai_evidence_ledger_service import (
    build_evidence_ledger,
    build_evidence_span_resolver,
)
from emlis_ai_grounded_observation_gate import evaluate_grounded_observation_gate
from emlis_ai_grounded_observation_plan import build_grounded_observation_plan
from emlis_ai_grounded_sentence_surface import (
    build_grounded_sentence_plan,
    realize_grounded_sentence_plan,
)
import emlis_ai_reply_service as reply_service


def _canonical_artifacts():
    case = next(
        item for item in GROUND_OBSERVATION_I0_KNOWN_REGRESSION_CASES
        if item.case_id == "C"
    )
    current_input = normalize_emlis_current_input(case.as_current_input())
    spans = tuple(build_evidence_ledger(current_input))
    resolver = build_evidence_span_resolver(spans, current_input=current_input)
    plan = build_grounded_observation_plan(current_input, evidence_spans=spans)
    sentence_plan = build_grounded_sentence_plan(plan, resolver)
    surface = realize_grounded_sentence_plan(sentence_plan, plan, resolver)
    return case, resolver, plan, sentence_plan, surface


def test_p8_canonical_grounded_artifact_is_the_only_public_candidate() -> None:
    case, resolver, plan, sentence_plan, surface = _canonical_artifacts()
    gate = evaluate_grounded_observation_gate(
        plan=plan,
        sentence_plan=sentence_plan,
        surface_result=surface,
        resolver=resolver,
    )
    reply = asyncio.run(
        reply_service.render_emlis_ai_reply(
            user_id="p8-canonical-existing-gate-chain",
            subscription_tier="free",
            current_input=case.as_current_input(),
        )
    )

    assert gate.passed is True
    assert gate.semantic_quality_gate == "passed"
    assert reply.comment_text == surface.text
    assert reply.meta["generation_path"] == gate.generation_path
    assert reply.meta["composer_source"] == "grounded_plan_realizer"
    assert reply.meta["grounded_observation"]["public_reply_path_connected"] is True
    assert reply.comment_text not in json.dumps(reply.meta, ensure_ascii=False)


def test_p8_grounded_gate_failure_cannot_be_adopted_or_relaxed() -> None:
    _case, resolver, plan, sentence_plan, surface = _canonical_artifacts()
    rejected_surface = replace(surface, completed_semantic_template_used=True)
    gate = evaluate_grounded_observation_gate(
        plan=plan,
        sentence_plan=sentence_plan,
        surface_result=rejected_surface,
        resolver=resolver,
    )

    assert gate.passed is False
    assert gate.semantic_quality_gate == "failed"
    assert gate.anti_template_gate == "failed"
    assert "grounded_anti_template_failed" in gate.rejection_reasons
    meta = gate.as_body_free_meta()
    assert meta["public_observation_status"] == "rejected"
    assert meta["raw_input_included"] is False
    assert meta["comment_text_included"] is False
    assert rejected_surface.text not in json.dumps(meta, ensure_ascii=False)


def test_p8_legacy_recomposition_adoption_owner_remains_absent() -> None:
    source = inspect.getsource(reply_service)

    assert reply_service.__all__ == ["render_emlis_ai_reply"]
    assert "_reply_service_recomposition_existing_gate_chain_summary" not in source
    assert "_regeneration_reasons_for_retry" not in source
    assert "candidate_adopted_after_existing_gates" not in source
    assert "legacy candidate adoption" not in source
