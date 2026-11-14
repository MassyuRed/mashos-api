"""Synthetic source-marked reason/condition -> canonical Piece body checks."""
from dataclasses import replace
import hashlib
import json

import pytest
from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.piece_v1c import (
    PieceGenerationRequest, compile_piece_artifact_plan, realize_piece_artifact,
)
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate
from piece_v2_contract import canonical_sha256_hex
from piece_v2_visual import build_visual_recipe
from piece_v2_layout import TextMeasurement, build_measured_layout


CASES = [
    ('集中できる時間が少ないので、私は朝の予定を少し減らしたい。',
     '私は、集中できる時間が少ないので、朝の予定を少し減らしたい。', 'SOURCE_EXPLICIT_REASON'),
    ('一度には答えを出せないので、私は自分の考えを順番に整理したい。',
     '私は、一度には答えを出せないので、自分の考えを順番に整理したい。', 'SOURCE_EXPLICIT_REASON'),
    ('昨日は十分に話せなかったので、僕は次に会うときは最後まで話を聞きたい。',
     '僕は、昨日は十分に話せなかったので、次に会うときは最後まで話を聞きたい。', 'SOURCE_EXPLICIT_REASON'),
    ('まだ少し不安なので、わたしは答えを急がず自分のペースで考えたいです。',
     'わたしは、まだ少し不安なので、答えを急がず自分のペースで考えたいです。', 'SOURCE_EXPLICIT_REASON'),
    ('明日は疲れているかもしれないので、私は予定を詰め込みたくない。',
     '私は、明日は疲れているかもしれないので、予定を詰め込みたくない。', 'SOURCE_EXPLICIT_REASON'),
    ('相手にも余裕があるなら、私は焦らずに自分の考えを伝えたい。',
     '私は、相手にも余裕があるなら、焦らずに自分の考えを伝えたい。', 'SOURCE_EXPLICIT_CONDITION'),
    ('明日の朝に時間が取れるならば、私は静かな場所で少し本を読みたい。',
     '私は、明日の朝に時間が取れるならば、静かな場所で少し本を読みたい。', 'SOURCE_EXPLICIT_CONDITION'),
    ('まだ気持ちが落ち着かないなら、私は無理に話を続けたくない。',
     '私は、まだ気持ちが落ち着かないなら、無理に話を続けたくない。', 'SOURCE_EXPLICIT_CONDITION'),
    ('今日は一人で過ごせるなら、ぼくは好きな曲をゆっくり聴いてみたい。',
     'ぼくは、今日は一人で過ごせるなら、好きな曲をゆっくり聴いてみたい。', 'SOURCE_EXPLICIT_CONDITION'),
    ('友人の佐藤さんと昨日は話せなかったので、私は次に会うときは落ち着いて話したい。まだ、会う日は決めていない。',
     '私は、友人と昨日は話せなかったので、次に会うときは落ち着いて話したい。まだ、会う日は決めていない。', 'SOURCE_EXPLICIT_REASON'),
    ('友人の佐藤さんが時間を取れるなら、私は無理のない日にゆっくり話したい。まだ、返事はもらっていない。',
     '私は、友人が時間を取れるなら、無理のない日にゆっくり話したい。まだ、返事はもらっていない。', 'SOURCE_EXPLICIT_CONDITION'),
    ('昨日は上司の田中さんと話した。気持ちが整理できるなら、私は田中さんに自分の考えを伝えたい。ただし、まだ何を伝えるかは決めていない。',
     '昨日は上司と話した。私は、気持ちが整理できるなら、自分の考えを上司に伝えたい。ただし、まだ何を伝えるかは決めていない。', 'SOURCE_EXPLICIT_CONDITION'),
]
# No argument-order rewrite is authorized: retain the original argument order.
CASES[-1] = (CASES[-1][0], CASES[-1][1].replace('自分の考えを上司に', '上司に自分の考えを'), CASES[-1][2])


def run(text, **changes):
    request = PieceGenerationRequest('synthetic-scope-request',
        PieceSourceSnapshot('synthetic-owner', 'synthetic-scope-source', 'v1', text),
        'synthetic-owner', 'synthetic-scope-source', 'v1')
    return MeaningExperienceEngine().generate(replace(request, **changes))


def generated(text, **changes):
    out = run(text, **changes)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    assert out.artifact is not None
    return out


