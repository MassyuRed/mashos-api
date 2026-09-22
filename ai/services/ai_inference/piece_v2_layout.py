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


def _script_run_kind(cluster: str) -> str:
    """A soft visual run hint, not Japanese word/meaning segmentation.

    Inspect only the first scalar of a renderer-owned grapheme. Variation
    selectors, combining marks and halfwidth voicing stay in that grapheme.
    Hiragana and mixed-script word boundaries are deliberately not inferred.
    """
    char = cluster[0]
    name = unicodedata.name(char, '')
    if name.startswith(('CJK UNIFIED IDEOGRAPH-', 'CJK COMPATIBILITY IDEOGRAPH-')):
        return 'han'
    if (name.startswith(('KATAKANA LETTER ', 'HALFWIDTH KATAKANA LETTER '))
            or char in 'ーｰヽヾ'):
        return 'katakana'
    return ''


def _kana_attachment_breaks(clusters: list[str], script_runs: list[str]) -> list[bool]:
    """Soft attachment of a written Han/Katakana run to following hiragana.

    Keep okurigana and following kana together when the existing line-count,
    script-run and sentence-head preferences permit it. This is not lexical
    segmentation: a hiragana-to-Han transition may still be inside a compound.
    Punctuation, spaces, Latin text and other scripts reset the attachment.
    No grapheme is split, joined, normalized or declared unbreakable here.
    """
    attached = False
    boundaries = [False] * (len(clusters) + 1)
    for index, (cluster, kind) in enumerate(zip(clusters, script_runs, strict=True)):
        if unicodedata.name(cluster[0], '').startswith('HIRAGANA LETTER '):
            boundaries[index] = attached
        else:
            attached = kind in ('han', 'katakana')
    return boundaries


_SHORT_KANA_BRIDGES = frozenset('いきぎしじちぢびぴみりえけげせぜねべぺめれ')


def _kana_bridge_breaks(clusters: list[str], script_runs: list[str]) -> list[bool]:
    """Soft visual hint for one short kana between a written run and Han.

    This joins neither text nor words. The selected kana cover short written
    stem bridges, while common case/topic particles and te/de links are not
    admitted. Longer hiragana sequences and general compound boundaries are
    not inferred. Existing line-count, run, orphan and kana-attachment costs
    all take precedence; overwide sequences remain freely breakable.
    """
    boundaries = [False] * (len(clusters) + 1)
    for index in range(2, len(clusters)):
        # Compare the complete renderer grapheme canonically: decomposed
        # voiced/semi-voiced kana must use the same existing bridge hint.
        # Keep the original clusters for measurement, layout and text hashes.
        bridge = unicodedata.normalize('NFC', clusters[index - 1])[0]
        boundaries[index] = (script_runs[index] == 'han'
                             and script_runs[index - 2] in ('han', 'katakana')
                             and bridge in _SHORT_KANA_BRIDGES)
    return boundaries


def _fitting_bridge_run_breaks(clusters: list[str], script_runs: list[str],
                               kana_attachments: list[bool], kana_bridges: list[bool],
                               *, size: int, width: int, metrics: RendererMetrics) -> list[bool]:
    """Prefer intact, measured-to-fit mixed-script runs over fewer lines.

    Use only the existing short-kana bridge and attachment hints, not a word
    dictionary or a source/fixture selector. A maximal connected run must
    contain a bridge; ordinary particles and long kana-to-Han links do not
    join runs. Overwide runs keep the existing freely breakable preferences.
    Include adjacent kinsoku punctuation in the fit measurement: a run that
    fits alone may not fit together with its required opening/closing marks.
    These remain soft costs, never new line prohibitions or text mutations.
    """
    n = len(clusters)
    boundaries = [False] * (n + 1)
    start = 0
    has_bridge = False
    for end in range(1, n + 1):
        connected = end < n and (kana_attachments[end] or kana_bridges[end]
            or bool(script_runs[end - 1]) and script_runs[end - 1] == script_runs[end])
        if connected:
            has_bridge = has_bridge or kana_bridges[end]
            continue
        if has_bridge:
            left, right = start, end
            while left and clusters[left - 1][-1] in _NO_END:
                left -= 1
            while right < n and clusters[right][0] in _NO_START:
                right += 1
            measured = _measure(metrics, ''.join(clusters[left:right]), size)
            if _width(measured) <= width:
                for boundary in range(start + 1, end):
                    boundaries[boundary] = True
        start, has_bridge = end, False
    return boundaries


