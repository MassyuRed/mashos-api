import asyncio
import hashlib
import json
import random
from itertools import islice, product

import pytest

from cocolon_meaning_experience_engine import deep_insight_question
from cocolon_meaning_experience_engine.deep_insight_question import (
    ANSWER_READ_SYSTEM_MESSAGE, PLAN_SYSTEM_MESSAGE, READ_SYSTEM_MESSAGE,
    RECORD_REASON_READ_SYSTEM_MESSAGE, WRITE_SYSTEM_MESSAGE,
    _RECORD_ALTERNATIVE_PLAN_MESSAGE, _RECORD_ALTERNATIVE_READ_MESSAGE, _RECORD_ALTERNATIVE_WRITE_MESSAGE,
    _THEME_COMPARE_EVIDENCE_SYSTEM_MESSAGE, _THEME_COMPARE_PAIR_SYSTEM_MESSAGE, _THEME_COMPARE_SYSTEM_MESSAGE,
    _THEME_PLAN_SYSTEM_MESSAGE, _THEME_READ_RETRY_SYSTEM_MESSAGE, _THEME_READ_SYSTEM_MESSAGE,
    _THEME_FORM_REPAIR_SYSTEM_MESSAGE, _THEME_REPAIR_SYSTEM_MESSAGE, _THEME_WRITE_SYSTEM_MESSAGE,
    _bind_anchor, _display_citation_matches, _review_theme_candidate, _theme_has_new_answer, _theme_position_key,
    generate_question, prepare_question_material,
)

from cocolon_meaning_experience_engine.deep_insight_theme import (
    THEME_DISTINCT_POSITIONS, THEME_EQUIVALENT_POSITIONS, THEME_SCENES, THEME_TARGET_FORMS, THEME_VERIFIED_BODIES,
)
from cocolon_meaning_experience_engine.deep_insight_theme_intents import THEME_SCENE_ANGLE_TARGETS


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


def run(original, plan, question=BODY, *, reading=None, alternative=None):
    prepared, sources = prepare_question_material(original, lane="records", theme=None)
    calls = []

    async def generate(system, payload):
        calls.append((system, payload))
        if system.startswith(PLAN_SYSTEM_MESSAGE):
            response = plan
        elif system.startswith(_RECORD_ALTERNATIVE_PLAN_MESSAGE):
            assert alternative is not None
            response = alternative
        elif system in (WRITE_SYSTEM_MESSAGE, _RECORD_ALTERNATIVE_WRITE_MESSAGE):
            response = {"question": question}
        else:
            assert system.startswith((
                READ_SYSTEM_MESSAGE, ANSWER_READ_SYSTEM_MESSAGE, RECORD_REASON_READ_SYSTEM_MESSAGE,
                _RECORD_ALTERNATIVE_READ_MESSAGE,
            ))
            selected_plan = plan if alternative is None else {**ask(), **alternative}
            response = reading if reading is not None else read(
                selected_plan, record_reason=system.startswith((
                    RECORD_REASON_READ_SYSTEM_MESSAGE, _RECORD_ALTERNATIVE_READ_MESSAGE,
                )))
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


def test_dismissed_emlis_wording_is_deny_only_and_blocks_the_same_anchored_body():
    original = material(source(emlis_skipped_question=BODY))
    result, calls = run(original, ask())
    assert result.disposition == "rejected" and result.candidate is None
    assert len(calls) == 2
    planner, writing = calls
    assert "skipped_emlis_questions" in planner[0]
    assert planner[1]["skipped_emlis_questions"] == [{"question": BODY, "sources": ["r1.thought"]}]
    assert set(planner[1]["sources"]) == {"r1.thought"}
    assert planner[1]["open_emlis_questions"] == planner[1]["answered_emlis_questions"] == []
    assert "skipped_emlis_questions" not in writing[1]


def test_dismissed_question_scope_reaches_reader_without_blocking_another_record():
    other = source("まだ残っていた資料を先に直した。", id="00000000-0000-0000-0000-000000000017")
    original = material(source(emlis_skipped_question=BODY), other)
    result, calls = run(original, ask(source="r2.thought", quote="残っていた資料を先に直した"))
    assert result.disposition == "selected"
    assert "skipped_emlis_questions" in calls[2][0]
    assert calls[2][1]["material"]["skipped_emlis_questions"] == [
        {"question": BODY, "sources": ["r1.thought"]},
    ]


def test_reader_can_refuse_a_paraphrase_of_a_dismissed_emlis_question():
    original = material(source(emlis_skipped_question=BODY))
    result, calls = run(original, ask(), "そうしたのはなぜですか？",
                        reading={"verdict": "reject", "new_information": False})
    assert result.disposition == "rejected" and result.candidate is None
    assert len(calls) == 3 and "skipped_emlis_questions" in calls[2][0]


def test_record_is_not_retained_if_its_dismissal_cannot_fit(monkeypatch):
    plain, _ = prepare_question_material(material(source()), lane="records", theme=None)
    cap = len(json.dumps(plain, ensure_ascii=False, separators=(",", ":")).encode())
    monkeypatch.setattr(deep_insight_question, "_MAX_MATERIAL_BYTES", cap)

    original = material(source(emlis_skipped_question=BODY))
    prepared, sources = prepare_question_material(original, lane="records", theme=None)
    assert not sources and not prepared["sources"]
    assert "skipped_emlis_questions" not in prepared


@pytest.mark.parametrize("reason_quote", ["相手が困っていたので", "相手が困っていたので、" + QUOTE])
def test_explicit_reason_is_replaced_only_by_a_supported_new_condition(reason_quote):
    causal_sentence = "相手が困っていたので、" + QUOTE
    original = material(source(causal_sentence + "。自分の仕事はまだ途中だった。"))
    invalid_plan = ask(quote=reason_quote, ask="相手が困っていた理由")
    condition = {"decision": "ask", "focus": "CONDITION", "ask": "自分の仕事を先にする条件"}

    question = "同じような場面で、自分の仕事を先にするのはどんなときですか？"
    result, calls = run(original, invalid_plan, question, alternative=condition)
    assert result.disposition == "selected"
    assert [system for system, _ in calls] == [
        PLAN_SYSTEM_MESSAGE, _RECORD_ALTERNATIVE_PLAN_MESSAGE,
        _RECORD_ALTERNATIVE_WRITE_MESSAGE, _RECORD_ALTERNATIVE_READ_MESSAGE,
    ]
    assert result.candidate.text == f"「{QUOTE}」と書いていましたが、{question}"
    assert calls[1][1] == {"action": QUOTE, "alternatives": ["自分の仕事はまだ途中だった"], "material": calls[0][1]}
    assert calls[2][1] == {
        "lane": "records", "theme": None, "focus": "CONDITION", "quote": QUOTE,
        "condition": "", "ask": condition["ask"], "alternatives": ["自分の仕事はまだ途中だった"],
    }
    assert calls[3][1] == {"citation": QUOTE, "body": question, "material": calls[0][1]}
    receipt = result.candidate.receipt
    assert original["records"][0]["thought"][receipt["start"]:receipt["end"]] == QUOTE

    result, calls = run(original, invalid_plan, "自分の仕事を先にしたとき、どんな条件がありましたか？",
                        reading={"verdict": "reject", "reason": "unsupported_premise"}, alternative=condition)
    assert result.disposition == "rejected" and len(calls) == 4


def test_alternative_writer_reversing_the_choice_is_still_rejected_by_the_reader():
    causal_sentence = "相手が困っていたので、" + QUOTE
    original = material(source(causal_sentence + "。自分の仕事はまだ途中だった。"))
    result, calls = run(
        original, ask(quote=causal_sentence, ask="相手が困っていた理由"),
        "頼まれたことを先にすることの条件は、どんなときですか？",
        alternative={"decision": "ask", "focus": "CONDITION", "ask": "同じような場面で自分の仕事を先にする条件"},
        reading={
            "verdict": "accept", "focus": "CONDITION", "source": "r1.thought", "quote": QUOTE,
            "condition": "相手が困っていた", "premise_supported": False, "new_information": True,
        },
    )
    assert result.disposition == "rejected" and result.candidate is None
    assert calls[-1][0] == _RECORD_ALTERNATIVE_READ_MESSAGE
    assert calls[-1][1] == {
        "citation": QUOTE,
        "body": "頼まれたことを先にすることの条件は、どんなときですか？",
        "material": calls[0][1],
    }


