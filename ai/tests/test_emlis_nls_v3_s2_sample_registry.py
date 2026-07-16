# -*- coding: utf-8 -*-
from __future__ import annotations

"""Independent Step 2 contracts for NLS v3 sample and corpus tooling."""

import ast
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
from typing import Any, Callable, Mapping, Sequence

from helpers import emlis_nls_v3_s2_sample_registry as s2


_AI_ROOT = Path(__file__).resolve().parents[1]
_REPO_ROOT = _AI_ROOT.parent
_INFERENCE_ROOT = _AI_ROOT / "services" / "ai_inference"


def _valid_samples() -> list[Mapping[str, Any]]:
    return s2.load_canonical_jsonl(s2.VALID_FIXTURE_PATH)


def _assert_raises(call: Callable[[], Any], expected: str) -> None:
    try:
        call()
    except (OSError, UnicodeError, ValueError) as exc:
        assert expected in str(exc), (expected, type(exc).__name__, str(exc))
    else:
        raise AssertionError(f"expected failure containing: {expected}")


def _write_canonical_json(path: Path, value: Any) -> None:
    path.write_bytes(s2.canonical_json_text(value).encode("utf-8") + b"\n")


def _write_canonical_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    path.write_bytes(
        b"".join(s2.canonical_json_text(row).encode("utf-8") + b"\n" for row in rows)
    )


def _case_with_text(source: Mapping[str, Any], case_id: str, text: str) -> dict[str, Any]:
    value = deepcopy(source)
    value["case_id"] = case_id
    value["input"]["thought_text"] = text
    value["input"]["action_text"] = ""
    value["input"]["emotions"] = [{"type": "平穏", "strength": "medium"}]
    value["input"]["categories"] = ["生活"]
    value["coverage"]["input_field_presence"] = "thought_only"
    value["coverage"]["thought_action_relation"] = "not_applicable"
    value["coverage"]["emotion_cardinality"] = "single"
    value["coverage"]["emotion_strength_shape"] = "single_strength"
    value["coverage"]["category_cardinality"] = "single"
    return value


def _batch001_samples(count: int) -> list[dict[str, Any]]:
    source = _valid_samples()[0]
    rows: list[dict[str, Any]] = []
    for number in range(1, count + 1):
        token = hashlib.sha256(f"nls3-step2-boundary-{number}".encode()).hexdigest()
        row = _case_with_text(
            source,
            f"nls3s_b001_{number:04d}",
            f"境界確認用の合成記述 {token}",
        )
        row["batch_id"] = "nls3_batch_001"
        rows.append(row)
    return rows


def _pending_privacy_review() -> dict[str, Any]:
    return {
        "status": "pending",
        "reviewer": None,
        "pii_absent": False,
        "real_user_text_copy_absent": False,
        "expected_response_absent": False,
    }


def _passed_privacy_review() -> dict[str, Any]:
    return {
        "status": "passed",
        "reviewer": "karen",
        "pii_absent": True,
        "real_user_text_copy_absent": True,
        "expected_response_absent": True,
    }


def test_step2_app_reachable_positive_and_independent_negative_fixtures() -> None:
    valid = _valid_samples()
    assert len(valid) == 4
    assert all(s2.validate_sample_case(row) == () for row in valid)

    invalid = s2.load_canonical_jsonl(s2.INVALID_FIXTURE_PATH, validator=None)
    assert len(invalid) >= 13
    fixture_ids = {row["fixture_id"] for row in invalid}
    assert {"self_insight_mixed", "both_whitespace", "emotion_not_array"} <= fixture_ids
    for row in invalid:
        issues = s2.validate_app_reachable_input(row["input"])
        assert row["expected_issue"] in issues, row["fixture_id"]

    base = deepcopy(valid[0]["input"])
    for whitespace in ("\ufeff", "\u00a0", "\u3000"):
        mutation = deepcopy(base)
        mutation["thought_text"] = whitespace
        mutation["action_text"] = whitespace
        assert "input:thought_action_both_empty_after_js_trim" in (
            s2.validate_app_reachable_input(mutation)
        )
    for rn_non_whitespace in ("\u0085", "\u001c", "\u200b"):
        mutation = deepcopy(base)
        mutation["thought_text"] = rn_non_whitespace
        mutation["action_text"] = ""
        assert s2.validate_app_reachable_input(mutation) == ()

    long_text = deepcopy(base)
    long_text["thought_text"] = "長" * 200_000
    assert s2.validate_app_reachable_input(long_text) == ()

    maximum_labels = deepcopy(base)
    maximum_labels["emotions"] = [
        {"type": emotion, "strength": "medium"}
        for emotion in s2.EMOTION_TYPES[:-1]
    ]
    maximum_labels["categories"] = list(s2.CATEGORY_TYPES)
    assert s2.validate_app_reachable_input(maximum_labels) == ()