@pytest.mark.parametrize('source,expected,relation', CASES)
def test_actual_scoped_meaning_reaches_existing_b8_body(source, expected, relation):
    out = generated(source)
    assert out.artifact.piece_text == expected
    assert out.artifact.body_blocks == (expected,)
    assert out.artifact.eligible_formats == ('short_essay',)
    assert out.source_meaning.expression_scopes[0].relation == relation
    scopes = {s.node_id for s in out.source_meaning.expression_scopes}
    assert all(d.operation == 'SOURCE_SCOPED_EXPRESSION_TO_FIRST_PERSON'
               for d in out.artifact_plan.duties if d.node_id in scopes)
    assert generate_piece_candidate(PieceSourceSnapshot('synthetic-owner', 'synthetic-scope-source', 'v1', source),
                                    authenticated_owner_id='synthetic-owner') == out.artifact.as_candidate()
    assert out.artifact.piece_text_hash == hashlib.sha256(expected.encode('utf-8')).hexdigest()


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
def test_condition_is_not_an_unqualified_declaration_or_detached_quote(tier):
    out = generated(CASES[10][0], tier=tier)
    assert out.artifact.format_type == 'short_essay'
    assert not out.artifact_plan.declaration_eligible
    assert out.artifact.piece_text == CASES[10][1]
    for requested in ('quote', 'declaration'):
        refused = run(CASES[10][0], tier='premium', requested_format=requested)
        assert refused.status == EngineStatus.UNAVAILABLE and refused.artifact is None


@pytest.mark.parametrize('speaker', ('私', 'ぼく', '俺'))
@pytest.mark.parametrize('operator', ('ので', 'なら', 'ならば', 'けれど', 'けれども'))
@pytest.mark.parametrize('separator', ('、', '，', ','))
@pytest.mark.parametrize('tier', ('free', 'plus', 'premium'))
def test_qualification_inside_the_existing_self_topic_retains_short_essay(speaker, operator, separator, tier):
    text = f'{speaker}は余裕がある{operator}{separator}陶芸を選びたい。'
    out = generated(text, tier=tier)
    expected = f'{speaker}は、余裕がある{operator}{separator}陶芸を選びたい。'
    assert out.artifact.piece_text == expected
    assert out.artifact.eligible_formats == ('short_essay',)
    assert out.artifact.format_type == 'short_essay'
    assert not out.artifact_plan.declaration_eligible
    assert out.source_meaning.expression_scopes == ()
    assert out.artifact_plan.duties[0].operation == 'SOURCE_FIRST_PERSON_TOPIC'
    source = PieceSourceSnapshot('synthetic-owner', 'synthetic-scope-source', 'v1', text)
    assert generate_piece_candidate(source, authenticated_owner_id=source.owner_id,
        tier=tier) == out.artifact.as_candidate()
    assert out.source_meaning.envelope.raw_utf8 == text.encode('utf-8')


@pytest.mark.parametrize('operator', ('ので', 'なら', 'ならば', 'けれど', 'けれども'))
@pytest.mark.parametrize('requested_format', ('quote', 'declaration'))
def test_topic_first_qualification_cannot_be_requested_as_an_unqualified_format(operator, requested_format):
    text = f'私は余裕がある{operator}、陶芸を選びたい。'
    out = run(text, tier='premium', requested_format=requested_format)
    assert out.status == EngineStatus.UNAVAILABLE and out.artifact is None


@pytest.mark.parametrize('text', (
    '私はたぶん読書する時間を選びたい。',
    '私にとっておそらく休む時間が大切です。',
    '私が選びたいのは、たぶん読書する時間です。',
    '私は分からないことを調べる時間を大切にしたい。',
))
def test_ambiguous_target_uncertainty_does_not_gain_a_declaration(text):
    out = generated(text)
    assert not out.artifact_plan.declaration_eligible
    assert 'declaration' not in out.artifact.eligible_formats


@pytest.mark.parametrize('target', ('自分の迷いを整理する時間', '迷いのない時間'))
@pytest.mark.parametrize('shape', (
    '私は{target}を選びたい。',
    '私が選びたいのは、{target}です。',
    '私にとって{target}が大切です。',
))
@pytest.mark.parametrize('tier', ('free', 'plus', 'premium'))
def test_bound_nominal_doubt_does_not_qualify_the_outer_commitment(target, shape, tier):
    text = shape.format(target=target)
    out = generated(text, tier=tier)
    assert out.artifact_plan.declaration_eligible
    assert 'declaration' in out.artifact.eligible_formats
    assert target in out.artifact.piece_text
    assert out.source_meaning.envelope.raw_utf8 == text.encode('utf-8')
    # Selecting another eligible format cannot author away the noun or add a vow.
    explicit = generated(text, tier='premium', requested_format='declaration')
    assert explicit.artifact.piece_text == out.artifact.piece_text
    assert explicit.artifact.piece_text_hash == out.artifact.piece_text_hash
    assert explicit.artifact.format_type == 'declaration'


