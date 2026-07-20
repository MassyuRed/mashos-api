# -*- coding: utf-8 -*-
from __future__ import annotations

"""E2 integrated synchronization for the disconnected rc0030 lane.

E2 is GREEN only when the real forward candidate, Body-only Parser,
Independent Matcher, Hard Gate, and deterministic selector agree on the same
request-local material.  A test-only or metadata-only substitute is not an E2
success.  The frozen representative depth case is deliberately part of this
entry gate: if it cannot reach the integrated candidate chain, the test emits
one closed RED code and no production owner is changed here.
"""

from dataclasses import replace
from functools import lru_cache
import hashlib
import inspect
import json
from pathlib import Path
import re
from typing import Any, Callable

import pytest

import emlis_ai_step11_hard_gate_v3 as gate
import emlis_ai_step11_natural_surface_matcher_v3 as inverse
import emlis_ai_step11_rc0030_experiment_runtime_adapter_v3 as runtime


_TEST_ROOT = Path(__file__).resolve().parent
_CYCLE_ROOT = _TEST_ROOT / "fixtures" / "emlis_nls_v3" / "cycle_001"
_FIXTURE = _CYCLE_ROOT / "rc0030_representative8_body_free.json"
_PARENT_MANIFEST = _CYCLE_ROOT / (
    "cycle001_dependency_manifest_rc0029_surface_repair_experiment.json"
)
_BATCH = (
    _TEST_ROOT
    / "fixtures"
    / "emlis_nls_v3"
    / "generated"
    / "batch_001.jsonl"
)
_FIXTURE_SHA256 = (
    "9cfbdafaf43a3caed8b5dc00e68b56cd2b24003a002f0a7cbd1c3ec06d598fa5"
)
_CASE_IDS = (
    "nls3s_b001_0001",
    "nls3s_b001_0002",
    "nls3s_b001_0009",
    "nls3s_b001_0019",
    "nls3s_b001_0035",
    "nls3s_b001_0043",
    "nls3s_b001_0063",
    "nls3s_b001_0100",
)
_DENSITY_CASE_ID = "nls3s_b001_0063"
_SELECTED_CASE_IDS = tuple(
    case_id for case_id in _CASE_IDS if case_id != _DENSITY_CASE_ID
)
_FORBIDDEN_MATCHER_PARAMETERS = frozenset(
    {
        "candidate",
        "forward_plan",
        "surface_realization_plan",
        "candidate_ast",
        "surface_ast",
        "span_map",
        "candidate_owner_ids",
        "covered_ids",
        "selected",
        "lexical_atom_specs",
    }
)
_FORBIDDEN_PUBLIC_KEYS = frozenset(
    {
        "action_text",
        "base_body",
        "body",
        "current_input",
        "final_utf8_bytes",
        "input",
        "normalized_input",
        "output",
        "owner_expressions",
        "parsed_witness",
        "raw_text",
        "rendered_surface",
        "source_fragment",
        "supporting_expression",
        "surface_text",
        "target_expression",
        "unsalted_body_digest",
        "utf8_bytes",
    }
)


def _closed_fail(code: str) -> None:
    pytest.fail(code, pytrace=False)


def _mapping_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    if type(value) is dict:
        keys.update(value)
        for child in value.values():
            keys.update(_mapping_keys(child))
    elif type(value) in {list, tuple}:
        for child in value:
            keys.update(_mapping_keys(child))
    return keys


def _contains_bytes(value: Any) -> bool:
    if type(value) is bytes:
        return True
    if type(value) is dict:
        return any(_contains_bytes(child) for child in value.values())
    if type(value) in {list, tuple}:
        return any(_contains_bytes(child) for child in value)
    return False


@lru_cache(maxsize=1)
def _authority() -> tuple[dict[str, Any], dict[str, dict[str, Any]], str]:
    if hashlib.sha256(_FIXTURE.read_bytes()).hexdigest() != _FIXTURE_SHA256:
        _closed_fail("STEP11_RC0030_E2_FIXTURE_DRIFT")
    fixture = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    parent = json.loads(_PARENT_MANIFEST.read_text(encoding="utf-8"))
    rows = fixture.get("rows")
    closure = parent.get("source_dependency_closure_sha256")
    if (
        type(rows) is not list
        or tuple(row.get("case_id") for row in rows) != _CASE_IDS
        or type(closure) is not str
        or len(closure) != 64
    ):
        _closed_fail("STEP11_RC0030_E2_AUTHORITY_INVALID")
    samples = {
        row["case_id"]: row
        for line in _BATCH.read_text(encoding="utf-8").splitlines()
        if line
        for row in (json.loads(line),)
        if row.get("case_id") in _CASE_IDS
    }
    if set(samples) != set(_CASE_IDS):
        _closed_fail("STEP11_RC0030_E2_AUTHORITY_INVALID")
    return fixture, samples, closure


@lru_cache(maxsize=None)
def _execution(case_id: str) -> Any:
    fixture, samples, closure = _authority()
    row = next(item for item in fixture["rows"] if item["case_id"] == case_id)
    return runtime.execute_step11_rc0030_experiment_private(
        samples[case_id]["input"],
        case_id=case_id,
        source_case_commitment=row["source_case_commitment"],
        source_dependency_closure_sha256=closure,
    )


def _source_denominator(case_id: str) -> tuple[int, int]:
    fixture, _samples, _closure = _authority()
    row = next(item for item in fixture["rows"] if item["case_id"] == case_id)
    denominator = row["denominator"]
    semantic = sum(
        denominator[key]
        for key in (
            "construction_instances",
            "relations",
            "semantic_links",
            "explicit_unknowns",
        )
    )
    return semantic, denominator["receptions"]


