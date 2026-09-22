"""Canonical kana comparison in B9; raw renderer/source bytes stay authoritative.

Public synthetic tests, not device acceptance or general word segmentation.
The partition oracle below uses explicit grapheme-boundary positions, not the
production hint functions or dynamic program.
"""
from copy import deepcopy
import itertools
import unicodedata

import pytest
import piece_v2_layout as lm
from piece_v2_contract import canonical_sha256_hex, validate_piece_text_binding
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate
from piece_v2_visual import build_visual_recipe


class Metrics:
    profile_id = 'synthetic-canonical-kana-not-device'

    def graphemes(self, text):
        # Only the combining sequences exercised here; not a production UAX29
        # implementation. Production segmentation remains renderer-owned.
        clusters = []
        for char in text:
            if clusters and unicodedata.combining(char):
                clusters[-1] += char
            else:
                clusters.append(char)
        return clusters

    def measure(self, text, font_px):
        advance = len(self.graphemes(text)) * font_px
        return lm.TextMeasurement(advance, 0, -.8 * font_px, advance, .2 * font_px)


def hinted(text):
    clusters = Metrics().graphemes(text)
    return lm._kana_bridge_breaks(clusters, [lm._script_run_kind(c) for c in clusters])


@pytest.mark.parametrize('kana', tuple('いきぎしじちぢびぴみりえけげせぜねべぺめれ'))
def test_existing_admitted_alphabet_is_canonically_equivalent(kana):
    composed = '紙' + kana + '形'
    decomposed = unicodedata.normalize('NFD', composed)
    assert hinted(composed) == hinted(decomposed) == [False, False, True, False]


@pytest.mark.parametrize('kana', tuple('はがのにをとでへもやてひふほばぱぶぷぼぽ'))
def test_non_admitted_kana_are_not_promoted_by_comparison(kana):
    for text in ('紙' + kana + '形', unicodedata.normalize('NFD', '紙' + kana + '形')):
        assert not any(hinted(text))


def partitions(clusters, width):
    for mask in range(1 << (len(clusters) - 1)):
        points = [0] + [i for i in range(1, len(clusters)) if mask & (1 << (i - 1))] + [len(clusters)]
        groups = [clusters[a:b] for a, b in zip(points, points[1:])]
        if all(len(g) <= width and g[0] != '。' for g in groups):
            yield groups


def oracle_score(groups, width):
    # Explicit positions for あ / 運 / kana / 込 / む / 。.
    points = set(itertools.accumulate(len(g) for g in groups[:-1]))
    fitting = width >= 5  # complete 運-kana-込-む plus required 。
    cohesion = (len(points & {2, 3, 4}) + sum(len(g) == 1 for g in groups)) if fitting else 0
    return (cohesion, len(groups), 0, 0, 0, len(points & {2, 4}),
            len(points & {3}), sum((width - len(g)) ** 2 for g in groups))


@pytest.mark.parametrize('kana', ('び', 'ぴ', 'べ', 'ぺ'))
@pytest.mark.parametrize('width', (2, 3, 4, 5, 6))
@pytest.mark.parametrize('budget', (None, 1, 2, 3, 4))
def test_all_partitions_preserve_the_existing_costs_for_decomposed_bridges(kana, width, budget):
    text = 'あ運' + unicodedata.normalize('NFD', kana) + '込む。'
    metrics = Metrics()
    clusters = metrics.graphemes(text)
    expected = [oracle_score(g, width) for g in partitions(clusters, width)
                if budget is None or len(g) <= budget]
    if not expected:
        with pytest.raises(ValueError, match='unbreakable_line'):
            lm._wrap_solutions(text, size=1, width=width, metrics=metrics, max_lines=budget)
        return
    choices = lm._wrap_solutions(text, size=1, width=width, metrics=metrics, max_lines=budget)
    score, rows = min(choices.values(), key=lambda item: item[0])
    groups = [metrics.graphemes(part) for part, _ in rows]
    assert score == oracle_score(groups, width) == min(expected)
    assert ''.join(part for part, _ in rows).encode() == text.encode()


