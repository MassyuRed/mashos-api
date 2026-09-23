"""Synthetic B9 gap/comma checks; no private source or native-image credit."""
from copy import deepcopy
import hashlib
import unicodedata

import pytest
import piece_v2_layout as lm
from piece_v2_contract import PieceContractError, canonical_sha256_hex
from piece_v2_visual import build_visual_recipe


class Metrics:
    profile_id = 'synthetic-gap-comma-not-native'

    def graphemes(self, text):
        # Only the explicit combining/selector fixtures below are exercised.
        result = []
        for char in text:
            if result and (unicodedata.combining(char) or 0xE0100 <= ord(char) <= 0xE01EF):
                result[-1] += char
            else:
                result.append(char)
        return result

    def measure(self, text, font_px):
        advance = len(self.graphemes(text)) * font_px
        return lm.TextMeasurement(advance, 0, -.8 * font_px, advance, .2 * font_px)


def wrap(text, width, metrics=None, **kwargs):
    metrics = metrics or Metrics()
    solutions = lm._wrap_solutions(text, size=10, width=width * 10,
                                  metrics=metrics, **kwargs)
    rows = min(solutions.values(), key=lambda item: item[0])[1]
    assert ''.join(part for part, _ in rows).encode('utf-8') == text.encode('utf-8')
    assert all(lm._width(measured) <= width * 10 for _, measured in rows)
    return [part for part, _ in rows]


@pytest.mark.parametrize('gap', ('  ', '   ', '\u3000\u3000', ' \u3000', '\t ', '\u00a0\u00a0'))
@pytest.mark.parametrize('left,right', (('甲乙', '丙丁'), ('AB', 'CD')))
def test_complete_gap_ends_the_previous_row_when_the_same_line_budget_allows_it(gap, left, right):
    text = left + gap + right
    actual = wrap(text, len(gap) + 2)
    assert actual == [left + gap, right]
    assert len(actual) == 2


@pytest.mark.parametrize('gap', ('  ', '\u3000 ', '\t\t'))
@pytest.mark.parametrize('prefix', ('は\u3099', '漢\U000e0100', 'A\u0301'))
def test_gap_preference_preserves_renderer_graphemes_and_raw_codepoints(gap, prefix):
    actual = wrap(prefix + '甲' + gap + '乙丙', 4)
    assert actual == [prefix + '甲' + gap, '乙丙']
    assert all(not unicodedata.combining(part[0]) for part in actual)


@pytest.mark.parametrize('text', ('甲乙丙,丁戊。', 'ABCD,EFG', 'カタログ,余白。'))
@pytest.mark.parametrize('width', (4, 5))
def test_ascii_comma_cannot_become_an_introduced_line_head(text, width):
    actual = wrap(text, width)
    assert all(not part.startswith(',') for part in actual[1:])


@pytest.mark.parametrize('punctuation', (',', ',」', ',）', ',、'))
def test_comma_and_following_existing_closers_are_measured_with_the_left_text(punctuation):
    text = '甲乙' + punctuation + '丙丁'
    actual = wrap(text, 2 + len(punctuation))
    assert any('乙' + punctuation in part for part in actual)


def test_source_initial_comma_and_source_initial_gap_are_not_deleted():
    assert wrap(',甲乙', 4) == [',甲乙']
    actual = wrap('  甲乙丙丁', 4)
    assert actual[0].startswith('  ')


def test_a_comma_without_a_fitting_left_grapheme_is_unavailable_not_a_partial_layout():
    with pytest.raises(PieceContractError, match='unbreakable_line'):
        wrap('A,B', 1)


@pytest.mark.parametrize('kind', ('advance', 'ink'))
def test_comma_fit_uses_renderer_advance_and_ink_extents(kind):
    class WideComma(Metrics):
        def measure(self, text, font_px):
            normal = super().measure(text, font_px)
            if ',' in text:
                if kind == 'advance':
                    return lm.TextMeasurement(normal.advance + 10, 0, -8, normal.right, 2)
                return lm.TextMeasurement(normal.advance, -10, -8, normal.right, 2)
            return normal
    actual = wrap('AB,CD', 4, WideComma())
    assert all(not part.startswith(',') for part in actual[1:])


