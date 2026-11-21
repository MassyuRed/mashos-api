import asyncio
import hashlib
import json

import pytest

from cocolon_meaning_experience_engine.deep_insight_question import (
    ANSWER_READ_SYSTEM_MESSAGE, PLAN_SYSTEM_MESSAGE, READ_SYSTEM_MESSAGE,
    RECORD_REASON_READ_SYSTEM_MESSAGE, WRITE_SYSTEM_MESSAGE,
    _bind_anchor, _display_citation_matches, generate_question, prepare_question_material,
)


RECORD_ID = "00000000-0000-0000-0000-000000000123"
ANSWER_ID = "00000000-0000-0000-0000-000000000124"
VERSION = "b" * 64
STAMP = "2026-11-21T10:00:00Z"
QUOTE = "頼まれたことを先にした"
BODY = "どんな理由からですか？"
QUESTION = f"「{QUOTE}」と書いていましたが、{BODY}"


def source(text=QUOTE + "。", **changes):
    return {
        "id": RECORD_ID, "source_version": VERSION, "thought": text,
        "action": None, "created_at": STAMP, "emlis_open_question": None, **changes,
    }


def material(*records, prior=(), map_reference=None):
    return {"records": records, "prior": prior, "map": map_reference}


def ask(**changes):
    return {"decision": "ask", "focus": "REASON", "source": "r1.thought",
            "quote": QUOTE, "condition": "", "ask": "引用した内容の理由", **changes}


def read(plan, *, record_reason=False, **changes):
    result = {"verdict": "accept", "focus": plan["focus"], "condition": plan["condition"],
              "premise_supported": True, "new_information": True}
    if not record_reason:
        result.update(source=plan["source"], quote=plan["quote"])
    return {**result, **changes}


def run(original, plan, question=BODY, *, reading=None, lane="records", theme=None):
    prepared, sources = prepare_question_material(original, lane=lane, theme=theme)
    calls = []

    async def generate(system, payload):
        calls.append((system, payload))
        if system == PLAN_SYSTEM_MESSAGE:
            response = plan
        elif system == WRITE_SYSTEM_MESSAGE:
            response = {"question": question}
        else:
            assert system in (READ_SYSTEM_MESSAGE, ANSWER_READ_SYSTEM_MESSAGE, RECORD_REASON_READ_SYSTEM_MESSAGE)
            response = reading if reading is not None else read(plan, record_reason=system == RECORD_REASON_READ_SYSTEM_MESSAGE)
        return json.dumps(response, ensure_ascii=False)

    result = asyncio.run(generate_question(prepared, sources, material=original, generate=generate))
    return result, calls


def test_plan_write_read_are_separate_and_receipt_resolves_original():
    original_text = "  " + QUOTE + "。"
    result, calls = run(material(source(original_text)), ask())
    assert result.disposition == "selected"
    assert [system for system, _ in calls] == [PLAN_SYSTEM_MESSAGE, WRITE_SYSTEM_MESSAGE, RECORD_REASON_READ_SYSTEM_MESSAGE]
    assert "question" not in calls[0][1] and "sources" not in calls[1][1]
    assert calls[2][1] == {"question": QUESTION, "material": calls[0][1]}
    candidate = result.candidate
    receipt = candidate.receipt
    assert candidate.text == QUESTION
    assert receipt["policy_version"] == "deep-insight.v2"
    assert receipt["source_id"] == RECORD_ID and receipt["source_version"] == VERSION
    assert receipt["field"] == "thought"
    assert receipt["start"] == 2 and original_text[receipt["start"]: receipt["end"]] == QUOTE
    assert receipt["literal_sha256"] == hashlib.sha256(QUOTE.encode()).hexdigest()
    assert candidate.question_key == "deep-insight-target-" + receipt["target_key"]


def test_explicit_reason_stops_before_writing_but_new_condition_can_pass():
    original = material(source("相手が困っていたので、" + QUOTE + "。"))
    result, calls = run(original, ask())
    assert result.disposition == "rejected" and len(calls) == 1

    plan = ask(focus="CONDITION", ask="自分の仕事を先にする条件")
    question = "逆に、自分の仕事を先にするのはどんなときですか？"
    result, calls = run(original, plan, question)
    assert result.disposition == "selected" and len(calls) == 3


@pytest.mark.parametrize("updates", [
    {"premise_supported": False},
    {"new_information": False},
    {"new_information": 1},
    {"focus": "CONDITION"},
    {"source": "r2.thought"},
    {"condition": "家庭"},
    {"verdict": "reject"},
])
def test_independent_reading_must_support_the_actual_candidate(updates):
    result, calls = run(material(source()), ask(), reading=read(ask(), record_reason=True, **updates))
    assert result.disposition == "rejected" and result.candidate is None
    assert len(calls) == 3


