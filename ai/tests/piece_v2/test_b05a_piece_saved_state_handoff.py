"""Original-only saved-stage handoff; no live auth, DB, API or native claim.

Shape/adversarial tests use synthetic control records. SQL tests separately use
unmodified EmlisThreadService + migration + real CMEE to create the saved result.
The current upstream requires selected feelings; Piece still refuses them.
State admission is tested separately and never called end-to-end body success.
"""
import asyncio
import copy
import importlib.util
import json
import os
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException
import pytest
import httpx
import api_account_visibility
import emlis_thread_store
from emlis_thread_service import EmlisThreadService, RUNTIME_PROFILE, Q3_PROFILE
from cocolon_meaning_experience_engine.emlis_thread_contracts import SEMANTIC_SCHEMA
from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
import piece_v2_source_adapter as mod

OWNER = '40000000-0000-4000-8000-000000000001'
INPUT = '50000000-0000-4000-8000-000000000001'
THREAD = '60000000-0000-4000-8000-000000000001'
AUTH = 'Bearer synthetic-owner-session'
THOUGHT = '余裕があるなら、私が選びたいのは、陶芸です。'
ACTION = 'まだ、始める日は決めていません。'
BODY = '余裕があるなら、私は陶芸を選びたい。\n\n' + ACTION
STAMP = '2026-09-26T00:30:00+00:00'
OPERATION = '70000000-0000-4000-8000-000000000001'
ATTEMPT = '80000000-0000-4000-8000-000000000001'


def adapter_type():
    assert hasattr(mod.PieceSavedSourceAdapter, 'resolve_original_handoff'), 'saved-state original handoff is not implemented'
    return mod.PieceSavedSourceAdapter


def run(awaitable):
    return asyncio.run(awaitable)


@pytest.fixture(autouse=True)
def prerequisites(monkeypatch):
    async def verify(token):
        if token != 'synthetic-owner-session':
            raise HTTPException(401, 'private diagnostic')
        return OWNER
    monkeypatch.setattr(api_account_visibility, '_resolve_user_id_from_token', verify)


def event(n, kind, payload, round_index=0):
    return {'id': f'90000000-0000-4000-8000-{n:012d}', 'thread_id': THREAD,
        'seq': n, 'kind': kind, 'round_index': round_index,
        'question_id': 'synthetic-question' if kind == 'QUESTION' else None,
        'operation_id': OPERATION, 'attempt_id': ATTEMPT,
        'recorded_at': STAMP, 'payload': payload}


def snapshot(pre=False, tier='free', profile=RUNTIME_PROFILE):
    original = {'id': INPUT, 'created_at': '2026-09-26T00:00:00', 'memo': THOUGHT,
        'memo_action': ACTION, 'category': ['生活'], 'emotions': [], 'emotion_details': []}
    cp = event(1, 'MEANING_UPDATE', {'semantic_schema_version': SEMANTIC_SCHEMA,
        'source_prefix_ref': 'synthetic-prefix', 'checkpoint_id': 'synthetic-checkpoint', 'answer_update': None})
    obs = event(2, 'OBSERVATION', {'stage': 'INITIAL', 'source_prefix_ref': 'synthetic-prefix',
        'meaning_checkpoint_ref': 'synthetic-checkpoint', 'text': 'PRIVATE EMLIS BODY MUST NOT ENTER PIECE',
        'artifact': {'interpretation': 'PRIVATE INTERPRETATION'}})
    state = 'AWAITING_ANSWER' if pre else 'COMPLETED'
    events = [cp, obs]
    if pre:
        events.append(event(3, 'QUESTION', {'schema_version': 'cocolon.cmee.emlis_clarification.v1',
            'question_id': 'synthetic-question', 'thread_id': THREAD, 'original_source_ref': 'synthetic-original',
            'prompt_private': 'PRIVATE QUESTION', 'decision': {'disposition': 'ASK'}}, 1))
    events.append(event(len(events)+1, 'OPERATION', {'status': state, 'failure_code': None}))
    thread = {'id': THREAD, 'user_id': OWNER, 'original_emotion_id': INPUT,
        'revision': 3, 'state': state, 'source_snapshot': copy.deepcopy(original),
        'source_prefix_ref': 'synthetic-prefix', 'evaluated_prefix_ref': 'synthetic-prefix',
        'issued_count': int(pre), 'current_meaning_event_id': cp['id'], 'last_observation_event_id': obs['id'],
        'latest_answer_event_id': None, 'active_operation_id': None, 'active_attempt_id': None,
        'processing_deadline_at': None,
        'data': {'runtime_profile': profile, 'body_state': 'PRE_QUESTION' if pre else 'FINAL',
            'original_source_ref': 'synthetic-original', 'failure_code': None, 'meaning_updated': False,
            'answer_assessment': 'NOT_APPLICABLE', 'operation_id': OPERATION, 'attempt_id': ATTEMPT,
            'context_guards': [], 'context_feedback': [], 'evaluated_tier': tier}}
    return {'original': original, 'tier': tier, 'now': '2026-09-26T01:00:00+00:00', 'thread': thread, 'events': events}


