"""Read the live uncertainty and answer-owned standard through shared source duties.

Public synthetic examples only. Historical inputs and expectations are unchanged.
"""

from helpers.retained_assertions import continue_assertions, retained_assertion
from dataclasses import replace
from functools import lru_cache
from collections import Counter
import pytest
from cocolon_meaning_experience_engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning, build_updated_grounded_plan
from cocolon_meaning_experience_engine.emlis_thread_projection import project_thread_meaning
from cocolon_meaning_experience_engine.emlis_thread_contracts import EmlisQuestionControlV1
from test_cmee_emlis_q1_thread import initial, answered, prepared_request
from test_cmee_emlis_q3_thread import begin
from test_cmee_emlis_received_discourse import actual, inverse
from test_cmee_emlis_outcome_standard_question import MEMO, MATERIAL, APPRAISAL
from test_emlis_q3_application import qdb, qcase
from test_emlis_q2_application import run, answer

WISH = '続けたい気持ちはある'
UNKNOWN = 'この練習でいいか分からなくなった'
ACTION = '絵筆を洗った'
INPUT = WISH + '。でも' + UNKNOWN + '。'


def application(memo=INPUT, action=ACTION+'。', tier='premium'):
    req=initial(memo, action)
    return replace(req,emlis_thread=replace(req.emlis_thread,
        capability_snapshot='Q3_'+tier.upper(),
        question_control_context=EmlisQuestionControlV1(question_limit=3 if tier=='premium' else 1)))


@lru_cache(maxsize=32)
def focused(memo=INPUT, legacy=False):
    req=initial(memo,ACTION+'。') if legacy else application(memo)
    outer=MeaningExperienceEngine().generate(req)
    assert outer.artifact is not None,outer.reason_codes
    context=actual(request=req)
    assert context[0].artifact.text==outer.artifact.text
    return req,outer,context


@pytest.mark.parametrize('tier',['free','plus','premium'])
@pytest.mark.parametrize('matter',['この練習でいいか','この色でいいか','この順番でいいか'])
def test_initial_application_keeps_intention_and_locates_uncertainty_not_its_absence(tier,matter):
    req=application(WISH+'。でも'+matter+'分からなくなった。',tier=tier)
    before=req; out=MeaningExperienceEngine().generate(req)
    assert out.artifact is not None,out.reason_codes
    first=out.artifact.reception.split('。')[0]
    assert WISH in first and matter in first and '分からなくなったのは' in first
    assert '受け止め' not in first and '大切' not in first
    assert ACTION in out.artifact.reception
    assert out.question is None and not out.automatic_progression and req==before
    assert req.emlis_thread.question_control_context.question_limit==(3 if tier=='premium' else 1)
    prepared=prepare_emlis_meaning(req);plan=build_updated_grounded_plan(prepared)
    selection=project_thread_meaning(prepared,plan).selected_reception
    refs=[r for d in selection.decisions for r in d.selected_contribution_refs]
    assert refs and max(Counter(refs).values())==1
    assert set(refs)=={r for d in selection.decisions for r in d.subjective_proposition.target_contribution_refs}


@pytest.mark.parametrize('memo, retained, state',[
    (INPUT,WISH,'分からなくなった'),
    ('泳ぎたい。でも今の練習量でいいのか分からない。','泳ぎたい','分からない'),
    ('作品を見てもらえてうれしかった。でもこの色でよいのか迷っている。',
     '作品を見てもらえてうれしかった','迷っている'),
])
def test_legacy_outer_engine_uses_finite_focus_without_inventing_a_cause(memo,retained,state):
    out=MeaningExperienceEngine().generate(initial(memo,ACTION+"。"))
    assert out.artifact is not None,out.reason_codes
    first=out.artifact.reception.split('。')[0]
    assert retained in first and state+'のは' in first
    assert not any(x in first for x in ('本当は','だから','原因','受け止めています'))


@pytest.mark.parametrize('old,new',[
    ('続けたい気持ちはある','続けたい気持ちはない'),
    ('続けたい気持ちはある','友人には続けたい気持ちはある'),
    ('分からなくなったのは','分かっているのは'),
    ('分からなくなったのは','分からないのは'),
    ('この練習でいいか','練習したくないか'),
    ('一方で、','そのため、'),
    ('絵筆を洗った','絵筆を洗わなかった'),
])
def test_changed_meaning_is_rejected_without_using_author_as_oracle(old,new):
    _,out,context=focused(); before=out.artifact.reception;changed=before.replace(old,new)
    assert changed!=before
    assert inverse(context,before,without_author=True).passed
    assert not inverse(context,changed,without_author=True).passed


