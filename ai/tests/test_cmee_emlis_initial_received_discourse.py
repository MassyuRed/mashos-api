"""Initial source-owned relations and later answers use one prose owner.

Public synthetic cases only. Existing literal expectations remain unchanged.
"""
from dataclasses import replace
import pytest
from cocolon_meaning_experience_engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.emlis_thread_contracts import EmlisQuestionControlV1
from test_cmee_emlis_q1_thread import initial, A
from test_cmee_emlis_q3_thread import begin, advance
from test_cmee_emlis_received_discourse import actual, inverse
from test_emlis_q3_application import qdb, qcase
from test_emlis_q2_application import run, answer


SINGLE = '褒められたのに、嬉しくなかった。'
MULTI = SINGLE + '誘われたのに、悲しかった。頼まれたのに、寂しかった。'


@pytest.mark.parametrize('memo', [SINGLE, '誘われたのに、悲しかった。',
    '頼まれたけど、寂しかった。', '言われたけれど、嬉しくなかった。'])
def test_initial_engine_receives_an_experience_not_a_placed_word(memo):
    req=initial(memo)
    result=MeaningExperienceEngine().generate(req)
    assert result.artifact is not None, result.reason_codes
    follow=result.artifact.reception
    assert '受け止めています' not in follow
    assert '今ここに置かれた言葉' not in follow
    assert 'のですね' in follow
    assert result.question is not None
    assert result.question.prompt_private not in result.artifact.text
    assert req.emlis_thread.current_round == 0 and not req.emlis_thread.answers
    assert not result.automatic_progression


@pytest.mark.parametrize('memo',[SINGLE,SINGLE+'誘われたのに、悲しかった。',MULTI])
@pytest.mark.parametrize('capability',['Q3_FREE','Q3_PLUS','Q3_PREMIUM'])
def test_grouped_application_initial_body_preserves_every_independent_pair(memo,capability):
    req=initial(memo)
    limit=3 if capability=='Q3_PREMIUM' else 1
    req=replace(req,emlis_thread=replace(req.emlis_thread,capability_snapshot=capability,
        question_control_context=EmlisQuestionControlV1(question_limit=limit)))
    result=MeaningExperienceEngine().generate(req)
    assert result.artifact is not None, result.reason_codes
    follow=result.artifact.reception
    assert follow.count('のですね')==1
    assert '受け止めています' not in follow and '今ここに置かれた言葉' not in follow
    for source,noun in [('褒められた','嬉しさ'),('誘われた','悲しさ'),('頼まれた','寂しさ')]:
        if source in memo:
            assert follow.count(source)==1 and noun in follow
    # One answer per issued question; Premium changes the thread's question budget.
    assert result.question is not None and result.question.answer_limit==1
    assert req.emlis_thread.question_control_context.question_limit==limit
    assert result.meaning_checkpoint is not None


@pytest.mark.parametrize('old,new',[
    ('嬉しさにはつながらなかった','嬉しさにつながった'),
    ('嬉しさにはつながらなかった','嬉しさにつなげられなかった'),
    ('嬉しさにはつながらなかった','嬉しさにはつながっていない'),
    ('嬉しさ','楽しさ'),('褒められたことは','友人が褒められたことは'),
    ('褒められたことは','今日も褒められたことは'),
    ('褒められたことは','褒められなかったことは'),
    ('褒められたことは、',''),
])
def test_initial_meaning_mutations_are_rejected_without_author_oracle(old,new):
    context=actual(request=initial(SINGLE))
    follow=context[0].artifact.reception
    changed=follow.replace(old,new)
    assert changed!=follow
    assert inverse(context,follow,without_author=True).passed
    assert not inverse(context,changed,without_author=True).passed


@pytest.mark.parametrize('old,new',[
    ('誘われたのに','誘われたので'),('悲しさ','嬉しさ'),
    ('悲しさを感じた','悲しさを感じ続けている'),('悲しさを感じた','悲しさを感じなかった'),
])
def test_affirmed_negative_feeling_keeps_contrast_and_past(old,new):
    context=actual(request=initial('誘われたのに、悲しかった。'))
    follow=context[0].artifact.reception;changed=follow.replace(old,new)
    assert changed!=follow and not inverse(context,changed,without_author=True).passed


