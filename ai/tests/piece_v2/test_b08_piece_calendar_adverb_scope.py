"""A clause-leading prospective calendar adverb is not a nominal referent.

Synthetic sources exercise the live Piece consumer. No global pronoun exemption,
inferred author/date, removed reservation, or activated product route.
"""
from dataclasses import asdict, replace
import hashlib
import pytest

from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.piece_v1c import (
    PieceGenerationRequest, compile_piece_artifact_plan, realize_piece_artifact,
)
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate
from piece_v2_expression import _REFERENCE
from piece_v2_contract import canonical_sha256_hex
from piece_v2_visual import build_visual_recipe
from piece_v2_layout import TextMeasurement, build_measured_layout

TARGET = '朝に窓辺で葉の形をゆっくり眺める時間'
FOCAL = '以前は、私が望んでいたかもしれないのは、' + TARGET + 'です。'
BODY = '以前は、私は' + TARGET + 'を望んでいたかもしれない。'


def outcome(text, *, tier='free', requested_format=None):
    s = PieceSourceSnapshot('synthetic-owner', 'calendar-adverb', 'v1', text)
    return MeaningExperienceEngine().generate(PieceGenerationRequest(
        'calendar-adverb', s, s.owner_id, s.saved_input_id, s.source_version,
        tier=tier, requested_format=requested_format))


def assert_body(text, expected, *, tier='free', requested_format=None):
    out = outcome(text, tier=tier, requested_format=requested_format)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    m, plan = out.source_meaning, out.artifact_plan
    assert m.envelope.raw_utf8 == text.encode()
    for node, ev in zip(m.graph.nodes, m.evidence, strict=True):
        assert text[ev.scalar_start:ev.scalar_end] == node.value
        assert text.encode()[ev.utf8_start:ev.utf8_end] == node.value.encode()
    assert tuple(n for b in plan.block_node_ids for n in b) == tuple(n.node_id for n in m.graph.nodes)
    assert compile_piece_artifact_plan(m) == plan
    saved = asdict(m), asdict(plan)
    assert realize_piece_artifact(m, plan, tier=tier, requested_format=requested_format) == out.artifact
    assert saved == (asdict(m), asdict(plan))
    source = PieceSourceSnapshot('synthetic-owner', 'calendar-adverb', 'v1', text)
    candidate = generate_piece_candidate(source, authenticated_owner_id=source.owner_id,
        tier=tier, requested_format=requested_format)
    assert candidate == out.artifact.as_candidate()
    assert candidate['piece_text'] == expected
    assert candidate['piece_text_hash'] == hashlib.sha256(expected.encode()).hexdigest()
    assert candidate['candidate_state'] == 'OFFLINE_NOT_ACCEPTED'
    assert not candidate['production_enabled'] and not out.automatic_progression
    assert candidate['record_effect'] == candidate['quota_effect'] == 0
    return out


@pytest.mark.parametrize('recurrence', ('毎日', '毎週', '毎月', '毎年', '毎朝', '毎晩'))
@pytest.mark.parametrize('link', ('', 'ただ、', 'しかし、'))
def test_calendar_time_and_undecided_continuation_stay_in_the_body(recurrence, link):
    tail = link + 'これから' + recurrence + '続けるかはまだ決めていない。'
    out = assert_body(FOCAL + tail, BODY + tail)
    assert out.source_meaning.nominal_references == ()
    assert len(out.source_meaning.expression_scopes) == 1
    assert out.artifact_plan.duties[-1].operation == 'KEEP_COMPLETE_SOURCE_CONTEXT'
    assert not out.artifact_plan.declaration_eligible
    assert out.artifact.eligible_formats == ('short_essay',)


@pytest.mark.parametrize('speaker', ('私', 'わたし', '僕', 'ぼく', '俺', 'おれ'))
def test_explicit_self_topic_is_not_inferred_from_time(speaker):
    tail = 'まだ続けるかは決めていない。'
    text = speaker + 'はこれから毎朝窓辺の葉を眺めたい。' + tail
    assert_body(text, speaker + 'は、これから毎朝窓辺の葉を眺めたい。' + tail)


@pytest.mark.parametrize('separator', ('、', '，', ',', '、\t', '、　', ' '))
def test_original_internal_spacing_and_calendar_adverb_are_not_normalized(separator):
    tail = 'ただ、これから' + separator + '毎週続けるかはまだ決めていない。'
    assert_body(FOCAL + tail, BODY + tail)


def test_actual_nominal_binding_is_separate_from_calendar_time():
    evaluation = '私はその時間が好きとは限りません。'
    tail = 'ただ、これから毎日続けるかはまだ決めていない。'
    out = assert_body(FOCAL + evaluation + tail, BODY + '私は、その時間が好きとは限りません。' + tail)
    ref, = out.source_meaning.nominal_references
    assert (ref.antecedent_node_id, ref.reference_node_id) == ('piece:s1', 'piece:s2')
    assert (FOCAL + evaluation + tail)[slice(*ref.reference_scalar_span)] == 'その時間'
    assert out.source_meaning.personal_evaluations[0].commitment == 'NON_UNIVERSAL'


@pytest.mark.parametrize('tail', (
    'ただ、これから取り出したものを見直している。',
    'ただ、これから毎日の予定を考えている。',
    'ただ、これから毎日を選ぶかはまだ決めていない。',
    'ただ、これから先の予定はまだ決めていない。',
    'ただ、それから毎日続けるかはまだ決めていない。',
    'ただ、あれから毎日続けるかはまだ決めていない。',
    'ただ、ここから毎日続けるかはまだ決めていない。',
    'ただ、あれこれから毎日選ぶかはまだ決めていない。',
    '彼はこれから毎日続けるかはまだ決めていない。',
    'ただ、これから毎日これを続けるかはまだ決めていない。',
    'ただ、これから毎日そのことを続けるかはまだ決めていない。',
    'ただ、これから毎日続けるかはまだ決めていない。これは大切だ。',
))
def test_temporal_token_does_not_exempt_other_or_ambiguous_deixis(tail):
    out = outcome(FOCAL + tail)
    assert out.status == EngineStatus.UNAVAILABLE and out.artifact is None


