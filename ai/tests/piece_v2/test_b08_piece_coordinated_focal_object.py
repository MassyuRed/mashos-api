"""A source-explicit focal object keeps both coordinated nominal referents.

Synthetic inputs only. Existing predicate/source/format/image owners remain
unchanged; this does not infer an author, a referent, or a current commitment.
"""
from dataclasses import asdict, replace
import hashlib

import pytest

from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.piece_v1c import (
    PieceGenerationRequest, compile_piece_artifact_plan, realize_piece_artifact,
)
from piece_v2_contract import canonical_sha256_hex
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate
from piece_v2_layout import TextMeasurement, build_measured_layout
from piece_v2_visual import build_visual_recipe

TIME = '休日に台所でゆっくりお茶をいれる時間'
ACT = '気づいた考えを短く手帳に残すこと'
THING = '長い間大事に使ってきたもの'
TAIL = 'まだ毎週続けるかどうかは決めていない。'


def outcome(source, *, tier='free', requested_format=None):
    snap = PieceSourceSnapshot('synthetic-owner', 'focal-coordination', 'v1', source)
    return MeaningExperienceEngine().generate(PieceGenerationRequest(
        'focal-coordination', snap, snap.owner_id, snap.saved_input_id,
        snap.source_version, tier=tier, requested_format=requested_format))


def intro(speaker='私', first=TIME, second=ACT):
    return (speaker + 'が大切にしたいのは、' + first + 'です。'
            + speaker + 'が選びたいのは、' + second + 'です。')


def source(predicate='大切にしたい', pair='その時間とこのこと', speaker='私'):
    return intro(speaker) + speaker + 'が' + predicate + 'のは、' + pair + 'です。' + TAIL


def body(predicate='大切にしたい', pair='その時間とこのこと', speaker='私'):
    return (speaker + 'は、' + TIME + 'を大切にしたい。' + ACT + 'を選びたい。'
            + pair + 'を' + predicate + '。' + TAIL)


def assert_body(text, expected, *, tier='free'):
    out = outcome(text, tier=tier)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    meaning, plan, artifact = out.source_meaning, out.artifact_plan, out.artifact
    assert artifact.piece_text == expected
    assert artifact.piece_text_hash == hashlib.sha256(expected.encode()).hexdigest()
    assert meaning.envelope.raw_utf8 == text.encode()
    assert compile_piece_artifact_plan(meaning) == plan
    assert tuple(n for block in plan.block_node_ids for n in block) == tuple(n.node_id for n in meaning.graph.nodes)
    for node, ev in zip(meaning.graph.nodes, meaning.evidence, strict=True):
        assert text[ev.scalar_start:ev.scalar_end] == node.value
        assert text.encode()[ev.utf8_start:ev.utf8_end] == node.value.encode()
    for ref in meaning.nominal_references:
        for scalar, utf8 in ((ref.antecedent_scalar_span, ref.antecedent_utf8_span),
                             (ref.reference_scalar_span, ref.reference_utf8_span)):
            assert text[slice(*scalar)].encode() == text.encode()[slice(*utf8)]
    frozen = asdict(meaning), asdict(plan)
    assert realize_piece_artifact(meaning, plan, tier=tier, requested_format=None) == artifact
    assert (asdict(meaning), asdict(plan)) == frozen
    assert generate_piece_candidate(PieceSourceSnapshot(
        'synthetic-owner', 'focal-coordination', 'v1', text),
        authenticated_owner_id='synthetic-owner', tier=tier) == artifact.as_candidate()
    assert artifact.eligible_formats == ('short_essay',)
    assert not out.automatic_progression and not artifact.as_candidate()['production_enabled']
    assert artifact.as_candidate()['record_effect'] == artifact.as_candidate()['quota_effect'] == 0
    return out


@pytest.mark.parametrize('pair', ('その時間とこのこと', 'このこととその時間',
                                  'その時間と、このこと', 'このことと，\tその時間',
                                  'その時間と,　このこと'))
def test_focal_and_direct_word_orders_keep_the_same_whole_argument(pair):
    out = assert_body(source(pair=pair), body(pair=pair))
    direct = outcome(intro() + '私は' + pair + 'を大切にしたい。' + TAIL)
    assert out.artifact == direct.artifact
    refs = out.source_meaning.nominal_references
    assert len(refs) == 2
    assert [r.antecedent_node_id for r in refs] == (
        ['piece:s1', 'piece:s2'] if pair.startswith('その時間') else ['piece:s2', 'piece:s1'])
    assert len([e for e in out.source_meaning.graph.edges
                if e.relation == 'SOURCE_BOUND_NOMINAL_REFERENCE']) == 2
    assert out.artifact_plan.duties[2].operation == 'SOURCE_FOCAL_TO_FIRST_PERSON'


