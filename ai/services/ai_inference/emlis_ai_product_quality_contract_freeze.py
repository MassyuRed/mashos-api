# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase 0 contract freeze material for EmlisAI Product Quality work.

This module does not change RN, API, DB, public response shape, or runtime
rendering behavior.  It builds a small internal, meta-only contract inventory so
Phase 1+ measurement code can prove that product-quality work starts from the
existing public/RN contract instead of relaxing it.
"""

import json
from collections.abc import Mapping, Sequence
from typing import Any, Final

PRODUCT_QUALITY_CONTRACT_FREEZE_VERSION: Final = (
    "cocolon.emlis.product_quality.contract_freeze.v1"
)
PRODUCT_QUALITY_CONTRACT_FREEZE_PHASE: Final = "Phase0_Contract_Freeze"
RN_EMLIS_OBSERVATION_TITLE: Final = "Emlisの観測"

_FORBIDDEN_TEXT_PAYLOAD_KEYS: Final[frozenset[str]] = frozenset(
    {
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
        "memo_action",
        "memoAction",
        "current_input",
        "currentInput",
        "comment_text",
        "commentText",
        "comment_text_body",
        "commentTextBody",
        "input_feedback_comment",
        "inputFeedbackComment",
        "public_comment_text",
        "candidate_comment_text",
        "candidate_body",
        "candidateBody",
        "surface_body",
        "surfaceBody",
        "surface_text",
        "surfaceText",
        "reply_text",
        "replyText",
        "realized_text",
        "realizedText",
        "display_text",
        "displayText",
        "observation_text",
        "reception_text",
        "body",
        "text",
    }
)

_FORBIDDEN_TRUE_FLAGS: Final[frozenset[str]] = frozenset(
    {
        "api_route_changed",
        "request_key_changed",
        "response_shape_changed",
        "public_response_key_added",
        "public_response_key_change",
        "db_physical_name_changed",
        "rn_visible_contract_changed",
        "rn_visible_title_changed",
        "display_gate_relaxed",
        "grounding_gate_relaxed",
        "reader_gate_relaxed",
        "template_gate_relaxed",
        "gate_relaxed",
        "raw_input_included",
        "raw_text_included",
        "input_text_included",
        "comment_text_included",
        "comment_text_body_included",
        "candidate_body_included",
        "surface_body_included",
        "product_gate_ready",
        "product_gate_reached",
        "product_gate_public_release_applied",
        "public_release_applied",
        "product_quality_released",
        "machine_metrics_used_for_read_feeling",
        "read_feeling_auto_filled_from_machine_metrics",
        "read_feeling_auto_estimation_allowed",
        "fixed_sentence_template_added",
        "fixed_sentence_template_used",
        "input_specific_template_added",
        "external_ai_used",
        "local_llm_used",
    }
)


def _clean(value: Any) -> str:
    if value is None or isinstance(value, (Mapping, list, tuple, set)):
        return ""
    return str(value).strip()


def _contains_text_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in _FORBIDDEN_TEXT_PAYLOAD_KEYS:
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
        for idx, child in enumerate(value):
            nested = _forbidden_true_flag_path(child, path=f"{path}[{idx}]")
            if nested:
                return nested
    return None


def assert_emlis_ai_product_quality_contract_freeze_meta_only(
    value: Mapping[str, Any],
    *,
    source: str = "emlis_ai_product_quality_contract_freeze",
) -> None:
    """Raise if Phase 0 material contains public/body/release leakage."""

    if not isinstance(value, Mapping):
        raise ValueError(f"{source} must be a mapping")
    if _contains_text_payload_key(value):
        raise ValueError(f"{source} contains a forbidden text payload key")
    flag_path = _forbidden_true_flag_path(value)
    if flag_path:
        raise ValueError(f"{source} marks forbidden contract/release flag true at {flag_path}")


def build_emlis_ai_product_quality_contract_freeze() -> dict[str, Any]:
    """Return the Phase 0 fixed boundary inventory for product-quality work."""

    freeze: dict[str, Any] = {
        "schema_version": PRODUCT_QUALITY_CONTRACT_FREEZE_VERSION,
        "version": PRODUCT_QUALITY_CONTRACT_FREEZE_VERSION,
        "phase": PRODUCT_QUALITY_CONTRACT_FREEZE_PHASE,
        "source": "EmlisAI_ProductQuality_Phase0_ContractFreeze",
        "contract_frozen": True,
        "measurement_connection_only": True,
        "runtime_behavior_changed": False,
        "contract_assertions": {
            "api_route_changed": False,
            "request_key_changed": False,
            "response_shape_changed": False,
            "public_response_key_added": False,
            "db_physical_name_changed": False,
            "rn_visible_contract_changed": False,
            "rn_visible_title_changed": False,
            "display_gate_relaxed": False,
            "grounding_gate_relaxed": False,
            "reader_gate_relaxed": False,
            "template_gate_relaxed": False,
            "gate_relaxed": False,
            "raw_input_included": False,
            "raw_text_included": False,
            "comment_text_body_included": False,
            "candidate_body_included": False,
        },
        "rn_display_contract": {
            "title": RN_EMLIS_OBSERVATION_TITLE,
            "requires_observation_status": "passed",
            "requires_comment_text_non_empty": True,
            "meta_only_passed_does_not_display": True,
            "status_not_passed_does_not_display": True,
            "contract_change_allowed": False,
        },
        "api_public_input_feedback_contract": {
            "route": "/emotion/submit",
            "comment_text_required": True,
            "public_emlis_meta_required": True,
            "public_observation_status_required": "passed",
            "runtime_surface_gate_may_block": True,
            "visible_surface_gate_may_block": True,
            "two_stage_reception_gate_may_block": True,
            "state_answer_gate_may_block": True,
            "contract_change_allowed": False,
        },
        "product_quality_material_contract": {
            "meta_only": True,
            "product_gate_ready": False,
            "product_gate_reached": False,
            "public_release_applied": False,
            "release_judgment_deferred": True,
            "machine_metrics_used_for_read_feeling": False,
            "read_feeling_auto_filled_from_machine_metrics": False,
        },
        "non_targets": [
            "RN display condition relaxation",
            "RN visible title change",
            "API response key addition",
            "DB physical schema change",
            "Gate relaxation",
            "fixed observation template addition",
            "external AI or local LLM addition",
            "Product Gate ready/public release declaration",
        ],
        "allowed_phase1_touch_area": [
            "local_product_qa_composer_profile",
            "composer_resolution_meta",
            "composer_disabled_blocker_recording",
            "internal_measurement_runner_bootstrap",
            "unit_tests",
        ],
        "product_gate_ready": False,
        "product_gate_reached": False,
        "product_gate_public_release_applied": False,
        "public_release_applied": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
    }
    assert_emlis_ai_product_quality_contract_freeze_meta_only(freeze)
    return freeze


def dump_emlis_ai_product_quality_contract_freeze(
    freeze: Mapping[str, Any] | None = None,
) -> str:
    data = dict(freeze or build_emlis_ai_product_quality_contract_freeze())
    assert_emlis_ai_product_quality_contract_freeze_meta_only(data)
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


__all__ = [
    "PRODUCT_QUALITY_CONTRACT_FREEZE_PHASE",
    "PRODUCT_QUALITY_CONTRACT_FREEZE_VERSION",
    "RN_EMLIS_OBSERVATION_TITLE",
    "assert_emlis_ai_product_quality_contract_freeze_meta_only",
    "build_emlis_ai_product_quality_contract_freeze",
    "dump_emlis_ai_product_quality_contract_freeze",
]
