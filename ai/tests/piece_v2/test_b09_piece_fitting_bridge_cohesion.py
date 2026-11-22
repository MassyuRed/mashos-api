"""Synthetic measured-fit bridge cohesion; no private replays or native credit.

Small exhaustive partitions are independent of the production hint builder
and dynamic program. Old tests/expected preferences are left untouched.
"""
from copy import deepcopy
from functools import lru_cache
import hashlib
import itertools
import unicodedata

import pytest

from piece_v2_layout import TextMeasurement, _wrap, build_measured_layout, fit_summary
from piece_v2_contract import canonical_sha256_hex
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate
from piece_v2_visual import build_visual_recipe


class Metrics:
    profile_id = 'synthetic-fitting-bridge-not-native'

    def graphemes(self, text):
        # Fixture support for the explicitly tested combining/variation forms,
        # not a replacement production UAX29 segmenter.
        result = []
        for char in text:
            if result and (unicodedata.combining(char) or 0xE0100 <= ord(char) <= 0xE01EF):
                result[-1] += char
            else:
                result.append(char)
        return result

    def measure(self, text, font_px):
        width = len(self.graphemes(text)) * font_px
        return TextMeasurement(width, 0, -font_px * .8, width, font_px * .2)


def wrapped(text, width, metrics=None):
    return [part for part, _ in _wrap(text, size=1, width=width, metrics=metrics or Metrics())]


def cuts(parts):
    return set(itertools.accumulate(map(len, parts[:-1])))


# text, ASCII cuts, script cuts, attached-kana cuts, short-bridge cuts,
# maximal connected run, complete required-punctuation measurement range.
# All coordinates are hand-authored for these small BMP-only strings.
ORACLES = (
    ('あい読み返す。まだ', (), (), (3, 5), (4,), (2, 6), (2, 7)),
    ('あい書き直す。まだ', (), (), (3, 5), (4,), (2, 6), (2, 7)),
    ('あい落ち着く。まだ', (), (), (3, 5), (4,), (2, 6), (2, 7)),
    ('あいメモし直す。まだ', (), (3,), (4, 6), (5,), (2, 7), (2, 8)),
    ('AB読み返す。まだ', (1,), (), (3, 5), (4,), (2, 6), (2, 7)),
    ('あ読み返す。まだ', (), (), (2, 4), (3,), (1, 5), (1, 6)),
    ('あい「読み返す。」まだ', (), (), (4, 6), (5,), (3, 7), (2, 9)),
    ('あい読、み返す。', (), (), (6,), (), None, None),
    ('あい資料を読む。', (), (3,), (4, 6), (), None, None),
    ('あい読み返し直す。', (), (), (3, 5, 7), (4, 6), (2, 8), (2, 9)),
    ('あい読んで返す。', (), (), (3, 4, 6), (), None, None),
)


def partitions(text, width):
    for mask in range(1 << (len(text) - 1)):
        points = [0] + [i for i in range(1, len(text)) if mask & (1 << (i - 1))] + [len(text)]
        parts = [text[a:b] for a, b in zip(points, points[1:])]
        if all(len(part) <= width and part[0] not in '。、」' and part[-1] != '「' for part in parts):
            yield parts


def independent_score(parts, case, width):
    text, ascii_cuts, script_cuts, kana_cuts, bridge_cuts, run, required = case
    points = cuts(parts)
    fitting = bool(required and required[1] - required[0] <= width)
    cohesion = (len(points.intersection(range(run[0] + 1, run[1])))
                + sum(len(part) == 1 for part in parts)) if fitting else 0
    return (cohesion, len(parts), len(points.intersection(ascii_cuts)),
            len(points.intersection(script_cuts)),
            sum(i >= 2 and text[i - 2] in '。！？!?' for i in points),
            len(points.intersection(kana_cuts)), len(points.intersection(bridge_cuts)),
            sum((width - len(part)) ** 2 for part in parts))


@pytest.mark.parametrize('case', ORACLES)
@pytest.mark.parametrize('width', (2, 3, 4, 5, 6, 7, 8))
def test_exhaustive_measured_fit_cohesion_without_single_grapheme_tradeoff(case, width):
    text = case[0]
    legal = list(partitions(text, width))
    if not legal:
        with pytest.raises(ValueError, match='unbreakable_line'):
            wrapped(text, width)
        return
    actual = wrapped(text, width)
    assert ''.join(actual) == text
    assert independent_score(actual, case, width) == min(
        independent_score(parts, case, width) for parts in legal)


