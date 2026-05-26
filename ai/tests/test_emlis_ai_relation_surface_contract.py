from __future__ import annotations

from emlis_ai_relation_surface_contract import (
    PHRASE_SURFACE_SHAPE_VERSION,
    RELATION_SURFACE_CONTRACT_VERSION,
    classify_phrase_surface_shape,
    compress_phrase_for_relation_surface,
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



def test_step5_phrase_surface_shape_classifies_obligation_without_exposing_text() -> None:
    meta = classify_phrase_surface_shape("イベントに出なければいけない予定があること")
    compressed = compress_phrase_for_relation_surface("イベントに出なければいけない予定があること", shape_meta=meta)

    assert meta["phrase_surface_shape_version"] == PHRASE_SURFACE_SHAPE_VERSION
    assert meta["shape"] == "obligation_or_schedule"
    assert meta["safe_for_direct_koto_attachment"] is False
    assert meta["safe_for_relation_line"] is True
    assert meta["requires_surface_compression"] is True
    assert meta["raw_input_included"] is False
    assert meta["comment_text_body_included"] is False
    assert compressed == "イベント予定の近さ"
    assert "なければこと" not in compressed


def test_step5_phrase_surface_shape_compresses_prediction_without_koto_splice() -> None:
    meta = classify_phrase_surface_shape("キャパオーバーしそうな予感があること")
    compressed = compress_phrase_for_relation_surface("キャパオーバーしそうな予感があること", shape_meta=meta)

    assert meta["shape"] == "prediction_or_capacity"
    assert meta["safe_for_direct_koto_attachment"] is False
    assert compressed == "キャパオーバーしそうな予感"
    assert "予感こと" not in compressed
    assert "があること" not in compressed


def test_step5_phrase_surface_shape_defers_unsafe_koto_splice() -> None:
    meta = classify_phrase_surface_shape("コミュニケーションも取らなければこと")
    compressed = compress_phrase_for_relation_surface("コミュニケーションも取らなければこと", shape_meta=meta)

    assert meta["shape"] == "unsafe_koto_splice"
    assert meta["safe_for_relation_line"] is False
    assert meta["requires_drop_or_defer"] is True
    assert compressed == ""


def test_step5_coexistence_marker_avoids_mechanical_relation_stack() -> None:
    phrase = relation_marker_phrase("coexistence")
    signal = detect_relation_surface(phrase, expected_relation_types=("coexistence",))

    assert "片方だけに減らさず" not in phrase
    assert "重なりとして並んで" not in phrase
    assert "状態が一色" not in phrase
    assert signal["reader_relation_signal_detected"] is True
    assert "coexistence" in signal["reader_relation_signal_relation_types"]
