# -*- coding: utf-8 -*-
from __future__ import annotations

"""P1 exact-seven semantic RED for the rc0031 Proposition Surface.

Until the disconnected rc0031 adapter exists, the subject is the immutable
rc0030 experiment.  A missing rc0031 module is not a RED.  Every semantic
node executes selected final bytes and checks a visible Surface property;
source, rendered text, and parsed spans are never written to test output.
"""

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
_FIXTURE = _CYCLE_ROOT / "rc0031_representative8_body_free.json"
_RC0030_REPRESENTATIVE = _CYCLE_ROOT / "rc0030_representative8_body_free.json"
_RC0030_MANIFEST = _CYCLE_ROOT / (
    "cycle001_dependency_manifest_rc0030_surface_planning_experiment.json"
)
_BATCH = _GENERATED_ROOT / "batch_001.jsonl"
_BATCH_MANIFEST = _GENERATED_ROOT / "batch_001_manifest.json"
_COVERAGE = _GENERATED_ROOT / "batch_001_coverage_matrix.json"
_DUPLICATES = _GENERATED_ROOT / "batch_001_duplicate_report.json"

_FIXTURE_SHA256 = (
    "15e8047cd95b453fba4a7a677b428955ea2819e6738e4e1fc1488d24952b78a8"
)
_RC0030_REPRESENTATIVE_SHA256 = (
    "9cfbdafaf43a3caed8b5dc00e68b56cd2b24003a002f0a7cbd1c3ec06d598fa5"
)
_RC0030_MANIFEST_SHA256 = (
    "06327f7e0e6d63923bbdf836aa5d25744a83eeb8f8a704aa23c89a3ca057857b"
)
_RC0031_ADAPTER = "emlis_ai_step11_rc0031_experiment_runtime_adapter_v3"
_RC0030_ADAPTER = "emlis_ai_step11_rc0030_experiment_runtime_adapter_v3"
_RC0031_PRIVATE_API = "execute_step11_rc0031_experiment_private"
_RC0030_PRIVATE_API = "execute_step11_rc0030_experiment_private"

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
_MAIN_CASE_IDS = _CASE_IDS[2:]
_RELATION_CASE_IDS = (
    "nls3s_b001_0009",
    "nls3s_b001_0019",
    "nls3s_b001_0035",
    "nls3s_b001_0043",
)
_DISTRIBUTION_CASE_IDS = (
    "nls3s_b001_0035",
    "nls3s_b001_0063",
    "nls3s_b001_0100",
)
_RECEPTION_FAILURE_CASE_IDS = (
    "nls3s_b001_0001",
    "nls3s_b001_0009",
    "nls3s_b001_0019",
    "nls3s_b001_0035",
    "nls3s_b001_0043",
    "nls3s_b001_0063",
    "nls3s_b001_0100",
)
_EXPECTED_RED_CODES = (
    "STEP11_RC0031_SOURCE_ROOT_DOMINANCE_NOT_PROVED",
    "STEP11_RC0031_SCHEMA_FREE_PROPOSITION_NOT_PROVED",
    "STEP11_RC0031_RELATION_PROPOSITION_NOT_PROVED",
    "STEP11_RC0031_DISTRIBUTION_DEPTH_NOT_PROVED",
    "STEP11_RC0031_GROUNDED_RECEPTION_PREDICATION_NOT_PROVED",
    "STEP11_RC0031_CONTROL_RETAINED_NON_REGRESSION_NOT_PROVED",
)
_EXPECTED_EXACT18 = (
    "ai/services/ai_inference/emlis_ai_rc0031_proposition_surface_experiment_dependency_manifest_v3.py",
    "ai/services/ai_inference/emlis_ai_step11_rc0031_experiment_runtime_adapter_v3.py",
    "ai/services/ai_inference/emlis_ai_step11_rc0031_experiment_surface_catalog_v3.py",
    "ai/tools/emlis_nls_v3_rc0031_proposition_surface_dependency_manifest.py",
    "ai/tools/emlis_nls_v3_rc0031_proposition_surface_bounded_experiment.py",
    "ai/tests/fixtures/emlis_nls_v3/cycle_001/cycle001_dependency_manifest_rc0031_proposition_surface_experiment.json",
    "ai/tests/fixtures/emlis_nls_v3/cycle_001/rc0031_representative8_body_free.json",
    "ai/tests/test_emlis_nls_v3_s11_rc0031_proposition_surface_red.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0031_proposition_surface_mutation.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0031_e2_integration.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0031_forward_inverse_independence.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0031_runtime_disconnect.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0031_predecessor_immutability.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0031_predecessor_behavior_regression.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0031_control_non_regression.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0031_e3_representative8.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0031_e4_frozen100_read_only.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0031_dependency_closure.py",
)
_EXPECTED_P1_ACTIVE = frozenset(_EXPECTED_EXACT18[6:8])
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
        "parsed_span",
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
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_CLOSED_CODE_RE = re.compile(r"^STEP11_RC0031_[A-Z0-9_]{2,127}$")


