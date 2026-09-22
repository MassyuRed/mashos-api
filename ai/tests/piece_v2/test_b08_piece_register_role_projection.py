"""Original-source register parity in the disabled CMEE Piece consumer.

Synthetic inputs only. A register-neutral role hint must never replace the
original evidence, expand the author grammar, infer an owner or enable export.
"""
from dataclasses import asdict, replace
import hashlib

import pytest

from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.piece_v1c import (
    PieceGenerationRequest, compile_piece_artifact_plan, realize_piece_artifact,
)
import cocolon_meaning_experience_engine.piece_source as source_module
from emlis_ai_input_meaning_block_service import build_input_meaning_blocks
from emlis_ai_types import EvidenceRef
from piece_v2_contract import canonical_sha256_hex, validate_piece_text_binding
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate
from piece_v2_layout import TextMeasurement, build_measured_layout
from piece_v2_visual import build_visual_recipe

SPEAKERS = ('私', 'わたし', '僕', 'ぼく', '俺', 'おれ')
POSITIVE = '机の上の道具を並べ替えたい'
NEGATIVE = '机の上の道具を片づけたくない'
SECOND = '配置を紙に描いて比べたい'
LIMIT = 'まだ、作業を始める日は決めていない。'


def case_text(speaker='僕', register='です', negative=False):
    first = NEGATIVE if negative else POSITIVE
    return f'{speaker}は{first}{register}。{speaker}は{SECOND}{register}。{LIMIT}'


def expected_text(speaker='僕', register='です', negative=False):
    first = NEGATIVE if negative else POSITIVE
    return f'{speaker}は、{first}{register}。{SECOND}{register}。{LIMIT}'


def outcome(text, *, tier='free', requested=None, **source_changes):
    source = PieceSourceSnapshot('synthetic-owner', 'synthetic-register', '1', text)
    changed = replace(source, **source_changes) if source_changes else source
    request = PieceGenerationRequest(
        'synthetic-register', changed, source.owner_id, source.saved_input_id,
        source.source_version, tier, requested)
    return source, MeaningExperienceEngine().generate(request)


@pytest.mark.parametrize('speaker', SPEAKERS)
@pytest.mark.parametrize('register', ('', 'です'))
@pytest.mark.parametrize('negative', (False, True))
def test_politeness_keeps_every_original_proposition(speaker, register, negative):
    text = case_text(speaker, register, negative)
    source, out = outcome(text)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    meaning, plan, artifact = out.source_meaning, out.artifact_plan, out.artifact
    expected = expected_text(speaker, register, negative)
    assert artifact.piece_text == expected
    assert meaning.envelope.raw_utf8 == text.encode('utf-8')
    assert meaning.envelope.raw_sha256 == hashlib.sha256(text.encode('utf-8')).hexdigest()
    assert plan == compile_piece_artifact_plan(meaning)
    covered = [n for block in plan.block_node_ids for n in block]
    assert sorted(covered) == sorted(n.node_id for n in meaning.graph.nodes)
    assert len(covered) == len(meaning.graph.nodes) == 3
    for node, evidence in zip(meaning.graph.nodes, meaning.evidence, strict=True):
        assert text[evidence.scalar_start:evidence.scalar_end] == node.value
        assert text.encode('utf-8')[evidence.utf8_start:evidence.utf8_end] == node.value.encode('utf-8')
    before = asdict(meaning), asdict(plan)
    candidate = generate_piece_candidate(source, authenticated_owner_id=source.owner_id)
    assert candidate == artifact.as_candidate()
    assert (asdict(meaning), asdict(plan)) == before
    assert candidate['piece_text_hash'] == hashlib.sha256(expected.encode('utf-8')).hexdigest()
    assert validate_piece_text_binding(candidate['content_payload'], expected,
                                       candidate['piece_text_hash']) == expected
    assert candidate['eligible_formats'] == ['short_essay']
    assert not candidate['production_enabled']
    assert candidate['record_effect'] == candidate['quota_effect'] == 0


def test_compatibility_classifier_is_unchanged_and_hint_is_not_source(monkeypatch):
    text = case_text()
    evidence = EvidenceRef(kind='saved_input', ref_id='synthetic-register')
    before = build_input_meaning_blocks(current_input={'memo': text},
                                        shaped_user_phrases=(), evidence=evidence)
    assert before[0].role == 'current_expression'
    calls = []
    def observed(*, current_input, shaped_user_phrases, evidence):
        calls.append(current_input['memo'])
        return build_input_meaning_blocks(current_input=current_input,
            shaped_user_phrases=shaped_user_phrases, evidence=evidence)
    monkeypatch.setattr(source_module, 'build_input_meaning_blocks', observed)
    _, out = outcome(text)
    assert out.status == EngineStatus.GENERATED
    assert text in calls
    assert case_text(register='') in calls
    assert set(calls) == {text, case_text(register='')}
    assert out.source_meaning.envelope.raw_utf8 == text.encode('utf-8')
    assert out.artifact.piece_text == expected_text()
    after = build_input_meaning_blocks(current_input={'memo': text},
                                       shaped_user_phrases=(), evidence=evidence)
    assert before == after