def test_step2_sample_schema_cross_fields_and_forbidden_annotations_are_closed() -> None:
    source = _valid_samples()[2]

    mutation = deepcopy(source)
    mutation["expected_final_text"] = "must never be a sample annotation"
    assert s2.validate_sample_case(mutation) == ("sample:keyset_mismatch",)

    mutation = deepcopy(source)
    del mutation["semantic_contract"]
    assert s2.validate_sample_case(mutation) == ("sample:keyset_mismatch",)

    mutation = deepcopy(source)
    mutation["schema_version"] = "cocolon.emlis.nls_v3.sample_case.v2"
    assert "sample.schema_version:mismatch" in s2.validate_sample_case(mutation)

    mutation = deepcopy(source)
    mutation["case_id"] = "nls3s_b999_0003"
    assert "sample.case_id:batch_identity_mismatch" in s2.validate_sample_case(mutation)

    mutation = deepcopy(source)
    mutation["source"] = "claimed_without_review"
    assert "sample.source:enum_invalid" in s2.validate_sample_case(mutation)

    mutation = deepcopy(source)
    mutation["semantic_contract"]["required_meaning_codes"] *= 2
    assert "sample.semantic_contract.required_meaning_codes:duplicate_value" in (
        s2.validate_sample_case(mutation)
    )

    mutation = deepcopy(source)
    mutation["semantic_contract"]["expected_depth_range"] = ["minimal", "layered"]
    assert "sample.semantic_contract.expected_depth_range:enum_unique_order_invalid" in (
        s2.validate_sample_case(mutation)
    )

    mutation = deepcopy(source)
    mutation["coverage"]["emotion_strength_shape"] = "single_strength"
    assert "sample.coverage.emotion_strength_shape:input_mismatch" in (
        s2.validate_sample_case(mutation)
    )

    mutation = deepcopy(source)
    mutation["coverage"]["input_field_presence"] = "thought_only"
    assert "sample.coverage.input_field_presence:input_mismatch" in (
        s2.validate_sample_case(mutation)
    )

    mutation = deepcopy(source)
    mutation["coverage"]["structural_variation"]["order_variation_eligible"] = 1
    assert "sample.coverage.structural_variation:strict_boolean_required" in (
        s2.validate_sample_case(mutation)
    )

    mutation = deepcopy(source)
    mutation["input"]["emotions"][0]["strength"] = []
    assert "input.emotions[0].strength:string_or_unicode_invalid" in (
        s2.validate_sample_case(mutation)
    )

    mutation = deepcopy(source)
    mutation["input"]["emotions"][0]["type"] = {}
    assert "input.emotions[0].type:string_or_unicode_invalid" in (
        s2.validate_sample_case(mutation)
    )


def test_step2_json_and_jsonl_are_utf8_lf_canonical_and_adversarially_strict() -> None:
    row = _valid_samples()[0]
    canonical = s2.canonical_json_text(row).encode("utf-8") + b"\n"
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        good = root / "good.jsonl"
        good.write_bytes(canonical)
        assert s2.load_canonical_jsonl(good) == [row]

        cases = {
            "bom": b"\xef\xbb\xbf" + canonical,
            "crlf": canonical[:-1] + b"\r\n",
            "no_final_lf": canonical[:-1],
            "blank_line": canonical + b"\n",
            "noncanonical": json.dumps(row, ensure_ascii=False).encode("utf-8") + b"\n",
            "invalid_utf8": b"{\"x\":\"\xff\"}\n",
            "duplicate_key": b'{"a":1,"a":2}\n',
            "nan": b'{"a":NaN}\n',
            "infinity": b'{"a":Infinity}\n',
            "lone_surrogate": b'{"a":"\\ud800"}\n',
            "duplicate_case_id": canonical + canonical,
        }
        expected = {
            "bom": "bom",
            "crlf": "lf_only",
            "no_final_lf": "final_lf",
            "blank_line": "blank_line",
            "noncanonical": "noncanonical",
            "invalid_utf8": "UnicodeDecodeError",
            "duplicate_key": "duplicate_json_key",
            "nan": "non_finite_number",
            "infinity": "non_finite_number",
            "lone_surrogate": "lone_surrogate",
            "duplicate_case_id": "duplicate_case_id",
        }
        for name, payload in cases.items():
            path = root / f"{name}.jsonl"
            path.write_bytes(payload)
            if name == "invalid_utf8":
                try:
                    s2.load_canonical_jsonl(path)
                except UnicodeDecodeError:
                    pass
                else:
                    raise AssertionError("invalid UTF-8 was accepted")
            else:
                _assert_raises(lambda path=path: s2.load_canonical_jsonl(path), expected[name])

        canonical_json = root / "canonical.json"
        _write_canonical_json(canonical_json, {"body_free": True, "count": 0})
        assert s2.load_canonical_json(canonical_json) == {"body_free": True, "count": 0}
        canonical_json.write_bytes(b'{"count":0,"body_free":true}\n')
        _assert_raises(lambda: s2.load_canonical_json(canonical_json), "noncanonical")


