"""Source-owned relational responses, not expected-body/template equality.

Only public Q1/Q3 grammar inputs are used. Old snapshots stay unchanged.
"""

from helpers.retained_assertions import continue_assertions, retained_assertion
from types import SimpleNamespace
from unittest.mock import patch
import pytest
import emlis_ai_grounded_human_reception as reception
import emlis_ai_grounded_observation_gate as gate
import emlis_ai_grounded_sentence_surface as surface
from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning, build_updated_grounded_plan
from cocolon_meaning_experience_engine.emlis_thread_projection import project_thread_meaning
from cocolon_meaning_experience_engine.emlis_thread_surface import realize_emlis_thread_body
from test_cmee_emlis_q1_thread import A, B, C, initial, answered
from test_cmee_emlis_q3_thread import begin, advance
from test_emlis_q3_application import qdb, qcase
from test_emlis_q2_application import run, answer


OWNED_INITIAL = ('誘われたのに、私も少し不安だった。'
                 '頼まれたのに、少し私は怖くなかった。'
                 '言われたけど、僕には少し寂しかった。')


FEELING_CONTRAST_MEMO = '褒められたのに、嬉しくなかった。悲しかったけど嬉しかった。'


@pytest.mark.parametrize('reply,retained,removed', [
    ('今は少し苦しい。', ('悲しかった', '嬉しかった', '少し苦しい'), ()),
    ('「悲しかった」ではなく「少し怖かった」です。', ('少し怖かった', '嬉しかった'), ('悲しかった',)),
    ('「悲しかった」は誤りです。', ('嬉しかった',), ('悲しかった',)),
    ('「嬉しかった」は誤りです。', ('悲しかった',), ('嬉しかった',)),
])
def test_finite_contrast_correction_withdrawal_preserves_other_source(reply, retained, removed):
    from test_cmee_emlis_detached_observation import read_body
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    req = begin(FEELING_CONTRAST_MEMO)
    original = MeaningExperienceEngine().generate(req)
    context = actual(request=advance(req, reply))
    body = context[0].artifact.text
    assert all(text in body for text in retained)
    assert all(text not in body for text in removed)
    assert '今は、「嬉しかった」' not in body and '今は、「悲しかった」' not in body
    assert '変化' not in body
    assert '悲しかったけど、嬉しかったのですね' in original.artifact.reception
    # Updating another event does not attach this independent feeling pair to it.
    plan = context[1]
    index = {n.nucleus_id: n for n in plan.nuclei}
    for relation in plan.relations:
        if relation.type == 'evaluation_about_event':
            assert index[relation.to_nucleus_id].source_fields == ('answer_text_private',)
    assert read_body(context, body).passed


@pytest.mark.parametrize('reply,retained,removed', [
    ('今は少し苦しい。', ('悲しかった', '嬉しかった', '少し苦しい'), ()),
    ('「悲しかった」ではなく「少し怖かった」です。', ('少し怖かった', '嬉しかった'), ('悲しかった',)),
    ('「悲しかった」は誤りです。', ('嬉しかった',), ('悲しかった',)),
    ('「嬉しかった」は誤りです。', ('悲しかった',), ('嬉しかった',)),
])
def test_finite_contrast_saved_update_and_original_replay(qcase, qdb, monkeypatch, reply, retained, removed):
    user, parent, service = qcase
    qdb.query('update public.emotions set memo=$1 where id=$2', [FEELING_CONTRAST_MEMO, parent])
    first = run(service.start(user, parent))
    assert '悲しかったけど、嬉しかったのですね' in first['current_observation']['text']
    with monkeypatch.context() as saved:
        saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved initial body must not regenerate'))
        assert run(service.get(user, parent)) == first
        assert run(service.start(user, parent)) == first
    current = run(answer(service, user, first, reply, 'feeling-contrast-answer'))
    assert current['body_state'] == 'REFINED' and current['original'] == first['original']
    body = current['current_observation']['text']
    assert all(text in body for text in retained) and all(text not in body for text in removed)
    assert '今は、「嬉しかった」' not in body and '今は、「悲しかった」' not in body
    assert '今回の観測に反映できていない' not in body
    with monkeypatch.context() as saved:
        saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved revised body must not regenerate'))
        assert run(service.get(user, parent)) == current
        assert run(service.start(user, parent)) == current


@pytest.mark.parametrize('reply,correction,corrected,time', [
    ('今は少し苦しい。', '「少し苦しい」ではなく「少し怖い」です。', '少し怖い', '先の回答時点では'),
    ('その時は少し苦しかった。', '「少し苦しかった」ではなく「少し寂しかった」です。', '少し寂しかった', 'その時は'),
    ('今は私も少し不安です。', '「私も少し不安です」ではなく「私も少し苦しいです」です。', 'あなたも少し苦しい', '先の回答時点では'),
    ('今は嬉しい。', '「嬉しい」ではなく「少し楽しい」です。', '少し楽しい', '先の回答時点では'),
])
def test_owned_initial_answer_correction_and_event_withdrawal(reply, correction, corrected, time):
    from test_cmee_emlis_detached_observation import read_body
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    req = begin(OWNED_INITIAL)
    for index, text in enumerate((reply, correction, '「誘われた」は誤りです。')):
        req = advance(req, text)
        context = actual(request=req)
        body = context[0].artifact.text
        public = MeaningExperienceEngine().generate(req)
        assert public.artifact is not None and public.artifact.text == body
        assert '頼まれたのに、あなたは少し怖くなかった' in body
        assert '言われたけど、あなたには少し寂しかった' in body
        assert 'あなたも少し不安だった' in body
        if index:
            delivered_time = '先の回答時点で、' if index == 2 and corrected.startswith('あなた') else time
            assert delivered_time + corrected in body
        assert ('誘われた' in body) == (index != 2)
        assert read_body(context, body).passed


@pytest.mark.parametrize('time', ['今は', 'その時は'])
@pytest.mark.parametrize('memo', ['誘われたのに、私も少し不安だった。', OWNED_INITIAL])
def test_owned_initial_keeps_past_explanation_answer(time, memo):
    from test_cmee_emlis_detached_observation import read_body
    context = actual(request=advance(begin(memo), time + '私は不安なのだった。'))
    body = context[0].artifact.text
    assert '私は不安なのだった' in body
    assert 'あなたは不安な' in context[0].artifact.reception
    assert read_body(context, body).passed
    changed = body.replace('あなたは不安なのでしたね', 'あなたは不安なのですね').replace(
        'あなたは不安なのだったし', 'あなたは不安なのだし')
    assert changed != body and not read_body(context, changed).passed


@pytest.mark.parametrize('old,new', [
    ('回答した時点では少し苦しい', 'その時は少し苦しい'),
    ('回答した時点では少し苦しい', '先の回答時点では少し苦しい'),
    ('回答した時点では少し苦しい', '少し苦しい'),
    ('回答した時点では少し苦しい', '回答した時点では苦しい'),
    ('回答した時点では少し苦しい', '回答した時点では少し苦しかった'),
    ('あなたも少し不安だった', 'あなたも少し不安だ'),
    ('あなたも少し不安だった', 'あなたは少し不安だった'),
    ('誘われたのに', '誘われたから'),
    ('し、回答した時点では少し苦しい', ''),
])
def test_owned_initial_about_meaning_cannot_be_donated_by_another_layer(old, new):
    from test_cmee_emlis_detached_observation import read_body
    context = actual(request=advance(begin(OWNED_INITIAL), '今は少し苦しい。'))
    body = context[0].artifact.text
    assert read_body(context, body).passed
    changed = body.replace(old, new, 1)
    assert changed != body and not read_body(context, changed).passed


@pytest.mark.parametrize('polite', [False, True])
def test_owned_initial_original_revision_and_withdrawal(polite):
    from test_cmee_emlis_detached_observation import read_body
    source = '私は少し怖くなかったです' if polite else '私も少し不安だった'
    memo = '誘われたのに、' + source + '。頼まれたのに、私も少し不安でした。'
    for reply in ('「' + source + '」ではなく「少し苦しかった」です。', '「誘われた」は誤りです。'):
        context = actual(request=advance(begin(memo), reply))
        body = context[0].artifact.text
        assert '頼まれたのに、あなたも少し不安だった' in body
        if 'ではなく' in reply:
            assert source not in body and '少し苦しかった' in body
        else:
            assert '誘われた' not in body and source in body
            assert 'という言葉' not in context[0].artifact.reception
        assert read_body(context, body).passed


@pytest.mark.parametrize('sequence', [
    ('今は私も少し不安です。', '「私も少し不安です」ではなく「私も少し苦しいです」です。', '「誘われた」は誤りです。'),
    ('今は嬉しい。', '「嬉しい」ではなく「少し楽しい」です。', '「少し楽しい」は誤りです。'),
    ('「私も少し不安だった」ではなく「少し苦しかった」です。', '今は嬉しい。', '「頼まれた」は誤りです。'),
])
def test_owned_initial_saved_corrections_withdrawals_reuse_exact_body(qcase, qdb, monkeypatch, sequence):
    from test_emlis_q3_application import cont
    user, parent, service = qcase
    qdb.query('update public.emotions set memo=$1 where id=$2', [OWNED_INITIAL, parent])
    first = current = run(service.start(user, parent))
    for index, text in enumerate(sequence):
        if index:
            current = run(cont(service, user, current, f'owned-continue-{index}'))
        current = run(answer(service, user, current, text, f'owned-answer-{index}'))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        body = current['current_observation']['text']
        assert '言われたけど、あなたには少し寂しかった' in body
        assert '今回の観測に反映できていない' not in body
        if index == 2:
            if text == '「誘われた」は誤りです。':
                assert '誘われた' not in body and '先の回答時点で、あなたも少し苦しい' in body
            elif text == '「頼まれた」は誤りです。':
                assert '頼まれた' not in body and '少し苦しかった' in body
            else:
                assert '少し楽しい' not in body and '誘われたのに、あなたも少し不安だった' in body
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved body must not regenerate'))
            assert run(service.get(user, parent)) == current
            assert run(service.start(user, parent)) == current


def actual(text=A, request=None):
    prepared = prepare_emlis_meaning(request or answered(text))
    plan = build_updated_grounded_plan(prepared)
    projection = project_thread_meaning(prepared, plan)
    result = realize_emlis_thread_body(prepared)
    assert result.artifact is not None, result
    resolver = prepared.thread.resolver()
    sentence = surface.build_grounded_sentence_plan(plan, resolver, recovery_stage='full')
    return result, plan, sentence, resolver, projection.selected_reception


def inverse(context, follow, *, without_author=False):
    result, plan, sentence, resolver, selected = context
    body = result.artifact.text.replace(result.artifact.reception, follow)
    def evaluate():
        return gate.evaluate_grounded_surface_body_inverse(body=body.encode(), plan=plan,
            sentence_plan=sentence, resolver=resolver, selected_subjective_input=selected)
    if not without_author:
        return evaluate()
    with patch.object(gate, 'replay_source_grounded_human_reception_from_plan',
                      return_value=SimpleNamespace(text=follow)), patch.object(
            reception, '_author_source_grounded_reception_clauses', side_effect=AssertionError('author is not an oracle')):
        return evaluate()


