"""Optional finite hints cannot consume the original natural reply's budget."""
import asyncio
from copy import deepcopy
import hashlib
import json

import httpx
import pytest

from cocolon_meaning_experience_engine.natural_reply import (
    MEANING_SUPPORT_MAX_BYTES,
    MEANING_SUPPORT_MAX_WITNESS_BYTES,
    MEANING_SUPPORT_MAX_WITNESSES,
    MEANING_SUPPORT_MESSAGES_MAX_BYTES,
    MEANING_SUPPORT_MESSAGE,
    NaturalReplyInput,
    SelfHostedNaturalReplySource,
    SYSTEM_MESSAGE,
    material_with_meaning_support,
    system_message_for,
)
from cocolon_meaning_experience_engine.natural_reply_meaning import (
    compare_reply_meaning,
    prepare_meaning_support,
)


def encoded(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def material(memo):
    return {"current": {"memo": memo, "memo_action": "", "category": ["仕事"],
            "emotions": ["平穏"], "emotion_details": [{"type": "平穏", "strength": "weak"}],
            "created_at": "2026-11-08T08:00:00+00:00"},
        "current_input_id": "current-input", "current_answers": [],
        "past_user_records": [], "user_frame_feedback": []}


def messages(value):
    return [{"role": "system", "content": system_message_for(value)},
            {"role": "user", "content": encoded(value)}]


def test_base_prompt_is_byte_identical_to_the_pre_reuse_prompt():
    # This is the original current prompt, before optional reuse instructions.
    assert len(SYSTEM_MESSAGE.encode("utf-8")) == 2627
    assert hashlib.sha256(SYSTEM_MESSAGE.encode("utf-8")).hexdigest() == (
        "9c76df27ff323720b89ff51459aa1161c94fbfd96551bc3de4e42ba94683d293")


def test_no_witness_keeps_all_base_material_and_the_exact_original_prompt():
    original = material("「私は友人に頼まれた」と同僚が話した。")
    before = deepcopy(original)
    prepared = material_with_meaning_support(original)
    assert prepared is original and original == before
    assert system_message_for(prepared) == SYSTEM_MESSAGE
    assert system_message_for(NaturalReplyInput("prefix", encoded(prepared))) == SYSTEM_MESSAGE


def test_written_person_called_honnin_is_not_the_record_writer():
    written = material_with_meaning_support(material("本人は友人に頼んだ。"))
    writer = material_with_meaning_support(material("私は友人に頼んだ。"))
    assert written['source_meaning_support']['witnesses'][0]['行為者'] == '原文の人物表記：本人'
    assert writer['source_meaning_support']['witnesses'][0]['行為者'] == '記録を書いた本人'


def test_past_wish_is_not_projected_as_a_current_generation_hint():
    original = material('原文を読み返していた。')
    original['past_user_records'] = [dict(input_id='past', recorded_at='2026-10-01T00:00:00Z',
        original=material('私は資料を書きたい。')['current'], answers=[])]
    original['past_user_records'][0]['original']['created_at'] = '2026-10-01T00:00:00Z'
    before = deepcopy(original)
    assert material_with_meaning_support(original) is original
    assert original == before and system_message_for(original) == SYSTEM_MESSAGE
    assert prepare_meaning_support(original)['witnesses'][0]['source_group'] == 'PAST'


def test_bounded_compact_hints_declare_missing_witnesses_without_truncating_source():
    original = material("私は資料を書いた。" * 12)
    before = deepcopy(original)
    prepared = material_with_meaning_support(original)
    support = prepared["source_meaning_support"]
    assert original == before and prepared["current"] == before["current"]
    assert {key: value for key, value in prepared.items()
            if key != "source_meaning_support"} == before
    assert 0 < support["included_witness_count"] <= MEANING_SUPPORT_MAX_WITNESSES
    assert support["total_witness_count"] == 12
    assert support["omitted_witness_count"] == 12 - support["included_witness_count"] > 0
    assert len(encoded(support).encode("utf-8")) <= MEANING_SUPPORT_MAX_BYTES
    assert len(encoded(messages(prepared)).encode("utf-8")) <= MEANING_SUPPORT_MESSAGES_MAX_BYTES
    for witness in support["witnesses"]:
        assert len(encoded(witness).encode("utf-8")) <= MEANING_SUPPORT_MAX_WITNESS_BYTES
        assert "utf8_start" not in witness and "agent" not in witness
        assert original["current"]["memo"][witness["scalar_start"]:witness["scalar_end"]]
    assert system_message_for(prepared) == SYSTEM_MESSAGE + MEANING_SUPPORT_MESSAGE


def test_long_source_loses_only_optional_hints_and_full_comparison_still_reads_it():
    original = material("私は資料を書いた。" * 150)
    before = deepcopy(original)
    prepared = material_with_meaning_support(original)
    assert prepared is original and original == before
    assert "source_meaning_support" not in prepared
    assert system_message_for(prepared) == SYSTEM_MESSAGE
    assert len(prepare_meaning_support(original)["witnesses"]) == 150
    review = compare_reply_meaning(encoded(prepared), "あなたは資料を書いたのですね。", "prefix")
    assert review.source_witness_count == 150
    assert review.verdict == "UNASSESSED"  # No arbitrary choice among repeated events.


def test_utf8_oversized_witness_is_omitted_whole_without_losing_the_next_small_one():
    large = "石" * 48 + "は" + "川" * 48 + "に" + "山" * 48 + "を頼んだ。"
    original = material(large + "私は友人に頼まれた。")
    full = prepare_meaning_support(original)
    assert len(full["witnesses"]) == 2
    prepared = material_with_meaning_support(original)
    support = prepared["source_meaning_support"]
    assert support["total_witness_count"] == 2 and support["included_witness_count"] == 1
    assert support["omitted_witness_count"] == 1
    assert support["witnesses"][0]["行為者"] == "原文の人物表記：友人"
    assert support["witnesses"][0]["相手"] == "記録を書いた本人"
    assert prepared["current"]["memo"] == original["current"]["memo"]


@pytest.mark.parametrize("error", [ValueError("unsupported-scope"), RuntimeError("reader-bug")])
def test_optional_reader_failure_preserves_original_material_and_base_prompt(monkeypatch, error):
    import cocolon_meaning_experience_engine.natural_reply_meaning as meaning

    def unavailable(*args):
        raise error

    monkeypatch.setattr(meaning, "prepare_meaning_support", unavailable)
    original = material("私は友人に頼まれた。")
    assert material_with_meaning_support(original) is original
    assert system_message_for(original) == SYSTEM_MESSAGE


def test_long_material_uses_the_original_http_payload_without_new_context_loss():
    original = material("私は資料を書いた。" * 150)
    request_material = encoded(material_with_meaning_support(original))
    sent = []

    def transport(request):
        sent.append(request)
        payload = json.loads(request.content)
        assert payload["messages"] == messages(original)
        assert payload["max_tokens"] == 2048
        assert len(request.content) < 65536
        return httpx.Response(200, json={"model": "synthetic-4b", "choices": [{
            "finish_reason": "stop", "message": {"role": "assistant", "content": "受け取りました。"}}]})

    provider = SelfHostedNaturalReplySource(endpoint="https://model.invalid/v1/chat/completions",
        model="synthetic-4b", api_key="synthetic-only", transport=httpx.MockTransport(transport))
    reply = asyncio.run(provider(NaturalReplyInput("prefix", request_material)))
    assert reply.text == "受け取りました。" and len(sent) == 1
