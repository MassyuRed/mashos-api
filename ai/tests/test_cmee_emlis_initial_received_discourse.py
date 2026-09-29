"""Initial source-owned relations and later answers use one prose owner.

Public synthetic cases only. Preserve complete meaning and unproved boundaries.
"""

from helpers.retained_assertions import continue_assertions, retained_assertion
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


@pytest.mark.parametrize('left,link,right,left_time,right_time', [
    ('悲しかった', 'けど', '嬉しかった', 'past', 'past'),
    ('悲しい', 'けれど', '嬉しかった', 'current_input', 'past'),
    ('悲しかった', 'けれども', '嬉しい', 'past', 'current_input'),
    ('嬉しかった', 'けど', '悲しかった', 'past', 'past'),
    ('私も少し不安だった', 'けれど', '嬉しかった', 'past', 'past'),
    ('悲しかった', 'けど', '怖くなかった', 'past', 'past'),
    ('悲しかった', 'けど', '嬉しかったです', 'past', 'past'),
    ('悲しかった', 'けれど', '私には嬉しい', 'past', 'current_input'),
])
@pytest.mark.parametrize('capability', ['Q3_FREE', 'Q3_PLUS', 'Q3_PREMIUM'])
def test_finite_feeling_contrast_keeps_each_feeling_and_its_time(
        left, link, right, left_time, right_time, capability):
    from test_cmee_emlis_detached_observation import read_body
    req = begin(left + link + right + '。')
    req = replace(req, emlis_thread=replace(req.emlis_thread, capability_snapshot=capability,
        question_control_context=EmlisQuestionControlV1(question_limit=3 if capability == 'Q3_PREMIUM' else 1)))
    context = actual(request=req)
    result = MeaningExperienceEngine().generate(req)
    assert result.artifact is not None and result.artifact.text == context[0].artifact.text
    # A contrast states neither becoming nor simultaneous current feelings.
    body = result.artifact.text
    assert '変化' not in body and '同時' not in body and '今は' not in body
    assert '「' + left + '」' in body and '「' + right + '」' in body
    assert link + '、' in result.artifact.reception and 'のですね' in result.artifact.reception
    assert '今ここに置かれた言葉' not in body
    nuclei = {n.nucleus_id: n for n in context[1].nuclei}
    relation = next(r for r in context[1].relations if r.type == 'contrast')
    for nucleus_id, time in ((relation.from_nucleus_id, left_time), (relation.to_nucleus_id, right_time)):
        nucleus = nuclei[nucleus_id]
        assert (nucleus.kind, nucleus.semantic_frame.predicate_kind, nucleus.semantic_frame.time_scope) == (
            'reaction', 'feeling', time)
    assert result.question is None  # No event or new question target is invented.
    assert read_body(context, body).passed


