"""B5-A original-only retrieval; synthetic sources, no live credentials or DB.

RPC tests reuse the existing Q2 PostgreSQL WASM bridge and actual migration.
Bearer verification is the existing implementation with only the remote token
lookup substituted; this is not a live Supabase authentication claim.
"""
import asyncio
import copy
from dataclasses import FrozenInstanceError
import importlib
import importlib.util
import json
import os
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException
import httpx
import pytest

import api_account_visibility
import emlis_thread_store
from piece_v2_contract import canonical_sha256_hex
from emlis_ai_nls_v3_artifact_contract import artifact_sha256

OWNER = '40000000-0000-4000-8000-000000000001'
OTHER = '40000000-0000-4000-8000-000000000002'
INPUT = '50000000-0000-4000-8000-000000000001'
VERSION = 'emlis.current_input_bundle.v1'
TEXT = '  保存された考え。\r\n結論はまだ出していません。  '
ACTION = '今朝は少し歩いた。'
AUTH = 'Bearer synthetic-owner-session'


def module():
    try:
        return importlib.import_module('piece_v2_source_adapter')
    except ModuleNotFoundError as exc:
        if exc.name != 'piece_v2_source_adapter':
            raise
        pytest.fail('B5-A saved-original adapter is not implemented', pytrace=False)


def run(value):
    return asyncio.run(value)


def source():
    return {'original': {'id': INPUT, 'created_at': '2026-09-26T00:00:00',
            'memo': TEXT, 'memo_action': ACTION, 'category': ['生活'],
            'emotions': ['平穏'], 'emotion_details': [{'type': '平穏', 'strength': 'medium'}]},
            'tier': 'free', 'now': '2026-09-26T01:00:00+00:00',
            'thread': None, 'events': []}


class Store:
    def __init__(self, value=None):
        self.value = source() if value is None else value
        self.calls = []

    async def read(self, user_id, *, input_id=None):
        self.calls.append((user_id, input_id))
        return self.value

    async def commit(self, *args, **kwargs):
        pytest.fail('original retrieval must not write')


@pytest.fixture(autouse=True)
def verified_remote_token_lookup(monkeypatch):
    async def resolve_token(token):
        if token != 'synthetic-owner-session':
            raise HTTPException(401, 'private authentication diagnostic')
        return OWNER
    monkeypatch.setattr(api_account_visibility, '_resolve_user_id_from_token', resolve_token)


def load(store=None, **kwargs):
    return module().PieceSavedSourceAdapter(store=store or Store()).resolve_original(
        AUTH, INPUT, **kwargs)


def error(awaitable, code):
    with pytest.raises(ValueError) as caught:
        run(awaitable)
    assert str(caught.value) == code
    assert TEXT not in str(caught.value) and 'synthetic-owner-session' not in str(caught.value)


def test_verified_owner_saved_id_and_all_original_fields_are_preserved():
    store = Store()
    result = run(load(store))
    assert store.calls == [(OWNER, INPUT)]
    assert result.authenticated_owner_id == OWNER and result.saved_input_id == INPUT
    assert result.original_payload() == source()['original']
    assert result.source_input_version == VERSION and result.subscription_tier == 'free'
    assert result.original_payload()['memo_action'] == ACTION
    assert result.original_payload()['memo'] == TEXT
    assert result.input_bundle_payload()['memo'] == TEXT.strip()
    assert result.input_bundle_commitment == 'sha256:' + artifact_sha256(result.input_bundle_payload())
    assert result.record_commitment == 'sha256:' + canonical_sha256_hex(source()['original'])


def test_private_original_and_bundle_copies_cannot_mutate_frozen_revision():
    store = Store()
    result = run(load(store))
    record, bundle = result.original_payload(), result.input_bundle_payload()
    record['emotion_details'][0]['strength'] = 'strong'
    bundle['category'].append('仕事')
    store.value['original']['memo'] = 'later change'
    assert result.original_payload() == source()['original']
    assert result.input_bundle_payload()['category'] == ['生活']
    with pytest.raises(FrozenInstanceError):
        result.record_commitment = 'replacement'
    assert TEXT.strip() not in repr(result) and OWNER not in repr(result)
    assert not hasattr(result, 'piece_text') and not hasattr(result, 'piece_generation_eligibility')
    assert not hasattr(result, 'as_body_free')


