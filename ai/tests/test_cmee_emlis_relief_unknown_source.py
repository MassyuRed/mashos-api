"""Existing three-object sources survive reflexive/value detector defaults."""
from dataclasses import replace
import json
from pathlib import Path
import pytest
import emlis_ai_grounded_observation_plan as gp
from cocolon_meaning_experience_engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning, build_updated_grounded_plan
from cocolon_meaning_experience_engine.emlis_thread_projection import project_thread_meaning
from test_cmee_emlis_relief_cognition import BASE, encoded, digest
from test_cmee_emlis_source_scope_regressions import request
from test_cmee_emlis_q1_thread import initial
from test_cmee_emlis_received_discourse import actual, inverse

BASELINE = json.loads((Path(__file__).parent/'fixtures/cmee_emlis_u334_relief_unknown_source_v1.json').read_text())
IMPROVED = {'relief','unknown_jibun','relief_self','relief_boku','relief_degree',
            'relief_unknown_boku','relief_jibun','jibun_self','jibun_doko'}


def assert_record(req, row):
    p = prepare_emlis_meaning(req); plan = build_updated_grounded_plan(p)
    assert encoded(p.checkpoint) == row['checkpoint']
    assert digest(plan) == row['plan_sha']
    if 'error' in row:
        with pytest.raises(ValueError) as error: project_thread_meaning(p, plan)
        assert type(error.value).__name__+':'+str(error.value) == row['error']
    else:
        assert digest(project_thread_meaning(p, plan).selected_reception) == row['selected_sha']
    out = MeaningExperienceEngine().generate(req)
    assert (encoded(out.artifact) if out.artifact else None) == row['body']
    assert list(out.reason_codes) == row['reasons']
    assert (encoded(out.question) if out.question else None) == row['question']
    return p


@pytest.mark.parametrize('row', BASELINE['cases'], ids=lambda row: row['case'])
def test_complete_original_meaning_and_delivery_against_u334(row):
    req = request(row['memo'])
    if row['case'] not in IMPROVED:
        assert_record(req, row)
        return
    p = prepare_emlis_meaning(req); plan = build_updated_grounded_plan(p)
    assert row['body'] is None
    assert p.checkpoint.checkpoint_id != row['checkpoint']['checkpoint_id']
    out = MeaningExperienceEngine().generate(req)
    assert out.artifact and out.question is None
    assert '私も少し安心しましたが' in out.artifact.reception
    assert '今、耳を傾けていたいです。' in out.artifact.reception
    assert ('ご自身' if '自分' in row['memo'] else 'あなた') in out.artifact.reception
    assert 'わからないのですね' in out.artifact.reception or '分からないのですね' in out.artifact.reception
    group = gp._source_relief_cognition_unknown_from_resolver(plan.nuclei, plan.relations, p.thread.resolver())
    assert len(group) == 3
    unknown, left, right = group
    assert (unknown.kind, unknown.semantic_frame.predicate_kind) == ('uncertainty','uncertainty')
    assert all(n.retention == 'required' for n in group)
    incident = [r for r in plan.relations if unknown.nucleus_id in (r.from_nucleus_id,r.to_nucleus_id)]
    assert all(r.type == 'uncertain_connection' and r.retention != 'required'
               and r.grounding_kind == 'bounded_structural_inference' for r in incident)
    aggregate, = project_thread_meaning(p, plan).meaning_plan.subjective_claim_rows
    assert len(aggregate.asserted_subjective_proposition.response_object_refs) == 3
    resumed = MeaningExperienceEngine().generate(replace(req, emlis_thread=replace(req.emlis_thread,
        prepared_meaning_checkpoint_ref=p.checkpoint.checkpoint_id)))
    assert resumed.artifact == out.artifact


