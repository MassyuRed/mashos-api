from __future__ import annotations

from astor_self_structure_report import _build_myprofile_report_content_json


def _basis():
    return {
        "target_role_map": [
            {
                "target_key": "work",
                "target_label_ja": "仕事",
                "target_type": "environment",
                "role_key": "organizer",
                "role_label_ja": "整える役割",
                "score": 0.9,
                "evidence_count": 9,
                "top_action_keys": ["prioritize"],
            }
        ],
        "action_patterns": [{"key": "prioritize", "label_ja": "先に整理する"}],
        "role_gaps": [],
        "question_candidates": [],
        "identity_snapshot_excerpt": {"target_role_scores": []},
        "emotion_bridge": {"top_emotions": []},
    }


def _analysis_set():
    return {
        "standard_row": {
            "id": "std-1",
            "payload": {
                "standardReport": {
                    "summary": {"core_role": {"key": "organizer", "label_ja": "整える役割"}},
                    "top_roles": [],
                    "top_targets": [],
                }
            },
        },
        "deep_row": {
            "id": "deep-1",
            "payload": {
                "deepReport": {
                    "generated_roles": [],
                }
            },
        },
        "refs": {"standard": {"id": "std-1"}, "deep": {"id": "deep-1"}},
    }


def test_report_content_json_adds_watashi_map_without_removing_legacy_payloads():
    content = _build_myprofile_report_content_json(
        report_mode="deep",
        report_type="latest",
        period="28d",
        period_start="2026-05-01T00:00:00Z",
        period_end="2026-05-28T00:00:00Z",
        distribution_utc="2026-05-28T00:00:00Z",
        self_structure_set=_analysis_set(),
        emotion_bridge_set={"standard_row": None, "deep_row": None, "refs": {}},
        basis=_basis(),
        sections={"current_structure": ["仕事の場面では、整える役割が立ち上がりやすく見えます。"]},
        generated_at_server="2026-05-28T00:00:00Z",
    )

    assert content["version"] == "myprofile.report.v5"
    assert content["watashiMap"]["version"] == "watashi.map.v1"
    assert content["watashiMap"]["report_mode"] == "deep"
    assert content["watashiMap"]["overview"]["title"] == "今のわたしマップ"
    assert content["watashiMap"]["role_switches"][0]["context"]["label"] == "仕事"
    assert "standardReport" in content
    assert "deepReport" in content
    assert "selfStructureDeepVisual" in content
    assert "watashi.map.v1" in content.get("visual_contracts", [])


def test_report_content_json_light_watashi_map_is_free_locked():
    content = _build_myprofile_report_content_json(
        report_mode="light",
        report_type="latest",
        period="28d",
        period_start="2026-05-01T00:00:00Z",
        period_end="2026-05-28T00:00:00Z",
        distribution_utc="2026-05-28T00:00:00Z",
        self_structure_set=_analysis_set(),
        emotion_bridge_set={"standard_row": None, "deep_row": None, "refs": {}},
        basis=_basis(),
        sections={"current_structure": ["仕事の場面では、整える役割が立ち上がりやすく見えます。"]},
        generated_at_server="2026-05-28T00:00:00Z",
    )

    watashi_map = content["watashiMap"]
    assert watashi_map["report_mode"] == "light"
    assert watashi_map["visibility"]["viewer_tier"] == "free"
    assert watashi_map["routes"] == []
    assert watashi_map["crossroads"] == []
    assert watashi_map["detail_report"]["visible"] is False
    assert content["lightReport"]["detail_report_locked"] is True