@pytest.mark.parametrize('word', ('読み返す', '書き直す', '落ち着く', '取り戻す', '受け取る'))
def test_a_readable_extra_line_can_keep_a_fitting_compound_intact(word):
    text = 'あい' + word + '。まだ'
    actual = wrapped(text, 5)
    assert actual == ['あい', word + '。', 'まだ']
    assert ''.join(actual) == text


def test_cohesion_does_not_buy_a_new_single_grapheme_line():
    text = 'あ読み返す。まだ'
    actual = wrapped(text, 5)
    assert len(actual) == 2
    assert all(len(part) > 1 for part in actual)
    assert ''.join(actual) == text


@pytest.mark.parametrize('text,width', (
    ('あい「読み返す。」まだ', 5),
    ('あい読み返す。まだ', 4),
    ('あい読み返し直す。', 5),
    ('あい読み返し書き直し取り戻す。', 4),
))
def test_overwide_maximal_runs_and_required_marks_stay_freely_breakable(text, width):
    @lru_cache(None)
    def minimum(start):
        if start == len(text):
            return 0
        scores = [1 + minimum(end) for end in range(start + 1, min(len(text), start + width) + 1)
                  if (end == len(text) or text[end] not in '。、」') and text[end - 1] != '「']
        return min(scores, default=10000)
    actual = wrapped(text, width)
    assert len(actual) == minimum(0)
    assert ''.join(actual) == text
    assert all(len(part) <= width for part in actual)


@pytest.mark.parametrize('particle', tuple('はがのにをとでへもやて'))
def test_common_particles_do_not_acquire_a_fit_cohesion_priority(particle):
    text = f'あい本{particle}読む。まだ'
    actual = wrapped(text, 5)
    assert len(actual) == 2
    assert ''.join(actual) == text


@pytest.mark.parametrize('text,unit', (
    ('あい泳き\u3099直す。まだ', '泳き\u3099直す。'),
    ('あい読\U000E0100み返す。まだ', '読\U000E0100み返す。'),
    ('あいﾒﾓし直す。まだ', 'ﾒﾓし直す。'),
))
def test_fitting_and_line_cuts_use_renderer_graphemes_not_scalar_counts(text, unit):
    metrics = Metrics()
    width = len(metrics.graphemes(unit))
    actual = wrapped(text, width, metrics)
    assert actual == ['あい', unit, 'まだ']
    assert ''.join(actual) == text
    assert cuts(actual).issubset(cuts(metrics.graphemes(text)))


@pytest.mark.parametrize('overhang', (0, .25, 1))
def test_required_punctuation_real_overhang_and_nonadditive_width_control_fit(overhang):
    class Proportional(Metrics):
        def measure(self, text, font_px):
            advance = len(self.graphemes(text)) - .5 * text.count('読み')
            return TextMeasurement(advance, -overhang, -.8, advance + overhang, .2)
    metrics = Proportional()
    unit = '読み返す。'
    m = metrics.measure(unit, 1)
    exact_width = max(m.advance, m.right) - min(0, m.left)
    rows = _wrap('あい' + unit + 'まだ', size=1, width=exact_width, metrics=metrics)
    assert any(part == unit for part, _ in rows)
    for part, measurement in rows:
        assert measurement == metrics.measure(part, 1)
        assert max(measurement.advance, measurement.right) - min(0, measurement.left) <= exact_width


@pytest.mark.parametrize('fault', ('missing', 'nonfinite', 'exception', 'broken_grapheme'))
def test_fitting_hint_never_bypasses_measurement_or_partition_failure(fault):
    class Broken(Metrics):
        def graphemes(self, text):
            return list(text) if fault == 'broken_grapheme' else super().graphemes(text)
        def measure(self, text, font_px):
            if fault == 'exception':
                raise RuntimeError('synthetic measurement failure')
            if fault == 'missing':
                return TextMeasurement(1, 0, -.8, 1, .2, False)
            if fault == 'nonfinite':
                return TextMeasurement(float('nan'), 0, -.8, 1, .2)
            return super().measure(text, font_px)
    with pytest.raises(ValueError):
        wrapped('あい泳き\u3099直す。まだ', 5, Broken())


SOURCES = (
    '私は机で下書きを読み返す時間を大切にしたい。まだ、毎日続けられるとは限らない。',
    '私にとって棚の道具を取り戻すことが大切。私はそのことが好き。まだ、日程は決めていない。',
    '僕が大切にしたいのは、机で下書きを書き直す時間です。僕はその時間が好き。まだ、毎日続けられるとは限らない。',
)


