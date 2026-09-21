"""Preserve source-written relational qualifications in disabled Piece sharing.

Synthetic source/CMEE/B8/B9 regressions, not general person resolution or
public-safety/native acceptance. Existing name and role grammar stays bounded.
"""
from dataclasses import asdict
import hashlib

import pytest

from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.piece_v1c import PieceGenerationRequest
from piece_v2_contract import canonical_sha256_hex, validate_piece_text_binding
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate
from piece_v2_layout import TextMeasurement, build_measured_layout
from piece_v2_visual import build_visual_recipe


CASES = (
    ('qualified_following_name',
     '私は友人の上司の佐藤さんと話したい。佐藤さんの都合はまだ分からない。',
     '私は、友人の上司と話したい。友人の上司の都合はまだ分からない。'),
    ('intent_after_context',
     '友人の上司の佐藤さんは忙しかった。私は佐藤さんと落ち着いて話したい。',
     '私は、友人の上司と落ち着いて話したい。\n\n友人の上司は忙しかった。'),
    ('three_roles',
     '私は同僚の友人の先生の佐藤さんに話を聞きたい。佐藤さんは今日は休みだった。',
     '私は、同僚の友人の先生に話を聞きたい。同僚の友人の先生は今日は休みだった。'),
    ('repeated_role_is_not_deduplicated',
     '私は友人の友人の佐藤さんと話したい。佐藤さんとはまだ会っていない。',
     '私は、友人の友人と話したい。友人の友人とはまだ会っていない。'),
    ('name_before_explicit_binding',
     '私は佐藤さんと話したい。友人の上司の佐藤さんは忙しかった。',
     '私は、友人の上司と話したい。友人の上司は忙しかった。'),
    ('distinct_qualified_people',
     '私は友人の上司の佐藤さんと同僚の上司の田中さんに話を聞きたい。佐藤さんと田中さんは別々の部署で働いている。',
     '私は、友人の上司と同僚の上司に話を聞きたい。友人の上司と同僚の上司は別々の部署で働いている。'),
    ('qualified_then_shorter_binding',
     '私は友人の上司の佐藤さんと話したい。上司の佐藤さんは今日は休みだった。佐藤さんの都合はまだ分からない。',
     '私は、友人の上司と話したい。友人の上司は今日は休みだった。友人の上司の都合はまだ分からない。'),
    ('shorter_then_qualified_binding',
     '私は上司の佐藤さんと話したい。友人の上司の佐藤さんは今日は休みだった。佐藤さんの都合はまだ分からない。',
     '私は、友人の上司と話したい。友人の上司は今日は休みだった。友人の上司の都合はまだ分からない。'),
    ('concession_and_negative_intent',
     '友人の上司の佐藤さんは忙しいけれど、私は佐藤さんと急いで話したくない。まだ、会う日は決めていない。',
     '友人の上司は忙しいけれど、私は、友人の上司と急いで話したくない。まだ、会う日は決めていない。'),
    ('condition_is_not_an_event',
     '友人の上司の佐藤さんが来られるなら、私は佐藤さんと話したい。まだ、会う日は決めていない。',
     '私は、友人の上司が来られるなら、友人の上司と話したい。まだ、会う日は決めていない。'),
    ('evaluation_target_and_reservation',
     '私にとって友人の上司の佐藤さんと話す時間が大切です。佐藤さんと毎日会えるとは限らない。',
     '私にとって、友人の上司と話す時間が大切です。友人の上司と毎日会えるとは限らない。'),
    ('simple_role_unchanged',
     '私は友人の佐藤さんと話したい。佐藤さんの都合はまだ分からない。',
     '私は、友人と話したい。友人の都合はまだ分からない。'),
    ('full_and_terminal_role_are_distinguishable',
     '私は友人の上司の佐藤さんと上司の田中さんに話を聞きたい。佐藤さんと田中さんは別々の部署で働いている。',
     '私は、友人の上司と上司に話を聞きたい。友人の上司と上司は別々の部署で働いている。'),
    ('three_role_compatible_suffixes',
     '私は先生の後輩の先輩の佐藤さんに話を聞きたい。後輩の先輩の佐藤さんは今日は休みだった。先輩の佐藤さんとはまだ会っていない。',
     '私は、先生の後輩の先輩に話を聞きたい。先生の後輩の先輩は今日は休みだった。先生の後輩の先輩とはまだ会っていない。'),
)


