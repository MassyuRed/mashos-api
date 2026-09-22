"""Synthetic comparison operands retain their source-bound reference and polarity."""
from dataclasses import replace
import hashlib
import pytest

from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.piece_v1c import (
    PieceGenerationRequest, compile_piece_artifact_plan, realize_piece_artifact,
)
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate

ANTECEDENT = '机で静かに本を読む時間'
OTHER = '庭で季節の花を眺める時間'
TAIL = 'まだ、毎日続けられるとは限らない。'


def run(text, **kwargs):
    source = PieceSourceSnapshot('synthetic-owner', 'synthetic-comparison', 'v1', text)
    request = PieceGenerationRequest('synthetic-comparison', source,
                                    source.owner_id, source.saved_input_id,
                                    source.source_version, **kwargs)
    return MeaningExperienceEngine().generate(request)


def generated(text, **kwargs):
    out = run(text, **kwargs)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    assert not out.automatic_progression
    c = out.artifact.as_candidate()
    assert c['record_effect'] == c['quota_effect'] == 0
    assert c['production_enabled'] is False
    assert c['piece_text_hash'] == hashlib.sha256(c['piece_text'].encode()).hexdigest()
    source = PieceSourceSnapshot('synthetic-owner', 'synthetic-comparison', 'v1', text)
    assert generate_piece_candidate(source, authenticated_owner_id=source.owner_id,
                                    **kwargs) == c
    return out


def target(side, gap='、'):
    return ('その時間より' + gap + OTHER if side == 'left'
            else OTHER + 'より' + gap + 'その時間')


def first(speaker='私', obj=ANTECEDENT):
    return speaker + 'が大切にしたいのは、' + obj + 'です。'


def check_reference(out, text, expected='その時間'):
    meaning = out.source_meaning
    raw = text.encode()
    assert meaning.envelope.raw_utf8 == raw
    assert meaning.envelope.raw_sha256 == hashlib.sha256(raw).hexdigest()
    for node, sentence, evidence in zip(meaning.graph.nodes, meaning.sentences,
                                       meaning.evidence, strict=True):
        assert text[sentence.source_start:sentence.source_end] == node.value
        assert raw[evidence.utf8_start:evidence.utf8_end].decode() == node.value
    refs = meaning.nominal_references
    assert len(refs) == 1
    ref = refs[0]
    assert ref.antecedent_node_id == 'piece:s1'
    assert ref.reference_node_id == 'piece:s2'
    assert text[slice(*ref.antecedent_scalar_span)] == ANTECEDENT
    assert text[slice(*ref.reference_scalar_span)] == expected
    assert raw[slice(*ref.antecedent_utf8_span)].decode() == ANTECEDENT
    assert raw[slice(*ref.reference_utf8_span)].decode() == expected
    edges = [e for e in meaning.graph.edges if e.relation == 'SOURCE_BOUND_NOMINAL_REFERENCE']
    assert len(edges) == 1 and edges[0].target_node_id == ref.antecedent_node_id
    assert edges[0].source_node_id == ref.reference_node_id
    assert edges[0].evidence_ids == ('piece:e1', 'piece:e2')
    assert out.artifact_plan.block_node_ids == (tuple(n.node_id for n in meaning.graph.nodes),)
    assert out.artifact.eligible_formats == ('short_essay',)


@pytest.mark.parametrize('speaker', ('私', 'わたし', '僕', 'ぼく', '俺', 'おれ'))
@pytest.mark.parametrize('side', ('left', 'right'))
@pytest.mark.parametrize('order', ('finite', 'focus'))
def test_bound_operand_keeps_both_comparison_sides_and_explicit_author(speaker, side, order):
    argument = target(side)
    second = (speaker + 'は' + argument + 'が好きです。' if order == 'finite'
              else speaker + 'が好きなのは、' + argument + 'です。')
    text = first(speaker) + '  ' + second + '\t' + TAIL
    out = generated(text)
    assert out.artifact.piece_text == (
        speaker + 'は、' + ANTECEDENT + 'を大切にしたい。'
        + speaker + 'は、' + argument + 'が好きです。' + TAIL)
    # A comparison is not the prior whole-target preference continuity edit.
    assert len(out.source_meaning.personal_evaluations) == 1
    frame = out.source_meaning.personal_evaluations[0]
    assert text[slice(*frame.scalar_parts[2])] == argument
    check_reference(out, text)