@pytest.mark.parametrize("overrides", [
    {
        # Raw fields returned by the general 4B reader for a correct alternate question.
        "quote": "相手が困っていたので、" + QUOTE, "condition": "相手が困っていたとき",
        "premise_supported": False, "new_information": False,
    },
    {"quote": "相手が困っていたので、" + QUOTE},
    {"source": "r2.thought"},
    {"condition": "相手が困っていたとき"},
    {"premise_supported": False},
    {"new_information": False},
    {"verdict": "reject", "reason": "already_answered"},
])
def test_alternative_reader_must_return_semantics_without_a_citation_override(overrides):
    original = material(source("相手が困っていたので、" + QUOTE + "。自分の仕事はまだ途中だった。"))
    question = "同じような場面で、自分の仕事を先にするのはどんなときですか？"
    result, calls = run(
        original, ask(), question,
        alternative={"decision": "ask", "focus": "CONDITION", "ask": "同じような場面で自分の仕事を先にする条件"},
        reading=read(ask(focus="CONDITION"), record_reason=True, **overrides),
    )
    assert result.disposition == "rejected" and result.candidate is None and len(calls) == 4
    assert calls[-1] == (_RECORD_ALTERNATIVE_READ_MESSAGE, {
        "citation": QUOTE, "body": question, "material": calls[0][1],
    })


def test_alternative_planning_refuses_the_same_citation_in_another_field():
    original = material(source(
        "相手が困っていたので、" + QUOTE + "。自分の仕事はまだ途中だった。",
        action=QUOTE + "。",
    ))
    result, calls = run(
        original, ask(),
        alternative={"decision": "ask", "focus": "CONDITION", "ask": "自分の仕事を先にする条件"},
    )
    assert result.disposition == "rejected" and result.candidate is None
    assert [system for system, _ in calls] == [PLAN_SYSTEM_MESSAGE, _RECORD_ALTERNATIVE_PLAN_MESSAGE]


def test_alternative_reader_can_reject_an_undocumented_action():
    original = material(source("相手が困っていたので、" + QUOTE + "。自分の仕事はまだ途中だった。"))
    result, calls = run(
        original, ask(), "同じような場面で、翌日の献立を先に考えるのはどんなときですか？",
        alternative={"decision": "ask", "focus": "CONDITION", "ask": "同じような場面で自分の仕事を先にする条件"},
        reading={"verdict": "reject", "reason": "unsupported_premise"},
    )
    assert result.disposition == "rejected" and result.candidate is None and len(calls) == 4
    assert calls[-1][0] == _RECORD_ALTERNATIVE_READ_MESSAGE


def test_alternative_reader_still_rejects_an_answer_beyond_the_visible_citation():
    evidence = "自分の仕事の締切が当日なら、自分の仕事を先に進める"
    original = material(source("相手が困っていたので、" + QUOTE + "。自分の仕事はまだ途中だった。"
                               + evidence + "。"))
    question = "同じような場面で、自分の仕事を先にするのはどんなときですか？"
    result, calls = run(
        original, ask(), question,
        alternative={"decision": "ask", "focus": "CONDITION", "ask": "同じような場面で自分の仕事を先にする条件"},
        reading={"verdict": "reject", "reason": "already_answered", "evidence": evidence},
    )
    assert result.disposition == "rejected" and result.candidate is None
    assert calls[-1] == (_RECORD_ALTERNATIVE_READ_MESSAGE, {
        "citation": QUOTE, "body": question, "material": calls[0][1],
    })
    assert evidence in calls[-1][1]["material"]["sources"]["r1.thought"]["text"]


@pytest.mark.parametrize("response,disposition", [
    ({"decision": "skip"}, "no_merit"),
    ({"decision": "ask", "focus": "REASON", "ask": "相手が困っていた理由"}, "rejected"),
    ({"decision": "ask", "focus": "CONDITION", "source": "a1", "ask": "仕事を先にする条件"}, "rejected"),
])
def test_alternative_planning_cannot_repeat_reason_or_choose_another_source(response, disposition):
    original = material(source("相手が困っていたので、" + QUOTE + "。自分の仕事はまだ途中だった。"))
    result, calls = run(original, ask(), alternative=response)
    assert result.disposition == disposition and result.candidate is None and len(calls) == 2


def test_alternative_planning_still_blocks_a_dismissed_question_before_reading():
    question = "同じような場面で、自分の仕事を先にするのはどんなときですか？"
    original = material(source("相手が困っていたので、" + QUOTE + "。自分の仕事はまだ途中だった。",
                               emlis_skipped_question=question))
    result, calls = run(original, ask(), question, alternative={
        "decision": "ask", "focus": "CONDITION", "ask": "自分の仕事を先にする条件",
    })
    assert result.disposition == "rejected" and result.candidate is None and len(calls) == 3
    assert "skipped_emlis_questions" in calls[1][0]


def test_explicit_reason_without_a_new_question_can_still_skip():
    original = material(source("相手が困っていたので、" + QUOTE + "。"))
    result, calls = run(original, {"decision": "skip"})
    assert result.disposition == "no_merit" and len(calls) == 1
    result, calls = run(original, ask(quote="相手が困っていたので", ask="相手が困っていた理由"))
    assert result.disposition == "rejected" and len(calls) == 1


def test_invalid_reason_quote_cannot_trigger_alternative_planning():
    original = material(source("相手が困っていたので、" + QUOTE + "。自分の仕事はまだ途中だった。"))
    result, calls = run(original, ask(quote="原文にはない理由"))
    assert result.disposition == "rejected" and len(calls) == 1


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


def select_theme_angle(scene, angle):
    return lambda values: next(value for value in values if value[0] in (scene, angle))


def theme_pair_result(verdict="distinct"):
    earlier = "以前の選択を決めた基準"
    return {"previous_answer": earlier,
            "question_answer": "今回の選択で最初に取る行動" if verdict == "distinct" else earlier,
            "verdict": verdict}


def theme_run(theme, question, *, questions=(), reading=None, comparison=None, extra=None,
              scene=None, target=None, repair=None, rereading=None, raw_write=False,
              choose_theme=lambda values: values[0]):
    original = {"questions": questions, **(extra or {})}
    prepared, sources = prepare_question_material(
        original, lane="theme", theme=theme, choose_theme=choose_theme,
    )
    calls = []

    async def generate(system, payload):
        calls.append((system, payload))
        if system == _THEME_PLAN_SYSTEM_MESSAGE:
            return json.dumps({"scene": scene, "target": target}, ensure_ascii=False)
        if system.startswith(_THEME_WRITE_SYSTEM_MESSAGE):
            return question if raw_write else json.dumps({"question": question}, ensure_ascii=False)
        if system.startswith((_THEME_REPAIR_SYSTEM_MESSAGE, _THEME_FORM_REPAIR_SYSTEM_MESSAGE)):
            return json.dumps({"question": repair or question}, ensure_ascii=False)
        if system.startswith(_THEME_READ_RETRY_SYSTEM_MESSAGE) and rereading is not None:
            return json.dumps(rereading, ensure_ascii=False)
        if system == _THEME_COMPARE_SYSTEM_MESSAGE:
            return json.dumps(comparison if comparison is not None else {"verdict": "distinct"})
        return json.dumps(reading if reading is not None
                          else {"verdict": "accept"})

    result = asyncio.run(generate_question(prepared, sources, material=original, generate=generate))
    return result, calls


def test_theme_needs_no_history_but_an_unrelated_meal_is_rejected():
    theme = "人間関係"
    question = "最初にどんな話題を出しますか？"
    result, calls = theme_run(theme, question)
    assert result.disposition == "selected"
    assert result.candidate.receipt["source_id"] is None
    assert result.candidate.text == f"初対面の人と話すとき、{question}"
    assert [system for system, _ in calls] == [_THEME_WRITE_SYSTEM_MESSAGE, _THEME_READ_SYSTEM_MESSAGE]
    result, calls = theme_run(theme, "朝ごはんに何を食べたいですか？")
    assert result.disposition == "rejected" and len(calls) == 2


@pytest.mark.parametrize("raw", [
    "最初にどんな話題を出しますか？",
    "「最初にどんな話題を出しますか？」",
    "{'question': '最初にどんな話題を出しますか？'}",
])
def test_theme_reads_single_question_wrappers_but_still_checks_the_display(raw):
    selected, calls = theme_run("人間関係", raw, raw_write=True)
    assert selected.candidate.text == "初対面の人と話すとき、最初にどんな話題を出しますか？"
    assert calls[1][0] == _THEME_READ_SYSTEM_MESSAGE

    rejected, _ = theme_run("人間関係", raw, raw_write=True, reading={"verdict": "reject", "reason": "angle"})
    assert rejected.disposition == "rejected"


