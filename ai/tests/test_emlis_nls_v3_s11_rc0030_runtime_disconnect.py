# -*- coding: utf-8 -*-
from __future__ import annotations

"""P4 disconnected runtime contract for the bounded rc0030 experiment."""

import ast
from dataclasses import replace
from functools import lru_cache
import inspect
import json
from pathlib import Path
from typing import Any

import pytest

import emlis_ai_rc0030_surface_planning_experiment_dependency_manifest_v3 as dependency
import emlis_ai_step11_rc0030_experiment_runtime_adapter_v3 as runtime


_TEST_ROOT = Path(__file__).resolve().parent
_REPO_ROOT = _TEST_ROOT.parents[1]
_SERVICE_ROOT = _REPO_ROOT / "ai" / "services" / "ai_inference"
_TOOL_ROOT = _REPO_ROOT / "ai" / "tools"
_RUNTIME_PATH = (
    _SERVICE_ROOT / "emlis_ai_step11_rc0030_experiment_runtime_adapter_v3.py"
)
_SHARED_RUNTIME_PATH = _SERVICE_ROOT / "emlis_ai_step11_runtime_adapter_v3.py"
_REPRESENTATIVE_PATH = (
    _TEST_ROOT
    / "fixtures"
    / "emlis_nls_v3"
    / "cycle_001"
    / "rc0030_representative8_body_free.json"
)
_PARENT_MANIFEST_PATH = (
    _TEST_ROOT
    / "fixtures"
    / "emlis_nls_v3"
    / "cycle_001"
    / "cycle001_dependency_manifest_rc0029_surface_repair_experiment.json"
)
_BATCH_PATH = (
    _TEST_ROOT
    / "fixtures"
    / "emlis_nls_v3"
    / "generated"
    / "batch_001.jsonl"
)
_RUNTIME_MODULE = "emlis_ai_step11_rc0030_experiment_runtime_adapter_v3"
_PHASE_PREDECESSOR = "afcd089a872d71b07930592b068bdc3d480b8e3b"
_PARENT_CLOSURE = (
    "cd46925c6db478ac07e501acb64c45cae3a122ab0c1d834d06a83f1190cfb082"
)
_SMOKE_CASE_ID = "nls3s_b001_0001"
_REJECTED_MATCH_CASE_ID = "nls3s_b001_0002"
_CANDIDATE_LOCAL_REJECTION_CASE_ID = "nls3s_b001_0035"
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


def _imports_module(path: Path, module_name: str) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(
            alias.name == module_name for alias in node.names
        ):
            return True
        if isinstance(node, ast.ImportFrom) and node.module == module_name:
            return True
    return False


def _reuse_projection(value: Any) -> tuple[Any, ...]:
    return tuple(
        getattr(value, field, None)
        for field in (
            "source_atom_id",
            "semantic_family",
            "base_parsed_atom_id",
            "base_obligation_id",
            "match_basis",
            "base_surface_sha256",
            "source_authority_sha256",
            "independent_binding_sha256",
        )
    )


def _assert_exact_body_accounting(execution: Any) -> None:
    evaluations = execution.base_inverse_evaluations
    assert all(
        row.charged_body_scan_pass_count == 2 * row.parser_invocation_count
        and row.body_byte_inspection_count
        == row.base_body_byte_count * row.charged_body_scan_pass_count
        for row in evaluations
    )
    evaluation_bytes = sum(
        row.body_byte_inspection_count for row in evaluations
    )
    context_by_candidate_id = {
        candidate.candidate_id: context
        for candidate, context in zip(
            execution.experiment_candidates,
            execution.base_inverse_contexts,
            strict=True,
        )
    }
    selector_bytes = sum(
        row.body_byte_inspection_count for row in execution.gate_results
    )
    selector_base_bytes = sum(
        context_by_candidate_id[row.candidate_id].body_byte_inspection_count
        for row in execution.gate_results
    )
    assert execution.body_free_result.body_byte_inspection_count == (
        evaluation_bytes + selector_bytes - selector_base_bytes
    )


