"""Snapshot facts and derived features are independent of every display candidate."""
import asyncio
from copy import deepcopy
from datetime import timedelta
import hashlib
import json
from pathlib import Path

import pytest
import httpx
from fastapi import HTTPException

import astor_material_snapshots as materials
import api_analysis_reports as reports
from cocolon_text_generation_core.adapters.analysis_composer import evaluate_analysis_composer

OWNER = '00000000-0000-0000-0000-000000000001'
SCOPES = dict(daily='emotion_daily:2026-11-07', weekly='emotion_weekly:2026-11-08', monthly='emotion_monthly:2026-11')


def fixture(monkeypatch, kind='weekly'):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / 'services'))
    import astor_worker as worker
    from analysis_engine_adapter import build_emotion_entries_from_rows
    from analysis_engine.emotion_structure_engine.weekly import build_weekly_features
    from analysis_engine.emotion_structure_engine.monthly import assemble_monthly
    scope = SCOPES[kind]
    info = materials._parse_emotion_period_scope(scope)
    rows = [dict(id=f'00000000-0000-0000-0000-{index + 101:012d}',
        created_at=(info['period_start_utc'] + timedelta(hours=index + 1)).isoformat(),
        is_secret=False, memo='私は公園で休んだ。', memo_action='私は資料を確認しなかった。',
        category=['生活', '仕事', '趣味', '人間関係', '恋愛', '健康', '学習', '価値観', '人生'],
        emotions=[emotion], emotion_details=[dict(type=emotion, strength='strong')], emotion_strength_avg=3.0)
        for index, emotion in enumerate(['不安', '平穏'])]
    if kind == 'daily':
        day = materials._build_day_single(rows, info['period_start_utc'])
        views = dict(day=day, metrics=materials._compute_daily_metrics(day), movement={})
    elif kind == 'weekly':
        days = materials._build_days_fixed7(rows, info['period_start_utc'])
        views = dict(days=days, metrics=materials._compute_weekly_metrics(days))
    else:
        weeks = materials._build_weeks_fixed4(rows, info['period_start_utc'])
        views = dict(weeks=weeks, metrics=materials._compute_monthly_metrics(weeks))
    source_hash = materials.compute_source_hash_from_emotion_meta(user_id=OWNER, scope=scope,
        snapshot_type='public', meta_rows=rows)
    payload = materials.build_emotion_period_payload(scope=scope, snapshot_type='public', source_hash=source_hash,
        total_rows=2, public_rows=2, secret_rows=0,
        period_meta=dict(periodStartIso=info['period_start_iso'], periodEndIso=info['period_end_iso']), views=views)
    snap = dict(id='00000000-0000-0000-0000-000000000201', user_id=OWNER, scope=scope,
        snapshot_type='public', source_hash=source_hash, payload=payload)
    alignment = dict(profile='emotion_period.rows.v1', snapshot_id=snap['id'], source_hash=source_hash,
        scope=scope, snapshot_type='public', row_count=2)
    base = dict(engine='analysis_engine', analysis_type='emotion_structure', scope=kind,
        source_hash=source_hash, snapshot_ref=dict(snapshot_id=snap['id'], scope=scope, snapshot_type='public'),
        period=dict(start_iso=info['period_start_iso'], end_iso=info['period_end_iso']),
        entry_count=2, source_alignment=alignment)
    entries = worker._normalize_entries_to_jst(build_emotion_entries_from_rows(rows))
    standard = dict(base, analysis_stage='standard', analysis_version='emotion_structure.standard.v1')
    if kind == 'weekly':
        standard['weekly_snapshot'] = build_weekly_features(entries, 'synthetic').to_dict()
    elif kind == 'monthly':
        weeks = [build_weekly_features(worker._entries_in_window(entries,
            info['period_start_utc'] + timedelta(days=7 * i), info['period_start_utc'] + timedelta(days=7 * (i + 1))),
            'synthetic') for i in range(4)]
        standard['monthly_report'] = assemble_monthly(weeks, 'synthetic').to_dict()
    deep = dict(base, analysis_stage='deep', analysis_version='emotion_structure.deep.v2',
        deep_control_model=worker._build_deep_control_model_payload(entries, scope_kind=kind, period_label='synthetic'))
    def saved(stage, value):
        return dict(id='derived-' + stage, target_user_id=OWNER, snapshot_id=snap['id'], source_hash=source_hash,
            analysis_type='emotion_structure', scope=kind, analysis_stage=stage, payload=value)
    return scope, rows, snap, saved('standard', standard), saved('deep', deep)


