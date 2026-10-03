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
        self.assertNotEqual(visual['wire_kind'], artifact.safe_projection(
            authenticated_owner_scope=OWNER)['wire_kind'])
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

    def test_explicit_sequence_reaches_safe_text_and_graph_with_exact_evidence(self):
        for marker in ('その後、', 'それから', 'その後\u3000'):
            with self.subTest(marker=marker):
                req = request(record(memo='\u3000私は資料を調べた。\n' + marker
                    + '私は考えをノートに書いた。'))
                artifact = self.generate(req).artifact
                visual = artifact.safe_projection(authenticated_owner_scope=OWNER)
                text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)
                self.assertEqual(len(visual['edges']), 1)
                self.assertEqual(visual['edges'][0]['edge_kind'], 'OBSERVED_ORDER')
                self.assertEqual((visual['edges'][0]['from_ref'], visual['edges'][0]['to_ref']),
                                 ('n1', 'n2'))
                self.assertEqual([n['visible_label'] for n in visual['nodes']],
                    ['資料を調べる（実行済み）',
                     marker.rstrip('、\u3000') + '：考えをノートに書く（実行済み）'])
                self.assertEqual(visual['projection_of'], text['projection_of'])
                self.assertIn('原因を示す線ではありません', text['text'])
                self.assertFalse(any(g.missing_scope == 'ROUTE_CONNECTION'
                                     for g in artifact.graph.unknown_gaps))
                sources = {s.envelope.envelope_id: s for s in freeze_analysis_sources(req).sources}
                edge = artifact.graph.edges[0]
                self.assertEqual(len(edge.evidence_refs), 2)
                for evidence in edge.evidence_refs:
                    envelope = sources[evidence.source_envelope_id].envelope
                    literal = envelope.raw_utf8[evidence.utf8_start:evidence.utf8_end]
                    field = envelope.raw_utf8[evidence.field_utf8_start:evidence.field_utf8_end].decode()
                    self.assertEqual(literal.decode(), field[evidence.scalar_start:evidence.scalar_end])
                    self.assertEqual(hashlib.sha256(literal).hexdigest(), evidence.literal_sha256)
                for private in (OWNER, 'analysis-source:', 'synthetic-record-', 'sha256:', '私は'):
                    self.assertNotIn(private, json.dumps(visual, ensure_ascii=False))

    def test_repeated_actions_keep_sequence_occurrences_without_self_edges_or_cycles(self):
        memo = ('私は資料を調べた。その後私は考えをノートに書いた。'
                'それから私は資料を調べた。')
        artifact = self.generate(request(record(memo=memo), record(2, memo=memo))).artifact
        visual = artifact.safe_projection(authenticated_owner_scope=OWNER)
        self.assertEqual(len(visual['nodes']), 6)
        self.assertTrue(all(n['evidence_badge_count'] == 1 for n in visual['nodes']))
        self.assertEqual([(e['from_ref'], e['to_ref']) for e in visual['edges']],
                         [('n1', 'n2'), ('n2', 'n3'), ('n4', 'n5'), ('n5', 'n6')])
        repeated = self.generate(request(record(memo=
            '私は資料を調べた。その後私は資料を調べた。'))).artifact
        self.assertEqual(len(repeated.graph.nodes), 2)
        self.assertEqual(repeated.graph.edges[0].endpoint_refs, ('n1', 'n2'))

    def test_unmarked_order_and_distinct_fields_or_sources_cannot_create_sequence(self):
        cases = [
            request(record(memo='私は資料を調べた。私は記録を残した。')),
            request(record(memo='私は資料を調べた。', action='その後私は記録を残した。')),
            request(record(memo='私は資料を調べた。'), record(2, memo='その後私は記録を残した。')),
            request(self.with_answer(record(memo='私は資料を調べた。'),
                                     'その後私は記録を残した。')),
        ]
        for req in cases:
            with self.subTest():
                artifact = self.generate(req).artifact
                self.assertIsNotNone(artifact)
                self.assertFalse(artifact.safe_projection(authenticated_owner_scope=OWNER)['edges'])
                self.assertTrue(any(g.missing_scope == 'ROUTE_CONNECTION'
                                    for g in artifact.graph.unknown_gaps))

    def test_unread_clause_cannot_be_skipped_by_sequence(self):
        artifact = self.generate(request(record(memo=
            '私は資料を調べた。まだわからない。その後私は記録を残した。'))).artifact
        self.assertFalse(artifact.safe_projection(authenticated_owner_scope=OWNER)['edges'])
        self.assertIn('SOURCE_SCOPE', [g.missing_scope for g in artifact.graph.unknown_gaps])
        self.assertIn('ROUTE_CONNECTION', [g.missing_scope for g in artifact.graph.unknown_gaps])

    def test_sequence_retains_negation_and_does_not_promote_wish_to_action(self):
        artifact = self.generate(request(record(memo=
            '私は資料を調べませんでした。その後私は記録を残した。'))).artifact
        visual = artifact.safe_projection(authenticated_owner_scope=OWNER)
        self.assertIn('行わなかった', visual['nodes'][0]['visible_label'])
        self.assertEqual(len(visual['edges']), 1)
        for memo in ('私は仕事を続けたい。その後私は記録を残した。',
                     '私は資料を調べた。その後私は仕事を続けたい。',
                     '私は資料を調べた。それから私は仕事を続けたい。'):
            with self.subTest(memo=memo):
                artifact = self.generate(request(record(memo=memo))).artifact
                visual = artifact.safe_projection(authenticated_owner_scope=OWNER)
                self.assertFalse(visual['edges'])
                wish = next(n for n in visual['nodes'] if n['node_kind'] == 'ATTENTION_OR_THOUGHT')
                self.assertIn('希望', wish['visible_label'])
                if 'それから' in memo:
                    self.assertEqual(wish['visible_label'], 'それから：仕事を続けることへの希望')

    def test_local_sequence_in_ordinary_answer_keeps_answer_provenance(self):
        req = request(self.with_answer(record(memo='私は記録を残した。'),
            '私は資料を調べた。その後私は考えをノートに書いた。'))
        artifact = self.generate(req).artifact
        self.assertEqual(len(artifact.graph.edges), 1)
        self.assertEqual(artifact.graph.edges[0].endpoint_refs, ('n2', 'n3'))
        sources = {s.envelope.envelope_id: s for s in freeze_analysis_sources(req).sources}
        self.assertTrue(all(sources[e.source_envelope_id].envelope.source_role == 'SUPPLEMENTAL_ANSWER'
                            for e in artifact.graph.edges[0].evidence_refs))
        self.assertTrue(all(len(n.record_refs) == 1 for n in artifact.graph.nodes))
        artifact.safe_projection(authenticated_owner_scope=OWNER)

    def test_withdrawal_or_replacement_does_not_restore_original_sequence(self):
        original = record(memo='私は資料を調べた。その後私は記録を残した。')
        for answer in ('「私は資料を調べた」は取り消します。',
                       '「その後私は記録を残した」は取り消します。',
                       '「私は資料を調べた」ではなく「私は資料を調べなかった」です。'):
            with self.subTest(answer=answer):
                artifact = self.generate(request(self.with_answer(original, answer))).artifact
                self.assertIsNotNone(artifact)
                self.assertFalse(artifact.safe_projection(authenticated_owner_scope=OWNER)['edges'])
                self.assertEqual(len(artifact.graph.source_updates), 1)
        chain = record(memo='私は資料を調べた。その後私は考えを書いた。それから私は記録を残した。')
        artifact = self.generate(request(self.with_answer(chain,
            '「その後私は考えを書いた」は取り消します。'))).artifact
        self.assertFalse(artifact.safe_projection(authenticated_owner_scope=OWNER)['edges'])

    def test_sequence_resolves_only_its_pair_and_orphan_connective_keeps_gap(self):
        artifact = self.generate(request(record(memo=
            '私は資料を調べた。その後私は考えを書いた。私は記録を残した。'))).artifact
        self.assertEqual([e.endpoint_refs for e in artifact.graph.edges], [('n1', 'n2')])
        self.assertEqual([g.between_node_refs for g in artifact.graph.unknown_gaps
                          if g.missing_scope == 'ROUTE_CONNECTION'], [('n2', 'n3')])
        orphan = self.generate(request(record(memo='その後私は記録を残した。'))).artifact
        self.assertFalse(orphan.graph.edges)
        self.assertTrue(any(g.reason_code == 'EXPLICIT_PREDECESSOR_NOT_ESTABLISHED'
                            for g in orphan.graph.unknown_gaps))
        self.assertIn('その後：', orphan.safe_projection(authenticated_owner_scope=OWNER)
                      ['nodes'][0]['visible_label'])

    def test_sequence_does_not_admit_other_speaker_quote_question_or_condition(self):
        for memo in ('私は資料を調べた。その後友人は記録を残した。',
                     '私は資料を調べた。その後私は記録を残した？',
                     '私は資料を調べた。その後「私は記録を残した」と聞いた。',
                     '私は資料を調べた。もしその後私は記録を残したなら、安心できる。'):
            with self.subTest(memo=memo):
                result = self.generate(request(record(memo=memo)))
                self.assertFalse(result.artifact and result.artifact.graph.edges)

    def test_application_mode_is_not_enabled(self):
        result = self.generate(replace(request(record()), execution_mode='ANALYSIS_APPLICATION'))
        self.assertEqual(result.status, EngineStatus.REJECTED)

    def test_empty_period_does_not_invent_route(self):
        self.assertEqual(self.generate(request()).status, EngineStatus.UNAVAILABLE)

    def test_existing_emlis_invalid_request_dispatch_is_preserved(self):
        result = self.generate(GenerationRequest('', {}, 'synthetic-record'))
        self.assertEqual(result.status, EngineStatus.REJECTED)
        self.assertEqual(result.reason_codes, ('request_id_required',))

    def with_answer(self, original, text):
        answer = AnalysisSupplement('synthetic-answer', OWNER,
            original.saved_record_ref, original.saved_record_version,
            text, commitment(text))
        return replace(original, supplements=(answer,))

    def test_ordinary_answer_adds_own_wish_to_same_record_and_safe_text(self):
        original = record(memo='私は考えをノートに書いた。')
        answered = self.with_answer(original, '　私は仕事を続けたい。\n')
        req = request(answered)
        result = self.generate(req)
        self.assertEqual(result.status, EngineStatus.GENERATED)
        artifact = result.artifact
        visual = artifact.safe_projection(authenticated_owner_scope=OWNER)
        text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)
        self.assertEqual([n['visible_label'] for n in visual['nodes']],
            ['考えをノートに書く（実行済み）', '仕事を続けることへの希望'])
        self.assertEqual([n['evidence_badge_count'] for n in visual['nodes']], [1, 1])
        self.assertFalse(visual['edges'])
        self.assertFalse(artifact.graph.source_updates)
        self.assertEqual(original.original_json, answered.original_json)
        self.assertEqual(visual['projection_of'], text['projection_of'])
        for node in visual['nodes']:
            self.assertIn(node['visible_label'], text['text'])
        wish = artifact.graph.nodes[1]
        source = next(s for s in freeze_analysis_sources(req).sources
                      if s.envelope.source_role == 'SUPPLEMENTAL_ANSWER')
        for evidence in wish.evidence_refs:
            self.assertEqual(evidence.source_envelope_id, source.envelope.envelope_id)
            raw = source.envelope.raw_utf8[evidence.utf8_start:evidence.utf8_end]
            field = source.envelope.raw_utf8[
                evidence.field_utf8_start:evidence.field_utf8_end].decode()
            self.assertEqual(raw.decode(), field[evidence.scalar_start:evidence.scalar_end])
            self.assertIn('私は仕事を続けたい', raw.decode())
            self.assertEqual(hashlib.sha256(raw).hexdigest(), evidence.literal_sha256)

    def test_answer_can_add_multiple_complete_claims_without_inventing_order(self):
        answered = self.with_answer(record(memo='私は考えをノートに書いた。'),
            '私は資料を調べました。私は仕事を続けたくない。')
        artifact = self.generate(request(answered)).artifact
        self.assertIsNotNone(artifact)
        self.assertEqual([n['visible_label'] for n in artifact.safe_projection(
            authenticated_owner_scope=OWNER)['nodes']],
            ['考えをノートに書く（実行済み）', '資料を調べる（実行済み）',
             '仕事を続けることを望まない'])
        self.assertFalse(artifact.graph.edges)

    def test_answer_restatement_is_one_claim_and_never_self_cooccurrence(self):
        answered = self.with_answer(record(memo='私は図書館で資料を調べた。'),
            '僕は資料を図書館で調べました。')
        for members, count in [((answered,), 1),
                ((answered, record(2, memo='わたしは資料を図書館で調べました。')), 2)]:
            with self.subTest(count=count):
                artifact = self.generate(request(*members)).artifact
                self.assertEqual(len(artifact.graph.nodes), 1)
                node = artifact.graph.nodes[0]
                self.assertEqual(len(node.evidence_refs), count + 1)
                visual = artifact.safe_projection(authenticated_owner_scope=OWNER)
                self.assertEqual(visual['nodes'][0]['evidence_badge_count'], count)
                self.assertFalse(visual['edges'])

    def test_repeated_original_and_answer_claims_require_independent_records(self):
        first = self.with_answer(record(memo='私は資料を調べた。'), '私は仕事を続けたい。')
        second = self.with_answer(record(2, memo='私は資料を調べました。'), '僕は仕事を続けたいです。')
        second = replace(second, supplements=(replace(second.supplements[0],
                         source_id='synthetic-second-answer'),))
        artifact = self.generate(request(first, second)).artifact
        visual = artifact.safe_projection(authenticated_owner_scope=OWNER)
        self.assertEqual([n['evidence_badge_count'] for n in visual['nodes']], [2, 2])
        self.assertEqual(len(visual['edges']), 1)
        self.assertEqual(visual['edges'][0]['edge_kind'], 'REPEATED_COOCCURRENCE')
        self.assertNotIn('from_ref', visual['edges'][0])

    def test_ordinary_answer_must_not_drop_uninterpreted_or_corrective_text(self):
        answers = [
            '私は資料を調べた。でも、元の記録は間違いです。',
            '違います。私は資料を調べた。',
            '私は資料を調べた。まだわからない。',
            '私は資料を調べた。友人は仕事を続けたい。',
            '私は資料を調べた？',
            '友人の話です。私は資料を調べた。',
            '「私は資料を調べた」と聞いた。',
            'もし私は資料を調べたなら、安心できる。',
            '私は昨日、資料を調べた。',
            '私は資料を調べた。※',
        ]
        for answer in answers:
            with self.subTest(answer=answer):
                result = self.generate(request(self.with_answer(record(), answer), record(2)))
                self.assertEqual(result.status, EngineStatus.UNAVAILABLE)
                self.assertIsNone(result.artifact)

    def test_ordinary_answer_cannot_silently_choose_opposite_claim(self):
        cases = [
            ('私は図書館で資料を調べた。', '私は資料を図書館で調べなかった。'),
            ('私は図書館で資料を調べた。', '私は調べなかった。'),
            ('私は仕事を続けたい。', '私は仕事を続けたくない。'),
            ('私は考えをノートに書いた。',
             '私は資料を調べた。私は資料を調べなかった。'),
        ]
        for original, answer in cases:
            with self.subTest(original=original, answer=answer):
                result = self.generate(request(self.with_answer(record(memo=original), answer)))
                self.assertEqual(result.status, EngineStatus.UNAVAILABLE)
                self.assertIsNone(result.artifact)

    def test_distinct_answer_objects_and_modalities_are_not_merged(self):
        answered = self.with_answer(record(memo='私は資料を調べた。'),
            '私は書類を調べなかった。私は資料を調べたい。')
        artifact = self.generate(request(answered)).artifact
        visual = artifact.safe_projection(authenticated_owner_scope=OWNER)
        self.assertEqual([n['visible_label'] for n in visual['nodes']],
            ['資料を調べる（実行済み）', '書類を調べる（行わなかった）',
             '資料を調べることへの希望'])
        self.assertFalse(visual['edges'])

    def test_withdrawal_removes_only_parent_occurrence_and_recomputes_cooccurrence(self):
        original = record()
        corrected = self.with_answer(original, '「私は考えをノートに書いた」は取り消します。')
        artifact = self.generate(request(corrected, record(2))).artifact
        action = next(n for n in artifact.graph.nodes if n.node_kind == 'ACTION_OR_NONACTION')
        self.assertEqual(action.record_refs, ('synthetic-record-2',))
        self.assertFalse(artifact.graph.edges)
        self.assertEqual(artifact.graph.source_updates[0].operation, 'WITHDRAW')
        self.assertEqual(original.original_json, corrected.original_json)
        one = self.generate(request(corrected)).artifact
        self.assertEqual([n.node_kind for n in one.graph.nodes], ['ATTENTION_OR_THOUGHT'])

    def test_replacement_preserves_negation_and_exact_supplement_ranges(self):
        corrected = self.with_answer(record(),
            '　「私は考えをノートに書いた」ではなく「私は考えをノートに書かなかった」です。')
        req = request(corrected)
        artifact = self.generate(req).artifact
        node = next(n for n in artifact.graph.nodes if n.node_kind == 'ACTION_OR_NONACTION')
        self.assertEqual((node.polarity, node.modality, node.temporal_scope),
                         ('negative', 'fact', 'past'))
        self.assertTrue(node.update_refs)
        sources = {s.envelope.envelope_id: s for s in freeze_analysis_sources(req).sources}
        for evidence in node.evidence_refs:
            source = sources[evidence.source_envelope_id]
            self.assertEqual(source.envelope.source_role, 'SUPPLEMENTAL_ANSWER')
            literal = source.envelope.raw_utf8[evidence.utf8_start:evidence.utf8_end]
            self.assertEqual(literal.decode(), '私は考えをノートに書かなかった')
            self.assertEqual(hashlib.sha256(literal).hexdigest(), evidence.literal_sha256)
        self.assertNotIn('ACTION_OR_NONACTION', [g.missing_scope for g in artifact.graph.unknown_gaps])
        self.assertEqual(artifact.graph.source_updates[0].operation, 'REVISE')

    def test_replacement_does_not_inherit_old_negation_or_wish(self):
        original = record(memo='私は考えをノートに書かなかった。')
        corrected = self.with_answer(original,
            '「私は考えをノートに書かなかった」ではなく「私は考えをノートに書いた」です。')
        node = self.generate(request(corrected)).artifact.graph.nodes[0]
        self.assertEqual((node.polarity, node.modality), ('positive', 'fact'))
        corrected = self.with_answer(record(),
            '「私は仕事を続けたい」ではなく「私は仕事を続けたくない」です。')
        node = next(n for n in self.generate(request(corrected)).artifact.graph.nodes
                    if n.node_kind == 'ATTENTION_OR_THOUGHT')
        self.assertEqual((node.polarity, node.modality), ('negative', 'wish'))

    def test_correction_requires_unique_whole_parent_clause(self):
        examples = [
            (record(), '「考えをノートに書いた」は取り消します。'),
            (record(memo=TEXT, action='私は考えをノートに書いた。'),
             '「私は考えをノートに書いた」は取り消します。'),
            (record(), '友人は「私は考えをノートに書いた」は取り消しますと言った。'),
            (record(), '違います。'),
            (record(), '「私は考えをノートに書いた」ではなく「まだわからない」です。'),
        ]
        for original, text in examples:
            with self.subTest(text=text):
                result = self.generate(request(self.with_answer(original, text), record(2)))
                self.assertEqual(result.status, EngineStatus.UNAVAILABLE)
                self.assertIsNone(result.artifact)

    def test_owner_projection_reconstructs_whole_meaning_without_raw_body(self):
        artifact = self.generate(request(record(), record(2))).artifact
        visual = artifact.safe_projection(authenticated_owner_scope=OWNER)
        text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)
        self.assertEqual(visual['schema_version'],
            'cocolon.cmee.analysis_watashi_map_safe_projection.v1alpha1')
        self.assertEqual(visual['wire_kind'], 'watashi.map.v2')
        self.assertEqual([n['visible_label'] for n in visual['nodes']],
            ['考えをノートに書く（実行済み）', '仕事を続けることへの希望'])
        self.assertEqual(visual['projection_of'], text['projection_of'])
        self.assertEqual(visual['accessibility_linear_order'], text['accessibility_linear_order'])
        self.assertIn('順序や原因は確定していません', text['text'])
        for node in visual['nodes']:
            self.assertIn(node['visible_label'], text['text'])
        for raw in (TEXT, OWNER, '私は', 'synthetic-record', 'analysis-source:', 'sha256:'):
            self.assertNotIn(raw, json.dumps(visual, ensure_ascii=False))
        self.assertNotIn('text', visual)
        self.assertEqual(set(visual['nodes'][0]),
            {'node_ref', 'node_kind', 'visible_label', 'evidence_badge_count'})

    def test_correction_cannot_reassign_reported_speaker_or_question_to_self(self):
        for original in (
            record(memo='友人の話です。私は考えをノートに書いた。'),
            record(memo='私は考えをノートに書いた。', action='友人の報告です。'),
            record(memo='私は考えをノートに書いた？'),
        ):
            corrected = self.with_answer(original,
                '「私は考えをノートに書いた」ではなく「私は考えをノートに書かなかった」です。')
            result = self.generate(request(corrected, record(2)))
            self.assertEqual(result.status, EngineStatus.UNAVAILABLE)
            self.assertIsNone(result.artifact)

    def test_surface_keeps_all_arguments_and_finite_operators(self):
        cases = [
            ('私は図書館で資料を調べました。', '図書館で資料を調べる（実行済み）'),
            ('私は仕事を続けたかった。', '仕事を続けることへの希望（当時）'),
            ('私は記録を残しませんでした。', '記録を残す（行わなかった）'),
            ('私は私の考えをノートに書いた。', '私の考えをノートに書く（実行済み）'),
        ]
        for source, label in cases:
            with self.subTest(source=source):
                artifact = self.generate(request(record(memo=source))).artifact
                self.assertIsNotNone(artifact)
                self.assertEqual(artifact.safe_projection(authenticated_owner_scope=OWNER)
                    ['nodes'][0]['visible_label'], label)

    def test_safe_surface_cannot_drop_modifiers_or_accept_altered_parts(self):
        for source in ('私は昨日、考えをノートに書いた。',
                       '私は急いで考えをノートに書いた。'):
            with self.subTest(source=source):
                artifact = self.generate(request(record(memo=source))).artifact
                self.assertIsNotNone(artifact)
                with self.assertRaisesRegex(AnalysisSourceError, 'analysis_safe_surface_unavailable'):
                    artifact.safe_projection(authenticated_owner_scope=OWNER)
        artifact = self.generate(request(record())).artifact
        node = artifact.graph.nodes[0]
        broken = replace(artifact, graph=replace(artifact.graph,
            nodes=(replace(node, proposition=replace(node.proposition, polarity='negative')),)))
        with self.assertRaisesRegex(AnalysisSourceError, 'analysis_safe_surface_unavailable'):
            broken.safe_projection(authenticated_owner_scope=OWNER)


if __name__ == '__main__':
    unittest.main()
