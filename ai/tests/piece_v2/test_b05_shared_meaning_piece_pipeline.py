"""Default Emlis shared meaning -> explicit Piece CMEE profile -> saved work.

Auth and model HTTP prose are fictional; real services and disposable SQL run.
This verifies consumer continuity, not real 4B language quality or live use.
"""
from copy import deepcopy
import json

import httpx
import pytest

import piece_model_source as model
from cocolon_meaning_experience_engine.piece_v1c import MODEL_REALIZATION_PROFILE
from piece_v2_contract import PieceContractError
from piece_v2_source_adapter import PieceSavedSourceAdapter
from test_cmee_piece_request_saved_pipeline import (
    saved_piece_db, _prepare_saved_request, _finish_saved_request,
)
from test_b05_refined_preview_saved_pipeline import refined_pipeline_db, _finish_refined_pipeline
from test_b05_natural_refined_saved_pipeline import (
    natural_refined_db, _prepare_natural, run,
)
from test_b05_piece_answer_update_saved_pipeline import (
    answer_update_db, prepare_answer_update, prepare_later_update,
    MEMO, ACTION, RETAINED, ANSWERS,
)
from test_b05_refined_source_fence_sql import (
    _update, _canonical_lineage, _RECORD, _issue_args, _piece_state, rpc,
)


def configured_piece(monkeypatch, blocks):
    for key, value in dict(PIECE_MODEL_SOURCE=model.CMEE_SELECTOR,
        EMLIS_NATURAL_REPLY_ENDPOINT='https://synthetic-shared.invalid/v1/chat/completions',
        EMLIS_NATURAL_REPLY_MODEL='synthetic-piece-cmee-realization',
        EMLIS_NATURAL_REPLY_API_KEY='synthetic-existing-piece-key-32').items():
        monkeypatch.setenv(key, value)
    seen = []
    def handler(request):
        payload = json.loads(request.content)
        material = json.loads(payload['messages'][1]['content'])
        assert material['control']['realization_profile'] == MODEL_REALIZATION_PROFILE
        # JSON object key order is lexical, while the server partition owns
        # original-before-answer order. Never swap the two source blocks.
        keys = [part['field_path'] + '_' + str(index) for index, part in
                enumerate(material['control']['block_partition'])]
        raw = json.dumps(dict(field_blocks=dict(zip(keys, blocks, strict=True))), ensure_ascii=False)
        seen.append(dict(material=material, raw=raw))
        return httpx.Response(200, json=dict(model=payload['model'], candidate_format='piece.field_slots.v1',
            choices=[dict(finish_reason='stop', message=dict(role='assistant', content=raw))]))
    real = model.Shared4BPieceModelSource
    monkeypatch.setattr(model, 'Shared4BPieceModelSource',
        lambda **kwargs: real(**kwargs, transport=httpx.MockTransport(handler)))
    return seen


def assert_shared_observations(snapshot):
    bodies = [event for event in snapshot['events'] if event['kind'] == 'OBSERVATION']
    assert bodies
    for event in bodies:
        artifact = event['payload']['artifact']
        assert artifact['meaning_profile'] == 'source_grounded_active_meaning.v1'
        material = artifact['analysis_material']
        assert material['source_prefix_ref'] == event['payload']['source_prefix_ref']
        assert material['original_record'] == snapshot['original']
        assert material['graph_scope'] == 'ANALYSIS_SOURCE_GROUNDED_INTERPRETATION'
        assert material['state'] == artifact['analysis_state']
    return bodies


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
def test_default_initial_shared_meaning_reaches_new_piece_profile_and_saved_detail(
        natural_refined_db, monkeypatch, tier):
    db = natural_refined_db
    text = '私は、静かに考える時間を大切にしたい。私は、返事の前にメモを見返したい。'
    seen = configured_piece(monkeypatch, [text])
    record = dict(id='shared-initial-'+tier,
        created_at=db.query('select clock_timestamp()::text as stamp')['rows'][0]['stamp'],
        memo=text, memo_action='', category=['生活'], emotions=['自己理解'],
        emotion_details=[dict(type='自己理解', strength='medium')])
    state = _prepare_saved_request(db, monkeypatch, record, tier=tier)
    assert_shared_observations(state['emlis_snapshot_before'])
    result = _finish_saved_request(db, monkeypatch, state)
    assert result['detail']['piece_text'] == text.replace('私は、返事の前に', '返事の前に')
    assert result['source_unchanged'] and result['emlis_unchanged']
    assert result['quota_consumptions'] == 1 and len(seen) == 1