@pytest.mark.parametrize('stage', ['AWAITING_ANSWER', 'REFINING', 'COMPLETED', 'RESPONSE_FAILED'])
def test_original_partition_never_promotes_an_observation_stage_or_answer(stage):
    value = source()
    value.update(thread={'user_id': OWNER, 'original_emotion_id': INPUT, 'state': stage,
                         'data': {'body': 'PRIVATE_OBSERVATION_DO_NOT_COPY'}},
                 events=[{'kind': 'ANSWER', 'payload': {'text': 'SUPPLEMENTAL_NOT_ORIGINAL'}},
                         {'kind': 'OBSERVATION', 'payload': {'text': 'PRIVATE_OBSERVATION_DO_NOT_COPY'}}])
    result = run(load(Store(value)))
    assert result.original_payload() == source()['original']
    assert not hasattr(result, 'source_stage')
    assert all(marker not in result._original_json.decode() + result._bundle_json.decode()
               for marker in ('SUPPLEMENTAL_NOT_ORIGINAL', 'PRIVATE_OBSERVATION_DO_NOT_COPY'))


@pytest.mark.parametrize('authorization', [None, '', 'Bearer rejected-token'])
def test_rejected_authentication_cannot_read_storage(authorization):
    m, store = module(), Store()
    error(m.PieceSavedSourceAdapter(store=store).resolve_original(authorization, INPUT), 'PIECE_AUTH_REQUIRED')
    assert store.calls == []


@pytest.mark.parametrize('input_id', ['invalid-id', None, 'x,or(user_id.eq.other)'])
def test_invalid_saved_identity_is_not_a_query(input_id):
    m, store = module(), Store()
    error(m.PieceSavedSourceAdapter(store=store).resolve_original(AUTH, input_id), 'PIECE_REQUEST_INVALID')
    assert store.calls == []


@pytest.mark.parametrize('version', ['other-version', None, 1])
def test_bundle_schema_mismatch_does_not_read_or_generate(version):
    store = Store()
    error(load(store, source_input_version=version), 'PIECE_SOURCE_NOT_ELIGIBLE')
    assert store.calls == []


@pytest.mark.parametrize('value', ['', 'sha256:bad', 'sha256:' + 'A' * 64, 1])
def test_malformed_expected_revision_is_not_ignored(value):
    store = Store()
    error(load(store, expected_record_commitment=value), 'PIECE_REQUEST_INVALID')
    assert store.calls == []


@pytest.mark.parametrize('change', [
    {'memo': '変更された考え。'}, {'memo_action': '変更された行動。'},
    {'emotions': ['不安']}, {'emotion_details': [{'type': '平穏', 'strength': 'strong'}]},
    {'category': ['仕事']}, {'created_at': '2026-09-25T23:59:00'},
])
def test_every_saved_source_field_is_part_of_the_exact_revision(change):
    m, store = module(), Store()
    adapter = m.PieceSavedSourceAdapter(store=store)
    old = run(adapter.resolve_original(AUTH, INPUT))
    store.value['original'].update(change)
    error(adapter.revalidate_original(AUTH, old), 'PIECE_CONFLICT')


def test_whitespace_change_is_stale_even_when_normalized_bundle_is_equal():
    m, store = module(), Store()
    adapter = m.PieceSavedSourceAdapter(store=store)
    old = run(adapter.resolve_original(AUTH, INPUT))
    store.value['original']['memo'] = TEXT.strip()
    current = run(adapter.resolve_original(AUTH, INPUT))
    assert old.input_bundle_commitment == current.input_bundle_commitment
    assert old.record_commitment != current.record_commitment
    error(adapter.revalidate_original(AUTH, old), 'PIECE_CONFLICT')


def test_expected_normalized_bundle_commitment_and_exact_revision_are_distinct():
    result = run(load())
    assert run(load(expected_record_commitment=result.record_commitment,
                    expected_input_bundle_commitment=result.input_bundle_commitment)) == result
    error(load(expected_input_bundle_commitment='sha256:' + '0' * 64), 'PIECE_CONFLICT')


@pytest.mark.parametrize('change,code', [
    ({'original': None}, 'PIECE_SOURCE_NOT_FOUND'),
    ({'tier': 'enterprise'}, 'PIECE_TEMPORARILY_UNAVAILABLE'),
    ({'now': None}, 'PIECE_TEMPORARILY_UNAVAILABLE'),
    ({'now': 'bad-clock'}, 'PIECE_TEMPORARILY_UNAVAILABLE'),
    ({'thread': {'user_id': OTHER, 'original_emotion_id': INPUT}}, 'PIECE_SOURCE_NOT_FOUND'),
])
def test_invalid_backend_envelope_does_not_gain_source_authority(change, code):
    value = source(); value.update(change)
    error(load(Store(value)), code)


@pytest.mark.parametrize('change', [
    {'memo': {'text': 'not scalar'}}, {'emotions': 'not array'},
    {'emotion_details': [{'type': '平穏', 'hidden_body': 'must not enter'}]},
    {'created_at': 'invalid-time'}, {'memo': '\ud800'},
    {'emlis_body': 'must not enter'},
])
def test_unmapped_or_malformed_original_columns_are_not_silently_dropped(change):
    value = source(); value['original'].update(change)
    error(load(Store(value)), 'PIECE_TEMPORARILY_UNAVAILABLE')


