# -*- coding: utf-8 -*-
from __future__ import annotations

"""Frozen offline dependency closure for dormant NLS v3 Step 9.

Step 10 owns runtime integration.  Until then, this manifest binds the Step 9
decision path to the exact Step 0--8 owners, Step 9 implementation modules and
the unchanged public v1 owner without importing the public runtime path.
"""

import hashlib
from pathlib import Path
import re
from typing import Any

from emlis_ai_nls_v3_artifact_contract import artifact_sha256


STEP9_DEPENDENCY_MANIFEST: dict[str, Any] = {
    "schema_version": "cocolon.emlis.nls_v3.step9_dependency_manifest.v1",
    "source_files": {
        "emlis_ai_body_semantic_atom_parser_v3.py": "a006c87081b7f3978305a8a024c22f9d27be0e5f034a900f5341f3b59a13cc9f",
        "emlis_ai_bounded_recovery_v3.py": "e1e62049fc521658597124832d700a4842aca995ffd9ae38f8db583b7ba4f13f",
        "emlis_ai_canonical_renderer_v3.py": "7f85e7dc8c5e2009409adf5a6700cfc12a4c1e7b2ffa522c96f7319fcbfa5507",
        "emlis_ai_content_selection_v3.py": "ec2ccfc92c5566e8ec780e67db54b4a4c620a9334f2ab2cac91a314550f43f0d",
        "emlis_ai_discourse_graph_planner_v3.py": "b53fc447707f1fe77440aaf0f59ccb815557064ecfeb9c6b484db0733e4917bf",
        "emlis_ai_evidence_ledger_service.py": "17e51d7ff39535d60f81ad17582f36ab252301502a3a3328e703d116cea7f9e2",
        "emlis_ai_grounded_observation_plan.py": "b422093f907f3a825ec30f687f2f8b1d2688bf89950d9bc7436bfe0b5a67d177",
        "emlis_ai_grounded_observation_semantic_restatement_v3.py": "a014e942b34c2c8f2a424dda0b0ecd30cb34ff99112e813d2182ad84d34b65fc",
        "emlis_ai_independent_semantic_matcher_v3.py": "12f040407adc299b2695ee58b93619157690cfb745072b4e72f529ee5dd2ed9e",
        "emlis_ai_lexicographic_selector_v3.py": "4fa8770d82273b328e0a968b1315ec68f6c57cdf4aec576dbc36434f5453833d",
        "emlis_ai_nls_v3_artifact_contract.py": "c20b262495276c9b549b257380e1a7c28069c316a7aca4b6e00a49de03d1512b",
        "emlis_ai_observation_stage_context_v3.py": "c112508fa530d23c15f6771debaaaa63c972855bdae8e007530179c5cef8f935",
        "emlis_ai_reply_service.py": "a8b494ff6d14df771e3f1c17d7d516c8457daf17a9431a118f3b44088aff90b6",
        "emlis_ai_semantic_hard_gate_v3.py": "ce2a9818b46196fa5966a2e13394cc1b51089aab664e6660e86c4526f9050c51",
        "emlis_ai_semantic_obligation_inventory_v3.py": "1dadb411fad46abb617da9ef9fcb48b18d8be987318966616d804c6ec69adbcb",
        "emlis_ai_step8_artifact_contract_v3.py": "50768051c12128ebb62ed0f01116251fb488f2c3204ffb6f291d895c36d8fbe8",
        "emlis_ai_step9_artifact_contract_v3.py": "216d6d1105a158dc9807d6dada006cff13050b2e2a7b133a31bdf479b5ab2d56",
        "emlis_ai_surface_grammar_catalog_v3.py": "954a2dec34443d664ff3a58c0abe4336c113c11f5be72eade41f24685d8dbc3c",
        "emlis_ai_surface_grammar_catalog_v3_step8.py": "844e2c314bcfadbee6bc59b8a1863f958c5418c9da3a4c3ac960ad902b27fafb",
        "emlis_ai_typed_surface_ast_v3.py": "2c35115761245534c3c811251e451b8bb163b6e664454a21f275acf0dc76046b",
    },
}

STEP9_DEPENDENCY_MANIFEST_SHA256 = artifact_sha256(STEP9_DEPENDENCY_MANIFEST)
FROZEN_STEP9_DEPENDENCY_MANIFEST_SHA256 = (
    "9ac49f3ee8978f48ff402afdd9fb15f16063595546898e514b09b9bdaf58e880"
)
HISTORICAL_V1_REPLY_SERVICE_SHA256 = (
    "a8b494ff6d14df771e3f1c17d7d516c8457daf17a9431a118f3b44088aff90b6"
)