@pytest.mark.parametrize('operation,rounds,tier', [
    ('ADD', 1, 'premium'), ('ADD', 2, 'free'), ('ADD', 3, 'plus'),
    ('REVISE', 1, 'free'), ('WITHDRAW', 1, 'plus'),
    ('REVISE', 2, 'premium'), ('WITHDRAW', 2, 'free'),
    ('REVISE', 3, 'plus'), ('WITHDRAW', 3, 'premium'),
])
def test_latest_answer_update_uses_shared_meaning_but_only_selected_piece_source(
        answer_update_db, monkeypatch, operation, rounds, tier):
    db = answer_update_db
    if operation == 'ADD':
        state, handoff, _ = _prepare_natural(db, monkeypatch, tier=tier, rounds=rounds,
            case_id=f'shared-add-{rounds}-{tier}')
        blocks = [state['original']['memo'], state['answer_text']]
    elif rounds == 1:
        state = prepare_answer_update(db, monkeypatch, operation, tier=tier)
        blocks = [RETAINED, ACTION] + (['私は家族を守りたい。'] if operation == 'REVISE' else [])
    else:
        state, blocks, _ = prepare_later_update(db, monkeypatch, rounds, operation, tier)
    assert_shared_observations(state['snapshot_before'])
    seen = configured_piece(monkeypatch, blocks)
    result = _finish_refined_pipeline(db, monkeypatch, state,
        visual_change=tier != 'free', expected_blocks=blocks)
    assert result['detail']['piece_text'] == '\n\n'.join(blocks)
    assert result['source_unchanged'] and result['emlis_unchanged']
    assert result['quota_consumptions'] == 1 and len(seen) == 1
    sources = seen[0]['material']['sources']
    assert [source['role'] for source in sources] == ['ORIGINAL_INPUT', 'SUPPLEMENTAL_ANSWER']
    assert '記録を受け取る合成の返事' not in json.dumps(sources, ensure_ascii=False)
    if operation != 'ADD':
        assert '仕事を続けたい' not in json.dumps(sources, ensure_ascii=False)


@pytest.mark.parametrize('context', ['history', 'frame'])
def test_consumed_history_or_frame_context_does_not_become_piece_text(
        natural_refined_db, monkeypatch, context):
    state, handoff, _ = _prepare_natural(natural_refined_db, monkeypatch,
        with_history=context == 'history', with_frame_target=context == 'frame',
        case_id='shared-context-'+context)
    assert_shared_observations(state['snapshot_before'])
    blocks = [state['original']['memo'], state['answer_text']]
    seen = configured_piece(monkeypatch, blocks)
    result = _finish_refined_pipeline(natural_refined_db, monkeypatch, state,
        visual_change=True, expected_blocks=blocks)
    assert result['source_unchanged'] and result['emlis_unchanged']
    assert len(seen) == 1
    assert len(seen[0]['material']['sources']) == 2


@pytest.mark.parametrize('change', ['owner', 'prefix', 'active_text', 'active_range', 'source'])
def test_full_shared_material_rederivation_rejects_even_consistently_echoed_tampering(
        natural_refined_db, monkeypatch, change):
    db = natural_refined_db
    state, _, _ = _prepare_natural(db, monkeypatch, case_id='shared-material-tamper-'+change)
    assert_shared_observations(state['snapshot_before'])
    def alter(material):
        if change == 'owner':
            material['owner_scope'] = '00000000-0000-0000-0000-000000000000'
        elif change == 'prefix':
            material['source_prefix_ref'] = 'src-foreign-material'
        elif change == 'source':
            material['sources'][0]['fields']['memo'] += '私は別の記録を書いた。'
        elif not material['active_fields']:
            # A pending source cannot gain a fabricated active interpretation.
            material['active_fields'].append(dict(text='私は別の記録を書いた。',
                scalar_start=0, scalar_end=12))
        elif change == 'active_text':
            material['active_fields'][0]['text'] += '私は別の記録を書いた。'
        else:
            material['active_fields'][0]['scalar_start'] += 1
    db.query('BEGIN')
    try:
        for event in state['snapshot_before']['events']:
            payload = deepcopy(event['payload'])
            artifact = payload.get('artifact')
            if not isinstance(artifact, dict) or 'analysis_material' not in artifact:
                continue
            material = artifact['analysis_material']
            alter(material)
            _update(db, 'update public.emlis_thread_events set payload=$2::jsonb where id=$1',
                    [event['id'], json.dumps(payload, ensure_ascii=False)])
        data = deepcopy(state['snapshot_before']['thread']['data'])
        alter(data['analysis_material'])
        _update(db, 'update public.emlis_input_threads set data=$2::jsonb where id=$1',
                [state['snapshot_before']['thread']['id'], json.dumps(data, ensure_ascii=False)])
        with pytest.raises(PieceContractError):
            run(PieceSavedSourceAdapter().resolve_refined_handoff('Bearer '+state['token'],
                state['source_id'], supplemental_answer_identity=state['snapshot_before']['thread']['latest_answer_event_id'],
                opted_in=True))
    finally:
        db.query('ROLLBACK')


