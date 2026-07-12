# -*- coding: utf-8 -*-
from __future__ import annotations

"""Current-owner proofs for the FB172 B6 candidate families.

Only the positive-recovery relation direction is a production RED.  The D and
H lineage cases prove that their valid obligations already pass through the
Grounded canonical owner without restoring legacy recomposition or material
IDs.  No exact public body is asserted.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from emlis_ai_current_input_bundle import normalize_emlis_current_input
from emlis_ai_evidence_ledger_service import (
    build_evidence_ledger,
    build_evidence_span_resolver,
)
from emlis_ai_grounded_observation_gate import evaluate_grounded_observation_gate
from emlis_ai_grounded_observation_plan import build_grounded_observation_plan
from emlis_ai_grounded_sentence_surface import (
    build_grounded_sentence_plan,
    realize_grounded_sentence_plan,
)
from emlis_ai_reply_service import render_emlis_ai_reply


_POSITIVE_RECOVERY = {
    "memo": (
        "疲れが残っていたけれど、少し戻ってくる感覚もある。"
        "重さが全部消えたわけではないけれど、整え直したい気持ちがある。"
    ),
    "emotions": ["自己理解"],
    "category": ["生活"],
}
_D_CURRENT_INPUT = {
    "memo": (
        "悲しい気持ちばかりで身の回りにある優しさを見逃してしまいそうになるが、"
        "ちゃんと優しさに触れてそれを実感出来ていることが嬉しい。"
        "そして私のために怒ってくれる存在に感謝の気持ちが溢れてくる。"
        "1つの関係の終わりが、もうひとつの友達という関係を強くしてくれたと考えれば、"
        "少し自分の中で区切りがついて成長出来るように感じる。"
        "そしてその優しさを今回受け止めて別の形で必ず返していきたい。"
    ),
    "memo_action": "彼氏と別れたが、友達が変わらず今も優しくしてくれている。そして私のために怒ってくれている。",
    "emotions": ["喜び"],
    "category": ["恋愛", "人間関係", "価値観"],
}
_H_CURRENT_INPUT = {
    "memo": (
        "ふとした時に、これやってみたいなとか\n"
        "自分にも出来るかもしれないって思う瞬間がある\n"
        "でもそのあとに、なんで私はそう思ったんだろうって考えることが多い\n"
        "きっと今までの経験とか気持ちとか\n"
        "色んなものが重なってその考えが出てきてるんだと思う\n"
        "だから私は、その「やりたい」と思った気持ちを大事にしたい\n"
        "頑張って良かった もっと色々挑戦したい\n"
        "そう思えることが大きな一歩だと思う\n"
        "ずっと落ち込んでて何もしたくなくて\n"
        "自信をなくして諦めていたから\n"
        "この気持ちになれたことを大切にして\n"
        "つぎどう頑張るか知って行きたい"
    ),
    "emotions": ["平穏"],
    "category": ["生活"],
}


def _artifacts(raw_input: dict[str, Any]):
    current_input = normalize_emlis_current_input(raw_input)
    spans = tuple(build_evidence_ledger(current_input))
    resolver = build_evidence_span_resolver(spans, current_input=current_input)
    plan = build_grounded_observation_plan(current_input, evidence_spans=spans)
    sentence_plan = build_grounded_sentence_plan(plan, resolver)
    surface = realize_grounded_sentence_plan(sentence_plan, plan, resolver)
    gate = evaluate_grounded_observation_gate(
        plan=plan,
        sentence_plan=sentence_plan,
        surface_result=surface,
        resolver=resolver,
        product_readfeel_status="not_evaluated",
    )
    return plan, sentence_plan, gate


def _render(raw_input: dict[str, Any]):
    async def render():
        return await render_emlis_ai_reply(
            user_id="fb172-b6-current-owner",
            subscription_tier="free",
            current_input=raw_input,
        )

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(render())
    with ThreadPoolExecutor(max_workers=1) as executor:
        return executor.submit(lambda: asyncio.run(render())).result()


def test_fb172_b6_positive_recovery_preserves_required_relation_direction() -> None:
    plan, sentence_plan, gate = _artifacts(_POSITIVE_RECOVERY)
    required = {
        relation.relation_id: relation
        for relation in plan.relations
        if relation.relation_id in plan.coverage_requirements.required_relation_ids
    }
    assert required
    for relation_id, relation in required.items():
        line = next(
            line for line in sentence_plan.lines
            if relation_id in line.binding.relation_ids
        )
        assert line.binding.nucleus_ids.index(relation.from_nucleus_id) < (
            line.binding.nucleus_ids.index(relation.to_nucleus_id)
        )
    assert gate.passed is True
    assert "required_relation_direction_mismatch" not in gate.rejection_reasons
    reply = _render(_POSITIVE_RECOVERY)
    assert reply.meta["observation_status"] == "passed"
    assert reply.comment_text.strip()


def test_fb172_b6_d_lineage_is_already_current_canonical_pass() -> None:
    plan, sentence_plan, gate = _artifacts(_D_CURRENT_INPUT)
    assert gate.passed is True
    assert set(plan.coverage_requirements.required_nucleus_ids) <= {
        nucleus_id
        for line in sentence_plan.lines
        for nucleus_id in line.binding.nucleus_ids
    }
    reply = _render(_D_CURRENT_INPUT)
    assert reply.meta["observation_status"] == "passed"
    assert reply.meta["generation_path"] == (
        "grounded_observation_plan_sentence_surface_canonical_v1"
    )
    assert reply.comment_text.strip()
    assert "complete_initial_surface_recomposition_summary" not in reply.meta


def test_fb172_b6_h_lineage_retains_change_and_intention_without_old_material_ids() -> None:
    plan, sentence_plan, gate = _artifacts(_H_CURRENT_INPUT)
    required = [
        nucleus for nucleus in plan.nuclei
        if nucleus.nucleus_id in plan.coverage_requirements.required_nucleus_ids
    ]
    attributes = {
        code for nucleus in required for code in nucleus.semantic_frame.attribute_codes
    }
    assert "semantic_role:retained_intention" in attributes
    assert attributes & {
        "semantic_role:current_change",
        "semantic_role:explicit_result",
    }
    assert gate.passed is True
    assert set(plan.coverage_requirements.required_nucleus_ids) <= {
        nucleus_id
        for line in sentence_plan.lines
        for nucleus_id in line.binding.nucleus_ids
    }
    reply = _render(_H_CURRENT_INPUT)
    assert reply.meta["observation_status"] == "passed"
    assert reply.comment_text.strip()
    assert "relation_material_ids" not in reply.meta
