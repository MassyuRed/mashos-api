# -*- coding: utf-8 -*-
from __future__ import annotations

import json

import pytest

from emlis_ai_p7_body_free_leak_guard import (
    P7_BODY_FREE_LEAK_GUARD_CONTRACT_SCHEMA_VERSION,
    P7_BODY_FREE_LEAK_GUARD_CONTRACT_STEP,
    P7_BODY_FREE_SAFE_CURRENT_INPUT_RUBRIC_PATH_SUFFIX,
    P7_BODY_FREE_SAFE_CURRENT_INPUT_RUBRIC_VALUE,
    P7BodyFreeLeakGuardContractError,
    assert_p7_body_free_leak_guard_contract,
    build_p7_product_quality_connection_scorecard_body_free_contract,
)
from emlis_ai_p7_contracts import assert_p7_no_body_payload_or_contract_mutation

_SAMPLE_MEMO = "疲れているけれど、少し整えたい気持ちもある。"
_SAMPLE_INPUT_ID = "step6-product-quality-scorecard-input"


def test_r13_1_product_quality_scorecard_body_free_contract_is_definition_only() -> None:
    contract = build_p7_product_quality_connection_scorecard_body_free_contract()

    assert contract["schema_version"] == P7_BODY_FREE_LEAK_GUARD_CONTRACT_SCHEMA_VERSION
    assert contract["implementation_step"] == P7_BODY_FREE_LEAK_GUARD_CONTRACT_STEP
    assert contract["phase"] == "P7_ProductQualityRunner_LongRunGate"
    assert contract["source_mode"] == "local_snapshot"
    assert contract["git_checked"] is False
    assert contract["contract_kind"] == "body_free_leak_guard_definition_only"
    assert contract["scanner_implemented"] is False
    assert contract["e2e_assertion_replaced"] is False
    assert contract["body_free"] is True
    assert contract["release_boundary"] == {
        "p7_complete": False,
        "p8_start_allowed": False,
        "release_allowed": False,
    }
    assert_p7_body_free_leak_guard_contract(contract)
    assert_p7_no_body_payload_or_contract_mutation(contract, source="r13_1_contract_test")


def test_r13_1_contract_keeps_current_input_key_forbidden_but_rubric_vocabulary_allowed_by_path() -> None:
    contract = build_p7_product_quality_connection_scorecard_body_free_contract()

    forbidden_key_names = set(contract["forbidden_key_names"])
    assert "current_input" in forbidden_key_names
    assert "memo_action" in forbidden_key_names
    assert "source_text" in forbidden_key_names
    assert "comment_text" in forbidden_key_names
    assert "candidate_body" in forbidden_key_names

    allowed_occurrences = contract["allowed_string_occurrences"]
    assert allowed_occurrences == [
        {
            "token": "current_input",
            "path_suffix": P7_BODY_FREE_SAFE_CURRENT_INPUT_RUBRIC_PATH_SUFFIX,
            "exact_value": P7_BODY_FREE_SAFE_CURRENT_INPUT_RUBRIC_VALUE,
            "reason_code": "safe_rubric_vocabulary_not_raw_payload",
        }
    ]


def test_r13_1_contract_lists_raw_value_refs_without_materializing_sample_body_or_id() -> None:
    contract = build_p7_product_quality_connection_scorecard_body_free_contract()
    serialized = json.dumps(contract, ensure_ascii=False, sort_keys=True)

    assert _SAMPLE_MEMO not in serialized
    assert _SAMPLE_INPUT_ID not in serialized
    assert "current_input.memo" in serialized
    assert "current_input.id" in serialized
    assert all(item["value_materialized_in_contract"] is False for item in contract["forbidden_raw_value_refs"])
    assert {item["kind"] for item in contract["forbidden_raw_value_refs"]} >= {
        "raw_current_input_body",
        "raw_current_input_id",
        "raw_comment_text_body",
        "raw_candidate_body",
    }


def test_r13_1_contract_forbids_failure_output_payload_dump() -> None:
    contract = build_p7_product_quality_connection_scorecard_body_free_contract()

    assert contract["failure_output_policy"]["include_raw_values"] is False
    assert contract["failure_output_policy"]["include_serialized_payload"] is False
    assert 1 <= contract["failure_output_policy"]["max_reported_violations"] <= 20
    assert 40 <= contract["failure_output_policy"]["max_path_length"] <= 300


def test_r13_1_contract_rejects_raw_value_materialization() -> None:
    contract = build_p7_product_quality_connection_scorecard_body_free_contract()
    contract["forbidden_raw_value_refs"][0]["raw_value"] = _SAMPLE_MEMO

    with pytest.raises(P7BodyFreeLeakGuardContractError, match="must not materialize raw values"):
        assert_p7_body_free_leak_guard_contract(contract)


def test_r13_1_contract_rejects_unbounded_failure_output_policy() -> None:
    contract = build_p7_product_quality_connection_scorecard_body_free_contract()
    contract["failure_output_policy"]["include_serialized_payload"] = True

    with pytest.raises(P7BodyFreeLeakGuardContractError, match="include_serialized_payload=false"):
        assert_p7_body_free_leak_guard_contract(contract)
