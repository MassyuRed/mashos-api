# -*- coding: utf-8 -*-
from __future__ import annotations

"""E3 phase-qualified dependency authority for the disconnected rc0030 lane.

The rc0029 parent and completed P4/P5/E2 manifests are immutable historical
predecessors.  The exact eighteen-path list remains the closed maximum for the
whole run.  E3 activates only the bounded runner and representative-eight
test, and requires the E4 path to remain absent.  All four production owners
and the E2 integration test stay pinned byte-for-byte to E2 evidence.
Filesystem discovery is rejection-only and cannot admit a path.
"""

import ast
import hashlib
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

from emlis_ai_nls_v3_artifact_contract import artifact_sha256
from emlis_ai_rc0029_surface_repair_experiment_dependency_manifest_v3 import (
    RC0029_SURFACE_REPAIR_DEPENDENCY_MANIFEST_SCHEMA,
    validate_rc0029_surface_repair_dependency_manifest_shape,
)


RC0030_SURFACE_PLANNING_DEPENDENCY_MANIFEST_SCHEMA = (
    "cocolon.emlis.nls_v3."
    "rc0030_surface_planning_experiment_dependency_manifest.v4"
)
RC0030_SURFACE_PLANNING_EXPERIMENT_ID = (
    "nls_v3_rc0030_common_surface_planning_experiment"
)
RC0030_BASELINE_GIT_COMMIT = (
    "e1e2ec5c17fa165f9972373304899802832ecd5b"
)
RC0030_P4_PHASE_PREDECESSOR_GIT_COMMIT = (
    "afcd089a872d71b07930592b068bdc3d480b8e3b"
)
RC0030_P5_PHASE_PREDECESSOR_GIT_COMMIT = (
    "3897331a5f605762e09f9953e47801d45d3c5da2"
)
RC0030_E2_PHASE_PREDECESSOR_GIT_COMMIT = (
    "45b178cfc0e7d94ab8385682ab3c7bbf0ab9aa25"
)
RC0030_E3_PHASE_PREDECESSOR_GIT_COMMIT = (
    "38ca7fa779065998a363ce9bb581338d98b8f79d"
)
RC0030_MANIFEST_PHASE = "E3_MACHINE_AND_PRODUCT_READ"

RC0030_P4_MANIFEST_SCHEMA = (
    "cocolon.emlis.nls_v3."
    "rc0030_surface_planning_experiment_dependency_manifest.v1"
)
RC0030_P4_MANIFEST_PHASE = "P4_GATE_RUNTIME_CLOSURE"
RC0030_P4_MANIFEST_FILE_SHA256 = (
    "147c395d6250553aa9fa2fc1c14888b357827f6f8d8bf64f2dae18e71fd33f60"
)
RC0030_P4_MANIFEST_ARTIFACT_SHA256 = (
    "ec0f49f013ac4814749ad928849ff5382c9df97bb5fb78df3e89cb75143932f1"
)
RC0030_P4_SOURCE_DEPENDENCY_CLOSURE_SHA256 = (
    "29abbb08da497c902ea56cffbc82703801c7228f86e8a4f0f95d00800c31456b"
)
RC0030_P4_SOURCE_FILE_COUNT = 219

RC0030_P5_MANIFEST_SCHEMA = (
    "cocolon.emlis.nls_v3."
    "rc0030_surface_planning_experiment_dependency_manifest.v2"
)
RC0030_P5_MANIFEST_GIT_COMMIT = (
    "924bd458255f226db54c17d84dd4aafc5db2b1e2"
)
RC0030_P5_MANIFEST_PHASE = "P5_CARDINALITY_REGRESSION"
RC0030_P5_MANIFEST_FILE_SHA256 = (
    "4ceb33aa6bb6f15d6ad9b7212bbdcee901edb352707f3f19a90e91ff6d91f62c"
)
RC0030_P5_MANIFEST_ARTIFACT_SHA256 = (
    "265418796ec720112ea046014b7dd3c612d392382647a64db5fe7396b4a976b7"
)
RC0030_P5_SOURCE_DEPENDENCY_CLOSURE_SHA256 = (
    "7c905f06c88ed4a19f8ece102cafbb1333dcce1b3e840081952682703ec038e5"
)
RC0030_P5_FILE_HASHES_SHA256 = (
    "75663d3799c8da7e196d4a30fcc29b1358ab4fc3a56b2461f7eb3b9ec2ecbf70"
)
RC0030_P5_SOURCE_FILE_COUNT = 222

RC0030_E2_MANIFEST_SCHEMA = (
    "cocolon.emlis.nls_v3."
    "rc0030_surface_planning_experiment_dependency_manifest.v3"
)
RC0030_E2_MANIFEST_GIT_COMMIT = (
    "38ca7fa779065998a363ce9bb581338d98b8f79d"
)
RC0030_E2_MANIFEST_PHASE = "E2_INTEGRATED_SYNCHRONIZATION"
RC0030_E2_MANIFEST_FILE_SHA256 = (
    "754e79dc0f871b9b6c650b174f067f16cef35a9f141bf91205d42c308b1041f7"
)
RC0030_E2_MANIFEST_ARTIFACT_SHA256 = (
    "fe468b51e3b9f37558f30b010aad205500759806dfb939f859b0b9699466e097"
)
RC0030_E2_SOURCE_DEPENDENCY_CLOSURE_SHA256 = (
    "a49e9bc2b8ce1443c955c9fd010fd07454e2e8a17c70a845db180e97b7023832"
)
RC0030_E2_FILE_HASHES_SHA256 = (
    "f7a6fb9c08e3286f1784127e675f0761e87a4431699692082b8e20fbc87a33f3"
)
RC0030_E2_SOURCE_FILE_COUNT = 223

RC0029_SURFACE_REPAIR_PARENT_MANIFEST_PATH = (
    "ai/tests/fixtures/emlis_nls_v3/cycle_001/"
    "cycle001_dependency_manifest_rc0029_surface_repair_experiment.json"
)
RC0029_SURFACE_REPAIR_PARENT_MANIFEST_FILE_SHA256 = (
    "9b232da64222f83c33aaf77af2662097cb417ab177f4a1fb374e69a92cae0ad7"
)
RC0029_SURFACE_REPAIR_PARENT_MANIFEST_ARTIFACT_SHA256 = (
    "05365d90ffec011868a6c7b9926505ca71fc675b9285ee6b8c3f4d15f714af8b"
)
RC0029_SURFACE_REPAIR_PARENT_SOURCE_CLOSURE_SHA256 = (
    "cd46925c6db478ac07e501acb64c45cae3a122ab0c1d834d06a83f1190cfb082"
)
RC0029_SURFACE_REPAIR_PARENT_FILE_HASHES_SHA256 = (
    "55acda0e6971aefd6ab5c04cd214cb0668c3e0e9e05a1741981b63ba60872835"
)
RC0029_SURFACE_REPAIR_PARENT_SOURCE_FILE_COUNT = 209

RC0030_LEXICALIZATION_PATH = (
    "ai/services/ai_inference/emlis_ai_step11_grounded_lexicalization_v3.py"
)
RC0030_SURFACE_PATH = (
    "ai/services/ai_inference/emlis_ai_step11_natural_surface_v3.py"
)
RC0030_MATCHER_PATH = (
    "ai/services/ai_inference/"
    "emlis_ai_step11_natural_surface_matcher_v3.py"
)
RC0030_HARD_GATE_PATH = (
    "ai/services/ai_inference/emlis_ai_step11_hard_gate_v3.py"
)

