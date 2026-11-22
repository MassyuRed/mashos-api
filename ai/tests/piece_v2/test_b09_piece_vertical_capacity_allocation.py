"""Synthetic B9 line-budget checks; no saved input, device or product credit.

The independent oracle enumerates legal partitions of short hand-annotated
strings. It does not call the layout scorer, hint builder or dynamic program.
"""
from copy import deepcopy
from functools import lru_cache
import hashlib
import itertools
import math
import unicodedata

import pytest

import piece_v2_layout as layout_module
from piece_v2_layout import TextMeasurement, build_measured_layout, fit_summary
from piece_v2_contract import canonical_sha256_hex
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate
from piece_v2_visual import build_visual_recipe


class Metrics:
    profile_id = 'synthetic-shared-line-budget-not-native'

    def graphemes(self, text):
        result = []
        for char in text:
            if result and (unicodedata.combining(char) or 0xE0100 <= ord(char) <= 0xE01EF):
                result[-1] += char
            else:
                result.append(char)
        return result

    def measure(self, text, font_px):
        advance = len(self.graphemes(text)) * font_px
        return TextMeasurement(advance, 0, -font_px * .8, advance, font_px * .2)


@lru_cache(None)
def base_candidate():
    source = PieceSourceSnapshot('synthetic-owner', 'synthetic-line-budget', '1',
        '私は机で下書きを読み返す時間を大切にしたい。まだ、毎日続けられるとは限らない。')
    return generate_piece_candidate(source, authenticated_owner_id=source.owner_id)


def fixture(blocks, fmt='short_essay'):
    # These are pure layout fixtures, not newly admitted CMEE source records.
    c = deepcopy(base_candidate())
    c['format_type'] = c['content_payload']['format_type'] = fmt
    c['content_payload']['body_blocks'] = list(blocks)
    c['piece_text'] = '\n\n'.join(blocks)
    c['piece_text_hash'] = hashlib.sha256(c['piece_text'].encode()).hexdigest()
    r = build_visual_recipe(fmt, tier='premium', aspect_ratio='9:16')
    return c, r


def set_capacity(monkeypatch, *, columns, lines, block_count, slack=0, sizes=None):
    original = layout_module.resolve_visual
    def surface(recipe):
        v = original(recipe)
        top_size = v['font_sizes'][0]
        lh = math.ceil(top_size * v['line_height_ratio'])
        v['width'] = 2 * v['margin'] + columns * top_size
        v['height'] = (2 * v['margin'] + v['branding_zone'] + lines * lh
                       + (block_count - 1) * lh * v['paragraph_spacing_ratio'] + slack)
        v['font_sizes'] = sizes or [top_size]
        return v
    monkeypatch.setattr(layout_module, 'resolve_visual', surface)


def assert_exact(c, r, result, before):
    assert (c, r) == before
    blocks = c['content_payload']['body_blocks']
    rows = [[line['text'] for line in result['lines'] if line['block_index'] == i]
            for i in range(len(blocks))]
    assert [''.join(group) for group in rows] == blocks
    assert result['piece_text_hash'] == c['piece_text_hash']
    assert result['visual_recipe_hash'] == canonical_sha256_hex(r)
    assert not result['clipped'] and not result['missing_glyph'] and not result['native_device_verified']
    assert result['record_effect'] == result['quota_effect'] == 0
    assert 'lines' not in fit_summary(result)
    assert [line['block_index'] for line in result['lines']] == sorted(line['block_index'] for line in result['lines'])
    for line in result['lines']:
        left, top, right, bottom = line['ink_box']
        assert result['margin'] <= left <= right <= result['width'] - result['margin']
        assert result['margin'] <= top <= bottom <= result['height'] - result['margin'] - result['branding_zone']
    return rows


# Each 9-scalar fixture has one hand-annotated fitting run [2,6), a required
# full stop at 6, kana attachments at 3/5, and the short-kana bridge at 4.
WORDS = ('読み返す', '書き直す', '落ち着く')
BLOCKS = tuple('あい' + word + '。まだ' for word in WORDS)


