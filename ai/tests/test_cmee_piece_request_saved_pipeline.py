"""Finite request reuse through existing Piece owners and disposable SQL.

Auth and the preceding Emlis provider are synthetic. Piece's source adapter,
CMEE author, bounded reviewer, preview/save RPCs and owner projection are real.
This does not execute PostgREST, a native renderer, a device or a live database.
"""
import asyncio
from contextlib import ExitStack
import json
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import pytest

from test_emlis_q3_application import Q3Database
from piece_v2_contract import PieceContractError

_ROOT = Path(__file__).parents[2]
_ARTIFACT_FIELDS = (
    'format_type', 'piece_text', 'piece_text_hash', 'content_payload',
    'content_payload_hash', 'visual_recipe', 'visual_recipe_hash', 'renderer_version',
    'piece_contract_version', 'export_contract_version',
    'render_interface_version', 'render_reproducibility_version',
)


@pytest.fixture(scope='module')
def saved_piece_db():
    db = Q3Database()
    try:
        db.migrate()
        legacy = ('id uuid, public_id text, owner_user_id uuid, source_type text, status text, '
                  'is_active bool, question_id int4, q_key text, topic_key text, category text, '
                  'question text, answer text, content_json jsonb, source_snapshot_id uuid, '
                  'source_hash text, source_refs jsonb, locked bool, lock_note text, '
                  'created_at timestamptz, updated_at timestamptz, published_at timestamptz')
        assert 'code' not in db.query('CREATE TABLE public.mymodel_reflections (' + legacy + ')')
        columns = ','.join(column.strip().split()[0] for column in legacy.split(','))
        assert 'code' not in db.query('CREATE VIEW public.pieces WITH (security_invoker=true) AS SELECT '
                                      + columns + ' FROM public.mymodel_reflections')
        assert 'code' not in db.query('REVOKE ALL ON public.pieces FROM PUBLIC,anon,authenticated')
        assert 'code' not in db.query('GRANT SELECT ON public.pieces TO service_role')
        for name in (
            '20260808_001_piece_v2_legacy_read_bridge.sql',
            '20260808_002_piece_v2_foundation.sql',
            '20260808_003_piece_v2_rls_and_staging.sql',
            '20260808_004_piece_v2_atomic_functions.sql',
            '20261010050940_piece_v2_preview_visual_change.sql',
            '20261010_005_piece_v2_quota_read.sql',
            '20261101022630_piece_natural_reply_context.sql',
            '20261103235434_piece_v2_expand_visual_palette.sql',
        ):
            sql = (_ROOT / 'supabase/migrations' / name).read_text()
            db.proc.stdin.write(json.dumps(dict(sql=sql, script=True)) + '\n')
            db.proc.stdin.flush()
            result = json.loads(db.proc.stdout.readline())
            assert 'code' not in result, (name, result)
        yield db
    finally:
        db.proc.stdin.close()
        db.proc.wait(timeout=10)


