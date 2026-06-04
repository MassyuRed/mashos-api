# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase 1 contract inventory for EmlisAI User Label Connection Observation v1.

This module freezes the implementation boundary before the User Label
Connection runtime layers are built.  It is intentionally meta-only: it does
not read user history, does not generate ``comment_text``, does not add public
response keys, and does not change RN, DB, or ``/emotion/submit`` contracts.
"""

import json
from collections.abc import Mapping, Sequence
from typing import Any

USER_LABEL_CONNECTION_CONTRACT_INVENTORY_SCHEMA_VERSION = (
    "cocolon.emlis.user_label_connection.contract_inventory.v1"
)
USER_LABEL_CONNECTION_CONTRACT_INVENTORY_PHASE = "Phase1_ContractInventory"

_FORBIDDEN_TEXT_PAYLOAD_KEYS = {
    "raw_input",
    "rawInput",
    "raw_text",
    "rawText",
    "raw_user_text",
    "rawUserText",
    "input_text",
    "inputText",
    "memo",
    "memo_text",
    "memoText",
    "memo_action",
    "memoAction",
    "current_input",
    "currentInput",
    "history_input",
    "historyInput",
    "comment_text_body",
    "commentTextBody",
    "candidate_body",
    "surface_body",
}

_SOURCE_FILES_CHECKED = (
    "ai/services/ai_inference/api_contract_registry.py",
    "ai/services/ai_inference/api_emotion_submit.py",
    "ai/services/ai_inference/emotion_submit_service.py",
    "ai/services/ai_inference/emlis_ai_reply_service.py",
    "ai/services/ai_inference/emlis_ai_complete_composer_client.py",
    "ai/services/ai_inference/emlis_ai_public_feedback_meta.py",
    "ai/services/ai_inference/emlis_ai_current_input_bundle.py",
    "ai/services/ai_inference/emlis_ai_capability.py",
    "ai/services/ai_inference/emlis_ai_context_service.py",
    "ai/services/ai_inference/emlis_ai_types.py",
    "Cocolon/screens/InputScreen.js",
    "Cocolon/screens/input/InputFeedbackReplyModal.js",
    "Cocolon/screens/input/inputFeedbackModel.js",
)

_ALLOWED_PHASE_0_1_TOUCH_FILES = (
    "Cocolon_前提資料/00_karen_read_first.md",
    "Cocolon_前提資料/Cocolon_EmlisAI_UserLabelConnectionObservation_v1_Design_2026-06-03.md",
    "ai/services/ai_inference/emlis_ai_user_label_connection_contract_inventory.py",
    "ai/tests/test_emlis_ai_user_label_connection_e2e_contract.py",
)

_CONTRACT_LOCKS = (
    {
        "contract_id": "emotion_submit_route_stable",
        "owner": "backend_public_api",
        "must_keep": "POST /emotion/submit",
        "change_allowed": False,
    },
    {
        "contract_id": "emotion_submit_request_additive_only",
        "owner": "backend_public_api",
        "must_keep": "legacy request keys remain accepted; user label connection does not add required request keys",
        "change_allowed": False,
    },
    {
        "contract_id": "emotion_submit_response_additive_only",
        "owner": "backend_public_api",
        "must_keep": "public response shape remains status/id/created_at/input_feedback",
        "change_allowed": False,
    },
    {
        "contract_id": "input_feedback_comment_text_display_source",
        "owner": "backend_public_response_and_rn_reader",
        "must_keep": "input_feedback.comment_text is the only visible Emlis observation body",
        "change_allowed": False,
    },
    {
        "contract_id": "input_feedback_emlis_ai_additive_meta",
        "owner": "backend_public_response_and_rn_reader",
        "must_keep": "input_feedback.emlis_ai remains additive public-safe metadata",
        "change_allowed": False,
    },
    {
        "contract_id": "rn_passed_plus_non_empty_comment_contract",
        "owner": "Cocolon RN",
        "must_keep": "RN opens the Emlis modal only when observation_status is passed and public comment text is non-empty",
        "change_allowed": False,
    },
    {
        "contract_id": "rn_visible_title_stable",
        "owner": "Cocolon RN",
        "must_keep": "Emlisの観測",
        "change_allowed": False,
    },
    {
        "contract_id": "db_physical_schema_boundary",
        "owner": "storage_boundary",
        "must_keep": "Phase 0/1 do not change DB physical names, schema, or write paths",
        "change_allowed": False,
    },
    {
        "contract_id": "structure_insight_gate_not_relaxed",
        "owner": "EmlisAI backend gates",
        "must_keep": "User Label Connection will be implemented as a later separate history-connection gate, not by relaxing Structure Insight Gate",
        "change_allowed": False,
    },
    {
        "contract_id": "public_meta_raw_body_boundary",
        "owner": "public_feedback_meta_sanitizer",
        "must_keep": "raw memo/action/history text, candidate bodies, and public comment bodies are not included in public meta",
        "change_allowed": False,
    },
    {
        "contract_id": "phase1_inventory_only_boundary",
        "owner": "UserLabelConnectionObservation v1",
        "must_keep": "Phase 1 adds contract inventory/test only; material/candidate/gate/surface runtime layers are not connected yet",
        "change_allowed": False,
    },
)

_NON_TARGETS = (
    "RN screen addition",
    "RN modal title change",
    "RN display condition relaxation",
    "/emotion/submit route change",
    "/emotion/submit request key requirement addition",
    "/emotion/submit response shape change",
    "DB physical schema change",
    "history connection runtime material builder",
    "User Label Connection candidate builder",
    "User Label Connection Gate",
    "User Label Connection Surface Plan",
    "comment_text generation by User Label Connection layer",
    "public response key addition",
    "fixed observation sentence template",
    "external AI or local LLM prerequisite",
    "EmlisAI as Karen personality copy",
    "diagnosis/personality/future/advice surface",
)

_CONNECTION_POINTS = (
    {
        "connection_id": "public_contract_registry",
        "file": "ai/services/ai_inference/api_contract_registry.py",
        "phase1_reading": "POST /emotion/submit is additive-only and keeps input_feedback.comment_text stable while input_feedback.emlis_ai is additive-only",
        "runtime_change_in_phase1": False,
    },
    {
        "connection_id": "submit_response_model",
        "file": "ai/services/ai_inference/api_emotion_submit.py",
        "phase1_reading": "EmotionSubmitResponse exposes status/id/created_at/input_feedback; input_feedback exposes comment_text/emlis_ai",
        "runtime_change_in_phase1": False,
    },
    {
        "connection_id": "saved_input_to_current_bundle",
        "file": "ai/services/ai_inference/emotion_submit_service.py",
        "phase1_reading": "saved id/created_at/emotions/emotion_details/memo/memo_action/category are normalized before render_emlis_ai_reply",
        "runtime_change_in_phase1": False,
    },
    {
        "connection_id": "reply_service_source_bundle",
        "file": "ai/services/ai_inference/emlis_ai_reply_service.py",
        "phase1_reading": "render_emlis_ai_reply resolves capability and builds source bundle before composer/gates",
        "runtime_change_in_phase1": False,
    },
    {
        "connection_id": "complete_composer_meta_boundary",
        "file": "ai/services/ai_inference/emlis_ai_complete_composer_client.py",
        "phase1_reading": "CompleteComposerClient contract meta preserves public response, RN, DB, and gate boundaries",
        "runtime_change_in_phase1": False,
    },
    {
        "connection_id": "public_feedback_meta_sanitizer",
        "file": "ai/services/ai_inference/emlis_ai_public_feedback_meta.py",
        "phase1_reading": "should_include_public_input_feedback requires passed public status and non-empty comment_text",
        "runtime_change_in_phase1": False,
    },
    {
        "connection_id": "rn_modal_contract",
        "file": "Cocolon/screens/input/InputFeedbackReplyModal.js",
        "phase1_reading": "modal title remains Emlisの観測 and visibility remains delegated to passed-plus-comment helper",
        "runtime_change_in_phase1": False,
    },
)


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
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_forbidden_text_payload_key(item) for item in value)
    return False


def assert_user_label_connection_contract_inventory_meta_only(
    value: Mapping[str, Any],
    *,
    source: str = "user_label_connection_contract_inventory",
) -> None:
    """Validate that the Phase 1 inventory did not become a text payload."""

    if _contains_forbidden_text_payload_key(value):
        raise ValueError(f"{source} contains a forbidden text payload key")

    false_flags = (
        "api_route_changed",
        "request_key_changed",
        "response_shape_changed",
        "public_response_key_added",
        "db_physical_name_changed",
        "rn_visible_contract_changed",
        "rn_visible_title_changed",
        "structure_insight_gate_relaxed",
        "user_label_connection_runtime_connected",
        "user_label_connection_comment_text_generated",
        "fixed_sentence_template_added",
        "external_ai_added",
        "local_llm_added",
        "raw_input_included",
        "raw_text_included",
        "comment_text_body_included",
        "history_raw_text_included",
    )
    for flag in false_flags:
        if value.get(flag) is True:
            raise ValueError(f"{source} marks forbidden flag {flag}=true")


def build_user_label_connection_contract_inventory() -> dict[str, Any]:
    """Return the Phase 1 inventory used to lock public/RN boundaries."""

    inventory: dict[str, Any] = {
        "schema_version": USER_LABEL_CONNECTION_CONTRACT_INVENTORY_SCHEMA_VERSION,
        "phase": USER_LABEL_CONNECTION_CONTRACT_INVENTORY_PHASE,
        "feature": "EmlisAI User Label Connection Observation v1",
        "implementation_scope": "phase0_design_doc_and_phase1_contract_inventory_only",
        "design_document_added": True,
        "design_document_path": "Cocolon_前提資料/Cocolon_EmlisAI_UserLabelConnectionObservation_v1_Design_2026-06-03.md",
        "work_attitude_rules_folder": "work_attitude_rules_for_karen",
        "source_files_checked": list(_SOURCE_FILES_CHECKED),
        "allowed_phase_0_1_touch_files": list(_ALLOWED_PHASE_0_1_TOUCH_FILES),
        "contract_locks": [dict(item) for item in _CONTRACT_LOCKS],
        "connection_points": [dict(item) for item in _CONNECTION_POINTS],
        "non_targets": list(_NON_TARGETS),
        "public_route_contract": {
            "method": "POST",
            "path": "/emotion/submit",
            "contract_id": "emotion.submit.v1",
            "request_policy": "additive-only",
            "response_policy": "additive-only",
        },
        "public_response_contract": {
            "top_level_keys": ["status", "id", "created_at", "input_feedback"],
            "input_feedback_keys": ["comment_text", "emlis_ai"],
            "visible_body_source": "input_feedback.comment_text",
            "emlis_meta_source": "input_feedback.emlis_ai",
            "public_feedback_requires_passed_status": True,
            "public_feedback_requires_non_empty_comment": True,
        },
        "rn_visible_contract": {
            "title": "Emlisの観測",
            "display_condition": "observation_status == passed && comment_text non-empty",
            "dedicated_user_label_connection_screen_added": False,
            "display_condition_relaxed": False,
        },
        "phase2_runtime_layers_deferred": [
            "emlis_ai_user_label_connection_types.py",
            "emlis_ai_user_label_connection_material.py",
            "emlis_ai_user_label_connection_candidate.py",
            "emlis_ai_user_label_connection_gate.py",
            "emlis_ai_user_label_connection_surface.py",
        ],
        "api_route_changed": False,
        "request_key_changed": False,
        "response_shape_changed": False,
        "public_response_key_added": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "structure_insight_gate_relaxed": False,
        "user_label_connection_runtime_connected": False,
        "user_label_connection_comment_text_generated": False,
        "fixed_sentence_template_added": False,
        "external_ai_added": False,
        "local_llm_added": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_body_included": False,
        "history_raw_text_included": False,
    }
    assert_user_label_connection_contract_inventory_meta_only(inventory)
    return inventory


def dump_user_label_connection_contract_inventory(value: Mapping[str, Any] | None = None) -> str:
    inventory = dict(value or build_user_label_connection_contract_inventory())
    assert_user_label_connection_contract_inventory_meta_only(inventory)
    return json.dumps(inventory, ensure_ascii=False, sort_keys=True, indent=2)


__all__ = [
    "USER_LABEL_CONNECTION_CONTRACT_INVENTORY_PHASE",
    "USER_LABEL_CONNECTION_CONTRACT_INVENTORY_SCHEMA_VERSION",
    "assert_user_label_connection_contract_inventory_meta_only",
    "build_user_label_connection_contract_inventory",
    "dump_user_label_connection_contract_inventory",
]
