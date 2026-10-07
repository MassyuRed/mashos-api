"""Actual bounded PCE-4 review -> B5 issuance on disposable PostgreSQL.

CMEE/B9, source/format/meaning checks, review and SQL are real code. Authentication,
saved-state reads, source records, TTL and renderer identity are synthetic.
These tests do not establish real Auth/PostgREST, HTTP/RN, general safety coverage,
production readiness, or human acceptance. Earlier synthetic-review tests stay.
"""
from __future__ import annotations

import asyncio
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import runpy

import pytest

_B5 = runpy.run_path(str(Path(__file__).with_name('test_b05_generated_preview_issuance.py')))
database = _B5['database']
from piece_v2_contract import PieceContractError, canonical_json_bytes, canonical_sha256_hex
import piece_v2_preview_service as service
import piece_v2_safety_review as review


def _no_author(monkeypatch):
    import cocolon_meaning_experience_engine.engine as engine
    import cocolon_meaning_experience_engine.piece_v1c as piece
    def forbidden(*args, **kwargs):
        raise AssertionError('Review/issuance must not author or regenerate text.')
    monkeypatch.setattr(service, 'generate_piece_candidate', forbidden)
    monkeypatch.setattr(engine.MeaningExperienceEngine, 'generate', forbidden)
    monkeypatch.setattr(piece, 'realize_piece_artifact', forbidden)
    monkeypatch.setattr(piece, 'generate_piece_artifact', forbidden)


def _changed(prepared, *, blocks=None, fmt=None, eligible=None, edit=None):
    value = prepared.artifact_payload()
    payload = value['content_payload']
    if blocks is not None:
        payload['body_blocks'] = blocks
    if fmt is not None:
        payload['format_type'] = value['format_type'] = fmt
    if eligible is not None:
        value['eligible_formats'] = eligible
    value['piece_text'] = '\n\n'.join(payload['body_blocks'])
    value['piece_text_hash'] = sha256(value['piece_text'].encode('utf-8')).hexdigest()
    value['content_payload_hash'] = canonical_sha256_hex(payload)
    if edit is not None:
        edit(value)
    return replace(prepared, _artifact_json=canonical_json_bytes(value))


def _source_changed(prepared, text):
    original = prepared.handoff.original.original_payload()
    original['memo'] = text
    row = _B5['_B6']['_row'](tier=prepared.handoff.original.subscription_tier)
    row['source_lineage']['source_input']['source_recorded_at'] = original['created_at']
    handoff = _B5['_B6']['_handoff'](row,
        tier=prepared.handoff.original.subscription_tier, original=original)
    return replace(prepared, handoff=handoff)


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
@pytest.mark.parametrize('named', [False, True], ids=['ready', 'role-transformed'])
def test_actual_review_issues_same_generated_body_and_replays_without_author(database, monkeypatch, tier, named):
    conn, _, _ = database
    owner, request, prepared, _, state = _B5['_setup'](monkeypatch, tier=tier, named=named)
    original, artifact = prepared.handoff.original._original_json, prepared._artifact_json
    expected = prepared.artifact_payload()
    _no_author(monkeypatch)
    assert asyncio.run(review.review_prepared_original(prepared)) == ('transformed' if named else 'ready')
    rpc = _B5['_native_rpc'](conn, state)
    first = _B5['_issue'](owner, request, prepared, review.review_prepared_original, state, rpc)
    second = _B5['_issue'](owner, request, prepared, review.review_prepared_original, state, rpc)
    assert second == dict(first, idempotency_replayed=True)
    assert first['idempotency_replayed'] is False
    assert first['safety_state'] == ('adjusted' if named else 'ready')
    for key in ('piece_text', 'piece_text_hash', 'content_payload', 'content_payload_hash',
                'format_type', 'eligible_formats', 'visual_recipe', 'visual_recipe_hash'):
        assert first[key] == expected[key]
    assert conn.execute('SELECT piece_text, content_payload, visual_recipe FROM public.piece_records').fetchone() == (
        expected['piece_text'], expected['content_payload'], expected['visual_recipe'])
    assert conn.execute('SELECT count(*) FROM public.piece_records').fetchone() == (1,)
    assert _B5['_B4']['_used'](conn) == 0
    assert prepared.handoff.original._original_json == original
    assert prepared._artifact_json == artifact
    assert 'source_lineage' not in first and 'owner_user_id' not in first


