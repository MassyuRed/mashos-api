"""Map correction source qualification, owner API and confirmed-save queue.

SQL target/cohort races have separate PGlite coverage. No real model, remote
account, live database or worker is called here.
"""
import asyncio
import copy
from unittest.mock import AsyncMock
from uuid import UUID

from fastapi import FastAPI, HTTPException
import httpx
import pytest

import analysis_map_correction_service as service
import analysis_cumulative_service as cumulative
import analysis_observed_service as observed
from cocolon_meaning_experience_engine.cores.analysis.map_interpretation_correction import (
    checked_map_correction, map_correction_target_field, qualify_map_correction,
)

OWNER, OTHER = str(UUID(int=1)), str(UUID(int=2))
ARTIFACT = 'artifact:' + UUID(int=10).hex + '@1'


def row():
    return dict(schema_version='cocolon.analysis.map_correction.v1',
        correction_id=str(UUID(int=20)), owner_scope=OWNER,
        recorded_at='2026-11-14T14:00:00+00:00', source_state='ACTIVE',
        target_context=dict(artifact_ref=ARTIFACT, kind='node', ref='n1', field='summary',
            target_text='いつも他人に合わせる', field_text='あなたはいつも他人に合わせる人です。',
            source_guard='analysis-db-cumulative-v1:' + 'a' * 64,
            cohort=[dict(record_ref=str(UUID(int=101)), source_guard='analysis-map-member-v1:' + 'b' * 64),
                    dict(record_ref=str(UUID(int=102)), source_guard='analysis-map-member-v1:' + 'c' * 64)]),
        explanation=dict(source_role='USER_ANALYSIS_MAP_CORRECTION',
            text='今回だけ作業の都合で合わせました。🦉普段の選び方とは違います。'))


def command():
    source = row()
    target = source['target_context']
    return {**{key: target[key] for key in ('artifact_ref', 'kind', 'ref', 'field', 'target_text')},
        'explanation': source['explanation']['text'], 'idempotency_key': 'correction-once'}


def run(value):
    return asyncio.run(value)


def test_explanation_alone_is_a_qualified_source_with_multirecord_control():
    source = qualify_map_correction(OWNER, row())
    assert source.envelope.source_role == 'USER_ANALYSIS_MAP_CORRECTION'
    assert source.envelope.source_record_id == row()['correction_id']
    assert source.envelope.raw_utf8.decode() == row()['explanation']['text']
    assert row()['target_context']['field_text'] not in source.envelope.raw_utf8.decode()
    assert source.cohort_refs == tuple(m['record_ref'] for m in row()['target_context']['cohort'])
    evidence = source.evidence
    assert evidence.field_path == 'explanation'
    assert source.envelope.raw_utf8[evidence.utf8_start:evidence.utf8_end].decode() == source.explanation
    assert evidence.scalar_end == len(source.explanation)
    assert evidence.utf8_end == len(source.explanation.encode())
    assert source.target_context['artifact_ref'] == ARTIFACT
    assert source.target_context['field_text'] == row()['target_context']['field_text']


def test_stale_cannot_qualify_as_current_but_preserves_historical_source_identity():
    current = qualify_map_correction(OWNER, row())
    stale = row(); stale['source_state'] = 'STALE'
    with pytest.raises(ValueError):
        qualify_map_correction(OWNER, stale)
    old = qualify_map_correction(OWNER, stale, allow_stale=True)
    assert old.envelope == current.envelope and old.evidence == current.evidence
    with pytest.raises(ValueError):
        qualify_map_correction(OTHER, row())


@pytest.mark.parametrize('field', ['context.0', 'unknowns.0'])
def test_displayed_array_field_and_unique_substring_bind_without_generated_source(field):
    projection = dict(wire_kind='watashi.map.v3', projection_of=ARTIFACT,
        nodes=[dict(node_ref='n1', context=['その場の条件'], unknowns=['相手の意図は分からない'])])
    expected = projection['nodes'][0][field.split('.')[0]][0]
    assert map_correction_target_field(projection, artifact_ref=ARTIFACT, kind='node',
        reference='n1', field=field, target_text=expected) == expected
    with pytest.raises(ValueError):
        map_correction_target_field(projection, artifact_ref=ARTIFACT, kind='node',
            reference='n1', field=field.replace('.0', '.1'), target_text=expected)


def test_overlapping_or_wrong_field_target_and_duplicate_cohort_are_not_admitted():
    value = row(); value['target_context'].update(field_text='aaaa', target_text='aa')
    with pytest.raises(ValueError):
        checked_map_correction(OWNER, value)
    value = row(); value['target_context']['cohort'].append(copy.deepcopy(value['target_context']['cohort'][0]))
    with pytest.raises(ValueError):
        checked_map_correction(OWNER, value)
    value = row(); value['target_context']['field'] = 'source_id'
    with pytest.raises(ValueError):
        checked_map_correction(OWNER, value)


@pytest.fixture
def environment(monkeypatch):
    monkeypatch.setattr(observed, 'observed_mode', lambda: 'development')
    rpc = AsyncMock(return_value=row())
    queue = AsyncMock(return_value='queued')
    reads = AsyncMock(return_value={'items': []})
    status = AsyncMock(return_value=None)
    monkeypatch.setattr(observed, '_rpc', rpc)
    monkeypatch.setattr(cumulative, 'request_map_refresh', queue)
    monkeypatch.setattr(cumulative, 'read_maps', reads)
    monkeypatch.setattr(cumulative, 'map_refresh_status', status)
    return rpc, queue, reads, status


