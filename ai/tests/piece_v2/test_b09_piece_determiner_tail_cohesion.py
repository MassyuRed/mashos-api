"""Synthetic B9 short-kana tail cohesion; no native or product acceptance.

The exhaustive oracle annotates boundaries by hand, independently of the
production hint functions. Direct layout fixtures do not claim CMEE admission.
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
    profile_id = 'synthetic-determiner-tail-not-native'

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
    wrapped = lm._wrap(text, size=10, width=columns * 10, metrics=metrics or Metrics())
    assert ''.join(line for line, _ in wrapped) == text
    for _, m in wrapped:
        assert max(m.advance, m.right) - min(0, m.left) <= columns * 10
    return [line for line, _ in wrapped]


@pytest.mark.parametrize('prefix', ('この', 'その', 'あの', 'どの'))
@pytest.mark.parametrize('head', ('地図', 'ノート'))
@pytest.mark.parametrize('tail,ending', (('が', '必要。'), ('を', '残す。'),
                                        ('には', '記す。'), ('では', '十分。')))
@pytest.mark.parametrize('delimiter', ('。', '、'))
def test_fitting_short_tail_stays_with_its_delimited_written_run(prefix, head, tail, ending, delimiter):
    phrase = prefix + head + tail
    text = '余白' + delimiter + phrase + ending
    # Prefer one readable extra row over detaching the short tail.
    result = rows(text, len(phrase + ending) - 1)
    assert len(result) == 3
    assert any(phrase in line for line in result)


def partitions(text, width):
    if not text:
        yield []
    for end in range(1, min(width, len(text)) + 1):
        if end < len(text) and text[end] == '。':
            continue
        for suffix in partitions(text[end:], width):
            yield [text[:end]] + suffix


def oracle_score(parts, width):
    # 海辺。その記録が残る。 : [3,7) original run; [3,8) with short tail.
    cuts = set(itertools.accumulate(map(len, parts[:-1])))
    protected = {4, 5, 6, 7} if width >= 5 else {4, 5, 6} if width >= 4 else set()
    return ((len(cuts & protected) + sum(len(p) == 1 for p in parts)) if protected else 0,
            len(parts), 0, len(cuts & {1, 6}), int(4 in cuts), len(cuts & {7, 9}), 0,
            sum(((width - len(p)) * 10) ** 2 for p in parts))


@pytest.mark.parametrize('width', (3, 4, 5, 6, 7, 8))
@pytest.mark.parametrize('budget', (1, 2, 3, 4))
def test_all_constrained_paths_match_an_independent_tail_partition_oracle(width, budget):
    text = '海辺。その記録が残る。'
    expected = [oracle_score(p, width) for p in partitions(text, width) if len(p) <= budget]
    if not expected:
        with pytest.raises(ValueError, match='unbreakable_line'):
            lm._wrap_solutions(text, size=10, width=width * 10, metrics=Metrics(),
                               max_lines=budget, line_height=16)
        return
    choices = lm._wrap_solutions(text, size=10, width=width * 10, metrics=Metrics(),
                                 max_lines=budget, line_height=16)
    score, actual = min(choices.values(), key=lambda item: item[0])
    assert ''.join(p for p, _ in actual) == text
    assert score == oracle_score([p for p, _ in actual], width) == min(expected)


@lru_cache(None)
def template():
    source = PieceSourceSnapshot('synthetic-owner', 'synthetic-tail-layout', '1',
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
def test_shared_capacity_keeps_best_attainable_tail_cohesion_without_shrinking(monkeypatch, width, budget):
    blocks = [f'前書き。{prefix}地図が必要。' for prefix in ('この', 'その', 'あの')]
    candidate, recipe = fixture(blocks)
    original = deepcopy(candidate), deepcopy(recipe)
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
    assert (candidate, recipe) == original
    assert [''.join(g) for g in groups] == blocks
    cuts = sum(len(set(itertools.accumulate(map(len, g[:-1]))) & {5, 6, 7, 8}) for g in groups)
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


@pytest.mark.parametrize('text,part', (
    ('余白。この地図が必要。', 'この地図が'),
    ('余白。この地図か\u3099必要。', 'この地図か\u3099'),
    ('余白。この地\U000e0100図が必要。', 'この地\U000e0100図が'),
    ('余白。と\u3099の地図には記す。', 'と\u3099の地図には'),
))
def test_original_graphemes_and_scalar_bytes_are_not_normalized(text, part):
    result = rows(text, len(Metrics().graphemes(part)) + 2)
    assert any(part in line for line in result)
    valid = set(itertools.accumulate(map(len, Metrics().graphemes(text))))
    assert set(itertools.accumulate(map(len, result))) <= valid


@pytest.mark.parametrize('overhang', (0, 3, 10))
def test_expanded_tail_uses_actual_nonadditive_width_and_ink_overhang(overhang):
    class Proportional(Metrics):
        def measure(self, text, size):
            advance = (len(self.graphemes(text)) - text.count('地図') / 2) * size
            return TextMeasurement(advance, -overhang, -.8 * size, advance + overhang, .2 * size)
    result = rows('余白。この地図が必要。', 7.5 + 2 * overhang / 10, Proportional())
    assert any('この地図が' in line for line in result)


@pytest.mark.parametrize('width', (4, 5, 6))
def test_overwide_tail_and_required_punctuation_keep_original_determiner_preference(width):
    # The tail plus full stop needs seven columns, even though the base run fits.
    text = '前書き。この地図には。'
    result = rows(text, width)
    assert any('この地図' in line for line in result)
    assert not any('この地図には' in line for line in result)
    assert all(not line.startswith('。') for line in result)


@pytest.mark.parametrize('text,word', (
    ('机で手紙を読む。その記録が必要。', '読む'),
    ('駅で切符を買う。この切符が必要。', '買う'),
    ('資料を机に置く。この資料が必要。', '置く'),
))
def test_cohesion_does_not_move_the_cut_into_another_fitting_short_ending(text, word):
    result = rows(text, 7)
    assert len(result) == 4
    assert any(word in line for line in result)
    assert any(phrase in line for line in result for phrase in ('その記録が', 'この切符が', 'この資料が'))


@pytest.mark.parametrize('text,width,expected', (
    ('きのこの地図が必要。', 5, ['きのこの地', '図が必要。']),
    ('きのこの地図が必要。', 7, ['きのこの', '地図が必要。']),
    ('きのこの地図が必要。', 9, ['きのこの', '地図が必要。']),
    ('余白。このひとが必要。', 5, ['余白。', 'このひと', 'が必要。']),
    ('余白。このひとが必要。', 7, ['余白。この', 'ひとが必要。']),
    ('余白。このひとが必要。', 9, ['余白。この', 'ひとが必要。']),
    ('余白。この地図からは必要。', 5, ['余白。', 'この地図か', 'らは必要。']),
    ('余白。この地図からは必要。', 7, ['余白。この地図', 'からは必要。']),
    ('余白。この地図からは必要。', 9, ['余白。この地図', 'からは必要。']),
    ('余白。この地図、が必要。', 5, ['余白。', 'この地図、', 'が必要。']),
    ('余白。この地図、が必要。', 7, ['余白。', 'この地図、', 'が必要。']),
    ('余白。この地図、が必要。', 9, ['余白。この地図、', 'が必要。']),
    ('余白。この地図 が必要。', 5, ['余白。', 'この地図', ' が必要。']),
    ('余白。この地図 が必要。', 7, ['余白。この地図', ' が必要。']),
    ('余白。この地図 が必要。', 9, ['余白。この地図', ' が必要。']),
))
def test_ineligible_prefix_long_kana_and_separators_keep_previous_layout(text, width, expected):
    assert rows(text, width) == expected


def neighboring_ending_score(parts, width):
    # 机で手紙を読む。その記録が必要。 Hand-marked complete written runs.
    cuts = set(itertools.accumulate(map(len, parts[:-1])))
    protected = ({1, 3, 4, 6, 9, 10, 11, 12} if width >= 5
                 else {9, 10, 11} if width >= 4 else set())
    return ((len(cuts & protected) + sum(len(p) == 1 for p in parts)) if protected else 0,
            len(parts), 0, len(cuts & {3, 11, 14}), int(9 in cuts),
            len(cuts & {1, 4, 6, 12}), 0,
            sum(((width - len(p)) * 10) ** 2 for p in parts))


@pytest.mark.parametrize('width', (4, 5, 7, 8))
@pytest.mark.parametrize('budget', (2, 3, 4, 5))
def test_neighboring_endings_remain_soft_under_an_exhaustive_capacity_oracle(width, budget):
    text = '机で手紙を読む。その記録が必要。'
    expected = [neighboring_ending_score(p, width) for p in partitions(text, width) if len(p) <= budget]
    if not expected:
        with pytest.raises(ValueError, match='unbreakable_line'):
            lm._wrap_solutions(text, size=10, width=width * 10, metrics=Metrics(),
                               max_lines=budget, line_height=16)
        return
    choices = lm._wrap_solutions(text, size=10, width=width * 10, metrics=Metrics(),
                                 max_lines=budget, line_height=16)
    score, actual = min(choices.values(), key=lambda item: item[0])
    assert ''.join(p for p, _ in actual) == text
    assert score == neighboring_ending_score([p for p, _ in actual], width) == min(expected)