def _selected_material(execution: Any) -> tuple[Any, Any, Any, Any]:
    selection = execution.selection_result
    candidate = selection.selected_candidate
    parsed = execution.selected_parsed_witness
    joined = execution.selected_verified_binding
    context = execution.selected_base_inverse_context
    if any(row is None for row in (candidate, parsed, joined, context)):
        _closed_fail("STEP11_RC0030_E2_SELECTED_MATERIAL_MISSING")
    return candidate, parsed, joined, context


def _source_kwargs(execution: Any, candidate: Any) -> dict[str, Any]:
    baseline = execution.base_execution
    return {
        "successor_snapshot": execution.successor_snapshot,
        "inventory_result": baseline.inventory_result,
        "content_plan": baseline.content_plan,
        "discourse_plan": candidate.base_candidate.discourse_plan,
        "current_input": baseline.projected_current_input,
    }


def _gate_kwargs(execution: Any, context: Any) -> dict[str, Any]:
    baseline = execution.base_execution
    return {
        "base_inverse_context": context,
        "successor_snapshot": execution.successor_snapshot,
        "lexical_atom_specs": execution.lexical_atom_specs,
        "inventory_result": baseline.inventory_result,
        "content_plan": baseline.content_plan,
        "current_input": baseline.projected_current_input,
    }


def _assert_inverse_rejected(call: Callable[[], Any], red_code: str) -> None:
    try:
        call()
    except inverse.Step11Rc0030ExperimentInverseSurfaceError as error:
        assert error.code == str(error)
        assert error.code.startswith("STEP11_RC0030_")
        assert "\n" not in error.code and "\r" not in error.code
        return
    except Exception:
        _closed_fail(red_code)
    _closed_fail(red_code)


def _rematch(execution: Any, witness: Any) -> Any:
    candidate, _parsed, _joined, context = _selected_material(execution)
    return inverse.match_step11_rc0030_experiment_surface(
        witness,
        base_body_witness=context.base_body_witness,
        verified_base_reuse_bindings=context.verified_base_reuse_bindings,
        **_source_kwargs(execution, candidate),
    )


def _delimiter_candidate_atom(parsed: Any) -> Any:
    rows = tuple(
        row
        for row in parsed.semantic_atoms
        if row.owner_expression_candidate_commitments
    )
    assert len(rows) == 1
    row = rows[0]
    assert row.owner_expressions == ()
    assert len(row.owner_expression_candidate_commitments) == 2
    assert row.owner_expression_candidate_commitments == tuple(
        sorted(row.owner_expression_candidate_commitments)
    )
    assert len(set(row.owner_expression_candidate_commitments)) == 2
    assert all(
        re.fullmatch(r"[0-9a-f]{64}", commitment) is not None
        for commitment in row.owner_expression_candidate_commitments
    )
    assert re.fullmatch(
        r"[0-9a-f]{64}", row.owner_expression_prefix_sha256
    ) is not None
    return row


def _delimiter_candidate_body_context(
    execution: Any,
) -> tuple[Any, Any, str, int, int, str, dict[str, Any], str, tuple[str, ...]]:
    candidate, parsed, _joined, _context = _selected_material(execution)
    atom = _delimiter_candidate_atom(parsed)
    catalog, _catalog_sha256 = inverse._step11_rc0030_inverse_catalog()
    terminal = next(
        row[0]
        for row in inverse._step11_rc0030_semantic_terminal_index(catalog)
        if row[1:] == (
            atom.semantic_family,
            atom.semantic_key,
            atom.direction,
        )
    )
    same_terminal_atoms = tuple(
        row
        for row in parsed.semantic_atoms
        if (
            row.semantic_family,
            row.semantic_key,
            row.direction,
        )
        == (atom.semantic_family, atom.semantic_key, atom.direction)
    )
    target_ordinal = next(
        index for index, row in enumerate(same_terminal_atoms) if row is atom
    )
    text = candidate.final_utf8_bytes.decode("utf-8")
    terminal_positions = tuple(
        match.start() for match in re.finditer(re.escape(terminal), text)
    )
    assert len(terminal_positions) == len(same_terminal_atoms)
    terminal_start = terminal_positions[target_ordinal]

    morphology = catalog["clause_morphology"]
    boundary_markers = (
        "\n",
        morphology["semantic_item_join"],
        morphology["clause_join"],
        morphology["grammatical_chunk_join"],
    )
    owner_start = max(
        text.rfind(marker, 0, terminal_start) + len(marker)
        for marker in boundary_markers
    )
    owner_prefix = text[owner_start:terminal_start]
    assert hashlib.sha256(owner_prefix.encode("utf-8")).hexdigest() == (
        atom.owner_expression_prefix_sha256
    )
    separator = (
        morphology["symmetric_join"]
        if atom.direction == "bidirectional"
        else morphology["source_particle"]
    )
    pieces = tuple(owner_prefix.split(separator))
    assert len(pieces) == 3
    assert all(pieces)
    return (
        candidate,
        atom,
        text,
        owner_start,
        terminal_start,
        terminal,
        catalog,
        separator,
        pieces,
    )


