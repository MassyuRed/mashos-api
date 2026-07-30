from __future__ import annotations

import ast
import copy
import hashlib
import importlib
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
from types import ModuleType
from typing import Any, Callable, Mapping

import pytest


_TEST_PATH = (
    "ai/tests/"
    "test_emlis_nls_v3_recovery_epoch004_operational_admission_v2_"
    "event1_connection_actual_git_identity_parent_phase3_red.py"
)
_ENTRY_COMMIT_SHA1 = "97e8dd4d7021b8a1781d534aaa603f71dffa41b9"
_ENTRY_TREE_SHA1 = "cd3fc3da0976bbbcb708319e4bc8cbbb6a73ec19"
_LOGICAL_CYCLE_ID = "NLS_V3_CYCLE_001"
_RECOVERY_EPOCH_ID = "NLS_V3_CYCLE001_RECOVERY_EPOCH_004"

_EVENT_SCHEMA_V2 = (
    "cocolon.emlis.nls_v3.recovery_epoch004.sequence_event.v2"
)
_OPERATIONAL_ADMISSION_SCHEMA_V2 = (
    "cocolon.emlis.nls_v3.recovery_epoch004.operational_admission.v2"
)
_CANDIDATE_SCHEMA_V1 = (
    "cocolon.emlis.nls_v3.recovery_epoch004.candidate_allocation.v1"
)
_SOURCE_CLOSURE_SCHEMA_V1 = (
    "cocolon.emlis.nls_v3.recovery_epoch004."
    "source_baseline_eligibility_closure.v1"
)
_BOOTSTRAP_CLOSURE_SCHEMA_V1 = (
    "cocolon.emlis.nls_v3.recovery_epoch004."
    "formal_worker_bootstrap_manifest.v1"
)

_OWNER_API = (
    "validate_recovery_epoch004_sequence_event1_contract_state_v2"
)
_INDEPENDENT_API = (
    "verify_recovery_epoch004_sequence_event1_contract_state_v2"
)
_PARENT_PHASE3_API = (
    "validate_recovery_epoch004_parent_phase3_event1_evidence_state_v2"
)

_OWNER_FAILURE = ("RECOVERY_EPOCH004_EVENT1_V2_CONNECTION_INVALID",)
_INDEPENDENT_FAILURE = (
    "RECOVERY_EPOCH004_EVENT1_V2_INDEPENDENT_VERIFICATION_INVALID",
)
_PARENT_FAILURE = (
    "RECOVERY_EPOCH004_PARENT_PHASE3_EVENT1_EVIDENCE_INVALID",
)

_CAUSAL_RED_SIGNATURES = {
    "O01": (
        "O01_RECOVERY_EPOCH004_EVENT1_V2_OWNER_API_NOT_IMPLEMENTED"
    ),
    "O02": (
        "O02_RECOVERY_EPOCH004_EVENT1_V2_INDEPENDENT_API_NOT_IMPLEMENTED"
    ),
    "O03": (
        "O03_RECOVERY_EPOCH004_EVENT1_V2_EXECUTOR_IDENTITY_"
        "CONNECTION_NOT_IMPLEMENTED"
    ),
    "O04": (
        "O04_RECOVERY_EPOCH004_EVENT1_V2_SCHEMA_DISPATCH_NOT_IMPLEMENTED"
    ),
    "O05": (
        "O05_RECOVERY_EPOCH004_EVENT1_V2_EXACT23_EXACTLY_ONCE_"
        "NOT_IMPLEMENTED"
    ),
    "O06": (
        "O06_RECOVERY_EPOCH004_PARENT_PHASE3_REEXECUTION_NOT_IMPLEMENTED"
    ),
    "O07": (
        "O07_RECOVERY_EPOCH004_EVENT1_V2_FAIL_CLOSED_ZERO_EFFECTS_"
        "NOT_IMPLEMENTED"
    ),
}