@pytest.mark.parametrize('memo', [
    '褒められたのに、嬉しくなかった。',
    '誘われたのに、悲しかった。',
    '頼まれたのに、寂しかった。',
])
@pytest.mark.parametrize('text', [A, B, C,
    '次も説明を求められるようで、苦しかった。', 'その時は重かった。'])
def test_relations_form_a_response_without_generic_reception_objects(memo, text):
    context = actual(request=answered(text, initial(memo)))
    result, plan, _, resolver, selected = context
    follow = result.artifact.reception
    for forbidden in ('受け止めています', '大切に思っています', 'どちらの側も残したまま', 'その出来事への'):
        assert forbidden not in follow
    moves = plan.response_plan.human_reception_plan.moves
    assert len(moves) == 1
    assert gate.read_received_discourse(follow, moves[0], plan, resolver, selected) is not None
    assert inverse(context, follow, without_author=True).passed
    assert follow.count('のですね') == 1


@pytest.mark.parametrize('ending', ['のです。', 'のだと受け取りました。'])
def test_semantically_identical_acknowledgements_are_not_fixed_to_author_text(ending):
    context = actual()
    before = context[0].artifact.reception
    changed = before.replace('のですね。', ending)
    assert changed != before
    # Canonical replay remains enabled; spelling inequality alone cannot
    # reject an independently verified reading of the same source meaning.
    assert inverse(context, changed).passed


@pytest.mark.parametrize('old,new', [
    ('嬉しさにはつながらず', '嬉しさにつながり'), ('嬉しさにはつながらず、', ''),
    ('次も', ''), ('同じ', ''), ('求められるような', '求められるための'),
    ('重さ', '軽さ'), ('重さ', '苦しさ'), ('届いた', '届いている'),
    ('褒められたことは', '友人が褒められたことは'), ('褒められたことは', '今、褒められたことは'),
    ('求められるような', '求められないような'),
])
def test_complete_semantic_mutations_fail_without_author_replay(old, new):
    context = actual(); follow = context[0].artifact.reception
    changed = follow.replace(old, new)
    assert changed != follow
    result = inverse(context, changed, without_author=True)
    assert not result.passed, result


@pytest.mark.parametrize('text,old,new', [
    (B, '見てもらえていない', '見てもらえている'), (B, 'と思った', 'と分かった'), (B, 'だけ', ''),
    (C, '嫌なのではなく', '嫌なので'), (C, '自分では', '相手は'), (C, 'まだ', ''),
])
def test_belief_negation_and_noncausal_boundary_survive(text, old, new):
    context=actual(text); follow=context[0].artifact.reception
    changed=follow.replace(old,new)
    assert changed!=follow and not inverse(context,changed,without_author=True).passed


@pytest.mark.parametrize('sequence', [(A,), (A,B), (A,B,'その時は苦しかった。')])
def test_unasked_originals_and_separate_answers_keep_their_own_events(sequence):
    request=begin()
    for text in sequence:
        request=advance(request,text)
    context=actual(request=request)
    result,plan,_,resolver,selected=context
    follow=result.artifact.reception
    assert follow.count('のですね') == 1
    assert '受け止めています' not in follow
    for event in ('褒められた','誘われた','頼まれた'):
        assert follow.count(event)==1
    assert gate.read_received_discourse(follow,plan.response_plan.human_reception_plan.moves[0],
        plan,resolver,selected) is not None
    assert inverse(context,follow,without_author=True).passed
    for original in ('誘われた','頼まれた'):
        assert not inverse(context,follow.replace(original,'別の出来事'),without_author=True).passed


@pytest.mark.parametrize('correction', ['「重かった」ではなく「苦しかった」です。','「重かった」は誤りです。'])
def test_correction_and_withdrawal_do_not_restore_old_answer(correction):
    request=advance(advance(advance(begin(),'その時は重かった。'),'その時は怖かった。'),correction)
    context=actual(request=request)
    follow=context[0].artifact.reception
    assert '重かった' not in follow and '重さ' not in follow
    assert '怖' in follow
    assert inverse(context,follow).passed


@pytest.mark.parametrize('text',[A,B,C])
def test_finite_response_is_saved_and_retrieved_without_rerendering(qcase,qdb,text,monkeypatch):
    user,parent,service=qcase
    qdb.query('update public.emotions set memo=$1 where id=$2', ['褒められたのに、嬉しくなかった。',parent])
    first=run(service.start(user,parent))
    current=run(answer(service,user,first,text))
    assert current['current_observation'] is not None
    assert '受け止めています' not in current['current_observation']['text'].split('Emlisから：',1)[1]
    assert current['original']==first['original']
    monkeypatch.setattr(service.engine,'generate',lambda *_:pytest.fail('GET must not regenerate'))
    assert run(service.get(user,parent))==current
    assert run(service.start(user,parent))==current


@pytest.mark.parametrize('memo', [
    '褒められたのに、嬉しくなかった。',
    '誘われたのに、悲しかった。',
    '頼まれたのに、寂しかった。',
])
@pytest.mark.parametrize('text,source', [
    ('今は怖い。', '怖い'), ('今は怖くない。', '怖くない'),
    ('今は重い。', '重い'),
    ('今はまだよく分からない。', 'まだよく分からない'),
    ('今はどう受け止めているのか分からない。', 'どう受け止めているのか分からない'),
])
def test_later_state_has_its_own_finite_time_without_generic_approval(memo, text, source):
    context = actual(request=answered(text, initial(memo)))
    result, plan, _, resolver, selected = context
    follow = result.artifact.reception
    event = memo.split('のに')[0]
    assert follow.count(event) == 1
    assert event + '時は' in follow
    assert '回答した時点では' + source in follow
    assert not any(s in follow for s in ('ことと、その出来事', '受け止めています', '大切に思っています'))
    assert gate.read_received_discourse(follow, plan.response_plan.human_reception_plan.moves[0],
        plan, resolver, selected) is not None
    assert inverse(context, follow, without_author=True).passed


@pytest.mark.parametrize('old,new', [
    ('回答した時点では', ''), ('回答した時点では', 'その時には'),
    ('回答した時点では', '先の回答時点では'),
    ('褒められた時は', '誘われた時は'), ('褒められた時は', '彼が褒められた時は'),
    ('嬉しくなく、', ''), ('嬉しくなく、', '嬉しく、'),
    ('怖くない', '怖い'), ('怖くない', '怖くなかった'),
    ('回答した時点では', 'そのため回答した時点では'),
])
def test_temporal_discourse_mutations_fail_without_author(old, new):
    context = actual(request=answered('今は怖くない。', initial()))
    follow = context[0].artifact.reception
    changed = follow.replace(old, new)
    assert changed != follow
    assert not inverse(context, changed, without_author=True).passed


@pytest.mark.parametrize('old,new', [('まだ', ''), ('よく', ''), ('分からない', '分かる')])
def test_current_unknown_scope_is_not_lost_in_finite_response(old, new):
    context = actual(request=answered('今はまだよく分からない。', initial()))
    follow = context[0].artifact.reception
    changed = follow.replace(old, new)
    assert changed != follow and not inverse(context, changed, without_author=True).passed


def test_prior_answer_revision_keeps_its_time_and_withdrawn_event_stays_absent():
    request = advance(begin('褒められたのに、嬉しくなかった。誘われたのに、悲しかった。'), '今は重い。')
    request = advance(request, '「重い」ではなく「苦しい」です。「誘われた」は誤りです。')
    context = actual(request=request)
    follow = context[0].artifact.reception
    assert '先の回答時点では苦しい' in follow
    assert '誘われた' not in follow and '重い' not in follow and '悲しかった' in follow
    assert inverse(context, follow, without_author=True).passed
    assert not inverse(context, follow.replace('先の回答時点では', '回答した時点では'), without_author=True).passed


@pytest.mark.parametrize('text', ['今は不安です。', '今は怖いです。', '今は不安だ。',
                                  '今は私は少し怖くない。', '今は私も怖い。', '今は自分は怖い。'])
def test_temporal_adjective_and_polite_noun_use_finite_clause(text):
    context = actual(request=answered(text, initial()))
    follow = context[0].artifact.reception
    assert 'ですのですね' not in follow and 'だのですね' not in follow
    assert '褒められた時は嬉しくなく、回答した時点では' in follow
    assert '受け止めています' not in follow
    assert '私は' not in follow and '私も' not in follow and '自分は' not in follow
    assert '回答した時点' in follow
    assert inverse(context, follow, without_author=True).passed


@pytest.mark.parametrize('text', ['今は怖い。', '今は怖くない。', '今はまだよく分からない。'])
def test_temporal_finite_body_survives_save_and_no_author_restart(qcase, qdb, text, monkeypatch):
    user, parent, service = qcase
    qdb.query('update public.emotions set memo=$1 where id=$2', ['褒められたのに、嬉しくなかった。', parent])
    first = run(service.start(user, parent))
    current = run(answer(service, user, first, text))
    follow = current['current_observation']['text'].split('Emlisから：', 1)[1]
    assert '回答した時点では' in follow and '受け止めています' not in follow
    assert current['original'] == first['original']
    monkeypatch.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved body must not rerender'))
    assert run(service.get(user, parent)) == current
    assert run(service.start(user, parent)) == current


@pytest.mark.parametrize('memo', [
    '褒められたのに、嬉しくなかった。',
    '誘われたのに、悲しかった。',
    '頼まれたのに、寂しかった。',
])
@pytest.mark.parametrize('text,time,source', [
    ('今は嬉しい。', '回答した時点では', '嬉しい'),
    ('今は少し嬉しい。', '回答した時点では', '少し嬉しい'),
    ('その時は嬉しかった。', 'その時は', '嬉しかった'),
])
@continue_assertions
def test_positive_answer_is_a_time_bound_finite_feeling(memo, text, time, source):
    context = actual(request=answered(text, initial(memo)))
    result, plan, _, resolver, selected = context
    follow = result.artifact.reception
    event = memo.split('のに')[0]
    retained_assertion(lambda: (event + 'ことについて、' + time + source in follow), "event + 'ことについて、' + time + source in follow")
    retained_assertion(lambda: ('という気持ち' not in follow and '受け止めています' not in follow), "'という気持ち' not in follow and '受け止めています' not in follow")
    retained_assertion(lambda: (len(plan.response_plan.human_reception_plan.moves) == 2), 'len(plan.response_plan.human_reception_plan.moves) == 2')
    retained_assertion(lambda: (inverse(context, follow, without_author=True).passed), 'inverse(context, follow, without_author=True).passed')
    # The original reaction is an independent duty, including when the
    # added answer names a different feeling about the original occasion.
    original = actual(request=initial(memo))[0].artifact.reception
    retained_assertion(lambda: (original in follow), 'original in follow')
    retained_assertion(lambda: (not inverse(context, follow.replace(original, ''), without_author=True).passed), "not inverse(context, follow.replace(original, ''), without_author=True).passed")