def freeze(data):
    scope, _, snap, standard, deep = data
    return reports._freeze_snapshot_report_source(user_id=OWNER, scope=scope, snapshot=snap,
        standard_row=standard, deep_row=deep)


def evaluate(source, *, text=None, payload=None, legacy=None):
    bound = reports._snapshot_composer_binding(source)
    rendered = reports._render_snapshot_source(source)
    output = {k: v for k, v in rendered.items() if k != 'content_text' and v is not None}
    output['publish'] = bound['expected_publish']
    return evaluate_analysis_composer(materials=reports._snapshot_analysis_materials_for_core(source),
        report_text=bound['expected_text'] if text is None else text,
        output_payload=output if payload is None else payload,
        snapshot_binding=bound, snapshot_legacy_text=rendered['content_text'] if legacy is None else legacy)


@pytest.mark.parametrize('kind', ['daily', 'weekly', 'monthly'])
def test_source_bound_report_passes_without_candidate_phrase_units_and_keeps_detail_shape(monkeypatch, kind):
    source = freeze(fixture(monkeypatch, kind))
    result = evaluate(source)
    assert result.passed, result.rejection_reasons
    assert not any('candidate-sentence' in ref for ref in result.candidate.used_phrase_unit_ids)
    rendered = reports._render_snapshot_source(source)
    assert rendered['standardReport']['contentText'].count('【') == 5
    assert rendered['deepReport']['transitionEdges']
    facts = reports._snapshot_analysis_materials_for_core(source)
    assert all('memo' not in row for row in facts)
    assert rendered['standardReport']['contentText'] not in json.dumps(facts, ensure_ascii=False)


@pytest.mark.parametrize('replacement', [
    'この期間の記録では、安心を確かめたい気持ちが続いていたようです。',
    '対象期間の記録は999件です。', '不安が原因で平穏へ戻る必要があります。'])
def test_candidate_rewrite_cannot_create_its_own_support(monkeypatch, replacement):
    source = freeze(fixture(monkeypatch))
    before = reports._snapshot_analysis_materials_for_core(source)
    result = evaluate(source, text=replacement)
    assert not result.passed and 'analysis_snapshot_source_mismatch' in result.rejection_reasons
    assert before == reports._snapshot_analysis_materials_for_core(source)


@pytest.mark.parametrize('field', ['metrics', 'standardReport', 'deepReport', 'kokoroWeather'])
def test_candidate_graph_or_deep_field_mutation_is_rejected(monkeypatch, field):
    source = freeze(fixture(monkeypatch))
    binding = reports._snapshot_composer_binding(source)
    payload = deepcopy(binding['expected_payload'])
    payload['publish'] = binding['expected_publish']
    assert evaluate(source, payload=payload).passed
    payload[field]['injected_claim'] = '安心を求めていました。'
    assert not evaluate(source, payload=payload).passed


def test_legacy_light_body_is_checked_separately(monkeypatch):
    source = freeze(fixture(monkeypatch))
    assert not evaluate(source, legacy='原記録と関係のない文章です。').passed


def test_generated_source_comments_are_never_reintroduced_as_facts_or_visible_output(monkeypatch):
    data = fixture(monkeypatch)
    before = freeze(data)
    data[3]['payload']['narrative'] = {'structural_comment': '安心を確かめたい気持ちが続いていました。'}
    data[4]['payload']['deep_control_model']['meaning_comment'] = '本人の本質が表れています。'
    after = freeze(data)
    assert before == after
    assert reports._render_snapshot_source(before) == reports._render_snapshot_source(after)


