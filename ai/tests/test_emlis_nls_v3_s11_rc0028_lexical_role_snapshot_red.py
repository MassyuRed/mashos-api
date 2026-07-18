# -*- coding: utf-8 -*-
from __future__ import annotations

"""rc0028 E1a: experiment-only snapshot propagation without Step 4 drift."""

from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path

import emlis_ai_semantic_obligation_inventory_v3 as inventory_module
from emlis_ai_evidence_ledger_service import (
    build_evidence_ledger,
    build_evidence_span_resolver,
)
from emlis_ai_grounded_lexical_role_experiment_snapshot_v3 import (
    GROUNDED_LEXICAL_ROLE_EXPERIMENT_SNAPSHOT_SCHEMA,
    build_grounded_lexical_role_experiment_snapshot,
    grounded_lexical_role_experiment_snapshot_material,
    validate_grounded_lexical_role_experiment_snapshot,
)
from emlis_ai_grounded_observation_plan import build_grounded_observation_plan
from emlis_ai_observation_stage_context_v3 import (
    build_observation_stage_context,
)
from emlis_ai_semantic_obligation_inventory_v3 import (
    build_grounded_source_snapshot,
    build_semantic_obligation_inventory,
    validate_semantic_obligation_inventory,
)


def _sources(current_input: dict[str, object]):
    spans = build_evidence_ledger(current_input)
    resolver = build_evidence_span_resolver(
        spans,
        current_input=current_input,
    )
    plan = build_grounded_observation_plan(
        current_input,
        evidence_spans=spans,
    )
    stage = build_observation_stage_context(
        stage="normal_observation",
        original_input_bundle=current_input,
    )
    return plan, resolver, stage


def test_rc0028_experiment_snapshot_binds_base_and_witness_body_free() -> None:
    current_input: dict[str, object] = {
        "thought_text": "静かな方が、考えを整理しやすい。",
        "action_text": "順番を決めてから、一つ試した。",
        "emotions": [],
        "categories": [],
    }
    plan, resolver, stage = _sources(current_input)
    baseline = build_grounded_source_snapshot(
        plan,
        resolver,
        observation_stage_context=stage,
        original_input_bundle=current_input,
    )
    baseline_result = build_semantic_obligation_inventory(baseline)

    experiment = build_grounded_lexical_role_experiment_snapshot(
        plan,
        resolver,
        observation_stage_context=stage,
        original_input_bundle=current_input,
    )

    assert validate_grounded_lexical_role_experiment_snapshot(
        experiment
    ) == ()
    assert experiment.schema_version == (
        GROUNDED_LEXICAL_ROLE_EXPERIMENT_SNAPSHOT_SCHEMA
    )
    assert experiment.experimental_only is True
    assert experiment.body_free is True
    assert experiment.base_snapshot == baseline
    assert len(experiment.base_snapshot_sha256) == 64
    assert experiment.source_lexical_role_witness_sha256 == (
        experiment.lexical_role_witness.witness_sha256
    )
    assert experiment.lexical_role_witness.facets

    # The wrapper gives the unchanged base snapshot back to the existing Step
    # 4 owner.  The resulting ledger is byte-for-byte equivalent in material
    # and never receives lexical-role fields.
    after_result = build_semantic_obligation_inventory(
        experiment.base_snapshot
    )
    assert after_result.ledger == baseline_result.ledger
    assert validate_semantic_obligation_inventory(
        after_result.ledger,
        source_snapshot=experiment.base_snapshot,
    ) == ()
    encoded_ledger = json.dumps(
        after_result.ledger,
        ensure_ascii=False,
        sort_keys=True,
    )
    assert "lexical_role" not in encoded_ledger
    assert all(
        row.facet_id not in encoded_ledger
        for row in experiment.lexical_role_witness.facets
    )

    material = grounded_lexical_role_experiment_snapshot_material(
        experiment
    )
    encoded = json.dumps(material, ensure_ascii=False, sort_keys=True)
    assert current_input["thought_text"] not in encoded
    assert current_input["action_text"] not in encoded
    assert material["experimental_only"] is True
    assert material["body_free"] is True