def _fitting_determiner_run_breaks(clusters: list[str], script_runs: list[str],
                                  *, size: int, width: int,
                                  metrics: RendererMetrics) -> list[bool]:
    """Soft cohesion for a delimited determiner and its following written run.

    Only この/その/あの/どの at a paragraph start or after an explicit
    punctuation/space boundary qualify. Never match inside another word or
    infer a referent. Prefer including a complete following hiragana run
    of one or two renderer graphemes, so a short tail is not stranded on the
    next line. This is a written-run hint, not a particle/word parser: never
    take just the beginning of a longer kana run. Measure the expanded form
    with required kinsoku marks; if it is overwide, retain the original
    determiner-plus-Han/Katakana preference when that smaller form fits.
    When expanded tails are used, give other fitting short kana endings in
    this paragraph the same preference, rather than moving the cut into a
    different short ending. Vertical capacity can still require a cut.
    """
    boundaries = [False] * (len(clusters) + 1)
    expanded_tail = False
    delimiters = _NO_END | frozenset('、。，．？！!?：；:;')
    for start in range(len(clusters) - 2):
        if start and not (clusters[start - 1][-1].isspace()
                          or clusters[start - 1][-1] in delimiters):
            continue
        # Normalize only the comparison view; render the untouched graphemes.
        prefix = unicodedata.normalize('NFC', ''.join(clusters[start:start + 2]))
        if prefix not in ('この', 'その', 'あの', 'どの'):
            continue
        kind = script_runs[start + 2]
        if kind not in ('han', 'katakana'):
            continue
        end = start + 3
        while end < len(clusters) and script_runs[end] == kind:
            end += 1
        tail_end = end
        while (tail_end < len(clusters) and unicodedata.name(
                clusters[tail_end][0], '').startswith('HIRAGANA LETTER ')):
            tail_end += 1
        ends = [end]
        if 1 <= tail_end - end <= 2:
            ends.insert(0, tail_end)
        for candidate_end in ends:
            left, right = start, candidate_end
            while left and clusters[left - 1][-1] in _NO_END:
                left -= 1
            while right < len(clusters) and clusters[right][0] in _NO_START:
                right += 1
            if _width(_measure(metrics, ''.join(clusters[left:right]), size)) <= width:
                for boundary in range(start + 1, candidate_end):
                    boundaries[boundary] = True
                expanded_tail = expanded_tail or candidate_end > end
                break
    if expanded_tail:
        # Protect equivalent short written endings in the same composition.
        # No source labels, word dictionary, or hard line prohibition is used.
        start = 0
        while start < len(clusters):
            kind = script_runs[start]
            if kind not in ('han', 'katakana'):
                start += 1
                continue
            end = start + 1
            while end < len(clusters) and script_runs[end] == kind:
                end += 1
            tail_end = end
            while (tail_end < len(clusters) and unicodedata.name(
                    clusters[tail_end][0], '').startswith('HIRAGANA LETTER ')):
                tail_end += 1
            if 1 <= tail_end - end <= 2:
                left, right = start, tail_end
                while left and clusters[left - 1][-1] in _NO_END:
                    left -= 1
                while right < len(clusters) and clusters[right][0] in _NO_START:
                    right += 1
                if _width(_measure(metrics, ''.join(clusters[left:right]), size)) <= width:
                    for boundary in range(start + 1, tail_end):
                        boundaries[boundary] = True
            start = tail_end
    return boundaries


def _fitting_long_kana_run_breaks(clusters: list[str], script_runs: list[str],
                                 existing_fitting_runs: list[bool], *, size: int, width: int,
                                 metrics: RendererMetrics) -> list[bool]:
    """Soft cohesion for a complete written run with a longer kana tail.

    A maximal Han/Katakana run followed by at least three hiragana graphemes
    is measured as a whole, with required kinsoku punctuation. Keep that
    whole run together when it fits instead of cutting a longer written
    ending merely to reduce line count. This is not lexical analysis: the
    tail can include particles, inflection, degree or modality, and none of
    those meanings is inferred. Never protect only a prefix of an overwide
    tail. Short tails retain their existing determiner/bridge preferences.
    Existing bridge/determiner scopes take precedence: do not extend or
    overlap one with this additional hint. All hints remain soft under the
    shared vertical-capacity allocator.
    """
    boundaries = [False] * (len(clusters) + 1)
    start = 0
    while start < len(clusters):
        kind = script_runs[start]
        if kind not in ('han', 'katakana'):
            start += 1
            continue
        end = start + 1
        while end < len(clusters) and script_runs[end] == kind:
            end += 1
        tail_end = end
        while (tail_end < len(clusters) and unicodedata.name(
                clusters[tail_end][0], '').startswith('HIRAGANA LETTER ')):
            tail_end += 1
        if (tail_end - end >= 3
                and not any(existing_fitting_runs[start:tail_end])):
            left, right = start, tail_end
            while left and clusters[left - 1][-1] in _NO_END:
                left -= 1
            while right < len(clusters) and clusters[right][0] in _NO_START:
                right += 1
            if _width(_measure(metrics, ''.join(clusters[left:right]), size)) <= width:
                for boundary in range(start + 1, tail_end):
                    boundaries[boundary] = True
        start = tail_end
    return boundaries


