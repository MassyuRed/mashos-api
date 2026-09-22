"""Sentence-separator spacing must not erase explicit Piece authorship.

Public synthetic inputs only. Source bytes and coordinates remain authoritative;
this is not general whitespace normalization or a saved-input authentication test.
"""
from dataclasses import replace
import hashlib

import pytest

from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.piece_v1c import (
    PieceGenerationRequest, realize_piece_artifact,
)
from piece_v2_generation import PieceSourceSnapshot, _sentences, generate_piece_candidate

TARGET = '机で静かに本を読む時間'
TAIL = 'まだ、毎朝続けられるとは限らない。'
GAPS = (' ', '   ', '\t', '\u3000', ' \t\u3000 ')


def request(text, **kwargs):
    source = PieceSourceSnapshot('spacing-owner', 'spacing-input', 'v1', text)
    return PieceGenerationRequest('spacing-test', source, source.owner_id,
                                  source.saved_input_id, source.source_version, **kwargs)


def run(text, **kwargs):
    return MeaningExperienceEngine().generate(request(text, **kwargs))


def generated(text, **kwargs):
    out = run(text, **kwargs)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    return out


def focal(speaker='私'):
    return speaker + 'が大切にしたいのは、' + TARGET + 'です。'


def assert_source_ranges(out, text, expected_sentences):
    meaning = out.source_meaning
    raw = text.encode('utf-8')
    assert meaning.envelope.raw_utf8 == raw
    assert meaning.envelope.raw_sha256 == hashlib.sha256(raw).hexdigest()
    assert [node.value for node in meaning.graph.nodes] == expected_sentences
    cursor = 0
    for sentence, node, evidence in zip(
            meaning.sentences, meaning.graph.nodes, meaning.evidence, strict=True):
        start, end = sentence.source_start, sentence.source_end
        assert start >= cursor
        assert not text[cursor:start].strip(' \t\u3000\r\n')
        assert text[start:end] == node.value
        assert (evidence.scalar_start, evidence.scalar_end) == (start, end)
        assert evidence.utf8_start == len(text[:start].encode('utf-8'))
        assert evidence.utf8_end == len(text[:end].encode('utf-8'))
        assert raw[evidence.utf8_start:evidence.utf8_end].decode('utf-8') == node.value
        assert evidence.literal_sha256 == hashlib.sha256(node.value.encode('utf-8')).hexdigest()
        cursor = end
    assert not text[cursor:].strip(' \t\u3000\r\n')
    for frame in meaning.personal_evaluations:
        for scalar, utf8 in zip(frame.scalar_parts, frame.utf8_parts, strict=True):
            assert text[slice(*scalar)] == raw[slice(*utf8)].decode('utf-8')
    for ref in meaning.nominal_references:
        for scalar, utf8 in ((ref.antecedent_scalar_span, ref.antecedent_utf8_span),
                             (ref.reference_scalar_span, ref.reference_utf8_span)):
            assert text[slice(*scalar)] == raw[slice(*utf8)].decode('utf-8')
    for scope in meaning.expression_scopes:
        for scalar, utf8 in ((scope.scope_scalar_span, scope.scope_utf8_span),
                             (scope.expression_scalar_span, scope.expression_utf8_span)):
            assert text[slice(*scalar)] == raw[slice(*utf8)].decode('utf-8')


@pytest.mark.parametrize('gap', GAPS)
@pytest.mark.parametrize('speaker', ('私', 'わたし', '僕', 'ぼく', '俺', 'おれ'))
def test_separator_spacing_reaches_the_bound_preference_without_changing_source(gap, speaker):
    parts = [focal(speaker), speaker + 'はその時間が好きではなかったかもしれない。', TAIL]
    text = gap.join(parts)
    out = generated(text)
    plain = generated(''.join(parts))
    expected = speaker + 'は、' + TARGET + 'を大切にしたい。その時間が好きではなかったかもしれない。' + TAIL
    assert out.artifact.piece_text == expected
    assert out.artifact.as_candidate() == plain.artifact.as_candidate()
    assert out.source_meaning.graph.graph_id != plain.source_meaning.graph.graph_id
    assert_source_ranges(out, text, parts)
    frame, = out.source_meaning.personal_evaluations
    assert (frame.polarity, frame.temporal_scope, frame.commitment) == ('NEGATIVE', 'PAST', 'POSSIBLE')
    assert not out.artifact_plan.declaration_eligible
    candidate = generate_piece_candidate(request(text).source, authenticated_owner_id='spacing-owner')
    assert candidate == out.artifact.as_candidate()
    assert candidate['piece_text_hash'] == hashlib.sha256(expected.encode('utf-8')).hexdigest()
    assert candidate['production_enabled'] is False
    assert candidate['record_effect'] == candidate['quota_effect'] == 0