@pytest.mark.parametrize('ending',['のです。','のだと受け取りました。'])
def test_initial_acknowledgement_is_not_fixed_author_spelling(ending):
    context=actual(request=initial(SINGLE))
    follow=context[0].artifact.reception.replace('のですね。',ending)
    assert inverse(context,follow).passed


@pytest.mark.parametrize('memo',[
    '友人が褒められたのに、嬉しくなかった。',
    '「褒められたのに、嬉しくなかった」と友人が言った。',
    '褒められたなら、嬉しくなかったかもしれない。',
    '褒められなかったのに、嬉しくなかった。',
    '褒められたのに、少しも嬉しくなかった。',
])
def test_unproved_actor_modality_and_qualified_feeling_are_not_rewritten(memo):
    result=MeaningExperienceEngine().generate(initial(memo))
    follow=result.artifact.reception if result.artifact else ''
    assert '褒められたことは、嬉しさにはつながらなかった' not in follow


@pytest.mark.parametrize('tier',['free','plus','premium'])
@pytest.mark.parametrize('memo',[SINGLE,SINGLE+'誘われたのに、悲しかった。',MULTI])
def test_initial_finite_prose_and_answer_are_saved_without_rerendering(qcase,qdb,monkeypatch,tier,memo):
    user,parent,service=qcase
    qdb.query('update public.profiles set subscription_tier=$2 where id=$1',[user,tier])
    qdb.query('update public.emotions set memo=$1 where id=$2',[memo,parent])
    first=run(service.start(user,parent))
    assert first['current_observation'] is not None,first
    text=first['current_observation']['text'].split('Emlisから：',1)[1]
    assert '受け止めています' not in text and text.count('のですね')==1
    assert first['issued_count']==1 and first['question_limit']==(3 if tier=='premium' else 1)
    for event in ('褒められた','誘われた','頼まれた'):
        if event in memo: assert text.count(event)==1
    assert run(service.get(user,parent))==first
    after=run(answer(service,user,first,A))
    assert after['current_observation'] is not None,after
    assert after['original']==first['original']
    assert after['body_state']=='REFINED'
    updated=after['current_observation']['text'].split('Emlisから：',1)[1]
    expected_answer='次も同じ成果を求められるような重さとして' + ('届いた' if memo==SINGLE else '届き、誘われた')
    assert expected_answer in updated
    for event in ('褒められた','誘われた','頼まれた'):
        if event in memo: assert updated.count(event)==1
    monkeypatch.setattr(service.engine,'generate',lambda *_:pytest.fail('saved text must not rerender'))
    assert run(service.get(user,parent))==after
    assert run(service.start(user,parent))==after


@pytest.mark.parametrize('old,new',[
    ('嬉しさにはつながらず','嬉しさにつながり'),
    ('誘われたのに、悲しさを感じ、',''),
    ('誘われたのに','誘われたので'),
    ('悲しさ','嬉しさ'),
    ('頼まれたのに','友人が頼まれたのに'),
    ('寂しさを感じた','寂しさを感じ続けている'),
])
def test_initial_group_inverse_keeps_all_pairs_without_an_author_oracle(old,new):
    context=actual(request=begin(MULTI))
    follow=context[0].artifact.reception;changed=follow.replace(old,new)
    assert changed!=follow
    assert inverse(context,follow,without_author=True).passed
    assert not inverse(context,changed,without_author=True).passed


@pytest.mark.parametrize('reply,withdraws,time',[
    ('その時は嬉しかった。',False,'その時に嬉しかった'),
    ('今は嬉しい。',False,'回答した時点で嬉しい'),
    ('「嬉しくなかった」は誤りです。',True,None),
    ('あの時も本当は嬉しかった。書き方を間違えた。',True,'その時に嬉しかった'),
])
def test_answer_time_and_original_correction_preserve_other_events(reply,withdraws,time):
    request=advance(begin(MULTI),reply)
    context=actual(request=request);follow=context[0].artifact.reception
    assert '誘われたのに、悲しさを感じ' in follow
    assert '頼まれたのに、寂しさを感じた' in follow
    assert ('嬉しさにはつながらず' in follow)==(not withdraws)
    if time is not None:assert time in follow
    assert inverse(context,follow,without_author=True).passed
    assert not inverse(context,follow.replace('悲しさ','楽しさ'),without_author=True).passed
