# -*- coding: utf-8 -*-
from __future__ import annotations

"""Prove that rc0029 inverse consumption shares no forward helper."""

import ast
import hashlib
from pathlib import Path

import pytest

from emlis_ai_step11_natural_surface_matcher_v3 import (
    Step11Rc0029ExperimentInverseSurfaceError,
    parse_step11_rc0029_experiment_surface,
)


_MATCHER = (
    Path(__file__).resolve().parents[1]
    / "services"
    / "ai_inference"
    / "emlis_ai_step11_natural_surface_matcher_v3.py"
)
_RC0027_PREFIX_BYTES = 392_348
_RC0027_PREFIX_SHA256 = (
    "c9cacd3112f90f8f38fb7163a52ced248af78da2670459f7f418311a848f48b0"
)
_FORBIDDEN_INVERSE_IMPORTS = frozenset(
    {
        "emlis_ai_step11_grounded_lexicalization_v3",
        "emlis_ai_step11_natural_surface_v3",
        "emlis_ai_step11_hard_gate_v3",
        "emlis_ai_step11_rc0029_experiment_runtime_adapter_v3",
    }
)


def _import_roots(source: bytes) -> frozenset[str]:
    tree = ast.parse(source)
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".", 1)[0])
    return frozenset(names)


def test_rc0029_inverse_owner_is_append_only_and_forward_import_free() -> None:
    source = _MATCHER.read_bytes()
    assert hashlib.sha256(source[:_RC0027_PREFIX_BYTES]).hexdigest() == (
        _RC0027_PREFIX_SHA256
    )
    experiment_suffix = source[_RC0027_PREFIX_BYTES:]
    assert not (_import_roots(experiment_suffix) & _FORBIDDEN_INVERSE_IMPORTS), (
        "STEP11_RC0029_FORWARD_INVERSE_IMPORT_FORBIDDEN"
    )


@pytest.mark.parametrize(
    "args,kwargs",
    (
        ((b"x", object()), {}),
        ((b"x",), {"candidate": object()}),
        ((b"x",), {"covered_ids": ()}),
        ((b"x",), {"generator_span_map": {}}),
    ),
)
def test_rc0029_body_only_parser_rejects_all_forward_metadata(
    args: tuple[object, ...],
    kwargs: dict[str, object],
) -> None:
    with pytest.raises(
        Step11Rc0029ExperimentInverseSurfaceError
    ) as captured:
        parse_step11_rc0029_experiment_surface(*args, **kwargs)
    assert captured.value.code == (
        "STEP11_RC0029_PARSER_FORWARD_METADATA_FORBIDDEN"
    )