def generated(text):
    source = PieceSourceSnapshot('synthetic-owner', 'synthetic-role-chain', 'v1', text)
    out = MeaningExperienceEngine().generate(PieceGenerationRequest(
        'synthetic-role-chain', source, source.owner_id, source.saved_input_id, source.source_version))
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    return source, out


@pytest.mark.parametrize('name,text,expected', CASES, ids=[c[0] for c in CASES])
def test_whole_relation_survives_source_to_share_text(name, text, expected):
    source, out = generated(text)
    meaning, plan = out.source_meaning, out.artifact_plan
    assert meaning.envelope.raw_utf8 == text.encode('utf-8')
    assert out.artifact.piece_text == expected
    assert out.artifact.piece_text_hash == hashlib.sha256(expected.encode('utf-8')).hexdigest()
    for binding in meaning.role_bindings:
        assert text[binding.source_start:binding.source_end] == binding.role + 'の' + binding.name
        assert binding.name not in expected
    nodes = {n.node_id: n for n in meaning.graph.nodes}
    for sentence in meaning.sentences:
        assert text[sentence.source_start:sentence.source_end] == nodes[sentence.node_id].value
    for node, evidence in zip(meaning.graph.nodes, meaning.evidence, strict=True):
        assert meaning.envelope.raw_utf8[evidence.utf8_start:evidence.utf8_end].decode('utf-8') == node.value
    ordered = [node_id for block in plan.block_node_ids for node_id in block]
    assert sorted(ordered) == sorted(nodes) and len(ordered) == len(nodes)
    before = asdict(meaning), asdict(plan)
    candidate = generate_piece_candidate(source, authenticated_owner_id=source.owner_id)
    assert candidate == out.artifact.as_candidate()
    assert before == (asdict(meaning), asdict(plan))
    assert validate_piece_text_binding(candidate['content_payload'], expected, candidate['piece_text_hash']) == expected
    assert not candidate['production_enabled']
    assert candidate['record_effect'] == candidate['quota_effect'] == 0


@pytest.mark.parametrize('text,roles', [
    (CASES[0][1], ('友人の上司',)),
    (CASES[2][1], ('同僚の友人の先生',)),
    (CASES[3][1], ('友人の友人',)),
    (CASES[5][1], ('友人の上司', '同僚の上司')),
    (CASES[6][1], ('友人の上司', '上司')),
    (CASES[7][1], ('上司', '友人の上司')),
    (CASES[13][1], ('先生の後輩の先輩', '後輩の先輩', '先輩')),
])
def test_source_binding_covers_full_written_role_chain(text, roles):
    _, out = generated(text)
    assert tuple(b.role for b in out.source_meaning.role_bindings) == roles


@pytest.mark.parametrize('text,reason', [
    ('私は友人の上司の佐藤さんと友人の上司の田中さんに話を聞きたい。', 'public_role_binding_ambiguous'),
    ('私は友人の上司の佐藤さんと話したい。同僚の上司の佐藤さんは今日は休みだった。', 'public_role_binding_ambiguous'),
    ('私は友人の上司の佐藤さんと話したい。先生の佐藤さんは今日は休みだった。', 'public_role_binding_ambiguous'),
    ('私は佐藤さんと話したい。', 'public_role_binding_missing'),
    ('私は友人の上司の佐藤さんという名前を書きたい。', 'public_identity_is_material'),
    ('私は友人の上司の佐藤さんと話したい。呼び名は佐藤さん。', 'public_identity_is_material'),
])
def test_ambiguous_or_material_identity_is_not_invented(text, reason):
    source = PieceSourceSnapshot('synthetic-owner', 'synthetic-role-chain-rejected', 'v1', text)
    out = MeaningExperienceEngine().generate(PieceGenerationRequest(
        'synthetic-role-chain-rejected', source, source.owner_id, source.saved_input_id, source.source_version))
    assert out.status == EngineStatus.UNAVAILABLE
    assert out.reason_codes == (reason,)
    assert out.artifact is None


@pytest.mark.parametrize('case_index', [0, 5, 8, 10])
@pytest.mark.parametrize('ratio', ['4:5', '9:16'])
def test_b9_uses_same_complete_qualified_body(case_index, ratio):
    class Metrics:
        profile_id = 'synthetic-role-chain-not-device'
        def graphemes(self, text): return list(text)
        def measure(self, text, font_px):
            width = len(text) * font_px
            return TextMeasurement(width, 0, -font_px * .8, width, font_px * .2, True)
    _, out = generated(CASES[case_index][1])
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
