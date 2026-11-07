"""Subscriber settings and old-client negotiation; no live account or DB IO."""
from copy import deepcopy

import pytest

from piece_v2_contract import PieceContractError, canonical_sha256_hex
from piece_v2_quota import project_piece_plan_capabilities
from piece_v2_visual import LEGACY_THEME_IDS, THEME_IDS, build_visual_recipe, validate_visual_recipe


@pytest.mark.parametrize('theme', THEME_IDS)
@pytest.mark.parametrize('ratio', ['4:5', '9:16'])
@pytest.mark.parametrize('branding', ['required_small', 'off'])
def test_free_allows_only_two_original_colors_fixed_ratio_and_logo(theme, ratio, branding):
    permitted = theme in LEGACY_THEME_IDS and ratio == '4:5' and branding == 'required_small'
    if not permitted:
        with pytest.raises(PieceContractError):
            build_visual_recipe('short_essay', tier='free', theme=theme,
                                aspect_ratio=ratio, branding=branding)
        return
    recipe = build_visual_recipe('short_essay', tier='free', theme=theme,
                                 aspect_ratio=ratio, branding=branding)
    saved = deepcopy(recipe)
    assert validate_visual_recipe(recipe, format_type='short_essay', language='ja',
                                  expected_hash=canonical_sha256_hex(saved)) == saved


@pytest.mark.parametrize('tier', ['plus', 'premium'])
@pytest.mark.parametrize('theme', THEME_IDS)
@pytest.mark.parametrize('ratio', ['4:5', '9:16'])
@pytest.mark.parametrize('branding', ['required_subtle', 'off'])
def test_each_subscriber_can_choose_catalog_ratio_and_logo_without_saved_rewrite(tier, theme, ratio, branding):
    recipe = build_visual_recipe('short_essay', tier=tier, theme=theme,
                                 aspect_ratio=ratio, branding=branding)
    saved = deepcopy(recipe)
    assert validate_visual_recipe(recipe, format_type='short_essay', language='ja',
                                  expected_hash=canonical_sha256_hex(saved)) == saved


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
@pytest.mark.parametrize('expanded', [False, True])
def test_old_client_capability_lists_stay_exact(tier, expanded):
    from piece_v2_visual import THEME_IDS
    assert project_piece_plan_capabilities(server_tier=tier, expanded_palette=expanded) == {
        'format_selection': {'free': 'fixed', 'plus': 'automatic', 'premium': 'eligible_choice'}[tier],
        'theme_ids': ['soft_paper'] if tier == 'free' else list(THEME_IDS if expanded else LEGACY_THEME_IDS),
        'aspect_ratios': ['4:5', '9:16'] if tier == 'premium' else ['4:5'],
        'branding_modes': ['required_small'] if tier == 'free' else
                          ['required_subtle', 'off'] if tier == 'premium' else ['required_subtle'],
    }


@pytest.mark.parametrize('tier', ['free', 'plus', 'premium'])
def test_new_client_choices_match_server_tier_and_keep_format_policy(tier):
    caps = project_piece_plan_capabilities(server_tier=tier, expanded_palette=True,
                                           subscriber_customization=True)
    assert caps['theme_ids'] == list(LEGACY_THEME_IDS if tier == 'free' else THEME_IDS)
    assert caps['aspect_ratios'] == (['4:5'] if tier == 'free' else ['4:5', '9:16'])
    assert caps['branding_modes'] == (['required_small'] if tier == 'free' else ['required_subtle', 'off'])
    assert caps['format_selection'] == {'free': 'fixed', 'plus': 'automatic', 'premium': 'eligible_choice'}[tier]
    # Mutating a response never changes a later user's capabilities.
    caps['theme_ids'].clear()
    assert project_piece_plan_capabilities(server_tier=tier, expanded_palette=True,
        subscriber_customization=True)['theme_ids']
