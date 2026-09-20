"""Synthetic source/activity and original-feeling retention regressions.

An omitted object is not a missing action; a source-order connection cannot
make an independent self-appraisal disappear. No evaluation input is copied.
"""
from types import SimpleNamespace
import pytest
import emlis_ai_grounded_human_reception as reception
import emlis_ai_grounded_observation_gate as gate
from emlis_ai_grounded_observation_plan import (
    _bounded_past_activity_finite, source_proven_performed_action_status,
)
from test_emlis_cmee_body_inverse_protected import _final_stage1_artifacts
from test_cmee_emlis_q3_thread import begin, initial, advance, MeaningExperienceEngine

MEMO = '準備を忘れた自分が情けない。'
ACTIONS = ('今日は三分だけ音読した。', 'それでも今朝は二分だけ体操しました。',
           'けれど昨日は十分ほど復習した。', 'それでも今日は内容を記録した。')

def nominal(action):
    clause = action.rstrip('。')
    return clause + ('という実際の行動' if clause.endswith('しました') else 'こと')

@pytest.mark.parametrize('noun', ['練習', '音読', '読書', '復習', '予習', '勉強', '運動', '体操', '散歩', '掃除'])
@pytest.mark.parametrize('form', ['した', 'しました'])
def test_activity_lexeme_requires_its_own_finite_past(noun, form):
    assert _bounded_past_activity_finite('それでも私は昨日は十分だけ' + noun + form)

@pytest.mark.parametrize('text', [
    '三分だけ安心した', '三分だけ失神した', '三分だけ骨折した',
    '友人が三分だけ音読した', '昨日は友人が三分だけ音読した',
    '友人の音読した', '明日は三分だけ音読した', '三分だけ音読する',
    '三分だけ音読したい', '三分だけ音読したかった', '三分だけ音読しなかった',
    '三分だけ音読しませんでした', '三分だけ音読したら', '三分だけ音読したので',
    '三分だけ音読したかもしれない', '三分だけ音読したらしい',
    '三分だけ音読してもらった', '三分だけ音読してくれた',
    '「三分だけ音読した」', '三分だけ音読したと言われた',
    '三分だけ音読したことにした', '三分だけ音読することにした',
    '三分だけ音読しようとした', '音読した。友人が掃除した',
])
def test_whole_activity_proof_rejects_different_owner_status_and_embedded_host(text):
    assert not _bounded_past_activity_finite(text)

@pytest.mark.parametrize('action', ACTIONS)
def test_original_self_appraisal_and_performed_activity_both_reach_follow(action):
    plan, sentence, surface, resolver, selected = _final_stage1_artifacts(MEMO, memo_action=action)
    assert surface.recovery_stage == 'full'
    target = next(n for n in plan.nuclei if n.source_fields == ('memo_action',))
    assert source_proven_performed_action_status(target)
    assert target.semantic_frame.time_scope == 'past'
    assert 'aspect:completed' not in target.semantic_frame.attribute_codes
    follow = surface.text.split('Emlisから：', 1)[1].strip()
    assert MEMO.rstrip('。') in follow
    assert nominal(action) in follow
    assert action.rstrip('。') + 'という言葉' not in follow
    assert follow.index(MEMO.rstrip('。')) < follow.index(action.rstrip('。'))
    assert gate.evaluate_grounded_surface_body_inverse(body=surface.text.encode(), plan=plan,
        sentence_plan=sentence, resolver=resolver, selected_subjective_input=selected).passed

@pytest.mark.parametrize('mutation', ['duration', 'actor', 'future', 'negation', 'appraisal', 'erase'])
def test_independent_inverse_rejects_losing_or_changing_source_meaning(monkeypatch, mutation):
    action = ACTIONS[1]
    plan, sentence, surface, resolver, selected = _final_stage1_artifacts(MEMO, memo_action=action)
    follow = surface.text.split('Emlisから：', 1)[1].strip()
    def forbidden(*args, **kwargs):
        raise AssertionError('Body inverse must not call the author')
    monkeypatch.setattr(reception, '_author_source_grounded_reception_clauses', forbidden)
    def passes(value):
        monkeypatch.setattr(gate, 'replay_source_grounded_human_reception_from_plan',
                            lambda *a, **kw: SimpleNamespace(text=value))
        return gate.evaluate_grounded_surface_body_inverse(
            body=surface.text.replace(follow, value).encode(), plan=plan, sentence_plan=sentence,
            resolver=resolver, selected_subjective_input=selected).passed
    assert passes(follow)
    changed = {'duration': follow.replace('二分', '十分'),
               'actor': follow.replace('今朝は', '友人が今朝は'),
               'future': follow.replace('今朝は', '明日は'),
               'negation': follow.replace('体操しました', '体操しませんでした'),
               'appraisal': follow.replace('情けない', '情けなかった'),
               'erase': follow.replace(nominal(action), 'その行動')}[mutation]
    assert changed != follow
    assert not passes(changed)

@pytest.mark.parametrize('premium', [False, True])
@pytest.mark.parametrize('action', ACTIONS[:2])
def test_answer_updates_keep_independent_appraisal_and_activity(premium, action):
    req = (begin if premium else initial)('誘われたのに、悲しかった。' + MEMO, action)
    original = req.current_input_bundle
    first = MeaningExperienceEngine().generate(req)
    assert first.artifact and first.question, first.reason_codes
    assert MEMO.rstrip('。') in first.artifact.reception
    assert action.rstrip('。') in first.artifact.reception
    req = advance(req, 'その時は重かった。')
    out = MeaningExperienceEngine().generate(req)
    assert out.artifact, out.reason_codes
    assert req.current_input_bundle == original
    assert MEMO.rstrip('。') in out.artifact.reception
    assert action.rstrip('。') in out.artifact.reception
    assert 'その時の重さ' in out.artifact.reception

@pytest.mark.parametrize('operation,removed,new', [
    ('「重かった」ではなく「苦しかった」です。', 'その時の重さ', '苦しさ'),
    ('「重かった」は誤りです。', 'その時の重さ', None),
])
def test_correction_and_withdrawal_do_not_erase_untouched_activity(operation, removed, new):
    action = ACTIONS[0]
    req = begin('誘われたのに、悲しかった。頼まれたのに、寂しかった。' + MEMO, action)
    req = advance(advance(req, 'その時は重かった。'), operation)
    out = MeaningExperienceEngine().generate(req)
    assert out.artifact, out.reason_codes
    assert MEMO.rstrip('。') in out.artifact.reception
    assert action.rstrip('。') in out.artifact.reception
    assert '頼まれたのに寂しかったこと' in out.artifact.reception
    assert removed not in out.artifact.reception
    if new:
        assert new in out.artifact.reception
