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
from cocolon_meaning_experience_engine.piece_source import _calendar_time_adverb_span

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


@pytest.mark.parametrize('speaker', ('私', 'わたし'))
@pytest.mark.parametrize('comma', ('', '、'))
@pytest.mark.parametrize('gap', (' ', '\t', '\u3000'))
@pytest.mark.parametrize('time', ('これから毎朝', 'これから3日間、'))
def test_self_topic_horizontal_pause_keeps_existing_calendar_and_duration(time, gap, comma, speaker):
    body = time + '窓辺の葉を眺めたい。'
    text = speaker + 'は' + comma + gap + body
    expected = speaker + 'は、' + gap + body
    tail = 'まだ続けるかは決めていない。'
    actual = assert_body(text + tail, expected + tail)
    span = _calendar_time_adverb_span(text)
    assert span == (text.index('これから'), text.index('これから') + len('これから'))
    assert text[slice(*span)] == 'これから'
    assert actual.source_meaning.nominal_references == ()
    assert not actual.artifact_plan.declaration_eligible


@pytest.mark.parametrize('gap', ('\n', '\u00a0', '\u200b', ' 、'))
@pytest.mark.parametrize('time', ('これから毎朝', 'これから3日間、'))
def test_topic_pause_does_not_admit_unproved_calendar_separators(gap, time):
    text = '私は、' + gap + time + '窓辺の葉を眺めたい。'
    assert _calendar_time_adverb_span(text) is None
    actual = outcome(text + 'まだ続けるかは決めていない。')
    assert actual.status == EngineStatus.UNAVAILABLE and actual.artifact is None


@pytest.mark.parametrize('mode', ('平穏', '自己理解'))
@pytest.mark.parametrize('gap', (' ', '\t', '\u3000'))
@pytest.mark.parametrize('time', ('これから毎朝', 'これから3日間、'))
def test_saved_topic_pause_retains_source_fields_and_author_free_review(monkeypatch, mode, gap, time):
    from test_b05a_piece_saved_original_generation import row, source, outcome as saved_outcome, OWNER
    import api_account_visibility
    from cocolon_meaning_experience_engine import piece_v1c
    from piece_v2_content_policy import validate_source_meaning_preservation
    from piece_v2_contract import canonical_json_bytes

    async def synthetic_owner(token):
        assert token == 'synthetic-owner-session'
        return OWNER
    monkeypatch.setattr(api_account_visibility, '_resolve_user_id_from_token', synthetic_owner)
    text = '私は、' + gap + time + '窓辺の葉を眺めたい。'
    tail = 'まだ続けるかは決めていない。'
    value = row(text, tail)
    value['original']['emotions'] = [mode]
    value['original']['emotion_details'] = [{'type': mode, 'strength': 'medium'}]
    raw = canonical_json_bytes(value['original'])
    actual = saved_outcome(source(value))
    assert actual.status == EngineStatus.GENERATED, actual.as_body_free()
    assert actual.source_meaning.saved_snapshot.saved_original_json == raw
    assert canonical_json_bytes(value['original']) == raw
    assert actual.artifact.piece_text == text + '\n\n' + tail
    assert actual.artifact.eligible_formats == ('short_essay',)
    def forbidden(*args, **kwargs):
        pytest.fail('saved preservation review must not generate or author')
    monkeypatch.setattr(MeaningExperienceEngine, 'generate', forbidden)
    monkeypatch.setattr(piece_v1c, 'compile_piece_artifact_plan', forbidden)
    monkeypatch.setattr(piece_v1c, 'realize_piece_artifact', forbidden)
    validate_source_meaning_preservation(actual.source_meaning, actual.artifact_plan, actual.artifact)
    changed_text = actual.artifact.piece_text.replace('これから', '昨日から', 1)
    changed = replace(actual.artifact, body_blocks=tuple(changed_text.split('\n\n')),
        piece_text=changed_text, piece_text_hash=hashlib.sha256(changed_text.encode()).hexdigest())
    with pytest.raises(ValueError, match='piece_meaning_not_preserved'):
        validate_source_meaning_preservation(actual.source_meaning, actual.artifact_plan, changed)


@pytest.mark.parametrize('opening', ('私は', 'ただ、わたしは、\t', 'しかし、僕は\u3000'))
@pytest.mark.parametrize('time', ('これから毎朝', 'これから3日間、'))
@pytest.mark.parametrize('stop', ('！', '!'))
def test_self_topic_calendar_exclamation_keeps_literal_time_and_terminator(opening, time, stop):
    first = opening + time + '窓辺の葉を眺めたい' + stop
    tail = 'まだ続けるかは決めていない。'
    actual = assert_body(FOCAL + first + tail, BODY + first + tail)
    start = first.index('これから')
    assert _calendar_time_adverb_span(first) == (start, start + len('これから'))
    assert actual.source_meaning.nominal_references == ()
    assert actual.artifact_plan.duties[1].operation == 'KEEP_COMPLETE_SOURCE_CONTEXT'
    assert actual.artifact.eligible_formats == ('short_essay',)
    assert not actual.artifact_plan.declaration_eligible


