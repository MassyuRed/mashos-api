"""Source-owned SELF continuation, complete u332 replay, and live body checks."""
from dataclasses import replace
import json
from pathlib import Path
import pytest
from cocolon_meaning_experience_engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning, build_updated_grounded_plan
from cocolon_meaning_experience_engine.emlis_thread_projection import project_thread_meaning
from test_cmee_emlis_relief_cognition import BASE, LEFT, RIGHT, UPDATES, encoded, digest, facets
from test_cmee_emlis_source_scope_regressions import request
from test_cmee_emlis_received_discourse import actual, inverse
from test_cmee_emlis_q1_thread import initial
from test_cmee_emlis_q3_thread import begin, advance

BASELINE = json.loads((Path(__file__).parent / 'fixtures' / 'cmee_emlis_u332_self_continuation_v1.json').read_text())
IMPROVED = {'self_watashi', 'self_hiragana', 'self_boku', 'self_ore', 'self_jibun', 'self_ga',
            'relief_degree', 'lonely_slight', 'past_possible', 'with_unknown', 'with_question'}


@pytest.mark.parametrize('row', BASELINE['cases'], ids=lambda r: r['case'])
def test_complete_self_host_continues_but_controls_keep_their_old_result(row):
    req = request(row['memo'])
    p = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(p)
    out = MeaningExperienceEngine().generate(req)
    if row['case'] in IMPROVED or row['case'] in {'base','both_self','right_self'}:
        assert out.artifact, out.reason_codes
        assert 'と聞いて、私も少し安心しましたが' in out.artifact.reception
        assert '今、耳を傾けていたいです' in out.artifact.reception
        assert 'かもしれない' in out.artifact.observation
        assert row['memo'].split('。')[0] in out.artifact.observation
        assert facets(project_thread_meaning(p, plan).selected_reception)
        assert p.checkpoint.checkpoint_id != row['checkpoint']['checkpoint_id']
        assert inverse(actual(request=req), out.artifact.reception, without_author=True).passed
        if row['case'] == 'with_unknown':
            assert '私にもまだわからない' in out.artifact.observation
        if row['case'] == 'with_question':
            assert out.question is not None
    else:
        assert encoded(p.checkpoint) == row['checkpoint']
        assert digest(plan) == row['plan_sha']
        assert (encoded(out.artifact) if out.artifact else None) == row['body']
        assert list(out.reason_codes) == row['reasons']
        assert (encoded(out.question) if out.question else None) == row['question']


@pytest.mark.parametrize('row', BASELINE['cases'], ids=lambda r: r['case'])
def test_saved_u332_meaning_is_rederived_in_full(row):
    assert BASELINE['source_commit'] == '2af661109e81456bce0da03b7d2df34cf3c93129'
    req = request(row['memo'])
    req = replace(req, emlis_thread=replace(req.emlis_thread,
        prepared_meaning_checkpoint_ref=row['checkpoint']['checkpoint_id']))
    p = prepare_emlis_meaning(req)
    assert p.legacy_cognitive_self_continuation == (row['case'] in IMPROVED)
    assert encoded(p.checkpoint) == row['checkpoint']
    plan = build_updated_grounded_plan(p)
    assert digest(plan) == row['plan_sha']
    if 'error' in row:
        with pytest.raises(ValueError) as error:
            project_thread_meaning(p, plan)
        assert type(error.value).__name__ + ':' + str(error.value) == row['error']
    else:
        assert digest(project_thread_meaning(p, plan).selected_reception) == row['selected_sha']
    out = MeaningExperienceEngine().generate(req)
    assert (encoded(out.artifact) if out.artifact else None) == row['body']
    assert list(out.reason_codes) == row['reasons']
    assert (encoded(out.question) if out.question else None) == row['question']


@pytest.mark.parametrize('memo', ['私は'+BASE, '僕は'+BASE, '私は'+BASE+'何が不安なのか、私にもまだわからない。'])
def test_q1_and_q3_keep_the_same_new_body(memo):
    one = MeaningExperienceEngine().generate(initial(memo))
    three = MeaningExperienceEngine().generate(request(memo))
    assert one.artifact and three.artifact and one.artifact.text == three.artifact.text
    assert one.question is None and three.question is None


@pytest.fixture(scope='module', params=[False, True], ids=['NORMAL', 'LIMITED'])
def current_context(request):
    memo = '私は'+BASE+('何が不安なのか、私にもまだわからない。' if request.param else '')
    from test_cmee_emlis_source_scope_regressions import request as generation_request
    context = actual(request=generation_request(memo))
    assert context[4].decisions[0].branch == ('LIMITED' if request.param else 'NORMAL')
    return context


@pytest.mark.parametrize('before,after', [
    ('あなたは', '友達は'), ('あなたは', '私は'),
    ('友達からの誘い', '上司からの誘い'),
    ('ほっとした', 'ほっとしなかった'),
    ('かもしれない', 'に違いない'), ('寂しい', '怖い'),
    ('と聞いて、', 'が原因で、'),
    ('私も少し安心しましたが、', ''),
    ('今、耳を傾けていたいです', '違いを感じています'),
    ('今、耳を傾けていたいです', 'これから誘われるはずです'),
])
def test_current_body_rejects_owner_object_scope_and_facet_loss_without_author(current_context, before, after):
    from test_cmee_emlis_detached_observation import read_body
    body = current_context[0].artifact.text
    # The original SELF actor is now retained in Layer 1.
    before, after = (('私は', '友達は' if after == '友達は' else '僕は')
                     if before == 'あなたは' else (before, after))
    changed = body.replace(before, after)
    assert changed != body
    assert not read_body(current_context, changed).passed


