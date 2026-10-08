"""Public synthetic inputs only; offline Analysis behavior and source boundaries."""
from dataclasses import FrozenInstanceError, replace
import hashlib
import json
import re
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

    def test_standalone_self_past_feeling_preserves_source_and_explicit_order(self):
        for feeling in ('安心した', '安心しました', '落ち着いた', '嬉しかった', 'うれしかった'):
            for subject in ('私は', '僕は、', 'ぼくは， ', '俺は', 'おれは', 'わたしは、　', '自分は'):
                with self.subTest(feeling=feeling, subject=subject):
                    literal = subject + feeling
                    req = request(record(memo='　' + literal + '。'))
                    artifact = self.generate(req).artifact
                    self.assertIsNotNone(artifact)
                    node, = artifact.graph.nodes
                    self.assertEqual((node.node_kind, node.proposition.actor,
                        node.proposition.result_state, node.modality, node.temporal_scope),
                        ('IMMEDIATE_RESULT_OR_AFTERMATH', 'SELF', 'PAST_FEELING', 'feeling', 'past'))
                    self.assertFalse(artifact.graph.edges)
                    source, = freeze_analysis_sources(req).sources
                    evidence, = node.evidence_refs
                    raw = source.envelope.raw_utf8[evidence.utf8_start:evidence.utf8_end]
                    field = source.envelope.raw_utf8[evidence.field_utf8_start:evidence.field_utf8_end].decode()
                    self.assertEqual(raw.decode(), literal)
                    self.assertEqual(field[evidence.scalar_start:evidence.scalar_end], literal)
                    self.assertEqual(hashlib.sha256(raw).hexdigest(), evidence.literal_sha256)
                    self.assertEqual({i for _, a, b in node.proposition.source_parts for i in range(a, b)},
                                     set(range(len(literal))))
                    label = artifact.safe_projection(authenticated_owner_scope=OWNER)['nodes'][0]['visible_label']
                    self.assertTrue(label.endswith('（記録された気持ち）'))
                    for marker, action in (('その後', '残した'), ('それから', '残さなかった')):
                        ordered = self.generate(request(record(memo=literal + '。'
                            + marker + '、私は記録を' + action + '。'))).artifact
                        first, second = ordered.graph.nodes
                        edge, = ordered.graph.edges
                        self.assertEqual((edge.edge_kind, edge.endpoint_refs),
                            ('OBSERVED_ORDER', (first.node_ref, second.node_ref)))
                        self.assertEqual(edge.evidence_refs, first.evidence_refs + second.evidence_refs)
                        text = ordered.safe_text_projection(authenticated_owner_scope=OWNER)['text']
                        self.assertIn(label, text)
                        self.assertIn('原因を示す線ではありません', text)

    def test_polite_past_feelings_preserve_single_and_following_order(self):
        for polite, plain in (('落ち着きました', '落ち着いた'),
                              ('嬉しかったです', '嬉しかった'), ('うれしかったです', 'うれしかった')):
            for subject in ('私は', '僕は、', 'ぼくは', '俺は', 'おれは', 'わたしは， ', '自分は'):
                with self.subTest(polite=polite, subject=subject):
                    literal = subject + polite
                    req = request(record(memo=literal + '。その後、私は記録を残した。'))
                    artifact = self.generate(req).artifact
                    self.assertIsNotNone(artifact)
                    feelings = [n for n in artifact.graph.nodes if n.proposition.result_state == 'PAST_FEELING']
                    feeling, = feelings
                    self.assertEqual((feeling.proposition.actor, feeling.modality,
                        feeling.temporal_scope, feeling.proposition.polarity), ('SELF', 'feeling', 'past', 'positive'))
                    self.assertEqual(len(artifact.graph.nodes), 2)
                    self.assertEqual(len(artifact.graph.edges), 1)
                    source, = freeze_analysis_sources(req).sources
                    evidence, = feeling.evidence_refs
                    raw = source.envelope.raw_utf8[evidence.utf8_start:evidence.utf8_end]
                    self.assertEqual(raw.decode(), subject + polite)
                    self.assertEqual(hashlib.sha256(raw).hexdigest(), evidence.literal_sha256)
                    self.assertEqual(artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'],
                        self.generate(request(record(memo=(subject + plain)
                            + '。その後、私は記録を残した。'))).artifact.safe_text_projection(
                                authenticated_owner_scope=OWNER)['text'])

    def test_polite_past_feelings_keep_unread_scope_pending(self):
        for feeling in ('落ち着きました', '嬉しかったです', 'うれしかったです'):
            for prefix, suffix in (('友人は', '。'), ('私は少し', '。'), ('私は', 'か。'),
                    ('私は', '？'), ('私は', 'と聞いた。'), ('私は', '。とは言えない。'),
                    ('私は', '\nわけではない。'), ('私は', '。と思う。'), ('「私は', '」。'),
                    ('夢を見た。私は', '。'), ('友人によると。私は', '。'),
                    ('友人は言った。私は', '。')):
                for action in ('', '私は資料を調べた後、'):
                    with self.subTest(feeling=feeling, prefix=prefix, suffix=suffix, action=action):
                        result = self.generate(request(record(memo=action + prefix + feeling + suffix)))
                        self.assertFalse(result.artifact and any(n.proposition.result_state == 'PAST_FEELING'
                            for n in result.artifact.graph.nodes))
            self.assertIsNone(self.generate(request(record(memo=feeling + '。'))).artifact)
            self.assertIsNone(self.generate(request(record(memo='', action='私は' + feeling + '。'))).artifact)
            for action in ('私は資料を調べた後、', '私は資料を調べてから、'):
                for subject in ('', '私は、'):
                    with self.subTest(action=action, subject=subject, feeling=feeling):
                        self.assertIsNone(self.generate(request(record(memo=action + subject + feeling + '。'))).artifact)

    def test_polite_past_feelings_keep_answer_sources_and_period_meaning(self):
        for polite, plain in (('落ち着きました', '落ち着いた'),
                              ('嬉しかったです', '嬉しかった'), ('うれしかったです', 'うれしかった')):
            new = '私は、' + polite
            old = '私は安心した'
            original = record(memo=old + '。その後、私は記録を残した。')
            for answer in (new + '。', '「' + old + '」ではなく「' + new + '」です。'):
                with self.subTest(polite=polite, answer=answer):
                    req = request(self.with_answer(original, answer))
                    artifact = self.generate(req).artifact
                    self.assertIsNotNone(artifact)
                    feeling = next(n for n in artifact.graph.nodes if n.visible_label == new)
                    sources = {s.envelope.envelope_id: s.envelope for s in freeze_analysis_sources(req).sources}
                    evidence, = feeling.evidence_refs
                    source = sources[evidence.source_envelope_id]
                    self.assertEqual(source.source_role, 'SUPPLEMENTAL_ANSWER')
                    self.assertEqual(source.raw_utf8[evidence.utf8_start:evidence.utf8_end].decode(), new)
                    if answer.startswith('「'):
                        self.assertFalse(artifact.graph.edges)
                    artifact.safe_projection(authenticated_owner_scope=OWNER)
            withdrawn = self.generate(request(self.with_answer(record(memo=new + '。その後、私は記録を残した。'),
                '「' + new + '」は取り消します。'))).artifact
            self.assertEqual(len(withdrawn.graph.nodes), 1)
            self.assertFalse(withdrawn.graph.edges)
            compared = self.compared(new + '。その後、私は記録を残した。',
                '僕は' + plain + '。その後、私は記録を残した。').artifact
            self.assertEqual(compared.period_comparison.change_claims, ())
            repeated = self.generate(request(record(memo=new + '。'), record(2, memo='僕は' + plain + '。'))).artifact
            node, = repeated.graph.nodes
            self.assertEqual(len(node.evidence_refs), 2)
            with self.assertRaises(AnalysisSourceError):
                replace(repeated, graph=replace(repeated.graph, nodes=(replace(node,
                    proposition=replace(node.proposition, polarity='negative')),))).safe_projection(
                        authenticated_owner_scope=OWNER)

    def test_standalone_self_past_feeling_keeps_unknown_and_source_boundaries(self):
        for memo in ('安心した。', '落ち着いた。', '友人は安心した。', '私も安心した。',
                '私は少し安心した。', '私は安心しなかった。', '私は安心したい。',
                '私は安心する。', '私は落ち着きませんでした。', '私はほっとした。',
                '私は安心したかもしれない。', '私は安心した？',
                '私は安心したと聞いた。', '夢を見た。私は安心した。',
                '友人によると。私は安心した。', '「私は安心した」。',
                '私は安心した、とは思わない。', '私は安心したが不安だった。'):
            with self.subTest(memo=memo):
                result = self.generate(request(record(memo=memo)))
                self.assertFalse(result.artifact and any(n.proposition.result_state == 'PAST_FEELING'
                                                        for n in result.artifact.graph.nodes))
        for req in (
                request(record(memo='私は安心した。私は記録を残した。')),
                request(record(memo='私は安心した。まだわからない。その後、私は記録を残した。')),
                request(record(memo='私は安心した。私は仕事を続けたい。その後、私は記録を残した。')),
                request(record(memo='私は安心した。', action='その後、私は記録を残した。')),
                request(record(memo='私は安心した。'), record(2, memo='その後、私は記録を残した。'))):
            with self.subTest(members=req.members):
                artifact = self.generate(req).artifact
                self.assertIsNotNone(artifact)
                self.assertFalse(any(e.edge_kind == 'OBSERVED_ORDER' for e in artifact.graph.edges))
                artifact.safe_projection(authenticated_owner_scope=OWNER)
        self.assertIsNone(self.generate(request(record(memo='', action='私は安心した。'))).artifact)

    def test_standalone_self_past_feeling_keeps_split_dependent_host_pending(self):
        for feeling in ('安心した', '安心しました', '落ち着いた', '嬉しかった', 'うれしかった'):
            for boundary in ('\n', '\r\n', '；', '。', '！'):
                for suffix in ('わけではない。', 'と思う。', 'とは言えない。', 'とは思わない。',
                               'という話だった。', 'のではない。', 'かどうかわからない。'):
                    with self.subTest(feeling=feeling, boundary=boundary, suffix=suffix):
                        result = self.generate(request(record(memo='私は' + feeling + boundary
                            + suffix + 'その後、私は記録を残した。')))
                        self.assertIsNotNone(result.artifact)
                        self.assertFalse(any(n.proposition.result_state == 'PAST_FEELING'
                                             for n in result.artifact.graph.nodes))
                        self.assertFalse(result.artifact.graph.edges)
                        self.assertTrue(result.artifact.graph.unknown_gaps)
                        result.artifact.safe_projection(authenticated_owner_scope=OWNER)

    def test_standalone_self_past_feeling_keeps_updates_comparison_and_safe_replay(self):
        old, new = '私は安心した', '僕は、落ち着いた'
        original = record(memo=old + '。その後、私は記録を残した。')
        for answer, lemma in ((new + '。', '落ち着く'),
                ('「' + old + '」ではなく「' + new + '」です。', '落ち着く'),
                ('「' + old + '」は取り消します。', None)):
            with self.subTest(answer=answer):
                req = request(self.with_answer(original, answer))
                artifact = self.generate(req).artifact
                self.assertIsNotNone(artifact)
                if lemma:
                    node = next(n for n in artifact.graph.nodes if n.proposition.predicate_lemma == lemma)
                    sources = {s.envelope.envelope_id: s.envelope for s in freeze_analysis_sources(req).sources}
                    for e in node.evidence_refs:
                        source = sources[e.source_envelope_id]
                        self.assertEqual(source.source_role, 'SUPPLEMENTAL_ANSWER')
                        self.assertEqual(source.raw_utf8[e.utf8_start:e.utf8_end].decode(), new)
                if answer.startswith('「'):
                    self.assertFalse(artifact.graph.edges)
                    self.assertNotIn('安心する', [n.proposition.predicate_lemma for n in artifact.graph.nodes])
                artifact.safe_projection(authenticated_owner_scope=OWNER)
        for current, previous in (('僕は、安心しました。', old + '。'),
                                  ('私はうれしかった。', '私は嬉しかった。')):
            self.assertEqual(self.compared(current, previous).artifact.period_comparison.change_claims, ())
        self.assertIn('ROUTE_EVIDENCE_CHANGED', self.compared(new + '。', old + '。').artifact
            .safe_projection(authenticated_owner_scope=OWNER)['period_comparison']['safe_change_kinds'])
        repeated = self.generate(request(record(memo=old + '。'), record(2, memo='僕は安心しました。'))).artifact
        node, = repeated.graph.nodes
        self.assertEqual(len(node.evidence_refs), 2)
        for changes in ({'modality': 'fact'}, {'actor': 'UNSPECIFIED'}, {'temporal_scope': 'current_input'},
                        {'predicate_lemma': '落ち着く'}, {'source_parts': node.proposition.source_parts[1:]}):
            with self.subTest(changes=changes), self.assertRaises(AnalysisSourceError):
                replace(repeated, graph=replace(repeated.graph, nodes=(replace(node,
                    proposition=replace(node.proposition, **changes)),))).safe_projection(authenticated_owner_scope=OWNER)

    def test_standalone_self_past_feeling_requires_complete_shared_witness(self):
        from cocolon_meaning_experience_engine.cores.analysis import intent_compiler as compiler
        builder = compiler.build_final_stage1_grounded_observation_plan
        mutations = (
            lambda n: replace(n, kind='action'),
            lambda n: replace(n, grounding_kind='inferred'),
            lambda n: replace(n, allowed_claim_scope='other'),
            lambda n: replace(n, retention='optional'),
            lambda n: replace(n, semantic_frame=replace(n.semantic_frame, actor='other_person')),
            lambda n: replace(n, semantic_frame=replace(n.semantic_frame, predicate_kind='event')),
            lambda n: replace(n, semantic_frame=replace(n.semantic_frame, polarity='negative')),
            lambda n: replace(n, semantic_frame=replace(n.semantic_frame, modality='wish')),
            lambda n: replace(n, semantic_frame=replace(n.semantic_frame, time_scope='future')),
            lambda n: replace(n, semantic_frame=replace(n.semantic_frame, attribute_codes=tuple(
                c for c in n.semantic_frame.attribute_codes if c != 'operator:positive_change'))),
            lambda n: replace(n, semantic_frame=replace(n.semantic_frame, attribute_codes=(
                *n.semantic_frame.attribute_codes, 'thread_time:unknown'))),
        )
        for memo in ('私は安心した。', '私は嬉しかった。'):
            for index, mutate in enumerate(mutations):
                def changed(*args, **kwargs):
                    plan = builder(*args, **kwargs)
                    return replace(plan, nuclei=tuple(mutate(n) for n in plan.nuclei))
                with self.subTest(memo=memo, mutation=index), patch.object(
                        compiler, 'build_final_stage1_grounded_observation_plan', side_effect=changed):
                    self.assertIsNone(self.generate(request(record(memo=memo))).artifact)
        late = self.generate(request(record(memo='私は会議を担当した。私は資料を調べた。'
            '私は記録を残した。私は嬉しかった。'))).artifact
        self.assertEqual(late.graph.nodes[-1].proposition.result_state, 'PAST_FEELING')
        self.assertFalse(late.graph.edges)

    def test_explicit_self_spellings_preserves_explicit_self_claims_and_original_evidence(self):
        clauses = (
            'ぼくは、資料を調べました。', 'ぼくは昨日資料を調べなかったです。',
            'ぼくは仕事を続けたい。', 'ぼくは仕事を続けたくありませんでした。',
            'ぼくは、職場にいた。', 'ぼくは昨日、職場にいなかったです。',
            'ぼくは会議を担当した。', 'ぼくは会議を担当しなかったです。',
            'ぼくは、家族を守りたいです。',
            'ぼくは、資料を調べないかもしれないと思う。',
            'ぼくは資料を調べた後、ぼくは嬉しかった。',
            'ぼくは資料を調べてから、ぼくは、安心しました。',
            'ぼくは仕事を続けたいけれど、ぼくはつらいです。',
            'ぼくは家族の生活を守りたい。',
            'ぼくは家族の新しい生活を守りたいけれど、ぼくはつらいです。',
            'ぼくは、家族の新しい生活を守りたいけれど、ぼくは、つらいです。',
        )
        for subject, memo in ((subject, clause.replace('ぼく', subject))
                              for subject in ('ぼく', '俺', 'おれ') for clause in clauses):
            with self.subTest(memo=memo):
                req = request(record(memo=memo))
                result = self.generate(req)
                self.assertEqual(result.status, EngineStatus.GENERATED)
                artifact = result.artifact
                baseline = self.generate(request(record(memo=memo.replace(subject, '僕')))).artifact
                self.assertEqual(artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'],
                    baseline.safe_text_projection(authenticated_owner_scope=OWNER)['text'])
                source = freeze_analysis_sources(req).sources[0].envelope
                for node in artifact.graph.nodes:
                    self.assertEqual(node.proposition.actor, 'SELF')
                    if node.proposition.possible_content:
                        self.assertEqual(node.proposition.possible_content.actor, 'UNSPECIFIED')
                    for e in node.evidence_refs:
                        raw = source.raw_utf8[e.utf8_start:e.utf8_end]
                        field = source.raw_utf8[e.field_utf8_start:e.field_utf8_end].decode()
                        self.assertIn(subject + 'は', raw.decode())
                        self.assertEqual(field[e.scalar_start:e.scalar_end], raw.decode())
                        self.assertEqual(hashlib.sha256(raw).hexdigest(), e.literal_sha256)
                compared = self.compared(memo, memo.replace(subject, '僕')).artifact
                self.assertEqual(compared.period_comparison.change_claims, ())
        for action in (subject + clause for subject in ('ぼく', '俺', 'おれ')
                       for clause in ('は資料を調べた。', 'は資料を調べなかった。', 'は仕事を続けたい。')):
            with self.subTest(action=action):
                artifact = self.generate(request(record(memo='', action=action))).artifact
                self.assertIsNotNone(artifact)
                self.assertEqual(artifact.graph.nodes[0].evidence_refs[0].field_path, 'memo_action')
                artifact.safe_projection(authenticated_owner_scope=OWNER)

    def test_explicit_self_spellings_keeps_supplement_updates_order_and_meaning_differences(self):
        for subject in ('ぼく', '俺', 'おれ'):
            old = subject + 'は資料を調べた'
            new = subject + 'は記録を残した'
            original = record(memo=old + '。私は仕事を続けたい。')
            for answer, expected in ((new + '。', ('調べる', '続ける', '残す')),
                    ('「' + old + '」ではなく「' + new + '」です。', ('続ける', '残す')),
                    ('「' + old + '」は取り消します。', ('続ける',))):
                with self.subTest(answer=answer):
                    artifact = self.generate(request(self.with_answer(original, answer))).artifact
                    self.assertIsNotNone(artifact)
                    self.assertEqual(tuple(n.proposition.predicate_lemma for n in artifact.graph.nodes), expected)
                    artifact.safe_projection(authenticated_owner_scope=OWNER)
            ordered = self.generate(request(record(memo=old + '。その後、' + new + '。'))).artifact
            first, second = ordered.graph.nodes
            self.assertEqual([(e.edge_kind, e.endpoint_refs) for e in ordered.graph.edges],
                             [('OBSERVED_ORDER', (first.node_ref, second.node_ref))])
            repeated = self.generate(request(record(memo=old + '。'), record(2, memo=old.replace(subject, '僕') + '。'))).artifact
            node, = repeated.graph.nodes
            self.assertEqual(len(node.evidence_refs), 2)
            for now in (subject + clause for clause in ('は資料を調べなかった。',
                    'は資料を調べたい。', 'は記録を残した。')):
                with self.subTest(now=now):
                    self.assertIn('ROUTE_EVIDENCE_CHANGED', self.compared(now, old + '。').artifact.safe_projection(
                        authenticated_owner_scope=OWNER)['period_comparison']['safe_change_kinds'])

    def test_explicit_self_spellings_does_not_infer_collective_other_or_unsupported_subjects(self):
        topics = tuple(subject + suffix for subject in ('ぼく', '俺', 'おれ')
                       for suffix in ('らは', 'たちは', '自身は', 'も', 'が'))
        for topic in topics + ('友人は', 'あなたは', ''):
            with self.subTest(topic=topic):
                self.assertIsNone(self.generate(request(record(memo=topic + '資料を調べた。'))).artifact)
        clauses = ('ぼくは資料を調べた？', 'ぼくは資料を調べたと聞いた。',
                     '夢を見た。ぼくは資料を調べた。',
                     'ぼくは資料を調べた後、友人は安心した。',
                     'ぼくは仕事を続けたいけれど、友人はつらい。',
                     'ぼくは資料を調べた後、不安が減りました。')
        for memo in (clause.replace('ぼく', subject) for subject in ('ぼく', '俺', 'おれ')
                     for clause in clauses):
            with self.subTest(memo=memo):
                self.assertIsNone(self.generate(request(record(memo=memo))).artifact)
        for subject in ('ぼく', '俺', 'おれ'):
            artifact = self.generate(request(record(memo=subject + 'は資料を調べた。'))).artifact
            node, = artifact.graph.nodes
            for changes in ({'actor': 'UNSPECIFIED'}, {'polarity': 'negative'},
                            {'source_parts': node.proposition.source_parts[1:]}):
                with self.subTest(changes=changes), self.assertRaises(AnalysisSourceError):
                    forged = replace(node, proposition=replace(node.proposition, **changes))
                    replace(artifact, graph=replace(artifact.graph, nodes=(forged,))).safe_projection(
                        authenticated_owner_scope=OWNER)

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

    def test_protective_burden_contrast_keeps_both_annotations_and_exact_source(self):
        cases = (
            ('私', '', '家族', '守りたい', 'けれど', 'つらい'),
            ('僕', '、 ', '生活', '守りたいです', 'けれども', '苦しいです'),
            ('ぼく', '、\u3000', '生活', '守りたい', 'けど', '辛いです'),
            ('わたし', '、', '気持ち', '守りたいです', 'が', 'つらいです'),
            ('自分', '', '新しい生活', '守りたい', 'けれど', '辛い'),
            ('私', '', '家族の時間', '守りたい', 'けれど', 'つらい'),
            ('ぼく', '、\u3000', '生活の基盤', '守りたいです', 'けど', '辛いです'),
            ('自分', '', '自分の家族の時間', '守りたい', 'けれども', '苦しい'),
            ('私', '', '家族の気持ち', '守りたい', 'けれど', 'つらい'),
            ('自分', '', '自分の家族の気持ち', '守りたいです', 'けど', '辛いです'),
            ('ぼく', '、　', '学びノートの振り返り', '守りたいです', 'けれども', '苦しいです'),
            ('私', '', '家族の考え', '守りたい', 'けれど', 'つらい'),
            ('私', '', '家族の思い', '守りたい', 'けれど', 'つらい'),
            ('私', '', '家族の学び', '守りたい', 'けれど', 'つらい'),
            ('私', '', '家族の取り組み', '守りたい', 'けれど', 'つらい'),
            ('私', '', '新しい家族の生活', '守りたい', 'けれど', 'つらい'),
            ('ぼく', '、　', '新しい学びノートの長い振り返り', '守りたいです', 'けれども', '苦しいです'),
        ) + tuple(('私', '', '家族の' + adjective + '取り組み', '守りたい', 'けれど', 'つらい')
            for adjective in ('新しい', '古い', '大きい', '小さい', '長い', '短い', '詳しい',
                              '難しい', '易しい', '良い'))
        for subject, comma, noun, ending, connector, feeling in cases:
            with self.subTest(subject=subject, noun=noun):
                left = subject + 'は' + comma + noun + 'を' + ending
                right = subject + 'は' + comma + feeling
                memo = left + connector + '、' + right
                req = request(record(memo=memo + '。'))
                artifact = self.generate(req).artifact
                self.assertIsNotNone(artifact)
                node, = artifact.graph.nodes
                protective, burden = artifact.graph.annotations
                self.assertEqual((node.node_kind, node.modality, node.proposition.arguments),
                    ('ATTENTION_OR_THOUGHT', 'wish', (('を', noun),)))
                self.assertEqual((protective.kind, burden.kind), ('PROTECTIVE', 'BURDEN'))
                self.assertEqual((protective.target_ref, burden.target_ref), (node.node_ref,) * 2)
                self.assertEqual(protective.evidence_refs, node.evidence_refs)
                self.assertEqual(burden.evidence_refs[0], node.evidence_refs[0])
                self.assertFalse(artifact.graph.edges)
                self.assertFalse(artifact.graph.conflicts)
                self.assertNotIn('SOURCE_SCOPE', [g.missing_scope for g in artifact.graph.unknown_gaps])
                envelope = freeze_analysis_sources(req).sources[0].envelope
                for ref, expected in zip(burden.evidence_refs, (left, right, memo)):
                    raw = envelope.raw_utf8[ref.utf8_start:ref.utf8_end]
                    field = envelope.raw_utf8[ref.field_utf8_start:ref.field_utf8_end].decode()
                    self.assertEqual(raw.decode(), expected)
                    self.assertEqual(field[ref.scalar_start:ref.scalar_end], expected)
                    self.assertEqual(hashlib.sha256(raw).hexdigest(), ref.literal_sha256)
                visual = artifact.safe_projection(authenticated_owner_scope=OWNER)
                text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text']
                for badge in visual['annotation_badges']:
                    self.assertIn(badge['visible_label'], text)
                self.assertIn('実際に守れているかは確定していません', text)
                self.assertIn('原因や続いている期間は確定していません', text)

    def test_protective_burden_requires_complete_shared_pair(self):
        from cocolon_meaning_experience_engine.cores.analysis import intent_compiler as compiler
        build = compiler.build_final_stage1_grounded_observation_plan
        memo = '私は家族を守りたいけれど、私はつらい。私は記録を残した。'
        for mismatch in ('relation', 'reverse', 'relation_scope', 'wish_operator',
                'wish_grounding', 'wish_scope', 'wish_time', 'wish_retention',
                'wish_unknown_fragment', 'wish_range', 'feeling_witness', 'feeling_actor'):
            def changed(*args, **kwargs):
                plan = build(*args, **kwargs)
                if mismatch == 'relation': return replace(plan, relations=())
                if mismatch in ('reverse', 'relation_scope'):
                    relations = tuple((replace(r, from_nucleus_id=r.to_nucleus_id,
                        to_nucleus_id=r.from_nucleus_id) if mismatch == 'reverse'
                        else replace(r, grounding_kind='inferred')) if r.type == 'contrast' else r
                        for r in plan.relations)
                    return replace(plan, relations=relations)
                index = 1 if mismatch.startswith('feeling_') else 0
                nuclei = list(plan.nuclei)
                n = nuclei[index]
                if mismatch == 'wish_grounding': n = replace(n, grounding_kind='inferred')
                elif mismatch == 'wish_scope': n = replace(n, allowed_claim_scope='unsupported')
                elif mismatch == 'wish_retention': n = replace(n, retention='optional')
                else:
                    f, codes = n.semantic_frame, n.semantic_frame.attribute_codes
                    if mismatch == 'wish_time': f = replace(f, time_scope='past')
                    elif mismatch == 'feeling_actor': f = replace(f, actor='other')
                    else:
                        if mismatch == 'wish_operator': codes = tuple(c for c in codes if c != 'operator:wish')
                        elif mismatch == 'feeling_witness': codes = tuple(c for c in codes if c != 'lexical:source_finite_contrast_feeling')
                        elif mismatch == 'wish_unknown_fragment': codes += ('source_fragment_unproved:yes',)
                        elif mismatch == 'wish_range': codes = tuple(
                            'source_fragment_scalar_range:1:9' if c.startswith('source_fragment_scalar_range:') else c
                            for c in codes)
                        f = replace(f, attribute_codes=codes)
                    n = replace(n, semantic_frame=f)
                nuclei[index] = n
                return replace(plan, nuclei=tuple(nuclei))
            with self.subTest(mismatch=mismatch), patch.object(compiler,
                    'build_final_stage1_grounded_observation_plan', side_effect=changed):
                artifact = self.generate(request(record(memo=memo))).artifact
                self.assertIsNotNone(artifact)
                self.assertFalse(artifact.graph.annotations)
                self.assertEqual(len(artifact.graph.nodes), 1)
                self.assertIn('SOURCE_SCOPE', [g.missing_scope for g in artifact.graph.unknown_gaps])

    def test_protective_burden_keeps_unsupported_hosts_and_partial_updates_unresolved(self):
        old = '私は家族を守りたいけれど、私はつらい'
        cases = [old.replace('私はつらい', right) for right in (
            '友人はつらい', 'つらい', '私はつらかった', '私はつらくない',
            '私はつらいかもしれない', '私はとてもつらい', '私はつらいと思う')]
        cases += [old.replace('守りたい', wish) for wish in ('守った', '守りたかった', '守りたくない')]
        # Lexical kana nouns have a complete shared proof; free kana does not.
        cases += [old.replace('家族を', noun + 'を') for noun in
                  ('家族のつらさ', '家族の読んでメモ', '家族の気持ちなら')]
        cases += [old.replace('けれど', 'なら'), old + '？',
            '「' + old + '」と友人が言った', '夢を見た。' + old,
            '友人から聞いた話です。' + old, old + '、という夢を見たのですが、' + '詳細を考えた' * 15]
        for memo in cases:
            with self.subTest(memo=memo):
                artifact = self.generate(request(record(memo=memo + '。'))).artifact
                self.assertFalse(artifact and artifact.graph.annotations)
        artifact = self.generate(request(record(memo='私は記録を残した。', action=old + '。'))).artifact
        self.assertFalse(artifact.graph.annotations)
        original = record(memo='私は記録を残した。' + old + '。')
        for quoted in ('私は家族を守りたい', old.replace('つらい', '辛い')):
            with self.subTest(quoted=quoted):
                result = self.generate(request(self.with_answer(original, '「' + quoted + '」は取り消します。')))
                self.assertEqual(result.status, EngineStatus.UNAVAILABLE)

    def test_protective_burden_preserves_updates_aggregation_comparison_and_safe_projection(self):
        old = '私は家族を守りたいけれど、私はつらい'
        equivalent = 'ぼくは、家族を守りたいですけど、ぼくは、辛いです'
        new = '私は生活を守りたいけれど、私は苦しいです'
        artifact = self.generate(request(record(memo=old + '。'), record(2, memo=equivalent + '。'))).artifact
        self.assertIsNotNone(artifact)
        self.assertEqual(len(artifact.graph.nodes), 1)
        self.assertEqual([len(a.evidence_refs) for a in artifact.graph.annotations], [2, 6])
        for before, now in ((old, equivalent), (equivalent, old)):
            with self.subTest(now=now):
                compared = self.compared(now + '。', before + '。').artifact
                self.assertEqual(compared.period_comparison.change_claims, ())
                compared.safe_projection(authenticated_owner_scope=OWNER)
        for now in (new, old.replace('つらい', '苦しい')):
            compared = self.compared(now + '。', old + '。').artifact
            self.assertIn('ANNOTATION_EVIDENCE_CHANGED', compared.safe_projection(
                authenticated_owner_scope=OWNER)['period_comparison']['safe_change_kinds'])
        original = record(memo='私は記録を残した。' + old + '。')
        for answer, count in ((new + '。', 4),
                ('「' + old + '」ではなく「' + new + '」です。', 2),
                ('「' + old + '」は取り消します。', 0)):
            with self.subTest(answer=answer):
                value = request(self.with_answer(original, answer))
                result = self.generate(value).artifact
                self.assertIsNotNone(result)
                self.assertEqual(len(result.graph.annotations), count)
                result.safe_projection(authenticated_owner_scope=OWNER)
                if count == 2:
                    for claim in result.graph.annotations:
                        self.assertEqual(claim.update_refs, (result.graph.source_updates[0].update_ref,))
                    self.assertEqual(result.graph.nodes[1].proposition.arguments, (('を', '生活'),))
        for index in (0, 1):
            for changes in ({'target_ref': 'absent'}, {'evidence_refs': ()},
                    {'predicate_lemma': '続ける'}, {'source_labels': ('友人は家族を守りたい',)}):
                with self.subTest(index=index, changes=changes), self.assertRaises(AnalysisSourceError):
                    claims = list(artifact.graph.annotations)
                    claims[index] = replace(claims[index], **changes)
                    replace(artifact, graph=replace(artifact.graph, annotations=tuple(claims))).safe_projection(
                        authenticated_owner_scope=OWNER)

    def test_genitive_wish_contrast_keeps_updates_aggregation_and_comparison(self):
        old = '私は家族の時間を守りたいけれど、私はつらい'
        equivalent = 'ぼくは、家族の時間を守りたいですけど、ぼくは、辛いです'
        new = '私は生活の基盤を守りたいけれど、私は苦しい'
        artifact = self.generate(request(record(memo=old + '。'),
            record(2, memo=equivalent + '。'))).artifact
        self.assertIsNotNone(artifact)
        self.assertEqual(len(artifact.graph.nodes), 1)
        self.assertEqual([len(a.evidence_refs) for a in artifact.graph.annotations], [2, 6])
        self.assertEqual(self.compared(old + '。', equivalent + '。').artifact.period_comparison.change_claims, ())
        for now in (new, old.replace('つらい', '苦しい')):
            with self.subTest(now=now):
                compared = self.compared(now + '。', old + '。').artifact
                self.assertIn('ANNOTATION_EVIDENCE_CHANGED', compared.safe_projection(
                    authenticated_owner_scope=OWNER)['period_comparison']['safe_change_kinds'])
        original = record(memo='私は記録を残した。' + old + '。')
        for answer, count in ((new + '。', 4),
                ('「' + old + '」ではなく「' + new + '」です。', 2),
                ('「' + old + '」は取り消します。', 0)):
            with self.subTest(answer=answer):
                result = self.generate(request(self.with_answer(original, answer))).artifact
                self.assertIsNotNone(result)
                self.assertEqual(len(result.graph.annotations), count)
                result.safe_projection(authenticated_owner_scope=OWNER)
                if count == 2:
                    self.assertEqual(result.graph.nodes[1].proposition.arguments, (('を', '生活の基盤'),))
                    for claim in result.graph.annotations:
                        self.assertEqual(claim.update_refs, (result.graph.source_updates[0].update_ref,))
        partial = '「私は家族の時間を守りたい」は取り消します。'
        self.assertEqual(self.generate(request(self.with_answer(original, partial))).status,
                         EngineStatus.UNAVAILABLE)
        ordinary = self.generate(request(record(memo='私は資料の内容を調べたいけれど、私はつらい。'))).artifact
        self.assertEqual(ordinary.graph.nodes[0].proposition.arguments, (('を', '資料の内容'),))
        self.assertEqual([a.kind for a in ordinary.graph.annotations], ['BURDEN'])

    def test_genitive_wish_contrast_keeps_unproved_owners_and_hosts_unresolved(self):
        old = '私は家族の時間を守りたいけれど、私はつらい'
        cases = [old.replace('私は家族', prefix + '家族') for prefix in ('友人は', '', '私は友人は')]
        cases += [old.replace('守りたい', v) for v in ('守りたくない', '守りたかった',
            '守りたいと思う', '守りたい気持ちがある')]
        cases += [old.replace('私はつらい', v) for v in ('友人はつらい', 'つらい',
            '私はつらかった', '私はつらくない', '私はとてもつらい', '私はつらいかもしれない')]
        cases += ['「' + old + '」と友人が言った', '夢を見た。' + old,
            '友人から聞いた話です。' + old, old + '？']
        for memo in cases:
            with self.subTest(memo=memo):
                artifact = self.generate(request(record(memo=memo + '。'),
                    record(2, memo='私は記録を残した。'))).artifact
                self.assertIsNotNone(artifact)
                self.assertFalse(artifact.graph.annotations)
                self.assertEqual(len(artifact.graph.nodes), 1)
                self.assertEqual(artifact.graph.nodes[0].proposition.predicate_lemma, '残す')
                self.assertIn('SOURCE_SCOPE', [g.missing_scope for g in artifact.graph.unknown_gaps])

    def test_kana_genitive_wish_keeps_updates_aggregation_and_comparison(self):
        old = '私は家族の気持ちを守りたいけれど、私はつらい'
        new = '私は家族の考えを守りたいけれど、私は苦しい'
        equivalent = 'ぼくは、家族の気持ちを守りたいですけど、ぼくは、辛いです'
        artifact = self.generate(request(record(memo=old + '。'),
            record(2, memo=equivalent + '。'))).artifact
        self.assertEqual(len(artifact.graph.nodes), 1)
        self.assertEqual([len(a.evidence_refs) for a in artifact.graph.annotations], [2, 6])
        self.assertEqual(self.compared(old + '。', equivalent + '。').artifact.period_comparison.change_claims, ())
        self.assertIn('ANNOTATION_EVIDENCE_CHANGED', self.compared(new + '。', old + '。').artifact.safe_projection(
            authenticated_owner_scope=OWNER)['period_comparison']['safe_change_kinds'])
        original = record(memo='私は記録を残した。' + old + '。')
        for answer, count in ((new + '。', 4),
                ('「' + old + '」ではなく「' + new + '」です。', 2),
                ('「' + old + '」は取り消します。', 0)):
            with self.subTest(answer=answer):
                updated = self.generate(request(self.with_answer(original, answer))).artifact
                self.assertIsNotNone(updated)
                self.assertEqual(len(updated.graph.annotations), count)
                updated.safe_projection(authenticated_owner_scope=OWNER)
                if count == 2:
                    self.assertEqual(updated.graph.nodes[1].proposition.arguments, (('を', '家族の考え'),))
                    for annotation in updated.graph.annotations:
                        self.assertEqual(annotation.update_refs, (updated.graph.source_updates[0].update_ref,))
        partial = '「私は家族の気持ちを守りたい」は取り消します。'
        self.assertEqual(self.generate(request(self.with_answer(original, partial))).status, EngineStatus.UNAVAILABLE)
        ordinary = self.generate(request(record(memo='私は資料の振り返りを調べたいけれど、私はつらい。'))).artifact
        self.assertEqual(ordinary.graph.nodes[0].proposition.arguments, (('を', '資料の振り返り'),))
        self.assertEqual([a.kind for a in ordinary.graph.annotations], ['BURDEN'])
        for memo in (old.replace('私は家族', '友人は家族'), old.replace('私は家族', '家族'),
                old.replace('守りたい', '守りたいと思う'), old.replace('私はつらい', '友人はつらい'),
                '夢を見た。' + old, '友人から聞いた話です。' + old, '「' + old + '」と友人が言った', old + '？'):
            with self.subTest(memo=memo):
                result = self.generate(request(record(memo=memo + '。'), record(2, memo='私は記録を残した。'))).artifact
                self.assertIsNotNone(result)
                self.assertFalse(result.graph.annotations)
                self.assertEqual(len(result.graph.nodes), 1)
                self.assertIn('SOURCE_SCOPE', [g.missing_scope for g in result.graph.unknown_gaps])

    def test_attributive_genitive_wish_keeps_target_updates_and_comparison(self):
        old = '私は家族の新しい生活を守りたいけれど、私はつらい'
        new = old.replace('新しい', '古い')
        equivalent = 'ぼくは、家族の新しい生活を守りたいですけど、ぼくは、辛いです'
        artifact = self.generate(request(record(memo=old + '。'),
            record(2, memo=equivalent + '。'))).artifact
        node, = artifact.graph.nodes
        self.assertEqual(node.proposition.arguments, (('を', '家族の新しい生活'),))
        self.assertEqual([len(a.evidence_refs) for a in artifact.graph.annotations], [2, 6])
        self.assertEqual(self.compared(old + '。', equivalent + '。').artifact.period_comparison.change_claims, ())
        self.assertIn('ANNOTATION_EVIDENCE_CHANGED', self.compared(new + '。', old + '。').artifact.safe_projection(
            authenticated_owner_scope=OWNER)['period_comparison']['safe_change_kinds'])
        for noun in ('家族の生活', '家族の古い生活', '新しい家族の生活'):
            with self.subTest(noun=noun), self.assertRaises(AnalysisSourceError):
                forged = replace(node, proposition=replace(node.proposition, arguments=(('を', noun),)))
                replace(artifact, graph=replace(artifact.graph, nodes=(forged,))).safe_projection(
                    authenticated_owner_scope=OWNER)
        original = record(memo='私は記録を残した。' + old + '。')
        for answer, count in ((new + '。', 4),
                ('「' + old + '」ではなく「' + new + '」です。', 2),
                ('「' + old + '」は取り消します。', 0)):
            with self.subTest(answer=answer):
                updated = self.generate(request(self.with_answer(original, answer))).artifact
                self.assertIsNotNone(updated)
                self.assertEqual(len(updated.graph.annotations), count)
                updated.safe_projection(authenticated_owner_scope=OWNER)
                if count == 2:
                    self.assertEqual(updated.graph.nodes[1].proposition.arguments, (('を', '家族の古い生活'),))
                    for annotation in updated.graph.annotations:
                        self.assertEqual(annotation.update_refs, (updated.graph.source_updates[0].update_ref,))
        partial = '「私は家族の新しい生活を守りたい」は取り消します。'
        self.assertEqual(self.generate(request(self.with_answer(original, partial))).status, EngineStatus.UNAVAILABLE)
        ordinary = self.generate(request(record(memo='私は資料の詳しい振り返りを調べたいけれど、私はつらい。'))).artifact
        self.assertEqual(ordinary.graph.nodes[0].proposition.arguments, (('を', '資料の詳しい振り返り'),))
        self.assertEqual([a.kind for a in ordinary.graph.annotations], ['BURDEN'])

    def test_bad_attributive_wish_keeps_target_updates_and_comparison(self):
        old = '私は家族の悪い取り組みを守りたいけれど、私はつらい'
        new = old.replace('悪い', '良い')
        equivalent = 'ぼくは、家族の悪い取り組みを守りたいですけど、ぼくは、辛いです'
        artifact = self.generate(request(record(memo=old + '。'),
            record(2, memo=equivalent + '。'))).artifact
        node, = artifact.graph.nodes
        self.assertEqual(node.proposition.arguments, (('を', '家族の悪い取り組み'),))
        self.assertEqual([len(a.evidence_refs) for a in artifact.graph.annotations], [2, 6])
        self.assertEqual(self.compared(old + '。', equivalent + '。').artifact.period_comparison.change_claims, ())
        self.assertIn('ANNOTATION_EVIDENCE_CHANGED', self.compared(new + '。', old + '。').artifact.safe_projection(
            authenticated_owner_scope=OWNER)['period_comparison']['safe_change_kinds'])
        source = freeze_analysis_sources(request(record(memo=old + '。'))).sources[0].envelope
        for ref in node.evidence_refs[:1]:
            raw = source.raw_utf8[ref.utf8_start:ref.utf8_end]
            field = source.raw_utf8[ref.field_utf8_start:ref.field_utf8_end].decode()
            self.assertEqual(field[ref.scalar_start:ref.scalar_end], raw.decode())
            self.assertEqual(hashlib.sha256(raw).hexdigest(), ref.literal_sha256)
            self.assertEqual(raw.decode(), '私は家族の悪い取り組みを守りたい')
        for noun in ('家族の取り組み', '家族の良い取り組み', '悪い家族の取り組み'):
            with self.subTest(noun=noun), self.assertRaises(AnalysisSourceError):
                forged = replace(node, proposition=replace(node.proposition, arguments=(('を', noun),)))
                replace(artifact, graph=replace(artifact.graph, nodes=(forged,))).safe_projection(
                    authenticated_owner_scope=OWNER)
        original = record(memo='私は記録を残した。' + old + '。')
        for answer, count in ((new + '。', 4),
                ('「' + old + '」ではなく「' + new + '」です。', 2),
                ('「' + old + '」は取り消します。', 0)):
            with self.subTest(answer=answer):
                updated = self.generate(request(self.with_answer(original, answer))).artifact
                self.assertIsNotNone(updated)
                self.assertEqual(len(updated.graph.annotations), count)
                updated.safe_projection(authenticated_owner_scope=OWNER)
                if count == 2:
                    self.assertEqual(updated.graph.nodes[1].proposition.arguments, (('を', '家族の良い取り組み'),))
                    for annotation in updated.graph.annotations:
                        self.assertEqual(annotation.update_refs, (updated.graph.source_updates[0].update_ref,))
        partial = '「私は家族の悪い取り組みを守りたい」は取り消します。'
        self.assertEqual(self.generate(request(self.with_answer(original, partial))).status, EngineStatus.UNAVAILABLE)
        ordinary = self.generate(request(record(memo='私は資料の悪い振り返りを調べたいけれど、私はつらい。'))).artifact
        self.assertEqual(ordinary.graph.nodes[0].proposition.arguments, (('を', '資料の悪い振り返り'),))
        self.assertEqual([a.kind for a in ordinary.graph.annotations], ['BURDEN'])

    def test_attributive_genitive_wish_keeps_unproved_forms_and_scope_unresolved(self):
        old = '私は家族の新しい生活を守りたいけれど、私はつらい'
        cases = [old.replace('新しい生活', noun) for noun in ('新しくない生活', '新しかった生活',
            '新しく生活', 'とても新しい生活', '新しい大きい生活', '楽しい生活', '新しい',
            '新しい来週生活', '新しい何', '大きい取り組み来週メモ',
            '悪いやり方')]
        cases += [old.replace('私は家族', '友人は家族'), old.replace('私は家族', '家族'),
            old.replace('生活を守りたい', '生活を友人は守りたい'), old.replace('守りたい', '守りたいと思う'),
            old.replace('守りたい', '守りたかった'), old.replace('守りたい', '守りたくない'),
            old.replace('私はつらい', '友人はつらい'), '夢を見た。' + old,
            '友人から聞いた話です。' + old, '「' + old + '」と友人が言った', old + '？']
        for memo in cases:
            with self.subTest(memo=memo):
                artifact = self.generate(request(record(memo=memo + '。'),
                    record(2, memo='私は記録を残した。'))).artifact
                self.assertIsNotNone(artifact)
                self.assertFalse(artifact.graph.annotations)
                node, = artifact.graph.nodes
                self.assertEqual(node.proposition.predicate_lemma, '残す')
                self.assertIn('SOURCE_SCOPE', [g.missing_scope for g in artifact.graph.unknown_gaps])

    def test_protective_topic_comma_keeps_wish_object_and_exact_source(self):
        for subject, separator, noun, ending in (
            ('私', '、', '家族', '守りたい'),
            ('僕', '， ', '生活', '守りたいです'),
            ('わたし', '、　', '家族の時間', '守りたい'),
            ('自分', '，', '新しい気持ちメモ', '守りたいです'),
        ):
            with self.subTest(subject=subject, noun=noun):
                clause = subject + 'は' + separator + noun + 'を' + ending
                req = request(record(memo='　' + clause + '。'))
                artifact = self.generate(req).artifact
                self.assertIsNotNone(artifact)
                node, = artifact.graph.nodes
                claim, = artifact.graph.annotations
                self.assertEqual((node.proposition.actor, node.proposition.arguments,
                    node.modality, node.temporal_scope),
                    ('SELF', (('を', noun),), 'wish', 'current_input'))
                self.assertEqual(node.proposition.source_parts[0],
                    ('SELF_TOPIC', 0, len(subject + 'は' + separator)))
                self.assertEqual([i for _, a, b in node.proposition.source_parts
                    for i in range(a, b)], list(range(len(clause))))
                self.assertEqual(claim.evidence_refs, node.evidence_refs)
                evidence, = claim.evidence_refs
                envelope = freeze_analysis_sources(req).sources[0].envelope
                raw = envelope.raw_utf8[evidence.utf8_start:evidence.utf8_end]
                field = envelope.raw_utf8[evidence.field_utf8_start:evidence.field_utf8_end].decode()
                self.assertEqual(raw.decode(), clause)
                self.assertEqual(field[evidence.scalar_start:evidence.scalar_end], clause)
                self.assertEqual(hashlib.sha256(raw).hexdigest(), evidence.literal_sha256)
                projection = artifact.safe_projection(authenticated_owner_scope=OWNER)
                self.assertEqual(projection['nodes'][0]['visible_label'], noun + 'を守ることへの希望')
                self.assertIn('実際に守れているかは確定していません',
                    artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'])
                self.assertEqual(artifact.graph.edges, ())

    def test_protective_topic_comma_keeps_updates_aggregation_and_period_meaning(self):
        old, new = '私は、家族を守りたい', '僕は， 生活を守りたいです'
        base = record(memo='私は記録を残した。' + old + '。')
        for answer, count in ((new + '。', 2), ('「' + old + '」ではなく「' + new + '」です。', 1)):
            with self.subTest(answer=answer):
                req = request(self.with_answer(base, answer))
                artifact = self.generate(req).artifact
                self.assertIsNotNone(artifact)
                self.assertEqual(len(artifact.graph.annotations), count)
                claim = next(a for a in artifact.graph.annotations if new in a.source_labels)
                evidence, = claim.evidence_refs
                envelopes = {s.envelope.envelope_id: s.envelope for s in freeze_analysis_sources(req).sources}
                envelope = envelopes[evidence.source_envelope_id]
                self.assertEqual(envelope.source_role, 'SUPPLEMENTAL_ANSWER')
                self.assertEqual(envelope.raw_utf8[evidence.utf8_start:evidence.utf8_end].decode(), new)
                artifact.safe_projection(authenticated_owner_scope=OWNER)
        withdrawn = self.generate(request(self.with_answer(base, '「' + old + '」は取り消します。'))).artifact
        self.assertEqual(withdrawn.graph.annotations, ())
        aggregated = self.generate(request(record(memo=old + '。'),
            record(2, memo='私は家族を守りたい。'))).artifact
        self.assertEqual(len(aggregated.graph.nodes), 1)
        self.assertEqual(len(aggregated.graph.annotations[0].evidence_refs), 2)
        self.assertEqual(self.compared(old + '。', '私は家族を守りたい。')
            .artifact.period_comparison.change_claims, ())
        different = self.compared(new + '。', old + '。').artifact
        self.assertIn('ANNOTATION_EVIDENCE_CHANGED', different.safe_projection(
            authenticated_owner_scope=OWNER)['period_comparison']['safe_change_kinds'])

    def test_protective_topic_comma_does_not_erase_unread_scope_or_forge_meaning(self):
        for clause in (
            '私は、、家族を守りたい', '私は、\t家族を守りたい',
            '私は、\n家族を守りたい', '私は、友人は家族を守りたい',
            '友人は、家族を守りたい', '私は、家族を守りたくない',
            '私は、家族を守りたかった', '私は、家族を守った',
            '私は、家族を守りたいかもしれない', '私は、家族を守りたいと聞いた',
            '私は、家族を守りたい？', '「私は、家族を守りたい」と友人が言った',
            '私は、何を守りたい', '私は、来週家族を守りたい',
            '私は、今日家族を守りたい', '私は、絶対に家族を守りたい',
        ):
            with self.subTest(clause=clause):
                artifact = self.generate(request(record(memo=clause + '。'))).artifact
                self.assertFalse(artifact and artifact.graph.annotations)
        artifact = self.generate(request(record(memo='私は、家族を守りたい。'))).artifact
        self.assertIsNotNone(artifact)
        node, = artifact.graph.nodes
        for changes in ({'arguments': (('を', '生活'),)}, {'actor': 'UNSPECIFIED'},
                {'modality': 'fact'}, {'temporal_scope': 'past'}, {'polarity': 'negative'},
                {'source_parts': node.proposition.source_parts[1:]}):
            with self.subTest(changes=changes), self.assertRaises(AnalysisSourceError):
                altered = replace(node, proposition=replace(node.proposition, **changes))
                replace(artifact, graph=replace(artifact.graph, nodes=(altered,)))\
                    .safe_projection(authenticated_owner_scope=OWNER)

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
        # Neither a reason nor endpoint order may disappear through display.
        gaps = (UnknownGap('g1', ('n1', 'n2'), 'ROUTE_CONNECTION', 'ONLY_EXPLICIT_ORDER_IS_SHOWN'),
            UnknownGap('g2', ('n1', 'n2'), 'ROUTE_CONNECTION', 'EXPLICIT_PREDECESSOR_NOT_ESTABLISHED'),
            UnknownGap('g3', ('n2', 'n1'), 'ROUTE_CONNECTION', 'ONLY_EXPLICIT_ORDER_IS_SHOWN'))
        artifact = replace(artifact, graph=replace(artifact.graph, unknown_gaps=gaps))
        visual = artifact.safe_projection(authenticated_owner_scope=OWNER)
        self.assertEqual([g['gap_ref'] for g in visual['unknown_gaps']], ['g1', 'g2', 'g3'])
        self.assertEqual([g['between_node_refs'] for g in visual['unknown_gaps']],
                         [['n1', 'n2'], ['n1', 'n2'], ['n2', 'n1']])
        self.assertEqual([g['visible_label'] for g in visual['unknown_gaps']], [
            '段階同士のつながりは、この記録からは確定していません。',
            'この記述がどの内容に続くのかは、この記録からは確定していません。',
            '段階同士のつながりは、この記録からは確定していません。'])
        self.assertEqual(artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'].count('未確定（'), 3)

    def test_missing_predecessor_explains_its_own_unknown_without_erasing_pair_or_source(self):
        original = record(memo='私は記録を担当した。その後、私は資料を調べた。')
        cases = (
            (request(record(memo='その後、私は資料を調べた。')), 0, False),
            (request(record(memo='それから、私は資料を調べなかった。')), 0, False),
            (request(record(memo='私は記録を担当した。まだわからない。その後、私は資料を調べた。')), 1, True),
            (request(self.with_answer(original, '「私は記録を担当した」は取り消します。')), 0, False),
            (request(self.with_answer(original, '「私は記録を担当した」ではなく「私はメモを担当しなかった」です。')), 1, False),
            (request(self.with_answer(record(memo='私は記録を担当した。'), 'それから、私は資料を調べた。')), 1, False),
        )
        label = 'この記述がどの内容に続くのかは、この記録からは確定していません。'
        for req, pair_count, unread in cases:
            with self.subTest(req=req):
                artifact = self.generate(req).artifact
                before = artifact.graph
                visual = artifact.safe_projection(authenticated_owner_scope=OWNER)
                gaps = visual['unknown_gaps']
                specific, = [g for g in gaps if g['visible_label'] == label]
                target, = specific['between_node_refs']
                node = next(n for n in before.nodes if n.node_ref == target)
                self.assertIn(node.proposition.sequence_marker, ('AFTER_PREVIOUS', 'THEN_OR_ADDITION'))
                self.assertEqual(sum(g['visible_label'].startswith('段階同士のつながりは') for g in gaps), pair_count)
                self.assertEqual(any('まだ読み取れていない内容' in g['visible_label'] for g in gaps), unread)
                self.assertFalse(visual['edges'])
                self.assertEqual(gaps, artifact.private_visual_preview(authenticated_owner_scope=OWNER)['unknown_gaps'])
                text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text']
                self.assertEqual(text.count(label), 1)
                self.assertIs(artifact.graph, before)
                self.assertEqual(next(g for g in before.unknown_gaps if g.gap_ref == specific['gap_ref']).reason_code,
                                 'EXPLICIT_PREDECESSOR_NOT_ESTABLISHED')
        resolved = self.generate(request(original)).artifact
        self.assertEqual(len(resolved.graph.edges), 1)
        self.assertNotIn(label, resolved.safe_text_projection(authenticated_owner_scope=OWNER)['text'])
        same = self.compared('その後、私は資料を調べた。', 'その後、僕は資料を調べました。').artifact
        self.assertEqual(same.period_comparison.change_claims, ())

    def test_explicit_wish_burden_is_a_targeted_annotation_with_whole_evidence(self):
        for subject in ('私', '僕', 'ぼく', 'わたし', '自分'):
            for feeling in ('つらい', 'つらいです', '辛い', '辛いです', '苦しい', '苦しいです'):
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
                    predicate = feeling.removesuffix('です').replace('辛い', 'つらい')
                    self.assertEqual(claim.predicate_lemma, predicate)
                    self.assertEqual(claim.source_labels, (subject + 'は' + feeling,))
                    self.assertIn(predicate + 'と記述されています', badge['visible_label'])
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
                for feeling in ('つらい', '辛い', '、つらい', '、 辛いです'):
                    artifact = self.generate(request(record(memo='私は仕事を続けたいけれど、私は' + feeling + '。'))).artifact
                    self.assertEqual(artifact.graph.annotations, ())
                    self.assertIn('SOURCE_SCOPE', [g.missing_scope for g in artifact.graph.unknown_gaps])

    def test_burden_spelling_keeps_target_meaning_and_exact_source_updates(self):
        kanji = '私は仕事を続けたいけれど、私は辛い'
        kana = kanji.replace('辛い', 'つらい')
        artifact = self.generate(request(record(memo=kanji + '。'),
            record(2, memo=kana + 'です。'))).artifact
        claim, = artifact.graph.annotations
        self.assertEqual(claim.predicate_lemma, 'つらい')
        self.assertEqual(set(claim.source_labels), {'私は辛い', '私はつらいです'})
        self.assertEqual(len(claim.evidence_refs), 6)
        self.assertEqual(len(artifact.graph.nodes), 1)
        self.assertEqual(len(artifact.graph.nodes[0].record_refs), 2)
        self.assertFalse(artifact.graph.edges)
        artifact.safe_projection(authenticated_owner_scope=OWNER)
        for before, now in ((kanji, kana), (kana, kanji)):
            with self.subTest(now=now):
                compared = self.compared(now + '。', before + '。').artifact
                self.assertEqual(compared.period_comparison.change_claims, ())
                compared.safe_projection(authenticated_owner_scope=OWNER)
        for now in (kanji.replace('辛い', '苦しい'), kanji.replace('仕事を続けたい', '資料を調べたい')):
            with self.subTest(now=now):
                compared = self.compared(now + '。', kanji + '。').artifact
                self.assertIn('ANNOTATION_EVIDENCE_CHANGED', compared.safe_projection(
                    authenticated_owner_scope=OWNER)['period_comparison']['safe_change_kinds'])
        new = '私は資料を調べたいけど、私は辛いです'
        original = record(memo='私は記録を残した。' + kanji + '。')
        for answer, count in ((new + '。', 2),
                ('「' + kanji + '」ではなく「' + new + '」です。', 1),
                ('「' + kanji + '」は取り消します。', 0)):
            with self.subTest(answer=answer):
                artifact = self.generate(request(self.with_answer(original, answer))).artifact
                self.assertIsNotNone(artifact)
                self.assertEqual(len(artifact.graph.annotations), count)
                if count:
                    claim = next(a for a in artifact.graph.annotations if '私は辛いです' in a.source_labels)
                    target = next(n for n in artifact.graph.nodes if n.node_ref == claim.target_ref)
                    self.assertEqual(target.proposition.predicate_lemma, '調べる')
                    self.assertEqual(len(claim.update_refs), 1 if count == 1 else 0)
                artifact.safe_projection(authenticated_owner_scope=OWNER)
        # Only the proved predicate meaning is normalized, never the original
        # text used to identify a correction or withdrawal target.
        self.assertIsNone(self.generate(request(self.with_answer(original,
            '「' + kana + '」は取り消します。'))).artifact)

    def test_burden_topic_comma_preserves_full_original_and_annotation(self):
        for subject in ('私', '僕', 'ぼく', 'わたし', '自分'):
            for separator in ('、', '、 ', '、\u3000'):
                for feeling in ('つらい', '辛いです', '苦しいです'):
                    with self.subTest(subject=subject, separator=separator, feeling=feeling):
                        right = subject + 'は' + separator + feeling
                        memo = '私は仕事を続けたいけれど、' + right + '。'
                        req = request(record(memo=memo))
                        artifact = self.generate(req).artifact
                        self.assertIsNotNone(artifact)
                        claim, = artifact.graph.annotations
                        self.assertEqual(claim.source_labels, (right.replace('\u3000', ' '),))
                        self.assertEqual(claim.target_ref, artifact.graph.nodes[0].node_ref)
                        self.assertEqual(len(artifact.graph.nodes), 1)
                        self.assertFalse(artifact.graph.edges)
                        self.assertEqual(len(claim.evidence_refs), 3)
                        envelope = freeze_analysis_sources(req).sources[0].envelope
                        for e in claim.evidence_refs:
                            literal = envelope.raw_utf8[e.utf8_start:e.utf8_end]
                            field = envelope.raw_utf8[e.field_utf8_start:e.field_utf8_end].decode()
                            self.assertEqual(literal.decode(), field[e.scalar_start:e.scalar_end])
                            self.assertEqual(hashlib.sha256(literal).hexdigest(), e.literal_sha256)
                        right_ref = claim.evidence_refs[1]
                        self.assertEqual(envelope.raw_utf8[right_ref.utf8_start:right_ref.utf8_end].decode(), right)
                        # Compare by replacing only the topic separator; the
                        # connective comma and original evidence are distinct.
                        baseline = self.generate(request(record(memo=memo.replace(right, subject + 'は' + feeling))))
                        self.assertEqual(artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'],
                            baseline.artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'])
                        self.assertNotIn('SOURCE_SCOPE', [g.missing_scope for g in artifact.graph.unknown_gaps])

    def test_burden_topic_comma_keeps_exact_updates_comparison_and_safe_replay(self):
        old = '私は仕事を続けたいけれど、私は、辛い'
        plain = old.replace('私は、', '私は')
        new = '私は資料を調べたいけれど、私は、\u3000苦しいです'
        for before, now in ((old, plain), (plain, old)):
            with self.subTest(before=before):
                artifact = self.compared(now + '。', before + '。').artifact
                self.assertEqual(artifact.period_comparison.change_claims, ())
                artifact.safe_projection(authenticated_owner_scope=OWNER)
        changed = self.compared(new + '。', old + '。').artifact
        self.assertIn('ANNOTATION_EVIDENCE_CHANGED', changed.safe_projection(
            authenticated_owner_scope=OWNER)['period_comparison']['safe_change_kinds'])
        combined = self.generate(request(record(memo=old + '。'), record(2, memo=plain + '。'))).artifact
        claim, = combined.graph.annotations
        self.assertEqual(len(claim.evidence_refs), 6)
        self.assertEqual(set(claim.source_labels), {'私は、辛い', '私は辛い'})
        original = record(memo='私は記録を残した。' + old + '。')
        for answer, burdens in ((new + '。', 2),
                ('「' + old + '」ではなく「' + new + '」です。', 1),
                ('「' + old + '」は取り消します。', 0)):
            with self.subTest(answer=answer):
                artifact = self.generate(request(self.with_answer(original, answer))).artifact
                self.assertIsNotNone(artifact)
                self.assertEqual(len([a for a in artifact.graph.annotations if a.kind == 'BURDEN']), burdens)
                artifact.safe_projection(authenticated_owner_scope=OWNER)
        self.assertIsNone(self.generate(request(self.with_answer(original,
            '「' + plain + '」は取り消します。'))).artifact)
        artifact = self.generate(request(record(memo=old + '。'))).artifact
        claim, = artifact.graph.annotations
        for changes in ({'predicate_lemma': '苦しい'}, {'source_labels': ('友人は、辛い',)},
                        {'evidence_refs': claim.evidence_refs[:2]}):
            with self.subTest(changes=changes), self.assertRaises(AnalysisSourceError):
                forged = replace(artifact, graph=replace(artifact.graph,
                    annotations=(replace(claim, **changes),)))
                forged.safe_projection(authenticated_owner_scope=OWNER)

    def test_burden_topic_comma_does_not_promote_unproved_or_nonpresent_feelings(self):
        prefix = '私は仕事を続けたいけれど、'
        for right in ('私は、、つらい', '私は、\tつらい', '私は、\nつらい',
                      '私は，つらい', '私は,つらい',
                      '友人は、つらい', '私は、つらかった', '私は、つらくない',
                      '私は、つらいかもしれない', '私は、つらいと聞いた',
                      '私は、とてもつらい', '私は、辛い料理を見た', '私は、つらい？',
                      '私は、嬉しい', '私は、不安です'):
            with self.subTest(right=right):
                artifact = self.generate(request(record(memo=prefix + right + '。'))).artifact
                self.assertFalse(artifact and artifact.graph.annotations)
        artifact = self.generate(request(record(memo='', action=prefix + '私は、つらい。'))).artifact
        self.assertFalse(artifact and artifact.graph.annotations)

    def test_burden_spelling_does_not_promote_food_or_qualified_feelings(self):
        prefix = '私は仕事を続けたいけれど、'
        for right in ('辛い', 'カレーは辛い', '友人は辛い', '私はカレーが辛い',
                      '私は辛い料理を見た', '私は辛いものを食べたい',
                      '私は辛かった', '私は辛くない', '私は辛くなかった',
                      '私は辛いかもしれない', '私は辛いと思う',
                      '私は辛いと聞いた', '私は辛いという夢を見た',
                      '私はとても辛い', '私は辛い？'):
            with self.subTest(right=right):
                artifact = self.generate(request(record(memo=prefix + right + '。'))).artifact
                if artifact:
                    self.assertFalse(artifact.graph.annotations)
                    artifact.safe_projection(authenticated_owner_scope=OWNER)
        for memo in ('私は辛い。', '私は仕事を続けたい。私は辛い。',
                     '私は仕事を続けたけれど、私は辛い。',
                     '私は仕事を続けたくないけれど、私は辛い。',
                     '「私は仕事を続けたいけれど、私は辛い」と友人が言った。'):
            with self.subTest(memo=memo):
                artifact = self.generate(request(record(memo=memo))).artifact
                if artifact:
                    self.assertFalse(artifact.graph.annotations)
        artifact = self.generate(request(record(memo='', action=prefix + '私は辛い。'))).artifact
        self.assertIsNotNone(artifact)
        self.assertFalse(artifact.graph.annotations)
        self.assertIn('SOURCE_SCOPE', [g.missing_scope for g in artifact.graph.unknown_gaps])
        artifact.safe_projection(authenticated_owner_scope=OWNER)

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

    def test_open_dream_and_heard_read_scope_do_not_become_observed_claims(self):
        for prefix in ('夢を見た。', '友人から聞いた話です。', '本で読んだ内容です。'):
            for clause in ('私は資料を調べた。', '私は資料を調べなかった。',
                           '私は仕事を続けたくありませんでした。',
                           '私は資料を調べるかもしれないと思う。',
                           '私は資料を調べた後、疑問が減った。',
                           '私は仕事を続けたいけれど、私はつらい。'):
                with self.subTest(prefix=prefix, clause=clause):
                    self.assertIsNone(self.generate(request(record(memo=prefix + clause))).artifact)
            for memo, action in ((prefix, '私は資料を調べた。'),
                                 ('私は資料を調べた。', prefix)):
                with self.subTest(memo=memo, action=action):
                    self.assertIsNone(self.generate(request(record(memo=memo, action=action))).artifact)

    def test_open_dream_scope_keeps_independent_record_and_unresolved_source(self):
        for context in ('夢を見た。', '友人から聞いた話です。', '本で読んだ内容です。'):
            with self.subTest(context=context):
                req = request(record(memo=context + '私は資料を調べた。その後私は作品を作った。'),
                              record(2, memo='私は記録を残した。'))
                artifact = self.generate(req).artifact
                self.assertIsNotNone(artifact)
                visual = artifact.safe_projection(authenticated_owner_scope=OWNER)
                text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text']
                self.assertEqual([n['visible_label'] for n in visual['nodes']], ['記録を残す（実行済み）'])
                self.assertFalse(visual['edges'])
                self.assertIn('まだ読み取れていない内容', text)
                self.assertNotIn('資料を調べる', text)
                node, = artifact.graph.nodes
                evidence, = node.evidence_refs
                source = next(s.envelope for s in freeze_analysis_sources(req).sources
                              if s.envelope.envelope_id == evidence.source_envelope_id)
                literal = source.raw_utf8[evidence.utf8_start:evidence.utf8_end]
                self.assertEqual(literal.decode(), '私は記録を残した')
                self.assertEqual(hashlib.sha256(literal).hexdigest(), evidence.literal_sha256)
        # The same clear clause outside an open attribution retains its fact.
        clean = self.generate(request(record(memo='私は資料を調べた。'))).artifact
        self.assertEqual(clean.safe_projection(authenticated_owner_scope=OWNER)['nodes'][0]['visible_label'],
                         '資料を調べる（実行済み）')

    def test_open_dream_scope_cannot_be_adopted_by_supplement_or_correction(self):
        clause = '私は資料を調べた'
        for context in ('夢を見た。', '友人から聞いた話です。', '本で読んだ内容です。'):
            original = record(memo=context + clause + '。')
            for answer in ('「' + clause + '」ではなく「私は資料を調べなかった」です。',
                           '「' + clause + '」は取り消します。'):
                with self.subTest(context=context, answer=answer):
                    self.assertIsNone(self.generate(request(self.with_answer(original, answer),
                        record(2, memo='私は記録を残した。'))).artifact)
            self.assertIsNone(self.generate(request(self.with_answer(
                record(memo='私は記録を残した。'), context + clause + '。'))).artifact)

    def test_split_sentence_does_not_erase_uncertainty_or_negation_host(self):
        tail = 'その内容を忘れないように長い文章として残しています' * 4
        for head in ('私は資料を調べた、と思います、',
                     '私は資料を調べた、とは言えないのですが、',
                     '私は仕事を続けたい、とは思いません、'):
            for ending in ('', tail):
                memo = head + ending + '。'
                for original in (record(memo=memo), record(memo='', action=memo)):
                    with self.subTest(head=head, long=bool(ending), field=original.original_json):
                        self.assertIsNone(self.generate(request(original)).artifact)
        # A mechanically cut leading context is not a sentence boundary.
        self.assertIsNone(self.generate(request(record(memo=tail + '、私は資料を調べた。'))).artifact)

    def test_split_sentence_keeps_separate_statement_and_its_exact_evidence(self):
        tail = 'その内容を忘れないように長い文章として残しています' * 4
        unresolved = '私は仕事を続けたい、とは思いません、' + tail
        for separator in ('。', '。　', '\n', '\r\n', ';', '；'):
            with self.subTest(separator=separator):
                req = request(record(memo=unresolved + separator + '　私は記録を残した。'))
                artifact = self.generate(req).artifact
                self.assertIsNotNone(artifact)
                projection = artifact.safe_projection(authenticated_owner_scope=OWNER)
                self.assertEqual([n['visible_label'] for n in projection['nodes']], ['記録を残す（実行済み）'])
                self.assertFalse(projection['edges'])
                text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text']
                self.assertIn('まだ読み取れていない内容', text)
                self.assertNotIn('続けることへの希望', text)
                node, = artifact.graph.nodes
                evidence, = node.evidence_refs
                envelope = freeze_analysis_sources(req).sources[0].envelope
                raw = envelope.raw_utf8[evidence.utf8_start:evidence.utf8_end]
                field = envelope.raw_utf8[evidence.field_utf8_start:evidence.field_utf8_end].decode()
                self.assertEqual(raw.decode(), '私は記録を残した')
                self.assertEqual(field[evidence.scalar_start:evidence.scalar_end], raw.decode())
                self.assertEqual(hashlib.sha256(raw).hexdigest(), evidence.literal_sha256)
        for separator in (';', '；'):
            artifact = self.generate(request(record(memo=
                '私は資料を調べた' + separator + '私は記録を残した。'))).artifact
            self.assertEqual(len(artifact.graph.nodes), 2)
            self.assertFalse(artifact.graph.edges)

    def test_split_sentence_stays_unresolved_in_updates_and_period_comparison(self):
        tail = 'その内容を忘れないように長い文章として残しています' * 4
        unresolved = '私は仕事を続けたい、とは思いません、' + tail + '。'
        clean = '私は記録を残した。'
        self.assertIsNone(self.generate(request(self.with_answer(record(memo=clean), unresolved))).artifact)
        original = record(memo=unresolved + clean)
        for answer in ('「私は仕事を続けたい」ではなく「私は仕事を続けたくありません」です。',
                       '「私は仕事を続けたい」は取り消します。'):
            with self.subTest(answer=answer):
                self.assertIsNone(self.generate(request(self.with_answer(original, answer))).artifact)
        artifact = self.compared(unresolved + clean,
            '私は資料を調べた、とは言えないのですが、' + tail + '。' + clean).artifact
        self.assertEqual(artifact.period_comparison.change_claims, ())
        self.assertEqual(artifact.period_comparison.comparability_state, 'COMPARABLE')

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

    def test_cognitive_topic_comma_keeps_possible_content_and_whole_source(self):
        for topic, content, suffix, host, polarity, time in (
            ('私は、', '資料を調べる', 'かもしれないと', '思う', 'positive', 'nonpast'),
            ('僕は,', '資料を調べなかった', 'かも知れないと', '考えている', 'negative', 'past'),
            ('わたしは、', '考えをノートに書いた', 'かもって', '考えちゃう', 'positive', 'past'),
            ('自分は,', '新しい資料を調べない', 'かもしれないと', '思ってしまう', 'negative', 'nonpast'),
        ):
            with self.subTest(topic=topic, content=content):
                clause = topic + content + suffix + host
                req = request(record(memo='　' + clause + '。'))
                artifact = self.generate(req).artifact
                self.assertIsNotNone(artifact)
                node, = artifact.graph.nodes
                p = node.proposition
                inner = p.possible_content
                self.assertEqual((p.actor, node.node_kind, node.polarity, node.modality, node.temporal_scope),
                                 ('SELF', 'ATTENTION_OR_THOUGHT', 'neutral', 'fact', 'current_input'))
                self.assertEqual((inner.actor, inner.modality, inner.polarity, inner.temporal_scope),
                                 ('UNSPECIFIED', 'possibility', polarity, time))
                self.assertEqual([i for _, a, b in p.source_parts for i in range(a, b)], list(range(len(clause))))
                source, = freeze_analysis_sources(req).sources
                e, = node.evidence_refs
                raw = source.envelope.raw_utf8[e.utf8_start:e.utf8_end]
                field = source.envelope.raw_utf8[e.field_utf8_start:e.field_utf8_end].decode()
                self.assertEqual(raw.decode(), clause)
                self.assertEqual(field[e.scalar_start:e.scalar_end], clause)
                self.assertEqual(hashlib.sha256(raw).hexdigest(), e.literal_sha256)
                plain = self.generate(request(record(memo=topic[:-1] + content + suffix + host + '。'))).artifact
                text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text']
                self.assertEqual(text, plain.safe_text_projection(authenticated_owner_scope=OWNER)['text'])
                self.assertIn('（この記述時点の考え）', text)
                self.assertNotIn('実行済み', text)
                self.assertFalse(artifact.graph.edges)
                for changed in (replace(inner, modality='fact'), replace(inner, actor='SELF'),
                                replace(inner, polarity='negative' if polarity == 'positive' else 'positive')):
                    forged = replace(node, proposition=replace(p, possible_content=changed))
                    with self.assertRaises(AnalysisSourceError):
                        replace(artifact, graph=replace(artifact.graph, nodes=(forged,))).safe_projection(
                            authenticated_owner_scope=OWNER)

    def test_cognitive_topic_comma_keeps_updates_and_semantic_comparison(self):
        old = '私は、資料を調べるかもしれないと思う'
        new = '僕は,資料を調べなかったかも知れないと考えている'
        base = record(memo='私は記録を残した。' + old + '。')
        for answer, count in ((new + '。', 3), ('「' + old + '」ではなく「' + new + '」です。', 2)):
            with self.subTest(answer=answer):
                req = request(self.with_answer(base, answer))
                artifact = self.generate(req).artifact
                self.assertIsNotNone(artifact)
                self.assertEqual(len(artifact.graph.nodes), count)
                self.assertFalse(artifact.graph.edges)
                node = next(n for n in artifact.graph.nodes if n.proposition.possible_content
                            and n.proposition.possible_content.polarity == 'negative')
                source = next(s.envelope for s in freeze_analysis_sources(req).sources
                              if s.envelope.source_role == 'SUPPLEMENTAL_ANSWER')
                e, = node.evidence_refs
                self.assertEqual(e.source_envelope_id, source.envelope_id)
                self.assertEqual(source.raw_utf8[e.utf8_start:e.utf8_end].decode(), new)
                artifact.safe_projection(authenticated_owner_scope=OWNER)
        withdrawn = self.generate(request(self.with_answer(base, '「' + old + '」は取り消します。'))).artifact
        self.assertEqual([n.visible_label for n in withdrawn.graph.nodes], ['私は記録を残した'])
        same = self.compared(old + '。', old.replace('、', '') + '。').artifact
        self.assertEqual(same.period_comparison.change_claims, ())
        changed = self.compared(old.replace('調べる', '調べない') + '。', old + '。').artifact
        self.assertEqual(changed.safe_projection(authenticated_owner_scope=OWNER)['period_comparison']
                         ['safe_change_kinds'], ['ROUTE_EVIDENCE_CHANGED'])

    def test_cognitive_topic_comma_keeps_unproved_scopes_pending(self):
        for clause in ('私は，資料を調べるかもしれないと思う',
                       '私は、、資料を調べるかもしれないと思う',
                       '私は、 資料を調べるかもしれないと思う',
                       '私は、　資料を調べるかもしれないと思う',
                       '私は、\t資料を調べるかもしれないと思う',
                       '私は、\n資料を調べるかもしれないと思う',
                       '私は、今日資料を調べるかもしれないと思う',
                       '友人は、資料を調べるかもしれないと思う',
                       '私は、友人が資料を調べるかもしれないと思う',
                       '私は、資料を調べるかもしれないと思っていた',
                       '私は、資料を調べるかもしれないと思っていない',
                       '私は、資料を調べるかもしれないと思う？',
                       '私は、資料を調べるかもしれないと思うと聞いた',
                       '私は、資料を調べたいかもしれないと思う',
                       '私は、資料を読んだかもしれないと思う'):
            with self.subTest(clause=clause):
                self.assertIsNone(self.generate(request(record(memo=clause + '。'))).artifact)
        self.assertIsNone(self.generate(request(record(memo=
            '私は記録を残した。私は、資料を調べるかもしれないと思う。まだ違うかもしれない。'))).artifact)

    def test_unparsed_cognitive_time_preserves_independent_original_claims(self):
        for time in ('今朝', '今週', '今月', '今年'):
            for predicate in ('調べた', '調べない'):
                with self.subTest(time=time, predicate=predicate):
                    unresolved = '私は' + time + '資料を' + predicate + 'かもしれないと思う'
                    for memo in (unresolved + '。私は記録を残した。',
                                 '私は記録を残した。' + unresolved + '。'):
                        req = request(record(memo=memo))
                        result = self.generate(req)
                        self.assertEqual(result.status, EngineStatus.GENERATED)
                        artifact = result.artifact
                        node, = artifact.graph.nodes
                        self.assertEqual(node.proposition.arguments, (('を', '記録'),))
                        self.assertEqual(node.proposition.predicate_lemma, '残す')
                        e, = node.evidence_refs
                        source = freeze_analysis_sources(req).sources[0].envelope
                        literal = '私は記録を残した'
                        field = source.raw_utf8[e.field_utf8_start:e.field_utf8_end].decode()
                        self.assertEqual(source.raw_utf8[e.utf8_start:e.utf8_end].decode(), literal)
                        self.assertEqual(field[e.scalar_start:e.scalar_end], literal)
                        self.assertEqual(hashlib.sha256(literal.encode()).hexdigest(), e.literal_sha256)
                        p = artifact.safe_projection(authenticated_owner_scope=OWNER)
                        text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)
                        self.assertEqual(p['projection_of'], text['projection_of'])
                        self.assertEqual([n['visible_label'] for n in p['nodes']], ['記録を残す（実行済み）'])
                        self.assertIn('まだ読み取れていない内容', text['text'])
                        self.assertNotIn(time + '資料', text['text'])
                        self.assertFalse(p['edges'])

    def test_unparsed_cognitive_time_keeps_order_updates_and_period_meaning(self):
        unresolved = '私は今月資料を調べないかもしれないと思う'
        normal = '私は記録を残した'
        base = record(memo=normal + '。' + unresolved + '。その後私は作品を作った。')
        artifact = self.generate(request(base)).artifact
        self.assertEqual([n.proposition.predicate_lemma for n in artifact.graph.nodes], ['残す', '作る'])
        self.assertFalse(artifact.graph.edges)
        for answer, expected in (('私は資料を調べた。', ['残す', '作る', '調べる']),
                ('「' + normal + '」ではなく「私は考えを書いた」です。', ['作る', '書く']),
                ('「' + normal + '」は取り消します。', ['作る'])):
            with self.subTest(answer=answer):
                artifact = self.generate(request(self.with_answer(base, answer))).artifact
                self.assertEqual([n.proposition.predicate_lemma for n in artifact.graph.nodes], expected)
                artifact.safe_projection(authenticated_owner_scope=OWNER)
        for answer in ('「' + unresolved + '」は取り消します。',
                       '「' + unresolved + '」ではなく「私は資料を調べた」です。'):
            with self.subTest(answer=answer):
                self.assertIsNone(self.generate(request(self.with_answer(base, answer))).artifact)
        compared = self.compared(unresolved + '。' + normal + '。',
                                 unresolved.replace('今月', '来月') + '。' + normal + '。').artifact
        self.assertEqual(compared.period_comparison.change_claims, ())

    def test_cognitive_time_recovery_does_not_admit_unparsed_or_open_uncertainty(self):
        unresolved = '私は今月資料を調べないかもしれないと思う'
        self.assertIsNone(self.generate(request(record(memo=unresolved + '。'))).artifact)
        # No expansion to new cognition nouns, other time markers or unknown
        # predicates; open speculation still blocks the complete source field.
        for bad in ('私は今月号を見たかもしれないと思う',
                    '私は今年度の資料を調べたかもしれないと思う',
                    '私は今週の資料を調べたかもしれないと思う',
                    '私は今、資料を調べたかもしれないと思う',
                    '私は今資料を明日ノートに書いたかもしれないと思う',
                    '私は現在資料を調べたかもしれないと思う',
                    '私は今日資料を調べたかもしれないと思う',
                    '私は今月資料を読んだかもしれないと思う',
                    '私は今月資料を調べたいかもしれないと思う',
                    'まだ違うかもしれない'):
            with self.subTest(bad=bad):
                self.assertIsNone(self.generate(request(record(
                    memo='私は記録を残した。' + unresolved + '。' + bad + '。'))).artifact)
        target = 'cocolon_meaning_experience_engine.cores.analysis.intent_compiler._source_current_cognition'
        with patch(target, return_value=False):
            self.assertIsNone(self.generate(request(record(
                memo=unresolved + '。私は記録を残した。'))).artifact)
        with_answer = self.with_answer(record(memo='私は記録を残した。'), unresolved + '。')
        self.assertIsNone(self.generate(request(with_answer)).artifact)

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
        for topic in ('私は', '私は、', '僕は,'):
            with self.subTest(topic=topic), patch(target, return_value=False):
                result = self.generate(request(record(memo=topic + '資料を調べたかもと思っている。')))
            self.assertEqual(result.status, EngineStatus.UNAVAILABLE)

    def test_unfinished_result_reaches_text_and_graph_without_inventing_actor(self):
        for noun, particle, predicate in (
            ('方法', 'が', '見つかっていない'), ('方針', 'は', '決まっていません'),
            ('仕事の方針', 'も', '定まっていない'),
            ('昨日の方針', 'が', '決まっていない'), ('昨日分の方法', 'は', '見つかっていません'),
            ('仕事の昨日分', 'も', '定まっていない'),
            ('昨日の新しい方針', 'が', '決まっていません')):
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

    def test_unfinished_nominal_yesterday_survives_completed_self_writing(self):
        unfinished = 'まだ昨日の方針が決まっていない'
        for writing in ('私は記録を書いた', '僕は、新しい記録を書きました',
                        'ぼくは新しいメモを書いた', '俺は振り返りを書いた'):
            for memo, action in ((writing + '。' + unfinished + '。', ''),
                                 (unfinished + '。' + writing + '。', ''),
                                 (unfinished + '。', writing + '。')):
                with self.subTest(memo=memo, action=action):
                    req = request(record(memo=memo, action=action))
                    artifact = self.generate(req).artifact
                    self.assertIsNotNone(artifact)
                    nodes = [n for n in artifact.graph.nodes if n.proposition.result_state == 'NOT_YET']
                    self.assertEqual(len(nodes), 1)
                    node, = nodes
                    self.assertEqual((node.proposition.actor, node.polarity, node.modality,
                                      node.temporal_scope), ('UNSPECIFIED', 'negative', 'fact', 'current_input'))
                    source, = freeze_analysis_sources(req).sources
                    e, = node.evidence_refs
                    raw = source.envelope.raw_utf8[e.utf8_start:e.utf8_end]
                    self.assertEqual(raw.decode(), unfinished)
                    self.assertEqual(hashlib.sha256(raw).hexdigest(), e.literal_sha256)
                    self.assertEqual(e.field_path, 'memo')
                    self.assertFalse(artifact.graph.edges)
                    label = unfinished + '（この記述時点）'
                    self.assertIn(label, artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'])
                    self.assertIn(label, [n['visible_label'] for n in
                        artifact.safe_projection(authenticated_owner_scope=OWNER)['nodes']])

    def test_unfinished_nominal_yesterday_writing_preserves_updates_and_comparison(self):
        old, new = 'まだ昨日の方針が決まっていない', 'まだ仕事の昨日分が定まっていない'
        writing = '私は記録を書いた。'
        original = record(memo=writing + old + '。')
        for answer, expected in ((old.replace('いない', 'いません') + '。', [old]),
                ('「' + old + '」ではなく「' + new + '」です。', [new]),
                ('「' + old + '」は取り消します。', [])):
            with self.subTest(answer=answer):
                artifact = self.generate(request(self.with_answer(original, answer))).artifact
                self.assertIsNotNone(artifact)
                self.assertEqual([n.visible_label for n in artifact.graph.nodes
                                  if n.proposition.result_state == 'NOT_YET'], expected)
                self.assertFalse(artifact.graph.edges)
                artifact.safe_projection(authenticated_owner_scope=OWNER)
        same = self.compared(writing + old + '。', writing + old.replace('いない', 'いません') + '。').artifact
        self.assertEqual(same.period_comparison.change_claims, ())
        changed = self.compared(writing + old + '。', writing + old.replace('昨日', '今日') + '。').artifact
        self.assertIn('ROUTE_EVIDENCE_CHANGED', changed.safe_projection(authenticated_owner_scope=OWNER)
                      ['period_comparison']['safe_change_kinds'])

    def test_unfinished_state_survives_writing_with_medium_or_location(self):
        unfinished = 'まだ昨日の方針が決まっていない'
        for writing in ('私は考えをノートに書いた', '私はノートに考えを書いた',
                        '僕は、職場で記録を書きました', '俺は記録を職場で書いた'):
            for memo, action in ((writing + '。' + unfinished + '。', ''),
                                 (unfinished + '。' + writing + '。', ''),
                                 (unfinished + '。', writing + '。')):
                with self.subTest(memo=memo, action=action):
                    req = request(record(memo=memo, action=action))
                    artifact = self.generate(req).artifact
                    self.assertIsNotNone(artifact)
                    self.assertEqual([n.node_kind for n in artifact.graph.nodes].count('ACTION_OR_NONACTION'), 1)
                    node, = (n for n in artifact.graph.nodes if n.proposition.result_state == 'NOT_YET')
                    self.assertEqual((node.proposition.actor, node.polarity, node.modality, node.temporal_scope),
                                     ('UNSPECIFIED', 'negative', 'fact', 'current_input'))
                    self.assertEqual(node.proposition.relative_day, '')
                    self.assertFalse(artifact.graph.edges)
                    source, = freeze_analysis_sources(req).sources
                    e, = node.evidence_refs
                    raw = source.envelope.raw_utf8[e.utf8_start:e.utf8_end]
                    field = source.envelope.raw_utf8[e.field_utf8_start:e.field_utf8_end].decode()
                    self.assertEqual((raw.decode(), field[e.scalar_start:e.scalar_end]), (unfinished, unfinished))
                    self.assertEqual(hashlib.sha256(raw).hexdigest(), e.literal_sha256)
                    text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text']
                    self.assertIn(unfinished + '（この記述時点）', text)
                    visual = artifact.safe_projection(authenticated_owner_scope=OWNER)
                    self.assertIn(unfinished + '（この記述時点）', [n['visible_label'] for n in visual['nodes']])

    def test_writing_medium_keeps_unfinished_updates_and_period_meaning(self):
        old, new = 'まだ昨日の方針が決まっていない', 'まだ仕事の昨日分が定まっていない'
        writing = '私は考えをノートに書いた。'
        original = record(memo=writing + old + '。')
        for answer, expected in ((old.replace('いない', 'いません') + '。', [old]),
                ('「' + old + '」ではなく「' + new + '」です。', [new]),
                ('「' + old + '」は取り消します。', [])):
            with self.subTest(answer=answer):
                artifact = self.generate(request(self.with_answer(original, answer))).artifact
                self.assertIsNotNone(artifact)
                self.assertEqual([n.visible_label for n in artifact.graph.nodes
                                  if n.proposition.result_state == 'NOT_YET'], expected)
                self.assertEqual(artifact.graph.nodes[0].proposition.arguments, (('を', '考え'), ('に', 'ノート')))
                self.assertFalse(artifact.graph.edges)
                artifact.safe_projection(authenticated_owner_scope=OWNER)
        same = self.compared(writing + old + '。', writing + old.replace('いない', 'いません') + '。').artifact
        self.assertIsNotNone(same)
        self.assertEqual(same.period_comparison.change_claims, ())
        changed = self.compared(writing + old + '。', writing + old.replace('昨日', '今日') + '。').artifact
        self.assertIsNotNone(changed)
        self.assertIn('ROUTE_EVIDENCE_CHANGED', changed.safe_projection(authenticated_owner_scope=OWNER)
                      ['period_comparison']['safe_change_kinds'])

    def test_unfinished_nominal_yesterday_keeps_updates_evidence_and_comparison(self):
        old, new = 'まだ昨日の方針が決まっていない', 'まだ仕事の昨日分が定まっていない'
        original = record(memo='私は資料を調べた。' + old + '。')
        repeated = self.generate(request(self.with_answer(original, old.replace('いない', 'いません') + '。'))).artifact
        node = next(n for n in repeated.graph.nodes if n.proposition.result_state)
        self.assertEqual((len(node.record_refs), len(node.evidence_refs)), (1, 2))
        for answer, expected in (('「' + old + '」ではなく「' + new + '」です。', new),
                                  ('「' + old + '」は取り消します。', None)):
            with self.subTest(answer=answer):
                req = request(self.with_answer(original, answer))
                artifact = self.generate(req).artifact
                self.assertIsNotNone(artifact)
                self.assertFalse(artifact.graph.edges)
                results = [n for n in artifact.graph.nodes if n.proposition.result_state]
                self.assertEqual([n.visible_label for n in results], [] if expected is None else [expected])
                for node in results:
                    e, = node.evidence_refs
                    source = next(s.envelope for s in freeze_analysis_sources(req).sources
                                  if s.envelope.envelope_id == e.source_envelope_id)
                    self.assertEqual(source.source_role, 'SUPPLEMENTAL_ANSWER')
                    self.assertEqual(source.raw_utf8[e.utf8_start:e.utf8_end].decode(), new)
                artifact.safe_projection(authenticated_owner_scope=OWNER)
        self.assertEqual(self.compared(old + '。', old.replace('いない', 'いません') + '。')
                         .artifact.period_comparison.change_claims, ())
        changed = self.compared(old + '。', old.replace('昨日', '今日') + '。').artifact
        self.assertIn('ROUTE_EVIDENCE_CHANGED', changed.safe_projection(authenticated_owner_scope=OWNER)
                      ['period_comparison']['safe_change_kinds'])
        for memo in ('まだ昨日方針が決まっていない。', '昨日まだ方針が決まっていない。',
                     'まだ昨日の方針が決まっていなかった。', 'まだ昨日の方針が決まっていない？',
                     'まだ昨日の方針が決まっていないかもしれない。',
                     'まだ昨日の方針が決まっていないわけではない。',
                     '夢を見た。' + old + '。', '友人によると、' + old + '。',
                     '友人が話した。' + old + '。', '友人から聞いた話です。' + old + '。'):
            with self.subTest(memo=memo):
                outcome = self.generate(request(record(memo=memo)))
                self.assertFalse(outcome.artifact and any(n.proposition.result_state
                    for n in outcome.artifact.graph.nodes))

    def test_feeling_nominal_keeps_unfinished_fact_and_exact_evidence(self):
        for noun, stem in (('気持ち', '定ま'), ('不安の原因', '見つか'), ('昨日の気持ち', '決ま')):
            for particle in ('が', 'は', 'も'):
                for ending in ('いない', 'いません'):
                    literal = 'まだ' + noun + particle + stem + 'って' + ending
                    with self.subTest(literal=literal):
                        req = request(record(memo='私は記録を残した。' + literal + '。'))
                        artifact = self.generate(req).artifact
                        self.assertIsNotNone(artifact)
                        node, = (n for n in artifact.graph.nodes if n.proposition.result_state == 'NOT_YET')
                        self.assertEqual((node.node_kind, node.proposition.actor, node.polarity,
                                          node.modality, node.temporal_scope),
                            ('IMMEDIATE_RESULT_OR_AFTERMATH', 'UNSPECIFIED', 'negative', 'fact', 'current_input'))
                        self.assertEqual(node.proposition.arguments, ((particle, noun),))
                        self.assertEqual(node.proposition.relative_day, '')
                        source, = freeze_analysis_sources(req).sources
                        e, = node.evidence_refs
                        raw = source.envelope.raw_utf8[e.utf8_start:e.utf8_end]
                        field = source.envelope.raw_utf8[e.field_utf8_start:e.field_utf8_end].decode()
                        self.assertEqual((raw.decode(), field[e.scalar_start:e.scalar_end]), (literal, literal))
                        self.assertEqual(hashlib.sha256(raw).hexdigest(), e.literal_sha256)
                        label = literal.replace('いません', 'いない') + '（この記述時点）'
                        self.assertIn(label, artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'])
                        self.assertFalse(artifact.graph.edges)
                        self.assertFalse(artifact.graph.annotations)
                        for changes in ({'actor': 'SELF'}, {'polarity': 'positive'}, {'arguments': ((particle, '方針'),)}):
                            with self.assertRaises(AnalysisSourceError):
                                forged = replace(node, proposition=replace(node.proposition, **changes))
                                replace(artifact, graph=replace(artifact.graph, nodes=(artifact.graph.nodes[0], forged))).safe_projection(
                                    authenticated_owner_scope=OWNER)

    def test_feeling_nominal_unfinished_keeps_updates_and_period_differences(self):
        old, new = 'まだ気持ちが定まっていない', 'まだ不安の原因が見つかっていない'
        prefix = '私は記録を残した。'
        original = record(memo=prefix + old + '。')
        for answer, expected in ((new + '。', [old, new]),
                ('「' + old + '」ではなく「' + new + '」です。', [new]),
                ('「' + old + '」は取り消します。', [])):
            with self.subTest(answer=answer):
                artifact = self.generate(request(self.with_answer(original, answer))).artifact
                self.assertIsNotNone(artifact)
                self.assertEqual([n.visible_label for n in artifact.graph.nodes
                                  if n.proposition.result_state == 'NOT_YET'], expected)
                self.assertFalse(artifact.graph.edges)
                artifact.safe_projection(authenticated_owner_scope=OWNER)
        same = self.compared(prefix + old + '。', prefix + old.replace('いない', 'いません') + '。').artifact
        self.assertIsNotNone(same)
        self.assertEqual(same.period_comparison.change_claims, ())
        changed = self.compared(prefix + new + '。', prefix + old + '。').artifact
        self.assertIsNotNone(changed)
        self.assertIn('ROUTE_EVIDENCE_CHANGED', changed.safe_projection(authenticated_owner_scope=OWNER)
                      ['period_comparison']['safe_change_kinds'])
        for text in ('まだ気持ちがつらい。', 'まだ気持ちが定まっていなかった。',
                old + '？', old + 'と思う。', old + 'かもしれない。', old + 'なら。',
                '夢を見た。' + old + '。', '友人が話した。' + old + '。', '「' + old + '」と聞いた。'):
            with self.subTest(text=text):
                artifact = self.generate(request(record(memo=text))).artifact
                self.assertFalse(artifact and any(n.proposition.result_state == 'NOT_YET' for n in artifact.graph.nodes))

    def test_unfinished_result_requires_shared_full_clause_witness(self):
        from cocolon_meaning_experience_engine.cores.analysis import intent_compiler as compiler
        build = compiler.build_final_stage1_grounded_observation_plan
        def without_witness(*args, **kwargs):
            plan = build(*args, **kwargs)
            return replace(plan, nuclei=tuple(replace(n, semantic_frame=replace(n.semantic_frame,
                attribute_codes=tuple(c for c in n.semantic_frame.attribute_codes
                                      if c != 'semantic_role:present_unfinished'))) for n in plan.nuclei))
        with patch.object(compiler, 'build_final_stage1_grounded_observation_plan', side_effect=without_witness):
            for noun in ('方法', '昨日の方法', '仕事の昨日分'):
                with self.subTest(noun=noun):
                    self.assertIsNone(self.generate(request(record(memo='まだ' + noun + 'が見つかっていない。'))).artifact)

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

    def test_nominal_changes_with_feeling_words_keep_whole_meaning_and_evidence(self):
        for ending in ('気持ちメモが増えた', '不安が減った', '気持ちが変わった',
                       '不安メモは戻った', '新しい気持ちメモも増えた'):
            for action in ('私は振り返りメモを残した後、', '僕は資料を調べてから、'):
                memo = action + ending
                with self.subTest(memo=memo):
                    req = request(record(memo=memo + '。'))
                    artifact = self.generate(req).artifact
                    self.assertIsNotNone(artifact)
                    first, change = artifact.graph.nodes
                    self.assertEqual((change.node_kind, change.proposition.result_state,
                        change.proposition.actor, change.modality, change.temporal_scope),
                        ('IMMEDIATE_RESULT_OR_AFTERMATH', 'BOUNDED_CHANGE',
                         'UNSPECIFIED', 'fact', 'past'))
                    edge, = artifact.graph.edges
                    self.assertEqual((edge.edge_kind, edge.endpoint_refs),
                        ('OBSERVED_ORDER', (first.node_ref, change.node_ref)))
                    source, = freeze_analysis_sources(req).sources
                    for node in artifact.graph.nodes:
                        self.assertEqual([i for _, a, b in node.proposition.source_parts
                                          for i in range(a, b)], list(range(len(node.visible_label))))
                        for e in node.evidence_refs:
                            raw = source.envelope.raw_utf8[e.utf8_start:e.utf8_end]
                            field = source.envelope.raw_utf8[e.field_utf8_start:e.field_utf8_end].decode()
                            self.assertEqual(raw.decode(), field[e.scalar_start:e.scalar_end])
                            self.assertEqual(hashlib.sha256(raw).hexdigest(), e.literal_sha256)
                    text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text']
                    self.assertIn(ending + '（記録された変化）', text)
                    self.assertIn('原因を示す線ではありません', text)
                    self.assertEqual(artifact.graph.annotations, ())

    def test_feeling_word_changes_still_require_shared_episode_witness(self):
        from cocolon_meaning_experience_engine.cores.analysis import intent_compiler as compiler
        build = compiler.build_final_stage1_grounded_observation_plan
        for corruption in ('relation', 'range', 'actor', 'wish', 'bounded_marker', 'action_modality'):
            def corrupt(*args, **kwargs):
                plan = build(*args, **kwargs)
                if corruption == 'relation':
                    return replace(plan, relations=())
                index = 0 if corruption == 'action_modality' else 1
                n = plan.nuclei[index]
                frame = n.semantic_frame
                if corruption == 'actor':
                    frame = replace(frame, actor='other_person')
                elif corruption in ('wish', 'action_modality'):
                    frame = replace(frame, modality='wish')
                elif corruption == 'bounded_marker':
                    frame = replace(frame, attribute_codes=tuple(c for c in frame.attribute_codes
                        if c != 'operator:bounded_change'))
                else:
                    frame = replace(frame, attribute_codes=tuple(
                        'source_fragment_scalar_range:0:1' if c.startswith('source_fragment_scalar_range:') else c
                        for c in frame.attribute_codes))
                nuclei = list(plan.nuclei)
                nuclei[index] = replace(n, semantic_frame=frame)
                return replace(plan, nuclei=tuple(nuclei))
            with self.subTest(corruption=corruption), patch.object(compiler,
                    'build_final_stage1_grounded_observation_plan', side_effect=corrupt):
                self.assertIsNone(self.generate(request(record(memo=
                    '私は資料を調べた後、不安が減った。'))).artifact)

    def test_feeling_word_changes_preserve_unread_scope_and_safe_reparse(self):
        for memo in ('私は資料を調べた後、不安が減らなかった。',
                     '私は資料を調べた後、不安が減ったかもしれない。',
                     '私は資料を調べた後、不安が減ったと聞いた。',
                     '私は資料を調べた後、不安が減ったなら。',
                     '私は資料を調べた後、不安が減った？',
                     '友人は資料を調べた後、不安が減った。',
                     '資料を調べた後、不安が減った。',
                     '私は資料を調べなかった後、不安が減った。',
                     '私は資料を調べてから、気持ち来週メモが増えた。',
                     '私は資料を調べた後、友人の不安が減った。',
                     '私は資料を調べた後、私の不安が減った。',
                     '私は資料を調べた後、仕事の気持ちメモが増えた。'):
            with self.subTest(memo=memo):
                self.assertIsNone(self.generate(request(record(memo=memo))).artifact)
        artifact = self.generate(request(record(memo='私は資料を調べた後、不安が減った。'))).artifact
        first, change = artifact.graph.nodes
        for proposition in (replace(change.proposition, arguments=(('が', '気持ちメモ'),)),
                            replace(change.proposition, predicate_lemma='増える'),
                            replace(change.proposition, modality='feeling'),
                            replace(change.proposition, actor='SELF')):
            with self.subTest(proposition=proposition), self.assertRaises(AnalysisSourceError):
                changed = replace(change, proposition=proposition)
                replace(artifact, graph=replace(artifact.graph, nodes=(first, changed))).safe_projection(
                    authenticated_owner_scope=OWNER)

    def test_feeling_word_changes_preserve_updates_and_period_meaning(self):
        old = '私は資料を調べた後、不安が減った'
        new = '私は記録を残してから、気持ちメモが増えた'
        original = record(memo='私は仕事を続けたい。' + old + '。')
        req = request(self.with_answer(original, '「' + old + '」ではなく「' + new + '」です。'))
        artifact = self.generate(req).artifact
        self.assertIsNotNone(artifact)
        self.assertEqual([n.visible_label for n in artifact.graph.nodes],
            ['私は仕事を続けたい', '私は記録を残して', '気持ちメモが増えた'])
        source = next(s.envelope for s in freeze_analysis_sources(req).sources
                      if s.envelope.source_role == 'SUPPLEMENTAL_ANSWER')
        self.assertTrue(all(e.source_envelope_id == source.envelope_id
                            for e in artifact.graph.edges[0].evidence_refs))
        withdrawn = self.generate(request(self.with_answer(original, '「' + old + '」は取り消します。'))).artifact
        self.assertEqual([n.visible_label for n in withdrawn.graph.nodes], ['私は仕事を続けたい'])
        added = self.generate(request(self.with_answer(record(memo='私は記録を残した。'), old + '。'))).artifact
        self.assertEqual(len(added.graph.nodes), 3)
        same = self.compared('僕は資料を調べてから、不安が減った。', old + '。').artifact
        self.assertEqual(same.period_comparison.change_claims, ())
        for changed in ('私は資料を調べた後、不安が増えた。',
                        '私は資料を調べた後、気持ちメモが減った。'):
            artifact = self.compared(changed, old + '。').artifact
            self.assertIn('ROUTE_EVIDENCE_CHANGED', artifact.safe_projection(
                authenticated_owner_scope=OWNER)['period_comparison']['safe_change_kinds'])

    def test_polite_change_keeps_nominal_meaning_order_and_original_evidence(self):
        for noun, case in (('気持ち', 'が'), ('取り組み方', 'は'),
                           ('新しい気持ちメモ', 'も'), ('仕事の資料', 'が')):
            for action in ('私は資料を調べた後、', '僕は記録を残してから、'):
                memo = action + noun + case + '変わりました'
                with self.subTest(memo=memo):
                    req = request(record(memo=memo + '。'))
                    artifact = self.generate(req).artifact
                    self.assertIsNotNone(artifact)
                    first, change = artifact.graph.nodes
                    self.assertEqual((change.proposition.arguments,
                        change.proposition.predicate_lemma, change.proposition.actor,
                        change.polarity, change.modality, change.temporal_scope),
                        (((case, noun),), '変わる', 'UNSPECIFIED', 'positive', 'fact', 'past'))
                    edge, = artifact.graph.edges
                    self.assertEqual((edge.edge_kind, edge.endpoint_refs),
                        ('OBSERVED_ORDER', (first.node_ref, change.node_ref)))
                    source, = freeze_analysis_sources(req).sources
                    for node in artifact.graph.nodes:
                        self.assertEqual([i for _, a, b in node.proposition.source_parts
                            for i in range(a, b)], list(range(len(node.visible_label))))
                    for e in edge.evidence_refs:
                        raw = source.envelope.raw_utf8[e.utf8_start:e.utf8_end]
                        field = source.envelope.raw_utf8[e.field_utf8_start:e.field_utf8_end].decode()
                        self.assertEqual(raw.decode(), field[e.scalar_start:e.scalar_end])
                        self.assertEqual(hashlib.sha256(raw).hexdigest(), e.literal_sha256)
                    text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text']
                    self.assertIn(noun + case + '変わった（記録された変化）', text)
                    self.assertIn('原因を示す線ではありません', text)
                    self.assertEqual(artifact.graph.annotations, ())

    def test_polite_change_does_not_promote_unproven_scope_or_tampered_meaning(self):
        for memo in (
            '私は資料を調べた後、気持ちが変わりませんでした。',
            '私は資料を調べた後、気持ちが変わります。',
            '私は資料を調べた後、気持ちが変わりましたか。',
            '私は資料を調べた後、気持ちが変わりました？',
            '私は資料を調べた後、気持ちが変わりましたと聞いた。',
            '私は資料を調べた後、気持ちが変わりましたなら。',
            '「私は資料を調べた後、気持ちが変わりました」と友人が言った。',
            '友人は資料を調べた後、気持ちが変わりました。',
            '資料を調べた後、気持ちが変わりました。',
            '私は資料を調べなかった後、気持ちが変わりました。',
            '私は資料を調べた後、友人の気持ちが変わりました。',
            '私は資料を調べた後、私の気持ちが変わりました。',
            '私は資料を調べた後、気持ち来週メモが変わりました。',
        ):
            with self.subTest(memo=memo):
                self.assertIsNone(self.generate(request(record(memo=memo))).artifact)
        artifact = self.generate(request(record(memo=
            '私は資料を調べた後、気持ちが変わりました。'))).artifact
        self.assertIsNotNone(artifact)
        first, change = artifact.graph.nodes
        for proposition in (replace(change.proposition, predicate_lemma='減る'),
                            replace(change.proposition, polarity='negative'),
                            replace(change.proposition, temporal_scope='current_input'),
                            replace(change.proposition, arguments=(('が', '資料'),)),
                            replace(change.proposition, actor='SELF')):
            with self.subTest(proposition=proposition), self.assertRaises(AnalysisSourceError):
                altered = replace(change, proposition=proposition)
                replace(artifact, graph=replace(artifact.graph, nodes=(first, altered))).safe_projection(
                    authenticated_owner_scope=OWNER)

    def test_polite_change_preserves_updates_and_semantic_period_comparison(self):
        old = '私は資料を調べた後、気持ちが変わりました'
        new = '私は記録を残してから、取り組み方が変わりました'
        original = record(memo='私は仕事を続けたい。' + old + '。')
        req = request(self.with_answer(original, '「' + old + '」ではなく「' + new + '」です。'))
        artifact = self.generate(req).artifact
        self.assertIsNotNone(artifact)
        self.assertEqual([n.visible_label for n in artifact.graph.nodes],
            ['私は仕事を続けたい', '私は記録を残して', '取り組み方が変わりました'])
        source = next(s.envelope for s in freeze_analysis_sources(req).sources
                      if s.envelope.source_role == 'SUPPLEMENTAL_ANSWER')
        self.assertTrue(all(e.source_envelope_id == source.envelope_id
                            for e in artifact.graph.edges[0].evidence_refs))
        withdrawn = self.generate(request(self.with_answer(original, '「' + old + '」は取り消します。'))).artifact
        self.assertEqual([n.visible_label for n in withdrawn.graph.nodes], ['私は仕事を続けたい'])
        added = self.generate(request(self.with_answer(record(memo='私は記録を残した。'), old + '。'))).artifact
        self.assertEqual(len(added.graph.nodes), 3)
        same = self.compared(old + '。', '僕は資料を調べてから、気持ちが変わった。').artifact
        self.assertEqual(same.period_comparison.change_claims, ())
        changed = self.compared(new + '。', old + '。').artifact
        self.assertIn('ROUTE_EVIDENCE_CHANGED', changed.safe_projection(
            authenticated_owner_scope=OWNER)['period_comparison']['safe_change_kinds'])

    def test_polite_decrease_increase_return_keep_complete_meaning_and_evidence(self):
        # These three episodes were deliberately unavailable in u139: the
        # shared owner now proves their complete finite clauses as well.
        for noun, case, polite, lemma, plain in (
            ('不安', 'が', '減りました', '減る', '減った'),
            ('気持ちメモ', 'も', '増えました', '増える', '増えた'),
            ('資料', 'は', '戻りました', '戻る', '戻った'),
            ('新しい学びノート', 'が', '増えました', '増える', '増えた'),
        ):
            for action in ('私は資料を調べた後、', '僕は記録を残してから、'):
                memo = action + noun + case + polite
                with self.subTest(memo=memo):
                    req = request(record(memo=memo + '。'))
                    artifact = self.generate(req).artifact
                    self.assertIsNotNone(artifact)
                    first, change = artifact.graph.nodes
                    self.assertEqual((change.proposition.arguments,
                        change.proposition.predicate_lemma, change.proposition.actor,
                        change.modality, change.temporal_scope),
                        (((case, noun),), lemma, 'UNSPECIFIED', 'fact', 'past'))
                    edge, = artifact.graph.edges
                    self.assertEqual((edge.edge_kind, edge.endpoint_refs),
                        ('OBSERVED_ORDER', (first.node_ref, change.node_ref)))
                    source, = freeze_analysis_sources(req).sources
                    for e in edge.evidence_refs:
                        raw = source.envelope.raw_utf8[e.utf8_start:e.utf8_end]
                        field = source.envelope.raw_utf8[e.field_utf8_start:e.field_utf8_end].decode()
                        self.assertEqual(raw.decode(), field[e.scalar_start:e.scalar_end])
                        self.assertEqual(hashlib.sha256(raw).hexdigest(), e.literal_sha256)
                    self.assertEqual([i for _, a, b in change.proposition.source_parts
                        for i in range(a, b)], list(range(len(change.visible_label))))
                    text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text']
                    self.assertIn(noun + case + plain + '（記録された変化）', text)
                    self.assertIn('原因を示す線ではありません', text)
                    self.assertEqual(artifact.graph.annotations, ())

    def test_polite_decrease_increase_return_keep_unproven_scope_unavailable(self):
        for ending in ('不安が減りませんでした', '不安が減ります',
                       '気持ちメモが増えましたか', '資料が戻りましたと聞いた',
                       '不安が減りましたなら', '友人の不安が減りました',
                       '私の不安が減りました', '気持ち来週メモが増えました',
                       '何が戻りました'):
            with self.subTest(ending=ending):
                self.assertIsNone(self.generate(request(record(
                    memo='私は資料を調べた後、' + ending + '。'))).artifact)
        for memo in ('私は資料を調べた後、不安が減りました？',
                     '友人は資料を調べた後、不安が減りました。',
                     '資料を調べた後、不安が減りました。',
                     '私は資料を調べなかった後、不安が減りました。',
                     '「私は資料を調べた後、不安が減りました」と友人が言った。'):
            with self.subTest(memo=memo):
                self.assertIsNone(self.generate(request(record(memo=memo))).artifact)

    def test_polite_decrease_increase_return_preserve_updates_and_comparison(self):
        old = '私は資料を調べた後、不安が減りました'
        new = '私は記録を残してから、気持ちメモが増えました'
        original = record(memo='私は仕事を続けたい。' + old + '。')
        artifact = self.generate(request(self.with_answer(original,
            '「' + old + '」ではなく「' + new + '」です。'))).artifact
        self.assertEqual([n.visible_label for n in artifact.graph.nodes],
            ['私は仕事を続けたい', '私は記録を残して', '気持ちメモが増えました'])
        withdrawn = self.generate(request(self.with_answer(original,
            '「' + old + '」は取り消します。'))).artifact
        self.assertEqual([n.visible_label for n in withdrawn.graph.nodes], ['私は仕事を続けたい'])
        added = self.generate(request(self.with_answer(record(memo='私は記録を残した。'),
            '私は資料を調べた後、資料が戻りました。'))).artifact
        self.assertEqual(len(added.graph.nodes), 3)
        for polite, plain in (('不安が減りました', '不安が減った'),
                              ('気持ちメモが増えました', '気持ちメモが増えた'),
                              ('資料が戻りました', '資料が戻った')):
            same = self.compared('私は資料を調べた後、' + polite + '。',
                '僕は資料を調べてから、' + plain + '。').artifact
            self.assertEqual(same.period_comparison.change_claims, ())
        changed = self.compared(old.replace('減りました', '増えました') + '。', old + '。').artifact
        self.assertIn('ROUTE_EVIDENCE_CHANGED', changed.safe_projection(
            authenticated_owner_scope=OWNER)['period_comparison']['safe_change_kinds'])

    def test_action_change_pair_does_not_merge_distinct_episodes(self):
        memo = '私は資料を調べた後、疑問が減った。'
        artifact = self.generate(request(record(memo=memo + memo), record(2, memo=memo))).artifact
        self.assertEqual(len(artifact.graph.nodes), 6)
        self.assertEqual(len(artifact.graph.edges), 3)
        self.assertTrue(all(e.edge_kind == 'OBSERVED_ORDER' for e in artifact.graph.edges))
        self.assertEqual([len(n.record_refs) for n in artifact.graph.nodes], [1] * 6)
        self.assertEqual(len({ref for e in artifact.graph.edges for ref in e.endpoint_refs}), 6)

    def test_compound_change_keeps_explicit_outgoing_order_and_source(self):
        for prefix in ('私は資料を調べた後、', '私は資料を調べてから、'):
            for change in ('疑問が減った', '気持ちが変わりました'):
                for marker in ('その後、', 'それから、'):
                    for ending in ('私は記録を残した', '私は記録を残さなかった'):
                        memo = prefix + change + '。' + marker + ending + '。'
                        with self.subTest(memo=memo):
                            req = request(record(memo=memo))
                            artifact = self.generate(req).artifact
                            self.assertEqual(len(artifact.graph.nodes), 3)
                            self.assertEqual([e.endpoint_refs for e in artifact.graph.edges],
                                             [('n1', 'n2'), ('n2', 'n3')])
                            self.assertEqual([len(e.evidence_refs) for e in artifact.graph.edges], [3, 2])
                            self.assertNotIn('EXPLICIT_PREDECESSOR_NOT_ESTABLISHED',
                                {g.reason_code for g in artifact.graph.unknown_gaps})
                            source, = freeze_analysis_sources(req).sources
                            for edge in artifact.graph.edges:
                                for e in edge.evidence_refs:
                                    raw = source.envelope.raw_utf8[e.utf8_start:e.utf8_end]
                                    field = source.envelope.raw_utf8[e.field_utf8_start:e.field_utf8_end].decode()
                                    self.assertEqual(field[e.scalar_start:e.scalar_end], raw.decode())
                                    self.assertEqual(hashlib.sha256(raw).hexdigest(), e.literal_sha256)
                            outgoing = artifact.graph.edges[1]
                            self.assertEqual(outgoing.evidence_refs[0], artifact.graph.nodes[1].evidence_refs[0])
                            self.assertEqual(outgoing.evidence_refs[1], artifact.graph.nodes[2].evidence_refs[0])
                            text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text']
                            self.assertEqual(text.count('記録内の順序：'), 2)
                            self.assertIn('原因を示す線ではありません', text)
                            self.assertNotIn('どの内容に続くのか', text)

    def test_compound_outgoing_order_does_not_bridge_unread_or_separate_sources(self):
        episode = '私は資料を調べてから、疑問が減った。'
        following = 'その後、私は記録を残した。'
        cases = (
            request(record(memo=episode + 'まだ方針を考えている。' + following)),
            request(record(memo=episode + '私は仕事を続けたい。' + following)),
            request(record(memo=episode + following.replace('その後、', ''))),
            request(record(memo=episode, action=following)),
            request(record(memo=episode), record(2, memo=following)),
            request(record(memo='私は資料を調べてから、疑問が減ったかもしれない。' + following)),
            request(record(memo='夢を見た。' + episode + following)),
        )
        for req in cases:
            with self.subTest(records=[r.original_json for r in req.members]):
                result = self.generate(req)
                if result.artifact is not None:
                    graph = result.artifact.graph
                    for edge in graph.edges:
                        target = next(n for n in graph.nodes if n.node_ref == edge.endpoint_refs[1])
                        if edge.edge_kind == 'OBSERVED_ORDER':
                            self.assertEqual(target.node_kind, 'IMMEDIATE_RESULT_OR_AFTERMATH')

    def test_compound_outgoing_order_preserves_updates_and_period_meaning(self):
        old = '私は資料を調べてから、疑問が減った'
        new = '私は資料を調べた後、疑問が増えた'
        following = 'その後、私は記録を残した。'
        original = record(memo=old + '。' + following)
        for answer in ('「' + old + '」は取り消します。',
                       '「' + old + '」ではなく「' + new + '」です。'):
            with self.subTest(answer=answer):
                artifact = self.generate(request(self.with_answer(original, answer))).artifact
                self.assertIn('EXPLICIT_PREDECESSOR_NOT_ESTABLISHED',
                    {g.reason_code for g in artifact.graph.unknown_gaps})
                for edge in artifact.graph.edges:
                    target = next(n for n in artifact.graph.nodes if n.node_ref == edge.endpoint_refs[1])
                    self.assertEqual(target.node_kind, 'IMMEDIATE_RESULT_OR_AFTERMATH')
        answered = self.generate(request(self.with_answer(record(memo='私は仕事を続けたい。'),
            old + '。' + following))).artifact
        self.assertEqual([e.endpoint_refs for e in answered.graph.edges], [('n2', 'n3'), ('n3', 'n4')])
        same = self.compared(old + '。' + following,
            old.replace('調べてから', '調べた後') + '。' + following).artifact
        self.assertEqual(same.period_comparison.change_claims, ())
        changed = self.compared(old + '。' + following,
            old + '。' + following.replace('その後、', '')).artifact
        self.assertIn('ROUTE_EVIDENCE_CHANGED', changed.safe_projection(
            authenticated_owner_scope=OWNER)['period_comparison']['safe_change_kinds'])

    def test_past_feeling_outgoing_order_preserves_experience_and_source(self):
        for prefix in ('私は資料を調べた後、', '私は資料を調べてから、'):
            for feeling in ('安心した', '安心しました', '落ち着いた', '嬉しかった', 'うれしかった'):
                for subject in ('', '私は', '私は、'):
                    marker, action = (('その後、', '私は記録を残した') if subject
                                      else ('それから、', '私は記録を残さなかった'))
                    memo = prefix + subject + feeling + '。' + marker + action + '。'
                    with self.subTest(memo=memo):
                        req = request(record(memo=memo))
                        artifact = self.generate(req).artifact
                        self.assertEqual(len(artifact.graph.nodes), 3)
                        self.assertEqual([e.endpoint_refs for e in artifact.graph.edges],
                                         [('n1', 'n2'), ('n2', 'n3')])
                        emotion = artifact.graph.nodes[1]
                        self.assertEqual((emotion.modality, emotion.temporal_scope,
                            emotion.proposition.result_state, emotion.proposition.actor),
                            ('feeling', 'past', 'PAST_FEELING', 'SELF' if subject else 'UNSPECIFIED'))
                        self.assertEqual([len(e.evidence_refs) for e in artifact.graph.edges], [3, 2])
                        self.assertEqual(artifact.graph.edges[1].evidence_refs[0], emotion.evidence_refs[0])
                        source, = freeze_analysis_sources(req).sources
                        for edge in artifact.graph.edges:
                            for e in edge.evidence_refs:
                                raw = source.envelope.raw_utf8[e.utf8_start:e.utf8_end]
                                field = source.envelope.raw_utf8[e.field_utf8_start:e.field_utf8_end].decode()
                                self.assertEqual(field[e.scalar_start:e.scalar_end], raw.decode())
                                self.assertEqual(hashlib.sha256(raw).hexdigest(), e.literal_sha256)
                        text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text']
                        self.assertIn('（記録された気持ち）', text)
                        self.assertEqual(text.count('記録内の順序：'), 2)
                        self.assertNotIn('どの内容に続くのか', text)
                        self.assertIn('原因を示す線ではありません', text)
                        # An outgoing order must never retype the feeling.
                        broken_node = replace(emotion, modality='fact',
                            proposition=replace(emotion.proposition, modality='fact'))
                        broken = replace(artifact, graph=replace(artifact.graph,
                            nodes=(artifact.graph.nodes[0], broken_node, artifact.graph.nodes[2])))
                        with self.assertRaisesRegex(AnalysisSourceError, 'analysis_safe_surface_unavailable'):
                            broken.safe_projection(authenticated_owner_scope=OWNER)

    def test_past_feeling_outgoing_order_does_not_bridge_or_infer_experience(self):
        episode = '私は資料を調べてから、私は嬉しかった。'
        following = 'その後、私は記録を残した。'
        cases = [request(record(memo=episode + middle + following)) for middle in (
            'まだ方針を考えている。', '私は仕事を続けたい。')]
        cases += [request(record(memo=episode + following.replace('その後、', ''))),
            request(record(memo=episode, action=following)),
            request(record(memo=episode), record(2, memo=following)),
            request(record(memo='嬉しかった。' + following)),
            request(record(memo='友人から聞いた話です。' + episode + following)),
            request(record(memo='夢を見た。' + episode + following))]
        for feeling in ('私は嬉しくなかった', '私は嬉しかったかもしれない',
                        '友人は嬉しかった', '私は落ち着きました'):
            cases.append(request(record(memo='私は資料を調べてから、' + feeling + '。' + following)))
        for req in cases:
            with self.subTest(records=[r.original_json for r in req.members]):
                artifact = self.generate(req).artifact
                if artifact is not None:
                    for edge in artifact.graph.edges:
                        if edge.edge_kind == 'OBSERVED_ORDER':
                            target = next(n for n in artifact.graph.nodes if n.node_ref == edge.endpoint_refs[1])
                            self.assertEqual(target.node_kind, 'IMMEDIATE_RESULT_OR_AFTERMATH')

    def test_past_feeling_outgoing_order_keeps_updates_and_period_meaning(self):
        episode = '私は資料を調べてから、私は嬉しかった'
        following = 'その後、私は記録を残した。'
        original = record(memo=episode + '。' + following)
        for answer in ('「' + episode + '」は取り消します。',
                       '「' + episode + '」ではなく「私は資料を調べた後、安心した」です。'):
            with self.subTest(answer=answer):
                artifact = self.generate(request(self.with_answer(original, answer))).artifact
                self.assertIn('EXPLICIT_PREDECESSOR_NOT_ESTABLISHED',
                    {g.reason_code for g in artifact.graph.unknown_gaps})
                self.assertFalse(any(e.endpoint_refs[1] == 'n1' for e in artifact.graph.edges))
        answered = self.generate(request(self.with_answer(record(memo='私は仕事を続けたい。'),
            episode + '。' + following))).artifact
        self.assertEqual([e.endpoint_refs for e in answered.graph.edges], [('n2', 'n3'), ('n3', 'n4')])
        same = self.compared(episode + '。' + following,
            episode.replace('調べてから', '調べた後') + '。' + following).artifact
        self.assertEqual(same.period_comparison.change_claims, ())
        changed = self.compared(episode + '。' + following,
            episode + '。' + following.replace('その後、', '')).artifact
        self.assertIn('ROUTE_EVIDENCE_CHANGED', changed.safe_projection(
            authenticated_owner_scope=OWNER)['period_comparison']['safe_change_kinds'])

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

    def test_action_change_topic_comma_keeps_whole_episode_and_raw_evidence(self):
        for topic, action, connector, change in (
            ('私は、', '資料を調べて', 'から、', '疑問が減った'),
            ('僕は， ', '記録を残して', 'から、', '気持ちメモが増えました'),
            ('わたしは、　', '考えをノートに書いた', '後、', '資料が戻りました'),
            ('自分は，', '資料を調べて', 'から、', '不安が減りました'),
            ('私は、 ', '資料を調べた', 'あとに、', '不安が増えました'),
            ('僕は、', '資料を調べて', 'から、', '気持ちが変わりました'),
        ):
            with self.subTest(topic=topic, change=change):
                left = topic + action
                episode = left + connector + change
                req = request(record(memo='　' + episode + '。'))
                artifact = self.generate(req).artifact
                self.assertIsNotNone(artifact)
                first, second = artifact.graph.nodes
                self.assertEqual([n.visible_label for n in artifact.graph.nodes],
                                 [left.replace('\u3000', ' '), change])
                self.assertEqual(first.proposition.source_parts[0], ('SELF_TOPIC', 0, len(topic)))
                for node in (first, second):
                    self.assertEqual([i for _, a, b in node.proposition.source_parts for i in range(a, b)],
                                     list(range(len(node.visible_label))))
                self.assertEqual((first.proposition.actor, first.modality, first.temporal_scope),
                                 ('SELF', 'fact', 'past'))
                self.assertEqual((second.proposition.actor, second.modality, second.temporal_scope),
                                 ('UNSPECIFIED', 'fact', 'past'))
                edge, = artifact.graph.edges
                self.assertEqual((edge.edge_kind, edge.endpoint_refs),
                                 ('OBSERVED_ORDER', (first.node_ref, second.node_ref)))
                source, = freeze_analysis_sources(req).sources
                for e, expected in zip(edge.evidence_refs, (left, change, episode), strict=True):
                    raw = source.envelope.raw_utf8[e.utf8_start:e.utf8_end]
                    field = source.envelope.raw_utf8[e.field_utf8_start:e.field_utf8_end].decode()
                    self.assertEqual(raw.decode(), expected)
                    self.assertEqual(field[e.scalar_start:e.scalar_end], expected)
                    self.assertEqual(hashlib.sha256(raw).hexdigest(), e.literal_sha256)
                baseline = self.generate(request(record(memo=re.sub(r'[、，][ \u3000]*$', '', topic)
                    + action + connector + change + '。'))).artifact
                self.assertEqual(artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'],
                                 baseline.safe_text_projection(authenticated_owner_scope=OWNER)['text'])
                if first.proposition.dependent_form == 'TE_BEFORE_PAST_CHANGE':
                    for edges in ((), (replace(edge, evidence_refs=edge.evidence_refs[:2]),),
                                  (replace(edge, endpoint_refs=tuple(reversed(edge.endpoint_refs))),)):
                        with self.assertRaises(AnalysisSourceError):
                            replace(artifact, graph=replace(artifact.graph, edges=edges)).safe_projection(
                                authenticated_owner_scope=OWNER)

    def test_action_change_topic_comma_keeps_past_feeling_scope(self):
        artifact = self.generate(request(record(memo='私は、資料を調べてから、安心した。'))).artifact
        self.assertIsNotNone(artifact)
        first, feeling = artifact.graph.nodes
        self.assertEqual(first.proposition.dependent_form, 'TE_BEFORE_PAST_CHANGE')
        self.assertEqual((feeling.proposition.result_state, feeling.proposition.actor,
                          feeling.modality, feeling.temporal_scope),
                         ('PAST_FEELING', 'UNSPECIFIED', 'feeling', 'past'))
        self.assertFalse(artifact.graph.annotations)
        text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text']
        self.assertIn('安心した（記録された気持ち）', text)
        self.assertIn('原因を示す線ではありません', text)

    def test_action_change_topic_comma_keeps_updates_and_semantic_comparison(self):
        old = '私は、資料を調べてから、不安が減りました'
        new = '僕は，　記録を残してから、資料が戻りました'
        original = record(memo='私は仕事を続けたい。' + old + '。')
        for answer in (new + '。', '「' + old + '」ではなく「' + new + '」です。'):
            with self.subTest(answer=answer):
                req = request(self.with_answer(original, answer))
                artifact = self.generate(req).artifact
                self.assertIsNotNone(artifact)
                source = next(s.envelope for s in freeze_analysis_sources(req).sources
                              if s.envelope.source_role == 'SUPPLEMENTAL_ANSWER')
                edge = next(e for e in artifact.graph.edges
                            if e.evidence_refs[-1].source_envelope_id == source.envelope_id)
                whole = edge.evidence_refs[-1]
                self.assertEqual(source.raw_utf8[whole.utf8_start:whole.utf8_end].decode(), new)
                artifact.safe_projection(authenticated_owner_scope=OWNER)
        withdrawn = self.generate(request(self.with_answer(original,
            '「' + old + '」は取り消します。'))).artifact
        self.assertEqual([n.visible_label for n in withdrawn.graph.nodes], ['私は仕事を続けたい'])
        self.assertFalse(withdrawn.graph.edges)
        partial = self.generate(request(self.with_answer(original, '「私は、資料を調べて」は取り消します。')))
        self.assertIsNone(partial.artifact)
        same = self.compared(old + '。', '私は資料を調べた後、不安が減った。').artifact
        self.assertEqual(same.period_comparison.change_claims, ())
        changed = self.compared(old.replace('減りました', '増えました') + '。', old + '。').artifact
        self.assertIn('ROUTE_EVIDENCE_CHANGED', changed.safe_projection(
            authenticated_owner_scope=OWNER)['period_comparison']['safe_change_kinds'])

    def test_action_change_topic_comma_does_not_skip_unread_scope(self):
        for memo in (
            '私は、、資料を調べてから、疑問が減った。',
            '私は、\t資料を調べてから、疑問が減った。',
            '私は、\n資料を調べてから、疑問が減った。',
            '私は、明日資料を調べてから、不安が減りました。',
            '友人は、資料を調べてから、不安が減りました。',
            '私は、友人が資料を調べてから、不安が減りました。',
            '私は、資料を調べなかった後、不安が減りました。',
            '私は、資料を調べてから、不安が減りましたと聞いた。',
            '私は、資料を調べてから、不安が減りました？',
            '「私は、資料を調べてから、不安が減りました」と友人が言った。',
            '私は、資料を調べて。',
        ):
            with self.subTest(memo=memo):
                self.assertIsNone(self.generate(request(record(memo=memo))).artifact)

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

        # An unparsed wish is unknown, not a raw private node whose safe
        # projection would also block independently readable content.
        wish = self.generate(request(record(memo='私は資料を調べてから、疑問を減らしたい。')))
        self.assertEqual(wish.status, EngineStatus.UNAVAILABLE)
        self.assertIsNone(wish.artifact)

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

    def test_feeling_topic_comma_preserves_whole_source_and_experienced_state(self):
        for action, topic, feeling, lemma in (
            ('私は資料を調べた後、', '私は、', '安心しました', '安心する'),
            ('私は、資料を調べてから、', '僕は， ', '落ち着いた', '落ち着く'),
            ('私は記録を残したあとに、', 'わたしは、　', '嬉しかった', '嬉しい'),
            ('私は資料を調べてから、', '自分は，', 'うれしかった', 'うれしい'),
        ):
            with self.subTest(topic=topic, feeling=feeling):
                episode = action + topic + feeling
                req = request(record(memo='　' + episode + '。'))
                artifact = self.generate(req).artifact
                self.assertIsNotNone(artifact)
                first, second = artifact.graph.nodes
                p = second.proposition
                self.assertEqual((p.actor, p.result_state, p.predicate_lemma,
                    second.polarity, second.modality, second.temporal_scope),
                    ('SELF', 'PAST_FEELING', lemma, 'positive', 'feeling', 'past'))
                self.assertEqual(p.source_parts, (('SELF_TOPIC', 0, len(topic)),
                    ('FINITE_FEELING', len(topic), len(topic + feeling))))
                edge, = artifact.graph.edges
                self.assertEqual((edge.edge_kind, edge.endpoint_refs),
                    ('OBSERVED_ORDER', (first.node_ref, second.node_ref)))
                source, = freeze_analysis_sources(req).sources
                for evidence, literal in ((second.evidence_refs[0], topic + feeling),
                                          (edge.evidence_refs[-1], episode)):
                    raw = source.envelope.raw_utf8[evidence.utf8_start:evidence.utf8_end]
                    field = source.envelope.raw_utf8[evidence.field_utf8_start:evidence.field_utf8_end].decode()
                    self.assertEqual(raw.decode(), literal)
                    self.assertEqual(field[evidence.scalar_start:evidence.scalar_end], literal)
                    self.assertEqual(hashlib.sha256(raw).hexdigest(), evidence.literal_sha256)
                plain = re.sub(r'[、，][ \u3000]*$', '', topic)
                baseline = self.generate(request(record(memo=action + plain + feeling + '。'))).artifact
                text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text']
                self.assertEqual(text, baseline.safe_text_projection(authenticated_owner_scope=OWNER)['text'])
                self.assertIn('（記録された気持ち）', text)
                self.assertIn('原因を示す線ではありません', text)
                for changes in ({'actor': 'UNSPECIFIED'}, {'predicate_lemma': '安心する' if lemma != '安心する' else '落ち着く'},
                                {'modality': 'fact'}, {'source_parts': p.source_parts[1:]}):
                    forged = replace(second, proposition=replace(p, **changes))
                    with self.assertRaises(AnalysisSourceError):
                        replace(artifact, graph=replace(artifact.graph, nodes=(first, forged))).safe_projection(
                            authenticated_owner_scope=OWNER)

    def test_feeling_topic_comma_keeps_updates_and_semantic_comparison(self):
        old = '私は資料を調べた後、私は、安心しました'
        new = '私は記録を残してから、僕は， 落ち着いた'
        base = record(memo='私は仕事を続けたい。' + old + '。')
        for answer, count in ((new + '。', 2), ('「' + old + '」ではなく「' + new + '」です。', 1)):
            with self.subTest(answer=answer):
                req = request(self.with_answer(base, answer))
                artifact = self.generate(req).artifact
                self.assertIsNotNone(artifact)
                self.assertEqual(len(artifact.graph.edges), count)
                node = next(n for n in artifact.graph.nodes if n.proposition.predicate_lemma == '落ち着く')
                source = next(s.envelope for s in freeze_analysis_sources(req).sources
                              if s.envelope.source_role == 'SUPPLEMENTAL_ANSWER')
                for e in node.evidence_refs:
                    self.assertEqual(e.source_envelope_id, source.envelope_id)
                    self.assertEqual(source.raw_utf8[e.utf8_start:e.utf8_end].decode(), '僕は， 落ち着いた')
                artifact.safe_projection(authenticated_owner_scope=OWNER)
        withdrawn = self.generate(request(self.with_answer(base, '「' + old + '」は取り消します。'))).artifact
        self.assertEqual([n.visible_label for n in withdrawn.graph.nodes], ['私は仕事を続けたい'])
        self.assertFalse(withdrawn.graph.edges)
        for answer in ('「私は、安心しました」は取り消します。', new + '。別の意味です。'):
            self.assertIsNone(self.generate(request(self.with_answer(base, answer))).artifact)
        same = self.compared(old + '。', '私は資料を調べた後、私は安心した。').artifact
        self.assertEqual(same.period_comparison.change_claims, ())
        changed = self.compared(old.replace('安心しました', '落ち着いた') + '。', old + '。').artifact
        self.assertEqual(changed.safe_projection(authenticated_owner_scope=OWNER)['period_comparison']
                         ['safe_change_kinds'], ['ROUTE_EVIDENCE_CHANGED'])

    def test_feeling_topic_comma_keeps_unsupported_scope_pending(self):
        for ending in ('私は、、安心した', '私は、\t安心した', '私は、\n安心した',
                       '私は、今日安心した', '私は、明日安心した', '友人は、安心した',
                       '私は、友人が安心した', '私は、安心しなかった', '私は、安心したい',
                       '私は、安心したかもしれない', '私は、落ち着きました', '私は、嬉しかったです',
                       '私は、安心した？', '私は、安心したと聞いた', '私は、安心したという夢を見た'):
            with self.subTest(ending=ending):
                self.assertIsNone(self.generate(request(record(memo='私は資料を調べた後、' + ending + '。'))).artifact)
        standalone = self.generate(request(record(memo='私は、安心しました。'))).artifact
        self.assertEqual(standalone.graph.nodes[0].proposition.result_state, 'PAST_FEELING')
        partial = self.generate(request(record(memo='私は記録を残した。私は、安心しました。'))).artifact
        self.assertEqual([n.visible_label for n in partial.graph.nodes], ['私は記録を残した', '私は、安心しました'])
        self.assertFalse(partial.graph.edges)
        self.assertNotIn('SOURCE_SCOPE', [g.missing_scope for g in partial.graph.unknown_gaps])

    def test_past_feeling_spelling_alone_is_not_a_period_change(self):
        for topic in ('', '私は、'):
            kanji = '私は資料を調べた後、' + topic + '嬉しかった。'
            kana = kanji.replace('嬉しかった', 'うれしかった')
            for before, now in ((kanji, kana), (kana, kanji)):
                with self.subTest(before=before, now=now):
                    result = self.compared(now, before)
                    self.assertEqual(result.status, EngineStatus.GENERATED)
                    artifact = result.artifact
                    self.assertEqual(artifact.period_comparison.change_claims, ())
                    visual = artifact.safe_projection(authenticated_owner_scope=OWNER)
                    self.assertEqual(visual['period_comparison'], {'state': 'COMPARABLE',
                        'reason_codes': [], 'safe_change_kinds': []})
                    text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text']
                    self.assertIn('今回比較した記述内容では差分を検出していません', text)
                    spelling = 'うれしかった' if 'うれしかった' in now else '嬉しかった'
                    self.assertIn(spelling + '（記録された気持ち）', text)

    def test_past_feeling_spelling_keeps_meaning_differences_and_episode_evidence(self):
        kanji = '私は資料を調べた後、嬉しかった。'
        kana = kanji.replace('嬉しかった', 'うれしかった')
        for now in (kana.replace('うれしかった', '安心した'),
                    kana.replace('うれしかった', '落ち着いた'),
                    kana.replace('、うれしかった', '、私はうれしかった'),
                    kana.replace('資料を調べた後', '記録を残した後')):
            with self.subTest(now=now):
                artifact = self.compared(now, kanji).artifact
                self.assertEqual(artifact.safe_projection(authenticated_owner_scope=OWNER)
                    ['period_comparison']['safe_change_kinds'], ['ROUTE_EVIDENCE_CHANGED'])
        req = request(record(memo=kanji), record(2, memo=kana))
        artifact = self.generate(req).artifact
        self.assertEqual((len(artifact.graph.nodes), len(artifact.graph.edges)), (4, 2))
        self.assertEqual(len({ref for edge in artifact.graph.edges for ref in edge.endpoint_refs}), 4)
        sources = {s.envelope.envelope_id: s.envelope for s in freeze_analysis_sources(req).sources}
        feelings = [n for n in artifact.graph.nodes if n.proposition.result_state == 'PAST_FEELING']
        self.assertEqual([n.proposition.predicate_lemma for n in feelings], ['嬉しい', 'うれしい'])
        for node, literal in zip(feelings, ('嬉しかった', 'うれしかった')):
            p = node.proposition
            self.assertEqual((p.actor, p.polarity, p.modality, p.temporal_scope),
                             ('UNSPECIFIED', 'positive', 'feeling', 'past'))
            e, = node.evidence_refs
            source = sources[e.source_envelope_id]
            raw = source.raw_utf8[e.utf8_start:e.utf8_end]
            field = source.raw_utf8[e.field_utf8_start:e.field_utf8_end].decode()
            self.assertEqual(raw.decode(), literal)
            self.assertEqual(field[e.scalar_start:e.scalar_end], literal)
            self.assertEqual(hashlib.sha256(raw).hexdigest(), e.literal_sha256)
            edge, = [edge for edge in artifact.graph.edges if edge.endpoint_refs[-1] == node.node_ref]
            self.assertEqual(edge.edge_kind, 'OBSERVED_ORDER')
        artifact.safe_projection(authenticated_owner_scope=OWNER)
        for node in feelings:
            forged = replace(node, proposition=replace(node.proposition,
                predicate_lemma='うれしい' if node.proposition.predicate_lemma == '嬉しい' else '嬉しい'))
            with self.assertRaises(AnalysisSourceError):
                replace(artifact, graph=replace(artifact.graph, nodes=tuple(
                    forged if n.node_ref == node.node_ref else n for n in artifact.graph.nodes))).safe_projection(
                        authenticated_owner_scope=OWNER)

    def test_past_feeling_requires_shared_pair_and_matching_modality(self):
        from cocolon_meaning_experience_engine.cores.analysis import intent_compiler as compiler
        original_builder = compiler.build_final_stage1_grounded_observation_plan
        for memo in ('私は資料を調べた後、安心した。', '私は資料を調べてから、落ち着いた。',
                     '私は資料を調べた後、私は、安心しました。'):
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
        for memo in ('安心した。', '落ち着いた。',
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

    def test_late_past_scene_keeps_evidence_and_does_not_depend_on_sentence_position(self):
        context = '私は会議を担当した。私は資料を調べた。私は記録を残した。'
        for scene, polarity, day in (
                ('私は職場にいた', 'positive', ''),
                ('俺は、家族の良い職場にいました', 'positive', ''),
                ('私は昨日、図書館にいなかったです', 'negative', 'YESTERDAY'),
                ('僕は今日職場にいませんでした', 'negative', 'TODAY')):
            with self.subTest(scene=scene):
                req = request(record(memo=context + scene + '。'))
                artifact = self.generate(req).artifact
                self.assertIsNotNone(artifact)
                scenes = [n for n in artifact.graph.nodes if n.node_kind == 'SCENE']
                self.assertEqual(len(scenes), 1)
                node, = scenes
                self.assertEqual((node.polarity, node.temporal_scope, node.proposition.relative_day),
                                 (polarity, 'past', day))
                self.assertEqual(node.proposition.actor, 'SELF')
                evidence, = node.evidence_refs
                envelope = freeze_analysis_sources(req).sources[0].envelope
                raw = envelope.raw_utf8[evidence.utf8_start:evidence.utf8_end]
                field = envelope.raw_utf8[evidence.field_utf8_start:evidence.field_utf8_end].decode()
                self.assertEqual(raw.decode(), scene)
                self.assertEqual(field[evidence.scalar_start:evidence.scalar_end], scene)
                self.assertEqual(hashlib.sha256(raw).hexdigest(), evidence.literal_sha256)
                self.assertFalse(artifact.graph.edges)
                self.assertNotIn('SCENE', {g.missing_scope for g in artifact.graph.unknown_gaps})
                self.assertNotIn('SOURCE_SCOPE', {g.missing_scope for g in artifact.graph.unknown_gaps})
                front = self.generate(request(record(memo=scene + '。' + context))).artifact
                self.assertEqual(artifact.safe_projection(authenticated_owner_scope=OWNER)['nodes'][-1]['visible_label'],
                    front.safe_projection(authenticated_owner_scope=OWNER)['nodes'][0]['visible_label'])
                compared = self.compared(context + scene + '。', scene + '。' + context).artifact
                self.assertEqual(compared.period_comparison.change_claims, ())

    def test_late_past_scene_preserves_order_updates_and_opposed_claims(self):
        context = '私は会議を担当した。私は資料を調べた。私は記録を残した。'
        old, new = '私は職場にいた', '私は図書館にいませんでした'
        base = record(memo=context + old + '。')
        for answer, expected in ((new + '。', ('positive', 'negative')),
                ('「' + old + '」ではなく「' + new + '」です。', ('negative',)),
                ('「' + old + '」は取り消します。', ())):
            with self.subTest(answer=answer):
                artifact = self.generate(request(self.with_answer(base, answer))).artifact
                self.assertIsNotNone(artifact)
                self.assertEqual(tuple(n.polarity for n in artifact.graph.nodes if n.node_kind == 'SCENE'), expected)
                artifact.safe_projection(authenticated_owner_scope=OWNER)
        supplemented = self.generate(request(self.with_answer(record(memo='私は仕事を続けたい。'),
            context + old + '。'))).artifact
        self.assertIsNotNone(supplemented)
        self.assertEqual(len([n for n in supplemented.graph.nodes if n.node_kind == 'SCENE']), 1)
        ordered = self.generate(request(record(memo=context + 'その後、' + old + '。'))).artifact
        edge, = ordered.graph.edges
        self.assertEqual((edge.edge_kind, edge.endpoint_refs), ('OBSERVED_ORDER', ('n3', 'n4')))
        self.assertIn('その後：職場にいた', ordered.safe_text_projection(authenticated_owner_scope=OWNER)['text'])
        opposed = self.generate(request(record(memo=context + old + '。私は職場にいなかった。'))).artifact
        self.assertEqual({n.polarity for n in opposed.graph.nodes if n.node_kind == 'SCENE'}, {'positive', 'negative'})
        self.assertEqual(len(opposed.graph.conflicts), 1)
        changed = self.compared(context + '私は職場にいなかった。', context + old + '。').artifact
        self.assertIn('ROUTE_EVIDENCE_CHANGED', changed.safe_projection(
            authenticated_owner_scope=OWNER)['period_comparison']['safe_change_kinds'])

    def test_late_past_scene_still_requires_complete_explicit_shared_witness(self):
        from cocolon_meaning_experience_engine.cores.analysis import intent_compiler as compiler
        build = compiler.build_final_stage1_grounded_observation_plan
        context = '私は会議を担当した。私は資料を調べた。私は記録を残した。'
        for mismatch in ('retention', 'grounding', 'scope', 'actor', 'modality', 'time', 'polarity', 'fragment'):
            def altered(*args, **kwargs):
                plan = build(*args, **kwargs)
                n = plan.nuclei[-1]
                self.assertEqual(n.retention, 'should')
                changes = {'retention': {'retention': 'optional'},
                    'grounding': {'grounding_kind': 'interpretive_hypothesis'},
                    'scope': {'allowed_claim_scope': 'unknown'}}
                frames = {'actor': {'actor': 'other'}, 'modality': {'modality': 'wish'},
                    'time': {'time_scope': 'future'}, 'polarity': {'polarity': 'negative'},
                    'fragment': {'attribute_codes': n.semantic_frame.attribute_codes + ('semantic_dependency:unknown',)}}
                n = replace(n, **changes[mismatch]) if mismatch in changes else replace(
                    n, semantic_frame=replace(n.semantic_frame, **frames[mismatch]))
                return replace(plan, nuclei=plan.nuclei[:-1] + (n,))
            with self.subTest(mismatch=mismatch), patch.object(
                    compiler, 'build_final_stage1_grounded_observation_plan', side_effect=altered):
                artifact = self.generate(request(record(memo=context + '私は職場にいた。'))).artifact
                self.assertIsNotNone(artifact)
                self.assertFalse(any(n.node_kind == 'SCENE' for n in artifact.graph.nodes))
                self.assertIn('SOURCE_SCOPE', {g.missing_scope for g in artifact.graph.unknown_gaps})
        for scene in ('友人は職場にいた', '私は職場にいたい', '私は職場にいたかもしれない',
                      '私は職場にいたと聞いた', '夢を見た。私は職場にいた', '私は職場にいた？'):
            with self.subTest(scene=scene):
                artifact = self.generate(request(record(memo=context + scene + '。'))).artifact
                self.assertFalse(artifact and any(n.node_kind == 'SCENE' for n in artifact.graph.nodes))

    def test_explicit_past_presence_is_a_scene_with_exact_whole_clause_evidence(self):
        for subject, noun in (('私', '職場'), ('僕', '会議の会場'),
                              ('わたし', '図書館'), ('自分', 'オフィス'),
                              ('私', '悪い職場'), ('ぼく', '家族の悪い職場'),
                              ('自分', '悪い会社の新しい職場'),
                              ('私', '良い職場'), ('ぼく', '家族の良い職場'),
                              ('自分', '良い会社の新しい職場'), ('私', '良い会社の良い職場')):
            for ending, polarity in (('いた', 'positive'), ('いました', 'positive'),
                                     ('いなかった', 'negative'), ('いなかったです', 'negative'),
                                     ('いませんでした', 'negative')):
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

    def test_bad_scene_keeps_updates_comparison_order_and_modifier_scope(self):
        old, new = '私は悪い職場にいた', '私は家族の悪い職場にいませんでした'
        base = record(memo=old + '。私は資料を調べた。')
        for answer, expected in ((new + '。', ('positive', 'negative')),
                ('「' + old + '」ではなく「' + new + '」です。', ('negative',)),
                ('「' + old + '」は取り消します。', ())):
            with self.subTest(answer=answer):
                artifact = self.generate(request(self.with_answer(base, answer))).artifact
                self.assertIsNotNone(artifact)
                scenes = [n for n in artifact.graph.nodes if n.node_kind == 'SCENE']
                self.assertEqual(tuple(n.polarity for n in scenes), expected)
                artifact.safe_projection(authenticated_owner_scope=OWNER)
        self.assertIsNone(self.generate(request(self.with_answer(base,
            '「悪い職場にいた」は取り消します。'))).artifact)
        memo = '私は昨日、悪い職場にいた。その後、私は資料を調べた。'
        artifact = self.generate(request(record(memo=memo))).artifact
        scene, action = artifact.graph.nodes
        self.assertEqual(scene.proposition.relative_day, 'YESTERDAY')
        self.assertEqual([(e.edge_kind, e.endpoint_refs) for e in artifact.graph.edges],
                         [('OBSERVED_ORDER', (scene.node_ref, action.node_ref))])
        merged = self.generate(request(record(memo=old + '。'),
            record(2, memo='ぼくは悪い職場にいました。'))).artifact
        node, = merged.graph.nodes
        self.assertEqual((len(node.record_refs), len(node.evidence_refs)), (2, 2))
        for now in ('ぼくは悪い職場にいました。', '私は悪い職場にいなかった。',
                    '私は職場にいた。', '私は悪い会社の職場にいた。'):
            with self.subTest(now=now):
                changed = self.compared(now, old + '。').artifact.safe_projection(
                    authenticated_owner_scope=OWNER)['period_comparison']['safe_change_kinds']
                self.assertEqual('ROUTE_EVIDENCE_CHANGED' in changed, not now.startswith('ぼく'))
        original = self.generate(request(record(memo='私は家族の悪い職場にいた。'))).artifact
        node, = original.graph.nodes
        for noun in ('家族の職場', '家族の良い職場', '悪い家族の職場'):
            with self.subTest(noun=noun), self.assertRaises(AnalysisSourceError):
                forged = replace(node, proposition=replace(node.proposition, arguments=(('に', noun),)))
                replace(original, graph=replace(original.graph, nodes=(forged,))).safe_projection(
                    authenticated_owner_scope=OWNER)
        for text in ('私は悪い職場にいたい。', '私は悪い職場にいたと思う。',
                     '私は悪い職場にいたと聞いた。', '私は悪い職場にいた？',
                     '友人は悪い職場にいた。', '夢を見た。私は悪い職場にいた。'):
            with self.subTest(text=text):
                self.assertIsNone(self.generate(request(record(memo=text))).artifact)

    def test_good_scene_keeps_updates_comparison_order_and_modifier_scope(self):
        old, new = '私は良い職場にいた', '私は家族の良い職場にいませんでした'
        base = record(memo=old + '。私は資料を調べた。')
        for answer, expected in ((new + '。', ('positive', 'negative')),
                ('「' + old + '」ではなく「' + new + '」です。', ('negative',)),
                ('「' + old + '」は取り消します。', ())):
            with self.subTest(answer=answer):
                artifact = self.generate(request(self.with_answer(base, answer))).artifact
                self.assertIsNotNone(artifact)
                scenes = [n for n in artifact.graph.nodes if n.node_kind == 'SCENE']
                self.assertEqual(tuple(n.polarity for n in scenes), expected)
                artifact.safe_projection(authenticated_owner_scope=OWNER)
        self.assertIsNone(self.generate(request(self.with_answer(base,
            '「良い職場にいた」は取り消します。'))).artifact)
        memo = '私は昨日、良い職場にいた。その後、私は資料を調べた。'
        artifact = self.generate(request(record(memo=memo))).artifact
        scene, action = artifact.graph.nodes
        self.assertEqual(scene.proposition.relative_day, 'YESTERDAY')
        self.assertEqual([(e.edge_kind, e.endpoint_refs) for e in artifact.graph.edges],
                         [('OBSERVED_ORDER', (scene.node_ref, action.node_ref))])
        merged = self.generate(request(record(memo=old + '。'),
            record(2, memo='ぼくは良い職場にいました。'))).artifact
        node, = merged.graph.nodes
        self.assertEqual((len(node.record_refs), len(node.evidence_refs)), (2, 2))
        for now in ('ぼくは良い職場にいました。', '私は良い職場にいなかった。',
                    '私は職場にいた。', '私は良い会社の職場にいた。'):
            with self.subTest(now=now):
                changed = self.compared(now, old + '。').artifact.safe_projection(
                    authenticated_owner_scope=OWNER)['period_comparison']['safe_change_kinds']
                self.assertEqual('ROUTE_EVIDENCE_CHANGED' in changed, not now.startswith('ぼく'))
        original = self.generate(request(record(memo='私は家族の良い職場にいた。'))).artifact
        node, = original.graph.nodes
        for noun in ('家族の職場', '家族の悪い職場', '良い家族の職場'):
            with self.subTest(noun=noun), self.assertRaises(AnalysisSourceError):
                forged = replace(node, proposition=replace(node.proposition, arguments=(('に', noun),)))
                replace(original, graph=replace(original.graph, nodes=(forged,))).safe_projection(
                    authenticated_owner_scope=OWNER)
        for text in ('私は良い職場にいたい。', '私は良い職場にいたと思う。',
                     '私は良い職場にいたと聞いた。', '私は良い職場にいた？',
                     '友人は良い職場にいた。', '夢を見た。私は良い職場にいた。'):
            with self.subTest(text=text):
                self.assertIsNone(self.generate(request(record(memo=text))).artifact)

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

    def test_difficult_nominals_keep_past_role_scene_and_exact_source(self):
        for kind, case, endings in (
                ('ROLE', 'を', ('担当した', '担当しました', '担当しなかった', '担当しなかったです', '担当しませんでした')),
                ('SCENE', 'に', ('いた', 'いました', 'いなかった', 'いなかったです', 'いませんでした'))):
            for noun in ('難しい会議', '家族の難しい会議', '難しい会社の難しい会議'):
                for ending in endings:
                    literal = '私は、昨日、' + noun + case + ending
                    with self.subTest(literal=literal):
                        req = request(record(memo=literal + '。'))
                        artifact = self.generate(req).artifact
                        self.assertIsNotNone(artifact)
                        node, = artifact.graph.nodes
                        negative = 'なかった' in ending or 'ません' in ending
                        self.assertEqual((node.node_kind, node.polarity, node.modality, node.temporal_scope),
                            (kind, 'negative' if negative else 'positive', 'fact', 'past'))
                        self.assertEqual(node.proposition.arguments, ((case, noun),))
                        self.assertEqual(node.proposition.relative_day, 'YESTERDAY')
                        source, = freeze_analysis_sources(req).sources
                        e, = node.evidence_refs
                        raw = source.envelope.raw_utf8[e.utf8_start:e.utf8_end]
                        field = source.envelope.raw_utf8[e.field_utf8_start:e.field_utf8_end].decode()
                        self.assertEqual((raw.decode(), field[e.scalar_start:e.scalar_end]), (literal, literal))
                        self.assertEqual(hashlib.sha256(raw).hexdigest(), e.literal_sha256)
                        text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text']
                        self.assertIn(noun + case, text)
                        self.assertNotIn('実行済み', text)
                        self.assertFalse(artifact.graph.edges)
                        with self.assertRaises(AnalysisSourceError):
                            replace(artifact, graph=replace(artifact.graph, nodes=(replace(node,
                                proposition=replace(node.proposition, arguments=((case, noun.replace('難しい', '易しい')),))),))).safe_projection(
                                    authenticated_owner_scope=OWNER)

    def test_difficult_nominals_keep_updates_order_comparison_and_boundaries(self):
        old, new = '私は難しい会議を担当した', '私は家族の難しい会議を担当しなかった'
        base = record(memo=old + '。その後、私は資料を調べた。')
        self.assertIsNone(self.generate(request(self.with_answer(base,
            '私は難しい会議を担当しなかった。'))).artifact)
        for answer, expected in ((new + '。', ('positive', 'negative')),
                ('「' + old + '」ではなく「' + new + '」です。', ('negative',)),
                ('「' + old + '」は取り消します。', ())):
            with self.subTest(answer=answer):
                artifact = self.generate(request(self.with_answer(base, answer))).artifact
                self.assertIsNotNone(artifact)
                self.assertEqual(tuple(n.polarity for n in artifact.graph.nodes if n.node_kind == 'ROLE'), expected)
                self.assertEqual(len(artifact.graph.edges), 1 if answer == new + '。' else 0)
                artifact.safe_projection(authenticated_owner_scope=OWNER)
        route = self.generate(request(record(memo='私は難しい職場にいた。'
            'その後、私は難しい会議を担当した。それから、私は資料を調べた。'))).artifact
        self.assertIsNotNone(route)
        self.assertEqual([n.node_kind for n in route.graph.nodes], ['SCENE', 'ROLE', 'ACTION_OR_NONACTION'])
        self.assertEqual([e.endpoint_refs for e in route.graph.edges], [('n1', 'n2'), ('n2', 'n3')])
        route.safe_projection(authenticated_owner_scope=OWNER)
        for now, changed in (('ぼくは難しい会議を担当しました。', False),
                             ('私は易しい会議を担当した。', True), (new + '。', True)):
            with self.subTest(now=now):
                comparison = self.compared(now, old + '。').artifact
                self.assertIsNotNone(comparison)
                kinds = comparison.safe_projection(authenticated_owner_scope=OWNER)['period_comparison']['safe_change_kinds']
                self.assertEqual('ROUTE_EVIDENCE_CHANGED' in kinds, changed)
        for clause in ('難しい会議を担当した', '難しい職場にいた'):
            for memo in ('私は' + clause + 'と思う。', '私は' + clause + 'と聞いた。',
                         '私は' + clause + '？', '友人は' + clause + '。',
                         '夢を見た。私は' + clause + '。', '私は' + clause + 'なら。'):
                with self.subTest(memo=memo):
                    self.assertIsNone(self.generate(request(record(memo=memo))).artifact)

    def test_good_responsibility_keeps_nominal_modifier_and_complete_role_evidence(self):
        for noun in ('良い会議', '家族の良い会議', '良い会社の新しい会議', '良い記録'):
            for ending in ('担当した', '担当しました', '担当しなかった',
                           '担当しなかったです', '担当しませんでした'):
                literal = '私は' + noun + 'を' + ending
                with self.subTest(literal=literal):
                    req = request(record(memo=literal + '。'))
                    artifact = self.generate(req).artifact
                    self.assertIsNotNone(artifact)
                    node, = artifact.graph.nodes
                    negative = ending.startswith(('担当しなかった', '担当しません'))
                    self.assertEqual((node.node_kind, node.proposition.role_state, node.proposition.actor),
                                     ('ROLE', 'PAST_RESPONSIBILITY', 'SELF'))
                    self.assertEqual((node.polarity, node.modality, node.temporal_scope),
                                     ('negative' if negative else 'positive', 'fact', 'past'))
                    self.assertEqual(node.proposition.arguments, (('を', noun),))
                    source, = freeze_analysis_sources(req).sources
                    e, = node.evidence_refs
                    raw = source.envelope.raw_utf8[e.utf8_start:e.utf8_end]
                    field = source.envelope.raw_utf8[e.field_utf8_start:e.field_utf8_end].decode()
                    self.assertEqual((raw.decode(), field[e.scalar_start:e.scalar_end]), (literal, literal))
                    self.assertEqual(hashlib.sha256(raw).hexdigest(), e.literal_sha256)
                    label = noun + 'を' + ('担当しなかった' if negative else '担当した') + '（記録された担当）'
                    self.assertEqual(artifact.safe_projection(authenticated_owner_scope=OWNER)['nodes'][0]['visible_label'], label)
                    text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text']
                    self.assertIn(label, text)
                    self.assertNotIn('実行済み', text)
                    self.assertFalse(artifact.graph.edges)
                    for altered in (noun.replace('良い', ''), noun.replace('良い', '悪い')):
                        with self.assertRaises(AnalysisSourceError):
                            replace(artifact, graph=replace(artifact.graph, nodes=(replace(node,
                                proposition=replace(node.proposition, arguments=(('を', altered),))),))).safe_projection(
                                    authenticated_owner_scope=OWNER)

    def test_good_responsibility_keeps_updates_order_comparison_and_unread_boundaries(self):
        old, new = '私は良い会議を担当した', '私は家族の良い会議を担当しませんでした'
        base = record(memo=old + '。その後、私は資料を調べた。')
        for answer, polarities in ((new + '。', ('positive', 'negative')),
                ('「' + old + '」ではなく「' + new + '」です。', ('negative',)),
                ('「' + old + '」は取り消します。', ())):
            with self.subTest(answer=answer):
                artifact = self.generate(request(self.with_answer(base, answer))).artifact
                self.assertIsNotNone(artifact)
                roles = [n for n in artifact.graph.nodes if n.node_kind == 'ROLE']
                self.assertEqual(tuple(n.polarity for n in roles), polarities)
                self.assertEqual(len(artifact.graph.edges), 1 if answer == new + '。' else 0)
                artifact.safe_projection(authenticated_owner_scope=OWNER)
        self.assertIsNone(self.generate(request(self.with_answer(base,
            '「良い会議を担当した」は取り消します。'))).artifact)
        route = self.generate(request(record(memo='私は昨日、良い職場にいた。'
            'その後、私は良い会議を担当した。それから、私は資料を調べた。'))).artifact
        self.assertEqual([n.node_kind for n in route.graph.nodes], ['SCENE', 'ROLE', 'ACTION_OR_NONACTION'])
        self.assertEqual([e.endpoint_refs for e in route.graph.edges], [('n1', 'n2'), ('n2', 'n3')])
        route.safe_projection(authenticated_owner_scope=OWNER)
        repeated = self.generate(request(record(memo=old + '。'),
            record(2, memo='ぼくは良い会議を担当しました。'))).artifact
        node, = repeated.graph.nodes
        self.assertEqual((len(node.record_refs), len(node.evidence_refs)), (2, 2))
        for now in ('ぼくは良い会議を担当しました。', '私は会議を担当した。',
                    '私は悪い会議を担当した。', '私は良い会議を担当しなかった。'):
            with self.subTest(now=now):
                changed = self.compared(now, old + '。').artifact.safe_projection(
                    authenticated_owner_scope=OWNER)['period_comparison']['safe_change_kinds']
                self.assertEqual('ROUTE_EVIDENCE_CHANGED' in changed, not now.startswith('ぼく'))
        for memo in ('私は良い会議を担当したい。', '私は良い会議を担当したと思う。',
                     '私は良い会議を担当したと聞いた。', '私は良い会議を担当した？',
                     '私は良い会議に担当した。', '友人は良い会議を担当した。',
                     '夢を見た。私は良い会議を担当した。', '私は良い会議を担当したなら。'):
            with self.subTest(memo=memo):
                self.assertIsNone(self.generate(request(record(memo=memo))).artifact)

    def test_keyword_action_responsibility_preserves_role_and_whole_source(self):
        for noun in ('記録', 'メモ', '仕事メモ', '会議の記録'):
            for ending in ('担当した', '担当しました', '担当しなかった',
                           '担当しなかったです', '担当しませんでした'):
                literal = '私は' + noun + 'を' + ending
                with self.subTest(literal=literal):
                    req = request(record(memo=literal + '。'))
                    artifact = self.generate(req).artifact
                    self.assertIsNotNone(artifact)
                    node, = artifact.graph.nodes
                    negative = ending.startswith(('担当しなかった', '担当しません'))
                    self.assertEqual((node.node_kind, node.proposition.role_state, node.proposition.actor),
                                     ('ROLE', 'PAST_RESPONSIBILITY', 'SELF'))
                    self.assertEqual((node.polarity, node.modality, node.temporal_scope),
                                     ('negative' if negative else 'positive', 'fact', 'past'))
                    self.assertEqual(node.proposition.arguments, (('を', noun),))
                    source, = freeze_analysis_sources(req).sources
                    e, = node.evidence_refs
                    raw = source.envelope.raw_utf8[e.utf8_start:e.utf8_end]
                    field = source.envelope.raw_utf8[e.field_utf8_start:e.field_utf8_end].decode()
                    self.assertEqual((raw.decode(), field[e.scalar_start:e.scalar_end]), (literal, literal))
                    self.assertEqual(hashlib.sha256(raw).hexdigest(), e.literal_sha256)
                    label = noun + 'を' + ('担当しなかった' if negative else '担当した') + '（記録された担当）'
                    self.assertEqual(artifact.safe_projection(authenticated_owner_scope=OWNER)['nodes'][0]['visible_label'], label)
                    text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text']
                    self.assertIn(label, text)
                    self.assertNotIn('実行済み', text)
                    self.assertFalse(artifact.graph.edges)
                    self.assertNotIn('ROLE', {g.missing_scope for g in artifact.graph.unknown_gaps})
                    self.assertIn('ACTION_OR_NONACTION', {g.missing_scope for g in artifact.graph.unknown_gaps})
                    with self.assertRaises(AnalysisSourceError):
                        replace(artifact, graph=replace(artifact.graph, nodes=(replace(node,
                            proposition=replace(node.proposition, arguments=(('を', '資料'),))),))).safe_projection(
                                authenticated_owner_scope=OWNER)

    def test_keyword_action_responsibility_keeps_order_updates_and_comparison(self):
        old, new = '私は記録を担当した', '私はメモを担当しなかった'
        base = record(memo=old + '。その後、私は資料を調べた。')
        for answer, labels in ((new + '。', [old, new]),
                ('「' + old + '」ではなく「' + new + '」です。', [new]),
                ('「' + old + '」は取り消します。', [])):
            with self.subTest(answer=answer):
                artifact = self.generate(request(self.with_answer(base, answer))).artifact
                self.assertIsNotNone(artifact)
                self.assertEqual([n.visible_label for n in artifact.graph.nodes if n.node_kind == 'ROLE'], labels)
                self.assertEqual(len(artifact.graph.edges), 1 if answer == new + '。' else 0)
                artifact.safe_projection(authenticated_owner_scope=OWNER)
        repeated = self.generate(request(self.with_answer(record(memo=old + '。'),
            '僕は記録を担当しました。'), record(2, memo=old + '。'))).artifact
        node, = repeated.graph.nodes
        self.assertEqual((len(node.evidence_refs), len(node.record_refs)), (3, 2))
        opposed = self.generate(request(record(memo=old + '。私は記録を担当しなかった。'))).artifact
        self.assertEqual({n.polarity for n in opposed.graph.nodes}, {'positive', 'negative'})
        self.assertEqual(len(opposed.graph.conflicts), 1)
        self.assertFalse(opposed.graph.edges)
        self.assertEqual(self.compared(old + '。', '僕は記録を担当しました。').artifact.period_comparison.change_claims, ())
        for other in (new, '私は記録を担当しなかった'):
            self.assertIn('ROUTE_EVIDENCE_CHANGED', self.compared(old + '。', other + '。').artifact.safe_projection(
                authenticated_owner_scope=OWNER)['period_comparison']['safe_change_kinds'])
        route = self.generate(request(record(memo='昨日、私は職場にいた。その後、私は会議の記録を担当した。'
            'それから、私は資料を調べた。'))).artifact
        self.assertEqual([n.node_kind for n in route.graph.nodes], ['SCENE', 'ROLE', 'ACTION_OR_NONACTION'])
        self.assertEqual([e.endpoint_refs for e in route.graph.edges], [('n1', 'n2'), ('n2', 'n3')])
        route.safe_projection(authenticated_owner_scope=OWNER)

    def test_keyword_action_responsibility_requires_consistent_shared_witness(self):
        from cocolon_meaning_experience_engine.cores.analysis import intent_compiler as compiler
        build = compiler.build_final_stage1_grounded_observation_plan
        for mismatch in ('kind', 'predicate', 'operator', 'actor', 'modality', 'polarity',
                         'future', 'optional', 'fragment', 'dependency'):
            def changed(*args, **kwargs):
                plan = build(*args, **kwargs)
                n, = plan.nuclei
                # Keep the bounded consumer contract exercised even after
                # the shared producer distinguishes nominal 記録 from an act.
                f = replace(n.semantic_frame, predicate_kind='action',
                    attribute_codes=tuple(dict.fromkeys((*n.semantic_frame.attribute_codes, 'operator:action'))))
                n = replace(n, kind='action', semantic_frame=f)
                if mismatch == 'kind': n = replace(n, kind='event')
                elif mismatch == 'optional': n = replace(n, retention='optional')
                else:
                    fields = {'predicate': {'predicate_kind': 'event'}, 'actor': {'actor': 'other'},
                        'modality': {'modality': 'wish'}, 'polarity': {'polarity': 'negative'},
                        'future': {'time_scope': 'future'},
                        'operator': {'attribute_codes': tuple(c for c in f.attribute_codes if c != 'operator:action')},
                        'fragment': {'attribute_codes': f.attribute_codes + ('source_fragment_scalar_range:0:12',)},
                        'dependency': {'attribute_codes': f.attribute_codes + ('semantic_dependency:unknown',)}}
                    n = replace(n, semantic_frame=replace(f, **fields[mismatch]))
                return replace(plan, nuclei=(n,))
            with self.subTest(mismatch=mismatch), patch.object(
                    compiler, 'build_final_stage1_grounded_observation_plan', side_effect=changed):
                self.assertIsNone(self.generate(request(record(memo='私は記録を担当した。'))).artifact)

    def test_keyword_action_responsibility_does_not_promote_unread_or_reported_scope(self):
        for memo in ('私は記録にいた。', '私はメモにいました。', '私は記録係です。',
                '記録を担当した。', '友人は記録を担当した。', '私は記録を担当したい。',
                '私は記録を担当している。', '私は記録を担当したと思う。',
                '私は記録を担当したかもしれない。', '私は記録を担当した？',
                '私は何を担当した。', '私は昨日記録の確認を担当した。',
                '友人の報告です。私は記録を担当した。',
                '夢を見た。私は記録を担当した。', '「私は記録を担当した」と聞いた。'):
            with self.subTest(memo=memo):
                outcome = self.generate(request(record(memo=memo)))
                self.assertFalse(outcome.artifact and any(n.node_kind in {'ROLE', 'SCENE'}
                                                        for n in outcome.artifact.graph.nodes))
        self.assertIsNone(self.generate(request(record(memo='', action='私は記録を担当した。'))).artifact)

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
        # A consistent shared action witness can ground a complete written
        # responsibility, but must never claim that its nominal task was done.
        artifact = self.generate(request(record(memo='私は記録を担当した。'))).artifact
        node, = artifact.graph.nodes
        self.assertEqual((node.node_kind, node.proposition.predicate_lemma), ('ROLE', '担当する'))
        self.assertNotIn('実行済み', artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'])

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

    def test_result_day_prefixes_stay_unresolved_without_erasing_other_complete_clauses(self):
        invalid = (
            '私は資料を調べた後、今日疑問が減った',
            '私は資料を調べてから、昨日疑問が減った',
            '私は資料を調べた後、今日分疑問が減った',
            '私は資料を調べた後、昨日午前疑問が減った',
            'まだ今日方針が決まっていない',
            'まだ昨日方針が見つかっていません',
            'まだ今日分方針が定まっていない',
            'まだ昨日以前方針が決まっていない',
        )
        for clause in invalid:
            with self.subTest(clause=clause):
                self.assertIsNone(self.generate(request(record(memo=clause + '。'))).artifact)
                req = request(record(memo='私は職場にいた。' + clause + '。その後私は記録を残した。'))
                artifact = self.generate(req).artifact
                self.assertEqual([n.node_kind for n in artifact.graph.nodes], ['SCENE', 'ACTION_OR_NONACTION'])
                self.assertEqual([n.proposition.predicate_lemma for n in artifact.graph.nodes], ['いる', '残す'])
                self.assertFalse(artifact.graph.edges)
                source = freeze_analysis_sources(req).sources[0].envelope
                for node, literal in zip(artifact.graph.nodes, ('私は職場にいた', 'その後私は記録を残した')):
                    e, = node.evidence_refs
                    raw = source.raw_utf8[e.utf8_start:e.utf8_end]
                    field = source.raw_utf8[e.field_utf8_start:e.field_utf8_end].decode()
                    self.assertEqual(raw.decode(), literal)
                    self.assertEqual(field[e.scalar_start:e.scalar_end], literal)
                    self.assertEqual(hashlib.sha256(raw).hexdigest(), e.literal_sha256)
                visual = artifact.safe_projection(authenticated_owner_scope=OWNER)
                text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)
                self.assertEqual(visual['projection_of'], text['projection_of'])
                self.assertIn('まだ読み取れていない内容', text['text'])
                for node in visual['nodes']:
                    self.assertIn(node['visible_label'], text['text'])
                self.assertNotIn('疑問', text['text'])
                self.assertNotIn('方針', text['text'])

    def test_result_day_nominal_boundaries_keep_explicit_nominals_and_existing_day_parsers(self):
        for noun in ('今日の疑問', '昨日の疑問', '今日分の疑問', '昨日分の疑問',
                     '仕事の昨日分', '今日', '昨日分'):
            for clause, state in (('私は資料を調べた後、' + noun + 'が減った', 'BOUNDED_CHANGE'),
                                  ('まだ' + noun + 'が決まっていない', 'NOT_YET')):
                with self.subTest(clause=clause):
                    artifact = self.generate(request(record(memo=clause + '。'))).artifact
                    self.assertIsNotNone(artifact)
                    result = artifact.graph.nodes[-1].proposition
                    self.assertEqual(result.result_state, state)
                    self.assertEqual(result.arguments, (('が', noun),))
                    self.assertEqual(result.relative_day, '')
                    self.assertIn(noun, artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'])
        for clause in ('私は今日資料を調べた', '私は昨日職場にいた', '私は今日会議を担当した'):
            with self.subTest(clause=clause):
                node, = self.generate(request(record(memo=clause + '。'))).artifact.graph.nodes
                self.assertEqual(node.proposition.relative_day, 'YESTERDAY' if '昨日' in clause else 'TODAY')

    def test_result_unparsed_day_keeps_updates_and_period_comparison_conservative(self):
        for invalid, valid in (('私は資料を調べた後、今日疑問が減った', '私は資料を調べた後、疑問が減った'),
                               ('まだ今日方針が決まっていない', 'まだ方針が決まっていない')):
            for original, answer in ((valid, invalid + '。'),
                    (valid, '「' + valid + '」ではなく「' + invalid + '」です。'),
                    (invalid, '「' + invalid + '」ではなく「' + valid + '」です。'),
                    (invalid, '「' + invalid + '」は取り消します。')):
                with self.subTest(answer=answer):
                    result = self.generate(request(self.with_answer(record(
                        memo=original + '。私は記録を残した。'), answer)))
                    self.assertEqual(result.status, EngineStatus.UNAVAILABLE)
            partial = invalid + '。私は記録を残した。'
            comparison = self.compared(partial, '私は記録を残した。').artifact
            self.assertEqual(comparison.safe_projection(authenticated_owner_scope=OWNER)
                ['period_comparison']['safe_change_kinds'], ['UNKNOWN_SCOPE_CHANGED'])
            comparison = self.compared(partial, partial.replace('今日', '昨日')).artifact
            self.assertEqual(comparison.period_comparison.change_claims, ())

    def test_unparsed_time_prefixes_do_not_become_scene_role_or_action_nouns(self):
        for time in ('明日', '明後日', '一昨日', '今朝', '昨夜', '先週', '来週',
                     '今週', '今月', '今年', '先月', '来月', '昨年', '来年'):
            for clause in ('職場にいた', '会議を担当した', '資料を調べた',
                           '職場にいなかった', '会議を担当しなかった', '資料を調べたい'):
                memo = '私は' + time + clause + '。'
                with self.subTest(memo=memo):
                    result = self.generate(request(record(memo=memo)))
                    self.assertEqual(result.status, EngineStatus.UNAVAILABLE)
                    self.assertIsNone(result.artifact)

    def test_unparsed_time_scope_keeps_readable_nodes_source_and_unknown(self):
        for clause in ('私は明日職場にいた', '私は来週会議を担当した',
                       '私は今朝資料を調べた', '私は資料を明日手帳に書いた',
                       '私は今日明日資料を調べた', '昨日私は明日職場にいた',
                       '私は明日資料を調べてから、疑問が減った',
                       '私は資料を調べてから、明日疑問が減った',
                       '私は明日資料を調べたかもしれないと思っている',
                       '私は家族の明日生活を守りたい',
                       '私は今週資料を調べた', '私は今年仕事を続けたくない',
                       '私は資料を昨年手帳に書いた', '私は新しい先月資料を見た',
                       '私は学び来月メモを残した', '私は家族の来年生活を守りたい',
                       '私は来月資料を調べないかもしれないと思う',
                       '私は資料を調べた後、今年疑問が減った',
                       '私は今年度資料を調べた', '私は今月号資料を見た'):
            with self.subTest(clause=clause):
                req = request(record(memo=clause + '。私は記録を残した。'))
                artifact = self.generate(req).artifact
                node, = artifact.graph.nodes
                self.assertEqual(node.node_kind, 'ACTION_OR_NONACTION')
                e, = node.evidence_refs
                source = freeze_analysis_sources(req).sources[0].envelope
                literal = '私は記録を残した'
                field = source.raw_utf8[e.field_utf8_start:e.field_utf8_end].decode()
                self.assertEqual(source.raw_utf8[e.utf8_start:e.utf8_end].decode(), literal)
                self.assertEqual(field[e.scalar_start:e.scalar_end], literal)
                self.assertEqual(hashlib.sha256(literal.encode()).hexdigest(), e.literal_sha256)
                visual = artifact.safe_projection(authenticated_owner_scope=OWNER)
                text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)
                self.assertEqual([n['visible_label'] for n in visual['nodes']], ['記録を残す（実行済み）'])
                self.assertTrue(any('まだ読み取れていない内容' in g['visible_label'] for g in visual['unknown_gaps']))
                self.assertIn('まだ読み取れていない内容', text['text'])
                self.assertEqual(visual['projection_of'], text['projection_of'])
                self.assertFalse(visual['edges'])
                self.assertFalse(visual['annotation_badges'])
        artifact = self.compared('私は明日職場にいた。私は資料を調べた。',
                                 '私は資料を調べた。').artifact
        self.assertEqual(artifact.safe_projection(authenticated_owner_scope=OWNER)
                         ['period_comparison']['safe_change_kinds'], ['UNKNOWN_SCOPE_CHANGED'])
        # Mixed-script nouns are parseable, but the unparsed time prefix
        # still cannot establish a route when no other clause is readable.
        result = self.generate(request(record(memo='私は資料を明日ノートに書いた。')))
        if result.artifact:
            with self.assertRaises(AnalysisSourceError):
                result.artifact.safe_projection(authenticated_owner_scope=OWNER)
        else:
            self.assertEqual(result.status, EngineStatus.UNAVAILABLE)

    def test_explicit_temporal_nominal_modifiers_and_objects_keep_their_meaning(self):
        for memo, noun, label in (
            ('私は明日の会議を担当した。', '明日の会議', '明日の会議を担当した（記録された担当）'),
            ('私は明日の資料を調べた。', '明日の資料', '明日の資料を調べる（実行済み）'),
            ('私は来週の資料を調べなかった。', '来週の資料', '来週の資料を調べる（行わなかった）'),
            ('私は明日を記録した。', '明日', '明日を記録する（実行済み）'),
            ('私は今週の資料を調べた。', '今週の資料', '今週の資料を調べる（実行済み）'),
            ('私は今年を記録した。', '今年', '今年を記録する（実行済み）'),
        ):
            with self.subTest(memo=memo):
                artifact = self.generate(request(record(memo=memo))).artifact
                node, = artifact.graph.nodes
                self.assertEqual(node.proposition.arguments, (('を', noun),))
                self.assertEqual(node.proposition.relative_day, '')
                self.assertEqual(node.temporal_scope, 'past')
                visual = artifact.safe_projection(authenticated_owner_scope=OWNER)
                self.assertEqual(visual['nodes'][0]['visible_label'], label)
                self.assertIn(label, artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'])

    def test_period_time_nominal_heads_preserve_existing_year_and_issue_objects(self):
        # These are complete nominal segments, not a date for the action.
        for noun in ('今年度', '昨年度', '来年度', '今月号', '先月号', '来月号'):
            for target in (noun, noun + 'の資料'):
                with self.subTest(target=target):
                    req = request(record(memo='私は' + target + 'を見なかった。'))
                    artifact = self.generate(req).artifact
                    self.assertIsNotNone(artifact)
                    node, = artifact.graph.nodes
                    self.assertEqual(node.proposition.arguments, (('を', target),))
                    self.assertEqual(node.proposition.relative_day, '')
                    self.assertEqual(node.proposition.polarity, 'negative')
                    self.assertIn(target + 'を見る（行わなかった）',
                        artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'])

    def test_period_time_scope_preserves_updates_comparison_and_order_barrier(self):
        invalid, valid = '私は今週資料を調べた', '私は資料を調べた'
        for original, answer in ((valid, invalid + '。'),
                (valid, '「' + valid + '」ではなく「' + invalid + '」です。'),
                (invalid, '「' + invalid + '」ではなく「' + valid + '」です。'),
                (invalid, '「' + invalid + '」は取り消します。')):
            with self.subTest(answer=answer):
                outcome = self.generate(request(self.with_answer(
                    record(memo=original + '。私は記録を残した。'), answer)))
                self.assertEqual(outcome.status, EngineStatus.UNAVAILABLE)
        for field in ('memo', 'memo_action'):
            with self.subTest(field=field):
                text = '私は記録を残した。' + invalid + '。その後私は作品を作った。'
                member = record(memo=text) if field == 'memo' else record(memo='', action=text)
                artifact = self.generate(request(member)).artifact
                self.assertEqual([n.proposition.predicate_lemma for n in artifact.graph.nodes],
                                 ['残す', '作る'])
                self.assertFalse(artifact.graph.edges)
                self.assertIn('まだ読み取れていない内容',
                    artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'])
        artifact = self.compared(invalid + '。私は記録を残した。',
                                 '私は今年仕事を続けたい。私は記録を残した。').artifact
        self.assertEqual(artifact.period_comparison.change_claims, ())

    def test_unparsed_time_supplements_and_updates_do_not_resolve_by_guessing(self):
        valid, invalid = '私は職場にいた', '私は明日職場にいた'
        for original, answer in (
            (valid, invalid + '。'),
            (valid, '「' + valid + '」ではなく「' + invalid + '」です。'),
            (invalid, '「' + invalid + '」ではなく「' + valid + '」です。'),
            (invalid, '「' + invalid + '」は取り消します。'),
        ):
            with self.subTest(original=original, answer=answer):
                result = self.generate(request(self.with_answer(
                    record(memo=original + '。私は資料を調べた。'), answer)))
                self.assertEqual(result.status, EngineStatus.UNAVAILABLE)
                self.assertIsNone(result.artifact)

    def test_unparsed_time_nominal_cannot_be_reintroduced_into_safe_surface(self):
        artifact = self.generate(request(record(memo='私は職場にいた。'))).artifact
        node, = artifact.graph.nodes
        forged = replace(node, visible_label='私は明日職場にいた',
            proposition=replace(node.proposition, arguments=(('に', '明日職場'),),
                source_parts=tuple((role, a if role in {'SELF_TOPIC', 'SCENE_NOMINAL'} else a + 2,
                                    b if role == 'SELF_TOPIC' else b + 2)
                                   for role, a, b in node.proposition.source_parts)))
        with self.assertRaises(AnalysisSourceError):
            replace(artifact, graph=replace(artifact.graph, nodes=(forged,))).safe_projection(
                authenticated_owner_scope=OWNER)

    def test_mixed_script_nominals_keep_arguments_operators_and_exact_source(self):
        cases = (
            ('私は仕事メモを残した', (('を', '仕事メモ'),), 'positive', 'fact', 'past'),
            ('僕は考えをメモ帳に書かなかった', (('を', '考え'), ('に', 'メモ帳')), 'negative', 'fact', 'past'),
            ('私は、今日、会議メモの内容を調べたい', (('を', '会議メモの内容'),), 'positive', 'wish', 'current_input'),
            ('私は仕事メモを残したくない', (('を', '仕事メモ'),), 'negative', 'wish', 'current_input'),
            ('私は、昨日、会議室ロビーにいた', (('に', '会議室ロビー'),), 'positive', 'fact', 'past'),
            ('私はイベント企画を担当しなかった', (('を', 'イベント企画'),), 'negative', 'fact', 'past'),
            ('まだイベント会場が決まっていない', (('が', 'イベント会場'),), 'negative', 'fact', 'current_input'),
            ('私は家族サービスの時間を守りたい', (('を', '家族サービスの時間'),), 'positive', 'wish', 'current_input'),
        )
        for literal, arguments, polarity, modality, time in cases:
            with self.subTest(literal=literal):
                req = request(record(memo='　' + literal + '。'))
                artifact = self.generate(req).artifact
                self.assertIsNotNone(artifact)
                node, = artifact.graph.nodes
                p = node.proposition
                self.assertEqual((p.arguments, p.polarity, p.modality, p.temporal_scope),
                                 (arguments, polarity, modality, time))
                self.assertEqual([i for _, a, b in p.source_parts for i in range(a, b)],
                                 list(range(len(literal))))
                e, = node.evidence_refs
                source = freeze_analysis_sources(req).sources[0].envelope
                raw = source.raw_utf8[e.utf8_start:e.utf8_end]
                field = source.raw_utf8[e.field_utf8_start:e.field_utf8_end].decode()
                self.assertEqual(raw.decode(), literal)
                self.assertEqual(field[e.scalar_start:e.scalar_end], literal)
                self.assertEqual(hashlib.sha256(raw).hexdigest(), e.literal_sha256)
                visual = artifact.safe_projection(authenticated_owner_scope=OWNER)
                text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)
                self.assertEqual(text['projection_of'], visual['projection_of'])
                self.assertIn(visual['nodes'][0]['visible_label'], text['text'])
                broken = replace(p, arguments=((arguments[0][0], '別ノート'),))
                with self.assertRaises(AnalysisSourceError):
                    replace(artifact, graph=replace(artifact.graph, nodes=(replace(node,
                        proposition=broken),))).safe_projection(authenticated_owner_scope=OWNER)

    def test_mixed_script_nominals_keep_cognitive_and_order_scopes(self):
        cognition = self.generate(request(record(memo='私はメモ帳に書くかもしれないと思う。'))).artifact
        node, = cognition.graph.nodes
        self.assertEqual(node.node_kind, 'ATTENTION_OR_THOUGHT')
        content = node.proposition.possible_content
        self.assertEqual((content.actor, content.arguments, content.modality),
                         ('UNSPECIFIED', (('に', 'メモ帳'),), 'possibility'))
        self.assertNotIn('実行済み', cognition.safe_text_projection(authenticated_owner_scope=OWNER)['text'])
        for memo, kinds, edge_count in (
            ('私は会議室ロビーにいた。その後、私はイベント企画を担当した。それから、私は仕事メモを残した。',
             ['SCENE', 'ROLE', 'ACTION_OR_NONACTION'], 2),
            ('私は仕事メモを残してから、ストレス量が減った。',
             ['ACTION_OR_NONACTION', 'IMMEDIATE_RESULT_OR_AFTERMATH'], 1),
            ('私は仕事メモを残した後、ストレス量が減った。',
             ['ACTION_OR_NONACTION', 'IMMEDIATE_RESULT_OR_AFTERMATH'], 1),
        ):
            with self.subTest(memo=memo):
                artifact = self.generate(request(record(memo=memo))).artifact
                self.assertEqual([n.node_kind for n in artifact.graph.nodes], kinds)
                self.assertEqual(len(artifact.graph.edges), edge_count)
                self.assertIn('原因を示す線ではありません',
                              artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'])
        plain = self.generate(request(record(memo='私は仕事メモを残した。私はメモ帳を見た。'))).artifact
        self.assertEqual(plain.graph.edges, ())

    def test_mixed_script_nominals_do_not_erase_unread_grammar_or_actor(self):
        for literal in (
            '仕事メモを残した', '友人は仕事メモを残した',
            '私は急いで仕事メモを残した', '私は読んで仕事メモを残した',
            '私は仕事メモを残したと聞いた', '私は仕事メモを残したなら',
            '私は仕事メモを残した？', '「私は仕事メモを残した」',
            '私は仕事メモを残した夢を見た', '私は仕事メモを残して',
            '私は仕事メモを残したあと', '私は新しくないメモ帳を見た',
        ):
            with self.subTest(literal=literal):
                self.assertIsNone(self.generate(request(record(memo=literal + '。'))).artifact)
        partial = self.generate(request(record(memo=
            '私は仕事メモを残した。私は急いでメモ帳を見た。その後私は資料を調べた。'))).artifact
        self.assertEqual(len(partial.graph.nodes), 2)
        self.assertEqual(partial.graph.edges, ())
        self.assertIn('SOURCE_SCOPE', [g.missing_scope for g in partial.graph.unknown_gaps])

    def test_mixed_script_nominals_keep_unparsed_time_out_of_every_argument(self):
        for literal in (
            '私は明日メモ帳を見た', '私は来週イベント企画を担当した',
            '私は今朝会議室ロビーにいた', '私は考えを明日ノートに書いた',
            '私は会議メモの来週イベントを記録した',
            '私は明日メモ帳に書くかもしれないと思う',
            '私は来週家族サービスの時間を守りたい',
            '私は仕事メモを残してから、来週ストレス量が減った',
            '私は明日仕事メモを残してから、疑問が減った',
        ):
            with self.subTest(literal=literal):
                artifact = self.generate(request(record(memo=literal + '。私は記録を残した。'))).artifact
                self.assertEqual([n.proposition.arguments for n in artifact.graph.nodes], [(('を', '記録'),)])
                self.assertEqual(artifact.graph.edges, ())
                self.assertIn('SOURCE_SCOPE', [g.missing_scope for g in artifact.graph.unknown_gaps])
                artifact.safe_projection(authenticated_owner_scope=OWNER)
        nominal = self.generate(request(record(memo='私は明日の仕事メモを残した。'))).artifact
        self.assertEqual(nominal.graph.nodes[0].proposition.arguments, (('を', '明日の仕事メモ'),))
        self.assertEqual(nominal.graph.nodes[0].proposition.relative_day, '')

    def test_mixed_script_nominals_keep_update_lineage_and_comparison_meaning(self):
        old, new = '私は仕事メモを残した', '私は会議メモを残さなかった'
        original = record(memo=old + '。私は資料を調べた。')
        req = request(self.with_answer(original, '「' + old + '」ではなく「' + new + '」です。'))
        artifact = self.generate(req).artifact
        node = next(n for n in artifact.graph.nodes if n.proposition.predicate_lemma == '残す')
        self.assertEqual((node.proposition.arguments, node.polarity), ((('を', '会議メモ'),), 'negative'))
        source = next(s.envelope for s in freeze_analysis_sources(req).sources
                      if s.envelope.source_role == 'SUPPLEMENTAL_ANSWER')
        for e in node.evidence_refs:
            self.assertEqual(e.source_envelope_id, source.envelope_id)
            self.assertEqual(source.raw_utf8[e.utf8_start:e.utf8_end].decode(), new)
        withdrawn = self.generate(request(self.with_answer(original, '「' + old + '」は取り消します。'))).artifact
        self.assertEqual([n.proposition.arguments for n in withdrawn.graph.nodes], [(('を', '資料'),)])
        supplemented = self.generate(request(self.with_answer(record(memo='私は資料を調べた。'), old + '。'))).artifact
        self.assertEqual(len(supplemented.graph.nodes), 2)
        for answer in ('私は急いでメモ帳を見た。', '「' + old + '」ではなく「私は明日メモ帳を見た」です。'):
            self.assertIsNone(self.generate(request(self.with_answer(original, answer))).artifact)
        same = self.compared('僕は、メモ帳に考えを書きました。', '私は考えをメモ帳に書いた。').artifact
        self.assertEqual(same.period_comparison.change_claims, ())
        for changed in ('私は会議メモを残した。', '私は仕事メモを残さなかった。'):
            artifact = self.compared(changed, old + '。').artifact
            self.assertIn('ROUTE_EVIDENCE_CHANGED', artifact.safe_projection(authenticated_owner_scope=OWNER)
                          ['period_comparison']['safe_change_kinds'])

    def test_interrogative_nominals_do_not_become_completed_actions_or_wishes(self):
        for clause in ('私は何を調べた', '私は誰を見なかった', '私は誰の資料を見た',
                       '私は資料の何を調べた', '私は何語を調べた', '私は何度ノートを見た',
                       '私は何を調べたい', '私は誰の資料を見たくなかった',
                       '私は何を調べるかもしれないと思う',
                       '私は、誰の資料を見なかったかもしれないと思っている',
                       '私は新しい何を見た', '私は考えを誰のノートに書いた',
                       '私は何を調べてから、疑問が減った', 'まだ誰の方針が決まっていない'):
            with self.subTest(clause=clause):
                self.assertIsNone(self.generate(request(record(memo=clause + '。'))).artifact)
                req = request(record(memo=clause + '。私は記録を残した。'))
                artifact = self.generate(req).artifact
                self.assertIsNotNone(artifact)
                node, = artifact.graph.nodes
                self.assertEqual(node.proposition.arguments, (('を', '記録'),))
                self.assertFalse(artifact.graph.edges)
                self.assertIn('SOURCE_SCOPE', [g.missing_scope for g in artifact.graph.unknown_gaps])
                e, = node.evidence_refs
                source, = freeze_analysis_sources(req).sources
                raw = source.envelope.raw_utf8[e.utf8_start:e.utf8_end]
                field = source.envelope.raw_utf8[e.field_utf8_start:e.field_utf8_end].decode()
                self.assertEqual(raw.decode(), '私は記録を残した')
                self.assertEqual(field[e.scalar_start:e.scalar_end], raw.decode())
                self.assertEqual(hashlib.sha256(raw).hexdigest(), e.literal_sha256)
                text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text']
                self.assertIn('まだ読み取れていない内容', text)
                self.assertNotRegex(text, '何|誰')
        # A graph built while admission is bypassed must still fail safe replay.
        target = 'cocolon_meaning_experience_engine.cores.analysis.intent_compiler._has_unparsed_nominal_scope'
        for clause in ('私は何を調べた', '私は誰の資料を見るかもしれないと思う'):
            with self.subTest(replay=clause):
                with patch(target, return_value=False):
                    unsafe = self.generate(request(record(memo=clause + '。'))).artifact
                self.assertIsNotNone(unsafe)
                with self.assertRaises(AnalysisSourceError):
                    unsafe.safe_projection(authenticated_owner_scope=OWNER)

    def test_interrogative_nominals_do_not_supply_update_targets_or_period_claims(self):
        valid, unknown = '私は記録を残した', '私は誰の資料を見た'
        base = record(memo=valid + '。' + unknown + '。')
        for answer in (unknown + '。',
                       '「' + valid + '」ではなく「' + unknown + '」です。',
                       '「' + unknown + '」ではなく「私は資料を見た」です。',
                       '「' + unknown + '」は取り消します。'):
            with self.subTest(answer=answer):
                self.assertIsNone(self.generate(request(self.with_answer(base, answer))).artifact)
        safe = self.generate(request(self.with_answer(base,
            '「' + valid + '」ではなく「私は記録を残さなかった」です。'))).artifact
        self.assertEqual(len(safe.graph.nodes), 1)
        self.assertIn('行わなかった', safe.safe_text_projection(authenticated_owner_scope=OWNER)['text'])
        self.assertIn('SOURCE_SCOPE', [g.missing_scope for g in safe.graph.unknown_gaps])
        same = self.compared(valid + '。' + unknown + '。', valid + '。私は何を調べた。').artifact
        self.assertEqual(same.period_comparison.change_claims, ())
        self.assertIn('読み取れていない内容の変化は判断していません',
                      same.safe_text_projection(authenticated_owner_scope=OWNER)['text'])
        interrupted = self.generate(request(record(memo=
            '私は資料を調べた。私は何を見た。それから私は記録を残した。'))).artifact
        self.assertEqual(len(interrupted.graph.nodes), 2)
        self.assertFalse(interrupted.graph.edges)
        interrupted.safe_projection(authenticated_owner_scope=OWNER)

    def test_interrogative_guard_keeps_written_ordinary_nominals(self):
        for noun in ('幾何学', '幾何の資料', '新しい幾何学', '仕事の資料', '疑問', '何か'):
            with self.subTest(noun=noun):
                result = self.generate(request(record(memo='私は' + noun + 'を調べた。')))
                if noun in ('新しい幾何学', '何か'):
                    # Existing modified 幾 and arbitrary kana remain unparsed.
                    self.assertIsNone(result.artifact)
                    continue
                node, = result.artifact.graph.nodes
                self.assertEqual(node.proposition.arguments, (('を', noun),))
                self.assertIn(noun + 'を調べる（実行済み）',
                              result.artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'])

    def test_attributive_nominals_keep_whole_arguments_and_exact_source(self):
        cases = [(f'私は{word}メモ帳を見た', (('を', word + 'メモ帳'),), 'positive', 'fact')
            for word in ('新しい', '古い', '大きい', '小さい', '長い', '短い',
                         '詳しい', '難しい', '易しい', '良い', '悪い')]
        cases += [
            ('僕は、詳しい仕事メモを古いノートに書かなかった',
             (('を', '詳しい仕事メモ'), ('に', '古いノート')), 'negative', 'fact'),
            ('私は新しい仕事を続けたくない', (('を', '新しい仕事'),), 'negative', 'wish'),
            ('私は昨日、新しい会議室にいた', (('に', '新しい会議室'),), 'positive', 'fact'),
            ('私は新しいイベント企画を担当しなかった', (('を', '新しいイベント企画'),), 'negative', 'fact'),
            ('私は良い生活を守りたい', (('を', '良い生活'),), 'positive', 'wish'),
            ('まだ新しいイベント会場が決まっていない', (('が', '新しいイベント会場'),), 'negative', 'fact'),
            ('私は新しいメモ帳の詳しい説明を調べた', (('を', '新しいメモ帳の詳しい説明'),), 'positive', 'fact'),
        ]
        for literal, arguments, polarity, modality in cases:
            with self.subTest(literal=literal):
                req = request(record(memo='　' + literal + '。'))
                artifact = self.generate(req).artifact
                self.assertIsNotNone(artifact)
                node, = artifact.graph.nodes
                p = node.proposition
                self.assertEqual((p.arguments, p.polarity, p.modality), (arguments, polarity, modality))
                self.assertEqual([i for _, a, b in p.source_parts for i in range(a, b)], list(range(len(literal))))
                e, = node.evidence_refs
                source = freeze_analysis_sources(req).sources[0].envelope
                raw = source.raw_utf8[e.utf8_start:e.utf8_end]
                field = source.raw_utf8[e.field_utf8_start:e.field_utf8_end].decode()
                self.assertEqual((raw.decode(), field[e.scalar_start:e.scalar_end]), (literal, literal))
                self.assertEqual(hashlib.sha256(raw).hexdigest(), e.literal_sha256)
                visual = artifact.safe_projection(authenticated_owner_scope=OWNER)
                text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)
                self.assertEqual(text['projection_of'], visual['projection_of'])
                for _, noun in arguments:
                    self.assertIn(noun, visual['nodes'][0]['visible_label'])
                    self.assertIn(noun, text['text'])
                self.assertEqual(artifact.graph.edges, ())

    def test_attributive_nominals_preserve_cognition_order_and_result_scope(self):
        artifact = self.generate(request(record(memo='私は新しいメモ帳に書くかもしれないと思う。'))).artifact
        content = artifact.graph.nodes[0].proposition.possible_content
        self.assertEqual((content.actor, content.arguments, content.modality),
            ('UNSPECIFIED', (('に', '新しいメモ帳'),), 'possibility'))
        self.assertNotIn('実行済み', artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'])
        for memo, expected in (
            ('私は新しい会議室にいた。その後、私は新しい企画を担当した。それから、私は詳しいメモを書いた。',
             ['SCENE', 'ROLE', 'ACTION_OR_NONACTION']),
            ('私は新しい仕事メモを残してから、古い資料が減った。',
             ['ACTION_OR_NONACTION', 'IMMEDIATE_RESULT_OR_AFTERMATH']),
        ):
            with self.subTest(memo=memo):
                artifact = self.generate(request(record(memo=memo))).artifact
                self.assertEqual([n.node_kind for n in artifact.graph.nodes], expected)
                self.assertEqual(len(artifact.graph.edges), len(expected) - 1)
                self.assertIn('原因を示す線ではありません', artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'])

    def test_attributive_nominals_leave_unproved_inflection_actor_and_scope_unknown(self):
        for literal in (
            '私は新しくないメモ帳を見た', '私は新しかったメモ帳を見た',
            '私は新しくメモ帳を見た', '私は新しくて大きいメモ帳を見た',
            '私はとても新しいメモ帳を見た', '私は新しい大きいメモ帳を見た',
            '私は楽しいメモ帳を見た', '私は新しいを見た',
            '新しいメモ帳を見た', '友人は新しいメモ帳を見た',
            '「私は新しいメモ帳を見た」', '私は新しいメモ帳を見た？',
            '私は新しいメモ帳を見たと聞いた', '私は新しいメモ帳を見たなら',
        ):
            with self.subTest(literal=literal):
                self.assertIsNone(self.generate(request(record(memo=literal + '。'))).artifact)
        # The formerly unproved shared witness now distinguishes the nominal
        # modifier from a constraint. Preserve the whole target and past role.
        artifact = self.generate(request(record(memo='私は難しいイベント企画を担当した。'))).artifact
        self.assertIsNotNone(artifact)
        node, = artifact.graph.nodes
        self.assertEqual((node.node_kind, node.polarity, node.modality, node.temporal_scope),
                         ('ROLE', 'positive', 'fact', 'past'))
        self.assertEqual(node.proposition.arguments, (('を', '難しいイベント企画'),))
        self.assertIn('難しいイベント企画を担当した（記録された担当）',
                      artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'])

    def test_attributive_nominals_cannot_hide_unparsed_time_or_question_heads(self):
        for literal in (
            '私は新しい来週資料を見た', '私は詳しい仕事の古い今朝メモを残した',
            '私は考えを新しい昨日ノートに書いた', '私は新しい今日会議室にいた',
            '私は新しい何を見た', '私は新しい誰のメモを見た',
            '私は新しい来週資料に書くかもしれないと思う',
            '私は新しい来週仕事を守りたい',
            '私は新しい資料を見てから、古い来週資料が減った',
        ):
            with self.subTest(literal=literal):
                artifact = self.generate(request(record(memo=literal + '。私は記録を残した。'))).artifact
                self.assertEqual([n.proposition.arguments for n in artifact.graph.nodes], [(('を', '記録'),)])
                self.assertEqual(artifact.graph.edges, ())
                self.assertIn('SOURCE_SCOPE', [g.missing_scope for g in artifact.graph.unknown_gaps])
                artifact.safe_projection(authenticated_owner_scope=OWNER)
        for noun in ('明日の新しい資料', '今日の新しいメモ帳', '仕事の昨日分'):
            with self.subTest(noun=noun):
                artifact = self.generate(request(record(memo='私は' + noun + 'を調べた。'))).artifact
                self.assertEqual(artifact.graph.nodes[0].proposition.arguments, (('を', noun),))
                self.assertEqual(artifact.graph.nodes[0].proposition.relative_day, '')

    def test_attributive_nominals_keep_correction_withdrawal_and_comparison(self):
        old, new = '私は新しいメモ帳を見た', '私は古いメモ帳を見なかった'
        original = record(memo=old + '。私は資料を調べた。')
        req = request(self.with_answer(original, '「' + old + '」ではなく「' + new + '」です。'))
        artifact = self.generate(req).artifact
        node = next(n for n in artifact.graph.nodes if n.proposition.predicate_lemma == '見る')
        self.assertEqual((node.proposition.arguments, node.polarity), ((('を', '古いメモ帳'),), 'negative'))
        source = next(s.envelope for s in freeze_analysis_sources(req).sources if s.envelope.source_role == 'SUPPLEMENTAL_ANSWER')
        self.assertTrue(all(e.source_envelope_id == source.envelope_id and
            source.raw_utf8[e.utf8_start:e.utf8_end].decode() == new for e in node.evidence_refs))
        withdrawn = self.generate(request(self.with_answer(original, '「' + old + '」は取り消します。'))).artifact
        self.assertEqual([n.proposition.arguments for n in withdrawn.graph.nodes], [(('を', '資料'),)])
        added = self.generate(request(self.with_answer(record(memo='私は資料を調べた。'), old + '。'))).artifact
        self.assertEqual(len(added.graph.nodes), 2)
        for answer in ('私は新しくないメモ帳を見た。', '「' + old + '」ではなく「私は新しい来週資料を見た」です。'):
            self.assertIsNone(self.generate(request(self.with_answer(original, answer))).artifact)
        same = self.compared('僕は古いノートに新しい考えを書きました。', '私は新しい考えを古いノートに書いた。').artifact
        self.assertEqual(same.period_comparison.change_claims, ())
        for changed in ('私は古いメモ帳を見た。', '私は新しいメモ帳を見なかった。'):
            artifact = self.compared(changed, old + '。').artifact
            self.assertIn('ROUTE_EVIDENCE_CHANGED', artifact.safe_projection(authenticated_owner_scope=OWNER)['period_comparison']['safe_change_kinds'])

    def test_attributive_nominal_cannot_be_removed_or_swapped_in_safe_projection(self):
        artifact = self.generate(request(record(memo='私は新しいメモ帳を見た。'))).artifact
        node, = artifact.graph.nodes
        for noun in ('メモ帳', '古いメモ帳', '新しい来週資料'):
            with self.subTest(noun=noun), self.assertRaises(AnalysisSourceError):
                changed = replace(node, proposition=replace(node.proposition, arguments=(('を', noun),)))
                replace(artifact, graph=replace(artifact.graph, nodes=(changed,))).safe_projection(authenticated_owner_scope=OWNER)

    def test_kana_compounds_keep_whole_arguments_and_exact_source(self):
        cases = [
            ('私は振り返りメモを書いた', (('を', '振り返りメモ'),), 'positive', 'fact'),
            ('私は気持ちメモを残した', (('を', '気持ちメモ'),), 'positive', 'fact'),
            ('私は学びノートを見た', (('を', '学びノート'),), 'positive', 'fact'),
            ('私は取り組み方を記録した', (('を', '取り組み方'),), 'positive', 'fact'),
            ('私は考え方を思い出ノートに書いた', (('を', '考え方'), ('に', '思い出ノート')), 'positive', 'fact'),
            ('私は新しい振り返りメモを古い学びノートに書かなかった',
             (('を', '新しい振り返りメモ'), ('に', '古い学びノート')), 'negative', 'fact'),
            ('私は振り返りメモの考え方を学びノートに書きたい',
             (('を', '振り返りメモの考え方'), ('に', '学びノート')), 'positive', 'wish'),
        ]
        for literal, arguments, polarity, modality in cases:
            with self.subTest(literal=literal):
                req = request(record(memo='　' + literal + '。'))
                artifact = self.generate(req).artifact
                self.assertIsNotNone(artifact)
                node, = artifact.graph.nodes
                p = node.proposition
                self.assertEqual((p.arguments, p.polarity, p.modality), (arguments, polarity, modality))
                self.assertEqual([i for _, a, b in p.source_parts for i in range(a, b)], list(range(len(literal))))
                e, = node.evidence_refs
                source = freeze_analysis_sources(req).sources[0].envelope
                raw = source.raw_utf8[e.utf8_start:e.utf8_end]
                field = source.raw_utf8[e.field_utf8_start:e.field_utf8_end].decode()
                self.assertEqual((raw.decode(), field[e.scalar_start:e.scalar_end]), (literal, literal))
                self.assertEqual(hashlib.sha256(raw).hexdigest(), e.literal_sha256)
                visual = artifact.safe_projection(authenticated_owner_scope=OWNER)
                text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)
                self.assertEqual(text['projection_of'], visual['projection_of'])
                for _, noun in arguments:
                    self.assertIn(noun, visual['nodes'][0]['visible_label'])
                    self.assertIn(noun, text['text'])
                self.assertEqual(artifact.graph.edges, ())

    def test_kana_compounds_preserve_cognition_day_and_result_scope(self):
        artifact = self.generate(request(record(memo='私は振り返りメモを書くかもしれないと思う。'))).artifact
        content = artifact.graph.nodes[0].proposition.possible_content
        self.assertEqual((content.actor, content.arguments, content.modality),
            ('UNSPECIFIED', (('を', '振り返りメモ'),), 'possibility'))
        self.assertNotIn('実行済み', artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'])
        artifact = self.generate(request(record(memo=
            '私は昨日、振り返りメモを書いた。その後、私は学びノートを見なかった。'))).artifact
        self.assertEqual([n.proposition.relative_day for n in artifact.graph.nodes], ['YESTERDAY', ''])
        self.assertEqual([n.polarity for n in artifact.graph.nodes], ['positive', 'negative'])
        self.assertEqual(len(artifact.graph.edges), 1)
        artifact = self.generate(request(record(memo='私は振り返りメモを残してから、学びノートが減った。'))).artifact
        self.assertEqual([n.proposition.arguments for n in artifact.graph.nodes],
            [(('を', '振り返りメモ'),), (('が', '学びノート'),)])
        self.assertEqual([n.node_kind for n in artifact.graph.nodes],
            ['ACTION_OR_NONACTION', 'IMMEDIATE_RESULT_OR_AFTERMATH'])
        self.assertIn('原因を示す線ではありません', artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'])

    def test_kana_compounds_do_not_hide_unproved_clauses_or_suffix_scope(self):
        # These scopes are rejected for the entire source, even beside a
        # supported clause. Keep that existing source-admission boundary.
        for literal in (
            '「私は振り返りメモを書いた」', '私は振り返りメモを書いた？',
            '私は振り返りメモを書いたと聞いた', '私は振り返りメモを書いたなら',
        ):
            self.assertIsNone(self.generate(request(record(memo=literal + '。'))).artifact)
            self.assertIsNone(self.generate(request(record(memo=literal + '。私は記録を残した。'))).artifact)
        for literal in (
            '私は学び直しを記録した', '私は考えてメモを書いた',
            '私は思い出してメモを書いた', '私は取り組み続けた',
            '私は振り返り学びノートを見た', '私は急いで気持ちメモを書いた',
            '振り返りメモを書いた', '友人は振り返りメモを書いた',
            '私は気持ち明日メモを残した', '私は新しい振り返り来週資料を見た',
            '私は学び今日ノートを見た', '私は考え昨日資料を見た',
            '私は気持ち何メモを残した', '私は思い誰メモを見た',
            '私は取り組み幾資料を見た', '私は資料の気持ち今朝メモを残した',
            '私は学び来週ノートに書くかもしれないと思う',
            '私は考え来週生活を守りたい',
            '私は振り返りメモを残してから、気持ち来週メモが増えた',
        ):
            with self.subTest(literal=literal):
                self.assertIsNone(self.generate(request(record(memo=literal + '。'))).artifact)
                artifact = self.generate(request(record(memo=literal + '。私は記録を残した。'))).artifact
                self.assertEqual([n.proposition.arguments for n in artifact.graph.nodes], [(('を', '記録'),)])
                self.assertEqual(artifact.graph.edges, ())
                self.assertIn('SOURCE_SCOPE', [g.missing_scope for g in artifact.graph.unknown_gaps])
                artifact.safe_projection(authenticated_owner_scope=OWNER)
        for noun in ('明日の振り返りメモ', '仕事の昨日分', '振り返りメモの昨日分'):
            artifact = self.generate(request(record(memo='私は' + noun + 'を見た。'))).artifact
            self.assertEqual(artifact.graph.nodes[0].proposition.arguments, (('を', noun),))
            self.assertEqual(artifact.graph.nodes[0].proposition.relative_day, '')

    def test_kana_compounds_keep_correction_withdrawal_and_comparison(self):
        old, new = '私は振り返りメモを書いた', '私は気持ちメモを書かなかった'
        original = record(memo=old + '。私は資料を調べた。')
        req = request(self.with_answer(original, '「' + old + '」ではなく「' + new + '」です。'))
        artifact = self.generate(req).artifact
        node = next(n for n in artifact.graph.nodes if n.proposition.predicate_lemma == '書く')
        self.assertEqual((node.proposition.arguments, node.polarity), ((('を', '気持ちメモ'),), 'negative'))
        source = next(s.envelope for s in freeze_analysis_sources(req).sources if s.envelope.source_role == 'SUPPLEMENTAL_ANSWER')
        self.assertTrue(all(e.source_envelope_id == source.envelope_id and
            source.raw_utf8[e.utf8_start:e.utf8_end].decode() == new for e in node.evidence_refs))
        withdrawn = self.generate(request(self.with_answer(original, '「' + old + '」は取り消します。'))).artifact
        self.assertEqual([n.proposition.arguments for n in withdrawn.graph.nodes], [(('を', '資料'),)])
        added = self.generate(request(self.with_answer(record(memo='私は資料を調べた。'), old + '。'))).artifact
        self.assertEqual(len(added.graph.nodes), 2)
        bad = '「' + old + '」ではなく「私は振り返り来週メモを書いた」です。'
        self.assertIsNone(self.generate(request(self.with_answer(original, bad))).artifact)
        same = self.compared('僕は学びノートに気持ちメモを書きました。', '私は気持ちメモを学びノートに書いた。').artifact
        self.assertEqual(same.period_comparison.change_claims, ())
        for changed in ('私は気持ちメモを書いた。', '私は振り返りメモを書かなかった。'):
            artifact = self.compared(changed, old + '。').artifact
            self.assertIn('ROUTE_EVIDENCE_CHANGED', artifact.safe_projection(authenticated_owner_scope=OWNER)['period_comparison']['safe_change_kinds'])

    def test_kana_compounds_cannot_be_shortened_or_swapped_in_safe_projection(self):
        artifact = self.generate(request(record(memo='私は振り返りメモを書いた。'))).artifact
        node, = artifact.graph.nodes
        for noun in ('振り返り', 'メモ', '気持ちメモ', '振り返り来週メモ'):
            with self.subTest(noun=noun), self.assertRaises(AnalysisSourceError):
                changed = replace(node, proposition=replace(node.proposition, arguments=(('を', noun),)))
                replace(artifact, graph=replace(artifact.graph, nodes=(changed,))).safe_projection(authenticated_owner_scope=OWNER)

    def test_event_topic_comma_preserves_finite_meaning_and_original_evidence(self):
        for literal in (
            '私は、職場にいた', '僕は，職場にいました',
            'わたしは、 職場にいなかった', '自分は、\u3000職場にいませんでした',
            '私は、会議の司会を担当した', '僕は，会議を担当しました',
            'わたしは、 会議を担当しなかった', '自分は、\u3000会議を担当しませんでした',
            '私は、昨日職場にいた', '私は、今日、会議の司会を担当した',
            '昨日、私は、職場にいた', 'その後、私は、会議を担当した',
        ):
            with self.subTest(literal=literal):
                req = request(record(memo=literal + '。'))
                artifact = self.generate(req).artifact
                baseline = self.generate(request(record(memo=re.sub(r'は[、，][ \u3000]*', 'は', literal) + '。'))).artifact
                self.assertIsNotNone(artifact)
                node, = artifact.graph.nodes
                e, = node.evidence_refs
                source = freeze_analysis_sources(req).sources[0].envelope
                raw = source.raw_utf8[e.utf8_start:e.utf8_end]
                field = source.raw_utf8[e.field_utf8_start:e.field_utf8_end].decode()
                self.assertEqual(raw.decode(), literal)
                self.assertEqual(field[e.scalar_start:e.scalar_end], literal)
                self.assertEqual(hashlib.sha256(raw).hexdigest(), e.literal_sha256)
                self.assertEqual([i for _, a, b in node.proposition.source_parts for i in range(a, b)],
                                 list(range(len(literal))))
                text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)
                visual = artifact.safe_projection(authenticated_owner_scope=OWNER)
                self.assertEqual(text['text'], baseline.safe_text_projection(authenticated_owner_scope=OWNER)['text'])
                self.assertEqual(text['projection_of'], visual['projection_of'])
                self.assertEqual((node.node_kind, node.polarity, node.modality, node.temporal_scope),
                    tuple(getattr(baseline.graph.nodes[0], k) for k in
                          ('node_kind', 'polarity', 'modality', 'temporal_scope')))
                broken = replace(node.proposition, source_parts=tuple(
                    (role, a, b - 1 if role == 'SELF_TOPIC' else b)
                    for role, a, b in node.proposition.source_parts))
                with self.assertRaises(AnalysisSourceError):
                    replace(artifact, graph=replace(artifact.graph, nodes=(replace(node,
                        proposition=broken),))).safe_projection(authenticated_owner_scope=OWNER)

    def test_event_topic_comma_keeps_subject_scope_and_shared_witness_boundaries(self):
        for literal in (
            '職場にいた', '友人は、職場にいた', '私は、友人は職場にいた',
            '私は、\n職場にいた', '私は、\r\n会議を担当した', '私は、。職場にいた',
            '私は、、職場にいた', '私は、\t会議を担当した',
            '私は、明日職場にいた', '私は、今日昨日会議を担当した',
            '私は、昨日朝職場にいた', '私は、昨日開催の会議を担当した',
            '今日、私は、昨日職場にいた', 'その後、私は、今日会議を担当した',
            '私は、今日の会議を担当した', '私は、職場にいる', '私は、会議を担当したい',
            '私は、職場にいたそうだ', '私は、職場にいたと聞いた',
            '私は、職場にいた夢を見た', '私は、会議を担当したなら',
            '「私は、職場にいた」', '私は、職場にいた？',
        ):
            with self.subTest(literal=literal):
                self.assertIsNone(self.generate(request(record(memo=literal + '。'))).artifact)
        artifact = self.generate(request(record(memo='私は、記録を担当した。'))).artifact
        node, = artifact.graph.nodes
        self.assertEqual((node.node_kind, node.proposition.arguments), ('ROLE', (('を', '記録'),)))
        artifact.safe_projection(authenticated_owner_scope=OWNER)
        # The event witness stays memo-only; memo_action cannot replace it.
        artifact = self.generate(request(record(memo='私は資料を調べた。',
            action='私は、職場にいた。'))).artifact
        self.assertEqual([n.node_kind for n in artifact.graph.nodes], ['ACTION_OR_NONACTION'])
        artifact.safe_projection(authenticated_owner_scope=OWNER)

    def test_event_topic_comma_keeps_order_and_period_comparison_semantics(self):
        route = '私は、職場にいた。その後、私は、会議を担当した。それから、私は、資料を調べた。'
        artifact = self.generate(request(record(memo=route))).artifact
        self.assertEqual([n.node_kind for n in artifact.graph.nodes], ['SCENE', 'ROLE', 'ACTION_OR_NONACTION'])
        self.assertEqual(len(artifact.graph.edges), 2)
        self.assertEqual(artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'],
            self.generate(request(record(memo=route.replace('は、', 'は')))).artifact
                .safe_text_projection(authenticated_owner_scope=OWNER)['text'])
        for before, now in (('私は職場にいた。', '僕は、職場にいました。'),
                            ('私は今日、会議を担当しなかった。', '私は、今日、会議を担当しませんでした。')):
            compared = self.compared(now, before).artifact
            self.assertEqual(compared.period_comparison.change_claims, ())
            self.assertEqual(compared.safe_projection(authenticated_owner_scope=OWNER)
                             ['period_comparison']['state'], 'COMPARABLE')
        changed = self.compared('私は、職場にいなかった。', '私は職場にいた。').artifact
        self.assertIn('ROUTE_EVIDENCE_CHANGED', changed.safe_projection(authenticated_owner_scope=OWNER)
                      ['period_comparison']['safe_change_kinds'])

    def test_event_topic_comma_supplements_and_corrections_keep_independent_evidence(self):
        for old, new in (('私は、職場にいた', '僕は、職場にいませんでした'),
                         ('私は、会議を担当した', '僕は、会議を担当しませんでした')):
            original = record(memo=old + '。私は資料を調べた。')
            answer = '「' + old + '」ではなく「' + new + '」です。'
            req = request(self.with_answer(original, answer))
            artifact = self.generate(req).artifact
            node = next(n for n in artifact.graph.nodes if n.node_kind in {'SCENE', 'ROLE'})
            self.assertEqual(node.polarity, 'negative')
            source = next(s.envelope for s in freeze_analysis_sources(req).sources
                          if s.envelope.source_role == 'SUPPLEMENTAL_ANSWER')
            for e in node.evidence_refs:
                self.assertEqual(e.source_envelope_id, source.envelope_id)
                raw = source.raw_utf8[e.utf8_start:e.utf8_end]
                self.assertEqual(raw.decode(), new)
                self.assertEqual(hashlib.sha256(raw).hexdigest(), e.literal_sha256)
            artifact.safe_projection(authenticated_owner_scope=OWNER)
            withdrawn = self.generate(request(self.with_answer(original, '「' + old + '」は取り消します。'))).artifact
            self.assertEqual([n.node_kind for n in withdrawn.graph.nodes], ['ACTION_OR_NONACTION'])
            supplemented = self.generate(request(self.with_answer(record(memo='私は資料を調べた。'), new + '。'))).artifact
            self.assertEqual(len(supplemented.graph.nodes), 2)
            supplemented.safe_projection(authenticated_owner_scope=OWNER)
            bad = '「' + old + '」ではなく「友人は、職場にいた」です。'
            self.assertIsNone(self.generate(request(self.with_answer(original, bad))).artifact)

    def test_post_topic_event_days_keep_kind_polarity_and_full_source(self):
        cases = (
            ('私は昨日職場にいた', 'SCENE', 'YESTERDAY', 'positive', '職場にいた（記録された場面）'),
            ('僕は今日，職場にいませんでした', 'SCENE', 'TODAY', 'negative', '職場にいなかった（記録された場面）'),
            ('わたしは昨日\u3000図書館にいました', 'SCENE', 'YESTERDAY', 'positive', '図書館にいた（記録された場面）'),
            ('私は今日、会議の司会を担当した', 'ROLE', 'TODAY', 'positive', '会議の司会を担当した（記録された担当）'),
            ('自分は昨日、会議の司会を担当しなかった', 'ROLE', 'YESTERDAY', 'negative', '会議の司会を担当しなかった（記録された担当）'),
            ('僕は今日会議を担当しました', 'ROLE', 'TODAY', 'positive', '会議を担当した（記録された担当）'),
        )
        for literal, kind, day, polarity, label in cases:
            with self.subTest(literal=literal):
                req = request(record(memo=literal + '。'))
                artifact = self.generate(req).artifact
                node, = artifact.graph.nodes
                p = node.proposition
                self.assertEqual((node.node_kind, node.polarity, node.modality,
                                  node.temporal_scope, p.relative_day),
                                 (kind, polarity, 'fact', 'past', day))
                self.assertEqual([i for _, a, b in p.source_parts for i in range(a, b)],
                                 list(range(len(literal))))
                e, = node.evidence_refs
                source = freeze_analysis_sources(req).sources[0].envelope
                field = source.raw_utf8[e.field_utf8_start:e.field_utf8_end].decode()
                self.assertEqual(source.raw_utf8[e.utf8_start:e.utf8_end].decode(), literal)
                self.assertEqual(field[e.scalar_start:e.scalar_end], literal)
                self.assertEqual(hashlib.sha256(literal.encode()).hexdigest(), e.literal_sha256)
                visual = artifact.safe_projection(authenticated_owner_scope=OWNER)
                text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)
                expected = 'この記述時点の' + ('今日' if day == 'TODAY' else '昨日') + '：' + label
                self.assertEqual(visual['nodes'][0]['visible_label'], expected)
                self.assertIn(expected, text['text'])
                self.assertEqual(visual['projection_of'], text['projection_of'])
                self.assertFalse(visual['edges'])
                for altered in (replace(p, relative_day=''), replace(p, source_parts=p.source_parts[1:])):
                    with self.assertRaises(AnalysisSourceError):
                        replace(artifact, graph=replace(artifact.graph,
                            nodes=(replace(node, proposition=altered),))).safe_projection(
                                authenticated_owner_scope=OWNER)

    def test_post_topic_event_days_do_not_promote_unresolved_day_or_nominal_scope(self):
        for memo in (
            '今日私は昨日職場にいた。', 'その後私は今日職場にいた。',
            '私は今日昨日職場にいた。', '私は昨日朝職場にいた。',
            '私は昨日、午前の会議を担当した。', '私は昨日開催の会議を担当した。',
            '私は昨日会議の司会を担当した。', '私は今日の会議を担当した。',
            '私は昨日分の会議を担当した。', '私は昨日以前の職場にいた。',
            '私は昨日職場にいる。', '私は昨日会議を担当したい。',
            '友人は昨日職場にいた。',
            '私は昨日、誰の会議を担当した。',
        ):
            with self.subTest(memo=memo):
                artifact = self.generate(request(record(memo=memo))).artifact
                self.assertFalse(artifact and any(n.node_kind in {'SCENE', 'ROLE'} for n in artifact.graph.nodes))

        artifact = self.generate(request(record(memo='私は昨日記録を担当した。'))).artifact
        node, = artifact.graph.nodes
        self.assertEqual((node.node_kind, node.proposition.relative_day), ('ROLE', 'YESTERDAY'))
        self.assertEqual(node.proposition.arguments, (('を', '記録'),))
        artifact.safe_projection(authenticated_owner_scope=OWNER)

    def test_post_topic_event_days_do_not_erase_report_dream_or_sentence_tail(self):
        tail = 'その内容を忘れないように長い文章として残しています' * 4
        for clause in ('私は昨日職場にいた', '私は今日、会議の司会を担当した'):
            for memo in ('友人から聞いた話です。' + clause, '夢を見た。' + clause,
                         clause + '？', clause + 'かもしれない',
                         clause + '、という夢を見たのですが、' + tail,
                         tail + '、' + clause):
                with self.subTest(memo=memo):
                    artifact = self.generate(request(record(memo=memo + '。'))).artifact
                    self.assertFalse(artifact and any(n.node_kind in {'SCENE', 'ROLE'} for n in artifact.graph.nodes))

    def test_post_topic_event_days_keep_supplement_revision_and_withdrawal_evidence(self):
        for old, new in (('私は昨日職場にいた', '私は今日、図書館にいなかった'),
                         ('私は昨日、会議の司会を担当した', '私は今日、会議の司会を担当しなかった')):
            original = record(memo=old + '。私は資料を調べた。')
            for answer in (new + '。', '「' + old + '」ではなく「' + new + '」です。'):
                with self.subTest(answer=answer):
                    base = original if answer.startswith('「') else record(memo='私は資料を調べた。')
                    req = request(self.with_answer(base, answer))
                    artifact = self.generate(req).artifact
                    node = next(n for n in artifact.graph.nodes if n.polarity == 'negative')
                    e, = node.evidence_refs
                    source = next(s.envelope for s in freeze_analysis_sources(req).sources
                                  if s.envelope.envelope_id == e.source_envelope_id)
                    self.assertEqual(source.source_role, 'SUPPLEMENTAL_ANSWER')
                    self.assertEqual(source.raw_utf8[e.utf8_start:e.utf8_end].decode(), new)
                    self.assertEqual(node.proposition.relative_day, 'TODAY')
                    artifact.safe_projection(authenticated_owner_scope=OWNER)
            withdrawn = self.generate(request(self.with_answer(original,
                '「' + old + '」は取り消します。'))).artifact
            self.assertEqual([n.node_kind for n in withdrawn.graph.nodes], ['ACTION_OR_NONACTION'])
            self.assertNotIn('昨日', withdrawn.safe_text_projection(authenticated_owner_scope=OWNER)['text'])
        # A supplement's day belongs to its own source; an opposed answer
        # is not silently treated as a correction of the original role.
        self.assertIsNone(self.generate(request(self.with_answer(original, new + '。'))).artifact)

    def test_post_topic_event_days_keep_comparison_and_do_not_inherit_time_or_order(self):
        for before, now in (
            ('昨日私は職場にいた。', '私は昨日職場にいた。'),
            ('今日私は会議の司会を担当した。', '私は今日、会議の司会を担当しました。'),
            ('今日私は職場にいなかった。', '私は今日職場にいませんでした。'),
        ):
            with self.subTest(now=now):
                p = self.compared(now, before).artifact.safe_projection(authenticated_owner_scope=OWNER)
                self.assertEqual(p['period_comparison']['safe_change_kinds'], [])
        p = self.compared('私は今日職場にいた。', '私は昨日職場にいた。').artifact.safe_projection(
            authenticated_owner_scope=OWNER)
        self.assertIn('ROUTE_EVIDENCE_CHANGED', p['period_comparison']['safe_change_kinds'])
        artifact = self.generate(request(record(memo=
            '私は昨日職場にいた。私は会議の司会を担当した。'))).artifact
        self.assertEqual([n.proposition.relative_day for n in artifact.graph.nodes], ['YESTERDAY', ''])
        self.assertFalse(artifact.safe_projection(authenticated_owner_scope=OWNER)['edges'])

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
                     '今日私は昨日職場にいた。',
                     '私は今日会議の司会を担当した。'):
            with self.subTest(memo=memo):
                artifact = self.generate(request(record(memo=memo))).artifact
                self.assertFalse(artifact and any(n.node_kind in {'SCENE', 'ROLE'} for n in artifact.graph.nodes))

        artifact = self.generate(request(record(memo='昨日私は記録を担当した。'))).artifact
        node, = artifact.graph.nodes
        self.assertEqual((node.node_kind, node.proposition.relative_day), ('ROLE', 'YESTERDAY'))
        self.assertEqual(node.proposition.arguments, (('を', '記録'),))
        artifact.safe_projection(authenticated_owner_scope=OWNER)

    def test_prefixed_events_still_require_shared_event_witness(self):
        from cocolon_meaning_experience_engine.cores.analysis import intent_compiler as compiler
        builder = compiler.build_final_stage1_grounded_observation_plan
        for clause in ('今日私は職場にいた。', 'その後私は会議の司会を担当した。',
                       '私は今日職場にいた。', '私は昨日、会議の司会を担当した。'):
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

    def test_polite_past_wishes_keep_full_meaning_evidence_and_plain_equivalence(self):
        for body, lemma in (
            ('考えをノートに書き', '書く'), ('資料を調べ', '調べる'),
            ('方法を試し', '試す'), ('景色を見', '見る'), ('作品を作り', '作る'),
            ('記録を残し', '残す'), ('気持ちを記録し', '記録する'),
            ('考えをメモし', 'メモする'), ('仕事を続け', '続ける'),
        ):
            for ending, polarity in (('たかった', 'positive'), ('たくなかった', 'negative')):
                with self.subTest(body=body, ending=ending):
                    literal = '私は、昨日、' + body + ending + 'です'
                    req = request(record(memo='　' + literal + '。'))
                    artifact = self.generate(req).artifact
                    self.assertIsNotNone(artifact)
                    node, = artifact.graph.nodes
                    p = node.proposition
                    self.assertEqual((node.node_kind, p.actor, p.predicate_lemma,
                        p.polarity, p.modality, p.temporal_scope, p.relative_day),
                        ('ATTENTION_OR_THOUGHT', 'SELF', lemma, polarity, 'wish', 'past', 'YESTERDAY'))
                    self.assertEqual([i for _, a, b in p.source_parts for i in range(a, b)],
                                     list(range(len(literal))))
                    e, = node.evidence_refs
                    envelope = freeze_analysis_sources(req).sources[0].envelope
                    raw = envelope.raw_utf8[e.utf8_start:e.utf8_end]
                    field = envelope.raw_utf8[e.field_utf8_start:e.field_utf8_end].decode()
                    self.assertEqual(raw.decode(), literal)
                    self.assertEqual(field[e.scalar_start:e.scalar_end], literal)
                    self.assertEqual(hashlib.sha256(raw).hexdigest(), e.literal_sha256)
                    visual = artifact.safe_projection(authenticated_owner_scope=OWNER)
                    text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)
                    plain = self.generate(request(record(memo=literal[:-2] + '。'))).artifact
                    self.assertEqual(text['text'], plain.safe_text_projection(authenticated_owner_scope=OWNER)['text'])
                    self.assertEqual(visual['projection_of'], text['projection_of'])
                    self.assertIn(visual['nodes'][0]['visible_label'], text['text'])
                    self.assertIn('（当時）', text['text'])
                    self.assertNotIn('実行済み', text['text'])
                    self.assertFalse(visual['edges'])
                    compared = self.compared(literal + '。', literal[:-2] + '。').artifact
                    self.assertEqual(compared.period_comparison.change_claims, ())
                    self.assertEqual(compared.period_comparison.comparability_state, 'COMPARABLE')

    def test_polite_past_wishes_keep_revision_withdrawal_and_semantic_differences(self):
        old = '私は仕事を続けたかったです'
        new = '僕は仕事を続けたくなかったです'
        original = record(memo=old + '。私は記録を残した。')
        for base, answer in (
            (record(memo='私は記録を残した。'), new + '。'),
            (original, '「' + old + '」ではなく「' + new + '」です。'),
        ):
            with self.subTest(answer=answer):
                req = request(self.with_answer(base, answer))
                artifact = self.generate(req).artifact
                node = next(n for n in artifact.graph.nodes if n.proposition.polarity == 'negative')
                source = next(s.envelope for s in freeze_analysis_sources(req).sources
                              if s.envelope.source_role == 'SUPPLEMENTAL_ANSWER')
                self.assertTrue(all(e.source_envelope_id == source.envelope_id for e in node.evidence_refs))
                self.assertIn('仕事を続けることを望まない（当時）',
                    artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'])
        withdrawn = self.generate(request(self.with_answer(original, '「' + old + '」は取り消します。'))).artifact
        self.assertEqual([n['visible_label'] for n in withdrawn.safe_projection(
            authenticated_owner_scope=OWNER)['nodes']], ['記録を残す（実行済み）'])
        # An opposing ordinary answer cannot silently act as a correction.
        self.assertIsNone(self.generate(request(self.with_answer(original, new + '。'))).artifact)
        ordered = self.generate(request(record(memo=old + '。その後私は記録を残した。'))).artifact
        self.assertFalse(ordered.safe_projection(authenticated_owner_scope=OWNER)['edges'])
        for other in (new, '私は仕事を続けたいです', '私は仕事を続けました'):
            with self.subTest(other=other):
                visual = self.compared(other + '。', old + '。').artifact.safe_projection(authenticated_owner_scope=OWNER)
                self.assertIn('ROUTE_EVIDENCE_CHANGED', visual['period_comparison']['safe_change_kinds'])
        artifact = self.generate(request(record(memo=old + '。'))).artifact
        node, = artifact.graph.nodes
        for changed in (replace(node.proposition, polarity='negative'),
                        replace(node.proposition, modality='fact'),
                        replace(node.proposition, temporal_scope='current_input'),
                        replace(node.proposition, source_parts=node.proposition.source_parts[:-1])):
            with self.subTest(changed=changed):
                broken = replace(artifact, graph=replace(artifact.graph,
                    nodes=(replace(node, proposition=changed),)))
                with self.assertRaises(AnalysisSourceError):
                    broken.safe_projection(authenticated_owner_scope=OWNER)

    def test_polite_past_wishes_do_not_admit_unparsed_or_reported_scope(self):
        for memo in ('仕事を続けたかったです。', '友人は仕事を続けたかったです。',
            '私は仕事を続けたかったですか。', '私は仕事を続けたかったです？',
            '「私は仕事を続けたかったです」と聞いた。',
            '私は仕事を続けたかったですが。', '私は仕事を続けたかったですです。',
            '明日私は仕事を続けたかったです。', '私は何を調べたかったです。',
            '私は仕事を続けたかったですかもしれないと思う。'):
            with self.subTest(memo=memo):
                self.assertIsNone(self.generate(request(record(memo=memo))).artifact)

    def test_formal_negative_wishes_keep_tense_full_source_and_plain_equivalence(self):
        for body, lemma in (
            ('考えをノートに書き', '書く'), ('資料を調べ', '調べる'),
            ('方法を試し', '試す'), ('景色を見', '見る'), ('作品を作り', '作る'),
            ('記録を残し', '残す'), ('気持ちを記録し', '記録する'),
            ('考えをメモし', 'メモする'), ('仕事を続け', '続ける'),
        ):
            for ending, plain, time, day in (
                ('たくありません', 'たくないです', 'current_input', '今日'),
                ('たくありませんでした', 'たくなかったです', 'past', '昨日'),
            ):
                with self.subTest(body=body, ending=ending):
                    literal = '僕は、' + day + '、' + body + ending
                    req = request(record(memo='　' + literal + '。'))
                    artifact = self.generate(req).artifact
                    self.assertIsNotNone(artifact)
                    node, = artifact.graph.nodes
                    p = node.proposition
                    self.assertEqual((node.node_kind, p.actor, p.predicate_lemma,
                        p.polarity, p.modality, p.temporal_scope),
                        ('ATTENTION_OR_THOUGHT', 'SELF', lemma, 'negative', 'wish', time))
                    self.assertEqual([i for _, a, b in p.source_parts for i in range(a, b)],
                                     list(range(len(literal))))
                    e, = node.evidence_refs
                    envelope = freeze_analysis_sources(req).sources[0].envelope
                    raw = envelope.raw_utf8[e.utf8_start:e.utf8_end]
                    field = envelope.raw_utf8[e.field_utf8_start:e.field_utf8_end].decode()
                    self.assertEqual(raw.decode(), literal)
                    self.assertEqual(field[e.scalar_start:e.scalar_end], literal)
                    self.assertEqual(hashlib.sha256(raw).hexdigest(), e.literal_sha256)
                    visual = artifact.safe_projection(authenticated_owner_scope=OWNER)
                    text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)
                    baseline = '僕は、' + day + '、' + body + plain + '。'
                    plain_artifact = self.generate(request(record(memo=baseline))).artifact
                    self.assertEqual(text['text'], plain_artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'])
                    self.assertEqual(text['projection_of'], visual['projection_of'])
                    self.assertIn(visual['nodes'][0]['visible_label'], text['text'])
                    self.assertIn('望まない', text['text'])
                    self.assertEqual('（当時）' in text['text'], time == 'past')
                    self.assertNotIn('実行済み', text['text'])
                    compared = self.compared(literal + '。', baseline).artifact
                    self.assertEqual(compared.period_comparison.change_claims, ())
                    self.assertEqual(compared.period_comparison.comparability_state, 'COMPARABLE')
                    for changed in (replace(p, polarity='positive'), replace(p, modality='fact'),
                                    replace(p, temporal_scope='past' if time == 'current_input' else 'current_input')):
                        broken = replace(artifact, graph=replace(artifact.graph,
                            nodes=(replace(node, proposition=changed),)))
                        with self.assertRaises(AnalysisSourceError):
                            broken.safe_projection(authenticated_owner_scope=OWNER)

    def test_formal_negative_wishes_keep_updates_and_do_not_become_nonactions(self):
        for suffix, positive, label in (
            ('たくありません', 'たいです', '仕事を続けることを望まない'),
            ('たくありませんでした', 'たかったです', '仕事を続けることを望まない（当時）'),
        ):
            with self.subTest(suffix=suffix):
                old, new = '私は仕事を続け' + positive, '自分は仕事を続け' + suffix
                original = record(memo=old + '。私は記録を残した。')
                for base, answer in (
                    (record(memo='私は記録を残した。'), new + '。'),
                    (original, '「' + old + '」ではなく「' + new + '」です。'),
                ):
                    req = request(self.with_answer(base, answer))
                    artifact = self.generate(req).artifact
                    node = next(n for n in artifact.graph.nodes if n.proposition.modality == 'wish')
                    source = next(s.envelope for s in freeze_analysis_sources(req).sources
                                  if s.envelope.source_role == 'SUPPLEMENTAL_ANSWER')
                    self.assertTrue(all(e.source_envelope_id == source.envelope_id for e in node.evidence_refs))
                    self.assertIn(label, artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'])
                    self.assertFalse(artifact.graph.edges)
                negative_original = record(memo=new + '。私は記録を残した。')
                withdrawn = self.generate(request(self.with_answer(negative_original,
                    '「' + new + '」は取り消します。'))).artifact
                self.assertEqual([n['visible_label'] for n in withdrawn.safe_projection(
                    authenticated_owner_scope=OWNER)['nodes']], ['記録を残す（実行済み）'])
                self.assertIsNone(self.generate(request(self.with_answer(original, new + '。'))).artifact)
                for other in (old, '私は仕事を続けませんでした'):
                    kinds = self.compared(new + '。', other + '。').artifact.safe_projection(
                        authenticated_owner_scope=OWNER)['period_comparison']['safe_change_kinds']
                    self.assertIn('ROUTE_EVIDENCE_CHANGED', kinds)
        changed = self.compared('私は仕事を続けたくありませんでした。',
                                '私は仕事を続けたくありません。').artifact
        self.assertTrue(changed.period_comparison.change_claims)
        ordered = self.generate(request(record(memo=
            '私は仕事を続けたくありませんでした。その後私は記録を残した。'))).artifact
        self.assertFalse(ordered.graph.edges)
        for memo in ('仕事を続けたくありません。', '友人は仕事を続けたくありませんでした。',
            '私は仕事を続けたくありませんか。', '私は仕事を続けたくありませんでした？',
            '「私は仕事を続けたくありません」と聞いた。', '私は仕事を続けたくありませんが。',
            '私は仕事を続けたくありませんでしたです。', '昨日私は仕事を続けたくありません。',
            '私は何を調べたくありません。', '私は誰の資料を見たくありませんでした。',
            '私は仕事を続けたくありませんかもしれないと思う。'):
            with self.subTest(memo=memo):
                self.assertIsNone(self.generate(request(record(memo=memo))).artifact)

    def test_polite_past_nonaction_preserves_complete_source_and_plain_meaning(self):
        for body, lemma in (
            ('考えをノートに書か', '書く'), ('資料を調べ', '調べる'),
            ('方法を試さ', '試す'), ('景色を見', '見る'), ('作品を作ら', '作る'),
            ('記録を残さ', '残す'), ('気持ちを記録し', '記録する'),
            ('考えをメモし', 'メモする'), ('仕事を続け', '続ける'),
        ):
            for field in ('memo', 'memo_action'):
                with self.subTest(body=body, field=field):
                    literal = '僕は、昨日、' + body + 'なかったです'
                    req = request(record(memo='　' + literal + '。' if field == 'memo' else '',
                        action='　' + literal + '。' if field == 'memo_action' else ''))
                    artifact = self.generate(req).artifact
                    self.assertIsNotNone(artifact)
                    node, = artifact.graph.nodes
                    p = node.proposition
                    self.assertEqual((node.node_kind, p.actor, p.predicate_lemma,
                        p.polarity, p.modality, p.temporal_scope, p.relative_day),
                        ('ACTION_OR_NONACTION', 'SELF', lemma, 'negative', 'fact', 'past', 'YESTERDAY'))
                    self.assertEqual([i for _, a, b in p.source_parts for i in range(a, b)],
                                     list(range(len(literal))))
                    e, = node.evidence_refs
                    envelope = freeze_analysis_sources(req).sources[0].envelope
                    raw = envelope.raw_utf8[e.utf8_start:e.utf8_end]
                    source_field = envelope.raw_utf8[e.field_utf8_start:e.field_utf8_end].decode()
                    self.assertEqual(raw.decode(), literal)
                    self.assertEqual(source_field[e.scalar_start:e.scalar_end], literal)
                    self.assertEqual(hashlib.sha256(raw).hexdigest(), e.literal_sha256)
                    visual = artifact.safe_projection(authenticated_owner_scope=OWNER)
                    text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)
                    self.assertEqual(text['projection_of'], visual['projection_of'])
                    self.assertIn(visual['nodes'][0]['visible_label'], text['text'])
                    self.assertIn('行わなかった', text['text'])
                    self.assertNotIn('望まない', text['text'])
                    plain = literal[:-2] + '。'
                    self.assertEqual(text['text'], self.generate(request(record(memo=plain))).artifact
                        .safe_text_projection(authenticated_owner_scope=OWNER)['text'])
                    comparison = self.compared(literal + '。', plain).artifact.period_comparison
                    self.assertEqual((comparison.comparability_state, comparison.change_claims), ('COMPARABLE', ()))
                    for changed in (replace(p, polarity='positive'), replace(p, modality='wish'),
                                    replace(p, temporal_scope='current_input')):
                        broken = replace(artifact, graph=replace(artifact.graph,
                            nodes=(replace(node, proposition=changed),)))
                        with self.assertRaises(AnalysisSourceError):
                            broken.safe_projection(authenticated_owner_scope=OWNER)

    def test_polite_past_nonaction_preserves_updates_order_and_conflicts(self):
        old, new = '私は資料を調べた', '私は資料を調べなかったです'
        original = record(memo=old + '。私は記録を残した。')
        for base, answer in (
            (record(memo='私は記録を残した。'), new + '。'),
            (original, '「' + old + '」ではなく「' + new + '」です。'),
        ):
            with self.subTest(answer=answer):
                req = request(self.with_answer(base, answer))
                artifact = self.generate(req).artifact
                self.assertIsNotNone(artifact)
                node = next(n for n in artifact.graph.nodes if n.polarity == 'negative')
                source = next(s.envelope for s in freeze_analysis_sources(req).sources
                              if s.envelope.source_role == 'SUPPLEMENTAL_ANSWER')
                self.assertTrue(all(e.source_envelope_id == source.envelope_id for e in node.evidence_refs))
                self.assertIn('資料を調べる（行わなかった）', artifact.safe_text_projection(
                    authenticated_owner_scope=OWNER)['text'])
        withdrawn = self.generate(request(self.with_answer(record(memo=new + '。私は記録を残した。'),
            '「' + new + '」は取り消します。'))).artifact
        self.assertEqual([n['visible_label'] for n in withdrawn.safe_projection(
            authenticated_owner_scope=OWNER)['nodes']], ['記録を残す（実行済み）'])
        for tail in ('その後私は記録を残した。', old + '。'):
            with self.subTest(tail=tail):
                actual = self.generate(request(record(memo=new + '。' + tail))).artifact
                baseline = self.generate(request(record(memo='私は資料を調べなかった。' + tail))).artifact
                self.assertEqual(actual.safe_text_projection(authenticated_owner_scope=OWNER)['text'],
                                 baseline.safe_text_projection(authenticated_owner_scope=OWNER)['text'])
                self.assertEqual(bool(actual.graph.edges), tail.startswith('その後'))
        for other in (old, '私は資料を調べたくなかったです'):
            with self.subTest(other=other):
                comparison = self.compared(new + '。', other + '。').artifact.period_comparison
                self.assertTrue(comparison.change_claims)

    def test_polite_past_nonaction_does_not_admit_unresolved_hosts(self):
        for literal in ('資料を調べなかったです', '友人は資料を調べなかったです',
            '私は資料を調べなかったですか', '私は資料を調べなかったです？',
            '「私は資料を調べなかったです」と聞いた', '私は資料を調べなかったですが',
            '私は資料を調べなかったですです', '私は何を調べなかったです',
            '私は誰の資料を見なかったです', '私は明日、資料を調べなかったです',
            '私は資料を調べなかったですかもしれないと思う',
            '私は資料を調べなかったです、とは言えません'):
            with self.subTest(literal=literal):
                self.assertIsNone(self.generate(request(record(memo=literal + '。'))).artifact)

    def test_polite_negative_past_events_keep_kind_time_and_exact_source(self):
        for body, kind, lemma in (
            ('職場にいなかった', 'SCENE', 'いる'),
            ('会議の司会を担当しなかった', 'ROLE', '担当する'),
        ):
            for field in ('memo', 'memo_action'):
                for topic in ('私は', '僕は、昨日、', '今日、私は、'):
                    with self.subTest(body=body, field=field, topic=topic):
                        literal = topic + body + 'です'
                        req = request(record(memo='　' + literal + '。' if field == 'memo' else '',
                            action='　' + literal + '。' if field == 'memo_action' else ''))
                        artifact = self.generate(req).artifact
                        if field == 'memo_action':
                            # Scene/role shared witnesses remain memo-only,
                            # just as for the existing plain negative form.
                            self.assertIsNone(artifact)
                            self.assertIsNone(self.generate(request(record(memo='',
                                action=topic + body + '。'))).artifact)
                            continue
                        self.assertIsNotNone(artifact)
                        node, = artifact.graph.nodes
                        p = node.proposition
                        self.assertEqual((node.node_kind, p.actor, p.predicate_lemma,
                            p.polarity, p.modality, p.temporal_scope),
                            (kind, 'SELF', lemma, 'negative', 'fact', 'past'))
                        self.assertEqual(p.relative_day,
                            'YESTERDAY' if '昨日' in topic else 'TODAY' if '今日' in topic else '')
                        self.assertEqual([i for _, a, b in p.source_parts for i in range(a, b)],
                                         list(range(len(literal))))
                        e, = node.evidence_refs
                        source = freeze_analysis_sources(req).sources[0].envelope
                        raw = source.raw_utf8[e.utf8_start:e.utf8_end]
                        source_field = source.raw_utf8[e.field_utf8_start:e.field_utf8_end].decode()
                        self.assertEqual(raw.decode(), literal)
                        self.assertEqual(source_field[e.scalar_start:e.scalar_end], literal)
                        self.assertEqual(hashlib.sha256(raw).hexdigest(), e.literal_sha256)
                        visual = artifact.safe_projection(authenticated_owner_scope=OWNER)
                        text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)
                        self.assertEqual(text['projection_of'], visual['projection_of'])
                        self.assertIn(visual['nodes'][0]['visible_label'], text['text'])
                        self.assertNotIn('実行済み', text['text'])
                        plain = topic + body + '。'
                        self.assertEqual(text['text'], self.generate(request(record(memo=plain))).artifact
                            .safe_text_projection(authenticated_owner_scope=OWNER)['text'])
                        self.assertEqual(self.compared(literal + '。', plain).artifact
                                         .period_comparison.change_claims, ())
                        for changed in (replace(p, polarity='positive'), replace(p, modality='wish'),
                                        replace(p, temporal_scope='current_input')):
                            with self.assertRaises(AnalysisSourceError):
                                replace(artifact, graph=replace(artifact.graph, nodes=(replace(node,
                                    proposition=changed),))).safe_projection(authenticated_owner_scope=OWNER)

    def test_polite_negative_past_events_keep_supplement_correction_and_withdrawal(self):
        for old, new in (('私は職場にいた', '私は職場にいなかったです'),
                         ('私は会議を担当した', '私は会議を担当しなかったです')):
            with self.subTest(new=new):
                for base, answer in (
                    (record(memo='私は記録を残した。'), new + '。'),
                    (record(memo=old + '。私は記録を残した。'),
                     '「' + old + '」ではなく「' + new + '」です。'),
                ):
                    req = request(self.with_answer(base, answer))
                    artifact = self.generate(req).artifact
                    self.assertIsNotNone(artifact)
                    node = next(n for n in artifact.graph.nodes if n.polarity == 'negative')
                    source = next(s.envelope for s in freeze_analysis_sources(req).sources
                                  if s.envelope.source_role == 'SUPPLEMENTAL_ANSWER')
                    for e in node.evidence_refs:
                        self.assertEqual(e.source_envelope_id, source.envelope_id)
                        self.assertEqual(source.raw_utf8[e.utf8_start:e.utf8_end].decode(), new)
                withdrawn = self.generate(request(self.with_answer(
                    record(memo=new + '。私は記録を残した。'), '「' + new + '」は取り消します。'))).artifact
                self.assertEqual([n['visible_label'] for n in withdrawn.safe_projection(
                    authenticated_owner_scope=OWNER)['nodes']], ['記録を残す（実行済み）'])
                for tail in ('その後私は記録を残した。', old + '。'):
                    actual = self.generate(request(record(memo=new + '。' + tail))).artifact
                    baseline = self.generate(request(record(memo=new[:-2] + '。' + tail))).artifact
                    self.assertEqual(actual.safe_text_projection(authenticated_owner_scope=OWNER)['text'],
                                     baseline.safe_text_projection(authenticated_owner_scope=OWNER)['text'])
                    self.assertEqual(bool(actual.graph.edges), tail.startswith('その後'))
                self.assertIn('ROUTE_EVIDENCE_CHANGED', self.compared(new + '。', old + '。').artifact
                    .safe_projection(authenticated_owner_scope=OWNER)['period_comparison']['safe_change_kinds'])

    def test_polite_negative_past_events_preserve_unresolved_scopes(self):
        for body in ('職場にいなかったです', '会議を担当しなかったです'):
            for literal in (body, '友人は' + body, '私は' + body + 'か',
                '私は' + body + '？', '私は' + body + 'です', '私は' + body + 'が',
                '私は' + body + 'かもしれないと思う', '私は' + body + 'とは言えません',
                '夢を見た。私は' + body, '「私は' + body + '」と聞いた',
                '私は明日、' + body, '私は誰の' + body):
                with self.subTest(literal=literal):
                    self.assertIsNone(self.generate(request(record(memo=literal + '。'))).artifact)
        partial = self.generate(request(record(memo=
            '私は職場にいなかったです。私は急いで資料を調べた。その後私は記録を残した。'))).artifact
        self.assertEqual([n.node_kind for n in partial.graph.nodes], ['SCENE', 'ACTION_OR_NONACTION'])
        self.assertEqual(partial.graph.edges, ())
        self.assertIn('SOURCE_SCOPE', [g.missing_scope for g in partial.graph.unknown_gaps])

    def test_safe_surface_cannot_drop_modifiers_or_accept_altered_parts(self):
        for source in ('私は明日、考えをノートに書いた。',
                       '私は急いで考えをノートに書いた。'):
            with self.subTest(source=source):
                result = self.generate(request(record(memo=source)))
                self.assertEqual(result.status, EngineStatus.UNAVAILABLE)
                self.assertEqual(result.reason_codes, ('analysis_observed_route_not_established',))
                self.assertIsNone(result.artifact)
        artifact = self.generate(request(record())).artifact
        node = artifact.graph.nodes[0]
        broken = replace(artifact, graph=replace(artifact.graph,
            nodes=(replace(node, proposition=replace(node.proposition, polarity='negative')),)))
        with self.assertRaisesRegex(AnalysisSourceError, 'analysis_safe_surface_unavailable'):
            broken.safe_projection(authenticated_owner_scope=OWNER)

    def test_self_topic_comma_keeps_meaning_and_complete_original_evidence(self):
        cases = (
            ('私', '、', '考えをノートに書いた'),
            ('僕', '，', '資料を調べました'),
            ('わたし', '、 ', '方法を試さなかった'),
            ('自分', '、\u3000', '景色を見ませんでした'),
            ('私', '， ', '作品を作りたい'),
            ('僕', '、', '記録を残したくない'),
            ('わたし', '，', '気持ちを記録したかった'),
            ('自分', '、', '考えをメモしたくなかった'),
            ('私', '、', '仕事を続けたいです'),
            ('私', '、', '昨日資料を調べた'),
            ('私', '、 ', '今日、資料を調べなかった'),
        )
        for actor, separator, body in cases:
            with self.subTest(actor=actor, separator=separator, body=body):
                literal = actor + 'は' + separator + body
                original = record(memo=literal + '。')
                req = request(original)
                artifact = self.generate(req).artifact
                baseline = self.generate(request(record(memo=actor + 'は' + body + '。'))).artifact
                self.assertIsNotNone(artifact)
                node, = artifact.graph.nodes
                p = node.proposition
                self.assertEqual(p.source_parts[0], ('SELF_TOPIC', 0, len(actor + 'は' + separator)))
                self.assertEqual([i for _, a, b in p.source_parts for i in range(a, b)],
                                 list(range(len(literal))))
                self.assertEqual((p.actor, p.arguments, p.predicate_lemma, p.polarity,
                                  p.modality, p.temporal_scope, p.relative_day),
                    tuple(getattr(baseline.graph.nodes[0].proposition, key) for key in
                          ('actor', 'arguments', 'predicate_lemma', 'polarity',
                           'modality', 'temporal_scope', 'relative_day')))
                evidence, = node.evidence_refs
                source = freeze_analysis_sources(req).sources[0].envelope
                raw = source.raw_utf8[evidence.utf8_start:evidence.utf8_end]
                field = source.raw_utf8[evidence.field_utf8_start:evidence.field_utf8_end].decode()
                self.assertEqual(raw.decode(), literal)
                self.assertEqual(field[evidence.scalar_start:evidence.scalar_end], literal)
                self.assertEqual(hashlib.sha256(raw).hexdigest(), evidence.literal_sha256)
                visual = artifact.safe_projection(authenticated_owner_scope=OWNER)
                text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)
                self.assertEqual(text['projection_of'], visual['projection_of'])
                self.assertEqual(text['text'], baseline.safe_text_projection(authenticated_owner_scope=OWNER)['text'])
                self.assertIn(visual['nodes'][0]['visible_label'], text['text'])
                self.assertEqual(req.members[0].original_json, original.original_json)

    def test_self_topic_comma_does_not_skip_unparsed_scope_or_subject_boundaries(self):
        for literal in (
            '資料を調べた', '友人は、資料を調べた', '私は、友人は資料を調べた',
            '私は、\n資料を調べた', '私は、\r\n資料を調べた', '私は、。資料を調べた',
            '私は、、資料を調べた', '私は、，資料を調べた', '私は、\t資料を調べた',
            '私は、急いで資料を調べた', '私は、明日資料を調べた',
            '私は、昨日資料を調べたい', '私は、資料を調べたそうだ',
            '私は、資料を調べたと聞いた', '私は、資料を調べた夢を見た',
            '私は、資料を調べたなら', '私は、資料を調べた？', '「私は、資料を調べた」',
        ):
            with self.subTest(literal=literal):
                result = self.generate(request(record(memo=literal + '。')))
                self.assertEqual(result.status, EngineStatus.UNAVAILABLE)
                self.assertIsNone(result.artifact)

    def test_self_topic_comma_preserves_proved_order_change_and_burden(self):
        for literal, node_count, edge_count, annotation_count in (
            ('昨日、私は、資料を調べた', 1, 0, 0),
            ('私は、資料を調べた。その後、私は、記録を残した', 2, 1, 0),
            ('私は、資料を調べた後、疑問が減った', 2, 1, 0),
            ('私は、仕事を続けたいけれど、私はつらい', 1, 0, 1),
        ):
            with self.subTest(literal=literal):
                artifact = self.generate(request(record(memo=literal + '。'))).artifact
                baseline = self.generate(request(record(memo=literal.replace('は、', 'は') + '。'))).artifact
                self.assertEqual((len(artifact.graph.nodes), len(artifact.graph.edges),
                                  len(artifact.graph.annotations)), (node_count, edge_count, annotation_count))
                self.assertEqual(artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'],
                                 baseline.safe_text_projection(authenticated_owner_scope=OWNER)['text'])
        partial = self.generate(request(record(memo='私は、資料を調べた。私は、明日記録を残した。'))).artifact
        self.assertEqual(len(partial.graph.nodes), 1)
        self.assertFalse(partial.graph.edges)
        self.assertTrue(any(g.missing_scope == 'SOURCE_SCOPE' for g in partial.graph.unknown_gaps))
        partial.safe_projection(authenticated_owner_scope=OWNER)

    def test_self_topic_comma_answers_corrections_and_withdrawals_keep_answer_evidence(self):
        original = record(memo='私は、資料を調べた。私は記録を残した。')
        for answer, expected in (
            ('私は、仕事を続けたい。', '仕事を続けることへの希望'),
            ('「私は、資料を調べた」ではなく「僕は、資料を調べなかった」です。',
             '資料を調べる（行わなかった）'),
        ):
            with self.subTest(answer=answer):
                req = request(self.with_answer(original, answer))
                artifact = self.generate(req).artifact
                visual = artifact.safe_projection(authenticated_owner_scope=OWNER)
                index = next(i for i, n in enumerate(visual['nodes']) if n['visible_label'] == expected)
                source = next(s.envelope for s in freeze_analysis_sources(req).sources
                              if s.envelope.source_role == 'SUPPLEMENTAL_ANSWER')
                for e in artifact.graph.nodes[index].evidence_refs:
                    self.assertEqual(e.source_envelope_id, source.envelope_id)
                    raw = source.raw_utf8[e.utf8_start:e.utf8_end]
                    self.assertIn(raw.decode(), answer)
                    self.assertIn('は、', raw.decode())
                    self.assertEqual(hashlib.sha256(raw).hexdigest(), e.literal_sha256)
        withdrawn = self.generate(request(self.with_answer(original,
            '「私は、資料を調べた」は取り消します。'))).artifact
        self.assertEqual([n['visible_label'] for n in withdrawn.safe_projection(
            authenticated_owner_scope=OWNER)['nodes']], ['記録を残す（実行済み）'])
        for answer in ('私は、仕事を続けたい。まだわからない。',
                       '「私は、資料を調べた」ではなく「友人は、資料を調べた」です。'):
            self.assertIsNone(self.generate(request(self.with_answer(original, answer))).artifact)

    def test_self_topic_comma_is_not_a_period_change_or_new_meaning(self):
        for before, now in (
            ('私は資料を調べた。', '僕は、資料を調べました。'),
            ('昨日、私は資料を調べなかった。', '私は、昨日資料を調べなかった。'),
            ('私は仕事を続けたい。', 'わたしは，仕事を続けたいです。'),
        ):
            with self.subTest(before=before):
                artifact = self.compared(now, before).artifact
                self.assertEqual(artifact.period_comparison.change_claims, ())
                self.assertEqual(artifact.safe_projection(authenticated_owner_scope=OWNER)
                    ['period_comparison']['state'], 'COMPARABLE')
        changed = self.compared('私は、資料を調べなかった。', '私は資料を調べた。').artifact
        self.assertIn('ROUTE_EVIDENCE_CHANGED', changed.safe_projection(authenticated_owner_scope=OWNER)
                      ['period_comparison']['safe_change_kinds'])
        repeated = self.generate(request(record(memo='私は資料を調べた。'),
            record(2, memo='私は、資料を調べた。'))).artifact
        self.assertEqual(len(repeated.graph.nodes), 1)
        self.assertEqual(repeated.safe_projection(authenticated_owner_scope=OWNER)
                         ['nodes'][0]['evidence_badge_count'], 2)

    def test_self_topic_comma_does_not_relax_safe_proposition_revalidation(self):
        artifact = self.generate(request(record(memo='私は、資料を調べた。'))).artifact
        node, = artifact.graph.nodes
        for altered in (replace(node.proposition, actor='UNSPECIFIED'),
                        replace(node.proposition, polarity='negative'),
                        replace(node.proposition, source_parts=(('SELF_TOPIC', 0, 2),
                            *node.proposition.source_parts[1:]))):
            with self.subTest(altered=altered), self.assertRaisesRegex(
                    AnalysisSourceError, 'analysis_safe_surface_unavailable'):
                replace(artifact, graph=replace(artifact.graph,
                    nodes=(replace(node, proposition=altered),))).safe_projection(authenticated_owner_scope=OWNER)

    def test_unparsed_original_keeps_readable_clauses_fields_and_records(self):
        unread = '私は資料を明日ノートに書いた。'
        read = '私は記録を残した。'
        cases = (
            request(record(memo=unread + read)),
            request(record(memo=read + unread)),
            request(record(memo=read, action=unread)),
            request(record(memo=unread, action=read)),
            request(record(memo=unread), record(2, memo=read)),
            request(record(memo=read), record(2, memo=unread)),
        )
        for req in cases:
            with self.subTest(members=[r.original_json for r in req.members]):
                result = self.generate(req)
                self.assertEqual(result.status, EngineStatus.GENERATED)
                artifact = result.artifact
                node, = artifact.graph.nodes
                self.assertIsNotNone(node.proposition)
                visual = artifact.safe_projection(authenticated_owner_scope=OWNER)
                text = artifact.safe_text_projection(authenticated_owner_scope=OWNER)
                self.assertEqual([n['visible_label'] for n in visual['nodes']],
                                 ['記録を残す（実行済み）'])
                self.assertEqual(visual['projection_of'], text['projection_of'])
                self.assertTrue(any(g.missing_scope == 'SOURCE_SCOPE' and
                    g.reason_code == 'UNSUPPORTED_OR_UNCERTAIN_SOURCE_SCOPE'
                    for g in artifact.graph.unknown_gaps))
                self.assertFalse(artifact.graph.edges)
                self.assertNotIn('明日ノート', text['text'])
                sources = {s.envelope.envelope_id: s.envelope
                           for s in freeze_analysis_sources(req).sources}
                for evidence in node.evidence_refs:
                    envelope = sources[evidence.source_envelope_id]
                    raw = envelope.raw_utf8[evidence.utf8_start:evidence.utf8_end]
                    field = envelope.raw_utf8[evidence.field_utf8_start:evidence.field_utf8_end].decode()
                    self.assertEqual(raw.decode(), read.rstrip('。'))
                    self.assertEqual(raw.decode(), field[evidence.scalar_start:evidence.scalar_end])
                    self.assertEqual(hashlib.sha256(raw).hexdigest(), evidence.literal_sha256)

    def test_unparsed_original_cannot_bridge_order_or_invent_repetition(self):
        unread = '私は急いで考えをノートに書いた。'
        artifact = self.generate(request(record(memo='私は資料を調べた。' + unread
            + 'その後私は記録を残した。'))).artifact
        self.assertEqual(len(artifact.graph.nodes), 2)
        self.assertFalse(artifact.graph.edges)
        self.assertIn('EXPLICIT_PREDECESSOR_NOT_ESTABLISHED',
                      {g.reason_code for g in artifact.graph.unknown_gaps})
        artifact.safe_projection(authenticated_owner_scope=OWNER)
        repeated = self.generate(request(record(memo=unread + '私は記録を残した。'),
            record(2, memo=unread + '私は記録を残した。'))).artifact
        node, = repeated.graph.nodes
        self.assertEqual(len(node.record_refs), 2)
        self.assertFalse(repeated.graph.edges)

    def test_unparsed_original_adds_only_unknown_change_to_period_comparison(self):
        read = '私は記録を残した。'
        unread = '私は資料を明日ノートに書いた。'
        for before, now in ((read, unread + read), (unread + read, read)):
            with self.subTest(before=before):
                artifact = self.compared(now, before).artifact
                visual = artifact.safe_projection(authenticated_owner_scope=OWNER)
                self.assertEqual(visual['period_comparison'], {'state': 'COMPARABLE',
                    'reason_codes': [], 'safe_change_kinds': ['UNKNOWN_SCOPE_CHANGED']})

    def test_unparsed_supplement_or_correction_still_blocks_the_whole_update(self):
        unread = '私は資料を明日ノートに書いた'
        read = '私は記録を残した'
        cases = (
            (read + '。', unread + '。'),
            (read + '。', '私は資料を調べた。' + unread + '。'),
            (read + '。', '「' + read + '」ではなく「' + unread + '」です。'),
            (unread + '。' + read + '。', '「' + unread + '」ではなく「私は資料を調べた」です。'),
            (unread + '。' + read + '。', '「' + unread + '」は取り消します。'),
        )
        for original, answer in cases:
            with self.subTest(answer=answer):
                result = self.generate(request(self.with_answer(record(memo=original), answer)))
                self.assertEqual(result.status, EngineStatus.UNAVAILABLE)
                self.assertIsNone(result.artifact)

    def test_unparsed_original_keeps_typed_burden_and_rejects_raw_surface_tampering(self):
        artifact = self.generate(request(record(memo='私は資料を明日ノートに書いた。'
            '私は仕事を続けたいけれど、私はつらい。'))).artifact
        self.assertEqual(len(artifact.graph.nodes), 1)
        self.assertEqual(len(artifact.graph.annotations), 1)
        self.assertIn('つらいと記述されています',
                      artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'])
        node = artifact.graph.nodes[0]
        broken = replace(artifact, graph=replace(artifact.graph,
            nodes=(replace(node, proposition=None),)))
        with self.assertRaisesRegex(AnalysisSourceError, 'analysis_safe_surface_unavailable'):
            broken.safe_projection(authenticated_owner_scope=OWNER)


if __name__ == '__main__':
    unittest.main()