_ORACLE_NAMES = (
    "EVENT1_V2_OWNER_SCHEMA_DISPATCH_PUBLIC_SIGNATURE_AND_INVALID_ENVELOPE",
    (
        "EVENT1_V2_INDEPENDENT_SCHEMA_DISPATCH_REEXECUTES_WITHOUT_"
        "OWNER_TRUST"
    ),
    (
        "SOURCE_SUBJECT_OWNER_INDEPENDENT_SAME_ACTUAL_GIT_ROOT_HEAD_TREE_"
        "MODULE_BLOB_RAW"
    ),
    "UNKNOWN_MIXED_AND_V2_TO_V1_FALLBACK_REJECTED_FAIL_CLOSED",
    (
        "EVENT1_EXACT23_NESTS_DISTINCT_CANDIDATE_AND_CONSUMES_OA_V2_"
        "EXACTLY_ONCE"
    ),
    (
        "PARENT_PHASE3_RECONSTRUCTS_ACTUAL_POSTFETCH_AND_CALLS_"
        "INDEPENDENT_ONCE"
    ),
    "MISSING_MIXED_STALE_IDENTITY_EVIDENCE_FAILS_CLOSED_ZERO_EFFECTS",
    "V1_EXACT16_EXACT8_AND_PREDECESSOR_ORACLES_REMAIN_IMMUTABLE",
)
_ORACLE_LIST_SHA256 = (
    "8f91b84d07f3272e1e342ecf7fd3bb0015596b29608bda6251c42e9bd5a8de58"
)

_NODE_NAMES = (
    (
        "test_o01_event1_v2_owner_schema_dispatch_public_signature_and_"
        "invalid_envelope"
    ),
    (
        "test_o02_event1_v2_independent_schema_dispatch_reexecutes_"
        "without_owner_trust"
    ),
    (
        "test_o03_source_subject_owner_independent_same_actual_git_root_"
        "head_tree_module_blob_raw"
    ),
    (
        "test_o04_unknown_mixed_and_v2_to_v1_fallback_rejected_"
        "fail_closed"
    ),
    (
        "test_o05_event1_exact23_nests_distinct_candidate_and_consumes_"
        "oa_v2_exactly_once"
    ),
    (
        "test_o06_parent_phase3_reconstructs_actual_postfetch_and_calls_"
        "independent_once"
    ),
    (
        "test_o07_missing_mixed_stale_identity_evidence_fail_closed_with_"
        "zero_effects"
    ),
    (
        "test_o08_v1_exact16_exact8_and_predecessor_oracles_remain_"
        "immutable"
    ),
)
_ORDERED_NODE_IDS = tuple(f"{_TEST_PATH}::{name}" for name in _NODE_NAMES)
_ORDERED_NODE_LIST_SHA256 = (
    "e2661d946c060efc44ce7da06f8c55f51d10dfad2af4f5f0526bd38109c340bc"
)

_EVENT_KEYS_ORDERED = (
    "schema_version",
    "ledger_id",
    "event_id",
    "logical_cycle_id",
    "recovery_epoch_id",
    "candidate_version_id",
    "event_ordinal",
    "event_name",
    "state",
    "prior_event",
    "challenge_id",
    "timestamp_utc",
    "timestamp_kind",
    "authority",
    "p0_external_identity",
    "candidate_allocation",
    "source_closure",
    "bootstrap_closure",
    "primary_evidence_artifact",
    "publication",
    "body_free",
    "automatic_progression",
    "event_sha256",
)
_CANDIDATE_KEYS_ORDERED = (
    "schema_version",
    "logical_cycle_id",
    "recovery_epoch_id",
    "candidate_version_id",
    "allocated_at_utc",
    "p0_external_identity_sha256",
    "source_closure_sha256",
    "reference_runtime_observation_external_identity_sha256",
    "candidate_allocation_sha256",
)
_V1_ADMISSION_KEYS_ORDERED = (
    "schema_version",
    "logical_cycle_id",
    "recovery_epoch_id",
    "predecessor_bindings",
    "source_closure",
    "bootstrap_closure",
    "authority",
    "scope",
    "freshness",
    "effect_boundary",
    "owner_validation_state",
    "independent_verification_state",
    "state",
    "automatic_progression",
    "body_free",
    "operational_admission_sha256",
)
_V1_PREDECESSOR_KEYS_ORDERED = (
    "p0_external_identity",
    (
        "operational_admission_parent_addendum_receipt_external_identity"
    ),
    "bootstrap_contract_d1_receipt_external_identity",
    "bootstrap_contract_d2_receipt_external_identity",
    "operational_admission_contract_d1_receipt_external_identity",
    "operational_admission_contract_d2_receipt_external_identity",
    "reference_runtime_observation_external_identity",
    "predecessor_bindings_sha256",
)
_V1_ADMISSION_KEYSET_SHA256 = (
    "965d297c7413c243cdebbc744f15334ca5eb0972801fd4254d443369f9caf66b"
)
_V1_PREDECESSOR_KEYSET_SHA256 = (
    "ea2dfb2bf3289209bf272ec460173fd5b9ae0429e4adc7c6f900ced4b44458d8"
)

