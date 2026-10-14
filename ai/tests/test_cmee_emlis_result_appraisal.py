"""Original appraisals own their objects; semantic checks are not Product Read."""
from dataclasses import replace

import pytest

from test_cmee_emlis_q1_thread import initial
from cocolon_meaning_experience_engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning, build_updated_grounded_plan
from cocolon_meaning_experience_engine.emlis_thread_projection import project_thread_meaning
from emlis_ai_grounded_observation_plan import source_owned_result_appraisal
from emlis_ai_grounded_observation_gate import evaluate_grounded_surface_body_inverse
from emlis_ai_grounded_sentence_surface import build_grounded_sentence_plan


def request(memo, action="植木に水をやった。"):
    req = initial(memo, action)
    return replace(req, emlis_thread=replace(req.emlis_thread, capability_snapshot="Q3_FREE"))


@pytest.mark.parametrize("memo,polarity,time", [
    ("資料を分類できて満足した。", "positive", "past"),
    ("予定を決められて納得しました。", "positive", "past"),
    ("文章を直せたことに満足している。", "positive", "present"),
    ("案を選んで納得した。", "positive", "past"),
    ("意見をまとめて満足しなかった。", "negative", "past"),
    ("資料を分類したことにまだ納得していない。", "negative", "present"),
    ("昨日は私は資料を分類できてとても満足しました。", "positive", "past"),
    ("資料を分類したことにはあまり満足しませんでした。", "negative", "past"),
])
def test_appraisal_keeps_its_object_outer_polarity_and_time_in_actual_body(memo, polarity, time):
    req = request(memo)
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    about = [r for r in plan.relations if source_owned_result_appraisal(r, plan.nuclei)]
    assert len(about) == 1
    index = {n.nucleus_id: n for n in plan.nuclei}
    event, feeling = (index[nid] for nid in (about[0].from_nucleus_id, about[0].to_nucleus_id))
    assert event.kind == "event" and event.semantic_frame.modality == "fact"
    assert (feeling.kind, feeling.semantic_frame.predicate_kind, feeling.semantic_frame.modality,
            feeling.semantic_frame.polarity, feeling.semantic_frame.time_scope) == ("reaction", "feeling", "feeling", polarity, time)
    assert event.source_span_ids == feeling.source_span_ids
    assert plan.response_plan.human_follow_target_ids == (feeling.nucleus_id,)
    projection = project_thread_meaning(prepared, plan)
    assert any(str(row.relation_kind).endswith("ABOUT_TARGET") for row in projection.premeaning.source_relation_rows)
    outcome = MeaningExperienceEngine().generate(req)
    assert outcome.artifact is not None, outcome.reason_codes
    assert "植木" in outcome.artifact.observation
    assert "植木" not in outcome.artifact.reception
    assert "状態に表れた変化" not in outcome.artifact.reception
    assert "努力" not in outcome.artifact.reception
    assert "満足" in outcome.artifact.reception or "納得" in outcome.artifact.reception


@pytest.mark.parametrize("memo", [
    "同僚は資料を分類できて満足したと言った。",
    "同僚が資料を分類できて満足した。",
    "同僚が話した。資料を分類できて満足した。",
    "『資料を分類できて満足した』と聞いた。",
    "資料を分類できたら満足できそう。",
    "資料を分類できて満足したかもしれない。",
    "資料を分類できて満足した？",
    "資料を分類できて満足したら。",
    "資料を分類できて満足し",
    "満足度調査の項目を分類した。",
    "資料を分類しなくて満足した。",
    "資料を分類しないで満足した。",
    "資料を分類した。嬉しかったのは友人からの返事だ。",
    "資料を準備中で満足した。",
    "資料を分類する予定で満足した。",
    "資料を分類したつもりで満足した。",
    "山田さんは仕事を終えた。資料を分類できて満足した。",
    "ともこは仕事を終えた。資料を分類できて満足した。",
    "同僚たちが仕事を終えた。資料を分類できて満足した。",
])
def test_nonasserted_foreign_nominal_or_unfinished_text_does_not_acquire_appraisal_proof(memo):
    plan = build_updated_grounded_plan(prepare_emlis_meaning(request(memo)))
    assert not any(source_owned_result_appraisal(r, plan.nuclei) for r in plan.relations)


def test_changing_an_independent_action_does_not_replace_the_appraisal():
    bodies = [MeaningExperienceEngine().generate(request("資料を分類できて満足した。", action)).artifact
              for action in ("植木に水をやった。", "机を拭いた。", "")]
    assert all(bodies)
    assert len({body.reception for body in bodies}) == 1
    assert bodies[0].observation != bodies[1].observation


def test_body_reader_rejects_swapped_object_polarity_and_invented_answer_time():
    req = request("資料を分類できて満足した。")
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    projection = project_thread_meaning(prepared, plan)
    resolver = prepared.thread.resolver()
    sentence = build_grounded_sentence_plan(plan, resolver, recovery_stage="full")
    body = MeaningExperienceEngine().generate(req).artifact.text
    def valid(text):
        return evaluate_grounded_surface_body_inverse(body=text.encode(), plan=plan,
            sentence_plan=sentence, resolver=resolver,
            selected_subjective_input=projection.selected_reception).passed
    assert valid(body)
    for changed in (body.replace("満足した", "満足しなかった"),
                    body.replace("資料を分類でき", "植木に水をやっ"),
                    body.replace("出来事に対する評価は", "回答した時点の評価は"),
                    body.replace("資料を分類できたことに", "資料を分類できなかったことに")):
        assert changed != body
        assert not valid(changed)