# rc0029 bytes are a strict prefix of each rc0030 owner.  The size makes the
# prefix check independent from git and prevents a rewrite followed by append.
RC0030_MODIFIED_OWNER_PREDECESSORS = (
    {
        "path": RC0030_LEXICALIZATION_PATH,
        "predecessor_size": 103805,
        "predecessor_sha256": (
            "43e99c6077e93db61908e11672d08122cb5928fe63fe64ae0ca565659b43bff4"
        ),
        "p4_phase_predecessor_sha256": (
            "592f3ab7c90831c3191f51e9e7dd9a1f8c3fe4add1fd31bba9fdc65dccaecc28"
        ),
        "p5_phase_predecessor_sha256": (
            "592f3ab7c90831c3191f51e9e7dd9a1f8c3fe4add1fd31bba9fdc65dccaecc28"
        ),
        "e2_phase_predecessor_sha256": (
            "592f3ab7c90831c3191f51e9e7dd9a1f8c3fe4add1fd31bba9fdc65dccaecc28"
        ),
    },
    {
        "path": RC0030_SURFACE_PATH,
        "predecessor_size": 290131,
        "predecessor_sha256": (
            "2f797d7aad7f16b234b8a8dad57204b5788e4ae23e43306ac8ca5da790eba7a2"
        ),
        "p4_phase_predecessor_sha256": (
            "8f8ea6f197bac02edc8ee3594165625e1e8f06e5a6a7bb44e41445d880ae9c37"
        ),
        "p5_phase_predecessor_sha256": (
            "8f8ea6f197bac02edc8ee3594165625e1e8f06e5a6a7bb44e41445d880ae9c37"
        ),
        "e2_phase_predecessor_sha256": (
            "5f548499e05e5a982f375dde5f059d7eba08f06fbc59bd0a76d9ed788a1e8eaf"
        ),
    },
    {
        "path": RC0030_MATCHER_PATH,
        "predecessor_size": 589793,
        "predecessor_sha256": (
            "9bdae4b5c3d99e99dd01b622b9b191afbfa0e601789fba082a03c069b70028b5"
        ),
        "p4_phase_predecessor_sha256": (
            "629305364ac50530265d7d87a6ca28678eb3e1be6ac7289ae770b3b5f871d8c9"
        ),
        "p5_phase_predecessor_sha256": (
            "7665406076bdbae621a713df9fdf40ac6bf7cf2bfbbbc6659bcc2829908ddb5a"
        ),
        "e2_phase_predecessor_sha256": (
            "648a3a6690f8df860053c811a5416fcfc9983524e5ff880a0e6921a122a52e30"
        ),
    },
    {
        "path": RC0030_HARD_GATE_PATH,
        "predecessor_size": 129756,
        "predecessor_sha256": (
            "6911291682508bcd6df66d39acb7a6b29b1cfc411434d1ff13160125c9af6c9a"
        ),
        "p4_phase_predecessor_sha256": (
            "1926ef12e74f1a9f53015f2d913cbb4b6881606e57e5078c6f8192e2894af4c7"
        ),
        "p5_phase_predecessor_sha256": (
            "2a70d294a8457d7f9328789ae6cba118d71bef477e2cc9a2ccb4facf24df68ca"
        ),
        "e2_phase_predecessor_sha256": (
            "88514bb2a179e8d726f36e1666d2618330d95979107403ededc93aa35655943b"
        ),
    },
)
RC0030_MODIFIED_OWNER_PATHS = tuple(
    row["path"] for row in RC0030_MODIFIED_OWNER_PREDECESSORS
)
RC0030_E2_CHANGED_OWNER_PATHS = (
    RC0030_SURFACE_PATH,
    RC0030_MATCHER_PATH,
    RC0030_HARD_GATE_PATH,
)

RC0030_CATALOG_PATH = (
    "ai/services/ai_inference/"
    "emlis_ai_step11_rc0030_experiment_surface_catalog_v3.py"
)
RC0030_RUNTIME_ADAPTER_PATH = (
    "ai/services/ai_inference/"
    "emlis_ai_step11_rc0030_experiment_runtime_adapter_v3.py"
)
RC0030_MANIFEST_OWNER_PATH = (
    "ai/services/ai_inference/"
    "emlis_ai_rc0030_surface_planning_experiment_dependency_manifest_v3.py"
)
RC0030_MANIFEST_TOOL_PATH = (
    "ai/tools/emlis_nls_v3_rc0030_surface_planning_dependency_manifest.py"
)
RC0030_BOUNDED_EXPERIMENT_TOOL_PATH = (
    "ai/tools/emlis_nls_v3_rc0030_surface_planning_bounded_experiment.py"
)
RC0030_GENERATED_MANIFEST_PATH = (
    "ai/tests/fixtures/emlis_nls_v3/cycle_001/"
    "cycle001_dependency_manifest_rc0030_surface_planning_experiment.json"
)
RC0030_REPRESENTATIVE_FIXTURE_PATH = (
    "ai/tests/fixtures/emlis_nls_v3/cycle_001/"
    "rc0030_representative8_body_free.json"
)
RC0030_E2_INTEGRATION_PATH = (
    "ai/tests/test_emlis_nls_v3_s11_rc0030_e2_integration.py"
)
RC0030_E3_REPRESENTATIVE_TEST_PATH = (
    "ai/tests/test_emlis_nls_v3_s11_rc0030_e3_representative8.py"
)
RC0030_E4_FROZEN100_TEST_PATH = (
    "ai/tests/test_emlis_nls_v3_s11_rc0030_e4_frozen100_read_only.py"
)
RC0030_E2_INTEGRATION_PHASE_PREDECESSOR_SHA256 = (
    "789008643a4d7ba388a26f35fbf2276eea5f1c3702f94ea6089377ce372d5eaa"
)