def test_only_absent_alignment_is_recoverable_after_both_stages_bind(monkeypatch):
    data = fixture(monkeypatch)
    del data[3]['payload']['source_alignment']
    with pytest.raises(HTTPException) as failure:
        freeze(data)
    assert failure.value.status_code == 409
    assert failure.value.detail == 'analysis_snapshot_alignment_missing'
    # A later stage mismatch cannot be hidden by the first missing alignment.
    data[4]['target_user_id'] = 'another-owner'
    with pytest.raises(HTTPException) as failure:
        freeze(data)
    assert failure.value.detail == 'analysis_snapshot_source_mismatch'


@pytest.mark.parametrize('invalid', [None, {}])
def test_present_but_invalid_alignment_is_never_recoverable(monkeypatch, invalid):
    data = fixture(monkeypatch)
    data[3]['payload']['source_alignment'] = invalid
    with pytest.raises(HTTPException) as failure:
        freeze(data)
    assert failure.value.detail == 'analysis_snapshot_source_mismatch'


@pytest.mark.parametrize('mismatch', [False, True])
def test_actual_snapshot_generation_checks_source_before_upsert_and_keeps_all_report_fields(monkeypatch, mismatch):
    from subscription import SubscriptionTier
    scope, _, snap, standard, deep = fixture(monkeypatch)
    writes = []
    async def snapshot(*args, **kwargs):
        return deepcopy(snap)
    async def derived(*args, **kwargs):
        row = deepcopy(standard if kwargs['analysis_stage'] == 'standard' else deep)
        if mismatch:
            row['source_hash'] = 'f' * 64
        return row
    async def tier(*args, **kwargs):
        return SubscriptionTier.PREMIUM
    async def save(payload):
        writes.append(deepcopy(payload))
        return 'synthetic-saved-report'
    monkeypatch.setattr(reports, '_fetch_latest_snapshot_row', snapshot)
    monkeypatch.setattr(reports, '_fetch_analysis_result', derived)
    monkeypatch.setattr(reports, 'get_subscription_tier_for_user', tier)
    monkeypatch.setattr(reports, '_upsert_report', save)
    monkeypatch.setattr(reports, 'attach_emlis_context_anchors', lambda body, anchors: body)
    if mismatch:
        with pytest.raises(HTTPException):
            asyncio.run(reports._generate_and_save_from_snapshot(OWNER, scope=scope, include_astor=True))
        assert writes == []
    else:
        text, body, supplement, meta = asyncio.run(reports._generate_and_save_from_snapshot(OWNER, scope=scope, include_astor=True))
        assert meta['report_id'] == 'synthetic-saved-report' and len(writes) == 1, (
            meta, body.get('reportValidity', {}).get('blocked_reasons'))
        assert text and supplement and body['reportValidity']['save_allowed'] is True
        assert body['reportValidity']['material_count'] == 2
        assert body['standardReport']['contentText'].count('【') == 5
        assert body['deepReport']['transitionEdges'] and body['kokoroWeather']['items']
        assert writes[0]['content_text'] and writes[0]['content_json'] == body
        assert 'narrative' not in body['standardReport']['analysisPayload']


@pytest.mark.parametrize('key,value', [('secretExcluded', False), ('publicSourceHash', 'f' * 64), ('scope', 'global')])
def test_publish_source_cannot_be_rebound_after_render(monkeypatch, key, value):
    source = freeze(fixture(monkeypatch))
    binding = reports._snapshot_composer_binding(source)
    payload = deepcopy(binding['expected_payload'])
    payload['publish'] = deepcopy(binding['expected_publish'])
    assert evaluate(source, payload=payload).passed
    payload['publish'][key] = value
    assert not evaluate(source, payload=payload).passed


def test_unrequested_supplement_cannot_escape_the_source_check(monkeypatch):
    source = freeze(fixture(monkeypatch))
    binding = reports._snapshot_composer_binding(source)
    payload = deepcopy(binding['expected_payload'])
    payload['publish'] = binding['expected_publish']
    assert evaluate(source, payload=payload).passed
    payload['astorText'] = '安心を確かめたい気持ちが続いていました。'
    assert not evaluate(source, payload=payload).passed


