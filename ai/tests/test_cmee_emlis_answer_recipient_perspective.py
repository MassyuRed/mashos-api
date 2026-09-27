"""A user's later answer remains theirs when Emlis addresses them."""

from unittest.mock import patch

import pytest

from test_cmee_emlis_received_discourse import actual, inverse
from test_cmee_emlis_q3_thread import begin, advance
from test_emlis_q2_application import answer, run
from test_emlis_q3_application import cont, qcase, qdb
from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning


@pytest.mark.parametrize("memo", [
    "褒められたのに、嬉しくなかった。",
    "褒められたのに、嬉しくなかった。誘われたのに、悲しかった。",
])
@pytest.mark.parametrize("reply,recipient", [
    ("今は私には重い。", "あなたには重い"),
    ("今は僕には怖い。", "あなたには怖い"),
])
def test_later_answer_addresses_source_speaker_and_retains_event(memo, reply, recipient):
    context = actual(request=advance(begin(memo), reply))
    follow = context[0].artifact.reception
    assert "回答した時点では" + recipient in follow
    assert "回答した時点では私には" not in follow
    assert "回答した時点では僕には" not in follow
    assert "褒められた時は嬉しくなく" in follow
    assert inverse(context, follow, without_author=True).passed


@pytest.mark.parametrize("old,new", [
    ("あなたには", "私には"),
    ("あなたには", "友人には"),
    ("あなたには", "あなたも"),
    ("回答した時点では", "先の回答時点では"),
    ("重い", "軽い"),
    ("嬉しくなく", "嬉しく"),
])
def test_independent_inverse_rejects_changed_owner_time_and_meaning(old, new):
    context = actual(request=advance(begin(), "今は私には重い。"))
    follow = context[0].artifact.reception
    changed = follow.replace(old, new, 1)
    assert changed != follow
    assert not inverse(context, changed, without_author=True).passed


def test_correction_keeps_prior_answer_time_and_withdrawal_removes_only_answer():
    request = advance(begin(), "今は私には重い。")
    corrected = actual(request=advance(request, "「私には重い」ではなく「私には苦しい」です。"))
    follow = corrected[0].artifact.reception
    assert "先の回答時点ではあなたには苦しい" in follow
    assert "重い" not in follow and "褒められた" in follow
    assert inverse(corrected, follow, without_author=True).passed
    assert not inverse(corrected, follow.replace("先の回答時点では", "回答した時点では"),
                       without_author=True).passed

    withdrawn = actual(request=advance(request, "「私には重い」は誤りです。"))
    body = withdrawn[0].artifact.reception
    assert "あなたには重い" not in body and "褒められた" in body
    assert inverse(withdrawn, body, without_author=True).passed


def test_saved_answer_and_correction_are_read_without_regeneration(qcase, qdb):
    user, parent, service = qcase
    first = run(service.start(user, parent))
    assert "褒められた" in first["current_observation"]["text"]
    current = run(answer(service, user, first, "今は私には重い。"))
    assert "回答した時点ではあなたには重い" in current["current_observation"]["text"]
    with patch.object(service.engine, "generate", side_effect=AssertionError("saved GET rendered")):
        assert run(service.get(user, parent)) == current
        assert run(service.start(user, parent)) == current

    current = run(cont(service, user, current, "continue-recipient"))
    current = run(answer(service, user, current,
                         "「私には重い」ではなく「私には苦しい」です。", "correct-recipient"))
    assert "先の回答時点ではあなたには苦しい" in current["current_observation"]["text"]
    assert "回答した時点では私には重い" not in current["current_observation"]["text"]
    assert current["original"] == first["original"]
    with patch.object(service.engine, "generate", side_effect=AssertionError("saved GET rendered")):
        assert run(service.get(user, parent)) == current
        assert run(service.start(user, parent)) == current

    current = run(cont(service, user, current, "continue-withdraw-recipient"))
    current = run(answer(service, user, current,
                         "「私には苦しい」は誤りです。", "withdraw-recipient"))
    assert "あなたには苦しい" not in current["current_observation"]["text"]
    assert "褒められた" in current["current_observation"]["text"]
    with patch.object(service.engine, "generate", side_effect=AssertionError("saved GET rendered")):
        assert run(service.get(user, parent)) == current
        assert run(service.start(user, parent)) == current


