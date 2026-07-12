# -*- coding: utf-8 -*-
from __future__ import annotations

"""Body-free I7 read-feel and real-device progression boundary.

This helper never stores an input or returned body.  It lets a local reviewer
read the body in memory, records only axis/fatal outcomes, and prevents stale
device evidence from opening the P5 formal-24 lane.
"""

from dataclasses import asdict, dataclass
import hashlib
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
_QUOTED_ANCHOR_RE = re.compile(r"「[^」]*」")
_OBSERVATION_LABEL = "見えたこと："
_RECEPTION_LABEL = "Emlisから："
_LEDGER_NARRATION_RE = re.compile(
    r"(?:記|記録|記載)されています|(?:記録|入力)に(?:あります|置かれています)|"
    r"この記録には|同じ記録には|(?:入力|記録)に書かれています|"
    r"この順に書かれています|入力として受け取ります"
)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _split_two_stage_surface(surface_text: str) -> tuple[str, str, tuple[str, ...]]:
    text = str(surface_text or "")
    reasons: list[str] = []
    lines = text.splitlines()
    observation_positions = tuple(
        index for index, line in enumerate(lines) if line.strip() == _OBSERVATION_LABEL
    )
    reception_positions = tuple(
        index for index, line in enumerate(lines) if line.strip() == _RECEPTION_LABEL
    )
    if len(observation_positions) != 1 or len(reception_positions) != 1:
        return "", "", ("two_stage_labels_missing_or_duplicated",)
    observation_index = observation_positions[0]
    reception_index = reception_positions[0]
    if observation_index != 0 or reception_index <= observation_index:
        return "", "", ("two_stage_label_order_invalid",)
    observation = "\n".join(lines[observation_index + 1 : reception_index]).strip()
    reception = "\n".join(lines[reception_index + 1 :]).strip()
    if not observation:
        reasons.append("two_stage_observation_section_empty")
    if not reception:
        reasons.append("two_stage_reception_section_empty")
    return observation, reception, tuple(reasons)


@dataclass(frozen=True)
class I7LocalReadFeelAssessment:
    case_id: str
    review_kind: str
    axis_refs: tuple[str, ...]
    fatal_reason_refs: tuple[str, ...]
    character_count: int
    line_count: int
    candidate_status: str
    surface_sha256: str
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
    two_stage_contract_verified: bool
    mechanical_restatement_gate_verified: bool
    runtime_visible_contract_guard_verified: bool
    visible_surface_hash_verified: bool
    visible_surface_sha256: str = ""
    expected_local_surface_sha256: str = ""
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
    reviewed_surface_sha256: str = ""
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
    expected_surface_sha256_by_case: Mapping[str, str] | None = None,
) -> tuple[str, ...]:
    """Validate explicit reviews and, when supplied, bind them to exact bodies.

    The body itself remains absent from the receipt.  Its SHA-256 is required
    at progression boundaries so a pass cannot be carried forward after the
    visible text changes, and a body-free axis sheet cannot claim to represent
    text that was never linked to the review.
    """

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
    expected_hashes = {
        str(case_id): str(value or "")
        for case_id, value in dict(expected_surface_sha256_by_case or {}).items()
    }
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
        reviewed_hash = str(item.reviewed_surface_sha256 or "")
        if reviewed_hash and not _SHA256_RE.fullmatch(reviewed_hash):
            reasons.append("actual_local_review_surface_sha256_invalid")
        if expected_surface_sha256_by_case is not None:
            expected_hash = expected_hashes.get(item.case_id, "")
            if not _SHA256_RE.fullmatch(expected_hash):
                reasons.append("expected_local_surface_sha256_missing")
            elif not reviewed_hash:
                reasons.append("actual_local_review_surface_sha256_missing")
            elif reviewed_hash != expected_hash:
                reasons.append("actual_local_review_surface_sha256_mismatch")
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
    observation, reception, two_stage_reasons = _split_two_stage_surface(text)
    content_lines = tuple(
        line.strip()
        for section in (observation, reception)
        for line in section.splitlines()
        if line.strip()
    )
    reasons: list[str] = []
    reasons.extend(two_stage_reasons)
    if not text:
        reasons.append("empty_surface")
    required_nucleus_count = int(grounded_meta.get("required_nucleus_count") or 0)
    required_relation_count = int(grounded_meta.get("required_relation_count") or 0)
    complex_surface = required_nucleus_count >= 5 or required_relation_count >= 3
    character_limit = 520 if complex_surface else 360
    line_limit = 6 if complex_surface else 4
    if len(text) > character_limit:
        reasons.append("surface_overlong")
    if len(content_lines) > line_limit:
        reasons.append("surface_too_many_lines")
    if "?" in text or "？" in text:
        reasons.append("question_substituted_for_observation")
    if _TECHNICAL_SURFACE_RE.search(text):
        reasons.append("internal_taxonomy_visible")
    if _DEPENDENT_QUOTE_RE.search(text):
        reasons.append("dependent_evidence_fragment_visible")
    if _LEDGER_NARRATION_RE.search(_QUOTED_ANCHOR_RE.sub("", text)):
        reasons.append("ledger_narration_visible")
    if len(content_lines) != len(set(content_lines)):
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
        line_count=len(content_lines),
        candidate_status="candidate_pass" if not reasons else "repair_required",
        surface_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
    )


