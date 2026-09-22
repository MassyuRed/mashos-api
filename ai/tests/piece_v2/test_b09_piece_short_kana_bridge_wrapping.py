"""Synthetic B9 short-kana bridge tests; no private replay bodies or native credit."""
from copy import deepcopy
from functools import lru_cache
import itertools
import unicodedata

import pytest
import piece_v2_layout as module
from piece_v2_layout import TextMeasurement, _wrap, build_measured_layout, fit_summary
from piece_v2_contract import canonical_sha256_hex
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate
from piece_v2_visual import build_visual_recipe


class Metrics:
    profile_id = 'synthetic-short-kana-bridge-not-native'

    def graphemes(self, text):
        # Only the explicitly exercised combining/variation sequences. This is
        # a test fixture, not a replacement UAX29 segmenter in production.
        clusters = []
        for c in text:
            if clusters and (unicodedata.combining(c) or 0xE0100 <= ord(c) <= 0xE01EF):
                clusters[-1] += c
            else:
                clusters.append(c)
        return clusters

    def measure(self, text, font_px):
        width = len(self.graphemes(text)) * font_px
        return TextMeasurement(width, 0, -font_px * .8, width, font_px * .2)


def wrapped(text, width, metrics=None):
    return [part for part, _ in _wrap(text, size=1, width=width, metrics=metrics or Metrics())]


def cuts(parts):
    return set(itertools.accumulate(len(part) for part in parts[:-1]))


# Explicit boundary positions independently authored for small visual strings.
# The oracle enumerates every legal partition; it does not call a production
# hint helper or reproduce the production dynamic program.
ORACLES = (
    ('あ読み返す。', (), (), (2, 4), (3,)),
    ('あ取り戻す。', (), (), (2, 4), (3,)),
    ('あ書き直す。', (), (), (2, 4), (3,)),
    ('あ受け取る。', (), (), (2, 4), (3,)),
    ('あ落ち着く。', (), (), (2, 4), (3,)),
    ('あメモし直す。', (), (2,), (3, 5), (4,)),
    ('あ資料を読む。', (), (2,), (3, 5), ()),
    ('あ見て読む。', (), (), (2, 4), ()),
    ('あ先に読む。', (), (), (2, 4), ()),
    ('あ読み返す。まだ', (), (), (2, 4), (3,)),
    ('AB読み返す。', (1,), (), (3, 5), (4,)),
)


def partitions(text, width):
    for mask in range(1 << (len(text) - 1)):
        points = [0] + [i for i in range(1, len(text)) if mask & (1 << (i - 1))] + [len(text)]
        parts = [text[a:b] for a, b in zip(points, points[1:])]
        if all(len(part) <= width and part[0] not in '。、' for part in parts):
            yield parts


def score(parts, text, width, ascii_cuts, script_cuts, kana_cuts, bridge_cuts):
    points = cuts(parts)
    return (len(parts), len(points.intersection(ascii_cuts)),
            len(points.intersection(script_cuts)),
            sum(i >= 2 and text[i - 2] in '。！？!?' for i in points),
            len(points.intersection(kana_cuts)), len(points.intersection(bridge_cuts)),
            sum((width - len(part)) ** 2 for part in parts))


@pytest.mark.parametrize('case', ORACLES)
@pytest.mark.parametrize('width', (2, 3, 4, 5, 6, 7))
def test_exhaustive_ordered_preferences_preserve_priorities(case, width):
    text, ascii_cuts, script_cuts, kana_cuts, bridge_cuts = case
    actual = wrapped(text, width)
    def cost(parts):
        return score(parts, text, width, ascii_cuts, script_cuts, kana_cuts, bridge_cuts)
    assert ''.join(actual) == text
    assert cost(actual) == min(map(cost, partitions(text, width)))


@pytest.mark.parametrize('particle', tuple('はがのにをとでへもやて'))
def test_common_particles_are_not_promoted_to_compound_bridges(particle):
    text = f'あ本{particle}読む。'
    actual = wrapped(text, 4)
    def cost(parts):
        return score(parts, text, 4, (), (), (2, 4), ())
    assert cost(actual) == min(map(cost, partitions(text, 4)))
    assert ''.join(actual) == text


@pytest.mark.parametrize('separator', (' ', '、', '。', 'A', '🙂'))
def test_separators_do_not_create_a_short_bridge(separator):
    text = f'あ読{separator}み返す。'
    actual = wrapped(text, 4)
    # The hiragana has no immediately preceding Han/Katakana grapheme.
    def cost(parts):
        return score(parts, text, 4, (), (), (5,), ())
    assert cost(actual) == min(map(cost, partitions(text, 4)))
    assert ''.join(actual) == text


