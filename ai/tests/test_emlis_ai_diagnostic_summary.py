from __future__ import annotations

import pytest

from emlis_ai_display_gate import build_emlis_gate_trace
from emlis_ai_listener_reader_judge import judge_listener_readability
from emlis_ai_grounding_judge import judge_grounding
from emlis_ai_template_echo_guard import guard_template_echo


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

PASSING_PUBLIC_TEXT = (
    "Mashさん、Emlisです。\n"
    "今回の入力では、リラックスできて自分のことを優先できる嬉しさと、現実と向き合うダメージが同じ場所で重なっています。\n"
    "気をつけなきゃ行けないことを分かりながら普通に生活したい願いも離れていない中で、たまに逃げ出したくなる言葉は今の生活不便だなと感じる重さとつながっています。"
)

TEMPLATE_TEXT = (
    "Mashさん、Emlisです。\n"
    "入力全体では、『悲しみ』が中心に出ています。\n"
    "言葉の流れには、外からは見えにくい緊張が含まれています。\n"
    "Emlisは、『悲しみ』を急いで片づけず、今の言葉として一緒に見ます。"
)


def _input(memo: str):
    return {
        "id": "diagnostic-emotion",
        "created_at": "2026-05-14T00:00:00Z",
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


def _assert_summary_contract(summary: dict):
    assert summary["version"] == "emlis.diagnostic_summary.v1"
    assert summary["observation_status"] in {"passed", "rejected", "unavailable", "safety_blocked"}
    assert summary["stage"] in {"flag", "rollout", "scope", "composer", "reader", "grounding", "template", "display"}
    assert isinstance(summary["primary_reason"], str)
    assert summary["primary_reason"]
    assert isinstance(summary["secondary_reasons"], list)
    assert isinstance(summary["feature_flag_enabled"], bool)
    assert isinstance(summary["rollout_stage"], str)
    assert isinstance(summary["scope_status"], str)
    assert isinstance(summary["coverage_scope"], str)
    assert isinstance(summary["scope_diagnostic"], dict)
    assert isinstance(summary["scope_rejection_reasons"], list)
    assert isinstance(summary["scope_safety_boundaries"], list)
    assert isinstance(summary["scope_excluded_reason_codes"], list)
    assert isinstance(summary["scope_reason_category"], str)
    assert isinstance(summary["scope_coverage_matrix_hints"], list)
    assert isinstance(summary["composer_model"], str)
    assert isinstance(summary["composer_status"], str)
    assert isinstance(summary["composer_diagnostic"], dict)
    assert isinstance(summary["composer_rejection_reasons"], list)
    assert isinstance(summary["composer_reason_category"], str)
    assert isinstance(summary["composer_coverage_matrix_hints"], list)
    assert isinstance(summary["gate_diagnostic"], dict)
    assert isinstance(summary["gate_rejection_reasons"], list)
    assert isinstance(summary["gate_reason_category"], str)
    assert isinstance(summary["gate_coverage_matrix_hints"], list)
    assert isinstance(summary["gate_failure_stage"], str)
    assert isinstance(summary["coverage_matrix"], dict)
    assert summary["coverage_matrix"].get("version") == "emlis.coverage_matrix.v1"
    assert isinstance(summary["coverage_groups"], list)
    assert isinstance(summary["coverage_primary_group"], str)
    assert isinstance(summary["coverage_next_steps"], list)
    assert isinstance(summary["coverage_unclassified_reasons"], list)
    assert isinstance(summary["coverage_unmapped_reasons"], list)
    assert summary["gate_diagnostic"].get("version") == "emlis.gate_diagnostic.v1"
    assert isinstance(summary["used_evidence_span_count"], int)
    assert isinstance(summary["included_claim_count"], int)
    assert isinstance(summary["excluded_claim_count"], int)
    assert isinstance(summary["comment_text_allowed"], bool)
    assert isinstance(summary["feature_flag_state"], dict)
    assert isinstance(summary["release_decision"], dict)
    assert isinstance(summary["default_composer_resolution"], dict)
    assert isinstance(summary["rollout_decision"], dict)
    assert isinstance(summary["registry_resolution"], dict)
    assert isinstance(summary["pre_connection"], dict)
    assert isinstance(summary["b_plan_connection"], dict)
    assert summary["b_plan_connection"].get("version") == "emlis.b_plan_normal_connection.v1"
    assert isinstance(summary["release_enabled"], bool)
    assert isinstance(summary["release_cohort"], str)
    assert isinstance(summary["release_reason_code"], str)
    assert isinstance(summary["composer_connection_attempted"], bool)
    assert isinstance(summary["rollout_attempted"], bool)
    assert summary["pre_connection"].get("version") == "emlis.pre_connection_diagnostic.v1"
    assert summary["pre_connection"].get("b_plan_connection") == summary["b_plan_connection"]
    assert set(summary["gate_results"]) == {"reader", "grounding", "template_echo", "display", "visible_surface_acceptance"}
    for gate in summary["gate_results"].values():
        assert isinstance(gate["passed"], bool)
        assert isinstance(gate["primary_reason"], str)
        assert isinstance(gate["rejection_reasons"], list)
        assert isinstance(gate["reason_category"], str)
        assert isinstance(gate["diagnostics"], dict)


class _TextComposer:
    def __init__(self, text: str):
        self.text = text

    def generate(self, payload):
        return {
            "response_schema_version": "emlis.composer.response.v1",
            "composer_source": "ai_generated",
            "composer_model": "diagnostic_fake_composer.v1",
            "generation_method": "test_composer",
            "generation_scope": "scoped_graph_only",
            "coverage_scope": "current_input_core",
            "fixed_string_renderer_used": False,
            "confidence": 0.91,
            "comment_text": self.text,
            "used_evidence_span_ids": [item["span_id"] for item in payload["evidence_spans"][:4]],
        }


@pytest.mark.asyncio
async def test_diagnostic_summary_exists_for_feature_flag_unavailable(monkeypatch):
    _clear_limited_composer_env(monkeypatch)
    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="diagnostic-flag-user",
        subscription_tier="free",
        current_input=_input(SAMPLE_MEMO),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    summary = reply.meta["diagnostic_summary"]
    _assert_summary_contract(summary)
    assert summary == reply.meta["multi_perspective"]["diagnostic_summary"]
    assert summary["observation_status"] == "unavailable"
    assert summary["stage"] == "flag"
    assert summary["primary_reason"] == "default_limited_composer_feature_disabled"
    assert summary["feature_flag_enabled"] is False
    assert summary["feature_flag_state"]["enabled"] is False
    assert summary["release_decision"]["reason_code"] == "feature_flag_disabled"
    assert summary["registry_resolution"]["connection_status"] == "blocked_feature_flag"
    assert summary["composer_connection_attempted"] is False
    assert summary["rollout_attempted"] is False
    assert summary["comment_text_allowed"] is False
    assert reply.comment_text == ""


@pytest.mark.asyncio
async def test_diagnostic_summary_exists_for_passed_candidate(monkeypatch):
    _clear_limited_composer_env(monkeypatch)
    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="diagnostic-passed-user",
        subscription_tier="free",
        current_input=_input(SAMPLE_MEMO),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
        composer_client=_TextComposer(PASSING_TEXT),
    )

    summary = reply.meta["diagnostic_summary"]
    _assert_summary_contract(summary)
    assert summary["observation_status"] == "passed"
    assert summary["stage"] == "display"
    assert summary["primary_reason"] == "passed"
    assert summary["composer_status"] == "generated"
    assert summary["comment_text_allowed"] is True
    assert summary["gate_results"]["display"]["passed"] is True
    assert reply.comment_text == PASSING_PUBLIC_TEXT


