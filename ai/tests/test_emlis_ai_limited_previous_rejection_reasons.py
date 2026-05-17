from __future__ import annotations

from emlis_ai_limited_composer_client import (
    _previous_rejection_reasons,
    _requires_limited_reader_repair,
)


def test_limited_previous_rejection_reasons_reads_contract_ordered_and_deduped() -> None:
    payload = {
        "composition_contract": {
            "previous_rejection_reasons": [
                "relation_not_expressed",
                "",
                None,
                "addressee_not_clear",
                "relation_not_expressed",
                "grounding_not_supported",
            ]
        }
    }

    assert _previous_rejection_reasons(payload) == (
        "relation_not_expressed",
        "addressee_not_clear",
        "grounding_not_supported",
    )


def test_limited_previous_rejection_reasons_accepts_single_string_reason() -> None:
    payload = {"composition_contract": {"previous_rejection_reasons": "addressee_not_clear"}}

    assert _previous_rejection_reasons(payload) == ("addressee_not_clear",)


def test_limited_previous_rejection_reasons_is_fail_closed_for_invalid_payloads() -> None:
    assert _previous_rejection_reasons(None) == ()
    assert _previous_rejection_reasons({}) == ()
    assert _previous_rejection_reasons({"composition_contract": []}) == ()
    assert _previous_rejection_reasons({"composition_contract": {"previous_rejection_reasons": {"x": 1}}}) == ()


def test_requires_limited_reader_repair_only_for_reader_surface_reasons() -> None:
    assert _requires_limited_reader_repair(("relation_not_expressed",)) is True
    assert _requires_limited_reader_repair(("addressee_not_clear",)) is True
    assert _requires_limited_reader_repair(("grounding_not_supported", "template_echo")) is False
    assert _requires_limited_reader_repair(()) is False
    assert _requires_limited_reader_repair("relation_not_expressed") is True