@pytest.mark.parametrize('predicate', ('大切にしたい', '大切にしている', '大切にしたくない',
                                       '望んでいる', '望んでいない', '選びたい', '選びたくない'))
def test_all_existing_focal_predicates_keep_their_written_stance(predicate):
    assert_body(source(predicate), body(predicate))


@pytest.mark.parametrize('speaker', ('私', 'わたし', '僕', 'ぼく', '俺', 'おれ'))
def test_same_source_written_author_can_be_shared(speaker):
    assert_body(source(speaker=speaker), body(speaker=speaker))


@pytest.mark.parametrize('first,second,pair', (
    (TIME, THING, 'このものとその時間'), (ACT, THING, 'そのこととこのもの'),
))
def test_other_existing_nominal_heads_keep_both_source_objects(first, second, pair):
    text = intro(first=first, second=second) + '私が望んでいないのは、' + pair + 'です。' + TAIL
    assert_body(text, '私は、' + first + 'を大切にしたい。' + second
                + 'を選びたい。' + pair + 'を望んでいない。' + TAIL)


@pytest.mark.parametrize('scope', ('予定が合うなら', '予定が合うならば', '予定が合うので',
                                   '予定は合わないけれど', '予定は合わないけれども'))
def test_written_scope_remains_outside_the_complete_focal_object(scope):
    text = intro() + scope + '、私が選びたくないのは、その時間とこのことです。' + TAIL
    expected = ('私は、' + TIME + 'を大切にしたい。私は、' + ACT + 'を選びたい。'
                + scope + '、私はその時間とこのことを選びたくない。' + TAIL)
    out = assert_body(text, expected)
    scoped, = out.source_meaning.expression_scopes
    assert text[slice(*scoped.scope_scalar_span)] == scope
    assert len(out.source_meaning.nominal_references) == 2


@pytest.mark.parametrize('gap', ('\n', '\r\n', '今日は食器を片付けた。'))
def test_source_boundaries_decline_only_optional_author_omission(gap):
    text = intro() + gap + '私が望んでいないのは、その時間とこのことです。' + TAIL
    context = gap if gap.endswith('。') else ''
    assert_body(text, '私は、' + TIME + 'を大切にしたい。私は、' + ACT
                + 'を選びたい。' + context + '私は、その時間とこのことを望んでいない。' + TAIL)


@pytest.mark.parametrize('second,third', (('僕', '私'), ('私', '僕'), ('わたし', '私')))
def test_different_written_speakers_are_not_equated(second, third):
    text = ('私が大切にしたいのは、' + TIME + 'です。' + second + 'が選びたいのは、'
            + ACT + 'です。' + third + 'が大切にしたいのは、その時間とこのことです。' + TAIL)
    assert_body(text, '私は、' + TIME + 'を大切にしたい。' + second + 'は、' + ACT
                + 'を選びたい。' + third + 'は、その時間とこのことを大切にしたい。' + TAIL)


def test_explicit_viewpoints_are_not_deleted_or_promoted_to_wishes():
    text = ('私にとって' + TIME + 'が大切でした。私にとって' + ACT
            + 'が必要かもしれません。私が望んでいないのは、その時間とこのことです。' + TAIL)
    assert_body(text, '私にとって、' + TIME + 'が大切でした。私にとって、' + ACT
                + 'が必要かもしれません。その時間とこのことを望んでいない。' + TAIL)


def test_direct_antecedents_keep_past_time_and_modality():
    text = ('私は' + TIME + 'を望んでいませんでした。私は' + ACT
            + 'を選びたくなかったかもしれません。私が大切にしているのは、このこととその時間です。' + TAIL)
    assert_body(text, '私は、' + TIME + 'を望んでいませんでした。' + ACT
                + 'を選びたくなかったかもしれません。このこととその時間を大切にしている。' + TAIL)


def test_original_utf8_binding_precedes_existing_role_publicization():
    target = '私の友人の森田さんと🍵を楽しむ時間'
    out = assert_body(source().replace(TIME, target), body().replace(TIME, '私の友人と🍵を楽しむ時間'))
    assert out.source_meaning.envelope.raw_utf8.decode()[slice(*out.source_meaning.nominal_references[0].antecedent_scalar_span)] == target
    assert '森田' not in out.artifact.piece_text


