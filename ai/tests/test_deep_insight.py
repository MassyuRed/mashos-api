import asyncio
import json
import os
from pathlib import Path
import subprocess

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import api_deep_insight as api
from cocolon_meaning_experience_engine.deep_insight_question import admit_question, prepare_question_material


OWNER = "00000000-0000-0000-0000-000000000001"
QUESTION = "00000000-0000-0000-0000-000000000101"
RECORD = {"thought": "頼まれたことを先にした。", "action": None,
          "created_at": "2026-11-21T10:00:00Z", "emlis_open_question": None}
Q = {"id": QUESTION, "lane": "records", "theme": None, "question_text": "何を大切にしていますか？",
     "issued_on": "2026-11-21", "answer_text": None, "answered_at": None}
AUTH = {"Authorization": "Bearer verified"}


def material(*, records=(), prior=(), map_reference=None):
    return {"records": list(records), "prior": list(prior), "map": map_reference}


def candidate(**changes):
    return json.dumps({"decision": "ask", "focus": "REASON", "source": "r1.thought", "quote": "頼まれたことを先にした",
                       "question": "「頼まれたことを先にした」のは、どんな理由からですか？", **changes}, ensure_ascii=False)


def previous(*, text, answer=None):
    return {"question_text": text, "question_key": "previous-target", "text_key": "previous-text",
            "answer_text": answer, "answered_at": "2026-11-20T00:00:00Z" if answer else None}


def test_cmee_reflection_checks_literal_source_and_already_asked_focus():
    original = material(records=[RECORD])
    prepared, sources = prepare_question_material(original, lane="records", theme=None)
    assert prepared["sources"]["r1.thought"]["text"] == RECORD["thought"]
    approved = admit_question(candidate(), lane="records", theme=None, sources=sources, material=original)
    assert approved is not None
    for raw in (candidate(source="a99"), candidate(quote="頼まれなかったこと"),
                candidate(question="他の人を優先してしまう性格ですか？"), candidate(decision="skip")):
        assert admit_question(raw, lane="records", theme=None, sources=sources, material=original) is None
    prior = previous(text=approved.text, answer="その時は相手が困っていたからです。")
    prior["question_key"] = approved.question_key
    known = material(records=[RECORD], prior=[prior])
    assert admit_question(candidate(), lane="records", theme=None, sources=sources, material=known) is None
    new_condition = candidate(focus="CONDITION", question="「頼まれたことを先にした」ときとは逆に、自分の仕事を先にするのはどんなときですか？")
    assert admit_question(new_condition, lane="records", theme=None, sources=sources, material=known)


def test_answer_alone_is_evidence_and_theme_starts_without_a_record():
    raw = material(prior=[previous(text="どんなときに友達だと感じますか？", answer="意見が違っても本音を言えるときです。")])
    prepared, sources = prepare_question_material(raw, lane="records", theme=None)
    assert prepared["previous_questions"][0]["answer_source"] == "a1"
    follow_up = candidate(focus="CONDITION", source="a1", quote="意見が違っても本音を言える",
                          question="「意見が違っても本音を言える」のは、相手がどんなふうに聞いてくれるときですか？")
    assert admit_question(follow_up, lane="records", theme=None, sources=sources, material=raw)

    raw = material()
    _, sources = prepare_question_material(raw, lane="theme", theme="人間関係")
    theme = candidate(focus="RELATIONSHIP", source="", quote="", question="どんなときに、この人は友達だなと感じますか？")
    assert admit_question(theme, lane="theme", theme="人間関係", sources=sources, material=raw)


def test_safety_and_map_preferences_are_not_promoted_to_authored_evidence():
    raw = material(records=[{**RECORD, "action": "もう死にたい。"}],
                   map_reference={"summary": "役割を引き受けると落ち着くと推定した。", "generated_at": "2026-11-19T00:00:00Z"})
    prepared, sources = prepare_question_material(raw, lane="records", theme=None)
    assert not sources
    assert prepared["map_reference"]["summary"] == raw["map"]["summary"]


def test_existing_emlis_confirmation_is_context_and_blocks_a_repeated_question():
    old_question = json.loads(candidate())["question"]
    record = {**RECORD, "emlis_open_question": "どんなことを頼まれたのですか？",
              "emlis_answered_questions": [{"question": old_question, "answer": "相手が困っていたからです。"}]}
    raw = material(records=[record])
    prepared, sources = prepare_question_material(raw, lane="records", theme=None)
    assert prepared["open_emlis_questions"][0]["sources"] == ["r1.thought"]
    assert prepared["answered_emlis_questions"][0]["answer"] == "相手が困っていたからです。"
    assert admit_question(candidate(), lane="records", theme=None, sources=sources, material=raw) is None