@pytest.mark.asyncio
async def test_diagnostic_summary_exists_for_rejected_candidate(monkeypatch):
    _clear_limited_composer_env(monkeypatch)
    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="diagnostic-rejected-user",
        subscription_tier="free",
        current_input=_input("悲しい。何かしてあげたいけど出来なくてゲンナリする。"),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
        composer_client=_TextComposer(TEMPLATE_TEXT),
    )

    summary = reply.meta["diagnostic_summary"]
    _assert_summary_contract(summary)
    assert summary["observation_status"] == "rejected"
    assert summary["stage"] in {"reader", "grounding", "template", "display"}
    assert summary["composer_status"] == "generated"
    assert summary["comment_text_allowed"] is False
    assert reply.comment_text == ""


@pytest.mark.asyncio
async def test_diagnostic_summary_exists_for_safety_blocked(monkeypatch):
    _clear_limited_composer_env(monkeypatch)
    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="diagnostic-safety-user",
        subscription_tier="free",
        current_input=_input("消えたい気持ちが強い"),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
        composer_client=_TextComposer(PASSING_TEXT),
    )

    summary = reply.meta["diagnostic_summary"]
    _assert_summary_contract(summary)
    assert summary["observation_status"] == "safety_blocked"
    assert summary["stage"] == "scope"
    assert summary["primary_reason"] == "safety_boundary"
    assert summary["scope_status"] == "safety_blocked"
    assert summary["scope_diagnostic"]["scope_status"] == "safety_blocked"
    assert summary["scope_diagnostic"]["coverage_matrix_hint"] == "safety_boundary"
    assert summary["scope_safety_boundaries"]
    assert "safety_boundary" in summary["scope_coverage_matrix_hints"]
    assert summary["comment_text_allowed"] is False
    assert reply.comment_text == ""


@pytest.mark.asyncio
async def test_step03_scope_diagnostic_records_eligible_scope(monkeypatch):
    _clear_limited_composer_env(monkeypatch)
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED", "true")
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ROLLOUT_STAGE", "all")
    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="diagnostic-step03-eligible-user",
        subscription_tier="free",
        current_input=_input(SAMPLE_MEMO),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    summary = reply.meta["diagnostic_summary"]
    _assert_summary_contract(summary)
    diagnostic = summary["scope_diagnostic"]
    assert diagnostic["version"] == "emlis.scope_diagnostic.v1"
    assert diagnostic["scope_attempted"] is True
    assert diagnostic["scope_status"] == "eligible"
    assert diagnostic["scope_ready_for_composer"] is True
    assert summary["scope_status"] == "eligible"
    assert summary["coverage_scope"] in {"partial_observation", "current_input_core"}
    assert diagnostic["included_claim_count"] == summary["included_claim_count"]
    assert diagnostic["excluded_claim_count"] == summary["excluded_claim_count"]
    assert isinstance(diagnostic["excluded_reason_counts"], dict)
    assert isinstance(diagnostic["excluded_source_counts"], dict)
    assert summary["scope_safety_boundaries"] == []
    assert summary["scope_coverage_matrix_hints"]