def test_wrong_saved_id_missing_field_and_expired_original_are_rejected():
    value = source(); value['original']['id'] = OTHER
    error(load(Store(value)), 'PIECE_SOURCE_NOT_FOUND')
    value = source(); del value['original']['memo_action']
    error(load(Store(value)), 'PIECE_TEMPORARILY_UNAVAILABLE')
    value = source(); value['original']['created_at'] = '2024-01-01T00:00:00'
    error(load(Store(value)), 'PIECE_SOURCE_NOT_FOUND')


def test_null_original_columns_are_preserved_not_rewritten_in_the_raw_snapshot():
    value = source()
    for key in ('memo', 'memo_action', 'category', 'emotions', 'emotion_details'):
        value['original'][key] = None
    assert run(load(Store(value))).original_payload() == value['original']


@pytest.mark.parametrize('status,code', [(404, 'PIECE_SOURCE_NOT_FOUND'),
                                       (409, 'PIECE_TEMPORARILY_UNAVAILABLE'),
                                       (503, 'PIECE_TEMPORARILY_UNAVAILABLE')])
def test_storage_failure_does_not_return_a_cached_source(status, code):
    m = module()
    class Failed(Store):
        async def read(self, *args, **kwargs):
            raise emlis_thread_store.ThreadStoreError('private diagnostic ' + TEXT, status)
    error(m.PieceSavedSourceAdapter(store=Failed()).resolve_original(AUTH, INPUT), code)


def test_transport_failure_and_changed_tier_require_new_resolution():
    m, store = module(), Store()
    adapter = m.PieceSavedSourceAdapter(store=store)
    old = run(adapter.resolve_original(AUTH, INPUT))
    store.value['tier'] = 'premium'
    error(adapter.revalidate_original(AUTH, old), 'PIECE_CONFLICT')
    class Failed(Store):
        async def read(self, *args, **kwargs):
            raise httpx.ReadTimeout(TEXT)
    error(load(Failed()), 'PIECE_TEMPORARILY_UNAVAILABLE')


@pytest.fixture(scope='module')
def database():
    # Reuse an existing test fixture and runner; never create a second SQL schema.
    assert os.environ.get('Q2_PGLITE_MODULE'), 'fixed PostgreSQL WASM runtime required'
    path = Path(__file__).parents[1] / 'test_emlis_q2_application.py'
    spec = importlib.util.spec_from_file_location('piece_existing_q2_fixture', path)
    existing = importlib.util.module_from_spec(spec); spec.loader.exec_module(existing)
    db = existing.Database()
    yield db
    db.proc.stdin.close(); db.proc.wait(timeout=10)


@pytest.fixture
def persisted(database, monkeypatch):
    owner, input_id = str(uuid4()), str(uuid4())
    assert 'code' not in database.query('insert into auth.users values ($1)', [owner])
    assert 'code' not in database.query("insert into public.profiles values ($1,'free')", [owner])
    assert 'code' not in database.query(
        "insert into public.emotions values ($1,$2,now() at time zone 'UTC',$3,$4,array['生活'],array['平穏'],$5)",
        [input_id, owner, TEXT, ACTION, json.dumps([{'type':'平穏','strength':'medium'}], ensure_ascii=False)])
    async def lookup(token):
        if token != 'synthetic-owner-session':
            raise HTTPException(401, 'not authenticated')
        return owner
    monkeypatch.setattr(api_account_visibility, '_resolve_user_id_from_token', lookup)
    monkeypatch.setattr(emlis_thread_store, 'sb_post_rpc', database.rpc)
    return database, owner, input_id


def test_actual_existing_rpc_reads_original_without_creating_an_emlis_thread(persisted):
    m = module(); db, owner, input_id = persisted
    adapter = m.PieceSavedSourceAdapter()
    result = run(adapter.resolve_original(AUTH, input_id))
    assert result.authenticated_owner_id == owner and result.original_payload()['memo'] == TEXT
    assert result.original_payload()['memo_action'] == ACTION
    assert run(adapter.revalidate_original(AUTH, result)).record_commitment == result.record_commitment
    for table in ('emlis_input_threads', 'emlis_thread_events'):
        assert db.query(f'select count(*)::int as n from public.{table}')['rows'][0]['n'] == 0


@pytest.mark.parametrize('change', ['foreign', 'deleted', 'retention', 'account_deleted'])
def test_actual_sql_denies_foreign_deleted_expired_and_removed_account(persisted, monkeypatch, change):
    m = module(); db, owner, input_id = persisted
    adapter = m.PieceSavedSourceAdapter()
    old = run(adapter.resolve_original(AUTH, input_id))
    if change == 'foreign':
        async def other(token): return OTHER
        monkeypatch.setattr(api_account_visibility, '_resolve_user_id_from_token', other)
    elif change == 'deleted':
        assert 'code' not in db.query('delete from public.emotions where id=$1', [input_id])
    elif change == 'account_deleted':
        assert 'code' not in db.query('delete from auth.users where id=$1', [owner])
    else:
        assert 'code' not in db.query("update public.emotions set created_at=timestamp '2024-01-01' where id=$1", [input_id])
    error(adapter.revalidate_original(AUTH, old), 'PIECE_SOURCE_NOT_FOUND')