@pytest.mark.parametrize('word', ('飛び立つ', '運び込む', '並べ直す', '食べ比べる'))
def test_natural_written_runs_use_the_same_breaks_without_rewriting(word):
    composed = 'あ' + word + '。'
    decomposed = unicodedata.normalize('NFD', composed)
    width = len(Metrics().graphemes(word)) + 1
    before = [s for s, _ in lm._wrap(composed, size=1, width=width, metrics=Metrics())]
    after = [s for s, _ in lm._wrap(decomposed, size=1, width=width, metrics=Metrics())]
    assert [unicodedata.normalize('NFC', s) for s in after] == before
    assert ''.join(after) == decomposed != composed


@pytest.mark.parametrize('mark', ('\u3099', '\u309a'))
def test_measurement_uses_raw_whole_substrings_even_when_their_widths_differ(mark):
    class DifferentWidth(Metrics):
        def __init__(self):
            self.measured = []
        def measure(self, text, font_px):
            self.measured.append(text)
            assert not any(c in text for c in 'びぴべぺ')
            advance = len(self.graphemes(text)) * font_px + (2 if mark in text else 0)
            return lm.TextMeasurement(advance, -.1, -.8, advance + .1, .2)
    text = 'あ運ひ' + mark + '込む。'
    metrics = DifferentWidth()
    rows = lm._wrap(text, size=1, width=5, metrics=metrics)
    assert ''.join(s for s, _ in rows) == text
    assert any(mark in s for s in metrics.measured)
    for part, m in rows:
        assert m == metrics.measure(part, 1)
        assert max(m.advance, m.right) - min(0, m.left) <= 5


@pytest.mark.parametrize('ratio', ('4:5', '9:16'))
@pytest.mark.parametrize('theme', ('soft_paper', 'quiet_night'))
def test_cmee_body_and_byte_hash_remain_bound_to_the_original_decomposed_input(ratio, theme):
    text = '私は机で紙を並へ\u3099直す時間を大切にしたい。まだ、毎日できるとは限らない。'
    source = PieceSourceSnapshot('synthetic-owner', 'synthetic-canonical-kana', '1', text)
    candidate = generate_piece_candidate(source, authenticated_owner_id=source.owner_id)
    assert '並へ\u3099直す' in candidate['piece_text']
    recipe = build_visual_recipe(candidate['format_type'], tier='premium', theme=theme, aspect_ratio=ratio)
    before = deepcopy(candidate), deepcopy(recipe)
    layout = lm.build_measured_layout(candidate, recipe, canonical_sha256_hex(recipe), Metrics())
    assert (candidate, recipe) == before
    blocks = candidate['content_payload']['body_blocks']
    assert [''.join(row['text'] for row in layout['lines'] if row['block_index'] == i)
            for i in range(len(blocks))] == blocks
    validate_piece_text_binding(candidate['content_payload'], candidate['piece_text'], layout['piece_text_hash'])
    other_source = PieceSourceSnapshot(source.owner_id, source.saved_input_id, '1', unicodedata.normalize('NFC', text))
    other = generate_piece_candidate(other_source, authenticated_owner_id=source.owner_id)
    assert other['piece_text_hash'] != candidate['piece_text_hash']
    assert not candidate['production_enabled'] and not layout['native_device_verified']
    assert layout['record_effect'] == layout['quota_effect'] == 0


@pytest.mark.parametrize('fault', ('split', 'missing', 'exception', 'nonfinite'))
def test_normalized_comparison_does_not_bypass_invalid_renderer_data(fault):
    class Broken(Metrics):
        def graphemes(self, text):
            return list(text) if fault == 'split' else super().graphemes(text)
        def measure(self, text, font_px):
            if fault == 'exception':
                raise RuntimeError('synthetic measurement failure')
            if fault == 'missing':
                return lm.TextMeasurement(1, 0, 0, 1, 1, False)
            if fault == 'nonfinite':
                return lm.TextMeasurement(float('nan'), 0, 0, 1, 1)
            return super().measure(text, font_px)
    with pytest.raises(ValueError):
        lm._wrap('あ運ひ\u3099込む。', size=1, width=5, metrics=Broken())