@pytest.mark.parametrize('mutation', ['negation', 'object', 'extra-claim', 'empty', 'uncertainty', 'name', 'role'])
def test_hash_consistent_unfaithful_body_cannot_pass_real_review_or_write(database, monkeypatch, mutation):
    conn, _, _ = database
    named = mutation in {'uncertainty', 'name', 'role'}
    owner, request, prepared, _, state = _B5['_setup'](monkeypatch, named=named)
    _no_author(monkeypatch)
    blocks = prepared.artifact_payload()['content_payload']['body_blocks']
    if mutation == 'negation':
        blocks = [b.replace('大切にしていない', '大切にしている') for b in blocks]
    elif mutation == 'object':
        blocks = [b.replace('一人で落ち着いて考える時間', '誰かに褒められる時間') for b in blocks]
    elif mutation == 'extra-claim':
        blocks[-1] += '私は自分を必ず変えられる。'
    elif mutation == 'empty':
        blocks = []
    elif mutation == 'uncertainty':
        blocks = [b.replace('まだ分からない', '分かっている') for b in blocks]
    elif mutation == 'name':
        blocks = [b.replace('友人', '友人のAliceさん', 1) for b in blocks]
    else:
        blocks = [b.replace('友人', '同僚') for b in blocks]
    altered = _changed(prepared, blocks=blocks)
    assert altered._artifact_json != prepared._artifact_json
    assert asyncio.run(review.review_prepared_original(altered)) == 'ineligible'
    reviewed = []

    async def actual_review(candidate):
        reviewed.append(candidate)
        return await review.review_prepared_original(candidate)

    with pytest.raises(PieceContractError) as error:
        _B5['_issue'](owner, request, altered, actual_review,
                      state, _B5['_native_rpc'](conn, state))
    if mutation == 'empty':
        # Empty body_blocks violates the existing content contract before the
        # service calls its reviewer. Do not weaken that early rejection.
        assert error.value.code == 'PIECE_REQUEST_INVALID'
        assert reviewed == []
    else:
        # Well-shaped, hash-consistent meaning changes must reach the actual
        # reviewer and fail there, not pass via an unrelated transient error.
        assert error.value.code == 'PIECE_SAFETY_UNAVAILABLE'
        assert reviewed == [altered]
    assert not state['posts']
    assert conn.execute('SELECT count(*) FROM public.piece_records').fetchone() == (0,)
    assert _B5['_B4']['_used'](conn) == 0


_RISK = [
    ('私は連絡先test@example.invalidを残したい。', 'ineligible'),
    ('私はｔｅｓｔ＠ｅｘａｍｐｌｅ．ｉｎｖａｌｉｄを残したい。', 'ineligible'),
    ('私はhttps://example.invalidへ案内したい。', 'ineligible'),
    ('私は@private_exampleへ案内したい。', 'ineligible'),
    ('私は090-1234-5678を伝えたい。', 'ineligible'),
    ('私はpassword=synthetic-secretを残したい。', 'ineligible'),
    ('私は勤務先を公開してやりたい。', 'blocked'),
    ('私は相手を殺してやる。', 'blocked'),
    ('友人は詐欺師だ。私は距離を置きたい。', 'ineligible'),
    ('私は\u202e連絡先を残したい。', 'ineligible'),
]


@pytest.mark.parametrize('text,verdict', _RISK)
def test_source_scan_is_not_replaced_by_clean_piece_body(monkeypatch, text, verdict):
    _, _, prepared, _, _ = _B5['_setup'](monkeypatch)
    altered = _source_changed(prepared, text)
    def no_meaning(*args, **kwargs):
        raise AssertionError('Unsafe source must stop before meaning planning.')
    monkeypatch.setattr(review, 'build_piece_source_meaning', no_meaning)
    _no_author(monkeypatch)
    assert altered.artifact_payload() == prepared.artifact_payload()
    assert asyncio.run(review.review_prepared_original(altered)) == verdict


@pytest.mark.parametrize('text,verdict', _RISK)
def test_post_format_scan_is_not_replaced_by_source_scan(monkeypatch, text, verdict):
    _, _, prepared, _, _ = _B5['_setup'](monkeypatch)
    altered = _changed(prepared, blocks=[text])
    def no_meaning_gate(*args, **kwargs):
        raise AssertionError('Unsafe visible text must stop before S7.')
    monkeypatch.setattr(review, 'validate_source_meaning_preservation', no_meaning_gate)
    _no_author(monkeypatch)
    assert altered.handoff == prepared.handoff
    assert asyncio.run(review.review_prepared_original(altered)) == verdict


