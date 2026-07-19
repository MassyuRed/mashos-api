# -*- coding: utf-8 -*-
from __future__ import annotations

"""P5 control and S/R cardinality non-regression for rc0030.

This suite keeps typed semantic bindings (S) and required grounded Reception
bindings (R) as independent, source-exact denominators.  It uses only the
frozen body-free authority fixture; final bytes remain request-local.
"""

import ast
from dataclasses import replace
from functools import lru_cache
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

import emlis_ai_step11_hard_gate_v3 as gate
import emlis_ai_step11_natural_surface_matcher_v3 as inverse
import emlis_ai_step11_rc0030_experiment_runtime_adapter_v3 as runtime


_TEST_ROOT = Path(__file__).resolve().parent
_REPO_ROOT = _TEST_ROOT.parents[1]
_SERVICE_ROOT = _REPO_ROOT / "ai" / "services" / "ai_inference"
_FIXTURE = (
    _TEST_ROOT
    / "fixtures"
    / "emlis_nls_v3"
    / "cycle_001"
    / "rc0030_representative8_body_free.json"
)
_PARENT_MANIFEST = (
    _TEST_ROOT
    / "fixtures"
    / "emlis_nls_v3"
    / "cycle_001"
    / "cycle001_dependency_manifest_rc0029_surface_repair_experiment.json"
)
_BATCH = (
    _TEST_ROOT
    / "fixtures"
    / "emlis_nls_v3"
    / "generated"
    / "batch_001.jsonl"
)
_MATCHER_PATH = _SERVICE_ROOT / "emlis_ai_step11_natural_surface_matcher_v3.py"
_GATE_PATH = _SERVICE_ROOT / "emlis_ai_step11_hard_gate_v3.py"
_RUNTIME_PATH = (
    _SERVICE_ROOT / "emlis_ai_step11_rc0030_experiment_runtime_adapter_v3.py"
)
_FIXTURE_SHA256 = (
    "9cfbdafaf43a3caed8b5dc00e68b56cd2b24003a002f0a7cbd1c3ec06d598fa5"
)
_ZERO_SEMANTIC_CONTROL = "nls3s_b001_0002"
_POSITIVE_SEMANTIC_CONTROL = "nls3s_b001_0001"
_CONTROL_IDS = (
    "nls3s_b001_0001",
    "nls3s_b001_0002",
    "nls3s_b001_0009",
)
_SEMANTIC_FAMILIES = (
    "construction_atom_count",
    "relation_endpoint_atom_count",
    "semantic_link_atom_count",
    "explicit_unknown_atom_count",
)


def _closed_fail(code: str) -> None:
    pytest.fail(code, pytrace=False)


@lru_cache(maxsize=1)
def _authority() -> tuple[dict[str, dict[str, Any]], dict[str, Any], str]:
    if hashlib.sha256(_FIXTURE.read_bytes()).hexdigest() != _FIXTURE_SHA256:
        _closed_fail("STEP11_RC0030_P5_CONTROL_FIXTURE_DRIFT")
    fixture = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    parent = json.loads(_PARENT_MANIFEST.read_text(encoding="utf-8"))
    rows = fixture.get("rows")
    if type(rows) is not list:
        _closed_fail("STEP11_RC0030_P5_CONTROL_AUTHORITY_INVALID")
    row_by_id = {row.get("case_id"): row for row in rows}
    samples = {
        row["case_id"]: row["input"]
        for line in _BATCH.read_text(encoding="utf-8").splitlines()
        if line
        for row in (json.loads(line),)
        if row.get("case_id") in row_by_id
    }
    closure = parent.get("source_dependency_closure_sha256")
    if (
        not all(case_id in row_by_id and case_id in samples for case_id in _CONTROL_IDS)
        or type(closure) is not str
        or len(closure) != 64
    ):
        _closed_fail("STEP11_RC0030_P5_CONTROL_AUTHORITY_INVALID")
    return row_by_id, samples, closure


@lru_cache(maxsize=None)
def _execution(case_id: str) -> Any:
    rows, samples, closure = _authority()
    return runtime.execute_step11_rc0030_experiment_private(
        samples[case_id],
        case_id=case_id,
        source_case_commitment=rows[case_id]["source_case_commitment"],
        source_dependency_closure_sha256=closure,
    )


