# -*- coding: utf-8 -*-
from __future__ import annotations

import pytest

from emlis_ai_p7_body_free_leak_guard import (
    P7_BODY_FREE_LEAK_VIOLATION_SCHEMA_VERSION,
    P7_BODY_FREE_SAFE_CURRENT_INPUT_RUBRIC_VALUE,
    P7BodyFreeLeakGuardError,
    assert_p7_body_free_no_payload_leak,
    build_p7_product_quality_connection_scorecard_body_free_contract,
    collect_p7_body_free_leak_violations,
)

_SAMPLE_MEMO = "疲れているけれど、少し整えたい気持ちもある。"
_SAMPLE_INPUT_ID = "step6-product-quality-scorecard-input"
_SOURCE = "scorecard"


def _contract() -> dict[str, object]:
    return build_p7_product_quality_connection_scorecard_body_free_contract()


def _raw_values() -> dict[str, str]:
    return {
        "current_input.memo": _SAMPLE_MEMO,
        "current_input.id": _SAMPLE_INPUT_ID,
    }


def _safe_scorecard() -> dict[str, object]:
    return {
        "phase2_product_readfeel_rubric": {
            "dimensions": {
                "evidence_boundary": {
                    "green": P7_BODY_FREE_SAFE_CURRENT_INPUT_RUBRIC_VALUE,
                }
            }
        },
        "body_free": True,
        "raw_input_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "release_allowed": False,
    }


def test_r13_3_safe_current_input_rubric_vocabulary_is_path_limited_allowed() -> None:
    payload = _safe_scorecard()

    violations = collect_p7_body_free_leak_violations(payload, source=_SOURCE, contract=_contract(), forbidden_raw_values=_raw_values())

    assert violations == []
    assert_p7_body_free_no_payload_leak(payload, source=_SOURCE, contract=_contract(), forbidden_raw_values=_raw_values())


def test_r13_3_current_input_dict_key_is_rejected_as_forbidden_key() -> None:
    payload = {"phase": {"current_input": {"entry_ref": "sample"}}}

    violations = collect_p7_body_free_leak_violations(payload, source=_SOURCE, contract=_contract())

    assert violations[0]["schema_version"] == P7_BODY_FREE_LEAK_VIOLATION_SCHEMA_VERSION
    assert violations[0]["violation_kind"] == "forbidden_key"
    assert violations[0]["token_ref"] == "current_input"
    assert violations[0]["token_kind"] == "raw_payload_key"
    assert violations[0]["raw_value_included"] is False
    assert violations[0]["serialized_payload_included"] is False
    assert violations[0]["body_free"] is True


def test_r13_3_raw_memo_body_is_rejected_without_copying_body_to_violation_or_error() -> None:
    payload = {"diagnostic": {"line": f"detected body leak marker: {_SAMPLE_MEMO}"}}

    violations = collect_p7_body_free_leak_violations(payload, source=_SOURCE, contract=_contract(), forbidden_raw_values=_raw_values())

    assert violations[0]["violation_kind"] == "forbidden_raw_value"
    assert violations[0]["token_ref"] == "current_input.memo"
    assert violations[0]["token_kind"] == "raw_current_input_body"
    assert _SAMPLE_MEMO not in str(violations)

    with pytest.raises(P7BodyFreeLeakGuardError) as exc_info:
        assert_p7_body_free_no_payload_leak(payload, source=_SOURCE, contract=_contract(), forbidden_raw_values=_raw_values())
    message = str(exc_info.value)
    assert "forbidden_raw_value" in message
    assert "current_input.memo" in message
    assert _SAMPLE_MEMO not in message
    assert "detected body leak marker" not in message


def test_r13_3_current_input_id_is_rejected_without_copying_id_value() -> None:
    payload = {"diagnostic": {"line": f"source id={_SAMPLE_INPUT_ID}"}}

    violations = collect_p7_body_free_leak_violations(payload, source=_SOURCE, contract=_contract(), forbidden_raw_values=_raw_values())

    assert violations[0]["violation_kind"] == "forbidden_raw_value"
    assert violations[0]["token_ref"] == "current_input.id"
    assert violations[0]["token_kind"] == "raw_current_input_id"
    assert _SAMPLE_INPUT_ID not in str(violations)


@pytest.mark.parametrize("forbidden_key", ["memo_action", "comment_text"])
def test_r13_3_payload_body_keys_are_rejected(forbidden_key: str) -> None:
    payload = {"meta": {forbidden_key: "runtime body must not be materialized"}}

    violations = collect_p7_body_free_leak_violations(payload, source=_SOURCE, contract=_contract())

    assert violations[0]["violation_kind"] == "forbidden_key"
    assert violations[0]["token_ref"] == forbidden_key
    assert violations[0]["token_kind"] == "raw_payload_key"


def test_r13_3_false_body_free_markers_are_allowed() -> None:
    payload = {
        "raw_input_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "release_allowed": False,
    }

    violations = collect_p7_body_free_leak_violations(payload, source=_SOURCE, contract=_contract())

    assert violations == []


def test_r13_3_true_body_free_marker_is_rejected() -> None:
    payload = {"raw_input_included": True}

    violations = collect_p7_body_free_leak_violations(payload, source=_SOURCE, contract=_contract())

    assert violations[0]["violation_kind"] == "forbidden_true_flag"
    assert violations[0]["token_ref"] == "raw_input_included"
    assert violations[0]["token_kind"] == "contract_mutation_flag"


def test_r13_3_unregistered_current_input_string_occurrence_is_rejected() -> None:
    payload = {"rubric": {"green": P7_BODY_FREE_SAFE_CURRENT_INPUT_RUBRIC_VALUE}}

    violations = collect_p7_body_free_leak_violations(payload, source=_SOURCE, contract=_contract())

    assert violations[0]["violation_kind"] == "unsafe_unregistered_string_occurrence"
    assert violations[0]["token_ref"] == "current_input"
    assert violations[0]["token_kind"] == "unregistered_safe_vocabulary"


def test_r13_3_current_input_string_on_allowed_path_but_wrong_exact_value_is_rejected() -> None:
    payload = _safe_scorecard()
    payload["phase2_product_readfeel_rubric"]["dimensions"]["evidence_boundary"]["green"] = (
        P7_BODY_FREE_SAFE_CURRENT_INPUT_RUBRIC_VALUE + "_changed"
    )

    violations = collect_p7_body_free_leak_violations(payload, source=_SOURCE, contract=_contract())

    assert violations[0]["violation_kind"] == "unsafe_unregistered_string_occurrence"
    assert violations[0]["token_ref"] == "current_input"
    assert violations[0]["reason_code"] == "safe_vocabulary_path_or_value_not_allowlisted"


def test_r13_3_compact_failure_message_does_not_dump_raw_value_or_serialized_payload() -> None:
    payload = {
        "diagnostic": {
            "line": f"raw memo leaked here: {_SAMPLE_MEMO}",
            "nested": {"current_input": {"id": _SAMPLE_INPUT_ID}},
        },
        "raw_input_included": True,
    }

    with pytest.raises(P7BodyFreeLeakGuardError) as exc_info:
        assert_p7_body_free_no_payload_leak(payload, source=_SOURCE, contract=_contract(), forbidden_raw_values=_raw_values())

    message = str(exc_info.value)
    assert len(message) < 1100
    assert "body-free leak guard violations" in message
    assert "forbidden_raw_value" in message
    assert "forbidden_key" in message
    assert _SAMPLE_MEMO not in message
    assert _SAMPLE_INPUT_ID not in message
    assert "raw memo leaked here" not in message
    assert "serialized" not in message.lower()
