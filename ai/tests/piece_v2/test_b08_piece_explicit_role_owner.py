"""Keep source-written first-person possessors in disabled Piece publicization.

Synthetic regressions for the existing CMEE/B8/B9 path, not a general identity,
modifier, authentication or native-rendering acceptance suite.
"""
from dataclasses import asdict
import hashlib

import pytest

from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.piece_source import piece_public_role_aliases
from cocolon_meaning_experience_engine.piece_v1c import PieceGenerationRequest
from piece_v2_contract import canonical_sha256_hex, validate_piece_text_binding
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate
from piece_v2_layout import TextMeasurement, build_measured_layout
from piece_v2_visual import build_visual_recipe


SPEAKERS = ('私', 'わたし', '僕', 'ぼく', '俺', 'おれ')
CASES = tuple(
    (f'speaker_{i}',
     f'{speaker}は{speaker}の友人の佐藤さんと話したい。佐藤さんの都合はまだ分からない。',
     f'{speaker}は、{speaker}の友人と話したい。{speaker}の友人の都合はまだ分からない。',
     (speaker + 'の友人',))
    for i, speaker in enumerate(SPEAKERS)
) + (
    ('owner_chain_context_first',
     '私の友人の上司の佐藤さんは忙しかった。私は佐藤さんと落ち着いて話したい。',
     '私は、私の友人の上司と落ち着いて話したい。\n\n私の友人の上司は忙しかった。',
     ('私の友人の上司',)),
    ('short_then_owned_role',
     '私は上司の佐藤さんと話したい。私の上司の佐藤さんは今日は休みだった。佐藤さんとはまだ会っていない。',
     '私は、私の上司と話したい。私の上司は今日は休みだった。私の上司とはまだ会っていない。',
     ('上司', '私の上司')),
    ('owned_then_short_role',
     '私は私の上司の佐藤さんと話したい。上司の佐藤さんは今日は休みだった。佐藤さんとはまだ会っていない。',
     '私は、私の上司と話したい。私の上司は今日は休みだった。私の上司とはまだ会っていない。',
     ('私の上司', '上司')),
    ('name_before_owner_binding',
     '私は佐藤さんと話したい。私の友人の佐藤さんは忙しかった。',
     '私は、私の友人と話したい。私の友人は忙しかった。',
     ('私の友人',)),
    ('repeated_relationship',
     '私は私の友人の友人の佐藤さんと話したい。佐藤さんとはまだ会っていない。',
     '私は、私の友人の友人と話したい。私の友人の友人とはまだ会っていない。',
     ('私の友人の友人',)),
    ('same_final_role_distinct_full_owners',
     '私は私の上司の佐藤さんと友人の上司の田中さんに話を聞きたい。佐藤さんと田中さんは別々の部署で働いている。',
     '私は、私の上司と友人の上司に話を聞きたい。私の上司と友人の上司は別々の部署で働いている。',
     ('私の上司', '友人の上司')),
    ('concession_negative',
     '私の友人の上司の佐藤さんは忙しいけれど、私は佐藤さんと急いで話したくない。まだ、会う日は決めていない。',
     '私の友人の上司は忙しいけれど、私は、私の友人の上司と急いで話したくない。まだ、会う日は決めていない。',
     ('私の友人の上司',)),
    ('condition_and_reservation',
     '私の友人の佐藤さんが来られるなら、私は佐藤さんと話したい。まだ、会う日は決めていない。',
     '私は、私の友人が来られるなら、私の友人と話したい。まだ、会う日は決めていない。',
     ('私の友人',)),
    ('evaluation_with_uncertainty',
     '私にとって私の友人の佐藤さんと話す時間が大切です。佐藤さんと毎日会えるとは限らない。',
     '私にとって、私の友人と話す時間が大切です。私の友人と毎日会えるとは限らない。',
     ('私の友人',)),
    ('compatible_owned_chain_suffixes',
     '私は私の友人の上司の佐藤さんと話したい。友人の上司の佐藤さんは今日は休みだった。上司の佐藤さんとはまだ会っていない。',
     '私は、私の友人の上司と話したい。私の友人の上司は今日は休みだった。私の友人の上司とはまだ会っていない。',
     ('私の友人の上司', '友人の上司', '上司')),
    ('unqualified_role_unchanged',
     '私は友人の佐藤さんと話したい。佐藤さんの都合はまだ分からない。',
     '私は、友人と話したい。友人の都合はまだ分からない。',
     ('友人',)),
)


def outcome(text):
    source = PieceSourceSnapshot('synthetic-owner', 'synthetic-explicit-role-owner', 'v1', text)
    out = MeaningExperienceEngine().generate(PieceGenerationRequest(
        'synthetic-explicit-role-owner', source, source.owner_id,
        source.saved_input_id, source.source_version))
    return source, out


