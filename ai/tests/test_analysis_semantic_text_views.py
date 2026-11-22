"""Compact graph text and immutable historical saved-text compatibility."""
import asyncio
from copy import deepcopy
import json
from pathlib import Path
from unittest.mock import AsyncMock

from fastapi import FastAPI, HTTPException
import httpx
import pytest

import analysis_cumulative_service as service
import analysis_semantic_map as semantic
from cocolon_meaning_experience_engine.cores.analysis.observed_route_realizer import (
    analysis_semantic_projection_text as current_text,
    analysis_semantic_projection_text_legacy as legacy_text,
)
from test_analysis_cumulative import OWNER
from test_analysis_cumulative_model_source import sql_source
from test_analysis_semantic_integration import completion, semantic_source
from test_analysis_semantic_map import sample


def view():
    return dict(wire_kind='watashi.map.v3',
        overview=dict(title='図書館の記録', summary='私は図書館へ行った。\n全体で残る留保。'),
        nodes=[dict(node_ref='n1', title='訪問', summary='私は図書館へ行った。',
            explanation='私は図書館へ行った。\n昨日、私は図書館へ行った。\n私は図書館へ行った。',
            context=['趣味：平穏・中'], unknowns=['返却日はまだ確認していない。']),
            dict(node_ref='n2', title='貸出', summary='私は本を借りていない。',
                explanation='私は本を借りていない。', context=[], unknowns=[])],
        edges=[dict(from_ref='n1', to_ref='n2', label='訪問と貸出の違い',
            explanation='私は図書館へ行った。\n昨日、私は図書館へ行った。\n私は本を借りていない。')])


def test_compact_text_preserves_distinct_qualification_and_graph_without_endpoint_reprints():
    projection = view()
    before = deepcopy(projection)
    assert current_text(projection) == (
        '図書館の記録\n全体で残る留保。\n\n訪問\n私は図書館へ行った。\n昨日、私は図書館へ行った。'
        '\n趣味：平穏・中\nまだ記録にないこと：返却日はまだ確認していない。'
        '\n\n貸出\n私は本を借りていない。\n\n訪問 ／ 貸出\n訪問と貸出の違い')
    assert projection == before


def test_distinct_edge_qualification_remains_without_reprinting_endpoint_facts():
    projection = view()
    projection['edges'][0]['explanation'] += '\n借りていない理由は書いていない。'
    before = deepcopy(projection)
    text = current_text(projection)
    assert text.endswith('訪問 ／ 貸出\n訪問と貸出の違い\n借りていない理由は書いていない。')
    assert text.splitlines().count('私は図書館へ行った。') == 1
    assert text.splitlines().count('昨日、私は図書館へ行った。') == 1
    assert text.splitlines().count('私は本を借りていない。') == 1
    assert projection == before


def test_exact_summary_concatenation_does_not_repeat_separate_detail_paragraphs():
    projection = view()
    first = projection['nodes'][0]
    first['explanation'] = '私は図書館へ行った。\n昨日、私は図書館へ行った。'
    first['summary'] = '私は図書館へ行った。昨日、私は図書館へ行った。'
    projection['overview']['summary'] = first['summary']
    before = deepcopy(projection)
    text = current_text(projection)
    assert text.splitlines().count('私は図書館へ行った。') == 1
    assert text.splitlines().count('昨日、私は図書館へ行った。') == 1
    assert first['summary'] not in text
    assert projection == before


def test_historical_formatter_keeps_the_exact_prechange_saved_bytes():
    assert legacy_text(view()) == (
        '図書館の記録\n私は図書館へ行った。\n全体で残る留保。'
        '\n\n訪問\n私は図書館へ行った。\n私は図書館へ行った。\n昨日、私は図書館へ行った。\n私は図書館へ行った。'
        '\n趣味：平穏・中\nまだ記録にないこと：返却日はまだ確認していない。'
        '\n\n貸出\n私は本を借りていない。\n私は本を借りていない。'
        '\n\n訪問 ／ 貸出\n訪問と貸出の違い\n私は図書館へ行った。\n昨日、私は図書館へ行った。\n私は本を借りていない。')


@pytest.mark.parametrize('render', [current_text, legacy_text])
def test_only_exact_current_or_historical_text_is_admitted(render):
    projection = view()
    text = render(projection)
    assert service._saved_projection_text_matches(projection, text)
    for changed in (text + '\n', text.replace('借りていない', '借りた'), text[:-1], None):
        assert not service._saved_projection_text_matches(projection, changed)


