# -*- coding: utf-8 -*-
"""Step 8 branch routing for Emlis observation diagnostics.

This module does not repair Composer, RN, Display Gate, Surface Realizer, or
Tone. It converts the Step 7 classification into one locked next-work branch
and keeps the payload meta-only.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

try:
    from emlis_ai_observation_diagnostic_lockdown import classify_observation_diagnostic
except Exception:  # pragma: no cover
    from .emlis_ai_observation_diagnostic_lockdown import classify_observation_diagnostic  # type: ignore

BRANCHING_VERSION = "emlis.observation_diagnostic_branching.v1"

_FORBIDDEN_TEXT_PAYLOAD_KEYS = {
    "raw_input", "rawInput", "input", "input_text", "inputText",
    "memo", "memo_text", "memoText", "current_input", "currentInput",
    "comment_text", "commentText", "input_feedback_comment", "inputFeedbackComment",
    "public_comment_text", "candidate_comment_text", "reply_text", "text",
}

_BRANCH_TABLE: dict[str, dict[str, Any]] = {
    "backend_exception_or_timeout": {
        "target_layer": "backend_exception_or_timeout",
        "target_area": "timeout / error / dependency",
        "next_work_name": "Backend timeout / error / dependency investigation",
        "next_work_summary": "render_emlis_ai_reply の timeout / exception / dependency 停止を先に切り分ける。",
        "touch_files": ["emotion_submit_service", "render_emlis_ai_reply dependency path", "service logs around emlis_ai_timeout_or_error"],
        "do_not_touch": ["Surface Realizer", "Tone Engine", "RN表示条件", "fixed observation sentence"],
        "forbidden_actions": ["timeout/error を固定文 fallback で隠す", "Gate を緩める"],
        "required_evidence": ["rejection_reasons contains emlis_ai_timeout_or_error or exception-path diagnostic"],
        "test_focus": ["exception path still fail-closed", "timeout/error diagnostic keeps raw input and comment_text out"],
        "exit_condition": "timeout/error/dependency reason が特定され、submit が backend診断で次層へ進むか fail-closed として説明できる。",
        "terminal": False,
        "requires_diagnostic_enrichment": False,
    },
    "pre_connection_stop": {
        "target_layer": "pre_connection",
        "target_area": "Composer connection / release / AP0 / rollout",
        "next_work_name": "Composer connection / release / AP0 / rollout fix",
        "next_work_summary": "Complete Composer 接続前に止まっているため、feature flag / rollout / AP0 / client resolution を修正する。",
        "touch_files": ["emlis_ai_composer_client_registry.py", "release_ladder", "reply_service resolution meta"],
        "do_not_touch": ["Surface Realizer", "Tone Engine", "RN表示条件", "Display Gate緩和"],
        "forbidden_actions": ["接続前停止を Surface Realizer で直そうとする", "RN 表示条件を変更する"],
        "required_evidence": ["stage is flag / rollout / scope, or composer_client_resolution.connection_status is not connected/resolved/ready"],
        "test_focus": ["pre-connection stop reason is preserved", "connected/provided client is not misclassified as pre_connection_stop"],
        "exit_condition": "composer client resolution が connected/resolved/ready になり、candidate 層以降の分類へ進む。",
        "terminal": False,
        "requires_diagnostic_enrichment": False,
    },
    "candidate_missing": {
        "target_layer": "candidate",
        "target_area": "CompleteComposerClient material / focus / relation / sentence plan",
        "next_work_name": "CompleteComposerClient material / focus / relation / sentence plan recovery",
        "next_work_summary": "候補が生成されていないため、材料化・焦点選択・relation graph・sentence plan・composer client を復旧する。",
        "touch_files": ["complete_material", "focus_selector", "relation_graph", "sentence_planner", "composer_client"],
        "do_not_touch": ["Display Gate緩和", "RN表示条件", "fixed observation sentence"],
        "forbidden_actions": ["candidate 未生成のまま Display Gate を緩める", "fixed observation sentence を足す"],
        "required_evidence": ["candidate.generated is false, or composer_status/source is not generated/ai_generated"],
        "test_focus": ["candidate_generated_before_display_gate becomes true for eligible input", "non-eligible/safety paths remain fail-closed"],
        "exit_condition": "candidate が生成され、reader / grounding / template / display のいずれかで分類可能になる。",
        "terminal": False,
        "requires_diagnostic_enrichment": False,
    },
    "candidate_generated_but_reader_rejected": {
        "target_layer": "reader",
        "target_area": "Reader / relation surface / relation_not_expressed",
        "next_work_name": "Reader / relation surface consistency fix",
        "next_work_summary": "候補生成後に Reader で落ちているため、読める観測文・relation surface・relation_not_expressed を整合させる。",
        "touch_files": ["listener_reader_judge", "relation_surface_contract", "self_repair relation marker"],
        "do_not_touch": ["Groundingだけの修正に決め打ちしない", "Display Gate緩和", "RN表示条件", "fixed sentence"],
        "forbidden_actions": ["Reader rejection を Grounding だけの問題に決め打ちする", "relation_not_expressed を握りつぶす"],
        "required_evidence": ["candidate generated is true and gate_results.reader.passed is false"],
        "test_focus": ["relation_not_expressed / readability rejection is reproduced by meta fixture", "repair keeps evidence and relation IDs traceable"],
        "exit_condition": "reader gate が pass し、次の grounding/template/display 層で判定できる。",
        "terminal": False,
        "requires_diagnostic_enrichment": False,
    },
    "candidate_generated_but_grounding_rejected": {
        "target_layer": "grounding",
        "target_area": "sentence binding / evidence binding / unsupported_sentence",
        "next_work_name": "sentence binding / evidence binding fix",
        "next_work_summary": "候補生成後に Grounding で落ちているため、文単位の根拠束縛・used ids・unsupported_sentence を修正する。",
        "touch_files": ["complete_grounding_binding", "grounding_service", "used ids"],
        "do_not_touch": ["template sentence addition", "テンプレ文追加", "Display Gate緩和", "RN表示条件", "Tone Engine"],
        "forbidden_actions": ["unsupported_sentence を無視して通す", "テンプレ文追加でごまかす"],
        "required_evidence": ["candidate generated is true and gate_results.grounding.passed is false"],
        "test_focus": ["unsupported_sentence becomes release-blocking in tests", "each displayed sentence can trace back to evidence / phrase / relation"],
        "exit_condition": "grounding gate が pass し、template/display 層へ進む。",
        "terminal": False,
        "requires_diagnostic_enrichment": False,
    },
    "candidate_generated_but_template_rejected": {
        "target_layer": "template",
        "target_area": "Surface variation / echo guard",
        "next_work_name": "Surface variation / echo suppression fix",
        "next_work_summary": "候補生成後に Template/Echo で落ちているため、raw echo・同型語尾・固定文臭を抑制する。",
        "touch_files": ["complete_surface_realizer", "template_echo_guard"],
        "do_not_touch": ["Gate緩和", "fixed sentence", "RN表示条件", "input-specific branch"],
        "forbidden_actions": ["固定文を増やす", "Template/Echo Gate を緩める"],
        "required_evidence": ["candidate generated is true and gate_results.template_echo.passed is false"],
        "test_focus": ["raw echo / same ending / fixed sentence are rejected", "surface variation does not add unsupported content"],
        "exit_condition": "template_echo gate が pass し、display 層へ進む。",
        "terminal": False,
        "requires_diagnostic_enrichment": False,
    },
    "candidate_generated_but_display_rejected": {
        "target_layer": "display",
        "target_area": "phase readiness / composer source / empty text wiring",
        "next_work_name": "phase readiness / source / empty text wiring fix",
        "next_work_summary": "Reader/Grounding/Template 後に Display で落ちているため、phase readiness・composer source・empty text wiring を修正する。",
        "touch_files": ["reply_service phase6/7/8", "display_gate input meta"],
        "do_not_touch": ["文章品質修正", "Gate緩和", "RN表示条件", "fixed observation sentence"],
        "forbidden_actions": ["Display rejection を文章品質修正に決め打ちする", "phase_not_complete を無視する"],
        "required_evidence": ["reader/grounding/template are not failed and gate_results.display.passed is false"],
        "test_focus": ["display rejection reason is preserved", "non-passed remains comment_text empty"],
        "exit_condition": "public observation_status passed + comment_text_length > 0 へ到達するか、display rejection reason が説明可能になる。",
        "terminal": False,
        "requires_diagnostic_enrichment": False,
    },
    "passed_backend_frontend_hidden": {
        "target_layer": "frontend",
        "target_area": "RN input_feedback receive / status reading / modal condition",
        "next_work_name": "RN receive / modal condition / status reading fix",
        "next_work_summary": "backend は passed + text だが RN で開いていないため、input_feedback 受信・status 読み取り・modal 条件を修正する。",
        "touch_files": ["InputScreen", "inputFeedbackModel", "useInputFeedbackModal"],
        "do_not_touch": ["backend Composer", "Surface Realizer", "Grounding", "Display Gate緩和"],
        "forbidden_actions": ["backend Composer を修正対象にする", "public status 以外で RN を強制 passed にする"],
        "required_evidence": ["backend observation_status passed and comment_text_length > 0, but RN modal_opened is false"],
        "test_focus": ["RN uses public observation_status only", "passed + comment_text opens modal; non-passed never opens modal"],
        "exit_condition": "RN frontend diagnostic shows modal_opened true for backend passed + text.",
        "terminal": False,
        "requires_diagnostic_enrichment": False,
    },
    "passed_displayed": {
        "target_layer": "scorecard",
        "target_area": "scorecard / coverage suite / blind QA",
        "next_work_name": "Complete Composer product-quality scorecard",
        "next_work_summary": "非表示修正対象ではなく、coverage suite / blind QA / scorecard へ進む。",
        "touch_files": ["coverage suite", "blind QA", "scorecard"],
        "do_not_touch": ["non-display repair path", "非表示修正扱いにしない", "Gate緩和", "input-specific branch"],
        "forbidden_actions": ["非表示修正扱いにする", "原因修正パッチを作る"],
        "required_evidence": ["backend passed + comment_text_length > 0 and RN modal_opened true"],
        "test_focus": ["displayed samples enter product-quality scoring instead of repair"],
        "exit_condition": "eligible coverage / safety / non-template / read-feel scorecard が評価される。",
        "terminal": True,
        "requires_diagnostic_enrichment": False,
    },
    "unclassified_non_display": {
        "target_layer": "diagnostic",
        "target_area": "diagnostic schema enrichment before repair",
        "next_work_name": "diagnostic schema enrichment before repair",
        "next_work_summary": "分類不能のため、Composer/RN修正ではなく diagnostic_summary / gate_results / repair meta を補強する。",
        "touch_files": ["diagnostic_summary extraction", "gate_results normalization", "complete_reply_service_diagnostics aliases"],
        "do_not_touch": ["SelfRepair", "Surface Realizer", "Tone Engine", "Display Gate緩和", "RN表示条件"],
        "forbidden_actions": ["原因未分類のまま修正に入る", "SelfRepair / Surface Realizer / Tone Engine へ進む"],
        "required_evidence": ["classification is unclassified_non_display or required stage/gate/candidate meta is missing"],
        "test_focus": ["missing meta is reported as diagnostic gap", "raw input and comment_text remain excluded"],
        "exit_condition": "classification が pre_connection / candidate / reader / grounding / template / display / frontend のいずれかに落ちる。",
        "terminal": False,
        "requires_diagnostic_enrichment": True,
    },
    "unknown_diagnostic_missing": {
        "target_layer": "diagnostic",
        "target_area": "diagnostic schema enrichment before repair",
        "next_work_name": "diagnostic schema enrichment before repair",
        "next_work_summary": "diagnostic が不足しているため、原因修正ではなく stage / gate / candidate / repair meta を補強する。",
        "touch_files": ["diagnostic_summary extraction", "gate_results normalization", "complete_reply_service_diagnostics aliases"],
        "do_not_touch": ["SelfRepair", "Surface Realizer", "Tone Engine", "Display Gate緩和", "RN表示条件"],
        "forbidden_actions": ["原因未分類のまま修正に入る", "SelfRepair / Surface Realizer / Tone Engine へ進む"],
        "required_evidence": ["classification is missing or diagnostic_summary/gate_results are missing"],
        "test_focus": ["missing diagnostic meta is surfaced", "raw input and comment_text remain excluded"],
        "exit_condition": "classification が既知の分岐へ落ちる。",
        "terminal": False,
        "requires_diagnostic_enrichment": True,
    },
}


# Phase18-7 canonical taxonomy classes.  Keep the old branch destinations as
# compatibility targets; canonical classes simply route to the same next-work
# layer without changing public/RN contracts.
_BRANCH_TABLE.update(
    {
        "candidate_not_generated": dict(_BRANCH_TABLE["candidate_missing"]),
        "candidate_generated_display_passed": dict(_BRANCH_TABLE["passed_displayed"]),
        "candidate_blocked_surface_grammar": {
            **dict(_BRANCH_TABLE["candidate_generated_but_display_rejected"]),
            "target_area": "surface grammar / visible surface acceptance",
            "next_work_name": "Surface grammar / visible surface acceptance fix",
            "next_work_summary": "候補生成後に表示文法・visible surface acceptanceで落ちているため、表示文整形とanti-templateを修正する。",
            "touch_files": ["complete_surface_realizer", "visible_surface_acceptance_gate", "runtime_surface_pre_return_gate"],
            "required_evidence": ["surface grammar / visible_surface_acceptance reason code is present"],
        },
        "candidate_blocked_two_stage_contract": {
            **dict(_BRANCH_TABLE["candidate_generated_but_display_rejected"]),
            "target_area": "TwoStage required / label contract",
            "next_work_name": "TwoStage required / label contract boundary fix",
            "next_work_summary": "候補生成後にTwoStage label contractで落ちているため、required境界・section label伝搬を修正する。",
            "touch_files": ["two_stage_applicability", "two_stage_reception_gate", "complete_surface_realizer"],
            "required_evidence": ["two_stage_* reason code is present"],
        },
        "candidate_blocked_meta_boundary": {
            **dict(_BRANCH_TABLE["candidate_generated_but_display_rejected"]),
            "target_area": "meta-only public boundary",
            "next_work_name": "meta-only boundary sanitizer fix",
            "next_work_summary": "候補生成後にmeta境界違反で落ちているため、raw/body/policy本文のpayload混入を除外する。",
            "touch_files": ["public_feedback_meta", "diagnostic_summary", "state_answer_surface_contract"],
            "required_evidence": ["meta_boundary / public_meta_leak reason code is present"],
        },
        "low_information_public_repair_applied": dict(_BRANCH_TABLE["passed_displayed"]),
        "low_information_public_repair_failed": dict(_BRANCH_TABLE["candidate_generated_but_display_rejected"]),
        "pre_connection_blocked_safety": dict(_BRANCH_TABLE["pre_connection_stop"]),
        "pre_connection_blocked_scope": dict(_BRANCH_TABLE["pre_connection_stop"]),
        "pre_connection_blocked_ap0": dict(_BRANCH_TABLE["pre_connection_stop"]),
        "pre_connection_blocked_rollout": dict(_BRANCH_TABLE["pre_connection_stop"]),
        "pre_connection_blocked_flag": dict(_BRANCH_TABLE["pre_connection_stop"]),
    }
)

_KNOWN_CLASSIFICATIONS = tuple(_BRANCH_TABLE.keys())


def _clean(value: Any) -> str:
    if value is None or isinstance(value, (Mapping, list, tuple, set)):
        return ""
    return str(value).strip()


def _contains_forbidden_text_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if _clean(key) in _FORBIDDEN_TEXT_PAYLOAD_KEYS:
                return True
            if _contains_forbidden_text_payload_key(nested):
                return True
    elif isinstance(value, list):
        return any(_contains_forbidden_text_payload_key(item) for item in value)
    return False


def assert_observation_branch_meta_only(value: Mapping[str, Any], *, source: str = "branch") -> None:
    if _contains_forbidden_text_payload_key(value):
        raise ValueError(f"{source} contains a forbidden text payload key")
    if value.get("raw_input_included") is True or value.get("comment_text_included") is True:
        raise ValueError(f"{source} marks raw input or comment text as included")


def _assert_meta_only(value: Mapping[str, Any], *, source: str = "branch") -> None:
    assert_observation_branch_meta_only(value, source=source)


def _source_classification_value(source: Mapping[str, Any]) -> str:
    return _clean(
        source.get("next_action_classification")
        or source.get("canonical_classification")
        or source.get("diagnostic_classification")
        or source.get("classification")
    )


def _first_non_display_row(rows: Sequence[Mapping[str, Any]]) -> Mapping[str, Any] | None:
    for row in rows:
        classification = _source_classification_value(row)
        if classification and classification not in {"passed_displayed", "candidate_generated_display_passed"}:
            return row
    return None


def known_observation_branch_classifications() -> tuple[str, ...]:
    return _KNOWN_CLASSIFICATIONS


def extract_branch_classification(source: Mapping[str, Any]) -> str:
    _assert_meta_only(source, source="branch_source")
    explicit = _source_classification_value(source)
    if explicit:
        return explicit
    rows_value = source.get("rows")
    if isinstance(rows_value, Sequence) and not isinstance(rows_value, (str, bytes, bytearray)):
        rows = [dict(row) for row in rows_value if isinstance(row, Mapping)]
        non_display = _first_non_display_row(rows)
        if non_display is not None:
            return _source_classification_value(non_display) or classify_observation_diagnostic(non_display)
        if rows:
            return _source_classification_value(rows[0]) or classify_observation_diagnostic(rows[0])
    return classify_observation_diagnostic(source)


def _classification_from_source(value: str | Mapping[str, Any]) -> tuple[str, dict[str, Any]]:
    if isinstance(value, str):
        classification = _clean(value)
        source: dict[str, Any] = {"classification": classification, "raw_input_included": False, "comment_text_included": False}
    elif isinstance(value, Mapping):
        source = dict(value or {})
        _assert_meta_only(source, source="branch_source")
        classification = extract_branch_classification(source)
    else:
        classification = "unknown_diagnostic_missing"
        source = {"classification": classification, "raw_input_included": False, "comment_text_included": False}
    if not classification:
        classification = "unknown_diagnostic_missing"
    if classification not in _BRANCH_TABLE:
        classification = "unclassified_non_display"
    return classification, source


def resolve_observation_diagnostic_next_branch(value: str | Mapping[str, Any], *, first_divergence_layer: str = "") -> dict[str, Any]:
    classification, source = _classification_from_source(value)
    table = dict(_BRANCH_TABLE[classification])
    source_layer = _clean(first_divergence_layer or source.get("first_difference_layer") or source.get("first_divergence_layer"))
    terminal = bool(table["terminal"])
    requires_enrichment = bool(table["requires_diagnostic_enrichment"])
    ready_for_repair = not terminal and not requires_enrichment
    branch_locked = not requires_enrichment
    branch = {
        "version": BRANCHING_VERSION,
        "source": "emlis_observation_step8_branching",
        "classification": classification,
        "target_layer": table["target_layer"],
        "target_area": table["target_area"],
        "next_work_unit": table["target_area"] if terminal else f"{table['target_area']} の修正",
        "next_work_name": table["next_work_name"],
        "next_work_summary": table["next_work_summary"],
        "touch_files": list(table["touch_files"]),
        "touch_targets": list(table["touch_files"]),
        "do_not_touch": list(table["do_not_touch"]),
        "forbidden_actions": list(table["forbidden_actions"]),
        "required_evidence": list(table["required_evidence"]),
        "test_focus": list(table["test_focus"]),
        "exit_condition": table["exit_condition"],
        "first_divergence_layer": source_layer,
        "first_difference_layer": source_layer,
        "branch_locked": branch_locked,
        "ready_for_cause_repair": ready_for_repair,
        "cause_confirmed_for_repair": ready_for_repair,
        "requires_diagnostic_enrichment": requires_enrichment,
        "repair_allowed": ready_for_repair,
        "routing_status": "scorecard_candidate" if terminal else "diagnostic_incomplete" if requires_enrichment else "ready_for_next_repair",
        "terminal": terminal,
        "raw_input_included": False,
        "comment_text_included": False,
    }
    _assert_meta_only(branch, source="branch")
    return branch


def resolve_observation_diagnostic_branch(value: str | Mapping[str, Any], *, first_divergence_layer: str = "") -> dict[str, Any]:
    return resolve_observation_diagnostic_next_branch(value, first_divergence_layer=first_divergence_layer)


def build_observation_diagnostic_branch_plan(source: Mapping[str, Any]) -> dict[str, Any]:
    return resolve_observation_diagnostic_next_branch(source)


def attach_observation_diagnostic_next_branch(report: Mapping[str, Any]) -> dict[str, Any]:
    data = dict(report or {})
    data["raw_input_included"] = False
    data["comment_text_included"] = False
    _assert_meta_only(data, source="branch_report")
    branch = resolve_observation_diagnostic_next_branch(data)
    data["next_action_branch"] = branch
    data["next_branch"] = branch
    data["next_action_classification"] = branch["classification"]
    data["next_action_layer"] = branch["target_layer"]
    data["next_action_target"] = branch["target_area"]
    data["next_step"] = branch["next_work_unit"]
    data["target_layer"] = branch["target_layer"]
    data["branch_locked"] = branch["branch_locked"]
    data["ready_for_cause_repair"] = branch["ready_for_cause_repair"]
    data["requires_diagnostic_enrichment"] = branch["requires_diagnostic_enrichment"]
    _assert_meta_only(data, source="branch_report")
    return data


def dump_observation_diagnostic_branch_plan(plan: Mapping[str, Any]) -> str:
    data = dict(plan or {})
    data["raw_input_included"] = False
    data["comment_text_included"] = False
    _assert_meta_only(data, source="branch_plan")
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def format_observation_diagnostic_branch_markdown(plan: Mapping[str, Any]) -> str:
    _assert_meta_only(plan, source="branch_plan")

    def items(values: Any) -> list[str]:
        if not isinstance(values, Sequence) or isinstance(values, (str, bytes, bytearray)):
            return []
        return [f"- {v}" for v in values]

    lines = [
        f"classification: {_clean(plan.get('classification'))}",
        f"target_layer: {_clean(plan.get('target_layer'))}",
        f"target_area: {_clean(plan.get('target_area'))}",
        f"branch_locked: {plan.get('branch_locked')}",
        f"ready_for_cause_repair: {plan.get('ready_for_cause_repair')}",
        f"requires_diagnostic_enrichment: {plan.get('requires_diagnostic_enrichment')}",
        f"terminal: {plan.get('terminal')}",
        "",
        "touch_files:",
        *items(plan.get("touch_files")),
        "",
        "do_not_touch:",
        *items(plan.get("do_not_touch")),
        "",
        "forbidden_actions:",
        *items(plan.get("forbidden_actions")),
        "",
        f"exit_condition: {_clean(plan.get('exit_condition'))}",
    ]
    return "\n".join(lines)


def build_branch_plan(source: Mapping[str, Any]) -> dict[str, Any]:
    return build_observation_diagnostic_branch_plan(source)


def dump_branch_plan(plan: Mapping[str, Any]) -> str:
    return dump_observation_diagnostic_branch_plan(plan)


def format_branch_plan_markdown(plan: Mapping[str, Any]) -> str:
    return format_observation_diagnostic_branch_markdown(plan)


__all__ = [
    "BRANCHING_VERSION",
    "assert_observation_branch_meta_only",
    "attach_observation_diagnostic_next_branch",
    "build_branch_plan",
    "build_observation_diagnostic_branch_plan",
    "dump_branch_plan",
    "dump_observation_diagnostic_branch_plan",
    "extract_branch_classification",
    "format_branch_plan_markdown",
    "format_observation_diagnostic_branch_markdown",
    "known_observation_branch_classifications",
    "resolve_observation_diagnostic_branch",
    "resolve_observation_diagnostic_next_branch",
]
