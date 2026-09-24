"""Written register does not sever a direct expression's source argument.

Synthetic fixtures; no new semantic predicate, past/modal admission, author
inference, source normalization, public route or production activation.
"""
from dataclasses import replace
import hashlib
import pytest
from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.piece_source import _direct_transitive_expression
from cocolon_meaning_experience_engine.piece_v1c import (
    PieceGenerationRequest, compile_piece_artifact_plan, realize_piece_artifact,
)
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate
from piece_v2_contract import canonical_sha256_hex
from piece_v2_visual import build_visual_recipe
from piece_v2_layout import TextMeasurement, build_measured_layout

PAIRS = (('大切にしたい', '大切にしたいです'),
         ('大切にしている', '大切にしています'),
         ('大切にしたくない', '大切にしたくないです'),
         ('望んでいる', '望んでいます'),
         ('望んでいない', '望んでいません'),
         ('選びたい', '選びたいです'),
         ('選びたくない', '選びたくないです'))
TARGETS = (('一人で静かに手帳を開く時間', '時間'),
           ('机で小さな紙を折ること', 'こと'),
           ('長く大切に使い続けてきたもの', 'もの'))
TARGET = TARGETS[0][0]
TAIL = 'まだ、毎朝続けるかは決めていません。'
SCOPES = (('落ち着いて考えられるので', 'SOURCE_EXPLICIT_REASON'),
          ('無理なく続けられるなら', 'SOURCE_EXPLICIT_CONDITION'),
          ('無理なく続けられるならば', 'SOURCE_EXPLICIT_CONDITION'),
          ('まだ迷っているけれど', 'SOURCE_EXPLICIT_CONCESSION'),
          ('まだ迷っているけれども', 'SOURCE_EXPLICIT_CONCESSION'))


def outcome(text):
    source = PieceSourceSnapshot('synthetic-owner', 'polite-transitive', '1', text)
    out = MeaningExperienceEngine().generate(PieceGenerationRequest(
        'polite-transitive', source, source.owner_id, source.saved_input_id, source.source_version))
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
@pytest.mark.parametrize('plain,polite', PAIRS)
def test_polite_expression_introduces_its_whole_argument_without_register_rewrite(target, head, plain, polite):
    text = '私は' + target + 'を' + polite + '。私はその' + head + 'が好きです。' + TAIL
    expected = '私は、' + target + 'を' + polite + '。私は、その' + head + 'が好きです。' + TAIL
    out = generated(text, expected)
    _, old_register = outcome(text.replace(polite, plain))
    assert old_register.status == EngineStatus.GENERATED
    assert old_register.artifact.piece_text == expected.replace(polite, plain)
    ref, = out.source_meaning.nominal_references
    assert text[slice(*ref.antecedent_scalar_span)] == target
    assert (ref.antecedent_node_id, ref.reference_node_id) == ('piece:s1', 'piece:s2')
    assert out.artifact_plan.block_node_ids == (('piece:s1', 'piece:s2', 'piece:s3'),)


@pytest.mark.parametrize('speaker', ('私', 'わたし', '僕', 'ぼく', '俺', 'おれ'))
@pytest.mark.parametrize('determiner', ('その', 'この'))
def test_polite_negative_reference_keeps_written_author_and_original_antecedent(speaker, determiner):
    first = speaker + 'は' + TARGET + 'を大切にしています。'
    second = speaker + 'は' + determiner + '時間を望んでいません。'
    out = generated(first + second + TAIL, speaker + 'は、' + TARGET + 'を大切にしています。'
                    + speaker + 'は、' + determiner + '時間を望んでいません。' + TAIL)
    ref, = out.source_meaning.nominal_references
    assert ref.antecedent_node_id == 'piece:s1'
    assert out.artifact_plan.duties[1].operation == 'SOURCE_TRANSITIVE_SELF_TOPIC'


@pytest.mark.parametrize('scope,relation', SCOPES)
@pytest.mark.parametrize('polite', ('大切にしています', '望んでいません', '選びたいです'))
def test_inner_polite_expression_keeps_scope_reference_and_reservation(scope, relation, polite):
    first = '僕にとって大切なのは、' + TARGET + 'です。'
    prefix = '僕は' + scope + '、'
    expression = '僕はその時間を' + polite + '。'
    text = first + prefix + expression + TAIL
    out = generated(text, '僕にとって、' + TARGET + 'が大切です。'
                    + prefix + 'その時間を' + polite + '。' + TAIL)
    info, = out.source_meaning.expression_scopes
    assert info.relation == relation
    assert text[slice(*info.expression_scalar_span)] == expression
    assert text.encode('utf-8')[slice(*info.expression_utf8_span)] == expression.encode('utf-8')
    assert not out.artifact_plan.declaration_eligible


