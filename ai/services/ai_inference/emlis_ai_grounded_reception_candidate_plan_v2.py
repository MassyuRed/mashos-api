# -*- coding: utf-8 -*-
from __future__ import annotations

"""Deterministic body-free Discourse Candidate Planner v2.

The planner enumerates a bounded set of discourse readings from one frozen
Reception Content Plan.  It owns unit order, sentence grouping, referent
policy, speaker presence, and variation identity; it never receives source
text, fixture identity, or a completed sentence.
"""

from dataclasses import asdict, dataclass
import hashlib
import json
import re
from typing import Any, Final, Literal, Mapping, Sequence

from emlis_ai_grounded_reception_content_plan_v2 import (
    RECEPTION_CONTENT_PLAN_V2_SCHEMA_VERSION,
    ReceptionContentPlanV2,
    ReceptionContentUnitV2,
)


RECEPTION_CANDIDATE_PLAN_V2_SCHEMA_VERSION: Final = (
    "cocolon.emlis.reception_candidate_plan.v1"
)
RECEPTION_CANDIDATE_SET_V2_SCHEMA_VERSION: Final = (
    "cocolon.emlis.reception_candidate_set.v1"
)

DiscourseStrategyV2 = Literal[
    "attention_then_felt",
    "attention_significance_felt",
    "contrast_then_felt",
    "uncertainty_then_action",
    "action_then_meaning",
    "burden_then_counterposition",
    "parallel_layered",
]
OpeningPolicyV2 = Literal[
    "specific_point",
    "semantic_shift",
    "concrete_action",
    "emlis_attention",
    "uncertainty_boundary",
    "burden_boundary",
]
ReferentPolicyV2 = Literal[
    "semantic_paraphrase",
    "short_bound_anchor",
    "deictic_after_unique_antecedent",
    "nominalized_content",
]
SpeakerPresenceV2 = Literal[
    "implicit_emlis",
    "explicit_first_sentence",
    "explicit_terminal_sentence",
]
ConnectionPolicyV2 = Literal[
    "parallel",
    "contrast_safe",
    "uncertainty_then_action",
    "relation_bound",
    "separate_responsibilities",
]
TerminalFamilyV2 = Literal[
    "felt_reception",
    "attention_hold",
    "meaning_preservation",
    "restraint",
    "bounded_counterposition",
]

_ALLOWED_STRATEGIES: Final = (
    "attention_then_felt",
    "attention_significance_felt",
    "contrast_then_felt",
    "uncertainty_then_action",
    "action_then_meaning",
    "burden_then_counterposition",
    "parallel_layered",
)
_CANDIDATE_LIMITS: Final[Mapping[str, tuple[int, int]]] = {
    "minimal": (3, 4),
    "focused": (5, 8),
    "layered": (8, 12),
}
_TARGET_CANDIDATE_COUNT: Final[Mapping[str, int]] = {
    "minimal": 3,
    "focused": 5,
    "layered": 8,
}
_CANDIDATE_ID_RE: Final = re.compile(r"^rcand_[0-9a-f]{16}_[0-9]{2}$")
_CODE_RE: Final = re.compile(r"^[a-z][a-z0-9_.:-]*$")
_UNCERTAINTY_SIGNATURES: Final = frozenset(
    {
        "connection_kept_uncertain",
        "continuation_or_refusal_preserved",
        "wish_held_with_constraint",
        "attempt_held_with_block",
    }
)
_CONTRAST_SIGNATURES: Final = frozenset(
    {
        "attention_or_evaluation_shift",
        "value_or_intention_preserved_despite_burden",
        "counterposed_meanings_coexist",
        "distinct_meanings_coexist",
        "identity_claim_and_grounded_counterdirection",
        "continuation_or_refusal_preserved",
    }
)
_ACTION_SIGNATURES: Final = frozenset(
    {
        "concrete_action_recorded",
        "help_seeking_preserved",
        "intention_retained",
        "action_connected_to_observed_change",
    }
)
_FORBIDDEN_META_KEYS: Final = frozenset(
    {
        "case_id",
        "fixture_id",
        "input_family",
        "memo",
        "memo_action",
        "raw_input",
        "raw_text",
        "source_text",
        "surface_text",
        "candidate_text",
        "expected_text",
        "visible_surface",
        "wording_cue",
    }
)


class ReceptionCandidatePlanV2Error(ValueError):
    """Raised when bounded body-free candidate planning cannot be satisfied."""