def _closed_fail(code: str) -> None:
    pytest.fail(code, pytrace=False)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        _closed_fail("STEP11_RC0031_P1_AUTHORITY_UNAVAILABLE")
    if type(value) is not dict:
        _closed_fail("STEP11_RC0031_P1_AUTHORITY_TYPE_INVALID")
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


@lru_cache(maxsize=1)
def _authority() -> tuple[
    dict[str, Any], dict[str, dict[str, Any]], str
]:
    if _sha256(_FIXTURE) != _FIXTURE_SHA256:
        _closed_fail("STEP11_RC0031_P1_FIXTURE_COMMITMENT_MISMATCH")
    if _sha256(_RC0030_REPRESENTATIVE) != _RC0030_REPRESENTATIVE_SHA256:
        _closed_fail("STEP11_RC0031_P1_PREDECESSOR_FIXTURE_MISMATCH")
    if _sha256(_RC0030_MANIFEST) != _RC0030_MANIFEST_SHA256:
        _closed_fail("STEP11_RC0031_P1_PREDECESSOR_MANIFEST_MISMATCH")

    fixture = _load_json(_FIXTURE)
    manifest = _load_json(_RC0030_MANIFEST)
    batch_manifest = _load_json(_BATCH_MANIFEST)
    closure = manifest.get("source_dependency_closure_sha256")
    if (
        type(closure) is not str
        or _SHA256_RE.fullmatch(closure) is None
        or closure
        != fixture["predecessor"][
            "rc0030_source_dependency_closure_sha256"
        ]
    ):
        _closed_fail("STEP11_RC0031_P1_PREDECESSOR_CLOSURE_MISMATCH")

    rows = fixture.get("rows")
    if (
        type(rows) is not list
        or len(rows) != 8
        or tuple(row.get("case_id") for row in rows) != _CASE_IDS
    ):
        _closed_fail("STEP11_RC0031_P1_REPRESENTATIVE_SET_INVALID")
    expected_commitments = {
        row["case_id"]: row["case_commitment"]
        for row in batch_manifest["case_commitments"]
    }
    if any(
        row.get("source_case_commitment")
        != expected_commitments.get(row.get("case_id"))
        for row in rows
    ):
        _closed_fail("STEP11_RC0031_P1_SOURCE_CASE_COMMITMENT_MISMATCH")

    samples: dict[str, dict[str, Any]] = {}
    try:
        lines = _BATCH.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        _closed_fail("STEP11_RC0031_P1_SOURCE_FIXTURE_UNAVAILABLE")
    for line in lines:
        if not line:
            continue
        row = json.loads(line)
        if type(row) is dict and row.get("case_id") in _CASE_IDS:
            samples[row["case_id"]] = row
    if tuple(case_id for case_id in _CASE_IDS if case_id in samples) != _CASE_IDS:
        _closed_fail("STEP11_RC0031_P1_SOURCE_CASE_SET_MISMATCH")
    return fixture, samples, closure


