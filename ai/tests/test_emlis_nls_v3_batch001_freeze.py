# -*- coding: utf-8 -*-
from __future__ import annotations

"""Freeze checks for the pre-Step-3 Karen-generated batch 001 corpus."""

from collections import Counter
import re
from pathlib import Path
from typing import Any, Mapping

from helpers import emlis_nls_v3_s2_sample_registry as s2


_AI_ROOT = Path(__file__).resolve().parents[1]
_GENERATED_ROOT = _AI_ROOT / "tests" / "fixtures" / "emlis_nls_v3" / "generated"
_CORPUS_PATH = _GENERATED_ROOT / "batch_001.jsonl"
_COVERAGE_PATH = _GENERATED_ROOT / "batch_001_coverage_matrix.json"
_DUPLICATE_PATH = _GENERATED_ROOT / "batch_001_duplicate_report.json"
_MANIFEST_PATH = _GENERATED_ROOT / "batch_001_manifest.json"

_PRIVACY_REVIEW = {
    "status": "passed",
    "reviewer": "karen",
    "pii_absent": True,
    "real_user_text_copy_absent": True,
    "expected_response_absent": True,
}

_FORBIDDEN_RESPONSE_KEYS = {
    "answer",
    "body",
    "expected_final_text",
    "expected_response",
    "expected_terminal",
    "generated_text",
    "reply",
    "reply_text",
    "response",
    "response_text",
}

_PII_PATTERNS = {
    "email": re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}"),
    "handle": re.compile(r"(?<![A-Za-z0-9_])@[A-Za-z0-9_]{2,}"),
    "phone": re.compile(r"(?<!\d)(?:\d[ -]?){9,11}\d(?!\d)"),
    "postal_code": re.compile(r"〒?\d{3}-?\d{4}"),
    "url": re.compile(r"(?:https?://|www\.)", re.IGNORECASE),
}

_LENGTH_CLASS_THRESHOLDS = (
    (25, "short"),
    (60, "medium"),
    (140, "long"),
)


def _samples() -> list[Mapping[str, Any]]:
    return s2.load_canonical_jsonl(_CORPUS_PATH)


def _walk_keys(value: Any) -> list[str]:
    if isinstance(value, Mapping):
        keys = [str(key) for key in value]
        for child in value.values():
            keys.extend(_walk_keys(child))
        return keys
    if isinstance(value, list):
        keys: list[str] = []
        for child in value:
            keys.extend(_walk_keys(child))
        return keys
    return []


def _axis_counts(matrix: Mapping[str, Any]) -> dict[str, dict[str, int]]:
    return {
        row["axis"]: {
            item["value"]: item["case_count"] for item in row["value_counts"]
        }
        for row in matrix["axis_counts"]
    }


def _evaluated_length_class(sample: Mapping[str, Any]) -> str:
    input_value = sample["input"]
    size = sum(
        len(s2.ecmascript_trim(input_value[field]))
        for field in ("thought_text", "action_text")
    )
    for maximum, label in _LENGTH_CLASS_THRESHOLDS:
        if size <= maximum:
            return label
    return "very_long"


def test_batch001_has_exactly_100_ordered_karen_app_reachable_cases() -> None:
    samples = _samples()
    assert len(samples) == 100
    assert [row["case_id"] for row in samples] == [
        f"nls3s_b001_{number:04d}" for number in range(1, 101)
    ]
    assert {row["batch_id"] for row in samples} == {"nls3_batch_001"}
    assert {row["source"] for row in samples} == {"karen_generated"}
    for sample in samples:
        assert s2.validate_sample_case(sample) == (), sample["case_id"]
        assert s2.validate_app_reachable_input(sample["input"]) == (), sample["case_id"]


def test_batch001_is_input_only_private_safe_and_has_no_expected_reply() -> None:
    samples = _samples()
    for sample in samples:
        assert not (_FORBIDDEN_RESPONSE_KEYS & set(_walk_keys(sample))), sample["case_id"]
        text = "\n".join(
            (sample["input"]["thought_text"], sample["input"]["action_text"])
        )
        for label, pattern in _PII_PATTERNS.items():
            assert pattern.search(text) is None, (sample["case_id"], label)


def test_batch001_annotations_never_enter_generation_input() -> None:
    for sample in _samples():
        projected = s2.project_generation_input(sample)
        assert projected == sample["input"], sample["case_id"]
        assert set(projected) == {
            "thought_text",
            "action_text",
            "emotions",
            "categories",
        }


def test_batch001_coverage_recomputes_and_has_no_empty_designed_cell() -> None:
    samples = _samples()
    matrix = s2.load_canonical_json(_COVERAGE_PATH)
    assert s2.validate_coverage_matrix(matrix, samples) == ()
    counts = _axis_counts(matrix)
    assert all(
        count > 0
        for value_counts in counts.values()
        for count in value_counts.values()
    )
    assert set(counts["families"]) == set(s2.COVERAGE_FAMILIES)
    assert all(counts["families"][family] >= 4 for family in s2.COVERAGE_FAMILIES)

    emotion_counts = Counter(
        emotion["type"]
        for sample in samples
        for emotion in sample["input"]["emotions"]
    )
    category_counts = Counter(
        category for sample in samples for category in sample["input"]["categories"]
    )
    assert all(emotion_counts[label] > 0 for label in s2.EMOTION_TYPES)
    assert all(category_counts[label] > 0 for label in s2.CATEGORY_TYPES)


