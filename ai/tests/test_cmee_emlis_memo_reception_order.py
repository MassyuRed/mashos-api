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

# A received contrast, a separate feeling and its later correction use the
# same source-owned selection; the action's rhetorical role must not split it.
from test_cmee_emlis_q3_thread import begin, advance, NOMINAL_BACKGROUND_JOY

RECEIVED = ('誘われたのに、悲しかった。', '頼まれたのに、寂しかった。')
APPRAISAL = '準備を忘れた自分が情けない'


@pytest.mark.parametrize('pairs', [1, 2])
@pytest.mark.parametrize('answered', [False, True])
@pytest.mark.parametrize('action', ['机を拭いた', '今日は三分だけ音読した'])
def test_retained_feelings_stay_together_initially_and_after_answer(pairs, answered, action):
    req = begin(''.join(RECEIVED[:pairs]) + NOMINAL_BACKGROUND_JOY + '。', action + '。')
    original = req.current_input_bundle
    if answered:
        req = advance(req, 'その時は重かった。')
    out = MeaningExperienceEngine().generate(req)
    assert out.artifact is not None, out.reason_codes
    follow = out.artifact.reception
    assert follow.index('誘われた') < follow.index(NOMINAL_BACKGROUND_JOY) < follow.index(action)
    if pairs == 2:
        assert follow.index('頼まれた') < follow.index(NOMINAL_BACKGROUND_JOY)
    if answered:
        assert '重く' in follow or '重かった' in follow
    else:
        direct = MeaningExperienceEngine().generate(replace(req, emlis_thread=None))
        assert direct.artifact is not None, direct.reason_codes
        assert direct.artifact.reception == follow
    assert req.current_input_bundle == original


@pytest.mark.parametrize('pairs', [1, 2])
@pytest.mark.parametrize('replacement,visible', [('不安です', 'その時の不安'), ('嬉しいです', 'その時の嬉しさ')])
def test_independent_correction_is_received_before_action_without_restoring_old_feeling(pairs, replacement, visible):
    req = begin(''.join(RECEIVED[:pairs]) + APPRAISAL + '。', ACTION + '。')
    original = req.current_input_bundle
    req = advance(req, f'「{APPRAISAL}」ではなく「{replacement}」。')
    out = MeaningExperienceEngine().generate(req)
    assert out.artifact is not None, out.reason_codes
    follow = out.artifact.reception
    assert follow.index('誘われた') < follow.index(visible) < follow.index(ACTION)
    assert APPRAISAL not in follow and req.current_input_bundle == original


@pytest.mark.parametrize('replacement,visible', [('不安です', 'その時の不安'), ('嬉しいです', 'その時の嬉しさ')])
def test_independent_feeling_withdrawal_preserves_original_contrast_and_action(replacement, visible):
    req = begin(''.join(RECEIVED) + APPRAISAL + '。', ACTION + '。')
    original = req.current_input_bundle
    req = advance(req, f'「{APPRAISAL}」ではなく「{replacement}」。')
    # Withdrawal removes the correction, not the untouched original contrast.
    req = advance(req, f'「{replacement}」は誤りです。')
    out = MeaningExperienceEngine().generate(req)
    assert out.artifact is not None, out.reason_codes
    assert out.artifact.reception.index('誘われた') < out.artifact.reception.index(ACTION)
    assert APPRAISAL not in out.artifact.reception and visible not in out.artifact.reception
    assert req.current_input_bundle == original