@pytest.mark.parametrize('scope,relation', SCOPES)
def test_outer_premise_does_not_supply_a_different_inner_author(scope, relation):
    text = '私にとって大切なのは、' + TARGET + 'です。' + scope + '、僕はその時間を望んでいません。' + TAIL
    generated(text, '私にとって、' + TARGET + 'が大切です。' + scope + '、僕はその時間を望んでいません。' + TAIL)


@pytest.mark.parametrize('polite', ('大切にしています', '望んでいます', '望んでいません'))
def test_polite_state_remains_an_expression_without_a_shared_wish_label(monkeypatch, polite):
    import cocolon_meaning_experience_engine.piece_source as adapter
    monkeypatch.setattr(adapter, 'build_input_meaning_blocks', lambda **kwargs: ())
    out = generated('私は' + TARGET + 'を' + polite + '。' + TAIL,
                    '私は、' + TARGET + 'を' + polite + '。' + TAIL)
    assert out.artifact_plan.duties[0].operation == 'SOURCE_TRANSITIVE_SELF_TOPIC'


def test_polite_scoped_antecedent_retains_original_unicode_and_role_ranges():
    target = '同僚の秋山さんと静かに話す時間'
    text = '🌱を見た。\r\n\u3000僕は無理なく続けられるなら、僕は' + target + 'を大切にしています。\t僕はその時間が苦手ではありません。' + TAIL
    out = generated(text, '🌱を見た。\n\n僕は無理なく続けられるなら、同僚と静かに話す時間を大切にしています。'
                    + '僕は、その時間が苦手ではありません。' + TAIL)
    ref, = out.source_meaning.nominal_references
    assert text[slice(*ref.antecedent_scalar_span)] == target
    assert ref.antecedent_scalar_span[0] == text.index(target)
    assert '秋山' not in out.artifact.piece_text


@pytest.mark.parametrize('predicate', ('望んでいました', '望んでいませんでした',
    '望んでいますかもしれない', '望んでいるです', '望んでいないです',
    '大切にしたいでした', '大切にしていました', '選びます', '選びません',
    '好きです', '望んでいますと聞いた'))
def test_other_tense_modal_predicate_and_report_are_not_granted_transitive_authority(predicate):
    sentence = '私はその時間を' + predicate + '。'
    assert _direct_transitive_expression(sentence) is None
    first = '私にとって大切なのは、' + TARGET + 'です。'
    assert outcome(first + 'まだ迷っているけれど、' + sentence + TAIL)[1].status == EngineStatus.UNAVAILABLE


@pytest.mark.parametrize('first', (
    '私は空を眺めた。',
    '私は空いた時間に手帳を開いた。',
    '彼は一人で静かに手帳を開く時間を望んでいます。',
    '私は一人で静かに手帳を開く時間を望んでいます。私は川辺で散歩する時間を望んでいます。',
    '私は一人で静かに手帳を開く時間を望んでいます。別の時間に外出した。',
))
def test_polite_register_does_not_guess_an_unknown_or_competing_referent(first):
    assert outcome(first + '私はその時間が好きです。' + TAIL)[1].status == EngineStatus.UNAVAILABLE


@pytest.mark.parametrize('mutation', ('reference', 'scope', 'operation', 'drop_context'))
def test_polite_register_cannot_bypass_source_or_plan_binding(mutation):
    text = '僕は' + TARGET + 'を大切にしています。僕はまだ迷っているけれど、僕はその時間を望んでいません。' + TAIL
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
        duties = list(plan.duties)
        duties[0] = replace(duties[0], operation='KEEP_COMPLETE_SOURCE_CONTEXT')
        plan = replace(plan, duties=tuple(duties))
    else:
        plan = replace(plan, block_node_ids=(('piece:s1', 'piece:s2'),))
    with pytest.raises(ValueError):
        realize_piece_artifact(meaning, plan, tier='free', requested_format=None)


class Metrics:
    profile_id = 'polite-transitive-synthetic-not-native'
    def graphemes(self, text):
        return list(text)
    def measure(self, text, font_px):
        width = len(text) * font_px
        return TextMeasurement(width, 0, -font_px * .8, width, font_px * .2)


@pytest.mark.parametrize('ratio', ('4:5', '9:16'))
def test_complete_polite_body_enters_existing_layout(ratio):
    text = '私は' + TARGET + 'を大切にしています。私はその時間が好きです。' + TAIL
    _, out = outcome(text)
    assert out.status == EngineStatus.GENERATED
    candidate = out.artifact.as_candidate()
    recipe = build_visual_recipe('short_essay', tier='premium', aspect_ratio=ratio)
    layout = build_measured_layout(candidate, recipe, canonical_sha256_hex(recipe), Metrics())
    assert [''.join(row['text'] for row in layout['lines'] if row['block_index'] == i)
            for i in range(len(out.artifact.body_blocks))] == list(out.artifact.body_blocks)
    assert layout['piece_text_hash'] == candidate['piece_text_hash']
