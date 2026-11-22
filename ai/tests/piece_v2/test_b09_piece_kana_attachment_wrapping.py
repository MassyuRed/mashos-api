"""Synthetic B9 mixed-script attachment checks, not native/product acceptance.

Attachment hints belong to the existing measured layout. They never create
word meanings, rewrite the candidate or supersede renderer-owned graphemes.
"""
from copy import deepcopy
import hashlib
import itertools
import math
import unicodedata

import pytest

from piece_v2_contract import canonical_sha256_hex
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate
from piece_v2_layout import TextMeasurement, _wrap, build_measured_layout, fit_summary
from piece_v2_visual import build_visual_recipe


class Metrics:
    profile_id = 'synthetic-kana-attachment-not-device'

    def graphemes(self, text):
        clusters = []
        for char in text:
            if clusters and (unicodedata.combining(char) or char in '\U000E0100ﾞﾟ'):
                clusters[-1] += char
            else:
                clusters.append(char)
        return clusters

    def measure(self, text, font_px):
        advance = len(self.graphemes(text)) * font_px
        return TextMeasurement(advance, 0, -font_px * .8, advance, font_px * .2)


def wrapped(text, width, metrics=None):
    return [part for part, _ in _wrap(text, size=1, width=width,
                                     metrics=metrics or Metrics())]


def cuts(parts):
    return set(itertools.accumulate(map(len, parts[:-1])))


@pytest.mark.parametrize('text,width,attachment', (
    ('机で資料を眺めて過ごす。', 7, '眺めて'),
    ('机で資料を眺めて過ごす。', 9, '眺めて'),
    ('私は絵を描いてみたい。', 7, '描いてみたい'),
    ('私は絵を描いてみたい。', 9, '描いてみたい'),
    ('自分で確かめたい。', 6, '確かめたい'),
    ('自分で確かめたい。', 8, '確かめたい'),
    ('新しく読み返してみたい。', 7, '返してみたい'),
    ('庭で花を育てる時間が好き。', 7, '育てる'),
))
def test_attached_kana_stays_together_at_the_existing_minimum_line_count(text, width, attachment):
    parts = wrapped(text, width)
    assert ''.join(parts) == text
    assert len(parts) == math.ceil(len(text) / width)
    start = text.index(attachment)
    assert not cuts(parts).intersection(range(start + 1, start + len(attachment)))


# Exact synthetic boundary sets, independent of the layout's Unicode helper.
# Each set contains scalar positions between characters, not lexical labels.
ORACLE_CASES = (
    ('あ描いてみたい。', (), (), (2, 3, 4, 5, 6)),
    ('あ資料を描く。', (), (2,), (3, 5)),
    ('あメモして読む。', (), (2,), (3, 4, 6)),
    ('あABと描く。', (2,), (), (5,)),
    ('あ描く。まだ', (), (), (2,)),
    ('あ描く、みたい。', (), (), (2,)),
    ('あ描く みたい。', (), (), (2,)),
)


@pytest.mark.parametrize('text,ascii_cuts,script_cuts,kana_cuts', ORACLE_CASES)
@pytest.mark.parametrize('width', (3, 4, 5, 6))
def test_exhaustive_partitions_follow_the_ordered_soft_preferences(text, ascii_cuts, script_cuts, kana_cuts, width):
    # Exhaustively enumerate all legal partitions instead of using DP.
    # Minimum lines, ASCII, prior script runs and sentence heads all retain
    # priority over this new hint; only balance is lower priority.
    def score(parts):
        points = cuts(parts)
        heads = sum(i >= 2 and text[i - 2] in '。！？!?' for i in points)
        return (len(parts), len(points.intersection(ascii_cuts)),
                len(points.intersection(script_cuts)), heads,
                len(points.intersection(kana_cuts)),
                sum((width - len(part)) ** 2 for part in parts))
    possible = []
    for mask in range(1 << (len(text) - 1)):
        points = [0] + [i for i in range(1, len(text)) if mask & (1 << (i - 1))] + [len(text)]
        parts = [text[a:b] for a, b in zip(points, points[1:])]
        if all(len(part) <= width and part[0] not in '。、' for part in parts):
            possible.append(parts)
    actual = wrapped(text, width)
    assert ''.join(actual) == text
    assert score(actual) == min(map(score, possible))


@pytest.mark.parametrize('width', (3, 5, 8))
@pytest.mark.parametrize('text', (
    '書いてみたかったかもしれない。',
    'メモしてみたかったかもしれない。',
    'あいうえおかきくけこさしすせそ。',
))
def test_overwide_attached_runs_still_split_without_extra_lines_or_text_changes(text, width):
    parts = wrapped(text, width)
    assert ''.join(parts) == text
    # Hard kinsoku can require more lines than ceil(length / width).
    # Count all reachable legal endings without any readability preferences.
    reachable = {0}
    for count in range(1, len(text) + 1):
        reachable = {end for start in reachable
                     for end in range(start + 1, min(start + width, len(text)) + 1)
                     if end == len(text) or text[end] not in '。、っ'}
        if len(text) in reachable:
            break
    assert len(parts) == count
    assert all(0 < len(part) <= width for part in parts)


