"""Real saved adapters/CMEE/reviewer with synthetic auth and stored control.

No SQL, native drawing, live account or deployed configuration is exercised.
The persisted SQL round trip is covered by the separate refined pipeline test.
"""
import asyncio
import copy
from dataclasses import replace
import hashlib

import httpx
import pytest
from fastapi import FastAPI

import api_account_visibility
import api_piece_v2
import piece_v2_source_adapter as adapters
import piece_v2_source_ref_http as source_http
import piece_v2_preview_service as preview
import piece_v2_safety_review as safety
from piece_v2_contract import canonical_json_bytes, canonical_sha256_hex, PieceContractError
import test_b05a_piece_refined_source_handoff as saved_fixture


def setup_saved(monkeypatch, *, tier='free', answer='私は嬉しかった。'):
    async def verify(token):
        assert token == 'refined-synthetic-session'
        return saved_fixture.OWNER
    monkeypatch.setattr(api_account_visibility, '_resolve_user_id_from_token', verify)
    monkeypatch.setattr(saved_fixture, 'ANSWER_TEXT', answer)
    value = saved_fixture.snapshot(saved_fixture.Q3_PROFILE, tier)
    store = saved_fixture.Store(value)
    adapter = adapters.PieceSavedSourceAdapter(store=store)
    refs = asyncio.run(adapter.resolve_refined_source_ref(saved_fixture.AUTH, saved_fixture.INPUT,
        supplemental_answer_identity=saved_fixture.ANSWER, opted_in=True))
    request = dict(source_ref=refs, requested_format=None,
                   visual_selection=dict(theme_id=None, aspect_ratio=None, branding_mode=None))
    return preview.PiecePreviewService(source_adapter=adapter), adapter, store, value, request


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
def test_selected_refined_prepare_and_author_free_review(monkeypatch, tier):
    service, adapter, store, value, request = setup_saved(monkeypatch, tier=tier)
    before = copy.deepcopy(value)
    prepared = asyncio.run(service.prepare_original(saved_fixture.AUTH, request))
    artifact = prepared.artifact_payload()
    assert artifact['piece_text'] == saved_fixture.ORIGINAL_TEXT + '\n\n私は嬉しかった。'
    assert artifact['eligible_formats'] == ['short_essay']
    assert artifact['visibility_scope'] == 'private'
    assert len(request['source_ref']) == 7
    line = preview._canonical_handoff_lineage(prepared.handoff)
    assert len(line) == 8 and len(line['source_input']) == 5 and len(line['observation']) == 7
    assert line['observation']['supplemental_answer_bundle_commitment'].startswith('sha256:')
    assert 'PRIVATE EMLIS BODY' not in artifact['piece_text']
    seen = []
    scan = safety._scan
    def observed(text):
        seen.append(text)
        return scan(text)
    def forbidden(*args, **kw):
        pytest.fail('review or visual change generated text')
    monkeypatch.setattr(safety, '_scan', observed)
    monkeypatch.setattr(preview, 'generate_piece_candidate', forbidden)
    monkeypatch.setattr('cocolon_meaning_experience_engine.piece_v1c.realize_piece_artifact', forbidden)
    assert asyncio.run(safety.review_prepared_original(prepared)) == 'ready'
    assert seen == [saved_fixture.ORIGINAL_TEXT, '私は嬉しかった。', artifact['piece_text']]
    changed = asyncio.run(service.prepare_visual_change(saved_fixture.AUTH, prepared,
        dict(theme_id='quiet_night', aspect_ratio=None, branding_mode=None)))
    after = changed.artifact_payload()
    for key in ('piece_text', 'piece_text_hash', 'content_payload', 'content_payload_hash'):
        assert after[key] == artifact[key]
    assert after['visual_recipe']['theme']['theme_id'] == 'quiet_night'
    assert value == before


