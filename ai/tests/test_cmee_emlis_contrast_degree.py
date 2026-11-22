"""Degree belongs to the source predicate, not to the topic-particle guard."""
from dataclasses import asdict, is_dataclass, replace
import hashlib
import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest
import emlis_ai_grounded_observation_plan as gp
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
    'cmee_emlis_u340_contrast_degree_v1.json').read_text())
IMPROVED = {'degree_first', 'degree_both', 'degree_second', 'degree_negative',
    'degree_untimed_first', 'degree_untimed_second', 'degree_time_also', 'degree_now'}


def encoded(value):
    if is_dataclass(value): return encoded(asdict(value))
    if isinstance(value, (tuple, list)): return [encoded(v) for v in value]
    if isinstance(value, dict): return {k: encoded(v) for k, v in value.items()}
    return value


def digest(value):
    return hashlib.sha256(json.dumps(encoded(value), ensure_ascii=False,
        sort_keys=True, separators=(',', ':')).encode()).hexdigest()


@pytest.mark.parametrize('row', BASELINE['cases'], ids=lambda r: r['case'])
def test_degree_repairs_only_reference_realization(row):
    assert BASELINE['source_commit'] == '741463920723bae5ac81d5052a779ca838778cfe'
    req = request(row['memo'])
    prepared = prepare_emlis_meaning(req)
    plan = build_updated_grounded_plan(prepared)
    assert digest(prepared.checkpoint) == row['checkpoint_sha']
    assert prepared.checkpoint.checkpoint_id == row['checkpoint_id']
    assert digest(plan.nuclei) == row['nuclei_sha']
    assert digest(plan.relations) == row['relations_sha']
    reception = plan.response_plan.human_reception_plan
    restored = replace(plan, response_plan=replace(plan.response_plan,
        human_reception_plan=replace(reception, moves=tuple(replace(m, reference_mode=mode)
            for m, mode in zip(reception.moves, row['reference_modes'], strict=True)))))
    assert digest(restored) == row['plan_sha']
    if 'projection_error' in row:
        with pytest.raises(ValueError, match=row['projection_error']):
            project_thread_meaning(prepared, plan)
    else:
        selected = project_thread_meaning(prepared, plan).selected_reception
        assert digest(selected.decisions) == row['decisions_sha']
        if row['case'] not in IMPROVED:
            assert digest(selected) == row['selected_sha']
    out = MeaningExperienceEngine().generate(req)
    assert encoded(out.question) == row['question']
    assert encoded(out.question_decision) == row['question_decision']
    assert list(out.reason_codes) == row['reasons']
    if row['case'] not in IMPROVED:
        assert digest(plan) == row['plan_sha']
        assert digest(out.artifact) == row['artifact_sha']
        return
    assert digest(plan) != row['plan_sha']
    assert all(m.reference_mode == 'short_anchor_if_ambiguous' for m in reception.moves)
    # The resolver proof keeps full clauses, including every degree word.
    resolver = prepared.thread.resolver()
    pair = gp._source_separate_contrast_objects_from_resolver(
        reception.moves[0], plan.nuclei, plan.relations, resolver)
    assert len(pair) == 2
    left, right = (resolver.resolve(n.source_span_ids[0]).raw_text for n in pair)
    assert out.artifact.reception == f'{left}ことと{right}ことの両方を、その違いも含めて小さくせずに受け止めています。'
    assert out.artifact.reception.count('とても') == row['memo'].count('とても')
    if 'untimed' not in row['case']:
        assert out.artifact.observation == f'「{left}」の一方で「{right}」とあります。'
        assert '同時' not in out.artifact.observation
    else:
        assert out.artifact.observation == row['observation']
    assert out.question is None and out.question_decision.disposition == 'END'
    assert not out.automatic_progression
    restored_request = replace(req, emlis_thread=replace(req.emlis_thread,
        prepared_meaning_checkpoint_ref=row['checkpoint_id']))
    assert MeaningExperienceEngine().generate(restored_request).artifact == out.artifact
    assert MeaningExperienceEngine().generate(initial(row['memo'])).artifact.text == out.artifact.text


