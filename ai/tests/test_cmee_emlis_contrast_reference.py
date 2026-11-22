"""Concrete contrast objects survive realization without new meaning selection."""

from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path

import pytest

from cocolon_meaning_experience_engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning, build_updated_grounded_plan
from cocolon_meaning_experience_engine.emlis_thread_projection import project_thread_meaning
from emlis_ai_grounded_observation_plan import _source_separate_contrast_objects_from_resolver
from test_cmee_emlis_source_scope_regressions import request
from test_cmee_emlis_q1_thread import initial
from test_cmee_emlis_received_discourse import actual, inverse


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
        separators=(',', ':')).encode()).hexdigest()


BASELINE = json.loads((Path(__file__).parent / 'fixtures' /
    'cmee_emlis_u330_contrast_reference_v1.json').read_text())
IMPROVED = {'base', 'hiragana_degree', 'tada', 'distinct_times', 'negative_joy', 'negative_fatigue'}


@pytest.mark.parametrize('row', BASELINE['cases'], ids=lambda row: row['case'])
def test_contrast_reference_preserves_original_meaning_and_unproved_controls(row):
    assert BASELINE['source_commit'] == '44d8e47836d3443d446ff31cf167963c06548e9f'
    req = request(row['memo'])
    p = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(p)
    assert digest(asdict(p.checkpoint)) == row['checkpoint_sha256']
    assert digest([asdict(n) for n in plan.nuclei]) == row['nuclei_sha256']
    assert digest([asdict(r) for r in plan.relations]) == row['relations_sha256']
    if row['decisions_sha256'] is not None:
        assert digest(asdict(project_thread_meaning(p, plan).selected_reception)['decisions']) == row['decisions_sha256']
    out = MeaningExperienceEngine().generate(req)
    improved = row['case'] in IMPROVED
    groups = [_source_separate_contrast_objects_from_resolver(m, plan.nuclei,
        plan.relations, p.thread.resolver()) for m in plan.response_plan.human_reception_plan.moves]
    assert any(groups) == improved
    if improved:
        assert out.artifact and out.artifact.text != row['body']
        assert out.artifact.observation == row['observation']
        assert out.question is None and out.question_decision.disposition == 'END'
        follow = out.artifact.reception
        pair, = (g for g in groups if g)
        for nucleus in pair:
            raw = p.thread.resolver().resolve(nucleus.source_span_ids[0]).raw_text
            assert raw + 'こと' in follow
        assert not any(s in follow for s in ('今ここに置かれた言葉', 'もう一方の向き'))
        context = actual(request=req)
        assert context[0].artifact.text == out.artifact.text
        assert inverse(context, follow, without_author=True).passed
    else:
        assert (out.artifact.text if out.artifact else None) == row['body']
        assert list(out.reason_codes) == row['reason_codes']


@pytest.mark.parametrize('row', [r for r in BASELINE['cases'] if r['case'] in IMPROVED], ids=lambda row: row['case'])
def test_original_q1_uses_the_same_proved_contrast_reference(row):
    old_route = MeaningExperienceEngine().generate(initial(row['memo']))
    modern = MeaningExperienceEngine().generate(request(row['memo']))
    assert old_route.artifact and modern.artifact
    assert old_route.artifact.text == modern.artifact.text


@pytest.fixture(scope='module')
def time_context():
    return actual(request=request('昨日は友達と話せて嬉しかった。でも、今日は疲れている。'))


@pytest.mark.parametrize('before,after', [
    ('昨日は', '今日は'), ('今日は', '昨日は'),
    ('嬉しかった', '嬉しくなかった'), ('疲れている', '疲れていない'),
    ('友達と', '上司と'), ('友達と', '私は友達と'),
    ('と今日は疲れていること', ''),
    ('昨日は友達と話せて嬉しかったことと', ''),
    ('の両方を、その違いも含めて', 'の因果関係を'),
])
def test_contrast_objects_cannot_lose_source_time_owner_or_endpoint(time_context, before, after):
    follow = time_context[0].artifact.reception
    changed = follow.replace(before, after)
    assert changed != follow
    assert not inverse(time_context, changed, without_author=True).passed


@pytest.mark.parametrize('change', [
    dict(retention='optional'), dict(type='cause_effect'),
    dict(grounding_kind='bounded_structural_inference'),
    dict(source_relation_ids=()), dict(source_relation_ids=('conflict.e1',)),
    dict(source_span_ids=('s1',)),
])
def test_contrast_reference_requires_the_explicit_relation_provenance(change):
    p = prepare_emlis_meaning(request('友達と話せて嬉しかった。でも、疲れた。'))
    plan = build_updated_grounded_plan(p)
    move, = plan.response_plan.human_reception_plan.moves
    edge, = plan.relations
    assert _source_separate_contrast_objects_from_resolver(move, plan.nuclei, plan.relations, p.thread.resolver())
    assert not _source_separate_contrast_objects_from_resolver(move, plan.nuclei,
        (replace(edge, **change),), p.thread.resolver())