def _assert_selected_chain(execution: Any) -> None:
    result = execution.body_free_result
    selection = execution.selection_result
    assert result.disposition == "selected"
    assert result.selected_candidate_present is True
    assert result.closed_failure_codes == ()
    assert result.base_candidate_count == (
        result.base_inverse_rejected_candidate_count
        + len(execution.attempted_base_inverse_contexts)
    )
    assert len(execution.attempted_base_inverse_contexts) == (
        result.forward_rejected_base_candidate_count
        + result.experiment_candidate_count
    )
    assert len(execution.base_inverse_contexts) == (
        result.experiment_candidate_count
    )
    assert result.experiment_candidate_count == result.evaluated_candidate_count
    assert result.evaluated_candidate_count == len(execution.gate_results)
    assert result.hard_gate_pass_count == len(
        tuple(row for row in execution.gate_results if row.hard_pass)
    )
    assert result.hard_gate_pass_count >= 1
    assert runtime.validate_step11_rc0030_experiment_result(result) == ()
    assert runtime.validate_step11_rc0030_experiment_private_execution(execution) == ()

    candidate, parsed, joined, context = _selected_material(execution)
    assert selection.status == "selected"
    assert selection.selected_candidate_id == candidate.candidate_id
    assert execution.selected_final_utf8_bytes == candidate.final_utf8_bytes
    assert parsed is selection.selected_parsed_witness
    assert joined is selection.selected_verified_binding
    assert joined.hard_verified is True
    assert joined.issue_codes == ()
    assert joined.semantic_coverage_authorized is False

    expected_semantic, expected_reception = _source_denominator(
        execution.case_id
    )
    candidate_semantic = sum(
        len(getattr(candidate, name))
        for name in (
            "construction_atoms",
            "relation_atoms",
            "semantic_link_atoms",
            "explicit_unknown_atoms",
        )
    )
    forward_semantic = len(
        candidate.surface_realization_plan.semantic_chunk_bindings
    )
    forward_reuse = len(
        candidate.surface_realization_plan.base_body_exact_reuse_bindings
    )
    assert candidate_semantic == expected_semantic
    assert forward_semantic + forward_reuse == expected_semantic
    assert len(parsed.semantic_atoms) + forward_reuse == expected_semantic
    assert joined.semantic_binding_count == expected_semantic
    assert len(candidate.reception_bindings) == expected_reception
    assert len(parsed.reception_bindings) == expected_reception
    assert len(joined.verified_surface_binding.reception_bindings) == (
        expected_reception
    )
    assert joined.reception_binding_count == expected_reception

    reparsed = inverse.parse_step11_rc0030_experiment_surface(
        candidate.final_utf8_bytes
    )
    rebound = inverse.match_step11_rc0030_experiment_surface(
        reparsed,
        base_body_witness=context.base_body_witness,
        verified_base_reuse_bindings=context.verified_base_reuse_bindings,
        **_source_kwargs(execution, candidate),
    )
    assert reparsed == parsed
    assert rebound == joined.verified_surface_binding
    gate.step11_rc0030_experiment_gate_verified_binding_material(joined)

    planned_sources = {
        row.source_atom_id
        for row in candidate.surface_realization_plan.semantic_chunk_bindings
    } | {
        row.source_atom_id
        for row in candidate.surface_realization_plan.base_body_exact_reuse_bindings
    }
    verified_sources = {
        row.source_atom_id
        for row in joined.verified_surface_binding.semantic_bindings
    }
    assert planned_sources == verified_sources
    assert joined.semantic_binding_count == len(verified_sources)
    assert joined.exact_reuse_count == len(context.verified_base_reuse_bindings)
    assert joined.reception_binding_count == len(candidate.reception_bindings)

    direct = gate.evaluate_step11_rc0030_experiment_candidate(
        candidate,
        **_gate_kwargs(execution, context),
    )
    original = next(
        row for row in execution.gate_results if row.candidate_id == candidate.candidate_id
    )
    assert gate.step11_rc0030_experiment_gate_result_material(
        direct.gate_result
    ) == gate.step11_rc0030_experiment_gate_result_material(original)


