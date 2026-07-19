# -*- coding: utf-8 -*-
from __future__ import annotations

"""RED/GREEN contract for the runtime-disconnected rc0028 v2 snapshot."""

from copy import deepcopy
from dataclasses import replace
import importlib
import json

import pytest

from emlis_ai_current_input_bundle import normalize_emlis_current_input
from emlis_ai_evidence_ledger_service import (
    build_evidence_ledger,
    build_evidence_span_resolver,
)
from emlis_ai_grounded_observation_plan import build_grounded_observation_plan
from emlis_ai_observation_stage_context_v3 import build_observation_stage_context
from emlis_ai_semantic_obligation_inventory_v3 import (
    build_grounded_source_snapshot,
    build_semantic_obligation_inventory,
)


def _owner():
    try:
        return importlib.import_module(
            "emlis_ai_grounded_lexical_role_experiment_snapshot_successor_v3"
        )
    except ModuleNotFoundError:
        pytest.fail(
            "rc0028 lexical-role experiment snapshot successor is not implemented",
            pytrace=False,
        )


def _sources(current_input: dict[str, object]):
    normalized = normalize_emlis_current_input(dict(current_input))
    spans = tuple(build_evidence_ledger(normalized))
    resolver = build_evidence_span_resolver(
        spans,
        current_input=normalized,
    )
    plan = build_grounded_observation_plan(
        normalized,
        evidence_spans=spans,
    )
    stage = build_observation_stage_context(
        stage="normal_observation",
        original_input_bundle=normalized,
    )
    return normalized, plan, resolver, stage


def test_rc0028_successor_snapshot_binds_unchanged_base_and_v2_owners() -> None:
    owner = _owner()
    current_input: dict[str, object] = {
        "thought_text": "静かな方が、考えを整理しやすい。",
        "action_text": "順番を決めてから、一つ試した。",
        "emotions": [],
        "categories": [],
    }
    normalized, plan, resolver, stage = _sources(current_input)
    baseline = build_grounded_source_snapshot(
        plan,
        resolver,
        observation_stage_context=stage,
        original_input_bundle=normalized,
    )
    baseline_ledger = build_semantic_obligation_inventory(baseline).ledger

    snapshot = owner.build_grounded_lexical_role_experiment_snapshot_successor(
        plan,
        resolver,
        observation_stage_context=stage,
        original_input_bundle=normalized,
    )
    assert owner.validate_grounded_lexical_role_experiment_snapshot_successor(
        snapshot
    ) == ()
    assert snapshot.schema_version.endswith(".rc0028.experiment.v2")
    assert snapshot.base_snapshot == baseline
    assert snapshot.relation_construction_authority.experimental_only is True
    assert snapshot.lexical_role_witness.semantic_coverage_authority == "none"
    assert snapshot.semantic_coverage_authorized is False
    assert snapshot.runtime_connected is False
    assert snapshot.experimental_only is True
    assert snapshot.body_free is True
    assert build_semantic_obligation_inventory(snapshot.base_snapshot).ledger == (
        baseline_ledger
    )

    material = (
        owner.grounded_lexical_role_experiment_snapshot_successor_material(
            snapshot
        )
    )
    encoded = json.dumps(material, ensure_ascii=False, sort_keys=True)
    assert material["semantic_coverage_authorized"] is False
    assert material["runtime_connected"] is False
    assert "covered_required_nucleus_ids" not in encoded
    assert normalized["memo"] not in encoded
    assert normalized["memo_action"] not in encoded
    assert "start_index" not in encoded
    assert "end_index" not in encoded


def test_rc0028_successor_snapshot_origin_hash_and_coverage_tamper_fail_closed() -> None:
    owner = _owner()
    current_input: dict[str, object] = {
        "thought_text": "続けるか迷っている。",
        "action_text": "",
        "emotions": [],
        "categories": [],
    }
    normalized, plan, resolver, stage = _sources(current_input)
    snapshot = owner.build_grounded_lexical_role_experiment_snapshot_successor(
        plan,
        resolver,
        observation_stage_context=stage,
        original_input_bundle=normalized,
    )
    assert deepcopy(snapshot) is snapshot
    clone = replace(snapshot)
    assert "LEXICAL_ROLE_SUCCESSOR_EXPERIMENT_ORIGIN_AUTHORITY_REQUIRED" in (
        owner.validate_grounded_lexical_role_experiment_snapshot_successor(
            clone
        )
    )

    mutations = (
        (
            replace(snapshot, experiment_snapshot_sha256="0" * 64),
            "LEXICAL_ROLE_SUCCESSOR_EXPERIMENT_HASH_MISMATCH",
        ),
        (
            replace(snapshot, semantic_coverage_authorized=True),
            "LEXICAL_ROLE_SEMANTIC_COVERAGE_SELF_CLAIM_FORBIDDEN",
        ),
        (
            replace(snapshot, semantic_coverage_authorized=1),
            "LEXICAL_ROLE_SEMANTIC_COVERAGE_SELF_CLAIM_FORBIDDEN",
        ),
        (
            replace(snapshot, semantic_coverage_authorized="false"),
            "LEXICAL_ROLE_SEMANTIC_COVERAGE_SELF_CLAIM_FORBIDDEN",
        ),
        (
            replace(snapshot, runtime_connected=True),
            "LEXICAL_ROLE_SUCCESSOR_RUNTIME_CONNECTION_FORBIDDEN",
        ),
    )
    for forged, expected in mutations:
        assert expected in (
            owner.validate_grounded_lexical_role_experiment_snapshot_successor(
                forged
            )
        )


def test_rc0028_successor_snapshot_rejects_witness_or_authority_rebinding() -> None:
    owner = _owner()
    current_input: dict[str, object] = {
        "thought_text": "準備は進んだ。でも、結論はまだ決められない。",
        "action_text": "",
        "emotions": [],
        "categories": [],
    }
    normalized, plan, resolver, stage = _sources(current_input)
    snapshot = owner.build_grounded_lexical_role_experiment_snapshot_successor(
        plan,
        resolver,
        observation_stage_context=stage,
        original_input_bundle=normalized,
    )
    forged_witness = replace(
        snapshot.lexical_role_witness,
        witness_sha256="0" * 64,
    )
    forged = replace(snapshot, lexical_role_witness=forged_witness)
    assert "LEXICAL_ROLE_SUCCESSOR_EXPERIMENT_WITNESS_COMMITMENT_MISMATCH" in (
        owner.validate_grounded_lexical_role_experiment_snapshot_successor(
            forged
        )
    )

    forged_authority = replace(
        snapshot.relation_construction_authority,
        authority_sha256="0" * 64,
    )
    forged = replace(
        snapshot,
        relation_construction_authority=forged_authority,
    )
    assert "LEXICAL_ROLE_SUCCESSOR_EXPERIMENT_AUTHORITY_COMMITMENT_MISMATCH" in (
        owner.validate_grounded_lexical_role_experiment_snapshot_successor(
            forged
        )
    )

