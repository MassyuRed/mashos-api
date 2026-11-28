"""B9 versioned visual recipe. No native, network, DB or export side effects."""
from __future__ import annotations

from copy import deepcopy
from collections.abc import Mapping
from piece_v2_contract import PieceContractError, canonical_sha256_hex

TEMPLATES = {'short_essay': 'essay_frame', 'quote': 'focus_frame', 'declaration': 'stance_frame'}
# Preserve the original tokens and identity of previously saved recipes.
THEMES = {
    'soft_paper': {'canvas': '#F6F1E8', 'surface': '#FFFDF8', 'text': '#111827',
                   'secondary': '#4B5563', 'accent': '#800020', 'border': '#D7D2C9',
                   'branding': '#800020', 'vector_end': '#FFFFFF'},
    'quiet_night': {'canvas': '#0B1120', 'surface': '#111827', 'text': '#F9FAFB',
                    'secondary': '#CBD5E1', 'accent': '#D4AF37', 'border': '#334155',
                    'branding': '#D4AF37', 'vector_end': '#1E293B'},
    'rose_paper': {'canvas': '#F5E5E7', 'surface': '#FFF6F6', 'text': '#352629',
                   'secondary': '#625054', 'accent': '#8D364D', 'border': '#D6B9BF', 'vector_end': '#FDF1F1',
                   'branding': '#8D364D'},
    'rose_berry': {'canvas': '#F5E5E7', 'surface': '#FFF6F6', 'text': '#702942',
                   'secondary': '#74485A', 'accent': '#832747', 'border': '#D6B9BF', 'vector_end': '#FDF1F1',
                   'branding': '#832747'},
    'sand_umber': {'canvas': '#EFE4CE', 'surface': '#FFF8EA', 'text': '#4D3223',
                   'secondary': '#6A5548', 'accent': '#774729', 'border': '#CDBA9A', 'vector_end': '#FAF0D8',
                   'branding': '#774729'},
    'sand_olive': {'canvas': '#EFE4CE', 'surface': '#FFF8EA', 'text': '#384322',
                   'secondary': '#515B40', 'accent': '#526027', 'border': '#CDBA9A', 'vector_end': '#FAF0D8',
                   'branding': '#526027'},
    'mist_slate': {'canvas': '#DDE8EE', 'surface': '#F4FAFD', 'text': '#263949',
                   'secondary': '#4C606F', 'accent': '#315D77', 'border': '#AFCCD9', 'vector_end': '#EBF5F9',
                   'branding': '#315D77'},
    'mist_teal': {'canvas': '#DDE8EE', 'surface': '#F4FAFD', 'text': '#174C48',
                  'secondary': '#43645F', 'accent': '#25685C', 'border': '#AFCCD9', 'vector_end': '#EBF5F9',
                  'branding': '#25685C'},
    'lavender_ink': {'canvas': '#E8E3F4', 'surface': '#FAF6FF', 'text': '#31294B',
                     'secondary': '#5F5272', 'accent': '#624683', 'border': '#CDC0DF', 'vector_end': '#F4ECFF',
                     'branding': '#624683'},
    'lavender_plum': {'canvas': '#E8E3F4', 'surface': '#FAF6FF', 'text': '#632D58',
                      'secondary': '#70536D', 'accent': '#7A3B6B', 'border': '#CDC0DF', 'vector_end': '#F4ECFF',
                      'branding': '#7A3B6B'},
    'forest_mint': {'canvas': '#102821', 'surface': '#19372D', 'text': '#E3F7ED',
                    'secondary': '#B9D9C9', 'accent': '#9ADBB8', 'border': '#3A6252', 'vector_end': '#24463C',
                    'branding': '#9ADBB8'},
    'ocean_ice': {'canvas': '#102336', 'surface': '#182F47', 'text': '#E3F3FC',
                  'secondary': '#B9D4E6', 'accent': '#9CD7F5', 'border': '#3A5973', 'vector_end': '#23435E',
                  'branding': '#9CD7F5'},
}
LEGACY_THEME_IDS = ('soft_paper', 'quiet_night')
THEME_IDS = tuple(THEMES)
ANDROID_BITMAP_RENDERER_VERSION = 'piece.rn_bitmap_renderer.android.v1'
EXPANDED_PALETTE_RENDERERS = frozenset(('piece.rn_bitmap_renderer.ios.v2', ANDROID_BITMAP_RENDERER_VERSION))
THEMES.update({
    'sage_paper': {'canvas': '#E5EEE0', 'surface': '#E5EEE0', 'text': '#273727',
                   'secondary': '#4A5D48', 'accent': '#4C674B', 'border': '#B4C6AC',
                   'branding': '#4C674B', 'vector_end': '#E5EEE0'},
    'peach_paper': {'canvas': '#F8E4D8', 'surface': '#F8E4D8', 'text': '#462D27',
                    'secondary': '#654941', 'accent': '#884834', 'border': '#D7B4A3',
                    'branding': '#884834', 'vector_end': '#F8E4D8'},
    'slate_paper': {'canvas': '#E3E7EF', 'surface': '#E3E7EF', 'text': '#293447',
                    'secondary': '#4B586C', 'accent': '#4C5F7A', 'border': '#B8C2D2',
                    'branding': '#4C5F7A', 'vector_end': '#E3E7EF'},
})
EDITOR_THEME_IDS = tuple(THEMES)
FONT_STYLE_IDS = ('system_readable', 'serif_readable')
TEXT_COLOR_IDS = ('neutral_ink',)
TEXT_ALIGNMENTS = ('left', 'center')
TEXT_SIZES = ('small', 'standard', 'large')
BACKGROUND_STYLES = ('solid', 'gradient')
DECORATED_BACKGROUND_STYLES = ('color_bands', 'color_wash', 'dot_pattern', 'stripe_pattern')
FRAME_STYLES = ('none', 'line', 'double_line')
ACCENT_STYLES = ('none', 'top_rule', 'corner_marks')
GRADIENT_ENDS = {'sage_paper': '#F5F8F0', 'peach_paper': '#FFF2EC', 'slate_paper': '#F3F5FA'}
DARK_THEME_IDS = frozenset({'quiet_night', 'forest_mint', 'ocean_ice'})
SCALES = {
    'short_essay': {'4:5': (48, 44, 40, 36), '9:16': (52, 48, 44, 40)},
    'quote': {'4:5': (72, 64, 56), '9:16': (80, 72, 64)},
    'declaration': {'4:5': (64, 56, 48), '9:16': (72, 64, 56)},
}
LINE_HEIGHT = {'short_essay': 1.55, 'quote': 1.35, 'declaration': 1.42}
CANVASES = {'4:5': (1080, 1350, 96, 72), '9:16': (1080, 1920, 108, 84)}