class Store:
    def __init__(self, value):
        self.value, self.calls = value, []
        self.live_context = {'history': [], 'feedback': []}
    async def read(self, owner, *, input_id=None):
        self.calls.append((owner, input_id))
        return copy.deepcopy(self.value)
    async def context(self, owner, input_id):
        return copy.deepcopy(self.live_context)
    async def commit(self, *args, **kwargs):
        pytest.fail('Piece handoff must not write')


def resolve(value):
    return run(adapter_type()(store=Store(value)).resolve_original_handoff(AUTH, INPUT))


@pytest.mark.parametrize('pre', [False, True])
def test_saved_state_not_caller_value_selects_original_only_stage_and_actual_body(pre):
    store = Store(snapshot(pre)); adapter = adapter_type()(store=store)
    result = run(adapter.generate_original_candidate_from_saved_state(AUTH, INPUT))
    assert result['candidate']['piece_text'] == BODY
    print('SAVED_STATE_SYNTHETIC_CONTROL', json.dumps({'pre': pre, 'original': store.value['original'],
        'result': result}, ensure_ascii=False))
    assert store.calls == [(OWNER, INPUT), (OWNER, INPUT)]
    line = result['source_lineage']; observation = line['observation']
    assert line['source_input']['source_recorded_at'] == '2026-09-26T00:00:00+00:00'
    assert store.value['original']['created_at'] == '2026-09-26T00:00:00'
    assert observation['emlis_observation_stage'] == ('pre_question_observation' if pre else 'normal_observation')
    assert observation['emlis_observation_result_identity'] == store.value['events'][1]['id']
    assert observation['emlis_observation_result_state'] == 'terminal_success'
    assert observation['question_need_decision_identity'] == (store.value['events'][2]['id'] if pre else None)
    assert line['semantic_source_roles'] == ['original_input']
    assert line['piece_generation_eligibility']['decision'] == 'eligible'
    assert line['lineage_control_roles'] == ['emlis_observation_result'] + (['question_need_decision'] if pre else [])
    assert all(observation[key] is None for key in ('supplemental_answer_identity',
        'supplemental_answer_version', 'supplemental_answer_bundle_commitment'))
    assert result['candidate']['record_effect'] == result['candidate']['quota_effect'] == 0
    assert result['candidate']['production_enabled'] is False
    assert 'PRIVATE' not in json.dumps(result, ensure_ascii=False)


@pytest.mark.parametrize('action', ['skip', 'stop'])
def test_closed_unanswered_question_retains_pre_question_identity(action):
    s = snapshot(True); s['thread']['state'] = 'COMPLETED'; s['thread']['data']['body_state'] = 'FINAL'
    s['events'].append(event(5, 'TERMINAL', {'reason': action}))
    assert resolve(s).lineage_payload()['observation']['emlis_observation_stage'] == 'pre_question_observation'


def test_source_and_control_payloads_are_immutable_copies_without_visible_body_reuse(monkeypatch):
    saved = resolve(snapshot(True)); line = saved.lineage_payload()
    line['semantic_source_roles'].append('analysis_inference')
    saved.original.original_payload()['memo'] = 'changed'
    assert saved.lineage_payload()['semantic_source_roles'] == ['original_input']
    assert saved.original.original_payload()['memo'] == THOUGHT
    assert 'PRIVATE' not in json.dumps(saved.lineage_payload()) and THOUGHT not in repr(saved)
    actual = MeaningExperienceEngine.generate; seen = []
    def piece_only(self, request):
        from cocolon_meaning_experience_engine.piece_v1c import PieceGenerationRequest
        assert isinstance(request, PieceGenerationRequest), 'handoff must not generate Emlis'
        seen.append(request)
        return actual(self, request)
    monkeypatch.setattr(MeaningExperienceEngine, 'generate', piece_only)
    result = run(adapter_type()(store=Store(snapshot(True)))
        .generate_original_candidate_from_saved_state(AUTH, INPUT))
    assert len(seen) == 1 and result['candidate']['piece_text'] == BODY
    assert seen[0].source.saved_original_json == saved.original._original_json


