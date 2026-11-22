"""Explicit aims stay distinct from actual acts through the existing app path.

Public synthetic inputs only; inherited inputs and fixed prose are untouched.
"""
from dataclasses import replace
from functools import lru_cache
import pytest
from cocolon_meaning_experience_engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.emlis_thread_contracts import EmlisQuestionControlV1
from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning, build_updated_grounded_plan
from emlis_ai_grounded_observation_plan import GroundedSemanticRelation, source_owned_action_purpose
from test_cmee_emlis_q1_thread import initial
from test_cmee_emlis_q3_thread import advance
from test_cmee_emlis_received_discourse import actual, inverse
from test_emlis_q3_application import qdb, qcase
from test_emlis_q2_application import run, answer

MEMO = '褒められたのに、嬉しくなかった。'
ACTIONS = (
    ('手順を確かめる', '資料を読み直した'),
    ('伝える内容を整理する', 'メモを残した'),
    ('自分の考えを伝える', '手紙を書いた'),
)


def request(aim=ACTIONS[0][0], act=ACTIONS[0][1], tier='premium'):
    req = initial(MEMO, aim+'ために、'+act+'。')
    return replace(req, emlis_thread=replace(req.emlis_thread,
        capability_snapshot='Q3_'+tier.upper(),
        question_control_context=EmlisQuestionControlV1(question_limit=3 if tier=='premium' else 1)))


@lru_cache(maxsize=1)
def context():
    return actual(request=request())


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
@pytest.mark.parametrize('aim,act', ACTIONS)
def test_explicit_aim_not_generic_praise_is_the_focus(tier, aim, act):
    req = request(aim, act, tier)
    before = req
    out = MeaningExperienceEngine().generate(req)
    assert out.artifact is not None, out.reason_codes
    follow = out.artifact.reception
    assert act+'のは、'+aim+'ためなのですね' in follow
    assert follow.count(aim) == follow.count(act) == 1
    assert '大切に' not in follow and '見過ごさず' not in follow
    assert '嬉しさにはつながらなかった' in follow
    assert out.question is not None and req == before and not out.automatic_progression


@pytest.mark.parametrize('old,new', [
    ('資料を読み直した', '資料を読み直していない'),
    ('資料を読み直した', '資料を読み直す'),
    ('資料を読み直した', '友人が資料を読み直した'),
    ('資料を読み直した', '昨日は資料を読み直した'),
    ('手順を確かめる', '手順を確かめた'),
    ('手順を確かめる', '手順を確かめない'),
    ('手順を確かめる', '正解を確かめる'),
    ('ためなのですね', '結果なのですね'),
    ('ためなのですね', 'からなのですね'),
    ('資料を読み直したのは、手順を確かめる', '手順を確かめたのは、資料を読み直す'),
])
def test_actual_inverse_rejects_role_time_actor_and_result_mutations(old, new):
    ctx = context()
    follow = ctx[0].artifact.reception
    assert inverse(ctx, follow, without_author=True).passed
    changed = follow.replace(old, new)
    assert changed != follow and not inverse(ctx, changed, without_author=True).passed


@pytest.mark.parametrize('ending', ['なのです。', 'なのだと受け取りました。'])
def test_same_reading_does_not_require_literal_author_ending(ending):
    ctx = context()
    follow = ctx[0].artifact.reception.replace('ためなのですね。', 'ため'+ending)
    assert inverse(ctx, follow).passed