def test_theme_provider_sees_only_selected_direction_and_previous_question_wording():
    theme = "人間関係"
    previous = "人と距離を縮めたいと思うのはどんな場面ですか？"
    result, calls = theme_run(theme, "最初にどんな話題を出しますか？",
        questions=[{"question_key": "prior", "question_text": previous,
                    "answer_text": "回答は渡さない", "answered_at": STAMP}],
        extra={"records": [source("本人記録は渡さない")], "map": {"summary": "マップは渡さない"}})
    assert result.disposition == "selected"
    writer, reader, comparer = [payload for _, payload in calls]
    direction = {"target": "最初のひと言", "angle": "話し始めるために最初にすること"}
    assert writer == {**direction, "scene": "初対面の人と話すとき",
                      "form": "最初にどんなひと言をかけますか？"}
    assert reader == {
        **direction, "theme": theme, "scene": "初対面の人と話すとき",
        "body": "最初にどんな話題を出しますか？", "answer_kind": "first_action",
    }
    assert comparer == {
        **direction, "theme": theme, "scene": reader["scene"],
        "question": result.candidate.text, "history": [{"id": 1, "question": previous}],
    }
    assert calls[1][0] == _THEME_READ_SYSTEM_MESSAGE
    assert calls[2][0] == _THEME_COMPARE_SYSTEM_MESSAGE


@pytest.mark.parametrize("reason", ["surface", "angle", "premise"])
def test_theme_reader_must_accept_scene_and_angle(reason):
    reading = {"verdict": "reject", "reason": reason}
    result, calls = theme_run("人間関係", "最初にどんな話題を出しますか？",
                              reading=reading)
    assert result.disposition == "rejected"
    assert len(calls) == 4
    if reason == "surface":
        assert calls[2][0] == _THEME_FORM_REPAIR_SYSTEM_MESSAGE
        assert set(calls[2][1]) == {"form", "scene"}
    else:
        assert calls[2][1]["reason"] == reason


@pytest.mark.parametrize("corrected_read", [None, {"verdict": "accept"}])
def test_theme_retries_only_the_reader_when_it_echoes_the_scene_and_body(corrected_read):
    draft = "一度伝え方を決めた後、どんなときにもう一方の方法に切り替えますか？"
    result, calls = theme_run(
        "人間関係", draft, choose_theme=select_theme_angle("contact_channel", "change"),
        reading={"scene": "大切な話をメッセージにするか直接伝えるか迷ったとき", "body": draft},
        rereading=corrected_read,
    )
    assert [system for system, _ in calls] == [
        _THEME_WRITE_SYSTEM_MESSAGE, _THEME_READ_SYSTEM_MESSAGE, _THEME_READ_RETRY_SYSTEM_MESSAGE,
    ]
    assert calls[1][1] == calls[2][1]
    if corrected_read is None:
        assert result.disposition == "rejected" and result.candidate is None
    else:
        assert result.candidate.text == f"{calls[1][1]['scene']}、{draft}"


def test_theme_replaces_two_independent_answers_with_one_before_the_reader():
    draft = "本格的に切り替える前に、どの程度の範囲で別の方法を試し、その結果をどう判断しますか？"
    revised = "本格的に切り替える前に、どこまで別の方法を試しますか？"
    selected, calls = theme_run(
        "仕事・学び", draft, repair=revised, choose_theme=select_theme_angle("experiment", "boundary"),
    )
    assert calls[1][0] == _THEME_FORM_REPAIR_SYSTEM_MESSAGE
    assert set(calls[1][1]) == {"form", "scene"}
    assert calls[2][1]["body"] == revised
    assert selected.candidate.text.endswith(revised)


def test_theme_preserves_an_unmade_choice_in_the_independent_review():
    result, calls = theme_run(
        "仕事・学び", "新しいやり方に切り替えるために、まず何をしますか？",
        reading={"verdict": "reject", "reason": "premise"},
        choose_theme=select_theme_angle("experiment", "first_action"),
    )
    writer, reader, repair, _ = [payload for _, payload in calls]
    assert result.disposition == "rejected"
    assert writer["premise"] == reader["premise"] == repair["premise"]
    assert "二つの方法を試し比べ始める段階" in reader["premise"]
    assert "form" not in reader and "draft" not in repair
    assert "どの選択が未確定か" in calls[0][0] and "どの選択が未確定か" in calls[2][0]
    assert calls[1][0].startswith(_THEME_READ_SYSTEM_MESSAGE)
    assert calls[1][0] != _THEME_READ_SYSTEM_MESSAGE


def test_theme_distinguishes_two_ordering_questions_by_their_answer_targets():
    theme = "これからのこと"
    history = [{
        "question_key": _theme_position_key(theme, "several_goals", "priority"),
        "question_text": "始めてみたいことがいくつかあるとき、どれから始めるか何を基準に決めますか？",
    }]
    result, calls = theme_run(
        theme, "新しい生活にも残す習慣は、何を基準に選びますか？",
        questions=history, choose_theme=select_theme_angle("change_habits", "priority"),
    )
    assert result.disposition == "selected"
    assert calls[-1][0] == _THEME_COMPARE_SYSTEM_MESSAGE
    assert calls[-1][1]["target"] == "暮らしを変えても残しておきたい習慣"
    assert calls[-1][1]["history"] == [{"id": 1, "question": history[0]["question_text"]}]


@pytest.mark.parametrize("recent_count", [0, 30])
def test_theme_uses_reviewed_distinction_for_recent_and_archived_displays(recent_count):
    theme = "自分の価値観"
    previous, _ = theme_run(theme, THEME_VERIFIED_BODIES[(theme, "ownership", "boundary")][-1],
                            choose_theme=select_theme_angle("ownership", "boundary"))
    old = {"question_key": previous.candidate.question_key, "text_key": previous.candidate.text_key}
    if not recent_count:
        old["question_text"] = previous.candidate.text
    recent = [{"question_key": f"recent-{i}", "question_text": f"{i}回目は何を選びますか？"}
              for i in range(recent_count)]
    body = THEME_VERIFIED_BODIES[(theme, "risk", "boundary")][0]
    result, calls = theme_run(theme, body, questions=recent + [old],
                              choose_theme=select_theme_angle("risk", "boundary"))
    assert result.disposition == "selected"
    assert calls[0][1]["form"] == body
    assert calls[1][1]["body"] == body
    assert calls[1][1]["answer_kind"] == "boundary"
    assert "form" not in calls[1][1]
    if recent_count:
        assert calls[2][0] == _THEME_COMPARE_SYSTEM_MESSAGE
        assert calls[2][1]["history"] == [{"id": i + 1, "question": row["question_text"]}
                                         for i, row in enumerate(recent)]
    else:
        assert len(calls) == 2


@pytest.mark.parametrize("changed", ["prior_key", "prior_wording", "current_wording"])
def test_theme_still_compares_displays_outside_reviewed_distinction(changed):
    theme = "自分の価値観"
    previous, _ = theme_run(theme, THEME_VERIFIED_BODIES[(theme, "ownership", "boundary")][0],
                            choose_theme=select_theme_angle("ownership", "boundary"))
    old = {"question_key": previous.candidate.question_key, "text_key": previous.candidate.text_key,
           "question_text": previous.candidate.text}
    body = THEME_VERIFIED_BODIES[(theme, "risk", "boundary")][0]
    if changed == "prior_key":
        old["text_key"] = "unknown"
    elif changed == "prior_wording":
        old["question_text"] = "うまくいかない場合に、どの程度の負担を引き受けますか？"
    else:
        body = "失敗したときは、どの範囲まで損を受け入れられますか？"
    result, calls = theme_run(theme, body, questions=[old], comparison={"verdict": "repeat", "id": 1},
                              choose_theme=select_theme_angle("risk", "boundary"))
    assert result.disposition == "rejected"
    assert calls[2][0] == _THEME_COMPARE_SYSTEM_MESSAGE
    assert calls[2][1]["history"][0]["question"] == old["question_text"]
    assert calls[3][0] == _THEME_COMPARE_PAIR_SYSTEM_MESSAGE


@pytest.mark.parametrize(("issued_scene", "next_scene"), [
    ("new_method", "experiment"), ("experiment", "new_method"),
])
def test_theme_avoids_an_equivalent_outcome_in_another_scene(issued_scene, next_scene):
    theme = "仕事・学び"
    key = _theme_position_key(theme, issued_scene, "outcome")

    def choose(options):
        if len(options[0]) == 4:
            return next(option for option in options if option[0] == next_scene)
        assert "outcome" not in {angle for angle, _ in options}
        return options[0]

    prepared, _ = prepare_question_material(
        {"questions": [{"question_key": key}]}, lane="theme", theme=theme, choose_theme=choose,
    )
    assert prepared["question_key"] != _theme_position_key(theme, next_scene, "outcome")


