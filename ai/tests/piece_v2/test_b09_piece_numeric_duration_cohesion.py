"""Measured numeric-duration cohesion; synthetic text, no native acceptance.

The small exhaustive oracle marks its own boundaries. It neither calls the
production hint helper nor uses the production dynamic program for expectations.
"""
from copy import deepcopy
from functools import lru_cache
import itertools
import unicodedata

import pytest
import piece_v2_layout as lm
from piece_v2_layout import TextMeasurement
from piece_v2_contract import canonical_sha256_hex
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate
from piece_v2_visual import build_visual_recipe


class Metrics:
    profile_id = 'synthetic-numeric-duration-not-native'

    def graphemes(self, text):
        result = []
        for char in text:
            if result and (unicodedata.combining(char) or 0xFE00 <= ord(char) <= 0xFE0F
                           or 0xE0100 <= ord(char) <= 0xE01EF):
                result[-1] += char
            else:
                result.append(char)
        return result

    def measure(self, text, font_px):
        width = len(self.graphemes(text)) * font_px
        return TextMeasurement(width, 0, -.8 * font_px, width, .2 * font_px)


def rows(text, width, metrics=None):
    return [part for part, _ in lm._wrap(text, size=10, width=width * 10,
                                       metrics=metrics or Metrics())]


@pytest.mark.parametrize('duration', (
    '30秒間', '15分間', '24時間', '3日間', '2週間', '6か月間', '6ヶ月間', '6箇月間', '1年間',
    '３日間', '０３日間', '3４日間',
))
def test_complete_fitting_duration_is_kept_together(duration):
    text = '前記。これから' + duration + '、続けたい。'
    actual = rows(text, len(duration) + 4)
    assert ''.join(actual) == text
    assert any(duration in part for part in actual), actual


@pytest.mark.parametrize('left,right', (('「', '」'), ('（', '）'), ('', '、')))
def test_required_punctuation_participates_in_measured_fit(left, right):
    run = left + '３日間' + right
    text = '前記。' + run + '後記。'
    actual = rows(text, len(run))
    assert ''.join(actual) == text
    assert any(run in part for part in actual), actual
    narrow = rows(text, len(run) - 1)
    assert ''.join(narrow) == text
    assert all(len(part) <= len(run) - 1 for part in narrow)


@pytest.mark.parametrize('kind', ('advance', 'left_ink', 'right_ink'))
def test_fit_uses_complete_measured_advance_and_ink_not_character_count(kind):
    class Wide(Metrics):
        def measure(self, text, font_px):
            if text == '3日間、':
                return {'advance': TextMeasurement(200, 0, -8, 40, 2),
                        'left_ink': TextMeasurement(40, -160, -8, 40, 2),
                        'right_ink': TextMeasurement(40, 0, -8, 200, 2)}[kind]
            return super().measure(text, font_px)
    actual = rows('3日間、', 4, Wide())
    assert ''.join(actual) == '3日間、' and len(actual) > 1
    assert all(lm._width(Wide().measure(part, 10)) <= 40 for part in actual)


@pytest.mark.parametrize('width', (2, 3, 4, 5))
def test_overwide_duration_can_still_break_without_text_loss(width):
    text = '123456789０日間、'
    actual = rows(text, width)
    assert ''.join(actual).encode() == text.encode()
    assert all(len(part) <= width for part in actual)
    assert not any(part.startswith('、') for part in actual)


@pytest.mark.parametrize('text', (
    'ID3日間、', 'Ａ3日間、', '1.3日間、', '１．３日間、', '-3日間、', '1/3日間、',
    '3日間隔', '3日間2', '3日', '三日間', '3 日間、', '3\t日間、', '3️⃣日間、',
))
def test_no_partial_identifier_decimal_unit_or_renderer_grapheme_hint(text):
    clusters = Metrics().graphemes(text)
    hints = lm._fitting_numeric_duration_breaks(clusters, size=10, width=300, metrics=Metrics())
    assert not any(hints)
    assert ''.join(rows(text, 6)) == text


def test_adjacent_durations_are_not_joined_across_written_connector():
    text = '前記。3日間と2週間を残したい。'
    actual = rows(text, 7)
    assert ''.join(actual) == text
    assert any('3日間' in part for part in actual)
    assert any('2週間' in part for part in actual)


def test_original_unicode_and_whitespace_are_neither_normalized_nor_trimmed():
    text = '🌿漢\U000e0100。\tこれから３日間、静かに過ごしたい。'
    actual = rows(text, 9)
    assert ''.join(actual).encode() == text.encode()
    assert any('３日間' in part for part in actual)
    assert any('漢\U000e0100' in part for part in actual)


