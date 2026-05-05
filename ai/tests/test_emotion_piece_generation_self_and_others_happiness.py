from __future__ import annotations

from emotion_piece_generation_service import generate_emotion_reflection_preview


SELF_AND_OTHERS_HAPPINESS_MEMO = """
誰かの役に立てればそれでいい
私は私自身頑張ることも楽しむことも中途半端だから
自分のことは好きになれないけど
他の人たちが幸せに笑ってくれてて
その人たちの役に立てるなら1番それが幸せかな
自分のこと 今後のこと まだ諦めたくないけれど
諦めてる自分もいる もう期待して裏切られたくないから
そう思う中でも私も幸せになりたいって思う自分もいる
それは諦めたくない時だと思う
前に考えた、もう既に幸せなことはあるって事
それ以上に求めてるんだよねきっと
好きなことをもっとしたい
納得いくまで十分にたのしみたい
素敵なパートナーと出会って幸せになりたい
手の届かい所にある願い
でもその願いに届くように、今頑張れることを大切にしたい
"""


def test_piece_communicates_self_and_others_happiness_core_instead_of_generic_relationship():
    preview = generate_emotion_reflection_preview(
        emotion_details=[{"type": "悲しみ", "strength": "medium"}],
        memo=SELF_AND_OTHERS_HAPPINESS_MEMO,
        memo_action="",
        categories=["人間関係"],
    )

    question = preview["question"]
    answer = preview["answer_display_text"]
    core = preview.get("piece_core") or {}

    assert ("自分" in question or "願い" in question) and ("大切" in question or "怖" in question or "近づ" in question)
    assert question != "伸ばしたいことは？"
    assert "人間関係です" not in answer
    assert "誰かの役に立" in answer
    assert "幸せ" in answer and ("願い" in answer or "自分自身" in answer)
    assert "裏切られる" in answer or "傷つく" in answer or "怖" in answer
    assert "好きなこと" in answer
    assert "好き" in answer or "楽し" in answer or "願い" in answer
    assert "今" in answer and "大切" in answer
    assert "中途半端だ気持ち" not in answer
    assert core.get("category_generic_suppressed") is True
    assert core.get("communicative_core_ok") is True
