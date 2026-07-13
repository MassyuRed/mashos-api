# -*- coding: utf-8 -*-
from __future__ import annotations

"""Body-free Hard Gate and deterministic Soft Selector for reception v2.

The selector consumes process-local Step 5 bodies but emits only ids, codes,
coverage, and numeric scores.  Hard failures are never rescued by a soft
score.  This Step 6/7 owner remains offline and never invokes the v1 fallback
or the production reply service.
"""

from dataclasses import asdict, dataclass, replace
import json
import re
from typing import Any, Final, Literal, Mapping, Sequence

from emlis_ai_evidence_ledger_service import EvidenceSpanResolver
from emlis_ai_grounded_human_reception_v2 import (
    RECEPTION_SURFACE_CANDIDATE_SET_V2_SCHEMA_VERSION,
    ReceptionSurfaceCandidateSetV2,
    ReceptionSurfaceCandidateV2,
    validate_reception_surface_candidate_v2,
)
from emlis_ai_grounded_observation_plan import (
    GroundedObservationPlan,
    GroundedSemanticNucleus,
)
from emlis_ai_grounded_reception_candidate_plan_v2 import (
    RECEPTION_CANDIDATE_SET_V2_SCHEMA_VERSION,
    ReceptionCandidatePlanSetV2,
    ReceptionCandidatePlanV2,
)
from emlis_ai_grounded_reception_content_plan_v2 import (
    RECEPTION_CONTENT_PLAN_V2_SCHEMA_VERSION,
    ReceptionContentPlanV2,
    ReceptionContentUnitV2,
)


RECEPTION_CANDIDATE_EVALUATION_V2_SCHEMA_VERSION: Final = (
    "cocolon.emlis.reception_candidate_evaluation.v1"
)
RECEPTION_CANDIDATE_SELECTION_V2_SCHEMA_VERSION: Final = (
    "cocolon.emlis.reception_candidate_selection.v1"
)
RECEPTION_SELECTOR_CONFIG_V2_VERSION: Final = (
    "cocolon.emlis.reception_selector_config.s7.v1"
)

HardGateStatus = Literal["passed", "failed"]
SelectionStatus = Literal["selected", "v2_no_valid_candidate"]
HardGateCode = Literal[
    "evidence_resolution",
    "required_content_coverage",
    "polarity_preservation",
    "relation_direction",
    "reference_scope",
    "unknown_preservation",
    "self_denial_boundary",
    "unsupported_claim",
    "observation_replay",
    "enumeration_only",
    "section_role_distinctness",
    "surface_integrity",
    "depth_proportionality",
    "body_free_meta",
]

HARD_GATE_CODES: Final[tuple[HardGateCode, ...]] = (
    "evidence_resolution",
    "required_content_coverage",
    "polarity_preservation",
    "relation_direction",
    "reference_scope",
    "unknown_preservation",
    "self_denial_boundary",
    "unsupported_claim",
    "observation_replay",
    "enumeration_only",
    "section_role_distinctness",
    "surface_integrity",
    "depth_proportionality",
    "body_free_meta",
)
SOFT_SCORE_AXES: Final = (
    "input_specificity",
    "content_distinctness",
    "discourse_coherence",
    "emlis_presence",
    "quote_independence",
    "observation_reception_separation",
    "lexical_repetition",
    "syntactic_variation",
    "depth_fit",
    "temperature_fit",
    "restraint",
)
SOFT_SCORE_WEIGHTS: Final[tuple[tuple[str, float], ...]] = (
    ("input_specificity", 0.15),
    ("content_distinctness", 0.12),
    ("discourse_coherence", 0.12),
    ("emlis_presence", 0.10),
    ("quote_independence", 0.07),
    ("observation_reception_separation", 0.12),
    ("lexical_repetition", 0.08),
    ("syntactic_variation", 0.07),
    ("depth_fit", 0.07),
    ("temperature_fit", 0.05),
    ("restraint", 0.05),
)
CANDIDATE_LIMIT_FREEZE: Final[Mapping[str, tuple[int, int, int]]] = {
    "minimal": (3, 4, 3),
    "focused": (5, 8, 5),
    "layered": (8, 12, 8),
}
DISTRIBUTION_THRESHOLD_FREEZE: Final[Mapping[str, float | int]] = {
    "exact_duplicate_max": 0,
    "rich_single_sentence_max": 0,
    "short_meaningless_inflation_max": 0,
    "strategy_share_max": 0.45,
    "terminal_family_share_max": 0.65,
    "predicate_family_share_max": 0.45,
    "skeleton_share_max": 0.45,
}