# Step 10 is the designated runtime-manifest owner.  The historical manifest
# above stays byte-for-byte identical as an artifact; this separate authority
# admits only the exact Step 10 reply-service wrapper whose default owner is
# independently proven to remain v1.
AUTHORIZED_STEP10_REPLY_SERVICE_SHA256 = (
    "162b94eb185c519e50dceee62e591cc8ab02204312761874eb2fbb636ffbe50a"
)

_SHA_RE = re.compile(r"^[0-9a-f]{64}$")
_INFERENCE_ROOT = Path(__file__).resolve().parent


def _read_current_source_hashes() -> dict[str, str | None]:
    current: dict[str, str | None] = {}
    for filename in STEP9_DEPENDENCY_MANIFEST["source_files"]:
        try:
            current[filename] = hashlib.sha256(
                (_INFERENCE_ROOT / filename).read_bytes()
            ).hexdigest()
        except OSError:
            current[filename] = None
    return current


_CURRENT_SOURCE_SHA256 = _read_current_source_hashes()


def dependency_source_file_matches(filename: str) -> bool:
    if type(STEP9_DEPENDENCY_MANIFEST) is not dict:
        return False
    files = STEP9_DEPENDENCY_MANIFEST.get("source_files")
    if type(files) is not dict:
        return False
    expected = files.get(filename)
    if filename == "emlis_ai_reply_service.py":
        return (
            type(expected) is str
            and _SHA_RE.fullmatch(expected) is not None
            and expected == HISTORICAL_V1_REPLY_SERVICE_SHA256
            and _SHA_RE.fullmatch(AUTHORIZED_STEP10_REPLY_SERVICE_SHA256)
            is not None
            and AUTHORIZED_STEP10_REPLY_SERVICE_SHA256 != "0" * 64
            and _CURRENT_SOURCE_SHA256.get(filename)
            in {expected, AUTHORIZED_STEP10_REPLY_SERVICE_SHA256}
        )
    return (
        type(expected) is str
        and _SHA_RE.fullmatch(expected) is not None
        and _CURRENT_SOURCE_SHA256.get(filename) == expected
    )


def validate_step9_dependency_manifest() -> tuple[str, ...]:
    issues: set[str] = set()
    if type(STEP9_DEPENDENCY_MANIFEST) is not dict:
        return ("STEP9_DEPENDENCY_MANIFEST_SHAPE_INVALID",)
    try:
        live_manifest_sha256 = artifact_sha256(STEP9_DEPENDENCY_MANIFEST)
    except (RecursionError, TypeError, ValueError, UnicodeError):
        live_manifest_sha256 = None
    if (
        STEP9_DEPENDENCY_MANIFEST_SHA256
        != FROZEN_STEP9_DEPENDENCY_MANIFEST_SHA256
        or live_manifest_sha256 != FROZEN_STEP9_DEPENDENCY_MANIFEST_SHA256
    ):
        issues.add("STEP9_DEPENDENCY_MANIFEST_HASH_DRIFT")
    files = STEP9_DEPENDENCY_MANIFEST.get("source_files")
    if type(files) is not dict or not files:
        issues.add("STEP9_DEPENDENCY_MANIFEST_SHAPE_INVALID")
        return tuple(sorted(issues))
    for filename, expected in files.items():
        if (
            type(filename) is not str
            or Path(filename).name != filename
            or not filename.endswith(".py")
            or type(expected) is not str
            or _SHA_RE.fullmatch(expected) is None
        ):
            issues.add("STEP9_DEPENDENCY_MANIFEST_ENTRY_INVALID")
            continue
        actual = _CURRENT_SOURCE_SHA256.get(filename)
        if actual is None:
            issues.add("STEP9_DEPENDENCY_SOURCE_MISSING")
        elif filename == "emlis_ai_reply_service.py" and actual in {
            expected,
            AUTHORIZED_STEP10_REPLY_SERVICE_SHA256,
        } and expected == HISTORICAL_V1_REPLY_SERVICE_SHA256:
            continue
        elif actual != expected:
            issues.add("STEP9_DEPENDENCY_SOURCE_BYTES_DRIFT")
    return tuple(sorted(issues))


__all__ = [
    "AUTHORIZED_STEP10_REPLY_SERVICE_SHA256",
    "FROZEN_STEP9_DEPENDENCY_MANIFEST_SHA256",
    "HISTORICAL_V1_REPLY_SERVICE_SHA256",
    "STEP9_DEPENDENCY_MANIFEST",
    "STEP9_DEPENDENCY_MANIFEST_SHA256",
    "dependency_source_file_matches",
    "validate_step9_dependency_manifest",
]
