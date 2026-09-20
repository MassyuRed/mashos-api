"""Synthetic coverage for selected performed-action attention references.

Reference policy may not erase an independent performed action merely because
another required Move is first. No new meaning, source, status or author.
"""

from helpers.retained_assertions import continue_assertions, retained_assertion
from dataclasses import replace
from types import SimpleNamespace
import pytest
import emlis_ai_grounded_human_reception as reception
import emlis_ai_grounded_observation_gate as gate
from emlis_ai_grounded_observation_plan import source_proven_performed_action_status
from test_emlis_cmee_body_inverse_protected import _final_stage1_artifacts
from test_cmee_emlis_q3_thread import begin, initial, advance, MeaningExperienceEngine

MEMOS = ('予定を聞かれると、少し不安だ。', '予定を聞かれると、少しつらい。')
ACTIONS = ('窓を閉めた。', '昨日は棚を拭いた。', '昨日は結論を決めず、条件を見てから連絡した。')

def artifacts(memo=MEMOS[0], action=ACTIONS[0]):
    plan, sentence, surface, resolver, selected = _final_stage1_artifacts(memo, memo_action=action)
    hr = plan.response_plan.human_reception_plan
    move = next(m for m in hr.moves if m.reception_act == 'honor_concrete_effort')
    target = next(n for n in plan.nuclei if n.nucleus_id == move.target_nucleus_ids[0])
    return plan, sentence, surface, resolver, selected, hr, move, target

@pytest.mark.parametrize('memo', MEMOS)
@pytest.mark.parametrize('action', ACTIONS)
def test_selected_attention_keeps_complete_performed_action_after_original_feeling(memo, action):
    plan, sentence, surface, resolver, selected, hr, move, target = artifacts(memo, action)
    body = surface.text.split('Emlisから：', 1)[1].strip()
    assert surface.recovery_stage == 'full'
    assert move.required and move.move_role == 'attention'
    assert move.reference_mode == 'short_anchor_if_ambiguous'
    assert source_proven_performed_action_status(target)
    assert target.source_fields == ('memo_action',)
    assert target.semantic_frame.actor == 'current_user'
    assert not move.support_nucleus_ids
    assert action.rstrip('。') + 'こと' in body
    assert memo.rstrip('。') in body
    assert body.index(memo.rstrip('。')) < body.index(action.rstrip('。'))
    assert '実際の行動に目が留まり、それを' not in body
    assert 'これからの行動' not in body
    checked = gate.evaluate_grounded_surface_body_inverse(body=surface.text.encode(), plan=plan,
        sentence_plan=sentence, resolver=resolver, selected_subjective_input=selected)
    assert checked.passed, checked.failure_codes

@pytest.mark.parametrize('mutation', ['erase', 'negation', 'actor', 'time', 'action'])
def test_independent_inverse_rejects_wrong_performed_action_without_reauthoring(monkeypatch, mutation):
    action = ACTIONS[2]
    plan, sentence, surface, resolver, selected, hr, move, target = artifacts(action=action)
    body = surface.text.split('Emlisから：', 1)[1].strip()
    def forbidden(*a, **kw):
        raise AssertionError('The independent inverse may not call the body author')
    monkeypatch.setattr(reception, '_author_source_grounded_reception_clauses', forbidden)
    def passes(follow):
        # Replay equality alone is disabled; the independently parsed inverse
        # must still reject every changed source-bound meaning below.
        monkeypatch.setattr(gate, 'replay_source_grounded_human_reception_from_plan',
                            lambda *a, **kw: SimpleNamespace(text=follow))
        return gate.evaluate_grounded_surface_body_inverse(
            body=surface.text.replace(body, follow).encode(), plan=plan,
            sentence_plan=sentence, resolver=resolver,
            selected_subjective_input=selected).passed
    assert passes(body)
    changed = {'erase': body.replace(action.rstrip('。') + 'こと', '実際の行動'),
               'negation': body.replace('決めず', '決めて'),
               'actor': body.replace('昨日は', '友人が昨日は'),
               'time': body.replace('昨日は', '明日は'),
               'action': body.replace('連絡した', '片付けた')}[mutation]
    assert changed != body
    assert not passes(changed)

