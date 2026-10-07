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
    # Keep each existing case and semantic mutation when its admitted
    # PERCEIVED answer is expressed as a finite clause rather than a noun.
    old, new = {
        ('嬉しさにはつながらず', '嬉しさにつながり'): ('嬉しくなかった', '嬉しかった'),
        ('嬉しさにはつながらず、', ''): ('嬉しくなかったし、', ''),
        ('求められるような', '求められるための'): ('求められるようで', '求められるので'),
        ('重さ', '軽さ'): ('重かった', '軽かった'),
        ('重さ', '苦しさ'): ('重かった', '苦しかった'),
        ('届いた', '届いている'): ('重かった', '重い'),
        ('褒められたことは', '友人が褒められたことは'): ('褒められたのに', '友人が褒められたのに'),
        ('褒められたことは', '今、褒められたことは'): ('褒められたのに', '今、褒められたのに'),
        ('求められるような', '求められないような'): ('求められるようで', '求められないようで'),
    }.get((old, new), (old, new))
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
    assert follow.count('のですね') == (2 if len(sequence) == 1 else 3)
    assert 'を見失わず、小さくせずに受け止めています' not in follow
    groups = ((0,), (1, 2)) if len(sequence) == 1 else ((0,), (1,), (2,))
    assert_complete_occasion_scopes(context, ('褒められた', '誘われた', '頼まれた'), groups)
    for event in ('褒められた','誘われた','頼まれた'):
        assert follow.count(event)==1
    assert gate.read_received_discourse(follow.split('。')[0] + '。',plan.response_plan.human_reception_plan.moves[0],
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
    assert memo.rstrip('。') + 'し、' in follow
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
    anchors = {'褒められた時は': '褒められたのに、', '誘われた時は': '誘われたのに、',
               '彼が褒められた時は': '彼が褒められたのに、',
               '嬉しくなく、': '嬉しくなかったし、', '嬉しく、': '嬉しかったし、'}
    changed = follow.replace(anchors.get(old, old), anchors.get(new, new))
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
    assert '褒められたのに、嬉しくなかったし、回答した時点では' in follow
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
            assert event + 'のに、' + feeling + 'し、回答した時点では' + source in follow
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
    anchors = {'褒められた時は': '褒められたのに、', '誘われた時は': '誘われたのに、',
               '友人が褒められた時は': '友人が褒められたのに、',
               '嬉しくなく、': '嬉しくなかったし、', '嬉しく、': '嬉しかったし、'}
    old, new = anchors.get(old, old), anchors.get(new, new)
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
            assert f'褒められたのに、嬉しくなかったし、回答した時点では{source}' in follow
        elif index == 1:
            if operation == 'correct':
                assert f'褒められたのに、嬉しくなかったし、先の回答時点では{replacement}' in follow
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
            original = ('嬉しくなかった', '悲しかった', '寂しかった')[index]
            assert event + 'のに、' + original + 'し、回答した時点では' + source in follow
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
    anchors = {
        '褒められた時は': '褒められたのに、',
        '友人が褒められた時は': '友人が褒められたのに、',
        '嬉しくなく、': '嬉しくなかったし、', '悲しく、': '悲しかったし、',
        '褒められた時は嬉しくなく、回答した時点ではまだよく分からないし、':
            '褒められたのに、嬉しくなかったし、回答した時点ではまだよく分からないし、',
        '誘われた時は悲しく、回答した時点では分からないし、':
            '誘われたのに、悲しかったし、回答した時点では分からないし、',
    }
    old, new = anchors.get(old, old), anchors.get(new, new)
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
        if index == 2 and operation == 'withdraw_first':
            assert '褒められたことは、嬉しさにはつながらなかったし、' in follow
        else:
            scope = '先の回答時点では' if index == 2 and operation == 'correct_first' else '回答した時点では'
            retained = '分からない' if index == 2 and operation == 'correct_first' else 'まだよく分からない'
            assert '褒められたのに、嬉しくなかったし、' + scope + retained in follow
        assert '悲し' in follow and '寂し' in follow
        if index < 2:
            assert '回答した時点ではまだよく分からない' in follow
            assert '誘われた' in follow
            if index == 1:
                assert ('怖かった' if second == MULTI_NEGATIVE else '回答した時点では分からない') in follow
        elif operation == 'correct_first':
            assert '先の回答時点では分からない' in follow and 'まだよく' not in follow and '怖かった' in follow
        elif operation == 'withdraw_first':
            assert 'まだよく' not in follow and '誘われたのに、悲しかったし、回答した時点では分からない' in follow
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
    assert '褒められたのに、嬉しくなかったし、回答した時点ではまだよく分からない' in follow
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
    original = ('嬉しくなかった', '悲しかった', '寂しかった')[position]
    time = 'その時は' if other == MULTI_NEGATIVE else '回答した時点では'
    assert event + 'のに、' + original + 'し、' + time in follow
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
    anchors = {'嬉しくなく': '嬉しくなかったし、', '嬉しく': '嬉しかったし、'}
    old, new = anchors.get(old, old), anchors.get(new, new)
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


@pytest.mark.parametrize('count,slot', [(2, 0), (2, 1), (3, 0), (3, 1), (3, 2)])
@pytest.mark.parametrize('reply,replacement,retained', [
    ('その時は少し苦しかった。', '少し怖かった', '少し怖かった'),
    ('今は少し苦しい。', '私も少し不安でした', 'あなたも少し不安だった'),
    ('その時は少し苦しかった。', '私には少し不安だったのです', 'あなたには少し不安だった'),
    ('今は少し苦しい。', '私も少し怖くなかった', 'あなたも少し怖くなかった'),
])
def test_current_original_revision_separates_about_owned_occasions(count, slot, reply, replacement, retained):
    from test_cmee_emlis_q3_thread import MEMO
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    events = ('褒められた', '誘われた', '頼まれた')[:count]
    removed = ('嬉しくなかった', '悲しかった', '寂しかった')[slot]
    request = begin('。'.join(MEMO.split('。')[:count]) + '。')
    for text in (reply, 'その時は少し重かった。')[:slot]:
        request = advance(request, text)
    request = advance(request, '「' + removed + '」ではなく「' + replacement + '」です。')
    context = actual(request=request)
    result, plan, _, _, _ = context
    follow = result.artifact.reception
    sentences = follow.split('。')[:-1]
    assert len(sentences) == min(count, slot + 2)
    assert retained in sentences[slot] and removed not in result.artifact.text
    for position in range(slot + 1):
        assert events[position] in sentences[position]
        assert all(event not in sentences[position] for event in events if event != events[position])
    if slot:
        assert ('回答した時点では少し苦しい' if reply.startswith('今は') else '少し苦しかった') in sentences[0]
    event_id = f'nucleus:s{slot + 1}:event'
    assert not any(n.nucleus_id == f'nucleus:s{slot + 1}:reaction' for n in plan.nuclei)
    about = [r for r in plan.relations if r.type == 'evaluation_about_event' and r.from_nucleus_id == event_id]
    assert len(about) == 1
    moves = plan.response_plan.human_reception_plan.moves
    owned = [set((*m.target_nucleus_ids, *m.support_nucleus_ids)) for m in moves]
    assert len(moves) == len(sentences)
    assert {event_id, about[0].to_nucleus_id} in owned
    assert all(a.isdisjoint(b) for i, a in enumerate(owned) for b in owned[i+1:])
    for relation in plan.relations:
        if relation.retention == 'required':
            assert sum({relation.from_nucleus_id, relation.to_nucleus_id} <= ids for ids in owned) == 1
    assert MeaningExperienceEngine().generate(request).artifact.text == result.artifact.text
    assert inverse(context, follow, without_author=True).passed
    polarity = retained.replace('怖くなかった', '怖かった') if '怖くなかった' in retained else (
        retained.replace('怖かった', '怖くなかった').replace('不安だった', '不安ではなかった'))
    timed = sentences[slot].replace('その時に', '回答した時点で') if 'その時に' in sentences[slot] else (
        sentences[slot].replace('時は', '今は'))
    mutations = [follow.replace(events[slot], events[(slot + 1) % count], 1),
                 follow.replace(retained, retained.replace('少し', ''), 1),
                 follow.replace(retained, polarity, 1), follow.replace(sentences[slot], timed, 1),
                 follow.replace(sentences[slot] + '。', '', 1),
                 follow.replace(sentences[slot], sentences[(slot + 1) % len(sentences)], 1)]
    if 'あなた' in retained:
        mutations += [follow.replace('あなた', '相手', 1), follow.replace('あなたも', 'あなたは', 1)
                      if 'あなたも' in retained else follow.replace('あなたには', 'あなたも', 1)]
    for changed in mutations:
        assert changed != follow and not inverse(context, changed, without_author=True).passed


@pytest.mark.parametrize('count', [2, 3])
@pytest.mark.parametrize('reply,retained', [(A, '求められるような重さ'),
    (B, '見てもらえていないと思った'), (C, '自分ではまだ納得していなかった')])
def test_current_original_revision_keeps_other_answer_interpretation(count, reply, retained):
    from test_cmee_emlis_q3_thread import MEMO
    if reply == A:
        retained = '求められるようで、重かった'
    memo = '。'.join(MEMO.split('。')[:count]) + '。'
    context = actual(request=advance(advance(begin(memo), reply), '「悲しかった」ではなく「少し怖かった」です。'))
    follow = context[0].artifact.reception
    sentences = follow.split('。')[:-1]
    assert len(sentences) == count
    assert '褒められた' in sentences[0] and retained in sentences[0] and '誘われた' not in sentences[0]
    assert '誘われた' in sentences[1] and '少し怖かった' in sentences[1] and '褒められた' not in sentences[1]
    assert inverse(context, follow, without_author=True).passed
    changed = follow.replace('ようで', 'ために') if reply == A else (
        follow.replace('いないと思った', 'いない') if reply == B else follow.replace('まだ', ''))
    assert changed != follow and not inverse(context, changed, without_author=True).passed


@pytest.mark.parametrize('count,replies', [
    (2, ('今は少し苦しい。', '「悲しかった」ではなく「少し怖かった」です。')),
    (3, ('その時は少し苦しかった。', '「悲しかった」ではなく「少し怖かった」です。',
         '「少し怖かった」ではなく「少し寂しかった」です。')),
    (3, ('その時は少し苦しかった。', '「悲しかった」ではなく「少し怖かった」です。',
         '「少し怖かった」は誤りです。')),
    (3, ('その時は少し苦しかった。', 'その時は少し重かった。', '「寂しかった」ではなく「少し怖かった」です。')),
])
def test_current_original_revision_separation_saved_updates(qcase, qdb, monkeypatch, count, replies):
    from test_cmee_emlis_q3_thread import MEMO
    from test_emlis_q3_application import cont
    user, parent, service = qcase
    qdb.query('update public.emotions set memo=$1 where id=$2', ['。'.join(MEMO.split('。')[:count]) + '。', parent])
    first = current = run(service.start(user, parent))
    for position, reply in enumerate(replies):
        if position:
            current = run(cont(service, user, current, f'about-revision-continue-{position}'))
        current = run(answer(service, user, current, reply, f'about-revision-answer-{position}'))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        body = current['current_observation']['text']
        if 'ではなく' in reply:
            follow = body.split('Emlisから：', 1)[1].strip()
            sentences = follow.split('。')[:-1]
            assert len(sentences) == count
            assert all(event in sentences[i] for i, event in enumerate(('褒められた', '誘われた', '頼まれた')[:count]))
            assert '褒められた' not in sentences[1] and '誘われた' not in sentences[0]
            old = reply.split('「')[1].split('」')[0]
            new = reply.split('「')[2].split('」')[0]
            assert old not in body and new in body
        if reply == '「少し怖かった」は誤りです。':
            assert '少し怖かった' not in body and '悲しかった' not in body
            assert '褒められた' in body and '頼まれた' in body and '少し苦しかった' in body
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved current-target revision must not regenerate'))
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
        assert len(sentences) == (3 if position == 1 else 2)
        assert follow.index('褒められた') < follow.index('誘われた') < follow.index('頼まれた')
        if position == 2:
            assert '頼まれた' not in sentences[0]
            assert '頼まれたのに、寂しかったし、回答した時点では少し重い' in sentences[1]
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
    assert '頼まれたのに、寂しかったし、回答した時点では少し重い' in follow[1]
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
    assert empty == '' and '私は私には' in first and 'あなたは私には' not in first
    assert 'その出来事' not in first and 'という、回答した時点のあなたの気持ち' in first
    assert 'に目が留まり、それを小さくせずに受け止めています' in first
    assert '誘われた' in second and '頼まれた' in second and '回答した時点' not in second
    corruptions = [
        follow.replace('私は私には', '私には', 1),
        follow.replace('回答した時点の', 'その時の', 1),
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


@pytest.mark.parametrize('memo', [
    '褒められたのに、嬉しくなかった。誘われたのに、悲しかった。頼まれたのに、寂しかった。',
    OWNED_INITIAL,
])
@pytest.mark.parametrize('sequence,retained,removed', [
    (('今は少し苦しい。', '今は少し怖い。'), ('少し苦しい', '少し怖い'), ()),
    (('今は少し苦しい。', '今は少し怖い。', '今は少し重い。'), ('少し苦しい', '少し怖い', '少し重い'), ()),
    (('今は少し苦しい。', '「少し苦しい」は誤りです。今は少し怖い。'), ('少し怖い',), ('少し苦しい',)),
    (('今は少し苦しい。', '今は少し怖い。', '「少し怖い」ではなく「少し寂しい」です。'),
     ('少し苦しい', '先の回答時点で少し寂しい'), ('少し怖い',)),
    (('今は少し苦しい。', '今は少し怖い。', '「少し怖い」は誤りです。今は少し重い。'),
     ('少し苦しい', '少し重い'), ('少し怖い',)),
    (('今は少し不安です。', '今は私も少しもやもやでした。'),
     ('あなたも少しもやもやだったこと',), ('もやもやでしたこと',)),
    (('今は少し苦しい。', '今は少し私は不安です。'),
     ('あなたは少し不安なこと',), ('不安ですこと', '少し私は不安')),
])
def test_middle_and_multiple_answers_keep_complete_occasion_scopes(memo, sequence, retained, removed):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    request = begin(memo)
    for text in sequence:
        request = advance(request, text)
    context = actual(request=request)
    result, plan, _, resolver, _ = context
    follow = result.artifact.reception
    sentences = tuple(s for s in follow.split('。') if s)
    moves = plan.response_plan.human_reception_plan.moves
    assert len(sentences) == len(moves) == 3
    assert tuple(m.move_role for m in moves) == ('attention', 'significance', 'felt_response')
    assert 'その出来事' not in sentences[1]
    retained = tuple({
        "先の回答時点で少し寂しい": "先の回答時点では少し寂しい",
        "あなたも少しもやもやだったこと": "あなたも少しもやもやだったのですね",
        "あなたは少し不安なこと": "あなたは少し不安なのですね",
    }.get(value, value) for value in retained)
    assert all(value in follow for value in retained) and all(value not in follow for value in removed)
    owned = [set((*m.target_nucleus_ids, *m.support_nucleus_ids)) for m in moves]
    assert all(owned[i].isdisjoint(owned[j]) for i in range(3) for j in range(i + 1, 3))
    required = {n.nucleus_id for n in plan.nuclei if n.retention == 'required'
                and set(n.source_fields) & {'memo', 'memo_action', 'answer_text_private'}}
    assert set.union(*owned) == required
    index = {n.nucleus_id: n for n in plan.nuclei}
    events = tuple(part.split('のに')[0].split('けど')[0] for part in memo.split('。') if part)
    for position, event in enumerate(events):
        assert event in sentences[position]
        assert all(event not in sentence for i, sentence in enumerate(sentences) if i != position)
        for nid in moves[position].target_nucleus_ids:
            assert reception.final_reception_source_anchor_text(nid, index, resolver) == event
    for relation in plan.relations:
        if relation.relation_id in plan.coverage_requirements.required_relation_ids:
            assert sum({relation.from_nucleus_id, relation.to_nucleus_id} <= ids for ids in owned) == 1
    if memo == OWNED_INITIAL:
        ending = ('のですね' if '「少し怖い」は誤りです。今は少し重い。' in sequence else 'し、')
        assert '頼まれたのに、あなたは少し怖くなかった' + ending in sentences[1]
        assert '少し私は怖くなかったこと' not in follow
    assert inverse(context, follow, without_author=True).passed
    assert MeaningExperienceEngine().generate(request).artifact.text == result.artifact.text


@pytest.fixture(scope='module')
def multiple_answer_scope_context():
    return actual(request=advance(advance(begin(OWNED_INITIAL), '今は少し不安です。'),
                                  '今は私も少しもやもやでした。'))


@pytest.mark.parametrize('mutation', [
    'drop_middle', 'swap_sentences', 'drop_answer', 'time', 'tense', 'degree', 'polarity',
    'owner', 'answer_owner', 'answer_particle', 'cause', 'swap_events', 'drop_significance',
    'drop_original', 'drop_time', 'other_event_answer', 'swap_answers', 'quoted_answer',
])
def test_multiple_answer_scopes_reject_changed_meaning_without_author(multiple_answer_scope_context, mutation):
    context = multiple_answer_scope_context
    follow = context[0].artifact.reception
    first, middle, last, empty = follow.split('。')
    assert empty == '' and inverse(context, follow, without_author=True).passed
    changes = {
        'drop_middle': first + '。' + last + '。',
        'swap_sentences': middle + '。' + first + '。' + last + '。',
        'drop_answer': follow.replace('し、回答した時点ではあなたも少しもやもやだった', ''),
        'time': follow.replace('回答した時点ではあなたも', 'その時はあなたも'),
        'tense': follow.replace('もやもやだったのですね', 'もやもやなのですね'),
        'degree': follow.replace('あなたは少し怖くなかった', 'あなたは怖くなかった'),
        'polarity': follow.replace('怖くなかったし', '怖かったし'),
        'owner': follow.replace('あなたは少し怖くなかった', '友人は少し怖くなかった'),
        'answer_owner': follow.replace('あなたも少しもやもや', '友人も少しもやもや'),
        'answer_particle': follow.replace('あなたも少しもやもや', 'あなたは少しもやもや'),
        'cause': follow.replace('頼まれたのに', '頼まれたから'),
        'swap_events': follow.replace('誘われた', 'TEMP').replace('頼まれた', '誘われた').replace('TEMP', '頼まれた'),
        'drop_significance': follow.replace(middle, middle.removesuffix('のですね')),
        'drop_original': follow.replace('頼まれたのに、あなたは少し怖くなかったし、', ''),
        'drop_time': follow.replace('回答した時点ではあなたも', 'あなたも'),
        'other_event_answer': follow.replace('し、回答した時点ではあなたも',
                                            'し、誘われたことについて、回答した時点ではあなたも'),
        'swap_answers': follow.replace('少し不安な', 'TEMP').replace(
            'あなたも少しもやもやだった', '少し不安な').replace('TEMP', 'あなたも少しもやもやだった'),
        'quoted_answer': follow.replace('回答した時点ではあなたも少しもやもやだったのですね',
                                       '「回答した時点ではあなたも少しもやもやだったのですね」'),
    }
    assert changes[mutation] != follow
    assert not inverse(context, changes[mutation], without_author=True).passed


@pytest.mark.parametrize('source', [
    '私は私には怖かったです', '私は私には不安です', '私は私には不安なのです',
])
def test_original_time_group_keeps_explicit_event_reference(source):
    context = actual(request=advance(begin(), 'その時は' + source + '。'))
    follow = context[0].artifact.reception
    assert '褒められたのに嬉しくなかったことと、私は私には' in follow
    assert 'その出来事について、' not in follow
    assert 'という、その時のあなたの気持ち' in follow
    assert inverse(context, follow, without_author=True).passed
    changed = follow.replace('褒められたのに', '')
    assert changed != follow and not inverse(context, changed, without_author=True).passed


@pytest.mark.parametrize('memo,event', [
    ('褒められたのに、嬉しくなかった。誘われたのに、悲しかった。頼まれたのに、寂しかった。', '誘われた'),
    (OWNED_INITIAL, '頼まれた'),
])
@pytest.mark.parametrize('operation', ['add', 'correct', 'withdraw_answer', 'withdraw_event'])
def test_multiple_answer_scope_saved_update_and_replay(qcase, qdb, monkeypatch, memo, event, operation):
    from test_emlis_q3_application import cont
    user, parent, service = qcase
    qdb.query('update public.emotions set memo=$1 where id=$2', [memo, parent])
    first = current = run(service.start(user, parent))
    third = {'add': '今は少し重い。', 'correct': '「少し怖い」ではなく「少し寂しい」です。',
             'withdraw_answer': '「少し苦しい」は誤りです。',
             'withdraw_event': '「' + event + '」は誤りです。'}[operation]
    with monkeypatch.context() as saved:
        saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved initial response must not regenerate'))
        assert run(service.get(user, parent)) == run(service.start(user, parent)) == first
    for position, text in enumerate(('今は少し苦しい。', '今は少し怖い。', third)):
        if position:
            current = run(cont(service, user, current, f'multi-scope-continue-{position}'))
        current = run(answer(service, user, current, text, f'multi-scope-answer-{position}'))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        body = current['current_observation']['text']
        follow = body.split('Emlisから：', 1)[1].strip()
        if position == 1 or position == 2 and operation != 'withdraw_event':
            assert follow.count('。') == 3
        if position == 2:
            if operation == 'correct':
                assert '少し怖い' not in body and '先の回答時点では少し寂しい' in follow
            elif operation == 'withdraw_answer':
                assert '少し苦しい' not in body and '少し怖い' in body
            elif operation == 'withdraw_event':
                assert event not in body and '少し怖い' in body
            else:
                assert '少し重い' in body
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved multiple answer response must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current


@pytest.mark.parametrize('source,nominal', [
    ('私は少し不安です', 'あなたは少し不安なこと'),
    ('私は少し不安なのです', 'あなたは少し不安なのだということ'),
    ('私は少し不安だったのです', 'あなたは少し不安だったのだということ'),
    ('私は少し不安なのだった', 'あなたは少し不安なのだったということ'),
    ('少し私は怖いのです', 'あなたは少し怖いのだということ'),
    ('少し私は怖くなかったのです', 'あなたは少し怖くなかったのだということ'),
    ('私は私には不安です', 'あなたは私には不安なこと'),
    ('私は私には不安なのです', 'あなたは私には不安なのだということ'),
    ('私は私には不安でした', 'あなたは私には不安だったこと'),
    ('私は私には不安だったのです', 'あなたは私には不安だったのだということ'),
])
def test_middle_nominal_keeps_whole_copula_or_explanation(source, nominal):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    initial = begin()
    request = advance(advance(initial, '今は少し苦しい。'), '今は' + source + '。')
    context = actual(request=request)
    result, plan, _, _, _ = context
    follow = result.artifact.reception
    first, middle, last, empty = follow.split('。')
    assert empty == '' and '褒められた' in first and '頼まれた' in last
    owned = {
        '私は私には不安です': '私は私には不安だ',
        '私は私には不安なのです': '私は私には不安なのだ',
        '私は私には不安でした': '私は私には不安だった',
        '私は私には不安だったのです': '私は私には不安だったのだ',
    }
    finite = {
        '私は少し不安です': 'あなたは少し不安なのですね',
        '私は少し不安なのです': 'あなたは少し不安なのですね',
        '私は少し不安だったのです': 'あなたは少し不安だったのですね',
        '私は少し不安なのだった': 'あなたは少し不安なのでしたね',
        '少し私は怖いのです': 'あなたは少し怖いのですね',
        '少し私は怖くなかったのです': 'あなたは少し怖くなかったのですね',
    }
    expected = ('誘われたのに悲しかったことと、' + owned[source]
                + 'という、回答した時点のあなたの気持ち' if source in owned
                else '誘われたのに、悲しかったし、回答した時点では' + finite[source])
    assert expected in middle
    assert '少し苦しい' not in middle and '回答した時点' not in last
    assert not any(fragment in follow for fragment in ('ですこと', 'でしたこと', 'のなこと'))
    assert source in result.artifact.observation
    assert tuple(m.move_role for m in plan.response_plan.human_reception_plan.moves) == (
        'attention', 'significance', 'felt_response')
    assert request.current_input_bundle == initial.current_input_bundle
    assert inverse(context, follow, without_author=True).passed
    assert MeaningExperienceEngine().generate(request).artifact.text == result.artifact.text


@pytest.fixture(scope='module')
def explanatory_nominal_context():
    return actual(request=advance(advance(begin(OWNED_INITIAL), '今は少し苦しい。'),
                                  '今は私は少し不安だったのです。'))


@pytest.mark.parametrize('mutation', [
    'explanation', 'inner_past', 'outer_past', 'past_position', 'degree', 'owner',
    'particle', 'time', 'drop_time', 'swap_events', 'quoted', 'cause',
])
def test_explanatory_nominal_rejects_changed_meaning_without_author(explanatory_nominal_context, mutation):
    context = explanatory_nominal_context
    follow = context[0].artifact.reception
    assert inverse(context, follow, without_author=True).passed
    changes = {
        'explanation': follow.replace('不安だったのですね', '不安でしたね'),
        'inner_past': follow.replace('不安だったのですね', '不安なのですね'),
        'outer_past': follow.replace('不安だったのですね', '不安だったのでしたね'),
        'past_position': follow.replace('不安だったのですね', '不安なのでしたね'),
        'degree': follow.replace('少し不安だったのですね', '不安だったのですね'),
        'owner': follow.replace('あなたは少し不安だったの', '友人は少し不安だったの'),
        'particle': follow.replace('あなたは少し不安だったの', 'あなたも少し不安だったの'),
        'time': follow.replace('回答した時点ではあなたは', 'その時はあなたは'),
        'drop_time': follow.replace('回答した時点ではあなたは', 'あなたは'),
        'swap_events': follow.replace('誘われた', 'TEMP').replace('頼まれた', '誘われた').replace('TEMP', '頼まれた'),
        'quoted': follow.replace('あなたは少し不安だったのですね',
                                '「あなたは少し不安だったのですね」'),
        'cause': follow.replace('頼まれたのに', '頼まれたから'),
    }
    assert changes[mutation] != follow
    assert not inverse(context, changes[mutation], without_author=True).passed


@pytest.mark.parametrize('operation', ['correct', 'withdraw_answer', 'withdraw_event', 'add'])
def test_explanatory_nominal_saved_update_and_replay(qcase, monkeypatch, operation):
    from test_emlis_q3_application import cont
    user, parent, service = qcase
    first = current = run(service.start(user, parent))
    source = '私は少し不安だったのです'
    third = {'correct': '「' + source + '」ではなく「私は少し不安なのだった」です。',
             'withdraw_answer': '「' + source + '」は誤りです。',
             'withdraw_event': '「誘われた」は誤りです。', 'add': '今は少し重い。'}[operation]
    with monkeypatch.context() as saved:
        saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved initial body must not regenerate'))
        assert run(service.get(user, parent)) == run(service.start(user, parent)) == first
    for position, text in enumerate(('今は少し苦しい。', '今は' + source + '。', third)):
        if position:
            current = run(cont(service, user, current, f'explanatory-continue-{position}'))
        current = run(answer(service, user, current, text, f'explanatory-answer-{position}'))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        body = current['current_observation']['text']
        follow = body.split('Emlisから：', 1)[1].strip()
        assert all(event in body for event in ('褒められた', '頼まれた'))
        if position == 1:
            assert '回答した時点ではあなたは少し不安だったのですね' in follow
        elif position == 2:
            if operation == 'correct':
                assert source not in body and '不安だったのですね' not in follow
                assert '先の回答時点ではあなたは少し不安なのでしたね' in follow
            elif operation == 'withdraw_answer':
                assert '不安' not in body and '誘われた' in body
            elif operation == 'withdraw_event':
                assert '誘われた' not in body and source in body and '不安だったのですね' in follow
            else:
                assert '少し重い' in body and '不安だったのですね' in follow
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved explanatory body must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current


@pytest.fixture(scope='module', params=['不安だった', '不安ではなかった'])
def multiple_self_nominal_context(request):
    source = '僕は自分には少し' + request.param + 'のです'
    context = actual(request=advance(advance(begin(), '今は少し苦しい。'), '今は' + source + '。'))
    nominal = '僕は自分には少し' + request.param + 'のだという、回答した時点のあなたの気持ち'
    assert nominal in context[0].artifact.reception and source in context[0].artifact.observation
    assert inverse(context, context[0].artifact.reception, without_author=True).passed
    return context, nominal


@pytest.mark.parametrize('mutation', [
    'first_self', 'second_self', 'drop_self', 'particle', 'degree', 'polarity',
    'inner_past', 'outer_past', 'explanation', 'owner', 'time', 'drop_time',
    'quoted', 'extra_predicate', 'swap_events',
])
def test_multiple_self_nominal_rejects_meaning_changes_without_author(multiple_self_nominal_context, mutation):
    context, nominal = multiple_self_nominal_context
    follow = context[0].artifact.reception
    polarity = ('不安だった' if '不安ではなかった' in nominal else '不安ではなかった')
    changes = {
        'first_self': nominal.replace('僕は', '友人は'),
        'second_self': nominal.replace('自分には', '友人には'),
        'drop_self': nominal.replace('僕は', ''),
        'particle': nominal.replace('自分には', '自分にも'),
        'degree': nominal.replace('少し', ''),
        'polarity': nominal.replace('不安ではなかった' if '不安ではなかった' in nominal else '不安だった', polarity),
        'inner_past': nominal.replace('不安ではなかった', '不安ではない').replace('不安だった', '不安な'),
        'outer_past': nominal.replace('のだという、', 'のだったという、'),
        'explanation': nominal.replace('のだという、', 'という、'),
        'owner': nominal.replace('あなたの気持ち', '私の気持ち'),
        'time': nominal.replace('回答した時点の', 'その時の'),
        'drop_time': nominal.replace('回答した時点の', ''),
        'quoted': '「' + nominal + '」',
        'extra_predicate': nominal + 'が改善したこと',
    }
    changed = (follow.replace('誘われた', 'TEMP').replace('頼まれた', '誘われた').replace('TEMP', '頼まれた')
               if mutation == 'swap_events' else follow.replace(nominal, changes[mutation]))
    assert changed != follow
    assert not inverse(context, changed, without_author=True).passed


@pytest.mark.parametrize('source,finite', [
    ('私は少し不安です', '私は少し不安だ'),
    ('私は少し不安だったのです', '私は少し不安だったのだ'),
])
def test_single_self_cannot_borrow_multiple_self_attribution(source, finite):
    context = actual(request=advance(advance(begin(), '今は少し苦しい。'), '今は' + source + '。'))
    follow = context[0].artifact.reception
    assert 'という、回答した時点のあなたの気持ち' not in follow
    first, middle, last, empty = follow.split('。')
    assert empty == ''
    assert '回答した時点では' in middle
    borrowed = '誘われたのに悲しかったことと、' + finite + 'という、回答した時点のあなたの気持ち' + 'を見失わず、小さくせずに受け止めています'
    assert not inverse(context, first + '。' + borrowed + '。' + last + '。', without_author=True).passed


@pytest.mark.parametrize('operation', ['correct', 'withdraw_answer', 'withdraw_event', 'add'])
def test_multiple_self_nominal_saved_update_and_replay(qcase, monkeypatch, operation):
    from test_emlis_q3_application import cont
    user, parent, service = qcase
    first = current = run(service.start(user, parent))
    source = '私は私には不安だったのです'
    third = {'correct': '「' + source + '」ではなく「私は私には不安なのだった」です。',
             'withdraw_answer': '「' + source + '」は誤りです。',
             'withdraw_event': '「誘われた」は誤りです。', 'add': '今は少し重い。'}[operation]
    for position, text in enumerate(('今は少し苦しい。', '今は' + source + '。', third)):
        if position:
            current = run(cont(service, user, current, f'multiple-self-continue-{position}'))
        current = run(answer(service, user, current, text, f'multiple-self-answer-{position}'))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        body = current['current_observation']['text']
        follow = body.split('Emlisから：', 1)[1].strip()
        assert all(event in body for event in ('褒められた', '頼まれた'))
        if position == 1 or position == 2 and operation == 'add':
            assert '私は私には不安だったのだという、回答した時点のあなたの気持ち' in follow
            assert 'あなたは私には' not in follow
        if position == 2:
            if operation == 'correct':
                assert source not in body and '不安だったのだ' not in follow
                assert '私は私には不安なのだったという、先の回答時点のあなたの気持ち' in follow
            elif operation == 'withdraw_answer':
                assert '不安' not in body and '誘われた' in body
            elif operation == 'withdraw_event':
                assert '誘われた' not in body and source in body
            else:
                assert '少し重い' in body
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved multiple SELF body must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current


@pytest.mark.parametrize('position', [0, 1, 2])
@pytest.mark.parametrize('source,finite', [
    ('私は私には不安です', '私は私には不安だ'),
    ('私は私には不安でした', '私は私には不安だった'),
    ('私は私には不安だったのです', '私は私には不安だったのだ'),
    ('僕は自分には少し不安ではなかったのです', '僕は自分には少し不安ではなかったのだ'),
])
def test_multiple_self_original_answer_keeps_its_event_and_time(position, source, finite):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    initial = request = begin()
    for reply in ('今は少し苦しい。', '今は少し怖い。')[:position] + ('その時は' + source + '。',):
        request = advance(request, reply)
    context = actual(request=request)
    result, plan, _, _, _ = context
    follow = result.artifact.reception
    original = ('褒められたのに嬉しくなかった', '誘われたのに悲しかった', '頼まれたのに寂しかった')
    bound = original[position] + 'ことと、' + finite + 'という、その時のあなたの気持ち'
    assert bound in follow and source in result.artifact.observation
    assert not any(part in follow for part in ('あなたは私には', 'あなたは自分には', 'ですこと', 'でしたこと'))
    groups = ((0,), (1, 2)) if position == 0 else ((0,), (1,), (2,))
    assert_complete_occasion_scopes(context, ('褒められた', '誘われた', '頼まれた'), groups)
    assert request.current_input_bundle == initial.current_input_bundle
    assert inverse(context, follow, without_author=True).passed
    assert MeaningExperienceEngine().generate(request).artifact.text == result.artifact.text


@pytest.fixture(scope='module')
def multiple_self_mixed_time_group():
    request = advance(advance(begin(), 'その時は私は私には少し不安だったのです。'),
                      '今は僕は自分には少し怖かったのです。')
    context = actual(request=request)
    first = '私は私には少し不安だったのだという、その時のあなたの気持ち'
    second = '僕は自分には少し怖かったのだという、回答した時点のあなたの気持ち'
    assert first in context[0].artifact.reception and second in context[0].artifact.reception
    assert_complete_occasion_scopes(context, ('褒められた', '誘われた', '頼まれた'), ((0,), (1,), (2,)))
    assert inverse(context, context[0].artifact.reception, without_author=True).passed
    return context, first, second


@pytest.mark.parametrize('mutation', [
    'drop_first_reference', 'drop_second_reference', 'different_event', 'swap_answers',
    'swap_originals', 'drop_original', 'first_time', 'second_time',
    'borrow_time', 'owner', 'quote', 'extra_predicate',
])
def test_multiple_self_group_cannot_borrow_another_event_or_time(multiple_self_mixed_time_group, mutation):
    context, first, second = multiple_self_mixed_time_group
    follow = context[0].artifact.reception
    changes = {
        'drop_first_reference': follow.replace('褒められたのに嬉しくなかったことと、' + first, first),
        'drop_second_reference': follow.replace('誘われたのに悲しかったことと、' + second, second),
        'different_event': follow.replace('誘われたのに悲しかったことと、' + second,
                                         '頼まれたのに悲しかったことと、' + second),
        'swap_answers': follow.replace(first, 'TEMP').replace(second, first).replace('TEMP', second),
        'swap_originals': follow.replace('嬉しくなかった', 'TEMP').replace('悲しかった', '嬉しくなかった').replace('TEMP', '悲しかった'),
        'drop_original': follow.replace('褒められたのに嬉しくなかったことと、', ''),
        'first_time': follow.replace(first, first.replace('その時の', '回答した時点の')),
        'second_time': follow.replace(second, second.replace('回答した時点の', 'その時の')),
        'borrow_time': follow.replace(second, second.replace('回答した時点の', '')),
        'owner': follow.replace(first, first.replace('あなたの気持ち', '私の気持ち')),
        'quote': follow.replace(first, '「' + first + '」'),
        'extra_predicate': follow.replace(second, second + 'が改善したこと'),
    }
    assert changes[mutation] != follow
    assert not inverse(context, changes[mutation], without_author=True).passed


@pytest.mark.parametrize('operation', ['correct', 'withdraw_answer', 'withdraw_event', 'add'])
def test_multiple_self_original_answer_saved_updates_retain_time(qcase, monkeypatch, operation):
    from test_emlis_q3_application import cont
    user, parent, service = qcase
    first = current = run(service.start(user, parent))
    source = '私は私には不安だったのです'
    third = {'correct': '「' + source + '」ではなく「私は私には不安なのだった」です。',
             'withdraw_answer': '「' + source + '」は誤りです。',
             'withdraw_event': '「誘われた」は誤りです。', 'add': '今は少し重い。'}[operation]
    for position, reply in enumerate(('今は少し苦しい。', 'その時は' + source + '。', third)):
        if position:
            current = run(cont(service, user, current, f'original-self-continue-{position}'))
        current = run(answer(service, user, current, reply, f'original-self-answer-{position}'))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        body = current['current_observation']['text']
        follow = body.split('Emlisから：', 1)[1].strip()
        assert all(event in body for event in ('褒められた', '頼まれた'))
        if position == 1 or position == 2 and operation == 'add':
            assert '誘われたのに悲しかったことと、私は私には不安だったのだという、その時のあなたの気持ち' in follow
        if position == 2:
            if operation == 'correct':
                assert source not in body and '不安だったのだ' not in follow
                assert '私は私には不安なのだったという、その時のあなたの気持ち' in follow
                assert '先の回答時点' not in body
            elif operation == 'withdraw_answer':
                assert '不安' not in body and '誘われた' in body
            elif operation == 'withdraw_event':
                assert '誘われた' not in body and source in body
                assert 'その時の「' + source + '」' in body
            else:
                assert '少し重い' in body
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved original-time SELF body must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current


@pytest.mark.parametrize('time,prefix', [('今は', '回答した時点の'), ('その時は', 'その時の')])
@pytest.mark.parametrize('source,finite', [
    ('私は私には不安です', '私は私には不安だ'),
    ('私は私には不安でした', '私は私には不安だった'),
    ('私は私には不安なのです', '私は私には不安なのだ'),
    ('私は私には不安だったのです', '私は私には不安だったのだ'),
    ('私は私には怖かったです', '私は私には怖かった'),
    ('僕は自分には少し不安ではなかったのです', '僕は自分には少し不安ではなかったのだ'),
])
def test_withdrawn_event_multiple_self_answer_keeps_independent_time(time, prefix, source, finite):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    request = begin()
    for reply in ('今は少し苦しい。', time + source + '。', '「誘われた」は誤りです。'):
        request = advance(request, reply)
    context = actual(request=request)
    result, plan, _, _, _ = context
    nominal = finite + 'という、' + prefix + 'あなたの気持ち'
    assert ('その時に悲しかったことと、' + nominal
            + 'に目が留まり、それを小さくせずに受け止めています。') in result.artifact.reception
    sentences = result.artifact.reception.split('。')[:-1]
    assert len(sentences) == 3
    assert '褒められたのに嬉しくなかったことと、回答した時点で少し苦しいこと' in sentences[1]
    assert '頼まれたのに、寂しさを感じたのですね' == sentences[2]
    assert source in result.artifact.observation and '誘われた' not in result.artifact.text
    assert all(event in result.artifact.text for event in ('褒められた', '頼まれた'))
    assert not any(bad in result.artifact.reception for bad in ('これまで、', '今、', 'ですこと', 'でしたこと'))
    detached = next(n for n in plan.nuclei if n.source_fields == ('answer_text_private',)
                    and 'thread_subject:withdrawn_source_event' in n.semantic_frame.attribute_codes)
    assert not any(detached.nucleus_id in (r.from_nucleus_id, r.to_nucleus_id) for r in plan.relations)
    assert inverse(context, result.artifact.reception, without_author=True).passed
    assert MeaningExperienceEngine().generate(request).artifact.text == result.artifact.text


@pytest.fixture(scope='module', params=[('今は', '回答した時点の'), ('その時は', 'その時の')])
def withdrawn_multiple_self_answer(request):
    time, prefix = request.param
    req = begin()
    for reply in ('今は少し苦しい。', time + '僕は自分には少し不安ではなかったのです。',
                  '「誘われた」は誤りです。'):
        req = advance(req, reply)
    context = actual(request=req)
    nominal = '僕は自分には少し不安ではなかったのだという、' + prefix + 'あなたの気持ち'
    assert nominal in context[0].artifact.reception
    assert inverse(context, context[0].artifact.reception, without_author=True).passed
    return context, nominal, prefix


@pytest.mark.parametrize('mutation', [
    'first_self', 'second_self', 'drop_self', 'particle', 'degree', 'negation',
    'inner_past', 'outer_past', 'explanation', 'owner', 'time', 'drop_time',
    'duration', 'now', 'event', 'quote', 'extra_predicate', 'role',
])
def test_withdrawn_multiple_self_answer_rejects_meaning_changes(withdrawn_multiple_self_answer, mutation):
    context, nominal, prefix = withdrawn_multiple_self_answer
    follow = context[0].artifact.reception
    changes = {
        'first_self': nominal.replace('僕は', '友人は'),
        'second_self': nominal.replace('自分には', '友人には'),
        'drop_self': nominal.replace('僕は', ''),
        'particle': nominal.replace('自分には', '自分にも'),
        'degree': nominal.replace('少し', ''),
        'negation': nominal.replace('不安ではなかった', '不安だった'),
        'inner_past': nominal.replace('不安ではなかった', '不安ではない'),
        'outer_past': nominal.replace('のだという、', 'のだったという、'),
        'explanation': nominal.replace('のだという、', 'という、'),
        'owner': nominal.replace('あなたの気持ち', '私の気持ち'),
        'time': nominal.replace(prefix, 'その時の' if prefix == '回答した時点の' else '回答した時点の'),
        'drop_time': nominal.replace(prefix, ''),
        'duration': 'これまで、' + nominal,
        'now': '今、' + nominal,
        'event': '誘われたことについて、' + nominal,
        'quote': '「' + nominal + '」',
        'extra_predicate': nominal + 'が改善したこと',
    }
    changed = (follow.replace('に目が留まり、それを小さくせずに', 'を小さくせずに')
               if mutation == 'role' else follow.replace(nominal, changes[mutation]))
    assert changed != follow
    assert not inverse(context, changed, without_author=True).passed


@pytest.mark.parametrize('time', ['今は', 'その時は'])
@pytest.mark.parametrize('correct_first', [True, False])
def test_withdrawn_multiple_self_saved_correction_order_keeps_time(qcase, monkeypatch, time, correct_first):
    from test_emlis_q3_application import cont
    user, parent, service = qcase
    first = current = run(service.start(user, parent))
    source, revised = '私は私には不安だったのです', '私は私には不安なのだった'
    correction = '「' + source + '」ではなく「' + revised + '」です。'
    withdrawal = '「褒められた」は誤りです。'
    sequence = (time + source + '。',) + ((correction, withdrawal) if correct_first else (withdrawal, correction))
    for position, reply in enumerate(sequence):
        if position:
            current = run(cont(service, user, current, f'detached-self-continue-{position}'))
        current = run(answer(service, user, current, reply, f'detached-self-answer-{position}'))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        body = current['current_observation']['text']
        assert all(event in body for event in ('誘われた', '頼まれた'))
        if position == 2:
            follow = body.split('Emlisから：', 1)[1].strip()
            prefix = 'その時の' if time == 'その時は' else '先の回答時点の'
            assert revised + 'という、' + prefix + 'あなたの気持ち' in follow
            assert 'その時は嬉しくなかったのですね。' in follow
            assert source not in body and '褒められた' not in body
            assert not any(bad in follow for bad in ('これまで、', '今、', 'ですこと', 'でしたこと'))
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved detached SELF body must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current


def assert_complete_occasion_scopes(context, events, groups):
    result, plan, _, resolver, _ = context
    sentences = tuple(s for s in result.artifact.reception.split('。') if s)
    moves = plan.response_plan.human_reception_plan.moves
    assert len(sentences) == len(moves) == len(groups)
    owned = [set((*m.target_nucleus_ids, *m.support_nucleus_ids)) for m in moves]
    assert all(owned[i].isdisjoint(owned[j]) for i in range(len(moves)) for j in range(i + 1, len(moves)))
    required = {n.nucleus_id for n in plan.nuclei if n.retention == 'required'
                and set(n.source_fields) & {'memo', 'memo_action', 'answer_text_private'}}
    assert set.union(*owned) == required
    index = {n.nucleus_id: n for n in plan.nuclei}
    for sentence, move, group in zip(sentences, moves, groups):
        assert tuple(reception.final_reception_source_anchor_text(nid, index, resolver)
                     for nid in move.target_nucleus_ids) == tuple(events[i] for i in group)
        assert all((event in sentence) == (i in group) for i, event in enumerate(events))
        assert [sentence.index(events[i]) for i in group] == sorted(sentence.index(events[i]) for i in group)
    for relation in plan.relations:
        if relation.relation_id in plan.coverage_requirements.required_relation_ids:
            assert sum({relation.from_nucleus_id, relation.to_nucleus_id} <= ids for ids in owned) == 1
    assert inverse(context, result.artifact.reception, without_author=True).passed


@pytest.mark.parametrize('memo,events', [
    ('褒められたのに、嬉しくなかった。誘われたのに、悲しかった。頼まれたのに、寂しかった。',
     ('褒められた', '誘われた', '頼まれた')),
    (OWNED_INITIAL, ('誘われた', '頼まれた', '言われた')),
])
@pytest.mark.parametrize('sequence,groups,retained,removed', [
    (('その時は少し苦しかった。',), ((0,), (1, 2)), ('少し苦しかった',), ()),
    (('今は少し苦しい。', 'その時は少し怖かった。'), ((0,), (1,), (2,)),
     ('回答した時点では少し苦しい', 'その時に少し怖かった'), ()),
    (('その時は少し苦しかった。', 'その時は少し怖かった。', 'その時は少し寂しかった。'),
     ((0,), (1,), (2,)), ('少し苦しかった', '少し怖かった', '少し寂しかった'), ()),
    (('その時は少し苦しかった。', 'その時は少し怖かった。', '「少し怖かった」ではなく「少し寂しかった」です。'),
     ((0,), (1,), (2,)), ('その時に少し寂しかった',), ('少し怖かった', '先の回答時点')),
    (('その時は少し苦しかった。', 'その時は少し怖かった。', '「少し苦しかった」は誤りです。'),
     ((0,), (1,), (2,)), ('その時に少し怖かった',), ('少し苦しかった',)),
    (('その時は少し苦しかった。', 'その時は私も少し不安でした。'), ((0,), (1,), (2,)),
     ('その時にあなたも少し不安だったこと',), ('不安でしたこと',)),
])
def test_original_feeling_scopes_retain_each_complete_occasion(memo, events, sequence, groups, retained, removed):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    initial = request = begin(memo)
    for reply in sequence:
        request = advance(request, reply)
    context = actual(request=request)
    assert_complete_occasion_scopes(context, events, groups)
    body = context[0].artifact.text
    original = ('頼まれたのに、あなたは少し怖くなかったし、その時は'
                if memo == OWNED_INITIAL else '誘われたのに、悲しかったし、その時は')
    retained = tuple(original + value.removeprefix('その時に').removesuffix('こと')
                     if value.startswith('その時に') else value for value in retained)
    assert all(fragment in body for fragment in retained) and all(fragment not in body for fragment in removed)
    assert request.current_input_bundle == initial.current_input_bundle
    assert MeaningExperienceEngine().generate(request).artifact.text == body


@pytest.mark.parametrize('sequence', [
    ('その時は少し苦しかった。',),
    ('今は少し苦しい。', 'その時は少し怖かった。'),
    ('その時は少し苦しかった。', 'その時は私も少し不安でした。'),
])
def test_two_original_feeling_scopes_retain_both_occasions(sequence):
    request = begin('褒められたのに、嬉しくなかった。誘われたのに、悲しかった。')
    for reply in sequence:
        request = advance(request, reply)
    assert_complete_occasion_scopes(actual(request=request), ('褒められた', '誘われた'), ((0,), (1,)))


@pytest.mark.parametrize('first,second,correction,groups,retained,removed', [
    ('その時は少し苦しかった。', 'その時は少し怖かった。', '「少し怖かった」ではなく「少し重かった」です。',
     ((0,), (1,), (2,)), '少し重かった', '少し怖かった'),
    ('その時は少し苦しかった。', 'その時は少し重かった。', '「少し重かった」ではなく「少し怖かった」です。',
     ((0,), (1,), (2,)), '少し怖かった', '少し重かった'),
    ('その時は少し苦しかった。', 'その時は少しこわかった。', None,
     ((0,), (1,), (2,)), '少しこわかった', ''),
])
def test_original_feeling_operator_boundary_preserves_meaning(first, second, correction, groups, retained, removed):
    request = advance(advance(begin(), first), second)
    if correction:
        request = advance(request, correction)
    context = actual(request=request)
    assert_complete_occasion_scopes(context, ('褒められた', '誘われた', '頼まれた'), groups)
    assert retained in context[0].artifact.text
    assert not removed or removed not in context[0].artifact.text
    assert '先の回答時点' not in context[0].artifact.text


@pytest.fixture(scope='module')
def original_feeling_scope_context():
    return actual(request=advance(advance(begin(OWNED_INITIAL), 'その時は少し苦しかった。'),
                                  'その時は私も少し不安でした。'))


@pytest.mark.parametrize('mutation', [
    'drop_middle', 'swap_sentences', 'drop_answer', 'time', 'tense', 'degree', 'polarity',
    'owner', 'answer_owner', 'answer_particle', 'cause', 'swap_events', 'drop_original',
    'drop_time', 'other_event_answer', 'quoted_answer',
])
def test_original_feeling_scopes_reject_changed_meaning_without_author(original_feeling_scope_context, mutation):
    context = original_feeling_scope_context
    follow = context[0].artifact.reception
    first, middle, last, empty = follow.split('。')
    assert empty == '' and inverse(context, follow, without_author=True).passed
    bound = 'し、その時はあなたも少し不安だった'
    changes = {
        'drop_middle': first + '。' + last + '。',
        'swap_sentences': middle + '。' + first + '。' + last + '。',
        'drop_answer': follow.replace(bound, ''),
        'time': follow.replace('その時はあなたも', '回答した時点ではあなたも'),
        'tense': follow.replace('不安だったのですね', '不安なのですね'),
        'degree': follow.replace('あなたは少し怖くなかった', 'あなたは怖くなかった'),
        'polarity': follow.replace('怖くなかったし', '怖かったし'),
        'owner': follow.replace('あなたは少し怖くなかった', '友人は少し怖くなかった'),
        'answer_owner': follow.replace('あなたも少し不安', '友人も少し不安'),
        'answer_particle': follow.replace('あなたも少し不安', 'あなたは少し不安'),
        'cause': follow.replace('頼まれたのに', '頼まれたから'),
        'swap_events': follow.replace('誘われた', 'TEMP').replace('頼まれた', '誘われた').replace('TEMP', '頼まれた'),
        'drop_original': follow.replace('頼まれたのに、あなたは少し怖くなかったし、', ''),
        'drop_time': follow.replace('その時はあなたも', 'あなたも'),
        'other_event_answer': follow.replace(bound, 'し、誘われたことについて、その時はあなたも少し不安だった'),
        'quoted_answer': follow.replace(bound, 'し、「その時はあなたも少し不安だった」'),
    }
    assert changes[mutation] != follow
    assert not inverse(context, changes[mutation], without_author=True).passed


@pytest.mark.parametrize('operation', ['add', 'correct', 'withdraw_answer', 'withdraw_event'])
def test_original_feeling_scopes_saved_update_and_replay(qcase, monkeypatch, operation):
    from test_emlis_q3_application import cont
    user, parent, service = qcase
    first = current = run(service.start(user, parent))
    third = {'add': 'その時は少し寂しかった。',
             'correct': '「少し怖かった」ではなく「少し寂しかった」です。',
             'withdraw_answer': '「少し苦しかった」は誤りです。',
             'withdraw_event': '「誘われた」は誤りです。'}[operation]
    for position, reply in enumerate(('その時は少し苦しかった。', 'その時は少し怖かった。', third)):
        if position:
            current = run(cont(service, user, current, f'original-scope-continue-{position}'))
        current = run(answer(service, user, current, reply, f'original-scope-answer-{position}'))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        body = current['current_observation']['text']
        follow = body.split('Emlisから：', 1)[1].strip()
        if position == 1 or position == 2 and operation != 'withdraw_event':
            assert follow.count('。') == 3
        assert '回答した時点' not in body and '先の回答時点' not in body
        if position == 2:
            if operation == 'correct':
                assert '少し怖かった' not in body and '誘われたのに、悲しかったし、その時は少し寂しかった' in follow
            elif operation == 'withdraw_answer':
                assert '少し苦しかった' not in body and '少し怖かった' in body
            elif operation == 'withdraw_event':
                assert '誘われた' not in body and 'その時の「少し怖かった」' in body
            else:
                assert '少し寂しかった' in follow
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved original scope body must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current


@pytest.mark.parametrize('source,nominal', [
    ('少し怖かった', 'その時に少し怖かったこと'),
    ('私も少し不安でした', 'その時にあなたも少し不安だったこと'),
    ('私は少し不安だったのです', 'その時にあなたは少し不安だったのだということ'),
    ('私は私には少し不安だったのです', '私は私には少し不安だったのだという、その時のあなたの気持ち'),
    ('不安です', 'その時に不安なこと'),
    ('不安でした', 'その時に不安だったこと'),
])
def test_original_occasion_reference_is_owned_by_complete_same_event(source, nominal):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    request = advance(advance(begin(), '今は少し苦しい。'), 'その時は' + source + '。')
    context = actual(request=request)
    follow = context[0].artifact.reception
    legacy = source == '私は私には少し不安だったのです'
    original = '誘われたのに悲しかったことと、' if legacy else '誘われたのに、悲しかったし、その時は'
    nominal = nominal if legacy else {
        '少し怖かった': '少し怖かったのですね',
        '私も少し不安でした': 'あなたも少し不安だったのですね',
        '私は少し不安だったのです': 'あなたは少し不安だったのですね',
        '不安です': '不安なのですね', '不安でした': '不安だったのですね',
    }[source]
    bound = original + nominal
    assert bound in follow and 'その出来事について、' not in follow
    assert source in context[0].artifact.observation
    assert_complete_occasion_scopes(context, ('褒められた', '誘われた', '頼まれた'), ((0,), (1,), (2,)))
    assert MeaningExperienceEngine().generate(request).artifact.text == context[0].artifact.text
    assert inverse(context, follow, without_author=True).passed
    for changed in (
        follow.replace(bound, nominal),
        follow.replace(original, original.replace('誘われた', '頼まれた')),
        follow.replace(nominal, '褒められたことについて、' + nominal),
        follow.replace(nominal, '「' + nominal + '」'),
        (follow.replace(nominal, nominal.replace('その時の', '回答した時点の')) if legacy
         else follow.replace(original, original.replace('その時は', '回答した時点では'))),
        (follow.replace(nominal, nominal.replace('その時の', '')) if legacy
         else follow.replace(original, original.replace('その時は', ''))),
    ):
        assert changed != follow
        assert not inverse(context, changed, without_author=True).passed


@pytest.mark.parametrize('source', ['私は私には不安です', '私は私には不安だったのです'])
def test_multiple_original_events_still_require_each_answer_reference(source):
    request = advance(advance(begin(), 'その時は' + source + '。'), 'その時は少し重かった。')
    context = actual(request=request)
    follow = context[0].artifact.reception
    assert_complete_occasion_scopes(context, ('褒められた', '誘われた', '頼まれた'), ((0,), (1,), (2,)))
    assert '褒められたのに嬉しくなかったことと、私は私には' in follow
    assert 'その出来事について、' not in follow
    assert inverse(context, follow, without_author=True).passed
    # The local omission now has its own complete original. Removing it or
    # replacing it by another event must still fail the independent reader.
    for changed in (follow.replace('褒められたのに嬉しくなかったことと、', '', 1),
                    follow.replace('褒められた', '誘われた', 1)):
        assert changed != follow and not inverse(context, changed, without_author=True).passed


@pytest.mark.parametrize('source,predicate', [
    ('不安です', '不安な'),
    ('不安でした', '不安だった'),
    ('私も少し不安でした', 'あなたも少し不安だった'),
    ('少し私は不安なのです', 'あなたは少し不安なのだという'),
    ('私は少し不安だったのです', 'あなたは少し不安だったのだという'),
    ('私は少し不安なのだった', 'あなたは少し不安なのだったという'),
])
@pytest.mark.parametrize('time,temporal', [('その時は', 'その時に'), ('今は', '回答した時点で')])
@pytest.mark.parametrize('position', [0, 1])
def test_grouped_answer_nominal_keeps_own_copula_and_explanation(source, predicate, time, temporal, position):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    initial = request = begin()
    replies = ['その時は私は私には不安だったのです。']
    replies.insert(position, time + source + '。')
    for reply in (*replies, 'その時は少し重かった。'):
        request = advance(request, reply)
    context = actual(request=request)
    result = context[0]
    follow = result.artifact.reception
    sentences = follow.split('。')[:-1]
    original = ('褒められたのに、嬉しくなかったし、',
                '誘われたのに、悲しかったし、')[position]
    # Each eligible event uses the same finite form while keeping its own
    # original time or explicit answer time and complete source scope.
    finite = {
        '不安です': '不安なのですね', '不安でした': '不安だったのですね',
        '私も少し不安でした': 'あなたも少し不安だったのですね',
        '少し私は不安なのです': 'あなたは少し不安なのですね',
        '私は少し不安だったのです': 'あなたは少し不安だったのですね',
        '私は少し不安なのだった': 'あなたは少し不安なのでしたね',
    }[source]
    nominal = finite
    bound = original + ('回答した時点では' if time == '今は' else 'その時は') + nominal
    assert bound in follow and source in result.artifact.observation
    assert 'ですこと' not in follow and 'でしたこと' not in follow
    assert request.current_input_bundle == initial.current_input_bundle
    assert_complete_occasion_scopes(context, ('褒められた', '誘われた', '頼まれた'), ((0,), (1,), (2,)))
    assert MeaningExperienceEngine().generate(request).artifact.text == result.artifact.text
    other = '私は私には不安だったのだという、その時のあなたの気持ち'
    mutations = [
        follow.replace(original, '', 1),
        follow.replace('褒められた', '誘われた', 1),
        follow.replace(nominal, '「' + nominal + '」'),
        follow.replace(nominal, 'TEMP').replace(other, nominal).replace('TEMP', other),
        follow.replace(sentences[2] + '。', ''),
        follow.replace(nominal, nominal.replace('不安', '安心')),
    ]
    if time == '今は':
        mutations.extend((follow.replace('回答した時点では', 'その時は'),
                          follow.replace('回答した時点では', '')))
    else:
        mutations.append(follow.replace(original + 'その時は', original + '回答した時点では'))
        mutations.append(follow.replace(original + 'その時は', original))
    if 'のだ' in predicate:
        changed = finite.replace('不安なの', '不安だったの') if '不安なの' in finite else finite.replace('不安だったの', '不安なの')
        mutations.extend((follow.replace(finite, changed),
            follow.replace(finite, finite.replace('のでしたね', 'のですね') if 'のでしたね' in finite else finite.replace('のですね', 'のでしたね')),
            follow.replace(finite, finite.replace('のでしたね', 'でしたね').replace('のですね', 'ですね'))))
    else:
        changed = nominal.replace('不安な', '不安だった') if '不安な' in nominal else nominal.replace('不安だった', '不安な')
        mutations.append(follow.replace(nominal, changed))
    if 'あなた' in predicate:
        mutations.extend((
            follow.replace(nominal, nominal.replace('あなた', '友人')),
            follow.replace(nominal, nominal.replace('少し', '')),
            follow.replace(nominal, nominal.replace('あなたも', 'あなたには') if 'あなたも' in nominal else nominal.replace('あなたは', 'あなたにも')),
        ))
    for changed in mutations:
        assert changed != follow
        assert not inverse(context, changed, without_author=True).passed



@pytest.mark.parametrize('source,nominal', [
    ('不安です', 'その時に不安なこと'),
    ('不安でした', 'その時に不安だったこと'),
    ('私も少し不安でした', 'その時にあなたも少し不安だったこと'),
    ('私は少し不安だったのです', 'その時にあなたは少し不安だったのだということ'),
])
def test_grouped_answer_nominal_third_answer_saved_replay(qcase, monkeypatch, source, nominal):
    from test_emlis_q3_application import cont
    user, parent, service = qcase
    first = current = run(service.start(user, parent))
    for position, reply in enumerate(('その時は' + source + '。',
            'その時は私は私には不安だったのです。', 'その時は少し重かった。')):
        if position:
            current = run(cont(service, user, current, f'group-nominal-continue-{position}'))
        current = run(answer(service, user, current, reply, f'group-nominal-answer-{position}'))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        body = current['current_observation']['text']
        assert '今回の観測に反映できていない' not in body
        if position == 2:
            follow = body.split('Emlisから：', 1)[1].strip()
            expected = nominal.removeprefix('その時に').removesuffix('こと').removesuffix('のだという')
            assert '褒められたのに、嬉しくなかったし、その時は' + expected + 'のですね' in follow.split('。')[0]
            assert source in body and 'その出来事について、' not in follow
            assert all(event in follow for event in ('褒められた', '誘われた', '頼まれた'))
            assert '頼まれたのに、寂しかったし、その時は少し重かったのですね' in follow
            assert 'ですこと' not in follow and 'でしたこと' not in follow
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved grouped answer must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current


@pytest.mark.parametrize('source,predicate', [
    ('私も少し不安でした', 'あなたも少し不安だった'),
    ('少し私は怖くなかったです', 'あなたは少し怖くなかった'),
    ('僕には少し寂しかった', 'あなたには少し寂しかった'),
    ('私は少し不安だった', 'あなたは少し不安だった'),
    ('不安でした', '不安だった'),
    ('怖くなかったです', '怖くなかった'),
])
@pytest.mark.parametrize('position', [0, 1])
@pytest.mark.parametrize('event_count', [2, 3])
def test_grouped_original_nominal_keeps_actor_degree_negation_and_past(source, predicate, position, event_count):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    events = ('褒められた', '誘われた', '頼まれた')[:event_count]
    feelings = ['嬉しくなかった', '悲しかった', '寂しかった'][:event_count]
    feelings[position] = source
    memo = ''.join(event + 'のに、' + feeling + '。' for event, feeling in zip(events, feelings))
    initial = request = begin(memo)
    for reply in ('その時は私は私には不安だったのです。', 'その時は少し重かった。'):
        request = advance(request, reply)
    context = actual(request=request)
    result = context[0]
    follow = result.artifact.reception
    original = events[position] + ('のに、' + predicate if position == 1
                                   else 'のに' + predicate + 'こと')
    assert original in follow
    assert source in result.artifact.observation
    assert 'ですこと' not in follow and 'でしたこと' not in follow
    assert request.current_input_bundle == initial.current_input_bundle
    assert_complete_occasion_scopes(context, events, tuple((i,) for i in range(event_count)))
    assert MeaningExperienceEngine().generate(request).artifact.text == result.artifact.text
    assert inverse(context, follow, without_author=True).passed
    mutations = [
        follow.replace(original, original.replace(events[position], events[1 - position])),
        follow.replace(original, original.replace('のに', 'から')),
        follow.replace(original, ''),
        follow.replace(original, '「' + original + '」'),
        follow.replace('少し重かった', ''),
        follow.replace('少し重かった', '褒められたことについて、少し重かった'),
        follow.replace('少し重かった', '回答した時点では少し重かった'),
    ]
    current_predicate = (predicate.replace('くなかった', 'くない') if 'くなかった' in predicate
        else predicate.replace('寂しかった', '寂しい').replace('不安だった', '不安な'))
    mutations.append(follow.replace(original, original.replace(predicate, current_predicate)))
    if 'くなかった' in predicate:
        mutations.append(follow.replace(original, original.replace('くなかった', 'かった')))
    if 'あなた' in predicate:
        mutations.extend((
            follow.replace(original, original.replace('あなた', '友人')),
            follow.replace(original, original.replace('少し', '')),
            follow.replace(original, original.replace('あなたには', 'あなたにも').replace('あなたも', 'あなたは')
                if 'あなたは' not in original else original.replace('あなたは', 'あなたも')),
        ))
    for changed in mutations:
        assert changed != follow
        assert not inverse(context, changed, without_author=True).passed


@pytest.mark.parametrize('operation', ['add', 'correct_original', 'withdraw_original', 'withdraw_event'])
def test_grouped_original_nominal_saved_updates_keep_original_and_replay(qcase, qdb, monkeypatch, operation):
    from test_emlis_q3_application import cont
    user, parent, service = qcase
    memo = ('褒められたのに、私も少し不安でした。'
            '誘われたのに、少し私は怖くなかったです。頼まれたのに、寂しかった。')
    qdb.query('update public.emotions set memo=$1 where id=$2', [memo, parent])
    first = current = run(service.start(user, parent))
    third = {'add': 'その時は少し苦しかった。',
             'correct_original': '「私も少し不安でした」ではなく「私も少し悲しかった」です。',
             'withdraw_original': '「私も少し不安でした」は誤りです。',
             'withdraw_event': '「褒められた」は誤りです。'}[operation]
    for position, reply in enumerate(('その時は私は私には不安だったのです。', 'その時は少し重かった。', third)):
        if position:
            current = run(cont(service, user, current, f'group-original-continue-{position}'))
        current = run(answer(service, user, current, reply, f'group-original-answer-{position}'))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        body = current['current_observation']['text']
        follow = body.split('Emlisから：', 1)[1].strip()
        assert '今回の観測に反映できていない' not in body
        if position == 1:
            assert '褒められたのにあなたも少し不安だったこと' in follow
            assert '誘われたのに、あなたは少し怖くなかった' in follow
            assert 'ですこと' not in follow and 'でしたこと' not in follow
        if position == 2:
            if operation == 'correct_original':
                assert '私も少し不安でした' not in body and '少し悲しかった' in body
            elif operation == 'withdraw_original':
                assert '私も少し不安でした' not in body and 'あなたも少し不安だったこと' not in follow
            elif operation == 'withdraw_event':
                assert '褒められた' not in body
            else:
                assert '少し苦しかった' in body
            assert '怖くなかった' in body and '少し重かった' in body
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved original nominal must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current


@pytest.mark.parametrize('source,old,new', [
    (A, '求められるよう', '求められたから'),
    (A.replace('、', ','), '求められるよう', '求められたから'),
    (B, '見てもらえていない', '見てもらえている'),
    (C, '相手が嫌なのではなく', '相手が嫌だから'),
    ('その時は少し重かった。', '少し重', '重'),
    ('その時は少しこわかった。', '少しこわ', '少しこわくな'),
    ('その時は私は私には不安だったのです。', '私は私には', '私は友人には'),
])
@pytest.mark.parametrize('position', [0, 1, 2])
def test_accepted_original_answers_keep_complete_independent_occasions(source, old, new, position):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    request = begin()
    replies = ['その時は少し苦しかった。'] * 3
    replies[position] = source
    for reply in replies:
        request = advance(request, reply)
    context = actual(request=request)
    follow = context[0].artifact.reception
    assert_complete_occasion_scopes(context, ('褒められた', '誘われた', '頼まれた'), ((0,), (1,), (2,)))
    assert MeaningExperienceEngine().generate(request).artifact.text == context[0].artifact.text
    sentences = follow.split('。')[:-1]
    target = sentences[position]
    assert old in target
    # Every answer retains its original source in the observation and its
    # own full event/contrast/ABOUT duty in the independent body reader.
    assert source.rstrip('。').removeprefix('その時は') in context[0].artifact.observation
    mutations = [
        follow.replace(target + '。', ''),
        follow.replace(target, target.replace(old, new)),
        follow.replace(target, '「' + target + '」'),
        follow.replace('褒められた', '誘われた'),
        (follow.replace('見失わず、', '') if '見失わず、' in sentences[1]
         else follow.replace(sentences[1], sentences[1].removesuffix('のですね'))),
    ]
    if source in {A, A.replace('、', ',')}:
        mutations.extend(follow.replace(target, target.replace(word, '')) for word in ('次も', '同じ'))
    elif source == B:
        mutations.append(follow.replace(target, target.replace('だけ', '')))
    elif source == C:
        mutations.append(follow.replace(target, target.replace('まだ', '')))
    if position == 1 and '誘われたのに、悲しかったし、その時は' in target:
        original = '誘われたのに、悲しかったし、その時は'
        mutations.extend((
            follow.replace(target, target.replace('その時は', '回答した時点では')),
            follow.replace(target, target.replace('その時は', '')),
            follow.replace(target, target.replace(original, '')),
            follow.replace(target, target.replace(original, original + '褒められたことについて、')),
        ))
    elif position == 1 and '誘われた時は悲しく、' in target:
        original = '誘われた時は悲しく、'
        mutations.extend((
            follow.replace(target, target.replace(original, '誘われたことについて、回答した時点では悲しく、')),
            follow.replace(target, target.replace(original, '誘われたことについて、悲しく、')),
            follow.replace(target, target.replace(original, '')),
            follow.replace(target, target.replace(original, original + '褒められたことについて、')),
        ))
    elif position == 1:
        assert 'その出来事への' not in target
        mutations.extend((
            follow.replace(target, target.replace('その時', '回答した時点')),
            follow.replace(target, target.replace('その時の', '').replace('その時に', '')),
            follow.replace(target, target.replace('誘われたのに悲しかったことと、', '')),
            follow.replace(target, target.replace('ことと、', 'ことと、褒められたことについて、', 1)),
        ))
    for changed in mutations:
        assert changed != follow
        assert not inverse(context, changed, without_author=True).passed


@pytest.mark.parametrize('operation', ['correct_answer', 'withdraw_answer', 'correct_original', 'withdraw_event'])
def test_interpretation_occasion_updates_save_and_replay(qcase, monkeypatch, operation):
    from test_emlis_q3_application import cont
    user, parent, service = qcase
    first = current = run(service.start(user, parent))
    third = {
        'correct_answer': '「' + B.rstrip('。') + '」ではなく「少し重かった」です。',
        'withdraw_answer': '「' + B.rstrip('。') + '」は誤りです。',
        'correct_original': '「悲しかった」ではなく「少し怖かった」です。',
        'withdraw_event': '「誘われた」は誤りです。',
    }[operation]
    for position, reply in enumerate((A, B, third)):
        if position:
            current = run(cont(service, user, current, f'interpretation-continue-{position}'))
        current = run(answer(service, user, current, reply, f'interpretation-answer-{position}'))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        body = current['current_observation']['text']
        assert '今回の観測に反映できていない' not in body
        follow = body.split('Emlisから：', 1)[1].strip()
        if position == 1:
            sentences = follow.split('。')[:-1]
            assert len(sentences) == 3
            assert '誘われたのに、悲しかったし、その時は結果だけで' in sentences[1]
            assert 'そこまでの苦労は見てもらえていないと思ったのですね' in sentences[1]
            assert 'その出来事への結果' not in follow
        if position == 2:
            if operation in {'correct_answer', 'withdraw_answer'}:
                assert '見てもらえていない' not in body
                assert ('少し重かった' in body) == (operation == 'correct_answer')
            elif operation == 'correct_original':
                assert '悲しかった' not in body and '少し怖かった' in body
            else:
                assert '誘われた' not in body and '見てもらえていない' in body
            assert '次も同じ成果を求められる' in body and '寂し' in body
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved interpretation must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current


@pytest.mark.parametrize('source', [A, A.replace('、', ','), B])
@pytest.mark.parametrize('when', ['original_occasion', 'answer_time', 'prior_answer_time'])
def test_interpretation_nominal_omission_keeps_own_time(source, when):
    request = advance(begin(), 'その時は少し苦しかった。')
    reply = source if when == 'original_occasion' else '今は' + source
    request = advance(request, reply)
    if when == 'prior_answer_time':
        # The same full interpretation remains a prior-time answer after
        # replacing its source through the real correction lifecycle.
        changed = source.replace('重かった', '苦しかった').replace('苦労', '努力')
        request = advance(request, '「' + source.rstrip('。') + '」ではなく「' + changed.rstrip('。') + '」です。')
    context = actual(request=request)
    follow = context[0].artifact.reception
    assert_complete_occasion_scopes(context, ('褒められた', '誘われた', '頼まれた'), ((0,), (1,), (2,)))
    original = '誘われたのに、悲しかったし、'
    time = {'original_occasion': 'その時は', 'answer_time': '回答した時点では',
            'prior_answer_time': '先の回答時点では'}[when]
    middle = follow.split('。')[1]
    assert time in middle and 'その出来事への' not in middle
    assert original in middle
    assert middle.endswith('のですね')
    other_time = '先の回答時点では' if when == 'answer_time' else '回答した時点では'
    for changed in (follow.replace(time, ''), follow.replace(time, other_time),
                    follow.replace(original, ''),
                    follow.replace(original, original + '褒められたことについて、', 1)):
        assert changed != follow and not inverse(context, changed, without_author=True).passed


@pytest.mark.parametrize('memo,events', [
    ('褒められたのに、嬉しくなかった。誘われたのに、悲しかった。頼まれたのに、寂しかった。',
     ('褒められた', '誘われた', '頼まれた')),
    (OWNED_INITIAL, ('誘われた', '頼まれた', '言われた')),
])
@pytest.mark.parametrize('sequence', [
    ('その時は少し苦しかった。', 'その時は少し重かった。'),
    ('今は少し苦しい。', '今は少し重い。'), (A, B),
])
@pytest.mark.parametrize('withdraw', [0, 1, 2])
def test_withdrawal_keeps_two_complete_live_occasions(memo, events, sequence, withdraw):
    request = begin(memo)
    for reply in (*sequence, '「' + events[withdraw] + '」は誤りです。'):
        request = advance(request, reply)
    context = actual(request=request)
    result, plan, _, _, _ = context
    follow = result.artifact.reception
    sentences = follow.split('。')[:-1]
    assert len(sentences) == 3 and events[withdraw] not in result.artifact.text
    surviving = tuple(event for i, event in enumerate(events) if i != withdraw)
    assert all(sum(event in sentence for sentence in sentences) == 1 for event in surviving)
    assert not any(all(event in sentence for event in surviving) for sentence in sentences)
    moves = plan.response_plan.human_reception_plan.moves
    assert len(moves) == 3 and {m.move_role for m in moves} == {'attention', 'significance', 'felt_response'}
    detached = {n.nucleus_id for n in plan.nuclei
                if 'thread_subject:withdrawn_source_event' in n.semantic_frame.attribute_codes}
    assert len(detached) == (2 if withdraw < 2 else 1)
    assert not any(detached & {r.from_nucleus_id, r.to_nucleus_id} for r in plan.relations)
    expected = {nid for m in moves for nid in (*m.target_nucleus_ids, *m.support_nucleus_ids)}
    assert expected == {n.nucleus_id for n in plan.nuclei if n.retention == 'required'
                        and set(n.source_fields) & {'memo', 'answer_text_private'}}
    assert inverse(context, follow, without_author=True).passed
    for changed in (follow.replace(surviving[0], surviving[1], 1),
                    '。'.join(sentences[1:]) + '。',
                    follow.replace(sentences[1], sentences[2], 1),
                    follow.replace('その時', '先の回答時点').replace('回答した時点', 'その時')):
        assert changed != follow and not inverse(context, changed, without_author=True).passed


@pytest.mark.parametrize('time', ['その時は', '今は'])
@pytest.mark.parametrize('original', ['嬉しくなかった', '私も少し不安でした', '少し私は怖くなかった'])
def test_withdrawal_repeated_self_keeps_whole_nominal_and_other_original(original, time):
    source = '僕は自分には少し不安ではなかったのです'
    memo = '褒められたのに、' + original + '。誘われたのに、悲しかった。頼まれたのに、寂しかった。'
    request = begin(memo)
    for reply in (time + source + '。', 'その時は少し重かった。', '「褒められた」は誤りです。'):
        request = advance(request, reply)
    context = actual(request=request)
    follow = context[0].artifact.reception
    temporal = 'その時の' if time == 'その時は' else '回答した時点の'
    nominal = '僕は自分には少し不安ではなかったのだという、' + temporal + 'あなたの気持ち'
    first = follow.split('。')[0]
    assert nominal in first and first.endswith('に目が留まり、それを小さくせずに受け止めています')
    assert 'その時に' in first and ('あなたも少し不安だったこと' in first if '不安でした' in original else True)
    assert '褒められた' not in context[0].artifact.text
    assert not any(bad in follow for bad in ('ですのですね', 'でしたこと', 'ですこと', 'あなたは自分には'))
    assert inverse(context, follow, without_author=True).passed
    for old, new in [('僕は自分には', '僕は'), ('僕は自分には', 'あなたは自分には'),
                     ('自分には', '自分にも'), ('少し不安ではなかった', '不安ではなかった'),
                     ('不安ではなかった', '不安だった'), ('のだという、', 'という、'),
                     (temporal, ''), (temporal, '先の回答時点の'),
                     ('その時に', '回答した時点で'),
                     ('に目が留まり、それを', 'を見失わず、'),
                     ('ことと、', 'ことと、誘われたことについて、')]:
        changed = follow.replace(old, new, 1)
        assert changed != follow and not inverse(context, changed, without_author=True).passed
    ending = 'に目が留まり、それを小さくせずに受け止めています'
    left, right = first[:-len(ending)].split('と、', 1)
    for changed in (follow.replace(first, right + ending),
                    follow.replace(first, right + 'と、' + left + ending),
                    follow.replace(first, left + 'と、' + left + ending)):
        assert changed != follow and not inverse(context, changed, without_author=True).passed
    original_finite = {'嬉しくなかった': '嬉しくなかった', '私も少し不安でした': 'あなたも少し不安だった',
                       '少し私は怖くなかった': 'あなたは少し怖くなかった'}[original]
    prefix = 'その時、' if time == 'その時は' else '回答した時点で、'
    broken = 'その時' + ('は' if original == '嬉しくなかった' else '、') + original_finite
    broken += 'し、' + prefix + source.replace('僕は', 'あなたは', 1) + 'のですね'
    changed = follow.replace(first, broken)
    assert changed != follow and not inverse(context, changed, without_author=True).passed


@pytest.mark.parametrize('sequence,withdraw', [
    (('その時は少し苦しかった。', 'その時は少し重かった。'), '誘われた'),
    (('今は少し苦しい。', '今は少し重い。'), '頼まれた'),
    (('その時は私は私には不安だったのです。', 'その時は少し重かった。'), '褒められた'),
])
def test_withdrawal_separate_occasions_save_original_and_exact_replay(qcase, monkeypatch, sequence, withdraw):
    from test_emlis_q3_application import cont
    user, parent, service = qcase
    first = current = run(service.start(user, parent))
    for position, reply in enumerate((*sequence, '「' + withdraw + '」は誤りです。')):
        if position:
            current = run(cont(service, user, current, f'withdrawal-scope-continue-{position}'))
        current = run(answer(service, user, current, reply, f'withdrawal-scope-answer-{position}'))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        body = current['current_observation']['text']
        assert '今回の観測に反映できていない' not in body
        if position == 2:
            assert withdraw not in body
            follow = body.split('Emlisから：', 1)[1].strip()
            assert len(follow.split('。')[:-1]) == 3
            assert 'を見失わず、小さくせずに受け止めています。' in follow
            assert all(word in body for word in ('嬉しくなかった', '悲しかった', '寂し'))
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('withdrawal saved body must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current


@pytest.mark.parametrize('source,finite', [
    ('私は少し不安です', 'あなたは少し不安なのですね'),
    ('私は少し不安でした', 'あなたは少し不安だったのですね'),
    ('私は少し不安だったのです', 'あなたは少し不安だったのですね'),
    ('私は少し不安なのだった', 'あなたは少し不安なのでしたね'),
])
@pytest.mark.parametrize('time,prefix', [('今は', '回答した時点で、'), ('その時は', 'その時、')])
def test_withdrawal_single_self_keeps_copula_and_explanation(source, finite, time, prefix):
    request = begin()
    for reply in ('今は少し苦しい。', time + source + '。', '「誘われた」は誤りです。'):
        request = advance(request, reply)
    context = actual(request=request)
    follow = context[0].artifact.reception
    assert 'その時は悲しかったし、' + prefix + finite + '。' in follow
    assert '誘われた' not in context[0].artifact.text and source in context[0].artifact.observation
    assert len(follow.split('。')[:-1]) == 3
    assert inverse(context, follow, without_author=True).passed
    for changed in (follow.replace(prefix, ''), follow.replace(prefix, '先の回答時点で、'),
                    follow.replace('あなたは少し不安', 'あなたは不安'),
                    follow.replace('あなたは少し不安', '友人は少し不安'),
                    follow.replace('その時は悲しかったし、', ''),
                    follow.replace('あなたは少し不安なのでしたね', 'あなたは少し不安なのですね')
                        if source.endswith('のだった') else follow.replace(finite, 'あなたは少し不安ですのですね')):
        assert changed != follow and not inverse(context, changed, without_author=True).passed


@pytest.mark.parametrize('source,finite', [
    ('私は少し不安だったのです', 'あなたは少し不安だったのですね'),
    ('私は少し不安なのだった', 'あなたは少し不安なのでしたね'),
])
def test_shared_revision_explanation_keeps_both_sources_under_one_ending(source, finite):
    from test_cmee_emlis_detached_observation import two_independent_revision_answers
    request = begin()
    for reply in two_independent_revision_answers((source, source)):
        request = advance(request, reply)
    context = actual(request=request)
    follow = context[0].artifact.reception
    assert '二つの言い直しでは、どちらも当時、' + finite + '。' in follow
    assert inverse(context, follow, without_author=True).passed
    for changed in (follow.replace('二つの言い直しでは、どちらも', '一つの言い直しでは、'),
                    follow.replace('当時、', '回答した時点で、'),
                    follow.replace('少し不安', '不安'),
                    follow.replace('不安なのでしたね', '不安なのですね') if source.endswith('のだった')
                        else follow.replace('不安だったのですね', '不安なのですね')):
        assert changed != follow and not inverse(context, changed, without_author=True).passed


@pytest.mark.parametrize('count,removed', [(2, '嬉しくなかった'), (3, '寂しかった')])
@pytest.mark.parametrize('reply,retained', [
    ('その時は少し苦しかった。', 'その時に少し苦しかった'),
    ('今は少し苦しい。', '回答した時点で少し苦しい'),
    ('その時は私も少し不安でした。', 'その時にあなたも少し不安だった'),
    ('その時は私には少し不安だったのです。', 'その時にあなたには少し不安だったのだということ'),
])
def test_original_revision_separates_two_retained_occasions(count, removed, reply, retained):
    from test_cmee_emlis_q3_thread import MEMO
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    memo = '。'.join(MEMO.split('。')[:count]) + '。'
    request = advance(advance(begin(memo), reply), '「' + removed + '」ではなく「少し怖かった」です。')
    context = actual(request=request)
    result, plan, _, _, _ = context
    follow = result.artifact.reception
    sentences = follow.split('。')[:-1]
    assert len(sentences) == 3
    assert '当時は少し怖かった' in sentences[0]
    assert all(event not in sentences[0] for event in ('褒められた', '誘われた', '頼まれた'))
    assert '褒められた' in sentences[1] and retained in sentences[1]
    assert '誘われた' not in sentences[1] and '頼まれた' not in sentences[1]
    assert '誘われたのに、悲しさを感じた' in sentences[2]
    assert removed not in result.artifact.text
    if count == 3:
        # The bare event remains an observation fact, not the correction's cause.
        assert '頼まれた' in result.artifact.observation and '頼まれた' not in follow
    moves = plan.response_plan.human_reception_plan.moves
    assert len(moves) == 3 and {m.move_role for m in moves} == {'attention', 'significance', 'felt_response'}
    revised = {n.nucleus_id for n in plan.nuclei
               if 'thread_subject:independent_source_replacement' in n.semantic_frame.attribute_codes}
    assert len(revised) == 1
    assert not any(revised & {r.from_nucleus_id, r.to_nucleus_id} for r in plan.relations)
    owned = [set((*m.target_nucleus_ids, *m.support_nucleus_ids)) for m in moves]
    assert all(a.isdisjoint(b) for i, a in enumerate(owned) for b in owned[i+1:])
    assert revised in owned
    for relation in plan.relations:
        if relation.retention == 'required':
            assert sum({relation.from_nucleus_id, relation.to_nucleus_id} <= ids for ids in owned) == 1
    assert MeaningExperienceEngine().generate(request).artifact.text == result.artifact.text
    assert inverse(context, follow, without_author=True).passed
    for changed in (follow.replace('褒められた', '誘われた', 1),
                    follow.replace('少し怖かった', '怖かった', 1),
                    follow.replace('少し怖かった', '少し怖くなかった', 1),
                    follow.replace('当時は', '今は', 1),
                    follow.replace(retained, retained.replace('その時に', '回答した時点で')
                        if 'その時に' in retained else retained.replace('回答した時点で', 'その時に'), 1),
                    follow.replace(sentences[1], sentences[2], 1),
                    '。'.join(sentences[1:]) + '。'):
        assert changed != follow and not inverse(context, changed, without_author=True).passed


@pytest.mark.parametrize('count,removed', [(2, '嬉しくなかった'), (3, '寂しかった')])
def test_original_revision_separated_occasions_save_and_replay(qcase, qdb, monkeypatch, count, removed):
    from test_cmee_emlis_q3_thread import MEMO
    from test_emlis_q3_application import cont
    user, parent, service = qcase
    memo = '。'.join(MEMO.split('。')[:count]) + '。'
    qdb.query('update public.emotions set memo=$1 where id=$2', [memo, parent])
    first = current = run(service.start(user, parent))
    sequence = ('今は少し苦しい。', '「' + removed + '」ではなく「少し怖かった」です。')
    for position, reply in enumerate(sequence):
        if position:
            current = run(cont(service, user, current, 'revision-scope-continue'))
        current = run(answer(service, user, current, reply, f'revision-scope-{position}'))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        body = current['current_observation']['text']
        if position:
            follow = body.split('Emlisから：', 1)[1].strip()
            sentences = follow.split('。')[:-1]
            assert len(sentences) == 3 and removed not in body
            assert '少し怖かった' in sentences[0]
            assert '褒められた' in sentences[1] and '回答した時点で少し苦しい' in sentences[1]
            assert '誘われた' in sentences[2] and '誘われた' not in sentences[1]
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved correction must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current


@pytest.mark.parametrize('owner', ['', '私は', '私も', '僕には'])
@pytest.mark.parametrize('copula', ['です', 'でした', 'だ', 'だった'])
@pytest.mark.parametrize('position', [0, 1])
def test_answer_degree_correction_keeps_source_owner_copula_and_prior_time(owner, copula, position):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    old, new = owner + '少し不安' + copula, owner + 'とても不安' + copula
    request = begin()
    if position:
        request = advance(request, 'その時は少し怖かった。')
    request = advance(request, '今は' + old + '。')
    prior = prepare_emlis_meaning(request)
    prior_plan = build_updated_grounded_plan(prior)
    old_id = prior.accepted_nuclei[0].nucleus_id
    old_about = next(r for r in prior_plan.relations
                     if r.type == 'evaluation_about_event' and r.to_nucleus_id == old_id)
    correction = '「' + old + '」ではなく「' + new + '」です。'
    request = advance(request, correction)
    prepared = prepare_emlis_meaning(request)
    update = prepared.checkpoint.answer_update.updates[0]
    assert prepared.checkpoint.assessment_status == 'RESOLVED'
    assert update.operation == 'REVISE' and update.target_meaning_refs == (old_id,)
    assert update.temporal_binding.anchor_source_ref == prior.thread.answers[-1].envelope.envelope_id
    assert update.temporal_binding.about_time == 'ANSWER_TIME'
    context = actual(request=request)
    result, plan, _, resolver, _ = context
    nucleus = prepared.accepted_nuclei[0]
    assert reception.final_reception_source_anchor_text(
        nucleus.nucleus_id, {n.nucleus_id: n for n in plan.nuclei}, resolver) == new
    assert old_id in prepared.checkpoint.inactive_claim_refs and old_id not in {n.nucleus_id for n in plan.nuclei}
    assert any(r.type == 'evaluation_about_event' and r.from_nucleus_id == old_about.from_nucleus_id
               and r.to_nucleus_id == nucleus.nucleus_id for r in plan.relations)
    assert prior.thread.original == prepared.thread.original
    assert all(n in plan.nuclei for n in prior_plan.nuclei if n.nucleus_id != old_id)
    public = MeaningExperienceEngine().generate(request)
    assert public.artifact is not None and public.artifact.text == result.artifact.text
    assert new in public.artifact.observation and old not in public.artifact.text
    assert '今回の観測に反映できていない' not in public.artifact.text
    follow = public.artifact.reception
    assert '先の回答時点では' in follow and 'とても不安' in follow
    assert inverse(context, follow, without_author=True).passed
    mutations = [follow.replace('とても不安', '少し不安'),
                 follow.replace('とても不安', 'とても安心'),
                 follow.replace('先の回答時点では', '回答した時点では'),
                 follow.replace('先の回答時点では', ''),
                 follow.replace('嬉しくなかった', '嬉しかった')]
    if owner:
        phrase = {'私は': 'あなたは', '私も': 'あなたも', '僕には': 'あなたには'}[owner] + 'とても不安'
        mutations.append(follow.replace(phrase, '友人はとても不安', 1))
    # Reception normalizes polite copulas while retaining their source tense.
    mutations.append(follow.replace('不安だったのですね', '不安なのですね')
                     if copula in ('でした', 'だった') else
                     follow.replace('不安なのですね', '不安だったのですね'))
    for changed in mutations:
        assert changed != follow and not inverse(context, changed, without_author=True).passed


@pytest.mark.parametrize('new', [
    '彼はとても不安です', 'あなたはとても不安です', '私はとても不安です',
    'とても不安でした', 'とても不安ではないです', 'とても不安かもしれない',
    'とても不安なら', 'とても安心です', 'とても不安なのです', '未整理',
])
def test_answer_degree_correction_does_not_admit_different_owner_or_predicate(new):
    request = advance(begin(), '今は少し不安です。')
    request = advance(request, '「少し不安です」ではなく「' + new + '」です。')
    prepared = prepare_emlis_meaning(request)
    assert prepared.checkpoint.assessment_status == 'PARTIAL'
    assert prepared.checkpoint.answer_update.updates[0].operation == 'WITHDRAW'
    assert not prepared.accepted_nuclei
    assert prepared.checkpoint.unresolved_parts[0].reason_code == 'correction_replacement_unsupported'


@pytest.mark.parametrize('boundary', ['initial', 'original_memo', 'ambiguous_answer'])
def test_answer_degree_correction_requires_unique_admitted_answer(boundary):
    request = begin(memo_action='少し不安です。' if boundary == 'original_memo' else '')
    if boundary == 'initial':
        request = advance(request, '今はとても不安です。')
    else:
        if boundary == 'ambiguous_answer':
            request = advance(advance(request, '今は少し不安です。'), '今は少し不安です。')
        request = advance(request, '「少し不安です」ではなく「とても不安です」です。')
    prepared = prepare_emlis_meaning(request)
    assert not prepared.accepted_nuclei
    if boundary == 'original_memo':
        assert prepared.checkpoint.answer_update.updates[0].operation == 'WITHDRAW'
        assert prepared.checkpoint.unresolved_parts[0].reason_code == 'correction_replacement_unsupported'
    else:
        assert prepared.checkpoint.assessment_status == 'UNRESOLVED'
        assert not prepared.checkpoint.answer_update.updates and not prepared.checkpoint.inactive_claim_refs


@pytest.mark.parametrize('third', ['「とても不安です」ではなく「少し不安です」です。',
                                  '「とても不安です」ではなく「とても不安です」です。'])
def test_answer_degree_recorrection_preserves_first_answer_anchor(third):
    request = advance(begin(), '今は少し不安です。')
    first = prepare_emlis_meaning(request).thread.answers[0].envelope.envelope_id
    request = advance(advance(request, '「少し不安です」ではなく「とても不安です」です。'), third)
    prepared = prepare_emlis_meaning(request)
    assert prepared.checkpoint.assessment_status == 'RESOLVED'
    update = prepared.checkpoint.answer_update.updates[0]
    assert update.operation == 'REVISE' and update.temporal_binding.anchor_source_ref == first
    context = actual(request=request)
    expected = third.split('」ではなく「')[1].split('」')[0]
    assert reception.final_reception_source_anchor_text(
        prepared.accepted_nuclei[0].nucleus_id,
        {n.nucleus_id: n for n in context[1].nuclei}, context[3]) == expected
    assert expected in context[0].artifact.observation
    assert '先の回答時点では' in context[0].artifact.reception
    assert inverse(context, context[0].artifact.reception, without_author=True).passed


@pytest.mark.parametrize('source,position', [('少し不安です', 0), ('少し不安でした', 1),
                                           ('私も少し不安です', 0), ('僕には少し不安でした', 1)])
def test_answer_degree_saved_correction_withdrawal_and_original_replay(qcase, monkeypatch, source, position):
    from test_emlis_q3_application import cont
    user, parent, service = qcase
    first = current = run(service.start(user, parent))
    corrected = source.replace('少し', 'とても')
    replies = (['その時は少し怖かった。'] if position else []) + [
        '今は' + source + '。', '「' + source + '」ではなく「' + corrected + '」です。']
    if not position:
        replies.append('「' + corrected + '」は誤りです。')
    for index, reply in enumerate(replies):
        if index:
            current = run(cont(service, user, current, f'degree-continue-{index}'))
        current = run(answer(service, user, current, reply, f'degree-answer-{index}'))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        body = current['current_observation']['text']
        if index == position + 1:
            assert corrected in body and source not in body
            assert '先の回答時点では' in body and '今回の観測に反映できていない' not in body
        if not position and index == 2:
            assert corrected not in body and source not in body and '嬉しくなかった' in body
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved degree correction must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current


@pytest.mark.parametrize('source', ['少し不安です', '私も少し不安でした'])
@pytest.mark.parametrize('position', [0, 1])
def test_answer_degree_original_occasion_correction_keeps_original_anchor(source, position):
    request = begin()
    if position:
        request = advance(request, 'その時は少し怖かった。')
    request = advance(request, 'その時は' + source + '。')
    prior = prepare_emlis_meaning(request)
    old_id = prior.accepted_nuclei[0].nucleus_id
    old_about = next(r for r in build_updated_grounded_plan(prior).relations
                     if r.type == 'evaluation_about_event' and r.to_nucleus_id == old_id)
    request = advance(request, '「' + source + '」ではなく「' + source.replace('少し', 'とても') + '」です。')
    prepared = prepare_emlis_meaning(request)
    update = prepared.checkpoint.answer_update.updates[0]
    assert prepared.checkpoint.assessment_status == 'RESOLVED' and update.operation == 'REVISE'
    assert update.temporal_binding.about_time == 'ORIGINAL_OCCASION'
    assert update.temporal_binding.anchor_source_ref == prior.thread.original.envelope.envelope_id
    assert prepared.thread.original == prior.thread.original
    context = actual(request=request)
    new_id = prepared.accepted_nuclei[0].nucleus_id
    assert reception.final_reception_source_anchor_text(
        new_id, {n.nucleus_id: n for n in context[1].nuclei}, context[3]) == source.replace('少し', 'とても')
    assert any(r.type == 'evaluation_about_event' and r.from_nucleus_id == old_about.from_nucleus_id
               and r.to_nucleus_id == new_id for r in context[1].relations)
    follow = context[0].artifact.reception
    assert 'その時は' in follow and 'とても不安' in follow and '回答時点' not in follow
    assert inverse(context, follow, without_author=True).passed
    for changed in (follow.replace('とても不安', '少し不安'),
                    follow.replace('その時は', '先の回答時点では')):
        assert changed != follow and not inverse(context, changed, without_author=True).passed


@pytest.mark.parametrize('source', ['少し重かった', '私も少し苦しかった',
                                    '私は嬉しくなかった', '僕には寂しかった'])
@pytest.mark.parametrize('ending', ['のです', 'のだ', 'のだった'])
@pytest.mark.parametrize('time', ['今は', 'その時は'])
@pytest.mark.parametrize('position', [0, 1])
def test_answer_explanation_revision_preserves_complete_source_and_about(source, ending, time, position):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    request = begin()
    if position:
        request = advance(request, 'その時は少し怖かった。')
    request = advance(request, time + source + '。')
    prior = prepare_emlis_meaning(request)
    prior_plan = build_updated_grounded_plan(prior)
    old_id = prior.accepted_nuclei[0].nucleus_id
    old_about = next(r for r in prior_plan.relations
                     if r.type == 'evaluation_about_event' and r.to_nucleus_id == old_id)
    new = source + ending
    request = advance(request, '「' + source + '」ではなく「' + new + '」です。')
    prepared = prepare_emlis_meaning(request)
    update = prepared.checkpoint.answer_update.updates[0]
    assert prepared.checkpoint.assessment_status == 'RESOLVED' and update.operation == 'REVISE'
    assert update.target_meaning_refs == (old_id,)
    expected_time = 'ANSWER_TIME' if time == '今は' else 'ORIGINAL_OCCASION'
    expected_anchor = (prior.thread.answers[-1].envelope.envelope_id if time == '今は'
                       else prior.thread.original.envelope.envelope_id)
    assert update.temporal_binding.about_time == expected_time
    assert update.temporal_binding.anchor_source_ref == expected_anchor
    context = actual(request=request)
    result, plan, _, resolver, _ = context
    new_id = prepared.accepted_nuclei[0].nucleus_id
    assert reception.final_reception_source_anchor_text(
        new_id, {n.nucleus_id: n for n in plan.nuclei}, resolver) == new
    assert any(r.type == 'evaluation_about_event' and r.from_nucleus_id == old_about.from_nucleus_id
               and r.to_nucleus_id == new_id for r in plan.relations)
    assert old_id in prepared.checkpoint.inactive_claim_refs
    assert all(n in plan.nuclei for n in prior_plan.nuclei if n.nucleus_id != old_id)
    assert prior.thread.original == prepared.thread.original
    public = MeaningExperienceEngine().generate(request)
    assert public.artifact is not None and public.artifact.text == result.artifact.text
    assert '「' + new + '」' in result.artifact.observation
    assert '今回の観測に反映できていない' not in result.artifact.text
    follow = result.artifact.reception
    assert ('先の回答時点では' if time == '今は' else 'その時は') in follow
    if ending == 'のだった':
        assert 'のでしたね' in follow or 'のだったし' in follow
    assert inverse(context, follow, without_author=True).passed


@pytest.fixture(scope='module')
def explained_revision_context():
    request = advance(begin(), '今は私も少し重くなかった。')
    return actual(request=advance(request,
        '「私も少し重くなかった」ではなく「私も少し重くなかったのだった」です。'))


@pytest.mark.parametrize('old,new', [
    ('あなたも少し重くなかった', '友人も少し重くなかった'),
    ('あなたも少し重くなかった', 'あなたは少し重くなかった'),
    ('少し重くなかった', '重くなかった'),
    ('重くなかった', '重かった'),
    ('重くなかった', '重くない'),
    ('のでしたね', 'のですね'),
    ('先の回答時点では', 'その時は'),
    ('先の回答時点では', ''),
    ('褒められたのに', '褒められたから'),
    ('嬉しくなかったし、', ''),
])
def test_answer_explanation_revision_inverse_rejects_semantic_mutations(explained_revision_context, old, new):
    context = explained_revision_context
    follow = context[0].artifact.reception
    assert inverse(context, follow, without_author=True).passed
    changed = follow.replace(old, new, 1)
    assert changed != follow and not inverse(context, changed, without_author=True).passed


@pytest.mark.parametrize('new', ['彼は少し重かったのです', 'あなたは少し重かったのです',
    '少し重かったんです', '少し重かったですのです', '少し重かったのではない',
    '少し重かったかもしれないのです', '少し重かったならのです', '少し重かったのですか',
    '楽しかったのです', '軽かったのです', 'こわかったのです', 'さびしかったのです'])
def test_answer_explanation_revision_keeps_unsupported_source_boundary(new):
    request = advance(advance(begin(), '今は少し重かった。'),
        '「少し重かった」ではなく「' + new + '」です。')
    prepared = prepare_emlis_meaning(request)
    assert prepared.checkpoint.assessment_status == 'PARTIAL'
    assert prepared.checkpoint.answer_update.updates[0].operation == 'WITHDRAW'
    assert not prepared.accepted_nuclei
    assert prepared.checkpoint.unresolved_parts[0].reason_code == 'correction_replacement_unsupported'


@pytest.mark.parametrize('boundary', ['initial', 'original_memo', 'ambiguous_answer'])
def test_answer_explanation_revision_requires_unique_existing_answer(boundary):
    request = begin()
    if boundary == 'original_memo':
        # Check the pure meaning boundary even when this original material
        # cannot yet produce a Q3 initial body. Do not fabricate a public round.
        request = answered('「少し重かった」ではなく「少し重かったのです」です。',
                           initial(memo_action='少し重かった。'))
    elif boundary == 'initial':
        request = advance(request, 'その時は少し重かったのです。')
    else:
        if boundary == 'ambiguous_answer':
            request = advance(advance(request, '今は少し重かった。'), '今は少し重かった。')
        request = advance(request, '「少し重かった」ではなく「少し重かったのです」です。')
    prepared = prepare_emlis_meaning(request)
    assert not prepared.accepted_nuclei
    if boundary == 'original_memo':
        assert prepared.checkpoint.answer_update.updates[0].operation == 'WITHDRAW'
        assert prepared.checkpoint.unresolved_parts[0].reason_code == 'correction_replacement_unsupported'
    else:
        assert prepared.checkpoint.assessment_status == 'UNRESOLVED'
        assert not prepared.checkpoint.answer_update.updates and not prepared.checkpoint.inactive_claim_refs


@pytest.mark.parametrize('third', ['「少し重かったのです」ではなく「少し苦しかったのだった」です。',
                                  '「少し重かったのです」は誤りです。'])
def test_answer_explanation_recorrection_or_withdrawal_keeps_original_anchor(third):
    request = advance(begin(), '今は少し重かった。')
    first_anchor = prepare_emlis_meaning(request).thread.answers[0].envelope.envelope_id
    request = advance(advance(request,
        '「少し重かった」ではなく「少し重かったのです」です。'), third)
    prepared = prepare_emlis_meaning(request)
    update = prepared.checkpoint.answer_update.updates[0]
    assert prepared.checkpoint.assessment_status == 'RESOLVED'
    assert update.temporal_binding.anchor_source_ref == first_anchor
    context = actual(request=request)
    assert '「少し重かったのです」' not in context[0].artifact.observation
    if 'ではなく' in third:
        assert update.operation == 'REVISE'
        assert '「少し苦しかったのだった」' in context[0].artifact.observation
        assert '先の回答時点では' in context[0].artifact.reception
    else:
        assert update.operation == 'WITHDRAW' and '重かった' not in context[0].artifact.text
    assert inverse(context, context[0].artifact.reception, without_author=True).passed


@pytest.mark.parametrize('time,ending', [('今は', 'のです'), ('その時は', 'のです'),
                                       ('今は', 'のだった'), ('その時は', 'のだ')])
def test_answer_explanation_saved_revision_withdrawal_and_original_replay(qcase, monkeypatch, time, ending):
    from test_emlis_q3_application import cont
    user, parent, service = qcase
    first = current = run(service.start(user, parent))
    new = '私も少し重かった' + ending
    replies = [time + '私も少し重かった。',
               '「私も少し重かった」ではなく「' + new + '」です。', '「' + new + '」は誤りです。']
    for index, reply in enumerate(replies):
        if index:
            current = run(cont(service, user, current, f'explanation-continue-{index}'))
        current = run(answer(service, user, current, reply, f'explanation-answer-{index}'))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        body = current['current_observation']['text']
        if index == 1:
            assert '「' + new + '」' in body and '今回の観測に反映できていない' not in body
        if index == 2:
            assert '重かった' not in body and '嬉しくなかった' in body
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved explanation must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
@pytest.mark.parametrize('replies,visible', [
    (('今は嬉しい。', 'その時は楽しかった。', '今は安心なのです。'),
     ('嬉しい', '楽しかった', '安心なの')),
    (('今は少し私は少し安心です。', 'その時は私も楽しかった。', '今は私も嬉しい。'),
     ('少しあなたは少し安心', 'あなたも楽しかった', 'あなたも嬉しい')),
    (('今は安心なのです。', 'その時は幸せだったのです。', '今は私も嬉しい。'),
     ('安心なの', '幸せだったの', 'あなたも嬉しい')),
])
def test_received_chain_positive_group_keeps_two_and_three_answers(field, replies, visible):
    from test_cmee_emlis_detached_observation import read_body
    from emlis_ai_grounded_human_reception import final_reception_source_anchor_text
    request = begin(RECEIVED_CHAIN_MULTI if field == 'memo' else '',
                    RECEIVED_CHAIN_MULTI if field == 'memo_action' else '')
    for count, reply in enumerate(replies, 1):
        request = advance(request, reply)
        context = actual(request=request)
        result, plan, sentence, resolver, selected = context
        follow = result.artifact.reception
        assert len(plan.response_plan.human_reception_plan.moves) == 3
        assert follow.count('。') == 3
        assert '褒められたのに、悲しかったけれど、嬉しかったのですね。' in follow
        assert '誘われたのに、寂しさを感じ、頼まれたのに、怖さを感じたのですね。' in follow
        assert read_body(context, result.artifact.text).passed
        if count == 1:
            # The unchanged single-answer route can retain nominal source
            # wording; the finite group starts with the second answer.
            continue
        assert all(fragment in follow for fragment in visible[:count])
        moves = plan.response_plan.human_reception_plan.moves
        group, = (m for m in moves if m.reception_act == 'recognize_lived_change')
        assert len(group.target_nucleus_ids) == count and not group.support_nucleus_ids
        line, = (line for line in sentence.lines if line.binding.line_role == 'human_follow')
        parts = [part + '。' for part in follow.removesuffix('。').split('。')]
        part, = (part for clause, part in zip(line.reception_clause_plans, parts, strict=True)
                 if clause.move_ids == (group.move_id,))
        index = {n.nucleus_id: n for n in plan.nuclei}
        expected = []
        for nid in group.target_nucleus_ids:
            about, = (r for r in plan.relations if r.type == 'evaluation_about_event'
                      and r.to_nucleus_id == nid and r.retention == 'required')
            expected.extend(final_reception_source_anchor_text(source_id, index, resolver).encode()
                            for source_id in (about.from_nucleus_id, nid))
        with patch.object(reception, '_source_owned_positive_answer_group_sentence',
                          side_effect=AssertionError('group author is not a reader')), patch.object(
                reception, '_source_owned_answer_feeling_sentence',
                side_effect=AssertionError('single author is not a reader')), patch.object(
                reception, '_detached_feeling_finite_surface',
                side_effect=AssertionError('finite author is not a reader')):
            proof = gate.read_source_owned_discourse(part, group, plan, resolver, selected)
            assert proof is not None and len(proof) == 2 * count
            assert [source for _, _, source in proof] == expected
            assert all(part.encode()[a:b] for a, b, _ in proof)
            assert read_body(context, result.artifact.text).passed


@pytest.mark.parametrize('count', [2, 3])
def test_received_chain_positive_group_inverse_rejects_lost_or_changed_meaning(count):
    from test_cmee_emlis_detached_observation import read_body
    request = begin(RECEIVED_CHAIN_MULTI)
    for reply in ('今は嬉しい。', 'その時は楽しかった。', '今は安心なのです。')[:count]:
        request = advance(request, reply)
    context = actual(request=request)
    body, follow = context[0].artifact.text, context[0].artifact.reception
    mutations = [
        follow.replace('褒められたことについて、回答した時点では嬉しいし、', '', 1),
        follow.replace('褒められたことについて、', '頼まれたことについて、', 1),
        follow.replace('誘われたことについて、', '褒められたことについて、', 1),
        follow.replace('回答した時点では嬉しい', 'その時は嬉しい', 1),
        follow.replace('その時は楽しかった', '回答した時点では楽しかった', 1),
        follow.replace('では嬉しい', 'では嬉しくない', 1),
        follow.replace('その時は楽しかった', 'その時は楽しい', 1),
        follow.replace('悲しかったけれど、嬉しかった', '悲しかったから、嬉しかった', 1),
        follow.replace('悲しかったけれど、', '', 1),
        follow.replace('頼まれたのに、怖さを感じた', '頼まれたのに、安心を感じた', 1),
    ]
    with patch.object(reception, '_source_owned_positive_answer_group_sentence',
                      side_effect=AssertionError('no group author')), patch.object(
            reception, '_source_owned_answer_feeling_sentence', side_effect=AssertionError('no single author')):
        assert read_body(context, body).passed
        for changed in mutations:
            assert changed != follow
            assert not read_body(context, body.replace(follow, changed)).passed


@pytest.mark.parametrize('third,retained,removed', [
    ('今は安心なのです。', ('回答した時点では安心なのですね', 'その時は楽しかった'), ()),
    ('「嬉しい」ではなく「少し楽しい」です。', ('先の回答時点では少し楽しい', 'その時は楽しかった'), ('では嬉しい',)),
    ('「嬉しい」は誤りです。', ('その時に楽しかった',), ('では嬉しい', '時点で嬉しい')),
])
def test_received_chain_positive_group_saved_add_correct_withdraw(qcase, qdb, monkeypatch, third, retained, removed):
    from test_emlis_q3_application import cont
    user, parent, service = qcase
    qdb.query('update public.emotions set memo=$1 where id=$2', [RECEIVED_CHAIN_MULTI, parent])
    first = run(service.start(user, parent))
    original = first['original']
    current = first
    for index, reply in enumerate(('今は嬉しい。', 'その時は楽しかった。', third)):
        if index:
            current = run(cont(service, user, current, f'chain-positive-continue-{index}'))
        current = run(answer(service, user, current, reply, f'chain-positive-answer-{index}'))
        assert current['body_state'] == 'REFINED' and current['original'] == original
        follow = current['current_observation']['text'].split('Emlisから：\n', 1)[1]
        assert follow.count('。') == 3
        assert '褒められたのに、悲しかったけれど、嬉しかったのですね。' in follow
        assert '誘われたのに、寂しさを感じ、頼まれたのに、怖さを感じたのですね。' in follow
        if index == 2:
            assert all(value in follow for value in retained)
            assert all(value not in follow for value in removed)
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved chain must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current
        assert qdb.query('select memo from public.emotions where id=$1', [parent])['rows'][0]['memo'] == RECEIVED_CHAIN_MULTI
    assert current['state'] == 'COMPLETED' and not current['can_continue']


def test_received_chain_positive_group_does_not_admit_unresolved_third_answer():
    request = advance(advance(begin(RECEIVED_CHAIN_MULTI), '今は少し私は少し安心です。'),
                      'その時は私も楽しかった。')
    before = actual(request=request)
    updated = advance(request, '今はとても幸せです。')
    prepared = prepare_emlis_meaning(updated)
    assert prepared.checkpoint.assessment_status == 'UNRESOLVED'
    assert not prepared.accepted_nuclei
    assert prepared.checkpoint.unresolved_parts[0].reason_code == 'answer_syntax_unsupported'
    after = actual(request=updated)
    retained = tuple(n for n in before[1].nuclei if n.source_fields == ('answer_text_private',))
    assert len(retained) == 2
    assert tuple(n for n in after[1].nuclei if n.source_fields == ('answer_text_private',)) == retained
    assert after[0].artifact.reception == before[0].artifact.reception
    assert after[0].artifact.observation.startswith(before[0].artifact.observation)
    assert '回答の「今はとても幸せです」には、今回の観測に反映できていない部分があります。' in after[0].artifact.observation


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
@pytest.mark.parametrize('replies,visible', [
    (('今は嬉しい。', 'その時は楽しかった。'), ('回答した時点では嬉しい', 'その時は楽しかった')),
    (('その時は楽しかった。', '今は少し安心です。'), ('その時は楽しかった', '回答した時点では少し安心')),
    (('今は少し私は少し安心です。', 'その時は私も楽しかった。'),
     ('回答した時点では少しあなたは少し安心', 'その時はあなたも楽しかった')),
    (('今は安心なのです。', 'その時は幸せだったのです。'),
     ('回答した時点では安心なのだ', 'その時は幸せだったの')),
])
def test_received_chain_detached_positive_group_keeps_source_time_and_survivors(field, replies, visible):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    from test_cmee_emlis_detached_observation import read_body
    request = begin(RECEIVED_CHAIN_MULTI if field == 'memo' else '',
                    RECEIVED_CHAIN_MULTI if field == 'memo_action' else '')
    for text in (*replies, '「褒められた」は誤りです。'):
        request = advance(request, text)
    context = actual(request=request)
    result, plan, sentence, resolver, selected = context
    public = MeaningExperienceEngine().generate(request)
    assert public.artifact is not None and public.artifact.text == result.artifact.text
    follow = result.artifact.reception
    assert '褒められた' not in result.artifact.text
    assert '悲しかったけれど、嬉しかったのですね。' in follow
    assert '誘われたのに、寂しさを感じ、頼まれたのに、怖さを感じたのですね。' in follow
    assert '先の回答では、' + visible[0] in follow and visible[1] in follow
    assert follow.count('。') == len(plan.response_plan.human_reception_plan.moves) == 3
    group, = (m for m in plan.response_plan.human_reception_plan.moves
              if len(m.target_nucleus_ids) == 2 and m.reception_act == 'recognize_lived_change')
    assert not group.support_nucleus_ids
    index = {n.nucleus_id: n for n in plan.nuclei}
    detached, linked = (index[nid] for nid in group.target_nucleus_ids)
    assert 'thread_subject:withdrawn_source_event' in detached.semantic_frame.attribute_codes
    assert not any(detached.nucleus_id in (r.from_nucleus_id, r.to_nucleus_id) for r in plan.relations)
    about, = (r for r in plan.relations if r.type == 'evaluation_about_event' and r.to_nucleus_id == linked.nucleus_id)
    expected = [reception.final_reception_source_anchor_text(nid, index, resolver).encode()
                for nid in (detached.nucleus_id, about.from_nucleus_id, linked.nucleus_id)]
    part, = (p + '。' for p in follow.removesuffix('。').split('。') if p.startswith('先の回答では、'))
    with (patch.object(reception, '_source_owned_positive_answer_group_sentence', side_effect=AssertionError('no author')),
          patch.object(reception, '_source_owned_answer_feeling_sentence', side_effect=AssertionError('no author')),
          patch.object(reception, '_detached_feeling_finite_surface', side_effect=AssertionError('no author'))):
        proof = gate.read_source_owned_discourse(part, group, plan, resolver, selected)
        assert proof is not None and len(proof) == 3
        assert [source for _, _, source in proof] == expected
        assert all(0 <= a < b <= len(part.encode()) for a, b, _ in proof)
        assert read_body(context, result.artifact.text).passed


def test_received_chain_detached_positive_group_inverse_rejects_scope_or_meaning_changes():
    from test_cmee_emlis_detached_observation import read_body
    request = begin(RECEIVED_CHAIN_MULTI)
    for text in ('今は嬉しい。', 'その時は楽しかった。', '「褒められた」は誤りです。'):
        request = advance(request, text)
    context = actual(request=request)
    body, follow = context[0].artifact.text, context[0].artifact.reception
    changes = [
        follow.replace('先の回答では、', ''),
        follow.replace('先の回答では、', '褒められたことについて、先の回答では、'),
        follow.replace('先の回答では、', '先の回答では、誘われたことについて、'),
        follow.replace('回答した時点では嬉しい', 'その時は嬉しい'),
        follow.replace('その時は楽しかった', '回答した時点では楽しかった'),
        follow.replace('では嬉しい', 'では嬉しくない'),
        follow.replace('その時は楽しかった', 'その時は楽しい'),
        follow.replace('誘われたことについて、', '頼まれたことについて、'),
        follow.replace('先の回答では、回答した時点では嬉しいし、', ''),
        follow.replace('し、誘われたことについて、その時は楽しかったのですね。', 'のですね。'),
        follow.replace('悲しかったけれど、嬉しかったのですね。', ''),
        follow.replace('悲しかったけれど、', '悲しかったから、'),
        follow.replace('頼まれたのに、怖さを感じた', '頼まれたのに、安心を感じた'),
    ]
    with patch.object(reception, '_source_owned_positive_answer_group_sentence', side_effect=AssertionError('no author')):
        assert read_body(context, body).passed
        for changed in changes:
            assert changed != follow
            assert not read_body(context, body.replace(follow, changed)).passed


@pytest.mark.parametrize('change', ['marker', 'relation', 'time', 'polarity', 'field'])
def test_received_chain_detached_positive_group_requires_detached_source_proof(change):
    from dataclasses import replace
    request = begin(RECEIVED_CHAIN_MULTI)
    for text in ('今は嬉しい。', 'その時は楽しかった。', '「褒められた」は誤りです。'):
        request = advance(request, text)
    result, plan, _, resolver, selected = actual(request=request)
    move, = (m for m in plan.response_plan.human_reception_plan.moves
             if m.reception_act == 'recognize_lived_change' and len(m.target_nucleus_ids) == 2)
    first = next(n for n in plan.nuclei if n.nucleus_id == move.target_nucleus_ids[0])
    follow, = (p + '。' for p in result.artifact.reception.removesuffix('。').split('。') if p.startswith('先の回答では、'))
    if change == 'relation':
        about, = (r for r in plan.relations if r.type == 'evaluation_about_event')
        plan = replace(plan, relations=(*plan.relations, replace(about, relation_id='invalid-detached-about',
                                                               to_nucleus_id=first.nucleus_id)))
    else:
        frame = first.semantic_frame
        if change == 'marker':
            frame = replace(frame, attribute_codes=tuple(c for c in frame.attribute_codes if c != 'thread_subject:withdrawn_source_event'))
        elif change == 'time':
            frame = replace(frame, attribute_codes=tuple('thread_time:original_occasion' if c == 'thread_time:answer_time' else c for c in frame.attribute_codes), time_scope='past')
        elif change == 'polarity':
            frame = replace(frame, polarity='negative')
        changed = replace(first, semantic_frame=frame, source_fields=('memo',) if change == 'field' else first.source_fields)
        plan = replace(plan, nuclei=tuple(changed if n.nucleus_id == first.nucleus_id else n for n in plan.nuclei))
    with patch.object(reception, '_source_owned_positive_answer_group_sentence', side_effect=AssertionError('no author')):
        assert gate._read_positive_answer_group_discourse(follow, move, plan, resolver, selected) is None


@pytest.mark.parametrize('replies', [
    ('今は嬉しい。', 'その時は楽しかった。'),
    ('その時は楽しかった。', '今は少し安心です。'),
    ('今は安心なのです。', 'その時は幸せだったのです。'),
])
def test_received_chain_detached_positive_group_saved_withdrawal(qcase, qdb, monkeypatch, replies):
    from test_emlis_q3_application import cont
    user, parent, service = qcase
    qdb.query('update public.emotions set memo=$1 where id=$2', [RECEIVED_CHAIN_MULTI, parent])
    first = current = run(service.start(user, parent))
    for i, text in enumerate((*replies, '「褒められた」は誤りです。')):
        if i:
            current = run(cont(service, user, current, f'detached-positive-continue-{i}'))
        current = run(answer(service, user, current, text, f'detached-positive-answer-{i}'))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        if i == 2:
            body = current['current_observation']['text']
            assert '褒められた' not in body and '先の回答では、' in body
            assert all(x in body for x in ('悲しかった', '嬉しかった', '誘われた', '寂し', '頼まれた', '怖'))
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved withdrawal must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current
        assert qdb.query('select memo from public.emotions where id=$1', [parent])['rows'][0]['memo'] == RECEIVED_CHAIN_MULTI
    assert current['state'] == 'COMPLETED' and not current['can_continue']



def test_received_chain_detached_positive_group_does_not_promote_repeated_original_feeling():
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    request = advance(begin(RECEIVED_CHAIN_MULTI), 'その時は嬉しかった。')
    prepared = prepare_emlis_meaning(request)
    assert prepared.checkpoint.answer_update.disposition == 'NO_MATERIAL_UPDATE'
    assert not prepared.accepted_nuclei
    outcome = MeaningExperienceEngine().generate(request)
    assert outcome.artifact is None and outcome.body_state == 'UNCHANGED'
    assert outcome.reason_codes == ('reuse_saved_observation_required',)


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
@pytest.mark.parametrize('replies,replacement,visible', [
    (('今は嬉しい。', 'その時は楽しかった。'), '少し怖かった',
     ('回答した時点では嬉しい', 'その時は楽しかった', '当時は少し怖かった')),
    (('その時は楽しかった。', '今は少し安心です。'), '少し怖かった',
     ('その時は楽しかった', '回答した時点では少し安心', '当時は少し怖かった')),
    (('今は少し私は少し安心です。', 'その時は私も楽しかった。'), '私も少し怖かった',
     ('回答した時点では少しあなたは少し安心', 'その時はあなたも楽しかった', '当時、あなたも少し怖かった')),
    (('今は安心なのです。', 'その時は幸せだったのです。'), '少し怖かったのです',
     ('回答した時点では安心なのだ', 'その時は幸せだったの', '当時は少し怖かったの')),
])
def test_received_chain_middle_revision_keeps_every_source_in_reception(field, replies, replacement, visible):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    from test_cmee_emlis_detached_observation import read_body
    request = begin(RECEIVED_CHAIN_MULTI if field == 'memo' else '',
                    RECEIVED_CHAIN_MULTI if field == 'memo_action' else '')
    for text in (*replies, '「悲しかった」ではなく「' + replacement + '」です。'):
        request = advance(request, text)
    context = actual(request=request)
    result, plan, sentence, resolver, selected = context
    public = MeaningExperienceEngine().generate(request)
    assert public.artifact is not None and public.artifact.text == result.artifact.text
    follow = result.artifact.reception
    assert '悲しかった' not in result.artifact.text
    assert all(s in follow for s in (*visible, '嬉しかった', '誘われたのに、寂し', '頼まれたのに、怖'))
    assert '言い直してくださった気持ちについては、' in follow
    moves = plan.response_plan.human_reception_plan.moves
    assert len(moves) == follow.count('。') == 3
    assert not any(r.type == 'contrast' and r.source_span_ids == ('s1',) for r in plan.relations)
    revised, = (n for n in plan.nuclei if 'thread_subject:revised_original_reaction' in n.semantic_frame.attribute_codes)
    survivor, = (n for n in plan.nuclei if 'source_received_chain_slot:second' in n.semantic_frame.attribute_codes)
    assert not any({revised.nucleus_id, survivor.nucleus_id} & {r.from_nucleus_id, r.to_nucleus_id}
                   for r in plan.relations)
    # Every required text contribution owns a reception target, support or
    # event context. Observation coverage alone cannot satisfy this check.
    covered = {nid for move in moves for nid in (*move.target_nucleus_ids, *move.support_nucleus_ids,
               *reception.final_reception_context_nucleus_ids(move=move, plan=plan))}
    required = {n.nucleus_id for n in plan.nuclei if n.retention == 'required'
                and n.source_fields in {(field,), ('answer_text_private',)}}
    assert required <= covered
    index = {n.nucleus_id: n for n in plan.nuclei}
    line, = (line for line in sentence.lines if line.binding.line_role == 'human_follow')
    parts = [p + '。' for p in follow.removesuffix('。').split('。')]
    with (patch.object(reception, '_source_owned_positive_answer_group_sentence', side_effect=AssertionError('no author')),
          patch.object(reception, '_source_grounded_received_discourse', side_effect=AssertionError('no author')),
          patch.object(reception, '_detached_feeling_finite_surface', side_effect=AssertionError('no author'))):
        for clause, part in zip(line.reception_clause_plans, parts, strict=True):
            move, = (m for m in moves if clause.move_ids == (m.move_id,))
            if len(move.target_nucleus_ids) == 1:
                continue
            if move.reception_act == 'recognize_lived_change':
                source_ids = []
                for nid in move.target_nucleus_ids:
                    about, = (r for r in plan.relations if r.type == 'evaluation_about_event' and r.to_nucleus_id == nid)
                    source_ids.extend((about.from_nucleus_id, nid))
            else:
                source_ids = []
                for nid in move.target_nucleus_ids:
                    # The received reader proves event roles internally;
                    # its returned byte ranges restore feeling predicates.
                    if index[nid].kind == 'reaction':
                        source_ids.append(nid)
                    source_ids.extend(r.to_nucleus_id for r in plan.relations
                                      if r.type == 'contrast' and r.from_nucleus_id == nid)
            proof = gate.read_source_owned_discourse(part, move, plan, resolver, selected)
            assert proof is not None
            assert [source for _, _, source in proof] == [
                reception.final_reception_source_anchor_text(nid, index, resolver).encode() for nid in source_ids]
            assert all(0 <= a < b <= len(part.encode()) for a, b, _ in proof)
        assert read_body(context, result.artifact.text).passed


def test_received_chain_middle_revision_rejects_missing_or_relinked_reception():
    from test_cmee_emlis_detached_observation import read_body
    request = begin(RECEIVED_CHAIN_MULTI)
    for text in ('今は嬉しい。', 'その時は楽しかった。', '「悲しかった」ではなく「少し怖かった」です。'):
        request = advance(request, text)
    context = actual(request=request)
    body, follow = context[0].artifact.text, context[0].artifact.reception
    changes = [
        follow.replace('嬉しかったという気持ちを受け止めています。', ''),
        follow.replace('褒められたことについて、回答した時点では嬉しいし、', ''),
        follow.replace('し、誘われたことについて、その時は楽しかったのですね。', 'のですね。'),
        follow.replace('誘われたのに、寂しさを感じ、', ''),
        follow.replace('頼まれたのに、怖さを感じ、', ''),
        follow.replace('、言い直してくださった気持ちについては、当時は少し怖かったのですね。', 'たのですね。'),
        follow.replace('嬉しかったという気持ち', '少し怖かったけれど嬉しかったという気持ち'),
        follow.replace('言い直してくださった気持ちについては、', '褒められたから、'),
        follow.replace('回答した時点では嬉しい', 'その時は嬉しい'),
        follow.replace('その時は楽しかった', '回答した時点では楽しかった'),
        follow.replace('誘われたことについて、', '頼まれたことについて、'),
        follow.replace('当時は少し怖かった', '当時は少し怖くなかった'),
        follow.replace('誘われたのに、寂しさ', '褒められたのに、寂しさ'),
        follow.replace('頼まれたのに、怖さ', '頼まれたから、怖さ'),
    ]
    with (patch.object(reception, '_source_owned_positive_answer_group_sentence', side_effect=AssertionError('no author')),
          patch.object(reception, '_source_grounded_received_discourse', side_effect=AssertionError('no author'))):
        assert read_body(context, body).passed
        for changed in changes:
            assert changed != follow
            assert not read_body(context, body.replace(follow, changed)).passed


@pytest.mark.parametrize('replies,replacement,retained', [
    (('今は嬉しい。', 'その時は楽しかった。'), '少し怖かった', ('では嬉しい', 'その時は楽しかった')),
    (('その時は楽しかった。', '今は少し安心です。'), '少し怖かった', ('その時は楽しかった', '時点では少し安心')),
    (('今は安心なのです。', 'その時は幸せだったのです。'), '少し怖かったのです', ('では安心なのだ', 'その時は幸せだったの')),
])
def test_received_chain_middle_revision_saved_body_retains_all_sources(qcase, qdb, monkeypatch, replies, replacement, retained):
    from test_emlis_q3_application import cont
    user, parent, service = qcase
    qdb.query('update public.emotions set memo=$1 where id=$2', [RECEIVED_CHAIN_MULTI, parent])
    first = current = run(service.start(user, parent))
    for i, text in enumerate((*replies, '「悲しかった」ではなく「' + replacement + '」です。')):
        if i:
            current = run(cont(service, user, current, f'middle-revision-continue-{i}'))
        current = run(answer(service, user, current, text, f'middle-revision-answer-{i}'))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        if i == 2:
            body = current['current_observation']['text']
            follow = body.split('Emlisから：\n', 1)[1]
            assert '悲しかった' not in body and follow.count('。') == 3
            assert all(s in follow for s in (*retained, '嬉しかった', '誘われたのに、寂し',
                                             '頼まれたのに、怖', '当時は少し怖かった'))
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved revision must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current
        assert qdb.query('select memo from public.emotions where id=$1', [parent])['rows'][0]['memo'] == RECEIVED_CHAIN_MULTI
    assert current['state'] == 'COMPLETED' and not current['can_continue']


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
@pytest.mark.parametrize('replies,replacement,visible', [
    (('今は嬉しい。', 'その時は楽しかった。'), '少し楽しかった',
     ('回答した時点では嬉しい', 'その時は楽しかった', '当時は少し楽しかった')),
    (('その時は楽しかった。', '今は少し安心です。'), '少し安心だった',
     ('その時は楽しかった', '回答した時点では少し安心', '当時は少し安心だった')),
    (('今は少し私は少し安心です。', 'その時は私も楽しかった。'), '私も少し楽しかった',
     ('回答した時点では少しあなたは少し安心', 'その時はあなたも楽しかった', '当時、あなたも少し楽しかった')),
])
def test_received_chain_positive_revision_keeps_every_source_in_reception(field, replies, replacement, visible):
    # Use the same complete source-coverage and independent byte-reading
    # assertions for either polarity; no old case or expectation is replaced.
    test_received_chain_middle_revision_keeps_every_source_in_reception(field, replies, replacement, visible)


def test_received_chain_positive_revision_rejects_missing_or_relinked_reception():
    from test_cmee_emlis_detached_observation import read_body
    request = begin(RECEIVED_CHAIN_MULTI)
    for text in ('今は嬉しい。', 'その時は楽しかった。', '「悲しかった」ではなく「少し楽しかった」です。'):
        request = advance(request, text)
    context = actual(request=request)
    body, follow = context[0].artifact.text, context[0].artifact.reception
    changes = [
        follow.replace('嬉しかったという気持ちを受け止めています。', ''),
        follow.replace('褒められたことについて、回答した時点では嬉しいし、', ''),
        follow.replace('し、誘われたことについて、その時は楽しかったのですね。', 'のですね。'),
        follow.replace('誘われたのに、寂しさを感じ、', ''),
        follow.replace('頼まれたのに、怖さを感じ、', ''),
        follow.replace('、言い直してくださった気持ちについては、当時は少し楽しかったのですね。', 'たのですね。'),
        follow.replace('嬉しかったという気持ち', '少し楽しかったけれど嬉しかったという気持ち'),
        follow.replace('言い直してくださった気持ちについては、', '褒められたから、'),
        follow.replace('回答した時点では嬉しい', 'その時は嬉しい'),
        follow.replace('その時は楽しかった', '回答した時点では楽しかった'),
        follow.replace('誘われたことについて、', '頼まれたことについて、'),
        follow.replace('当時は少し楽しかった', '当時は少し楽しくなかった'),
        follow.replace('誘われたのに、寂しさ', '褒められたのに、寂しさ'),
        follow.replace('頼まれたのに、怖さ', '頼まれたから、怖さ'),
        follow.replace('当時は少し楽しかった', '当時は楽しかった'),
        follow.replace('当時は少し楽しかった', '当時は友人が少し楽しかった'),
    ]
    with (patch.object(reception, '_source_owned_positive_answer_group_sentence', side_effect=AssertionError('no author')),
          patch.object(reception, '_source_grounded_received_discourse', side_effect=AssertionError('no author'))):
        assert read_body(context, body).passed
        for changed in changes:
            assert changed != follow
            assert not read_body(context, body.replace(follow, changed)).passed


@pytest.mark.parametrize('change', ['marker', 'relation', 'time', 'unsupported_polarity', 'field', 'actor'])
def test_received_chain_positive_revision_requires_independent_source_proof(change):
    from dataclasses import replace
    request = begin(RECEIVED_CHAIN_MULTI)
    for text in ('今は嬉しい。', 'その時は楽しかった。', '「悲しかった」ではなく「少し楽しかった」です。'):
        request = advance(request, text)
    result, plan, _, resolver, selected = actual(request=request)
    revised, = (n for n in plan.nuclei if 'thread_subject:revised_original_reaction' in n.semantic_frame.attribute_codes)
    move, = (m for m in plan.response_plan.human_reception_plan.moves if revised.nucleus_id in m.target_nucleus_ids)
    follow, = (p + '。' for p in result.artifact.reception.removesuffix('。').split('。')
               if '言い直してくださった気持ちについては、' in p)
    assert gate.read_source_owned_discourse(follow, move, plan, resolver, selected) is not None
    if change == 'relation':
        about = next(r for r in plan.relations if r.type == 'evaluation_about_event')
        plan = replace(plan, relations=(*plan.relations, replace(about, relation_id='invalid-revision-about',
                                                               to_nucleus_id=revised.nucleus_id)))
    else:
        frame = revised.semantic_frame
        if change == 'marker':
            frame = replace(frame, attribute_codes=tuple(c for c in frame.attribute_codes if c != 'thread_subject:independent_source_replacement'))
        elif change == 'time':
            frame = replace(frame, time_scope='present')
        elif change == 'unsupported_polarity':
            # Both positive and negative are admitted revision shapes.
            # The independent reader proves visible polarity against the
            # complete source; it does not rerun semantic classification.
            frame = replace(frame, polarity='neutral')
        elif change == 'actor':
            frame = replace(frame, actor='other_person')
        changed = replace(revised, semantic_frame=frame, source_fields=('memo',) if change == 'field' else revised.source_fields)
        plan = replace(plan, nuclei=tuple(changed if n.nucleus_id == revised.nucleus_id else n for n in plan.nuclei))
    with patch.object(reception, '_source_grounded_received_discourse', side_effect=AssertionError('no author')):
        assert gate.read_source_owned_discourse(follow, move, plan, resolver, selected) is None


@pytest.mark.parametrize('replies,replacement,retained', [
    (('今は嬉しい。', 'その時は楽しかった。'), '少し楽しかった', ('では嬉しい', 'その時は楽しかった')),
    (('その時は楽しかった。', '今は少し安心です。'), '少し楽しかった', ('その時は楽しかった', '時点では少し安心')),
    (('今は少し私は少し安心です。', 'その時は私も楽しかった。'), '少し楽しかった', ('では少しあなたは少し安心', 'その時はあなたも楽しかった')),
])
def test_received_chain_positive_revision_saved_body_retains_all_sources(qcase, qdb, monkeypatch, replies, replacement, retained):
    from test_emlis_q3_application import cont
    user, parent, service = qcase
    qdb.query('update public.emotions set memo=$1 where id=$2', [RECEIVED_CHAIN_MULTI, parent])
    first = current = run(service.start(user, parent))
    for i, text in enumerate((*replies, '「悲しかった」ではなく「' + replacement + '」です。')):
        if i:
            current = run(cont(service, user, current, f'positive-revision-continue-{i}'))
        current = run(answer(service, user, current, text, f'positive-revision-answer-{i}'))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        if i == 2:
            body = current['current_observation']['text']
            follow = body.split('Emlisから：\n', 1)[1]
            assert '悲しかった' not in body and follow.count('。') == 3
            assert all(s in follow for s in (*retained, '嬉しかった', '誘われたのに、寂し',
                                             '頼まれたのに、怖', '当時は少し楽しかった'))
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved revision must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current
        assert qdb.query('select memo from public.emotions where id=$1', [parent])['rows'][0]['memo'] == RECEIVED_CHAIN_MULTI
    assert current['state'] == 'COMPLETED' and not current['can_continue']


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
@pytest.mark.parametrize('replies,replacement,visible', [
    (('今は嬉しい。', 'その時は楽しかった。'), '少し怖かった',
     ('回答した時点では嬉しい', 'その時は楽しかった', '当時は少し怖かった')),
    (('その時は楽しかった。', '今は少し安心です。'), '少し怖かった',
     ('その時は楽しかった', '回答した時点では少し安心', '当時は少し怖かった')),
    (('今は少し私は少し安心です。', 'その時は私も楽しかった。'), '私も少し怖かった',
     ('回答した時点では少しあなたは少し安心', 'その時はあなたも楽しかった', '当時、あなたも少し怖かった')),
    (('今は安心なのです。', 'その時は幸せだったのです。'), '少し怖かったのです',
     ('回答した時点では安心なのだ', 'その時は幸せだったの', '当時は少し怖かったの')),
])
def test_received_chain_final_revision_keeps_every_source_in_reception(field, replies, replacement, visible):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    from test_cmee_emlis_detached_observation import read_body
    request = begin(RECEIVED_CHAIN_MULTI if field == 'memo' else '',
                    RECEIVED_CHAIN_MULTI if field == 'memo_action' else '')
    for text in (*replies, '「嬉しかった」ではなく「' + replacement + '」です。'):
        request = advance(request, text)
    context = actual(request=request)
    result, plan, sentence, resolver, selected = context
    public = MeaningExperienceEngine().generate(request)
    assert public.artifact is not None and public.artifact.text == result.artifact.text
    follow = result.artifact.reception
    assert '嬉しかった' not in result.artifact.text
    assert all(s in follow for s in (*visible, '褒められたのに、悲しかった', '誘われたのに、寂し', '頼まれたのに、怖'))
    assert '言い直してくださった気持ちについては、' in follow
    moves = plan.response_plan.human_reception_plan.moves
    assert len(moves) == follow.count('。') == 3
    original, = (r for r in plan.relations if r.type == 'contrast' and r.source_span_ids == ('s1',))
    revised, = (n for n in plan.nuclei if 'thread_subject:revised_original_reaction' in n.semantic_frame.attribute_codes)
    survivor, = (n for n in plan.nuclei if 'source_received_chain_slot:first' in n.semantic_frame.attribute_codes)
    assert original.to_nucleus_id == survivor.nucleus_id
    assert not any(revised.nucleus_id in (r.from_nucleus_id, r.to_nucleus_id) for r in plan.relations)
    assert not any('source_received_chain_slot:second' in n.semantic_frame.attribute_codes for n in plan.nuclei)
    # Every required text contribution owns a reception target, support or
    # event context. Observation coverage alone cannot satisfy this check.
    covered = {nid for move in moves for nid in (*move.target_nucleus_ids, *move.support_nucleus_ids,
               *reception.final_reception_context_nucleus_ids(move=move, plan=plan))}
    required = {n.nucleus_id for n in plan.nuclei if n.retention == 'required'
                and n.source_fields in {(field,), ('answer_text_private',)}}
    assert required <= covered
    index = {n.nucleus_id: n for n in plan.nuclei}
    line, = (line for line in sentence.lines if line.binding.line_role == 'human_follow')
    parts = [p + '。' for p in follow.removesuffix('。').split('。')]
    with (patch.object(reception, '_source_owned_relational_focus_sentence', side_effect=AssertionError('no author')),
          patch.object(reception, '_source_owned_positive_answer_group_sentence', side_effect=AssertionError('no author')),
          patch.object(reception, '_source_grounded_received_discourse', side_effect=AssertionError('no author')),
          patch.object(reception, '_detached_feeling_finite_surface', side_effect=AssertionError('no author'))):
        for clause, part in zip(line.reception_clause_plans, parts, strict=True):
            move, = (m for m in moves if clause.move_ids == (m.move_id,))
            if len(move.target_nucleus_ids) == 1:
                assert move.target_nucleus_ids == (original.from_nucleus_id,)
                assert move.support_nucleus_ids == (survivor.nucleus_id,)
                proof = gate.read_source_owned_discourse(part, move, plan, resolver, selected)
                assert proof is not None and [source for _, _, source in proof] == [
                    reception.final_reception_source_anchor_text(nid, index, resolver).encode()
                    for nid in (original.from_nucleus_id, survivor.nucleus_id)]
                continue
            if move.reception_act == 'recognize_lived_change':
                source_ids = []
                for nid in move.target_nucleus_ids:
                    about, = (r for r in plan.relations if r.type == 'evaluation_about_event' and r.to_nucleus_id == nid)
                    source_ids.extend((about.from_nucleus_id, nid))
            else:
                source_ids = []
                for nid in move.target_nucleus_ids:
                    # The received reader proves event roles internally;
                    # its returned byte ranges restore feeling predicates.
                    if index[nid].kind == 'reaction':
                        source_ids.append(nid)
                    source_ids.extend(r.to_nucleus_id for r in plan.relations
                                      if r.type == 'contrast' and r.from_nucleus_id == nid)
            proof = gate.read_source_owned_discourse(part, move, plan, resolver, selected)
            assert proof is not None
            assert [source for _, _, source in proof] == [
                reception.final_reception_source_anchor_text(nid, index, resolver).encode() for nid in source_ids]
            assert all(0 <= a < b <= len(part.encode()) for a, b, _ in proof)
        assert read_body(context, result.artifact.text).passed


def test_received_chain_final_revision_rejects_missing_or_relinked_reception():
    from test_cmee_emlis_detached_observation import read_body
    request = begin(RECEIVED_CHAIN_MULTI)
    for text in ('今は嬉しい。', 'その時は楽しかった。', '「嬉しかった」ではなく「少し怖かった」です。'):
        request = advance(request, text)
    context = actual(request=request)
    body, follow = context[0].artifact.text, context[0].artifact.reception
    changes = [
        follow.replace('褒められたのに、悲しかったのですね。', ''),
        follow.replace('褒められたことについて、回答した時点では嬉しいし、', ''),
        follow.replace('し、誘われたことについて、その時は楽しかったのですね。', 'のですね。'),
        follow.replace('誘われたのに、寂しさを感じ、', ''),
        follow.replace('頼まれたのに、怖さを感じ、', ''),
        follow.replace('、言い直してくださった気持ちについては、当時は少し怖かったのですね。', 'たのですね。'),
        follow.replace('褒められたのに、悲しかったのですね。', '褒められたのに、悲しかったけれど、嬉しかったのですね。'),
        follow.replace('言い直してくださった気持ちについては、', '褒められたから、'),
        follow.replace('回答した時点では嬉しい', 'その時は嬉しい'),
        follow.replace('その時は楽しかった', '回答した時点では楽しかった'),
        follow.replace('誘われたことについて、', '頼まれたことについて、'),
        follow.replace('当時は少し怖かった', '当時は少し怖くなかった'),
        follow.replace('誘われたのに、寂しさ', '褒められたのに、寂しさ'),
        follow.replace('頼まれたのに、怖さ', '頼まれたから、怖さ'),
        follow.replace('褒められたのに、悲しかった', '褒められたから、悲しかった'),
        follow.replace('褒められたのに、悲しかった', '誘われたのに、悲しかった'),
        follow.replace('褒められたのに、悲しかった', '褒められたのに、悲しくなかった'),
        follow.replace('当時は少し怖かった', '当時は怖かった'),
    ]
    with (patch.object(reception, '_source_owned_relational_focus_sentence', side_effect=AssertionError('no author')),
          patch.object(reception, '_source_owned_positive_answer_group_sentence', side_effect=AssertionError('no author')),
          patch.object(reception, '_source_grounded_received_discourse', side_effect=AssertionError('no author'))):
        assert read_body(context, body).passed
        for changed in changes:
            assert changed != follow
            assert not read_body(context, body.replace(follow, changed)).passed


@pytest.mark.parametrize('change', ['kind', 'source', 'owner', 'grounding', 'reverse', 'answer_field'])
def test_received_chain_final_revision_keeps_about_outside_original_contrast(change):
    from dataclasses import replace
    import emlis_ai_grounded_observation_plan as plan_owner
    request = begin(RECEIVED_CHAIN_MULTI)
    for text in ('今は嬉しい。', 'その時は楽しかった。', '「嬉しかった」ではなく「少し怖かった」です。'):
        request = advance(request, text)
    result, plan, _, resolver, selected = actual(request=request)
    original, = (r for r in plan.relations if r.type == 'contrast' and r.source_span_ids == ('s1',))
    move, = (m for m in plan.response_plan.human_reception_plan.moves
             if m.target_nucleus_ids == (original.from_nucleus_id,) and m.support_nucleus_ids == (original.to_nucleus_id,))
    about, = (r for r in plan.relations if r.type == 'evaluation_about_event' and r.from_nucleus_id == original.from_nucleus_id)
    body = '褒められたのに、悲しかったのですね。'
    assert body in result.artifact.reception
    assert gate.read_source_owned_discourse(body, move, plan, resolver, selected) is not None
    if change == 'answer_field':
        plan = replace(plan, nuclei=tuple(replace(n, source_fields=('memo',)) if n.nucleus_id == about.to_nucleus_id
                                         else n for n in plan.nuclei))
    else:
        updates = {
            'kind': dict(type='coexistence'),
            'source': dict(from_nucleus_id=original.to_nucleus_id),
            'owner': dict(to_nucleus_id=original.to_nucleus_id),
            'grounding': dict(grounding_kind='explicit'),
            'reverse': dict(from_nucleus_id=about.to_nucleus_id, to_nucleus_id=about.from_nucleus_id),
        }[change]
        plan = replace(plan, relations=tuple(replace(r, **updates) if r == about else r for r in plan.relations))
    assert plan_owner.source_owned_relational_focus(move, plan) is None
    with patch.object(reception, '_source_owned_relational_focus_sentence', side_effect=AssertionError('no author')):
        assert gate.read_source_owned_discourse(body, move, plan, resolver, selected) is None


@pytest.mark.parametrize('replies,replacement,retained', [
    (('今は嬉しい。', 'その時は楽しかった。'), '少し怖かった', ('では嬉しい', 'その時は楽しかった')),
    (('その時は楽しかった。', '今は少し安心です。'), '少し怖かった', ('その時は楽しかった', '時点では少し安心')),
    (('今は安心なのです。', 'その時は幸せだったのです。'), '少し怖かったのです', ('では安心なのだ', 'その時は幸せだったの')),
])
def test_received_chain_final_revision_saved_body_retains_all_sources(qcase, qdb, monkeypatch, replies, replacement, retained):
    from test_emlis_q3_application import cont
    user, parent, service = qcase
    qdb.query('update public.emotions set memo=$1 where id=$2', [RECEIVED_CHAIN_MULTI, parent])
    first = current = run(service.start(user, parent))
    for i, text in enumerate((*replies, '「嬉しかった」ではなく「' + replacement + '」です。')):
        if i:
            current = run(cont(service, user, current, f'final-revision-continue-{i}'))
        current = run(answer(service, user, current, text, f'final-revision-answer-{i}'))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        if i == 2:
            body = current['current_observation']['text']
            follow = body.split('Emlisから：\n', 1)[1]
            assert '嬉しかった' not in body and follow.count('。') == 3
            assert all(s in follow for s in (*retained, '褒められたのに、悲しかった', '誘われたのに、寂し',
                                             '頼まれたのに、怖', '当時は少し怖かった'))
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved revision must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current
        assert qdb.query('select memo from public.emotions where id=$1', [parent])['rows'][0]['memo'] == RECEIVED_CHAIN_MULTI
    assert current['state'] == 'COMPLETED' and not current['can_continue']


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
@pytest.mark.parametrize('replacement,visible', [
    ('少し楽しかったのです', '当時は少し楽しかったのですね'),
    ('私も少し楽しかったのだ', '当時、あなたも少し楽しかったのですね'),
    ('少し楽しかったのだった', '当時は少し楽しかったのでしたね'),
    ('少し楽しくなかったのです', '当時は少し楽しくなかったのですね'),
    ('少し軽かったのです', '当時は少し軽かったのですね'),
    ('少しこわかったのです', '当時は少しこわかったのですね'),
    ('少しさびしかったのです', '当時は少しさびしかったのですね'),
])
def test_finite_explanation_alignment_revision_keeps_every_source(field, replacement, visible):
    replies = ('今は嬉しい。', 'その時は楽しかった。')
    # Reuse the existing source-coverage and author-disabled UTF8 inverse
    # assertions; no expected prose is generated by the author for this test.
    test_received_chain_middle_revision_keeps_every_source_in_reception(
        field, replies, replacement, ('回答した時点では嬉しい', 'その時は楽しかった', visible))
    request = begin(RECEIVED_CHAIN_MULTI if field == 'memo' else '',
                    RECEIVED_CHAIN_MULTI if field == 'memo_action' else '')
    original = prepare_emlis_meaning(request).thread.original
    for text in (*replies, '「悲しかった」ではなく「' + replacement + '」です。'):
        request = advance(request, text)
    prepared = prepare_emlis_meaning(request)
    assert prepared.checkpoint.assessment_status == 'RESOLVED'
    assert prepared.checkpoint.answer_update.updates[0].operation == 'REVISE'
    assert not prepared.checkpoint.unresolved_parts and prepared.thread.original == original


@pytest.mark.parametrize('position', [0, 1])
@pytest.mark.parametrize('ending', ['のです', 'のだ', 'のだった'])
def test_finite_explanation_alignment_group_preserves_clause_and_outer_tense(position, ending):
    from test_cmee_emlis_detached_observation import read_body
    replies = ['今は嬉しい。', 'その時は楽しかった。']
    source = '少し楽しい' if position == 0 else '少し楽しかった'
    replies[position] = ('今は' if position == 0 else 'その時は') + source + ending + '。'
    request = begin(RECEIVED_CHAIN_MULTI)
    for reply in replies:
        request = advance(request, reply)
    context = actual(request=request)
    body, follow = context[0].artifact.text, context[0].artifact.reception
    assert '今回の観測に反映できていない' not in body
    assert all(x in follow for x in ('褒められた', '悲しかった', '嬉しかった', '誘われたのに、寂し', '頼まれたのに、怖'))
    assert '回答した時点では' in follow and 'その時は' in follow
    expected = source + (('のだったし' if ending == 'のだった' else 'のだし') if position == 0
                         else ('のでしたね' if ending == 'のだった' else 'のですね'))
    assert expected in follow
    _, plan, sentence, resolver, selected = context
    group, = (m for m in plan.response_plan.human_reception_plan.moves
              if m.reception_act == 'recognize_lived_change' and len(m.target_nucleus_ids) == 2)
    line, = (line for line in sentence.lines if line.binding.line_role == 'human_follow')
    parts = [p + '。' for p in follow.removesuffix('。').split('。')]
    part, = (part for clause, part in zip(line.reception_clause_plans, parts, strict=True)
             if clause.move_ids == (group.move_id,))
    with (patch.object(reception, '_source_owned_positive_answer_group_sentence', side_effect=AssertionError('no author')),
          patch.object(reception, '_detached_feeling_finite_surface', side_effect=AssertionError('no author'))):
        assert gate.read_source_owned_discourse(part, group, plan, resolver, selected) is not None
    with patch.object(reception, '_source_owned_positive_answer_group_sentence', side_effect=AssertionError('no author')):
        assert read_body(context, body).passed
        replacements = [(source, source.replace('少し', 'とても')),
                        ('回答した時点では', 'その時は'), ('誘われたことについて', '頼まれたことについて')]
        replacements.append(('のだったし', 'のだし') if position == 0 and ending == 'のだった' else
                            ('のだし', 'し') if position == 0 else
                            ('のでしたね', 'のですね') if ending == 'のだった' else ('のですね', 'でしたね'))
        for old, new in replacements:
            changed = follow.replace(old, new, 1)
            assert changed != follow and not read_body(context, body.replace(follow, changed)).passed


@pytest.mark.parametrize('replacement', ['私も少し楽しかったのです', '少し楽しかったのだった'])
def test_finite_explanation_alignment_revision_rejects_semantic_changes(replacement):
    from test_cmee_emlis_detached_observation import read_body
    request = begin(RECEIVED_CHAIN_MULTI)
    for reply in ('今は嬉しい。', 'その時は楽しかった。', '「悲しかった」ではなく「' + replacement + '」です。'):
        request = advance(request, reply)
    context = actual(request=request)
    body, follow = context[0].artifact.text, context[0].artifact.reception
    changes = [follow.replace('少し楽しかった', 'とても楽しかった'),
               follow.replace('少し楽しかった', '少し楽しくなかった'),
               follow.replace('少し楽しかった', '少し楽しい'),
               follow.replace('回答した時点では嬉しい', 'その時は嬉しい'),
               follow.replace('誘われたことについて', '頼まれたことについて'),
               follow.replace('嬉しかったという気持ちを受け止めています。', ''),
               follow.replace('誘われたのに、寂しさを感じたし、', ''),
               follow.replace('頼まれたのに、怖さを感じたし、', ''),
               follow.replace('言い直してくださった気持ちについては、', '褒められたから、')]
    changes.append(follow.replace('あなたも', 'あなたは') if replacement.startswith('私も') else
                   follow.replace('のでしたね', 'のですね'))
    with (patch.object(reception, '_source_owned_positive_answer_group_sentence', side_effect=AssertionError('no author')),
          patch.object(reception, '_source_grounded_received_discourse', side_effect=AssertionError('no author')),
          patch.object(reception, '_detached_feeling_finite_surface', side_effect=AssertionError('no author'))):
        assert read_body(context, body).passed
        for changed in changes:
            assert changed != follow and not read_body(context, body.replace(follow, changed)).passed


@pytest.mark.parametrize('source', ['友人は楽しかったのです', '楽しかったかもしれないのです',
    '楽しかったならのです', '楽しかったのですか', '楽しかったですのです',
    '忙しかったのです', '私も私も楽しかったのです', '楽しかったそうなのです'])
def test_finite_explanation_alignment_keeps_unsupported_correction_boundary(source):
    request = advance(advance(begin(), '今は少し重かった。'),
                      '「少し重かった」ではなく「' + source + '」です。')
    prepared = prepare_emlis_meaning(request)
    assert prepared.checkpoint.assessment_status == 'PARTIAL'
    assert not prepared.accepted_nuclei
    assert prepared.checkpoint.unresolved_parts[0].reason_code == 'correction_replacement_unsupported'


@pytest.mark.parametrize('replacement,visible', [
    ('少し楽しかったのです', '当時は少し楽しかったのですね'),
    ('私も少し楽しかったのだ', '当時、あなたも少し楽しかったのですね'),
    ('少し楽しくなかったのだった', '当時は少し楽しくなかったのでしたね'),
])
def test_finite_explanation_alignment_saved_revision_replays_complete_body(qcase, qdb, monkeypatch, replacement, visible):
    from test_emlis_q3_application import cont
    user, parent, service = qcase
    qdb.query('update public.emotions set memo=$1 where id=$2', [RECEIVED_CHAIN_MULTI, parent])
    first = current = run(service.start(user, parent))
    for index, reply in enumerate(('今は嬉しい。', 'その時は楽しかった。',
                                  '「悲しかった」ではなく「' + replacement + '」です。')):
        if index:
            current = run(cont(service, user, current, f'finite-explanation-continue-{index}'))
        current = run(answer(service, user, current, reply, f'finite-explanation-answer-{index}'))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        if index == 2:
            body = current['current_observation']['text']
            follow = body.split('Emlisから：\n', 1)[1]
            assert '悲しかった' not in body and '今回の観測に反映できていない' not in body
            assert all(x in follow for x in (visible, '回答した時点では嬉しい', 'その時は楽しかった',
                                             '嬉しかった', '誘われたのに、寂し', '頼まれたのに、怖'))
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved explanation must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current
        assert qdb.query('select memo from public.emotions where id=$1', [parent])['rows'][0]['memo'] == RECEIVED_CHAIN_MULTI
    assert current['state'] == 'COMPLETED' and not current['can_continue']


@pytest.mark.parametrize('change', ['move_count', 'other_optional', 'other_act', 'answer_field', 'about_kind', 'about_direction'])
def test_finite_explanation_alignment_single_attention_keeps_source_boundary(change):
    from dataclasses import replace
    import emlis_ai_grounded_observation_plan as plan_owner
    context = actual(request=advance(begin(RECEIVED_CHAIN_MULTI), '今は少し楽しいのだった。'))
    result, plan, _, resolver, selected = context
    moves = plan.response_plan.human_reception_plan.moves
    move, = (m for m in moves if m.reception_act == 'recognize_lived_change')
    assert move.move_role == 'attention'
    roles = plan_owner.source_owned_answer_feeling(move, plan)
    assert roles is not None
    part, = (p + '。' for p in result.artifact.reception.removesuffix('。').split('。')
             if '回答した時点では少し楽しいのでしたね' in p)
    with patch.object(reception, '_source_owned_answer_feeling_sentence', side_effect=AssertionError('no author')):
        assert gate.read_source_owned_discourse(part, move, plan, resolver, selected) is not None
    if change.startswith('other_') or change == 'move_count':
        others = [m for m in moves if m != move]
        altered = tuple(m for m in moves if m != others[0]) if change == 'move_count' else tuple(
            replace(m, **({'required': False} if change == 'other_optional' else
                          {'reception_act': 'hold_without_rush'})) if m == others[0] else m for m in moves)
        plan = replace(plan, response_plan=replace(plan.response_plan,
            human_reception_plan=replace(plan.response_plan.human_reception_plan, moves=altered)))
    elif change == 'answer_field':
        plan = replace(plan, nuclei=tuple(replace(n, source_fields=('memo',)) if n == roles[1] else n
                                          for n in plan.nuclei))
    else:
        about, = (r for r in plan.relations if r.to_nucleus_id == roles[1].nucleus_id)
        updates = {'type': 'contrast'} if change == 'about_kind' else {
            'from_nucleus_id': about.to_nucleus_id, 'to_nucleus_id': about.from_nucleus_id}
        plan = replace(plan, relations=tuple(replace(r, **updates) if r == about else r for r in plan.relations))
    assert plan_owner.source_owned_answer_feeling(move, plan) is None


def test_finite_explanation_alignment_single_survivor_after_withdrawal_replays(qcase, qdb, monkeypatch):
    # The same finite attention route also applies after one answer is
    # withdrawn. Keep the frozen nominal-prose expectation above untouched;
    # exercise all its source-retention and saved-replay checks with the
    # finite sentence's explicit original-occasion scope.
    test_received_chain_positive_group_saved_add_correct_withdraw(
        qcase, qdb, monkeypatch, '「嬉しい」は誤りです。',
        ('その時は楽しかったのですね',), ('では嬉しい', '時点で嬉しい'))


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
@pytest.mark.parametrize('replies,replacement,visible', [
    (('今は嬉しい。', 'その時は楽しかった。'), replacement,
     ('回答した時点では嬉しい', 'その時は楽しかった'))
    for replacement in ('友人は楽しかったのです', '楽しかったかもしれない', '少し忙しかったのです', None)
] + [
    (('その時は楽しかった。', '今は少し安心です。'), '友人は楽しかったのです',
     ('その時は楽しかった', '回答した時点では少し安心')),
    (('今は少し私は少し安心です。', 'その時は私も楽しかった。'), '楽しかったかもしれない',
     ('回答した時点では少しあなたは少し安心', 'その時はあなたも楽しかった')),
    (('今は安心なのです。', 'その時は幸せだったのです。'), '少し忙しかったのです',
     ('回答した時点では安心なのだ', 'その時は幸せだったの')),
])
def test_received_chain_middle_withdrawal_keeps_every_active_source(field, replies, replacement, visible):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    from test_cmee_emlis_detached_observation import read_body
    request = begin(RECEIVED_CHAIN_MULTI if field == 'memo' else '',
                    RECEIVED_CHAIN_MULTI if field == 'memo_action' else '')
    original = prepare_emlis_meaning(request).thread.original
    third = ('「悲しかった」ではなく「' + replacement + '」です。' if replacement else '「悲しかった」は誤りです。')
    for reply in (*replies, third):
        request = advance(request, reply)
    prepared = prepare_emlis_meaning(request)
    assert prepared.thread.original == original
    assert prepared.checkpoint.assessment_status == ('PARTIAL' if replacement else 'RESOLVED')
    assert [u.operation for u in prepared.checkpoint.answer_update.updates] == ['WITHDRAW']
    assert [u.reason_code for u in prepared.checkpoint.unresolved_parts] == (
        ['correction_replacement_unsupported'] if replacement else [])
    context = actual(request=request)
    result, plan, sentence, resolver, selected = context
    public = MeaningExperienceEngine().generate(request)
    assert public.artifact is not None and public.artifact.text == result.artifact.text
    follow = result.artifact.reception
    assert all(s in follow for s in (*visible, '嬉しかった', '誘われたのに、寂し', '頼まれたのに、怖'))
    assert '悲しかった' not in follow and '言い直してくださった' not in follow
    if replacement:
        assert replacement not in follow
        assert '回答の「' + third.rstrip('。') + '」には、今回の観測に反映できていない部分があります。' in result.artifact.observation
    else:
        assert '今回の観測に反映できていない' not in result.artifact.text
    assert len([n for n in plan.nuclei if n.source_fields == ('answer_text_private',)]) == 2
    assert not any('thread_subject:revised_original_reaction' in n.semantic_frame.attribute_codes for n in plan.nuclei)
    assert not any(r.type == 'contrast' and r.source_span_ids == ('s1',) for r in plan.relations)
    survivor, = (n for n in plan.nuclei if 'source_received_chain_slot:second' in n.semantic_frame.attribute_codes)
    assert not any(survivor.nucleus_id in (r.from_nucleus_id, r.to_nucleus_id) for r in plan.relations)
    moves = plan.response_plan.human_reception_plan.moves
    assert len(moves) == follow.count('。') == 3
    covered = {nid for move in moves for nid in (*move.target_nucleus_ids, *move.support_nucleus_ids,
               *reception.final_reception_context_nucleus_ids(move=move, plan=plan))}
    required = {n.nucleus_id for n in plan.nuclei if n.retention == 'required'
                and n.source_fields in {(field,), ('answer_text_private',)}}
    assert required <= covered
    index = {n.nucleus_id: n for n in plan.nuclei}
    line, = (line for line in sentence.lines if line.binding.line_role == 'human_follow')
    parts = [p + '。' for p in follow.removesuffix('。').split('。')]
    with (patch.object(reception, '_source_owned_positive_answer_group_sentence', side_effect=AssertionError('no author')),
          patch.object(reception, '_source_grounded_received_discourse', side_effect=AssertionError('no author')),
          patch.object(reception, '_detached_feeling_finite_surface', side_effect=AssertionError('no author'))):
        for clause, part in zip(line.reception_clause_plans, parts, strict=True):
            move, = (m for m in moves if clause.move_ids == (m.move_id,))
            if move.target_nucleus_ids == (survivor.nucleus_id,):
                continue
            source_ids = []
            for nid in move.target_nucleus_ids:
                if move.reception_act == 'recognize_lived_change':
                    about, = (r for r in plan.relations if r.type == 'evaluation_about_event' and r.to_nucleus_id == nid)
                    source_ids.extend((about.from_nucleus_id, nid))
                else:
                    source_ids.extend(r.to_nucleus_id for r in plan.relations
                                      if r.type == 'contrast' and r.from_nucleus_id == nid)
            proof = gate.read_source_owned_discourse(part, move, plan, resolver, selected)
            assert proof is not None
            assert [source for _, _, source in proof] == [
                reception.final_reception_source_anchor_text(nid, index, resolver).encode() for nid in source_ids]
            assert all(0 <= a < b <= len(part.encode()) for a, b, _ in proof)
        assert read_body(context, result.artifact.text).passed


def test_received_chain_middle_withdrawal_rejects_missing_or_relinked_meaning():
    from test_cmee_emlis_detached_observation import read_body
    request = begin(RECEIVED_CHAIN_MULTI)
    for reply in ('今は私も少し嬉しい。', 'その時は少し楽しかった。',
                  '「悲しかった」ではなく「友人は楽しかったのです」です。'):
        request = advance(request, reply)
    context = actual(request=request)
    body, follow = context[0].artifact.text, context[0].artifact.reception
    changes = [follow.replace('嬉しかったという気持ちを受け止めています。', ''),
               follow.replace('褒められたことについて、回答した時点ではあなたも少し嬉しいし、', ''),
               follow.replace('し、誘われたことについて、その時は少し楽しかったのですね。', 'のですね。'),
               follow.replace('誘われたのに、寂しさを感じ、', ''),
               follow.replace('、頼まれたのに、怖さを感じたのですね', 'たのですね'),
               follow.replace('回答した時点では', 'その時は'),
               follow.replace('誘われたことについて', '頼まれたことについて'),
               follow.replace('あなたも', 'あなたは'),
               follow.replace('少し嬉しい', '嬉しい'),
               follow.replace('少し嬉しい', '少し嬉しくない'),
               follow.replace('少し楽しかった', '少し楽しい'),
               follow.replace('嬉しかったという気持ち', '悲しかったけれど嬉しかったという気持ち'),
               follow.replace('褒められたことについて', '褒められたから'),
               follow + '友人は楽しかったのですね。']
    with (patch.object(reception, '_source_owned_positive_answer_group_sentence', side_effect=AssertionError('no author')),
          patch.object(reception, '_source_grounded_received_discourse', side_effect=AssertionError('no author')),
          patch.object(reception, '_detached_feeling_finite_surface', side_effect=AssertionError('no author'))):
        assert read_body(context, body).passed
        for changed in changes:
            assert changed != follow and not read_body(context, body.replace(follow, changed)).passed


@pytest.mark.parametrize('replacement', ['友人は楽しかったのです', '楽しかったかもしれない', '少し忙しかったのです', None])
def test_received_chain_middle_withdrawal_saved_complete_body(qcase, qdb, monkeypatch, replacement):
    from test_emlis_q3_application import cont
    user, parent, service = qcase
    qdb.query('update public.emotions set memo=$1 where id=$2', [RECEIVED_CHAIN_MULTI, parent])
    first = current = run(service.start(user, parent))
    third = ('「悲しかった」ではなく「' + replacement + '」です。' if replacement else '「悲しかった」は誤りです。')
    for index, reply in enumerate(('今は嬉しい。', 'その時は楽しかった。', third)):
        if index:
            current = run(cont(service, user, current, f'middle-withdrawal-continue-{index}'))
        current = run(answer(service, user, current, reply, f'middle-withdrawal-answer-{index}'))
        expected_state = 'PARTIALLY_REFINED' if index == 2 and replacement else 'REFINED'
        assert current['body_state'] == expected_state and current['original'] == first['original']
        if index == 2:
            body = current['current_observation']['text']
            follow = body.split('Emlisから：\n', 1)[1]
            assert follow.count('。') == 3 and '悲しかった' not in follow
            assert all(s in follow for s in ('回答した時点では嬉しい', 'その時は楽しかった',
                                            '嬉しかった', '誘われたのに、寂し', '頼まれたのに、怖'))
            assert ('今回の観測に反映できていない' in body) == bool(replacement)
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved withdrawal must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current
        assert qdb.query('select memo from public.emotions where id=$1', [parent])['rows'][0]['memo'] == RECEIVED_CHAIN_MULTI
    assert current['state'] == 'COMPLETED' and not current['can_continue']


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
@pytest.mark.parametrize('replacement', [None, '友人は楽しかったのです', '楽しかったかもしれない',
                                       '少し忙しかったのです', '少し怖かった', '少し楽しかったのです'])
def test_original_record_feeling_keeps_its_source_beside_retained_answers(field, replacement):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    from test_cmee_emlis_detached_observation import read_body
    request = begin(RECEIVED_CHAIN_MULTI if field == 'memo' else '',
                    RECEIVED_CHAIN_MULTI if field == 'memo_action' else '')
    original = prepare_emlis_meaning(request).thread.original
    third = ('「悲しかった」ではなく「' + replacement + '」です。' if replacement else '「悲しかった」は誤りです。')
    for reply in ('今は嬉しい。', 'その時は楽しかった。', third):
        request = advance(request, reply)
    context = actual(request=request)
    result, plan, _, resolver, _ = context
    assert prepare_emlis_meaning(request).thread.original == original
    assert MeaningExperienceEngine().generate(request).artifact.text == result.artifact.text
    assert '最初の記録には、「嬉しかった」という当時の気持ちも書かれています。' in result.artifact.observation
    assert '最初の記録にある、嬉しかったという気持ちを受け止めています。' in result.artifact.reception
    assert 'その背景には、「嬉しかった」' not in result.artifact.observation
    assert all(s in result.artifact.reception for s in ('回答した時点では嬉しい', 'その時は楽しかった',
                                                       '誘われたのに、寂し', '頼まれたのに、怖'))
    survivor, = (n for n in plan.nuclei if 'source_received_chain_slot:second' in n.semantic_frame.attribute_codes)
    assert not any(survivor.nucleus_id in (r.from_nucleus_id, r.to_nucleus_id) for r in plan.relations)
    assert not any(c.startswith('thread_subject:') for c in survivor.semantic_frame.attribute_codes)
    assert reception.source_grounded_original_record_feeling(survivor, plan.relations, resolver) == '嬉しかった'
    with patch.object(reception, 'source_grounded_original_record_feeling', side_effect=AssertionError('no author')):
        assert read_body(context, result.artifact.text).passed


@pytest.mark.parametrize('source', ['少し嬉しかった', '私も少し嬉しかった', 'とても楽しかった'])
def test_original_record_feeling_preserves_complete_owner_and_degree(source):
    from test_cmee_emlis_detached_observation import read_body
    request = begin(RECEIVED_CHAIN_MULTI.replace('けれど嬉しかった', 'けれど' + source))
    for reply in ('今は嬉しい。', 'その時は楽しかった。', '「悲しかった」は誤りです。'):
        request = advance(request, reply)
    context = actual(request=request)
    assert f'最初の記録には、「{source}」という当時の気持ちも書かれています。' in context[0].artifact.observation
    assert f'最初の記録にある、{source}という気持ちを受け止めています。' in context[0].artifact.reception
    assert read_body(context, context[0].artifact.text).passed


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
def test_original_record_feeling_inverse_rejects_source_time_and_survivor_changes(field):
    from test_cmee_emlis_detached_observation import read_body
    memo = RECEIVED_CHAIN_MULTI.replace('けれど嬉しかった', 'けれど私も少し嬉しかった')
    request = begin(memo if field == 'memo' else '', memo if field == 'memo_action' else '')
    for reply in ('今は嬉しい。', 'その時は楽しかった。', '「悲しかった」は誤りです。'):
        request = advance(request, reply)
    context = actual(request=request)
    body = context[0].artifact.text
    observed = '最初の記録には、「私も少し嬉しかった」という当時の気持ちも書かれています。'
    received = '最初の記録にある、私も少し嬉しかったという気持ちを受け止めています。'
    alternatives = (
        (observed, ''), (received, ''),
        (observed, observed.replace('最初の記録には、', '回答には、')),
        (observed, observed.replace('最初の記録には、', 'その背景には、')),
        (observed, observed.replace('当時の', '今も続く')),
        (observed, observed.replace('嬉しかった', '嬉しい')),
        (observed, observed + observed),
        (received, received.replace('最初の記録にある、', '')),
        (received, received.replace('最初の記録にある、', '回答した時点の、')),
        (received, received.replace('最初の記録にある、', '褒められたから、')),
        (received, received.replace('私も', '友人も')),
        (received, received.replace('私も', '私は')),
        (received, received.replace('少し', 'とても')),
        (received, received.replace('嬉しかった', '嬉しくなかった')),
        (received, received.replace('嬉しかった', '嬉しい')),
        (received, received.replace('私も少し嬉しかった', '悲しかったけれど私も少し嬉しかった')),
        (received, received.replace('受け止めています', '続いていると思います')),
    )
    with patch.object(reception, 'source_grounded_original_record_feeling', side_effect=AssertionError('no author')):
        assert read_body(context, body).passed
        for old, new in alternatives:
            changed = body.replace(old, new, 1)
            assert changed != body and not read_body(context, changed).passed
            if old == received and new:
                # Even an oracle replaying the altered body must not license
                # its changed provenance, actor, time or feeling proposition.
                with patch.object(gate, 'replay_source_grounded_human_reception_from_plan',
                        return_value=SimpleNamespace(text=changed.split('Emlisから：\n', 1)[1])), patch.object(
                        reception, '_author_source_grounded_reception_clauses', side_effect=AssertionError('no author')):
                    proof = gate.evaluate_grounded_surface_body_inverse(body=changed.encode(),
                        plan=context[1], sentence_plan=context[2], resolver=context[3],
                        selected_subjective_input=context[4])
                assert not proof.passed
                assert any(c.startswith('body_inverse_original_record_reception_scope_mismatch:')
                           for c in proof.failure_codes)


def test_original_record_feeling_scope_requires_original_past_isolated_source():
    from dataclasses import replace
    from test_cmee_emlis_detached_observation import read_body
    request = begin(RECEIVED_CHAIN_MULTI)
    for reply in ('今は嬉しい。', 'その時は楽しかった。', '「悲しかった」は誤りです。'):
        request = advance(request, reply)
    context = actual(request=request)
    result, plan, sentence, resolver, selected = context
    survivor, = (n for n in plan.nuclei if 'source_received_chain_slot:second' in n.semantic_frame.attribute_codes)
    frame = survivor.semantic_frame
    changed_nuclei = [replace(survivor, source_fields=('answer_text_private',)),
                      replace(survivor, source_fields=('memo_action',)),
                      replace(survivor, retention='optional'),
                      replace(survivor, semantic_frame=replace(frame, actor='other')),
                      replace(survivor, semantic_frame=replace(frame, time_scope='current_input')),
                      replace(survivor, semantic_frame=replace(frame, polarity='negative')),
                      replace(survivor, semantic_frame=replace(frame, attribute_codes=tuple(
                          c for c in frame.attribute_codes if c != 'source_received_chain_slot:second'))),
                      replace(survivor, semantic_frame=replace(frame, attribute_codes=(*frame.attribute_codes,
                          'thread_subject:withdrawn_source_event'))),
                      replace(survivor, semantic_frame=replace(frame, attribute_codes=tuple(
                          'source_fragment_scalar_range:0:5' if c.startswith('source_fragment_scalar_range:') else c
                          for c in frame.attribute_codes)))]
    for changed in changed_nuclei:
        changed_plan = replace(plan, nuclei=tuple(changed if n == survivor else n for n in plan.nuclei))
        assert not reception.source_grounded_original_record_feeling(changed, changed_plan.relations, resolver)
        assert not gate._body_inverse_original_record_feeling(changed, changed_plan, resolver)
    about = next(r for r in plan.relations if r.type == 'evaluation_about_event')
    for changed_relations in (tuple(r for r in plan.relations if r != about),
                              (*plan.relations, replace(about, relation_id='test-relinked-original',
                                                       to_nucleus_id=survivor.nucleus_id))):
        changed_plan = replace(plan, relations=changed_relations)
        assert not reception.source_grounded_original_record_feeling(survivor, changed_relations, resolver)
        assert not gate._body_inverse_original_record_feeling(survivor, changed_plan, resolver)


@pytest.mark.parametrize('source', ['嬉しい', '少し私も楽しかったです'])
def test_original_record_feeling_does_not_relabel_other_temporal_realizations(source):
    from test_cmee_emlis_detached_observation import read_body
    request = begin(RECEIVED_CHAIN_MULTI.replace('けれど嬉しかった', 'けれど' + source))
    for reply in ('今は嬉しい。', 'その時は楽しかった。', '「悲しかった」は誤りです。'):
        request = advance(request, reply)
    context = actual(request=request)
    assert '最初の記録に' not in context[0].artifact.text
    assert source in context[0].artifact.reception
    assert read_body(context, context[0].artifact.text).passed


@pytest.mark.parametrize('replacement', [None, '友人は楽しかったのです'])
def test_original_record_feeling_saved_body_replays_with_original_unchanged(qcase, qdb, monkeypatch, replacement):
    from test_emlis_q3_application import cont
    user, parent, service = qcase
    qdb.query('update public.emotions set memo=$1 where id=$2', [RECEIVED_CHAIN_MULTI, parent])
    first = current = run(service.start(user, parent))
    third = ('「悲しかった」ではなく「' + replacement + '」です。' if replacement else '「悲しかった」は誤りです。')
    for index, reply in enumerate(('今は嬉しい。', 'その時は楽しかった。', third)):
        if index:
            current = run(cont(service, user, current, f'original-feeling-continue-{index}'))
        current = run(answer(service, user, current, reply, f'original-feeling-answer-{index}'))
        assert current['original'] == first['original']
        if index == 2:
            assert current['body_state'] == ('PARTIALLY_REFINED' if replacement else 'REFINED')
            body = current['current_observation']['text']
            assert '最初の記録には、「嬉しかった」という当時の気持ちも書かれています。' in body
            assert '最初の記録にある、嬉しかったという気持ちを受け止めています。' in body
            assert ('今回の観測に反映できていない' in body) == bool(replacement)
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved original source must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current
        assert qdb.query('select memo from public.emotions where id=$1', [parent])['rows'][0]['memo'] == RECEIVED_CHAIN_MULTI
    assert current['state'] == 'COMPLETED' and not current['can_continue']


def test_original_record_feeling_reader_requires_raw_source_not_only_markers():
    from dataclasses import replace
    request = begin(RECEIVED_CHAIN_MULTI)
    for reply in ('今は嬉しい。', 'その時は楽しかった。', '「悲しかった」は誤りです。'):
        request = advance(request, reply)
    _, plan, _, resolver, _ = actual(request=request)
    survivor, = (n for n in plan.nuclei if 'source_received_chain_slot:second' in n.semantic_frame.attribute_codes)
    original_resolve = resolver.resolve
    span = original_resolve(survivor.source_span_ids[0])
    assert gate._body_inverse_original_record_feeling(survivor, plan, resolver) == '嬉しかった'
    # Same-length source changes preserve every scalar offset and marker.
    # A conditional event or a denied feeling cannot borrow their old proof.
    for raw in (span.raw_text.replace('のに', 'なら'), span.raw_text.replace('嬉しかった', '悲しかった')):
        assert len(raw) == len(span.raw_text) and raw != span.raw_text
        with patch.object(resolver, 'resolve', side_effect=lambda sid: replace(span, raw_text=raw)
                          if sid == span.span_id else original_resolve(sid)), patch.object(
                          reception, 'source_grounded_original_record_feeling', side_effect=AssertionError('no author')):
            assert not gate._body_inverse_original_record_feeling(survivor, plan, resolver)


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
@pytest.mark.parametrize('old', ['悲しかった', '嬉しかった'])
@pytest.mark.parametrize('source,finite', [
    ('少し怖かった', '当時は少し怖かったのですね'),
    ('少し楽しかったのです', '当時は少し楽しかったのですね'),
    ('少し楽しかった', '当時は少し楽しかったのですね'),
    ('私も少し怖くなかったです', '当時、あなたも少し怖くなかったのですね'),
    ('少し私は怖かった', '当時、あなたは少し怖かったのですね'),
    ('私も少し不安でした', '当時、あなたも少し不安だったのですね'),
    ('少し楽しかったのだった', '当時は少し楽しかったのでしたね'),
    ('少し怖くなかったのだった', '当時は少し怖くなかったのでしたね'),
])
def test_correction_answer_source_preserves_every_mixed_source(field, old, source, finite):
    # The final-chain positive replacements also reproduce a pre-existing
    # four-Move Plan defect (six cases across both fields). Keep the failing
    # delivery witnesses until that separate Plan owner is repaired.
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    from test_cmee_emlis_detached_observation import read_body
    request = begin(RECEIVED_CHAIN_MULTI if field == 'memo' else '',
                    RECEIVED_CHAIN_MULTI if field == 'memo_action' else '')
    original = prepare_emlis_meaning(request).thread.original
    for reply in ('今は嬉しい。', 'その時は楽しかった。', f'「{old}」ではなく「{source}」です。'):
        request = advance(request, reply)
    prepared = prepare_emlis_meaning(request)
    assert prepared.thread.original == original and prepared.checkpoint.assessment_status == 'RESOLVED'
    assert [u.operation for u in prepared.checkpoint.answer_update.updates] == ['REVISE']
    assert not prepared.checkpoint.unresolved_parts
    context = actual(request=request)
    result, plan, sentence, resolver, selected = context
    assert MeaningExperienceEngine().generate(request).artifact.text == result.artifact.text
    assert f'訂正の回答では、当時の気持ちを「{source}」と言い直されています。' in result.artifact.observation
    follow = result.artifact.reception
    assert follow.count('訂正の回答では、') == 1 and '訂正の回答では、' + finite + '。' in follow
    assert old not in result.artifact.text
    assert all(s in follow for s in ('回答した時点では嬉しい', 'その時は楽しかった',
                                     '誘われたのに、寂し', '頼まれたのに、怖'))
    if old == '悲しかった':
        assert '最初の記録にある、嬉しかったという気持ちを受け止めています。' in follow
    else:
        assert '褒められたのに、悲しかった' in follow
    revised, = (n for n in plan.nuclei if 'thread_subject:revised_original_reaction' in n.semantic_frame.attribute_codes)
    assert revised.source_fields == ('answer_text_private',) and revised.semantic_frame.time_scope == 'past'
    assert not any(revised.nucleus_id in (r.from_nucleus_id, r.to_nucleus_id) for r in plan.relations)
    moves = plan.response_plan.human_reception_plan.moves
    assert len(moves) == follow.count('。') == 3
    covered = {nid for m in moves for nid in (*m.target_nucleus_ids, *m.support_nucleus_ids,
               *reception.final_reception_context_nucleus_ids(move=m, plan=plan))}
    assert {n.nucleus_id for n in plan.nuclei if n.retention == 'required'
            and n.source_fields in {(field,), ('answer_text_private',)}} <= covered
    index = {n.nucleus_id: n for n in plan.nuclei}
    line, = (line for line in sentence.lines if line.binding.line_role == 'human_follow')
    parts = [p + '。' for p in follow.removesuffix('。').split('。')]
    with (patch.object(reception, '_source_owned_positive_answer_group_sentence', side_effect=AssertionError('no author')),
          patch.object(reception, '_source_grounded_received_discourse', side_effect=AssertionError('no author')),
          patch.object(reception, '_revised_feeling_discourse_prefix', side_effect=AssertionError('no author')),
          patch.object(reception, '_detached_feeling_finite_surface', side_effect=AssertionError('no author'))):
        for clause, part in zip(line.reception_clause_plans, parts, strict=True):
            move, = (m for m in moves if clause.move_ids == (m.move_id,))
            if len(move.target_nucleus_ids) == 1:
                continue
            source_ids = []
            for nid in move.target_nucleus_ids:
                if move.reception_act == 'recognize_lived_change':
                    about, = (r for r in plan.relations if r.type == 'evaluation_about_event' and r.to_nucleus_id == nid)
                    source_ids.extend((about.from_nucleus_id, nid))
                else:
                    if index[nid].kind == 'reaction':
                        source_ids.append(nid)
                    source_ids.extend(r.to_nucleus_id for r in plan.relations if r.type == 'contrast' and r.from_nucleus_id == nid)
            proof = gate.read_source_owned_discourse(part, move, plan, resolver, selected)
            assert proof is not None and [s for _, _, s in proof] == [
                reception.final_reception_source_anchor_text(nid, index, resolver).encode() for nid in source_ids]
            assert all(0 <= a < b <= len(part.encode()) for a, b, _ in proof)
        assert read_body(context, result.artifact.text).passed


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
@pytest.mark.parametrize('source', ['私も少し怖くなかったです', '少し怖くなかったのだった'])
def test_correction_answer_source_inverse_rejects_matching_replay_with_wrong_meaning(field, source):
    request = begin(RECEIVED_CHAIN_MULTI if field == 'memo' else '',
                    RECEIVED_CHAIN_MULTI if field == 'memo_action' else '')
    for reply in ('今は嬉しい。', 'その時は楽しかった。', f'「悲しかった」ではなく「{source}」です。'):
        request = advance(request, reply)
    result, plan, sentence, resolver, selected = actual(request=request)
    body, follow = result.artifact.text, result.artifact.reception
    observed = f'訂正の回答では、当時の気持ちを「{source}」と言い直されています。'
    changes = [
        body.replace(observed, ''), body.replace(observed, observed + observed),
        body.replace(observed, observed.replace('訂正の回答では、', '最初の記録には、')),
        body.replace(observed, observed.replace('当時の', '今の')),
        body.replace(observed, observed.replace('怖くなかった', '怖かった')),
    ]
    for old, new in [('訂正の回答では、', ''), ('訂正の回答では、', '頼まれたことについて、'),
                     ('訂正の回答では、', '言い直してくださった気持ちについては、'),
                     ('当時、' if source.startswith('私も') else '当時は', '回答した時点では'),
                     ('少し怖くなかった', '怖くなかった'), ('怖くなかった', '怖かった'),
                     ('怖くなかった', '怖くない'), ('誘われたのに、', '誘われたから、'),
                     ('頼まれたのに、', '頼まれたので、'),
                     ('最初の記録にある、嬉しかったという気持ちを受け止めています。', '')]:
        changes.append(body.replace(follow, follow.replace(old, new, 1)))
    if source.startswith('私も'):
        changes += [body.replace(follow, follow.replace('あなたも', owner)) for owner in ('あなたは', '友人も')]
    else:
        changes.append(body.replace(follow, follow.replace('のでしたね', 'のですね')))
    with (patch.object(reception, '_source_grounded_received_discourse', side_effect=AssertionError('no author')),
          patch.object(reception, '_revised_feeling_discourse_prefix', side_effect=AssertionError('no author')),
          patch.object(reception, '_detached_feeling_finite_surface', side_effect=AssertionError('no author')),
          patch.object(reception, '_author_source_grounded_reception_clauses', side_effect=AssertionError('no author'))):
        for candidate in (body, *changes):
            with patch.object(gate, 'replay_source_grounded_human_reception_from_plan',
                              return_value=SimpleNamespace(text=candidate.split('Emlisから：\n', 1)[1])):
                proof = gate.evaluate_grounded_surface_body_inverse(body=candidate.encode(), plan=plan,
                    sentence_plan=sentence, resolver=resolver, selected_subjective_input=selected)
            assert proof.passed == (candidate == body)
    assert all(changed != body for changed in changes)


def test_correction_answer_source_reader_requires_independent_source_proof():
    from dataclasses import replace
    request = begin(RECEIVED_CHAIN_MULTI)
    for reply in ('今は嬉しい。', 'その時は楽しかった。', '「悲しかった」ではなく「少し楽しかった」です。'):
        request = advance(request, reply)
    result, plan, _, resolver, selected = actual(request=request)
    revised, = (n for n in plan.nuclei if 'thread_subject:revised_original_reaction' in n.semantic_frame.attribute_codes)
    move, = (m for m in plan.response_plan.human_reception_plan.moves if revised.nucleus_id in m.target_nucleus_ids)
    part, = (p + '。' for p in result.artifact.reception.removesuffix('。').split('。') if '訂正の回答では、' in p)
    assert gate.read_source_owned_discourse(part, move, plan, resolver, selected) is not None
    frame = revised.semantic_frame
    about = next(r for r in plan.relations if r.type == 'evaluation_about_event')
    changed_plans = [replace(plan, relations=(*plan.relations,
        replace(about, relation_id='invalid-revision-about', to_nucleus_id=revised.nucleus_id)))]
    changed_nuclei = [replace(revised, source_fields=('memo',))]
    for change in [dict(time_scope='present'), dict(polarity='neutral'), dict(actor='other_person'),
                   dict(attribute_codes=tuple(c for c in frame.attribute_codes
                        if c != 'thread_subject:independent_source_replacement'))]:
        changed_nuclei.append(replace(revised, semantic_frame=replace(frame, **change)))
    changed_plans += [replace(plan, nuclei=tuple(changed if n == revised else n for n in plan.nuclei))
                     for changed in changed_nuclei]
    with patch.object(reception, '_source_grounded_received_discourse', side_effect=AssertionError('no author')):
        for changed in changed_plans:
            assert gate.read_source_owned_discourse(part, move, changed, resolver, selected) is None


@pytest.mark.parametrize('source', ['私も少し怖くなかったです', '少し楽しかったのだった'])
def test_correction_answer_source_saved_body_retains_original_and_exact_display(qcase, qdb, monkeypatch, source):
    from test_emlis_q3_application import cont
    user, parent, service = qcase
    qdb.query('update public.emotions set memo=$1 where id=$2', [RECEIVED_CHAIN_MULTI, parent])
    first = current = run(service.start(user, parent))
    for index, reply in enumerate(('今は嬉しい。', 'その時は楽しかった。', f'「悲しかった」ではなく「{source}」です。')):
        if index:
            current = run(cont(service, user, current, f'correction-source-continue-{index}'))
        current = run(answer(service, user, current, reply, f'correction-source-answer-{index}'))
        assert current['original'] == first['original'] and current['body_state'] == 'REFINED'
        if index == 2:
            assert current['current_observation']['text'].count('訂正の回答では、') == 2
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved correction must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current
        assert qdb.query('select memo from public.emotions where id=$1', [parent])['rows'][0]['memo'] == RECEIVED_CHAIN_MULTI
    assert current['state'] == 'COMPLETED' and not current['can_continue']


def test_correction_answer_source_negative_copula_keeps_other_source_duties():
    from test_cmee_emlis_detached_observation import EXACT_RECORD_MEMO, TWO_POSITIVE_PAIRS, read_body
    request = begin(EXACT_RECORD_MEMO)
    for reply in (*TWO_POSITIVE_PAIRS[0], '「悲しかった」ではなく「私も幸せではなかったのです」です。'):
        request = advance(request, reply)
    context = actual(request=request)
    body, follow = context[0].artifact.text, context[0].artifact.reception
    assert '悲しかった' not in body and '悲しさ' not in follow
    assert all(value in follow for value in ('嬉し', '寂し', '回答した時点では嬉しい', 'その時は楽しかった',
        '訂正の回答では、当時、あなたも幸せではなかったのですね'))
    # Same-name events put this correction on its own Observation line;
    # the ambiguous mixed Reception still needs the answer-source switch.
    assert '「私も幸せではなかったのです」と、当時の気持ちを言い直されています。' in context[0].artifact.observation
    assert read_body(context, body).passed
    with patch.object(gate, 'replay_source_grounded_human_reception_from_plan',
                      return_value=SimpleNamespace(text=follow.replace('あなたも', '相手も'))):
        assert not gate.evaluate_grounded_surface_body_inverse(body=body.replace(follow,
            follow.replace('あなたも', '相手も')).encode(), plan=context[1], sentence_plan=context[2],
            resolver=context[3], selected_subjective_input=context[4]).passed


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
@pytest.mark.parametrize('source', ['少し楽しかった', '少し楽しかったのです', '少し楽しかったのだった'])
def test_positive_final_revision_inverse_rejects_matching_replay(field, source):
    request = begin(RECEIVED_CHAIN_MULTI if field == 'memo' else '',
                    RECEIVED_CHAIN_MULTI if field == 'memo_action' else '')
    for reply in ('今は嬉しい。', 'その時は楽しかった。', f'「嬉しかった」ではなく「{source}」です。'):
        request = advance(request, reply)
    result, plan, sentence, resolver, selected = actual(request=request)
    body, follow = result.artifact.text, result.artifact.reception
    revised, = (n for n in plan.nuclei if 'thread_subject:revised_original_reaction' in n.semantic_frame.attribute_codes)
    moves = plan.response_plan.human_reception_plan.moves
    mixed, = (m for m in moves if revised.nucleus_id in m.target_nucleus_ids)
    assert len(moves) == 3 and len(mixed.target_nucleus_ids) == 3
    assert mixed.reception_act == 'stay_with_current_burden'
    assert revised.semantic_frame.polarity == 'positive'
    assert not any(revised.nucleus_id in (r.from_nucleus_id, r.to_nucleus_id) for r in plan.relations)
    correction, = (part + '。' for part in follow.removesuffix('。').split('。') if '訂正の回答では、' in part)
    replacements = [
        (correction, ''), ('訂正の回答では、', ''),
        ('訂正の回答では、', '頼まれたことについて、'),
        ('当時は少し楽しかった', '回答した時点では少し楽しかった'),
        ('当時は少し楽しかった', '当時は楽しかった'),
        ('当時は少し楽しかった', '当時は少し楽しくなかった'),
        ('当時は少し楽しかった', '当時は友人が少し楽しかった'),
        ('当時は少し楽しかった', '当時は少し楽しい'),
        ('褒められたのに、悲しかった', '褒められたから、悲しかった'),
        ('誘われたのに、寂しさを感じ', '誘われたのに、寂しさを感じず'),
        ('頼まれたのに、怖さを感じ', '頼まれたのに、怖さを感じず'),
        ('回答した時点では嬉しい', 'その時は嬉しい'),
        ('その時は楽しかった', '今は楽しかった'),
    ]
    if source.endswith('のだった'):
        replacements.append(('のでしたね', 'のですね'))
    changed = [body.replace(follow, follow.replace(old, new, 1)) for old, new in replacements]
    assert all(candidate != body for candidate in changed)
    with (patch.object(reception, '_source_grounded_received_discourse', side_effect=AssertionError('no author')),
          patch.object(reception, '_revised_feeling_discourse_prefix', side_effect=AssertionError('no author')),
          patch.object(reception, '_detached_feeling_finite_surface', side_effect=AssertionError('no author')),
          patch.object(reception, '_author_source_grounded_reception_clauses', side_effect=AssertionError('no author'))):
        for candidate in (body, *changed):
            with patch.object(gate, 'replay_source_grounded_human_reception_from_plan',
                              return_value=SimpleNamespace(text=candidate.split('Emlisから：\n', 1)[1])):
                proof = gate.evaluate_grounded_surface_body_inverse(body=candidate.encode(), plan=plan,
                    sentence_plan=sentence, resolver=resolver, selected_subjective_input=selected)
            assert proof.passed == (candidate == body)


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
@pytest.mark.parametrize('source', ['少し楽しかった', '少し楽しかったのです', '少し楽しかったのだった'])
def test_positive_final_revision_saved_body_keeps_every_source(qcase, qdb, monkeypatch, field, source):
    from test_emlis_q3_application import cont
    user, parent, service = qcase
    memo, action = (RECEIVED_CHAIN_MULTI, '') if field == 'memo' else ('', RECEIVED_CHAIN_MULTI)
    qdb.query('update public.emotions set memo=$1,memo_action=$2 where id=$3', [memo, action, parent])
    first = current = run(service.start(user, parent))
    replies = ('今は嬉しい。', 'その時は楽しかった。', f'「嬉しかった」ではなく「{source}」です。')
    for index, reply in enumerate(replies):
        if index:
            current = run(cont(service, user, current, f'positive-final-continue-{index}'))
        current = run(answer(service, user, current, reply, f'positive-final-answer-{index}'))
        assert current['original'] == first['original'] and current['body_state'] == 'REFINED'
        if index == 2:
            text = current['current_observation']['text']
            follow = text.split('Emlisから：\n', 1)[1]
            assert follow.count('。') == 3 and follow.count('訂正の回答では、') == 1
            assert all(value in follow for value in ('褒められたのに、悲しかった',
                '誘われたのに、寂しさを感じ', '頼まれたのに、怖さを感じ',
                '回答した時点では嬉しい', 'その時は楽しかった', '当時は少し楽しかった'))
            assert '嬉しかった' not in text
            assert ('のでしたね' in follow) == source.endswith('のだった')
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved correction must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current
        assert qdb.query('select memo,memo_action from public.emotions where id=$1', [parent])['rows'][0] == {
            'memo': memo, 'memo_action': action}
    assert current['state'] == 'COMPLETED' and not current['can_continue']


DETACHED_ANSWER_SOURCE_CASES = (
    (('今は嬉しい。', 'その時は楽しかった。'), '回答した時点', '嬉しい'),
    (('その時は少し楽しかった。', '今は少し安心です。'), 'その時', '少し楽しかった'),
    (('今は少し私は少し安心です。', 'その時は私も楽しかった。'), '回答した時点', '少し私は少し安心です'),
    (('今は安心なのです。', 'その時は幸せだったのです。'), '回答した時点', '安心なのです'),
    (('今は嬉しい。', '「嬉しい」ではなく「少し楽しい」です。'), '先の回答時点', '少し楽しい'),
)


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
@pytest.mark.parametrize('replies,when,source', DETACHED_ANSWER_SOURCE_CASES)
def test_detached_answer_source_report_reads_each_complete_scope(field, replies, when, source):
    request = begin(RECEIVED_CHAIN_MULTI if field == 'memo' else '',
                    RECEIVED_CHAIN_MULTI if field == 'memo_action' else '')
    for reply in (*replies, '「褒められた」は誤りです。'):
        request = advance(request, reply)
    result, plan, sentence, resolver, selected = actual(request=request)
    body, follow = result.artifact.text, result.artifact.reception
    report = f'先の回答には、{when}の気持ちが「{source}」と書かれています。'
    assert result.artifact.observation.endswith(report) and body.count(report) == 1
    assert '褒められた' not in body and follow.count('。') == 3
    assert all(value in body for value in ('悲しかった', '嬉しかった', '誘われた', '寂し', '頼まれた', '怖'))
    detached, = (n for n in plan.nuclei if n.source_fields == ('answer_text_private',)
                 and 'thread_subject:withdrawn_source_event' in n.semantic_frame.attribute_codes)
    assert not any(detached.nucleus_id in (r.from_nucleus_id, r.to_nucleus_id) for r in plan.relations)
    moves = plan.response_plan.human_reception_plan.moves
    grouped = when != '先の回答時点'
    if grouped:
        assert '先の回答にあるとおり、' in follow and '先の回答では、' not in follow
        move, = (m for m in moves if detached.nucleus_id in m.target_nucleus_ids)
        part, = (p + '。' for p in follow.removesuffix('。').split('。')
                 if p.startswith('先の回答にあるとおり、'))
        index = {n.nucleus_id: n for n in plan.nuclei}
        linked = index[move.target_nucleus_ids[1]]
        about, = (r for r in plan.relations if r.type == 'evaluation_about_event'
                  and r.to_nucleus_id == linked.nucleus_id)
        expected = [reception.final_reception_source_anchor_text(nid, index, resolver).encode()
                    for nid in (detached.nucleus_id, about.from_nucleus_id, linked.nucleus_id)]
        with (patch.object(reception, '_source_owned_positive_answer_group_sentence', side_effect=AssertionError('no author')),
              patch.object(reception, '_detached_feeling_finite_surface', side_effect=AssertionError('no author'))):
            proof = gate.read_source_owned_discourse(part, move, plan, resolver, selected)
            assert proof is not None and [v for _, _, v in proof] == expected
            assert all(0 <= a < b <= len(part.encode()) for a, b, _ in proof)
    legacy = body.replace(report, f'また、{when}の気持ちとして、「{source}」が見えます。').replace(
        '先の回答にあるとおり、', '先の回答では、')
    time_change = 'その時' if when != 'その時' else '回答した時点'
    changes = [
        body.replace(report, ''), body.replace(report, report + report),
        body.replace('先の回答には、', ''),
        body.replace('先の回答には、', '頼まれたことについて、'),
        body.replace('先の回答には、', '褒められたことについて、先の回答には、'),
        body.replace('。' + report, '、' + report),
        body.replace(report, report.replace(when, time_change, 1)),
        body.replace(report, report.replace(source, '友人は' + source, 1)),
        body.replace(report, report.replace(source, '怖くなかった', 1)),
    ]
    if '少し' in source:
        changes.append(body.replace(report, report.replace(source, source.replace('少し', '', 1))))
    if grouped:
        changes.extend(body.replace(follow, follow.replace(old, new, 1)) for old, new in (
            ('先の回答にあるとおり、', ''),
            ('先の回答にあるとおり、', '頼まれたことについて、'),
            ('誘われたことについて、', '頼まれたことについて、'),
            ('その時は', '回答した時点では'),
            ('回答した時点では', '先の回答時点では'),
        ))
    assert all(candidate != body for candidate in changes)
    with (patch.object(reception, '_author_source_grounded_reception_clauses', side_effect=AssertionError('no author')),
          patch.object(reception, '_source_owned_positive_answer_group_sentence', side_effect=AssertionError('no author')),
          patch.object(surface, '_render_observation', side_effect=AssertionError('no author'))):
        for candidate in (body, legacy, *changes):
            with patch.object(gate, 'replay_source_grounded_human_reception_from_plan',
                              return_value=SimpleNamespace(text=candidate.split('Emlisから：\n', 1)[1])):
                proof = gate.evaluate_grounded_surface_body_inverse(body=candidate.encode(), plan=plan,
                    sentence_plan=sentence, resolver=resolver, selected_subjective_input=selected)
            assert proof.passed == (candidate in (body, legacy)), proof.failure_codes


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
@pytest.mark.parametrize('replies,when,source', (DETACHED_ANSWER_SOURCE_CASES[0],
    DETACHED_ANSWER_SOURCE_CASES[1], DETACHED_ANSWER_SOURCE_CASES[4]))
def test_detached_answer_source_report_saved_reads_preserve_original(qcase, qdb, monkeypatch, field, replies, when, source):
    from test_emlis_q3_application import cont
    user, parent, service = qcase
    memo, action = (RECEIVED_CHAIN_MULTI, '') if field == 'memo' else ('', RECEIVED_CHAIN_MULTI)
    qdb.query('update public.emotions set memo=$1,memo_action=$2 where id=$3', [memo, action, parent])
    first = current = run(service.start(user, parent))
    for index, reply in enumerate((*replies, '「褒められた」は誤りです。')):
        if index:
            current = run(cont(service, user, current, f'answer-source-continue-{index}'))
        current = run(answer(service, user, current, reply, f'answer-source-answer-{index}'))
        assert current['original'] == first['original'] and current['body_state'] == 'REFINED'
        if index == 2:
            text = current['current_observation']['text']
            assert f'先の回答には、{when}の気持ちが「{source}」と書かれています。' in text
            assert '褒められた' not in text
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved answer must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current
        assert qdb.query('select memo,memo_action from public.emotions where id=$1', [parent])['rows'][0] == {
            'memo': memo, 'memo_action': action}
    assert current['state'] == 'COMPLETED' and not current['can_continue']


@pytest.mark.parametrize('change', ['marker', 'relation', 'time', 'polarity', 'field'])
def test_detached_answer_source_report_requires_independent_source_proof(change):
    from dataclasses import replace
    request = begin(RECEIVED_CHAIN_MULTI)
    for reply in ('今は嬉しい。', 'その時は楽しかった。', '「褒められた」は誤りです。'):
        request = advance(request, reply)
    result, plan, _, resolver, selected = actual(request=request)
    move, = (m for m in plan.response_plan.human_reception_plan.moves
             if m.reception_act == 'recognize_lived_change' and len(m.target_nucleus_ids) == 2)
    first = next(n for n in plan.nuclei if n.nucleus_id == move.target_nucleus_ids[0])
    part, = (p + '。' for p in result.artifact.reception.removesuffix('。').split('。')
             if p.startswith('先の回答にあるとおり、'))
    if change == 'relation':
        about, = (r for r in plan.relations if r.type == 'evaluation_about_event')
        altered = replace(plan, relations=(*plan.relations, replace(about, relation_id='invalid-detached-about',
                                                                   to_nucleus_id=first.nucleus_id)))
    else:
        frame = first.semantic_frame
        if change == 'marker':
            frame = replace(frame, attribute_codes=tuple(c for c in frame.attribute_codes
                                                         if c != 'thread_subject:withdrawn_source_event'))
        elif change == 'time':
            frame = replace(frame, attribute_codes=tuple('thread_time:original_occasion'
                if c == 'thread_time:answer_time' else c for c in frame.attribute_codes), time_scope='past')
        elif change == 'polarity':
            frame = replace(frame, polarity='negative')
        changed = replace(first, semantic_frame=frame, source_fields=('memo',) if change == 'field' else first.source_fields)
        altered = replace(plan, nuclei=tuple(changed if n.nucleus_id == first.nucleus_id else n for n in plan.nuclei))
    with patch.object(reception, '_source_owned_positive_answer_group_sentence', side_effect=AssertionError('no author')):
        assert gate._read_positive_answer_group_discourse(part, move, plan, resolver, selected) is not None
        assert gate._read_positive_answer_group_discourse(part, move, altered, resolver, selected) is None


OTHER_EVENT_WITHDRAWAL_ANSWERS = tuple(row[0] for row in DETACHED_ANSWER_SOURCE_CASES[:4]) + (
    ('今は嬉しい。', '今は嬉しい。'),
)


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
@pytest.mark.parametrize('replies', OTHER_EVENT_WITHDRAWAL_ANSWERS)
def test_received_chain_other_event_withdrawal_retains_each_answer_and_original(field, replies):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    request = begin(RECEIVED_CHAIN_MULTI if field == 'memo' else '',
                    RECEIVED_CHAIN_MULTI if field == 'memo_action' else '')
    for reply in (*replies, '「頼まれた」は誤りです。'):
        request = advance(request, reply)
    result, plan, sentence, resolver, selected = actual(request=request)
    public = MeaningExperienceEngine().generate(request)
    assert public.artifact is not None and public.artifact.text == result.artifact.text
    body, follow = result.artifact.text, result.artifact.reception
    report = '最初の記録からは、当時の「怖かった」という気持ちが読み取れます。'
    assert result.artifact.observation.endswith(report)
    assert '頼まれた' not in body and follow.count('。') == 3
    assert '褒められたのに、悲しかったけれど、嬉しかったのですね。' in follow
    assert '誘われたのに、寂しさを感じたのですね、また、最初の記録にあるとおり、当時は怖かったのですね。' in follow
    moves = plan.response_plan.human_reception_plan.moves
    assert len(moves) == 3
    required = {n.nucleus_id for n in plan.nuclei if n.retention == 'required'
                and set(n.source_fields) & {field, 'answer_text_private'}}
    assert {nid for m in moves for nid in (*m.target_nucleus_ids, *m.support_nucleus_ids)} == required
    group, = (m for m in moves if m.reception_act == 'recognize_lived_change')
    assert len(group.target_nucleus_ids) == 2 and not group.support_nucleus_ids
    detached, = (n for n in plan.nuclei if 'thread_subject:withdrawn_source_event' in n.semantic_frame.attribute_codes)
    assert detached.source_fields == (field,) and detached.kind == 'reaction'
    assert not any(detached.nucleus_id in (r.from_nucleus_id, r.to_nucleus_id) for r in plan.relations)
    mixed, = (m for m in moves if detached.nucleus_id in m.target_nucleus_ids)
    assert len(mixed.target_nucleus_ids) == 2 and len(mixed.support_nucleus_ids) == 1
    line, = (line for line in sentence.lines if line.binding.line_role == 'human_follow')
    parts = [part + '。' for part in follow.removesuffix('。').split('。')]
    part, = (part for clause, part in zip(line.reception_clause_plans, parts, strict=True)
             if clause.move_ids == (group.move_id,))
    index = {n.nucleus_id: n for n in plan.nuclei}
    expected, events = [], []
    for nid in group.target_nucleus_ids:
        about, = (r for r in plan.relations if r.type == 'evaluation_about_event'
                  and r.to_nucleus_id == nid and r.retention == 'required')
        assert about.grounding_kind == 'user_stated_relation'
        events.append(reception.final_reception_source_anchor_text(about.from_nucleus_id, index, resolver))
        expected.extend(reception.final_reception_source_anchor_text(source_id, index, resolver).encode()
                        for source_id in (about.from_nucleus_id, nid))
    assert events == ['褒められた', '誘われた']
    changes = [
        body.replace(part, ''),
        body.replace(report, ''), body.replace(report, report + report),
        body.replace(report, report.replace('最初の記録からは、', '先の回答からは、')),
        body.replace(report, report.replace('最初の記録からは、', '誘われたことについて、')),
        body.replace(report, report.replace('当時', '回答した時点')),
        body.replace(report, report.replace('怖かった', '友人は怖かった')),
        body.replace('最初の記録にあるとおり、当時は', '先の回答にあるとおり、当時は', 1),
        body.replace(part, part.split('し、', 1)[1]),
        body.replace(part, part.replace('褒められたことについて、', '誘われたことについて、', 1)),
        body.replace(part, part.replace('誘われたことについて、', '頼まれたことについて、', 1)),
        body.replace(part, part.replace('回答した時点では', '先の回答時点では', 1)),
        body.replace('また、最初の記録にあるとおり、当時は怖かった', 'また、誘われたことについて、その時は怖かった', 1),
        body.replace('また、最初の記録にあるとおり、当時は怖かった', 'また、頼まれた時は怖かった', 1),
        body.replace('当時は怖かった', '回答した時点では怖かった', 1),
        body.replace('当時は怖かった', '当時は怖くなかった', 1),
        body.replace('悲しかったけれど、嬉しかった', '悲しかったから、嬉しかった', 1),
        body.replace('悲しかったけれど、', '', 1),
        body.replace('誘われたのに、寂しさを感じた', '誘われたのに、安心を感じた', 1),
    ]
    for old, new in (('その時は', '回答した時点では'), ('少し', ''), ('あなた', '友人'),
                     ('嬉しい', '嬉しくない'), ('安心なのだし', '安心だし')):
        if old in part:
            changes.append(body.replace(part, part.replace(old, new, 1)))
    assert all(candidate != body for candidate in changes)
    legacy = body.replace(report, 'その時の気持ちとして、「怖かった」が見えます。').replace(
        '最初の記録にあるとおり、当時は', 'その時は')
    with (patch.object(reception, '_source_owned_positive_answer_group_sentence', side_effect=AssertionError('no author')),
          patch.object(reception, '_source_owned_answer_feeling_sentence', side_effect=AssertionError('no author')),
          patch.object(reception, '_detached_feeling_finite_surface', side_effect=AssertionError('no author')),
          patch.object(reception, '_author_source_grounded_reception_clauses', side_effect=AssertionError('no author')),
          patch.object(surface, '_render_observation', side_effect=AssertionError('no author'))):
        proof = gate.read_source_owned_discourse(part, group, plan, resolver, selected)
        assert proof is not None and len(proof) == 4 and [value for _, _, value in proof] == expected
        assert all(0 <= a < b <= len(part.encode()) for a, b, _ in proof)
        for candidate in (body, legacy, *changes):
            with patch.object(gate, 'replay_source_grounded_human_reception_from_plan',
                              return_value=SimpleNamespace(text=candidate.split('Emlisから：\n', 1)[1])):
                proof = gate.evaluate_grounded_surface_body_inverse(body=candidate.encode(), plan=plan,
                    sentence_plan=sentence, resolver=resolver, selected_subjective_input=selected)
            assert proof.passed == (candidate in (body, legacy)), proof.failure_codes


@pytest.mark.parametrize('field,replies', [
    ('memo', OTHER_EVENT_WITHDRAWAL_ANSWERS[0]), ('memo_action', OTHER_EVENT_WITHDRAWAL_ANSWERS[0]),
    ('memo', OTHER_EVENT_WITHDRAWAL_ANSWERS[1]), ('memo_action', OTHER_EVENT_WITHDRAWAL_ANSWERS[3]),
])
def test_received_chain_other_event_withdrawal_saved_complete_body(qcase, qdb, monkeypatch, field, replies):
    from test_emlis_q3_application import cont
    user, parent, service = qcase
    memo, action = (RECEIVED_CHAIN_MULTI, '') if field == 'memo' else ('', RECEIVED_CHAIN_MULTI)
    qdb.query('update public.emotions set memo=$1,memo_action=$2 where id=$3', [memo, action, parent])
    first = current = run(service.start(user, parent))
    for index, reply in enumerate((*replies, '「頼まれた」は誤りです。')):
        if index:
            current = run(cont(service, user, current, f'other-event-continue-{index}'))
        current = run(answer(service, user, current, reply, f'other-event-answer-{index}'))
        assert current['original'] == first['original'] and current['body_state'] == 'REFINED'
        if index == 2:
            text = current['current_observation']['text']
            follow = text.split('Emlisから：\n', 1)[1]
            assert follow.count('。') == 3 and '頼まれた' not in text
            assert all(value in follow for value in ('褒められたことについて、', '誘われたことについて、',
                '悲しかったけれど、嬉しかった', '寂しさを感じた', '当時は怖かった'))
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved withdrawal must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current
        assert qdb.query('select memo,memo_action from public.emotions where id=$1', [parent])['rows'][0] == {
            'memo': memo, 'memo_action': action}
    assert current['state'] == 'COMPLETED' and not current['can_continue']


def test_two_positive_withdrawal_original_source_frame_keeps_negative_past_without_authors():
    request = begin()
    for reply in ('今は嬉しい。', 'その時は楽しかった。', '「褒められた」は誤りです。'):
        request = advance(request, reply)
    result, plan, sentence, resolver, selected = actual(request=request)
    body, follow = result.artifact.text, result.artifact.reception
    original = '最初の記録にあるとおり、当時は嬉しくなかった'
    assert original in follow and '褒められた' not in body
    replacements = ('当時は嬉しかった', '当時は嬉しくない', '今は嬉しくなかった',
        '回答した時点では嬉しくなかった', '嬉しくなかった',
        '当時は友人は嬉しくなかった', '当時は褒められたことについて、嬉しくなかった')
    changed = [body.replace(original, '最初の記録にあるとおり、' + replacement, 1)
               for replacement in replacements]
    changed.append(body.replace(original + 'のですね、また、', '', 1))
    changed.append(body.replace(original, original.replace('最初の記録', '先の回答'), 1))
    assert all(candidate != body for candidate in changed)
    with (patch.object(reception, '_author_source_grounded_reception_clauses', side_effect=AssertionError('no author')),
          patch.object(surface, '_render_observation', side_effect=AssertionError('no author'))):
        for candidate in (body, *changed):
            with patch.object(gate, 'replay_source_grounded_human_reception_from_plan',
                              return_value=SimpleNamespace(text=candidate.split('Emlisから：\n', 1)[1])):
                proof = gate.evaluate_grounded_surface_body_inverse(body=candidate.encode(), plan=plan,
                    sentence_plan=sentence, resolver=resolver, selected_subjective_input=selected)
            assert proof.passed == (candidate == body), proof.failure_codes


MIXED_WITHDRAWAL_ANSWERS = (
    ('今は私も少し怖くないです。', '回答した時点で、あなたも少し怖くないのですね'),
    ('その時は私も少し怖くなかった。', 'その時、あなたも少し怖くなかったのですね'),
    ('今は少し苦しい。', '回答した時点では少し苦しいのですね'),
    ('その時は少し苦しかった。', 'その時は少し苦しかったのですね'),
    ('今は私は不安です。', '回答した時点で、あなたは不安なのですね'),
    ('その時は私も不安でした。', 'その時、あなたも不安だったのですね'),
    ('今は私も少し怖いのです。', '回答した時点で、あなたも少し怖いのですね'),
    ('その時は少し怖かったのだった。', 'その時は少し怖かったのでしたね'),
    ('その時は私が頼まれたようで、重かった。', 'その時、あなたが頼まれたようで、重かったのですね'),
    ('今は私が頼まれたようで、重かった。', '回答した時点で、あなたが頼まれたようで、重かったのですね'),
)


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
@pytest.mark.parametrize('reply,finite', MIXED_WITHDRAWAL_ANSWERS)
def test_received_chain_mixed_withdrawal_keeps_independent_answer_source(field, reply, finite):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    request = begin(RECEIVED_CHAIN_MULTI if field == 'memo' else '',
                    RECEIVED_CHAIN_MULTI if field == 'memo_action' else '')
    for text in (reply, 'その時は楽しかった。', '「褒められた」は誤りです。'):
        request = advance(request, text)
    result, plan, sentence, resolver, selected = actual(request=request)
    assert MeaningExperienceEngine().generate(request).artifact.text == result.artifact.text
    body, follow = result.artifact.text, result.artifact.reception
    phrase = '先の回答にあるとおり、' + finite
    assert phrase in follow and '褒められた' not in body
    assert all(value in follow for value in ('悲しかったけれど、嬉しかった',
        '誘われたことについて、その時は楽しかった', '誘われたのに、寂しさを感じた',
        '頼まれたのに、怖さを感じた'))
    moves = plan.response_plan.human_reception_plan.moves
    assert len(moves) == follow.count('。') == 3
    required = {n.nucleus_id for n in plan.nuclei if n.retention == 'required'
                and set(n.source_fields) & {field, 'answer_text_private'}}
    assert {nid for m in moves for nid in (*m.target_nucleus_ids, *m.support_nucleus_ids)} == required
    detached, = (n for n in plan.nuclei if n.source_fields == ('answer_text_private',)
                 and 'thread_subject:withdrawn_source_event' in n.semantic_frame.attribute_codes)
    assert not any(detached.nucleus_id in (r.from_nucleus_id, r.to_nucleus_id) for r in plan.relations)
    mixed, = (m for m in moves if detached.nucleus_id in m.target_nucleus_ids)
    positive, = (m for m in moves if m.reception_act == 'recognize_lived_change'
                 and any(n.nucleus_id in m.target_nucleus_ids and n.source_fields == ('answer_text_private',)
                         for n in plan.nuclei))
    assert len(mixed.target_nucleus_ids) == 3 and len(mixed.support_nucleus_ids) == 2
    assert positive.target_nucleus_ids != (detached.nucleus_id,) and len(positive.target_nucleus_ids) == 1
    assert sum(r.type == 'evaluation_about_event' for r in plan.relations) == 1
    part, = (p + '。' for p in follow.removesuffix('。').split('。') if phrase in p)
    source = reception.final_reception_source_anchor_text(detached.nucleus_id,
        {n.nucleus_id: n for n in plan.nuclei}, resolver)
    changes = [body.replace(phrase, ''), body.replace(phrase, phrase + '、また、' + phrase),
        body.replace(phrase, phrase.replace('先の回答', '最初の記録')),
        body.replace(phrase, phrase.replace('先の回答にあるとおり、', '誘われたことについて、')),
        body.replace(phrase, phrase.replace('先の回答にあるとおり、', '褒められたことについて、')),
        body.replace(phrase, phrase.replace('その時', '回答した時点') if 'その時' in phrase
                     else phrase.replace('回答した時点', 'その時')),
        body.replace('悲しかったけれど、嬉しかった', '悲しかったから、嬉しかった', 1),
        body.replace('誘われたのに、寂しさを感じた', '頼まれたのに、寂しさを感じた', 1)]
    for old, new in (('あなた', '友人'), ('あなたも', 'あなたは'), ('少し', ''),
                     ('怖くない', '怖い'), ('怖くなかった', '怖かった'),
                     ('苦しかった', '苦しい'), ('不安だった', '不安だ'),
                     ('のでしたね', 'のですね')):
        if old in phrase:
            changes.append(body.replace(phrase, phrase.replace(old, new, 1)))
    if 'あなたが' in phrase:
        changes.extend(body.replace(phrase, phrase.replace(old, new, 1)) for old, new in (
            ('あなたが', 'あなたは'), ('ようで', 'ので'), ('重かった', '軽かった')))
    assert all(changed != body for changed in changes)
    with (patch.object(reception, '_source_grounded_received_discourse', side_effect=AssertionError('no author')),
          patch.object(reception, '_author_source_grounded_reception_clauses', side_effect=AssertionError('no author')),
          patch.object(surface, '_render_observation', side_effect=AssertionError('no author'))):
        with patch.object(reception, '_detached_feeling_finite_surface', side_effect=AssertionError('no author helper')):
            proof = gate._read_received_discourse_parts(part, mixed, plan, resolver, selected)
        assert proof is not None and any(value == source.encode() for _, _, value in proof)
        assert all(0 <= a < b <= len(part.encode()) for a, b, _ in proof)
        for candidate in (body, *changes):
            with patch.object(gate, 'replay_source_grounded_human_reception_from_plan',
                              return_value=SimpleNamespace(text=candidate.split('Emlisから：\n', 1)[1])):
                proof = gate.evaluate_grounded_surface_body_inverse(body=candidate.encode(), plan=plan,
                    sentence_plan=sentence, resolver=resolver, selected_subjective_input=selected)
            assert proof.passed == (candidate == body), proof.failure_codes


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
@pytest.mark.parametrize('reply,finite', [MIXED_WITHDRAWAL_ANSWERS[0], MIXED_WITHDRAWAL_ANSWERS[7]])
def test_received_chain_mixed_withdrawal_saved_without_regeneration(qcase, qdb, monkeypatch, field, reply, finite):
    from test_emlis_q3_application import cont
    user, parent, service = qcase
    memo, action = (RECEIVED_CHAIN_MULTI, '') if field == 'memo' else ('', RECEIVED_CHAIN_MULTI)
    qdb.query('update public.emotions set memo=$1,memo_action=$2 where id=$3', [memo, action, parent])
    first = current = run(service.start(user, parent))
    for index, text in enumerate((reply, 'その時は楽しかった。', '「褒められた」は誤りです。')):
        if index:
            current = run(cont(service, user, current, f'mixed-withdraw-continue-{index}'))
        current = run(answer(service, user, current, text, f'mixed-withdraw-answer-{index}'))
        assert current['original'] == first['original'] and current['body_state'] == 'REFINED'
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved mixed withdrawal must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current
        assert qdb.query('select memo,memo_action from public.emotions where id=$1', [parent])['rows'][0] == {
            'memo': memo, 'memo_action': action}
    assert current['state'] == 'COMPLETED' and not current['can_continue']
    assert '褒められた' not in current['current_observation']['text']
    assert '先の回答にあるとおり、' + finite in current['current_observation']['text']


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
def test_received_chain_mixed_withdrawal_source_proof_rejects_changed_ownership(field):
    from dataclasses import replace
    from emlis_ai_grounded_observation_plan import GroundedObservationPlanError
    request = begin(RECEIVED_CHAIN_MULTI if field == 'memo' else '',
                    RECEIVED_CHAIN_MULTI if field == 'memo_action' else '')
    for text in ('今は私も少し怖くないです。', 'その時は楽しかった。', '「褒められた」は誤りです。'):
        request = advance(request, text)
    result, plan, sentence, resolver, selected = actual(request=request)
    target, = (n for n in plan.nuclei if n.source_fields == ('answer_text_private',)
               and 'thread_subject:withdrawn_source_event' in n.semantic_frame.attribute_codes)
    move, = (m for m in plan.response_plan.human_reception_plan.moves if target.nucleus_id in m.target_nucleus_ids)
    part, = (p + '。' for p in result.artifact.reception.removesuffix('。').split('。')
             if '先の回答にあるとおり、' in p)
    frame = target.semantic_frame
    changes = [replace(target, source_fields=('memo',)), replace(target, retention='optional'),
        replace(target, semantic_frame=replace(frame, actor='other')),
        replace(target, semantic_frame=replace(frame, polarity='positive')),
        replace(target, semantic_frame=replace(frame, time_scope='past')),
        replace(target, semantic_frame=replace(frame, modality='uncertain')),
        replace(target, semantic_frame=replace(frame, attribute_codes=tuple(c for c in frame.attribute_codes
            if c != 'thread_subject:withdrawn_source_event'))),
        replace(target, semantic_frame=replace(frame, attribute_codes=tuple(
            'thread_time:original_occasion' if c == 'thread_time:answer_time' else c for c in frame.attribute_codes)))]
    altered = [replace(plan, nuclei=tuple(n if n.nucleus_id != target.nucleus_id else changed
               for n in plan.nuclei)) for changed in changes]
    relation = next(r for r in plan.relations if r.type == 'evaluation_about_event')
    altered.append(replace(plan, relations=(*plan.relations, replace(relation,
        relation_id='forged_answer_owner', to_nucleus_id=target.nucleus_id))))
    with patch.object(reception, '_source_grounded_received_discourse', side_effect=AssertionError('no author')):
        assert gate._read_received_discourse_parts(part, move, plan, resolver, selected) is not None
        for changed in altered:
            try:
                proof = gate._read_received_discourse_parts(part, move, changed, resolver, selected)
            except GroundedObservationPlanError:
                proof = None
            assert proof is None


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
@pytest.mark.parametrize('event', ['褒められた', '誘われた'])
@pytest.mark.parametrize('answers', [
    ('今は嬉しい。', 'その時は楽しかった。'),
    ('今は私も少し嬉しいです。', 'その時は私も少し楽しかった。'),
])
def test_same_name_received_chain_retains_initial_answers_and_withdrawal(field, event, answers):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    memo = RECEIVED_CHAIN_MULTI.replace('誘われた', '褒められた').replace('褒められた', event)
    request = begin(memo if field == 'memo' else '', memo if field == 'memo_action' else '')
    chain = f'「{event}」のに「悲しかった」けれど「嬉しかった」とあります。'
    pair = f'「{event}」と「寂しかった」が、異なる向きのまま同時にあります。'
    for step, reply in enumerate((None, *answers, '「頼まれた」は誤りです。')):
        if reply:
            request = advance(request, reply)
        context = actual(request=request)
        result, plan, sentence, resolver, selected = context
        assert MeaningExperienceEngine().generate(request).artifact.text == result.artifact.text
        body, obs, follow = result.artifact.text, result.artifact.observation, result.artifact.reception
        assert chain in obs and pair in obs
        assert '悲しかったけれど、嬉しかった' in follow and '寂しさ' in follow
        assert ('怖さ' in follow) if step < 3 else ('当時は怖かった' in follow)
        assert ('頼まれた' in body) == (step < 3)
        moves = plan.response_plan.human_reception_plan.moves
        required = {n.nucleus_id for n in plan.nuclei if n.retention == 'required'
                    and set(n.source_fields) & {field, 'answer_text_private'}}
        assert required == {nid for m in moves for nid in (*m.target_nucleus_ids, *m.support_nucleus_ids)}
        assert 1 <= len(moves) <= 3
        events = [n for n in plan.nuclei if n.kind == 'event'
                  and reception.final_reception_source_anchor_text(n.nucleus_id,
                      {v.nucleus_id: v for v in plan.nuclei}, resolver) == event]
        assert len(events) == 2 and len({n.source_span_ids for n in events}) == 2
        spans = [resolver.resolve(n.source_span_ids[0]) for n in events]
        assert all(s.source_field == field for s in spans) and spans[0].end_index <= spans[1].start_index
        if step:
            assert '回答した時点' in follow and '嬉しい' in follow and '先に書かれた方では、' in follow
        if step >= 2:
            assert 'その時' in follow and '楽しかった' in follow and '後に書かれた方では、' in follow
            about = [r for r in plan.relations if r.type == 'evaluation_about_event']
            assert len(about) == len({r.from_nucleus_id for r in about}) == len({r.to_nucleus_id for r in about}) == 2
            assert {r.from_nucleus_id for r in about} == {n.nucleus_id for n in events}
        observations = [obs.replace(chain, ''), obs.replace(pair, ''), obs.replace(pair, pair + pair),
            obs.replace(chain, chain.replace('のに', 'ので', 1)),
            obs.replace(chain, chain.replace('けれど', 'ので', 1)),
            obs.replace('「悲しかった」', '「寂しかった」', 1).replace('「寂しかった」が', '「悲しかった」が', 1),
            obs.replace('「寂しかった」', '「寂しくなかった」', 1),
            pair + ' ' + obs.replace(pair, '', 1)]
        if step:
            observations += [obs.replace('嬉しい', '嬉しくない', 1),
                             obs.replace('回答した時点', 'その時', 1)]
        if step >= 2:
            observations.append(obs.replace('楽しかった', '楽しくなかった', 1))
        candidates = [body.replace(obs, changed, 1) for changed in observations]
        if step:
            candidates += [body.replace(follow, follow.replace('先に書かれた方では、', '後に書かれた方では、', 1), 1),
                           body.replace(follow, follow.replace('嬉しい', '嬉しくない', 1), 1)]
        assert all(changed != body for changed in candidates)
        with (patch.object(reception, '_author_source_grounded_reception_clauses', side_effect=AssertionError('no author')),
              patch.object(surface, '_render_observation', side_effect=AssertionError('no author')),
              patch.object(surface, '_render_relation', side_effect=AssertionError('no author'))):
            for changed in (body, *candidates):
                with patch.object(gate, 'replay_source_grounded_human_reception_from_plan',
                                  return_value=SimpleNamespace(text=changed.split('Emlisから：\n', 1)[1])):
                    proof = gate.evaluate_grounded_surface_body_inverse(body=changed.encode(), plan=plan,
                        sentence_plan=sentence, resolver=resolver, selected_subjective_input=selected)
                assert proof.passed == (changed == body), proof.failure_codes


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
@pytest.mark.parametrize('last', ['「頼まれた」は誤りです。', '「嬉しい」ではなく「少し楽しい」です。'])
def test_same_name_received_chain_saved_replay_keeps_original(qcase, qdb, monkeypatch, field, last):
    from test_emlis_q3_application import cont
    user, parent, service = qcase
    source = RECEIVED_CHAIN_MULTI.replace('誘われた', '褒められた')
    memo, action = (source, '') if field == 'memo' else ('', source)
    qdb.query('update public.emotions set memo=$1,memo_action=$2 where id=$3', [memo, action, parent])
    original = current = run(service.start(user, parent))
    with monkeypatch.context() as saved:
        saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved initial must not regenerate'))
        assert run(service.get(user, parent)) == run(service.start(user, parent)) == current
    for step, reply in enumerate(('今は嬉しい。', 'その時は楽しかった。', last)):
        if step:
            current = run(cont(service, user, current, f'same-chain-continue-{step}'))
        current = run(answer(service, user, current, reply, f'same-chain-answer-{step}'))
        assert current['original'] == original['original'] and current['body_state'] == 'REFINED'
        assert qdb.query('select memo,memo_action from public.emotions where id=$1', [parent])['rows'][0] == {
            'memo': memo, 'memo_action': action}
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved update must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current
    assert current['state'] == 'COMPLETED' and not current['can_continue']
    text = current['current_observation']['text']
    assert '悲しかったけれど、嬉しかった' in text and '楽しかった' in text and '寂しさ' in text
    assert ('当時は怖かった' in text and '頼まれた' not in text) if '誤り' in last else (
        '先の回答時点では少し楽しい' in text and '頼まれた' in text)


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
def test_same_name_received_chain_occurrence_source_cannot_be_reassigned(field):
    from dataclasses import replace
    source = RECEIVED_CHAIN_MULTI.replace('誘われた', '褒められた')
    req = begin(source if field == 'memo' else '', source if field == 'memo_action' else '')
    for reply in ('今は嬉しい。', 'その時は楽しかった。'):
        req = advance(req, reply)
    result, plan, _, resolver, selected = actual(request=req)
    move, = [m for m in plan.response_plan.human_reception_plan.moves if len(m.target_nucleus_ids) == 2
             and m.reception_act == 'recognize_lived_change']
    raw = result.artifact.reception.split('。')[0] + '。'
    links = [r for r in plan.relations if r.type == 'evaluation_about_event']
    first, second = links
    event = next(n for n in plan.nuclei if n.nucleus_id == first.from_nucleus_id)
    other = next(n for n in plan.nuclei if n.nucleus_id == second.from_nucleus_id)
    answer_node = next(n for n in plan.nuclei if n.nucleus_id == first.to_nucleus_id)
    altered = [replace(plan, relations=tuple(replace(r, from_nucleus_id=second.from_nucleus_id)
        if r == first else r for r in plan.relations))]
    changes = [replace(event, source_span_ids=other.source_span_ids),
        replace(event, source_fields=('memo_action' if field == 'memo' else 'memo',)),
        replace(event, semantic_frame=replace(event.semantic_frame, attribute_codes=tuple(
            c for c in event.semantic_frame.attribute_codes if not c.startswith('source_received_event_link:')))),
        replace(answer_node, semantic_frame=replace(answer_node.semantic_frame, attribute_codes=tuple(
            c for c in answer_node.semantic_frame.attribute_codes if not c.startswith('thread_subject:distinct_source_occurrence:')))),
        replace(answer_node, semantic_frame=replace(answer_node.semantic_frame, attribute_codes=tuple(
            'thread_time:original_occasion' if c == 'thread_time:answer_time' else c
            for c in answer_node.semantic_frame.attribute_codes)))]
    altered.extend(replace(plan, nuclei=tuple(changed if n.nucleus_id == changed.nucleus_id else n
        for n in plan.nuclei)) for changed in changes)
    with patch.object(reception, '_source_owned_positive_answer_group_sentence', side_effect=AssertionError('no author')):
        assert gate._read_positive_answer_group_discourse(raw, move, plan, resolver, selected) is not None
        for changed in altered:
            assert gate._read_positive_answer_group_discourse(raw, move, changed, resolver, selected) is None


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
@pytest.mark.parametrize('second', ['その時は楽しかった。', 'その時は少し怖かった。'])
def test_same_name_received_chain_unproved_negative_window_cannot_drop_duties(field, second):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    from emlis_ai_grounded_observation_plan import GroundedObservationPlanError
    source = RECEIVED_CHAIN_MULTI.replace('誘われた', '褒められた')
    req = begin(source if field == 'memo' else '', source if field == 'memo_action' else '')
    for reply in ('今は少し苦しい。', second):
        req = advance(req, reply)
    with pytest.raises(GroundedObservationPlanError, match='human_reception_answer_source_capability_gap'):
        build_updated_grounded_plan(prepare_emlis_meaning(req))
    result = MeaningExperienceEngine().generate(req)
    assert result.artifact is None and result.meaning_checkpoint is not None
    assert result.body_state == 'MEANING_UPDATED_BODY_UNAVAILABLE'


SAME_CHAIN_NEGATIVE_ANSWERS = (
    ('今は少し苦しい。', '回答した時点では少し苦しい', '少し苦しくない'),
    ('その時は少し苦しかった。', 'その時は少し苦しかった', '少し苦しくなかった'),
    ('今は私も少し怖くないです。', '回答した時点ではあなたも少し怖くない', 'あなたも少し怖い'),
    ('その時は私も不安でした。', 'その時はあなたも不安だった', 'あなたも不安ではなかった'),
    ('今は私は不安です。', '回答した時点ではあなたは不安', 'あなたは不安ではない'),
    ('今は私も少し怖いのです。', '回答した時点ではあなたも少し怖い', 'あなたも少し怖くない'),
)


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
@pytest.mark.parametrize('first,finite,opposite', SAME_CHAIN_NEGATIVE_ANSWERS)
@pytest.mark.parametrize('second,second_finite', [
    ('その時は楽しかった。', 'その時は楽しかった'),
    ('その時は少し怖かった。', 'その時は少し怖かった'),
])
def test_same_name_received_chain_negative_answers_keep_every_owned_source(field, first, finite, opposite, second, second_finite):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    source = RECEIVED_CHAIN_MULTI.replace('誘われた', '褒められた')
    request = begin(source if field == 'memo' else '', source if field == 'memo_action' else '')
    for reply in (first, second):
        request = advance(request, reply)
    for withdrawn in (False, True):
        if withdrawn:
            request = advance(request, '「頼まれた」は誤りです。')
        result, plan, sentence, resolver, selected = context = actual(request=request)
        body, follow = result.artifact.text, result.artifact.reception
        assert MeaningExperienceEngine().generate(request).artifact.text == body
        first_forms = (finite,) if first.startswith('今は') else (
            '褒められた時は、' + finite.removeprefix('その時は'),
            *(('褒められた時は、少し苦しく',) if first == 'その時は少し苦しかった。' else ()))
        visible_first = next((value for value in first_forms if value in follow), None)
        assert visible_first and second_finite in follow
        assert 'だのですね' not in follow
        assert '悲しかったけれど、嬉しかった' in follow and '寂し' in follow
        assert ('頼まれた' in body) == (not withdrawn)
        assert ('最初の記録からは、当時の「怖かった」' in body) if withdrawn else ('怖さを感じ' in follow)
        if withdrawn:
            assert '最初の記録にあるとおり、当時は怖かった' in follow
        moves = plan.response_plan.human_reception_plan.moves
        required = {n.nucleus_id for n in plan.nuclei if n.retention == 'required'
                    and set(n.source_fields) & {field, 'answer_text_private'}}
        assert required == {nid for move in moves for nid in (*move.target_nucleus_ids, *move.support_nucleus_ids)}
        assert 1 <= len(moves) <= 3
        about = [r for r in plan.relations if r.type == 'evaluation_about_event']
        assert len(about) == len({r.from_nucleus_id for r in about}) == len({r.to_nucleus_id for r in about}) == 2
        nodes = {n.nucleus_id: n for n in plan.nuclei}
        events = [nodes[r.from_nucleus_id] for r in about]
        spans = [resolver.resolve(n.source_span_ids[0]) for n in events]
        assert len({n.source_span_ids for n in events}) == 2 and spans[0].end_index <= spans[1].start_index
        assert all(n.source_fields == (field,) and s.source_field == field for n,s in zip(events,spans))
        for relation in about:
            answer_node = nodes[relation.to_nucleus_id]
            markers = [c for c in answer_node.semantic_frame.attribute_codes
                       if c.startswith('thread_subject:distinct_source_occurrence:')]
            assert len(markers) == 1 and nodes[relation.from_nucleus_id].source_span_ids[0] in markers[0]
        when = '回答した時点では' if first.startswith('今は') else '褒められた時は、'
        changed_time = 'その時は' if first.startswith('今は') else '褒められたことについて、回答した時点では'
        follows = [follow.replace(visible_first, '', 1), follow.replace(second_finite, '', 1),
            follow.replace(visible_first, when + opposite, 1), follow.replace(visible_first, visible_first.replace(when, changed_time), 1),
            follow.replace('先に書かれた', '後に書かれた', 1),
            follow.replace('後に書かれた', '先に書かれた', 1),
            follow.replace('悲しかったけれど、嬉しかった', '嬉しかったけれど、悲しかった', 1),
            follow.replace(second_finite, 'その時は楽しくなかった' if '楽しかった' in second_finite else 'その時は少し怖くなかった', 1)]
        if '少し' in visible_first:
            follows.append(follow.replace(visible_first, visible_first.replace('少し', ''), 1))
        if 'あなたも' in visible_first:
            follows.append(follow.replace(visible_first, visible_first.replace('あなたも', '相手は'), 1))
        if withdrawn:
            follows += [follow.replace('最初の記録にあるとおり、当時は怖かった', value, 1)
                        for value in ('先の回答にあるとおり、当時は怖かった',
                                      '最初の記録にあるとおり、今は怖い',
                                      '最初の記録にあるとおり、当時は怖くなかった',
                                      '褒められた時は怖かった', '頼まれた時は怖かった')]
        assert all(v != follow for v in follows)
        with (patch.object(reception, '_author_source_grounded_reception_clauses', side_effect=AssertionError('no author')),
              patch.object(surface, '_render_observation', side_effect=AssertionError('no author'))):
            if withdrawn:
                legacy = follow.replace('最初の記録にあるとおり、当時は怖かった', 'その時は怖かった', 1)
                with patch.object(gate, 'replay_source_grounded_human_reception_from_plan', return_value=SimpleNamespace(text=legacy)):
                    proof = gate.evaluate_grounded_surface_body_inverse(body=body.replace(follow, legacy).encode(),
                        plan=plan, sentence_plan=sentence, resolver=resolver, selected_subjective_input=selected)
                assert proof.passed, proof.failure_codes
            for candidate in (follow, *follows):
                with patch.object(gate, 'replay_source_grounded_human_reception_from_plan', return_value=SimpleNamespace(text=candidate)):
                    proof = gate.evaluate_grounded_surface_body_inverse(body=body.replace(follow, candidate).encode(),
                        plan=plan, sentence_plan=sentence, resolver=resolver, selected_subjective_input=selected)
                assert proof.passed == (candidate == follow), proof.failure_codes


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
@pytest.mark.parametrize('second', ['その時は楽しかった。', 'その時は少し怖かった。'])
@pytest.mark.parametrize('last', ['「頼まれた」は誤りです。', '「少し苦しい」ではなく「少し怖い」です。'])
def test_same_name_received_chain_negative_saved_correction_withdrawal_and_replay(qcase, qdb, monkeypatch, field, second, last):
    from test_emlis_q3_application import cont
    user, parent, service = qcase
    source = RECEIVED_CHAIN_MULTI.replace('誘われた', '褒められた')
    memo, action = (source, '') if field == 'memo' else ('', source)
    qdb.query('update public.emotions set memo=$1,memo_action=$2 where id=$3', [memo, action, parent])
    original = current = run(service.start(user, parent))
    for step, reply in enumerate(('今は少し苦しい。', second, last)):
        if step:
            current = run(cont(service, user, current, f'negative-chain-continue-{step}'))
        current = run(answer(service, user, current, reply, f'negative-chain-answer-{step}'))
        assert current['body_state'] == 'REFINED' and current['original'] == original['original']
        assert qdb.query('select memo,memo_action from public.emotions where id=$1', [parent])['rows'][0] == {'memo':memo, 'memo_action':action}
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved body must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current
    assert current['state'] == 'COMPLETED' and not current['can_continue']
    body = current['current_observation']['text']
    assert '悲しかったけれど、嬉しかった' in body and '寂し' in body and second[4:-1] in body
    if '誤り' in last:
        assert '頼まれた' not in body and '最初の記録からは、当時の「怖かった」' in body
        assert '最初の記録にあるとおり、当時は怖かった' in body
        assert '回答した時点では少し苦しい' in body
    else:
        assert '先の回答時点では少し怖い' in body and '少し苦しい' not in body and '頼まれた' in body


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
@pytest.mark.parametrize('second', ['その時は楽しかった。', 'その時は少し怖かった。'])
def test_same_name_received_chain_negative_occurrence_requires_original_owner(field, second):
    from dataclasses import replace
    from emlis_ai_grounded_observation_plan import GroundedObservationPlanError
    source = RECEIVED_CHAIN_MULTI.replace('誘われた', '褒められた')
    req = begin(source if field == 'memo' else '', source if field == 'memo_action' else '')
    for reply in ('今は少し苦しい。', second):
        req = advance(req, reply)
    result, plan, sentence, resolver, selected = actual(request=req)
    links = [r for r in plan.relations if r.type == 'evaluation_about_event']
    first, second_link = links
    event = next(n for n in plan.nuclei if n.nucleus_id == first.from_nucleus_id)
    other = next(n for n in plan.nuclei if n.nucleus_id == second_link.from_nucleus_id)
    response = next(n for n in plan.nuclei if n.nucleus_id == first.to_nucleus_id)
    changes = [replace(event, source_span_ids=other.source_span_ids),
        replace(event, source_fields=('memo_action' if field == 'memo' else 'memo',)),
        replace(response, semantic_frame=replace(response.semantic_frame, attribute_codes=tuple(c for c in response.semantic_frame.attribute_codes
            if not c.startswith('thread_subject:distinct_source_occurrence:')))),
        replace(response, semantic_frame=replace(response.semantic_frame, attribute_codes=tuple(
            'thread_time:original_occasion' if c == 'thread_time:answer_time' else c for c in response.semantic_frame.attribute_codes))),
        replace(response, semantic_frame=replace(response.semantic_frame, modality='uncertain'))]
    altered = [replace(plan, nuclei=tuple(changed if n.nucleus_id == changed.nucleus_id else n for n in plan.nuclei)) for changed in changes]
    altered.append(replace(plan, relations=tuple(replace(r, from_nucleus_id=second_link.from_nucleus_id) if r==first else r for r in plan.relations)))
    with (patch.object(reception, '_author_source_grounded_reception_clauses', side_effect=AssertionError('no author')),
          patch.object(surface, '_render_observation', side_effect=AssertionError('no author')),
          patch.object(gate, 'replay_source_grounded_human_reception_from_plan', return_value=SimpleNamespace(text=result.artifact.reception))):
        for changed in altered:
            try:
                proof = gate.evaluate_grounded_surface_body_inverse(body=result.artifact.text.encode(),plan=changed,
                    sentence_plan=sentence,resolver=resolver,selected_subjective_input=selected)
                assert not proof.passed
            except (GroundedObservationPlanError, reception.GroundedHumanReceptionSurfaceError):
                pass


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
@pytest.mark.parametrize('event', ['褒められた', '誘われた'])
@pytest.mark.parametrize('reply,when,value', [
    ('今は嬉しい。', '回答した時点', '嬉しい'),
    ('その時は楽しかった。', 'その時', '楽しかった'),
    ('今は少し苦しい。', '回答した時点', '少し苦しい'),
])
def test_same_name_identical_answer_occurrences_are_visible_and_independently_bound(field, event, reply, when, value):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    source = RECEIVED_CHAIN_MULTI.replace('誘われた', '褒められた').replace('褒められた', event)
    req = begin(source if field == 'memo' else '', source if field == 'memo_action' else '')
    for text in (reply, reply):
        req = advance(req, text)
    for third in (False, True):
        if third:
            req = advance(req, '「頼まれた」は誤りです。')
        context = actual(request=req)
        result, plan, sentence, resolver, selected = context
        assert MeaningExperienceEngine().generate(req).artifact.text == result.artifact.text
        body, obs = result.artifact.text, result.artifact.observation
        first = f'先に書かれた「{event}」ことについて、{when}の受け止めは「{value}」と書かれています。'
        second = first.replace('先に書かれた', '後に書かれた', 1)
        assert obs.count(first) == obs.count(second) == 1
        assert obs.index(first) < obs.index(second)
        assert ('頼まれた' not in body) if third else ('頼まれた' in body)
        assert '悲しかった' in obs and '嬉しかった' in obs and '寂しかった' in obs
        links = [r for r in plan.relations if r.type == 'evaluation_about_event']
        assert len(links) == len({r.from_nucleus_id for r in links}) == len({r.to_nucleus_id for r in links}) == 2
        nodes = {n.nucleus_id: n for n in plan.nuclei}
        assert len({nodes[r.to_nucleus_id].source_span_ids for r in links}) == 2
        for link in links:
            event_node, answer_node = nodes[link.from_nucleus_id], nodes[link.to_nucleus_id]
            assert event_node.source_fields == (field,)
            assert answer_node.source_fields == ('answer_text_private',)
            markers = [c for c in answer_node.semantic_frame.attribute_codes
                       if c.startswith('thread_subject:distinct_source_occurrence:')]
            assert len(markers) == 1
            assert markers[0].startswith('thread_subject:distinct_source_occurrence:' + event_node.source_span_ids[0] + ':')
        moves = plan.response_plan.human_reception_plan.moves
        required = {n.nucleus_id for n in plan.nuclei if n.retention == 'required'}
        assert required == {n for m in moves for n in (*m.target_nucleus_ids, *m.support_nucleus_ids)}
        assert 1 <= len(moves) <= 3
        changed_observations = [
            obs.replace(second, ''),
            obs.replace(second, first),
            obs.replace(second, second + second),
            obs.replace(first, first.removeprefix('先に書かれた')),
            obs.replace('先に書かれた', '間に書かれた', 1),
            obs.replace(first, 'SWAPPED_SOURCE_REPORT').replace(second, first).replace('SWAPPED_SOURCE_REPORT', second),
            obs.replace(first, first.replace(when, 'その時' if when != 'その時' else '回答した時点')),
            obs.replace(second, second.replace(f'「{value}」', '「嬉しくない」')),
            obs.replace(second, second.replace(f'「{event}」', '「頼まれた」')),
        ]
        assert all(changed != obs for changed in changed_observations)
        with (patch.object(reception, '_author_source_grounded_reception_clauses', side_effect=AssertionError('no author')),
              patch.object(surface, '_render_observation', side_effect=AssertionError('no author')),
              patch.object(surface, '_render_relation', side_effect=AssertionError('no author'))):
            for changed in (obs, *changed_observations):
                candidate = body.replace(obs, changed, 1)
                with patch.object(gate, 'replay_source_grounded_human_reception_from_plan',
                                  return_value=SimpleNamespace(text=candidate.split('Emlisから：\n', 1)[1])):
                    proof = gate.evaluate_grounded_surface_body_inverse(body=candidate.encode(), plan=plan,
                        sentence_plan=sentence, resolver=resolver, selected_subjective_input=selected)
                assert proof.passed == (changed == obs), proof.failure_codes


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
@pytest.mark.parametrize('reply', ['今は嬉しい。', '今は少し苦しい。'])
def test_same_name_identical_answers_saved_replay_preserves_both_occurrences(qcase, qdb, monkeypatch, field, reply):
    from test_emlis_q3_application import cont
    user, parent, service = qcase
    source = RECEIVED_CHAIN_MULTI.replace('誘われた', '褒められた')
    memo, action = (source, '') if field == 'memo' else ('', source)
    qdb.query('update public.emotions set memo=$1,memo_action=$2 where id=$3', [memo, action, parent])
    original = current = run(service.start(user, parent))
    for step, text in enumerate((reply, reply, '「頼まれた」は誤りです。')):
        if step:
            current = run(cont(service, user, current, f'identical-continue-{step}'))
        current = run(answer(service, user, current, text, f'identical-answer-{step}'))
        assert current['body_state'] == 'REFINED' and current['original'] == original['original']
        if step >= 1:
            body = current['current_observation']['text']
            assert '先に書かれた「褒められた」ことについて' in body
            assert '後に書かれた「褒められた」ことについて' in body
        assert qdb.query('select memo,memo_action from public.emotions where id=$1', [parent])['rows'][0] == {
            'memo': memo, 'memo_action': action}
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved output must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current
    assert current['state'] == 'COMPLETED' and not current['can_continue']


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
@pytest.mark.parametrize('event', ['褒められた', '誘われた'])
@pytest.mark.parametrize('connector', ['のに', 'けど', 'けれど', 'けれども'])
def test_received_position_annotation_binds_only_its_contrast_event(field, event, connector):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    source = RECEIVED_CHAIN_MULTI.replace('誘われた', '褒められた').replace('褒められた', event)
    source = source.replace('のに寂しかった', connector + '寂しかった')
    req = begin(source if field == 'memo' else '', source if field == 'memo_action' else '')
    label = f'後に書かれた「{event}」ということがあった'
    legacy_label = f'後に書かれた方では、{event}'
    for text in (None, '今は嬉しい。', 'その時は楽しかった。', '「頼まれた」は誤りです。'):
        if text:
            req = advance(req, text)
        context = actual(request=req)
        result, plan, sentence, resolver, selected = context
        follow = result.artifact.reception
        assert MeaningExperienceEngine().generate(req).artifact.text == result.artifact.text
        # Once the following distinct event is withdrawn, the original
        # single-event scope has no ambiguous following event to annotate.
        active_label = legacy_label if text == '「頼まれた」は誤りです。' else label
        assert active_label + connector + '、寂しさを感じ' in follow
        if active_label == label:
            assert legacy_label + connector not in follow
        assert '悲しかったけれど、嬉しかった' in follow
        assert ('頼まれた' not in follow) == (text == '「頼まれた」は誤りです。')
        if text == '「頼まれた」は誤りです。':
            assert '最初の記録にあるとおり、当時は怖かった' in follow
        legacy = follow.replace(label, legacy_label)
        changes = [
            follow.replace(active_label, active_label.replace('後', '先', 1)),
            follow.replace(active_label, active_label.replace('後', '間', 1)),
            follow.replace(active_label, active_label.replace(event, '頼まれた')),
            follow.replace(active_label, active_label + active_label),
            follow.replace(active_label, ''),
            follow.replace(active_label + connector, active_label + 'から'),
            follow.replace('寂しさを感じ', '怖さを感じ'),
        ]
        if active_label == label:
            changes.append(follow.replace(label, label.replace('」ということがあった', '」')))
        assert all(changed != follow for changed in changes)
        with (patch.object(reception, '_author_source_grounded_reception_clauses', side_effect=AssertionError('no author')),
              patch.object(surface, '_render_observation', side_effect=AssertionError('no author'))):
            for candidate in (follow, legacy, *changes):
                # Matching replay cannot hide a wrong written position or
                # donate the event/reaction from the Observation layer.
                with patch.object(gate, 'replay_source_grounded_human_reception_from_plan',
                                  return_value=SimpleNamespace(text=candidate)):
                    proof = gate.evaluate_grounded_surface_body_inverse(
                        body=result.artifact.text.replace(follow, candidate).encode(), plan=plan,
                        sentence_plan=sentence, resolver=resolver, selected_subjective_input=selected)
                assert proof.passed == (candidate in (follow, legacy)), proof.failure_codes


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
@pytest.mark.parametrize('reply', ['今は嬉しい。', '今は少し苦しい。'])
def test_received_position_annotation_saved_correction_and_withdrawal(qcase, qdb, monkeypatch, field, reply):
    from test_emlis_q3_application import cont
    user, parent, service = qcase
    source = RECEIVED_CHAIN_MULTI.replace('誘われた', '褒められた')
    memo, action = (source, '') if field == 'memo' else ('', source)
    qdb.query('update public.emotions set memo=$1,memo_action=$2 where id=$3', [memo, action, parent])
    original = current = run(service.start(user, parent))
    for step, text in enumerate((reply, '「寂しかった」ではなく「少し怖かった」です。', '「頼まれた」は誤りです。')):
        if step:
            current = run(cont(service, user, current, f'position-continue-{step}'))
        current = run(answer(service, user, current, text, f'position-answer-{step}'))
        assert current['body_state'] == 'REFINED' and current['original'] == original['original']
        assert qdb.query('select memo,memo_action from public.emotions where id=$1', [parent])['rows'][0] == {
            'memo': memo, 'memo_action': action}
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved output must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current
    body = current['current_observation']['text']
    assert '少し怖かった' in body and '寂しかった' not in body and '頼まれた' not in body
    assert current['state'] == 'COMPLETED' and not current['can_continue']


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
@pytest.mark.parametrize('source,replies', [
    ('私は褒められたのに悲しかったけれど嬉しかった。私は褒められたのに寂しかった。頼まれたのに怖かった。', (None, '今は嬉しい。')),
    ('誘われたのに嬉しくなかった。誘われたのに悲しかった。誘われたのに寂しかった。', (None, '今は嬉しい。')),
    # A long event keeps the unquoted form after its answer as well.
    ('昔から親しくしている先生に褒められたのに悲しかったけれど嬉しかった。昔から親しくしている先生に褒められたのに寂しかった。頼まれたのに怖かった。', (None, '今は嬉しい。')),
])
def test_received_position_annotation_preserves_other_source_scopes(field, source, replies):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    req = begin(source if field == 'memo' else '', source if field == 'memo_action' else '')
    for reply in replies:
        if reply:
            req = advance(req, reply)
        context = actual(request=req)
        result = context[0]
        assert MeaningExperienceEngine().generate(req).artifact.text == result.artifact.text
        assert '」ということがあった' not in result.artifact.reception
        assert '後に書かれた方では、' in result.artifact.reception
        assert inverse(context, result.artifact.reception, without_author=True).passed
        assert '悲し' in result.artifact.reception and '寂し' in result.artifact.reception


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
def test_received_position_annotation_keeps_literal_answer_words(field):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    source = RECEIVED_CHAIN_MULTI.replace('誘われた', '褒められた')
    req = begin(source if field == 'memo' else '', source if field == 'memo_action' else '')
    req = advance(req, '今は私は先に書かれた方では、重いと思った。')
    context = actual(request=req)
    result = context[0]
    assert MeaningExperienceEngine().generate(req).artifact.text == result.artifact.text
    follow = result.artifact.reception
    assert '回答した時点ではあなたは先に書かれた方では、重いと思った' in follow
    assert '後に書かれた「褒められた」ということがあったのに、寂しさを感じ' in follow
    assert inverse(context, follow, without_author=True).passed


LONG_CHAIN_EVENT = '昔から親しくしている先生に褒められた'


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
@pytest.mark.parametrize('middle,focus', [(LONG_CHAIN_EVENT, '頼まれた'), ('誘われた', '誘われた')])
@pytest.mark.parametrize('reply,time,feeling', [
    ('今は嬉しい。', '回答した時点', '嬉しい'),
    ('今は少し苦しい。', '回答した時点', '少し苦しい'),
    ('その時は楽しかった。', 'その時', '楽しかった'),
    ('その時は少し苦しかった。', 'その時', '少し苦しかった'),
])
def test_reserved_outer_contrast_keeps_later_answer_and_every_original(field, middle, focus, reply, time, feeling):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    from emlis_ai_grounded_human_reception import final_reception_source_anchor_text
    source = f'{LONG_CHAIN_EVENT}のに悲しかったけれど嬉しかった。{middle}のに寂しかった。頼まれたのに怖かった。'
    req = begin(source if field == 'memo' else '', source if field == 'memo_action' else '')
    first = actual(request=req)
    out = MeaningExperienceEngine().generate(req)
    assert out.question and f'「{focus}」' in out.question.prompt_private
    req = advance(req, reply)
    context = actual(request=req)
    result, plan, sentence, resolver, selected = context
    assert MeaningExperienceEngine().generate(req).artifact.text == result.artifact.text
    follow = result.artifact.reception
    assert all(s in follow for s in (LONG_CHAIN_EVENT, middle, '頼まれた',
        '悲しかったけれど、嬉しかった', '寂し', '怖', time, feeling))
    moves = plan.response_plan.human_reception_plan.moves
    assert 1 <= len(moves) <= 3
    assert {n.nucleus_id for n in plan.nuclei if n.retention == 'required'} == {
        nid for m in moves for nid in (*m.target_nucleus_ids, *m.support_nucleus_ids)}
    nodes = {n.nucleus_id: n for n in plan.nuclei}
    about, = (r for r in plan.relations if r.type == 'evaluation_about_event')
    assert final_reception_source_anchor_text(about.from_nucleus_id, nodes, resolver) == focus
    assert nodes[about.to_nucleus_id].source_fields == ('answer_text_private',)
    assert nodes[about.from_nucleus_id].source_fields == (field,)
    assert {r.relation_id for r in first[1].relations if r.retention == 'required'} <= {
        r.relation_id for r in plan.relations if r.retention == 'required'}
    for sid in first[3].span_ids:
        assert resolver.qualified_ref(sid) == first[3].qualified_ref(sid)
    changes = [follow.replace('悲しかったけれど、嬉しかった', '悲しかったから、嬉しかった'),
        follow.replace('寂し', '楽し'), follow.replace(feeling, '平気'),
        follow.replace(time, 'その時' if time == '回答した時点' else '回答した時点'),
        follow.replace(focus, '断られた')]
    assert inverse(context, follow, without_author=True).passed
    assert all(changed != follow for changed in changes)
    for changed in changes:
        assert not inverse(context, changed, without_author=True).passed


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
@pytest.mark.parametrize('reply,old,new', [('今は嬉しい。', '嬉しい', '少し楽しい'),
                                         ('今は少し苦しい。', '少し苦しい', '少し怖い')])
@pytest.mark.parametrize('withdraw', [False, True])
def test_reserved_outer_contrast_saved_answer_correction_or_withdrawal(qcase, qdb, monkeypatch, field, reply, old, new, withdraw):
    from test_emlis_q3_application import cont
    user, parent, service = qcase
    source = f'{LONG_CHAIN_EVENT}のに悲しかったけれど嬉しかった。誘われたのに寂しかった。頼まれたのに怖かった。'
    memo, action = (source, '') if field == 'memo' else ('', source)
    qdb.query('update public.emotions set memo=$1,memo_action=$2 where id=$3', [memo, action, parent])
    first = current = run(service.start(user, parent))
    change = f'「{old}」は誤りです。' if withdraw else f'「{old}」ではなく「{new}」です。'
    for step, text in enumerate((reply, change)):
        if step:
            current = run(cont(service, user, current, 'reserved-continue'))
        current = run(answer(service, user, current, text, f'reserved-answer-{step}'))
        assert current['body_state'] == 'REFINED' and current['original'] == first['original']
        assert qdb.query('select memo,memo_action from public.emotions where id=$1', [parent])['rows'][0] == {
            'memo': memo, 'memo_action': action}
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved body must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current
    follow = current['current_observation']['text'].split('Emlisから：\n', 1)[1]
    assert all(s in follow for s in ('悲しかったけれど、嬉しかった', '誘われた', '寂し', '頼まれた', '怖'))
    assert old not in follow
    assert ('先の回答時点' not in follow) if withdraw else (new in follow and '先の回答時点' in follow)
    assert current['state'] == 'COMPLETED' and not current['can_continue']


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
@pytest.mark.parametrize('reply', ['今は嬉しい。', '今は少し苦しい。'])
def test_reserved_outer_contrast_saved_last_eligible_answer(qcase, qdb, monkeypatch, field, reply):
    user, parent, service = qcase
    source = f'{LONG_CHAIN_EVENT}のに悲しかったけれど嬉しかった。{LONG_CHAIN_EVENT}のに寂しかった。頼まれたのに怖かった。'
    memo, action = (source, '') if field == 'memo' else ('', source)
    qdb.query('update public.emotions set memo=$1,memo_action=$2 where id=$3', [memo, action, parent])
    first = run(service.start(user, parent))
    current = run(answer(service, user, first, reply, 'reserved-last-answer'))
    assert current['body_state'] == 'REFINED' and current['original'] == first['original']
    assert current['state'] == 'COMPLETED' and not current['can_continue']
    with monkeypatch.context() as saved:
        saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved body must not regenerate'))
        assert run(service.get(user, parent)) == run(service.start(user, parent)) == current


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
@pytest.mark.parametrize('withdrawn', ['誘われた', '頼まれた'])
@pytest.mark.parametrize('reply,time,feeling', [
    ('今は嬉しい。', '回答した時点', '嬉しい'),
    ('今は少し苦しい。', '回答した時点', '少し苦しい'),
    ('その時は楽しかった。', 'その時', '楽しかった'),
    ('その時は少し苦しかった。', 'その時', '少し苦しかった'),
])
def test_reserved_outer_contrast_event_withdrawal_keeps_sources(field, withdrawn, reply, time, feeling):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    source = f'{LONG_CHAIN_EVENT}のに悲しかったけれど嬉しかった。誘われたのに寂しかった。頼まれたのに怖かった。'
    req = advance(begin(source if field == 'memo' else '', source if field == 'memo_action' else ''), reply)
    before = actual(request=req)
    req = advance(req, f'「{withdrawn}」は誤りです。')
    context = actual(request=req)
    result, plan, sentence, resolver, selected = context
    body, follow = result.artifact.text, result.artifact.reception
    assert MeaningExperienceEngine().generate(req).artifact.text == body
    assert withdrawn not in body
    assert all(text in body for text in (LONG_CHAIN_EVENT, '悲しかった', '嬉しかった', '寂し', '怖', time, feeling))
    assert '悲しかったけれど、嬉しかった' in follow
    moves = plan.response_plan.human_reception_plan.moves
    assert len(moves) == 3
    required = {n.nucleus_id for n in plan.nuclei if n.retention == 'required'}
    owned = [nid for m in moves for nid in (*m.target_nucleus_ids, *m.support_nucleus_ids)]
    assert set(owned) == required and len(owned) == len(set(owned))
    nodes = {n.nucleus_id: n for n in plan.nuclei}
    answer_node, = (n for n in plan.nuclei if n.source_fields == ('answer_text_private',))
    about = [r for r in plan.relations if r.type == 'evaluation_about_event']
    if withdrawn == '誘われた':
        assert not about
        assert 'thread_subject:withdrawn_source_event' in answer_node.semantic_frame.attribute_codes
    else:
        link, = about
        assert link.to_nucleus_id == answer_node.nucleus_id
        assert reception.final_reception_source_anchor_text(link.from_nucleus_id, nodes, resolver) == '誘われた'
    for detached in (n for n in plan.nuclei
                     if 'thread_subject:withdrawn_source_event' in n.semantic_frame.attribute_codes):
        assert not any(detached.nucleus_id in (r.from_nucleus_id, r.to_nucleus_id) for r in plan.relations)
    for sid in before[3].span_ids:
        assert resolver.qualified_ref(sid) == before[3].qualified_ref(sid)
    surviving_ids = set(nodes)
    assert {r for r in before[1].relations if {r.from_nucleus_id, r.to_nucleus_id} <= surviving_ids} <= set(plan.relations)
    changed_follow = [follow.replace('悲しかったけれど、嬉しかった', '悲しかったから、嬉しかった'),
        follow.replace('寂し', '楽し'), follow.replace(feeling, '平気'),
        follow.replace(time, 'その時' if time == '回答した時点' else '回答した時点'),
        follow + f'{withdrawn}のですね。']
    candidates = [body, *(body.replace(follow, changed) for changed in changed_follow),
        body.replace('「寂しかった」', '「友人が寂しかった」')]
    assert all(candidate != body for candidate in candidates[1:])
    with (patch.object(reception, '_author_source_grounded_reception_clauses', side_effect=AssertionError('no author')),
          patch.object(surface, '_render_observation', side_effect=AssertionError('no author'))):
        for candidate in candidates:
            with patch.object(gate, 'replay_source_grounded_human_reception_from_plan',
                              return_value=SimpleNamespace(text=candidate.split('Emlisから：\n', 1)[1])):
                proof = gate.evaluate_grounded_surface_body_inverse(body=candidate.encode(), plan=plan,
                    sentence_plan=sentence, resolver=resolver, selected_subjective_input=selected)
            assert proof.passed == (candidate == body), proof.failure_codes


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
@pytest.mark.parametrize('withdrawn', ['誘われた', '頼まれた'])
@pytest.mark.parametrize('reply', ['今は嬉しい。', 'その時は少し苦しかった。'])
def test_reserved_outer_contrast_event_withdrawal_saved_without_regeneration(qcase, qdb, monkeypatch, field, withdrawn, reply):
    from test_emlis_q3_application import cont
    user, parent, service = qcase
    source = f'{LONG_CHAIN_EVENT}のに悲しかったけれど嬉しかった。誘われたのに寂しかった。頼まれたのに怖かった。'
    memo, action = (source, '') if field == 'memo' else ('', source)
    qdb.query('update public.emotions set memo=$1,memo_action=$2 where id=$3', [memo, action, parent])
    original = current = run(service.start(user, parent))
    for step, text in enumerate((reply, f'「{withdrawn}」は誤りです。')):
        if step:
            current = run(cont(service, user, current, 'event-withdrawal-continue'))
        current = run(answer(service, user, current, text, f'event-withdrawal-answer-{step}'))
        assert current['body_state'] == 'REFINED' and current['original'] == original['original']
        assert qdb.query('select memo,memo_action from public.emotions where id=$1', [parent])['rows'][0] == {
            'memo': memo, 'memo_action': action}
        with monkeypatch.context() as saved:
            saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved output must not regenerate'))
            assert run(service.get(user, parent)) == run(service.start(user, parent)) == current
    body = current['current_observation']['text']
    assert withdrawn not in body and all(s in body for s in ('悲しかった', '嬉しかった', '寂し', '怖'))


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
@pytest.mark.parametrize('unresolved,sensation', [
    ('今は気持ちが重いと思った。', '重い'),
    ('今は同僚が圧迫されたと思った。', '圧迫'),
    ('今は同僚が痛いと言った。', '痛い'),
    ('今は同僚が息苦しいと言った。', '息苦しい'),
    ('今は「重い」と同僚が言った。', '重い'),
])
def test_unresolved_sensation_disclosure_keeps_partial_answer_without_adopting_quote(field, unresolved, sensation):
    from cocolon_meaning_experience_engine import MeaningExperienceEngine
    from test_cmee_emlis_detached_observation import read_body
    source = f'{LONG_CHAIN_EVENT}のに悲しかったけれど嬉しかった。誘われたのに寂しかった。頼まれたのに怖かった。'
    req = begin(source if field == 'memo' else '', source if field == 'memo_action' else '')
    accepted = '今は少し苦しい。'
    before = actual(request=advance(req, accepted))
    updated = advance(req, accepted + unresolved)
    prepared = prepare_emlis_meaning(updated)
    context = actual(request=updated)
    result, plan, sentence, resolver, selected = context
    output = MeaningExperienceEngine().generate(updated)
    assert output.body_state == 'PARTIALLY_REFINED' and output.question is None
    assert output.artifact.text == result.artifact.text
    assert prepared.checkpoint.assessment_status == 'PARTIAL'
    assert len(prepared.checkpoint.answer_update.updates) == len(prepared.accepted_nuclei) == 1
    assert prepared.checkpoint.unresolved_parts
    assert plan.nuclei == before[1].nuclei
    assert tuple(r for r in plan.relations if r.type != 'evaluation_about_event') == tuple(
        r for r in before[1].relations if r.type != 'evaluation_about_event')
    about, = (r for r in plan.relations if r.type == 'evaluation_about_event')
    prior, = (r for r in before[1].relations if r.type == 'evaluation_about_event')
    # Update identities bind the complete submitted answer. Only the
    # accepted clause supplies this relation's endpoints and evidence.
    assert (about.from_nucleus_id, about.to_nucleus_id, about.source_span_ids) == (
        prior.from_nucleus_id, prior.to_nucleus_id, prior.source_span_ids)
    assert result.artifact.reception == before[0].artifact.reception
    assert sensation not in result.artifact.reception
    disclosure = f'回答の「{unresolved.removesuffix("。")}」には、今回の観測に反映できていない部分があります。'
    assert result.artifact.observation == before[0].artifact.observation + '\n' + disclosure
    body = result.artifact.text
    # The quoted source is evidence only for the disclosure, never a new
    # sensation the author may donate to the user's observation/reception.
    with patch.object(surface, '_render_limited_scope', side_effect=AssertionError('no disclosure author')):
        assert read_body(context, body).passed
        for changed in (body + f'{sensation}のですね。', body.replace(disclosure, disclosure + f'{sensation}のですね。')):
            reasons, _, _ = gate._semantic_subcheck_reasons(plan=plan, sentence_plan=sentence,
                surface_result=SimpleNamespace(text=changed, lines=()), resolver=resolver)
            assert 'ungrounded_sensation_family_added' in reasons
            assert not read_body(context, changed).passed


def test_unresolved_sensation_disclosure_requires_exact_source_and_bound_line():
    from dataclasses import replace
    from test_cmee_emlis_detached_observation import read_body
    source = f'{LONG_CHAIN_EVENT}のに悲しかったけれど嬉しかった。誘われたのに寂しかった。頼まれたのに怖かった。'
    context = actual(request=advance(begin(source), '今は少し苦しい。今は「重い」と同僚が言った。'))
    result, plan, sentence, resolver, selected = context
    body = result.artifact.text
    disclosure = result.artifact.observation.splitlines()[-1]
    mutations = [body.replace('今は「重い」', 'その時は「重い」'),
        body.replace('同僚が言った', '私が言った'),
        body.replace('同僚が言った」', '同僚が言った』'),
        body.replace('には、今回の観測に反映できていない部分があります', 'は、あなたの気持ちです'),
        body.replace(disclosure, disclosure + '\n' + disclosure)]
    limit, = (line for line in sentence.lines if line.binding.claim_scope == 'unresolved_answer_interpretation')
    altered = replace(sentence, lines=tuple(replace(line, binding=replace(line.binding,
        evidence_span_ids=('s1',))) if line == limit else line for line in sentence.lines))
    with patch.object(surface, '_render_limited_scope', side_effect=AssertionError('no disclosure author')):
        for changed, planned in [*( (text, sentence) for text in mutations), (body, altered)]:
            reasons, _, _ = gate._semantic_subcheck_reasons(plan=plan, sentence_plan=planned,
                surface_result=SimpleNamespace(text=changed, lines=()), resolver=resolver)
            assert 'ungrounded_sensation_family_added' in reasons
            assert not read_body((result, plan, planned, resolver, selected), changed).passed
        assert not read_body(context, body.replace(disclosure + '\n', '')).passed


@pytest.mark.parametrize('field', ['memo', 'memo_action'])
@pytest.mark.parametrize('unresolved', ['今は気持ちが重いと思った。', '今は「重い」と同僚が言った。'])
def test_unresolved_sensation_disclosure_saved_partial_answer(qcase, qdb, monkeypatch, field, unresolved):
    user, parent, service = qcase
    source = f'{LONG_CHAIN_EVENT}のに悲しかったけれど嬉しかった。誘われたのに寂しかった。頼まれたのに怖かった。'
    memo, action = (source, '') if field == 'memo' else ('', source)
    qdb.query('update public.emotions set memo=$1,memo_action=$2 where id=$3', [memo, action, parent])
    original = run(service.start(user, parent))
    current = run(answer(service, user, original, '今は少し苦しい。' + unresolved, 'partial-sensation-answer'))
    assert current['body_state'] == 'PARTIALLY_REFINED' and current['original'] == original['original']
    assert current['state'] == 'COMPLETED' and not current['can_continue']
    body = current['current_observation']['text']
    observation, follow = body.split('Emlisから：\n', 1)
    assert unresolved.removesuffix('。') in observation and '反映できていない部分があります' in observation
    assert '回答した時点では少し苦しい' in follow and '重い' not in follow
    assert all(s in follow for s in (LONG_CHAIN_EVENT, '悲しかったけれど、嬉しかった', '誘われた', '寂し', '頼まれた', '怖'))
    assert qdb.query('select memo,memo_action from public.emotions where id=$1', [parent])['rows'][0] == {
        'memo': memo, 'memo_action': action}
    with monkeypatch.context() as saved:
        saved.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved partial body must not regenerate'))
        assert run(service.get(user, parent)) == run(service.start(user, parent)) == current
