"""Public synthetic past episodes retain their supplied time and connection."""
from dataclasses import replace
from functools import lru_cache
import pytest
from cocolon_meaning_experience_engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning, build_updated_grounded_plan
from emlis_ai_grounded_observation_plan import source_owned_action_change
from test_cmee_emlis_source_owned_focus import application
from test_cmee_emlis_received_discourse import actual, inverse
from test_emlis_q3_application import qdb, qcase
from test_emlis_q2_application import run

ACT = '机の書類を棚へ移した'
CHANGE = '机の上が広くなって気分が落ち着いた'
BURDEN = '手元に資料がない寂しさも残っている'
MEMO = ACT + 'ら、' + CHANGE + '。一方で、' + BURDEN + '。'


def request(tier='premium'):
    return application(MEMO, 'お茶を飲んだ。', tier=tier)


@lru_cache(maxsize=1)
def context():
    return actual(request=request())


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
def test_past_episode_keeps_its_connection_and_remaining_feeling(tier):
    req = request(tier)
    out = MeaningExperienceEngine().generate(req)
    assert out.artifact is not None, out.reason_codes
    assert ACT + 'ら、' + CHANGE + 'のですね。' in out.artifact.reception
    assert 'ことが支えている' not in out.artifact.reception
    assert BURDEN in out.artifact.reception
    assert out.question is None and not out.automatic_progression


@pytest.mark.parametrize('old,new', [
    ('ら、', 'ので、'), ('ら、', 'から、'),
    (ACT, '友人が' + ACT), (ACT, '昨日は' + ACT),
    (ACT, '机の書類を棚へ移している'), (ACT, '机の書類を棚へ移していない'),
    (CHANGE, '机の上が広くなって気分が落ち着かなかった'),
    (ACT + 'ら、' + CHANGE, CHANGE + 'ら、' + ACT),
    (ACT + 'ら、', ''), (CHANGE + 'のですね。', ''),
])
def test_independent_inverse_rejects_changed_actor_time_connection_and_missing_endpoints(old, new):
    ctx = context()
    body = ctx[0].artifact.reception
    assert inverse(ctx, body, without_author=True).passed
    changed = body.replace(old, new, 1)
    assert changed != body
    assert not inverse(ctx, changed, without_author=True).passed


@pytest.mark.parametrize('ending', ['のです。', 'のだと受け取りました。'])
def test_independent_inverse_reads_same_episode_without_literal_author_ending(ending):
    ctx = context()
    assert inverse(ctx, ctx[0].artifact.reception.replace('のですね。', ending, 1), without_author=True).passed


@pytest.mark.parametrize('field,value', [('actor', 'other'), ('time_scope', 'present'), ('modality', 'uncertain')])
def test_source_owned_view_cannot_promote_an_unproven_episode(field, value):
    prepared = prepare_emlis_meaning(request())
    plan = build_updated_grounded_plan(prepared)
    move = plan.response_plan.human_reception_plan.moves[0]
    assert source_owned_action_change(move, plan, prepared.thread.resolver())
    nid = move.target_nucleus_ids[0]
    nuclei = tuple(replace(n, semantic_frame=replace(n.semantic_frame, **{field:value})) if n.nucleus_id == nid else n for n in plan.nuclei)
    assert source_owned_action_change(move, replace(plan, nuclei=nuclei), prepared.thread.resolver()) is None


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
def test_actual_saved_terminal_episode_restarts_without_rerender(qcase, qdb, monkeypatch, tier):
    user, parent, service = qcase
    qdb.query('update public.profiles set subscription_tier=$2 where id=$1', [user,tier])
    qdb.query('update public.emotions set memo=$1,memo_action=$2 where id=$3', [MEMO,'お茶を飲んだ。',parent])
    first = run(service.start(user,parent))
    assert first['current_observation'] is not None
    assert ACT+'ら、'+CHANGE+'のですね。' in first['current_observation']['text']
    assert first['pending_question'] is None and first['body_state'] == 'FINAL'
    assert run(service.get(user,parent)) == first
    monkeypatch.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved content rerendered'))
    assert run(service.start(user,parent)) == first
    assert run(service.get(user,parent)) == first
