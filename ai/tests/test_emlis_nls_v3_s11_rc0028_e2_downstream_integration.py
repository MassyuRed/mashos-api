# -*- coding: utf-8 -*-
from __future__ import annotations

"""E2 end-to-end closure for the disconnected rc0028 consumer chain."""

from dataclasses import replace
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from emlis_ai_evidence_ledger_service import (
    build_evidence_ledger,
    build_evidence_span_resolver,
)
from emlis_ai_grounded_lexical_role_experiment_snapshot_successor_v3 import (
    build_grounded_lexical_role_experiment_snapshot_successor,
)
from emlis_ai_observation_stage_context_v3 import build_observation_stage_context
from emlis_ai_step11_grounded_lexicalization_v3 import (
    build_step11_rc0028_experiment_lexical_atom_specs,
)
from emlis_ai_step11_hard_gate_v3 import (
    evaluate_step11_rc0028_experiment_candidate,
    select_step11_rc0028_experiment_candidates,
)
from emlis_ai_step11_natural_surface_matcher_v3 import (
    Step11Rc0028ExperimentInverseSurfaceError,
    match_step11_rc0028_experiment_surface,
    parse_step11_rc0028_experiment_surface,
)
from emlis_ai_step11_natural_surface_v3 import (
    STEP11_CANDIDATE_VERSION_ID,
    build_step11_rc0028_experiment_surface_candidates,
)
from emlis_ai_step11_runtime_adapter_v3 import execute_step11_offline_v3


_BATCH = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "emlis_nls_v3"
    / "generated"
    / "batch_001.jsonl"
)
_SOURCE_CLOSURE = (
    "1214bb6c586a0aecbb3f7d6b251613c9b05e190057aa276d5c29a045be538dc7"
)


def _sample(case_id: str) -> dict[str, object]:
    rows = tuple(
        json.loads(line)
        for line in _BATCH.read_text(encoding="utf-8").splitlines()
        if line
    )
    matches = tuple(row for row in rows if row.get("case_id") == case_id)
    assert len(matches) == 1, "RC0028_FROZEN_CASE_LOOKUP_FAILED"
    return matches[0]


def _build(case_id: str) -> SimpleNamespace:
    sample = _sample(case_id)
    base = execute_step11_offline_v3(
        sample["input"],
        candidate_version_id=STEP11_CANDIDATE_VERSION_ID,
        source_dependency_closure_sha256=_SOURCE_CLOSURE,
    )
    spans = tuple(build_evidence_ledger(base.normalized_input))
    resolver = build_evidence_span_resolver(
        spans,
        current_input=base.normalized_input,
    )
    stage = build_observation_stage_context(
        stage="normal_observation",
        original_input_bundle=base.normalized_input,
    )
    successor = build_grounded_lexical_role_experiment_snapshot_successor(
        base.grounded_plan,
        resolver,
        observation_stage_context=stage,
        original_input_bundle=base.normalized_input,
    )
    lexical_specs = build_step11_rc0028_experiment_lexical_atom_specs(
        successor
    )
    candidates = build_step11_rc0028_experiment_surface_candidates(
        base.natural_candidates,
        successor_snapshot=successor,
        lexical_atom_specs=lexical_specs,
    )
    parsed = tuple(
        parse_step11_rc0028_experiment_surface(row.final_utf8_bytes)
        for row in candidates
    )
    bindings = tuple(
        match_step11_rc0028_experiment_surface(
            row,
            successor_snapshot=successor,
        )
        for row in parsed
    )
    gates = tuple(
        evaluate_step11_rc0028_experiment_candidate(
            row,
            successor_snapshot=successor,
            lexical_atom_specs=lexical_specs,
            inventory_result=base.inventory_result,
            content_plan=base.content_plan,
            current_input=base.projected_current_input,
        )
        for row in candidates
    )
    selection = select_step11_rc0028_experiment_candidates(
        candidates,
        successor_snapshot=successor,
        lexical_atom_specs=lexical_specs,
        inventory_result=base.inventory_result,
        content_plan=base.content_plan,
        current_input=base.projected_current_input,
    )
    return SimpleNamespace(
        base=base,
        successor=successor,
        lexical_specs=lexical_specs,
        candidates=candidates,
        parsed=parsed,
        bindings=bindings,
        gates=gates,
        selection=selection,
    )


@pytest.fixture(scope="module")
def low_information() -> SimpleNamespace:
    return _build("nls3s_b001_0001")


@pytest.fixture(scope="module")
def relation_construction() -> SimpleNamespace:
    return _build("nls3s_b001_0019")