@pytest.mark.parametrize('text', (
    '私はたぶん自分の迷いを整理する時間を選びたい。',
    '私が選びたいのは、おそらく自分の迷いを整理する時間です。',
    '私にとってたぶん迷いのない時間が大切です。',
    '私は自分の迷いを整理する時間を選びたいかもしれない。',
    '私が選びたいとは限らないのは、迷いのない時間です。',
    '私にとって迷いのない時間が大切かもしれない。',
    '私にとって迷いのない時間が大切ではありません。',
    '私にとって迷いのない時間が大切でした。',
    '私は自分の迷いを整理する時間を選びたかった。',
    '私は判断に迷いがちな時間を選びたい。',
    '私にとって判断に迷いにくい時間が大切です。',
    '私にとって迷いのだという時間が大切です。',
    '私は迷いのに考える時間を選びたい。',
    '余裕があるなら、私は迷いのない時間を選びたい。',
))
def test_nominal_doubt_keeps_real_reservations_past_and_unproved_inflections(text):
    out = generated(text, tier='premium')
    assert not out.artifact_plan.declaration_eligible
    assert 'declaration' not in out.artifact.eligible_formats


@pytest.mark.parametrize('text', (
    '私は自分の迷いを整理する時間を選びたい。',
    '私が選びたいのは、迷いのない時間です。',
    '私にとって自分の迷いを整理する時間が大切です。',
))
def test_author_free_offer_review_accepts_the_bound_nominal_doubt_plan(monkeypatch, text):
    import piece_v2_safety_review as review
    import cocolon_meaning_experience_engine.piece_v1c as author
    out = generated(text, tier='premium', requested_format='declaration')

    def forbidden(*args, **kwargs):
        raise AssertionError('Format review must not author or regenerate text.')

    monkeypatch.setattr(author, 'realize_piece_artifact', forbidden)
    assert review._check_formats(out.source_meaning, out.artifact_plan,
        out.artifact.content_payload(), out.artifact) is None


@pytest.mark.parametrize('operator', ('ので', 'なら', 'ならば', 'けれど', 'けれども'))
@pytest.mark.parametrize('offered', (None, 'quote', 'declaration'))
def test_author_free_format_review_matches_the_qualified_topic_offer(monkeypatch, operator, offered):
    import piece_v2_safety_review as review
    import cocolon_meaning_experience_engine.piece_v1c as author
    from piece_v2_contract import PieceContractError
    out = generated(f'私は余裕がある{operator}、陶芸を選びたい。')

    def forbidden(*args, **kwargs):
        raise AssertionError('Format review must not author or regenerate text.')

    monkeypatch.setattr(author, 'realize_piece_artifact', forbidden)
    artifact = out.artifact if offered is None else replace(out.artifact,
        eligible_formats=('short_essay', offered))
    if offered is None:
        assert review._check_formats(out.source_meaning, out.artifact_plan,
            artifact.content_payload(), artifact) is None
    else:
        with pytest.raises(PieceContractError) as error:
            review._check_formats(out.source_meaning, out.artifact_plan,
                artifact.content_payload(), artifact)
        assert error.value.code == 'PIECE_SAFETY_UNAVAILABLE'


@pytest.mark.parametrize('text', [
    '友人が遠くに住んでいる。私は手紙でゆっくり近況を伝えたい。',
    '私は、友人が遠くに住んでいるので手紙で近況を伝えたい。',
])
def test_no_invented_causal_link_or_change_to_existing_self_topic(text):
    out = generated(text)
    assert out.source_meaning.expression_scopes == ()
    if 'ので' not in text:
        assert 'ので' not in out.artifact.piece_text and 'から' not in out.artifact.piece_text


