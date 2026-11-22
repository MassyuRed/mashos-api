"""Initial explanation stays original source; u352 replay remains complete."""
from dataclasses import replace
from functools import lru_cache
import json
from pathlib import Path
import pytest
from cocolon_meaning_experience_engine import MeaningExperienceEngine, contracts as c
from cocolon_meaning_experience_engine import emlis_answer_update as update
from cocolon_meaning_experience_engine.emlis_thread_contracts import SupplementalAnswerSource
from cocolon_meaning_experience_engine.emlis_thread_projection import project_thread_meaning
import emlis_ai_grounded_observation_plan as gp
import emlis_ai_grounded_human_reception as hr
from test_cmee_emlis_q1_thread import initial
from test_cmee_emlis_q3_thread import begin, advance
from test_cmee_emlis_relief_received import checkpoint, decode_question, full_snapshot
from test_cmee_emlis_received_discourse import actual
from test_cmee_emlis_detached_observation import read_body
from test_cmee_emlis_contrast_degree import digest

BASELINE = json.loads((Path(__file__).parent / 'fixtures/cmee_emlis_u352_initial_personal_meaning_v1.json').read_text())
ROWS = {r['case']: r for r in BASELINE['cases']}
UPDATES = {r['case']: r for r in BASELINE['updates']}
QUALIFIED = {'received', 'received_unknown', 'pair_received', 'pair_received_unknown', 'then', 'canonical', 'degree', 'positive'}

@lru_cache(None)
def request(case, profile='q3', answered=False, historical=False):
    row = (UPDATES if answered else ROWS)[case]
    req = (initial if profile == 'q1' else begin)(row['memo'])
    if not answered:
        return checkpoint(req, row[profile]['checkpoint_id']) if historical else req
    if historical:
        q = decode_question(row[profile + '_initial']['question'])
    else:
        q = MeaningExperienceEngine().generate(req).question
        assert q is not None
    t = req.emlis_thread
    answer = SupplementalAnswerSource('answer-1', t.thread_id, q.question_id, 1,
        t.original_source_ref, row['answer'], '2026-09-11T01:00:00Z')
    control = replace(t.question_control_context, pending_question=q,
        asked_target_refs=(q.decision.target_ref,), issued_count=1, issued_questions=(q,))
    req = replace(req, emlis_thread=replace(t, answers=(answer,), current_round=1,
        prepared_meaning_checkpoint_ref=row[profile]['checkpoint_id'] if historical else None,
        question_control_context=control))
    return req if historical else checkpoint(req, update.prepare_emlis_meaning(req).checkpoint.checkpoint_id)

@pytest.mark.parametrize('profile', ['q1', 'q3'])
@pytest.mark.parametrize('answered,case', [(False,k) for k in ROWS] + [(True,k) for k in UPDATES])
def test_u352_full_checkpoint_plan_selection_body_and_stop(answered, case, profile):
    assert BASELINE['source_commit'] == 'a47d26fc2469bc3461549f9b4a58a37c2bb6c50f'
    row = (UPDATES if answered else ROWS)[case]
    p, _ = full_snapshot(request(case,profile,answered,True), row[profile])
    assert digest(p.accepted_nuclei) == row[profile]['accepted_nuclei_sha']

@pytest.mark.parametrize('case', sorted(QUALIFIED))
@pytest.mark.parametrize('profile', ['q1','q3'])
def test_initial_three_roles_and_all_independent_duties_reach_body(case, profile):
    req = request(case,profile)
    context = actual(request=req)
    out, plan, _, resolver, selected = context
    group = gp._source_initial_personal_meaning_from_resolver(plan.nuclei,plan.relations,resolver)
    assert group
    unknown,left,right,event,reaction,meaning,*_ = group
    p = update.prepare_emlis_meaning(req)
    assert not p.thread.answers and not p.accepted_nuclei and p.checkpoint.answer_update is None
    assert p.checkpoint.checkpoint_id != ROWS[case][profile]['checkpoint_id']
    assert meaning.source_fields == ('memo',) and meaning.semantic_frame.time_scope == 'past'
    assert all(e.type != 'evaluation_about_event' for e in plan.relations)
    assert len(selected.decisions) == 1 + bool(left) + bool(unknown)
    local = selected.decisions[0].initial_received_personal_meaning
    assert type(local) is c.InitialReceivedPersonalMeaningContentV1
    assert (len(local.basis_rows),len(local.qualifier_rows)) == (3,3)
    refs = [ref for d in selected.decisions for ref in d.selected_contribution_refs]
    assert len(set(refs)) == len(refs) == 2+bool(left)+bool(unknown)
    assert set(refs) == set(selected.decisions[0].subjective_proposition.target_contribution_refs)
    body=out.artifact.text
    assert '一つの流れ' not in out.artifact.observation and '同時' not in out.artifact.observation
    assert '今は、' not in out.artifact.observation
    source=resolver.resolve(meaning.source_span_ids[0]).raw_text
    assert source.removesuffix('です') in out.artifact.reception
    assert '嬉しくなかったし、' in out.artifact.reception
    if left:
        assert '私も少し安心しましたが' in out.artifact.reception
        assert 'その寂しさにも' in out.artifact.reception
    if unknown:
        assert 'わからない' in out.artifact.reception
    assert read_body(context,body).passed
    public=MeaningExperienceEngine().generate(req)
    assert public.artifact and public.artifact.text==body
    assert public.question is None and public.question_decision.disposition=='END'