def test_rc0028_experiment_snapshot_origin_and_tamper_fail_closed() -> None:
    current_input: dict[str, object] = {
        "thought_text": "短い方が、読み取りやすい。",
        "action_text": "候補を比べてから、一つ選んだ。",
        "emotions": [],
        "categories": [],
    }
    plan, resolver, stage = _sources(current_input)
    experiment = build_grounded_lexical_role_experiment_snapshot(
        plan,
        resolver,
        observation_stage_context=stage,
        original_input_bundle=current_input,
    )

    assert deepcopy(experiment) is experiment
    clone_without_origin = replace(experiment)
    assert (
        "LEXICAL_ROLE_EXPERIMENT_ORIGIN_AUTHORITY_REQUIRED"
        in validate_grounded_lexical_role_experiment_snapshot(
            clone_without_origin
        )
    )

    forged_hash = replace(
        experiment,
        experiment_snapshot_sha256="0" * 64,
    )
    assert "LEXICAL_ROLE_EXPERIMENT_HASH_MISMATCH" in (
        validate_grounded_lexical_role_experiment_snapshot(forged_hash)
    )

    forged_witness = replace(
        experiment.lexical_role_witness,
        witness_sha256="0" * 64,
    )
    forged_witness_snapshot = replace(
        experiment,
        lexical_role_witness=forged_witness,
    )
    assert "LEXICAL_ROLE_EXPERIMENT_WITNESS_COMMITMENT_MISMATCH" in (
        validate_grounded_lexical_role_experiment_snapshot(
            forged_witness_snapshot
        )
    )

    forged_base = replace(
        experiment.base_snapshot,
        source_policy_sha256="0" * 64,
    )
    forged_base_snapshot = replace(
        experiment,
        base_snapshot=forged_base,
    )
    issues = validate_grounded_lexical_role_experiment_snapshot(
        forged_base_snapshot
    )
    assert "LEXICAL_ROLE_EXPERIMENT_BASE_HASH_MISMATCH" in issues
    assert "LEXICAL_ROLE_EXPERIMENT_BASE_COMMITMENTS_MISMATCH" in issues


def test_rc0028_experiment_snapshot_preserves_unresolved_reason() -> None:
    current_input: dict[str, object] = {
        "thought_text": "整ったのに、見直してから迷いが残った。",
        "action_text": "",
        "emotions": [],
        "categories": [],
    }
    plan, resolver, stage = _sources(current_input)
    experiment = build_grounded_lexical_role_experiment_snapshot(
        plan,
        resolver,
        observation_stage_context=stage,
        original_input_bundle=current_input,
    )
    witness = experiment.lexical_role_witness

    assert witness.unresolved_owner_reasons
    owner_id, reason_code = witness.unresolved_owner_reasons[0]
    assert reason_code == "LEXICAL_ROLE_AMBIGUOUS_ROLE_OVERLAP"
    assert owner_id in witness.unresolved_required_nucleus_ids
    material = grounded_lexical_role_experiment_snapshot_material(
        experiment
    )
    assert [
        owner_id,
        reason_code,
    ] in material["lexical_role_witness"]["fields"][
        "unresolved_owner_reasons"
    ]

    forged_witness = replace(
        witness,
        unresolved_owner_reasons=(
            (owner_id, "LEXICAL_ROLE_INVENTED_REASON"),
        ),
    )
    forged = replace(
        experiment,
        lexical_role_witness=forged_witness,
    )
    assert "LEXICAL_ROLE_EXPERIMENT_UNRESOLVED_REASONS_INVALID" in (
        validate_grounded_lexical_role_experiment_snapshot(forged)
    )


def test_rc0028_experiment_does_not_modify_step4_owner_or_policy() -> None:
    assert inventory_module.SOURCE_SNAPSHOT_SCHEMA == (
        "cocolon.emlis.nls_v3.grounded_source_snapshot.v1"
    )
    assert inventory_module.FROZEN_SOURCE_POLICY_SHA256 == (
        "de77b13a27e08ae3337d3ea8c11e1ba18ff24fb3f601d7639fe38c3948b8ff8c"
    )
    assert inventory_module.SOURCE_POLICY_SHA256 == (
        inventory_module.FROZEN_SOURCE_POLICY_SHA256
    )
    inventory_source = Path(inventory_module.__file__).read_text(
        encoding="utf-8"
    )
    assert "emlis_ai_grounded_lexical_role" not in inventory_source
    assert "lexical_role_witness" not in inventory_source