@pytest.mark.parametrize("plan,question", [
    (ask(), "家族のために仕事をやめたのはどうしてですか？"),
    (ask(focus="CONDITION"), BODY),
    (ask(), "どうしてですか？ほかにはどんなことがありますか？"),
    (ask(), QUESTION),
])
def test_unwarranted_premise_focus_change_and_multiple_questions_stop_before_reader(plan, question):
    result, calls = run(material(source()), plan, question)
    assert result.disposition == "rejected" and len(calls) == 2


@pytest.mark.parametrize("quote,new_action", [
    (QUOTE, "頼まれたことを先に引き受けた理由は何ですか？"),
    ("残っていた資料を先に直した", "残っていた資料を新しく作った理由は何ですか？"),
])
def test_record_reason_is_about_the_literal_event_even_if_the_planner_paraphrases(quote, new_action):
    plan = ask(quote=quote, ask="先に引き受けた理由")
    original = material(source(quote + "。"))
    result, calls = run(original, plan, new_action)
    assert result.disposition == "rejected" and len(calls) == 2
    assert calls[1][1]["quote"] == quote
    assert calls[1][1]["ask"] == "引用した内容の理由"

    result, calls = run(original, plan, "そうしたのは、なぜですか？")
    assert result.disposition == "selected" and calls[2][0] == RECORD_REASON_READ_SYSTEM_MESSAGE
    assert result.candidate.text == f"「{quote}」と書いていましたが、そうしたのは、なぜですか？"
    assert result.candidate.receipt["literal_sha256"] == hashlib.sha256(quote.encode()).hexdigest()


def test_display_citation_is_bound_to_the_selected_span_without_reader_copy():
    quote = "残っていた資料を先に直した"
    original = material(source(quote + "。お礼の連絡を後から送った。"))
    _, sources = prepare_question_material(original, lane="records", theme=None)
    anchor = _bind_anchor(sources["r1.thought"], quote)
    assert _display_citation_matches(f"「{quote}」と書いていましたが、{BODY}", anchor)
    assert not _display_citation_matches(f"「{quote}{BODY}」と書いていましたが、{BODY}", anchor)
    assert not _display_citation_matches(f"「お礼の連絡を後から送った」と書いていましたが、{BODY}", anchor)
    result, calls = run(original, ask(quote=quote), reading=read(ask(quote=quote), record_reason=True))
    assert result.disposition == "selected" and len(calls) == 3
    assert calls[2][1]["question"].startswith(f"「{quote}」")


def test_plan_boundary_removes_only_a_source_literal_terminal_mark():
    plan = ask(quote=QUOTE + "。", ask="頼まれたことを先にした理由")
    accepted, calls = run(material(source()), plan)
    assert accepted.disposition == "selected"
    assert calls[1][1]["quote"] == QUOTE
    assert calls[2][1]["question"] == QUESTION
    assert accepted.candidate.receipt["end"] == len(QUOTE)
    assert accepted.candidate.receipt["literal_sha256"] == hashlib.sha256(QUOTE.encode()).hexdigest()

    for text in (QUOTE + "よ。", QUOTE + "。" + QUOTE + "よ。"):
        rejected, calls = run(material(source(text)), plan)
        assert rejected.disposition == "rejected" and len(calls) == 1

    known = "相手が困っていたので、" + QUOTE + "。"
    reason_already_written, calls = run(material(source(known)), ask(quote=known, ask="相手が困っていた理由"))
    assert reason_already_written.disposition == "rejected" and len(calls) == 1


def test_writer_can_repeat_the_exact_displayed_event_once_with_no_extra_premise():
    quote = "残っていた資料を先に直した"
    original = material(source(quote + "。"))
    plan = ask(quote=quote, ask="先に引き受けた理由")
    recorded_write = quote + "のは、" + BODY
    accepted, calls = run(original, plan, recorded_write)
    final = f"「{quote}」と書いていましたが、{BODY}"
    assert accepted.disposition == "selected" and accepted.candidate.text == final
    assert calls[2][1]["question"] == final and final.count(quote) == 1

    for wrong in ("残っていた資料を新しく作ったのは、" + BODY,
                  quote + "のは" + BODY,
                  quote + "のは、家族のために仕事をやめた理由は何ですか？",
                  quote + "のは、" + quote + "のは、" + BODY):
        rejected, calls = run(original, plan, wrong)
        assert rejected.disposition == "rejected" and len(calls) == 2


