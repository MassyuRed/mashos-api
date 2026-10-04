"""Public synthetic inputs only; offline Analysis behavior and source boundaries."""
from dataclasses import FrozenInstanceError, replace
import hashlib
import json
import unittest
from unittest.mock import patch

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

    def compared(self, current, previous):
        old = replace(request(record(3, memo=previous, created_at='2026-09-30T01:00:00Z')),
            period_start='2026-09-29T00:00:00Z', period_end='2026-10-01T00:00:00Z')
        return self.generate(replace(request(record(memo=current)), comparison_previous_request=old))

    def test_period_comparison_ignores_ids_inflection_order_and_dependent_proof_form(self):
        for before, now in (
            ('私は家族を守りたい。', '僕は家族を守りたいです。'),
            ('私は資料を調べた後、疑問が減った。', '私は資料を調べてから、疑問が減った。'),
            ('私は家族を守りたい。私は仕事を続けたい。', '私は仕事を続けたい。私は家族を守りたい。'),
        ):
            with self.subTest(before=before):
                result = self.compared(now, before)
                self.assertEqual(result.status, EngineStatus.GENERATED)
                p = result.artifact.safe_projection(authenticated_owner_scope=OWNER)['period_comparison']
                self.assertEqual(p, {'state': 'COMPARABLE', 'reason_codes': [], 'safe_change_kinds': []})
                self.assertNotEqual(result.artifact.reference, result.previous_artifact.reference)
                self.assertNotEqual(result.artifact.source_set_ref, result.previous_artifact.source_set_ref)
        old = replace(request(record(3, memo='私は家族を守りたい。', created_at='2026-09-30T01:00:00Z')),
            period_start='2026-09-29T00:00:00Z', period_end='2026-10-01T00:00:00Z')
        result = self.generate(replace(request(record(memo='私は家族を守りたい。'),
            record(2, memo='私は家族を守りたい。')), comparison_previous_request=old))
        self.assertEqual(result.artifact.period_comparison.change_claims, ())
        self.assertIn('記録の件数や、読み取れていない内容の変化は判断していません',
            result.artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'])

    def test_period_comparison_detects_written_semantics_without_rating_the_person(self):
        cases = (
            ('私は資料を調べた。', '私は資料を調べなかった。', ['ROUTE_EVIDENCE_CHANGED']),
            ('私は仕事を続けた。', '私は仕事を続けたい。', ['ROUTE_EVIDENCE_CHANGED', 'UNKNOWN_SCOPE_CHANGED']),
            ('私は仕事を続けたい。', '私は仕事を続けたいけれど、私はつらい。', ['ANNOTATION_EVIDENCE_CHANGED']),
            ('私は資料を調べた。', '私は資料を調べた。まだよくわからない。', ['UNKNOWN_SCOPE_CHANGED']),
            ('私は資料を調べた。', '私は資料を調べた。私は資料を調べなかった。',
                ['ROUTE_EVIDENCE_CHANGED', 'UNKNOWN_SCOPE_CHANGED', 'CONFLICT_STATE_CHANGED']),
            ('私は資料を調べた。その後私は記録を残した。',
                '私は記録を残した。その後私は資料を調べた。', ['ROUTE_EVIDENCE_CHANGED']),
        )
        for before, now, kinds in cases:
            with self.subTest(before=before, now=now):
                artifact = self.compared(now, before).artifact
                p = artifact.safe_projection(authenticated_owner_scope=OWNER)['period_comparison']
                self.assertEqual(p['safe_change_kinds'], kinds)
                self.assertIn('改善・悪化や原因を示すものではありません',
                    artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'])

    def test_period_comparison_has_inline_identity_and_evidence_without_public_locators(self):
        result = self.compared('私は生活を守りたい。', '私は家族を守りたい。')
        current, old = result.artifact, result.previous_artifact
        c = current.period_comparison
        self.assertEqual((c.current_artifact_ref, c.current_source_set_ref,
            c.previous_artifact_ref, c.previous_source_set_ref),
            (current.reference, current.source_set_ref, old.reference, old.source_set_ref))
        current_ids = {e.evidence_id for n in current.graph.nodes for e in n.evidence_refs}
        old_ids = {e.evidence_id for n in old.graph.nodes for e in n.evidence_refs}
        for claim in c.change_claims:
            self.assertTrue(claim.evidence_refs)
            self.assertTrue(set(claim.evidence_refs) <= current_ids | old_ids)
            self.assertTrue(set(claim.evidence_refs) & current_ids)
            self.assertTrue(set(claim.evidence_refs) & old_ids)
            self.assertEqual((claim.current_ref, claim.previous_ref), (current.reference, old.reference))
        public = json.dumps(current.safe_projection(authenticated_owner_scope=OWNER))
        for private in (OWNER, old.reference, old.source_set_ref, c.comparison_id, *current_ids, *old_ids):
            self.assertNotIn(private, public)
        with self.assertRaises(AnalysisSourceError):
            current.safe_projection(authenticated_owner_scope='someone-else')

    def test_period_comparison_requires_equal_adjacent_nonoverlapping_windows(self):
        from datetime import timedelta
        from cocolon_meaning_experience_engine.cores.analysis.source_adapter import _time
        for start, end, reason in (
            ('2026-09-28T00:00:00Z', '2026-10-01T00:00:00Z', 'PERIOD_LENGTH_MISMATCH'),
            ('2026-09-30T00:00:00Z', '2026-10-02T00:00:00Z', 'PERIOD_OVERLAP'),
            ('2026-10-03T00:00:00Z', '2026-10-05T00:00:00Z', 'PREVIOUS_PERIOD_NOT_EARLIER'),
            ('2026-09-28T00:00:00Z', '2026-09-30T00:00:00Z', 'PERIOD_NOT_ADJACENT'),
        ):
            with self.subTest(reason=reason):
                old = replace(request(record(3, created_at=(_time(start) + timedelta(hours=1)).isoformat())),
                    period_start=start, period_end=end)
                artifact = self.generate(replace(request(record()), comparison_previous_request=old)).artifact
                c = artifact.period_comparison
                self.assertEqual(c.comparability_state, 'NOT_COMPARABLE')
                self.assertIn(reason, c.reason_codes)
                self.assertEqual(c.change_claims, ())
                self.assertIn('比較できません', artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'])
        # Equivalent UTC bounds expressed in JST are still adjacent.
        old = replace(request(record(3, created_at='2026-09-30T01:00:00Z')),
            period_start='2026-09-29T09:00:00+09:00', period_end='2026-10-01T09:00:00+09:00')
        self.assertEqual(self.generate(replace(request(record()), comparison_previous_request=old))
            .artifact.period_comparison.comparability_state, 'COMPARABLE')
        same_id = replace(old, members=(record(created_at='2026-09-30T01:00:00Z'),))
        self.assertIn('SHARED_RECORD_IDENTITY', self.generate(replace(request(record()),
            comparison_previous_request=same_id)).artifact.period_comparison.reason_codes)

    def test_period_comparison_rejects_other_owner_nested_or_unavailable_previous_source(self):
        old = replace(request(record(3, created_at='2026-09-30T01:00:00Z')),
            period_start='2026-09-29T00:00:00Z', period_end='2026-10-01T00:00:00Z')
        for previous in (replace(old, authenticated_owner_scope='someone-else'),
                replace(old, comparison_previous_request=old), {'text': TEXT},
                replace(old, locale='en-US'), replace(old, members=()),
                replace(old, members=(replace(old.members[0], record_state='DELETED'),))):
            with self.subTest(previous_type=type(previous).__name__):
                result = self.generate(replace(request(record()), comparison_previous_request=previous))
                self.assertIsNone(result.artifact)
                self.assertIsNone(result.previous_artifact)
                self.assertNotEqual(result.status, EngineStatus.GENERATED)

    def test_period_comparison_uses_corrected_previous_sources_and_rejects_broken_binding(self):
        base = record(3, memo='私は家族を守りたい。私は記録を残した。', created_at='2026-09-30T01:00:00Z')
        old = replace(request(self.with_answer(base,
            '「私は家族を守りたい」ではなく「私は生活を守りたい」です。')),
            period_start='2026-09-29T00:00:00Z', period_end='2026-10-01T00:00:00Z')
        artifact = self.generate(replace(request(record(memo='私は生活を守りたい。私は記録を残した。')),
            comparison_previous_request=old)).artifact
        self.assertEqual(artifact.period_comparison.change_claims, ())
        for changes in ({'current_artifact_ref': 'artifact:wrong@1'},
                {'current_source_set_ref': 'wrong'}, {'previous_artifact_ref': artifact.reference},
                {'comparability_state': 'NOT_COMPARABLE'}, {'reason_codes': ('private-raw-text',)}):
            with self.subTest(changes=changes), self.assertRaises(AnalysisSourceError):
                replace(artifact, period_comparison=replace(artifact.period_comparison, **changes))\
                    .safe_projection(authenticated_owner_scope=OWNER)

    def test_protective_wish_preserves_explicit_object_and_full_source(self):
        for subject, noun, ending in (('私', '家族', '守りたい'),
                ('僕', '生活', '守りたいです'), ('わたし', '家族の時間', '守りたい'),
                ('自分', '気持ち', '守りたいです')):
            with self.subTest(subject=subject, noun=noun):
                memo = subject + 'は' + noun + 'を' + ending + '。'
                value = request(record(memo=memo))
                artifact = self.generate(value).artifact
                node, = artifact.graph.nodes
                claim, = artifact.graph.annotations
                self.assertEqual((node.node_kind, node.polarity, node.modality, node.temporal_scope),
                    ('ATTENTION_OR_THOUGHT', 'positive', 'wish', 'current_input'))
                self.assertEqual(node.proposition.arguments, (('を', noun),))
                self.assertEqual((claim.kind, claim.target_ref, claim.annotation_state),
                    ('PROTECTIVE', node.node_ref, 'SOURCE_EXPLICIT_ANNOTATION'))
                self.assertEqual(claim.evidence_refs, node.evidence_refs)
                self.assertEqual(artifact.graph.edges, ())
                self.assertNotIn('SOURCE_SCOPE', [g.missing_scope for g in artifact.graph.unknown_gaps])
                e, = claim.evidence_refs
                envelope = freeze_analysis_sources(value).sources[0].envelope
                literal = envelope.raw_utf8[e.utf8_start:e.utf8_end]
                self.assertEqual(literal.decode(), memo[:-1])
                self.assertEqual(hashlib.sha256(literal).hexdigest(), e.literal_sha256)
                field = envelope.raw_utf8[e.field_utf8_start:e.field_utf8_end].decode()
                self.assertEqual(field[e.scalar_start:e.scalar_end], memo[:-1])
                visual = artifact.safe_projection(authenticated_owner_scope=OWNER)
                self.assertEqual(visual['nodes'][0]['visible_label'], noun + 'を守ることへの希望')
                self.assertIn('実際に守れているかは確定していません', visual['annotation_badges'][0]['visible_label'])
                self.assertIn(visual['annotation_badges'][0]['visible_label'],
                    artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'])

    def test_protective_does_not_infer_other_forms_speakers_or_unread_hosts(self):
        values = ['私は家族を' + ending + '。' for ending in (
            '守った', '守る', '守っている', '守りたかった', '守りたくない',
            '守りたくなかった', '守りたいと思う', '守りたいかもしれない',
            '守りたいと聞いた', '守りたいという夢を見た', '守りたいから、私は仕事を続けた')]
        values += ['家族を守りたい。', '友人は家族を守りたい。',
            '私は何を守りたい。', '私は誰の生活を守りたい。', '私は幾人を守りたい。',
            '私は家族を絶対に守りたい。', '私は家族も守りたい。',
            '今日私は家族を守りたい。', '私は家族を守りたい？',
            '「私は家族を守りたい」と友人が言った。',
            '友人によると、私は家族を守りたい。',
            '友人から聞いた話です。私は家族を守りたい。',
            '本で読んだ話です。私は家族を守りたい。',
            '夢を見ました。私は家族を守りたい。',
            '私は家族を守りたい、という夢を見たのですが、' + '詳細を考えた' * 15 + '。',
            '詳細を考えた' * 15 + '、私は家族を守りたい。']
        for memo in values:
            with self.subTest(memo=memo):
                artifact = self.generate(request(record(memo=memo))).artifact
                self.assertFalse(artifact and any(a.kind == 'PROTECTIVE' for a in artifact.graph.annotations))
        artifact = self.generate(request(record(memo='私は記録を残した。', action='私は家族を守りたい。'))).artifact
        self.assertEqual(artifact.graph.annotations, ())
        artifact = self.generate(request(record(memo='私は家族を守りたい。',
            action='友人から聞いた話です。'))).artifact
        self.assertFalse(artifact and artifact.graph.annotations)

    def test_protective_requires_shared_wish_witness(self):
        from cocolon_meaning_experience_engine.cores.analysis import intent_compiler as compiler
        build = compiler.build_final_stage1_grounded_observation_plan
        for mismatch in ('kind', 'scope', 'grounding', 'retention', 'time', 'actor',
                'polarity', 'operator', 'predicate', 'unwitnessed_feeling'):
            def changed(*args, **kwargs):
                plan = build(*args, **kwargs)
                n = plan.nuclei[0]
                if mismatch == 'kind': n = replace(n, kind='value')
                elif mismatch == 'scope': n = replace(n, allowed_claim_scope='unsupported')
                elif mismatch == 'grounding': n = replace(n, grounding_kind='inferred')
                elif mismatch == 'retention': n = replace(n, retention='optional')
                else:
                    f = n.semantic_frame
                    if mismatch == 'time': f = replace(f, time_scope='past')
                    if mismatch == 'actor': f = replace(f, actor='other')
                    if mismatch == 'polarity': f = replace(f, polarity='negative')
                    if mismatch == 'predicate': f = replace(f, predicate_kind='action')
                    if mismatch == 'unwitnessed_feeling': f = replace(f, predicate_kind='feeling')
                    if mismatch == 'operator': f = replace(f, attribute_codes=tuple(c for c in f.attribute_codes if c != 'operator:wish'))
                    n = replace(n, semantic_frame=f)
                return replace(plan, nuclei=(n,))
            with self.subTest(mismatch=mismatch), patch.object(compiler,
                    'build_final_stage1_grounded_observation_plan', side_effect=changed):
                artifact = self.generate(request(record(memo='私は家族を守りたい。'))).artifact
                self.assertFalse(artifact and artifact.graph.annotations)

    def test_protective_aggregation_keeps_targets_burden_and_unknown_separate(self):
        one = record(memo='私は家族を守りたい。私は仕事を続けたいけれど、私はつらい。')
        artifact = self.generate(request(one, one, record(2,
            memo='僕は家族を守りたいです。僕は生活を守りたい。まだよくわからない。'))).artifact
        claims = [a for a in artifact.graph.annotations if a.kind == 'PROTECTIVE']
        self.assertEqual(len(claims), 2)
        self.assertEqual([len(a.evidence_refs) for a in claims], [2, 1])
        self.assertEqual([len(n.record_refs) for n in artifact.graph.nodes], [2, 1, 1])
        self.assertEqual(len([a for a in artifact.graph.annotations if a.kind == 'BURDEN']), 1)
        self.assertIn('SOURCE_SCOPE', [g.missing_scope for g in artifact.graph.unknown_gaps])
        visual = artifact.safe_projection(authenticated_owner_scope=OWNER)
        self.assertEqual(len(visual['annotation_badges']), 3)
        # Four ordinary source clauses have should retention; all still
        # retain full grounding without guessing a sequence or motive.
        artifact = self.generate(request(record(memo='私は家族を守りたい。私は生活を守りたい。'
            '私は記録を残した。私は資料を調べた。'))).artifact
        self.assertEqual(len(artifact.graph.annotations), 2)
        self.assertEqual(artifact.graph.edges, ())
        artifact.safe_projection(authenticated_owner_scope=OWNER)

    def test_protective_supplement_correction_and_withdrawal_preserve_lineage(self):
        old, new = '私は家族を守りたい', '私は生活を守りたいです'
        base = record(memo='私は記録を残した。' + old + '。')
        for answer, count in ((new + '。', 2), ('「' + old + '」ではなく「' + new + '」です。', 1)):
            with self.subTest(answer=answer):
                value = request(self.with_answer(base, answer))
                artifact = self.generate(value).artifact
                self.assertEqual(len(artifact.graph.annotations), count)
                claim = next(a for a in artifact.graph.annotations if new in a.source_labels)
                envelopes = {s.envelope.envelope_id: s.envelope for s in freeze_analysis_sources(value).sources}
                e, = claim.evidence_refs
                self.assertEqual(envelopes[e.source_envelope_id].source_role, 'SUPPLEMENTAL_ANSWER')
                self.assertEqual(envelopes[e.source_envelope_id].raw_utf8[e.utf8_start:e.utf8_end].decode(), new)
                if count == 1:
                    self.assertEqual(claim.update_refs, (artifact.graph.source_updates[0].update_ref,))
                artifact.safe_projection(authenticated_owner_scope=OWNER)
        withdrawn = self.with_answer(base, '「' + old + '」は取り消します。')
        self.assertEqual(self.generate(request(withdrawn)).artifact.graph.annotations, ())
        artifact = self.generate(request(withdrawn, record(2, memo=old + '。'))).artifact
        self.assertEqual(len(artifact.graph.annotations), 1)
        self.assertEqual(len(artifact.graph.annotations[0].evidence_refs), 1)
        artifact.safe_projection(authenticated_owner_scope=OWNER)
        for answer in (new + '。でも元の記録は間違いです。',
                '「' + old + '」ではなく「私は生活を守りたくない」です。'):
            with self.subTest(answer=answer):
                self.assertEqual(self.generate(request(self.with_answer(base, answer))).status, EngineStatus.UNAVAILABLE)

    def test_protective_safe_projection_rejects_wrong_target_or_evidence(self):
        artifact = self.generate(request(record(memo='私は仕事を続けたい。私は家族を守りたい。'))).artifact
        claim, = artifact.graph.annotations
        for change in ({'target_ref': 'n1'}, {'source_labels': ('私は生活を守りたい',)},
                {'source_labels': ('私は家族を守りたくない',)}, {'predicate_lemma': '続ける'},
                {'annotation_state': 'EVIDENCE_BOUND_INTERPRETIVE_HYPOTHESIS'},
                {'kind': 'BURDEN'}, {'evidence_refs': ()},
                {'evidence_refs': artifact.graph.nodes[0].evidence_refs}):
            with self.subTest(change=change):
                broken = replace(artifact, graph=replace(artifact.graph, annotations=(replace(claim, **change),)))
                with self.assertRaisesRegex(AnalysisSourceError, 'analysis_safe_surface_unavailable'):
                    broken.safe_projection(authenticated_owner_scope=OWNER)

    def test_repeated_period_gaps_display_once_without_losing_records_or_burden(self):
        value = request(record(memo='私は仕事を続けたいけれど、私はつらい。'),
            record(2, memo='僕は仕事を続けたいけれど、僕はつらいです。'))
        artifact = self.generate(value).artifact
        before = artifact.graph
        self.assertEqual(len(before.unknown_gaps), 8)
        self.assertEqual(len(before.nodes[0].record_refs), 2)
        self.assertEqual(len(before.nodes[0].evidence_refs), 2)
        self.assertEqual(len(before.annotations[0].evidence_refs), 6)
        visual = artifact.safe_projection(authenticated_owner_scope=OWNER)
        self.assertEqual([g['gap_ref'] for g in visual['unknown_gaps']], ['g1', 'g2', 'g3', 'g4'])
        self.assertEqual(visual['unknown_gaps'], artifact.private_visual_preview(
            authenticated_owner_scope=OWNER)['unknown_gaps'])
        self.assertEqual(visual['nodes'][0]['evidence_badge_count'], 2)
        text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text']
        self.assertEqual(text.count('未確定（'), 4)
        self.assertEqual(text.count('注記（'), 1)
        self.assertIs(artifact.graph, before)
        self.assertEqual(len(before.unknown_gaps), 8)

    def test_unknown_gap_display_retains_other_targets_and_unread_material(self):
        artifact = self.generate(request(
            record(memo='私は仕事を続けたい。まだよくわからない。'),
            record(2, memo='僕は仕事を続けたいです。まだよくわからない。'),
            record(3, memo='私は資料を調べたい。', created_at='2026-10-02T10:00:00Z'))).artifact
        visual = artifact.safe_projection(authenticated_owner_scope=OWNER)
        gaps = visual['unknown_gaps']
        self.assertEqual(len(artifact.graph.unknown_gaps), 14)
        self.assertEqual(len(gaps), 9)
        self.assertEqual([g['gap_ref'] for g in gaps], ['g1', 'g2', 'g3', 'g4', 'g5', 'g11', 'g12', 'g13', 'g14'])
        unread = [g for g in gaps if 'まだ読み取れていない内容' in g['visible_label']]
        self.assertEqual(len(unread), 1)
        self.assertEqual(unread[0]['between_node_refs'], ['n1'])
        scene = [g for g in gaps if g['visible_label'].startswith('場面は')]
        self.assertEqual([g['between_node_refs'] for g in scene], [['n1'], ['n2']])
        self.assertEqual(artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'].count('未確定（'), 9)

    def test_unknown_gap_display_preserves_reason_and_endpoint_order(self):
        from cocolon_meaning_experience_engine.cores.analysis.intent_compiler import UnknownGap
        artifact = self.generate(request(record())).artifact
        # Distinct uncertainty claims can share the same current surface.
        # Neither a reason nor endpoint order may disappear through display.
        gaps = (UnknownGap('g1', ('n1', 'n2'), 'ROUTE_CONNECTION', 'ONLY_EXPLICIT_ORDER_IS_SHOWN'),
            UnknownGap('g2', ('n1', 'n2'), 'ROUTE_CONNECTION', 'EXPLICIT_PREDECESSOR_NOT_ESTABLISHED'),
            UnknownGap('g3', ('n2', 'n1'), 'ROUTE_CONNECTION', 'ONLY_EXPLICIT_ORDER_IS_SHOWN'))
        artifact = replace(artifact, graph=replace(artifact.graph, unknown_gaps=gaps))
        visual = artifact.safe_projection(authenticated_owner_scope=OWNER)
        self.assertEqual([g['gap_ref'] for g in visual['unknown_gaps']], ['g1', 'g2', 'g3'])
        self.assertEqual([g['between_node_refs'] for g in visual['unknown_gaps']],
                         [['n1', 'n2'], ['n1', 'n2'], ['n2', 'n1']])
        self.assertEqual(artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'].count('未確定（'), 3)

    def test_explicit_wish_burden_is_a_targeted_annotation_with_whole_evidence(self):
        for subject in ('私', '僕', 'わたし', '自分'):
            for feeling in ('つらい', 'つらいです', '苦しい', '苦しいです'):
                with self.subTest(subject=subject, feeling=feeling):
                    memo = subject + 'は資料を調べたいけれど、' + subject + 'は' + feeling + '。'
                    value = request(record(memo=memo))
                    artifact = self.generate(value).artifact
                    self.assertIsNotNone(artifact)
                    self.assertEqual(len(artifact.graph.nodes), 1)
                    self.assertEqual(artifact.graph.edges, ())
                    self.assertEqual(artifact.graph.conflicts, ())
                    self.assertNotIn('SOURCE_SCOPE', [g.missing_scope for g in artifact.graph.unknown_gaps])
                    claim = artifact.graph.annotations[0]
                    self.assertEqual((claim.target_ref, claim.kind, claim.annotation_state),
                        ('n1', 'BURDEN', 'SOURCE_EXPLICIT_ANNOTATION'))
                    self.assertEqual(len(claim.evidence_refs), 3)
                    self.assertEqual(claim.evidence_refs[0], artifact.graph.nodes[0].evidence_refs[0])
                    envelope = freeze_analysis_sources(value).sources[0].envelope
                    for e in claim.evidence_refs:
                        raw = envelope.raw_utf8
                        literal = raw[e.utf8_start:e.utf8_end]
                        field = raw[e.field_utf8_start:e.field_utf8_end].decode()
                        self.assertEqual(literal.decode(), field[e.scalar_start:e.scalar_end])
                        self.assertEqual(hashlib.sha256(literal).hexdigest(), e.literal_sha256)
                    whole = claim.evidence_refs[2]
                    self.assertEqual(envelope.raw_utf8[whole.utf8_start:whole.utf8_end].decode(), memo[:-1])
                    visual = artifact.safe_projection(authenticated_owner_scope=OWNER)
                    badge = visual['annotation_badges'][0]
                    self.assertEqual(badge['target_ref'], 'n1')
                    self.assertIn(feeling.removesuffix('です') + 'と記述されています', badge['visible_label'])
                    self.assertIn('原因や続いている期間は確定していません', badge['visible_label'])
                    self.assertIn(badge['visible_label'], artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'])
                    self.assertEqual(visual['annotation_badges'], artifact.private_visual_preview(
                        authenticated_owner_scope=OWNER)['annotation_badges'])

    def test_burden_annotation_does_not_infer_absent_or_qualified_contrast(self):
        prefix = '私は仕事を続けたいけれど、'
        values = [prefix + ending + '。' for ending in (
            'つらい', '友人はつらい', '私はつらかった', '私はつらくない',
            '私はつらくなかった', '私は嬉しくない', '私はつらいかもしれない',
            '私はつらいと思う', '私はつらいと聞いた', '私はつらいという夢を見た',
            '私はとてもつらい', '私はつらい？', '私はつらいが、私は苦しい')]
        values += ['私は仕事を続けたい。私はつらい。', '私はつらい。',
            '私は仕事を続けたけれど、私はつらい。',
            '私は仕事を続けたかったけれど、私はつらい。',
            '私は仕事を続けたくないけれど、私はつらい。',
            '友人は仕事を続けたいけれど、私はつらい。',
            '私は仕事を続けたいなら、私はつらい。',
            '「私は仕事を続けたいけれど、私はつらい」と友人が言った。',
            '友人によると、私は仕事を続けたいけれど、私はつらい。',
            prefix + '私はつらい、という夢を見たのですが、' + '詳細を考えた' * 15 + '。',
            '詳細を考えた' * 15 + '、' + prefix + '私はつらい。']
        for memo in values:
            with self.subTest(memo=memo):
                artifact = self.generate(request(record(memo=memo))).artifact
                self.assertFalse(artifact and artifact.graph.annotations)
        artifact = self.generate(request(record(memo='私は仕事を続けたい。',
            action='私は仕事を続けたいけれど、私はつらい。'))).artifact
        self.assertEqual(artifact.graph.annotations, ())

    def test_burden_annotation_requires_the_shared_relation_and_finite_witness(self):
        from cocolon_meaning_experience_engine.cores.analysis import intent_compiler as compiler
        build = compiler.build_final_stage1_grounded_observation_plan
        for mismatch in ('relation', 'grounding', 'time', 'actor', 'witness', 'range', 'retention'):
            def changed(*args, **kwargs):
                plan = build(*args, **kwargs)
                if mismatch == 'relation': return replace(plan, relations=())
                n = plan.nuclei[1]
                if mismatch == 'grounding': n = replace(n, grounding_kind='inferred')
                elif mismatch == 'retention': n = replace(n, retention='optional')
                else:
                    f = n.semantic_frame
                    if mismatch == 'time': f = replace(f, time_scope='past')
                    if mismatch == 'actor': f = replace(f, actor='other')
                    if mismatch == 'witness': f = replace(f, attribute_codes=tuple(
                        c for c in f.attribute_codes if c != 'lexical:source_finite_contrast_feeling'))
                    if mismatch == 'range': f = replace(f, attribute_codes=tuple(
                        'source_fragment_scalar_range:14:18' if c.startswith('source_fragment_scalar_range:') else c
                        for c in f.attribute_codes))
                    n = replace(n, semantic_frame=f)
                return replace(plan, nuclei=(plan.nuclei[0], n))
            with self.subTest(mismatch=mismatch), patch.object(compiler,
                    'build_final_stage1_grounded_observation_plan', side_effect=changed):
                artifact = self.generate(request(record(memo='私は仕事を続けたいけれど、私はつらい。'))).artifact
                self.assertEqual(artifact.graph.annotations, ())
                self.assertIn('SOURCE_SCOPE', [g.missing_scope for g in artifact.graph.unknown_gaps])

    def test_burden_annotation_aggregates_only_its_target_and_preserves_unread_scope(self):
        memo = '私は仕事を続けたいけれど、私はつらい。'
        one = record(memo=memo)
        artifact = self.generate(request(one, one, record(2,
            memo='僕は仕事を続けたいけれど、僕はつらいです。'))).artifact
        self.assertEqual(len(artifact.graph.annotations), 1)
        self.assertEqual(len(artifact.graph.annotations[0].evidence_refs), 6)
        self.assertEqual(len(artifact.graph.nodes[0].record_refs), 2)
        self.assertEqual(artifact.graph.edges, ())
        self.assertEqual(set(artifact.graph.annotations[0].source_labels), {'私はつらい', '僕はつらいです'})
        artifact.safe_projection(authenticated_owner_scope=OWNER)
        artifact = self.generate(request(record(memo=memo + 'まだよくわからない。'))).artifact
        self.assertEqual(len(artifact.graph.annotations), 1)
        self.assertIn('SOURCE_SCOPE', [g.missing_scope for g in artifact.graph.unknown_gaps])
        artifact = self.generate(request(record(memo=memo),
            record(2, memo='私は資料を調べたいけど、私は苦しいです。'))).artifact
        self.assertEqual([a.target_ref for a in artifact.graph.annotations], ['n1', 'n2'])

    def test_burden_supplement_revision_and_withdrawal_follow_exact_source(self):
        old = '私は仕事を続けたいけれど、私はつらい'
        new = '私は資料を調べたいけど、私は苦しいです'
        base = record(memo='私は記録を残した。' + old + '。')
        for answer, count in ((new + '。', 2), ('「' + old + '」ではなく「' + new + '」です。', 1)):
            with self.subTest(answer=answer):
                value = request(self.with_answer(base, answer))
                artifact = self.generate(value).artifact
                self.assertEqual(len(artifact.graph.annotations), count)
                claim = next(a for a in artifact.graph.annotations if a.predicate_lemma == '苦しい')
                sources = {s.envelope.envelope_id: s.envelope for s in freeze_analysis_sources(value).sources}
                for e in claim.evidence_refs:
                    self.assertEqual(sources[e.source_envelope_id].source_role, 'SUPPLEMENTAL_ANSWER')
                    raw = sources[e.source_envelope_id].raw_utf8[e.utf8_start:e.utf8_end]
                    self.assertEqual(hashlib.sha256(raw).hexdigest(), e.literal_sha256)
                if count == 1:
                    self.assertEqual(claim.update_refs, (artifact.graph.source_updates[0].update_ref,))
                artifact.safe_projection(authenticated_owner_scope=OWNER)
        artifact = self.generate(request(self.with_answer(base, '「' + old + '」は取り消します。'))).artifact
        self.assertEqual(artifact.graph.annotations, ())
        self.assertEqual(len(artifact.graph.nodes), 1)
        artifact = self.generate(request(self.with_answer(base, '「' + old + '」は取り消します。'),
            record(2, memo=old + '。'))).artifact
        self.assertEqual(len(artifact.graph.annotations), 1)
        self.assertEqual(len(artifact.graph.annotations[0].evidence_refs), 3)
        self.assertEqual(artifact.graph.annotations[0].update_refs, ())
        target = next(n for n in artifact.graph.nodes if n.node_ref == artifact.graph.annotations[0].target_ref)
        self.assertEqual(len(target.record_refs), 1)
        artifact.safe_projection(authenticated_owner_scope=OWNER)
        artifact = self.generate(request(self.with_answer(record(memo='私は仕事を続けたい。'),
            '「私は仕事を続けたい」ではなく「' + new + '」です。'))).artifact
        self.assertEqual(len(artifact.graph.annotations), 1)
        self.assertEqual(artifact.graph.annotations[0].update_refs, (artifact.graph.source_updates[0].update_ref,))
        for answer in (new + '。でも、元の記録は間違いです。',
                       '「' + old + '」ではなく「私は資料を調べたいけど、友人はつらい」です。'):
            with self.subTest(answer=answer):
                result = self.generate(request(self.with_answer(base, answer)))
                self.assertEqual(result.status, EngineStatus.UNAVAILABLE)

    def test_burden_safe_surface_rejects_broken_target_evidence_or_replay(self):
        artifact = self.generate(request(record(memo='私は記録を残した。私は仕事を続けたいけれど、私はつらい。'))).artifact
        claim = artifact.graph.annotations[0]
        changes = [{'target_ref': 'n1'}, {'predicate_lemma': '苦しい'},
            {'source_labels': ('私はつらくない',)}, {'kind': 'PROTECTIVE'},
            {'annotation_state': 'EVIDENCE_BOUND_INTERPRETIVE_HYPOTHESIS'},
            {'evidence_refs': claim.evidence_refs[:2]},
            {'evidence_refs': (claim.evidence_refs[1], claim.evidence_refs[0], claim.evidence_refs[2])}]
        for change in changes:
            with self.subTest(change=change):
                broken = replace(artifact, graph=replace(artifact.graph, annotations=(replace(claim, **change),)))
                with self.assertRaisesRegex(AnalysisSourceError, 'analysis_safe_surface_unavailable'):
                    broken.safe_projection(authenticated_owner_scope=OWNER)

    def test_opposed_original_claims_keep_both_targets_and_exact_evidence(self):
        pairs = [('私は資料を調べた', '私は資料を調べませんでした'),
                 ('私は会議の司会を担当した', '私は会議の司会を担当しなかった'),
                 ('私は職場にいた', '私は職場にいませんでした')]
        for positive, negative in pairs:
            with self.subTest(positive=positive):
                value = request(record(memo=positive + '。' + negative + '。'))
                artifact = self.generate(value).artifact
                self.assertEqual(len(artifact.graph.conflicts), 1)
                conflict = artifact.graph.conflicts[0]
                nodes = {n.node_ref: n for n in artifact.graph.nodes}
                self.assertEqual({nodes[r].polarity for r in conflict.target_refs}, {'positive', 'negative'})
                self.assertEqual(set(conflict.evidence_refs),
                    {e for r in conflict.target_refs for e in nodes[r].evidence_refs})
                sources = freeze_analysis_sources(value)
                envelopes = {s.envelope.envelope_id: s.envelope for s in sources.sources}
                for evidence in conflict.evidence_refs:
                    raw = envelopes[evidence.source_envelope_id].raw_utf8
                    literal = raw[evidence.utf8_start:evidence.utf8_end]
                    self.assertEqual(hashlib.sha256(literal).hexdigest(), evidence.literal_sha256)
                visual = artifact.safe_projection(authenticated_owner_scope=OWNER)
                badge = visual['conflict_badges'][0]
                self.assertEqual(badge['target_refs'], list(conflict.target_refs))
                self.assertIn('同じ機会のことかは確定していません', badge['visible_label'])
                self.assertIn(badge['visible_label'], artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'])
                self.assertEqual(visual['conflict_badges'], artifact.private_visual_preview(
                    authenticated_owner_scope=OWNER)['conflict_badges'])

    def test_opposed_claims_are_not_inferred_across_occasions_fields_or_meanings(self):
        values = [
            request(record(memo='私は資料を調べた。'), record(2, memo='私は資料を調べなかった。')),
            request(record(memo='私は資料を調べた。', action='私は資料を調べなかった。')),
            request(record(memo='今日私は資料を調べた。昨日私は資料を調べなかった。')),
            request(record(memo='私は資料を調べた。その後私は資料を調べなかった。')),
            request(record(memo='私は資料を調べた。その後私は資料を見た。私は資料を調べなかった。')),
            request(record(memo='私は資料を調べた。私は記録を調べなかった。')),
            request(record(memo='私は資料を調べた。私は資料を調べたくない。')),
            request(record(memo='私は資料を調べたい。私は資料を調べたくない。')),
        ]
        for value in values:
            with self.subTest(value=value.members):
                artifact = self.generate(value).artifact
                self.assertIsNotNone(artifact)
                self.assertEqual(artifact.graph.conflicts, ())
                self.assertEqual(artifact.safe_projection(authenticated_owner_scope=OWNER)['conflict_badges'], [])

    def test_opposed_claims_aggregate_witnesses_without_duplicate_badges(self):
        memo = '今日私は資料を調べた。今日私は資料を調べなかった。'
        one = record(memo=memo)
        artifact = self.generate(request(one, one)).artifact
        self.assertEqual(len(artifact.graph.conflicts), 1)
        self.assertEqual(len(artifact.graph.conflicts[0].evidence_refs), 2)
        memo = '私は資料を調べた。私は資料を調べなかった。'
        artifact = self.generate(request(record(memo=memo), record(2, memo=memo))).artifact
        self.assertEqual(len(artifact.graph.conflicts), 1)
        self.assertEqual(len(artifact.graph.conflicts[0].evidence_refs), 4)
        self.assertEqual([len(n.record_refs) for n in artifact.graph.nodes], [2, 2])

    def test_correction_and_withdrawal_remove_only_the_opposed_original_claim(self):
        original = record(memo='私は資料を調べた。私は資料を調べなかった。')
        for answer in ('「私は資料を調べなかった」は取り消します。',
                       '「私は資料を調べなかった」ではなく「私は記録を残した」です。'):
            with self.subTest(answer=answer):
                artifact = self.generate(request(self.with_answer(original, answer))).artifact
                self.assertIsNotNone(artifact)
                self.assertEqual(artifact.graph.conflicts, ())
                self.assertFalse(any(n.polarity == 'negative' for n in artifact.graph.nodes))
                self.assertTrue(any(n.proposition.predicate_lemma == '調べる' for n in artifact.graph.nodes))
        result = self.generate(request(self.with_answer(record(memo='私は資料を調べた。'),
                                                       '私は資料を調べなかった。')))
        self.assertEqual(result.status, EngineStatus.UNAVAILABLE)
        self.assertEqual(result.reason_codes, ('analysis_supplement_interpretation_pending',))

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

    def test_relative_days_reach_safe_text_and_graph_with_complete_evidence(self):
        for prefix, day in [('今日、', '今日'), ('昨日，', '昨日'), ('今日\u3000', '今日')]:
            with self.subTest(prefix=prefix):
                req = request(record(memo='\u3000' + prefix + '私は資料を調べました。'))
                artifact = self.generate(req).artifact
                visual = artifact.safe_projection(authenticated_owner_scope=OWNER)
                label = 'この記述時点の' + day + '：資料を調べる（実行済み）'
                self.assertEqual([n['visible_label'] for n in visual['nodes']], [label])
                text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)
                self.assertIn(label, text['text'])
                self.assertEqual(visual['projection_of'], text['projection_of'])
                node = artifact.graph.nodes[0]
                p = node.proposition
                self.assertEqual(set(i for _, a, b in p.source_parts for i in range(a, b)),
                                 set(range(len(node.visible_label))))
                envelope = freeze_analysis_sources(req).sources[0].envelope
                for e in node.evidence_refs:
                    literal = envelope.raw_utf8[e.utf8_start:e.utf8_end]
                    field = envelope.raw_utf8[e.field_utf8_start:e.field_utf8_end].decode()
                    self.assertEqual(literal.decode(), field[e.scalar_start:e.scalar_end])
                    self.assertEqual(hashlib.sha256(literal).hexdigest(), e.literal_sha256)
                    self.assertIn(day, literal.decode())
                self.assertNotIn('2026', label)
                for private in ('relative_day', 'source_parts', 'analysis-source:', OWNER, '私は'):
                    self.assertNotIn(private, json.dumps(visual, ensure_ascii=False))

    def test_relative_day_does_not_overwrite_negation_wish_or_tense(self):
        cases = [
            ('昨日私は資料を調べなかった。', 'negative', 'fact', 'past', '行わなかった'),
            ('今日私は仕事を続けたい。', 'positive', 'wish', 'current_input', '希望'),
            ('昨日私は仕事を続けたかった。', 'positive', 'wish', 'past', '希望（当時）'),
            ('昨日私は仕事を続けたくなかった。', 'negative', 'wish', 'past', '望まない（当時）'),
        ]
        for memo, polarity, modality, time, label in cases:
            with self.subTest(memo=memo):
                artifact = self.generate(request(record(memo=memo))).artifact
                n = artifact.graph.nodes[0]
                self.assertEqual((n.polarity, n.modality, n.temporal_scope), (polarity, modality, time))
                visual = artifact.safe_projection(authenticated_owner_scope=OWNER)
                self.assertIn(label, visual['nodes'][0]['visible_label'])
                if modality == 'wish':
                    self.assertEqual(n.node_kind, 'ATTENTION_OR_THOUGHT')
                    self.assertNotIn('実行済み', visual['nodes'][0]['visible_label'])

    def test_post_topic_day_preserves_arguments_operators_and_complete_evidence(self):
        cases = (
            ('私は昨日資料を調べた。', 'YESTERDAY', 'positive', 'fact', 'past',
             'この記述時点の昨日：資料を調べる（実行済み）'),
            ('僕は昨日，資料を調べませんでした。', 'YESTERDAY', 'negative', 'fact', 'past',
             'この記述時点の昨日：資料を調べる（行わなかった）'),
            ('わたしは今日\u3000仕事を続けたいです。', 'TODAY', 'positive', 'wish', 'current_input',
             'この記述時点の今日：仕事を続けることへの希望'),
            ('自分は昨日仕事を続けたくなかった。', 'YESTERDAY', 'negative', 'wish', 'past',
             'この記述時点の昨日：仕事を続けることを望まない（当時）'),
            ('私は昨日、考えをノートに書いた。', 'YESTERDAY', 'positive', 'fact', 'past',
             'この記述時点の昨日：考えをノートに書く（実行済み）'),
            ('私は昨日、仕事の資料を調べた。', 'YESTERDAY', 'positive', 'fact', 'past',
             'この記述時点の昨日：仕事の資料を調べる（実行済み）'),
        )
        for memo, day, polarity, modality, time, label in cases:
            with self.subTest(memo=memo):
                req = request(record(memo=memo))
                artifact = self.generate(req).artifact
                node = artifact.graph.nodes[0]
                p = node.proposition
                self.assertEqual((p.relative_day, node.polarity, node.modality, node.temporal_scope),
                                 (day, polarity, modality, time))
                self.assertFalse(any(noun.startswith(('今日', '昨日')) for _, noun in p.arguments))
                covered = [i for _, a, b in p.source_parts for i in range(a, b)]
                self.assertEqual(covered, list(range(len(node.visible_label))))
                source = freeze_analysis_sources(req).sources[0].envelope
                e = node.evidence_refs[0]
                literal = source.raw_utf8[e.utf8_start:e.utf8_end]
                field = source.raw_utf8[e.field_utf8_start:e.field_utf8_end].decode()
                self.assertEqual(literal.decode(), field[e.scalar_start:e.scalar_end])
                self.assertEqual(hashlib.sha256(literal).hexdigest(), e.literal_sha256)
                self.assertIn('昨日' if day == 'YESTERDAY' else '今日', literal.decode())
                visual = artifact.safe_projection(authenticated_owner_scope=OWNER)
                text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)
                self.assertEqual(visual['nodes'][0]['visible_label'], label)
                self.assertIn(label, text['text'])
                self.assertEqual(visual['projection_of'], text['projection_of'])
                self.assertFalse(visual['edges'])

                altered = replace(artifact, graph=replace(artifact.graph, nodes=(
                    replace(node, proposition=replace(p, relative_day='')),)))
                with self.assertRaises(AnalysisSourceError):
                    altered.safe_projection(authenticated_owner_scope=OWNER)

    def test_post_topic_day_keeps_nominal_modifiers_and_does_not_invent_operators(self):
        for memo, noun in (('私は今日の資料を調べた。', '今日の資料'),
                           ('私は昨日の記録を見た。', '昨日の記録'),
                           ('私は昨日を記録した。', '昨日')):
            with self.subTest(memo=memo):
                artifact = self.generate(request(record(memo=memo))).artifact
                p = artifact.graph.nodes[0].proposition
                self.assertEqual(p.arguments, (('を', noun),))
                self.assertEqual(p.relative_day, '')
                self.assertNotIn('この記述時点の', artifact.safe_projection(
                    authenticated_owner_scope=OWNER)['nodes'][0]['visible_label'])
        artifact = self.generate(request(record(memo=
            '私は昨日資料を調べた。私は記録を残した。'))).artifact
        self.assertEqual([n.proposition.relative_day for n in artifact.graph.nodes], ['YESTERDAY', ''])
        self.assertFalse(artifact.graph.edges)

    def test_post_topic_day_does_not_erase_unsupported_temporal_scopes(self):
        for memo in (
            '私は昨日仕事を続けたい。', '私は今日昨日資料を調べた。',
            '昨日私は今日資料を調べた。', 'その後私は今日資料を調べた。',
            '私は昨日資料を調べてから、疑問が減った。',
            '私は昨日資料を調べた後、疑問が減った。',
            '私は昨日資料を調べたかもしれないと思っている。',
            '私は資料を昨日ノートに書いた。',
            '私は昨日急いで資料を調べた。', '私は昨日資料を調べた？',
            '友人の話です。私は昨日資料を調べた。', '友人は昨日資料を調べた。',
        ):
            with self.subTest(memo=memo):
                result = self.generate(request(record(memo=memo)))
                if result.artifact:
                    with self.assertRaises(AnalysisSourceError):
                        result.artifact.safe_projection(authenticated_owner_scope=OWNER)
                else:
                    self.assertEqual(result.status, EngineStatus.UNAVAILABLE)

    def test_post_topic_day_answers_corrections_and_withdrawals_keep_source(self):
        original = record(memo='私は考えを書いた。')
        for answer in ('私は昨日、資料を調べた。', '私は今日資料を調べた。'):
            with self.subTest(answer=answer):
                req = request(self.with_answer(original, answer))
                artifact = self.generate(req).artifact
                node = next(n for n in artifact.graph.nodes if n.proposition.relative_day)
                sources = {s.envelope.envelope_id: s.envelope for s in freeze_analysis_sources(req).sources}
                e = node.evidence_refs[0]
                source = sources[e.source_envelope_id]
                self.assertEqual(source.source_role, 'SUPPLEMENTAL_ANSWER')
                self.assertEqual(source.raw_utf8[e.utf8_start:e.utf8_end].decode(), answer[:-1])
                self.assertFalse(artifact.safe_projection(authenticated_owner_scope=OWNER)['edges'])
        original = record(memo='私は昨日資料を調べた。私は記録を残した。')
        req = request(self.with_answer(original,
            '「私は昨日資料を調べた」ではなく「私は今日資料を調べなかった」です。'))
        corrected = self.generate(req).artifact
        labels = [n['visible_label'] for n in corrected.safe_projection(authenticated_owner_scope=OWNER)['nodes']]
        self.assertIn('この記述時点の今日：資料を調べる（行わなかった）', labels)
        self.assertFalse(any('昨日' in label for label in labels))
        node = next(n for n in corrected.graph.nodes if n.update_refs)
        source = next(s.envelope for s in freeze_analysis_sources(req).sources
                      if s.envelope.envelope_id == node.evidence_refs[0].source_envelope_id)
        e = node.evidence_refs[0]
        self.assertEqual(source.raw_utf8[e.utf8_start:e.utf8_end].decode(), '私は今日資料を調べなかった')
        withdrawn = self.generate(request(self.with_answer(original,
            '「私は昨日資料を調べた」は取り消します。'))).artifact
        self.assertEqual(len(withdrawn.graph.nodes), 1)
        self.assertNotIn('昨日', withdrawn.safe_text_projection(authenticated_owner_scope=OWNER)['text'])

    def test_post_topic_day_does_not_promote_nominal_suffixes_or_finer_times(self):
        for extension in ('分の', '以前の', '以後の', '以降の', '時点の', '当時の',
                          '現在の', '中の', '付の', '以来の', '頃の', 'までの',
                          'からの', '朝の', '午前の', '午後の', '夜の',
                          '版の', '提出の', '発行の', '仕事の'):
            for day in ('今日', '昨日'):
                memo = '私は' + day + extension + '資料を調べた。'
                with self.subTest(memo=memo):
                    result = self.generate(request(record(memo=memo)))
                    if result.artifact:
                        with self.assertRaises(AnalysisSourceError):
                            result.artifact.safe_projection(authenticated_owner_scope=OWNER)
                    else:
                        self.assertEqual(result.status, EngineStatus.UNAVAILABLE)

    def test_post_topic_day_comparison_uses_meaning_not_word_order(self):
        for before, now in (
            ('昨日私は資料を調べた。', '私は昨日資料を調べた。'),
            ('今日私は仕事を続けたい。', '私は今日仕事を続けたいです。'),
            ('昨日私は資料を調べなかった。', '私は昨日資料を調べなかった。'),
        ):
            with self.subTest(now=now):
                artifact = self.compared(now, before).artifact
                self.assertEqual(artifact.safe_projection(authenticated_owner_scope=OWNER)
                                 ['period_comparison']['safe_change_kinds'], [])
        artifact = self.compared('私は今日資料を調べた。', '私は昨日資料を調べた。').artifact
        self.assertIn('ROUTE_EVIDENCE_CHANGED', artifact.safe_projection(
            authenticated_owner_scope=OWNER)['period_comparison']['safe_change_kinds'])

    def test_relative_day_aggregation_stays_with_its_own_source(self):
        memo = '今日私は資料を調べた。今日わたしは資料を調べました。'
        artifact = self.generate(request(record(memo=memo), record(2, memo=memo))).artifact
        self.assertEqual(len(artifact.graph.nodes), 2)
        self.assertTrue(all(len(n.record_refs) == 1 and len(n.evidence_refs) == 2
                            for n in artifact.graph.nodes))
        self.assertFalse(artifact.graph.edges)
        artifact.safe_projection(authenticated_owner_scope=OWNER)
        three = self.generate(request(record(memo='私は資料を調べた。'
            '昨日私は資料を調べた。今日私は資料を調べた。'))).artifact
        self.assertEqual(len(three.graph.nodes), 3)
        self.assertFalse(three.graph.edges)

    def test_relative_day_in_answer_keeps_its_separate_statement_source(self):
        req = request(self.with_answer(record(memo='今日私は資料を調べた。'),
                                       '今日私は資料を調べました。'))
        artifact = self.generate(req).artifact
        visual = artifact.safe_projection(authenticated_owner_scope=OWNER)
        self.assertEqual(len(visual['nodes']), 2)
        self.assertEqual([n['evidence_badge_count'] for n in visual['nodes']], [1, 1])
        self.assertFalse(visual['edges'])
        refs = [n.evidence_refs[0] for n in artifact.graph.nodes]
        self.assertNotEqual(refs[0].source_envelope_id, refs[1].source_envelope_id)
        sources = {s.envelope.envelope_id: s for s in freeze_analysis_sources(req).sources}
        self.assertEqual([sources[e.source_envelope_id].envelope.source_role for e in refs],
                         ['ORIGINAL_INPUT', 'SUPPLEMENTAL_ANSWER'])
        answer = sources[refs[1].source_envelope_id].envelope
        self.assertEqual(answer.raw_utf8[refs[1].utf8_start:refs[1].utf8_end].decode(),
                         '今日私は資料を調べました')

    def test_only_distinct_days_in_one_answer_can_disambiguate_opposition(self):
        original = record(memo='私は考えを書いた。')
        admitted = self.generate(request(self.with_answer(original,
            '昨日私は資料を調べた。今日私は資料を調べなかった。')))
        self.assertEqual(admitted.status, EngineStatus.GENERATED)
        self.assertEqual(len(admitted.artifact.safe_projection(authenticated_owner_scope=OWNER)['nodes']), 3)
        for original_text, answer in [
            ('今日私は資料を調べた。', '昨日私は資料を調べなかった。'),
            ('昨日私は資料を調べた。', '今日私は資料を調べなかった。'),
            ('今日私は資料を調べた。', '今日私は資料を調べなかった。'),
            ('私は考えを書いた。', '今日私は資料を調べた。今日私は資料を調べなかった。'),
            ('私は考えを書いた。', '昨日私は資料を調べた。私は資料を調べなかった。'),
        ]:
            with self.subTest(original=original_text, answer=answer):
                r = self.generate(request(self.with_answer(record(memo=original_text), answer)))
                self.assertEqual(r.status, EngineStatus.UNAVAILABLE)
                self.assertIn('analysis_supplement_interpretation_pending', r.reason_codes)

    def test_day_words_alone_never_create_order_or_inherit_to_next_claim(self):
        separate = self.generate(request(record(memo=
            '昨日私は資料を調べた。今日私は記録を残した。'))).artifact
        self.assertFalse(separate.safe_projection(authenticated_owner_scope=OWNER)['edges'])
        sequence = self.generate(request(record(memo=
            '昨日私は資料を調べた。その後私は記録を残した。'))).artifact
        visual = sequence.safe_projection(authenticated_owner_scope=OWNER)
        self.assertEqual(len(visual['edges']), 1)
        self.assertEqual(sequence.graph.nodes[1].proposition.relative_day, '')
        self.assertNotIn('昨日', visual['nodes'][1]['visible_label'])

    def test_day_qualified_correction_and_withdrawal_keep_exact_target(self):
        original = record(memo='昨日私は資料を調べた。私は記録を残した。')
        req = request(self.with_answer(original,
            '「昨日私は資料を調べた」ではなく「今日私は資料を調べなかった」です。'))
        corrected = self.generate(req).artifact
        labels = [n['visible_label'] for n in corrected.safe_projection(authenticated_owner_scope=OWNER)['nodes']]
        self.assertTrue(any('今日' in label and '行わなかった' in label for label in labels))
        self.assertFalse(any('昨日' in label for label in labels))
        updated = next(n for n in corrected.graph.nodes if n.update_refs)
        sources = {s.envelope.envelope_id: s for s in freeze_analysis_sources(req).sources}
        e = updated.evidence_refs[0]
        envelope = sources[e.source_envelope_id].envelope
        self.assertEqual(envelope.source_role, 'SUPPLEMENTAL_ANSWER')
        self.assertEqual(envelope.raw_utf8[e.utf8_start:e.utf8_end].decode(), '今日私は資料を調べなかった')
        withdrawn = self.generate(request(self.with_answer(original,
            '「昨日私は資料を調べた」は取り消します。'))).artifact
        self.assertEqual(len(withdrawn.graph.nodes), 1)
        self.assertNotIn('昨日', withdrawn.safe_text_projection(authenticated_owner_scope=OWNER)['text'])
        unqualified = self.generate(request(self.with_answer(original,
            '「昨日私は資料を調べた」ではなく「私は資料を調べなかった」です。'))).artifact
        self.assertTrue(all(not n.proposition.relative_day for n in unqualified.graph.nodes))

    def test_unsupported_day_scopes_cannot_be_silently_shortened(self):
        for memo in ('昨日私は仕事を続けたい。', '明日私は資料を調べた。',
                     'その後今日私は資料を調べた。', '昨日私は資料を調べた？',
                     '昨日友人は資料を調べた。', '昨日「私は資料を調べた」と聞いた。'):
            with self.subTest(memo=memo):
                result = self.generate(request(record(memo=memo)))
                if result.artifact:
                    with self.assertRaises(AnalysisSourceError):
                        result.artifact.safe_projection(authenticated_owner_scope=OWNER)
                else:
                    self.assertEqual(result.status, EngineStatus.UNAVAILABLE)

    def test_cognitive_content_is_possible_not_a_performed_action(self):
        for content, polarity, time in [('資料を調べた', 'positive', 'past'),
                ('資料を調べなかった', 'negative', 'past'),
                ('資料を調べる', 'positive', 'nonpast'),
                ('資料を調べない', 'negative', 'nonpast')]:
            with self.subTest(content=content):
                req = request(record(memo='\u3000私は' + content + 'かもしれないと思っている。'))
                artifact = self.generate(req).artifact
                visual = artifact.safe_projection(authenticated_owner_scope=OWNER)
                self.assertEqual(len(visual['nodes']), 1)
                n = artifact.graph.nodes[0]
                self.assertEqual(n.node_kind, 'ATTENTION_OR_THOUGHT')
                self.assertEqual((n.polarity, n.modality, n.temporal_scope), ('neutral', 'fact', 'current_input'))
                inner = n.proposition.possible_content
                self.assertEqual((inner.actor, inner.modality, inner.polarity, inner.temporal_scope),
                                 ('UNSPECIFIED', 'possibility', polarity, time))
                label = content + 'かもしれないと思っている（この記述時点の考え）'
                self.assertEqual(visual['nodes'][0]['visible_label'], label)
                self.assertIn(label, artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'])
                self.assertNotIn('実行済み', label)
                self.assertFalse(visual['edges'])
                self.assertIn('ACTION_OR_NONACTION', [g.missing_scope for g in artifact.graph.unknown_gaps])
                self.assertEqual(set(i for _, a, b in n.proposition.source_parts for i in range(a, b)),
                                 set(range(len(n.visible_label))))
                e = n.evidence_refs[0]
                envelope = freeze_analysis_sources(req).sources[0].envelope
                literal = envelope.raw_utf8[e.utf8_start:e.utf8_end]
                field = envelope.raw_utf8[e.field_utf8_start:e.field_utf8_end].decode()
                self.assertEqual(literal.decode(), field[e.scalar_start:e.scalar_end])
                self.assertEqual(hashlib.sha256(literal).hexdigest(), e.literal_sha256)

    def test_actual_action_survives_beside_cognition_without_inferred_order(self):
        for memo in ('私は記録を残した。私は資料を調べたかもしれないと思っている。',
                     '私は資料を調べたかもしれないと思っている。その後私は記録を残した。'):
            with self.subTest(memo=memo):
                artifact = self.generate(request(record(memo=memo))).artifact
                visual = artifact.safe_projection(authenticated_owner_scope=OWNER)
                self.assertEqual(sorted(n['node_kind'] for n in visual['nodes']),
                                 ['ACTION_OR_NONACTION', 'ATTENTION_OR_THOUGHT'])
                self.assertFalse(visual['edges'])
                self.assertEqual(sum('実行済み' in n['visible_label'] for n in visual['nodes']), 1)

    def test_cognitive_grouping_preserves_content_polarity_tense_and_host(self):
        memo = ('私は資料を調べたかもしれないと思っている。'
                '私は資料を調べなかったかもしれないと思っている。'
                '私は資料を調べるかもしれないと思っている。'
                '私は資料を調べたかもしれないと思ってしまう。'
                '私は記録を残したかもしれないと思っている。')
        artifact = self.generate(request(record(memo=memo))).artifact
        self.assertEqual(len(artifact.safe_projection(authenticated_owner_scope=OWNER)['nodes']), 5)
        restated = ('私は考えをノートに書いたかもって考えちゃう。'
                    '僕はノートに考えを書いたかもしれないと考えてしまう。')
        artifact = self.generate(request(record(memo=restated), record(2, memo=restated))).artifact
        self.assertEqual(len(artifact.graph.nodes), 1)
        self.assertEqual(len(artifact.graph.nodes[0].evidence_refs), 4)
        visual = artifact.safe_projection(authenticated_owner_scope=OWNER)
        self.assertEqual(visual['nodes'][0]['evidence_badge_count'], 2)
        self.assertFalse(visual['edges'])

    def test_ordinary_cognitive_answer_retains_provenance_and_alternatives(self):
        answer = ('私は資料を調べたかもしれないと思っている。'
                  '私は資料を調べなかったかもしれないと思っている。')
        req = request(self.with_answer(record(memo='私は記録を残した。'), answer))
        artifact = self.generate(req).artifact
        self.assertEqual(len(artifact.safe_projection(authenticated_owner_scope=OWNER)['nodes']), 3)
        sources = {s.envelope.envelope_id: s for s in freeze_analysis_sources(req).sources}
        thoughts = [n for n in artifact.graph.nodes if n.proposition.possible_content]
        self.assertEqual(len(thoughts), 2)
        for n in thoughts:
            e = n.evidence_refs[0]
            self.assertEqual(sources[e.source_envelope_id].envelope.source_role, 'SUPPLEMENTAL_ANSWER')
            self.assertEqual(len(n.record_refs), 1)
        unavailable = self.generate(request(self.with_answer(record(),
            '私は資料を調べたかもしれないと思っている。まだわからない。')))
        self.assertEqual(unavailable.status, EngineStatus.UNAVAILABLE)

    def test_cognitive_replacement_and_withdrawal_do_not_keep_old_scope(self):
        thought = '私は資料を調べたかもしれないと思っている'
        original = record(memo=thought + '。私は記録を残した。')
        withdrawn = self.generate(request(self.with_answer(original, '「' + thought + '」は取り消します。'))).artifact
        self.assertEqual(len(withdrawn.graph.nodes), 1)
        self.assertNotIn('かもしれない', withdrawn.safe_text_projection(authenticated_owner_scope=OWNER)['text'])
        for before, after in [('私は資料を調べた', thought), (thought, '私は資料を調べなかった')]:
            with self.subTest(before=before):
                req = request(self.with_answer(record(memo=before + '。'),
                    '「' + before + '」ではなく「' + after + '」です。'))
                artifact = self.generate(req).artifact
                visual = artifact.safe_projection(authenticated_owner_scope=OWNER)
                self.assertEqual(len(visual['nodes']), 1)
                self.assertEqual(visual['nodes'][0]['node_kind'],
                    'ATTENTION_OR_THOUGHT' if after == thought else 'ACTION_OR_NONACTION')
                self.assertEqual(len(artifact.graph.source_updates), 1)
                e = artifact.graph.nodes[0].evidence_refs[0]
                sources = {s.envelope.envelope_id: s for s in freeze_analysis_sources(req).sources}
                envelope = sources[e.source_envelope_id].envelope
                self.assertEqual(envelope.source_role, 'SUPPLEMENTAL_ANSWER')
                self.assertEqual(envelope.raw_utf8[e.utf8_start:e.utf8_end].decode(), after)

    def test_unproved_cognitive_scopes_are_not_safe_surface_content(self):
        for memo in ('友人は資料を調べたかもしれないと思っている。',
                     '私は資料を調べたかもしれないと思っていない。',
                     '私は資料を調べたかもしれないと思っていた。',
                     '私は資料を調べたかもしれないと思っている？',
                     'もし私は資料を調べたかもしれないと思っているなら、安心する。',
                     '私は仕事が終わっただけなのに、資料を調べたかもしれないと思っている。',
                     '私は資料を読んだかもしれないと思っている。',
                     '私は資料を調べたいかもしれないと思っている。',
                     '私は資料を調べたかもしれない。',
                     '私は資料を調べる。',
                     '友人の話によると、私は資料を調べたかもしれないと思っている。'):
            with self.subTest(memo=memo):
                result = self.generate(request(record(memo=memo)))
                if result.artifact:
                    with self.assertRaises(AnalysisSourceError):
                        result.artifact.safe_projection(authenticated_owner_scope=OWNER)
                else:
                    self.assertEqual(result.status, EngineStatus.UNAVAILABLE)

    def test_unread_uncertainty_still_blocks_other_claims_in_same_field(self):
        for tail in ('まだ違うかもしれない。', '私は資料を読んだかもしれないと思っている。',
                     'もし私は資料を見たなら、安心する。'):
            result = self.generate(request(record(memo='私は記録を残した。'
                '私は資料を調べたかもしれないと思っている。' + tail)))
            if result.artifact:
                with self.assertRaises(AnalysisSourceError):
                    result.artifact.safe_projection(authenticated_owner_scope=OWNER)
            else:
                self.assertEqual(result.status, EngineStatus.UNAVAILABLE)

    def test_cognitive_grammar_alone_cannot_replace_shared_semantic_witness(self):
        target = 'cocolon_meaning_experience_engine.cores.analysis.intent_compiler._source_current_cognition'
        with patch(target, return_value=False):
            result = self.generate(request(record(memo='私は資料を調べたかもと思っている。')))
        self.assertEqual(result.status, EngineStatus.UNAVAILABLE)

    def test_unfinished_result_reaches_text_and_graph_without_inventing_actor(self):
        for noun, particle, predicate in (
            ('方法', 'が', '見つかっていない'), ('方針', 'は', '決まっていません'),
            ('仕事の方針', 'も', '定まっていない')):
            memo = 'まだ' + noun + particle + predicate
            with self.subTest(memo=memo):
                req = request(record(memo=memo + '。'))
                artifact = self.generate(req).artifact
                node, = artifact.graph.nodes
                self.assertEqual(node.node_kind, 'IMMEDIATE_RESULT_OR_AFTERMATH')
                self.assertEqual((node.polarity, node.modality, node.temporal_scope),
                                 ('negative', 'fact', 'current_input'))
                self.assertEqual(node.proposition.actor, 'UNSPECIFIED')
                self.assertEqual(node.proposition.arguments, ((particle, noun),))
                self.assertEqual(node.proposition.result_state, 'NOT_YET')
                parts = node.proposition.source_parts
                self.assertEqual([i for _, a, b in parts for i in range(a, b)], list(range(len(memo))))
                source, = freeze_analysis_sources(req).sources
                evidence, = node.evidence_refs
                literal = source.envelope.raw_utf8[evidence.utf8_start:evidence.utf8_end]
                self.assertEqual(literal.decode(), memo)
                self.assertEqual(hashlib.sha256(literal).hexdigest(), evidence.literal_sha256)
                label = artifact.safe_projection(authenticated_owner_scope=OWNER)['nodes'][0]['visible_label']
                self.assertEqual(label, memo.replace('いません', 'いない') + '（この記述時点）')
                self.assertIn(label, artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'])
                scopes = {g.missing_scope for g in artifact.graph.unknown_gaps}
                self.assertNotIn('IMMEDIATE_RESULT_OR_AFTERMATH', scopes)
                self.assertIn('ACTION_OR_NONACTION', scopes)

    def test_unfinished_result_and_action_do_not_imply_order_or_cause(self):
        one = record(memo='私は資料を調べた。まだ方法が見つかっていない。')
        artifact = self.generate(request(one)).artifact
        self.assertEqual([n.node_kind for n in artifact.graph.nodes],
                         ['ACTION_OR_NONACTION', 'IMMEDIATE_RESULT_OR_AFTERMATH'])
        self.assertEqual(artifact.graph.edges, ())
        self.assertIn('ROUTE_CONNECTION', {g.missing_scope for g in artifact.graph.unknown_gaps})
        repeated = self.generate(request(one, record(2, memo=json.loads(one.original_json)['memo']))).artifact
        self.assertEqual([e.edge_kind for e in repeated.graph.edges], ['REPEATED_COOCCURRENCE'])

    def test_unfinished_result_equivalence_preserves_particle_and_predicate(self):
        memo = ('まだ方法が見つかっていない。まだ方法が見つかっていません。'
                'まだ方法も見つかっていない。まだ方法が決まっていない。')
        artifact = self.generate(request(record(memo=memo))).artifact
        self.assertEqual(len(artifact.graph.nodes), 3)
        self.assertEqual(len(artifact.graph.nodes[0].evidence_refs), 2)
        self.assertEqual([len(n.record_refs) for n in artifact.graph.nodes], [1, 1, 1])
        self.assertFalse(artifact.graph.edges)

    def test_unfinished_result_answer_keeps_answer_source_and_record_count(self):
        original = record(memo='まだ方法が見つかっていない。')
        value = self.with_answer(original, 'まだ方法が見つかっていません。')
        req = request(value)
        artifact = self.generate(req).artifact
        node, = artifact.graph.nodes
        self.assertEqual(len(node.record_refs), 1)
        self.assertEqual(len(node.evidence_refs), 2)
        sources = {s.envelope.envelope_id: s.envelope for s in freeze_analysis_sources(req).sources}
        self.assertEqual({sources[e.source_envelope_id].source_role for e in node.evidence_refs},
                         {'ORIGINAL_INPUT', 'SUPPLEMENTAL_ANSWER'})
        bad = self.with_answer(original, 'まだ方法が見つかっていません。別の意味です。')
        self.assertIn('analysis_supplement_interpretation_pending', self.generate(request(bad)).reason_codes)

    def test_unfinished_result_correction_and_withdrawal_keep_exact_scope(self):
        old, new = 'まだ方法が見つかっていない', 'まだ方針は決まっていない'
        original = record(memo='私は資料を調べた。' + old + '。')
        corrected = self.with_answer(original, '「' + old + '」ではなく「' + new + '」です。')
        req = request(corrected)
        artifact = self.generate(req).artifact
        result_node = next(n for n in artifact.graph.nodes if n.proposition.result_state)
        self.assertEqual(result_node.visible_label, new)
        self.assertEqual(artifact.graph.source_updates[0].operation, 'REVISE')
        envelope = next(s.envelope for s in freeze_analysis_sources(req).sources
                        if s.envelope.source_role == 'SUPPLEMENTAL_ANSWER')
        e, = result_node.evidence_refs
        self.assertEqual(envelope.raw_utf8[e.utf8_start:e.utf8_end].decode(), new)
        withdrawn = self.with_answer(original, '「' + old + '」は取り消します。')
        artifact = self.generate(request(withdrawn)).artifact
        self.assertEqual(len(artifact.graph.nodes), 1)
        self.assertEqual(artifact.graph.nodes[0].node_kind, 'ACTION_OR_NONACTION')
        self.assertIn('IMMEDIATE_RESULT_OR_AFTERMATH', {g.missing_scope for g in artifact.graph.unknown_gaps})

    def test_unfinished_result_requires_shared_full_clause_witness(self):
        from cocolon_meaning_experience_engine.cores.analysis import intent_compiler as compiler
        build = compiler.build_final_stage1_grounded_observation_plan
        def without_witness(*args, **kwargs):
            plan = build(*args, **kwargs)
            return replace(plan, nuclei=tuple(replace(n, semantic_frame=replace(n.semantic_frame,
                attribute_codes=tuple(c for c in n.semantic_frame.attribute_codes
                                      if c != 'semantic_role:present_unfinished'))) for n in plan.nuclei))
        with patch.object(compiler, 'build_final_stage1_grounded_observation_plan', side_effect=without_witness):
            self.assertIsNone(self.generate(request(record(memo='まだ方法が見つかっていない。'))).artifact)

    def test_unfinished_result_never_shortens_unsupported_scope(self):
        cases = ('まだ方法が見つかっていなかった。', 'まだ方法が見つかっている。',
                 'まだ方法が見つかっていないわけではない。', 'まだ方法が見つかっていない？',
                 'まだ方法が見つかっていないかもしれない。', 'もしまだ方法が見つかっていないなら。',
                 '友人によると、まだ方法が見つかっていない。', '「まだ方法が見つかっていない」と聞いた。',
                 'どちらも本当で、まだ方法が見つかっていない。', 'まだ実行する方法が見つかっていない。',
                 '昨日まだ方法が見つかっていない。', 'まだ何が決まっていない。',
                 'まだ誰が見つかっていない。', 'まだ誰の方針が決まっていない。')
        for memo in cases:
            with self.subTest(memo=memo):
                result = self.generate(request(record(memo=memo)))
                self.assertFalse(result.artifact and any(n.proposition and n.proposition.result_state
                                                        for n in result.artifact.graph.nodes))
        result = self.generate(request(record(memo='', action='まだ方法が見つかっていない。')))
        self.assertIsNone(result.artifact)

    def test_action_change_pair_preserves_complete_evidence_and_order(self):
        for connector, result_clause in (
            ('後、', '疑問が減った'), ('あとに、', '負担が増えた'),
            ('後に, ', '仕事の方針は変わった'), ('あと、', '状態も戻った')):
            memo = '私は資料を調べた' + connector + result_clause
            with self.subTest(memo=memo):
                req = request(record(memo='　' + memo + '。'))
                artifact = self.generate(req).artifact
                action, result_node = artifact.graph.nodes
                self.assertEqual([n.node_kind for n in artifact.graph.nodes],
                    ['ACTION_OR_NONACTION', 'IMMEDIATE_RESULT_OR_AFTERMATH'])
                self.assertEqual((result_node.proposition.actor, result_node.polarity,
                    result_node.modality, result_node.temporal_scope), ('UNSPECIFIED', 'positive', 'fact', 'past'))
                self.assertEqual(result_node.proposition.result_state, 'BOUNDED_CHANGE')
                edge, = artifact.graph.edges
                self.assertEqual((edge.edge_kind, edge.endpoint_refs),
                    ('OBSERVED_ORDER', (action.node_ref, result_node.node_ref)))
                source, = freeze_analysis_sources(req).sources
                literals = []
                for e in edge.evidence_refs:
                    literal = source.envelope.raw_utf8[e.utf8_start:e.utf8_end]
                    field = source.envelope.raw_utf8[e.field_utf8_start:e.field_utf8_end].decode()
                    self.assertEqual(literal.decode(), field[e.scalar_start:e.scalar_end])
                    self.assertEqual(hashlib.sha256(literal).hexdigest(), e.literal_sha256)
                    literals.append(literal.decode())
                self.assertEqual(literals, ['私は資料を調べた', result_clause, memo])
                for node in artifact.graph.nodes:
                    self.assertEqual([i for _, a, b in node.proposition.source_parts for i in range(a, b)],
                                     list(range(len(node.visible_label))))
                text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text']
                self.assertIn(result_clause + '（記録された変化）', text)
                self.assertIn('原因を示す線ではありません', text)
                self.assertNotIn('ROUTE_CONNECTION', {g.missing_scope for g in artifact.graph.unknown_gaps})
                self.assertIn('SCENE', {g.missing_scope for g in artifact.graph.unknown_gaps})

    def test_action_change_pair_does_not_merge_distinct_episodes(self):
        memo = '私は資料を調べた後、疑問が減った。'
        artifact = self.generate(request(record(memo=memo + memo), record(2, memo=memo))).artifact
        self.assertEqual(len(artifact.graph.nodes), 6)
        self.assertEqual(len(artifact.graph.edges), 3)
        self.assertTrue(all(e.edge_kind == 'OBSERVED_ORDER' for e in artifact.graph.edges))
        self.assertEqual([len(n.record_refs) for n in artifact.graph.nodes], [1] * 6)
        self.assertEqual(len({ref for e in artifact.graph.edges for ref in e.endpoint_refs}), 6)

    def test_action_change_answer_consumes_connector_and_keeps_answer_evidence(self):
        original = record(memo='私は記録を残した。')
        answer = '私は資料を調べた後、疑問が減った。'
        req = request(self.with_answer(original, answer))
        artifact = self.generate(req).artifact
        self.assertEqual(len(artifact.graph.nodes), 3)
        edge, = artifact.graph.edges
        envelopes = {s.envelope.envelope_id: s.envelope for s in freeze_analysis_sources(req).sources}
        self.assertTrue(all(envelopes[e.source_envelope_id].source_role == 'SUPPLEMENTAL_ANSWER'
                            for e in edge.evidence_refs))
        self.assertTrue(all(len(n.record_refs) == 1 for n in artifact.graph.nodes))
        bad = self.with_answer(original, answer + '別の意味です。')
        self.assertIn('analysis_supplement_interpretation_pending', self.generate(request(bad)).reason_codes)

    def test_action_change_correction_and_withdrawal_apply_to_whole_episode(self):
        old, new = '私は資料を調べた後、疑問が減った', '私は記録を残したあとに、疑問が増えた'
        original = record(memo='私は仕事を続けたい。' + old + '。')
        req = request(self.with_answer(original, '「' + old + '」ではなく「' + new + '」です。'))
        artifact = self.generate(req).artifact
        self.assertEqual([n.visible_label for n in artifact.graph.nodes],
                         ['私は仕事を続けたい', '私は記録を残した', '疑問が増えた'])
        edge, = artifact.graph.edges
        envelope = next(s.envelope for s in freeze_analysis_sources(req).sources
                        if s.envelope.source_role == 'SUPPLEMENTAL_ANSWER')
        self.assertEqual(envelope.raw_utf8[edge.evidence_refs[-1].utf8_start:edge.evidence_refs[-1].utf8_end].decode(), new)
        self.assertEqual(artifact.graph.source_updates[0].operation, 'REVISE')
        withdrawn = self.generate(request(self.with_answer(original, '「' + old + '」は取り消します。'))).artifact
        self.assertEqual(len(withdrawn.graph.nodes), 1)
        self.assertFalse(withdrawn.graph.edges)
        partial = self.with_answer(original, '「私は資料を調べた」は取り消します。')
        self.assertIn('analysis_correction_target_unresolved', self.generate(request(partial)).reason_codes)
        unsupported = self.with_answer(original, '「' + old + '」ではなく「私は資料を調べた後、疑問が減ったという夢を見た」です。')
        self.assertIsNone(self.generate(request(unsupported)).artifact)

    def test_action_change_requires_shared_relation_and_exact_ranges(self):
        from cocolon_meaning_experience_engine.cores.analysis import intent_compiler as compiler
        build = compiler.build_final_stage1_grounded_observation_plan
        for memo, corruption in ((memo, corruption)
                for memo in ('私は資料を調べた後、疑問が減った。', '私は資料を調べてから、疑問が減った。')
                for corruption in ('relation', 'range', 'actor')):
            def corrupt(*args, **kwargs):
                plan = build(*args, **kwargs)
                if corruption == 'relation':
                    return replace(plan, relations=())
                n = plan.nuclei[1]
                frame = n.semantic_frame
                if corruption == 'actor':
                    frame = replace(frame, actor='other_person')
                else:
                    frame = replace(frame, attribute_codes=tuple(
                        'source_fragment_scalar_range:0:1' if c.startswith('source_fragment_scalar_range:') else c
                        for c in frame.attribute_codes))
                return replace(plan, nuclei=(plan.nuclei[0], replace(n, semantic_frame=frame)))
            with self.subTest(memo=memo, corruption=corruption), patch.object(compiler,
                    'build_final_stage1_grounded_observation_plan', side_effect=corrupt):
                self.assertIsNone(self.generate(request(record(memo=memo))).artifact)

    def test_te_after_past_change_preserves_all_nine_inflections_and_source(self):
        for action, lemma in (('考えをノートに書いて', '書く'), ('資料を調べて', '調べる'),
                ('方法を試して', '試す'), ('資料を見て', '見る'), ('資料を作って', '作る'),
                ('記録を残して', '残す'), ('考えを記録して', '記録する'),
                ('考えをメモして', 'メモする'), ('仕事を続けて', '続ける')):
            with self.subTest(action=action):
                clause = '私は' + action
                memo = clause + 'から、疑問が減った'
                req = request(record(memo='　' + memo + '。'))
                artifact = self.generate(req).artifact
                left, right = artifact.graph.nodes
                self.assertEqual(left.visible_label, clause)
                self.assertEqual((left.proposition.predicate_lemma, left.polarity,
                    left.modality, left.temporal_scope), (lemma, 'positive', 'fact', 'past'))
                self.assertEqual(left.proposition.dependent_form, 'TE_BEFORE_PAST_CHANGE')
                self.assertEqual([i for _, a, b in left.proposition.source_parts for i in range(a, b)],
                                 list(range(len(clause))))
                edge, = artifact.graph.edges
                self.assertEqual(edge.endpoint_refs, (left.node_ref, right.node_ref))
                source, = freeze_analysis_sources(req).sources
                literals = []
                for e in edge.evidence_refs:
                    literal = source.envelope.raw_utf8[e.utf8_start:e.utf8_end]
                    field = source.envelope.raw_utf8[e.field_utf8_start:e.field_utf8_end].decode()
                    self.assertEqual(literal.decode(), field[e.scalar_start:e.scalar_end])
                    self.assertEqual(hashlib.sha256(literal).hexdigest(), e.literal_sha256)
                    literals.append(literal.decode())
                self.assertEqual(literals, [clause, '疑問が減った', memo])
                projection = artifact.safe_projection(authenticated_owner_scope=OWNER)
                text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text']
                self.assertIn('疑問が減った（記録された変化）', text)
                self.assertIn(lemma + '（実行済み）', text)
                self.assertIn('原因を示す線ではありません', text)
                self.assertNotIn('dependent_form', json.dumps(projection))

    def test_te_surface_requires_its_own_whole_order_context(self):
        artifact = self.generate(request(record(memo='私は資料を調べてから、疑問が減った。'))).artifact
        edge, = artifact.graph.edges
        a, b, whole = edge.evidence_refs
        for edges in ((), (replace(edge, evidence_refs=(a, b)),),
                (replace(edge, evidence_refs=(a, b, replace(whole, scalar_end=whole.scalar_end + 1))),),
                (replace(edge, evidence_refs=(a, b, replace(whole, source_envelope_id='different-source'))),),
                (replace(edge, endpoint_refs=tuple(reversed(edge.endpoint_refs))),)):
            with self.subTest(edges=len(edges)), self.assertRaises(AnalysisSourceError):
                replace(artifact, graph=replace(artifact.graph, edges=edges)).safe_projection(
                    authenticated_owner_scope=OWNER)

    def test_te_after_answer_revision_and_withdrawal_keep_whole_source(self):
        old = '私は資料を調べた後、疑問が減った'
        new = '私は記録を残してから、疑問が増えた'
        original = record(memo='私は仕事を続けたい。' + old + '。')
        for answer in (new + '。', '「' + old + '」ではなく「' + new + '」です。'):
            with self.subTest(answer=answer):
                req = request(self.with_answer(original, answer))
                artifact = self.generate(req).artifact
                te_node = next(n for n in artifact.graph.nodes if n.proposition.dependent_form)
                edge = next(e for e in artifact.graph.edges if e.endpoint_refs[0] == te_node.node_ref)
                sources = {s.envelope.envelope_id: s.envelope for s in freeze_analysis_sources(req).sources}
                for evidence in edge.evidence_refs:
                    self.assertEqual(sources[evidence.source_envelope_id].source_role, 'SUPPLEMENTAL_ANSWER')
                e = edge.evidence_refs[-1]
                self.assertEqual(sources[e.source_envelope_id].raw_utf8[e.utf8_start:e.utf8_end].decode(), new)
                self.assertEqual(len(te_node.record_refs), 1)
                artifact.safe_projection(authenticated_owner_scope=OWNER)
        original_te = record(memo='私は仕事を続けたい。' + new + '。')
        withdrawn = self.generate(request(self.with_answer(original_te, '「' + new + '」は取り消します。'))).artifact
        self.assertEqual([n.node_kind for n in withdrawn.graph.nodes], ['ATTENTION_OR_THOUGHT'])
        self.assertFalse(withdrawn.graph.edges)
        for answer in ('「私は記録を残して」は取り消します。',
                '「' + new + '」ではなく「私は記録を残して」です。',
                new + '。別の意味です。'):
            with self.subTest(answer=answer):
                self.assertIsNone(self.generate(request(self.with_answer(original_te, answer))).artifact)

    def test_te_and_past_after_keep_distinct_episodes_without_cross_links(self):
        te = '私は資料を調べてから、疑問が減った。'
        past = '私は資料を調べた後、疑問が減った。'
        artifact = self.generate(request(record(memo=te + past), record(2, memo=te))).artifact
        self.assertEqual(len(artifact.graph.nodes), 6)
        self.assertEqual(len(artifact.graph.edges), 3)
        self.assertEqual(len({ref for e in artifact.graph.edges for ref in e.endpoint_refs}), 6)
        self.assertEqual(sum(bool(n.proposition.dependent_form) for n in artifact.graph.nodes), 2)
        artifact.safe_projection(authenticated_owner_scope=OWNER)

    def test_te_ending_never_asserts_a_standalone_or_unread_action(self):
        for memo in ('私は資料を調べて。', '私は資料を調べてから。',
                '私は資料を調べてから、疑問が減る。',
                '私は資料を調べてから、疑問が減ったという夢を見た。',
                '私は資料を調べてから、記録を残してから、疑問が減った。',
                '私は資料を調べてから、疑問が減ったら安心した。',
                '私は資料を調べてから、疑問が減ったかもしれない。',
                '私は資料を調べてから、疑問が減らなかった。',
                '私は資料を調べてから、疑問が減ったと聞いた。',
                '私は資料を調べてから、疑問が減った？',
                '私は資料を調べなくてから、疑問が減った。',
                '友人は資料を調べてから、疑問が減った。',
                '私は何を調べてから、疑問が減った。',
                '私は資料を調べてから、幾人が減った。',
                '私は資料を調べたから、疑問が減った。'):
            with self.subTest(memo=memo):
                self.assertIsNone(self.generate(request(record(memo=memo))).artifact)

        # The existing private wish preview may remain; it must never become
        # a completed te action, an order edge, or an unsupported safe label.
        wish = self.generate(request(record(memo='私は資料を調べてから、疑問を減らしたい。'))).artifact
        self.assertTrue(all(n.node_kind == 'ATTENTION_OR_THOUGHT' for n in wish.graph.nodes))
        self.assertFalse(wish.graph.edges)
        with self.assertRaises(AnalysisSourceError):
            wish.safe_projection(authenticated_owner_scope=OWNER)

    def test_past_feeling_after_action_keeps_experience_and_exact_source(self):
        forms = [('安心した', '安心する'), ('安心しました', '安心する'),
            ('落ち着いた', '落ち着く'),
            ('嬉しかった', '嬉しい'), ('うれしかった', 'うれしい')]
        for action in ('私は資料を調べた後、', '私は資料を調べたあとに、',
                       '私は資料を調べてから、'):
            for feeling, lemma in forms:
                for subject in ('', '私は'):
                    with self.subTest(action=action, feeling=feeling, subject=subject):
                        literal = action + subject + feeling
                        req = request(record(memo='　' + literal + '。'))
                        artifact = self.generate(req).artifact
                        action_node, result = artifact.graph.nodes
                        self.assertEqual(result.node_kind, 'IMMEDIATE_RESULT_OR_AFTERMATH')
                        self.assertEqual((result.proposition.result_state, result.modality,
                            result.temporal_scope, result.proposition.predicate_lemma),
                            ('PAST_FEELING', 'feeling', 'past', lemma))
                        self.assertEqual(result.proposition.actor, 'SELF' if subject else 'UNSPECIFIED')
                        edge, = artifact.graph.edges
                        self.assertEqual((edge.edge_kind, edge.endpoint_refs),
                            ('OBSERVED_ORDER', (action_node.node_ref, result.node_ref)))
                        sources = {s.envelope.envelope_id: s.envelope
                                   for s in freeze_analysis_sources(req).sources}
                        whole = edge.evidence_refs[-1]
                        self.assertEqual(sources[whole.source_envelope_id].raw_utf8[
                            whole.utf8_start:whole.utf8_end].decode(), literal)
                        for node in artifact.graph.nodes:
                            evidence, = node.evidence_refs
                            raw = sources[evidence.source_envelope_id].raw_utf8[
                                evidence.utf8_start:evidence.utf8_end]
                            self.assertEqual(hashlib.sha256(raw).hexdigest(), evidence.literal_sha256)
                            covered = {i for _, a, b in node.proposition.source_parts for i in range(a, b)}
                            self.assertEqual(covered, set(range(len(raw.decode()))))
                        projection = artifact.safe_projection(authenticated_owner_scope=OWNER)
                        text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text']
                        self.assertTrue(projection['nodes'][1]['visible_label'].endswith('（記録された気持ち）'))
                        self.assertNotIn('実行済み', projection['nodes'][1]['visible_label'])
                        self.assertIn(projection['nodes'][1]['visible_label'], text)
                        self.assertIn('原因を示す線ではありません', text)

    def test_past_feeling_requires_shared_pair_and_matching_modality(self):
        from cocolon_meaning_experience_engine.cores.analysis import intent_compiler as compiler
        original_builder = compiler.build_final_stage1_grounded_observation_plan
        for memo in ('私は資料を調べた後、安心した。', '私は資料を調べてから、落ち着いた。'):
            for mismatch in ('relation', 'modality'):
                def changed(*args, **kwargs):
                    plan = original_builder(*args, **kwargs)
                    if mismatch == 'relation':
                        return replace(plan, relations=())
                    return replace(plan, nuclei=tuple(replace(n, semantic_frame=replace(
                        n.semantic_frame, modality='wish')) if n.kind == 'change' else n for n in plan.nuclei))
                with self.subTest(memo=memo, mismatch=mismatch), patch.object(
                        compiler, 'build_final_stage1_grounded_observation_plan', side_effect=changed):
                    self.assertIsNone(self.generate(request(record(memo=memo))).artifact)

    def test_past_feeling_does_not_erase_unread_scope_or_inherit_other_subject(self):
        for ending in ('友人は安心した', '私も安心した', '少し安心した',
                '安心しなかった', '安心したい', '安心する', '安心したと思う',
                '安心したという夢を見た', '安心したと聞いた', '安心したかもしれない',
                '安心した？', '嬉しくなかった', '落ち着いたが不安だった',
                '落ち着きました', 'ほっとした'):
            with self.subTest(ending=ending):
                result = self.generate(request(record(memo='私は資料を調べてから、' + ending + '。')))
                self.assertFalse(result.artifact and any(n.proposition and
                    n.proposition.result_state == 'PAST_FEELING' for n in result.artifact.graph.nodes))
                self.assertFalse(result.artifact and result.artifact.graph.edges)
        for memo in ('安心した。', '私は落ち着いた。',
                '友人は資料を調べた後、安心した。',
                '私は資料を調べたら、安心した。'):
            with self.subTest(memo=memo):
                self.assertIsNone(self.generate(request(record(memo=memo))).artifact)

    def test_past_feeling_supplement_revision_withdrawal_and_episode_identity(self):
        old = '私は資料を調べた後、安心した'
        new = '私は記録を残してから、落ち着いた'
        base = record(memo='私は仕事を続けたい。' + old + '。')
        for answer, count in ((new + '。', 2), ('「' + old + '」ではなく「' + new + '」です。', 1)):
            with self.subTest(answer=answer):
                req = request(self.with_answer(base, answer))
                artifact = self.generate(req).artifact
                self.assertEqual(len(artifact.graph.edges), count)
                result = next(n for n in artifact.graph.nodes if n.proposition.predicate_lemma == '落ち着く')
                sources = {s.envelope.envelope_id: s.envelope for s in freeze_analysis_sources(req).sources}
                for e in result.evidence_refs:
                    self.assertEqual(sources[e.source_envelope_id].source_role, 'SUPPLEMENTAL_ANSWER')
                    self.assertEqual(sources[e.source_envelope_id].raw_utf8[e.utf8_start:e.utf8_end].decode(), '落ち着いた')
                artifact.safe_projection(authenticated_owner_scope=OWNER)
        withdrawn = self.generate(request(self.with_answer(base, '「' + old + '」は取り消します。'))).artifact
        self.assertEqual([n.node_kind for n in withdrawn.graph.nodes], ['ATTENTION_OR_THOUGHT'])
        self.assertFalse(withdrawn.graph.edges)
        for answer in ('「安心した」は取り消します。', new + '。別の意味です。'):
            self.assertIsNone(self.generate(request(self.with_answer(base, answer))).artifact)
        repeated = self.generate(request(record(memo=old + '。' + old + '。'), record(2, memo=old + '。'))).artifact
        self.assertEqual((len(repeated.graph.nodes), len(repeated.graph.edges)), (6, 3))
        self.assertEqual(len({ref for edge in repeated.graph.edges for ref in edge.endpoint_refs}), 6)

    def test_te_feeling_result_requires_own_order_context_for_safe_display(self):
        artifact = self.generate(request(record(memo='私は資料を調べてから、落ち着いた。'))).artifact
        artifact.safe_projection(authenticated_owner_scope=OWNER)
        for graph in (replace(artifact.graph, edges=()), replace(artifact.graph,
                edges=tuple(replace(e, evidence_refs=e.evidence_refs[:2]) for e in artifact.graph.edges))):
            with self.assertRaises(AnalysisSourceError):
                replace(artifact, graph=graph).safe_projection(authenticated_owner_scope=OWNER)

    def test_unsupported_action_change_never_leaves_a_factual_action_fragment(self):
        for memo in (
            '私は資料を調べた後、疑問が減ったという夢を見た。',
            '私は資料を調べたら、疑問が減ったという夢を見た。',
            '私は資料を調べた後、疑問が減ったかもしれない。',
            '私は資料を調べた後、疑問が減ったと聞いた。',
            '私は資料を調べた後、疑問が減った？',
            '私は資料を調べた後、疑問が減らなかった。',
            '私は資料を調べた後、何が減った。',
            '私は資料を調べた後、誰の負担が減った。',
            '私は資料を調べた後、幾人が減った。',
            '私は何を調べた後、疑問が減った。',
            '私は誰の資料を調べた後、疑問が減った。',
            '私は資料を調べなかった後、疑問が減った。',
            '友人は資料を調べた後、疑問が減った。',
            '友人によると、私は資料を調べた後、疑問が減った。',
            '私は資料を調べたら、疑問が減った。',
            '私は資料を調べた後、議論が進んだ。',
            '私は資料を調べた後、友人の不安が減った。',
            '疑問が減った。'):
            with self.subTest(memo=memo):
                self.assertIsNone(self.generate(request(record(memo=memo))).artifact)

    def test_explicit_past_presence_is_a_scene_with_exact_whole_clause_evidence(self):
        for subject, noun in (('私', '職場'), ('僕', '会議の会場'),
                              ('わたし', '図書館'), ('自分', 'オフィス')):
            for ending, polarity in (('いた', 'positive'), ('いました', 'positive'),
                                     ('いなかった', 'negative'), ('いませんでした', 'negative')):
                with self.subTest(subject=subject, noun=noun, ending=ending):
                    literal = subject + 'は' + noun + 'に' + ending
                    req = request(record(memo='　' + literal + '。'))
                    result = self.generate(req)
                    self.assertEqual(result.status, EngineStatus.GENERATED)
                    artifact = result.artifact
                    node, = artifact.graph.nodes
                    self.assertEqual((node.node_kind, node.polarity, node.modality, node.temporal_scope),
                                     ('SCENE', polarity, 'fact', 'past'))
                    self.assertEqual((node.proposition.actor, node.proposition.arguments),
                                     ('SELF', (('に', noun),)))
                    evidence, = node.evidence_refs
                    envelope = freeze_analysis_sources(req).sources[0].envelope
                    raw = envelope.raw_utf8[evidence.utf8_start:evidence.utf8_end]
                    field = envelope.raw_utf8[evidence.field_utf8_start:evidence.field_utf8_end].decode()
                    self.assertEqual(raw.decode(), literal)
                    self.assertEqual(field[evidence.scalar_start:evidence.scalar_end], literal)
                    self.assertEqual(hashlib.sha256(raw).hexdigest(), evidence.literal_sha256)
                    covered = {i for _, a, b in node.proposition.source_parts for i in range(a, b)}
                    self.assertEqual(covered, set(range(len(literal))))
                    label = noun + 'に' + ('いた' if polarity == 'positive' else 'いなかった') + '（記録された場面）'
                    visual = artifact.safe_projection(authenticated_owner_scope=OWNER)
                    self.assertEqual(visual['nodes'][0]['visible_label'], label)
                    self.assertIn(label, artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'])
                    self.assertFalse(artifact.graph.edges)
                    gaps = {gap.missing_scope for gap in artifact.graph.unknown_gaps}
                    self.assertNotIn('SCENE', gaps)
                    self.assertIn('ROLE', gaps)
                    self.assertIn('ACTION_OR_NONACTION', gaps)

    def test_past_presence_requires_matching_full_shared_event_witness(self):
        from cocolon_meaning_experience_engine.cores.analysis import intent_compiler as compiler
        original_builder = compiler.build_final_stage1_grounded_observation_plan
        for mismatch in ('grounding', 'retention', 'claim_scope', 'kind', 'actor',
                         'modality', 'polarity', 'time', 'fragment', 'dependency'):
            def changed(*args, **kwargs):
                plan = original_builder(*args, **kwargs)
                n, = plan.nuclei
                changes = {'grounding': {'grounding_kind': 'inferred'},
                    'retention': {'retention': 'optional'},
                    'claim_scope': {'allowed_claim_scope': 'unknown'}, 'kind': {'kind': 'action'}}
                frame_changes = {'actor': {'actor': 'other'}, 'modality': {'modality': 'wish'},
                    'polarity': {'polarity': 'negative'}, 'time': {'time_scope': 'future'},
                    'fragment': {'attribute_codes': n.semantic_frame.attribute_codes + (
                        'source_fragment_scalar_range:0:7', 'source_fragment_scalar_source:normalized_raw_text')},
                    'dependency': {'attribute_codes': n.semantic_frame.attribute_codes + ('semantic_dependency:unknown',)}}
                n = replace(n, **changes[mismatch]) if mismatch in changes else replace(
                    n, semantic_frame=replace(n.semantic_frame, **frame_changes[mismatch]))
                return replace(plan, nuclei=(n,))
            with self.subTest(mismatch=mismatch), patch.object(
                    compiler, 'build_final_stage1_grounded_observation_plan', side_effect=changed):
                self.assertIsNone(self.generate(request(record(memo='私は職場にいた。'))).artifact)

    def test_past_presence_does_not_erase_unread_scope_or_infer_a_role(self):
        for memo in ('職場にいた。', '友人は職場にいた。', '私も職場にいた。',
                '私は職場にいたい。', '私は職場にいる。', '私は職場にいる予定です。',
                '私は職場にいたと思う。', '私は職場にいたかもしれない。',
                '私は職場にいたと聞いた。', '私は職場にいたという夢を見た。',
                '私は夢の中で職場にいた。', '私は職場にいた？',
                'もし私は職場にいたなら、安心できる。', '友人の報告です。私は職場にいた。',
                '私は何処にいた。', '私は誰の家にいた。', '私は幾人の会議にいた。',
                '私は職場でいた。', '私は不安にいた。', '私は職場に少しいた。',
                '私は担当者として職場にいた。', '私は司会者だった。'):
            with self.subTest(memo=memo):
                result = self.generate(request(record(memo=memo)))
                self.assertFalse(result.artifact and any(n.proposition and
                    n.proposition.scene_state for n in result.artifact.graph.nodes))
        self.assertIsNone(self.generate(request(record(memo='', action='私は職場にいた。'))).artifact)
        artifact = self.generate(request(record(memo='私は職場で資料を調べた。'))).artifact
        self.assertEqual([n.node_kind for n in artifact.graph.nodes], ['ACTION_OR_NONACTION'])

    def test_scene_never_treats_mechanically_split_span_as_a_complete_sentence(self):
        long_tail = 'その内容を忘れないように長い文章として残しています' * 4
        for memo in ('私は職場にいた、という夢を見たのですが、' + long_tail + '。',
                     long_tail + '、私は職場にいた。',
                     'でも私は職場にいた。'):
            with self.subTest(memo=memo):
                result = self.generate(request(record(memo=memo)))
                self.assertFalse(result.artifact and any(
                    n.node_kind == 'SCENE' for n in result.artifact.graph.nodes))
        for separator in ('。', '。　', '\n'):
            with self.subTest(separator=separator):
                result = self.generate(request(record(memo=long_tail + separator + '私は職場にいた。')))
                self.assertEqual([n.node_kind for n in result.artifact.graph.nodes], ['SCENE'])

    def test_scene_action_order_requires_written_connective(self):
        for connector, count in (('', 0), ('その後、', 1), ('それから、', 1)):
            with self.subTest(connector=connector):
                artifact = self.generate(request(record(
                    memo='私は職場にいた。' + connector + '私は資料を調べた。'))).artifact
                self.assertEqual([n.node_kind for n in artifact.graph.nodes], ['SCENE', 'ACTION_OR_NONACTION'])
                self.assertEqual(len(artifact.graph.edges), count)
                if count:
                    edge, = artifact.graph.edges
                    self.assertEqual((edge.edge_kind, edge.endpoint_refs),
                        ('OBSERVED_ORDER', tuple(n.node_ref for n in artifact.graph.nodes)))
                    self.assertIn('原因を示す線ではありません',
                        artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'])

    def test_scene_supplement_restatement_revision_and_withdrawal_keep_source_identity(self):
        old, new = '私は職場にいた', '私は図書館にいませんでした'
        base = record(memo=old + '。私は資料を調べた。')
        for answer, count in ((new + '。', 2), ('「' + old + '」ではなく「' + new + '」です。', 1)):
            with self.subTest(answer=answer):
                req = request(self.with_answer(base, answer))
                artifact = self.generate(req).artifact
                scenes = [n for n in artifact.graph.nodes if n.node_kind == 'SCENE']
                self.assertEqual(len(scenes), count)
                node = next(n for n in scenes if n.polarity == 'negative')
                source = next(s for s in freeze_analysis_sources(req).sources
                              if s.envelope.source_role == 'SUPPLEMENTAL_ANSWER')
                evidence, = node.evidence_refs
                self.assertEqual(evidence.source_envelope_id, source.envelope.envelope_id)
                self.assertEqual(source.envelope.raw_utf8[evidence.utf8_start:evidence.utf8_end].decode(), new)
                self.assertEqual(len(node.record_refs), 1)
                artifact.safe_projection(authenticated_owner_scope=OWNER)
        withdrawn = self.generate(request(self.with_answer(base, '「' + old + '」は取り消します。'))).artifact
        self.assertEqual([n.node_kind for n in withdrawn.graph.nodes], ['ACTION_OR_NONACTION'])
        self.assertIn('SCENE', {g.missing_scope for g in withdrawn.graph.unknown_gaps})
        for answer in ('私は職場にいなかった。', '「職場にいた」は取り消します。', new + '。別の意味です。'):
            self.assertIsNone(self.generate(request(self.with_answer(base, answer))).artifact)
        answered = self.with_answer(record(memo=old + '。'), '僕は職場にいました。')
        artifact = self.generate(request(answered, record(2, memo='わたしは職場にいた。'))).artifact
        node, = artifact.graph.nodes
        self.assertEqual((len(node.record_refs), len(node.evidence_refs)), (2, 3))
        self.assertEqual(artifact.safe_projection(authenticated_owner_scope=OWNER)['nodes'][0]['evidence_badge_count'], 2)
        self.assertFalse(artifact.graph.edges)

    def test_positive_and_negative_scene_stay_distinct_and_safe_surface_replays_them(self):
        artifact = self.generate(request(record(memo='私は職場にいた。'),
                                         record(2, memo='私は職場にいなかった。'))).artifact
        self.assertEqual({n.polarity for n in artifact.graph.nodes}, {'positive', 'negative'})
        self.assertEqual(len(artifact.graph.nodes), 2)
        self.assertFalse(artifact.graph.edges)
        node = artifact.graph.nodes[0]
        for changed in (replace(node, polarity='negative'),
                        replace(node, proposition=replace(node.proposition, scene_state=''))):
            with self.assertRaises(AnalysisSourceError):
                replace(artifact, graph=replace(artifact.graph,
                    nodes=(changed,) + artifact.graph.nodes[1:])).safe_projection(authenticated_owner_scope=OWNER)

    def test_explicit_past_responsibility_preserves_role_polarity_and_exact_evidence(self):
        for subject, noun in (('私', '会議の司会'), ('僕', '受付'),
                              ('わたし', '調査'), ('自分', '資料の確認')):
            for ending, polarity in (('担当した', 'positive'), ('担当しました', 'positive'),
                                     ('担当しなかった', 'negative'), ('担当しませんでした', 'negative')):
                with self.subTest(subject=subject, noun=noun, ending=ending):
                    literal = subject + 'は' + noun + 'を' + ending
                    req = request(record(memo='　' + literal + '。'))
                    artifact = self.generate(req).artifact
                    node, = artifact.graph.nodes
                    self.assertEqual((node.node_kind, node.polarity, node.modality, node.temporal_scope),
                                     ('ROLE', polarity, 'fact', 'past'))
                    self.assertEqual((node.proposition.actor, node.proposition.arguments),
                                     ('SELF', (('を', noun),)))
                    evidence, = node.evidence_refs
                    envelope = freeze_analysis_sources(req).sources[0].envelope
                    raw = envelope.raw_utf8[evidence.utf8_start:evidence.utf8_end]
                    field = envelope.raw_utf8[evidence.field_utf8_start:evidence.field_utf8_end].decode()
                    self.assertEqual(raw.decode(), literal)
                    self.assertEqual(field[evidence.scalar_start:evidence.scalar_end], literal)
                    self.assertEqual(hashlib.sha256(raw).hexdigest(), evidence.literal_sha256)
                    self.assertEqual({i for _, a, b in node.proposition.source_parts for i in range(a, b)},
                                     set(range(len(literal))))
                    label = noun + 'を' + ('担当した' if polarity == 'positive' else '担当しなかった') + '（記録された担当）'
                    self.assertEqual(artifact.safe_projection(authenticated_owner_scope=OWNER)['nodes'][0]['visible_label'], label)
                    self.assertIn(label, artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'])
                    self.assertNotIn('ROLE', {g.missing_scope for g in artifact.graph.unknown_gaps})
                    self.assertIn('ACTION_OR_NONACTION', {g.missing_scope for g in artifact.graph.unknown_gaps})
                    self.assertFalse(artifact.graph.edges)
                    with self.assertRaises(AnalysisSourceError):
                        replace(artifact, graph=replace(artifact.graph, nodes=(replace(node,
                            proposition=replace(node.proposition, role_state='')),))).safe_projection(authenticated_owner_scope=OWNER)

    def test_responsibility_requires_matching_shared_event_not_keyword_action(self):
        from cocolon_meaning_experience_engine.cores.analysis import intent_compiler as compiler
        original_builder = compiler.build_final_stage1_grounded_observation_plan
        for mismatch in ('actor', 'modality', 'polarity', 'predicate_kind', 'time_scope', 'fragment', 'dependency', 'optional'):
            def changed(*args, **kwargs):
                plan = original_builder(*args, **kwargs)
                n, = plan.nuclei
                if mismatch == 'optional':
                    return replace(plan, nuclei=(replace(n, retention='optional'),))
                codes = n.semantic_frame.attribute_codes
                changes = {'actor': {'actor': 'other'}, 'modality': {'modality': 'wish'},
                    'polarity': {'polarity': 'negative'}, 'predicate_kind': {'predicate_kind': 'action'},
                    'time_scope': {'time_scope': 'future'},
                    'fragment': {'attribute_codes': codes + ('source_fragment_scalar_range:0:14',
                        'source_fragment_scalar_source:normalized_raw_text')},
                    'dependency': {'attribute_codes': codes + ('semantic_dependency:unknown',)}}
                return replace(plan, nuclei=(replace(n, semantic_frame=replace(n.semantic_frame, **changes[mismatch])),))
            with self.subTest(mismatch=mismatch), patch.object(
                    compiler, 'build_final_stage1_grounded_observation_plan', side_effect=changed):
                self.assertIsNone(self.generate(request(record(memo='私は会議の司会を担当した。'))).artifact)
        # The shared owner reads this nominal keyword as action. Do not
        # turn it into either a responsibility or an actually completed log.
        self.assertIsNone(self.generate(request(record(memo='私は記録を担当した。'))).artifact)

    def test_responsibility_does_not_infer_identity_or_drop_unread_scope(self):
        long_tail = 'その内容を忘れないように長い文章として残しています' * 4
        for memo in ('私は司会者です。', '私の役割は司会だった。', '私は会議の司会担当だった。',
                '会議の司会を担当した。', '友人は会議の司会を担当した。', '私も会議の司会を担当した。',
                '私は会議の司会を担当している。', '私は会議の司会を担当したい。',
                '私は会議の司会を担当する予定です。', '私は会議の司会を担当できなかった。',
                '私は会議の司会を担当したと思う。', '私は会議の司会を担当したと聞いた。',
                '私は会議の司会を担当したという夢を見た。', '私は会議の司会を担当したかもしれない。',
                '私は会議の司会を担当した？', '友人の報告です。私は会議の司会を担当した。',
                '私は何を担当した。', '私は誰の仕事を担当した。', '私は幾人の仕事を担当した。',
                '私は会議の司会と受付を担当した。', '私は会議の司会を少し担当した。',
                '私は会議の司会を担当した、という夢を見たのですが、' + long_tail + '。',
                long_tail + '、私は会議の司会を担当した。', 'でも私は会議の司会を担当した。'):
            with self.subTest(memo=memo):
                result = self.generate(request(record(memo=memo)))
                self.assertFalse(result.artifact and any(n.node_kind == 'ROLE' for n in result.artifact.graph.nodes))
        self.assertIsNone(self.generate(request(record(memo='', action='私は会議の司会を担当した。'))).artifact)

    def test_role_supplement_revision_withdrawal_and_restatement_keep_identity(self):
        old, new = '私は会議の司会を担当した', '私は受付を担当しませんでした'
        base = record(memo=old + '。私は資料を調べた。')
        for answer, count in ((new + '。', 2), ('「' + old + '」ではなく「' + new + '」です。', 1)):
            with self.subTest(answer=answer):
                req = request(self.with_answer(base, answer))
                artifact = self.generate(req).artifact
                roles = [n for n in artifact.graph.nodes if n.node_kind == 'ROLE']
                self.assertEqual(len(roles), count)
                role = next(n for n in roles if n.polarity == 'negative')
                source = next(s for s in freeze_analysis_sources(req).sources
                              if s.envelope.source_role == 'SUPPLEMENTAL_ANSWER')
                evidence, = role.evidence_refs
                self.assertEqual(evidence.source_envelope_id, source.envelope.envelope_id)
                self.assertEqual(source.envelope.raw_utf8[evidence.utf8_start:evidence.utf8_end].decode(), new)
                self.assertEqual(len(role.record_refs), 1)
                artifact.safe_projection(authenticated_owner_scope=OWNER)
        withdrawn = self.generate(request(self.with_answer(base, '「' + old + '」は取り消します。'))).artifact
        self.assertEqual([n.node_kind for n in withdrawn.graph.nodes], ['ACTION_OR_NONACTION'])
        self.assertIn('ROLE', {g.missing_scope for g in withdrawn.graph.unknown_gaps})
        for answer in ('私は会議の司会を担当しなかった。', '「会議の司会」は取り消します。', new + '。別の意味です。'):
            self.assertIsNone(self.generate(request(self.with_answer(base, answer))).artifact)
        answered = self.with_answer(record(memo=old + '。'), '僕は会議の司会を担当しました。')
        artifact = self.generate(request(answered, record(2, memo='わたしは会議の司会を担当した。'))).artifact
        node, = artifact.graph.nodes
        self.assertEqual((len(node.record_refs), len(node.evidence_refs)), (2, 3))
        self.assertFalse(artifact.graph.edges)
        both = self.generate(request(record(memo=old + '。'),
            record(2, memo='私は会議の司会を担当しなかった。'))).artifact
        self.assertEqual({n.polarity for n in both.graph.nodes}, {'positive', 'negative'})
        self.assertEqual(len(both.graph.nodes), 2)
        self.assertFalse(both.graph.edges)

    def test_role_joins_observed_stages_without_inventing_order_or_task_completion(self):
        artifact = self.generate(request(record(memo='私は職場にいた。私は会議の司会を担当した。'
            '私は仕事を続けたい。私は資料を調べた後、安心した。'))).artifact
        self.assertEqual([n.node_kind for n in artifact.graph.nodes], [
            'SCENE', 'ROLE', 'ATTENTION_OR_THOUGHT', 'ACTION_OR_NONACTION', 'IMMEDIATE_RESULT_OR_AFTERMATH'])
        self.assertEqual(len(artifact.graph.edges), 1)
        self.assertEqual(artifact.graph.edges[0].endpoint_refs,
                         tuple(n.node_ref for n in artifact.graph.nodes[-2:]))
        self.assertTrue(all(g.missing_scope == 'ROUTE_CONNECTION' for g in artifact.graph.unknown_gaps))
        artifact.safe_projection(authenticated_owner_scope=OWNER)
        for connector, count in (('', 0), ('その後、', 1)):
            value = self.generate(request(record(memo='私は会議の司会を担当しなかった。'
                + connector + '私は資料を調べた。'))).artifact
            self.assertEqual(len(value.graph.edges), count)
            self.assertEqual([n.node_kind for n in value.graph.nodes], ['ROLE', 'ACTION_OR_NONACTION'])
            if count:
                self.assertIn('原因を示す線ではありません', value.safe_text_projection(authenticated_owner_scope=OWNER)['text'])

    def test_prefixed_scene_and_role_keep_finite_polarity_and_complete_source(self):
        for prefix, lead in (('今日、', 'この記述時点の今日：'), ('昨日', 'この記述時点の昨日：'),
                             ('その後、', 'その後：'), ('それから、', 'それから：')):
            for clause, kind, label in (
                    ('私は職場にいた', 'SCENE', '職場にいた（記録された場面）'),
                    ('私は職場にいませんでした', 'SCENE', '職場にいなかった（記録された場面）'),
                    ('私は会議の司会を担当しました', 'ROLE', '会議の司会を担当した（記録された担当）'),
                    ('私は会議の司会を担当しなかった', 'ROLE', '会議の司会を担当しなかった（記録された担当）')):
                with self.subTest(prefix=prefix, clause=clause):
                    literal = prefix + clause
                    req = request(record(memo=literal + '。'))
                    artifact = self.generate(req).artifact
                    node, = artifact.graph.nodes
                    self.assertEqual((node.node_kind, node.modality, node.temporal_scope), (kind, 'fact', 'past'))
                    e, = node.evidence_refs
                    source = freeze_analysis_sources(req).sources[0].envelope
                    self.assertEqual(source.raw_utf8[e.utf8_start:e.utf8_end].decode(), literal)
                    self.assertEqual(hashlib.sha256(literal.encode()).hexdigest(), e.literal_sha256)
                    covered = {i for _, a, b in node.proposition.source_parts for i in range(a, b)}
                    self.assertEqual(covered, set(range(len(literal))))
                    visual = artifact.safe_projection(authenticated_owner_scope=OWNER)
                    self.assertEqual(visual['nodes'][0]['visible_label'], lead + label)
                    self.assertIn(lead + label, artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'])
                    self.assertFalse(visual['edges'])
                    if prefix in ('その後、', 'それから、'):
                        self.assertTrue(any(g.missing_scope == 'ROUTE_CONNECTION' for g in artifact.graph.unknown_gaps))

    def test_scene_role_action_route_keeps_written_order_and_occurrences(self):
        req = request(record(memo='今日、私は職場にいた。その後、私は会議の司会を担当した。'
                             'それから、私は資料を調べた。'))
        artifact = self.generate(req).artifact
        self.assertEqual([n.node_kind for n in artifact.graph.nodes], ['SCENE', 'ROLE', 'ACTION_OR_NONACTION'])
        self.assertEqual([n.proposition.relative_day for n in artifact.graph.nodes], ['TODAY', '', ''])
        self.assertEqual([e.endpoint_refs for e in artifact.graph.edges], [('n1', 'n2'), ('n2', 'n3')])
        self.assertTrue(all(e.edge_kind == 'OBSERVED_ORDER' for e in artifact.graph.edges))
        self.assertNotIn('ROUTE_CONNECTION', {g.missing_scope for g in artifact.graph.unknown_gaps})
        for edge in artifact.graph.edges:
            self.assertEqual(len(edge.evidence_refs), 2)
        repeated = self.generate(request(record(memo='私は職場にいた。その後、私は会議の司会を担当した。'
            'その後、私は職場にいた。'))).artifact
        self.assertEqual([n.node_kind for n in repeated.graph.nodes], ['SCENE', 'ROLE', 'SCENE'])
        self.assertEqual([e.endpoint_refs for e in repeated.graph.edges], [('n1', 'n2'), ('n2', 'n3')])
        self.assertIn('原因を示す線ではありません', repeated.safe_text_projection(authenticated_owner_scope=OWNER)['text'])

    def test_prefixed_event_days_do_not_invent_order_or_cross_source_identity(self):
        first = record(memo='昨日私は職場にいた。今日私は職場にいなかった。')
        artifact = self.generate(request(first)).artifact
        self.assertEqual(len(artifact.graph.nodes), 2)
        self.assertFalse(artifact.graph.edges)
        self.assertFalse(artifact.graph.conflicts)
        repeated = self.generate(request(first, record(2, memo='昨日私は職場にいた。'))).artifact
        self.assertEqual(len(repeated.graph.nodes), 3)
        unmarked = self.generate(request(record(memo='私は職場にいた。今日私は会議の司会を担当した。'))).artifact
        self.assertFalse(unmarked.graph.edges)
        split = self.generate(request(record(memo='私は職場にいた。'),
            record(2, memo='その後私は会議の司会を担当した。'))).artifact
        self.assertFalse(split.graph.edges)

    def test_prefixed_events_do_not_erase_unread_operators_or_reported_speakers(self):
        tail = 'その内容を忘れないように長い文章として残しています' * 4
        for clause in ('私は職場にいた', '私は会議の司会を担当した'):
            for memo in ('昨日その後' + clause, 'その後今日' + clause, '昨日は' + clause,
                    '昨日、' + clause.replace('私は', '友人は'), '今日、' + clause + '？',
                    '昨日、' + clause + 'と聞いた', '昨日、' + clause + 'かもしれない',
                    '昨日、' + clause + 'という夢を見た', 'もし昨日、' + clause + 'なら安心できる',
                    '友人から聞いた話です。昨日、' + clause,
                    '夢を見た。今日、' + clause,
                    '今日、' + clause + '、という夢を見たのですが、' + tail,
                    tail + '、昨日、' + clause):
                with self.subTest(memo=memo):
                    artifact = self.generate(request(record(memo=memo + '。'))).artifact
                    self.assertFalse(artifact and any(n.node_kind in {'SCENE', 'ROLE'} for n in artifact.graph.nodes))
        for memo in ('今日私は職場にいる。', '今日私は会議の司会を担当したい。',
                     '私は昨日職場にいた。', '今日私は昨日職場にいた。',
                     '私は今日会議の司会を担当した。', '昨日私は記録を担当した。'):
            with self.subTest(memo=memo):
                artifact = self.generate(request(record(memo=memo))).artifact
                self.assertFalse(artifact and any(n.node_kind in {'SCENE', 'ROLE'} for n in artifact.graph.nodes))

    def test_prefixed_events_still_require_shared_event_witness(self):
        from cocolon_meaning_experience_engine.cores.analysis import intent_compiler as compiler
        builder = compiler.build_final_stage1_grounded_observation_plan
        for clause in ('今日私は職場にいた。', 'その後私は会議の司会を担当した。'):
            for mismatch in ('kind', 'time', 'actor', 'fragment'):
                def changed(*args, **kwargs):
                    plan = builder(*args, **kwargs)
                    n, = plan.nuclei
                    if mismatch == 'kind':
                        n = replace(n, kind='action')
                    else:
                        updates = {'time': {'time_scope': 'future'}, 'actor': {'actor': 'other'},
                            'fragment': {'attribute_codes': n.semantic_frame.attribute_codes + (
                                'source_fragment_scalar_range:0:1', 'source_fragment_scalar_source:normalized_raw_text')}}
                        n = replace(n, semantic_frame=replace(n.semantic_frame, **updates[mismatch]))
                    return replace(plan, nuclei=(n,))
                with self.subTest(clause=clause, mismatch=mismatch), patch.object(
                        compiler, 'build_final_stage1_grounded_observation_plan', side_effect=changed):
                    self.assertIsNone(self.generate(request(record(memo=clause))).artifact)
        artifact = self.generate(request(record(memo='昨日私は職場にいた。'))).artifact
        node, = artifact.graph.nodes
        for parts in (replace(node.proposition, relative_day='TODAY'),
                      replace(node.proposition, source_parts=node.proposition.source_parts[1:])):
            with self.assertRaises(AnalysisSourceError):
                replace(artifact, graph=replace(artifact.graph,
                    nodes=(replace(node, proposition=parts),))).safe_projection(authenticated_owner_scope=OWNER)

    def test_prefixed_event_answers_corrections_and_withdrawals_keep_answer_evidence(self):
        old, new = '昨日私は職場にいた', '今日私は図書館にいなかった'
        base = record(memo=old + '。その後私は会議の司会を担当した。')
        for answer in (new + '。', '「' + old + '」ではなく「' + new + '」です。'):
            with self.subTest(answer=answer):
                req = request(self.with_answer(base, answer))
                artifact = self.generate(req).artifact
                node = next(n for n in artifact.graph.nodes if n.polarity == 'negative')
                e, = node.evidence_refs
                source = next(s.envelope for s in freeze_analysis_sources(req).sources
                              if s.envelope.source_role == 'SUPPLEMENTAL_ANSWER')
                self.assertEqual(source.raw_utf8[e.utf8_start:e.utf8_end].decode(), new)
                self.assertEqual(node.proposition.relative_day, 'TODAY')
                artifact.safe_projection(authenticated_owner_scope=OWNER)
        # The answer's yesterday may be the original record's today.
        self.assertIsNone(self.generate(request(self.with_answer(record(memo='今日私は職場にいた。'),
            '昨日私は職場にいなかった。'))).artifact)
        original = record(memo='私は職場にいた。その後私は会議の司会を担当した。'
                              'その後私は資料を調べた。')
        withdrawn = self.generate(request(self.with_answer(original,
            '「その後私は会議の司会を担当した」は取り消します。'))).artifact
        self.assertEqual([n.node_kind for n in withdrawn.graph.nodes], ['SCENE', 'ACTION_OR_NONACTION'])
        self.assertFalse(withdrawn.graph.edges)
        revised = self.generate(request(self.with_answer(original,
            '「その後私は会議の司会を担当した」ではなく「今日私は会議の受付を担当した」です。'))).artifact
        self.assertFalse(revised.graph.edges)

    def test_prefixed_event_period_comparison_uses_meaning_and_written_day(self):
        unchanged = self.compared('今日僕は職場にいました。', '今日私は職場にいた。').artifact
        self.assertFalse(unchanged.period_comparison.change_claims)
        changed = self.compared('今日私は会議の司会を担当した。', '昨日私は会議の司会を担当した。').artifact
        self.assertIn('ROUTE_EVIDENCE_CHANGED', [c.change_kind for c in changed.period_comparison.change_claims])

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
            '私は明日、資料を調べた。',
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
        for source in ('私は明日、考えをノートに書いた。',
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
