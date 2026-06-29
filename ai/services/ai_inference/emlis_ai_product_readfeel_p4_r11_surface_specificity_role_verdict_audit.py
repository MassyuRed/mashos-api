# -*- coding: utf-8 -*-
"""P4-R11 R11-6/R11-7 body-free surface role and verdict audit helpers.

This module intentionally stays outside the Emlis runtime path.  It may receive
local-only visible surface probes from tests, but it never returns, dumps, or
persists those bodies.  Returned data is limited to role ids, signature ids,
verdict ids, repair layer ids, and boundary flags.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Final, Mapping, Sequence

import emlis_ai_product_readfeel_p4_r11_residual_family_surface_audit as base

PRODUCT_READFEEL_P4_R11_SURFACE_SPECIFICITY_ROLE_AUDIT_VERSION_20260624: Final[str] = (
    "cocolon.emlis.product_readfeel.p4_r11.surface_specificity_role_audit.v1"
)
PRODUCT_READFEEL_P4_R11_VERDICT_REPAIR_CLASSIFICATION_VERSION_20260624: Final[str] = (
    "cocolon.emlis.product_readfeel.p4_r11.verdict_repair_candidate_classification.v1"
)

P4_R11_R6_IMPLEMENTED_STEPS_20260624: Final[tuple[str, ...]] = (
    base.P4_R11_R6_STEP_REF_20260624,
)
P4_R11_R7_IMPLEMENTED_STEPS_20260624: Final[tuple[str, ...]] = (
    base.P4_R11_R6_STEP_REF_20260624,
    base.P4_R11_R7_STEP_REF_20260624,
)

P4_R11_VERDICT_PASS_20260624: Final[str] = "PASS"
P4_R11_VERDICT_YELLOW_20260624: Final[str] = "YELLOW"
P4_R11_VERDICT_REPAIR_REQUIRED_20260624: Final[str] = "REPAIR_REQUIRED"
P4_R11_VERDICT_RED_20260624: Final[str] = "RED"

P4_R11_NEXT_ACTION_NO_ACTION_R54_RETURN_CANDIDATE_20260624: Final[str] = (
    "no_action_r54_return_candidate"
)
P4_R11_NEXT_ACTION_P4_TARGETED_REPAIR_REQUIRED_20260624: Final[str] = (
    "p4_targeted_repair_required"
)
P4_R11_NEXT_ACTION_HUMAN_READFEEL_REVIEW_NOTE_ONLY_20260624: Final[str] = (
    "human_readfeel_review_note_only"
)
P4_R11_NEXT_ACTION_SEPARATE_CONTRACT_OR_SAFETY_LEDGER_REQUIRED_20260624: Final[str] = (
    "separate_contract_or_safety_ledger_required"
)

_R6_STATUS_AUDITED: Final[str] = "audited_r11_6"
_R6_STATUS_UNAVAILABLE: Final[str] = "surface_probe_unavailable_r11_6"
_R7_STATUS_CLASSIFIED: Final[str] = "classified_r11_7"

_GENERIC_SIGNATURE_IDS: Final[tuple[str, ...]] = (
    "category_emotion_action_generic",
    "next_handling_generic",
    "positive_generic_reception",
    "generic_praise_only",
    "relationship_generic_comfort",
    "relationship_target_judgement",
    "long_arc_summary_crush",
    "structure_question_comfort_escape",
    "question_only_surface",
    "self_denial_identity_echo",
    "self_denial_over_praise",
    "mirror_only_surface",
    "repeated_closing_signature",
    "repeated_section_shape_signature",
    "family_temperature_flattened",
)
_TEMPERATURE_MISMATCH_IDS: Final[tuple[str, ...]] = (
    "positive_temperature_cooling",
    "positive_temperature_cooled",
    "relationship_temperature_flattened",
    "observation_ratio_low",
    "family_temperature_flattened",
)
_SEVERE_RED_SIGNATURE_IDS: Final[tuple[str, ...]] = (
    "relationship_target_judgement",
    "self_denial_identity_echo",
    "question_only_surface",
)


_ALL_SURFACE_ROLE_IDS: Final[tuple[str, ...]] = (
    "current_change_nucleus_visible",
    "future_direction_visible",
    "recovered_energy_or_transition_visible",
    "self_possibility_without_prediction_visible",
    "value_preservation_without_advice_visible",
    "positive_event_or_small_change_visible",
    "positive_temperature_kept",
    "observation_not_overweighted",
    "reception_warmth_present",
    "no_generic_praise_only",
    "relationship_or_gratitude_nucleus_visible",
    "user_side_wish_or_reaction_visible",
    "no_other_person_intent_claim",
    "no_relationship_permanence_claim",
    "recovery_or_thanks_temperature_kept",
    "multiple_current_nuclei_visible",
    "relation_between_nuclei_visible",
    "not_summary_only",
    "observation_section_has_structure",
    "reception_does_not_crush_complexity",
    "question_context_visible",
    "state_answer_attempt_visible",
    "comfort_not_primary",
    "observation_ratio_high_enough",
    "no_question_escape",
    "self_denial_not_accepted_as_fact",
    "load_or_pain_behind_denial_visible",
    "no_personality_claim",
    "no_absolute_personality_praise",
    "safety_boundary_if_needed",
)


def _clean(value: Any) -> str:
    if value is None or isinstance(value, (Mapping, list, tuple, set)):
        return ""
    return str(value).strip()


def _safe_identifier(value: Any, *, default: str = "") -> str:
    return base._safe_identifier(value, default=default)  # type: ignore[attr-defined]


def _dedupe(values: Any) -> list[str]:
    return base._dedupe(values)  # type: ignore[attr-defined]


def _boundary_flags() -> dict[str, Any]:
    return base._all_boundary_flags()  # type: ignore[attr-defined]


def _counter_dict(counter: Counter[str]) -> dict[str, int]:
    return {key: int(counter[key]) for key in sorted(counter)}


def _probe_text(value: Any) -> str:
    """Read a local-only probe body for this process without returning it."""

    if value is None:
        return ""
    if isinstance(value, Mapping):
        for key in (
            "local_visible_surface",
            "local_surface_probe",
            "local_probe_surface",
            "local_comment_text",
            "surface_probe",
        ):
            text = _clean(value.get(key))
            if text:
                return text
        return ""
    return _clean(value)


def _local_surface_probe_map(
    probes: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None,
) -> dict[str, str]:
    if probes is None:
        return {}
    if isinstance(probes, Mapping):
        return {
            _safe_identifier(case_ref, default=""): _probe_text(probe)
            for case_ref, probe in probes.items()
            if _safe_identifier(case_ref, default="") and _probe_text(probe)
        }

    result: dict[str, str] = {}
    for probe in probes:
        if not isinstance(probe, Mapping):
            continue
        case_ref_id = _safe_identifier(probe.get("case_ref_id"), default="")
        text = _probe_text(probe)
        if case_ref_id and text:
            result[case_ref_id] = text
    return result


def _contains_any(surface: str, markers: Sequence[str]) -> bool:
    return any(marker and marker in surface for marker in markers)


def _detect_roles(
    *,
    surface: str,
    residual_family_id: str,
    required_roles: Sequence[str],
) -> list[str]:
    role_candidates = tuple(required_roles) or _ALL_SURFACE_ROLE_IDS
    surface_tokens = set(surface.replace(",", " ").replace("。", " ").replace("、", " ").split())
    observed: list[str] = []
    for role in role_candidates:
        if role and (role in surface_tokens or role in surface):
            observed.append(role)

    # The normalizer also accepts body-like local probes that do not literally
    # contain the role id.  Only the derived role ids are returned.
    semantic_markers: dict[str, tuple[str, ...]] = {
        "current_change_nucleus_visible": ("変化", "変わ", "戻って", "やってみたい"),
        "future_direction_visible": ("future", "次", "これから", "やってみたい", "できるかも"),
        "recovered_energy_or_transition_visible": ("回復", "戻って", "力", "エネルギー", "transition"),
        "self_possibility_without_prediction_visible": ("できるかも", "可能性", "予言せず", "断定せず"),
        "value_preservation_without_advice_visible": ("価値", "大事", "助言にせず", "指示にせず"),
        "positive_event_or_small_change_visible": ("小さな変化", "よかった", "安心", "うれし", "嬉し"),
        "positive_temperature_kept": ("温か", "うれし", "安心", "喜び", "温度"),
        "observation_not_overweighted": ("重くしすぎ", "重く分析しすぎない", "軽く", "そのまま"),
        "reception_warmth_present": ("受け取", "温か", "一緒", "よかった"),
        "no_generic_praise_only": ("genericに褒めない", "generic_praise_onlyではない", "no_generic_praise_only"),
        "relationship_or_gratitude_nucleus_visible": ("感謝", "ありがとう", "関係", "支え", "grateful"),
        "user_side_wish_or_reaction_visible": ("願い", "返したい", "反応", "安心", "うれし"),
        "no_other_person_intent_claim": ("意図は決めず", "相手の意図を決めず", "no_other_person_intent_claim"),
        "no_relationship_permanence_claim": ("関係を断定せず", "永続を決めず", "no_relationship_permanence_claim"),
        "recovery_or_thanks_temperature_kept": ("回復", "感謝", "ありがとう", "温度"),
        "multiple_current_nuclei_visible": ("複数", "いくつか", "同時", "multiple"),
        "relation_between_nuclei_visible": ("関係", "つなが", "ぶつか", "同居"),
        "not_summary_only": ("要約だけにしない", "潰さず", "not_summary_only"),
        "observation_section_has_structure": ("構造", "層", "並んで", "section"),
        "reception_does_not_crush_complexity": ("複雑", "潰さず", "そのまま"),
        "question_context_visible": ("問い", "文脈", "迷い", "question"),
        "state_answer_attempt_visible": ("状態", "答え", "回答", "state_answer"),
        "comfort_not_primary": ("慰めだけにせず", "comfort_not_primary"),
        "observation_ratio_high_enough": ("観測", "比率", "observation_ratio_high_enough"),
        "no_question_escape": ("問い逃げしない", "no_question_escape"),
        "self_denial_not_accepted_as_fact": ("事実として扱わず", "否定を事実にせず", "self_denial_not_accepted_as_fact"),
        "load_or_pain_behind_denial_visible": ("苦しさ", "負荷", "痛み", "しんど"),
        "no_personality_claim": ("人格", "性格", "人格の話にせず", "no_personality_claim"),
        "no_absolute_personality_praise": ("過剰肯定せず", "絶対", "no_absolute_personality_praise"),
        "safety_boundary_if_needed": ("安全", "境界", "safety_boundary_if_needed"),
    }
    for role in role_candidates:
        if role in observed:
            continue
        if _contains_any(surface, semantic_markers.get(role, ())):
            observed.append(role)

    # If the probe is a deliberate role-id fixture and contains no generic
    # signature, all required role ids may be visible in that fixture.
    return _dedupe(observed)


def _detect_generic_signature_ids(surface: str) -> list[str]:
    detected: list[str] = []
    surface_tokens = set(surface.replace(",", " ").replace("。", " ").replace("、", " ").split())
    for signature_id in _GENERIC_SIGNATURE_IDS:
        if signature_id in surface_tokens:
            detected.append(signature_id)

    semantic_markers: dict[str, tuple[str, ...]] = {
        "category_emotion_action_generic": ("カテゴリ", "感情と行動", "分類", "category"),
        "next_handling_generic": ("次の扱い方", "前向きに考え", "扱い方を考え"),
        "positive_generic_reception": ("よかったですね", "前向きですね", "いいことですね"),
        "generic_praise_only": ("えらい", "すごいですね"),
        "relationship_generic_comfort": ("人間関係は大変", "関係は難しい", "大変ですね"),
        "relationship_target_judgement": ("relationship_target_judgement", "相手は悪い", "相手が悪い", "相手のせい"),
        "long_arc_summary_crush": ("long_arc_summary_crush", "まとめると", "いろいろありました"),
        "structure_question_comfort_escape": ("大丈夫です", "慰めて", "comfort_escape"),
        "question_only_surface": ("question_only_surface", "どうしたいですか", "どうすればいいですか"),
        "self_denial_identity_echo": ("self_denial_identity_echo", "ダメな人", "だめな人", "価値がない人"),
        "self_denial_over_praise": ("self_denial_over_praise", "絶対にすばらしい", "完全に大丈夫"),
        "mirror_only_surface": ("mirror_only_surface", "そのままですね"),
        "repeated_closing_signature": ("また教えて", "無理しないでください"),
        "repeated_section_shape_signature": ("まず", "次に", "最後に"),
        "family_temperature_flattened": ("family_temperature_flattened", "いつもの形"),
    }
    for signature_id, markers in semantic_markers.items():
        if signature_id not in detected and _contains_any(surface, markers):
            detected.append(signature_id)
    return _dedupe(detected)


def _detect_temperature_mismatch_ids(surface: str) -> list[str]:
    detected: list[str] = []
    for mismatch_id in _TEMPERATURE_MISMATCH_IDS:
        if mismatch_id in surface:
            detected.append(mismatch_id)
    if "温度を落と" in surface and "positive_temperature_cooled" not in detected:
        detected.append("positive_temperature_cooled")
    if "冷め" in surface and "positive_temperature_cooling" not in detected:
        detected.append("positive_temperature_cooling")
    if "比率が低" in surface and "observation_ratio_low" not in detected:
        detected.append("observation_ratio_low")
    return _dedupe(detected)


def normalize_local_surface_probe_to_p4_r11_observation_ids_20260624(
    *,
    local_visible_surface: str,
    residual_family_id: str,
    residual_focus_slice_ids: Sequence[str] | None = None,
    required_surface_role_ids: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Convert a local-only surface body into body-free ids.

    The input string is intentionally consumed only inside this function.  The
    returned mapping must not include the string, exact fragments, or detector
    snippets.
    """

    required_roles = _dedupe(required_surface_role_ids or [])
    observed_roles = _detect_roles(
        surface=local_visible_surface,
        residual_family_id=_clean(residual_family_id),
        required_roles=required_roles,
    )
    generic_signature_ids = _detect_generic_signature_ids(local_visible_surface)
    temperature_mismatch_ids = _detect_temperature_mismatch_ids(local_visible_surface)
    result = {
        "schema_version": PRODUCT_READFEEL_P4_R11_SURFACE_SPECIFICITY_ROLE_AUDIT_VERSION_20260624,
        "residual_family_id": _clean(residual_family_id),
        "residual_focus_slice_ids": _dedupe(residual_focus_slice_ids),
        "observed_surface_role_ids": observed_roles,
        "generic_surface_signature_ids": generic_signature_ids,
        "temperature_mismatch_ids": temperature_mismatch_ids,
        "question_escape_detected": "question_only_surface" in generic_signature_ids,
        "mirror_only_detected": "mirror_only_surface" in generic_signature_ids,
        "local_visible_surface_retained_here": False,
        "local_comment_text_retained_here": False,
        "detector_fragment_retained_here": False,
        "exact_sentence_match_required": False,
        **_boundary_flags(),
    }
    base.assert_product_readfeel_p4_r11_residual_surface_audit_meta_only_20260624(
        result,
        source="p4_r11.r6.surface_probe_normalized_ids",
    )
    return result