@pytest.mark.parametrize('old,new', [
    ('回答した時点では', 'その時は'), ('回答した時点では', '先の回答時点では'),
    ('回答した時点では', ''), ('回答した時点では', 'そのため回答した時点では'),
    ('回答した時点では', '回答した時点では友人は'),
    ('ことについて、', 'ことのおかげで、'),
    ('少し嬉しい', '嬉しい'), ('少し嬉しい', '少し嬉しかった'),
    ('少し嬉しい', '少し嬉しくない'), ('少し嬉しい', '「少し嬉しい」'),
    ('褒められたことについて', '誘われたことについて'),
])
@continue_assertions
def test_positive_finite_answer_mutations_are_rejected_without_author(old, new):
    context = actual(request=answered('今は少し嬉しい。', initial()))
    follow = context[0].artifact.reception
    changed = follow.replace(old, new)
    retained_assertion(lambda: (changed != follow), 'changed != follow')
    retained_assertion(lambda: (not inverse(context, changed, without_author=True).passed), 'not inverse(context, changed, without_author=True).passed')


@pytest.mark.parametrize('ending', ['のです。', 'のだと受け取りました。'])
def test_positive_answer_acknowledgement_does_not_require_author_spelling(ending):
    context = actual(request=answered('今は嬉しい。', initial()))
    follow = context[0].artifact.reception
    before, last = follow.rsplit('。', 2)[:2]
    changed = before + '。' + last.removesuffix('のですね') + ending
    assert changed != follow
    assert inverse(context, changed).passed


def test_positive_answer_correction_replaces_only_the_original_reaction():
    context = actual(request=answered('あの時も本当は嬉しかった。書き方を間違えた。', initial()))
    follow = context[0].artifact.reception
    assert 'その時は嬉しかった' in follow
    assert '嬉しくなかった' not in follow and 'つながらなかった' not in follow
    assert len(context[1].response_plan.human_reception_plan.moves) == 1
    assert inverse(context, follow, without_author=True).passed


def test_prior_positive_answer_has_its_own_time_after_correction():
    request = advance(begin('褒められたのに、嬉しくなかった。誘われたのに、悲しかった。'), '今は嬉しい。')
    request = advance(request, '「嬉しい」ではなく「少し嬉しい」です。')
    context = actual(request=request)
    follow = context[0].artifact.reception
    assert '先の回答時点では少し嬉しい' in follow
    assert '誘われた' in follow and '悲しさ' in follow
    assert inverse(context, follow, without_author=True).passed
    assert not inverse(context, follow.replace('先の回答時点では', '回答した時点では'), without_author=True).passed


def test_positive_replacement_and_event_withdrawal_preserve_each_surviving_feeling():
    request = advance(begin('褒められたのに、嬉しくなかった。誘われたのに、悲しかった。'), '今は嬉しい。')
    request = advance(request, '「嬉しい」ではなく「楽しい」です。「誘われた」は誤りです。')
    # The already-admitted feeling must keep its operator after replacement.
    # Withdraw only the event; neither the detached sadness nor the other
    # event's original reaction is removed by that operation.
    context = actual(request=request)
    follow = context[0].artifact.reception
    assert '誘われた' not in follow and 'その時は悲しかった' in follow
    assert '褒められたことは、嬉しさにはつながらなかった' in follow
    assert '先の回答時点では楽しい' in follow
    assert inverse(context, follow, without_author=True).passed
    for old, new in (('悲しかった', '悲しくなかった'),
                     ('先の回答時点では', '回答した時点では'),
                     ('楽しい', '嬉しい')):
        assert not inverse(context, follow.replace(old, new), without_author=True).passed


@pytest.mark.parametrize('text', ['今は嬉しいです。', '今は私は嬉しい。', '今は僕は嬉しい。'])
def test_positive_answer_uses_proven_recipient_finite_clause(text):
    context = actual(request=answered(text, initial()))
    follow = context[0].artifact.reception
    if text.endswith('です。'):
        assert '回答した時点では嬉しい' in follow
    else:
        assert '回答した時点ではあなたは嬉しい' in follow
        assert '私は' not in follow and '僕は' not in follow
    assert follow.count('褒められた') == 1
    assert 'ですのですね' not in follow
    assert inverse(context, follow, without_author=True).passed


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
@pytest.mark.parametrize('text', ['今は嬉しい。', 'あの時も本当は嬉しかった。書き方を間違えた。'])
def test_positive_finite_answer_survives_saved_reads(qcase, qdb, tier, text, monkeypatch):
    user, parent, service = qcase
    assert 'code' not in qdb.query('update public.profiles set subscription_tier=$1 where id=$2', [tier, user])
    qdb.query('update public.emotions set memo=$1 where id=$2', ['褒められたのに、嬉しくなかった。', parent])
    first = run(service.start(user, parent))
    current = run(answer(service, user, first, text))
    body = current['current_observation']['text']
    assert 'という気持ちを受け止めています' not in body
    assert ('回答した時点では嬉しい' if text.startswith('今') else 'その時は嬉しかった') in body
    assert current['original'] == first['original']
    assert current['question_limit'] == (3 if tier == 'premium' else 1)
    monkeypatch.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved reads must not rerender'))
    assert run(service.get(user, parent)) == current
    assert run(service.start(user, parent)) == current


@pytest.mark.parametrize('memo', [
    '褒められたのに、嬉しくなかった。',
    '誘われたのに、悲しかった。',
    '頼まれたのに、寂しかった。',
])
@pytest.mark.parametrize('text,feeling', [('今は嬉しい。', '嬉しい'),
                                         ('今は少し嬉しい。', '少し嬉しい')])
def test_answer_continues_the_unique_preceding_event_without_repeating_it(memo, text, feeling):
    context = actual(request=answered(text, initial(memo)))
    result, plan, _, resolver, selected = context
    follow = result.artifact.reception
    original = actual(request=initial(memo))[0].artifact.reception
    assert follow == original + '回答した時点では' + feeling + 'のですね。'
    assert follow.count(memo.split('のに')[0]) == 1
    reception_plan = plan.response_plan.human_reception_plan
    assert len(reception_plan.moves) == 2
    assert reception_plan.depth_policy.min_sentences == 2
    assert len(reception.build_grounded_reception_clause_plans(reception_plan, 'full', plan=plan)) == 2
    assert inverse(context, follow, without_author=True).passed
    # The feeling alone is not an independent reading of an unspecified event.
    second = follow[len(original):]
    assert gate.read_source_owned_discourse(second, reception_plan.moves[1], plan, resolver, selected) is None


@pytest.mark.parametrize('old,new', [
    ('褒められた', '誘われた'), ('褒められた', '友人が褒められた'),
    ('嬉しさにはつながらなかった', '嬉しさにつながった'),
    ('嬉しさにはつながらなかった', '嬉しさにはつながらない'),
    ('回答した時点では', 'その時は'), ('回答した時点では', '先の回答時点では'),
    ('回答した時点では', ''), ('回答した時点では', 'そのため回答した時点では'),
    ('回答した時点では', '回答した時点では友人は'),
    ('少し嬉しい', '嬉しい'), ('少し嬉しい', '少し嬉しかった'),
    ('少し嬉しい', '少し嬉しくない'), ('少し嬉しい', '「少し嬉しい」'),
])
def test_shared_event_actual_context_mutations_fail_without_author(old, new):
    context = actual(request=answered('今は少し嬉しい。', initial()))
    follow = context[0].artifact.reception
    changed = follow.replace(old, new)
    assert changed != follow
    assert not inverse(context, changed, without_author=True).passed


@pytest.mark.parametrize('mutation', ['delete', 'swap', 'insert', 'quote'])
def test_shared_event_requires_the_immediately_preceding_complete_sentence(mutation):
    context = actual(request=answered('今は嬉しい。', initial()))
    follow = context[0].artifact.reception
    first, second, end = follow.split('。')
    assert end == ''
    changed = {'delete': second + '。', 'swap': second + '。' + first + '。',
               'insert': first + '。別の出来事がありました。' + second + '。',
               'quote': '「' + first + '」。' + second + '。'}[mutation]
    assert not inverse(context, changed, without_author=True).passed


def test_answer_does_not_share_an_ambiguous_multiple_event_context():
    request = advance(begin('褒められたのに、嬉しくなかった。誘われたのに、悲しかった。'), '今は嬉しい。')
    context = actual(request=request)
    follow = context[0].artifact.reception
    assert follow.startswith('当時、褒められたことは、嬉しさにはつながらず、回答した時点では嬉しい')
    assert inverse(context, follow, without_author=True).passed
    # A middle focus still follows a multiple-event sentence. It cannot
    # borrow the last event as its antecedent or omit its own explicit owner.
    request = advance(advance(begin(), 'その時は重かった。'), '今は嬉しい。')
    context = actual(request=request)
    follow = context[0].artifact.reception
    explicit = '誘われたことについて、回答した時点では嬉しい'
    assert explicit in follow
    assert inverse(context, follow, without_author=True).passed
    assert not inverse(context, follow.replace('誘われたことについて、', ''), without_author=True).passed


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
@pytest.mark.parametrize('memo', ['誘われたのに、悲しかった。', '頼まれたのに、寂しかった。'])
def test_shared_event_survives_saved_retrieval_without_generation(qcase, qdb, tier, memo, monkeypatch):
    user, parent, service = qcase
    assert 'code' not in qdb.query('update public.profiles set subscription_tier=$1 where id=$2', [tier, user])
    qdb.query('update public.emotions set memo=$1 where id=$2', [memo, parent])
    first = run(service.start(user, parent))
    current = run(answer(service, user, first, '今は少し嬉しい。'))
    follow = current['current_observation']['text'].split('Emlisから：', 1)[1].strip()
    assert follow.count(memo.split('のに')[0]) == 1
    assert '回答した時点では少し嬉しい' in follow
    assert current['original'] == first['original']
    assert current['question_limit'] == (3 if tier == 'premium' else 1)
    monkeypatch.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved read must not rerender'))
    assert run(service.get(user, parent)) == current
    assert run(service.start(user, parent)) == current


def test_shared_event_accepts_explicit_reference_and_equivalent_acknowledgements():
    context = actual(request=answered('今は嬉しい。', initial()))
    follow = context[0].artifact.reception
    expanded = follow.replace('回答した時点では', '褒められたことについて、回答した時点では')
    assert expanded != follow and inverse(context, expanded).passed
    changed = follow.replace('のですね。', 'のです。')
    assert changed != follow and inverse(context, changed).passed


# An epistemic ADD owns one event; it cannot replace the other lived reactions.
ATTACHED_UNKNOWN_ANSWERS = (
    ('今はまだよく分からない。', 'まだよく分からない'),
    ('現在は分からない。', '分からない'),
)


