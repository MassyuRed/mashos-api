"""Public source contrasts: a closed utterance never supplies an owner's fact."""
import unittest
import json
from pathlib import Path
import tempfile
from unittest.mock import AsyncMock, patch
from uuid import UUID

from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from test_cmee_analysis_v1d_vertical import OWNER, record, request
from cocolon_meaning_experience_engine.cores.analysis.source_adapter import freeze_analysis_sources


class ClosedQuoteSelfActionTests(unittest.TestCase):
    def generate(self, text, action=''):
        return MeaningExperienceEngine().generate(request(record(memo=text, action=action)))

    def assert_self_action(self, text, expected):
        result = self.generate(text)
        self.assertIsNotNone(result.artifact, result.reason_codes)
        artifact = result.artifact
        self.assertEqual([n.visible_label for n in artifact.graph.nodes], expected)
        self.assertIn('SOURCE_SCOPE', [g.missing_scope for g in artifact.graph.unknown_gaps])
        source, = freeze_analysis_sources(request(record(memo=text))).sources
        for node in artifact.graph.nodes:
            self.assertEqual(node.proposition.actor, 'SELF')
            for evidence in node.evidence_refs:
                self.assertEqual(text[evidence.scalar_start:evidence.scalar_end], node.visible_label)
                self.assertEqual(source.envelope.raw_utf8[evidence.utf8_start:evidence.utf8_end].decode(),
                                 node.visible_label)
        value = artifact.safe_text_projection(authenticated_owner_scope=OWNER)
        diagram = artifact.safe_projection(authenticated_owner_scope=OWNER)
        self.assertIn('まだ読み取れていない', value['text'])
        self.assertTrue(diagram['unknown_gaps'])
        self.assertFalse(artifact.graph.edges)
        return artifact

    def test_closed_past_speech_preserves_independent_positive_and_negative_actions(self):
        for speaker in ('受付の人', '友人', '親しい新しい友人'):
            for speech in ('言った', '説明しました'):
                for action in ('私は資料を調べた', '私は資料を調べなかった'):
                    with self.subTest(speaker=speaker, speech=speech, action=action):
                        self.assert_self_action(speaker + 'は「会議室を確保しました」と'
                            + speech + '。' + action + '。', [action])

    def test_quoted_self_content_and_speculation_never_become_owner_actions(self):
        for content in ('私は記録を残した', '私は記録を残した。私は予定を決めた',
                        '準備には二日ほど必要かもしれません'):
            with self.subTest(content=content):
                self.assert_self_action('友人は「' + content + '」と言った。私は資料を調べた。',
                                        ['私は資料を調べた'])

    def test_unread_utterance_between_actions_does_not_create_an_order_edge(self):
        self.assert_self_action('私は予定を書いた。友人は「記録を残した」と言った。'
                                '私は資料を調べた。', ['私は予定を書いた', '私は資料を調べた'])

    def test_open_nested_or_nonpast_speech_does_not_release_owner_claims(self):
        for host in ('友人は「私は記録を残した」と言う。',
                     '友人は「私は記録を残した」と言わなかった。',
                     '友人は「私は記録を残した」と言っていた。',
                     '友人は「私は記録を残した」と言ったなら、',
                     '友人は「私は記録を残した。',
                     '友人は「姉は「私は記録を残した」と言った」と言った。',
                     '友人は言う。姉は「準備ができた」と言った。',
                     '友人が話した！受付の人は「会議室を確保しました」と言った。',
                     '受付の人は「会議室を確保しました」と言った。わけではない。',
                     '受付の人は「会議室を確保しました」と言った。のは嘘だった。',
                     '受付の人は「会議室を確保しました」と言った。そういう話だ。',
                     '聞いた内容は、友人は「準備ができた」と言った。',
                     '夢を見た。友人は「準備ができた」と言った。'):
            with self.subTest(host=host):
                result = self.generate(host + '私は資料を調べた。')
                self.assertIsNone(result.artifact)

    def test_other_field_quote_does_not_close_an_open_speaker(self):
        result = self.generate('友人は「準備ができた」と言った。', '私は資料を調べた。')
        self.assertIsNone(result.artifact)

    def test_quoted_supplement_is_not_treated_as_completely_read(self):
        import test_cmee_analysis_v1d_vertical as vertical
        original = record(memo='私は記録を残した。')
        member = vertical.AnalysisVerticalTests().with_answer(original,
            '友人は「準備ができた」と言った。私は資料を調べた。')
        result = MeaningExperienceEngine().generate(request(member))
        self.assertIsNone(result.artifact)

    def test_targeted_withdrawal_and_replacement_keep_unread_quote_scope(self):
        import test_cmee_analysis_v1d_vertical as vertical
        original = record(memo='友人は「準備ができた」と言った。私は資料を調べた。')
        helper = vertical.AnalysisVerticalTests()
        withdrawn = MeaningExperienceEngine().generate(request(helper.with_answer(original,
            '「私は資料を調べた」は取り消します。')))
        self.assertIsNone(withdrawn.artifact)
        revised = MeaningExperienceEngine().generate(request(helper.with_answer(original,
            '「私は資料を調べた」ではなく「私は資料を見た」です。')))
        self.assertIsNotNone(revised.artifact, revised.reason_codes)
        self.assertEqual([n.visible_label for n in revised.artifact.graph.nodes], ['私は資料を見た'])
        self.assertTrue(revised.artifact.graph.source_updates)
        self.assertIn('SOURCE_SCOPE', [g.missing_scope for g in revised.artifact.graph.unknown_gaps])