@pytest.mark.parametrize(("issued", "equivalent"), [("change", "boundary"), ("boundary", "change")])
def test_theme_avoids_asking_twice_when_to_stop_researching_alone(issued, equivalent):
    theme = "仕事・学び"
    recent = [{"question_key": f"recent-{i}"} for i in range(30)]
    old = {"question_key": _theme_position_key(theme, "stuck", issued)}

    def choose(options):
        if len(options[0]) == 4:
            # Every scene has one issued slot, so we can revisit this one.
            return next(option for option in options if option[0] == "stuck")
        assert equivalent not in {angle for angle, _ in options}
        return options[0]

    other_scenes = [{"question_key": _theme_position_key(theme, scene, "first_action")}
                    for scene in THEME_SCENES[theme] if scene != "stuck"]
    prepared, _ = prepare_question_material(
        {"questions": recent + [old] + other_scenes}, lane="theme", theme=theme, choose_theme=choose,
    )
    assert prepared["question_key"] != _theme_position_key(theme, "stuck", equivalent)


def test_theme_checks_cited_wording_then_rechecks_the_rest_of_the_history():
    question = {"question": "守りたい約束と目の前の都合がぶつかったとき、どこまで負担を引き受けますか？"}
    earlier = {"id": 1, "question": "人に勧められたことを試すとき、どこまで負担を引き受けますか？"}
    other = {"id": 2, "question": "自分のルールを見直そうと決めるのはどんなときですか？"}
    responses = iter([{"verdict": "repeat", "id": 1}, theme_pair_result(), {"verdict": "distinct"}])
    calls = []

    async def generate(system, payload):
        calls.append((system, payload))
        return json.dumps(next(responses))

    assert asyncio.run(_theme_has_new_answer(question, [earlier, other], generate))
    assert calls == [
        (_THEME_COMPARE_SYSTEM_MESSAGE, {**question, "history": [earlier, other]}),
        (_THEME_COMPARE_PAIR_SYSTEM_MESSAGE, {**question, "previous": earlier["question"]}),
        (_THEME_COMPARE_SYSTEM_MESSAGE, {**question, "history": [other]}),
    ]
    assert list(calls[1][1]) == ["previous", "question"]


@pytest.mark.parametrize("pair", [
    {"verdict": "distinct"},
    {**theme_pair_result(), "question_answer": " "},
    {**theme_pair_result(), "question_answer": "、。？"},
    {**theme_pair_result(), "question_answer": theme_pair_result()["previous_answer"]},
])
def test_theme_does_not_clear_a_matched_question_without_two_distinct_answer_targets(pair):
    question = {"question": "何を最初に試しますか？"}
    history = [{"id": 1, "question": "前に何を試しましたか？"}]
    responses = iter([{"verdict": "repeat", "id": 1}, pair])

    async def generate(system, payload):
        return json.dumps(next(responses))

    assert not asyncio.run(_theme_has_new_answer(question, history, generate))


@pytest.mark.parametrize(("previous", "current", "previous_excerpt", "current_excerpt", "difference"), [
    (
        "その場で伝えようと思ったあと、どんなことがあれば別の機会に伝えますか？",
        "少数派の意見をその場で伝えるかどうかは、何を基準に決めますか？",
        "その場で伝えようと思ったあと", "伝えるかどうか",
        "予定を別の機会に変えるきっかけからは、まだ伝えると決めていない時の基準は分からない。",
    ),
    (
        "覚えたことを初めて人に教えるとき、説明の組み立てを決める前に、相手の理解について何を確かめますか？",
        "覚えたことを初めて人に教えるとき、説明に入る前にまず何をしますか？",
        "相手の理解について何を確かめますか", "説明に入る前にまず何をしますか",
        "図を描くという準備の行動を答えても、相手の理解について何を確認するかは分からない。",
    ),
    (
        "どんなときに自分で調べ続けるのをやめて別の方法を取りますか？",
        "手が止まった直後に、まず何を見直しますか？",
        "自分で調べ続けるのをやめて別の方法を取りますか", "まず何を見直しますか",
        "直前の手順を見直すと答えても、別の方法に切り替える条件は分からない。",
    ),
])
def test_theme_rechecks_a_repeat_verdict_against_both_original_questions(
    previous, current, previous_excerpt, current_excerpt, difference,
):
    question = {"question": current}
    past = {"id": 1, "question": previous}
    other = {"id": 2, "question": "どのくらいの時間を取りますか？"}
    responses = iter([
        {"verdict": "repeat", "id": 1},
        theme_pair_result("repeat"),
        {"verdict": "distinct", "previous_excerpt": previous_excerpt,
         "question_excerpt": current_excerpt, "difference": difference},
        {"verdict": "distinct"},
    ])
    calls = []

    async def generate(system, payload):
        calls.append((system, payload))
        return json.dumps(next(responses))

    assert asyncio.run(_theme_has_new_answer(question, [past, other], generate))
    assert calls[2] == (_THEME_COMPARE_EVIDENCE_SYSTEM_MESSAGE, {"previous": previous, "question": current})
    assert calls[3] == (_THEME_COMPARE_SYSTEM_MESSAGE, {**question, "history": [other]})


@pytest.mark.parametrize("evidence", [
    {"verdict": "repeat"},
    {"verdict": "distinct", "previous_excerpt": "どの程度", "question_excerpt": "どのくらい", "difference": "、。"},
    {"verdict": "distinct", "previous_excerpt": "今の仕事", "question_excerpt": "どのくらい", "difference": "量の違いです。"},
    {"verdict": "distinct", "previous_excerpt": "負担", "question_excerpt": "どのくらい", "difference": "量の違いです。"},
])
def test_theme_keeps_paraphrases_blocked_without_text_evidence(evidence):
    question = {"question": "どのくらいの負担まで受け入れられますか？"}
    history = [{"id": 1, "question": "どの程度の負担なら引き受けられますか？"}]
    responses = iter([{"verdict": "repeat", "id": 1}, theme_pair_result("repeat"), evidence])

    async def generate(system, payload):
        return json.dumps(next(responses))

    assert not asyncio.run(_theme_has_new_answer(question, history, generate))


@pytest.mark.parametrize("final_verdict", [{"verdict": "distinct"}, {"verdict": "repeat", "id": 3}])
def test_theme_checks_two_cited_questions_before_the_remaining_history(final_verdict):
    question = {"question": "新しい方法を試すとしたら、どのくらいの負担を引き受けますか？"}
    history = [
        {"id": 1, "question": "約束を守るためにはどこまで負担を引き受けますか？"},
        {"id": 2, "question": "人からの勧めを試すとき、どこまで負担を引き受けますか？"},
        {"id": 3, "question": "慣れた手順を変える前に、試すことにどのくらい負担をかけますか？"},
    ]
    responses = iter([
        {"verdict": "repeat", "id": 1}, theme_pair_result(),
        {"verdict": "repeat", "id": 2}, theme_pair_result(),
        final_verdict, theme_pair_result("repeat"), {"verdict": "repeat"},
    ])
    calls = []

    async def generate(system, payload):
        calls.append((system, payload))
        return json.dumps(next(responses))

    assert asyncio.run(_theme_has_new_answer(question, history, generate)) is (final_verdict["verdict"] == "distinct")
    assert [payload["history"] for system, payload in calls if system == _THEME_COMPARE_SYSTEM_MESSAGE] == [
        history, history[1:], history[2:],
    ]


def test_theme_checks_the_fifth_suspected_repeat_in_long_history():
    question = {"question": "久しぶりに連絡するとしたら、最初に何を伝えますか？"}
    history = [{"id": i, "question": f"{i}回目は何を選びますか？"} for i in range(1, 32)]
    suspects = {4, 7, 10, 12, 30}
    cleared = []
    scanned = []

    async def generate(system, payload):
        if system == _THEME_COMPARE_SYSTEM_MESSAGE:
            ids = [row["id"] for row in payload["history"]]
            scanned.append(ids)
            suspect = next((i for i in ids if i in suspects), None)
            if suspect is None:
                return '{"verdict":"distinct"}'
            suspects.remove(suspect)
            return json.dumps({"verdict": "repeat", "id": suspect})
        assert system == _THEME_COMPARE_PAIR_SYSTEM_MESSAGE
        cleared.append(payload["previous"])
        return json.dumps(theme_pair_result())

    assert asyncio.run(_theme_has_new_answer(question, history, generate))
    assert cleared == [history[i - 1]["question"] for i in (4, 7, 10, 12, 30)]
    assert [len(batch) for batch in scanned[:2]] == [31, 30]
    assert all(len(batch) <= deep_insight_question._THEME_HISTORY_SUBBATCH_SIZE for batch in scanned[2:])
    assert set().union(*map(set, scanned[2:])) == set(range(1, 32)) - {4, 7}