@pytest.mark.asyncio
async def test_step03_scope_diagnostic_records_out_of_scope_reason(monkeypatch):
    _clear_limited_composer_env(monkeypatch)
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED", "true")
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ROLLOUT_STAGE", "all")
    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="diagnostic-step03-out-of-scope-user",
        subscription_tier="free",
        current_input=_input(""),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    summary = reply.meta["diagnostic_summary"]
    _assert_summary_contract(summary)
    diagnostic = summary["scope_diagnostic"]
    assert summary["stage"] == "display"
    assert summary["scope_status"] == "out_of_scope"
    assert summary["primary_reason"] == "passed"
    assert diagnostic["scope_status"] == "out_of_scope"
    assert diagnostic["scope_ready_for_composer"] is False
    assert diagnostic["included_claim_count"] == 0
    assert diagnostic["out_of_scope_reason"] == "limited_scope_no_grounded_primary_state"
    assert "limited_scope_no_grounded_primary_state" in summary["scope_rejection_reasons"]
    assert "no_grounded_primary_state" in summary["scope_excluded_reason_codes"]
    assert summary["scope_reason_category"] == "primary_state"
    assert "primary_state_grounding" in summary["scope_coverage_matrix_hints"]
    assert summary["observation_status"] == "passed"
    assert summary["comment_text_allowed"] is True
    assert reply.comment_text
    assert "詳しく残せそうなら" in reply.comment_text


