"""Bounded same-author continuity through the existing disabled CMEE writer.

All inputs are synthetic. Only a redundant written self-topic may be omitted;
full source propositions, their duties, public roles and limits still survive.
This is not authentication, activation, general coreference or native export.
"""
from dataclasses import asdict, replace
import hashlib

import pytest

from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.piece_v1c import (
    PieceGenerationRequest, compile_piece_artifact_plan, realize_piece_artifact,
)
from piece_v2_contract import canonical_sha256_hex, validate_piece_text_binding
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate
from piece_v2_layout import TextMeasurement, build_measured_layout
from piece_v2_visual import build_visual_recipe


CASES = (
    ('successive_wishes',
     '私は自分で納得して選びたい。私は小さく試して確かめたい。まだ、答えは決めていない。',
     '私は、自分で納得して選びたい。小さく試して確かめたい。まだ、答えは決めていない。'),
    ('named_owner_and_reservation',
     '私は友人の高橋さんの上司の伊藤さんと話したい。私は伊藤さんの考えを聞きたい。まだ、会う日は決めていない。',
     '私は、友人の上司と話したい。友人の上司の考えを聞きたい。まだ、会う日は決めていない。'),
    ('negative_then_positive',
     '私は焦って決めたくない。私は一人で考える時間を残したい。',
     '私は、焦って決めたくない。一人で考える時間を残したい。'),
    ('three_wishes',
     '私は自分で納得して選びたい。私は小さく試して確かめたい。私は後からゆっくり読み返したい。',
     '私は、自分で納得して選びたい。小さく試して確かめたい。後からゆっくり読み返したい。'),
    ('first_topic_in_later_block_stays',
     '私は静かな場所で読みたい。私は自分の感想を残したい。私は後からゆっくり読み返したい。',
     '私は静かな場所で読みたい。\n\n私は、自分の感想を残したい。後からゆっくり読み返したい。'),
    ('second_wish_negative',
     '私は自分で納得して選びたい。私は焦って結論を出したくない。まだ、答えは決めていない。',
     '私は、自分で納得して選びたい。焦って結論を出したくない。まだ、答えは決めていない。'),
) + tuple(
    (f'literal_speaker_{i}_{j}',
     f'{speaker}は自分で納得して選びたい{register}。{speaker}は小さく試して確かめたい{register}。',
     f'{speaker}は、自分で納得して選びたい{register}。小さく試して確かめたい{register}。')
    for i, speaker in enumerate(('私', 'わたし', '僕', 'ぼく', '俺', 'おれ'))
    for j, register in enumerate(('', 'です'))
    if not register or speaker == '私'
)

PRESERVED = (
    ('different_literal_speaker',
     '私は自分で選びたい。僕は小さく試したい。まだ、答えは決めていない。',
     '私は、自分で選びたい。僕は、小さく試したい。まだ、答えは決めていない。'),
    ('other_subject_before',
     '私は母が戻るなら、話したい。私は自分の気持ちを伝えたい。',
     '私は、母が戻るなら、話したい。私は、自分の気持ちを伝えたい。'),
    ('other_subject_after',
     '私は家族と話したい。私は母が戻るなら、話したい。',
     '私は、家族と話したい。私は、母が戻るなら、話したい。'),
    ('contrasting_topic',
     '私は人の話を聞きたい。私は今は返事を急ぎたくない。',
     '私は、人の話を聞きたい。私は、今は返事を急ぎたくない。'),
    ('additive_participant',
     '私は友人も試せるなら、話したい。私は自分の考えを整理したい。',
     '私は、友人も試せるなら、話したい。私は、自分の考えを整理したい。'),
    ('intervening_context',
     '私は自分で選びたい。昨日は時間が足りなかった。私は小さく試したい。',
     '私は、自分で選びたい。昨日は時間が足りなかった。私は、小さく試したい。'),
    ('intervening_other_person',
     '私は自分で選びたい。友人は休みたい。私は小さく試したい。',
     '私は、自分で選びたい。友人は休みたい。私は、小さく試したい。'),
    ('distinct_scope_operation',
     '私は家族と話したい。時間が取れるなら、私は近況を伝えたい。',
     '私は、家族と話したい。私は、時間が取れるなら、近況を伝えたい。'),
    ('reservation_is_not_a_wish',
     '私は小さく試したい。私はすぐに答えが出るとは思っていない。',
     '私は、小さく試したい。私はすぐに答えが出るとは思っていない。'),
    ('repeated_proposition',
     '私は自分で納得して選びたい。私は自分で納得して選びたい。まだ、答えは決めていない。',
     '私は、自分で納得して選びたい。私は自分で納得して選びたい。まだ、答えは決めていない。'),
    ('written_line_boundary',
     '私は自分で納得して選びたい。\n私は小さく試して確かめたい。',
     '私は、自分で納得して選びたい。私は、小さく試して確かめたい。'),
    ('written_paragraph_boundary',
     '私は自分で納得して選びたい。\n\n私は小さく試して確かめたい。',
     '私は、自分で納得して選びたい。私は、小さく試して確かめたい。'),
    ('minimum_envelope_not_lowered',
     '私は自分で選びたい。私は少しだけ試してみたい。',
     '私は、自分で選びたい。私は、少しだけ試してみたい。'),
)