@pytest.mark.parametrize('field,value', [
    ('supplemental_answer_identity', None), ('question_need_decision_identity', None),
    ('emlis_observation_stage', 'normal_observation'),
    ('source_input_bundle_commitment', 'sha256:' + '0' * 64),
    ('supplemental_answer_identity', '90000000-0000-4000-8000-000000000099'),
])
def test_selected_refined_reference_cannot_drop_or_substitute_source(monkeypatch, field, value):
    service, _, _, _, request = setup_saved(monkeypatch)
    request['source_ref'][field] = value
    with pytest.raises(PieceContractError):
        asyncio.run(service.prepare_original(saved_fixture.AUTH, request))


def test_rehashed_substitute_body_is_not_safety_ready(monkeypatch):
    service, _, _, _, request = setup_saved(monkeypatch)
    prepared = asyncio.run(service.prepare_original(saved_fixture.AUTH, request))
    artifact = prepared.artifact_payload()
    artifact['piece_text'] = artifact['piece_text'].replace('嬉しかった', '嬉しくなかった')
    artifact['content_payload']['body_blocks'][-1] = '私は嬉しくなかった。'
    artifact['piece_text_hash'] = hashlib.sha256(artifact['piece_text'].encode()).hexdigest()
    artifact['content_payload_hash'] = canonical_sha256_hex(artifact['content_payload'])
    forged = replace(prepared, _artifact_json=canonical_json_bytes(artifact))
    assert asyncio.run(safety.review_prepared_original(forged)) == 'ineligible'


def test_answer_change_after_generation_cannot_issue_prepared_source(monkeypatch):
    service, adapter, store, _, request = setup_saved(monkeypatch)
    original = adapter.revalidate_refined_handoff
    async def changed(authorization, previous, *, opted_in):
        answer = next(e for e in store.value['events'] if e['kind'] == 'ANSWER')
        answer['payload']['source']['answer_text_private'] = '私は嬉しくなかった。'
        return await original(authorization, previous, opted_in=opted_in)
    monkeypatch.setattr(adapter, 'revalidate_refined_handoff', changed)
    with pytest.raises(PieceContractError):
        asyncio.run(service.prepare_original(saved_fixture.AUTH, request))


@pytest.fixture
def http_saved(monkeypatch):
    _, adapter, _, _, request = setup_saved(monkeypatch)
    async def verify(authorization):
        assert authorization == saved_fixture.AUTH
        return saved_fixture.OWNER
    monkeypatch.setattr(api_piece_v2, '_verify_bearer', verify)
    monkeypatch.setattr(adapters, 'PieceSavedSourceAdapter', lambda: adapter)
    app = FastAPI()
    app.state.piece_v2_runtime = dict(requested=dict(piece_v2_preview_enabled=True),
                                    ready=dict(piece_v2_preview_enabled=True))
    app.include_router(source_http.source_ref_router)
    async def send(query=''):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://test') as c:
            return await c.get('/emotion/piece/source-ref/' + saved_fixture.INPUT + query,
                               headers={'Authorization': saved_fixture.AUTH})
    return lambda query='': asyncio.run(send(query)), request


def test_http_explicit_exact_answer_returns_only_existing_seven_fields(http_saved):
    send, request = http_saved
    response = send('?supplemental_answer_identity=' + saved_fixture.ANSWER)
    assert response.status_code == 200 and response.json() == request['source_ref']
    assert response.headers['cache-control'] == 'no-store'
    assert len(response.json()) == 7
    assert not any(key in response.text for key in ('answer_text_private', 'source_owner_user_id',
        'supplemental_answer_bundle_commitment', 'PRIVATE EMLIS'))


def test_http_omitted_answer_does_not_select_latest_refinement(http_saved):
    send, _ = http_saved
    assert send().status_code == 422


@pytest.mark.parametrize('query', [
    '?supplemental_answer_identity=bad',
    '?supplemental_answer_identity=00000000-0000-0000-0000-000000000000',
    '?supplemental_answer_identity=' + saved_fixture.ANSWER + '&opted_in=true',
    '?supplemental_answer_identity=' + saved_fixture.ANSWER + '&supplemental_answer_identity=' + saved_fixture.ANSWER,
    '?stage=refined_observation',
])
def test_http_does_not_accept_ambiguous_or_implicit_answer_selection(http_saved, query):
    send, _ = http_saved
    response = send(query)
    assert response.status_code == 400 and response.json() == {'code': 'PIECE_REQUEST_INVALID'}
