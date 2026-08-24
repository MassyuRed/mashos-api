#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""Generate the disabled CMEE V1-A private Product-Read packet.

Stdout is body-free. Full synthetic input and generated text are written only
when ``--body-full-output`` is explicitly supplied; that file is private and
must not be committed.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
from typing import Any, Mapping


AI_ROOT = Path(__file__).resolve().parents[1]
AI_INFERENCE = AI_ROOT / "services" / "ai_inference"
if str(AI_INFERENCE) not in sys.path:
    sys.path.insert(0, str(AI_INFERENCE))

from emlis_ai_current_input_bundle import build_emlis_current_input_bundle  # noqa: E402
from emlis_ai_grounded_observation_plan import (  # noqa: E402
    build_final_stage1_grounded_observation_plan,
)
from cocolon_meaning_experience_engine import GenerationRequest, MeaningExperienceEngine  # noqa: E402
import cocolon_meaning_experience_engine.emlis_stage1_composition as stage1_composition  # noqa: E402
import cocolon_meaning_experience_engine.emlis_stage1_response as stage1_response  # noqa: E402
from cocolon_meaning_experience_engine.contracts import (  # noqa: E402
    AttachmentAdmission,
    CMEE_COMMON_GUARD_PROOF_VERSION,
    CMEE_STAGE1_TRACE_EXTENSION_SCHEMA_VERSION,
    CMEE_TERMINAL_GENERATED_DISABLED,
    CommonGuardProof,
    CommonGuardResultProof,
    EmlisStage1PositiveTraceExtension,
    EmlisTraceClaimDomain,
    EpistemicState,
    ExperiencePlan,
    GenerationArtifactBundle,
    GroundedMeaningGraph,
    MeaningNode,
    OwnerClass,
    ProviderResolution,
    RouteBDisposition,
    VisibleAuthority,
    VisibleUnitTrace,
    VisibleUnknownUnit,
)
from cocolon_meaning_experience_engine.emlis_v1a import (  # noqa: E402
    COMMON_GUARD_STABILIZATION_CORE_ID,
    COMMON_GUARD_STABILIZATION_PHASE,
    COMMON_GUARD_STABILIZATION_REPORT_NAME,
    EXPECTED_COMMON_GUARD_IDS,
    REALIZER_CONTRACT_IDS,
    TRUST_POLICY_IDS,
    _build_experience_plan,
    _build_graph,
    _common_guard_proof_id,
    _ordered,
    _planned_visible_source_ids,
)
from cocolon_meaning_experience_engine.source_kernel import freeze_text_source  # noqa: E402


EXACT8: tuple[tuple[str, str, str, str, str], ...] = (
    ("SX-01", "疲れているけれど、少し整えたい気持ちもある。", "生活", "自己理解", "medium"),
    ("SX-02", "続けたいのに限界が近い感じがある。", "仕事", "不安", "medium"),
    (
        "SX-03",
        "今日は仕事の話を受けたあと、納得したい気持ちと引っかかりが残っている。",
        "仕事",
        "自己理解",
        "medium",
    ),
    (
        "SX-04",
        "だるいし何もしたくない。相談したいけど迷惑かもしれない。",
        "健康",
        "不安",
        "strong",
    ),
    ("SX-05", "環境を変えたいけど変えられなくて疲れた。", "生活", "不安", "medium"),
    (
        "SX-06",
        "変えたいのに動けなくて疲れた。ずっとこのままなのが不安で、どうしたらいいのか考えている。",
        "生活",
        "不安",
        "strong",
    ),
    (
        "SX-07",
        "この職場でやっていけるか不安。でも、続けられる形は探したい。",
        "仕事",
        "不安",
        "medium",
    ),
    (
        "SX-08",
        "今日は仕事で疲れたけど、帰ってから少し散歩したら落ち着いた。",
        "生活",
        "平穏",
        "medium",
    ),
)

# Public-safe early inputs are review material, not expected-output fixtures.
# Their family labels remain outside every production request and selector.
EARLY_KNOWN_EXACT4: tuple[tuple[str, str, str, str, str], ...] = (
    (
        "tension",
        "続けたい気持ちはある。でも、もうかなり無理をしている気もする。",
        "生活",
        "不安",
        "medium",
    ),
    (
        "temporal_change",
        "散歩に出たら、少し落ち着いた。ただ、いつもそうなるとは思っていない。",
        "生活",
        "不安",
        "medium",
    ),
    (
        "help_seeking",
        "相談したい。でも、迷惑かもしれないと思うと切り出せない。",
        "生活",
        "不安",
        "medium",
    ),
    (
        "unfinished",
        "仕事の話はした。でも、まだ気持ちが残っていて、どうしたいかは分からない。",
        "生活",
        "不安",
        "medium",
    ),
)
EARLY_STRUCTURAL_FAMILIES = tuple(row[0] for row in EARLY_KNOWN_EXACT4)
EARLY_WITHHELD_INPUT_SCHEMA_VERSION = (
    "cocolon.cmee.stage1.withheld_early_input.v1"
)
EARLY_KNOWN_VISIBLE_SCHEMA_VERSION = (
    "cocolon.cmee.stage1.known_early_actual_visible.v1"
)
EARLY_WITHHELD_BODY_FREE_SCHEMA_VERSION = (
    "cocolon.cmee.stage1.withheld_early_machine_body_free.v1"
)
EARLY_BODY_FREE_PACKET_SCHEMA_VERSION = (
    "cocolon.cmee.stage1.early_actual_body_free.v1"
)
EARLY_HUMAN_READ_RESULT_SCHEMA_VERSION = (
    "cocolon.cmee.stage1.early_human_read_result.v1"
)
EARLY_PRIVATE_PACKET_SCHEMA_VERSION = (
    "cocolon.cmee.stage1.withheld_early_private_packet.v1"
)
EARLY_BOUNDED_UNIT_ID = (
    "cocolon.cmee.stage1.additional_correction.route_a.20260824.v1"
)
WITHHELD_EARLY_PACKET_ID = (
    "CMEE_STAGE1_ADDITIONAL_CORRECTION_WITHHELD_EARLY_20260824_V1"
)
WITHHELD_EARLY_PRIVATE_SLOT_ID = (
    "PRIVATE_SLOT_WITHHELD_EARLY_20260824_V1"
)
STEP2_FROZEN_LANGUAGE_CORE_IDENTITY = (
    "b74ea2f448011c8a721ed0b08bca8caa5c794e3f07c149612030451015953ae9"
)
EARLY_HUMAN_READ_RESULTS = (
    "CLEAR",
    "COMMON_DEFECT",
    "ROUTE_LEVEL_CEILING",
)
EARLY_COMMON_DEFECT_CAUSE_COMPONENTS = (
    "SUBJECTIVE_MEANING_PLANNER",
    "DISCOURSE_PLANNER",
    "RESPONSE_OBJECT_EXPRESSION",
    "GROUNDED_JAPANESE_COMPOSER",
    "WHOLE_ARTIFACT_NORMALIZER",
)
EARLY_COMMON_DEFECT_CLASSES = (
    "SURFACE_SEAM",
    "SAME_FAMILY_CONCENTRATION",
    "GENERIC_SUBJECTIVE_CONTENT",
    "NON_IDIOMATIC_SURFACE",
)
EARLY_ROUTE_LEVEL_CEILING_REASONS = (
    "CASE_OR_PHRASE_FAMILY_RULE_REQUIRED",
    "FINISHED_SENTENCE_REQUIRED",
    "NEW_ENUM_OR_AXIS_REQUIRED",
    "NEW_ASSET_FAMILY_REQUIRED",
    "LISTED_OUTSIDE_PATH_OR_PROVIDER_REQUIRED",
    "TYPED_PROFILE_CANNOT_RESOLVE_IDIOMATICITY",
)

