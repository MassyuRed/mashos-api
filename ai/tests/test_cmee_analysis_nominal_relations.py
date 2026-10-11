"""Public synthetic period records: preserve relations inside action objects."""
from dataclasses import replace
import hashlib
import unittest

import test_cmee_analysis_v1d_vertical as existing
from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.cores.analysis.source_adapter import (
    freeze_analysis_sources,
)

OWNER = existing.OWNER
record, request = existing.record, existing.request


class NominalRelationTests(unittest.TestCase):
    def generate(self, value):
        return MeaningExperienceEngine().generate(value)

    def test_written_nominal_relation_survives_with_original_evidence(self):
        for clause, noun, lemma in (
            ('私は同僚からの資料を調べた', '同僚からの資料', '調べる'),
            ('私は家族への手紙を書いた', '家族への手紙', '書く'),
            ('私は同僚との会議を記録した', '同僚との会議', '記録する'),
            ('私は職場での考えをノートに書いた', '職場での考え', '書く'),
            ('私は学校からの家族への連絡を見た', '学校からの家族への連絡', '見る'),
            ('私は同僚からの新しい資料を調べました', '同僚からの新しい資料', '調べる'),
        ):
            with self.subTest(clause=clause):
                req = request(record(memo=clause + '。'))
                artifact = self.generate(req).artifact
                self.assertIsNotNone(artifact)
                node, = artifact.graph.nodes
                self.assertIn(('を', noun), node.proposition.arguments)
                self.assertEqual(node.proposition.predicate_lemma, lemma)
                self.assertEqual((node.proposition.actor, node.polarity, node.temporal_scope),
                                 ('SELF', 'positive', 'past'))
                ref, = node.evidence_refs
                source, = freeze_analysis_sources(req).sources
                raw = source.envelope.raw_utf8[ref.utf8_start:ref.utf8_end]
                self.assertEqual(raw.decode(), clause)
                self.assertEqual(hashlib.sha256(raw).hexdigest(), ref.literal_sha256)
                visual = artifact.safe_projection(authenticated_owner_scope=OWNER)
                text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text']
                self.assertIn(noun, visual['nodes'][0]['visible_label'])
                self.assertIn(visual['nodes'][0]['visible_label'], text)

    def test_multiple_records_keep_shared_content_and_nondirectional_cooccurrence(self):
        artifact = self.generate(request(
            record(1, memo='私は職場での考えをノートに書いた。私は同僚へのメモを残した。'),
            record(2, memo='僕はノートに職場での考えを書きました。僕は同僚へのメモを残しました。'),
        )).artifact
        self.assertIsNotNone(artifact)
        self.assertEqual(len(artifact.graph.nodes), 2)
        self.assertEqual([len(n.record_refs) for n in artifact.graph.nodes], [2, 2])
        edge, = artifact.graph.edges
        self.assertEqual(edge.edge_kind, 'REPEATED_COOCCURRENCE')
        visual = artifact.safe_projection(authenticated_owner_scope=OWNER)
        self.assertEqual([n['evidence_badge_count'] for n in visual['nodes']], [2, 2])
        self.assertNotIn('from_ref', visual['edges'][0])
        self.assertNotIn('to_ref', visual['edges'][0])

    def test_period_preserves_each_written_sequence_without_cross_record_links(self):
        memo = ('私は会議の司会を担当した。その後、私は同僚からの資料を調べた。'
                'それから、私は家族への手紙を書いた。')
        artifact = self.generate(request(record(1, memo=memo), record(2, memo=memo))).artifact
        self.assertIsNotNone(artifact)
        self.assertEqual(len(artifact.graph.edges), 4)
        for edge in artifact.graph.edges:
            self.assertEqual(edge.edge_kind, 'OBSERVED_ORDER')
            self.assertEqual(len({e.source_envelope_id for e in edge.evidence_refs}), 1)
        self.assertEqual(sum(n.proposition.predicate_lemma == '調べる'
                             for n in artifact.graph.nodes), 2)
        artifact.safe_projection(authenticated_owner_scope=OWNER)

    def test_different_nominal_relations_do_not_merge_or_disappear_in_comparison(self):
        memo = '。'.join('私は同僚' + link + '資料を調べた'
                        for link in ('からの', 'への', 'との', 'の')) + '。'
        artifact = self.generate(request(record(memo=memo))).artifact
        self.assertEqual(len(artifact.graph.nodes), 4)
        helper = existing.AnalysisVerticalTests()
        same = helper.compared('私はノートに職場での考えを書いた。',
                               '僕は職場での考えをノートに書きました。').artifact
        self.assertFalse(same.period_comparison.change_claims)
        changed = helper.compared('私は同僚への資料を調べた。',
                                  '私は同僚からの資料を調べた。').artifact
        self.assertIn('ROUTE_EVIDENCE_CHANGED', changed.safe_projection(
            authenticated_owner_scope=OWNER)['period_comparison']['safe_change_kinds'])

    def test_negative_past_and_explicit_day_keep_their_scope(self):
        for clause in ('私は同僚からの資料を調べなかった。',
                       '僕は同僚からの資料を調べませんでした。'):
            artifact = self.generate(request(record(memo=clause))).artifact
            self.assertIsNotNone(artifact)
            node, = artifact.graph.nodes
            self.assertEqual((node.polarity, node.temporal_scope), ('negative', 'past'))
            self.assertIn('行わなかった', artifact.safe_text_projection(
                authenticated_owner_scope=OWNER)['text'])
        artifact = self.generate(request(record(memo='私は昨日、同僚からの資料を調べた。'))).artifact
        self.assertEqual(artifact.graph.nodes[0].proposition.relative_day, 'YESTERDAY')
        artifact.safe_projection(authenticated_owner_scope=OWNER)

    def test_unread_scopes_do_not_become_actions_or_bridge_a_sequence(self):
        for clause in (
            '同僚からの資料を調べた', '友人は同僚からの資料を調べた',
            '私は同僚から調べた資料を見た', '私は誰からの資料を見た',
            '私は同僚との誰の会議を記録した', '私は同僚との明日会議を記録した',
            '私は同僚との今日からの会議を記録した',
            '私は同僚との昨日での会議を記録した',
            '私は昨日同僚からの資料を調べた',
            '私は同僚からの資料を調べたと思う',
            '私は同僚からの資料を調べたい',
            '私は同僚からの資料を調べるかもしれないと思う',
            '私は同僚からの資料を調べてから、私は安心した',
        ):
            with self.subTest(clause=clause):
                self.assertIsNone(self.generate(request(record(memo=clause + '。'))).artifact)
        partial = self.generate(request(record(memo=
            '私は同僚からの資料を調べた。まだ読めない文がある。その後、私は家族への手紙を書いた。'))).artifact
        self.assertEqual(len(partial.graph.nodes), 2)
        self.assertFalse(partial.graph.edges)
        self.assertTrue(any(g.missing_scope == 'SOURCE_SCOPE' for g in partial.graph.unknown_gaps))

    def test_quotations_reports_and_dreams_keep_attribution_boundary(self):
        clause = '私は同僚からの資料を調べた'
        for memo in ('「' + clause + '」', clause + 'と聞いた。',
                     clause + 'なら。', clause + '？', clause + '夢を見た。',
                     '友人の話です。' + clause + '。',
                     '友人は言っていた。' + clause + '。'):
            with self.subTest(memo=memo):
                self.assertIsNone(self.generate(request(record(memo=memo))).artifact)

    def test_following_attribution_or_retraction_is_not_lost_at_punctuation(self):
        for finite in ('調べた', '調べなかった'):
            clause = '私は同僚からの資料を' + finite
            for host in ('と友人が言った。', 'というのは嘘だった。',
                         'のではなかった。', 'と思っただけだった。', 'わけではない。'):
                with self.subTest(finite=finite, host=host):
                    self.assertIsNone(self.generate(request(record(memo=clause + '。' + host))).artifact)
            for independent in ('とても長い一日だった。', '明日は休む。', 'ところで、別のこともあった。'):
                with self.subTest(finite=finite, independent=independent):
                    artifact = self.generate(request(record(memo=clause + '。' + independent))).artifact
                    self.assertIsNotNone(artifact)
                    self.assertEqual(len(artifact.graph.nodes), 1)
                    self.assertTrue(artifact.graph.unknown_gaps)
                    artifact.safe_projection(authenticated_owner_scope=OWNER)

    def test_supplement_correction_and_withdrawal_preserve_remaining_period_content(self):
        helper = existing.AnalysisVerticalTests()
        old, new = '私は同僚からの資料を調べた', '私は同僚への資料を調べなかった'
        original = record(memo=old + '。その後、私は家族への手紙を書いた。')
        req = request(helper.with_answer(original, '「' + old + '」ではなく「' + new + '」です。'))
        artifact = self.generate(req).artifact
        self.assertIsNotNone(artifact)
        node = next(n for n in artifact.graph.nodes if n.proposition.predicate_lemma == '調べる')
        self.assertEqual((node.proposition.arguments, node.polarity),
                         ((('を', '同僚への資料'),), 'negative'))
        self.assertFalse(artifact.graph.edges)
        artifact.safe_projection(authenticated_owner_scope=OWNER)
        withdrawn = self.generate(request(helper.with_answer(original,
            '「' + old + '」は取り消します。'))).artifact
        self.assertEqual(len(withdrawn.graph.nodes), 1)
        self.assertFalse(withdrawn.graph.edges)
        ordinary = self.generate(request(helper.with_answer(record(memo='私は記録を残した。'),
            old + '。'))).artifact
        self.assertEqual(len(ordinary.graph.nodes), 2)
        contradiction = self.generate(request(helper.with_answer(record(memo=old + '。'),
            old.replace('調べた', '調べなかった') + '。')))
        self.assertIsNone(contradiction.artifact)
        self.assertEqual(contradiction.reason_codes, ('analysis_supplement_interpretation_pending',))


