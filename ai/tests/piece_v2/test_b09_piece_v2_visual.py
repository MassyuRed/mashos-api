"""B9 pure tests use declared synthetic metrics, not native device claims."""
from copy import deepcopy
import hashlib
import pytest
from piece_v2_contract import PieceContractError, canonical_sha256_hex
from piece_v2_generation import PieceSourceSnapshot, generate_piece_candidate
from piece_v2_visual import build_visual_recipe, validate_visual_recipe, resolve_visual
from piece_v2_layout import TextMeasurement, build_measured_layout, fit_summary


class Metrics:
    profile_id = 'synthetic-monospace-test-only'
    def graphemes(self, text):
        return list(text)
    def measure(self, text, font_px):
        width = len(text) * font_px
        return TextMeasurement(width, 0, -font_px * .8, width, font_px * .2)


def candidate(fmt='short_essay', text=None):
    if text is None:
        return generate_piece_candidate(PieceSourceSnapshot('test', 'saved', '1',
            '私が大切にしたいのは、自分で納得してから、自分の答えを選ぶことです。'),
            authenticated_owner_id='test', tier='premium', requested_format=fmt)
    payload = {'schema_version': 'piece.content_payload.v1', 'format_type': fmt,
        'body_blocks': [text], 'title': None, 'language': 'ja',
        'meaning_contract_version': 'piece.content_meaning.v1',
        'safety_contract_version': 'piece.public_safety_transformation.v1'}
    return {'content_payload': payload, 'piece_text': text,
            'piece_text_hash': hashlib.sha256(text.encode()).hexdigest()}


def render(c=None, r=None, metrics=None):
    c = c or candidate()
    r = r or build_visual_recipe(c['content_payload']['format_type'])
    return build_measured_layout(c, r, canonical_sha256_hex(r), metrics or Metrics())


@pytest.mark.parametrize('fmt', ['short_essay', 'quote', 'declaration'])
@pytest.mark.parametrize('ratio', ['4:5', '9:16'])
@pytest.mark.parametrize('theme', ['soft_paper', 'quiet_night'])
def test_all_catalog_combinations(fmt, ratio, theme):
    c = candidate(fmt)
    r = build_visual_recipe(fmt, tier='premium', aspect_ratio=ratio, theme=theme)
    p = render(c, r)
    assert ''.join(l['text'] for l in p['lines']) == c['piece_text']
    assert p['font_px'] >= p['font_floor_px']
    assert p['width'] == 1080 and p['height'] == (1350 if ratio == '4:5' else 1920)
    for l in p['lines']:
        left, top, right, bottom = l['ink_box']
        assert left >= p['margin'] and right <= p['width'] - p['margin']
        assert top >= p['margin'] and bottom <= p['height'] - p['margin'] - p['branding_zone']
    assert not p['native_device_verified']
    assert 'lines' not in fit_summary(p)


@pytest.mark.parametrize('kw', [dict(tier='free', theme='quiet_night'),
    dict(tier='plus', aspect_ratio='9:16'), dict(tier='free', branding='off'),
    dict(tier='plus', branding='required_small'), dict(tier='free', theme=''),
    dict(tier='premium', aspect_ratio='1:1')])
def test_choices_do_not_override_entitlements(kw):
    with pytest.raises(PieceContractError):
        build_visual_recipe('short_essay', **kw)


def test_saved_recipe_is_not_rewritten_on_later_downgrade():
    r = build_visual_recipe('short_essay', tier='premium', branding='off')
    assert validate_visual_recipe(r, format_type='short_essay', language='ja',
        expected_hash=canonical_sha256_hex(r)) == r
    visible = build_visual_recipe('short_essay', tier='premium')
    assert render(r=r)['lines'] == render(r=visible)['lines']


@pytest.mark.parametrize('change', [lambda r: r.update(extra='hidden'),
    lambda r: r['theme'].update(theme_version=2),
    lambda r: r['theme'].update(theme_version=True),
    lambda r: r['template'].update(template_id='focus_frame'),
    lambda r: r['theme'].update(url='https://example.com'),
    lambda r: r.update(visual_catalog_version='latest')])
def test_unknown_or_inconsistent_recipe_rejected(change):
    r = build_visual_recipe('short_essay')
    change(r)
    with pytest.raises(PieceContractError):
        render(r=r)


def test_hash_and_text_binding():
    c = candidate()
    c['piece_text'] += '改変'
    with pytest.raises(PieceContractError):
        render(c)


def test_missing_glyph_not_deleted():
    class Missing(Metrics):
        def measure(self, text, font_px):
            return TextMeasurement(10, 0, -10, 10, 0, False)
    with pytest.raises(PieceContractError, match='missing_glyph'):
        render(metrics=Missing())


def test_bad_segmenter_rejected():
    class Bad(Metrics):
        def graphemes(self, text): return [text[:-1]]
    with pytest.raises(PieceContractError, match='partition'):
        render(metrics=Bad())


def test_nonfinite_measurement_rejected():
    class Bad(Metrics):
        def measure(self, text, font_px): return TextMeasurement(float('nan'), 0, 0, 10, 10)
    with pytest.raises(PieceContractError, match='invalid_metrics'):
        render(metrics=Bad())


def test_font_floor_overflow_has_no_partial_image():
    class Tall(Metrics):
        def measure(self, text, font_px):
            return TextMeasurement(10, 0, -1000, 10, 1000)
    with pytest.raises(PieceContractError, match='font_floor_overflow'):
        render(metrics=Tall())


def test_long_text_does_not_change_ratio_or_truncate():
    c = candidate(text='納得してから進みたい。' * 40)
    with pytest.raises(PieceContractError):  # sentence envelope is not erased to make it fit
        render(c)


def test_kinsoku_and_exact_reconstruction():
    c = candidate(text='自分の気持ちも置き去りにせず、相手の考えも丁寧に聞いていたいと思う。')
    p = render(c)
    assert all(l['text'][0] not in '、。）」』' for l in p['lines'])
    assert ''.join(l['text'] for l in p['lines']) == c['piece_text']


def test_profiles_and_catalog_not_mutated():
    r = build_visual_recipe('short_essay')
    a = resolve_visual(r)
    a['colors']['text'] = '#000000'
    assert resolve_visual(r)['colors']['text'] == '#111827'
    metrics = Metrics(); metrics.profile_id = ''
    with pytest.raises(PieceContractError, match='profile'):
        render(metrics=metrics)


def test_short_final_line_is_balanced_without_deletion():
    c = candidate(text='まだ迷っているので、今は答えを急がないと思っている。')
    p = render(c)
    assert len(p['lines'][-1]['text']) > 2
    assert ''.join(l['text'] for l in p['lines']) == c['piece_text']
