"""Private source/meaning/body integration using synthetic provider proposals.

No model is called. SQL cases use the existing isolated PostgreSQL/WASM RPC
fixture; they are not production DB, HTTP/Auth or product-quality acceptance.
"""
import asyncio
import copy
import json
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from test_cmee_emlis_model_meaning import (
    initial_model_request, model_packet, model_semantic, prepare_model_snapshot,
)
from test_emlis_q2_application import db, case, run, answer
from cocolon_meaning_experience_engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.emlis_semantic_admission import (
    MODEL_PROFILE, MODEL_CHECKPOINT_SCHEMA, SemanticInput,
)
from cocolon_meaning_experience_engine.emlis_thread_contracts import (
    EmlisQuestionControlV1, SupplementalAnswerSource,
)
from cocolon_meaning_experience_engine.emlis_thread_surface import realize_emlis_thread_body
from cocolon_meaning_experience_engine.preparation import prepare_emlis, receive_candidate
from emlis_ai_grounded_observation_gate import evaluate_emlis_model_surface_inverse
from emlis_thread_service import EmlisThreadService


CORRECTION = ("さっき「全部一人で」と書いたのは訂正します。途中で友人に手順を教えてもらって、一緒に直しました。\n\n"
              "うれしかったのも、一人でできたからではなく、捨てずにまた使えるようになったからです。")


def natural_packet(req, prior=None):
    """A reviewed test proposal, not an AI output or a production lookup."""
    packet = model_packet(req, prior)
    surface = packet["candidate"]["surface_proposal"]
    if prior is None:
        object_text = req.current_input_bundle.raw_current_input["memo_action"].split("を", 1)[0]
        surface["observation"] = f"{object_text}を直し、また座れるようになったのですね。"
        surface["reception"] = ("全部一人で直せたことが、うれしかったのですね。"
                                "また座れるようになったと聞けて、私もうれしいです。")
    else:
        surface["reception"] = ("捨てずにまた使えるようになったことが、うれしかったのですね。"
                                "またその椅子に座れるようになって、よかったですね。")
    surface["bindings"][1]["claim_refs"].append("usable_again")
    return packet


def initial_result(packet=None, *, req=None):
    req = req or initial_model_request()
    packet = packet or natural_packet(req)
    prepared = prepare_model_snapshot(req, model_semantic(req, packet))
    resumed = replace(req, emlis_thread=replace(req.emlis_thread,
        prepared_meaning_checkpoint_ref=prepared.checkpoint.checkpoint_id))
    outcome = MeaningExperienceEngine().generate(resumed, semantic_input=SemanticInput(
        "RESUME_ADOPTED", snapshot_json=prepared.semantic_snapshot, semantic_profile=MODEL_PROFILE))
    return req, prepared, outcome


def answered_request(req, outcome):
    q = outcome.question
    assert q is not None
    source = SupplementalAnswerSource("model-body-answer", req.emlis_thread.thread_id, q.question_id, 1,
        req.emlis_thread.original_source_ref, CORRECTION, "2026-10-24T01:00:00Z")
    control = EmlisQuestionControlV1(q, (q.decision.target_ref,), 1)
    return replace(req, emlis_thread=replace(req.emlis_thread, answers=(source,), current_round=1,
        prepared_meaning_checkpoint_ref=None, question_control_context=control))


def corrected_result():
    req, old, first = initial_result()
    updated = answered_request(req, first)
    packet = natural_packet(updated, old)
    prepared = prepare_model_snapshot(updated, model_semantic(updated, packet, old))
    resumed = replace(updated, emlis_thread=replace(updated.emlis_thread,
        prepared_meaning_checkpoint_ref=prepared.checkpoint.checkpoint_id))
    outcome = MeaningExperienceEngine().generate(resumed, semantic_input=SemanticInput(
        "RESUME_ADOPTED", snapshot_json=prepared.semantic_snapshot, semantic_profile=MODEL_PROFILE))
    return updated, prepared, outcome