@pytest.mark.parametrize('corrected', [False, True])
@pytest.mark.parametrize('mutation', ['action_first', 'split_feelings', 'omit_feeling', 'omit_action', 'actor', 'time', 'negation'])
def test_retained_reaction_body_inverse_checks_order_and_meaning_without_author(corrected, mutation):
    req = begin(''.join(RECEIVED) + (APPRAISAL if corrected else NOMINAL_BACKGROUND_JOY) + '。', ACTION + '。')
    if corrected:
        req = advance(req, f'「{APPRAISAL}」ではなく「不安です」。')
    ctx = actual(request=req)
    follow = ctx[0].artifact.reception
    assert inverse(ctx, follow, without_author=True).passed
    parts = [p + '。' for p in follow.split('。') if p]
    assert len(parts) == 3
    if mutation == 'action_first':
        changed = parts[2] + parts[0] + parts[1]
    elif mutation == 'split_feelings':
        changed = parts[0] + parts[2] + parts[1]
    elif mutation == 'omit_feeling':
        changed = parts[0] + parts[2]
    elif mutation == 'omit_action':
        changed = parts[0] + parts[1]
    elif mutation == 'actor':
        changed = follow.replace('誘われた', '友人が誘われた')
    elif mutation == 'time':
        changed = follow.replace('その時の不安', '今の不安') if corrected else follow.replace('嬉しかった', '嬉しい')
    else:
        changed = follow.replace('その時の不安', 'その時の安心') if corrected else follow.replace('嬉しかった', '嬉しくなかった')
    assert changed != follow
    assert not inverse(ctx, changed, without_author=True).passed


@lru_cache(maxsize=1)
def retained_reaction_surface_artifacts():
    import test_cmee_final_stage1_generic_move_projection as helpers
    row = {'case_id': 'public-retained-reaction-order', 'input': {
        'thought_text': ''.join(RECEIVED) + NOMINAL_BACKGROUND_JOY + '。',
        'action_text': ACTION + '。', 'categories': ['仕事'],
        'emotions': [{'type': '不安', 'strength': 'medium'}]}}
    return helpers._full_surface_artifacts(row)


@pytest.mark.parametrize('recovery', ['full', 'optional_removed'])
def test_supported_recovery_keeps_all_reactions_before_action_with_complete_meaning(recovery):
    import emlis_ai_grounded_sentence_surface as surface
    import emlis_ai_grounded_observation_gate as gate
    import test_cmee_final_stage1_generic_move_projection as helpers
    a = retained_reaction_surface_artifacts()
    assert a.gate.passed and a.inverse.passed
    # Existing collective grammar deliberately offers these two stages only;
    # the others would require an ambiguous single-owner pronoun candidate.
    assert {row.recovery_stage for row in a.authored} == {'full', 'optional_removed'}
    sp = a.sentence_plan if recovery == 'full' else surface.build_reception_recovery_sentence_plan(
        a.sentence_plan, a.plan, a.resolver, recovery_stage=recovery)
    body = helpers._recovery_surface(a, sp).text
    follow = body.split('Emlisから：', 1)[1]
    assert follow.index('誘われた') < follow.index(NOMINAL_BACKGROUND_JOY) < follow.index(ACTION)
    assert gate.evaluate_grounded_surface_body_inverse(body=body.encode(), plan=a.plan,
        sentence_plan=sp, resolver=a.resolver, selected_subjective_input=a.selected_subjective_input).passed


@pytest.mark.parametrize('mutation', ['actor', 'field', 'future', 'action_relation', 'optional'])
def test_action_postposition_requires_existing_independent_source_proof(mutation):
    plan = build_updated_grounded_plan(prepare_emlis_meaning(begin(
        ''.join(RECEIVED) + NOMINAL_BACKGROUND_JOY + '。', ACTION + '。')))
    groups = owner._thread_retained_reaction_groups(plan.nuclei, plan.relations)
    assert groups and any(g[0] == 'concrete_effort' for g in groups)
    target_id = next(g[1][0] for g in groups if g[0] == 'concrete_effort')
    target = next(n for n in plan.nuclei if n.nucleus_id == target_id)
    if mutation == 'action_relation':
        relation = next(r for r in plan.relations if r.retention == 'required')
        relations = (*plan.relations, replace(relation, relation_id='synthetic-action-context', from_nucleus_id=target_id))
        nuclei = plan.nuclei
    else:
        kwargs = {'retention': 'optional'} if mutation == 'optional' else {'source_fields': ('memo',)} if mutation == 'field' else {
            'semantic_frame': replace(target.semantic_frame, **({'actor': 'other'} if mutation == 'actor' else {'time_scope': 'future'}))}
        nuclei = tuple(replace(n, **kwargs) if n.nucleus_id == target_id else n for n in plan.nuclei)
        relations = plan.relations
    assert not owner._thread_retained_reaction_groups(nuclei, relations)