@lru_cache(maxsize=1)
def _private_runner() -> tuple[Callable[..., Any], str]:
    try:
        module = importlib.import_module(_RC0031_ADAPTER)
    except ModuleNotFoundError as error:
        if error.name != _RC0031_ADAPTER:
            raise
        module = importlib.import_module(_RC0030_ADAPTER)
        api_name = _RC0030_PRIVATE_API
        subject_version = "rc0030"
    else:
        api_name = _RC0031_PRIVATE_API
        subject_version = "rc0031"
    runner = getattr(module, api_name, None)
    if not callable(runner):
        _closed_fail("STEP11_RC0031_P1_PRIVATE_RUNTIME_API_INVALID")
    return runner, subject_version


@lru_cache(maxsize=None)
def _execution(case_id: str) -> tuple[Any, str]:
    fixture, samples, closure = _authority()
    row = next(item for item in fixture["rows"] if item["case_id"] == case_id)
    runner, subject_version = _private_runner()
    execution = runner(
        samples[case_id]["input"],
        case_id=case_id,
        source_case_commitment=row["source_case_commitment"],
        source_dependency_closure_sha256=closure,
    )
    result = getattr(execution, "body_free_result", None)
    body = getattr(execution, "selected_final_utf8_bytes", None)
    if (
        result is None
        or getattr(result, "disposition", None) != "selected"
        or getattr(result, "selected_candidate_present", None) is not True
        or type(body) is not bytes
        or not body
    ):
        _closed_fail("STEP11_RC0031_P1_SUBJECT_NOT_SELECTED")
    if (
        subject_version == "rc0030"
        and hashlib.sha256(body).hexdigest()
        != row["rc0030_selected_final_utf8_sha256"]
    ):
        _closed_fail("STEP11_RC0031_P1_RC0030_OUTPUT_COMMITMENT_MISMATCH")
    return execution, subject_version


def _selected_candidate(execution: Any) -> Any:
    selection = getattr(execution, "selection_result", None)
    candidate = getattr(selection, "selected_candidate", None)
    if candidate is None:
        _closed_fail("STEP11_RC0031_P1_SELECTED_CANDIDATE_MISSING")
    return candidate


def _surface_sections(body: bytes) -> tuple[tuple[str, ...], tuple[str, ...]]:
    try:
        text = body.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        _closed_fail("STEP11_RC0031_P1_SELECTED_UTF8_INVALID")
    if text.encode("utf-8", errors="strict") != body:
        _closed_fail("STEP11_RC0031_P1_SELECTED_UTF8_NONCANONICAL")
    prefix = "見えたこと：\n"
    separator = "\n\nEmlisから：\n"
    if not text.startswith(prefix) or text.count(separator) != 1:
        _closed_fail("STEP11_RC0031_P1_SURFACE_LAYOUT_INVALID")
    observation, reception = text[len(prefix) :].split(separator)
    observation_lines = tuple(observation.split("\n"))
    reception_lines = tuple(reception.split("\n"))
    if (
        not observation_lines
        or not reception_lines
        or any(not line for line in (*observation_lines, *reception_lines))
    ):
        _closed_fail("STEP11_RC0031_P1_SURFACE_LAYOUT_INVALID")
    return observation_lines, reception_lines