@pytest.mark.parametrize("memo", [
    "褒められたのに、嬉しくなかった。",
    "褒められたのに、嬉しくなかった。誘われたのに、悲しかった。",
])
@pytest.mark.parametrize("reply,recipient", [
    ("その時は私には怖くなかった。", "あなたには怖くな"),
    ("その時は僕には怖くなかった。", "あなたには怖くな"),
    ("その時は私は怖くなかった。", "あなたは怖くな"),
    ("その時は私には嬉しかった。", "その時はあなたには嬉しかった"),
    ("今は私には嬉しい。", "回答した時点ではあなたには嬉しい"),
])
def test_original_time_and_positive_answer_address_the_source_speaker(memo, reply, recipient):
    context = actual(request=advance(begin(memo), reply))
    follow = context[0].artifact.reception
    assert recipient in follow and "褒められた" in follow
    assert "私には" not in follow and "僕には" not in follow and "私は" not in follow
    assert inverse(context, follow, without_author=True).passed


@pytest.mark.parametrize("reply,old,new", [
    ("その時は私には怖くなかった。", "あなたには", "私には"),
    ("その時は私は怖くなかった。", "あなたは", "友人は"),
    ("その時は私には怖くなかった。", "怖くなく", "怖く"),
    ("その時は私には嬉しかった。", "その時はあなたには", "回答した時点ではあなたには"),
    ("今は私には嬉しい。", "あなたには", "友人には"),
    ("今は私には嬉しい。", "嬉しい", "悲しい"),
])
def test_original_time_and_positive_inverse_rejects_owner_time_polarity_meaning(reply, old, new):
    context = actual(request=advance(begin(), reply))
    follow = context[0].artifact.reception
    changed = follow.replace(old, new, 1)
    assert changed != follow
    assert not inverse(context, changed, without_author=True).passed


def test_saved_original_time_answer_correction_withdrawal_and_reopen(qcase, qdb):
    user, parent, service = qcase
    first = run(service.start(user, parent))
    current = run(answer(service, user, first, "その時は私には怖くなかった。"))
    assert "あなたには怖くな" in current["current_observation"]["text"]
    with patch.object(service.engine, "generate", side_effect=AssertionError("saved GET rendered")):
        assert run(service.get(user, parent)) == current

    current = run(cont(service, user, current, "continue-original-recipient"))
    current = run(answer(service, user, current,
                         "「私には怖くなかった」ではなく「私には寂しくなかった」です。",
                         "correct-original-recipient"))
    assert "あなたには寂しくな" in current["current_observation"]["text"]
    assert "あなたには怖くな" not in current["current_observation"]["text"]
    assert current["original"] == first["original"]
    with patch.object(service.engine, "generate", side_effect=AssertionError("saved GET rendered")):
        assert run(service.get(user, parent)) == current

    current = run(cont(service, user, current, "continue-withdraw-original-recipient"))
    current = run(answer(service, user, current,
                         "「私には寂しくなかった」は誤りです。", "withdraw-original-recipient"))
    assert "あなたには寂しくな" not in current["current_observation"]["text"]
    assert "褒められた" in current["current_observation"]["text"]
    with patch.object(service.engine, "generate", side_effect=AssertionError("saved GET rendered")):
        assert run(service.get(user, parent)) == current
        assert run(service.start(user, parent)) == current


def test_saved_positive_answer_reopens_with_recipient_perspective(qcase, qdb):
    user, parent, service = qcase
    first = run(service.start(user, parent))
    current = run(answer(service, user, first, "今は私には嬉しい。"))
    assert "回答した時点ではあなたには嬉しい" in current["current_observation"]["text"]
    with patch.object(service.engine, "generate", side_effect=AssertionError("saved GET rendered")):
        assert run(service.get(user, parent)) == current
        assert run(service.start(user, parent)) == current


@pytest.mark.parametrize("memo", [
    "褒められたのに、嬉しくなかった。誘われたのに、悲しかった。",
    "褒められたのに、嬉しくなかった。誘われたのに、悲しかった。頼まれたのに、寂しかった。",
])
@pytest.mark.parametrize("old,new,time,feeling", [
    ("今は私には嬉しい。", "「私には嬉しい」ではなく「私には楽しい」です。",
     "先の回答時点では", "楽しい"),
    ("今は僕には嬉しい。", "「僕には嬉しい」ではなく「僕には楽しい」です。",
     "先の回答時点では", "楽しい"),
    ("その時は私には嬉しかった。", "「私には嬉しかった」ではなく「私には楽しかった」です。",
     "その時は", "楽しかった"),
])
def test_positive_dative_correction_keeps_original_reactions_and_answer(memo, old, new, time, feeling):
    request = advance(advance(begin(memo), old), new)
    prepared = prepare_emlis_meaning(request)
    assert prepared.checkpoint.assessment_status == "RESOLVED"
    context = actual(request=request)
    follow = context[0].artifact.reception
    assert {m.reception_act for m in context[1].response_plan.human_reception_plan.moves} == {
        "stay_with_current_burden", "recognize_lived_change"}
    assert "嬉しさにはつながらず" in follow and "悲しさを感じ" in follow
    if "頼まれた" in memo:
        assert "頼まれたのに、寂しさを感じた" in follow
    assert time + "あなたには" + feeling in follow
    assert "私には" not in follow and "僕には" not in follow
    assert inverse(context, follow, without_author=True).passed