# A separate received contrast is not required to receive an explicit feeling
# before an unrelated performed act. Existing source witnesses own both duties.
from test_cmee_emlis_q3_thread import NOMINAL_COGNITION_FEELING

SINGLE_FEELING_MEMOS = (
    NOMINAL_COGNITION_FEELING,
    '片付けが終わった。背伸びをしなくても、少しずつ取り組めると思えたことが嬉しい',
)


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
@pytest.mark.parametrize('source', SINGLE_FEELING_MEMOS)
def test_single_source_feeling_precedes_action_without_changing_selected_meaning(tier, source):
    req = application(source + '。', ACTION + '。', tier=tier)
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    hr = plan.response_plan.human_reception_plan
    with patch.object(owner, '_source_owned_memo_duties_before_action', return_value=False):
        before = build_updated_grounded_plan(prepared)
    assert plan.nuclei == before.nuclei and plan.relations == before.relations
    assert plan.coverage_requirements == before.coverage_requirements
    assert hr.moves == before.response_plan.human_reception_plan.moves
    assert tuple(m.reception_act for m in reception_active_moves(hr, 'full')) == (
        'recognize_lived_change', 'honor_concrete_effort')
    for current in (req, replace(req, emlis_thread=None)):
        out = MeaningExperienceEngine().generate(current)
        assert out.artifact is not None, out.reason_codes
        assert out.artifact.reception.index(source.split('。')[-1]) < out.artifact.reception.index(ACTION)
        if current.emlis_thread is not None:
            assert out.question is None and not out.automatic_progression


@pytest.mark.parametrize('mutation', ['feeling_actor', 'field', 'witness', 'action_actor',
    'action_retention', 'action_span', 'action_grounding', 'action_time', 'action_relation',
    'optional', 'role', 'unsupported_support'])
def test_single_feeling_order_requires_complete_source_ownership(mutation):
    plan = build_updated_grounded_plan(prepare_emlis_meaning(begin(
        NOMINAL_COGNITION_FEELING + '。', ACTION + '。')))
    moves, nuclei, relations = plan.response_plan.human_reception_plan.moves, plan.nuclei, plan.relations
    assert owner._source_owned_memo_duties_before_action(moves, nuclei, relations)
    feeling = next(m for m in moves if m.reception_act == 'recognize_lived_change')
    action = next(m for m in moves if m.reception_act == 'honor_concrete_effort')
    if mutation == 'action_relation':
        relations = tuple(replace(r, retention='required', grounding_kind='user_stated_relation')
                          for r in relations)
    elif mutation in {'optional', 'role', 'unsupported_support'}:
        changes = {'required': False} if mutation == 'optional' else {'move_role': 'significance'} if mutation == 'role' else {
            'support_nucleus_ids': action.target_nucleus_ids}
        moves = tuple(replace(m, **changes) if m == feeling else m for m in moves)
    else:
        target_id = (action if mutation.startswith('action_') else feeling).target_nucleus_ids[0]
        def changed(n):
            if n.nucleus_id != target_id: return n
            if mutation == 'field': return replace(n, source_fields=('answer_text_private',))
            if mutation == 'action_retention': return replace(n, retention='optional')
            if mutation == 'action_span': return replace(n, source_span_ids=())
            if mutation == 'action_grounding': return replace(n, grounding_kind='bounded_structural_inference')
            frame = replace(n.semantic_frame, attribute_codes=tuple(c for c in n.semantic_frame.attribute_codes
                if c != 'lexical:source_bounded_expression')) if mutation == 'witness' else replace(
                    n.semantic_frame, **({'time_scope': 'future'} if mutation == 'action_time' else {'actor': 'other'}))
            return replace(n, semantic_frame=frame)
        nuclei = tuple(changed(n) for n in nuclei)
    assert not owner._source_owned_memo_duties_before_action(moves, nuclei, relations)


