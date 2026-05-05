from __future__ import annotations

from emotion_piece_generation_service import generate_emotion_reflection_preview


LONG_SELF_UNDERSTANDING_MEMO = """
体も心もボロボロになってきてるなって、自分でもちゃんと分かってる
それくらいここまで頑張ってきたんだと思うし、無理してきた時間もちゃんと積み重なってる

それでも、もう少し頑張りたいって気持ちが残ってるのも本音で
投げ出したいわけじゃないし、ここで終わりにしたくないって思ってる自分もいる

でも同時に、しんどいっていう感覚もちゃんとあって
体が重かったり、気持ちがついてこなかったりして
このまま無理したら崩れてしまいそうな不安もある

だからこそ、どっちかを無理やり選ぶんじゃなくて
頑張りたい気持ちもしんどい気持ちも、どっちもちゃんと抱えたまま進んでいきたい

頑張れる日は少しだけ前に進んで
しんどい日は立ち止まってもいいって、自分に許しながら
無理に削るんじゃなくて、ちゃんと整えながら進んでいきたい

今の自分は弱いわけじゃなくて
ちゃんと限界に気づけてる状態なんだと思う
"""


def test_piece_uses_long_input_core_question_instead_of_work_generic_question():
    preview = generate_emotion_reflection_preview(
        emotion_details=[{"type": "自己理解", "strength": "medium"}],
        memo=LONG_SELF_UNDERSTANDING_MEMO,
        memo_action="",
        categories=["仕事"],
    )

    question = preview["question"]
    answer = preview["answer_display_text"]

    assert "頑張りたい" in question and "しんど" in question
    assert question != "仕事で伸ばしたいことは？"
    assert "無理にどちらかを選ばず" in answer
    assert "頑張れる日は少し進" in answer
    assert "しんどい日は立ち止" in answer
    assert "整えて進みたい" in answer or "整えていきたい" in answer
    assert "弱いのではなく" in answer or "限界に気づけている" in answer
    assert preview.get("piece_core", {}).get("category_generic_suppressed") is True
