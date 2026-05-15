from __future__ import annotations

from emlis_ai_coverage_matrix_service import COVERAGE_GROUP_ORDER, build_emlis_coverage_matrix


def test_coverage_matrix_defines_step08_input_groups():
    assert COVERAGE_GROUP_ORDER == (
        "energy_fatigue",
        "anxiety",
        "anger_hurt",
        "positive_recovery",
        "relationship",
        "limit_escape",
        "value_wish",
        "long_meaning_arc",
    )

    matrix = build_emlis_coverage_matrix(
        diagnostic_summary={
            "observation_status": "unavailable",
            "stage": "flag",
            "primary_reason": "default_limited_composer_feature_disabled",
            "secondary_reasons": ["default_limited_composer_feature_disabled"],
        },
        current_input={},
    )
    assert matrix["version"] == "emlis.coverage_matrix.v1"
    assert matrix["phase"] == "B-S1"
    assert "connection_rollout" in matrix["technical_coverage_groups"]
    assert matrix["primary_coverage_group"] == "connection_rollout"


def test_coverage_matrix_maps_current_input_to_input_groups():
    matrix = build_emlis_coverage_matrix(
        diagnostic_summary={
            "observation_status": "rejected",
            "stage": "reader",
            "primary_reason": "too_short_for_observation",
            "gate_coverage_matrix_hints": ["reader_readability"],
        },
        current_input={
            "memo": "だるいし何もしたくない。相談したいけど迷惑かもしれない。",
            "emotions": ["不安"],
            "category": ["人間関係"],
        },
    )

    assert "energy_fatigue" in matrix["input_coverage_groups"]
    assert "relationship" in matrix["input_coverage_groups"]
    assert "limit_escape" in matrix["input_coverage_groups"]
    assert "anxiety" in matrix["input_coverage_groups"]
    assert "gate_quality" in matrix["technical_coverage_groups"]
    assert matrix["coverage_group_map"]["energy_fatigue"]["matched_from_input"] is True
    assert matrix["coverage_group_map"]["gate_quality"]["reason_codes"] == ["reader_readability"]


def test_coverage_matrix_maps_scope_complexity_to_long_meaning_arc():
    matrix = build_emlis_coverage_matrix(
        diagnostic_summary={
            "observation_status": "unavailable",
            "stage": "scope",
            "primary_reason": "limited_scope_multiple_core_tension",
            "secondary_reasons": ["limited_scope_multiple_core_tension"],
            "scope_coverage_matrix_hints": ["scope_complexity"],
            "scope_diagnostic": {
                "reason_codes": ["limited_scope_multiple_core_tension"],
                "reason_categories": ["relation_complexity"],
                "coverage_matrix_hints": ["scope_complexity"],
            },
        },
        current_input={"memo": "考えることが多すぎて、いくつも気持ちが重なっている。"},
    )

    assert "long_meaning_arc" in matrix["coverage_groups"]
    assert "scope_contract" in matrix["technical_coverage_groups"]
    assert "long_meaning_arc" in matrix["input_coverage_groups"] or matrix["coverage_group_map"]["long_meaning_arc"]["reason_count"] > 0
    assert matrix["coverage_group_map"]["long_meaning_arc"]["target_step"] == "Step12 SentencePlan拡張 / Step15 共通Core安定化"


def test_coverage_matrix_keeps_unclassified_reasons_visible():
    matrix = build_emlis_coverage_matrix(
        diagnostic_summary={
            "observation_status": "unavailable",
            "stage": "composer",
            "primary_reason": "new_unknown_reason_code_for_future_case",
            "secondary_reasons": ["new_unknown_reason_code_for_future_case"],
        },
        current_input={"memo": "短い"},
    )

    assert "new_unknown_reason_code_for_future_case" in matrix["unclassified_reasons"]
    assert matrix["unclassified_reason_count"] >= 1
    assert "scope_contract" in matrix["coverage_groups"]


def test_coverage_matrix_uses_step09_scope_expansion_groups():
    matrix = build_emlis_coverage_matrix(
        diagnostic_summary={
            "observation_status": "rejected",
            "stage": "grounding",
            "primary_reason": "unsupported_sentence",
            "scope_diagnostic": {
                "coverage_groups": ["anxiety", "limit_escape", "value_wish"],
                "scope_expansion": {
                    "version": "emlis.scope_expansion.v1",
                    "coverage_groups": ["anxiety", "limit_escape", "value_wish"],
                },
            },
            "gate_coverage_matrix_hints": ["grounding_unsupported"],
        },
        current_input={"memo": "短い"},
    )

    assert "anxiety" in matrix["input_coverage_groups"]
    assert "limit_escape" in matrix["input_coverage_groups"]
    assert "value_wish" in matrix["input_coverage_groups"]
    assert matrix["scope_expansion_groups"] == ["anxiety", "limit_escape", "value_wish"]
    assert "gate_quality" in matrix["technical_coverage_groups"]
