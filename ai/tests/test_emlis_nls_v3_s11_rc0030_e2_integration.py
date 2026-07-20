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
        assert result.forward_rejected_base_candidate_count == 2
        assert result.experiment_candidate_count == 0
        assert result.evaluated_candidate_count == 0
        assert result.final_body_parse_count == 0
        assert result.final_surface_match_count == 0
        assert result.hard_gate_pass_count == 0
        assert result.closed_failure_codes == (
            "STEP11_RC0030_SURFACE_PLAN_DENSITY_UNSATISFIABLE",
        )
        assert runtime.validate_step11_rc0030_experiment_result(result) == ()
        assert (
            runtime.validate_step11_rc0030_experiment_private_execution(
                execution
            )
            == ()
        )
        _closed_fail("STEP11_RC0030_E2_FORWARD_DENSITY_NOT_SYNCHRONIZED")
    _assert_selected_chain(execution)


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