@pytest.mark.parametrize('side', ('left', 'right'))
@pytest.mark.parametrize('ending,polarity,time,commitment', (
    ('でした', 'AFFIRMATIVE', 'PAST', 'ASSERTED'),
    ('ではない', 'NEGATIVE', 'NONPAST', 'ASSERTED'),
    ('じゃなかった', 'NEGATIVE', 'PAST', 'ASSERTED'),
    ('だったかもしれない', 'AFFIRMATIVE', 'PAST', 'POSSIBLE'),
    ('ではなかったかもしれない', 'NEGATIVE', 'PAST', 'POSSIBLE'),
    ('ではないとは限らない', 'NEGATIVE', 'NONPAST', 'NON_UNIVERSAL'),
))
def test_comparison_does_not_choose_a_winner_or_change_evaluation_state(side, ending, polarity, time, commitment):
    text = first() + '私は' + target(side) + 'が好き' + ending + '。' + TAIL
    out = generated(text)
    assert out.artifact.piece_text == (
        '私は、' + ANTECEDENT + 'を大切にしたい。私は、'
        + target(side) + 'が好き' + ending + '。' + TAIL)
    frame = out.source_meaning.personal_evaluations[0]
    assert (frame.polarity, frame.temporal_scope, frame.commitment) == (polarity, time, commitment)
    assert out.artifact.piece_text.count('大切にしたい') == 1
    assert '選びたい' not in out.artifact.piece_text
    check_reference(out, text)


@pytest.mark.parametrize('scope', ('日程が合うなら、', '日程が合うので、', '日程が合うけれど、'))
@pytest.mark.parametrize('side', ('left', 'right'))
def test_viewpoint_stays_inside_its_source_marked_scope(scope, side):
    text = first() + scope + '私にとって' + target(side) + 'が必要ではなかったかもしれない。' + TAIL
    out = generated(text)
    assert out.artifact.piece_text == ('私は、' + ANTECEDENT + 'を大切にしたい。'
        + scope + '私にとって、' + target(side) + 'が必要ではなかったかもしれない。' + TAIL)
    check_reference(out, text)


@pytest.mark.parametrize('gap', ('、', '，', ',', '、  ', ',\t', '、\u3000'))
def test_operand_delimiter_and_source_offsets_are_not_normalized(gap):
    argument = target('right', gap)
    text = ' \t' + first() + ' \r\n\u3000私は' + argument + 'が苦手でした。 ' + TAIL
    out = generated(text)
    assert '私は、' + argument + 'が苦手でした。' in out.artifact.piece_text
    check_reference(out, text)


def test_scope_and_comparison_can_bind_two_distinct_mentions_of_one_antecedent():
    text = first() + 'その時間が取れるなら、私は' + target('right') + 'が好きです。' + TAIL
    out = generated(text)
    refs = out.source_meaning.nominal_references
    assert len(refs) == 2 and refs[0].reference_scalar_span != refs[1].reference_scalar_span
    assert all(ref.antecedent_node_id == 'piece:s1' for ref in refs)
    assert out.artifact.piece_text == ('私は、' + ANTECEDENT + 'を大切にしたい。'
        + 'その時間が取れるなら、私は、' + target('right') + 'が好きです。' + TAIL)


def test_named_role_publicization_does_not_swallow_the_comparison_operand():
    first_sentence = '僕にとって友人の森さんの先輩の原さんと落ち着いて話す時間が大切です。'
    text = first_sentence + '僕はその時間より、庭で季節の花を眺める時間が好きかもしれない。' + TAIL
    out = generated(text)
    assert out.artifact.piece_text == ('僕にとって、友人の先輩と落ち着いて話す時間が大切です。'
        + '僕は、その時間より、庭で季節の花を眺める時間が好きかもしれない。' + TAIL)
    assert all(name not in out.artifact.piece_text for name in ('森さん', '原さん'))