def outcome(text, *, tier='free', requested=None):
    source = PieceSourceSnapshot('synthetic-owner', 'synthetic-continuity', '1', text)
    out = MeaningExperienceEngine().generate(PieceGenerationRequest(
        'synthetic-continuity', source, source.owner_id,
        source.saved_input_id, source.source_version, tier, requested))
    return source, out


@pytest.mark.parametrize('case,text,expected', CASES + PRESERVED,
                         ids=[c[0] for c in CASES + PRESERVED])
def test_complete_source_owned_body_and_unchanged_plan(case, text, expected):
    source, out = outcome(text)
    assert out.status == EngineStatus.GENERATED, out.as_body_free()
    meaning, plan, artifact = out.source_meaning, out.artifact_plan, out.artifact
    assert artifact.piece_text == expected
    assert meaning.envelope.raw_utf8 == text.encode('utf-8')
    assert plan == compile_piece_artifact_plan(meaning)
    covered = [n for block in plan.block_node_ids for n in block]
    assert sorted(covered) == sorted(n.node_id for n in meaning.graph.nodes)
    assert len(covered) == len(meaning.graph.nodes)
    for node, evidence in zip(meaning.graph.nodes, meaning.evidence, strict=True):
        assert text[evidence.scalar_start:evidence.scalar_end] == node.value
        assert text.encode('utf-8')[evidence.utf8_start:evidence.utf8_end].decode('utf-8') == node.value
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


@pytest.mark.parametrize('tier,requested', (
    ('free', None), ('plus', None), ('premium', None), ('premium', 'short_essay'),
))
def test_existing_tiers_use_same_complete_continuity(tier, requested):
    _, out = outcome(CASES[0][1], tier=tier, requested=requested)
    assert out.status == EngineStatus.GENERATED
    assert out.artifact.piece_text == CASES[0][2]
    assert out.artifact.format_type == 'short_essay'


@pytest.mark.parametrize('tier,requested', (
    ('free', 'short_essay'), ('plus', 'short_essay'),
    ('premium', 'quote'), ('premium', 'declaration'),
))
def test_omission_cannot_grant_format_choice(tier, requested):
    _, out = outcome(CASES[0][1], tier=tier, requested=requested)
    assert out.status == EngineStatus.UNAVAILABLE
    assert out.reason_codes == ('format_choice_not_admitted',)
    assert out.artifact is None


@pytest.mark.parametrize('damage', ('drop_duty', 'reorder', 'change_source'))
def test_continuity_does_not_license_damaged_source_or_plan(damage):
    _, out = outcome(CASES[0][1])
    meaning, plan = out.source_meaning, out.artifact_plan
    if damage == 'drop_duty':
        plan = replace(plan, duties=plan.duties[:-1])
    elif damage == 'reorder':
        plan = replace(plan, block_node_ids=(tuple(reversed(plan.block_node_ids[0])),))
    else:
        node = replace(meaning.graph.nodes[1], value='僕は小さく試して確かめたい。')
        meaning = replace(meaning, graph=replace(meaning.graph,
                          nodes=(meaning.graph.nodes[0], node, meaning.graph.nodes[2])))
    with pytest.raises(ValueError):
        realize_piece_artifact(meaning, plan, tier='free', requested_format=None)


def test_still_short_source_is_not_rescued():
    _, out = outcome('私は自分で選びたい。私は小さく試したい。')
    assert out.status == EngineStatus.UNAVAILABLE
    assert out.artifact is None
    assert out.reason_codes == ('format_not_eligible',)


@pytest.mark.parametrize('speaker', ('わたし', '僕', 'ぼく', '俺', 'おれ'))
def test_existing_unadmitted_polite_source_stays_unavailable(speaker):
    # The shared provisional-role parser does not yet admit these complete
    # inputs. An optional writer edit is not permission to change that owner.
    text = f'{speaker}は自分で納得して選びたいです。{speaker}は小さく試して確かめたいです。'
    _, out = outcome(text)
    assert out.status == EngineStatus.UNAVAILABLE
    assert out.reason_codes == ('expression_meaning_not_admitted',)
    assert out.artifact is None


@pytest.mark.parametrize('case_index', (0, 1, 2, 4))
@pytest.mark.parametrize('ratio', ('4:5', '9:16'))
def test_b9_receives_the_same_complete_body(case_index, ratio):
    class Metrics:
        profile_id = 'synthetic-continuity-not-device'
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
