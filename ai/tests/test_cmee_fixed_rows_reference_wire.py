"""Fixed-row syntax and explicit private admission; standard-library tests."""
import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'services/ai_inference'))
from cocolon_meaning_experience_engine import fixed_rows_reference_wire as rows
from cocolon_meaning_experience_engine import named_reference_wire as named
from cocolon_meaning_experience_engine.preparation import PreparedRequest, receive_candidate, _prepare


def teacher():
    # Independently written columns, including null, empty cells, explicit
    # quote/identity names and repeated legal use of the same quote name.
    return [rows.SCHEMA, named.SCHEMA, [['source', 'source-id']],
        [['quote1', '@source', 'memo', '気になる']],
        [[
            [['@source', ['quote1'], None, 'WRITTEN_PRESENT'], 'c1', ['quote1'],
             'STATE', [['quote1'], 'ASSERTED_AS_WRITTEN'],
             [['quote1'], [], 'AFFIRMED'], [[], '気になる'], [],
             ['OMITTED', ['quote1'], None], '気になる']
         ], [], 'emlis', None, [],
         'cocolon.cmee.semantic_and_surface_proposal.v1', [], [],
         [[[['c1'], [], 'observation']], '気になるのですね。', '受け止めました。', '']]]


def material(topic='book', **changes):
    originals = {
        'book': ('借りていた本を返すのが遅れて、友人に謝った。', '大丈夫って言ってくれたけど、まだちょっと気になる。'),
        'shop': ('昔からの友人が店を開いたと知って、お祝いのメッセージを送った。', 'うれしかったけど、少し置いていかれた気がした。'),
    }
    action, memo = originals[topic]
    value = dict(core='emlis', tier='free', task='EMLIS_ANSWER_MATERIAL',
        sources=[dict(source_id='source-id', role='ORIGINAL_INPUT',
            text_fields=dict(memo=memo, memo_action=action)),
            dict(source_id='answer-id', role='SUPPLEMENTAL_ANSWER',
            text_fields=dict(answer_text_private='本人の回答。'))])
    value.update(changes)
    return _prepare(value)