def assess_i7_device_evidence(
    *,
    case_id: str,
    evidence_meta: Mapping[str, Any],
) -> I7DeviceEvidenceAssessment:
    """Accept only evidence that proves both runtime lineage and visible body.

    Path/composer/semantic metadata alone cannot prove what the user actually
    saw.  The device receipt must also carry the mandatory two-stage and
    mechanical-restatement gate results plus a SHA-256 of the exact visible
    ``comment_text`` that matches the locally reviewed candidate.
    """

    path_ok = evidence_meta.get("generation_path") == I7_CANONICAL_GENERATION_PATH
    composer_ok = evidence_meta.get("composer_source") == I7_CANONICAL_COMPOSER_SOURCE
    semantic_ok = evidence_meta.get("semantic_quality_gate") == "passed"
    public_ok = evidence_meta.get("public_reply_path_connected") is True
    two_stage_ok = evidence_meta.get("two_stage_contract_gate") == "passed"
    mechanical_ok = evidence_meta.get("mechanical_restatement_gate") == "passed"
    runtime_guard_ok = evidence_meta.get("runtime_visible_contract_guard") == "passed"
    visible_hash = str(evidence_meta.get("visible_surface_sha256") or "").strip()
    expected_hash = str(evidence_meta.get("expected_local_surface_sha256") or "").strip()
    visible_hash_valid = bool(_SHA256_RE.fullmatch(visible_hash))
    expected_hash_valid = bool(_SHA256_RE.fullmatch(expected_hash))
    surface_hash_ok = bool(visible_hash_valid and expected_hash_valid and visible_hash == expected_hash)

    reasons: list[str] = []
    if not path_ok:
        reasons.append("canonical_generation_path_not_verified")
    if not composer_ok:
        reasons.append("grounded_plan_realizer_not_verified")
    if not semantic_ok:
        reasons.append("semantic_quality_gate_not_verified")
    if not public_ok:
        reasons.append("public_reply_path_not_verified")
    if not two_stage_ok:
        reasons.append("two_stage_contract_not_verified")
    if not mechanical_ok:
        reasons.append("mechanical_restatement_gate_not_verified")
    if not runtime_guard_ok:
        reasons.append("runtime_visible_contract_guard_not_verified")
    if not visible_hash_valid:
        reasons.append("device_visible_surface_sha256_missing_or_invalid")
    if not expected_hash_valid:
        reasons.append("expected_local_surface_sha256_missing_or_invalid")
    if visible_hash_valid and expected_hash_valid and visible_hash != expected_hash:
        reasons.append("device_visible_surface_sha256_mismatch")

    return I7DeviceEvidenceAssessment(
        case_id=case_id,
        evidence_status="verified" if not reasons else "runtime_mismatch",
        reason_refs=tuple(reasons),
        canonical_generation_path_verified=path_ok,
        canonical_composer_verified=composer_ok,
        semantic_gate_verified=semantic_ok,
        public_path_verified=public_ok,
        two_stage_contract_verified=two_stage_ok,
        mechanical_restatement_gate_verified=mechanical_ok,
        runtime_visible_contract_guard_verified=runtime_guard_ok,
        visible_surface_hash_verified=surface_hash_ok,
        visible_surface_sha256=visible_hash if visible_hash_valid else "",
        expected_local_surface_sha256=expected_hash if expected_hash_valid else "",
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
        expected_surface_sha256_by_case={
            item.case_id: item.surface_sha256
            for item in local_assessments
        },
    )
    actual_local_ready = bool(
        automated_candidate_ready
        and not local_review_reasons
        and all(item.verdict == "local_human_pass" for item in actual_local_reviews)
    )
    device_case_ids = tuple(item.case_id for item in device_assessments)
    device_case_set_valid = bool(
        len(device_assessments) == I7_REQUIRED_DEVICE_CASE_COUNT
        and len(set(device_case_ids)) == I7_REQUIRED_DEVICE_CASE_COUNT
        and set(device_case_ids) <= set(expected_case_ids)
    )
    device_reason_refs: list[str] = []
    if len(device_assessments) != I7_REQUIRED_DEVICE_CASE_COUNT:
        device_reason_refs.append("device_evidence_count_mismatch")
    if len(set(device_case_ids)) != len(device_case_ids):
        device_reason_refs.append("device_evidence_duplicate_case")
    if not set(device_case_ids) <= set(expected_case_ids):
        device_reason_refs.append("device_evidence_case_not_in_local_review_set")
    if any(item.evidence_status != "verified" for item in device_assessments):
        device_reason_refs.append("device_evidence_runtime_or_visible_contract_mismatch")
    device_ready = bool(
        device_case_set_valid
        and all(item.evidence_status == "verified" for item in device_assessments)
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
        "local_review_surface_hash_binding_passed": bool(
            actual_local_reviews
            and not any(
                reason.startswith((
                    "actual_local_review_surface_sha256_",
                    "expected_local_surface_sha256_",
                ))
                for reason in local_review_reasons
            )
        ),
        "required_device_case_count": I7_REQUIRED_DEVICE_CASE_COUNT,
        "device_case_set_valid": device_case_set_valid,
        "device_reason_refs": list(dict.fromkeys(device_reason_refs)),
        "verified_device_case_count": sum(
            item.evidence_status == "verified" for item in device_assessments
        ),
        "verified_device_visible_surface_hash_count": sum(
            item.visible_surface_hash_verified for item in device_assessments
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
