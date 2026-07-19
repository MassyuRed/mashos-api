# -*- coding: utf-8 -*-
from __future__ import annotations

"""E2 end-to-end closure for the disconnected rc0029 consumer chain."""

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
    evaluate_step11_rc0029_experiment_candidate,
    select_step11_rc0029_experiment_candidate,
)
from emlis_ai_step11_natural_surface_matcher_v3 import (
    Step11Rc0029ExperimentInverseSurfaceError,
    match_step11_rc0029_experiment_surface,
    parse_step11_rc0029_experiment_surface,
)
from emlis_ai_step11_natural_surface_v3 import (
    STEP11_CANDIDATE_VERSION_ID,
    build_step11_rc0029_experiment_surface_candidates,
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
    assert len(matches) == 1, "RC0029_FROZEN_CASE_LOOKUP_FAILED"
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
    candidates = build_step11_rc0029_experiment_surface_candidates(
        base.natural_candidates,
        successor_snapshot=successor,
        lexical_atom_specs=lexical_specs,
    )
    parsed = tuple(
        parse_step11_rc0029_experiment_surface(row.final_utf8_bytes)
        for row in candidates
    )
    bindings = tuple(
        match_step11_rc0029_experiment_surface(
            row,
            successor_snapshot=successor,
        )
        for row in parsed
    )
    gates = tuple(
        evaluate_step11_rc0029_experiment_candidate(
            row,
            successor_snapshot=successor,
            lexical_atom_specs=lexical_specs,
            inventory_result=base.inventory_result,
            content_plan=base.content_plan,
            current_input=base.projected_current_input,
        )
        for row in candidates
    )
    selection = select_step11_rc0029_experiment_candidate(
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


@pytest.fixture(scope="module")
def depth_compaction() -> SimpleNamespace:
    return _build("nls3s_b001_0063")


@pytest.fixture(scope="module")
def reception_only() -> SimpleNamespace:
    return _build("nls3s_b001_0002")


def test_rc0029_e2_reception_only_surface_is_body_recoverable(
    reception_only: SimpleNamespace,
) -> None:
    assert reception_only.candidates
    assert all(not row.construction_atoms for row in reception_only.parsed)
    assert all(not row.relation_atoms for row in reception_only.parsed)
    assert all(not row.semantic_link_atoms for row in reception_only.parsed)
    assert all(not row.explicit_unknown_atoms for row in reception_only.parsed)
    assert all(row.reception_bindings for row in reception_only.parsed)
    assert all(row.fused_structure_item_count == 0 for row in reception_only.parsed)
    assert all(row.fused_structure_group_count == 1 for row in reception_only.parsed)
    assert all(row.hard_verified for row in reception_only.bindings)
    assert all(row.hard_pass for row in reception_only.gates)
    assert reception_only.selection.status == "selected"


def test_rc0029_e2_forward_inverse_gate_chain_is_green(
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


def test_rc0029_e2_handles_keep_the_semantic_head_and_only_minimal_disambiguation(
    low_information: SimpleNamespace,
    relation_construction: SimpleNamespace,
) -> None:
    """A handle may disambiguate a collision, but may not expose a role dump."""

    for value in (low_information, relation_construction):
        for candidate in value.candidates:
            specs = candidate.natural_handle_specs
            assert specs.handles
            for handle in specs.handles:
                assert 1 <= len(handle.handle_text) <= 32, (
                    "STEP11_RC0029_NATURAL_HANDLE_NOT_BOUNDED"
                )
                visible_qualifiers = sum(
                    token in handle.handle_text
                    for token in handle.role_qualifier_tokens
                )
                assert visible_qualifiers <= 1, (
                    "STEP11_RC0029_NATURAL_HANDLE_SCHEMA_EXPOSITION"
                )
            text = candidate.final_utf8_bytes.decode("utf-8", errors="strict")
            assert "としてと" not in text
            assert "では「" not in text, (
                "STEP11_RC0029_ROLE_RECORD_SCHEMA_EXPOSITION"
            )


def test_rc0029_e2_depth_case_coalesces_records_into_shared_clauses(
    depth_compaction: SimpleNamespace,
) -> None:
    for candidate in depth_compaction.candidates:
        record_count = sum(
            len(getattr(candidate, name))
            for name in (
                "construction_atoms",
                "relation_atoms",
                "semantic_link_atoms",
                "explicit_unknown_atoms",
            )
        )
        assert record_count >= 4
        assert candidate.rendered_surface.fused_structure_item_count < (
            record_count
        ), "STEP11_RC0029_RECORD_PER_CLAUSE_NOT_COMPACTED"


def test_rc0029_e2_relation_endpoint_and_direction_attacks_fail_closed(
    relation_construction: SimpleNamespace,
) -> None:
    parsed = relation_construction.parsed[0]
    relation = parsed.relation_atoms[0]
    attacks = (
        (
            replace(
                relation,
                from_handle_index=relation.to_handle_index,
                to_handle_index=relation.from_handle_index,
            ),
            "STEP11_RC0029_RELATION_ENDPOINT_MISMATCH",
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
            "STEP11_RC0029_RELATION_DIRECTION_MISMATCH",
        ),
    )
    for forged_relation, expected_code in attacks:
        forged = replace(parsed, relation_atoms=(forged_relation,))
        with pytest.raises(
            Step11Rc0029ExperimentInverseSurfaceError
        ) as captured:
            match_step11_rc0029_experiment_surface(
                forged,
                successor_snapshot=relation_construction.successor,
            )
        assert captured.value.code == expected_code


def test_rc0029_e2_construction_and_unknown_attacks_fail_closed(
    low_information: SimpleNamespace,
    relation_construction: SimpleNamespace,
) -> None:
    with pytest.raises(
        Step11Rc0029ExperimentInverseSurfaceError
    ) as construction_error:
        match_step11_rc0029_experiment_surface(
                replace(
                    relation_construction.parsed[0],
                    construction_atoms=relation_construction.parsed[0].construction_atoms[:1],
                ),
            successor_snapshot=relation_construction.successor,
        )
    assert construction_error.value.code == (
        "STEP11_RC0029_CONSTRUCTION_CARDINALITY_MISMATCH"
    )

    with pytest.raises(
        Step11Rc0029ExperimentInverseSurfaceError
    ) as unknown_error:
        match_step11_rc0029_experiment_surface(
            replace(
                low_information.parsed[0],
                explicit_unknown_atoms=(),
                fused_structure_item_count=(
                    low_information.parsed[0].fused_structure_item_count - 1
                ),
            ),
            successor_snapshot=low_information.successor,
        )
    assert unknown_error.value.code == "STEP11_RC0029_EXPLICIT_UNKNOWN_MISSING"


def test_rc0029_e2_generic_body_and_coverage_self_claim_do_not_pass_gate(
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
            added_observation_line_count=0,
            fused_structure_item_count=0,
            fused_structure_group_count=0,
            reception_binding_count=0,
        ),
    )
    covered = replace(candidate, semantic_coverage_authorized=True)
    for forged, required_code in (
        (generic, "STEP11_RC0029_FINAL_BYTES_COMMITMENT_MISMATCH"),
        (covered, "STEP11_RC0029_SEMANTIC_COVERAGE_SELF_CLAIM"),
    ):
        result = evaluate_step11_rc0029_experiment_candidate(
            forged,
            successor_snapshot=relation_construction.successor,
            lexical_atom_specs=relation_construction.lexical_specs,
            inventory_result=relation_construction.base.inventory_result,
            content_plan=relation_construction.base.content_plan,
            current_input=relation_construction.base.projected_current_input,
        )
        assert result.hard_pass is False
        assert required_code in result.failure_codes