class FixedRowsWireTests(unittest.TestCase):
    def test_values_and_names_are_retained_without_completion(self):
        value = teacher()
        restored = rows.decode_named(value)
        self.assertIsNone(restored['c']['claims'][0]['time']['expr'])
        self.assertIsNone(restored['c']['claims'][0]['subject']['entity'])
        self.assertEqual(restored['c']['unknowns'], [])
        self.assertEqual(rows.decode(value), named.decode(restored))
        self.assertEqual(value, teacher())
        value[4][0][0][0][2] = 'null'
        self.assertEqual(rows.decode_named(value)['c']['claims'][0]['time']['expr'], 'null')
        value[4][0].clear()
        self.assertEqual(rows.decode_named(value)['c']['claims'], [])

    def test_bad_shapes_types_versions_and_names_are_rejected(self):
        changes = [
            lambda p: p[4][0][0].pop(),
            lambda p: p[4][7].append(['q', 'ADD']),
            lambda p: p[2].append(p[2][0]),
            lambda p: p[3][0].__setitem__(3, None),
            lambda p: p.__setitem__(0, 'unknown'),
            lambda p: p[4][0][0][2].__setitem__(0, 'undefined'),
            lambda p: p[3].append(p[3][0]),
            lambda p: p[2][0].__setitem__(0, 'bad-name!'),
            lambda p: p[4][8][0][0].append(['undefined-update']),
            lambda p: p[4][0][0][0].__setitem__(0, '@missing'),
            lambda p: p[4][7].extend([ [[], 'ADD', '@source', [], 'CLAIM', 'c1', 'u1'] ] * 2),
        ]
        for i, change in enumerate(changes):
            with self.subTest(i=i):
                value = teacher(); change(value)
                with self.assertRaises(ValueError): rows.decode(value)

    def test_receipt_keeps_actual_rows_and_metadata_and_replays(self):
        req = material()
        raw = ' \n' + json.dumps(teacher(), ensure_ascii=False) + '\n'
        receipt = receive_candidate(req, request_id=req.request_id, raw_output=raw,
            finish_reason='stop', provider='test', model='4B', revision='base',
            adapter_revision='adapter', usage={'completion_tokens': 10},
            elapsed_seconds=1, candidate_format=rows.SCHEMA)
        self.assertEqual(receipt.raw_output, raw)
        metadata = json.loads(receipt.metadata_json)
        self.assertEqual(metadata.pop('candidate_format'), rows.SCHEMA)
        metadata['candidate_format'] = rows.SCHEMA
        metadata.pop('evidence_check')
        self.assertEqual(receive_candidate(req, request_id=req.request_id,
            raw_output=raw, **metadata), receipt)
        self.assertEqual(receipt.status, 'CANDIDATE_UNREVIEWED')

    def test_explicit_scope_and_no_autodetection_or_named_fallback(self):
        raw = json.dumps(teacher(), ensure_ascii=False)
        for topic in ('book', 'shop'):
            req = material(topic)
            self.assertTrue(rows.accepts_material(req.payload()))
            for fmt in (None, named.SCHEMA):
                self.assertEqual(receive_candidate(req, request_id=req.request_id,
                    raw_output=raw, finish_reason='stop', candidate_format=fmt).status, 'INVALID_FORMAT')
            self.assertEqual(receive_candidate(req, request_id=req.request_id,
                raw_output=json.dumps(rows.decode_named(teacher()), ensure_ascii=False),
                finish_reason='stop', candidate_format=rows.SCHEMA).status, 'INVALID_FORMAT')
        for changes in ({'tier': 'plus'}, {'core': 'piece'},
                        {'task': 'EMLIS_INITIAL_MATERIAL'}):
            req = material(**changes)
            self.assertFalse(rows.accepts_material(req.payload()))
            self.assertEqual(receive_candidate(req, request_id=req.request_id,
                raw_output=raw, finish_reason='stop', candidate_format=rows.SCHEMA).status, 'INVALID_FORMAT')
        payload = material().payload()
        payload['sources'][0]['text_fields']['memo'] = '別の題材。'
        self.assertFalse(rows.accepts_material(payload))
        payload = material().payload(); payload['execution_mode'] = 'PUBLIC'
        self.assertFalse(rows.accepts_material(payload))

    def test_finish_priority_strict_json_and_legacy_receipt_bytes(self):
        req = material(); raw = json.dumps(teacher(), ensure_ascii=False)
        for finish, status in [('timeout', 'TIMEOUT'), ('length', 'TOKEN_LIMIT'),
                               ('error', 'PROVIDER_ERROR'), ('future', 'UNKNOWN_FINISH')]:
            self.assertEqual(receive_candidate(req, request_id=req.request_id,
                raw_output=raw, finish_reason=finish, candidate_format=rows.SCHEMA).status, status)
        for bad in (raw[:-1], raw.replace('null', 'NaN', 1),
                    raw.replace('null', '1e999', 1), raw.replace('null', '{"x":1,"x":2}', 1),
                    raw.replace('気になる', '\\ud800', 1)):
            receipt = receive_candidate(req, request_id=req.request_id, raw_output=bad,
                finish_reason='stop', candidate_format=rows.SCHEMA)
            self.assertEqual(receipt.status, 'INVALID_FORMAT')
            self.assertIsNone(receipt.candidate_json)
        receipt = receive_candidate(req, request_id=req.request_id, raw_output=None, finish_reason='stop')
        self.assertEqual(receipt.metadata_json,
            '{"elapsed_seconds":null,"evidence_check":"LOCATION_ONLY_NOT_SEMANTIC_ADMISSION",'
            '"finish_reason":"stop","model":null,"provider":null,"revision":null,"usage":null}')


if __name__ == '__main__':
    unittest.main()