@lru_cache(maxsize=None)
def _case_request(case_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    representative = json.loads(_REPRESENTATIVE_PATH.read_text(encoding="utf-8"))
    parent = json.loads(_PARENT_MANIFEST_PATH.read_text(encoding="utf-8"))
    authority = next(
        row for row in representative["rows"] if row["case_id"] == case_id
    )
    samples = tuple(
        json.loads(line)
        for line in _BATCH_PATH.read_text(encoding="utf-8").splitlines()
        if line
    )
    sample = next(row for row in samples if row.get("case_id") == case_id)
    return sample["input"], {
        "case_id": case_id,
        "source_case_commitment": authority["source_case_commitment"],
        "source_dependency_closure_sha256": parent[
            "source_dependency_closure_sha256"
        ],
    }


@lru_cache(maxsize=None)
def _case_execution(case_id: str) -> Any:
    current_input, kwargs = _case_request(case_id)
    return runtime.execute_step11_rc0030_experiment_private(
        current_input,
        **kwargs,
    )


def _selected_execution() -> Any:
    return _case_execution(_SMOKE_CASE_ID)


def test_rc0030_runtime_is_disconnected_and_has_no_eager_project_imports() -> None:
    source = _RUNTIME_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(_RUNTIME_PATH))
    top_level_imports = tuple(
        node
        for node in tree.body
        if isinstance(node, (ast.Import, ast.ImportFrom))
    )
    assert all(
        isinstance(node, ast.ImportFrom) and node.module == "__future__"
        or isinstance(node, ast.Import)
        and all(alias.name in {"dataclasses", "re", "typing"} for alias in node.names)
        or isinstance(node, ast.ImportFrom)
        and node.module in {"dataclasses", "typing"}
        for node in top_level_imports
    )
    assert "Step11Rc0030ExperimentBaseInverseContext(" not in source
    assert "parse_step11_rc0030_base_body_exact_reuse" not in source
    assert "match_step11_rc0030_base_body_exact_reuse" not in source
    assert "prepare_step11_rc0030_experiment_base_inverse(" not in source
    assert (
        source.count("evaluate_step11_rc0030_experiment_base_inverse(") == 1
    )
    assert source.count("select_step11_rc0030_experiment_candidate(") == 1
    assert "nls3s_b001_" not in source
    conditional_material = tuple(
        ast.unparse(node.test if isinstance(node, (ast.If, ast.IfExp)) else node.subject)
        for node in ast.walk(tree)
        if isinstance(node, (ast.If, ast.IfExp, ast.Match))
    )
    assert all("semantic_family" not in row for row in conditional_material)
    assert not any(
        isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Name)
        and node.value.id == "current_input"
        or isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "current_input"
        for node in ast.walk(tree)
    )

    shared_source = _SHARED_RUNTIME_PATH.read_text(encoding="utf-8").lower()
    assert "rc0030" not in shared_source
    forbidden_importers = tuple(
        str(path.relative_to(_REPO_ROOT))
        for root in (_SERVICE_ROOT, _TOOL_ROOT)
        for path in root.rglob("*.py")
        if path != _RUNTIME_PATH and _imports_module(path, _RUNTIME_MODULE)
    )
    assert forbidden_importers == ()


def test_rc0030_runtime_keeps_phase_and_historical_authority_separate() -> None:
    representative = json.loads(_REPRESENTATIVE_PATH.read_text(encoding="utf-8"))
    parent = json.loads(_PARENT_MANIFEST_PATH.read_text(encoding="utf-8"))
    assert dependency.RC0030_P4_PHASE_PREDECESSOR_GIT_COMMIT == _PHASE_PREDECESSOR
    assert (
        dependency.RC0029_SURFACE_REPAIR_PARENT_SOURCE_CLOSURE_SHA256
        == _PARENT_CLOSURE
    )
    assert parent["source_dependency_closure_sha256"] == _PARENT_CLOSURE
    assert (
        representative["predecessor"][
            "rc0029_source_dependency_closure_sha256"
        ]
        == _PARENT_CLOSURE
    )


