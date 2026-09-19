"""A source-owned memo response stays together before a separate action.

Public synthetic sources; existing corpus inputs and expectations are unchanged.
"""
from dataclasses import replace
from functools import lru_cache
from unittest.mock import patch
import pytest
from cocolon_meaning_experience_engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning, build_updated_grounded_plan
import emlis_ai_grounded_observation_plan as owner
from emlis_ai_grounded_human_reception import reception_active_moves
from test_cmee_emlis_source_owned_focus import application
from test_cmee_emlis_received_discourse import actual, inverse
from test_emlis_q3_application import qdb, qcase
from test_emlis_q2_application import run

BACKGROUND = 'すぐには返事をもらえず、待つ時間もあった'
FEELINGS = ('それでも話が終わった後、説明を聞いてもらえたことにほっとした',
            'それでも話が終わった後、提案を聞いてもらえたことにほっとした')
BURDEN = '不安が消えたわけではないけれど、別の方法もありそうだと思えた'
ACTION = '机を拭いた'


def memo(feeling=FEELINGS[0]):
    return '以前は予定を詰めることが多かった。今回の会議では、少し迷ったけれど自分の案を伝えた。' + BACKGROUND + '。' + feeling + '。' + BURDEN + '。'


def request(feeling=FEELINGS[0], tier='premium'):
    return application(memo(feeling), ACTION + '。', tier=tier)


@lru_cache(maxsize=2)
def context(feeling=FEELINGS[0]):
    return actual(request=request(feeling))


@pytest.mark.parametrize('feeling', FEELINGS)
def test_original_source_projection_preserves_the_same_complete_memo_order(feeling):
    req = replace(request(feeling), emlis_thread=None)
    out = MeaningExperienceEngine().generate(req)
    assert out.artifact is not None, out.reason_codes
    text = out.artifact.reception
    assert text.index(BURDEN) < text.index(BACKGROUND) < text.index(feeling) < text.index(ACTION)


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
@pytest.mark.parametrize('feeling', FEELINGS)
def test_primary_memo_and_its_feeling_relation_precede_independent_action(tier, feeling):
    req = request(feeling, tier)
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    hr = plan.response_plan.human_reception_plan
    assert tuple(m.move_id for m in hr.moves) == ('rm1', 'rm2', 'rm3')
    assert tuple(m.move_id for m in reception_active_moves(hr, 'full')) == ('rm1', 'rm3', 'rm2')
    with patch.object(owner, '_source_owned_memo_duties_before_action', return_value=False):
        before = build_updated_grounded_plan(prepared)
    assert plan.nuclei == before.nuclei and plan.relations == before.relations
    assert plan.coverage_requirements == before.coverage_requirements
    assert hr.target_nucleus_ids == before.response_plan.human_reception_plan.target_nucleus_ids
    assert hr.moves == before.response_plan.human_reception_plan.moves
    out = MeaningExperienceEngine().generate(req)
    assert out.artifact is not None, out.reason_codes
    text = out.artifact.reception
    assert text.index(BURDEN) < text.index(BACKGROUND) < text.index(feeling) < text.index(ACTION)
    assert out.question is None and not out.automatic_progression


@pytest.mark.parametrize('mutation', ['old_order', 'omit_feeling', 'omit_background', 'actor', 'time', 'negation', 'cause'])
def test_body_inverse_requires_complete_source_meanings_in_planned_order_without_author(mutation):
    ctx = context()
    text = ctx[0].artifact.reception
    assert inverse(ctx, text, without_author=True).passed
    sentences = [x + '。' for x in text.split('。') if x]
    if mutation == 'old_order':
        changed = sentences[0] + sentences[2] + sentences[1]
    elif mutation == 'omit_feeling':
        changed = sentences[0] + sentences[2]
    elif mutation == 'omit_background':
        changed = text.replace(BACKGROUND + 'けれど、', '')
    else:
        old, new = {'actor': ('説明を聞いてもらえた', '友人が説明を聞いてもらえた'),
                    'time': ('ほっとした', 'ほっとしている'),
                    'negation': ('ほっとした', 'ほっとしなかった'),
                    'cause': ('けれど、それでも', 'ので、そのため')}[mutation]
        changed = text.replace(old, new)
    assert changed != text
    assert not inverse(ctx, changed, without_author=True).passed


@pytest.mark.parametrize('mutation', ['actor', 'field', 'witness', 'missing_support', 'action_link', 'optional', 'role'])
def test_schedule_requires_existing_ownership_and_complete_independent_duties(mutation):
    plan = build_updated_grounded_plan(prepare_emlis_meaning(request()))
    moves, nuclei, relations = plan.response_plan.human_reception_plan.moves, plan.nuclei, plan.relations
    assert owner._source_owned_memo_duties_before_action(moves, nuclei, relations)
    feeling = next(m for m in moves if m.reception_act == 'recognize_lived_change')
    action = next(m for m in moves if m.reception_act == 'honor_concrete_effort')
    if mutation in {'actor', 'field', 'witness'}:
        def changed(n):
            if n.nucleus_id != feeling.target_nucleus_ids[0]: return n
            if mutation == 'field': return replace(n, source_fields=('answer_text_private',))
            frame = replace(n.semantic_frame, actor='other') if mutation == 'actor' else replace(n.semantic_frame, attribute_codes=tuple(c for c in n.semantic_frame.attribute_codes if c != 'lexical:source_bounded_expression'))
            return replace(n, semantic_frame=frame)
        nuclei = tuple(changed(n) for n in nuclei)
    elif mutation == 'missing_support':
        moves = tuple(replace(m, support_nucleus_ids=()) if m == feeling else m for m in moves)
    elif mutation == 'action_link':
        relation = next(r for r in relations if r.retention == 'required')
        relations = (*relations, replace(relation, relation_id='synthetic-action-link', from_nucleus_id=action.target_nucleus_ids[0]))
    else:
        moves = tuple(replace(m, **({'required': False} if mutation == 'optional' else {'move_role': 'significance'})) if m == action else m for m in moves)
    assert not owner._source_owned_memo_duties_before_action(moves, nuclei, relations)


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
@pytest.mark.parametrize('feeling', FEELINGS)
def test_saved_body_and_question_decision_survive_get_and_no_author_restart(qdb, qcase, monkeypatch, tier, feeling):
    user, parent, service = qcase
    qdb.query('update public.profiles set subscription_tier=$2 where id=$1', [user, tier])
    qdb.query('update public.emotions set memo=$1,memo_action=$2 where id=$3', [memo(feeling), ACTION + '。', parent])
    dto = run(service.start(user, parent))
    assert dto['current_observation'] is not None
    text = dto['current_observation']['text'].split('Emlisから：', 1)[1]
    assert text.index(BURDEN) < text.index(BACKGROUND) < text.index(feeling) < text.index(ACTION)
    assert dto['pending_question'] is None and dto['body_state'] == 'FINAL'
    assert run(service.get(user, parent)) == dto
    monkeypatch.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved content rerendered'))
    assert run(service.start(user, parent)) == dto
    assert run(service.get(user, parent)) == dto