@pytest.mark.parametrize('row', BASELINE['cases'], ids=lambda row: row['case'])
def test_saved_u334_checkpoint_restores_complete_old_record(row):
    assert BASELINE['source_commit'] == 'd5d47b81ed95cf081224cf5918627073ace18673'
    req = request(row['memo'])
    req = replace(req, emlis_thread=replace(req.emlis_thread,
        prepared_meaning_checkpoint_ref=row['checkpoint']['checkpoint_id']))
    p = assert_record(req, row)
    assert p.legacy_relief_unknown_source == (row['case'] in IMPROVED)


@pytest.fixture(scope='module', params=['relief','unknown_jibun','relief_jibun','jibun_doko'])
def context(request):
    row = next(r for r in BASELINE['cases'] if r['case'] == request.param)
    return actual(request=initial(row['memo']))


def test_independent_reader_q1_q3_and_existing_synonym(context):
    body = context[0].artifact.reception
    assert inverse(context, body, without_author=True).passed
    assert inverse(context, body.replace('私も少し安心しましたが','私も少しほっとしましたし'), without_author=True).passed
    source = context[3].source_text_for_span_field('s1')
    out = MeaningExperienceEngine().generate(request(source))
    assert out.artifact.text == context[0].artifact.text and out.question is None


@pytest.mark.parametrize('mutation', ['relief','loneliness','unknown','object','owner','time','certainty','cause'])
def test_reader_rejects_missing_facets_and_changed_unknown_source(context, mutation):
    body = context[0].artifact.reception
    if mutation == 'relief': changed = body.replace('私も少し安心しましたが、','')
    elif mutation == 'loneliness': changed = body.replace('今、耳を傾けていたいです','違いを感じています')
    elif mutation == 'unknown': changed = body[:body.index('です。')+3]
    elif mutation == 'object': changed = body.replace('何が嫌なのか','何が嬉しいのか').replace('何が不安なのか','何が悲しいのか').replace('どこが不安なのか','どこが悲しいのか')
    elif mutation == 'owner': changed = body.replace('ご自身でも','友達でも').replace('あなたにも','友達にも').replace('ご自身にも','友達にも')
    elif mutation == 'time': changed = body.replace('わからない','わからなかった').replace('分からない','分からなかった')
    elif mutation == 'certainty': changed = body.replace('かもしれない','に違いない')
    else: changed = body.replace('です。何が','です。だから、何が').replace('です。どこが','です。だから、どこが')
    assert changed != body
    assert not inverse(context, changed, without_author=True).passed


@pytest.mark.parametrize('mutation', ['cause','result','foreign_provenance','foreign_arc','missing_span','foreign_endpoint','inferred_grounding','optional_retention'])
def test_source_repair_cannot_downgrade_an_asserted_or_foreign_edge(mutation):
    row = next(r for r in BASELINE['cases'] if r['case'] == 'relief')
    req = request(row['memo']); req = replace(req, emlis_thread=replace(req.emlis_thread,
        prepared_meaning_checkpoint_ref=row['checkpoint']['checkpoint_id']))
    p = prepare_emlis_meaning(req); plan = build_updated_grounded_plan(p)
    edge, = (r for r in plan.relations if r.type == 'attempt_and_block')
    if mutation in {'cause','result'}: changed = replace(edge, type='user_stated_'+mutation)
    elif mutation == 'foreign_provenance': changed = replace(edge, source_relation_ids=('foreign',))
    elif mutation == 'foreign_arc': changed = replace(edge, source_meaning_arc_keys=('foreign',))
    elif mutation == 'inferred_grounding': changed = replace(edge, grounding_kind='bounded_structural_inference')
    elif mutation == 'optional_retention': changed = replace(edge, retention='should')
    elif mutation == 'missing_span': changed = replace(edge, source_span_ids=edge.source_span_ids[:1])
    else: changed = replace(edge, from_nucleus_id='foreign')
    edges = tuple(changed if r == edge else r for r in plan.relations)
    resolver = p.thread.resolver()
    assert gp._final_source_relief_unknown(plan.nuclei, edges, resolver.resolve_many(resolver.span_ids),
        p.thread.original.normalized_current_input) == (plan.nuclei, edges)