@pytest.mark.parametrize('missing', ['evaluate_analysis_report_validity', 'attach_report_validity_meta',
    'evaluate_analysis_composer', 'attach_analysis_composer_meta'])
def test_optional_import_failure_never_skips_the_bound_source_check(monkeypatch, missing):
    source = freeze(fixture(monkeypatch))
    bound = reports._snapshot_composer_binding(source)
    rendered = reports._render_snapshot_source(source)
    body = deepcopy(bound['expected_payload'])
    body['publish'] = bound['expected_publish']
    monkeypatch.setattr(reports, missing, None)
    result = reports._attach_analysis_report_validity_meta_if_available(body,
        material_count=2, output_text=bound['expected_text'], output_payload=body,
        materials=bound['materials'], snapshot_binding=bound, legacy_text=rendered['content_text'])
    assert not reports._analysis_report_save_allowed(result)
    assert 'analysis_snapshot_source_unavailable' in result['reportValidity']['blocked_reasons']


def test_source_digest_is_verified_and_private_source_bytes_never_enter_public_meta(monkeypatch):
    source = freeze(fixture(monkeypatch))
    binding = reports._snapshot_composer_binding(source)
    rendered = reports._render_snapshot_source(source)
    body = deepcopy(binding['expected_payload'])
    body['publish'] = binding['expected_publish']
    original_digest = binding['source_digest']
    binding['source_digest'] = 'f' * 64
    bad = evaluate_analysis_composer(materials=binding['materials'], report_text=binding['expected_text'],
        output_payload=body, snapshot_binding=binding, snapshot_legacy_text=rendered['content_text'])
    assert not bad.passed
    binding['source_digest'] = original_digest
    good = evaluate_analysis_composer(materials=binding['materials'], report_text=binding['expected_text'],
        output_payload=body, snapshot_binding=binding, snapshot_legacy_text=rendered['content_text'])
    assert good.passed
    metadata = good.as_meta()
    def contains_private_source(value):
        if isinstance(value, dict):
            return 'source_bytes' in value or any(contains_private_source(item) for item in value.values())
        if isinstance(value, list):
            return any(contains_private_source(item) for item in value)
        return value == source
    assert not contains_private_source(metadata)
    assert set(metadata['meta']['runtime_meta']['snapshot_source']) == {'profile', 'source_digest', 'matched'}


@pytest.mark.parametrize('broken', ['evaluate_analysis_report_validity', 'attach_report_validity_meta',
    'evaluate_analysis_composer', 'attach_analysis_composer_meta'])
def test_validation_exception_never_becomes_best_effort_acceptance_for_bound_reports(monkeypatch, broken):
    source = freeze(fixture(monkeypatch))
    bound = reports._snapshot_composer_binding(source)
    rendered = reports._render_snapshot_source(source)
    body = deepcopy(bound['expected_payload'])
    body['publish'] = bound['expected_publish']
    def fail(*args, **kwargs):
        raise RuntimeError('synthetic validation unavailable')
    monkeypatch.setattr(reports, broken, fail)
    result = reports._attach_analysis_report_validity_meta_if_available(body,
        material_count=2, output_text=bound['expected_text'], output_payload=body,
        materials=bound['materials'], snapshot_binding=bound, legacy_text=rendered['content_text'])
    assert not reports._analysis_report_save_allowed(result)
    assert 'analysis_snapshot_source_unavailable' in result['reportValidity']['blocked_reasons']