@pytest.mark.parametrize('text', ('読み返し書き直し取り戻す。', '受け取り直してみたかった。'))
@pytest.mark.parametrize('width', (2, 3, 4, 5, 7))
def test_overwide_chains_remain_breakable_at_minimum_legal_line_count(text, width):
    @lru_cache(None)
    def minimum(start):
        if start == len(text):
            return 0
        return min(1 + minimum(end) for end in range(start + 1, min(len(text), start + width) + 1)
                   if end == len(text) or text[end] not in '。、っ')
    actual = wrapped(text, width)
    assert len(actual) == minimum(0)
    assert ''.join(actual) == text
    assert all(len(part) <= width and part[0] not in '。、っ' for part in actual)


@pytest.mark.parametrize('text', ('あ泳き\u3099直す。', 'あ読\U000E0100み返す。', 'あﾒﾓし直す。'))
@pytest.mark.parametrize('width', (3, 4, 5))
def test_renderer_owned_graphemes_stay_exact(text, width):
    metrics = Metrics()
    actual = wrapped(text, width, metrics)
    assert ''.join(actual) == text
    assert cuts(actual).issubset(cuts(metrics.graphemes(text)))
    assert all(len(metrics.graphemes(part)) <= width for part in actual)


def test_whole_substring_measurement_and_bearings_remain_authoritative():
    class Proportional(Metrics):
        def measure(self, text, font_px):
            advance = sum(.4 if c == 'あ' else 1.0 for c in text)
            # Non-additive pair width and non-zero overhang both matter.
            advance -= .2 * text.count('読み')
            return TextMeasurement(advance, -.2, -.8, advance + .1, .2)
    metrics = Proportional()
    text = 'あ読み返す。'
    rows = _wrap(text, size=1, width=4, metrics=metrics)
    assert ''.join(part for part, _ in rows) == text
    for part, measurement in rows:
        assert measurement == metrics.measure(part, 1)
        assert max(measurement.advance, measurement.right) - min(0, measurement.left) <= 4


@pytest.mark.parametrize('fault', ('missing', 'nonfinite', 'exception', 'broken_grapheme'))
def test_bridges_never_bypass_renderer_failure(fault):
    class Broken(Metrics):
        def graphemes(self, text):
            return list(text) if fault == 'broken_grapheme' else super().graphemes(text)
        def measure(self, text, font_px):
            if fault == 'exception':
                raise RuntimeError('synthetic metrics failure')
            if fault == 'missing':
                return TextMeasurement(1, 0, -.8, 1, .2, False)
            if fault == 'nonfinite':
                return TextMeasurement(float('nan'), 0, -.8, 1, .2)
            return super().measure(text, font_px)
    with pytest.raises(ValueError):
        wrapped('あ泳き\u3099直す。', 4, Broken())


@pytest.mark.parametrize('ratio', ('4:5', '9:16'))
@pytest.mark.parametrize('theme', ('soft_paper', 'quiet_night'))
def test_existing_cmee_candidate_and_recipe_are_not_rewritten(ratio, theme):
    text = '私は机で資料を読み返す時間を大切にしたい。まだ、毎日できるとは限らない。'
    source = PieceSourceSnapshot('synthetic-owner', 'synthetic-bridge', '1', text)
    candidate = generate_piece_candidate(source, authenticated_owner_id=source.owner_id)
    recipe = build_visual_recipe(candidate['format_type'], tier='premium', theme=theme, aspect_ratio=ratio)
    before = deepcopy(candidate), deepcopy(recipe)
    result = build_measured_layout(candidate, recipe, canonical_sha256_hex(recipe), Metrics())
    assert (candidate, recipe) == before
    blocks = candidate['content_payload']['body_blocks']
    assert [''.join(row['text'] for row in result['lines'] if row['block_index'] == i)
            for i in range(len(blocks))] == blocks
    assert result['piece_text_hash'] == candidate['piece_text_hash']
    assert result['visual_recipe_hash'] == canonical_sha256_hex(recipe)
    assert result['font_px'] >= result['font_floor_px']
    assert not result['clipped'] and not result['missing_glyph']
    assert not result['native_device_verified'] and not candidate['production_enabled']
    assert result['record_effect'] == result['quota_effect'] == 0
    assert 'lines' not in fit_summary(result)


def test_imported_owner_path_is_reported():
    print('TESTED_LAYOUT_PATH', module.__file__)
    assert module.__file__.endswith('/ai/services/ai_inference/piece_v2_layout.py')