class NominalRelationStorageTests(unittest.IsolatedAsyncioTestCase):
    async def test_period_map_is_saved_and_reread_without_generation(self):
        import copy
        import os
        from unittest.mock import patch
        from uuid import UUID
        import analysis_observed_service as service
        import test_analysis_observed_storage as saved
        memo = ('私は会議の司会を担当した。その後、私は同僚からの資料を調べた。'
                'それから、私は家族への手紙を書いた。')
        fx = saved.fixture(memo)
        fx['original']['emotion_details'] = [{'type': '平穏', 'strength': 'medium'}]
        second = copy.deepcopy(fx['original'])
        second.update(id=str(UUID(int=102)), created_at='2026-10-02T01:00:00')
        row, writes = fx['row'], []

        async def rpc(name, payload):
            if name == 'analysis_observed_source_snapshot':
                return {'guard': saved.GUARD, 'tier': 'plus', 'now': saved.END,
                        'members': [{'original': original, 'thread': None, 'events': []}
                                    for original in (fx['original'], second)]}
            if name == 'analysis_observed_commit':
                writes.append(payload)
                row['id'] = str(UUID(payload['p_artifact_id'][9:]))
                row['content_text'] = payload['p_text']
                row['content_json']['watashiMap'] = payload['p_projection']
                return row['id']
            self.assertEqual(name, 'analysis_observed_read')
            return saved.result([row], matched=True)

        with patch.dict(os.environ, COCOLON_ANALYSIS_PERIOD_COMPARISON_MODE='off'), \
                patch.object(service, '_rpc', side_effect=rpc):
            current = await service.generate_saved(saved.OWNER, start=saved.START, end=saved.END,
                report_mode='standard', report_type='latest')
            with patch.object(MeaningExperienceEngine, 'generate', side_effect=AssertionError('regenerated')):
                reread = await service.read_saved(saved.OWNER, report_id=current['id'], report_mode='standard')
        self.assertEqual(len(writes), 1)
        self.assertEqual(current, reread['items'][0])
        self.assertEqual(current['content_text'], writes[0]['p_text'])
        projection = current['content_json']['watashiMap']
        self.assertEqual(projection, writes[0]['p_projection'])
        self.assertEqual(len(projection['edges']), 4)
        self.assertEqual(sum('同僚からの資料' in n['visible_label'] for n in projection['nodes']), 2)
        self.assertIn('家族への手紙を書く', current['content_text'])