_MODULE_NAMES = {
    "contract": "emlis_ai_nls_v3_artifact_contract",
    "sequence": "emlis_ai_recovery_epoch002_sequence_ledger_v3",
    "closure": "emlis_ai_recovery_epoch002_canonical_current_closure_v3",
    "independent": (
        "emlis_nls_v3_recovery_epoch002_closure_receipt_verify"
    ),
    "parent": (
        "emlis_nls_v3_recovery_epoch002_formal_parent_orchestrator_v3"
    ),
    "preflight": (
        "emlis_nls_v3_recovery_epoch002_formal_worker_bootstrap_preflight"
    ),
}
_MANDATORY_DIRECT_PATHS = {
    "sequence": (
        "ai/services/ai_inference/"
        "emlis_ai_recovery_epoch002_sequence_ledger_v3.py"
    ),
    "independent": (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_closure_receipt_verify.py"
    ),
    "parent": (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_formal_parent_orchestrator_v3.py"
    ),
}
_CANONICAL_LOADER_PATH = (
    "ai/services/ai_inference/emlis_ai_nls_v3_artifact_contract.py"
)
_CANONICAL_LOADER_BLOB_SHA1 = (
    "953d062fa858870e65d96cf03694d68c99003594"
)
_CANONICAL_LOADER_RAW_SHA256 = (
    "c20b262495276c9b549b257380e1a7c28069c316a7aca4b6e00a49de03d1512b"
)

_FUNCTION_SOURCE_HASHES = {
    _CANONICAL_LOADER_PATH: {
        "canonical_json_bytes": (
            "394387ad45c71df8437e6d2755d4043eaf6bb8e19f20514b508a8f40687c341c"
        ),
        "load_canonical_json_bytes": (
            "2176bce9b2421ccb3cd0217af346d164f4fd10bdca7b3d1d1223e81e0f168865"
        ),
    },
    _MANDATORY_DIRECT_PATHS["sequence"]: {
        "build_recovery_epoch003_operational_admission": (
            "ad85c66692d2b8e9bb3787ef6d8afff21c0e4b4f4a08c1fa6978e1a07e8bbfae"
        ),
        "validate_recovery_epoch003_sequence_event1_contract_state": (
            "63ef2fb2e3a17e5aac2605cd82d8b40e7ffd07e1b0f1bec5baeb6dc994249695"
        ),
        "_recovery_epoch003_current_event_valid": (
            "17bc86dda311ac503e7634f459a5f62a8c9993fd0e4d00aced4410e69b093e32"
        ),
    },
    (
        "ai/services/ai_inference/"
        "emlis_ai_recovery_epoch002_canonical_current_closure_v3.py"
    ): {
        "build_recovery_epoch003_source_bootstrap_closure": (
            "24bf12d6d1937ae5dc54dc74a45094a779df2338ea40ff4862ddb710c4789002"
        ),
        "validate_recovery_epoch003_source_bootstrap_contract_state": (
            "eb255d7243f45acf194f20044748d1ad20971653faa3c09fbd39668021ed321e"
        ),
    },
    _MANDATORY_DIRECT_PATHS["independent"]: {
        "verify_recovery_epoch003_reference_runtime_observation": (
            "05cd2d7f8182fe1dc0ec20536445ab7d63ba092e47ff8f3f649211f1e1cb60b9"
        ),
        "verify_recovery_epoch003_operational_admission_contract": (
            "089bfb98ddf540ef85aa2ddcf97b15ab5cef8e6e55a35c5bad6ad4cfe2de50c5"
        ),
        "_recovery_epoch003_current_event_nested_valid": (
            "78e835d067f5f9d1474a3d6d4b7c58bdf920829b7140ca8adb7a0bd08c571493"
        ),
    },
    _MANDATORY_DIRECT_PATHS["parent"]: {
        "validate_recovery_epoch003_parent_phase_evidence_state": (
            "fcb7056bbd2868ad59115832c4f68a2c9728a945780ae4a9f5a546eaf4826c3e"
        ),
        "execute_recovery_epoch003_current_strict_parent_phase_v1": (
            "0865deb09995a19d6b0e91249e4a3176ed3cb64f55806e73cda3d56c5035a138"
        ),
    },
    (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_formal_worker_bootstrap_preflight.py"
    ): {
        "materialize_recovery_epoch003_reference_runtime": (
            "558f7cba3b57df408508974fa03ab6927cfb1830f92931bef615562ccc4e953b"
        ),
        "build_recovery_epoch003_reference_runtime_observation": (
            "9792f7446d6f26b48239df10c05f6283943259ee7eb65c0b3cd2ba8bd1bc364e"
        ),
        "execute_recovery_epoch003_current_strict_preflight_v1": (
            "faf706fa297e912ac43b534eda6da744449ec905f4cd3cb374951e70bb9b1cdc"
        ),
        "_recovery_epoch003_baseline_valid": (
            "5087babfcc289f89548708858cf7a690bf21c5edbca0153e3cc2cbaa7f611df7"
        ),
    },
}