def test_unread_material_keeps_active_original_without_claiming_piece_meaning(
        natural_refined_db, monkeypatch):
    db = natural_refined_db
    text = 'くるくるした余韻だけが残った。'
    record = dict(id='shared-unread',
        created_at=db.query('select clock_timestamp()::text as stamp')['rows'][0]['stamp'],
        memo=text, memo_action='', category=['生活'], emotions=['自己理解'],
        emotion_details=[dict(type='自己理解', strength='medium')])
    state = _prepare_saved_request(db, monkeypatch, record, tier='premium')
    bodies = assert_shared_observations(state['emlis_snapshot_before'])
    material = bodies[-1]['payload']['artifact']['analysis_material']
    assert material['state'] == 'NOT_GENERATED'
    assert material['coverage']['active_state'] == 'RESOLVED'
    assert [field['text'] for field in material['active_fields']] == [text]
    assert material['source_duties']['claims'] == []
    assert material['coverage']['unassessed_source_ranges']
    # The source-ref read succeeded above. Do not turn that into an assertion
    # that Piece's independent source/meaning grammar has interpreted this text.
    assert state['source_ref']['source_input_id'] == state['source_id']


def test_normal_correction_api_revision_invalidates_prepared_piece_writer(
        natural_refined_db, monkeypatch):
    from emlis_thread_service import EmlisThreadService, Q3_PROFILE
    from cocolon_meaning_experience_engine.natural_reply import NaturalReply
    from test_emlis_interpretation_correction import correct
    db = natural_refined_db
    state, handoff, _ = _prepare_natural(db, monkeypatch, case_id='shared-stale-revision')
    snapshot = state['snapshot_before']
    record = _RECORD()
    record['source_lineage'] = _canonical_lineage(handoff)
    case = dict(owner=state['owner'], record=record,
        expected=dict(original=state['original'], thread_id=snapshot['thread']['id'],
            thread_revision=snapshot['thread']['revision'], lineage=record['source_lineage']))
    args = _issue_args(case)
    async def provider(material):
        return NaturalReply('訂正を受け取る合成の返事です。',
            'synthetic-natural-provider', material.source_prefix_ref)
    service = EmlisThreadService(runtime_profile=Q3_PROFILE, natural_reply_source=provider)
    updated = run(correct(service, state['owner'], state['completed_dto'],
        text='記録を受け取る合成の返事です。',
        explanation='受け取っただけではなく、今は気持ちを整理しています。', key='piece-stale-revision'))
    assert updated['revision'] > snapshot['thread']['revision']
    latest = run(service.store.read(state['owner'], input_id=state['source_id']))
    assert latest['original'] == snapshot['original']
    before = _piece_state(db)
    outcome = rpc(db, 'piece_issue_preview_v2', args)
    assert outcome.get('message') == 'PIECE_CONFLICT', outcome
    assert _piece_state(db) == before


def test_legacy_saved_natural_observation_still_reaches_explicit_new_piece_profile(
        natural_refined_db, monkeypatch):
    from emlis_thread_service import EmlisThreadService
    original_init = EmlisThreadService.__init__
    def legacy(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self.natural_meaning_profile = None
    monkeypatch.setattr(EmlisThreadService, '__init__', legacy)
    state, _, _ = _prepare_natural(natural_refined_db, monkeypatch, case_id='legacy-saved-meaning')
    for event in state['snapshot_before']['events']:
        if event['kind'] == 'OBSERVATION':
            artifact = event['payload']['artifact']
            assert artifact['analysis_state'] == 'NOT_GENERATED'
            assert 'meaning_profile' not in artifact and 'analysis_material' not in artifact
    blocks = [state['original']['memo'], state['answer_text']]
    seen = configured_piece(monkeypatch, blocks)
    result = _finish_refined_pipeline(natural_refined_db, monkeypatch, state,
        visual_change=True, expected_blocks=blocks)
    assert len(seen) == 1 and result['quota_consumptions'] == 1
    assert result['source_unchanged'] and result['emlis_unchanged']