def require_piece_visual_selection(selection: Mapping, *, expanded_palette: bool,
                                   visual_editor: bool = False, visual_alignment: bool = False,
                                   visual_text_size: bool = False, visual_background_style: bool = False,
                                   visual_decorations: bool = False) -> None:
    """Guard client compatibility separately from the current plan."""
    themes = EDITOR_THEME_IDS if visual_editor else THEME_IDS if expanded_palette else LEGACY_THEME_IDS
    theme = selection['theme_id']
    if (theme is not None and theme not in themes
            or not visual_editor and ('font_style_id' in selection or 'text_color_id' in selection)
            or not visual_alignment and 'text_alignment' in selection
            or not visual_text_size and 'text_size' in selection
            or not visual_background_style and 'background_style' in selection
            or not visual_decorations and (
                selection.get('background_style') in DECORATED_BACKGROUND_STYLES
                or 'frame_style' in selection or 'accent_style' in selection)):
        raise PieceContractError('PIECE_VISUAL_SELECTION_NOT_ALLOWED')


def invalid() -> PieceContractError:
    return PieceContractError('PIECE_REQUEST_INVALID', 'visual_recipe')


def default_text_alignment(format_type: str) -> str:
    return 'center' if format_type == 'quote' else 'left'


def build_visual_recipe(format_type: str, *, tier: str = 'free', language: str = 'ja',
                        theme: str | None = None, aspect_ratio: str | None = None,
                        branding: str | None = None, font_style_id: str | None = None,
                        text_color_id: str | None = None, text_alignment: str | None = None,
                        text_size: str | None = None, background_style: str | None = None,
                        frame_style: str | None = None, accent_style: str | None = None) -> dict:
    if tier not in ('free', 'plus', 'premium') or format_type not in TEMPLATES:
        raise invalid()
    if language not in ('ja', 'en', 'mixed'):
        raise invalid()
    theme = 'soft_paper' if theme is None else theme
    aspect_ratio = '4:5' if aspect_ratio is None else aspect_ratio
    default_mark = 'required_small' if tier == 'free' else 'required_subtle'
    branding = default_mark if branding is None else branding
    font_style_id = FONT_STYLE_IDS[0] if font_style_id is None else font_style_id
    if (theme not in THEMES or aspect_ratio not in CANVASES
            or font_style_id not in FONT_STYLE_IDS
            or text_color_id is not None and text_color_id not in TEXT_COLOR_IDS
            or text_alignment is not None and (tier == 'free' or text_alignment not in TEXT_ALIGNMENTS)
            or text_size is not None and (tier == 'free' or text_size not in TEXT_SIZES)
            or background_style is not None and (
                tier != 'premium' or background_style not in (*BACKGROUND_STYLES, *DECORATED_BACKGROUND_STYLES))
            or frame_style is not None and (tier != 'premium' or frame_style not in FRAME_STYLES)
            or accent_style is not None and (tier != 'premium' or accent_style not in ACCENT_STYLES)
            or tier != 'premium' and (font_style_id != FONT_STYLE_IDS[0] or text_color_id is not None)
            or tier == 'free' and theme not in LEGACY_THEME_IDS
            or tier == 'free' and aspect_ratio != '4:5'
            or branding not in ((default_mark,) if tier == 'free' else (default_mark, 'off'))):
        raise invalid()
    font_style = {'font_style_id': font_style_id, 'font_style_version': 1}
    if text_color_id is not None:
        font_style['text_color_id'] = text_color_id
    if text_alignment is not None and text_alignment != default_text_alignment(format_type):
        font_style['text_alignment'] = text_alignment
    if text_size not in (None, 'standard'):
        font_style['text_size'] = text_size
    theme_settings = {'theme_id': theme, 'theme_version': 1}
    if background_style not in (None, 'solid'):
        theme_settings['background_style'] = background_style
    if frame_style not in (None, 'none'):
        theme_settings['frame_style'] = frame_style
    if accent_style not in (None, 'none'):
        theme_settings['accent_style'] = accent_style
    return {
        'visual_recipe_version': 'piece.visual_recipe.v1',
        'visual_catalog_version': 'piece.visual_catalog.v1',
        'format_type': format_type,
        'template': {'template_id': TEMPLATES[format_type], 'template_version': 1},
        'theme': theme_settings,
        'font_style': font_style,
        'aspect_ratio': aspect_ratio,
        'branding': {'branding_mode': branding, 'branding_mark_id': 'cocolon_text_mark',
                     'branding_mark_version': 1},
        'layout_policy_version': 'piece.long_text_layout.v1', 'language': language,
    }