@pytest.mark.parametrize('gap', GAPS)
@pytest.mark.parametrize('second', (
    '私にとってその時間が必要ではなかったかもしれない。',
    '日程が合うなら、私はその時間が好きです。',
    'その時間が取れるなら、私は落ち着いて考えたい。',
    '僕はその時間が好きです。',
))
def test_viewpoint_condition_and_different_speaker_keep_their_own_meaning(gap, second):
    parts = [focal(), second, TAIL]
    out = generated(gap.join(parts))
    assert out.artifact.as_candidate() == generated(''.join(parts)).artifact.as_candidate()
    assert_source_ranges(out, gap.join(parts), parts)
    if second.startswith('私にとって'):
        assert '私にとって、その時間が必要ではなかったかもしれない。' in out.artifact.piece_text
    if second.startswith('僕は'):
        assert '僕は、その時間が好きです。' in out.artifact.piece_text
    if second.startswith('日程'):
        assert '日程が合うなら、私は、その時間が好きです。' in out.artifact.piece_text


@pytest.mark.parametrize('newline', ('\n', '\r\n', '\r', '\n\n'))
def test_horizontal_indentation_does_not_hide_a_source_line_boundary(newline):
    parts = [focal('ぼく'), 'ぼくはその時間が好きです。', TAIL]
    text = ' \t' + parts[0] + '  ' + newline + '\u3000' + parts[1] + ' \t' + parts[2] + '  '
    out = generated(text)
    assert '。ぼくは、その時間が好きです。' in out.artifact.piece_text
    assert_source_ranges(out, text, parts)


def test_interior_spaces_and_repeated_propositions_are_not_normalized_or_deduplicated():
    parts = ['私は小さく  試して確かめたい。', '予定は  まだ決めていない。',
             '予定は  まだ決めていない。']
    text = ' \t'.join(parts)
    out = generated(text)
    assert out.artifact.as_candidate() == generated(''.join(parts)).artifact.as_candidate()
    assert out.artifact.piece_text.count('予定は  まだ決めていない。') == 2
    assert '小さく  試して確かめたい。' in out.artifact.piece_text
    assert_source_ranges(out, text, parts)


@pytest.mark.parametrize('text,reason', (
    ('私はその時間が好きです。  ' + TAIL, 'evaluation_target_not_self_contained'),
    (focal() + '  私はそのことが好きです。', 'evaluation_target_not_self_contained'),
    (focal() + '  ' + focal() + '\t私はその時間が好きです。', 'evaluation_target_not_self_contained'),
    ('私は少し\n考えたい。  ' + TAIL, 'source_line_mid_sentence'),
    ('私は「静かにしたい。」と言った。  ' + TAIL, 'quoted_discourse_not_yet_supported'),
    ('私は小さく試したい。  。', 'complete_sentence_required'),
    ('私は小さく試したい。\t\u3000！', 'complete_sentence_required'),
    ('私は小さく試したい。' + '  予定は未定です。' * 6, 'complete_sentence_required'),
))
def test_spacing_cannot_supply_missing_meaning_or_remove_sentence_limits(text, reason):
    out = run(text)
    assert out.status == EngineStatus.UNAVAILABLE
    assert out.reason_codes == (reason,)
    assert out.artifact is None


def test_rebased_or_tampered_evidence_cannot_authorize_the_new_candidate():
    text = focal() + '  私はその時間が好きです。  ' + TAIL
    out = generated(text)
    meaning = out.source_meaning
    ref, = meaning.nominal_references
    shifted = replace(ref, reference_scalar_span=(ref.reference_scalar_span[0] - 2,
                                                  ref.reference_scalar_span[1] - 2))
    with pytest.raises(ValueError):
        realize_piece_artifact(replace(meaning, nominal_references=(shifted,)),
                               out.artifact_plan, tier='free', requested_format=None)
    evidence = meaning.evidence[1]
    shifted_evidence = replace(evidence, utf8_start=evidence.utf8_start - 2)
    with pytest.raises(ValueError):
        realize_piece_artifact(replace(meaning, evidence=(meaning.evidence[0], shifted_evidence,
                                                         *meaning.evidence[2:])),
                               out.artifact_plan, tier='free', requested_format=None)


@pytest.mark.parametrize('field,value,reason', (
    ('expected_owner_id', 'another-owner', 'source_owner_mismatch'),
    ('expected_saved_input_id', 'another-input', 'saved_input_binding_mismatch'),
    ('expected_source_version', 'v2', 'source_version_binding_mismatch'),
))
def test_spacing_does_not_relax_source_identity(field, value, reason):
    req = request(focal() + '  私はその時間が好きです。  ' + TAIL)
    out = MeaningExperienceEngine().generate(replace(req, **{field: value}))
    assert out.status == EngineStatus.UNAVAILABLE and out.reason_codes == (reason,)


@pytest.mark.parametrize('terminal', ('。', '！', '？', '!', '?'))
def test_spacing_retains_the_written_terminal_and_interior_spacing(terminal):
    assert _sentences('確認した' + terminal + '  予定は  未定です。') == [
        '確認した' + terminal, '予定は  未定です。']
