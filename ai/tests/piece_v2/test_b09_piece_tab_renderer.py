"""Development-renderer tab policy; no fonts/native dependencies or user inputs."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from piece_v2_contract import PieceContractError
from piece_v2_layout import TextMeasurement, _measure, _wrap


SCRIPT = Path(__file__).resolve().parents[3] / 'scripts/piece_v2_preview_probe.py'
spec = importlib.util.spec_from_file_location('piece_probe_under_test', SCRIPT)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class PlainMetrics:
    profile_id = 'synthetic-renderer'

    def graphemes(self, text):
        return list(text)

    def font(self, size):
        return ('face', size)

    def measure(self, text, size):
        # Space is proportional to the selected size; visible letters are wider.
        advance = sum(size / 4 if c == ' ' else size for c in text)
        return TextMeasurement(advance, -0.5 if text.strip() else 0,
                               -size, advance, 1, '\t' not in text)


def adapter(base=None):
    base = base or PlainMetrics()
    # Run the same expectations against the old renderer rather than skip them.
    return getattr(probe, 'TabAwareMetrics', lambda value: value)(base)


class Drawing:
    def __init__(self):
        self.calls = []

    def text(self, position, text, **kwargs):
        self.calls.append((position, text, kwargs))


def draw(metrics, text, size=4, position=(10, 20)):
    target = Drawing()
    if hasattr(metrics, 'draw_text'):
        metrics.draw_text(target, position, text, font_px=size, fill=255)
    else:
        target.text(position, text, font=metrics.font(size), fill=255, anchor='ls')
    return target.calls


@pytest.mark.parametrize('size', [1, 4, 7, 36, 52])
@pytest.mark.parametrize(('text', 'units'), [
    ('A\tB', 3), ('\tAB', 3), ('AB\t', 3),
    ('A\t\tB', 4), ('\t\t', 2), ('A \tB', 3),
])
def test_tabs_use_next_renderer_measured_stop_without_replacement(text, units, size):
    m = _measure(adapter(), text, size)
    assert m.advance == pytest.approx(units * size)
    assert m.glyphs_available is True
    calls = draw(adapter(), text, size)
    assert all('\t' not in call[1] for call in calls)
    assert ''.join(call[1] for call in calls) == text.replace('\t', '')


@pytest.mark.parametrize(('text', 'offsets'), [
    ('A\tB', [0, 8]), ('A \tB', [0, 8]), ('\tAB', [4]),
    ('A\t\tB', [0, 12]), ('A\tB\tC', [0, 8, 16]),
])
def test_drawing_uses_the_measured_run_origins(text, offsets):
    calls = draw(adapter(), text)
    assert [xy[0] - 10 for xy, _, _ in calls] == offsets
    assert all(xy[1] == 20 and kw == {'font': ('face', 4), 'fill': 255, 'anchor': 'ls'}
               for xy, _, kw in calls)


@pytest.mark.parametrize('text', ['AB', 'A B', 'A\u0301', 'は\u3099甲', '漢\U000e0100', '\u200d', ''])
def test_non_tab_text_is_one_unchanged_renderer_run(text):
    base = PlainMetrics()
    assert adapter(base).measure(text, 4) == base.measure(text, 4)
    assert draw(adapter(base), text) == draw(base, text)


@pytest.mark.parametrize('control', ['\0', '\x01', '\x08', '\n', '\r', '\x0b', '\x0c', '\x1b', '\x7f', '\x85'])
def test_other_controls_cannot_be_silently_rendered_or_removed(control):
    metrics = adapter()
    with pytest.raises(PieceContractError):
        _measure(metrics, 'A' + control + 'B', 4)
    with pytest.raises(PieceContractError):
        draw(metrics, 'A' + control + 'B')


def test_plain_missing_glyphs_still_fail_before_drawing_any_run():
    class Missing(PlainMetrics):
        def measure(self, text, size):
            m = super().measure(text, size)
            return TextMeasurement(m.advance, m.left, m.top, m.right, m.bottom, '?' not in text)
    metrics = adapter(Missing())
    with pytest.raises(PieceContractError):
        _measure(metrics, 'A\t?', 4)
    target = Drawing()
    if hasattr(metrics, 'draw_text'):
        with pytest.raises(PieceContractError):
            metrics.draw_text(target, (0, 0), 'A\t?', font_px=4, fill=255)
        assert target.calls == []
    else:
        pytest.fail('old renderer has no shared measured drawing plan')


@pytest.mark.parametrize('advance', [0, -1, float('nan'), float('inf')])
def test_invalid_tab_interval_does_not_fall_back_to_character_counts(advance):
    class Invalid(PlainMetrics):
        def measure(self, text, size):
            return TextMeasurement(advance, 0, 0, 0, 0) if text == '    ' else super().measure(text, size)
    with pytest.raises(PieceContractError):
        _measure(adapter(Invalid()), 'A\tB', 4)


def test_ink_extents_are_shifted_without_changing_the_advance():
    class Overhang(PlainMetrics):
        def measure(self, text, size):
            if text == 'B':
                return TextMeasurement(4, -2, -7, 9, 3)
            return super().measure(text, size)
    m = _measure(adapter(Overhang()), 'A\tB', 4)
    assert (m.advance, m.left, m.top, m.right, m.bottom) == (12, -0.5, -7, 17, 3)


def test_raw_tabs_are_preserved_in_the_existing_layout_lines():
    text = '甲\t乙丙\t丁'
    rows = _wrap(text, size=4, width=13, metrics=adapter())
    assert ''.join(part for part, _ in rows) == text
    assert sum(part.count('\t') for part, _ in rows) == 2
    assert all(max(m.advance, m.right) - min(0, m.left) <= 13 for _, m in rows)


def test_profile_identifies_the_new_control_policy_and_delegates_graphemes():
    metrics = adapter()
    assert metrics.profile_id == 'synthetic-renderer-tab4-v1'
    assert metrics.graphemes('甲\t乙') == ['甲', '\t', '乙']
