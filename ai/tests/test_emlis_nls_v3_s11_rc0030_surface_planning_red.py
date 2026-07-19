# -*- coding: utf-8 -*-
from __future__ import annotations

"""P1 semantic RED for the rc0030 common Surface-planning contract.

The subject is the current rc0029 private experiment until the exact rc0030
private adapter exists.  A missing rc0030 module is therefore not the RED.
Each failing node inspects selected final bytes or an independent body-free
witness and emits one closed code without exporting source or rendered text.
"""

import ast
from functools import lru_cache
import hashlib
import importlib
import json
from pathlib import Path
import re
from typing import Any, Callable

import pytest


_TEST_ROOT = Path(__file__).resolve().parent
_REPO_ROOT = _TEST_ROOT.parents[1]
_FIXTURE_ROOT = _TEST_ROOT / "fixtures" / "emlis_nls_v3"
_CYCLE_ROOT = _FIXTURE_ROOT / "cycle_001"
_GENERATED_ROOT = _FIXTURE_ROOT / "generated"
_FIXTURE = _CYCLE_ROOT / "rc0030_representative8_body_free.json"
_RC0029_REPRESENTATIVE = (
    _CYCLE_ROOT / "rc0029_representative8_body_free.json"
)
_RC0029_MANIFEST = _CYCLE_ROOT / (
    "cycle001_dependency_manifest_rc0029_surface_repair_experiment.json"
)
_BATCH = _GENERATED_ROOT / "batch_001.jsonl"
_BATCH_MANIFEST = _GENERATED_ROOT / "batch_001_manifest.json"
_COVERAGE = _GENERATED_ROOT / "batch_001_coverage_matrix.json"
_DUPLICATES = _GENERATED_ROOT / "batch_001_duplicate_report.json"
_RC0029_MUTATION = (
    _TEST_ROOT / "test_emlis_nls_v3_s11_rc0029_surface_repair_mutation.py"
)

_FIXTURE_SHA256 = (
    "9cfbdafaf43a3caed8b5dc00e68b56cd2b24003a002f0a7cbd1c3ec06d598fa5"
)
_RC0029_REPRESENTATIVE_SHA256 = (
    "0c3fa4e078dcbb27c91989798426e8ee4c2bf7acc9424eee3488198e4f52d0fc"
)
_RC0029_MANIFEST_SHA256 = (
    "9b232da64222f83c33aaf77af2662097cb417ab177f4a1fb374e69a92cae0ad7"
)
_RC0030_ADAPTER = "emlis_ai_step11_rc0030_experiment_runtime_adapter_v3"
_RC0029_ADAPTER = "emlis_ai_step11_rc0029_experiment_runtime_adapter_v3"
_RC0030_PRIVATE_API = "execute_step11_rc0030_experiment_private"
_RC0029_PRIVATE_API = "execute_step11_rc0029_experiment_private"

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
_CONTROL_IDS = _CASE_IDS[:3]
_MAIN_CASE = "nls3s_b001_0009"
_HIGH_LOAD_CASE = "nls3s_b001_0035"
_EXPECTED_BASELINES = {
    "nls3s_b001_0001": ("PASS", "MINOR", ("PASS",)),
    "nls3s_b001_0002": ("PASS", "PASS", ("PASS",)),
    "nls3s_b001_0009": ("MINOR", "MAJOR", ("PASS", "MINOR")),
}
_EXPECTED_RED_CODES = (
    "STEP11_RC0030_MAIN_MEANING_APPENDIX_DOMINANCE",
    "STEP11_RC0030_SCHEMA_EXPOSITION",
    "STEP11_RC0030_SURFACE_DISTRIBUTION_OVERCONCENTRATED",
    "STEP11_RC0030_GROUNDED_RECEPTION_PREFIX_LIST",
    "STEP11_RC0030_CONTROL_NON_REGRESSION",
)
_EXPECTED_RETAINED_ATTACK_IDS = (
    "generic-body-replacement-retaining-forward-metadata",
    "forward-metadata-injection",
    "relation-from-to-swap",
    "relation-direction-reverse",
    "effective-relation-type-mutation",
    "inner-construction-deletion",
    "construction-slot-duplicate",
    "construction-slot-orphan",
    "construction-role-field-key-mismatch",
    "participation-owner-mutation",
    "semantic-link-endpoint-mutation",
    "semantic-link-type-mutation",
    "semantic-link-direction-mutation",
    "explicit-unknown-drop",
    "explicit-unknown-duplicate",
    "explicit-unknown-valid-other-dimension",
    "explicit-unknown-affected-owner-order-mutation",
    "natural-handle-collision",
    "valid-other-input-natural-handle-cross-swap",
    "depth-compaction-overflow",
    "generic-reception-without-antecedent",
    "reception-antecedent-owner-swap",
    "required-reception-obligation-drop",
    "required-reception-obligation-duplicate",
    "semantic-coverage-authorized-bool-true",
    "semantic-coverage-authorized-int-one",
    "semantic-coverage-authorized-string-false",
    "stale-artifact-hash",
    "valid-other-input-successor-swap",
    "catalog-token-mutation",
    "resource-bound-plus-one",
    "candidate-count-thirteen",
    "replan-count-two",
)
_EXPECTED_PENDING_ATTACK_IDS = (
    "base-body-lexical-only-reuse-credit",
    "base-body-partial-match-reuse-credit",
    "base-body-forged-covered-reuse-credit",
    "base-body-exact-atom-duplicate-reexposition",
    "chunk-wrong-owner-assignment",
    "chunk-reorder",
    "chunk-duplicate",
    "cross-group-bridge-endpoint-swap",
    "cross-group-bridge-direction-swap",
    "catalog-token-raw-quote-false-parse",
    "catalog-token-other-section-false-parse",
    "reception-support-omission",
    "reception-target-collision",
    "reception-act-swap",
    "reception-scope-borrowing",
    "sole-line-unmapped-reception-fallback",
    "control-fixture-mutation",
    "control-baseline-severity-mutation",
    "rc0030-symbol-duplicate",
    "rc0030-shadow-definition",
)
_FORBIDDEN_BODY_KEYS = frozenset(
    {
        "action_text",
        "body",
        "current_input",
        "final_utf8_bytes",
        "input",
        "memo",
        "memo_action",
        "normalized_input",
        "output",
        "parsed_witness",
        "raw_text",
        "rendered_surface",
        "source_fragment",
        "surface_text",
        "thought_text",
        "unsalted_body_digest",
        "utf8_bytes",
    }
)
_SHA256_RE = re.compile(r"[0-9a-f]{64}")


