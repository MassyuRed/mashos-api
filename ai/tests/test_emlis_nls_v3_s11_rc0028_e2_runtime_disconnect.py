# -*- coding: utf-8 -*-
from __future__ import annotations

"""Keep the rc0028 adapter private, body-free, and runtime-disconnected."""

import ast
from pathlib import Path

from emlis_ai_step11_rc0028_experiment_runtime_adapter_v3 import (
    STEP11_RC0028_EXPERIMENT_EXECUTION_SCOPE,
    run_step11_rc0028_experiment,
    step11_rc0028_experiment_result_material,
    validate_step11_rc0028_experiment_result,
)


_SERVICES = Path(__file__).resolve().parents[1] / "services" / "ai_inference"
_EXPERIMENT_ADAPTER = (
    _SERVICES / "emlis_ai_step11_rc0028_experiment_runtime_adapter_v3.py"
)
_SHARED_ADAPTER = _SERVICES / "emlis_ai_step11_runtime_adapter_v3.py"
_FORBIDDEN_SHAREABLE_KEYS = frozenset(
    {
        "body",
        "current_input",
        "final_utf8_bytes",
        "normalized_input",
        "output",
        "parsed_witness",
        "rendered_surface",
        "source_fragment",
        "thought_text",
        "action_text",
        "unsalted_body_digest",
        "utf8_bytes",
    }
)


def test_rc0028_adapter_has_no_eager_project_import() -> None:
    tree = ast.parse(_EXPERIMENT_ADAPTER.read_bytes())
    eager_nodes = tuple(
        node
        for node in tree.body
        if isinstance(node, (ast.Import, ast.ImportFrom))
    )
    eager_project_modules: set[str] = set()
    for node in eager_nodes:
        if isinstance(node, ast.Import):
            eager_project_modules.update(
                alias.name for alias in node.names if alias.name.startswith("emlis_ai_")
            )
        elif node.module and node.module.startswith("emlis_ai_"):
            eager_project_modules.add(node.module)
    assert eager_project_modules == set(), (
        "STEP11_RC0028_EAGER_RUNTIME_IMPORT_FORBIDDEN"
    )


def test_rc0028_shared_runtime_has_no_reverse_import_or_call() -> None:
    source = _SHARED_ADAPTER.read_text(encoding="utf-8")
    assert "emlis_ai_step11_rc0028_experiment_runtime_adapter_v3" not in source
    assert "run_step11_rc0028_experiment" not in source
    assert "execute_step11_rc0028_experiment_private" not in source


def test_rc0028_public_result_is_closed_and_body_free_on_fail_close() -> None:
    result = run_step11_rc0028_experiment(
        {},
        case_id="rc0028_disconnect_probe",
        source_case_commitment="1" * 64,
        source_dependency_closure_sha256="2" * 64,
    )
    assert result.execution_scope == STEP11_RC0028_EXPERIMENT_EXECUTION_SCOPE
    assert result.disposition == "fail_close"
    assert validate_step11_rc0028_experiment_result(result) == ()
    material = step11_rc0028_experiment_result_material(result)
    assert not (_FORBIDDEN_SHAREABLE_KEYS & frozenset(material))
    nested_keys = frozenset(
        key
        for row in material.get("gate_failure_code_counts", ())
        if type(row) is dict
        for key in row
    )
    assert not (_FORBIDDEN_SHAREABLE_KEYS & nested_keys)
    assert material["experimental_only"] is True
    assert material["body_free"] is True
    assert material["runtime_connected"] is False
