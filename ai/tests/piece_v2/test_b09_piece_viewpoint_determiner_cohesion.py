"""Measured determiner cohesion after a complete, delimited self-viewpoint.

Synthetic inputs only. A layout boundary does not infer an author/referent or
change CMEE admission. Exhaustive partitions use hand-annotated costs.
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
    profile_id = 'synthetic-viewpoint-determiner-not-native'

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
        return lm.TextMeasurement(advance, 0, -.8 * size, advance, .2 * size)


def wrap(text, width, metrics=None):
    metrics = metrics or Metrics()
    rows = lm._wrap(text, size=10, width=width * 10, metrics=metrics)
    assert ''.join(part for part, _ in rows) == text
    boundaries = set(itertools.accumulate(map(len, metrics.graphemes(text))))
    assert set(itertools.accumulate(len(part) for part, _ in rows)) <= boundaries
    for _, measured in rows:
        assert max(measured.advance, measured.right) - min(0, measured.left) <= width * 10
    return [part for part, _ in rows]


@pytest.mark.parametrize('speaker', ('私', 'わたし', '僕', 'ぼく', '俺', 'おれ'))
@pytest.mark.parametrize('viewpoint', ('は', 'にとって'))
@pytest.mark.parametrize('determiner', ('この', 'その', 'あの', 'どの'))
def test_delimited_viewpoint_keeps_determiner_head_and_short_tail_together(speaker, viewpoint, determiner):
    phrase = determiner + '時間が'
    text = '今は、' + speaker + viewpoint + phrase + '大切です。'
    rows = wrap(text, 8)
    assert any(phrase in row for row in rows)
    assert any(speaker + viewpoint in row for row in rows)


@pytest.mark.parametrize('delimiter', ('', '。', '、', '，', '！', ':', ' ', '\t', '「'))
def test_viewpoint_itself_must_start_at_an_explicit_boundary(delimiter):
    opening = '' if not delimiter else '前置き' + delimiter
    closing = '」' if delimiter == '「' else ''
    text = opening + '私はその記録が大切です' + closing + '。'
    assert any('その記録が' in row for row in wrap(text, 8))


@pytest.mark.parametrize('text', (
    '公私はその時間が大切。', '私たちはその時間が大切。',
    '友人はその時間が大切。', '私は私はその時間が大切。',
    'きのこの時間。', '私についてその時間が大切。',
))
def test_unknown_or_embedded_viewpoints_do_not_grant_a_determiner_boundary(text):
    clusters = list(text)
    hints = lm._fitting_determiner_run_breaks(
        clusters, [lm._script_run_kind(c) for c in clusters],
        size=10, width=80, metrics=Metrics())
    assert not any(hints)


@pytest.mark.parametrize('width', (5, 6, 7))
@pytest.mark.parametrize('budget', (1, 2, 3))
def test_capacity_constrained_paths_match_hand_annotated_partition_oracle(width, budget):
    text = '私はこの地図。'
    # Positions: 私0 は1 こ2 の3 地4 図5 。6. The fitting determiner
    # [2,6) includes the required final stop in measurement, so width >= 5.
    # The separate fitting viewpoint [0,2) also protects cut=1. Boundary=2
    # remains free. Kana attachment cuts=1,2,3; the only Han cut=5. No long-kana scope
    # overlaps this determiner, and no following short tail is present.
    def partitions(start):
        if start == len(text):
            yield []
        for end in range(start + 1, min(start + width, len(text)) + 1):
            if end < len(text) and text[end] == '。':
                continue
            for tail in partitions(end):
                yield [text[start:end]] + tail
    def score(parts):
        cuts = set(itertools.accumulate(map(len, parts[:-1])))
        return (len(cuts & {1, 3, 4, 5}) + sum(len(p) == 1 for p in parts),
                len(parts), 0, int(5 in cuts), 0, len(cuts & {1, 2, 3}), 0,
                sum(((width - len(p)) * 10) ** 2 for p in parts))
    valid = [score(parts) for parts in partitions(0) if len(parts) <= budget]
    if not valid:
        with pytest.raises(ValueError, match='unbreakable_line'):
            lm._wrap_solutions(text, size=10, width=width * 10, metrics=Metrics(),
                               max_lines=budget, line_height=16)
        return
    solutions = lm._wrap_solutions(text, size=10, width=width * 10, metrics=Metrics(),
                                   max_lines=budget, line_height=16)
    actual_score, actual_rows = min(solutions.values(), key=lambda value: value[0])
    parts = [part for part, _ in actual_rows]
    assert ''.join(parts) == text
    assert actual_score == score(parts) == min(valid)


@pytest.mark.parametrize('width', (3, 4))
def test_overwide_head_and_required_punctuation_remain_breakable(width):
    text = '私はその記録。'
    clusters = list(text)
    hints = lm._fitting_determiner_run_breaks(
        clusters, [lm._script_run_kind(c) for c in clusters],
        size=10, width=width * 10, metrics=Metrics())
    assert not any(hints)  # The complete determiner plus stop needs five.
    assert len(wrap(text, width)) >= 2


@pytest.mark.parametrize('head', ('地図', '地\U000e0100図', 'ノート'))
@pytest.mark.parametrize('overhang', (0, 3))
def test_renderer_graphemes_nonadditive_width_and_ink_control_cohesion(head, overhang):
    class Proportional(Metrics):
        def measure(self, text, size):
            advance = (len(self.graphemes(text)) - text.count(head) / 2) * size
            return lm.TextMeasurement(advance, -overhang, -.8 * size, advance + overhang, .2 * size)
    phrase = 'どの' + head + 'が'
    text = '現在は、僕にとって' + phrase + '大切です。'
    assert any(phrase in row for row in wrap(text, 8 + 2 * overhang / 10, Proportional()))


@pytest.mark.parametrize('ratio', ('4:5', '9:16'))
def test_connected_temporal_candidate_keeps_exact_body_recipe_and_effects(ratio):
    source = PieceSourceSnapshot('synthetic-owner', 'synthetic-viewpoint-layout', 'v1',
        '以前は、僕が苦手だったのは、川辺で風の音を聞く時間です。'
        '今は、僕はその時間が好きかもしれません。まだ、毎週予定を空けられるとは限りません。')
    candidate = generate_piece_candidate(source, authenticated_owner_id=source.owner_id)
    recipe = build_visual_recipe(candidate['format_type'], tier='premium', aspect_ratio=ratio)
    frozen = deepcopy(candidate), deepcopy(recipe)
    layout = lm.build_measured_layout(candidate, recipe, canonical_sha256_hex(recipe), Metrics())
    assert (candidate, recipe) == frozen
    blocks = candidate['content_payload']['body_blocks']
    assert [''.join(line['text'] for line in layout['lines'] if line['block_index'] == i)
            for i in range(len(blocks))] == blocks
    assert any('その時間が' in line['text'] for line in layout['lines'])
    assert layout['piece_text_hash'] == hashlib.sha256(candidate['piece_text'].encode()).hexdigest()
    assert layout['visual_recipe_hash'] == canonical_sha256_hex(recipe)
    assert layout['font_px'] == (48 if ratio == '4:5' else 52)
    assert layout['record_effect'] == layout['quota_effect'] == 0
    assert not layout['clipped'] and not layout['missing_glyph'] and not layout['native_device_verified']
    for line in layout['lines']:
        left, top, right, bottom = line['ink_box']
        assert layout['margin'] <= left <= right <= layout['width'] - layout['margin']
        assert layout['margin'] <= top <= bottom <= layout['height'] - layout['margin'] - layout['branding_zone']


@pytest.mark.parametrize('width', (7, 8, 9, 10))
@pytest.mark.parametrize('viewpoint', ('私にとって', 'わたしにとって'))
def test_cohesion_does_not_move_the_cut_inside_the_licensing_viewpoint(width, viewpoint):
    text = '以前は、休息が大切でした。今は、' + viewpoint + 'その時間が必要かもしれません。'
    rows = wrap(text, width)
    assert any(viewpoint in row for row in rows)
    assert any('その時間が' in row for row in rows)
    # Whole viewpoint + determiner can be overwide: a break BETWEEN them
    # stays available, even when every internal cut has a cohesion cost.
    if width < len(viewpoint + 'その時間が'):
        assert not any(viewpoint + 'その時間が' in row for row in rows)
