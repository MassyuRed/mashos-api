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
    explicit = '褒められたことについて、回答した時点では嬉しい'
    assert explicit in follow
    assert not inverse(context, follow.replace('褒められたことについて、', ''), without_author=True).passed


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
    assert len(moves) == (2 if MULTI_POSITIVE in sequence else 1)
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