RC0030_NEW_PATH_ALLOWLIST = (
    RC0030_MANIFEST_OWNER_PATH,
    RC0030_RUNTIME_ADAPTER_PATH,
    RC0030_CATALOG_PATH,
    RC0030_MANIFEST_TOOL_PATH,
    RC0030_BOUNDED_EXPERIMENT_TOOL_PATH,
    RC0030_GENERATED_MANIFEST_PATH,
    RC0030_REPRESENTATIVE_FIXTURE_PATH,
    "ai/tests/test_emlis_nls_v3_s11_rc0030_surface_planning_red.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0030_surface_planning_mutation.py",
    RC0030_E2_INTEGRATION_PATH,
    "ai/tests/test_emlis_nls_v3_s11_rc0030_forward_inverse_independence.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0030_runtime_disconnect.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0030_predecessor_immutability.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0030_predecessor_behavior_regression.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0030_control_non_regression.py",
    RC0030_E3_REPRESENTATIVE_TEST_PATH,
    RC0030_E4_FROZEN100_TEST_PATH,
    "ai/tests/test_emlis_nls_v3_s11_rc0030_dependency_closure.py",
)
RC0030_P4_ACTIVE_NEW_PATHS = (
    RC0030_MANIFEST_OWNER_PATH,
    RC0030_RUNTIME_ADAPTER_PATH,
    RC0030_CATALOG_PATH,
    RC0030_MANIFEST_TOOL_PATH,
    RC0030_GENERATED_MANIFEST_PATH,
    RC0030_REPRESENTATIVE_FIXTURE_PATH,
    "ai/tests/test_emlis_nls_v3_s11_rc0030_surface_planning_red.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0030_surface_planning_mutation.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0030_forward_inverse_independence.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0030_runtime_disconnect.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0030_dependency_closure.py",
)
RC0030_P4_HASHED_NEW_PATHS = tuple(
    path for path in RC0030_P4_ACTIVE_NEW_PATHS
    if path != RC0030_GENERATED_MANIFEST_PATH
)
RC0030_P4_RESERVED_ABSENT_PATHS = (
    RC0030_BOUNDED_EXPERIMENT_TOOL_PATH,
    RC0030_E2_INTEGRATION_PATH,
    "ai/tests/test_emlis_nls_v3_s11_rc0030_predecessor_immutability.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0030_predecessor_behavior_regression.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0030_control_non_regression.py",
    RC0030_E3_REPRESENTATIVE_TEST_PATH,
    RC0030_E4_FROZEN100_TEST_PATH,
)
RC0030_P5_NEWLY_ACTIVE_PATHS = (
    "ai/tests/test_emlis_nls_v3_s11_rc0030_predecessor_immutability.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0030_predecessor_behavior_regression.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0030_control_non_regression.py",
)
RC0030_P5_ACTIVE_NEW_PATHS = tuple(
    path
    for path in RC0030_NEW_PATH_ALLOWLIST
    if path not in {
        RC0030_BOUNDED_EXPERIMENT_TOOL_PATH,
        RC0030_E2_INTEGRATION_PATH,
        RC0030_E3_REPRESENTATIVE_TEST_PATH,
        RC0030_E4_FROZEN100_TEST_PATH,
    }
)
RC0030_P5_HASHED_NEW_PATHS = tuple(
    path for path in RC0030_P5_ACTIVE_NEW_PATHS
    if path != RC0030_GENERATED_MANIFEST_PATH
)
RC0030_P5_RESERVED_ABSENT_PATHS = (
    RC0030_BOUNDED_EXPERIMENT_TOOL_PATH,
    RC0030_E2_INTEGRATION_PATH,
    RC0030_E3_REPRESENTATIVE_TEST_PATH,
    RC0030_E4_FROZEN100_TEST_PATH,
)
RC0030_E2_NEWLY_ACTIVE_PATHS = (
    RC0030_E2_INTEGRATION_PATH,
)
RC0030_E2_ACTIVE_NEW_PATHS = tuple(
    path
    for path in RC0030_NEW_PATH_ALLOWLIST
    if path not in {
        RC0030_BOUNDED_EXPERIMENT_TOOL_PATH,
        RC0030_E3_REPRESENTATIVE_TEST_PATH,
        RC0030_E4_FROZEN100_TEST_PATH,
    }
)
RC0030_E2_HASHED_NEW_PATHS = tuple(
    path for path in RC0030_E2_ACTIVE_NEW_PATHS
    if path != RC0030_GENERATED_MANIFEST_PATH
)
RC0030_E2_RESERVED_ABSENT_PATHS = (
    RC0030_BOUNDED_EXPERIMENT_TOOL_PATH,
    RC0030_E3_REPRESENTATIVE_TEST_PATH,
    RC0030_E4_FROZEN100_TEST_PATH,
)
RC0030_E3_NEWLY_ACTIVE_PATHS = (
    RC0030_BOUNDED_EXPERIMENT_TOOL_PATH,
    RC0030_E3_REPRESENTATIVE_TEST_PATH,
)
RC0030_E3_ACTIVE_NEW_PATHS = tuple(
    path
    for path in RC0030_NEW_PATH_ALLOWLIST
    if path != RC0030_E4_FROZEN100_TEST_PATH
)
RC0030_E3_HASHED_NEW_PATHS = tuple(
    path for path in RC0030_E3_ACTIVE_NEW_PATHS
    if path != RC0030_GENERATED_MANIFEST_PATH
)
RC0030_E3_RESERVED_ABSENT_PATHS = (
    RC0030_E4_FROZEN100_TEST_PATH,
)
RC0030_LATER_PHASE_ACTIVATION = {
    "E4_FROZEN100": (
        RC0030_E4_FROZEN100_TEST_PATH,
    ),
}
RC0030_LATER_PHASE_ORDER = (
    "E4_FROZEN100",
)

_FLAGS = {
    "experimental_only": True,
    "runtime_connected": False,
    "public_owner_unchanged": True,
    "rc0027_default_behavior_equivalent": True,
    "rc0028_experiment_behavior_equivalent": True,
    "rc0029_experiment_behavior_equivalent": True,
    "eligible_for_formal": False,
    "eligible_for_production": False,
}
_CANONICAL_REBUILD = {
    "algorithm": "artifact_sha256_without_source_dependency_closure_sha256",
    "file_order": "path_ascending",
    "filesystem_discovery_admission": False,
    "deterministic": True,
}
_GENERATED_MANIFEST_POLICY = {
    "path": RC0030_GENERATED_MANIFEST_PATH,
    "included_in_file_hashes": False,
    "included_in_new_file_hashes": False,
    "artifact_hash_authority": "external_body_free_receipt",
}
_SHA_RE = re.compile(r"^[0-9a-f]{64}$")
_SAFE_PATH_RE = re.compile(r"^ai/[A-Za-z0-9_./-]+$")
_PROJECT_MODULE_PREFIXES = ("emlis_ai_", "emlis_nls_", "test_emlis_")


class Rc0030SurfacePlanningDependencyError(ValueError):
    """Fail closed without including source paths or bodies in the code."""

    def __init__(self, code: str) -> None:
        if (
            type(code) is not str
            or re.fullmatch(r"RC0030_[A-Z0-9_]{2,110}", code) is None
        ):
            code = "RC0030_SURFACE_PLANNING_DEPENDENCY_REJECTED"
        self.code = code
        super().__init__(code)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _activation_policy_material() -> dict[str, Any]:
    return {
        "phase": RC0030_MANIFEST_PHASE,
        "exact18_is_closed_maximum": True,
        "active_new_paths": list(sorted(RC0030_E3_ACTIVE_NEW_PATHS)),
        "newly_active_paths": list(sorted(RC0030_E3_NEWLY_ACTIVE_PATHS)),
        "reserved_absent_paths": list(
            sorted(RC0030_E3_RESERVED_ABSENT_PATHS)
        ),
        "later_phase_activation": {
            phase: list(sorted(paths))
            for phase, paths in sorted(
                RC0030_LATER_PHASE_ACTIVATION.items()
            )
        },
        "later_phase_order": list(RC0030_LATER_PHASE_ORDER),
        "activation_is_monotonic": True,
    }


def _phase_predecessor_material() -> dict[str, Any]:
    return {
        "schema_version": RC0030_E2_MANIFEST_SCHEMA,
        "git_commit": RC0030_E2_MANIFEST_GIT_COMMIT,
        "manifest_phase": RC0030_E2_MANIFEST_PHASE,
        "phase_predecessor_git_commit": (
            RC0030_E2_PHASE_PREDECESSOR_GIT_COMMIT
        ),
        "manifest_path": RC0030_GENERATED_MANIFEST_PATH,
        "manifest_file_sha256": RC0030_E2_MANIFEST_FILE_SHA256,
        "manifest_artifact_sha256": RC0030_E2_MANIFEST_ARTIFACT_SHA256,
        "source_dependency_closure_sha256": (
            RC0030_E2_SOURCE_DEPENDENCY_CLOSURE_SHA256
        ),
        "file_hashes_sha256": RC0030_E2_FILE_HASHES_SHA256,
        "source_file_count": RC0030_E2_SOURCE_FILE_COUNT,
        "immutable": True,
    }


