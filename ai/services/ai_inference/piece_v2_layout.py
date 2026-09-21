"""B9 pure measured layout. Pixel/font profile belongs to the actual renderer.

Measurements and grapheme segmentation MUST come from that renderer, not from
character counts. Linux probe measurements are not valid for iOS/Android.
This module does not claim to be a native renderer or authorize a record save.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import unicodedata
from typing import Protocol
from piece_v2_contract import PieceContractError, validate_piece_text_binding
from piece_v2_content_policy import validate_candidate_text
from piece_v2_visual import validate_visual_recipe, resolve_visual


@dataclass(frozen=True)
class TextMeasurement:
    advance: float
    left: float
    top: float
    right: float
    bottom: float
    glyphs_available: bool = True


class RendererMetrics(Protocol):
    profile_id: str
    def graphemes(self, text: str) -> list[str]: ...
    def measure(self, text: str, font_px: int) -> TextMeasurement: ...


_NO_START = frozenset('、。，．？！!?：；:;)]）］｝】〉》」』〕〗〙〛ー々ぁぃぅぇぉっゃゅょァィゥェォッャュョ')
_NO_END = frozenset('([（［｛【〈《「『〔〖〘〚')


def _fail(reason: str) -> PieceContractError:
    return PieceContractError('PIECE_LAYOUT_UNAVAILABLE', reason)


def _measure(metrics: RendererMetrics, text: str, size: int) -> TextMeasurement:
    try:
        m = metrics.measure(text, size)
    except Exception as exc:
        raise _fail('measurement_failed') from exc
    if type(m) is not TextMeasurement or m.glyphs_available is not True:
        raise _fail('missing_glyph_or_metrics')
    values = (m.advance, m.left, m.top, m.right, m.bottom)
    if (any(type(v) not in (int, float) or not math.isfinite(v) for v in values)
            or m.advance < 0 or m.right < m.left or m.bottom < m.top):
        raise _fail('invalid_metrics')
    return m


def _width(m: TextMeasurement) -> float:
    return max(m.advance, m.right) - min(0.0, m.left)


def _wrap(text: str, *, size: int, width: int, metrics: RendererMetrics) -> list[tuple[str, TextMeasurement]]:
    try:
        clusters = metrics.graphemes(text)
    except Exception as exc:
        raise _fail('grapheme_segmentation_failed') from exc
    if (not isinstance(clusters, list) or not clusters
            or any(not isinstance(c, str) or not c for c in clusters)
            or ''.join(clusters) != text):
        raise _fail('grapheme_partition_invalid')
    # Reject evident broken partitions; full UAX29 segmentation is the renderer
    # contract, not a second partial Unicode implementation in the compiler.
    for i, c in enumerate(clusters):
        if i and (unicodedata.combining(c[0]) or c[0] == '\u200d'
                  or 0xFE00 <= ord(c[0]) <= 0xFE0F or clusters[i - 1].endswith('\u200d')):
            raise _fail('split_grapheme')
    # Minimize line count first, then balance raggedness over ALL lines.
    # Counting the final line avoids the long-line + one-character-orphan
    # result of greedy wrapping without altering content or font scale.
    n = len(clusters)
    costs = {n: (0, 0.0)}
    choices = {}
    for start in range(n - 1, -1, -1):
        best = None
        for end in range(start + 1, n + 1):
            if end not in costs:
                continue
            if end < n and (clusters[end][0] in _NO_START or clusters[end - 1][-1] in _NO_END):
                continue
            part = ''.join(clusters[start:end])
            measured = _measure(metrics, part, size)
            measured_width = _width(measured)
            if measured_width > width:
                continue
            count, penalty = costs[end]
            score = (count + 1, penalty + (width - measured_width) ** 2)
            if best is None or score < best[0]:
                best = (score, end, part, measured)
        if best is not None:
            costs[start] = best[0]
            choices[start] = best[1:]
    if 0 not in choices:
        raise _fail('unbreakable_line')
    out, start = [], 0
    while start < n:
        end, part, measured = choices[start]
        out.append((part, measured))
        start = end
    return out


def build_measured_layout(candidate: dict, recipe: dict, recipe_hash: str,
                          metrics: RendererMetrics) -> dict:
    payload = candidate['content_payload']
    text = validate_piece_text_binding(payload, candidate['piece_text'], candidate['piece_text_hash'])
    validate_candidate_text(payload)
    if not isinstance(getattr(metrics, 'profile_id', None), str) or not metrics.profile_id:
        raise _fail('renderer_profile_required')
    recipe = validate_visual_recipe(recipe, format_type=payload['format_type'],
        language=payload['language'], expected_hash=recipe_hash)
    v = resolve_visual(recipe)
    width = v['width'] - 2 * v['margin']
    available_height = v['height'] - 2 * v['margin'] - v['branding_zone']
    for size in v['font_sizes']:
        line_height = math.ceil(size * v['line_height_ratio'])
        gap = line_height * v['paragraph_spacing_ratio']
        try:
            groups = [_wrap(b, size=size, width=width, metrics=metrics) for b in payload['body_blocks']]
        except PieceContractError as exc:
            if exc.detail == 'unbreakable_line':
                continue
            raise
        line_count = sum(len(group) for group in groups)
        height = line_count * line_height + (len(groups) - 1) * gap
        if height > available_height or any(m.bottom - m.top > line_height for g in groups for _, m in g):
            continue
        # Center the complete composition in the reserved content zone. Every
        # line retains its exact substring; layout does not rewrite text.
        top = v['margin'] + (available_height - height) / 2
        lines = []
        for index, group in enumerate(groups):
            for line, m in group:
                x = v['margin'] - min(0, m.left)
                if v['alignment'] == 'center':
                    x += (width - _width(m)) / 2
                baseline = top + (line_height - (m.bottom - m.top)) / 2 - m.top
                if (x + m.left < v['margin'] - 0.01 or x + m.right > v['width'] - v['margin'] + 0.01
                        or baseline + m.top < v['margin'] - 0.01
                        or baseline + m.bottom > v['height'] - v['margin'] - v['branding_zone'] + 0.01):
                    raise _fail('ink_outside_content_zone')
                lines.append({'block_index': index, 'text': line, 'x': x, 'baseline': baseline,
                              'ink_box': [x + m.left, baseline + m.top, x + m.right, baseline + m.bottom]})
                top += line_height
            top += gap
        rebuilt = [''.join(l['text'] for l in lines if l['block_index'] == i) for i in range(len(groups))]
        if rebuilt != payload['body_blocks']:
            raise _fail('text_loss')
        return {'layout_state': 'fit', 'renderer_profile': metrics.profile_id,
                'piece_text_hash': candidate['piece_text_hash'], 'visual_recipe_hash': recipe_hash,
                'width': v['width'], 'height': v['height'], 'font_px': size,
                'font_floor_px': v['font_sizes'][-1], 'line_height_px': line_height,
                'margin': v['margin'], 'branding_zone': v['branding_zone'],
                'colors': v['colors'], 'branding_mode': recipe['branding']['branding_mode'],
                'lines': lines, 'clipped': False, 'missing_glyph': False,
                'native_device_verified': False, 'record_effect': 0, 'quota_effect': 0}
    raise _fail('font_floor_overflow')


def fit_summary(layout: dict) -> dict:
    """Body-free summary; never serialize exact lines as monitoring metadata."""
    keys = ('layout_state', 'width', 'height', 'font_px', 'font_floor_px',
            'clipped', 'missing_glyph', 'native_device_verified', 'record_effect', 'quota_effect')
    return {**{key: layout[key] for key in keys}, 'line_count': len(layout['lines'])}
