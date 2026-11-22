"""Existing separate SELF objects retain their distinct original times."""
from dataclasses import asdict, replace
import hashlib
import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest
import emlis_ai_grounded_observation_plan as gp
import emlis_ai_grounded_observation_gate as gate
import emlis_ai_grounded_sentence_surface as surface
from cocolon_meaning_experience_engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.emlis_answer_update import prepare_emlis_meaning, build_updated_grounded_plan
from cocolon_meaning_experience_engine.emlis_thread_projection import project_thread_meaning
from test_cmee_emlis_source_scope_regressions import request
from test_cmee_emlis_q1_thread import initial
from test_cmee_emlis_received_discourse import actual
from test_cmee_emlis_detached_observation import read_body
from test_emlis_q3_application import qdb, qcase
from test_emlis_q2_application import run

BASELINE = json.loads((Path(__file__).parent / 'fixtures' /
    'cmee_emlis_u339_separate_time_contrast_v1.json').read_text())
IMPROVED = {'past_today', 'past_now', 'negative', 'past_also', 'punctuation'}


def digest(value):
    return hashlib.sha256(json.dumps(asdict(value), ensure_ascii=False,
        sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def encoded(value):
    return json.loads(json.dumps(asdict(value))) if value is not None else None


@pytest.mark.parametrize('row', BASELINE['cases'], ids=lambda r: r['case'])
def test_only_proved_separate_time_observation_changes(row):
    assert BASELINE['source_commit'] == 'd28e7bc079c3a8bceb30f94d539f416625a12e39'
    req = request(row['memo'])
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    assert digest(prepared.checkpoint) == row['checkpoint_sha']
    assert digest(plan) == row['plan_sha']
    if 'projection_error' in row:
        with pytest.raises(ValueError, match=row['projection_error']):
            project_thread_meaning(prepared, plan)
    else:
        assert digest(project_thread_meaning(prepared, plan).selected_reception) == row['selected_sha']
    ids = gp.source_owned_separate_time_contrast_ids(plan, prepared.thread.resolver())
    assert bool(ids) == (row['case'] in IMPROVED)
    out = MeaningExperienceEngine().generate(req)
    assert encoded(out.question) == row['question']
    assert encoded(out.question_decision) == row['question_decision']
    assert list(out.reason_codes) == row['reasons']
    if row['case'] not in IMPROVED:
        assert encoded(out.artifact) == row['artifact']
        return
    edge, = (r for r in plan.relations if r.relation_id in ids)
    index = {n.nucleus_id: n for n in plan.nuclei}
    left, right = (prepared.thread.resolver().resolve(index[nid].source_span_ids[0]).raw_text
                   for nid in (edge.from_nucleus_id, edge.to_nucleus_id))
    assert out.artifact.observation == f'「{left}」の一方で「{right}」とあります。'
    assert out.artifact.reception == row['artifact']['reception']
    assert out.question is None and out.question_decision.disposition == 'END'
    assert not out.automatic_progression
    # The same saved meaning checkpoint receives a repaired realization.
    restored = replace(req, emlis_thread=replace(req.emlis_thread,
        prepared_meaning_checkpoint_ref=row['checkpoint_id']))
    assert MeaningExperienceEngine().generate(restored).artifact == out.artifact
    assert MeaningExperienceEngine().generate(initial(row['memo'])).artifact.text == out.artifact.text


@pytest.fixture(scope='module', params=['past_today', 'past_now', 'negative'])
def context(request):
    row = next(r for r in BASELINE['cases'] if r['case'] == request.param)
    return actual(request=initial(row['memo']))


@pytest.mark.parametrize('mutation', ['simultaneous', 'cause', 'swapped_time', 'missing_time',
    'missing_operand', 'owner', 'polarity', 'extra_sentence', 'extra_prefix'])
def test_reader_consumes_complete_neutral_contrast_without_an_author(context, mutation):
    body = context[0].artifact.text
    observation = context[0].artifact.observation
    if mutation == 'simultaneous':
        changed = observation.replace('の一方で', 'と').replace('とあります。', 'が、異なる向きのまま同時にあります。')
    elif mutation == 'cause': changed = observation.replace('の一方で', 'が原因で')
    elif mutation == 'swapped_time': changed = observation.replace('昨日', '今日')
    elif mutation == 'missing_time': changed = observation.replace('昨日は', '')
    elif mutation == 'missing_operand': changed = observation[observation.index('の一方で') + 4:]
    elif mutation == 'owner': changed = observation.replace('友達と', '友達が')
    elif mutation == 'polarity': changed = observation.replace('疲れている', '疲れていない')
    elif mutation == 'extra_sentence': changed = observation + '両方は同時に起きています。'
    else: changed = '同時に、' + observation
    assert changed != observation
    with patch.object(surface, '_realize_line', side_effect=AssertionError('no surface oracle')):
        assert read_body(context, body).passed
        assert not read_body(context, body.replace(observation, changed)).passed


@pytest.mark.parametrize('change', ['same_time', 'forged_times', 'owner', 'coexistence', 'no_marker', 'missing_move'])
def test_time_realization_cannot_expand_original_source_qualification(context, change):
    _, plan, _, resolver, _ = context
    ids = gp.source_owned_separate_time_contrast_ids(plan, resolver)
    assert len(ids) == 1
    edge, = (r for r in plan.relations if r.relation_id in ids)
    if change in {'same_time', 'forged_times', 'owner'}:
        def altered(n):
            if n.nucleus_id not in {edge.from_nucleus_id, edge.to_nucleus_id}: return n
            if change == 'owner': frame = replace(n.semantic_frame, actor='other')
            else:
                value = 'past' if change == 'same_time' else ('present' if n.semantic_frame.time_scope == 'past' else 'past')
                frame = replace(n.semantic_frame, time_scope=value)
            return replace(n, semantic_frame=frame)
        plan = replace(plan, nuclei=tuple(altered(n) for n in plan.nuclei))
    elif change == 'missing_move':
        plan = replace(plan, response_plan=replace(plan.response_plan,
            human_reception_plan=replace(plan.response_plan.human_reception_plan, moves=())))
    else:
        altered = replace(edge, **({'type': 'coexistence'} if change == 'coexistence' else {'source_relation_ids': ()}))
        plan = replace(plan, relations=tuple(altered if r == edge else r for r in plan.relations))
    assert not gp.source_owned_separate_time_contrast_ids(plan, resolver)


class NoGeneration:
    def __getattr__(self, name):
        raise AssertionError('saved body attempted generation: ' + name)


def test_only_the_proved_required_edge_receives_neutral_time_grammar(context):
    _, plan, _, resolver, _ = context
    proved = gp.source_owned_separate_time_contrast_ids(plan, resolver)
    edge, = (r for r in plan.relations if r.relation_id in proved)
    extra = tuple(replace(edge, relation_id='optional:' + kind, type=kind, retention='optional')
                  for kind in ('contrast', 'coexistence', 'user_stated_cause'))
    plan = replace(plan, relations=(*plan.relations, *extra))
    assert gp.source_owned_separate_time_contrast_ids(plan, resolver) == proved


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
@pytest.mark.parametrize('case', ['past_today', 'negative'])
@pytest.mark.parametrize('historical', [False, True], ids=['current', 'historical_body'])
def test_saved_complete_body_reopens_without_generation(qcase, qdb, tier, case, historical):
    from emlis_thread_service import EmlisThreadService, Q3_PROFILE
    user, parent, service = qcase
    row = next(r for r in BASELINE['cases'] if r['case'] == case)
    qdb.query('update public.profiles set subscription_tier=$2 where id=$1', [user, tier])
    qdb.query('update public.emotions set memo=$2 where id=$1', [parent, row['memo']])
    if historical:
        # Reproduce the prior renderer, then require exact pre-edit body bytes.
        # SQL storage and all subsequent reads use the actual service.
        with patch.object(surface, 'source_owned_separate_time_contrast_ids', return_value=frozenset()), \
             patch.object(gate, 'source_owned_separate_time_contrast_ids', return_value=frozenset()):
            saved = run(service.start(user, parent))
        assert saved['current_observation']['text'] == (
            '見えたこと：\n' + row['artifact']['observation'] + '\n\nEmlisから：\n' + row['artifact']['reception'])
    else:
        saved = run(service.start(user, parent))
        assert 'の一方で' in saved['current_observation']['text']
        assert '同時' not in saved['current_observation']['text']
    assert saved['state'] == 'COMPLETED' and saved['body_state'] == 'FINAL'
    assert saved['pending_question'] is None and not saved['can_continue']
    assert not any(e['kind'] in {'QUESTION', 'ANSWER'} for e in saved['timeline'])
    reader = EmlisThreadService(runtime_profile=Q3_PROFILE, engine=NoGeneration())
    assert run(reader.get(user, parent)) == saved
    assert run(reader.start(user, parent)) == saved
    if folder := os.environ.get('CMEE_SEPARATE_TIME_DTO_DIR'):
        Path(folder).mkdir(parents=True, exist_ok=True)
        Path(folder, f'{tier}-{case}-{historical}.json').write_text(json.dumps(saved, ensure_ascii=False))
