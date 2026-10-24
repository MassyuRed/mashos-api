"""Injected inference/timeout boundary; no external model or network calls."""
import asyncio
import copy
from dataclasses import replace
import json

import pytest

from test_cmee_emlis_model_meaning import initial_model_request
from cocolon_meaning_experience_engine.model_candidate_source import (
    MODEL, REVISION, JSON_INSTRUCTION, ModelCallLimits, ModelCandidateSource,
    ModelResponse, build_model_messages,
)


def response(req, *, finish="stop", **changes):
    raw = req.current_input_bundle.raw_current_input
    packet = dict(candidate={"unadopted": True}, evidence=[dict(source_id=raw["id"],
        field_path="memo", start=0, end=len(raw["memo"]), quote=raw["memo"])])
    value = ModelResponse(json.dumps(packet, ensure_ascii=False), finish, "synthetic-generator",
                          MODEL, REVISION, usage={"input_tokens": 100, "output_tokens": 30})
    return replace(value, **changes)


def test_messages_preserve_full_native_material_and_distinguish_generated_interpretation():
    req = initial_model_request()
    messages = build_model_messages(req)
    assert JSON_INSTRUCTION in messages[0]["content"]
    body = json.loads(messages[1]["content"])
    assert body["prior_adopted_interpretation"] is None
    assert body["material"]["sources"][0]["original"] == req.current_input_bundle.raw_current_input
    assert body["material"]["control"]["actual_question_budget_remaining"] == 1
    changed = copy.deepcopy(messages)
    changed[1]["content"] = "discarded"
    assert build_model_messages(req) == messages


def test_non_offline_or_non_free_request_never_reaches_generator():
    req = initial_model_request()
    with pytest.raises(ValueError, match="explicit_offline"):
        build_model_messages(replace(req, execution_mode="APPLICATION"))
    other = replace(req, emlis_thread=replace(req.emlis_thread, capability_snapshot="Q3_PLUS"))
    with pytest.raises(ValueError, match="free_one_answer"):
        build_model_messages(other)


def test_actual_raw_metadata_and_adapter_identity_reach_unadopted_receipt_once():
    req = initial_model_request()
    raw_response = response(req, adapter_revision="sha256:synthetic-adapter")
    calls = []
    async def generate(messages, limits):
        calls.append((messages, limits))
        return raw_response
    source = ModelCandidateSource(generate, lambda _: 100,
        limits=ModelCallLimits(500, 200, 1), adapter_revision="sha256:synthetic-adapter")
    got = asyncio.run(source(req))
    assert len(calls) == 1
    assert got.raw_output == raw_response.raw_output
    assert got.status == "CANDIDATE_UNREVIEWED" and got.adoption_state == "NOT_ADOPTED"
    metadata = json.loads(got.metadata_json)
    assert metadata["revision"] == REVISION
    assert metadata["adapter_revision"] == "sha256:synthetic-adapter"
    assert metadata["usage"] == raw_response.usage


@pytest.mark.parametrize("finish,status", [("length", "TOKEN_LIMIT"), ("timeout", "TIMEOUT"),
    ("error", "PROVIDER_ERROR"), ("unknown", "UNKNOWN_FINISH"), ("eos", "UNKNOWN_FINISH")])
def test_non_stop_finish_dominates_complete_json_without_repair_or_retry(finish, status):
    req = initial_model_request()
    raw_response = response(req, finish=finish)
    calls = []
    async def generate(*_):
        calls.append(1)
        return raw_response
    got = asyncio.run(ModelCandidateSource(generate, lambda _: 100, limits=ModelCallLimits(500, 200, 1))(req))
    assert got.raw_output == raw_response.raw_output
    assert got.status == status and len(calls) == 1


@pytest.mark.parametrize("change", [dict(model="other"), dict(revision="other"),
                                   dict(adapter_revision="unexpected-adapter")])
def test_other_base_or_adapter_is_recorded_but_never_normal_success(change):
    req = initial_model_request()
    async def generate(*_):
        return response(req, **change)
    got = asyncio.run(ModelCandidateSource(generate, lambda _: 100, limits=ModelCallLimits(500, 200, 1))(req))
    assert got.status == "PROVIDER_ERROR" and got.raw_output
    meta = json.loads(got.metadata_json)
    for k, v in change.items():
        assert meta[k] == v


def test_input_limit_does_not_invoke_or_truncate_material():
    calls = []
    async def generate(*_):
        calls.append(1)
        raise AssertionError("must not call")
    source = ModelCandidateSource(generate, lambda _: 501, limits=ModelCallLimits(500, 200, 1))
    got = asyncio.run(source(initial_model_request()))
    assert got.status == "TOKEN_LIMIT" and got.raw_output is None and not calls
    assert json.loads(got.metadata_json)["provider"] is None


def test_timeout_cancels_one_async_attempt_and_never_invents_usage():
    state = {"calls": 0, "cancelled": False}
    async def generate(*_):
        state["calls"] += 1
        try:
            await asyncio.Event().wait()
        finally:
            state["cancelled"] = True
    source = ModelCandidateSource(generate, lambda _: 100, limits=ModelCallLimits(500, 200, .01))
    got = asyncio.run(source(initial_model_request()))
    assert state == {"calls": 1, "cancelled": True}
    assert got.status == "TIMEOUT" and json.loads(got.metadata_json)["usage"] is None


def test_external_cancellation_propagates_for_existing_service_acquisition_state():
    async def exercise():
        entered = asyncio.Event()
        async def generate(*_):
            entered.set()
            await asyncio.Event().wait()
        task = asyncio.create_task(ModelCandidateSource(generate, lambda _: 100,
            limits=ModelCallLimits(500, 200, 5))(initial_model_request()))
        await entered.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
    asyncio.run(exercise())


def test_exception_text_is_not_recorded_as_provider_output():
    async def generate(*_):
        raise RuntimeError("synthetic-secret-never-record-this")
    got = asyncio.run(ModelCandidateSource(generate, lambda _: 100,
        limits=ModelCallLimits(500, 200, 1))(initial_model_request()))
    assert got.status == "PROVIDER_ERROR" and got.raw_output is None
    assert "synthetic-secret" not in got.metadata_json