def test_positive_dative_correction_inverse_rejects_lost_source_and_changed_owner_time():
    request = advance(advance(begin(), "今は私には嬉しい。"),
                      "「私には嬉しい」ではなく「私には楽しい」です。")
    context = actual(request=request)
    follow = context[0].artifact.reception
    for old, new in (("あなたには楽しい", "私には楽しい"),
                     ("あなたには楽しい", "友人には楽しい"),
                     ("先の回答時点では", "回答した時点では"),
                     ("あなたには楽しい", "あなたには嬉しい"),
                     ("悲しさを感じ", "嬉しさを感じ")):
        changed = follow.replace(old, new, 1)
        assert changed != follow
        assert not inverse(context, changed, without_author=True).passed


def test_unsupported_positive_dative_correction_does_not_admit_foreign_replacement():
    request = advance(advance(begin(), "今は私には嬉しい。"),
                      "「私には嬉しい」ではなく「友人には楽しい」です。")
    prepared = prepare_emlis_meaning(request)
    assert prepared.checkpoint.assessment_status == "PARTIAL"
    follow = actual(request=request)[0].artifact.reception
    assert "友人には楽しい" not in follow and "あなたには嬉しい" not in follow
    assert "褒められた" in follow and "悲しさを感じ" in follow


def test_saved_positive_dative_correction_withdrawal_and_reopen(qcase, qdb):
    user, parent, service = qcase
    first = run(service.start(user, parent))
    current = run(answer(service, user, first, "今は私には嬉しい。"))
    assert "回答した時点ではあなたには嬉しい" in current["current_observation"]["text"]
    current = run(cont(service, user, current, "continue-positive-correction"))
    current = run(answer(service, user, current,
                         "「私には嬉しい」ではなく「私には楽しい」です。", "correct-positive-dative"))
    assert "先の回答時点ではあなたには楽しい" in current["current_observation"]["text"]
    assert "悲しさを感じ" in current["current_observation"]["text"]
    assert current["original"] == first["original"]
    with patch.object(service.engine, "generate", side_effect=AssertionError("saved GET rendered")):
        assert run(service.get(user, parent)) == current
        assert run(service.start(user, parent)) == current

    current = run(cont(service, user, current, "continue-positive-withdrawal"))
    current = run(answer(service, user, current,
                         "「私には楽しい」は誤りです。", "withdraw-positive-dative"))
    assert "あなたには楽しい" not in current["current_observation"]["text"]
    assert "褒められた" in current["current_observation"]["text"]
    with patch.object(service.engine, "generate", side_effect=AssertionError("saved GET rendered")):
        assert run(service.get(user, parent)) == current
        assert run(service.start(user, parent)) == current


