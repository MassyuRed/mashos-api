import asyncio
import json
import os
from pathlib import Path
import subprocess
from types import SimpleNamespace

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import api_deep_insight as api
from cocolon_meaning_experience_engine.deep_insight_question import (
    PLAN_SYSTEM_MESSAGE, READ_SYSTEM_MESSAGE, WRITE_SYSTEM_MESSAGE,
)


OWNER = "00000000-0000-0000-0000-000000000001"
QUESTION = "00000000-0000-0000-0000-000000000101"
RECORD = {"id": "00000000-0000-0000-0000-000000000201", "source_version": "a" * 64,
          "thought": "頼まれたことを先にした。", "action": None,
          "created_at": "2026-11-21T10:00:00Z", "emlis_open_question": None}
Q = {"id": QUESTION, "lane": "records", "theme": None, "question_text": "何を大切にしていますか？",
     "issued_on": "2026-11-21", "answer_text": None, "answered_at": None}
AUTH = {"Authorization": "Bearer verified"}


def material(*, records=(), prior=(), map_reference=None):
    return {"records": list(records), "prior": list(prior), "map": map_reference}


REFLECTION_PLAN = {"decision": "ask", "focus": "REASON", "source": "r1.thought",
                   "quote": "頼まれたことを先にした", "condition": "", "ask": "頼まれたことを先にした理由"}
REFLECTION_TEXT = {"question": "どんな理由からですか？"}
REFLECTION_READ = {"verdict": "accept", "focus": "REASON", "source": "r1.thought",
                   "quote": "頼まれたことを先にした", "condition": "",
                   "premise_supported": True, "new_information": True}


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
    assert asyncio.run(api._generate_candidate(PLAN_SYSTEM_MESSAGE, prepared)) == '{"decision":"skip"}'
    assert len(sent) == 1


@pytest.fixture
def api_harness(monkeypatch):
    calls = []
    state = {"day": "2026-11-21", "can_use_theme": False, "records": None, "theme": None,
             "record_available_today": True, "theme_available_today": False, "history": []}

    async def resolve(token):
        assert token == "verified"
        return OWNER

    answers = {PLAN_SYSTEM_MESSAGE: REFLECTION_PLAN, WRITE_SYSTEM_MESSAGE: REFLECTION_TEXT,
               READ_SYSTEM_MESSAGE: REFLECTION_READ}
    input_material = {"value": material(records=[RECORD]), "guard": "source-guard"}

    async def storage_rpc(name, payload, *, timeout):
        assert payload["p_user_id"] == OWNER
        calls.append((name, payload))
        if name == "deep_insight_state":
            return httpx.Response(200, json=state)
        if name == "deep_insight_candidate_context":
            return httpx.Response(200, json={"material": input_material["value"], "guard": input_material["guard"]})
        if name == "deep_insight_issue_grounded":
            return httpx.Response(200, json={"status": "issued", "question": {**Q, "question_text": payload["p_question_text"]}})
        if name == "deep_insight_answer":
            return httpx.Response(200, json={"inserted": True, "question": {
                **Q, "answer_text": payload["p_answer_text"], "answered_at": "2026-11-21T10:00:00Z"}})
        raise AssertionError(name)

    async def generate(system, payload):
        calls.append(("4B", system, payload))
        return json.dumps(answers[system], ensure_ascii=False)

    async def acquire(*, lock_key, ttl_seconds):
        return SimpleNamespace(acquired=True, lock_key=lock_key, owner_id="test-lease")

    async def release(*, lock_key, owner_id):
        assert owner_id == "test-lease"

    async def refresh(owner, *, trigger):
        calls.append(("refresh", (owner, trigger)))

    import analysis_cumulative_service
    monkeypatch.setattr(api, "_resolve_user_id_from_token", resolve)
    monkeypatch.setattr(api, "sb_post_rpc", storage_rpc)
    monkeypatch.setattr(api, "_generate_candidate", generate)
    monkeypatch.setattr(api, "try_acquire_lock", acquire)
    monkeypatch.setattr(api, "release_lock", release)
    monkeypatch.setattr(analysis_cumulative_service, "request_map_refresh", refresh)
    app = FastAPI()
    api.register_deep_insight_routes(app)
    return TestClient(app), state, calls, answers, input_material