@pytest.mark.parametrize('text,source', ATTACHED_UNKNOWN_ANSWERS)
@pytest.mark.parametrize('count', [2, 3])
@pytest.mark.parametrize('reversed_events', [False, True])
def test_attached_unknown_preserves_every_event_and_original_reaction(text, source, count, reversed_events):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    clauses = ['褒められたのに、嬉しくなかった', '誘われたのに、悲しかった', '頼まれたのに、寂しかった'][:count]
    if reversed_events:
        clauses.reverse()
    request = advance(begin('。'.join(clauses) + '。'), text)
    public = MeaningExperienceEngine().generate(request)
    assert public.artifact is not None, public.reason_codes
    context = actual(request=request)
    result, plan, _, resolver, selected = context
    assert result.artifact.text == public.artifact.text
    follow = result.artifact.reception
    assert f'回答した時点では{source}' in follow
    assert '受け止めています' not in follow
    for clause in clauses:
        event, feeling = clause.split('のに、')
        assert follow.count(event) == 1
        if clause == clauses[0]:
            assert event + '時は' + feeling.removesuffix('かった') + 'く、' in follow
        elif feeling == '嬉しくなかった':
            assert event + 'ことは、嬉しさにはつながらなかった' in follow
        else:
            assert event + 'のに、' + feeling.removesuffix('かった') + 'さを感じた' in follow
    move, = plan.response_plan.human_reception_plan.moves
    assert set((*move.target_nucleus_ids, *move.support_nucleus_ids)) == {
        n.nucleus_id for n in plan.nuclei if n.retention == 'required'
        and n.source_fields in {('memo',), ('answer_text_private',)}}
    state, = (n for n in plan.nuclei if n.source_fields == ('answer_text_private',))
    assert (state.kind, state.semantic_frame.predicate_kind, state.semantic_frame.modality) == ('state', 'state', 'uncertain')
    about, = (r for r in plan.relations if r.type == 'evaluation_about_event')
    assert about.to_nucleus_id == state.nucleus_id and about.from_nucleus_id == move.target_nucleus_ids[0]
    assert gate.read_received_discourse(follow, move, plan, resolver, selected) is not None
    assert inverse(context, follow, without_author=True).passed


@pytest.fixture(scope='module')
def attached_unknown_context():
    return actual(request=advance(begin(), ATTACHED_UNKNOWN_ANSWERS[0][0]))


@pytest.mark.parametrize('old,new', [
    ('まだよく分からない', 'よく分からない'),
    ('まだよく分からない', 'まだ分からない'),
    ('まだよく分からない', 'まだよく分かった'),
    ('まだよく分からない', 'まだよく分からなかった'),
    ('まだよく分からない', 'まだよく分からない気持ちだ'),
    ('回答した時点では', 'その時は'),
    ('回答した時点では', '先の回答時点では'),
    ('回答した時点では', ''),
    ('嬉しくなく、', ''), ('嬉しくなく、', '嬉しく、'),
    ('褒められた時は', '誘われた時は'),
    ('褒められた時は', '友人が褒められた時は'),
    ('誘われたのに、悲しさを感じたし、', ''),
    ('悲しさを感じた', '悲しさを感じなかった'),
    ('頼まれたのに、寂しさを感じた', '頼まれたのに、嬉しさを感じた'),
    ('誘われたのに、', '誘われたので、'),
    ('分からないし、誘われた', '分からないから、誘われた'),
    ('頼まれたのに、', '今、頼まれたのに、'),
])
def test_attached_unknown_rejects_lost_or_reassigned_meaning_without_author(attached_unknown_context, old, new):
    follow = attached_unknown_context[0].artifact.reception
    assert old in follow
    changed = follow.replace(old, new, 1)
    assert not inverse(attached_unknown_context, changed, without_author=True).passed


def test_attached_unknown_accepts_equivalent_acknowledgement(attached_unknown_context):
    follow = attached_unknown_context[0].artifact.reception.replace('のですね。', 'のです。')
    assert inverse(attached_unknown_context, follow).passed


@pytest.mark.parametrize('text,source', ATTACHED_UNKNOWN_ANSWERS)
@pytest.mark.parametrize('operation', ['correct', 'withdraw'])
def test_attached_unknown_saved_updates_keep_original_reactions_and_replay(qcase, qdb, monkeypatch, text, source, operation):
    from test_emlis_q3_application import cont
    user, parent, service = qcase
    replacement = '分からない' if source == 'まだよく分からない' else 'まだよく分からない'
    change = (f'「{source}」ではなく「{replacement}」です。' if operation == 'correct'
              else f'「{source}」は誤りです。')
    first = current = run(service.start(user, parent))
    for index, value in enumerate((text, change, '「褒められた」は誤りです。')):
        if index:
            current = run(cont(service, user, current, f'attached-continue-{index}'))
        current = run(answer(service, user, current, value, f'attached-answer-{index}'))
        assert current['body_state'] == 'REFINED', current
        assert current['original'] == first['original']
        follow = current['current_observation']['text'].split('Emlisから：', 1)[1].strip()
        for event, feeling in [('誘われた', '悲し'), ('頼まれた', '寂し')]:
            assert event in follow and feeling in follow
        if index == 0:
            assert f'褒められた時は嬉しくなく、回答した時点では{source}' in follow
        elif index == 1:
            if operation == 'correct':
                assert f'褒められた時は嬉しくなく、先の回答時点では{replacement}' in follow
            else:
                assert '褒められたことは、嬉しさにはつながらず' in follow
                assert '分からない' not in follow
        else:
            assert '褒められた' not in follow and 'その時は嬉しくなかった' in follow
            assert ('分からない' in follow) == (operation == 'correct')
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved reads must not generate'))
            assert run(service.get(user, parent)) == current
            assert run(service.start(user, parent)) == current


MULTI_UNKNOWN = '今はまだよく分からない。'
MULTI_OTHER_UNKNOWN = '現在は分からない。'
MULTI_NEGATIVE = 'その時は怖かった。'
MULTI_POSITIVE = '今は嬉しい。'
MULTI_THIRD = 'その時は苦しかった。'
MULTI_UNKNOWN_PAIRS = (
    (MULTI_UNKNOWN, MULTI_NEGATIVE), (MULTI_NEGATIVE, MULTI_UNKNOWN),
    (MULTI_UNKNOWN, MULTI_OTHER_UNKNOWN), (MULTI_OTHER_UNKNOWN, MULTI_UNKNOWN),
    (MULTI_UNKNOWN, MULTI_POSITIVE), (MULTI_POSITIVE, MULTI_UNKNOWN),
)
MULTI_UNKNOWN_TRIPLES = (
    (MULTI_UNKNOWN, MULTI_NEGATIVE, MULTI_THIRD),
    (MULTI_NEGATIVE, MULTI_UNKNOWN, MULTI_THIRD),
    (MULTI_NEGATIVE, MULTI_THIRD, MULTI_UNKNOWN),
    (MULTI_UNKNOWN, MULTI_OTHER_UNKNOWN, MULTI_UNKNOWN),
    (MULTI_UNKNOWN, MULTI_NEGATIVE, MULTI_POSITIVE),
    (MULTI_POSITIVE, MULTI_UNKNOWN, MULTI_NEGATIVE),
    (MULTI_UNKNOWN, MULTI_OTHER_UNKNOWN, MULTI_POSITIVE),
)


def multi_unknown_request(sequence, count=3):
    from test_cmee_emlis_q3_thread import MEMO
    request = begin('。'.join(MEMO.split('。')[:count]) + '。')
    for text in sequence:
        request = advance(request, text)
    return request


def assert_multi_unknown_duties(context, sequence, count):
    result, plan, _, _, _ = context
    follow = result.artifact.reception
    moves = plan.response_plan.human_reception_plan.moves
    adjacent = MULTI_POSITIVE in sequence and sequence.index(MULTI_POSITIVE) in (0, count - 1)
    assert len(moves) == (3 if adjacent else 2 if MULTI_POSITIVE in sequence else 1)
    assert set(nid for move in moves for nid in (*move.target_nucleus_ids, *move.support_nucleus_ids)) == {
        n.nucleus_id for n in plan.nuclei if n.retention == 'required'
        and n.source_fields in {('memo',), ('answer_text_private',)}}
    for event in ('褒められた', '誘われた', '頼まれた')[:count]:
        assert event in follow
    for feeling in ('嬉し', '悲し', '寂し')[:count]:
        assert feeling in follow
    for index, text in enumerate(sequence):
        event = ('褒められた', '誘われた', '頼まれた')[index]
        if text in (MULTI_UNKNOWN, MULTI_OTHER_UNKNOWN):
            source = 'まだよく分からない' if text == MULTI_UNKNOWN else '分からない'
            assert event + '時は' in follow and '回答した時点では' + source in follow
        elif text == MULTI_POSITIVE:
            if adjacent:
                parts = follow.split('。')[:-1]
                position = 0 if index == 0 else 1
                assert len(parts) == 2 and parts[position].startswith('当時、' + event)
                assert parts[position].endswith('、回答した時点では嬉しいのですね')
                events = ('褒められた', '誘われた', '頼まれた')[:count]
                assert all(follow.count(source) == 1 for source in events)
                assert [follow.index(source) for source in events] == sorted(follow.index(source) for source in events)
            else:
                assert event + 'ことについて、回答した時点では嬉しい' in follow
        else:
            assert text.removeprefix('その時は').removesuffix('。') in follow
    for n in plan.nuclei:
        if n.source_fields == ('answer_text_private',) and n.semantic_frame.modality == 'uncertain':
            assert (n.kind, n.semantic_frame.predicate_kind, n.semantic_frame.time_scope) == ('state', 'state', 'present')
    assert inverse(context, follow, without_author=True).passed


@pytest.mark.parametrize('sequence', MULTI_UNKNOWN_PAIRS)
@pytest.mark.parametrize('count', [2, 3])
def test_multi_unknown_two_answers_keep_each_source_and_original(sequence, count):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    request = multi_unknown_request(sequence, count)
    public = MeaningExperienceEngine().generate(request)
    assert public.artifact is not None, public.reason_codes
    context = actual(request=request)
    assert public.artifact.text == context[0].artifact.text
    assert_multi_unknown_duties(context, sequence, count)


@pytest.mark.parametrize('sequence', MULTI_UNKNOWN_TRIPLES)
def test_multi_unknown_three_answers_keep_all_sources(sequence):
    assert_multi_unknown_duties(actual(request=multi_unknown_request(sequence)), sequence, 3)


@pytest.fixture(scope='module')
def multi_unknown_context():
    return actual(request=multi_unknown_request((MULTI_UNKNOWN, MULTI_OTHER_UNKNOWN, MULTI_NEGATIVE)))


