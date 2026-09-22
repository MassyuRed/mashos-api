"""Source-bound named possessors in the existing disabled CMEE Piece path.

The names and inputs are synthetic. These checks do not admit authentication,
public activation, general coreference or a native renderer.
"""
from dataclasses import asdict, replace
import hashlib

import pytest

from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.piece_source import piece_public_role_aliases
from cocolon_meaning_experience_engine.piece_v1c import (
    PieceGenerationRequest, _publicize_source_sentence,
)
from piece_v2_contract import canonical_sha256_hex, validate_piece_text_binding
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate
from piece_v2_layout import TextMeasurement, build_measured_layout
from piece_v2_visual import build_visual_recipe


CASES = (
    ('inline_named_owner',
     '私は友人の佐藤さんの上司の田中さんと話したい。田中さんとはまだ会っていない。',
     '私は、友人の上司と話したい。友人の上司とはまだ会っていない。',
     {'佐藤さん': '友人', '田中さん': '友人の上司'}),
    ('written_speaker_and_two_mentions',
     '私は私の友人の佐藤さんの上司の田中さんと話したい。佐藤さんと田中さんの都合はまだ分からない。',
     '私は、私の友人の上司と話したい。私の友人と私の友人の上司の都合はまだ分からない。',
     {'佐藤さん': '私の友人', '田中さん': '私の友人の上司'}),
    ('three_named_links',
     '私は友人の佐藤さんの上司の田中さんの同僚の鈴木さんと話したい。鈴木さんとはまだ会っていない。',
     '私は、友人の上司の同僚と話したい。友人の上司の同僚とはまだ会っていない。',
     {'佐藤さん': '友人', '田中さん': '友人の上司', '鈴木さん': '友人の上司の同僚'}),
    ('owner_bound_in_another_sentence',
     '私は田中さんと話したい。友人の佐藤さんは忙しかった。佐藤さんの上司の田中さんとはまだ会っていない。',
     '私は、友人の上司と話したい。友人は忙しかった。友人の上司とはまだ会っていない。',
     {'佐藤さん': '友人', '田中さん': '友人の上司'}),
    ('owner_binding_after_reference',
     '私は佐藤さんの上司の田中さんと話したい。友人の佐藤さんとはまだ会っていない。田中さんの都合はまだ分からない。',
     '私は、友人の上司と話したい。友人とはまだ会っていない。友人の上司の都合はまだ分からない。',
     {'佐藤さん': '友人', '田中さん': '友人の上司'}),
    ('later_written_qualification_propagates',
     '私は友人の佐藤さんの上司の田中さんと話したい。私の友人の佐藤さんは今日は休みだった。田中さんとはまだ会っていない。',
     '私は、私の友人の上司と話したい。私の友人は今日は休みだった。私の友人の上司とはまだ会っていない。',
     {'佐藤さん': '私の友人', '田中さん': '私の友人の上司'}),
    ('same_terminal_role_different_owners',
     '私は友人の佐藤さんの上司の田中さんと同僚の鈴木さんの上司の山田さんに話を聞きたい。田中さんと山田さんは別々の部署で働いている。',
     '私は、友人の上司と同僚の上司に話を聞きたい。友人の上司と同僚の上司は別々の部署で働いている。',
     {'佐藤さん': '友人', '田中さん': '友人の上司', '鈴木さん': '同僚', '山田さん': '同僚の上司'}),
    ('repeated_role_is_not_collapsed',
     '私は友人の佐藤さんの友人の田中さんと話したい。田中さんとはまだ会っていない。',
     '私は、友人の友人と話したい。友人の友人とはまだ会っていない。',
     {'佐藤さん': '友人', '田中さん': '友人の友人'}),
    ('concession_and_negative_intention',
     '友人の佐藤さんの上司の田中さんは忙しいけれど、私は田中さんと急いで話したくない。まだ、会う日は決めていない。',
     '友人の上司は忙しいけれど、私は、友人の上司と急いで話したくない。まだ、会う日は決めていない。',
     {'佐藤さん': '友人', '田中さん': '友人の上司'}),
    ('condition_and_reservation',
     '私は友人の佐藤さんの上司の田中さんが来られるなら、田中さんと話したい。まだ、会う日は決めていない。',
     '私は、友人の上司が来られるなら、友人の上司と話したい。まだ、会う日は決めていない。',
     {'佐藤さん': '友人', '田中さん': '友人の上司'}),
    ('evaluation_and_uncertainty',
     '私にとって友人の佐藤さんの上司の田中さんと話す時間が大切です。田中さんと毎日会えるとは限らない。',
     '私にとって、友人の上司と話す時間が大切です。友人の上司と毎日会えるとは限らない。',
     {'佐藤さん': '友人', '田中さん': '友人の上司'}),
    ('compatible_short_terminal_binding',
     '私は友人の佐藤さんの上司の田中さんと話したい。上司の田中さんは今日は休みだった。田中さんとはまだ会っていない。',
     '私は、友人の上司と話したい。友人の上司は今日は休みだった。友人の上司とはまだ会っていない。',
     {'佐藤さん': '友人', '田中さん': '友人の上司'}),
    ('two_unlabelled_links_between_names',
     '私は私の友人の佐藤さんの同僚の上司の田中さんと話したい。田中さんとはまだ会っていない。',
     '私は、私の友人の同僚の上司と話したい。私の友人の同僚の上司とはまだ会っていない。',
     {'佐藤さん': '私の友人', '田中さん': '私の友人の同僚の上司'}),
) + tuple(
    (f'existing_role_{i}',
     f'私は友人の佐藤さんの{role}の田中さんと話したい。田中さんの都合はまだ分からない。',
     f'私は、友人の{role}と話したい。友人の{role}の都合はまだ分からない。',
     {'佐藤さん': '友人', '田中さん': '友人の' + role})
    for i, role in enumerate(('友人', '同僚', '上司', '部下', '先輩', '後輩', '先生'))
) + tuple(
    (f'existing_speaker_{i}',
     f'{speaker}は{speaker}の友人の佐藤さんの上司の田中さんと話したい。田中さんとはまだ会っていない。',
     f'{speaker}は、{speaker}の友人の上司と話したい。{speaker}の友人の上司とはまだ会っていない。',
     {'佐藤さん': speaker + 'の友人', '田中さん': speaker + 'の友人の上司'})
    for i, speaker in enumerate(('私', 'わたし', '僕', 'ぼく', '俺', 'おれ'))
)


