# -*- coding: utf-8 -*-
from __future__ import annotations

"""Deterministic, offline-only R6 reception batch and review contracts."""

from collections import Counter, defaultdict
from dataclasses import dataclass
import hashlib
import re
import unicodedata
from typing import Any, Iterable, Mapping, Sequence


R6_BATCH_QA_SCHEMA_VERSION = (
    "cocolon.emlis.grounded_human_reception.r6_batch_qa.v1"
)
R6_KAREN_REVIEW_SCHEMA_VERSION = (
    "cocolon.emlis.grounded_human_reception.r6_karen_review.v1"
)
R6_REVIEW_AXES = (
    "reception_role_distinctness",
    "human_warmth",
    "conversational_naturalness",
    "grounded_specificity",
    "whole_input_balance",
    "safety_boundary",
    "non_template_readfeel",
    "wants_more_input_candidate",
)

_SPACE_RE = re.compile(r"\s+")
_CLOSING_DISPLAY_RE = re.compile(r"[\s、。,.!！?？「」『』（）()・:：;；]")
_ABSTRACT_ENDING_PATTERNS = (
    ("abstract_valued_received", re.compile(r"を大切に受け取りました$")),
    ("abstract_as_arrived", re.compile(r"として届きました$")),
    ("abstract_received", re.compile(r"と受け取りました$")),
)
_BODY_KEYS = frozenset(
    {
        "memo",
        "memo_action",
        "current_input",
        "raw_input",
        "raw_text",
        "source_text",
        "comment_text",
        "surface_text",
        "visible_surface",
        "observation_text",
        "reception_text",
        "sentence_text",
        "closing_stem_text",
        "source_anchor",
        "human_notes",
    }
)
_BODY_FLAGS = frozenset(
    {
        "raw_input_included",
        "surface_body_included",
        "comment_text_included",
        "anchor_text_included",
        "sentence_text_included",
        "closing_stem_text_included",
    }
)
_BODY_FREE_VALUE_RE = re.compile(r"^[A-Za-z0-9_.:/-]*$")
_KAREN_RECEIPT_ALLOWED_KEYS = frozenset(
    {
        "schema_version",
        "reviewer",
        "review_scope",
        "visible_packet_ref",
        "visible_packet_sha256",
        "review_axes",
        "reviews",
        "product_readfeel_status",
        "technical_pass_is_product_readfeel_pass",
        "automatic_gate_result_used_as_human_result",
        "raw_input_included",
        "surface_body_included",
        "comment_text_included",
        "anchor_text_included",
        "sentence_text_included",
        "closing_stem_text_included",
        "progression_authority",
        "representative4_actual_device_status",
        "exact8_actual_device_status",
        "valid_for_progression",
    }
)
_KAREN_REVIEW_ROW_ALLOWED_KEYS = frozenset(
    {
        "case_id",
        "visible_surface_sha256",
        "axes",
        "fatal_reason_refs",
        "verdict",
    }
)


def sha256_text(value: str) -> str:
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()


def split_reception_sentences(value: str) -> tuple[str, ...]:
    """Split on visible terminators outside Japanese/ASCII quote pairs."""

    opening_to_closing = {"「": "」", "『": "』", "（": "）", "(": ")"}
    closing = set(opening_to_closing.values())
    stack: list[str] = []
    current: list[str] = []
    output: list[str] = []
    for char in str(value or ""):
        if char in opening_to_closing:
            stack.append(opening_to_closing[char])
            current.append(char)
            continue
        if char in closing and stack and char == stack[-1]:
            stack.pop()
            current.append(char)
            continue
        if not stack and char in "。！？!?\n\r":
            sentence = "".join(current).strip()
            if sentence:
                output.append(sentence)
            current = []
            continue
        current.append(char)
    sentence = "".join(current).strip()
    if sentence:
        output.append(sentence)
    return tuple(output)


