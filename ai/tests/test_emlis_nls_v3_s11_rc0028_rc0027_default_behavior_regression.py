# -*- coding: utf-8 -*-
from __future__ import annotations

"""Lock the rc0027 default owner prefixes and disconnected import graph."""

import hashlib
import importlib
from pathlib import Path
import sys


_AI_ROOT = Path(__file__).resolve().parents[1]
_SERVICES = _AI_ROOT / "services" / "ai_inference"
_PREFIXES = {
    "emlis_ai_step11_grounded_lexicalization_v3.py": (
        29_520,
        "2207ce37b13dd98d13433721c259f9854c2e3e70d5dc579cf9661cab6c7a81aa",
    ),
    "emlis_ai_step11_natural_surface_v3.py": (
        221_884,
        "f397675a4cf88d94b40c5e4363f1ba182fe19c98becea546f06b564f43aa1ba9",
    ),
    "emlis_ai_step11_natural_surface_matcher_v3.py": (
        392_348,
        "c9cacd3112f90f8f38fb7163a52ced248af78da2670459f7f418311a848f48b0",
    ),
    "emlis_ai_step11_hard_gate_v3.py": (
        79_178,
        "6e8000b58bb9679cec4c95519fec0154fa525649f1115e9f92fa4da74e26ebe9",
    ),
}
_IMMUTABLE = {
    "emlis_ai_step11_runtime_adapter_v3.py": (
        "012d09ab82ff526a9d854c845a7930eb8836e1dbd41c67428644c2c3a02bfbc7"
    ),
    "emlis_ai_step11_surface_catalog_v3.py": (
        "63cfd9b1677062dcfe10368b2b75aeaeba4a990f6ec1993c0b3fa9ae04a210db"
    ),
}
_DISCONNECTED_MODULES = frozenset(
    {
        "emlis_ai_grounded_lexical_role_experiment_snapshot_successor_v3",
        "emlis_ai_grounded_lexical_role_witness_successor_v3",
        "emlis_ai_grounded_relation_construction_authority_successor_v3",
        "emlis_ai_step11_rc0028_experiment_surface_catalog_v3",
        "emlis_ai_step11_rc0028_experiment_runtime_adapter_v3",
    }
)


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def test_rc0028_four_default_owner_prefixes_are_exact_rc0027_bytes() -> None:
    for name, (size, expected) in _PREFIXES.items():
        source = (_SERVICES / name).read_bytes()
        assert len(source) > size, "RC0028_ADDITIVE_OWNER_SECTION_MISSING"
        assert _sha256(source[:size]) == expected, (
            "RC0027_DEFAULT_OWNER_PREFIX_CHANGED:" + name
        )


def test_rc0028_shared_runtime_and_catalog_are_byte_immutable() -> None:
    for name, expected in _IMMUTABLE.items():
        assert _sha256((_SERVICES / name).read_bytes()) == expected, (
            "RC0027_IMMUTABLE_OWNER_CHANGED:" + name
        )


def test_rc0028_shared_runtime_import_is_successor_disconnected() -> None:
    for module_name in _DISCONNECTED_MODULES:
        sys.modules.pop(module_name, None)
    sys.modules.pop("emlis_ai_step11_runtime_adapter_v3", None)
    owner = importlib.import_module("emlis_ai_step11_runtime_adapter_v3")
    assert owner.STEP11_RUNTIME_ADAPTER_VERSION.endswith(".rc0027.v1")
    assert not (_DISCONNECTED_MODULES & frozenset(sys.modules)), (
        "RC0028_SHARED_RUNTIME_REVERSE_IMPORT_DETECTED"
    )
