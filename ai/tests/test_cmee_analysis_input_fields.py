"""Real Analysis parsing of the two actual input fields, with source fidelity."""
import json
import unittest
from dataclasses import replace

from cocolon_meaning_experience_engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.cores.analysis.source_adapter import (
    AnalysisObservedMapRequest, AnalysisSavedRecord, AnalysisSupplement, canonical_bytes, commitment,
    freeze_analysis_sources,
)

OWNER = 'synthetic-field-audit-owner'
CATEGORIES = ['生活', '仕事', '趣味', '人間関係', '恋愛', '健康', '学習', '価値観', '人生']


def saved(memo='', action='', *, emotion='平穏', strength='medium'):
    original = dict(id='synthetic-field-audit-record', created_at='2026-11-07T01:00:00Z',
        memo=memo, memo_action=action, category=list(CATEGORIES), emotions=[emotion],
        emotion_details=[dict(type=emotion, strength=strength)])
    return AnalysisSavedRecord(OWNER, original['id'], commitment(original),
        canonical_bytes(original).decode())


def request(record):
    return AnalysisObservedMapRequest('synthetic-field-audit-request', OWNER,
        '2026-11-07T00:00:00Z', '2026-11-08T00:00:00Z', (record,),
        selected_category_context=True)


class ActualInputFieldTests(unittest.TestCase):
    def generate(self, record):
        result = MeaningExperienceEngine().generate(request(record))
        return result

    def test_complete_written_scene_role_and_feeling_keep_their_meaning_in_either_field(self):
        cases = [
            ('私は会議を担当した。', 'ROLE', 'positive', 'past'),
            ('私は会議を担当しなかった。', 'ROLE', 'negative', 'past'),
            ('私は職場にいた。', 'SCENE', 'positive', 'past'),
            ('私は職場にいなかった。', 'SCENE', 'negative', 'past'),
            ('私は不安だった。', 'IMMEDIATE_RESULT_OR_AFTERMATH', 'positive', 'past'),
            ('私は不安ではなかった。', 'IMMEDIATE_RESULT_OR_AFTERMATH', 'negative', 'past'),
            ('私は不安だ。', 'IMMEDIATE_RESULT_OR_AFTERMATH', 'positive', 'current_input'),
            ('私はとても不安だった。', 'IMMEDIATE_RESULT_OR_AFTERMATH', 'positive', 'past'),
            ('私は嬉しかった。', 'IMMEDIATE_RESULT_OR_AFTERMATH', 'positive', 'past'),
            ('私は嬉しくなかった。', 'IMMEDIATE_RESULT_OR_AFTERMATH', 'negative', 'past'),
            ('私は落ち着いた。', 'IMMEDIATE_RESULT_OR_AFTERMATH', 'positive', 'past'),
            ('私は落ち着かなかった。', 'IMMEDIATE_RESULT_OR_AFTERMATH', 'negative', 'past'),
            ('私は安心した。', 'IMMEDIATE_RESULT_OR_AFTERMATH', 'positive', 'past'),
            ('私は安心しなかった。', 'IMMEDIATE_RESULT_OR_AFTERMATH', 'negative', 'past'),
            ('私は時間を守りたい。', 'ATTENTION_OR_THOUGHT', 'positive', 'current_input'),
            ('まだ方針が決まっていない。', 'IMMEDIATE_RESULT_OR_AFTERMATH', 'negative', 'current_input'),
        ]
        for text, kind, polarity, time in cases:
            meanings = []
            for field in ('memo', 'memo_action'):
                with self.subTest(text=text, field=field):
                    record = saved(**({'memo': text} if field == 'memo' else {'action': text}))
                    result = self.generate(record)
                    self.assertEqual(result.status, EngineStatus.GENERATED)
                    artifact = result.artifact
                    node, = artifact.graph.nodes
                    self.assertEqual((node.node_kind, node.polarity, node.temporal_scope),
                        (kind, polarity, time))
                    meanings.append((node.node_kind, node.proposition.actor,
                        node.proposition.arguments, node.proposition.predicate_lemma,
                        node.polarity, node.modality, node.temporal_scope))
                    source, = freeze_analysis_sources(request(record)).sources
                    evidence, = node.evidence_refs
                    self.assertEqual(evidence.field_path, field)
                    raw = source.envelope.raw_utf8
                    self.assertEqual(raw[evidence.utf8_start:evidence.utf8_end].decode(),
                        text.rstrip('。'))
                    self.assertEqual(raw[evidence.field_utf8_start:evidence.field_utf8_end].decode(), text)
                    self.assertIn(kind, [n['node_kind'] for n in artifact.safe_projection(
                        authenticated_owner_scope=OWNER)['nodes']])
            self.assertEqual(meanings[0], meanings[1])

    def test_two_fields_keep_their_own_sources_without_inventing_an_order(self):
        record = saved('私は会議を担当した。', '私は職場にいた。私は不安だった。')
        artifact = self.generate(record).artifact
        self.assertIsNotNone(artifact)
        self.assertEqual([n.node_kind for n in artifact.graph.nodes],
            ['ROLE', 'SCENE', 'IMMEDIATE_RESULT_OR_AFTERMATH'])
        self.assertEqual([n.evidence_refs[0].field_path for n in artifact.graph.nodes],
            ['memo', 'memo_action', 'memo_action'])
        self.assertFalse(artifact.graph.edges)
        self.assertEqual(json.loads(record.original_json)['memo_action'],
            '私は職場にいた。私は不安だった。')

    def test_same_fact_in_both_fields_is_one_occasion_with_two_field_evidences(self):
        artifact = self.generate(saved('私は会議を担当した。', '私は会議を担当した。')).artifact
        node, = artifact.graph.nodes
        self.assertEqual(node.node_kind, 'ROLE')
        self.assertEqual(len(node.record_refs), 1)
        self.assertEqual({e.field_path for e in node.evidence_refs}, {'memo', 'memo_action'})
        self.assertFalse(artifact.graph.edges)

    def test_all_selected_categories_and_each_emotion_strength_are_not_role_evidence(self):
        for emotion in ('喜び', '悲しみ', '怒り', '不安', '平穏'):
            for strength in ('weak', 'medium', 'strong'):
                for field in ('memo', 'memo_action'):
                    with self.subTest(emotion=emotion, strength=strength, field=field):
                        record = saved(**({'memo': '私は会議を担当した。'}
                            if field == 'memo' else {'action': '私は会議を担当した。'}),
                            emotion=emotion, strength=strength)
                        artifact = self.generate(record).artifact
                        node, = artifact.graph.nodes
                        self.assertEqual(node.node_kind, 'ROLE')
                        self.assertEqual(node.proposition.predicate_lemma, '担当する')
                        original = json.loads(record.original_json)
                        self.assertEqual(original['category'], CATEGORIES)
                        self.assertEqual(original['emotion_details'], [dict(type=emotion, strength=strength)])
                        source, = freeze_analysis_sources(request(record)).sources
                        self.assertEqual(source.normalized['emotion_details'], original['emotion_details'])
        for record in (saved(emotion='喜び', strength='strong'), saved(emotion='自己理解')):
            self.assertIsNone(self.generate(record).artifact)
        for field in ('memo', 'memo_action'):
            rec = saved(**({'memo': '私は会議を担当した。'}
                if field == 'memo' else {'action': '私は会議を担当した。'}))
            original = json.loads(rec.original_json)
            original['emotions'] = ['喜び', '悲しみ', '怒り', '不安', '平穏']
            original['emotion_details'] = [dict(type=e, strength=('weak', 'medium', 'strong')[i % 3])
                for i, e in enumerate(original['emotions'])]
            rec = replace(rec, saved_record_version=commitment(original),
                original_json=canonical_bytes(original).decode())
            artifact = self.generate(rec).artifact
            node, = artifact.graph.nodes
            self.assertEqual((node.node_kind, node.proposition.predicate_lemma), ('ROLE', '担当する'))
            self.assertEqual(set(node.selected_categories), set(CATEGORIES))
            self.assertFalse(artifact.graph.edges)
            source, = freeze_analysis_sources(request(rec)).sources
            self.assertEqual(source.normalized['emotions'], original['emotions'])
            self.assertEqual(source.normalized['emotion_details'], original['emotion_details'])

    def test_moving_fields_does_not_close_reports_or_supply_missing_actors(self):
        for clause in ('私は会議を担当した。', '私は職場にいた。', '私は不安だった。'):
            for field in ('memo', 'memo_action'):
                for source in ('友人の話です。' + clause, clause + 'と友人が言った。',
                               'もし' + clause, clause.replace('私は', '友人は')):
                    with self.subTest(source=source, field=field):
                        record = saved(**({'memo': source} if field == 'memo' else {'action': source}))
                        self.assertIsNone(self.generate(record).artifact)
            for record in (saved('友人の話です。', clause), saved(clause, '友人の話です。')):
                self.assertIsNone(self.generate(record).artifact)
        self.assertIsNone(self.generate(saved(action='嬉しかった。')).artifact)

    def test_existing_wishes_refusals_cognition_results_and_episodes_use_the_actual_field(self):
        # Written grammar is unchanged. These previously admitted memo forms
        # also need their complete meaning and exact evidence in memo_action.
        texts = [
            '友人の誘いを断った。', '友人の誘いを断らなかった。',
            '仕事を続けたい。', '仕事を続けたかった。',
            '仕事を続けたくない。', '仕事を続けたくなかった。',
            '私は仕事を続けたい。', '私は仕事を続けたかった。',
            '私は仕事を続けたくない。', '私は仕事を続けたくなかった。',
            '私は同僚と分担を決めなかった。', '私は今日、分担を決めておかなかった。',
            'まだ気持ちが定まっていない。', 'まだ不安の原因が見つかっていない。',
            'まだ昨日の方針が決まっていない。', 'まだ仕事の昨日分が定まっていない。',
            '私は資料を調べたかもしれないと思っている。',
            '私は、資料を調べるかもしれないと思う。',
            '私は家族への説明を書いた。', '今日、私は不安だった。',
            '私は落ち着きました。', 'それから、私は嬉しかったです。',
            '私は資料を調べてから、私は安心しなかった。',
            'その後、私は資料を調べてから、落ち着いた。',
            '私は資料を調べた後、資料が戻りました。',
            '私は資料を調べてから、不安が減りました。',
            '私は仕事を続けたいけれど、私はつらい。',
            '私は家族を守りたいけれど、私は、辛い。',
        ]
        for text in texts:
            rendered = []
            for field in ('memo', 'memo_action'):
                with self.subTest(text=text, field=field):
                    rec = saved(**({'memo': text} if field == 'memo' else {'action': text}))
                    artifact = self.generate(rec).artifact
                    self.assertIsNotNone(artifact)
                    rendered.append(artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'])
                    source, = freeze_analysis_sources(request(rec)).sources
                    evidence = [e for node in artifact.graph.nodes for e in node.evidence_refs]
                    evidence += [e for a in artifact.graph.annotations for e in a.evidence_refs]
                    self.assertTrue(evidence)
                    for e in evidence:
                        self.assertEqual(e.field_path, field)
                        literal = source.envelope.raw_utf8[e.utf8_start:e.utf8_end].decode()
                        self.assertEqual(literal, text[e.scalar_start:e.scalar_end])
                    for edge in artifact.graph.edges:
                        self.assertEqual({e.field_path for e in edge.evidence_refs}, {field})
            self.assertEqual(rendered[0], rendered[1])

    def test_action_field_supplement_targets_keep_original_and_answer_envelopes_separate(self):
        old, new = '私は職場にいた', '私は職場にいなかった'
        base = saved('私は会議を担当した。', old + '。')
        answer = AnalysisSupplement('synthetic-field-audit-answer', OWNER,
            base.saved_record_ref, base.saved_record_version,
            '「' + old + '」ではなく「' + new + '」です。', '')
        answer = replace(answer, source_version=commitment(answer.text))
        req = request(replace(base, supplements=(answer,)))
        artifact = MeaningExperienceEngine().generate(req).artifact
        self.assertIsNotNone(artifact)
        role, scene = artifact.graph.nodes
        self.assertEqual((role.node_kind, scene.node_kind, scene.polarity), ('ROLE', 'SCENE', 'negative'))
        original, supplement = freeze_analysis_sources(req).sources
        self.assertEqual(role.evidence_refs[0].source_envelope_id, original.envelope.envelope_id)
        self.assertEqual(scene.evidence_refs[0].source_envelope_id, supplement.envelope.envelope_id)
        update, = artifact.graph.source_updates
        self.assertEqual(update.target_evidence.field_path, 'memo_action')
        self.assertFalse(artifact.graph.edges)
        # Identical text in two original fields has no unique correction
        # target. Its ambiguity must not silently revise both copies.
        duplicate = saved(old + '。', old + '。')
        ambiguous = replace(answer, parent_record_version=duplicate.saved_record_version)
        self.assertIsNone(self.generate(replace(duplicate, supplements=(ambiguous,))).artifact)

    def test_two_complete_unattributed_fields_never_supply_an_actor_or_a_repeated_occasion(self):
        rec = saved('仕事を続けたい。', '友人の誘いを断った。')
        artifact = self.generate(rec).artifact
        self.assertIsNotNone(artifact)
        self.assertEqual({n.proposition.actor for n in artifact.graph.nodes}, {'UNSPECIFIED'})
        self.assertEqual({e.field_path for n in artifact.graph.nodes for e in n.evidence_refs},
                         {'memo', 'memo_action'})
        self.assertTrue(all(len(n.record_refs) == 1 for n in artifact.graph.nodes))
        self.assertFalse(artifact.graph.edges)
        self.assertIn('誰の行動かは未確定', artifact.safe_text_projection(authenticated_owner_scope=OWNER)['text'])

    def test_shared_existing_callers_keep_their_default_memo_scope(self):
        from emlis_ai_grounded_observation_plan import (
            build_final_stage1_grounded_observation_plan,
            _final_source_current_cognition_nuclei, _final_source_unfinished_result_nuclei,
        )
        rec = saved(action='私は資料を調べたかもしれないと思っている。')
        source, = freeze_analysis_sources(request(rec)).sources
        prior = build_final_stage1_grounded_observation_plan(source.normalized, evidence_spans=source.spans)
        opted = build_final_stage1_grounded_observation_plan(source.normalized,
            evidence_spans=source.spans, _analysis_action_field=True)
        prior_node, = (n for n in prior.nuclei if n.source_fields == ('memo_action',))
        new_node, = (n for n in opted.nuclei if n.source_fields == ('memo_action',))
        self.assertNotIn('lexical:source_current_cognition', prior_node.semantic_frame.attribute_codes)
        self.assertIn('lexical:source_current_cognition', new_node.semantic_frame.attribute_codes)
        self.assertEqual(prior_node.source_span_ids, new_node.source_span_ids)
        self.assertEqual(prior_node.source_fields, new_node.source_fields)
        quoted = saved(memo='「私は資料を調べたかもしれないと思っている」')
        quoted_source, = freeze_analysis_sources(request(quoted)).sources
        quoted_plan = build_final_stage1_grounded_observation_plan(quoted_source.normalized,
            evidence_spans=quoted_source.spans)
        for helper in (_final_source_current_cognition_nuclei, _final_source_unfinished_result_nuclei):
            original_rows = list(quoted_plan.nuclei)
            self.assertIs(helper(original_rows, quoted_source.spans, quoted_source.normalized),
                          original_rows)

    def test_existing_grammar_in_either_field_keeps_report_quote_and_open_host_boundaries(self):
        for clause in ('仕事を続けたい', '友人の誘いを断った',
                       'まだ不安の原因が見つかっていない',
                       '私は資料を調べたかもしれないと思っている',
                       '私は資料を調べてから、私は安心しなかった',
                       '私は仕事を続けたいけれど、私はつらい'):
            for field in ('memo', 'memo_action'):
                for text in ('友人の話です。' + clause + '。', '「' + clause + '」。',
                             clause + '。と友人が言った。'):
                    with self.subTest(text=text, field=field):
                        rec = saved(**({'memo': text} if field == 'memo' else {'action': text}))
                        self.assertIsNone(self.generate(rec).artifact)


if __name__ == '__main__':
    unittest.main()