@pytest.fixture(scope='module', params=['degree_both', 'degree_negative'])
def context(request):
    row = next(r for r in BASELINE['cases'] if r['case'] == request.param)
    return actual(request=initial(row['memo']))


@pytest.mark.parametrize('mutation', ['observation_degree', 'reception_degree',
    'reception_swapped_degree', 'time', 'owner', 'polarity', 'cause',
    'simultaneous', 'missing_operand', 'extra_claim'])
def test_body_reader_preserves_degree_without_an_author(context, mutation):
    artifact = context[0].artifact
    observation, reception = artifact.observation, artifact.reception
    if mutation == 'observation_degree': observation = observation.replace('とても', '', 1)
    elif mutation == 'reception_degree': reception = reception.replace('とても', '', 1)
    elif mutation == 'reception_swapped_degree':
        reception = 'とても' + reception.replace('とても', '', 1)
    elif mutation == 'time': observation = observation.replace('昨日', '今日')
    elif mutation == 'owner': reception = reception.replace('友達と', '友達が')
    elif mutation == 'polarity': observation = observation.replace('疲れている', '疲れていない')
    elif mutation == 'cause': observation = observation.replace('の一方で', 'が原因で')
    elif mutation == 'simultaneous': observation = '同時に、' + observation
    elif mutation == 'missing_operand': reception = reception.split('ことと', 1)[1]
    else: reception += 'だから明日はきっと元気になります。'
    changed = artifact.text.replace(artifact.observation, observation).replace(artifact.reception, reception)
    assert changed != artifact.text
    with patch.object(surface, '_realize_line', side_effect=AssertionError('no surface oracle')):
        assert read_body(context, artifact.text).passed
        assert not read_body(context, changed).passed


class NoGeneration:
    def __getattr__(self, name):
        raise AssertionError('saved body attempted generation: ' + name)


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
@pytest.mark.parametrize('case', ['degree_both', 'degree_negative'])
@pytest.mark.parametrize('historical', [False, True], ids=['current', 'historical_body'])
def test_saved_degree_body_reopens_without_generation(qcase, qdb, tier, case, historical):
    from emlis_thread_service import EmlisThreadService, Q3_PROFILE
    user, parent, service = qcase
    row = next(r for r in BASELINE['cases'] if r['case'] == case)
    qdb.query('update public.profiles set subscription_tier=$2 where id=$1', [user, tier])
    qdb.query('update public.emotions set memo=$2 where id=$1', [parent, row['memo']])
    if historical:
        # Reproduce the pre-repair proof only during creation. Reads use the
        # real service and may neither generate nor replace the saved body.
        with patch.object(gp, 'source_owned_separate_contrast_objects', return_value=()):
            saved = run(service.start(user, parent))
        assert saved['current_observation']['text'] == row['body']
    else:
        saved = run(service.start(user, parent))
        assert 'の一方で' in saved['current_observation']['text']
        assert '同時' not in saved['current_observation']['text']
        assert saved['current_observation']['text'].count('とても') == 2 * row['memo'].count('とても')
    assert saved['state'] == 'COMPLETED' and saved['body_state'] == 'FINAL'
    assert saved['pending_question'] is None and not saved['can_continue']
    assert not any(e['kind'] in {'QUESTION', 'ANSWER'} for e in saved['timeline'])
    reader = EmlisThreadService(runtime_profile=Q3_PROFILE, engine=NoGeneration())
    assert run(reader.get(user, parent)) == saved
    assert run(reader.start(user, parent)) == saved
    if folder := os.environ.get('CMEE_CONTRAST_DEGREE_DTO_DIR'):
        Path(folder).mkdir(parents=True, exist_ok=True)
        Path(folder, f'{tier}-{case}-{historical}.json').write_text(json.dumps(saved, ensure_ascii=False))