def normalize_reception_sentence(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", str(value or ""))
    normalized = _SPACE_RE.sub(" ", normalized).strip()
    return normalized.rstrip("。！？!?").strip().casefold()


def normalize_closing(value: str) -> str:
    return _CLOSING_DISPLAY_RE.sub(
        "",
        unicodedata.normalize("NFKC", str(value or "")).casefold(),
    )


def _longest_common_suffix(left: str, right: str) -> str:
    limit = min(len(left), len(right))
    matched = 0
    while matched < limit and left[-(matched + 1)] == right[-(matched + 1)]:
        matched += 1
    return left[-matched:] if matched else ""


def _body_free(value: Any) -> bool:
    if isinstance(value, dict):
        for raw_key, nested in value.items():
            key = str(raw_key or "")
            if not _BODY_FREE_VALUE_RE.fullmatch(key):
                return False
            if key in _BODY_KEYS:
                return False
            if key in _BODY_FLAGS and nested is not False:
                return False
            if not _body_free(nested):
                return False
        return True
    if isinstance(value, (list, tuple)):
        return all(_body_free(item) for item in value)
    if isinstance(value, str):
        return bool(_BODY_FREE_VALUE_RE.fullmatch(value))
    return True


@dataclass(frozen=True)
class ReceptionBatchCase:
    case_id: str
    reception_text: str
    full_surface_sha256: str
    reception_act: str
    terminal_predicate_kind: str


@dataclass(frozen=True)
class ReceptionBatchQaResult:
    cohort_id: str
    case_count: int
    case_order: tuple[str, ...]
    duplicate_sentence_groups: tuple[dict[str, Any], ...]
    self_repeated_sentence_cases: tuple[str, ...]
    closing_stem_families: tuple[dict[str, Any], ...]
    abstract_ending_counts: tuple[tuple[str, int], ...]
    abstract_ending_union_count: int
    reception_act_counts: tuple[tuple[str, int], ...]
    terminal_predicate_counts: tuple[tuple[str, int], ...]
    closing_hard_threshold: int
    verdict: str
    reason_codes: tuple[str, ...]
    sentence_hashes_by_case: tuple[tuple[str, tuple[str, ...]], ...]

    def as_body_free_meta(self) -> dict[str, Any]:
        payload = {
            "schema_version": R6_BATCH_QA_SCHEMA_VERSION,
            "cohort_id": self.cohort_id,
            "case_count": self.case_count,
            "case_order_sha256": sha256_text("\n".join(self.case_order)),
            "duplicate_sentence_groups": list(self.duplicate_sentence_groups),
            "self_repeated_sentence_cases": list(
                self.self_repeated_sentence_cases
            ),
            "closing_stem_families": list(self.closing_stem_families),
            "abstract_ending_counts": dict(self.abstract_ending_counts),
            "abstract_ending_union_count": self.abstract_ending_union_count,
            "reception_act_counts": dict(self.reception_act_counts),
            "terminal_predicate_counts": dict(self.terminal_predicate_counts),
            "closing_hard_threshold": self.closing_hard_threshold,
            "verdict": self.verdict,
            "reason_codes": list(self.reason_codes),
            "sentence_hashes_by_case": {
                case_id: list(hashes)
                for case_id, hashes in self.sentence_hashes_by_case
            },
            "raw_input_included": False,
            "surface_body_included": False,
            "comment_text_included": False,
            "anchor_text_included": False,
            "sentence_text_included": False,
            "closing_stem_text_included": False,
            "runtime_history_used": False,
            "product_readfeel_status": "not_evaluated",
        }
        if not _body_free(payload):
            raise ValueError("r6_batch_qa_meta_body_leak")
        return payload


def evaluate_reception_batch(
    cohort_id: str,
    cases: Sequence[ReceptionBatchCase],
    *,
    closing_hard_threshold: int,
) -> ReceptionBatchQaResult:
    """Evaluate cross-case repetition without exposing bodies in the result."""

    case_ids = tuple(case.case_id for case in cases)
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("r6_batch_case_id_duplicate")
    if closing_hard_threshold < 2:
        raise ValueError("r6_closing_threshold_invalid")

    sentence_members: dict[str, set[str]] = defaultdict(set)
    sentence_hashes_by_case: list[tuple[str, tuple[str, ...]]] = []
    self_repeated: list[str] = []
    final_closings: dict[str, str] = {}
    abstract_counts: Counter[str] = Counter()
    act_counts: Counter[str] = Counter()
    terminal_counts: Counter[str] = Counter()

    for case in cases:
        sentences = tuple(
            normalize_reception_sentence(sentence)
            for sentence in split_reception_sentences(case.reception_text)
            if normalize_reception_sentence(sentence)
        )
        sentence_hashes = tuple(sha256_text(sentence) for sentence in sentences)
        sentence_hashes_by_case.append((case.case_id, sentence_hashes))
        if len(sentence_hashes) != len(set(sentence_hashes)):
            self_repeated.append(case.case_id)
        for sentence_hash in sentence_hashes:
            sentence_members[sentence_hash].add(case.case_id)
        final_closing = normalize_closing(sentences[-1] if sentences else "")
        final_closings[case.case_id] = final_closing
        for family, pattern in _ABSTRACT_ENDING_PATTERNS:
            if pattern.search(final_closing):
                abstract_counts[family] += 1
                break
        act_counts[case.reception_act] += 1
        terminal_counts[case.terminal_predicate_kind] += 1

    duplicate_groups = tuple(
        {
            "normalized_sentence_sha256": sentence_hash,
            "case_ids": sorted(members),
            "case_count": len(members),
        }
        for sentence_hash, members in sorted(sentence_members.items())
        if len(members) >= 2
    )

    stems_by_members: dict[tuple[str, ...], str] = {}
    ordered_ids = tuple(final_closings)
    for index, left_id in enumerate(ordered_ids):
        for right_id in ordered_ids[index + 1 :]:
            stem = _longest_common_suffix(
                final_closings[left_id],
                final_closings[right_id],
            )
            if len(stem) < 12:
                continue
            members = tuple(
                case_id
                for case_id in ordered_ids
                if final_closings[case_id].endswith(stem)
            )
            current = stems_by_members.get(members, "")
            if len(stem) > len(current):
                stems_by_members[members] = stem
    closing_families = tuple(
        {
            "closing_stem_sha256": sha256_text(stem),
            "closing_stem_character_count": len(stem),
            "case_ids": list(members),
            "case_count": len(members),
        }
        for members, stem in sorted(
            stems_by_members.items(),
            key=lambda item: (-len(item[0]), item[0]),
        )
    )

    reasons: list[str] = []
    if duplicate_groups:
        reasons.append("r6_exact_reception_sentence_duplicate")
    if self_repeated:
        reasons.append("r6_reception_sentence_self_repetition")
    if any(
        family["case_count"] >= closing_hard_threshold
        for family in closing_families
    ):
        reasons.append("r6_closing_stem_concentration")
    abstract_union = sum(abstract_counts.values())
    if abstract_union > len(cases) / 2:
        reasons.append("r6_abstract_ending_concentration")

    return ReceptionBatchQaResult(
        cohort_id=cohort_id,
        case_count=len(cases),
        case_order=case_ids,
        duplicate_sentence_groups=duplicate_groups,
        self_repeated_sentence_cases=tuple(self_repeated),
        closing_stem_families=closing_families,
        abstract_ending_counts=tuple(sorted(abstract_counts.items())),
        abstract_ending_union_count=abstract_union,
        reception_act_counts=tuple(sorted(act_counts.items())),
        terminal_predicate_counts=tuple(sorted(terminal_counts.items())),
        closing_hard_threshold=closing_hard_threshold,
        verdict="passed" if not reasons else "failed",
        reason_codes=tuple(reasons),
        sentence_hashes_by_case=tuple(sentence_hashes_by_case),
    )


def validate_karen_review_receipt(
    receipt: Mapping[str, Any],
    *,
    expected_surface_hashes: Mapping[str, str],
    expected_packet_sha256: str,
) -> tuple[str, ...]:
    """Validate a body-free exact8 receipt bound to the visible packet read."""

    issues: list[str] = []
    if set(receipt) != set(_KAREN_RECEIPT_ALLOWED_KEYS):
        issues.append("r6_karen_review_top_level_schema_mismatch")
    if receipt.get("schema_version") != R6_KAREN_REVIEW_SCHEMA_VERSION:
        issues.append("r6_karen_review_schema_mismatch")
    if receipt.get("reviewer") != "karen_local_actual_read":
        issues.append("r6_karen_review_reviewer_mismatch")
    if receipt.get("review_scope") != "exact8_visible_surface":
        issues.append("r6_karen_review_scope_mismatch")
    if receipt.get("visible_packet_ref") != (
        "../local_only/"
        "grounded_human_reception_r6_exact8_visible_packet_20260712.json"
    ):
        issues.append("r6_karen_review_packet_ref_mismatch")
    if receipt.get("visible_packet_sha256") != expected_packet_sha256:
        issues.append("r6_karen_review_packet_hash_mismatch")
    if receipt.get("technical_pass_is_product_readfeel_pass") is not False:
        issues.append("r6_karen_review_technical_product_boundary_missing")
    if receipt.get("automatic_gate_result_used_as_human_result") is not False:
        issues.append("r6_karen_review_automatic_result_boundary_missing")
    if receipt.get("review_axes") != list(R6_REVIEW_AXES):
        issues.append("r6_karen_review_axis_contract_mismatch")
    if receipt.get("progression_authority") != "none":
        issues.append("r6_karen_review_progression_authority_invalid")
    if receipt.get("valid_for_progression") is not False:
        issues.append("r6_karen_review_progression_validity_invalid")
    if receipt.get("representative4_actual_device_status") != "not_run":
        issues.append("r6_karen_review_representative4_status_invalid")
    if receipt.get("exact8_actual_device_status") != "not_run":
        issues.append("r6_karen_review_exact8_device_status_invalid")
    reviews = receipt.get("reviews")
    if not isinstance(reviews, list):
        issues.append("r6_karen_review_rows_missing")
        reviews = []
    review_case_ids = tuple(
        str(review.get("case_id") or "")
        for review in reviews
        if isinstance(review, dict)
    )
    if len(reviews) != len(expected_surface_hashes):
        issues.append("r6_karen_review_row_count_mismatch")
    if len(review_case_ids) != len(reviews):
        issues.append("r6_karen_review_row_type_invalid")
    if len(review_case_ids) != len(set(review_case_ids)):
        issues.append("r6_karen_review_case_id_duplicate")
    review_by_id = {
        str(review.get("case_id") or ""): review
        for review in reviews
        if isinstance(review, dict)
    }
    if set(review_by_id) != set(expected_surface_hashes):
        issues.append("r6_karen_review_case_set_mismatch")
    for case_id, expected_hash in expected_surface_hashes.items():
        review = review_by_id.get(case_id, {})
        if set(review) != set(_KAREN_REVIEW_ROW_ALLOWED_KEYS):
            issues.append(f"r6_karen_review_row_schema_mismatch:{case_id}")
        if review.get("visible_surface_sha256") != expected_hash:
            issues.append(f"r6_karen_review_surface_hash_mismatch:{case_id}")
        axes = review.get("axes")
        if not isinstance(axes, dict) or set(axes) != set(R6_REVIEW_AXES):
            issues.append(f"r6_karen_review_axes_mismatch:{case_id}")
            continue
        if any(status not in {"pass", "fail"} for status in axes.values()):
            issues.append(f"r6_karen_review_axis_status_invalid:{case_id}")
        failed_axes = sorted(
            axis for axis, status in axes.items() if status == "fail"
        )
        if failed_axes and review.get("verdict") != "human_fail":
            issues.append(f"r6_karen_review_failure_hidden:{case_id}")
        if not failed_axes and review.get("verdict") != "human_pass":
            issues.append(f"r6_karen_review_pass_mismatch:{case_id}")
        fatal_reasons = review.get("fatal_reason_refs")
        if not isinstance(fatal_reasons, list) or any(
            not isinstance(reason, str)
            or not _BODY_FREE_VALUE_RE.fullmatch(reason)
            for reason in fatal_reasons or ()
        ):
            issues.append(f"r6_karen_review_reason_code_invalid:{case_id}")
        elif failed_axes and not fatal_reasons:
            issues.append(f"r6_karen_review_failure_reason_missing:{case_id}")
    all_reviews_passed = bool(review_by_id) and all(
        review.get("verdict") == "human_pass"
        for review in review_by_id.values()
    )
    expected_product_status = (
        "human_pass" if all_reviews_passed else "human_fail"
    )
    if receipt.get("product_readfeel_status") != expected_product_status:
        issues.append("r6_karen_review_aggregate_pass_invalid")
    if not _body_free(dict(receipt)):
        issues.append("r6_karen_review_receipt_body_leak")
    return tuple(dict.fromkeys(issues))


__all__ = [
    "R6_BATCH_QA_SCHEMA_VERSION",
    "R6_KAREN_REVIEW_SCHEMA_VERSION",
    "R6_REVIEW_AXES",
    "ReceptionBatchCase",
    "ReceptionBatchQaResult",
    "evaluate_reception_batch",
    "normalize_closing",
    "normalize_reception_sentence",
    "sha256_text",
    "split_reception_sentences",
    "validate_karen_review_receipt",
]