@pytest.mark.parametrize('change', [
    'no_thread','initializing','refining','failed','active','missing_lease','body_unavailable',
    'answer_pointer','answer_event','unchanged_answer','refined','source_edit','prefix',
    'missing_observation','stale_checkpoint','checkpoint_schema','checkpoint_ref','checkpoint_update',
    'other_thread_event','duplicate_event','unsorted','missing_finish','failed_finish',
    'other_attempt','missing_original_ref','invalid_revision','future_result','profile',
    'question_count','question_source','question_decision','question_finish','closed_without_terminal',
])
def test_unfinished_stale_refined_or_invalid_control_cannot_issue_original_eligibility(change):
    s = snapshot(change.startswith('question') or change == 'closed_without_terminal')
    t, d, events = s['thread'], s['thread']['data'], s['events']
    if change == 'no_thread': s['thread'] = None
    elif change in ('initializing','refining','failed'): t['state'] = {'initializing':'INITIALIZING','refining':'REFINING','failed':'RESPONSE_FAILED'}[change]
    elif change == 'active': t['active_attempt_id'] = ATTEMPT
    elif change == 'missing_lease': del t['active_attempt_id']
    elif change == 'body_unavailable': d['body_state'] = 'MEANING_UPDATED_BODY_UNAVAILABLE'
    elif change == 'answer_pointer': t['latest_answer_event_id'] = events[0]['id']
    elif change == 'answer_event': events.append(event(5,'ANSWER',{'source':{'answer_text_private':'PRIVATE ANSWER'}},1))
    elif change == 'unchanged_answer': d.update(body_state='UNCHANGED',answer_assessment='NO_MATERIAL_UPDATE')
    elif change == 'refined': events[1]['payload']['stage'] = 'REFINED'
    elif change == 'source_edit': s['original']['memo'] += ' '
    elif change == 'prefix': t['evaluated_prefix_ref'] = 'different-prefix'
    elif change == 'missing_observation': events.pop(1)
    elif change == 'stale_checkpoint': t['current_meaning_event_id'] = events[1]['id']
    elif change == 'checkpoint_schema': events[0]['payload']['semantic_schema_version'] = 'unknown'
    elif change == 'checkpoint_ref': events[1]['payload']['meaning_checkpoint_ref'] = 'other'
    elif change == 'checkpoint_update': events[0]['payload']['answer_update'] = {'disposition':'UPDATED'}
    elif change == 'other_thread_event': events[1]['thread_id'] = INPUT
    elif change == 'duplicate_event': events.insert(1,copy.deepcopy(events[0]))
    elif change == 'unsorted': events.reverse()
    elif change == 'missing_finish': events.pop()
    elif change == 'failed_finish': events[-1]['payload']['failure_code'] = 'body_not_validated'
    elif change == 'other_attempt': events[1]['attempt_id'] = INPUT
    elif change == 'missing_original_ref': del d['original_source_ref']
    elif change == 'invalid_revision': t['revision'] = True
    elif change == 'future_result': events[1]['recorded_at'] = '2099-01-01T00:00:00+00:00'
    elif change == 'profile': d['runtime_profile'] = 'unknown'
    elif change == 'question_count': t['issued_count'] = 0
    elif change == 'question_source': events[2]['payload']['original_source_ref'] = 'foreign'
    elif change == 'question_decision': events[2]['payload']['decision']['disposition'] = 'END'
    elif change == 'question_finish': events[-1]['payload']['status'] = 'COMPLETED'
    elif change == 'closed_without_terminal': t['state'] = 'COMPLETED'; d['body_state'] = 'FINAL'
    with pytest.raises(ValueError) as error:
        resolve(s)
    assert str(error.value) in {'PIECE_SOURCE_NOT_ELIGIBLE','PIECE_CONFLICT'}
    assert 'PRIVATE' not in str(error.value)