_PREDECESSOR_TEST_IDENTITIES = {
    (
        "ai/tests/"
        "test_emlis_nls_v3_recovery_epoch003_operational_admission_"
        "contract_red.py"
    ): (
        "cd79f1be2f2321c90deb817c93e75e848ba7d3fe",
        "9af99873afd7d77f151e4b6b0a75f350bfc96a1aea781e047f162d1e5379560d",
    ),
    (
        "ai/tests/"
        "test_emlis_nls_v3_recovery_epoch003_bootstrap_source_runtime_"
        "expected_observed_contract_red.py"
    ): (
        "dda02f15be90387dd045ef117a5961961e2cae2b",
        "8c8fcaf5211064ca59127a8081dc41ae8b9207472f070746c84a8e4b591a07e5",
    ),
    (
        "ai/tests/"
        "test_emlis_nls_v3_recovery_epoch003_actual_unclassified_import_"
        "exact3_and_versioned_current_strict_preflight_connection_red.py"
    ): (
        "f705b5296088c15accc76eb629bac637d16c714a",
        "cda6119f9dc85fd386eb2447f1c85d8e250b973388866dad2fff6855d342311a",
    ),
    (
        "ai/tests/"
        "test_emlis_nls_v3_recovery_epoch003_prestart_predecessor_actual_"
        "git_bytes_exact6_operational_admission_v2_schema_dispatch_red.py"
    ): (
        "b61913a784512d65d712ee9bc6f15736b4ae91d2",
        "ac136e06c8eaa0bb9d7342b8cbe5669f974865e89d4fecbb0c24257893d6bb1a",
    ),
}

_FORBIDDEN_EFFECT_CALL_PARTS = (
    "materialize",
    "publish",
    "allocate",
    "reservation",
    "create_attempt",
    "formal_exact134",
    "pytest.main",
)


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _sha256_value(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _git(root: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        check=check,
        capture_output=True,
        text=True,
        timeout=20,
    )
    return result.stdout.strip()


def _git_bytes(root: Path, *args: str) -> bytes:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        timeout=20,
    ).stdout


def _repository_root() -> Path:
    configured = os.environ.get("MASHOS_API_SOURCE_REPOSITORY_ROOT")
    root = (
        Path(configured)
        if configured
        else Path(__file__).resolve().parents[2]
    ).resolve()
    assert _git(root, "rev-parse", "--show-toplevel") == str(root)
    remote = _git(root, "remote", "get-url", "origin")
    assert remote.rstrip("/").endswith("MassyuRed/mashos-api.git")
    assert (
        subprocess.run(
            [
                "git",
                "merge-base",
                "--is-ancestor",
                _ENTRY_COMMIT_SHA1,
                "HEAD",
            ],
            cwd=root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=20,
        ).returncode
        == 0
    )
    assert _git(root, "rev-parse", f"{_ENTRY_COMMIT_SHA1}^{{tree}}") == (
        _ENTRY_TREE_SHA1
    )
    expected_head = os.environ.get("MASHOS_API_EXPECTED_HEAD_COMMIT_SHA1")
    expected_tree = os.environ.get("MASHOS_API_EXPECTED_HEAD_TREE_SHA1")
    if expected_head is not None:
        assert _git(root, "rev-parse", "HEAD") == expected_head
    if expected_tree is not None:
        assert _git(root, "rev-parse", "HEAD^{tree}") == expected_tree
    return root


def _prepare_imports(root: Path) -> None:
    for path in (
        root / "ai" / "services" / "ai_inference",
        root / "ai" / "tools",
    ):
        value = str(path)
        if value not in sys.path:
            sys.path.insert(0, value)


def _module(role: str) -> ModuleType:
    root = _repository_root()
    _prepare_imports(root)
    return importlib.import_module(_MODULE_NAMES[role])


def _require_api(
    role: str,
    name: str,
    oracle: str,
) -> Callable[[Mapping[str, Any]], Any]:
    api = getattr(_module(role), name, None)
    if not callable(api):
        pytest.fail(_CAUSAL_RED_SIGNATURES[oracle], pytrace=False)
    return api


def _function_node(module: ModuleType, name: str) -> ast.FunctionDef:
    source = Path(inspect.getsourcefile(module) or "").read_text(
        encoding="utf-8"
    )
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"missing function AST: {name}")