def test_theme_retains_a_true_paraphrase_in_the_last_subbatch():
    question = {"question": "やり方を試した結果、どんな手応えがあれば今後も使おうと思いますか？"}
    earlier = "新しい手順をこの先も使い続ける決め手になる結果は何ですか？"
    history = [{"id": i, "question": f"{i}回目は何を選びますか？"} for i in range(1, 31)]
    history.append({"id": 31, "question": earlier})
    suspects = {1, 2, 31}
    checked_sizes = []

    async def generate(system, payload):
        if system == _THEME_COMPARE_SYSTEM_MESSAGE:
            ids = [row["id"] for row in payload["history"]]
            checked_sizes.append(len(ids))
            suspect = next((i for i in ids if i in suspects), None)
            if suspect:
                suspects.remove(suspect)
                return json.dumps({"verdict": "repeat", "id": suspect})
            return '{"verdict":"distinct"}'
        if system == _THEME_COMPARE_EVIDENCE_SYSTEM_MESSAGE:
            return '{"verdict":"repeat"}'
        assert system == _THEME_COMPARE_PAIR_SYSTEM_MESSAGE
        return json.dumps(theme_pair_result("repeat" if payload["previous"] == earlier else "distinct"))

    assert not asyncio.run(_theme_has_new_answer(question, history, generate))
    assert checked_sizes == [31, 30, 8, 8, 8, 5]
    assert not suspects


def test_theme_rejects_an_unchecked_nomination_after_the_pair_budget():
    question = {"question": "何から新しい手順を試しますか？"}
    history = [{"id": i, "question": f"{i}回目は何を選びますか？"} for i in range(1, 11)]
    pairs = []

    async def generate(system, payload):
        if system == _THEME_COMPARE_SYSTEM_MESSAGE:
            return json.dumps({"verdict": "repeat", "id": payload["history"][0]["id"]})
        assert system == _THEME_COMPARE_PAIR_SYSTEM_MESSAGE
        pairs.append(payload["previous"])
        return json.dumps(theme_pair_result())

    assert not asyncio.run(_theme_has_new_answer(question, history, generate))
    assert len(pairs) == 3


def test_theme_uses_an_archived_position_without_omitting_an_unresolved_match():
    question = {"question": "人に頼まれたことを引き受ける上限はどこまでですか？"}
    old = {"id": 31, "scene": "人に何かを勧められて、応じるか迷ったとき", "target": "負担", "angle": "負担の上限"}

    async def generate(system, payload):
        assert system == _THEME_COMPARE_SYSTEM_MESSAGE
        assert payload["history"] == [old]
        return '{"verdict":"repeat","id":31}'

    assert not asyncio.run(_theme_has_new_answer(question, [old], generate))


@pytest.mark.parametrize("control", ["distinct", "semantic_repeat", "exact_repeat"])
def test_theme_resolves_three_cited_questions_with_archived_history(control):
    theme = "自分の価値観"
    current_position = (theme, "risk", "boundary")
    archived_position = (theme, "ownership", "boundary")
    current_body = THEME_VERIFIED_BODIES[current_position][-1]
    previous_position = current_position if control == "exact_repeat" else archived_position
    previous, _ = theme_run(
        theme, THEME_VERIFIED_BODIES[previous_position][-1],
        choose_theme=select_theme_angle(*previous_position[1:]),
    )
    # An older issuance supplied by SQL has only its position and text keys.
    archived = {"question_key": previous.candidate.question_key, "text_key": previous.candidate.text_key}
    if control == "exact_repeat":
        # A historic wording collision should still block a different position.
        archived["question_key"] = _theme_position_key(theme, *archived_position[1:])
    scenes_and_questions = product(THEME_SCENES[theme].values(), (
        "何を基準に選びますか？", "最初に何をしますか？",
    ))
    recent = [
        {"question_key": f"recent-{i}", "question_text": f"{scene}、{body}"}
        for i, (scene, body) in enumerate(islice(scenes_and_questions, 30))
    ]
    original = {"questions": recent + [archived]}
    prepared, sources = prepare_question_material(
        original, lane="theme", theme=theme, choose_theme=select_theme_angle(*current_position[1:]),
    )
    # Match the order in which the actual 4B retest cited distinct history.
    cited_ids = [21, 30, 17]
    comparisons = []
    pairs = []
    calls = []

    async def generate(system, payload):
        calls.append(system)
        if system.startswith(_THEME_WRITE_SYSTEM_MESSAGE):
            return json.dumps({"question": current_body})
        if system.startswith(_THEME_READ_SYSTEM_MESSAGE):
            return '{"verdict":"accept"}'
        if system == _THEME_COMPARE_SYSTEM_MESSAGE:
            ids = [row["id"] for row in payload["history"]]
            comparisons.append(ids)
            cited = next((i for i in cited_ids if i in ids), None)
            if cited:
                cited_ids.remove(cited)
            return json.dumps({"verdict": "repeat", "id": cited} if cited else {"verdict": "distinct"})
        if system == _THEME_COMPARE_EVIDENCE_SYSTEM_MESSAGE:
            return '{"verdict":"repeat"}'
        assert system == _THEME_COMPARE_PAIR_SYSTEM_MESSAGE
        pairs.append(payload["previous"])
        answer = "repeat" if len(pairs) == 3 and control == "semantic_repeat" else "distinct"
        return json.dumps(theme_pair_result(answer))

    result = asyncio.run(generate_question(prepared, sources, material=original, generate=generate))
    assert len(original["questions"]) == 31
    assert result.disposition == ("selected" if control == "distinct" else "rejected")
    if control == "exact_repeat":
        assert len(calls) == 1
        return
    assert pairs == [recent[i - 1]["question_text"] for i in (21, 30, 17)]
    after_split = [i for i in range(1, 31) if i not in (21, 30)]
    expected = [list(range(1, 31)), [i for i in range(1, 31) if i != 21],
                after_split[:8], after_split[8:16], after_split[16:24]]
    if control == "distinct":
        expected.extend([after_split[17:24], after_split[24:]])
    assert comparisons == expected


@pytest.mark.parametrize("control", ["distinct", "semantic_repeat", "exact_repeat"])
def test_theme_compares_older_legacy_wording_in_the_next_history_batch(control):
    theme = "自分の価値観"
    position = (theme, "risk", "boundary")
    body = THEME_VERIFIED_BODIES[position][-1]
    old_text = "うまくいかない場合、試したい選択でどの程度の損まで受け入れられますか？"
    older = {"question_key": "legacy-slot", "text_key": "legacy-text", "question_text": old_text}
    if control == "exact_repeat":
        # An older algorithm may not have stored the current text key.
        older["question_text"] = f"{THEME_SCENES[theme][position[1]]}、{body}"
    batch_size = deep_insight_question._THEME_HISTORY_BATCH_SIZE
    recent = [
        {"question_key": f"prior-{index}", "question_text": f"{index}回目は何を選びますか？"}
        for index in range(batch_size)
    ]
    original = {"questions": recent + [older]}
    prepared, sources = prepare_question_material(
        original, lane="theme", theme=theme, choose_theme=select_theme_angle(*position[1:]),
    )
    calls = []
    old_id = batch_size + 1

    async def generate(system, payload):
        calls.append((system, payload))
        if system.startswith(_THEME_WRITE_SYSTEM_MESSAGE):
            return json.dumps({"question": body})
        if system.startswith(_THEME_READ_SYSTEM_MESSAGE):
            return '{"verdict":"accept"}'
        if system == _THEME_COMPARE_SYSTEM_MESSAGE:
            if payload["history"][0]["id"] == old_id and control == "semantic_repeat":
                return json.dumps({"verdict": "repeat", "id": old_id})
            return '{"verdict":"distinct"}'
        if system == _THEME_COMPARE_EVIDENCE_SYSTEM_MESSAGE:
            return '{"verdict":"repeat"}'
        assert system == _THEME_COMPARE_PAIR_SYSTEM_MESSAGE
        assert payload["previous"] == old_text
        return json.dumps(theme_pair_result("repeat"))

    result = asyncio.run(generate_question(prepared, sources, material=original, generate=generate))
    assert result.disposition == ("selected" if control == "distinct" else "rejected")
    if control == "exact_repeat":
        assert len(calls) == 1
        return
    compared = [
        row for system, payload in calls if system == _THEME_COMPARE_SYSTEM_MESSAGE for row in payload["history"]
    ]
    assert [row["id"] for row in compared] == list(range(1, old_id + 1))
    assert compared[-1] == {"id": old_id, "question": old_text}