def _safe_file_rows(value: Any) -> list[dict[str, str]]:
    if type(value) is not list or not value:
        raise Rc0030SurfacePlanningDependencyError(
            "RC0030_FILE_ROWS_REQUIRED"
        )
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in value:
        if type(item) is not dict or set(item) != {"path", "sha256"}:
            raise Rc0030SurfacePlanningDependencyError(
                "RC0030_FILE_ROW_SHAPE_INVALID"
            )
        path = item.get("path")
        sha256 = item.get("sha256")
        if (
            type(path) is not str
            or _SAFE_PATH_RE.fullmatch(path) is None
            or ".." in Path(path).parts
            or type(sha256) is not str
            or _SHA_RE.fullmatch(sha256) is None
            or sha256 == "0" * 64
            or path in seen
        ):
            raise Rc0030SurfacePlanningDependencyError(
                "RC0030_FILE_ROW_INVALID"
            )
        seen.add(path)
        rows.append({"path": path, "sha256": sha256})
    if rows != sorted(rows, key=lambda row: row["path"]):
        raise Rc0030SurfacePlanningDependencyError(
            "RC0030_FILE_ROWS_NOT_SORTED"
        )
    return rows


def _validated_parent_manifest(value: Any) -> dict[str, Any]:
    if type(value) is not dict:
        raise Rc0030SurfacePlanningDependencyError(
            "RC0030_PARENT_MAPPING_REQUIRED"
        )
    if validate_rc0029_surface_repair_dependency_manifest_shape(value):
        raise Rc0030SurfacePlanningDependencyError(
            "RC0030_PARENT_SHAPE_INVALID"
        )
    try:
        files = _safe_file_rows(value["file_hashes"])
    except (KeyError, TypeError) as error:
        raise Rc0030SurfacePlanningDependencyError(
            "RC0030_PARENT_FILE_ROWS_INVALID"
        ) from error
    if (
        value.get("schema_version")
        != RC0029_SURFACE_REPAIR_DEPENDENCY_MANIFEST_SCHEMA
        or artifact_sha256(value)
        != RC0029_SURFACE_REPAIR_PARENT_MANIFEST_ARTIFACT_SHA256
        or value.get("source_dependency_closure_sha256")
        != RC0029_SURFACE_REPAIR_PARENT_SOURCE_CLOSURE_SHA256
        or len(files) != RC0029_SURFACE_REPAIR_PARENT_SOURCE_FILE_COUNT
        or artifact_sha256(files)
        != RC0029_SURFACE_REPAIR_PARENT_FILE_HASHES_SHA256
    ):
        raise Rc0030SurfacePlanningDependencyError(
            "RC0030_PARENT_BINDING_INVALID"
        )
    return dict(value)


