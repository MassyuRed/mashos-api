"""One complete current expression governs attention and material reception.

Only synthetic sources already represented by public regression fixtures are
used here. Selection, time, uncertainty and the separate action duty are kept.
"""
from functools import lru_cache
from types import SimpleNamespace

import pytest

import emlis_ai_grounded_human_reception as reception
import emlis_ai_grounded_observation_gate as gate
from test_emlis_cmee_body_inverse_protected import _final_stage1_artifacts
from test_cmee_emlis_q3_thread import MeaningExperienceEngine, begin, initial

SOURCES = (
    '準備を忘れた自分が情けない。',
    '私が頼りない。',
    'たぶん疲れている。',
    '昨日は準備を忘れた自分が情けなかった。',
)
ACTION = '何もしなかった。'


@lru_cache(maxsize=None)
def artifacts(memo):
    return _final_stage1_artifacts(memo, memo_action=ACTION)


@pytest.mark.parametrize('memo', SOURCES)
def test_complete_expression_has_one_case_and_keeps_both_reception_duties(memo):
    plan, sentence, surface, resolver, selected = artifacts(memo)
    follow = surface.text.split('Emlisから：', 1)[1].strip()
    moves = plan.response_plan.human_reception_plan.moves
    assert surface.recovery_stage == 'full'
    assert len(moves) == 2 and all(m.required for m in moves)
    assert [(m.move_role, m.reception_act) for m in moves] == [
        ('attention', 'stay_with_current_burden'),
        ('felt_response', 'stay_with_current_burden'),
    ]
    assert follow == (memo.rstrip('。') + 'という言葉を見過ごさず、小さくせずに受け止めています。'
                      + ACTION.rstrip('。') + 'という言葉を小さくせずに受け止めています。')
    inverse = gate.evaluate_grounded_surface_body_inverse(
        body=surface.text.encode(), plan=plan, sentence_plan=sentence,
        resolver=resolver, selected_subjective_input=selected,
    )
    assert inverse.passed, inverse.failure_codes


@pytest.mark.parametrize('memo', SOURCES)
@pytest.mark.parametrize('mutation', [
    'drop_source', 'insert_actor', 'insert_time', 'drop_attention',
    'negate_attention', 'drop_burden_guard', 'negate_reception', 'replace_case',
])
def test_independent_inverse_requires_whole_object_and_affirmative_duties(monkeypatch, memo, mutation):
    plan, sentence, surface, resolver, selected = artifacts(memo)
    follow = surface.text.split('Emlisから：', 1)[1].strip()

    def forbidden(*args, **kwargs):
        raise AssertionError('Independent body inverse must not re-run the author')

    monkeypatch.setattr(reception, '_author_source_grounded_reception_clauses', forbidden)

    def passes(text):
        # Neutralize author replay equality only; independent duties stay active.
        monkeypatch.setattr(gate, 'replay_source_grounded_human_reception_from_plan',
                            lambda *args, **kwargs: SimpleNamespace(text=text))
        return gate.evaluate_grounded_surface_body_inverse(
            body=surface.text.replace(follow, text).encode(), plan=plan,
            sentence_plan=sentence, resolver=resolver,
            selected_subjective_input=selected,
        ).passed

    assert passes(follow)
    source = memo.rstrip('。')
    before, after = {
        'drop_source': (source + 'という言葉', '今回の気持ち'),
        'insert_actor': (source, '友人の話では、' + source),
        'insert_time': (source, 'これまでは、' + source),
        'drop_attention': ('見過ごさず、', ''),
        'negate_attention': ('見過ごさず、', '見過ごして、'),
        'drop_burden_guard': ('小さくせずに受け止めています', '受け止めています'),
        'negate_reception': ('受け止めています', '受け止めていません'),
        'replace_case': ('という言葉を見過ごさず、', 'という言葉に見過ごさず、'),
    }[mutation]
    changed = follow.replace(before, after, 1)
    assert changed != follow
    assert not passes(changed)


@pytest.mark.parametrize('premium', [False, True])
@pytest.mark.parametrize('memo', SOURCES)
def test_initial_thread_keeps_existing_availability_and_input_limits(premium, memo):
    request = (begin if premium else initial)(memo, ACTION)
    original = request.current_input_bundle
    result = MeaningExperienceEngine().generate(request)
    assert request.current_input_bundle == original
    assert request.emlis_thread.question_control_context.question_limit == (3 if premium else 1)
    if premium and memo == 'たぶん疲れている。':
        # This public fixture is already unsupported by the unchanged Q3
        # limited-composition route. Do not turn a direct diagnostic body
        # into a claim that it was or is deliverable by Premium.
        assert result.artifact is None
        assert result.reason_codes == ('emlis_q3_initial_body_unavailable',)
    else:
        assert result.artifact, result.reason_codes
        assert result.artifact.reception == artifacts(memo)[2].text.split('Emlisから：', 1)[1].strip()


def test_polite_past_feeling_preserves_existing_typed_time_outside_whole_object():
    request = begin('頼まれたのに、寂しかった。', '怖かったです。')
    result = MeaningExperienceEngine().generate(request)
    assert result.artifact, result.reason_codes
    assert ('これまで、怖かったですという言葉を見過ごさず、小さくせずに受け止めています。'
            in result.artifact.reception)
    assert '頼まれたのに寂しかったこと' in result.artifact.reception
