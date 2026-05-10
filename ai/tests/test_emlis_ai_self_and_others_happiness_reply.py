from __future__ import annotations

from emlis_multi_perspective_test_helpers import assert_no_legacy_observation_text, assert_phase1_display_closed, run_multi_perspective_case


SELF_AND_OTHERS_HAPPINESS_MEMO = """
誰かの役に立てると嬉しいし、周りの人が幸せだと安心する。
でもそればかり考えていると、自分自身の幸せを後回しにしてしまうことがある。
他の人のことを大切にしたい気持ちと、自分も幸せになりたい気持ちが両方ある。
"""


def test_self_and_others_happiness_uses_relation_graph_without_fixed_reply_body():
    result = run_multi_perspective_case(SELF_AND_OTHERS_HAPPINESS_MEMO, display_name="Mash", emotion="悲しみ", category="人間関係")

    assert_phase1_display_closed(result.decision)
    assert result.graph.core_tensions or len(result.graph.value_or_strength_signals) >= 2
    assert result.text == ""
    joined_evidence = "\n".join(span.raw_text for span in result.evidence)
    assert "役に立" in joined_evidence or "幸せ" in joined_evidence
    assert_no_legacy_observation_text(result.text)
