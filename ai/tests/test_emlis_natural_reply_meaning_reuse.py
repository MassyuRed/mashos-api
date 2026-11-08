"""Actual finite source/recipient readers; no mocked semantic verdicts."""
from dataclasses import FrozenInstanceError
import json

import pytest

from cocolon_meaning_experience_engine.natural_reply_meaning import (
    compare_reply_meaning, prepare_meaning_support,
)


def material(memo, memo_action="", **extra):
    return dict(current=dict(memo=memo, memo_action=memo_action), current_input_id="current-input",
                current_answers=[], past_user_records=[], user_frame_feedback=[], **extra)


def compare(source, reply):
    payload = material(source) if isinstance(source, str) else source
    return compare_reply_meaning(json.dumps(payload, ensure_ascii=False), reply, "admitted-prefix")


@pytest.mark.parametrize("source,reply", [
    ("私は友人に頼まれた。", "あなたは友人に頼まれたのですね。"),
    ("私は友人に頼んだ。", "友人はあなたに頼まれたのですね。"),
    ("私は友人に相談された。", "友人はあなたに相談したのですね。"),
    ("私は同僚に注意された。", "あなたは同僚に注意されたんですね。"),
    ("私は同僚に怒られた。", "あなたは同僚に怒られたんですね。"),
    ("私は友人に頼られた。", "あなたは友人に頼られたのですね。"),
    ("私は先生から教わった。", "あなたは先生から教わったのですね。"),
    ("私は友人に本を貸した。", "友人はあなたから本を借りましたね。"),
    ("私は資料を書かなかった。", "あなたは資料を書かなかったのですね。"),
    ("私は記録を残した。", "あなたは記録を残しましたね。"),
    ("昨日、私は資料を調べた。", "あなたは資料を調べたのですね。"),
])
def test_case_voice_and_old_finite_inflections_agree_without_fixed_reply(source, reply):
    report = compare(source, reply)
    assert report.verdict == "NO_CONFLICT_IN_CHECKED_SCOPE", report
    assert report.checked_reply_count == 1
    assert not report.full_reply_semantic_coverage


@pytest.mark.parametrize("source,reply,reason", [
    ("私は友人に頼まれた。", "あなたは友人に頼んだのですね。", "WRITTEN_PARTICIPANT_ROLES_REVERSED"),
    ("同僚に注意された。", "あなたは同僚に注意しましたね。", "WRITTEN_PARTICIPANT_ROLES_REVERSED"),
    ("同僚に怒られた。", "あなたは同僚に怒ったのですね。", "WRITTEN_PARTICIPANT_ROLES_REVERSED"),
    ("私は友人に相談した。", "あなたは友人に相談されたのですね。", "WRITTEN_PARTICIPANT_ROLES_REVERSED"),
    ("私は友人から本を借りた。", "友人はあなたから本を借りたのですね。", "WRITTEN_PARTICIPANT_ROLES_REVERSED"),
    ("私は資料を書かなかった。", "あなたは資料を書いたのですね。", "POLARITY_CHANGED"),
    ("昨日、私は資料を書かなかった。", "昨日、あなたは資料を書いたのですね。", "POLARITY_CHANGED"),
])
def test_complete_matching_event_has_scoped_counter_witness(source, reply, reason):
    report = compare(source, reply)
    assert report.verdict == "CONFLICT", report
    assert reason in report.checks[0].reason_codes