def test_rc0030_runtime_api_rejects_expanded_bounds_with_closed_codes() -> None:
    private_signature = inspect.signature(
        runtime.execute_step11_rc0030_experiment_private
    )
    public_signature = inspect.signature(runtime.run_step11_rc0030_experiment)
    assert tuple(private_signature.parameters) == tuple(public_signature.parameters)
    assert runtime.STEP11_RC0030_MAX_CANDIDATES == 12
    assert runtime.STEP11_RC0030_MAX_REPLANS == 1
    assert runtime.STEP11_RC0030_MAX_PARSER_INVOCATIONS_PER_CANDIDATE == 2
    assert runtime.STEP11_RC0030_MAX_MATCHER_INVOCATIONS_PER_CANDIDATE == 2
    assert runtime.STEP11_RC0030_MAX_PARSER_INVOCATIONS == 24
    assert runtime.STEP11_RC0030_MAX_MATCHER_INVOCATIONS == 24
    assert runtime.STEP11_RC0030_MAX_BODY_BYTE_INSPECTIONS == 48_000_000

    kwargs = {
        "case_id": "bounded-check",
        "source_case_commitment": "1" * 64,
        "source_dependency_closure_sha256": "2" * 64,
    }
    with pytest.raises(runtime.Step11Rc0030ExperimentRuntimeError) as candidate:
        runtime.run_step11_rc0030_experiment({}, candidate_limit=13, **kwargs)
    assert candidate.value.code == "STEP11_RC0030_CANDIDATE_BOUND_EXCEEDED"
    assert str(candidate.value) == candidate.value.code
    with pytest.raises(runtime.Step11Rc0030ExperimentRuntimeError) as replan:
        runtime.run_step11_rc0030_experiment({}, replan_limit=2, **kwargs)
    assert replan.value.code == "STEP11_RC0030_REPLAN_BOUND_EXCEEDED"
    assert str(replan.value) == replan.value.code


def test_rc0030_runtime_composes_candidate_local_inverse_and_gate_once() -> None:
    execution = _selected_execution()
    result = execution.body_free_result
    selection = execution.selection_result

    assert result.disposition == "selected"
    assert result.experimental_only is True
    assert result.body_free is True
    assert result.runtime_connected is False
    assert result.bounded_candidate_limit == 12
    assert result.bounded_replan_limit == 1
    assert 1 <= result.base_candidate_count <= 12
    assert result.experiment_candidate_count == result.base_candidate_count
    assert result.base_inverse_prepass_count == result.experiment_candidate_count
    assert result.evaluated_candidate_count == result.experiment_candidate_count
    assert result.base_body_parse_count == result.experiment_candidate_count
    assert result.base_reuse_match_count == result.experiment_candidate_count
    assert result.final_body_parse_count == result.evaluated_candidate_count
    assert result.final_surface_match_count == result.evaluated_candidate_count
    assert result.replan_count == 0
    assert result.body_byte_inspection_count <= 48_000_000
    _assert_exact_body_accounting(execution)
    assert runtime.validate_step11_rc0030_experiment_result(result) == ()
    assert (
        runtime.validate_step11_rc0030_experiment_private_execution(execution)
        == ()
    )

    assert selection.parser_invocation_count == (
        result.base_body_parse_count + result.final_body_parse_count
    )
    assert selection.matcher_invocation_count == (
        result.base_reuse_match_count + result.final_surface_match_count
    )
    assert selection.body_byte_inspection_count == result.body_byte_inspection_count
    assert all(row.parser_invocation_count <= 2 for row in execution.gate_results)
    assert all(row.matcher_invocation_count <= 2 for row in execution.gate_results)
    assert all(
        row.body_byte_inspection_count <= 4_000_000
        for row in execution.gate_results
    )

    for candidate, context in zip(
        execution.experiment_candidates,
        execution.base_inverse_contexts,
        strict=True,
    ):
        assert candidate.base_candidate.candidate_id == context.source_base_candidate_id
        assert context.parser_invocation_count == 1
        assert context.matcher_invocation_count == 1
        assert context.body_scan_pass_count == 2
        assert (
            context.body_byte_inspection_count
            == context.base_body_byte_count * context.body_scan_pass_count
        )
        forward_rows = candidate.surface_realization_plan.base_body_exact_reuse_bindings
        assert tuple(map(_reuse_projection, forward_rows)) == tuple(
            map(_reuse_projection, context.verified_base_reuse_bindings)
        )

    selected = selection.selected_candidate
    joined = execution.selected_verified_binding
    assert execution.selected_final_utf8_bytes == selected.final_utf8_bytes
    assert execution.selected_parsed_witness is selection.selected_parsed_witness
    assert joined is selection.selected_verified_binding
    assert joined.parsed_witness is execution.selected_parsed_witness
    assert joined.hard_verified is True
    assert joined.issue_codes == ()
    assert joined.semantic_coverage_authorized is False
    assert joined.base_leading_observation_match_count == 1