@pytest.mark.parametrize('case', sorted(set(ROWS)-QUALIFIED))
def test_nonqualified_source_keeps_complete_previous_interpretation(case):
    full_snapshot(request(case),ROWS[case]['q3'])

@pytest.mark.parametrize('profile',['q1','q3'])
@pytest.mark.parametrize('meaning',[
    '私は期待されている気がして、重かった。',
    '期待されているようで、軽かった。',
])
def test_qualified_source_variants_never_ask_already_supplied_meaning(meaning,profile):
    req=(initial if profile=='q1' else begin)('褒められたのに、嬉しくなかった。'+meaning)
    context=actual(request=req)
    _,plan,_,resolver,_=context
    assert gp._source_initial_personal_meaning_from_resolver(plan.nuclei,plan.relations,resolver)
    out=MeaningExperienceEngine().generate(req)
    assert out.artifact and out.question is None and out.question_decision.disposition=='END'
    assert meaning.strip('。').replace('私は','あなたは') in out.artifact.reception
    assert read_body(context,out.artifact.text).passed

@pytest.mark.parametrize('case', list(UPDATES))
def test_existing_actual_pending_answer_revise_withdraw(case):
    req=request(case,answered=True)
    context=actual(request=req)
    p=update.prepare_emlis_meaning(req)
    out=context[0]
    assert p.checkpoint.answer_update and read_body(context,out.artifact.text).passed
    if case.startswith('add'):
        assert '重かった' in out.artifact.reception
        assert '嬉しさを伴わない経験' in out.artifact.reception or '嬉しくなかった' in out.artifact.reception
    if 'mixed' in case:
        assert 'わからない' in out.artifact.reception
    if case!='add_received' and case!='revise_received':
        assert '私も少し安心しましたが' in out.artifact.reception
    if case=='withdraw_event':
        assert '褒められた' not in out.artifact.text
    if case=='withdraw_reaction':
        assert '嬉しくなかった' not in out.artifact.text
    public=MeaningExperienceEngine().generate(req)
    assert public.artifact and public.artifact.text==out.artifact.text

@pytest.mark.parametrize('correction',[
    '「期待されているように感じて、重かった」ではなく「期待されているように感じて、苦しかった」です。',
    '「期待されているように感じて、重かった」は誤りです。',
    '「重かった」は誤りです。',
])
def test_actual_q3_next_question_keeps_full_explanation_correction_scope(correction):
    first=advance(begin(),'期待されているように感じて、重かった。')
    prior=MeaningExperienceEngine().generate(first)
    assert prior.question and prior.artifact
    following=advance(first,correction)
    p=update.prepare_emlis_meaning(following)
    out=MeaningExperienceEngine().generate(following)
    if correction=='「重かった」は誤りです。':
        assert out.artifact is None and 'correction_target_unresolved' in out.reason_codes
        assert not p.accepted_nuclei and not p.checkpoint.inactive_claim_refs
        assert not p.checkpoint.answer_update.updates
        assert following.emlis_thread.answers[:-1] == first.emlis_thread.answers
        assert p.checkpoint.unresolved_parts[0].reason_code=='correction_target_unresolved'
        return
    assert out.artifact,out.reason_codes
    assert '期待されているように感じて、重かった' not in out.artifact.text
    assert not p.checkpoint.unresolved_parts
    if '苦しかった' in correction:
        assert '期待されているように感じて、苦しかった' in out.artifact.text
    assert '褒められた' in out.artifact.text and '誘われた' in out.artifact.text
    assert read_body(actual(request=following),out.artifact.text).passed
