# -*- coding: utf-8 -*-
from __future__ import annotations

"""Baseline and connection-visibility meta for EmlisAI limited Composer extension.

This module is meta-only. It does not rename public contracts, does not change
DB/API names, and does not create user-facing Emlis observation text.
"""

from typing import Any, Iterable, Mapping

_BASELINE_VERSION = "emlis.limited_composer_extension_baseline.v1"
_CONNECTION_VISIBILITY_VERSION = "emlis.limited_composer_connection_visibility.v1"
_BINDING_PRESENCE_VERSION = "emlis.limited_composer_binding_presence.v1"
_DIAGNOSTIC_SUMMARY_EXTENSION_VERSION = "emlis.limited_composer_diagnostic_summary_extension.v1"
_GATE_BINDING_CONTRACT_VERSION = "emlis.gate_binding_contract.v2"
_BINDING_DECISION_GATES = {"grounding", "display"}


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _dedupe(values: Iterable[Any]) -> list[str]:
    out: list[str] = []
    for value in values or []:
        item = _clean(value)
        if item and item not in out:
            out.append(item)
    return out


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return []


def _gate_support_source(*, gate: str, binding_used: bool, diagnostics: Mapping[str, Any]) -> str:
    if not binding_used:
        return "none"
    explicit = _clean(
        diagnostics.get("binding_support_source")
        or diagnostics.get("grounding_support_source")
        or diagnostics.get("support_source")
    )
    if explicit:
        return explicit
    if gate == "display":
        return "display_binding_aware_result"
    if gate == "grounding":
        return "declared_relation_binding"
    return "none"


def _candidate_mapping(candidate: Any) -> Mapping[str, Any]:
    return candidate if isinstance(candidate, Mapping) else {}


def _candidate_attr(candidate: Any, key: str, default: Any = None) -> Any:
    mapping = _candidate_mapping(candidate)
    if key in mapping:
        return mapping.get(key)
    return getattr(candidate, key, default)


def _candidate_meta(candidate: Any) -> Mapping[str, Any]:
    meta = _candidate_attr(candidate, "composer_meta", {})
    return meta if isinstance(meta, Mapping) else {}


def _candidate_text(candidate: Any) -> str:
    text = _candidate_attr(candidate, "comment_text", "")
    if not text:
        text = _candidate_attr(candidate, "text", "")
    return str(text or "").strip()


def _body_lines(text: Any) -> list[str]:
    lines = [line.strip() for line in str(text or "").replace("\r", "\n").split("\n") if line.strip()]
    body: list[str] = []
    for line in lines:
        if "Emlis" in line and ("です" in line or "だよ" in line) and len(line) <= 40:
            continue
        body.append(line)
    return body


def _binding_items_from_meta(meta: Mapping[str, Any]) -> tuple[list[Mapping[str, Any]], str, Mapping[str, Any]]:
    candidates: list[Any] = []
    source_key = ""
    bundle_meta: Mapping[str, Any] = {}
    for key in (
        "sentence_bindings",
        "sentence_binding",
        "bindings",
    ):
        value = meta.get(key)
        if isinstance(value, Mapping):
            bundle_meta = value
            source_key = source_key or key
            candidates.extend(_as_list(value.get("bindings") or value.get("sentence_bindings")))
        items = _as_list(value)
        if items:
            source_key = source_key or key
            candidates.extend(items)
    for key in ("sentence_binding_bundle", "binding_bundle", "binding"):
        bundle = meta.get(key)
        if isinstance(bundle, Mapping):
            bundle_meta = bundle
            source_key = key
            candidates.extend(_as_list(bundle.get("bindings") or bundle.get("sentence_bindings") or bundle.get("items")))
    out: list[Mapping[str, Any]] = []
    seen: set[str] = set()
    for index, item in enumerate(candidates, start=1):
        if not isinstance(item, Mapping):
            continue
        sentence_id = _clean(item.get("sentence_id") or item.get("id") or f"s{index}")
        key = f"{sentence_id}:{_clean(item.get('relation_type') or item.get('relation'))}"
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out, source_key, bundle_meta