def test_step2_exact_normalized_near_duplicate_policies_are_distinct_and_order_stable() -> None:
    valid = _valid_samples()

    exact_left = deepcopy(valid[0])
    exact_right = deepcopy(valid[0])
    exact_right["case_id"] = "nls3s_b000_0091"
    exact = s2.build_duplicate_report([exact_left, exact_right])
    assert exact["counts"] == {"exact": 1, "normalized": 0, "near": 0}

    normalized_left = deepcopy(valid[2])
    normalized_right = deepcopy(valid[2])
    normalized_right["case_id"] = "nls3s_b000_0092"
    normalized_right["input"]["thought_text"] = (
        "　" + normalized_right["input"]["thought_text"] + "  "
    )
    normalized_right["input"]["action_text"] += "\t"
    normalized_right["input"]["emotions"].reverse()
    normalized_right["input"]["categories"].reverse()
    normalized = s2.build_duplicate_report([normalized_left, normalized_right])
    assert normalized["counts"] == {"exact": 0, "normalized": 1, "near": 0}

    near_left = _case_with_text(
        valid[0], "nls3s_b000_0093", "駅まで歩く途中で、朝の風が心地よいと感じた。"
    )
    near_right = _case_with_text(
        valid[0], "nls3s_b000_0094", "駅まで歩く途中で、夕方の風が心地よいと感じた。"
    )
    near = s2.build_duplicate_report([near_left, near_right])
    assert near["counts"] == {"exact": 0, "normalized": 0, "near": 1}

    far = _case_with_text(
        valid[0], "nls3s_b000_0095", "図書館で歴史資料の索引を静かに調べた。"
    )
    assert s2.build_duplicate_report([near_left, far])["counts"] == {
        "exact": 0,
        "normalized": 0,
        "near": 0,
    }

    asymmetric_left = _case_with_text(valid[0], "nls3s_b000_0096", "cdbcacaeeeadedaee")
    asymmetric_right = _case_with_text(valid[0], "nls3s_b000_0097", "cdbaacaeedadeabed")
    forward = s2.build_duplicate_report([asymmetric_left, asymmetric_right])
    reverse = s2.build_duplicate_report([asymmetric_right, asymmetric_left])
    assert s2.strict_json_equal(forward, reverse)
    assert forward["counts"]["near"] == 1

    short_left = _case_with_text(valid[0], "nls3s_b000_0098", "短文A")
    short_right = _case_with_text(valid[0], "nls3s_b000_0099", "短文B")
    assert s2.build_duplicate_report([short_left, short_right])["counts"]["near"] == 0


def test_step2_identity_commitments_separate_input_case_and_private_hmac_domains() -> None:
    sample = deepcopy(_valid_samples()[0])
    input_identity = s2.exact_input_identity(sample)
    case_identity = s2.case_commitment(sample)
    assert input_identity != case_identity

    annotation_mutation = deepcopy(sample)
    annotation_mutation["coverage"]["families"] = ["limited_grounding"]
    assert s2.exact_input_identity(annotation_mutation) == input_identity
    assert s2.case_commitment(annotation_mutation) != case_identity

    private = deepcopy(sample)
    private["source"] = "real_user_anonymized_private"
    assert s2.validate_sample_case(private) == ()
    _assert_raises(lambda: s2.case_commitment(private), "reviewed_synthetic_source")
    _assert_raises(
        lambda: s2.build_duplicate_report([private]), "reviewed_synthetic_source"
    )
    _assert_raises(
        lambda: s2.build_coverage_matrix([private], batch_id=private["batch_id"]),
        "reviewed_synthetic_source",
    )

    reviewed_other_ai = deepcopy(sample)
    reviewed_other_ai["source"] = "other_ai_generated_reviewed"
    assert s2.validate_sample_case(reviewed_other_ai) == ()
    assert len(s2.case_commitment(reviewed_other_ai)) == 64
    assert s2.build_duplicate_report([reviewed_other_ai])["counts"] == {
        "exact": 0,
        "normalized": 0,
        "near": 0,
    }
    assert s2.build_coverage_matrix(
        [reviewed_other_ai], batch_id=reviewed_other_ai["batch_id"]
    )["case_count"] == 1

    key = bytes(range(32))
    input_hmac = s2.private_input_identity_hmac(private["input"], key=key, key_id="local_v1")
    case_hmac = s2.private_case_commitment_hmac(private, key=key, key_id="local_v1")
    corpus_hmac = s2.private_corpus_set_commitment_hmac(
        [private], key=key, key_id="local_v1"
    )
    assert len({input_hmac, case_hmac, corpus_hmac}) == 3
    assert all(len(value) == 64 for value in (input_hmac, case_hmac, corpus_hmac))
    same_id_different_case = deepcopy(private)
    same_id_different_case["input"]["thought_text"] += "別の内容"
    _assert_raises(
        lambda: s2.private_corpus_set_commitment_hmac(
            [private, same_id_different_case], key=key, key_id="local_v1"
        ),
        "private_corpus_duplicate_case_id",
    )
    _assert_raises(
        lambda: s2.private_case_commitment_hmac(private, key=b"short", key_id="local_v1"),
        "256_bits",
    )