def _reachable_function_names(
    module: ModuleType,
    root_name: str,
) -> tuple[str, ...]:
    source = Path(inspect.getsourcefile(module) or "").read_text(
        encoding="utf-8"
    )
    tree = ast.parse(source)
    functions = {
        node.name: node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
    }
    assert root_name in functions
    pending = [root_name]
    seen: list[str] = []
    while pending:
        name = pending.pop(0)
        if name in seen:
            continue
        seen.append(name)
        node = functions[name]
        calls = {
            child.func.id
            for child in ast.walk(node)
            if isinstance(child, ast.Call)
            and isinstance(child.func, ast.Name)
            and child.func.id in functions
        }
        pending.extend(sorted(calls - set(seen)))
    return tuple(seen)


def _reachable_source(module: ModuleType, root_name: str) -> str:
    return "\n".join(
        inspect.getsource(getattr(module, name))
        for name in _reachable_function_names(module, root_name)
    )


def _reachable_call_names(
    module: ModuleType,
    root_name: str,
) -> frozenset[str]:
    names: set[str] = set()
    for function_name in _reachable_function_names(module, root_name):
        node = _function_node(module, function_name)
        for child in ast.walk(node):
            if not isinstance(child, ast.Call):
                continue
            function = child.func
            if isinstance(function, ast.Name):
                names.add(function.id)
            elif isinstance(function, ast.Attribute):
                parts = [function.attr]
                value = function.value
                while isinstance(value, ast.Attribute):
                    parts.append(value.attr)
                    value = value.value
                if isinstance(value, ast.Name):
                    parts.append(value.id)
                names.add(".".join(reversed(parts)))
    return frozenset(names)


def _function_source_sha256(path: str, name: str) -> str:
    raw = (_repository_root() / path).read_bytes()
    text = raw.decode("utf-8")
    lines = text.splitlines(keepends=True)
    tree = ast.parse(text)
    for node in tree.body:
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == name
        ):
            source = "".join(lines[node.lineno - 1 : node.end_lineno])
            if not source.endswith("\n"):
                source += "\n"
            return hashlib.sha256(source.encode("utf-8")).hexdigest()
    raise AssertionError(f"missing frozen function: {path}::{name}")


def _assert_public_signature(api: Callable[..., Any]) -> None:
    signature = inspect.signature(api)
    assert tuple(signature.parameters) == ("state",)
    parameter = signature.parameters["state"]
    assert parameter.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert parameter.default is inspect.Parameter.empty


