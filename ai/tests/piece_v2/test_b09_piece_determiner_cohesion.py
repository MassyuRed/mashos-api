"""Synthetic B9 determiner cohesion; no saved data or native/product credit.

Hand-annotated partitions below are an independent oracle, not calls to the
production hint builder or scorer. Layout fixture text is not CMEE admission.
"""
from copy import deepcopy
from functools import lru_cache
import hashlib
import itertools
import math
import unicodedata

import pytest

import piece_v2_layout as lm
from piece_v2_layout import TextMeasurement, build_measured_layout, fit_summary
from piece_v2_contract import canonical_sha256_hex
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate
from piece_v2_visual import build_visual_recipe


class Metrics:
    profile_id = 'synthetic-determiner-cohesion-not-native'

    def graphemes(self, text):
        clusters = []
        for char in text:
            if clusters and (unicodedata.combining(char) or 0xE0100 <= ord(char) <= 0xE01EF):
                clusters[-1] += char
            else:
                clusters.append(char)
        return clusters

    def measure(self, text, size):
        advance = len(self.graphemes(text)) * size
        return TextMeasurement(advance, 0, -.8 * size, advance, .2 * size)


def rows(text, columns, metrics=None):
    metrics = metrics or Metrics()
    wrapped = lm._wrap(text, size=10, width=columns * 10, metrics=metrics)
    assert ''.join(s for s, _ in wrapped) == text
    for _, measurement in wrapped:
        assert max(measurement.advance, measurement.right) - min(0, measurement.left) <= columns * 10
    return [s for s, _ in wrapped]


@pytest.mark.parametrize('prefix', ('この', 'その', 'あの', 'どの'))
@pytest.mark.parametrize('head', ('地図', 'ノート'))
@pytest.mark.parametrize('delimiter', ('。', '、', '！', ':', ' ', '「'))
def test_delimited_determiner_stays_with_a_measured_fitting_run(prefix, head, delimiter):
    closing = '」' if delimiter == '「' else ''
    text = '前置き' + delimiter + prefix + head + closing + 'を残す。'
    result = rows(text, 8)
    assert any(prefix + head in line for line in result)
    assert all(not line.startswith(('。', '、', '！', '」')) for line in result)
    assert all(not line.endswith('「') for line in result)


def oracle_score(parts, width):
    # 海辺。この記録。 : Han cuts=1,6; prefix run=[3,7); final 。 binds.
    cuts = set(itertools.accumulate(map(len, parts[:-1])))
    fit = width >= 5
    return ((len(cuts & {4, 5, 6}) + sum(len(p) == 1 for p in parts)) if fit else 0,
            len(parts), 0, len(cuts & {1, 6}), int(4 in cuts), 0, 0,
            sum(((width - len(p)) * 10) ** 2 for p in parts))


def partitions(text, width):
    if not text:
        yield []
    for end in range(1, min(width, len(text)) + 1):
        if end < len(text) and text[end] == '。':
            continue
        for suffix in partitions(text[end:], width):
            yield [text[:end]] + suffix


@pytest.mark.parametrize('width', (3, 4, 5, 6))
@pytest.mark.parametrize('budget', (1, 2, 3, 4))
def test_constrained_determiner_paths_match_independent_partition_oracle(width, budget):
    text = '海辺。この記録。'
    valid = [oracle_score(p, width) for p in partitions(text, width) if len(p) <= budget]
    if not valid:
        with pytest.raises(ValueError, match='unbreakable_line'):
            lm._wrap_solutions(text, size=10, width=width * 10,
                               metrics=Metrics(), max_lines=budget, line_height=16)
        return
    solutions = lm._wrap_solutions(text, size=10, width=width * 10,
                                   metrics=Metrics(), max_lines=budget, line_height=16)
    score, actual = min(solutions.values(), key=lambda item: item[0])
    parts = [p for p, _ in actual]
    assert ''.join(parts) == text
    assert oracle_score(parts, width) == min(valid)
    assert score == min(valid)


@lru_cache(None)
def template():
    source = PieceSourceSnapshot('synthetic-owner', 'synthetic-determiner', '1',
        '私は机で下書きを読み返す時間を大切にしたい。まだ、毎日続けられるとは限らない。')
    return generate_piece_candidate(source, authenticated_owner_id=source.owner_id)