@pytest.mark.parametrize('memo', [
    '友人は悲しかったけど嬉しかった。',
    '私は悲しかったけど友人は嬉しかった。',
    '「悲しかったけど嬉しかった」と言われた。',
    '悲しかったけど嬉しかったかもしれない。',
    '褒められたのに、悲しかったけど嬉しかった。',
])
def test_unproved_compound_feelings_are_not_promoted_to_self_finite_pair(memo):
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning, build_updated_grounded_plan
    req = begin(memo)
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    if memo == '褒められたのに、悲しかったけど嬉しかった。':
        # u13 proves this whole source, not an isolated inner feeling pair.
        # Keep the original parameter and require the event and both edges;
        # a marker alone or a two-feeling-only reception is insufficient.
        from test_cmee_emlis_detached_observation import read_body
        nodes = [n for n in plan.nuclei if n.source_fields == ('memo',)]
        assert len(nodes) == 3
        expected = (
            ('event', 'event', 'neutral', 'fact', 0, 5, '褒められた'),
            ('reaction', 'feeling', 'negative', 'feeling', 8, 13, '悲しかった'),
            ('reaction', 'feeling', 'positive', 'feeling', 15, 20, '嬉しかった'),
        )
        resolver = prepared.thread.resolver()
        for node, (kind, predicate, polarity, modality, start, end, fragment) in zip(nodes, expected):
            assert (node.kind, node.semantic_frame.predicate_kind,
                    node.semantic_frame.polarity, node.semantic_frame.modality) == (
                        kind, predicate, polarity, modality)
            assert (node.semantic_frame.actor, node.semantic_frame.time_scope,
                    node.grounding_kind, node.retention, node.allowed_claim_scope) == (
                        'current_user', 'past', 'explicit', 'required', 'explicit_current_input')
            assert len(node.source_span_ids) == 1 and node.source_span_ids == nodes[0].source_span_ids
            ranges = [code for code in node.semantic_frame.attribute_codes
                      if code.startswith('source_fragment_scalar_range:')]
            assert ranges == [f'source_fragment_scalar_range:{start}:{end}']
            raw = resolver.resolve(node.source_span_ids[0]).raw_text
            assert raw[start:end] == memo[start:end] == fragment
        assert [(r.type, r.from_nucleus_id, r.to_nucleus_id, r.grounding_kind,
                 r.source_span_ids) for r in plan.relations if r.retention == 'required'] == [
            ('contrast', nodes[0].nucleus_id, nodes[1].nucleus_id, 'user_stated_relation', nodes[0].source_span_ids),
            ('contrast', nodes[1].nucleus_id, nodes[2].nucleus_id, 'user_stated_relation', nodes[0].source_span_ids),
        ]
        result = MeaningExperienceEngine().generate(req)
        assert result.artifact is not None
        assert '「褒められた」のに「悲しかった」けど「嬉しかった」' in result.artifact.observation
        assert '褒められたのに、悲しかったけど、嬉しかった' in result.artifact.reception
        context = actual(request=req)
        body = result.artifact.text
        assert context[0].artifact.text == body and read_body(context, body).passed
        partial = body.replace(result.artifact.reception, '悲しかったけど、嬉しかったのですね。')
        assert partial != body and not read_body(context, partial).passed
        return
    assert not any('lexical:source_finite_contrast_feeling' in n.semantic_frame.attribute_codes for n in plan.nuclei)
    result = MeaningExperienceEngine().generate(req)
    assert result.artifact is None or '悲しかったけど、嬉しかったのですね' not in result.artifact.reception


@pytest.mark.parametrize('change', ['嬉しくなった', '不安になった', '落ち着いてきた'])
def test_explicit_change_does_not_acquire_finite_feeling_proof(change):
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning, build_updated_grounded_plan
    from emlis_ai_grounded_human_reception import final_reception_source_anchor_text
    req = begin('悲しかったけど' + change + '。')
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    index = {n.nucleus_id: n for n in plan.nuclei}
    changed = [n for n in plan.nuclei if change in final_reception_source_anchor_text(
        n.nucleus_id, index, prepared.thread.resolver())]
    assert changed
    assert all('lexical:source_finite_contrast_feeling' not in n.semantic_frame.attribute_codes for n in changed)


@pytest.mark.parametrize('old,new', [
    ('悲しいけれど', '悲しかったけれど'),
    ('嬉しかったのですね', '嬉しいのですね'),
    ('嬉しかったのですね', '嬉しくなったのですね'),
    ('けれど、', 'から、'), ('けれど、', 'けど、'),
    ('悲しいけれど、', ''),
    ('悲しいけれど、', '今は悲しいけれど、'),
    ('悲しいけれど、', '悲しいけれど、同時に'),
    ('「悲しい」', '「悲しかった」'),
    ('「嬉しかった」', '「嬉しい」'),
])
def test_contrast_tense_relation_and_no_added_change_are_read_from_actual_body(old, new):
    from test_cmee_emlis_detached_observation import read_body
    context = actual(request=begin('悲しいけれど嬉しかった。'))
    body = context[0].artifact.text
    changed = body.replace(old, new, 1)
    assert changed != body and read_body(context, body).passed
    assert not read_body(context, changed).passed


@pytest.mark.parametrize('old,new', [
    ('あなたも', 'あなたは'), ('あなたも', '友人も'),
    ('少し怖くなかった', '怖くなかった'),
    ('少し怖くなかった', '少し怖かった'),
    ('少し怖くなかった', '安心した'),
    ('少し怖くなかった', '少し怖くない'),
    ('あなたも少し怖くなかったけれど、嬉しかった',
     'あなたも怖くなかったけれど、少し嬉しかった'),
])
def test_contrast_owner_degree_and_negation_cannot_move_between_feelings(old, new):
    from test_cmee_emlis_detached_observation import read_body
    context = actual(request=begin('私も少し怖くなかったけれど嬉しかった。'))
    body = context[0].artifact.text
    changed = body.replace(old, new, 1)
    assert changed != body and read_body(context, body).passed
    assert not read_body(context, changed).passed