@pytest.mark.parametrize("source,reply", [
    ("私は友人に頼まれた。", "気持ちが揺れているのですね。"),
    ("友人は資料を書いた。", "あなたは資料を書いたのですね。"),
    ("私は友人に頼まれたと思う。", "あなたは友人に頼んだのですね。"),
    ("私は友人に頼まれたのだろうか？", "あなたは友人に頼んだのですね。"),
    ("私は友人に頼まれた？", "あなたは友人に頼んだのですね。"),
    ("「私は友人に頼まれた」と同僚が話した。", "あなたは友人に頼んだのですね。"),
    ("私は友人に頼まれた。", "「あなたは友人に頼んだ」とは言えません。"),
    ("私は新人に教えられた。", "あなたは新人に教えたのですね。"),
    ("私は友人に頼まれた。", "友人に頼んだのですね。"),
    ("私は資料を書いた。私は資料を書かなかった。", "あなたは資料を書いたのですね。"),
    ("私は資料を書いた。", "Emlisは資料を書いたのですね。"),
    ("私は資料を書いた。", "あなたは資料を書いたかもしれません。"),
    ("友人は自分に頼んだ。", "友人はあなたに頼んだのですね。"),
    ("自分は友人に頼んだ。", "あなたは友人に頼んだのですね。"),
    ("私は友人に頼んだ。", "友人は自分に頼まれたのですね。"),
    ("友人は自分自身に頼んだ。", "友人はあなたに頼んだのですね。"),
    ("私は友人に頼んだ。", "友人はご自身に頼まれたのですね。"),
    ("私は午後に相談された。", "あなたは午後に相談したのですね。"),
    ("私は三日前に頼まれた。", "あなたは三日前に頼んだのですね。"),
    ("私は会に誘われた。", "あなたは会に誘ったのですね。"),
    ("友人曰く私は友人に頼まれた。", "あなたは友人に頼んだのですね。"),
    ("私は資料を書きたい。", "あなたは資料を書いたのですね。"),
    ("私は資料を書きたかった。", "あなたは資料を書いたのですね。"),
    ("私は資料を書かなかった。", "あなたは資料を書きたいのですね。"),
    ("昨日、私は友人に頼まれた。", "今日、あなたは友人に頼んだのですね。"),
    ("私は友人に頼まれた。", "明日、あなたは友人に頼んだのですね。"),
    ("当時、私は友人に頼まれた。", "今回、あなたは友人に頼んだのですね。"),
    ("私は友人に頼まれた。", "以前、あなたは友人に頼んだのですね。"),
    ("私は友人に頼まれた。", "あなたは友人に頼んだ。"),
])
def test_unsupported_scope_quote_omitted_actor_or_nonunique_event_is_unassessed(source, reply):
    report = compare(source, reply)
    assert report.verdict == "UNASSESSED", report
    assert report.checked_reply_count == 0


def test_normal_omission_is_not_opposite_and_partial_coverage_stays_explicit():
    report = compare("私は資料を書いた。不安も期待もある。",
                     "あなたは資料を書いたのですね。いろいろな気持ちがあるのですね。")
    assert report.verdict == "NO_CONFLICT_IN_CHECKED_SCOPE"
    assert report.reply_segment_count == 2 and report.checked_reply_count == 1
    assert report.unassessed_reply_count == 1 and not report.full_reply_semantic_coverage


def test_support_preserves_original_scalar_utf8_bounds_and_no_omitted_writer_invention():
    text = "  同僚に注意された。\n私は資料を書いた。"
    support = prepare_meaning_support(material(text))
    assert len(support["witnesses"]) == 2
    first = support["witnesses"][0]
    assert first["subject"] == "UNSTATED" and first["agent"] == "WRITTEN:同僚"
    for witness in support["witnesses"]:
        assert text[witness["scalar_start"]:witness["scalar_end"]] == witness["raw_text"]
        assert text.encode()[witness["utf8_start"]:witness["utf8_end"]].decode() == witness["raw_text"]
    assert any("_FINITE_PREDICATES" in path for path in support["reused_assets"])


def test_admitted_past_is_separate_and_duplicate_sources_are_not_arbitrarily_selected():
    value = material("私は記録を残した。")
    value["past_user_records"] = [dict(input_id="past-input", original=dict(memo="私は友人に頼まれた。"), answers=[])]
    report = compare(value, "あなたは友人に頼まれたのですね。")
    assert report.verdict == "NO_CONFLICT_IN_CHECKED_SCOPE"
    assert report.checks[0].source_path == "past_user_records[0].original.memo"
    value["current"]["memo"] = "私は友人に頼まれた。"
    assert compare(value, "あなたは友人に頼まれたのですね。").verdict == "UNASSESSED"


