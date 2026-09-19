"""Public synthetic appraisal/material cases; no private product-read inputs.

The initial engine must not drop an outcome appraisal merely because another
sentence has the same reception family. A non-cancelling stance preserves both
sources without inventing a personal goal, diagnosis, cause or extra question.
"""
from dataclasses import replace
from functools import lru_cache
from types import SimpleNamespace
from unittest.mock import patch

import pytest
import emlis_ai_grounded_human_reception as reception
import emlis_ai_grounded_observation_gate as gate
import emlis_ai_grounded_observation_plan as grounded
import emlis_ai_grounded_sentence_surface as surface
from cocolon_meaning_experience_engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning, build_updated_grounded_plan
from cocolon_meaning_experience_engine.emlis_thread_projection import project_thread_meaning
from cocolon_meaning_experience_engine.emlis_thread_surface import realize_emlis_thread_body
from test_cmee_emlis_q1_thread import initial

MATERIAL = '今日は散歩に出て帰っただけ'
APPRAISAL = '何一つできなかった'
MEMO = MATERIAL + '。' + APPRAISAL + '。'


@lru_cache(maxsize=8)
def context(memo=MEMO):
    prepared = prepare_emlis_meaning(initial(memo))
    plan = build_updated_grounded_plan(prepared)
    projected = project_thread_meaning(prepared, plan)
    result = realize_emlis_thread_body(prepared)
    assert result.artifact is not None, result.reason_codes
    resolver = prepared.thread.resolver()
    sentence = surface.build_grounded_sentence_plan(plan, resolver, recovery_stage='full')
    return result, plan, sentence, resolver, projected.selected_reception


def inverse(follow, without_author=False):
    result, plan, sentence, resolver, selected = context()
    body = result.artifact.text.replace(result.artifact.reception, follow)
    def evaluate():
        return gate.evaluate_grounded_surface_body_inverse(body=body.encode(), plan=plan,
            sentence_plan=sentence, resolver=resolver, selected_subjective_input=selected)
    if not without_author:
        return evaluate()
    with patch.object(gate, 'replay_source_grounded_human_reception_from_plan',
                      return_value=SimpleNamespace(text=follow)), patch.object(
            reception, '_author_source_grounded_reception_clauses', side_effect=AssertionError('not an oracle')):
        return evaluate()


@pytest.mark.parametrize('quantifier', ['何も', '何一つ', '何ひとつ', '一つも', 'ひとつも'])
@pytest.mark.parametrize('ending,scope', [('できなかった','past'), ('出来なかった','past'), ('できていない','current_input')])
def test_whole_zero_quantity_outcome_has_its_own_source_scope(quantifier, ending, scope):
    text = quantifier + ending
    proof = grounded._source_self_appraisal_parts(text)
    assert proof is not None and proof[0] == scope
    assert proof[1] == (('appraisal', 0, len(text)),)


@pytest.mark.parametrize('fragment', [
    '友人は何もできなかった', '彼女も何もできなかった', '何もできなかったら困る',
    '何もできなかったかもしれない', 'もし何もできなかったなら', '何もできなかったと思った',
    '「何もできなかった」と言われた', '何もできなかった？', '何もできなかった…',
    '何もできなかったわけではない', '何もできない自分が駄目だ', '昨日は何もできていない',
])
def test_another_speaker_negation_condition_and_qualifier_are_not_silent_appraisals(fragment):
    assert grounded._source_self_appraisal_parts(fragment) is None


