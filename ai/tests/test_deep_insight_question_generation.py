import asyncio
import hashlib
import json
import random

import pytest

from cocolon_meaning_experience_engine import deep_insight_question
from cocolon_meaning_experience_engine.deep_insight_question import (
    ANSWER_READ_SYSTEM_MESSAGE, PLAN_SYSTEM_MESSAGE, READ_SYSTEM_MESSAGE,
    RECORD_REASON_READ_SYSTEM_MESSAGE, WRITE_SYSTEM_MESSAGE,
    _THEME_COMPARE_PAIR_SYSTEM_MESSAGE, _THEME_COMPARE_SYSTEM_MESSAGE,
    _THEME_PLAN_SYSTEM_MESSAGE, _THEME_READ_SYSTEM_MESSAGE,
    _THEME_REPAIR_SYSTEM_MESSAGE, _THEME_WRITE_SYSTEM_MESSAGE,
    _bind_anchor, _display_citation_matches, _review_theme_candidate, _theme_has_new_answer, _theme_position_key,
    generate_question, prepare_question_material,
)

from cocolon_meaning_experience_engine.deep_insight_theme import THEME_SCENES
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


def run(original, plan, question=BODY, *, reading=None):
    prepared, sources = prepare_question_material(original, lane="records", theme=None)
    calls = []

    async def generate(system, payload):
        calls.append((system, payload))
        if system.startswith(PLAN_SYSTEM_MESSAGE):
            response = plan
        elif system == WRITE_SYSTEM_MESSAGE:
            response = {"question": question}
        else:
            assert system.startswith((READ_SYSTEM_MESSAGE, ANSWER_READ_SYSTEM_MESSAGE, RECORD_REASON_READ_SYSTEM_MESSAGE))
            response = reading if reading is not None else read(
                plan, record_reason=system.startswith(RECORD_REASON_READ_SYSTEM_MESSAGE))
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


def select_theme_angle(scene, angle):
    return lambda values: next(value for value in values if value[0] in (scene, angle))


def theme_run(theme, question, *, questions=(), reading=None, comparison=None, extra=None,
              scene=None, target=None, repair=None, raw_write=False, choose_theme=lambda values: values[0]):
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
        if system.startswith(_THEME_REPAIR_SYSTEM_MESSAGE):
            return json.dumps({"question": repair or question}, ensure_ascii=False)
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
        "question": result.candidate.text,
    }
    assert comparer == {**reader, "history": [{"id": 1, "question": previous}]}
    assert calls[1][0] == _THEME_READ_SYSTEM_MESSAGE
    assert calls[2][0] == _THEME_COMPARE_SYSTEM_MESSAGE


@pytest.mark.parametrize("reason", ["surface", "angle", "premise"])
def test_theme_reader_must_accept_scene_and_angle(reason):
    reading = {"verdict": "reject", "reason": reason}
    result, calls = theme_run("人間関係", "最初にどんな話題を出しますか？",
                              reading=reading)
    assert result.disposition == "rejected"
    assert len(calls) == 4
    assert calls[2][1]["reason"] == reason


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
    assert calls[-1][1]["history"][0]["target"] == "取りかかる順番"


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


def test_theme_checks_cited_wording_then_rechecks_the_rest_of_the_history():
    question = {"question": "守りたい約束と目の前の都合がぶつかったとき、どこまで負担を引き受けますか？"}
    earlier = {"id": 1, "question": "人に勧められたことを試すとき、どこまで負担を引き受けますか？"}
    other = {"id": 2, "question": "自分のルールを見直そうと決めるのはどんなときですか？"}
    responses = iter([{"verdict": "repeat", "id": 1}, {"verdict": "distinct"}, {"verdict": "distinct"}])
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


def test_theme_will_try_new_situations_after_all_catalog_positions():
    from cocolon_meaning_experience_engine.deep_insight_theme import THEME_ANGLES

    theme = "仕事・学び"
    issued = [{"question_key": _theme_position_key(theme, scene_id, angle_id)}
              for scene_id in THEME_SCENES[theme] for angle_id in THEME_ANGLES]
    result, calls = theme_run(theme, "最初に何を確認しますか？",
        questions=issued, scene="学んだ手順が通じない現場に出会ったとき", target="別の手順を選ぶかどうか")
    assert result.disposition == "selected"
    assert result.candidate.question_key not in {row["question_key"] for row in issued}
    assert [system for system, _ in calls] == [
        _THEME_PLAN_SYSTEM_MESSAGE, _THEME_WRITE_SYSTEM_MESSAGE, _THEME_READ_SYSTEM_MESSAGE,
        _THEME_COMPARE_SYSTEM_MESSAGE,
    ]


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


