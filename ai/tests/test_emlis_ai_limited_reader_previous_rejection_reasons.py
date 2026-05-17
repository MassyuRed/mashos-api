from __future__ import annotations

from typing import Any

from emlis_ai_limited_composer_client import (
    CocolonAPlanEquivalentComposerClient,
    CocolonLimitedComposerClient,
    _previous_rejection_reasons,
    _requires_limited_reader_repair,
)


def _payload(previous_rejection_reasons: list[str]) -> dict[str, Any]:
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
            "previous_rejection_reasons": previous_rejection_reasons,
        },
    }


def test_previous_rejection_reasons_reads_composition_contract() -> None:
    payload = _payload(["relation_not_expressed", "", "grounding_unsupported"])

    assert _previous_rejection_reasons(payload) == (
        "relation_not_expressed",
        "grounding_unsupported",
    )


def test_requires_limited_reader_repair_is_limited_to_reader_reasons() -> None:
    assert _requires_limited_reader_repair(["relation_not_expressed"]) is True
    assert _requires_limited_reader_repair(["addressee_not_clear"]) is True
    assert _requires_limited_reader_repair(["grounding_unsupported"]) is False
    assert _requires_limited_reader_repair([]) is False


def test_limited_composer_consumes_relation_reader_reason_after_step5() -> None:
    response = CocolonLimitedComposerClient().generate(_payload(["relation_not_expressed"]))
    repair_meta = dict(dict(response.get("composer_meta") or {}).get("limited_reader_repair") or {})

    assert response["composer_source"] == "ai_generated"
    assert repair_meta["target_step"] == "Step5_relation_surface_marker_repair"
    assert repair_meta["attempted"] is True
    assert repair_meta["applied"] is True
    assert repair_meta["previous_rejection_reasons"] == ["relation_not_expressed"]
    assert repair_meta["reader_rejection_reasons"] == ["relation_not_expressed"]
    assert repair_meta["requires_limited_reader_repair"] is True
    assert repair_meta["relation_surface_repair_required"] is True
    assert repair_meta["relation_surface_repaired"] is True
    assert "relation_marker_appended" in repair_meta["operations"]
    assert repair_meta["relation_marker_key"]
    assert repair_meta["gate_relaxed"] is False
    assert repair_meta["raw_input_included"] is False
    assert repair_meta["comment_text_changed"] is True


def test_limited_composer_does_not_attach_step3_meta_for_non_reader_reason() -> None:
    response = CocolonLimitedComposerClient().generate(_payload(["grounding_unsupported"]))
    composer_meta = dict(response.get("composer_meta") or {})

    assert "limited_reader_repair" not in composer_meta


def test_a1_equivalent_inherits_limited_previous_rejection_reader_meta() -> None:
    response = CocolonAPlanEquivalentComposerClient().generate(_payload(["addressee_not_clear"]))
    repair_meta = dict(dict(response.get("composer_meta") or {}).get("limited_reader_repair") or {})

    assert response["composer_model"] == "cocolon_emlis_observation_composer.a1.v1"
    assert repair_meta["attempted"] is True
    assert repair_meta["applied"] is False
    assert repair_meta["reader_rejection_reasons"] == ["addressee_not_clear"]
    assert repair_meta["addressee_repair_required"] is True
    assert repair_meta["complete_client_self_repair_touched"] is False