_CODE_RE: Final = re.compile(r"^[A-Za-z0-9_.:/-]+$")
_QUOTE_RE: Final = re.compile(r"「([^」]*)」")
_QUESTION_RE: Final = re.compile(r"[?？]")
_SPACE_PUNCT_RE: Final = re.compile(r"[\s\u3000、。,.!！?？「」『』（）()・:：;；]")
_CAUSAL_CONNECTOR_RE: Final = re.compile(
    r"(?:だから|そのため|ことで|につながっている|として表れている)"
)
_CERTAINTY_RE: Final = re.compile(
    r"(?:必ず|絶対に|確実に|原因は.{0,18}(?:です|あります)|"
    r"に違いありません|もう解決|回復しました|成功しました)"
)
_POSITIVE_OVERCLAIM_RE: Final = re.compile(
    r"(?:成長しました|乗り越えました|解決しました|回復しました|"
    r"成功しました|もう大丈夫|幸せになりました)"
)
_NEGATIVE_INVENTION_RE: Final = re.compile(
    r"(?:悪化しました|失敗した人|壊れてしまった|絶望的|危険です)"
)
_CELEBRATORY_RE: Final = re.compile(r"(?:うれしくて|喜ばしい|よかったですね)")
_BURDEN_RE: Final = re.compile(r"(?:苦しさ|つらさ|しんどさ|負担)")
_UNSUPPORTED_RE: Final = re.compile(
    r"(?:うつ病|鬱病|パニック障害|適応障害|診断|"
    r"あなたは(?:強い|優しい|立派|素晴らしい)(?:人)?です|"
    r"(?:してください|しましょう|してみて|すべき|した方がいい|"
    r"受診して|相談して|連絡して))"
)
_IDENTITY_ACCEPTANCE_RE: Final = re.compile(
    r"(?:価値がない|だめな人間|悪い人間|役に立たない).{0,18}"
    r"(?:事実|本当|その通り|確か)"
)
_SELF_DENIAL_COUNTER_RE: Final = re.compile(
    r"苦しさ.{0,48}否定せず.*Emlis.{0,48}自身.{0,24}思えません"
)
_OBSERVATION_ROLE_RE: Final = re.compile(
    r"(?:という|の)(?:構造|関係|傾向|パターン)(?:です|に見えます)|"
    r"(?:分析|整理|分類)(?:できます|しました)|"
    r"(?:入力|記録)に(?:書かれています|あります|置かれています)"
)
_RECEPTION_STANCE_RE: Final = re.compile(
    r"(?:受け取|受け止|印象に残|見過ご|心に留め|大切に|"
    r"流したくありません|決めつけず|思えません)"
)
_UNCERTAINTY_MARKER_RE: Final = re.compile(
    r"(?:分から|わから|決めきれ|不明|まだ|決めつけず)"
)
_ALLOWED_CAUSAL_RELATION_TYPES: Final = frozenset(
    {"user_stated_cause", "user_stated_result", "action_supports_change"}
)
_UNCERTAINTY_SIGNATURES: Final = frozenset(
    {
        "connection_kept_uncertain",
        "continuation_or_refusal_preserved",
        "wish_held_with_constraint",
    }
)
_FORBIDDEN_META_KEYS: Final = frozenset(
    {
        "text",
        "surface_text",
        "candidate_text",
        "selected_text",
        "visible_surface",
        "expected_text",
        "raw_input",
        "raw_text",
        "source_text",
        "comment_text",
    }
)


class ReceptionCandidateSelectorV2Error(ValueError):
    """Raised when the Step 6/7 selector contract is internally invalid."""


@dataclass(frozen=True)
class ReceptionHardGateCheckV2:
    code: HardGateCode
    status: HardGateStatus
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class ReceptionHardGateResultV2:
    status: HardGateStatus
    failed_codes: tuple[HardGateCode, ...]
    checks: tuple[ReceptionHardGateCheckV2, ...]


@dataclass(frozen=True)
class ReceptionCandidateCoverageV2:
    required_unit_ids: tuple[str, ...]
    covered_unit_ids: tuple[str, ...]
    missing_unit_ids: tuple[str, ...]
    grounded_nucleus_count: int
    grounded_evidence_count: int


@dataclass(frozen=True)
class ReceptionCandidateSoftScoresV2:
    input_specificity: float
    content_distinctness: float
    discourse_coherence: float
    emlis_presence: float
    quote_independence: float
    observation_reception_separation: float
    lexical_repetition: float
    syntactic_variation: float
    depth_fit: float
    temperature_fit: float
    restraint: float

    def as_mapping(self) -> dict[str, float]:
        return {axis: float(getattr(self, axis)) for axis in SOFT_SCORE_AXES}


@dataclass(frozen=True)
class ReceptionCandidateEvaluationV2:
    schema_version: str
    candidate_id: str
    content_plan_id: str
    hard_gate: ReceptionHardGateResultV2
    coverage: ReceptionCandidateCoverageV2
    soft_scores: ReceptionCandidateSoftScoresV2 | None
    total_score: float | None
    score_reason_codes: tuple[str, ...]
    selected: bool
    body_free: bool = True


