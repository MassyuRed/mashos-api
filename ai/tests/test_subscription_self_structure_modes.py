from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for candidate in (ROOT, ROOT / "services", ROOT / "services" / "ai_inference"):
    path_str = str(candidate)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from subscription import (  # noqa: E402
    MyProfileMode,
    SubscriptionTier,
    allowed_self_structure_modes_for_tier,
    is_self_structure_mode_allowed,
)


def test_self_structure_modes_allow_free_light_only():
    assert allowed_self_structure_modes_for_tier(SubscriptionTier.FREE) == [MyProfileMode.LIGHT]
    assert is_self_structure_mode_allowed("free", "light") is True
    assert is_self_structure_mode_allowed("free", "standard") is False


def test_self_structure_modes_keep_plus_and_premium_depth():
    assert is_self_structure_mode_allowed("plus", "standard") is True
    assert is_self_structure_mode_allowed("plus", "deep") is False
    assert is_self_structure_mode_allowed("premium", "deep") is True
