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
    def test_omitted_actor_past_actions_keep_object_polarity_and_source(self):
        # Natural diary omissions must keep the action without assigning it
        # to the account owner. Cover the existing verb inflections as input.
        for lemma, noun, forms in (
            ('書く', '家族への手紙', ('書いた', '書きました', '書かなかった', '書きませんでした', '書かなかったです')),
            ('調べる', '同僚からの資料', ('調べた', '調べました', '調べなかった', '調べませんでした', '調べなかったです')),
            ('試す', '方法', ('試した', '試しました', '試さなかった', '試しませんでした', '試さなかったです')),
            ('見る', '記録', ('見た', '見ました', '見なかった', '見ませんでした', '見なかったです')),
            ('作る', '資料', ('作った', '作りました', '作らなかった', '作りませんでした', '作らなかったです')),
            ('残す', 'メモ', ('残した', '残しました', '残さなかった', '残しませんでした', '残さなかったです')),
            ('記録する', '会議', ('記録した', '記録しました', '記録しなかった', '記録しませんでした', '記録しなかったです')),
            ('メモする', '考え', ('メモした', 'メモしました', 'メモしなかった', 'メモしませんでした', 'メモしなかったです')),
            ('続ける', '仕事', ('続けた', '続けました', '続けなかった', '続けませんでした', '続けなかったです')),
        ):
            for index, finite in enumerate(forms):
                with self.subTest(lemma=lemma, finite=finite):
                    literal = noun + 'を' + finite
                    req = request(record(memo=literal + '。'))
                    artifact = self.generate(req).artifact
                    self.assertIsNotNone(artifact)
                    node, = artifact.graph.nodes
                    p = node.proposition
                    self.assertEqual((p.actor, p.arguments, p.predicate_lemma, p.polarity, p.modality, p.temporal_scope),
                        ('UNSPECIFIED', (('を', noun),), lemma,
                         'positive' if index < 2 else 'negative', 'fact', 'past'))
                    source, = freeze_analysis_sources(req).sources
                    ref, = node.evidence_refs
                    raw = source.envelope.raw_utf8[ref.utf8_start:ref.utf8_end]
                    self.assertEqual(raw.decode(), literal)
                    self.assertEqual(hashlib.sha256(raw).hexdigest(), ref.literal_sha256)
                    label = artifact.safe_projection(authenticated_owner_scope=OWNER)['nodes'][0]['visible_label']
                    self.assertIn('誰の行動かは未確定', label)
                    self.assertIn(noun, label)
                    self.assertIn(label, artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'])

    def test_omitted_actor_occurrences_do_not_merge_or_assert_same_person_conflict(self):
        memo = '資料を調べた。'
        for members in ((record(memo=memo), record(2, memo=memo)),
                        (record(memo=memo + memo),)):
            artifact = self.generate(request(*members)).artifact
            self.assertEqual(len(artifact.graph.nodes), 2)
            self.assertTrue(all(len(n.evidence_refs) == len(n.record_refs) == 1 for n in artifact.graph.nodes))
            self.assertFalse(artifact.graph.edges)
        artifact = self.generate(request(record(memo='資料を調べた。私は資料を調べた。資料を調べなかった。'))).artifact
        self.assertEqual([n.proposition.actor for n in artifact.graph.nodes], ['UNSPECIFIED', 'SELF', 'UNSPECIFIED'])
        self.assertFalse(artifact.graph.conflicts)
        helper = existing.AnalysisVerticalTests()
        same = helper.compared('同僚からの資料を調べた。', '同僚からの資料を調べました。').artifact
        self.assertFalse(same.period_comparison.change_claims)
        for new in ('私は同僚からの資料を調べた。', '同僚からの資料を調べなかった。'):
            compared = helper.compared('同僚からの資料を調べた。', new).artifact
            self.assertIn('ROUTE_EVIDENCE_CHANGED', compared.safe_projection(
                authenticated_owner_scope=OWNER)['period_comparison']['safe_change_kinds'])

    def test_omitted_actor_route_keeps_written_order_day_and_unknown_gaps(self):
        artifact = self.generate(request(record(memo='私は職場にいた。その後、資料を調べた。それから、私は安心した。'))).artifact
        self.assertEqual([n.proposition.actor for n in artifact.graph.nodes], ['SELF', 'UNSPECIFIED', 'SELF'])
        self.assertEqual(len(artifact.graph.edges), 2)
        self.assertTrue(all(e.edge_kind == 'OBSERVED_ORDER' for e in artifact.graph.edges))
        self.assertIn('原因を示す線ではありません', artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'])
        for req in (request(record(memo='資料を調べた。不明な出来事がある。その後、私は安心した。')),
                    request(record(memo='資料を調べた。', action='その後、私は記録を残した。')),
                    request(record(memo='資料を調べた。'), record(2, memo='その後、私は安心した。'))):
            artifact = self.generate(req).artifact
            self.assertEqual(len(artifact.graph.nodes), 2)
            self.assertFalse(artifact.graph.edges)
        for day, marker in (('今日', 'TODAY'), ('昨日', 'YESTERDAY')):
            artifact = self.generate(request(record(memo=day + '、資料を調べなかった。'))).artifact
            self.assertEqual(artifact.graph.nodes[0].proposition.relative_day, marker)
            self.assertIn('この記述時点の' + day, artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'])

    def test_omitted_actor_requires_closed_past_object_and_unreported_source(self):
        for clause in ('調べた', '職場で調べた', '友人は資料を調べた', '何を調べた',
                '資料を調べる', '資料を調べたい', '資料を調べられなかった', '資料を調べていた',
                '資料を調べた後、安心した', '資料を調べてから、不安が減った',
                '今回は事前に資料を調べた', '明日資料を調べた', '昨日分の資料を調べた',
                '資料を調べたかもしれない', '資料を調べなければならなかった'):
            with self.subTest(clause=clause):
                self.assertIsNone(self.generate(request(record(memo=clause + '。'))).artifact)
        for clause in ('資料を調べた', '家族への手紙を書きませんでした'):
            for host in ('友人は言いました。', '友人の話でした。', '友人は話していました。', '夢を見た。'):
                for req in (request(record(memo=host + clause + '。')),
                            request(record(memo=host, action=clause + '。')),
                            request(record(memo=clause + '。', action=host))):
                    with self.subTest(clause=clause, host=host):
                        self.assertIsNone(self.generate(req).artifact)
            for suffix in ('と友人が言った。', 'と私は思う。', 'わけではない。', 'のは嘘だった。'):
                artifact = self.generate(request(record(memo=clause + '。' + suffix
                    + 'その後、私は記録を残した。'))).artifact
                self.assertEqual([n.proposition.predicate_lemma for n in artifact.graph.nodes], ['残す'])
                self.assertFalse(artifact.graph.edges)

    def test_omitted_actor_correction_withdrawal_and_projection_keep_uncertainty(self):
        helper = existing.AnalysisVerticalTests()
        old = '同僚からの資料を調べた'
        original = record(memo=old + '。その後、私は記録を残した。')
        for new, actor, polarity in (('同僚への資料を調べなかった', 'UNSPECIFIED', 'negative'),
                                     ('私は同僚からの資料を調べた', 'SELF', 'positive')):
            req = request(helper.with_answer(original, '「' + old + '」ではなく「' + new + '」です。'))
            artifact = self.generate(req).artifact
            self.assertIsNotNone(artifact)
            node = next(n for n in artifact.graph.nodes if n.update_refs)
            self.assertEqual((node.proposition.actor, node.polarity), (actor, polarity))
            self.assertFalse(artifact.graph.edges)
            artifact.safe_projection(authenticated_owner_scope=OWNER)
        withdrawn = self.generate(request(helper.with_answer(original, '「' + old + '」は取り消します。'))).artifact
        self.assertEqual([n.proposition.predicate_lemma for n in withdrawn.graph.nodes], ['残す'])
        self.assertFalse(withdrawn.graph.edges)
        artifact = self.generate(request(record(memo=old + '。'))).artifact
        node, = artifact.graph.nodes
        invalid = replace(artifact, graph=replace(artifact.graph, nodes=(replace(node,
            proposition=replace(node.proposition, actor='SELF')),)))
        with self.assertRaises(existing.AnalysisSourceError):
            invalid.safe_projection(authenticated_owner_scope=OWNER)

    def test_omitted_actor_does_not_discard_a_split_written_topic(self):
        for prefix in ('', '昨日、', 'その後、'):
            for boundary in ('\n', '\r\n', '。'):
                with self.subTest(prefix=prefix, boundary=boundary):
                    self.assertIsNone(self.generate(request(record(memo=prefix
                        + '私は、' + boundary + '資料を調べた。'))).artifact)
        self.assertIsNone(self.generate(request(record(memo='昨日、私は、',
            action='資料を調べた。'))).artifact)

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
            '友人は同僚からの資料を調べた',
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
