"""Direct word order preserves the same explicit transitive expression.

Synthetic source fixtures. No inferred author, new predicate dictionary,
fulfilled condition, state-to-wish rewrite or production activation.
"""
from dataclasses import replace
import hashlib
import pytest
from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.piece_v1c import (
    PieceGenerationRequest, compile_piece_artifact_plan, realize_piece_artifact,
)
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate
from piece_v2_contract import canonical_sha256_hex
from piece_v2_visual import build_visual_recipe
from piece_v2_layout import TextMeasurement, build_measured_layout

TARGETS = (('一人で静かに手帳を開く時間', '時間'),
           ('机で小さな紙を折ること', 'こと'),
           ('長く大切に使い続けてきたもの', 'もの'))
PREDICATES = ('大切にしたい', '大切にしている', '大切にしたくない',
              '望んでいる', '望んでいない', '選びたい', '選びたくない')
SCOPES = (('落ち着いて考えられるので', 'SOURCE_EXPLICIT_REASON'),
          ('無理なく続けられるなら', 'SOURCE_EXPLICIT_CONDITION'),
          ('無理なく続けられるならば', 'SOURCE_EXPLICIT_CONDITION'),
          ('まだ迷っているけれど', 'SOURCE_EXPLICIT_CONCESSION'),
          ('まだ迷っているけれども', 'SOURCE_EXPLICIT_CONCESSION'))
TARGET = TARGETS[0][0]
TAIL = 'まだ、毎朝続けるかは決めていません。'


def outcome(text):
    source = PieceSourceSnapshot('synthetic-owner', 'direct-transitive', '1', text)
    out = MeaningExperienceEngine().generate(PieceGenerationRequest(
        'direct-transitive', source, source.owner_id, source.saved_input_id, source.source_version))
    return source, out


def generated(text, expected):
    source, out = outcome(text)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    assert out.artifact.piece_text == expected
    meaning = out.source_meaning
    assert meaning.envelope.raw_utf8 == text.encode('utf-8')
    assert out.artifact_plan == compile_piece_artifact_plan(meaning)
    for node, ev in zip(meaning.graph.nodes, meaning.evidence, strict=True):
        assert text[ev.scalar_start:ev.scalar_end] == node.value
        assert text.encode('utf-8')[ev.utf8_start:ev.utf8_end] == node.value.encode('utf-8')
    for ref in meaning.nominal_references:
        for scalar, utf8 in ((ref.antecedent_scalar_span, ref.antecedent_utf8_span),
                             (ref.reference_scalar_span, ref.reference_utf8_span)):
            assert text[slice(*scalar)].encode('utf-8') == text.encode('utf-8')[slice(*utf8)]
    candidate = generate_piece_candidate(source, authenticated_owner_id=source.owner_id)
    assert candidate == out.artifact.as_candidate()
    assert candidate['piece_text_hash'] == hashlib.sha256(expected.encode('utf-8')).hexdigest()
    assert candidate['eligible_formats'] == ['short_essay']
    assert not out.automatic_progression and not candidate['production_enabled']
    assert candidate['quota_effect'] == candidate['record_effect'] == 0
    return out


@pytest.mark.parametrize('target,head', TARGETS)
@pytest.mark.parametrize('predicate', PREDICATES)
def test_direct_object_introduces_the_same_referent_without_changing_the_predicate(target, head, predicate):
    first = '私は' + target + 'を' + predicate + '。'
    following = '私はその' + head + 'が好きではなかったかもしれません。'
    text = first + following + TAIL
    out = generated(text, '私は、' + target + 'を' + predicate + '。'
                    + '私は、その' + head + 'が好きではなかったかもしれません。' + TAIL)
    ref, = out.source_meaning.nominal_references
    assert text[slice(*ref.antecedent_scalar_span)] == target
    assert (ref.antecedent_node_id, ref.reference_node_id) == ('piece:s1', 'piece:s2')
    frame, = out.source_meaning.personal_evaluations
    assert (frame.polarity, frame.temporal_scope, frame.commitment) == ('NEGATIVE', 'PAST', 'POSSIBLE')
    assert out.artifact_plan.block_node_ids == (('piece:s1', 'piece:s2', 'piece:s3'),)