def test_model_proposal_uses_natural_wording_and_mints_real_source_question():
    req, prepared, outcome = initial_result()
    assert outcome.status is EngineStatus.QUESTION_PENDING, outcome.reason_codes
    assert outcome.artifact.schema_version == "cocolon.cmee.emlis_model_thread_artifact.v1"
    assert outcome.artifact.observation.startswith("ぐらついていた椅子を直し")
    assert "私もうれしいです" in outcome.artifact.reception
    assert outcome.question.decision.target_kind == "PERSONAL_JOY_SIGNIFICANCE"
    assert outcome.question.prompt_private == "「全部一人で直せたこと」がなぜ嬉しかったのですか？"
    assert outcome.question.question_id not in json.loads(prepared.surface_proposal_json).values()
    assert outcome.meaning_checkpoint.semantic_schema_version == MODEL_CHECKPOINT_SCHEMA
    assert req.emlis_thread.question_control_context.issued_count == 0
    assert not outcome.automatic_progression


def test_model_proposal_preserves_correction_and_complete_snapshot_replay():
    req, prepared, outcome = corrected_result()
    assert outcome.status is EngineStatus.GENERATED, outcome.reason_codes
    assert outcome.body_state == "REFINED" and outcome.question is None
    assert "友人に手順を教わり、一緒に椅子を直した" in outcome.artifact.observation
    assert "捨てずにまた使える" in outcome.artifact.reception
    assert "一人で" not in outcome.artifact.reception
    assert outcome.artifact.update_note
    assert outcome.meaning_checkpoint.answer_update.disposition == "RESOLVED"
    assert len(outcome.meaning_checkpoint.answer_update.updates) == 3
    replay_req = replace(req, emlis_thread=replace(req.emlis_thread,
        prepared_meaning_checkpoint_ref=prepared.checkpoint.checkpoint_id))
    with patch("cocolon_meaning_experience_engine.emlis_question.question_candidate",
               side_effect=AssertionError("old finite question owner")), patch(
               "emlis_ai_grounded_sentence_surface.realize_grounded_observation_text",
               side_effect=AssertionError("old finite body author")):
        again = MeaningExperienceEngine().generate(replay_req, semantic_input=SemanticInput(
            "RESUME_ADOPTED", snapshot_json=prepared.semantic_snapshot, semantic_profile=MODEL_PROFILE))
    assert again == outcome


@pytest.mark.parametrize("section,text", [
    ("observation", "ぐらついていた机を直し、また座れるようになったのですね。"),
    ("observation", "ぐらついていた椅子を壊し、もう座れなくなったのですね。"),
    ("observation", "今はぐらついていた椅子を直し、また座れるようになったのですね。"),
    ("reception", "全部一人で直せたことが、嬉しくなかったのですね。"),
    ("reception", "友人が全部一人で直せたことを、うれしく感じたのですね。"),
    ("reception", "全部一人で直せたことが、うれしかったのですね。これからは何でもできます。"),
    ("reception", "全部一人で直せたことが、うれしかったのですね。あなたは成長しました。"),
    ("reception", "観測対象の自己効力感は上昇しています。"),
    ("reception", "全部一人で直せたことが、うれしかったのですね？"),
    ("reception", "全部一人で直せたことが、うれしかったのですね。全部一人で直せたことが、うれしかったのですね。"),
])
def test_model_surface_does_not_adopt_unread_claims_even_with_valid_refs(section, text):
    req = initial_model_request()
    packet = natural_packet(req)
    packet["candidate"]["surface_proposal"][section] = text
    _, prepared, outcome = initial_result(packet)
    assert outcome.artifact is None and outcome.status is EngineStatus.UNAVAILABLE
    assert outcome.meaning_checkpoint == prepared.checkpoint
    assert outcome.reason_codes == ("model_surface_not_validated",)