@pytest.mark.asyncio
async def test_step03_diagnostic_summary_classifies_out_of_scope_scope_reason(monkeypatch):
    _clear_limited_composer_env(monkeypatch)
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED", "true")
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ROLLOUT_STAGE", "all")
    from emlis_ai_reply_service import render_emlis_ai_reply

    payload = _input("")
    payload["emotion_details"] = []
    payload["emotions"] = []
    payload["category"] = []

    reply = await render_emlis_ai_reply(
        user_id="diagnostic-scope-out-of-scope-user",
        subscription_tier="free",
        current_input=payload,
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    summary = reply.meta["diagnostic_summary"]
    _assert_summary_contract(summary)
    assert summary["observation_status"] == "unavailable"
    assert summary["stage"] == "scope"
    assert summary["scope_status"] == "out_of_scope"
    assert summary["scope_diagnostic"]["scope_status"] == "out_of_scope"
    assert summary["scope_diagnostic"]["scope_ready_for_composer"] is False
    assert summary["scope_diagnostic"]["included_claim_count"] == 0
    assert summary["scope_diagnostic"]["coverage_matrix_hint"] == "required_structure"
    assert "limited_scope_required_structure_missing" in summary["scope_rejection_reasons"]
    assert summary["scope_reason_category"] == "required_structure"
    assert "required_structure" in summary["scope_coverage_matrix_hints"]
    assert summary["comment_text_allowed"] is False
    assert reply.comment_text == ""

@pytest.mark.asyncio
async def test_step02_diagnostic_summary_marks_rollout_off_before_composer(monkeypatch):
    _clear_limited_composer_env(monkeypatch)
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED", "true")
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ROLLOUT_STAGE", "off")
    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="diagnostic-rollout-off-user",
        subscription_tier="free",
        current_input=_input(SAMPLE_MEMO),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    summary = reply.meta["diagnostic_summary"]
    _assert_summary_contract(summary)
    assert summary["stage"] == "rollout"
    assert summary["feature_flag_enabled"] is True
    assert summary["feature_flag_state"]["set_flags"]["COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED"] == "true"
    assert summary["rollout_stage"] == "off"
    assert summary["release_enabled"] is False
    assert summary["release_reason_code"] == "rollout_stage_off"
    assert summary["rollout_decision"]["stage"] == "off"
    assert summary["rollout_decision"]["enabled"] is False
    assert summary["registry_resolution"]["connection_status"] == "blocked_rollout"
    assert summary["default_composer_resolution"]["release_allowed"] is False
    assert summary["composer_connection_attempted"] is False
    assert summary["rollout_attempted"] is False
    assert summary["pre_connection"]["blocked_before_composer"] is True
    b_plan = summary["b_plan_connection"]
    assert b_plan["decision"] == "blocked_rollout"
    assert b_plan["registry_connection_status"] == "blocked_rollout"
    assert b_plan["environment_blocked"] is True
    assert b_plan["generator_or_gate_path"] is False
    assert b_plan["blocked_before_composer"] is True
    assert b_plan["status_family"] == "environment_blocked"
    assert b_plan["diagnostic_consistent"] is True
    assert reply.comment_text == ""


@pytest.mark.asyncio
async def test_step02_diagnostic_summary_marks_internal_rollout_block(monkeypatch):
    _clear_limited_composer_env(monkeypatch)
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED", "true")
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ROLLOUT_STAGE", "internal")
    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="diagnostic-not-internal-user",
        subscription_tier="free",
        current_input=_input(SAMPLE_MEMO),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    summary = reply.meta["diagnostic_summary"]
    _assert_summary_contract(summary)
    assert summary["stage"] == "rollout"
    assert summary["rollout_stage"] == "internal"
    assert summary["release_decision"]["enabled"] is False
    assert summary["release_decision"]["reason_code"] == "rollout_stage_not_matched"
    assert "limited_composer_rollout_not_allowed" in summary["release_decision"]["rejection_reasons"]
    assert summary["registry_resolution"]["connection_status"] == "blocked_rollout"
    assert summary["composer_connection_attempted"] is False
    b_plan = summary["b_plan_connection"]
    assert b_plan["decision"] == "blocked_rollout"
    assert b_plan["registry_connection_status"] == "blocked_rollout"
    assert b_plan["release_reason_code"] == "rollout_stage_not_matched"
    assert b_plan["environment_blocked"] is True
    assert b_plan["diagnostic_consistent"] is True
    assert reply.comment_text == ""


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "stage,user_id,input_extra,internal_ids,expected_cohort",
    [
        ("internal", "diagnostic-internal-user", {}, "diagnostic-internal-user", "internal"),
        ("tutorial", "diagnostic-tutorial-user", {"is_tutorial": True, "source": "tutorial"}, "", "tutorial"),
        ("limited_cases", "diagnostic-limited-user", {}, "", "limited_case"),
        ("all", "diagnostic-all-user", {}, "", "all"),
    ],
)
async def test_step02_diagnostic_summary_records_allowed_pre_connection_stages(
    monkeypatch, stage, user_id, input_extra, internal_ids, expected_cohort
):
    _clear_limited_composer_env(monkeypatch)
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED", "true")
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ROLLOUT_STAGE", stage)
    if internal_ids:
        monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_INTERNAL_USER_IDS", internal_ids)
    from emlis_ai_reply_service import render_emlis_ai_reply

    payload = _input(SAMPLE_MEMO)
    payload.update(input_extra)
    reply = await render_emlis_ai_reply(
        user_id=user_id,
        subscription_tier="free",
        current_input=payload,
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    summary = reply.meta["diagnostic_summary"]
    _assert_summary_contract(summary)
    assert summary["feature_flag_enabled"] is True
    assert summary["feature_flag_state"]["set_flags"]["COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED"] == "true"
    assert summary["rollout_stage"] == stage
    assert summary["release_enabled"] is True
    assert summary["release_cohort"] == expected_cohort
    assert summary["release_decision"]["enabled"] is True
    assert summary["release_decision"]["attempted"] is True
    assert summary["rollout_decision"]["stage"] == stage
    assert summary["registry_resolution"]["connection_status"] == "default_client_resolved"
    assert summary["registry_resolution"]["default_client_used"] is True
    assert summary["default_composer_resolution"]["default_client_used"] is True
    assert summary["default_composer_resolution"]["default_client_resolved"] is True
    assert summary["composer_connection_attempted"] is True
    assert summary["rollout_attempted"] is True
    assert summary["pre_connection"]["blocked_before_composer"] is False
    b_plan = summary["b_plan_connection"]
    assert b_plan["phase"] == "B-D1"
    assert b_plan["route"] == "default_composer_route"
    assert b_plan["decision"] == "default_composer_connected"
    assert b_plan["default_client_used"] is True
    assert b_plan["default_client_resolved"] is True
    assert b_plan["composer_connection_attempted"] is True
    assert b_plan["composer_model_expected"] == "cocolon_limited_composer.v1"
    assert b_plan["rollout_stage"] == stage
    assert b_plan["release_gate_allowed"] is True
    assert b_plan["release_cohort"] == expected_cohort
    assert b_plan["blocked_before_composer"] is False
    assert b_plan["generator_or_gate_path"] is True
    assert b_plan["diagnostic_consistent"] is True
    assert b_plan["observation_status"] in b_plan["allowed_observation_statuses"]
    assert reply.meta["observation_status"] in {"passed", "rejected", "unavailable"}


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "stage,user_id,input_extra,internal_ids,expected_allowed,expected_decision",
    [
        ("off", "diagnostic-step06-off-user", {}, "", False, "blocked_rollout"),
        ("internal", "diagnostic-step06-internal-user", {}, "diagnostic-step06-internal-user", True, "default_composer_connected"),
        ("tutorial", "diagnostic-step06-tutorial-user", {"is_tutorial": True, "source": "tutorial"}, "", True, "default_composer_connected"),
        ("limited_cases", "diagnostic-step06-limited-user", {}, "", True, "default_composer_connected"),
        ("all", "diagnostic-step06-all-user", {}, "", True, "default_composer_connected"),
    ],
)
async def test_step06_b_plan_normal_connection_matrix(
    monkeypatch, stage, user_id, input_extra, internal_ids, expected_allowed, expected_decision
):
    _clear_limited_composer_env(monkeypatch)
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED", "true")
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ROLLOUT_STAGE", stage)
    if internal_ids:
        monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_INTERNAL_USER_IDS", internal_ids)
    from emlis_ai_reply_service import render_emlis_ai_reply

    payload = _input(SAMPLE_MEMO)
    payload.update(input_extra)
    reply = await render_emlis_ai_reply(
        user_id=user_id,
        subscription_tier="free",
        current_input=payload,
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    summary = reply.meta["diagnostic_summary"]
    _assert_summary_contract(summary)
    normal = summary["b_plan_connection"]
    assert normal == summary["pre_connection"]["b_plan_connection"]
    assert normal == reply.meta["multi_perspective"]["b_plan_connection"]
    assert normal["rollout_stage"] == stage
    assert normal["release_gate_allowed"] is expected_allowed
    assert normal["decision"] == expected_decision
    assert normal["diagnostic_consistent"] is True
    assert normal["release_registry_consistent"] is True
    assert normal["rollout_release_consistent"] is True
    assert normal["observation_status"] == reply.meta["observation_status"]

    if expected_allowed:
        assert summary["registry_resolution"]["connection_status"] == "default_client_resolved"
        assert normal["default_client_used"] is True
        assert normal["default_client_resolved"] is True
        assert normal["composer_connection_attempted"] is True
        assert normal["composer_model_expected"] == "cocolon_limited_composer.v1"
        assert normal["composer_model"] == "cocolon_limited_composer.v1"
        assert normal["generator_or_gate_path"] is True
        assert normal["environment_blocked"] is False
        assert reply.meta["observation_status"] in {"passed", "rejected", "unavailable"}
    else:
        assert summary["stage"] == "rollout"
        assert summary["registry_resolution"]["connection_status"] == "blocked_rollout"
        assert normal["default_client_used"] is False
        assert normal["composer_connection_attempted"] is False
        assert normal["environment_blocked"] is True
        assert normal["generator_or_gate_path"] is False
        assert normal["allowed_observation_statuses"] == ["unavailable"]
        assert reply.comment_text == ""



@pytest.mark.asyncio
async def test_step04_composer_diagnostic_records_generated_profile(monkeypatch):
    _clear_limited_composer_env(monkeypatch)
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED", "true")
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ROLLOUT_STAGE", "all")
    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="diagnostic-step04-generated-user",
        subscription_tier="free",
        current_input=_input(SAMPLE_MEMO),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    summary = reply.meta["diagnostic_summary"]
    _assert_summary_contract(summary)
    diagnostic = summary["composer_diagnostic"]
    assert diagnostic["version"] == "emlis.composer_diagnostic.v1"
    assert diagnostic["composer_status"] == summary["composer_status"] == "generated"
    assert diagnostic["composer_ready_for_gate"] is True
    assert diagnostic["profile_matched"] is True
    assert diagnostic["profile_unmatched"] is False
    assert diagnostic["phrase_unit_count"] > 0
    assert diagnostic["sentence_plan_count"] > 0
    assert diagnostic["required_roles"]
    assert diagnostic["available_roles"]
    assert diagnostic["missing_roles"] == []
    assert diagnostic["required_role_missing"] is False
    assert diagnostic["missing_phrase_units"] is False
    assert diagnostic["sentence_plan_unavailable"] is False
    assert "composer_generated" in diagnostic["coverage_matrix_hints"]
    assert summary["composer_rejection_reasons"] == []
    assert reply.meta["observation_status"] in {"passed", "rejected", "unavailable"}


class _UnavailableComposerWithStep04Meta:
    def generate(self, payload):
        return {
            "response_schema_version": "emlis.composer.response.v1",
            "composer_source": "unavailable",
            "composer_model": "diagnostic_fake_composer.v1",
            "generation_method": "test_composer",
            "generation_scope": "scoped_graph_only",
            "coverage_scope": "partial_observation",
            "fixed_string_renderer_used": False,
            "confidence": 0.0,
            "comment_text": "",
            "rejection_reasons": ["limited_composer_required_role_missing"],
            "composer_meta": {
                "profile_key": "mixed_positive_anxiety",
                "missing_roles": ["anxiety_return"],
                "composer_diagnostic": {
                    "version": "emlis.composer_diagnostic.v1",
                    "composer_attempted": True,
                    "composer_status": "unavailable",
                    "composer_ready_for_gate": False,
                    "coverage_scope": "partial_observation",
                    "profile_key": "mixed_positive_anxiety",
                    "source_profile_key": "",
                    "profile_matched": True,
                    "profile_unmatched": False,
                    "shallow_observation_path": False,
                    "phrase_unit_count": 1,
                    "used_phrase_unit_count": 0,
                    "evidence_span_count": 1,
                    "sentence_plan_count": 0,
                    "required_roles": ["positive_state", "anxiety_return"],
                    "available_roles": ["positive_state"],
                    "covered_roles": [],
                    "missing_roles": ["anxiety_return"],
                    "required_role_missing": True,
                    "missing_phrase_units": False,
                    "shallow_insufficient_evidence": False,
                    "sentence_plan_unavailable": False,
                    "reason_codes": ["limited_composer_required_role_missing"],
                    "reason_categories": ["required_role_missing"],
                    "reason_category": "required_role_missing",
                    "coverage_matrix_hints": ["required_role_missing"],
                    "stop_reason": "required_role_missing",
                },
            },
        }


@pytest.mark.asyncio
async def test_step04_diagnostic_summary_surfaces_composer_stop_reason(monkeypatch):
    _clear_limited_composer_env(monkeypatch)
    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="diagnostic-step04-required-role-user",
        subscription_tier="free",
        current_input=_input(SAMPLE_MEMO),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
        composer_client=_UnavailableComposerWithStep04Meta(),
    )

    summary = reply.meta["diagnostic_summary"]
    _assert_summary_contract(summary)
    diagnostic = summary["composer_diagnostic"]
    assert summary["stage"] == "composer"
    assert summary["composer_status"] == "unavailable"
    assert summary["primary_reason"] == "limited_composer_required_role_missing"
    assert "limited_composer_required_role_missing" in summary["composer_rejection_reasons"]
    assert diagnostic["reason_category"] == "required_role_missing"
    assert diagnostic["required_role_missing"] is True
    assert diagnostic["missing_roles"] == ["anxiety_return"]
    assert "required_role_missing" in summary["composer_coverage_matrix_hints"]
    assert summary["composer_reason_category"] == "required_role_missing"
    assert reply.comment_text == ""
    repair = summary["observation_display_repair_integration"]
    assert repair["display_repair_integration_ready"] is True
    assert repair["display_gate_relaxed"] is False
    assert repair["raw_input_included"] is False