@pytest.mark.parametrize('text', [
    '駅から、私は静かな道を通ってゆっくり家まで歩いて帰りたい。',
    '友人が来るので、友人は一人でゆっくり話したい。',
    '雨が降るなら、私は出かけたいとは思っていない。',
    '時間が取れるなら、私は会いたいと言ってもらいたい。',
    '時間が取れるなら、私はそれをゆっくり考えてみたい。',
])
def test_unsupported_relation_report_ownership_and_reference_do_not_become_intentions(text):
    out = run(text)
    assert out.status == EngineStatus.UNAVAILABLE and out.artifact is None


def test_exact_clause_spans_include_unicode_negative_and_uncertain_material():
    text = '昨日は少し疲れていた。朝に花🌿を見ると落ち着くので、わたしは慌てずに一日を始めたい。まだ、毎日は難しいかもしれない。'
    out = generated(text)
    meaning = out.source_meaning
    scope = meaning.expression_scopes[0]
    raw = text.encode('utf-8')
    a, b = scope.scope_scalar_span
    c, d = scope.expression_scalar_span
    assert text[a:b] == raw[slice(*scope.scope_utf8_span)].decode() == '朝に花🌿を見ると落ち着くので'
    assert text[c:d] == raw[slice(*scope.expression_utf8_span)].decode() == 'わたしは慌てずに一日を始めたい。'
    assert out.artifact.piece_text.endswith('まだ、毎日は難しいかもしれない。')
    assert len(meaning.graph.nodes) == len(meaning.sentences) == len(meaning.evidence) == 3


@pytest.mark.parametrize('mutation', ['relation', 'marker', 'scope_span', 'intent_span', 'utf8', 'node_kind', 'drop'])
def test_writer_cannot_detach_or_forge_the_bound_scope(mutation):
    out = generated(CASES[10][0])
    meaning, plan = out.source_meaning, out.artifact_plan
    scope = meaning.expression_scopes[0]
    if mutation == 'relation': scope = replace(scope, relation='SOURCE_EXPLICIT_REASON')
    if mutation == 'marker': scope = replace(scope, marker='ので')
    if mutation == 'scope_span': scope = replace(scope, scope_scalar_span=(0, 1))
    if mutation == 'intent_span': scope = replace(scope, expression_scalar_span=(0, 1))
    if mutation == 'utf8': scope = replace(scope, scope_utf8_span=(0, 1))
    if mutation == 'node_kind':
        node = replace(meaning.graph.nodes[0], node_kind='PIECE_SOURCE_REASON_SCOPED_EXPRESSION')
        meaning = replace(meaning, graph=replace(meaning.graph, nodes=(node,)+meaning.graph.nodes[1:]))
    meaning = replace(meaning, expression_scopes=() if mutation == 'drop' else (scope,))
    with pytest.raises(ValueError):
        realize_piece_artifact(meaning, plan, tier='free', requested_format=None)


@pytest.mark.parametrize('ratio', ['4:5', '9:16'])
def test_same_qualified_canonical_body_reaches_b9_without_truncation(ratio):
    class Metrics:
        profile_id = 'synthetic-contract-not-native'
        def graphemes(self, text): return list(text)
        def measure(self, text, font_px):
            return TextMeasurement(len(text)*font_px, 0, -font_px*.8,
                                   len(text)*font_px, font_px*.2, True)
    out = generated(CASES[10][0])
    candidate = out.artifact.as_candidate()
    recipe = build_visual_recipe(candidate['format_type'], tier='premium', aspect_ratio=ratio)
    layout = build_measured_layout(candidate, recipe, canonical_sha256_hex(recipe), Metrics())
    assert ''.join(row['text'] for row in layout['lines']) == CASES[10][1]
    assert candidate['record_effect'] == candidate['quota_effect'] == 0
    assert candidate['production_enabled'] is False


def test_scope_body_and_names_are_private_not_diagnostics():
    out = generated(CASES[10][0])
    rendered = json.dumps(out.as_body_free(), ensure_ascii=False) + repr(out.source_meaning.expression_scopes)
    assert '佐藤' not in rendered and CASES[10][0] not in rendered
    assert 'synthetic-owner' not in rendered and '時間を取れる' not in rendered


def test_surface_comparison_is_kept_not_converted_to_a_wish_or_declaration():
    text = '少し身軽になれたので、私は旅に出る前の鳥みたい。'
    out = generated(text, tier='premium')
    assert out.artifact.piece_text == '私は、少し身軽になれたので、旅に出る前の鳥みたい。'
    assert out.artifact.eligible_formats == ('short_essay',)
    assert not out.artifact_plan.declaration_eligible
    assert 'なりたい' not in out.artifact.piece_text
