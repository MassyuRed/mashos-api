"""Synthetic B9 run-aware wrapping; never native/device or product acceptance.

The renderer still owns every grapheme and measurement. These preferences do
not parse Japanese words, rewrite the canonical body or change its recipe.
"""
from copy import deepcopy
import hashlib
import itertools
import math

import pytest

from piece_v2_contract import canonical_sha256_hex
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate
from piece_v2_layout import TextMeasurement, _wrap, build_measured_layout, fit_summary
from piece_v2_visual import build_visual_recipe


class Metrics:
    profile_id = 'synthetic-japanese-runs-not-device'

    def graphemes(self, text):
        clusters = []
        for char in text:
            if char in 'ﾞﾟ' and clusters:
                clusters[-1] += char
            else:
                clusters.append(char)
        return clusters

    def measure(self, text, font_px):
        width = len(text) * font_px
        return TextMeasurement(width, 0, -font_px * .8, width, font_px * .2)


def wrapped(text, width, metrics=None):
    return [part for part, _ in _wrap(text, size=1, width=width,
                                     metrics=metrics or Metrics())]


def breaks(lines):
    return set(itertools.accumulate(map(len, lines[:-1])))


def assert_intact(text, lines, word):
    start = text.index(word)
    assert not breaks(lines).intersection(range(start + 1, start + len(word)))


@pytest.mark.parametrize('text,width,word,count', (
    ('静かな時間を大切にしたい。', 6, '時間', 3),
    ('机で読書する時間を大切にしたい。', 6, '大切', 3),
    ('机で読書する時間を大切にしたい。', 7, '大切', 3),
    ('私はパソコンで日記を書きたい。', 6, 'パソコン', 3),
    ('私はパソコンで日記を書きたい。', 7, 'パソコン', 3),
    ('私はﾊﾟｿｺﾝで日記を書きたい。', 7, 'ﾊﾟｿｺﾝ', 3),
))
def test_short_written_script_runs_stay_together_without_an_extra_line(text, width, word, count):
    lines = wrapped(text, width)
    assert ''.join(lines) == text
    assert len(lines) == count
    assert_intact(text, lines, word)


@pytest.mark.parametrize('mark', ('。', '！', '？', '!', '?'))
@pytest.mark.parametrize('width', (7, 13))
def test_a_single_japanese_sentence_head_is_not_stranded(mark, width):
    text = '机で本を読み返したい' + mark + 'まだ、答えは決めていない。'
    lines = wrapped(text, width)
    assert ''.join(lines) == text
    assert len(lines) == math.ceil(len(text) / width)
    assert all(not line.endswith(mark + 'ま') for line in lines[:-1])


@pytest.mark.parametrize('text', (
    'abcdefghijk', '12345678901', '東京都美術館展示室案内',
    'アイウエオカキクケコサ', 'ｱｲｳｴｵｶｷｸｹｺｻ',
))
def test_overwide_runs_are_soft_preferences_not_new_refusals_or_hyphenation(text):
    lines = wrapped(text, 3)
    assert ''.join(lines) == text
    assert len(lines) == math.ceil(len(text) / 3)
    assert all(0 < len(line) <= 3 for line in lines)


def test_cjk_extension_and_variation_selector_use_renderer_clusters():
    text = 'あ𠮷野を見たい。'
    lines = wrapped(text, 5)
    assert_intact(text, lines, '𠮷野')
    class Variation(Metrics):
        def graphemes(self, text):
            return ['あ', '葛\U000E0100', '飾', 'を', '見', 'た', 'い', '。']
        def measure(self, text, font_px):
            width = sum(c != '\U000E0100' for c in text)
            return TextMeasurement(width, 0, -.8, width, .2)
    source = 'あ葛\U000E0100飾を見たい。'
    lines = wrapped(source, 5, Variation())
    assert ''.join(lines) == source
    assert_intact(source, lines, '葛\U000E0100飾')


def test_halfwidth_voicing_and_emoji_are_not_resegmented():
    clusters = ['あ', 'ｶﾞ', 'ラ', 'ス', 'と', '👩\u200d💻', 'を', '見', 'た', 'い', '。']
    class Clustered(Metrics):
        def graphemes(self, text): return clusters
        def measure(self, text, font_px):
            width = len(text.replace('ｶﾞ', 'x').replace('👩\u200d💻', 'x'))
            return TextMeasurement(width, 0, -.8, width, .2)
    text = ''.join(clusters)
    lines = wrapped(text, 5, Clustered())
    assert ''.join(lines) == text
    assert_intact(text, lines, 'ｶﾞ')
    assert_intact(text, lines, '👩\u200d💻')