def _assert_density_schedule(execution: Any) -> None:
    result = execution.body_free_result
    candidate, parsed, joined, _context = _selected_material(execution)
    plan = candidate.surface_realization_plan
    bindings = tuple(plan.semantic_chunk_bindings)
    assert result.base_candidate_count == 2
    assert result.base_inverse_rejected_candidate_count == 0
    assert result.base_inverse_prepass_count == 2
    assert result.forward_rejected_base_candidate_count == 1
    assert result.experiment_candidate_count == 1
    assert result.evaluated_candidate_count == 1
    assert result.final_body_parse_count == 1
    assert result.final_surface_match_count == 1
    assert result.hard_gate_pass_count == 1
    assert len(bindings) == 10
    assert len(plan.base_body_exact_reuse_bindings) == 0
    assert len(plan.structure_only_unit_ids) == 6
    assert candidate.base_candidate is execution.base_execution.natural_candidates[1]

    by_unit: dict[str, list[Any]] = {}
    for binding in bindings:
        by_unit.setdefault(binding.clause_unit_id, []).append(binding)
    assert set(by_unit) == set(plan.structure_only_unit_ids)
    assert all(1 <= len(rows) <= 2 for rows in by_unit.values())
    assert tuple(sorted(len(rows) for rows in by_unit.values())) == (
        1,
        1,
        2,
        2,
        2,
        2,
    )
    assert all(
        len({row.sentence_group_ordinal for row in rows}) == 1
        for rows in by_unit.values()
    )
    assert all(
        len({max(row.owner_sentence_group_ordinals) for row in rows}) == 1
        for rows in by_unit.values()
    )

    ready_by_unit = {
        unit_id: max(rows[0].owner_sentence_group_ordinals)
        for unit_id, rows in by_unit.items()
    }
    assigned_by_unit = {
        unit_id: rows[0].sentence_group_ordinal
        for unit_id, rows in by_unit.items()
    }
    assert all(
        assigned_by_unit[unit_id] >= ready_group
        for unit_id, ready_group in ready_by_unit.items()
    )
    assert sum(
        assigned_by_unit[unit_id] > ready_group
        for unit_id, ready_group in ready_by_unit.items()
    ) == 1
    assert tuple(
        sum(ready_group == group for ready_group in ready_by_unit.values())
        for group in range(1, 4)
    ) == (3, 1, 2)
    assert tuple(
        sum(assigned_group == group for assigned_group in assigned_by_unit.values())
        for group in range(1, 4)
    ) == (2, 2, 2)

    assert plan.maximum_observation_clauses_per_sentence == 4
    assert plan.maximum_visible_clauses_per_grammatical_sentence == 2
    assert plan.maximum_grammatical_complexity_load == 4
    assert plan.maximum_repeated_joiner_per_group == 2
    assert plan.peak_observation_clause_count == 4
    assert plan.peak_grammatical_clause_count == 2
    assert plan.peak_grammatical_complexity_load == 4
    assert plan.peak_group_repeated_joiner_count == 2
    assert all(row.visible_clause_count <= 2 for row in plan.observation_chunk_assignments)
    assert all(row.complexity_load <= 4 for row in plan.observation_chunk_assignments)

    parsed_by_id = {row.atom_id: row for row in parsed.semantic_atoms}
    parsed_by_source = {
        row.source_atom_id: parsed_by_id[row.parsed_atom_id]
        for row in joined.verified_surface_binding.semantic_bindings
    }
    assert set(parsed_by_source) == {row.source_atom_id for row in bindings}
    assert all(
        parsed_by_source[row.source_atom_id].sentence_group_ordinal
        == row.sentence_group_ordinal
        for row in bindings
    )

    deferred = next(
        row
        for row in bindings
        if row.sentence_group_ordinal > max(row.owner_sentence_group_ordinals)
    )
    deferred_parsed_id = next(
        row.parsed_atom_id
        for row in joined.verified_surface_binding.semantic_bindings
        if row.source_atom_id == deferred.source_atom_id
    )
    forged_atoms = tuple(
        replace(
            row,
            sentence_group_ordinal=max(deferred.owner_sentence_group_ordinals),
        )
        if row.atom_id == deferred_parsed_id
        else row
        for row in parsed.semantic_atoms
    )
    _assert_inverse_rejected(
        lambda: _rematch(
            execution,
            replace(parsed, semantic_atoms=forged_atoms),
        ),
        "STEP11_RC0030_E2_DEFERRED_PLACEMENT_ATTACK_ACCEPTED",
    )


def test_rc0030_e2_frozen_authority_and_retained_attack_denominator() -> None:
    fixture, _samples, _closure = _authority()
    assert fixture["body_free"] is True
    assert fixture["representative_count"] == 8
    attacks = fixture["retained_attack_contract"]
    existing = tuple(attacks["existing_rc0029_attack_ids"])
    successor = tuple(attacks["rc0030_pending_executable_attack_ids"])
    assert len(existing) == attacks["existing_rc0029_executed_mutation_count"] == 33
    assert len(successor) == attacks["rc0030_pending_executable_attack_count"] == 20
    assert len(set((*existing, *successor))) == 53

    resource = fixture["resource_contract"]
    assert resource["global_bounds"]["candidate_total_max"] == 12
    assert resource["global_bounds"]["replan_max"] == 1
    assert resource["global_bounds"]["owner_max"] == 24
    assert resource["global_bounds"]["parser_body_bytes_max"] == 1_000_000
    assert resource["parser_contract_bounds"][
        "parser_invocations_across_candidate_ceiling_max"
    ] == 24
    assert resource["parser_contract_bounds"][
        "body_byte_inspections_across_candidate_ceiling_max"
    ] == 48_000_000
    assert {
        case_id: _source_denominator(case_id)
        for case_id in (
            "nls3s_b001_0001",
            "nls3s_b001_0002",
            "nls3s_b001_0019",
            "nls3s_b001_0063",
        )
    } == {
        "nls3s_b001_0001": (1, 1),
        "nls3s_b001_0002": (0, 1),
        "nls3s_b001_0019": (3, 1),
        "nls3s_b001_0063": (10, 1),
    }


def test_rc0030_e2_forward_parser_matcher_gate_selector_are_synchronized() -> None:
    for case_id in _SELECTED_CASE_IDS:
        _assert_selected_chain(_execution(case_id))


def test_rc0030_e2_depth_compaction_reaches_the_integrated_chain() -> None:
    """E2 RED until the frozen high-density case reaches Parser and Gate."""

    execution = _execution(_DENSITY_CASE_ID)
    result = execution.body_free_result
    assert _source_denominator(_DENSITY_CASE_ID) == (10, 1)
    if result.disposition != "selected":
        assert result.disposition == "no_valid_candidate"
        assert result.base_candidate_count == 2
        assert result.base_inverse_rejected_candidate_count == 0
        assert result.base_inverse_prepass_count == 2
        assert result.forward_rejected_base_candidate_count == 1
        assert result.forward_failure_code_counts == (
            ("STEP11_RC0030_SURFACE_PLAN_DENSITY_UNSATISFIABLE", 1),
        )
        assert result.experiment_candidate_count == 1
        assert result.evaluated_candidate_count == 1
        assert result.final_body_parse_count == 1
        assert result.final_surface_match_count == 1
        assert result.hard_gate_pass_count == 0
        assert result.closed_failure_codes == (
            "STEP11_RC0030_BASE_PREFIX_COMMITMENT_MISMATCH",
        )
        assert result.gate_failure_code_counts == (
            ("STEP11_RC0030_BASE_PREFIX_COMMITMENT_MISMATCH", 1),
        )
        assert runtime.validate_step11_rc0030_experiment_result(result) == ()
        assert (
            runtime.validate_step11_rc0030_experiment_private_execution(
                execution
            )
            == ()
        )
        _closed_fail(
            "STEP11_RC0030_E2_BODY_ONLY_OWNER_EXPRESSION_NOT_SYNCHRONIZED"
        )
    _assert_selected_chain(execution)
    _assert_density_schedule(execution)