@pytest.mark.parametrize('wish',['休みたかった','本を読みたかった','手紙を書きたかった'])
@pytest.mark.parametrize('feedback',['そうです。','違います。'])
def test_explicit_answer_not_the_tentative_question_sets_the_reading(wish,feedback):
    req,cp=prepared_request(answered(feedback+wish+'。',initial(MEMO)))
    out=MeaningExperienceEngine().generate(req)
    assert out.artifact is not None,out.reason_codes
    follow=out.artifact.reception
    assert APPRAISAL in follow and wish in follow and '望みを起点に' in follow
    assert '一緒に見ていきたいです' in follow
    assert '受け止めています' not in follow and 'やりたかったことには手が届かなかった' not in out.artifact.text
    assert MATERIAL in out.artifact.observation
    assert inverse(actual(request=req),follow,without_author=True).passed
    assert cp.assessment_status=='RESOLVED'


@pytest.mark.parametrize('old,new',[
    ('休みたかった','休みたくなかった'),('休みたかった','休めた'),
    ('何一つできなかった','何一つできた'),
    ('望みを起点に、一緒に見ていきたいです','原因だと断定できます'),
])
def test_answer_standard_cannot_become_action_or_cause(old,new):
    req,_=prepared_request(answered('違います。休みたかった。',initial(MEMO)))
    context=actual(request=req);before=context[0].artifact.reception;changed=before.replace(old,new)
    assert changed!=before and not inverse(context,changed,without_author=True).passed


@pytest.mark.parametrize('reply',['はい。','違います。','分からない。'])
def test_bare_feedback_never_supplies_a_standard(reply):
    req,_=prepared_request(answered(reply,initial(MEMO)))
    out=MeaningExperienceEngine().generate(req)
    assert out.artifact is not None and out.body_state=='UNCHANGED'
    assert '望みを起点に' not in out.artifact.reception
    assert not prepare_emlis_meaning(req).accepted_nuclei


@pytest.mark.parametrize('tier',['free','plus','premium'])
def test_real_saved_initial_focus_is_retrieved_without_rerender(qcase,qdb,monkeypatch,tier):
    user,parent,s=qcase
    qdb.query('update public.profiles set subscription_tier=$2 where id=$1',[user,tier])
    qdb.query('update public.emotions set memo=$1,memo_action=$2 where id=$3',[INPUT,ACTION+'。',parent])
    dto=run(s.start(user,parent));assert dto['current_observation'] is not None,dto
    assert '分からなくなったのは、この練習でいいか' in dto['current_observation']['text']
    assert run(s.get(user,parent))==dto
    monkeypatch.setattr(s.engine,'generate',lambda *_:pytest.fail('saved text must not rerender'))
    assert run(s.start(user,parent))==dto
    assert run(s.get(user,parent))==dto


@pytest.mark.parametrize('tier',['free','plus','premium'])
@pytest.mark.parametrize('reply',['違います。休みたかった。','「何一つできなかった」は誤りです。'])
def test_saved_answer_and_withdrawal_preserve_unrelated_original(qcase,qdb,monkeypatch,tier,reply):
    user,parent,s=qcase
    qdb.query('update public.profiles set subscription_tier=$2 where id=$1',[user,tier])
    qdb.query('update public.emotions set memo=$1,memo_action=$2 where id=$3',[MEMO,'',parent])
    first=run(s.start(user,parent));assert first['pending_question'] is not None,first
    updated=run(answer(s,user,first,reply));assert updated['current_observation'] is not None,updated
    assert updated['original']==first['original']
    text=updated['current_observation']['text']
    assert MATERIAL in text
    if '誤り' in reply: assert APPRAISAL not in text
    else: assert '休みたかったという望みを起点に' in text
    assert run(s.get(user,parent))==updated
    monkeypatch.setattr(s.engine,'generate',lambda *_:pytest.fail('saved text must not rerender'))
    assert run(s.start(user,parent))==updated


