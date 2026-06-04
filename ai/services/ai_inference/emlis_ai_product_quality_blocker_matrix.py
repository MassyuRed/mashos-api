# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase 4 Blocker Matrix for EmlisAI Product Quality measurement.

The matrix maps measurement blockers to repair owner areas and repair policies.
It is internal QA material only: it does not change public response shape, RN
visibility, DB physical names, product-gate flags, or any EmlisAI gate.
"""

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
import json
from typing import Any, Final, NamedTuple

from emlis_ai_product_quality_contract_freeze import (
    assert_emlis_ai_product_quality_contract_freeze_meta_only,
    build_emlis_ai_product_quality_contract_freeze,
)
from emlis_ai_product_quality_measurement_event import normalize_product_quality_family
from emlis_ai_product_readfeel_current_output_inventory import PRODUCT_READFEEL_REQUIRED_FAMILIES

PRODUCT_QUALITY_BLOCKER_MATRIX_VERSION: Final = "cocolon.emlis.product_quality.blocker_matrix.v1"
PRODUCT_QUALITY_BLOCKER_MATRIX_SCHEMA_VERSION: Final = PRODUCT_QUALITY_BLOCKER_MATRIX_VERSION
PRODUCT_QUALITY_BLOCKER_MATRIX_ROW_VERSION: Final = "cocolon.emlis.product_quality.blocker_matrix_row.v1"
PRODUCT_QUALITY_BLOCKER_MATRIX_ROW_SCHEMA_VERSION: Final = PRODUCT_QUALITY_BLOCKER_MATRIX_ROW_VERSION
PRODUCT_QUALITY_BLOCKER_MATRIX_PHASE: Final = "Phase4_BlockerMatrix"
PRODUCT_QUALITY_BLOCKER_MATRIX_TARGET_STEP: Final = "ProductQualityMeasurement_BlockerRepair"

FAMILY_ALL: Final = "all"
FAMILY_UNKNOWN: Final = "unknown"
_SAMPLE_ROW_LIMIT: Final = 8

_TEXT_PAYLOAD_KEYS: Final[frozenset[str]] = frozenset(
    {
        "raw_input", "rawInput", "raw_text", "rawText", "source_text", "sourceText",
        "input", "input_text", "inputText", "user_input", "userInput", "memo",
        "memo_text", "memoText", "memo_action", "memoAction", "current_input",
        "currentInput", "comment_text", "commentText", "comment_text_body",
        "commentTextBody", "input_feedback_comment", "inputFeedbackComment",
        "public_comment_text", "candidate_comment_text", "reply_text", "replyText",
        "surface_text", "surfaceText", "realized_text", "realizedText", "display_text",
        "displayText", "observation_text", "reception_text", "candidate_body",
        "candidateBody", "surface_body", "surfaceBody", "body", "text",
    }
)
_FORBIDDEN_TRUE_FLAGS: Final[frozenset[str]] = frozenset(
    {
        "api_route_changed", "request_key_changed", "response_shape_changed",
        "public_response_key_added", "public_response_key_change",
        "db_physical_name_changed", "rn_visible_contract_changed", "rn_visible_title_changed",
        "display_gate_relaxed", "grounding_gate_relaxed", "reader_gate_relaxed",
        "template_gate_relaxed", "gate_relaxed", "raw_input_included", "raw_text_included",
        "input_text_included", "comment_text_included", "comment_text_body_included",
        "candidate_body_included", "surface_body_included", "product_gate_ready",
        "product_gate_reached", "product_gate_public_release_applied", "public_release_applied",
        "product_quality_released", "machine_metrics_used_for_read_feeling",
        "read_feeling_auto_filled_from_machine_metrics", "read_feeling_auto_estimation_allowed",
        "fixed_sentence_template_added", "fixed_sentence_template_used",
        "input_specific_template_added", "external_ai_used", "local_llm_used",
    }
)
_ALLOWED_ROW_KEYS: Final[frozenset[str]] = frozenset(
    {
        "schema_version", "run_id", "blocker_id", "severity", "blocker_group", "family",
        "observed_count", "sample_row_ids", "likely_owner_area", "candidate_modules",
        "repair_policy", "target_metric", "target_metric_value", "contract_change_allowed",
        "public_contract_change_allowed", "gate_relaxation_allowed", "fixed_template_allowed",
        "runtime_fixture_branch_allowed", "release_blocking", "product_gate_ready",
        "public_release_applied", "raw_input_included", "comment_text_body_included",
        "candidate_body_included",
    }
)
_ALLOWED_MATRIX_KEYS: Final[frozenset[str]] = frozenset(
    {
        "schema_version", "version", "phase", "target_step", "run_id", "matrix_status",
        "source_event_count", "source_blocker_count", "row_count", "release_blocking_row_count",
        "contract_freeze", "contract_assertions", "rows", "repair_work_queue", "repair_queue",
        "blocker_ids", "blocker_group_counts", "owner_area_counts", "family_counts",
        "family_blocker_counts", "blockers_without_owner_area", "blockers_without_repair_policy",
        "all_release_blockers_have_owner_area", "all_release_blockers_have_repair_policy",
        "all_release_blockers_have_owner_area_and_repair_policy", "all_rows_contract_change_disallowed",
        "gate_relaxation_required", "fixed_template_required", "runtime_fixture_branch_required",
        "summary", "raw_input_included", "raw_text_included", "comment_text_body_included",
        "candidate_body_included", "public_response_key_added", "response_shape_changed",
        "api_route_changed", "db_physical_name_changed", "rn_visible_contract_changed",
        "rn_visible_title_changed", "display_gate_relaxed", "grounding_gate_relaxed",
        "template_gate_relaxed", "product_gate_ready", "product_gate_reached",
        "product_gate_public_release_applied", "public_release_applied",
    }
)

class _Taxonomy(NamedTuple):
    blocker_group: str
    likely_owner_area: str
    candidate_modules: tuple[str, ...]
    repair_policy: str
    severity: str = "blocker"
    release_blocking: bool = True

_GROUP_COMPOSER = _Taxonomy(
    "composer_bootstrap", "local_product_qa_composer_bootstrap",
    ("emlis_ai_composer_client_registry.py", "emlis_ai_limited_release_service.py", "emlis_ai_product_quality_measurement_runner.py"),
    "QAではComposer無効を成功扱いせず、local_product_qa profileとrollout境界を明示する。本番flagを雑に開けない。",
)
_GROUP_DISPLAY = _Taxonomy(
    "display_reach", "display_repair_and_gate_recovery",
    ("emlis_ai_observation_display_repair_integration.py", "emlis_ai_gate_recovery_loop.py", "emlis_ai_low_information_observation_composer.py", "emlis_ai_reply_service.py"),
    "passed条件やRN/API契約を緩めず、生成・短縮・限定・post-final recoveryで表示可能な観測文へ戻す。",
)
_GROUP_LOW_INFORMATION = _Taxonomy(
    "low_information", "display_repair_low_information",
    ("emlis_ai_low_information_observation_composer.py", "emlis_ai_observation_display_repair_integration.py", "emlis_ai_gate_recovery_loop.py"),
    "低情報でも分かったふりをせず、詳細化されていない重さ・未形成さを短い観測として返す。質問だけ・原因推定へ逃がさない。",
)
_GROUP_BINDING = _Taxonomy(
    "binding", "evidence_ledger_and_sentence_binding",
    ("emlis_ai_evidence_ledger_service.py", "emlis_ai_shared_reception_evidence.py", "emlis_ai_complete_sentence_planner.py", "emlis_ai_grounding_judge.py"),
    "sentenceが現在入力の根拠へ接続するよう、根拠ledger・sentence plan・groundingを狭める。根拠なし断定で埋めない。",
)
_GROUP_REASON = _Taxonomy(
    "reason_coverage", "relation_reason_planner",
    ("emlis_ai_complete_relation_graph_service.py", "emlis_ai_complete_sentence_planner.py", "emlis_ai_relation_surface_contract.py", "emlis_ai_limited_sentence_quality_guard.py"),
    "理由が必要な文に、入力根拠・関係・限定表現を付ける。原因推定や人格推定で補完しない。",
)
_GROUP_SURFACE = _Taxonomy(
    "surface_repetition_template", "surface_realizer_anti_template",
    ("emlis_ai_complete_surface_realizer_anti_template.py", "emlis_ai_complete_surface_quality_signature.py", "emlis_ai_runtime_surface_tone_engine_2_1.py", "emlis_ai_mirror_only_surface_detector.py"),
    "固定文ではなく、入力の整理軸・状態語・関係構造に接続したsurfaceへ変える。family横断の同型反復を止める。",
)
_GROUP_SAFETY = _Taxonomy(
    "self_denial_safety", "self_denial_safe_state_answer_and_safety_triage",
    ("emlis_ai_safety_triage.py", "emlis_ai_safety_boundary_service.py", "emlis_ai_state_answer_special_cases.py", "emlis_ai_state_answer_gate_boundary.py"),
    "自己否定を事実認定せず、負荷の高い状態として扱う。緊急安全境界と通常の安全な状態回答を分ける。",
)
_GROUP_STRUCTURE = _Taxonomy(
    "structure_insight", "structure_insight_gate_and_surface",
    ("emlis_ai_structure_insight_candidate.py", "emlis_ai_structure_insight_gate.py", "emlis_ai_structure_insight_surface.py", "emlis_ai_complete_surface_quality_signature.py"),
    "Structure Insightは許可familyに限定し、断定・診断・人格化・single record tendencyをGateで止める。日常短文へ無理に深掘りしない。",
)
_GROUP_USER_LABEL = _Taxonomy(
    "user_label_connection", "user_label_connection_material_gate_surface_qa",
    ("emlis_ai_user_label_connection_material.py", "emlis_ai_user_label_connection_gate.py", "emlis_ai_user_label_connection_surface.py", "emlis_ai_user_label_connection_product_quality_qa.py"),
    "履歴で決めつけず、今回の言葉との軽い接続に留める。creepy・overclaim・self-blame増幅をrelease blockerとして扱う。",
)
_GROUP_BLIND_QA = _Taxonomy(
    "blind_qa", "runtime_surface_blind_qa_review_flow",
    ("emlis_ai_runtime_surface_blind_qa_long_run.py", "emlis_ai_product_readfeel_scorecard.py", "emlis_ai_user_label_connection_product_quality_qa.py"),
    "人間Blind QAのratings-only reviewなしで商品pass扱いしない。read feelingをmachine metricsで自動補完しない。",
)
_GROUP_PHASE11 = _Taxonomy(
    "phase11_long_run", "long_run_product_gate_material_and_input_set",
    ("emlis_ai_product_readfeel_long_run_product_gate.py", "emlis_ai_runtime_surface_blind_qa_long_run.py", "emlis_ai_product_quality_measurement_runner.py"),
    "長期安定性、required family coverage、5/10連続pass、surface repetitionなしを満たすまでrelease不可として扱う。",
)
_GROUP_CONTRACT = _Taxonomy(
    "contract_leakage", "public_contract_boundary_and_meta_sanitizer",
    ("emlis_ai_product_quality_contract_freeze.py", "emlis_ai_product_quality_measurement_event.py", "emlis_ai_public_feedback_meta.py", "api_emotion_submit.py"),
    "raw input/comment body/candidate body/public key変更をrelease blockerにし、public/RN/DB契約を変えずmeta-only materialへ戻す。", "critical",
)
_GROUP_UNKNOWN = _Taxonomy(
    "unmapped_product_quality_blocker", "product_quality_measurement_triage",
    ("emlis_ai_product_quality_measurement_event.py", "emlis_ai_product_quality_measurement_runner.py"),
    "未分類blockerとして扱い、Gate緩和やfixture専用分岐ではなく、原因のowner_areaを追加分類してから修正する。",
)

_EXACT_TAXONOMY: Final[dict[str, _Taxonomy]] = {
    "composer_generation_path_not_open_for_product_qa": _GROUP_COMPOSER,
    "composer_feature_flag_disabled_for_product_qa": _GROUP_COMPOSER,
    "default_limited_composer_feature_disabled": _GROUP_COMPOSER,
    "composer_rollout_not_open_for_local_product_qa": _GROUP_COMPOSER,
    "complete_initial_not_ready_for_product_qa": _GROUP_COMPOSER,
    "complete_initial_rollout_not_allowed_for_product_qa": _GROUP_COMPOSER,
    "display_not_reached": _GROUP_DISPLAY,
    "comment_text_missing": _GROUP_DISPLAY,
    "observation_status_not_passed": _GROUP_DISPLAY,
    "product_readfeel_display_reach_rate_below_target": _GROUP_DISPLAY,
    "binding_not_passed": _GROUP_BINDING,
    "product_readfeel_binding_pass_rate_below_target": _GROUP_BINDING,
    "unsupported_binding": _GROUP_BINDING,
    "reason_coverage_not_passed": _GROUP_REASON,
    "product_readfeel_reason_coverage_below_target": _GROUP_REASON,
    "product_readfeel_reason_coverage_incomplete": _GROUP_REASON,
    "template_major_detected": _GROUP_SURFACE,
    "product_readfeel_template_major_detected": _GROUP_SURFACE,
    "family_cross_surface_repetition_detected": _GROUP_SURFACE,
    "long_run_surface_signature_repeat_detected": _GROUP_SURFACE,
    "insight_surface_same_syntax_repetition_detected": _GROUP_SURFACE,
    "shallow_repeat_risk": _GROUP_SURFACE,
    "mirror_only_detected": _GROUP_SURFACE,
    "low_information_display_repair_failed": _GROUP_LOW_INFORMATION,
    "unsafe_insight_surface_detected": _GROUP_SAFETY,
    "safety_major_detected": _GROUP_SAFETY,
    "product_readfeel_safety_major_detected": _GROUP_SAFETY,
    "red_or_repair_required_row_present": _GROUP_SAFETY,
    "product_readfeel_red_family_detected": _GROUP_SAFETY,
    "product_readfeel_repair_required_family_detected": _GROUP_SAFETY,
    "blind_qa_red_review_detected": _GROUP_SAFETY,
    "insight_surface_signature_missing": _GROUP_STRUCTURE,
    "product_readfeel_v2_scorecard_not_ready": _GROUP_STRUCTURE,
    "structure_insight_v2_not_ready": _GROUP_STRUCTURE,
    "structure_insight_backlog_families_present": _GROUP_STRUCTURE,
    "insight_delta_not_evaluated": _GROUP_STRUCTURE,
    "insight_delta_below_structure_insight_target": _GROUP_STRUCTURE,
    "v1_product_pass_required_first": _GROUP_STRUCTURE,
    "no_reviewable_user_label_connection_candidates": _GROUP_USER_LABEL,
    "history_connection_creepiness_risk": _GROUP_USER_LABEL,
    "history_connection_naturalness_below_target": _GROUP_USER_LABEL,
    "overclaim_or_deciding_risk": _GROUP_USER_LABEL,
    "self_blame_amplification_risk": _GROUP_USER_LABEL,
    "self_information_organization_below_target": _GROUP_USER_LABEL,
    "accumulation_motivation_not_confirmed": _GROUP_USER_LABEL,
    "product_quality_qa_text_payload_detected": _GROUP_USER_LABEL,
    "product_quality_qa_contract_relaxation_detected": _GROUP_USER_LABEL,
    "non_limited_visible_connection": _GROUP_USER_LABEL,
    "blind_qa_missing": _GROUP_BLIND_QA,
    "blind_qa_not_evaluated": _GROUP_BLIND_QA,
    "blind_qa_not_ready": _GROUP_BLIND_QA,
    "blind_qa_review_required": _GROUP_BLIND_QA,
    "blind_qa_review_coverage_below_target": _GROUP_BLIND_QA,
    "product_readfeel_blind_qa_missing": _GROUP_BLIND_QA,
    "read_feeling_score_below_product_gate_target": _GROUP_BLIND_QA,
    "read_feeling_below_product_quality_target": _GROUP_BLIND_QA,
    "product_readfeel_read_feeling_below_product_target": _GROUP_BLIND_QA,
    "runtime_surface_blind_qa_long_run_not_ready": _GROUP_BLIND_QA,
    "phase3_events_missing": _GROUP_PHASE11,
    "phase11_events_missing": _GROUP_PHASE11,
    "required_family_cross_coverage_incomplete": _GROUP_PHASE11,
    "product_readfeel_family_coverage_incomplete": _GROUP_PHASE11,
    "product_readfeel_v1_scorecard_not_product_pass": _GROUP_PHASE11,
    "product_readfeel_v1_scorecard_blockers_present": _GROUP_PHASE11,
    "product_readfeel_machine_metrics_missing": _GROUP_PHASE11,
    "product_readfeel_yellow_family_detected": _GROUP_PHASE11,
    "five_consecutive_v1_product_pass_not_observed": _GROUP_PHASE11,
    "ten_consecutive_v1_product_pass_not_observed": _GROUP_PHASE11,
    "phase11_attempted_to_set_release_flag": _GROUP_CONTRACT,
    "forbidden_text_payload_key_detected_in_source": _GROUP_CONTRACT,
    "forbidden_contract_or_release_flag_true_in_source": _GROUP_CONTRACT,
    "measurement_event_schema_invalid": _GROUP_CONTRACT,
}
_BLOCKER_ALIASES: Final[dict[str, str]] = {
    "public_display_boundary_not_reached": "public_display_not_reached",
}

def _clean(value: Any) -> str:
    if value is None or isinstance(value, (Mapping, list, tuple, set)):
        return ""
    return str(value).strip()

def _listify(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (str, bytes, bytearray)):
        return [value]
    if isinstance(value, Mapping):
        return list(value.values())
    if isinstance(value, Iterable):
        return list(value)
    return [value]

def _dedupe(values: Iterable[Any] | Any | None) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in _listify(values):
        text = _clean(item)
        if text and text not in seen:
            seen.add(text)
            out.append(text)
    return out

def _safe_identifier(value: Any, *, max_length: int = 96, default: str = "") -> str:
    text = _clean(value)
    if not text:
        return default
    text = text[:max_length]
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.:/-"
    if any(ch not in allowed for ch in text):
        return default
    return text

def _to_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default

def _normalize_family(value: Any) -> str:
    family = normalize_product_quality_family(value)
    return family or FAMILY_UNKNOWN

def _normalize_blocker_id(value: Any) -> str:
    blocker = _safe_identifier(value, max_length=128, default="unknown_blocker")
    return _BLOCKER_ALIASES.get(blocker, blocker)

def _contains_text_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in _TEXT_PAYLOAD_KEYS:
                return True
            if _contains_text_payload_key(child):
                return True
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_text_payload_key(child) for child in value)
    return False

def _forbidden_true_flag_path(value: Any, *, path: str = "payload") -> str | None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if str(key) in _FORBIDDEN_TRUE_FLAGS and child is True:
                return child_path
            nested = _forbidden_true_flag_path(child, path=child_path)
            if nested:
                return nested
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            nested = _forbidden_true_flag_path(child, path=f"{path}[{index}]")
            if nested:
                return nested
    return None

def _taxonomy_for(blocker_id: str) -> _Taxonomy:
    if blocker_id in _EXACT_TAXONOMY:
        return _EXACT_TAXONOMY[blocker_id]
    text = blocker_id.lower()
    if "composer" in text or "default_limited" in text or "complete_initial" in text:
        return _GROUP_COMPOSER
    if "display" in text or "comment_text" in text or "observation_status" in text:
        return _GROUP_DISPLAY
    if "binding" in text or "grounding" in text:
        return _GROUP_BINDING
    if "reason" in text:
        return _GROUP_REASON
    if "low_information" in text or "low_info" in text:
        return _GROUP_LOW_INFORMATION
    if "repeat" in text or "repetition" in text or "template" in text or "mirror_only" in text or "shallow" in text:
        return _GROUP_SURFACE
    if "history_connection" in text or "overclaim" in text or "self_blame" in text or "user_label" in text or "creepy" in text or "accumulation" in text:
        return _GROUP_USER_LABEL
    if "blind_qa" in text or "read_feeling" in text or "review" in text:
        return _GROUP_BLIND_QA
    if "unsafe" in text or "safety" in text or "self_denial" in text or "red" in text or "repair_required" in text:
        return _GROUP_SAFETY
    if "insight" in text or "structure" in text:
        return _GROUP_STRUCTURE
    if "phase11" in text or "consecutive" in text or "family_coverage" in text or "coverage" in text or "events_missing" in text:
        return _GROUP_PHASE11
    if "contract" in text or "forbidden" in text or "schema" in text or "release_flag" in text:
        return _GROUP_CONTRACT
    return _GROUP_UNKNOWN

def _target_metric_for(blocker_id: str, taxonomy: _Taxonomy) -> tuple[str, float | int]:
    group = taxonomy.blocker_group
    if group in {"display_reach", "low_information"}:
        return "display_reach_rate", 0.9
    if group == "binding":
        return "binding_pass_rate", 0.98
    if group == "reason_coverage":
        return "reason_coverage_rate", 1.0
    if group == "surface_repetition_template":
        return "surface_repetition_count", 0
    if group == "self_denial_safety":
        return "safety_major_count", 0
    if group == "blind_qa":
        return "blind_qa_review_coverage_rate", 1.0
    if group == "user_label_connection":
        return "user_label_connection_quality_score", 0.9
    if group == "phase11_long_run":
        return "long_run_product_pass", 1.0
    if group == "composer_bootstrap":
        return "composer_generation_path_open", 1.0
    if group == "contract_leakage":
        return "contract_violation_count", 0
    return "manual_triage_required", 1.0

def classify_product_quality_blocker(blocker_id: Any, *, family: Any = FAMILY_ALL) -> dict[str, Any]:
    blocker = _normalize_blocker_id(blocker_id)
    normalized_family = family if family in {FAMILY_ALL, FAMILY_UNKNOWN} else _normalize_family(family)
    taxonomy = _taxonomy_for(blocker)
    if normalized_family in {"low_information_short", "positive_only"} and (
        taxonomy == _GROUP_DISPLAY
        or blocker in {"display_not_reached", "public_display_not_reached", "comment_text_missing", "product_readfeel_display_reach_rate_below_target", "low_information_display_repair_failed"}
    ):
        taxonomy = _GROUP_LOW_INFORMATION
    if normalized_family == "self_denial" and taxonomy.blocker_group in {"display_reach", "self_denial_safety"}:
        taxonomy = _GROUP_SAFETY
    metric, target = _target_metric_for(blocker, taxonomy)
    return {
        "blocker_id": blocker,
        "blocker_group": taxonomy.blocker_group,
        "severity": taxonomy.severity,
        "family": normalized_family,
        "likely_owner_area": taxonomy.likely_owner_area,
        "candidate_modules": list(taxonomy.candidate_modules),
        "repair_policy": taxonomy.repair_policy,
        "target_metric": metric,
        "target_metric_value": target,
        "contract_change_allowed": False,
        "public_contract_change_allowed": False,
        "gate_relaxation_allowed": False,
        "fixed_template_allowed": False,
        "runtime_fixture_branch_allowed": False,
        "release_blocking": bool(taxonomy.release_blocking),
    }

def _event_family(event: Mapping[str, Any]) -> str:
    return _normalize_family(event.get("family") or event.get("product_readfeel_family") or event.get("coverage_group"))

def _event_row_id(event: Mapping[str, Any]) -> str:
    return _safe_identifier(event.get("row_id") or event.get("candidate_id") or event.get("event_id"), max_length=96, default="")

def _event_blockers(event: Mapping[str, Any]) -> list[str]:
    blockers = [_normalize_blocker_id(item) for item in _dedupe(event.get("blockers"))]
    if "public_display_not_reached" in blockers and "display_not_reached" not in blockers:
        blockers.append("display_not_reached")
    return blockers

def _event_binding_failed(event: Mapping[str, Any]) -> bool:
    binding = event.get("binding") if isinstance(event.get("binding"), Mapping) else event
    return bool(binding) and binding.get("binding_passed") is False

def _event_reason_failed(event: Mapping[str, Any]) -> bool:
    reason = event.get("reason_coverage") if isinstance(event.get("reason_coverage"), Mapping) else event
    return bool(reason) and reason.get("reason_coverage_passed") is False

def _event_template_detected(event: Mapping[str, Any]) -> bool:
    surface = event.get("surface_quality") if isinstance(event.get("surface_quality"), Mapping) else event
    return _to_int(surface.get("template_major_count")) > 0 or surface.get("mirror_only_detected") is True

def _event_safety_detected(event: Mapping[str, Any]) -> bool:
    surface = event.get("surface_quality") if isinstance(event.get("surface_quality"), Mapping) else {}
    safety = event.get("safety") if isinstance(event.get("safety"), Mapping) else event
    return _to_int(safety.get("safety_major_count")) > 0 or surface.get("unsafe_insight_surface_detected") is True

def _matching_events_for_run_blocker(blocker_id: str, events: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    text = blocker_id.lower()
    if "display" in text or blocker_id in {"comment_text_missing", "observation_status_not_passed"}:
        return [event for event in events if event.get("public_display_reached") is not True]
    if "binding" in text:
        return [event for event in events if _event_binding_failed(event)]
    if "reason" in text:
        return [event for event in events if _event_reason_failed(event)]
    if "template" in text or "repeat" in text or "repetition" in text or "mirror_only" in text or "shallow" in text:
        return [event for event in events if _event_template_detected(event)]
    if "safety" in text or "unsafe" in text or "self_denial" in text or "red" in text or "repair_required" in text:
        return [event for event in events if _event_safety_detected(event)]
    if "low_information" in text or "low_info" in text:
        return [event for event in events if _event_family(event) == "low_information_short"]
    if "history_connection" in text or "overclaim" in text or "self_blame" in text or "user_label" in text or "creepy" in text or "accumulation" in text:
        return [event for event in events if _event_family(event) in {"structure_question", "long_meaning_arc", "self_understanding_follow"}]
    if "insight" in text or "structure" in text:
        return [event for event in events if _event_family(event) in {"structure_question", "long_meaning_arc", "self_understanding_follow"}]
    return []

def _collect_summary_blockers(*, product_readfeel_scorecard: Mapping[str, Any] | None = None, runtime_surface_blind_qa_long_run_summary: Mapping[str, Any] | None = None, runtime_summary: Mapping[str, Any] | None = None, user_label_connection_qa_summary: Mapping[str, Any] | None = None, user_label_summary: Mapping[str, Any] | None = None, phase11_long_run_product_gate: Mapping[str, Any] | None = None, phase11_gate: Mapping[str, Any] | None = None) -> list[str]:
    blockers: list[str] = []
    scorecard = product_readfeel_scorecard if isinstance(product_readfeel_scorecard, Mapping) else {}
    runtime = runtime_surface_blind_qa_long_run_summary if isinstance(runtime_surface_blind_qa_long_run_summary, Mapping) else (runtime_summary if isinstance(runtime_summary, Mapping) else {})
    user_label = user_label_connection_qa_summary if isinstance(user_label_connection_qa_summary, Mapping) else (user_label_summary if isinstance(user_label_summary, Mapping) else {})
    phase11 = phase11_long_run_product_gate if isinstance(phase11_long_run_product_gate, Mapping) else (phase11_gate if isinstance(phase11_gate, Mapping) else {})
    blockers.extend(_dedupe(scorecard.get("release_blockers") or scorecard.get("product_readfeel_scorecard_release_blockers")))
    blockers.extend(_dedupe(runtime.get("release_blockers") or runtime.get("step11_release_blockers")))
    blockers.extend(_dedupe(user_label.get("release_blockers") or user_label.get("qa_blockers")))
    blockers.extend(_dedupe(phase11.get("v1_product_pass_blockers")))
    if phase11.get("product_gate_ready") is True or phase11.get("public_release_applied") is True:
        blockers.append("phase11_attempted_to_set_release_flag")
    return [_normalize_blocker_id(item) for item in _dedupe(blockers)]

def _add_occurrence(occurrences: dict[tuple[str, str], dict[str, Any]], *, blocker_id: Any, family: Any, row_ids: Iterable[str] | None = None, observed_count: int | None = None) -> None:
    blocker = _normalize_blocker_id(blocker_id)
    normalized_family = family if family in {FAMILY_ALL, FAMILY_UNKNOWN} else _normalize_family(family)
    key = (blocker, normalized_family)
    bucket = occurrences.setdefault(key, {"blocker_id": blocker, "family": normalized_family, "row_ids": [], "observed_count": 0})
    row_values = [row_id for row_id in _dedupe(row_ids or []) if row_id]
    for row_id in row_values:
        if row_id not in bucket["row_ids"]:
            bucket["row_ids"].append(row_id)
    if observed_count is not None:
        bucket["observed_count"] += max(0, int(observed_count))
    elif row_values:
        bucket["observed_count"] += len(row_values)
    else:
        bucket["observed_count"] += 1

def _families_from_events(events: Sequence[Mapping[str, Any]]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for event in events:
        family = _event_family(event)
        row_id = _event_row_id(event)
        grouped.setdefault(family, [])
        if row_id and row_id not in grouped[family]:
            grouped[family].append(row_id)
    return grouped

def _build_row(*, run_id: str, blocker_id: str, family: str, observed_count: int, row_ids: Sequence[str]) -> dict[str, Any]:
    classified = classify_product_quality_blocker(blocker_id, family=family)
    row = {
        "schema_version": PRODUCT_QUALITY_BLOCKER_MATRIX_ROW_VERSION,
        "run_id": _safe_identifier(run_id, max_length=96, default=""),
        "blocker_id": classified["blocker_id"],
        "severity": classified["severity"],
        "blocker_group": classified["blocker_group"],
        "family": classified["family"],
        "observed_count": max(0, int(observed_count)),
        "sample_row_ids": _dedupe(row_ids)[:_SAMPLE_ROW_LIMIT],
        "likely_owner_area": classified["likely_owner_area"],
        "candidate_modules": classified["candidate_modules"],
        "repair_policy": classified["repair_policy"],
        "target_metric": classified["target_metric"],
        "target_metric_value": classified["target_metric_value"],
        "contract_change_allowed": False,
        "public_contract_change_allowed": False,
        "gate_relaxation_allowed": False,
        "fixed_template_allowed": False,
        "runtime_fixture_branch_allowed": False,
        "release_blocking": bool(classified["release_blocking"]),
        "product_gate_ready": False,
        "public_release_applied": False,
        "raw_input_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
    }
    assert_product_quality_blocker_matrix_row_meta_only(row)
    return row

def build_product_quality_blocker_matrix(*, run_id: Any = "", measurement_events: Sequence[Mapping[str, Any]] | None = None, events: Sequence[Mapping[str, Any]] | None = None, run_blockers: Sequence[Any] | None = None, blockers: Sequence[Any] | None = None, summary_metrics: Mapping[str, Any] | None = None, machine_metrics: Mapping[str, Any] | None = None, family_counts: Mapping[str, Any] | None = None, missing_required_families: Sequence[Any] | None = None, product_readfeel_scorecard: Mapping[str, Any] | None = None, runtime_surface_blind_qa_long_run_summary: Mapping[str, Any] | None = None, runtime_summary: Mapping[str, Any] | None = None, user_label_connection_qa_summary: Mapping[str, Any] | None = None, user_label_summary: Mapping[str, Any] | None = None, phase11_long_run_product_gate: Mapping[str, Any] | None = None, phase11_gate: Mapping[str, Any] | None = None, composer_bootstrap: Mapping[str, Any] | None = None) -> dict[str, Any]:
    source_events = measurement_events if measurement_events is not None else events
    event_list = [dict(event) for event in (source_events or []) if isinstance(event, Mapping)]
    run_id_value = _safe_identifier(run_id or (event_list[0].get("run_id") if event_list else ""), max_length=96, default="product_quality_run")
    occurrences: dict[tuple[str, str], dict[str, Any]] = {}
    for event in event_list:
        family = _event_family(event)
        row_id = _event_row_id(event)
        for blocker in _event_blockers(event):
            _add_occurrence(occurrences, blocker_id=blocker, family=family, row_ids=[row_id] if row_id else [])
    all_run_blockers = [_normalize_blocker_id(item) for item in _dedupe(run_blockers if run_blockers is not None else blockers)]
    for blocker in _dedupe(blockers):
        normalized = _normalize_blocker_id(blocker)
        if normalized not in all_run_blockers:
            all_run_blockers.append(normalized)
    for blocker in _collect_summary_blockers(product_readfeel_scorecard=product_readfeel_scorecard, runtime_surface_blind_qa_long_run_summary=runtime_surface_blind_qa_long_run_summary, runtime_summary=runtime_summary, user_label_connection_qa_summary=user_label_connection_qa_summary, user_label_summary=user_label_summary, phase11_long_run_product_gate=phase11_long_run_product_gate, phase11_gate=phase11_gate):
        if blocker not in all_run_blockers:
            all_run_blockers.append(blocker)
    if isinstance(composer_bootstrap, Mapping):
        for blocker in _dedupe(composer_bootstrap.get("blockers")):
            blocker = _normalize_blocker_id(blocker)
            if blocker not in all_run_blockers:
                all_run_blockers.append(blocker)
    metrics = dict(summary_metrics or machine_metrics or {})
    if metrics.get("template_major_count") and _to_int(metrics.get("template_major_count")) > 0 and "template_major_detected" not in all_run_blockers:
        all_run_blockers.append("template_major_detected")
    if metrics.get("safety_major_count") and _to_int(metrics.get("safety_major_count")) > 0 and "safety_major_detected" not in all_run_blockers:
        all_run_blockers.append("safety_major_detected")
    normalized_family_counts = {_normalize_family(family): _to_int(count) for family, count in dict(family_counts or {}).items() if _clean(family)}
    missing_families = [_normalize_family(family) for family in _dedupe(missing_required_families)]
    if "required_family_cross_coverage_incomplete" in all_run_blockers and not missing_families:
        missing_families = [family for family in PRODUCT_READFEEL_REQUIRED_FAMILIES if normalized_family_counts.get(family, 0) <= 0]
    for blocker in all_run_blockers:
        if blocker == "required_family_cross_coverage_incomplete" and missing_families:
            for family in missing_families:
                _add_occurrence(occurrences, blocker_id=blocker, family=family, observed_count=1)
            continue
        matches = _matching_events_for_run_blocker(blocker, event_list)
        if matches:
            for family, row_ids in _families_from_events(matches).items():
                _add_occurrence(occurrences, blocker_id=blocker, family=family, row_ids=row_ids, observed_count=0 if row_ids else len(matches))
            continue
        family = FAMILY_ALL if event_list or all_run_blockers else FAMILY_UNKNOWN
        _add_occurrence(occurrences, blocker_id=blocker, family=family, observed_count=len(event_list) if event_list else 1)
    rows = [_build_row(run_id=run_id_value, blocker_id=bucket["blocker_id"], family=bucket["family"], observed_count=max(1, _to_int(bucket.get("observed_count"))), row_ids=list(bucket.get("row_ids") or [])) for bucket in occurrences.values()]
    rows.sort(key=lambda row: (row["blocker_group"], row["blocker_id"], row["family"]))
    group_counts = Counter(str(row["blocker_group"]) for row in rows)
    owner_counts = Counter(str(row["likely_owner_area"]) for row in rows)
    family_blocker_counts = Counter(str(row["family"]) for row in rows)
    blocker_ids = _dedupe(row.get("blocker_id") for row in rows)
    blockers_without_owner = [str(row["blocker_id"]) for row in rows if not _clean(row.get("likely_owner_area"))]
    blockers_without_policy = [str(row["blocker_id"]) for row in rows if not _clean(row.get("repair_policy"))]
    release_blocking_count = sum(1 for row in rows if row.get("release_blocking") is True)
    summary = {
        "row_count": len(rows),
        "release_blocking_row_count": release_blocking_count,
        "blocker_group_counts": dict(sorted(group_counts.items())),
        "owner_area_counts": dict(sorted(owner_counts.items())),
    }
    matrix = {
        "schema_version": PRODUCT_QUALITY_BLOCKER_MATRIX_VERSION,
        "version": PRODUCT_QUALITY_BLOCKER_MATRIX_VERSION,
        "phase": PRODUCT_QUALITY_BLOCKER_MATRIX_PHASE,
        "target_step": PRODUCT_QUALITY_BLOCKER_MATRIX_TARGET_STEP,
        "run_id": run_id_value,
        "matrix_status": "ready" if rows else "no_blockers_detected",
        "source_event_count": len(event_list),
        "source_blocker_count": len(blocker_ids),
        "row_count": len(rows),
        "release_blocking_row_count": release_blocking_count,
        "contract_freeze": build_emlis_ai_product_quality_contract_freeze(),
        "contract_assertions": {
            "api_route_changed": False, "response_shape_changed": False, "public_response_key_added": False,
            "db_physical_name_changed": False, "rn_visible_contract_changed": False, "rn_visible_title_changed": False,
            "display_gate_relaxed": False, "grounding_gate_relaxed": False, "template_gate_relaxed": False,
            "raw_input_included": False, "raw_text_included": False, "comment_text_body_included": False,
            "candidate_body_included": False,
        },
        "rows": rows,
        "repair_work_queue": rows,
        "repair_queue": rows,
        "blocker_ids": blocker_ids,
        "blocker_group_counts": dict(sorted(group_counts.items())),
        "owner_area_counts": dict(sorted(owner_counts.items())),
        "family_counts": {key: int(value) for key, value in sorted(normalized_family_counts.items())},
        "family_blocker_counts": dict(sorted(family_blocker_counts.items())),
        "blockers_without_owner_area": _dedupe(blockers_without_owner),
        "blockers_without_repair_policy": _dedupe(blockers_without_policy),
        "all_release_blockers_have_owner_area": not blockers_without_owner,
        "all_release_blockers_have_repair_policy": not blockers_without_policy,
        "all_release_blockers_have_owner_area_and_repair_policy": not blockers_without_owner and not blockers_without_policy,
        "all_rows_contract_change_disallowed": all(row.get("contract_change_allowed") is False for row in rows),
        "gate_relaxation_required": False,
        "fixed_template_required": False,
        "runtime_fixture_branch_required": False,
        "summary": summary,
        "raw_input_included": False, "raw_text_included": False, "comment_text_body_included": False,
        "candidate_body_included": False, "public_response_key_added": False, "response_shape_changed": False,
        "api_route_changed": False, "db_physical_name_changed": False, "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False, "display_gate_relaxed": False, "grounding_gate_relaxed": False,
        "template_gate_relaxed": False, "product_gate_ready": False, "product_gate_reached": False,
        "product_gate_public_release_applied": False, "public_release_applied": False,
    }
    assert_product_quality_blocker_matrix_meta_only(matrix)
    return matrix

def build_product_quality_blocker_matrix_from_measurement_run(run: Mapping[str, Any]) -> dict[str, Any]:
    return build_product_quality_blocker_matrix(
        run_id=run.get("run_id") if isinstance(run, Mapping) else "",
        measurement_events=run.get("measurement_events") if isinstance(run.get("measurement_events"), Sequence) else [],
        run_blockers=run.get("blockers") if isinstance(run.get("blockers"), Sequence) else [],
        family_counts=run.get("family_counts") if isinstance(run.get("family_counts"), Mapping) else {},
        missing_required_families=run.get("missing_required_families") if isinstance(run.get("missing_required_families"), Sequence) else [],
        product_readfeel_scorecard=run.get("product_readfeel_scorecard") if isinstance(run.get("product_readfeel_scorecard"), Mapping) else {},
        runtime_surface_blind_qa_long_run_summary=run.get("runtime_surface_blind_qa_long_run_summary") if isinstance(run.get("runtime_surface_blind_qa_long_run_summary"), Mapping) else {},
        user_label_connection_qa_summary=run.get("user_label_connection_qa_summary") if isinstance(run.get("user_label_connection_qa_summary"), Mapping) else {},
        phase11_long_run_product_gate=run.get("phase11_long_run_product_gate") if isinstance(run.get("phase11_long_run_product_gate"), Mapping) else {},
    )

def assert_product_quality_blocker_matrix_row_meta_only(row: Mapping[str, Any]) -> None:
    if not isinstance(row, Mapping):
        raise ValueError("blocker matrix row must be a mapping")
    extra = set(row.keys()) - set(_ALLOWED_ROW_KEYS)
    if extra:
        raise ValueError(f"blocker matrix row contains unsupported keys: {sorted(extra)}")
    if row.get("schema_version") != PRODUCT_QUALITY_BLOCKER_MATRIX_ROW_VERSION:
        raise ValueError("blocker matrix row has invalid schema_version")
    if not _clean(row.get("blocker_id")):
        raise ValueError("blocker matrix row requires blocker_id")
    if not _clean(row.get("likely_owner_area")):
        raise ValueError("blocker matrix row requires likely_owner_area")
    if not _clean(row.get("repair_policy")):
        raise ValueError("blocker matrix row requires repair_policy")
    for key in ("contract_change_allowed", "public_contract_change_allowed", "gate_relaxation_allowed", "fixed_template_allowed", "runtime_fixture_branch_allowed", "product_gate_ready", "public_release_applied", "raw_input_included", "comment_text_body_included", "candidate_body_included"):
        if row.get(key) is not False:
            raise ValueError(f"blocker matrix row {key} must be false")
    if _contains_text_payload_key(row):
        raise ValueError("blocker matrix row contains a forbidden text payload key")
    flag_path = _forbidden_true_flag_path(row, path="blocker_matrix_row")
    if flag_path:
        raise ValueError(f"blocker matrix row marks forbidden flag true at {flag_path}")
    assert_emlis_ai_product_quality_contract_freeze_meta_only(row, source="emlis_ai_product_quality_blocker_matrix_row")

def assert_product_quality_blocker_matrix_meta_only(matrix: Mapping[str, Any]) -> None:
    if not isinstance(matrix, Mapping):
        raise ValueError("blocker matrix must be a mapping")
    extra = set(matrix.keys()) - set(_ALLOWED_MATRIX_KEYS)
    if extra:
        raise ValueError(f"blocker matrix contains unsupported keys: {sorted(extra)}")
    if matrix.get("schema_version") != PRODUCT_QUALITY_BLOCKER_MATRIX_VERSION:
        raise ValueError("blocker matrix has invalid schema_version")
    if matrix.get("product_gate_ready") is not False:
        raise ValueError("blocker matrix must keep product_gate_ready false")
    if matrix.get("public_release_applied") is not False:
        raise ValueError("blocker matrix must keep public_release_applied false")
    for row in matrix.get("rows") or []:
        assert_product_quality_blocker_matrix_row_meta_only(row)
    if matrix.get("repair_work_queue") != matrix.get("rows"):
        raise ValueError("repair_work_queue must mirror rows in Phase 4")
    if matrix.get("repair_queue") != matrix.get("rows"):
        raise ValueError("repair_queue must mirror rows in Phase 4")
    if matrix.get("all_release_blockers_have_owner_area_and_repair_policy") is not True:
        raise ValueError("all release blockers must have owner_area and repair_policy")
    for key in ("gate_relaxation_required", "fixed_template_required", "runtime_fixture_branch_required"):
        if matrix.get(key) is not False:
            raise ValueError(f"blocker matrix {key} must be false")
    if _contains_text_payload_key(matrix):
        raise ValueError("blocker matrix contains a forbidden text payload key")
    flag_path = _forbidden_true_flag_path(matrix, path="blocker_matrix")
    if flag_path:
        raise ValueError(f"blocker matrix marks forbidden flag true at {flag_path}")
    assert_emlis_ai_product_quality_contract_freeze_meta_only(matrix, source="emlis_ai_product_quality_blocker_matrix")

def dump_product_quality_blocker_matrix(matrix: Mapping[str, Any]) -> str:
    assert_product_quality_blocker_matrix_meta_only(matrix)
    return json.dumps(matrix, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

__all__ = [
    "PRODUCT_QUALITY_BLOCKER_MATRIX_PHASE",
    "PRODUCT_QUALITY_BLOCKER_MATRIX_ROW_SCHEMA_VERSION",
    "PRODUCT_QUALITY_BLOCKER_MATRIX_ROW_VERSION",
    "PRODUCT_QUALITY_BLOCKER_MATRIX_SCHEMA_VERSION",
    "PRODUCT_QUALITY_BLOCKER_MATRIX_TARGET_STEP",
    "PRODUCT_QUALITY_BLOCKER_MATRIX_VERSION",
    "assert_product_quality_blocker_matrix_meta_only",
    "assert_product_quality_blocker_matrix_row_meta_only",
    "build_product_quality_blocker_matrix",
    "build_product_quality_blocker_matrix_from_measurement_run",
    "classify_product_quality_blocker",
    "dump_product_quality_blocker_matrix",
]