@lru_cache(maxsize=1)
def single_feeling_context():
    return actual(request=begin(NOMINAL_COGNITION_FEELING + '。', ACTION + '。'))


@pytest.mark.parametrize('mutation', ['action_first', 'omit_feeling', 'omit_action',
    'actor', 'time', 'negation', 'cause'])
def test_single_feeling_inverse_preserves_order_and_complete_meaning_without_author(mutation):
    ctx = single_feeling_context()
    text = ctx[0].artifact.reception
    assert inverse(ctx, text, without_author=True).passed
    parts = [x + '。' for x in text.split('。') if x]
    assert len(parts) == 2 and NOMINAL_COGNITION_FEELING in parts[0]
    if mutation == 'action_first': changed = parts[1] + parts[0]
    elif mutation == 'omit_feeling': changed = parts[1]
    elif mutation == 'omit_action': changed = parts[0]
    else:
        old, new = {'actor': (NOMINAL_COGNITION_FEELING, '友人は' + NOMINAL_COGNITION_FEELING),
                    'time': ('うれしい', 'うれしかった'),
                    'negation': ('急がなくても', '急いだから'),
                    'cause': ('という気持ちを', 'ので、机を拭いたという気持ちを')}[mutation]
        changed = text.replace(old, new)
    assert changed != text and not inverse(ctx, changed, without_author=True).passed


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
def test_saved_single_feeling_order_survives_get_and_no_author_restart(qdb, qcase, monkeypatch, tier):
    user, parent, service = qcase
    qdb.query('update public.profiles set subscription_tier=$2 where id=$1', [user, tier])
    qdb.query('update public.emotions set memo=$1,memo_action=$2 where id=$3',
              [NOMINAL_COGNITION_FEELING + '。', ACTION + '。', parent])
    dto = run(service.start(user, parent))
    assert dto['current_observation'] is not None
    text = dto['current_observation']['text'].split('Emlisから：', 1)[1]
    assert text.index(NOMINAL_COGNITION_FEELING) < text.index(ACTION)
    assert dto['pending_question'] is None and dto['body_state'] == 'FINAL'
    assert run(service.get(user, parent)) == dto
    monkeypatch.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved content rerendered'))
    assert run(service.start(user, parent)) == dto
    assert run(service.get(user, parent)) == dto


# The existing source relation names the experience behind a feeling.
# Keep its duties while making that experience the focus of the response.
@pytest.mark.parametrize('feeling', FEELINGS)
@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
def test_experience_focus_preserves_background_feeling_and_independent_action(feeling, tier):
    req = request(feeling, tier)
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    current_focus = owner.source_owned_relational_focus
    def old_focus(*args, **kwargs):
        value = current_focus(*args, **kwargs)
        return None if value is not None and value[0] == 'received_experience_focus' else value
    with patch.object(owner, 'source_owned_relational_focus', side_effect=old_focus):
        before = build_updated_grounded_plan(prepared)
    assert plan == before  # No semantic selection, Move or reference-mode drift.
    out = MeaningExperienceEngine().generate(req)
    assert out.artifact is not None, out.reason_codes
    follow = out.artifact.reception
    experience = feeling.removeprefix('それでも').removesuffix('ことにほっとした')
    assert BACKGROUND + 'けれど、それでもほっとしたのは、' + experience + 'ことなのですね。' in follow
    assert follow.index(BURDEN) < follow.index(BACKGROUND) < follow.index(ACTION)
    assert 'ほっとしたという気持ちを受け止めています' not in follow
    assert req.emlis_thread.question_control_context.question_limit == (3 if tier == 'premium' else 1)
    assert out.question is None


