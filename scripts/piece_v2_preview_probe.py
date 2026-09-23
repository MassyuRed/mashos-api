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
import math
import unicodedata
from pathlib import Path
import sys


class TabAwareMetrics:
    """Development-only tab4-v1 policy shared by measurement and drawing.

    A tab advances to the next stop spaced by the renderer's measured four
    spaces, relative to the current line origin. It is not a missing glyph
    or a replacement string. Raw line text, graphemes and canonical hashes
    are unchanged. Other C0/C1 controls are unsupported, not silently hidden.
    This policy is not an iOS/Android renderer or a product export contract.
    """

    def __init__(self, base):
        self.base = base
        self.profile_id = base.profile_id + '-tab4-v1'

    def graphemes(self, text):
        return self.base.graphemes(text)

    def font(self, size):
        return self.base.font(size)

    @lru_cache(maxsize=8192)
    def _plan(self, text, font_px):
        from piece_v2_layout import TextMeasurement, _fail, _measure

        def fail(reason):
            raise _fail(reason)

        if any(unicodedata.category(c) == 'Cc' and c != '\t' for c in text):
            fail('unsupported_control_character')
        if '\t' not in text:
            return ((text, 0.0),), _measure(self.base, text, font_px)
        interval = _measure(self.base, '    ', font_px).advance
        if interval <= 0:
            fail('invalid_tab_interval')
        runs, boxes = [], []
        x = 0.0
        parts = text.split('\t')
        for index, part in enumerate(parts):
            if part:
                m = _measure(self.base, part, font_px)
                runs.append((part, x))
                if m.right > m.left and m.bottom > m.top:
                    boxes.append((x + m.left, m.top, x + m.right, m.bottom))
                x += m.advance
                if not math.isfinite(x):
                    fail('invalid_metrics')
            if index < len(parts) - 1:
                runs.append(('\t', x))
                stop = (math.floor(x / interval) + 1) * interval
                if not math.isfinite(stop) or stop <= x:
                    fail('invalid_tab_interval')
                x = stop
        bounds = (min(b[0] for b in boxes), min(b[1] for b in boxes),
                  max(b[2] for b in boxes), max(b[3] for b in boxes)) if boxes else (0, 0, 0, 0)
        return tuple(runs), TextMeasurement(x, *bounds)

    def measure(self, text, font_px):
        return self._plan(text, font_px)[1]

    def draw_text(self, draw, position, text, *, font_px, fill):
        # Resolve the entire plan before drawing: a missing later glyph must
        # not leave a partially rendered line that could be mistaken for fit.
        runs, _ = self._plan(text, font_px)
        font = self.font(font_px)
        for run, offset in runs:
            if run != '\t':
                draw.text((position[0] + offset, position[1]), run,
                          font=font, fill=fill, anchor='ls')


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
    metrics = TabAwareMetrics(FontMetrics())
    output = args.output_dir.resolve()
    if output.exists() and any(output.iterdir()):
        parser.error('output directory must be empty; preserve earlier evidence separately')
    output.mkdir(parents=True, exist_ok=True)
    cases = [
        ('choice', '私が大切にしたいのは、早く決めることより、自分で納得して選ぶことです。まだ迷っているので、今は答えを急がない。'),
        ('conversation', '私が望んでいるのは、たくさんの人に分かってもらうことではなく、近くにいる人と落ち着いて話すことです。'),
        ('solitude', '私が大切にしたいのは、ひとりで静かに過ごす時間です。人と会いたくないわけではない。'),
        ('learning', '私が選びたいのは、間違えない方法だけを探すことより、小さく試して確かめることです。分からないところは、分からないままにせずに聞きたい。'),
        ('schedule', '予定を詰めると、一人で過ごす時間が足りなくなる。人と会う時間も私には大切だ。私は自分の調子に合わせて、無理のない予定を選びたい。'),
        ('self_paced_choice', 'すぐに決めると、気持ちが追いつかないことがある。迷う時間も私には必要だ。私は速さだけで答えを決めず、自分で納得できる選び方を続けたい。'),
        ('walking', '長く歩くと、疲れてしまうこともある。新しい景色を見る楽しさも残っている。私は体調に余裕があるときに、知らない道も歩いてみたい。'),
        ('uncertainty', '今はまだ、考えが変わるかもしれない。人の意見を聞かないわけではない。私は迷いを隠して、決まった答えのようには話したくない。'),
        ('single_intent', '私は自分で納得できるまで、焦らずに自分の答えを考えたい。'),
        ('initial_intent', '私は自分で納得してから答えを決めたい。昨日は時間が足りなかった。まだ迷っている。'),
        ('middle_intent', '昨日は時間が足りなかった。私は自分で納得してから答えを決めたい。まだ迷っている。'),
        ('role_abstraction', '友人の佐藤さんと話した。私は自分で納得してから答えを決めたい。'),
        ('role_qualification', '昨日は上司の田中さんに相談しなかった。私は気持ちが整理できたら、自分の考えを伝えたい。まだ、いつ話すかは決めていない。'),
        ('role_reference', '同僚の山田さんと話した。山田さんには、まだ結論を伝えていない。私は答えを急がず、自分の考えを整理したい。'),
        ('reference_time', '私が大切にしたいのは、ひとりで静かに過ごす時間です。その時間を持てた日は、気持ちに余裕があった。'),
        ('reference_action', '私が大切にしたいのは、自分で納得して選ぶことです。そのことを人に押しつけたいわけではない。'),
        ('reference_object', '私が大切にしているのは、自分の手で長く使ってきたものです。このものには、使いながら直した跡が残っている。'),
        ('reference_condition', '私が望んでいるのは、家族と落ち着いて話す時間です。その時間が取れたら、私は近況を伝えたい。まだ、日程は決めていない。'),
        ('reference_role', '私が大切にしたいのは、友人の佐藤さんと落ち着いて話す時間です。その時間が持てなかった昨日は、少し寂しかった。まだ、いつ会うかは決めていない。'),
        ('reference_chain', '私が大切にしたいのは、一人で考えを整理する時間です。その時間は、昨日は取れなかった。私はその時間を毎日少しでも持ちたい。'),
        ('reference_context', '今週は予定が重なっていた。私が大切にしたいのは、家で静かに過ごす時間です。この時間を確保できるかは、まだ分からない。'),
        ('value_comparison', '私にとって大切なのは、早く答えることより、自分で納得して選ぶことです。まだ、答えは決めていない。'),
        ('preference_contrast', '私が好きなのは、にぎやかな場所で話すことではなく、一人ずつゆっくり話すことだ。人と会いたくないわけではない。'),
        ('negative_value', '私にとって必要ではないのは、すぐに結論を出すことだ。今は考えを整理する時間を残している。'),
        ('past_role', '私にとって大切だったのは、友人の佐藤さんと毎日話す時間だ。今も同じ頻度で会いたいとは限らない。'),
        ('conditional_value', '私にとって重要なのは、気持ちに余裕があるときに、家族の話を聞くことだ。余裕がない日は無理をしない。'),
        ('context_preference', '昨日は答えを急いでしまった。私が苦手なのは、考える間もなく結論を伝えることです。まだ、話す順番は決めていない。'),
        ('tentative_value', '私にとって必要かもしれないのは、一人でゆっくり考える時間だ。まだ、自分でもよく分からない。'),
        ('value_noun', '私にとって大切なのは、対話です。対話が続けば、考えを確かめ直せる。'),
        ('scope_reason', '集中できる時間が少ないので、私は朝の予定を少し減らしたい。'),
        ('scope_past_reason', '友人の佐藤さんと昨日は話せなかったので、私は次に会うときは落ち着いて話したい。まだ、会う日は決めていない。'),
        ('scope_conditional_role', '友人の佐藤さんが時間を取れるなら、私は無理のない日にゆっくり話したい。まだ、返事はもらっていない。'),
        ('scope_negative', 'まだ気持ちが落ち着かないなら、私は無理に話を続けたくない。'),
        ('scope_uncertain_reason', '明日は疲れているかもしれないので、私は予定を詰め込みたくない。'),
        ('scope_reading', '明日の朝に時間が取れるならば、私は静かな場所で少し本を読みたい。'),
        ('scope_context', '昨日は上司の田中さんと話した。気持ちが整理できるなら、私は田中さんに自分の考えを伝えたい。ただし、まだ何を伝えるかは決めていない。'),
        ('scope_comparison', '少し身軽になれたので、私は旅に出る前の鳥みたい。'),
        ('linked_value_condition', '私にとって大切なのは、友人の佐藤さんと落ち着いて話す時間です。その時間が取れるなら、私は急がずに気持ちを伝えたい。まだ、会う日は決めていない。'),
        ('linked_preference_condition', '僕が好きなのは、小さく試して確かめることです。そのことを続けられるなら、僕は焦らずに学びたい。すぐに答えが出るとは限らない。'),
        ('linked_negative_value', '私にとって必要ではないのは、すぐに結論を出すことだ。そのことを相手にも求めたいわけではない。'),
        ('linked_past_value', '私にとって大切だったのは、家族と毎日話す時間だ。この時間は昨日だけで、毎日あるわけではない。'),
        ('linked_tentative_reason', '私にとって必要かもしれないのは、一人で考えを整理する時間だ。その時間がまだ足りないので、私は答えを急ぎたくない。まだ、自分でもよく分からない。'),
        ('linked_context_preference', '今週は予定が重なっていた。私が好きなのは、家で静かに過ごす時間です。この時間を確保できるかは、まだ分からない。'),
        ('linked_distinct_targets', '私にとって大切なのは、家で静かに過ごす時間です。私が大切にしたいのは、自分で納得して選ぶことです。その時間が取れるなら、私は焦らずに考えたい。'),
        ('linked_object_reservation', '私が好きなのは、自分の手で長く使ってきたものです。このものには、使いながら直した跡が残っている。誰にでも勧めたいわけではない。'),
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
                metrics.draw_text(draw, at, line['text'], font_px=layout['font_px'],
                                  fill=layout['colors']['text'])
                metrics.draw_text(ink, at, line['text'], font_px=layout['font_px'], fill=255)
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
        'public_safety_complete': False, 'cmee_piece_consumer_connected': True,
        'meaning_scope': 'source_bound_personal_evaluation_nominal_reference_and_marked_clause_scope_not_general_inference',
        'source_retrieval_connected': False, 'records': records, 'negative': negative}
    (output / 'probe_results.private.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    for item in records[::2]:
        print(item['case'], '\nINPUT:', item['source'], '\nOUTPUT:', item['candidate']['piece_text'], '\n')
    print(f'{len(records)} PNGs; exact block reconstruction and actual ink bounds verified; native acceptance: no')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