@pytest.mark.parametrize("theme", THEME_SCENES)
def test_theme_selection_does_not_reuse_an_issued_position_over_fifty_draws(theme):
    questions = []
    scenes, angles, keys = set(), set(), set()
    for index in range(50):
        prepared, sources = prepare_question_material(
            {"questions": questions}, lane="theme", theme=theme, choose_theme=random.Random(index).choice,
        )
        key = prepared["question_key"]
        assert not sources and key and key not in keys
        if index < len(THEME_SCENES[theme]):
            assert prepared["scene"] not in scenes
        scenes.add(prepared["scene"])
        angles.add(prepared["angle"])
        keys.add(key)
        questions.insert(0, {"question_key": key, "question_text": f"第{index}回は何を選びますか？"})
        if index >= 30:
            assert len(prepared["previous_questions"]) == 30
            questions[30].pop("question_text", None)
    assert len(scenes) >= len(THEME_SCENES[theme]) and len(angles) > 1


def test_theme_evaluation_selects_fifty_untried_positions_per_theme_after_rejections():
    from io import StringIO

    from ai.tools import deep_insight_theme_batch_eval as batch

    async def reject(*_):
        return "{}"

    selected = batch.cases()
    output = StringIO()
    asyncio.run(batch.evaluate(selected, output, generate=reject))
    manifest, *results, summary = map(json.loads, output.getvalue().splitlines())
    assert manifest["position_selection"] == "seeded_untried_positions"
    assert summary["issued_history_by_theme"] == dict.fromkeys(batch.THEMES, 0)
    assert [row["id"] for row in results] == [case.id for case in selected]
    for theme in batch.THEMES:
        rows = [row for row in results if row["theme"] == theme]
        keys = {row["prepared"]["question_key"] for row in rows}
        assert None not in keys and len(keys) == 50
        assert len({row["prepared_sha256"] for row in rows}) == 50
        assert all(row["disposition"] == "rejected" and row["calls"] for row in rows)
        assert all(row["material"] == {"questions": []} for row in rows)
        assert any("replaced_question_key" in row for row in rows)
        for positions in THEME_EQUIVALENT_POSITIONS.get(theme, ()):
            assert len(keys & {_theme_position_key(theme, *position) for position in positions}) <= 1


def test_theme_will_try_new_situations_after_all_catalog_positions():
    from cocolon_meaning_experience_engine.deep_insight_theme import THEME_ANGLES

    theme = "仕事・学び"
    issued = [{"question_key": _theme_position_key(theme, scene_id, angle_id)}
              for scene_id in THEME_SCENES[theme] for angle_id in THEME_ANGLES]
    result, calls = theme_run(theme, "最初に何を確認しますか？",
        questions=issued, scene="学んだ手順が通じない現場に出会ったとき", target="別の手順を選ぶかどうか")
    assert result.disposition == "selected"
    assert result.candidate.question_key not in {row["question_key"] for row in issued}
    assert [system for system, _ in calls[:3]] == [
        _THEME_PLAN_SYSTEM_MESSAGE, _THEME_WRITE_SYSTEM_MESSAGE, _THEME_READ_SYSTEM_MESSAGE,
    ]
    assert all(system == _THEME_COMPARE_SYSTEM_MESSAGE for system, _ in calls[3:])
    assert sum(len(payload["history"]) for _, payload in calls[3:]) == len(issued)


def test_theme_rejects_old_exact_text_key_and_closed_question():
    theme = "仕事・学び"
    question = "最初に何をしますか？"
    prior, _ = theme_run(theme, question)
    assert prior.candidate is not None
    issued = {"question_key": "other-position", "text_key": prior.candidate.text_key}
    result, calls = theme_run(theme, question, questions=[issued])
    assert result.disposition == "rejected" and len(calls) == 1
    result, calls = theme_run(theme, "手が止まるときはありますか？")
    assert result.disposition == "rejected" and len(calls) == 2


def test_theme_repairs_a_closed_question_containing_its_usual_wording():
    draft = "感謝を伝える言葉をいつもと変えることはありますか？"
    revised = "いつもとは別の言葉を選ぶのは、どんなときですか？"
    result, calls = theme_run(
        "人間関係", draft, repair=revised, choose_theme=select_theme_angle("thanks", "change"),
    )
    assert [system for system, _ in calls] == [
        _THEME_WRITE_SYSTEM_MESSAGE, _THEME_FORM_REPAIR_SYSTEM_MESSAGE, _THEME_READ_SYSTEM_MESSAGE,
    ]
    assert result.candidate.text.endswith(revised)


@pytest.mark.parametrize(("theme", "scene", "angle", "draft", "revised"), [
    ("仕事・学び", "feedback", "cue",
     "指摘された改善点について、具体的に何を直す必要があるかを知っていますか？",
     "どこを直すか決める前に、相手の指摘について何を確かめますか？"),
    ("仕事・学び", "feedback", "cue",
     "どの部分について修正を求められているのかを確かめますか？",
     "直す部分を決める前に、指摘された内容のうち何を確かめますか？"),
    ("仕事・学び", "feedback", "change",
     "指摘された内容が、今の作業手順をどう変える必要があるかを示す具体的な条件はありますか？",
     "指摘にどんな内容があったら、今の作業手順を変えようと思いますか？"),
    ("これからのこと", "leave_space", "boundary",
     "空き時間を保ちながら、用事をどれくらいまで入れるか、その目安はありますか？",
     "空き時間を残すには、用事をどれくらいまで入れますか？"),
])
def test_theme_repairs_a_yes_no_main_clause_with_an_embedded_question(theme, scene, angle, draft, revised):
    result, calls = theme_run(theme, draft, repair=revised, choose_theme=select_theme_angle(scene, angle))
    assert len(calls) == 3
    assert calls[0][0].startswith(_THEME_WRITE_SYSTEM_MESSAGE)
    if angle == "cue":
        assert calls[1][0].startswith(_THEME_REPAIR_SYSTEM_MESSAGE)
        assert "情報そのもの" in calls[1][0] and calls[1][1]["reason"] == "surface"
    else:
        assert calls[1][0] == _THEME_FORM_REPAIR_SYSTEM_MESSAGE
        assert set(calls[1][1]) == {"form", "scene"}
    assert calls[2][0] == _THEME_READ_SYSTEM_MESSAGE
    assert result.candidate.text.endswith(revised)


def test_theme_edit_keeps_the_delayed_outcome_in_the_independent_review():
    form = "しばらくたったあと、どんなことがあれば、考えを見直してよかったと思いますか？"
    draft = "どんなことがあれば、考えを見直してよかったと思いますか？"
    result, calls = theme_run(
        "自分の価値観", draft, repair=form, reading={"verdict": "reject", "reason": "premise"},
        choose_theme=select_theme_angle("change_mind", "outcome"),
    )
    assert "今回はformを校正" in calls[0][0]
    assert calls[0][1]["form"] == calls[1][1]["form"] == form
    assert calls[1][1]["body"] == draft
    assert calls[3][1]["body"] == form
    assert result.candidate is None


@pytest.mark.parametrize(("theme", "scene", "draft", "revised"), [
    ("自分の価値観", "risk",
     "失敗した場合にやり直せる余地があるかどうか、どのように確かめておきますか？",
     "試す前に、やり直しに使える時間や手段について何を確かめますか？"),
    ("自分の価値観", "risk",
     "失敗した場合にやり直せる余地があるかどうか、どのように判断しますか？",
     "うまくいかなかった場合にやり直せる条件のうち、何を確かめておきますか？"),
    ("仕事・学び", "teach",
     "説明の組み立てを決める前に、相手がどこまで分かっているかをどう確かめますか？",
     "説明の組み立てを決める前に、相手の理解について何を確かめますか？"),
    ("日々の過ごし方", "rest_day",
     "用事にかかる時間について、どれくらい見積もりますか？",
     "用事と休息の時間を決める前に、用事にかかる時間について何を確かめますか？"),
    ("日々の過ごし方", "between_tasks",
     "用事の合間に実際に使える時間を決める際、移動や準備に必要な時間をどう確認しますか？",
     "合間の使い道を決める前に、移動や準備にかかる時間について何を確かめますか？"),
])
def test_theme_repairs_a_question_about_the_way_to_check_instead_of_the_cue(theme, scene, draft, revised):
    result, calls = theme_run(theme, draft, repair=revised, choose_theme=select_theme_angle(scene, "cue"))
    assert len(calls) == 3
    assert calls[1][0].startswith(_THEME_REPAIR_SYSTEM_MESSAGE)
    assert "情報そのもの" in calls[1][0] and calls[1][1]["reason"] == "angle"
    assert calls[2][1]["body"] == revised
    assert result.candidate.text.endswith(revised)


