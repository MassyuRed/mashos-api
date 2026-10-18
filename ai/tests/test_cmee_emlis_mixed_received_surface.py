"""Mixed received experience keeps its source time without changing its meaning."""
from dataclasses import fields, replace
from functools import lru_cache
import json
from pathlib import Path
import re
import os
import pytest
from cocolon_meaning_experience_engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine import emlis_answer_update as update
from cocolon_meaning_experience_engine.emlis_thread_projection import project_thread_meaning
from cocolon_meaning_experience_engine.emlis_thread_surface import _current_single_received_contrast_relations as owned
from test_cmee_emlis_contrast_degree import encoded, digest
import test_cmee_emlis_relief_received as received
import test_cmee_emlis_unknown_revision_time as unknown
from test_cmee_emlis_received_discourse import actual
from test_cmee_emlis_detached_observation import read_body

BASELINE = json.loads((Path(__file__).parent / 'fixtures' /
    'cmee_emlis_u354_mixed_received_surface_v1.json').read_text())
ROWS = BASELINE['cases']


def request(row):
    if row['kind'] == 'unknown_answer': return unknown.request(row['case'], row['profile'])
    return received.request(row['case'], row['profile'], row['kind'] == 'received_answer')


def neutral_observation(text, memo):
    # Only the complete received sentence can differ; source link is preserved.
    pattern = r'「([^「」]+)」と「([^「」]+)」が、異なる向きのまま同時にあります。'
    matches = list(re.finditer(pattern, text))
    assert len(matches) <= 1
    if not matches: return text
    left, right = matches[0].groups()
    link = re.search(re.escape(left) + r'(のに|けれども|けれど|けど)[、,]?' + re.escape(right), memo)
    assert link is not None
    return text.replace(matches[0][0], f'「{left}」{link[1]}「{right}」という経験が書かれています。', 1)


@pytest.mark.parametrize('row', ROWS, ids=lambda r: r['kind']+'-'+r['case']+'-'+r['profile'])
def test_u354_whole_meaning_reception_and_only_received_observation_change(row):
    assert BASELINE['source_commit'] == '7f9209ef1e8c0dfb56ddc72499440ac8ccb6180e'
    req = request(row); p = update.prepare_emlis_meaning(req)
    assert digest(p.checkpoint) == row['checkpoint_sha']
    assert digest(p.original_plan) == row['original_sha']
    assert digest(p.accepted_nuclei) == row['accepted_sha']
    if 'plan_error' in row:
        with pytest.raises(ValueError, match=row['plan_error']): update.build_updated_grounded_plan(p)
    else:
        plan = update.build_updated_grounded_plan(p)
        assert digest(plan) == row['plan_sha']
        if 'projection_error' in row:
            with pytest.raises(ValueError, match=row['projection_error']): project_thread_meaning(p, plan)
        else: assert digest(project_thread_meaning(p, plan).selected_reception) == row['selected_sha']
    out = MeaningExperienceEngine().generate(unknown.checkpoint(req, p.checkpoint.checkpoint_id))
    assert (out.status.value, out.body_state, list(out.reason_codes)) == (row['status'], row['body_state'], row['reasons'])
    assert encoded(out.question) == row['question']
    assert encoded(out.question_decision) == row['question_decision']
    if out.artifact is None:
        assert digest(None) == row['artifact_sha']; return
    artifact = encoded(out.artifact)
    new_id = artifact.pop('artifact_id'); observation = artifact.pop('observation')
    assert digest(artifact) == row['artifact_other_sha']
    assert out.artifact.reception == row['reception']
    changed = row['kind'] == 'initial' or (row['kind'] == 'unknown_answer' and row['case'] in {
        'mixed_unknown_now', 'mixed_unknown_current_negative', 'mixed_reflexive_now', 'mixed_unknown_now_negative'})
    expected = neutral_observation(row['observation'], row['memo']) if changed else row['observation']
    assert (expected != row['observation']) == changed
    if row['case'] == 'mixed_unknown_then':
        assert p.checkpoint.assessment_status == 'PARTIAL' and not owned(p, plan)
    assert observation == expected
    assert (new_id != row['artifact_id']) == (expected != row['observation'])
    assert not out.automatic_progression
    if folder := os.environ.get('CMEE_MIXED_RECEIVED_BODY_DIR'):
        Path(folder).mkdir(parents=True, exist_ok=True)
        Path(folder, row['kind']+'-'+row['case']+'-'+row['profile']+'.json').write_text(
            json.dumps(dict(case=row['case'], memo=row['memo'], body=out.artifact.text), ensure_ascii=False, indent=2)+'\n')