def _tokens(value: Any) -> list[str]:
    if isinstance(value, (list, tuple, set)):
        return _dedupe(value)
    token = _clean(value)
    return [token] if token else []


def _sanitized_binding_rows(binding_items: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(binding_items, start=1):
        rows.append(
            {
                "sentence_id": _clean(item.get("sentence_id") or item.get("id") or f"s{index}"),
                "line_role": _clean(item.get("line_role") or item.get("role")),
                "relation_type": _clean(item.get("relation_type") or item.get("relation")),
                "used_evidence_span_ids": _tokens(item.get("used_evidence_span_ids") or item.get("evidence_span_ids")),
                "used_phrase_unit_ids": _tokens(item.get("used_phrase_unit_ids") or item.get("phrase_unit_ids")),
                "coverage_scope": _clean(item.get("coverage_scope")),
                "must_include": bool(item.get("must_include")),
            }
        )
    return rows


def build_limited_composer_binding_presence_meta(
    *,
    composer_candidate: Any = None,
) -> dict[str, Any]:
    """Return Step 2 binding-presence diagnostics without requiring raw input.

    SentenceBinding itself is introduced later.  This step only makes absence or
    presence explicit so empty Emlis observations can be diagnosed without
    asking for Mash様's raw text.
    """

    text = _candidate_text(composer_candidate)
    body_lines = _body_lines(text)
    meta = _candidate_meta(composer_candidate)
    binding_items, binding_source, bundle_meta = _binding_items_from_meta(meta)
    binding_rows = _sanitized_binding_rows(binding_items)
    explicit_count = 0
    for key in ("binding_count", "sentence_binding_count"):
        try:
            explicit_count = max(explicit_count, int(meta.get(key) or bundle_meta.get(key) or 0))
        except (TypeError, ValueError):
            pass
    binding_count = max(len(binding_rows), explicit_count)
    binding_version_token = _clean(bundle_meta.get("binding_version") or bundle_meta.get("version"))
    binding_stage = "sentence_binding_type_added" if binding_count and binding_version_token else "presence_only_before_sentence_binding_type"
    status = _clean(_candidate_attr(composer_candidate, "status", ""))
    source = _clean(_candidate_attr(composer_candidate, "composer_source", ""))
    generated_text_present = bool(status == "generated" and source == "ai_generated" and text)
    binding_required = bool(generated_text_present)
    expected_binding_count = len(body_lines) if binding_required else 0
    binding_present = bool(binding_count > 0)
    binding_missing = bool(binding_required and binding_count < expected_binding_count)
    used_phrase_unit_ids = _dedupe(
        item for row in binding_rows for item in list(row.get("used_phrase_unit_ids") or [])
    )
    used_evidence_span_ids = _dedupe(
        [*_tokens(_candidate_attr(composer_candidate, "used_evidence_span_ids", []))]
        + [item for row in binding_rows for item in list(row.get("used_evidence_span_ids") or [])]
    )
    relation_types = _dedupe(
        [row.get("relation_type") for row in binding_rows]
        + list(meta.get("relation_types") or bundle_meta.get("relation_types") or [])
    )
    relation_taxonomy = _as_mapping(
        meta.get("step5_relation_taxonomy")
        or meta.get("relation_taxonomy")
        or meta.get("limited_composer_relation_taxonomy")
        or bundle_meta.get("step5_relation_taxonomy")
        or bundle_meta.get("relation_taxonomy")
    )
    return {
        "version": _BINDING_PRESENCE_VERSION,
        "target_step": "2_diagnostic_summary_extension",
        "step": "2_diagnostic_summary_extension",
        "binding_stage": binding_stage,
        "sentence_binding_type_added": bool(binding_stage == "sentence_binding_type_added"),
        "binding_expected": binding_required,
        "binding_required": binding_required,
        "binding_present": binding_present,
        "binding_missing": binding_missing,
        "binding_missing_reason": ("sentence_binding_count_below_body_sentence_count" if binding_stage == "sentence_binding_type_added" else "sentence_binding_not_yet_attached") if binding_missing else "",
        "binding_used": False,
        "binding_count": binding_count,
        "expected_binding_count": expected_binding_count,
        "missing_binding_count": max(0, expected_binding_count - binding_count),
        "sentence_count": len(body_lines),
        "body_sentence_count": len(body_lines),
        "candidate_body_sentence_count": len(body_lines),
        "body_line_count": len(body_lines),
        "candidate_comment_text_present": bool(text),
        "composer_status": status,
        "composer_source": source,
        "coverage_scope": _clean(_candidate_attr(composer_candidate, "coverage_scope", "") or bundle_meta.get("coverage_scope") or meta.get("coverage_scope")),
        "profile_key": _clean(bundle_meta.get("profile_key") or meta.get("profile_key")),
        "relation_types": relation_types,
        "relation_type_count": len(relation_types),
        "relation_taxonomy": dict(relation_taxonomy),
        "step5_relation_taxonomy": dict(relation_taxonomy),
        "relation_taxonomy_added": bool(relation_taxonomy.get("relation_taxonomy_added")),
        "relation_not_expressed_traceable": bool(relation_taxonomy.get("relation_not_expressed_traceable")),
        "canonical_relation_types": _dedupe(relation_taxonomy.get("canonical_relation_types") or []),
        "relation_families": _dedupe(relation_taxonomy.get("relation_families") or []),
        "unmapped_relation_types": _dedupe(relation_taxonomy.get("unmapped_relation_types") or []),
        "all_relation_types_mapped": bool(relation_taxonomy.get("all_relation_types_mapped")),
        "used_phrase_unit_count": len(used_phrase_unit_ids) or int(meta.get("used_phrase_unit_count") or 0),
        "used_evidence_span_count": len(used_evidence_span_ids),
        "binding_rows_sanitized": binding_rows,
        "binding_source": binding_source,
        "binding_version": binding_version_token,
        "relation_taxonomy_version": _clean(bundle_meta.get("relation_taxonomy_version") or meta.get("relation_taxonomy_version") or relation_taxonomy.get("version") or relation_taxonomy.get("taxonomy_version")),
        "raw_text_included": False,
        "raw_input_required_for_debug": False,
        "binding_contract_expected_next_step": "3_SentenceBinding_type_addition",
    }


def _gate_results_meta(gate_results: Any) -> dict[str, Any]:
    if not isinstance(gate_results, Mapping):
        return {}
    out: dict[str, Any] = {}
    for key, value in gate_results.items():
        as_meta = getattr(value, "as_meta", None)
        meta = as_meta() if callable(as_meta) else value
        if isinstance(meta, Mapping):
            diagnostics = meta.get("diagnostics") if isinstance(meta.get("diagnostics"), Mapping) else {}
            gate_key = str(key)
            raw_binding_used = bool(meta.get("binding_used") or diagnostics.get("binding_used"))
            binding_used = bool(raw_binding_used and gate_key in _BINDING_DECISION_GATES)
            binding_required = bool(
                gate_key in _BINDING_DECISION_GATES
                and (meta.get("binding_required") or diagnostics.get("binding_required"))
            )
            binding_present = bool(meta.get("binding_present") or meta.get("binding_available") or diagnostics.get("binding_present"))
            binding_available = bool(meta.get("binding_available") or meta.get("binding_present") or diagnostics.get("binding_present"))
            binding_missing = bool(binding_required and (meta.get("binding_missing") or diagnostics.get("binding_missing")))
            out[str(key)] = {
                "gate": str(key),
                "gate_binding_contract_version": _GATE_BINDING_CONTRACT_VERSION,
                "binding_contract_version": _GATE_BINDING_CONTRACT_VERSION,
                "passed": bool(meta.get("passed")),
                "primary_reason": _clean(meta.get("primary_reason")),
                "rejection_reasons": _dedupe(meta.get("rejection_reasons") or []),
                "reason_category": _clean(meta.get("reason_category")),
                "binding_used": binding_used,
                "binding_present": binding_present,
                "binding_available": binding_available,
                "binding_required": binding_required,
                "binding_missing": binding_missing,
                "binding_count": int(meta.get("binding_count") or diagnostics.get("binding_count") or 0),
                "expected_binding_count": int(meta.get("expected_binding_count") or diagnostics.get("expected_binding_count") or 0),
                "binding_support_source": _gate_support_source(gate=gate_key, binding_used=binding_used, diagnostics=diagnostics),
            }
    return out


def build_limited_composer_diagnostic_summary_extension_meta(
    *,
    diagnostic_summary: Mapping[str, Any] | None = None,
    coverage_matrix: Mapping[str, Any] | None = None,
    binding_presence: Mapping[str, Any] | None = None,
    gate_results: Any = None,
) -> dict[str, Any]:
    """Build Step 2 diagnostic summary extension meta.

    The contract added here is deliberately meta-only: every stop or pass path
    exposes stage, primary_reason, coverage_group, and binding presence.
    """

    summary = _as_mapping(diagnostic_summary)
    matrix = _as_mapping(coverage_matrix or summary.get("coverage_matrix"))
    binding = _as_mapping(binding_presence)
    stage = _clean(summary.get("stage"))
    primary_reason = _clean(summary.get("primary_reason"))
    coverage_group = _clean(
        summary.get("coverage_group")
        or summary.get("coverage_primary_group")
        or matrix.get("primary_coverage_group")
    )
    coverage_groups = _dedupe(summary.get("coverage_groups") or matrix.get("coverage_groups") or [])
    gate_meta = _gate_results_meta(gate_results or summary.get("gate_results"))
    for key, value in gate_meta.items():
        if isinstance(value, dict):
            gate_key = str(key)
            gate_requires_binding = bool(gate_key in _BINDING_DECISION_GATES and binding.get("binding_required"))
            value["binding_available"] = bool(value.get("binding_available") or binding.get("binding_present"))
            value["binding_present"] = bool(value.get("binding_present") or binding.get("binding_present"))
            value["binding_required"] = gate_requires_binding
            value["binding_missing"] = bool(gate_requires_binding and (value.get("binding_missing") or binding.get("binding_missing")))
            value["binding_used"] = bool(value.get("binding_used") and gate_key in _BINDING_DECISION_GATES)
            value["gate_binding_contract_version"] = _GATE_BINDING_CONTRACT_VERSION
            value["binding_contract_version"] = _GATE_BINDING_CONTRACT_VERSION
            value["binding_support_source"] = _gate_support_source(
                gate=gate_key,
                binding_used=bool(value.get("binding_used")),
                diagnostics=value,
            )
    first_failed_gate = ""
    first_failed_reason = ""
    for key in ("reader", "grounding", "template_echo", "display"):
        item = gate_meta.get(key) if isinstance(gate_meta, Mapping) else None
        if isinstance(item, Mapping) and not bool(item.get("passed")):
            first_failed_gate = key
            first_failed_reason = _clean(item.get("primary_reason"))
            break
    return {
        "version": _DIAGNOSTIC_SUMMARY_EXTENSION_VERSION,
        "target_step": "2_diagnostic_summary_extension",
        "step": "2_diagnostic_summary_extension",
        "baseline_stage": "limited_composer_extension",
        "diagnostic_contract": "stage_primary_reason_coverage_group_binding_presence",
        "gate_binding_contract_version": _GATE_BINDING_CONTRACT_VERSION,
        "stage": stage,
        "failed_stage": stage if _clean(summary.get("observation_status")) != "passed" else "",
        "primary_reason": primary_reason,
        "secondary_reasons": _dedupe(summary.get("secondary_reasons") or []),
        "observation_status": _clean(summary.get("observation_status")),
        "composer_status": _clean(summary.get("composer_status")),
        "coverage_scope": _clean(summary.get("coverage_scope")),
        "coverage_group": coverage_group,
        "coverage_primary_group": coverage_group,
        "coverage_groups": coverage_groups,
        "coverage_group_missing": not bool(coverage_group),
        "coverage_group_source": "coverage_matrix.primary_coverage_group" if coverage_group else "unclassified",
        "reason_codes": _dedupe([primary_reason, *list(summary.get("secondary_reasons") or []), *list(summary.get("gate_rejection_reasons") or []), *list(summary.get("composer_rejection_reasons") or []), *list(summary.get("scope_rejection_reasons") or [])]),
        "binding": dict(binding),
        "binding_required": bool(binding.get("binding_required")),
        "binding_expected": bool(binding.get("binding_expected") or binding.get("binding_required")),
        "binding_present": bool(binding.get("binding_present")),
        "binding_missing": bool(binding.get("binding_missing")),
        "binding_missing_reason": _clean(binding.get("binding_missing_reason")),
        "binding_count": int(binding.get("binding_count") or 0),
        "expected_binding_count": int(binding.get("expected_binding_count") or 0),
        "missing_binding_count": int(binding.get("missing_binding_count") or 0),
        "sentence_count": int(binding.get("sentence_count") or 0),
        "body_sentence_count": int(binding.get("body_sentence_count") or binding.get("sentence_count") or 0),
        "body_line_count": int(binding.get("body_line_count") or 0),
        "binding_used": bool(binding.get("binding_used")),
        "binding_presence": dict(binding),
        "relation_taxonomy": dict(binding.get("relation_taxonomy") or {}),
        "step5_relation_taxonomy": dict(binding.get("step5_relation_taxonomy") or binding.get("relation_taxonomy") or {}),
        "relation_taxonomy_added": bool(binding.get("relation_taxonomy_added")),
        "relation_not_expressed_traceable": bool(binding.get("relation_not_expressed_traceable")),
        "canonical_relation_types": _dedupe(binding.get("canonical_relation_types") or []),
        "relation_families": _dedupe(binding.get("relation_families") or []),
        "unmapped_relation_types": _dedupe(binding.get("unmapped_relation_types") or []),
        "all_relation_types_mapped": bool(binding.get("all_relation_types_mapped")),
        "gate_results": gate_meta,
        "first_failed_gate": first_failed_gate,
        "first_failed_reason": first_failed_reason,
        "raw_input_required_for_debug": False,
    }


def build_limited_composer_extension_baseline_meta() -> dict[str, Any]:
    """Return the fixed Step 0 baseline for the limited Composer extension.

    The baseline makes the current working vocabulary explicit while preserving
    legacy import/module names and public API contracts.  It is intentionally
    diagnostic meta only.
    """

    return {
        "version": _BASELINE_VERSION,
        "implementation_order": ["0_baseline", "1_connection_visibility"],
        "current_stage": "limited_composer_extension",
        "current_state": "limited_composer_basis_available_extension_in_progress",
        "target_state": "limited_composer_extension_complete",
        "next_target": "complete_composer_initial",
        "canonical_terms": {
            "current_composer": "限定Composer",
            "extension_complete": "限定Composer拡張完了",
            "next_goal": "完全Composer",
            "product_grade_goal": "完全Composer商品品質版",
        },
        "legacy_term_policy": "compat_keys_preserved_no_runtime_rename",
        "db_api_rename_performed": False,
        "public_route_rename_performed": False,
        "response_key_rename_performed": False,
        "display_contract_preserved": True,
        "display_contract": "input_feedback.comment_text is visible only when observation_status=passed and text exists",
        "visible_name": "Emlisの観測",
        "external_ai_rental_used": False,
        "local_llm_used": False,
        "fixed_completed_sentence_template_allowed": False,
        "input_specific_template_allowed": False,
    }


def _gate_reasons(gate_results: Any) -> list[str]:
    reasons: list[str] = []
    if not isinstance(gate_results, Mapping):
        return reasons
    for value in gate_results.values():
        passed = bool(getattr(value, "passed", True))
        if passed:
            continue
        primary = _clean(getattr(value, "primary_reason", ""))
        if primary:
            reasons.append(primary)
        reasons.extend(getattr(value, "rejection_reasons", []) or [])
    return _dedupe(reasons)


def build_limited_composer_connection_visibility_meta(
    *,
    resolution_meta: Mapping[str, Any] | None = None,
    release_meta: Mapping[str, Any] | None = None,
    scope_meta: Mapping[str, Any] | None = None,
    composer_candidate: Any = None,
    gate_results: Any = None,
    observation_status: Any = "",
    composer_status: Any = "",
) -> dict[str, Any]:
    """Classify connection stops separately from Composer/Gate rejection.

    This is Step 1 of the limited Composer extension.  It keeps
    ``composer_client_not_connected`` visible, but classifies it as a
    pre-connection condition when the registry never resolved a Composer client.
    """

    resolution = _as_mapping(resolution_meta)
    release = _as_mapping(release_meta)
    scope = _as_mapping(scope_meta)
    default_resolution = _as_mapping(resolution.get("default_composer_resolution"))
    registry_visibility = _as_mapping(resolution.get("connection_visibility"))

    explicit_client_used = bool(resolution.get("explicit_client_used") or resolution.get("explicit_client_provided"))
    default_client_used = bool(resolution.get("default_client_used") or default_resolution.get("default_client_used"))
    default_client_resolved = bool(
        resolution.get("default_client_resolved")
        or resolution.get("default_connection_active")
        or default_resolution.get("default_client_resolved")
        or default_resolution.get("default_connection_active")
        or default_client_used
    )
    safety_blocked = bool(resolution.get("safety_blocked") or default_resolution.get("safety_blocked"))
    connection_status = _clean(
        resolution.get("connection_status")
        or default_resolution.get("connection_status")
        or registry_visibility.get("connection_status")
        or "not_resolved"
    )
    pre_connection_stop_stage = _clean(
        resolution.get("pre_connection_stop_stage")
        or default_resolution.get("pre_connection_stop_stage")
        or registry_visibility.get("pre_connection_stop_stage")
        or registry_visibility.get("stop_stage")
    )
    composer_connection_attempted = bool(
        resolution.get("composer_attempted")
        or default_resolution.get("composer_attempted")
        or explicit_client_used
        or default_client_resolved
    )
    if safety_blocked:
        composer_connection_attempted = False

    raw_composer_status = _clean(composer_status or getattr(composer_candidate, "status", "") or "not_attempted")
    composer_reasons = _dedupe(getattr(composer_candidate, "rejection_reasons", []) or [])
    composer_client_not_connected_present = "composer_client_not_connected" in composer_reasons
    if not composer_connection_attempted and raw_composer_status == "unavailable" and composer_client_not_connected_present:
        visible_composer_status = "not_attempted"
    else:
        visible_composer_status = raw_composer_status

    resolution_reasons = _dedupe(resolution.get("rejection_reasons") or [])
    release_reasons = _dedupe(release.get("rejection_reasons") or [])
    release_reason_code = _clean(release.get("reason_code"))
    if release_reason_code:
        release_reasons = _dedupe([release_reason_code, *release_reasons])
    scope_reasons = _dedupe([
        *(scope.get("rejection_reasons") or []),
        *(scope.get("excluded_reason_codes") or []),
        *(scope.get("missing_information") or []),
    ])
    pre_connection_reasons = _dedupe([*resolution_reasons, *release_reasons, *scope_reasons])
    if not pre_connection_reasons and connection_status == "blocked_feature_flag":
        pre_connection_reasons = ["default_limited_composer_feature_disabled"]
    elif not pre_connection_reasons and connection_status == "blocked_safety":
        pre_connection_reasons = ["safety_boundary"]
    elif not pre_connection_reasons and connection_status == "blocked_rollout":
        pre_connection_reasons = ["limited_composer_rollout_not_allowed"]
    elif not pre_connection_reasons and connection_status == "blocked_scope":
        pre_connection_reasons = ["scope_limited_case_not_eligible"]

    runtime_composer_reasons = [] if not composer_connection_attempted else [
        reason for reason in composer_reasons if reason != "composer_client_not_connected"
    ]
    runtime_composer_reasons = _dedupe(runtime_composer_reasons)
    gate_reasons = _gate_reasons(gate_results)
    gate_rejection = bool(
        composer_connection_attempted
        and visible_composer_status == "generated"
        and _clean(observation_status) not in {"passed", ""}
        and gate_reasons
    )
    actual_composer_rejection = bool(
        composer_connection_attempted
        and visible_composer_status != "generated"
        and runtime_composer_reasons
    )
    pre_connection_stop = bool(not composer_connection_attempted)

    if pre_connection_stop:
        primary_stage = pre_connection_stop_stage or ("safety" if safety_blocked else "connection")
        primary_reason = pre_connection_reasons[0] if pre_connection_reasons else connection_status or "composer_client_not_connected"
    elif actual_composer_rejection:
        primary_stage = "composer"
        primary_reason = runtime_composer_reasons[0]
    elif gate_rejection:
        primary_stage = "gate"
        primary_reason = gate_reasons[0]
    else:
        primary_stage = "display" if _clean(observation_status) == "passed" else "composer"
        primary_reason = _clean(observation_status) or visible_composer_status or connection_status

    visible_pre_connection_reasons = pre_connection_reasons if pre_connection_stop else []

    return {
        "version": _CONNECTION_VISIBILITY_VERSION,
        "baseline_stage": "limited_composer_extension",
        "connection_status": connection_status,
        "pre_connection_stop_stage": pre_connection_stop_stage,
        "primary_stage": primary_stage,
        "primary_reason": primary_reason,
        "pre_connection_stop": pre_connection_stop,
        "blocked_before_composer": pre_connection_stop,
        "composer_connection_attempted": composer_connection_attempted,
        "composer_generation_attempted": composer_connection_attempted,
        "composer_client_not_connected_present": composer_client_not_connected_present,
        "composer_client_not_connected_class": "pre_connection" if pre_connection_stop and composer_client_not_connected_present else ("runtime" if composer_client_not_connected_present else ""),
        "actual_composer_rejection": actual_composer_rejection,
        "gate_rejection": gate_rejection,
        "composer_candidate_status": visible_composer_status,
        "raw_composer_candidate_status": raw_composer_status,
        "observation_status": _clean(observation_status),
        "explicit_client_used": explicit_client_used,
        "default_client_used": default_client_used,
        "default_client_resolved": default_client_resolved,
        "resolved_client_class": _clean(resolution.get("resolved_client_class") or resolution.get("resolved_client_name")),
        "composer_model": _clean(resolution.get("composer_model") or getattr(composer_candidate, "composer_model", "")),
        "release_stage": _clean(release.get("stage")),
        "release_enabled": bool(release.get("enabled")),
        "release_reason_code": release_reason_code,
        "scope_status": _clean(scope.get("scope_status")),
        "rejection_groups": {
            "pre_connection": visible_pre_connection_reasons,
            "composer_runtime": runtime_composer_reasons,
            "gate": gate_reasons if gate_rejection else [],
        },
        "pre_connection_reasons": visible_pre_connection_reasons,
        "runtime_composer_rejection_reasons": runtime_composer_reasons,
        "gate_rejection_reasons": gate_reasons if gate_rejection else [],
        "reason_classification_policy": "composer_client_not_connected_is_pre_connection_when_registry_did_not_resolve_client",
    }


__all__ = [
    "build_limited_composer_extension_baseline_meta",
    "build_limited_composer_connection_visibility_meta",
    "build_limited_composer_binding_presence_meta",
    "build_limited_composer_diagnostic_summary_extension_meta",
]