def test_model_transport_uses_the_existing_authenticated_natural_request_contract(monkeypatch):
    endpoint = "https://model.invalid/v1/chat/completions"
    model = "test-natural-4b"
    monkeypatch.setenv("EMLIS_NATURAL_REPLY_ENDPOINT", endpoint)
    monkeypatch.setenv("EMLIS_NATURAL_REPLY_MODEL", model)
    monkeypatch.setenv("EMLIS_NATURAL_REPLY_API_KEY", "unit-test-key")
    prepared = {"lane": "theme", "theme": "人間関係", "sources": {}}
    sent = []

    def capture(request):
        sent.append(request)
        post = json.loads(request.content)
        assert str(request.url) == endpoint and request.headers["Authorization"] == "Bearer unit-test-key"
        assert post["model"] == model and post["temperature"] == 0 and post["max_tokens"] == 2048
        assert post["stream"] is False and post["chat_template_kwargs"] == {"enable_thinking": False}
        assert [row["role"] for row in post["messages"]] == ["system", "user"]
        assert json.loads(post["messages"][1]["content"]) == prepared
        return httpx.Response(200, json={"model": model, "choices": [{"finish_reason": "stop", "message": {
            "role": "assistant", "content": '{"decision":"skip"}'}}]})

    real_client = httpx.AsyncClient
    transport = httpx.MockTransport(capture)
    monkeypatch.setattr(api.httpx, "AsyncClient", lambda **kwargs: real_client(transport=transport, **kwargs))
    assert asyncio.run(api._generate_candidate(prepared)) == '{"decision":"skip"}'
    assert len(sent) == 1


@pytest.fixture
def api_harness(monkeypatch):
    calls = []
    state = {"day": "2026-11-21", "can_use_theme": False, "records": None, "theme": None,
             "record_available_today": True, "theme_available_today": False, "history": []}

    async def resolve(token):
        assert token == "verified"
        return OWNER

    async def storage_rpc(name, payload, *, timeout):
        assert payload["p_user_id"] == OWNER
        calls.append((name, payload))
        if name == "deep_insight_state":
            return httpx.Response(200, json=state)
        if name == "deep_insight_candidate_context":
            return httpx.Response(200, json={"material": material(records=[RECORD]), "guard": "source-guard"})
        if name == "deep_insight_issue":
            return httpx.Response(200, json={"status": "issued", "question": {**Q, "question_text": payload["p_question_text"]}})
        if name == "deep_insight_answer":
            return httpx.Response(200, json={"inserted": True, "question": {
                **Q, "answer_text": payload["p_answer_text"], "answered_at": "2026-11-21T10:00:00Z"}})
        raise AssertionError(name)

    async def generate(prompt):
        calls.append(("4B", prompt))
        return candidate()

    async def refresh(owner, *, trigger):
        calls.append(("refresh", (owner, trigger)))

    import analysis_cumulative_service
    monkeypatch.setattr(api, "_resolve_user_id_from_token", resolve)
    monkeypatch.setattr(api, "sb_post_rpc", storage_rpc)
    monkeypatch.setattr(api, "_generate_candidate", generate)
    monkeypatch.setattr(analysis_cumulative_service, "request_map_refresh", refresh)
    app = FastAPI()
    api.register_deep_insight_routes(app)
    return TestClient(app), state, calls


def test_read_and_repeat_never_generate_and_free_cannot_issue_a_theme(api_harness):
    client, state, calls = api_harness
    assert client.get("/deep-insight").status_code == 401
    response = client.get("/deep-insight", headers=AUTH)
    assert response.status_code == 200 and response.headers["cache-control"] == "no-store"
    assert "day" not in response.json()
    assert client.post("/deep-insight/questions", headers=AUTH, json={"lane": "theme", "theme": "人間関係"}).status_code == 403
    state["records"] = Q
    assert client.post("/deep-insight/questions", headers=AUTH, json={"lane": "records"}).json() == {
        "status": "existing", "question": Q}
    assert [name for name, _ in calls] == ["deep_insight_state"] * 3


def test_issue_and_exact_answer_pass_verified_owner_to_the_store(api_harness):
    client, _, calls = api_harness
    response = client.post("/deep-insight/questions", headers=AUTH, json={"lane": "records"})
    assert response.status_code == 200 and response.json()["status"] == "issued"
    assert calls[-1][0] == "deep_insight_issue" and calls[-1][1]["p_material_guard"] == "source-guard"
    response = client.post("/deep-insight/answers", headers=AUTH, json={"question_id": QUESTION, "answer_text": "本人の回答\n次の段落"})
    assert response.status_code == 200 and response.json()["question"]["answer_text"] == "本人の回答\n次の段落"
    assert "inserted" not in response.json()
    assert calls[-1] == ("refresh", (OWNER, "deep_insight_answer"))


def test_normal_app_routes_expose_only_deep_insight_as_active_question_feature():
    from app import create_application

    paths = create_application().openapi()["paths"]
    assert "get" in paths["/deep-insight"]
    assert "post" in paths["/deep-insight/questions"]
    assert "post" in paths["/deep-insight/answers"]
    assert not any(path.startswith("/today-question/") for path in paths)


def test_deep_insight_migration_in_isolated_postgres():
    if not os.environ.get("Q2_PGLITE_MODULE"):
        pytest.skip("Existing PostgreSQL WASM dependency not configured")
    root = Path(__file__).parents[2]
    result = subprocess.run(["node", "ai/tests/deep_insight_sql.cjs"], cwd=root,
                            capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