def test_rc0030_e2_delimiter_candidate_is_unique_bounded_and_body_free() -> None:
    execution = _execution(_DENSITY_CASE_ID)
    candidate, parsed, joined, _context = _selected_material(execution)
    atom = _delimiter_candidate_atom(parsed)
    binding = joined.verified_surface_binding

    assert parsed.schema_version == (
        inverse.STEP11_RC0030_EXPERIMENT_PARSED_WITNESS_SCHEMA_V2
    )
    assert len(parsed.semantic_atoms) == 10
    assert (
        len(candidate.surface_realization_plan.base_body_exact_reuse_bindings)
        == 0
    )
    assert len(binding.semantic_bindings) == 10
    assert binding.reception_binding_count == 1
    assert binding.unique_solution_count == 1
    assert 0 <= binding.owner_binding_comparison_count <= 576
    assert parsed.body_scan_pass_count == 2
    assert 0 <= parsed.decomposition_locus_count <= 38
    assert 0 <= parsed.evaluated_decomposition_count <= 76
    assert 0 <= parsed.peak_stored_decomposition_count < 2
    assert len(candidate.final_utf8_bytes) <= 1_000_000
    assert inverse._STEP11_RC0030_STORED_DECOMPOSITION_MAX == 2
    assert inverse._STEP11_RC0030_EVALUATED_DECOMPOSITION_MAX == 76
    assert inverse._STEP11_RC0030_OWNER_COMPARISON_MAX == 576
    assert inverse._STEP11_RC0030_BODY_SCAN_PASS_MAX == 2
    assert inverse._STEP11_RC0030_BODY_BYTE_MAX == 1_000_000

    material = inverse.step11_rc0030_experiment_parsed_witness_material(
        parsed
    )
    assert not (_mapping_keys(material) & _FORBIDDEN_PUBLIC_KEYS)
    assert _contains_bytes(material) is False
    serialized = json.dumps(material, ensure_ascii=False, sort_keys=True)
    assert candidate.final_utf8_bytes.decode("utf-8") not in serialized
    assert all(
        expression not in serialized
        for row in parsed.semantic_atoms
        for expression in row.owner_expressions
    )
    atom_material = next(
        row
        for row in material["semantic_atoms"]
        if row["atom_id"] == atom.atom_id
    )
    assert atom_material["owner_expression_count"] == 0
    assert atom_material["owner_expression_sha256"] == []
    assert atom_material["owner_expression_candidate_count"] == 2
    assert tuple(atom_material["owner_expression_candidate_commitments"]) == (
        atom.owner_expression_candidate_commitments
    )
    assert atom_material["owner_expression_prefix_sha256"] == (
        atom.owner_expression_prefix_sha256
    )
    assert candidate.final_utf8_bytes.decode("utf-8") not in repr(parsed)
    assert _DENSITY_CASE_ID not in inspect.getsource(inverse)


def test_rc0030_e2_owner_candidate_exact_one_solver_rejects_zero_and_two() -> None:
    execution = _execution(_DENSITY_CASE_ID)
    _candidate, parsed, _joined, _context = _selected_material(execution)
    atom = _delimiter_candidate_atom(parsed)
    commitments = atom.owner_expression_candidate_commitments

    def signature(commitment: str) -> tuple[str, str, str, str, str | None]:
        return (
            atom.semantic_family,
            atom.semantic_key,
            atom.direction,
            commitment,
            atom.owner_expression_prefix_sha256,
        )

    unique_authority = {signature(commitments[0]): ("source-unique",)}
    resolved = inverse._step11_rc0030_resolve_owner_candidate(
        semantic_family=atom.semantic_family,
        semantic_key=atom.semantic_key,
        direction=atom.direction,
        candidate_commitments=commitments,
        owner_expression_prefix_sha256=atom.owner_expression_prefix_sha256,
        source_ids_by_signature=unique_authority,
        comparison_count=17,
    )
    reversed_resolved = inverse._step11_rc0030_resolve_owner_candidate(
        semantic_family=atom.semantic_family,
        semantic_key=atom.semantic_key,
        direction=atom.direction,
        candidate_commitments=tuple(reversed(commitments)),
        owner_expression_prefix_sha256=atom.owner_expression_prefix_sha256,
        source_ids_by_signature=unique_authority,
        comparison_count=17,
    )
    assert resolved == reversed_resolved == ("source-unique", 19)

    with pytest.raises(
        inverse.Step11Rc0030ExperimentInverseSurfaceError
    ) as zero:
        inverse._step11_rc0030_resolve_owner_candidate(
            semantic_family=atom.semantic_family,
            semantic_key=atom.semantic_key,
            direction=atom.direction,
            candidate_commitments=commitments,
            owner_expression_prefix_sha256=atom.owner_expression_prefix_sha256,
            source_ids_by_signature={},
            comparison_count=0,
        )
    assert zero.value.code == "STEP11_RC0030_SEMANTIC_BINDING_UNRESOLVED"

    two_authorities = {
        signature(commitment): (f"source-{ordinal}",)
        for ordinal, commitment in enumerate(commitments, 1)
    }
    with pytest.raises(
        inverse.Step11Rc0030ExperimentInverseSurfaceError
    ) as multiple:
        inverse._step11_rc0030_resolve_owner_candidate(
            semantic_family=atom.semantic_family,
            semantic_key=atom.semantic_key,
            direction=atom.direction,
            candidate_commitments=commitments,
            owner_expression_prefix_sha256=atom.owner_expression_prefix_sha256,
            source_ids_by_signature=two_authorities,
            comparison_count=0,
        )
    assert multiple.value.code == (
        "STEP11_RC0030_OWNER_EXPRESSION_CANDIDATE_AMBIGUOUS"
    )

    forged_atom = replace(
        atom,
        owner_expression_candidate_commitments=tuple(reversed(commitments)),
    )
    assert inverse._step11_rc0030_semantic_atom_owner_state_valid(
        forged_atom
    ) is False
    forged_witness = replace(
        parsed,
        semantic_atoms=tuple(
            forged_atom if row is atom else row for row in parsed.semantic_atoms
        ),
    )
    with pytest.raises(
        inverse.Step11Rc0030ExperimentInverseSurfaceError
    ) as forged:
        inverse.step11_rc0030_experiment_parsed_witness_material(
            forged_witness
        )
    assert forged.value.code == "STEP11_RC0030_PARSED_WITNESS_ORIGIN_REQUIRED"