def _schema_probe(
    *,
    event_schema: str,
    admission_schema: str,
    candidate_schema: str = _CANDIDATE_SCHEMA_V1,
    source_schema: str = _SOURCE_CLOSURE_SCHEMA_V1,
    bootstrap_schema: str = _BOOTSTRAP_CLOSURE_SCHEMA_V1,
    extras: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    state: dict[str, Any] = {
        "logical_cycle_id": _LOGICAL_CYCLE_ID,
        "recovery_epoch_id": _RECOVERY_EPOCH_ID,
        "event1": {
            "schema_version": event_schema,
            "candidate_allocation": {
                "schema_version": candidate_schema,
            },
            "source_closure": {"schema_version": source_schema},
            "bootstrap_closure": {"schema_version": bootstrap_schema},
            "authority": {
                "operational_admission": {
                    "schema_version": admission_schema,
                }
            },
        },
        "automatic_progression": False,
    }
    if extras:
        state.update(copy.deepcopy(dict(extras)))
    return state


def _assert_module_actual_git_identity(
    api: Callable[..., Any],
    path: str,
) -> None:
    root = _repository_root()
    origin = Path(inspect.getsourcefile(api) or "").resolve()
    assert origin == (root / path).resolve()
    blob = _git(root, "rev-parse", f"HEAD:{path}")
    raw = _git_bytes(root, "show", f"HEAD:{path}")
    assert hashlib.sha256(raw).hexdigest() == hashlib.sha256(
        origin.read_bytes()
    ).hexdigest()
    assert blob == _git(root, "hash-object", path)


def _assert_versioned_constants(module: ModuleType) -> None:
    assert module._RECOVERY_EPOCH004_SEQUENCE_EVENT_SCHEMA == (
        _EVENT_SCHEMA_V2
    )
    assert module._RECOVERY_EPOCH004_OPERATIONAL_ADMISSION_V2_SCHEMA == (
        _OPERATIONAL_ADMISSION_SCHEMA_V2
    )
    assert module._RECOVERY_EPOCH004_CANDIDATE_SCHEMA == (
        _CANDIDATE_SCHEMA_V1
    )
    assert module._RECOVERY_EPOCH004_SOURCE_CLOSURE_SCHEMA == (
        _SOURCE_CLOSURE_SCHEMA_V1
    )
    assert module._RECOVERY_EPOCH004_BOOTSTRAP_CLOSURE_SCHEMA == (
        _BOOTSTRAP_CLOSURE_SCHEMA_V1
    )


def _assert_no_effect_sink_calls(
    module: ModuleType,
    api_name: str,
) -> None:
    for call in _reachable_call_names(module, api_name):
        lowered = call.lower()
        assert not any(part in lowered for part in _FORBIDDEN_EFFECT_CALL_PARTS)


def test_o01_event1_v2_owner_schema_dispatch_public_signature_and_invalid_envelope() -> None:
    api = _require_api("sequence", _OWNER_API, "O01")
    _assert_public_signature(api)
    assert api({}) == _OWNER_FAILURE
    module = _module("sequence")
    _assert_versioned_constants(module)
    source = _reachable_source(module, _OWNER_API)
    for token in (
        "_RECOVERY_EPOCH004_SEQUENCE_EVENT_SCHEMA",
        "_RECOVERY_EPOCH004_OPERATIONAL_ADMISSION_V2_SCHEMA",
        "_RECOVERY_EPOCH004_CANDIDATE_SCHEMA",
        "_RECOVERY_EPOCH004_SOURCE_CLOSURE_SCHEMA",
        "_RECOVERY_EPOCH004_BOOTSTRAP_CLOSURE_SCHEMA",
    ):
        assert token in source
    assert "validate_recovery_epoch003_sequence_event1_contract_state" not in (
        source
    )


def test_o02_event1_v2_independent_schema_dispatch_reexecutes_without_owner_trust() -> None:
    api = _require_api("independent", _INDEPENDENT_API, "O02")
    _assert_public_signature(api)
    assert api({}) == _INDEPENDENT_FAILURE
    module = _module("independent")
    _assert_versioned_constants(module)
    source = _reachable_source(module, _INDEPENDENT_API)
    for token in (
        "_RECOVERY_EPOCH004_SEQUENCE_EVENT_SCHEMA",
        "_RECOVERY_EPOCH004_OPERATIONAL_ADMISSION_V2_SCHEMA",
        "_RECOVERY_EPOCH004_CANDIDATE_SCHEMA",
        "_RECOVERY_EPOCH004_SOURCE_CLOSURE_SCHEMA",
        "_RECOVERY_EPOCH004_BOOTSTRAP_CLOSURE_SCHEMA",
    ):
        assert token in source
    assert "validate_recovery_epoch003_sequence_event1_contract_state" not in (
        source
    )
    assert _MODULE_NAMES["sequence"] not in Path(
        inspect.getsourcefile(module) or ""
    ).read_text(encoding="utf-8")


def test_o03_source_subject_owner_independent_same_actual_git_root_head_tree_module_blob_raw() -> None:
    owner = _require_api("sequence", _OWNER_API, "O03")
    independent = _require_api("independent", _INDEPENDENT_API, "O03")
    parent = _require_api("parent", _PARENT_PHASE3_API, "O03")
    root = _repository_root()
    head = _git(root, "rev-parse", "HEAD")
    tree = _git(root, "rev-parse", "HEAD^{tree}")
    assert len(head) == 40 and len(tree) == 40
    _assert_module_actual_git_identity(
        owner,
        _MANDATORY_DIRECT_PATHS["sequence"],
    )
    _assert_module_actual_git_identity(
        independent,
        _MANDATORY_DIRECT_PATHS["independent"],
    )
    _assert_module_actual_git_identity(
        parent,
        _MANDATORY_DIRECT_PATHS["parent"],
    )
    parent_source = _reachable_source(_module("parent"), _PARENT_PHASE3_API)
    for token in (
        "source_repository_root",
        "source_subject",
        "owner_executor",
        "independent_executor",
        "source_commit_sha1",
        "source_tree_sha1",
        "git_blob_sha1",
        "raw_sha256",
        "origin/main",
        "worktree_clean",
    ):
        assert token in parent_source


def test_o04_unknown_mixed_and_v2_to_v1_fallback_rejected_fail_closed() -> None:
    owner = _require_api("sequence", _OWNER_API, "O04")
    independent = _require_api("independent", _INDEPENDENT_API, "O04")
    v1_event = _module("sequence").RECOVERY_EPOCH003_SEQUENCE_EVENT_SCHEMA
    v1_admission = _module(
        "sequence"
    )._RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_SCHEMA
    probes = (
        _schema_probe(
            event_schema="cocolon.invalid.unknown_event.v99",
            admission_schema=_OPERATIONAL_ADMISSION_SCHEMA_V2,
        ),
        _schema_probe(
            event_schema=_EVENT_SCHEMA_V2,
            admission_schema="cocolon.invalid.unknown_admission.v99",
        ),
        _schema_probe(
            event_schema=_EVENT_SCHEMA_V2,
            admission_schema=v1_admission,
        ),
        _schema_probe(
            event_schema=v1_event,
            admission_schema=_OPERATIONAL_ADMISSION_SCHEMA_V2,
        ),
        _schema_probe(
            event_schema=_EVENT_SCHEMA_V2,
            admission_schema=_OPERATIONAL_ADMISSION_SCHEMA_V2,
            extras={
                "selected_schema": _EVENT_SCHEMA_V2,
                "allow_v1_fallback": True,
                "profile": "fixture_only",
            },
        ),
    )
    for probe in probes:
        original = copy.deepcopy(probe)
        assert owner(probe) == _OWNER_FAILURE
        assert probe == original
        assert independent(probe) == _INDEPENDENT_FAILURE
        assert probe == original


def test_o05_event1_exact23_nests_distinct_candidate_and_consumes_oa_v2_exactly_once() -> None:
    owner = _require_api("sequence", _OWNER_API, "O05")
    independent = _require_api("independent", _INDEPENDENT_API, "O05")
    owner_module = _module("sequence")
    independent_module = _module("independent")
    assert set(owner_module.RECOVERY_EPOCH004_SEQUENCE_EVENT_KEYS) == set(
        _EVENT_KEYS_ORDERED
    )
    assert set(
        owner_module._RECOVERY_EPOCH004_EVENT_CANDIDATE_KEYS
    ) == set(_CANDIDATE_KEYS_ORDERED)
    assert set(independent_module.RECOVERY_EPOCH004_SEQUENCE_EVENT_KEYS) == (
        set(_EVENT_KEYS_ORDERED)
    )
    assert set(
        independent_module._RECOVERY_EPOCH004_EVENT_CANDIDATE_KEYS
    ) == set(_CANDIDATE_KEYS_ORDERED)
    assert len(owner_module.RECOVERY_EPOCH004_SEQUENCE_EVENT_KEYS) == 23
    assert len(owner_module._RECOVERY_EPOCH004_EVENT_CANDIDATE_KEYS) == 9
    for module, api_name in (
        (owner_module, _OWNER_API),
        (independent_module, _INDEPENDENT_API),
    ):
        source = _reachable_source(module, api_name)
        for token in (
            "candidate_version_id",
            "candidate_allocation",
            "candidate_allocation_sha256",
            "historical_candidate_version_ids",
            "primary_evidence_artifact",
            "supporting_artifacts",
            "supporting_artifact_count",
            "expected_changed_path_count",
            "maximum_event1_consumption_count",
            "reuse_allowed",
            "automatic_progression",
            "event_sha256",
        ):
            assert token in source
    incomplete = _schema_probe(
        event_schema=_EVENT_SCHEMA_V2,
        admission_schema=_OPERATIONAL_ADMISSION_SCHEMA_V2,
    )
    assert owner(incomplete) == _OWNER_FAILURE
    assert independent(incomplete) == _INDEPENDENT_FAILURE


def test_o06_parent_phase3_reconstructs_actual_postfetch_and_calls_independent_once() -> None:
    api = _require_api("parent", _PARENT_PHASE3_API, "O06")
    _assert_public_signature(api)
    assert api({}) == _PARENT_FAILURE
    module = _module("parent")
    source = _reachable_source(module, _PARENT_PHASE3_API)
    for token in (
        "parent_phase_evidence_state",
        "completed_phases",
        "phase_evidence",
        "CANDIDATE_ALLOCATED_WITH_EVENT1_PUBLISHED_AND_POSTVERIFIED",
        "OPERATIONAL_RUNTIME_MATERIALIZATION_AND_PREFLIGHT",
        "published_body",
        "postfetch_body",
        "publication_commit_sha1",
        "git_blob_sha1",
        "raw_sha256",
        "logical_artifact_sha256",
        "identity_sha256",
        _OWNER_API,
        _INDEPENDENT_API,
        "deepcopy",
    ):
        assert token in source
    assert source.count(_INDEPENDENT_API) == 1
    assert (
        "validate_recovery_epoch003_parent_phase_evidence_state"
        not in source
    )


def test_o07_missing_mixed_stale_identity_evidence_fail_closed_with_zero_effects() -> None:
    owner = _require_api("sequence", _OWNER_API, "O07")
    independent = _require_api("independent", _INDEPENDENT_API, "O07")
    parent = _require_api("parent", _PARENT_PHASE3_API, "O07")
    root = _repository_root()
    before_repository = (
        _git(root, "rev-parse", "HEAD"),
        _git(root, "rev-parse", "HEAD^{tree}"),
        _git(root, "status", "--porcelain", "--untracked-files=all"),
    )
    stale = _schema_probe(
        event_schema=_EVENT_SCHEMA_V2,
        admission_schema=_OPERATIONAL_ADMISSION_SCHEMA_V2,
        extras={
            "source_subject": {
                "source_commit_sha1": "0" * 40,
                "source_tree_sha1": "0" * 40,
            },
            "owner_executor": None,
            "independent_executor": None,
        },
    )
    mixed = _schema_probe(
        event_schema=_EVENT_SCHEMA_V2,
        admission_schema=_module(
            "sequence"
        )._RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_SCHEMA,
    )
    for value in ({}, stale, mixed):
        original = copy.deepcopy(value)
        assert owner(value) == _OWNER_FAILURE
        assert value == original
        assert independent(value) == _INDEPENDENT_FAILURE
        assert value == original
        assert parent(value) == _PARENT_FAILURE
        assert value == original
    for module, api_name in (
        (_module("sequence"), _OWNER_API),
        (_module("independent"), _INDEPENDENT_API),
        (_module("parent"), _PARENT_PHASE3_API),
    ):
        _assert_no_effect_sink_calls(module, api_name)
        source = _reachable_source(module, api_name)
        assert "pytest.main" not in source
    after_repository = (
        _git(root, "rev-parse", "HEAD"),
        _git(root, "rev-parse", "HEAD^{tree}"),
        _git(root, "status", "--porcelain", "--untracked-files=all"),
    )
    assert after_repository == before_repository


def test_o08_v1_exact16_exact8_and_predecessor_oracles_remain_immutable() -> None:
    assert _sha256_value(_ORACLE_NAMES) == _ORACLE_LIST_SHA256
    assert _sha256_value(_ORDERED_NODE_IDS) == _ORDERED_NODE_LIST_SHA256
    assert len(_ORACLE_NAMES) == len(_NODE_NAMES) == 8
    assert _sha256_value(_V1_ADMISSION_KEYS_ORDERED) == (
        _V1_ADMISSION_KEYSET_SHA256
    )
    assert _sha256_value(_V1_PREDECESSOR_KEYS_ORDERED) == (
        _V1_PREDECESSOR_KEYSET_SHA256
    )
    root = _repository_root()
    loader_raw = (root / _CANONICAL_LOADER_PATH).read_bytes()
    assert hashlib.sha256(loader_raw).hexdigest() == (
        _CANONICAL_LOADER_RAW_SHA256
    )
    assert _git(root, "rev-parse", f"HEAD:{_CANONICAL_LOADER_PATH}") == (
        _CANONICAL_LOADER_BLOB_SHA1
    )
    for path, functions in _FUNCTION_SOURCE_HASHES.items():
        for name, expected in functions.items():
            assert _function_source_sha256(path, name) == expected
    for path, (expected_blob, expected_raw) in (
        _PREDECESSOR_TEST_IDENTITIES.items()
    ):
        raw = _git_bytes(root, "show", f"HEAD:{path}")
        assert _git(root, "rev-parse", f"HEAD:{path}") == expected_blob
        assert hashlib.sha256(raw).hexdigest() == expected_raw
    sequence = _module("sequence")
    independent = _module("independent")
    assert sequence._RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_SCHEMA == (
        "cocolon.emlis.nls_v3.recovery_epoch003.operational_admission.v1"
    )
    assert independent._RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_SCHEMA == (
        "cocolon.emlis.nls_v3.recovery_epoch003.operational_admission.v1"
    )
    assert set(sequence._RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_KEYS) == (
        set(_V1_ADMISSION_KEYS_ORDERED)
    )
    assert set(independent._RECOVERY_EPOCH003_OPERATIONAL_ADMISSION_KEYS) == (
        set(_V1_ADMISSION_KEYS_ORDERED)
    )
    assert set(sequence._RECOVERY_EPOCH003_PREDECESSOR_KEYS) == set(
        _V1_PREDECESSOR_KEYS_ORDERED
    )
    assert set(independent._RECOVERY_EPOCH003_PREDECESSOR_KEYS) == set(
        _V1_PREDECESSOR_KEYS_ORDERED
    )
