from __future__ import annotations

from emlis_ai_reply_final_review_service import review_emlis_ai_reply_text
from emlis_ai_types import WorldModel, WorldModelFacts


def test_final_review_blocks_broken_connection_before_user_return():
    text = """Emlisです。
たまに泣きそうになるくらい嫌になる時あるけどそれだとことが、今回大きく残っていたのですね。
悲しみだけでなく、怒りも同じ場所にあったのですね。"""

    review = review_emlis_ai_reply_text(comment_text=text, world_model=WorldModel(facts=WorldModelFacts()))

    assert any(issue.code == "raw_anchor_broken_connection" for issue in review.issues)
    assert review.passed is False
    assert review.repaired_text is None


def test_final_review_reports_ending_repetition_without_adding_presence_line():
    text = """Emlisです。
泣きそうになるくらい嫌になる時があったのですね。
怒りも同じ場所にあったのですね。
癒しになっていたのですね。"""

    review = review_emlis_ai_reply_text(comment_text=text, world_model=WorldModel(facts=WorldModelFacts()))

    assert review.passed is False
    assert review.repaired_text is None
    assert any(issue.code in {"sentence_ending_repetition", "sentence_ending_repetition_remaining", "presence_line_missing"} for issue in review.issues)