@pytest.mark.parametrize('text,grapheme', (
    ('私は泳き\u3099たい。', 'き\u3099'),
    ('私は葛\U000E0100を描きたい。', '葛\U000E0100'),
    ('私はｶﾞラスを描きたい。', 'ｶﾞ'),
))
@pytest.mark.parametrize('width', (4, 6))
def test_renderer_owned_combining_and_variation_clusters_are_not_split(text, grapheme, width):
    parts = wrapped(text, width)
    assert ''.join(parts) == text
    start = text.index(grapheme)
    assert not cuts(parts).intersection(range(start + 1, start + len(grapheme)))


def test_variable_width_and_bearings_use_full_substring_measurements():
    class Proportional(Metrics):
        def measure(self, text, font_px):
            advance = sum(1.8 if c == '描' else .6 for c in text)
            return TextMeasurement(advance, -1.2, -.8, advance + .7, .2)
    text = 'あ描いてみたい。'
    metrics = Proportional()
    rows = _wrap(text, size=1, width=7, metrics=metrics)
    assert ''.join(part for part, _ in rows) == text
    for part, measurement in rows:
        assert measurement == metrics.measure(part, 1)
        assert max(measurement.advance, measurement.right) - min(0, measurement.left) <= 7


@pytest.mark.parametrize('fault', ('missing', 'nonfinite', 'exception', 'broken_grapheme'))
def test_attachment_hints_do_not_bypass_renderer_failures(fault):
    class Broken(Metrics):
        def graphemes(self, text):
            return list(text) if fault == 'broken_grapheme' else super().graphemes(text)
        def measure(self, text, font_px):
            if fault == 'exception':
                raise RuntimeError('synthetic measurement failure')
            if fault == 'nonfinite':
                return TextMeasurement(float('nan'), 0, -.8, 1, .2)
            if fault == 'missing':
                return TextMeasurement(1, 0, -.8, 1, .2, False)
            return super().measure(text, font_px)
    with pytest.raises(ValueError):
        wrapped('泳き\u3099たい。', 4, Broken())


SOURCES = (
    '僕は棚の資料を並べ替える時間が好き。まだ、毎日続けられるとは限らない。',
    '日程が合うなら、私にとって机で下書きを読み返す時間が必要。まだ、毎日続けられるとは限らない。',
    '僕が大切にしたいのは、机で下書きを読み返す時間です。僕はその時間が好き。まだ、毎日続けられるとは限らない。',
)


@pytest.mark.parametrize('source_text', SOURCES)
@pytest.mark.parametrize('ratio', ('4:5', '9:16'))
@pytest.mark.parametrize('theme', ('soft_paper', 'quiet_night'))
def test_cmee_candidate_recipe_and_every_block_remain_exact(source_text, ratio, theme):
    source = PieceSourceSnapshot('synthetic-owner', 'synthetic-kana-layout', '1', source_text)
    candidate = generate_piece_candidate(source, authenticated_owner_id=source.owner_id)
    recipe = build_visual_recipe(candidate['format_type'], tier='premium', theme=theme, aspect_ratio=ratio)
    before = deepcopy(candidate), deepcopy(recipe)
    layout = build_measured_layout(candidate, recipe, canonical_sha256_hex(recipe), Metrics())
    blocks = candidate['content_payload']['body_blocks']
    rebuilt = [''.join(line['text'] for line in layout['lines'] if line['block_index'] == i)
               for i in range(len(blocks))]
    assert rebuilt == blocks
    assert '\n\n'.join(rebuilt) == candidate['piece_text']
    assert layout['piece_text_hash'] == hashlib.sha256(candidate['piece_text'].encode()).hexdigest()
    assert layout['visual_recipe_hash'] == canonical_sha256_hex(recipe)
    assert before == (candidate, recipe)
    assert layout['font_px'] >= layout['font_floor_px']
    assert not layout['clipped'] and not layout['missing_glyph']
    assert not layout['native_device_verified'] and not candidate['production_enabled']
    assert layout['record_effect'] == layout['quota_effect'] == 0
    assert 'lines' not in fit_summary(layout)
    for line in layout['lines']:
        left, top, right, bottom = line['ink_box']
        assert layout['margin'] <= left <= right <= layout['width'] - layout['margin']
        assert layout['margin'] <= top <= bottom <= layout['height'] - layout['margin'] - layout['branding_zone']