@pytest.mark.parametrize('name,old,new,time', UPDATES, ids=[r[0] for r in UPDATES])
def test_actual_question_revision_or_withdrawal_drops_old_joint_reaction(name, old, new, time):
    left = '私は'+LEFT
    old = left if old == LEFT else old
    req = begin('私は'+BASE+'褒められたのに、嬉しくなかった。')
    first = MeaningExperienceEngine().generate(req)
    assert first.artifact and first.question
    reply = f'「{old}」ではなく「{new}」です。' if new else f'「{old}」は誤りです。'
    req = advance(req, reply)
    p = prepare_emlis_meaning(req)
    update, = p.checkpoint.answer_update.updates
    assert update.operation == ('REVISE' if new else 'WITHDRAW')
    assert not p.checkpoint.unresolved_parts
    plan = build_updated_grounded_plan(p)
    assert not facets(project_thread_meaning(p, plan).selected_reception)
    out = MeaningExperienceEngine().generate(req)
    assert out.artifact, out.reason_codes
    assert old not in out.artifact.observation
    assert (RIGHT if old == left else left) in out.artifact.observation
    assert '私も少し安心しました' not in out.artifact.reception
    assert '耳を傾けていたい' not in out.artifact.reception
    if new:
        assert new in out.artifact.observation
        assert any(n.source_fields == ('answer_text_private',) and n.semantic_frame.time_scope == time for n in plan.nuclei)
    assert inverse(actual(request=req), out.artifact.reception, without_author=True).passed


def test_other_source_or_forged_checkpoint_cannot_restore_self_continuation():
    row = BASELINE['cases'][0]
    for memo, reference in [('私は'+BASE, 'foreign'), ('友達は'+BASE, row['checkpoint']['checkpoint_id'])]:
        req = request(memo)
        with pytest.raises(ValueError, match='emlis_checkpoint_source_prefix_mismatch'):
            prepare_emlis_meaning(replace(req, emlis_thread=replace(req.emlis_thread,
                prepared_meaning_checkpoint_ref=reference)))


from test_emlis_q3_application import qdb, qcase
from test_emlis_q2_application import run, answer


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
def test_service_saves_and_rereads_new_self_body_without_generation(qcase, qdb, monkeypatch, tier):
    user, parent, service = qcase
    qdb.query('update public.profiles set subscription_tier=$2 where id=$1', [user, tier])
    qdb.query('update public.emotions set memo=$2 where id=$1', [parent, '私は'+BASE])
    dto = run(service.start(user, parent))
    assert dto['body_state'] == 'FINAL' and dto['pending_question'] is None
    assert '「私は友達からの誘い' in dto['current_observation']['text']
    assert 'その寂しさにも、今、耳を傾けていたいです。' in dto['current_observation']['text']
    assert '私も少し安心しました' in dto['current_observation']['text']
    monkeypatch.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved body regenerated'))
    assert run(service.get(user, parent)) == dto
    assert run(service.start(user, parent)) == dto


@pytest.mark.parametrize('name,old,new,time', UPDATES, ids=[r[0] for r in UPDATES])
def test_service_keeps_self_source_update_and_reread(qcase, qdb, monkeypatch, name, old, new, time):
    user, parent, service = qcase
    qdb.query('update public.emotions set memo=$2 where id=$1', [parent, '私は'+BASE+'褒められたのに、嬉しくなかった。'])
    old = '私は'+LEFT if old == LEFT else old
    first = run(service.start(user, parent))
    assert first['pending_question']
    reply = f'「{old}」ではなく「{new}」です。' if new else f'「{old}」は誤りです。'
    dto = run(answer(service, user, first, reply, 'self-continuation-'+name))
    assert dto['body_state'] == 'REFINED' and dto['original'] == first['original']
    body = dto['current_observation']['text']
    assert old not in body and '私も少し安心しました' not in body and '耳を傾けていたい' not in body
    assert (RIGHT if old == '私は'+LEFT else '私は'+LEFT) in body
    assert new is None or new in body
    monkeypatch.setattr(service.engine, 'generate', lambda *_: pytest.fail('saved body regenerated'))
    assert run(service.get(user, parent)) == dto
    assert run(service.start(user, parent)) == dto


@pytest.mark.parametrize('ending', ['これは友人の話でした。', 'これは友人の話であった。', 'これは友人の感想だった。'])
@pytest.mark.parametrize('field', ['memo', 'memo_action'])
def test_past_attribution_cannot_activate_new_self_continuation(ending, field):
    from cocolon_meaning_experience_engine.emlis_question import original_meaning_plan
    req = initial('私は'+BASE+(ending if field == 'memo' else ''), ending if field == 'memo_action' else '')
    req = replace(req, execution_mode='EMLIS_APPLICATION',
        emlis_thread=replace(req.emlis_thread, capability_snapshot='Q3_FREE'))
    p = prepare_emlis_meaning(req)
    old = original_meaning_plan(p.thread, _legacy_cognitive_self_continuation=True)
    assert p.original_plan.nuclei == old.nuclei and p.original_plan.relations == old.relations
    assert not any(c.startswith('source_relief_cognition_slot:') for n in p.original_plan.nuclei for c in n.semantic_frame.attribute_codes)