@pytest.mark.parametrize('mode', ('平穏', '自己理解'))
@pytest.mark.parametrize('time', ('これから毎朝', 'これから3日間、'))
@pytest.mark.parametrize('stop', ('！', '!'))
def test_saved_calendar_exclamation_retains_fields_and_author_free_review(monkeypatch, mode, time, stop):
    from test_b05a_piece_saved_original_generation import row, source, outcome as saved_outcome, OWNER
    import api_account_visibility
    from cocolon_meaning_experience_engine import piece_v1c
    from piece_v2_content_policy import validate_source_meaning_preservation
    from piece_v2_contract import canonical_json_bytes

    async def synthetic_owner(token):
        assert token == 'synthetic-owner-session'
        return OWNER
    monkeypatch.setattr(api_account_visibility, '_resolve_user_id_from_token', synthetic_owner)
    first = 'わたしは、\t' + time + '窓辺の🌿の形を静かに眺めたい' + stop
    tail = '続けるかはまだ決めていない。'
    value = row(first, tail)
    value['original']['emotions'] = [mode]
    value['original']['emotion_details'] = [{'type': mode, 'strength': 'medium'}]
    raw = canonical_json_bytes(value['original'])
    actual = saved_outcome(source(value))
    assert actual.status == EngineStatus.GENERATED, actual.as_body_free()
    assert actual.source_meaning.saved_snapshot.saved_original_json == raw
    assert canonical_json_bytes(value['original']) == raw
    assert actual.artifact.body_blocks == (first, tail)
    assert actual.artifact.piece_text == first + '\n\n' + tail
    assert actual.artifact.eligible_formats == ('short_essay',)
    for node, evidence in zip(actual.source_meaning.graph.nodes, actual.source_meaning.evidence, strict=True):
        field = value['original'][evidence.field_path]
        assert field[evidence.scalar_start:evidence.scalar_end] == node.value
        assert actual.source_meaning.envelope.raw_utf8[evidence.utf8_start:evidence.utf8_end].decode() == node.value
    def forbidden(*args, **kwargs):
        pytest.fail('saved preservation review must not generate or author')
    monkeypatch.setattr(MeaningExperienceEngine, 'generate', forbidden)
    monkeypatch.setattr(piece_v1c, 'compile_piece_artifact_plan', forbidden)
    monkeypatch.setattr(piece_v1c, 'realize_piece_artifact', forbidden)
    validate_source_meaning_preservation(actual.source_meaning, actual.artifact_plan, actual.artifact)
    for old, new in (('これから', '昨日から'), (stop, '。')):
        changed_text = actual.artifact.piece_text.replace(old, new, 1)
        changed = replace(actual.artifact, body_blocks=tuple(changed_text.split('\n\n')),
            piece_text=changed_text, piece_text_hash=hashlib.sha256(changed_text.encode()).hexdigest())
        with pytest.raises(ValueError, match='piece_meaning_not_preserved'):
            validate_source_meaning_preservation(actual.source_meaning, actual.artifact_plan, changed)


@pytest.mark.parametrize('stop', ('！', '!'))
@pytest.mark.parametrize('first', (
    '私はこれから3日間窓辺の葉を眺めたい',
    '私はそれから毎朝窓辺の葉を眺めたい',
    '私はあれから毎朝窓辺の葉を眺めたい',
    '私はこれから毎日の予定を眺めたい',
    '私はこれから毎朝眺める時間が好きです',
    '私は窓辺でこれから毎朝眺めるものを選びたい',
))
def test_calendar_exclamation_does_not_resolve_nominal_or_other_deictic_uses(first, stop):
    actual = outcome(first + stop + 'まだ続けるかは決めていない。')
    assert actual.status == EngineStatus.UNAVAILABLE and actual.artifact is None


@pytest.mark.parametrize('stop', ('！！', '!?', '！。', '？'))
def test_calendar_topic_view_does_not_complete_other_terminators(stop):
    actual = outcome('私はこれから毎朝窓辺の葉を眺めたい' + stop + 'まだ続けるかは決めていない。')
    assert actual.status == EngineStatus.UNAVAILABLE and actual.artifact is None


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
