from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
for candidate in (ROOT, ROOT / "services", ROOT / "services" / "ai_inference"):
    path_str = str(candidate)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role")
os.environ.setdefault("MYMODEL_APP_NAME", "Cocolon Test App")


@pytest.fixture(scope="session")
def app_module():
    return importlib.import_module("app")


@pytest.fixture()
def client(app_module):
    return TestClient(app_module.app)