def test_role_hint_still_requires_shared_role_admission(monkeypatch):
    text = case_text()
    original = build_input_meaning_blocks
    def deny_projection(*, current_input, shaped_user_phrases, evidence):
        # The untouched original remains available; only the temporary view
        # has no admitted role. An ending alone must not manufacture one.
        if current_input['memo'] != text:
            return ()
        return original(current_input=current_input,
                        shaped_user_phrases=shaped_user_phrases, evidence=evidence)
    monkeypatch.setattr(source_module, 'build_input_meaning_blocks', deny_projection)
    _, out = outcome(text)
    assert out.status == EngineStatus.UNAVAILABLE
    assert out.reason_codes == ('expression_meaning_not_admitted',)
    assert out.artifact is None


@pytest.mark.parametrize('text', (
    '友人は机の上の道具を並べ替えたいです。友人は配置を紙に描いて比べたいです。',
    '机の上の道具を並べ替えたいです。配置を紙に描いて比べたいです。',
    '僕は机の上の道具を並べ替えたかったです。まだ、作業を始める日は決めていない。',
    '僕は机の上の道具を並べ替えたいとは思いません。まだ、作業を始める日は決めていない。',
    '僕は机の上の道具を並べ替えたいかもしれません。まだ、作業を始める日は決めていない。',
    '僕は机の上の道具を並べ替えたいと話した。まだ、作業を始める日は決めていない。',
    '僕は遠くを飛ぶ鳥みたいです。まだ、作業を始める日は決めていない。',
    '僕は「道具を並べ替えたいです」と聞いた。まだ、作業を始める日は決めていない。',
))
def test_projection_does_not_expand_the_existing_complete_wish_grammar(text):
    _, out = outcome(text)
    assert out.status == EngineStatus.UNAVAILABLE, out.as_body_free()
    assert out.artifact is None


@pytest.mark.parametrize('changes,reason', (
    ({'owner_id': 'another-owner'}, 'source_owner_mismatch'),
    ({'saved_input_id': 'another-source'}, 'saved_input_binding_mismatch'),
    ({'source_version': '2'}, 'source_version_binding_mismatch'),
    ({'source_role': 'supplemental'}, 'source_role_or_stage_not_yet_supported'),
    ({'source_stage': 'refined'}, 'source_role_or_stage_not_yet_supported'),
))
def test_source_identity_and_stage_boundaries(changes, reason):
    _, out = outcome(case_text(), **changes)
    assert out.status == EngineStatus.UNAVAILABLE
    assert out.reason_codes == (reason,)
    assert out.artifact is None


@pytest.mark.parametrize('tier,requested', (
    ('free', None), ('plus', None), ('premium', None), ('premium', 'short_essay'),
))
def test_existing_tiers_receive_the_same_body(tier, requested):
    _, out = outcome(case_text(), tier=tier, requested=requested)
    assert out.status == EngineStatus.GENERATED
    assert out.artifact.piece_text == expected_text()


@pytest.mark.parametrize('tier,requested', (
    ('free', 'short_essay'), ('plus', 'short_essay'),
    ('premium', 'quote'), ('premium', 'declaration'),
))
def test_register_projection_cannot_grant_format_choice(tier, requested):
    _, out = outcome(case_text(), tier=tier, requested=requested)
    assert out.status == EngineStatus.UNAVAILABLE
    assert out.reason_codes == ('format_choice_not_admitted',)
    assert out.artifact is None


def test_short_source_is_not_padded():
    _, out = outcome('僕は選びたいです。')
    assert out.status == EngineStatus.UNAVAILABLE
    assert out.reason_codes == ('format_not_eligible',)
    assert out.artifact is None


@pytest.mark.parametrize('damage', ('drop_duty', 'reorder', 'change_source'))
def test_role_projection_cannot_license_damaged_source_or_plan(damage):
    _, out = outcome(case_text())
    assert out.status == EngineStatus.GENERATED
    meaning, plan = out.source_meaning, out.artifact_plan
    if damage == 'drop_duty':
        plan = replace(plan, duties=plan.duties[:-1])
    elif damage == 'reorder':
        plan = replace(plan, block_node_ids=(tuple(reversed(plan.block_node_ids[0])),))
    else:
        node = replace(meaning.graph.nodes[0], value=meaning.graph.nodes[0].value.replace('です', ''))
        meaning = replace(meaning, graph=replace(meaning.graph,
                          nodes=(node, *meaning.graph.nodes[1:])))
    with pytest.raises(ValueError):
        realize_piece_artifact(meaning, plan, tier='free', requested_format=None)