GATE_READER_FAIL_TEXT = "Mashさん、Emlisです。"

GATE_GROUNDING_FAIL_TEXT = (
    "Mashさん、Emlisです。\n"
    "友達と話せて楽しかった時間と、本当の願いは愛されたいという断定が同じ場所で重なっています。\n"
    "その言葉は、今の流れの中で強い人だと決める材料にもつながっています。"
)

GATE_TEMPLATE_FAIL_TEXT = (
    "Mashさん、Emlisです。\n"
    "ずっと家にいて、リラックスできて自分のことを優先して色々整えたりお家のことも出来るから嬉しいんだけど、ふっと気が抜けたときに現実と向き合うことがあるからその時にダメージでかい。\n"
    "気をつけなきゃ行けないこと、全部無視して普通に生活したい。でもそうしたらもっと悪化する。\n"
    "この二つは同じ場所で重なっています。"
)



@pytest.mark.asyncio
async def test_step05_gate_diagnostic_records_reader_failure(monkeypatch):
    _clear_limited_composer_env(monkeypatch)
    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="diagnostic-step05-reader-user",
        subscription_tier="free",
        current_input=_input(SAMPLE_MEMO),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
        composer_client=_TextComposer(GATE_READER_FAIL_TEXT),
    )

    summary = reply.meta["diagnostic_summary"]
    _assert_summary_contract(summary)
    diagnostic = summary["gate_diagnostic"]
    assert summary["stage"] == "composer"
    assert summary["primary_reason"] == "environment_state_output_body_line_missing"
    assert summary["composer_status"] == "schema_invalid"
    assert "environment_state_output_body_line_missing" in summary["composer_rejection_reasons"]
    assert summary["gate_failure_stage"] == "reader"
    assert summary["gate_reason_category"] == "reader_readability"
    assert "reader_readability" in summary["gate_coverage_matrix_hints"]
    assert diagnostic["first_failed_gate"] == "reader"
    assert diagnostic["first_failed_reason"] in {"empty_text", "too_short_for_observation"}
    assert diagnostic["reader_passed"] is False
    assert diagnostic["generated_but_not_displayed"] is False
    assert summary["gate_results"]["reader"]["primary_reason"] == "empty_text"
    assert summary["gate_results"]["reader"]["reason_category"] == "reader_readability"
    assert summary["gate_results"]["reader"]["diagnostics"]["understandable"] is False
    assert reply.comment_text == ""