@pytest.mark.parametrize('old,new', [
    (BACKGROUND, ''), ('けれど、それでも', 'ので、そのため'),
    ('説明を聞いてもらえた', '提案を聞いてもらえた'),
    ('聞いてもらえた', '聞いてもらえる'), ('聞いてもらえた', '聞いてもらえなかった'),
    ('話が終わった後', '話が終わる前'), ('ほっとしたのは', 'ほっとしているのは'),
    ('ほっとしたのは', '安心したのは'), ('それでもほっとした', '友人がほっとした'),
])
def test_experience_focus_inverse_rejects_changed_source_roles_without_author(old, new):
    ctx = context(); follow = ctx[0].artifact.reception
    assert inverse(ctx, follow, without_author=True).passed
    changed = follow.replace(old, new)
    assert changed != follow
    assert not inverse(ctx, changed, without_author=True).passed


@pytest.mark.parametrize('ending', ['なのです。', 'なのだと受け取りました。'])
def test_experience_focus_acknowledgement_is_not_bound_to_author_spelling(ending):
    ctx = context(); follow = ctx[0].artifact.reception
    changed = follow.replace('ことなのですね。', 'こと' + ending)
    assert changed != follow and inverse(ctx, changed).passed


def test_experience_focus_keeps_degree_and_connective_punctuation():
    feeling = 'それでも、話が終わった後、説明を聞いてもらえたことに少しほっとした'
    ctx = actual(request=request(feeling)); follow = ctx[0].artifact.reception
    assert 'それでも、少しほっとしたのは、話が終わった後、説明を聞いてもらえたことなのですね。' in follow
    assert '、、' not in follow and inverse(ctx, follow, without_author=True).passed
    assert not inverse(ctx, follow.replace('少しほっとした', 'ほっとした'), without_author=True).passed


@pytest.mark.parametrize('source', [
    'それでも説明を聞いてもらえたことでほっとした',
    'それでも私は説明を聞いてもらえたことにほっとした',
    'それでも安心だとは思わないけれど、説明を聞いてもらえたことにほっとした',
])
def test_experience_focus_boundary_does_not_change_source_grammar(source):
    parts = owner._source_nominal_past_feeling_parts(source)
    assert parts is not None and owner._source_nominal_past_feeling_is_bound(source)
    experience, particle, degree, feeling = parts
    assert experience + 'こと' + particle + degree + feeling == source
    # Synthetic raw body cannot gain the new discourse authority at a
    # source/plan boundary; the existing grammar remains independently used.
    ctx = context(); move = next(m for m in ctx[1].response_plan.human_reception_plan.moves
                                if m.reception_act == 'recognize_lived_change')
    import emlis_ai_grounded_observation_gate as inverse_owner
    fabricated = BACKGROUND + 'けれど、ほっとしたのは、' + experience + 'ことなのですね。'
    assert inverse_owner.read_source_owned_discourse(fabricated, move, ctx[1], ctx[3], ctx[4]) is None


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
def test_experience_focus_saved_body_and_restart_are_identical(qcase, qdb, tier, monkeypatch):
    user, parent, service = qcase
    qdb.query('update public.profiles set subscription_tier=$1 where id=$2', [tier, user])
    qdb.query('update public.emotions set memo=$1, memo_action=$2 where id=$3', [memo(), ACTION+'。', parent])
    dto = run(service.start(user, parent))
    assert dto['current_observation'] is not None, dto['failure_code']
    assert 'ほっとしたのは、話が終わった後、説明を聞いてもらえたことなのですね。' in dto['current_observation']['text']
    monkeypatch.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved read rerendered'))
    assert run(service.get(user, parent)) == dto
    assert run(service.start(user, parent)) == dto
