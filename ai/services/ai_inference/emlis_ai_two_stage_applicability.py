# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase18 TwoStage applicability contract for EmlisAI.

The contract is intentionally narrow and meta-only.  It decides whether a
candidate path must be treated as a labelled two-stage public surface before the
TwoStage Gate attaches terminal label-missing reasons.  It does not render text,
change public response keys, relax gates, or promote low-information repairs.
"""

from collections.abc import Iterable, Mapping
from typing import Any, Final

TWO_STAGE_APPLICABILITY_SCHEMA_VERSION: Final = "cocolon.emlis.two_stage_applicability_decision.v1"
TWO_STAGE_APPLICABILITY_SOURCE_PHASE: Final = "Phase18_product_quality_stabilization"

DECISION_REASON_EXPLICIT_GATE_REQUIRED: Final = "explicit_gate_required"
DECISION_REASON_COMPLETE_CANDIDATE_TWO_STAGE_SURFACE_EXPECTED: Final = (
    "complete_candidate_two_stage_surface_expected"
)
DECISION_REASON_STATE_ANSWER_CONTRACT_REQUIRED: Final = "state_answer_contract_required"
DECISION_REASON_SECTION_PLAN_REQUIRED: Final = "two_stage_section_surface_plan_required"
DECISION_REASON_LABELLED_SURFACE_PRESENT: Final = "labelled_surface_present_without_required_terminal"
DECISION_REASON_NO_TWO_STAGE_CONTRACT: Final = "no_two_stage_contract"
DECISION_REASON_EXPLICIT_NOT_REQUIRED: Final = "explicit_gate_not_required"

EXEMPTION_REASON_LOW_INFORMATION_REPAIR_BRANCH: Final = "low_information_public_repair_owns_surface_shape"
EXEMPTION_REASON_ORDINARY_UNAVAILABLE_PATH: Final = "ordinary_unavailable_path_exempt"
EXEMPTION_REASON_LEGACY_TEXT_COMPOSER: Final = "legacy_text_composer_without_two_stage_surface_exempt"
EXEMPTION_REASON_PRE_CONNECTION_BLOCK: Final = "pre_connection_block_exempt"
EXEMPTION_REASON_DIAGNOSTIC_META_ONLY_STAGE: Final = "diagnostic_meta_only_stage_exempt"

_TRUE_VALUES: Final = frozenset({"1", "true", "yes", "y", "on", "enabled", "enable", "green", "passed", "ok", "allowed", "allow"})
_EMPTY_OR_UNAVAILABLE_SOURCES: Final = frozenset({"", "unavailable", "empty", "none", "null"})
_UNAVAILABLE_STATUSES: Final = frozenset({"", "unavailable", "not_generated", "none", "null"})
_PRE_CONNECTION_STAGES: Final = frozenset({"ap0", "rollout", "scope", "flag", "feature_flag", "safety"})
_REQUIRED_META_KEYS: Final = (
    "two_stage_reception_gate_required",
    "two_stage_required",
    "state_answer_two_stage_display_required",
    "state_answer_two_stage_reception_surface_required",
    "state_answer_joined_comment_text_required",
    "state_answer_section_labels_required",
    "two_stage_display_required",
    "two_stage_reception_surface_required",
    "joined_comment_text_required",
    "section_labels_required",
)
_EXPECTED_SHAPE_KEYS: Final = (
    "state_answer_expected_comment_text_shape",
    "expected_comment_text_shape",
)
_CONTAINER_KEYS: Final = (
    "state_answer_composer_role_plan",
    "composition_contract",
    "composer_payload",
    "payload",
    "diagnostic_summary",
    "state_answer_surface_contract",
    "emlis_state_answer_surface_contract",
    "state_answer_contract",
    "complete_composer_candidate",
)
_FORBIDDEN_META_KEYS: Final = frozenset(
    {
        "raw_input",
        "raw_text",
        "input_text",
        "user_input",
        "current_input",
        "memo",
        "memo_text",
        "memo_action",
        "comment_text",
        "candidate_comment_text",
        "public_comment_text",
        "observation_text",
        "reception_text",
        "body",
        "text",
        "sentence",
        "sentences",
    }
)
_FORBIDDEN_TRUE_FLAGS: Final = frozenset(
    {
        "public_response_key_added",
        "observation_text_key_added",
        "reception_text_key_added",
        "rn_visible_contract_changed",
        "db_physical_name_changed",
        "api_route_changed",
        "raw_input_included",
        "raw_text_included",
        "comment_text_body_included",
        "generated_candidate_text_included",
        "surface_policy_included",
        "display_gate_relaxed",
        "grounding_gate_relaxed",
        "reader_gate_relaxed",
        "template_gate_relaxed",
    }
)
_FALSE_PUBLIC_CONTRACT: Final = {
    "public_response_key_added": False,
    "observation_text_key_added": False,
    "reception_text_key_added": False,
    "rn_visible_contract_changed": False,
    "db_physical_name_changed": False,
    "api_route_changed": False,
    "raw_input_included": False,
    "raw_text_included": False,
    "comment_text_body_included": False,
    "generated_candidate_text_included": False,
    "surface_policy_included": False,
}
_FALSE_GATE_POLICY: Final = {
    "display_gate_relaxed": False,
    "grounding_gate_relaxed": False,
    "reader_gate_relaxed": False,
    "template_gate_relaxed": False,
}


def _clean(value: Any) -> str:
    return str(value or "").replace("\u3000", " ").replace("\r", " ").replace("\n", " ").strip()


def _clean_lower(value: Any) -> str:
    return _clean(value).lower()


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return _clean_lower(value) in _TRUE_VALUES


def _as_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    as_meta = getattr(value, "as_meta", None)
    if callable(as_meta):
        try:
            result = as_meta()
        except Exception:
            return {}
        return dict(result) if isinstance(result, Mapping) else {}
    return {}


def _listify(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    if isinstance(value, (tuple, set)):
        return list(value)
    if isinstance(value, (str, bytes, bytearray)):
        return [value]
    try:
        return list(value)
    except TypeError:
        return [value]


def _dedupe(values: Iterable[Any] | Any | None) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in _listify(values):
        item = _clean(value)
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _containers(*sources: Any) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    queue: list[dict[str, Any]] = []
    for source in sources:
        mapping = _as_mapping(source)
        if mapping:
            queue.append(mapping)
    while queue:
        current = queue.pop(0)
        found.append(current)
        for key in _CONTAINER_KEYS:
            nested = _as_mapping(current.get(key))
            if nested:
                queue.append(nested)
    return found


def _first_text(*values: Any) -> str:
    for value in values:
        text = _clean(value)
        if text:
            return text
    return ""


def _explicit_required_present(value: bool | None) -> bool:
    return isinstance(value, bool)


def _expected_labelled_shape(container: Mapping[str, Any]) -> bool:
    return any(_clean(container.get(key)) == "labelled_two_stage_text" for key in _EXPECTED_SHAPE_KEYS)


def _container_requires_two_stage(container: Mapping[str, Any]) -> bool:
    return any(_bool(container.get(key)) for key in _REQUIRED_META_KEYS) or _expected_labelled_shape(container)


def _has_required_contract(containers: Iterable[Mapping[str, Any]]) -> bool:
    return any(_container_requires_two_stage(container) for container in containers)


def _section_plan_required(two_stage_section_surface_plan: Any, containers: Iterable[Mapping[str, Any]]) -> bool:
    plan = _as_mapping(two_stage_section_surface_plan)
    candidates: list[dict[str, Any]] = [plan] if plan else []
    for container in containers:
        for key in ("two_stage_section_surface_plan", "section_surface_plan"):
            nested = _as_mapping(container.get(key))
            if nested:
                candidates.append(nested)
        if _bool(container.get("two_stage_section_surface_plan_required")):
            return True
    for candidate in candidates:
        if not candidate:
            continue
        looks_like_section_plan = any(
            key in candidate
            for key in (
                "material_id",
                "schema_version",
                "section_order",
                "section_ids",
                "sections",
                "comment_text_section_labels",
                "expected_comment_text_shape",
            )
        )
        if looks_like_section_plan and _bool(candidate.get("required") if "required" in candidate else True):
            return True
    return False


def _section_plan_connected(two_stage_section_surface_plan: Any, containers: Iterable[Mapping[str, Any]]) -> bool:
    if _as_mapping(two_stage_section_surface_plan):
        return True
    for container in containers:
        if _as_mapping(container.get("two_stage_section_surface_plan")):
            return True
        if _bool(container.get("two_stage_section_surface_plan_connected")):
            return True
    return False


def _low_information_branch(containers: Iterable[Mapping[str, Any]]) -> bool:
    for container in containers:
        values = {
            _clean_lower(container.get("observation_reply_kind")),
            _clean_lower(container.get("reply_kind")),
            _clean_lower(container.get("eligibility_status")),
            _clean_lower(container.get("status")),
        }
        if "low_information_observation" in values or "low_information" in values:
            return True
        if _bool(container.get("low_information_repair_branch")) or _bool(container.get("low_information_repair_applied")):
            return True
        if _as_mapping(container.get("low_information_observation_composer")):
            return True
    return False


def _pre_connection_block(containers: Iterable[Mapping[str, Any]]) -> str:
    for container in containers:
        connection_status = _clean_lower(container.get("connection_status"))
        stop_stage = _clean_lower(container.get("pre_connection_stop_stage") or container.get("stop_stage"))
        reason_group = _clean_lower(container.get("composer_client_not_connected_reason_group"))
        if _bool(container.get("blocked_before_composer")) or _bool(container.get("pre_connection_stop")):
            return stop_stage or reason_group or "pre_connection"
        if connection_status.startswith("blocked_"):
            return connection_status.removeprefix("blocked_") or "pre_connection"
        if stop_stage in _PRE_CONNECTION_STAGES:
            return stop_stage
        if reason_group in _PRE_CONNECTION_STAGES:
            return reason_group
        reasons = _dedupe(container.get("rejection_reasons") or [])
        for reason in reasons:
            lowered = reason.lower()
            if lowered.startswith("scope_"):
                return "scope"
            if lowered in {"complete_initial_ap0_not_green", "composer_resolution_blocked_ap0"}:
                return "ap0"
            if lowered in {"complete_initial_rollout_not_allowed", "limited_composer_rollout_not_allowed"}:
                return "rollout"
    return ""


def _complete_composer_path(containers: Iterable[Mapping[str, Any]]) -> bool:
    for container in containers:
        model = _clean_lower(container.get("composer_model") or container.get("model"))
        method = _clean_lower(container.get("generation_method") or container.get("composer_method"))
        source = _clean_lower(container.get("composer_source"))
        if _bool(container.get("complete_composer")) or _bool(container.get("complete_initial_client_used")):
            return True
        if method in {"complete_composer", "complete_composer_initial"}:
            return True
        if model == "cocolon.complete_composer.initial.v1" or model.startswith("cocolon.complete_composer"):
            return True
        if source in {"complete_composer", "complete_initial"}:
            return True
    return False


def _legacy_text_composer(containers: Iterable[Mapping[str, Any]]) -> bool:
    # Phase18-7 compatibility: diagnostic/test/legacy text composers may be
    # evaluated with state-answer or section-plan meta attached later in the
    # pipeline.  That meta must not turn an otherwise plain legacy candidate
    # into a required two-stage surface.  CompleteComposer paths keep their
    # explicit markers and are handled by the required branch below.
    if _complete_composer_path(containers):
        return False
    for container in containers:
        model = _clean_lower(container.get("composer_model") or container.get("model"))
        method = _clean_lower(container.get("generation_method") or container.get("composer_method"))
        source = _clean_lower(container.get("composer_source"))
        if _bool(container.get("limited_composer")):
            return True
        if "text_composer" in model or "textcomposer" in model or "text_composer" in method or "legacy_text" in method:
            return True
        if method in {"test_composer", "step10_e2e_test_composer"}:
            return True
        if source in {"legacy_text_composer", "text_composer"}:
            return True
    return False


def _complete_candidate_expected(containers: Iterable[Mapping[str, Any]], *, candidate_source: str, candidate_status: str) -> bool:
    if candidate_source != "ai_generated" or candidate_status != "generated":
        return False
    for container in containers:
        if _bool(container.get("complete_composer")) or _clean_lower(container.get("generation_method")) == "complete_composer_initial":
            return _container_requires_two_stage(container) or _section_plan_required(container.get("two_stage_section_surface_plan"), [container])
        if _clean_lower(container.get("composer_model")) == "cocolon.complete_composer.initial.v1":
            return _container_requires_two_stage(container) or _section_plan_required(container.get("two_stage_section_surface_plan"), [container])
    return False


def _ordinary_unavailable_path(*, candidate_source: str, candidate_status: str, comment_text_present: bool) -> bool:
    return (
        candidate_source in _EMPTY_OR_UNAVAILABLE_SOURCES
        and candidate_status in _UNAVAILABLE_STATUSES
        and not comment_text_present
    )


def build_two_stage_applicability_decision(
    *,
    composer_meta: Mapping[str, Any] | None = None,
    state_answer_surface_contract: Mapping[str, Any] | None = None,
    state_answer_two_stage_meta: Mapping[str, Any] | None = None,
    two_stage_section_surface_plan: Mapping[str, Any] | None = None,
    two_stage_section_plan_meta: Mapping[str, Any] | None = None,
    two_stage_surface_meta: Mapping[str, Any] | None = None,
    surface_shape: Mapping[str, Any] | None = None,
    branch_kind: Any = "",
    candidate_source: Any = "",
    candidate_status: Any = "",
    comment_text_present: bool | None = None,
    labels_present: bool | None = None,
    explicit_required: bool | None = None,
) -> dict[str, Any]:
    """Return the meta-only decision for applying the labelled TwoStage contract."""

    all_containers = _containers(
        composer_meta,
        state_answer_surface_contract,
        state_answer_two_stage_meta,
        two_stage_section_surface_plan,
        two_stage_section_plan_meta,
        two_stage_surface_meta,
        {"branch_kind": branch_kind} if branch_kind else {},
    )
    source = _clean_lower(
        candidate_source
        or _first_text(*(container.get("composer_source") for container in all_containers))
    )
    status = _clean_lower(
        candidate_status
        or _first_text(
            *(container.get("candidate_status") or container.get("status") or container.get("complete_initial_candidate_status") for container in all_containers)
        )
    )
    comment_present = bool(comment_text_present)
    shape = _as_mapping(surface_shape)
    labels_present_flag = bool(labels_present) or bool(shape.get("labels_present"))
    plan_connected = _section_plan_connected(two_stage_section_surface_plan, all_containers)
    state_contract_required = _has_required_contract(all_containers)
    section_plan_required = _section_plan_required(two_stage_section_surface_plan, all_containers) or _section_plan_required(two_stage_section_plan_meta, all_containers)

    exemption_reason = ""
    if _low_information_branch(all_containers):
        exemption_reason = EXEMPTION_REASON_LOW_INFORMATION_REPAIR_BRANCH
    elif _ordinary_unavailable_path(candidate_source=source, candidate_status=status, comment_text_present=comment_present):
        exemption_reason = EXEMPTION_REASON_ORDINARY_UNAVAILABLE_PATH
    elif _legacy_text_composer(all_containers) and explicit_required is not True:
        # Phase18-7 compatibility: legacy/test text-composer candidates may carry
        # state-answer or section-plan material for diagnostics, but they do not
        # own the labelled TwoStage surface.  Do not let stale material-only
        # plan meta turn a legacy generated body into a terminal label-missing
        # failure unless the caller explicitly requires TwoStage.
        exemption_reason = EXEMPTION_REASON_LEGACY_TEXT_COMPOSER
    else:
        pre_connection = _pre_connection_block(all_containers)
        if pre_connection:
            exemption_reason = f"{EXEMPTION_REASON_PRE_CONNECTION_BLOCK}:{pre_connection}"
        elif not comment_present and not labels_present_flag and not state_contract_required and not section_plan_required:
            exemption_reason = EXEMPTION_REASON_DIAGNOSTIC_META_ONLY_STAGE

    if exemption_reason:
        decision_reason = exemption_reason
        required = False
        terminal_when_label_missing = False
    elif _explicit_required_present(explicit_required):
        required = bool(explicit_required)
        decision_reason = DECISION_REASON_EXPLICIT_GATE_REQUIRED if required else DECISION_REASON_EXPLICIT_NOT_REQUIRED
        terminal_when_label_missing = required
    elif _complete_candidate_expected(all_containers, candidate_source=source, candidate_status=status):
        required = True
        decision_reason = DECISION_REASON_COMPLETE_CANDIDATE_TWO_STAGE_SURFACE_EXPECTED
        terminal_when_label_missing = True
    elif state_contract_required:
        required = True
        decision_reason = DECISION_REASON_STATE_ANSWER_CONTRACT_REQUIRED
        terminal_when_label_missing = True
    elif section_plan_required:
        required = True
        decision_reason = DECISION_REASON_SECTION_PLAN_REQUIRED
        terminal_when_label_missing = True
    else:
        required = False
        terminal_when_label_missing = False
        decision_reason = DECISION_REASON_LABELLED_SURFACE_PRESENT if labels_present_flag else DECISION_REASON_NO_TWO_STAGE_CONTRACT

    decision = {
        "schema_version": TWO_STAGE_APPLICABILITY_SCHEMA_VERSION,
        "source_phase": TWO_STAGE_APPLICABILITY_SOURCE_PHASE,
        "required": bool(required),
        "decision_reason": decision_reason,
        "candidate_source": source,
        "candidate_status": status,
        "comment_text_present": comment_present,
        "labels_present": labels_present_flag,
        "section_plan_connected": bool(plan_connected),
        "state_answer_contract_required": bool(state_contract_required),
        "two_stage_section_surface_plan_required": bool(section_plan_required),
        "exempt": bool(exemption_reason),
        "exemption_reason": exemption_reason,
        "terminal_when_label_missing": bool(terminal_when_label_missing),
        "public_contract": dict(_FALSE_PUBLIC_CONTRACT),
        "gate_policy": dict(_FALSE_GATE_POLICY),
    }
    assert_two_stage_applicability_contract(decision)
    return decision


def two_stage_applicability_public_summary(value: Mapping[str, Any] | None) -> dict[str, Any]:
    source = _as_mapping(value)
    if not source:
        return {}
    summary = {
        "schema_version": TWO_STAGE_APPLICABILITY_SCHEMA_VERSION,
        "source_phase": TWO_STAGE_APPLICABILITY_SOURCE_PHASE,
        "required": bool(source.get("required")),
        "decision_reason": _clean(source.get("decision_reason")),
        "exempt": bool(source.get("exempt")),
        "exemption_reason": _clean(source.get("exemption_reason")),
        "terminal_when_label_missing": bool(source.get("terminal_when_label_missing")),
        "section_plan_connected": bool(source.get("section_plan_connected")),
        "state_answer_contract_required": bool(source.get("state_answer_contract_required")),
        "two_stage_section_surface_plan_required": bool(source.get("two_stage_section_surface_plan_required")),
        "comment_text_present": bool(source.get("comment_text_present")),
        "labels_present": bool(source.get("labels_present")),
        "public_contract": dict(_FALSE_PUBLIC_CONTRACT),
        "gate_policy": dict(_FALSE_GATE_POLICY),
    }
    assert_two_stage_applicability_contract(summary)
    return summary


def assert_two_stage_applicability_contract(value: Any, *, source: str = "two_stage_applicability") -> None:
    if not isinstance(value, Mapping):
        raise ValueError(f"{source} must be a mapping")
    _assert_no_forbidden_keys(value)
    _assert_no_true_contract_flags(value)


def _assert_no_forbidden_keys(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if _clean(key) in _FORBIDDEN_META_KEYS:
                raise ValueError(f"two_stage_applicability must not include body/raw key: {key}")
            _assert_no_forbidden_keys(child)
    elif isinstance(value, (list, tuple, set)):
        for child in value:
            _assert_no_forbidden_keys(child)


def _assert_no_true_contract_flags(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if _clean(key) in _FORBIDDEN_TRUE_FLAGS and child is True:
                raise ValueError(f"two_stage_applicability violates contract: {key}=true")
            _assert_no_true_contract_flags(child)
    elif isinstance(value, (list, tuple, set)):
        for child in value:
            _assert_no_true_contract_flags(child)


__all__ = [
    "TWO_STAGE_APPLICABILITY_SCHEMA_VERSION",
    "TWO_STAGE_APPLICABILITY_SOURCE_PHASE",
    "DECISION_REASON_COMPLETE_CANDIDATE_TWO_STAGE_SURFACE_EXPECTED",
    "DECISION_REASON_EXPLICIT_GATE_REQUIRED",
    "DECISION_REASON_EXPLICIT_NOT_REQUIRED",
    "DECISION_REASON_LABELLED_SURFACE_PRESENT",
    "DECISION_REASON_NO_TWO_STAGE_CONTRACT",
    "DECISION_REASON_SECTION_PLAN_REQUIRED",
    "DECISION_REASON_STATE_ANSWER_CONTRACT_REQUIRED",
    "EXEMPTION_REASON_DIAGNOSTIC_META_ONLY_STAGE",
    "EXEMPTION_REASON_LEGACY_TEXT_COMPOSER",
    "EXEMPTION_REASON_LOW_INFORMATION_REPAIR_BRANCH",
    "EXEMPTION_REASON_ORDINARY_UNAVAILABLE_PATH",
    "EXEMPTION_REASON_PRE_CONNECTION_BLOCK",
    "assert_two_stage_applicability_contract",
    "build_two_stage_applicability_decision",
    "two_stage_applicability_public_summary",
]
