"""Bounded mixed-text line breaking in the existing B9 measured owner.

Synthetic renderer metrics are not native/device acceptance. The same canonical
text, grapheme partition, font floors and long-token break candidates are kept.
"""
import hashlib

import pytest

from piece_v2_contract import canonical_sha256_hex
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate
from piece_v2_layout import TextMeasurement, _wrap, build_measured_layout
from piece_v2_visual import build_visual_recipe


class Metrics:
    profile_id = 'synthetic-word-boundaries-not-device'

    def graphemes(self, text):
        return list(text)

    def measure(self, text, font_px):
        width = len(text) * font_px
        return TextMeasurement(width, 0, -font_px * .8, width, font_px * .2)


@pytest.mark.parametrize('word', ['Python', 'Cocolon', 'JavaScript', 'ABC123'])
def test_equal_line_count_prefers_a_whole_word_over_even_raggedness(word):
    text = 'あいうえおか' + word + 'きくけこ'
    width = (len(word) + 4) * 10
    lines = _wrap(text, size=10, width=width, metrics=Metrics())
    parts = [part for part, _ in lines]
    assert len(parts) == 2
    assert ''.join(parts) == text
    assert any(word in part for part in parts)
    assert all(m.advance <= width for _, m in lines)


@pytest.mark.parametrize('word', ['ABCDEFGHIJKLMNOPQRSTUVWXYZ', '01234567890123456789012345'])
def test_long_token_still_breaks_without_deleting_or_inserting_characters(word):
    lines = _wrap(word, size=10, width=100, metrics=Metrics())
    assert len(lines) == 3
    assert ''.join(part for part, _ in lines) == word
    assert all(m.advance <= 100 for _, m in lines)


def test_ascii_base_with_combining_mark_remains_one_renderer_cluster():
    class ClusterMetrics(Metrics):
        def graphemes(self, text):
            return ['あ', 'い', 'う', 'え', 'お', 'か', 'C', 'a', 'f', 'e\u0301', 'き', 'く', 'け', 'こ']
        def measure(self, text, font_px):
            width = (len(text) - text.count('\u0301')) * font_px
            return TextMeasurement(width, 0, -font_px * .8, width, font_px * .2)
    text = 'あいうえおかCafe\u0301きくけこ'
    lines = _wrap(text, size=10, width=80, metrics=ClusterMetrics())
    assert ''.join(part for part, _ in lines) == text
    assert any('Cafe\u0301' in part for part, _ in lines)
    assert all(not part.startswith('\u0301') for part, _ in lines)


@pytest.mark.parametrize('ratio', ['4:5', '9:16'])
@pytest.mark.parametrize('theme', ['soft_paper', 'quiet_night'])
def test_cmee_body_hash_and_existing_visual_choices_are_unchanged(ratio, theme):
    source = '私が大切にしたいのは、Pythonで小さく試して確かめることです。まだ、毎日続けるとは決めていない。'
    candidate = generate_piece_candidate(
        PieceSourceSnapshot('synthetic-owner', 'synthetic-word-source', 'v1', source),
        authenticated_owner_id='synthetic-owner')
    expected = '私は、Pythonで小さく試して確かめることを大切にしたい。\n\nまだ、毎日続けるとは決めていない。'
    assert candidate['piece_text'] == expected
    assert candidate['piece_text_hash'] == hashlib.sha256(expected.encode()).hexdigest()
    recipe = build_visual_recipe(candidate['format_type'], tier='premium', aspect_ratio=ratio, theme=theme)
    layout = build_measured_layout(candidate, recipe, canonical_sha256_hex(recipe), Metrics())
    assert [''.join(line['text'] for line in layout['lines'] if line['block_index'] == i)
            for i in range(len(candidate['content_payload']['body_blocks']))] == candidate['content_payload']['body_blocks']
    assert any('Python' in line['text'] for line in layout['lines'])
    assert layout['piece_text_hash'] == candidate['piece_text_hash']
    assert layout['visual_recipe_hash'] == canonical_sha256_hex(recipe)
    assert layout['font_px'] >= layout['font_floor_px']
    assert not layout['clipped'] and not layout['native_device_verified']
    assert layout['record_effect'] == layout['quota_effect'] == 0


def test_no_ascii_word_keeps_existing_balanced_line_choice():
    text = 'あいうえおかきくけこさしすせそた'
    lines = _wrap(text, size=10, width=100, metrics=Metrics())
    assert [part for part, _ in lines] == [text[:8], text[8:]]


@pytest.mark.parametrize('width', [150, 180])
def test_whole_word_does_not_strand_a_single_sentence_head(width):
    class MixedMetrics(Metrics):
        def measure(self, text, font_px):
            width = sum(.5 if c.isascii() else 1 for c in text) * font_px
            return TextMeasurement(width, 0, -font_px * .8, width, font_px * .2)
    text = '私は、人と落ち着いてJavaScriptの学び方を話したい。まだ、日時は決めていない。'
    lines = _wrap(text, size=10, width=width, metrics=MixedMetrics())
    parts = [part for part, _ in lines]
    assert len(parts) == 3
    assert ''.join(parts) == text
    assert any('JavaScript' in part for part in parts)
    assert all(not (len(part) >= 2 and part[-2] in '。！？!?') for part in parts[:-1])
    assert all(m.advance <= width for _, m in lines)