STAGE1_KAREN_DERIVED_MUTATION_SET_ID = (
    "STAGE1_KAREN_DERIVED_MUTATION_SET_V1"
)
STAGE1_KAREN_DERIVED_AFTER_PACKET_ID = (
    "CMEE_STAGE1_KAREN_DERIVED_AFTER_EXACT8_20260823_V2"
)
STAGE1_KAREN_DERIVED_AFTER_PRIVATE_SLOT_ID = (
    "PRIVATE_SLOT_AFTER_EXACT8_20260823_V2"
)
STAGE1_KAREN_DERIVED_MUTATION_SET_V1: tuple[
    tuple[str, str, str], ...
] = (
    ("KDM-SE-01", "SEMANTIC_EQUIVALENCE_MUTATION", "REGISTER_INFLECTION"),
    ("KDM-SE-02", "SEMANTIC_EQUIVALENCE_MUTATION", "LEXICAL_PARAPHRASE"),
    ("KDM-SE-03", "SEMANTIC_EQUIVALENCE_MUTATION", "CLAUSE_ORDER"),
    ("KDM-RC-01", "RELATION_CONTRAST_MUTATION", "TEMPORAL_ORDER"),
    ("KDM-RC-02", "RELATION_CONTRAST_MUTATION", "COEXISTENCE_TENSION"),
    ("KDM-RC-03", "RELATION_CONTRAST_MUTATION", "SEQUENCE_CAUSE"),
    ("KDM-CB-01", "CLAIM_BOUNDARY_MUTATION", "NEGATION"),
    ("KDM-CB-02", "CLAIM_BOUNDARY_MUTATION", "MODALITY"),
    ("KDM-CB-03", "CLAIM_BOUNDARY_MUTATION", "EXPERIENCER"),
    ("KDM-CB-04", "CLAIM_BOUNDARY_MUTATION", "MATERIAL_UNRELATED"),
    ("KDM-SU-01", "SUBJECTIVITY_MUTATION", "SOURCE_STRENGTH"),
    ("KDM-SU-02", "SUBJECTIVITY_MUTATION", "DISCOMFORT_PERSON_TARGET"),
)

PRODUCT_READ_AXES = (
    "PRIMARY_MEANING_RETAINED",
    "RELATION_DIRECTION_CORRECT",
    "NO_CAUSE_PERSONALITY_DIAGNOSIS_PROMOTION",
    "UNKNOWN_BOUNDARY_PRESERVED",
    "SELF_DENIAL_NOT_ADOPTED_OR_AMPLIFIED",
    "BOUND_EMLIS_RECEPTION",
    "SECTION_SEMANTIC_DISTINCTNESS",
    "NATURAL_NON_REPETITIVE_SURFACE",
    "DISTRIBUTION_NOT_OVERCONCENTRATED",
    "DEPTH_PROPORTIONAL",
    "NO_FALSE_UNDERSTANDING_COMPLETION",
    "IMMEDIATE_OBSERVATION_FEELS_READ",
)
PRIVATE_OUTPUT_ROOT = Path(
    os.environ.get("CMEE_PRIVATE_OUTPUT_ROOT", "/tmp/cocolon-cmee-v1a-private")
).resolve()
CHECKOUT_ROOT = AI_ROOT.parent.resolve()


def _body_free_mutation_registry() -> dict[str, Any]:
    expected_classes = (
        ("SEMANTIC_EQUIVALENCE_MUTATION", 3),
        ("RELATION_CONTRAST_MUTATION", 3),
        ("CLAIM_BOUNDARY_MUTATION", 4),
        ("SUBJECTIVITY_MUTATION", 2),
    )
    case_ids = tuple(row[0] for row in STAGE1_KAREN_DERIVED_MUTATION_SET_V1)
    if (
        len(STAGE1_KAREN_DERIVED_MUTATION_SET_V1) != 12
        or len(case_ids) != len(set(case_ids))
        or any(
            sum(row[1] == class_name for row in STAGE1_KAREN_DERIVED_MUTATION_SET_V1)
            != expected_count
            for class_name, expected_count in expected_classes
        )
    ):
        raise RuntimeError("stage1_mutation_registry_invalid")
    return {
        "set_id": STAGE1_KAREN_DERIVED_MUTATION_SET_ID,
        "case_count": len(STAGE1_KAREN_DERIVED_MUTATION_SET_V1),
        "body_payload_present": False,
        "runner_executes_source_bodies": False,
        "execution_owner": "current_and_new_tests",
        "class_counts": {
            class_name: expected_count
            for class_name, expected_count in expected_classes
        },
        "cases": [
            {
                "case_id": case_id,
                "mutation_class": mutation_class,
                "mutation_operator": mutation_operator,
            }
            for case_id, mutation_class, mutation_operator
            in STAGE1_KAREN_DERIVED_MUTATION_SET_V1
        ],
    }


def _raw(case_id: str, memo: str, category: str, emotion: str, strength: str) -> dict[str, Any]:
    return {
        "id": f"cmee-i1sx-{case_id.lower()}",
        "created_at": "2026-08-15T00:00:00Z",
        "memo": memo,
        "memo_action": "",
        "category": [category],
        "emotion_details": [{"type": emotion, "strength": strength}],
        "emotions": [emotion],
        "is_secret": False,
    }


def _valid_ref_tuple(value: object, *, allow_empty: bool = False) -> bool:
    return (
        type(value) is tuple
        and (allow_empty or bool(value))
        and all(type(ref) is str and bool(ref) for ref in value)
        and len(value) == len(set(value))
    )


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical_sha256(value: object) -> str:
    return _sha256_text(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    )


def _validate_early_repo_heads(
    *,
    runtime_repo_head: str,
    design_repo_head: str,
) -> None:
    if any(
        re.fullmatch(r"[0-9a-f]{40}", head) is None
        for head in (runtime_repo_head, design_repo_head)
    ):
        raise ValueError("early private packet repo head binding invalid")


def _validate_withheld_early_payload(
    payload: object,
) -> tuple[dict[str, str], ...]:
    """Validate the private exact4 without retaining any caller identity field."""

    expected_root_keys = {
        "schema_version",
        "selection_frozen_before_first_after",
        "synthetic_non_identifying",
        "cases",
    }
    if type(payload) is not dict or set(payload) != expected_root_keys:
        raise ValueError("withheld early private input invalid")
    if (
        payload["schema_version"] != EARLY_WITHHELD_INPUT_SCHEMA_VERSION
        or payload["selection_frozen_before_first_after"] is not True
        or payload["synthetic_non_identifying"] is not True
        or type(payload["cases"]) is not list
        or len(payload["cases"]) != len(EARLY_STRUCTURAL_FAMILIES)
    ):
        raise ValueError("withheld early private input invalid")

    expected_case_keys = {
        "structural_family",
        "memo",
        "category",
        "emotion",
        "strength",
    }
    rows: list[dict[str, str]] = []
    for row in payload["cases"]:
        if type(row) is not dict or set(row) != expected_case_keys:
            raise ValueError("withheld early private input invalid")
        if any(type(row[key]) is not str or not row[key] for key in expected_case_keys):
            raise ValueError("withheld early private input invalid")
        if row["strength"] not in {"weak", "medium", "strong"}:
            raise ValueError("withheld early private input invalid")
        rows.append({key: row[key] for key in expected_case_keys})

    if tuple(row["structural_family"] for row in rows) != EARLY_STRUCTURAL_FAMILIES:
        raise ValueError("withheld early private input invalid")
    memos = tuple(row["memo"] for row in rows)
    if (
        len(memos) != len(set(memos))
        or set(memos).intersection(row[1] for row in EARLY_KNOWN_EXACT4)
    ):
        raise ValueError("withheld early private input invalid")
    return tuple(rows)


def _early_case_failure_summary(error: Exception) -> dict[str, Any]:
    return {
        "actual_japanese_reached": False,
        "phase_a_and_b_validated": False,
        "subjective_claim_count": 0,
        "internal_candidate_count": 0,
        "ranked_candidate_count": 0,
        "material_alternate_present": False,
        "normal_form_phase_exact6": False,
        "normal_form_defect_free": False,
        "normalization_idempotent": False,
        "required_duty_coverage_exact": False,
        "language_core_identity_match": False,
        "machine_invariant_clear": False,
        "failure_class": type(error).__name__,
    }