def test_rc0030_public_receipt_is_body_free_and_committed() -> None:
    execution = _selected_execution()
    result = execution.body_free_result
    material = runtime.step11_rc0030_experiment_result_material(result)

    assert _mapping_keys(material).isdisjoint(_FORBIDDEN_PUBLIC_KEYS)
    assert _contains_bytes(material) is False
    assert material["result_sha256"] == result.result_sha256
    assert material["source_dependency_closure_sha256"] == _PARENT_CLOSURE
    assert material["semantic_coverage_authority"] == "none"
    serialized = json.dumps(material, ensure_ascii=False, sort_keys=True)
    selected_text = execution.selected_final_utf8_bytes.decode("utf-8")
    assert selected_text not in serialized
    assert selected_text not in repr(execution)


def test_rc0030_matcher_rejection_keeps_exact_attempt_accounting() -> None:
    execution = _case_execution(_REJECTED_MATCH_CASE_ID)
    result = execution.body_free_result
    selection = execution.selection_result

    assert result.disposition in {"selected", "no_valid_candidate"}
    assert result.disposition != "fail_close"
    assert runtime.validate_step11_rc0030_experiment_result(result) == ()
    assert (
        runtime.validate_step11_rc0030_experiment_private_execution(execution)
        == ()
    )
    assert selection.parser_invocation_count == (
        len(execution.base_inverse_contexts) + result.final_body_parse_count
    )
    assert selection.matcher_invocation_count == (
        len(execution.base_inverse_contexts) + result.final_surface_match_count
    )
    assert result.final_body_parse_count == result.evaluated_candidate_count
    assert result.final_surface_match_count == result.evaluated_candidate_count
    assert all(row.parser_invocation_count == 2 for row in execution.gate_results)
    assert all(row.matcher_invocation_count == 2 for row in execution.gate_results)
    if result.disposition == "no_valid_candidate":
        assert result.hard_gate_pass_count == 0
        assert result.closed_failure_codes
        assert execution.selected_final_utf8_bytes is None
        assert execution.selected_parsed_witness is None
        assert execution.selected_verified_binding is None


def test_rc0030_expected_forward_rejection_is_candidate_local() -> None:
    execution = _case_execution(_CANDIDATE_LOCAL_REJECTION_CASE_ID)
    result = execution.body_free_result
    selection = execution.selection_result

    assert result.disposition == "selected"
    assert result.base_candidate_count == 2
    assert result.base_inverse_prepass_count == 2
    assert result.experiment_candidate_count == 1
    assert result.forward_rejected_base_candidate_count == 1
    assert result.forward_failure_code_counts == (
        ("STEP11_RC0030_SURFACE_PLAN_DENSITY_UNSATISFIABLE", 1),
    )
    assert result.base_body_parse_count == 2
    assert result.base_reuse_match_count == 2
    assert result.final_body_parse_count == 1
    assert result.final_surface_match_count == 1
    assert len(execution.attempted_base_inverse_contexts) == 2
    assert len(execution.base_inverse_contexts) == 1
    assert execution.base_inverse_contexts[0] in (
        execution.attempted_base_inverse_contexts
    )
    assert selection.parser_invocation_count == 2
    assert selection.matcher_invocation_count == 2
    successful_base_bytes = sum(
        row.body_byte_inspection_count
        for row in execution.base_inverse_contexts
    )
    attempted_base_bytes = sum(
        row.body_byte_inspection_count
        for row in execution.attempted_base_inverse_contexts
    )
    assert result.body_byte_inspection_count == (
        attempted_base_bytes
        + selection.body_byte_inspection_count
        - successful_base_bytes
    )
    _assert_exact_body_accounting(execution)
    assert runtime.validate_step11_rc0030_experiment_result(result) == ()
    assert (
        runtime.validate_step11_rc0030_experiment_private_execution(execution)
        == ()
    )


