"""Synthetic B9 competing-kana checks; no replay material or native credit."""
from copy import deepcopy
import itertools
import unicodedata

import pytest
import piece_v2_layout as lm
from piece_v2_contract import canonical_sha256_hex
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate
from piece_v2_visual import build_visual_recipe


class Metrics:
    profile_id = 'synthetic-competing-kana-not-native'

    def graphemes(self, text):
        # These fixtures exercise combining kana and ideographic selectors.
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


def rows(text, width, metrics=None):
    return [part for part, _ in lm._wrap(
        text, size=10, width=width * 10, metrics=metrics or Metrics())]


@pytest.mark.parametrize('anchor', ('残したい。', '眺めていた。', '迷っている。'))
@pytest.mark.parametrize('other', ('冬です。', 'メモです。', 'ゆったり', 'ぼくらは、'))
@pytest.mark.parametrize('width', (7, 9, 11))
def test_long_tail_does_not_move_cut_into_complete_competing_kana(anchor, other, width):
    text = '前記。' + anchor + other + '後記。'
    actual = rows(text, width)
    assert ''.join(actual) == text
    assert any(anchor in part for part in actual), actual
    assert any(other in part for part in actual), actual


@pytest.mark.parametrize('normalization', ('NFC', 'NFD'))
@pytest.mark.parametrize('prefix', ('', '🌱', '漢\U000e0100'))
def test_unattached_voiced_kana_and_raw_graphemes_are_preserved(normalization, prefix):
    kana = unicodedata.normalize(normalization, 'ぼくらは、')
    text = prefix + '前記。残したい。' + kana + '後記。'
    actual = rows(text, 8)
    assert ''.join(actual).encode('utf-8') == text.encode('utf-8')
    assert any(kana in part for part in actual), actual
    assert all(not unicodedata.combining(part[0]) for part in actual)


@pytest.mark.parametrize('left,right', (('「', '」'), ('（', '）'), ('', '。')))
def test_required_punctuation_is_measured_with_the_competing_run(left, right):
    text = '前記。残したい。' + left + 'ぼくらだけ' + right + '後記。'
    run = left + 'ぼくらだけ' + right
    actual = rows(text, 7)
    assert ''.join(actual) == text
    assert any(run in part for part in actual), actual


@pytest.mark.parametrize('kind', ('advance', 'overhang'))
def test_overwide_competing_run_is_not_declared_unbreakable(kind):
    class WideRun(Metrics):
        def measure(self, text, font_px):
            if 'ぼくらだけ。' in text:
                if kind == 'advance':
                    return lm.TextMeasurement(1000, 0, -8, 80, 2)
                return lm.TextMeasurement(80, -1000, -8, 80, 2)
            return super().measure(text, font_px)
    text = '前記。残したい。ぼくらだけ。後記。'
    actual = rows(text, 8, WideRun())
    assert ''.join(actual) == text
    assert not any('ぼくらだけ。' in part for part in actual)
    assert all(lm._width(WideRun().measure(part, 10)) <= 80 for part in actual)


@pytest.mark.parametrize('text,width,expected', (
    ('余白。ひらがなだけ。', 7, ['余白。ひら', 'がなだけ。']),
    ('余白。この地図からは必要。', 7, ['余白。この地図', 'からは必要。']),
    ('余白。写真を置く。', 6, ['余白。', '写真を置く。']),
))
def test_no_active_long_tail_keeps_previous_layout(text, width, expected):
    assert rows(text, width) == expected


