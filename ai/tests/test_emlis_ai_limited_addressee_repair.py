from __future__ import annotations

from typing import Any

from emlis_ai_limited_composer_client import _apply_limited_addressee_repair_if_needed


def _payload(previous_rejection_reasons: list[str] | None = None) -> dict[str, Any]:
    return {
        "schema_version": "emlis.composer.request.v1",
        "addressee": {
            "display_name_call": "Mash様",
            "greeting_text": "Emlisです",
        },
        "composition_contract": {
            "previous_rejection_reasons": previous_rejection_reasons or ["addressee_not_clear"],
        },
    }


def _response(comment_text: str) -> dict[str, Any]:
    return {
        "schema_version": "emlis.composer.response.v1",
        "composer_source": "ai_generated",
        "status": "generated",
        "comment_text": comment_text,
        "composer_meta": {},
    }


def test_limited_addressee_repair_replaces_only_invalid_first_line() -> None:
    body_lines = [
        "楽しさと不安が同じ中にあります。",
        "小さな回復も並んでいます。",
    ]
    response = _response("Mash、Emlisです。\n" + "\n".join(body_lines))

    repaired = _apply_limited_addressee_repair_if_needed(
        response=response,
        payload=_payload(["addressee_not_clear"]),
        coverage_scope="partial_observation",
        profile_key="mixed_positive_anxiety",
    )

    lines = str(repaired["comment_text"]).splitlines()
    repair_meta = dict(dict(repaired.get("composer_meta") or {}).get("limited_reader_repair") or {})

    assert lines[0] == "Mash様、Emlisです。"
    assert lines[1:] == body_lines
    assert repair_meta["attempted"] is True
    assert repair_meta["applied"] is True
    assert repair_meta["addressee_repaired"] is True
    assert repair_meta["comment_text_changed"] is True
    assert "addressee_line_replaced" in repair_meta["operations"]
    assert "addressee_repair_pending_step4" not in repair_meta["pending_operations"]
    assert repair_meta["meaning_added"] is False
    assert repair_meta["gate_relaxed"] is False
    assert repair_meta["raw_input_included"] is False


def test_limited_addressee_repair_leaves_valid_greeting_body_unchanged() -> None:
    comment_text = "Mash様、Emlisです。\n楽しさと不安が同じ中にあります。\n小さな回復も並んでいます。"
    response = _response(comment_text)

    repaired = _apply_limited_addressee_repair_if_needed(
        response=response,
        payload=_payload(["addressee_not_clear"]),
        coverage_scope="partial_observation",
        profile_key="mixed_positive_anxiety",
    )

    repair_meta = dict(dict(repaired.get("composer_meta") or {}).get("limited_reader_repair") or {})

    assert repaired["comment_text"] == comment_text
    assert repair_meta["attempted"] is True
    assert repair_meta["applied"] is False
    assert repair_meta["addressee_repaired"] is False
    assert repair_meta["comment_text_changed"] is False
    assert repair_meta["meaning_added"] is False
    assert repair_meta["gate_relaxed"] is False
    assert repair_meta["raw_input_included"] is False


def test_limited_addressee_repair_does_not_run_for_relation_only_reason() -> None:
    response = _response("Mash、Emlisです。\n楽しさと不安が同じ中にあります。\n小さな回復も並んでいます。")

    repaired = _apply_limited_addressee_repair_if_needed(
        response=response,
        payload=_payload(["relation_not_expressed"]),
        coverage_scope="partial_observation",
        profile_key="mixed_positive_anxiety",
    )

    assert repaired == response


def test_limited_addressee_repair_does_not_create_fallback_for_empty_text() -> None:
    response = _response("")

    repaired = _apply_limited_addressee_repair_if_needed(
        response=response,
        payload=_payload(["addressee_not_clear"]),
        coverage_scope="partial_observation",
        profile_key="mixed_positive_anxiety",
    )

    repair_meta = dict(dict(repaired.get("composer_meta") or {}).get("limited_reader_repair") or {})

    assert repaired["comment_text"] == ""
    assert repair_meta["attempted"] is True
    assert repair_meta["applied"] is False
    assert repair_meta["comment_text_changed"] is False
    assert repair_meta["meaning_added"] is False
    assert repair_meta["gate_relaxed"] is False
    assert repair_meta["raw_input_included"] is False
