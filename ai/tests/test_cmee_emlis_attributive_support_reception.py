"""Direct support attribution in the existing relation author and inverse.

The scenarios extend the existing public synthetic plant fixture. No private
case or expectation is used. Historical full-text assertions remain intact.
"""
from dataclasses import replace
from unittest.mock import patch

import pytest

from test_cmee_emlis_shared_change_context import (
    _actual, _independent_passes, CONTINUATIONS,
)
import emlis_ai_grounded_human_reception as reception

BASE = CONTINUATIONS[0]
SCENARIOS = (
    BASE,
    BASE.replace('窓辺の鉢を棚へ移した', '机の本を本棚へ移した')
        .replace('机の上が広くなってうれしかった', '机の上が使いやすくなってうれしかった'),
    BASE.replace('窓辺の鉢を棚へ移した', '玄関の椅子を廊下へ移した')
        .replace('机の上が広くなってうれしかった', '玄関が広くなって気分は落ち着いた'),
    BASE.replace('机の上が広くなってうれしかった', '机の上が広くなって気分は落ち着いたように感じた'),
    BASE.replace('窓辺の鉢を棚へ移したら', '窓辺の鉢を棚へ移してみたら'),
)


@pytest.mark.parametrize('memo', SCENARIOS)
@pytest.mark.parametrize('premium', [False, True])
@pytest.mark.parametrize('ending', ['まだ配置は見つかっていない。', 'まだ配置は見つかっていません。'])
def test_support_is_attributed_without_three_nominal_layers(memo, premium, ending):
    context = _actual(memo, premium=premium, ending=ending)
    result, plan, *_ = context
    first, second, last, empty = result.artifact.reception.split('。')
    action, following = memo.split('ら、', 1)
    change = following.split('。', 1)[0]
    assert not empty
    assert first == (action + 'ことが支えている、' + change
        + 'という変化を見過ごさず、大切に思っています')
    assert 'ことを支えていること' not in first
    assert first.count('こと') == 1
    assert second.startswith('その一方で、')
    assert second.count(memo.split('一方で、', 1)[1].rstrip('。')) == 1
    assert last.startswith(ending.rstrip('。'))
    assert result.artifact.reception.count(change) == 1
    assert len(plan.response_plan.human_reception_plan.moves) == 3
    assert _independent_passes(context, result.artifact.reception)


@pytest.fixture
def subjective_support():
    return _actual(SCENARIOS[3])


@pytest.mark.parametrize('old,new', [
    ('窓辺の鉢を棚へ移したこと', 'その行動'),
    ('窓辺の鉢を棚へ移したこと', '弟が窓辺の鉢を棚へ移したこと'),
    ('移したこと', '移すこと'),
    ('移したこと', '移さなかったこと'),
    ('ことが支えている、', 'ことを支えている、'),
    ('ことが支えている、', 'ことが引き起こした、'),
    ('ことが支えている、', 'ことが必ず支えている、'),
    ('ことが支えている、', 'ことが支えていない、'),
    ('ことが支えている、', 'ことに支えられている、'),
    ('ことが支えている、', 'ことが支えていた、'),
    ('気分は落ち着いたように感じた', '気分は落ち着いた'),
    ('気分は落ち着いたように感じた', '気分は落ち着くように感じた'),
    ('という変化を見過ごさず、', 'という変化を'),
    ('大切に思っています', '大切には思っていません'),
    ('その一方で、', 'そのため、'),
    ('手元に緑がない寂しさも残っている', '手元に緑がない寂しさはなくなった'),
    ('まだ配置は見つかっていない', '配置は見つかった'),
])
def test_independent_inverse_rejects_actual_changed_relation_or_source(subjective_support, old, new):
    original = subjective_support[0].artifact.reception
    changed = original.replace(old, new, 1)
    assert changed != original
    assert not _independent_passes(subjective_support, changed)


@pytest.mark.parametrize('axis,value', [
    ('actor_kind', 'OTHER'), ('quoted_boundary', True),
    ('future_action', True), ('performed_action', False), ('modality', 'uncertain'),
])
def test_attribution_is_not_extended_to_unproven_action_profiles(axis, value):
    captured = []
    original = reception._source_grounded_argument_surface
    def capture(move, **kwargs):
        value_out = original(move, **kwargs)
        if (len(move.relations) == 1
            and move.relations[0].relation_kind == 'action_supports_change'):
            captured.append((move, kwargs, value_out))
        return value_out
    with patch.object(reception, '_source_grounded_argument_surface', side_effect=capture):
        _actual()
    assert captured
    move, kwargs, full = next(row for row in captured if 'ことが支えている、' in row[2][0])
    profiles = list(move.semantic_profiles)
    profiles[0] = replace(profiles[0], **{axis: value})
    changed = replace(move, semantic_profiles=tuple(profiles))
    # This isolates the existing grammar boundary, not an accepted forged plan.
    # End-to-end validation still requires the original source/projection.
    try:
        text, *_ = original(changed, **kwargs)
    except reception.GroundedHumanReceptionSurfaceError:
        return
    assert 'ことが支えている、' not in text


def test_existing_alternative_attention_case_remains_independently_readable():
    context = _actual(SCENARIOS[3].replace('ずっと見ていた', 'いつも見ていた'))
    follow = context[0].artifact.reception
    assert 'その一方で、' not in follow
    # Same object, source and act, using the already supported second attention
    # construction. This does not license arbitrary attention-word insertion.
    changed = follow.replace('という変化を見過ごさず、', 'という変化に目が留まり、それを', 1)
    assert changed != follow
    assert _independent_passes(context, changed)
    assert not _independent_passes(context, changed.replace('に目が留まり、それを', 'に目が留まり、', 1))