def test_record_reason_preserves_explicit_original_condition_and_action_field():
    plan = ask(source="r1.action", condition="仕事")
    original = material(source(None, action="仕事では頼まれたことを先にした。"))
    result, _ = run(original, plan, "仕事のときに、そうしたのはなぜですか？")
    assert result.disposition == "selected" and result.candidate.receipt["field"] == "action"
    rejected, _ = run(original, plan, "家庭のときに、そうしたのはなぜですか？")
    assert rejected.disposition == "rejected"


def test_answer_alone_has_private_provenance_and_can_supply_a_follow_up():
    answer = {
        "id": ANSWER_ID, "source_version": VERSION, "question_text": "どんなときに友達だと感じますか？",
        "answer_text": "意見が違っても本音を言えるときです。", "answered_at": STAMP,
    }
    quote = "意見が違っても本音を言える"
    plan = ask(focus="CONDITION", source="a1", quote=quote, ask="相手がどう聞くかの条件")
    text = "相手がどんなふうに話を聞いてくれると、本音を言いやすいですか？"
    result, calls = run(material(prior=[answer]), plan, text, reading=read(
        plan, quote="意見が違っても本音を言えるときです"))
    assert result.disposition == "selected"
    assert calls[0][1]["previous_questions"][0]["answer_source"] == "a1"
    assert calls[2][0] == ANSWER_READ_SYSTEM_MESSAGE
    assert result.candidate.receipt["field"] == "answer"
    assert result.candidate.receipt["source_id"] == ANSWER_ID
    assert result.candidate.receipt["end"] == len(quote)
    rejected, _ = run(material(prior=[answer]), plan, text, reading=read(
        plan, quote="意見が違っても本音を言えるはずです"))
    assert rejected.disposition == "rejected"


def test_theme_needs_no_history_but_an_unrelated_meal_is_rejected():
    plan = ask(focus="RELATIONSHIP", source="", quote="", ask="友達だと感じる場面")
    original = material()
    result, _ = run(original, plan, "どんなときに、この人は友達だなと感じますか？",
                    lane="theme", theme="人間関係")
    assert result.disposition == "selected"
    assert result.candidate.receipt["source_id"] is None
    result, calls = run(original, plan, "朝ごはんに何を食べたいですか？",
                        lane="theme", theme="人間関係")
    assert result.disposition == "rejected" and len(calls) == 2


def test_two_conditions_do_not_collapse_from_surface_similarity():
    original = material(source("仕事と家庭のそれぞれで頼まれたことを先にした。"))
    work = ask(focus="CONDITION", condition="仕事", ask="仕事で優先する条件")
    home = ask(focus="CONDITION", condition="家庭", ask="家庭で優先する条件")
    work_text = "仕事ではどんな条件なら順番を変えますか？"
    home_text = "家庭ではどんな条件なら順番を変えますか？"
    first, _ = run(original, work, work_text)
    prior = {"question_text": first.candidate.text, "question_key": first.candidate.question_key,
             "text_key": first.candidate.text_key, "answer_text": None, "answered_at": None}
    second, _ = run(material(*original["records"], prior=[prior]), home, home_text)
    assert second.disposition == "selected"
    assert first.candidate.question_key != second.candidate.question_key


def test_target_identity_does_not_change_with_quote_length():
    original = material(source("昨日、" + QUOTE + "。"))
    first, _ = run(original, ask())
    short = "頼まれたことを先に"
    shorter = ask(quote=short)
    second, _ = run(original, shorter, "どうしてそうしたのですか？")
    assert first.candidate.question_key == second.candidate.question_key
    prior = {"question_text": first.candidate.text, "question_key": first.candidate.question_key,
             "text_key": first.candidate.text_key, "answer_text": None, "answered_at": None}
    blocked, calls = run(material(*original["records"], prior=[prior]), shorter, "どうしてそうしたのですか？")
    assert blocked.disposition == "rejected" and len(calls) == 2


def test_map_or_unversioned_text_cannot_supply_a_record_anchor():
    result, calls = run(material(source(source_version=None),
                                 map_reference={"summary": QUOTE, "generated_at": STAMP}), ask())
    assert result.disposition == "no_merit" and not calls


def test_valid_skip_is_not_conflated_with_malformed_plan():
    original = material(source())
    result, calls = run(original, {"decision": "skip"})
    assert result.disposition == "no_merit" and len(calls) == 1
    result, calls = run(original, {"decision": "ask"})
    assert result.disposition == "rejected" and len(calls) == 1