@pytest.mark.parametrize('text', (
    '私が望んでいるのは、これから毎日取り出すものです。',
    '私にとってこれから毎日選ぶことが大切です。',
    '私が好きなのは、これから毎日選ぶことです。',
    '以前は、私が望んでいたのは、これから毎日取り出すものです。',
    '都合が合うなら、私が選びたいのは、これから毎日使うものです。',
))
def test_calendar_adverb_is_not_searched_inside_nominal_arguments(text):
    out = outcome(text)
    assert out.status == EngineStatus.UNAVAILABLE and out.artifact is None


@pytest.mark.parametrize('text', (
    'これから毎日続けるかはまだ決めていない。',
    'ただ、これから毎日続けるかはまだ決めていない。',
    'これから毎朝眺めたい。',
    'ただ、これから毎日続けるかはまだ決めていない。彼は続けたい。',
))
def test_time_alone_supplies_no_piece_intent_or_author(text):
    out = outcome(text)
    assert out.status == EngineStatus.UNAVAILABLE and out.artifact is None


def test_temporal_context_before_a_terminal_wish_is_not_fronted():
    context = 'これから毎日続けるかはまだ決めていない。'
    wish = '私は窓辺の葉を眺めたい。'
    out = assert_body(context + wish, context + '\n\n私は、窓辺の葉を眺めたい。')
    assert out.artifact_plan.block_node_ids == (('piece:s1',), ('piece:s2',))


def test_unicode_newlines_and_explicit_role_keep_full_source_ranges():
    target = '私の友人の三浦さんと🌿の形を静かに眺める時間'
    first = '以前は、僕が望んでいたとは限らないのは、' + target + 'です。'
    tail = 'ただ、これから毎週続けるかはまだ決めていない。'
    text = '\t' + first + '\r\n　' + tail
    out = assert_body(text, '以前は、僕は私の友人と🌿の形を静かに眺める時間を望んでいたとは限らない。' + tail)
    assert out.source_meaning.sentences[1].source_start == text.index('ただ')


@pytest.mark.parametrize('tier', ('free', 'plus', 'premium'))
def test_time_and_reservation_cannot_be_excerpted_or_turned_into_a_pledge(tier):
    tail = 'ただ、これから毎日続けるかはまだ決めていない。'
    assert_body(FOCAL + tail, BODY + tail, tier=tier)
    for fmt in ('quote', 'declaration'):
        out = outcome(FOCAL + tail, tier=tier, requested_format=fmt)
        assert out.status == EngineStatus.UNAVAILABLE and out.artifact is None


def test_nominal_detector_itself_still_reports_the_whole_deictic_surface():
    # The change must not globally whitelist this spelling in other grammars.
    assert _REFERENCE.search('これから')[0] == 'これから'
    assert _REFERENCE.search('それから')[0] == 'それから'


@pytest.mark.parametrize('change', ('source_word', 'word_order', 'declaration'))
def test_forged_plan_or_source_cannot_remove_time_or_uncertainty(change):
    tail = 'ただ、これから毎日続けるかはまだ決めていない。'
    out = assert_body(FOCAL + tail, BODY + tail)
    m, plan = out.source_meaning, out.artifact_plan
    if change == 'source_word':
        nodes = m.graph.nodes
        m = replace(m, graph=replace(m.graph, nodes=(*nodes[:-1], replace(nodes[-1], value=tail.replace('これから', '')))))
    elif change == 'word_order':
        plan = replace(plan, block_node_ids=(('piece:s2', 'piece:s1'),))
    else:
        plan = replace(plan, declaration_eligible=True)
    with pytest.raises(ValueError):
        realize_piece_artifact(m, plan, tier='free', requested_format=None)


@pytest.mark.parametrize('ratio', ('4:5', '9:16'))
def test_exact_canonical_text_reaches_both_existing_layouts(ratio):
    tail = 'ただ、これから毎日続けるかはまだ決めていない。'
    out = assert_body(FOCAL + tail, BODY + tail)
    class Metrics:
        profile_id = 'synthetic-calendar-adverb-not-native'
        def graphemes(self, value): return list(value)
        def measure(self, value, size):
            width = len(value) * size
            return TextMeasurement(width, 0, -.8 * size, width, .2 * size)
    candidate = out.artifact.as_candidate()
    recipe = build_visual_recipe('short_essay', tier='premium', aspect_ratio=ratio)
    layout = build_measured_layout(candidate, recipe, canonical_sha256_hex(recipe), Metrics())
    assert [''.join(row['text'] for row in layout['lines'] if row['block_index'] == i)
            for i in range(len(out.artifact.body_blocks))] == list(out.artifact.body_blocks)
    assert layout['piece_text_hash'] == candidate['piece_text_hash']
    assert not layout['native_device_verified']


@pytest.mark.parametrize('speaker', ('私', 'わたし', '僕', 'ぼく', '俺', 'おれ'))
def test_short_statement_still_obeys_existing_content_envelope(speaker):
    text = speaker + 'はこれから毎朝窓辺の葉を眺めたい。'
    out = outcome(text)
    assert out.status == EngineStatus.UNAVAILABLE
    assert out.reason_codes == ('format_not_eligible',)