_WrapScore = tuple[int, int, int, int, int, int, int, float]
_MeasuredRows = list[tuple[str, TextMeasurement]]
_WrapSolutions = dict[int, tuple[_WrapScore, _MeasuredRows]]


def _wrap_solutions(text: str, *, size: int, width: int, metrics: RendererMetrics,
                    prefer_fitting_bridges: bool = True, max_lines: int | None = None,
                    line_height: int | None = None) -> _WrapSolutions:
    """Keep the old optimum, or the best measured path for each line count.

    A constrained suffix needs its line count as well as its position: keeping
    only its unconstrained optimum can discard a readable path that fits the
    remaining vertical space. Measurements and costs are shared by both modes.
    """
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
    # First keep short-bridge, determiner and long-kana runs intact when their
    # complete measured form
    # (including required punctuation) fits. A readable extra line is better
    # than cutting such a run merely to achieve the minimum line count.
    # Otherwise prefer the minimum line count, then preserve ASCII runs, then visible
    # Han/Katakana runs and the letter after a sokuon, then avoid a lone
    # character after a sentence mark, then avoid splitting attached hiragana.
    # Short kana bridges are preferred next, without parsing Japanese words.
    # Balance every line only after these readability preferences. No break
    # is prohibited by a run hint: overwide runs still split at a renderer's
    # grapheme boundary instead of shrinking, padding or refusing the body.
    n = len(clusters)
    word_clusters = [c[0].isascii() and c[0].isalnum() for c in clusters]
    script_runs = [_script_run_kind(c) for c in clusters]
    kana_attachments = _kana_attachment_breaks(clusters, script_runs)
    kana_bridges = _kana_bridge_breaks(clusters, script_runs)
    fitting_bridges = (_fitting_bridge_run_breaks(
        clusters, script_runs, kana_attachments, kana_bridges,
        size=size, width=width, metrics=metrics) if prefer_fitting_bridges else [False] * (n + 1))
    fitting_determiners = _fitting_determiner_run_breaks(
        clusters, script_runs, size=size, width=width, metrics=metrics)
    fitting_runs = [bridge or determiner for bridge, determiner in
                    zip(fitting_bridges, fitting_determiners, strict=True)]
    fitting_long_kana = _fitting_long_kana_run_breaks(
        clusters, script_runs, fitting_runs, size=size, width=width, metrics=metrics)
    fitting_runs = [prior or long_kana for prior, long_kana in
                    zip(fitting_runs, fitting_long_kana, strict=True)]
    has_fitting_run = any(fitting_runs)
    has_long_kana_run = any(fitting_long_kana)
    costs = {n: {0: (0, 0, 0, 0, 0, 0, 0, 0.0)}}
    choices = {}
    for start in range(n - 1, -1, -1):
        best = {}
        for end in range(start + 1, n + 1):
            if end not in costs:
                continue
            if end < n and (clusters[end][0] in _NO_START or clusters[end - 1][-1] in _NO_END):
                continue
            part = ''.join(clusters[start:end])
            measured = _measure(metrics, part, size)
            measured_width = _width(measured)
            if (measured_width > width or line_height is not None
                    and measured.bottom - measured.top > line_height):
                continue
            split = int(end < n and word_clusters[end - 1] and word_clusters[end])
            script_split = int(end < n and (
                bool(script_runs[end - 1]) and script_runs[end - 1] == script_runs[end]
                or clusters[end - 1][-1] in 'っッ'
                and unicodedata.category(clusters[end][0]).startswith('L')))
            # The source's sentence mark is enough to detect this orphan;
            # Japanese-only text need not contain an ASCII word to benefit.
            head_orphan = int(end < n and end >= 2
                              and clusters[end - 2][-1] in '。！？!?')
            # Do not buy cohesion by stranding a single grapheme on its own.
            # With no fitting run this tier stays zero, preserving the
            # previous ordered preferences exactly.
            singleton = int(has_fitting_run and end - start == 1)
            # A longer protected ending must not merely move the defect into
            # the first grapheme of the next sentence. Reuse the existing
            # written sentence-head signal; infer no words or new meaning.
            long_kana_orphan = int(has_long_kana_run and head_orphan)
            for tail_count, tail_cost in costs[end].items():
                count = tail_count + 1
                if max_lines is not None and count > max_lines:
                    continue
                (cohesion_cost, _, word_splits, script_splits, head_orphans,
                 kana_splits, bridge_splits, penalty) = tail_cost
                score = (cohesion_cost + int(fitting_runs[end]) + singleton + long_kana_orphan,
                         count, word_splits + split, script_splits + script_split,
                         head_orphans + head_orphan, kana_splits + int(kana_attachments[end]),
                         bridge_splits + int(kana_bridges[end]),
                         penalty + (width - measured_width) ** 2)
                if count not in best or score < best[count]:
                    best[count] = score
                    choices[start, count] = (end, tail_count, part, measured)
        if best:
            if max_lines is None:
                count = min(best, key=best.get)
                best = {count: best[count]}
            costs[start] = best
    if 0 not in costs:
        raise _fail('unbreakable_line')
    solutions = {}
    for count, score in costs[0].items():
        out, start, remaining = [], 0, count
        while start < n:
            end, remaining, part, measured = choices[start, remaining]
            out.append((part, measured))
            start = end
        solutions[count] = (score, out)
    return solutions


