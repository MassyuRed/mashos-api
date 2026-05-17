from __future__ import annotations

from emlis_ai_relation_surface_contract import (
    RELATION_SURFACE_CONTRACT_VERSION,
    detect_relation_surface,
    relation_marker_key,
    relation_marker_meta,
    relation_marker_phrase,
)


def test_relation_surface_contract_detects_positive_recovery_old_marker_without_reader_relaxation() -> None:
    signal = detect_relation_surface(
        "戻ってくる動きと前段の負荷の関係も残しています。",
        expected_relation_types=("positive_recovery",),
    )

    assert signal["relation_surface_contract_version"] == RELATION_SURFACE_CONTRACT_VERSION
    assert signal["reader_relation_signal_detected"] is True
    assert "recovery_load_bridge" in signal["reader_relation_signal_keys"]
    assert signal["reader_relation_signal_relation_types"] == ["recovery"]
    assert signal["expected_relation_types"] == ["recovery"]
    assert signal["raw_input_included"] is False


def test_relation_surface_contract_detects_recovery_marker_phrase_with_prior_load() -> None:
    phrase = relation_marker_phrase("recovery", {"prior_load_present": True})
    signal = detect_relation_surface(phrase, expected_relation_types=("recovery",))

    assert relation_marker_key("recovery", {"prior_load_present": True}) == "recovery_load_bridge_v1"
    assert "その前の重さ" in phrase
    assert signal["reader_relation_signal_detected"] is True
    assert signal["reader_relation_signal_count"] >= 1
    assert "recovery" in signal["reader_relation_signal_relation_types"]


def test_relation_surface_contract_requires_strict_recovery_bridge_not_bare_relation_word() -> None:
    signal = detect_relation_surface(
        "回復の関係も残しています。",
        expected_relation_types=("recovery",),
    )

    assert signal["reader_relation_signal_detected"] is False
    assert signal["reader_relation_signal_count"] == 0
    assert signal["reader_relation_signal_keys"] == []


def test_relation_surface_contract_does_not_let_generic_cue_alone_satisfy_recovery() -> None:
    signal = detect_relation_surface(
        "同じ場所に残っています。",
        expected_relation_types=("recovery",),
    )

    assert signal["generic_relation_signal_keys"]
    assert signal["reader_relation_signal_detected"] is False


def test_relation_marker_meta_is_additive_and_does_not_claim_public_display_contract() -> None:
    meta = relation_marker_meta("positive_recovery", {"prior_load_present": True})

    assert meta["relation_surface_contract_version"] == RELATION_SURFACE_CONTRACT_VERSION
    assert meta["relation_type"] == "recovery"
    assert meta["relation_marker_key"] == "recovery_load_bridge_v1"
    assert meta["relation_marker_signal"]["reader_relation_signal_detected"] is True
    assert meta["meaning_added"] is False
    assert meta["gate_relaxed"] is False
    assert meta["raw_input_included"] is False
    assert "observation_status" not in meta
    assert "comment_text" not in meta