def fixture(blocks):
    candidate = deepcopy(template())
    candidate['format_type'] = candidate['content_payload']['format_type'] = 'short_essay'
    candidate['content_payload']['body_blocks'] = list(blocks)
    candidate['piece_text'] = '\n\n'.join(blocks)
    candidate['piece_text_hash'] = hashlib.sha256(candidate['piece_text'].encode()).hexdigest()
    recipe = build_visual_recipe('short_essay', tier='premium', aspect_ratio='9:16')
    return candidate, recipe


@pytest.mark.parametrize('width', (6, 7))
@pytest.mark.parametrize('budget', (6, 7, 8, 9))
def test_global_capacity_keeps_the_best_attainable_prefix_cohesion(monkeypatch, width, budget):
    blocks = [f'前置き。{prefix}時間が大切。' for prefix in ('この', 'その', 'あの')]
    candidate, recipe = fixture(blocks)
    before = deepcopy(candidate), deepcopy(recipe)
    real_visual = lm.resolve_visual
    def visual(value):
        v = real_visual(value)
        size = v['font_sizes'][0]
        line_height = math.ceil(size * v['line_height_ratio'])
        v['width'] = 2 * v['margin'] + width * size
        v['height'] = (2 * v['margin'] + v['branding_zone'] + budget * line_height
                       + 2 * line_height * v['paragraph_spacing_ratio'])
        v['font_sizes'] = [size]
        return v
    monkeypatch.setattr(lm, 'resolve_visual', visual)
    out = build_measured_layout(candidate, recipe, canonical_sha256_hex(recipe), Metrics())
    groups = [[line['text'] for line in out['lines'] if line['block_index'] == i] for i in range(3)]
    assert (candidate, recipe) == before
    assert [''.join(group) for group in groups] == blocks
    # Each two-line paragraph must cut its prefix run; three lines avoid it.
    cuts = sum(len(set(itertools.accumulate(map(len, group[:-1]))) & {5, 6, 7}) for group in groups)
    assert cuts == 9 - budget
    assert len(out['lines']) == budget and out['font_px'] == 52
    assert out['piece_text_hash'] == candidate['piece_text_hash']
    assert out['visual_recipe_hash'] == canonical_sha256_hex(recipe)
    assert out['record_effect'] == out['quota_effect'] == 0
    assert not out['clipped'] and not out['missing_glyph'] and not out['native_device_verified']
    assert 'lines' not in fit_summary(out)
    for line in out['lines']:
        left, top, right, bottom = line['ink_box']
        assert out['margin'] <= left <= right <= out['width'] - out['margin']
        assert out['margin'] <= top <= bottom <= out['height'] - out['margin'] - out['branding_zone']


@pytest.mark.parametrize('text,expected', (
    ('きのこの時間。', ['きのこ', 'の時間。']),
    ('前置き。このひとを待つ。', ['前置き。', 'このひと', 'を待つ。']),
    ('前置き。この時間。', ['前置き。', 'この', '時間。']),
))
def test_noneligible_or_overwide_runs_keep_the_existing_freely_breakable_path(text, expected):
    # Four columns: この時間 plus its required full stop needs five.
    assert rows(text, 4) == expected


@pytest.mark.parametrize('text,part', (
    ('前置き。どの地図を残す。', 'どの地図'),
    ('前置き。と\u3099の地図を残す。', 'と\u3099の地図'),
    ('前置き。この地\U000e0100図を残す。', 'この地\U000e0100図'),
))
def test_renderer_graphemes_and_original_scalar_bytes_are_preserved(text, part):
    result = rows(text, 8)
    assert any(part in line for line in result)
    boundaries = set(itertools.accumulate(map(len, Metrics().graphemes(text))))
    assert set(itertools.accumulate(map(len, result))) <= boundaries


@pytest.mark.parametrize('overhang', (0, 3, 10))
def test_fit_decision_uses_actual_nonadditive_width_and_overhang(overhang):
    class Proportional(Metrics):
        def measure(self, text, size):
            advance = (len(self.graphemes(text)) - text.count('地図') / 2) * size
            return TextMeasurement(advance, -overhang, -.8 * size, advance + overhang, .2 * size)
    text = '前置き。この地図を残す。'
    result = rows(text, 7.5 + 2 * overhang / 10, Proportional())
    assert any('この地図' in line for line in result)
