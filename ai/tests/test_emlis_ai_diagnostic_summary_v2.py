from __future__ import annotations

import pytest


SAMPLE_MEMO = """
ずっと家にいて、リラックスできて自分のことを優先して色々整えたりお家のことも出来るから嬉しいんだけど、ふっと気が抜けたときに現実と向き合うことがあるからその時にダメージでかい。
今の生活不便だな、と。
気をつけなきゃ行けないこと、全部無視して普通に生活したい。でもそうしたらもっと悪化する。
そんなの分かってる。たまに逃げ出したくなる。
"""

PASSING_TEXT = (
    "Mashさん、Emlisです。\n"
    "リラックスできて自分のことを優先できる嬉しさと、現実と向き合うダメージが同じ場所で重なっています。\n"
    "気をつけなきゃ行けないことを分かりながら普通に生活したい願いも離れていない中で、たまに逃げ出したくなる言葉は今の生活不便だなと感じる重さとつながっています。"
)


def _input(memo: str):
    return {
        "id": "diagnostic-v2-emotion",
        "created_at": "2026-05-15T00:00:00Z",
        "memo": memo,
        "memo_action": "",
        "emotion_details": [{"type": "自己理解", "strength": "medium"}],
        "emotions": ["自己理解"],
        "category": ["生活"],
    }


def _clear_limited_composer_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED",
        "COCOLON_EMLIS_AI_LIMITED_COMPOSER_ENABLED",
        "EMLIS_AI_LIMITED_COMPOSER_ENABLED",
        "COCOLON_LIMITED_COMPOSER_ENABLED",
        "COCOLON_EMLIS_AI_DEFAULT_LIMITED_COMPOSER_ENABLED",
        "EMLIS_AI_DEFAULT_LIMITED_COMPOSER_ENABLED",
        "COCOLON_EMLIS_DEFAULT_COMPOSER",
        "COCOLON_EMLIS_AI_DEFAULT_COMPOSER",
        "EMLIS_AI_DEFAULT_COMPOSER",
        "COCOLON_EMLIS_LIMITED_COMPOSER_ROLLOUT_STAGE",
        "COCOLON_EMLIS_AI_LIMITED_COMPOSER_ROLLOUT_STAGE",
        "EMLIS_AI_LIMITED_COMPOSER_ROLLOUT_STAGE",
        "COCOLON_EMLIS_LIMITED_COMPOSER_ROLLOUT",
        "EMLIS_AI_LIMITED_COMPOSER_ROLLOUT",
        "COCOLON_EMLIS_LIMITED_COMPOSER_INTERNAL_USER_IDS",
        "COCOLON_EMLIS_AI_LIMITED_COMPOSER_INTERNAL_USER_IDS",
        "EMLIS_AI_LIMITED_COMPOSER_INTERNAL_USER_IDS",
    ):
        monkeypatch.delenv(name, raising=False)


class _TextComposer:
    def __init__(self, text: str):
        self.text = text

    def generate(self, payload):
        return {
            "response_schema_version": "emlis.composer.response.v1",
            "composer_source": "ai_generated",
            "composer_model": "diagnostic_v2_fake_composer.v1",
            "generation_method": "test_composer",
            "generation_scope": "scoped_graph_only",
            "coverage_scope": "current_input_core",
            "fixed_string_renderer_used": False,
            "confidence": 0.91,
            "comment_text": self.text,
            "used_evidence_span_ids": [item["span_id"] for item in payload["evidence_spans"][:4]],
        }


