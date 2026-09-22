"""Synthetic B9 long-kana cohesion; no private replay text or native credit.

The small partition oracle uses hand-marked boundary positions and enumerates
legal partitions. It does not call a production hint helper or dynamic program.
"""
from copy import deepcopy
from functools import lru_cache
import hashlib
import itertools
import unicodedata

import pytest
import piece_v2_layout as lm
from piece_v2_layout import TextMeasurement
from piece_v2_contract import canonical_sha256_hex
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate
from piece_v2_visual import build_visual_recipe


class Metrics:
    profile_id = 'synthetic-long-kana-not-native'

    def graphemes(self, text):
        # Test fixture for the exercised marks, not a production UAX29 parser.
        result = []
        for c in text:
            if result and (unicodedata.combining(c) or 0xE0100 <= ord(c) <= 0xE01EF):
                result[-1] += c
            else:
                result.append(c)
        return result

    def measure(self, text, font_px):
        width = len(self.graphemes(text)) * font_px
        return TextMeasurement(width, 0, -font_px * .8, width, font_px * .2)


def rows(text, width, metrics=None):
    return [part for part, _ in lm._wrap(text, size=10, width=width * 10,
                                       metrics=metrics or Metrics())]


def boundaries(parts, metrics=None):
    metrics = metrics or Metrics()
    return set(itertools.accumulate(len(metrics.graphemes(p)) for p in parts[:-1]))


@pytest.mark.parametrize('written', (
    '苦手ではなかったかもしれない。', '大切にしていた。',
    '相談をしてみたい。', 'メモをなくしたくない。',
    '写真があまり', '書いたことがある。',
))
@pytest.mark.parametrize('extra_width', (0, 2))
def test_complete_fitting_written_tail_is_not_split(written, extra_width):
    text = '余白。' + written + '後記。'
    width = len(written) + extra_width
    actual = rows(text, width)
    assert ''.join(actual) == text
    assert any(written in part for part in actual), actual


@pytest.mark.parametrize('normalization', ('NFC', 'NFD'))
@pytest.mark.parametrize('prefix', ('', '🌱', '漢\U000e0100'))
def test_raw_combining_and_non_bmp_graphemes_remain_intact(normalization, prefix):
    run = unicodedata.normalize(normalization, '好きではなかった。')
    text = prefix + '余白。' + run + '後記。'
    actual = rows(text, len(Metrics().graphemes(run)) + 1)
    assert ''.join(actual).encode() == text.encode()
    assert any(run in part for part in actual)
    assert all(not unicodedata.combining(part[0]) for part in actual)


@pytest.mark.parametrize('left,right', (('「', '」'), ('（', '）'), ('', '。')))
def test_required_punctuation_is_part_of_complete_run_fit(left, right):
    text = '前。' + left + '必要かもしれない' + right + '後。'
    run = left + '必要かもしれない' + right
    actual = rows(text, len(run))
    assert ''.join(actual) == text
    assert any(run in part for part in actual)
    narrower = rows(text, len(run) - 1)
    assert ''.join(narrower) == text
    assert all(len(part) <= len(run) - 1 for part in narrower)
    assert not any(run in part for part in narrower)


@pytest.mark.parametrize('kind', ('advance', 'overhang'))
def test_complete_run_measurement_not_character_width_sum(kind):
    class WideRun(Metrics):
        def measure(self, text, font_px):
            result = super().measure(text, font_px)
            if text == '必要かもしれない。':
                if kind == 'advance':
                    return TextMeasurement(500, 0, -8, 100, 2)
                return TextMeasurement(100, -400, -8, 100, 2)
            return result
    text = '必要かもしれない。'
    actual = rows(text, len(text), WideRun())
    assert ''.join(actual) == text
    assert len(actual) > 1
    assert all(lm._width(WideRun().measure(p, 10)) <= len(text) * 10 for p in actual)


@pytest.mark.parametrize('width', (5, 7, 9))
def test_existing_determiner_scope_is_not_extended(width):
    text = '余白。この地図からは必要。'
    expected = (['余白。', 'この地図か', 'らは必要。'] if width == 5
                else ['余白。この地図', 'からは必要。'])
    assert rows(text, width) == expected


@pytest.mark.parametrize('text,width,expected', (
    ('余白。写真を置く。', 6, ['余白。', '写真を置く。']),
    ('余白。ひらがなだけ。', 7, ['余白。ひら', 'がなだけ。']),
))
def test_short_or_unattached_kana_keeps_previous_preferences(text, width, expected):
    assert rows(text, width) == expected


ORACLE_TEXT = '前。苦手ではない。後。'
# Positions are in renderer graphemes. The complete tail with its required
# period occupies [2:9] and therefore fits exactly at width seven.
PROTECTED = {3, 4, 5, 6, 7}
SCRIPT_SPLITS = {3}
KANA_SPLITS = {4, 5, 6, 7}
HEAD_ORPHANS = {3, 10}


@lru_cache(maxsize=None)
def partitions(width):
    text = ORACLE_TEXT
    out = []
    def visit(start, result):
        if start == len(text):
            out.append(tuple(result))
            return
        for end in range(start + 1, min(len(text), start + width) + 1):
            if end < len(text) and text[end] == '。':
                continue
            visit(end, result + [text[start:end]])
    visit(0, [])
    return tuple(out)


