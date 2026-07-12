# -*- coding: utf-8 -*-
from __future__ import annotations

"""Body-free I7 read-feel and real-device progression boundary.

This helper never stores an input or returned body.  It lets a local reviewer
read the body in memory, records only axis/fatal outcomes, and prevents stale
device evidence from opening the P5 formal-24 lane.
"""

from dataclasses import asdict, dataclass
import re
from typing import Any, Mapping, Sequence


I7_READFEEL_AXES = (
    "grounded_specificity",
    "whole_input_balance",
    "natural_japanese",
    "human_follow_fit",
    "safety_boundary",
)
I7_REQUIRED_DEVICE_CASE_COUNT = 8
I7_P5_FORMAL_CASE_COUNT = 24
I7_CANONICAL_GENERATION_PATH = "grounded_observation_plan_sentence_surface_canonical_v1"
I7_CANONICAL_COMPOSER_SOURCE = "grounded_plan_realizer"
I7_KAREN_LOCAL_REVIEW_KIND = "karen_local_product_read"
I7_KAREN_LOCAL_REVIEW_AXES = (
    "required_nucleus_retained",
    "required_relation_direction",
    "lexical_fidelity",
    "whole_input_balance",
    "human_follow_fit",
    "natural_japanese",
    "non_template_readfeel",
    "safety_boundary",
    "wants_more_input_candidate",
)

_TECHNICAL_SURFACE_RE = re.compile(
    r"(?:入力内の関係として|順序上のつながり|required nucleus|semantic nucleus|coverage requirement)",
    re.IGNORECASE,
)
_DEPENDENT_QUOTE_RE = re.compile(
    r"「(?:とか|という|と考え)|(?:何故|なぜ|どうして)」"
)