def test_confirmed_save_uses_existing_queue_and_owner_only_response(environment):
    rpc, queue, reads, status = environment
    result = run(service.submit_map_correction(OWNER, command()))
    assert result['source_state'] == 'ACTIVE' and result['refresh_status'] == 'queued'
    assert result['explanation'] == row()['explanation']['text']
    assert set(result) == {'schema_version', 'correction_id', 'artifact_ref', 'kind', 'ref', 'field',
        'target_text', 'explanation', 'recorded_at', 'source_state', 'refresh_status'}
    assert rpc.call_args.args[0] == 'analysis_map_correction_submit'
    assert rpc.call_args.args[1]['p_user_id'] == OWNER
    queue.assert_awaited_once_with(OWNER, force=True, trigger='manual',
        requested_at=row()['recorded_at'], debounce_seconds=0)


def test_lost_write_ack_is_recovered_by_one_read_not_a_second_write(environment):
    rpc, queue, *_ = environment
    rpc.side_effect = [HTTPException(503, 'unknown write result'), row()]
    result = run(service.submit_map_correction(OWNER, command()))
    assert [call.args[0] for call in rpc.call_args_list] == [
        'analysis_map_correction_submit', 'analysis_map_correction_read']
    assert result['correction_id'] == row()['correction_id'] and result['refresh_status'] == 'queued'
    assert queue.await_count == 1


def test_unknown_write_without_matching_saved_result_stays_unknown(environment):
    rpc, queue, *_ = environment
    rpc.side_effect = [HTTPException(503, 'unknown'), HTTPException(404, 'missing')]
    with pytest.raises(HTTPException) as error:
        run(service.submit_map_correction(OWNER, command()))
    assert error.value.status_code == 503 and queue.await_count == 0
    assert rpc.await_count == 2


def test_same_key_conflict_or_stale_source_does_not_queue(environment):
    rpc, queue, *_ = environment
    changed = row(); changed['explanation']['text'] = '別の本人説明'
    rpc.return_value = changed
    with pytest.raises(HTTPException) as error:
        run(service.submit_map_correction(OWNER, command()))
    assert error.value.status_code == 409 and queue.await_count == 0
    stale = row(); stale['source_state'] = 'STALE'; rpc.return_value = stale
    assert run(service.submit_map_correction(OWNER, command()))['source_state'] == 'STALE'
    assert queue.await_count == 0


def test_queue_failure_preserves_confirmed_source_and_get_is_read_only(environment):
    rpc, queue, *_ = environment
    queue.side_effect = RuntimeError('queue temporarily unavailable')
    saved = run(service.submit_map_correction(OWNER, command()))
    assert saved['correction_id'] == row()['correction_id'] and saved['refresh_status'] == 'failed'
    queue.reset_mock()
    read = run(service.read_map_correction(OWNER, idempotency_key='correction-once'))
    assert read['correction_id'] == saved['correction_id']
    assert queue.await_count == 0


def test_read_only_mode_refuses_new_source_write(environment, monkeypatch):
    rpc, queue, *_ = environment
    monkeypatch.setattr(observed, 'observed_mode', lambda: 'read_only')
    with pytest.raises(HTTPException) as error:
        run(service.submit_map_correction(OWNER, command()))
    assert error.value.status_code == 503 and rpc.await_count == queue.await_count == 0


@pytest.mark.parametrize('explanation', ['違います。', ' なんか違う！ ', '分からない'])
def test_bare_disagreement_keeps_the_same_target_available_without_a_source_write(environment, explanation):
    rpc, queue, *_ = environment
    value = command(); value['explanation'] = explanation
    with pytest.raises(HTTPException) as error:
        run(service.submit_map_correction(OWNER, value))
    assert error.value.status_code == 422
    assert error.value.detail == 'analysis_map_correction_explanation_required'
    assert rpc.await_count == queue.await_count == 0


def test_existing_api_registration_authenticates_and_never_takes_a_body_owner(monkeypatch):
    import api_self_structure as api
    submitted, read = AsyncMock(return_value={'saved': True}), AsyncMock(return_value={'saved': True})
    monkeypatch.setattr(service, 'submit_map_correction', submitted)
    monkeypatch.setattr(service, 'read_map_correction', read)
    resolver = AsyncMock(return_value=OWNER)
    monkeypatch.setattr(api, '_resolve_user_id_from_token', resolver)
    app = FastAPI(); api.register_self_structure_routes(app)
    routes = [route for route in app.routes if route.path == '/self-structure/map-corrections']
    assert len(routes) == 2 and all(route.response_model is dict for route in routes)

    async def scenario():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='https://synthetic') as client:
            assert (await client.post('/self-structure/map-corrections', json=command())).status_code == 401
            headers = {'Authorization': 'Bearer synthetic'}
            assert (await client.post('/self-structure/map-corrections', headers=headers,
                json={**command(), 'owner_scope': OTHER})).status_code == 422
            assert (await client.post('/self-structure/map-corrections', headers=headers,
                json=command())).status_code == 200
            assert (await client.get('/self-structure/map-corrections?idempotency_key=correction-once',
                headers=headers)).status_code == 200
    run(scenario())
    submitted.assert_awaited_once_with(OWNER, command())
    read.assert_awaited_once_with(OWNER, idempotency_key='correction-once')