def test_read_and_repeat_never_generate_and_free_cannot_issue_a_theme(api_harness):
    client, state, calls, _, _ = api_harness
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
    client, _, calls, _, _ = api_harness
    response = client.post("/deep-insight/questions", headers=AUTH, json={"lane": "records"})
    assert response.status_code == 200 and response.json()["status"] == "issued"
    assert calls[-1][0] == "deep_insight_issue_grounded" and calls[-1][1]["p_material_guard"] == "source-guard"
    assert [row[1] for row in calls if row[0] == "4B"] == list((PLAN_SYSTEM_MESSAGE, WRITE_SYSTEM_MESSAGE, READ_SYSTEM_MESSAGE))
    receipt = calls[-1][1]["p_grounding_receipt"]
    assert receipt["source_id"] == RECORD["id"] and receipt["source_version"] == RECORD["source_version"]
    assert "quote" not in receipt and "question" not in receipt
    assert "p_grounding_receipt" not in response.json()["question"]
    response = client.post("/deep-insight/answers", headers=AUTH, json={"question_id": QUESTION, "answer_text": "本人の回答\n次の段落"})
    assert response.status_code == 200 and response.json()["question"]["answer_text"] == "本人の回答\n次の段落"
    assert "inserted" not in response.json()
    assert calls[-1] == ("refresh", (OWNER, "deep_insight_answer"))


def test_no_merit_is_reused_for_same_material_but_rechecked_after_edit(api_harness):
    client, _, calls, answers, context = api_harness
    context["guard"] = "no-merit-1"
    answers[PLAN_SYSTEM_MESSAGE] = {"decision": "skip"}
    for _ in range(2):
        response = client.post("/deep-insight/questions", headers=AUTH, json={"lane": "records"})
        assert response.json() == {"status": "no_question", "question": None}
    assert len([row for row in calls if row[0] == "4B"]) == 1
    context["guard"] = "no-merit-2"
    assert client.post("/deep-insight/questions", headers=AUTH, json={"lane": "records"}).status_code == 200
    assert len([row for row in calls if row[0] == "4B"]) == 2


def test_independent_rejection_stops_before_storage(api_harness):
    client, _, calls, answers, context = api_harness
    context["guard"] = "reader-rejection"
    answers[READ_SYSTEM_MESSAGE] = {**REFLECTION_READ, "verdict": "reject", "premise_supported": False}
    response = client.post("/deep-insight/questions", headers=AUTH, json={"lane": "records"})
    assert response.json() == {"status": "no_question", "question": None}
    assert not [row for row in calls if row[0] == "deep_insight_issue_grounded"]


def test_second_instance_does_not_generate_while_the_same_slot_is_locked(api_harness, monkeypatch):
    client, _, calls, _, context = api_harness
    context["guard"] = "busy-guard"

    async def busy(**kwargs):
        return SimpleNamespace(acquired=False)

    monkeypatch.setattr(api, "try_acquire_lock", busy)
    response = client.post("/deep-insight/questions", headers=AUTH, json={"lane": "records"})
    assert response.status_code == 503 and response.headers["retry-after"] == "3"
    assert not [row for row in calls if row[0] in {"4B", "deep_insight_issue_grounded"}]


def test_same_revision_requests_share_one_issue_and_receive_the_same_question(api_harness, monkeypatch):
    client, _, calls, _, context = api_harness
    context["guard"] = "concurrent-guard"
    generate = api._generate_candidate

    async def both():
        started, checked = asyncio.Event(), asyncio.Event()
        storage = api.sb_post_rpc

        async def wait_on_other_request(system, payload):
            if system == PLAN_SYSTEM_MESSAGE:
                started.set()
                await checked.wait()
            return await generate(system, payload)

        async def note_second_context(name, payload, *, timeout):
            result = await storage(name, payload, timeout=timeout)
            if name == "deep_insight_candidate_context" and started.is_set():
                checked.set()
            return result

        monkeypatch.setattr(api, "_generate_candidate", wait_on_other_request)
        monkeypatch.setattr(api, "sb_post_rpc", note_second_context)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=client.app), base_url="http://test") as session:
            def request():
                return session.post("/deep-insight/questions", headers=AUTH, json={"lane": "records"})

            first = asyncio.create_task(request())
            await started.wait()
            return await asyncio.gather(first, request())

    first, second = asyncio.run(asyncio.wait_for(both(), timeout=5))
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    assert len([row for row in calls if row[0] == "4B"]) == 3
    assert len([row for row in calls if row[0] == "deep_insight_issue_grounded"]) == 1


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
