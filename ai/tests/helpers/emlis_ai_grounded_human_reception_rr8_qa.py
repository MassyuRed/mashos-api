# -*- coding: utf-8 -*-
from __future__ import annotations

"""Body-free RR8 batch metrics and RR9 human-read receipt contracts."""

from collections import Counter, defaultdict
from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any, Mapping, Sequence

from helpers.emlis_ai_grounded_human_reception_r6_qa import (
    normalize_closing,
    normalize_reception_sentence,
    split_reception_sentences,
)


RR8_BATCH_QA_SCHEMA_VERSION = (
    "cocolon.emlis.grounded_human_reception.rr8_batch_qa.v1"
)
RR9_KAREN_REVIEW_SCHEMA_VERSION = (
    "cocolon.emlis.grounded_human_reception.rr9_karen_review.v1"
)
RR9_REVIEW_AXES = (
    "reception_role_distinctness",
    "human_warmth",
    "conversational_naturalness",
    "grounded_specificity",
    "whole_input_balance",
    "response_depth_proportionality",
    "meaning_selection_quality",
    "meaningful_support_utilization",
    "non_enumerative_readfeel",
    "language_variety",
    "safety_boundary",
    "non_template_readfeel",
    "wants_more_input_candidate",
)

_BODY_KEYS = frozenset(
    {
        "memo",
        "memo_action",
        "current_input",
        "exact_current_input",
        "raw_input",
        "raw_text",
        "source_text",
        "surface_text",
        "visible_surface",
        "comment_text",
        "observation_text",
        "reception_text",
        "sentence_text",
        "closing_stem_text",
        "anchor_text",
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
_BODY_BEARING_KEY_RE = re.compile(
    r"(?:^|_)(?:input|text|body|content|comment|note|quote|anchor|surface)$"
)
_RR9_PACKET_REF = (
    "../local_only/grounded_human_reception_rr9_visible_packet_20260713.json"
)
_RR9_RECEIPT_KEYS = frozenset(
    {
        "schema_version",
        "reviewer",
        "review_scope",
        "visible_packet_ref",
        "visible_packet_sha256",
        "source_snapshot_sha256",
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
_RR9_REVIEW_ROW_KEYS = frozenset(
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


def sha256_json(value: Any) -> str:
    return sha256_text(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    )


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
            if key not in _BODY_FLAGS and _BODY_BEARING_KEY_RE.search(key):
                return False
            if not _body_free(nested):
                return False
        return True
    if isinstance(value, (list, tuple)):
        return all(_body_free(item) for item in value)
    if isinstance(value, str):
        return bool(_BODY_FREE_VALUE_RE.fullmatch(value))
    return True


def assert_body_free_metadata(value: Mapping[str, Any]) -> None:
    if not _body_free(dict(value)):
        raise ValueError("rr8_body_free_metadata_contract_failed")


def _longest_common_suffix(left: str, right: str) -> str:
    limit = min(len(left), len(right))
    matched = 0
    while matched < limit and left[-(matched + 1)] == right[-(matched + 1)]:
        matched += 1
    return left[-matched:] if matched else ""


@dataclass(frozen=True)
class RR8BatchThresholds:
    closing_stem_family_limit: int
    terminal_lexeme_family_limit: int
    skeleton_family_limit: int
    opening_strategy_family_limit: int
    basis: str


@dataclass(frozen=True)
class RR8ReceptionQaCase:
    case_id: str
    reception_text: str
    full_surface_sha256: str
    depth_level: str
    opportunity_count: int
    planned_move_count: int
    realized_move_count: int
    sentence_count: int
    move_roles: tuple[str, ...]
    surface_strategies: tuple[str, ...]
    predicate_families: tuple[str, ...]
    connector_patterns: tuple[str, ...]
    speaker_presences: tuple[str, ...]
    required_move_ids: tuple[str, ...]
    realized_move_ids: tuple[str, ...]
    move_distinctness_gate: str
    non_enumeration_gate: str


@dataclass(frozen=True)
class RR8BatchQaResult:
    cohort_id: str
    case_order: tuple[str, ...]
    thresholds: RR8BatchThresholds
    depth_distribution: tuple[tuple[str, int], ...]
    duplicate_sentence_groups: tuple[dict[str, Any], ...]
    self_repeated_sentence_cases: tuple[str, ...]
    closing_stem_families: tuple[dict[str, Any], ...]
    terminal_lexeme_family_counts: tuple[tuple[str, int], ...]
    skeleton_families: tuple[dict[str, Any], ...]
    opening_strategy_counts: tuple[tuple[str, int], ...]
    depth_proportionality_failure_cases: tuple[str, ...]
    meaningful_support_eligible_cases: tuple[str, ...]
    meaningful_support_unutilized_cases: tuple[str, ...]
    move_distinctness_failure_cases: tuple[str, ...]
    non_enumerative_selection_failure_cases: tuple[str, ...]
    rich_one_line_cases: tuple[str, ...]
    rich_input_case_count: int
    one_line_rich_input_rate_basis_points: int
    short_water_filling_cases: tuple[str, ...]
    clipped_anchor_cases: tuple[str, ...]
    surface_sha256_by_case: tuple[tuple[str, str], ...]
    fingerprint_sha256_by_case: tuple[tuple[str, str], ...]
    verdict: str
    reason_codes: tuple[str, ...]

    @property
    def case_count(self) -> int:
        return len(self.case_order)

    def as_body_free_meta(self) -> dict[str, Any]:
        payload = {
            "schema_version": RR8_BATCH_QA_SCHEMA_VERSION,
            "cohort_id": self.cohort_id,
            "case_count": self.case_count,
            "case_order_sha256": sha256_text("\n".join(self.case_order)),
            "thresholds": {
                "closing_stem_family_limit": (
                    self.thresholds.closing_stem_family_limit
                ),
                "terminal_lexeme_family_limit": (
                    self.thresholds.terminal_lexeme_family_limit
                ),
                "skeleton_family_limit": self.thresholds.skeleton_family_limit,
                "opening_strategy_family_limit": (
                    self.thresholds.opening_strategy_family_limit
                ),
                "basis": self.thresholds.basis,
            },
            "depth_distribution": dict(self.depth_distribution),
            "duplicate_sentence_groups": list(self.duplicate_sentence_groups),
            "self_repeated_sentence_cases": list(
                self.self_repeated_sentence_cases
            ),
            "closing_stem_families": list(self.closing_stem_families),
            "terminal_lexeme_family_counts": dict(
                self.terminal_lexeme_family_counts
            ),
            "skeleton_families": list(self.skeleton_families),
            "opening_strategy_counts": dict(self.opening_strategy_counts),
            "response_depth_proportionality_failures": list(
                self.depth_proportionality_failure_cases
            ),
            "meaningful_support_eligible_cases": list(
                self.meaningful_support_eligible_cases
            ),
            "meaningful_support_unutilized_cases": list(
                self.meaningful_support_unutilized_cases
            ),
            "move_distinctness_failure_cases": list(
                self.move_distinctness_failure_cases
            ),
            "non_enumerative_selection_failure_cases": list(
                self.non_enumerative_selection_failure_cases
            ),
            "rich_one_line_cases": list(self.rich_one_line_cases),
            "rich_input_case_count": self.rich_input_case_count,
            "rich_one_line_case_count": len(self.rich_one_line_cases),
            "one_line_rich_input_rate_basis_points": (
                self.one_line_rich_input_rate_basis_points
            ),
            "short_water_filling_cases": list(self.short_water_filling_cases),
            "clipped_anchor_cases": list(self.clipped_anchor_cases),
            "surface_sha256_by_case": dict(self.surface_sha256_by_case),
            "fingerprint_sha256_by_case": dict(
                self.fingerprint_sha256_by_case
            ),
            "verdict": self.verdict,
            "reason_codes": list(self.reason_codes),
            "raw_input_included": False,
            "surface_body_included": False,
            "comment_text_included": False,
            "anchor_text_included": False,
            "sentence_text_included": False,
            "closing_stem_text_included": False,
            "runtime_history_used": False,
            "product_readfeel_status": "not_evaluated",
        }
        assert_body_free_metadata(payload)
        return payload


def _depth_is_proportional(case: RR8ReceptionQaCase) -> bool:
    bounds = {
        "minimal": (1, 1),
        "focused": (1, 2),
        "layered": (2, 3),
    }
    if case.depth_level not in bounds:
        return False
    lower, upper = bounds[case.depth_level]
    return bool(
        lower <= case.sentence_count <= upper
        and lower <= case.realized_move_count <= upper
        and case.realized_move_count <= case.planned_move_count
    )


def _visible_terminal_lexeme_family(sentences: tuple[str, ...]) -> str:
    final = sentences[-1] if sentences else ""
    if "思えません" in final:
        return "bounded_counterposition"
    if re.search(r"感じ(?:ます|ています|たいです)$", final):
        return "feel"
    if re.search(r"受け止め(?:ます|ています|たいです)$", final):
        return "receive"
    if re.search(r"(?:したい|いたい|おきたい)です$", final):
        return "intention"
    if re.search(r"大切に思います$", final):
        return "value"
    return "other"


def evaluate_rr8_reception_batch(
    cohort_id: str,
    cases: Sequence[RR8ReceptionQaCase],
    *,
    thresholds: RR8BatchThresholds,
) -> RR8BatchQaResult:
    """Evaluate RR8 proportions and body-free cross-case fingerprints."""

    rows = tuple(cases)
    case_ids = tuple(case.case_id for case in rows)
    if not rows:
        raise ValueError("rr8_batch_empty")
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("rr8_batch_case_id_duplicate")
    if min(
        thresholds.closing_stem_family_limit,
        thresholds.terminal_lexeme_family_limit,
        thresholds.skeleton_family_limit,
        thresholds.opening_strategy_family_limit,
    ) < 1:
        raise ValueError("rr8_batch_threshold_invalid")

    sentence_members: dict[str, set[str]] = defaultdict(set)
    self_repeated: list[str] = []
    closings: dict[str, str] = {}
    terminal_counts: Counter[str] = Counter()
    skeleton_members: dict[str, list[str]] = defaultdict(list)
    opening_counts: Counter[str] = Counter()
    depth_counts: Counter[str] = Counter()
    fingerprints: list[tuple[str, str]] = []
    surface_hashes: list[tuple[str, str]] = []
    depth_failures: list[str] = []
    support_eligible: list[str] = []
    support_unutilized: list[str] = []
    distinctness_failures: list[str] = []
    nonenumeration_failures: list[str] = []
    rich_one_line: list[str] = []
    water_filling: list[str] = []
    clipped_anchors: list[str] = []

    for case in rows:
        if not re.fullmatch(r"[0-9a-f]{64}", case.full_surface_sha256):
            raise ValueError(f"rr8_case_surface_hash_invalid:{case.case_id}")
        surface_hashes.append((case.case_id, case.full_surface_sha256))
        if not (
            len(case.move_roles)
            == len(case.surface_strategies)
            == len(case.predicate_families)
            == case.realized_move_count
        ):
            raise ValueError(f"rr8_case_move_shape_invalid:{case.case_id}")
        sentences = tuple(
            normalize_reception_sentence(sentence)
            for sentence in split_reception_sentences(case.reception_text)
            if normalize_reception_sentence(sentence)
        )
        hashes = tuple(sha256_text(sentence) for sentence in sentences)
        if len(hashes) != len(set(hashes)):
            self_repeated.append(case.case_id)
        for sentence_hash in hashes:
            sentence_members[sentence_hash].add(case.case_id)
        closings[case.case_id] = normalize_closing(
            sentences[-1] if sentences else ""
        )

        terminal_family = _visible_terminal_lexeme_family(sentences)
        terminal_counts[terminal_family] += 1
        opening = (
            case.surface_strategies[0]
            if case.surface_strategies
            else "missing"
        )
        opening_counts[opening] += 1
        depth_counts[case.depth_level] += 1
        fingerprint = {
            "move_roles": list(case.move_roles),
            "surface_strategies": list(case.surface_strategies),
            "predicate_families": list(case.predicate_families),
            "sentence_count": case.sentence_count,
            "connector_patterns": list(case.connector_patterns),
            "speaker_presences": list(case.speaker_presences),
        }
        fingerprint_hash = sha256_json(fingerprint)
        fingerprints.append((case.case_id, fingerprint_hash))
        skeleton_members[fingerprint_hash].append(case.case_id)

        if not _depth_is_proportional(case):
            depth_failures.append(case.case_id)
        if case.planned_move_count >= 2:
            support_eligible.append(case.case_id)
            if not (
                case.realized_move_count >= 2
                and set(case.required_move_ids) <= set(case.realized_move_ids)
            ):
                support_unutilized.append(case.case_id)
        contributions = tuple(
            zip(
                case.move_roles,
                case.surface_strategies,
                case.predicate_families,
            )
        )
        if (
            case.move_distinctness_gate != "passed"
            or len(contributions) != len(set(contributions))
        ):
            distinctness_failures.append(case.case_id)
        if (
            case.non_enumeration_gate != "passed"
            or case.planned_move_count > 3
            or case.realized_move_count > 3
        ):
            nonenumeration_failures.append(case.case_id)
        if case.planned_move_count >= 2 and case.sentence_count < 2:
            rich_one_line.append(case.case_id)
        if case.depth_level == "minimal" and (
            case.sentence_count != 1 or case.realized_move_count != 1
        ):
            water_filling.append(case.case_id)
        if re.search(r"…(?=」)", case.reception_text):
            clipped_anchors.append(case.case_id)

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
    for index, left_id in enumerate(case_ids):
        for right_id in case_ids[index + 1 :]:
            stem = _longest_common_suffix(
                closings[left_id],
                closings[right_id],
            )
            if len(stem) < 12:
                continue
            members = tuple(
                case_id
                for case_id in case_ids
                if closings[case_id].endswith(stem)
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
    skeleton_families = tuple(
        {
            "fingerprint_sha256": fingerprint_hash,
            "case_ids": list(members),
            "case_count": len(members),
        }
        for fingerprint_hash, members in sorted(skeleton_members.items())
    )

    reasons: list[str] = []
    checks = (
        (bool(duplicate_groups), "rr8_exact_reception_sentence_duplicate"),
        (bool(self_repeated), "rr8_reception_sentence_self_repetition"),
        (
            any(
                row["case_count"]
                > thresholds.closing_stem_family_limit
                for row in closing_families
            ),
            "rr8_closing_stem_concentration",
        ),
        (
            max(terminal_counts.values(), default=0)
            > thresholds.terminal_lexeme_family_limit,
            "rr8_terminal_lexeme_family_concentration",
        ),
        (
            max(
                (len(members) for members in skeleton_members.values()),
                default=0,
            )
            > thresholds.skeleton_family_limit,
            "rr8_sentence_skeleton_concentration",
        ),
        (
            max(opening_counts.values(), default=0)
            > thresholds.opening_strategy_family_limit,
            "rr8_opening_strategy_concentration",
        ),
        (bool(depth_failures), "rr8_response_depth_not_proportional"),
        (bool(support_unutilized), "rr8_meaningful_support_unutilized"),
        (bool(distinctness_failures), "rr8_move_distinctness_failed"),
        (bool(nonenumeration_failures), "rr8_non_enumerative_selection_failed"),
        (bool(rich_one_line), "rr8_rich_input_one_line_collapse"),
        (bool(water_filling), "rr8_short_input_water_filling"),
        (bool(clipped_anchors), "rr8_source_anchor_clipped"),
    )
    reasons.extend(code for failed, code in checks if failed)

    return RR8BatchQaResult(
        cohort_id=cohort_id,
        case_order=case_ids,
        thresholds=thresholds,
        depth_distribution=tuple(sorted(depth_counts.items())),
        duplicate_sentence_groups=duplicate_groups,
        self_repeated_sentence_cases=tuple(self_repeated),
        closing_stem_families=closing_families,
        terminal_lexeme_family_counts=tuple(sorted(terminal_counts.items())),
        skeleton_families=skeleton_families,
        opening_strategy_counts=tuple(sorted(opening_counts.items())),
        depth_proportionality_failure_cases=tuple(depth_failures),
        meaningful_support_eligible_cases=tuple(support_eligible),
        meaningful_support_unutilized_cases=tuple(support_unutilized),
        move_distinctness_failure_cases=tuple(distinctness_failures),
        non_enumerative_selection_failure_cases=tuple(
            nonenumeration_failures
        ),
        rich_one_line_cases=tuple(rich_one_line),
        rich_input_case_count=len(support_eligible),
        one_line_rich_input_rate_basis_points=(
            round(len(rich_one_line) * 10000 / len(support_eligible))
            if support_eligible
            else 0
        ),
        short_water_filling_cases=tuple(water_filling),
        clipped_anchor_cases=tuple(clipped_anchors),
        surface_sha256_by_case=tuple(surface_hashes),
        fingerprint_sha256_by_case=tuple(fingerprints),
        verdict="passed" if not reasons else "failed",
        reason_codes=tuple(reasons),
    )


def validate_rr9_karen_review_receipt(
    receipt: Mapping[str, Any],
    *,
    expected_surface_hashes: Mapping[str, str],
    expected_packet_sha256: str,
    expected_source_snapshot_sha256: str,
) -> tuple[str, ...]:
    """Validate a 13-axis, hash-bound, body-free local human-read receipt."""

    issues: list[str] = []
    if not expected_surface_hashes:
        issues.append("rr9_karen_review_expected_case_set_empty")
    if set(receipt) != set(_RR9_RECEIPT_KEYS):
        issues.append("rr9_karen_review_top_level_schema_mismatch")
    if receipt.get("schema_version") != RR9_KAREN_REVIEW_SCHEMA_VERSION:
        issues.append("rr9_karen_review_schema_mismatch")
    if receipt.get("reviewer") != "karen_local_product_readfeel":
        issues.append("rr9_karen_review_reviewer_mismatch")
    if receipt.get("review_scope") != (
        "exact8_plus_unseen_representative_visible_surface"
    ):
        issues.append("rr9_karen_review_scope_mismatch")
    if receipt.get("visible_packet_ref") != _RR9_PACKET_REF:
        issues.append("rr9_karen_review_packet_ref_mismatch")
    if receipt.get("visible_packet_sha256") != expected_packet_sha256:
        issues.append("rr9_karen_review_packet_hash_mismatch")
    if receipt.get("source_snapshot_sha256") != (
        expected_source_snapshot_sha256
    ):
        issues.append("rr9_karen_review_source_snapshot_mismatch")
    if receipt.get("review_axes") != list(RR9_REVIEW_AXES):
        issues.append("rr9_karen_review_axis_contract_mismatch")
    if receipt.get("technical_pass_is_product_readfeel_pass") is not False:
        issues.append("rr9_karen_review_technical_product_boundary_missing")
    if receipt.get("automatic_gate_result_used_as_human_result") is not False:
        issues.append("rr9_karen_review_automatic_result_boundary_missing")
    if receipt.get("progression_authority") != "none":
        issues.append("rr9_karen_review_progression_authority_invalid")
    if receipt.get("valid_for_progression") is not False:
        issues.append("rr9_karen_review_progression_validity_invalid")
    if receipt.get("representative4_actual_device_status") != "not_run":
        issues.append("rr9_karen_review_representative4_status_invalid")
    if receipt.get("exact8_actual_device_status") != "not_run":
        issues.append("rr9_karen_review_exact8_device_status_invalid")

    reviews = receipt.get("reviews")
    if not isinstance(reviews, list):
        issues.append("rr9_karen_review_rows_missing")
        reviews = []
    typed_reviews = [row for row in reviews if isinstance(row, dict)]
    if len(typed_reviews) != len(reviews):
        issues.append("rr9_karen_review_row_type_invalid")
    review_ids = tuple(str(row.get("case_id") or "") for row in typed_reviews)
    if len(review_ids) != len(set(review_ids)):
        issues.append("rr9_karen_review_case_id_duplicate")
    if len(reviews) != len(expected_surface_hashes):
        issues.append("rr9_karen_review_row_count_mismatch")
    review_by_id = {
        str(row.get("case_id") or ""): row for row in typed_reviews
    }
    if set(review_by_id) != set(expected_surface_hashes):
        issues.append("rr9_karen_review_case_set_mismatch")

    for case_id, expected_hash in expected_surface_hashes.items():
        row = review_by_id.get(case_id, {})
        if set(row) != set(_RR9_REVIEW_ROW_KEYS):
            issues.append(f"rr9_karen_review_row_schema_mismatch:{case_id}")
        if row.get("visible_surface_sha256") != expected_hash:
            issues.append(f"rr9_karen_review_surface_hash_mismatch:{case_id}")
        axes = row.get("axes")
        if not isinstance(axes, dict) or set(axes) != set(RR9_REVIEW_AXES):
            issues.append(f"rr9_karen_review_axes_mismatch:{case_id}")
            continue
        if any(status not in {"pass", "fail"} for status in axes.values()):
            issues.append(f"rr9_karen_review_axis_status_invalid:{case_id}")
        failed_axes = sorted(
            axis for axis, status in axes.items() if status == "fail"
        )
        if failed_axes and row.get("verdict") != "human_fail":
            issues.append(f"rr9_karen_review_failure_hidden:{case_id}")
        if not failed_axes and row.get("verdict") != "human_pass":
            issues.append(f"rr9_karen_review_pass_mismatch:{case_id}")
        reasons = row.get("fatal_reason_refs")
        if not isinstance(reasons, list) or any(
            not isinstance(reason, str)
            or not _BODY_FREE_VALUE_RE.fullmatch(reason)
            for reason in reasons or ()
        ):
            issues.append(f"rr9_karen_review_reason_code_invalid:{case_id}")
        elif failed_axes and not reasons:
            issues.append(f"rr9_karen_review_failure_reason_missing:{case_id}")
        elif not failed_axes and reasons:
            issues.append(f"rr9_karen_review_pass_has_fatal_reason:{case_id}")

    all_pass = bool(review_by_id) and all(
        row.get("verdict") == "human_pass" for row in review_by_id.values()
    )
    if receipt.get("product_readfeel_status") != (
        "human_pass" if all_pass else "human_fail"
    ):
        issues.append("rr9_karen_review_aggregate_pass_invalid")
    if not _body_free(dict(receipt)):
        issues.append("rr9_karen_review_receipt_body_leak")
    return tuple(dict.fromkeys(issues))


__all__ = [
    "RR8_BATCH_QA_SCHEMA_VERSION",
    "RR9_KAREN_REVIEW_SCHEMA_VERSION",
    "RR9_REVIEW_AXES",
    "RR8BatchThresholds",
    "RR8ReceptionQaCase",
    "RR8BatchQaResult",
    "assert_body_free_metadata",
    "evaluate_rr8_reception_batch",
    "sha256_json",
    "sha256_text",
    "validate_rr9_karen_review_receipt",
]