@pytest.mark.parametrize("change", ["answer", "revised", "rejected"])
def test_unresolved_update_cannot_reactivate_an_old_source_witness(change):
    value = material("私は友人に頼まれた。")
    if change == "answer":
        value["current_answers"] = [dict(text="その部分は取り消します。")]
    else:
        value["user_frame_feedback"] = [dict(input_id="current-input", status=change.upper(), correction_text="別の意味です。")]
    report = compare(value, "あなたは友人に頼んだのですね。")
    assert report.verdict == "UNASSESSED" and report.excluded_source_count == 1
    assert not prepare_meaning_support(value)["witnesses"]


def test_model_supplied_protected_meaning_and_question_text_are_never_evidence():
    value = material("まだ考えている。")
    value["protected_meaning"] = dict(witnesses=[dict(raw_text="私は友人に頼まれた。")])
    value["ai_question_context"] = "私は友人に頼まれた。"
    assert compare(value, "あなたは友人に頼んだのですね。").verdict == "UNASSESSED"


@pytest.mark.parametrize("tail", ["その話は嘘だった。", "その部分は取り消します。", "そう思っただけだった。"])
def test_later_unresolved_withdrawal_cannot_be_discarded_by_partial_source_reader(tail):
    report = compare("私は友人に頼まれた。" + tail, "あなたは友人に頼んだのですね。")
    assert report.verdict == "UNASSESSED" and report.excluded_source_count == 1


@pytest.mark.parametrize("tail", ["かもしれない。", "のではない。", "と友人が話した。", "のだろうか？"])
def test_newline_does_not_turn_source_hedge_or_report_into_asserted_fact(tail):
    value = material("私は資料を書いた\n" + tail)
    assert not prepare_meaning_support(value)["witnesses"]
    report = compare(value, "あなたは資料を書かなかったのですね。")
    assert report.verdict == "UNASSESSED" and report.source_witness_count == 0


@pytest.mark.parametrize("tail", ["かもしれない。", "のではない。", "と友人が話した。", "のだろうか？"])
def test_newline_does_not_discard_reply_hedge_report_or_question(tail):
    report = compare("私は資料を書かなかった。", "あなたは資料を書いた\n" + tail)
    assert report.verdict == "UNASSESSED" and report.parsed_reply_count == 0


def test_real_sentence_terminators_allow_independent_lines_and_preserve_raw_bounds():
    value = material("私は資料を書いた。\n私は記録を残した。")
    support = prepare_meaning_support(value)
    assert len(support["witnesses"]) == 2
    report = compare(value, "あなたは資料を書いたのですね。\nあなたは記録を残したのですね。")
    assert report.checked_reply_count == 2 and report.verdict == "NO_CONFLICT_IN_CHECKED_SCOPE"


def test_past_relative_day_does_not_share_the_current_record_calendar_anchor():
    value = material("私は記録を残した。")
    value["past_user_records"] = [dict(input_id="past", original=dict(memo="昨日、私は友人に頼まれた。"), answers=[])]
    assert compare(value, "昨日、あなたは友人に頼んだのですね。").verdict == "UNASSESSED"


def test_unread_same_record_context_may_qualify_the_matching_event():
    value = material("私は友人に頼まれた。", "翌々日には私が逆の立場になった。")
    support = prepare_meaning_support(value)
    assert support["witnesses"] and not support["witnesses"][0]["source_context_complete"]
    assert compare(value, "あなたは友人に頼んだのですね。").verdict == "UNASSESSED"


