"""Cumulative behavior with the real compiler/author and synthetic owned input."""
import copy
import json
from pathlib import Path
import unittest
from unittest.mock import AsyncMock, patch
from uuid import UUID

import analysis_cumulative_service as service
from analysis_observed_service import private_storage_evidence
from astor_material_snapshots import AnalysisSavedSourceError

OWNER = str(UUID(int=1))


def source_snapshot(count=201, tier='free'):
    members = []
    for i in range(count):
        members.append(dict(original=dict(id=str(UUID(int=101+i)),
            created_at='2025-01-01T01:00:00' if i == 0 else '2026-10-01T01:00:00',
            memo='私は考えをノートに書いた。私は仕事を続けたい。',
            memo_action='', category=['仕事'], emotions=['平穏'], emotion_details=[]), thread=None, events=[]))
    return dict(tier=tier, now='2026-11-01T08:00:00+00:00', members=members,
        period_start='2025-01-01T01:00:00+00:00', period_end='2026-11-01T08:00:00+00:00',
        guard='analysis-db-cumulative-v1:' + 'a'*64)


def sql_fixture(safety=False):
    snap = source_snapshot(2 if safety else 201)
    if safety:
        snap['members'][1]['original']['memo'] = '死にたい。'
    artifact, coverage = service.build_cumulative_map(OWNER, snap)
    private = private_storage_evidence(artifact)
    private['coverage'] = coverage
    private['source_record_refs'] = [r['original']['id'] for r in snap['members']]
    result = dict(snapshot=snap, private=private, id=str(UUID(artifact.artifact_id[9:])),
        projection=artifact.safe_projection(authenticated_owner_scope=OWNER),
        text=artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'])
    if not safety:
        result['safety_case'] = sql_fixture(safety=True)
    return result


class CumulativeMapTests(unittest.TestCase):
    def test_all_201_records_include_the_oldest_on_free_and_match_other_plans(self):
        snap = source_snapshot()
        artifact, coverage = service.build_cumulative_map(OWNER, snap)
        self.assertEqual(coverage['source_count'], 201)
        self.assertEqual(coverage['mapped_count'], 201)
        self.assertEqual(len(artifact.source_members), 201)
        self.assertIn(snap['members'][0]['original']['id'], artifact.graph.nodes[0].record_refs)
        self.assertIn(snap['members'][100]['original']['id'], artifact.graph.nodes[0].record_refs)
        self.assertTrue(any(e.edge_kind == 'REPEATED_COOCCURRENCE' for e in artifact.graph.edges))
        text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text']
        for tier in ('plus', 'premium'):
            other, counts = service.build_cumulative_map(OWNER, dict(snap, tier=tier))
            self.assertEqual(other.safe_text_projection(authenticated_owner_scope=OWNER)['text'], text)
            self.assertEqual(counts, coverage)

    def test_one_unhandled_record_is_disclosed_and_does_not_erase_old_structures(self):
        snap = source_snapshot(2)
        snap['members'][1]['original']['memo'] = 'ふと思い出したことを、まだ言葉にできません。'
        artifact, coverage = service.build_cumulative_map(OWNER, snap)
        self.assertIsNotNone(artifact)
        self.assertEqual(coverage['source_count'], 2)
        self.assertEqual(coverage['unparsed_count'], 1)
        self.assertEqual(coverage['mapped_count'], 1)

    def test_safety_source_does_not_become_an_ordinary_map_fact(self):
        snap = source_snapshot(2)
        snap['members'][1]['original']['memo'] = '死にたい。'
        artifact, coverage = service.build_cumulative_map(OWNER, snap)
        self.assertIsNotNone(artifact)
        self.assertEqual(coverage['excluded_count'], 1)
        self.assertEqual(coverage['exclusion_reasons'], {'analysis_separate_safety_required': 1})
        self.assertNotIn(snap['members'][1]['original']['id'], artifact.graph.nodes[0].record_refs)

    def test_edited_original_remains_usable_and_old_bound_answers_are_not_reused(self):
        snap = source_snapshot(1)
        old = copy.deepcopy(snap['members'][0]['original'])
        old['memo'] = '私は仕事を続けた。'
        snap['members'][0]['thread'] = dict(user_id=OWNER,
            original_emotion_id=old['id'], source_snapshot=old)
        snap['members'][0]['events'] = [{'kind': 'ANSWER'}]
        artifact, coverage = service.build_cumulative_map(OWNER, snap)
        self.assertIsNotNone(artifact)
        self.assertEqual(coverage['stale_supplement_count'], 1)

    def test_foreign_thread_is_an_error_not_a_silent_exclusion(self):
        snap = source_snapshot(1)
        snap['members'][0]['thread'] = dict(user_id=str(UUID(int=2)),
            original_emotion_id=snap['members'][0]['original']['id'])
        with self.assertRaises(AnalysisSavedSourceError):
            service.build_cumulative_map(OWNER, snap)


class CumulativeReadTests(unittest.IsolatedAsyncioTestCase):
    async def test_month_is_forwarded_for_direct_detail_and_evidence(self):
        rpc = AsyncMock(return_value=dict(items=[], subscription_tier='free', matched=True, history_limit=2))
        with patch.object(service, '_rpc', rpc):
            await service.read_maps(OWNER, report_id=str(UUID(int=101)), month='2026-09')
        self.assertEqual(rpc.await_args.args[1]['p_month'], '2026-09-01')

    async def test_reused_current_map_attempts_this_month_capture_without_running_author(self):
        fx = sql_fixture()
        row = dict(id=fx['id'], source_profile='cumulative.v1', report_mode='standard', report_type='latest',
            title='わたしマップ', period_start=fx['snapshot']['period_start'], period_end=fx['snapshot']['period_end'],
            generated_at=fx['snapshot']['period_end'], snapshot_month=None, captured_at=None,
            content_text=fx['text'], content_json=dict(report_mode='standard', watashiMap=fx['projection'], map_context=fx['private']['coverage']))
        rpc = AsyncMock(side_effect=[fx['snapshot'], fx['id']])
        with patch.object(service, 'read_maps', AsyncMock(return_value={'items':[row]})), \
                patch.object(service, '_rpc', rpc), patch.object(service, 'observed_mode', return_value='development'), \
                patch.object(service, 'build_cumulative_map', side_effect=AssertionError('must not regenerate')):
            result = await service.ensure_map(OWNER)
        self.assertTrue(result['has_visible_content'])
        self.assertEqual(rpc.await_args.args[0], 'analysis_cumulative_commit')
        self.assertEqual(rpc.await_args.args[1]['p_existing_id'], fx['id'])


def test_real_q3_saved_answers_cross_trimmed_sql_source_and_cumulative_lifecycle(monkeypatch):
    import asyncio
    from dataclasses import asdict
    import os
    import pytest
    from fastapi import HTTPException
    from test_emlis_q3_application import Q3Database, run, answer, cont
    from emlis_thread_service import EmlisThreadService, Q3_PROFILE
    import emlis_thread_store
    from astor_material_snapshots import _analysis_saved_member
    from cocolon_meaning_experience_engine.cores.analysis.source_adapter import _time
    if not os.environ.get('Q2_PGLITE_MODULE'):
        pytest.skip('PostgreSQL WASM dependency is not configured')
    db = Q3Database()
    try:
        db.migrate()
        for name in ('20261003134440_analysis_observed_artifacts.sql', '20261004041627_analysis_period_comparison.sql',
                     '20261101080144_cumulative_watashi_map.sql'):
            db.proc.stdin.write(json.dumps({'script': True, 'sql': (Path(__file__).parents[2]/'supabase/migrations'/name).read_text()})+'\n')
            db.proc.stdin.flush()
            assert 'code' not in json.loads(db.proc.stdout.readline())
        parent, other_parent = str(UUID(int=501)), str(UUID(int=502))
        db.query('insert into auth.users values ($1)', [OWNER])
        db.query("insert into public.profiles values ($1,'premium')", [OWNER])
        memo = '褒められたのに、嬉しくなかった。誘われたのに、悲しかった。頼まれたのに、寂しかった。'
        for rid, text in ((parent, memo), (other_parent, '私は考えをノートに書いた。私は仕事を続けたい。')):
            db.query("insert into public.emotions values ($1,$2,now() at time zone 'UTC',$3,'',array['仕事'],array['不安'],$4)",
                [rid, OWNER, text, json.dumps([{'type':'不安','strength':'medium'}])])
        monkeypatch.setattr(emlis_thread_store, 'sb_post_rpc', db.rpc)
        emlis = EmlisThreadService(runtime_profile=Q3_PROFILE)
        dto = run(emlis.start(OWNER, parent))
        for n, text in enumerate(('その時は重かった。','その時は怖かった。','その時は苦しかった。'), 1):
            dto = run(answer(emlis, OWNER, dto, text, 'cumulative-'+str(n)))
            assert dto['answer_saved'] and dto['body_state'] == 'REFINED'
            if n < 3:
                dto = run(cont(emlis, OWNER, dto, 'continue-'+str(n)))
        db.query("update public.profiles set subscription_tier='free' where id=$1", [OWNER])
        async def rpc(name, payload):
            args = ','.join(f'{k} => ${i}' for i,k in enumerate(payload,1))
            params = [json.dumps(v, ensure_ascii=False) if isinstance(v,(dict,list)) else v for v in payload.values()]
            result = await asyncio.to_thread(db.query, f'select public.{name}({args}) as value', params, 'service_role')
            if 'code' in result:
                raise HTTPException(409, result['code'])
            return result['rows'][0]['value']
        monkeypatch.setattr(service, '_rpc', rpc)
        monkeypatch.setattr(service, 'observed_mode', lambda:'development')
        snap = run(rpc('analysis_cumulative_source_snapshot', {'p_user_id':OWNER}))
        raw = next(x for x in snap['members'] if x['original']['id'] == parent)
        assert len([x for x in raw['events'] if x['kind'] == 'ANSWER']) == 3
        assert set(x['kind'] for x in raw['events']) == {'QUESTION','ANSWER'}
        assert set(raw['thread']['data']) <= {'runtime_profile','semantic_profile','execution_mode','original_source_ref'}
        member, _ = _analysis_saved_member(dict(raw,tier='free',now=snap['now']), owner=OWNER,
            input_id=parent, tier='free', start=_time(snap['period_start']), end=_time(snap['period_end']), cumulative=True)
        assert len(member.supplements) == 3
        built = run(service.ensure_map(OWNER))
        assert built['has_visible_content'], built
        assert built['map_context']['source_count'] == 2
        assert built['map_context']['processed_count'] + built['map_context']['excluded_count'] == 2
        historical = run(service.ensure_map(OWNER, monthly=True))
        assert historical['meta'] == built['meta']
        for node in built['meta']['nodes']:
            evidence = run(service.map_evidence(OWNER, built['report_id'], node['node_ref'], month=historical['snapshot_month']))
            assert evidence['items']
            assert all(x['version_state'] == 'CURRENT' for x in evidence['items'])
        # A later Emlis body-only change must not dirty the map source identity.
        guard = snap['guard']
        db.query("update public.emlis_input_threads set revision=revision+1 where original_emotion_id=$1", [parent])
        assert run(rpc('analysis_cumulative_source_snapshot', {'p_user_id':OWNER}))['guard'] == guard
        # Explicit source deletion purges the saved derivative and monthly reference.
        db.query('delete from public.emotions where id=$1', [parent])
        assert not run(service.read_maps(OWNER, history=True))['items']
    finally:
        db.proc.stdin.close()
        db.proc.wait(timeout=10)


if __name__ == '__main__':
    unittest.main()