def test_step2_coverage_matrix_is_complete_recomputed_body_free_and_strictly_typed() -> None:
    samples = _valid_samples()
    matrix = s2.build_coverage_matrix(samples, batch_id="nls3_batch_000")
    reversed_matrix = s2.build_coverage_matrix(
        list(reversed(samples)), batch_id="nls3_batch_000"
    )
    assert s2.strict_json_equal(matrix, reversed_matrix)
    assert s2.validate_coverage_matrix(matrix, samples) == ()
    assert len(matrix["axis_counts"]) == 21
    assert matrix["body_free"] is True
    serialized = s2.canonical_json_text(matrix)
    assert all(
        not row["input"]["thought_text"]
        or row["input"]["thought_text"] not in serialized
        for row in samples
    )

    mutation = deepcopy(matrix)
    mutation["body_free"] = 1
    assert s2.validate_coverage_matrix(mutation, samples)

    mutation = deepcopy(matrix)
    mutation["axis_counts"][0]["value_counts"][0]["case_count"] = False
    assert s2.validate_coverage_matrix(mutation, samples)

    duplicated_id = [deepcopy(samples[0]), deepcopy(samples[0])]
    _assert_raises(
        lambda: s2.build_coverage_matrix(duplicated_id, batch_id="nls3_batch_000"),
        "duplicate_case_id",
    )