@pytest.mark.parametrize('text,width', (
    ('あ時間を大切に', 5), ('あパソコンで', 4),
    ('あABと時間を', 4), ('あ時間。まだ', 4),
))
def test_small_exhaustive_partition_oracle_uses_measured_width_and_exact_text(text, width):
    # Independent enumeration, not the compiler's dynamic program or helper.
    # The sets here describe only these synthetic strings, not a tokenizer.
    def cost(parts):
        cuts = breaks(parts)
        ascii_splits = sum(text[i-1].isascii() and text[i-1].isalnum()
                           and text[i].isascii() and text[i].isalnum() for i in cuts)
        script_splits = sum(any(text[i-1] in chars and text[i] in chars
                                for chars in ('時間大切', 'パソコン')) for i in cuts)
        heads = sum(i >= 2 and text[i-2] in '。！？!?' for i in cuts)
        return len(parts), ascii_splits, script_splits, heads, sum((width-len(p))**2 for p in parts)
    allowed = []
    for mask in range(1 << (len(text)-1)):
        cuts = [0] + [i for i in range(1, len(text)) if mask & (1 << (i-1))] + [len(text)]
        parts = [text[a:b] for a, b in zip(cuts, cuts[1:])]
        if all(len(p) <= width and p[0] not in '。' for p in parts):
            allowed.append(parts)
    actual = wrapped(text, width)
    assert ''.join(actual) == text
    assert cost(actual) == min(map(cost, allowed))


CASES = (
    ('僕が大切にしたいのは、机で静かに本を読む時間です。'
     '僕は庭で季節の花を眺める時間より、その時間が好きです。'
     'まだ、毎日続けられるとは限らない。'),
    ('私が大切にしたいのは、机で静かに本を読む時間です。'
     '私はその時間より、庭で季節の花を眺める時間が好きではなかったかもしれない。'
     'まだ、毎日続けられるとは限らない。'),
    ('私が大切にしたいのは、机で静かに本を読む時間です。'
     '日程が合うなら、私にとってその時間より、庭で季節の花を眺める時間が必要かもしれない。'
     'まだ、毎日続けられるとは限らない。'),
    ('僕にとって友人の森さんの先輩の原さんと落ち着いて話す時間が大切です。'
     '僕はその時間より、庭で季節の花を眺める時間が好きかもしれない。'
     'まだ、毎日続けられるとは限らない。'),
)


@pytest.mark.parametrize('text', CASES)
@pytest.mark.parametrize('ratio', ('4:5', '9:16'))
@pytest.mark.parametrize('theme', ('soft_paper', 'quiet_night'))
def test_complete_cmee_body_and_visual_identity_survive_wrapping(text, ratio, theme):
    source = PieceSourceSnapshot('synthetic-owner', 'synthetic-wrap', '1', text)
    candidate = generate_piece_candidate(source, authenticated_owner_id=source.owner_id)
    recipe = build_visual_recipe(candidate['format_type'], tier='premium',
                                 aspect_ratio=ratio, theme=theme)
    before = deepcopy(candidate), deepcopy(recipe)
    layout = build_measured_layout(candidate, recipe, canonical_sha256_hex(recipe), Metrics())
    blocks = candidate['content_payload']['body_blocks']
    rebuilt = [''.join(line['text'] for line in layout['lines'] if line['block_index'] == i)
               for i in range(len(blocks))]
    assert rebuilt == blocks
    assert '\n\n'.join(rebuilt) == candidate['piece_text']
    assert layout['piece_text_hash'] == hashlib.sha256(candidate['piece_text'].encode()).hexdigest()
    assert layout['visual_recipe_hash'] == canonical_sha256_hex(recipe)
    assert before == (candidate, recipe)
    assert layout['font_px'] >= layout['font_floor_px']
    assert not layout['clipped'] and not layout['missing_glyph']
    assert not layout['native_device_verified']
    assert layout['record_effect'] == layout['quota_effect'] == 0
    assert not candidate['production_enabled']
    assert 'lines' not in fit_summary(layout)
    for line in layout['lines']:
        a, b, c, d = line['ink_box']
        assert layout['margin'] <= a <= c <= layout['width'] - layout['margin']
        assert layout['margin'] <= b <= d <= layout['height'] - layout['margin'] - layout['branding_zone']


def test_whole_substring_bearings_and_variable_width_are_measured_not_counted():
    class Proportional(Metrics):
        def measure(self, text, font_px):
            advance = sum(2 if c in '時間' else .5 for c in text)
            return TextMeasurement(advance, -1, -.8, advance + 1, .2)
    text = 'あ時間を大切にしたい。'
    metrics = Proportional()
    result = _wrap(text, size=1, width=7, metrics=metrics)
    assert ''.join(part for part, _ in result) == text
    for part, measurement in result:
        assert measurement == metrics.measure(part, 1)
        assert max(measurement.advance, measurement.right) - min(0, measurement.left) <= 7
    assert_intact(text, [p for p, _ in result], '時間')


@pytest.mark.parametrize('text,width', (
    ('私にとって、その時間が大切です。', 5),
    ('今日はもっとゆっくり考えたい。', 7),
    ('今日はもっとゆっくり考えたい。', 9),
    ('机でしっかり考えてみたい。', 6),
))
def test_script_preference_does_not_strand_a_sokuon_before_its_following_letter(text, width):
    lines = wrapped(text, width)
    assert ''.join(lines) == text
    assert len(lines) == math.ceil(len(text) / width)
    assert all(not part.endswith(('っ', 'ッ')) for part in lines[:-1])