class _BoundTextComposer(_TextComposer):
    def generate(self, payload):
        response = dict(super().generate(payload))
        evidence_ids = [item["span_id"] for item in payload["evidence_spans"][:2]]
        response["composer_meta"] = {
            "profile_key": "mixed_positive_anxiety",
            "sentence_binding_bundle": {
                "version": "emlis.sentence_binding_bundle.test.v1",
                "binding_version": "test.binding.v1",
                "binding_count": 2,
                "coverage_scope": "current_input_core",
                "profile_key": "mixed_positive_anxiety",
                "relation_taxonomy_version": "test.relation_taxonomy.v1",
                "bindings": [
                    {
                        "sentence_id": "s1",
                        "text": "diagnostic must not copy this text",
                        "line_role": "coexistence",
                        "relation_type": "coexistence",
                        "used_evidence_span_ids": evidence_ids[:1],
                        "used_phrase_unit_ids": ["pu_positive", "pu_impact"],
                        "coverage_scope": "current_input_core",
                        "must_include": True,
                    },
                    {
                        "sentence_id": "s2",
                        "text": "diagnostic must not copy this text either",
                        "line_role": "limit_escape",
                        "relation_type": "approach_avoidance",
                        "used_evidence_span_ids": evidence_ids[1:2],
                        "used_phrase_unit_ids": ["pu_limit", "pu_escape"],
                        "coverage_scope": "current_input_core",
                        "must_include": True,
                    },
                ],
            },
        }
        return response


def _assert_step2_contract(summary: dict):
    step2 = summary["step2_diagnostic_summary_extension"]
    assert step2["version"] == "emlis.limited_composer_diagnostic_summary_extension.v1"
    assert step2 == summary["diagnostic_summary_extension"]
    assert step2 == summary["diagnostic_summary_v2"]
    assert step2 == summary["limited_composer_diagnostic_summary_extension"]
    assert step2["stage"] == summary["stage"]
    assert step2["primary_reason"] == summary["primary_reason"]
    assert step2["coverage_group"] == summary["coverage_group"]
    assert step2["coverage_group"] == summary["coverage_primary_group"]
    assert isinstance(step2["coverage_groups"], list)
    assert isinstance(step2["gate_results"], dict)
    assert set(step2["gate_results"]) == {"reader", "grounding", "template_echo", "display"}
    assert isinstance(step2["binding"], dict)
    assert step2["binding"]["version"] == "emlis.limited_composer_binding_presence.v1"
    assert summary["binding_diagnostic"] == step2["binding"]
    assert summary["binding_missing"] == step2["binding_missing"]
    assert summary["binding_present"] == step2["binding_present"]
    assert summary["binding_count"] == step2["binding_count"]
    assert summary["expected_binding_count"] == step2["expected_binding_count"]
    assert summary["gate_binding_contract_version"] == "emlis.gate_binding_contract.v2"
    for gate_name, gate in summary["gate_results"].items():
        assert gate["gate_binding_contract_version"] == "emlis.gate_binding_contract.v2"
        assert gate["binding_contract_version"] == "emlis.gate_binding_contract.v2"
        assert isinstance(gate["binding_used"], bool)
        assert isinstance(gate["binding_available"], bool)
        assert isinstance(gate["binding_present"], bool)
        assert isinstance(gate["binding_required"], bool)
        assert isinstance(gate["binding_missing"], bool)
        assert gate["binding_support_source"] in {
            "none",
            "declared_evidence_binding",
            "declared_phrase_binding",
            "declared_relation_binding",
            "display_binding_aware_result",
        }
        if gate_name in {"reader", "template_echo"}:
            assert gate["binding_used"] is False
    assert step2["raw_input_required_for_debug"] is False
    assert step2["binding"]["raw_text_included"] is False


@pytest.mark.asyncio
async def test_step2_diagnostic_summary_extension_records_pre_connection_without_binding(monkeypatch):
    _clear_limited_composer_env(monkeypatch)
    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="diagnostic-v2-pre-connection-user",
        subscription_tier="free",
        current_input=_input(SAMPLE_MEMO),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    summary = reply.meta["diagnostic_summary"]
    _assert_step2_contract(summary)
    assert summary["stage"] == "flag"
    assert summary["failed_stage"] == "flag"
    assert summary["primary_reason"] == "default_limited_composer_feature_disabled"
    assert summary["binding_present"] is False
    assert summary["binding_missing"] is False
    assert summary["expected_binding_count"] == 0
    assert reply.meta["step2_diagnostic_summary_extension"] == summary["step2_diagnostic_summary_extension"]
    assert reply.meta["multi_perspective"]["step2_diagnostic_summary_extension"] == summary["step2_diagnostic_summary_extension"]
    assert reply.meta["multi_perspective"]["gate_trace"]["display_gate"]["binding_missing"] is False
    assert all(gate["binding_used"] is False for gate in summary["gate_results"].values())
    assert reply.comment_text == ""


