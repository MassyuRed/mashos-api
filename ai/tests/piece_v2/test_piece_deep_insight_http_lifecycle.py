"""Normal ASGI handlers with isolated PostgreSQL and a synthetic model reply."""

import json
from uuid import UUID

import httpx
import pytest
from fastapi.testclient import TestClient

import api_deep_insight
import api_piece_v2
import piece_model_source
import piece_v2_source_adapter
import supabase_client
from cocolon_meaning_experience_engine.piece_semantic_admission import (
    PIECE_FIELD_SLOTS_FORMAT, receive_piece_model_candidate,
)
from cocolon_meaning_experience_engine.piece_v1c import MODEL_MEMO_SELECTION_PROFILE
from cocolon_meaning_experience_engine.preparation_sources import piece_model_field_slots
from piece_v2_runtime_control import create_piece_preview_application
from test_b05_deep_insight_lifecycle import (
    corrected_db, effective_fence_db, mixed_fence_db, natural_refined_db, piece_db,
    recovered_natural_db, refined_pipeline_db, revised_frame_db, saved_piece_db,
)
from test_b05_effective_round_sql_fence import _apply
from test_b05_refined_source_fence_sql import rpc
from test_piece_deep_insight_source_binding import ANSWER, QUESTION, RECORD, selection, value


AUTH = {'Authorization': 'Bearer synthetic-owner'}
PREVIEW = '/emotion/piece/preview'


@pytest.fixture(scope='module')
def linked_db(piece_db):
    _apply(piece_db, '20261128062500_deep_insight_piece_history_links.sql')
    return piece_db


@pytest.fixture
def application(linked_db, selection, monkeypatch):
    owner, _, source, question, _ = selection
    model_calls = []
    server = create_piece_preview_application(
        preview_requested=True, preview_ready=True,
        save_requested=True, save_ready=True, owner_read_requested=True, owner_read_ready=True,
        preview_runtime={'ttl_seconds': 600, 'renderer_version': 'piece.rn_bitmap_renderer.ios.v1'},
    )
    api_deep_insight.register_deep_insight_routes(server)
    server.dependency_overrides[api_deep_insight._owner] = lambda: owner

    async def authenticate(authorization):
        assert authorization == AUTH['Authorization']
        return owner

    async def post_rpc(name, args, **_kwargs):
        if name == 'deep_insight_piece_history_links':
            ids = [str(UUID(item)) for item in args['p_question_ids']]
            body = value(linked_db, 'select public.deep_insight_piece_history_links($1,$2::uuid[]) as v',
                         args['p_owner'], '{' + ','.join(ids) + '}')
        else:
            body = rpc(linked_db, name, args)
        if isinstance(body, dict) and 'code' in body:
            return httpx.Response(400, json=body)
        if body is None:
            return httpx.Response(200, content=b'null', headers={'Content-Type': 'application/json'})
        return httpx.Response(200, json=body)

    async def read_table(path, *, params, **_kwargs):
        assert path == '/rest/v1/piece_records'
        columns = params['select'].split(',')
        assert all(column.replace('_', '').isalnum() for column in columns)
        result = linked_db.query(f"select {','.join(columns)} from public.piece_records where id=$1 and owner_user_id=$2",
                                 [params['id'][3:], params['owner_user_id'][3:]])
        assert 'code' not in result, result
        return httpx.Response(200, json=result['rows'])

    model = object()

    async def call_model(selected, prepared, *, source_request):
        assert selected is model
        assert source_request.source.question_id == question
        assert QUESTION not in prepared.private_json
        slots = piece_model_field_slots(prepared.payload())
        model_calls.append(tuple(slot['literal'] for slot in slots.values()))
        return receive_piece_model_candidate(prepared, raw_output=json.dumps({
            'field_blocks': {key: slot['literal'] for key, slot in slots.items()},
        }, ensure_ascii=False), finish_reason='stop', candidate_format=PIECE_FIELD_SLOTS_FORMAT,
            realization_profile=MODEL_MEMO_SELECTION_PROFILE)

    monkeypatch.setattr(api_piece_v2, '_verify_bearer', authenticate)
    monkeypatch.setattr(piece_v2_source_adapter, '_require_user_id', authenticate)
    monkeypatch.setattr(supabase_client, 'sb_post_rpc', post_rpc)
    monkeypatch.setattr(api_deep_insight, 'sb_post_rpc', post_rpc)
    monkeypatch.setattr(supabase_client, 'sb_get', read_table)
    monkeypatch.setattr(piece_model_source, 'application_piece_model_source', lambda: model)
    monkeypatch.setattr(piece_model_source, 'application_piece_realization_profile', lambda: MODEL_MEMO_SELECTION_PROFILE)
    monkeypatch.setattr(piece_model_source, 'require_current_piece_model_source', lambda selected: None)
    monkeypatch.setattr(piece_model_source, 'call_piece_model_source', call_model)
    return TestClient(server, headers=AUTH), model_calls