def test_rc0030_e2_parser_issued_owner_candidate_zero_solution_fails() -> None:
    execution = _execution(_DENSITY_CASE_ID)
    candidate, parsed, _joined, _context = _selected_material(execution)
    atom = _delimiter_candidate_atom(parsed)
    catalog, _catalog_sha256 = inverse._step11_rc0030_inverse_catalog()
    terminal = next(
        row[0]
        for row in inverse._step11_rc0030_semantic_terminal_index(catalog)
        if row[1:] == (
            atom.semantic_family,
            atom.semantic_key,
            atom.direction,
        )
    )
    same_terminal_atoms = tuple(
        row
        for row in parsed.semantic_atoms
        if (
            row.semantic_family,
            row.semantic_key,
            row.direction,
        )
        == (atom.semantic_family, atom.semantic_key, atom.direction)
    )
    target_ordinal = next(
        index for index, row in enumerate(same_terminal_atoms) if row is atom
    )
    text = candidate.final_utf8_bytes.decode("utf-8")
    terminal_positions = tuple(
        match.start() for match in re.finditer(re.escape(terminal), text)
    )
    assert len(terminal_positions) == len(same_terminal_atoms)
    position = terminal_positions[target_ordinal]
    mutated_body = (text[:position] + "異" + text[position:]).encode("utf-8")
    mutated = inverse.parse_step11_rc0030_experiment_surface(mutated_body)
    mutated_atom = _delimiter_candidate_atom(mutated)
    assert len(mutated.semantic_atoms) == 10
    assert mutated_atom.owner_expression_prefix_sha256 != (
        atom.owner_expression_prefix_sha256
    )
    with pytest.raises(
        inverse.Step11Rc0030ExperimentInverseSurfaceError
    ) as caught:
        _rematch(execution, mutated)
    assert caught.value.code == "STEP11_RC0030_SEMANTIC_BINDING_UNRESOLVED"


def test_rc0030_e2_delimiter_owner_attacks_fail_closed_within_stored_two() -> None:
    execution = _execution(_DENSITY_CASE_ID)
    (
        candidate,
        atom,
        text,
        owner_start,
        terminal_start,
        terminal,
        catalog,
        separator,
        pieces,
    ) = _delimiter_candidate_body_context(execution)

    attacked_prefixes = (
        pieces[0] + pieces[1] + separator + pieces[2],
        pieces[0] + separator + pieces[1] + pieces[2],
        separator.join(tuple(reversed(pieces))),
    )
    assert len(set(attacked_prefixes)) == 3
    for attacked_prefix in attacked_prefixes:
        attacked_body = (
            text[:owner_start] + attacked_prefix + text[terminal_start:]
        ).encode("utf-8")
        assert attacked_body != candidate.final_utf8_bytes
        _assert_inverse_rejected(
            lambda attacked_body=attacked_body: _rematch(
                execution,
                inverse.parse_step11_rc0030_experiment_surface(attacked_body),
            ),
            "STEP11_RC0030_E2_DELIMITER_OWNER_ATTACK_ACCEPTED",
        )

    swapped_direction_terminal = next(
        row[0]
        for row in inverse._step11_rc0030_semantic_terminal_index(catalog)
        if row[1] == atom.semantic_family
        and row[2] == atom.semantic_key
        and row[3] != atom.direction
    )
    direction_body = (
        text[:terminal_start]
        + swapped_direction_terminal
        + text[terminal_start + len(terminal) :]
    ).encode("utf-8")
    _assert_inverse_rejected(
        lambda: _rematch(
            execution,
            inverse.parse_step11_rc0030_experiment_surface(direction_body),
        ),
        "STEP11_RC0030_E2_DELIMITER_DIRECTION_ATTACK_ACCEPTED",
    )

    morphology = catalog["clause_morphology"]
    three_delimiter_prefix = separator.join(("甲", "乙", "丙", "丁"))
    with pytest.raises(
        inverse.Step11Rc0030ExperimentInverseSurfaceError
    ) as bounded:
        inverse._step11_rc0030_parse_owner_expression(
            three_delimiter_prefix,
            family=atom.semantic_family,
            direction=atom.direction,
            morphology=morphology,
        )
    assert bounded.value.code == "STEP11_RC0030_OWNER_EXPRESSION_AMBIGUOUS"


