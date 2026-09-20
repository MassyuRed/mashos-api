"""Public synthetic regression: quoted correction metadata is not self authority."""

from helpers.retained_assertions import continue_assertions, retained_assertion
from dataclasses import replace
from itertools import product

import pytest

from cocolon_meaning_experience_engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.emlis_answer_update import (
    build_updated_grounded_plan,
    prepare_emlis_meaning,
)
from cocolon_meaning_experience_engine.emlis_thread_projection import project_thread_meaning
from emlis_ai_grounded_observation_gate import evaluate_grounded_surface_body_inverse
import emlis_ai_grounded_sentence_surface as surface
from test_cmee_emlis_q1_thread import answered, initial, prepared_request
from test_cmee_emlis_q3_thread import advance, begin


_MARKERS = ("書き方を間違えた", "記録が間違っていた")
_QUOTES = (("「", "」"), ("『", "』"))


def _reported(marker, quotes=("「", "」")):
    opening, closing = quotes
    return f"友人は{opening}記録を見た。{marker}。{closing}と言った。"


def _assert_original_reaction_retained(prepared):
    original = prepared.original_plan
    reaction = next(n for n in original.nuclei if n.nucleus_id == "nucleus:s1:reaction")
    after = build_updated_grounded_plan(prepared)
    assert not prepared.checkpoint.inactive_claim_refs
    assert reaction in after.nuclei
    assert all(r in after.relations for r in original.relations)
    assert [u.operation for u in prepared.checkpoint.answer_update.updates] == ["ADD"]


@pytest.mark.parametrize("marker,quotes,report_first", product(_MARKERS, _QUOTES, (False, True)))
@continue_assertions
def test_quoted_meta_cannot_revise_original_or_remove_its_follow(marker, quotes, report_first):
    report = _reported(marker, quotes)
    self_answer = "その時は嬉しかった。"
    text = report + self_answer if report_first else self_answer + report
    request = answered(text)
    prepared = prepare_emlis_meaning(request)
    _assert_original_reaction_retained(prepared)
    retained_assertion(lambda: (prepared.checkpoint.assessment_status == "PARTIAL"), "prepared.checkpoint.assessment_status == 'PARTIAL'")
    request, checkpoint = prepared_request(request)
    result = MeaningExperienceEngine().generate(request)
    retained_assertion(lambda: (result.artifact is not None), 'result.artifact is not None', lambda: (result.reason_codes))
    retained_assertion(lambda: (result.meaning_checkpoint == checkpoint), 'result.meaning_checkpoint == checkpoint')
    retained_assertion(lambda: (result.body_state == "PARTIALLY_REFINED" and result.question is None), "result.body_state == 'PARTIALLY_REFINED' and result.question is None")
    retained_assertion(lambda: ("嬉しくなかった" in result.artifact.observation), "'嬉しくなかった' in result.artifact.observation")
    retained_assertion(lambda: ("褒められたのに嬉しくなかったこと" in result.artifact.reception), "'褒められたのに嬉しくなかったこと' in result.artifact.reception")
    retained_assertion(lambda: ("その時に嬉しかったという気持ち" in result.artifact.reception), "'その時に嬉しかったという気持ち' in result.artifact.reception")
    retained_assertion(lambda: (report.rstrip("。") in result.artifact.observation), "report.rstrip('。') in result.artifact.observation")
    retained_assertion(lambda: ("今回の観測に反映できていない部分があります" in result.artifact.observation), "'今回の観測に反映できていない部分があります' in result.artifact.observation")
    retained_assertion(lambda: (marker not in result.artifact.reception), 'marker not in result.artifact.reception')


@pytest.mark.parametrize("marker,marker_first", product(_MARKERS, (False, True)))
@continue_assertions
def test_self_owned_meta_still_revises_regardless_of_sentence_order(marker, marker_first):
    claim = "その時は嬉しかった。"
    text = marker + "。" + claim if marker_first else claim + marker + "。"
    request = answered(text)
    prepared = prepare_emlis_meaning(request)
    update, = prepared.checkpoint.answer_update.updates
    retained_assertion(lambda: (update.operation == "REVISE"), "update.operation == 'REVISE'")
    retained_assertion(lambda: (update.superseded_claim_refs == ("nucleus:s1:reaction",)), "update.superseded_claim_refs == ('nucleus:s1:reaction',)")
    retained_assertion(lambda: (prepared.checkpoint.assessment_status == "RESOLVED"), "prepared.checkpoint.assessment_status == 'RESOLVED'")
    request, _ = prepared_request(request)
    result = MeaningExperienceEngine().generate(request)
    retained_assertion(lambda: (result.artifact is not None), 'result.artifact is not None', lambda: (result.reason_codes))
    retained_assertion(lambda: ("嬉しくなかった" not in result.artifact.text), "'嬉しくなかった' not in result.artifact.text")
    retained_assertion(lambda: ("その時に嬉しかった" in result.artifact.reception), "'その時に嬉しかった' in result.artifact.reception")


