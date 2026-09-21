"""B9 versioned visual recipe. No native, network, DB or export side effects."""
from __future__ import annotations

from copy import deepcopy
from collections.abc import Mapping
from piece_v2_contract import PieceContractError, canonical_sha256_hex

TEMPLATES = {'short_essay': 'essay_frame', 'quote': 'focus_frame', 'declaration': 'stance_frame'}
# Exact tokens from Piece_Visual_Recipe_Contract_20260808, not a new theme.
THEMES = {
    'soft_paper': {'canvas': '#F6F1E8', 'surface': '#FFFDF8', 'text': '#111827',
                   'secondary': '#4B5563', 'accent': '#800020', 'border': '#D7D2C9',
                   'branding': '#800020', 'vector_end': '#FFFFFF'},
    'quiet_night': {'canvas': '#0B1120', 'surface': '#111827', 'text': '#F9FAFB',
                    'secondary': '#CBD5E1', 'accent': '#D4AF37', 'border': '#334155',
                    'branding': '#D4AF37', 'vector_end': '#1E293B'},
}
SCALES = {
    'short_essay': {'4:5': (48, 44, 40, 36), '9:16': (52, 48, 44, 40)},
    'quote': {'4:5': (72, 64, 56), '9:16': (80, 72, 64)},
    'declaration': {'4:5': (64, 56, 48), '9:16': (72, 64, 56)},
}
LINE_HEIGHT = {'short_essay': 1.55, 'quote': 1.35, 'declaration': 1.42}
CANVASES = {'4:5': (1080, 1350, 96, 72), '9:16': (1080, 1920, 108, 84)}


def invalid() -> PieceContractError:
    return PieceContractError('PIECE_REQUEST_INVALID', 'visual_recipe')


def build_visual_recipe(format_type: str, *, tier: str = 'free', language: str = 'ja',
                        theme: str | None = None, aspect_ratio: str | None = None,
                        branding: str | None = None) -> dict:
    if tier not in ('free', 'plus', 'premium') or format_type not in TEMPLATES:
        raise invalid()
    if language not in ('ja', 'en', 'mixed'):
        raise invalid()
    theme = 'soft_paper' if theme is None else theme
    aspect_ratio = '4:5' if aspect_ratio is None else aspect_ratio
    default_mark = 'required_small' if tier == 'free' else 'required_subtle'
    branding = default_mark if branding is None else branding
    if (theme not in THEMES or aspect_ratio not in CANVASES
            or tier == 'free' and theme != 'soft_paper'
            or tier != 'premium' and aspect_ratio != '4:5'
            or branding not in ((default_mark, 'off') if tier == 'premium' else (default_mark,))):
        raise invalid()
    return {
        'visual_recipe_version': 'piece.visual_recipe.v1',
        'visual_catalog_version': 'piece.visual_catalog.v1',
        'format_type': format_type,
        'template': {'template_id': TEMPLATES[format_type], 'template_version': 1},
        'theme': {'theme_id': theme, 'theme_version': 1},
        'font_style': {'font_style_id': 'system_readable', 'font_style_version': 1},
        'aspect_ratio': aspect_ratio,
        'branding': {'branding_mode': branding, 'branding_mark_id': 'cocolon_text_mark',
                     'branding_mark_version': 1},
        'layout_policy_version': 'piece.long_text_layout.v1', 'language': language,
    }


def validate_visual_recipe(recipe: Mapping, *, format_type: str, language: str,
                           expected_hash: str) -> dict:
    """Validate saved identity without reapplying today's subscription tier.

    New candidate entitlements belong to build_visual_recipe; saved record
    entitlement binding remains B6. Never change saved branding on downgrade.
    """
    try:
        mark = recipe['branding']['branding_mode']
        implied_tier = 'free' if mark == 'required_small' else 'premium'
        expected = build_visual_recipe(format_type, tier=implied_tier, language=language,
            theme=recipe['theme']['theme_id'], aspect_ratio=recipe['aspect_ratio'], branding=mark)
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
    return {'width': w, 'height': h, 'margin': margin, 'branding_zone': brand_zone,
            'font_sizes': list(SCALES[fmt][ratio]), 'line_height_ratio': LINE_HEIGHT[fmt],
            'paragraph_spacing_ratio': 0.65 if fmt == 'short_essay' else 0.0,
            'alignment': 'center' if fmt == 'quote' else 'left',
            'colors': deepcopy(THEMES[recipe['theme']['theme_id']])}