@dataclass(frozen=True)
class I7LocalReadFeelAssessment:
    case_id: str
    review_kind: str
    axis_refs: tuple[str, ...]
    fatal_reason_refs: tuple[str, ...]
    character_count: int
    line_count: int
    candidate_status: str
    human_review_claimed: bool = False
    raw_input_included: bool = False
    returned_surface_included: bool = False
    comment_text_included: bool = False

    def as_body_free_meta(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class I7DeviceEvidenceAssessment:
    case_id: str
    evidence_status: str
    reason_refs: tuple[str, ...]
    canonical_generation_path_verified: bool
    canonical_composer_verified: bool
    semantic_gate_verified: bool
    public_path_verified: bool
    raw_input_included: bool = False
    returned_surface_included: bool = False
    comment_text_included: bool = False

    def as_body_free_meta(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class I7KarenLocalReview:
    case_id: str
    snapshot_fingerprint: str
    required_nucleus_retained: str
    required_relation_direction: str
    lexical_fidelity: str
    whole_input_balance: str
    human_follow_fit: str
    natural_japanese: str
    non_template_readfeel: str
    safety_boundary: str
    wants_more_input_candidate: str
    fatal_reason_refs: tuple[str, ...]
    verdict: str
    review_kind: str = I7_KAREN_LOCAL_REVIEW_KIND
    raw_input_included: bool = False
    returned_surface_included: bool = False
    comment_text_included: bool = False

    @property
    def passed(self) -> bool:
        return self.verdict == "local_human_pass"

    def as_body_free_meta(self) -> dict[str, Any]:
        return asdict(self)


def validate_i7_karen_local_reviews(
    reviews: Sequence[I7KarenLocalReview],
    *,
    expected_case_ids: Sequence[str],
) -> tuple[str, ...]:
    """Validate explicit review receipts without deriving a verdict from a body."""

    reasons: list[str] = []
    expected = tuple(str(item) for item in expected_case_ids)
    actual = tuple(item.case_id for item in reviews)
    if len(reviews) != 16:
        reasons.append("actual_local_review_count_mismatch")
    if len(set(actual)) != len(actual):
        reasons.append("actual_local_review_duplicate_case")
    if actual != expected:
        reasons.append("actual_local_review_case_order_mismatch")
    if len({item.snapshot_fingerprint for item in reviews}) > 1:
        reasons.append("actual_local_review_snapshot_mismatch")
    for item in reviews:
        if item.review_kind != I7_KAREN_LOCAL_REVIEW_KIND:
            reasons.append("actual_local_review_kind_mismatch")
        if len(item.snapshot_fingerprint) != 64:
            reasons.append("actual_local_review_snapshot_missing")
        else:
            try:
                int(item.snapshot_fingerprint, 16)
            except ValueError:
                reasons.append("actual_local_review_snapshot_invalid")
        axis_values = {
            axis: str(getattr(item, axis, ""))
            for axis in I7_KAREN_LOCAL_REVIEW_AXES
        }
        for axis, value in axis_values.items():
            allowed = {"pass", "fail"}
            if axis in {"required_relation_direction", "safety_boundary"}:
                allowed.add("not_applicable")
            if value not in allowed:
                reasons.append("actual_local_review_axis_invalid")
        if item.verdict == "local_human_pass":
            if item.fatal_reason_refs or any(value == "fail" for value in axis_values.values()):
                reasons.append("actual_local_review_pass_inconsistent")
        elif item.verdict in {"repair_required", "hard_fatal"}:
            if not item.fatal_reason_refs or not any(value == "fail" for value in axis_values.values()):
                reasons.append("actual_local_review_failure_inconsistent")
        else:
            reasons.append("actual_local_review_verdict_invalid")
        if item.raw_input_included or item.returned_surface_included or item.comment_text_included:
            reasons.append("actual_local_review_body_leak")
    return tuple(dict.fromkeys(reasons))


def assess_i7_local_surface(
    *,
    case_id: str,
    surface_text: str,
    grounded_meta: Mapping[str, Any],
) -> I7LocalReadFeelAssessment:
    """Record deterministic fatal-axis results without retaining the body."""

    text = str(surface_text or "").strip()
    lines = tuple(line.strip() for line in text.splitlines() if line.strip())
    reasons: list[str] = []
    if not text:
        reasons.append("empty_surface")
    if len(text) > 360:
        reasons.append("surface_overlong")
    if len(lines) > 4:
        reasons.append("surface_too_many_lines")
    if "?" in text or "？" in text:
        reasons.append("question_substituted_for_observation")
    if _TECHNICAL_SURFACE_RE.search(text):
        reasons.append("internal_taxonomy_visible")
    if _DEPENDENT_QUOTE_RE.search(text):
        reasons.append("dependent_evidence_fragment_visible")
    if len(lines) != len(set(lines)):
        reasons.append("duplicate_sentence_visible")
    if grounded_meta.get("semantic_quality_gate") != "passed":
        reasons.append("semantic_gate_not_passed")
    if grounded_meta.get("generation_path") != I7_CANONICAL_GENERATION_PATH:
        reasons.append("canonical_generation_path_missing")
    if grounded_meta.get("composer_source") != I7_CANONICAL_COMPOSER_SOURCE:
        reasons.append("canonical_composer_missing")

    return I7LocalReadFeelAssessment(
        case_id=case_id,
        review_kind="assistant_local_product_read_candidate",
        axis_refs=I7_READFEEL_AXES,
        fatal_reason_refs=tuple(reasons),
        character_count=len(text),
        line_count=len(lines),
        candidate_status="candidate_pass" if not reasons else "repair_required",
    )


def assess_i7_device_evidence(
    *,
    case_id: str,
    evidence_meta: Mapping[str, Any],
) -> I7DeviceEvidenceAssessment:
    """Accept only evidence that proves the current canonical runtime path."""

    path_ok = evidence_meta.get("generation_path") == I7_CANONICAL_GENERATION_PATH
    composer_ok = evidence_meta.get("composer_source") == I7_CANONICAL_COMPOSER_SOURCE
    semantic_ok = evidence_meta.get("semantic_quality_gate") == "passed"
    public_ok = evidence_meta.get("public_reply_path_connected") is True
    reasons: list[str] = []
    if not path_ok:
        reasons.append("canonical_generation_path_not_verified")
    if not composer_ok:
        reasons.append("grounded_plan_realizer_not_verified")
    if not semantic_ok:
        reasons.append("semantic_quality_gate_not_verified")
    if not public_ok:
        reasons.append("public_reply_path_not_verified")
    return I7DeviceEvidenceAssessment(
        case_id=case_id,
        evidence_status="verified" if not reasons else "runtime_mismatch",
        reason_refs=tuple(reasons),
        canonical_generation_path_verified=path_ok,
        canonical_composer_verified=composer_ok,
        semantic_gate_verified=semantic_ok,
        public_path_verified=public_ok,
    )


def decide_i7_progression(
    *,
    local_assessments: Sequence[I7LocalReadFeelAssessment],
    actual_local_reviews: Sequence[I7KarenLocalReview] = (),
    device_assessments: Sequence[I7DeviceEvidenceAssessment],
) -> dict[str, Any]:
    """Apply D-I7-1 without constructing or executing a P5 packet early."""

    automated_candidate_ready = len(local_assessments) == 16 and all(
        item.candidate_status == "candidate_pass" for item in local_assessments
    )
    expected_case_ids = tuple(item.case_id for item in local_assessments)
    local_review_reasons = validate_i7_karen_local_reviews(
        actual_local_reviews,
        expected_case_ids=expected_case_ids,
    )
    actual_local_ready = bool(
        automated_candidate_ready
        and not local_review_reasons
        and all(item.verdict == "local_human_pass" for item in actual_local_reviews)
    )
    device_ready = len(device_assessments) == I7_REQUIRED_DEVICE_CASE_COUNT and all(
        item.evidence_status == "verified" for item in device_assessments
    )
    p5_allowed = actual_local_ready and device_ready
    if not automated_candidate_ready or not actual_local_ready:
        next_action = "return_to_current_input_surface_repair"
    elif not device_ready:
        next_action = "canonical_known4_unseen4_real_device_recheck"
    else:
        next_action = "start_p5_formal_24_owned_history_blind_qa"
    return {
        "schema_version": "cocolon.emlis.i7_progression.bodyfree.v1",
        "local_case_count": len(local_assessments),
        "local_product_read_candidate_ready": automated_candidate_ready,
        "actual_local_review_count": len(actual_local_reviews),
        "actual_local_human_ready": actual_local_ready,
        "local_human_review_claimed": bool(actual_local_reviews),
        "local_human_pass_count": sum(item.verdict == "local_human_pass" for item in actual_local_reviews),
        "local_repair_required_count": sum(item.verdict == "repair_required" for item in actual_local_reviews),
        "local_hard_fatal_count": sum(item.verdict == "hard_fatal" for item in actual_local_reviews),
        "local_review_reason_refs": list(local_review_reasons),
        "required_device_case_count": I7_REQUIRED_DEVICE_CASE_COUNT,
        "verified_device_case_count": sum(
            item.evidence_status == "verified" for item in device_assessments
        ),
        "current_input_baseline_verified": p5_allowed,
        "p5_formal_required_case_count": I7_P5_FORMAL_CASE_COUNT,
        "p5_formal_24_start_allowed": p5_allowed,
        "p5_formal_24_started_here": False,
        "p6_start_allowed": False,
        "p7_complete": False,
        "p8_start_allowed": False,
        "next_action_ref": next_action,
        "raw_input_included": False,
        "returned_surface_included": False,
        "comment_text_included": False,
    }
