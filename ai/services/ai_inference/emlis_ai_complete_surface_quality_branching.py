# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step5 RuntimeSurfaceQuality Branch Resolver for EmlisAI.

This resolver converts the meta-only results from Step1 source lock, Step2
surface signature, Step3 scorecard surface metrics, and Step4 coverage runtime
baseline into the next implementation branch.  It does not repair text, does
not generate observation sentences, and never relaxes RN/API/DB/Gate contracts.
"""

import json
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

RUNTIME_SURFACE_QUALITY_BRANCHING_VERSION = "emlis.runtime_surface_quality_branching.v1"
RUNTIME_SURFACE_QUALITY_BRANCHING_STEP = "Step5_RuntimeSurfaceQuality_Branch_Resolver"
RUNTIME_SURFACE_QUALITY_BRANCHING_SOURCE = "emlis_runtime_surface_quality_step5_branch_resolver"
RUNTIME_SURFACE_QUALITY_PRODUCT_GATE_READ_FEELING_TARGET = 0.90
RUNTIME_SURFACE_QUALITY_BINDING_TARGET = 0.98

_FORBIDDEN_TEXT_PAYLOAD_KEYS = {
    "raw_input",
    "rawInput",
    "raw_text",
    "rawText",
    "source_text",
    "sourceText",
    "input",
    "input_text",
    "inputText",
    "user_input",
    "userInput",
    "memo",
    "memo_text",
    "memoText",
    "current_input",
    "currentInput",
    "comment_text",
    "commentText",
    "input_feedback_comment",
    "inputFeedbackComment",
    "public_comment_text",
    "candidate_comment_text",
    "reply_text",
    "replyText",
    "surface_text",
    "realized_text",
    "body",
    "text",
}

_CONTRACT_TRUE_FLAGS = (
    "raw_input_included",
    "raw_text_included",
    "comment_text_included",
    "comment_text_body_included",
    "response_shape_changed",
    "public_response_key_change",
    "api_route_changed",
    "db_physical_name_changed",
    "rn_visible_contract_changed",
    "rn_visible_title_changed",
    "display_gate_relaxed",
    "grounding_gate_relaxed",
    "template_gate_relaxed",
    "reader_gate_relaxed",
    "gate_relaxed",
    "public_release_applied",
    "product_gate_public_release_applied",
    "product_quality_released",
    "product_gate_achieved",
    "product_gate_reached",
    "fixed_sentence_template_used",
    "fixed_fallback_used",
    "input_specific_template_added",
    "fixed_completed_sentence_template_added",
    "external_ai_used",
    "local_llm_used",
    "fixture_text_used_for_runtime_branching",
    "runtime_branching_uses_fixture_strings",
)

_DIAGNOSTIC_MARKERS = {
    "measurement_rows_missing",
    "diagnostic_log_missing_or_not_captured",
    "backend_diagnostic_missing_or_not_captured",
    "frontend_diagnostic_missing_or_not_captured",
    "unknown_diagnostic_missing",
    "unclassified_non_display",
    "reason_missing",
    "reason_coverage_missing",
    "reason_coverage_incomplete",
    "reason_coverage_below_target",
    "reason_coverage_rate_below_target",
    "runtime_surface_source_lock_missing",
    "runtime_composer_source_unknown",
}

_COMPLETE_RUNTIME_SOURCES = {"complete_initial", "complete_composer_initial"}
_NON_COMPLETE_RUNTIME_SOURCES = {
    "limited",
    "a1_equivalent",
    "a_plan_equivalent",
    "unavailable",
    "legacy_limited",
    "limited_composer",
}
_UNKNOWN_RUNTIME_SOURCES = {"", "unknown", "missing", "none", "null", "unclassified"}

_GROUNDING_MARKERS = {
    "binding_pass_rate_below_target",
    "binding_target_not_met",
    "binding_contract_unresolved",
    "unsupported_sentence",
    "grounding:unsupported_sentence",
    "grounding_relation_binding_repair",
    "relation_binding_missing",
    "relation_not_expressed",
    "sentence_binding_missing",
    "candidate_generated_but_grounding_rejected",
}
_GRAMMAR_MARKERS = {
    "grammar_warning",
    "surface_grammar_warning",
    "coverage_grammar_warning_detected",
    "malformed_nominalization",
    "malformed_nominalization_risk",
    "stem_koto_hanareru",
    "particle_leftover",
    "unfinished_phrase",
    "phrase_unit_grammar",
}
_SURFACE_MARKERS = {
    "template_major_detected",
    "surface_template_major_detected",
    "template_major",
    "surface_signature_repeat_detected",
    "coverage_surface_signature_repeat_detected",
    "surface_connector_repetition",
    "connector_repetition",
    "predicate_family_repetition",
    "same_ending_family",
    "ending_repetition",
    "generic_center_phrase",
    "raw_echo",
    "raw_echo_risk",
    "fixed_sentence",
    "fixed_template",
    "candidate_generated_but_template_rejected",
}
_TONE_MARKERS = {
    "read_feeling_score_below_connection_target",
    "read_feeling_score_below_broader_target",
    "read_feeling_score_below_product_gate_target",
    "distance_score_below_target",
    "naturalness_score_below_target",
    "tone_distance_low",
    "blind_qa_read_feeling_low",
}
_QA_MISSING_MARKERS = {
    "blind_qa_missing",
    "blind_qa_not_evaluated",
    "blind_qa_required",
    "long_run_missing",
    "qa_missing",
}

_BRANCH_TABLE: dict[str, dict[str, Any]] = {
    "contract_blocker": {
        "priority": 1,
        "target_layer": "contract_blocker",
        "target_area": "contract inventory / forbidden key guard",
        "next_work_name": "Runtime Surface Quality contract blocker cleanup",
        "next_work_summary": "raw/comment本文混入、Gate緩和、public契約変更などを先に戻す。Surface/Tone修正へ進まない。",
        "touch_files": [
            "emlis_ai_runtime_surface_quality_contract_inventory.py",
            "emlis_ai_complete_product_quality_measurement_connection.py",
            "forbidden-key guards",
        ],
        "do_not_touch": ["Surface Realizer", "Tone Engine", "RN表示条件", "Gate緩和", "public release"],
        "forbidden_actions": ["contract違反を文章修正で隠す", "Gateを緩める", "public response keyを変える"],
        "required_evidence": ["contract violation flag or forbidden text payload key detected"],
        "test_focus": ["forbidden payload is not serialized", "RN/API/DB/Gate contracts stay unchanged"],
        "exit_condition": "meta-only契約違反が消え、Step5入力を安全に再評価できる。",
        "repair_allowed": False,
        "requires_diagnostic_enrichment": False,
        "terminal": False,
    },
    "diagnostic_enrichment": {
        "priority": 2,
        "target_layer": "diagnostic_enrichment",
        "target_area": "diagnostic capture / join semantics / source lock completion",
        "next_work_name": "Runtime Surface diagnostic enrichment",
        "next_work_summary": "原因未分類または診断欠落のため、SurfaceやToneへ飛ばず、diagnostic capture / join / source lockを補う。",
        "touch_files": [
            "emlis_ai_complete_reply_diagnostics_service.py",
            "emlis_ai_complete_product_quality_measurement_connection.py",
            "emlis_ai_runtime_surface_source_lock.py",
        ],
        "do_not_touch": ["Surface Realizer", "Tone Engine", "SelfRepair", "RN表示条件", "fixed observation sentence"],
        "forbidden_actions": ["原因未分類のまま修正層を決める", "unknownをSurface/Tone問題に決め打ちする"],
        "required_evidence": ["diagnostic_missing / unknown / unclassified or source lock missing"],
        "test_focus": ["unknown_diagnostic_missing keeps repair_allowed false", "diagnostic rows stay meta-only"],
        "exit_condition": "classification、composer_source、coverage、surface metricsの欠落がなくなり、次層へ分岐できる。",
        "repair_allowed": False,
        "requires_diagnostic_enrichment": True,
        "terminal": False,
    },
    "complete_runtime_activation": {
        "priority": 3,
        "target_layer": "complete_runtime_activation",
        "target_area": "composer registry / AP0 / rollout / reply_service source resolution",
        "next_work_name": "Complete Runtime Activation Branch",
        "next_work_summary": "実表示文がcomplete_initial由来ではないため、Surface修正より先にComplete runtime接続を固定する。",
        "touch_files": [
            "emlis_ai_composer_client_registry.py",
            "emlis_ai_reply_service.py",
            "emlis_ai_ap0_migration_decision_service.py",
        ],
        "do_not_touch": ["Surface Realizer", "Tone Engine", "RN表示条件", "Gate緩和", "fixed sentence"],
        "forbidden_actions": ["limited/A1由来の表示をSurface修正対象にする", "complete専用のRN表示分岐を足す"],
        "required_evidence": ["composer_source is limited / a1_equivalent / unavailable"],
        "test_focus": ["complete_initial requested/resolved/source lock meta", "AP0 red path remains fail-closed"],
        "exit_condition": "eligible submitでcomplete_initial由来の表示文を測れる。",
        "repair_allowed": True,
        "requires_diagnostic_enrichment": False,
        "terminal": False,
    },
    "grounding_relation_binding_repair": {
        "priority": 4,
        "target_layer": "grounding_relation_binding_repair",
        "target_area": "grounding / relation / sentence binding",
        "next_work_name": "Grounding / relation binding repair",
        "next_work_summary": "bindingやunsupported_sentenceが先に詰まっているため、Gateを緩めず根拠・relation束縛へ戻す。",
        "touch_files": [
            "emlis_ai_complete_grounding_binding.py",
            "emlis_ai_complete_grounding_service.py",
            "emlis_ai_complete_sentence_planner.py",
            "relation binding meta",
        ],
        "do_not_touch": ["Gate緩和", "Surfaceだけの修正", "Tone Engine", "固定完成文"],
        "forbidden_actions": ["unsupported_sentenceを無視して通す", "根拠なし補完で自然に見せる"],
        "required_evidence": ["binding_pass_rate below target or unsupported/relation binding reason"],
        "test_focus": ["each displayed sentence traces to evidence / phrase / relation", "unsupported_sentence remains blocker"],
        "exit_condition": "binding_pass_rateが候補水準へ戻り、unsupported/relation不足が消える。",
        "repair_allowed": True,
        "requires_diagnostic_enrichment": False,
        "terminal": False,
    },
    "phrase_unit_grammar_normalizer": {
        "priority": 5,
        "target_layer": "phrase_unit_grammar_normalizer",
        "target_area": "material / phrase shaping / grammar guard",
        "next_work_name": "PhraseUnit Grammar Normalizer",
        "next_work_summary": "文法崩れや不自然な名詞化が見えているため、Surfaceで隠さず材料段階のPhraseUnit整形へ戻す。",
        "touch_files": [
            "emlis_ai_complete_material_service.py",
            "emlis_ai_phrase_shaping_service.py",
            "emlis_ai_complete_surface_quality_signature.py",
        ],
        "do_not_touch": ["根拠なし補完", "完成文テンプレ追加", "Tone Engine", "Gate緩和"],
        "forbidden_actions": ["文法崩れを固定文で覆う", "must_keep材料を勝手に落とす"],
        "required_evidence": ["grammar_warning_major or malformed_nominalization_risk"],
        "test_focus": ["離れこと系をwarning/repair対象にする", "PhraseUnit drop does not drop must_keep"],
        "exit_condition": "不自然な名詞化・助詞残り・未完了句が重大表示されない。",
        "repair_allowed": True,
        "requires_diagnostic_enrichment": False,
        "terminal": False,
    },
    "surface_realizer_2_1_anti_template": {
        "priority": 6,
        "target_layer": "surface_realizer_2_1_anti_template",
        "target_area": "surface realizer / sentence plan / relation surface",
        "next_work_name": "Surface Realizer 2.1 Anti-Template",
        "next_work_summary": "complete_initial由来かつsurface/template反復が出ているため、完成文定数を増やさず表層生成を分散する。",
        "touch_files": [
            "emlis_ai_complete_surface_realizer.py",
            "emlis_ai_complete_sentence_planner.py",
            "emlis_ai_relation_surface_contract.py",
        ],
        "do_not_touch": ["固定完成文テンプレ追加", "入力専用分岐", "Gate緩和", "RN表示条件"],
        "forbidden_actions": ["固定文を増やして自然に見せる", "fixture文字列をruntime分岐に使う"],
        "required_evidence": ["template_major or signature/connector/predicate/ending repetition"],
        "test_focus": ["surface_signature_repeat_rate decreases", "binding/safety gates remain unchanged"],
        "exit_condition": "テンプレ重大検出と過剰反復が消え、bindingとsafetyを維持する。",
        "repair_allowed": True,
        "requires_diagnostic_enrichment": False,
        "terminal": False,
    },
    "tone_engine_2_1_blind_qa": {
        "priority": 7,
        "target_layer": "tone_engine_2_1_blind_qa",
        "target_area": "tone policy / final review / blind QA rubric",
        "next_work_name": "Tone Engine 2.1 Blind QA branch",
        "next_work_summary": "machine metricsは候補水準だがBlind QAの読まれた感・距離感が低いため、Tone Engineへ進む。",
        "touch_files": [
            "emlis_ai_complete_tone_policy.py",
            "emlis_ai_reply_final_review_service.py",
            "emlis_ai_complete_product_quality_scorecard_service.py",
        ],
        "do_not_touch": ["機械metricsだけで読まれた感を推定", "Surface問題に決め打ち", "診断化", "命令・一般論化"],
        "forbidden_actions": ["Blind QAなしでTone完了扱いにする", "慰めテンプレを増やす"],
        "required_evidence": ["machine metrics good and Blind QA read_feeling/distance below target"],
        "test_focus": ["Blind QA rating and machine metrics stay separated", "diagnosis/advice/personality claim stays blocked"],
        "exit_condition": "Blind QAでread_feeling/distance/naturalnessが候補水準へ近づく。",
        "repair_allowed": True,
        "requires_diagnostic_enrichment": False,
        "terminal": False,
    },
    "blind_qa_long_run": {
        "priority": 8,
        "target_layer": "blind_qa_long_run",
        "target_area": "Blind QA / long-run / scorecard continuation",
        "next_work_name": "Blind QA / Long-run handoff",
        "next_work_summary": "runtime/surface/grammar/groundingの主要blockerは見えていないため、Blind QAとLong-runで商品品質候補を確認する。",
        "touch_files": [
            "emlis_ai_complete_product_quality_scorecard_service.py",
            "emlis_ai_long_term_quality_service.py",
            "blind QA review records",
        ],
        "do_not_touch": ["public release即適用", "Product Gate達成宣言", "RN表示条件", "Gate緩和"],
        "forbidden_actions": ["Blind QAなしでProduct Gate readyにする", "public releaseを即適用する"],
        "required_evidence": ["all machine metrics candidate-level and QA/long-run is remaining"],
        "test_focus": ["blind QA missing remains release blocker", "long-run surface diversity is measured"],
        "exit_condition": "読まれた感・非テンプレ性・安全性のQA材料が揃い、Product Gate候補判定に進める。",
        "repair_allowed": False,
        "requires_diagnostic_enrichment": False,
        "terminal": True,
    },
}

_TARGETS = tuple(_BRANCH_TABLE)


def _clean(value: Any) -> str:
    if value is None or isinstance(value, (Mapping, list, tuple, set)):
        return ""
    return str(value).strip()


def _safe_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    return {}


def _listify(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    if isinstance(value, (tuple, set)):
        return list(value)
    return [value]


def _dedupe(values: Iterable[Any] | Any) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in _listify(values):
        text = _clean(value)
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        if isinstance(value, bool):
            return int(value)
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value is None or value == "":
            return default
        if isinstance(value, bool):
            return float(int(value))
        return float(value)
    except (TypeError, ValueError):
        return default


def _contains_forbidden_text_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key) in _FORBIDDEN_TEXT_PAYLOAD_KEYS:
                return True
            if _contains_forbidden_text_payload_key(item):
                return True
        return False
    if isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_text_payload_key(item) for item in value)
    return False


def assert_runtime_surface_quality_branch_meta_only(
    value: Mapping[str, Any],
    *,
    source: str = "runtime_surface_quality_branch",
) -> None:
    """Validate a branch output.  Raw/comment bodies are never allowed."""

    if _contains_forbidden_text_payload_key(value):
        raise ValueError(f"{source} must stay meta-only and must not include text payload keys")
    if value.get("raw_input_included") is True or value.get("raw_text_included") is True:
        raise ValueError(f"{source} must not include raw input")
    if value.get("comment_text_included") is True or value.get("comment_text_body_included") is True:
        raise ValueError(f"{source} must not include public comment text body")


def _contract_violations(value: Any, *, prefix: str = "") -> list[str]:
    violations: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            dotted = f"{prefix}.{key_text}" if prefix else key_text
            if key_text in _FORBIDDEN_TEXT_PAYLOAD_KEYS:
                violations.append(f"forbidden_text_payload_key:{dotted}")
                continue
            if key_text in _CONTRACT_TRUE_FLAGS and item is True:
                violations.append(f"contract_flag_true:{dotted}")
            violations.extend(_contract_violations(item, prefix=dotted))
    elif isinstance(value, (list, tuple, set)):
        for index, item in enumerate(value):
            violations.extend(_contract_violations(item, prefix=f"{prefix}[{index}]"))
    return _dedupe(violations)


def _nested_mapping(*sources: Any) -> dict[str, Any]:
    for source in sources:
        data = _safe_mapping(source)
        if data:
            return data
    return {}


def _source_maps(source: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    scorecard = _nested_mapping(source.get("scorecard"), source.get("product_quality_scorecard"))
    machine = _nested_mapping(scorecard.get("machine_metrics"), source.get("machine_metrics"))
    coverage_baseline = _nested_mapping(
        source.get("coverage_runtime_baseline"),
        scorecard.get("coverage_runtime_baseline"),
        machine.get("coverage_runtime_baseline"),
    )
    next_action_branch = _nested_mapping(source.get("next_action_branch"), source.get("next_branch"), source.get("next_action"))
    events = [dict(_safe_mapping(item)) for item in _listify(source.get("scorecard_events") or source.get("events")) if _safe_mapping(item)]
    return scorecard, machine, coverage_baseline, next_action_branch, events


def _collect_reasons(source: Mapping[str, Any]) -> list[str]:
    scorecard, machine, coverage_baseline, next_action_branch, events = _source_maps(source)
    capture_summary = _safe_mapping(source.get("capture_summary"))
    release_ladder = _safe_mapping(source.get("release_ladder"))
    reasons: list[str] = []
    for container in (source, scorecard, machine, coverage_baseline, next_action_branch, capture_summary, release_ladder):
        for key in (
            "release_blockers",
            "ladder_blockers",
            "top_rejection_reasons",
            "surface_major_reasons",
            "surface_grammar_warning_codes",
            "grammar_warning_codes",
            "capture_blockers",
            "display_count_blockers",
            "coverage_runtime_baseline_release_blockers",
            "groups_needing_attention",
            "coverage_runtime_baseline_groups_needing_attention",
            "release_blockers_considered",
            "top_rejection_reasons_considered",
        ):
            reasons.extend(_dedupe(container.get(key)))
        for key in (
            "classification",
            "next_action_classification",
            "selected_classification",
            "selected_release_blocker",
            "selected_top_rejection_reason",
            "target_layer",
            "diagnostic_capture_status",
            "backend_diagnostic_capture_status",
            "frontend_diagnostic_capture_status",
            "routing_basis",
        ):
            text = _clean(container.get(key))
            if text:
                reasons.append(text)
    for row in _listify(source.get("coverage_runtime_baseline_rows") or coverage_baseline.get("coverage_group_rows")):
        row_map = _safe_mapping(row)
        reasons.extend(_dedupe(row_map.get("top_rejection_reasons")))
        reasons.extend(_dedupe(row_map.get("surface_major_reasons")))
        reasons.extend(_dedupe(row_map.get("surface_grammar_warning_codes")))
    for event in events:
        reasons.extend(_dedupe(event.get("top_rejection_reasons")))
        reasons.extend(_dedupe(event.get("surface_major_reasons")))
        reasons.extend(_dedupe(event.get("surface_grammar_warning_codes") or event.get("grammar_warning_codes")))
        for key in ("classification", "measurement_classification", "observation_status"):
            text = _clean(event.get(key))
            if text:
                reasons.append(text)
    return _dedupe(reasons)


def _has_marker(values: Sequence[str], markers: set[str]) -> bool:
    for value in values:
        lower_value = value.lower()
        for marker in markers:
            marker_lower = marker.lower()
            if lower_value == marker_lower or marker_lower in lower_value:
                return True
    return False


def _first_marker(values: Sequence[str], markers: set[str]) -> str:
    for value in values:
        lower_value = value.lower()
        for marker in markers:
            marker_lower = marker.lower()
            if lower_value == marker_lower or marker_lower in lower_value:
                return value
    return ""


def _all_runtime_composer_sources(source: Mapping[str, Any]) -> list[str]:
    scorecard, machine, coverage_baseline, next_action_branch, events = _source_maps(source)
    sources: list[str] = []
    containers: list[Mapping[str, Any]] = [source, scorecard, machine, coverage_baseline, next_action_branch]
    containers.extend(events)
    source_keys = (
        "runtime_composer_source",
        "runtime_surface_composer_source",
        "runtime_surface_source_composer_source",
        "step1_composer_source",
    )
    fallback_keys = ("composer_source", "composer_resolved")
    requested_keys = ("composer_requested", "requested_composer")
    known_runtime_values = _COMPLETE_RUNTIME_SOURCES | _NON_COMPLETE_RUNTIME_SOURCES | _UNKNOWN_RUNTIME_SOURCES
    for container in containers:
        lock = _safe_mapping(container.get("runtime_surface_source_lock") or container.get("step1_runtime_surface_source_lock"))
        for key in source_keys:
            sources.append(_clean(container.get(key)).lower())
            sources.append(_clean(lock.get(key)).lower())
        for key in fallback_keys:
            lock_value = _clean(lock.get(key)).lower()
            if lock_value:
                sources.append(lock_value)
            container_value = _clean(container.get(key)).lower()
            if container_value in known_runtime_values:
                sources.append(container_value)
        if not sources:
            for key in requested_keys:
                requested = _clean(lock.get(key) or container.get(key)).lower()
                if requested in known_runtime_values:
                    sources.append(requested)
    return _dedupe([item for item in sources if item])


def _metric(source: Mapping[str, Any], key: str, default: float | None = None) -> float | None:
    scorecard, machine, coverage_baseline, _next_action_branch, _events = _source_maps(source)
    for container in (source, scorecard, machine, coverage_baseline):
        if key in container:
            return _safe_float(container.get(key), default)
    return default


def _int_metric(source: Mapping[str, Any], key: str, default: int = 0) -> int:
    scorecard, machine, coverage_baseline, _next_action_branch, _events = _source_maps(source)
    for container in (source, scorecard, machine, coverage_baseline):
        if key in container:
            return _safe_int(container.get(key), default)
    return default


def _bool_metric(source: Mapping[str, Any], key: str, default: bool = False) -> bool:
    scorecard, machine, coverage_baseline, next_action_branch, _events = _source_maps(source)
    for container in (source, scorecard, machine, coverage_baseline, next_action_branch):
        if key in container:
            return bool(container.get(key))
    return default


def _blind_qa_ready(source: Mapping[str, Any]) -> bool:
    scorecard, machine, _coverage_baseline, _next_action_branch, _events = _source_maps(source)
    blind_qa = _safe_mapping(scorecard.get("blind_qa_metrics") or source.get("blind_qa_metrics"))
    return bool(
        source.get("blind_qa_ready")
        or scorecard.get("blind_qa_ready")
        or machine.get("blind_qa_ready")
        or blind_qa.get("blind_qa_ready")
    )


def _read_feeling_score(source: Mapping[str, Any]) -> float | None:
    scorecard, machine, _coverage_baseline, _next_action_branch, _events = _source_maps(source)
    blind_qa = _safe_mapping(scorecard.get("blind_qa_metrics") or source.get("blind_qa_metrics"))
    for container in (source, scorecard, blind_qa):
        score = _safe_float(container.get("read_feeling_score"))
        if score is not None:
            return score
    # Machine metrics are deliberately ignored for read feeling.
    _ = machine
    return None


def _metrics_snapshot(source: Mapping[str, Any]) -> dict[str, Any]:
    scorecard, machine, coverage_baseline, _next_action_branch, _events = _source_maps(source)
    read_feeling_score = _read_feeling_score(source)
    return {
        "display_reach_rate": _metric(source, "display_reach_rate", 0.0) or 0.0,
        "binding_pass_rate": _metric(source, "binding_pass_rate", 0.0) or 0.0,
        "reason_coverage_rate": _metric(source, "reason_coverage_rate", 0.0) or 0.0,
        "surface_signature_repeat_rate": _metric(source, "surface_signature_repeat_rate", 0.0) or 0.0,
        "connector_repetition_rate": _metric(source, "connector_repetition_rate", 0.0) or 0.0,
        "predicate_family_repetition_rate": _metric(source, "predicate_family_repetition_rate", 0.0) or 0.0,
        "ending_repetition_rate": _metric(source, "ending_repetition_rate", 0.0) or 0.0,
        "generic_opening_rate": _metric(source, "generic_opening_rate", 0.0) or 0.0,
        "grammar_warning_rate": _metric(source, "grammar_warning_rate", 0.0) or 0.0,
        "coverage_surface_diversity_rate": _metric(source, "coverage_surface_diversity_rate", 0.0) or 0.0,
        "template_major_count": _int_metric(source, "template_major_count", 0),
        "surface_template_major_count": _int_metric(source, "surface_template_major_count", 0),
        "surface_signature_repeat_count": _int_metric(source, "surface_signature_repeat_count", 0),
        "surface_grammar_warning_count": _int_metric(source, "surface_grammar_warning_count", 0),
        "safety_major_count": _int_metric(source, "safety_major_count", 0),
        "coverage_group_missing_count": _int_metric(source, "coverage_group_missing_count", 0),
        "blind_qa_ready": _blind_qa_ready(source),
        "blind_qa_missing": bool(
            source.get("blind_qa_missing")
            or scorecard.get("blind_qa_missing")
            or machine.get("blind_qa_missing")
            or "blind_qa_missing" in _dedupe(scorecard.get("release_blockers"))
        ),
        "read_feeling_score": read_feeling_score,
        "read_feeling_source": _clean(source.get("read_feeling_source") or scorecard.get("read_feeling_source")),
        "coverage_runtime_baseline_ready": bool(coverage_baseline.get("coverage_runtime_baseline_ready")),
    }


def _machine_metrics_good_before_tone_or_qa(snapshot: Mapping[str, Any], reasons: Sequence[str]) -> bool:
    if _has_marker(reasons, _GROUNDING_MARKERS | _GRAMMAR_MARKERS | _SURFACE_MARKERS):
        return False
    if _safe_int(snapshot.get("safety_major_count"), 0) > 0:
        return False
    if _safe_int(snapshot.get("template_major_count"), 0) > 0 or _safe_int(snapshot.get("surface_template_major_count"), 0) > 0:
        return False
    if _safe_int(snapshot.get("surface_signature_repeat_count"), 0) > 0:
        return False
    for key in (
        "surface_signature_repeat_rate",
        "connector_repetition_rate",
        "predicate_family_repetition_rate",
        "ending_repetition_rate",
        "grammar_warning_rate",
    ):
        if float(snapshot.get(key) or 0.0) > 0:
            return False
    binding_rate = float(snapshot.get("binding_pass_rate") or 0.0)
    return binding_rate >= RUNTIME_SURFACE_QUALITY_BINDING_TARGET or binding_rate == 0.0


def _select_branch_key(source: Mapping[str, Any]) -> tuple[str, str, list[str], dict[str, Any]]:
    contract_violations = _contract_violations(source)
    reasons = _collect_reasons(source)
    snapshot = _metrics_snapshot(source)
    composer_sources = _all_runtime_composer_sources(source)
    selected_reason = ""

    if contract_violations:
        return "contract_blocker", contract_violations[0], contract_violations, snapshot

    if (
        _has_marker(reasons, _DIAGNOSTIC_MARKERS)
        or _bool_metric(source, "requires_diagnostic_enrichment", False)
        or _clean(source.get("diagnostic_capture_status")) in _DIAGNOSTIC_MARKERS
        or _int_metric(source, "event_count", 1) == 0
    ):
        selected_reason = _first_marker(reasons, _DIAGNOSTIC_MARKERS) or "diagnostic_missing_or_unclassified"
        return "diagnostic_enrichment", selected_reason, reasons, snapshot

    if not composer_sources:
        return "diagnostic_enrichment", "runtime_surface_source_lock_missing", reasons, snapshot
    normalized_sources = {source_name.lower() for source_name in composer_sources}
    if normalized_sources & _UNKNOWN_RUNTIME_SOURCES:
        return "diagnostic_enrichment", "runtime_composer_source_unknown", reasons, snapshot
    if normalized_sources & _NON_COMPLETE_RUNTIME_SOURCES or not normalized_sources <= _COMPLETE_RUNTIME_SOURCES:
        non_complete_source = next((name for name in composer_sources if name.lower() not in _COMPLETE_RUNTIME_SOURCES), "not_complete_initial")
        selected_reason = f"composer_source:{non_complete_source}"
        return "complete_runtime_activation", selected_reason, reasons, snapshot

    binding_rate = float(snapshot.get("binding_pass_rate") or 0.0)
    if (
        _has_marker(reasons, _GROUNDING_MARKERS)
        or (binding_rate > 0.0 and binding_rate < RUNTIME_SURFACE_QUALITY_BINDING_TARGET)
    ):
        selected_reason = _first_marker(reasons, _GROUNDING_MARKERS) or "binding_pass_rate_below_target"
        return "grounding_relation_binding_repair", selected_reason, reasons, snapshot

    if (
        _has_marker(reasons, _GRAMMAR_MARKERS)
        or float(snapshot.get("grammar_warning_rate") or 0.0) > 0.0
        or _safe_int(snapshot.get("surface_grammar_warning_count"), 0) > 0
    ):
        selected_reason = _first_marker(reasons, _GRAMMAR_MARKERS) or "grammar_warning_major"
        return "phrase_unit_grammar_normalizer", selected_reason, reasons, snapshot

    if (
        _has_marker(reasons, _SURFACE_MARKERS)
        or _safe_int(snapshot.get("template_major_count"), 0) > 0
        or _safe_int(snapshot.get("surface_template_major_count"), 0) > 0
        or _safe_int(snapshot.get("surface_signature_repeat_count"), 0) > 0
        or float(snapshot.get("surface_signature_repeat_rate") or 0.0) > 0.0
        or float(snapshot.get("connector_repetition_rate") or 0.0) > 0.0
        or float(snapshot.get("predicate_family_repetition_rate") or 0.0) > 0.0
        or float(snapshot.get("ending_repetition_rate") or 0.0) > 0.0
        or float(snapshot.get("generic_opening_rate") or 0.0) > 0.0
    ):
        selected_reason = _first_marker(reasons, _SURFACE_MARKERS) or "surface_signature_or_template_repetition"
        return "surface_realizer_2_1_anti_template", selected_reason, reasons, snapshot

    blind_qa_ready = bool(snapshot.get("blind_qa_ready"))
    read_feeling_score = snapshot.get("read_feeling_score")
    machine_good = _machine_metrics_good_before_tone_or_qa(snapshot, reasons)
    if (
        machine_good
        and blind_qa_ready
        and read_feeling_score is not None
        and float(read_feeling_score) < RUNTIME_SURFACE_QUALITY_PRODUCT_GATE_READ_FEELING_TARGET
    ):
        selected_reason = _first_marker(reasons, _TONE_MARKERS) or "blind_qa_read_feeling_below_target"
        return "tone_engine_2_1_blind_qa", selected_reason, reasons, snapshot

    if machine_good and (not blind_qa_ready or _has_marker(reasons, _QA_MISSING_MARKERS)):
        selected_reason = _first_marker(reasons, _QA_MISSING_MARKERS) or "blind_qa_or_long_run_required"
        return "blind_qa_long_run", selected_reason, reasons, snapshot

    if _safe_int(snapshot.get("safety_major_count"), 0) > 0:
        return "diagnostic_enrichment", "safety_major_detected_needs_overclaim_diagnostic", reasons, snapshot

    return "blind_qa_long_run", "no_runtime_surface_blocker_detected", reasons, snapshot


def known_runtime_surface_quality_branch_targets() -> tuple[str, ...]:
    return _TARGETS


def resolve_runtime_surface_quality_branch(report: Mapping[str, Any] | None = None, **kwargs: Any) -> dict[str, Any]:
    """Resolve the next Step5 target from meta-only scorecard/baseline data."""

    source = dict(report or {})
    if kwargs:
        source.update(kwargs)
    branch_key, selected_reason, reasons, snapshot = _select_branch_key(source)
    table = dict(_BRANCH_TABLE[branch_key])
    priority = int(table["priority"])
    branch_locked = branch_key not in {"contract_blocker", "diagnostic_enrichment"}
    repair_allowed = bool(table["repair_allowed"])
    requires_diagnostic_enrichment = bool(table["requires_diagnostic_enrichment"])
    terminal = bool(table["terminal"])
    scorecard, _machine, coverage_baseline, _next_action_branch, _events = _source_maps(source)
    composer_sources = _all_runtime_composer_sources(source)
    release_blockers = _dedupe([
        *(_dedupe(source.get("release_blockers"))),
        *(_dedupe(scorecard.get("release_blockers"))),
        *(_dedupe(coverage_baseline.get("release_blockers"))),
    ])
    groups_needing_attention = _dedupe(
        source.get("coverage_runtime_baseline_groups_needing_attention")
        or coverage_baseline.get("groups_needing_attention")
        or []
    )
    branch = {
        "version": RUNTIME_SURFACE_QUALITY_BRANCHING_VERSION,
        "source": RUNTIME_SURFACE_QUALITY_BRANCHING_SOURCE,
        "source_step": RUNTIME_SURFACE_QUALITY_BRANCHING_STEP,
        "step": RUNTIME_SURFACE_QUALITY_BRANCHING_STEP,
        "target_step": RUNTIME_SURFACE_QUALITY_BRANCHING_STEP,
        "branch_resolver_ready": True,
        "step5_branch_resolver_ready": True,
        "runtime_surface_quality_branch_resolver_ready": True,
        "step5_runtime_surface_quality_branch_resolver_ready": True,
        "runtime_surface_quality_branch_ready": True,
        "step5_runtime_surface_quality_branch_ready": True,
        "branch_key": branch_key,
        "priority": priority,
        "branch_priority": priority,
        "priority_order": list(_TARGETS),
        "selected_reason": selected_reason,
        "selected_branch_reason": selected_reason,
        "branch_reasons": _dedupe([selected_reason, *reasons])[:24],
        "release_blockers_considered": release_blockers,
        "top_rejection_reasons_considered": _dedupe(reasons)[:24],
        "composer_sources_considered": composer_sources,
        "coverage_groups_needing_attention": groups_needing_attention,
        "target_layer": table["target_layer"],
        "target_area": table["target_area"],
        "target_branch": branch_key,
        "next_work_unit": table["target_area"] if terminal else f"{table['target_area']} の次工程",
        "next_work_name": table["next_work_name"],
        "next_work_summary": table["next_work_summary"],
        "touch_files": list(table["touch_files"]),
        "touch_targets": list(table["touch_files"]),
        "do_not_touch": list(table["do_not_touch"]),
        "forbidden_actions": list(table["forbidden_actions"]),
        "required_evidence": list(table["required_evidence"]),
        "test_focus": list(table["test_focus"]),
        "exit_condition": table["exit_condition"],
        "branch_locked": branch_locked,
        "repair_allowed": repair_allowed,
        "ready_for_cause_repair": repair_allowed,
        "cause_confirmed_for_repair": repair_allowed,
        "requires_diagnostic_enrichment": requires_diagnostic_enrichment,
        "terminal": terminal,
        "classification_decided_before_cause_repair": True,
        "unknown_or_unclassified_returns_to_diagnostic_enrichment": branch_key == "diagnostic_enrichment",
        "branch_resolver_repairs_surface_text": False,
        "runtime_source_checked_before_surface_fix": True,
        "complete_initial_required_before_surface_fix": branch_key != "complete_runtime_activation",
        "surface_or_tone_jump_blocked_without_measured_issue": branch_key not in {
            "surface_realizer_2_1_anti_template",
            "tone_engine_2_1_blind_qa",
        },
        "machine_metrics_snapshot": snapshot,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_requires_blind_qa": True,
        "tone_branch_requires_blind_qa": branch_key == "tone_engine_2_1_blind_qa",
        "qa_branch_only": branch_key == "blind_qa_long_run",
        "surface_text_repaired_by_step5": False,
        "runtime_surface_quality_repair_executed_by_step5": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "fixture_text_used_for_runtime_branching": False,
        "runtime_branching_uses_fixture_strings": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "response_shape_changed": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "gate_relaxed": False,
        "product_gate_achieved": False,
        "product_gate_reached": False,
        "public_release_applied": False,
        "product_gate_public_release_applied": False,
        "product_quality_released": False,
    }
    assert_runtime_surface_quality_branch_meta_only(branch)
    return branch


def attach_runtime_surface_quality_branch(report: Mapping[str, Any]) -> dict[str, Any]:
    data = dict(report or {})
    branch = resolve_runtime_surface_quality_branch(data)
    data.update(
        {
            "runtime_surface_quality_branch_version": RUNTIME_SURFACE_QUALITY_BRANCHING_VERSION,
            "runtime_surface_quality_branch_step": RUNTIME_SURFACE_QUALITY_BRANCHING_STEP,
            "branch_resolver_ready": True,
            "step5_branch_resolver_ready": True,
            "runtime_surface_quality_branch_resolver_ready": True,
            "step5_runtime_surface_quality_branch_resolver_ready": True,
            "runtime_surface_quality_branch_ready": True,
            "step5_runtime_surface_quality_branch_ready": True,
            "surface_text_repaired_by_step5": False,
            "branch_resolver_repairs_surface_text": False,
            "runtime_surface_quality_branch": branch,
            "runtime_surface_quality_target_layer": branch.get("target_layer"),
            "runtime_surface_quality_target_area": branch.get("target_area"),
            "runtime_surface_quality_next_step": branch.get("next_work_unit"),
            "runtime_surface_quality_repair_allowed": branch.get("repair_allowed"),
            "runtime_surface_quality_requires_diagnostic_enrichment": branch.get("requires_diagnostic_enrichment"),
            "runtime_surface_quality_branch_selected_reason": branch.get("selected_reason"),
            "runtime_branching_uses_fixture_strings": False,
            "fixture_text_used_for_runtime_branching": False,
            "raw_input_included": False,
            "raw_text_included": False,
            "comment_text_included": False,
            "comment_text_body_included": False,
        }
    )
    assert_runtime_surface_quality_branch_meta_only(branch)
    return data


def dump_runtime_surface_quality_branch(branch: Mapping[str, Any]) -> str:
    data = dict(branch or {})
    data["raw_input_included"] = False
    data["raw_text_included"] = False
    data["comment_text_included"] = False
    data["comment_text_body_included"] = False
    assert_runtime_surface_quality_branch_meta_only(data)
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


build_runtime_surface_quality_branch_resolver = resolve_runtime_surface_quality_branch
build_runtime_surface_quality_branch = resolve_runtime_surface_quality_branch


__all__ = [
    "RUNTIME_SURFACE_QUALITY_BRANCHING_VERSION",
    "RUNTIME_SURFACE_QUALITY_BRANCHING_STEP",
    "RUNTIME_SURFACE_QUALITY_PRODUCT_GATE_READ_FEELING_TARGET",
    "assert_runtime_surface_quality_branch_meta_only",
    "attach_runtime_surface_quality_branch",
    "build_runtime_surface_quality_branch",
    "build_runtime_surface_quality_branch_resolver",
    "dump_runtime_surface_quality_branch",
    "known_runtime_surface_quality_branch_targets",
    "resolve_runtime_surface_quality_branch",
]