def test_purpose_sentence_cannot_bypass_required_context_without_the_author():
    ctx = actual(request=initial('', ACTIONS[0][0]+'ために、'+ACTIONS[0][1]+'。'))
    result, plan, sentence, resolver, selected = ctx
    follow = result.artifact.reception
    assert inverse(ctx, follow, without_author=True).passed
    move = plan.response_plan.human_reception_plan.moves[-1]
    context_nucleus = replace(plan.nuclei[0], nucleus_id='nucleus:required_context')
    relation = GroundedSemanticRelation(relation_id='relation:required_context', type='contrast',
        from_nucleus_id=move.target_nucleus_ids[0], to_nucleus_id=context_nucleus.nucleus_id,
        source_span_ids=move.source_evidence_span_ids, grounding_kind='user_stated_relation',
        certainty=0.86, retention='required')
    changed_plan = replace(plan, nuclei=(*plan.nuclei, context_nucleus), relations=(*plan.relations, relation),
        coverage_requirements=replace(plan.coverage_requirements,
            required_relation_ids=(*plan.coverage_requirements.required_relation_ids, relation.relation_id)))
    changed = (result, changed_plan, sentence, resolver, selected)
    assert not inverse(changed, follow, without_author=True).passed


@pytest.mark.parametrize('reply', ['その時は重かった。',
    'あの時も本当は嬉しかった。書き方を間違えた。',
    '「嬉しくなかった」は誤りです。', '今は嬉しい。'])
def test_answer_correction_withdrawal_and_now_keep_the_unrelated_original_purpose(reply):
    req = request()
    original = req.current_input_bundle
    updated = advance(req, reply)
    out = MeaningExperienceEngine().generate(updated)
    assert out.artifact is not None, out.reason_codes
    assert '資料を読み直したのは、手順を確かめるためなのですね' in out.artifact.reception
    assert updated.current_input_bundle == original
    if '誤り' in reply or '間違えた' in reply:
        assert '嬉しさにはつながらなかった' not in out.artifact.reception


@pytest.mark.parametrize('text', [
    '手順が違ったために、資料を読み直した。',
    '友人が手順を確かめるために、資料を読み直した。',
    '手順を確かめたために、資料を読み直した。',
    '手順を確かめるために、資料を読み直したかもしれない。',
    '手順を確かめるために、資料を読み直したい。',
    '手順を確かめるために、資料を読み直さなかった。',
    '「手順を確かめるために、資料を読み直した」と聞いた。',
    '手順を確かめるために、メモを残したと聞いた。',
    '手順を確かめるために、メモを残したと教わった。',
    '手順を確かめるために、メモを残したと伝えられた。',
    'かれは手順を確かめるために、メモを残した。',
    'かれが手順を確かめるために、メモを残した。',
    '手順を確かめるために、資料を読み直したら、安心した。',
    '次に話すときは、手順を伝えるため、メモを残した。',
])
def test_unsupported_purpose_is_not_promoted_from_a_source_label(text):
    prepared = prepare_emlis_meaning(initial(MEMO, text))
    plan = build_updated_grounded_plan(prepared)
    for nucleus in plan.nuclei:
        if nucleus.source_fields == ('memo_action',):
            assert source_owned_action_purpose(nucleus, prepared.thread.resolver()) is None


@pytest.mark.parametrize('tier', ['free','plus','premium'])
@pytest.mark.parametrize('reply', ['その時は重かった。',
    'あの時も本当は嬉しかった。書き方を間違えた。',
    '「嬉しくなかった」は誤りです。'])
def test_saved_application_preserves_purpose_after_each_update_and_restart(qcase, qdb, monkeypatch, tier, reply):
    user, parent, service = qcase
    qdb.query('update public.profiles set subscription_tier=$2 where id=$1', [user,tier])
    qdb.query('update public.emotions set memo=$1,memo_action=$2 where id=$3',
             [MEMO, ACTIONS[0][0]+'ために、'+ACTIONS[0][1]+'。', parent])
    first = run(service.start(user,parent))
    updated = run(answer(service,user,first,reply))
    for dto in (first, updated):
        assert dto['current_observation'] is not None, dto
        assert '資料を読み直したのは、手順を確かめるためなのですね' in dto['current_observation']['text']
    assert updated['original'] == first['original']
    assert run(service.get(user,parent)) == updated
    monkeypatch.setattr(service.engine, 'generate', lambda *_:pytest.fail('saved content rerendered'))
    assert run(service.start(user,parent)) == updated
    assert run(service.get(user,parent)) == updated