@pytest.mark.parametrize('link', ['が', 'けども'])
def test_other_existing_contrast_connectors_keep_fallback_and_local_times(link):
    from test_cmee_emlis_detached_observation import read_body
    context = actual(request=begin('悲しかった' + link + '嬉しかった。'))
    body = context[0].artifact.text
    assert '「悲しかった」' in body and '「嬉しかった」' in body
    assert '変化' not in body and '同時' not in body
    assert read_body(context, body).passed


@pytest.mark.parametrize('ending', ['のです。', 'のだと受け取りました。'])
def test_contrast_independent_reader_accepts_equivalent_acknowledgement(ending):
    from test_cmee_emlis_detached_observation import read_body
    context = actual(request=begin('悲しかったけど嬉しかった。'))
    body = context[0].artifact.text.replace('のですね。', ending)
    assert read_body(context, body).passed


@pytest.mark.parametrize('memo', ['不安だけど嬉しかった。', '悲しかったけど不安だ。',
                                 '不安だったけど悲しくなかった。', '悲しかったけど不安でした。'])
def test_contrast_copula_keeps_finite_first_and_acknowledged_final_clause(memo):
    from test_cmee_emlis_detached_observation import read_body
    context = actual(request=begin(memo))
    body = context[0].artifact.text
    assert 'のですね' in context[0].artifact.reception and '今ここに置かれた言葉' not in body
    assert read_body(context, body).passed
    if '不安だけど、' in body:
        assert not read_body(context, body.replace('不安だけど、', '不安なけど、')).passed


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
@continue_assertions
def test_answer_time_and_original_correction_preserve_other_events(reply,withdraws,time):
    request=advance(begin(MULTI),reply)
    context=actual(request=request);follow=context[0].artifact.reception
    retained_assertion(lambda: ('誘われたのに、悲しさを感じ' in follow), "'誘われたのに、悲しさを感じ' in follow")
    retained_assertion(lambda: ('頼まれたのに、寂しさを感じた' in follow), "'頼まれたのに、寂しさを感じた' in follow")
    retained_assertion(lambda: (('嬉しさにはつながらず' in follow)==(not withdraws)), "('嬉しさにはつながらず' in follow) == (not withdraws)")
    if time is not None:retained_assertion(lambda: (time in follow), 'time in follow')
    retained_assertion(lambda: (inverse(context,follow,without_author=True).passed), 'inverse(context, follow, without_author=True).passed')
    retained_assertion(lambda: (not inverse(context,follow.replace('悲しさ','楽しさ'),without_author=True).passed), "not inverse(context, follow.replace('悲しさ', '楽しさ'), without_author=True).passed")


OWNED_PAST = (
    '誘われたのに、私も少し不安だった。'
    '頼まれたのに、少し私は怖くなかった。'
    '言われたけど、僕には少し寂しかった。'
)


@pytest.mark.parametrize('source,finite', [
    ('私も少し不安だった', 'あなたも少し不安だった'),
    ('少し私は怖くなかった', 'あなたは少し怖くなかった'),
    ('僕には少し寂しかった', 'あなたには少し寂しかった'),
    ('少し不安だった', '少し不安だった'),
    ('私も少し不安でした', 'あなたも少し不安だった'),
    ('私は少し怖くなかったです', 'あなたは少し怖くなかった'),
    ('少し私は不安だった', 'あなたは少し不安だった'),
])
@pytest.mark.parametrize('capability', ['Q3_FREE', 'Q3_PLUS', 'Q3_PREMIUM'])
def test_owned_past_initial_body_keeps_complete_reaction(source, finite, capability):
    from test_cmee_emlis_detached_observation import read_body
    req = begin('誘われたのに、' + source + '。')
    req = replace(req, emlis_thread=replace(req.emlis_thread,
        capability_snapshot=capability,
        question_control_context=EmlisQuestionControlV1(
            question_limit=3 if capability == 'Q3_PREMIUM' else 1)))
    result = MeaningExperienceEngine().generate(req)
    assert result.artifact is not None, result.reason_codes
    assert '誘われたのに、' + finite + 'のですね。' in result.artifact.reception
    assert source in result.artifact.observation
    assert result.question is not None and not result.automatic_progression
    context = actual(request=req)
    assert read_body(context, result.artifact.text).passed