def outcome(text):
    source = PieceSourceSnapshot('synthetic-owner', 'synthetic-named-owner', 'v1', text)
    out = MeaningExperienceEngine().generate(PieceGenerationRequest(
        'synthetic-named-owner', source, source.owner_id,
        source.saved_input_id, source.source_version))
    return source, out


@pytest.mark.parametrize('case,text,expected,aliases', CASES, ids=[c[0] for c in CASES])
def test_named_owner_cmee_b8_source_and_canonical_body(case, text, expected, aliases):
    source, out = outcome(text)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    meaning, plan = out.source_meaning, out.artifact_plan
    assert out.artifact.piece_text == expected
    assert out.artifact.piece_text_hash == hashlib.sha256(expected.encode('utf-8')).hexdigest()
    assert meaning.envelope.raw_utf8 == text.encode('utf-8')
    assert piece_public_role_aliases(meaning.role_bindings) == aliases
    for binding in meaning.role_bindings:
        assert text[binding.source_start:binding.source_end] == binding.role + 'の' + binding.name
        assert binding.name not in expected
    for node, evidence in zip(meaning.graph.nodes, meaning.evidence, strict=True):
        assert text[evidence.scalar_start:evidence.scalar_end] == node.value
        assert text.encode('utf-8')[evidence.utf8_start:evidence.utf8_end].decode('utf-8') == node.value
    covered = [node for block in plan.block_node_ids for node in block]
    assert sorted(covered) == sorted(node.node_id for node in meaning.graph.nodes)
    assert len(covered) == len(meaning.graph.nodes)
    before = asdict(meaning), asdict(plan)
    candidate = generate_piece_candidate(source, authenticated_owner_id=source.owner_id)
    assert candidate == out.artifact.as_candidate()
    assert (asdict(meaning), asdict(plan)) == before
    assert validate_piece_text_binding(candidate['content_payload'], expected,
                                       candidate['piece_text_hash']) == expected
    assert not candidate['production_enabled']
    assert candidate['record_effect'] == candidate['quota_effect'] == 0


