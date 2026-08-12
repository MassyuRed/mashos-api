#!/usr/bin/env python3
"""Effect-free exact18 tests for the G4-B preparation controller family V1."""

from __future__ import annotations

import ast
import base64
import copy
import hashlib
import io
import os
from pathlib import Path
import stat
import tempfile
import types
import unittest
from unittest import mock
import zipfile

from ai.tools import emlis_nls_v3_s11_g4b_runtime_acquisition_v1 as acquisition
from ai.tools import emlis_nls_v3_s11_g4b_runtime_admission_bridge_v1 as bridge
from ai.tools import emlis_nls_v3_s11_g4b_runtime_admission_contract_v1 as checker_contract
from ai.tools import emlis_nls_v3_s11_g4b_runtime_materialization_v1 as materialization
from ai.tools import emlis_nls_v3_s11_g4b_runtime_preparation_contract_v1 as contract
from ai.tools import emlis_nls_v3_s11_g4b_runtime_preparation_controller_v1 as controller


REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS = REPO_ROOT / "ai" / "tools"
CONFIGS = REPO_ROOT / "ai" / "configs"
DERIVED_LOCK = CONFIGS / "emlis_nls_v3_s11_g4b_runtime_preparation_exact5_lock_v1.json"
FORMAL_LOCK = CONFIGS / "emlis_nls_v3_recovery_epoch002_formal_worker_bootstrap_lock_v1.json"
SHA256_ZERO = "0" * 64


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _path_plan(authority_root: str = "/private/g4b-authority", repo: str = "/repo") -> dict[str, str]:
    plan = {
        "authority_root": authority_root,
        "controller_test_cwd": repo,
        "checker_test_cwd": repo,
    }
    for role, leaf in contract.PreparationContractV1.PATH_ROLE_LEAVES:
        plan[role] = authority_root + "/" + leaf
    return plan


def _execution_request() -> dict[str, object]:
    c = contract.PreparationContractV1
    authority_id = "AUTHORITY_001"
    observation_session_id = "OBSERVATION_001"
    stable_binding = "1" * 64
    attestation = {
        "schema_version": c.EGRESS_ATTESTATION_SCHEMA,
        "source_class": c.EGRESS_ISSUER_CLASS,
        "issuer_policy_id": c.EGRESS_ISSUER_POLICY_ID,
        "platform_control_state_instance_id": "PLATFORM_STATE_001",
        "issuer_provenance_binding_sha256": "",
        "stable_authority_approval_binding_sha256": stable_binding,
        "approved_candidate_body_sha256": c.APPROVED_CANDIDATE_BODY_SHA256,
        "policy_id": c.ACQUISITION_POLICY_ID,
        "allowed_scheme": c.ALLOWED_SCHEME,
        "allowed_hosts": list(c.ALLOWED_HOSTS),
        "enforcement_scope": "CURRENT_G4B_ONE_SHOT_ACQUISITION_EXACT1",
        "authority_id": authority_id,
        "observation_session_id": observation_session_id,
        "acquisition_process_count": 1,
        "active": True,
        "issued_at": "2026-08-12T00:00:00Z",
        "expires_at": "2026-08-12T00:15:00Z",
    }
    provenance = {key: attestation[key] for key in c.ISSUER_PROVENANCE_KEYS}
    attestation["issuer_provenance_binding_sha256"] = contract.canonical_sha256(provenance)
    attestation_sha = contract.canonical_sha256(attestation)
    return {
        "schema_version": c.EXECUTION_REQUEST_SCHEMA,
        "candidate_id": c.CANDIDATE_ID,
        "approved_candidate_body_sha256": c.APPROVED_CANDIDATE_BODY_SHA256,
        "stable_authority_approval_binding_sha256": stable_binding,
        "authority_id": authority_id,
        "observation_session_id": observation_session_id,
        "receiver_session_id": observation_session_id,
        "receiver_nonce": "NONCE_001",
        "expected_git": {
            "cocolon_commit": "a" * 40,
            "cocolon_tree": "b" * 40,
            "mashos_api_commit": "c" * 40,
            "mashos_api_tree": "d" * 40,
        },
        "control_runtime": {
            "executable": "/control/python",
            "implementation": c.EXPECTED_IMPLEMENTATION,
            "python_version": c.EXPECTED_PYTHON_VERSION,
            "platform_tag": c.EXPECTED_PLATFORM_TAG,
            "resolved_interpreter_sha256": c.EXPECTED_INTERPRETER_SHA256,
            "pip_version": c.EXPECTED_PIP_VERSION,
            "pip_installed_source_manifest_sha256": "e" * 64,
            "pip_main_parser_sha256": c.PIP_MAIN_PARSER_SHA256,
            "pip_build_env_sha256": c.PIP_BUILD_ENV_SHA256,
            "pip_runner_sha256": c.PIP_RUNNER_SHA256,
            "p5_static_launch_edge_proof_state": c.P5_STATIC_PROOF_STATE,
        },
        "path_plan": _path_plan(),
        "private_transport": {
            "schema_version": c.PRIVATE_TRANSPORT_SCHEMA,
            "https_proxy": "https://proxy.private:8443",
            "custom_ca_locator": "/private/work-ca.pem",
            "expected_proxy_class": "WORK_TRANSPORT_PROXY_V1",
            "expected_ca_raw_sha256": "f" * 64,
            "expected_stable_projection_sha256": "0" * 64,
        },
        "egress_attestation_source": {
            "schema_version": c.EGRESS_ATTESTATION_SOURCE_SCHEMA,
            "private_locator": "/platform/egress-attestation.json",
            "expected_owner_class": "PLATFORM_ROOT",
            "expected_mode": "0400",
            "expected_regular_file": True,
            "expected_nlink": 1,
            "expected_raw_sha256": attestation_sha,
            "expected_expiry": attestation["expires_at"],
        },
        "egress_attestation": attestation,
        "egress_attestation_sha256": attestation_sha,
        "publication_contract": {
            "schema_version": c.PUBLICATION_CONTRACT_SCHEMA,
            "cocolon_pre_head": "9" * 40,
            "receipt_path": "documents/receipt.json",
            "current_state_path": "Cocolon_前提資料/08_cycle001_current_state.md",
            "conditional_closure_route_path": "documents/closure.md",
            "conditional_milestone_path": "",
            "approved_public_path_set_sha256": "8" * 64,
            "result_unknown_policy": c.RESULT_UNKNOWN_POLICY,
        },
    }


def _validated_lock() -> dict[str, object]:
    return contract.validate_lock_derivation(FORMAL_LOCK.read_bytes(), DERIVED_LOCK.read_bytes())


