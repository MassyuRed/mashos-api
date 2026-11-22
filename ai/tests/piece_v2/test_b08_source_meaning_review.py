"""S7 checks source meaning without asking the text author to repeat itself.

All inputs are synthetic. The fault is in the author used BOTH by the real
CMEE engine and by B8's existing replay fence. No source/parser/plan is mocked.
These checks establish neither full public safety nor device acceptance.
"""
from dataclasses import replace
import hashlib

import pytest

from cocolon_meaning_experience_engine import piece_v1c
from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from piece_v2_contract import PieceContractError, canonical_json_bytes, validate_piece_text_binding
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate
from piece_v2_visual import build_visual_recipe


_MEMO = '私は友人の佐藤さんの上司の田中さんと話したい。'
_ACTION = '田中さんとはまだ会っていない。'
_REFERENCE = _MEMO + _ACTION


def _source(text=_REFERENCE, *, saved=False):
    record = {
        'id': 'synthetic-meaning-review-input', 'created_at': '2026-10-07T00:00:00Z',
        'memo': _MEMO, 'memo_action': _ACTION, 'category': ['対人関係'],
        'emotions': ['自己理解'],
        'emotion_details': [{'type': '自己理解', 'strength': 'medium'}],
    }
    return PieceSourceSnapshot(
        'synthetic-meaning-review-owner', record['id'],
        'emlis.current_input_bundle.v1' if saved else 'v1',
        _MEMO + '\n\n' + _ACTION if saved else text,
        saved_original_json=canonical_json_bytes(record) if saved else None,
    )


def _actual(source, tier='free'):
    result = MeaningExperienceEngine().generate(piece_v1c.PieceGenerationRequest(
        'synthetic-meaning-review', source, source.owner_id,
        source.saved_input_id, source.source_version, tier=tier,
    ))
    assert result.status == EngineStatus.GENERATED, result.as_body_free()
    assert result.artifact is not None
    return result


def _with_blocks(artifact, blocks):
    text = '\n\n'.join(blocks)
    changed = replace(artifact, body_blocks=tuple(blocks), piece_text=text,
                      piece_text_hash=hashlib.sha256(text.encode('utf-8')).hexdigest())
    assert validate_piece_text_binding(changed.content_payload(), text,
                                       changed.piece_text_hash) == text
    return changed


@pytest.mark.parametrize('mutation', [
    'omit_context', 'invert_negation', 'add_claim', 'change_role',
    'reintroduce_name', 'change_speaker', 'reverse_sentences',
])
@pytest.mark.parametrize('saved', [False, True], ids=['text', 'saved_fields'])
def test_same_fault_in_author_and_replay_cannot_pass_s7(monkeypatch, mutation, saved):
    source = _source(saved=saved)
    original = _actual(source)
    author = piece_v1c.realize_piece_artifact
    calls = []

    def faulty(meaning, plan, **kwargs):
        actual = author(meaning, plan, **kwargs)
        text = actual.piece_text
        if mutation == 'omit_context':
            text = text.replace('友人の上司とはまだ会っていない。', '')
        elif mutation == 'invert_negation':
            text = text.replace('まだ会っていない', 'もう会った')
        elif mutation == 'add_claim':
            text += '私は新しい約束をした。'
        elif mutation == 'change_role':
            text = text.replace('友人の上司', '同僚')
        elif mutation == 'reintroduce_name':
            text = text.replace('友人の上司', '田中さん')
        elif mutation == 'change_speaker':
            text = text.replace('私は、', '彼は、')
        else:
            text = ('友人の上司とはまだ会っていない。' + ('\n\n' if saved else '')
                    + '私は、友人の上司と話したい。')
        changed = _with_blocks(actual, text.strip().split('\n\n'))
        assert changed.piece_text != original.artifact.piece_text
        calls.append(changed)
        return changed

    monkeypatch.setattr(piece_v1c, 'realize_piece_artifact', faulty)
    with pytest.raises(PieceContractError) as error:
        generate_piece_candidate(source, authenticated_owner_id=source.owner_id)
    assert len(calls) == 2
    assert calls[0] == calls[1], 'The old replay fence must see the same faulty result.'
    assert error.value.code == 'PIECE_CONTENT_UNAVAILABLE'
    assert error.value.detail == 'piece_meaning_not_preserved'
    assert source.original_text not in str(error.value)