def test_rc0028_e2_forward_inverse_gate_chain_is_green(
    low_information: SimpleNamespace,
    relation_construction: SimpleNamespace,
) -> None:
    for value in (low_information, relation_construction):
        assert value.candidates
        assert all(row.hard_verified for row in value.bindings)
        assert all(row.hard_pass for row in value.gates)
        assert value.selection.status == "selected"
        assert value.selection.selected_candidate is not None
    assert len(low_information.parsed[0].explicit_unknown_atoms) == 1
    assert len(relation_construction.parsed[0].construction_atoms) == 2
    assert len(relation_construction.parsed[0].relation_atoms) == 1
    assert relation_construction.bindings[0].construction_slot_binding_count == 4
    assert relation_construction.bindings[0].relation_endpoint_binding_count == 2


def test_rc0028_e2_relation_endpoint_and_direction_attacks_fail_closed(
    relation_construction: SimpleNamespace,
) -> None:
    parsed = relation_construction.parsed[0]
    relation = parsed.relation_atoms[0]
    attacks = (
        (
            replace(
                relation,
                from_owner_ordinal=relation.to_owner_ordinal,
                to_owner_ordinal=relation.from_owner_ordinal,
            ),
            "STEP11_RC0028_RELATION_ENDPOINT_MISMATCH",
        ),
        (
            replace(
                relation,
                direction=(
                    "bidirectional"
                    if relation.direction == "source_to_target"
                    else "source_to_target"
                ),
            ),
            "STEP11_RC0028_RELATION_DIRECTION_MISMATCH",
        ),
    )
    for forged_relation, expected_code in attacks:
        forged = replace(parsed, relation_atoms=(forged_relation,))
        with pytest.raises(
            Step11Rc0028ExperimentInverseSurfaceError
        ) as captured:
            match_step11_rc0028_experiment_surface(
                forged,
                successor_snapshot=relation_construction.successor,
            )
        assert captured.value.code == expected_code


def test_rc0028_e2_construction_and_unknown_attacks_fail_closed(
    low_information: SimpleNamespace,
    relation_construction: SimpleNamespace,
) -> None:
    with pytest.raises(
        Step11Rc0028ExperimentInverseSurfaceError
    ) as construction_error:
        match_step11_rc0028_experiment_surface(
            replace(
                relation_construction.parsed[0],
                construction_atoms=relation_construction.parsed[0].construction_atoms[:1],
                structure_line_count=(
                    relation_construction.parsed[0].structure_line_count - 1
                ),
            ),
            successor_snapshot=relation_construction.successor,
        )
    assert construction_error.value.code == (
        "STEP11_RC0028_CONSTRUCTION_CARDINALITY_MISMATCH"
    )

    with pytest.raises(
        Step11Rc0028ExperimentInverseSurfaceError
    ) as unknown_error:
        match_step11_rc0028_experiment_surface(
            replace(
                low_information.parsed[0],
                explicit_unknown_atoms=(),
                structure_line_count=(
                    low_information.parsed[0].structure_line_count - 1
                ),
            ),
            successor_snapshot=low_information.successor,
        )
    assert unknown_error.value.code == "STEP11_RC0028_EXPLICIT_UNKNOWN_MISSING"


def test_rc0028_e2_generic_body_and_coverage_self_claim_do_not_pass_gate(
    relation_construction: SimpleNamespace,
) -> None:
    candidate = relation_construction.candidates[0]
    base_bytes = candidate.base_candidate.final_utf8_bytes
    generic = replace(
        candidate,
        rendered_surface=replace(
            candidate.rendered_surface,
            utf8_bytes=base_bytes,
            sha256=hashlib.sha256(base_bytes).hexdigest(),
            added_construction_line_count=0,
            added_relation_line_count=0,
            added_semantic_link_line_count=0,
            added_explicit_unknown_line_count=0,
        ),
    )
    covered = replace(candidate, semantic_coverage_authorized=True)
    for forged, required_code in (
        (generic, "STEP11_RC0028_FINAL_BYTES_COMMITMENT_MISMATCH"),
        (covered, "STEP11_RC0028_SEMANTIC_COVERAGE_SELF_CLAIM"),
    ):
        result = evaluate_step11_rc0028_experiment_candidate(
            forged,
            successor_snapshot=relation_construction.successor,
            lexical_atom_specs=relation_construction.lexical_specs,
            inventory_result=relation_construction.base.inventory_result,
            content_plan=relation_construction.base.content_plan,
            current_input=relation_construction.base.projected_current_input,
        )
        assert result.hard_pass is False
        assert required_code in result.failure_codes
