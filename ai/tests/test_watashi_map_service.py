from __future__ import annotations

from watashi_map_service import build_watashi_map, build_watashi_map_from_content_json


def _basis():
    return {
        "target_role_map": [
            {
                "target_key": "work",
                "target_label_ja": "仕事",
                "target_type": "environment",
                "role_key": "organizer",
                "role_label_ja": "整える役割",
                "score": 0.82,
                "evidence_count": 8,
                "top_action_keys": ["prioritize"],
            },
            {
                "target_key": "family",
                "target_label_ja": "家族",
                "target_type": "person",
                "role_key": "listener",
                "role_label_ja": "受け止める役割",
                "score": 0.52,
                "evidence_count": 4,
                "top_action_keys": ["listen"],
            },
        ],
        "action_patterns": [{"key": "prioritize", "label_ja": "先に整理する"}],
        "role_gaps": [
            {
                "target_key": "work",
                "target_label_ja": "仕事",
                "left_role_label_ja": "落ち着いていたい役割",
                "right_role_label_ja": "進める役割",
                "desired_role_label_ja": "余白を持って関わる役割",
            }
        ],
        "question_candidates": [
            {
                "target_key": "friends",
                "target_label_ja": "友人との場面",
                "reason": "入力がまだ少なく、役割を言い切らない状態です。",
                "hint": "次に友人との関わりを入力すると、地図が見えやすくなります。",
            }
        ],
    }


def test_build_watashi_map_standard_payload_has_required_sections_without_type_claim():
    payload = build_watashi_map(
        _basis(),
        report_mode="standard",
        viewer_tier="plus",
        period="28d",
        sections={"current_structure": ["仕事の場面では、整える役割が立ち上がりやすく見えます。"]},
    )

    assert payload["version"] == "watashi.map.v1"
    assert payload["status"] == "ok"
    assert payload["label"] == "わたしマップ"
    assert payload["overview"]["title"] == "今のわたしマップ"
    assert payload["role_switches"][0]["context"]["label"] == "仕事"
    assert payload["role_switches"][0]["role"]["label"] == "整える役割"
    assert payload["routes"][0]["steps"][1]["label"] == "役割スイッチ"
    assert payload["crossroads"][0]["context"]["label"] == "仕事"
    assert payload["unknown_areas"][0]["label"] == "友人との場面"
    assert "タイプ" not in payload["overview"]["summary"]
    assert payload["detail_report"]["visible"] is True


def test_build_watashi_map_light_is_free_safe_and_locks_deep_sections():
    payload = build_watashi_map(_basis(), report_mode="light", viewer_tier="free", period="28d")

    assert payload["visibility"]["viewer_tier"] == "free"
    assert payload["visibility"]["detail_report_visible"] is False
    assert payload["routes"] == []
    assert payload["crossroads"] == []
    assert len(payload["role_switches"]) <= 2
    assert "detail_report" in payload["visibility"]["locked_sections"]
    assert payload["detail_report"]["lock_label"] == "詳しい自己分析レポートは Plus プラン以上で読めます。"


def test_build_watashi_map_from_existing_deep_content_projects_to_light():
    deep = build_watashi_map(_basis(), report_mode="deep", viewer_tier="premium", period="28d")

    projected = build_watashi_map_from_content_json(
        {"watashiMap": deep, "distribution": {"period": "28d"}},
        report_mode="light",
        viewer_tier="free",
    )

    assert projected["report_mode"] == "light"
    assert projected["visibility"]["viewer_tier"] == "free"
    assert projected["routes"] == []
    assert projected["crossroads"] == []
    assert projected["detail_report"]["visible"] is False


def test_build_watashi_map_from_legacy_summary_keeps_light_entry():
    projected = build_watashi_map_from_content_json(
        {
            "summaryText": "仕事の場面では、整える役割が立ち上がりやすく見えます。",
            "distribution": {"period": "28d"},
        },
        report_mode="light",
        viewer_tier="free",
    )

    assert projected["version"] == "watashi.map.v1"
    assert projected["overview"]["summary"] == "仕事の場面では、整える役割が立ち上がりやすく見えます。"
    assert projected["visibility"]["summary_visible"] is True