@pytest.mark.parametrize('old,new', [
    ('あなたも少し不安だった', 'あなたは少し不安だった'),
    ('あなたも少し不安だった', '少し不安だった'),
    ('あなたも少し不安だった', '友人も少し不安だった'),
    ('あなたも少し不安だった', 'あなたも不安だった'),
    ('あなたも少し不安だった', 'あなたも少し不安だ'),
    ('あなたは少し怖くなかった', 'あなたは少し怖かった'),
    ('あなたは少し怖くなかった', 'あなたは少し安心した'),
    ('誘われたのに', '誘われたので'),
    ('言われたけど', '言われたのに'),
    ('頼まれたのに、あなたは少し怖くなかったし、', ''),
    ('「私も少し不安だった」', '「私も不安だった」'),
    ('「少し私は怖くなかった」', '「少し私は怖くない」'),
])
def test_owned_past_initial_meaning_is_read_without_either_author(old, new):
    from test_cmee_emlis_detached_observation import read_body
    context = actual(request=begin(OWNED_PAST))
    body = context[0].artifact.text
    assert read_body(context, body).passed
    changed = body.replace(old, new, 1)
    assert changed != body
    assert not read_body(context, changed).passed


@pytest.mark.parametrize('memo', [
    '友人が誘われたのに、私も少し不安だった。',
    '誘われたのに、友人も少し不安だった。',
    '「誘われたのに、私も少し不安だった」と友人が言った。',
    '誘われたのに、私も少し不安だったらしい。',
    '誘われたなら、私も少し不安だったかもしれない。',
    '誘われなかったのに、私も少し不安だった。',
    '誘われたのに、私も少し不安だったと思う。',
    '誘われたのに、私も少し不安だったわけではない。',
    '誘われたのに、私も少し不安だ。',
    '誘われたのに、少し私は少し不安だった。',
    '誘われたのに、少しも怖くなかった。',
])
def test_owned_past_projection_does_not_promote_unproved_sources(memo):
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning, build_updated_grounded_plan
    plan = build_updated_grounded_plan(prepare_emlis_meaning(begin(memo)))
    assert not any(flag.startswith('source_received_event_link:')
                   for nucleus in plan.nuclei for flag in nucleus.semantic_frame.attribute_codes)


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
def test_owned_past_initial_and_answer_saved_body_reuse(qcase, qdb, monkeypatch, tier):
    user, parent, service = qcase
    qdb.query('update public.profiles set subscription_tier=$2 where id=$1', [user, tier])
    qdb.query('update public.emotions set memo=$1 where id=$2', [OWNED_PAST, parent])
    first = run(service.start(user, parent))
    follow = first['current_observation']['text'].split('Emlisから：', 1)[1]
    for text in ('誘われたのに、あなたも少し不安だった',
                 '頼まれたのに、あなたは少し怖くなかった',
                 '言われたけど、あなたには少し寂しかった'):
        assert text in follow
    after = run(answer(service, user, first, '今は少し苦しい。'))
    assert after['body_state'] == 'REFINED' and after['original'] == first['original']
    assert '回答した時点では少し苦しい' in after['current_observation']['text']
    monkeypatch.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved body must not regenerate'))
    assert run(service.get(user, parent)) == after
    assert run(service.start(user, parent)) == after


@pytest.mark.parametrize('memo,fragments,times', [
    ('褒められたのに、悲しいけれど嬉しかった。', ('褒められた', '悲しい', '嬉しかった'), ('past', 'current_input', 'past')),
    ('誘われたのに、悲しかったけど怖くなかった。', ('誘われた', '悲しかった', '怖くなかった'), ('past', 'past', 'past')),
    ('頼まれたけど、私も少し不安だったけれど嬉しかった。', ('頼まれた', '私も少し不安だった', '嬉しかった'), ('past', 'past', 'past')),
    ('評価されたけれど、嬉しかったけど悲しかった。', ('評価された', '嬉しかった', '悲しかった'), ('past', 'past', 'past')),
])
@pytest.mark.parametrize('capability', ['Q3_FREE', 'Q3_PLUS', 'Q3_PREMIUM'])
def test_received_feeling_chain_keeps_three_operands_and_two_source_edges(memo, fragments, times, capability):
    from test_cmee_emlis_detached_observation import read_body
    req = begin(memo)
    req = replace(req, emlis_thread=replace(req.emlis_thread, capability_snapshot=capability,
        question_control_context=EmlisQuestionControlV1(question_limit=3 if capability == 'Q3_PREMIUM' else 1)))
    context = actual(request=req)
    result = MeaningExperienceEngine().generate(req)
    assert result.artifact and result.artifact.text == context[0].artifact.text
    assert result.question is not None and not result.automatic_progression
    body = result.artifact.text
    assert all('「' + text + '」' in result.artifact.observation for text in fragments)
    assert '変化' not in body and '同時' not in body and '安心' not in body and '今は' not in body
    assert all(text.replace('私も', 'あなたも') in result.artifact.reception for text in fragments)
    nodes = [n for n in context[1].nuclei if 'semantic_dependency:received_feeling_contrast_chain' in n.semantic_frame.attribute_codes]
    assert len(nodes) == 3 and tuple(n.semantic_frame.time_scope for n in nodes) == times
    assert [(r.from_nucleus_id, r.to_nucleus_id) for r in context[1].relations if r.retention == 'required'] == [
        (nodes[0].nucleus_id, nodes[1].nucleus_id), (nodes[1].nucleus_id, nodes[2].nucleus_id)]
    assert read_body(context, body).passed