class ClosedQuoteSavedReadTests(unittest.IsolatedAsyncioTestCase):
    async def test_normal_saved_wire_keeps_text_diagram_and_unknown_without_generation(self):
        import analysis_cumulative_service as service
        import test_analysis_cumulative as cumulative
        from cocolon_meaning_experience_engine.cores.analysis import intent_compiler, observed_route_realizer
        snapshot = cumulative.source_snapshot(1)
        snapshot['members'][0]['original']['memo'] = (
            '受付の人は「会議室を確保しました」と言った。私は資料を調べた。')
        artifact, coverage = service.build_cumulative_map(cumulative.OWNER, snapshot)
        self.assertIsNotNone(artifact)
        self.assertEqual(coverage['mapped_count'], 1)
        self.assertEqual(coverage['unparsed_count'], 1)
        projection = artifact.safe_projection(authenticated_owner_scope=cumulative.OWNER)
        text = artifact.safe_text_projection(authenticated_owner_scope=cumulative.OWNER)['text']
        self.assertIn('まだ読み取れていない', text)
        row = dict(id=str(UUID(artifact.artifact_id[9:])), source_profile='cumulative.v1',
            report_mode='standard', content_text=text, content_json=dict(report_mode='standard',
                watashiMap=projection, map_context=coverage))
        expected = dict(items=[row], subscription_tier='free', matched=True, history_limit=2)
        with tempfile.TemporaryDirectory() as folder:
            saved = Path(folder) / 'saved.json'
            saved.write_text(json.dumps(expected, ensure_ascii=False))
            rpc = AsyncMock(return_value=json.loads(saved.read_text()))
            forbidden = AssertionError('saved read must not regenerate')
            with patch.object(service, '_rpc', rpc), \
                 patch.object(MeaningExperienceEngine, 'generate', side_effect=forbidden), \
                 patch.object(intent_compiler, 'compile_observed_graph', side_effect=forbidden), \
                 patch.object(observed_route_realizer, 'generate_observed_map', side_effect=forbidden):
                loaded = await service.read_maps(cumulative.OWNER, report_id=row['id'])
        self.assertEqual(loaded, expected)
        self.assertEqual(rpc.await_args.args[1]['p_user_id'], cumulative.OWNER)

if __name__ == '__main__':
    unittest.main()