def _closed_fail(code: str) -> None:
    pytest.fail(code, pytrace=False)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if type(value) is not dict:
        _closed_fail("STEP11_RC0030_P1_AUTHORITY_TYPE_INVALID")
    return value


def _all_mapping_keys(value: Any) -> frozenset[str]:
    keys: set[str] = set()
    if type(value) is dict:
        keys.update(value)
        for child in value.values():
            keys.update(_all_mapping_keys(child))
    elif type(value) is list:
        for child in value:
            keys.update(_all_mapping_keys(child))
    return frozenset(keys)


def _mutation_attack_ids() -> tuple[str, ...]:
    tree = ast.parse(_RC0029_MUTATION.read_text(encoding="utf-8"))
    rows: list[str] = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_attack"
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and type(node.args[0].value) is str
        ):
            rows.append(node.args[0].value)
    return tuple(rows)


@lru_cache(maxsize=1)
def _authority() -> tuple[
    dict[str, Any], dict[str, dict[str, Any]], str
]:
    if _sha256(_FIXTURE) != _FIXTURE_SHA256:
        _closed_fail("STEP11_RC0030_P1_FIXTURE_COMMITMENT_MISMATCH")
    if _sha256(_RC0029_REPRESENTATIVE) != _RC0029_REPRESENTATIVE_SHA256:
        _closed_fail("STEP11_RC0030_P1_PREDECESSOR_FIXTURE_MISMATCH")
    if _sha256(_RC0029_MANIFEST) != _RC0029_MANIFEST_SHA256:
        _closed_fail("STEP11_RC0030_P1_PREDECESSOR_MANIFEST_MISMATCH")

    fixture = _load_json(_FIXTURE)
    manifest = _load_json(_RC0029_MANIFEST)
    batch_manifest = _load_json(_BATCH_MANIFEST)
    closure = manifest.get("source_dependency_closure_sha256")
    if type(closure) is not str or _SHA256_RE.fullmatch(closure) is None:
        _closed_fail("STEP11_RC0030_P1_PREDECESSOR_CLOSURE_INVALID")
    if closure != fixture["predecessor"][
        "rc0029_source_dependency_closure_sha256"
    ]:
        _closed_fail("STEP11_RC0030_P1_PREDECESSOR_CLOSURE_MISMATCH")

    rows = fixture.get("rows")
    if type(rows) is not list or len(rows) != 8:
        _closed_fail("STEP11_RC0030_P1_REPRESENTATIVE_SET_INVALID")
    if tuple(row.get("case_id") for row in rows) != _CASE_IDS:
        _closed_fail("STEP11_RC0030_P1_REPRESENTATIVE_ORDER_MISMATCH")
    commitments = {
        row.get("case_id"): row.get("source_case_commitment")
        for row in rows
    }
    expected_commitments = {
        row["case_id"]: row["case_commitment"]
        for row in batch_manifest["case_commitments"]
    }
    if any(
        commitments[case_id] != expected_commitments.get(case_id)
        for case_id in _CASE_IDS
    ):
        _closed_fail("STEP11_RC0030_P1_SOURCE_CASE_COMMITMENT_MISMATCH")
    if any(
        _SHA256_RE.fullmatch(str(row.get("base_realization_plan_sha256")))
        is None
        or row["base_realization_plan_id"].removeprefix("nls3s11real_")
        != row["base_realization_plan_sha256"][:16]
        for row in rows
    ):
        _closed_fail("STEP11_RC0030_P1_BASE_PLAN_COMMITMENT_MISMATCH")

    samples: dict[str, dict[str, Any]] = {}
    for line in _BATCH.read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        row = json.loads(line)
        if type(row) is dict and row.get("case_id") in _CASE_IDS:
            samples[row["case_id"]] = row
    if tuple(case_id for case_id in _CASE_IDS if case_id in samples) != _CASE_IDS:
        _closed_fail("STEP11_RC0030_P1_SOURCE_CASE_SET_MISMATCH")
    return fixture, samples, closure


