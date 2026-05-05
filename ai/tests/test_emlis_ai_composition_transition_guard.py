from __future__ import annotations

from emlis_ai_reply_final_review_service import review_emlis_ai_reply_text


def test_first_content_line_cannot_start_midstream():
    review = review_emlis_ai_reply_text(
        comment_text="Emlisです。\nただ同時に、しんどさもありました。\nここに置いてくれた言葉を、Emlisは軽く扱いません。",
        world_model=None,
    )
    codes = {issue.code for issue in review.issues}
    assert review.passed is False
    assert "first_content_line_midstream" in codes or "first_content_line_midstream_remaining" in codes