def _materialize_early_case(
    *,
    request_token: str,
    structural_family: str,
    memo: str,
    category: str,
    emotion: str,
    strength: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Run one case through the final Step 2 production call graph only."""

    raw = _raw(request_token, memo, category, emotion, strength)
    public_source = {
        "memo": memo,
        "category": category,
        "emotion": emotion,
        "strength": strength,
    }
    try:
        request = GenerationRequest(
            request_id=f"req-{request_token}",
            current_input_bundle=build_emlis_current_input_bundle(raw),
            expected_source_record_id=str(raw["id"]),
        )
        source = freeze_text_source(request)
        grounded_plan = build_final_stage1_grounded_observation_plan(
            source.normalized_current_input,
            evidence_spans=source.evidence_spans,
        )
        required_nuclei, required_relations, reception_targets = (
            _planned_visible_source_ids(grounded_plan)
        )
        graph = _build_graph(
            source,
            grounded_plan,
            _ordered((*required_nuclei, *reception_targets)),
            required_relations,
        )
        parent_plan = _build_experience_plan(
            source,
            graph,
            grounded_plan,
            required_nuclei,
            required_relations,
            reception_targets,
        )
        phase_a = stage1_response.build_subjective_planning_inputs(
            source=source,
            grounded_graph=graph,
            parent_plan=parent_plan,
            grounded_plan=grounded_plan,
        )
        subjective_plan = stage1_composition.project_subjective_meaning_plan(
            phase_a
        )
        projection = stage1_response.seal_stage1_projection(
            phase_a,
            subjective_plan,
        )
        phase_b = stage1_response.build_surface_composition_inputs(
            phase_a,
            projection,
        )
        result = stage1_composition.compose_stage1_from_projection(phase_b)
        ranked = result.ranked_candidates
        selected = result.selected_candidate
        units = selected.sentence_units
        selected_normalized = selected.normalized_artifact
        repeated = stage1_composition.normalize_to_normal_form(
            selected_normalized,
            selected_normalized.layout_preference_seed,
            phase_b,
        )
        idempotent = (
            stage1_composition.canonical_normalized_bytes(selected_normalized)
            == stage1_composition.canonical_normalized_bytes(repeated)
        )
        realized_duties = tuple(ref for unit in units for ref in unit.duty_refs)
        required_coverage = (
            len(realized_duties) == len(set(realized_duties))
            and set(realized_duties) == set(selected_normalized.required_duty_refs)
        )
        exact6 = all(
            candidate.normalized_artifact.normalization_phase_trace
            == tuple(stage1_composition.NormalFormPhase)
            for candidate in ranked
        )
        defect_free = all(
            candidate.normalized_artifact.correctable_defect_rows == ()
            for candidate in ranked
        )
        japanese_reached = bool(units) and all(
            unit.text.endswith("。")
            and re.search(r"[ぁ-んァ-ヶ一-龯]", unit.text) is not None
            for unit in units
        )
        identity_match = (
            result.language_core_identity
            == stage1_composition.LANGUAGE_CORE_IDENTITY
            == STEP2_FROZEN_LANGUAGE_CORE_IDENTITY
        )
        ranked_count = len(ranked)
        summary = {
            "actual_japanese_reached": japanese_reached,
            "phase_a_and_b_validated": True,
            "subjective_claim_count": len(subjective_plan.subjective_claim_rows),
            "internal_candidate_count": result.internal_candidate_count,
            "ranked_candidate_count": ranked_count,
            "material_alternate_present": (
                result.internal_candidate_count >= 2 and ranked_count >= 2
            ),
            "normal_form_phase_exact6": exact6,
            "normal_form_defect_free": defect_free,
            "normalization_idempotent": idempotent,
            "required_duty_coverage_exact": required_coverage,
            "language_core_identity_match": identity_match,
            "machine_invariant_clear": all(
                (
                    japanese_reached,
                    bool(subjective_plan.subjective_claim_rows),
                    result.internal_candidate_count >= ranked_count,
                    1 <= ranked_count <= 2,
                    tuple(row.rank for row in ranked)
                    == tuple(range(1, ranked_count + 1)),
                    selected.rank == 1,
                    exact6,
                    defect_free,
                    idempotent,
                    required_coverage,
                    identity_match,
                )
            ),
            "failure_class": None,
        }
        actual_japanese = "\n".join(unit.text for unit in units)
    except Exception as error:  # The body-free surface never serializes repr(error).
        summary = _early_case_failure_summary(error)
        actual_japanese = ""

    public_case = {
        "structural_family": structural_family,
        "synthetic_input": public_source,
        "actual_japanese": actual_japanese,
        "machine_invariant": summary,
    }
    private_case = {
        "structural_family": structural_family,
        "synthetic_input_private": raw,
        "candidate_private": actual_japanese,
        "machine_invariant_body_free": summary,
    }
    return public_case, private_case


def _early_private_packet_binding(
    *,
    runtime_repo_head: str,
    design_repo_head: str,
    withheld_set_digest: str,
) -> dict[str, Any]:
    _validate_early_repo_heads(
        runtime_repo_head=runtime_repo_head,
        design_repo_head=design_repo_head,
    )
    material = {
        "binding_version": "cocolon.cmee.stage1.withheld_early_binding.v1",
        "packet_id": WITHHELD_EARLY_PACKET_ID,
        "bounded_unit_id": EARLY_BOUNDED_UNIT_ID,
        "runtime_repo_head": runtime_repo_head,
        "design_repo_head": design_repo_head,
        "language_core_identity": stage1_composition.LANGUAGE_CORE_IDENTITY,
        "known_structural_families": EARLY_STRUCTURAL_FAMILIES,
        "withheld_set_digest": withheld_set_digest,
        "runner_identity": {
            "repo_relative_path": str(
                Path(__file__).resolve().relative_to(CHECKOUT_ROOT)
            ),
            "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
    }
    return {**material, "packet_binding_sha256": _canonical_sha256(material)}


def run_early_actual(
    *,
    withheld_private_payload: object,
    runtime_repo_head: str,
    design_repo_head: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Materialize known exact4 plus private withheld exact4 through one core."""

    _validate_early_repo_heads(
        runtime_repo_head=runtime_repo_head,
        design_repo_head=design_repo_head,
    )
    withheld_rows = _validate_withheld_early_payload(withheld_private_payload)
    fresh_identity = stage1_composition.compute_language_core_identity()
    if (
        fresh_identity != stage1_composition.LANGUAGE_CORE_IDENTITY
        or fresh_identity != STEP2_FROZEN_LANGUAGE_CORE_IDENTITY
    ):
        raise RuntimeError("early language core identity mismatch")

    known_public_cases: list[dict[str, Any]] = []
    known_private_cases: list[dict[str, Any]] = []
    for index, (family, memo, category, emotion, strength) in enumerate(
        EARLY_KNOWN_EXACT4,
        start=1,
    ):
        public_case, private_case = _materialize_early_case(
            request_token=f"early-known-{index:02d}",
            structural_family=family,
            memo=memo,
            category=category,
            emotion=emotion,
            strength=strength,
        )
        known_public_cases.append(public_case)
        known_private_cases.append(private_case)

    withheld_set_digest = _canonical_sha256(
        {
            "schema_version": EARLY_WITHHELD_INPUT_SCHEMA_VERSION,
            "selection_frozen_before_first_after": True,
            "synthetic_non_identifying": True,
            "cases": withheld_rows,
        }
    )
    withheld_private_cases: list[dict[str, Any]] = []
    withheld_summaries: list[dict[str, Any]] = []
    for index, row in enumerate(withheld_rows, start=1):
        _public_case, private_case = _materialize_early_case(
            request_token=f"early-withheld-{index:02d}",
            structural_family=row["structural_family"],
            memo=row["memo"],
            category=row["category"],
            emotion=row["emotion"],
            strength=row["strength"],
        )
        withheld_private_cases.append(private_case)
        withheld_summaries.append(private_case["machine_invariant_body_free"])

    known_summaries = [row["machine_invariant"] for row in known_public_cases]
    known_clear_count = sum(row["machine_invariant_clear"] for row in known_summaries)
    withheld_clear_count = sum(
        row["machine_invariant_clear"] for row in withheld_summaries
    )
    family_counts = {
        family: sum(row["structural_family"] == family for row in withheld_rows)
        for family in EARLY_STRUCTURAL_FAMILIES
    }
    withheld_body_free = {
        "schema_version": EARLY_WITHHELD_BODY_FREE_SCHEMA_VERSION,
        "packet_id": WITHHELD_EARLY_PACKET_ID,
        "bounded_unit_id": EARLY_BOUNDED_UNIT_ID,
        "language_core_identity": fresh_identity,
        "withheld_set_count": len(withheld_rows),
        "structural_family_counts": family_counts,
        "withheld_set_digest": withheld_set_digest,
        "selection_frozen_before_first_after": True,
        "synthetic_non_identifying_attested": True,
        "actual_japanese_reached_count": sum(
            row["actual_japanese_reached"] for row in withheld_summaries
        ),
        "machine_invariant_clear_count": withheld_clear_count,
        "normal_form_phase_exact6_count": sum(
            row["normal_form_phase_exact6"] for row in withheld_summaries
        ),
        "normal_form_defect_free_count": sum(
            row["normal_form_defect_free"] for row in withheld_summaries
        ),
        "normalization_idempotent_count": sum(
            row["normalization_idempotent"] for row in withheld_summaries
        ),
        "required_duty_coverage_exact_count": sum(
            row["required_duty_coverage_exact"] for row in withheld_summaries
        ),
        "material_alternate_case_count": sum(
            row["material_alternate_present"] for row in withheld_summaries
        ),
        "machine_failure_classes": sorted(
            {
                row["failure_class"]
                for row in withheld_summaries
                if row["failure_class"] is not None
            }
        ),
        "machine_invariant_result": (
            "CLEAR"
            if withheld_clear_count == len(withheld_rows)
            else "FAIL"
        ),
        "body_payload_present": False,
        "private_text_published": False,
        "body_full_readers": "PRO_ONLY",
        "ultra_withheld_body_access": 0,
        "mash_withheld_body_access": 0,
        "formal_exact8_denominator_effect": 0,
        "product_acceptance_denominator_effect": 0,
        "numeric_score_or_pass_rate": 0,
        "product_credit": 0,
        "candidate_ready": False,
        "production_effect": 0,
        "automatic_progression": False,
    }
    known_visible = {
        "schema_version": EARLY_KNOWN_VISIBLE_SCHEMA_VERSION,
        "case_count": len(known_public_cases),
        "structural_family_counts": {
            family: sum(
                row["structural_family"] == family for row in known_public_cases
            )
            for family in EARLY_STRUCTURAL_FAMILIES
        },
        "machine_invariant_clear_count": known_clear_count,
        "machine_invariant_result": (
            "CLEAR"
            if known_clear_count == len(known_public_cases)
            else "FAIL"
        ),
        "material_alternate_case_count": sum(
            row["material_alternate_present"] for row in known_summaries
        ),
        "cases": known_public_cases,
    }
    known_body_free = {
        "case_count": len(known_public_cases),
        "structural_family_counts": known_visible["structural_family_counts"],
        "actual_japanese_reached_count": sum(
            row["actual_japanese_reached"] for row in known_summaries
        ),
        "machine_invariant_clear_count": known_clear_count,
        "machine_invariant_result": known_visible["machine_invariant_result"],
        "material_alternate_case_count": known_visible[
            "material_alternate_case_count"
        ],
        "body_payload_present": False,
    }
    body_free_packet = {
        "schema_version": EARLY_BODY_FREE_PACKET_SCHEMA_VERSION,
        "packet_id": WITHHELD_EARLY_PACKET_ID,
        "bounded_unit_id": EARLY_BOUNDED_UNIT_ID,
        "runtime_repo_head": runtime_repo_head,
        "design_repo_head": design_repo_head,
        "language_core_identity": fresh_identity,
        "known_exact4_body_free": known_body_free,
        "withheld_exact4_body_free": withheld_body_free,
        "early_human_read_result": "NOT_RUN",
        "early_actual_status": "NOT_RUN",
        "body_payload_present": False,
        "private_text_published": False,
    }
    private_packet = {
        "schema_version": EARLY_PRIVATE_PACKET_SCHEMA_VERSION,
        "packet_id": WITHHELD_EARLY_PACKET_ID,
        "private_slot_id": WITHHELD_EARLY_PRIVATE_SLOT_ID,
        "private_body_full": True,
        "private_packet_binding": _early_private_packet_binding(
            runtime_repo_head=runtime_repo_head,
            design_repo_head=design_repo_head,
            withheld_set_digest=withheld_set_digest,
        ),
        "language_core_identity": fresh_identity,
        "selection_frozen_before_first_after": True,
        "known_cases": known_private_cases,
        "withheld_cases": withheld_private_cases,
        "human_language_viability_read": {
            "body_full_readers": "PRO_ONLY",
            "early_human_read_result": None,
            "defect_class": None,
            "cause_component": None,
            "ceiling_reason": None,
        },
    }
    return body_free_packet, known_visible, private_packet


def validate_early_human_read_result(
    payload: object,
    *,
    body_free_machine_packet: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate Pro's sole body-free human transition input exact1."""

    expected_keys = (
        "schema_version",
        "packet_id",
        "bounded_unit_id",
        "runtime_repo_head",
        "design_repo_head",
        "language_core_identity",
        "withheld_set_digest",
        "reviewed_known_count",
        "reviewed_withheld_count",
        "body_payload_present",
        "early_human_read_result",
        "defect_class",
        "cause_component",
        "ceiling_reason",
    )
    if type(payload) is not dict or set(payload) != set(expected_keys):
        raise ValueError("early human read result invalid")
    if type(body_free_machine_packet) is not dict:
        raise ValueError("early human read machine binding invalid")
    known = body_free_machine_packet.get("known_exact4_body_free")
    withheld = body_free_machine_packet.get("withheld_exact4_body_free")
    if type(known) is not dict or type(withheld) is not dict:
        raise ValueError("early human read machine binding invalid")
    machine_bindings = {
        "packet_id": body_free_machine_packet.get("packet_id"),
        "bounded_unit_id": body_free_machine_packet.get("bounded_unit_id"),
        "runtime_repo_head": body_free_machine_packet.get("runtime_repo_head"),
        "design_repo_head": body_free_machine_packet.get("design_repo_head"),
        "language_core_identity": body_free_machine_packet.get(
            "language_core_identity"
        ),
        "withheld_set_digest": withheld.get("withheld_set_digest"),
    }
    if (
        body_free_machine_packet.get("schema_version")
        != EARLY_BODY_FREE_PACKET_SCHEMA_VERSION
        or body_free_machine_packet.get("packet_id")
        != WITHHELD_EARLY_PACKET_ID
        or body_free_machine_packet.get("body_payload_present") is not False
        or known.get("case_count") != 4
        or withheld.get("withheld_set_count") != 4
        or known.get("machine_invariant_result") != "CLEAR"
        or withheld.get("machine_invariant_result") != "CLEAR"
        or any(payload[key] != value for key, value in machine_bindings.items())
        or payload["schema_version"] != EARLY_HUMAN_READ_RESULT_SCHEMA_VERSION
        or payload["reviewed_known_count"] != 4
        or payload["reviewed_withheld_count"] != 4
        or payload["body_payload_present"] is not False
        or payload["early_human_read_result"] not in EARLY_HUMAN_READ_RESULTS
    ):
        raise ValueError("early human read result invalid")

    result = payload["early_human_read_result"]
    defect_class = payload["defect_class"]
    cause = payload["cause_component"]
    ceiling = payload["ceiling_reason"]
    if result == "CLEAR":
        conditional_valid = (
            defect_class is None and cause is None and ceiling is None
        )
    elif result == "COMMON_DEFECT":
        conditional_valid = (
            defect_class in EARLY_COMMON_DEFECT_CLASSES
            and cause in EARLY_COMMON_DEFECT_CAUSE_COMPONENTS
            and ceiling is None
        )
    else:
        conditional_valid = (
            defect_class is None
            and cause is None
            and ceiling in EARLY_ROUTE_LEVEL_CEILING_REASONS
        )
    if not conditional_valid:
        raise ValueError("early human read result invalid")
    return {key: payload[key] for key in expected_keys}


def _private_packet_binding(
    *,
    runtime_repo_head: str,
    design_repo_head: str,
) -> dict[str, Any]:
    """Bind one private materialization to both repos, fixture and runner."""

    heads = (runtime_repo_head, design_repo_head)
    if any(re.fullmatch(r"[0-9a-f]{40}", head) is None for head in heads):
        raise ValueError("private packet repo head binding invalid")
    fixture_identity = {
        "fixture_order": [row[0] for row in EXACT8],
        "fixture_and_axes_sha256": _canonical_sha256(
            {
                "exact8": EXACT8,
                "product_read_axes": PRODUCT_READ_AXES,
            }
        ),
    }
    runner_identity = {
        "repo_relative_path": str(Path(__file__).resolve().relative_to(CHECKOUT_ROOT)),
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    material = {
        "binding_version": "cocolon.cmee.stage1.private_packet_binding.v1",
        "packet_id": STAGE1_KAREN_DERIVED_AFTER_PACKET_ID,
        "runtime_repo_head": runtime_repo_head,
        "design_repo_head": design_repo_head,
        "fixture_identity": fixture_identity,
        "runner_identity": runner_identity,
    }
    return {
        **material,
        "packet_binding_sha256": _canonical_sha256(material),
    }


_STRICT_DIRECTIONAL_TRACE_RELATIONS = frozenset(
    {
        "temporal_before_after",
        "shift_from_to",
        "user_stated_cause",
        "user_stated_result",
        "attempt_and_block",
        "action_supports_change",
        "evaluation_about_event",
        "self_evaluation_about_state",
    }
)


def _route_b_dispositions_valid(graph: GroundedMeaningGraph) -> bool:
    """Validate the exact disabled Route B row shapes used by the packet."""

    nodes = {row.node_id: row for row in graph.nodes}
    edges = {row.edge_id: row for row in graph.edges}
    claims = {**nodes, **edges}
    positive = {
        RouteBDisposition.SOURCE_EXPLICIT_VISIBLE,
        RouteBDisposition.SUPPLEMENTAL_USER_VISIBLE,
    }
    for row in graph.owner_dispositions:
        refs = tuple(row.visible_claim_refs)
        if not row.evidence_ids or len(row.evidence_ids) != len(set(row.evidence_ids)):
            return False
        if row.disposition in positive:
            expected_fields = (
                (
                    ProviderResolution.MISSING_OR_INVALID,
                    AttachmentAdmission.UNAVAILABLE,
                    VisibleAuthority.SOURCE_EXPLICIT,
                )
                if row.disposition is RouteBDisposition.SOURCE_EXPLICIT_VISIBLE
                else (
                    ProviderResolution.UNIQUE,
                    AttachmentAdmission.PROVISIONAL_ONLY,
                    VisibleAuthority.SUPPLEMENTAL_USER,
                )
            )
            if (
                (
                    row.provider_resolution,
                    row.attachment_admission,
                    row.visible_authority,
                )
                != expected_fields
                or not refs
                or len(refs) != len(set(refs))
                or row.target_unknown_ref is not None
                or row.reason_codes
            ):
                return False
            for claim_ref in refs:
                claim = claims.get(claim_ref)
                if (
                    claim is None
                    or claim.owner_id != row.owner_id
                    or claim.epistemic_state is not EpistemicState.SOURCE_EXPLICIT
                    or not claim.evidence_ids
                    or not set(claim.evidence_ids).issubset(set(row.evidence_ids))
                ):
                    return False
        elif row.disposition is RouteBDisposition.UNKNOWN_PRESERVED_LIMITED:
            target = nodes.get(row.target_unknown_ref or "")
            if (
                row.provider_resolution is not ProviderResolution.UNRESOLVED
                or row.attachment_admission is not AttachmentAdmission.UNRESOLVED
                or row.visible_authority is not VisibleAuthority.NONE
                or row.target_unknown_ref is None
                or refs != (row.target_unknown_ref,)
                or type(target) is not MeaningNode
                or target.owner_id != row.owner_id
                or target.epistemic_state is not EpistemicState.UNKNOWN
                or target.evidence_ids != row.evidence_ids
                or row.reason_codes != ("ATTACHMENT_UNRESOLVED",)
            ):
                return False
        elif row.disposition is RouteBDisposition.NOT_VISIBLE_UNRESOLVED:
            if (
                row.provider_resolution is not ProviderResolution.MISSING_OR_INVALID
                or row.attachment_admission is not AttachmentAdmission.UNAVAILABLE
                or row.visible_authority is not VisibleAuthority.NONE
                or refs
                or row.target_unknown_ref is not None
                or row.reason_codes != ("ATTACHMENT_UNRESOLVED",)
            ):
                return False
        else:
            return False
    return True


def _structural_trace_valid(outcome: object) -> bool:
    artifact = getattr(outcome, "artifact", None)
    graph = getattr(outcome, "meaning_graph", None)
    status = getattr(getattr(outcome, "status", None), "value", "")
    if status not in {"GENERATED", "LIMITED"}:
        return False
    if (
        type(artifact) is not GenerationArtifactBundle
        or type(graph) is not GroundedMeaningGraph
        or type(artifact.plan) is not ExperiencePlan
        or type(artifact.trace) is not tuple
        or any(type(row) is not VisibleUnitTrace for row in artifact.trace)
        or type(artifact.visible_unknowns) is not tuple
        or any(
            type(row) is not VisibleUnknownUnit for row in artifact.visible_unknowns
        )
        or getattr(outcome, "terminal_state", "")
        != CMEE_TERMINAL_GENERATED_DISABLED
        or getattr(outcome, "automatic_progression", True)
    ):
        return False
    expected_lineage = (
        graph.source_envelope_id,
        graph.source_version,
        graph.obligation_version,
        graph.owner_universe_digest,
    )
    if (
        type(artifact.observation) is not str
        or not artifact.observation
        or type(artifact.reception) is not str
        or not artifact.reception
        or type(artifact.artifact_id) is not str
        or re.fullmatch(r"artifact-[0-9a-f]{24}", artifact.artifact_id) is None
        or artifact.realizer_contract_ids != REALIZER_CONTRACT_IDS
        or artifact.trust_policy_ids != TRUST_POLICY_IDS
        or (
            artifact.plan.source_envelope_id,
            artifact.plan.source_version,
            artifact.plan.obligation_version,
            artifact.plan.owner_universe_digest,
        )
        != expected_lineage
        or any(
            (
                row.source_envelope_id,
                row.source_version,
                row.obligation_version,
                row.owner_universe_digest,
            )
            != expected_lineage
            for row in artifact.trace
        )
    ):
        return False
    owner_ids = tuple(row.owner_id for row in graph.owner_dispositions)
    if owner_ids != graph.required_owner_refs + graph.active_optional_owner_refs:
        return False
    if len(owner_ids) != len(set(owner_ids)):
        return False
    roles = tuple(row.role for row in artifact.trace)
    observation_count = roles.count("OBSERVATION")
    unknown_traces = tuple(row for row in artifact.trace if row.role == "UNKNOWN")
    reception_traces = tuple(
        row for row in artifact.trace if row.role == "RECEPTION"
    )
    visible_unknowns = tuple(getattr(artifact, "visible_unknowns", ()))
    expected_status = "LIMITED" if unknown_traces else "GENERATED"
    if (
        status != expected_status
        or not 1 <= observation_count <= 5
        or not 0 <= len(unknown_traces) <= 1
        or not 1 <= len(reception_traces) <= 4
        or roles
        != (
            *("OBSERVATION" for _ in range(observation_count)),
            *("UNKNOWN" for _ in range(len(unknown_traces))),
            *("RECEPTION" for _ in range(len(reception_traces))),
        )
    ):
        return False
    visible_unit_ids = tuple(row.visible_unit_id for row in artifact.trace)
    source_sentence_ids = tuple(row.source_sentence_id for row in artifact.trace)
    if (
        visible_unit_ids != tuple(
            f"visible:{index}" for index in range(1, len(artifact.trace) + 1)
        )
        or len(visible_unit_ids) != len(set(visible_unit_ids))
        or len(source_sentence_ids) != len(set(source_sentence_ids))
    ):
        return False
    expected_source_sentence_ids = (
        *(f"cmee:observation:{index}" for index in range(1, observation_count + 1)),
        *(f"cmee:unknown:{index}" for index in range(1, len(unknown_traces) + 1)),
        *(f"cmee:reception:{index}" for index in range(1, len(reception_traces) + 1)),
    )
    if source_sentence_ids != expected_source_sentence_ids:
        return False
    if len(visible_unknowns) != len(unknown_traces):
        return False
    if (
        tuple(
            owner_id
            for trace in unknown_traces
            for owner_id in trace.constrained_by_owner_ids
        )
        != artifact.plan.visible_unknown_owner_ids
        or not set(artifact.plan.required_unknown_owner_ids).issubset(
            artifact.plan.visible_unknown_owner_ids
        )
    ):
        return False
    if any(
        unknown_trace.visible_unit_id != visible_unknown.unknown_unit_id
        or unknown_trace.source_sentence_id != visible_unknown.source_sentence_id
        or unknown_trace.source_envelope_id != visible_unknown.source_envelope_id
        or unknown_trace.source_version != visible_unknown.source_version
        or unknown_trace.obligation_version != visible_unknown.obligation_version
        or unknown_trace.owner_universe_digest
        != visible_unknown.owner_universe_digest
        or unknown_trace.duty_id != visible_unknown.duty_id
        or unknown_trace.constrained_by_owner_ids != visible_unknown.owner_ids
        or unknown_trace.evidence_ids != visible_unknown.evidence_ids
        for unknown_trace, visible_unknown in zip(
            unknown_traces, visible_unknowns, strict=True
        )
    ):
        return False
    if not all(
        _valid_ref_tuple(row.evidence_ids)
        and _valid_ref_tuple(row.meaning_node_ids, allow_empty=True)
        and _valid_ref_tuple(row.meaning_edge_ids, allow_empty=True)
        and _valid_ref_tuple(row.constrained_by_owner_ids, allow_empty=True)
        for row in artifact.trace
    ):
        return False
    nodes = {row.node_id: row for row in graph.nodes}
    edges = {row.edge_id: row for row in graph.edges}
    disposition = {row.owner_id: row for row in graph.owner_dispositions}
    if not _route_b_dispositions_valid(graph):
        return False
    disposition_evidence_ids = {
        evidence_id
        for row in graph.owner_dispositions
        for evidence_id in row.evidence_ids
    }
    positive_dispositions = {
        RouteBDisposition.SOURCE_EXPLICIT_VISIBLE,
        RouteBDisposition.SUPPLEMENTAL_USER_VISIBLE,
    }
    for row in graph.owner_dispositions:
        refs = tuple(row.visible_claim_refs)
        if (
            (row.disposition in positive_dispositions and not refs)
            or len(refs) != len(set(refs))
            or any(
                (
                    ref not in nodes
                    or nodes[ref].owner_id != row.owner_id
                    or (
                        row.disposition in positive_dispositions
                        and nodes[ref].epistemic_state
                        is not EpistemicState.SOURCE_EXPLICIT
                    )
                )
                and (
                    ref not in edges
                    or edges[ref].owner_id != row.owner_id
                    or (
                        row.disposition in positive_dispositions
                        and edges[ref].epistemic_state
                        is not EpistemicState.SOURCE_EXPLICIT
                    )
                )
                for ref in refs
            )
        ):
            return False
    expected_visible_owner_ids = tuple(
        row.owner_id
        for row in graph.owner_dispositions
        if row.disposition in positive_dispositions
    )
    expected_unresolved_owner_ids = tuple(
        row.owner_id
        for row in graph.owner_dispositions
        if row.disposition not in positive_dispositions
    )
    if (
        artifact.plan.visible_owner_ids != expected_visible_owner_ids
        or artifact.plan.unresolved_owner_ids != expected_unresolved_owner_ids
    ):
        return False
    for unknown in unknown_traces:
        constrained_evidence_ids = {
            evidence_id
            for owner_id in unknown.constrained_by_owner_ids
            if owner_id in disposition
            for evidence_id in disposition[owner_id].evidence_ids
        }
        allowed_unknown_evidence_owner_ids = set(
            unknown.constrained_by_owner_ids
        ) | set(artifact.plan.required_observation_owner_ids)
        allowed_unknown_evidence_ids = {
            evidence_id
            for owner_id in allowed_unknown_evidence_owner_ids
            if owner_id in disposition
            for evidence_id in disposition[owner_id].evidence_ids
        }
        if (
            unknown.duty_id != "PRESERVE_EVIDENCE_BOUND_UNKNOWN"
            or unknown.operation != "EVIDENCE_BOUND_UNKNOWN_PRESERVATION"
            or unknown.meaning_node_ids
            or unknown.meaning_edge_ids
            or not unknown.constrained_by_owner_ids
            or unknown.emlis_stage1_extension is not None
            or any(
                owner_id not in disposition
                for owner_id in unknown.constrained_by_owner_ids
            )
            or any(
                disposition[owner_id].disposition
                is not RouteBDisposition.UNKNOWN_PRESERVED_LIMITED
                and (
                    disposition[owner_id].owner_class is not OwnerClass.REQUIRED
                    or disposition[owner_id].disposition in positive_dispositions
                )
                for owner_id in unknown.constrained_by_owner_ids
            )
            or not constrained_evidence_ids.issubset(unknown.evidence_ids)
            or not set(unknown.evidence_ids).issubset(
                allowed_unknown_evidence_ids & disposition_evidence_ids
            )
        ):
            return False
    trace_position = {
        row.visible_unit_id: index for index, row in enumerate(artifact.trace)
    }
    observation_trace_ids = {
        row.visible_unit_id for row in artifact.trace if row.role == "OBSERVATION"
    }
    observation_contributions_by_trace: dict[str, tuple[str, ...]] = {}
    positive_variants: set[str] = set()
    observation_contribution_refs: list[str] = []
    reception_claim_refs: list[str] = []
    for trace in artifact.trace:
        extension = trace.emlis_stage1_extension
        semantic_evidence_ids: set[str] = set()
        if trace.role in {"OBSERVATION", "RECEPTION"}:
            if (
                type(extension) is not EmlisStage1PositiveTraceExtension
                or not (trace.meaning_node_ids or trace.meaning_edge_ids)
                or trace.constrained_by_owner_ids
            ):
                return False
            if (
                extension.schema_version
                != CMEE_STAGE1_TRACE_EXTENSION_SCHEMA_VERSION
                or type(extension.owner_ref) is not str
                or extension.owner_ref
                != "owner:emlis@cocolon.cmee.v1a.emlis_stage1_response.v1"
                or type(extension.user_fact_effect) is not int
                or extension.user_fact_effect != 0
                or type(extension.composition_variant_id) is not str
                or not extension.composition_variant_id
                or not _valid_ref_tuple(extension.contribution_refs, allow_empty=True)
                or not _valid_ref_tuple(extension.basis_trace_refs, allow_empty=True)
                or not _valid_ref_tuple(
                    extension.interpretation_candidate_refs, allow_empty=True
                )
                or not _valid_ref_tuple(
                    extension.basis_observation_contribution_refs,
                    allow_empty=True,
                )
                or not _valid_ref_tuple(extension.value_principle_refs, allow_empty=True)
            ):
                return False
            positive_variants.add(extension.composition_variant_id)
            if trace.role == "OBSERVATION":
                if (
                    trace.duty_id != artifact.plan.observation_duty_id
                    or trace.operation != "SOURCE_EXPLICIT_GROUNDED_OBSERVATION"
                    or extension.claim_domain
                    is not EmlisTraceClaimDomain.INTERPRETIVE_OBSERVATION
                    or len(extension.contribution_refs) != 1
                    or not extension.interpretation_candidate_refs
                    or extension.subjective_claim_ref is not None
                    or extension.basis_trace_refs
                    or extension.basis_observation_contribution_refs
                    or extension.value_principle_refs
                    or extension.speaker_owner is not None
                ):
                    return False
                observation_contributions_by_trace[trace.visible_unit_id] = (
                    extension.contribution_refs
                )
                observation_contribution_refs.extend(extension.contribution_refs)
            elif (
                trace.duty_id != artifact.plan.reception_duty_id
                or trace.operation != "BOUND_HUMAN_RECEPTION"
                or extension.claim_domain
                is not EmlisTraceClaimDomain.SUBJECTIVE_RESPONSE
                or extension.contribution_refs
                or extension.interpretation_candidate_refs
                or type(extension.subjective_claim_ref) is not str
                or not extension.subjective_claim_ref
                or not extension.basis_observation_contribution_refs
                or not extension.basis_trace_refs
                or extension.speaker_owner != "EMLIS"
                or any(
                    basis_ref not in observation_trace_ids
                    or trace_position[basis_ref] >= trace_position[trace.visible_unit_id]
                    for basis_ref in extension.basis_trace_refs
                )
            ):
                return False
            else:
                reception_claim_refs.append(extension.subjective_claim_ref)
                reachable_basis_contributions = tuple(
                    contribution_ref
                    for basis_ref in extension.basis_trace_refs
                    for contribution_ref in observation_contributions_by_trace.get(
                        basis_ref, ()
                    )
                )
                if (
                    extension.basis_observation_contribution_refs
                    != reachable_basis_contributions
                ):
                    return False
        for node_id in trace.meaning_node_ids:
            node = nodes.get(node_id)
            owner_disposition = disposition.get(node.owner_id) if node else None
            if (
                node is None
                or owner_disposition is None
                or owner_disposition.disposition not in positive_dispositions
                or node.owner_id not in set(artifact.plan.visible_owner_ids)
                or node.node_id not in set(owner_disposition.visible_claim_refs)
                or node.epistemic_state is not EpistemicState.SOURCE_EXPLICIT
                or node.grounding_kind not in {"explicit", "user_stated_relation"}
                or not node.evidence_ids
            ):
                return False
            semantic_evidence_ids.update(node.evidence_ids)
        for edge_id in trace.meaning_edge_ids:
            edge = edges.get(edge_id)
            owner_disposition = disposition.get(edge.owner_id) if edge else None
            if (
                edge is None
                or owner_disposition is None
                or owner_disposition.disposition not in positive_dispositions
                or edge.owner_id not in set(artifact.plan.visible_owner_ids)
                or edge.edge_id not in set(owner_disposition.visible_claim_refs)
                or edge.epistemic_state is not EpistemicState.SOURCE_EXPLICIT
                or edge.grounding_kind != "user_stated_relation"
                or not edge.evidence_ids
            ):
                return False
            semantic_evidence_ids.update(edge.evidence_ids)
            if edge.relation in _STRICT_DIRECTIONAL_TRACE_RELATIONS:
                try:
                    source_position = trace.meaning_node_ids.index(
                        edge.source_node_id
                    )
                    target_position = trace.meaning_node_ids.index(
                        edge.target_node_id
                    )
                except ValueError:
                    return False
                if source_position >= target_position:
                    return False
        if trace.role in {"OBSERVATION", "RECEPTION"} and set(
            trace.evidence_ids
        ) != semantic_evidence_ids:
            return False
    if len(positive_variants) != 1:
        return False
    if (
        len(observation_contribution_refs)
        != len(set(observation_contribution_refs))
        or len(reception_claim_refs) != len(set(reception_claim_refs))
    ):
        return False
    guarded_ids = tuple(
        row.source_sentence_id
        for row in artifact.trace
        if row.role == "OBSERVATION"
    )
    proof = artifact.common_guard_proof
    if (
        type(proof) is not CommonGuardProof
        or type(proof.guarded_observation_units) is not tuple
        or any(
            type(row) is not tuple
            or len(row) != 2
            or any(type(value) is not str or not value for value in row)
            for row in proof.guarded_observation_units
        )
    ):
        return False
    if tuple(
        row[0] for row in proof.guarded_observation_units
    ) != guarded_ids:
        return False
    if "\r" in artifact.observation or "\r" in artifact.reception:
        return False
    observation_lines = tuple(artifact.observation.split("\n"))
    reception_lines = tuple(artifact.reception.split("\n"))
    if (
        any(not line for line in (*observation_lines, *reception_lines))
        or artifact.observation != "\n".join(observation_lines)
        or artifact.reception != "\n".join(reception_lines)
        or len(observation_lines) != observation_count
        or len(reception_lines) != len(reception_traces)
    ):
        return False
    visible_text = (
        *observation_lines,
        *(row.text for row in visible_unknowns),
        *reception_lines,
    )
    if any(
        trace.text_sha256 != _sha256_text(text)
        for trace, text in zip(artifact.trace, visible_text, strict=True)
    ):
        return False
    expected_guarded_observation_units = tuple(
        (source_sentence_id, _sha256_text(text))
        for source_sentence_id, text in zip(
            guarded_ids,
            observation_lines,
            strict=True,
        )
    )
    if (
        proof.schema_version != CMEE_COMMON_GUARD_PROOF_VERSION
        or type(proof.proof_id) is not str
        or not proof.proof_id
        or proof.source_envelope_id != graph.source_envelope_id
        or proof.graph_id != graph.graph_id
        or proof.plan_id != artifact.plan.plan_id
        or any(
            row.artifact_common_guard_proof_ref != proof.proof_id
            for row in artifact.trace
        )
        or type(proof.guarded_observation_units) is not tuple
        or proof.guarded_observation_units != expected_guarded_observation_units
        or type(proof.guard_results) is not tuple
        or len(proof.guard_results) != len(EXPECTED_COMMON_GUARD_IDS)
        or any(
            type(row) is not CommonGuardResultProof
            or row.guard_id != expected_guard_id
            or type(row.passed) is not bool
            or row.passed is not True
            for expected_guard_id, row in zip(
                EXPECTED_COMMON_GUARD_IDS,
                proof.guard_results,
                strict=True,
            )
        )
        or proof.stabilization_report_name
        != COMMON_GUARD_STABILIZATION_REPORT_NAME
        or proof.stabilization_phase != COMMON_GUARD_STABILIZATION_PHASE
        or proof.stabilization_core_id != COMMON_GUARD_STABILIZATION_CORE_ID
        or type(proof.stabilization_passed) is not bool
        or proof.stabilization_passed is not True
        or type(proof.common_shapes_ready) is not bool
        or proof.common_shapes_ready is not True
        or type(proof.stabilization_guard_names) is not tuple
        or proof.stabilization_guard_names != EXPECTED_COMMON_GUARD_IDS
        or type(proof.issue_codes) is not tuple
        or proof.issue_codes != ()
    ):
        return False
    if proof.proof_id != _common_guard_proof_id(
        source_envelope_id=proof.source_envelope_id,
        graph_id=proof.graph_id,
        plan_id=proof.plan_id,
        guarded_observation_units=proof.guarded_observation_units,
        guard_results=proof.guard_results,
        stabilization_report_name=proof.stabilization_report_name,
        stabilization_phase=proof.stabilization_phase,
        stabilization_core_id=proof.stabilization_core_id,
        stabilization_passed=proof.stabilization_passed,
        common_shapes_ready=proof.common_shapes_ready,
        stabilization_guard_names=proof.stabilization_guard_names,
        issue_codes=proof.issue_codes,
    ):
        return False
    return True


def run(
    *,
    runtime_repo_head: str | None = None,
    design_repo_head: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if (runtime_repo_head is None) != (design_repo_head is None):
        raise ValueError("private packet repo head binding incomplete")
    engine = MeaningExperienceEngine()
    mutation_registry = _body_free_mutation_registry()
    private_cases: list[dict[str, Any]] = []
    body_free_cases: list[dict[str, Any]] = []
    for case_id, memo, category, emotion, strength in EXACT8:
        raw = _raw(case_id, memo, category, emotion, strength)
        outcome = engine.generate(
            GenerationRequest(
                request_id=f"req-{case_id}",
                current_input_bundle=build_emlis_current_input_bundle(raw),
                expected_source_record_id=str(raw["id"]),
            )
        )
        structural_valid = _structural_trace_valid(outcome)
        private_cases.append(
            {
                "case_id": case_id,
                "synthetic_input_private": raw,
                "candidate_private": outcome.artifact.text if outcome.artifact else "",
                "structural_trace_valid": structural_valid,
                "review_axes": list(PRODUCT_READ_AXES),
                "human_product_read": {
                    "axis_results": None,
                    "common_severity": None,
                    "accepted": None,
                },
            }
        )
        body_free_cases.append(
            {
                "case_id": case_id,
                "status": outcome.status.value,
                "reason_codes": list(outcome.reason_codes),
                "structural_trace_valid": structural_valid,
                "artifact_present": outcome.artifact is not None,
                "visible_unit_trace_count": len(outcome.artifact.trace) if outcome.artifact else 0,
            }
        )

    artifact_count = sum(item["artifact_present"] for item in body_free_cases)
    structural_count = sum(item["structural_trace_valid"] for item in body_free_cases)
    candidate_state = (
        "GENERATED_FOR_PRODUCT_READ_DISABLED"
        if structural_count == len(EXACT8)
        else "EXACT8_GENERATION_INCOMPLETE_DISABLED"
    )
    full = {
        "packet_id": STAGE1_KAREN_DERIVED_AFTER_PACKET_ID,
        "private_slot_id": STAGE1_KAREN_DERIVED_AFTER_PRIVATE_SLOT_ID,
        "private_body_full": True,
        "private_packet_binding": (
            _private_packet_binding(
                runtime_repo_head=runtime_repo_head,
                design_repo_head=design_repo_head,
            )
            if runtime_repo_head is not None and design_repo_head is not None
            else {"binding_state": "UNMATERIALIZED"}
        ),
        "candidate_state": candidate_state,
        "finite_mutation_set_body_free": mutation_registry,
        "cases": private_cases,
        "candidate_evaluation_not_yet_accepted": {
            "structural_trace_valid_is_observation_only": False,
            "human_axes_required": list(PRODUCT_READ_AXES),
            "common_blocker_or_major_required": 0,
            "set_level_reread_required": True,
        },
    }
    body_free: dict[str, Any] = {
        "packet_id": full["packet_id"],
        "case_count": len(body_free_cases),
        "generated_count": sum(item["status"] == "GENERATED" for item in body_free_cases),
        "limited_count": sum(item["status"] == "LIMITED" for item in body_free_cases),
        "material_unknown_case_count": sum(
            item["status"] == "LIMITED" for item in body_free_cases
        ),
        "structural_trace_valid_count": sum(item["structural_trace_valid"] for item in body_free_cases),
        "artifact_count": artifact_count,
        "observation_plus_bound_reception_trace_count": sum(
            item["structural_trace_valid"] for item in body_free_cases
        ),
        "cases": body_free_cases,
        "candidate_state": candidate_state,
        "finite_mutation_set_body_free": mutation_registry,
        "implementation_state": "DRAFT_WIP_DISABLED",
        "route_b_contract_complete": False,
        "candidate_ready": False,
        "product_read_eligible": False,
        "exact8_acceptance_complete": False,
        "product_read_evaluated": False,
        "private_text_published": False,
        "p0_credit": 0,
        "l3i_credit": 0,
        "full_i1_credit": 0,
        "cycle001_credit": 0,
        "production_effect": 0,
        "automatic_progression": False,
    }
    return body_free, full


def _paths_overlap(left: Path, right: Path) -> bool:
    return left == right or left in right.parents or right in left.parents


def _private_output_target(
    parser: argparse.ArgumentParser,
    requested: Path,
) -> Path:
    """Resolve a private target that is disjoint from this checkout."""

    root = PRIVATE_OUTPUT_ROOT.resolve()
    checkout = CHECKOUT_ROOT.resolve()
    target = requested.resolve()
    if _paths_overlap(root, checkout):
        parser.error("private output root is not isolated from the checkout")
    if (
        target == root
        or root not in target.parents
        or _paths_overlap(target, checkout)
    ):
        parser.error("private output target is not isolated")
    return target


def _private_input_target(
    parser: argparse.ArgumentParser,
    requested: Path,
) -> Path:
    """Resolve one regular, owner-only input below the isolated private root."""

    root = PRIVATE_OUTPUT_ROOT.resolve()
    checkout = CHECKOUT_ROOT.resolve()
    if requested.is_symlink():
        parser.error("private input target is not isolated")
    try:
        target = requested.resolve(strict=True)
        target_stat = target.stat(follow_symlinks=False)
    except OSError:
        parser.error("private input target is unavailable")
    if (
        _paths_overlap(root, checkout)
        or target == root
        or root not in target.parents
        or _paths_overlap(target, checkout)
        or not stat.S_ISREG(target_stat.st_mode)
        or stat.S_IMODE(target_stat.st_mode) != 0o600
        or not 0 < target_stat.st_size <= 64 * 1024
    ):
        parser.error("private input target is not isolated")
    return target


def _require_new_private_output_targets(
    parser: argparse.ArgumentParser,
    targets: tuple[Path, ...],
) -> None:
    """Reject an already materialized early output before any body is read."""

    for target in targets:
        try:
            target.lstat()
        except FileNotFoundError:
            continue
        except OSError:
            parser.error("early actual private output target is unavailable")
        parser.error("early actual private output target already exists")


def _read_private_json(target: Path) -> object:
    no_follow = getattr(os, "O_NOFOLLOW", 0)
    file_fd = os.open(target, os.O_RDONLY | no_follow)
    try:
        file_stat = os.fstat(file_fd)
        if (
            not stat.S_ISREG(file_stat.st_mode)
            or stat.S_IMODE(file_stat.st_mode) != 0o600
            or not 0 < file_stat.st_size <= 64 * 1024
        ):
            raise ValueError("withheld early private input invalid")
        with os.fdopen(file_fd, "r", encoding="utf-8") as handle:
            file_fd = -1
            return json.load(handle)
    finally:
        if file_fd >= 0:
            os.close(file_fd)


def _write_private_json_exclusive(
    parser: argparse.ArgumentParser,
    target: Path,
    payload: Mapping[str, Any],
) -> None:
    root = PRIVATE_OUTPUT_ROOT.resolve()
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    if _paths_overlap(root, CHECKOUT_ROOT.resolve()):
        parser.error("private output target is not isolated")
    os.chmod(root, 0o700)
    no_follow = getattr(os, "O_NOFOLLOW", 0)
    directory = getattr(os, "O_DIRECTORY", 0)
    relative_parts = target.relative_to(root).parts
    directory_fd = os.open(root, os.O_RDONLY | directory | no_follow)
    try:
        for part in relative_parts[:-1]:
            try:
                os.mkdir(part, mode=0o700, dir_fd=directory_fd)
            except FileExistsError:
                pass
            next_directory_fd = os.open(
                part,
                os.O_RDONLY | directory | no_follow,
                dir_fd=directory_fd,
            )
            os.close(directory_fd)
            directory_fd = next_directory_fd
            os.fchmod(directory_fd, 0o700)
        output_fd = os.open(
            relative_parts[-1],
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | no_follow,
            0o600,
            dir_fd=directory_fd,
        )
        with os.fdopen(output_fd, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    finally:
        os.close(directory_fd)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--body-full-output", type=Path)
    parser.add_argument("--runtime-repo-head")
    parser.add_argument("--design-repo-head")
    parser.add_argument("--early-actual", action="store_true")
    parser.add_argument("--withheld-input", type=Path)
    parser.add_argument("--known-visible-output", type=Path)
    args = parser.parse_args()
    if args.early_actual:
        if (
            args.withheld_input is None
            or args.known_visible_output is None
            or args.body_full_output is None
        ):
            parser.error("early actual requires isolated input and exact2 output")
        input_target = _private_input_target(parser, args.withheld_input)
        known_output_target = _private_output_target(
            parser,
            args.known_visible_output,
        )
        private_output_target = _private_output_target(
            parser,
            args.body_full_output,
        )
        if len({input_target, known_output_target, private_output_target}) != 3:
            parser.error("early actual input and exact2 output must be distinct")
        _require_new_private_output_targets(
            parser,
            (known_output_target, private_output_target),
        )
        if (
            re.fullmatch(r"[0-9a-f]{40}", str(args.runtime_repo_head or ""))
            is None
            or re.fullmatch(r"[0-9a-f]{40}", str(args.design_repo_head or ""))
            is None
        ):
            parser.error("early private packet repo head binding invalid")
        try:
            withheld_payload = _read_private_json(input_target)
            body_free_packet, known_visible, private_packet = run_early_actual(
                withheld_private_payload=withheld_payload,
                runtime_repo_head=args.runtime_repo_head,
                design_repo_head=args.design_repo_head,
            )
            _write_private_json_exclusive(
                parser,
                known_output_target,
                known_visible,
            )
            _write_private_json_exclusive(
                parser,
                private_output_target,
                private_packet,
            )
        except (OSError, ValueError, RuntimeError, json.JSONDecodeError):
            parser.error("early actual private materialization failed")
        print(json.dumps(body_free_packet, ensure_ascii=False, sort_keys=True))
        known_result = body_free_packet["known_exact4_body_free"][
            "machine_invariant_result"
        ]
        withheld_result = body_free_packet["withheld_exact4_body_free"][
            "machine_invariant_result"
        ]
        return 0 if known_result == withheld_result == "CLEAR" else 1
    if args.withheld_input is not None or args.known_visible_output is not None:
        parser.error("early-only input or output requires early actual mode")
    target: Path | None = None
    if args.body_full_output is not None:
        target = _private_output_target(parser, args.body_full_output)
        if (
            re.fullmatch(r"[0-9a-f]{40}", str(args.runtime_repo_head or ""))
            is None
            or re.fullmatch(r"[0-9a-f]{40}", str(args.design_repo_head or ""))
            is None
        ):
            parser.error("private packet repo head binding invalid")
    body_free, full = run(
        runtime_repo_head=args.runtime_repo_head if target is not None else None,
        design_repo_head=args.design_repo_head if target is not None else None,
    )
    if target is not None:
        root = PRIVATE_OUTPUT_ROOT.resolve()
        root.mkdir(mode=0o700, parents=True, exist_ok=True)
        if _paths_overlap(root, CHECKOUT_ROOT.resolve()):
            parser.error("private output target is not isolated")
        os.chmod(root, 0o700)
        no_follow = getattr(os, "O_NOFOLLOW", 0)
        directory = getattr(os, "O_DIRECTORY", 0)
        relative_parts = target.relative_to(root).parts
        directory_fd = os.open(root, os.O_RDONLY | directory | no_follow)
        try:
            for part in relative_parts[:-1]:
                try:
                    os.mkdir(part, mode=0o700, dir_fd=directory_fd)
                except FileExistsError:
                    pass
                next_directory_fd = os.open(
                    part,
                    os.O_RDONLY | directory | no_follow,
                    dir_fd=directory_fd,
                )
                os.close(directory_fd)
                directory_fd = next_directory_fd
                os.fchmod(directory_fd, 0o700)
            output_fd = os.open(
                relative_parts[-1],
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | no_follow,
                0o600,
                dir_fd=directory_fd,
            )
            with os.fdopen(output_fd, "w", encoding="utf-8") as handle:
                handle.write(json.dumps(full, ensure_ascii=False, indent=2) + "\n")
        finally:
            os.close(directory_fd)
    print(json.dumps(body_free, ensure_ascii=False, sort_keys=True))
    # Candidate generation gaps are reported, not hidden by fixture tuning.
    # A complete packet is not the same thing as a successful candidate run.
    return 0 if body_free["structural_trace_valid_count"] == len(EXACT8) else 1


if __name__ == "__main__":
    raise SystemExit(main())