@dataclass(frozen=True)
class ReceptionVariationSignatureV2:
    opening: OpeningPolicyV2
    referent: ReferentPolicyV2
    speaker_presence: SpeakerPresenceV2
    connection: ConnectionPolicyV2
    terminal_family: TerminalFamilyV2


@dataclass(frozen=True)
class ReceptionCandidatePlanV2:
    schema_version: str
    candidate_id: str
    content_plan_id: str
    strategy_code: DiscourseStrategyV2
    ordered_unit_ids: tuple[str, ...]
    sentence_groups: tuple[tuple[str, ...], ...]
    variation_signature: ReceptionVariationSignatureV2
    required_coverage_unit_ids: tuple[str, ...]
    candidate_rank_seed: int
    body_free: bool = True


@dataclass(frozen=True)
class ReceptionCandidatePlanSetV2:
    schema_version: str
    content_plan_id: str
    source_content_plan_schema_version: str
    depth: str
    candidates: tuple[ReceptionCandidatePlanV2, ...]
    candidate_limit_min: int
    candidate_limit_max: int
    enumerated_variant_count: int
    deduplicated_variant_count: int
    stable_ordering: bool
    body_free: bool = True

    def as_body_free_meta(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.update(
            {
                "case_id_included": False,
                "fixture_family_included": False,
                "raw_input_included": False,
                "raw_text_included": False,
                "source_text_included": False,
                "surface_text_included": False,
                "candidate_text_included": False,
                "expected_text_included": False,
                "random_selection_used": False,
                "runtime_connected": False,
                "public_contract_changed": False,
            }
        )
        return payload


@dataclass(frozen=True)
class _VariantSpec:
    strategy_preferences: tuple[str, ...]
    opening: OpeningPolicyV2
    referent: ReferentPolicyV2
    speaker_presence: SpeakerPresenceV2
    connection: ConnectionPolicyV2
    terminal_family: TerminalFamilyV2
    grouping: Literal["split", "merge_compatible"] = "split"


_VARIANT_CATALOG: Final[tuple[_VariantSpec, ...]] = (
    _VariantSpec(
        ("attention_then_felt",),
        "specific_point",
        "semantic_paraphrase",
        "implicit_emlis",
        "parallel",
        "felt_reception",
    ),
    _VariantSpec(
        ("attention_significance_felt", "attention_then_felt"),
        "emlis_attention",
        "nominalized_content",
        "explicit_first_sentence",
        "relation_bound",
        "attention_hold",
    ),
    _VariantSpec(
        ("contrast_then_felt", "attention_significance_felt", "attention_then_felt"),
        "semantic_shift",
        "semantic_paraphrase",
        "implicit_emlis",
        "contrast_safe",
        "meaning_preservation",
    ),
    _VariantSpec(
        ("action_then_meaning", "attention_then_felt"),
        "concrete_action",
        "short_bound_anchor",
        "explicit_terminal_sentence",
        "parallel",
        "restraint",
    ),
    _VariantSpec(
        ("uncertainty_then_action", "attention_significance_felt", "attention_then_felt"),
        "uncertainty_boundary",
        "nominalized_content",
        "explicit_first_sentence",
        "uncertainty_then_action",
        "meaning_preservation",
    ),
    _VariantSpec(
        ("burden_then_counterposition", "attention_then_felt"),
        "burden_boundary",
        "semantic_paraphrase",
        "explicit_terminal_sentence",
        "separate_responsibilities",
        "bounded_counterposition",
    ),
    _VariantSpec(
        ("parallel_layered", "attention_significance_felt", "attention_then_felt"),
        "specific_point",
        "nominalized_content",
        "implicit_emlis",
        "parallel",
        "restraint",
        "merge_compatible",
    ),
    _VariantSpec(
        ("action_then_meaning", "contrast_then_felt", "attention_then_felt"),
        "concrete_action",
        "semantic_paraphrase",
        "explicit_first_sentence",
        "relation_bound",
        "felt_reception",
        "merge_compatible",
    ),
    _VariantSpec(
        ("contrast_then_felt", "parallel_layered", "attention_then_felt"),
        "semantic_shift",
        "deictic_after_unique_antecedent",
        "explicit_terminal_sentence",
        "contrast_safe",
        "attention_hold",
        "merge_compatible",
    ),
    _VariantSpec(
        ("uncertainty_then_action", "parallel_layered", "attention_then_felt"),
        "uncertainty_boundary",
        "semantic_paraphrase",
        "implicit_emlis",
        "uncertainty_then_action",
        "restraint",
    ),
    _VariantSpec(
        ("burden_then_counterposition", "parallel_layered", "attention_then_felt"),
        "burden_boundary",
        "nominalized_content",
        "explicit_first_sentence",
        "separate_responsibilities",
        "meaning_preservation",
    ),
    _VariantSpec(
        ("parallel_layered", "attention_significance_felt", "attention_then_felt"),
        "emlis_attention",
        "short_bound_anchor",
        "explicit_terminal_sentence",
        "parallel",
        "felt_reception",
        "merge_compatible",
    ),
)


def _dedupe(values: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    rows: list[str] = []
    for raw in values:
        value = str(raw or "").strip()
        if value and value not in seen:
            seen.add(value)
            rows.append(value)
    return tuple(rows)


def _select_strategy(
    preferences: Sequence[str],
    allowed: Sequence[str],
) -> DiscourseStrategyV2:
    available = tuple(
        strategy
        for strategy in allowed
        if strategy in _ALLOWED_STRATEGIES
    )
    for strategy in preferences:
        if strategy in available:
            return strategy
    if "attention_then_felt" in available:
        return "attention_then_felt"
    if available:
        return available[0]
    raise ReceptionCandidatePlanV2Error("allowed_discourse_strategy_missing")


def _strategy_rank(
    strategy: str,
    unit: ReceptionContentUnitV2,
    original_index: int,
) -> tuple[int, float, int]:
    role = unit.role
    signature = unit.semantic_signature
    if strategy == "attention_then_felt":
        rank = {
            "attention": 0,
            "significance": 1,
            "connection": 2,
            "bounded_counterposition": 2,
            "felt_response": 3,
        }.get(role, 4)
    elif strategy == "attention_significance_felt":
        rank = {
            "attention": 0,
            "significance": 1,
            "connection": 2,
            "bounded_counterposition": 2,
            "felt_response": 3,
        }.get(role, 4)
    elif strategy == "contrast_then_felt":
        rank = 0 if signature in _CONTRAST_SIGNATURES else (
            1 if role == "attention" else 3 if role == "felt_response" else 2
        )
    elif strategy == "uncertainty_then_action":
        rank = 0 if signature in _UNCERTAINTY_SIGNATURES else (
            1 if signature in _ACTION_SIGNATURES else 3 if role == "felt_response" else 2
        )
    elif strategy == "action_then_meaning":
        rank = (
            0
            if signature in {
                "concrete_action_recorded",
                "emlis_reception_of_concrete_action_recorded",
            }
            else 1
            if role in {"significance", "connection"}
            else 3
            if role == "felt_response"
            else 2
        )
    elif strategy == "burden_then_counterposition":
        rank = 0 if signature == "current_burden_present" else (
            3 if role == "bounded_counterposition" else 2 if role == "felt_response" else 1
        )
    else:
        rank = original_index
    return (rank, -float(unit.priority), original_index)


def _ordered_units(
    content_plan: ReceptionContentPlanV2,
    strategy: str,
) -> tuple[ReceptionContentUnitV2, ...]:
    indexed = tuple(enumerate(content_plan.content_units))
    return tuple(
        unit
        for index, unit in sorted(
            indexed,
            key=lambda row: _strategy_rank(strategy, row[1], row[0]),
        )
    )


def _pair_key(left: str, right: str) -> frozenset[str]:
    return frozenset((left, right))


def _merge_compatible_pair(
    ordered: Sequence[ReceptionContentUnitV2],
    content_plan: ReceptionContentPlanV2,
) -> tuple[int, int] | None:
    if len(ordered) < 4:
        return None
    separated_pairs = {
        _pair_key(left, right)
        for left, right in content_plan.discourse_constraints.must_keep_units_separate
    }
    for index in range(len(ordered) - 1):
        left = ordered[index]
        right = ordered[index + 1]
        if (
            left.role == "bounded_counterposition"
            or right.role == "bounded_counterposition"
            or _pair_key(left.unit_id, right.unit_id) in separated_pairs
        ):
            continue
        left_nuclei = set((*left.target_nucleus_ids, *left.support_nucleus_ids))
        right_nuclei = set((*right.target_nucleus_ids, *right.support_nucleus_ids))
        relation_linked = bool(set(left.relation_ids) & set(right.relation_ids))
        if left_nuclei & right_nuclei or relation_linked:
            return (index, index + 1)
    return None


def _sentence_groups(
    ordered: Sequence[ReceptionContentUnitV2],
    content_plan: ReceptionContentPlanV2,
    grouping: str,
) -> tuple[tuple[str, ...], ...]:
    merge_pair = (
        _merge_compatible_pair(ordered, content_plan)
        if grouping == "merge_compatible"
        else None
    )
    groups: list[tuple[str, ...]] = []
    index = 0
    while index < len(ordered):
        if merge_pair == (index, index + 1):
            groups.append((ordered[index].unit_id, ordered[index + 1].unit_id))
            index += 2
        else:
            groups.append((ordered[index].unit_id,))
            index += 1
    return tuple(groups)


def _deictic_is_safe(
    groups: Sequence[Sequence[str]],
    unit_index: Mapping[str, ReceptionContentUnitV2],
) -> bool:
    for group in groups:
        if len(group) != 2:
            continue
        left = unit_index[group[0]]
        right = unit_index[group[1]]
        left_nuclei = set((*left.target_nucleus_ids, *left.support_nucleus_ids))
        right_nuclei = set((*right.target_nucleus_ids, *right.support_nucleus_ids))
        if left_nuclei & right_nuclei:
            return True
    return False


def _candidate_id(
    content_plan_id: str,
    ordinal: int,
    strategy: str,
    groups: Sequence[Sequence[str]],
    variation: ReceptionVariationSignatureV2,
) -> str:
    payload = {
        "content_plan_id": content_plan_id,
        "ordinal": ordinal,
        "strategy": strategy,
        "sentence_groups": groups,
        "variation_signature": asdict(variation),
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"rcand_{hashlib.sha256(encoded).hexdigest()[:16]}_{ordinal:02d}"


def _ordered_variant_catalog(
    allowed: Sequence[str],
    *,
    prefer_anchor: bool,
) -> tuple[_VariantSpec, ...]:
    """Keep the baseline first, then exercise grounded non-default readings.

    A fixed catalog alone would place the safety-bounded reading outside the
    five-candidate focused budget.  This stable, semantic-only ordering keeps
    one conservative baseline first and advances only catalog rows whose
    primary strategy is actually allowed by the Content Plan.
    """

    baseline = _VARIANT_CATALOG[:1]
    remainder = _VARIANT_CATALOG[1:]
    anchors = (
        tuple(spec for spec in remainder if spec.referent == "short_bound_anchor")[:1]
        if prefer_anchor
        else ()
    )
    remainder = tuple(spec for spec in remainder if spec not in anchors)
    specific = tuple(
        spec
        for spec in remainder
        if spec.strategy_preferences[0] in allowed
        and spec.strategy_preferences[0] != "attention_then_felt"
    )
    fallback = tuple(spec for spec in remainder if spec not in specific)
    return (*baseline, *anchors, *specific, *fallback)


def build_reception_candidate_plans_v2(
    content_plan: ReceptionContentPlanV2,
) -> ReceptionCandidatePlanSetV2:
    """Enumerate a stable bounded candidate set from one body-free plan."""

    if not isinstance(content_plan, ReceptionContentPlanV2):
        raise ReceptionCandidatePlanV2Error("reception_content_plan_v2_required")
    if content_plan.schema_version != RECEPTION_CONTENT_PLAN_V2_SCHEMA_VERSION:
        raise ReceptionCandidatePlanV2Error("content_plan_schema_mismatch")
    limits = _CANDIDATE_LIMITS.get(content_plan.depth)
    if limits is None:
        raise ReceptionCandidatePlanV2Error(
            f"unsupported_candidate_depth:{content_plan.depth}"
        )
    target_count = _TARGET_CANDIDATE_COUNT[content_plan.depth]
    allowed = content_plan.discourse_constraints.allowed_strategy_codes
    unit_index = {item.unit_id: item for item in content_plan.content_units}

    candidates: list[ReceptionCandidatePlanV2] = []
    variation_keys: set[tuple[str, ...]] = set()
    for spec in _ordered_variant_catalog(
        allowed,
        prefer_anchor=bool(
            content_plan.quote_policy.mode == "optional_single_anchor"
        ),
    ):
        strategy = _select_strategy(spec.strategy_preferences, allowed)
        ordered = _ordered_units(content_plan, strategy)
        groups = _sentence_groups(ordered, content_plan, spec.grouping)
        opening: OpeningPolicyV2 = spec.opening
        connection: ConnectionPolicyV2 = spec.connection
        terminal_family: TerminalFamilyV2 = spec.terminal_family
        if opening == "semantic_shift" and strategy != "contrast_then_felt":
            opening = "specific_point"
        elif opening == "uncertainty_boundary" and strategy != "uncertainty_then_action":
            opening = "specific_point"
        elif opening == "burden_boundary" and strategy != "burden_then_counterposition":
            opening = "specific_point"
        if connection == "contrast_safe" and strategy != "contrast_then_felt":
            connection = "parallel"
        elif (
            connection == "uncertainty_then_action"
            and strategy != "uncertainty_then_action"
        ):
            connection = "parallel"
        elif (
            connection == "separate_responsibilities"
            and strategy != "burden_then_counterposition"
        ):
            connection = "parallel"
        if terminal_family == "bounded_counterposition" and not any(
            unit.role == "bounded_counterposition" for unit in ordered
        ):
            terminal_family = "restraint"
        referent: ReferentPolicyV2 = spec.referent
        if referent == "short_bound_anchor" and (
            content_plan.quote_policy.mode != "optional_single_anchor"
            or content_plan.quote_policy.max_anchor_count < 1
        ):
            referent = "nominalized_content"
        if referent == "deictic_after_unique_antecedent" and not _deictic_is_safe(
            groups,
            unit_index,
        ):
            referent = "semantic_paraphrase"
        variation = ReceptionVariationSignatureV2(
            opening=opening,
            referent=referent,
            speaker_presence=spec.speaker_presence,
            connection=connection,
            terminal_family=terminal_family,
        )
        variation_key = (
            strategy,
            variation.opening,
            variation.referent,
            variation.speaker_presence,
            variation.connection,
            variation.terminal_family,
            json.dumps(groups, ensure_ascii=False, separators=(",", ":")),
        )
        if variation_key in variation_keys:
            continue
        variation_keys.add(variation_key)
        ordinal = len(candidates) + 1
        candidates.append(
            ReceptionCandidatePlanV2(
                schema_version=RECEPTION_CANDIDATE_PLAN_V2_SCHEMA_VERSION,
                candidate_id=_candidate_id(
                    content_plan.plan_id,
                    ordinal,
                    strategy,
                    groups,
                    variation,
                ),
                content_plan_id=content_plan.plan_id,
                strategy_code=strategy,
                ordered_unit_ids=tuple(item.unit_id for item in ordered),
                sentence_groups=groups,
                variation_signature=variation,
                required_coverage_unit_ids=content_plan.required_unit_ids,
                candidate_rank_seed=ordinal,
                body_free=True,
            )
        )
        if len(candidates) >= target_count:
            break

    if len(candidates) < target_count:
        raise ReceptionCandidatePlanV2Error(
            f"candidate_minimum_unmet:{content_plan.depth}:{len(candidates)}:{target_count}"
        )
    candidate_set = ReceptionCandidatePlanSetV2(
        schema_version=RECEPTION_CANDIDATE_SET_V2_SCHEMA_VERSION,
        content_plan_id=content_plan.plan_id,
        source_content_plan_schema_version=content_plan.schema_version,
        depth=content_plan.depth,
        candidates=tuple(candidates),
        candidate_limit_min=limits[0],
        candidate_limit_max=limits[1],
        enumerated_variant_count=len(_VARIANT_CATALOG),
        deduplicated_variant_count=len(candidates),
        stable_ordering=True,
        body_free=True,
    )
    issues = validate_reception_candidate_plan_set_v2(
        candidate_set,
        content_plan,
    )
    if issues:
        raise ReceptionCandidatePlanV2Error(
            "invalid_reception_candidate_plan_set_v2:" + ",".join(issues)
        )
    return candidate_set


def validate_reception_candidate_plan_set_v2(
    candidate_set: ReceptionCandidatePlanSetV2,
    content_plan: ReceptionContentPlanV2,
) -> tuple[str, ...]:
    issues: list[str] = []
    if candidate_set.schema_version != RECEPTION_CANDIDATE_SET_V2_SCHEMA_VERSION:
        issues.append("candidate_set_schema_mismatch")
    if candidate_set.content_plan_id != content_plan.plan_id:
        issues.append("candidate_set_content_plan_id_mismatch")
    if candidate_set.source_content_plan_schema_version != content_plan.schema_version:
        issues.append("candidate_set_source_schema_mismatch")
    if candidate_set.depth != content_plan.depth:
        issues.append("candidate_set_depth_mismatch")
    limits = _CANDIDATE_LIMITS.get(content_plan.depth)
    if limits is None or not limits[0] <= len(candidate_set.candidates) <= limits[1]:
        issues.append("candidate_count_out_of_bounds")
    elif (
        candidate_set.candidate_limit_min,
        candidate_set.candidate_limit_max,
    ) != limits:
        issues.append("candidate_limit_contract_mismatch")
    if candidate_set.stable_ordering is not True or candidate_set.body_free is not True:
        issues.append("candidate_set_body_free_or_ordering_invalid")

    unit_ids = tuple(item.unit_id for item in content_plan.content_units)
    unit_id_set = set(unit_ids)
    unit_index = {item.unit_id: item for item in content_plan.content_units}
    variation_signatures: set[tuple[Any, ...]] = set()
    candidate_ids: set[str] = set()
    keep_separate = {
        _pair_key(left, right)
        for left, right in content_plan.discourse_constraints.must_keep_units_separate
    }
    for ordinal, candidate in enumerate(candidate_set.candidates, start=1):
        prefix = candidate.candidate_id or f"candidate_{ordinal}"
        if candidate.schema_version != RECEPTION_CANDIDATE_PLAN_V2_SCHEMA_VERSION:
            issues.append(f"{prefix}:schema_mismatch")
        if not _CANDIDATE_ID_RE.fullmatch(candidate.candidate_id):
            issues.append(f"{prefix}:id_invalid")
        if candidate.candidate_id in candidate_ids:
            issues.append(f"{prefix}:id_duplicate")
        candidate_ids.add(candidate.candidate_id)
        if candidate.content_plan_id != content_plan.plan_id:
            issues.append(f"{prefix}:content_plan_id_mismatch")
        if candidate.strategy_code not in _ALLOWED_STRATEGIES:
            issues.append(f"{prefix}:strategy_invalid")
        if candidate.strategy_code not in (
            content_plan.discourse_constraints.allowed_strategy_codes
        ):
            issues.append(f"{prefix}:strategy_not_allowed_by_content_plan")
        if set(candidate.ordered_unit_ids) != unit_id_set or len(
            candidate.ordered_unit_ids
        ) != len(unit_ids):
            issues.append(f"{prefix}:ordered_unit_coverage_invalid")
        flattened = tuple(unit_id for group in candidate.sentence_groups for unit_id in group)
        if flattened != candidate.ordered_unit_ids:
            issues.append(f"{prefix}:sentence_group_order_invalid")
        if any(not group or len(group) > 2 for group in candidate.sentence_groups):
            issues.append(f"{prefix}:sentence_group_size_invalid")
        if not (
            content_plan.sentence_budget.min
            <= len(candidate.sentence_groups)
            <= content_plan.sentence_budget.max
        ):
            issues.append(f"{prefix}:sentence_budget_invalid")
        for group in candidate.sentence_groups:
            if len(group) == 2 and _pair_key(*group) in keep_separate:
                issues.append(f"{prefix}:must_keep_units_separate_violated")
        if candidate.required_coverage_unit_ids != content_plan.required_unit_ids:
            issues.append(f"{prefix}:required_coverage_mismatch")
        if candidate.candidate_rank_seed != ordinal:
            issues.append(f"{prefix}:stable_rank_seed_invalid")
        if candidate.body_free is not True:
            issues.append(f"{prefix}:body_free_false")
        variation_key = tuple(asdict(candidate.variation_signature).values()) + (
            candidate.strategy_code,
            candidate.sentence_groups,
        )
        if variation_key in variation_signatures:
            issues.append(f"{prefix}:variation_signature_duplicate")
        variation_signatures.add(variation_key)
        for code in asdict(candidate.variation_signature).values():
            if not _CODE_RE.fullmatch(str(code)):
                issues.append(f"{prefix}:variation_code_invalid")
        for unit_id in candidate.ordered_unit_ids:
            if unit_id not in unit_index:
                issues.append(f"{prefix}:unknown_unit")

    serialized = asdict(candidate_set)

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if str(key) in _FORBIDDEN_META_KEYS:
                    issues.append(f"body_field_forbidden:{key}")
                walk(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                walk(child)

    walk(serialized)
    return _dedupe(issues)


__all__ = [
    "RECEPTION_CANDIDATE_PLAN_V2_SCHEMA_VERSION",
    "RECEPTION_CANDIDATE_SET_V2_SCHEMA_VERSION",
    "ReceptionCandidatePlanV2Error",
    "ReceptionVariationSignatureV2",
    "ReceptionCandidatePlanV2",
    "ReceptionCandidatePlanSetV2",
    "build_reception_candidate_plans_v2",
    "validate_reception_candidate_plan_set_v2",
]