@pytest.mark.parametrize('change', ['memo', 'memo_action', 'category', 'emotions', 'emotion_details', 'tier'])
def test_actual_sql_change_invalidates_an_earlier_resolution(persisted, change):
    m = module(); db, owner, input_id = persisted
    adapter = m.PieceSavedSourceAdapter()
    old = run(adapter.resolve_original(AUTH, input_id))
    sql = {
        'memo': "update public.emotions set memo='changed thought' where id=$1",
        'memo_action': "update public.emotions set memo_action='changed action' where id=$1",
        'category': "update public.emotions set category=array['仕事'] where id=$1",
        'emotions': "update public.emotions set emotions=array['不安'] where id=$1",
        'emotion_details': "update public.emotions set emotion_details='[{\"type\":\"平穏\",\"strength\":\"strong\"}]'::jsonb where id=$1",
        'tier': "update public.profiles set subscription_tier='premium' where id=$1",
    }[change]
    assert 'code' not in db.query(sql, [owner if change == 'tier' else input_id])
    error(adapter.revalidate_original(AUTH, old), 'PIECE_CONFLICT')


def test_actual_sql_read_rpc_is_not_callable_by_untrusted_database_roles(persisted):
    module(); db, owner, input_id = persisted
    for role in ('anon', 'authenticated'):
        result = db.query('select public.emlis_thread_read($1,$2,null)', [owner, input_id], role)
        assert result['code'] == '42501'


@pytest.mark.parametrize('authorization', [1, {'token': 'not a header'}])
def test_nontext_authorization_is_rejected_before_storage(authorization):
    m, store = module(), Store()
    error(m.PieceSavedSourceAdapter(store=store).resolve_original(authorization, INPUT), 'PIECE_AUTH_REQUIRED')
    assert not store.calls


def test_authentication_transport_and_decode_errors_are_body_free(monkeypatch):
    m, store = module(), Store()
    for exc in (httpx.ReadTimeout(TEXT), ValueError(TEXT), HTTPException(503, TEXT)):
        async def fail(token): raise exc
        monkeypatch.setattr(api_account_visibility, '_resolve_user_id_from_token', fail)
        error(m.PieceSavedSourceAdapter(store=store).resolve_original(AUTH, INPUT), 'PIECE_TEMPORARILY_UNAVAILABLE')
    assert not store.calls


def test_backend_configuration_http_error_does_not_escape_as_a_source_detail():
    m = module()
    class Failed(Store):
        async def read(self, *args, **kwargs): raise HTTPException(503, TEXT)
    error(m.PieceSavedSourceAdapter(store=Failed()).resolve_original(AUTH, INPUT), 'PIECE_TEMPORARILY_UNAVAILABLE')


def test_revalidation_does_not_accept_a_caller_replacement_object():
    m = module()
    error(m.PieceSavedSourceAdapter().revalidate_original(AUTH, {'owner': OWNER}), 'PIECE_REQUEST_INVALID')


def test_source_adapter_has_no_runtime_or_legacy_route_registration():
    m = module()
    root = Path(m.__file__).parents[3]
    app_text = (root / 'ai/services/ai_inference/app.py').read_text()
    old_api = (root / 'ai/services/ai_inference/api_emotion_piece.py').read_text()
    assert 'piece_v2_source_adapter' not in app_text + old_api
    assert not hasattr(m, 'register_routes') and not hasattr(m, 'generate_piece_candidate')


@pytest.mark.parametrize('memo', [TEXT, 'か\u3099を含む保存原文。\r\nまだ決めていません。'])
def test_bundle_identity_matches_the_current_saved_original_request_owner(memo):
    module()
    from emlis_thread_service import _request, RUNTIME_PROFILE
    snapshot = source(); snapshot['original']['memo'] = memo
    snapshot['thread'] = {'id': INPUT, 'issued_count': 0, 'data': {'runtime_profile': RUNTIME_PROFILE}}
    expected = _request(snapshot).current_input_bundle.to_current_input_payload()
    snapshot['thread'].update(user_id=OWNER, original_emotion_id=INPUT)
    result = run(load(Store(snapshot)))
    assert result.input_bundle_payload() == expected
    assert result.input_bundle_commitment == 'sha256:' + artifact_sha256(expected)
    assert result.original_payload()['memo'] == memo
    assert result.original_payload()['created_at'] == snapshot['original']['created_at']
