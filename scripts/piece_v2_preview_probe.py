#!/usr/bin/env python3
"""Development-only PNG probe for B8/B9, NOT a backend/native export owner.

Uses already installed Pillow, regex and fontTools in the development host.
Nothing is added to application dependencies. No font is bundled or copied.
Production remains disabled. Linux metrics cannot be reused on iOS/Android.
"""
from __future__ import annotations
import argparse
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--font-file', type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'ai/services/ai_inference'))
    from PIL import Image, ImageDraw, ImageFont, PngImagePlugin
    import PIL
    import regex
    from fontTools.ttLib import TTFont
    from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate
    from piece_v2_contract import PieceContractError, canonical_sha256_hex
    from piece_v2_visual import build_visual_recipe
    from piece_v2_layout import TextMeasurement, build_measured_layout, fit_summary

    font_file = args.font_file.resolve(strict=True)
    font_hash = hashlib.sha256(font_file.read_bytes()).hexdigest()
    glyphs = set(TTFont(font_file, fontNumber=0).getBestCmap())
    class FontMetrics:
        profile_id = f'linux-development-pillow-{PIL.__version__}-font-{font_hash}-face0'
        def graphemes(self, text):
            return regex.findall(r'\X', text)
        @lru_cache(maxsize=32)
        def font(self, size):
            return ImageFont.truetype(str(font_file), size, index=0)
        @lru_cache(maxsize=8192)
        def measure(self, text, font_px):
            font = self.font(font_px)
            bbox = font.getbbox(text, anchor='ls')
            # Variation selectors and ZWJ are shaping controls, not standalone
            # glyphs. Missing visible glyphs never become a success placeholder.
            missing = any(ord(c) not in glyphs and not (c == '\u200d' or 0xFE00 <= ord(c) <= 0xFE0F) for c in text)
            return TextMeasurement(float(font.getlength(text)), *map(float, bbox), not missing)
    metrics = FontMetrics()
    output = args.output_dir.resolve()
    if output.exists() and any(output.iterdir()):
        parser.error('output directory must be empty; preserve earlier evidence separately')
    output.mkdir(parents=True, exist_ok=True)
    cases = [
        ('choice', '私が大切にしたいのは、早く決めることより、自分で納得して選ぶことです。まだ迷っているので、今は答えを急がない。'),
        ('conversation', '私が望んでいるのは、たくさんの人に分かってもらうことではなく、近くにいる人と落ち着いて話すことです。'),
        ('solitude', '私が大切にしたいのは、ひとりで静かに過ごす時間です。人と会いたくないわけではない。'),
        ('learning', '私が選びたいのは、間違えない方法だけを探すことより、小さく試して確かめることです。分からないところは、分からないままにせずに聞きたい。'),
    ]
    records = []
    # Dynamic ICC creation embeds a wall-clock timestamp. A fixed PNG sRGB
    # intent chunk declares the same color space without changing repeat bytes.
    png_info = PngImagePlugin.PngInfo()
    png_info.add(b'sRGB', b'\x00')
    for name, text in cases:
        c = generate_piece_candidate(PieceSourceSnapshot('synthetic-owner', name, '1', text),
                                     authenticated_owner_id='synthetic-owner')
        for ratio, theme in (('4:5', 'soft_paper'), ('9:16', 'quiet_night')):
            r = build_visual_recipe(c['format_type'], tier='premium', theme=theme, aspect_ratio=ratio)
            layout = build_measured_layout(c, r, canonical_sha256_hex(r), metrics)
            image = Image.new('RGB', (layout['width'], layout['height']), layout['colors']['canvas'])
            draw = ImageDraw.Draw(image)
            w, h = image.size
            draw.rounded_rectangle((36, 36, w - 36, h - 36), radius=24,
                                   fill=layout['colors']['surface'], outline=layout['colors']['border'], width=2)
            # Text and measurement use precisely the same face, size, baseline.
            mask = Image.new('L', image.size)
            ink = ImageDraw.Draw(mask)
            for line in layout['lines']:
                at = (line['x'], line['baseline'])
                font = metrics.font(layout['font_px'])
                draw.text(at, line['text'], font=font, fill=layout['colors']['text'], anchor='ls')
                ink.text(at, line['text'], font=font, fill=255, anchor='ls')
            box = mask.getbbox()
            m = layout['margin']
            assert box and box[0] >= m and box[1] >= m
            assert box[2] <= w - m and box[3] <= h - m - layout['branding_zone']
            if layout['branding_mode'] != 'off':
                draw.text((m, h - m), 'Cocolon', font=metrics.font(28),
                          fill=layout['colors']['branding'], anchor='ls')
            filename = f'{name}_{ratio.replace(":", "x")}.png'
            image.save(output / filename, format='PNG', pnginfo=png_info)
            records.append({'case': name, 'source': text, 'candidate': c,
                'visual_recipe': r, 'layout': layout, 'fit': fit_summary(layout),
                'actual_ink_box': list(box), 'file': filename,
                'sha256': hashlib.sha256((output / filename).read_bytes()).hexdigest()})
    negative = []
    for text in ('なんとなく。', '私が大切にしたいのは、user@example.com への連絡です。'):
        try:
            generate_piece_candidate(PieceSourceSnapshot('test', 'negative', '1', text), authenticated_owner_id='test')
        except PieceContractError as exc:
            negative.append({'source': text, 'state': 'unavailable', 'reason_code': exc.detail})
        else:
            raise AssertionError('negative example unexpectedly generated')
    report = {'scope': 'DEVELOPMENT_PROBE_NOT_NATIVE_ACCEPTANCE', 'renderer_profile': metrics.profile_id,
        'application_dependency_changes': 0, 'native_device_verified': False,
        'public_safety_complete': False, 'cmee_piece_consumer_connected': False,
        'source_retrieval_connected': False, 'records': records, 'negative': negative}
    (output / 'probe_results.private.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    for item in records[::2]:
        print(item['case'], '\nINPUT:', item['source'], '\nOUTPUT:', item['candidate']['piece_text'], '\n')
    print(f'{len(records)} PNGs; exact block reconstruction and actual ink bounds verified; native acceptance: no')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