def test_two_different_written_days_do_not_hide_a_second_event_as_a_literal_actor():
    value = material("昨日、私は友人に頼まれた。翌日、私は友人に頼んだ。")
    assert compare(value, "あなたは友人に頼んだのですね。").verdict == "UNASSESSED"


def test_unknown_passive_subject_is_not_assessed_as_a_known_counterpart():
    report = compare("同僚に怒られた。", "あなたは同僚に怒られたのですね。")
    assert report.verdict == "NO_CONFLICT_IN_CHECKED_SCOPE"
    assert "written_agent" in report.checks[0].assessed_axes
    assert "written_counterpart" not in report.checks[0].assessed_axes


def test_private_report_is_immutable_stable_hash_bound_and_does_not_copy_personal_text():
    value = material("私は友人に頼まれた。")
    report = compare(value, "あなたは友人に頼まれたのですね。")
    assert report == compare(value, "あなたは友人に頼まれたのですね。")
    with pytest.raises(FrozenInstanceError):
        report.verdict = "CONFLICT"
    raw = json.dumps(report.as_private_dict(), ensure_ascii=False)
    assert "友人" not in raw and "頼まれ" not in raw
    assert report.source_prefix_ref == "admitted-prefix"
    assert compare(value, "あなたは友人に頼んだのですね。").reply_sha256 != report.reply_sha256
    changed = material("私は友人に頼んだ。")
    assert compare(changed, "あなたは友人に頼まれたのですね。").material_sha256 != report.material_sha256


@pytest.mark.parametrize("bad", ["{", "[]", '{"current":3}', '{"current":{"memo":3}}'])
def test_invalid_material_propagates_instead_of_becoming_semantically_unassessed(bad):
    with pytest.raises(ValueError):
        compare_reply_meaning(bad, "受け取りました。", "prefix")


@pytest.mark.parametrize("source,subject,agent,counterpart,arguments", [
    ("姉が呼び止めたのは先生だった。", "WRITTEN:姉", "WRITTEN:姉", "", (("を", "先生"),)),
    ("先生に呼び止められたのは姉だった。", "WRITTEN:姉", "WRITTEN:先生", "WRITTEN:姉", ()),
    ("先生から呼び止められたのは姉だった。", "WRITTEN:姉", "WRITTEN:先生", "WRITTEN:姉", ()),
    ("母が呼び止めなかったのは妹だった。", "WRITTEN:母", "WRITTEN:母", "", (("を", "妹"),)),
    ("母に呼び止められなかったのは妹だった。", "WRITTEN:妹", "WRITTEN:母", "WRITTEN:妹", ()),
    ("先生から褒められたのは姉だった。", "WRITTEN:姉", "WRITTEN:先生", "WRITTEN:姉", ()),
    ("先生から教えられたのは姉だった。", "WRITTEN:姉", "WRITTEN:先生", "WRITTEN:姉", ()),
])
def test_complete_participant_focus_retains_written_voice_roles_and_case(source, subject, agent, counterpart, arguments):
    witnesses = prepare_meaning_support(material(source))["witnesses"]
    assert len(witnesses) == 1
    row = witnesses[0]
    assert (row["subject"], row["agent"], row["counterpart"], row["arguments"]) == (
        subject, agent, counterpart, arguments)
    assert row["source_construction"] == "EXPLICIT_FOCUS"
    assert row["source_context_complete"]
    assert row["predicate"] in {"呼び止める", "褒める", "教える"}


def test_focus_uses_original_ranges_and_does_not_rewrite_source_or_complete_other_field():
    text = "  昨日、姉が呼び止めたのは先生だった。"
    value = material(text, "私は少し離れて待っていた。")
    row, = prepare_meaning_support(value)["witnesses"]
    assert row["raw_text"] == "昨日、姉が呼び止めたのは先生だった"
    assert text[row["scalar_start"]:row["scalar_end"]] == row["raw_text"]
    assert text.encode()[row["utf8_start"]:row["utf8_end"]].decode() == row["raw_text"]
    assert row["relative_day"] == "昨日" and not row["source_context_complete"]
    assert value["current"]["memo"] == text