def oracle_score(parts, width):
    cuts = boundaries(parts)
    active = width >= 7
    primary = (len(cuts & PROTECTED) + sum(len(p) == 1 for p in parts)
               + len(cuts & HEAD_ORPHANS)) if active else 0
    return (primary, len(parts), 0, len(cuts & SCRIPT_SPLITS),
            len(cuts & HEAD_ORPHANS), len(cuts & KANA_SPLITS), 0,
            sum(((width - len(p)) * 10) ** 2 for p in parts))


@pytest.mark.parametrize('width', (3, 5, 6, 7, 8, 9))
@pytest.mark.parametrize('budget', (2, 3, 4, 5))
def test_capacity_constrained_result_matches_independent_partition_oracle(width, budget):
    legal = [p for p in partitions(width) if len(p) <= budget]
    if not legal:
        with pytest.raises(ValueError, match='unbreakable_line'):
            lm._wrap_solutions(ORACLE_TEXT, size=10, width=width * 10,
                               metrics=Metrics(), max_lines=budget, line_height=16)
        return
    solutions = lm._wrap_solutions(ORACLE_TEXT, size=10, width=width * 10,
                                  metrics=Metrics(), max_lines=budget, line_height=16)
    score, measured = min(solutions.values(), key=lambda x: x[0])
    actual = [s for s, _ in measured]
    assert ''.join(actual) == ORACLE_TEXT
    assert score == oracle_score(actual, width) == min(oracle_score(p, width) for p in legal)


@pytest.mark.parametrize('budget', (4, 5, 6, 7, 8))
def test_shared_paragraph_budget_keeps_same_cohesion_objective(budget):
    width = 7
    legal = [(a, b) for a in partitions(width) for b in partitions(width)
             if len(a) + len(b) <= budget]
    expected = min(tuple(x + y for x, y in zip(oracle_score(a, width),
                   oracle_score(b, width), strict=True)) for a, b in legal)
    groups = lm._fit_measured_groups([ORACLE_TEXT, ORACLE_TEXT], size=10,
        width=70, line_height=16, gap=10.4, available_height=budget * 16 + 10.4,
        metrics=Metrics())
    assert groups is not None
    actual = [[part for part, _ in group] for group in groups]
    assert [''.join(p) for p in actual] == [ORACLE_TEXT, ORACLE_TEXT]
    assert sum(map(len, actual)) <= budget
    assert tuple(x + y for x, y in zip(oracle_score(actual[0], width),
                 oracle_score(actual[1], width), strict=True)) == expected


def test_long_tail_does_not_move_the_cut_to_a_sentence_head_orphan():
    text = '前。苦手ではない。後。'
    actual = rows(text, 7)
    assert not (boundaries(actual) & HEAD_ORPHANS), actual
    assert any('苦手ではない。' in p for p in actual)


@pytest.mark.parametrize('ratio', ('4:5', '9:16'))
@pytest.mark.parametrize('normalization', ('NFC', 'NFD'))
def test_existing_cmee_candidate_recipe_hash_and_exact_body_are_unchanged(ratio, normalization):
    # The existing source grammar admits raw target text, not a normalized
    # spelling of every structural particle/predicate. Exercise its actual
    # admitted boundary; full NFD tails are tested directly in rows() above.
    target = unicodedata.normalize(normalization, '机で紙を折る時間')
    text = ('僕は' + target + 'があまり好きではなかったかもしれない。'
            'まだ、毎日続けられるとは限らない。')
    candidate = generate_piece_candidate(PieceSourceSnapshot('synthetic', 'long-tail', '1', text),
                                         authenticated_owner_id='synthetic')
    recipe = build_visual_recipe(candidate['format_type'], tier='premium', aspect_ratio=ratio)
    original = deepcopy((candidate, recipe))
    layout = lm.build_measured_layout(candidate, recipe, canonical_sha256_hex(recipe), Metrics())
    body = candidate['piece_text']
    blocks = candidate['content_payload']['body_blocks']
    assert [''.join(l['text'] for l in layout['lines'] if l['block_index'] == i)
            for i in range(len(blocks))] == blocks
    assert original == (candidate, recipe)
    assert layout['piece_text_hash'] == hashlib.sha256(body.encode()).hexdigest()
    assert layout['visual_recipe_hash'] == canonical_sha256_hex(recipe)
    assert any('好きではなかったかもしれない。' in l['text'] for l in layout['lines'])
    assert any('あまり' in l['text'] for l in layout['lines'])
    assert layout['font_px'] >= layout['font_floor_px']
    assert not layout['clipped'] and not layout['missing_glyph']
    assert not layout['native_device_verified'] and not candidate['production_enabled']
    assert layout['record_effect'] == layout['quota_effect'] == 0
    for line in layout['lines']:
        a, b, c, d = line['ink_box']
        assert layout['margin'] <= a <= c <= layout['width'] - layout['margin']
        assert layout['margin'] <= b <= d <= layout['height'] - layout['margin'] - layout['branding_zone']
    assert 'lines' not in lm.fit_summary(layout)


def test_full_nfd_source_grammar_is_not_silently_expanded_by_layout():
    text = unicodedata.normalize('NFD',
        '僕は机で紙を折る時間があまり好きではなかったかもしれない。'
        'まだ、毎日続けられるとは限らない。')
    with pytest.raises(ValueError, match='expression_meaning_not_admitted'):
        generate_piece_candidate(PieceSourceSnapshot('synthetic', 'nfd-source', '1', text),
                                 authenticated_owner_id='synthetic')
