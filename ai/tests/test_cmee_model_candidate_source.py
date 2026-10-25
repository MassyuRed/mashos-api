"""Injected inference/timeout boundary; no external model or network calls."""
import asyncio
import copy
from dataclasses import replace
import json

import pytest

from test_cmee_emlis_model_meaning import (
    initial_model_request, model_answer, model_packet, model_semantic, prepare_model_snapshot,
)
from cocolon_meaning_experience_engine.emlis_semantic_admission import SemanticNotAdopted
from cocolon_meaning_experience_engine.preparation import prepare_emlis, receive_candidate
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


def assert_source_projection(body, native):
    assert {key: value for key, value in body["material"].items() if key != "sources"} == {
        key: value for key, value in native.items() if key != "sources"}
    assert len(body["material"]["sources"]) == len(native["sources"])
    for visible, original in zip(body["material"]["sources"], native["sources"], strict=True):
        assert visible == {key: value for key, value in original.items()
                           if key not in {"evidence", "envelope_id", "source_commitment"}}
        assert original["evidence"] and original["envelope_id"] and original["source_commitment"]
        assert not {"evidence", "envelope_id", "source_commitment"}.intersection(visible)


def test_messages_preserve_source_text_metadata_and_distinguish_generated_interpretation():
    req = initial_model_request()
    native = prepare_emlis(req).payload()
    messages = build_model_messages(req)
    assert JSON_INSTRUCTION in messages[0]["content"]
    body = json.loads(messages[1]["content"])
    assert body["prior_adopted_interpretation"] is None
    assert body["material"]["sources"][0]["original"] == req.current_input_bundle.raw_current_input
    assert_source_projection(body, native)
    assert prepare_emlis(req).payload() == native
    assert body["material"]["control"]["actual_question_budget_remaining"] == 1
    changed = copy.deepcopy(messages)
    changed[1]["content"] = "discarded"
    assert build_model_messages(req) == messages


def test_stage_instructions_preserve_answer_source_and_do_not_contaminate_initial_messages():
    req = initial_model_request()
    initial = build_model_messages(req)
    prepared = prepare_model_snapshot(req, model_semantic(req))
    answer = model_answer(req, prepared)
    body = json.loads(build_model_messages(answer, prepared.semantic_snapshot)[1]["content"])
    assert_source_projection(body, prepare_emlis(answer).payload())
    assert body["prior_adopted_interpretation"]["meaning_packet"] == json.loads(prepared.meaning_json)
    assert body["material"]["control"]["actual_question_budget_remaining"] == 0
    assert build_model_messages(req) == initial


@pytest.mark.parametrize("mutation", ["prompt_offsets", "utf8_offsets", "missing_conflicts",
    "bindings_object", "nested_surface", "literal_predicate", "observation_object",
    "reception_null", "missing_source_entity", "merged_claims", "envelope_byte_offsets",
    "field_path_prefix", "missing_core", "claim_conflicts", "binding_section_label", "inner_source_id"])
def test_explained_output_errors_remain_rejected_without_repair(mutation):
    # Regression classes observed in the real diagnostic. Synthetic packets
    # exercise the unchanged consumer; no real raw is corrected or substituted.
    req = initial_model_request()
    packet = model_packet(req)
    assert prepare_model_snapshot(req, model_semantic(req, packet)).checkpoint
    candidate = packet["candidate"]
    if mutation == "prompt_offsets":
        packet["evidence"][0]["start"] += 406
        packet["evidence"][0]["end"] += 406
    elif mutation == "utf8_offsets":
        ev = packet["evidence"][0]
        field = req.current_input_bundle.raw_current_input[ev["field_path"]]
        ev["start"], ev["end"] = (len(field[:ev["start"]].encode("utf-8")),
                                  len(field[:ev["end"]].encode("utf-8")))
    elif mutation == "missing_conflicts":
        candidate.pop("conflicts")
    elif mutation == "bindings_object":
        surface = candidate["surface_proposal"]
        surface["bindings"] = {row["section"]: row for row in surface["bindings"]}
    elif mutation == "nested_surface":
        candidate["claims"][0]["surface_proposal"] = candidate.pop("surface_proposal")
    elif mutation == "literal_predicate":
        candidate["claims"][0]["predicate"]["surface"] = "the same exact quote as claim.text"
    elif mutation == "observation_object":
        candidate["surface_proposal"]["observation"] = {"text": candidate["surface_proposal"]["observation"]}
    elif mutation == "reception_null":
        candidate["surface_proposal"]["reception"] = None
    elif mutation == "missing_source_entity":
        candidate["claims"][0]["subject"].pop("source_entity")
    elif mutation == "merged_claims":
        candidate["claims"][0]["text"] += candidate["claims"].pop(1)["text"]
    elif mutation == "envelope_byte_offsets":
        ev = packet["evidence"][0]
        native = next(e for e in prepare_emlis(req).payload()["sources"][0]["evidence"]
                      if e["field_path"] == ev["field_path"])
        ev["start"], ev["end"] = native["utf8_start"], native["utf8_end"]
    elif mutation == "field_path_prefix":
        packet["evidence"][0]["field_path"] = "text_fields." + packet["evidence"][0]["field_path"]
    elif mutation == "inner_source_id":
        packet["evidence"][0]["source_id"] = req.emlis_thread.original_source_ref
    elif mutation == "missing_core":
        candidate.pop("core")
    elif mutation == "claim_conflicts":
        candidate["claims"][0]["conflicts"] = candidate.pop("conflicts")
    elif mutation == "binding_section_label":
        candidate["surface_proposal"]["bindings"][0]["section"] = "repair_result"
    raw = json.dumps(packet, ensure_ascii=False)
    prepared = prepare_emlis(req)
    receipt = receive_candidate(prepared, request_id=prepared.request_id,
                                raw_output=raw, finish_reason="stop")
    assert receipt.raw_output == raw
    if mutation in {"prompt_offsets", "utf8_offsets", "envelope_byte_offsets", "field_path_prefix", "inner_source_id"}:
        assert receipt.status == "INVALID_EVIDENCE"
    else:
        assert receipt.status == "CANDIDATE_UNREVIEWED"
        with pytest.raises(SemanticNotAdopted):
            prepare_model_snapshot(req, model_semantic(req, packet))
    assert json.loads(receipt.raw_output) == packet


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