def _direct_match(execution: Any) -> tuple[tuple[Any, ...], tuple[str, ...]]:
    baseline = execution.base_execution
    bindings: list[Any] = []
    failures: list[str] = []
    for candidate, context in zip(
        execution.experiment_candidates,
        execution.base_inverse_contexts,
        strict=True,
    ):
        witness = inverse.parse_step11_rc0030_experiment_surface(
            candidate.final_utf8_bytes
        )
        assert len(witness.semantic_atoms) == 0
        assert len(witness.reception_bindings) == 1
        try:
            binding = inverse.match_step11_rc0030_experiment_surface(
                witness,
                base_body_witness=context.base_body_witness,
                successor_snapshot=execution.successor_snapshot,
                inventory_result=baseline.inventory_result,
                content_plan=baseline.content_plan,
                discourse_plan=candidate.base_candidate.discourse_plan,
                current_input=baseline.projected_current_input,
                verified_base_reuse_bindings=(
                    context.verified_base_reuse_bindings
                ),
            )
        except inverse.Step11Rc0030ExperimentInverseSurfaceError as error:
            failures.append(error.code)
        else:
            bindings.append(binding)
    return tuple(bindings), tuple(failures)


def _assert_join_rejected(
    candidate: Any,
    parsed_witness: Any,
    binding: Any,
    reuse: tuple[Any, ...],
    expected_code: str,
) -> None:
    with pytest.raises(gate.Step11Rc0030ExperimentGateError) as caught:
        gate._step11_rc0030_forward_inverse_join(
            candidate,
            parsed_witness,
            binding,
            verified_base_reuse_bindings=reuse,
        )
    assert caught.value.code == expected_code
    assert str(caught.value) == expected_code


def test_rc0030_p5_zero_semantic_grounded_reception_full_chain() -> None:
    """RED first: 0002 must become S=0/R=1 selected without an exception."""

    execution = _execution(_ZERO_SEMANTIC_CONTROL)
    result = execution.body_free_result
    assert result.owner_binding_count == 4
    assert sum(getattr(result, name) for name in _SEMANTIC_FAMILIES) == 0
    assert result.experiment_candidate_count == 1
    assert result.evaluated_candidate_count == 1
    assert result.final_body_parse_count == 1
    assert result.final_surface_match_count == 1
    assert tuple(
        (
            len(candidate.surface_realization_plan.semantic_chunk_bindings),
            len(candidate.surface_realization_plan.base_body_exact_reuse_bindings),
            len(candidate.reception_bindings),
        )
        for candidate in execution.experiment_candidates
    ) == ((0, 0, 1),)

    bindings, direct_failures = _direct_match(execution)
    if result.disposition != "selected":
        assert result.disposition == "no_valid_candidate"
        assert result.hard_gate_pass_count == 0
        assert result.rejected_candidate_count == 1
        assert execution.selected_final_utf8_bytes is None
        assert execution.selected_verified_binding is None
        if direct_failures:
            assert bindings == ()
            assert direct_failures == (
                "STEP11_RC0030_VERIFIED_BINDING_INVALID",
            )
            assert result.closed_failure_codes == (
                "STEP11_RC0030_VERIFIED_BINDING_INVALID",
            )
            assert result.gate_failure_code_counts == (
                ("STEP11_RC0030_VERIFIED_BINDING_INVALID", 1),
            )
            _closed_fail(
                "STEP11_RC0030_P5_MATCHER_ZERO_SEMANTIC_CARDINALITY_RED"
            )
        assert len(bindings) == 1
        assert result.closed_failure_codes == (
            "STEP11_RC0030_GATE_BINDING_INVALID",
        )
        _closed_fail("STEP11_RC0030_P5_GATE_ZERO_SEMANTIC_CARDINALITY_RED")

    assert direct_failures == ()
    assert len(bindings) == 1
    binding = bindings[0]
    assert binding.semantic_bindings == ()
    assert len(binding.reception_bindings) == binding.reception_binding_count == 1
    assert binding.semantic_coverage_authorized is False
    assert binding.issue_codes == ()
    assert binding.hard_verified is True
    assert execution.selected_verified_binding.semantic_binding_count == 0
    assert execution.selected_verified_binding.exact_reuse_count == 0
    assert execution.selected_verified_binding.reception_binding_count == 1
    assert runtime.validate_step11_rc0030_experiment_result(result) == ()
    assert runtime.validate_step11_rc0030_experiment_private_execution(execution) == ()

    for case_id in _CONTROL_IDS:
        control = _execution(case_id)
        assert control.body_free_result.disposition == "selected"
        assert control.selected_verified_binding is not None
        source_count = sum(
            getattr(control.body_free_result, name) for name in _SEMANTIC_FAMILIES
        )
        assert control.selected_verified_binding.semantic_binding_count == source_count
        assert control.selected_verified_binding.reception_binding_count == len(
            control.selection_result.selected_candidate.reception_bindings
        )