def test_selected_answer_survives_piece_issue_edit_save_and_reload(application, selection):
    client, model_calls = application
    _, _, source, question, _ = selection
    history = client.get('/deep-insight')
    assert history.status_code == 200, history.text
    assert [(row['id'], row.get('piece_source_input_id')) for row in history.json()['history']] == [(question, source)]

    url = f'/emotion/piece/source-ref/{source}'
    ref = client.get(url, params={'deep_insight_question_id': question})
    assert ref.status_code == 200, ref.text
    wire = ref.json()
    assert wire == {'source_kind': 'deep_insight_record_answer', 'source_input_id': source,
                    'deep_insight_question_id': question, 'source_commitment': wire['source_commitment']}

    visuals = {'theme_id': 'soft_paper', 'aspect_ratio': '4:5', 'branding_mode': None}
    request = {'source_ref': wire, 'requested_format': None, 'visual_selection': visuals}
    issued = client.post(PREVIEW, headers={'Idempotency-Key': 'selected-piece'}, json=request)
    assert issued.status_code == 200, issued.text
    preview = issued.json()
    assert model_calls == [(RECORD, ANSWER)]
    assert RECORD in preview['piece_text'] and ANSWER in preview['piece_text']
    assert QUESTION not in issued.text and 'source_lineage' not in preview

    visual = client.patch(f"{PREVIEW}/{preview['preview_id']}", json={
        'expected_preview_revision': preview['preview_revision'],
        'visual_selection': visuals | {'aspect_ratio': '9:16'},
    })
    assert visual.status_code == 200, visual.text
    edited = visual.json()
    assert edited['piece_text'] == preview['piece_text'] and edited['preview_revision'] == 2
    saved = client.post('/emotion/piece/save', headers={'Idempotency-Key': 'save-selected-piece'}, json={
        'preview_id': edited['preview_id'], 'expected_preview_revision': edited['preview_revision'],
        **{key: edited[key] for key in ('piece_text_hash', 'content_payload_hash', 'visual_recipe_hash')},
    })
    assert saved.status_code == 200, saved.text
    detail = client.get(f"/emotion/piece/{saved.json()['piece_id']}")
    assert detail.status_code == 200, detail.text
    assert detail.json()['piece_text'] == edited['piece_text']
    assert QUESTION not in detail.text and 'source_lineage' not in detail.json()
    assert model_calls == [(RECORD, ANSWER)]


def test_wrong_or_revoked_selection_does_not_reach_model(application, linked_db, selection):
    client, model_calls = application
    owner, _, source, question, other_record = selection
    wrong = client.get(f'/emotion/piece/source-ref/{other_record}', params={'deep_insight_question_id': question})
    assert wrong.status_code == 404
    source_path = f'/emotion/piece/source-ref/{source}'
    ref = client.get(source_path, params={'deep_insight_question_id': question})
    assert ref.status_code == 200, ref.text
    assert 'code' not in linked_db.query("update public.profiles set subscription_tier='plus' where id=$1", [owner])
    assert client.get(source_path, params={'deep_insight_question_id': question}).status_code == 404
    assert 'piece_source_input_id' not in client.get('/deep-insight').json()['history'][0]
    assert model_calls == []


def test_history_omits_an_answer_that_requires_the_generated_question(application, linked_db, selection):
    client, model_calls = application
    _, _, source, question, _ = selection
    assert 'code' not in linked_db.query(
        'update public.deep_insight_questions set answer_text=$1 where id=$2',
        ['相手が一人の時です。', question],
    )
    assert 'piece_source_input_id' not in client.get('/deep-insight').json()['history'][0]
    result = client.get(f'/emotion/piece/source-ref/{source}', params={'deep_insight_question_id': question})
    assert result.status_code == 422
    assert model_calls == []