@lru_cache(maxsize=1)
def _private_runner() -> Callable[..., Any]:
    try:
        module = importlib.import_module(_RC0030_ADAPTER)
    except ModuleNotFoundError as error:
        if error.name != _RC0030_ADAPTER:
            raise
        module = importlib.import_module(_RC0029_ADAPTER)
        api_name = _RC0029_PRIVATE_API
    else:
        api_name = _RC0030_PRIVATE_API
    runner = getattr(module, api_name, None)
    if not callable(runner):
        _closed_fail("STEP11_RC0030_P1_PRIVATE_RUNTIME_API_INVALID")
    return runner


@lru_cache(maxsize=None)
def _execution(case_id: str) -> Any:
    fixture, samples, closure = _authority()
    row = next(item for item in fixture["rows"] if item["case_id"] == case_id)
    execution = _private_runner()(
        samples[case_id]["input"],
        case_id=case_id,
        source_case_commitment=row["source_case_commitment"],
        source_dependency_closure_sha256=closure,
    )
    result = getattr(execution, "body_free_result", None)
    if (
        result is None
        or getattr(result, "disposition", None) != "selected"
        or getattr(result, "selected_candidate_present", None) is not True
    ):
        _closed_fail("STEP11_RC0030_P1_SUBJECT_NOT_SELECTED")
    body = getattr(execution, "selected_final_utf8_bytes", None)
    if type(body) is not bytes or not body:
        _closed_fail("STEP11_RC0030_P1_SELECTED_FINAL_BYTES_MISSING")
    return execution


def _selected_candidate(execution: Any) -> Any:
    selection = getattr(execution, "selection_result", None)
    candidate = getattr(selection, "selected_candidate", None)
    if candidate is None:
        _closed_fail("STEP11_RC0030_P1_SELECTED_CANDIDATE_MISSING")
    return candidate


def _surface_sections(body: bytes) -> tuple[tuple[str, ...], tuple[str, ...]]:
    try:
        text = body.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        _closed_fail("STEP11_RC0030_P1_SELECTED_UTF8_INVALID")
    if text.encode("utf-8", errors="strict") != body:
        _closed_fail("STEP11_RC0030_P1_SELECTED_UTF8_NONCANONICAL")
    prefix = "見えたこと：\n"
    separator = "\n\nEmlisから：\n"
    if not text.startswith(prefix) or text.count(separator) != 1:
        _closed_fail("STEP11_RC0030_P1_SURFACE_LAYOUT_INVALID")
    observation, reception = text[len(prefix) :].split(separator)
    observation_lines = tuple(observation.split("\n"))
    reception_lines = tuple(reception.split("\n"))
    if (
        not observation_lines
        or not reception_lines
        or any(not line for line in (*observation_lines, *reception_lines))
    ):
        _closed_fail("STEP11_RC0030_P1_SURFACE_LAYOUT_INVALID")
    return observation_lines, reception_lines


