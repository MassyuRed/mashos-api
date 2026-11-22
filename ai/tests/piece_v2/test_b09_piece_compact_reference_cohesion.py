"""Compact written reference pairs remain readable without changing the body.

These are synthetic measured-layout checks, not semantic/source admission or
native rendering acceptance. A fitting hint remains soft under line budgets.
"""
from copy import deepcopy
import hashlib
import itertools
import unicodedata

import pytest

import piece_v2_layout as lm
from piece_v2_contract import canonical_sha256_hex
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate
from piece_v2_visual import build_visual_recipe


class Metrics:
    profile_id = 'synthetic-compact-reference-not-native'

    def graphemes(self, text):
        result = []
        for char in text:
            if result and (unicodedata.combining(char) or 0xE0100 <= ord(char) <= 0xE01EF):
                result[-1] += char
            else:
                result.append(char)
        return result

    def measure(self, text, size):
        advance = len(self.graphemes(text)) * size
        return lm.TextMeasurement(advance, 0, -.8 * size, advance, .2 * size)


def rows(text, width, metrics=None):
    metrics = metrics or Metrics()
    result = lm._wrap(text, size=10, width=width * 10, metrics=metrics)
    parts = [part for part, _ in result]
    assert ''.join(parts) == text
    assert set(itertools.accumulate(map(len, parts))) <= set(
        itertools.accumulate(map(len, metrics.graphemes(text))))
    assert all(lm._width(m) <= width * 10 for _, m in result)
    return parts


@pytest.mark.parametrize('heads', tuple(itertools.permutations(('時間', 'こと', 'もの'), 2)))
@pytest.mark.parametrize('operator', ('と', 'より'))
@pytest.mark.parametrize('prefix', ('前置き。', '今は、私にとって'))
def test_complete_fitting_pair_keeps_its_connector_and_following_particle(heads, operator, prefix):
    phrase = 'その' + heads[0] + operator + 'この' + heads[1] + 'が'
    text = prefix + phrase + '大切です。まだ、決めていません。'
    result = rows(text, len(phrase) + 1)
    assert any(phrase in row for row in result)
    if prefix.endswith('私にとって'):
        assert any('私にとって' in row for row in result)


@pytest.mark.parametrize('prefix', ('きの', '友人は', '私たちは', '私は私は'))
def test_pair_inside_an_unknown_prefix_does_not_gain_a_new_start(prefix):
    text = prefix + 'そのこととこのものが必要。'
    c = Metrics().graphemes(text)
    hints = lm._fitting_determiner_run_breaks(c, [lm._script_run_kind(s) for s in c],
        size=10, width=200, metrics=Metrics())
    assert not any(hints)


@pytest.mark.parametrize('text', (
    'そのこととこのものがら必要。', 'そのこととこのものものしい。',
    'そのこととてもこのものが必要。', 'そのことこのものが必要。',
    'そのことと、このものが必要。', 'そのことと このものが必要。',
))
def test_partial_tokens_missing_links_and_delimited_pairs_keep_the_old_hint_boundary(text):
    c = Metrics().graphemes(text)
    hints = lm._fitting_determiner_run_breaks(c, [lm._script_run_kind(s) for s in c],
        size=10, width=200, metrics=Metrics())
    # All-kana reference operands had no determiner/Han hint. Do not extend
    # this compact-form edit into another grammar or normalize separators.
    assert not any(hints)


@pytest.mark.parametrize('width', (4, 6, 8))
def test_overwide_pair_keeps_existing_breakable_layout(width):
    text = 'そのことよりこのものが必要。'
    c = Metrics().graphemes(text)
    hints = lm._fitting_determiner_run_breaks(c, [lm._script_run_kind(s) for s in c],
        size=10, width=width * 10, metrics=Metrics())
    assert not any(hints)
    assert len(rows(text, width)) >= 2


def test_required_punctuation_participates_in_the_fit_measurement():
    text = '「そのこととこのものが」。'
    c = Metrics().graphemes(text)
    kinds = [lm._script_run_kind(s) for s in c]
    too_narrow = lm._fitting_determiner_run_breaks(c, kinds, size=10, width=110, metrics=Metrics())
    enough = lm._fitting_determiner_run_breaks(c, kinds, size=10, width=130, metrics=Metrics())
    assert not any(too_narrow)
    assert all(enough[2:11])
    rows(text, 11)


@pytest.mark.parametrize('overhang', (0, 3))
def test_actual_graphemes_and_nonadditive_ink_width_are_used(overhang):
    class Proportional(Metrics):
        def measure(self, text, size):
            a = (len(self.graphemes(text)) - text.count('時間') / 2) * size
            return lm.TextMeasurement(a, -overhang, -.8 * size, a + overhang, .2 * size)
    phrase = 'その時\U000e0100間とこのことか\u3099'
    text = '前置き。' + phrase + '必要です。'
    result = rows(text, 10 + 2 * overhang / 10, Proportional())
    assert any(phrase in row for row in result)


@pytest.mark.parametrize('budget', (2, 3))
def test_vertical_capacity_can_break_the_hint_without_losing_text(budget):
    text = '前置き。そのこととこのものが必要。'
    solutions = lm._wrap_solutions(text, size=10, width=110, metrics=Metrics(),
        max_lines=budget, line_height=16)
    for count, (_, measured) in solutions.items():
        assert count <= budget
        assert ''.join(part for part, _ in measured) == text
        assert all(lm._width(m) <= 110 for _, m in measured)
    if budget == 2:
        assert not any('そのこととこのものが' in part for part, _ in solutions[2][1])


@pytest.mark.parametrize('ratio', ('4:5', '9:16'))
@pytest.mark.parametrize('tier', ('free', 'plus', 'premium'))
def test_same_cmee_body_flows_into_the_existing_versioned_layout(ratio, tier):
    text = ('僕にとって友人と落ち着いて話す時間が大切です。'
        '僕が大切にしたいのは、先輩へ手紙を書くことです。'
        '僕はその時間とこのことが好きかもしれません。まだ、始める日は決めていません。')
    source = PieceSourceSnapshot('synthetic-owner', 'synthetic-compact-layout', '1', text)
    candidate = generate_piece_candidate(source, authenticated_owner_id=source.owner_id, tier=tier)
    recipe = build_visual_recipe(candidate['format_type'], tier='premium', aspect_ratio=ratio)
    before = deepcopy((candidate, recipe))
    result = lm.build_measured_layout(candidate, recipe, canonical_sha256_hex(recipe), Metrics())
    assert (candidate, recipe) == before
    assert result['piece_text_hash'] == hashlib.sha256(candidate['piece_text'].encode()).hexdigest()
    assert any('その時間とこのことが' in row['text'] for row in result['lines'])
    assert [''.join(row['text'] for row in result['lines'] if row['block_index'] == i)
        for i in range(len(candidate['content_payload']['body_blocks']))] == candidate['content_payload']['body_blocks']
    assert result['record_effect'] == result['quota_effect'] == 0
    assert not result['native_device_verified']