def test_theme_allows_asking_where_to_start_without_treating_it_as_a_yes_no_question():
    result, calls = theme_run(
        "日々の過ごし方", "自由時間になった直後に何から始めますか？",
        choose_theme=select_theme_angle("short_day", "first_action"),
    )
    assert result.candidate.text == "自由に使える時間が少ない日、自由時間になった直後に何から始めますか？"
    assert calls[1][0] == _THEME_READ_SYSTEM_MESSAGE


@pytest.mark.parametrize(("theme", "scene", "angle", "draft", "expected"), [
    ("人間関係", "asking_help", "priority",
     "誰かに助けを求めるかどうか、何を基準に決めますか？", "何を基準に決めますか？"),
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
    ("これからのこと", "change_habits", "change",
     "新しい暮らしの中で、習慣を変えるのはどんなときですか？",
     "新しい暮らしの中で、習慣を変えるのはどんなときですか？"),
])
def test_theme_removes_only_the_verified_opening_before_reading(theme, scene, angle, draft, expected):
    result, calls = theme_run(theme, draft, choose_theme=select_theme_angle(scene, angle))
    assert result.candidate.text == f"{calls[1][1]['scene']}、{expected}"
    assert calls[1][1]["question"] == result.candidate.text


def test_theme_preserves_a_qualifier_that_makes_a_repeated_opening_a_different_condition():
    draft = "朝に体を動かす時間を日常に組み込むために、まず何をしますか？"
    result, calls = theme_run("日々の過ごし方", draft, choose_theme=select_theme_angle("move", "first_action"))
    assert result.candidate.text == f"{calls[1][1]['scene']}、{draft}"


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
        for angles in targets.values():
            assert len(angles) >= 4 and len(set(angles.values())) == len(angles)
    assert "change" in THEME_SCENE_ANGLE_TARGETS["人間関係"]["thanks"]
    assert "伝え" in THEME_SCENE_ANGLE_TARGETS["人間関係"]["thanks"]["change"][0]


def test_theme_reader_receives_older_same_scene_angles_without_guessing_their_text():
    theme = "人間関係"
    recent = [{"question_key": f"recent-{index}", "question_text": f"{index}回目は何を選びますか？"}
              for index in range(30)]
    archived = [{"question_key": _theme_position_key(theme, scene_id, "first_action")}
                for scene_id in THEME_SCENES[theme]]
    result, calls = theme_run(
        theme, "会話の話題は何を基準に選びますか？", questions=recent + archived,
        comparison={"verdict": "repeat", "id": 31},
    )
    assert result.disposition == "rejected" and len(calls) == 3
    assert "history" not in calls[1][1]
    history = calls[2][1]["history"]
    assert [item["question"] for item in history[:30]] == [row["question_text"] for row in recent]
    assert history[30] == {"id": 31, "scene": "初対面の人と話すとき",
                           "target": "最初のひと言", "angle": "話し始めるために最初にすること"}


def test_theme_refuses_a_matching_older_answer_target_before_the_model_reads_it():
    async def unexpected_read(*args):
        pytest.fail("A known repeated angle should be declined before model review")

    candidate, reason = asyncio.run(_review_theme_candidate(
        '{"question":"取りかかる順番は何を基準に決めますか？"}',
        plan=None, direction={"angle": "始めたいことに取りかかる順番を決める基準"},
        scene="始めてみたいことがいくつかあるとき", key="new-slot", material={"questions": []},
        previous_angles=["始めたいことに取りかかる順番を決める基準"],
        generate=unexpected_read,
    ))
    assert candidate is None and reason == "repeat"


def test_theme_reviews_a_repaired_question_without_changing_its_issued_key():
    repaired = "夜の予定を切り上げるのは、どんなときですか？"
    direct, _ = theme_run("日々の過ごし方", repaired)
    result, calls = theme_run("日々の過ごし方", "どんなときに変えますか？", repair=repaired)
    assert result.candidate == direct.candidate
    assert [system for system, _ in calls] == [
        _THEME_WRITE_SYSTEM_MESSAGE, _THEME_REPAIR_SYSTEM_MESSAGE, _THEME_READ_SYSTEM_MESSAGE,
    ]
    assert calls[1][1]["reason"] == "surface"
    assert "draft" not in calls[1][1]
    assert calls[2][1]["question"] == result.candidate.text


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