@pytest.mark.parametrize('expression', (
    '大切にしたいのは、その時間とこのことです。',
    '彼が大切にしたいのは、その時間とこのことです。',
    '私が大切にしたいのは、その時間とこの時間です。',
    '私が大切にしたいのは、その時間とこのものです。',
    '私が大切にしたいのは、その時間とあのことです。',
    '私が大切にしたいのは、その時間と長いこのことです。',
    '私が大切にしたいのは、その時間とこのこととその時間です。',
    '私が大切にしたいのは、その時間よりこのことです。',
    '私が大切にしたいのは、その時間かこのことです。',
    '私が振り返ったのは、その時間とこのことです。',
    '私が大切にしたかったのは、その時間とこのことです。',
    '私が望んでいるかもしれないのは、その時間とこのことです。',
    '以前は、私が大切にしたいのは、その時間とこのことです。',
))
def test_no_author_referent_comparison_or_new_focal_grammar_is_inferred(expression):
    out = outcome(intro() + expression + TAIL)
    assert out.status == EngineStatus.UNAVAILABLE and out.artifact is None


@pytest.mark.parametrize('text', (
    '私が大切にしたいのは、その時間とこのことです。' + TAIL,
    intro() + '私は公園で過ごす時間を選びたい。私が大切にしたいのは、その時間とこのことです。' + TAIL,
    'ことの始まりを考えていた。' + source(),
))
def test_missing_or_ambiguous_antecedents_remain_unavailable(text):
    assert outcome(text).status == EngineStatus.UNAVAILABLE


@pytest.mark.parametrize('damage', ('reference', 'target', 'utf8', 'edge', 'plan'))
def test_both_references_and_complete_reading_group_are_required(damage):
    out = outcome(source()); assert out.status == EngineStatus.GENERATED, out.as_body_free()
    meaning, plan = out.source_meaning, out.artifact_plan
    first, second = meaning.nominal_references
    if damage == 'reference':
        meaning = replace(meaning, nominal_references=(first,))
    elif damage in ('target', 'utf8'):
        field = 'antecedent_scalar_span' if damage == 'target' else 'reference_utf8_span'
        a, b = getattr(second, field)
        meaning = replace(meaning, nominal_references=(first, replace(second, **{field: (a + 1, b)})))
    elif damage == 'edge':
        meaning = replace(meaning, graph=replace(meaning.graph, edges=meaning.graph.edges[:-1]))
    else:
        plan = replace(plan, block_node_ids=(('piece:s1',), ('piece:s2', 'piece:s3', 'piece:s4')))
    with pytest.raises(ValueError):
        realize_piece_artifact(meaning, plan, tier='free', requested_format=None)


@pytest.mark.parametrize('tier', ('free', 'plus', 'premium'))
def test_format_selection_does_not_excerpt_either_object_or_reservation(tier):
    assert_body(source(), body(), tier=tier)
    for fmt in ('quote', 'declaration'):
        out = outcome(source(), tier=tier, requested_format=fmt)
        assert out.status == EngineStatus.UNAVAILABLE
        assert out.reason_codes == ('format_choice_not_admitted',)


@pytest.mark.parametrize('ratio', ('4:5', '9:16'))
def test_canonical_focal_body_reaches_the_existing_measured_layout(ratio):
    out = outcome(source()); assert out.status == EngineStatus.GENERATED, out.as_body_free()
    candidate = out.artifact.as_candidate()
    class Metrics:
        profile_id = 'synthetic-focal-coordination-not-native'
        def graphemes(self, value): return list(value)
        def measure(self, value, size):
            width = len(value) * size
            return TextMeasurement(width, 0, -.8 * size, width, .2 * size)
    recipe = build_visual_recipe('short_essay', tier='premium', aspect_ratio=ratio)
    layout = build_measured_layout(candidate, recipe, canonical_sha256_hex(recipe), Metrics())
    assert [''.join(row['text'] for row in layout['lines'] if row['block_index'] == i)
            for i in range(len(out.artifact.body_blocks))] == list(out.artifact.body_blocks)
    assert layout['piece_text_hash'] == candidate['piece_text_hash']
    assert not layout['native_device_verified']


def test_optional_omission_is_not_source_or_plan_mutation(monkeypatch):
    import cocolon_meaning_experience_engine.piece_v1c as author
    out = outcome(source()); assert out.status == EngineStatus.GENERATED
    frozen = asdict(out.source_meaning), asdict(out.artifact_plan)
    monkeypatch.setattr(author, '_paired_self_continuations', lambda *args: frozenset())
    full = realize_piece_artifact(out.source_meaning, out.artifact_plan, tier='free', requested_format=None)
    assert full.piece_text == ('私は、' + TIME + 'を大切にしたい。私は、' + ACT
                               + 'を選びたい。私は、その時間とこのことを大切にしたい。' + TAIL)
    assert (asdict(out.source_meaning), asdict(out.artifact_plan)) == frozen