@pytest.mark.parametrize('text', (
    '私はその時間より、' + OTHER + 'が好きです。' + TAIL,
    '私は' + OTHER + 'より、その時間が好きです。' + first(),
    first() + first('私', OTHER) + '私はその時間より、家で休む時間が好きです。',
    first() + '友人は散歩する時間を取った。私は' + target('left') + 'が好きです。',
    '私が大切にしたいのは、読書より、' + ANTECEDENT + 'です。私は' + target('left') + 'が好きです。',
    first() + '私はその時間帯より、' + OTHER + 'が好きです。',
    first() + '私はその時間を確保することより、' + OTHER + 'が好きです。',
    first() + '私はその時間より前に出発することが好きです。',
    first() + '私はその時間よりも、' + OTHER + 'が好きです。',
    first() + '私はその時間ではなく、' + OTHER + 'が好きです。',
    first() + '私はその時間より、この時間が好きです。',
    first() + '私はその時間より、誰かと話すことより、' + OTHER + 'が好きです。',
    first() + '私はその 時間より、' + OTHER + 'が好きです。',
    first() + '私はそのことより、' + OTHER + 'が好きです。',
    first() + '私は' + target('left') + 'が好きです。私はその時間が苦手です。',
))
def test_missing_ambiguous_nested_or_differently_marked_operands_are_not_guessed(text):
    out = run(text)
    assert out.status == EngineStatus.UNAVAILABLE
    assert out.artifact is None
    assert out.reason_codes
    assert out.as_body_free()['quota_effect'] == out.as_body_free()['record_effect'] == 0


@pytest.mark.parametrize('change', ('scalar', 'utf8', 'antecedent', 'edge', 'evaluation'))
def test_reference_and_frame_tampering_is_rejected_by_existing_plan_validation(change):
    text = first() + '私は' + target('right') + 'が好きです。' + TAIL
    out = generated(text)
    meaning = out.source_meaning
    ref = meaning.nominal_references[0]
    if change == 'scalar':
        a, b = ref.reference_scalar_span
        meaning = replace(meaning, nominal_references=(replace(ref, reference_scalar_span=(a-1, b)),))
    elif change == 'utf8':
        a, b = ref.reference_utf8_span
        meaning = replace(meaning, nominal_references=(replace(ref, reference_utf8_span=(a+1, b)),))
    elif change == 'antecedent':
        meaning = replace(meaning, nominal_references=(replace(ref, antecedent_node_id='piece:s2'),))
    elif change == 'edge':
        edges = tuple(e for e in meaning.graph.edges if e.relation != 'SOURCE_BOUND_NOMINAL_REFERENCE')
        meaning = replace(meaning, graph=replace(meaning.graph, edges=edges))
    else:
        frame = meaning.personal_evaluations[0]
        meaning = replace(meaning, personal_evaluations=(replace(frame, polarity='NEGATIVE'),))
    with pytest.raises(ValueError):
        compile_piece_artifact_plan(meaning)
    with pytest.raises(ValueError):
        realize_piece_artifact(meaning, out.artifact_plan, tier='free', requested_format=None)


@pytest.mark.parametrize('head,antecedent,other', (
    ('こと', '自分で納得して選ぶこと', '周りの意見だけで決めること'),
    ('もの', '手で触れて形を確かめられるもの', '机に並べて眺められるもの'),
    ('時間', ANTECEDENT, OTHER),
))
@pytest.mark.parametrize('deictic', ('その', 'この'))
def test_nominal_operand_head_is_preserved_not_replaced_by_a_time_template(head, antecedent, other, deictic):
    argument = other + 'より、' + deictic + head
    text = first('わたし', antecedent) + 'わたしは' + argument + 'が好きです。' + TAIL
    out = generated(text)
    assert out.artifact.piece_text == ('わたしは、' + antecedent + 'を大切にしたい。'
        + 'わたしは、' + argument + 'が好きです。' + TAIL)
    ref = out.source_meaning.nominal_references[0]
    assert ref.nominal_head == head
    assert text[slice(*ref.antecedent_scalar_span)] == antecedent
    assert text[slice(*ref.reference_scalar_span)] == deictic + head
