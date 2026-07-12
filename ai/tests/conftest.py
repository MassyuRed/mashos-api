"""Shared pytest path setup for EmlisAI backend tests.

The EmlisAI tests import the ai_inference modules as top-level modules, e.g.
``from emlis_ai_listener_reader_judge import ...``.  Keep that contract local to
tests so Step 8 commands run from ``mashos-api/ai`` without requiring callers to
set PYTHONPATH manually.
"""

from __future__ import annotations

import sys
from pathlib import Path

pytest_plugins = ("helpers.emlis_ai_fb172_migration",)

_AI_ROOT = Path(__file__).resolve().parents[1]
_AI_INFERENCE_PATH = _AI_ROOT / "services" / "ai_inference"

_path = str(_AI_INFERENCE_PATH)
if _path not in sys.path:
    sys.path.insert(0, _path)
