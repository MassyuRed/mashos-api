from __future__ import annotations

from typing import Any

from emlis_ai_limited_composer_client import CocolonLimitedComposerClient
from emlis_ai_listener_reader_judge import judge_listener_readability


def _payload_with_previous_relation_rejection() -> dict[str, Any]:
    evidence = [
        {"span_id": "s1", "raw_text": "友達と話せて楽しかった。", "detected_type": "event", "source_field": "memo"},
        {"span_id": "s2", "raw_text": "夜になって急に不安になった。", "detected_type": "event", "source_field": "memo"},
    ]
    return {
        "schema_version": "emlis.composer.request.v1",
        "addressee": {"display_name_call": "Mashさん", "greeting_text": "Emlisです"},
        "observation_graph": {
            "primary_state": {
                "claim_id": "c1",
                "claim_type": "primary_state",
                "text": "source anchored",
                "evidence_span_ids": ["s1", "s2"],
            },
            "core_tensions": [],
            "pressure_sources": [],
            "limit_signals": [],
            "self_awareness": [],
            "value_or_strength_signals": [],
            "safety_boundaries": [],
            "forbidden_claims": [],
            "missing_information": [],
        },
        "evidence_spans": evidence,
        "limited_observation_scope": {"scope_status": "eligible", "coverage_scope": "partial_observation"},
        "composition_contract": {
            "forbidden_output_surfaces": [],
            "previous_rejection_reasons": ["relation_not_expressed"],
        },
    }


def test_limited_reader_repair_applies_relation_marker_from_previous_reason() -> None:
    response = CocolonLimitedComposerClient().generate(_payload_with_previous_relation_rejection())
    composer_meta = dict(response.get("composer_meta") or {})
    repair_meta = dict(composer_meta.get("limited_reader_repair") or {})

    assert response["composer_source"] == "ai_generated"
    assert repair_meta.get("attempted") is True
    assert repair_meta.get("applied") is True
    assert "relation_not_expressed" in repair_meta.get("previous_rejection_reasons", [])
    assert repair_meta.get("gate_relaxed") is False
    assert repair_meta.get("raw_input_included") is False
    assert repair_meta.get("relation_marker_key") or "relation_marker_appended" in repair_meta.get("operations", [])

    report = judge_listener_readability(
        response.get("comment_text"),
        expected_relation_types=composer_meta.get("relation_types") or (),
    )
    assert "relation_not_expressed" not in report.rejection_reasons
