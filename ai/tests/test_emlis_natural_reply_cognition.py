"""Source meanings/scopes and exclusions, not a mirror of a regex pattern."""
import pytest

from cocolon_meaning_experience_engine.natural_reply_cognition import read_cognition_clause


def read(text, *, prefix="", suffix="。", group="CURRENT"):
    source = prefix + text + suffix
    return read_cognition_clause(source, len(prefix), len(prefix) + len(text),
        source_path="current.memo_action", source_group=group)


def assert_exact_parts(result, source):
    for key in ("raw", "cognitive_host", "knowledge_time", "content", "content_time",
                "prior_event", "prior_event_time", "after_link"):
        part = result[key]
        if part is None:
            continue
        assert source[part["scalar_start"]:part["scalar_end"]] == part["raw_text"]
        assert source.encode()[part["utf8_start"]:part["utf8_end"]].decode() == part["raw_text"]


def test_prior_notice_retains_separate_knowledge_and_future_content():
    text = "昨日の朝、今日の午後に断水すると知った"
    result = read(text)
    assert result["knowledge_time"]["raw_text"] == "昨日の朝"
    assert result["content"]["raw_text"] == "今日の午後に断水する"
    assert result["content_time"]["raw_text"] == "今日の午後"
    assert result["cognitive_host"]["raw_text"] == "知った"
    assert result["knowledge_holder"] == "UNSTATED"
    assert result["explicit_day_order"] == "KNOWLEDGE_BEFORE_CONTENT_DAY"
    assert result["content_status"] == "AS_WRITTEN_NOT_ASSERTED_AS_COMPLETED"
    assert result["full_semantic_coverage"] is False
    assert result["prior_event"] is None
    assert_exact_parts(result, text + "。")


def test_unavailable_copier_is_not_relabelled_as_intention_or_performance():
    text = "昨日の昼、今日の午前はコピー機が点検で使えないと知った"
    result = read(text)
    assert result["content"]["raw_text"] == "今日の午前はコピー機が点検で使えない"
    assert "modality" not in result and "actor" not in result
    assert result["knowledge_time"]["raw_text"] == "昨日の昼"
    assert result["explicit_day_order"] == "KNOWLEDGE_BEFORE_CONTENT_DAY"
    assert_exact_parts(result, text + "。")


def test_after_event_does_not_invent_exact_time_for_knowledge():
    text = "今日の午後に水道が止まってから、断水だと知った"
    result = read(text)
    assert result["kind"] == "KNOWLEDGE_AFTER_WRITTEN_EVENT"
    assert result["prior_event"]["raw_text"] == "今日の午後に水道が止まって"
    assert result["prior_event_time"]["raw_text"] == "今日の午後"
    assert result["after_link"]["raw_text"] == "から"
    assert result["content"]["raw_text"] == "断水だ"
    assert result["knowledge_time"] is None
    assert result["content_time"] is None
    assert result["explicit_day_order"] is None
    assert result["knowledge_holder"] == "UNSTATED"
    assert_exact_parts(result, text + "。")


def test_same_written_day_does_not_infer_order_from_morning_and_afternoon():
    result = read("今日の朝、今日の午後に休館すると知った")
    assert result["explicit_day_order"] == "SAME_WRITTEN_DAY"


def test_future_relative_day_is_not_promoted_to_an_intention():
    result = read("今日の朝、明日の午後に停電すると知った")
    assert result["explicit_day_order"] == "KNOWLEDGE_BEFORE_CONTENT_DAY"
    assert result["content"]["raw_text"].endswith("停電する")
    assert "intended_future" not in str(result)


@pytest.mark.parametrize("text,content", [
    ("昨日の朝、今日の午後に病院の窓口が休業すると知った", "今日の午後に病院の窓口が休業する"),
    ("昨日の昼、今日の午前に商店街で停電すると知った", "今日の午前に商店街で停電する"),
])
def test_written_subject_or_location_in_a_notice_does_not_change_knowledge_scope(text, content):
    result = read(text)
    assert result["content"]["raw_text"] == content
    assert result["explicit_day_order"] == "KNOWLEDGE_BEFORE_CONTENT_DAY"
    assert result["knowledge_holder"] == "UNSTATED"
    assert_exact_parts(result, text + "。")


def test_nominal_prior_change_and_written_purpose_are_not_inferred():
    text = "今日の午後に照明が消灯してから、検査のための消灯だと知った"
    result = read(text)
    assert result["prior_event"]["raw_text"] == "今日の午後に照明が消灯して"
    assert result["content"]["raw_text"] == "検査のための消灯だ"
    assert result["knowledge_time"] is None


