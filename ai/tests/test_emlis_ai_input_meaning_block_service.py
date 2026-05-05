from __future__ import annotations

from emlis_ai_input_meaning_block_service import build_input_meaning_blocks, build_meaning_coverage_plan
from emlis_ai_phrase_shaping_service import shape_user_phrases
from emlis_ai_types import EvidenceRef


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


def test_long_clear_input_is_split_into_required_meaning_blocks():
    current_input = {"id": "emo-long", "memo": LONG_SELF_UNDERSTANDING_MEMO, "memo_action": ""}
    evidence = EvidenceRef(kind="emotion", ref_id="emo-long")
    shaped = shape_user_phrases(anchors=[], current_input=current_input)

    blocks = build_input_meaning_blocks(
        current_input=current_input,
        shaped_user_phrases=shaped,
        evidence=evidence,
    )
    roles = {block.role for block in blocks}

    assert "state_awareness" in roles
    assert "effort_history" in roles
    assert "continuation_wish" in roles
    assert "not_want_to_quit" in roles
    assert "fatigue_or_limit" in roles
    assert "collapse_anxiety" in roles
    assert "dual_holding" in roles
    assert "paced_progress" in roles
    assert "self_understanding" in roles

    plan = build_meaning_coverage_plan(current_input=current_input, meaning_blocks=blocks)
    assert plan.clear_long_input is True
    assert plan.input_level in {"long", "very_long"}
    assert plan.min_blocks_to_cover >= 5
    assert len(plan.selected_block_keys) >= 5