@pytest.mark.parametrize('source_text', SOURCES)
@pytest.mark.parametrize('ratio', ('4:5', '9:16'))
@pytest.mark.parametrize('theme', ('soft_paper', 'quiet_night'))
def test_existing_cmee_body_recipe_and_all_blocks_remain_exact(source_text, ratio, theme):
    source = PieceSourceSnapshot('synthetic-owner', 'synthetic-fitting-bridge', '1', source_text)
    candidate = generate_piece_candidate(source, authenticated_owner_id=source.owner_id)
    recipe = build_visual_recipe(candidate['format_type'], tier='premium', theme=theme, aspect_ratio=ratio)
    before = deepcopy(candidate), deepcopy(recipe)
    layout = build_measured_layout(candidate, recipe, canonical_sha256_hex(recipe), Metrics())
    blocks = candidate['content_payload']['body_blocks']
    rebuilt = [''.join(line['text'] for line in layout['lines'] if line['block_index'] == i)
               for i in range(len(blocks))]
    assert rebuilt == blocks and '\n\n'.join(rebuilt) == candidate['piece_text']
    assert before == (candidate, recipe)
    assert layout['piece_text_hash'] == hashlib.sha256(candidate['piece_text'].encode()).hexdigest()
    assert layout['visual_recipe_hash'] == canonical_sha256_hex(recipe)
    assert layout['font_px'] >= layout['font_floor_px']
    assert not layout['clipped'] and not layout['missing_glyph'] and not layout['native_device_verified']
    assert not candidate['production_enabled'] and layout['record_effect'] == layout['quota_effect'] == 0
    assert 'lines' not in fit_summary(layout)
    for line in layout['lines']:
        left, top, right, bottom = line['ink_box']
        assert layout['margin'] <= left <= right <= layout['width'] - layout['margin']
        assert layout['margin'] <= top <= bottom <= layout['height'] - layout['margin'] - layout['branding_zone']


@pytest.mark.parametrize('block_count', (1, 2))
@pytest.mark.parametrize('lines_per_block', (4, 5))
@pytest.mark.parametrize('single_size', (False, True))
def test_vertical_capacity_falls_back_at_same_size_before_shrinking_or_refusing(
        monkeypatch, block_count, lines_per_block, single_size):
    import math
    import piece_v2_layout as module
    source = PieceSourceSnapshot('synthetic-owner', 'synthetic-capacity', '1', SOURCES[0])
    candidate = generate_piece_candidate(source, authenticated_owner_id=source.owner_id)
    body = candidate['piece_text']
    # Valid pure-layout fixture with repeated blocks; no record is created.
    candidate['content_payload']['body_blocks'] = [body] * block_count
    candidate['piece_text'] = '\n\n'.join([body] * block_count)
    candidate['piece_text_hash'] = hashlib.sha256(candidate['piece_text'].encode()).hexdigest()
    recipe = build_visual_recipe(candidate['format_type'], tier='premium', aspect_ratio='9:16')
    original_resolve = module.resolve_visual

    def constrained_surface(value):
        # Synthetic content-zone capacity, not a change to the product recipe.
        resolved = original_resolve(value)
        size = resolved['font_sizes'][0]
        line_height = math.ceil(size * resolved['line_height_ratio'])
        gap = line_height * resolved['paragraph_spacing_ratio']
        resolved['width'] = 2 * resolved['margin'] + 10 * size
        resolved['height'] = (2 * resolved['margin'] + resolved['branding_zone']
                              + line_height * lines_per_block * block_count + gap * (block_count - 1))
        if single_size:
            resolved['font_sizes'] = [size]
        return resolved

    monkeypatch.setattr(module, 'resolve_visual', constrained_surface)
    before = deepcopy(candidate), deepcopy(recipe)
    layout = build_measured_layout(candidate, recipe, canonical_sha256_hex(recipe), Metrics())
    assert layout['font_px'] == 52
    assert len(layout['lines']) == lines_per_block * block_count
    assert (candidate, recipe) == before
    for index in range(block_count):
        parts = [line['text'] for line in layout['lines'] if line['block_index'] == index]
        assert ''.join(parts) == body
        if lines_per_block == 5:
            assert any('読み返す' in part for part in parts)
    assert layout['record_effect'] == layout['quota_effect'] == 0
    assert not layout['native_device_verified']