@pytest.mark.parametrize('changes', [
    {'actor': 'other_person'}, {'time_scope': 'future'}, {'modality': 'intention'},
    {'modality': 'uncertain'}, {'attribute_codes': ('operator:action',)},
])
def test_existing_performed_nominal_does_not_borrow_changed_owner_or_unproved_status(changes):
    plan, sentence, surface, resolver, selected, hr, move, target = artifacts()
    assert reception.source_grounded_performed_action_nominal(move, {target.nucleus_id: target}, resolver)
    changed = replace(target, semantic_frame=replace(target.semantic_frame, **changes))
    assert not reception.source_grounded_performed_action_nominal(move, {changed.nucleus_id: changed}, resolver)

@pytest.mark.parametrize('premium', [False, True])
@pytest.mark.parametrize('action', ACTIONS[:2])
@continue_assertions
def test_unrelated_answer_retains_original_condition_and_concrete_action(premium, action):
    memo = '誘われたのに、悲しかった。' + MEMOS[0]
    req = (begin if premium else initial)(memo, action)
    original = req.current_input_bundle
    first = MeaningExperienceEngine().generate(req)
    retained_assertion(lambda: (first.artifact and first.question), 'first.artifact and first.question')
    retained_assertion(lambda: (MEMOS[0].rstrip('。') in first.artifact.reception), "MEMOS[0].rstrip('。') in first.artifact.reception")
    retained_assertion(lambda: (action.rstrip('。') in first.artifact.reception), "action.rstrip('。') in first.artifact.reception")
    req = advance(req, 'その時は重かった。')
    out = MeaningExperienceEngine().generate(req)
    retained_assertion(lambda: (out.artifact), 'out.artifact', lambda: (out.reason_codes))
    retained_assertion(lambda: (req.current_input_bundle == original), 'req.current_input_bundle == original')
    retained_assertion(lambda: (MEMOS[0].rstrip('。') in out.artifact.reception), "MEMOS[0].rstrip('。') in out.artifact.reception")
    retained_assertion(lambda: (action.rstrip('。') in out.artifact.reception), "action.rstrip('。') in out.artifact.reception")
    retained_assertion(lambda: ('その時の重さ' in out.artifact.reception), "'その時の重さ' in out.artifact.reception")
    retained_assertion(lambda: (req.emlis_thread.question_control_context.question_limit == (3 if premium else 1)), 'req.emlis_thread.question_control_context.question_limit == (3 if premium else 1)')

@pytest.mark.parametrize('operation,removed,new', [
    ('「重かった」ではなく「苦しかった」です。', 'その時の重さ', '苦しさ'),
    ('「重かった」は誤りです。', 'その時の重さ', None),
])
@continue_assertions
def test_unrelated_correction_and_withdrawal_keep_performed_action_and_condition(operation, removed, new):
    memo = '誘われたのに、悲しかった。頼まれたのに、寂しかった。' + MEMOS[0]
    req = begin(memo, ACTIONS[0])
    req = advance(advance(req, 'その時は重かった。'), operation)
    out = MeaningExperienceEngine().generate(req)
    retained_assertion(lambda: (out.artifact), 'out.artifact', lambda: (out.reason_codes))
    retained_assertion(lambda: (MEMOS[0].rstrip('。') in out.artifact.reception), "MEMOS[0].rstrip('。') in out.artifact.reception")
    retained_assertion(lambda: (ACTIONS[0].rstrip('。') in out.artifact.reception), "ACTIONS[0].rstrip('。') in out.artifact.reception")
    retained_assertion(lambda: ('頼まれたのに寂しかったこと' in out.artifact.reception), "'頼まれたのに寂しかったこと' in out.artifact.reception")
    retained_assertion(lambda: (removed not in out.artifact.reception), 'removed not in out.artifact.reception')
    if new:
        retained_assertion(lambda: (new in out.artifact.reception), 'new in out.artifact.reception')