@pytest.mark.parametrize("quotes", _QUOTES)
def test_quoted_meta_without_a_self_answer_changes_no_meaning(quotes):
    prepared = prepare_emlis_meaning(answered(_reported(_MARKERS[0], quotes)))
    assert not prepared.checkpoint.answer_update.updates
    assert not prepared.checkpoint.inactive_claim_refs
    assert prepared.checkpoint.assessment_status == "UNRESOLVED"


def test_nested_quote_meta_is_unresolved_and_not_correction_authority():
    text = "友人は「彼は『記録を見た。書き方を間違えた。』と言った。」と話した。その時は嬉しかった。"
    prepared = prepare_emlis_meaning(answered(text))
    _assert_original_reaction_retained(prepared)
    assert prepared.checkpoint.assessment_status == "PARTIAL"


@pytest.mark.parametrize("round_index", (1, 2))
@continue_assertions
def test_premium_cumulative_answer_does_not_acquire_quoted_revision_authority(round_index):
    request = begin()
    if round_index == 2:
        request = advance(request, "その時は重かった。")
    request = advance(request, _reported(_MARKERS[0]) + "その時は嬉しかった。")
    prepared = prepare_emlis_meaning(request)
    retained_assertion(lambda: (not prepared.checkpoint.inactive_claim_refs), 'not prepared.checkpoint.inactive_claim_refs')
    retained_assertion(lambda: (all(u.operation == "ADD" for u in prepared.checkpoint.answer_update.updates)), "all((u.operation == 'ADD' for u in prepared.checkpoint.answer_update.updates))")
    result = MeaningExperienceEngine().generate(request)
    retained_assertion(lambda: (result.artifact is not None), 'result.artifact is not None', lambda: (result.reason_codes))
    retained_assertion(lambda: (result.body_state == "PARTIALLY_REFINED" and result.question is None), "result.body_state == 'PARTIALLY_REFINED' and result.question is None")
    for original in ("褒められたのに嬉しくなかったこと", "誘われたのに悲しかったこと", "頼まれたのに寂しかったこと"):
        retained_assertion(lambda: (original in result.artifact.reception), 'original in result.artifact.reception')
    if round_index == 2:
        retained_assertion(lambda: ("その時の重さ" in result.artifact.reception), "'その時の重さ' in result.artifact.reception")
    retained_assertion(lambda: (request.emlis_thread.current_round == round_index), 'request.emlis_thread.current_round == round_index')
    retained_assertion(lambda: (request.emlis_thread.question_control_context.question_limit == 3), 'request.emlis_thread.question_control_context.question_limit == 3')


@continue_assertions
def test_body_inverse_rejects_loss_of_original_after_reported_meta():
    prepared = prepare_emlis_meaning(answered(_reported(_MARKERS[0]) + "その時は嬉しかった。"))
    _assert_original_reaction_retained(prepared)
    request, _ = prepared_request(answered(_reported(_MARKERS[0]) + "その時は嬉しかった。"))
    result = MeaningExperienceEngine().generate(request)
    retained_assertion(lambda: (result.artifact is not None), 'result.artifact is not None', lambda: (result.reason_codes))
    plan = build_updated_grounded_plan(prepared)
    resolver = prepared.thread.resolver()
    projection = project_thread_meaning(prepared, plan)
    sentence = surface.build_grounded_sentence_plan(plan, resolver, recovery_stage="full")
    def inverse(text):
        return evaluate_grounded_surface_body_inverse(body=text.encode(), plan=plan,
            sentence_plan=sentence, resolver=resolver, selected_subjective_input=projection.selected_reception)
    retained_assertion(lambda: (inverse(result.artifact.text).passed), 'inverse(result.artifact.text).passed')
    original_follow = "褒められたのに嬉しくなかったことを小さくせずに受け止めています。"
    retained_assertion(lambda: (original_follow in result.artifact.text), 'original_follow in result.artifact.text')
    corrupted = result.artifact.text.replace(original_follow, "")
    retained_assertion(lambda: (not inverse(corrupted).passed), 'not inverse(corrupted).passed')