@pytest.mark.parametrize("source,reply", [
    ("姉が呼び止めたのは先生だった。", "姉が先生を呼び止めたのですね。"),
    ("先生に呼び止められたのは姉だった。", "先生が姉を呼び止めたのですね。"),
    ("姉が先生を呼び止めた。", "先生は姉に呼び止められたのですね。"),
    ("先生から褒められたのは姉だった。", "先生は姉を褒めたのですね。"),
    ("母は妹を呼び止めた。", "妹は母に呼び止められたのですね。"),
    ("姉が呼び止めたのは先生だった。", "姉が呼び止めたのは先生だったのですね。"),
])
def test_focused_or_ordinary_direct_patient_survives_valid_voice_paraphrase(source, reply):
    report = compare(source, reply)
    assert report.verdict == "NO_CONFLICT_IN_CHECKED_SCOPE", report
    assert report.checked_reply_count == 1
    assert "written_agent" in report.checks[0].assessed_axes
    assert "written_counterpart" in report.checks[0].assessed_axes
    assert not report.full_reply_semantic_coverage


@pytest.mark.parametrize("source,reply,reason", [
    ("姉が呼び止めたのは先生だった。", "先生が姉を呼び止めたのですね。", "WRITTEN_PARTICIPANT_ROLES_REVERSED"),
    ("先生に呼び止められたのは姉だった。", "姉が先生を呼び止めたのですね。", "WRITTEN_PARTICIPANT_ROLES_REVERSED"),
    ("母は妹を呼び止めた。", "母は妹に呼び止められたのですね。", "WRITTEN_PARTICIPANT_ROLES_REVERSED"),
    ("姉が呼び止めなかったのは先生だった。", "姉が先生を呼び止めたのですね。", "POLARITY_CHANGED"),
])
def test_fully_written_unique_direct_patient_mutation_is_detected(source, reply, reason):
    report = compare(source, reply)
    assert report.verdict == "CONFLICT", report
    assert reason in report.checks[0].reason_codes


@pytest.mark.parametrize("source", [
    "呼び止めたのは姉だった。",
    "姉が先生を呼び止めたのは母だった。",
    "妹が先生に呼び止められたのは姉だった。",
    "姉が呼び止めたのは駅だった。",
    "姉が呼び止めたのは昨日だった。",
    "先生に呼び止められたのは朝だった。",
    "先生に呼び止められたのは理由だった。",
    "姉が呼び止めたのは太郎だった。",
    "姉が書いたのは手紙だった。",
    "姉が相談したのは先生だった。",
    "先生に教えられたのは姉だった。",
    "姉が呼び止めたのは先生ではなかった。",
    "姉が呼び止めたのは先生だったと思う。",
    "姉が呼び止めたのは先生だったかもしれない。",
    "もし姉が呼び止めたのは先生だった。",
    "「姉が呼び止めたのは先生だった」と友人が話した。",
])
def test_focus_does_not_invent_missing_case_person_or_asserted_scope(source):
    assert not prepare_meaning_support(material(source))["witnesses"]


def test_focused_role_comparison_keeps_missing_target_unread_context_and_withdrawal_open():
    source = "姉が呼び止めたのは先生だった。"
    assert compare(source, "先生が呼び止めたのですね。").verdict == "UNASSESSED"
    assert compare(material(source, "別の日には逆の立場だった。"),
                   "先生が姉を呼び止めたのですね。").verdict == "UNASSESSED"
    assert not prepare_meaning_support(material(source + "その話は嘘だった。"))["witnesses"]


def test_plain_written_objects_are_not_made_focus_people_or_counterparts():
    row, = prepare_meaning_support(material("私は資料を書いた。"))["witnesses"]
    assert row["arguments"] == (("を", "資料"),) and row["counterpart"] == ""
    assert row["source_construction"] == "PLAIN_FINITE"