@pytest.fixture(scope='module', params=['base_unknown', 'received_owned_unknown', 'negative'])
def context(request):
    req = unknown.request('mixed_unknown_current_negative', 'q3') if request.param == 'negative' else received.request(request.param)
    return actual(request=req)


@pytest.mark.parametrize('mutation', ['time', 'polarity', 'event', 'simultaneous', 'cause', 'order', 'reverse', 'drop', 'link', 'duplicate', 'extra'])
def test_existing_independent_reader_preserves_full_received_source(context, mutation):
    body = context[0].artifact.text
    observation = context[0].artifact.observation
    sentences = re.findall(r'「([^「」]+)」(のに|けれども|けれど|けど)「([^「」]+)」という経験が書かれています。', observation)
    assert len(sentences) == 1
    left, link, right = sentences[0]
    clause = f'「{left}」{link}「{right}」という経験が書かれています。'
    changed = {
        'time': clause.replace('嬉しくなかった', '嬉しくない'),
        'polarity': clause.replace('嬉しくなかった', '嬉しかった'),
        'event': clause.replace('褒められた', '誘われた'),
        'simultaneous': clause.replace(link, 'の一方で同時に'),
        'cause': clause.replace(link, 'のが原因で'),
        'order': clause.replace(link, 'のあとに'),
        'reverse': f'「{right}」{link}「{left}」という経験が書かれています。',
        'drop': '',
        'duplicate': clause + clause,
        'extra': clause + 'これが寂しさの原因です。',
        'link': clause.replace(link, 'けど' if link != 'けど' else 'のに'),
    }[mutation]
    assert changed != clause
    assert read_body(context, body).passed
    assert not read_body(context, body.replace(clause, changed, 1)).passed


def test_source_and_current_ownership_does_not_revive_replaced_material():
    req = received.request('base_unknown'); p = update.prepare_emlis_meaning(req)
    plan = update.build_updated_grounded_plan(p); rid, = owned(p, plan)
    edge = next(r for r in plan.relations if r.relation_id == rid)
    assert not owned(replace(p, checkpoint=replace(p.checkpoint, assessment_status='PARTIAL')), plan)
    for name in (f.name for f in fields(p) if f.name.startswith('legacy_')):
        assert not owned(replace(p, **{name: True}), plan)
    for nid in (edge.from_nucleus_id, edge.to_nucleus_id):
        for frame in ({'actor':'other_person'}, {'time_scope':'present'}, {'polarity':'positive'}):
            node = next(n for n in plan.nuclei if n.nucleus_id == nid)
            if all(getattr(node.semantic_frame, k) == v for k,v in frame.items()): continue
            changed = replace(node, semantic_frame=replace(node.semantic_frame, **frame))
            assert not owned(p, replace(plan, nuclei=tuple(changed if n==node else n for n in plan.nuclei)))
    assert not owned(p, replace(plan, relations=tuple(r for r in plan.relations if r != edge)))
    for case in ('revise_unknown', 'withdraw_event_unknown', 'withdraw_reaction_unknown'):
        revised = update.prepare_emlis_meaning(received.request(case, answered=True))
        assert not owned(revised, update.build_updated_grounded_plan(revised))
    # An extra source span or missing witness cannot inherit the bounded proof.
    original = p.thread.original
    changed_source = replace(original, normalized_current_input=dict(original.normalized_current_input, memo=original.normalized_current_input['memo']+'別の出来事。'))
    assert not owned(replace(p, thread=replace(p.thread, original=changed_source)), plan)
    stripped = replace(p.original_plan, nuclei=tuple(replace(n, semantic_frame=replace(n.semantic_frame,
        attribute_codes=tuple(c for c in n.semantic_frame.attribute_codes if c != 'source_relief_received_retention:v1'))) for n in p.original_plan.nuclei))
    assert not owned(replace(p, original_plan=stripped), plan)


@pytest.mark.parametrize('lost', ['私は', '少し'])
def test_received_subject_and_degree_are_not_optional(lost):
    context = actual(request=received.request('received_owned_unknown'))
    body = context[0].artifact.text
    old = '「私は少し嬉しくなかった」という経験が書かれています。'
    assert old in body and read_body(context, body).passed
    assert not read_body(context, body.replace(old, old.replace(lost, ''), 1)).passed
