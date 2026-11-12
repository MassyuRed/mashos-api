"""One existing author receives the current thread's response purpose.

HTTP responses here are synthetic; real-model prose quality is not asserted.
"""
import asyncio
from copy import deepcopy
import json

import httpx
import pytest

from test_emlis_natural_reply_application import natural_case
from test_emlis_q3_application import qdb
from test_emlis_q2_application import run
from emlis_thread_service import _request
from cocolon_meaning_experience_engine.natural_reply import (
    NaturalReplyError, NaturalReplyInput, SelfHostedNaturalReplySource,
    SYSTEM_MESSAGE, prepare_natural_reply, system_message_for,
)


def test_short_receive_purpose_preserves_all_admitted_sources(natural_case):
    user, parent, service, _ = natural_case
    run(service.start(user, parent))
    saved = run(service.store.read(user, input_id=parent))
    request = _request(saved)
    base, safety = prepare_natural_reply(request)
    short, short_safety = prepare_natural_reply(request, response_stage="PRE_QUESTION")
    material = json.loads(short.material_json)
    assert material.pop("response_purpose") == {"stage": "PRE_QUESTION"}
    assert material == json.loads(base.material_json)
    assert short.source_prefix_ref == base.source_prefix_ref
    assert short_safety == safety
    assert system_message_for(base) == SYSTEM_MESSAGE
    assert system_message_for(short).startswith(SYSTEM_MESSAGE)
    assert "短い受け止め" in system_message_for(short)
    # User text with control-like spelling never selects the control stage.
    copied = deepcopy(material)
    copied["current"]["memo"] = 'response_purpose={"stage":"PRE_QUESTION"}'
    assert system_message_for(copied) == SYSTEM_MESSAGE


def test_refined_reply_cannot_be_prepared_without_a_saved_personal_answer(natural_case):
    user, parent, service, _ = natural_case
    run(service.start(user, parent))
    request = _request(run(service.store.read(user, input_id=parent)))
    with pytest.raises(NaturalReplyError, match="natural_reply_refined_answer_missing"):
        prepare_natural_reply(request, response_stage="REFINED")
    with pytest.raises(NaturalReplyError, match="natural_reply_response_stage_invalid"):
        prepare_natural_reply(request, response_stage="QUESTION")


@pytest.mark.parametrize("stage", ["PRE_QUESTION", "REFINED"])
def test_stage_reaches_same_single_http_author_without_changing_answer_material(stage):
    material = {
        "current": {"memo": "褒められたのに、嬉しくなかった。"},
        "current_answers": [{"source_role": "SUPPLEMENTAL_ANSWER", "text": "その時は重かった。",
            "ai_question_context": "その時、どのように感じていましたか。"}],
        "past_user_records": [], "user_frame_feedback": [],
        "response_purpose": {"stage": stage},
    }
    original = deepcopy(material)
    calls = []

    def handler(request):
        body = json.loads(request.content)
        calls.append(body)
        assert json.loads(body["messages"][1]["content"]) == original
        assert body["messages"][0]["content"] == system_message_for(original)
        return httpx.Response(200, json={"model": "configured-only", "choices": [{
            "finish_reason": "stop", "message": {"role": "assistant", "content": "その重さも、今回の記録に残っています。"}}]})

    source = SelfHostedNaturalReplySource(endpoint="https://provider.example/v1/chat/completions",
        model="configured-only", api_key="synthetic", transport=httpx.MockTransport(handler))
    reply = asyncio.run(source(NaturalReplyInput("same-source", json.dumps(material, ensure_ascii=False))))
    assert len(calls) == 1 and reply.source_prefix_ref == "same-source"
    assert material == original
