"""A refined Engine result must bind to this exact source at the B8 seam.

All examples are fictional. Recipe/layout uses synthetic font metrics, without
native bitmap, public preview, database, quota or export side effects.
"""
from dataclasses import replace
import hashlib
from unittest.mock import patch

import pytest

from cocolon_meaning_experience_engine.engine import MeaningExperienceEngine
from cocolon_meaning_experience_engine.contracts import EngineStatus
from cocolon_meaning_experience_engine.piece_v1c import PieceEngineOutcome
from cocolon_meaning_experience_engine.piece_refined import validate_refined_preservation
from piece_v2_contract import PieceContractError, canonical_sha256_hex, validate_piece_text_binding
from piece_v2_generation import generate_piece_candidate
from piece_v2_visual import build_visual_recipe
from piece_v2_layout import TextMeasurement, build_measured_layout
from test_cmee_piece_refined_sources import source, request


def result(s):
    out = MeaningExperienceEngine().generate(request(s))
    assert out.status == EngineStatus.GENERATED, out.reason_codes
    return out


def rehashed_artifact(artifact, blocks):
    text = '\n\n'.join(blocks)
    return replace(artifact, body_blocks=tuple(blocks), piece_text=text,
                   piece_text_hash=hashlib.sha256(text.encode()).hexdigest())


@pytest.mark.parametrize('tier,ratio', [('free', '4:5'), ('plus', '4:5'), ('premium', '9:16')])
def test_refined_canonical_body_reaches_existing_recipe_and_layout(tier, ratio):
    class Metrics:
        profile_id = 'synthetic-refined-contract-metrics-not-device'
        def graphemes(self, text):
            return list(text)
        def measure(self, text, font_px):
            return TextMeasurement(len(text) * font_px, 0, -font_px * .8,
                                   len(text) * font_px, font_px * .2, True)
    s = source(answer='今は、私は嬉しい。')
    candidate = generate_piece_candidate(s, authenticated_owner_id=s.original.owner_id, tier=tier)
    assert candidate['piece_text'] == '私は、陶芸を選びたい。\n\n今は、私は嬉しい。'
    assert candidate['eligible_formats'] == ['short_essay']
    assert candidate['candidate_state'] == 'OFFLINE_NOT_ACCEPTED'
    assert candidate['production_enabled'] is False
    assert candidate['record_effect'] == candidate['quota_effect'] == 0
    recipe = build_visual_recipe(candidate['format_type'], tier=tier, aspect_ratio=ratio)
    layout = build_measured_layout(candidate, recipe, canonical_sha256_hex(recipe), Metrics())
    assert validate_piece_text_binding(candidate['content_payload'], candidate['piece_text'],
                                      candidate['piece_text_hash']) == candidate['piece_text']
    recovered = [''.join(line['text'] for line in layout['lines'] if line['block_index'] == index)
                 for index in range(len(candidate['content_payload']['body_blocks']))]
    assert recovered == candidate['content_payload']['body_blocks']
    assert recipe['format_type'] == 'short_essay' and recipe['aspect_ratio'] == ratio


@pytest.mark.parametrize('substitution,expected', [
    ('source', 'piece_engine_source_binding'),
    ('plan', 'piece_engine_plan_binding'),
    ('rehashed-negation', 'piece_engine_artifact_binding'),
    ('rehashed-omission', 'piece_engine_artifact_binding'),
])
def test_generated_result_cannot_substitute_source_plan_or_body(substitution, expected):
    s = source(answer='私は嬉しかった。')
    good = result(s)
    other = result(source(answer='私は楽しかった。'))
    if substitution == 'source':
        forged = replace(good, source_meaning=other.source_meaning)
    elif substitution == 'plan':
        forged = replace(good, artifact_plan=other.artifact_plan)
    elif substitution == 'rehashed-negation':
        forged = replace(good, artifact=rehashed_artifact(good.artifact,
            (*good.artifact.body_blocks[:-1], '私は嬉しくなかった。')))
    else:
        forged = replace(good, artifact=rehashed_artifact(good.artifact,
            good.artifact.body_blocks[:-1]))
    with patch.object(MeaningExperienceEngine, 'generate', return_value=forged) as generated:
        with pytest.raises(PieceContractError) as exc:
            generate_piece_candidate(s, authenticated_owner_id=s.original.owner_id)
        assert exc.value.detail == expected
        assert generated.call_count == 1


def test_semantically_allowed_spelling_does_not_replace_the_canonical_author_output():
    s = source(answer='私は嬉しかった。')
    good = result(s)
    # The finite author-free check permits the same explicit first-person
    # proposition without the editorial comma. B8 still returns the sole
    # author's canonical artifact, rather than a substituted valid spelling.
    changed = rehashed_artifact(good.artifact,
        ('私は陶芸を選びたい。', *good.artifact.body_blocks[1:]))
    validate_refined_preservation(good.source_meaning, good.artifact_plan, changed)
    with patch.object(MeaningExperienceEngine, 'generate', return_value=replace(good, artifact=changed)):
        with pytest.raises(PieceContractError) as exc:
            generate_piece_candidate(s, authenticated_owner_id=s.original.owner_id)
        assert exc.value.detail == 'piece_engine_artifact_binding'


def test_refined_engine_cannot_hide_wrong_owner_behind_a_generated_result():
    s = source(answer='私は嬉しかった。')
    with patch.object(MeaningExperienceEngine, 'generate', return_value=result(s)):
        with pytest.raises(PieceContractError) as exc:
            generate_piece_candidate(s, authenticated_owner_id='different-owner')
        assert exc.value.detail == 'piece_refined_owner_mismatch'


@pytest.mark.parametrize('returned', [object(), PieceEngineOutcome(EngineStatus.UNAVAILABLE, ('test-unavailable',))])
def test_refined_candidate_requires_a_generated_typed_outcome(returned):
    s = source(answer='私は嬉しかった。')
    with patch.object(MeaningExperienceEngine, 'generate', return_value=returned):
        with pytest.raises(PieceContractError):
            generate_piece_candidate(s, authenticated_owner_id=s.original.owner_id)