@pytest.mark.parametrize('max_lines', (None, 4))
def test_overwide_gap_remains_breakable_without_trimming_or_refusal(max_lines):
    text = 'A' + ' ' * 9 + 'B'
    actual = wrap(text, 3, max_lines=max_lines)
    assert len(actual) == 4
    assert any(a.endswith(' ') and b.startswith(' ') for a, b in zip(actual, actual[1:]))


def test_vertical_budget_can_require_a_split_inside_a_short_gap():
    actual = wrap('AB  CD', 3, max_lines=2, line_height=10)
    assert actual == ['AB ', ' CD']
    with pytest.raises(PieceContractError, match='unbreakable_line'):
        wrap('AB  CD', 3, max_lines=1, line_height=10)


@pytest.mark.parametrize('text,width,expected', (
    ('AB CD', 3, ['AB', ' CD']),
    ('甲乙丙丁。', 5, ['甲乙丙丁。']),
    ('余白。写真を置く。', 6, ['余白。', '写真を置く。']),
    ('余白。この地図からは必要。', 7, ['余白。この地図', 'からは必要。']),
))
def test_unrelated_single_gap_and_existing_japanese_preferences_are_unchanged(text, width, expected):
    assert wrap(text, width) == expected


@pytest.mark.parametrize('ratio', ('4:5', '9:16'))
@pytest.mark.parametrize('theme', ('soft_paper', 'quiet_night'))
def test_full_layout_keeps_canonical_body_recipe_hash_and_zero_effects(ratio, theme):
    blocks = ['僕は、棚の本を  整理する時間を大切にしたい。',
              'まだ,毎朝続けられるとは限らない。']
    text = '\n\n'.join(blocks)
    payload = {'schema_version': 'piece.content_payload.v1', 'format_type': 'short_essay',
               'body_blocks': blocks, 'title': None, 'language': 'ja',
               'meaning_contract_version': 'piece.content_meaning.v1',
               'safety_contract_version': 'piece.public_safety_transformation.v1'}
    candidate = {'content_payload': payload, 'piece_text': text,
                 'piece_text_hash': hashlib.sha256(text.encode('utf-8')).hexdigest()}
    recipe = build_visual_recipe('short_essay', tier='premium', aspect_ratio=ratio, theme=theme)
    before = deepcopy((candidate, recipe))
    result = lm.build_measured_layout(candidate, recipe, canonical_sha256_hex(recipe), Metrics())
    assert (candidate, recipe) == before
    assert result['piece_text_hash'] == candidate['piece_text_hash']
    assert result['visual_recipe_hash'] == canonical_sha256_hex(recipe)
    assert [''.join(row['text'] for row in result['lines'] if row['block_index'] == i)
            for i in range(len(blocks))] == blocks
    assert all(not row['text'].startswith(',') for row in result['lines'])
    assert result['record_effect'] == result['quota_effect'] == 0
    assert result['native_device_verified'] is False
    assert result['clipped'] is result['missing_glyph'] is False


def test_unavailable_tab_glyph_is_not_erased_to_obtain_a_layout():
    class MissingTab(Metrics):
        def measure(self, text, font_px):
            m = super().measure(text, font_px)
            return lm.TextMeasurement(m.advance, m.left, m.top, m.right, m.bottom, '\t' not in text)
    with pytest.raises(PieceContractError, match='missing_glyph_or_metrics'):
        wrap('甲乙,\t丙丁', 4, MissingTab())


@pytest.mark.parametrize('gap_factor', (.25, .5))
def test_gap_choice_uses_proportional_renderer_measurements(gap_factor):
    class Proportional(Metrics):
        def measure(self, text, font_px):
            advance = sum(gap_factor if c.isspace() else 1 for c in self.graphemes(text)) * font_px
            return lm.TextMeasurement(advance, 0, -8, advance, 2)
    assert wrap('AB  CD', 3, Proportional()) == ['AB  ', 'CD']
