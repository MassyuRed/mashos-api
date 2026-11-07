"""Legacy report source integrity, using synthetic rows and HTTP transport only.

These tests cover transport/aggregation/provenance, not natural-language quality
or current cumulative-map behavior. No Supabase service or personal data is used.
"""
import asyncio
from copy import deepcopy
from datetime import datetime, timezone
import json

import httpx
import pytest

import api_analysis_reports as reports
import supabase_client


EMOTIONS = ['喜び', '悲しみ', '怒り', '不安', '平穏']


def _transport(monkeypatch, handler):
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    monkeypatch.setattr(supabase_client, '_client', client)
    monkeypatch.setattr(supabase_client, 'SUPABASE_URL', 'https://synthetic-analysis.invalid')
    monkeypatch.setattr(supabase_client, 'ensure_supabase_config', lambda: None)
    monkeypatch.setattr(reports, '_sb_headers', lambda **kwargs: {'Authorization': 'Bearer synthetic-test'})
    return client


def test_ready_transport_keeps_both_retention_timestamp_constraints(monkeypatch):
    captured = []

    def handler(request):
        captured.append(request)
        return httpx.Response(200, json=[])

    async def run():
        async with _transport(monkeypatch, handler):
            await reports._fetch_myweb_ready_full_candidate_chunk('synthetic-owner', 'weekly',
                retention={'gte_iso': '2026-10-01T00:00:00Z', 'lt_iso': '2026-11-01T00:00:00Z'},
                raw_page_size=4, raw_offset=0)

    asyncio.run(run())
    assert captured[0].url.params.get_list('period_end') == [
        'gte.2026-10-01T00:00:00Z', 'lt.2026-11-01T00:00:00Z']
    assert captured[0].url.params['user_id'] == 'eq.synthetic-owner'


@pytest.mark.parametrize('status,payload,expected', [
    (200, [{'source_hash': 'a' * 64}], 'a' * 64),
    (206, [{'source_hash': 'b' * 64}], 'b' * 64),
    (200, [], None),
    (404, {'code': 'missing'}, None),
])
def test_latest_snapshot_hash_is_read_from_successful_http_response(monkeypatch, status, payload, expected):
    captured = []

    def handler(request):
        captured.append(request)
        return httpx.Response(status, json=payload)

    async def run():
        async with _transport(monkeypatch, handler):
            return await reports._fetch_latest_snapshot_hash('synthetic-owner',
                scope='global', snapshot_type='public')

    assert asyncio.run(run()) == expected
    assert captured[0].url.params['user_id'] == 'eq.synthetic-owner'
    assert captured[0].url.params['snapshot_type'] == 'eq.public'


@pytest.mark.parametrize('kind', EMOTIONS)
def test_legacy_empty_details_remains_renderable_with_the_selected_emotion(kind):
    row = {'emotions': [kind], 'emotion_details': []}
    assert reports._has_renderable_emotion_content(row)
    metrics = reports._build_daily_metrics([row])
    assert metrics['totals'][reports.JP_TO_KEY[kind]] == 2
    assert metrics['totalAll'] == 2
    assert row == {'emotions': [kind], 'emotion_details': []}


@pytest.mark.parametrize('strength,score', [('weak', 1), ('medium', 2), ('strong', 3)])
def test_nonempty_details_keeps_all_five_selected_emotions_and_their_strengths(strength, score):
    row = {'emotions': EMOTIONS,
        'emotion_details': [{'type': kind, 'strength': strength} for kind in EMOTIONS]}
    before = deepcopy(row)
    assert reports._build_daily_metrics([row])['totals'] == dict.fromkeys(reports.EMOTION_KEYS, score)
    assert row == before


def test_self_understanding_does_not_become_an_ordinary_emotion():
    row = {'emotions': ['自己理解'], 'emotion_details': []}
    assert not reports._has_renderable_emotion_content(row)
    assert reports._build_daily_metrics([row])['totalAll'] == 0