@pytest.mark.parametrize('width', (6, 7, 8, 9))
def test_existing_determiner_and_bridge_scopes_are_not_extended(width):
    text = '残したい。この地図からは必要。書き直す。'
    clusters = Metrics().graphemes(text)
    kinds = [lm._script_run_kind(c) for c in clusters]
    attachment = lm._kana_attachment_breaks(clusters, kinds)
    bridge = lm._kana_bridge_breaks(clusters, kinds)
    prior = [a or b for a, b in zip(
        lm._fitting_bridge_run_breaks(clusters, kinds, attachment, bridge,
                                    size=10, width=width * 10, metrics=Metrics()),
        lm._fitting_determiner_run_breaks(clusters, kinds,
                                        size=10, width=width * 10, metrics=Metrics()), strict=True)]
    long_tail = lm._fitting_long_kana_run_breaks(
        clusters, kinds, prior, size=10, width=width * 10, metrics=Metrics())
    protected = [a or b for a, b in zip(prior, long_tail, strict=True)]
    added = lm._fitting_competing_kana_breaks(
        clusters, kinds, protected, size=10, width=width * 10, metrics=Metrics())
    assert not any(a and b for a, b in zip(protected, added, strict=True))
    # A prior determiner covers the Han head, not just an arbitrary kana suffix.
    start = text.index('地図')
    end = text.index('必要')
    assert not any(added[start:start + 3])
    assert all(added[start + 3:end])


ORACLE_TEXT = '前。見たい。ぼく。後。'
# Hand-marked script boundaries, independent of production hint construction.
LONG = {3, 4}
KANA = {3, 4}
COMPETING = {7}
HEAD = {3, 7, 10}


def partitions(text, width):
    result = []
    def visit(start, parts):
        if start == len(text):
            result.append(tuple(parts))
            return
        for end in range(start + 1, min(len(text), start + width) + 1):
            if end < len(text) and text[end] == '。':
                continue
            visit(end, parts + [text[start:end]])
    visit(0, [])
    return result


def oracle_score(parts, width):
    cuts = set(itertools.accumulate(len(part) for part in parts[:-1]))
    # 見たい is a TWO-kana ending, so it must not activate the new preference.
    return (0, len(parts), 0, 0, len(cuts & HEAD), len(cuts & KANA), 0,
            sum(((width - len(part)) * 10) ** 2 for part in parts))


@pytest.mark.parametrize('width', (4, 5, 6))
@pytest.mark.parametrize('budget', (2, 3, 4))
def test_no_activation_capacity_result_matches_independent_partition_oracle(width, budget):
    legal = [p for p in partitions(ORACLE_TEXT, width) if len(p) <= budget]
    if not legal:
        with pytest.raises(ValueError, match='unbreakable_line'):
            lm._wrap_solutions(ORACLE_TEXT, size=10, width=width * 10,
                               metrics=Metrics(), max_lines=budget)
        return
    solutions = lm._wrap_solutions(ORACLE_TEXT, size=10, width=width * 10,
                                   metrics=Metrics(), max_lines=budget)
    actual = min(solutions.values(), key=lambda item: item[0])
    assert actual[0] == min(oracle_score(p, width) for p in legal)


ACTIVE_TEXT = '前。残したい。ぼく。後。'
ACTIVE_LONG = {3, 4, 5}
ACTIVE_COMPETING = {8}
ACTIVE_HEAD = {3, 8, 11}


def active_oracle_score(parts, width):
    cuts = set(itertools.accumulate(len(part) for part in parts[:-1]))
    active = width >= 5  # The complete 残したい。 run, including punctuation.
    primary = (len(cuts & (ACTIVE_LONG | ACTIVE_COMPETING))
               + sum(len(part) == 1 for part in parts)
               + len(cuts & ACTIVE_HEAD)) if active else 0
    return (primary, len(parts), 0, 0, len(cuts & ACTIVE_HEAD),
            len(cuts & ACTIVE_LONG), 0,
            sum(((width - len(part)) * 10) ** 2 for part in parts))


@pytest.mark.parametrize('width', (4, 5, 6, 7, 8))
@pytest.mark.parametrize('budget', (2, 3, 4, 5))
def test_active_competition_matches_independent_partition_oracle(width, budget):
    legal = [p for p in partitions(ACTIVE_TEXT, width) if len(p) <= budget]
    if not legal:
        with pytest.raises(ValueError, match='unbreakable_line'):
            lm._wrap_solutions(ACTIVE_TEXT, size=10, width=width * 10,
                               metrics=Metrics(), max_lines=budget, line_height=16)
        return
    solutions = lm._wrap_solutions(ACTIVE_TEXT, size=10, width=width * 10,
                                   metrics=Metrics(), max_lines=budget, line_height=16)
    score, measured = min(solutions.values(), key=lambda item: item[0])
    actual = [part for part, _ in measured]
    assert ''.join(actual) == ACTIVE_TEXT
    assert score == active_oracle_score(actual, width)
    assert score == min(active_oracle_score(p, width) for p in legal)