def test_rc0030_final_parser_rejection_preserves_exact_attempts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import emlis_ai_step11_natural_surface_matcher_v3 as inverse

    failure_code = "STEP11_RC0030_TEST_FINAL_PARSE_REJECTED"

    def reject_final_parse(_body: bytes) -> Any:
        raise inverse.Step11Rc0030ExperimentInverseSurfaceError(failure_code)

    monkeypatch.setattr(
        inverse,
        "parse_step11_rc0030_experiment_surface",
        reject_final_parse,
    )
    current_input, kwargs = _case_request(_SMOKE_CASE_ID)
    execution = runtime.execute_step11_rc0030_experiment_private(
        current_input,
        **kwargs,
    )
    result = execution.body_free_result
    selection = execution.selection_result

    assert result.disposition == "no_valid_candidate"
    assert result.evaluated_candidate_count == 1
    assert result.base_body_parse_count == 1
    assert result.base_reuse_match_count == 1
    assert result.final_surface_parse_count == 1
    assert result.final_body_parse_count == 1
    assert result.final_surface_match_count == 0
    assert result.closed_failure_codes == (failure_code,)
    assert result.gate_failure_code_counts == ((failure_code, 1),)
    assert selection.status == "rc0030_experiment_no_valid_candidate"
    assert selection.parser_invocation_count == 2
    assert selection.matcher_invocation_count == 1
    assert len(execution.gate_results) == 1
    assert execution.gate_results[0].parser_invocation_count == 2
    assert execution.gate_results[0].matcher_invocation_count == 1
    assert execution.gate_results[0].failure_codes == (failure_code,)
    assert execution.gate_results[0].hard_pass is False
    assert execution.selected_final_utf8_bytes is None
    assert execution.selected_parsed_witness is None
    assert execution.selected_verified_binding is None
    assert runtime.validate_step11_rc0030_experiment_result(result) == ()
    assert (
        runtime.validate_step11_rc0030_experiment_private_execution(execution)
        == ()
    )


