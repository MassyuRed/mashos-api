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
