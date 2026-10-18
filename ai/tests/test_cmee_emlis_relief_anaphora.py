"""Short Layer-2 references require complete, unique actual Layer-1 meaning."""
from dataclasses import replace
import json
from pathlib import Path
from unittest.mock import patch

import pytest
import emlis_ai_grounded_human_reception as hr
import emlis_ai_grounded_observation_gate as gate
import emlis_ai_grounded_sentence_surface as surface
from cocolon_meaning_experience_engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning, build_updated_grounded_plan
from cocolon_meaning_experience_engine.emlis_thread_projection import project_thread_meaning
from cocolon_meaning_experience_engine.emlis_thread_surface import _bind_expression
from test_cmee_emlis_relief_cognition import BASE, LEFT, RIGHT, encoded, digest
from test_cmee_emlis_relief_unknown import UNKNOWN
from test_cmee_emlis_source_scope_regressions import request
from test_cmee_emlis_q1_thread import initial
from test_cmee_emlis_received_discourse import actual
from test_cmee_emlis_detached_observation import read_body

BASELINE = json.loads((Path(__file__).parent/'fixtures/cmee_emlis_u335_relief_anaphora_v1.json').read_text())


@pytest.mark.parametrize('row', BASELINE['cases'], ids=lambda row: row['case'])
def test_current_source_outcomes_keep_observation_and_shorten_only_selected_pair(row):
    out = MeaningExperienceEngine().generate(request(row['memo']))
    assert bool(out.artifact) == bool(row['body'])
    assert list(out.reason_codes) == row['reasons']
    assert (encoded(out.question) if out.question else None) == row['question']
    if not out.artifact:
        return
    assert out.artifact.observation == row['body']['observation']
    old = row['body']['reception']
    if '私も少し安心しましたが' in old:
        assert 'その寂しさにも、今、耳を傾けていたいです。' in out.artifact.reception
        assert len(out.artifact.reception) < len(old)
        assert 'かもしれない' not in out.artifact.reception
    else:
        assert out.artifact.reception == old


@pytest.mark.parametrize('row', BASELINE['cases'], ids=lambda row: row['case'])
def test_saved_u335_checkpoint_rederives_every_old_field_and_full_body(row):
    assert BASELINE['source_commit'] == '0717bd4d7dc6483ee1ddfdb34721feccc7955c6c'
    req = request(row['memo'])
    req = replace(req, emlis_thread=replace(req.emlis_thread,
        prepared_meaning_checkpoint_ref=row['checkpoint']['checkpoint_id']))
    p = prepare_emlis_meaning(req); plan = build_updated_grounded_plan(p)
    assert encoded(p.checkpoint) == row['checkpoint']
    assert digest(plan) == row['plan_sha']
    if 'error' in row:
        with pytest.raises(ValueError) as exc: project_thread_meaning(p, plan)
        assert type(exc.value).__name__+':'+str(exc.value) == row['error']
    else:
        assert digest(project_thread_meaning(p, plan).selected_reception) == row['selected_sha']
    out = MeaningExperienceEngine().generate(req)
    assert (encoded(out.artifact) if out.artifact else None) == row['body']
    assert list(out.reason_codes) == row['reasons']
    assert (encoded(out.question) if out.question else None) == row['question']


@pytest.fixture(scope='module', params=['base', 'self', 'relief_degree', 'jibun_doko', 'relief_pair'])
def context(request):
    row = next(r for r in BASELINE['cases'] if r['case'] == request.param)
    return row, actual(request=initial(row['memo']))