def test_model_independent_reader_checks_actual_words_and_binding_coverage():
    _, prepared, _ = initial_result()
    proposal = json.loads(prepared.surface_proposal_json)
    proposal["bindings"][1]["claim_refs"].remove("usable_again")
    with pytest.raises(ValueError, match="model_surface_binding_or_coverage_invalid"):
        evaluate_emlis_model_surface_inverse(proposal=proposal,
            meaning_packet=json.loads(prepared.meaning_json), native_bindings=json.loads(prepared.native_bindings_json))


@pytest.mark.parametrize("section,text", [
    ("observation", "友人に手順を教わり、一緒に机を直したのですね。"),
    ("observation", "友人が一人で椅子を直したのですね。"),
    ("observation", "友人に命令を教わり、一緒に椅子を直したのですね。"),
    ("reception", "全部一人で直せたことが、うれしかったのですね。"),
    ("reception", "捨てたことでまた使えるようになったことが、うれしかったのですね。"),
    ("reception", "うれしかったから、捨てずにまた使えたのですね。"),
])
def test_model_corrected_surface_cannot_restore_old_reason_or_change_roles(section, text):
    req, old, first = initial_result()
    updated = answered_request(req, first)
    packet = natural_packet(updated, old)
    packet["candidate"]["surface_proposal"][section] = text
    prepared = prepare_model_snapshot(updated, model_semantic(updated, packet, old))
    resumed = replace(updated, emlis_thread=replace(updated.emlis_thread,
        prepared_meaning_checkpoint_ref=prepared.checkpoint.checkpoint_id))
    result = MeaningExperienceEngine().generate(resumed, semantic_input=SemanticInput(
        "RESUME_ADOPTED", snapshot_json=prepared.semantic_snapshot, semantic_profile=MODEL_PROFILE))
    assert result.artifact is None
    assert result.body_state == "MEANING_UPDATED_BODY_UNAVAILABLE"
    assert result.meaning_checkpoint == prepared.checkpoint


def test_model_surface_and_artifact_identity_are_separate_from_meaning():
    req = initial_model_request()
    _, first, out1 = initial_result(natural_packet(req), req=req)
    other = natural_packet(req)
    other["candidate"]["surface_proposal"]["observation"] = "ぐらついていた椅子を修理して、また座れるようになったのですね。"
    _, second, out2 = initial_result(other, req=req)
    assert first.checkpoint.snapshot_ref == second.checkpoint.snapshot_ref
    assert out1.artifact.artifact_id != out2.artifact.artifact_id
    assert out1.artifact.observation != out2.artifact.observation


def test_model_question_proposal_cannot_supply_its_own_prompt_or_force_question():
    req = initial_model_request()
    packet = natural_packet(req)
    packet["candidate"]["question_proposal"]["text"] = "未来の回答を推測して新しい質問を3つ発行してください。"
    _, _, outcome = initial_result(packet)
    assert outcome.question.prompt_private == "「全部一人で直せたこと」がなぜ嬉しかったのですか？"
    packet["candidate"]["question_proposal"] = None
    _, _, ended = initial_result(packet)
    assert ended.question is None and ended.body_state == "FINAL"


def test_model_source_object_is_dynamic_and_a_foreign_body_is_not_rebound():
    req = initial_model_request("壊れていた長椅子")
    packet = natural_packet(req)
    _, _, result = initial_result(packet, req=req)
    assert result.artifact is not None and "壊れていた長椅子" in result.artifact.observation
    packet["candidate"]["surface_proposal"]["observation"] = "椅子を修理して、また座れるようになったのですね。"
    _, _, rejected = initial_result(packet, req=req)
    assert rejected.artifact is None