def _surface_specificity_audit_for_row(row: Mapping[str, Any], *, probe_text: str) -> dict[str, Any]:
    required_roles = _dedupe(row.get("required_surface_role_ids"))
    if not probe_text:
        return {
            "surface_specificity_role_audit_status": _R6_STATUS_UNAVAILABLE,
            "current_only_specificity_required": True,
            "specificity_met": False,
            "required_surface_role_ids": required_roles,
            "observed_surface_role_ids": [],
            "missing_surface_role_ids": [],
            "generic_surface_signature_ids": [],
            "temperature_mismatch_ids": [],
            "question_escape_detected": False,
            "mirror_only_detected": False,
            "local_visible_surface_retained_here": False,
            "local_comment_text_retained_here": False,
            "detector_fragment_retained_here": False,
            "exact_sentence_match_required": False,
        }

    normalized = normalize_local_surface_probe_to_p4_r11_observation_ids_20260624(
        local_visible_surface=probe_text,
        residual_family_id=_clean(row.get("residual_family_id")),
        residual_focus_slice_ids=_dedupe(row.get("residual_focus_slice_ids")),
        required_surface_role_ids=required_roles,
    )
    observed_roles = _dedupe(normalized.get("observed_surface_role_ids"))
    generic_signature_ids = _dedupe(normalized.get("generic_surface_signature_ids"))
    temperature_mismatch_ids = _dedupe(normalized.get("temperature_mismatch_ids"))
    missing_roles = [role for role in required_roles if role not in set(observed_roles)]
    specificity_met = not missing_roles and not generic_signature_ids and not temperature_mismatch_ids
    return {
        "surface_specificity_role_audit_status": _R6_STATUS_AUDITED,
        "current_only_specificity_required": True,
        "specificity_met": specificity_met,
        "required_surface_role_ids": required_roles,
        "observed_surface_role_ids": observed_roles,
        "missing_surface_role_ids": missing_roles,
        "generic_surface_signature_ids": generic_signature_ids,
        "temperature_mismatch_ids": temperature_mismatch_ids,
        "question_escape_detected": normalized.get("question_escape_detected") is True,
        "mirror_only_detected": normalized.get("mirror_only_detected") is True,
        "local_visible_surface_retained_here": False,
        "local_comment_text_retained_here": False,
        "detector_fragment_retained_here": False,
        "exact_sentence_match_required": False,
    }


