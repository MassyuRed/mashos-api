"""Legacy global material reads retain their explicit caps and reject partial sources."""
import asyncio
from copy import deepcopy

import httpx
import pytest

import astor_material_snapshots as materials

OWNER = '00000000-0000-0000-0000-000000000001'


def install_transport(monkeypatch, respond):
    client_class = httpx.AsyncClient
    monkeypatch.setattr(materials.httpx, 'AsyncClient',
        lambda **kwargs: client_class(transport=httpx.MockTransport(respond), **kwargs))
    monkeypatch.setattr(materials, '_has_supabase_config', lambda: True)
    monkeypatch.setattr(materials, 'SUPABASE_URL', 'https://synthetic-global.invalid')
    monkeypatch.setattr(materials, '_sb_headers', lambda **kwargs: {})


def rows(count):
    return [dict(id=str(index), user_id=OWNER, created_at='2026-11-07T01:00:00Z',
        memo='私は公園で休みました。', memo_action='私は資料を確認しました。',
        category=['生活', '仕事', '趣味', '人間関係', '恋愛', '健康', '学習', '価値観', '人生'],
        emotions=['喜び', '平穏'], emotion_details=[dict(type='喜び', strength='strong'),
            dict(type='平穏', strength='weak')], emotion_strength_avg=2, is_secret=False)
        for index in range(count)]


async def read(kind, *, maximum=20000):
    if kind == 'meta':
        return await materials.fetch_emotion_meta_for_hash(OWNER)
    if kind == 'recent':
        return await materials.fetch_recent_emotions(OWNER, include_secret=False)
    if kind == 'standard':
        return await materials.fetch_emotions_for_self_structure(OWNER, include_secret=False,
            page_size=1000, max_rows=maximum)
    if kind == 'premium':
        return await materials.fetch_emotions_for_premium_reflection(OWNER, include_secret=False,
            page_size=1000, max_rows=maximum)
    return await materials._fetch_optional_rows_by_user(table='optional_inputs', user_id=OWNER,
        include_secret=False, page_size=1000, max_rows=maximum)


@pytest.mark.parametrize('kind', ['meta', 'recent', 'standard', 'premium', 'optional'])
def test_short_global_pages_are_not_end_of_source(monkeypatch, kind):
    source = rows(8)
    seen = []
    def respond(request):
        query = request.url.params
        assert query['user_id'] == f'eq.{OWNER}'
        assert query['order'] == ('created_at.desc,id.desc' if kind == 'recent' else 'created_at.asc,id.asc')
        offset, limit = int(query['offset']), int(query['limit'])
        seen.append(offset)
        return httpx.Response(206, json=source[offset:offset + min(limit, 3)])
    install_transport(monkeypatch, respond)
    actual = asyncio.run(read(kind))
    expected = list(reversed(source)) if kind == 'recent' else source
    # Optional rows are sorted by stable source identity for the view contract.
    if kind == 'optional':
        expected = sorted(source, key=lambda row: row['id'])
    assert actual == expected
    assert seen == [0, 3, 6, 8]


@pytest.mark.parametrize('kind', ['meta', 'standard', 'premium', 'optional'])
def test_global_explicit_twenty_thousand_row_cap_remains(monkeypatch, kind):
    source = rows(20001)
    offsets = []
    monkeypatch.setattr(materials, 'SNAPSHOT_META_MAX_ROWS', 20000)
    def respond(request):
        query = request.url.params
        offset, limit = int(query['offset']), int(query['limit'])
        offsets.append(offset)
        return httpx.Response(200, json=source[offset:offset + min(limit, 137)])
    install_transport(monkeypatch, respond)
    actual = asyncio.run(read(kind))
    assert len(actual) == 20000
    assert {item['id'] for item in actual} == {str(index) for index in range(20000)}
    assert offsets == list(range(0, 20000, 137))


def test_optional_public_filter_does_not_change_transport_offset_or_raw_cap(monkeypatch):
    source = rows(1001)
    for item in source[:1000]:
        item['is_secret'] = True
    seen = []
    def respond(request):
        query = request.url.params
        offset, limit = int(query['offset']), int(query['limit'])
        seen.append(offset)
        return httpx.Response(200, json=source[offset:offset + min(limit, 137)])
    install_transport(monkeypatch, respond)
    actual = asyncio.run(materials._fetch_optional_rows_by_user(table='optional_inputs', user_id=OWNER,
        include_secret=False, page_size=1000, max_rows=1000))
    assert actual == []
    assert seen == list(range(0, 1000, 137))


@pytest.mark.parametrize('kind', ['meta', 'recent', 'standard', 'premium', 'optional'])
@pytest.mark.parametrize('broken', ['invalid-json', 'non-list', 'invalid-member'])
def test_malformed_later_global_page_is_never_an_empty_terminator(monkeypatch, kind, broken):
    source = rows(3)
    def respond(request):
        if request.url.params['offset'] == '0':
            return httpx.Response(200, json=source)
        if broken == 'invalid-json':
            return httpx.Response(206, content=b'{')
        return httpx.Response(206, json={} if broken == 'non-list' else [source[0], None])
    install_transport(monkeypatch, respond)
    with pytest.raises(RuntimeError, match='emotion_period_source_unavailable'):
        asyncio.run(read(kind))


@pytest.mark.parametrize('failed_source', ['emotions', materials.ECHO_INPUTS_TABLE])
@pytest.mark.parametrize('broken', ['invalid-json', 'non-list', 'invalid-member'])
def test_global_generation_cannot_save_a_partial_source(monkeypatch, failed_source, broken):
    source, writes = rows(3), []
    def respond(request):
        if request.url.path != f'/rest/v1/{failed_source}':
            return httpx.Response(200, json=[])
        if request.url.params['offset'] == '0':
            return httpx.Response(200, json=source)
        if broken == 'invalid-json':
            return httpx.Response(200, content=b'{')
        return httpx.Response(200, json={} if broken == 'non-list' else [source[0], None])
    install_transport(monkeypatch, respond)
    async def save(**kwargs):
        writes.append(deepcopy(kwargs))
        return True
    monkeypatch.setattr(materials, '_insert_snapshot_row', save)
    with pytest.raises(RuntimeError, match='emotion_period_source_unavailable'):
        asyncio.run(materials.generate_and_store_material_snapshots(user_id=OWNER, scope='global'))
    assert writes == []


def test_optional_first_page_not_found_remains_optional(monkeypatch):
    install_transport(monkeypatch, lambda request: httpx.Response(404, json={'message': 'not installed'}))
    assert asyncio.run(read('optional')) == []
    with pytest.raises(FileNotFoundError, match='emotion_material_source_not_found'):
        asyncio.run(read('meta'))


@pytest.mark.parametrize('status', [404, 401, 500])
def test_optional_later_http_failure_never_returns_partial_materials(monkeypatch, status):
    def respond(request):
        return httpx.Response(200, json=rows(2)) if request.url.params['offset'] == '0' else httpx.Response(status)
    install_transport(monkeypatch, respond)
    expected = FileNotFoundError if status == 404 else RuntimeError
    with pytest.raises(expected):
        asyncio.run(read('optional'))