class RuntimePreparationControllerV1Tests(unittest.TestCase):
    maxDiff = None

    def test_01_exact7_inventory_and_checker_exact5_unchanged(self) -> None:
        exact7 = (
            "ai/configs/emlis_nls_v3_s11_g4b_runtime_preparation_exact5_lock_v1.json",
            "ai/tools/emlis_nls_v3_s11_g4b_runtime_preparation_contract_v1.py",
            "ai/tools/emlis_nls_v3_s11_g4b_runtime_acquisition_v1.py",
            "ai/tools/emlis_nls_v3_s11_g4b_runtime_materialization_v1.py",
            "ai/tools/emlis_nls_v3_s11_g4b_runtime_admission_bridge_v1.py",
            "ai/tools/emlis_nls_v3_s11_g4b_runtime_preparation_controller_v1.py",
            "ai/tests/test_emlis_nls_v3_s11_g4b_runtime_preparation_controller_v1.py",
        )
        self.assertEqual(len(exact7), 7)
        self.assertTrue(all((REPO_ROOT / item).is_file() for item in exact7))
        protected = {
            "ai/tools/emlis_nls_v3_s11_g4b_runtime_admission_contract_v1.py": "cb2fb32912baee32a6d40f2791f68c61eeaa39c4e351d5a7cfbd52319dd01ea4",
            "ai/tools/emlis_nls_v3_s11_g4b_runtime_admission_checker_v1.py": "2fc106423c3aaae3ef26c4a4592d7a377efd2e214f03924f47a6055eabaf8c2a",
            "ai/tools/emlis_nls_v3_s11_g4b_runtime_admission_owner_v1.py": "065a8f6d76391a0499a6caf7a2a8e1e4b57ab22a30b2274de293722e901b33a4",
            "ai/tools/emlis_nls_v3_s11_g4b_runtime_admission_independent_v1.py": "0996a185160c03a8cedde7aa43e45310d40964ae30669e057030a31969e2435a",
            "ai/tests/test_emlis_nls_v3_s11_g4b_runtime_admission_checker_v1.py": "051d027e47a1ea734026a4e4f8456605be248efedb126e4a72d1bf76ced78e55",
        }
        self.assertEqual({name: _sha((REPO_ROOT / name).read_bytes()) for name in protected}, protected)

    def test_02_import_dag_allowlist_forbidden_imports_and_exact18_ast(self) -> None:
        modules = {
            "emlis_nls_v3_s11_g4b_runtime_preparation_contract_v1.py": set(),
            "emlis_nls_v3_s11_g4b_runtime_acquisition_v1.py": {
                "ai.tools.emlis_nls_v3_s11_g4b_runtime_preparation_contract_v1"
            },
            "emlis_nls_v3_s11_g4b_runtime_materialization_v1.py": {
                "ai.tools.emlis_nls_v3_s11_g4b_runtime_preparation_contract_v1"
            },
            "emlis_nls_v3_s11_g4b_runtime_admission_bridge_v1.py": {
                "ai.tools.emlis_nls_v3_s11_g4b_runtime_preparation_contract_v1",
                "ai.tools.emlis_nls_v3_s11_g4b_runtime_admission_contract_v1",
            },
            "emlis_nls_v3_s11_g4b_runtime_preparation_controller_v1.py": {
                "ai.tools.emlis_nls_v3_s11_g4b_runtime_preparation_contract_v1",
                "ai.tools.emlis_nls_v3_s11_g4b_runtime_acquisition_v1",
                "ai.tools.emlis_nls_v3_s11_g4b_runtime_materialization_v1",
                "ai.tools.emlis_nls_v3_s11_g4b_runtime_admission_bridge_v1",
            },
        }
        forbidden_roots = {"pip", "requests", "socket", "http", "urllib.request"}
        for name, expected_project in modules.items():
            tree = ast.parse((TOOLS / name).read_text(encoding="utf-8"))
            imported = {
                node.module
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom) and node.module is not None
            }
            imported.update(
                alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names
            )
            self.assertEqual({item for item in imported if item.startswith("ai.")}, expected_project)
            self.assertFalse(any(item in forbidden_roots for item in imported))
        own_tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
        methods = sorted(
            node.name for node in ast.walk(own_tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_")
        )
        self.assertEqual(methods, [f"test_{index:02d}_{suffix}" for index, suffix in (
            (1, "exact7_inventory_and_checker_exact5_unchanged"),
            (2, "import_dag_allowlist_forbidden_imports_and_exact18_ast"),
            (3, "full46_to_exact5_canonical_derivation"),
            (4, "strict_json_rejects_duplicate_bom_cr_non_nfc_and_noncanonical"),
            (5, "requirements_bytes_and_fixed_identities"),
            (6, "official_pypi_exact2_host_policy"),
            (7, "path20_distinct19_private18"),
            (8, "preactivation_head_identity_and_effect_zero_validation"),
            (9, "private_transport_b0_b1_b2_seal_and_public_redaction"),
            (10, "acquisition_argv_exact12_environment_and_single_success_child"),
            (11, "acquisition_rejection_timeout_hash_failure_consumed_no_retry"),
            (12, "wheel_metadata_record_and_zip_safety"),
            (13, "in_process_venv_and_offline_install_network_zero"),
            (14, "installed_closure_full_root_and_partial_cleanup"),
            (15, "checker_request_preserves_full46_and_composite_exact25"),
            (16, "conditional_exact11_ledger_schema_and_pinned_p5_edge"),
            (17, "option_b_lifecycle_cleanup_seal_and_post_cleanup_exact31"),
            (18, "official_cli_exact31_durable_exact17_and_body_free_result"),
        )])
        self.assertEqual(contract.__all__, (
            "PreparationViolation", "PreparationContractV1", "canonical_json_bytes",
            "canonical_file_bytes", "canonical_sha256", "strict_json_from_bytes",
            "validate_lock_derivation", "derive_requirements_bytes",
            "validate_stable_authority_approval", "validate_execution_request",
            "validate_path_plan", "validate_public_result",
            "validate_durable_publication_transition",
        ))
        self.assertEqual(acquisition.__all__, ("capture_transport_binding_at_start", "acquire_once"))
        self.assertEqual(materialization.__all__, ("materialize_once",))
        self.assertEqual(bridge.__all__, ("run_admission_once",))
        self.assertEqual(controller.__all__, ("main",))

    def test_03_full46_to_exact5_canonical_derivation(self) -> None:
        lock = _validated_lock()
        self.assertEqual(_sha(FORMAL_LOCK.read_bytes()), contract.PreparationContractV1.FORMAL_LOCK_RAW_SHA256)
        self.assertEqual(_sha(DERIVED_LOCK.read_bytes()), contract.PreparationContractV1.DERIVED_LOCK_RAW_SHA256)
        self.assertEqual(lock["root_requirements"], ["pytest==8.4.1"])
        self.assertEqual(lock["root_imports"], ["pytest"])
        rows = lock["distributions"]
        self.assertEqual([row["normalized_distribution_name"] for row in rows], list(contract.PreparationContractV1.EXACT5_NAMES))
        self.assertEqual(rows[-1]["selected_dependency_names"], ["iniconfig", "packaging", "pluggy", "pygments"])
        self.assertTrue(all(not row["selected_dependency_names"] for row in rows[:-1]))

    def test_04_strict_json_rejects_duplicate_bom_cr_non_nfc_and_noncanonical(self) -> None:
        invalid = (
            b'{"a":1,"a":2}', b'\xef\xbb\xbf{"a":1}', b'{"a":1}\r',
            '{"x":"e\u0301"}'.encode("utf-8"), b'{"b":1, "a":2}', b'{"a":1.0}',
        )
        for payload in invalid:
            with self.subTest(payload=payload), self.assertRaises(contract.PreparationViolation):
                contract.strict_json_from_bytes(payload)
        with self.assertRaises(contract.PreparationViolation):
            contract.strict_json_from_bytes(b'{"a":1}\n\n', require_final_lf=True)
        self.assertEqual(contract.strict_json_from_bytes(b'{"a":1}\n', require_final_lf=True), {"a": 1})
        with mock.patch.object(bridge, "_read_regular", return_value=b'{"a":1}'):
            with self.assertRaises(contract.PreparationViolation):
                bridge._load_private_json("/private/evidence.json")
        with mock.patch.object(bridge, "_read_regular", return_value=b'{"a":1}\n'):
            self.assertEqual(bridge._load_private_json("/private/evidence.json")[0], {"a": 1})

    def test_05_requirements_bytes_and_fixed_identities(self) -> None:
        lock = _validated_lock()
        requirements = contract.derive_requirements_bytes(lock)
        self.assertEqual(len(requirements), 473)
        self.assertEqual(requirements.count(b"\n"), 5)
        self.assertTrue(requirements.endswith(b"\n"))
        self.assertEqual(_sha(requirements), contract.PreparationContractV1.REQUIREMENTS_SHA256)
        self.assertEqual(_sha(DERIVED_LOCK.read_bytes()[:-1]), contract.PreparationContractV1.DERIVED_LOCK_BODY_SHA256)
        self.assertEqual(bridge._git_blob_oid(DERIVED_LOCK.read_bytes()), contract.PreparationContractV1.DERIVED_LOCK_GIT_BLOB)

    def test_06_official_pypi_exact2_host_policy(self) -> None:
        c = contract.PreparationContractV1
        self.assertEqual(c.PRIMARY_INDEX_URL, "https://pypi.org/simple/")
        self.assertEqual(c.ALLOWED_HOSTS, ("files.pythonhosted.org", "pypi.org"))
        argv = acquisition._acquisition_argv(_execution_request())
        self.assertEqual(argv.count("--index-url"), 1)
        self.assertEqual(argv[argv.index("--index-url") + 1], c.PRIMARY_INDEX_URL)
        for forbidden in ("--extra-index-url", "--find-links", "--trusted-host", "--no-binary"):
            self.assertNotIn(forbidden, argv)
        for required in ("--require-hashes", "--only-binary=:all:", "--no-deps", "--no-cache-dir"):
            self.assertIn(required, argv)

    def test_07_path20_distinct19_private18(self) -> None:
        plan = contract.validate_path_plan(_path_plan())
        self.assertEqual(len(plan), 20)
        self.assertEqual(len(set(plan.values())), 19)
        self.assertEqual(plan["controller_test_cwd"], plan["checker_test_cwd"])
        private = [value for role, value in plan.items() if role not in ("controller_test_cwd", "checker_test_cwd")]
        self.assertEqual(len(private), 18)
        self.assertTrue(all(value == plan["authority_root"] or value.startswith(plan["authority_root"] + "/") for value in private))
        bad = dict(plan)
        bad["wheel_root"] = bad["runtime_root"]
        with self.assertRaises(contract.PreparationViolation):
            contract.validate_path_plan(bad)

    def test_08_preactivation_head_identity_and_effect_zero_validation(self) -> None:
        request = _execution_request()
        with mock.patch("builtins.open", side_effect=AssertionError("filesystem effect")), mock.patch(
            "subprocess.Popen", side_effect=AssertionError("process effect")
        ):
            self.assertEqual(contract.validate_execution_request(request), request)
        for path, replacement in (
            (("expected_git", "mashos_api_commit"), "x" * 40),
            (("control_runtime", "python_version"), "3.12.12"),
            (("control_runtime", "pip_runner_sha256"), "0" * 64),
        ):
            bad = copy.deepcopy(request)
            bad[path[0]][path[1]] = replacement
            with self.assertRaises(contract.PreparationViolation):
                contract.validate_execution_request(bad)
        unknown = copy.deepcopy(request)
        unknown["unapproved_extension"] = False
        with self.assertRaises(contract.PreparationViolation):
            contract.validate_execution_request(unknown)
        self.assertEqual(
            contract.PreparationContractV1.COMPOSITE_BINDING_SCHEMA,
            "emlis.nls_v3.s11.g4b.runtime_preparation.composite_binding.v1",
        )
        self.assertEqual(
            contract.PreparationContractV1.PRIVATE_HANDOFF_SCHEMA,
            "emlis.nls_v3.s11.g4b.runtime_preparation.private_handoff.v1",
        )

        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary).resolve() / "packed-clean-repo"
            git_dir = repo / ".git"
            pack_dir = git_dir / "objects" / "pack"
            pack_dir.mkdir(parents=True)
            tracked = repo / "tracked.txt"
            tracked_payload = b"tracked synthetic body\n"
            tracked.write_bytes(tracked_payload)

            blob_object = f"blob {len(tracked_payload)}\0".encode("ascii") + tracked_payload
            blob_oid = hashlib.sha1(blob_object).digest()
            path_bytes = b"tracked.txt"
            tree_body = b"100644 " + path_bytes + b"\0" + blob_oid
            tree_object = f"tree {len(tree_body)}\0".encode("ascii") + tree_body
            tree_oid = hashlib.sha1(tree_object).hexdigest()
            commit_body = f"tree {tree_oid}\n\nsynthetic packed commit\n".encode("ascii")
            commit_object = f"commit {len(commit_body)}\0".encode("ascii") + commit_body
            commit_oid = hashlib.sha1(commit_object).hexdigest()

            (git_dir / "HEAD").write_bytes(b"ref: refs/heads/main\n")
            (git_dir / "packed-refs").write_bytes(
                f"# pack-refs with: sorted\n{commit_oid} refs/heads/main\n".encode("ascii")
            )
            index_entry = (
                controller.struct.pack(">10I", 0, 0, 0, 0, 0, 0, 0o100644, 0, 0, len(tracked_payload))
                + blob_oid
                + controller.struct.pack(">H", len(path_bytes))
                + path_bytes
                + b"\0"
            )
            index_entry += b"\0" * ((-len(index_entry)) % 8)
            index_body = b"DIRC" + controller.struct.pack(">II", 2, 1) + index_entry
            (git_dir / "index").write_bytes(index_body + hashlib.sha1(index_body).digest())

            remaining = len(commit_body) >> 4
            first = (1 << 4) | (len(commit_body) & 0x0F)
            if remaining:
                first |= 0x80
            object_header = bytearray((first,))
            while remaining:
                current = remaining & 0x7F
                remaining >>= 7
                if remaining:
                    current |= 0x80
                object_header.append(current)
            packed_entry = bytes(object_header) + controller.zlib.compress(commit_body)
            pack_without_checksum = b"PACK" + controller.struct.pack(">II", 2, 1) + packed_entry
            pack_checksum = hashlib.sha1(pack_without_checksum).digest()
            oid_bytes = bytes.fromhex(commit_oid)
            fanout = [0 if slot < oid_bytes[0] else 1 for slot in range(256)]
            index_without_checksum = (
                b"\xfftOc"
                + controller.struct.pack(">I", 2)
                + controller.struct.pack(">256I", *fanout)
                + oid_bytes
                + controller.struct.pack(">I", controller.zlib.crc32(packed_entry) & 0xFFFFFFFF)
                + controller.struct.pack(">I", 12)
                + pack_checksum
            )
            (pack_dir / "pack-synthetic.pack").write_bytes(pack_without_checksum + pack_checksum)
            (pack_dir / "pack-synthetic.idx").write_bytes(
                index_without_checksum + hashlib.sha1(index_without_checksum).digest()
            )

            self.assertEqual(controller._actual_git_head_tree(repo.as_posix()), (commit_oid, tree_oid))
            tracked.write_bytes(b"tracked content drift\n")
            with self.assertRaises(contract.PreparationViolation):
                controller._actual_git_head_tree(repo.as_posix())
            tracked.write_bytes(tracked_payload)
            (repo / "untracked.txt").write_bytes(b"untracked\n")
            with self.assertRaises(contract.PreparationViolation):
                controller._actual_git_head_tree(repo.as_posix())

    def test_09_private_transport_b0_b1_b2_seal_and_public_redaction(self) -> None:
        request = _execution_request()
        ca_raw = b"PRIVATE CA BYTES"
        observed = types.SimpleNamespace(
            st_dev=1, st_ino=2, st_mode=stat.S_IFREG | 0o400, st_nlink=1,
            st_uid=1, st_gid=1, st_size=len(ca_raw), st_mtime_ns=3,
        )
        request["private_transport"]["expected_ca_raw_sha256"] = _sha(ca_raw)
        online, _offline = acquisition._literal_environments(request)
        stable = {
            "schema_version": contract.PreparationContractV1.TRANSPORT_BINDING_SCHEMA,
            "proxy_url": "https://proxy.private:8443", "proxy_scheme": "https",
            "proxy_host": "proxy.private", "proxy_port": 8443,
            "proxy_userinfo_present": False, "ca_locator": "/private/work-ca.pem",
            "ca_stat_tuple": {key: getattr(observed, key) for key in (
                "st_dev", "st_ino", "st_mode", "st_nlink", "st_uid", "st_gid", "st_size", "st_mtime_ns"
            )},
            "ca_raw_sha256": _sha(ca_raw), "tls_verification": True,
            "normalized_child_environment_sha256": contract.canonical_sha256(online),
            "locator_published": False,
        }
        stable["ca_stat_tuple"]["st_mode"] = 0o400
        request["private_transport"]["expected_stable_projection_sha256"] = contract.canonical_sha256(stable)
        with mock.patch.object(acquisition, "_read_regular_nofollow", return_value=(ca_raw, observed)), mock.patch.object(
            acquisition.os, "geteuid", return_value=2
        ), mock.patch.object(acquisition.time, "monotonic_ns", side_effect=(10, 20, 30)):
            records = [acquisition._transport_record(request, stage) for stage in ("B0", "B1", "B2")]
        self.assertEqual([row["stage"] for row in records], ["B0", "B1", "B2"])
        self.assertEqual(len({row["binding_sha256"] for row in records}), 1)
        state = {"fd": 7, "path": "/private/binding.jsonl", "records": records, "record_lines": [b"x\n"] * 3}
        with mock.patch.object(acquisition, "_append_record"), mock.patch.object(acquisition.os, "fchmod") as chmod, mock.patch.object(
            acquisition.os, "fsync"
        ), mock.patch.object(acquisition.os, "close"), mock.patch.object(acquisition.os, "open", return_value=8), mock.patch.object(
            acquisition, "_read_regular_nofollow", return_value=(b"sealed", observed)
        ):
            acquisition._seal_transport(state, full_match=True)
        chmod.assert_called_once_with(7, 0o400)
        self.assertEqual(state["fd"], -1)

        attestation_raw = contract.canonical_json_bytes(request["egress_attestation"])
        platform_source = types.SimpleNamespace(
            st_mode=stat.S_IFREG | 0o400, st_nlink=1, st_uid=0, st_gid=0,
        )

        class FrozenDateTime(acquisition._datetime.datetime):
            @classmethod
            def now(cls, tz: object = None) -> object:
                return cls(
                    2026, 8, 12, 0, 5, 0,
                    tzinfo=acquisition._datetime.timezone.utc,
                )

        with mock.patch.object(
            acquisition, "_read_regular_nofollow",
            return_value=(attestation_raw, platform_source),
        ), mock.patch.object(
            acquisition.os, "geteuid", return_value=1000
        ), mock.patch.object(
            acquisition.os, "getegid", return_value=1000
        ), mock.patch.object(
            acquisition.os, "getgroups", return_value=[]
        ), mock.patch.object(
            acquisition._datetime, "datetime", FrozenDateTime
        ):
            p1_row, _raw_sha = acquisition._source_observation(request, "P1_ENTRY")
            p3_row, _raw_sha = acquisition._source_observation(request, "P3_PRELAUNCH")
        self.assertTrue(p1_row["expiry_valid"] and p3_row["expiry_valid"])
        self.assertFalse(p3_row["authority_writable"])
        self.assertEqual(p3_row["owner_class"], "PLATFORM_ROOT")

        self_owned = types.SimpleNamespace(
            st_mode=stat.S_IFREG | 0o400, st_nlink=1, st_uid=1000, st_gid=1000,
        )
        with mock.patch.object(
            acquisition, "_read_regular_nofollow",
            return_value=(attestation_raw, self_owned),
        ), mock.patch.object(
            acquisition.os, "geteuid", return_value=1000
        ), mock.patch.object(
            acquisition.os, "getegid", return_value=1000
        ), mock.patch.object(
            acquisition.os, "getgroups", return_value=[]
        ), mock.patch.object(
            acquisition._datetime, "datetime", FrozenDateTime
        ), self.assertRaises(contract.PreparationViolation):
            acquisition._source_observation(request, "P3_PRELAUNCH")
        self.assertIn(
            "_validate_control_runtime_actual(request)",
            (TOOLS / "emlis_nls_v3_s11_g4b_runtime_acquisition_v1.py").read_text(
                encoding="utf-8"
            ),
        )

        # A failure after B0 but before acquire_once must seal one failure
        # summary, relinquish the descriptor, and be idempotent in finally.
        with tempfile.TemporaryDirectory() as temporary:
            abort_request = _execution_request()
            binding_path = Path(temporary) / "binding.jsonl"
            abort_request["path_plan"][
                "private_transport_binding_observation"
            ] = binding_path.as_posix()
            b0 = {"binding_sha256": "a" * 64}
            b0_raw = contract.canonical_json_bytes(b0) + b"\n"
            fd = os.open(binding_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            acquisition._write_all(fd, b0_raw)
            os.fsync(fd)
            key = acquisition._state_key(abort_request)
            acquisition._ACTIVE_TRANSPORT[key] = {
                "fd": fd,
                "path": binding_path.as_posix(),
                "records": [b0],
                "record_lines": [b0_raw],
                "source_rows": [],
            }
            sealed_sha256 = acquisition._abort_transport_binding(abort_request)
            self.assertNotIn(key, acquisition._ACTIVE_TRANSPORT)
            self.assertIsNone(acquisition._abort_transport_binding(abort_request))
            sealed_raw = binding_path.read_bytes()
            self.assertEqual(sealed_sha256, _sha(sealed_raw))
            self.assertEqual(stat.S_IMODE(binding_path.stat().st_mode), 0o400)
            lines = sealed_raw.splitlines()
            self.assertEqual(len(lines), 2)
            summary = contract.strict_json_from_bytes(lines[1], require_final_lf=False)
            self.assertEqual(summary["record_count"], 1)
            self.assertFalse(summary["stable_projection_full_match"])

    def _invoke_acquire(
        self,
        process: object,
        *,
        wheel_error: Exception | None = None,
        capture_error: Exception | None = None,
    ) -> tuple[object, mock.Mock]:
        request = _execution_request()
        lock = _validated_lock()
        b0 = {"binding_sha256": "4" * 64}
        key = (request["authority_id"], request["observation_session_id"], request["path_plan"]["private_transport_binding_observation"])
        acquisition._ACTIVE_TRANSPORT[key] = {"fd": 7, "path": key[2], "records": [b0], "record_lines": [], "source_rows": []}
        popen = mock.Mock(return_value=process)
        accepted = [{"wheel_filename": row["wheel_filename"], "wheel_sha256": row["wheel_sha256"]} for row in lock["distributions"]]
        wheel_side_effect = wheel_error if wheel_error is not None else None
        with mock.patch.object(acquisition, "validate_execution_request", side_effect=lambda value: value), mock.patch.object(
            acquisition, "_transport_record", side_effect=({"binding_sha256": "4" * 64}, {"binding_sha256": "4" * 64})
        ), mock.patch.object(acquisition, "_append_record"), mock.patch.object(
            acquisition, "_source_observation", return_value=({"stage": "P3_PRELAUNCH"}, "5" * 64)
        ), mock.patch.object(acquisition, "_exclusive_file"), mock.patch.object(acquisition.os, "mkdir"), mock.patch.object(
            acquisition, "_seal_transport", return_value="6" * 64
        ), mock.patch.object(acquisition.subprocess, "Popen", popen), mock.patch.object(
            acquisition, "_capture_child", side_effect=capture_error,
            return_value=(b"ok", b"")
        ), mock.patch.object(
            acquisition, "_validate_wheels", side_effect=wheel_side_effect, return_value=accepted
        ):
            return acquisition.acquire_once(request, lock, b0), popen

    def test_10_acquisition_argv_exact12_environment_and_single_success_child(self) -> None:
        process = mock.Mock(returncode=0)
        process.communicate.return_value = (b"ok", b"")
        observation, popen = self._invoke_acquire(process)
        self.assertEqual(popen.call_count, 1)
        kwargs = popen.call_args.kwargs
        self.assertFalse(kwargs["shell"])
        self.assertFalse(kwargs["text"])
        self.assertTrue(kwargs["close_fds"])
        self.assertEqual(kwargs["pass_fds"], ())
        self.assertTrue(kwargs["start_new_session"])
        self.assertEqual(len(kwargs["env"]), 12)
        self.assertEqual(set(kwargs["env"]), {
            "HTTPS_PROXY", "LANG", "LC_ALL", "NETRC", "PIP_CONFIG_FILE",
            "PYTHONDONTWRITEBYTECODE", "PYTHONNOUSERSITE", "REQUESTS_CA_BUNDLE",
            "SSL_CERT_FILE", "TEMP", "TMP", "TMPDIR",
        })
        self.assertTrue(observation["consumed"])
        self.assertEqual(len({key: value for key, value in observation.items() if not key.startswith("_")}), 18)
        self.assertEqual(
            set(observation["_process_evidence"]),
            {
                "pid", "returncode", "executable_sha256", "argv_sha256",
                "environment_sha256", "cwd_binding_sha256", "stdout_sha256",
                "stdout_bytes", "stderr_sha256", "stderr_bytes",
                "termination_state",
            },
        )

        # Regression: the stream-reader default is 1 MiB, while a locked wheel
        # is explicitly allowed through the contract's 16 MiB raw limit.
        with tempfile.TemporaryDirectory() as temporary:
            wheel_root = Path(temporary)
            payloads = {
                "package0-1-py3-none-any.whl": b"L" * (1_048_576 + 1),
                "package1-1-py3-none-any.whl": b"1",
                "package2-1-py3-none-any.whl": b"2",
                "package3-1-py3-none-any.whl": b"3",
                "package4-1-py3-none-any.whl": b"4",
            }
            for filename, payload in payloads.items():
                (wheel_root / filename).write_bytes(payload)
            expected_rows = [
                {"wheel_filename": filename, "wheel_sha256": _sha(payloads[filename])}
                for filename in sorted(payloads)
            ]
            synthetic_lock = {"distributions": expected_rows}
            with mock.patch.object(
                contract.PreparationContractV1,
                "ACCEPTED_WHEEL_MANIFEST_SHA256",
                contract.canonical_sha256(expected_rows),
            ):
                self.assertEqual(
                    acquisition._validate_wheels(wheel_root.as_posix(), synthetic_lock),
                    expected_rows,
                )

    def test_11_acquisition_rejection_timeout_hash_failure_consumed_no_retry(self) -> None:
        failures: list[tuple[object, Exception | None, Exception | None]] = []
        rejected = mock.Mock(side_effect=OSError("reject"))
        process_timeout = mock.Mock(returncode=None)
        timeout_error = contract.PreparationViolation(
            "ACQUISITION_PROCESS_INVALID", "timeout"
        )
        timeout_error.consumed = True
        failures.append((rejected, None, None))
        failures.append((mock.Mock(return_value=process_timeout), timeout_error, None))
        hash_process = mock.Mock(returncode=0)
        failures.append((
            mock.Mock(return_value=hash_process),
            None,
            contract.PreparationViolation("ACQUIRED_WHEEL_SET_INVALID", "hash"),
        ))
        for popen_behavior, capture_error, wheel_error in failures:
            request = _execution_request()
            lock = _validated_lock()
            b0 = {"binding_sha256": "4" * 64}
            key = (request["authority_id"], request["observation_session_id"], request["path_plan"]["private_transport_binding_observation"])
            acquisition._ACTIVE_TRANSPORT[key] = {"fd": 7, "path": key[2], "records": [b0], "record_lines": [], "source_rows": []}
            accepted = [{"wheel_filename": row["wheel_filename"], "wheel_sha256": row["wheel_sha256"]} for row in lock["distributions"]]
            with mock.patch.object(acquisition, "validate_execution_request", side_effect=lambda value: value), mock.patch.object(
                acquisition, "_transport_record", side_effect=({"binding_sha256": "4" * 64}, {"binding_sha256": "4" * 64})
            ), mock.patch.object(acquisition, "_append_record"), mock.patch.object(
                acquisition, "_source_observation", return_value=({"stage": "P3_PRELAUNCH"}, "5" * 64)
            ), mock.patch.object(acquisition, "_exclusive_file"), mock.patch.object(acquisition.os, "mkdir"), mock.patch.object(
                acquisition, "_seal_transport", return_value="6" * 64
            ), mock.patch.object(acquisition, "_terminate"), mock.patch.object(
                acquisition.subprocess, "Popen", popen_behavior
            ) as popen, mock.patch.object(
                acquisition, "_capture_child", side_effect=capture_error,
                return_value=(b"", b"")
            ), mock.patch.object(
                acquisition, "_validate_wheels", side_effect=wheel_error,
                return_value=accepted
            ):
                with self.assertRaises(contract.PreparationViolation) as caught:
                    acquisition.acquire_once(request, lock, b0)
            self.assertTrue(getattr(caught.exception, "consumed", False))
            self.assertEqual(popen.call_count, 1)

    def test_12_wheel_metadata_record_and_zip_safety(self) -> None:
        metadata_raw = b"Metadata-Version: 2.1\nName: demo\nVersion: 1.0\n\n"
        module_raw = b"VALUE = 1\n"
        def record_line(name: str, payload: bytes) -> str:
            digest = base64.urlsafe_b64encode(hashlib.sha256(payload).digest()).rstrip(b"=").decode()
            return f"{name},sha256={digest},{len(payload)}\n"
        record_raw = (
            record_line("demo.py", module_raw)
            + record_line("demo-1.0.dist-info/METADATA", metadata_raw)
            + "demo-1.0.dist-info/RECORD,,\n"
        ).encode()
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("demo.py", module_raw)
            archive.writestr("demo-1.0.dist-info/METADATA", metadata_raw)
            archive.writestr("demo-1.0.dist-info/RECORD", record_raw)
        raw = buffer.getvalue()
        row = {
            "normalized_distribution_name": "demo", "distribution_version": "1.0",
            "wheel_filename": "demo-1.0-py3-none-any.whl", "wheel_sha256": _sha(raw),
            "wheel_record_sha256": _sha(record_raw), "requires_dist": [],
            "top_level_imports": ["demo"],
        }
        observed = types.SimpleNamespace(st_mode=stat.S_IFREG | 0o400, st_nlink=1)
        with mock.patch.object(materialization, "_read_regular", return_value=(raw, observed)):
            self.assertEqual(materialization._wheel_record(row, "/private/demo.whl")["wheel_record_sha256"], _sha(record_raw))
        for unsafe in ("../escape", "/absolute", "a\\b", "a/../b"):
            with self.assertRaises(contract.PreparationViolation):
                materialization._safe_zip_name(unsafe)
        with mock.patch.object(materialization.time, "monotonic_ns", return_value=2):
            with self.assertRaises(contract.PreparationViolation):
                materialization._check_deadline(1)
        source = (
            TOOLS / "emlis_nls_v3_s11_g4b_runtime_materialization_v1.py"
        ).read_text(encoding="utf-8")
        self.assertIn('with archive.open(info, "r") as member', source)
        self.assertIn("wheel member expands beyond declared size", source)

    def test_13_in_process_venv_and_offline_install_network_zero(self) -> None:
        request = _execution_request()
        argv = materialization._offline_argv(request)
        environment = materialization._offline_environment(request)
        self.assertIn("--no-index", argv)
        self.assertEqual(argv.count("--find-links"), 1)
        self.assertEqual(argv[argv.index("--find-links") + 1], request["path_plan"]["wheel_root"])
        self.assertFalse(any("http://" in item or "https://" in item for item in argv))
        self.assertEqual(len(environment), 9)
        self.assertFalse({"HTTPS_PROXY", "HTTP_PROXY", "REQUESTS_CA_BUNDLE", "SSL_CERT_FILE"} & set(environment))
        tree = ast.parse((TOOLS / "emlis_nls_v3_s11_g4b_runtime_materialization_v1.py").read_text(encoding="utf-8"))
        builders = [node for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "EnvBuilder"]
        self.assertEqual(len(builders), 1)
        keywords = {item.arg: ast.literal_eval(item.value) for item in builders[0].keywords}
        self.assertEqual(keywords["with_pip"], False)
        self.assertEqual(keywords["symlinks"], False)
        source = (
            TOOLS / "emlis_nls_v3_s11_g4b_runtime_materialization_v1.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn("process.communicate(", source)
        self.assertIn("selectors.DefaultSelector()", source)
        self.assertIn("signal.setitimer", source)
        self.assertIn("pass_fds=()", source)
        with tempfile.TemporaryDirectory() as temporary:
            runtime = Path(temporary) / "runtime"
            (runtime / "lib").mkdir(parents=True)
            os.symlink("lib", runtime / "lib64")
            materialization._normalize_cpython_linux_venv_lib64(str(runtime))
            self.assertFalse((runtime / "lib64").exists())
            os.symlink("wrong", runtime / "lib64")
            with self.assertRaises(contract.PreparationViolation):
                materialization._normalize_cpython_linux_venv_lib64(str(runtime))

    def test_14_installed_closure_full_root_and_partial_cleanup(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "runtime"
            root.mkdir()
            (root / "file.txt").write_bytes(b"one")
            first = materialization._full_root_manifest(str(root))
            self.assertEqual(first, materialization._full_root_manifest(str(root)))
            (root / "file.txt").write_bytes(b"two")
            self.assertNotEqual(first, materialization._full_root_manifest(str(root)))
            (root / "bin").mkdir()
            baseline = materialization._fresh_venv_baseline(str(root))
            (root / "bin" / "outside-site-unclaimed").write_bytes(b"injected")
            with self.assertRaisesRegex(
                contract.PreparationViolation, "unclaimed regular file"
            ):
                materialization._verify_runtime_ownership(
                    str(root), baseline, set()
                )
            with self.assertRaises(contract.PreparationViolation):
                materialization._claim_path(str(root), str(root / "site"), "../../escape")
            authority = str(Path(temporary) / "authority")
            Path(authority).mkdir(mode=0o700)
            os.chmod(authority, 0o700)
            plan = _path_plan(authority, "/repo")
            Path(plan["runtime_root"]).mkdir()
            (Path(plan["runtime_root"]) / "partial").write_bytes(b"x")
            rows: list[dict[str, object]] = []
            ledger = mock.Mock()
            state, retention = controller._cleanup({"path_plan": plan}, False, rows, ledger)
            self.assertEqual((state, retention), ("COMPLETE", "EVIDENCE_RETAINED"))
            self.assertFalse(Path(plan["runtime_root"]).exists())
            # A success claim without its runtime and private handoff must not
            # be promoted to CURRENT_SESSION_RETAINED.
            success_state, success_retention = controller._cleanup(
                {"path_plan": plan}, True, rows, ledger
            )
            self.assertEqual(
                (success_state, success_retention),
                ("FAILED", "PARTIAL_PRIVATE_STATE_RETAINED"),
            )
        source = (TOOLS / "emlis_nls_v3_s11_g4b_runtime_materialization_v1.py").read_text(encoding="utf-8")
        self.assertIn("installed_record_closure_sha256", source)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "one").write_bytes(b"1")
            with mock.patch.object(materialization, "_RUNTIME_FILES", 0):
                with self.assertRaises(contract.PreparationViolation):
                    materialization._full_root_manifest(str(root))
            self.assertEqual(bridge._full_root_manifest(str(root)), materialization._full_root_manifest(str(root)))
            with mock.patch.object(bridge, "_RUNTIME_FILES", 0):
                with self.assertRaises(contract.PreparationViolation):
                    bridge._full_root_manifest(str(root))
            with mock.patch.object(bridge.time, "monotonic_ns", return_value=2):
                with self.assertRaises(contract.PreparationViolation):
                    bridge._full_root_manifest(str(root), 1)

        request = _execution_request()
        lock = _validated_lock()
        accepted = [
            {"wheel_filename": row["wheel_filename"], "wheel_sha256": row["wheel_sha256"]}
            for row in lock["distributions"]
        ]
        online, _offline = acquisition._literal_environments(request)
        observation = {
            "schema_version": contract.PreparationContractV1.ACQUISITION_OBSERVATION_SCHEMA,
            "authority_id": request["authority_id"],
            "observation_session_id": request["observation_session_id"],
            "consumed": True,
            "process_launch_count": 1,
            "argv_sha256": contract.canonical_sha256(acquisition._acquisition_argv(request)),
            "environment_sha256": contract.canonical_sha256(online),
            "egress_attestation_sha256": request["egress_attestation_sha256"],
            "egress_attestation_source_observation_sha256": "1" * 64,
            "transport_b0_sha256": "2" * 64,
            "transport_b1_sha256": "2" * 64,
            "transport_b2_sha256": "2" * 64,
            "returncode": 0,
            "stdout_sha256": "3" * 64,
            "stderr_sha256": "4" * 64,
            "requirements_sha256": contract.PreparationContractV1.REQUIREMENTS_SHA256,
            "accepted_wheel_rows": accepted,
            "accepted_wheel_manifest_sha256": (
                contract.PreparationContractV1.ACCEPTED_WHEEL_MANIFEST_SHA256
            ),
        }
        materialization._validate_acquisition_boundary(request, lock, observation)
        extended = dict(observation)
        extended["unknown"] = True
        with self.assertRaises(contract.PreparationViolation):
            materialization._validate_acquisition_boundary(request, lock, extended)
        self.assertIn("physical - record_self != owned", source)

    def test_15_checker_request_preserves_full46_and_composite_exact25(self) -> None:
        request = _execution_request()
        c = contract.PreparationContractV1
        lock = _validated_lock()
        root = request["path_plan"]["runtime_root"]
        root_sha = checker_contract.runtime_root_locator_sha256(root)
        full_root_sha = "7" * 64
        event_preimage = {
            "schema_version": checker_contract.ContractV1.MATERIALIZATION_ATTESTATION_SCHEMA,
            "authority_id": request["authority_id"], "observation_session_id": request["observation_session_id"],
            "procedure_ids": list(c.PROCEDURE_IDS),
            "fresh_root_nonexistent_before": True, "prior_artifact_reuse_count": 0,
            "root_locator_sha256": root_sha, "expected_full_root_manifest_sha256": full_root_sha,
            "site_packages_relative": c.SITE_PACKAGES_RELATIVE,
            "admitted_executable_relative_path": "bin/python",
        }
        accepted_rows = [
            {"wheel_filename": row["wheel_filename"], "wheel_sha256": row["wheel_sha256"]}
            for row in lock["distributions"]
        ]
        acquisition_observation = {
            "schema_version": c.ACQUISITION_OBSERVATION_SCHEMA,
            "authority_id": request["authority_id"],
            "observation_session_id": request["observation_session_id"],
            "consumed": True,
            "process_launch_count": 1,
            "argv_sha256": "1" * 64,
            "environment_sha256": "2" * 64,
            "egress_attestation_sha256": request["egress_attestation_sha256"],
            "egress_attestation_source_observation_sha256": "3" * 64,
            "transport_b0_sha256": "4" * 64,
            "transport_b1_sha256": "4" * 64,
            "transport_b2_sha256": "4" * 64,
            "returncode": 0,
            "stdout_sha256": "5" * 64,
            "stderr_sha256": "6" * 64,
            "requirements_sha256": c.REQUIREMENTS_SHA256,
            "accepted_wheel_rows": accepted_rows,
            "accepted_wheel_manifest_sha256": c.ACCEPTED_WHEEL_MANIFEST_SHA256,
        }
        self.assertEqual(
            contract._validate_acquisition_observation(request, acquisition_observation),
            acquisition_observation,
        )
        for mutation in ("unknown", "transport", "manifest"):
            bad_acquisition = copy.deepcopy(acquisition_observation)
            if mutation == "unknown":
                bad_acquisition["unapproved_extension"] = False
            elif mutation == "transport":
                bad_acquisition["transport_b2_sha256"] = "9" * 64
            else:
                bad_acquisition["accepted_wheel_rows"].reverse()
            with self.subTest(acquisition_mutation=mutation), self.assertRaises(
                contract.PreparationViolation
            ):
                contract._validate_acquisition_observation(request, bad_acquisition)

        wheel_record_rows = [
            {
                "wheel_filename": row["wheel_filename"],
                "wheel_sha256": row["wheel_sha256"],
                "wheel_record_sha256": row["wheel_record_sha256"],
            }
            for row in lock["distributions"]
        ]
        attestation = {
            "schema_version": c.MATERIALIZATION_ATTESTATION_SCHEMA,
            "authority_id": request["authority_id"],
            "observation_session_id": request["observation_session_id"],
            "event_id": checker_contract.canonical_sha256(event_preimage),
            "procedure_ids": list(c.PROCEDURE_IDS),
            "fresh_root_nonexistent_before": True, "prior_artifact_reuse_count": 0,
            "runtime_root_locator_sha256": root_sha,
            "site_packages_relative": c.SITE_PACKAGES_RELATIVE,
            "derived_lock_raw_sha256": c.DERIVED_LOCK_RAW_SHA256,
            "derived_lock_logical_sha256": c.DERIVED_LOCK_LOGICAL_SHA256,
            "accepted_wheel_manifest_sha256": c.ACCEPTED_WHEEL_MANIFEST_SHA256,
            "wheel_record_rows": wheel_record_rows,
            "wheel_record_manifest_sha256": c.WHEEL_RECORD_MANIFEST_SHA256,
            "distribution_closure_sha256": c.DISTRIBUTION_CLOSURE_SHA256,
            "runtime_executable_locator_sha256": checker_contract.runtime_executable_locator_sha256(
                root + "/bin/python"
            ),
            "resolved_interpreter_sha256": c.EXPECTED_INTERPRETER_SHA256,
            "installed_file_manifest_sha256": checker_contract.ContractV1.INSTALLED_MANIFEST_COMPARATOR_SHA256,
            "full_runtime_root_manifest_sha256": full_root_sha,
            "materialization_process_ledger_sha256": "8" * 64,
            "environment_policy_sha256": c.ENVIRONMENT_POLICY_SHA256,
            "status": "MATERIALIZED_VERIFIED",
        }
        self.assertEqual(
            contract._validate_materialization_attestation(request, attestation), attestation
        )
        for mutation in ("unknown", "event", "wheel_record"):
            bad_materialization = copy.deepcopy(attestation)
            if mutation == "unknown":
                bad_materialization["unapproved_extension"] = False
            elif mutation == "event":
                bad_materialization["event_id"] = "0" * 64
            else:
                bad_materialization["wheel_record_rows"].reverse()
            with self.subTest(materialization_mutation=mutation), self.assertRaises(
                contract.PreparationViolation
            ):
                contract._validate_materialization_attestation(request, bad_materialization)

        checker_request = bridge._checker_request(request, attestation)
        self.assertEqual(checker_request["frozen"]["lock_raw_sha256"], checker_contract.ContractV1.LOCK_RAW_SHA256)
        self.assertEqual(checker_request["frozen"]["lock_logical_sha256"], checker_contract.ContractV1.LOCK_LOGICAL_SHA256)
        self.assertNotEqual(checker_request["frozen"]["lock_logical_sha256"], c.DERIVED_LOCK_LOGICAL_SHA256)
        self.assertEqual(len(c.COMPOSITE_BINDING_KEYS), 25)
        source = (TOOLS / "emlis_nls_v3_s11_g4b_runtime_admission_bridge_v1.py").read_text(encoding="utf-8")
        for field in c.COMPOSITE_BINDING_KEYS:
            self.assertIn(f'"{field}"', source)
        checker_result = {
            "runtime_instance_observation_id": "a" * 64,
            "runtime_readiness_observation_id": "b" * 64,
            "handoff_binding_sha256": "0" * 64,
        }
        observed = types.SimpleNamespace(
            st_dev=11, st_ino=12, st_mode=stat.S_IFREG | 0o500,
            st_nlink=1, st_size=13, st_mtime_ns=14,
        )
        with mock.patch.object(bridge.os, "lstat", return_value=observed), mock.patch.object(
            bridge, "_file_sha256", return_value="c" * 64
        ):
            handoff_preimage = bridge._checker_handoff_preimage(
                request, attestation, checker_result
            )
            self.assertEqual(len(handoff_preimage), 18)
            self.assertEqual(frozenset(handoff_preimage), c.HANDOFF_BINDING_KEYS)
            checker_result["handoff_binding_sha256"] = contract.canonical_sha256(
                handoff_preimage
            )
            bridge._validate_checker_handoff_binding(request, attestation, checker_result)
            checker_result["handoff_binding_sha256"] = "d" * 64
            with self.assertRaises(contract.PreparationViolation):
                bridge._validate_checker_handoff_binding(
                    request, attestation, checker_result
                )

    def test_16_conditional_exact11_ledger_schema_and_pinned_p5_edge(self) -> None:
        self.assertEqual(controller.CONDITIONAL_EXPECTED_LAUNCH_EDGE_TOPOLOGY_EXACT11, contract.PreparationContractV1.CONDITIONAL_LAUNCH_EDGE_TOPOLOGY)
        self.assertEqual(len(controller.CONDITIONAL_EXPECTED_LAUNCH_EDGE_TOPOLOGY_EXACT11), 11)
        self.assertEqual(controller.DIRECT_CHILD_ORDER, (
            "P2_FOCUSED_UNITTEST", "P3_PIP_DOWNLOAD", "P4_CONTROL_PIP_OFFLINE_INSTALL",
            "P6_CHECKER_DEDICATED_TEST", "P7_OFFICIAL_CHECKER",
        ))
        rows: list[dict[str, object]] = []
        controller._append_observation_rows(rows, {
            "argv_sha256": "1" * 64, "environment_sha256": "2" * 64, "returncode": 0,
            "stdout_sha256": "3" * 64, "stderr_sha256": "4" * 64,
        }, {
            "materialization_process_ledger_sha256": "5" * 64,
            "environment_policy_sha256": "6" * 64,
            "resolved_interpreter_sha256": contract.PreparationContractV1.EXPECTED_INTERPRETER_SHA256,
            "runtime_executable_locator_sha256": "7" * 64,
        })
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(tuple(row) == controller.PROCESS_LEDGER_KEYS_EXACT14 for row in rows))
        self.assertEqual(rows[-1]["stage"], "P5_TARGET_INTERPRETER_PIP_REEXEC")
        self.assertEqual(rows[-1]["pid_or_source_edge"], contract.PreparationContractV1.P5_STATIC_PROOF_STATE)
        child_fields = {
            "pid": 123,
            "returncode": 0,
            "stdout": b"",
            "stderr": b"",
            "termination_state": "EXITED",
            "argv_sha256": "1" * 64,
            "environment_sha256": "2" * 64,
            "cwd_binding_sha256": "3" * 64,
            "executable_sha256": "4" * 64,
        }
        p6 = bridge._ChildResult(stage="P6_CHECKER_DEDICATED_TEST", **child_fields)
        p7 = bridge._ChildResult(stage="P7_OFFICIAL_CHECKER", **child_fields)
        failure = contract.PreparationViolation("CHECKER_PROCESS_INVALID", "synthetic")
        self.assertIs(
            bridge._bind_p7_attempt_failure(
                failure, p6, p7, nested_terminal="INTERNAL_FAIL_CLOSED"
            ),
            failure,
        )
        self.assertEqual(failure.checker_execution_attempt_count, 1)
        self.assertEqual(failure.checker_component_status, "STOP")
        self.assertEqual(failure.nested_checker_terminal, "INTERNAL_FAIL_CLOSED")
        self.assertEqual([row["stage"] for row in failure.process_rows], [
            "P6_CHECKER_DEDICATED_TEST", "P7_OFFICIAL_CHECKER",
        ])
        request = _execution_request()
        evidence = {
            "pid": 456, "returncode": 0,
            "executable_sha256": request["control_runtime"]["resolved_interpreter_sha256"],
            "argv_sha256": "1" * 64, "environment_sha256": "2" * 64,
            "cwd_binding_sha256": contract.canonical_sha256({
                "schema_version": "g4b.cwd.binding.v1",
                "cwd": request["path_plan"]["controller_test_cwd"],
            }),
            "stdout_sha256": "3" * 64, "stdout_bytes": 0,
            "stderr_sha256": "4" * 64, "stderr_bytes": 0,
            "termination_state": "EXITED_WITH_PINNED_P5_SOURCE_EDGE",
        }
        projection = materialization._materialization_process_projection(
            request,
            runtime_executable_locator_sha256="5" * 64,
            resolved_interpreter_sha256=contract.PreparationContractV1.EXPECTED_INTERPRETER_SHA256,
            process_evidence=evidence,
        )
        self.assertEqual([row["stage"] for row in projection], [
            "P4_CONTROL_PIP_OFFLINE_INSTALL", "P5_TARGET_INTERPRETER_PIP_REEXEC",
        ])
        self.assertEqual(projection[1], controller._p5_source_edge_row({}, {
            "runtime_executable_locator_sha256": "5" * 64,
            "resolved_interpreter_sha256": contract.PreparationContractV1.EXPECTED_INTERPRETER_SHA256,
        }, projection[0]) | {"sequence": 1})
        self.assertEqual(contract.canonical_sha256(projection), contract.canonical_sha256(copy.deepcopy(projection)))
        bridge_source = (
            TOOLS / "emlis_nls_v3_s11_g4b_runtime_admission_bridge_v1.py"
        ).read_text(encoding="utf-8")
        direct_child = bridge_source[
            bridge_source.index("def _run_direct_child(") :
            bridge_source.index("def _full_root_manifest(")
        ]
        self.assertIn('selector.register(process.stdin, selectors.EVENT_WRITE, "stdin")', direct_child)
        self.assertIn("os.set_blocking(process.stdin.fileno(), False)", direct_child)
        self.assertLess(direct_child.index("deadline = time.monotonic()"), direct_child.index("os.write("))

    def test_17_option_b_lifecycle_cleanup_seal_and_post_cleanup_exact31(self) -> None:
        c = contract.PreparationContractV1
        approval = {
            "schema_version": c.STABLE_AUTHORITY_APPROVAL_SCHEMA, "candidate_id": c.CANDIDATE_ID,
            "approved_candidate_body_sha256": c.APPROVED_CANDIDATE_BODY_SHA256,
            "authority_id": "AUTHORITY_001", "authority_policy_id": c.AUTHORITY_POLICY_ID,
            "acquisition_policy_id": c.ACQUISITION_POLICY_ID, "egress_issuer_class": c.EGRESS_ISSUER_CLASS,
            "egress_issuer_policy_id": c.EGRESS_ISSUER_POLICY_ID, "allowed_scheme": c.ALLOWED_SCHEME,
            "allowed_hosts": list(c.ALLOWED_HOSTS), "acquisition_process_count": 1,
            "attestation_issue_phase": c.ATTESTATION_ISSUE_PHASE,
            "attestation_max_lifetime_seconds": 900,
            "minimum_remaining_lifetime_at_p3_seconds": 330,
            "same_authority_reissue_allowed": False,
        }
        self.assertEqual(contract.validate_stable_authority_approval(approval), approval)
        with tempfile.TemporaryDirectory() as temporary:
            path = str(Path(temporary) / "cleanup-ledger.jsonl")
            ledger = controller._CleanupLedger(path)
            ledger.append("TERMINAL_CLEANUP", "runtime_root", "NOT_CREATED", "NOT_CREATED", "COMPLETE", "ABSENT", SHA256_ZERO)
            digest, raw = ledger.seal()
            self.assertEqual(_sha(raw), digest)
            self.assertEqual(stat.S_IMODE(os.stat(path).st_mode), 0o400)
            with self.assertRaises(contract.PreparationViolation):
                ledger.append("TERMINAL_CLEANUP", "runtime_root", "RETAIN", "PRESENT", "COMPLETE", "RETAINED", SHA256_ZERO)
        main_source = (TOOLS / "emlis_nls_v3_s11_g4b_runtime_preparation_controller_v1.py").read_text(encoding="utf-8")
        start = main_source.index("def _terminalize_started(")
        ordered = [main_source.index(token, start) for token in (
            "_cleanup(", "cleanup_ledger.seal()", "_build_public_result_once(",
            "_seal_terminal_evidence(", "return (",
        )]
        self.assertEqual(ordered, sorted(ordered))
        cleanup_failed_terminal = controller._Terminal(
            primary_terminal=c.PRIMARY_SUCCESS_TERMINAL,
            nested_checker_terminal="RUNTIME_READY_CURRENT_SESSION_STOP",
            consumed=True,
            checker_execution_attempt_count=1,
            checker_component_status="VALID",
            composite_binding_sha256="7" * 64,
            success=True,
        )
        cleanup_failed, _raw, _digest = controller._build_public_result_once(
            _execution_request(), cleanup_failed_terminal, "FAILED",
            "PARTIAL_PRIVATE_STATE_RETAINED",
        )
        self.assertEqual(cleanup_failed["status"], "STOP")
        self.assertEqual(cleanup_failed["primary_terminal"], "INTERNAL_FAIL_CLOSED")
        self.assertEqual(cleanup_failed["checker_component_status"], "VALID")
        self.assertEqual(cleanup_failed["composite_technical_result"], "STOP_CLEANUP_INCOMPLETE")
        self.assertFalse(cleanup_failed["technical_chain_complete"])
        fallback = controller._sanitized_started_fallback("PRIVACY_VIOLATION")
        fallback_value = contract.strict_json_from_bytes(fallback)
        self.assertEqual(len(fallback_value), 31)
        self.assertEqual(fallback_value["status"], "STOP")
        self.assertEqual(fallback_value["primary_terminal"], "PRIVACY_VIOLATION")
        self.assertEqual(fallback_value["cleanup_state"], "UNKNOWN")
        self.assertFalse(fallback_value["technical_chain_complete"])

        with tempfile.TemporaryDirectory() as temporary:
            authority = Path(temporary) / "authority"
            authority.mkdir(mode=0o700)
            os.chmod(authority, 0o700)
            request = _execution_request()
            request["path_plan"] = _path_plan(str(authority), str(REPO_ROOT))
            invalid_role = "private_transport_binding_observation"
            invalid_evidence = Path(request["path_plan"][invalid_role])
            invalid_evidence.write_bytes(b"unsealed")
            os.chmod(invalid_evidence, 0o600)
            invalid_terminal = controller._Terminal(primary_terminal="INTERNAL_FAIL_CLOSED")
            invalid_rows: list[dict[str, object]] = []
            invalid_ledger = mock.Mock()
            cleanup_state, retention_state = controller._cleanup(
                request,
                False,
                invalid_rows,
                invalid_ledger,
                terminal=invalid_terminal,
            )
            self.assertEqual(
                (cleanup_state, retention_state),
                ("FAILED", "PARTIAL_PRIVATE_STATE_RETAINED"),
            )
            ledger_row = next(
                call.args for call in invalid_ledger.append.call_args_list
                if call.args[1] == invalid_role
            )
            self.assertEqual(
                ledger_row[2:6], ("RETAIN", "PRESENT", "FAILED", "RETAINED")
            )
            path_row = next(row for row in invalid_rows if row["role"] == invalid_role)
            self.assertEqual(path_row["result"], "FAILED")
            self.assertEqual(path_row["pre_state"], "PRESENT")
            invalid_result, _invalid_raw, _invalid_sha = controller._build_public_result_once(
                request, invalid_terminal, cleanup_state, retention_state
            )
            self.assertEqual(invalid_result["status"], "STOP")
            self.assertEqual(invalid_result["current_session_runtime_readiness"], "NOT_READY")
            self.assertFalse(invalid_result["technical_chain_complete"])

        with tempfile.TemporaryDirectory() as temporary:
            authority = Path(temporary) / "authority"
            authority.mkdir(mode=0o700)
            request = _execution_request()
            request["path_plan"] = _path_plan(str(authority), str(REPO_ROOT))
            missing_role = "acquisition_observation"
            missing_terminal = controller._Terminal(primary_terminal="INTERNAL_FAIL_CLOSED")
            missing_terminal.retained_raw_sha256[missing_role] = "a" * 64
            missing_rows: list[dict[str, object]] = []
            controller._path_row(
                missing_rows,
                missing_role,
                request["path_plan"][missing_role],
                "CREATE",
                "ABSENT",
                "SEALED_0400",
                "COMPLETE",
            )
            missing_ledger = mock.Mock()
            missing_state, missing_retention = controller._cleanup(
                request,
                False,
                missing_rows,
                missing_ledger,
                terminal=missing_terminal,
            )
            self.assertEqual(
                (missing_state, missing_retention),
                ("FAILED", "PARTIAL_PRIVATE_STATE_RETAINED"),
            )
            missing_row = next(
                call.args for call in missing_ledger.append.call_args_list
                if call.args[1] == missing_role
            )
            self.assertEqual(
                missing_row[2:6],
                ("RETAIN", "EXPECTED_PRESENT", "FAILED", "ABSENT_AFTER_CREATION"),
            )

        with tempfile.TemporaryDirectory() as temporary:
            invalid_authority = Path(temporary) / "invalid-authority"
            invalid_authority.mkdir(mode=0o700)
            os.chmod(invalid_authority, 0o755)
            invalid_request = _execution_request()
            invalid_request["path_plan"] = _path_plan(
                str(invalid_authority), str(REPO_ROOT)
            )
            invalid_state, invalid_retention = controller._cleanup(
                invalid_request,
                False,
                [],
                mock.Mock(),
                terminal=controller._Terminal(primary_terminal="INTERNAL_FAIL_CLOSED"),
            )
            self.assertEqual(
                (invalid_state, invalid_retention),
                ("FAILED", "PARTIAL_PRIVATE_STATE_RETAINED"),
            )

            missing_request = _execution_request()
            missing_request["path_plan"] = _path_plan(
                str(Path(temporary) / "missing-authority"), str(REPO_ROOT)
            )
            missing_state, missing_retention = controller._cleanup(
                missing_request,
                False,
                [],
                mock.Mock(),
                terminal=controller._Terminal(primary_terminal="INTERNAL_FAIL_CLOSED"),
            )
            self.assertEqual(
                (missing_state, missing_retention),
                ("FAILED", "PARTIAL_PRIVATE_STATE_RETAINED"),
            )

    def test_18_official_cli_exact31_durable_exact17_and_body_free_result(self) -> None:
        request = _execution_request()
        terminal = controller._Terminal(
            primary_terminal=contract.PreparationContractV1.PRIMARY_SUCCESS_TERMINAL,
            nested_checker_terminal="HANDOFF_BOUND_CURRENT_SESSION", consumed=True,
            checker_execution_attempt_count=1, checker_component_status="VALID",
            composite_binding_sha256="7" * 64, success=True,
        )
        result, raw, digest = controller._build_public_result_once(
            request, terminal, "COMPLETE", "CURRENT_SESSION_RETAINED"
        )
        self.assertEqual(len(result), 31)
        self.assertEqual(tuple(result), controller.PUBLIC_RESULT_KEYS_EXACT31)
        self.assertEqual(_sha(raw), digest)
        self.assertTrue(result["technical_chain_complete"])
        self.assertFalse(result["gate_c_authorized"])
        self.assertFalse(result["automatic_progression"])
        for private in (
            request["authority_id"], request["observation_session_id"], request["receiver_session_id"],
            request["receiver_nonce"], request["private_transport"]["https_proxy"],
            request["private_transport"]["custom_ca_locator"], request["path_plan"]["runtime_root"],
        ):
            self.assertNotIn(str(private).encode(), raw)
        transition = {
            "schema_version": contract.PreparationContractV1.DURABLE_TRANSITION_SCHEMA,
            "candidate_id": contract.PreparationContractV1.CANDIDATE_ID,
            "authority_context_binding_sha256": result["authority_context_binding_sha256"],
            "session_context_binding_sha256": result["session_context_binding_sha256"],
            "controller_public_result_sha256": digest,
            "terminal_evidence_envelope_sha256": "6" * 64,
            "publication_state": "VERIFIED", "remote_postverify_state": "EXACT_MATCH",
            "durable_work_complete": True, "current_owner_runtime_ready": True,
            "current_owner_gate_b_closed": True, "current_owner_readiness_credit": 1,
            "current_owner_technical_credit": 1, "current_owner_product_credit": 0,
            "current_owner_primary_outcome": "TECHNICAL_CREDIT",
            "publication_staging_cleanup_state": "ABSENT_VERIFIED", "automatic_progression": False,
        }
        self.assertEqual(contract.validate_durable_publication_transition(transition), transition)
        self.assertEqual(controller.__all__, ("main",))
        source = (TOOLS / "emlis_nls_v3_s11_g4b_runtime_preparation_controller_v1.py").read_text(encoding="utf-8")
        self.assertIn('if __name__ == "__main__":', source)
        self.assertIn("_assert_official_cli_context()", source)
        p1_row = {
            "sequence": 0,
            "stage": "P1_CONTROLLER",
            "launch_owner": "ULTRA_KAREN_APPROVED_LIVE_AUTHORITY",
            "executable_sha256": "1" * 64,
            "argv_sha256": "2" * 64,
            "environment_sha256": "3" * 64,
            "cwd_binding_sha256": "4" * 64,
            "pid_or_source_edge": "123",
            "returncode": -1,
            "stdout_sha256": SHA256_ZERO,
            "stdout_bytes": -1,
            "stderr_sha256": SHA256_ZERO,
            "stderr_bytes": -1,
            "termination_state": "TERMINAL_EMIT_PENDING_RETURN_CODE_UNOBSERVED",
        }
        lifecycle_terminal = controller._Terminal(primary_terminal="INTERNAL_FAIL_CLOSED")
        fake_ledger = object()
        with mock.patch.object(
            controller, "_assert_official_cli_context", return_value=str(REPO_ROOT)
        ), mock.patch.object(
            controller, "_read_request", return_value=request
        ), mock.patch.object(
            controller, "_p1_process_row", return_value=p1_row
        ), mock.patch.object(
            controller, "_run_lifecycle", return_value=(lifecycle_terminal, fake_ledger)
        ) as run_lifecycle, mock.patch.object(
            controller, "_terminalize_started", return_value=(2, b"body-free")
        ) as terminalize, mock.patch.object(controller, "_emit_once") as emit:
            self.assertEqual(controller.main(), 2)
            self.assertEqual(run_lifecycle.call_count, 1)
            self.assertEqual(terminalize.call_count, 1)
            emit.assert_called_once_with(b"body-free")

        failed_ledger = mock.Mock()
        failed_ledger.seal.side_effect = OSError("seal failed")
        fatal_terminal = controller._Terminal(primary_terminal="INTERNAL_FAIL_CLOSED")
        with mock.patch.object(
            controller, "_assert_official_cli_context", return_value=str(REPO_ROOT)
        ), mock.patch.object(
            controller, "_read_request", return_value=request
        ), mock.patch.object(
            controller, "_p1_process_row", return_value=p1_row
        ), mock.patch.object(
            controller, "_run_lifecycle", return_value=(fatal_terminal, failed_ledger)
        ), mock.patch.object(
            controller, "_cleanup", return_value=("UNKNOWN", "PARTIAL_PRIVATE_STATE_RETAINED")
        ), mock.patch.object(
            controller, "_build_public_result_once"
        ) as build_result, mock.patch.object(
            controller, "_seal_terminal_evidence"
        ) as seal_evidence, mock.patch.object(controller, "_emit_once") as emit:
            self.assertEqual(controller.main(), 3)
            build_result.assert_not_called()
            seal_evidence.assert_not_called()
            emit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