@pytest.mark.parametrize('mutation',['duplicate','drop','swap'])
def test_shared_relation_partition_cannot_borrow_or_drop_another_duty(mutation):
    import emlis_ai_grounded_human_reception as hr
    import emlis_ai_grounded_sentence_surface as surface
    from cocolon_meaning_experience_engine.emlis_thread_surface import _bind_expression
    prepared=prepare_emlis_meaning(application())
    plan=build_updated_grounded_plan(prepared);projection=project_thread_meaning(prepared,plan)
    selected=projection.selected_reception;left,right=selected.decisions
    assert left.projected_claim_ref==right.projected_claim_ref
    assert set(left.selected_contribution_refs).isdisjoint(right.selected_contribution_refs)
    if mutation=='duplicate': refs=right.selected_contribution_refs
    elif mutation=='drop': refs=()
    else: refs=tuple(reversed(left.subjective_proposition.target_contribution_refs))
    wrong=hr.identify_selected_subjective_reception_decision(replace(left,decision_ref='',selected_contribution_refs=refs))
    altered=hr.identify_selected_subjective_reception_input(replace(selected,input_ref='',decisions=(wrong,right)))
    reception=plan.response_plan.human_reception_plan;resolver=prepared.thread.resolver()
    with pytest.raises(hr.GroundedHumanReceptionSurfaceError):
        expressions=tuple(_bind_expression(plan,resolver,replace(projection,selected_reception=altered),m,'FINITE') for m in reception.moves)
        sentence=surface.build_grounded_sentence_plan(plan,resolver,recovery_stage='full')
        clauses=next(l.reception_clause_plans for l in sentence.lines if l.binding.line_role=='human_follow')
        hr.realize_source_grounded_human_reception(reception,expressions,{n.nucleus_id:n for n in plan.nuclei},
            resolver,plan=plan,recovery_stage='full',clause_plans=clauses,selected_subjective_input=altered)


# Optional source-order hypotheses must not be promoted into an asserted
# background. These public scenarios exercise the existing application path;
# the relation graph, original source and mandatory duties remain available.
INDEPENDENT_SOURCES = (
    (INPUT, ACTION+'。', (WISH, UNKNOWN, ACTION)),
    ('作品を見てもらえてうれしかった。でもこの色でよいのか迷っている。',
     ACTION+'。', ('作品を見てもらえてうれしかった', 'この色でよいのか迷っている', ACTION)),
    ('話してみたら前より楽になった気がした。', '机を片づけた。',
     ('話してみたら前より楽になった気がした', '机を片づけた')),
    ('窓を開けたら気分が軽くなった。', '本を閉じた。',
     ('窓を開けたら気分が軽くなった', '本を閉じた')),
    ('予定が変わったので困った。でも待ち時間は嬉しかった。', ACTION+'。',
     ('予定が変わったので困った', '待ち時間は嬉しかった', ACTION)),
    ('泳ぎたい。', ACTION+'。', ('泳ぎたい', ACTION)),
    ('前より少し楽になった。', ACTION+'。', ('前より少し楽になった', ACTION)),
)


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
@pytest.mark.parametrize('memo,action,parts', INDEPENDENT_SOURCES)
def test_optional_adjacency_does_not_assert_background_or_displace_source(tier, memo, action, parts):
    req=application(memo, action, tier)
    original=req
    out=MeaningExperienceEngine().generate(req)
    assert out.artifact is not None, out.reason_codes
    assert all(part in out.artifact.text for part in parts)
    assert 'ことを背景に、' not in out.artifact.reception
    assert '気持ちを背景に、' not in out.artifact.reception
    assert req == original and not out.automatic_progression
    p=prepare_emlis_meaning(req); plan=build_updated_grounded_plan(p)
    hypotheses=tuple(r for r in plan.relations if r.grounding_kind=='bounded_structural_inference'
                     and r.retention=='should')
    assert hypotheses  # Retained as hypotheses, not deleted from meaning.
    moves=plan.response_plan.human_reception_plan.moves
    for move in moves:
        for target in move.target_nucleus_ids:
            for support in move.support_nucleus_ids:
                matching=[r for r in plan.relations
                          if {r.from_nucleus_id,r.to_nucleus_id}=={target,support}]
                assert not matching or any(r.retention=='required'
                    or r.grounding_kind!='bounded_structural_inference' for r in matching)
    selected=project_thread_meaning(p,plan).selected_reception
    refs=[r for d in selected.decisions for r in d.selected_contribution_refs]
    assert refs and max(Counter(refs).values())==1