@pytest.mark.parametrize('ratio', ('4:5', '9:16'))
def test_b9_gets_the_complete_original_register(ratio):
    class Metrics:
        profile_id = 'synthetic-register-not-device'
        def graphemes(self, text): return list(text)
        def measure(self, text, font_px):
            width = len(text) * font_px
            return TextMeasurement(width, 0, -font_px * .8, width, font_px * .2, True)
    _, out = outcome(case_text())
    assert out.status == EngineStatus.GENERATED
    candidate = out.artifact.as_candidate()
    recipe = build_visual_recipe(candidate['format_type'], tier='premium', aspect_ratio=ratio)
    layout = build_measured_layout(candidate, recipe, canonical_sha256_hex(recipe), Metrics())
    blocks = candidate['content_payload']['body_blocks']
    rebuilt = [''.join(line['text'] for line in layout['lines'] if line['block_index'] == i)
               for i in range(len(blocks))]
    assert rebuilt == blocks
    assert '\n\n'.join(rebuilt) == expected_text()
    assert layout['piece_text_hash'] == candidate['piece_text_hash']
    assert not layout['clipped'] and not layout['native_device_verified']
    assert layout['record_effect'] == layout['quota_effect'] == 0


@pytest.mark.parametrize('scope', ('時間が取れるなら、', '並べ方が気になるので、', '時間が足りなくても、'))
def test_written_scope_is_preserved_in_the_original_register(scope):
    text = f'僕は{scope}{SECOND}です。{LIMIT}'
    _, out = outcome(text)
    assert out.status == EngineStatus.GENERATED
    assert out.artifact.piece_text == f'僕は、{scope}{SECOND}です。{LIMIT}'
    assert out.source_meaning.graph.nodes[0].value == text[:-len(LIMIT)]
    assert out.artifact.eligible_formats == ('short_essay',)


@pytest.mark.parametrize('gap', ('\n', '\n\n', '友人は席を外していた。'))
def test_register_projection_does_not_merge_across_written_boundaries(gap):
    text = f'僕は{POSITIVE}です。{gap}僕は{SECOND}です。{LIMIT}'
    _, out = outcome(text)
    assert out.status == EngineStatus.GENERATED
    expected_gap = gap if '友人' in gap else ''
    assert out.artifact.piece_text == f'僕は、{POSITIVE}です。{expected_gap}僕は、{SECOND}です。{LIMIT}'
    assert out.source_meaning.envelope.raw_utf8 == text.encode('utf-8')


@pytest.mark.parametrize('first_register,second_register', (('', 'です'), ('です', '')))
def test_mixed_register_keeps_both_predicate_forms(first_register, second_register):
    text = f'僕は{POSITIVE}{first_register}。僕は{SECOND}{second_register}。{LIMIT}'
    _, out = outcome(text)
    assert out.status == EngineStatus.GENERATED
    assert out.artifact.piece_text == f'僕は、{POSITIVE}{first_register}。{SECOND}{second_register}。{LIMIT}'


def test_original_duplicate_propositions_are_not_removed():
    text = f'僕は{POSITIVE}です。僕は{POSITIVE}です。{LIMIT}'
    _, out = outcome(text)
    assert out.status == EngineStatus.GENERATED
    assert out.artifact.piece_text == f'僕は、{POSITIVE}です。僕は{POSITIVE}です。{LIMIT}'
    assert len(out.source_meaning.graph.nodes) == 3
    assert out.source_meaning.graph.nodes[0].value == out.source_meaning.graph.nodes[1].value
    assert out.source_meaning.sentences[1].role == 'source_context'


def test_different_written_speakers_are_not_unified():
    text = f'僕は{POSITIVE}です。わたしは{SECOND}です。{LIMIT}'
    _, out = outcome(text)
    assert out.status == EngineStatus.GENERATED
    assert out.artifact.piece_text == f'僕は、{POSITIVE}です。わたしは、{SECOND}です。{LIMIT}'


def test_existing_named_owner_publicization_and_reservation_survive():
    text = ('僕は友人の森さんの同僚の青木さんと話したいです。'
            '僕は青木さんの考えを聞きたいです。まだ、会う日は決めていない。')
    _, out = outcome(text)
    assert out.status == EngineStatus.GENERATED
    assert out.artifact.piece_text == ('僕は、友人の同僚と話したいです。'
                                      '友人の同僚の考えを聞きたいです。まだ、会う日は決めていない。')
    assert out.source_meaning.envelope.raw_utf8 == text.encode('utf-8')