@pytest.mark.parametrize('target,key,value', [
    ('snapshot', 'user_id', 'other-owner'), ('snapshot', 'id', 'other-snapshot'),
    ('snapshot', 'source_hash', 'b' * 64), ('snapshot', 'scope', 'emotion_weekly:2026-11-15'),
    ('snapshot', 'snapshot_type', 'internal'), ('body', 'source_hash', 'c' * 64),
    ('body', 'scope', 'emotion_weekly:2026-11-15'), ('body', 'snapshot_type', 'internal'),
    ('standard', 'target_user_id', 'other-owner'), ('standard', 'source_hash', 'd' * 64),
    ('standard', 'snapshot_id', 'other-snapshot'), ('standard', 'analysis_stage', 'deep'),
    ('standard', 'scope', 'monthly'), ('standard_payload', 'source_hash', 'e' * 64),
    ('standard_payload', 'analysis_stage', 'deep'), ('standard_payload', 'scope', 'monthly'),
    ('period', 'periodStartIso', '2026-01-01T00:00:00Z'),
    ('derived_period', 'start_iso', '2026-01-01T00:00:00Z'),
    ('ref', 'scope', 'emotion_weekly:2026-11-15'), ('alignment', 'row_count', 5),
])
def test_owner_version_period_stage_and_input_count_mismatch_fail_before_render(monkeypatch, target, key, value):
    data = fixture(monkeypatch)
    _, _, snap, standard, _ = data
    selected = dict(snapshot=snap, body=snap['payload'], period=snap['payload']['period'], standard=standard,
        standard_payload=standard['payload'], derived_period=standard['payload']['period'],
        ref=standard['payload']['snapshot_ref'], alignment=standard['payload']['source_alignment'])[target]
    selected[key] = value
    with pytest.raises(HTTPException) as caught:
        freeze(data)
    assert caught.value.status_code == 409


def test_derived_producer_checks_the_complete_actual_rows_before_lending_snapshot_identity(monkeypatch):
    import astor_worker as worker
    scope, rows, snap, _, _ = fixture(monkeypatch)
    async def fetch(owner, **kwargs):
        assert owner == OWNER and kwargs['max_rows'] is None and kwargs['include_secret'] is False
        return deepcopy(rows)
    monkeypatch.setattr(worker, 'fetch_emotions_in_range', fetch)
    actual_rows, alignment = asyncio.run(worker._aligned_emotion_period_rows(user_id=OWNER, scope=scope, snapshot=snap))
    assert alignment['source_hash'] == snap['source_hash'] and actual_rows == rows
    rows[0]['memo_action'] = '私は資料を確認した。'
    with pytest.raises(RuntimeError, match='emotion_snapshot_source_changed'):
        asyncio.run(worker._aligned_emotion_period_rows(user_id=OWNER, scope=scope, snapshot=snap))


@pytest.mark.parametrize('kind', ['daily', 'weekly', 'monthly'])
@pytest.mark.parametrize('stage', ['standard', 'deep'])
def test_actual_derived_handlers_save_alignment_for_the_rows_they_analyzed(monkeypatch, kind, stage):
    scope, rows, snap, _, _ = fixture(monkeypatch, kind)
    import astor_worker as worker
    writes = []
    info = materials._parse_emotion_period_scope(scope)
    async def snapshot(**kwargs):
        return deepcopy(snap)
    async def fetch(owner, **kwargs):
        assert owner == OWNER and kwargs['max_rows'] is None
        return deepcopy(rows) if kwargs['start_iso'] == info['period_start_iso'] else []
    async def save(*, row):
        writes.append(deepcopy(row))
        return True
    monkeypatch.setattr(worker, '_fetch_latest_public_snapshot_row', snapshot)
    monkeypatch.setattr(worker, 'fetch_emotions_in_range', fetch)
    monkeypatch.setattr(worker, '_upsert_analysis_result', save)
    handler = getattr(worker, '_handle_analyze_emotion_structure_' + stage + '_v1')
    result = asyncio.run(handler(user_id=OWNER, payload={'scope': scope}))
    assert result['status'] == 'ok' and len(writes) == 1
    row = writes[0]
    assert row['source_hash'] == snap['source_hash']
    assert row['payload']['source_alignment'] == dict(profile='emotion_period.rows.v1', snapshot_id=snap['id'],
        source_hash=snap['source_hash'], scope=scope, snapshot_type='public', row_count=2)


