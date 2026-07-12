from __future__ import annotations

from emlis_ai_input_meaning_block_service import (
    build_input_meaning_blocks,
    build_major_meaning_retention_plan,
    build_meaning_coverage_plan,
    build_whole_input_meaning_arc,
)
from emlis_ai_phrase_shaping_service import shape_user_phrases
from emlis_ai_types import EvidenceRef


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


def test_self_and_others_happiness_input_builds_arc_and_retention_plan():
    current_input = {"id": "emo-self-happy", "memo": SELF_AND_OTHERS_HAPPINESS_MEMO, "memo_action": ""}
    evidence = EvidenceRef(kind="emotion", ref_id="emo-self-happy")
    shaped = shape_user_phrases(anchors=[], current_input=current_input)
    blocks = build_input_meaning_blocks(current_input=current_input, shaped_user_phrases=shaped, evidence=evidence)
    roles = {block.role for block in blocks}

    assert {"self_view", "limit_or_exhaustion", "not_want_to_quit", "wish_or_hope"} <= roles
    assert not ({
        "other_contribution",
        "self_dislike_from_halfway",
        "future_not_giving_up",
        "betrayal_fear",
        "own_happiness_wish",
        "concrete_life_wishes",
        "unreachable_wish",
        "present_effort_toward_wish",
    } & roles)

    coverage = build_meaning_coverage_plan(current_input=current_input, meaning_blocks=blocks)
    arc = build_whole_input_meaning_arc(meaning_blocks=blocks, evidence=evidence)
    retention = build_major_meaning_retention_plan(
        meaning_blocks=blocks,
        coverage_plan=coverage,
        whole_input_meaning_arc=arc,
    )

    assert coverage.clear_long_input is True
    assert arc is not None
    assert arc.arc_key == "generic_current_input_source_order"
    assert arc.ordered_block_keys == [block.block_key for block in blocks]
    assert arc.core_wish_keys
    assert arc.fear_keys
    assert blocks[0].block_key in retention.must_keep_block_keys
    assert blocks[-1].block_key in retention.must_keep_block_keys
    assert retention.reason == "structural_retention_without_example_roles"
    assert retention.min_must_keep_coverage_ratio == 1.0
