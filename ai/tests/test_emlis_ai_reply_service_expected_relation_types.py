from __future__ import annotations

from types import SimpleNamespace

import emlis_ai_reply_service as reply_service


def test_expected_relation_types_for_reader_uses_binding_sources_and_filters_edge_ids() -> None:
    candidate = SimpleNamespace(
        composer_meta={
            "sentence_binding_bundle": {
                "relation_types": ["positive_recovery", "conflict.e1", "coexistence"],
                "bindings": [
                    {"relation_type": "contrast"},
                    {"canonical_relation_type": "pressure"},
                ],
            },
            "sentence_bindings": [
                {"relation_type": "approach_avoidance"},
            ],
            "relation_types": ["progress", "relation_12"],
            "used_relation_ids": ["conflict.e2", "residue"],
        },
        used_relation_ids=["edge_99", "limit"],
    )

    assert reply_service._expected_relation_types_for_reader(candidate) == [
        "recovery",
        "coexistence",
        "contrast",
        "pressure",
        "approach_avoidance",
        "residue",
        "limit",
    ]


def test_expected_relation_types_for_reader_does_not_treat_edge_ids_as_relation_types() -> None:
    candidate = SimpleNamespace(
        composer_meta={
            "relation_types": [],
            "used_relation_ids": ["conflict.e1", "edge_1", "relation_2"],
        },
        used_relation_ids=["rel-3"],
    )

    assert reply_service._expected_relation_types_for_reader(candidate) == []


def test_reply_reader_judge_receives_expected_relation_types(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_reader(comment_text, *, expected_relation_types=()):
        captured["comment_text"] = comment_text
        captured["expected_relation_types"] = list(expected_relation_types)
        return {"ok": True}

    monkeypatch.setattr(reply_service, "judge_listener_readability", fake_reader)
    candidate = SimpleNamespace(
        composer_meta={"sentence_binding_bundle": {"relation_types": ["positive_recovery"]}},
        used_relation_ids=[],
    )

    assert reply_service._judge_listener_readability_for_reply("Emlisです。", candidate) == {"ok": True}
    assert captured == {
        "comment_text": "Emlisです。",
        "expected_relation_types": ["recovery"],
    }


def test_reply_reader_judge_falls_back_for_legacy_one_argument_test_doubles(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_reader(comment_text):
        captured["comment_text"] = comment_text
        return {"ok": True}

    monkeypatch.setattr(reply_service, "judge_listener_readability", fake_reader)
    candidate = SimpleNamespace(
        composer_meta={"sentence_binding_bundle": {"relation_types": ["positive_recovery"]}},
        used_relation_ids=[],
    )

    assert reply_service._judge_listener_readability_for_reply("Emlisです。", candidate) == {"ok": True}
    assert captured == {"comment_text": "Emlisです。"}