@pytest.mark.parametrize('old,new', [
    ('まだよく分からない', '分からない'), ('まだよく分からない', 'まだ分からない'),
    ('まだよく分からない', 'まだよく分かった'),
    ('まだよく分からない', 'まだよく分からなかった'),
    ('まだよく分からない', 'まだよく分からない気持ちだ'),
    ('回答した時点では', 'その時は'), ('回答した時点では', '先の回答時点では'),
    ('褒められた時は', '友人が褒められた時は'),
    ('嬉しくなく、', ''), ('悲しく、', ''), ('怖かった', '怖くなかった'),
    ('褒められた時は嬉しくなく、回答した時点ではまだよく分からないし、', ''),
    ('誘われた時は悲しく、回答した時点では分からないし、', ''),
    ('分からないし、誘われた', '分からないので、誘われた'),
])
def test_multi_unknown_meaning_changes_fail_without_author(multi_unknown_context, old, new):
    follow = multi_unknown_context[0].artifact.reception
    assert old in follow
    assert not inverse(multi_unknown_context, follow.replace(old, new, 1), without_author=True).passed


def test_multi_unknown_swapped_sources_fail_and_equivalent_ending_passes(multi_unknown_context):
    follow = multi_unknown_context[0].artifact.reception
    changed = follow.replace('まだよく分からない', '<first>', 1).replace('では分からない', 'ではまだよく分からない', 1).replace('<first>', '分からない')
    assert changed != follow and not inverse(multi_unknown_context, changed, without_author=True).passed
    assert inverse(multi_unknown_context, follow.replace('のですね。', 'のです。')).passed


@pytest.mark.parametrize('mutation', ['missing', 'duplicate', 'same_event', 'independent'])
def test_multi_unknown_requires_unique_active_event_ownership(multi_unknown_context, mutation):
    from dataclasses import replace
    from emlis_ai_grounded_observation_plan import _thread_retained_reaction_groups
    plan = multi_unknown_context[1]
    about = [r for r in plan.relations if r.type == 'evaluation_about_event']
    first, second = about[:2]
    nuclei = plan.nuclei
    relations = list(plan.relations)
    if mutation in ('missing', 'independent'):
        relations.remove(first)
    elif mutation == 'duplicate':
        relations.append(replace(first, relation_id=first.relation_id + '-duplicate'))
    else:
        relations[relations.index(second)] = replace(second, from_nucleus_id=first.from_nucleus_id)
    if mutation == 'independent':
        nuclei = tuple(replace(n, semantic_frame=replace(n.semantic_frame,
            attribute_codes=tuple(c for c in n.semantic_frame.attribute_codes if c != 'thread_subject:unique_source_clause')
                + ('thread_subject:independent_source_replacement',))) if n.nucleus_id == first.to_nucleus_id else n for n in nuclei)
    assert _thread_retained_reaction_groups(nuclei, tuple(relations)) == ()


MULTI_UNKNOWN_UPDATES = (
    ('correct_first', MULTI_NEGATIVE, '「まだよく分からない」ではなく「分からない」です。'),
    ('withdraw_first', MULTI_OTHER_UNKNOWN, '「まだよく分からない」は誤りです。'),
    ('correct_second', MULTI_NEGATIVE, '「怖かった」ではなく「苦しかった」です。'),
    ('withdraw_other_event', MULTI_NEGATIVE, '「誘われた」は誤りです。'),
)


@pytest.mark.parametrize('operation,second,change', MULTI_UNKNOWN_UPDATES)
def test_multi_unknown_saved_update_retains_other_sources_and_replays(qcase, qdb, monkeypatch, operation, second, change):
    from test_emlis_q3_application import cont
    user, parent, service = qcase
    first = current = run(service.start(user, parent))
    for index, text in enumerate((MULTI_UNKNOWN, second, change)):
        if index:
            current = run(cont(service, user, current, f'multi-continue-{index}'))
        current = run(answer(service, user, current, text, f'multi-answer-{index}'))
        assert current['body_state'] == 'REFINED', current
        assert current['original'] == first['original']
        follow = current['current_observation']['text'].split('Emlisから：', 1)[1].strip()
        assert '褒められた' in follow and '頼まれた' in follow
        assert any(text in follow for text in ('嬉しくなく', '嬉しさにはつながらず', '嬉しさにはつながらなかった'))
        assert '悲し' in follow and '寂し' in follow
        if index < 2:
            assert '回答した時点ではまだよく分からない' in follow
            assert '誘われた' in follow
            if index == 1:
                assert ('怖かった' if second == MULTI_NEGATIVE else '回答した時点では分からない') in follow
        elif operation == 'correct_first':
            assert '先の回答時点では分からない' in follow and 'まだよく' not in follow and '怖かった' in follow
        elif operation == 'withdraw_first':
            assert 'まだよく' not in follow and '誘われた時は悲しく、回答した時点では分からない' in follow
        elif operation == 'correct_second':
            assert '怖かった' not in follow and '苦しかった' in follow and 'まだよく分からない' in follow
        else:
            assert '誘われた' not in follow and 'その時は怖かった' in follow and 'まだよく分からない' in follow
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved reads must not generate'))
            assert run(service.get(user, parent)) == current
            assert run(service.start(user, parent)) == current


def test_multi_unknown_other_event_withdrawal_keeps_attached_unknown():
    context = actual(request=multi_unknown_request((MULTI_UNKNOWN, '「誘われた」は誤りです。')))
    follow = context[0].artifact.reception
    assert '誘われた' not in follow and 'その時は悲しかった' in follow
    assert '褒められた時は嬉しくなく、回答した時点ではまだよく分からない' in follow
    assert '頼まれたのに、寂しさを感じた' in follow
    assert inverse(context, follow, without_author=True).passed


TWO_POSITIVE_PAIRS = (
    ('今は嬉しい。', '今は楽しい。'),
    ('今は嬉しい。', 'その時は楽しかった。'),
    ('その時は嬉しかった。', '今は楽しい。'),
    ('その時は嬉しかった。', 'その時は楽しかった。'),
)


def assert_two_positive_duties(context, count):
    result, plan, _, _, _ = context
    follow = result.artifact.reception
    moves = plan.response_plan.human_reception_plan.moves
    assert len(moves) == 3 and all(m.required for m in moves)
    assert set(nid for m in moves for nid in (*m.target_nucleus_ids, *m.support_nucleus_ids)) == {
        n.nucleus_id for n in plan.nuclei if n.retention == 'required'
        and n.source_fields in {('memo',), ('answer_text_private',)}}
    positives = [m for m in moves if m.reception_act == 'recognize_lived_change']
    assert [m.move_role for m in positives] == ['attention', 'felt_response']
    assert len({m.target_nucleus_ids for m in positives}) == 2
    for event, feeling in list(zip(('褒められた', '誘われた', '頼まれた'), ('嬉し', '悲し', '寂し')))[:count]:
        assert event in follow and feeling in follow
    assert follow.count('。') == 3
    # Original reactions precede the two supplemental readings; attention
    # is an act responsibility, not a reason to split the source account.
    assert '嬉し' in follow.split('。')[0] and '悲し' in follow.split('。')[0]
    assert inverse(context, follow, without_author=True).passed


@pytest.mark.parametrize('sequence', TWO_POSITIVE_PAIRS)
@pytest.mark.parametrize('count', [2, 3])
def test_two_positive_answers_keep_originals_and_each_event_time(sequence, count):
    context = actual(request=multi_unknown_request(sequence, count))
    assert_two_positive_duties(context, count)
    follow = context[0].artifact.reception
    for event, text in zip(('褒められた', '誘われた'), sequence):
        when = '回答した時点では' if text.startswith('今は') else 'その時は'
        source = text.removeprefix('今は').removeprefix('その時は').removesuffix('。')
        assert event + 'ことについて、' + when + source in follow


@pytest.mark.parametrize('other', [MULTI_UNKNOWN, MULTI_OTHER_UNKNOWN, MULTI_NEGATIVE])
@pytest.mark.parametrize('position', [0, 1, 2])
def test_two_positive_answers_keep_unknown_or_burden_in_every_position(other, position):
    sequence = ['今は嬉しい。', 'その時は楽しかった。']
    sequence.insert(position, other)
    context = actual(request=multi_unknown_request(sequence))
    assert_two_positive_duties(context, 3)
    follow = context[0].artifact.reception
    event = ('褒められた', '誘われた', '頼まれた')[position]
    assert event + '時は' in follow
    expected = ('怖' if other == MULTI_NEGATIVE else
                '回答した時点では' + ('まだよく分からない' if other == MULTI_UNKNOWN else '分からない'))
    assert expected in follow.split('。')[0]


@pytest.mark.parametrize('sequence,first,second', [
    (('今は私には嬉しい。', 'その時は少し楽しかった。'), '回答した時点ではあなたには嬉しい', 'その時は少し楽しかった'),
    (('その時は嬉しかったです。', '今は楽しいです。'), 'その時は嬉しかった', '回答した時点では楽しい'),
    (('今は少し嬉しい。', 'その時は私は楽しかった。'), '回答した時点では少し嬉しい', 'その時はあなたは楽しかった'),
    (('今は嬉しいのです。', 'その時は嬉しかったのです。'), '回答した時点では嬉しい', 'その時は嬉しかった'),
])
def test_two_positive_answers_preserve_self_degree_politeness_and_explanation(sequence, first, second):
    context = actual(request=multi_unknown_request(sequence))
    assert_two_positive_duties(context, 3)
    follow = context[0].artifact.reception
    assert first in follow and second in follow


@pytest.fixture(scope='module')
def two_positive_context():
    return actual(request=multi_unknown_request((MULTI_UNKNOWN, '今は私には嬉しい。', 'その時は少し楽しかった。')))


@pytest.mark.parametrize('old,new', [
    ('まだよく分からない', '分からない'), ('まだよく分からない', 'まだよく分かった'),
    ('嬉しくなく', '嬉しく'), ('悲しさ', '嬉しさ'), ('寂しさ', '悲しさ'),
    ('回答した時点ではあなたには', 'その時はあなたには'), ('あなたには', '友人には'),
    ('嬉しいのですね', '嬉しくないのですね'),
    ('その時は少し楽しかった', '回答した時点では少し楽しかった'),
    ('少し楽しかった', '楽しかった'), ('少し楽しかった', '少し楽しい'),
    ('誘われたことについて', '頼まれたことについて'),
    ('。頼まれたことについて', 'ので、頼まれたことについて'),
    ('誘われたことについて、回答した時点ではあなたには嬉しいのですね。', ''),
    ('頼まれたことについて、その時は少し楽しかったのですね。',
     '頼まれたことについて、その時は少し楽しかったのですね。頼まれたことについて、その時は少し楽しかったのですね。'),
])
def test_two_positive_semantic_mutations_fail_without_author(two_positive_context, old, new):
    follow = two_positive_context[0].artifact.reception
    assert old in follow
    changed = follow.replace(old, new, 1)
    assert changed != follow and not inverse(two_positive_context, changed, without_author=True).passed


def test_two_positive_equivalent_ending_is_independently_accepted(two_positive_context):
    follow = two_positive_context[0].artifact.reception
    assert_two_positive_duties(two_positive_context, 3)
    changed = follow.replace('嬉しいのですね。', '嬉しいのだと受け取りました。')
    assert changed != follow and inverse(two_positive_context, changed, without_author=True).passed