def test_batch001_evaluation_annotations_are_independent_and_consistent() -> None:
    samples = _samples()
    for sample in samples:
        assert sample["coverage"]["length_class"] == _evaluated_length_class(sample), (
            sample["case_id"],
            sample["coverage"]["length_class"],
            _evaluated_length_class(sample),
        )
        structure = sample["coverage"]["structural_variation"]
        if structure["minimal_single_structure_expected"]:
            assert structure == {
                "merge_split_eligible": False,
                "minimal_single_structure_expected": True,
                "order_variation_eligible": False,
                "reception_position_variation_eligible": False,
            }, sample["case_id"]

    topic_category_divergences = [
        sample["case_id"]
        for sample in samples
        if sample["coverage"]["topic_cardinality"]
        != sample["coverage"]["category_cardinality"]
    ]
    assert topic_category_divergences


def test_batch001_length_annotation_boundary_policy_is_frozen() -> None:
    def sample_with_lengths(thought_size: int, action_size: int) -> dict[str, Any]:
        return {
            "input": {
                "thought_text": "考" * thought_size,
                "action_text": "動" * action_size,
            }
        }

    assert _evaluated_length_class(sample_with_lengths(25, 0)) == "short"
    assert _evaluated_length_class(sample_with_lengths(20, 6)) == "medium"
    assert _evaluated_length_class(sample_with_lengths(30, 30)) == "medium"
    assert _evaluated_length_class(sample_with_lengths(30, 31)) == "long"
    assert _evaluated_length_class(sample_with_lengths(70, 70)) == "long"
    assert _evaluated_length_class(sample_with_lengths(70, 71)) == "very_long"


def test_batch001_novelty_report_recomputes_against_registered_references() -> None:
    samples = _samples()
    references = s2.load_canonical_jsonl(s2.VALID_FIXTURE_PATH)
    actual = s2.load_canonical_json(_DUPLICATE_PATH)
    expected = s2.build_duplicate_report(samples, reference_samples=references)
    assert s2.strict_json_equal(actual, expected)
    assert actual["query_case_count"] == 100
    assert actual["reference_case_count"] == 4
    assert actual["counts"] == {"exact": 0, "normalized": 0, "near": 0}
    assert actual["pairs"] == []


def test_batch001_manifest_is_validated_frozen_and_file_bound() -> None:
    samples = _samples()
    manifest = s2.load_canonical_json(_MANIFEST_PATH)
    assert s2.validate_batch_manifest(
        manifest,
        samples,
        corpus_path=_CORPUS_PATH,
        coverage_matrix_path=_COVERAGE_PATH,
        duplicate_report_path=_DUPLICATE_PATH,
        expected_state="VALIDATED",
        expected_frozen=True,
        expected_privacy_review=_PRIVACY_REVIEW,
    ) == ()
    assert manifest["case_count"] == manifest["valid_case_count"] == 100
    assert manifest["invalid_case_count"] == 0
    assert manifest["invalid_case_history"] == []
    assert manifest["state"] == "VALIDATED"
    assert manifest["frozen"] is True
    assert manifest["body_free"] is True
    assert manifest["privacy_review"] == _PRIVACY_REVIEW
    assert manifest["duplicate_counts"] == {
        "exact": 0,
        "normalized": 0,
        "near": 0,
    }
    assert manifest["near_review_summary"] == {
        "candidate_count": 0,
        "accepted_distinct_count": 0,
        "rejected_duplicate_count": 0,
        "unresolved_count": 0,
    }
    assert manifest["counts_toward_karen_minimum"] is False
    assert manifest["next_authority"] == "step3_only"


def test_batch001_manifest_preserves_the_step2_transition_boundary() -> None:
    registry = s2.load_canonical_json(s2.REGISTRY_PATH)
    manifest = s2.load_canonical_json(_MANIFEST_PATH)
    assert s2.batch001_creation_preflight(registry) == ()
    assert manifest["parent_registry_sha256"] == s2.sha256_file(s2.REGISTRY_PATH)
    assert manifest["sample_schema_sha256"] == s2.sha256_file(s2.SAMPLE_SCHEMA_PATH)
    assert manifest["validator_policy_sha256"] == s2.VALIDATOR_POLICY_SHA256
    assert manifest["duplicate_policy_sha256"] == s2.DUPLICATE_POLICY_SHA256
    assert manifest["corpus_file_sha256"] == s2.sha256_file(_CORPUS_PATH)
    assert manifest["coverage_matrix_sha256"] == s2.sha256_file(_COVERAGE_PATH)
    assert manifest["duplicate_report_sha256"] == s2.sha256_file(_DUPLICATE_PATH)
    assert registry["valid_for_runtime_switch"] is False
    assert manifest["counts_toward_karen_minimum"] is False