def visual_selection_from_recipe(recipe: Mapping) -> dict:
    selection = {'theme_id': recipe['theme']['theme_id'], 'aspect_ratio': recipe['aspect_ratio'],
                 'branding_mode': recipe['branding']['branding_mode']}
    style = recipe['font_style']
    if style['font_style_id'] != FONT_STYLE_IDS[0]:
        selection['font_style_id'] = style['font_style_id']
    if 'text_color_id' in style:
        selection['text_color_id'] = style['text_color_id']
    if 'text_alignment' in style:
        selection['text_alignment'] = style['text_alignment']
    if 'text_size' in style:
        selection['text_size'] = style['text_size']
    for field in ('background_style', 'frame_style', 'accent_style'):
        if field in recipe['theme']:
            selection[field] = recipe['theme'][field]
    return selection


def build_selected_visual_recipe(format_type: str, *, tier: str, language: str,
                                 selection: Mapping) -> dict:
    return build_visual_recipe(format_type, tier=tier, language=language,
        theme=selection['theme_id'], aspect_ratio=selection['aspect_ratio'],
        branding=selection['branding_mode'], font_style_id=selection.get('font_style_id'),
        text_color_id=selection.get('text_color_id'), text_alignment=selection.get('text_alignment'),
        text_size=selection.get('text_size'), background_style=selection.get('background_style'),
        frame_style=selection.get('frame_style'), accent_style=selection.get('accent_style'))


def validate_visual_recipe(recipe: Mapping, *, format_type: str, language: str,
                           expected_hash: str) -> dict:
    """Validate saved identity without reapplying today's subscription tier.

    New candidate entitlements belong to build_visual_recipe; saved record
    entitlement binding remains B6. Never change saved branding on downgrade.
    """
    try:
        mark = recipe['branding']['branding_mode']
        implied_tier = 'free' if mark == 'required_small' else 'premium'
        expected = build_selected_visual_recipe(format_type, tier=implied_tier, language=language,
            selection=visual_selection_from_recipe(recipe))
        # bool is not an integer version. Canonical bytes/hash alone would not
        # compensate for Python's True == 1 when comparing nested mappings.
        for key, v in (('template', 'template_version'), ('theme', 'theme_version'),
                       ('font_style', 'font_style_version'), ('branding', 'branding_mark_version')):
            if type(recipe[key][v]) is not int:
                raise invalid()
        if dict(recipe) != expected or canonical_sha256_hex(expected) != expected_hash:
            raise invalid()
        return deepcopy(expected)
    except (KeyError, TypeError, AttributeError) as exc:
        raise invalid() from exc


def resolve_visual(recipe: Mapping) -> dict:
    """For an already validated recipe; returns copies, not mutable catalog refs."""
    fmt, ratio = recipe['format_type'], recipe['aspect_ratio']
    w, h, margin, brand_zone = CANVASES[ratio]
    theme = recipe['theme']['theme_id']
    colors = deepcopy(THEMES[theme])
    if recipe['font_style'].get('text_color_id') == 'neutral_ink':
        colors['text'] = '#F1F5F9' if theme in DARK_THEME_IDS else '#334155'
    sizes = SCALES[fmt][ratio]
    text_size = recipe['font_style'].get('text_size')
    if text_size == 'small':
        sizes = sizes[1:]
    elif text_size == 'large':
        sizes = (sizes[0] + (sizes[0] - sizes[1]), *sizes)
    visual = {'width': w, 'height': h, 'margin': margin, 'branding_zone': brand_zone,
            'font_sizes': list(sizes), 'line_height_ratio': LINE_HEIGHT[fmt],
            'paragraph_spacing_ratio': 0.65 if fmt == 'short_essay' else 0.0,
            'alignment': recipe['font_style'].get('text_alignment', default_text_alignment(fmt)),
            'colors': colors}
    if recipe['theme'].get('background_style') == 'gradient':
        visual['background_gradient'] = {'start': colors['surface'],
                                         'end': GRADIENT_ENDS.get(theme, colors['vector_end'])}
    return visual