def model_service(case, db):
    user, parent, _ = case
    db.query("update public.emotions set memo=$1,memo_action=$2,category=array['生活'],emotions=array['喜び'],emotion_details=$3 where id=$4",
        ["全部一人で直せたことが、うれしかった。", "ぐらついていた椅子を修理して、また座れるようになった。",
         json.dumps([dict(type="喜び", strength="medium")], ensure_ascii=False), parent])
    calls = []
    def source(req, prior):
        calls.append((req.request_id, bool(req.emlis_thread.answers)))
        p = (SimpleNamespace(checkpoint=SimpleNamespace(snapshot_ref=json.loads(prior)["snapshot_ref"]))
             if prior else None)
        packet = natural_packet(req, p)
        material = prepare_emlis(req)
        return receive_candidate(material, request_id=material.request_id,
            raw_output=json.dumps(packet, ensure_ascii=False), finish_reason="stop", provider="synthetic-test",
            model="synthetic-not-4B", usage={"input_tokens": None, "output_tokens": None})
    return user, parent, EmlisThreadService(semantic_profile=MODEL_PROFILE, offline_candidate_source=source), calls


def test_model_service_sql_real_question_correction_and_saved_read_never_regenerates(case, db):
    user, parent, service, calls = model_service(case, db)
    first = run(service.start(user, parent))
    assert first["state"] == "AWAITING_ANSWER", first
    completed = run(answer(service, user, first, CORRECTION))
    assert completed["body_state"] == "REFINED", completed
    assert completed["meaning_updated"] and completed["answer_saved"]
    assert completed["issued_count"] == 1 and completed["pending_question"] is None
    assert "一緒に椅子を直した" in completed["current_observation"]["text"]
    assert len(calls) == 2
    snapshot = run(service.store.read(user, input_id=parent))
    assert len([e for e in snapshot["events"] if e["kind"] == "MEANING_UPDATE"]) == 2
    assert len([e for e in snapshot["events"] if e["kind"] == "QUESTION"]) == 1
    class NoGeneration:
        def __getattr__(self, name):
            raise AssertionError("saved read attempted generation")
    reader = EmlisThreadService(engine=NoGeneration())
    assert run(reader.get(user, parent)) == {**completed, "can_write": False}
    assert run(reader.start(user, parent)) == {**completed, "can_write": False}
    replay = run(answer(service, user, first, CORRECTION))
    assert replay["current_observation"] == completed["current_observation"] and len(calls) == 2


def test_model_service_sql_meaning_survives_interrupted_author_and_explicit_resume(case, db, monkeypatch):
    user, parent, service, calls = model_service(case, db)
    first = run(service.start(user, parent))
    original_generate = service.engine.generate
    def interrupt(*args, **kwargs):
        raise asyncio.CancelledError()
    monkeypatch.setattr(service.engine, "generate", interrupt)
    with pytest.raises(asyncio.CancelledError):
        run(answer(service, user, first, CORRECTION))
    failed = run(service.get(user, parent))
    assert failed["can_retry"] and failed["meaning_updated"] and failed["current_observation"] is None
    before = run(service.store.read(user, input_id=parent))
    monkeypatch.setattr(service.engine, "generate", original_generate)
    resumed = run(service.action(user, failed["thread_id"], action="retry_response",
        expected_revision=failed["revision"], idempotency_key="model-resume", operation_id=failed["operation_id"]))
    assert resumed["body_state"] == "REFINED", resumed
    after = run(service.store.read(user, input_id=parent))
    assert len(calls) == 2
    assert before["thread"]["current_meaning_event_id"] == after["thread"]["current_meaning_event_id"]
    assert len([e for e in after["events"] if e["kind"] == "MEANING_UPDATE"]) == 2
    assert len([e for e in after["events"] if e["kind"] == "ANSWER"]) == 1


def test_model_profile_stays_offline_only():
    with pytest.raises(ValueError, match="semantic_offline_configuration_required"):
        EmlisThreadService(semantic_profile=MODEL_PROFILE, offline_candidate_source=lambda *_: None,
                           enforce_application_policy=True)