@pytest.mark.parametrize('mutation', ['missing', 'duplicate', 'act', 'target'])
def test_two_positive_about_requires_one_real_owner_per_answer(two_positive_context, mutation):
    from dataclasses import replace
    plan = two_positive_context[1]
    moves = plan.response_plan.human_reception_plan.moves
    assert len(moves) == 3
    burden = next(m for m in moves if m.reception_act == 'stay_with_current_burden')
    positives = [m for m in moves if m.reception_act == 'recognize_lived_change']
    edges = {r.relation_id for r in plan.relations if r.type == 'evaluation_about_event'
             and r.to_nucleus_id in {m.target_nucleus_ids[0] for m in positives}}
    assert len(edges) == 2
    owned = {r.relation_id for m in positives for r in reception.source_grounded_reception_move_relations(m, plan)}
    assert edges <= owned
    assert not edges & {r.relation_id for r in reception.source_grounded_reception_move_relations(burden, plan)}
    changed = [m for m in moves if m != positives[0]]
    if mutation == 'duplicate':
        changed = [*moves, replace(positives[0], move_id='duplicate-positive')]
    elif mutation == 'act':
        changed.append(replace(positives[0], reception_act='stay_with_current_burden'))
    elif mutation == 'target':
        changed.append(replace(positives[0], target_nucleus_ids=positives[1].target_nucleus_ids))
    altered = replace(plan, response_plan=replace(plan.response_plan, human_reception_plan=replace(
        plan.response_plan.human_reception_plan, moves=tuple(changed))))
    assert edges <= {r.relation_id for r in reception.source_grounded_reception_move_relations(burden, altered)}


@pytest.mark.parametrize('mutation', ['missing', 'duplicate', 'same_event'])
def test_two_positive_selection_requires_unique_about_sources(two_positive_context, mutation):
    from dataclasses import replace
    from emlis_ai_grounded_observation_plan import _thread_retained_reaction_groups
    plan = two_positive_context[1]
    positive_ids = {n.nucleus_id for n in plan.nuclei if n.source_fields == ('answer_text_private',)
                    and n.semantic_frame.polarity == 'positive'}
    links = [r for r in plan.relations if r.type == 'evaluation_about_event' and r.to_nucleus_id in positive_ids]
    assert len(links) == 2
    relations = list(plan.relations)
    if mutation == 'missing':
        relations.remove(links[0])
    elif mutation == 'duplicate':
        relations.append(replace(links[0], relation_id='duplicate-about'))
    else:
        relations[relations.index(links[1])] = replace(links[1], from_nucleus_id=links[0].from_nucleus_id)
    assert _thread_retained_reaction_groups(plan.nuclei, relations) == ()


TWO_POSITIVE_SAVED = (
    (MULTI_UNKNOWN, '今は嬉しい。', 'その時は楽しかった。'),
    ('今は嬉しい。', 'その時は楽しかった。', '「嬉しい」ではなく「少し嬉しい」です。'),
    ('今は嬉しい。', 'その時は楽しかった。', '「楽しかった」は誤りです。'),
    ('今は嬉しい。', 'その時は楽しかった。', 'その時は怖かった。'),
)


@pytest.mark.parametrize('sequence', TWO_POSITIVE_SAVED)
def test_two_positive_saved_answer_correction_withdrawal_and_replay(qcase, qdb, monkeypatch, sequence):
    from test_emlis_q3_application import cont
    user, parent, service = qcase
    first = current = run(service.start(user, parent))
    for index, text in enumerate(sequence):
        if index:
            current = run(cont(service, user, current, f'positive-continue-{index}'))
        current = run(answer(service, user, current, text, f'positive-answer-{index}'))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        follow = current['current_observation']['text'].split('Emlisから：', 1)[1].strip()
        for event, feeling in zip(('褒められた', '誘われた', '頼まれた'), ('嬉し', '悲し', '寂し')):
            assert event in follow and feeling in follow
        if sequence[0] == MULTI_UNKNOWN:
            assert '回答した時点ではまだよく分からない' in follow
        if index == 2:
            if 'ではなく' in text:
                assert '先の回答時点では少し嬉しい' in follow and 'その時は楽しかった' in follow
            elif '誤り' in text:
                assert '楽しかった' not in follow and '回答した時点では嬉しい' in follow
            else:
                assert '回答した時点では嬉しい' in follow and 'その時は楽しかった' in follow
                if text == 'その時は怖かった。':
                    assert '怖かった' in follow
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved reads must not generate'))
            assert run(service.get(user, parent)) == current
            assert run(service.start(user, parent)) == current


def test_two_positive_unadmitted_explanation_is_not_silently_retyped():
    context = actual(request=multi_unknown_request(('今は嬉しいのです。', 'その時は楽しかったのです。')))
    result, plan, _, _, _ = context
    answers = [n for n in plan.nuclei if n.source_fields == ('answer_text_private',)]
    assert len(answers) == 1
    assert '回答の「その時は楽しかったのです」には、今回の観測に反映できていない部分があります。' in result.artifact.text
    assert '楽しかった' not in result.artifact.reception
    assert inverse(context, result.artifact.reception, without_author=True).passed


@pytest.fixture(scope='module', params=[
    (('今は私も少し嬉しいです。',), '回答した時点では', '私も少し嬉しいです'),
    (('その時は少し重かった。',), 'その時は', '少し重かった'),
    (('今は嬉しい。', '「嬉しい」ではなく「少し楽しい」です。'), '先の回答時点では', '少し楽しい'),
])
def compact_report_context(request):
    sequence, time, source = request.param
    req = begin()
    for reply in sequence:
        req = advance(req, reply)
    return actual(request=req), time, source


def test_compact_report_keeps_three_sources_and_two_owned_relations(compact_report_context):
    from test_cmee_emlis_detached_observation import read_body
    context, time, source = compact_report_context
    result, plan, _, _, _ = context
    report = f'「褒められた」のに「嬉しくなかった」、{time}「{source}」とあります。'
    assert result.artifact.observation.startswith(report)
    assert result.artifact.observation.count('「褒められた」') == 1
    assert all(q in result.artifact.observation for q in ('「誘われた」', '「悲しかった」', '「頼まれた」', '「寂しかった」'))
    event = next(n for n in plan.nuclei if n.nucleus_id == 'nucleus:s1:event')
    assert {r.type for r in plan.relations if r.from_nucleus_id == event.nucleus_id} == {'contrast', 'evaluation_about_event'}
    with patch.object(surface, '_render_relation', side_effect=AssertionError('no report author')):
        assert read_body(context, result.artifact.text).passed


@pytest.mark.parametrize('mutation', [
    'drop_event', 'drop_original', 'drop_answer', 'swap_feelings',
    'cause_original', 'cause_answer', 'time_missing', 'time_wrong',
    'wrong_event', 'original_polarity', 'degree_missing', 'extra_claim',
])
def test_compact_report_rejects_missing_or_crossed_duties(compact_report_context, mutation):
    from test_cmee_emlis_detached_observation import read_body
    context, time, source = compact_report_context
    body = context[0].artifact.text
    report = f'「褒められた」のに「嬉しくなかった」、{time}「{source}」とあります。'
    changed = {
        'drop_event': report.replace('「褒められた」', ''),
        'drop_original': report.replace('「嬉しくなかった」', ''),
        'drop_answer': report.replace(f'「{source}」', ''),
        'swap_feelings': f'「褒められた」のに「{source}」、{time}「嬉しくなかった」とあります。',
        'cause_original': report.replace('のに', 'ので'),
        'cause_answer': report.replace('」、' + time, '」、そのため' + time),
        'time_missing': report.replace(time, ''),
        'time_wrong': report.replace(time, 'その時は' if time != 'その時は' else '回答した時点では'),
        'wrong_event': report.replace('「褒められた」', '「誘われた」'),
        'original_polarity': report.replace('「嬉しくなかった」', '「嬉しかった」'),
        'degree_missing': report.replace(source, source.replace('少し', '')),
        'extra_claim': report.replace('とあります。', 'とあり、気持ちが改善しています。'),
    }[mutation]
    assert changed != report and report in body
    with patch.object(surface, '_render_relation', side_effect=AssertionError('no report author')):
        assert not read_body(context, body.replace(report, changed, 1)).passed


@pytest.mark.parametrize('legacy', [0, 1])
def test_compact_report_retains_complete_legacy_readings(compact_report_context, legacy):
    from test_cmee_emlis_detached_observation import read_body
    context, time, source = compact_report_context
    report = f'「褒められた」のに「嬉しくなかった」、{time}「{source}」とあります。'
    when = time.removesuffix('では').removesuffix('は')
    old = (f'「褒められた」一方で「嬉しくなかった」とあり、その出来事について、{when}の受け止めは「{source}」と書かれています。'
           if legacy == 0 else
           f'「褒められた」という出来事の一方で「嬉しくなかった」という反応があり、その出来事に対する{when}の受け止めとして、「{source}」が見えます。')
    with patch.object(surface, '_render_relation', side_effect=AssertionError('no report author')):
        assert read_body(context, context[0].artifact.text.replace(report, old, 1)).passed


def test_compact_report_saved_correction_and_withdrawal_reuses_dto(qcase, monkeypatch):
    from test_emlis_q3_application import cont
    user, parent, service = qcase
    first = current = run(service.start(user, parent))
    for i, reply in enumerate(('今は嬉しい。', '「嬉しい」ではなく「少し楽しい」です。', '「褒められた」は誤りです。')):
        if i:
            current = run(cont(service, user, current, f'compact-report-continue-{i}'))
        current = run(answer(service, user, current, reply, f'compact-report-answer-{i}'))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        body = current['current_observation']['text']
        if i < 2:
            time, source = ('回答した時点では', '嬉しい') if i == 0 else ('先の回答時点では', '少し楽しい')
            assert f'「褒められた」のに「嬉しくなかった」、{time}「{source}」とあります。' in body
        else:
            assert '褒められた' not in body
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved read must not regenerate'))
            assert run(service.get(user, parent)) == current
            assert run(service.start(user, parent)) == current
    assert current['state'] == 'COMPLETED' and not current['can_continue']


@pytest.fixture(scope='module', params=[
    (), ('今は嬉しい。',),
    ('今は嬉しい。', '「嬉しくなかった」ではなく「重かった」です。'),
    ('今は嬉しい。', '「褒められた」は誤りです。'),
])
def parallel_report_context(request):
    req = begin()
    for reply in request.param:
        req = advance(req, reply)
    pairs = [('褒められた', '嬉しくなかった'), ('誘われた', '悲しかった'), ('頼まれた', '寂しかった')]
    if request.param:
        pairs = pairs[1:]
    report = '、また'.join(f'「{event}」の一方で「{feeling}」' for event, feeling in pairs) + 'とあります。'
    return actual(request=req), pairs, report


def test_parallel_report_preserves_every_ordered_pair(parallel_report_context):
    from test_cmee_emlis_detached_observation import read_body
    context, pairs, report = parallel_report_context
    body = context[0].artifact.text
    assert report in context[0].artifact.observation
    assert all(body.count(f'「{event}」') == 1 for event, _ in pairs)
    with patch.object(surface, '_render_relation', side_effect=AssertionError('no author oracle')):
        assert read_body(context, body).passed