def test_negative_notice_keeps_its_own_content_negation():
    result = read("昨日の朝、今日の午後に停電しないと知った")
    assert result["content"]["raw_text"] == "今日の午後に停電しない"
    assert result["prior_event"] is None
    assert result["content_status"] == "AS_WRITTEN_NOT_ASSERTED_AS_COMPLETED"


def test_after_change_keeps_written_past_nominal_content():
    text = "今日の午後に受付が閉まってから、休業だったと知った"
    result = read(text)
    assert result["prior_event"]["raw_text"] == "今日の午後に受付が閉まって"
    assert result["content"]["raw_text"] == "休業だった"
    assert result["knowledge_time"] is None
    assert_exact_parts(result, text + "。")


def test_past_group_preserves_the_written_relative_day_without_reanchoring():
    result = read("昨日の朝、今日の午後に断水すると知った", group="PAST")
    assert result["source_group"] == "PAST"
    assert result["knowledge_time"]["raw_text"] == "昨日の朝"
    assert result["content_time"]["raw_text"] == "今日の午後"
    assert "date" not in result


def test_non_bmp_prefix_uses_scalar_and_utf8_coordinates_without_normalizing():
    text = "昨日の朝、今日の午後に断水すると知った"
    prefix = "🌷に水をやった。"
    result = read(text, prefix=prefix)
    assert result["raw"]["scalar_start"] == len(prefix)
    assert result["raw"]["utf8_start"] == len(prefix.encode())
    assert_exact_parts(result, prefix + text + "。")


@pytest.mark.parametrize("text", [
    "昨日の朝、今日の午後に断水するかもしれないと知った",
    "昨日の朝、今日の午後に断水すると知ったはず",
    "昨日の朝、今日の午後に断水すると知らなかった",
    "昨日の朝、今日の午後に断水するかは分からない",
    "昨日の朝、今日の午後に断水すると知りたい",
    "昨日の朝、今日の午後に断水すると思った",
    "昨日の朝、今日の午後に断水すると母から聞いた",
    "昨日の朝、今日の午後に断水すると知ったと母が言った",
    "もし昨日の朝、今日の午後に断水すると知ったなら",
    "『昨日の朝、今日の午後に断水すると知った』",
    "昨日の朝、今日の午後に断水すると知った？",
    "今日の午後に水道が止まってから、断水だと知ったと思う",
    "今日の午後に水道が止まるなら、断水だと知った",
    "今日の午後に水道が止まってから、断水だと知りたい",
    "今日の午後に水道が止まってから、断水だと知ったかもしれない",
    "今日の午後に水道が止まってから、断水だとは知らなかった",
    "昨日の朝、今日の午後に断水すると知っていた",
    "昨日の朝、今日の午後に断水するかが不明だと知った",
    "昨日の朝、今日の午後に断水すると知る人がいると知った",
    "昨日の朝、今日の午後に断水することを願う人がいると知った",
    "昨日の朝、今日の午後に断水したくないと知った",
    "昨日の朝、今日の午後に断水してほしくないと知った",
    "今日の午後に水道が止まらなくてから、断水だと知った",
    "今日の午後に水道が止まる予定でから、断水だと知った",
    "今日の午後に水道が止まってから、不明だと知った",
    "断水だと知った",
])
def test_unqualified_or_unsupported_cognition_stays_unassessed(text):
    assert read(text) is None


@pytest.mark.parametrize("prefix", [
    "これは架空の話だ。",
    "例として記す。",
    "次の話は撤回した。",
    "妹によると。",
    "これは母の説明だ。",
])
def test_field_context_cannot_be_dropped_to_assert_a_matching_inner_span(prefix):
    assert read("昨日の朝、今日の午後に断水すると知った", prefix=prefix) is None


def test_matching_substring_of_connected_clause_is_not_independent():
    text = "昨日の朝、今日の午後に断水すると知った"
    assert read(text, prefix="母は") is None
    assert read(text, suffix="けれど、違った。") is None


@pytest.mark.parametrize("args", [
    ("昨日の朝、今日の午後に断水すると知った", -1, 2),
    ("昨日の朝、今日の午後に断水すると知った", True, 2),
    ("昨日の朝、今日の午後に断水すると知った", 0, 999),
])
def test_invalid_source_coordinates_are_not_silently_repaired(args):
    with pytest.raises(ValueError, match="natural_cognition_source_invalid"):
        read_cognition_clause(*args, source_path="current.memo")