def score(parts, text, width, font_px):
    points = set(itertools.accumulate(map(len, parts[:-1])))
    starts = range(0, len(text), 9)
    fitting = width >= 5
    run_cuts = {offset + i for offset in starts for i in (3, 4, 5)}
    kana_cuts = {offset + i for offset in starts for i in (3, 5)}
    bridge_cuts = {offset + 4 for offset in starts}
    cohesion = (len(points & run_cuts) + sum(len(part) == 1 for part in parts)) if fitting else 0
    return (cohesion, len(parts), 0, 0,
            sum(i >= 2 and text[i-2] == '。' for i in points),
            len(points & kana_cuts), len(points & bridge_cuts),
            sum(((width - len(part)) * font_px) ** 2 for part in parts))


@lru_cache(None)
def oracle_frontier(text, width, font_px):
    best = {}
    def visit(start, parts):
        if start == len(text):
            value = score(parts, text, width, font_px)
            count = len(parts)
            if count not in best or value < best[count]:
                best[count] = value
            return
        for end in range(start+1, min(len(text), start+width)+1):
            if end < len(text) and text[end] == '。':
                continue
            visit(end, parts + [text[start:end]])
    visit(0, [])
    return best


@pytest.mark.parametrize('width', (4, 5, 6))
@pytest.mark.parametrize('budget', (6, 7, 8, 9))
@pytest.mark.parametrize('reversed_blocks', (False, True))
def test_global_capacity_matches_independent_partition_oracle(monkeypatch, width, budget, reversed_blocks):
    blocks = BLOCKS[::-1] if reversed_blocks else BLOCKS
    c, r = fixture(blocks)
    before = deepcopy(c), deepcopy(r)
    set_capacity(monkeypatch, columns=width, lines=budget, block_count=3)
    frontiers = [oracle_frontier(b, width, 52) for b in blocks]
    legal = [tuple(sum(items) for items in zip(*costs))
             for costs in itertools.product(*(f.values() for f in frontiers))
             if sum(cost[1] for cost in costs) <= budget]
    if not legal:
        with pytest.raises(ValueError, match='font_floor_overflow'):
            build_measured_layout(c, r, canonical_sha256_hex(r), Metrics())
        return
    out = build_measured_layout(c, r, canonical_sha256_hex(r), Metrics())
    groups = assert_exact(c, r, out, before)
    actual = tuple(sum(items) for items in zip(*(score(g, b, width, 52) for g, b in zip(groups, blocks))))
    assert actual == min(legal)
    assert out['font_px'] == 52


@pytest.mark.parametrize('width', (4, 5, 6))
@pytest.mark.parametrize('budget', (4, 5, 6))
def test_intermediate_single_paragraph_budget_keeps_best_attainable_cohesion(monkeypatch, width, budget):
    text = BLOCKS[0] + BLOCKS[1]
    c, r = fixture((text,), fmt='quote')
    before = deepcopy(c), deepcopy(r)
    set_capacity(monkeypatch, columns=width, lines=budget, block_count=1)
    legal = [cost for count, cost in oracle_frontier(text, width, 80).items() if count <= budget]
    if not legal:
        with pytest.raises(ValueError, match='font_floor_overflow'):
            build_measured_layout(c, r, canonical_sha256_hex(r), Metrics())
        return
    out = build_measured_layout(c, r, canonical_sha256_hex(r), Metrics())
    groups = assert_exact(c, r, out, before)
    assert score(groups[0], text, width, 80) == min(legal)
    assert out['font_px'] == 80


@pytest.mark.parametrize('slack,expected', ((-.01, 6), (0, 7), (.01, 7)))
def test_actual_paragraph_gaps_and_fractional_capacity_are_not_rounded_up(monkeypatch, slack, expected):
    c, r = fixture(BLOCKS)
    before = deepcopy(c), deepcopy(r)
    set_capacity(monkeypatch, columns=5, lines=7, block_count=3, slack=slack)
    out = build_measured_layout(c, r, canonical_sha256_hex(r), Metrics())
    assert_exact(c, r, out, before)
    assert len(out['lines']) == expected
    assert out['font_px'] == 52