@pytest.mark.parametrize('source_text,before,after', [
    ('私は友人のAliceさんが来られるなら、Aliceさんと急いで話したくない。'
     'まだ、会う日は決めていない。', 'なら', 'ので'),
    ('私は一人で落ち着いて考える時間を大切にしていない。', 'していない', 'している'),
    ('私が大切にしたかったのは、一人で落ち着いて考える時間です。', 'したかった', 'したい'),
    ('私は友人のAliceさんと落ち着いて話したい。Aliceさんの都合はまだ分からない。',
     'まだ分からない', 'もう分かった'),
])
def test_source_operators_survive_an_internally_consistent_author_fault(monkeypatch, source_text, before, after):
    source = _source(source_text)
    actual = _actual(source)
    assert before in actual.artifact.piece_text
    author = piece_v1c.realize_piece_artifact

    def faulty(meaning, plan, **kwargs):
        artifact = author(meaning, plan, **kwargs)
        return _with_blocks(artifact, [block.replace(before, after) for block in artifact.body_blocks])

    monkeypatch.setattr(piece_v1c, 'realize_piece_artifact', faulty)
    with pytest.raises(PieceContractError) as error:
        generate_piece_candidate(source, authenticated_owner_id=source.owner_id)
    assert error.value.detail == 'piece_meaning_not_preserved'


_GOOD = [
    _REFERENCE,
    '私が大切にしたいのは、一人で落ち着いて考える時間です。',
    '私は一人で落ち着いて考える時間を大切にしていない。',
    '私にとって、一人で落ち着いて考える時間が大切です。',
    '余裕があるなら、私は一人で落ち着いて考える時間を大切にしたい。',
    '私は静かな場所で本を読みたい。私は落ち着いて手紙を書きたい。',
    '私は友人のAliceさんが来られるなら、Aliceさんと急いで話したくない。'
    'まだ、会う日は決めていない。',
    '私が大切にしたかったのは、一人で落ち着いて考える時間です。',
]


@pytest.mark.parametrize('text', _GOOD)
@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
def test_actual_duties_keep_the_same_canonical_body_and_visual_recipe(text, tier):
    source = _source(text)
    actual = _actual(source, tier)
    candidate = generate_piece_candidate(source, authenticated_owner_id=source.owner_id, tier=tier)
    assert candidate == actual.artifact.as_candidate()
    assert source.original_text == text
    assert candidate['candidate_state'] == 'OFFLINE_NOT_ACCEPTED'
    assert candidate['record_effect'] == candidate['quota_effect'] == 0
    assert candidate['production_enabled'] is False
    assert 'content_status' not in candidate
    assert build_visual_recipe(candidate['format_type'], tier=tier, aspect_ratio='4:5') == (
        build_visual_recipe(actual.artifact.format_type, tier=tier, aspect_ratio='4:5'))


def test_review_does_not_call_the_author_or_recompile_the_plan(monkeypatch):
    from piece_v2_content_policy import validate_source_meaning_preservation
    actual = _actual(_source(saved=True))

    def forbidden(*args, **kwargs):
        raise AssertionError('S7 must inspect source anchors, not replay an author or plan.')

    monkeypatch.setattr(piece_v1c, 'realize_piece_artifact', forbidden)
    monkeypatch.setattr(piece_v1c, 'compile_piece_artifact_plan', forbidden)
    assert validate_source_meaning_preservation(
        actual.source_meaning, actual.artifact_plan, actual.artifact) is None


def test_review_is_not_byte_replay_and_does_not_rewrite_a_candidate():
    from piece_v2_content_policy import validate_source_meaning_preservation
    actual = _actual(_source())
    blocks = tuple(block.replace('私は、', '私は') for block in actual.artifact.body_blocks)
    candidate = _with_blocks(actual.artifact, blocks)
    assert candidate != actual.artifact
    before = candidate.content_payload(), candidate.piece_text_hash
    assert validate_source_meaning_preservation(
        actual.source_meaning, actual.artifact_plan, candidate) is None
    assert (candidate.content_payload(), candidate.piece_text_hash) == before
