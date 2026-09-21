"""Synthetic source-bound discourse tests, not user input or product acceptance."""
from dataclasses import replace
import hashlib
import json

import pytest

from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.piece_v1c import (
    PieceGenerationRequest, realize_piece_artifact,
)
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate
from piece_v2_contract import canonical_sha256_hex, validate_piece_text_binding
from piece_v2_visual import build_visual_recipe
from piece_v2_layout import TextMeasurement, build_measured_layout


CASES = (
    ('time', '私が大切にしたいのは、ひとりで静かに過ごす時間です。'
     'その時間を持てた日は、気持ちに余裕があった。',
     '私は、ひとりで静かに過ごす時間を大切にしたい。'
     'その時間を持てた日は、気持ちに余裕があった。'),
    ('action', '私が大切にしたいのは、自分で納得して選ぶことです。'
     'そのことを人に押しつけたいわけではない。',
     '私は、自分で納得して選ぶことを大切にしたい。'
     'そのことを人に押しつけたいわけではない。'),
    ('object', '私が大切にしているのは、自分の手で長く使ってきたものです。'
     'このものには、使いながら直した跡が残っている。',
     '私は、自分の手で長く使ってきたものを大切にしている。'
     'このものには、使いながら直した跡が残っている。'),
    ('condition', '私が望んでいるのは、家族と落ち着いて話す時間です。'
     'その時間が取れたら、私は近況を伝えたい。まだ、日程は決めていない。',
     '私は、家族と落ち着いて話す時間を望んでいる。'
     'その時間が取れたら、私は近況を伝えたい。まだ、日程は決めていない。'),
    ('role', '私が大切にしたいのは、友人の佐藤さんと落ち着いて話す時間です。'
     'その時間が持てなかった昨日は、少し寂しかった。まだ、いつ会うかは決めていない。',
     '私は、友人と落ち着いて話す時間を大切にしたい。'
     'その時間が持てなかった昨日は、少し寂しかった。まだ、いつ会うかは決めていない。'),
    ('chain', '私が大切にしたいのは、一人で考えを整理する時間です。'
     'その時間は、昨日は取れなかった。私はその時間を毎日少しでも持ちたい。',
     '私は、一人で考えを整理する時間を大切にしたい。'
     'その時間は、昨日は取れなかった。私は、その時間を毎日少しでも持ちたい。'),
    ('context', '今週は予定が重なっていた。私が大切にしたいのは、家で静かに過ごす時間です。'
     'この時間を確保できるかは、まだ分からない。',
     '今週は予定が重なっていた。\n\n私は、家で静かに過ごす時間を大切にしたい。'
     'この時間を確保できるかは、まだ分からない。'),
)


def run(text, *, tier='free', requested_format=None):
    request = PieceGenerationRequest('synthetic-reference',
        PieceSourceSnapshot('synthetic-owner', 'synthetic-input', 'v1', text),
        'synthetic-owner', 'synthetic-input', 'v1', tier=tier, requested_format=requested_format)
    return MeaningExperienceEngine().generate(request)


def generated(text):
    out = run(text)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    return out


@pytest.mark.parametrize('name,text,expected', CASES)
def test_actual_body_keeps_bound_antecedent_qualification_and_public_role(name, text, expected):
    out = generated(text)
    assert out.artifact.piece_text == expected
    assert out.artifact.eligible_formats == ('short_essay',)
    assert out.artifact.piece_text_hash == hashlib.sha256(expected.encode()).hexdigest()
    assert out.source_meaning.envelope.raw_utf8.decode() == text
    assert out.source_meaning.nominal_references
    ids = [n.node_id for n in out.source_meaning.graph.nodes]
    assert [i for group in out.artifact_plan.block_node_ids for i in group] == ids
    for ref in out.source_meaning.nominal_references:
        assert any(ref.antecedent_node_id in group and ref.reference_node_id in group
                   for group in out.artifact_plan.block_node_ids)
    direct = generate_piece_candidate(
        PieceSourceSnapshot('synthetic-owner', 'synthetic-input', 'v1', text),
        authenticated_owner_id='synthetic-owner')
    assert direct == out.artifact.as_candidate()
    assert direct['record_effect'] == direct['quota_effect'] == 0 and not direct['production_enabled']


@pytest.mark.parametrize('tail', [
    'その時間を人に強いたいわけではない。',
    'その時間が取れなければ、今週は予定を変えない。',
    'この時間は昨日だけで、毎日あるわけではない。',
    'その時間を持てるかどうか、今はまだ分からない。',
])
def test_reference_binding_does_not_infer_cause_remove_negation_or_promote_modality(tail):
    out = generated('私が大切にしたいのは、家で一人で過ごす時間です。' + tail)
    assert out.artifact.piece_text.endswith(tail)
    assert len(out.artifact.body_blocks) == 1