def _wrap(text: str, *, size: int, width: int, metrics: RendererMetrics,
          prefer_fitting_bridges: bool = True) -> list[tuple[str, TextMeasurement]]:
    solutions = _wrap_solutions(text, size=size, width=width, metrics=metrics,
                               prefer_fitting_bridges=prefer_fitting_bridges)
    return min(solutions.values(), key=lambda item: item[0])[1]


def _fit_measured_groups(blocks: list[str], *, size: int, width: int,
                         line_height: int, gap: float, available_height: float,
                         metrics: RendererMetrics) -> list[_MeasuredRows] | None:
    """Allocate the actual line budget across intact source-order paragraphs.

    Only used when the existing unconstrained layout does not fit. Minimize
    the SAME ordered costs, summed across paragraphs, within the shared line
    budget. Do not disable every paragraph's cohesion, shrink first, remove
    text, guess words, or change recipe/paragraph spacing to obtain a fit.
    """
    paragraph_height = (len(blocks) - 1) * gap
    max_lines = math.floor((available_height - paragraph_height) / line_height)
    # Subtraction/division can round an exact fit just below an integer.
    # Check with the same forward height expression used by the compositor;
    # do not add an epsilon that could admit genuinely overflowing content.
    if (max_lines + 1) * line_height + paragraph_height <= available_height:
        max_lines += 1
    if max_lines * line_height + paragraph_height > available_height:
        max_lines -= 1
    if max_lines < len(blocks):
        return None
    choices = {0: ((0, 0, 0, 0, 0, 0, 0, 0.0), [])}
    for index, block in enumerate(blocks):
        remaining_blocks = len(blocks) - index - 1
        block_limit = max_lines - min(choices) - remaining_blocks
        try:
            solutions = _wrap_solutions(block, size=size, width=width, metrics=metrics,
                                       max_lines=block_limit, line_height=line_height)
        except PieceContractError as exc:
            if exc.detail == 'unbreakable_line':
                return None
            raise
        next_choices = {}
        for used, (score, groups) in sorted(choices.items()):
            for count, (cost, rows) in sorted(solutions.items()):
                total = used + count
                if total + remaining_blocks > max_lines:
                    continue
                combined = tuple(a + b for a, b in zip(score, cost, strict=True))
                if total not in next_choices or combined < next_choices[total][0]:
                    next_choices[total] = (combined, groups + [rows])
        if not next_choices:
            return None
        choices = next_choices
    return min(choices.values(), key=lambda item: item[0])[1]


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
            groups = [_wrap(b, size=size, width=width, metrics=metrics)
                      for b in payload['body_blocks']]
        except PieceContractError as exc:
            if exc.detail == 'unbreakable_line':
                continue
            raise
        height = sum(map(len, groups)) * line_height + (len(groups) - 1) * gap
        if height > available_height or any(
                m.bottom - m.top > line_height for g in groups for _, m in g):
            groups = _fit_measured_groups(
                payload['body_blocks'], size=size, width=width, metrics=metrics,
                line_height=line_height, gap=gap, available_height=available_height)
            if groups is None:
                continue
            height = sum(map(len, groups)) * line_height + (len(groups) - 1) * gap
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