@pytest.mark.asyncio
async def test_step05_gate_diagnostic_records_grounding_failure(monkeypatch):
    _clear_limited_composer_env(monkeypatch)
    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="diagnostic-step05-grounding-user",
        subscription_tier="free",
        current_input=_input(SAMPLE_MEMO),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
        composer_client=_TextComposer(GATE_GROUNDING_FAIL_TEXT),
    )

    summary = reply.meta["diagnostic_summary"]
    _assert_summary_contract(summary)
    diagnostic = summary["gate_diagnostic"]
    assert summary["stage"] == "grounding"
    assert summary["primary_reason"] == "unsupported_sentence"
    assert summary["gate_failure_stage"] == "grounding"
    assert summary["gate_reason_category"] == "grounding_unsupported"
    assert "grounding_unsupported" in summary["gate_coverage_matrix_hints"]
    assert diagnostic["first_failed_gate"] == "grounding"
    assert diagnostic["reader_passed"] is True
    assert diagnostic["grounding_passed"] is False
    assert summary["gate_results"]["grounding"]["primary_reason"] == "unsupported_sentence"
    assert summary["gate_results"]["grounding"]["reason_category"] == "grounding_unsupported"
    assert summary["gate_results"]["grounding"]["diagnostics"]["unsupported_sentence_count"] >= 1
    assert reply.comment_text == ""


@pytest.mark.asyncio
async def test_step05_gate_diagnostic_records_template_failure(monkeypatch):
    _clear_limited_composer_env(monkeypatch)
    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="diagnostic-step05-template-user",
        subscription_tier="free",
        current_input=_input(SAMPLE_MEMO),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
        composer_client=_TextComposer(GATE_TEMPLATE_FAIL_TEXT),
    )

    summary = reply.meta["diagnostic_summary"]
    _assert_summary_contract(summary)
    diagnostic = summary["gate_diagnostic"]
    assert summary["stage"] == "template"
    assert summary["primary_reason"] == "excessive_raw_quote"
    assert summary["gate_failure_stage"] == "template_echo"
    assert summary["gate_reason_category"] == "template_echo_raw_copy"
    assert "template_echo_raw_copy" in summary["gate_coverage_matrix_hints"]
    assert diagnostic["first_failed_gate"] == "template_echo"
    assert diagnostic["reader_passed"] is True
    assert diagnostic["grounding_passed"] is True
    assert diagnostic["template_echo_passed"] is False
    assert summary["gate_results"]["template_echo"]["primary_reason"] == "excessive_raw_quote"
    assert summary["gate_results"]["template_echo"]["reason_category"] == "template_echo_raw_copy"
    assert summary["gate_results"]["template_echo"]["diagnostics"]["raw_quote_span_count"] >= 1
    assert "limited_composer_excessive_raw_quote" in summary["gate_rejection_reasons"]
    assert reply.comment_text == ""