@pytest.mark.parametrize('mutation', [
    'drop_pair', 'swap_reactions', 'reverse_pairs', 'cause', 'unrelated',
    'duplicate_pair', 'extra_clause', 'extra_sentence', 'quoted_extra_sentence', 'negation',
])
def test_parallel_report_rejects_changed_or_unconsumed_meaning(parallel_report_context, mutation):
    from test_cmee_emlis_detached_observation import read_body
    context, pairs, report = parallel_report_context
    operands = [f'「{event}」の一方で「{feeling}」' for event, feeling in pairs]
    crossed = list(pairs)
    crossed[0], crossed[1] = (pairs[0][0], pairs[1][1]), (pairs[1][0], pairs[0][1])
    changed = {
        'drop_pair': '、また'.join(operands[1:]) + 'とあります。',
        'swap_reactions': '、また'.join(f'「{e}」の一方で「{f}」' for e, f in crossed) + 'とあります。',
        'reverse_pairs': '、また'.join(reversed(operands)) + 'とあります。',
        'cause': report.replace('」の一方で「', '」ので「', 1),
        'unrelated': report.replace('」の一方で「', '」そして「', 1),
        'duplicate_pair': report.replace('とあります。', '、また' + operands[0] + 'とあります。'),
        'extra_clause': report.replace('とあります。', 'とあり、気持ちが改善しています。'),
        'extra_sentence': report + '気持ちが改善しています。',
        'quoted_extra_sentence': report + f'「{pairs[0][0]}」から気持ちが改善しています。',
        'negation': report.replace(f'「{pairs[-1][1]}」', '「寂しくなかった」', 1),
    }[mutation]
    assert changed != report and report in context[0].artifact.text
    with patch.object(surface, '_render_relation', side_effect=AssertionError('no author oracle')):
        assert not read_body(context, context[0].artifact.text.replace(report, changed, 1)).passed


def test_parallel_report_keeps_complete_legacy_reading(parallel_report_context):
    from test_cmee_emlis_detached_observation import read_body
    context, pairs, report = parallel_report_context
    old = '、また'.join(f'「{e}」の一方で「{f}」' for e, f in pairs) + 'という、それぞれ異なる向きが並んでいます。'
    with patch.object(surface, '_render_relation', side_effect=AssertionError('no author oracle')):
        assert read_body(context, context[0].artifact.text.replace(report, old, 1)).passed


@pytest.mark.parametrize('connector', ['けど', 'けれど', 'けれども'])
def test_parallel_report_does_not_add_expectation_violation(connector):
    from test_cmee_emlis_detached_observation import read_body
    memo = f'誘われた{connector}、悲しかった。頼まれた{connector}、寂しかった。'
    context = actual(request=begin(memo))
    report = '「誘われた」の一方で「悲しかった」、また「頼まれた」の一方で「寂しかった」とあります。'
    body = context[0].artifact.text
    assert context[0].artifact.observation == report
    with patch.object(surface, '_render_relation', side_effect=AssertionError('no author oracle')):
        assert read_body(context, body).passed
        assert not read_body(context, body.replace(report, report.replace('の一方で', 'のに', 1), 1)).passed


@pytest.mark.parametrize('old,new', [
    ('あまり悲しくなかった', '悲しくなかった'),
    ('あまり悲しくなかった', '友人はあまり悲しくなかった'),
    ('あまり悲しくなかった', 'あまり悲しかった'),
    ('とても寂しかった', 'とても寂しい'),
])
def test_parallel_report_preserves_each_sources_qualifiers(old, new):
    from test_cmee_emlis_detached_observation import read_body
    context = actual(request=begin('断られたのに、あまり悲しくなかった。誘われたのに、とても寂しかった。'))
    body = context[0].artifact.text
    assert '、また「誘われた」の一方で「とても寂しかった」とあります。' in body
    changed = body.replace(f'「{old}」', f'「{new}」', 1)
    assert changed != body
    with patch.object(surface, '_render_relation', side_effect=AssertionError('no author oracle')):
        assert not read_body(context, changed).passed


def test_parallel_report_cannot_move_before_its_answered_event():
    from test_cmee_emlis_detached_observation import read_body
    context = actual(request=advance(begin(), '今は嬉しい。'))
    obs = context[0].artifact.observation
    first, rest = obs.split('。 ', 1)
    changed = context[0].artifact.text.replace(obs, rest + ' ' + first + '。', 1)
    assert changed != context[0].artifact.text
    assert not read_body(context, changed).passed


@pytest.mark.parametrize('memo', [
    '褒められたのに、嬉しくなかった。',
    '誘われたのに、悲しかった。誘われたのに、悲しかった。',
])
def test_parallel_report_does_not_replace_single_or_ambiguous_sources(memo):
    from test_cmee_emlis_detached_observation import read_body
    context = actual(request=begin(memo))
    assert 'とあります。' not in context[0].artifact.observation
    assert read_body(context, context[0].artifact.text).passed


@pytest.mark.parametrize('withdraw', ['褒められた', '誘われた'])
def test_parallel_report_saved_flow_preserves_original_and_reuses_dto(qcase, monkeypatch, withdraw):
    from test_emlis_q3_application import cont
    user, parent, service = qcase
    first = current = run(service.start(user, parent))
    assert '、また「誘われた」の一方で「悲しかった」、また「頼まれた」の一方で「寂しかった」とあります。' in current['current_observation']['text']
    for i, reply in enumerate(('今は嬉しい。', '「嬉しい」ではなく「少し楽しい」です。', f'「{withdraw}」は誤りです。')):
        if i:
            current = run(cont(service, user, current, f'parallel-report-continue-{i}'))
        current = run(answer(service, user, current, reply, f'parallel-report-answer-{i}'))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        body = current['current_observation']['text']
        if i < 2:
            assert '「誘われた」の一方で「悲しかった」、また「頼まれた」の一方で「寂しかった」とあります。' in body
        else:
            assert withdraw not in body
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved read must not regenerate'))
            assert run(service.get(user, parent)) == current
            assert run(service.start(user, parent)) == current
    assert current['state'] == 'COMPLETED' and not current['can_continue']


RECEIVED_CHAIN = '褒められたのに、悲しかったけれど嬉しかった。'
RECEIVED_CHAIN_MULTI = RECEIVED_CHAIN + '誘われたのに寂しかった。頼まれたのに怖かった。'


@pytest.mark.parametrize('memo', [RECEIVED_CHAIN, RECEIVED_CHAIN_MULTI])
@pytest.mark.parametrize('reply,retained,removed,edges', [
    ('今は少し苦しい。', ('悲しかった', '嬉しかった', '少し苦しい'), (), 2),
    ('「悲しかった」ではなく「少し怖かった」です。', ('嬉しかった', '少し怖かった'), ('悲しかった',), 0),
    ('「嬉しかった」ではなく「少し不安だった」です。', ('悲しかった', '少し不安だった'), ('嬉しかった',), 1),
    ('「褒められた」は誤りです。', ('悲しかった', '嬉しかった'), ('褒められた',), 1),
    ('「悲しかった」は誤りです。', ('褒められた', '嬉しかった'), ('悲しかった',), 0),
    ('「嬉しかった」は誤りです。', ('褒められた', '悲しかった'), ('嬉しかった',), 1),
])
def test_received_chain_update_keeps_only_surviving_source_relations(memo, reply, retained, removed, edges):
    from test_cmee_emlis_detached_observation import read_body
    context = actual(request=advance(begin(memo), reply))
    body = context[0].artifact.text
    assert all(text in body for text in retained) and all(text not in body for text in removed)
    assert '一つの流れ' not in body and '今は、「' not in body and '変化' not in body
    relations = [r for r in context[1].relations if r.type == 'contrast' and r.source_span_ids == ('s1',)]
    assert len(relations) == edges
    if '少し怖かった' in reply:
        assert '嬉しかった' in context[0].artifact.reception
    if memo == RECEIVED_CHAIN_MULTI:
        assert all(text in body for text in ('誘われた', '寂しかった', '頼まれた', '怖かった'))
        assert all(text in context[0].artifact.reception for text in ('誘われた', '寂し', '頼まれた', '怖'))
    assert read_body(context, body).passed


@pytest.mark.parametrize('reply', ['今は少し苦しい。', 'その時は少し苦しかった。', '今は少し嬉しい。'])
def test_received_chain_three_rounds_keep_answer_time_and_unrelated_groups(reply):
    from test_cmee_emlis_detached_observation import read_body
    replacement = '少し怖かった' if 'その時' in reply else '少し怖い'
    old = reply.removeprefix('今は').removeprefix('その時は').removesuffix('。')
    request = begin(RECEIVED_CHAIN_MULTI)
    bodies = []
    for text in (reply, f'「{old}」ではなく「{replacement}」です。', '「褒められた」は誤りです。'):
        request = advance(request, text)
        context = actual(request=request)
        body = context[0].artifact.text
        assert read_body(context, body).passed
        assert all(source in body for source in ('悲しかった', '嬉しかった', '誘われた', '寂しかった', '頼まれた', '怖かった'))
        bodies.append(body)
    assert '褒められた' not in bodies[-1] and old not in bodies[-1]
    assert replacement in bodies[-1] and ('その時' if 'その時' in reply else '先の回答時点') in bodies[-1]


@pytest.mark.parametrize('old,new', [
    ('「褒められた」という出来事がありました。「嬉しかった」という気持ちが書かれています。',
     '「褒められた」から「嬉しかった」へ変わりました。'),
    ('「嬉しかった」という気持ちが書かれています。', '「嬉しい」という気持ちが書かれています。'),
])
def test_received_chain_withdrawal_inverse_cannot_reconnect_survivors(old, new):
    from test_cmee_emlis_detached_observation import read_body
    context = actual(request=advance(begin(RECEIVED_CHAIN_MULTI), '「悲しかった」は誤りです。'))
    body = context[0].artifact.text
    changed = body.replace(old, new, 1)
    assert changed != body and read_body(context, body).passed
    assert not read_body(context, changed).passed


@pytest.mark.parametrize('reply', ['今は少し苦しい。', '「悲しかった」ではなく「少し怖かった」です。',
                                   '「褒められた」は誤りです。', '「悲しかった」は誤りです。'])
def test_received_chain_saved_update_and_original_replay(qcase, qdb, monkeypatch, reply):
    user, parent, service = qcase
    qdb.query('update public.emotions set memo=$1 where id=$2', [RECEIVED_CHAIN_MULTI, parent])
    first = run(service.start(user, parent))
    assert '悲しかったけれど、嬉しかったのですね' in first['current_observation']['text']
    with monkeypatch.context() as saved:
        saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved initial body must not regenerate'))
        assert run(service.get(user, parent)) == first
        assert run(service.start(user, parent)) == first
    current = run(answer(service, user, first, reply, 'received-chain-update'))
    assert current['body_state'] == 'REFINED' and current['original'] == first['original']
    assert '嬉しかった' in current['current_observation']['text']
    with monkeypatch.context() as saved:
        saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved revised body must not regenerate'))
        assert run(service.get(user, parent)) == current
        assert run(service.start(user, parent)) == current