@pytest.mark.parametrize('index', [0, 2, 3])
@pytest.mark.parametrize('change', ['invent_background','drop_action','change_actor','change_time','negate_reception'])
def test_independent_source_body_is_checked_without_rerender(index,change):
    memo, action, _=INDEPENDENT_SOURCES[index]
    context=actual(request=application(memo, action));follow=context[0].artifact.reception
    anchor=action.rstrip('。')
    assert anchor in follow and inverse(context,follow,without_author=True).passed
    if change=='invent_background':
        edited=anchor+'ことを背景に、'+follow
    elif change=='drop_action':
        edited='。'.join(s for s in follow.split('。') if anchor not in s)
    elif change=='change_actor':
        edited=follow.replace(anchor,'友人が'+anchor)
    elif change=='change_time':
        edited=follow.replace(anchor,'来月は'+anchor)
    else:
        edited=follow.replace('大切に思っています','大切に思っていません')
    assert edited!=follow
    assert not inverse(context,edited,without_author=True).passed


@pytest.mark.parametrize('premium', [False, True])
@continue_assertions
def test_required_source_relation_remains_in_the_existing_relation_author(premium):
    from test_cmee_emlis_shared_change_context import _actual, _independent_passes
    context=_actual(premium=premium)
    out,plan,*_=context
    source_relations=[r for r in plan.relations if r.retention=='required'
                      and r.type=='action_supports_change']
    retained_assertion(lambda: (source_relations), 'source_relations')
    follow=out.artifact.reception
    retained_assertion(lambda: ('ことが支えている、' in follow), "'ことが支えている、' in follow")
    retained_assertion(lambda: ('手元に緑がない寂しさも残っている' in follow), "'手元に緑がない寂しさも残っている' in follow")
    retained_assertion(lambda: ('まだ配置は見つかっていない' in follow), "'まだ配置は見つかっていない' in follow")
    retained_assertion(lambda: (_independent_passes(context, follow)), '_independent_passes(context, follow)')


@pytest.mark.parametrize('tier', ['free','plus','premium'])
@pytest.mark.parametrize('memo,action,parts', INDEPENDENT_SOURCES)
def test_saved_independent_sources_keep_meaning_without_inferred_background(qcase,qdb,monkeypatch,tier,memo,action,parts):
    user,parent,service=qcase
    qdb.query('update public.profiles set subscription_tier=$2 where id=$1',[user,tier])
    qdb.query('update public.emotions set memo=$1,memo_action=$2 where id=$3',[memo,action,parent])
    dto=run(service.start(user,parent))
    assert dto['current_observation'] is not None, dto
    text=dto['current_observation']['text']
    assert all(part in text for part in parts)
    follow=text.split('Emlisから：',1)[1]
    assert 'ことを背景に、' not in follow and '気持ちを背景に、' not in follow
    assert run(service.get(user,parent))==dto
    monkeypatch.setattr(service.engine,'generate',lambda *_:pytest.fail('saved sources were regenerated'))
    assert run(service.start(user,parent))==dto
    assert run(service.get(user,parent))==dto


@pytest.mark.parametrize('tier', ['free','plus','premium'])
@pytest.mark.parametrize('reply,required,absent', [
    ('次も同じ成果を求められるようで、重かった。','次も同じ成果',''),
    ('「嬉しくなかった」は誤りです。','褒められた','嬉しくなかった'),
    ('今は嬉しい。','回答した時点',''),
])
def test_saved_answer_and_withdrawal_keep_separate_action_and_source_time(qcase,qdb,monkeypatch,tier,reply,required,absent):
    user,parent,service=qcase
    qdb.query('update public.profiles set subscription_tier=$2 where id=$1',[user,tier])
    qdb.query('update public.emotions set memo=$1,memo_action=$2 where id=$3',
              ['褒められたのに、嬉しくなかった。',ACTION+'。',parent])
    first=run(service.start(user,parent))
    assert first['current_observation'] is not None and first['pending_question'] is not None
    after=run(answer(service,user,first,reply))
    assert after['current_observation'] is not None, after
    text=after['current_observation']['text']
    assert ACTION in text and required in text
    assert not absent or absent not in text
    assert after['original']==first['original']
    assert run(service.get(user,parent))==after
    monkeypatch.setattr(service.engine,'generate',lambda *_:pytest.fail('saved update was regenerated'))
    assert run(service.start(user,parent))==after
    assert run(service.get(user,parent))==after


