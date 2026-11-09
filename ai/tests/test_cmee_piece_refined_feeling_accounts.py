"""Independent finite feelings in a real supplemental envelope, never selection.

These independently authored fictional development pairs check the existing
Piece author, source-qualified evidence and mutation
rejection; they do not establish general Japanese or public Piece acceptance.
"""
from dataclasses import replace
import hashlib
from unittest.mock import patch

import pytest

from piece_v2_contract import PieceContractError
from piece_v2_generation import generate_piece_candidate
from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine import piece_refined as refined
from test_cmee_piece_refined_sources import source, produce


CASES = (
    ('private-pottery', '私が大切にしたいのは、手を動かして器を作る時間です。',
     '私は嬉しかった。'),
    ('negative-choice', '私が選びたくないのは、急いで答えを出すことです。',
     'わたしは嬉しくなかったです。'),
    ('small-sadness', '私は朝に本を読みたい。', '僕は少し悲しい。'),
    ('past-enjoyment', '私は木の道具を大切にしたい。', 'ぼくはとても楽しかったです。'),
    ('negative-fear', '私が望んでいるのは、静かに過ごす時間です。',
     'おれはあまり怖くなかった。'),
    ('written-feeling', '私は急がずに予定を決めたい。', '俺は強い不安を感じませんでした。'),
    ('explicit-now', '今は、私が大切にしたいのは、家で休む時間です。',
     '今は、私は楽しい。'),
    ('explicit-current', '私はゆっくり選びたい。', '現在は、わたしは悲しくないです。'),
)


@pytest.mark.parametrize('case_id,original,answer', CASES, ids=[r[0] for r in CASES])
def test_explicit_finite_answer_retained_as_its_own_source(case_id, original, answer):
    s = source(original=original, answer=answer)
    original_bytes = s.original.saved_original_json
    before = generate_piece_candidate(s.original, authenticated_owner_id=s.original.owner_id)
    out = produce(s)
    assert out.status == EngineStatus.GENERATED, (case_id, out.reason_codes)
    assert out.artifact.piece_text == before['piece_text'] + '\n\n' + answer
    assert out.artifact.body_blocks[-1] == answer
    assert out.artifact.eligible_formats == ('short_essay',)
    assert all(d.operation == 'KEEP_COMPLETE_SOURCE_CONTEXT'
               for d in out.artifact_plan.supplemental_plan.duties)
    supplemental = out.source_meaning.supplemental
    assert supplemental.envelope.source_role == 'SUPPLEMENTAL_ANSWER'
    assert supplemental.saved_snapshot is None and not supplemental.selected_feelings
    assert not supplemental.selection_evidence and not supplemental.selection_contexts
    sentence, = supplemental.sentences
    evidence, = supplemental.evidence
    assert evidence.field_path == 'answer_text_private' and evidence.field_utf8_start > 0
    assert supplemental.envelope.raw_utf8[evidence.utf8_start:evidence.utf8_end].decode() == answer
    assert s.supplemental.answer_text_private[sentence.source_start:sentence.source_end] == answer
    assert s.original.saved_original_json == original_bytes
    assert '平穏' not in out.artifact.piece_text
    raw = refined.serialize_refined_piece(out)
    digest = hashlib.sha256(raw).hexdigest()
    forbidden = AssertionError('reread must not compile or author')
    with patch('cocolon_meaning_experience_engine.piece_v1c.compile_piece_artifact_plan', side_effect=forbidden), \
         patch('cocolon_meaning_experience_engine.piece_v1c.realize_piece_artifact', side_effect=forbidden), \
         patch.object(refined, 'build_refined_meaning', side_effect=forbidden):
        assert refined.read_saved_refined_artifact(raw, expected_state_sha256=digest) == out.artifact


@pytest.mark.parametrize('answer', (
    '嬉しかった。',
    '友人は嬉しかった。',
    '私は嬉しかったかもしれない。',
    '私は嬉しかったと聞いた。',
    '私は嬉しかった？',
    '私は忙しかった。',
    '私は私も嬉しかった。',
    '僕は自分は嬉しい。',
))
def test_no_guessed_owner_report_question_or_arbitrary_adjective(answer):
    out = produce(source(answer=answer))
    assert out.status == EngineStatus.UNAVAILABLE and out.artifact is None


@pytest.mark.parametrize('answer', (
    '私は嬉しかった。私は忙しかった。',
    '今は私は嬉しい。',
    '今は、嬉しい。',
))
def test_whole_answer_requires_proved_sentences_and_explicit_time_owner(answer):
    out = produce(source(answer=answer))
    assert out.status == EngineStatus.UNAVAILABLE and out.artifact is None


@pytest.mark.parametrize('index,old,new', (
    (0, '嬉しかった', '嬉しくなかった'),
    (1, '嬉しくなかったです', '嬉しかったです'),
    (2, '少し', 'とても'),
    (5, '感じませんでした', '感じました'),
    (6, '今は、', ''),
))
def test_rehashed_answer_polarity_degree_and_time_changes_are_rejected(index, old, new):
    _, original, answer = CASES[index]
    out = produce(source(original=original, answer=answer))
    assert out.status == EngineStatus.GENERATED, out.reason_codes
    blocks = (*out.artifact.body_blocks[:-1], answer.replace(old, new))
    text = '\n\n'.join(blocks)
    changed = replace(out.artifact, body_blocks=blocks, piece_text=text,
                      piece_text_hash=hashlib.sha256(text.encode()).hexdigest())
    forbidden = AssertionError('preservation review must not author')
    with patch('cocolon_meaning_experience_engine.piece_v1c.realize_piece_artifact', side_effect=forbidden):
        with pytest.raises(PieceContractError):
            refined.validate_refined_preservation(out.source_meaning, out.artifact_plan, changed)
