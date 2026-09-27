"""A user's later answer remains theirs when Emlis addresses them."""

from unittest.mock import patch

import pytest

from test_cmee_emlis_received_discourse import actual, inverse
from test_cmee_emlis_q3_thread import begin, advance
from test_emlis_q2_application import answer, run
from test_emlis_q3_application import cont, qcase, qdb


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