ORACLE_TEXT = '文前3日間、後記'
# Full duration [2:5] plus required comma [5:6] fits at four graphemes.
PROTECTED = {3, 4}
SCRIPT_CUTS = {1, 4, 7}


@lru_cache(maxsize=None)
def partitions(width):
    out = []
    def visit(start, parts):
        if start == len(ORACLE_TEXT):
            out.append(tuple(parts))
            return
        for end in range(start + 1, min(len(ORACLE_TEXT), start + width) + 1):
            if end < len(ORACLE_TEXT) and ORACLE_TEXT[end] == '、':
                continue
            visit(end, parts + [ORACLE_TEXT[start:end]])
    visit(0, [])
    return tuple(out)


def oracle_score(parts, width):
    cuts = set(itertools.accumulate(map(len, parts[:-1])))
    cohesion = (len(cuts & PROTECTED) + sum(len(p) == 1 for p in parts)) if width >= 4 else 0
    return (cohesion, len(parts), 0, len(cuts & SCRIPT_CUTS), 0, 0, 0,
            sum(((width - len(part)) * 10) ** 2 for part in parts))


@pytest.mark.parametrize('width', (2, 3, 4, 5, 6))
@pytest.mark.parametrize('budget', (1, 2, 3, 4))
def test_capacity_constrained_layout_matches_independent_partition_oracle(width, budget):
    legal = [p for p in partitions(width) if len(p) <= budget]
    if not legal:
        with pytest.raises(ValueError, match='unbreakable_line'):
            lm._wrap_solutions(ORACLE_TEXT, size=10, width=width * 10, metrics=Metrics(),
                               max_lines=budget, line_height=16)
        return
    results = lm._wrap_solutions(ORACLE_TEXT, size=10, width=width * 10, metrics=Metrics(),
                                 max_lines=budget, line_height=16)
    score, measured = min(results.values(), key=lambda row: row[0])
    actual = [part for part, _ in measured]
    assert ''.join(actual) == ORACLE_TEXT
    assert score == oracle_score(actual, width) == min(oracle_score(p, width) for p in legal)


@pytest.mark.parametrize('budget', (4, 5, 6))
def test_shared_vertical_budget_can_trade_soft_cohesion_without_shrinking(budget):
    legal = [(a, b) for a in partitions(5) for b in partitions(5) if len(a) + len(b) <= budget]
    expected = min(tuple(x + y for x, y in zip(oracle_score(a, 5), oracle_score(b, 5), strict=True))
                   for a, b in legal)
    groups = lm._fit_measured_groups([ORACLE_TEXT, ORACLE_TEXT], size=10, width=50,
        line_height=16, gap=10.4, available_height=budget * 16 + 10.4, metrics=Metrics())
    assert groups is not None
    actual = [[part for part, _ in group] for group in groups]
    assert [''.join(parts) for parts in actual] == [ORACLE_TEXT, ORACLE_TEXT]
    assert sum(map(len, actual)) <= budget
    assert tuple(x + y for x, y in zip(oracle_score(actual[0], 5), oracle_score(actual[1], 5), strict=True)) == expected


@pytest.mark.parametrize('ratio', ('4:5', '9:16'))
@pytest.mark.parametrize('duration', ('3日間', '２週間'))
def test_live_cmee_candidate_text_recipe_and_reservations_are_not_rewritten(ratio, duration):
    text = ('これからは、私が大切にしたいのは、朝に窓辺で葉の形をゆっくり眺める時間です。'
            'ただ、これから' + duration + '、続けるかはまだ決めていない。')
    source = PieceSourceSnapshot('synthetic-owner', 'numeric-duration-layout', '1', text)
    candidate = generate_piece_candidate(source, authenticated_owner_id=source.owner_id)
    recipe = build_visual_recipe(candidate['format_type'], tier='premium', aspect_ratio=ratio)
    before = deepcopy((candidate, recipe))
    layout = lm.build_measured_layout(candidate, recipe, canonical_sha256_hex(recipe), Metrics())
    assert (candidate, recipe) == before
    blocks = candidate['content_payload']['body_blocks']
    assert [''.join(row['text'] for row in layout['lines'] if row['block_index'] == i)
            for i in range(len(blocks))] == blocks
    assert any(duration in row['text'] for row in layout['lines'])
    assert layout['piece_text_hash'] == candidate['piece_text_hash']
    assert layout['visual_recipe_hash'] == canonical_sha256_hex(recipe)
    assert layout['font_px'] >= layout['font_floor_px']
    assert not layout['native_device_verified'] and not layout['clipped']
    assert layout['record_effect'] == layout['quota_effect'] == 0