CORRECTED_RECEPTIONS = (
    'あの時も本当は嬉しかった。書き方を間違えた。',
    '当時は嬉しかった。書き方を間違えた。',
    '「嬉しくなかった」は誤りです。本当は嬉しかった。',
)


def corrected_reception_request(reply=CORRECTED_RECEPTIONS[0], action=ACTION+'。', tier='free'):
    from test_cmee_emlis_q3_thread import advance
    return prepared_request(advance(application('褒められたのに、嬉しくなかった。', action, tier), reply))


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
@pytest.mark.parametrize('action', [ACTION+'。', '机を片づけた。', '本を読んだ。'])
@pytest.mark.parametrize('reply', CORRECTED_RECEPTIONS)
def test_corrected_reception_and_unrelated_action_own_distinct_complete_contributions(tier, action, reply):
    request, checkpoint = corrected_reception_request(reply, action, tier)
    before = request
    out = MeaningExperienceEngine().generate(request)
    assert out.artifact is not None, out.reason_codes
    assert out.body_state == 'REFINED' and checkpoint.assessment_status == 'RESOLVED'
    assert request == before and not out.automatic_progression
    text = out.artifact.text
    assert '褒められた' in text and '嬉しかった' in text and action.rstrip('。') in text
    assert '嬉しくなかった' not in text
    assert 'その時' in out.artifact.reception and 'ことを背景に、' not in out.artifact.reception
    prepared = prepare_emlis_meaning(request)
    plan = build_updated_grounded_plan(prepared)
    selected = project_thread_meaning(prepared, plan).selected_reception
    consumed = [ref for row in selected.decisions for ref in row.selected_contribution_refs]
    complete = {ref for row in selected.decisions for ref in row.subjective_proposition.target_contribution_refs}
    assert set(consumed) == complete and all(count == 1 for count in Counter(consumed).values())
    assert inverse(actual(request=request), out.artifact.reception, without_author=True).passed


@pytest.mark.parametrize('old,new', [
    ('褒められた', '叱られた'),
    ('嬉しかった', '嬉しくなかった'),
    ('その時に', '回答した時点では'),
    ('その時に', '友人がその時に'),
    ('絵筆を洗った', '絵筆を洗わなかった'),
    ('絵筆を洗った', '友人が絵筆を洗った'),
    ('絵筆を洗った', '来月は絵筆を洗った'),
    ('大切に思っています', '大切に思っていません'),
])
def test_corrected_reception_rejects_changed_event_feeling_time_and_unrelated_action(old, new):
    request, _ = corrected_reception_request()
    context = actual(request=request)
    assert context[0].artifact is not None
    follow = context[0].artifact.reception
    changed = follow.replace(old, new)
    assert changed != follow
    assert inverse(context, follow, without_author=True).passed
    assert not inverse(context, changed, without_author=True).passed


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
@pytest.mark.parametrize('reply', CORRECTED_RECEPTIONS)
def test_saved_corrected_reception_is_current_without_rewriting_original_or_rerender(qcase, qdb, monkeypatch, tier, reply):
    user, parent, service = qcase
    qdb.query('update public.profiles set subscription_tier=$2 where id=$1', [user, tier])
    qdb.query('update public.emotions set memo=$1,memo_action=$2 where id=$3',
              ['褒められたのに、嬉しくなかった。', ACTION+'。', parent])
    first = run(service.start(user, parent))
    assert first['current_observation'] is not None and first['pending_question'] is not None
    updated = run(answer(service, user, first, reply))
    assert updated['current_observation'] is not None, updated
    text = updated['current_observation']['text']
    assert '嬉しかった' in text and '嬉しくなかった' not in text
    assert '褒められた' in text and ACTION in text and 'その時' in text
    assert updated['original'] == first['original']
    assert run(service.get(user, parent)) == updated
    monkeypatch.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved correction was regenerated'))
    assert run(service.start(user, parent)) == updated
    assert run(service.get(user, parent)) == updated