@pytest.mark.asyncio
async def test_step05_gate_diagnostic_records_display_failure(monkeypatch):
    _clear_limited_composer_env(monkeypatch)
    import emlis_ai_reply_service as reply_service

    monkeypatch.setattr(reply_service, "phase6_composer_contract_ready", lambda: False)

    reply = await reply_service.render_emlis_ai_reply(
        user_id="diagnostic-step05-display-user",
        subscription_tier="free",
        current_input=_input(SAMPLE_MEMO),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
        composer_client=_TextComposer(PASSING_TEXT),
    )

    summary = reply.meta["diagnostic_summary"]
    _assert_summary_contract(summary)
    diagnostic = summary["gate_diagnostic"]
    assert summary["observation_status"] == "unavailable"
    assert summary["stage"] == "display"
    assert summary["primary_reason"] == "phase_not_complete"
    assert summary["gate_failure_stage"] == "display"
    assert summary["gate_reason_category"] == "display_phase"
    assert "display_phase" in summary["gate_coverage_matrix_hints"]
    assert diagnostic["first_failed_gate"] == "display"
    assert diagnostic["reader_passed"] is True
    assert diagnostic["grounding_passed"] is True
    assert diagnostic["template_echo_passed"] is True
    assert diagnostic["display_passed"] is False
    assert summary["gate_results"]["display"]["primary_reason"] == "phase_not_complete"
    assert summary["gate_results"]["display"]["reason_category"] == "display_phase"
    assert summary["gate_results"]["display"]["diagnostics"]["comment_text_allowed"] is False
    assert reply.comment_text == ""


@pytest.mark.asyncio
async def test_step06_limited_cases_scope_block_is_scope_not_rollout(monkeypatch):
    _clear_limited_composer_env(monkeypatch)
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED", "true")
    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="diagnostic-step06-scope-block-user",
        subscription_tier="free",
        current_input=_input(""),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    summary = reply.meta["diagnostic_summary"]
    _assert_summary_contract(summary)
    b_plan = summary["b_plan_connection"]
    assert summary["rollout_stage"] == "limited_cases"
    assert summary["scope_status"] == "out_of_scope"
    assert summary["stage"] == "display"
    assert summary["primary_reason"] == "passed"
    assert summary["release_decision"]["reason_code"] == "scope_limited_case_not_eligible"
    assert summary["registry_resolution"]["connection_status"] == "blocked_scope"
    assert summary["registry_resolution"]["pre_connection_stop_stage"] == "scope"
    assert b_plan["decision"] == "blocked_scope"
    assert b_plan["registry_connection_status"] == "blocked_scope"
    assert b_plan["environment_blocked"] is False
    assert b_plan["status_family"] == "passed"
    assert b_plan["blocked_before_composer"] is True
    assert summary["composer_connection_attempted"] is False
    assert summary["comment_text_allowed"] is True
    assert reply.comment_text
    assert "詳しく残せそうなら" in reply.comment_text


@pytest.mark.asyncio
async def test_step06_default_composer_env_connects_normal_route(monkeypatch):
    _clear_limited_composer_env(monkeypatch)
    monkeypatch.setenv("COCOLON_EMLIS_DEFAULT_COMPOSER", "cocolon_limited_composer")
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ROLLOUT_STAGE", "all")
    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="diagnostic-step06-default-env-user",
        subscription_tier="free",
        current_input=_input(SAMPLE_MEMO),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    summary = reply.meta["diagnostic_summary"]
    _assert_summary_contract(summary)
    b_plan = summary["b_plan_connection"]
    assert summary["feature_flag_enabled"] is True
    assert summary["feature_flag_state"]["source_kind"] == "default_composer_env"
    assert summary["release_decision"]["stage"] == "all"
    assert summary["release_decision"]["enabled"] is True
    assert summary["default_composer_resolution"]["release_allowed"] is True
    assert summary["registry_resolution"]["connection_status"] == "default_client_resolved"
    assert b_plan["decision"] == "default_composer_connected"
    assert b_plan["route"] == "default_composer_route"
    assert b_plan["composer_connection_attempted"] is True
    assert b_plan["composer_model_expected"] == "cocolon_limited_composer.v1"
    assert b_plan["release_registry_consistent"] is True
    assert b_plan["rollout_release_consistent"] is True
    assert reply.meta["observation_status"] in {"passed", "rejected", "unavailable"}


