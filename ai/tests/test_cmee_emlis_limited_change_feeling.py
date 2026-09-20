"""Finite observations keep the complete past episode and independent material.

All inputs extend existing public synthetic examples. Historical expectations
and the shared echo-quality threshold remain unchanged.
"""
from dataclasses import replace
from unittest.mock import patch

import pytest

from test_cmee_emlis_q3_thread import ACTION_CHANGE_CONTRAST_MEMO, begin
from test_cmee_emlis_q1_thread import initial
from cocolon_meaning_experience_engine import MeaningExperienceEngine
from emlis_ai_grounded_observation_gate import evaluate_grounded_surface_body_inverse
import emlis_ai_grounded_sentence_surface as surface
import emlis_ai_grounded_observation_gate as gate


@pytest.mark.parametrize('q3', [False, True])
@pytest.mark.parametrize('action', ['', 'お茶を飲んだ。'])
@pytest.mark.parametrize('unfinished', ['', 'まだ配置は見つかっていない。'])
def test_original_initial_route_provides_a_body_without_relaxing_quality(q3, action, unfinished):
    result = MeaningExperienceEngine().generate(
        (begin if q3 else initial)(ACTION_CHANGE_CONTRAST_MEMO + unfinished, action))
    assert result.artifact is not None, result.reason_codes
    if not q3 and (action or unfinished):
        assert 'うれしかったのは、机の上が広くなったことなのですね。' in result.artifact.observation
        assert '窓辺の鉢を棚へ移したら、' in result.artifact.observation
        assert 'いつも見ていた葉が遠くなって、手元に緑がないという寂しさも残っている' in result.artifact.observation
    for separate in (action, unfinished):
        if separate:
            assert separate.rstrip('。') in result.artifact.observation


def _limited_context(memo=ACTION_CHANGE_CONTRAST_MEMO):
    observed = []
    def capture(**kwargs):
        verdict = evaluate_grounded_surface_body_inverse(**kwargs)
        if verdict.passed:
            observed.append(kwargs)
        return verdict
    with patch.object(gate, 'evaluate_grounded_surface_body_inverse', capture):
        result = MeaningExperienceEngine().generate(initial(
            memo + 'まだ配置は見つかっていない。', '明日、棚を動かす。'))
    assert result.artifact is not None, result.reason_codes
    assert 'ことなのですね。' in result.artifact.observation
    actual = next(row for row in reversed(observed)
                  if row['body'] == result.artifact.text.encode())
    assert actual['sentence_plan'].lines[0].binding.line_role == 'limited_scope'
    return result, actual['plan'], actual['sentence_plan'], actual['resolver'], actual['selected_subjective_input']


def _read(context, observation, plan_override=None):
    result, plan, sentence, resolver, selected = context
    with patch.object(surface, '_limited_action_change_feeling_sentences', side_effect=AssertionError('author')), \
         patch.object(surface, '_shared_observation_change_relation', side_effect=AssertionError('eligibility')), \
         patch.object(surface, '_render_final_stage1_limited_scope', side_effect=AssertionError('renderer')):
        return evaluate_grounded_surface_body_inverse(
            body=result.artifact.text.replace(result.artifact.observation, observation).encode(),
            plan=plan_override or plan, sentence_plan=sentence, resolver=resolver,
            selected_subjective_input=selected)


@pytest.mark.parametrize('memo', [
    ACTION_CHANGE_CONTRAST_MEMO,
    ACTION_CHANGE_CONTRAST_MEMO.replace('窓辺の鉢を棚', '窓際の鉢を台'),
    ACTION_CHANGE_CONTRAST_MEMO.replace('机の上が広く', '作業台の上が広く'),
    ACTION_CHANGE_CONTRAST_MEMO.replace('広くなってうれしかった', '思っていたより広くなってとてもうれしかった'),
    ACTION_CHANGE_CONTRAST_MEMO.replace('広くなってうれしかった', '明るくなって嬉しかった'),
])
def test_complete_source_episode_and_degree_survive_independent_reading(memo):
    context = _limited_context(memo)
    verdict = _read(context, context[0].artifact.observation)
    assert verdict.passed, verdict.failure_codes


@pytest.fixture(scope='module')
def context():
    return _limited_context()


@pytest.mark.parametrize('old,new', [
    ('移したら、', '移したから、'), ('移したら、', '移したあと、'),
    ('移したら、', '移さなかったら、'), ('うれしかったのは、', 'うれしいのは、'),
    ('うれしかったのは、', 'うれしくなかったのは、'), ('のは、', 'のも、'),
    ('広くなったこと', '広くなること'), ('机の上が広くなったこと', '広くなったこと'),
    ('うれしかったのは、', '弟がうれしかったのは、'),
    ('一方で、', 'なので、'), ('一方で、', 'その結果、'),
    ('いつも見ていた葉が遠くなって、', ''), ('寂しさも残っている', '寂しさは残っていない'),
    ('なって、', 'なったので、'), ('ないという寂しさ', 'あるという寂しさ'),
    ('ないという寂しさ', 'ないことでの寂しさ'),
    ('寂しさも残っている', '寂しさも残っていた'),
    ('まだ配置は見つかっていない', '配置は見つかった'),
    ('明日、棚を動かす', '今日、棚を動かした'),
    ('という、これからの行動', 'という行動'),
    ('ことなのですね。', 'ことなのですね。相手も喜んでいました。'),
])
def test_changed_actual_meaning_is_rejected_without_author(context, old, new):
    original = context[0].artifact.observation
    changed = original.replace(old, new, 1)
    assert changed != original
    assert not _read(context, changed).passed


@pytest.mark.parametrize('operation', ['remove_action', 'remove_burden', 'remove_unfinished',
                                     'remove_future', 'swap', 'duplicate', 'quote'])
def test_missing_reordered_or_quoted_clauses_do_not_count_as_finite_evidence(context, operation):
    original = context[0].artifact.observation
    rows = original.split('。')
    if operation == 'remove_action': rows[0] = rows[0].replace('窓辺の鉢を棚へ移したら、', '')
    elif operation == 'remove_burden': rows[1] = ''
    elif operation == 'remove_unfinished': rows = [r for r in rows if 'まだ配置' not in r]
    elif operation == 'remove_future': rows = [r for r in rows if '明日、棚' not in r]
    elif operation == 'swap': rows[0], rows[1] = rows[1], rows[0]
    elif operation == 'duplicate': rows.insert(1, rows[0])
    elif operation == 'quote': rows[0] = '「' + rows[0] + '」'
    changed = '。'.join(rows)
    assert changed != original
    assert not _read(context, changed).passed


@pytest.mark.parametrize('field,value', [('actor', 'other_person'), ('time_scope', 'future'),
                                       ('polarity', 'negative'), ('modality', 'possibility')])
def test_changed_source_scope_cannot_borrow_a_valid_finite_body(context, field, value):
    result, plan, sentence, resolver, selected = context
    support = next(r for r in plan.relations if r.type == 'action_supports_change'
                   and r.relation_id in sentence.lines[0].binding.relation_ids)
    assert getattr(next(n for n in plan.nuclei if n.nucleus_id == support.to_nucleus_id).semantic_frame, field) != value
    nuclei = tuple(replace(n, semantic_frame=replace(n.semantic_frame, **{field: value}))
                   if n.nucleus_id == support.to_nucleus_id else n for n in plan.nuclei)
    assert not _read(context, result.artifact.observation, replace(plan, nuclei=nuclei)).passed