@pytest.mark.parametrize('variant', ('plain', 'combining', 'variation'))
def test_partial_reflow_preserves_renderer_graphemes(monkeypatch, variant):
    text = BLOCKS[0]
    if variant == 'combining':
        text = text.replace('読み', '泳き\u3099')
    elif variant == 'variation':
        text = text.replace('読', '読\U000E0100')
    c, r = fixture((text, BLOCKS[1], BLOCKS[2]))
    before = deepcopy(c), deepcopy(r)
    set_capacity(monkeypatch, columns=5, lines=7, block_count=3)
    out = build_measured_layout(c, r, canonical_sha256_hex(r), Metrics())
    groups = assert_exact(c, r, out, before)
    assert len(out['lines']) == 7
    for group, body in zip(groups, c['content_payload']['body_blocks']):
        cuts = set(itertools.accumulate(map(len, group)))
        assert cuts <= set(itertools.accumulate(map(len, Metrics().graphemes(body))))


def test_measured_ink_height_is_a_path_constraint_not_a_blanket_refusal(monkeypatch):
    class Tall(Metrics):
        def measure(self, text, font_px):
            m = super().measure(text, font_px)
            height = 2 * font_px if len(self.graphemes(text)) >= 5 else font_px
            return TextMeasurement(m.advance, 0, -height * .8, m.right, height * .2)
    text = BLOCKS[0] + BLOCKS[1]
    c, r = fixture((text,), fmt='quote')
    before = deepcopy(c), deepcopy(r)
    set_capacity(monkeypatch, columns=5, lines=6, block_count=1)
    out = build_measured_layout(c, r, canonical_sha256_hex(r), Tall())
    assert_exact(c, r, out, before)
    assert all(len(line['text']) < 5 for line in out['lines'])
    assert out['font_px'] == 80


@pytest.mark.parametrize('budget', (1, 2, 3, 4, 5))
def test_no_fitting_budget_does_not_truncate_or_authorize_save(monkeypatch, budget):
    c, r = fixture(BLOCKS)
    before = deepcopy(c), deepcopy(r)
    set_capacity(monkeypatch, columns=5, lines=budget, block_count=3)
    with pytest.raises(ValueError, match='font_floor_overflow'):
        build_measured_layout(c, r, canonical_sha256_hex(r), Metrics())
    assert (c, r) == before


@pytest.mark.parametrize('overhang', (0, 13, 52))
def test_constrained_paths_use_nonadditive_advance_and_real_overhang(monkeypatch, overhang):
    class Proportional(Metrics):
        def measure(self, text, font_px):
            advance = (len(self.graphemes(text)) - .5 * text.count('読み')) * font_px
            return TextMeasurement(advance, -overhang, -.8 * font_px, advance + overhang, .2 * font_px)
    c, r = fixture((BLOCKS[0],) * 3)
    before = deepcopy(c), deepcopy(r)
    set_capacity(monkeypatch, columns=4.5 + 2 * overhang / 52, lines=7, block_count=3)
    out = build_measured_layout(c, r, canonical_sha256_hex(r), Proportional())
    assert_exact(c, r, out, before)
    assert out['font_px'] == 52 and len(out['lines']) == 7
    assert any('読み返す。' == line['text'] for line in out['lines'])


def test_smaller_font_is_used_only_after_current_size_has_no_feasible_path(monkeypatch):
    c, r = fixture(BLOCKS)
    before = deepcopy(c), deepcopy(r)
    set_capacity(monkeypatch, columns=5, lines=5, block_count=3, sizes=[52, 48, 44, 40])
    out = build_measured_layout(c, r, canonical_sha256_hex(r), Metrics())
    assert_exact(c, r, out, before)
    assert out['font_px'] == 44
    assert len(out['lines']) == 6
