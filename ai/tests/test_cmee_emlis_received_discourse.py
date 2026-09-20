"""Source-owned relational responses, not expected-body/template equality.

Only public Q1/Q3 grammar inputs are used. Old snapshots stay unchanged.
"""
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
def test_incomplete_temporal_clause_grammar_keeps_the_existing_path(text):
    context = actual(request=answered(text, initial()))
    follow = context[0].artifact.reception
    assert 'ですのですね' not in follow and 'だのですね' not in follow
    assert '回答した時点では' not in follow
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
def test_positive_answer_is_a_time_bound_finite_feeling(memo, text, time, source):
    context = actual(request=answered(text, initial(memo)))
    result, plan, _, resolver, selected = context
    follow = result.artifact.reception
    event = memo.split('のに')[0]
    assert event + 'ことについて、' + time + source in follow
    assert 'という気持ち' not in follow and '受け止めています' not in follow
    assert len(plan.response_plan.human_reception_plan.moves) == 2
    assert inverse(context, follow, without_author=True).passed
    # The original reaction is an independent duty, including when the
    # added answer names a different feeling about the original occasion.
    original = actual(request=initial(memo))[0].artifact.reception
    assert original in follow
    assert not inverse(context, follow.replace(original, ''), without_author=True).passed


@pytest.mark.parametrize('old,new', [
    ('回答した時点では', 'その時は'), ('回答した時点では', '先の回答時点では'),
    ('回答した時点では', ''), ('回答した時点では', 'そのため回答した時点では'),
    ('回答した時点では', '回答した時点では友人は'),
    ('ことについて、', 'ことのおかげで、'),
    ('少し嬉しい', '嬉しい'), ('少し嬉しい', '少し嬉しかった'),
    ('少し嬉しい', '少し嬉しくない'), ('少し嬉しい', '「少し嬉しい」'),
    ('褒められたことについて', '誘われたことについて'),
])
def test_positive_finite_answer_mutations_are_rejected_without_author(old, new):
    context = actual(request=answered('今は少し嬉しい。', initial()))
    follow = context[0].artifact.reception
    changed = follow.replace(old, new)
    assert changed != follow
    assert not inverse(context, changed, without_author=True).passed


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


def test_unsupported_positive_replacement_and_event_withdrawal_stays_unavailable():
    from emlis_ai_grounded_observation_plan import GroundedObservationPlanError
    request = advance(begin('褒められたのに、嬉しくなかった。誘われたのに、悲しかった。'), '今は嬉しい。')
    request = advance(request, '「嬉しい」ではなく「楽しい」です。「誘われた」は誤りです。')
    with pytest.raises(GroundedObservationPlanError, match='human_reception_withdrawal_capability_gap'):
        build_updated_grounded_plan(prepare_emlis_meaning(request))


@pytest.mark.parametrize('text', ['今は嬉しいです。', '今は私は嬉しい。', '今は僕は嬉しい。'])
def test_positive_finite_answer_keeps_unproven_clause_grammar_on_old_path(text):
    context = actual(request=answered(text, initial()))
    follow = context[0].artifact.reception
    assert '回答した時点では' not in follow
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