def test_rc0030_first_base_parser_rejection_is_candidate_local(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import emlis_ai_step11_natural_surface_matcher_v3 as inverse

    original = inverse.parse_step11_rc0030_base_body_exact_reuse
    failure_code = "STEP11_RC0030_TEST_BASE_PARSE_REJECTED"
    call_count = 0

    def reject_first_base_parse(body: bytes) -> Any:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise inverse.Step11Rc0030ExperimentInverseSurfaceError(
                failure_code
            )
        return original(body)

    monkeypatch.setattr(
        inverse,
        "parse_step11_rc0030_base_body_exact_reuse",
        reject_first_base_parse,
    )
    current_input, kwargs = _case_request(_CANDIDATE_LOCAL_REJECTION_CASE_ID)
    execution = runtime.execute_step11_rc0030_experiment_private(
        current_input,
        **kwargs,
    )
    result = execution.body_free_result

    assert call_count == 2
    assert result.disposition == "selected"
    assert result.base_candidate_count == 2
    assert result.base_inverse_prepass_count == 2
    assert result.base_inverse_rejected_candidate_count == 1
    assert result.base_inverse_failure_code_counts == ((failure_code, 1),)
    assert result.forward_rejected_base_candidate_count == 0
    assert result.experiment_candidate_count == 1
    assert result.base_body_parse_count == 2
    assert result.base_reuse_match_count == 1
    assert result.final_surface_parse_count == 1
    assert result.final_surface_match_count == 1
    assert len(execution.base_inverse_evaluations) == 2
    assert len(execution.attempted_base_inverse_contexts) == 1
    assert len(execution.base_inverse_contexts) == 1
    _assert_exact_body_accounting(execution)
    assert result.base_candidate_count == (
        result.base_inverse_rejected_candidate_count
        + result.forward_rejected_base_candidate_count
        + result.experiment_candidate_count
    )
    assert runtime.validate_step11_rc0030_experiment_result(result) == ()
    assert (
        runtime.validate_step11_rc0030_experiment_private_execution(execution)
        == ()
    )


def test_rc0030_first_base_matcher_rejection_is_candidate_local(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import emlis_ai_step11_natural_surface_matcher_v3 as inverse

    original = inverse.match_step11_rc0030_base_body_exact_reuse
    failure_code = "STEP11_RC0030_TEST_BASE_MATCH_REJECTED"
    call_count = 0

    def reject_first_base_match(witness: Any, **kwargs: Any) -> Any:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise inverse.Step11Rc0030ExperimentInverseSurfaceError(
                failure_code
            )
        return original(witness, **kwargs)

    monkeypatch.setattr(
        inverse,
        "match_step11_rc0030_base_body_exact_reuse",
        reject_first_base_match,
    )
    current_input, kwargs = _case_request(_CANDIDATE_LOCAL_REJECTION_CASE_ID)
    execution = runtime.execute_step11_rc0030_experiment_private(
        current_input,
        **kwargs,
    )
    result = execution.body_free_result

    assert call_count == 2
    assert result.disposition == "selected"
    assert result.base_candidate_count == 2
    assert result.base_inverse_prepass_count == 2
    assert result.base_inverse_rejected_candidate_count == 1
    assert result.base_inverse_failure_code_counts == ((failure_code, 1),)
    assert result.forward_rejected_base_candidate_count == 0
    assert result.experiment_candidate_count == 1
    assert result.base_body_parse_count == 2
    assert result.base_reuse_match_count == 2
    assert result.final_surface_parse_count == 1
    assert result.final_surface_match_count == 1
    assert len(execution.base_inverse_evaluations) == 2
    assert len(execution.attempted_base_inverse_contexts) == 1
    assert len(execution.base_inverse_contexts) == 1
    _assert_exact_body_accounting(execution)
    assert runtime.validate_step11_rc0030_experiment_result(result) == ()
    assert (
        runtime.validate_step11_rc0030_experiment_private_execution(execution)
        == ()
    )


def test_rc0030_all_base_inverse_rejections_return_no_valid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import emlis_ai_step11_natural_surface_matcher_v3 as inverse

    failure_code = "STEP11_RC0030_TEST_ALL_BASE_PARSE_REJECTED"

    def reject_every_base_parse(_body: bytes) -> Any:
        raise inverse.Step11Rc0030ExperimentInverseSurfaceError(failure_code)

    monkeypatch.setattr(
        inverse,
        "parse_step11_rc0030_base_body_exact_reuse",
        reject_every_base_parse,
    )
    current_input, kwargs = _case_request(_SMOKE_CASE_ID)
    execution = runtime.execute_step11_rc0030_experiment_private(
        current_input,
        **kwargs,
    )
    result = execution.body_free_result

    assert result.disposition == "no_valid_candidate"
    assert result.base_candidate_count == 1
    assert result.base_inverse_prepass_count == 1
    assert result.base_inverse_rejected_candidate_count == 1
    assert result.base_inverse_failure_code_counts == ((failure_code, 1),)
    assert result.forward_rejected_base_candidate_count == 0
    assert result.experiment_candidate_count == 0
    assert result.evaluated_candidate_count == 0
    assert result.base_body_parse_count == 1
    assert result.base_reuse_match_count == 0
    assert result.final_surface_parse_count == 0
    assert result.final_surface_match_count == 0
    assert result.closed_failure_codes == (failure_code,)
    assert result.body_byte_inspection_count == (
        execution.base_inverse_evaluations[0].body_byte_inspection_count
    )
    assert len(execution.base_inverse_evaluations) == 1
    assert execution.attempted_base_inverse_contexts == ()
    assert execution.base_inverse_contexts == ()
    assert execution.selection_result is None
    assert execution.selected_final_utf8_bytes is None
    _assert_exact_body_accounting(execution)
    assert runtime.validate_step11_rc0030_experiment_result(result) == ()
    assert (
        runtime.validate_step11_rc0030_experiment_private_execution(execution)
        == ()
    )


def test_rc0030_pre_parser_boundary_failure_retains_original_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import emlis_ai_step11_hard_gate_v3 as gate

    failure_code = "STEP11_RC0030_BASE_INVERSE_PREPASS_FAILED"

    def unavailable_inverse_contracts() -> Any:
        raise RuntimeError("unavailable")

    monkeypatch.setattr(
        gate,
        "_step11_rc0030_inverse_contracts",
        unavailable_inverse_contracts,
    )
    current_input, kwargs = _case_request(_SMOKE_CASE_ID)
    execution = runtime.execute_step11_rc0030_experiment_private(
        current_input,
        **kwargs,
    )
    result = execution.body_free_result
    evaluation = execution.base_inverse_evaluations[0]

    assert result.disposition == "fail_close"
    assert result.closed_failure_codes == (failure_code,)
    assert result.base_inverse_prepass_count == 1
    assert result.base_inverse_rejected_candidate_count == 1
    assert result.base_inverse_failure_code_counts == ((failure_code, 1),)
    assert result.base_body_parse_count == 0
    assert result.base_reuse_match_count == 0
    assert result.final_surface_parse_count == 0
    assert result.final_surface_match_count == 0
    assert result.body_byte_inspection_count == 0
    assert evaluation.parser_invocation_count == 0
    assert evaluation.matcher_invocation_count == 0
    assert evaluation.charged_body_scan_pass_count == 0
    assert evaluation.body_byte_inspection_count == 0
    assert execution.selection_result is None
    assert runtime.validate_step11_rc0030_experiment_result(result) == ()
    assert (
        runtime.validate_step11_rc0030_experiment_private_execution(execution)
        == ()
    )


def test_rc0030_selection_aggregate_mismatch_retains_gate_attempts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import emlis_ai_step11_hard_gate_v3 as gate

    original = gate.select_step11_rc0030_experiment_candidate

    def corrupt_matcher_aggregate(*args: Any, **kwargs: Any) -> Any:
        selection = original(*args, **kwargs)
        return replace(
            selection,
            matcher_invocation_count=selection.matcher_invocation_count + 1,
        )

    monkeypatch.setattr(
        gate,
        "select_step11_rc0030_experiment_candidate",
        corrupt_matcher_aggregate,
    )
    current_input, kwargs = _case_request(_SMOKE_CASE_ID)
    execution = runtime.execute_step11_rc0030_experiment_private(
        current_input,
        **kwargs,
    )
    result = execution.body_free_result

    assert result.disposition == "fail_close"
    assert result.closed_failure_codes == (
        "STEP11_RC0030_SELECTION_COMMITMENT_MISMATCH",
    )
    assert result.evaluated_candidate_count == 1
    assert result.base_body_parse_count == 1
    assert result.base_reuse_match_count == 1
    assert result.final_surface_parse_count == 1
    assert result.final_surface_match_count == 1
    assert len(execution.gate_results) == 1
    assert execution.gate_results[0].parser_invocation_count == 2
    assert execution.gate_results[0].matcher_invocation_count == 2
    assert execution.selected_final_utf8_bytes is None
    _assert_exact_body_accounting(execution)
    assert runtime.validate_step11_rc0030_experiment_result(result) == ()
    assert (
        runtime.validate_step11_rc0030_experiment_private_execution(execution)
        == ()
    )