def test_received_chain_saved_three_round_sequence(qcase, qdb, monkeypatch):
    from test_emlis_q3_application import cont
    user, parent, service = qcase
    qdb.query('update public.emotions set memo=$1 where id=$2', [RECEIVED_CHAIN_MULTI, parent])
    first = run(service.start(user, parent))
    current = first
    for index, reply in enumerate(('今は少し苦しい。', '「少し苦しい」ではなく「少し怖い」です。', '「褒められた」は誤りです。')):
        if index:
            current = run(cont(service, user, current, 'received-chain-continue-' + str(index)))
        current = run(answer(service, user, current, reply, 'received-chain-answer-' + str(index)))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved round must not regenerate'))
            assert run(service.get(user, parent)) == current
            assert run(service.start(user, parent)) == current
    body = current['current_observation']['text']
    assert '褒められた' not in body and '少し苦しい' not in body
    assert all(text in body for text in ('悲しかった', '嬉しかった', '先の回答時点', '少し怖い', '誘われた', '頼まれた'))


@pytest.mark.parametrize('withdraw', [False, True])
def test_received_chain_event_owner_cannot_become_emlis_first_person(withdraw):
    from test_cmee_emlis_detached_observation import read_body
    request = begin('私は褒められたのに、悲しかったけど嬉しかった。')
    if withdraw:
        request = advance(request, '「嬉しかった」は誤りです。')
    context = actual(request=request)
    body = context[0].artifact.text
    changed = body.replace('あなたは褒められた', '私は褒められた')
    assert changed != body and read_body(context, body).passed
    assert not read_body(context, changed).passed


@pytest.mark.parametrize('memo', [
    '褒められたのに、嬉しくなかった。誘われたのに、悲しかった。頼まれたのに、寂しかった。',
    OWNED_INITIAL,
    '誘われたのに悲しかった。頼まれたのに寂しかった。',
    '断られたのにあまり悲しくなかった。誘われたのにとても寂しかった。',
])
@pytest.mark.parametrize('reply,answer_fragment', [
    ('今は少し苦しい。', '回答した時点では少し苦しい'),
    ('今は私も少し不安です。', '回答した時点ではあなたも少し不安な'),
])
def test_answer_scope_closes_before_unanswered_original_occasions(memo, reply, answer_fragment):
    from test_cmee_emlis_detached_observation import read_body
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    context = actual(request=advance(begin(memo), reply))
    result, plan, _, resolver, _ = context
    follow = result.artifact.reception
    sentences = tuple(s for s in follow.split('。') if s)
    assert len(sentences) == 2 and answer_fragment in sentences[0]
    assert '回答した時点' not in sentences[1] and '少し苦し' not in sentences[1]
    moves = plan.response_plan.human_reception_plan.moves
    assert tuple(m.move_role for m in moves) == ('attention', 'felt_response')
    assert plan.response_plan.human_reception_plan.depth_policy.max_sentences == 2
    owned = [set((*m.target_nucleus_ids, *m.support_nucleus_ids)) for m in moves]
    assert owned[0].isdisjoint(owned[1])
    text_ids = {n.nucleus_id for n in plan.nuclei if n.retention == 'required'
                and set(n.source_fields) & {'memo', 'memo_action', 'answer_text_private'}}
    assert set.union(*owned) == text_ids
    for relation in plan.relations:
        if relation.relation_id in plan.coverage_requirements.required_relation_ids:
            assert sum({relation.from_nucleus_id, relation.to_nucleus_id} <= ids for ids in owned) == 1
    index = {n.nucleus_id: n for n in plan.nuclei}
    for position, move in enumerate(moves):
        for nid in move.target_nucleus_ids:
            event = reception.final_reception_source_anchor_text(nid, index, resolver)
            assert event in sentences[position] and event not in sentences[1 - position]
    assert MeaningExperienceEngine().generate(advance(begin(memo), reply)).artifact.text == result.artifact.text
    assert read_body(context, result.artifact.text).passed


@pytest.fixture(scope='module')
def answer_scope_context():
    return actual(request=advance(begin(OWNED_INITIAL), '今は少し苦しい。'))


@pytest.mark.parametrize('mutation', [
    'drop_answer_sentence', 'drop_original_sentence', 'swap_sentences', 'duplicate_answer',
    'drop_answer', 'time', 'tense', 'degree', 'polarity', 'owner', 'cause', 'swap_events',
])
def test_answer_scope_meaning_cannot_be_borrowed_across_sentences(answer_scope_context, mutation):
    from test_cmee_emlis_detached_observation import read_body
    context = answer_scope_context
    body, follow = context[0].artifact.text, context[0].artifact.reception
    first, second, empty = follow.split('。')
    assert empty == '' and read_body(context, body).passed
    changes = {
        'drop_answer_sentence': second + '。',
        'drop_original_sentence': first + '。',
        'swap_sentences': second + '。' + first + '。',
        'duplicate_answer': first + '。' + first + '。' + second + '。',
        'drop_answer': follow.replace('し、回答した時点では少し苦しい', ''),
        'time': follow.replace('回答した時点では', 'その時は'),
        'tense': follow.replace('少し苦しい', '少し苦しかった'),
        'degree': follow.replace('少し苦しい', '苦しい'),
        'polarity': follow.replace('少し苦しい', '少し苦しくない'),
        'owner': follow.replace('あなたも少し不安だった', '友人も少し不安だった'),
        'cause': follow.replace('誘われたのに', '誘われたから'),
        'swap_events': follow.replace('誘われた', 'TEMP').replace('頼まれた', '誘われた').replace('TEMP', '頼まれた'),
    }
    changed = body.replace(follow, changes[mutation])
    assert changed != body and not read_body(context, changed).passed


@pytest.mark.parametrize('memo,event', [
    ('褒められたのに、嬉しくなかった。誘われたのに、悲しかった。頼まれたのに、寂しかった。', '褒められた'),
    (OWNED_INITIAL, '誘われた'),
])
@pytest.mark.parametrize('withdraw_event', [False, True])
def test_answer_scope_correction_withdrawal_and_saved_replay(qcase, qdb, monkeypatch, memo, event, withdraw_event):
    from test_emlis_q3_application import cont
    user, parent, service = qcase
    qdb.query('update public.emotions set memo=$1 where id=$2', [memo, parent])
    first = current = run(service.start(user, parent))
    sequence = ('今は少し苦しい。', '「少し苦しい」ではなく「少し怖い」です。',
                '「' + (event if withdraw_event else '少し怖い') + '」は誤りです。')
    with monkeypatch.context() as saved:
        saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('initial replay must not generate'))
        assert run(service.get(user, parent)) == run(service.start(user, parent)) == first
    for position, text in enumerate(sequence):
        if position:
            current = run(cont(service, user, current, f'scope-continue-{position}'))
        current = run(answer(service, user, current, text, f'scope-answer-{position}'))
        assert current['original'] == first['original'] and current['body_state'] == 'REFINED'
        body = current['current_observation']['text']
        follow = body.split('Emlisから：', 1)[1].strip()
        if position < 2:
            sentences = tuple(s for s in follow.split('。') if s)
            assert len(sentences) == 2 and event in sentences[0] and event not in sentences[1]
            assert ('回答した時点では少し苦しい' if position == 0 else '先の回答時点では少し怖い') in sentences[0]
        else:
            assert '少し苦しい' not in body
            if withdraw_event:
                assert event not in body and '先の回答時点' in body and '少し怖い' in body
            else:
                assert '少し怖い' not in body and event in body
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved response must not generate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current


def test_answer_scope_moves_to_last_event_without_reordering_middle():
    from test_cmee_emlis_detached_observation import read_body
    request = begin()
    for position, text in enumerate(('今は少し苦しい。',
            '「少し苦しい」は誤りです。今は少し怖い。',
            '「少し怖い」は誤りです。今は少し重い。')):
        request = advance(request, text)
        context = actual(request=request)
        body, follow = context[0].artifact.text, context[0].artifact.reception
        sentences = tuple(s for s in follow.split('。') if s)
        assert len(sentences) == (1 if position == 1 else 2)
        assert follow.index('褒められた') < follow.index('誘われた') < follow.index('頼まれた')
        if position == 2:
            assert '頼まれた' not in sentences[0]
            assert '頼まれた時は寂しく、回答した時点では少し重い' in sentences[1]
            assert '回答した時点' not in sentences[0]
        if position:
            assert '少し苦しい' not in body
        if position == 2:
            assert '少し怖い' not in body
        assert read_body(context, body).passed


def test_answer_scope_last_event_saved_withdraw_and_add(qcase, qdb, monkeypatch):
    from test_emlis_q3_application import cont
    user, parent, service = qcase
    first = current = run(service.start(user, parent))
    for position, text in enumerate(('今は少し苦しい。',
            '「少し苦しい」は誤りです。今は少し怖い。',
            '「少し怖い」は誤りです。今は少し重い。')):
        if position:
            current = run(cont(service, user, current, f'scope-edge-continue-{position}'))
        current = run(answer(service, user, current, text, f'scope-edge-answer-{position}'))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved edge response must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current
    body = current['current_observation']['text']
    follow = body.split('Emlisから：', 1)[1].strip().split('。')
    assert len(follow) == 3 and '頼まれた' not in follow[0]
    assert '頼まれた時は寂しく、回答した時点では少し重い' in follow[1]
    assert '少し苦しい' not in body and '少し怖い' not in body


@pytest.mark.parametrize('source', [
    '私は私には怖かったです', '私は私には不安です', '私は私には不安なのです',
])
def test_answer_scope_nominal_fallback_keeps_source_and_attention(source):
    from test_cmee_emlis_detached_observation import read_body
    context = actual(request=advance(begin(), '今は' + source + '。'))
    body, follow = context[0].artifact.text, context[0].artifact.reception
    assert read_body(context, body).passed
    first, second, empty = follow.split('。')
    assert empty == '' and 'あなたは私には' in first
    assert 'に目が留まり、それを小さくせずに受け止めています' in first
    assert '誘われた' in second and '頼まれた' in second and '回答した時点' not in second
    corruptions = [
        follow.replace('あなたは私には', 'あなたには', 1),
        follow.replace('回答した時点で', 'その時に', 1),
        follow.replace('褒められた', '誘われた', 1),
        follow.replace('嬉しくなかった', '嬉しかった', 1),
        follow.replace('目が留まり、', '目が留まらず、', 1),
        follow.replace('小さくせずに', '小さくして', 1),
        first + '。',
        second + '。' + first + '。',
    ]
    for corrupt in corruptions:
        changed = body.replace(follow, corrupt)
        assert changed != body and not read_body(context, changed).passed
        assert not inverse(context, corrupt, without_author=True).passed