def test_daily_previous_rows_are_part_of_derived_alignment(monkeypatch):
    scope, rows, snap, _, _ = fixture(monkeypatch, 'daily')
    import astor_worker as worker
    info = materials._parse_emotion_period_scope(scope)
    previous = deepcopy(rows[0])
    previous['id'] = '00000000-0000-0000-0000-000000000099'
    previous['created_at'] = info['prev_period_start_iso']
    snap['source_hash'] = materials.compute_source_hash_from_emotion_meta(user_id=OWNER, scope=scope,
        snapshot_type='public', meta_rows=[*rows, previous])
    async def fetch(owner, **kwargs):
        return deepcopy(rows if kwargs['start_iso'] == info['period_start_iso'] else [previous])
    monkeypatch.setattr(worker, 'fetch_emotions_in_range', fetch)
    asyncio.run(worker._aligned_emotion_period_rows(user_id=OWNER, scope=scope, snapshot=snap))
    previous['emotion_details'][0]['strength'] = 'weak'
    with pytest.raises(RuntimeError, match='emotion_snapshot_source_changed'):
        asyncio.run(worker._aligned_emotion_period_rows(user_id=OWNER, scope=scope, snapshot=snap))


def test_hash_is_stable_under_transport_order_and_complete_period_reader_exceeds_the_old_cap(monkeypatch):
    row = dict(id='row-a', created_at='2026-11-07T01:00:00Z', memo='記録', memo_action='',
        category=['人生'], emotions=['喜び'], emotion_details=[dict(type='喜び', strength='weak')], is_secret=False)
    rows = [dict(row, id=str(index)) for index in range(20001)]
    def identity(items):
        return materials.compute_source_hash_from_emotion_meta(user_id=OWNER, scope=SCOPES['daily'], snapshot_type='public', meta_rows=items)
    assert identity(rows) == identity(list(reversed(rows)))
    seen = []
    async def get(path, *, params, timeout, strict=False):
        assert strict
        args = dict(params)
        assert args['order'] == 'created_at.asc,id.asc' and 'category' in args['select']
        seen.append(int(args['offset']))
        start, size = int(args['offset']), int(args['limit'])
        return rows[start:start+min(size, 137)]
    monkeypatch.setattr(materials, '_sb_get_json', get)
    loaded = asyncio.run(materials.fetch_emotions_in_range(OWNER, start_iso='2026-11-07T00:00:00Z',
        end_iso='2026-11-07T23:59:59Z', include_secret=False, max_rows=None))
    assert len(loaded) == 20001 and len(seen) == 147


@pytest.mark.parametrize('broken_page', ['invalid-json', 'non-list', 'invalid-member'])
def test_malformed_later_page_never_saves_a_partial_snapshot(monkeypatch, broken_page):
    scope, rows, _, _, _ = fixture(monkeypatch)
    writes = []
    def respond(request):
        if request.url.params['offset'] == '0':
            return httpx.Response(200, json=rows)
        if broken_page == 'invalid-json':
            return httpx.Response(200, content=b'{')
        return httpx.Response(200, json={} if broken_page == 'non-list' else [rows[0], None])
    client_class = httpx.AsyncClient
    monkeypatch.setattr(materials.httpx, 'AsyncClient',
        lambda **kwargs: client_class(transport=httpx.MockTransport(respond), **kwargs))
    monkeypatch.setattr(materials, '_has_supabase_config', lambda: True)
    monkeypatch.setattr(materials, 'SUPABASE_URL', 'https://synthetic-period.invalid')
    monkeypatch.setattr(materials, '_sb_headers', lambda **kwargs: {})
    async def save(**kwargs):
        writes.append(kwargs)
        return True
    monkeypatch.setattr(materials, '_insert_snapshot_row', save)
    with pytest.raises(RuntimeError, match='emotion_period_source_unavailable'):
        asyncio.run(materials._generate_and_store_emotion_period_snapshots(user_id=OWNER, scope=scope, trigger='synthetic'))
    assert writes == []