def test_actual_short_body_preserves_complete_observation_and_same_two_antecedents(context):
    row, ctx = context
    out, plan, sentence, resolver, selected = ctx
    assert out.artifact.observation == row['body']['observation']
    assert out.artifact.reception.startswith(('ほっとしたと聞いて、', '安心したと聞いて、'))
    assert 'その寂しさにも、今、耳を傾けていたいです。' in out.artifact.reception
    assert len(out.artifact.reception) < len(row['body']['reception'])
    p = prepare_emlis_meaning(initial(row['memo']))
    assert p.checkpoint.checkpoint_id != row['checkpoint']['checkpoint_id']
    projection = project_thread_meaning(p, plan)
    move = plan.response_plan.human_reception_plan.moves[0]
    expression = _bind_expression(plan, resolver, projection, move, 'FINITE')
    assert expression.reference_mode == 'ANAPHORIC'
    assert expression.antecedent_condition == 'PRIOR_LAYER1_EXACT_SEMANTIC_COVER'
    assert len(expression.antecedent_refs) == 2
    pairs = dict(selected.semantic_nucleus_pairs)
    assert {pairs[ref] for ref in expression.antecedent_refs} == set((*move.target_nucleus_ids, *move.support_nucleus_ids))
    with patch.object(surface, '_realize_line', side_effect=AssertionError('no Layer-1 author')):
        assert read_body(ctx, out.artifact.text).passed
        changed = out.artifact.text.replace('私も少し安心しましたが', '私も少しほっとしましたし')
        assert changed != out.artifact.text and read_body(ctx, changed).passed
    three = MeaningExperienceEngine().generate(request(row['memo']))
    assert three.artifact.text == out.artifact.text and three.question is None


@pytest.fixture(scope='module')
def complete():
    return actual(request=initial('私は'+BASE.replace('寂しい','少し寂しい')+UNKNOWN))


@pytest.mark.parametrize('mutation', ['missing_left','missing_right','short_left','short_right','swap',
    'duplicate','owner','past','degree','possibility','condition','feeling','contrast','cause','extra_sentence',
    'unknown_missing','unknown_owner','unknown_past','unknown_cause'])
def test_actual_observation_mutations_cannot_license_short_reception(complete, mutation):
    artifact = complete[0].artifact
    obs = artifact.observation
    left, right = '私は'+LEFT, RIGHT.replace('寂しい','少し寂しい')
    if mutation == 'missing_left': changed = obs.replace('「'+left+'」','')
    elif mutation == 'missing_right': changed = obs.replace('「'+right+'」','')
    elif mutation == 'short_left': changed = obs.replace(left,'ほっとした')
    elif mutation == 'short_right': changed = obs.replace(right,'寂しい')
    elif mutation == 'swap': changed = obs.replace(left,'REPLACE').replace(right,left).replace('REPLACE',right)
    elif mutation == 'duplicate': changed = obs+'\n'+obs.splitlines()[0]
    elif mutation == 'owner': changed = obs.replace('私は','友達は')
    elif mutation == 'past': changed = obs.replace('ほっとした','ほっとする')
    elif mutation == 'degree': changed = obs.replace('少し寂しい','とても寂しい')
    elif mutation == 'possibility': changed = obs.replace('かもしれない','に違いない')
    elif mutation == 'condition': changed = obs.replace('と思うと','ので')
    elif mutation == 'feeling': changed = obs.replace('寂しい','怖い')
    elif mutation == 'contrast': changed = obs.replace('の一方で','と')
    elif mutation == 'cause': changed = obs.replace('の一方で','が原因で')
    elif mutation == 'extra_sentence': changed = obs.splitlines()[0]+'安心しました。\n'+obs.splitlines()[1]
    elif mutation == 'unknown_missing': changed = obs.splitlines()[0]
    elif mutation == 'unknown_owner': changed = obs.replace('私にも','友達にも')
    elif mutation == 'unknown_past': changed = obs.replace('わからない','わからなかった')
    else: changed = obs.replace('今回の中心には、','その寂しさが原因で、')
    assert changed != obs
    body = artifact.text.replace(obs, changed)
    with patch.object(surface, '_realize_line', side_effect=AssertionError('no Layer-1 author')):
        assert not read_body(complete, body).passed


@pytest.mark.parametrize('before,after', [('私も少し安心しましたが、',''),
    ('今、耳を傾けていたいです','違いを感じています'),('その寂しさ','その嬉しさ'),
    ('その寂しさ','その時の寂しさ'),('ほっとしたと聞いて','ほっとしなかったと聞いて'),
    ('私も少し安心しました','あなたも少し安心しました'),
    ('何が不安なのか、あなたにもまだわからないのですね。',''),
    ('です。何が','です。だから、何が')])
