# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step 0 baseline / contract inventory for EmlisAI observation replies.

The inventory fixes the contracts that Step 1+ must not break: RN passed-only
visibility, existing public status enum, Free current-input-only capability, and
low-information cases that must become first-class observation replies in later
steps.  It is diagnostic meta only and does not change runtime rendering.
"""

from collections.abc import Mapping, Sequence
import json
from typing import Any, Final

OBSERVATION_REPLY_BASELINE_CONTRACT_INVENTORY_VERSION: Final[str] = (
    "emlis.observation_reply_baseline_contract_inventory.v1"
)

_FORBIDDEN_TEXT_PAYLOAD_KEYS: Final[frozenset[str]] = frozenset(
    {
        "raw_input",
        "rawInput",
        "input",
        "input_text",
        "inputText",
        "current_input",
        "currentInput",
        "memo",
        "memo_text",
        "memoText",
        "comment_text",
        "commentText",
        "public_comment_text",
        "candidate_comment_text",
        "reply_text",
        "text",
    }
)


def _clean(value: Any) -> str:
    if value is None:
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


def assert_observation_reply_baseline_inventory_meta_only(
    inventory: Mapping[str, Any],
    *,
    source: str = "observation_reply_baseline_inventory",
) -> None:
    if _contains_forbidden_text_payload_key(inventory):
        raise ValueError(f"{source} contains a forbidden text payload key")
    if inventory.get("raw_input_included") is True or inventory.get("comment_text_body_included") is True:
        raise ValueError(f"{source} marks raw input or public comment text as included")
    if inventory.get("public_observation_status_added") is not False:
        raise ValueError(f"{source} must not add a public observation_status")
    if inventory.get("rn_display_contract_changed") is not False:
        raise ValueError(f"{source} must not change RN display contract")


def build_observation_reply_baseline_contract_inventory() -> dict[str, Any]:
    inventory: dict[str, Any] = {
        "version": OBSERVATION_REPLY_BASELINE_CONTRACT_INVENTORY_VERSION,
        "status": "fixed",
        "scope": "EmlisAI Observation Reply Step0-1",
        "step0_baseline_contract_inventory_ready": True,
        "step1_observation_reply_contract_required": True,
        "step2_eligibility_router_required": True,
        "step8_low_information_composer_required": True,
        "current_public_display_contract": "observation_status=passed + non_empty_input_feedback_comment",
        "public_statuses": ["passed", "rejected", "unavailable", "safety_blocked"],
        "public_observation_status_added": False,
        "low_information_public_status_added": False,
        "rn_display_contract_changed": False,
        "api_response_key_changed": False,
        "db_physical_name_changed": False,
        "gate_relaxation_allowed": False,
        "display_gate_fail_closed_preserved": True,
        "low_information_observation_is_public_passed_body": True,
        "low_information_kind_is_meta_only": True,
        "low_information_empty_body_gap_registered": True,
        "low_information_red_cases_are_current_gap_targets": True,
        "low_information_red_cases_expected_branch": "low_information_observation",
        "low_information_red_cases_expected_public_status_after_implementation": "passed",
        "low_information_red_cases_expected_comment_body_after_implementation": "non_empty",
        "low_information_red_case_categories": [
            "short_emotion_only",
            "unspecified_burden",
            "long_ambiguous_reference",
            "past_fact_strong_but_current_event_unknown",
        ],
        "free_capability_contract": {
            "tier": "free",
            "history_mode": "none",
            "source_scope": "current_input_only",
            "model_read_enabled": False,
            "include_derived_user_model": False,
            "user_dictionary_allowed": False,
        },
        "subscription_user_dictionary_boundary": {
            "allowed": True,
            "may_hint": True,
            "may_promote_low_information_to_eligible": False,
            "assert_current_event_from_user_fact": False,
        },
        "allowed_touch_files": [
            "ai/services/ai_inference/emlis_ai_observation_reply_contract_inventory.py",
            "ai/services/ai_inference/emlis_ai_observation_reply_contract.py",
            "ai/tests/test_emlis_ai_observation_current_display_contract.py",
            "ai/tests/test_emlis_ai_low_information_red_cases.py",
            "ai/tests/test_emlis_ai_observation_reply_contract.py",
            "Cocolon/tests/rn-screen-contracts.test.js",
        ],
        "non_targets": [
            "RN display condition relaxation",
            "new public observation_status for low information",
            "API response key rename",
            "DB physical name rename/drop/write-path change",
            "Display Gate relaxation",
            "fixed fallback observation sentence addition",
            "external AI/runtime service addition",
            "low information composer implementation before Step8",
        ],
        "raw_input_included": False,
        "comment_text_body_included": False,
        "meta_only": True,
    }
    assert_observation_reply_baseline_inventory_meta_only(inventory)
    return inventory


def dump_observation_reply_baseline_contract_inventory(inventory: Mapping[str, Any] | None = None) -> str:
    value = build_observation_reply_baseline_contract_inventory() if inventory is None else dict(inventory)
    assert_observation_reply_baseline_inventory_meta_only(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)