@pytest.mark.parametrize('tier', ['free','plus','premium'])
def test_q3_current_context_validation_is_reused_without_context_becoming_semantic_source(tier):
    s = snapshot(True,tier,Q3_PROFILE)
    result = run(adapter_type()(store=Store(s)).generate_original_candidate_from_saved_state(AUTH,INPUT))
    assert result['candidate']['piece_text'] == BODY
    assert result['source_lineage']['semantic_source_roles'] == ['original_input']


@pytest.mark.parametrize('change', ['history_removed','feedback_changed','tier_changed','context_failure'])
def test_q3_stale_context_and_context_read_failure_do_not_fall_back_to_original(change):
    s = snapshot(True,'premium',Q3_PROFILE);store=Store(s)
    if change == 'history_removed': s['thread']['data']['context_guards'] = [['private-history',1]]
    elif change == 'feedback_changed': store.live_context['feedback'] = [{'frame_key':'frame','version':2}]
    elif change == 'tier_changed': s['tier'] = 'free'
    else:
        async def fail(*args): raise httpx.ReadTimeout('PRIVATE')
        store.context=fail
    with pytest.raises(ValueError) as error:
        run(adapter_type()(store=store).resolve_original_handoff(AUTH,INPUT))
    assert str(error.value) == ('PIECE_TEMPORARILY_UNAVAILABLE' if change == 'context_failure' else 'PIECE_SOURCE_NOT_ELIGIBLE')


@pytest.mark.parametrize('change', ['revision','source','tier','answer','observation','auth'])
def test_change_during_actual_piece_generation_prevents_return(monkeypatch,change):
    store=Store(snapshot()); actual=MeaningExperienceEngine.generate
    def generate(self,request):
        result=actual(self,request)
        assert result.artifact.piece_text == BODY
        if change == 'revision': store.value['thread']['revision'] += 1
        elif change == 'source': store.value['original']['memo'] += ' '
        elif change == 'tier': store.value['tier'] = 'premium'
        elif change == 'answer': store.value['thread']['latest_answer_event_id'] = INPUT
        elif change == 'observation': store.value['thread']['last_observation_event_id'] = INPUT
        else:
            async def invalid(token): raise HTTPException(401,'PRIVATE')
            monkeypatch.setattr(api_account_visibility,'_resolve_user_id_from_token',invalid)
        return result
    monkeypatch.setattr(MeaningExperienceEngine,'generate',generate)
    with pytest.raises(ValueError) as error:
        run(adapter_type()(store=store).generate_original_candidate_from_saved_state(AUTH,INPUT))
    assert str(error.value) in {'PIECE_CONFLICT','PIECE_SOURCE_NOT_ELIGIBLE','PIECE_AUTH_REQUIRED'}


@pytest.mark.parametrize('kind', ['emotion','incomplete'])
def test_state_admission_does_not_override_existing_cmee_content_refusal(kind):
    s=snapshot()
    if kind == 'emotion': s['original']['emotions']=['平穏']
    else: s['original']['memo_action']='まだ決めて'
    s['thread']['source_snapshot']=copy.deepcopy(s['original'])
    with pytest.raises(ValueError):
        run(adapter_type()(store=Store(s)).generate_original_candidate_from_saved_state(AUTH,INPUT))


@pytest.fixture(scope='module')
def database():
    assert os.environ.get('Q2_PGLITE_MODULE'), 'retained SQL runtime required'
    p=Path(__file__).parents[1]/'test_emlis_q2_application.py'
    spec=importlib.util.spec_from_file_location('piece_state_q2_fixture',p)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    db=module.Database()
    yield db
    db.proc.stdin.close();db.proc.wait(timeout=10)


def seed_sql(database, monkeypatch, *, memo, action='', selected=True):
    db = database
    user, parent = str(uuid4()), str(uuid4())
    assert 'code' not in db.query('insert into auth.users values ($1)', [user])
    assert 'code' not in db.query("insert into public.profiles values ($1,'free')", [user])
    emotions = ['不安'] if selected else []
    details = [{'type': '不安', 'strength': 'medium'}] if selected else []
    assert 'code' not in db.query("insert into public.emotions values ($1,$2,now() at time zone 'UTC',$3,$4,array['仕事'],$5,$6)",
        [parent, user, memo, action, emotions, json.dumps(details, ensure_ascii=False)])
    async def owner(token):
        return user
    monkeypatch.setattr(api_account_visibility, '_resolve_user_id_from_token', owner)
    monkeypatch.setattr(emlis_thread_store, 'sb_post_rpc', db.rpc)
    return user, parent, EmlisThreadService()


