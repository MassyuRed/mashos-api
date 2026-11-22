"""Receive a selected subjective change without restarting its complete object.

Synthetic sources extend the public governed-change regression, not private
canonical cases. Original feeling, source owner and independent action stay.
"""
from functools import lru_cache
from types import SimpleNamespace

import pytest
import emlis_ai_grounded_human_reception as reception
import emlis_ai_grounded_observation_gate as gate
from test_emlis_cmee_body_inverse_protected import _final_stage1_artifacts

SOURCES = (
    '休憩したら、頭の切り替えができた感じ。',
    '作業を終えて、頭の切り替えができた感じ。',
    '少し休んで、頭の切り替えができた感じ。',
)
ACTION = '机の上を片づけた。'


@lru_cache(maxsize=None)
def artifacts(memo):
    return _final_stage1_artifacts(memo, memo_action=ACTION)


@pytest.mark.parametrize('memo', SOURCES)
def test_material_subjective_change_keeps_whole_source_and_one_governed_object(memo):
    plan, sentence, surface, resolver, selected = artifacts(memo)
    follow = surface.text.split('Emlisから：', 1)[1].strip()
    moves = plan.response_plan.human_reception_plan.moves
    nucleus = next(n for n in plan.nuclei if n.nucleus_id == moves[0].target_nucleus_ids[0])
    assert (nucleus.kind, nucleus.semantic_frame.predicate_kind,
            nucleus.semantic_frame.modality) == ('reaction', 'feeling', 'feeling')
    assert surface.recovery_stage == 'full'
    assert [(m.move_role, m.reception_act) for m in moves] == [
        ('attention', 'recognize_lived_change'), ('felt_response', 'honor_concrete_effort')]
    assert all(m.required for m in moves)
    assert follow == (memo.rstrip('。') + 'という変化を見過ごさず、受け止めています。'
                      + ACTION.rstrip('。') + 'ことを大切に思っています。')
    assert 'に表れた' not in follow and 'それを' not in follow
    assert gate.evaluate_grounded_surface_body_inverse(
        body=surface.text.encode(), plan=plan, sentence_plan=sentence,
        resolver=resolver, selected_subjective_input=selected).passed


@pytest.mark.parametrize('memo', SOURCES)
@pytest.mark.parametrize('mutation', (
    'drop_source', 'drop_subjective_ending', 'insert_actor', 'insert_time',
    'invent_cause', 'drop_attention', 'negate_attention', 'negate_reception',
    'replace_case', 'drop_action',
))
def test_independent_inverse_preserves_subjective_source_and_affirmative_reception(monkeypatch, memo, mutation):
    plan, sentence, surface, resolver, selected = artifacts(memo)
    follow = surface.text.split('Emlisから：', 1)[1].strip()

    def forbidden(*args, **kwargs):
        raise AssertionError('Body inverse must not re-run the author')

    monkeypatch.setattr(reception, '_author_source_grounded_reception_clauses', forbidden)

    def passes(text):
        monkeypatch.setattr(gate, 'replay_source_grounded_human_reception_from_plan',
                            lambda *a, **k: SimpleNamespace(text=text))
        return gate.evaluate_grounded_surface_body_inverse(
            body=surface.text.replace(follow, text).encode(), plan=plan,
            sentence_plan=sentence, resolver=resolver,
            selected_subjective_input=selected).passed

    assert passes(follow)
    source = memo.rstrip('。')
    before, after = {
        'drop_source': (source, '何かが変わった'),
        'drop_subjective_ending': ('できた感じ', 'できた'),
        'insert_actor': (source, '友人が' + source),
        'insert_time': (source, '先月は' + source),
        'invent_cause': (source, '褒められたので、' + source),
        'drop_attention': ('見過ごさず、', ''),
        'negate_attention': ('見過ごさず、', '見過ごして、'),
        'negate_reception': ('受け止めています', '受け止めていません'),
        'replace_case': ('という変化を見過ごさず、', 'という変化に見過ごさず、'),
        'drop_action': (ACTION.rstrip('。') + 'ことを大切に思っています。', ''),
    }[mutation]
    changed = follow.replace(before, after, 1)
    assert changed != follow
    assert not passes(changed)