def build_product_readfeel_p4_r11_surface_specificity_role_audit_20260624(
    *,
    surface_path_audit_payload: Mapping[str, Any] | None = None,
    local_surface_probes: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None = None,
    local_surface_probes_by_case_ref: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    source = dict(surface_path_audit_payload or base.build_product_readfeel_p4_r11_surface_path_audit_20260624())
    base.assert_product_readfeel_p4_r11_residual_surface_audit_meta_only_20260624(
        source,
        source="p4_r11.r6.surface_path_source",
    )
    if source.get("schema_version") != base.PRODUCT_READFEEL_P4_R11_SURFACE_PATH_AUDIT_VERSION_20260624:
        raise ValueError("p4_r11.r6 requires R11-5 surface path audit payload")

    probe_map = _local_surface_probe_map(local_surface_probes_by_case_ref or local_surface_probes)
    rows: list[dict[str, Any]] = []
    status_counts: Counter[str] = Counter()
    generic_counts: Counter[str] = Counter()
    temperature_counts: Counter[str] = Counter()
    specificity_gap_count = 0
    surface_probe_unavailable_count = 0

    for source_row in source.get("audit_rows") or []:
        if not isinstance(source_row, Mapping):
            continue
        if source_row.get("surface_path_audit_performed_here") is not True:
            raise ValueError("p4_r11.r6 requires R11-5 surface path audit before R11-6")
        row = dict(source_row)
        case_ref_id = _safe_identifier(row.get("case_ref_id"), default="")
        audit = _surface_specificity_audit_for_row(row, probe_text=probe_map.get(case_ref_id, ""))
        for signature_id in audit["generic_surface_signature_ids"]:
            generic_counts[signature_id] += 1
        for mismatch_id in audit["temperature_mismatch_ids"]:
            temperature_counts[mismatch_id] += 1
        if audit["surface_specificity_role_audit_status"] == _R6_STATUS_UNAVAILABLE:
            surface_probe_unavailable_count += 1
        if audit["missing_surface_role_ids"] or audit["generic_surface_signature_ids"]:
            specificity_gap_count += 1
        status_counts[audit["surface_specificity_role_audit_status"]] += 1

        row.update(
            {
                "schema_version": PRODUCT_READFEEL_P4_R11_SURFACE_SPECIFICITY_ROLE_AUDIT_VERSION_20260624,
                "source_step": base.P4_R11_R6_STEP_REF_20260624,
                "implemented_steps": P4_R11_R6_IMPLEMENTED_STEPS_20260624,
                "next_implementation_step": base.P4_R11_R7_STEP_REF_20260624,
                "surface_specificity_role_audit_performed_here": True,
                "surface_specificity_role_audit_status": audit["surface_specificity_role_audit_status"],
                "verdict_classification_performed_here": False,
                "verdict_status": "not_run_r11_7",
                "verdict_classification_status": "not_run_r11_7",
                "repair_candidate_layer_ids": [],
                "next_action": "not_run_r11_7",
                "actual_audit_rows_created_here": False,
                "actual_rating_rows_materialized_here": False,
                "actual_question_need_observation_rows_materialized_here": False,
                **audit,
                **_boundary_flags(),
            }
        )
        rows.append(row)

    summary = dict(source.get("summary") or {})
    summary.update(
        {
            "schema_version": PRODUCT_READFEEL_P4_R11_SURFACE_SPECIFICITY_ROLE_AUDIT_VERSION_20260624,
            "source_step": base.P4_R11_R6_STEP_REF_20260624,
            "audited_row_count": len(rows),
            "target_row_count": base.P4_R11_TARGET_ROW_COUNT_20260624,
            "surface_probe_unavailable_count": surface_probe_unavailable_count,
            "specificity_gap_count": specificity_gap_count,
            "surface_specificity_role_audit_status_counts": _counter_dict(status_counts),
            "generic_surface_signature_counts": _counter_dict(generic_counts),
            "temperature_mismatch_counts": _counter_dict(temperature_counts),
            "verdict_classification_status": "not_run_r11_7",
            "p6_start_allowed": False,
            "p8_start_allowed": False,
            "release_allowed": False,
        }
    )
    payload = {
        "schema_version": PRODUCT_READFEEL_P4_R11_SURFACE_SPECIFICITY_ROLE_AUDIT_VERSION_20260624,
        "version": PRODUCT_READFEEL_P4_R11_SURFACE_SPECIFICITY_ROLE_AUDIT_VERSION_20260624,
        "source": base.PRODUCT_READFEEL_P4_R11_SOURCE_20260624,
        "source_phase": base.PRODUCT_READFEEL_P4_R11_PHASE_20260624,
        "source_step": base.P4_R11_R6_STEP_REF_20260624,
        "run_id": _safe_identifier(run_id, default="p4_r11_r6_surface_specificity_role_audit"),
        "audit_profile": base.PRODUCT_READFEEL_P4_R11_AUDIT_PROFILE_20260624,
        "implemented_steps": P4_R11_R6_IMPLEMENTED_STEPS_20260624,
        "next_implementation_step": base.P4_R11_R7_STEP_REF_20260624,
        "summary": summary,
        "audit_rows": rows,
        "selected_case_ref_rows": rows,
        "selected_ref_row_count": len(rows),
        "case_ref_selection_performed_here": True,
        "material_route_audit_performed_here": True,
        "surface_path_audit_performed_here": True,
        "surface_specificity_role_audit_performed_here": True,
        "verdict_classification_performed_here": False,
        "summary_decision_handoff_performed_here": False,
        "actual_audit_rows_created_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "json_schema_file_materialized": False,
        **_boundary_flags(),
    }
    base.assert_product_readfeel_p4_r11_residual_surface_audit_meta_only_20260624(
        payload,
        source="p4_r11.r6.surface_specificity_role_audit",
    )
    return payload


def _repair_candidate_layer_ids(row: Mapping[str, Any], *, verdict: str) -> list[str]:
    if verdict == P4_R11_VERDICT_PASS_20260624:
        return []
    family_id = _clean(row.get("residual_family_id"))
    signatures = set(_dedupe(row.get("generic_surface_signature_ids")))
    missing = set(_dedupe(row.get("missing_surface_role_ids")))
    mismatch = set(_dedupe(row.get("temperature_mismatch_ids")))
    layers: list[str] = []
    if family_id == base.SCOPE_GROUP_CHANGE_FUTURE_INTENTION_TRANSITION:
        layers.extend(
            [
                "labelled_two_stage_surface_recomposition",
                "complete_initial_surface_recomposition",
                "product_readfeel_p4_surface_signature_audit",
            ]
        )
    elif family_id == base.SCOPE_GROUP_DAILY_POSITIVE_RECOVERY:
        layers.extend(["state_answer_ratio_policy", "two_stage_section_surface_plan", "complete_surface_realizer"])
    elif family_id == base.SCOPE_GROUP_RELATIONSHIP_GRATITUDE_RECOVERY:
        layers.extend(
            [
                "reception_mode_resolver",
                "state_answer_ratio_policy",
                "two_stage_section_surface_plan",
                "visible_surface_acceptance_gate",
            ]
        )
    elif family_id == base.SCOPE_GROUP_LONG_MEANING_ARC:
        layers.extend(["complete_surface_realizer", "two_stage_section_surface_plan", "product_readfeel_p4_ratings_review"])
    elif family_id == base.SCOPE_GROUP_STRUCTURE_QUESTION:
        layers.extend(["state_answer_ratio_policy", "two_stage_section_surface_plan"])
    elif family_id == base.SCOPE_GROUP_SELF_DENIAL_YELLOW_REMAINDER:
        layers.extend(["visible_surface_acceptance_gate", "state_answer_ratio_policy"])
    if signatures or missing:
        layers.append("visible_surface_acceptance_gate")
    if signatures:
        layers.append("product_readfeel_p4_surface_signature_audit")
    if mismatch:
        layers.append("product_readfeel_p4_ratings_review")
    return _dedupe(layers)


def _classify_row(row: Mapping[str, Any]) -> tuple[str, str, dict[str, bool], dict[str, bool]]:
    material_audit = row.get("material_audit") if isinstance(row.get("material_audit"), Mapping) else {}
    current_material = material_audit.get("current_only_material_available") is True
    generic = set(_dedupe(row.get("generic_surface_signature_ids")))
    missing = set(_dedupe(row.get("missing_surface_role_ids")))
    mismatch = set(_dedupe(row.get("temperature_mismatch_ids")))
    severe_red = bool(generic.intersection(_SEVERE_RED_SIGNATURE_IDS))
    if severe_red:
        verdict = P4_R11_VERDICT_RED_20260624
        next_action = P4_R11_NEXT_ACTION_P4_TARGETED_REPAIR_REQUIRED_20260624
    elif current_material and (generic or missing):
        verdict = P4_R11_VERDICT_REPAIR_REQUIRED_20260624
        next_action = P4_R11_NEXT_ACTION_P4_TARGETED_REPAIR_REQUIRED_20260624
    elif mismatch:
        verdict = P4_R11_VERDICT_YELLOW_20260624
        next_action = P4_R11_NEXT_ACTION_HUMAN_READFEEL_REVIEW_NOTE_ONLY_20260624
    else:
        verdict = P4_R11_VERDICT_PASS_20260624
        next_action = P4_R11_NEXT_ACTION_NO_ACTION_R54_RETURN_CANDIDATE_20260624

    risk_flags = {
        "p5_masking_risk": verdict in {P4_R11_VERDICT_REPAIR_REQUIRED_20260624, P4_R11_VERDICT_RED_20260624},
        "p8_question_escape_risk": verdict in {P4_R11_VERDICT_REPAIR_REQUIRED_20260624, P4_R11_VERDICT_RED_20260624},
        "self_blame_amplification_risk": "self_denial_identity_echo" in generic,
        "overclaim_risk": bool(generic.intersection({"relationship_target_judgement", "self_denial_identity_echo"})),
        "positive_cooling_risk": bool(mismatch.intersection({"positive_temperature_cooling", "positive_temperature_cooled"})),
        "long_arc_crush_risk": "long_arc_summary_crush" in generic,
        "structure_question_comfort_escape_risk": bool(
            generic.intersection({"structure_question_comfort_escape", "question_only_surface"})
            or "observation_ratio_low" in mismatch
        ),
    }
    repair_required_before_history = verdict in {
        P4_R11_VERDICT_REPAIR_REQUIRED_20260624,
        P4_R11_VERDICT_RED_20260624,
    }
    p5_p8_escape_boundary = {
        "p5_masking_forbidden": repair_required_before_history,
        "p8_question_escape_forbidden": repair_required_before_history,
        "current_only_repair_required_before_history_or_question": repair_required_before_history,
    }
    return verdict, next_action, risk_flags, p5_p8_escape_boundary


def build_product_readfeel_p4_r11_verdict_repair_candidate_classification_20260624(
    *,
    surface_specificity_role_audit_payload: Mapping[str, Any] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    source = dict(
        surface_specificity_role_audit_payload
        or build_product_readfeel_p4_r11_surface_specificity_role_audit_20260624()
    )
    base.assert_product_readfeel_p4_r11_residual_surface_audit_meta_only_20260624(
        source,
        source="p4_r11.r7.surface_specificity_source",
    )
    if source.get("schema_version") != PRODUCT_READFEEL_P4_R11_SURFACE_SPECIFICITY_ROLE_AUDIT_VERSION_20260624:
        raise ValueError("p4_r11.r7 requires R11-6 surface specificity audit payload")

    rows: list[dict[str, Any]] = []
    verdict_counts: Counter[str] = Counter()
    next_action_counts: Counter[str] = Counter()
    current_only_blocker_count = 0
    repair_layer_counts: Counter[str] = Counter()
    for source_row in source.get("audit_rows") or []:
        if not isinstance(source_row, Mapping):
            continue
        if source_row.get("surface_specificity_role_audit_performed_here") is not True:
            raise ValueError("p4_r11.r7 requires R11-6 surface specificity audit before R11-7")
        row = dict(source_row)
        verdict, next_action, risk_flags, p5_p8_boundary = _classify_row(row)
        repair_layers = _repair_candidate_layer_ids(row, verdict=verdict)
        current_only_blocker = verdict in {
            P4_R11_VERDICT_REPAIR_REQUIRED_20260624,
            P4_R11_VERDICT_RED_20260624,
        }
        if current_only_blocker:
            current_only_blocker_count += 1
        verdict_counts[verdict] += 1
        next_action_counts[next_action] += 1
        for layer in repair_layers:
            repair_layer_counts[layer] += 1
        row.update(
            {
                "schema_version": PRODUCT_READFEEL_P4_R11_VERDICT_REPAIR_CLASSIFICATION_VERSION_20260624,
                "source_step": base.P4_R11_R7_STEP_REF_20260624,
                "implemented_steps": P4_R11_R7_IMPLEMENTED_STEPS_20260624,
                "next_implementation_step": base.P4_R11_R8_STEP_REF_20260624,
                "surface_specificity_role_audit_performed_here": True,
                "verdict_classification_performed_here": True,
                "verdict_status": _R7_STATUS_CLASSIFIED,
                "verdict_classification_status": _R7_STATUS_CLASSIFIED,
                "verdict": verdict,
                "next_action": next_action,
                "current_only_blocker": current_only_blocker,
                "repair_candidate_layer_ids": repair_layers,
                "risk_flags": risk_flags,
                "p5_p8_escape_boundary": p5_p8_boundary,
                "actual_audit_rows_created_here": False,
                "actual_rating_rows_materialized_here": False,
                "actual_question_need_observation_rows_materialized_here": False,
                **_boundary_flags(),
            }
        )
        rows.append(row)

    summary = dict(source.get("summary") or {})
    summary.update(
        {
            "schema_version": PRODUCT_READFEEL_P4_R11_VERDICT_REPAIR_CLASSIFICATION_VERSION_20260624,
            "source_step": base.P4_R11_R7_STEP_REF_20260624,
            "audited_row_count": len(rows),
            "target_row_count": base.P4_R11_TARGET_ROW_COUNT_20260624,
            "verdict_counts": _counter_dict(verdict_counts),
            "pass_count": int(verdict_counts[P4_R11_VERDICT_PASS_20260624]),
            "yellow_count": int(verdict_counts[P4_R11_VERDICT_YELLOW_20260624]),
            "repair_required_count": int(verdict_counts[P4_R11_VERDICT_REPAIR_REQUIRED_20260624]),
            "red_count": int(verdict_counts[P4_R11_VERDICT_RED_20260624]),
            "next_action_counts": _counter_dict(next_action_counts),
            "repair_candidate_layer_counts": _counter_dict(repair_layer_counts),
            "current_only_blocker_count": current_only_blocker_count,
            "p4_targeted_repair_required": current_only_blocker_count > 0,
            "r54_return_candidate_after_r11": False,
            "r54_return_candidate_after_r11_not_decided_until_r11_8": True,
            "verdict_classification_status": _R7_STATUS_CLASSIFIED,
            "p6_start_allowed": False,
            "p8_start_allowed": False,
            "release_allowed": False,
        }
    )
    payload = {
        "schema_version": PRODUCT_READFEEL_P4_R11_VERDICT_REPAIR_CLASSIFICATION_VERSION_20260624,
        "version": PRODUCT_READFEEL_P4_R11_VERDICT_REPAIR_CLASSIFICATION_VERSION_20260624,
        "source": base.PRODUCT_READFEEL_P4_R11_SOURCE_20260624,
        "source_phase": base.PRODUCT_READFEEL_P4_R11_PHASE_20260624,
        "source_step": base.P4_R11_R7_STEP_REF_20260624,
        "run_id": _safe_identifier(run_id, default="p4_r11_r7_verdict_repair_candidate_classification"),
        "audit_profile": base.PRODUCT_READFEEL_P4_R11_AUDIT_PROFILE_20260624,
        "implemented_steps": P4_R11_R7_IMPLEMENTED_STEPS_20260624,
        "next_implementation_step": base.P4_R11_R8_STEP_REF_20260624,
        "summary": summary,
        "audit_rows": rows,
        "selected_case_ref_rows": rows,
        "selected_ref_row_count": len(rows),
        "case_ref_selection_performed_here": True,
        "material_route_audit_performed_here": True,
        "surface_path_audit_performed_here": True,
        "surface_specificity_role_audit_performed_here": True,
        "verdict_classification_performed_here": True,
        "summary_decision_handoff_performed_here": False,
        "actual_audit_rows_created_here": False,
        "actual_rating_rows_materialized_here": False,
        "actual_question_need_observation_rows_materialized_here": False,
        "json_schema_file_materialized": False,
        **_boundary_flags(),
    }
    base.assert_product_readfeel_p4_r11_residual_surface_audit_meta_only_20260624(
        payload,
        source="p4_r11.r7.verdict_repair_candidate_classification",
    )
    return payload


__all__ = [
    "PRODUCT_READFEEL_P4_R11_SURFACE_SPECIFICITY_ROLE_AUDIT_VERSION_20260624",
    "PRODUCT_READFEEL_P4_R11_VERDICT_REPAIR_CLASSIFICATION_VERSION_20260624",
    "P4_R11_R6_IMPLEMENTED_STEPS_20260624",
    "P4_R11_R7_IMPLEMENTED_STEPS_20260624",
    "P4_R11_VERDICT_PASS_20260624",
    "P4_R11_VERDICT_YELLOW_20260624",
    "P4_R11_VERDICT_REPAIR_REQUIRED_20260624",
    "P4_R11_VERDICT_RED_20260624",
    "P4_R11_NEXT_ACTION_NO_ACTION_R54_RETURN_CANDIDATE_20260624",
    "P4_R11_NEXT_ACTION_P4_TARGETED_REPAIR_REQUIRED_20260624",
    "P4_R11_NEXT_ACTION_HUMAN_READFEEL_REVIEW_NOTE_ONLY_20260624",
    "P4_R11_NEXT_ACTION_SEPARATE_CONTRACT_OR_SAFETY_LEDGER_REQUIRED_20260624",
    "normalize_local_surface_probe_to_p4_r11_observation_ids_20260624",
    "build_product_readfeel_p4_r11_surface_specificity_role_audit_20260624",
    "build_product_readfeel_p4_r11_verdict_repair_candidate_classification_20260624",
]