@pytest.mark.parametrize('budget', (4, 5, 6, 7, 8))
def test_active_competition_shares_the_existing_vertical_budget(budget):
    width = 7
    legal = [(a, b) for a in partitions(ACTIVE_TEXT, width)
             for b in partitions(ACTIVE_TEXT, width) if len(a) + len(b) <= budget]
    expected = min(tuple(x + y for x, y in zip(active_oracle_score(a, width),
                   active_oracle_score(b, width), strict=True)) for a, b in legal)
    groups = lm._fit_measured_groups([ACTIVE_TEXT, ACTIVE_TEXT], size=10,
        width=width * 10, line_height=16, gap=10.4,
        available_height=budget * 16 + 10.4, metrics=Metrics())
    assert groups is not None
    actual = [[part for part, _ in group] for group in groups]
    assert [''.join(parts) for parts in actual] == [ACTIVE_TEXT, ACTIVE_TEXT]
    assert sum(map(len, actual)) <= budget
    assert tuple(x + y for x, y in zip(active_oracle_score(actual[0], width),
                 active_oracle_score(actual[1], width), strict=True)) == expected


@pytest.mark.parametrize('ratio', ('4:5', '9:16'))
@pytest.mark.parametrize('normalization', ('NFC', 'NFD'))
def test_cmee_body_recipe_identity_and_effect_boundaries_are_preserved(ratio, normalization):
    target = unicodedata.normalize(normalization, '部屋で写真を並べる時間')
    source = PieceSourceSnapshot('synthetic', 'competing-kana', '1',
        'わたしは' + target + 'を大切にしたい。まだ、始める日は決めていない。')
    candidate = generate_piece_candidate(source, authenticated_owner_id='synthetic')
    recipe = build_visual_recipe(candidate['format_type'], tier='premium', aspect_ratio=ratio)
    original = deepcopy((candidate, recipe))
    layout = lm.build_measured_layout(candidate, recipe, canonical_sha256_hex(recipe), Metrics())
    blocks = candidate['content_payload']['body_blocks']
    assert [''.join(line['text'] for line in layout['lines'] if line['block_index'] == i)
            for i in range(len(blocks))] == blocks
    assert original == (candidate, recipe)
    assert layout['piece_text_hash'] == candidate['piece_text_hash']
    assert layout['visual_recipe_hash'] == canonical_sha256_hex(recipe)
    assert any('わたしは、' in line['text'] for line in layout['lines'])
    assert layout['font_px'] >= layout['font_floor_px']
    assert not layout['clipped'] and not layout['missing_glyph']
    assert not layout['native_device_verified'] and not candidate['production_enabled']
    assert layout['record_effect'] == layout['quota_effect'] == 0
    assert 'lines' not in lm.fit_summary(layout)


@pytest.mark.parametrize('width', (7, 8, 9, 10, 11, 12))
@pytest.mark.parametrize('suffix', ('がまだ', 'からは', 'ではなく'))
def test_protected_head_does_not_leave_its_kana_suffix_as_a_replacement_cut(width, suffix):
    text = '残したい。この地図' + suffix + '必要。冬です。'
    actual = rows(text, width)
    assert ''.join(actual) == text
    assert any(suffix in part for part in actual), actual
    assert any('この地図' in part for part in actual), actual


@pytest.mark.parametrize('core', ('速達便', 'ノート', '計画'))
@pytest.mark.parametrize('width', (6, 7, 8, 9))
def test_competing_ending_does_not_move_its_cut_into_a_fitting_written_head(core, width):
    text = '前記。残したい。' + core + 'で冬です。'
    actual = rows(text, width)
    assert ''.join(actual) == text
    assert any(core in part for part in actual), actual
    assert any('冬です。' in part for part in actual), actual