@dataclass(frozen=True)
class ReceptionCandidateSelectionV2:
    schema_version: str
    selector_config_version: str
    content_plan_id: str
    source_candidate_set_schema_version: str
    source_surface_set_schema_version: str
    status: SelectionStatus
    selected_candidate_id: str | None
    local_failure_code: str | None
    hard_gate_pass_count: int
    hard_gate_fail_count: int
    evaluations: tuple[ReceptionCandidateEvaluationV2, ...]
    stable_tie_break_applied: bool
    v1_fallback_used: bool
    runtime_connected: bool
    body_free: bool = True

    def as_body_free_meta(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.update(
            {
                "candidate_bodies_included": False,
                "selected_body_included": False,
                "raw_input_included": False,
                "raw_text_included": False,
                "source_text_included": False,
                "comment_text_included": False,
                "public_contract_changed": False,
            }
        )
        return payload


def _dedupe(values: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    rows: list[str] = []
    for raw in values:
        value = str(raw or "").strip()
        if value and value not in seen:
            seen.add(value)
            rows.append(value)
    return tuple(rows)


def _normalized(value: Any) -> str:
    return _SPACE_PUNCT_RE.sub("", str(value or "")).lower()


def _sentences(value: str) -> tuple[str, ...]:
    if not value or not value.endswith("。"):
        return ()
    rows = value.split("。")
    if rows[-1] != "" or any(not row.strip() for row in rows[:-1]):
        return ()
    return tuple(f"{row.strip()}。" for row in rows[:-1])


def _walk_keys(value: Any):
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from _walk_keys(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            yield from _walk_keys(child)


def _unit_index(content_plan: ReceptionContentPlanV2) -> dict[str, ReceptionContentUnitV2]:
    return {unit.unit_id: unit for unit in content_plan.content_units}


def _nucleus_index(observation_plan: GroundedObservationPlan) -> dict[str, GroundedSemanticNucleus]:
    return {nucleus.nucleus_id: nucleus for nucleus in observation_plan.nuclei}


def _unit_nucleus_ids(unit: ReceptionContentUnitV2) -> tuple[str, ...]:
    return _dedupe((*unit.target_nucleus_ids, *unit.support_nucleus_ids))


def _pair_key(left: str, right: str) -> frozenset[str]:
    return frozenset((left, right))


def _score(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 4)


def _add_reason(
    reasons: dict[HardGateCode, list[str]],
    gate: HardGateCode,
    reason: str,
) -> None:
    if not _CODE_RE.fullmatch(reason):
        raise ReceptionCandidateSelectorV2Error(f"invalid_reason_code:{reason}")
    reasons[gate].append(reason)


def _evaluate_hard_gate(
    observation_plan: GroundedObservationPlan,
    content_plan: ReceptionContentPlanV2,
    candidate_plan: ReceptionCandidatePlanV2,
    surface: ReceptionSurfaceCandidateV2,
    resolver: EvidenceSpanResolver,
) -> tuple[ReceptionHardGateResultV2, ReceptionCandidateCoverageV2]:
    reception_plan = observation_plan.response_plan.human_reception_plan
    if reception_plan is None:
        raise ReceptionCandidateSelectorV2Error("human_reception_plan_required")
    reasons: dict[HardGateCode, list[str]] = {code: [] for code in HARD_GATE_CODES}
    units = _unit_index(content_plan)
    nuclei = _nucleus_index(observation_plan)
    relations = {relation.relation_id: relation for relation in observation_plan.relations}

    required_ids = tuple(content_plan.required_unit_ids)
    covered_ids = tuple(
        unit_id
        for unit_id in surface.realized_unit_ids
        if unit_id in units
    )
    missing_ids = tuple(unit_id for unit_id in required_ids if unit_id not in covered_ids)
    coverage = ReceptionCandidateCoverageV2(
        required_unit_ids=required_ids,
        covered_unit_ids=covered_ids,
        missing_unit_ids=missing_ids,
        grounded_nucleus_count=len(surface.grounded_nucleus_ids),
        grounded_evidence_count=len(surface.grounded_evidence_span_ids),
    )

    expected_evidence = _dedupe(
        [
            span_id
            for unit_id in candidate_plan.ordered_unit_ids
            for span_id in units[unit_id].evidence_span_ids
        ]
    )
    if resolver.unresolved_ids(expected_evidence):
        _add_reason(reasons, "evidence_resolution", "EVIDENCE_UNRESOLVED")
    if surface.grounded_evidence_span_ids != expected_evidence:
        _add_reason(reasons, "evidence_resolution", "EVIDENCE_COVERAGE_MISMATCH")

    if missing_ids:
        _add_reason(
            reasons,
            "required_content_coverage",
            "REQUIRED_CONTENT_MISSING",
        )
    content_nucleus_ids = {
        nucleus_id
        for unit in content_plan.content_units
        for nucleus_id in _unit_nucleus_ids(unit)
    }
    required_reception_nuclei = {
        nucleus_id
        for move in reception_plan.moves
        if move.required
        for nucleus_id in (*move.target_nucleus_ids, *move.support_nucleus_ids)
    }
    if not required_reception_nuclei <= content_nucleus_ids:
        _add_reason(
            reasons,
            "required_content_coverage",
            "SEMANTIC_MATERIAL_MISSING",
        )
    safety_nuclei = {
        nucleus_id
        for opportunity in reception_plan.opportunities
        if opportunity.safety_required
        for nucleus_id in (
            *opportunity.target_nucleus_ids,
            *opportunity.support_nucleus_ids,
        )
    }
    if not safety_nuclei <= content_nucleus_ids:
        _add_reason(
            reasons,
            "required_content_coverage",
            "SAFETY_CONTENT_MISSING",
        )

    target_polarities = {
        nuclei[nucleus_id].semantic_frame.polarity
        for nucleus_id in surface.grounded_nucleus_ids
        if nucleus_id in nuclei
    }
    grounded_burden = any(
        units[unit_id].semantic_signature
        in {
            "current_burden_present",
            "self_denial_boundary",
            "emlis_reception_of_current_burden_present",
            "value_or_intention_preserved_despite_burden",
        }
        for unit_id in candidate_plan.ordered_unit_ids
    )
    if target_polarities and target_polarities <= {"positive", "neutral"}:
        if _BURDEN_RE.search(surface.text) and not grounded_burden:
            _add_reason(reasons, "polarity_preservation", "POLARITY_INVERTED")
    if target_polarities and target_polarities <= {"negative", "neutral"}:
        if _CELEBRATORY_RE.search(surface.text):
            _add_reason(reasons, "polarity_preservation", "POLARITY_INVERTED")
    if _POSITIVE_OVERCLAIM_RE.search(surface.text) or _NEGATIVE_INVENTION_RE.search(
        surface.text
    ):
        _add_reason(reasons, "polarity_preservation", "POLARITY_INVERTED")

    relation_units = tuple(
        unit for unit in content_plan.content_units if unit.relation_ids
    )
    for unit in relation_units:
        for relation_id in unit.relation_ids:
            relation = relations.get(relation_id)
            if relation is None:
                _add_reason(
                    reasons,
                    "relation_direction",
                    "RELATION_REFERENCE_UNRESOLVED",
                )
                continue
            endpoints = (relation.from_nucleus_id, relation.to_nucleus_id)
            if unit.target_nucleus_ids[:2] != endpoints:
                _add_reason(
                    reasons,
                    "relation_direction",
                    "RELATION_DIRECTION_INVERTED",
                )
    if _CAUSAL_CONNECTOR_RE.search(surface.text):
        grounded_causal = any(
            relation.type in _ALLOWED_CAUSAL_RELATION_TYPES
            for unit in relation_units
            for relation_id in unit.relation_ids
            if (relation := relations.get(relation_id)) is not None
        )
        if not grounded_causal:
            _add_reason(reasons, "relation_direction", "FALSE_CAUSAL_LINK")

    keep_separate = {
        _pair_key(left, right)
        for left, right in content_plan.discourse_constraints.must_keep_units_separate
    }
    safe_deictic_group = False
    for group in candidate_plan.sentence_groups:
        if len(group) != 2:
            continue
        left = units[group[0]]
        right = units[group[1]]
        if _pair_key(*group) in keep_separate:
            _add_reason(reasons, "reference_scope", "REFERENCE_SCOPE_MIXED")
        left_nuclei = set(_unit_nucleus_ids(left))
        right_nuclei = set(_unit_nucleus_ids(right))
        relation_linked = bool(set(left.relation_ids) & set(right.relation_ids))
        if not (left_nuclei & right_nuclei or relation_linked):
            _add_reason(reasons, "reference_scope", "REFERENCE_SCOPE_MIXED")
        safe_deictic_group = safe_deictic_group or bool(left_nuclei & right_nuclei)
    if candidate_plan.variation_signature.referent == (
        "deictic_after_unique_antecedent"
    ):
        if not safe_deictic_group or not any(
            kind.startswith("deictic_") for kind in surface.referent_kinds
        ):
            _add_reason(reasons, "reference_scope", "REFERENCE_SCOPE_MIXED")

    uncertainty_units = tuple(
        unit
        for unit in content_plan.content_units
        if unit.semantic_signature in _UNCERTAINTY_SIGNATURES
    )
    source_uncertain = any(
        nucleus.semantic_frame.modality == "uncertain"
        or "operator:uncertainty" in nucleus.semantic_frame.attribute_codes
        for nucleus in observation_plan.nuclei
    )
    if source_uncertain and not uncertainty_units:
        _add_reason(
            reasons,
            "unknown_preservation",
            "UNKNOWN_BOUNDARY_LOST",
        )
    if uncertainty_units and not _UNCERTAINTY_MARKER_RE.search(surface.text):
        _add_reason(
            reasons,
            "unknown_preservation",
            "UNKNOWN_BOUNDARY_LOST",
        )
    if observation_plan.unknown_boundaries and _CERTAINTY_RE.search(surface.text):
        _add_reason(
            reasons,
            "unknown_preservation",
            "UNKNOWN_BOUNDARY_LOST",
        )

    self_denial_required = bool(
        observation_plan.safety_policy.identity_claim_must_not_be_accepted_as_fact
        or reception_plan.depth_policy.safety_mode == "self_denial_bounded"
    )
    if self_denial_required:
        has_bounded_unit = any(
            unit.role == "bounded_counterposition"
            for unit in content_plan.content_units
        )
        if not has_bounded_unit or not _SELF_DENIAL_COUNTER_RE.search(surface.text):
            _add_reason(
                reasons,
                "self_denial_boundary",
                "SELF_DENIAL_AMPLIFIED",
            )
    if _IDENTITY_ACCEPTANCE_RE.search(surface.text):
        _add_reason(
            reasons,
            "self_denial_boundary",
            "SELF_DENIAL_AMPLIFIED",
        )

    if (
        _UNSUPPORTED_RE.search(surface.text)
        or _POSITIVE_OVERCLAIM_RE.search(surface.text)
        or _NEGATIVE_INVENTION_RE.search(surface.text)
    ):
        _add_reason(reasons, "unsupported_claim", "UNSUPPORTED_CLAIM")
    if _QUESTION_RE.search(surface.text):
        _add_reason(reasons, "unsupported_claim", "UNSUPPORTED_QUESTION")

    quote_chars = sum(len(value) for value in _QUOTE_RE.findall(surface.text))
    visible_chars = max(1, len(_normalized(surface.text)))
    if quote_chars / visible_chars > 0.35 or _OBSERVATION_ROLE_RE.search(surface.text):
        _add_reason(reasons, "observation_replay", "OBSERVATION_REPLAY")

    sentences = _sentences(surface.text)
    if len(set(sentences)) != len(sentences):
        _add_reason(reasons, "enumeration_only", "INPUT_ENUMERATION")
    normalized_signatures = tuple(
        units[unit_id].semantic_signature.removeprefix("emlis_reception_of_")
        for unit_id in candidate_plan.ordered_unit_ids
    )
    if len(normalized_signatures) > 1 and len(set(normalized_signatures)) == 1:
        _add_reason(reasons, "enumeration_only", "INPUT_ENUMERATION")
    if (
        len(candidate_plan.ordered_unit_ids) >= 3
        and all(len(group) == 1 for group in candidate_plan.sentence_groups)
        and candidate_plan.variation_signature.connection == "parallel"
        and candidate_plan.variation_signature.speaker_presence == "implicit_emlis"
        and surface.text.count("また、") >= 2
    ):
        _add_reason(reasons, "enumeration_only", "INPUT_ENUMERATION")

    if (
        not surface.predicate_families
        or any(
            not family.startswith("human_response_")
            for family in surface.predicate_families
        )
        or not _RECEPTION_STANCE_RE.search(surface.text)
        or _OBSERVATION_ROLE_RE.search(surface.text)
    ):
        _add_reason(
            reasons,
            "section_role_distinctness",
            "SECTION_ROLE_NOT_DISTINCT",
        )

    surface_issues = validate_reception_surface_candidate_v2(
        surface,
        candidate_plan,
        content_plan,
        reception_plan,
        resolver,
    )
    if surface_issues:
        _add_reason(reasons, "surface_integrity", "CANDIDATE_SURFACE_UNNATURAL")
    if not sentences or len(set(sentences)) != len(sentences):
        _add_reason(reasons, "surface_integrity", "SURFACE_INTEGRITY_FAILED")

    sentence_count = surface.sentence_count
    depth = content_plan.depth
    if (
        (depth == "minimal" and not 1 <= sentence_count <= 2)
        or (depth == "focused" and not 2 <= sentence_count <= 3)
        or (depth == "layered" and not 3 <= sentence_count <= 4)
        or not (
            content_plan.sentence_budget.min
            <= sentence_count
            <= content_plan.sentence_budget.max
        )
    ):
        _add_reason(
            reasons,
            "depth_proportionality",
            "RICH_INPUT_COLLAPSED"
            if depth == "layered"
            else "SHORT_INPUT_INFLATED",
        )

    source_meta = {
        "content_plan": content_plan.as_body_free_meta(),
        "surface_candidate": surface.as_body_free_meta(),
        "candidate_plan": asdict(candidate_plan),
    }
    encoded_meta = json.dumps(source_meta, ensure_ascii=False, sort_keys=True)
    if (
        _FORBIDDEN_META_KEYS & set(_walk_keys(source_meta))
        or surface.text in encoded_meta
    ):
        _add_reason(reasons, "body_free_meta", "BODY_LEAK")

    checks = tuple(
        ReceptionHardGateCheckV2(
            code=code,
            status="failed" if reasons[code] else "passed",
            reason_codes=_dedupe(reasons[code]),
        )
        for code in HARD_GATE_CODES
    )
    failed_codes = tuple(check.code for check in checks if check.status == "failed")
    return (
        ReceptionHardGateResultV2(
            status="failed" if failed_codes else "passed",
            failed_codes=failed_codes,
            checks=checks,
        ),
        coverage,
    )


def _predicate_uniqueness(surface: ReceptionSurfaceCandidateV2) -> float:
    if not surface.predicate_families:
        return 0.0
    return len(set(surface.predicate_families)) / len(surface.predicate_families)


def _score_candidate(
    observation_plan: GroundedObservationPlan,
    content_plan: ReceptionContentPlanV2,
    candidate_plan: ReceptionCandidatePlanV2,
    surface: ReceptionSurfaceCandidateV2,
) -> tuple[ReceptionCandidateSoftScoresV2, float, tuple[str, ...]]:
    units = _unit_index(content_plan)
    rows = tuple(units[unit_id] for unit_id in candidate_plan.ordered_unit_ids)
    normalized_signatures = {
        unit.semantic_signature.removeprefix("emlis_reception_of_")
        for unit in rows
    }
    signature_ratio = len(normalized_signatures) / max(1, len(rows))
    predicate_ratio = _predicate_uniqueness(surface)
    relation_specificity = sum(
        kind.startswith(("relation_", "nominalized_relation_"))
        for kind in surface.referent_kinds
    ) / max(1, len(surface.referent_kinds))
    structured_specificity = sum(
        kind.startswith("structured_label_") for kind in surface.referent_kinds
    ) / max(1, len(surface.referent_kinds))
    nominalized_ratio = sum(
        kind.startswith("nominalized_") for kind in surface.referent_kinds
    ) / max(1, len(surface.referent_kinds))
    input_specificity = _score(
        0.69
        + 0.15 * bool(surface.source_anchor_count)
        + 0.07 * relation_specificity
        + 0.10 * structured_specificity
        + 0.09 * min(1.0, len(rows) / 3)
        - 0.09 * nominalized_ratio
    )
    content_distinctness = _score(0.58 + 0.27 * signature_ratio + 0.15 * predicate_ratio)
    discourse_coherence = _score(
        0.86
        + 0.05 * any(len(group) == 2 for group in candidate_plan.sentence_groups)
        + 0.03
        * (len(rows) > 1 and candidate_plan.strategy_code == "contrast_then_felt")
    )
    explicit_emlis = candidate_plan.variation_signature.speaker_presence != (
        "implicit_emlis"
    ) or "Emlis" in surface.text
    emlis_presence = _score(0.94 + 0.06 * explicit_emlis)
    quote_chars = sum(len(value) for value in _QUOTE_RE.findall(surface.text))
    quote_ratio = quote_chars / max(1, len(_normalized(surface.text)))
    quote_independence = _score(1.0 - min(0.20, quote_ratio * 0.90))
    observation_reception_separation = _score(
        0.97
        + 0.03 * explicit_emlis
        - 0.10 * bool(_OBSERVATION_ROLE_RE.search(surface.text))
    )
    uncertainty_repetition = max(
        0,
        len(
            re.findall(
                r"(?:分からない部分|その不明さ|まだ決めつけず)",
                surface.text,
            )
        )
        - 1,
    )
    lexical_repetition = _score(
        0.64 + 0.36 * predicate_ratio - 0.12 * uncertainty_repetition
    )
    syntactic_variation = _score(
        0.78
        + 0.08 * any(len(group) == 2 for group in candidate_plan.sentence_groups)
        + 0.07
        * (
            len(rows) > 1
            and candidate_plan.variation_signature.connection != "parallel"
        )
        + 0.06
        * (
            len(rows) > 1
            and
            candidate_plan.variation_signature.referent
            != "semantic_paraphrase"
        )
    )
    target_sentences = content_plan.sentence_budget.target
    distance = abs(surface.sentence_count - target_sentences)
    depth_fit = _score(1.0 if distance == 0 else 0.86 if distance == 1 else 0.65)
    target_polarities = {
        nucleus.semantic_frame.polarity
        for nucleus in observation_plan.nuclei
        if nucleus.nucleus_id in surface.grounded_nucleus_ids
    }
    terminal_family = candidate_plan.variation_signature.terminal_family
    temperature_fit = 0.92
    if observation_plan.safety_policy.identity_claim_must_not_be_accepted_as_fact:
        temperature_fit = 1.0 if terminal_family == "bounded_counterposition" else 0.95
    elif all(
        unit.semantic_signature.removeprefix("emlis_reception_of_")
        == "expression_or_label_present"
        for unit in rows
    ):
        temperature_fit = 1.0 if terminal_family == "felt_reception" else 0.95
    elif target_polarities <= {"positive", "neutral"}:
        temperature_fit = 0.98 if terminal_family in {
            "felt_reception",
            "attention_hold",
        } else 0.92
    elif "negative" in target_polarities and any(
        unit.semantic_signature in {
            "current_burden_present",
            "emlis_reception_of_current_burden_present",
        }
        for unit in rows
    ):
        temperature_fit = 1.0 if terminal_family in {
            "meaning_preservation",
            "restraint",
        } else 0.96 if terminal_family == "felt_reception" else 0.92
    elif "uncertain" in {
        nucleus.semantic_frame.modality
        for nucleus in observation_plan.nuclei
        if nucleus.nucleus_id in surface.grounded_nucleus_ids
    }:
        temperature_fit = 0.98 if terminal_family in {
            "restraint",
            "meaning_preservation",
        } else 0.93
    temperature_fit = _score(temperature_fit)
    restraint = _score(
        1.0
        - 0.25 * bool(_UNSUPPORTED_RE.search(surface.text))
        - 0.20 * bool(_CAUSAL_CONNECTOR_RE.search(surface.text))
        - 0.10 * (surface.source_anchor_count > 1)
    )
    scores = ReceptionCandidateSoftScoresV2(
        input_specificity=input_specificity,
        content_distinctness=content_distinctness,
        discourse_coherence=discourse_coherence,
        emlis_presence=emlis_presence,
        quote_independence=quote_independence,
        observation_reception_separation=observation_reception_separation,
        lexical_repetition=lexical_repetition,
        syntactic_variation=syntactic_variation,
        depth_fit=depth_fit,
        temperature_fit=temperature_fit,
        restraint=restraint,
    )
    mapping = scores.as_mapping()
    total = round(
        sum(mapping[axis] * weight for axis, weight in SOFT_SCORE_WEIGHTS),
        6,
    )
    reason_codes = (
        f"score_profile:{RECEPTION_SELECTOR_CONFIG_V2_VERSION}",
        f"strategy:{candidate_plan.strategy_code}",
        f"opening:{candidate_plan.variation_signature.opening}",
        f"referent:{candidate_plan.variation_signature.referent}",
        f"terminal:{terminal_family}",
    )
    return scores, total, reason_codes


def _evaluation_rank(
    evaluation: ReceptionCandidateEvaluationV2,
    surface_index: Mapping[str, ReceptionSurfaceCandidateV2],
) -> tuple[float, int, int, str]:
    if evaluation.total_score is None:
        raise ReceptionCandidateSelectorV2Error("passed_candidate_score_missing")
    surface = surface_index[evaluation.candidate_id]
    covered_required = len(
        set(evaluation.coverage.required_unit_ids)
        & set(evaluation.coverage.covered_unit_ids)
    )
    return (
        -evaluation.total_score,
        -covered_required,
        surface.source_anchor_count,
        evaluation.candidate_id,
    )


def evaluate_and_select_reception_candidate_v2(
    observation_plan: GroundedObservationPlan,
    content_plan: ReceptionContentPlanV2,
    candidate_plan_set: ReceptionCandidatePlanSetV2,
    surface_candidate_set: ReceptionSurfaceCandidateSetV2,
    resolver: EvidenceSpanResolver,
) -> ReceptionCandidateSelectionV2:
    """Hard-gate every candidate and select only among passed candidates."""

    if not isinstance(observation_plan, GroundedObservationPlan):
        raise ReceptionCandidateSelectorV2Error("grounded_observation_plan_required")
    if content_plan.schema_version != RECEPTION_CONTENT_PLAN_V2_SCHEMA_VERSION:
        raise ReceptionCandidateSelectorV2Error("content_plan_schema_mismatch")
    if candidate_plan_set.schema_version != RECEPTION_CANDIDATE_SET_V2_SCHEMA_VERSION:
        raise ReceptionCandidateSelectorV2Error("candidate_plan_set_schema_mismatch")
    if surface_candidate_set.schema_version != (
        RECEPTION_SURFACE_CANDIDATE_SET_V2_SCHEMA_VERSION
    ):
        raise ReceptionCandidateSelectorV2Error("surface_candidate_set_schema_mismatch")
    if not (
        content_plan.plan_id
        == candidate_plan_set.content_plan_id
        == surface_candidate_set.content_plan_id
    ):
        raise ReceptionCandidateSelectorV2Error("content_plan_identity_mismatch")
    plan_index = {
        candidate.candidate_id: candidate
        for candidate in candidate_plan_set.candidates
    }
    surface_index = {
        candidate.candidate_id: candidate
        for candidate in surface_candidate_set.candidates
    }
    if tuple(plan_index) != tuple(surface_index):
        raise ReceptionCandidateSelectorV2Error("candidate_set_order_mismatch")

    evaluations: list[ReceptionCandidateEvaluationV2] = []
    for candidate_id in plan_index:
        candidate_plan = plan_index[candidate_id]
        surface = surface_index[candidate_id]
        hard_gate, coverage = _evaluate_hard_gate(
            observation_plan,
            content_plan,
            candidate_plan,
            surface,
            resolver,
        )
        if hard_gate.status == "passed":
            soft_scores, total_score, reason_codes = _score_candidate(
                observation_plan,
                content_plan,
                candidate_plan,
                surface,
            )
        else:
            soft_scores = None
            total_score = None
            reason_codes = ()
        evaluations.append(
            ReceptionCandidateEvaluationV2(
                schema_version=RECEPTION_CANDIDATE_EVALUATION_V2_SCHEMA_VERSION,
                candidate_id=candidate_id,
                content_plan_id=content_plan.plan_id,
                hard_gate=hard_gate,
                coverage=coverage,
                soft_scores=soft_scores,
                total_score=total_score,
                score_reason_codes=reason_codes,
                selected=False,
                body_free=True,
            )
        )

    passed = tuple(
        evaluation
        for evaluation in evaluations
        if evaluation.hard_gate.status == "passed"
    )
    selected_id: str | None = None
    if passed:
        selected_id = min(
            passed,
            key=lambda evaluation: _evaluation_rank(evaluation, surface_index),
        ).candidate_id
        evaluations = [
            replace(evaluation, selected=evaluation.candidate_id == selected_id)
            for evaluation in evaluations
        ]
    selection = ReceptionCandidateSelectionV2(
        schema_version=RECEPTION_CANDIDATE_SELECTION_V2_SCHEMA_VERSION,
        selector_config_version=RECEPTION_SELECTOR_CONFIG_V2_VERSION,
        content_plan_id=content_plan.plan_id,
        source_candidate_set_schema_version=candidate_plan_set.schema_version,
        source_surface_set_schema_version=surface_candidate_set.schema_version,
        status="selected" if selected_id else "v2_no_valid_candidate",
        selected_candidate_id=selected_id,
        local_failure_code=None if selected_id else "v2_no_valid_candidate",
        hard_gate_pass_count=len(passed),
        hard_gate_fail_count=len(evaluations) - len(passed),
        evaluations=tuple(evaluations),
        stable_tie_break_applied=True,
        v1_fallback_used=False,
        runtime_connected=False,
        body_free=True,
    )
    issues = validate_reception_candidate_selection_v2(
        selection,
        candidate_plan_set,
        surface_candidate_set,
    )
    if issues:
        raise ReceptionCandidateSelectorV2Error(
            "invalid_candidate_selection:" + ",".join(issues)
        )
    return selection


def resolve_selected_reception_surface_v2(
    selection: ReceptionCandidateSelectionV2,
    surface_candidate_set: ReceptionSurfaceCandidateSetV2,
) -> ReceptionSurfaceCandidateV2:
    """Resolve the selected process-local body without adding it to metadata."""

    if selection.status != "selected" or not selection.selected_candidate_id:
        raise ReceptionCandidateSelectorV2Error("v2_no_valid_candidate")
    for candidate in surface_candidate_set.candidates:
        if candidate.candidate_id == selection.selected_candidate_id:
            return candidate
    raise ReceptionCandidateSelectorV2Error("selected_candidate_body_missing")


def validate_reception_candidate_selection_v2(
    selection: ReceptionCandidateSelectionV2,
    candidate_plan_set: ReceptionCandidatePlanSetV2,
    surface_candidate_set: ReceptionSurfaceCandidateSetV2,
) -> tuple[str, ...]:
    issues: list[str] = []
    if selection.schema_version != RECEPTION_CANDIDATE_SELECTION_V2_SCHEMA_VERSION:
        issues.append("selection_schema_mismatch")
    if selection.selector_config_version != RECEPTION_SELECTOR_CONFIG_V2_VERSION:
        issues.append("selector_config_version_mismatch")
    if selection.content_plan_id != candidate_plan_set.content_plan_id:
        issues.append("selection_content_plan_id_mismatch")
    if tuple(item.candidate_id for item in selection.evaluations) != tuple(
        item.candidate_id for item in candidate_plan_set.candidates
    ):
        issues.append("evaluation_candidate_order_mismatch")
    surface_index = {
        item.candidate_id: item for item in surface_candidate_set.candidates
    }
    passed = tuple(
        item for item in selection.evaluations if item.hard_gate.status == "passed"
    )
    selected = tuple(item for item in selection.evaluations if item.selected)
    if selection.hard_gate_pass_count != len(passed):
        issues.append("hard_gate_pass_count_mismatch")
    if selection.hard_gate_fail_count != len(selection.evaluations) - len(passed):
        issues.append("hard_gate_fail_count_mismatch")
    for evaluation in selection.evaluations:
        if evaluation.schema_version != RECEPTION_CANDIDATE_EVALUATION_V2_SCHEMA_VERSION:
            issues.append(f"{evaluation.candidate_id}:evaluation_schema_mismatch")
        if tuple(check.code for check in evaluation.hard_gate.checks) != HARD_GATE_CODES:
            issues.append(f"{evaluation.candidate_id}:hard_gate_order_mismatch")
        failed_codes = tuple(
            check.code
            for check in evaluation.hard_gate.checks
            if check.status == "failed"
        )
        if evaluation.hard_gate.failed_codes != failed_codes:
            issues.append(f"{evaluation.candidate_id}:failed_code_mismatch")
        if evaluation.hard_gate.status == "passed":
            if evaluation.soft_scores is None or evaluation.total_score is None:
                issues.append(f"{evaluation.candidate_id}:soft_score_missing")
            elif not 0.0 <= evaluation.total_score <= 1.0:
                issues.append(f"{evaluation.candidate_id}:total_score_invalid")
            elif tuple(evaluation.soft_scores.as_mapping()) != SOFT_SCORE_AXES:
                issues.append(f"{evaluation.candidate_id}:soft_axis_mismatch")
        elif evaluation.soft_scores is not None or evaluation.total_score is not None:
            issues.append(f"{evaluation.candidate_id}:hard_failure_soft_rescue")
        if any(
            not _CODE_RE.fullmatch(reason)
            for check in evaluation.hard_gate.checks
            for reason in check.reason_codes
        ):
            issues.append(f"{evaluation.candidate_id}:reason_code_invalid")
        if evaluation.body_free is not True:
            issues.append(f"{evaluation.candidate_id}:body_free_false")

    if selection.status == "selected":
        if len(selected) != 1 or selected[0].candidate_id != selection.selected_candidate_id:
            issues.append("selected_candidate_contract_invalid")
        elif selected[0].hard_gate.status != "passed":
            issues.append("hard_failed_candidate_selected")
        elif passed:
            expected = min(
                passed,
                key=lambda item: _evaluation_rank(item, surface_index),
            ).candidate_id
            if selection.selected_candidate_id != expected:
                issues.append("stable_tie_break_mismatch")
        if selection.local_failure_code is not None:
            issues.append("selected_local_failure_present")
    elif selection.status == "v2_no_valid_candidate":
        if passed or selected or selection.selected_candidate_id is not None:
            issues.append("no_valid_candidate_contract_invalid")
        if selection.local_failure_code != "v2_no_valid_candidate":
            issues.append("no_valid_candidate_failure_code_missing")
    else:
        issues.append("selection_status_invalid")
    if selection.v1_fallback_used is not False:
        issues.append("v1_fallback_must_not_mask_offline_failure")
    if selection.runtime_connected is not False:
        issues.append("runtime_connection_forbidden")
    if selection.stable_tie_break_applied is not True:
        issues.append("stable_tie_break_missing")
    meta = selection.as_body_free_meta()
    if _FORBIDDEN_META_KEYS & set(_walk_keys(meta)):
        issues.append("body_free_meta_key_forbidden")
    encoded = json.dumps(meta, ensure_ascii=False, sort_keys=True)
    if any(candidate.text in encoded for candidate in surface_candidate_set.candidates):
        issues.append("candidate_body_leaked_to_meta")
    return _dedupe(issues)


def selector_config_as_body_free_meta() -> dict[str, Any]:
    """Expose only the frozen Step 7 numeric/configuration contract."""

    return {
        "schema_version": RECEPTION_SELECTOR_CONFIG_V2_VERSION,
        "hard_gate_codes": list(HARD_GATE_CODES),
        "soft_score_axes": list(SOFT_SCORE_AXES),
        "soft_score_weights": dict(SOFT_SCORE_WEIGHTS),
        "candidate_limits": {
            depth: {
                "minimum": values[0],
                "maximum": values[1],
                "target": values[2],
            }
            for depth, values in CANDIDATE_LIMIT_FREEZE.items()
        },
        "distribution_thresholds": dict(DISTRIBUTION_THRESHOLD_FREEZE),
        "random_selection_used": False,
        "case_specific_weight_used": False,
        "v1_fallback_counts_as_v2_success": False,
        "candidate_body_included": False,
        "runtime_connected": False,
        "public_contract_changed": False,
    }


__all__ = [
    "RECEPTION_CANDIDATE_EVALUATION_V2_SCHEMA_VERSION",
    "RECEPTION_CANDIDATE_SELECTION_V2_SCHEMA_VERSION",
    "RECEPTION_SELECTOR_CONFIG_V2_VERSION",
    "HARD_GATE_CODES",
    "SOFT_SCORE_AXES",
    "SOFT_SCORE_WEIGHTS",
    "CANDIDATE_LIMIT_FREEZE",
    "DISTRIBUTION_THRESHOLD_FREEZE",
    "ReceptionCandidateSelectorV2Error",
    "ReceptionHardGateCheckV2",
    "ReceptionHardGateResultV2",
    "ReceptionCandidateCoverageV2",
    "ReceptionCandidateSoftScoresV2",
    "ReceptionCandidateEvaluationV2",
    "ReceptionCandidateSelectionV2",
    "evaluate_and_select_reception_candidate_v2",
    "resolve_selected_reception_surface_v2",
    "validate_reception_candidate_selection_v2",
    "selector_config_as_body_free_meta",
]