@pytest.mark.parametrize('ending', ['open', 'skip', 'stop'])
def test_actual_sql_emlis_result_identifies_pre_question_without_promoting_content(database, monkeypatch, ending):
    adapter_type()
    user, parent, service = seed_sql(database, monkeypatch, memo='褒められたのに、嬉しくなかった。')
    initial = run(service.start(user, parent))
    assert initial['current_observation'] is not None, initial
    assert initial['pending_question'] is not None, initial
    if ending != 'open':
        current = run(service.action(user, initial['thread_id'], action=ending,
            expected_revision=initial['revision'], idempotency_key='piece-state-' + ending,
            question_id=initial['pending_question']['question_id']))
    else:
        current = initial
    before = run(service.store.read(user, input_id=parent))
    adapter = adapter_type()()
    handoff = run(adapter.resolve_original_handoff(AUTH, parent))
    lineage = handoff.lineage_payload()
    assert lineage['observation']['emlis_observation_result_identity'] == initial['current_observation']['event_id']
    assert lineage['observation']['emlis_observation_stage'] == 'pre_question_observation'
    assert lineage['piece_generation_eligibility']['decision'] == 'eligible'
    assert handoff == run(adapter_type()().resolve_original_handoff(AUTH, parent))
    # The real saved result still includes selected emotions. Do not silently
    # drop them to manufacture a successful Piece body.
    with pytest.raises(ValueError) as error:
        run(adapter.generate_original_candidate_from_saved_state(AUTH, parent))
    assert str(error.value) == 'PIECE_CONTENT_UNAVAILABLE:saved_emotion_meaning_not_yet_supported'
    after = run(service.store.read(user, input_id=parent))
    assert before['thread'] == after['thread'] and before['events'] == after['events']
    print('SAVED_STATE_SQL', json.dumps({'ending': ending, 'state': current['state'],
        'original': before['original'], 'lineage': lineage,
        'piece_candidate': None, 'content_status': str(error.value)}, ensure_ascii=False))


@pytest.mark.parametrize('answer_text', ['わからない。', '次も同じ成果を求められるようで、重かった。'])
def test_actual_sql_saved_answer_disallows_original_only_handoff(database, monkeypatch, answer_text):
    adapter_type()
    user, parent, service = seed_sql(database, monkeypatch, memo='褒められたのに、嬉しくなかった。')
    initial = run(service.start(user, parent))
    changed = run(service.answer(user, initial['thread_id'],
        question_id=initial['pending_question']['question_id'], expected_revision=initial['revision'],
        idempotency_key='piece-answer', answer_text=answer_text, authored_at=STAMP))
    assert changed['answer_saved']
    with pytest.raises(mod.PieceContractError, match='PIECE_SOURCE_NOT_ELIGIBLE'):
        run(adapter_type()().resolve_original_handoff(AUTH, parent))
    print('SAVED_STATE_SQL_REFUSAL', json.dumps({'answer': answer_text, 'body_state': changed['body_state']}, ensure_ascii=False))


@pytest.mark.parametrize('memo,action', [(THOUGHT, ACTION), ('私は読書を大切にしています。', '')])
def test_actual_upstream_without_selected_emotions_does_not_invent_a_terminal(database, monkeypatch, memo, action):
    adapter_type()
    from cocolon_meaning_experience_engine.source_kernel import SourceAdmissionError
    user, parent, service = seed_sql(database, monkeypatch, memo=memo, action=action, selected=False)
    with pytest.raises(SourceAdmissionError, match='noncanonical_current_input_source_shape'):
        run(service.start(user, parent))
    with pytest.raises(mod.PieceContractError, match='PIECE_SOURCE_NOT_ELIGIBLE'):
        run(adapter_type()().resolve_original_handoff(AUTH, parent))


def test_no_caller_stage_or_eligibility_parameter():
    adapter = adapter_type()(store=Store(snapshot()))
    with pytest.raises(TypeError):
        adapter.generate_original_candidate_from_saved_state(AUTH, INPUT, source_stage='normal_observation')
    with pytest.raises(TypeError):
        adapter.resolve_original_handoff(AUTH, INPUT, eligible=True)