def test_rc0030_p5_general_cardinality_attacks_fail_closed() -> None:
    execution = _execution(_POSITIVE_SEMANTIC_CONTROL)
    joined = execution.selected_verified_binding
    assert joined is not None
    candidate = execution.selection_result.selected_candidate
    context = execution.selected_base_inverse_context
    parsed = joined.parsed_witness
    binding = joined.verified_surface_binding
    semantic = binding.semantic_bindings[0]
    reception = binding.reception_bindings[0]

    _assert_join_rejected(
        candidate,
        parsed,
        replace(binding, semantic_bindings=()),
        context.verified_base_reuse_bindings,
        "STEP11_RC0030_SEMANTIC_BINDING_JOIN_MISMATCH",
    )
    _assert_join_rejected(
        candidate,
        parsed,
        replace(binding, semantic_bindings=(semantic, semantic)),
        context.verified_base_reuse_bindings,
        "STEP11_RC0030_SEMANTIC_BINDING_JOIN_MISMATCH",
    )
    for attacked_receptions in (
        (),
        (replace(reception, source_reception_opportunity_id="forged"),),
        (replace(reception, reception_act=reception.reception_act + "_forged"),),
        (replace(reception, target_owner_count=reception.target_owner_count + 1),),
    ):
        _assert_join_rejected(
            candidate,
            parsed,
            replace(binding, reception_bindings=attacked_receptions),
            context.verified_base_reuse_bindings,
            "STEP11_RC0030_GROUNDED_RECEPTION_BINDING_MISMATCH",
        )

    for attacked in (
        replace(binding, semantic_bindings=(), reception_bindings=(), reception_binding_count=0),
        replace(binding, semantic_coverage_authorized=True),
    ):
        with pytest.raises(
            inverse.Step11Rc0030ExperimentInverseSurfaceError
        ) as caught:
            inverse.step11_rc0030_experiment_verified_binding_material(attacked)
        assert caught.value.code == "STEP11_RC0030_VERIFIED_BINDING_INVALID"

    forged_gate_binding = replace(joined)
    with pytest.raises(gate.Step11Rc0030ExperimentGateError) as caught:
        gate.step11_rc0030_experiment_gate_verified_binding_material(
            forged_gate_binding
        )
    assert caught.value.code == "STEP11_RC0030_GATE_BINDING_ORIGIN_REQUIRED"


def test_rc0030_p5_cardinality_repair_has_no_case_or_runtime_branch() -> None:
    for path in (_MATCHER_PATH, _GATE_PATH, _RUNTIME_PATH):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        literals = {
            node.value
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and type(node.value) is str
        }
        assert not any("nls3s_b001_" in row for row in literals)
        assert _ZERO_SEMANTIC_CONTROL not in source
        assert "control_id" not in source
        assert "zero_semantic_control" not in source

    runtime_source = _RUNTIME_PATH.read_text(encoding="utf-8")
    runtime_tree = ast.parse(runtime_source, filename=str(_RUNTIME_PATH))
    conditional_material = tuple(
        ast.unparse(
            node.test
            if isinstance(node, (ast.If, ast.IfExp))
            else node.subject
        )
        for node in ast.walk(runtime_tree)
        if isinstance(node, (ast.If, ast.IfExp, ast.Match))
    )
    assert all("semantic_family" not in row for row in conditional_material)