@pytest.mark.parametrize('render', [current_text, legacy_text])
def test_real_sql_saved_current_and_historical_text_reread_without_rewrite(sql_source, monkeypatch, render):
    import api_self_structure as latest
    import api_self_structure_reports as reports
    db, rpc = sql_source
    migration = Path(__file__).parents[2] / 'supabase/migrations/20261107071033_analysis_semantic_map_wire.sql'
    db.proc.stdin.write(json.dumps({'script': True, 'sql': migration.read_text()}) + '\n')
    db.proc.stdin.flush()
    assert 'code' not in json.loads(db.proc.stdout.readline())
    assert 'code' not in db.query('insert into auth.users values ($1)', [OWNER])
    assert 'code' not in db.query("insert into public.profiles values ($1,'free')", [OWNER])
    for member in sample()['members']:
        item = member['original']
        assert 'code' not in db.query('insert into public.emotions values ($1,$2,$3,$4,$5,$6,$7,$8)',
            [item['id'], OWNER, item['created_at'], item['memo'], item['memo_action'],
             item['category'], item['emotions'], json.dumps(item['emotion_details'])])
    acquisitions = []
    def provider(request):
        acquisitions.append(request)
        return httpx.Response(200, json=completion())
    source = semantic_source(provider)

    async def run():
        # Simulate the previous writer before its immutable SQL commit. Never
        # bypass or modify the database's artifact immutability protections.
        from cocolon_meaning_experience_engine.cores.analysis import observed_route_realizer as realizer
        with monkeypatch.context() as previous_writer:
            if render is legacy_text:
                previous_writer.setattr(realizer, 'analysis_semantic_projection_text', legacy_text)
            first = await service.ensure_map(OWNER, model_source=source)
        projection = deepcopy(first['meta'])
        saved = render(projection)
        assert first['content_text'] == saved
        monthly = await service.ensure_map(OWNER, monthly=True, force=True, model_source=source)
        assert not monthly['refreshed'] and monthly['content_text'] == saved
        before = db.query('select * from public.analysis_observed_artifacts where id=$1', [first['report_id']])['rows'][0]
        calls = []
        async def read_only(name, payload):
            calls.append(name)
            assert name == 'analysis_cumulative_read'
            return await rpc(name, payload)
        monkeypatch.setattr(service, '_rpc', read_only)
        monkeypatch.setattr(semantic.MeaningExperienceEngine, 'generate', lambda *a, **k:
            (_ for _ in ()).throw(AssertionError('saved read regenerated')))
        current = await service.ensure_map(OWNER, ensure=False)
        month = await service.ensure_map(OWNER, monthly=True, ensure=False)
        detail = (await service.read_maps(OWNER, report_id=first['report_id']))['items'][0]
        history = await service.map_history(OWNER)
        assert current['content_text'] == month['content_text'] == detail['content_text'] == saved
        assert current['meta'] == month['meta'] == detail['content_json']['watashiMap'] == projection
        assert [row['id'] for row in history['items']] == [first['report_id']]
        monkeypatch.setenv('COCOLON_ANALYSIS_OBSERVED_MODE', 'development')
        monkeypatch.setattr(latest, '_resolve_user_id_from_token', AsyncMock(return_value=OWNER))
        monkeypatch.setattr(reports, '_require_user_id', AsyncMock(return_value=OWNER))
        app = FastAPI()
        latest.register_self_structure_routes(app)
        reports.register_self_structure_report_routes(app)
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url='http://synthetic') as client:
            headers = {'Authorization': 'Bearer synthetic', 'X-Watashi-Map-Renderer': 'semantic.v1'}
            response = await client.get('/self-structure/latest?ensure=false', headers=headers)
            assert response.status_code == 200, response.text
            assert response.json()['content_text'] == saved
            response = await client.get('/self-structure/reports/' + first['report_id'], headers=headers)
            assert response.status_code == 200, response.text
            assert response.json()['item']['content_text'] == saved
        after = db.query('select * from public.analysis_observed_artifacts where id=$1', [first['report_id']])['rows'][0]
        assert before == after and len(acquisitions) == 1
        assert set(calls) == {'analysis_cumulative_read'}
        async def corrupt_read(name, payload):
            result = await read_only(name, payload)
            for row in result['items']:
                row['content_text'] += '\n'
            return result
        monkeypatch.setattr(service, '_rpc', corrupt_read)
        with pytest.raises(HTTPException) as failure:
            await service.read_maps(OWNER, report_id=first['report_id'])
        assert failure.value.status_code == 503
    asyncio.run(run())
