from __future__ import annotations

from emlis_ai_input_meaning_block_service import build_input_meaning_blocks, build_meaning_coverage_plan
from emlis_ai_response_composition_service import build_reply_narrative_arc, build_response_composition_plan
from emlis_ai_types import EvidenceRef

SELF_SACRIFICE_MEMO = """
どこかで私が我慢していれば、誰にも心配かけないし負担もかけないからこれでいいって思ってた
自分が少し我慢すれば全部丸く収まるって考えてたし
それが一番楽なやり方だと思ってた

でもそれを続けていくと、しんどい気持ちをずっと一人で
抱え込むことになるし、気づいたら余裕がなくなってることもある

本当はしんどい時にちゃんと誰かに話したり
頼ったりすることも必要で、それができる方が無理せず
続けていけるんだと思う

それに、自分を守るために距離を取ったり
無理しない選択をすることもちゃんと必要なことなんだよね
我慢することだけが正しいわけじゃなくて
自分の状態を見ながらどう動くかを考えていくことも
大切なんだと思う
"""


def test_response_composition_plan_detects_self_sacrifice_to_boundary_care_flow():
    current_input = {"memo": SELF_SACRIFICE_MEMO, "memo_action": ""}
    ref = EvidenceRef(kind="emotion", ref_id="current")
    blocks = build_input_meaning_blocks(current_input=current_input, shaped_user_phrases=[], evidence=ref)
    coverage = build_meaning_coverage_plan(current_input=current_input, meaning_blocks=blocks)
    plan = build_response_composition_plan(
        input_level=coverage.input_level,
        clear_long_input=coverage.clear_long_input,
        meaning_blocks=blocks,
    )
    arc = build_reply_narrative_arc(composition_plan=plan, meaning_blocks=blocks)

    assert plan is not None
    assert plan.narrative_pattern == "old_strategy_limit_realization_new_boundary"
    assert plan.ordered_line_roles[:3] == ["greeting", "opening_thesis", "old_strategy"]
    assert arc is not None
    assert "我慢" in arc.opening_thesis
    assert "抱え" in arc.opening_thesis
