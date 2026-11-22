"""Actual isolated PostgreSQL migration/RPC behavior; no model or live DB."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


def test_map_correction_atomic_sql_owner_target_cohort_and_history(tmp_path):
    if not os.environ.get('Q2_PGLITE_MODULE'):
        pytest.skip('Existing PostgreSQL WASM dependency not configured')
    from test_analysis_semantic_map import sample
    root = Path(__file__).parents[2]
    fixture = tmp_path / 'map-correction-source.json'
    fixture.write_text(json.dumps(sample(), ensure_ascii=False))
    result = subprocess.run(['node', str(root / 'ai/tests/analysis_map_correction_sql.cjs'),
        str(fixture), sys.executable], cwd=root, env=os.environ.copy(),
        capture_output=True, text=True, timeout=90)
    assert result.returncode == 0, result.stdout + result.stderr
    outcome = json.loads(result.stdout.strip().splitlines()[-1])
    assert outcome['status'] == 'passed'
    assert outcome['model_calls'] == 0 and outcome['live_database'] is False