def _module_index(paths: Sequence[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in paths:
        if not path.endswith(".py"):
            continue
        module = Path(path).stem
        if module == "__init__":
            continue
        previous = result.get(module)
        if previous is not None and previous != path:
            raise Rc0030SurfacePlanningDependencyError(
                "RC0030_LOCAL_MODULE_NAME_COLLISION"
            )
        result[module] = path
    return result


class _ImportVisitor(ast.NodeVisitor):
    def __init__(self, literal_strings: Mapping[str, str]) -> None:
        self.static_modules: set[str] = set()
        self.module_scope_static_modules: set[str] = set()
        self.dynamic_modules: list[tuple[str, bool, str]] = []
        self.function_depth = 0
        self.literal_strings = dict(literal_strings)

    def visit_Import(self, node: ast.Import) -> None:
        modules = {alias.name.split(".", 1)[0] for alias in node.names}
        self.static_modules.update(modules)
        if self.function_depth == 0:
            self.module_scope_static_modules.update(modules)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        modules: set[str] = set()
        if node.module:
            modules.add(node.module.split(".", 1)[0])
        elif node.level:
            modules.update(
                alias.name.split(".", 1)[0] for alias in node.names
            )
        self.static_modules.update(modules)
        if self.function_depth == 0:
            self.module_scope_static_modules.update(modules)

    def _visit_function(self, node: ast.AST) -> None:
        self.function_depth += 1
        self.generic_visit(node)
        self.function_depth -= 1

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function(node)

    def visit_Call(self, node: ast.Call) -> None:
        kind: str | None = None
        if isinstance(node.func, ast.Name) and node.func.id == "__import__":
            kind = "function_local_literal___import__"
        elif (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "import_module"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "importlib"
        ) or (
            isinstance(node.func, ast.Name)
            and node.func.id == "import_module"
        ):
            kind = "function_local_literal_import_module"
        if kind is not None and node.args:
            first = node.args[0]
            value: str | None = None
            if isinstance(first, ast.Constant) and type(first.value) is str:
                value = first.value
            elif isinstance(first, ast.Name):
                value = self.literal_strings.get(first.id)
            if value is not None:
                module = value.split(".", 1)[0]
                self.dynamic_modules.append(
                    (module, self.function_depth > 0, kind)
                )
        self.generic_visit(node)


def _source_imports(
    source: bytes,
) -> tuple[
    tuple[str, ...],
    tuple[str, ...],
    tuple[tuple[str, bool, str], ...],
]:
    try:
        tree = ast.parse(source)
    except (SyntaxError, UnicodeError) as error:
        raise Rc0030SurfacePlanningDependencyError(
            "RC0030_SOURCE_AST_INVALID"
        ) from error
    literal_strings: dict[str, str] = {}
    assigned_names: set[str] = set()
    for node in tree.body:
        names: tuple[str, ...] = ()
        value: ast.expr | None = None
        if isinstance(node, ast.Assign):
            names = tuple(
                target.id
                for target in node.targets
                if isinstance(target, ast.Name)
            )
            value = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(
            node.target, ast.Name
        ):
            names = (node.target.id,)
            value = node.value
        for name in names:
            if name in assigned_names:
                literal_strings.pop(name, None)
                continue
            assigned_names.add(name)
            if isinstance(value, ast.Constant) and type(value.value) is str:
                literal_strings[name] = value.value
    visitor = _ImportVisitor(literal_strings)
    visitor.visit(tree)
    return (
        tuple(sorted(visitor.static_modules)),
        tuple(sorted(visitor.module_scope_static_modules)),
        tuple(sorted(set(visitor.dynamic_modules))),
    )


def _is_project_module(module: str) -> bool:
    return module.startswith(_PROJECT_MODULE_PREFIXES)


def _delta_import_edges(
    repo_root: Path,
    *,
    closure_paths: Sequence[str],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    index = _module_index(closure_paths)
    static_edges: set[tuple[str, str]] = set()
    dynamic_edges: set[tuple[str, str, str]] = set()
    importer_paths = tuple(
        path
        for path in (
            *RC0030_MODIFIED_OWNER_PATHS,
            *RC0030_E3_HASHED_NEW_PATHS,
        )
        if path.endswith(".py")
    )
    experiment_modules = {
        Path(RC0030_CATALOG_PATH).stem,
        Path(RC0030_RUNTIME_ADAPTER_PATH).stem,
        Path(RC0030_MANIFEST_OWNER_PATH).stem,
    }
    for importer_path in importer_paths:
        try:
            (
                static_modules,
                module_scope_static_modules,
                dynamic_modules,
            ) = _source_imports(
                (repo_root / importer_path).read_bytes()
            )
        except OSError as error:
            raise Rc0030SurfacePlanningDependencyError(
                "RC0030_IMPORT_SOURCE_UNAVAILABLE"
            ) from error
        for module in static_modules:
            imported_path = index.get(module)
            if imported_path is None:
                if _is_project_module(module):
                    raise Rc0030SurfacePlanningDependencyError(
                        "RC0030_UNBOUND_PROJECT_IMPORT"
                    )
                continue
            if (
                importer_path in RC0030_MODIFIED_OWNER_PATHS
                and module in experiment_modules
                and module in module_scope_static_modules
            ):
                raise Rc0030SurfacePlanningDependencyError(
                    "RC0030_EXACT_OWNER_STATIC_EXPERIMENT_IMPORT_FORBIDDEN"
                )
            static_edges.add((importer_path, imported_path))
        for module, function_local, kind in dynamic_modules:
            imported_path = index.get(module)
            if imported_path is None:
                if _is_project_module(module):
                    raise Rc0030SurfacePlanningDependencyError(
                        "RC0030_UNBOUND_DYNAMIC_PROJECT_IMPORT"
                    )
                continue
            if not function_local:
                raise Rc0030SurfacePlanningDependencyError(
                    "RC0030_NONLOCAL_DYNAMIC_IMPORT_FORBIDDEN"
                )
            dynamic_edges.add((importer_path, imported_path, kind))
    return (
        [
            {"importer_path": importer, "imported_path": imported}
            for importer, imported in sorted(static_edges)
        ],
        [
            {
                "importer_path": importer,
                "imported_path": imported,
                "import_kind": kind,
            }
            for importer, imported, kind in sorted(dynamic_edges)
        ],
    )


def find_rc0030_surface_planning_unexpected_paths(
    repo_root: Path,
) -> tuple[str, ...]:
    """Discover rc0030-named paths only to reject unapproved additions."""

    known = set(RC0030_NEW_PATH_ALLOWLIST)
    found: list[str] = []
    roots_and_suffixes = (
        (repo_root / "ai/services", frozenset({".py"})),
        (repo_root / "ai/tools", frozenset({".py"})),
        (repo_root / "ai/tests", frozenset({".py", ".json"})),
    )
    for root, suffixes in roots_and_suffixes:
        for path in sorted(root.rglob("*")):
            if (
                not path.is_file()
                or path.suffix not in suffixes
                or "rc0030" not in path.name.lower()
            ):
                continue
            relative = path.relative_to(repo_root).as_posix()
            if relative not in known:
                found.append(relative)
    return tuple(sorted(set(found)))


def find_rc0030_surface_planning_forbidden_reverse_imports(
    repo_root: Path,
) -> tuple[str, ...]:
    """Reject any shared/public service or tool loading rc0030 modules."""

    forbidden_modules = frozenset(
        {
            Path(RC0030_CATALOG_PATH).stem,
            Path(RC0030_RUNTIME_ADAPTER_PATH).stem,
            Path(RC0030_MANIFEST_OWNER_PATH).stem,
        }
    )
    excluded = set(RC0030_MODIFIED_OWNER_PATHS) | set(
        RC0030_E3_HASHED_NEW_PATHS
    )
    found: list[str] = []
    for root in (repo_root / "ai/services", repo_root / "ai/tools"):
        for path in sorted(root.rglob("*.py")):
            relative = path.relative_to(repo_root).as_posix()
            if relative in excluded:
                continue
            try:
                (
                    static_modules,
                    _module_scope,
                    dynamic_modules,
                ) = _source_imports(
                    path.read_bytes()
                )
            except OSError as error:
                raise Rc0030SurfacePlanningDependencyError(
                    "RC0030_REVERSE_IMPORT_SCAN_UNAVAILABLE"
                ) from error
            imported = set(static_modules) | {
                module for module, _local, _kind in dynamic_modules
            }
            if imported & forbidden_modules:
                found.append(relative)
    return tuple(found)


def find_rc0030_surface_planning_reserved_paths(
    repo_root: Path,
) -> tuple[str, ...]:
    """Return later-phase paths that E3 requires to remain absent."""

    return tuple(
        sorted(
            path
            for path in RC0030_E3_RESERVED_ABSENT_PATHS
            if (repo_root / path).exists()
        )
    )


def _parent_binding(parent: Mapping[str, Any]) -> dict[str, Any]:
    _safe_file_rows(parent["file_hashes"])
    return {
        "schema_version": (
            RC0029_SURFACE_REPAIR_DEPENDENCY_MANIFEST_SCHEMA
        ),
        "manifest_path": RC0029_SURFACE_REPAIR_PARENT_MANIFEST_PATH,
        "manifest_file_sha256": (
            RC0029_SURFACE_REPAIR_PARENT_MANIFEST_FILE_SHA256
        ),
        "manifest_artifact_sha256": (
            RC0029_SURFACE_REPAIR_PARENT_MANIFEST_ARTIFACT_SHA256
        ),
        "source_dependency_closure_sha256": (
            RC0029_SURFACE_REPAIR_PARENT_SOURCE_CLOSURE_SHA256
        ),
        "source_file_count": RC0029_SURFACE_REPAIR_PARENT_SOURCE_FILE_COUNT,
        "file_hashes_sha256": (
            RC0029_SURFACE_REPAIR_PARENT_FILE_HASHES_SHA256
        ),
        "immutable": True,
    }


def _modified_owner_rows(
    repo_root: Path,
    *,
    parent_by_path: Mapping[str, str],
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    rows: list[dict[str, Any]] = []
    current_by_path: dict[str, str] = {}
    for predecessor in RC0030_MODIFIED_OWNER_PREDECESSORS:
        path = predecessor["path"]
        expected = predecessor["predecessor_sha256"]
        if parent_by_path.get(path) != expected:
            raise Rc0030SurfacePlanningDependencyError(
                "RC0030_MODIFIED_OWNER_PARENT_MISMATCH"
            )
        try:
            source = (repo_root / path).read_bytes()
        except OSError as error:
            raise Rc0030SurfacePlanningDependencyError(
                "RC0030_MODIFIED_OWNER_UNAVAILABLE"
            ) from error
        size = predecessor["predecessor_size"]
        p4_phase_predecessor = predecessor[
            "p4_phase_predecessor_sha256"
        ]
        p5_phase_predecessor = predecessor[
            "p5_phase_predecessor_sha256"
        ]
        e2_phase_predecessor = predecessor[
            "e2_phase_predecessor_sha256"
        ]
        if (
            type(size) is not int
            or size <= 0
            or len(source) <= size
            or _sha256_bytes(source[:size]) != expected
        ):
            raise Rc0030SurfacePlanningDependencyError(
                "RC0030_MODIFIED_OWNER_PREFIX_DRIFT"
            )
        current = _sha256_bytes(source)
        current_by_path[path] = current
        rows.append(
            {
                "path": path,
                "predecessor_size": size,
                "predecessor_sha256": expected,
                "p4_phase_predecessor_sha256": p4_phase_predecessor,
                "p5_phase_predecessor_sha256": p5_phase_predecessor,
                "phase_predecessor_sha256": e2_phase_predecessor,
                "current_sha256": current,
                "append_only_prefix_verified": True,
            }
        )
        phase_changed = path in RC0030_E2_CHANGED_OWNER_PATHS
        if (
            current != e2_phase_predecessor
            or (phase_changed and current == p5_phase_predecessor)
            or (not phase_changed and current != p5_phase_predecessor)
        ):
            raise Rc0030SurfacePlanningDependencyError(
                "RC0030_E2_PHASE_OWNER_BINDING_INVALID"
            )
    rows.sort(key=lambda row: row["path"])
    return rows, current_by_path


def build_rc0030_surface_planning_dependency_manifest(
    parent_manifest: Mapping[str, Any],
    *,
    repo_root: Path,
) -> dict[str, Any]:
    """Build the E3-active rc0030 delta over immutable E2/P5/P4 evidence."""

    parent = _validated_parent_manifest(parent_manifest)
    parent_files = _safe_file_rows(parent["file_hashes"])
    parent_by_path = {row["path"]: row["sha256"] for row in parent_files}
    if any(path in parent_by_path for path in RC0030_E3_HASHED_NEW_PATHS):
        raise Rc0030SurfacePlanningDependencyError(
            "RC0030_NEW_PATH_ALREADY_IN_PARENT"
        )
    if RC0030_GENERATED_MANIFEST_PATH in parent_by_path:
        raise Rc0030SurfacePlanningDependencyError(
            "RC0030_GENERATED_SELF_HASH_IN_PARENT"
        )

    modified_rows, current_by_path = _modified_owner_rows(
        repo_root,
        parent_by_path=parent_by_path,
    )
    current_parent_rows: list[dict[str, str]] = []
    for row in parent_files:
        path = row["path"]
        current = current_by_path.get(path)
        if current is None:
            try:
                current = _sha256(repo_root / path)
            except OSError as error:
                raise Rc0030SurfacePlanningDependencyError(
                    "RC0030_IMMUTABLE_PARENT_SOURCE_UNAVAILABLE"
                ) from error
            if current != row["sha256"]:
                raise Rc0030SurfacePlanningDependencyError(
                    "RC0030_IMMUTABLE_PARENT_SOURCE_DRIFT"
                )
        current_parent_rows.append({"path": path, "sha256": current})

    new_rows: list[dict[str, str]] = []
    for path in RC0030_E3_HASHED_NEW_PATHS:
        try:
            sha256 = _sha256(repo_root / path)
        except OSError as error:
            raise Rc0030SurfacePlanningDependencyError(
                "RC0030_ALLOWLIST_PATH_MISSING"
            ) from error
        if (
            path == RC0030_E2_INTEGRATION_PATH
            and sha256
            != RC0030_E2_INTEGRATION_PHASE_PREDECESSOR_SHA256
        ):
            raise Rc0030SurfacePlanningDependencyError(
                "RC0030_E2_INTEGRATION_PREDECESSOR_DRIFT"
            )
        new_rows.append({"path": path, "sha256": sha256})
    new_rows.sort(key=lambda row: row["path"])

    unexpected = find_rc0030_surface_planning_unexpected_paths(repo_root)
    if unexpected:
        raise Rc0030SurfacePlanningDependencyError(
            "RC0030_UNEXPECTED_PATH"
        )
    reserved_present = find_rc0030_surface_planning_reserved_paths(repo_root)
    if reserved_present:
        raise Rc0030SurfacePlanningDependencyError(
            "RC0030_RESERVED_PATH_PRESENT_BEFORE_PHASE"
        )
    reverse_imports = find_rc0030_surface_planning_forbidden_reverse_imports(
        repo_root
    )
    if reverse_imports:
        raise Rc0030SurfacePlanningDependencyError(
            "RC0030_FORBIDDEN_REVERSE_IMPORT"
        )

    files = sorted(
        current_parent_rows + new_rows,
        key=lambda row: row["path"],
    )
    static_edges, dynamic_edges = _delta_import_edges(
        repo_root,
        closure_paths=[row["path"] for row in files],
    )
    material: dict[str, Any] = {
        "schema_version": RC0030_SURFACE_PLANNING_DEPENDENCY_MANIFEST_SCHEMA,
        "experiment_id": RC0030_SURFACE_PLANNING_EXPERIMENT_ID,
        "baseline_git_commit": RC0030_BASELINE_GIT_COMMIT,
        "phase_predecessor_git_commit": (
            RC0030_E3_PHASE_PREDECESSOR_GIT_COMMIT
        ),
        "manifest_phase": RC0030_MANIFEST_PHASE,
        "parent": _parent_binding(parent),
        "phase_predecessor": _phase_predecessor_material(),
        "modified_owner_file_hashes": modified_rows,
        "new_path_allowlist": list(sorted(RC0030_NEW_PATH_ALLOWLIST)),
        "activation_policy": _activation_policy_material(),
        "new_file_hashes": new_rows,
        "generated_manifest": dict(_GENERATED_MANIFEST_POLICY),
        "flags": dict(_FLAGS),
        "canonical_rebuild": dict(_CANONICAL_REBUILD),
        "source_file_count": len(files),
        "file_hashes": files,
        "static_project_import_edges": static_edges,
        "dynamic_project_import_edges": dynamic_edges,
        "unexpected_paths": [],
        "unbound_project_imports": [],
        "forbidden_reverse_imports": [],
        "reserved_paths_present": [],
        "body_free": True,
    }
    return {
        **material,
        "source_dependency_closure_sha256": artifact_sha256(material),
    }


def _normalized_edges(
    value: Any,
    *,
    dynamic: bool,
) -> tuple[tuple[str, ...], ...] | None:
    if type(value) is not list:
        return None
    expected_keys = (
        {"importer_path", "imported_path", "import_kind"}
        if dynamic
        else {"importer_path", "imported_path"}
    )
    rows: list[tuple[str, ...]] = []
    for item in value:
        if type(item) is not dict or set(item) != expected_keys:
            return None
        values = (
            item.get("importer_path"),
            item.get("imported_path"),
            *([item.get("import_kind")] if dynamic else []),
        )
        if any(type(part) is not str or not part for part in values):
            return None
        rows.append(values)
    normalized = tuple(rows)
    if normalized != tuple(sorted(set(normalized))):
        return None
    return normalized


def validate_rc0030_surface_planning_dependency_manifest_shape(
    value: Any,
) -> tuple[str, ...]:
    """Validate exact fields and canonical commitments without filesystem."""

    if type(value) is not dict:
        return ("RC0030_MANIFEST_MAPPING_REQUIRED",)
    expected_keys = {
        "schema_version",
        "experiment_id",
        "baseline_git_commit",
        "phase_predecessor_git_commit",
        "manifest_phase",
        "parent",
        "phase_predecessor",
        "modified_owner_file_hashes",
        "new_path_allowlist",
        "activation_policy",
        "new_file_hashes",
        "generated_manifest",
        "flags",
        "canonical_rebuild",
        "source_file_count",
        "file_hashes",
        "static_project_import_edges",
        "dynamic_project_import_edges",
        "unexpected_paths",
        "unbound_project_imports",
        "forbidden_reverse_imports",
        "reserved_paths_present",
        "body_free",
        "source_dependency_closure_sha256",
    }
    issues: set[str] = set()
    if set(value) != expected_keys:
        issues.add("RC0030_MANIFEST_SHAPE_INVALID")
    if (
        value.get("schema_version")
        != RC0030_SURFACE_PLANNING_DEPENDENCY_MANIFEST_SCHEMA
        or value.get("experiment_id") != RC0030_SURFACE_PLANNING_EXPERIMENT_ID
        or value.get("baseline_git_commit") != RC0030_BASELINE_GIT_COMMIT
        or value.get("phase_predecessor_git_commit")
        != RC0030_E3_PHASE_PREDECESSOR_GIT_COMMIT
        or value.get("manifest_phase") != RC0030_MANIFEST_PHASE
        or value.get("body_free") is not True
    ):
        issues.add("RC0030_MANIFEST_IDENTITY_INVALID")
    if value.get("flags") != _FLAGS:
        issues.add("RC0030_FLAGS_INVALID")
    if value.get("canonical_rebuild") != _CANONICAL_REBUILD:
        issues.add("RC0030_CANONICAL_REBUILD_INVALID")
    if value.get("generated_manifest") != _GENERATED_MANIFEST_POLICY:
        issues.add("RC0030_SELF_HASH_POLICY_INVALID")
    if value.get("new_path_allowlist") != list(
        sorted(RC0030_NEW_PATH_ALLOWLIST)
    ):
        issues.add("RC0030_PATH_ALLOWLIST_INVALID")
    if value.get("activation_policy") != _activation_policy_material():
        issues.add("RC0030_ACTIVATION_POLICY_INVALID")
    later_paths = tuple(
        path
        for phase in RC0030_LATER_PHASE_ORDER
        for path in RC0030_LATER_PHASE_ACTIVATION.get(phase, ())
    )
    if (
        len(RC0030_NEW_PATH_ALLOWLIST) != 18
        or set(RC0030_E3_ACTIVE_NEW_PATHS)
        & set(RC0030_E3_RESERVED_ABSENT_PATHS)
        or set(RC0030_E3_ACTIVE_NEW_PATHS)
        | set(RC0030_E3_RESERVED_ABSENT_PATHS)
        != set(RC0030_NEW_PATH_ALLOWLIST)
        or len(RC0030_E3_ACTIVE_NEW_PATHS) != 17
        or len(RC0030_E3_HASHED_NEW_PATHS) != 16
        or len(RC0030_E3_RESERVED_ABSENT_PATHS) != 1
        or set(RC0030_E3_NEWLY_ACTIVE_PATHS)
        != set(RC0030_E3_ACTIVE_NEW_PATHS)
        - set(RC0030_E2_ACTIVE_NEW_PATHS)
        or len(later_paths) != len(set(later_paths))
        or set(later_paths) != set(RC0030_E3_RESERVED_ABSENT_PATHS)
        or set(RC0030_LATER_PHASE_ORDER)
        != set(RC0030_LATER_PHASE_ACTIVATION)
    ):
        issues.add("RC0030_ACTIVATION_PARTITION_INVALID")
    expected_parent = {
        "schema_version": (
            RC0029_SURFACE_REPAIR_DEPENDENCY_MANIFEST_SCHEMA
        ),
        "manifest_path": RC0029_SURFACE_REPAIR_PARENT_MANIFEST_PATH,
        "manifest_file_sha256": (
            RC0029_SURFACE_REPAIR_PARENT_MANIFEST_FILE_SHA256
        ),
        "manifest_artifact_sha256": (
            RC0029_SURFACE_REPAIR_PARENT_MANIFEST_ARTIFACT_SHA256
        ),
        "source_dependency_closure_sha256": (
            RC0029_SURFACE_REPAIR_PARENT_SOURCE_CLOSURE_SHA256
        ),
        "source_file_count": RC0029_SURFACE_REPAIR_PARENT_SOURCE_FILE_COUNT,
        "file_hashes_sha256": (
            RC0029_SURFACE_REPAIR_PARENT_FILE_HASHES_SHA256
        ),
        "immutable": True,
    }
    if value.get("parent") != expected_parent:
        issues.add("RC0030_PARENT_BINDING_INVALID")
    if value.get("phase_predecessor") != _phase_predecessor_material():
        issues.add("RC0030_PHASE_PREDECESSOR_BINDING_INVALID")
    if any(
        value.get(key) != []
        for key in (
            "unexpected_paths",
            "unbound_project_imports",
            "forbidden_reverse_imports",
            "reserved_paths_present",
        )
    ):
        issues.add("RC0030_OPEN_DEPENDENCY_SET")

    try:
        files = _safe_file_rows(value.get("file_hashes"))
        new_rows = _safe_file_rows(value.get("new_file_hashes"))
    except Rc0030SurfacePlanningDependencyError:
        issues.add("RC0030_FILE_ROWS_INVALID")
        files = []
        new_rows = []
    by_path = {row["path"]: row["sha256"] for row in files}
    new_by_path = {row["path"]: row["sha256"] for row in new_rows}
    if (
        set(new_by_path) != set(RC0030_E3_HASHED_NEW_PATHS)
        or new_by_path.get(RC0030_E2_INTEGRATION_PATH)
        != RC0030_E2_INTEGRATION_PHASE_PREDECESSOR_SHA256
        or any(by_path.get(path) != sha for path, sha in new_by_path.items())
        or RC0030_GENERATED_MANIFEST_PATH in by_path
        or value.get("source_file_count") != len(files)
        or len(files)
        != RC0029_SURFACE_REPAIR_PARENT_SOURCE_FILE_COUNT
        + len(RC0030_E3_HASHED_NEW_PATHS)
    ):
        issues.add("RC0030_FILE_CLOSURE_INVALID")

    modified = value.get("modified_owner_file_hashes")
    expected_predecessors = {
        row["path"]: row for row in RC0030_MODIFIED_OWNER_PREDECESSORS
    }
    if type(modified) is not list:
        issues.add("RC0030_MODIFIED_OWNER_LEDGER_INVALID")
    else:
        seen: set[str] = set()
        normalized: list[str] = []
        for row in modified:
            if (
                type(row) is not dict
                or set(row)
                != {
                    "path",
                    "predecessor_size",
                    "predecessor_sha256",
                    "p4_phase_predecessor_sha256",
                    "p5_phase_predecessor_sha256",
                    "phase_predecessor_sha256",
                    "current_sha256",
                    "append_only_prefix_verified",
                }
            ):
                issues.add("RC0030_MODIFIED_OWNER_LEDGER_INVALID")
                continue
            path = row.get("path")
            predecessor = expected_predecessors.get(path)
            if (
                predecessor is None
                or row.get("predecessor_size")
                != predecessor["predecessor_size"]
                or row.get("predecessor_sha256")
                != predecessor["predecessor_sha256"]
                or row.get("p4_phase_predecessor_sha256")
                != predecessor["p4_phase_predecessor_sha256"]
                or row.get("p5_phase_predecessor_sha256")
                != predecessor["p5_phase_predecessor_sha256"]
                or row.get("phase_predecessor_sha256")
                != predecessor["e2_phase_predecessor_sha256"]
                or type(row.get("current_sha256")) is not str
                or _SHA_RE.fullmatch(row["current_sha256"]) is None
                or row.get("current_sha256")
                == predecessor["predecessor_sha256"]
                or row.get("current_sha256")
                != predecessor["e2_phase_predecessor_sha256"]
                or row.get("append_only_prefix_verified") is not True
                or by_path.get(path) != row.get("current_sha256")
                or path in seen
            ):
                issues.add("RC0030_MODIFIED_OWNER_LEDGER_INVALID")
            if predecessor is not None:
                phase_changed = path in RC0030_E2_CHANGED_OWNER_PATHS
                if (
                    (
                        phase_changed
                        and row.get("current_sha256")
                        == predecessor["p5_phase_predecessor_sha256"]
                    )
                    or (
                        not phase_changed
                        and row.get("current_sha256")
                        != predecessor["p5_phase_predecessor_sha256"]
                    )
                ):
                    issues.add("RC0030_E2_PHASE_OWNER_BINDING_INVALID")
            if type(path) is str:
                seen.add(path)
                normalized.append(path)
        if (
            set(seen) != set(RC0030_MODIFIED_OWNER_PATHS)
            or normalized != sorted(normalized)
        ):
            issues.add("RC0030_MODIFIED_OWNER_LEDGER_INVALID")

    static_edges = _normalized_edges(
        value.get("static_project_import_edges"),
        dynamic=False,
    )
    dynamic_edges = _normalized_edges(
        value.get("dynamic_project_import_edges"),
        dynamic=True,
    )
    if static_edges is None or dynamic_edges is None:
        issues.add("RC0030_IMPORT_GRAPH_INVALID")
    else:
        if any(
            importer not in by_path or imported not in by_path
            for importer, imported in static_edges
        ) or any(
            importer not in by_path or imported not in by_path
            for importer, imported, _kind in dynamic_edges
        ):
            issues.add("RC0030_IMPORT_GRAPH_INVALID")

    closure = value.get("source_dependency_closure_sha256")
    if type(closure) is not str or _SHA_RE.fullmatch(closure) is None:
        issues.add("RC0030_CLOSURE_HASH_INVALID")
    else:
        material = {
            key: item
            for key, item in value.items()
            if key != "source_dependency_closure_sha256"
        }
        try:
            recomputed = artifact_sha256(material)
        except (RecursionError, TypeError, ValueError, UnicodeError):
            recomputed = None
        if recomputed != closure:
            issues.add("RC0030_CLOSURE_HASH_MISMATCH")
    return tuple(sorted(issues))


def validate_rc0030_surface_planning_dependency_manifest(
    value: Any,
    *,
    parent_manifest: Mapping[str, Any],
    repo_root: Path,
) -> tuple[str, ...]:
    shape_issues = validate_rc0030_surface_planning_dependency_manifest_shape(
        value
    )
    if shape_issues:
        return shape_issues
    try:
        expected = build_rc0030_surface_planning_dependency_manifest(
            parent_manifest,
            repo_root=repo_root,
        )
    except (
        KeyError,
        OSError,
        TypeError,
        Rc0030SurfacePlanningDependencyError,
    ):
        return ("RC0030_DEPENDENCY_UNAVAILABLE_OR_DRIFTED",)
    if value != expected:
        return ("RC0030_DEPENDENCY_RECOMPUTATION_MISMATCH",)
    return ()


__all__ = [
    "RC0029_SURFACE_REPAIR_PARENT_MANIFEST_FILE_SHA256",
    "RC0029_SURFACE_REPAIR_PARENT_MANIFEST_PATH",
    "RC0030_BASELINE_GIT_COMMIT",
    "RC0030_E2_ACTIVE_NEW_PATHS",
    "RC0030_E2_CHANGED_OWNER_PATHS",
    "RC0030_E2_FILE_HASHES_SHA256",
    "RC0030_E2_HASHED_NEW_PATHS",
    "RC0030_E2_INTEGRATION_PATH",
    "RC0030_E2_INTEGRATION_PHASE_PREDECESSOR_SHA256",
    "RC0030_E2_MANIFEST_ARTIFACT_SHA256",
    "RC0030_E2_MANIFEST_FILE_SHA256",
    "RC0030_E2_MANIFEST_GIT_COMMIT",
    "RC0030_E2_MANIFEST_PHASE",
    "RC0030_E2_MANIFEST_SCHEMA",
    "RC0030_E2_NEWLY_ACTIVE_PATHS",
    "RC0030_E2_PHASE_PREDECESSOR_GIT_COMMIT",
    "RC0030_E2_RESERVED_ABSENT_PATHS",
    "RC0030_E2_SOURCE_DEPENDENCY_CLOSURE_SHA256",
    "RC0030_E2_SOURCE_FILE_COUNT",
    "RC0030_E3_ACTIVE_NEW_PATHS",
    "RC0030_E3_HASHED_NEW_PATHS",
    "RC0030_E3_NEWLY_ACTIVE_PATHS",
    "RC0030_E3_PHASE_PREDECESSOR_GIT_COMMIT",
    "RC0030_E3_REPRESENTATIVE_TEST_PATH",
    "RC0030_E3_RESERVED_ABSENT_PATHS",
    "RC0030_E4_FROZEN100_TEST_PATH",
    "RC0030_GENERATED_MANIFEST_PATH",
    "RC0030_LATER_PHASE_ACTIVATION",
    "RC0030_LATER_PHASE_ORDER",
    "RC0030_MANIFEST_PHASE",
    "RC0030_MODIFIED_OWNER_PATHS",
    "RC0030_MODIFIED_OWNER_PREDECESSORS",
    "RC0030_NEW_PATH_ALLOWLIST",
    "RC0030_P4_ACTIVE_NEW_PATHS",
    "RC0030_P4_HASHED_NEW_PATHS",
    "RC0030_P4_MANIFEST_ARTIFACT_SHA256",
    "RC0030_P4_MANIFEST_FILE_SHA256",
    "RC0030_P4_MANIFEST_PHASE",
    "RC0030_P4_MANIFEST_SCHEMA",
    "RC0030_P4_PHASE_PREDECESSOR_GIT_COMMIT",
    "RC0030_P4_RESERVED_ABSENT_PATHS",
    "RC0030_P4_SOURCE_DEPENDENCY_CLOSURE_SHA256",
    "RC0030_P4_SOURCE_FILE_COUNT",
    "RC0030_P5_ACTIVE_NEW_PATHS",
    "RC0030_P5_FILE_HASHES_SHA256",
    "RC0030_P5_HASHED_NEW_PATHS",
    "RC0030_P5_MANIFEST_ARTIFACT_SHA256",
    "RC0030_P5_MANIFEST_FILE_SHA256",
    "RC0030_P5_MANIFEST_GIT_COMMIT",
    "RC0030_P5_MANIFEST_PHASE",
    "RC0030_P5_MANIFEST_SCHEMA",
    "RC0030_P5_NEWLY_ACTIVE_PATHS",
    "RC0030_P5_PHASE_PREDECESSOR_GIT_COMMIT",
    "RC0030_P5_RESERVED_ABSENT_PATHS",
    "RC0030_P5_SOURCE_DEPENDENCY_CLOSURE_SHA256",
    "RC0030_P5_SOURCE_FILE_COUNT",
    "RC0030_SURFACE_PLANNING_DEPENDENCY_MANIFEST_SCHEMA",
    "RC0030_SURFACE_PLANNING_EXPERIMENT_ID",
    "Rc0030SurfacePlanningDependencyError",
    "build_rc0030_surface_planning_dependency_manifest",
    "find_rc0030_surface_planning_forbidden_reverse_imports",
    "find_rc0030_surface_planning_reserved_paths",
    "find_rc0030_surface_planning_unexpected_paths",
    "validate_rc0030_surface_planning_dependency_manifest",
    "validate_rc0030_surface_planning_dependency_manifest_shape",
]