@pytest.mark.asyncio
async def test_step08_coverage_matrix_maps_composer_reason_to_group(monkeypatch):
    _clear_limited_composer_env(monkeypatch)
    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="diagnostic-step08-coverage-user",
        subscription_tier="free",
        current_input=_input(SAMPLE_MEMO),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
        composer_client=_UnavailableComposerWithStep04Meta(),
    )

    summary = reply.meta["diagnostic_summary"]
    _assert_summary_contract(summary)
    matrix = summary["coverage_matrix"]
    assert matrix["phase"] == "B-S1"
    assert matrix["matrix_purpose"] == "map_diagnostic_reasons_to_coverage_groups"
    assert matrix["status"] == "classified"
    assert "composer_material" in matrix["technical_coverage_groups"]
    assert "positive_recovery" in matrix["input_coverage_groups"]
    assert "limit_escape" in matrix["input_coverage_groups"]
    assert summary["coverage_groups"] == matrix["coverage_groups"]
    assert summary["coverage_primary_group"] == matrix["primary_coverage_group"]
    assert "limited_composer_required_role_missing" in matrix["coverage_group_map"]["composer_material"]["reason_codes"]
    assert matrix["coverage_group_map"]["composer_material"]["target_step"] == "Step11-13 Composer拡張"
    assert reply.comment_text == ""


@pytest.mark.asyncio
async def test_step08_coverage_matrix_uses_evidence_roles_for_fake_composer(monkeypatch):
    _clear_limited_composer_env(monkeypatch)
    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="diagnostic-step08-evidence-role-user",
        subscription_tier="free",
        current_input=_input("だるいし、何もしたくない。全部投げ出したくなる。"),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
        composer_client=_TextComposer(GATE_READER_FAIL_TEXT),
    )

    summary = reply.meta["diagnostic_summary"]
    _assert_summary_contract(summary)
    matrix = summary["coverage_matrix"]
    assert "energy_fatigue" in matrix["input_coverage_groups"]
    assert "limit_escape" in matrix["input_coverage_groups"]
    assert matrix["coverage_group_map"]["energy_fatigue"]["matched_from_input"] is True
    assert matrix["coverage_group_map"]["limit_escape"]["matched_from_input"] is True
    assert "gate_quality" in matrix["technical_coverage_groups"]
    assert reply.comment_text == ""


def test_step10_registry_safety_takes_precedence_over_explicit_client(monkeypatch):
    _clear_limited_composer_env(monkeypatch)
    from emlis_ai_composer_client_registry import resolve_default_emlis_composer_client

    class ExplicitComposer:
        composer_model = "explicit_should_not_connect.v1"

    client, meta = resolve_default_emlis_composer_client(
        composer_client=ExplicitComposer(),
        safety_requires_block=True,
    )

    assert client is None
    assert meta["connection_status"] == "blocked_safety"
    assert meta["pre_connection_stop_stage"] == "safety"
    assert meta["explicit_client_used"] is False
    assert meta["default_client_used"] is False
    assert meta["composer_attempted"] is False
    assert meta["blocked_before_composer"] is True
    assert "safety_boundary" in meta["rejection_reasons"]
    assert "composer_prevented_by_safety_boundary" in meta["rejection_reasons"]


@pytest.mark.asyncio
async def test_step10_safety_blocks_before_composer_even_with_explicit_client(monkeypatch):
    _clear_limited_composer_env(monkeypatch)
    from emlis_ai_reply_service import render_emlis_ai_reply

    class ExplodingComposer:
        composer_model = "exploding_composer.v1"
        called = False

        def generate(self, payload):
            self.called = True
            raise AssertionError("Composer must not be called when safety boundary is present")

    composer = ExplodingComposer()
    reply = await render_emlis_ai_reply(
        user_id="diagnostic-step10-safety-user",
        subscription_tier="free",
        current_input=_input("生きていたくない。もう無理。"),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
        composer_client=composer,
    )

    summary = reply.meta["diagnostic_summary"]
    _assert_summary_contract(summary)
    assert composer.called is False
    assert reply.comment_text == ""
    assert summary["observation_status"] == "safety_blocked"
    assert summary["stage"] == "scope"
    assert summary["primary_reason"] == "safety_boundary"
    assert summary["scope_status"] == "safety_blocked"
    assert summary["composer_connection_attempted"] is False
    assert summary["composer_status"] == "not_attempted"
    assert summary["registry_resolution"]["connection_status"] == "blocked_safety"
    assert summary["registry_resolution"]["composer_attempted"] is False
    assert summary["default_composer_resolution"]["connection_status"] == "blocked_safety"
    assert summary["default_composer_resolution"]["composer_attempted"] is False
    assert summary["pre_connection"]["blocked_before_composer"] is True
    assert summary["b_plan_connection"]["decision"] == "blocked_safety"
    assert summary["b_plan_connection"]["blocked_before_composer"] is True
    assert summary["b_plan_connection"]["composer_connection_attempted"] is False
    assert summary["b_plan_connection"]["generator_or_gate_path"] is False
    assert summary["b_plan_connection"]["status_family"] == "safety_blocked"
    safety_pre_generation = summary["scope_diagnostic"]["safety_pre_generation_block"]
    assert safety_pre_generation["version"] == "emlis.safety_pre_generation_block.v1"
    assert safety_pre_generation["blocked_before_composer"] is True
    assert safety_pre_generation["composer_generation_allowed"] is False
    assert safety_pre_generation["fixed_reply_allowed"] is False
    assert safety_pre_generation["fallback_observation_allowed"] is False
    assert "safety_boundary" in summary["coverage_groups"]
