"""Public synthetic inputs only; offline Analysis behavior and source boundaries."""
from dataclasses import FrozenInstanceError, replace
import hashlib
import json
import unittest

from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.contracts import EngineStatus, GenerationRequest
from cocolon_meaning_experience_engine.cores.analysis.source_adapter import (
    AnalysisObservedMapRequest, AnalysisSavedRecord, AnalysisSupplement,
    AnalysisSourceError, canonical_bytes, commitment, freeze_analysis_sources,
)


OWNER = 'synthetic-owner'
TEXT = '私は考えをノートに書いた。私は仕事を続けたい。'


def record(number=1, memo=TEXT, *, action='', created_at=None):
    original = {'id': 'synthetic-record-' + str(number),
        'created_at': created_at or f'2026-10-0{number}T01:00:00Z',
        'memo': memo, 'memo_action': action, 'category': [],
        'emotions': [], 'emotion_details': []}
    return AnalysisSavedRecord(OWNER, original['id'], commitment(original),
                               canonical_bytes(original).decode())


def request(*members):
    return AnalysisObservedMapRequest('synthetic-request', OWNER,
        '2026-10-01T00:00:00Z', '2026-10-03T00:00:00Z', tuple(members))


class AnalysisVerticalTests(unittest.TestCase):
    def generate(self, value):
        return MeaningExperienceEngine().generate(value)

    def test_two_records_generate_matching_text_and_unordered_graph(self):
        result = self.generate(request(record(), record(2)))
        self.assertEqual(result.status, EngineStatus.GENERATED)
        artifact = result.artifact
        visual = artifact.private_visual_preview(authenticated_owner_scope=OWNER)
        text = artifact.private_text_preview(authenticated_owner_scope=OWNER)
        self.assertEqual(visual['projection_of'], text['projection_of'])
        self.assertEqual(visual['accessibility_linear_order'], text['accessibility_linear_order'])
        self.assertEqual(len(visual['nodes']), 2)
        self.assertEqual([n['evidence_badge_count'] for n in visual['nodes']], [2, 2])
        self.assertEqual(visual['edges'][0]['edge_kind'], 'REPEATED_COOCCURRENCE')
        self.assertNotIn('from_ref', visual['edges'][0])
        self.assertIn('順序や原因は確定していません', text['text'])
        self.assertEqual(visual['period_comparison']['state'], 'NO_PREVIOUS')
        self.assertEqual(visual['wire_kind'], 'watashi.map.v2.private-preview')
        self.assertFalse(hasattr(artifact, 'safe_projection'))
        self.assertTrue(visual['unknown_gaps'])
        for node in visual['nodes']:
            self.assertIn(node['visible_label'], text['text'])

    def test_single_record_and_duplicate_do_not_make_trend(self):
        one = record()
        for members in ((one,), (one, one)):
            with self.subTest(count=len(members)):
                artifact = self.generate(request(*members)).artifact
                self.assertEqual(artifact.graph.edges, ())
                self.assertEqual([len(n.record_refs) for n in artifact.graph.nodes], [1, 1])

    def test_wish_remains_thought_not_performed_action(self):
        artifact = self.generate(request(record())).artifact
        wish = next(n for n in artifact.graph.nodes if '続けたい' in n.visible_label)
        self.assertEqual(wish.node_kind, 'ATTENTION_OR_THOUGHT')
        self.assertEqual(wish.modality, 'wish')

    def test_other_person_quote_condition_question_and_future_are_not_actions(self):
        cases = ['友人は考えをノートに書いた。', '私は考えをノートに書きたい。',
            '私は明日、考えをノートに書く予定です。', '私はノートに書いた？',
            'もし私はノートに書いたなら、安心できる。',
            '私は「考えをノートに書いた」と聞いた。',
            '私はノートに書いたかもしれない。']
        for memo in cases:
            with self.subTest(memo=memo):
                result = self.generate(request(record(memo=memo)))
                self.assertFalse(result.artifact and any(
                    n.node_kind == 'ACTION_OR_NONACTION' for n in result.artifact.graph.nodes))

    def test_emotion_in_action_field_is_not_performed_action(self):
        result = self.generate(request(record(memo='', action='嬉しかった。')))
        self.assertEqual(result.status, EngineStatus.UNAVAILABLE)

    def test_open_report_scope_does_not_become_first_person_action(self):
        for memo, action in (
            ('', '友人の報告です。私はノートに書いた。'),
            ('友人によると、私はノートに書いた。', ''),
            ('友人の話です。', '私はノートに書いた。'),
        ):
            with self.subTest(memo=memo, action=action):
                result = self.generate(request(record(memo=memo, action=action)))
                self.assertIsNone(result.artifact)

    def test_unicode_whitespace_exact_evidence(self):
        value = record(memo='\u3000私は考えをノートに書いた。\u3000')
        sources = freeze_analysis_sources(request(value))
        artifact = self.generate(request(value)).artifact
        envelope_by_id = {s.envelope.envelope_id: s.envelope for s in sources.sources}
        for node in artifact.graph.nodes:
            for evidence in node.evidence_refs:
                envelope = envelope_by_id[evidence.source_envelope_id]
                literal = envelope.raw_utf8[evidence.utf8_start:evidence.utf8_end]
                self.assertEqual(hashlib.sha256(literal).hexdigest(), evidence.literal_sha256)
                field = envelope.raw_utf8[evidence.field_utf8_start:evidence.field_utf8_end].decode()
                self.assertEqual(field[evidence.scalar_start:evidence.scalar_end], literal.decode())

    def test_period_is_half_open_and_timezone_aware(self):
        inside = record(created_at='2026-10-01T09:00:00+09:00')
        outside = record(2, created_at='2026-10-03T00:00:00Z')
        sources = freeze_analysis_sources(request(inside, outside))
        self.assertEqual([m.inclusion_status for m in sources.members], ['INCLUDED', 'EXCLUDED'])
        self.assertEqual(len(sources.sources), 1)
        result = self.generate(replace(request(inside), period_end='2026-10-01T00:00:00'))
        self.assertEqual(result.status, EngineStatus.REJECTED)

    def test_owner_deleted_version_and_duplicate_conflict_are_rejected(self):
        one = record()
        changed = record(memo='私は別の考えをノートに書いた。')
        for members in ((replace(one, owner_scope='other'),),
                        (replace(one, record_state='DELETED'),),
                        (replace(one, saved_record_version='sha256:wrong'),),
                        (one, changed)):
            with self.subTest():
                self.assertEqual(self.generate(request(*members)).status, EngineStatus.REJECTED)

    def test_derived_body_or_question_fields_are_rejected(self):
        for key in ('emlis_body', 'question_text', 'simulation_result'):
            one = record()
            original = json.loads(one.original_json)
            original[key] = 'not source'
            result = self.generate(request(replace(one, original_json=canonical_bytes(original).decode(),
                saved_record_version=commitment(original))))
            self.assertEqual(result.status, EngineStatus.REJECTED)

    def test_supplement_binds_to_parent_and_cannot_count_as_an_occasion(self):
        one = record()
        text = '私は先ほどの入力を取り消したい。'
        supplement = AnalysisSupplement('synthetic-answer', OWNER, one.saved_record_ref,
            one.saved_record_version, text, commitment(text))
        value = replace(one, supplements=(supplement,))
        sources = freeze_analysis_sources(request(value))
        self.assertEqual(len(sources.members), 1)
        self.assertEqual([s.envelope.source_role for s in sources.sources],
                         ['ORIGINAL_INPUT', 'SUPPLEMENTAL_ANSWER'])
        result = self.generate(request(value))
        self.assertEqual(result.status, EngineStatus.UNAVAILABLE)
        self.assertEqual(result.reason_codes, ('analysis_supplement_interpretation_pending',))
        self.assertIsNone(result.artifact)
        for bad in (replace(supplement, owner_scope='other'),
                    replace(supplement, parent_record_version='wrong'),
                    replace(supplement, source_version='wrong'),
                    replace(supplement, source_role='EMLIS_BODY')):
            self.assertEqual(self.generate(request(replace(one, supplements=(bad,)))).status,
                             EngineStatus.REJECTED)

    def test_invalid_duplicate_supplement_is_not_skipped(self):
        one = record()
        result = self.generate(request(one, replace(one, supplements=('invalid',))))
        self.assertEqual(result.status, EngineStatus.REJECTED)

    def test_uninterpreted_record_remains_visible_as_missing_scope(self):
        artifact = self.generate(request(record(), record(2, memo='まだわからない。'))).artifact
        self.assertTrue(any(g.missing_scope == 'SOURCE_SCOPE' for g in artifact.graph.unknown_gaps))

    def test_member_identity_is_immutable_and_returned_preview_cannot_change_it(self):
        artifact = self.generate(request(record())).artifact
        with self.assertRaises(FrozenInstanceError):
            artifact.source_members[0].saved_record_version = 'other'
        view = artifact.private_visual_preview(authenticated_owner_scope=OWNER)
        view['nodes'][0]['visible_label'] = 'mutated'
        self.assertNotEqual(artifact.graph.nodes[0].visible_label, 'mutated')

    def test_wrong_projection_owner_is_rejected_and_diagnostics_are_body_free(self):
        result = self.generate(request(record()))
        with self.assertRaises(AnalysisSourceError):
            result.artifact.private_visual_preview(authenticated_owner_scope='other')
        diagnostic = json.dumps(result.as_body_free())
        for secret in (TEXT, OWNER, 'synthetic-record-1'):
            self.assertNotIn(secret, diagnostic)
        visual = json.dumps(result.artifact.private_visual_preview(authenticated_owner_scope=OWNER))
        for private in (OWNER, 'synthetic-record-1', 'analysis-evidence:', 'analysis-source:', 'sha256:'):
            self.assertNotIn(private, visual)

    def test_application_mode_is_not_enabled(self):
        result = self.generate(replace(request(record()), execution_mode='ANALYSIS_APPLICATION'))
        self.assertEqual(result.status, EngineStatus.REJECTED)

    def test_empty_period_does_not_invent_route(self):
        self.assertEqual(self.generate(request()).status, EngineStatus.UNAVAILABLE)

    def test_existing_emlis_invalid_request_dispatch_is_preserved(self):
        result = self.generate(GenerationRequest('', {}, 'synthetic-record'))
        self.assertEqual(result.status, EngineStatus.REJECTED)
        self.assertEqual(result.reason_codes, ('request_id_required',))


if __name__ == '__main__':
    unittest.main()