def _run_saved_request(db, monkeypatch, record, *, tier):
    """One test case, including explicit replay and non-generating owner read."""
    import api_account_visibility
    import emlis_thread_store
    from emlis_thread_service import EmlisThreadService, Q3_PROFILE
    from cocolon_meaning_experience_engine.natural_reply import NaturalReply
    from piece_v2_source_adapter import PieceSavedSourceAdapter
    from piece_v2_preview_service import PiecePreviewService
    from piece_v2_save_service import PieceSaveService
    from piece_v2_owner_service import PieceOwnerService

    owner, source_id = str(uuid4()), str(uuid4())
    token = 'ar04-synthetic-owner'
    counts = {'synthetic_emlis_provider': 0, 'piece_author': 0, 'piece_review': 0,
              'preview_rpc': 0, 'save_rpc': 0}
    assert 'code' not in db.query('INSERT INTO auth.users VALUES ($1)', [owner])
    assert 'code' not in db.query('INSERT INTO public.profiles VALUES ($1,$2)', [owner, tier])
    assert 'code' not in db.query(
        "INSERT INTO public.emotions VALUES ($1,$2,$3::timestamptz AT TIME ZONE 'UTC',$4,$5,$6,$7,$8::jsonb)",
        [source_id, owner, record['created_at'], record['memo'], record['memo_action'],
         record['category'], record['emotions'], json.dumps(record['emotion_details'], ensure_ascii=False)])
    original = db.query('SELECT public.emlis_parent_source(e) AS original FROM public.emotions e WHERE id=$1',
                        [source_id])['rows'][0]['original']
    assert set(original) == set(record)
    assert all(original[k] == record[k] for k in record if k not in ('id', 'created_at'))

    async def verify(value):
        assert value == token
        return owner

    async def preceding_emlis(material):
        counts['synthetic_emlis_provider'] += 1
        return NaturalReply('記録を受け取りました。', 'synthetic-provider', material.source_prefix_ref)

    monkeypatch.setattr(api_account_visibility, '_resolve_user_id_from_token', verify)
    monkeypatch.setattr(emlis_thread_store, 'sb_post_rpc', db.rpc)
    emlis = EmlisThreadService(runtime_profile=Q3_PROFILE, natural_reply_source=preceding_emlis)
    dto = asyncio.run(emlis.start(owner, source_id))
    assert dto['body_state'] == 'FINAL', dto
    emlis_before = db.query('SELECT to_jsonb(t) AS row FROM public.emlis_input_threads t WHERE user_id=$1', [owner])
    events_before = db.query('SELECT to_jsonb(e) AS row FROM public.emlis_thread_events e WHERE thread_id=$1 ORDER BY seq', [dto['thread_id']])
    adapter = PieceSavedSourceAdapter()
    reference = asyncio.run(adapter.resolve_original_source_ref('Bearer ' + token, source_id))
    request = dict(source_ref=reference, requested_format=None,
                   visual_selection=dict(theme_id=None, aspect_ratio=None, branding_mode=None))

    async def load_record(who, pid):
        rows = db.query('SELECT to_jsonb(r) AS row FROM public.piece_records r WHERE owner_user_id=$1 AND id=$2',
                        [who, pid], 'service_role')['rows']
        return rows[0]['row'] if rows else None

    async def load_preview(who, pid):
        from piece_v2_preview_service import _REPLAY_COLUMNS
        row = await load_record(who, pid)
        return {key: row[key] for key in _REPLAY_COLUMNS} if row else None

    async def rpc(name, args):
        assert name in ('piece_issue_preview_v2', 'piece_save_v2')
        counts['preview_rpc' if name == 'piece_issue_preview_v2' else 'save_rpc'] += 1
        params = [json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v for v in args.values()]
        named = ','.join(f'{k} => ${n}' for n, k in enumerate(args, 1))
        result = db.query(f'SELECT public.{name}({named}) AS value', params, 'service_role', error_message=True)
        if 'code' in result:
            raise PieceContractError(result['message'])
        return result['rows'][0]['value']

    async def load_saved(params):
        # The real owner service supplies its own owner/ID/state filters.
        from piece_v2_owner_service import _COLUMNS
        assert set(params) == {'select', 'owner_user_id', 'lifecycle_status', 'id', 'limit'}
        assert params['select'] == ','.join(_COLUMNS)
        assert params['owner_user_id'] == 'eq.' + owner
        assert params['lifecycle_status'] == 'eq.saved'
        assert params['limit'] == '2'
        columns = params['select'].split(',')
        rows = db.query('SELECT to_jsonb(r) AS row FROM public.piece_records r WHERE owner_user_id=$1 AND id=$2 AND lifecycle_status=\'saved\'',
                        [owner, params['id'][3:]], 'service_role')['rows']
        return [{k: r['row'][k] for k in columns} for r in rows]

    import piece_v2_preview_service as preview_module
    import piece_v2_safety_review as review_module
    author, reviewer = preview_module.generate_piece_candidate, review_module.review_prepared_original

    def observed_author(*args, **kwargs):
        counts['piece_author'] += 1
        return author(*args, **kwargs)

    async def observed_review(*args, **kwargs):
        counts['piece_review'] += 1
        return await reviewer(*args, **kwargs)

    monkeypatch.setattr(preview_module, 'generate_piece_candidate', observed_author)
    monkeypatch.setattr(review_module, 'review_prepared_original', observed_review)
    preview = PiecePreviewService(source_adapter=adapter)
    issue = dict(idempotency_key='ar04-preview', ttl_seconds=600,
                 renderer_version='piece.rn_bitmap_renderer.ios.v2',
                 allowed_renderers=('piece.rn_bitmap_renderer.ios.v2',),
                 expected_subscription_tier=tier, load_record=load_preview, rpc=rpc)
    first = asyncio.run(preview.issue_original('Bearer ' + token, request, **issue))
    assert counts['piece_author'] == counts['piece_review'] == counts['preview_rpc'] == 1
    saved_request = dict(preview_id=first['preview_id'], expected_preview_revision=first['preview_revision'],
                         **{k: first[k] for k in ('piece_text_hash', 'content_payload_hash', 'visual_recipe_hash')})

    def forbidden(*args, **kwargs):
        raise AssertionError('Saved Piece replay must not author, compile or review text')

    with ExitStack() as stack:
        for path in (
            'piece_v2_preview_service.generate_piece_candidate',
            'piece_v2_safety_review.review_prepared_original',
            'cocolon_meaning_experience_engine.piece_v1c.compile_piece_artifact_plan',
            'cocolon_meaning_experience_engine.piece_v1c.realize_piece_artifact',
            'cocolon_meaning_experience_engine.engine.MeaningExperienceEngine.generate',
        ):
            stack.enter_context(patch(path, side_effect=forbidden))
        replay = asyncio.run(PiecePreviewService().issue_original('Bearer ' + token, request, **issue))
        assert replay == dict(first, idempotency_replayed=True)
        save = PieceSaveService(load_record=load_record, rpc=rpc)
        kwargs = dict(authenticated_user_id=owner, request=saved_request, idempotency_key='ar04-save',
                      allowed_renderers=('piece.rn_bitmap_renderer.ios.v2',))
        committed = asyncio.run(save.save('Bearer ' + token, **kwargs))
        committed_again = asyncio.run(PieceSaveService(load_record=load_record, rpc=rpc).save('Bearer ' + token, **kwargs))
        assert committed_again == dict(committed, idempotency_replayed=True)
        detail = asyncio.run(PieceOwnerService(load_records=load_saved).detail(
            authenticated_user_id=owner, piece_id=committed['piece_id']))
        assert detail == asyncio.run(PieceOwnerService(load_records=load_saved).detail(
            authenticated_user_id=owner, piece_id=committed['piece_id']))
    row = asyncio.run(load_record(owner, first['preview_id']))
    assert row['lifecycle_status'] == detail['lifecycle_status'] == 'saved'
    assert row['visibility_scope'] == detail['visibility_scope'] == 'private'
    for key in _ARTIFACT_FIELDS:
        assert row[key] == detail[key]
        if key in first:
            assert first[key] == detail[key]
    assert '記録を受け取りました。' not in detail['piece_text']
    assert counts == dict(synthetic_emlis_provider=1, piece_author=1, piece_review=1, preview_rpc=1, save_rpc=2)
    assert db.query('SELECT count(*)::int AS n FROM public.piece_quota_consumptions WHERE owner_user_id=$1', [owner])['rows'][0]['n'] == 1
    assert db.query('SELECT public.emlis_parent_source(e) AS original FROM public.emotions e WHERE id=$1', [source_id])['rows'][0]['original'] == original
    assert emlis_before == db.query('SELECT to_jsonb(t) AS row FROM public.emlis_input_threads t WHERE user_id=$1', [owner])
    assert events_before == db.query('SELECT to_jsonb(e) AS row FROM public.emlis_thread_events e WHERE thread_id=$1 ORDER BY seq', [dto['thread_id']])
    return dict(case_id=record['id'], tier=tier, original=original, source_ref=reference,
                preview=first, replay=replay, save=committed, save_replay=committed_again,
                detail=detail, persisted_row=row, counts=counts,
                source_unchanged=True, emlis_unchanged=True, quota_consumptions=1)


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
@pytest.mark.parametrize('action', [
    '私は司書から展示の設営を頼まれなかった。',
    '私は司書から展示の設営を相談されなかった。',
    '私は司書から展示の設営を伝えられなかった。',
])
def test_finite_request_reaches_saved_artifact_without_second_author(saved_piece_db, monkeypatch, tier, action):
    now = saved_piece_db.query('SELECT now()::text AS stamp')['rows'][0]['stamp']
    record = dict(id='ar04-public-regression', created_at=now,
                  memo='まだ、決めていません。', memo_action=action,
                  category=['仕事', '生活'], emotions=['自己理解'],
                  emotion_details=[dict(type='自己理解', strength='medium')])
    result = _run_saved_request(saved_piece_db, monkeypatch, record, tier=tier)
    assert result['detail']['content_payload']['body_blocks'] == [record['memo'], record['memo_action']]
    assert result['detail']['piece_text'] == record['memo'] + '\n\n' + record['memo_action']
    assert result['detail']['format_type'] == 'short_essay'
