from __future__ import annotations

from emlis_ai_limited_composer_client import CocolonLimitedComposerClient
from emlis_ai_limited_relation_taxonomy import LIMITED_RELATION_TAXONOMY_VERSION, allowed_relation_types
from test_emlis_ai_limited_composer_client import _step04_payload


def _result_for(evidence: list[dict]) -> dict:
    payload = _step04_payload(evidence)
    payload["observation_graph"]["primary_state"]["evidence_span_ids"] = [item["span_id"] for item in evidence]
    return CocolonLimitedComposerClient().generate(payload)


def _assert_step5_relation_taxonomy_contract(result: dict) -> dict:
    assert result["composer_source"] == "ai_generated"
    meta = result["composer_meta"]
    bundle = result["sentence_binding_bundle"]
    taxonomy = meta["step5_relation_taxonomy"]

    assert taxonomy == meta["relation_taxonomy"]
    assert taxonomy == meta["limited_composer_relation_taxonomy"]
    assert bundle["step5_relation_taxonomy"] == taxonomy
    assert bundle["relation_taxonomy"] == taxonomy
    assert taxonomy["version"] == LIMITED_RELATION_TAXONOMY_VERSION
    assert taxonomy["target_step"] == "5_relation_taxonomy_addition"
    assert taxonomy["relation_taxonomy_added"] is True
    assert taxonomy["relation_not_expressed_traceable"] is True
    assert taxonomy["all_relation_types_mapped"] is True
    assert taxonomy["unmapped_relation_types"] == []
    assert taxonomy["raw_text_included"] is False
    assert taxonomy["completion_sentence_templates_added"] is False
    assert taxonomy["input_specific_template_added"] is False
    assert "contrast" in taxonomy["allowed_relation_types"]
    assert "coexistence" in taxonomy["allowed_relation_types"]
    assert "pressure" in taxonomy["allowed_relation_types"]
    assert "recovery" in taxonomy["allowed_relation_types"]
    assert "approach_avoidance" in taxonomy["allowed_relation_types"]
    assert set(bundle["relation_types"]).issubset(set(allowed_relation_types()))
    assert set(meta["relation_types"]) == set(bundle["relation_types"])
    assert meta["relation_taxonomy_version"] == LIMITED_RELATION_TAXONOMY_VERSION
    assert meta["relation_taxonomy_added"] is True
    assert meta["relation_not_expressed_traceable"] is True
    assert meta["all_relation_types_mapped"] is True
    assert meta["composer_diagnostic"]["step5_relation_taxonomy"] == taxonomy
    assert meta["composer_diagnostic"]["relation_taxonomy_version"] == LIMITED_RELATION_TAXONOMY_VERSION
    assert meta["text_generation_core"]["payload"]["sentence_binding_count"] == bundle["binding_count"]
    assert meta["text_generation_core"]["step5_relation_taxonomy"] == taxonomy
    return taxonomy


def test_step5_relation_taxonomy_attaches_structural_meta_to_full_profile_candidate() -> None:
    result = _result_for(
        [
            {"span_id": "se1", "raw_text": "朝から疲れが溜まっていて体力が残っていない。", "detected_type": "event", "source_field": "memo"},
            {"span_id": "se2", "raw_text": "資料を直そうとしても頭が回らず、集中が切れている。", "detected_type": "event", "source_field": "memo"},
            {"span_id": "se3", "raw_text": "途中でお茶を飲んだら少し落ち着いた。", "detected_type": "event", "source_field": "memo"},
        ]
    )

    taxonomy = _assert_step5_relation_taxonomy_contract(result)
    assert result["composer_meta"]["profile_key"] == "energy_fatigue"
    assert "pressure" in taxonomy["relation_types"]
    assert "coexistence" in taxonomy["relation_types"]
    assert "pressure_or_load" in taxonomy["relation_families"]
    assert taxonomy["major_coverage_group_relation_unset"] is False
    assert taxonomy["coverage_group"] == "energy_fatigue_pressure"


def test_step5_relation_taxonomy_maps_current_input_core_without_raw_text() -> None:
    result = _result_for(
        [
            {"span_id": "sh1", "raw_text": "今日は仕事で疲れた。", "detected_type": "event", "source_field": "memo"},
            {"span_id": "sh2", "raw_text": "お茶を飲んで少し落ち着いた。", "detected_type": "event", "source_field": "memo"},
        ]
    )

    taxonomy = _assert_step5_relation_taxonomy_contract(result)
    assert result["coverage_scope"] == "current_input_core"
    assert taxonomy["coverage_group"] == "current_input_core"
    assert "center" in taxonomy["relation_types"]
    assert all("text" not in row for row in taxonomy["binding_relation_rows"])


def test_step5_relation_taxonomy_covers_approach_avoidance_and_long_arc_profiles() -> None:
    cases = [
        (
            "relationship_approach_avoidance",
            [
                {"span_id": "ra1", "raw_text": "本当は相談したいし助けを借りたい。", "detected_type": "event", "source_field": "memo"},
                {"span_id": "ra2", "raw_text": "でも相手の時間を奪うのが怖くて、嫌われたり重いと思われそうで言い出せない。", "detected_type": "event", "source_field": "memo"},
                {"span_id": "ra3", "raw_text": "一人で抱えるのは限界に近い。", "detected_type": "event", "source_field": "memo"},
            ],
            {"approach", "approach_avoidance", "limit"},
        ),
        (
            "long_meaning_arc",
            [
                {"span_id": "la1", "raw_text": "朝から疲れが溜まっていて、予定も詰まっていて頭が回らない。", "detected_type": "event", "source_field": "memo"},
                {"span_id": "la2", "raw_text": "本当は大事にしたい作業を選びたいけれど、休みたい気持ちも強い。", "detected_type": "event", "source_field": "memo"},
                {"span_id": "la3", "raw_text": "少しだけ机を整えてお茶を飲んだら、少し落ち着いた。", "detected_type": "event", "source_field": "memo"},
                {"span_id": "la4", "raw_text": "このまま一人で抱えるのは限界に近い。", "detected_type": "event", "source_field": "memo"},
            ],
            {"pressure", "tension"},
        ),
    ]

    for expected_profile, evidence, expected_relations in cases:
        result = _result_for(evidence)
        taxonomy = _assert_step5_relation_taxonomy_contract(result)
        assert result["composer_meta"]["profile_key"] == expected_profile
        assert expected_relations.issubset(set(taxonomy["relation_types"]))
        assert taxonomy["missing_expected_relation_families"] == []
