from __future__ import annotations

from emlis_ai_phrase_shaping_service import shape_user_phrases
from emlis_ai_reply_final_review_service import review_emlis_ai_reply_text
from emlis_ai_types import EvidenceRef, UserWordAnchor


def test_phrase_shaping_avoids_broken_noun_phrase_for_halfway_clause():
    anchor = UserWordAnchor(
        anchor_key="a1",
        text="私は私自身頑張ることも楽しむことも中途半端だから",
        source_field="memo",
        role="self_dislike_from_halfway",
        evidence=[EvidenceRef(kind="emotion", ref_id="emo")],
    )
    phrase = shape_user_phrases(anchors=[anchor], current_input={"id": "emo", "memo": anchor.text, "memo_action": ""})[0]

    assert "中途半端だ気持ち" not in phrase.phrase
    assert "中途半端だから気持ち" not in phrase.nominal
    assert "中途半端に" in phrase.phrase


def test_final_review_blocks_broken_noun_phrase_without_rewriting():
    review = review_emlis_ai_reply_text(
        comment_text="Emlisです。\nそこには、中途半端だ気持ちも近くにありました。\nここに置いてくれた言葉を、Emlisは軽く扱いません。",
        world_model=None,
    )
    assert any(issue.code == "broken_noun_phrase" for issue in review.issues)
    assert review.passed is False
    assert review.repaired_text is None