@pytest.mark.asyncio
async def test_step2_diagnostic_summary_extension_marks_missing_binding_for_generated_body(monkeypatch):
    _clear_limited_composer_env(monkeypatch)
    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="diagnostic-v2-generated-missing-binding-user",
        subscription_tier="free",
        current_input=_input(SAMPLE_MEMO),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
        composer_client=_TextComposer(PASSING_TEXT),
    )

    summary = reply.meta["diagnostic_summary"]
    _assert_step2_contract(summary)
    assert summary["observation_status"] == "passed"
    assert summary["failed_stage"] == ""
    assert summary["coverage_group"]
    assert summary["expected_binding_count"] == 2
    assert summary["binding_count"] == 0
    assert summary["binding_present"] is False
    assert summary["binding_missing"] is True
    assert summary["binding_diagnostic"]["body_sentence_count"] == 2
    assert reply.meta["binding_diagnostic"] == summary["binding_diagnostic"]
    assert reply.meta["multi_perspective"]["gate_trace"]["display_gate"]["binding_required"] is True
    assert reply.meta["multi_perspective"]["gate_trace"]["display_gate"]["binding_missing"] is True
    assert summary["gate_results"]["reader"]["binding_required"] is False
    assert summary["gate_results"]["template_echo"]["binding_required"] is False
    assert summary["gate_results"]["grounding"]["binding_required"] is True
    assert summary["gate_results"]["display"]["binding_required"] is True
    assert all(gate["binding_used"] is False for gate in summary["gate_results"].values())
    assert reply.comment_text == PASSING_TEXT


@pytest.mark.asyncio
async def test_step2_diagnostic_summary_extension_uses_sanitized_sentence_bindings(monkeypatch):
    _clear_limited_composer_env(monkeypatch)
    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="diagnostic-v2-generated-bound-user",
        subscription_tier="free",
        current_input=_input(SAMPLE_MEMO),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
        composer_client=_BoundTextComposer(PASSING_TEXT),
    )

    summary = reply.meta["diagnostic_summary"]
    _assert_step2_contract(summary)
    binding = summary["binding_diagnostic"]
    assert summary["observation_status"] == "passed"
    assert summary["expected_binding_count"] == 2
    assert summary["binding_count"] == 2
    assert summary["binding_present"] is True
    assert summary["binding_missing"] is False
    assert binding["relation_types"] == ["coexistence", "approach_avoidance"]
    assert binding["used_phrase_unit_count"] == 4
    assert binding["binding_source"] == "sentence_binding_bundle"
    assert binding["relation_taxonomy_version"] == "test.relation_taxonomy.v1"
    assert all("text" not in row for row in binding["binding_rows_sanitized"])
    assert all(gate["binding_available"] is True for gate in summary["gate_results"].values())
    assert summary["gate_results"]["reader"]["binding_used"] is False
    assert summary["gate_results"]["grounding"]["binding_used"] is True
    assert summary["gate_results"]["grounding"]["binding_support_source"] in {"declared_relation_binding", "declared_phrase_binding", "declared_evidence_binding"}
    assert summary["gate_results"]["template_echo"]["binding_used"] is False
    assert summary["gate_results"]["display"]["binding_used"] is True
    assert summary["gate_results"]["display"]["binding_support_source"] == "display_binding_aware_result"
    assert reply.meta["multi_perspective"]["gate_trace"]["display_gate"]["binding_present"] is True
    assert reply.meta["multi_perspective"]["gate_trace"]["display_gate"]["binding_missing"] is False
    assert reply.meta["multi_perspective"]["diagnostic_summary"] == summary