def test_short_reception_keeps_both_facets_and_independent_unknown(complete,before,after):
    body = complete[0].artifact.text; changed = body.replace(before,after)
    assert changed != body and not read_body(complete,changed).passed


def test_valid_but_ambiguous_reference_falls_back_to_complete_reception_and_bad_observation_stays_rejected(complete):
    out, plan, sentence, resolver, selected = complete
    move = plan.response_plan.human_reception_plan.moves[0]
    pair = gate._relief_cognition_selected_reception(move,plan,resolver,selected)
    obs = out.artifact.observation
    assert gate._relief_cognition_observation_antecedents(pair,move,resolver,obs)
    assert not gate._relief_cognition_observation_antecedents(pair,move,resolver,obs+'\n別の寂しさがあります。')
    assert not gate._relief_cognition_observation_antecedents(pair,move,resolver,None)
    clauses, = (line.reception_clause_plans for line in sentence.lines if line.binding.line_role=='human_follow')
    full = hr.replay_source_grounded_human_reception_from_plan(plan.response_plan.human_reception_plan,
        {n.nucleus_id:n for n in plan.nuclei},resolver,plan=plan,recovery_stage='full',clause_plans=clauses,
        selected_subjective_input=selected,preceding_observation=None)
    assert 'その寂しさ' not in full.text and 'かもしれない' in full.text
    body = out.artifact.text.replace(out.artifact.reception,full.text)
    assert read_body(complete,body).passed
    assert not read_body(complete,body.replace('かもしれない','に違いない',1)).passed
    # A prior Reception is not a Layer-1 antecedent, even if it copies it.
    first = out.artifact.reception.split('。')[0]+'。'
    assert gate.read_source_owned_discourse(first,move,plan,resolver,selected,
        preceding_context=(move,obs)) is None


@pytest.mark.parametrize('mutation',['reference_mode','antecedent_refs','antecedent_condition'])
def test_existing_expression_contract_cannot_drop_or_replace_antecedent_duties(complete,mutation):
    out, plan, sentence, resolver, selected = complete
    p=prepare_emlis_meaning(initial('私は'+BASE.replace('寂しい','少し寂しい')+UNKNOWN))
    projection=project_thread_meaning(p,plan); reception=plan.response_plan.human_reception_plan
    expressions=tuple(_bind_expression(plan,resolver,projection,m,'FINITE') for m in reception.moves)
    change={'reference_mode':'EXPLICIT','antecedent_refs':(),
            'antecedent_condition':'FOREIGN_LAYER'}[mutation]
    forged=hr.identify_source_grounded_reception_expression(replace(expressions[0],**{mutation:change}))
    clauses, = (line.reception_clause_plans for line in sentence.lines if line.binding.line_role=='human_follow')
    with pytest.raises(hr.GroundedHumanReceptionSurfaceError):
        hr.realize_source_grounded_human_reception(reception,(forged,*expressions[1:]),
            {n.nucleus_id:n for n in plan.nuclei},resolver,plan=plan,recovery_stage='full',clause_plans=clauses,
            selected_subjective_input=selected,preceding_observation=out.artifact.observation)


def test_actual_ambiguous_unknown_preserves_full_reception():
    ctx = actual(request=initial(BASE+'何が寂しいのか、私にもまだわからない。'))
    body = ctx[0].artifact
    assert 'かもしれない' in body.reception and 'その寂しさにも' not in body.reception
    assert '何が寂しいのか、あなたにもまだわからないのですね。' in body.reception
    assert read_body(ctx,body.text).passed


def test_old_checkpoint_cannot_acquire_short_reference_permission():
    row=next(r for r in BASELINE['cases'] if r['case']=='base')
    req=request(row['memo']);req=replace(req,emlis_thread=replace(req.emlis_thread,
        prepared_meaning_checkpoint_ref=row['checkpoint']['checkpoint_id']))
    ctx=actual(request=req)
    short='ほっとしたと聞いて、私も少し安心しましたが、その寂しさにも、今、耳を傾けていたいです。'
    full=ctx[0].artifact.reception;changed=short+full[full.index('です。')+3:]
    body=ctx[0].artifact.text.replace(full,changed)
    assert changed != full and not read_body(ctx,body).passed