@pytest.mark.parametrize('speaker', ('私', 'わたし', '僕', 'ぼく', '俺', 'おれ'))
@pytest.mark.parametrize('determiner', ('その', 'この'))
def test_direct_reference_does_not_become_a_new_antecedent(speaker, determiner):
    first = speaker + 'が大切にしたいのは、' + TARGET + 'です。'
    direct = speaker + 'は' + determiner + '時間を望んでいない。'
    out = generated(first + direct + TAIL, speaker + 'は、' + TARGET + 'を大切にしたい。'
                    + speaker + 'は、' + determiner + '時間を望んでいない。' + TAIL)
    ref, = out.source_meaning.nominal_references
    assert ref.antecedent_node_id == 'piece:s1'
    assert out.artifact_plan.duties[1].operation == 'SOURCE_TRANSITIVE_SELF_TOPIC'


@pytest.mark.parametrize('scope,relation', SCOPES)
@pytest.mark.parametrize('predicate', ('大切にしたい', '大切にしている', '望んでいない'))
def test_scope_and_direct_object_preserve_the_same_order_and_meaning(scope, relation, predicate):
    first = '僕にとって大切なのは、' + TARGET + 'です。'
    prefix = '僕は' + scope + '、'
    direct = '僕はその時間を' + predicate + '。'
    out = generated(first + prefix + direct + TAIL,
                    '僕にとって、' + TARGET + 'が大切です。' + prefix + 'その時間を' + predicate + '。' + TAIL)
    focal = '僕が' + predicate + 'のは、その時間です。'
    _, focal_out = outcome(first + prefix + focal + TAIL)
    assert out.artifact.as_candidate() == focal_out.artifact.as_candidate()
    scope_info, = out.source_meaning.expression_scopes
    assert scope_info.relation == relation
    assert out.source_meaning.envelope.raw_utf8[slice(*scope_info.expression_utf8_span)] == direct.encode('utf-8')


@pytest.mark.parametrize('scope,relation', SCOPES)
def test_a_non_self_premise_does_not_take_over_the_explicit_direct_author(scope, relation):
    first = '私にとって大切なのは、' + TARGET + 'です。'
    generated(first + scope + '、僕はその時間を望んでいない。' + TAIL,
              '私にとって、' + TARGET + 'が大切です。' + scope + '、僕はその時間を望んでいない。' + TAIL)


@pytest.mark.parametrize('predicate', ('大切にしている', '望んでいる', '望んでいない'))
def test_an_explicit_state_does_not_need_a_shared_wish_label(monkeypatch, predicate):
    import cocolon_meaning_experience_engine.piece_source as adapter
    monkeypatch.setattr(adapter, 'build_input_meaning_blocks', lambda **kwargs: ())
    out = generated('私は' + TARGET + 'を' + predicate + '。' + TAIL,
                    '私は、' + TARGET + 'を' + predicate + '。' + TAIL)
    assert out.artifact_plan.duties[0].operation == 'SOURCE_TRANSITIVE_SELF_TOPIC'
    assert not out.artifact_plan.declaration_eligible


def test_direct_scoped_antecedent_excludes_its_condition_and_keeps_role_source_ranges():
    target = '同僚の秋山さんと静かに話す時間'
    prefix = '僕は無理なく続けられるなら、僕は'
    text = '🌱を見た。\r\n\u3000' + prefix + target + 'を大切にしている。\t僕はその時間が苦手ではありません。' + TAIL
    out = generated(text, '🌱を見た。\n\n僕は無理なく続けられるなら、同僚と静かに話す時間を大切にしている。'
                    + '僕は、その時間が苦手ではありません。' + TAIL)
    ref, = out.source_meaning.nominal_references
    assert text[slice(*ref.antecedent_scalar_span)] == target
    assert ref.antecedent_scalar_span[0] == text.index(target)
    assert '秋山' not in out.artifact.piece_text