@pytest.mark.parametrize('case,text,expected,roles', CASES, ids=[c[0] for c in CASES])
def test_written_owner_survives_full_cmee_and_b8(case, text, expected, roles):
    source, out = outcome(text)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    meaning, plan = out.source_meaning, out.artifact_plan
    assert out.artifact.piece_text == expected
    assert out.artifact.piece_text_hash == hashlib.sha256(expected.encode('utf-8')).hexdigest()
    assert meaning.envelope.raw_utf8 == text.encode('utf-8')
    assert tuple(b.role for b in meaning.role_bindings) == roles
    for binding in meaning.role_bindings:
        assert text[binding.source_start:binding.source_end] == binding.role + 'の' + binding.name
        assert binding.name not in expected
    # The selected alias is one complete source-written role, not a synthesis.
    for name, alias in piece_public_role_aliases(meaning.role_bindings).items():
        assert any(b.name == name and b.role == alias for b in meaning.role_bindings)
    nodes = {node.node_id: node for node in meaning.graph.nodes}
    for sentence in meaning.sentences:
        assert text[sentence.source_start:sentence.source_end] == nodes[sentence.node_id].value
    for node, evidence in zip(meaning.graph.nodes, meaning.evidence, strict=True):
        assert meaning.envelope.raw_utf8[evidence.utf8_start:evidence.utf8_end].decode('utf-8') == node.value
    covered = [node for block in plan.block_node_ids for node in block]
    assert sorted(covered) == sorted(nodes) and len(covered) == len(nodes)
    before = asdict(meaning), asdict(plan)
    candidate = generate_piece_candidate(source, authenticated_owner_id=source.owner_id)
    assert candidate == out.artifact.as_candidate()
    assert before == (asdict(meaning), asdict(plan))
    assert validate_piece_text_binding(candidate['content_payload'], expected,
                                       candidate['piece_text_hash']) == expected
    assert not candidate['production_enabled']
    assert candidate['record_effect'] == candidate['quota_effect'] == 0


REJECTED = (
    ('unresolved_parent_owner',
     '私は父の友人の佐藤さんと話したい。佐藤さんとはまだ会っていない。',
     'public_role_owner_not_bound'),
    ('unresolved_other_person',
     '私はあなたの友人の佐藤さんと話したい。佐藤さんとはまだ会っていない。',
     'public_role_owner_not_bound'),
    ('unresolved_named_owner',
     '私は友人の佐藤さんの上司の田中さんと話したい。田中さんとはまだ会っていない。',
     'public_role_owner_not_bound'),
    ('unresolved_owner_before_self',
     '私は父の私の友人の佐藤さんと話したい。佐藤さんとはまだ会っていない。',
     'public_role_owner_not_bound'),
    ('unresolved_owner_despite_prior_alias',
     '私は私の友人の佐藤さんと話したい。あなたの友人の佐藤さんは今日は休みだった。',
     'public_role_owner_not_bound'),
    ('unresolved_owner_with_space',
     '私は父の 友人の佐藤さんと話したい。佐藤さんとはまだ会っていない。',
     'public_role_owner_not_bound'),
    ('role_suffix_inside_noun',
     '私は大先生の佐藤さんと話したい。佐藤さんとはまだ会っていない。',
     'public_role_binding_missing'),
    ('role_suffix_despite_prior_alias',
     '私は友人の佐藤さんと話したい。大先生の佐藤さんは今日は休みだった。',
     'public_role_binding_missing'),
    ('unknown_role_despite_prior_alias',
     '私は友人の佐藤さんと話したい。恩師の佐藤さんは今日は休みだった。',
     'public_role_binding_missing'),
    ('conflicting_owned_relationship',
     '私は私の友人の佐藤さんと話したい。私の上司の佐藤さんは今日は休みだった。',
     'public_role_binding_ambiguous'),
    ('no_unstated_speaker_unification',
     '私は私の友人の佐藤さんと話したい。僕の友人の佐藤さんは今日は休みだった。',
     'public_role_binding_ambiguous'),
    ('indistinguishable_names',
     '私は私の友人の佐藤さんと私の友人の田中さんに話を聞きたい。',
     'public_role_binding_ambiguous'),
    ('identity_itself_is_material',
     '私は私の友人の佐藤さんという名前を書きたい。',
     'public_identity_is_material'),
)


@pytest.mark.parametrize('case,text,reason', REJECTED, ids=[c[0] for c in REJECTED])
def test_unresolved_owner_and_ambiguous_identity_are_not_shortened(case, text, reason):
    _, out = outcome(text)
    assert out.status == EngineStatus.UNAVAILABLE
    assert out.reason_codes == (reason,)
    assert out.artifact is None


@pytest.mark.parametrize('case_index', [0, 6, 11, 12, 13, 14])
@pytest.mark.parametrize('ratio', ['4:5', '9:16'])
def test_b9_keeps_identical_owned_body_and_reservations(case_index, ratio):
    class Metrics:
        profile_id = 'synthetic-explicit-role-owner-not-device'
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