def test_daily_generation_respects_exact_period_boundaries_and_saves_the_snapshot_hash(monkeypatch):
    from subscription import SubscriptionTier
    import astor_job_queue

    target = reports._build_target_period('daily', datetime(2026, 11, 8, 3, tzinfo=timezone.utc))
    rows = [
        {'created_at': '2026-11-06T14:59:59.999Z', 'emotions': ['怒り'],
            'emotion_details': [{'type': '怒り', 'strength': 'strong'}], 'is_secret': False},
        {'created_at': target.period_start_iso, 'emotions': ['喜び'], 'emotion_details': [], 'is_secret': False},
        {'created_at': target.period_end_iso, 'emotions': ['不安'],
            'emotion_details': [{'type': '不安', 'strength': 'strong'}], 'is_secret': False},
        {'created_at': '2026-11-07T15:00:00.000Z', 'emotions': ['悲しみ'],
            'emotion_details': [{'type': '悲しみ', 'strength': 'strong'}], 'is_secret': False},
        {'created_at': '2026-11-07T01:00:00.000Z', 'emotions': ['平穏'],
            'emotion_details': [{'type': '平穏', 'strength': 'strong'}], 'is_secret': True},
    ]
    captured, saved = [], []

    def handler(request):
        captured.append(request)
        if request.url.path == '/rest/v1/emotions':
            filters = request.url.params.get_list('created_at')
            assert filters == ['gte.' + target.period_start_iso, 'lte.' + target.period_end_iso]
            assert request.url.params['user_id'] == 'eq.synthetic-owner'
            # The mock storage applies the actual received predicates, not a
            # pre-filtered fixture, so a lost boundary cannot pass this test.
            selected = deepcopy(rows)
            for predicate in filters:
                operation, boundary = predicate.split('.', 1)
                if operation == 'gte':
                    selected = [r for r in selected if r['created_at'] >= boundary]
                elif operation == 'lte':
                    selected = [r for r in selected if r['created_at'] <= boundary]
            return httpx.Response(200, json=selected)
        if request.url.path == '/rest/v1/material_snapshots':
            return httpx.Response(200, json=[{'source_hash': 'c' * 64}])
        if request.url.path == '/rest/v1/myweb_reports' and request.method == 'POST':
            saved.append(json.loads(request.content))
            return httpx.Response(201, json=[{'id': 'synthetic-report'}])
        raise AssertionError('Unexpected synthetic request')

    async def tier(*args, **kwargs):
        return SubscriptionTier.FREE

    async def enqueue(**kwargs):
        return None

    monkeypatch.setattr(reports, 'get_subscription_tier_for_user', tier)
    monkeypatch.setattr(astor_job_queue, 'enqueue_job', enqueue)
    # This test targets source transport, period aggregation and provenance;
    # the existing independent gate suites own text admission and anchors.
    monkeypatch.setattr(reports, '_attach_analysis_report_validity_meta_if_available',
        lambda content_json, **kwargs: content_json)
    monkeypatch.setattr(reports, 'attach_emlis_context_anchors', lambda content_json, anchors: content_json)
    monkeypatch.setattr(reports, 'build_emotion_report_emlis_context_anchors', lambda **kwargs: {})

    async def run():
        async with _transport(monkeypatch, handler):
            return await reports._generate_and_save('synthetic-owner', target, include_astor=False)

    _, content, _, meta = asyncio.run(run())
    assert meta == {'status': 'generated', 'report_id': 'synthetic-report'}
    assert content['metrics']['totalAll'] == 5
    assert content['metrics']['totals'] == dict(joy=2, sadness=0, anxiety=3, anger=0, calm=0)
    assert content['publish']['publicSourceHash'] == 'c' * 64
    assert content['publish']['status'] == 'READY' and content['publish']['secretExcluded'] is True
    assert len(saved) == 1
    assert saved[0]['user_id'] == 'synthetic-owner'
    assert saved[0]['period_start'] == target.period_start_iso
    assert saved[0]['period_end'] == target.period_end_iso
    assert saved[0]['content_json']['publish']['publicSourceHash'] == 'c' * 64