REJECTED = (
    ('unbound_named_owner',
     '私は佐藤さんの上司の田中さんと話したい。田中さんとはまだ会っていない。',
     'public_role_owner_not_bound'),
    ('conflicting_owner_roles',
     '私は友人の佐藤さんの上司の田中さんと話したい。同僚の佐藤さんは忙しかった。',
     'public_role_binding_ambiguous'),
    ('different_named_owners_are_not_suffix_unified',
     '私は友人の佐藤さんの上司の田中さんと話したい。私の友人の鈴木さんの上司の田中さんは忙しかった。',
     'public_role_binding_ambiguous'),
    ('self_dependency_even_with_anchor',
     '私は友人の佐藤さんと話したい。佐藤さんの上司の佐藤さんは忙しかった。',
     'public_role_binding_ambiguous'),
    ('cycle_even_with_anchor',
     '私は友人の佐藤さんの上司の田中さんと話したい。田中さんの同僚の佐藤さんは忙しかった。',
     'public_role_binding_ambiguous'),
    ('aliases_collide_after_owner_resolution',
     '私は友人の佐藤さんの上司の田中さんと友人の上司の鈴木さんに話を聞きたい。',
     'public_role_binding_ambiguous'),
    ('unknown_owner_at_root',
     '私は父の友人の佐藤さんの上司の田中さんと話したい。田中さんとはまだ会っていない。',
     'public_role_owner_not_bound'),
    ('unknown_relationship_in_middle',
     '私は友人の佐藤さんの恩師の田中さんと話したい。田中さんとはまだ会っていない。',
     'public_role_binding_missing'),
    ('unknown_relationship_despite_existing_alias',
     '私は友人の佐藤さんの上司の田中さんと話したい。恩師の佐藤さんは忙しかった。',
     'public_role_binding_missing'),
    ('name_is_material_in_nested_role',
     '私は友人の佐藤さんの上司の田中さんという名前を書きたい。',
     'public_identity_is_material'),
    ('unknown_prefix_before_named_owner',
     '私は父の佐藤さんの上司の田中さんと話したい。友人の佐藤さんは忙しかった。',
     'public_role_owner_not_bound'),
)


@pytest.mark.parametrize('case,text,reason', REJECTED, ids=[c[0] for c in REJECTED])
def test_unresolved_named_owners_are_not_invented(case, text, reason):
    _, out = outcome(text)
    assert out.status == EngineStatus.UNAVAILABLE
    assert out.artifact is None
    assert out.reason_codes == (reason,)


@pytest.mark.parametrize('case_index', [0, 1, 2, 6, 8, 10])
@pytest.mark.parametrize('ratio', ['4:5', '9:16'])
def test_named_chain_b9_uses_the_same_complete_body(case_index, ratio):
    class Metrics:
        profile_id = 'synthetic-named-owner-not-device'
        def graphemes(self, text): return list(text)
        def measure(self, text, font_px):
            width = len(text) * font_px
            return TextMeasurement(width, 0, -font_px * .8, width, font_px * .2, True)
    _, out = outcome(CASES[case_index][1])
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    candidate = out.artifact.as_candidate()
    recipe = build_visual_recipe(candidate['format_type'], tier='premium', aspect_ratio=ratio)
    layout = build_measured_layout(candidate, recipe, canonical_sha256_hex(recipe), Metrics())
    blocks = candidate['content_payload']['body_blocks']
    rebuilt = [''.join(line['text'] for line in layout['lines'] if line['block_index'] == i)
               for i in range(len(blocks))]
    assert rebuilt == blocks
    assert '\n\n'.join(rebuilt) == CASES[case_index][2]
    assert layout['piece_text_hash'] == candidate['piece_text_hash']
    assert not layout['clipped'] and not layout['native_device_verified']
    assert layout['record_effect'] == layout['quota_effect'] == 0


def test_nested_binding_keeps_original_span_and_rejects_tampering():
    text = CASES[2][1]
    _, out = outcome(text)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    meaning = out.source_meaning
    bindings = meaning.role_bindings
    assert [b.role for b in bindings] == [
        '友人', '友人の佐藤さんの上司', '友人の佐藤さんの上司の田中さんの同僚']
    damaged = replace(meaning, role_bindings=bindings[:-1] + (
        replace(bindings[-1], source_start=bindings[-1].source_start + 1),))
    with pytest.raises(ValueError, match='public_role_source_binding'):
        _publicize_source_sentence(text, damaged)