def test_rc0030_e2_inverse_is_body_only_and_selector_is_order_independent() -> None:
    assert tuple(
        inspect.signature(
            inverse.parse_step11_rc0030_experiment_surface
        ).parameters
    ) == ("body",)
    matcher_parameters = set(
        inspect.signature(
            inverse.match_step11_rc0030_experiment_surface
        ).parameters
    )
    assert not (matcher_parameters & _FORBIDDEN_MATCHER_PARAMETERS)
    assert "base_body" not in matcher_parameters
    assert "base_body_witness" in matcher_parameters

    execution = _execution("nls3s_b001_0019")
    assert len(execution.experiment_candidates) == 2
    reversed_selection = gate.select_step11_rc0030_experiment_candidate(
        tuple(reversed(execution.experiment_candidates)),
        base_inverse_contexts=tuple(
            reversed(execution.base_inverse_contexts)
        ),
        successor_snapshot=execution.successor_snapshot,
        lexical_atom_specs=execution.lexical_atom_specs,
        inventory_result=execution.base_execution.inventory_result,
        content_plan=execution.base_execution.content_plan,
        current_input=execution.base_execution.projected_current_input,
    )
    assert reversed_selection.status == "selected"
    assert reversed_selection.selected_candidate_id == (
        execution.selection_result.selected_candidate_id
    )
    assert reversed_selection.recovery_attempted is False
    assert reversed_selection.soft_rescue_used is False


def test_rc0030_e2_generic_metadata_coverage_and_stale_attacks_fail_gate() -> None:
    execution = _execution("nls3s_b001_0019")
    candidate, _parsed, _joined, context = _selected_material(execution)
    base_body = candidate.base_candidate.final_utf8_bytes
    generic_rendered = replace(
        candidate.rendered_surface,
        utf8_bytes=base_body,
        sha256=hashlib.sha256(base_body).hexdigest(),
    )
    attacks = (
        (
            replace(candidate, rendered_surface=generic_rendered),
            "STEP11_RC0030_FINAL_BYTES_COMMITMENT_MISMATCH",
        ),
        (
            replace(candidate, semantic_coverage_authorized=True),
            "STEP11_RC0030_SEMANTIC_COVERAGE_SELF_CLAIM",
        ),
        (
            replace(candidate, successor_snapshot_sha256="0" * 64),
            "STEP11_RC0030_CANDIDATE_SOURCE_MISMATCH",
        ),
        (
            replace(candidate, replan_count=2),
            "STEP11_RC0030_REPLAN_BOUND_EXCEEDED",
        ),
    )
    for forged, required_code in attacks:
        evaluation = gate.evaluate_step11_rc0030_experiment_candidate(
            forged,
            **_gate_kwargs(execution, context),
        )
        assert evaluation.gate_result.hard_pass is False
        assert required_code in evaluation.gate_result.failure_codes
        assert evaluation.gate_result.semantic_coverage_authorized is False


def test_rc0030_e2_retained_semantic_and_reception_attacks_fail_inverse() -> None:
    dense = _execution("nls3s_b001_0035")
    _candidate, witness, _joined, _context = _selected_material(dense)
    atoms = list(witness.semantic_atoms)
    receptions = list(witness.reception_bindings)
    assert len(atoms) >= 3
    assert len(receptions) == 1
    relation_index = next(
        index for index, row in enumerate(atoms) if row.semantic_family == "relation"
    )
    unknown_index = next(
        index
        for index, row in enumerate(atoms)
        if row.semantic_family == "explicit_unknown"
    )

    semantic_attacks: list[Any] = []
    changed = list(atoms)
    changed[relation_index] = replace(
        changed[relation_index],
        owner_expressions=tuple(reversed(changed[relation_index].owner_expressions)),
    )
    semantic_attacks.append(replace(witness, semantic_atoms=tuple(changed)))
    changed = list(atoms)
    relation = changed[relation_index]
    changed[relation_index] = replace(
        relation,
        direction=(
            "bidirectional"
            if relation.direction == "source_to_target"
            else "source_to_target"
        ),
    )
    semantic_attacks.append(replace(witness, semantic_atoms=tuple(changed)))
    semantic_attacks.append(
        replace(witness, semantic_atoms=tuple((*atoms, atoms[0])))
    )
    semantic_attacks.append(
        replace(
            witness,
            semantic_atoms=tuple(
                row for index, row in enumerate(atoms) if index != unknown_index
            ),
        )
    )

    reception = receptions[0]
    reception_attacks = (
        replace(witness, reception_bindings=()),
        replace(
            witness,
            reception_bindings=(
                replace(reception, target_expression="forged_target"),
            ),
        ),
        replace(
            witness,
            reception_bindings=(
                replace(reception, reception_act=reception.reception_act + "_forged"),
            ),
        ),
    )
    for forged in (*semantic_attacks, *reception_attacks):
        _assert_inverse_rejected(
            lambda forged=forged: _rematch(dense, forged),
            "STEP11_RC0030_E2_RETAINED_INVERSE_ATTACK_ACCEPTED",
        )

    link_execution = _execution("nls3s_b001_0009")
    _candidate, link_witness, _joined, _context = _selected_material(
        link_execution
    )
    link_atoms = list(link_witness.semantic_atoms)
    link_index = next(
        index
        for index, row in enumerate(link_atoms)
        if row.semantic_family == "semantic_link"
    )
    link = link_atoms[link_index]
    link_atoms[link_index] = replace(
        link,
        owner_expressions=tuple(reversed(link.owner_expressions)),
    )
    forged_link = replace(link_witness, semantic_atoms=tuple(link_atoms))
    _assert_inverse_rejected(
        lambda: _rematch(link_execution, forged_link),
        "STEP11_RC0030_E2_SEMANTIC_LINK_ATTACK_ACCEPTED",
    )