def _base_and_final_sections(
    execution: Any,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    candidate = _selected_candidate(execution)
    base = getattr(candidate, "base_candidate", None)
    base_body = getattr(base, "final_utf8_bytes", None)
    if type(base_body) is not bytes:
        _closed_fail("STEP11_RC0030_P1_BASE_SURFACE_MISSING")
    base_observation, base_reception = _surface_sections(base_body)
    final_observation, final_reception = _surface_sections(
        execution.selected_final_utf8_bytes
    )
    return (
        base_observation,
        base_reception,
        final_observation,
        final_reception,
    )


def _typed_atom_count(candidate: Any) -> int:
    fields = (
        "construction_atoms",
        "relation_atoms",
        "semantic_link_atoms",
        "explicit_unknown_atoms",
    )
    values = tuple(getattr(candidate, field, None) for field in fields)
    if any(type(value) is not tuple for value in values):
        _closed_fail("STEP11_RC0030_P1_TYPED_ATOM_SET_INVALID")
    return sum(len(value) for value in values)


def _strict_structural_tail(execution: Any) -> bool:
    candidate = _selected_candidate(execution)
    if _typed_atom_count(candidate) == 0:
        return False
    base_observation, _base_reception, final_observation, _final_reception = (
        _base_and_final_sections(execution)
    )
    return (
        len(base_observation) == len(final_observation)
        and base_observation[:-1] == final_observation[:-1]
        and final_observation[-1] != base_observation[-1]
        and final_observation[-1].startswith(base_observation[-1])
    )


def _dominance_witness_proved(execution: Any) -> bool:
    candidate = _selected_candidate(execution)
    plan = getattr(candidate, "surface_realization_plan", None)
    leading_id = getattr(plan, "base_leading_observation_unit_id", None)
    assignments = getattr(plan, "observation_chunk_assignments", None)
    structure_only_ids = getattr(plan, "structure_only_unit_ids", None)
    if (
        type(leading_id) is not str
        or not leading_id
        or type(assignments) is not tuple
        or not assignments
        or type(structure_only_ids) is not tuple
    ):
        return False
    try:
        ordered = sorted(
            assignments,
            key=lambda row: (row.sentence_group_ordinal, row.chunk_ordinal),
        )
        first_ids = tuple(ordered[0].source_unit_ids)
    except (AttributeError, TypeError):
        return False
    if leading_id not in first_ids or any(
        item in structure_only_ids for item in first_ids[: first_ids.index(leading_id)]
    ):
        return False
    binding = getattr(execution, "selected_verified_binding", None)
    return getattr(binding, "base_leading_observation_match_count", None) == 1


def _schema_postscript_present(execution: Any) -> bool:
    candidate = _selected_candidate(execution)
    final_observation, _final_reception = _surface_sections(
        execution.selected_final_utf8_bytes
    )
    observation = "\n".join(final_observation)
    handle_specs = getattr(candidate, "natural_handle_specs", None)
    handles = getattr(handle_specs, "handles", ())
    quoted_handle_count = sum(
        observation.count("「" + row.handle_text + "」")
        for row in handles
        if type(getattr(row, "handle_text", None)) is str
    )
    return (
        "そこには、" in observation
        or "、さらに、" in observation
        or (_typed_atom_count(candidate) >= 4 and quoted_handle_count >= 2)
    )


def _distribution_witness_proved(execution: Any) -> bool:
    candidate = _selected_candidate(execution)
    expected = _typed_atom_count(candidate)
    plan = getattr(candidate, "surface_realization_plan", None)
    assignments = getattr(plan, "semantic_chunk_bindings", None)
    exact_reuse = getattr(plan, "base_body_exact_reuse_bindings", None)
    if type(assignments) is not tuple or type(exact_reuse) is not tuple:
        return False
    if len(assignments) + len(exact_reuse) != expected:
        return False
    source_atom_ids: list[str] = []
    for row in assignments:
        source_atom_id = getattr(row, "source_atom_id", None)
        source_owner_ids = getattr(row, "source_owner_ids", None)
        if (
            type(source_atom_id) is not str
            or not source_atom_id
            or type(source_owner_ids) is not tuple
            or not source_owner_ids
            or type(getattr(row, "sentence_group_ordinal", None)) is not int
            or type(getattr(row, "chunk_ordinal", None)) is not int
        ):
            return False
        source_atom_ids.append(source_atom_id)
    for row in exact_reuse:
        source_atom_id = getattr(row, "source_atom_id", None)
        if type(source_atom_id) is not str or not source_atom_id:
            return False
        source_atom_ids.append(source_atom_id)
    return len(source_atom_ids) == len(set(source_atom_ids)) == expected


def _reception_prefix_list_present(execution: Any) -> bool:
    candidate = _selected_candidate(execution)
    _base_observation, base_reception, _final_observation, final_reception = (
        _base_and_final_sections(execution)
    )
    bindings = getattr(candidate, "reception_bindings", None)
    if type(bindings) is not tuple:
        _closed_fail("STEP11_RC0030_P1_RECEPTION_BINDING_SET_INVALID")
    for binding in bindings:
        ordinal = getattr(binding, "reception_line_ordinal", None)
        additional = getattr(binding, "additional_clause", None)
        if type(ordinal) is not int or not 1 <= ordinal <= len(base_reception):
            _closed_fail("STEP11_RC0030_P1_RECEPTION_BINDING_SET_INVALID")
        base_line = base_reception[ordinal - 1]
        final_line = final_reception[ordinal - 1]
        if (
            additional is False
            and final_line != base_line
            and final_line.endswith(base_line)
            and "「" in final_line[: -len(base_line)]
            and "」" in final_line[: -len(base_line)]
        ):
            return True
    return False


def _base_exact_reuse_count(execution: Any, expected: dict[str, Any]) -> int:
    candidate = _selected_candidate(execution)
    plan = getattr(candidate, "surface_realization_plan", None)
    rows = getattr(plan, "base_body_exact_reuse_bindings", None)
    if type(rows) is not tuple:
        return 0
    return sum(
        getattr(row, "source_atom_id", None)
        == expected["successor_actual_source_id"]
        and getattr(row, "base_parsed_atom_id", None)
        == expected["base_parsed_atom_id"]
        and getattr(row, "base_obligation_id", None)
        == expected["base_obligation_id"]
        and getattr(row, "match_basis", None)
        == expected["independent_match_basis"]
        for row in rows
    )


def test_rc0030_p1_authority_resource_control_and_attack_denominator_is_exact() -> None:
    fixture, _samples, _closure = _authority()
    assert fixture["body_free"] is True
    assert fixture["representative_count"] == 8
    assert not (_all_mapping_keys(fixture) & _FORBIDDEN_BODY_KEYS)
    assert tuple(fixture["five_concern_contract"]["closed_red_codes"]) == (
        _EXPECTED_RED_CODES
    )

    sources = fixture["source_fixture_commitments"]
    batch_manifest = _load_json(_BATCH_MANIFEST)
    assert sources == {
        "batch_manifest_sha256": _sha256(_BATCH_MANIFEST),
        "corpus_file_sha256": _sha256(_BATCH),
        "corpus_set_commitment": batch_manifest["corpus_set_commitment"],
        "coverage_matrix_sha256": _sha256(_COVERAGE),
        "duplicate_report_sha256": _sha256(_DUPLICATES),
    }

    for path_text, commitment in fixture["frozen_exact4_prefix"].items():
        path = _REPO_ROOT / path_text
        prefix = path.read_bytes()[: commitment["byte_count"]]
        assert len(prefix) == commitment["byte_count"]
        assert hashlib.sha256(prefix).hexdigest() == commitment["sha256"]

    controls = {row["case_id"]: row for row in fixture["rows"]}
    assert {
        case_id: (
            controls[case_id]["baseline_product_read_severity"],
            controls[case_id]["rc0029_product_read_severity"],
            tuple(controls[case_id]["rc0030_required_product_read_severity"]),
        )
        for case_id in _CONTROL_IDS
    } == _EXPECTED_BASELINES
    reason_counts = {
        reason: sum(
            reason in row["rc0029_closed_reason_codes"]
            for row in fixture["rows"]
        )
        for reason in (
            "MAIN_MEANING_OBSCURED",
            "SCHEMA_EXPOSITION",
            "OPAQUE_ORDINAL_REFERENTS",
            "SURFACE_DISTRIBUTION_OVERCONCENTRATED",
            "DEPTH_OVERSHOOT",
            "EMLIS_RECEPTION_UNBOUND",
            "GENERIC_RECEPTION",
        )
    }
    assert reason_counts == {
        "MAIN_MEANING_OBSCURED": 6,
        "SCHEMA_EXPOSITION": 5,
        "OPAQUE_ORDINAL_REFERENTS": 3,
        "SURFACE_DISTRIBUTION_OVERCONCENTRATED": 2,
        "DEPTH_OVERSHOOT": 3,
        "EMLIS_RECEPTION_UNBOUND": 5,
        "GENERIC_RECEPTION": 2,
    }

    attacks = fixture["retained_attack_contract"]
    assert tuple(attacks["existing_rc0029_attack_ids"]) == (
        _EXPECTED_RETAINED_ATTACK_IDS
    )
    assert attacks["existing_rc0029_executed_mutation_count"] == 33
    assert _mutation_attack_ids() == _EXPECTED_RETAINED_ATTACK_IDS
    assert tuple(attacks["rc0030_pending_executable_attack_ids"]) == (
        _EXPECTED_PENDING_ATTACK_IDS
    )
    assert attacks["rc0030_pending_executable_attack_count"] == 20
    assert attacks["pending_attacks_count_as_executed_at_p1"] is False

    support = fixture["support_positive_authority_reference"]
    support_path = _REPO_ROOT / support["fixture_path"]
    assert _sha256(support_path) == support["fixture_sha256"]
    support_fixture = _load_json(support_path)
    support_case_ids = {row.get("case_id") for row in support_fixture["cases"]}
    assert set(support["source_authority_case_ids"]) <= support_case_ids
    assert support["representative8_support_positive_count"] == 0
    assert support["support_positive_required_for_rc0030_mutation"] is True
    assert support["service_case_branch_authorized"] is False

    resource = fixture["resource_contract"]
    assert resource["global_bounds"]["candidate_total_max"] == 12
    assert resource["global_bounds"]["replan_max"] == 1
    assert resource["global_bounds"]["owner_max"] == 24
    assert resource["global_bounds"]["parser_body_bytes_max"] == 1_000_000
    assert resource["parser_contract_bounds"][
        "evaluated_decompositions_per_candidate_max"
    ] == 76
    assert resource["catalog_semantic_denominator"][
        "realization_alternatives_per_semantic_key_max"
    ] == 1


def test_rc0030_p1_main_meaning_dominance_is_body_only_proved() -> None:
    execution = _execution(_MAIN_CASE)
    if _strict_structural_tail(execution) or not _dominance_witness_proved(
        execution
    ):
        _closed_fail("STEP11_RC0030_MAIN_MEANING_APPENDIX_DOMINANCE")


def test_rc0030_p1_schema_free_realization_rejects_schema_postscript() -> None:
    if _schema_postscript_present(_execution(_HIGH_LOAD_CASE)):
        _closed_fail("STEP11_RC0030_SCHEMA_EXPOSITION")


def test_rc0030_p1_semantic_atoms_have_owner_connected_chunk_distribution() -> None:
    execution = _execution(_HIGH_LOAD_CASE)
    if _strict_structural_tail(execution) or not _distribution_witness_proved(
        execution
    ):
        _closed_fail("STEP11_RC0030_SURFACE_DISTRIBUTION_OVERCONCENTRATED")


def test_rc0030_p1_grounded_reception_is_predication_not_handle_prefix_list() -> None:
    if _reception_prefix_list_present(_execution(_HIGH_LOAD_CASE)):
        _closed_fail("STEP11_RC0030_GROUNDED_RECEPTION_PREFIX_LIST")


def test_rc0030_p1_controls_share_common_contract_without_regression() -> None:
    fixture, _samples, _closure = _authority()
    row_by_id = {row["case_id"]: row for row in fixture["rows"]}
    executions = {case_id: _execution(case_id) for case_id in _CONTROL_IDS}
    reuse_expected = row_by_id["nls3s_b001_0001"][
        "base_exact_reuse_expectation"
    ]
    exact_reuse_count = _base_exact_reuse_count(
        executions["nls3s_b001_0001"], reuse_expected
    )
    common_proxy_failed = any(
        _strict_structural_tail(executions[case_id])
        or _schema_postscript_present(executions[case_id])
        or _reception_prefix_list_present(executions[case_id])
        for case_id in _CONTROL_IDS
    )
    if (
        exact_reuse_count != reuse_expected["exact_match_count"]
        or common_proxy_failed
        or not _dominance_witness_proved(executions["nls3s_b001_0009"])
    ):
        _closed_fail("STEP11_RC0030_CONTROL_NON_REGRESSION")