def test_theme_does_not_release_a_rewrite_that_still_asks_how_to_judge():
    result, calls = theme_run(
        "自分の価値観", "失敗した場合にやり直せる余地があることはありますか？",
        repair="失敗した場合にやり直せる余地があるかどうか、どのように判断しますか？",
        choose_theme=select_theme_angle("risk", "cue"),
    )
    assert result.disposition == "rejected" and result.candidate is None
    assert len(calls) == 2
    assert "やり直せる条件" in calls[1][1]["form"]


def test_theme_questions_about_trying_an_environment_keep_the_choice_unmade():
    open_question = "試すかどうかを決めるには、その環境のどんな条件を確かめますか？"
    result, calls = theme_run(
        "これからのこと", "試すかどうかを決める前に確かめたい具体的な条件はありますか？", repair=open_question,
        choose_theme=select_theme_angle("trial", "cue"),
    )
    writer, repair, reader = [payload for _, payload in calls]
    assert writer["scene"] == reader["scene"] == "新しい環境を少し試すか迷ったとき"
    assert writer["target"] == reader["target"] == "試すかどうかを決める前に知りたい環境の情報"
    assert "試すかどうかは未確定" in writer["premise"] == reader["premise"]
    assert calls[1][0] == _THEME_FORM_REPAIR_SYSTEM_MESSAGE
    assert repair == {field: writer[field] for field in ("form", "scene", "premise")}
    assert result.candidate.text == f"{writer['scene']}、{open_question}"


@pytest.mark.parametrize("draft", [
    "どれくらいの間隔なら相手も心地よく会えるか、決める前に何を確かめますか？",
    "今のやり方が合っているか考える前に、どんな手がかりがありますか？",
    "相手が心地よく会える間隔を判断するには、どんな手がかりを確かめますか？",
])
def test_theme_keeps_open_main_questions_about_facts(draft):
    result, calls = theme_run("人間関係", draft, choose_theme=select_theme_angle("distance", "cue"))
    assert len(calls) == 2 and result.candidate.text.endswith(draft)


def test_theme_allows_asking_for_a_start_time():
    draft = "話すと決めたら、いつから話し始めますか？"
    result, calls = theme_run("人間関係", draft)
    assert len(calls) == 2 and result.candidate.text.endswith(draft)


@pytest.mark.parametrize("body", [
    "最初に何をするか？",
    "どんなときに変えますか？",
    "何を基準に決めますか？",
    "Emlis、最初に何をしますか？",
    "仕事や勉強で新しいやり方を試すとき、何ですか？",
    "何か始めますか？",
])
def test_theme_rejects_non_polite_endings_and_unbound_questions(body):
    result, calls = theme_run("仕事・学び", body)
    assert result.disposition == "rejected" and len(calls) == 2


@pytest.mark.parametrize(("theme", "scene", "angle", "draft", "revised"), [
    ("人間関係", "cancel", "first_action",
     "約束の変更連絡を始める際、まず何をすべきでしょうか？",
     "約束を変えることを伝えるとき、まずどんな言葉をかけますか？"),
    ("人間関係", "group", "priority",
     "複数の案から一つを選ぶ基準は、何を基準に決めますか？",
     "複数の案から一つを選ぶ基準は何ですか？"),
    ("人間関係", "asking_help", "priority",
     "誰かに助けを求めるかどうかを決める際、どのような手がかりに決めますか？",
     "どんなことを手がかりに決めますか？"),
    ("人間関係", "thanks", "priority",
     "どの助けについて感謝の言葉を伝えるべきか、どのような基準で選ぶのが適切でしょうか？",
     "どの助けについてお礼を伝えるか、何を目安に選びますか？"),
    ("人間関係", "listening", "change",
     "相手の話を聞いていて、自分の考えを伝えるべきタイミングはどんなときですか？",
     "相手のどんな様子を見て、自分の考えも伝えようと思いますか？"),
    ("人間関係", "contact_channel", "priority",
     "二つの伝え方から選ぶ基準は何を手がかりにしますか？",
     "メッセージにするか直接話すか、どんなことを手がかりに決めますか？"),
    ("自分の価値観", "giving_credit", "priority",
     "誰のどんな働きを言葉にするかを選ぶ基準を、何を基準に決めますか？",
     "誰のどんな働きを言葉にするか、何を目安に決めますか？"),
    ("自分の価値観", "public_private", "priority",
     "何を基準に自分のルールを守るべきですか？",
     "自分のルールを守るべきか、何を基準に決めますか？"),
    ("自分の価値観", "spare_time", "outcome",
     "その時間の使い方でよかったと思える手がかりは、どんなことがあればありますか？",
     "あとでどんな気持ちになったら、その時間の使い方でよかったと思いますか？"),
    ("日々の過ごし方", "rest_day", "boundary",
     "休みの日に用事を入れる際、休んだと感じられる余裕を残すために、用事は何件まで入れるのが適切ですか？",
     "休める時間を残すには、用事を何件くらいまで入れますか？"),
    ("日々の過ごし方", "weather", "priority",
     "その外出の目的が、予定を当日に行うか後日に回すかをどう決める基準になりますか？",
     "予定どおり出かけるか後日に回すか、外出の目的のどんな点を重く見て決めますか？"),
])
def test_theme_repairs_advice_and_repeated_decision_criteria_before_reading(theme, scene, angle, draft, revised):
    result, calls = theme_run(theme, draft, repair=revised, choose_theme=select_theme_angle(scene, angle))

    prompts = (
        _THEME_WRITE_SYSTEM_MESSAGE, _THEME_FORM_REPAIR_SYSTEM_MESSAGE, _THEME_READ_SYSTEM_MESSAGE,
    )
    assert all(system.startswith(prompt) for (system, _), prompt in zip(calls, prompts, strict=True))
    assert calls[1][1] == {name: calls[0][1][name] for name in ("form", "scene", "premise") if name in calls[0][1]}
    assert result.candidate.text == f"{calls[0][1]['scene']}、{revised}"
    assert calls[2][1]["body"] == revised


def test_theme_allows_asking_where_to_start_without_treating_it_as_a_yes_no_question():
    result, calls = theme_run(
        "日々の過ごし方", "自由時間になった直後に何から始めますか？",
        choose_theme=select_theme_angle("short_day", "first_action"),
    )
    assert result.candidate.text == "自由に使える時間が少ない日、自由時間になった直後に何から始めますか？"
    assert calls[1][0] == _THEME_READ_SYSTEM_MESSAGE


def test_theme_reader_checks_the_corrected_particle_in_the_displayed_question():
    raw = "複数のことを取りかかるなら、いくつくらいまで無理なく始められますか？"
    result, calls = theme_run(
        "これからのこと", raw, choose_theme=select_theme_angle("several_goals", "boundary"),
    )
    _, reading = calls[1]
    assert reading["body"] == "複数のことに取りかかるなら、いくつくらいまで無理なく始められますか？"
    assert result.candidate.text == f"{reading['scene']}、{reading['body']}"


@pytest.mark.parametrize(("draft", "expected"), [
    ("無理なく贈り物に使える金額の上限は、いくらまでですか？", "無理なく贈り物に使える金額の上限はいくらですか？"),
    ("贈り物には、いくらまでなら無理なく使えますか？", "贈り物には、いくらまでなら無理なく使えますか？"),
])
def test_theme_reader_checks_the_amount_without_a_redundant_upper_limit(draft, expected):
    result, calls = theme_run(
        "自分の価値観", draft, choose_theme=select_theme_angle("useful_gift", "boundary"),
    )
    reading = calls[1][1]
    assert reading["body"] == expected
    assert result.candidate.text == f"{reading['scene']}、{expected}"