@pytest.mark.parametrize("self_text,recipient", [
    ("", ""), ("私は", "あなたは"), ("私も", "あなたも"),
    ("自分は", "あなたは"), ("私には", "あなたには"), ("僕には", "あなたには"),
])
@pytest.mark.parametrize("occasion,old,new,time", [
    ("今は", "嬉しい", "楽しい", "先の回答時点では"),
    ("その時は", "嬉しかった", "楽しかった", "その時は"),
])
@pytest.mark.parametrize("memo", [
    "褒められたのに、嬉しくなかった。誘われたのに、悲しかった。",
    "褒められたのに、嬉しくなかった。誘われたのに、悲しかった。頼まれたのに、寂しかった。",
])
def test_admitted_positive_correction_preserves_source_reactions_across_self_forms(
        self_text, recipient, occasion, old, new, time, memo):
    initial_request = begin(memo)
    first = actual(request=initial_request)
    request = advance(initial_request, occasion + self_text + old + "。")
    before = actual(request=request)
    assert recipient + old in before[0].artifact.reception
    request = advance(request, f"「{self_text}{old}」ではなく「{self_text}{new}」です。")
    prepared = prepare_emlis_meaning(request)
    update, = prepared.checkpoint.answer_update.updates
    assert update.operation == "REVISE" and prepared.checkpoint.assessment_status == "RESOLVED"
    corrected = actual(request=request)
    follow = corrected[0].artifact.reception
    assert time + recipient + new in follow
    assert "褒められたことは、嬉しさにはつながら" in follow
    assert "誘われたのに、悲しさを感じ" in follow
    if "頼まれた" in memo:
        assert "頼まれたのに、寂しさを感じた" in follow
    # Multiple events still require the answer's event to be explicit.
    assert "褒められたことについて、" + time in follow
    assert "小さくせずに受け止めています" not in follow
    assert inverse(corrected, follow, without_author=True).passed
    # The two-event thread ends after correction. Only the three-event
    # fixture has the third question needed to submit a later withdrawal.
    if "頼まれた" in memo:
        withdrawn = actual(request=advance(request, f"「{self_text}{new}」は誤りです。"))
        assert withdrawn[0].artifact.reception == first[0].artifact.reception
        assert inverse(withdrawn, withdrawn[0].artifact.reception, without_author=True).passed


@pytest.mark.parametrize("old,new", [
    ("あなたも", "私も"), ("あなたも", "友人も"), ("あなたも", "あなたは"),
    ("先の回答時点では", "回答した時点では"), ("楽しい", "楽しくない"),
    ("楽しい", "嬉しい"), ("悲しさを感じ", "嬉しさを感じ"),
    ("褒められたことについて、", "誘われたことについて、"),
])
def test_positive_self_correction_rejects_changed_source_without_author(old, new):
    request = advance(advance(begin(), "今は私も嬉しい。"),
                      "「私も嬉しい」ではなく「私も楽しい」です。")
    context = actual(request=request)
    follow = context[0].artifact.reception
    changed = follow.replace(old, new, 1)
    assert changed != follow
    assert not inverse(context, changed, without_author=True).passed


@pytest.mark.parametrize("text", ["今は私は私には嬉しい。", "今は私は僕には嬉しい。"])
def test_positive_answer_does_not_partially_rewrite_chained_self_subjects(text):
    context = actual(request=advance(begin("褒められたのに、嬉しくなかった。"), text))
    follow = context[0].artifact.reception
    assert "あなたは私には" not in follow and "あなたは僕には" not in follow
    assert inverse(context, follow, without_author=True).passed
    # A partial person shift must not become an independently accepted reading.
    corrupted = follow.replace("私は", "あなたは", 1)
    assert corrupted != follow
    assert not inverse(context, corrupted, without_author=True).passed


@pytest.mark.parametrize("self_text,recipient", [
    ("", ""), ("私は", "あなたは"), ("私も", "あなたも"), ("自分は", "あなたは"),
])
def test_saved_positive_correction_preserves_all_reactions_and_withdrawal(qcase, qdb, self_text, recipient):
    user, parent, service = qcase
    first = run(service.start(user, parent))
    current = run(answer(service, user, first, f"今は{self_text}嬉しい。"))
    assert "回答した時点では" + recipient + "嬉しい" in current["current_observation"]["text"]
    with patch.object(service.engine, "generate", side_effect=AssertionError("saved GET rendered")):
        assert run(service.get(user, parent)) == current
        assert run(service.start(user, parent)) == current
    current = run(cont(service, user, current, "continue-self-positive"))
    current = run(answer(service, user, current,
        f"「{self_text}嬉しい」ではなく「{self_text}楽しい」です。", "correct-self-positive"))
    text = current["current_observation"]["text"]
    assert "先の回答時点では" + recipient + "楽しい" in text
    assert "嬉しさにはつながらず" in text and "悲しさを感じ" in text and "寂しさを感じた" in text
    assert current["original"] == first["original"]
    with patch.object(service.engine, "generate", side_effect=AssertionError("saved GET rendered")):
        assert run(service.get(user, parent)) == current
        assert run(service.start(user, parent)) == current
    current = run(cont(service, user, current, "continue-withdraw-self-positive"))
    current = run(answer(service, user, current,
        f"「{self_text}楽しい」は誤りです。", "withdraw-self-positive"))
    assert current["current_observation"]["text"] == first["current_observation"]["text"]
    with patch.object(service.engine, "generate", side_effect=AssertionError("saved GET rendered")):
        assert run(service.get(user, parent)) == current
        assert run(service.start(user, parent)) == current