@pytest.mark.parametrize('memo, appraisal, material', [
    (MEMO, APPRAISAL, MATERIAL),
    ('何もできなかった。今日は出かけただけ。', '何もできなかった', '今日は出かけただけ'),
    ('用事を済ませただけ。私も何もできなかった。', '私も何もできなかった', '用事を済ませただけ'),
])
def test_initial_engine_keeps_both_sources_and_does_not_use_material_to_deny_appraisal(memo, appraisal, material):
    request = initial(memo)
    before = request
    result = MeaningExperienceEngine().generate(request)
    assert result.artifact is not None, result.reason_codes
    follow = result.artifact.reception
    assert follow.count(appraisal) == follow.count(material) == 1
    assert follow.index(appraisal) < follow.index(material)
    assert '打ち消すことはしません' in follow
    assert '小さくせずに受け止めています' not in follow
    assert result.question is None and not result.automatic_progression
    assert request == before
    assert not any(word in follow for word in ('本当は', '進めたかった', '価値がない', 'うつ病'))


def test_initial_engine_is_deterministic_and_legacy_temporal_path_is_not_retyped_halfway():
    request = initial(MEMO)
    assert MeaningExperienceEngine().generate(request) == MeaningExperienceEngine().generate(request)
    other = initial('昨日は何もできなかった。書店に寄って戻っただけ。')
    result = MeaningExperienceEngine().generate(other)
    assert result.artifact is not None, result.reason_codes
    plan = build_updated_grounded_plan(prepare_emlis_meaning(other))
    assert not any('lexical:source_self_appraisal' in n.semantic_frame.attribute_codes for n in plan.nuclei)


def test_independent_inverse_reads_complete_clauses_without_author():
    result, plan, _, resolver, selected = context()
    follow = result.artifact.reception
    assert inverse(follow, without_author=True).passed
    clauses = follow.split('。')[:-1]
    moves = plan.response_plan.human_reception_plan.moves
    assert len(clauses) == len(moves) == 2
    for clause, move in zip(clauses, moves):
        assert gate.read_source_owned_discourse(clause+'。', move, plan, resolver, selected) is not None


@pytest.mark.parametrize('old,new', [
    ('何一つできなかった', '何一つできた'), ('何一つ', '少ししか'),
    ('今日は', '昨日は'), ('だけ', ''), ('打ち消すことはしません', '打ち消します'),
    ('先ほどの言葉', 'あなたの人格'), ('気になりました', '誤りだと分かりました'),
    ('今日は散歩に出て帰っただけ', '友人は散歩に出て帰っただけ'),
])
def test_semantic_mutations_fail_even_when_author_replay_is_not_an_oracle(old,new):
    follow = context()[0].artifact.reception
    changed = follow.replace(old,new)
    assert changed != follow
    assert not inverse(changed, without_author=True).passed


@pytest.mark.parametrize('mutation', ['drop_first','drop_second','reverse','invent_goal'])
def test_missing_reordered_and_invented_duties_fail(mutation):
    follow = context()[0].artifact.reception
    first,second = (part+'。' for part in follow.split('。')[:-1])
    changed = {'drop_first':second, 'drop_second':first, 'reverse':second+first,
        'invent_goal':follow+'本当は創作を進めたかったのですね。'}[mutation]
    assert not inverse(changed, without_author=True).passed


@pytest.mark.parametrize('old,new', [('が気になりました','に目が留まりました'), ('打ち消す','否定する')])
def test_equivalent_non_cancelling_words_are_not_rejected_by_literal_replay(old,new):
    follow = context()[0].artifact.reception
    changed = follow.replace(old,new)
    assert changed != follow
    assert inverse(changed).passed


@pytest.mark.parametrize('field,value', [('actor','third_party'), ('modality','fact'), ('polarity','positive')])
def test_reader_cannot_borrow_self_appraisal_proof_from_another_source_kind(field,value):
    result, plan, _, resolver, selected = context()
    move = plan.response_plan.human_reception_plan.moves[0]
    target = next(n for n in plan.nuclei if n.nucleus_id == move.target_nucleus_ids[0])
    changed = replace(target,semantic_frame=replace(target.semantic_frame,**{field:value}))
    invalid = replace(plan,nuclei=tuple(changed if n==target else n for n in plan.nuclei))
    clause = result.artifact.reception.split('。')[0]+'。'
    assert gate.read_source_owned_discourse(clause,move,invalid,resolver,selected) is None