def _base_and_final_sections(
    execution: Any,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    candidate = _selected_candidate(execution)
    base = getattr(candidate, "base_candidate", None)
    base_body = getattr(base, "final_utf8_bytes", None)
    final_body = getattr(execution, "selected_final_utf8_bytes", None)
    if type(base_body) is not bytes or type(final_body) is not bytes:
        _closed_fail("STEP11_RC0031_P1_SURFACE_BYTES_MISSING")
    base_observation, base_reception = _surface_sections(base_body)
    final_observation, final_reception = _surface_sections(final_body)
    return base_observation, base_reception, final_observation, final_reception


@lru_cache(maxsize=1)
def _old_catalog() -> dict[str, Any]:
    module = importlib.import_module(
        "emlis_ai_step11_rc0030_experiment_surface_catalog_v3"
    )
    catalog = getattr(module, "STEP11_RC0030_EXPERIMENT_SURFACE_CATALOG", None)
    if type(catalog) is not dict:
        _closed_fail("STEP11_RC0031_P1_RC0030_CATALOG_INVALID")
    return catalog


def _new_occurrence_count(execution: Any, fragments: tuple[str, ...]) -> int:
    base_observation, base_reception, final_observation, final_reception = (
        _base_and_final_sections(execution)
    )
    base_text = "\n".join((*base_observation, *base_reception))
    final_text = "\n".join((*final_observation, *final_reception))
    return sum(
        max(0, final_text.count(fragment) - base_text.count(fragment))
        for fragment in set(fragments)
        if fragment
    )


def _old_schema_delta(execution: Any) -> int:
    catalog = _old_catalog()
    names = (
        "construction_clause_fragments",
        "role_position_clause_fragments",
        "relation_clause_fragments",
        "semantic_link_clause_fragments",
        "unknown_clause_fragments",
        "owner_role_clause_fragments",
        "owner_kind_referent_heads",
    )
    fragments = tuple(
        fragment
        for name in names
        for fragment in catalog[name].values()
    ) + (catalog["clause_morphology"]["semantic_pack_predicate_suffix"],)
    return _new_occurrence_count(execution, fragments)


def _old_relation_nominal_delta(execution: Any) -> int:
    catalog = _old_catalog()
    fragments = tuple(catalog["relation_clause_fragments"].values()) + tuple(
        catalog["semantic_link_clause_fragments"].values()
    )
    return _new_occurrence_count(execution, fragments)


def _old_generic_pack_delta(execution: Any) -> int:
    suffix = _old_catalog()["clause_morphology"][
        "semantic_pack_predicate_suffix"
    ]
    return _new_occurrence_count(execution, (suffix,))


def _root_proposition_is_visible_and_independently_bound(execution: Any) -> bool:
    base_observation, _base_reception, final_observation, _final_reception = (
        _base_and_final_sections(execution)
    )
    visible = bool(
        base_observation
        and final_observation
        and final_observation[0].startswith(base_observation[0])
    )
    candidate = _selected_candidate(execution)
    plan = getattr(candidate, "surface_realization_plan", None)
    binding = getattr(plan, "root_proposition_binding", None)
    verified = getattr(execution, "selected_verified_binding", None)
    return bool(
        visible
        and binding is not None
        and getattr(binding, "sentence_group_ordinal", None) == 1
        and getattr(binding, "grammatical_chunk_ordinal", None) == 1
        and getattr(verified, "root_proposition_match_count", None) == 1
    )


def _proposition_distribution_is_bounded(execution: Any) -> bool:
    candidate = _selected_candidate(execution)
    plan = getattr(candidate, "surface_realization_plan", None)
    rows = getattr(plan, "proposition_clause_bindings", None)
    if type(rows) is not tuple or not rows:
        return False
    seen: list[str] = []
    for row in rows:
        atom_ids = getattr(row, "source_atom_ids", None)
        if (
            type(atom_ids) is not tuple
            or not 1 <= len(atom_ids) <= 2
            or type(getattr(row, "sentence_group_ordinal", None)) is not int
            or type(getattr(row, "grammatical_chunk_ordinal", None)) is not int
        ):
            return False
        seen.extend(atom_ids)
    return bool(
        len(seen) == len(set(seen))
        and getattr(plan, "maximum_visible_clauses_per_grammatical_sentence", None)
        == 2
        and getattr(plan, "maximum_grammatical_complexity_load", None) == 4
    )


def _old_reception_layout_present(execution: Any) -> bool:
    _base_observation, base_reception, _final_observation, final_reception = (
        _base_and_final_sections(execution)
    )
    acts = tuple(
        _old_catalog()["reception_act_predicate_fragments"].values()
    )
    object_particle = _old_catalog()["clause_morphology"]["object_particle"]
    for ordinal, line in enumerate(final_reception):
        old_act = any(line.endswith(act + "。") for act in acts)
        if not old_act:
            continue
        base_equal = ordinal < len(base_reception) and line == base_reception[ordinal]
        quoted_target_list = "「" in line and "」" in line
        target_list_generic_act = any(
            object_particle + act in line and line.endswith(act + "。")
            for act in acts
        )
        if base_equal or quoted_target_list or target_list_generic_act:
            return True
    return False


def test_rc0031_p1_predecessor_source_evidence_path_attack_and_resource_freeze_is_exact() -> None:
    fixture, _samples, _closure = _authority()
    assert fixture["body_free"] is True
    assert fixture["representative_count"] == 8
    assert not (_all_mapping_keys(fixture) & _FORBIDDEN_BODY_KEYS)

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
        prefix = (_REPO_ROOT / path_text).read_bytes()[: commitment["byte_count"]]
        assert len(prefix) == commitment["byte_count"]
        assert hashlib.sha256(prefix).hexdigest() == commitment["sha256"]

    scope = fixture["path_scope"]
    assert tuple(scope["new_exact18"]) == _EXPECTED_EXACT18
    assert set(scope["p1_active_new_paths"]) == _EXPECTED_P1_ACTIVE
    assert scope["p1_modified_existing_paths"] == []
    assert scope["later_phase_reserved_path_count"] == 16
    if importlib.util.find_spec(_RC0031_ADAPTER) is None:
        assert {
            path for path in _EXPECTED_EXACT18 if (_REPO_ROOT / path).exists()
        } == _EXPECTED_P1_ACTIVE

    exact7 = fixture["exact7_contract"]
    assert exact7["collected_count"] == 7
    assert exact7["pass_count_on_unchanged_rc0030"] == 1
    assert exact7["intentional_red_count_on_unchanged_rc0030"] == 6
    assert tuple(
        row["closed_code"]
        for row in exact7["test_nodes"]
        if row["closed_code"] is not None
    ) == _EXPECTED_RED_CODES

    attacks = fixture["attack_contract"]
    inherited = _load_json(_REPO_ROOT / attacks["inherited_source_fixture_path"])
    assert _sha256(_REPO_ROOT / attacks["inherited_source_fixture_path"]) == (
        attacks["inherited_source_fixture_sha256"]
    )
    inherited_contract = inherited["retained_attack_contract"]
    assert len(inherited_contract["existing_rc0029_attack_ids"]) == 33
    assert len(inherited_contract["rc0030_pending_executable_attack_ids"]) == 20
    assert attacks["inherited_named_attack_count"] == 53
    new_attacks = attacks["new_pending_attacks"]
    assert len(new_attacks) == attacks["new_pending_attack_count"] == 24
    assert len({row["attack_id"] for row in new_attacks}) == 24
    assert {row["family"] for row in new_attacks} == {
        "root", "schema", "relation", "distribution", "reception", "boundary"
    }
    assert all(
        sum(row["family"] == family for row in new_attacks) == 4
        for family in {row["family"] for row in new_attacks}
    )
    assert all(
        row["executor_phase"] == "P5"
        and row["executed"] is False
        and _CLOSED_CODE_RE.fullmatch(row["expected_closed_code"])
        is not None
        for row in new_attacks
    )
    assert attacks["combined_named_attack_count_minimum"] == 77
    assert attacks["inherited_attack_replacement_or_subtraction_allowed"] is False

    resources = fixture["resource_contract"]
    assert resources["global_bounds"]["candidate_total_max"] == 12
    assert resources["global_bounds"]["replan_max"] == 1
    assert resources["global_bounds"]["source_owner_max"] == 24
    assert resources["global_bounds"]["parser_body_bytes_max"] == 1_000_000
    assert resources["parser_bounds"]["evaluated_decompositions_per_candidate_max"] == 76
    assert resources["parser_bounds"]["parser_invocations_across_candidates_max"] == 24
    assert resources["parser_bounds"]["body_byte_inspections_across_candidates_max"] == 48_000_000
    assert resources["catalog_denominator"]["realization_alternatives_per_semantic_key_max"] == 1

    support = fixture["support_positive_authority_reference"]
    assert _sha256(_REPO_ROOT / support["fixture_path"]) == support["fixture_sha256"]
    support_fixture = _load_json(_REPO_ROOT / support["fixture_path"])
    assert set(support["source_authority_case_ids"]) <= {
        row.get("case_id") for row in support_fixture["cases"]
    }
    assert support["representative8_support_positive_count"] == 0
    assert support["service_case_branch_authorized"] is False

    rows = fixture["rows"]
    assert sum(
        "MAIN_MEANING_OBSCURED" in row["rc0030_closed_reason_codes"]
        for row in rows
    ) == 6
    assert sum(
        "EMLIS_RECEPTION_UNBOUND" in row["rc0030_closed_reason_codes"]
        for row in rows
    ) == 5
    assert fixture["current_product_read_summary"]["severity_counts"] == {
        "PASS": 1,
        "MINOR": 1,
        "MAJOR": 6,
        "BLOCKER": 0,
    }


def test_rc0031_p1_source_root_and_main_meaning_dominance_is_proved() -> None:
    if any(
        not _root_proposition_is_visible_and_independently_bound(
            _execution(case_id)[0]
        )
        for case_id in _MAIN_CASE_IDS
    ):
        _closed_fail("STEP11_RC0031_SOURCE_ROOT_DOMINANCE_NOT_PROVED")


def test_rc0031_p1_schema_free_proposition_realization_is_proved() -> None:
    if any(
        _old_schema_delta(_execution(case_id)[0]) > 0
        for case_id in _MAIN_CASE_IDS
    ):
        _closed_fail("STEP11_RC0031_SCHEMA_FREE_PROPOSITION_NOT_PROVED")


def test_rc0031_p1_relation_endpoint_direction_and_legibility_is_proved() -> None:
    if any(
        _old_relation_nominal_delta(_execution(case_id)[0]) > 0
        for case_id in _RELATION_CASE_IDS
    ):
        _closed_fail("STEP11_RC0031_RELATION_PROPOSITION_NOT_PROVED")


def test_rc0031_p1_semantic_chunk_distribution_and_depth_is_proved() -> None:
    if any(
        _old_generic_pack_delta(_execution(case_id)[0]) > 0
        or not _proposition_distribution_is_bounded(_execution(case_id)[0])
        for case_id in _DISTRIBUTION_CASE_IDS
    ):
        _closed_fail("STEP11_RC0031_DISTRIBUTION_DEPTH_NOT_PROVED")


def test_rc0031_p1_grounded_reception_target_support_act_predication_is_proved() -> None:
    if any(
        _old_reception_layout_present(_execution(case_id)[0])
        for case_id in _RECEPTION_FAILURE_CASE_IDS
    ):
        _closed_fail("STEP11_RC0031_GROUNDED_RECEPTION_PREDICATION_NOT_PROVED")


def test_rc0031_p1_controls_and_retained_improvements_do_not_regress() -> None:
    fixture, _samples, _closure = _authority()
    controls = fixture["control_contract"]
    assert controls == {
        "nls3s_b001_0001": {
            "baseline": "PASS", "rc0030": "MINOR", "rc0031_required": ["PASS"]
        },
        "nls3s_b001_0002": {
            "baseline": "PASS", "rc0030": "PASS", "rc0031_required": ["PASS"]
        },
        "nls3s_b001_0009": {
            "baseline": "MINOR", "rc0030": "MAJOR", "rc0031_required": ["PASS", "MINOR"]
        },
    }
    executions = {case_id: _execution(case_id)[0] for case_id in _CONTROL_IDS}
    common_proxy_failed = bool(
        _old_reception_layout_present(executions["nls3s_b001_0001"])
        or _old_reception_layout_present(executions["nls3s_b001_0009"])
        or _old_schema_delta(executions["nls3s_b001_0009"]) > 0
        or not _root_proposition_is_visible_and_independently_bound(
            executions["nls3s_b001_0009"]
        )
    )
    if common_proxy_failed:
        _closed_fail("STEP11_RC0031_CONTROL_RETAINED_NON_REGRESSION_NOT_PROVED")