@pytest.mark.parametrize(("theme", "scene", "angle", "draft", "expected"), [
    ("人間関係", "asking_help", "priority",
     "誰かに助けを求めるかどうか、何を基準に決めますか？", "何を基準に決めますか？"),
    ("人間関係", "asking_help", "priority",
     "誰かに助けを求めるかどうかを決める際、どんなことを手がかりにしますか？",
     "どんなことを手がかりにしますか？"),
    ("人間関係", "disagreement", "priority",
     "意見が分かれたとき、お互いの意見をすり合わせるうえで何を大事にしますか？",
     "お互いの意見をすり合わせるうえで何を大事にしますか？"),
    ("人間関係", "feedback", "first_action",
     "改善してほしいことを伝えるとき、まず何を伝えますか？", "まず何を伝えますか？"),
    ("自分の価値観", "ownership", "priority",
     "勧めを断るか受けるか、何を基準に決めますか？", "何を基準に決めますか？"),
    ("自分の価値観", "giving_credit", "first_action",
     "感謝や評価を伝える際、まず何をしますか？", "まず何をしますか？"),
    ("仕事・学び", "finish", "change",
     "一区切りついた振り返りでは、次の作業の進め方を変えるのはどんなときですか？",
     "次の作業の進め方を変えるのはどんなときですか？"),
    ("仕事・学び", "scope", "first_action",
     "新しい依頼や情報が加わった直後、まず何に手をつけますか？", "まず何に手をつけますか？"),
    ("これからのこと", "route_change", "first_action",
     "目標の向かい方を変えようか迷ったとき、別の進め方を少し試すなら最初にどんなことをしますか？",
     "別の進め方を少し試すなら最初にどんなことをしますか？"),
    ("日々の過ごし方", "move", "first_action",
     "体を動かす時間を日常に組み込むために、まず何をしますか？", "まず何をしますか？"),
    ("日々の過ごし方", "changed_plans", "first_action",
     "その日の予定が急に変わった直後に、最初に何をしますか？", "最初に何をしますか？"),
    ("日々の過ごし方", "between_tasks", "priority",
     "用事の合間に少しだけ空き時間ができたとき、短い休憩にするか小さな用事を済ませるかの決め手は何ですか？",
     "短い休憩にするか小さな用事を済ませるかの決め手は何ですか？"),
    ("仕事・学び", "experiment", "priority",
     "慣れた手順を別の方法に切り替えるかどうか、何を基準に決めますか？", "何を基準に決めますか？"),
    ("これからのこと", "route_change", "priority",
     "目標の向かい方を変えようか迷ったとき、同じ目標に向かう別の進め方を選ぶ決め手は何ですか？",
     "同じ目標に向かう別の進め方を選ぶ決め手は何ですか？"),
    ("これからのこと", "change_habits", "change",
     "新しい暮らしの中で、習慣を変えるのはどんなときですか？",
     "新しい暮らしの中で、習慣を変えるのはどんなときですか？"),
])
def test_theme_removes_only_the_verified_opening_before_reading(theme, scene, angle, draft, expected):
    result, calls = theme_run(theme, draft, choose_theme=select_theme_angle(scene, angle))
    assert result.candidate.text == f"{calls[1][1]['scene']}、{expected}"
    assert calls[1][1]["body"] == expected
    assert calls[1][1]["answer_kind"] == angle


def test_theme_preserves_a_qualifier_that_makes_a_repeated_opening_a_different_condition():
    draft = "朝に体を動かす時間を日常に組み込むために、まず何をしますか？"
    result, calls = theme_run("日々の過ごし方", draft, choose_theme=select_theme_angle("move", "first_action"))
    assert result.candidate.text == f"{calls[1][1]['scene']}、{draft}"


def test_theme_preserves_the_question_after_a_punctuation_only_echo_of_the_scene():
    expected = "どちらの扱いにするかは、何を決め手にしますか？"
    draft = "全員を同じように扱うか、事情に合わせるか迷ったとき、" + expected
    result, calls = theme_run(
        "自分の価値観", draft, choose_theme=select_theme_angle("fairness", "priority"),
    )
    assert [system for system, _ in calls] == [_THEME_WRITE_SYSTEM_MESSAGE, _THEME_READ_SYSTEM_MESSAGE]
    assert calls[1][1]["body"] == expected
    assert result.candidate.text == f"{calls[1][1]['scene']}、{expected}"


def test_theme_preserves_a_new_scope_in_an_opening_about_asking_for_help():
    draft = "人にしかできない作業で誰かに助けを求めるかどうかを決める際、どんなことを手がかりにしますか？"
    result, calls = theme_run("人間関係", draft, choose_theme=select_theme_angle("asking_help", "priority"))
    assert result.candidate.text == f"{calls[1][1]['scene']}、{draft}"
    assert calls[1][1]["body"] == draft


def test_theme_checks_repeat_against_the_displayed_text_after_removing_an_opening():
    draft = "誰かに助けを求めるかどうか、何を基準に決めますか？"
    choose = select_theme_angle("asking_help", "priority")
    result, _ = theme_run("人間関係", draft, choose_theme=choose)
    prior = {"question_key": "old-slot", "text_key": result.candidate.text_key}
    repeated, calls = theme_run("人間関係", draft, questions=[prior], choose_theme=choose)
    assert repeated.disposition == "rejected" and len(calls) == 1


def test_theme_catalog_has_distinct_compatible_judgments_for_every_supported_scene():
    assert set(THEME_SCENE_ANGLE_TARGETS) == set(THEME_SCENES)
    for theme, scenes in THEME_SCENES.items():
        targets = THEME_SCENE_ANGLE_TARGETS[theme]
        assert set(targets) == set(scenes)
        assert sum(len(angles) for angles in targets.values()) >= 50
        for scene, angles in targets.items():
            assert len(angles) >= 4 and len(set(angles.values())) == len(angles)
            for angle in angles:
                position = (theme, scene, angle)
                bodies = THEME_VERIFIED_BODIES.get(position) or (THEME_TARGET_FORMS[position],)
                assert all(body.endswith("？") and body.count("？") == 1 and "〜" not in body for body in bodies)
    assert "change" in THEME_SCENE_ANGLE_TARGETS["人間関係"]["thanks"]
    assert "伝え" in THEME_SCENE_ANGLE_TARGETS["人間関係"]["thanks"]["change"][0]
    for theme, pairs in THEME_DISTINCT_POSITIONS.items():
        for first, second in pairs:
            assert first != second
            assert all(not {first, second} <= set(group) for group in THEME_EQUIVALENT_POSITIONS.get(theme, ()))
            for scene, angle in (first, second):
                assert angle in THEME_SCENE_ANGLE_TARGETS[theme][scene]
                assert THEME_VERIFIED_BODIES[(theme, scene, angle)]


@pytest.mark.parametrize("older_wording", [None, "初対面の人と話すとき、会話の話題はどう選びますか？"])
def test_theme_reader_receives_older_same_scene_angles_with_available_wording(older_wording):
    theme = "人間関係"
    recent = [{"question_key": f"recent-{index}", "question_text": f"{index}回目は何を選びますか？"}
              for index in range(30)]
    archived = [{"question_key": _theme_position_key(theme, scene_id, "first_action")}
                for scene_id in THEME_SCENES[theme]]
    if older_wording is not None:
        archived[0]["question_text"] = older_wording
    result, calls = theme_run(
        theme, "会話の話題は何を基準に選びますか？", questions=recent + archived,
        comparison={"verdict": "repeat", "id": 31},
    )
    assert result.disposition == "rejected"
    assert len(calls) == (4 if older_wording else 3)
    assert "history" not in calls[1][1]
    history = calls[2][1]["history"]
    assert [item["question"] for item in history[:30]] == [row["question_text"] for row in recent]
    expected = {"id": 31, "scene": "初対面の人と話すとき",
                "target": "最初のひと言", "angle": "話し始めるために最初にすること"}
    if older_wording is not None:
        expected = {"id": 31, "question": older_wording}
        assert calls[-1][1]["previous"] == older_wording
    assert history[30] == expected


def test_theme_refuses_a_matching_older_answer_target_before_the_model_reads_it():
    async def unexpected_read(*args):
        pytest.fail("A known repeated angle should be declined before model review")

    candidate, reason = asyncio.run(_review_theme_candidate(
        '{"question":"取りかかる順番は何を基準に決めますか？"}',
        plan=None, direction={"angle": "始めたいことに取りかかる順番を決める基準"},
        scene="始めてみたいことがいくつかあるとき", key="new-slot", material={"questions": []},
        previous_angles=["始めたいことに取りかかる順番を決める基準"], angle_id="priority",
        generate=unexpected_read,
    ))
    assert candidate is None and reason == "repeat"


def test_theme_reviews_a_repaired_question_without_changing_its_issued_key():
    repaired = "夜の予定を切り上げるのは、どんなときですか？"
    direct, _ = theme_run("日々の過ごし方", repaired)
    result, calls = theme_run("日々の過ごし方", "どんなときに変えますか？", repair=repaired)
    assert result.candidate == direct.candidate
    assert [system for system, _ in calls] == [
        _THEME_WRITE_SYSTEM_MESSAGE, _THEME_FORM_REPAIR_SYSTEM_MESSAGE, _THEME_READ_SYSTEM_MESSAGE,
    ]
    assert set(calls[1][1]) == {"form", "scene"}
    assert calls[2][1]["body"] == repaired


def test_theme_allows_an_interrogative_condition_opening():
    result, _ = theme_run("日々の過ごし方", "どんなとき、予定を減らして早く休みますか？")
    assert result.disposition == "selected"


@pytest.mark.parametrize("mark", ["", "。"])
def test_theme_restores_only_the_question_mark_on_a_complete_polite_question(mark):
    result, _ = theme_run("人間関係", "最初にどんな話題を出しますか" + mark)
    assert result.candidate.text == "初対面の人と話すとき、最初にどんな話題を出しますか？"


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