@pytest.mark.parametrize('mutation', ['duplicate', 'reorder', 'unknown', 'omitted', 'quote-context', 'declaration-context'])
def test_format_offer_and_selected_format_are_source_checked(monkeypatch, mutation):
    named = mutation in {'quote-context', 'declaration-context'}
    _, _, prepared, _, _ = _B5['_setup'](monkeypatch, named=named)
    eligible = prepared.artifact_payload()['eligible_formats']
    if mutation == 'duplicate':
        altered = _changed(prepared, eligible=eligible + eligible[:1])
    elif mutation == 'reorder':
        assert len(eligible) > 1
        altered = _changed(prepared, eligible=list(reversed(eligible)))
    elif mutation == 'unknown':
        altered = _changed(prepared, eligible=eligible + ['unregistered'])
    elif mutation == 'omitted':
        assert len(eligible) > 1
        altered = _changed(prepared, eligible=eligible[:1])
    else:
        fmt = 'quote' if mutation == 'quote-context' else 'declaration'
        altered = _changed(prepared, fmt=fmt, eligible=eligible + [fmt])
    _no_author(monkeypatch)
    assert asyncio.run(review.review_prepared_original(altered)) == 'ineligible'


@pytest.mark.parametrize('mutation', ['payload-hash', 'text-hash', 'language', 'title', 'extra-field', 'contract', 'visibility'])
def test_no_projection_of_unreviewed_content_or_future_contract(monkeypatch, mutation):
    _, _, prepared, _, _ = _B5['_setup'](monkeypatch)
    def edit(value):
        if mutation == 'payload-hash':
            value['content_payload_hash'] = '0' * 64
        elif mutation == 'text-hash':
            value['piece_text_hash'] = '0' * 64
        elif mutation == 'extra-field':
            value['unreviewed_body'] = _B5['PRIVATE']
        elif mutation == 'contract':
            value['piece_contract_version'] = 'unknown'
        elif mutation == 'visibility':
            value['visibility_scope'] = 'public'
        else:
            value['content_payload'][mutation] = 'en' if mutation == 'language' else _B5['PRIVATE']
            value['content_payload_hash'] = canonical_sha256_hex(value['content_payload'])
    _no_author(monkeypatch)
    assert asyncio.run(review.review_prepared_original(_changed(prepared, edit=edit))) == 'ineligible'


@pytest.mark.parametrize('change_at', [1, 2])
def test_real_review_does_not_bypass_existing_current_source_fence(database, monkeypatch, change_at):
    conn, _, _ = database
    owner, request, prepared, _, state = _B5['_setup'](monkeypatch)
    _no_author(monkeypatch)
    state['change_at'] = change_at
    with pytest.raises(PieceContractError) as error:
        _B5['_issue'](owner, request, prepared, review.review_prepared_original,
                      state, _B5['_native_rpc'](conn, state))
    assert error.value.code == 'PIECE_CONFLICT'
    assert not state['posts']
    assert conn.execute('SELECT count(*) FROM public.piece_records').fetchone() == (0,)


@pytest.mark.parametrize('failure', ['unexpected', 'cancel'])
def test_review_failure_is_body_free_and_cancellation_propagates(monkeypatch, failure):
    _, _, prepared, _, _ = _B5['_setup'](monkeypatch)
    def fail(*args, **kwargs):
        if failure == 'cancel':
            raise asyncio.CancelledError()
        raise RuntimeError(_B5['PRIVATE'])
    monkeypatch.setattr(review, 'build_piece_source_meaning', fail)
    with pytest.raises(asyncio.CancelledError if failure == 'cancel' else PieceContractError) as error:
        asyncio.run(review.review_prepared_original(prepared))
    if failure != 'cancel':
        assert error.value.code == 'PIECE_TEMPORARILY_UNAVAILABLE'
        assert _B5['PRIVATE'] not in str(error.value)


@pytest.mark.parametrize('candidate', [None, {}, True, 'ready'])
def test_client_values_are_not_server_prepared_artifacts(candidate):
    assert asyncio.run(review.review_prepared_original(candidate)) == 'ineligible'