def test_step2_schema_files_are_closed_and_runtime_bound_without_new_dependency() -> None:
    assert s2.schema_runtime_binding_issues() == ()
    paths = (
        s2.SAMPLE_SCHEMA_PATH,
        s2.COVERAGE_SCHEMA_PATH,
        s2.BATCH_MANIFEST_SCHEMA_PATH,
        s2.CORPUS_REGISTRY_SCHEMA_PATH,
    )
    for path in paths:
        value = json.loads(path.read_text(encoding="utf-8"))
        assert value["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert value["additionalProperties"] is False
        assert set(value["properties"]) == set(value["required"])

    sample_schema = json.loads(s2.SAMPLE_SCHEMA_PATH.read_text(encoding="utf-8"))
    assert len(sample_schema["properties"]["input"]["properties"]["emotions"]["oneOf"]) == 2
    coverage_schema = json.loads(s2.COVERAGE_SCHEMA_PATH.read_text(encoding="utf-8"))
    allowed_values = (
        coverage_schema["properties"]["axis_counts"]["items"]["properties"]
        ["value_counts"]["items"]["properties"]["value"]["enum"]
    )
    assert "raw user sentence" not in allowed_values
    for unsafe_ref in (
        "/absolute.json",
        "../escape.json",
        "a/../escape.json",
        "a/./file.json",
        "a//file.json",
        "a\\file.json",
        "C:file.json",
        "~/file.json",
        "line\nfeed.json",
        "nul\x00byte.json",
    ):
        assert s2._safe_relative_artifact_ref(unsafe_ref) is False
    assert s2._safe_relative_artifact_ref("ai/tests/fixtures/valid_v1.jsonl") is True

    tree = ast.parse(Path(s2.__file__).read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    assert not any("_v2" in name for name in imported)
    assert not any(name.startswith("emlis_ai_") for name in imported)
    assert not any(
        "emlis_nls_v3_s2_sample_registry" in path.read_text(encoding="utf-8")
        for path in _INFERENCE_ROOT.glob("*.py")
    )


def test_step2_projection_is_an_explicit_deep_copy_allowlist() -> None:
    sample = deepcopy(_valid_samples()[3])
    projection = s2.project_generation_input(sample)
    assert set(projection) == {"thought_text", "action_text", "emotions", "categories"}

    mutation = deepcopy(sample)
    mutation["coverage"]["structural_variation"]["merge_split_eligible"] = False
    mutation["semantic_contract"]["unknown_codes"] = ["EVALUATION_ONLY_SENTINEL"]
    assert s2.validate_sample_case(mutation) == ()
    assert s2.strict_json_equal(s2.project_generation_input(mutation), projection)

    projection["categories"].append("仕事")
    projection["emotions"][0]["strength"] = "weak"
    assert sample["input"]["categories"] == ["人間関係", "価値観"]
    assert sample["input"]["emotions"][0]["strength"] == "medium"

    forbidden = deepcopy(sample)
    forbidden["generation_hint"] = "test-only cue"
    _assert_raises(lambda: s2.project_generation_input(forbidden), "keyset_mismatch")


def test_step2_rn_contract_binding_and_independent_drift_mutations_are_red() -> None:
    assert s2.rn_contract_binding_issues() == ()
    contract = json.loads(s2.STEP1_INPUT_CONTRACT_PATH.read_text(encoding="utf-8"))
    assert s2.validate_rn_contract_snapshot(contract) == ()

    mutation = deepcopy(contract)
    mutation["app_reachable"]["emotion_types"].append("未知")
    assert "step2_policy_rn_contract_mismatch" in s2.validate_rn_contract_snapshot(mutation)

    mutation = deepcopy(contract)
    mutation["app_reachable"]["self_insight_exclusive"] = False
    assert "step2_policy_rn_contract_mismatch" in s2.validate_rn_contract_snapshot(mutation)

    mutation = deepcopy(contract)
    mutation["app_reachable"]["submit_condition"] = "backend_accepts"
    assert "step2_policy_rn_contract_mismatch" in s2.validate_rn_contract_snapshot(mutation)

    assert s2.validate_rn_contract_snapshot(None) == (
        "step1_input_contract_mapping_required",
    )

    original_duplicate_threshold = s2.DUPLICATE_POLICY[
        "near_threshold_basis_points"
    ]
    try:
        s2.DUPLICATE_POLICY["near_threshold_basis_points"] = 10001
        assert s2.policy_binding_issues() == ("duplicate_policy_hash_drift",)
        _assert_raises(
            lambda: s2.build_duplicate_report(_valid_samples()[:1]),
            "duplicate_policy_hash_drift",
        )
    finally:
        s2.DUPLICATE_POLICY[
            "near_threshold_basis_points"
        ] = original_duplicate_threshold

    sample_before_validator_drift = _valid_samples()[0]
    original_validator_authority = s2.VALIDATOR_POLICY["authority"]
    try:
        s2.VALIDATOR_POLICY["authority"] = "mutated_in_process"
        assert s2.policy_binding_issues() == ("validator_policy_hash_drift",)
        assert s2.validate_sample_case(sample_before_validator_drift) == (
            "sample.policy:validator_policy_hash_drift",
        )
        assert s2.validate_app_reachable_input(
            sample_before_validator_drift["input"]
        ) == ("input.policy:validator_policy_hash_drift",)
    finally:
        s2.VALIDATOR_POLICY["authority"] = original_validator_authority
    assert s2.policy_binding_issues() == ()


def test_step2_registry_separates_corpora_binds_tests_and_never_counts_fixture_progress() -> None:
    registry = s2.load_canonical_json(s2.REGISTRY_PATH)
    expected = s2.build_corpus_registry()
    assert s2.strict_json_equal(registry, expected)
    assert s2.validate_corpus_registry(registry) == ()
    assert s2.batch001_creation_preflight(registry) == ()
    assert s2.batch001_creation_preflight(None) == ("corpus_registry_mapping_required",)

    collections = {row["classification"]: row for row in registry["collections"]}
    assert collections["invalid_contract"]["app_reachable_valid_count"] == 0
    assert collections["legacy_input"]["counts_toward_karen_minimum"] is False
    assert collections["real_user_current_valid"]["status"] == "not_received"
    assert collections["real_user_current_valid"]["storage"] == "private_local_only"
    assert registry["aggregate_counts"]["accepted_karen_minimum"] == 0
    assert registry["cumulative_novelty_index"]["accepted_karen_case_count"] == 0
    assert registry["cumulative_novelty_index"]["retired_invalid_case_ids"] == []
    assert (
        registry["cumulative_novelty_index"]["replacement_case_id_reuse_allowed"]
        is False
    )
    assert registry["test_evidence"]["test_sha256"] == s2.sha256_file(Path(__file__))
    assert registry["valid_for_runtime_switch"] is False

    serialized = s2.canonical_json_text(registry)
    assert all(
        not row["input"]["thought_text"]
        or row["input"]["thought_text"] not in serialized
        for row in _valid_samples()
    )

    mutation = deepcopy(registry)
    mutation["aggregate_counts"]["accepted_karen_minimum"] = False
    assert s2.validate_corpus_registry(mutation)

    mutation = deepcopy(registry)
    mutation["collections"][0]["classification"] = "real_user_current_valid"
    assert s2.validate_corpus_registry(mutation)

    mutation = deepcopy(registry)
    mutation["valid_for_runtime_switch"] = 0
    assert s2.validate_corpus_registry(mutation)


def test_step2_manifest_binds_actual_files_review_and_transition_authority() -> None:
    samples = _batch001_samples(100)
    references = _valid_samples()
    with tempfile.TemporaryDirectory(prefix="nls3s2_", dir=_REPO_ROOT) as directory:
        root = Path(directory)
        corpus_path = root / "batch001.jsonl"
        coverage_path = root / "coverage.json"
        duplicate_path = root / "duplicates.json"
        _write_canonical_jsonl(corpus_path, samples)
        _write_canonical_json(
            coverage_path,
            s2.build_coverage_matrix(samples, batch_id="nls3_batch_001"),
        )
        report = s2.build_duplicate_report(samples, reference_samples=references)
        assert report["counts"] == {"exact": 0, "normalized": 0, "near": 0}
        _write_canonical_json(duplicate_path, report)

        draft = s2.build_batch_manifest(
            samples,
            corpus_path=corpus_path,
            coverage_matrix_path=coverage_path,
            duplicate_report_path=duplicate_path,
            state="DRAFT",
            frozen=False,
            privacy_review=_pending_privacy_review(),
        )
        assert draft["next_authority"] == "continue_batch_construction"
        assert draft["counts_toward_karen_minimum"] is False
        assert s2.validate_batch_manifest(
            draft,
            samples,
            corpus_path=corpus_path,
            coverage_matrix_path=coverage_path,
            duplicate_report_path=duplicate_path,
            expected_state="DRAFT",
            expected_frozen=False,
            expected_privacy_review=_pending_privacy_review(),
        ) == ()

        partial_pending_review = _pending_privacy_review()
        partial_pending_review["pii_absent"] = True
        _assert_raises(
            lambda: s2.build_batch_manifest(
                samples,
                corpus_path=corpus_path,
                coverage_matrix_path=coverage_path,
                duplicate_report_path=duplicate_path,
                state="DRAFT",
                frozen=False,
                privacy_review=partial_pending_review,
            ),
            "privacy_review_claim_invalid",
        )
        claimed_pending_reviewer = _pending_privacy_review()
        claimed_pending_reviewer["reviewer"] = "karen"
        _assert_raises(
            lambda: s2.build_batch_manifest(
                samples,
                corpus_path=corpus_path,
                coverage_matrix_path=coverage_path,
                duplicate_report_path=duplicate_path,
                state="DRAFT",
                frozen=False,
                privacy_review=claimed_pending_reviewer,
            ),
            "privacy_review_claim_invalid",
        )

        validated = s2.build_batch_manifest(
            samples,
            corpus_path=corpus_path,
            coverage_matrix_path=coverage_path,
            duplicate_report_path=duplicate_path,
            state="VALIDATED",
            frozen=False,
            privacy_review=_passed_privacy_review(),
        )
        frozen = s2.build_batch_manifest(
            samples,
            corpus_path=corpus_path,
            coverage_matrix_path=coverage_path,
            duplicate_report_path=duplicate_path,
            state="VALIDATED",
            frozen=True,
            privacy_review=_passed_privacy_review(),
        )
        assert validated["next_authority"] == "freeze_batch_manifest"
        assert frozen["next_authority"] == "step3_only"
        assert len({draft["manifest_id"], validated["manifest_id"], frozen["manifest_id"]}) == 3
        assert frozen["counts_toward_karen_minimum"] is False
        assert s2.validate_batch_manifest(
            frozen,
            samples,
            corpus_path=corpus_path,
            coverage_matrix_path=coverage_path,
            duplicate_report_path=duplicate_path,
            expected_state="VALIDATED",
            expected_frozen=True,
            expected_privacy_review=_passed_privacy_review(),
        ) == ()

        invalid_history = [
            {
                "invalid_case_id": "nls3s_b001_9001",
                "reason_code": "APP_REACHABLE_CONTRACT_INVALID",
                "replacement_case_id": samples[0]["case_id"],
                "status": "replaced_before_manifest_freeze",
            }
        ]
        frozen_with_replacement = s2.build_batch_manifest(
            samples,
            corpus_path=corpus_path,
            coverage_matrix_path=coverage_path,
            duplicate_report_path=duplicate_path,
            state="VALIDATED",
            frozen=True,
            privacy_review=_passed_privacy_review(),
            invalid_case_history=invalid_history,
        )
        assert frozen_with_replacement["invalid_case_count"] == 1
        assert frozen_with_replacement["invalid_case_history"] == invalid_history
        assert frozen_with_replacement["replacement_policy"] == (
            "invalid_case_id_never_reused_replacement_gets_new_id"
        )
        assert frozen_with_replacement["manifest_id"] != frozen["manifest_id"]
        assert s2.validate_batch_manifest(
            frozen_with_replacement,
            samples,
            corpus_path=corpus_path,
            coverage_matrix_path=coverage_path,
            duplicate_report_path=duplicate_path,
            expected_state="VALIDATED",
            expected_frozen=True,
            expected_privacy_review=_passed_privacy_review(),
            expected_invalid_case_history=invalid_history,
        ) == ()

        registry = s2.load_canonical_json(s2.REGISTRY_PATH)
        final_ids = {str(sample["case_id"]) for sample in samples}

        def lineage_row(
            invalid_case_id: str = "nls3s_b001_9002",
            replacement_case_id: str = "nls3s_b001_0002",
        ) -> dict[str, str]:
            return {
                "invalid_case_id": invalid_case_id,
                "reason_code": "APP_REACHABLE_CONTRACT_INVALID",
                "replacement_case_id": replacement_case_id,
                "status": "replaced_before_manifest_freeze",
            }

        _assert_raises(
            lambda: s2._normalize_invalid_case_history(
                [lineage_row("nls3s_b001_0001", "nls3s_b001_0001")],
                batch_id="nls3_batch_001",
                final_case_ids=final_ids,
                registry=registry,
            ),
            "replacement_must_use_new_id",
        )
        _assert_raises(
            lambda: s2._normalize_invalid_case_history(
                [lineage_row("nls3s_b002_9002")],
                batch_id="nls3_batch_001",
                final_case_ids=final_ids,
                registry=registry,
            ),
            "case_batch_mismatch",
        )
        _assert_raises(
            lambda: s2._normalize_invalid_case_history(
                [lineage_row("nls3s_b001_0001", "nls3s_b001_0002")],
                batch_id="nls3_batch_001",
                final_case_ids=final_ids,
                registry=registry,
            ),
            "final_corpus_membership_invalid",
        )
        _assert_raises(
            lambda: s2._normalize_invalid_case_history(
                [lineage_row(replacement_case_id="nls3s_b001_9999")],
                batch_id="nls3_batch_001",
                final_case_ids=final_ids,
                registry=registry,
            ),
            "final_corpus_membership_invalid",
        )

        registered_registry = deepcopy(registry)
        registered_registry["cumulative_novelty_index"]["registered_case_ids"].append(
            "nls3s_b001_9002"
        )
        _assert_raises(
            lambda: s2._normalize_invalid_case_history(
                [lineage_row()],
                batch_id="nls3_batch_001",
                final_case_ids=final_ids,
                registry=registered_registry,
            ),
            "case_id_reused",
        )
        registered_replacement_registry = deepcopy(registry)
        registered_replacement_registry["cumulative_novelty_index"][
            "registered_case_ids"
        ].append("nls3s_b001_0002")
        _assert_raises(
            lambda: s2._normalize_invalid_case_history(
                [lineage_row()],
                batch_id="nls3_batch_001",
                final_case_ids=final_ids,
                registry=registered_replacement_registry,
            ),
            "replacement_case_id_reused",
        )
        retired_registry = deepcopy(registry)
        retired_registry["cumulative_novelty_index"]["retired_invalid_case_ids"].append(
            "nls3s_b001_9002"
        )
        _assert_raises(
            lambda: s2._normalize_invalid_case_history(
                [lineage_row()],
                batch_id="nls3_batch_001",
                final_case_ids=final_ids,
                registry=retired_registry,
            ),
            "case_id_reused",
        )
        retired_replacement_registry = deepcopy(registry)
        retired_replacement_registry["cumulative_novelty_index"][
            "retired_invalid_case_ids"
        ].append("nls3s_b001_0002")
        _assert_raises(
            lambda: s2._normalize_invalid_case_history(
                [lineage_row()],
                batch_id="nls3_batch_001",
                final_case_ids=final_ids,
                registry=retired_replacement_registry,
            ),
            "replacement_case_id_reused",
        )
        _assert_raises(
            lambda: s2._normalize_invalid_case_history(
                [lineage_row(), lineage_row(replacement_case_id="nls3s_b001_0003")],
                batch_id="nls3_batch_001",
                final_case_ids=final_ids,
                registry=registry,
            ),
            "duplicate_id",
        )

        invalid_reason = lineage_row()
        invalid_reason["reason_code"] = "not_uppercase"
        _assert_raises(
            lambda: s2._normalize_invalid_case_history(
                [invalid_reason],
                batch_id="nls3_batch_001",
                final_case_ids=final_ids,
                registry=registry,
            ),
            "reason_code_invalid",
        )
        invalid_status = lineage_row()
        invalid_status["status"] = "replaced_after_freeze"
        _assert_raises(
            lambda: s2._normalize_invalid_case_history(
                [invalid_status],
                batch_id="nls3_batch_001",
                final_case_ids=final_ids,
                registry=registry,
            ),
            "status_invalid",
        )

        forged = deepcopy(frozen)
        forged["coverage_matrix_ref"] = "forged/coverage.json"
        assert s2.validate_batch_manifest(
            forged,
            samples,
            corpus_path=corpus_path,
            coverage_matrix_path=coverage_path,
            duplicate_report_path=duplicate_path,
            expected_state="VALIDATED",
            expected_frozen=True,
            expected_privacy_review=_passed_privacy_review(),
        )

        promoted = deepcopy(draft)
        promoted["state"] = "VALIDATED"
        promoted["frozen"] = True
        promoted["next_authority"] = "step3_only"
        assert s2.validate_batch_manifest(
            promoted,
            samples,
            corpus_path=corpus_path,
            coverage_matrix_path=coverage_path,
            duplicate_report_path=duplicate_path,
            expected_state="DRAFT",
            expected_frozen=False,
            expected_privacy_review=_pending_privacy_review(),
        )

        strict_type = deepcopy(frozen)
        strict_type["body_free"] = 1
        assert s2.validate_batch_manifest(
            strict_type,
            samples,
            corpus_path=corpus_path,
            coverage_matrix_path=coverage_path,
            duplicate_report_path=duplicate_path,
            expected_state="VALIDATED",
            expected_frozen=True,
            expected_privacy_review=_passed_privacy_review(),
        )

        _assert_raises(
            lambda: s2.build_batch_manifest(
                samples[:99],
                corpus_path=corpus_path,
                coverage_matrix_path=coverage_path,
                duplicate_report_path=duplicate_path,
                state="VALIDATED",
                frozen=True,
                privacy_review=_passed_privacy_review(),
            ),
            "requires_100_cases",
        )
        _assert_raises(
            lambda: s2.build_batch_manifest(
                [*samples, deepcopy(samples[-1])],
                corpus_path=corpus_path,
                coverage_matrix_path=coverage_path,
                duplicate_report_path=duplicate_path,
                state="VALIDATED",
                frozen=True,
                privacy_review=_passed_privacy_review(),
            ),
            "above_100",
        )


def test_step2_near_candidates_require_explicit_review_before_validation() -> None:
    valid = _valid_samples()
    left = _case_with_text(
        valid[0], "nls3s_b001_0001", "駅まで歩く途中で、朝の風が心地よいと感じた。"
    )
    right = _case_with_text(
        valid[0], "nls3s_b001_0002", "駅まで歩く途中で、夕方の風が心地よいと感じた。"
    )
    for row in (left, right):
        row["batch_id"] = "nls3_batch_001"
    report = s2.build_duplicate_report([left, right])
    assert report["counts"]["near"] == 1
    decisions, unresolved = s2._near_review_result(report, [])
    assert decisions == []
    assert unresolved["unresolved_count"] == 1
    pair = report["pairs"][0]
    accepted, summary = s2._near_review_result(
        report,
        [
            {
                "left_case_id": pair["left_case_id"],
                "right_case_id": pair["right_case_id"],
                "verdict": "accepted_distinct",
                "reason_code": "DISTINCT_MEANING_REVIEWED",
            }
        ],
    )
    assert accepted[0]["verdict"] == "accepted_distinct"
    assert summary == {
        "candidate_count": 1,
        "accepted_distinct_count": 1,
        "rejected_duplicate_count": 0,
        "unresolved_count": 0,
    }


def test_step2_previous_step_artifacts_remain_byte_frozen() -> None:
    expected = {
        _AI_ROOT / "tests" / "fixtures" / "emlis_nls_v3_s0_boundary_20260714.json": "57f0a583ca970c753bfe656627ca75879dd279ff4e2a1471ee2dd7b55586a024",
        _AI_ROOT / "tests" / "fixtures" / "emlis_nls_v3_s1_input_contract_20260714.json": "d577ac80457e25389c0bac351139b2c80a9a506f225023fb7928a1b9068d53c6",
        _AI_ROOT / "tests" / "local_only" / "emlis_nls_v3_s1_v1_visible_20260714.json": "ba7e1f3d11bd7cd156da80dc6594e889b10e57b123df2e6b9c80e4345f47286d",
        _AI_ROOT / "tests" / "fixtures" / "emlis_nls_v3_s1_baseline_receipt_20260714.json": "669835b0fdce3bc1e2e897325ab37b5f82abc9a353bc864993aa284083b7a518",
    }
    for path, expected_sha in expected.items():
        assert s2.sha256_file(path) == expected_sha