@pytest.mark.parametrize('old,new', [
    ('「頼まれた」けど', '「頼まれた」から'),
    ('「私も少し不安だった」けれど', '「私も少し不安だった」ので'),
    ('「私も少し不安だった」', '「私も不安だった」'),
    ('「嬉しかった」', '「嬉しい」'),
    ('頼まれたけど、', '頼まれたから、'),
    ('あなたも少し不安だった', 'あなたは少し不安だった'),
    ('あなたも少し不安だった', 'あなたも不安だった'),
    ('不安だったけれど、', '不安だったから、'),
    ('嬉しかったのですね', '嬉しくなかったのですね'),
    ('嬉しかったのですね', '嬉しいのですね'),
])
def test_received_feeling_chain_inverse_rejects_operand_and_edge_changes(old, new):
    from test_cmee_emlis_detached_observation import read_body
    context = actual(request=begin('頼まれたけど、私も少し不安だったけれど嬉しかった。'))
    body = context[0].artifact.text
    changed = body.replace(old, new, 1)
    assert changed != body and read_body(context, body).passed
    assert not read_body(context, changed).passed


@pytest.mark.parametrize('memo', [
    '友人が褒められたのに、悲しかったけど嬉しかった。',
    '褒められたのに、友人は悲しかったけど嬉しかった。',
    '「褒められたのに、悲しかったけど嬉しかった」と友人が言った。',
    '褒められたなら、悲しかったけど嬉しかったかもしれない。',
    '褒められたのに、悲しかったけど嬉しかったらしい。',
])
def test_received_feeling_chain_does_not_split_unproved_owners_or_modality(memo):
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning, build_updated_grounded_plan
    plan = build_updated_grounded_plan(prepare_emlis_meaning(begin(memo)))
    assert not any('semantic_dependency:received_feeling_contrast_chain' in n.semantic_frame.attribute_codes for n in plan.nuclei)


@pytest.mark.parametrize('old,new', [
    ('「褒められた」のに', ''),
    ('「悲しかった」けど', ''),
    ('けど「嬉しかった」', ''),
    ('「褒められた」のに', '「褒められた」から'),
    ('「悲しかった」けど', '「悲しかった」から'),
    ('「褒められた」のに「悲しかった」けど「嬉しかった」',
     '「褒められた」と「悲しかった」と「嬉しかった」'),
    ('褒められたのに、', ''),
    ('悲しかったけど、', ''),
    ('けど、嬉しかった', ''),
    ('褒められたのに、', '褒められたから、'),
    ('悲しかったけど、', '悲しかったから、'),
    ('悲しかったけど、', '悲しいけど、'),
    ('嬉しかったのですね', '嬉しくなかったのですね'),
    ('悲しかったけど、嬉しかった', '嬉しかったけど、悲しかった'),
])
def test_proved_chain_boundary_rejects_partial_or_changed_body(old, new):
    from test_cmee_emlis_detached_observation import read_body
    context = actual(request=begin('褒められたのに、悲しかったけど嬉しかった。'))
    body = context[0].artifact.text
    changed = body.replace(old, new, 1)
    assert changed != body and read_body(context, body).passed
    assert not read_body(context, changed).passed


@pytest.mark.parametrize('memo', [
    '褒められたのに、私は悲しかったけど友人は嬉しかった。',
    '褒められたのに、悲しかったけど嬉しかったかもしれない。',
    '褒められたのに、悲しかったけど「嬉しかった」と聞いた。',
    '褒められたのに、悲しかったけど嬉しくなった。',
])
def test_chain_boundary_does_not_prove_foreign_report_uncertainty_or_change(memo):
    from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning, build_updated_grounded_plan
    plan = build_updated_grounded_plan(prepare_emlis_meaning(begin(memo)))
    assert not any('semantic_dependency:received_feeling_contrast_chain' in n.semantic_frame.attribute_codes for n in plan.nuclei)