def test_rc0030_e2_join_cardinality_reuse_and_reception_attacks_fail_closed() -> None:
    positive = _execution("nls3s_b001_0019")
    candidate, parsed, joined, context = _selected_material(positive)
    binding = joined.verified_surface_binding
    semantic = binding.semantic_bindings[0]
    reception = binding.reception_bindings[0]
    attacks = (
        (
            replace(binding, semantic_bindings=()),
            "STEP11_RC0030_SEMANTIC_BINDING_JOIN_MISMATCH",
        ),
        (
            replace(binding, semantic_bindings=(semantic, semantic)),
            "STEP11_RC0030_SEMANTIC_BINDING_JOIN_MISMATCH",
        ),
        (
            replace(binding, reception_bindings=()),
            "STEP11_RC0030_GROUNDED_RECEPTION_BINDING_MISMATCH",
        ),
        (
            replace(
                binding,
                reception_bindings=(
                    replace(
                        reception,
                        source_reception_opportunity_id="forged",
                    ),
                ),
            ),
            "STEP11_RC0030_GROUNDED_RECEPTION_BINDING_MISMATCH",
        ),
    )
    for forged, expected in attacks:
        with pytest.raises(gate.Step11Rc0030ExperimentGateError) as caught:
            gate._step11_rc0030_forward_inverse_join(
                candidate,
                parsed,
                forged,
                verified_base_reuse_bindings=(
                    context.verified_base_reuse_bindings
                ),
            )
        assert caught.value.code == expected
        assert str(caught.value) == expected

    reuse_execution = _execution("nls3s_b001_0001")
    reuse_candidate, reuse_parsed, reuse_joined, _reuse_context = (
        _selected_material(reuse_execution)
    )
    with pytest.raises(gate.Step11Rc0030ExperimentGateError) as caught:
        gate._step11_rc0030_forward_inverse_join(
            reuse_candidate,
            reuse_parsed,
            reuse_joined.verified_surface_binding,
            verified_base_reuse_bindings=(),
        )
    assert caught.value.code == "STEP11_RC0030_BASE_REUSE_COMMITMENT_MISMATCH"

    zero = _execution("nls3s_b001_0002")
    _candidate, _parsed, zero_joined, _context = _selected_material(zero)
    zero_binding = zero_joined.verified_surface_binding
    assert zero_binding.semantic_bindings == ()
    assert len(zero_binding.reception_bindings) == 1
    for forged in (
        replace(
            zero_binding,
            reception_bindings=(),
            reception_binding_count=0,
        ),
        replace(zero_binding, semantic_coverage_authorized=True),
    ):
        with pytest.raises(
            inverse.Step11Rc0030ExperimentInverseSurfaceError
        ) as caught:
            inverse.step11_rc0030_experiment_verified_binding_material(forged)
        assert caught.value.code == "STEP11_RC0030_VERIFIED_BINDING_INVALID"


def test_rc0030_e2_resource_attempt_and_body_free_receipt_are_synchronized() -> None:
    for case_id in _SELECTED_CASE_IDS:
        execution = _execution(case_id)
        result = execution.body_free_result
        selection = execution.selection_result
        assert result.bounded_candidate_limit == 12
        assert result.bounded_replan_limit == 1
        assert result.replan_count == 0
        assert result.base_body_parse_count == len(
            execution.base_inverse_evaluations
        )
        assert result.base_reuse_match_count == len(
            execution.base_inverse_evaluations
        )
        assert result.final_body_parse_count == result.evaluated_candidate_count
        assert result.final_surface_match_count == result.evaluated_candidate_count
        assert selection.parser_invocation_count == (
            len(execution.base_inverse_contexts)
            + result.final_body_parse_count
        )
        assert selection.matcher_invocation_count == (
            len(execution.base_inverse_contexts)
            + result.final_surface_match_count
        )
        assert result.body_byte_inspection_count <= 48_000_000

        material = runtime.step11_rc0030_experiment_result_material(result)
        assert not (_mapping_keys(material) & _FORBIDDEN_PUBLIC_KEYS)
        assert _contains_bytes(material) is False
        assert material["result_sha256"] == result.result_sha256
        serialized = json.dumps(material, ensure_ascii=False, sort_keys=True)
        assert execution.selected_final_utf8_bytes.decode("utf-8") not in serialized

    kwargs = {
        "case_id": "e2-bounded-check",
        "source_case_commitment": "1" * 64,
        "source_dependency_closure_sha256": "2" * 64,
    }
    with pytest.raises(runtime.Step11Rc0030ExperimentRuntimeError) as candidate:
        runtime.run_step11_rc0030_experiment({}, candidate_limit=13, **kwargs)
    assert candidate.value.code == "STEP11_RC0030_CANDIDATE_BOUND_EXCEEDED"
    with pytest.raises(runtime.Step11Rc0030ExperimentRuntimeError) as replan:
        runtime.run_step11_rc0030_experiment({}, replan_limit=2, **kwargs)
    assert replan.value.code == "STEP11_RC0030_REPLAN_BOUND_EXCEEDED"