@pytest.mark.parametrize('text', [
    '朝は歩いた。私はその時間を大切にしたい。',
    '私が大切にしたいのは、一人で考える時間です。そのことはまだ難しい。',
    '私が大切にしたいのは、自分で選ぶことです。それはまだ難しい。',
    'その時間は昨日取れなかった。私が望んでいるのは、家で過ごす時間です。',
    '私が大切にしたいのは、家で過ごす時間です。私が望んでいるのは、友人と会う時間です。その時間が欲しい。',
    '私が大切にしたいのは、家で過ごす時間です。職場でも休む時間があった。その時間は短かった。',
    '私が大切にしたいのは、仕事の時間よりも、家で過ごす時間です。その時間が必要だ。',
    '私が大切にしたいのは、家で過ごす時間です。その時間帯は混雑する。',
    '私が大切にしたいのは、自分で選ぶことです。そのことわざが好きだ。',
    '私が大切にしたいのは、家で過ごす時間です。あの時間は取れなかった。',
    '私が大切にしたいのは、その時間を増やすことです。',
    '私が大切にしたいのは、家で過ごす時間です。その時間は好きだが、それはまだ難しい。',
    '私が大切にしたいのは、ひとりの機会より、家で過ごす時間です。その時間が必要だ。',
])
def test_unresolved_competing_or_non_nominal_reference_is_not_a_raw_fallback(text):
    out = run(text)
    assert out.status == EngineStatus.UNAVAILABLE and out.artifact is None
    assert not out.automatic_progression


def test_exact_scalar_and_utf8_spans_bind_each_reference_to_its_own_sentence():
    text = '  私が大切にしたいのは、🌱を眺めて静かに過ごす時間です。\r\nその時間を急いで終わらせたくはない。  '
    out = generated(text)
    meaning = out.source_meaning
    refs = meaning.nominal_references
    assert len(refs) == 1
    ref = refs[0]
    for scalar, utf8 in [(ref.antecedent_scalar_span, ref.antecedent_utf8_span),
                         (ref.reference_scalar_span, ref.reference_utf8_span)]:
        assert text[slice(*scalar)] == meaning.envelope.raw_utf8[slice(*utf8)].decode()
    assert text[slice(*ref.antecedent_scalar_span)] == '🌱を眺めて静かに過ごす時間'
    assert text[slice(*ref.reference_scalar_span)] == 'その時間'
    edge, = [e for e in meaning.graph.edges if e.relation == 'SOURCE_BOUND_NOMINAL_REFERENCE']
    assert edge.source_node_id == ref.reference_node_id
    assert edge.target_node_id == ref.antecedent_node_id
    assert set(edge.evidence_ids) == {meaning.evidence[0].evidence_id, meaning.evidence[1].evidence_id}


@pytest.mark.parametrize('mutation', ['omit', 'antecedent', 'span', 'utf8', 'head', 'edge'])
def test_reference_binding_is_consumed_not_just_attached_as_metadata(mutation):
    out = generated(CASES[0][1])
    m = out.source_meaning
    ref, = m.nominal_references
    if mutation == 'omit': m = replace(m, nominal_references=())
    if mutation == 'antecedent': m = replace(m, nominal_references=(replace(ref, antecedent_node_id=ref.reference_node_id),))
    if mutation == 'span': m = replace(m, nominal_references=(replace(ref, antecedent_scalar_span=(0, 1)),))
    if mutation == 'utf8': m = replace(m, nominal_references=(replace(ref, reference_utf8_span=(0, 1)),))
    if mutation == 'head': m = replace(m, nominal_references=(replace(ref, nominal_head='こと'),))
    if mutation == 'edge': m = replace(m, graph=replace(m.graph, edges=tuple(e for e in m.graph.edges if e.relation == 'SOURCE_ORDER')))
    with pytest.raises(ValueError):
        realize_piece_artifact(m, out.artifact_plan, tier='free', requested_format=None)


@pytest.mark.parametrize('mutation', ['split', 'reverse', 'cut_tail'])
def test_author_cannot_detach_antecedent_or_drop_qualification(mutation):
    out = generated(CASES[3][1])
    plan = out.artifact_plan
    ids = tuple(n.node_id for n in out.source_meaning.graph.nodes)
    groups = {'split': tuple((n,) for n in ids), 'reverse': (tuple(reversed(ids)),),
              'cut_tail': (ids[:-1],)}[mutation]
    with pytest.raises(ValueError):
        realize_piece_artifact(out.source_meaning, replace(plan, block_node_ids=groups),
                               tier='free', requested_format=None)


@pytest.mark.parametrize('format_type', ['quote', 'declaration'])
def test_contextual_reference_cannot_be_selected_as_a_standalone_quote_or_promise(format_type):
    out = run(CASES[3][1], tier='premium', requested_format=format_type)
    assert out.status == EngineStatus.UNAVAILABLE and out.artifact is None


@pytest.mark.parametrize('ratio', ['4:5', '9:16'])
def test_same_bound_body_reaches_visual_layout_without_reference_side_channel(ratio):
    class Metrics:
        profile_id = 'synthetic-not-device'
        def graphemes(self, text): return list(text)
        def measure(self, text, font_px):
            return TextMeasurement(len(text)*font_px, 0, -font_px*.8, len(text)*font_px, font_px*.2, True)
    out = generated(CASES[4][1])
    c = out.artifact.as_candidate()
    r = build_visual_recipe(c['format_type'], tier='premium', aspect_ratio=ratio)
    layout = build_measured_layout(c, r, canonical_sha256_hex(r), Metrics())
    assert validate_piece_text_binding(c['content_payload'], c['piece_text'], c['piece_text_hash']) == CASES[4][2]
    assert ''.join(x['text'] for x in layout['lines']) == CASES[4][2]
    body_free = json.dumps(out.as_body_free(), ensure_ascii=False) + repr(out.source_meaning.nominal_references)
    assert '佐藤' not in body_free and 'synthetic-input' not in body_free