@pytest.mark.parametrize('first', (
    '私は空を眺めた。',
    '私は空いた時間に手帳を開いた。',
    '私は無理なく続けられるので、一人で静かに手帳を開く時間を望んでいる。',
    '私は一人で静かに手帳を開く時間を望んでいる。私は川辺で散歩する時間を望んでいる。',
    '私は一人で静かに手帳を開く時間を望んでいる。別の時間に外出した。',
))
def test_unmodelled_and_competing_antecedents_are_not_guessed(first):
    assert outcome(first + '私はその時間が好きです。' + TAIL)[1].status == EngineStatus.UNAVAILABLE


@pytest.mark.parametrize('expression', (
    '彼はその時間を望んでいる。',
    '私はその時間を好き。',
    '私はその時間を望んでいた。',
    '私はその時間を望んでいるかもしれない。',
    '私はその時間を望んでいると聞いた。',
    '私はその時間とこの時間を望んでいる。',
    '私はその時間にすることを望んでいる。',
))
def test_unadmitted_direct_grammar_does_not_gain_a_scoped_expression(expression):
    text = '私にとって大切なのは、' + TARGET + 'です。まだ迷っているけれど、' + expression + TAIL
    assert outcome(text)[1].status == EngineStatus.UNAVAILABLE


@pytest.mark.parametrize('mutation', ('reference', 'scope', 'operation', 'drop_context'))
def test_forged_reference_scope_or_plan_cannot_drive_the_writer(mutation):
    text = '僕は' + TARGET + 'を大切にしている。僕はまだ迷っているけれど、僕はその時間を望んでいない。' + TAIL
    _, out = outcome(text)
    assert out.status == EngineStatus.GENERATED
    meaning, plan = out.source_meaning, out.artifact_plan
    if mutation == 'reference':
        ref, = meaning.nominal_references
        meaning = replace(meaning, nominal_references=(replace(ref, antecedent_scalar_span=(0, 4)),))
    elif mutation == 'scope':
        scope, = meaning.expression_scopes
        meaning = replace(meaning, expression_scopes=(replace(scope, marker='なら'),))
    elif mutation == 'operation':
        duties = list(plan.duties);duties[0] = replace(duties[0], operation='KEEP_COMPLETE_SOURCE_CONTEXT')
        plan = replace(plan, duties=tuple(duties))
    else:
        plan = replace(plan, block_node_ids=(('piece:s1', 'piece:s2'),))
    with pytest.raises(ValueError):
        realize_piece_artifact(meaning, plan, tier='free', requested_format=None)


class Metrics:
    profile_id = 'direct-transitive-synthetic-not-native'
    def graphemes(self, text):
        return list(text)
    def measure(self, text, font_px):
        w = len(text) * font_px
        return TextMeasurement(w, 0, -font_px * .8, w, font_px * .2)


@pytest.mark.parametrize('ratio', ('4:5', '9:16'))
def test_complete_direct_reference_body_enters_existing_layout(ratio):
    text = '私は' + TARGET + 'を大切にしている。私はその時間が好きです。' + TAIL
    _, out = outcome(text)
    assert out.status == EngineStatus.GENERATED
    candidate = out.artifact.as_candidate()
    recipe = build_visual_recipe('short_essay', tier='premium', aspect_ratio=ratio)
    layout = build_measured_layout(candidate, recipe, canonical_sha256_hex(recipe), Metrics())
    assert [''.join(l['text'] for l in layout['lines'] if l['block_index'] == i)
            for i in range(len(out.artifact.body_blocks))] == list(out.artifact.body_blocks)
    assert layout['piece_text_hash'] == candidate['piece_text_hash']
